@echo off
chcp 65001 >nul
title BEIMS Cloudflare Tunnel - 仅前端穿透 (3000)

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║  🌐 BEIMS Cloudflare Tunnel - 前端穿透                      ║
echo ║     前端 localhost:3000 ^-^> Cloudflare URL                 ║
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
echo   • 本地前端: http://localhost:3000
echo   • 将分配一个 Cloudflare URL (*.trycloudflare.com)
echo.

netstat -ano | findstr ":3000" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  警告: 前端服务未运行（端口 3000）
) else (
    echo ✅ 前端服务已在运行
)

echo.
echo 🚀 启动穿透...
echo.

cloudflared tunnel --url http://localhost:3000

pause
