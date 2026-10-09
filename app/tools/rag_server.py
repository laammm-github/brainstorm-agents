"""RAG MCP 服务器 - 提供知识库检索能力"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.mcp.server import MCPServer
from app.mcp.schemas import ToolResult, TextContent
from app.tools.rag_tool import rag_tool

# 创建 MCP 服务器
server = MCPServer(
    name="brainstorm-rag",
    version="1.0.0",
    description="RAG 知识库服务"
)

# 注册搜索工具
@server.tool(
    name="search_knowledge_base",
    description="检索本地知识库（个人学习笔记、投资分析框架等）",
    parameters={
        "query": {"type": "string", "description": "检索关键词"},
        "top_k": {"type": "integer", "description": "返回结果数量，默认3"}
    }
)
async def handle_search(query: str, top_k: int = 3) -> ToolResult:
    """知识库检索处理器"""
    try:
        result = rag_tool.search_knowledge_base(query, top_k)
        # 确保结果是 ASCII 安全的字符串
        if isinstance(result, bytes):
            result = result.decode('utf-8', errors='replace')
        result = str(result)
        return ToolResult(
            content=[TextContent(type="text", text=result)]
        )
    except Exception as e:
        error_msg = f"知识库搜索失败: {str(e)}"
        return ToolResult(
            content=[TextContent(type="text", text=error_msg)]
        )

# 注册添加文档工具
@server.tool(
    name="add_document",
    description="添加文档到知识库",
    parameters={
        "file_path": {"type": "string", "description": "文档文件路径"}
    }
)
async def handle_add(file_path: str) -> ToolResult:
    """添加文档处理器"""
    try:
        result = rag_tool.add_document(file_path)
        if isinstance(result, bytes):
            result = result.decode('utf-8', errors='replace')
        result = str(result)
        return ToolResult(
            content=[TextContent(type="text", text=result)]
        )
    except Exception as e:
        error_msg = f"添加文档失败: {str(e)}"
        return ToolResult(
            content=[TextContent(type="text", text=error_msg)]
        )

# 注册列出文档工具
@server.tool(
    name="list_documents",
    description="列出知识库中的所有文档",
    parameters={}
)
async def handle_list() -> ToolResult:
    """列出文档处理器"""
    try:
        result = rag_tool.list_documents()
        if isinstance(result, bytes):
            result = result.decode('utf-8', errors='replace')
        result = str(result)
        return ToolResult(
            content=[TextContent(type="text", text=result)]
        )
    except Exception as e:
        error_msg = f"列出文档失败: {str(e)}"
        return ToolResult(
            content=[TextContent(type="text", text=error_msg)]
        )

# 注册获取统计信息工具
@server.tool(
    name="get_stats",
    description="获取知识库统计信息",
    parameters={}
)
async def handle_stats() -> ToolResult:
    """统计信息处理器"""
    try:
        result = rag_tool.get_stats()
        if isinstance(result, bytes):
            result = result.decode('utf-8', errors='replace')
        result = str(result)
        return ToolResult(
            content=[TextContent(type="text", text=result)]
        )
    except Exception as e:
        error_msg = f"获取统计信息失败: {str(e)}"
        return ToolResult(
            content=[TextContent(type="text", text=error_msg)]
        )


if __name__ == "__main__":
    # 启动 stdio 模式的 MCP 服务器
    print("🚀 启动 RAG MCP 服务器...", file=sys.stderr)
    asyncio.run(server.handle_stdio())
