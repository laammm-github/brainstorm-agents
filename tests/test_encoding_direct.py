"""直接测试Bing搜索编码问题"""
import subprocess
import json
import sys
import io

# 强制UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("测试Bing搜索编码...")

# 启动服务器
proc = subprocess.Popen(
    [sys.executable, "-m", "app.tools.bing_search_server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd="D:\\agent-interview-guidance\\projects\\brainstorm-agents"
)

# 包装为UTF-8
proc.stdin = io.TextIOWrapper(proc.stdin, encoding='utf-8', line_buffering=True)
proc.stdout = io.TextIOWrapper(proc.stdout, encoding='utf-8', line_buffering=True)
proc.stderr = io.TextIOWrapper(proc.stderr, encoding='utf-8', line_buffering=True)

def send_request(req_dict):
    """发送请求"""
    # 关键修复：使用ensure_ascii=True，避免中文在GBK终端中被错误编码
    json_str = json.dumps(req_dict, ensure_ascii=True) + "\n"
    print(f"[DEBUG] 发送JSON: {json_str[:150]}", file=sys.stderr)
    proc.stdin.write(json_str)
    proc.stdin.flush()
    
    response_line = proc.stdout.readline()
    if response_line:
        return json.loads(response_line)
    return None

try:
    # 初始化
    send_request({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"}
        }
    })
    
    # 测试搜索
    print("\n发送查询: '人工智能 医疗应用'")
    resp = send_request({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "bing_search",
            "arguments": {
                "query": "人工智能 医疗应用",
                "max_results": 2
            }
        }
    })
    
    if resp and "result" in resp:
        text = resp["result"]["content"][0]["text"]
        # 只显示前200字符
        print(f"\n返回结果:\n{text[:300]}")
        
        # 检查查询词是否正确
        if "人工智能" in text:
            print("\n✅ 查询词编码正确！")
        else:
            print("\n❌ 查询词编码错误！")
            # 打印原始字节
            print(f"原始文本字节: {text[:100].encode('utf-8')}")

finally:
    proc.terminate()
