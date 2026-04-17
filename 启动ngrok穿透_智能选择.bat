@echo off
chcp 65001 >nul
title BEIMS 双穿透启动 - 前端+后端API

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║  🌐 BEIMS ngrok 双穿透启动                                 ║
echo ║     同时穿透前端和后端 API                                ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

echo 📝 这个方案会启动两个独立的 ngrok tunnel:
echo   1. 前端穿透 (port 3000)
echo   2. 后端 API 穿透 (port 8001)
echo.

echo ⚠️  方案选择:
echo.
echo [1] 仅穿透前端 (推荐 - 简单快速)
echo     • 只穿透 port 3000 (前端)
echo     • 后端 API 通过前端的相同域转发
echo.
echo [2] 同时穿透前端和后端 (完全隔离)
echo     • 需要启动两个 ngrok 进程
echo     • 前端: ngrok http 3000
echo     • 后端: ngrok http 8001
echo     • 需要手动配置后端 URL
echo.

set /p choice="请选择 [1 或 2]: "

if "%choice%"=="1" (
    echo.
    echo 🚀 启动方案 1: 仅穿透前端...
    echo.
    echo ngrok http 3000
    echo.
    echo 📍 访问地址会显示: https://xxx.ngrok-free.dev
    echo.
    echo ✅ 完成后，在浏览器访问该 URL 即可
    echo.
    ngrok http 3000
) else if "%choice%"=="2" (
    echo.
    echo 🚀 启动方案 2: 同时穿透前端和后端...
    echo.
    echo 这需要启动两个终端窗口...
    echo.
    echo 终端 1 - 前端穿透（自动启动）:
    start "BEIMS Frontend Tunnel" cmd /k "ngrok http 3000"
    
    echo.
    echo 等待 5 秒后再启动后端穿透...
    timeout /t 5 /nobreak >nul
    
    echo.
    echo 终端 2 - 后端 API 穿透:
    start "BEIMS Backend Tunnel" cmd /k "ngrok http 8001"
    
    echo.
    echo ⏳ 等待两个穿透都启动...
    timeout /t 3 /nobreak >nul
    
    echo.
    echo 📊 穿透信息将显示在两个新窗口中
    echo    • 前端窗口: 记下 https://xxx.ngrok-free.dev
    echo    • 后端窗口: 记下 https://yyy.ngrok-free.dev/chat
    echo.
    echo 📝 然后用前端 URL 访问，浮窗会自动使用同一主机的 API
    echo    或者手动在浮窗中设置后端 API 地址
    echo.
    pause
) else (
    echo.
    echo ❌ 无效选择，请输入 1 或 2
    pause
    exit /b 1
)

pause
