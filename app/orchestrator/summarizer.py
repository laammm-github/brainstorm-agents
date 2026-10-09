"""汇总 Agent - 冲突点标注 · 共识提炼 · 行动建议"""
from app.llm.adapter import chat
from app.config import settings


class Summarizer:
    """汇总 Agent - 生成结构化综合报告"""
    
    SYSTEM_PROMPT = """你是头脑风暴的汇总者。你的任务是将各角色的观点整合成结构化报告。

输出格式必须严格遵循：

## 📊 各角色核心观点摘要
- 白帽：...
- 红帽：...
- ...

## ⚔️ 争议焦点
（存在根本分歧的问题）
1. ...
2. ...

## ✅ 共识区
（所有角色一致认同的结论）
1. ...
2. ...

## 💡 行动建议
（优先级排序）
1. 【高优先级】...
2. 【中优先级】...
3. 【低优先级】...

## ❓ 遗留问题
（需要进一步收集信息才能判断的点）
1. ...

注意：
- 保持客观中立，不偏向任何角色
- 突出关键洞察
- 行动建议要具体可执行
"""
    
    def generate_report(self, debate_results: dict) -> str:
        """
        生成综合报告
        
        Args:
            debate_results: 辩论结果字典
            
        Returns:
            结构化报告文本
        """
        # 格式化输入
        input_text = self._format_debate_results(debate_results)
        
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": input_text}
        ]
        
        return chat(messages, use_strong_model=True)
    
    def _format_debate_results(self, results: dict) -> str:
        """格式化辩论结果为文本"""
        lines = ["请根据以下辩论结果生成综合报告：\n"]
        
        lines.append("## Round 1: 独立思考")
        for color, view in results.get("round_1", {}).items():
            lines.append(f"\n【{color}】\n{view}")
        
        if results.get("round_2"):
            lines.append("\n\n## Round 2: 交叉辩驳")
            for color, rebuttal in results["round_2"].items():
                lines.append(f"\n【{color}】\n{rebuttal}")
        
        return "\n".join(lines)
