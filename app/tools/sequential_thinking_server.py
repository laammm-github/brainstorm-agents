"""
顺序思考 MCP 服务器

提供结构化的逐步思考能力
"""

import json
import sys
from datetime import datetime


class SequentialThinkingServer:
    """顺序思考服务器"""
    
    def __init__(self):
        self.thought_count = 0
    
    def handle_request(self, request):
        """处理JSON-RPC请求"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        if method == "initialize":
            return self._respond(request_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "sequential-thinking-server",
                    "version": "1.0.0"
                }
            })
        
        elif method == "tools/list":
            return self._respond(request_id, {
                "tools": [
                    {
                        "name": "sequential_thinking",
                        "description": "进行结构化的顺序思考。将复杂问题分解为多个思考步骤，逐步分析。",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "thought": {
                                    "type": "string",
                                    "description": "当前思考内容"
                                },
                                "thought_number": {
                                    "type": "integer",
                                    "description": "思考步骤编号"
                                },
                                "total_thoughts": {
                                    "type": "integer",
                                    "description": "预计总思考步骤数"
                                },
                                "next_thought_needed": {
                                    "type": "boolean",
                                    "description": "是否需要继续思考"
                                }
                            },
                            "required": ["thought"]
                        }
                    }
                ]
            })
        
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            if tool_name == "sequential_thinking":
                return self._handle_sequential_thinking(request_id, tool_args)
            else:
                return self._error(request_id, -32601, f"Tool '{tool_name}' not found")
        
        elif method == "notifications/initialized":
            return None
        
        else:
            return self._error(request_id, -32601, f"Method '{method}' not found")
    
    def _handle_sequential_thinking(self, request_id, args):
        """处理顺序思考请求"""
        thought = args.get("thought", "")
        thought_number = args.get("thought_number", 1)
        total_thoughts = args.get("total_thoughts", 5)
        next_thought_needed = args.get("next_thought_needed", True)
        
        self.thought_count += 1
        
        # 生成结构化的思考输出
        content = f"🧠 顺序思考步骤 {thought_number}/{total_thoughts}\n\n"
        content += f"**思考内容**: {thought}\n\n"
        
        if next_thought_needed:
            content += f"💡 提示: 已进行 {thought_number} 步思考，还需 {total_thoughts - thought_number} 步"
        else:
            content += f"✅ 思考完成，共 {thought_number} 步"
        
        content += f"\n\n🕒 时间: {datetime.now().isoformat()}"
        
        return self._respond(request_id, {
            "content": [
                {
                    "type": "text",
                    "text": content
                }
            ]
        })
    
    def _respond(self, request_id, result):
        """创建JSON-RPC响应"""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
        return response
    
    def _error(self, request_id, code, message):
        """创建JSON-RPC错误响应"""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }
        return response


def main():
    """主函数"""
    server = SequentialThinkingServer()
    
    # 读取标准输入
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            request = json.loads(line.strip())
            response = server.handle_request(request)
            
            if response:
                sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
                sys.stdout.flush()
        
        except KeyboardInterrupt:
            break
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
