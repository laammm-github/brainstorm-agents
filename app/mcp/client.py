"""MCP客户端 - 符合官方 MCP 标准（JSON-RPC 2.0）"""
import asyncio
import json
import logging
from typing import Any, Dict, Optional, Union

import aiohttp

from .protocol import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCNotification,
    JSONRPCErrorCode,
    MCPInitializeRequest,
    MCPInitializeResponse,
    parse_jsonrpc_message,
)
from .schemas import (
    ToolDefinition,
    ToolInputSchema,
    ToolParameterSchema,
    ResourceDefinition,
    ServerInfo,
    ServerCapabilities,
    ToolResult,
    TextContent,
)

logger = logging.getLogger(__name__)


class MCPClient:
    """
    MCP 客户端（符合官方标准）
    
    支持：
    - JSON-RPC 2.0 协议
    - 初始化握手（initialize/initialized）
    - HTTP 和 stdio 传输
    - 连接池管理
    - 自动重试
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 30,
        retry_count: int = 3
    ):
        """
        初始化 MCP 客户端
        
        Args:
            base_url: HTTP 服务器 URL（stdio 模式为 None）
            timeout: 请求超时时间（秒）
            retry_count: 重试次数
        """
        self.base_url = base_url
        self.timeout = timeout
        self.retry_count = retry_count
        
        # 连接池
        self.session: Optional[aiohttp.ClientSession] = None
        self._connector: Optional[aiohttp.TCPConnector] = None
        
        # 状态
        self._initialized = False
        self._request_id = 0
        self._server_info: Optional[ServerInfo] = None
        self._server_capabilities: Optional[ServerCapabilities] = None
        
        # stdio 进程（如果使用 stdio 模式）
        self._stdio_process: Optional[asyncio.subprocess.Process] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        if self.base_url:
            # HTTP 模式：创建连接池
            self._connector = aiohttp.TCPConnector(
                limit=100,           # 总连接数限制
                limit_per_host=10,   # 每个主机的连接数限制
                ttl_dns_cache=300,   # DNS 缓存时间
                enable_cleanup_closed=True,
            )
            self.session = aiohttp.ClientSession(
                connector=self._connector,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
        if self._connector:
            await self._connector.close()
        if self._stdio_process:
            self._stdio_process.terminate()
            await self._stdio_process.wait()
    
    def _generate_request_id(self) -> int:
        """生成请求 ID（整数，符合 JSON-RPC 标准）"""
        self._request_id += 1
        return self._request_id
    
    async def initialize(
        self,
        client_name: str = "mcp-client",
        client_version: str = "1.0.0"
    ) -> Dict[str, Any]:
        """
        初始化握手（MCP 标准流程第一步）
        
        Args:
            client_name: 客户端名称
            client_version: 客户端版本
            
        Returns:
            服务器信息和能力
        """
        init_request = MCPInitializeRequest(
            protocol_version="2024-11-05",
            capabilities={},
            client_info={"name": client_name, "version": client_version}
        )
        
        # 发送 initialize 请求
        response = await self._send_request(
            method="initialize",
            params=init_request.to_dict()
        )
        
        if response.error:
            raise Exception(f"Initialize failed: {response.error}")
        
        # 解析响应
        result = response.result
        self._server_info = ServerInfo(
            name=result["serverInfo"]["name"],
            version=result["serverInfo"]["version"]
        )
        self._server_capabilities = ServerCapabilities(**result.get("capabilities", {}))
        
        # 发送 initialized 通知（第二步）
        await self._send_notification(
            method="notifications/initialized",
            params={}
        )
        
        self._initialized = True
        logger.info(
            f"Connected to {self._server_info.name} v{self._server_info.version}"
        )
        
        return {
            "server_info": self._server_info.to_dict(),
            "capabilities": self._server_capabilities.to_dict()
        }
    
    async def _send_request(
        self,
        method: str,
        params: Dict[str, Any]
    ) -> JSONRPCResponse:
        """
        发送 JSON-RPC 请求
        
        Args:
            method: 方法名
            params: 参数
            
        Returns:
            JSON-RPC 响应
        """
        request = JSONRPCRequest(
            id=self._generate_request_id(),
            method=method,
            params=params
        )
        
        # HTTP 模式
        if self.base_url and self.session:
            return await self._send_http_request(request)
        
        # stdio 模式
        elif self._stdio_process:
            return await self._send_stdio_request(request)
        
        else:
            raise RuntimeError("Client not initialized. Use async with or connect() first.")
    
    async def _send_http_request(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """通过 HTTP 发送请求"""
        for attempt in range(self.retry_count + 1):
            try:
                async with self.session.post(
                    f"{self.base_url}/mcp",
                    json=request.to_dict()
                ) as response:
                    if response.status != 200:
                        if attempt < self.retry_count and response.status >= 500:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        
                        return JSONRPCResponse.error(
                            code=JSONRPCErrorCode.INTERNAL_ERROR.value,
                            message=f"HTTP {response.status}: {await response.text()}",
                            id=request.id
                        )
                    
                    data = await response.json()
                    return JSONRPCResponse(
                        result=data.get("result"),
                        error=data.get("error"),
                        id=data.get("id"),
                        jsonrpc=data.get("jsonrpc", "2.0")
                    )
                    
            except asyncio.TimeoutError:
                if attempt < self.retry_count:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return JSONRPCResponse.error(
                    code=JSONRPCErrorCode.INTERNAL_ERROR.value,
                    message="Request timeout",
                    id=request.id
                )
            except Exception as e:
                if attempt < self.retry_count and "Connection" in str(e):
                    await asyncio.sleep(2 ** attempt)
                    continue
                return JSONRPCResponse.error(
                    code=JSONRPCErrorCode.INTERNAL_ERROR.value,
                    message=f"Request failed: {str(e)}",
                    id=request.id
                )
        
        return JSONRPCResponse.error(
            code=JSONRPCErrorCode.INTERNAL_ERROR.value,
            message="Request failed after all retries",
            id=request.id
        )
    
    async def _send_stdio_request(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """通过 stdio 发送请求"""
        # 写入请求
        self._stdio_process.stdin.write((request.to_json() + "\n").encode())
        await self._stdio_process.stdin.drain()
        
        # 读取响应
        while True:
            line = await self._stdio_process.stdout.readline()
            if not line:
                break
            
            message = parse_jsonrpc_message(line.decode().strip())
            if isinstance(message, JSONRPCResponse) and message.id == request.id:
                return message
    
    async def _send_notification(
        self,
        method: str,
        params: Dict[str, Any]
    ) -> None:
        """
        发送通知（没有响应）
        
        Args:
            method: 方法名
            params: 参数
        """
        notification = JSONRPCNotification(method=method, params=params)
        
        if self.base_url and self.session:
            # HTTP 模式
            async with self.session.post(
                f"{self.base_url}/mcp",
                json=notification.to_dict()
            ):
                pass
        elif self._stdio_process:
            # stdio 模式
            self._stdio_process.stdin.write((notification.to_json() + "\n").encode())
            await self._stdio_process.stdin.drain()
    
    async def list_tools(self) -> Dict[str, Any]:
        """列出可用工具"""
        response = await self._send_request("tools/list", {})
        
        if response.error:
            return {"error": response.error}
        
        return {"tools": response.result.get("tools", [])}
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        调用工具
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具执行结果
        """
        response = await self._send_request(
            "tools/call",
            {
                "name": tool_name,
                "arguments": arguments
            }
        )
        
        if response.error:
            return {"error": response.error}
        
        return {"result": response.result}
    
    async def list_resources(self) -> Dict[str, Any]:
        """列出可用资源"""
        response = await self._send_request("resources/list", {})
        
        if response.error:
            return {"error": response.error}
        
        return {"resources": response.result.get("resources", [])}
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """
        读取资源
        
        Args:
            uri: 资源 URI
            
        Returns:
            资源内容
        """
        response = await self._send_request(
            "resources/read",
            {"uri": uri}
        )
        
        if response.error:
            return {"error": response.error}
        
        return {"content": response.result}
    
    async def ping(self) -> bool:
        """Ping 服务器"""
        response = await self._send_request("ping", {})
        return response.error is None
    
    @classmethod
    async def create_stdio_client(cls, command: str, args: list = None) -> 'MCPClient':
        """
        创建 stdio 模式的客户端
        
        Args:
            command: 服务器命令（如 "python"）
            args: 命令参数（如 ["server.py"]）
            
        Returns:
            MCPClient 实例
        """
        client = cls(base_url=None)
        
        # 启动子进程
        client._stdio_process = await asyncio.create_subprocess_exec(
            command,
            *(args or []),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        return client


# ============ 同步客户端包装器 ============

import concurrent.futures


class SyncMCPClient:
    """
    同步 MCP 客户端包装器
    
    使用 ThreadPoolExecutor 运行异步操作
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 30,
        retry_count: int = 3
    ):
        """
        初始化同步客户端
        
        Args:
            base_url: HTTP 服务器 URL
            timeout: 请求超时时间
            retry_count: 重试次数
        """
        self.base_url = base_url
        self.timeout = timeout
        self.retry_count = retry_count
        
        # 使用线程池执行异步操作
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._async_client = MCPClient(
            base_url=base_url,
            timeout=timeout,
            retry_count=retry_count
        )
    
    def __enter__(self):
        """同步上下文管理器入口"""
        # 在线程池中初始化异步客户端
        future = self._executor.submit(
            asyncio.run,
            self._async_client.__aenter__()
        )
        future.result()  # 等待完成
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """同步上下文管理器出口"""
        future = self._executor.submit(
            asyncio.run,
            self._async_client.__aexit__(exc_type, exc_val, exc_tb)
        )
        future.result()
        self._executor.shutdown(wait=False)
    
    def initialize(
        self,
        client_name: str = "mcp-client",
        client_version: str = "1.0.0"
    ) -> Dict[str, Any]:
        """初始化握手"""
        future = self._executor.submit(
            asyncio.run,
            self._async_client.initialize(client_name, client_version)
        )
        return future.result()
    
    def list_tools(self) -> Dict[str, Any]:
        """列出工具"""
        future = self._executor.submit(
            asyncio.run,
            self._async_client.list_tools()
        )
        return future.result()
    
    def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """调用工具"""
        future = self._executor.submit(
            asyncio.run,
            self._async_client.call_tool(tool_name, arguments)
        )
        return future.result()
    
    def list_resources(self) -> Dict[str, Any]:
        """列出资源"""
        future = self._executor.submit(
            asyncio.run,
            self._async_client.list_resources()
        )
        return future.result()
    
    def read_resource(self, uri: str) -> Dict[str, Any]:
        """读取资源"""
        future = self._executor.submit(
            asyncio.run,
            self._async_client.read_resource(uri)
        )
        return future.result()
    
    def ping(self) -> bool:
        """Ping 服务器"""
        future = self._executor.submit(
            asyncio.run,
            self._async_client.ping()
        )
        return future.result()
