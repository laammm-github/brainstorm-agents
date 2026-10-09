"""测试 time 服务器"""
import subprocess
import json
import time

print("=" * 60)
print("测试 Time MCP 服务器")
print("=" * 60)

# 启动进程
print("\n1. 启动 time 服务器...")
process = subprocess.Popen(
    ["python", "-m", "app.tools.time_server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding='utf-8'
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
time.sleep(1)

# 读取响应
response_line = process.stdout.readline()
print(f"响应: {response_line.strip()}")

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
response = json.loads(response_line)
print(f"可用工具: {json.dumps(response['result']['tools'], indent=2, ensure_ascii=False)}")

# 发送 tools/call 请求
print("\n4. 调用 get_current_time 工具...")
request = {
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
        "name": "get_current_time",
        "arguments": {"timezone": "Asia/Shanghai"}
    }
}

process.stdin.write(json.dumps(request) + "\n")
process.stdin.flush()
time.sleep(1)

response_line = process.stdout.readline()
response = json.loads(response_line)
print(f"当前时间: {response['result']['content'][0]['text']}")

# 清理
print("\n5. 清理...")
process.terminate()
print("✅ 测试完成")
