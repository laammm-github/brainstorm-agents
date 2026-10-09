"""MCP 时间服务器 - 提供时间查询工具"""
import sys
import json
from datetime import datetime
import zoneinfo


def send_response(result):
    """发送 JSON-RPC 响应"""
    response = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": result
    }
    print(json.dumps(response), flush=True)


def handle_request(request_str):
    """处理 JSON-RPC 请求"""
    try:
        request = json.loads(request_str)
    except json.JSONDecodeError:
        return
    
    method = request.get("method")
    request_id = request.get("id")
    
    # 处理 initialize
    if method == "initialize":
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "time-server",
                    "version": "1.0.0"
                }
            }
        }
        print(json.dumps(response), flush=True)
    
    # 处理 tools/list
    elif method == "tools/list":
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": [
                    {
                        "name": "get_current_time",
                        "description": "获取当前时间，支持指定时区",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "timezone": {
                                    "type": "string",
                                    "description": "时区名称，如 'Asia/Shanghai', 'UTC', 'America/New_York'",
                                    "default": "Asia/Shanghai"
                                }
                            }
                        }
                    }
                ]
            }
        }
        print(json.dumps(response), flush=True)
    
    # 处理 tools/call
    elif method == "tools/call":
        tool_name = request["params"]["name"]
        arguments = request["params"].get("arguments", {})
        
        if tool_name == "get_current_time":
            timezone = arguments.get("timezone", "Asia/Shanghai")
            try:
                tz = zoneinfo.ZoneInfo(timezone)
                now = datetime.now(tz)
                time_str = now.strftime("%Y-%m-%d %H:%M:%S %Z")
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"当前时间（{timezone}）：{time_str}"
                            }
                        ]
                    }
                }
            except Exception as e:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"时间查询失败：{str(e)}"
                            }
                        ]
                    }
                }
            
            print(json.dumps(response), flush=True)
    
    # 处理 notifications/initialized
    elif method == "notifications/initialized":
        # 不需要响应
        pass


def main():
    """主函数 - 从 stdin 读取请求"""
    # 缓冲模式，逐行读取
    for line in sys.stdin:
        line = line.strip()
        if line:
            handle_request(line)


if __name__ == "__main__":
    main()
