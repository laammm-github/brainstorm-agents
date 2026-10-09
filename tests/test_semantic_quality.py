"""语义质量评估测试 - 验证输出的专业性、准确性和连贯性"""
import pytest
from pathlib import Path
import sys
import re

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.roles.white_hat import WhiteHat
from app.roles.black_hat import BlackHat
from app.roles.yellow_hat import YellowHat


class TestHallucinationDetection:
    """测试幻觉检测"""
    
    def test_no_fabricated_statistics(self):
        """测试不应编造统计数据"""
        white_hat = WhiteHat()
        
        question = "AI 市场的具体数据是什么？"
        
        try:
            result = white_hat.think(question)
            
            # 检测可能的幻觉
            # 如果包含具体数字，应该有来源说明
            numbers = re.findall(r'\d+%', result)
            
            if numbers:
                # 有具体数字，应注明来源
                has_source = any(kw in result for kw in ["来源", "报告", "根据", "显示"])
                
                print(f"⚠️  发现 {len(numbers)} 个具体百分比")
                if has_source:
                    print(f"   ✅ 已注明来源")
                else:
                    print(f"   ⚠️  未注明来源（可能是幻觉）")
            
            print(f"✅ 幻觉检测完成")
            print(f"   内容预览: {result[:150]}...")
        finally:
            white_hat.cleanup()
    
    def test_no_fabricated_quotes(self):
        """测试不应编造引用"""
        black_hat = BlackHat()
        
        question = "有哪些专家认为 AI 有风险？"
        
        try:
            result = black_hat.think(question)
            
            # 检测可能的编造引用
            quote_patterns = [
                r'["「"].*?["」]',  # 引用符号
                r'他说.*?认为',
                r'专家表示'
            ]
            
            has_quotes = any(re.search(pattern, result) for pattern in quote_patterns)
            
            if has_quotes:
                # 有引用，应验证真实性
                has_source = any(kw in result for kw in ["来源", "报告", "文章", "链接"])
                
                print(f"⚠️  发现引用内容")
                if has_source:
                    print(f"   ✅ 已注明来源")
                else:
                    print(f"   ⚠️  未注明来源（可能是编造）")
            
            print(f"✅ 引用检测完成")
        finally:
            black_hat.cleanup()


class TestFactualAccuracy:
    """测试事实准确性"""
    
    def test_white_hat_factual_basis(self):
        """测试白帽的事实依据"""
        white_hat = WhiteHat()
        
        question = "AI Agent 开发需要哪些技能？"
        
        try:
            result = white_hat.think(question)
            
            # 验证事实依据
            # 应包含具体技能而非模糊描述
            skill_keywords = ["Python", "LLM", "机器学习", "深度学习", "编程", "框架"]
            has_skills = any(kw in result for kw in skill_keywords)
            
            assert has_skills or len(result) > 100, \
                "白帽应提供具体技能或详细说明"
            
            print(f"✅ 白帽事实依据:")
            print(f"   包含具体技能: {'是' if has_skills else '否'}")
            print(f"   内容长度: {len(result)} 字符")
        finally:
            white_hat.cleanup()
    
    def test_consistency_across_roles(self):
        """测试跨角色的一致性"""
        white_hat = WhiteHat()
        black_hat = BlackHat()
        yellow_hat = YellowHat()
        
        question = "AI Agent 开发的学习难度如何？"
        
        try:
            white_result = white_hat.think(question)
            black_result = black_hat.think(question)
            yellow_result = yellow_hat.think(question)
            
            # 验证基本事实一致
            # 例如：如果白帽说需要 6 个月，黑帽和黄帽不应说只需要 1 周
            time_patterns = [
                (r'\d+\s*个?月', '月'),
                (r'\d+\s*周', '周'),
                (r'\d+\s*年', '年'),
            ]
            
            times_mentioned = []
            for pattern, unit in time_patterns:
                for result in [white_result, black_result, yellow_result]:
                    matches = re.findall(pattern, result)
                    if matches:
                        times_mentioned.append((unit, matches))
            
            print(f"✅ 跨角色一致性检查:")
            print(f"   时间提及: {times_mentioned}")
            
            # 清理
            white_hat.cleanup()
            black_hat.cleanup()
            yellow_hat.cleanup()
        except Exception as e:
            # 确保清理
            for hat in [white_hat, black_hat, yellow_hat]:
                try:
                    hat.cleanup()
                except:
                    pass
            raise


class TestLogicalCoherence:
    """测试逻辑连贯性"""
    
    def test_argument_structure(self):
        """测试论点结构的逻辑性"""
        black_hat = BlackHat()
        
        question = "学习 AI Agent 开发有什么挑战？"
        
        try:
            result = black_hat.think(question)
            
            # 验证逻辑结构
            # 应有论点、论据、结论
            has_structure = False
            
            structure_indicators = [
                ["首先", "其次", "最后"],
                ["一方面", "另一方面"],
                ["原因", "因此"],
                ["虽然", "但是"],
            ]
            
            for indicators in structure_indicators:
                if all(kw in result for kw in indicators):
                    has_structure = True
                    break
            
            print(f"✅ 论点结构逻辑性:")
            print(f"   有结构化论述: {'是' if has_structure else '否'}")
            print(f"   内容长度: {len(result)} 字符")
            print(f"   预览: {result[:150]}...")
        finally:
            black_hat.cleanup()
    
    def test_no_contradiction(self):
        """测试无自相矛盾"""
        yellow_hat = YellowHat()
        
        question = "AI Agent 开发的优势是什么？"
        
        try:
            result = yellow_hat.think(question)
            
            # 检测自相矛盾
            contradictions = [
                ("简单", "困难"),
                ("快速", "缓慢"),
                ("便宜", "昂贵"),
            ]
            
            found_contradictions = []
            for word1, word2 in contradictions:
                if word1 in result and word2 in result:
                    # 可能有转折，需要进一步判断
                    # 简单检测：如果两个词都出现，标记为可能矛盾
                    found_contradictions.append((word1, word2))
            
            if found_contradictions:
                print(f"⚠️  发现可能的矛盾: {found_contradictions}")
                print(f"   (需要人工验证是否为合理转折)")
            else:
                print(f"✅ 无自相矛盾")
            
            print(f"   内容预览: {result[:150]}...")
        finally:
            yellow_hat.cleanup()


class TestSourceAttribution:
    """测试信息来源标注"""
    
    def test_tool_result_attribution(self):
        """测试工具结果的信息来源标注"""
        white_hat = WhiteHat()
        
        question = "2024 年 AI 岗位需求数据"
        
        try:
            result = white_hat.think(question)
            
            # 如果使用工具，应标注来源
            if "工具调用结果" in result:
                has_source = any(kw in result for kw in ["来源", "报告", "文档"])
                
                assert has_source, "工具结果应标注来源"
                
                print(f"✅ 工具结果信息来源标注:")
                print(f"   已标注来源: {'是' if has_source else '否'}")
            else:
                print(f"ℹ️  未使用工具调用")
            
            print(f"   内容预览: {result[:150]}...")
        finally:
            white_hat.cleanup()


class TestResponseCompleteness:
    """测试响应完整性"""
    
    def test_comprehensive_answer(self):
        """测试回答的全面性"""
        purple_hat = PurpleHat()
        
        question = "是否应该学习 AI Agent 开发？"
        
        try:
            result = purple_hat.think(question)
            
            # 验证全面性
            # 应从多个角度分析
            perspective_keywords = [
                "技术",
                "市场",
                "职业",
                "学习",
                "成本",
                "收益",
            ]
            
            perspectives_covered = sum(1 for kw in perspective_keywords if kw in result)
            
            print(f"✅ 回答全面性:")
            print(f"   覆盖角度: {perspectives_covered}/{len(perspective_keywords)}")
            print(f"   内容长度: {len(result)} 字符")
            print(f"   预览: {result[:150]}...")
        finally:
            purple_hat.cleanup()
    
    def test_actionable_advice(self):
        """测试建议的可操作性"""
        green_hat = GreenHat()
        
        question = "如何开始学习 AI Agent 开发？"
        
        try:
            result = green_hat.think(question)
            
            # 验证建议的可操作性
            # 应包含具体行动步骤
            action_keywords = ["建议", "可以", "应该", "第一步", "首先", "然后", "最后"]
            has_action = any(kw in result for kw in action_keywords)
            
            print(f"✅ 建议可操作性:")
            print(f"   包含行动建议: {'是' if has_action else '否'}")
            print(f"   内容预览: {result[:150]}...")
        finally:
            green_hat.cleanup()


class TestSemanticQualityMetrics:
    """语义质量指标评估"""
    
    def test_readability(self):
        """测试可读性"""
        white_hat = WhiteHat()
        
        question = "解释 AI Agent 是什么"
        
        try:
            result = white_hat.think(question)
            
            # 简单可读性指标
            sentences = result.split('。')
            avg_sentence_length = len(result) / max(len(sentences), 1)
            
            # 理想句长：20-50 字符
            readability = "良好" if 20 <= avg_sentence_length <= 50 else "一般"
            
            print(f"✅ 可读性评估:")
            print(f"   平均句长: {avg_sentence_length:.1f} 字符")
            print(f"   可读性: {readability}")
        finally:
            white_hat.cleanup()
    
    def test_professional_terminology(self):
        """测试专业术语使用"""
        black_hat = BlackHat()
        
        question = "AI Agent 开发的技术挑战"
        
        try:
            result = black_hat.think(question)
            
            # 检测专业术语
            tech_terms = [
                "LLM", "API", "框架", "模型",
                "训练", "推理", "部署", "优化",
                "Python", "Agent", "Multi-Agent"
            ]
            
            terms_used = [term for term in tech_terms if term in result]
            
            print(f"✅ 专业术语使用:")
            print(f"   使用术语: {len(terms_used)}/{len(tech_terms)}")
            print(f"   术语列表: {', '.join(terms_used[:5])}")
        finally:
            black_hat.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
