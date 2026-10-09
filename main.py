"""头脑风暴智能体 - 命令行入口"""
from app.roles.white_hat import WhiteHat
from app.roles.red_hat import RedHat
from app.roles.black_hat import BlackHat
from app.roles.yellow_hat import YellowHat
from app.roles.green_hat import GreenHat
from app.roles.purple_hat import PurpleHat
from app.orchestrator.supervisor import Supervisor
from app.orchestrator.debater import DebateEngine
from app.orchestrator.summarizer import Summarizer


def main():
    """主函数"""
    print("=" * 60)
    print("🎭 头脑风暴智能体已启动（输入 exit 退出）")
    print("基于六顶思考帽的 Multi-Agent 辩证推理系统")
    print("=" * 60)
    
    # 初始化 6 个角色
    roles = [
        WhiteHat(),
        RedHat(),
        BlackHat(),
        YellowHat(),
        GreenHat(),
        PurpleHat()
    ]
    
    # 初始化协调者和引擎（启用并行执行 + 角色日志缓冲区）
    supervisor = Supervisor()
    debater = DebateEngine(roles, use_parallel=True)  # 启用并行执行
    summarizer = Summarizer()
    
    while True:
        question = input("\n💬 请输入你的问题：")
        
        if question.strip().lower() in ("exit", "quit"):
            print("\n👋 再见！")
            break
        
        if not question.strip():
            continue
        
        print("\n" + "=" * 60)
        print("🔍 协调者分析问题类型...")
        
        # Step 1: 协调者分类问题
        classification = supervisor.classify_problem(question)
        print(f"问题类型：{classification['problem_type']}")
        print(f"使用角色：{', '.join(classification['selected_roles'])}")
        
        # Step 2: 执行辩论
        print("\n" + "=" * 60)
        debate_results = debater.execute_debate(question)
        
        # Step 3: 生成综合报告
        print("\n" + "=" * 60)
        print("📝 生成综合报告...\n")
        report = summarizer.generate_report(debate_results)
        print(report)
        
        print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
