"""
测试流式响应 (SSE) 功能
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8001"

def test_sse_stream():
    """测试 SSE 流式响应"""
    print("=" * 80)
    print("🎭 测试流式响应 (SSE)")
    print("=" * 80)
    print()
    
    question = "是否应该学习AI Agent开发？"
    print(f"📝 问题: {question}")
    print()
    
    try:
        # 发起 SSE 请求
        response = requests.post(
            f"{BASE_URL}/brainstorm/stream",
            json={"question": question, "max_rounds": 2},
            stream=True,
            timeout=120
        )
        
        print(f"✅ 连接成功 - 状态码: {response.status_code}")
        print()
        print("📊 接收事件流:")
        print("-" * 80)
        
        event_count = 0
        events_received = []
        
        # 读取流式数据
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                
                if line.startswith('event:'):
                    event_type = line[6:].strip()
                    events_received.append(event_type)
                    event_count += 1
                    print(f"\n📨 事件 #{event_count}: {event_type}")
                
                elif line.startswith('data:'):
                    data_str = line[5:].strip()
                    if data_str:
                        try:
                            data = json.loads(data_str)
                            
                            # 根据事件类型显示不同信息
                            if 'status' in data and 'message' in data:
                                print(f"   💬 {data['message']}")
                            elif 'role_name' in data:
                                print(f"   ✓ {data['role_name']} 完成")
                            elif 'round' in data and 'results' in data:
                                result_count = len(data['results'])
                                print(f"   🎯 Round {data['round']} 完成 - {result_count} 个角色")
                            elif 'final_report' in data:
                                report_length = len(data['final_report'])
                                print(f"   📝 综合报告生成 - {report_length} 字符")
                                print(f"   🎉 完成！共接收 {event_count} 个事件")
                            elif 'problem_type' in data:
                                print(f"   🔍 问题类型: {data['problem_type']}")
                        except json.JSONDecodeError:
                            pass
        
        print()
        print("-" * 80)
        print()
        print("📈 测试统计:")
        print(f"  - 总事件数: {event_count}")
        print(f"  - 事件类型: {', '.join(set(events_received))}")
        print()
        
        if event_count > 0:
            print("✅ SSE 流式响应测试通过！")
            return True
        else:
            print("❌ 未接收到任何事件")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_sse_events():
    """测试 SSE 事件完整性"""
    print("\n" + "=" * 80)
    print("🔍 测试 SSE 事件完整性")
    print("=" * 80)
    print()
    
    try:
        response = requests.post(
            f"{BASE_URL}/brainstorm/stream",
            json={"question": "测试", "max_rounds": 1},
            stream=True,
            timeout=120
        )
        
        events = []
        has_classification = False
        has_round_complete = False
        has_complete = False
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('event:'):
                    events.append(line[6:].strip())
                elif line.startswith('data:'):
                    data_str = line[5:].strip()
                    if data_str:
                        try:
                            data = json.loads(data_str)
                            if 'problem_type' in data:
                                has_classification = True
                            if 'round' in data and 'results' in data:
                                has_round_complete = True
                            if 'final_report' in data:
                                has_complete = True
                        except:
                            pass
        
        # 验证关键事件
        print("📋 事件验证:")
        checks = [
            ("classification", has_classification, "问题分类事件"),
            ("round_complete", has_round_complete, "辩论完成事件"),
            ("complete", has_complete, "最终完成事件")
        ]
        
        all_passed = True
        for event_name, has_event, description in checks:
            status = "✅" if has_event else "❌"
            print(f"  {status} {description}: {'有' if has_event else '无'}")
            if not has_event:
                all_passed = False
        
        print()
        if all_passed:
            print("✅ 所有关键事件都存在！")
            return True
        else:
            print("⚠️  部分事件缺失")
            return False
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def main():
    """主测试函数"""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "🎭 SSE 流式响应测试套件" + " " * 33 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    # 检查服务是否运行
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        if r.status_code != 200:
            print("❌ 后端服务未运行")
            return False
        print("✅ 后端服务运行正常\n")
    except:
        print("❌ 无法连接到后端服务")
        return False
    
    results = []
    
    # 测试 1: SSE 流式响应
    results.append(("SSE 流式响应", test_sse_stream()))
    
    # 测试 2: SSE 事件完整性
    results.append(("SSE 事件完整性", test_sse_events()))
    
    # 总结
    print()
    print("=" * 80)
    print("📊 测试总结")
    print("=" * 80)
    
    passed = sum(1 for _, status in results if status)
    total = len(results)
    
    for name, status in results:
        icon = "✅" if status else "❌"
        print(f"  {icon} {name}")
    
    print()
    print(f"总计: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
    print("=" * 80)
    
    if passed == total:
        print("\n🎉 所有 SSE 测试通过！")
        return True
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
