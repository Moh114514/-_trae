@echo off
chcp 65001 >nul
title BEIMS Cloudflare Tunnel - 前端 + 后端穿透

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║  🌐 BEIMS Cloudflare Tunnel - 前端 + 后端穿透               ║
echo ║     将本地服务暴露到互联网（使用 Cloudflare Tunnel）      ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM 检查 cloudflared 是否已安装
where cloudflared >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: cloudflared 未安装
    echo.
    echo 💡 请先安装 cloudflared:
    echo    npm install -g cloudflared
    echo.
    echo 或访问官网下载: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
    echo.
    pause
    exit /b 1
)

echo ✅ cloudflared 已安装
echo.
echo 📍 配置信息:
echo   • 前端服务: http://localhost:3000
echo   • 后端服务: http://localhost:8001
echo.

REM 检查两个服务是否已启动
echo 🔍 检查本地服务...
timeout /t 2 /nobreak >nul

netstat -ano | findstr ":3000" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  警告: 前端服务（端口 3000）未运行
) else (
    echo ✅ 前端服务已运行
)

netstat -ano | findstr ":8001" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  警告: 后端服务（端口 8001）未运行
) else (
    echo ✅ 后端服务已运行
)

echo.
echo ═══════════════════════════════════════════════════════════
echo 🚀 启动 Cloudflare Tunnel 穿透...
echo ═══════════════════════════════════════════════════════════
echo.

REM 启动两个 cloudflared 进程 - 分别穿透前端和后端
echo 📌 打开新窗口启动前端穿透 (3000)...
start "BEIMS Frontend Tunnel" cmd /k "cloudflared tunnel --url http://localhost:3000"

timeout /t 2 /nobreak >nul

echo 📌 打开新窗口启动后端穿透 (8001)...
start "BEIMS Backend Tunnel" cmd /k "cloudflared tunnel --url http://localhost:8001"

echo.
echo ═══════════════════════════════════════════════════════════
echo ✅ Cloudflare Tunnel 已启动！
echo ═══════════════════════════════════════════════════════════
echo.
echo 📝 已打开两个新窗口:
echo   1️⃣  前端穿透 (端口 3000) - 查看分配的 URL
echo   2️⃣  后端穿透 (端口 8001) - 查看分配的 URL
echo.
echo 💡 使用方法:
echo   1. 在前端穿透窗口中获取 Frontend URL
echo   2. 在后端穿透窗口中获取 Backend URL
echo   3. 更新 config.js 中的 backendURL 为分配的后端 URL
echo.
echo 📌 关闭此窗口不会中断穿透（穿透在新窗口中运行）
echo.
pause
