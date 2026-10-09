"""测试头脑风暴功能 - 自动化测试"""
import sys
sys.path.insert(0, '.')

from app.roles.white_hat import WhiteHat
from app.roles.red_hat import RedHat
from app.roles.black_hat import BlackHat
from app.roles.yellow_hat import YellowHat
from app.roles.green_hat import GreenHat
from app.roles.purple_hat import PurpleHat
from app.orchestrator.supervisor import Supervisor
from app.orchestrator.debater import DebateEngine
from app.orchestrator.summarizer import Summarizer

def test_brainstorm():
    """测试头脑风暴功能"""
    print("=" * 70)
    print("🧪 测试头脑风暴功能")
    print("=" * 70)
    
    # 测试问题
    test_questions = [
        "AI Agent未来发展趋势是什么？",
        # "是否应该采用远程办公模式？",
        # "如何提升团队协作效率？"
    ]
    
    for question in test_questions:
        print(f"\n{'='*70}")
        print(f"📝 测试问题: {question}")
        print(f"{'='*70}")
        
        try:
            # 初始化 6 个角色
            print("\n🎭 初始化角色...")
            roles = [
                WhiteHat(),
                RedHat(),
                BlackHat(),
                YellowHat(),
                GreenHat(),
                PurpleHat()
            ]
            print("✅ 6个角色初始化成功")
            
            # 初始化协调者和引擎
            print("\n⚙️ 初始化协调者和辩论引擎...")
            supervisor = Supervisor()
            debater = DebateEngine(roles, use_parallel=True)
            summarizer = Summarizer()
            print("✅ 协调者和引擎初始化成功")
            
            # Step 1: 协调者分类问题
            print(f"\n{'='*70}")
            print("🔍 Step 1: 协调者分析问题类型...")
            print(f"{'='*70}")
            classification = supervisor.classify_problem(question)
            print(f"问题类型：{classification['problem_type']}")
            print(f"使用角色：{', '.join(classification['selected_roles'])}")
            
            # Step 2: 执行辩论
            print(f"\n{'='*70}")
            print("⚔️ Step 2: 执行辩论（并行模式）...")
            print(f"{'='*70}")
            debate_results = debater.execute_debate(question)
            
            print(f"\n✅ 辩论完成，共 {len(debate_results)} 个角色参与")
            for color, result in debate_results.items():
                status = "✅" if result else "❌"
                print(f"  {status} {color}: {'成功' if result else '失败'}")
            
            # Step 3: 生成综合报告
            print(f"\n{'='*70}")
            print("📝 Step 3: 生成综合报告...")
            print(f"{'='*70}")
            report = summarizer.generate_report(debate_results)
            print(report)
            
            print(f"\n{'='*70}")
            print(f"✅ 测试问题完成: {question}")
            print(f"{'='*70}")
            
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print(f"\n{'='*70}")
    print("✅ 所有测试完成！")
    print(f"{'='*70}")
    return True


if __name__ == "__main__":
    success = test_brainstorm()
    sys.exit(0 if success else 1)
