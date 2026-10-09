"""
文件系统MCP服务器 - 提供文件读写操作
替代 npm 包 @modelcontextprotocol/server-filesystem
"""
import json
import sys
import os
from pathlib import Path


class FilesystemServer:
    """文件系统服务器"""
    
    def __init__(self):
        self.base_dir = Path("./knowledge_base")
        self.base_dir.mkdir(exist_ok=True)
    
    def handle_request(self, request):
        """处理JSON-RPC请求"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        # 处理initialize
        if method == "initialize":
            return self._respond(request_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "filesystem-server",
                    "version": "1.0.0"
                }
            })
        
        # 处理tools/list
        elif method == "tools/list":
            return self._respond(request_id, {
                "tools": [
                    {
                        "name": "read_file",
                        "description": "读取文件内容。可以读取文本文件的内容并返回。",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "文件路径（相对于knowledge_base目录）"
                                }
                            },
                            "required": ["path"]
                        }
                    },
                    {
                        "name": "write_file",
                        "description": "写入文件内容。可以创建新文件或覆盖现有文件。",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "文件路径（相对于knowledge_base目录）"
                                },
                                "content": {
                                    "type": "string",
                                    "description": "要写入的文件内容"
                                }
                            },
                            "required": ["path", "content"]
                        }
                    },
                    {
                        "name": "list_files",
                        "description": "列出目录中的文件。可以查看knowledge_base目录中的所有文件。",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "目录路径（相对于knowledge_base目录，默认为根目录）"
                                }
                            },
                            "required": []
                        }
                    }
                ]
            })
        
        # 处理tools/call
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            if tool_name == "read_file":
                return self._handle_read_file(request_id, tool_args)
            elif tool_name == "write_file":
                return self._handle_write_file(request_id, tool_args)
            elif tool_name == "list_files":
                return self._handle_list_files(request_id, tool_args)
            else:
                return self._error(request_id, -32601, f"Tool '{tool_name}' not found")
        
        # 处理notifications/initialized
        elif method == "notifications/initialized":
            return None
        
        else:
            return self._error(request_id, -32601, f"Method '{method}' not found")
    
    def _handle_read_file(self, request_id, args):
        """处理读取文件请求"""
        path = args.get("path", "")
        
        if not path:
            return self._error(request_id, -32602, "路径参数不能为空")
        
        try:
            # 确保路径在base_dir内
            file_path = (self.base_dir / path).resolve()
            if not str(file_path).startswith(str(self.base_dir.resolve())):
                return self._error(request_id, -32602, "不允许访问base_dir之外的文件")
            
            if not file_path.exists():
                return self._respond(request_id, {
                    "content": [
                        {
                            "type": "text",
                            "text": f"文件不存在: {path}"
                        }
                    ]
                })
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self._respond(request_id, {
                "content": [
                    {
                        "type": "text",
                        "text": f"[文件] {path}:\n\n{content[:2000]}"  # 限制2000字符
                    }
                ]
            })
        
        except Exception as e:
            return self._error(request_id, -32603, f"读取文件失败: {str(e)}")
    
    def _handle_write_file(self, request_id, args):
        """处理写入文件请求"""
        path = args.get("path", "")
        content = args.get("content", "")
        
        if not path:
            return self._error(request_id, -32602, "路径参数不能为空")
        
        try:
            # 确保路径在base_dir内
            file_path = (self.base_dir / path).resolve()
            if not str(file_path).startswith(str(self.base_dir.resolve())):
                return self._error(request_id, -32602, "不允许访问base_dir之外的文件")
            
            # 创建目录（如果不存在）
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return self._respond(request_id, {
                "content": [
                    {
                        "type": "text",
                        "text": f"[写入成功] {path} ({len(content)} 字符)"
                    }
                ]
            })
        
        except Exception as e:
            return self._error(request_id, -32603, f"写入文件失败: {str(e)}")
    
    def _handle_list_files(self, request_id, args):
        """处理列出文件请求"""
        path = args.get("path", ".")
        
        try:
            # 确保路径在base_dir内
            dir_path = (self.base_dir / path).resolve()
            if not str(dir_path).startswith(str(self.base_dir.resolve())):
                return self._error(request_id, -32602, "不允许访问base_dir之外的目录")
            
            if not dir_path.exists():
                return self._respond(request_id, {
                    "content": [
                        {
                            "type": "text",
                            "text": f"目录不存在: {path}"
                        }
                    ]
                })
            
            # 列出文件
            files = []
            for item in dir_path.iterdir():
                if item.is_file():
                    files.append(f"[F] {item.name}")
                elif item.is_dir():
                    files.append(f"[D] {item.name}/")
            
            if not files:
                text = f"[目录] 目录为空: {path}"
            else:
                text = f"[目录] {path}:\n" + "\n".join(files)
            
            return self._respond(request_id, {
                "content": [
                    {
                        "type": "text",
                        "text": text
                    }
                ]
            })
        
        except Exception as e:
            return self._error(request_id, -32603, f"列出文件失败: {str(e)}")
    
    def _respond(self, request_id, result):
        """发送JSON-RPC响应"""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
        sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
        sys.stdout.flush()
        return response
    
    def _error(self, request_id, code, message):
        """发送JSON-RPC错误响应"""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }
        sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
        sys.stdout.flush()
        return response


def main():
    """主函数"""
    server = FilesystemServer()
    
    # 读取标准输入
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            request = json.loads(line)
            server.handle_request(request)
        except json.JSONDecodeError:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
