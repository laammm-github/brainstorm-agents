"""测试并行执行逻辑"""
import time
from app.roles.white_hat import WhiteHat
from app.roles.red_hat import RedHat
from app.roles.black_hat import BlackHat
from app.roles.yellow_hat import YellowHat
from app.roles.green_hat import GreenHat
from app.roles.purple_hat import PurpleHat
from app.orchestrator.debater import DebateEngine


def test_parallel_execution():
    """测试并行执行是否正确"""
    print("=" * 60)
    print("测试并行执行逻辑")
    print("=" * 60)
    
    # 初始化 6 个角色
    roles = [
        WhiteHat(),
        RedHat(),
        BlackHat(),
        YellowHat(),
        GreenHat(),
        PurpleHat()
    ]
    
    # 测试问题
    question = "是否应该学习 AI Agent 开发？"
    
    # 测试 1: 串行执行
    print("\n📊 测试 1: 串行执行")
    print("-" * 60)
    debater_serial = DebateEngine(roles, use_parallel=False)
    start_time = time.time()
    results_serial = debater_serial.execute_debate(question)
    serial_duration = time.time() - start_time
    print(f"\n⏱️ 串行耗时: {serial_duration:.2f} 秒")
    print(f"📝 Round 1 结果数量: {len(results_serial['round_1'])}")
    print(f"📝 Round 2 结果数量: {len(results_serial['round_2'])}")
    
    # 验证结果完整性
    assert len(results_serial['round_1']) == 6, "Round 1 应该有 6 个结果"
    assert len(results_serial['round_2']) == 6, "Round 2 应该有 6 个结果"
    
    # 测试 2: 并行执行
    print("\n\n📊 测试 2: 并行执行")
    print("-" * 60)
    debater_parallel = DebateEngine(roles, use_parallel=True)
    start_time = time.time()
    results_parallel = debater_parallel.execute_debate(question)
    parallel_duration = time.time() - start_time
    print(f"\n⏱️ 并行耗时: {parallel_duration:.2f} 秒")
    print(f"📝 Round 1 结果数量: {len(results_parallel['round_1'])}")
    print(f"📝 Round 2 结果数量: {len(results_parallel['round_2'])}")
    
    # 验证结果完整性
    assert len(results_parallel['round_1']) == 6, "Round 1 应该有 6 个结果"
    assert len(results_parallel['round_2']) == 6, "Round 2 应该有 6 个结果"
    
    # 验证角色名称正确性
    expected_colors = {'white', 'red', 'black', 'yellow', 'green', 'purple'}
    assert set(results_parallel['round_1'].keys()) == expected_colors, "Round 1 角色颜色不匹配"
    assert set(results_parallel['round_2'].keys()) == expected_colors, "Round 2 角色颜色不匹配"
    
    # 性能对比
    print("\n\n📈 性能对比")
    print("-" * 60)
    print(f"串行耗时: {serial_duration:.2f} 秒")
    print(f"并行耗时: {parallel_duration:.2f} 秒")
    speedup = serial_duration / parallel_duration if parallel_duration > 0 else 0
    print(f"加速比: {speedup:.2f}x")
    
    # 结果对比
    print("\n\n✅ 验证结果")
    print("-" * 60)
    print("✓ 串行和并行都返回了正确的结果数量")
    print("✓ 角色颜色映射正确（闭包问题已修复）")
    print(f"✓ 并行加速比: {speedup:.2f}x")
    
    print("\n" + "=" * 60)
    print("测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    test_parallel_execution()
