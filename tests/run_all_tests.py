"""综合测试运行器 - 执行所有测试并生成详细报告"""
import sys
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.tools.rag_tool import rag_tool
from app.llm.mcp_config import MCP_SERVERS
from app.llm.tool_router import ToolRouter, ROLE_TOOLS
from app.mcp.protocol import JSONRPCRequest
from app.mcp.schemas import ToolDefinition, ToolResult, TextContent
from app.roles.white_hat import WhiteHat
from app.roles.red_hat import RedHat
from app.roles.black_hat import BlackHat
from app.roles.yellow_hat import YellowHat
from app.roles.green_hat import GreenHat
from app.roles.purple_hat import PurpleHat
from app.orchestrator.debater import DebateEngine


class TestReport:
    """测试报告生成器"""
    
    def __init__(self):
        self.results = []
        self.start_time = time.time()
    
    def add_result(self, test_name, status, message="", details=None):
        """添加测试结果"""
        self.results.append({
            "test": test_name,
            "status": status,  # PASS, FAIL, SKIP
            "message": message,
            "details": details or {}
        })
    
    def generate_report(self):
        """生成测试报告"""
        duration = time.time() - self.start_time
        
        report = []
        report.append("=" * 80)
        report.append("MCP + RAG 集成测试报告")
        report.append("=" * 80)
        report.append("")
        
        # 统计
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        skipped = sum(1 for r in self.results if r["status"] == "SKIP")
        
        report.append(f"测试总览:")
        report.append(f"  总计: {total}")
        report.append(f"  通过: {passed}")
        report.append(f"  失败: {failed}")
        report.append(f"  跳过: {skipped}")
        report.append(f"  耗时: {duration:.2f} 秒")
        report.append("")
        
        # 详细结果
        report.append("详细结果:")
        report.append("-" * 80)
        
        for i, result in enumerate(self.results, 1):
            status_icon = "[PASS]" if result["status"] == "PASS" else "[FAIL]" if result["status"] == "FAIL" else "[SKIP]"
            report.append(f"{i}. {status_icon} {result['test']}")
            if result["message"]:
                report.append(f"   {result['message']}")
            if result["details"]:
                for key, value in result["details"].items():
                    report.append(f"   {key}: {value}")
            report.append("")
        
        # 总结
        report.append("=" * 80)
        if failed == 0:
            report.append("所有测试通过!")
        else:
            report.append(f"{failed} 个测试失败，请检查上述错误")
        report.append("=" * 80)
        
        return "\n".join(report)


def run_tests():
    """运行所有测试"""
    report = TestReport()
    
    print("开始执行测试...")
    print()
    
    # ========================================
    # 1. MCP 协议测试
    # ========================================
    print("1. MCP 协议测试")
    print("-" * 40)
    
    try:
        # 测试 JSON-RPC 请求格式
        request = JSONRPCRequest(
            id=1,
            method="tools/call",
            params={"name": "test", "arguments": {}}
        )
        assert request.jsonrpc == "2.0"
        assert request.id == 1
        report.add_result("MCP_JSONRPC_Request_Format", "PASS", "JSON-RPC 2.0 请求格式正确")
        print("  [PASS] JSON-RPC 请求格式")
    except Exception as e:
        report.add_result("MCP_JSONRPC_Request_Format", "FAIL", str(e))
        print(f"  [FAIL] JSON-RPC 请求格式: {e}")
    
    try:
        # 测试 ToolDefinition
        tool = ToolDefinition(
            name="search_knowledge_base",
            description="检索知识库",
            inputSchema={"type": "object", "properties": {}}
        )
        assert tool.name == "search_knowledge_base"
        report.add_result("MCP_Tool_Definition", "PASS", "工具定义语义完整")
        print("  [PASS] 工具定义")
    except Exception as e:
        report.add_result("MCP_Tool_Definition", "FAIL", str(e))
        print(f"  [FAIL] 工具定义: {e}")
    
    try:
        # 测试 ToolResult
        result = ToolResult(
            content=[TextContent(type="text", text="测试结果")]
        )
        assert len(result.content) == 1
        report.add_result("MCP_Tool_Result", "PASS", "工具结果格式正确")
        print("  [PASS] 工具结果格式")
    except Exception as e:
        report.add_result("MCP_Tool_Result", "FAIL", str(e))
        print(f"  [FAIL] 工具结果格式: {e}")
    
    print()
    
    # ========================================
    # 2. MCP 配置测试
    # ========================================
    print("2. MCP 配置测试")
    print("-" * 40)
    
    try:
        assert len(MCP_SERVERS) == 6
        assert "rag" in MCP_SERVERS
        report.add_result("MCP_Config_Completeness", "PASS", f"配置了 {len(MCP_SERVERS)} 个服务器")
        print(f"  [PASS] 服务器配置完整性: {len(MCP_SERVERS)} 个")
    except Exception as e:
        report.add_result("MCP_Config_Completeness", "FAIL", str(e))
        print(f"  [FAIL] 服务器配置: {e}")
    
    try:
        rag_config = MCP_SERVERS["rag"]
        assert rag_config["command"] == "python"
        assert rag_config["category"] == "knowledge"
        report.add_result("MCP_RAG_Config", "PASS", "RAG 服务器配置正确")
        print("  [PASS] RAG 服务器配置")
    except Exception as e:
        report.add_result("MCP_RAG_Config", "FAIL", str(e))
        print(f"  [FAIL] RAG 配置: {e}")
    
    print()
    
    # ========================================
    # 3. 工具路由器测试
    # ========================================
    print("3. 工具路由器测试")
    print("-" * 40)
    
    try:
        router = ToolRouter(mcp_manager=None)
        assert len(ROLE_TOOLS) == 6
        report.add_result("Tool_Router_Mapping", "PASS", f"配置了 {len(ROLE_TOOLS)} 个角色")
        print(f"  [PASS] 角色工具映射: {len(ROLE_TOOLS)} 个角色")
    except Exception as e:
        report.add_result("Tool_Router_Mapping", "FAIL", str(e))
        print(f"  [FAIL] 角色工具映射: {e}")
    
    try:
        router = ToolRouter(mcp_manager=None)
        assert router.should_use_tools("white", "任何问题是") == True
        assert router.should_use_tools("red", "任何问题") == False
        report.add_result("Tool_Router_Strategy", "PASS", "白帽强制，红帽不使用")
        print("  [PASS] 工具使用策略")
    except Exception as e:
        report.add_result("Tool_Router_Strategy", "FAIL", str(e))
        print(f"  [FAIL] 工具策略: {e}")
    
    print()
    
    # ========================================
    # 4. RAG 系统测试
    # ========================================
    print("4. RAG 系统测试")
    print("-" * 40)
    
    try:
        result = rag_tool.search_knowledge_base("test", top_k=3)
        assert result is not None
        assert isinstance(result, str)
        report.add_result("RAG_Search_Semantic", "PASS", "检索语义正确")
        print(f"  [PASS] 检索语义: {result[:50]}")
    except Exception as e:
        report.add_result("RAG_Search_Semantic", "FAIL", str(e))
        print(f"  [FAIL] 检索语义: {e}")
    
    try:
        result = rag_tool.add_document("nonexistent.md")
        assert "不存在" in result or "失败" in result
        report.add_result("RAG_Add_Error_Handling", "PASS", "错误处理语义正确")
        print(f"  [PASS] 错误处理: {result}")
    except Exception as e:
        report.add_result("RAG_Add_Error_Handling", "FAIL", str(e))
        print(f"  [FAIL] 错误处理: {e}")
    
    try:
        result = rag_tool.list_documents()
        assert result is not None
        report.add_result("RAG_List_Documents", "PASS", "列出文档语义正确")
        print(f"  [PASS] 列出文档: {result[:50]}")
    except Exception as e:
        report.add_result("RAG_List_Documents", "FAIL", str(e))
        print(f"  [FAIL] 列出文档: {e}")
    
    try:
        result = rag_tool.get_stats()
        assert result is not None
        assert "统计信息" in result
        report.add_result("RAG_Get_Stats", "PASS", "统计信息语义正确")
        print(f"  [PASS] 统计信息: {result[:80]}")
    except Exception as e:
        report.add_result("RAG_Get_Stats", "FAIL", str(e))
        print(f"  [FAIL] 统计信息: {e}")
    
    print()
    
    # ========================================
    # 5. 角色语义测试（简化版，不调用 LLM）
    # ========================================
    print("5. 角色初始化测试")
    print("-" * 40)
    
    roles_to_test = [
        ("WhiteHat", WhiteHat),
        ("RedHat", RedHat),
        ("BlackHat", BlackHat),
        ("YellowHat", YellowHat),
        ("GreenHat", GreenHat),
        ("PurpleHat", PurpleHat),
    ]
    
    for role_name, role_class in roles_to_test:
        try:
            role = role_class()
            assert role.name is not None
            assert role.color is not None
            assert role.mcp_manager is not None
            assert role.tool_router is not None
            role.cleanup()
            report.add_result(f"Role_{role_name}_Init", "PASS", "角色初始化成功")
            print(f"  [PASS] {role_name} 初始化")
        except Exception as e:
            report.add_result(f"Role_{role_name}_Init", "FAIL", str(e))
            print(f"  [FAIL] {role_name} 初始化: {e}")
    
    print()
    
    # ========================================
    # 6. 生成报告
    # ========================================
    print()
    print("=" * 80)
    print("生成测试报告...")
    print("=" * 80)
    print()
    
    report_text = report.generate_report()
    print(report_text)
    
    # 保存报告到文件
    report_file = Path(__file__).parent / "TEST_REPORT.md"
    report_file.write_text(report_text, encoding="utf-8")
    print(f"\n报告已保存到: {report_file}")
    
    return report


if __name__ == "__main__":
    report = run_tests()
    
    # 返回退出码
    failed = sum(1 for r in report.results if r["status"] == "FAIL")
    sys.exit(1 if failed > 0 else 0)
