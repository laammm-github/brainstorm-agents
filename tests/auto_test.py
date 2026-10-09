"""自动化测试脚本 - 运行头脑风暴并捕获日志"""
import subprocess
import sys
import os

# 设置工作目录
os.chdir(r"D:\agent-interview-guidance\projects\brainstorm-agents")

# 测试问题
test_question = "是否应该学习 AI Agent 开发？"

print("="*70)
print("🧪 开始自动化测试")
print("="*70)

# 运行 main.py 并捕获输出
try:
    # 设置环境变量强制使用 UTF-8
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    
    result = subprocess.run(
        [sys.executable, "main.py"],
        input=test_question + "\nexit\n",
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        timeout=300,  # 5分钟超时
        env=env  # 传递环境变量
    )
    
    # 保存日志到文件
    log_file = r"D:\agent-interview-guidance\projects\brainstorm-agents\tests\test_output.txt"
    with open(log_file, 'w', encoding='utf-8', errors='replace') as f:
        f.write(result.stdout)
        if result.stderr:
            f.write("\n\n=== STDERR ===\n")
            f.write(result.stderr)
    
    print(f"✅ 测试完成！日志已保存到: {log_file}")
    print(f"📊 输出行数: {len(result.stdout.splitlines())}")
    
    # 检查是否有错误
    if result.returncode != 0:
        print(f"⚠️  程序退出码: {result.returncode}")
    
    # 显示最后20行
    print("\n" + "="*70)
    print("📄 最后20行输出:")
    print("="*70)
    lines = result.stdout.splitlines()
    for line in lines[-20:]:
        print(line)
        
except subprocess.TimeoutExpired:
    print("❌ 测试超时（超过5分钟）")
except Exception as e:
    print(f"❌ 测试失败: {e}")
