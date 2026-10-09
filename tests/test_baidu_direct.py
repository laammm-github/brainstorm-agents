"""直接测试百度搜索MCP服务器"""
import sys
import os
import json
import subprocess
import time

sys.path.insert(0, '.')

from app.llm.tool_router import ToolRouter

# 测试用例
test_queries = [
    "怎么看待AI Agent岗位的发展前景？",
    "AI Agent",
    "人工智能发展趋势",
]

print("="*60)
print("🧪 百度搜索MCP直接测试")
print("="*60)

for i, query in enumerate(test_queries):
    print(f"\n{'='*60}")
    print(f"测试{i+1}: {query}")
    print(f"{'='*60}")
    
    # 优化查询词
    optimized = ToolRouter.optimize_search_query(query)
    print(f"优化后: {optimized}")
    
    # 启动百度搜索MCP服务器
    try:
        # 使用Python启动MCP服务器
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        # 启动子进程
        proc = subprocess.Popen(
            ['python', '-m', 'baidu_search_mcp'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            encoding='utf-8'
        )
        
        # 发送工具列表请求
        tools_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        proc.stdin.write(json.dumps(tools_request) + '\n')
        proc.stdin.flush()
        
        time.sleep(1)
        
        # 发送工具调用请求
        call_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "baidu_search",
                "arguments": {
                    "query": optimized,
                    "max_results": 3
                }
            }
        }
        proc.stdin.write(json.dumps(call_request) + '\n')
        proc.stdin.flush()
        
        time.sleep(3)
        
        # 读取结果
        proc.stdin.close()
        stdout, stderr = proc.communicate(timeout=5)
        
        if stdout:
            print(f"\n✅ 搜索结果:")
            print(stdout[:500])  # 打印前500个字符
        else:
            print(f"\n❌ 无输出")
            if stderr:
                print(f"错误: {stderr[:200]}")
                
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")

print("\n" + "="*60)
print("测试完成")
print("="*60)
