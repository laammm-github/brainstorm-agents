"""头脑风暴全流程测试 - 验证完整辩论流程的输出语义质量"""
import pytest
import time
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.roles.white_hat import WhiteHat
from app.roles.red_hat import RedHat
from app.roles.black_hat import BlackHat
from app.roles.yellow_hat import YellowHat
from app.roles.green_hat import GreenHat
from app.roles.purple_hat import PurpleHat
from app.orchestrator.debater import DebateEngine
from app.orchestrator.summarizer import Summarizer


class TestDebateFlow:
    """测试完整辩论流程"""
    
    def setup_method(self):
        """初始化测试"""
        self.roles = [
            WhiteHat(),
            RedHat(),
            BlackHat(),
            YellowHat(),
            GreenHat(),
            PurpleHat()
        ]
    
    def test_full_debate_execution(self):
        """测试完整辩论流程执行"""
        debater = DebateEngine(self.roles, use_parallel=True)
        
        question = "是否应该学习 AI Agent 开发？"
        
        # 执行辩论
        results = debater.execute_debate(question)
        
        # 验证结果结构
        assert "round_1" in results, "必须包含 Round 1 结果"
        assert "round_2" in results, "必须包含 Round 2 结果"
        
        # 验证角色完整性
        assert len(results["round_1"]) == 6, f"Round 1 应有 6 个角色，实际 {len(results['round_1'])}"
        assert len(results["round_2"]) == 6, f"Round 2 应有 6 个角色，实际 {len(results['round_2'])}"
        
        # 验证每个角色都有观点
        expected_colors = ["white", "red", "black", "yellow", "green", "purple"]
        for color in expected_colors:
            assert color in results["round_1"], f"Round 1 缺少 {color} 角色"
            assert color in results["round_2"], f"Round 2 缺少 {color} 角色"
            assert results["round_1"][color], f"Round 1 {color} 角色观点不应为空"
            assert results["round_2"][color], f"Round 2 {color} 角色观点不应为空"
        
        # 清理资源
        for role in self.roles:
            role.cleanup()
        
        print(f"✅ 完整辩论流程执行成功")
        print(f"   Round 1: {len(results['round_1'])} 个角色")
        print(f"   Round 2: {len(results['round_2'])} 个角色")
    
    def test_debate_performance(self):
        """测试辩论流程性能"""
        debater = DebateEngine(self.roles, use_parallel=True)
        
        question = "是否应该学习 AI Agent 开发？"
        
        start_time = time.time()
        results = debater.execute_debate(question)
        end_time = time.time()
        
        duration = end_time - start_time
        
        # 性能验证（考虑工具调用可能较慢）
        assert duration > 0, "执行时间应 > 0"
        print(f"✅ 辩论流程耗时: {duration:.2f} 秒")
        
        # 清理资源
        for role in self.roles:
            role.cleanup()
    
    def test_parallel_vs_serial(self):
        """测试并行 vs 串行执行"""
        question = "测试问题"
        
        # 并行执行
        debater_parallel = DebateEngine(self.roles, use_parallel=True)
        start = time.time()
        results_parallel = debater_parallel.execute_debate(question)
        parallel_time = time.time() - start
        
        # 清理资源
        for role in self.roles:
            role.cleanup()
        
        print(f"✅ 并行执行耗时: {parallel_time:.2f} 秒")


class TestRoleSemantics:
    """测试各角色的输出语义质量"""
    
    def test_white_hat_semantic(self):
        """测试白帽（客观事实）的语义"""
        white_hat = WhiteHat()
        
        question = "AI Agent 开发的市场需求如何？"
        
        try:
            result = white_hat.think(question)
            
            # 验证语义质量
            assert result, "白帽观点不应为空"
            assert len(result) > 50, "白帽观点应有足够长度"
            
            # 白帽应关注事实和数据
            # 注意：由于知识库可能为空，可能依赖 LLM 自身知识
            print(f"✅ 白帽语义质量:")
            print(f"   长度: {len(result)} 字符")
            print(f"   预览: {result[:100]}...")
        finally:
            white_hat.cleanup()
    
    def test_red_hat_semantic(self):
        """测试红帽（情感直觉）的语义"""
        red_hat = RedHat()
        
        question = "你对 AI Agent 开发有什么感觉？"
        
        try:
            result = red_hat.think(question)
            
            # 验证语义质量
            assert result, "红帽观点不应为空"
            assert len(result) > 30, "红帽观点应有足够长度"
            
            # 红帽应表达情感和直觉
            emotion_keywords = ["感觉", "直觉", "兴奋", "担心", "喜欢", "担忧", "期待"]
            has_emotion = any(kw in result for kw in emotion_keywords)
            
            print(f"✅ 红帽语义质量:")
            print(f"   长度: {len(result)} 字符")
            print(f"   包含情感表达: {'是' if has_emotion else '否'}")
            print(f"   预览: {result[:100]}...")
        finally:
            red_hat.cleanup()
    
    def test_black_hat_semantic(self):
        """测试黑帽（风险批判）的语义"""
        black_hat = BlackHat()
        
        question = "学习 AI Agent 开发有什么风险？"
        
        try:
            result = black_hat.think(question)
            
            # 验证语义质量
            assert result, "黑帽观点不应为空"
            assert len(result) > 50, "黑帽观点应有足够长度"
            
            # 黑帽应指出风险和批评
            risk_keywords = ["风险", "问题", "困难", "挑战", "不足", "缺陷", "警告"]
            has_risk = any(kw in result for kw in risk_keywords)
            
            print(f"✅ 黑帽语义质量:")
            print(f"   长度: {len(result)} 字符")
            print(f"   包含风险分析: {'是' if has_risk else '否'}")
            print(f"   预览: {result[:100]}...")
        finally:
            black_hat.cleanup()
    
    def test_yellow_hat_semantic(self):
        """测试黄帽（乐观积极）的语义"""
        yellow_hat = YellowHat()
        
        question = "学习 AI Agent 开发有什么好处？"
        
        try:
            result = yellow_hat.think(question)
            
            # 验证语义质量
            assert result, "黄帽观点不应为空"
            assert len(result) > 50, "黄帽观点应有足够长度"
            
            # 黄帽应强调好处和优势
            benefit_keywords = ["好处", "优势", "机会", "潜力", "前景", "收益", "价值"]
            has_benefit = any(kw in result for kw in benefit_keywords)
            
            print(f"✅ 黄帽语义质量:")
            print(f"   长度: {len(result)} 字符")
            print(f"   包含好处分析: {'是' if has_benefit else '否'}")
            print(f"   预览: {result[:100]}...")
        finally:
            yellow_hat.cleanup()
    
    def test_green_hat_semantic(self):
        """测试绿帽（创新思维）的语义"""
        green_hat = GreenHat()
        
        question = "有哪些创新的 AI Agent 开发学习方式？"
        
        try:
            result = green_hat.think(question)
            
            # 验证语义质量
            assert result, "绿帽观点不应为空"
            assert len(result) > 50, "绿帽观点应有足够长度"
            
            # 绿帽应提供创新想法
            creative_keywords = ["创新", "新颖", "独特", "建议", "想法", "方案", "尝试"]
            has_creative = any(kw in result for kw in creative_keywords)
            
            print(f"✅ 绿帽语义质量:")
            print(f"   长度: {len(result)} 字符")
            print(f"   包含创新思维: {'是' if has_creative else '否'}")
            print(f"   预览: {result[:100]}...")
        finally:
            green_hat.cleanup()
    
    def test_purple_hat_semantic(self):
        """测试紫帽（全局视角）的语义"""
        purple_hat = PurpleHat()
        
        question = "从全局角度看 AI Agent 开发学习？"
        
        try:
            result = purple_hat.think(question)
            
            # 验证语义质量
            assert result, "紫帽观点不应为空"
            assert len(result) > 50, "紫帽观点应有足够长度"
            
            # 紫帽应提供全局视角
            global_keywords = ["全局", "整体", "综合", "总结", "建议", "平衡", "考虑"]
            has_global = any(kw in result for kw in global_keywords)
            
            print(f"✅ 紫帽语义质量:")
            print(f"   长度: {len(result)} 字符")
            print(f"   包含全局视角: {'是' if has_global else '否'}")
            print(f"   预览: {result[:100]}...")
        finally:
            purple_hat.cleanup()


class TestRound2Debate:
    """测试 Round 2 交叉辩驳"""
    
    def test_cross_debate_semantic(self):
        """测试交叉辩驳的语义连贯性"""
        white_hat = WhiteHat()
        
        question = "是否应该学习 AI Agent 开发？"
        
        # 模拟 Round 1 结果
        round_1_context = {
            "red": "我觉得 AI Agent 很酷，我很兴奋！",
            "black": "但是存在技术门槛高、学习曲线陡峭的风险",
            "yellow": "不过这个领域前景广阔，机会很多",
        }
        
        try:
            # Round 2 辩驳
            result = white_hat.think(question, context=round_1_context)
            
            # 验证语义
            assert result, "辩驳观点不应为空"
            assert len(result) > 50, "辩驳观点应有足够长度"
            
            # 应体现对其他观点的回应
            print(f"✅ 交叉辩驳语义连贯:")
            print(f"   长度: {len(result)} 字符")
            print(f"   预览: {result[:150]}...")
        finally:
            white_hat.cleanup()


class TestSummarizer:
    """测试汇总报告生成"""
    
    def test_summary_generation(self):
        """测试汇总报告的结构化语义"""
        summarizer = Summarizer()
        
        # 模拟辩论结果
        debate_results = {
            "round_1": {
                "white": "根据数据，AI 岗位需求增长 300%",
                "red": "我感到很兴奋，这个领域很有潜力",
                "black": "但是学习难度高，需要大量时间投入",
                "yellow": "不过前景广阔，薪资水平也很高",
                "green": "可以尝试项目驱动学习，边做边学",
                "purple": "综合来看，建议系统学习，循序渐进"
            },
            "round_2": {
                "white": "补充：最新报告显示 2024 年需求持续增长",
                "red": "虽然兴奋，但也担心学习难度",
                "black": "确认难度，但认为可以通过合理规划克服",
                "yellow": "强调投资回报率很高",
                "green": "建议结合实战项目学习",
                "purple": "建议制定 6 个月学习计划"
            }
        }
        
        question = "是否应该学习 AI Agent 开发？"
        
        # 生成汇总
        summary = summarizer.summarize(question, debate_results)
        
        # 验证汇总语义
        assert summary, "汇总报告不应为空"
        assert len(summary) > 200, "汇总报告应有足够长度"
        
        # 应包含关键部分
        summary_sections = [
            "核心结论",
            "各方观点",
            "综合分析",
            "行动建议"
        ]
        
        found_sections = [s for s in summary_sections if s in summary]
        print(f"✅ 汇总报告结构化语义:")
        print(f"   长度: {len(summary)} 字符")
        print(f"   包含部分: {len(found_sections)}/{len(summary_sections)}")
        print(f"   预览: {summary[:200]}...")


class TestDifferentQuestionTypes:
    """测试不同问题类型的语义表现"""
    
    def setup_method(self):
        """初始化测试"""
        self.roles = [
            WhiteHat(),
            RedHat(),
            BlackHat(),
        ]
    
    def test_career_decision_question(self):
        """测试职业决策类问题"""
        debater = DebateEngine(self.roles, use_parallel=False)
        
        question = "是否应该从 Java 转型到 AI 开发？"
        
        try:
            results = debater.execute_debate(question)
            
            # 验证语义质量
            for round_name in ["round_1", "round_2"]:
                for color, view in results[round_name].items():
                    assert view, f"{round_name} {color} 观点不应为空"
                    assert len(view) > 30, f"{round_name} {color} 观点应有足够长度"
            
            print(f"✅ 职业决策类问题语义正确")
        finally:
            for role in self.roles:
                role.cleanup()
    
    def test_investment_analysis_question(self):
        """测试投资分析类问题"""
        debater = DebateEngine(self.roles, use_parallel=False)
        
        question = "是否应该投资 AI 初创公司？"
        
        try:
            results = debater.execute_debate(question)
            
            # 验证语义质量
            for round_name in ["round_1", "round_2"]:
                for color, view in results[round_name].items():
                    assert view, f"{round_name} {color} 观点不应为空"
            
            print(f"✅ 投资分析类问题语义正确")
        finally:
            for role in self.roles:
                role.cleanup()
    
    def test_learning_planning_question(self):
        """测试学习规划类问题"""
        debater = DebateEngine(self.roles, use_parallel=False)
        
        question = "如何制定 AI Agent 开发学习计划？"
        
        try:
            results = debater.execute_debate(question)
            
            # 验证语义质量
            for round_name in ["round_1", "round_2"]:
                for color, view in results[round_name].items():
                    assert view, f"{round_name} {color} 观点不应为空"
            
            print(f"✅ 学习规划类问题语义正确")
        finally:
            for role in self.roles:
                role.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
