"""
Bing搜索MCP服务器 - 提供可靠的搜索能力
使用requests + BeautifulSoup实现，无需API密钥
Bing搜索在国内可用，且反爬虫机制相对宽松
"""
import json
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urlparse


class BingSearchServer:
    """Bing搜索服务器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        # 设置编码
        self.session.trust_env = False
    
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
                    "name": "bing-search-server",
                    "version": "1.0.0"
                }
            })
        
        # 处理tools/list
        elif method == "tools/list":
            return self._respond(request_id, {
                "tools": [
                    {
                        "name": "bing_search",
                        "description": "使用Bing搜索网页内容。适合搜索中英文信息、新闻、技术文章等。返回搜索结果列表，包含标题、URL和摘要。",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "搜索关键词或问题"
                                },
                                "max_results": {
                                    "type": "integer",
                                    "description": "最大返回结果数量（默认5，最大10）"
                                }
                            },
                            "required": ["query"]
                        }
                    }
                ]
            })
        
        # 处理tools/call
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            if tool_name == "bing_search":
                return self._handle_bing_search(request_id, tool_args)
            else:
                return self._error(request_id, -32601, f"Tool '{tool_name}' not found")
        
        # 处理notifications/initialized
        elif method == "notifications/initialized":
            return None
        
        else:
            return self._error(request_id, -32601, f"Method '{method}' not found")
    
    def _handle_bing_search(self, request_id, args):
        """处理Bing搜索请求"""
        query = args.get("query", "")
        max_results = min(args.get("max_results", 5), 10)  # 最多10条
        
        # 调试：打印接收到的原始查询词
        import sys
        print(f"[DEBUG] 接收到的query: {repr(query)}", file=sys.stderr)
        print(f"[DEBUG] query编码: {query.encode('utf-8')}", file=sys.stderr)
        
        if not query:
            return self._error(request_id, -32602, "查询词不能为空")
        
        try:
            # 构建Bing搜索URL（使用更准确的参数）
            # 注意：query需要正确的URL编码
            encoded_query = quote(query, safe='', encoding='utf-8')
            search_url = f"https://cn.bing.com/search?q={encoded_query}&count={max_results}&mkt=zh-CN"
            
            # 调试：打印最终URL
            print(f"[DEBUG] 搜索URL: {search_url}", file=sys.stderr)
            
            # 发送请求
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            # 正确检测并设置编码
            if response.encoding == 'ISO-8859-1':
                # Bing可能返回ISO-8859-1，需要转换为UTF-8
                response.encoding = response.apparent_encoding or 'utf-8'
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取搜索结果
            results = []
            
            # Bing的搜索结果在li.b_algo中
            search_items = soup.find_all('li', class_='b_algo')
            
            if not search_items:
                # 备用选择器
                search_items = soup.find_all('div', class_='b_algo')
            
            for item in search_items[:max_results]:
                # 提取标题
                title_tag = item.find('h2')
                if not title_tag:
                    title_tag = item.find('a')
                
                if not title_tag:
                    continue
                
                title = title_tag.get_text(strip=True)
                
                # 提取链接
                link_tag = item.find('a', href=True)
                if not link_tag:
                    continue
                
                url = link_tag.get('href', '')
                
                # 提取摘要
                abstract_tag = item.find('p')
                if not abstract_tag:
                    abstract_tag = item.find('div', class_='b_caption')
                    if abstract_tag:
                        abstract_tag = abstract_tag.find('p')
                
                abstract = abstract_tag.get_text(strip=True) if abstract_tag else ''
                
                # 过滤无效结果
                if title and url and len(title) > 5 and not url.startswith('#'):
                    results.append({
                        'title': title,
                        'url': url,
                        'abstract': abstract
                    })
            
            # 格式化结果
            if results:
                result_text = f"[Bing搜索] \"{query}\" 找到 {len(results)} 条结果:\n\n"
                for i, result in enumerate(results, 1):
                    result_text += f"{i}. {result['title']}\n"
                    if result['url']:
                        result_text += f"   链接: {result['url']}\n"
                    if result['abstract']:
                        result_text += f"   摘要: {result['abstract'][:200]}...\n"
                    result_text += "\n"
            else:
                # 即使没有结果，也返回搜索建议
                result_text = f"[Bing搜索] \"{query}\" 未找到结构化结果。\n\n"
                result_text += "建议尝试以下关键词：\n"
                result_text += f"- {query} 最新\n"
                result_text += f"- {query} 教程\n"
                result_text += f"- {query} 2024\n"
                result_text += f"- {query} 是什么\n"
            
            return self._respond(request_id, {
                "content": [
                    {
                        "type": "text",
                        "text": result_text
                    }
                ]
            })
        
        except requests.exceptions.RequestException as e:
            # 网络错误时返回友好提示
            error_text = f"⚠️ Bing搜索请求失败: {str(e)}\n\n"
            error_text += "可能的原因：\n"
            error_text += "- 网络连接问题\n"
            error_text += "- Bing搜索暂时不可用\n"
            error_text += "- 请求被限制\n\n"
            error_text += "建议：\n"
            error_text += "1. 检查网络连接\n"
            error_text += "2. 稍后重试\n"
            error_text += "3. 尝试使用其他关键词"
            
            return self._respond(request_id, {
                "content": [
                    {
                        "type": "text",
                        "text": error_text
                    }
                ]
            })
        
        except Exception as e:
            return self._error(request_id, -32603, f"搜索失败: {str(e)}")
    
    def _respond(self, request_id, result):
        """构建成功响应"""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
        return response
    
    def _error(self, request_id, code, message):
        """构建错误响应"""
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
    import io
    # 设置标准输入输出为UTF-8
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    server = BingSearchServer()
    
    # 读取输入并处理请求
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            
            # 调试：打印接收到的请求
            if request.get("method") == "tools/call":
                params = request.get("params", {})
                args = params.get("arguments", {})
                query = args.get("query", "")
                print(f"[DEBUG] 收到查询: {repr(query)}", file=sys.stderr)
                print(f"[DEBUG] 查询字节: {query.encode('utf-8')}", file=sys.stderr)
            
            response = server.handle_request(request)
            
            if response:
                # 关键修复：使用ensure_ascii=True避免编码问题
                print(json.dumps(response, ensure_ascii=True))
                sys.stdout.flush()
        
        except json.JSONDecodeError:
            continue
        except KeyboardInterrupt:
            break
        except Exception as e:
            # 发送错误响应
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {str(e)}"
                }
            }
            print(json.dumps(error_response, ensure_ascii=True))
            sys.stdout.flush()


if __name__ == "__main__":
    main()
