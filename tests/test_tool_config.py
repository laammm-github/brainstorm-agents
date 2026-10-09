"""验证工具配置是否正确"""
import sys
sys.path.insert(0, '.')

from app.llm.tool_router import ToolRouter, ROLE_TOOLS

print("=" * 70)
print("🧪 验证MCP工具增强配置")
print("=" * 70)

# 验证阶段1：baidu_search工具
print("\n✅ 阶段1验证：baidu_search工具")
white_tools = ROLE_TOOLS.get("white", {})
black_tools = ROLE_TOOLS.get("black", {})
purple_tools = ROLE_TOOLS.get("purple", {})

assert "baidu-search" in white_tools.get("servers", []), "❌ 白帽缺少baidu-search服务器"
assert "baidu_search" in white_tools.get("tools", []), "❌ 白帽缺少baidu_search工具"
print("  ✅ 白帽：baidu-search服务器 + baidu_search工具")

assert "baidu-search" in black_tools.get("servers", []), "❌ 黑帽缺少baidu-search服务器"
assert "baidu_search" in black_tools.get("tools", []), "❌ 黑帽缺少baidu_search工具"
print("  ✅ 黑帽：baidu-search服务器 + baidu_search工具")

assert "baidu-search" in purple_tools.get("servers", []), "❌ 紫帽缺少baidu-search服务器"
assert "baidu_search" in purple_tools.get("tools", []), "❌ 紫帽缺少baidu_search工具"
assert "sequential-thinking" in purple_tools.get("servers", []), "❌ 紫帽缺少sequential-thinking服务器"
assert "sequential_thinking" in purple_tools.get("tools", []), "❌ 紫帽缺少sequential_thinking工具"
print("  ✅ 紫帽：baidu-search + sequential-thinking服务器 + baidu_search + sequential_thinking工具")

# 验证阶段2：execute_python工具
print("\n✅ 阶段2验证：execute_python工具")
assert "python-executor" in white_tools.get("servers", []), "❌ 白帽缺少python-executor服务器"
assert "execute_python" in white_tools.get("tools", []), "❌ 白帽缺少execute_python工具"
print("  ✅ 白帽：python-executor服务器 + execute_python工具")

assert "python-executor" in black_tools.get("servers", []), "❌ 黑帽缺少python-executor服务器"
assert "execute_python" in black_tools.get("tools", []), "❌ 黑帽缺少execute_python工具"
assert "fetch" in black_tools.get("servers", []), "❌ 黑帽缺少fetch服务器"
assert "fetch_url" in black_tools.get("tools", []), "❌ 黑帽缺少fetch_url工具"
print("  ✅ 黑帽：python-executor + fetch服务器 + execute_python + fetch_url工具")

yellow_tools = ROLE_TOOLS.get("yellow", {})
assert "fetch" in yellow_tools.get("servers", []), "❌ 黄帽缺少fetch服务器"
assert "fetch_url" in yellow_tools.get("tools", []), "❌ 黄帽缺少fetch_url工具"
assert "baidu-search" in yellow_tools.get("servers", []), "❌ 黄帽缺少baidu-search服务器"
assert "baidu_search" in yellow_tools.get("tools", []), "❌ 黄帽缺少baidu_search工具"
print("  ✅ 黄帽：fetch + baidu-search服务器 + fetch_url + baidu_search工具")

green_tools = ROLE_TOOLS.get("green", {})
assert "fetch" in green_tools.get("servers", []), "❌ 绿帽缺少fetch服务器"
assert "fetch_url" in green_tools.get("tools", []), "❌ 绿帽缺少fetch_url工具"
assert "memory" in green_tools.get("servers", []), "❌ 绿帽缺少memory服务器"
assert "query_memory" in green_tools.get("tools", []), "❌ 绿帽缺少query_memory工具"
print("  ✅ 绿帽：fetch + memory服务器 + fetch_url + query_memory工具")

assert "python-executor" in purple_tools.get("servers", []), "❌ 紫帽缺少python-executor服务器"
assert "execute_python" in purple_tools.get("tools", []), "❌ 紫帽缺少execute_python工具"
print("  ✅ 紫帽：python-executor服务器 + execute_python工具")

# 验证阶段3：read_file工具
print("\n✅ 阶段3验证：read_file工具")
assert "filesystem" in white_tools.get("servers", []), "❌ 白帽缺少filesystem服务器"
assert "read_file" in white_tools.get("tools", []), "❌ 白帽缺少read_file工具"
print("  ✅ 白帽：filesystem服务器 + read_file工具")

# 验证工具数量控制（3-5个）
print("\n✅ 工具数量验证（3-5个/角色）：")
for role, config in ROLE_TOOLS.items():
    tool_count = len(config.get("tools", []))
    if tool_count > 0:
        status = "✅" if 3 <= tool_count <= 5 else "⚠️"
        print(f"  {status} {role}帽: {tool_count}个工具 {config['tools']}")

# 验证MCP配置
print("\n✅ MCP服务器配置验证：")
from app.llm.mcp_config import MCP_SERVERS

required_servers = ["rag", "time", "python-executor", "filesystem", "fetch", "memory", "sequential-thinking", "baidu-search"]
for server in required_servers:
    assert server in MCP_SERVERS, f"❌ 缺少{server}服务器配置"
    print(f"  ✅ {server}服务器已配置")

print("\n" + "=" * 70)
print("✅ 所有验证通过！MCP工具增强配置正确！")
print("=" * 70)

print("\n📊 工具-角色映射总结：")
print("-" * 70)
print("角色     | 工具数量 | 工具列表")
print("-" * 70)
for role, config in ROLE_TOOLS.items():
    tools = config.get("tools", [])
    if tools:
        print(f"{role:8s} | {len(tools):2d}个     | {', '.join(tools)}")
print("-" * 70)
