@echo off
setlocal enabledelayedexpansion

:: 设置窗口标题
title RC Filtering Runner

:: 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python and add it to PATH.
    pause
    exit /b 1
)

:: 进入脚本所在目录
cd /d %~dp0

:: 创建虚拟环境 (如果不存在)
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

:: 激活虚拟环境并安装/更新依赖
echo [INFO] Activating virtual environment and checking requirements...
call venv\Scripts\activate.bat

if exist "requirements.txt" (
    echo [INFO] Installing/Updating dependencies...
    pip install -r requirements.txt
)

:: 运行主程序
echo [INFO] Starting RC Filtering...
:: 设置 PYTHONPATH 确保可以正确导入 src 下的模块
set PYTHONPATH=%PYTHONPATH%;%~dp0src
python src/main.py

:: 运行结束后的处理
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Program exited with error code %errorlevel%.
    pause
)

deactivate
