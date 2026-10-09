"""
百度搜索MCP服务器 - 提供中文搜索能力
使用requests + BeautifulSoup实现，无需API密钥
"""
import json
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urlparse


class BaiduSearchServer:
    """百度搜索服务器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
    
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
                    "name": "baidu-search-server",
                    "version": "1.0.0"
                }
            })
        
        # 处理tools/list
        elif method == "tools/list":
            return self._respond(request_id, {
                "tools": [
                    {
                        "name": "baidu_search",
                        "description": "使用百度搜索网页内容。适合搜索中文信息、新闻、技术文章等。返回搜索结果列表，包含标题、URL和摘要。",
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
            
            if tool_name == "baidu_search":
                return self._handle_baidu_search(request_id, tool_args)
            else:
                return self._error(request_id, -32601, f"Tool '{tool_name}' not found")
        
        # 处理notifications/initialized
        elif method == "notifications/initialized":
            return None
        
        else:
            return self._error(request_id, -32601, f"Method '{method}' not found")
    
    def _handle_baidu_search(self, request_id, args):
        """处理百度搜索请求"""
        query = args.get("query", "")
        max_results = min(args.get("max_results", 5), 10)  # 最多10条
        
        if not query:
            return self._error(request_id, -32602, "查询词不能为空")
        
        try:
            # 构建百度搜索URL
            search_url = f"https://www.baidu.com/s?wd={quote(query)}&rn={max_results}"
            
            # 发送请求
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取搜索结果
            results = []
            search_items = soup.find_all('div', class_='result c-container')
            
            for item in search_items[:max_results]:
                # 提取标题
                title_tag = item.find('h3')
                if not title_tag:
                    continue
                
                title = title_tag.get_text(strip=True)
                
                # 提取链接
                link_tag = title_tag.find('a')
                if not link_tag:
                    continue
                
                url = link_tag.get('href', '')
                
                # 提取摘要
                abstract_tag = item.find('span', class_='content-right_8Tb2Q')
                if not abstract_tag:
                    abstract_tag = item.find('div', class_='c-abstract')
                
                abstract = abstract_tag.get_text(strip=True) if abstract_tag else ''
                
                results.append({
                    'title': title,
                    'url': url,
                    'abstract': abstract
                })
            
            # 如果没有找到结果，尝试备用选择器
            if not results:
                results = self._fallback_parse(soup, max_results)
            
            # 格式化结果
            if results:
                result_text = f"[百度搜索] \"{query}\" 找到 {len(results)} 条结果:\n\n"
                for i, result in enumerate(results, 1):
                    result_text += f"{i}. {result['title']}\n"
                    if result['url']:
                        result_text += f"   链接: {result['url']}\n"
                    if result['abstract']:
                        result_text += f"   摘要: {result['abstract'][:150]}...\n"
                    result_text += "\n"
            else:
                # 即使没有结果，也返回搜索建议
                result_text = f"[百度搜索] \"{query}\" 未找到结构化结果。\n\n"
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
            error_text = f"⚠️ 百度搜索请求失败: {str(e)}\n\n"
            error_text += "可能的原因：\n"
            error_text += "- 网络连接问题\n"
            error_text += "- 百度搜索暂时不可用\n"
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
    
    def _fallback_parse(self, soup, max_results):
        """备用解析方法"""
        results = []
        
        # 尝试更通用的选择器
        all_links = soup.find_all('a', href=True)
        
        for link in all_links[:max_results * 2]:  # 多取一些，过滤后可能减少
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # 过滤有效的搜索结果链接
            if (text and 
                len(text) > 10 and 
                'baidu.com' not in href and
                href.startswith('http')):
                
                results.append({
                    'title': text[:100],
                    'url': href,
                    'abstract': ''
                })
                
                if len(results) >= max_results:
                    break
        
        return results
    
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
    server = BaiduSearchServer()
    
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
