@echo off
chcp 65001 >nul
title 安装 Cloudflare Tunnel (cloudflared)

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║  📦 安装 Cloudflare Tunnel CLI (cloudflared)                ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM 检查 cloudflared 是否已安装
where cloudflared >nul 2>&1
if errorlevel 0 (
    echo ✅ cloudflared 已安装
    echo.
    cloudflared --version
    echo.
    echo 无需重新安装
    echo.
    pause
    exit /b 0
)

echo 🔍 检查依赖...
echo.

REM 检查 npm 是否已安装
where npm >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: npm 未安装
    echo.
    echo 💡 请先安装 Node.js（包含 npm）:
    echo    https://nodejs.org/
    echo.
    echo 然后再运行此脚本
    echo.
    pause
    exit /b 1
)

echo ✅ npm 已安装
npm --version
echo.

echo ═══════════════════════════════════════════════════════════
echo 🚀 开始安装 cloudflared...
echo ═══════════════════════════════════════════════════════════
echo.

npm install -g cloudflared

echo.
echo ═══════════════════════════════════════════════════════════

REM 验证安装
where cloudflared >nul 2>&1
if errorlevel 1 (
    echo ❌ 安装失败
    echo.
    echo 💡 请尝试以下方法:
    echo    1. 重新运行此脚本（可能需要管理员权限）
    echo    2. 手动下载: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
    echo    3. 检查 npm 配置: npm config get registry
    echo.
) else (
    echo ✅ cloudflared 安装成功！
    echo.
    echo 📍 已安装版本:
    cloudflared --version
    echo.
    echo 🎉 您现在可以使用 Cloudflare Tunnel 了！
    echo.
    echo 📝 下一步：
    echo   1. 双击 start-cloudflare-tunnel.bat 启动穿透
    echo   2. 获取分配的 URL
    echo   3. 更新 config.js 中的后端 URL
    echo.
)

pause
