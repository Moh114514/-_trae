@echo off
chcp 65001 >nul
title BEIMS Cloudflare Tunnel - 仅后端穿透 (8001)

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║  🌐 BEIMS Cloudflare Tunnel - 后端穿透                      ║
echo ║     后端 localhost:8001 ^-^> Cloudflare URL                 ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM 检查 cloudflared
where cloudflared >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: cloudflared 未安装
    echo.
    echo 💡 请先安装: npm install -g cloudflared
    echo.
    pause
    exit /b 1
)

echo 📍 启动信息:
echo   • 本地后端: http://localhost:8001
echo   • 将分配一个 Cloudflare URL (*.trycloudflare.com)
echo.

netstat -ano | findstr ":8001" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  警告: 后端服务未运行（端口 8001）
) else (
    echo ✅ 后端服务已在运行
)

echo.
echo 🚀 启动穿透...
echo.

cloudflared tunnel --url http://localhost:8001

pause
