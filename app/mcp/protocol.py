"""MCP协议定义 - 基于 JSON-RPC 2.0 标准"""
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# ============ JSON-RPC 2.0 标准错误码 ============

class JSONRPCErrorCode(Enum):
    """JSON-RPC 2.0 标准错误码"""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603


# ============ MCP 标准错误码（应用层） ============

class MCPErrorCode(Enum):
    """MCP 应用层错误码"""
    RESOURCE_NOT_FOUND = -32001
    TOOL_NOT_FOUND = -32002
    INVALID_TOOL_INPUT = -32003
    SERVER_ERROR = -32004


# ============ JSON-RPC 2.0 消息格式 ============

@dataclass
class JSONRPCRequest:
    """JSON-RPC 2.0 请求"""
    method: str
    params: Dict[str, Any] = field(default_factory=dict)
    id: Optional[Union[int, str]] = None
    jsonrpc: str = "2.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "jsonrpc": self.jsonrpc,
            "method": self.method,
            "params": self.params
        }
        if self.id is not None:
            result["id"] = self.id
        return result
    
    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JSONRPCRequest':
        """从字典创建"""
        return cls(
            method=data.get("method", ""),
            params=data.get("params", {}),
            id=data.get("id"),
            jsonrpc=data.get("jsonrpc", "2.0")
        )


@dataclass
class JSONRPCResponse:
    """JSON-RPC 2.0 响应"""
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None  # 字段：错误信息字典
    id: Optional[Union[int, str]] = None
    jsonrpc: str = "2.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "jsonrpc": self.jsonrpc,
            "id": self.id
        }
        if self.error is not None:
            result["error"] = self.error
        else:
            # 即使 result 为 None 也要包含该字段
            result["result"] = self.result
        return result
    
    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        try:
            return json.dumps(self.to_dict(), ensure_ascii=False)
        except (TypeError, ValueError) as e:
            # 如果序列化失败，手动构建 JSON
            error_dict = self.to_dict()
            # 移除无法序列化的字段
            if self.error and not isinstance(self.error, dict):
                error_dict["error"] = {"code": -32603, "message": str(self.error)}
            return json.dumps(error_dict, ensure_ascii=False)
    
    @classmethod
    def success(cls, result: Any, id: Optional[Union[int, str]] = None) -> 'JSONRPCResponse':
        """创建成功响应"""
        return cls(result=result, id=id)
    
    @classmethod
    def make_error(
        cls,
        code: int,
        message: str,
        id: Optional[Union[int, str]] = None,
        data: Optional[Any] = None
    ) -> 'JSONRPCResponse':
        """创建错误响应"""
        error_dict = {
            "code": code,
            "message": message
        }
        if data is not None:
            error_dict["data"] = data
        return cls(error=error_dict, id=id)


@dataclass
class JSONRPCNotification:
    """JSON-RPC 2.0 通知（没有 id 字段）"""
    method: str
    params: Dict[str, Any] = field(default_factory=dict)
    jsonrpc: str = "2.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "jsonrpc": self.jsonrpc,
            "method": self.method,
            "params": self.params
        }
    
    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


# ============ MCP 特定消息 ============

@dataclass
class MCPInitializeRequest:
    """MCP 初始化请求"""
    protocol_version: str = "2024-11-05"
    capabilities: Dict[str, Any] = field(default_factory=dict)
    client_info: Dict[str, str] = field(default_factory=lambda: {"name": "unknown", "version": "0.0.0"})
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "protocolVersion": self.protocol_version,
            "capabilities": self.capabilities,
            "clientInfo": self.client_info
        }


@dataclass
class MCPInitializeResponse:
    """MCP 初始化响应"""
    protocol_version: str = "2024-11-05"
    capabilities: Dict[str, Any] = field(default_factory=dict)
    server_info: Dict[str, str] = field(default_factory=lambda: {"name": "unknown", "version": "0.0.0"})
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "protocolVersion": self.protocol_version,
            "capabilities": self.capabilities,
            "serverInfo": self.server_info
        }


# ============ 消息解析 ============

def parse_jsonrpc_message(json_str: str) -> Optional[Union[JSONRPCRequest, JSONRPCResponse, JSONRPCNotification]]:
    """解析 JSON-RPC 消息"""
    try:
        data = json.loads(json_str)
        
        # 验证 jsonrpc 版本
        if data.get("jsonrpc") != "2.0":
            logger.warning(f"Invalid JSON-RPC version: {data.get('jsonrpc')}")
            return None
        
        # 判断消息类型
        has_id = "id" in data
        has_error = "error" in data
        has_result = "result" in data
        
        if has_id:
            # 请求或响应
            if has_error or has_result:
                # 响应
                return JSONRPCResponse(
                    result=data.get("result"),
                    error=data.get("error"),
                    id=data.get("id"),
                    jsonrpc=data.get("jsonrpc", "2.0")
                )
            else:
                # 请求
                return JSONRPCRequest.from_dict(data)
        else:
            # 通知（没有 id）
            return JSONRPCNotification(
                method=data.get("method", ""),
                params=data.get("params", {}),
                jsonrpc=data.get("jsonrpc", "2.0")
            )
    
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to parse JSON-RPC message: {e}")
        return None


def create_error_response(
    error_code: Union[JSONRPCErrorCode, MCPErrorCode],
    message: str,
    request_id: Optional[Union[int, str]] = None,
    data: Optional[Any] = None
) -> JSONRPCResponse:
    """创建标准错误响应"""
    # 确保 code 是整数
    code = error_code.value if hasattr(error_code, 'value') else error_code
    
    return JSONRPCResponse.make_error(
        code=code,
        message=message,
        id=request_id,
        data=data
    )
