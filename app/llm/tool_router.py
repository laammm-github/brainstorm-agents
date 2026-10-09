"""工具路由器 - 角色专用工具映射"""
import re
from typing import Dict, List


# 角色工具映射
ROLE_TOOLS = {
    "white": {
        "servers": ["rag", "time", "bing-search", "python-executor", "filesystem"],
        "tools": ["search_knowledge_base", "get_current_time", 
                  "bing_search", "execute_python", "read_file"],
        "strategy": "mandatory"  # 强制使用
    },
    "black": {
        "servers": ["rag", "sequential-thinking", "bing-search", "fetch", "python-executor"],
        "tools": ["search_knowledge_base", "sequential_thinking",
                  "bing_search", "fetch_url", "execute_python"],
        "strategy": "optional"
    },
    "yellow": {
        "servers": ["rag", "fetch", "bing-search"],
        "tools": ["search_knowledge_base", "fetch_url", "bing_search"],
        "strategy": "optional"
    },
    "green": {
        "servers": ["rag", "fetch", "memory"],
        "tools": ["search_knowledge_base", "fetch_url", "query_memory"],
        "strategy": "optional"
    },
    "purple": {
        "servers": ["rag", "memory", "bing-search", "sequential-thinking", "python-executor"],
        "tools": ["search_knowledge_base", "query_memory",
                  "bing_search", "sequential_thinking", "execute_python"],
        "strategy": "optional"
    },
    "red": {
        "servers": [],
        "tools": [],
        "strategy": "none"  # 不使用工具
    }
}


class ToolRouter:
    """工具路由器"""
    
    def __init__(self, mcp_manager):
        self.mcp_manager = mcp_manager
    
    def get_role_tools(self, role_color: str) -> Dict:
        """
        获取角色的工具配置
        
        Args:
            role_color: 角色颜色（white, black, yellow, green, purple, red）
        
        Returns:
            工具配置字典
        """
        return ROLE_TOOLS.get(role_color, {"servers": [], "tools": [], "strategy": "none"})
    
    def should_use_tools(self, role_color: str, question: str) -> bool:
        """
        判断是否需要使用工具
        
        Args:
            role_color: 角色颜色
            question: 用户问题
        
        Returns:
            是否使用工具
        """
        role_config = self.get_role_tools(role_color)
        
        # 红帽不使用工具
        if role_config["strategy"] == "none":
            return False
        
        # 白帽总是使用工具
        if role_config["strategy"] == "mandatory":
            return True
        
        # 其他角色：根据关键词判断（扩展关键词覆盖更多场景）
        keywords = [
            # 数据相关
            "数据", "统计", "报告", "案例", "计算", 
            # 时间与发展
            "最新", "当前", "趋势", "未来", "发展",
            # 疑问词
            "什么", "如何", "为什么", "是否", "哪些",
            # 分析评估
            "分析", "评估", "比较", "优势", "劣势",
            "机会", "风险", "影响", "前景", "挑战"
        ]
        return any(kw in question for kw in keywords)
    
    def get_tools_prompt(self, role_color: str) -> str:
        """
        生成工具提示词
        
        Args:
            role_color: 角色颜色
        
        Returns:
            工具提示词文本
        """
        role_config = self.get_role_tools(role_color)
        
        if not role_config["tools"]:
            return ""
        
        prompt = "你可以使用以下工具：\n\n"
        for tool in role_config["tools"]:
            prompt += f"- {tool}\n"
        
        return prompt
    
    @staticmethod
    def optimize_search_query(query: str) -> str:
        """
        优化搜索查询词
            
        Args:
            query: 原始查询词
            
        Returns:
            优化后的查询词
        """
        # 0. 处理极短查询词（少于3个字符）
        if len(query.strip()) < 3:
            # 为极短查询词添加上下文
            short_query_map = {
                'ai': 'AI人工智能技术发展趋势',
                'AI': 'AI人工智能技术发展趋势',
                'ml': '机器学习技术应用',
                'ML': '机器学习技术应用',
                'dl': '深度学习技术应用',
                'DL': '深度学习技术应用',
            }
            return short_query_map.get(query.strip(), query + '技术应用')
            
        # 1. 去除主观疑问词和口语化表达（优先处理）
        subjective_words = [
            '怎么看待', '如何看待', '怎样看待', '你觉得', '你认为',
            '为什么', '为什么说', '是什么原因', '原因是什么',
            '是什么', '有哪些', '怎么办', '怎么做', '如何',
            '能不能', '是否可以', '好不好', '对不对',
            '请分析', '请说明', '请解释', '请评价',
            '谈谈', '说说', '介绍一下', '说明一下'
        ]
        for word in subjective_words:
            query = query.replace(word, '')
        
        # 2. 去除常见的句尾疑问词
        end_words = ['呢', '吗', '吧', '啊', '呀', '哦', '哈']
        for word in end_words:
            if query.endswith(word):
                query = query[:-len(word)]
        
        # 3. 去除标点符号（保留中文、英文、数字、空格）
        query = re.sub(r'[^\w\s\u4e00-\u9fff]', '', query)
            
        # 4. 去除多余的"的"、"了"、"在"等助词
        remove_chars = ['的', '了', '在', '是', '就', '都', '也', '还']
        for char in remove_chars:
            query = query.replace(char, '')
            
        # 5. 去除多余空格
        query = re.sub(r'\s+', ' ', query).strip()
        
        # 6. 智能截取：保留核心关键词
        # 如果查询包含技术术语（英文单词），优先保留
        english_words = re.findall(r'[a-zA-Z]+', query)
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', query)
        
        # 如果有英文术语且中文部分过长，智能截断
        if english_words and len(chinese_chars) > 15:
            # 保留英文术语和前后各5个中文字符
            first_english = english_words[0]
            idx = query.find(first_english)
            before = query[max(0, idx-8):idx]
            after = query[idx+len(first_english):idx+len(first_english)+8]
            query = (before + ' ' + first_english + ' ' + after).strip()
            
        # 7. 如果查询仍然过长（超过20字符），截取前20个字符
        if len(query) > 20:
            query = query[:20]
            
        # 8. 确保查询词至少有3个字符
        if len(query.strip()) < 3:
            # 如果原查询包含英文，保留英文
            if english_words:
                query = ' '.join(english_words[:2])
            else:
                query = query.strip() + ' 技术分析'
            
        return query.strip()
