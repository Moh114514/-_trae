# BEIMS 建筑能源智能管理系统 — 用户使用手册

> **版本：** v2.0  
> **更新日期：** 2026-04-18  
> **适用对象：** 系统管理员、运维工程师、终端用户

---

## 目录

1. [系统概述](#1-系统概述)
2. [系统架构](#2-系统架构)
3. [系统要求](#3-系统要求)
4. [安装与部署](#4-安装与部署)
5. [系统配置](#5-系统配置)
6. [智能问答助手使用指南](#6-智能问答助手使用指南)
7. [API 接口参考](#7-api-接口参考)
8. [知识库管理](#8-知识库管理)
9. [实时监测功能](#9-实时监测功能)
10. [能耗分析功能](#10-能耗分析功能)
11. [远程访问与内网穿透](#11-远程访问与内网穿透)
12. [常见问题与故障排除](#12-常见问题与故障排除)
13. [附录](#13-附录)

---

## 1. 系统概述

### 1.1 什么是 BEIMS

BEIMS（Building Energy Intelligent Management System，建筑能源智能管理系统）是一个基于 AI 的建筑能源管理平台，集成了智能问答、能耗分析、异常检测和实时监测等功能。系统采用"云边协同"架构，既能利用本地模型快速响应，又能在需要时调用云端大模型进行深度分析。

### 1.2 核心功能

| 功能模块 | 说明 |
|---------|------|
| **智能问答** | 通过自然语言对话查询建筑能耗数据、分析趋势、获取运维建议 |
| **云边协同路由** | 四层过滤逻辑（硬规则 → 语义路由 → 本地推理 → 云端增强），兼顾速度与智能 |
| **知识库检索** | 基于 ChromaDB 向量数据库的 RAG（检索增强生成），支持运维手册、操作指南等文档检索 |
| **能耗分析** | COP 制冷效率计算、同比环比分析、Z-Score 异常检测 |
| **实时监测** | 模拟历史数据流，实时告警推送，WebSocket 实时通信 |
| **上下文记忆** | 支持最多 20 轮对话历史，自动提取建筑、时间、指标等关键实体 |

### 1.3 支持的建筑

系统预置 14 栋建筑的数据：

| 建筑代码 | 中文名 | 类型 |
|---------|--------|------|
| Baikal | 贝加尔湖 | 办公/商业 |
| Aral | 咸海 | 工业 |
| Caspian | 里海 | 综合 |
| Huron | 休伦湖 | 教育 |
| Erie | 伊利湖 | 医疗 |
| Ladoga | 拉多加湖 | 住宅 |
| Superior | 苏必利尔湖 | 政府 |
| Titicaca | 的喀喀湖 | 酒店 |
| Victoria | 维多利亚湖 | 零售 |
| Winnipeg | 温尼伯湖 | 物流 |
| Vostok | 沃斯托克 | 研发 |
| Michigan | 密歇根湖 | 制造 |
| Ontario | 安大略湖 | 科技 |
| Malawi | 马拉维 | 文化 |

### 1.4 数据范围

- **时间跨度：** 2021 年全年数据（1 月 1 日 – 12 月 31 日）
- **采集粒度：** 每小时 1 条记录
- **总数据量：** 约 147 万条记录（14 栋 × 8760 小时）
- **数据字段：** 10 个核心指标（详见附录 A）

---

## 2. 系统架构

### 2.1 整体架构图

```
用户浏览器
    │
    ▼
┌─────────────────────────────────┐
│   前端（Vue.js + Vite :3000）     │
│   • 智能问答浮窗                  │
│   • Markdown 渲染               │
│   • 打字机效果 / 停止按钮         │
│   • 拖拽移动 / 窗口缩放           │
└──────────┬──────────────────────┘
           │ HTTP / WebSocket
           ▼
┌─────────────────────────────────┐
│   后端（FastAPI + Uvicorn :8082） │
│                                 │
│   ┌───────────────────────────┐ │
│   │  CloudEdgeRouter v2.3      │ │
│   │  ┌─ 第0层：知识库检测       │ │
│   │  ├─ 第1层：硬规则引擎       │ │
│   │  ├─ 第2层：语义路由         │ │
│   │  ├─ 第3层：本地推理(Ollama) │ │
│   │  └─ 第4层：云端增强(阿里云)  │ │
│   └───────────────────────────┘ │
│   • SmartBot 对话机器人           │
│   • EnergyAnalyzer 能耗分析      │
│   • RealTimeMonitor 实时监测     │
└──────┬──────────┬──────────┬─────┘
       │          │          │
       ▼          ▼          ▼
┌──────────┐ ┌────────┐ ┌──────────┐
│PostgreSQL│ │ Ollama │ │ 阿里云    │
│  数据库   │ │qwen2.5 │ │ qwen-plus│
│ :5432    │ │  :7b   │ │          │
└──────────┘ └────────┘ └──────────┘
       ▲
       │
┌──────────┐
│ ChromaDB │ 向量数据库
│  知识库   │ (fuwu_knowledge)
└──────────┘
```

### 2.2 云边协同路由四层逻辑

系统采用创新的四层过滤架构，确保每个查询都在最合适的层级处理：

| 层级 | 名称 | 处理方式 | 响应时间 | 置信度 |
|------|------|---------|---------|--------|
| **第 0 层** | 知识库检测 | 检测是否为运维/操作/故障类问题 → 知识库检索 | 毫秒级 | — |
| **第 1 层** | 硬规则引擎 | 正则匹配建筑名+日期+指标，直接生成 SQL | 毫秒级 | 0.95+ |
| **第 2 层** | 语义路由 | Embedding 向量匹配意图模板 | 秒级 | 0.75+ |
| **第 3 层** | 本地推理 | Ollama qwen2.5:7b 分析意图、生成 SQL | 10-15s | 0.8 |
| **第 4 层** | 云端增强 | 阿里云 qwen-plus 深度分析 | 5-10s | — |

**降级机制：** 当某层不可用时（如云端断网），系统自动降级到下一层，确保服务不中断。

---

## 3. 系统要求

### 3.1 硬件要求

| 组件 | 最低要求 | 推荐配置 |
|------|---------|---------|
| **CPU** | 4 核 | 8 核以上 |
| **内存** | 16 GB | 32 GB 以上（运行 Ollama 模型） |
| **硬盘** | 50 GB 可用空间 | 100 GB SSD |
| **网络** | 稳定的互联网连接（云端模型） | 千兆局域网 |

### 3.2 软件要求

| 软件 | 版本 | 用途 |
|------|------|------|
| **操作系统** | Windows 10/11 64 位 | 主机系统 |
| **Python** | 3.10+ | 后端运行环境 |
| **Node.js** | 18.17.0+ | 前端构建工具 |
| **PostgreSQL** | 13+ | 关系型数据库 |
| **Ollama** | 最新版 | 本地 LLM 运行 |

### 3.3 模型需求

| 模型 | 用途 | 大小 | 获取方式 |
|------|------|------|---------|
| **qwen2.5:7b** | 本地意图分析、SQL 生成 | ~4 GB | `ollama pull qwen2.5:7b` |
| **sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2** | 语义路由 Embedding | ~400 MB | 首次运行时自动下载 |
| **qwen-plus** | 云端深度分析 | — | 阿里云 DashScope API Key |

---

## 4. 安装与部署

### 4.1 环境准备

#### 步骤 1：安装 Python

1. 访问 [python.org/downloads](https://www.python.org/downloads/) 下载 Python 3.10+
2. 安装时勾选 **"Add Python to PATH"**
3. 验证安装：
   ```bash
   python --version
   pip --version
   ```

#### 步骤 2：安装 Node.js

1. 访问 [nodejs.org](https://nodejs.org/) 下载 LTS 版本（18.17.0+）
2. 安装后验证：
   ```bash
   node -v
   npm -v
   ```

#### 步骤 3：安装 PostgreSQL

1. 访问 [postgresql.org/download](https://www.postgresql.org/download/) 下载 PostgreSQL 13+
2. 安装过程中设置管理员密码
3. 创建数据库：
   ```sql
   CREATE DATABASE building_energy;
   ```
4. 导入数据表（使用项目提供的 SQL 脚本或数据导入工具）

#### 步骤 4：安装 Ollama

1. 访问 [ollama.com/download](https://ollama.com/download) 下载并安装
2. 启动 Ollama 服务：
   ```bash
   ollama serve
   ```
3. 下载本地模型：
   ```bash
   ollama pull qwen2.5:7b
   ```

### 4.2 项目部署

#### 步骤 1：准备项目文件

将 `Fuwu` 项目文件夹复制到目标位置，确保目录结构完整：

```
Fuwu/
├── api_server.py              # FastAPI 后端主程序
├── cloud_edge_router.py       # 云边协同路由分发器
├── energy_analyzer.py         # 能耗分析引擎
├── realtime_monitor.py        # 实时监测服务
├── knowledge_docs/            # 知识库文档目录
│   ├── Data_Dictionary.md     # 数据字典
│   ├── knowledge_base.py      # 知识库管理脚本
│   └── ...
├── chroma_db/                 # ChromaDB 向量数据库
├── .venv/                     # Python 虚拟环境
├── BEIMS建筑能源智能管理系统/   # 前端项目
│   └── frontend/
│       ├── dist/              # 构建输出
│       └── vite.config.js     # Vite 配置
└── *.bat                      # 启动脚本
```

#### 步骤 2：安装 Python 依赖

```bash
cd E:\openclaw-project\workspace\Fuwu

# 激活虚拟环境（如果已创建）
.venv\Scripts\activate

# 如果没有虚拟环境，先创建
python -m venv .venv
.venv\Scripts\activate

# 安装核心依赖
pip install fastapi uvicorn[standard] requests pydantic psycopg2-binary pandas numpy

# 安装可选依赖（知识库功能）
pip install chromadb sentence-transformers

# 如需 PDF/Word 文档支持
pip install pdfplumber python-docx
```

#### 步骤 3：初始化知识库

```bash
cd knowledge_docs
python knowledge_base.py
```

此脚本会：
- 加载 `knowledge_docs/` 目录下所有支持的文档（.md, .txt, .pdf, .docx）
- 使用 Embedding 模型将文档分割为向量块
- 存储到 `chroma_db/` 目录下的 ChromaDB 中

**知识库热更新：** 后续添加或修改文档后，重新运行 `knowledge_base.py` 即可。系统使用 MD5 哈希检测文件变化，只更新变化的文件。

#### 步骤 4：配置数据库连接

编辑 `api_server.py`，找到以下配置段并修改：

```python
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "building_energy",
    "user": "postgres",
    "password": "你的数据库密码"
}
```

如需更换云端模型配置，修改：

```python
CLOUD_API_KEY = "你的阿里云DashScope API Key"
CLOUD_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
CLOUD_MODEL = "qwen-plus"
```

#### 步骤 5：启动后端服务

```bash
cd E:\openclaw-project\workspace\Fuwu
.venv\Scripts\activate
python -B api_server.py
```

启动后访问 http://localhost:8082/docs 查看 API 文档（Swagger UI），确认服务正常运行。

#### 步骤 6：启动前端服务

**方式一：使用 Vite 开发服务器**

```bash
cd E:\openclaw-project\workspace\Fuwu\BEIMS建筑能源智能管理系统\frontend
npm install
npm run dev
```

访问 http://localhost:3000/

**方式二：直接打开构建版本**

双击 `open_frontend.bat` 或在浏览器中打开：
```
E:\openclaw-project\workspace\Fuwu\BEIMS建筑能源智能管理系统\frontend\dist\index.html
```

### 4.3 验证部署

1. **后端验证：** 浏览器访问 http://localhost:8082/，应返回：
   ```json
   {
     "name": "建筑能源管理系统 API v2",
     "version": "2.0.0",
     "features": ["智能对话", "上下文记忆", "SQL 自动生成", "知识库检索"]
   }
   ```

2. **前端验证：** 访问 http://localhost:3000/，页面右下角出现蓝色 "AI" 按钮。

3. **对话测试：** 点击 AI 按钮，输入测试问题：
   - `可查询的建筑有哪些？` → 应返回 14 栋建筑列表
   - `Caspian 2021年7月21日的电耗是多少？` → 应返回查询结果

---

## 5. 系统配置

### 5.1 核心配置项

以下配置项位于 `api_server.py` 文件顶部：

```python
# 数据库配置
DB_CONFIG = {
    "host": "localhost",          # 数据库主机
    "port": 5432,                  # 数据库端口
    "database": "building_energy", # 数据库名
    "user": "postgres",            # 用户名
    "password": "416417"           # 密码
}

# 本地模型配置
OLLAMA_URL = "http://localhost:11434/api/generate"  # Ollama 服务地址
LOCAL_MODEL = "qwen2.5:7b"                           # 本地模型名称

# 云端模型配置
CLOUD_API_KEY = "sk-xxx"         # 阿里云 DashScope API Key
CLOUD_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
CLOUD_MODEL = "qwen-plus"         # 云端模型名称

# 知识库配置
CHROMA_PATH = r"E:\openclaw-project\workspace\Fuwu\chroma_db"  # ChromaDB 存储路径
```

### 5.2 前端配置

前端浮窗的 API 地址配置在 `frontend/dist/index.html` 中自动判断：

- **本地访问**（localhost）：自动连接 `http://localhost:8001`
- **隧道访问**（ngrok/Cloudflare）：自动使用同域地址
- **生产部署**：默认同域

如需修改，编辑 `index.html` 中的 `window.__BEIMS_API_BASE__` 变量。

### 5.3 Vite 代理配置

`vite.config.js` 中配置了 API 代理：

```javascript
proxy: {
  '/api': {
    target: 'http://localhost:8001',  // 后端地址
    changeOrigin: true
  }
}
```

---

## 6. 智能问答助手使用指南

### 6.1 界面介绍

#### 6.1.1 浮窗入口

访问前端页面后，右下角有一个蓝色 **AI** 按钮，点击后展开智能问答窗口。

#### 6.1.2 浮窗功能

| 功能 | 说明 |
|------|------|
| 💬 **智能对话** | 输入自然语言问题，系统自动理解并回答 |
| ⌨️ **快捷问题** | 预设常见问题按钮，点击即可快速提问 |
| ⏳ **打字机效果** | 回答内容逐字显示，自适应速度 |
| 🛑 **停止按钮** | 长回答进行中可随时点击停止 |
| 🗑️ **清空对话** | 一键清空聊天记录 |
| 🖱️ **拖拽移动** | 自由拖动浮窗位置 |
| 📏 **窗口缩放** | 拖拽边缘调整窗口大小 |
| 📝 **Markdown** | 回答支持加粗、列表等 Markdown 格式 |

### 6.2 提问方式

系统支持多种自然语言提问方式，从简单到复杂均可理解：

#### 6.2.1 简单查询

```
建筑有哪些？
可查询的建筑列表
```

→ 返回所有可查询建筑的完整列表。

```
Caspian 2021年7月21日的电耗是多少？
Michigan 5月7日上午6点的电耗
Aral 2021-08-15的用水量
```

→ 精确查询指定建筑、日期、时间的能耗数据。

#### 6.2.2 指标查询

系统支持查询以下指标：

| 中文说法 | 数据库字段 | 单位 |
|---------|-----------|------|
| 电耗 / 用电量 / 电量 / 电力 | electricity_kwh | kWh |
| 水耗 / 用水量 / 水量 | water_m3 | m³ |
| 空调能耗 / 空调用电 | hvac_kwh | kWh |
| 供水温度 / 冷冻水供水 | chw_supply_temp | °C |
| 回水温度 / 冷冻水回水 | chw_return_temp | °C |
| 室外温度 / 气温 | outdoor_temp | °C |
| 湿度 / 相对湿度 | humidity_pct | % |
| 人员密度 / 人数 | occupancy_density | 人/100m² |

#### 6.2.3 时间表达

系统支持多种时间表达方式：

| 格式 | 示例 |
|------|------|
| 完整日期 | `Caspian 2021年7月21日` |
| 简化日期 | `Caspian 7月21日`（默认 2021 年） |
| 带时间 | `Caspian 7月21日上午6点` |
| 时间范围 | `Caspian 7月21日6点到12点` |
| 日期范围 | `Caspian 7月21日到25日` |
| 月份查询 | `Caspian 2021年7月的能耗趋势` |

#### 6.2.4 分析类问题

```
Caspian 7月的电耗正常吗？
这个数值算高吗？
Michigan 和 Ontario 的用水量对比
为什么电耗这么高？
有什么节能建议？
```

→ 系统会先查询相关数据，然后调用云端模型进行深度分析。

#### 6.2.5 追问

```
用户：Caspian 7月21日的电耗是多少？
系统：[返回查询结果]
用户：这个数值算高吗？        ← 系统自动关联上次结果
用户：那 Ontario 呢？           ← 系统自动关联建筑
```

系统支持上下文记忆，会自动关联上一轮的查询结果和建筑信息。

#### 6.2.6 知识库查询

```
COP 是什么意思？
空调外机出了问题怎么办？
如何进行能耗异常检测？
冷冻水供水温度的正常范围是多少？
```

→ 系统从知识库文档中检索相关内容，结合 AI 生成回答。

### 6.3 回答示例

**简单查询：**

```
用户：Caspian 7月21日的电耗是多少？

系统：电耗(kWh) 查询结果（共 24 条记录）：

### 分时段数据
• 00:00：256.30 kWh
• 06:00：198.50 kWh
• 12:00：412.80 kWh
• 18:00：385.20 kWh

### 统计摘要
• 总量：6842.50 kWh
• 平均值：285.10 kWh
• 最小值：152.30 kWh
• 最大值：445.60 kWh
```

**分析类问题：**

```
用户：Caspian 7月的电耗正常吗？

系统：根据 2021年7月 Caspian 的能耗数据分析：

**总体评估：** 电耗处于正常范围

📊 关键发现：
• 月总电耗：xxx kWh
• 日均电耗：xxx kWh
• 峰值出现在 7月15日下午，达到 xxx kWh
• 与同类型建筑相比，能耗水平中等

💡 建议：...
```

### 6.4 上下文记忆

系统自动维护以下上下文信息：

- **最近提及的建筑** — 追问时无需重复指定建筑名
- **最近查询的日期** — 后续问题自动关联
- **最近查询结果** — 支持"这个数值正常吗"等追问
- **对话历史** — 最多保存 20 轮对话
- **提取的实体** — 自动识别并记录建筑名、日期、指标关键词

**清空对话：**
在对话窗口中点击"清空"按钮，或发送消息 `清空历史` / `重新开始` / `新对话`。

---

## 7. API 接口参考

### 7.1 基础信息

- **Base URL：** `http://localhost:8082`
- **API 文档：** `http://localhost:8082/docs`（Swagger UI）
- **Content-Type：** `application/json`

### 7.2 接口列表

#### 7.2.1 系统根路径

```
GET /
```

**响应：**
```json
{
  "name": "建筑能源管理系统 API v2",
  "version": "2.0.0",
  "features": ["智能对话", "上下文记忆", "SQL 自动生成", "知识库检索"]
}
```

#### 7.2.2 建筑列表

```
GET /buildings
```

**响应：**
```json
{
  "buildings": ["Baikal", "Aral", "Caspian", ...],
  "count": 14
}
```

#### 7.2.3 智能对话 ⭐

```
POST /chat
```

**请求体：**
```json
{
  "message": "Caspian 7月21日的电耗是多少？",
  "building_id": null,
  "clear_history": false,
  "history": [],
  "session_id": "default"
}
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `message` | string | ✅ | 用户问题文本 |
| `building_id` | string | ❌ | 指定建筑（可选） |
| `clear_history` | bool | ❌ | 是否清空历史 |
| `history` | array | ❌ | 完整对话历史 `[{"role":"user","content":"..."}]` |
| `session_id` | string | ❌ | 会话标识，用于多会话支持 |

**响应：**
```json
{
  "response": "电耗(kWh) 查询结果...",
  "context": {
    "last_building": "Caspian",
    "last_date": "2021-07-21",
    "last_result": "...",
    "layer": "static_rule",
    "system_mode": "normal",
    "history_count": 2,
    "session_id": "default",
    "extracted_entities": {
      "buildings": ["Caspian"],
      "dates": ["2021-07-21"],
      "metrics": ["electricity_kwh"]
    }
  },
  "history": [
    {"role": "user", "content": "Caspian 7月21日的电耗是多少？"},
    {"role": "assistant", "content": "电耗(kWh) 查询结果..."}
  ]
}
```

#### 7.2.4 清空对话

```
POST /chat/clear
```

**响应：**
```json
{
  "status": "ok",
  "message": "对话历史已清空"
}
```

#### 7.2.5 路由器状态

```
GET /router/status
```

**响应：**
```json
{
  "mode": "normal",
  "cloud_available": true,
  "fallback_mode": false,
  "total_requests": 150,
  "layer_stats": {
    "static_rule": 100,
    "semantic": 10,
    "local_slm": 30,
    "cloud_llm": 10
  }
}
```

#### 7.2.6 建筑摘要报告

```
GET /buildings/{building_id}/summary
```

**响应：** 包含总体统计、COP 分析、同比环比、异常检测等综合报告。

#### 7.2.7 COP 效率分析

```
GET /buildings/{building_id}/cop
```

**响应：**
```json
{
  "building_id": "Caspian",
  "avg_cop": 4.52,
  "rating_distribution": {
    "优秀": 120,
    "良好": 450,
    "一般": 200,
    "异常": 15
  }
}
```

#### 7.2.8 异常检测

```
GET /buildings/{building_id}/anomalies?threshold=3.0
```

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `threshold` | float | 3.0 | Z-Score 阈值 |

#### 7.2.9 实时监测

```
GET  /monitor/status           # 获取监测状态
GET  /monitor/alerts           # 获取告警列表
POST /monitor/start            # 启动监测
POST /monitor/stop             # 停止监测
POST /monitor/pause            # 暂停监测
POST /monitor/resume           # 继续监测
POST /monitor/reset            # 重置监测
POST /monitor/speed?speed=60   # 调整模拟速度
POST /monitor/clear-alerts     # 清除告警
POST /monitor/simulation       # 设置模拟参数
POST /monitor/trigger-anomaly  # 手动触发异常
WS   /ws/monitor              # WebSocket 实时推送
```

**启动监测示例：**
```bash
curl -X POST "http://localhost:8082/monitor/start?speed=60&start_date=2021-07-01"
```

**手动触发异常示例：**
```bash
curl -X POST "http://localhost:8082/monitor/trigger-anomaly" \
  -H "Content-Type: application/json" \
  -d '{"building": "Caspian", "type": "electricity_high", "intensity": 8}'
```

---

## 8. 知识库管理

### 8.1 知识库概述

知识库模块使用 ChromaDB 向量数据库 + sentence-transformers 嵌入模型实现 RAG（检索增强生成）。当用户提出运维、操作、故障处理类问题时，系统会自动检索相关文档片段，增强 AI 回答的准确性。

### 8.2 支持的文档格式

| 格式 | 扩展名 | 依赖 |
|------|--------|------|
| Markdown | .md | 无需额外依赖 |
| 纯文本 | .txt | 无需额外依赖 |
| PDF | .pdf | `pip install pdfplumber` |
| Word | .docx / .doc | `pip install python-docx` |

### 8.3 添加文档

**步骤：**

1. 将文档放入 `knowledge_docs/` 目录（支持子文件夹）
2. 运行知识库加载脚本：
   ```bash
   cd E:\openclaw-project\workspace\Fuwu\knowledge_docs
   python knowledge_base.py
   ```

**热更新机制：**
- 脚本使用 MD5 哈希检测文件变化
- 未变化的文件自动跳过
- 已变化的文件自动删除旧块、添加新块
- 已删除的文件自动从知识库中移除

### 8.4 查看知识库统计

运行知识库脚本后，会显示统计信息：

```
知识库统计：
  总文档块数：125
  分类列表：['根目录', '设备手册', '运维指南', '能耗标准']
```

### 8.5 现有知识库文档

| 文件名 | 内容 |
|--------|------|
| `Data_Dictionary.md` | 完整数据字典，字段定义与标准 |
| `能耗标准` | 能耗评估标准与规范 |
| `设备手册` | 设备操作与维护手册 |
| `运维指南` | 系统运维操作指南 |
| `常见问题` | FAQ 文档 |

---

## 9. 实时监测功能

### 9.1 功能概述

实时监测模块通过模拟历史数据流，展示建筑能耗的实时变化，并在检测到异常时发出告警。

### 9.2 监测阈值

| 指标 | 最低值 | 最高值 | 异常检测 |
|------|--------|--------|---------|
| 电耗 (kWh) | 50 | 500 | Z-Score 3.0 |
| 水耗 (m³) | 0.1 | 50 | Z-Score 3.0 |
| 空调能耗 (kWh) | 10 | 300 | Z-Score 3.0 |
| 冷冻水供水温度 (°C) | 5 | 12 | Z-Score 3.0 |
| 冷冻水回水温度 (°C) | 10 | 18 | Z-Score 3.0 |
| 室外温度 (°C) | -40 | 50 | Z-Score 3.0 |

### 9.3 告警级别

| 级别 | 颜色 | 触发条件 |
|------|------|---------|
| INFO | 🔵 | 信息提示 |
| WARNING | 🟡 | 超出正常范围 |
| CRITICAL | 🔴 | 严重偏离正常范围（偏差 > 50%） |

### 9.4 使用方式

**通过 API 控制：**

```bash
# 启动监测（速度 60x，从 2021-07-01 开始）
curl -X POST "http://localhost:8082/monitor/start?speed=60&start_date=2021-07-01"

# 查看监测状态
curl http://localhost:8082/monitor/status

# 暂停监测
curl -X POST http://localhost:8082/monitor/pause

# 继续监测
curl -X POST http://localhost:8082/monitor/resume

# 调整速度（1x ~ 3600x）
curl -X POST "http://localhost:8082/monitor/speed?speed=120"

# 手动触发电耗异常
curl -X POST http://localhost:8082/monitor/trigger-anomaly \
  -H "Content-Type: application/json" \
  -d '{"building": "Caspian", "type": "electricity_high", "intensity": 8}'

# 停止监测
curl -X POST http://localhost:8082/monitor/stop

# 清除所有告警
curl -X POST http://localhost:8082/monitor/clear-alerts
```

**通过 WebSocket 实时推送：**

连接 `ws://localhost:8082/ws/monitor` 接收实时状态更新和告警推送。

---

## 10. 能耗分析功能

### 10.1 COP 制冷效率分析

COP（Coefficient of Performance）= 制冷量 / 压缩机功耗

| COP 范围 | 评级 |
|---------|------|
| ≥ 5.0 | 优秀 |
| 4.0 – 4.9 | 良好 |
| 3.0 – 3.9 | 一般 |
| < 3.0 | 异常 |

### 10.2 同比分析（Year-over-Year）

对比不同年份同一时期的能耗数据，计算同比增长率。

**API：** `GET /buildings/{building_id}/summary` 中包含同比分析结果。

### 10.3 环比分析（Month-over-Month）

对比相邻月份的能耗数据，计算环比增长率。

### 10.4 异常检测

使用 Z-Score 方法检测能耗异常：

```
Z = |值 - 均值| / 标准差
```

当 Z-Score > 阈值（默认 3.0）时标记为异常。

---

## 11. 远程访问与内网穿透

### 11.1 ngrok

**安装：**
1. 访问 [ngrok.com/download](https://ngrok.com/download) 下载
2. 注册账号获取 authtoken
3. 配置：`ngrok config add-authtoken YOUR_TOKEN`

**使用：**
```bash
ngrok http 3000    # 穿透前端
ngrok http 8082    # 穿透后端
```

### 11.2 Cloudflare Tunnel

**安装：**
```bash
npm install -g cloudflared
```

**使用批处理脚本：**

| 脚本 | 功能 |
|------|------|
| `start-cloudflare-backend.bat` | 启动后端 Cloudflare Tunnel |
| `start-cloudflare-frontend.bat` | 启动前端 Cloudflare Tunnel |
| `start-cloudflare-tunnel.bat` | 同时启动前后端 Tunnel |
| `start-cloudflare-config.bat` | 配置 Tunnel |

---

## 12. 常见问题与故障排除

### 12.1 后端启动失败

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 端口 8082 被占用 | 其他程序使用了相同端口 | 关闭占用端口的程序，或修改 `api_server.py` 中的端口 |
| 缺少 Python 依赖 | 未安装所需包 | 运行 `pip install fastapi uvicorn psycopg2-binary ...` |
| Ollama 模型未加载 | 模型未下载 | 运行 `ollama pull qwen2.5:7b` |
| 数据库连接失败 | 配置错误或 PG 未启动 | 检查 `DB_CONFIG` 配置，确认 PostgreSQL 服务运行中 |

### 12.2 前端无法访问

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 端口 3000 被占用 | 其他程序占用 | 关闭占用程序或修改 `vite.config.js` 中的端口 |
| 依赖未安装 | 未运行 npm install | 进入前端目录运行 `npm install` |
| 浮窗不显示 | 脚本加载失败 | 检查浏览器控制台（F12），确认 `ai-chat-widget.js` 路径正确 |

### 12.3 AI 对话无响应

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 本地模型不可用 | Ollama 未启动 | 运行 `ollama serve` |
| 云端模型调用失败 | API Key 无效或网络问题 | 检查 `CLOUD_API_KEY` 配置和网络连接 |
| 查询无结果 | 建筑名/日期不匹配 | 确认建筑名在支持列表中，日期在 2021 年范围内 |

### 12.4 知识库搜索无结果

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 知识库为空 | 文档未加载 | 运行 `python knowledge_base.py` |
| Embedding 模型下载失败 | 网络问题 | 设置 HF 镜像：`os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'` |

---

## 13. 附录

### 附录 A：数据库字段完整列表

| 字段名 | 中文名 | 数据类型 | 单位 | 说明 |
|--------|--------|---------|------|------|
| `timestamp` | 时间戳 | TIMESTAMP | — | 格式：YYYY-MM-DD HH:MM:SS |
| `building_id` | 建筑编号 | VARCHAR | — | 14 栋建筑的英文代码 |
| `building_type` | 建筑类型 | VARCHAR | — | 建筑功能分类 |
| `electricity_kwh` | 电耗 | FLOAT | kWh | 每小时电力消耗 |
| `water_m3` | 水耗 | FLOAT | m³ | 每小时用水量 |
| `hvac_kwh` | 空调能耗 | FLOAT | kWh | HVAC 系统耗电量 |
| `chw_supply_temp` | 冷冻水供水温度 | FLOAT | °C |  chilled water supply |
| `chw_return_temp` | 冷冻水回水温度 | FLOAT | °C | chilled water return |
| `outdoor_temp` | 室外温度 | FLOAT | °C | 环境温度 |
| `humidity_pct` | 湿度 | FLOAT | % | 相对湿度 |
| `occupancy_density` | 人员密度 | FLOAT | 人/100m² | 每百平方米人数 |
| `meter_id` | 仪表编号 | VARCHAR | — | 测量仪表标识 |
| `system_status` | 系统状态 | VARCHAR | — | 设备运行状态 |

### 附录 B：快捷问题按钮

浮窗预设的快捷问题（可在 `ai-chat-widget.js` 中自定义）：

- `可查询的建筑有哪些？`
- `Caspian 今日电耗`
- `系统状态如何？`
- `能耗异常检测`

### 附录 C：启动命令速查

| 服务 | 命令 | 端口 |
|------|------|------|
| Ollama 服务 | `ollama serve` | 11434 |
| 后端 API | `python -B api_server.py` | 8082 |
| 前端 Vite | `npm run dev`（在 frontend 目录） | 3000 |
| API 文档 | 浏览器访问 `/docs` | 8082 |
| ngrok 前端 | `ngrok http 3000` | — |
| ngrok 后端 | `ngrok http 8082` | — |

### 附录 D：技术栈清单

| 层级 | 技术 | 版本 |
|------|------|------|
| 前端框架 | Vue.js 3 + Vite | — |
| 前端浮窗 | 原生 JavaScript（打字机效果、Markdown 渲染） | — |
| 后端框架 | FastAPI + Uvicorn | Python |
| 数据库 | PostgreSQL | 13+ |
| 向量数据库 | ChromaDB | — |
| 本地 AI | Ollama + qwen2.5:7b | — |
| 云端 AI | 阿里云 DashScope + qwen-plus | — |
| Embedding | sentence-transformers | paraphrase-multilingual-MiniLM-L12-v2 |
| 内网穿透 | ngrok / Cloudflare Tunnel | — |
| 数据分析 | pandas + numpy | — |

---

**文档结束**

*BEIMS 建筑能源智能管理系统 — 用 AI 赋能建筑能源管理*
