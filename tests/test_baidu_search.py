"""测试百度搜索服务器"""
import subprocess
import json
import sys


def test_baidu_search():
    """测试百度搜索"""
    print("=" * 60)
    print("🧪 测试百度搜索服务器")
    print("=" * 60)
    
    # 启动百度搜索服务器
    proc = subprocess.Popen(
        [sys.executable, "-m", "app.tools.baidu_search_server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8',
        errors='replace',
        cwd=r"D:\agent-interview-guidance\projects\brainstorm-agents"
    )
    
    try:
        # Step 1: 初始化
        print("\n📡 Step 1: 初始化服务器...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }
        proc.stdin.write(json.dumps(init_request) + "\n")
        proc.stdin.flush()
        
        # 读取响应
        response_line = proc.stdout.readline()
        response = json.loads(response_line)
        print(f"✅ 初始化响应: {json.dumps(response.get('result', {}), ensure_ascii=False)[:100]}...")
        
        # 发送initialized通知
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        proc.stdin.write(json.dumps(initialized_notification) + "\n")
        proc.stdin.flush()
        
        # Step 2: 获取工具列表
        print("\n📡 Step 2: 获取工具列表...")
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        proc.stdin.write(json.dumps(tools_request) + "\n")
        proc.stdin.flush()
        
        response_line = proc.stdout.readline()
        response = json.loads(response_line)
        tools = response.get("result", {}).get("tools", [])
        print(f"✅ 找到 {len(tools)} 个工具:")
        for tool in tools:
            print(f"   - {tool['name']}: {tool.get('description', '')[:50]}...")
        
        # Step 3: 调用百度搜索
        print("\n📡 Step 3: 调用百度搜索...")
        search_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "baidu_search",
                "arguments": {
                    "query": "AI Agent未来发展趋势",
                    "max_results": 3
                }
            }
        }
        proc.stdin.write(json.dumps(search_request) + "\n")
        proc.stdin.flush()
        
        response_line = proc.stdout.readline()
        response = json.loads(response_line)
        
        if "result" in response:
            content = response["result"].get("content", [])
            if content:
                text = content[0].get("text", "")
                print(f"✅ 搜索成功！")
                print(f"\n📄 搜索结果预览（前500字符）:")
                print("-" * 60)
                print(text[:500])
                print("-" * 60)
                
                # 检查结果是否包含有效内容
                if "找到" in text and ("条结果" in text or "结果" in text):
                    print("\n✅ 搜索结果包含有效内容！")
                    return True
                else:
                    print("\n⚠️ 搜索结果可能为空或不完整")
                    return False
        elif "error" in response:
            print(f"❌ 搜索失败: {response['error']}")
            return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        proc.terminate()
    
    return False


if __name__ == "__main__":
    success = test_baidu_search()
    print("\n" + "=" * 60)
    if success:
        print("✅ 百度搜索服务器测试通过！")
    else:
        print("❌ 百度搜索服务器测试失败！")
    print("=" * 60)
