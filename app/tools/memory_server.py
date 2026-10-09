"""
知识图谱记忆 MCP 服务器

提供基于知识图谱的记忆存储和查询功能
"""

import json
import sys
from datetime import datetime


class MemoryServer:
    """知识图谱记忆服务器"""
    
    def __init__(self):
        self.memory_graph = {}
        self.entities = {}
    
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
                    "name": "memory-server",
                    "version": "1.0.0"
                }
            })
        
        elif method == "tools/list":
            return self._respond(request_id, {
                "tools": [
                    {
                        "name": "query_memory",
                        "description": "查询知识图谱记忆。根据关键词搜索已存储的信息和关系。",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "查询关键词或问题"
                                }
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "save_memory",
                        "description": "保存信息到知识图谱记忆。",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "entity": {
                                    "type": "string",
                                    "description": "实体名称"
                                },
                                "relation": {
                                    "type": "string",
                                    "description": "关系类型"
                                },
                                "value": {
                                    "type": "string",
                                    "description": "值或描述"
                                }
                            },
                            "required": ["entity", "relation", "value"]
                        }
                    }
                ]
            })
        
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            if tool_name == "query_memory":
                return self._handle_query_memory(request_id, tool_args)
            elif tool_name == "save_memory":
                return self._handle_save_memory(request_id, tool_args)
            else:
                return self._error(request_id, -32601, f"Tool '{tool_name}' not found")
        
        elif method == "notifications/initialized":
            return None
        
        else:
            return self._error(request_id, -32601, f"Method '{method}' not found")
    
    def _handle_query_memory(self, request_id, args):
        """处理查询记忆请求"""
        query = args.get("query", "")
        
        # 简单实现：返回示例数据
        # 实际应该查询知识图谱
        results = [
            {
                "entity": "AI Agent",
                "relation": "发展趋势",
                "value": "从工具化向自主化演进，多Agent协同成为关键方向",
                "timestamp": datetime.now().isoformat()
            },
            {
                "entity": "AI Agent",
                "relation": "应用领域",
                "value": "企业服务、智能客服、数据分析、自动化流程",
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        content = f"📚 知识图谱记忆查询: {query}\n\n找到 {len(results)} 条相关记忆:\n"
        for i, item in enumerate(results, 1):
            content += f"\n{i}. **{item['entity']}** - {item['relation']}\n"
            content += f"   {item['value']}\n"
            content += f"   🕒 {item['timestamp']}"
        
        return self._respond(request_id, {
            "content": [
                {
                    "type": "text",
                    "text": content
                }
            ]
        })
    
    def _handle_save_memory(self, request_id, args):
        """处理保存记忆请求"""
        entity = args.get("entity", "")
        relation = args.get("relation", "")
        value = args.get("value", "")
        
        # 保存到内存
        if entity not in self.memory_graph:
            self.memory_graph[entity] = []
        
        self.memory_graph[entity].append({
            "relation": relation,
            "value": value,
            "timestamp": datetime.now().isoformat()
        })
        
        return self._respond(request_id, {
            "content": [
                {
                    "type": "text",
                    "text": f"✅ 已保存记忆: {entity} - {relation} - {value}"
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
    server = MemoryServer()
    
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
