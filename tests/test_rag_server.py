"""测试 RAG MCP 服务器"""
import subprocess
import json
import time
import sys

print("=" * 60)
print("测试 RAG MCP 服务器")
print("=" * 60)

# 启动进程
print("\n1. 启动 RAG 服务器...")
process = subprocess.Popen(
    [sys.executable, "-m", "app.tools.rag_server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding='utf-8',
    cwd=r"D:\agent-interview-guidance\projects\brainstorm-agents"
)
print("✅ 进程启动成功")

# 发送 initialize 请求
print("\n2. 发送 initialize 请求...")
request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test-client", "version": "1.0.0"}
    }
}

process.stdin.write(json.dumps(request) + "\n")
process.stdin.flush()
time.sleep(2)

# 读取响应
response_line = process.stdout.readline()
if response_line:
    print(f"✅ 收到响应")
    try:
        response = json.loads(response_line)
        print(f"   响应: {json.dumps(response, indent=2, ensure_ascii=False)[:200]}...")
    except:
        print(f"   原始响应: {response_line.strip()}")
else:
    print("❌ 未收到响应")
    stderr = process.stderr.read()
    print(f"   stderr: {stderr}")

# 发送 tools/list 请求
print("\n3. 发送 tools/list 请求...")
request = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
}

process.stdin.write(json.dumps(request) + "\n")
process.stdin.flush()
time.sleep(1)

response_line = process.stdout.readline()
if response_line:
    print(f"✅ 收到响应")
    try:
        response = json.loads(response_line)
        tools = response.get("result", {}).get("tools", [])
        print(f"   可用工具数: {len(tools)}")
        for tool in tools:
            print(f"   - {tool['name']}: {tool['description']}")
    except Exception as e:
        print(f"   解析失败: {e}")
        print(f"   原始响应: {response_line.strip()[:200]}")
else:
    print("❌ 未收到响应")

# 发送 tools/call 请求 - 测试 search_knowledge_base
print("\n4. 调用 search_knowledge_base 工具...")
request = {
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
        "name": "search_knowledge_base",
        "arguments": {"query": "AI Agent", "top_k": 2}
    }
}

process.stdin.write(json.dumps(request) + "\n")
process.stdin.flush()
time.sleep(2)

response_line = process.stdout.readline()
if response_line:
    print(f"✅ 收到响应")
    try:
        response = json.loads(response_line)
        content = response.get("result", {}).get("content", [])
        if content:
            text = content[0].get("text", "")
            print(f"   检索结果: {text[:150]}...")
        else:
            print(f"   无内容")
    except Exception as e:
        print(f"   解析失败: {e}")
        print(f"   原始响应: {response_line.strip()[:200]}")
else:
    print("❌ 未收到响应")

# 发送 initialized 通知
print("\n5. 发送 initialized 通知...")
request = {
    "jsonrpc": "2.0",
    "method": "notifications/initialized",
    "params": {}
}

process.stdin.write(json.dumps(request) + "\n")
process.stdin.flush()
print("✅ 通知已发送")

# 清理
print("\n6. 清理...")
process.terminate()
try:
    process.wait(timeout=3)
    print("✅ 进程已终止")
except:
    process.kill()
    print("⚠️ 强制终止进程")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
