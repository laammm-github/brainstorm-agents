"""
前后端集成测试 - 完整测试套件
测试 FastAPI 后端和 Web 前端的集成
"""
import requests
import pytest
import time
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, Any

# 测试配置
BASE_URL = "http://localhost:8001"
TIMEOUT = 120  # 请求超时时间（秒） - 增加到120秒以适应LLM响应


class TestAPILayer:
    """API 接口测试"""
    
    def test_health_check(self):
        """测试健康检查接口"""
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        print("✅ 健康检查接口正常")
    
    def test_list_roles(self):
        """测试角色列表接口"""
        response = requests.get(f"{BASE_URL}/roles", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert "roles" in data
        assert len(data["roles"]) == 6
        
        # 验证每个角色的数据结构
        for role in data["roles"]:
            assert "name" in role
            assert "color" in role
            assert "description" in role
        
        # 验证6个角色都存在
        role_names = [role["name"] for role in data["roles"]]
        expected_roles = ["白帽", "红帽", "黑帽", "黄帽", "绿帽", "紫帽"]
        for expected in expected_roles:
            assert expected in role_names, f"缺少角色: {expected}"
        
        print(f"✅ 角色列表接口正常，共 {len(data['roles'])} 个角色")
    
    def test_brainstorm_request_validation(self):
        """测试头脑风暴请求验证"""
        # 测试空问题
        response = requests.post(
            f"{BASE_URL}/brainstorm",
            json={"question": "", "max_rounds": 2},
            timeout=TIMEOUT
        )
        # 应该返回 422 或正常处理（取决于后端实现）
        assert response.status_code in [200, 422]
        print("✅ 请求验证正常")
    
    def test_brainstorm_basic(self):
        """测试基础头脑风暴功能"""
        question = "是否应该学习AI Agent开发？"
        response = requests.post(
            f"{BASE_URL}/brainstorm",
            json={"question": question, "max_rounds": 2},
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证响应结构
        assert "problem_type" in data
        assert "selected_roles" in data
        assert "debate_results" in data
        assert "final_report" in data
        
        # 验证数据类型
        assert isinstance(data["problem_type"], str)
        assert isinstance(data["selected_roles"], list)
        assert isinstance(data["debate_results"], dict)
        assert isinstance(data["final_report"], str)
        
        # 验证辩论结果包含轮次
        assert "round_1" in data["debate_results"]
        
        # 验证有内容生成
        assert len(data["final_report"]) > 0
        assert len(data["selected_roles"]) > 0
        
        print(f"✅ 头脑风暴基础功能正常")
        print(f"   - 问题类型: {data['problem_type']}")
        print(f"   - 选择角色: {', '.join(data['selected_roles'])}")
        print(f"   - 报告长度: {len(data['final_report'])} 字符")
    
    def test_brainstorm_with_different_questions(self):
        """测试不同类型的问题"""
        questions = [
            "是否应该跳槽到创业公司？",
            "如何平衡工作与生活？",
            "AI会取代程序员吗？"
        ]
        
        for question in questions:
            response = requests.post(
                f"{BASE_URL}/brainstorm",
                json={"question": question, "max_rounds": 2},
                timeout=TIMEOUT
            )
            assert response.status_code == 200
            data = response.json()
            assert "final_report" in data
            print(f"✅ 问题测试通过: {question[:20]}...")
    
    def test_cors_headers(self):
        """测试CORS配置"""
        response = requests.options(
            f"{BASE_URL}/brainstorm",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
            timeout=TIMEOUT
        )
        
        # 检查 CORS  headers
        assert "access-control-allow-origin" in response.headers or response.status_code == 200
        print("✅ CORS配置正常")


class TestFrontendLayer:
    """前端页面测试"""
    
    def test_index_html_exists(self):
        """测试HTML文件存在"""
        web_dir = Path(__file__).parent.parent / "web"
        index_file = web_dir / "index.html"
        assert index_file.exists(), "index.html 文件不存在"
        print("✅ index.html 文件存在")
    
    def test_css_exists(self):
        """测试CSS文件存在"""
        web_dir = Path(__file__).parent.parent / "web"
        css_file = web_dir / "css" / "style.css"
        assert css_file.exists(), "style.css 文件不存在"
        print("✅ style.css 文件存在")
    
    def test_js_exists(self):
        """测试JS文件存在"""
        web_dir = Path(__file__).parent.parent / "web"
        js_file = web_dir / "js" / "app.js"
        assert js_file.exists(), "app.js 文件不存在"
        print("✅ app.js 文件存在")
    
    def test_html_content(self):
        """测试HTML内容结构"""
        web_dir = Path(__file__).parent.parent / "web"
        index_file = web_dir / "index.html"
        
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 验证关键元素存在
        assert 'id="chatMessages"' in content, "缺少 chatMessages 元素"
        assert 'id="userInput"' in content, "缺少 userInput 元素"
        assert 'id="sendBtn"' in content, "缺少 sendBtn 元素"
        assert 'id="statusPanel"' in content, "缺少 statusPanel 元素"
        assert 'startBrainstorm()' in content, "缺少 startBrainstorm 函数调用"
        
        # 验证六顶思考帽角色显示
        expected_roles = ["白帽", "红帽", "黑帽", "黄帽", "绿帽", "紫帽"]
        for role in expected_roles:
            assert role in content, f"缺少角色: {role}"
        
        print("✅ HTML内容结构正确")
    
    def test_js_functions(self):
        """测试JavaScript功能函数存在"""
        web_dir = Path(__file__).parent.parent / "web"
        js_file = web_dir / "js" / "app.js"
        
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 验证关键函数存在
        required_functions = [
            'startBrainstorm',
            'addUserMessage',
            'displayResults',
            'displayRound',
            'showLoading',
            'hideLoading',
            'updateStatus',
            'showError',
            'escapeHtml'
        ]
        
        for func in required_functions:
            assert f'function {func}' in content or f'{func} =' in content, f"缺少函数: {func}"
        
        # 验证API调用
        assert 'fetch(' in content, "缺少 fetch API 调用"
        assert '/brainstorm' in content, "缺少 /brainstorm 端点"
        
        print("✅ JavaScript功能函数完整")
    
    def test_css_variables(self):
        """测试CSS变量定义"""
        web_dir = Path(__file__).parent.parent / "web"
        css_file = web_dir / "css" / "style.css"
        
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 验证思考帽颜色变量
        hat_colors = [
            '--white-hat',
            '--red-hat',
            '--black-hat',
            '--yellow-hat',
            '--green-hat',
            '--purple-hat'
        ]
        
        for color in hat_colors:
            assert color in content, f"缺少CSS变量: {color}"
        
        print("✅ CSS变量定义完整")


class TestIntegrationLayer:
    """前后端集成测试"""
    
    def test_static_file_serving(self):
        """测试静态文件服务"""
        # 测试 CSS 文件可访问
        css_response = requests.get(f"{BASE_URL}/web/css/style.css", timeout=TIMEOUT)
        assert css_response.status_code == 200
        assert "text/css" in css_response.headers.get("content-type", "")
        print("✅ CSS静态文件服务正常")
        
        # 测试 JS 文件可访问
        js_response = requests.get(f"{BASE_URL}/web/js/app.js", timeout=TIMEOUT)
        assert js_response.status_code == 200
        assert "javascript" in js_response.headers.get("content-type", "")
        print("✅ JS静态文件服务正常")
    
    def test_root_redirect(self):
        """测试根路径重定向"""
        response = requests.get(f"{BASE_URL}/", timeout=TIMEOUT, allow_redirects=True)
        assert response.status_code == 200
        # 应该返回 HTML 内容
        assert "text/html" in response.headers.get("content-type", "")
        assert "头脑风暴智能体" in response.text
        print("✅ 根路径重定向正常")
    
    def test_api_from_frontend(self):
        """测试前端调用API的完整流程"""
        # 模拟前端发送请求
        payload = {
            "question": "测试前后端集成",
            "max_rounds": 2
        }
        
        headers = {
            "Content-Type": "application/json",
            "Origin": "http://localhost:3000"  # 模拟前端域名
        }
        
        response = requests.post(
            f"{BASE_URL}/brainstorm",
            json=payload,
            headers=headers,
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证响应可用于前端显示
        assert data["problem_type"]
        assert data["selected_roles"]
        assert data["debate_results"]["round_1"]
        assert data["final_report"]
        
        print("✅ 前端API调用集成正常")
    
    def test_error_handling(self):
        """测试错误处理机制"""
        # 测试无效JSON
        response = requests.post(
            f"{BASE_URL}/brainstorm",
            data="invalid json",
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        assert response.status_code in [400, 422]
        print("✅ 错误处理机制正常")


class TestEndToEnd:
    """端到端测试"""
    
    def test_complete_user_flow(self):
        """测试完整用户流程"""
        print("\n📋 开始端到端测试：完整用户流程")
        
        # Step 1: 用户访问页面
        response = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
        assert response.status_code == 200
        print("  ✅ Step 1: 页面加载成功")
        
        # Step 2: 检查页面元素
        assert "头脑风暴智能体" in response.text
        assert "chatMessages" in response.text
        assert "userInput" in response.text
        print("  ✅ Step 2: 页面元素完整")
        
        # Step 3: 提交问题
        question = "是否应该学习Python编程？"
        brainstorm_response = requests.post(
            f"{BASE_URL}/brainstorm",
            json={"question": question, "max_rounds": 2},
            timeout=TIMEOUT
        )
        assert brainstorm_response.status_code == 200
        data = brainstorm_response.json()
        print(f"  ✅ Step 3: 问题提交成功 - {question}")
        
        # Step 4: 验证响应数据
        assert "problem_type" in data
        assert "debate_results" in data
        assert "final_report" in data
        print(f"  ✅ Step 4: 响应数据完整")
        print(f"     - 问题类型: {data['problem_type']}")
        print(f"     - 辩论轮次: {len(data['debate_results'])} 轮")
        print(f"     - 报告长度: {len(data['final_report'])} 字符")
        
        # Step 5: 验证辩论内容
        round_1 = data["debate_results"]["round_1"]
        assert len(round_1) > 0, "Round 1 应该有内容"
        print(f"  ✅ Step 5: 辩论内容生成成功")
        print(f"     - Round 1 角色数: {len(round_1)}")
        
        # Step 6: 验证报告质量
        report = data["final_report"]
        assert len(report) > 100, "报告应该有一定长度"
        print(f"  ✅ Step 6: 报告质量合格")
        
        print("\n🎉 端到端测试完成！")
    
    def test_multiple_question_types(self):
        """测试多种问题类型"""
        test_cases = [
            ("决策类", "是否应该买房？"),
            ("认知类", "AI技术未来5年会如何发展？"),
            ("情感类", "如何处理职场人际关系？"),
            ("创意类", "如何设计一个创新的社交应用？")
        ]
        
        print("\n📋 测试多种问题类型")
        for category, question in test_cases:
            response = requests.post(
                f"{BASE_URL}/brainstorm",
                json={"question": question, "max_rounds": 2},
                timeout=TIMEOUT
            )
            assert response.status_code == 200
            data = response.json()
            assert data["final_report"]
            print(f"  ✅ {category}: {question[:15]}...")
        
        print("\n🎉 所有问题类型测试通过！")


def run_tests():
    """运行所有测试"""
    print("=" * 80)
    print("🎭 头脑风暴智能体 - 前后端集成测试")
    print("=" * 80)
    print()
    
    # 检查后端服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务运行正常")
        else:
            print(f"❌ 后端服务异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到后端服务: {BASE_URL}")
        print("请先启动后端服务: python -m app.api.app")
        return False
    
    print()
    print("=" * 80)
    print("开始执行测试...")
    print("=" * 80)
    print()
    
    # 运行 pytest
    pytest_args = [
        __file__,
        "-v",
        "--tb=short",
        "-s"
    ]
    
    exit_code = pytest.main(pytest_args)
    
    print()
    print("=" * 80)
    if exit_code == 0:
        print("🎉 所有测试通过！")
    else:
        print(f"❌ 部分测试失败，退出码: {exit_code}")
    print("=" * 80)
    
    return exit_code == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
