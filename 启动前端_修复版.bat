@echo off
chcp 65001 >nul
title BEIMS 前端服务 - 新配置启动

cd /d "e:\openclaw-project\workspace\Fuwu\BEIMS建筑能源智能管理系统\frontend"

echo.
echo 🚀 启动前端服务（新的 allowedHosts 配置）...
echo.
echo 允许的主机:
echo   ✓ ngrok-free.dev
echo   ✓ localhost
echo   ✓ 127.0.0.1
echo.

npm run dev

pause
