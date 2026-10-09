"""MCP数据模型定义 - 符合官方标准"""
from enum import Enum as PyEnum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


# ============ 工具定义（JSON Schema） ============

class ParameterType(str, PyEnum):
    """JSON Schema 类型"""
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"


class ToolParameterSchema(BaseModel):
    """工具参数 JSON Schema"""
    type: ParameterType = Field(..., description="参数类型")
    description: str = Field(..., description="参数描述")
    enum: Optional[List[str]] = Field(default=None, description="枚举值")
    default: Optional[Any] = Field(default=None, description="默认值")
    minimum: Optional[Union[int, float]] = Field(default=None, description="最小值")
    maximum: Optional[Union[int, float]] = Field(default=None, description="最大值")
    pattern: Optional[str] = Field(default=None, description="正则表达式模式")


class ToolInputSchema(BaseModel):
    """工具输入 Schema（JSON Schema 格式）"""
    type: str = Field(default="object", description="固定为 object")
    properties: Dict[str, ToolParameterSchema] = Field(
        default_factory=dict, 
        description="参数定义"
    )
    required: List[str] = Field(
        default_factory=list,
        description="必需参数列表"
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "type": self.type,
            "properties": {
                name: {
                    "type": param.type.value,
                    "description": param.description,
                    **({"enum": param.enum} if param.enum else {}),
                    **({"default": param.default} if param.default is not None else {}),
                    **({"minimum": param.minimum} if param.minimum is not None else {}),
                    **({"maximum": param.maximum} if param.maximum is not None else {}),
                    **({"pattern": param.pattern} if param.pattern else {}),
                }
                for name, param in self.properties.items()
            },
            "required": self.required
        }


class ToolDefinition(BaseModel):
    """工具完整定义（符合 MCP 标准）"""
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    inputSchema: ToolInputSchema = Field(..., description="输入参数 JSON Schema")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.inputSchema.to_dict()
        }


# ============ 资源定义 ============

class ResourceTemplate(BaseModel):
    """资源模板"""
    uriTemplate: str = Field(..., description="URI 模板，如 file://{path}")
    name: str = Field(..., description="资源名称")
    description: str = Field(..., description="资源描述")
    mimeType: Optional[str] = Field(default=None, description="MIME 类型")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "uriTemplate": self.uriTemplate,
            "name": self.name,
            "description": self.description,
            **({"mimeType": self.mimeType} if self.mimeType else {})
        }


class ResourceDefinition(BaseModel):
    """资源定义"""
    uri: str = Field(..., description="资源 URI")
    name: str = Field(..., description="资源名称")
    description: str = Field(..., description="资源描述")
    mimeType: Optional[str] = Field(default=None, description="MIME 类型")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            **({"mimeType": self.mimeType} if self.mimeType else {})
        }


# ============ Prompt 定义 ============

class PromptArgument(BaseModel):
    """Prompt 参数"""
    name: str = Field(..., description="参数名称")
    description: str = Field(..., description="参数描述")
    required: bool = Field(default=False, description="是否必需")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "required": self.required
        }


class PromptDefinition(BaseModel):
    """Prompt 定义"""
    name: str = Field(..., description="Prompt 名称")
    description: str = Field(..., description="Prompt 描述")
    arguments: Optional[List[PromptArgument]] = Field(default=None, description="参数列表")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            **({"arguments": [arg.to_dict() for arg in self.arguments]} if self.arguments else {})
        }


# ============ 能力定义 ============

class ToolCapabilities(BaseModel):
    """工具能力"""
    listChanged: Optional[bool] = Field(default=False, description="工具列表是否会变化")
    
    def to_dict(self) -> Dict[str, Any]:
        return {"listChanged": self.listChanged}


class ResourceCapabilities(BaseModel):
    """资源能力"""
    subscribe: Optional[bool] = Field(default=False, description="是否支持订阅")
    listChanged: Optional[bool] = Field(default=False, description="资源列表是否会变化")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "subscribe": self.subscribe,
            "listChanged": self.listChanged
        }


class PromptCapabilities(BaseModel):
    """Prompt 能力"""
    listChanged: Optional[bool] = Field(default=False, description="Prompt 列表是否会变化")
    
    def to_dict(self) -> Dict[str, Any]:
        return {"listChanged": self.listChanged}


class ServerCapabilities(BaseModel):
    """服务器能力（符合 MCP 标准）"""
    tools: Optional[ToolCapabilities] = Field(default=None, description="工具能力")
    resources: Optional[ResourceCapabilities] = Field(default=None, description="资源能力")
    prompts: Optional[PromptCapabilities] = Field(default=None, description="Prompt 能力")
    logging: Optional[Dict[str, Any]] = Field(default=None, description="日志能力")
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.tools:
            result["tools"] = self.tools.to_dict()
        if self.resources:
            result["resources"] = self.resources.to_dict()
        if self.prompts:
            result["prompts"] = self.prompts.to_dict()
        if self.logging:
            result["logging"] = self.logging
        return result


# ============ 服务器和客户端信息 ============

class ServerInfo(BaseModel):
    """服务器信息"""
    name: str = Field(..., description="服务器名称")
    version: str = Field(default="1.0.0", description="服务器版本")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version
        }


class ClientInfo(BaseModel):
    """客户端信息"""
    name: str = Field(..., description="客户端名称")
    version: str = Field(default="1.0.0", description="客户端版本")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version
        }


# ============ 工具调用结果 ============

class TextContent(BaseModel):
    """文本内容"""
    type: str = Field(default="text", description="固定为 text")
    text: str = Field(..., description="文本内容")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "text": self.text
        }


class ImageContent(BaseModel):
    """图片内容"""
    type: str = Field(default="image", description="固定为 image")
    data: str = Field(..., description="Base64 编码的图片数据")
    mimeType: str = Field(..., description="MIME 类型，如 image/png")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "data": self.data,
            "mimeType": self.mimeType
        }


class ToolResult(BaseModel):
    """工具调用结果"""
    content: List[Union[TextContent, ImageContent]] = Field(..., description="结果内容列表")
    isError: bool = Field(default=False, description="是否错误")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": [item.to_dict() for item in self.content],
            "isError": self.isError
        }
