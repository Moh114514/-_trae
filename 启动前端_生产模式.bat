@echo off
chcp 65001 >nul
title BEIMS 前端 - 生产构建模式 (port 3000)

cd /d "e:\openclaw-project\workspace\Fuwu\BEIMS建筑能源智能管理系统\frontend"

echo.
echo 🚀 启动前端生产构建模式...
echo.
echo 📍 访问地址: http://localhost:3000
echo.
echo ⏳ 正在启动...
echo.

npx vite preview --port 3000

pause
