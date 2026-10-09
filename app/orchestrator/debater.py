"""辩论引擎 - Round 1 独立思考 → Round 2 交叉辩驳（支持并行优化）"""
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.roles.base import ThinkingHat, enable_role_buffer, flush_role_buffer
from app.config import settings


class DebateEngine:
    """多轮辩论引擎（支持并行执行）"""
    
    def __init__(self, roles: list[ThinkingHat], use_parallel: bool = True):
        self.roles = roles
        self.max_rounds = settings.max_debate_rounds
        self.use_parallel = use_parallel  # 是否启用并行优化
    
    def execute_debate(self, question: str) -> dict:
        """
        执行完整辩论流程
        
        Args:
            question: 用户问题
            
        Returns:
            辩论结果字典
        """
        results = {
            "round_1": {},  # 独立思考
            "round_2": {},  # 交叉辩驳
        }
        
        # Round 1: 独立思考（看不到其他人观点）
        print("🎭 Round 1: 独立思考...")
        if self.use_parallel:
            results["round_1"] = self._execute_parallel(question, context=None, round_name="Round 1")
        else:
            for role in self.roles:
                print(f"  - {role.name}思考中...")
                view = role.think(question, use_strong_model=False)
                results["round_1"][role.color] = view
        
        # Round 2: 交叉辩驳（看到他人观点后反驳）
        if self.max_rounds >= 2:
            print("\n🎭 Round 2: 交叉辩驳...")
            if self.use_parallel:
                results["round_2"] = self._execute_parallel(
                    question, 
                    context=results["round_1"], 
                    round_name="Round 2"
                )
            else:
                for role in self.roles:
                    print(f"  - {role.name}辩驳中...")
                    rebuttal = role.think(
                        question, 
                        context=results["round_1"],
                        use_strong_model=False
                    )
                    results["round_2"][role.color] = rebuttal
        
        return results
    
    def _execute_parallel(self, question: str, context: dict, round_name: str) -> dict:
        """
        并行执行多个角色的思考（使用角色日志缓冲区）
        
        Args:
            question: 用户问题
            context: 上下文（Round 1 为 None，Round 2 为 Round 1 的结果）
            round_name: 轮次名称（用于打印）
            
        Returns:
            角色观点字典 {color: view}
        """
        results = {}
        
        # 打印开始信息
        for role in self.roles:
            action = "思考中" if context is None else "辩驳中"
            print(f"  - {role.name}{action}...")
        
        # 使用线程池并行执行
        with ThreadPoolExecutor(max_workers=len(self.roles)) as executor:
            # 提交所有任务（使用显式循环避免闭包变量问题）
            future_to_role = {}
            for role in self.roles:
                # 为每个角色启用日志缓冲区
                enable_role_buffer(role.name)
                
                future = executor.submit(
                    role.think, 
                    question, 
                    context=context, 
                    use_strong_model=False
                )
                future_to_role[future] = role
            
            # 收集结果（按完成顺序）
            completed_futures = []
            for future in as_completed(future_to_role):
                role = future_to_role[future]
                try:
                    view = future.result()
                    results[role.color] = view
                    completed_futures.append((role, None))
                except Exception as e:
                    completed_futures.append((role, e))
                    results[role.color] = f"执行失败: {str(e)}"
        
        # 按原始角色顺序输出日志缓冲区
        for role in self.roles:
            flush_role_buffer(role.name)
            # 打印完成状态
            role_result = results.get(role.color)
            if role_result and "执行失败" in str(role_result):
                print(f"  ⚠️ {role.name}执行失败: {role_result}")
            else:
                print(f"  ✓ {role.name}完成")
        
        return results
    
    def _format_other_views(self, views: dict) -> str:
        """格式化其他角色的观点"""
        formatted = []
        for color, view in views.items():
            formatted.append(f"【{color}】{view[:200]}...")  # 截断避免过长
        return "\n\n".join(formatted)
