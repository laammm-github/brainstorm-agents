"""
Python代码执行MCP服务器 - 安全沙箱环境

提供安全的Python代码执行能力，用于统计计算、数据分析等场景。

安全特性：
- 沙箱环境执行
- 禁止危险模块导入
- 超时限制（30秒）
- 禁止文件写入、网络请求
- 只允许安全的内置函数
"""
import sys
import json
import signal
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
from typing import Any


# 允许的内置函数白名单
SAFE_BUILTINS = {
    # 数学函数
    'abs': abs,
    'round': round,
    'min': min,
    'max': max,
    'sum': sum,
    'pow': pow,
    # 类型转换
    'int': int,
    'float': float,
    'str': str,
    'bool': bool,
    'list': list,
    'dict': dict,
    'tuple': tuple,
    'set': set,
    # 数据结构
    'len': len,
    'range': range,
    'enumerate': enumerate,
    'zip': zip,
    'map': map,
    'filter': filter,
    'sorted': sorted,
    'reversed': reversed,
    # 输入输出
    'print': print,
    'format': format,
    # 其他安全函数
    'isinstance': isinstance,
    'issubclass': issubclass,
    'hasattr': hasattr,
    'getattr': getattr,
    'type': type,
}

# 允许导入的安全模块
SAFE_MODULES = {
    'math': ['math'],
    'statistics': ['statistics'],
    'datetime': ['datetime'],
    'collections': ['collections'],
    'itertools': ['itertools'],
    'json': ['json'],
    're': ['re'],
}


class TimeoutError(Exception):
    """超时异常"""
    pass


def timeout_handler(signum, frame):
    """超时信号处理"""
    raise TimeoutError("代码执行超时（30秒）")


def execute_python_safely(code: str, timeout: int = 30) -> dict:
    """
    安全执行Python代码
    
    Args:
        code: 要执行的Python代码
        timeout: 超时时间（秒）
        
    Returns:
        执行结果字典 {success, output, error}
    """
    # 创建输出缓冲
    stdout_buffer = StringIO()
    stderr_buffer = StringIO()
    
    try:
        # 安全检查：禁止危险操作
        dangerous_patterns = [
            'import os', 'import sys', 'import subprocess',
            'import shutil', 'import socket', 'import requests',
            '__import__', 'eval(', 'exec(', 'compile(',
            'open(', 'file(', 'input(',
            'os.', 'sys.', 'subprocess.',
        ]
        
        for pattern in dangerous_patterns:
            if pattern in code:
                return {
                    "success": False,
                    "output": None,
                    "error": f"安全限制：禁止使用 '{pattern}'"
                }
        
        # 设置超时
        if sys.platform != 'win32':
            # Windows不支持signal.SIGALRM
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout)
        
        # 构建安全的执行环境
        safe_globals = {
            "__builtins__": SAFE_BUILTINS,
            "__name__": "__main__",
        }
        
        # 导入安全模块
        for module_name in SAFE_MODULES:
            try:
                module = __import__(module_name)
                safe_globals[module_name] = module
            except ImportError:
                pass
        
        # 执行代码
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            exec(code, safe_globals)
        
        # 取消超时
        if sys.platform != 'win32':
            signal.alarm(0)
        
        # 获取输出
        output = stdout_buffer.getvalue()
        error = stderr_buffer.getvalue()
        
        if error:
            return {
                "success": False,
                "output": output if output else None,
                "error": error
            }
        
        return {
            "success": True,
            "output": output if output else "执行成功（无输出）",
            "error": None
        }
        
    except TimeoutError as e:
        return {
            "success": False,
            "output": None,
            "error": str(e)
        }
    except Exception as e:
        # 取消超时
        if sys.platform != 'win32':
            signal.alarm(0)
        
        return {
            "success": False,
            "output": None,
            "error": f"执行错误: {str(e)}"
        }


# MCP服务器实现
class PythonExecutorServer:
    """Python执行器MCP服务器"""
    
    def __init__(self):
        self.name = "python-executor"
        self.tools = {
            "execute_python": {
                "name": "execute_python",
                "description": "在安全沙箱中执行Python代码。用于统计计算、数据分析、数学运算等。禁止文件操作、网络请求和系统调用。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "要执行的Python代码。只能使用安全的内置函数和模块（math, statistics, datetime, json, re等）。代码应该包含print()语句来输出结果。"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "超时时间（秒），默认30秒",
                            "default": 30
                        }
                    },
                    "required": ["code"]
                }
            }
        }
    
    def get_tool_list(self) -> list:
        """获取工具列表"""
        return list(self.tools.values())
    
    def call_tool(self, name: str, arguments: dict) -> dict:
        """
        调用工具
        
        Args:
            name: 工具名称
            arguments: 工具参数
            
        Returns:
            MCP格式的结果
        """
        if name == "execute_python":
            code = arguments.get("code", "")
            timeout = arguments.get("timeout", 30)
            
            result = execute_python_safely(code, timeout)
            
            if result["success"]:
                return {
                    "content": [{
                        "type": "text",
                        "text": result["output"]
                    }]
                }
            else:
                return {
                    "content": [{
                        "type": "text",
                        "text": f"执行失败：{result['error']}"
                    }],
                    "isError": True
                }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": f"未知工具: {name}"
                }],
                "isError": True
            }


# MCP stdio协议处理
def run_server():
    """运行MCP服务器（stdio模式）"""
    server = PythonExecutorServer()
    
    # 发送初始化响应
    def send_response(response: dict):
        """发送JSON-RPC响应"""
        print(json.dumps(response, ensure_ascii=False), flush=True)
    
    # 读取请求
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            request = json.loads(line.strip())
            method = request.get("method")
            request_id = request.get("id")
            params = request.get("params", {})
            
            # 处理initialize
            if method == "initialize":
                send_response({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": server.name,
                            "version": "1.0.0"
                        }
                    }
                })
            
            # 处理notifications/initialized
            elif method == "notifications/initialized":
                # 不需要响应
                pass
            
            # 处理tools/list
            elif method == "tools/list":
                send_response({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": server.get_tool_list()
                    }
                })
            
            # 处理tools/call
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_arguments = params.get("arguments", {})
                
                result = server.call_tool(tool_name, tool_arguments)
                
                send_response({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                })
            
            # 处理ping
            elif method == "ping":
                send_response({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {}
                })
            
        except Exception as e:
            # 发送错误响应
            if request_id:
                send_response({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": f"服务器错误: {str(e)}"
                    }
                })


if __name__ == "__main__":
    run_server()
