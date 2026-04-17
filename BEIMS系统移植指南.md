# BEIMS 建筑能源智能管理系统 - 移植指南

## 系统架构概述

BEIMS (Building Energy Intelligent Management System) 是一个完整的建筑能源管理平台，包含以下组件：

```
用户请求 → [前端 Vite 服务器 :3000] → [FastAPI 后端 :8082]
→ CloudEdgeRouter → [PostgreSQL 数据库]
                 → [Ollama 本地 LLM]
                 → [阿里云云端 LLM]
                 → [ChromaDB 知识库]
```

## 环境要求

### 硬件要求
- **CPU**: 至少 4 核
- **内存**: 至少 16GB (推荐 32GB 以上，用于 Ollama 模型)
- **磁盘**: 至少 50GB 可用空间
- **网络**: 稳定的互联网连接

### 软件要求
- **操作系统**: Windows 10/11 64位
- **Python**: 3.8+ (推荐 3.10)
- **Node.js**: 16+ (推荐 18.17.0+)
- **PostgreSQL**: 13+ (可选，用于生产环境)

## 依赖下载清单

### 1. Python 依赖

#### 核心依赖
```bash
pip install fastapi uvicorn requests pydantic python-dotenv
```

#### 可选依赖
```bash
pip install chromadb sentence-transformers psycopg2-binary
```

### 2. Node.js 依赖

```bash
# 在 energy-frontend 目录下
npm install
# 或
yarn install
```

### 3. 模型下载

#### Ollama 本地模型
- **模型名称**: `qwen2.5:7b`
- **下载命令**:
  ```bash
  ollama pull qwen2.5:7b
  ```
- **大小**: 约 4GB

#### 嵌入模型 (用于语义路由)
- **模型名称**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- **自动下载**: 首次运行时会自动下载
- **大小**: 约 400MB

### 4. 网络穿透工具

#### ngrok (推荐)
- **下载地址**: https://ngrok.com/download
- **配置**: 注册账号并获取 authtoken
- **使用**: `ngrok http 3000`

#### Cloudflare Tunnel (备选)
- **安装**: `npm install -g cloudflared`
- **使用**: `cloudflared tunnel --url http://localhost:3000`

## 必要文件清单

### 核心文件
1. **后端代码**
   - `cloud_edge_router.py` - 核心路由逻辑
   - `api_server.py` - FastAPI 后端服务

2. **前端文件**
   - `BEIMS建筑能源智能管理系统/` - 完整前端项目
   - `energy-frontend/` - Vite 配置和脚本

3. **知识库文件**
   - `knowledge_docs/` - 包含 Data_Dictionary.md 等文档

4. **配置文件**
   - `vite.config.js` - Vite 服务器配置
   - `share.js` - 内网穿透脚本
   - `start-tunnel.bat` - ngrok 启动脚本

## 移植步骤

### 步骤 1: 环境准备

1. **安装 Python**
   - 从 https://www.python.org/downloads/ 下载并安装 Python 3.10+
   - 确保添加到系统 PATH

2. **安装 Node.js**
   - 从 https://nodejs.org/en/download/ 下载并安装 Node.js 18+
   - 验证安装: `node -v` 和 `npm -v`

3. **安装 Ollama**
   - 从 https://ollama.com/download 下载并安装
   - 启动 Ollama 服务
   - 拉取模型: `ollama pull qwen2.5:7b`

4. **安装 ngrok** (可选)
   - 从 https://ngrok.com/download 下载并安装
   - 配置 authtoken: `ngrok config add-authtoken YOUR_TOKEN`

### 步骤 2: 项目部署

1. **复制项目文件**
   - 将整个 `Fuwu` 目录复制到新电脑
   - 确保文件结构保持完整

2. **安装 Python 依赖**
   ```bash
   cd Fuwu
   pip install fastapi uvicorn requests pydantic python-dotenv
   # 可选
   pip install chromadb sentence-transformers
   ```

3. **安装 Node.js 依赖**
   ```bash
   cd Fuwu/energy-frontend
   npm install
   ```

4. **配置 Vite 服务器**
   - 检查 `vite.config.js` 中的配置
   - 确保 `root` 路径正确指向 `../BEIMS建筑能源智能管理系统`

### 步骤 3: 启动服务

1. **启动后端 API 服务器**
   ```bash
   cd Fuwu
   python -B api_server.py
   ```
   - 验证: 访问 http://localhost:8082/docs

2. **启动前端 Vite 服务器**
   ```bash
   cd Fuwu/energy-frontend
   npm run dev
   ```
   - 验证: 访问 http://localhost:3000/

3. **启动内网穿透** (可选)
   ```bash
   # 使用 ngrok
   ngrok http 3000
   
   # 或使用 share.js
   node share.js
   ```

### 步骤 4: 验证系统

1. **测试 AI 聊天功能**
   - 打开前端页面
   - 点击右下角的 AI 聊天按钮
   - 发送 "查询所有建筑" 测试建筑列表查询

2. **测试数据查询**
   - 发送 "Caspian 2021年7月电耗" 测试数据查询

3. **测试网络穿透**
   - 使用 ngrok 提供的公网地址访问系统

## 常见问题排查

### 1. 后端启动失败
- **问题**: 端口 8082 被占用
  **解决**: 检查并关闭占用端口的进程

- **问题**: 缺少依赖
  **解决**: 重新安装所有 Python 依赖

- **问题**: Ollama 模型未下载
  **解决**: 运行 `ollama pull qwen2.5:7b`

### 2. 前端启动失败
- **问题**: 端口 3000 被占用
  **解决**: 检查并关闭占用端口的进程

- **问题**: 依赖安装失败
  **解决**: 删除 `node_modules` 目录后重新 `npm install`

### 3. AI 聊天功能不工作
- **问题**: 前端无法连接后端
  **解决**: 检查 API_BASE 配置是否正确

- **问题**: 模型加载失败
  **解决**: 确保 Ollama 服务正在运行

### 4. 网络穿透失败
- **问题**: ngrok 认证失败
  **解决**: 重新配置 authtoken

- **问题**: 防火墙阻止
  **解决**: 检查防火墙设置，允许相应端口

## 系统配置说明

### 后端配置
- **API 端口**: 8082 (可在 api_server.py 中修改)
- **Ollama URL**: http://localhost:11434 (默认)
- **数据库配置**: 可在 api_server.py 中修改

### 前端配置
- **开发端口**: 3000 (可在 vite.config.js 中修改)
- **API 代理**: 已配置为转发到 http://localhost:8082

### 知识库配置
- **文档路径**: knowledge_docs/
- **向量数据库**: 自动创建在本地

## 性能优化建议

1. **模型优化**
   - 对于内存有限的机器，可使用 `qwen2.5:3b` 模型
   - 启用 Ollama 的量化选项

2. **启动优化**
   - 首次启动会下载嵌入模型，可能需要较长时间
   - 建议在网络良好的环境下首次启动

3. **生产环境**
   - 使用 PM2 管理 Node.js 进程
   - 使用 systemd 或 NSSM 管理 Python 进程
   - 配置反向代理 (如 Nginx)

## 版本信息

- **系统版本**: BEIMS v2.3
- **CloudEdgeRouter**: v2.3-ENHANCED-CONTEXT
- **前端**: Vue.js + Vite
- **后端**: FastAPI + Uvicorn
- **AI 引擎**: Ollama (qwen2.5:7b) + 阿里云 qwen-plus

## 联系方式

如有任何问题，请联系系统管理员。

---

**文档版本**: v1.0
**更新日期**: 2026-04-14