"""六顶思考帽角色基类（增强工具调用）"""
import threading
import io
from abc import ABC, abstractmethod
from app.llm.adapter import chat
from app.llm.mcp_manager import MCPServerManager
from app.llm.tool_router import ToolRouter
from app.config import settings

# 全局打印锁，防止多线程输出混乱
_print_lock = threading.Lock()

# 角色日志缓冲区（用于并行执行时收集日志）
_role_log_buffers: dict = {}
_buffer_lock = threading.Lock()

def safe_print(*args, **kwargs):
    """线程安全的打印函数"""
    with _print_lock:
        print(*args, **kwargs)

def buffered_print(role_name: str, *args, **kwargs):
    """
    缓冲打印函数 - 如果在缓冲区模式，则收集到缓冲区；否则直接打印
    
    Args:
        role_name: 角色名称
        *args, **kwargs: print 的参数
    """
    import io
    
    with _buffer_lock:
        if role_name in _role_log_buffers:
            # 缓冲区模式：收集到缓冲区
            buffer = _role_log_buffers[role_name]
            buffer.write(" ".join(str(arg) for arg in args) + "\n")
        else:
            # 直接模式：直接打印
            with _print_lock:
                print(*args, **kwargs)

def flush_role_buffer(role_name: str):
    """
    刷新并输出角色的日志缓冲区
    
    Args:
        role_name: 角色名称
    """
    with _buffer_lock:
        if role_name in _role_log_buffers:
            buffer = _role_log_buffers[role_name]
            buffer.seek(0)
            content = buffer.read()
            
            # 一次性输出整个缓冲区
            with _print_lock:
                print(content, end="")
            
            # 清理缓冲区
            buffer.close()
            del _role_log_buffers[role_name]

def enable_role_buffer(role_name: str):
    """
    启用角色日志缓冲区
    
    Args:
        role_name: 角色名称
    """
    with _buffer_lock:
        _role_log_buffers[role_name] = io.StringIO()


class ThinkingHat(ABC):
    """思考帽角色基类"""
    
    def __init__(self, name: str, color: str, system_prompt: str):
        self.name = name
        self.color = color
        self.system_prompt = system_prompt
        
        # 初始化工具管理器（传入角色名称用于日志）
        self.mcp_manager = MCPServerManager(role_name=name)
        self.tool_router = ToolRouter(self.mcp_manager)
    
    def think(self, question: str, context: dict = None, use_strong_model: bool = False) -> str:
        """
        独立思考并可能调用工具
        
        Args:
            question: 用户问题
            context: 其他角色的观点（用于 Round 2 辩驳）
            use_strong_model: 是否使用强模型
            
        Returns:
            角色的观点文本
        """
        buffered_print(self.name, f"\n{'='*70}")
        buffered_print(self.name, f"🎭 【{self.name}】开始思考")
        buffered_print(self.name, f"{'='*70}")
        buffered_print(self.name, f"   📋 问题: {question[:100]}{'...' if len(question) > 100 else ''}")
        
        # Step 1: 判断是否需要使用工具
        if self.tool_router.should_use_tools(self.color, question):
            buffered_print(self.name, f"   📦 需要调用工具获取上下文")
            # 获取角色工具配置
            role_config = self.tool_router.get_role_tools(self.color)
            
            # Step 2: 按需连接服务器
            for server in role_config["servers"]:
                try:
                    buffered_print(self.name, f"   🔗 连接服务器: {server}")
                    self.mcp_manager.connect(server)
                except Exception as e:
                    buffered_print(self.name, f"   ⚠️  连接 {server} 失败: {e}")
            
            # Step 3: 调用工具获取上下文
            tool_results = self._call_tools(question, role_config["tools"])
            question_with_context = f"问题：{question}\n\n工具调用结果：\n{tool_results}"
            preview = tool_results[:100].replace('\n', ' ')
            buffered_print(self.name, f"   📄 工具结果预览: {preview}{'...' if len(tool_results) > 100 else ''}")
        else:
            buffered_print(self.name, f"   💭 不使用工具，直接思考")
            question_with_context = question
        
        # Step 4: 构建消息
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": question_with_context}
        ]
        
        # Round 2: 加入其他角色观点
        if context:
            buffered_print(self.name, f"   🔄 进入辩驳阶段，参考其他角色观点")
            other_views = self._format_context(context)
            messages.append({
                "role": "user",
                "content": f"其他角色的观点：\n{other_views}\n\n请针对与你不同的观点进行辩驳或补充。"
            })
        
        # Step 5: 调用 LLM
        buffered_print(self.name, f"   🤖 调用 LLM 生成回答...")
        response = chat(messages, use_strong_model=use_strong_model)
        
        # 记录完整回答
        buffered_print(self.name, f"\n{'='*70}")
        buffered_print(self.name, f"✅ 【{self.name}】完整回答")
        buffered_print(self.name, f"{'='*70}")
        buffered_print(self.name, response)
        buffered_print(self.name, f"{'='*70}\n")
        
        return response
    
    def _format_context(self, context: dict) -> str:
        """格式化其他角色的观点"""
        formatted = []
        for color, view in context.items():
            if color != self.color:  # 排除自己
                formatted.append(f"【{color}】{view}")
        return "\n\n".join(formatted)
    
    def _call_tools(self, question: str, tools: list) -> str:
        """
        调用工具获取上下文
        
        Args:
            question: 用户问题
            tools: 工具名称列表
        
        Returns:
            格式化的工具调用结果
        """
        results = []
        
        for tool in tools:
            try:
                # 根据工具名判断在哪个服务器
                server = self._find_tool_server(tool)
                
                buffered_print(self.name, f"\n   🔧 [{self.name}] 调用工具: {tool}")
                buffered_print(self.name, f"      服务器: {server}")
                
                # 根据不同工具传递不同参数
                if tool == "search_knowledge_base":
                    query_preview = question[:50].replace('\n', ' ')
                    buffered_print(self.name, f"      参数: query='{query_preview}...', top_k=3")
                    result = self.mcp_manager.call_tool(
                        server, tool, 
                        role_name=self.name,
                        query=question, 
                        top_k=3
                    )
                elif tool == "get_current_time":
                    buffered_print(self.name, f"      参数: (无)")
                    result = self.mcp_manager.call_tool(
                        server, tool, 
                        role_name=self.name
                    )
                elif tool == "bing_search":
                    # 优化查询词：去除标点符号、截取适当长度
                    from app.llm.tool_router import ToolRouter
                    optimized_query = ToolRouter.optimize_search_query(question)
                    
                    query_preview = optimized_query[:50].replace('\n', ' ')
                    buffered_print(self.name, f"      参数: query='{query_preview}...', max_results=5")
                    result = self.mcp_manager.call_tool(
                        server, tool, 
                        role_name=self.name,
                        query=optimized_query, 
                        max_results=5
                    )
                elif tool == "execute_python":
                    # 执行Python代码 - 根据角色生成不同的代码
                    buffered_print(self.name, f"      参数: code=<根据问题生成的Python代码>")
                    
                    # 根据问题生成简单的统计计算代码
                    # 这里使用问题本身作为代码（实际应该由LLM生成）
                    code = f"# 执行计算\nprint('执行计算: {question[:50]}')"
                    
                    result = self.mcp_manager.call_tool(
                        server, tool, 
                        role_name=self.name,
                        code=code
                    )
                else:
                    query_preview = question[:50].replace('\n', ' ')
                    buffered_print(self.name, f"      参数: query='{query_preview}...'")
                    result = self.mcp_manager.call_tool(
                        server, tool, 
                        role_name=self.name,
                        query=question
                    )
                
                results.append(f"[{tool}] {result}")
                
            except Exception as e:
                buffered_print(self.name, f"   ❌ [{self.name}] 工具调用失败: {tool}")
                buffered_print(self.name, f"      错误: {e}")
                results.append(f"[{tool}] 调用失败: {e}")
        
        return "\n\n".join(results) if results else "无工具结果"
    
    def _find_tool_server(self, tool_name: str) -> str:
        """
        查找工具所在的服务器
        
        Args:
            tool_name: 工具名称
        
        Returns:
            服务器名称
        """
        # 简单映射，实际可以从配置中读取
        tool_server_map = {
            "search_knowledge_base": "rag",
            "add_document": "rag",
            "list_documents": "rag",
            "get_stats": "rag",
            "bing_search": "bing-search",
            "get_current_time": "time",
            "execute_python": "python-executor",
            "fetch_url": "fetch",
            "read_file": "filesystem"
        }
        return tool_server_map.get(tool_name, "rag")
    
    def cleanup(self):
        """清理资源"""
        self.mcp_manager.close_all()
