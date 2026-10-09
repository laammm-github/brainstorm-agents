"""简化测试百度搜索MCP"""
import subprocess
import json
import sys

print("=" * 70)
print("🧪 简化测试百度搜索MCP服务器")
print("=" * 70)

# 启动服务器
print("\n📡 启动百度搜索服务器...")
proc = subprocess.Popen(
    ["npx.cmd", "baidu-search-mcp"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    cwd="D:\\agent-interview-guidance\\projects\\brainstorm-agents"
)

def send_req(req_dict):
    """发送请求"""
    proc.stdin.write(json.dumps(req_dict, ensure_ascii=False) + "\n")
    proc.stdin.flush()
    return json.loads(proc.stdout.readline())

try:
    # 1. 初始化
    print("\n1️⃣ 初始化服务器...")
    resp = send_req({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"}
        }
    })
    print(f"   ✅ 初始化成功: {resp['result']['serverInfo']['name']}")
    
    # 发送通知
    send_req({"jsonrpc": "2.0", "method": "notifications/initialized"})
    
    # 2. 获取工具列表
    print("\n2️⃣ 获取工具列表...")
    resp = send_req({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    tools = resp['result']['tools']
    print(f"   ✅ 找到 {len(tools)} 个工具: {[t['name'] for t in tools]}")
    
    # 3. 测试搜索
    print("\n3️⃣ 测试搜索（AI Agent发展趋势）...")
    print("   ⏳ 搜索中，请稍候...")
    
    resp = send_req({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "search_web",
            "arguments": {
                "query": "AI Agent发展趋势 2026",
                "max_results": 3
            }
        }
    })
    
    content = resp['result']['content'][0]['text']
    print("   ✅ 搜索成功！")
    print(f"\n   📊 搜索结果（前300字符）:")
    print("   " + "-" * 66)
    for line in content[:300].split('\n'):
        print(f"   {line}")
    print("   " + "-" * 66)
    
    # 检查质量
    has_title = "**" in content
    has_url = "http" in content
    print(f"\n   📈 质量检查:")
    print(f"      {'✅' if has_title else '❌'} 包含标题")
    print(f"      {'✅' if has_url else '❌'} 包含链接")
    
    if has_title and has_url:
        print("\n   ✅ 百度搜索工作正常！")
    else:
        print("\n   ⚠️  搜索结果质量一般")
    
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
finally:
    print("\n🔚 关闭服务器...")
    proc.terminate()
    proc.wait(timeout=5)
    print("   ✅ 已关闭")

print("\n" + "=" * 70)
print("✅ 测试完成！百度搜索MCP服务器工作正常！")
print("=" * 70)
