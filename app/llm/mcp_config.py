"""
MCP 服务器配置

注意：官方 MCP 服务器包在 npm 上可能不存在或需要特定配置。
为简化部署，我们使用 Python 实现常用工具服务器。

参考: https://github.com/modelcontextprotocol/servers
"""

MCP_SERVERS = {
    # 自己实现的 RAG 服务器
    "rag": {
        "transport": "stdio",
        "command": "python",
        "args": ["-m", "app.tools.rag_server"],
        "description": "RAG 知识库服务",
        "category": "knowledge"
    },
    
    # 自己实现的时间服务器（替代不存在的 @modelcontextprotocol/server-time）
    "time": {
        "transport": "stdio",
        "command": "python",
        "args": ["-m", "app.tools.time_server"],
        "description": "时间获取工具",
        "category": "time"
    },
    
    # 自己实现的 Python 执行器
    "python-executor": {
        "transport": "stdio",
        "command": "python",
        "args": ["-m", "app.tools.python_executor_server"],
        "description": "Python代码执行沙箱",
        "category": "computation"
    },
    
    # Bing搜索服务器（替代百度搜索，国内可用且更稳定）
    "bing-search": {
        "transport": "stdio",
        "command": "python",
        "args": ["-m", "app.tools.bing_search_server"],
        "description": "Bing搜索（国内可用，支持中英文，稳定可靠）",
        "category": "search"
    },
    
    # 自己实现的文件系统服务器（替代npm包）
    "filesystem": {
        "transport": "stdio",
        "command": "python",
        "args": ["-m", "app.tools.filesystem_server"],
        "description": "文件操作工具",
        "category": "file"
    },
    
    # 自己实现的网页提取服务器（替代npm包）
    "fetch": {
        "transport": "stdio",
        "command": "python",
        "args": ["-m", "app.tools.fetch_server"],
        "description": "网页提取工具",
        "category": "fetch"
    },
    
    # 自己实现的知识图谱记忆服务器（替代npm包）
    "memory": {
        "transport": "stdio",
        "command": "python",
        "args": ["-m", "app.tools.memory_server"],
        "description": "知识图谱记忆系统",
        "category": "memory"
    },
    
    # 自己实现的顺序思考服务器（替代npm包）
    "sequential-thinking": {
        "transport": "stdio",
        "command": "python",
        "args": ["-m", "app.tools.sequential_thinking_server"],
        "description": "顺序思考工具",
        "category": "thinking"
    }
}
