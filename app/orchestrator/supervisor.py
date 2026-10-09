"""协调者 Agent（蓝帽）- 问题分类 + 任务分发"""
from app.llm.adapter import chat
from app.config import settings


class Supervisor:
    """协调者 Agent - 负责问题分类和角色分发"""
    
    SYSTEM_PROMPT = """你是头脑风暴的协调者（蓝帽）。你的职责是：
1. 分析用户提出的问题类型（决策类/认知类/情感类/创意类）
2. 根据问题类型选择合适的思考帽角色组合
3. 将问题分发给各个角色 Agent
4. 收集各角色的观点并触发辩论流程
5. 最终调用汇总 Agent 生成综合报告

问题分类标准：
- 决策类：需要做选择的问题 → 使用全部 6 帽
- 认知类：需要理解的问题 → 减少红帽，增加白帽
- 情感类：需要表达感受的问题 → 增加红帽
- 创意类：需要创新想法的问题 → 增加绿帽

请严格按照上述逻辑进行分析和分发。
"""
    
    def classify_problem(self, question: str) -> dict:
        """分类问题并返回角色组合"""
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"请分类以下问题并推荐使用的思考帽：{question}"}
        ]
        
        response = chat(messages, use_strong_model=True)
        return self._parse_classification(response)
    
    def _parse_classification(self, response: str) -> dict:
        """解析分类结果"""
        # 简化实现：默认使用全部 6 帽
        return {
            "problem_type": "decision",
            "selected_roles": ["white", "red", "black", "yellow", "green", "purple"],
            "analysis": response
        }
