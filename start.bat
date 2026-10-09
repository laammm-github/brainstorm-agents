@echo off
chcp 65001 >nul
echo ========================================
echo   头脑风暴智能体 - 快速启动脚本
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

echo [1/3] 检查虚拟环境...
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
    echo 虚拟环境创建成功！
) else (
    echo 虚拟环境已存在
)

echo.
echo [2/3] 激活虚拟环境并安装依赖...
call venv\Scripts\activate.bat
pip install -r requirements.txt -q

echo.
echo [3/3] 请复制 .env.example 为 .env 并填写 API Key
if not exist ".env" (
    copy .env.example .env
    echo 已创建 .env 文件，请编辑并填写 LLM_API_KEY
)

echo.
echo ========================================
echo   请编辑 .env 文件，填写你的 API Key
echo   然后运行: python main.py
echo ========================================
pause
