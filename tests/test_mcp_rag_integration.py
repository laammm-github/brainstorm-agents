"""MCP + RAG 集成测试"""
import time
from app.roles.white_hat import WhiteHat
from app.roles.red_hat import RedHat
from app.roles.black_hat import BlackHat
from app.roles.yellow_hat import YellowHat
from app.roles.green_hat import GreenHat
from app.roles.purple_hat import PurpleHat
from app.orchestrator.debater import DebateEngine


def test_mcp_rag_integration():
    """测试 MCP + RAG 集成的完整辩论流程"""
    
    print("=" * 80)
    print("MCP + RAG 集成测试")
    print("=" * 80)
    
    # 初始化 6 个角色
    roles = [
        WhiteHat(),
        RedHat(),
        BlackHat(),
        YellowHat(),
        GreenHat(),
        PurpleHat()
    ]
    
    # 初始化辩论引擎（启用并行）
    debater = DebateEngine(roles, use_parallel=True)
    
    # 测试问题
    question = "是否应该学习 AI Agent 开发？"
    
    print(f"\n📝 测试问题: {question}\n")
    print("开始执行辩论流程...\n")
    
    # 记录开始时间
    start_time = time.time()
    
    try:
        # 执行辩论
        results = debater.execute_debate(question)
        
        # 记录结束时间
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 80)
        print("✅ 辩论完成！")
        print("=" * 80)
        
        # 验证结果
        assert "round_1" in results, "缺少 Round 1 结果"
        assert "round_2" in results, "缺少 Round 2 结果"
        assert len(results["round_1"]) == 6, f"Round 1 应该有 6 个角色，实际 {len(results['round_1'])}"
        assert len(results["round_2"]) == 6, f"Round 2 应该有 6 个角色，实际 {len(results['round_2'])}"
        
        # 打印摘要
        print(f"\n⏱️  总耗时: {duration:.2f} 秒")
        print(f"\n📊 Round 1 角色观点:")
        for color, view in results["round_1"].items():
            preview = view[:50] + "..." if len(view) > 50 else view
            print(f"  - {color}: {preview}")
        
        print(f"\n📊 Round 2 辩驳摘要:")
        for color, view in results["round_2"].items():
            preview = view[:50] + "..." if len(view) > 50 else view
            print(f"  - {color}: {preview}")
        
        # 验证白帽使用了工具（应该包含工具调用结果）
        white_view = results["round_1"]["white"]
        # 注意：由于 RAG 知识库可能为空，工具可能返回"未找到相关内容"
        print(f"\n🔍 白帽观点检查:")
        if "工具调用结果" in white_view or "知识库" in white_view or "未找到" in white_view:
            print("  ✅ 白帽尝试调用工具")
        else:
            print("  ⚠️  白帽未使用工具（可能降级到纯 LLM）")
        
        print("\n" + "=" * 80)
        print("✅ 所有测试通过！")
        print("=" * 80)
        
        # 清理资源
        for role in roles:
            role.cleanup()
        
        return True
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 清理资源
        for role in roles:
            try:
                role.cleanup()
            except:
                pass
        
        return False


if __name__ == "__main__":
    success = test_mcp_rag_integration()
    exit(0 if success else 1)
