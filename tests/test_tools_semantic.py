"""工具调用测试 - 验证 MCP 工具调用的输出语义和协议合规性"""
import pytest
from pathlib import Path
import sys
import json

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.llm.mcp_config import MCP_SERVERS
from app.llm.tool_router import ToolRouter, ROLE_TOOLS
from app.mcp.protocol import JSONRPCRequest, JSONRPCResponse
from app.mcp.schemas import ToolDefinition, ToolResult, TextContent


class TestMCPProtocol:
    """测试 MCP 协议合规性"""
    
    def test_jsonrpc_request_format(self):
        """测试 JSON-RPC 2.0 请求格式语义"""
        # 创建请求
        request = JSONRPCRequest(
            id=1,
            method="tools/call",
            params={"name": "search_knowledge_base", "arguments": {"query": "test"}}
        )
        
        # 验证协议语义
        assert request.jsonrpc == "2.0", "必须遵循 JSON-RPC 2.0 协议"
        assert request.id is not None, "请求必须包含 ID"
        assert request.method is not None, "请求必须包含方法名"
        assert request.params is not None, "请求必须包含参数"
        
        # 验证可序列化
        request_dict = request.model_dump()
        assert "jsonrpc" in request_dict, "序列化应包含 jsonrpc 字段"
        assert request_dict["jsonrpc"] == "2.0", "jsonrpc 版本必须为 2.0"
        
        print(f"✅ JSON-RPC 请求格式正确: {request_dict}")
    
    def test_jsonrpc_response_format(self):
        """测试 JSON-RPC 2.0 响应格式语义"""
        # 创建成功响应
        response = JSONRPCResponse(
            id=1,
            result={"content": [{"type": "text", "text": "测试结果"}]}
        )
        
        # 验证协议语义
        assert response.jsonrpc == "2.0", "必须遵循 JSON-RPC 2.0 协议"
        assert response.id == 1, "响应 ID 应与请求 ID 匹配"
        assert response.result is not None, "成功响应必须包含 result"
        
        print(f"✅ JSON-RPC 响应格式正确: {response.model_dump()}")
    
    def test_jsonrpc_error_response(self):
        """测试 JSON-RPC 错误响应语义"""
        # 创建错误响应
        response = JSONRPCResponse(
            id=1,
            error={"code": -32600, "message": "Invalid Request"}
        )
        
        # 验证错误语义
        assert response.error is not None, "错误响应必须包含 error"
        assert "code" in response.error, "错误必须包含错误码"
        assert "message" in response.error, "错误必须包含错误消息"
        
        # 标准错误码
        assert response.error["code"] in [-32700, -32600, -32601, -32602, -32603], \
            f"错误码必须是标准错误码，实际: {response.error['code']}"
        
        print(f"✅ JSON-RPC 错误响应语义正确: {response.error}")


class TestToolSchemas:
    """测试工具 Schema 定义的语义"""
    
    def test_tool_definition_semantic(self):
        """测试工具定义的语义完整性"""
        tool = ToolDefinition(
            name="search_knowledge_base",
            description="检索本地知识库",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "检索关键词"},
                    "top_k": {"type": "integer", "description": "返回结果数量"}
                },
                "required": ["query"]
            }
        )
        
        # 验证语义
        assert tool.name, "工具必须有名称"
        assert tool.description, "工具必须有描述"
        assert tool.inputSchema, "工具必须有输入 Schema"
        
        # 验证 Schema 结构
        schema = tool.inputSchema
        assert schema.get("type") == "object", "输入类型必须是 object"
        assert "properties" in schema, "必须定义属性"
        
        print(f"✅ 工具定义语义完整: {tool.name} - {tool.description}")
    
    def test_tool_result_format(self):
        """测试工具结果格式的语义"""
        result = ToolResult(
            content=[
                TextContent(type="text", text="检索到 3 条相关结果")
            ]
        )
        
        # 验证语义
        assert result.content, "工具结果必须包含内容"
        assert len(result.content) > 0, "内容列表不应为空"
        
        # 验证内容格式
        for content in result.content:
            assert content.type in ["text", "image", "resource"], \
                f"内容类型必须是 text/image/resource，实际: {content.type}"
            assert content.text, "文本内容不应为空"
        
        print(f"✅ 工具结果格式正确: {len(result.content)} 个内容项")


class TestMCPConfig:
    """测试 MCP 服务器配置的语义"""
    
    def test_server_config_completeness(self):
        """测试服务器配置的完整性"""
        # 验证配置不为空
        assert MCP_SERVERS, "MCP 服务器配置不应为空"
        assert len(MCP_SERVERS) >= 1, "至少应配置 1 个服务器"
        
        # 验证每个服务器的配置语义
        for name, config in MCP_SERVERS.items():
            assert "transport" in config, f"服务器 {name} 必须指定传输方式"
            assert config["transport"] == "stdio", f"当前仅支持 stdio 模式，实际: {config['transport']}"
            assert "command" in config, f"服务器 {name} 必须指定命令"
            assert "args" in config, f"服务器 {name} 必须指定参数"
            assert "description" in config, f"服务器 {name} 必须有描述"
            assert "category" in config, f"服务器 {name} 必须有分类"
            
            print(f"✅ 服务器配置完整: {name} ({config['category']})")
    
    def test_rag_server_config(self):
        """测试 RAG 服务器配置的语义"""
        assert "rag" in MCP_SERVERS, "必须配置 RAG 服务器"
        
        rag_config = MCP_SERVERS["rag"]
        assert rag_config["command"] == "python", "RAG 服务器应使用 python 命令"
        assert "-m" in rag_config["args"], "应使用模块模式启动"
        assert "app.tools.rag_server" in rag_config["args"], "应指定 RAG 服务器模块"
        assert rag_config["category"] == "knowledge", "RAG 服务器分类应为 knowledge"
        
        print(f"✅ RAG 服务器配置正确: {rag_config}")


class TestToolRouter:
    """测试工具路由器的语义"""
    
    def setup_method(self):
        """初始化测试"""
        self.router = ToolRouter(mcp_manager=None)  # 不需要实际管理器
    
    def test_role_tools_mapping_completeness(self):
        """测试角色工具映射的完整性"""
        # 验证所有 6 个角色都有配置
        expected_roles = ["white", "black", "yellow", "green", "purple", "red"]
        for role in expected_roles:
            assert role in ROLE_TOOLS, f"角色 {role} 必须有工具配置"
            
            config = ROLE_TOOLS[role]
            assert "servers" in config, f"角色 {role} 必须指定服务器"
            assert "tools" in config, f"角色 {role} 必须指定工具"
            assert "strategy" in config, f"角色 {role} 必须指定策略"
            assert config["strategy"] in ["mandatory", "optional", "none"], \
                f"策略必须是 mandatory/optional/none，实际: {config['strategy']}"
            
            print(f"✅ 角色 {role} 工具映射完整: {len(config['tools'])} 个工具")
    
    def test_white_hat_mandatory_strategy(self):
        """测试白帽强制使用工具策略的语义"""
        config = ROLE_TOOLS["white"]
        
        # 白帽应强制使用工具
        assert config["strategy"] == "mandatory", "白帽必须强制使用工具"
        assert len(config["tools"]) > 0, "白帽必须有可用工具"
        assert "search_knowledge_base" in config["tools"], "白帽应能检索知识库"
        
        # 验证路由器判断逻辑
        assert self.router.should_use_tools("white", "任何问题") == True, \
            "白帽应对任何问题都使用工具"
        
        print(f"✅ 白帽强制策略语义正确: {config['tools']}")
    
    def test_red_hat_no_tools(self):
        """测试红帽不使用工具的语义"""
        config = ROLE_TOOLS["red"]
        
        # 红帽不应使用工具
        assert config["strategy"] == "none", "红帽不应使用工具"
        assert len(config["tools"]) == 0, "红帽应无工具"
        assert len(config["servers"]) == 0, "红帽应无服务器"
        
        # 验证路由器判断逻辑
        assert self.router.should_use_tools("red", "任何问题") == False, \
            "红帽不应使用工具"
        
        print(f"✅ 红帽无工具策略语义正确")
    
    def test_optional_strategy_keyword_matching(self):
        """测试可选策略的关键词匹配语义"""
        # 黑帽使用可选策略
        test_cases = [
            ("AI 发展的最新数据是什么？", True),  # 包含"数据"、"最新"
            ("这个方案有什么风险？", False),  # 无关键词
            ("给我一些统计数据", True),  # 包含"统计"
            ("你的感觉如何？", False),  # 无关键词
        ]
        
        for question, expected in test_cases:
            result = self.router.should_use_tools("black", question)
            assert result == expected, \
                f"问题 '{question}' 预期 {expected}，实际 {result}"
        
        print(f"✅ 可选策略关键词匹配语义正确")
    
    def test_tools_prompt_generation(self):
        """测试工具提示词生成的语义"""
        # 白帽应有工具提示
        prompt = self.router.get_tools_prompt("white")
        assert prompt, "白帽应生成工具提示"
        assert "你可以使用以下工具" in prompt, "提示应包含引导语"
        assert "search_knowledge_base" in prompt, "提示应包含工具名称"
        
        # 红帽应无工具提示
        prompt = self.router.get_tools_prompt("red")
        assert prompt == "", "红帽不应生成工具提示"
        
        print(f"✅ 工具提示词生成语义正确")


class TestToolCallSemantics:
    """测试工具调用的语义质量"""
    
    def test_search_knowledge_base_semantic(self):
        """测试知识库检索工具的语义"""
        from app.tools.rag_tool import rag_tool
        
        # 测试空知识库
        result = rag_tool.search_knowledge_base("测试查询", top_k=3)
        
        # 验证语义质量
        assert result is not None, "检索结果不应为 None"
        assert isinstance(result, str), "结果应为字符串"
        assert len(result) > 0, "结果不应为空字符串"
        
        # 空知识库应返回友好提示
        assert "未找到" in result or "空" in result or "检索失败" in result, \
            f"应返回有意义的提示，实际: {result[:100]}"
        
        print(f"✅ 知识库检索语义正确: {result[:100]}")
    
    def test_add_document_semantic(self):
        """测试添加文档工具的语义"""
        from app.tools.rag_tool import rag_tool
        
        # 测试不存在的文件
        result = rag_tool.add_document("nonexistent.md")
        
        # 验证语义质量
        assert "不存在" in result or "失败" in result, \
            f"应返回明确的错误信息，实际: {result}"
        assert not result.startswith("成功"), "不存在的文件不应返回成功"
        
        print(f"✅ 添加文档语义正确: {result}")
    
    def test_list_documents_semantic(self):
        """测试列出文档工具的语义"""
        from app.tools.rag_tool import rag_tool
        
        result = rag_tool.list_documents()
        
        # 验证语义质量
        assert result is not None, "列出结果不应为 None"
        assert isinstance(result, str), "结果应为字符串"
        
        # 应包含状态信息
        assert "不存在" in result or "为空" in result or "文档列表" in result, \
            f"应包含明确的状态信息，实际: {result[:100]}"
        
        print(f"✅ 列出文档语义正确: {result[:100]}")
    
    def test_get_stats_semantic(self):
        """测试统计信息工具的语义"""
        from app.tools.rag_tool import rag_tool
        
        result = rag_tool.get_stats()
        
        # 验证语义质量
        assert result is not None, "统计结果不应为 None"
        assert isinstance(result, str), "结果应为字符串"
        
        # 应包含统计信息
        assert "不存在" in result or "统计信息" in result, \
            f"应包含统计信息，实际: {result[:100]}"
        
        if "统计信息" in result:
            assert "文档数量" in result, "应包含文档数量"
        
        print(f"✅ 统计信息语义正确: {result[:150]}")


class TestErrorHandling:
    """测试错误处理和降级语义"""
    
    def test_tool_call_error_message(self):
        """测试工具调用错误消息的语义"""
        from app.tools.rag_tool import rag_tool
        
        # 触发错误
        result = rag_tool.add_document("")  # 空路径
        
        # 验证错误消息语义
        assert result is not None, "错误情况应返回结果"
        assert isinstance(result, str), "结果应为字符串"
        
        # 应包含错误信息
        assert "失败" in result or "错误" in result or "异常" in result, \
            f"应包含错误信息，实际: {result}"
        
        # 不应抛出未捕获异常
        print(f"✅ 工具调用错误消息语义正确: {result}")
    
    def test_graceful_degradation(self):
        """测试优雅降级的语义"""
        from app.tools.rag_tool import rag_tool
        
        # 多种错误场景
        test_cases = [
            ("空查询", ""),
            ("不存在的文件", "nonexistent.md"),
            ("空文件路径", ""),
        ]
        
        for desc, query in test_cases:
            try:
                result = rag_tool.search_knowledge_base(query, top_k=3)
                # 应返回结果而非抛出异常
                assert result is not None, f"{desc} 应返回结果"
                print(f"✅ {desc} 优雅降级: {result[:50]}")
            except Exception as e:
                pytest.fail(f"{desc} 不应抛出未捕获异常: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
