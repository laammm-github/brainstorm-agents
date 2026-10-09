"""测试百度搜索查询词优化"""
from app.llm.tool_router import ToolRouter


def test_optimize():
    """测试查询词优化"""
    test_cases = [
        # (原始查询, 期望结果)
        ("怎么看待ai agent岗位", "ai agent 岗位"),
        ("AI Agent未来发展趋势是什么？", "AI Agent 未来发展趋势"),
        "人工智能在未来医疗领域的应用前景如何？",
        "怎么评价Python编程语言？",
        "请分析一下机器学习技术的优缺点",
        "你认为深度学习怎么样？",
        "介绍一下大语言模型的应用场景",
        "说说Agent技术",
        "AI",  # 极短查询
        "什么是Transformer架构？",
        "如何看待ChatGPT技术的发展前景？",
    ]
    
    print("=" * 70)
    print("🧪 百度搜索查询词优化测试")
    print("=" * 70)
    
    for i, query in enumerate(test_cases, 1):
        original = query
        optimized = ToolRouter.optimize_search_query(query)
        
        print(f"\n测试 {i}:")
        print(f"  原始: '{original}'")
        print(f"  优化: '{optimized}'")
        print(f"  长度: {len(original)} -> {len(optimized)}")
        
        # 验证优化效果
        checks = []
        if len(optimized) <= 20:
            checks.append("✅ 长度合理")
        else:
            checks.append("⚠️ 长度过长")
            
        if '怎么' not in optimized and '如何' not in optimized and '什么' not in optimized:
            checks.append("✅ 疑问词已去除")
        else:
            checks.append("⚠️ 仍包含疑问词")
            
        if len(optimized.strip()) >= 3:
            checks.append("✅ 最小长度满足")
        else:
            checks.append("❌ 长度过短")
        
        print(f"  验证: {', '.join(checks)}")
    
    print("\n" + "=" * 70)
    print("✅ 测试完成")
    print("=" * 70)


if __name__ == "__main__":
    test_optimize()
