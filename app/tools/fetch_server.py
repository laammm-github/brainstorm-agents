"""
网页提取 MCP 服务器

提取网页内容
"""

import json
import sys
from urllib.request import urlopen, Request
from urllib.parse import urlparse
from html.parser import HTMLParser
import ssl


class SimpleHTMLParser(HTMLParser):
    """简单的HTML解析器"""
    
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip_tags = {'script', 'style', 'noscript'}
        self.in_skip_tag = False
    
    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags:
            self.in_skip_tag = True
    
    def handle_endtag(self, tag):
        if tag in self.skip_tags:
            self.in_skip_tag = False
    
    def handle_data(self, data):
        if not self.in_skip_tag:
            text = data.strip()
            if text:
                self.text.append(text)
    
    def get_text(self):
        return '\n'.join(self.text)


class FetchServer:
    """网页提取服务器"""
    
    def __init__(self):
        pass
    
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
                    "name": "fetch-server",
                    "version": "1.0.0"
                }
            })
        
        elif method == "tools/list":
            return self._respond(request_id, {
                "tools": [
                    {
                        "name": "fetch_url",
                        "description": "获取指定URL的网页内容。提取网页的文本内容，去除HTML标签。",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "url": {
                                    "type": "string",
                                    "description": "要获取内容的网页URL"
                                }
                            },
                            "required": ["url"]
                        }
                    }
                ]
            })
        
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            if tool_name == "fetch_url":
                return self._handle_fetch_url(request_id, tool_args)
            else:
                return self._error(request_id, -32601, f"Tool '{tool_name}' not found")
        
        elif method == "notifications/initialized":
            return None
        
        else:
            return self._error(request_id, -32601, f"Method '{method}' not found")
    
    def _handle_fetch_url(self, request_id, args):
        """处理网页提取请求"""
        url = args.get("url", "")
        
        if not url:
            return self._error(request_id, -32602, "URL参数不能为空")
        
        try:
            # 验证URL格式
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return self._error(request_id, -32602, "URL格式不正确")
            
            # 创建请求
            req = Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Fetch-MCP-Server/1.0')
            
            # 发送请求（忽略SSL证书验证错误）
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with urlopen(req, timeout=10, context=context) as response:
                # 读取内容
                html_content = response.read()
                
                # 尝试解码
                try:
                    html_text = html_content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        html_text = html_content.decode('gbk')
                    except UnicodeDecodeError:
                        html_text = html_content.decode('latin-1')
                
                # 解析HTML
                parser = SimpleHTMLParser()
                parser.feed(html_text)
                text_content = parser.get_text()
                
                # 限制长度
                max_length = 5000
                if len(text_content) > max_length:
                    text_content = text_content[:max_length] + "\n\n[内容已截断...]"
                
                content = f"🌐 网页内容提取成功\n\n"
                content += f"**URL**: {url}\n"
                content += f"**标题**: {parsed.netloc}\n"
                content += f"**长度**: {len(text_content)} 字符\n\n"
                content += f"**内容**:\n{text_content}"
                
                return self._respond(request_id, {
                    "content": [
                        {
                            "type": "text",
                            "text": content
                        }
                    ]
                })
        
        except Exception as e:
            error_msg = f"获取网页内容失败: {str(e)}"
            return self._error(request_id, -32603, error_msg)
    
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
    server = FetchServer()
    
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
