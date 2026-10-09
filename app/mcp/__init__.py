"""
MCP (Model Context Protocol) 模块

符合官方 MCP 标准（JSON-RPC 2.0），支持：
- 初始化握手（initialize/initialized）
- 能力协商（capabilities）
- 工具调用（tools/list, tools/call）
- 资源访问（resources/list, resources/read）
- HTTP 和 stdio 传输
"""

from .protocol import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCNotification,
    JSONRPCErrorCode,
    MCPErrorCode,
    MCPInitializeRequest,
    MCPInitializeResponse,
    parse_jsonrpc_message,
    create_error_response,
)

from .schemas import (
    ToolDefinition,
    ToolInputSchema,
    ToolParameterSchema,
    ResourceDefinition,
    ServerCapabilities,
    ToolCapabilities,
    ResourceCapabilities,
    ServerInfo,
    ClientInfo,
    ToolResult,
    TextContent,
    ImageContent,
)

from .server import MCPServer
from .logging_config import setup_mcp_logging

# 延迟导入客户端（需要 aiohttp）
try:
    from .client import MCPClient, SyncMCPClient
    _HAS_AIOHTTP = True
except ImportError:
    _HAS_AIOHTTP = False
    MCPClient = None
    SyncMCPClient = None

__all__ = [
    # 协议
    "JSONRPCRequest",
    "JSONRPCResponse",
    "JSONRPCNotification",
    "JSONRPCErrorCode",
    "MCPErrorCode",
    "MCPInitializeRequest",
    "MCPInitializeResponse",
    "parse_jsonrpc_message",
    "create_error_response",
    
    # 数据模型
    "ToolDefinition",
    "ToolInputSchema",
    "ToolParameterSchema",
    "ResourceDefinition",
    "ServerCapabilities",
    "ToolCapabilities",
    "ResourceCapabilities",
    "ServerInfo",
    "ClientInfo",
    "ToolResult",
    "TextContent",
    "ImageContent",
    
    # 服务器和客户端
    "MCPServer",
    "MCPClient",
    "SyncMCPClient",
    
    # 日志
    "setup_mcp_logging",
]

__version__ = "2.0.0"
