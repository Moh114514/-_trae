@echo off
chcp 65001 >nul
title BEIMS Cloudflare Tunnel - 配置文件模式（持久化 URL）

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║  🌐 BEIMS Cloudflare Tunnel - 配置文件模式                  ║
echo ║     使用配置文件启动（永久相同的 URL）                    ║
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

echo ✅ cloudflared 已安装
echo.

REM 检查配置文件
if not exist "cloudflare-tunnel-config.yml" (
    echo ❌ 错误: cloudflare-tunnel-config.yml 不存在
    echo.
    echo 💡 请确保在 BEIMS 根目录中有配置文件
    echo.
    pause
    exit /b 1
)

echo ✅ 配置文件存在: cloudflare-tunnel-config.yml
echo.
echo 📍 启动信息:
echo   • 前端服务: http://localhost:3000
echo   • 后端服务: http://localhost:8001
echo   • 模式: 配置文件模式（永久 URL）
echo.

netstat -ano | findstr ":3000" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  警告: 前端服务未运行（端口 3000）
) else (
    echo ✅ 前端服务已运行
)

netstat -ano | findstr ":8001" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  警告: 后端服务未运行（端口 8001）
) else (
    echo ✅ 后端服务已运行
)

echo.
echo ═══════════════════════════════════════════════════════════
echo 🚀 使用配置文件启动 Cloudflare Tunnel...
echo ═══════════════════════════════════════════════════════════
echo.
echo 💡 提示: 
echo   • 首次运行会在 %USERPROFILE%\.cloudflared\ 生成凭证文件
echo   • 之后每次启动都会使用相同的 URL
echo   • 关闭此窗口会断开 Tunnel 连接
echo.

REM 启动 cloudflared
cloudflared tunnel run --config-file cloudflare-tunnel-config.yml

echo.
echo ⚠️  Tunnel 已断开连接
echo.

pause
