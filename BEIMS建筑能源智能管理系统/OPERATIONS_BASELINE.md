# BEIMS 主链路运行基线（阶段 1-3）

更新时间：2026-04-15

## 1. 主链路范围

本仓库以 BEIMS 管理系统为主承载体：
- 主目录：BEIMS建筑能源智能管理系统
- 主启动入口：BEIMS建筑能源智能管理系统/start.bat

以下脚本已冻结，不再作为日常入口：
- ../start.bat（仅做跳转提示）
- ../start-tunnel-v3.bat（冻结）
- ../start-cloudflare-tunnel.bat（冻结）

## 2. 端口统一约定

- 前端开发服务：3000
- 主后端 API：8001
- 智能助手独立服务：8082（当前阶段不对外暴露，不作为主入口）

## 3. 主链路请求路径

- 浏览器 -> 前端（3000）
- 前端 -> /api/*（Vite 代理）
- Vite 代理 -> http://localhost:8001

对应配置文件：
- frontend/vite.config.js
- backend/app/main.py
- backend/app/config/settings.py
- backend/.env

## 4. 环境变量基线

后端环境变量以 backend/.env 为准。
若 backend/.env 不存在，start.bat 会自动由 backend/.env.example 生成。

关键项：
- API_HOST=0.0.0.0
- API_PORT=8001
- DATABASE_URL=sqlite:///./beims.db（开发默认）

## 5. 标准启动顺序

1) 进入主目录并启动：
   - 运行 BEIMS建筑能源智能管理系统/start.bat
2) 访问地址：
   - Frontend: http://localhost:3000
   - Backend Docs: http://localhost:8001/docs

## 6. 阶段边界说明

本基线当前覆盖阶段 1-3：
- 阶段 1：入口收口与冻结
- 阶段 2：主链路端口和代理统一
- 阶段 3：主后端聊天入口接入智能助手代理（8082）并保留本地回退

后续阶段会再处理：
- 单入口内网穿透

## 7. 阶段3聊天链路

- 对外统一聊天入口：`/chat`
- 主后端优先代理到独立智能助手（`ASSISTANT_BASE_URL`）
- 代理失败时按配置决定是否回退本地 CloudEdgeRouter

关键配置项（backend/.env）：
- ASSISTANT_PROXY_ENABLED
- ASSISTANT_BASE_URL
- ASSISTANT_PROXY_TIMEOUT
- ASSISTANT_FALLBACK_LOCAL
