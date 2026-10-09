"""
快速测试脚本 - 仅测试核心功能（避免超时）
"""
import requests
import sys

BASE_URL = "http://localhost:8001"

def quick_test():
    """快速测试核心功能"""
    print("=" * 80)
    print("🎭 头脑风暴智能体 - 快速测试")
    print("=" * 80)
    print()
    
    results = []
    
    # Test 1: Health Check
    print("1️⃣  测试健康检查...")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
        print("   ✅ 通过")
        results.append(("健康检查", True))
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        results.append(("健康检查", False))
    
    # Test 2: List Roles
    print("\n2️⃣  测试角色列表...")
    try:
        r = requests.get(f"{BASE_URL}/roles", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert len(data["roles"]) == 6
        print(f"   ✅ 通过 - {len(data['roles'])} 个角色")
        results.append(("角色列表", True))
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        results.append(("角色列表", False))
    
    # Test 3: Static Files - CSS
    print("\n3️⃣  测试 CSS 文件服务...")
    try:
        r = requests.get(f"{BASE_URL}/web/css/style.css", timeout=5)
        assert r.status_code == 200
        assert "text/css" in r.headers.get("content-type", "")
        print("   ✅ 通过")
        results.append(("CSS文件", True))
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        results.append(("CSS文件", False))
    
    # Test 4: Static Files - JS
    print("\n4️⃣  测试 JS 文件服务...")
    try:
        r = requests.get(f"{BASE_URL}/web/js/app.js", timeout=5)
        assert r.status_code == 200
        assert "javascript" in r.headers.get("content-type", "")
        print("   ✅ 通过")
        results.append(("JS文件", True))
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        results.append(("JS文件", False))
    
    # Test 5: Root Redirect
    print("\n5️⃣  测试根路径...")
    try:
        r = requests.get(f"{BASE_URL}/", timeout=5)
        assert r.status_code == 200
        assert "头脑风暴智能体" in r.text
        print("   ✅ 通过")
        results.append(("根路径", True))
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        results.append(("根路径", False))
    
    # Test 6: CORS
    print("\n6️⃣  测试 CORS 配置...")
    try:
        r = requests.options(
            f"{BASE_URL}/brainstorm",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
            timeout=5
        )
        assert r.status_code == 200
        print("   ✅ 通过")
        results.append(("CORS", True))
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        results.append(("CORS", False))
    
    # Summary
    print()
    print("=" * 80)
    print("📊 测试结果汇总")
    print("=" * 80)
    
    passed = sum(1 for _, status in results if status)
    total = len(results)
    
    for name, status in results:
        icon = "✅" if status else "❌"
        print(f"  {icon} {name}")
    
    print()
    print(f"总计: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
    print("=" * 80)
    
    if passed == total:
        print("\n🎉 所有核心测试通过！前后端集成正常！")
        return True
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查错误信息")
        return False

if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)
