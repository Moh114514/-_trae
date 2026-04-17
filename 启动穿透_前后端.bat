@echo off
chcp 65001 >nul
title BEIMS ngrok 穿透 - 前端+后端

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║  🌐 BEIMS ngrok 穿透 - 前端 + 后端                         ║
echo ║     将本地服务暴露到互联网                                ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 📍 配置信息:
echo   • 前端服务: http://localhost:3000
echo   • 后端服务: http://localhost:8001
echo.

echo 🚀 启动 ngrok 同时穿透前端和后端...
echo.
echo 请稍候，这会打开 ngrok 管理界面 http://127.0.0.1:4040
echo.

REM 启动 ngrok，将前端和后端都穿透
REM 最简单的方式：一条命令穿透前端（它包含对后端的代理）
ngrok http http://localhost:3000

pause
