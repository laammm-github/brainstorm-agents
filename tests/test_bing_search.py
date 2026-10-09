"""测试Bing搜索MCP服务器"""
import subprocess
import json
import sys
import time
import io

# 强制设置标准输出为UTF-8（解决Windows终端GBK编码问题）
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 70)
print("测试Bing搜索MCP服务器")
print("=" * 70)

# 启动服务器
print("\n📡 启动Bing搜索服务器...")
proc = subprocess.Popen(
    [sys.executable, "-m", "app.tools.bing_search_server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding='utf-8',
    errors='replace',
    cwd="D:\\agent-interview-guidance\\projects\\brainstorm-agents"
)

def send_request(req_dict):
    """发送请求并获取响应"""
    proc.stdin.write(json.dumps(req_dict, ensure_ascii=False) + "\n")
    proc.stdin.flush()
    
    # 读取响应
    response_line = proc.stdout.readline()
    if response_line:
        return json.loads(response_line)
    return None

try:
    # 1. 初始化
    print("\n1️⃣ 初始化服务器...")
    resp = send_request({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"}
        }
    })
    
    if resp and "result" in resp:
        server_name = resp["result"].get("serverInfo", {}).get("name", "unknown")
        print(f"   ✅ 初始化成功: {server_name}")
    else:
        print(f"   ❌ 初始化失败: {resp}")
        sys.exit(1)
    
    # 2. 获取工具列表
    print("\n2️⃣ 获取工具列表...")
    resp = send_request({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list"
    })
    
    if resp and "result" in resp and "tools" in resp["result"]:
        tools = resp["result"]["tools"]
        print(f"   ✅ 找到 {len(tools)} 个工具:")
        for tool in tools:
            print(f"      - {tool['name']}: {tool.get('description', '')[:60]}...")
    else:
        print(f"   ⚠️ 工具列表异常: {resp}")
    
    # 3. 测试搜索 - AI Agent发展趋势
    print("\n3️⃣ 测试搜索: AI Agent 发展趋势")
    
    resp = send_request({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "bing_search",
            "arguments": {
                "query": "AI Agent 发展趋势",
                "max_results": 3
            }
        }
    })
    
    if resp and "result" in resp:
        content = resp["result"].get("content", [])
        if content:
            text = content[0].get("text", "")
            
            # 检测是否真的有搜索结果
            if "找到" in text and "条结果" in text:
                print(f"   ✅ 搜索成功！")
                print(f"\n📊 搜索结果:")
                print(f"   {text}")
                
                # 统计实际结果数量
                if "\n1. " in text:
                    result_count = text.count("\n") - text.count("\n   ") 
                    print(f"\n   📈 包含约 {result_count} 个搜索结果")
            elif "未找到" in text:
                print(f"   ❌ 搜索失败: 未找到结果")
                print(f"\n   返回内容: {text[:300]}")
            else:
                print(f"   ⚠️ 搜索结果异常")
                print(f"\n   返回内容: {text[:500]}")
        else:
            print(f"   ⚠️ 搜索结果为空")
    else:
        error = resp.get("error", {}) if resp else "无响应"
        print(f"   ❌ 搜索失败: {error}")
    
    # 4. 测试搜索 - 中文问题
    print("\n" + "=" * 70)
    print("4️⃣ 测试搜索: 人工智能在医疗领域的应用")
    
    resp = send_request({
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "bing_search",
            "arguments": {
                "query": "人工智能 医疗应用",
                "max_results": 3
            }
        }
    })
    
    if resp and "result" in resp:
        content = resp["result"].get("content", [])
        if content:
            text = content[0].get("text", "")
            
            if "找到" in text and "条结果" in text:
                print(f"   ✅ 搜索成功！")
                print(f"\n📊 搜索结果:")
                print(f"   {text}")
            elif "未找到" in text:
                print(f"   ❌ 搜索失败: 未找到结果")
                print(f"\n   返回内容: {text[:300]}")
            else:
                print(f"   ⚠️ 搜索结果异常")
                print(f"\n   返回内容: {text[:500]}")
        else:
            print(f"   ⚠️ 搜索结果为空")
    else:
        error = resp.get("error", {}) if resp else "无响应"
        print(f"   ❌ 搜索失败: {error}")
    
    # 5. 最终总结
    print("\n" + "=" * 70)
    print("✅ Bing搜索MCP服务器测试完成！")
    print("=" * 70)
    
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except:
        proc.kill()
