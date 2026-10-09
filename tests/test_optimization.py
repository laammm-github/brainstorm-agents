"""百度搜索查询词优化测试"""
import sys
sys.path.insert(0, '.')

from app.llm.tool_router import ToolRouter

test_cases = [
    ('怎么看待AI Agent岗位的发展前景？', 'AI Agent 岗位发展前景'),
    ('人工智能在未来医疗领域的应用前景如何？', '人工智能 医疗应用前景'),
    ('请分析一下机器学习的优缺点', '机器学习 优缺点'),
]

print('🧪 百度搜索查询词优化测试')
print('='*60)

for i, (orig, expect) in enumerate(test_cases):
    result = ToolRouter.optimize_search_query(orig)
    match = "✅" if result == expect else "⚠️"
    print(f'\n测试{i+1}:')
    print(f'  原始: {orig}')
    print(f'  优化: {result}')
    print(f'  期望: {expect}')
    print(f'  匹配: {match}')
