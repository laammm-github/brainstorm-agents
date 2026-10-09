"""MCP服务器 - 符合官方 MCP 标准（JSON-RPC 2.0）"""
import asyncio
import json
import logging
from typing import Any, Callable, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

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
    ToolResult,
    TextContent,
)

logger = logging.getLogger(__name__)


class MCPServer:
    """
    MCP 服务器（符合官方标准）
    
    支持：
    - JSON-RPC 2.0 协议
    - 初始化握手（initialize/initialized）
    - 能力协商（capabilities）
    - 工具调用（tools/list, tools/call）
    - 资源访问（resources/list, resources/read）
    - HTTP 和 stdio 传输
    """
    
    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        port: int = 3000,
        description: str = ""
    ):
        self.name = name
        self.version = version
        self.port = port
        self.description = description
        
        # 服务器状态
        self._initialized = False
        self._client_info: Optional[Dict[str, str]] = None
        
        # 工具和资源注册表
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._resources: Dict[str, Dict[str, Any]] = {}
        
        # 能力配置
        self.capabilities = ServerCapabilities(
            tools=ToolCapabilities(listChanged=False),
            resources=ResourceCapabilities(listChanged=False),
        )
        
        # FastAPI 应用
        self.app = FastAPI(title=f"MCP Server: {name}")
        self._setup_routes()
    
    def _setup_routes(self):
        """设置 HTTP 路由"""
        
        @self.app.post("/mcp")
        async def handle_mcp_request(request: Request):
            """处理 MCP 请求（HTTP 传输）"""
            try:
                body = await request.json()
                jsonrpc_request = parse_jsonrpc_message(json.dumps(body))
                
                if not isinstance(jsonrpc_request, JSONRPCRequest):
                    return JSONResponse(
                        status_code=400,
                        content=create_error_response(
                            JSONRPCErrorCode.INVALID_REQUEST,
                            "Invalid JSON-RPC request"
                        ).to_dict()
                    )
                
                response = await self._handle_request(jsonrpc_request)
                return JSONResponse(content=response.to_dict())
                
            except Exception as e:
                logger.error(f"Error handling request: {e}", exc_info=True)
                return JSONResponse(
                    status_code=500,
                    content=create_error_response(
                        JSONRPCErrorCode.INTERNAL_ERROR,
                        f"Internal server error: {str(e)}"
                    ).to_dict()
                )
        
        @self.app.get("/health")
        async def health_check():
            """健康检查"""
            return {
                "status": "healthy",
                "server": self.name,
                "version": self.version,
                "initialized": self._initialized
            }
    
    async def _handle_request(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """处理 JSON-RPC 请求"""
        method = request.method
        
        # 使用实际的方法对象，而不是引用
        method_handlers = {
            "initialize": self._handle_initialize,
            "tools/list": self._handle_tools_list,
            "tools/call": self._handle_tools_call,
            "resources/list": self._handle_resources_list,
            "resources/read": self._handle_resources_read,
            "ping": self._handle_ping,
        }
        
        handler = method_handlers.get(method)
        if not handler:
            return create_error_response(
                JSONRPCErrorCode.METHOD_NOT_FOUND,
                f"Method not found: {method}",
                request.id
            )
        
        try:
            return await handler(request)
        except Exception as e:
            logger.error(f"Error handling method {method}: {e}", exc_info=True)
            # 创建错误响应时传递 request.id
            return create_error_response(
                JSONRPCErrorCode.INTERNAL_ERROR,
                f"Method execution failed: {str(e)}",
                request.id
            )
    
    async def _handle_initialize(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """处理初始化请求（MCP 握手第一步）"""
        try:
            init_data = request.params
            client_info = init_data.get("clientInfo", {})
            
            self._client_info = client_info
            
            logger.info(
                f"Client initialized: {client_info.get('name')} v{client_info.get('version')}"
            )
            
            # 构建响应（使用简单的字典，确保可序列化）
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": False},
                    "resources": {"subscribe": False, "listChanged": False}
                },
                "serverInfo": {
                    "name": self.name,
                    "version": self.version
                }
            }
            
            # 验证可序列化性
            try:
                json.dumps(result)
            except TypeError as e:
                logger.error(f"Result not serializable: {e}")
                logger.error(f"Result content: {result}")
                raise
            
            response = JSONRPCResponse.success(
                result=result,
                id=request.id
            )
            
            # 验证 response 可序列化
            try:
                response.to_json()
            except TypeError as e:
                logger.error(f"Response not serializable: {e}")
                logger.error(f"Response dict: {response.to_dict()}")
                raise
            
            return response
            
        except Exception as e:
            logger.error(f"Initialize failed: {e}", exc_info=True)
            return create_error_response(
                JSONRPCErrorCode.INTERNAL_ERROR,
                f"Initialization failed: {str(e)}",
                request.id
            )
    
    async def _handle_initialized(self, notification: JSONRPCNotification) -> None:
        """处理初始化完成通知（MCP 握手第二步）"""
        self._initialized = True
        logger.info(f"Server {self.name} is now fully initialized")
    
    async def _handle_ping(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """处理 ping 请求"""
        return JSONRPCResponse.success(result={}, id=request.id)
    
    async def _handle_tools_list(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """处理工具列表请求"""
        tools = []
        for tool_data in self._tools.values():
            tools.append(tool_data["definition"].to_dict())
        
        return JSONRPCResponse.success(
            result={"tools": tools},
            id=request.id
        )
    
    async def _handle_tools_call(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """处理工具调用请求"""
        params = request.params
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            return create_error_response(
                JSONRPCErrorCode.INVALID_PARAMS,
                "Tool name is required",
                request.id
            )
        
        if tool_name not in self._tools:
            return create_error_response(
                MCPErrorCode.TOOL_NOT_FOUND,
                f"Tool '{tool_name}' not found",
                request.id
            )
        
        try:
            handler = self._tools[tool_name]["handler"]
            result = await self._execute_tool(handler, arguments)
            
            if isinstance(result, ToolResult):
                tool_result = result
            else:
                tool_result = ToolResult(
                    content=[TextContent(text=str(result))],
                    isError=False
                )
            
            return JSONRPCResponse.success(
                result=tool_result.to_dict(),
                id=request.id
            )
            
        except Exception as e:
            logger.error(f"Tool execution failed: {e}", exc_info=True)
            return create_error_response(
                MCPErrorCode.SERVER_ERROR,
                f"Tool execution failed: {str(e)}",
                request.id
            )
    
    async def _handle_resources_list(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """处理资源列表请求"""
        resources = []
        for resource_data in self._resources.values():
            resources.append(resource_data["definition"].to_dict())
        
        return JSONRPCResponse.success(
            result={"resources": resources},
            id=request.id
        )
    
    async def _handle_resources_read(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """处理资源读取请求"""
        uri = request.params.get("uri")
        
        if not uri:
            return create_error_response(
                JSONRPCErrorCode.INVALID_PARAMS,
                "Resource URI is required",
                request.id
            )
        
        if uri not in self._resources:
            return create_error_response(
                MCPErrorCode.RESOURCE_NOT_FOUND,
                f"Resource '{uri}' not found",
                request.id
            )
        
        try:
            handler = self._resources[uri]["handler"]
            content = await self._execute_tool(handler, {"uri": uri})
            
            return JSONRPCResponse.success(
                result={
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "text/plain",
                            "text": str(content)
                        }
                    ]
                },
                id=request.id
            )
            
        except Exception as e:
            logger.error(f"Resource read failed: {e}", exc_info=True)
            return create_error_response(
                MCPErrorCode.SERVER_ERROR,
                f"Resource read failed: {str(e)}",
                request.id
            )
    
    async def _execute_tool(self, handler: Callable, arguments: Dict[str, Any]) -> Any:
        """执行工具（支持同步和异步）"""
        if asyncio.iscoroutinefunction(handler):
            return await handler(**arguments)
        else:
            return handler(**arguments)
    
    def register_tool(
        self,
        name: str,
        handler: Callable,
        description: str,
        input_schema: ToolInputSchema
    ):
        """注册工具（符合 MCP 标准）"""
        definition = ToolDefinition(
            name=name,
            description=description,
            inputSchema=input_schema
        )
        
        self._tools[name] = {
            "definition": definition,
            "handler": handler
        }
        
        logger.info(f"Registered tool: {name}")
    
    def register_resource(
        self,
        uri: str,
        handler: Callable,
        name: str,
        description: str,
        mime_type: Optional[str] = None
    ):
        """注册资源"""
        definition = ResourceDefinition(
            uri=uri,
            name=name,
            description=description,
            mimeType=mime_type
        )
        
        self._resources[uri] = {
            "definition": definition,
            "handler": handler
        }
        
        logger.info(f"Registered resource: {uri}")
    
    def tool(self, name: str, description: str, parameters: Dict[str, Any] = None):
        """
        工具装饰器 - 简化注册工具
        
        Args:
            name: 工具名称
            description: 工具描述
            parameters: 参数字典 {param_name: {"type": "string", "description": "..."}}
        
        Returns:
            装饰器函数
        
        Example:
            @server.tool(
                name="search",
                description="Search knowledge base",
                parameters={"query": {"type": "string", "description": "Search query"}}
            )
            async def handle_search(query: str):
                return ToolResult(content=[TextContent(type="text", text="result")])
        """
        def decorator(func: Callable):
            # 构建 inputSchema
            params = parameters if parameters is not None else {}
            
            input_schema = ToolInputSchema(
                type="object",
                properties=params,
                required=[]
            )
            
            # 注册工具
            self.register_tool(
                name=name,
                handler=func,
                description=description,
                input_schema=input_schema
            )
            
            return func
        
        return decorator
    
    async def handle_stdio(self):
        """处理 stdio 传输（本地进程通信）"""
        import sys
        
        logger.info(f"Starting MCP server '{self.name}' in stdio mode")
        
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                
                message = parse_jsonrpc_message(line.strip())
                
                if isinstance(message, JSONRPCRequest):
                    response = await self._handle_request(message)
                    sys.stdout.write(response.to_json() + "\n")
                    sys.stdout.flush()
                    
                elif isinstance(message, JSONRPCNotification):
                    if message.method == "notifications/initialized":
                        await self._handle_initialized(message)
                
            except Exception as e:
                # 确保错误信息是字符串，不使用异常对象本身
                error_msg = str(e) if e else "Unknown error"
                logger.error(f"Error in stdio handling: {error_msg}", exc_info=True)
                
                # 尝试获取 request id（如果有）
                request_id = None
                if 'message' in locals() and isinstance(message, JSONRPCRequest):
                    request_id = message.id
                
                # 创建错误响应（data 参数使用字符串，不使用异常对象）
                error_response = JSONRPCResponse(
                    error={
                        "code": JSONRPCErrorCode.INTERNAL_ERROR.value,
                        "message": f"Error: {error_msg}"
                    },
                    id=request_id
                )
                sys.stdout.write(error_response.to_json() + "\n")
                sys.stdout.flush()
    
    def run(self, mode: str = "http", host: str = "0.0.0.0", log_level: str = "info"):
        """运行服务器"""
        if mode == "stdio":
            asyncio.run(self.handle_stdio())
        else:
            import uvicorn
            
            logger.info(
                f"Starting MCP server '{self.name}' on {host}:{self.port} (HTTP mode)"
            )
            uvicorn.run(
                self.app,
                host=host,
                port=self.port,
                log_level=log_level
            )
