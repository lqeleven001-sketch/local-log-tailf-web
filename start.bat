@echo off
chcp 65001 >nul
echo ========================================
echo   LogTail - 日志实时查看工具
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [信息] 检查依赖...
pip show aiohttp >nul 2>&1
if %errorlevel% neq 0 (
    echo [信息] 安装依赖...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

echo.
echo [信息] 启动 LogTail 服务器...
echo.
python server.py

pause
