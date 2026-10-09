"""MCP 服务器管理器 - 支持 stdio 模式"""
import subprocess
import json
import os
import sys
import io
import threading
from typing import Dict, Any, Optional
from app.llm.mcp_config import MCP_SERVERS

# 导入角色日志缓冲函数（延迟导入避免循环）
def _get_buffered_print():
    """延迟获取 buffered_print 函数"""
    from app.roles.base import buffered_print
    return buffered_print


class MCPServerManager:
    """MCP 服务器管理器（stdio 模式）"""
    
    def __init__(self, role_name: str = "未知角色"):
        self.connections: Dict[str, Dict[str, Any]] = {}
        self._request_id = 0
        self.role_name = role_name  # 记录调用者的角色名称
    
    def _generate_request_id(self) -> int:
        """生成请求 ID"""
        self._request_id += 1
        return self._request_id
    
    def _send_jsonrpc_request(self, process, method: str, params: dict = None, log_prefix: str = "") -> dict:
        """
        发送 JSON-RPC 2.0 请求到 stdio 服务器
        
        Args:
            process: subprocess.Popen 对象
            method: JSON-RPC 方法名
            params: 方法参数
            log_prefix: 日志前缀（用于标识调用者）
        
        Returns:
            JSON-RPC 响应结果
        """
        # 构建 JSON-RPC 2.0 请求
        request = {
            "jsonrpc": "2.0",
            "id": self._generate_request_id(),
            "method": method,
            "params": params or {}
        }
        
        # 记录请求日志
        if log_prefix and method == "tools/call":
            tool_name = params.get("name", "unknown") if params else "unknown"
            tool_params = params.get("arguments", {}) if params else {}
            buffered_print = _get_buffered_print()
            buffered_print(log_prefix, f"\n   📡 [{log_prefix}] MCP 请求")
            buffered_print(log_prefix, f"      工具: {tool_name}")
            # 格式化参数，限制长度
            params_str = json.dumps(tool_params, ensure_ascii=False)
            if len(params_str) > 100:
                params_str = params_str[:100] + "..."
            buffered_print(log_prefix, f"      参数: {params_str}")
        
        # 发送请求（添加换行符）
        request_str = json.dumps(request) + "\n"
        process.stdin.write(request_str)
        process.stdin.flush()
        
        # 读取响应
        response_line = process.stdout.readline()
        if not response_line:
            raise RuntimeError("服务器未返回响应")
        
        response = json.loads(response_line)
        
        # 检查错误
        if "error" in response:
            error_msg = response['error']
            if log_prefix and method == "tools/call":
                buffered_print = _get_buffered_print()
                buffered_print(log_prefix, f"   ❌ [{log_prefix}] MCP 失败")
                buffered_print(log_prefix, f"      错误: {error_msg}")
            raise RuntimeError(f"JSON-RPC 错误: {error_msg}")
        
        result = response.get("result", {})
        
        # 记录响应日志
        if log_prefix and method == "tools/call":
            # 提取文本内容用于日志（显示完整结果）
            content_text = ""
            if "content" in result and len(result["content"]) > 0:
                content = result["content"][0]
                if content.get("type") == "text":
                    # 不再截断，显示完整结果，但替换换行符为空格以保持单行
                    content_text = content["text"].replace('\n', ' \n   ')
            
            buffered_print = _get_buffered_print()
            buffered_print(log_prefix, f"   ✅ [{log_prefix}] MCP 成功")
            buffered_print(log_prefix, f"      结果:\n   {content_text}")
        
        return result
    
    def _send_jsonrpc_notification(self, process, method: str, params: dict = None):
        """
        发送 JSON-RPC 2.0 通知（不期待响应）
        
        Args:
            process: subprocess.Popen 对象
            method: 通知方法名
            params: 通知参数
        """
        # 构建通知（没有 id 字段）
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }
        
        # 发送通知
        notification_str = json.dumps(notification) + "\n"
        process.stdin.write(notification_str)
        process.stdin.flush()
    
    def connect(self, server_name: str) -> subprocess.Popen:
        """
        连接指定的 MCP 服务器（按需加载）
        
        Args:
            server_name: 服务器名称
        
        Returns:
            subprocess.Popen 对象
        """
        # 已连接则直接返回
        if server_name in self.connections:
            return self.connections[server_name]["process"]
        
        # 检查配置
        if server_name not in MCP_SERVERS:
            raise ValueError(f"未知的服务器: {server_name}")
        
        config = MCP_SERVERS[server_name]
        
        # 准备环境变量
        env = os.environ.copy()
        if "env" in config:
            env.update(config["env"])
        
        # 启动进程
        print(f"🚀 启动 {server_name} 服务器...")
        try:
            # 先创建不带text模式的Popen
            raw_process = subprocess.Popen(
                [config["command"]] + config["args"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,  # 无缓冲
                env=env
            )
            
            # 用io.TextIOWrapper包装stdin/stdout，设置UTF-8编码
            process = raw_process
            process.stdin = io.TextIOWrapper(
                raw_process.stdin,
                encoding='utf-8',
                errors='replace',
                line_buffering=True
            )
            process.stdout = io.TextIOWrapper(
                raw_process.stdout,
                encoding='utf-8',
                errors='replace',
                line_buffering=True
            )
            process.stderr = io.TextIOWrapper(
                raw_process.stderr,
                encoding='utf-8',
                errors='replace',
                line_buffering=True
            )
            
            # 初始化握手
            try:
                result = self._send_jsonrpc_request(
                    process,
                    "initialize",
                    {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "brainstorm-agent", "version": "1.0.0"}
                    }
                )
                
                # 发送 initialized 通知（不是请求！）
                self._send_jsonrpc_notification(
                    process,
                    "notifications/initialized",
                    {}
                )
                
                print(f"✅ {server_name} 连接成功")
            except Exception as e:
                process.terminate()
                raise RuntimeError(f"{server_name} 初始化失败: {e}")
            
            # 保存连接
            self.connections[server_name] = {
                "process": process,
                "config": config
            }
            
            return process
            
        except FileNotFoundError as e:
            raise RuntimeError(f"找不到命令: {config['command']}。请确保已安装 {config['command']}")
        except Exception as e:
            raise RuntimeError(f"启动 {server_name} 失败: {e}")
    
    def call_tool(self, server_name: str, tool_name: str, role_name: str = None, **kwargs) -> Any:
        """
        调用工具
        
        Args:
            server_name: 服务器名称
            tool_name: 工具名称
            role_name: 调用者的角色名称（用于日志）
            **kwargs: 工具参数
        
        Returns:
            工具调用结果
        """
        # 使用传入的角色名，如果没有则使用初始化时的角色名
        log_prefix = role_name or self.role_name
        
        process = self.connect(server_name)
        
        # 调用工具
        result = self._send_jsonrpc_request(
            process,
            "tools/call",
            {
                "name": tool_name,
                "arguments": kwargs
            },
            log_prefix=log_prefix
        )
        
        # 提取文本内容
        if "content" in result and len(result["content"]) > 0:
            content = result["content"][0]
            if content.get("type") == "text":
                return content["text"]
        
        return result
    
    def list_tools(self, server_name: str) -> list:
        """
        列出服务器的工具
        
        Args:
            server_name: 服务器名称
        
        Returns:
            工具列表
        """
        process = self.connect(server_name)
        
        result = self._send_jsonrpc_request(process, "tools/list", {})
        return result.get("tools", [])
    
    def disconnect(self, server_name: str):
        """
        断开指定服务器
        
        Args:
            server_name: 服务器名称
        """
        if server_name in self.connections:
            try:
                self.connections[server_name]["process"].terminate()
            except:
                pass
            del self.connections[server_name]
            print(f"🔌 断开 {server_name}")
    
    def close_all(self):
        """关闭所有服务器"""
        for name in list(self.connections.keys()):
            self.disconnect(name)
