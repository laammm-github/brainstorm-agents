"""测试 RAG 服务器初始化"""
import subprocess
import json
import time
import sys

print("启动 RAG 服务器...")
process = subprocess.Popen(
    [sys.executable, "-m", "app.tools.rag_server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding='utf-8',
    errors='replace',  # 添加错误处理
    cwd=r"D:\agent-interview-guidance\projects\brainstorm-agents"
)

time.sleep(2)

# 发送 initialize
print("发送 initialize...")
request = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0.0"}}}
process.stdin.write(json.dumps(request) + "\n")
process.stdin.flush()

time.sleep(2)
response = process.stdout.readline()
print("响应:", response.strip())

# 发送 tools/list
print("\n发送 tools/list...")
request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
process.stdin.write(json.dumps(request) + "\n")
process.stdin.flush()

time.sleep(1)
response = process.stdout.readline()
print("响应:", response.strip())

# 调用工具
print("\n调用 search_knowledge_base...")
request = {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "search_knowledge_base", "arguments": {"query": "test"}}}
process.stdin.write(json.dumps(request) + "\n")
process.stdin.flush()

time.sleep(2)
response = process.stdout.readline()
print("响应:", response.strip())

process.terminate()
print("\n✅ 测试完成")
