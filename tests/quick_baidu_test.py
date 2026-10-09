"""快速测试百度搜索功能"""
import subprocess
import json
import sys

print("=" * 70)
print("快速测试百度搜索MCP服务器")
print("=" * 70)

# 启动服务器
print("\n📡 启动百度搜索服务器...")
proc = subprocess.Popen(
    ["npx.cmd", "-y", "baidu-search-mcp"],
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
    return json.loads(proc.stdout.readline())

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
    
    if "result" in resp:
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
    
    if "result" in resp and "tools" in resp["result"]:
        tools = resp["result"]["tools"]
        print(f"   ✅ 找到 {len(tools)} 个工具:")
        for tool in tools:
            print(f"      - {tool['name']}: {tool.get('description', '')[:50]}...")
    else:
        print(f"   ⚠️ 工具列表异常: {resp}")
    
    # 3. 测试搜索
    print("\n3️⃣ 测试搜索功能...")
    print("   查询: AI Agent 发展趋势")
    
    resp = send_request({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "baidu_search",
            "arguments": {
                "query": "AI Agent 发展趋势",
                "max_results": 3
            }
        }
    })
    
    if "result" in resp:
        content = resp["result"].get("content", [])
        if content:
            text = content[0].get("text", "")
            print(f"   ✅ 搜索成功！")
            print(f"\n📊 搜索结果预览:")
            print(f"   {text[:300]}...")
            
            # 统计结果
            if "title" in text.lower():
                title_count = text.lower().count("title")
                print(f"\n   📈 包含 {title_count} 个搜索结果")
        else:
            print(f"   ⚠️ 搜索结果为空")
    else:
        print(f"   ❌ 搜索失败: {resp.get('error', '未知错误')}")
    
    print("\n" + "=" * 70)
    print("✅ 百度搜索MCP服务器测试完成！")
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
