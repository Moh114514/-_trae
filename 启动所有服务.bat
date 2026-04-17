@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title BEIMS 完整启动工具 - 启动所有服务
color 0A

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║  🚀 BEIMS 建筑能源智能管理系统                           ║
echo ║     完整启动工具 - 后端 + 前端(生产模式)                ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

set "ROOT_DIR=%~dp0"
set "BACKEND_DIR=%ROOT_DIR%BEIMS建筑能源智能管理系统\backend"
set "FRONTEND_DIR=%ROOT_DIR%BEIMS建筑能源智能管理系统\frontend"
set "VENV_PYTHON=%ROOT_DIR%.venv\Scripts\python.exe"

echo 📍 项目根目录: %ROOT_DIR%
echo.

REM ========== 启动后端 ==========
echo 【1】启动后端服务 (port 8001)...
cd /d "%BACKEND_DIR%"
if not exist "%VENV_PYTHON%" (
    echo ❌ 虚拟环境未找到!
    echo    预期路径: %VENV_PYTHON%
    pause
    exit /b 1
)
echo ✅ 使用虚拟环境: %VENV_PYTHON%
start "BEIMS Backend" cmd /c "title BEIMS Backend Service && "%VENV_PYTHON%" -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload && pause"
echo ⏳ 后端启动中...
timeout /t 3 /nobreak >nul
echo ✅ 后端启动命令已执行
echo.

REM ========== 启动前端 ==========
echo 【2】启动前端服务 (port 3000 - 生产模式)...
cd /d "%FRONTEND_DIR%"
start "BEIMS Frontend" cmd /c "title BEIMS Frontend Service && npx vite preview --port 3000 && pause"
echo ⏳ 前端启动中...
timeout /t 3 /nobreak >nul
echo ✅ 前端启动命令已执行
echo.

REM ========== 提示信息 ==========
echo ════════════════════════════════════════════════════════════
echo ✅ 所有服务启动完成！
echo ════════════════════════════════════════════════════════════
echo.
echo 📊 服务地址:
echo   • 后端 API:   http://localhost:8001
echo   • 前端页面:   http://localhost:3000
echo   • 健康检查:   http://localhost:8001/health
echo.
echo 📝 调试窗口:
echo   • 后端窗口:   BEIMS Backend Service (自动打开)
echo   • 前端窗口:   BEIMS Frontend Service (自动打开)
echo.
echo 🌐 下一步 - 启动内网穿透:
echo   1. 打开新的 PowerShell
echo   2. 执行: ngrok http 3000
echo   3. 复制生成的 URL 分享
echo.
echo 🛑 停止服务:
echo   • 关闭对应的服务窗口即可
echo.
pause
exit /b 0
