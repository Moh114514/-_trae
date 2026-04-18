# BEIMS 建筑能源智能管理系统用户使用手册

## 1. 系统概述

BEIMS (Building Energy Intelligent Management System) 是一款集查询统计与智慧运维于一体的建筑能源智能管理系统。

### 1.1 核心功能

- **数据层**：能耗数据集构建、清洗与标准化，支持CSV、Excel格式导入，数据验证和质量检查
- **查询统计模块**：基于MCP协议的数据接入与查询接口，支持按建筑、时间、监测参数等条件精准查询，13类核心统计分析功能，12种可视化图表展示，统计报表自动生成与导出（PDF格式）
- **智慧运维模块**：领域知识库构建，基于RAG技术的智能问答，能耗异常原因分析，设备运行状态查询，节能建议生成
- **系统集成**：RESTful API接口，MCP协议支持，Vue.js前端界面，响应式设计

### 1.2 技术栈

- **后端**：FastAPI、SQLAlchemy、PostgreSQL/SQLite、Pandas、NumPy、Plotly、Matplotlib、LangChain、ChromaDB、Sentence Transformers、ReportLab
- **前端**：Vue.js 3、Element Plus、ECharts、Axios、Pinia

## 2. 系统架构

### 2.1 整体架构

```
┌─────────────────────┐
│     前端界面        │
│  http://localhost:3000 │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│     Vite 代理       │
│  转发 /api 到后端    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│     后端服务        │
│  http://localhost:8001 │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│     数据库          │
│  SQLite/PostgreSQL  │
└─────────────────────┘
```

### 2.2 目录结构

```
BEIMS建筑能源智能管理系统/
├── backend/                    # 后端代码
│   ├── app/
│   │   ├── config/            # 配置文件
│   │   ├── models/            # 数据模型
│   │   ├── routers/           # API路由
│   │   ├── services/          # 业务逻辑
│   │   ├── utils/             # 工具类
│   │   └── main.py            # 主应用
│   ├── uploads/               # 上传文件存储
│   ├── requirements.txt       # Python依赖
│   └── .env.example           # 环境变量示例
├── frontend/                   # 前端代码
│   ├── dist/                  # 构建输出
│   └── vite.config.js         # Vite配置
├── Dataset/                    # 数据集
├── start.bat                   # 一键启动脚本
├── README.md                   # 项目说明
└── OPERATIONS_BASELINE.md      # 运行基线
```

## 3. 环境要求

- Python 3.8+
- Node.js 16+
- PostgreSQL 12+（可选，默认使用SQLite）

## 4. 安装部署

### 4.1 一键启动（推荐）

1. 进入 `BEIMS建筑能源智能管理系统` 目录
2. 双击运行 `start.bat` 脚本
3. 系统会自动：
   - 检查环境（Python、Node.js）
   - 安装依赖（首次运行）
   - 启动后端服务（端口 8001）
   - 启动前端服务（端口 3000）
4. 访问：http://localhost:3000

### 4.2 手动安装

#### 4.2.1 后端安装

1. 进入 `backend` 目录
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 配置环境变量：
   - 复制 `.env.example` 为 `.env`
   - 根据需要修改配置
4. 启动后端：
   ```bash
   python -m app.main
   ```

#### 4.2.2 前端安装

1. 进入 `frontend` 目录
2. 安装依赖：
   ```bash
   npm install
   ```
3. 启动前端：
   ```bash
   npm run dev
   ```

### 4.3 数据库配置

#### 4.3.1 SQLite（默认，推荐用于开发测试）
- 无需安装数据库软件
- 数据存储在本地文件 `beims.db`
- 开箱即用，适合快速体验

#### 4.3.2 PostgreSQL（推荐用于生产环境）
1. 安装 PostgreSQL（参考 README.md 中的详细指南）
2. 创建数据库：
   ```sql
   CREATE DATABASE building_energy;
   ```
3. 修改 `.env` 文件中的数据库连接字符串：
   ```env
   DATABASE_URL=postgresql://postgres:你的密码@localhost:5432/building_energy
   ```

## 5. 系统配置

### 5.1 环境变量配置

主要配置文件：`backend/.env`

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| API_HOST | 后端服务主机 | 0.0.0.0 |
| API_PORT | 后端服务端口 | 8001 |
| DATABASE_URL | 数据库连接字符串 | sqlite:///./beims.db |
| SECRET_KEY | JWT密钥 | your-secret-key-change-in-production |
| UPLOAD_DIR | 上传文件目录 | uploads |
| EXPORT_DIR | 导出文件目录 | exports |
| KNOWLEDGE_BASE_DIR | 知识库目录 | knowledge_base |
| ASSISTANT_PROXY_ENABLED | 是否启用智能助手代理 | True |
| ASSISTANT_BASE_URL | 智能助手服务地址 | http://localhost:8082 |

### 5.2 前端配置

主要配置文件：`frontend/vite.config.js`

- 前端服务端口：3000
- API代理配置：将 `/api` 转发到 `http://localhost:8001`

## 6. 功能模块使用指南

### 6.1 数据导入

#### 6.1.1 通过前端界面导入
1. 登录系统后，点击左侧菜单的"数据管理" → "数据导入"
2. 点击"选择文件"按钮，上传 CSV 或 Excel 文件
3. 点击"开始导入"按钮
4. 等待导入完成，查看导入结果

#### 6.1.2 通过 API 导入

```bash
curl -X POST "http://localhost:8001/api/data/import/csv" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@Dataset/SHIFDR_Structured_Energy_Dataset.csv"
```

### 6.2 数据查询

1. 点击左侧菜单的"数据管理" → "数据查询"
2. 设置查询条件：
   - 建筑选择
   - 时间范围
   - 监测参数
3. 点击"查询"按钮
4. 查看查询结果表格
5. 可选择导出数据

### 6.3 统计分析

系统提供13类核心统计分析功能：

1. **时段汇总统计**：按不同时段汇总能耗数据
2. **COP（性能系数）计算**：计算空调系统性能
3. **数据异常分析**：检测能耗异常
4. **能耗排名分析**：建筑能耗排名
5. **能耗趋势分析**：能耗随时间变化趋势
6. **峰值需求分析**：分析能耗峰值
7. **能耗强度分析**：单位面积能耗分析
8. **对比分析**：不同建筑或时段能耗对比
9. **天气相关性分析**：能耗与天气因素相关性
10. **人员密度影响分析**：人员密度对能耗的影响
11. **小时模式分析**：24小时能耗模式
12. **周模式分析**：一周内能耗模式
13. **季节性分析**：不同季节能耗模式

使用方法：
1. 点击左侧菜单的"统计分析"
2. 选择相应的分析类型
3. 设置分析参数
4. 查看分析结果和图表
5. 可选择导出分析报告

### 6.4 智能问答

1. 点击左侧菜单的"智能问答"
2. 在输入框中输入问题，例如：
   - "为什么建筑A的能耗突然增加？"
   - "如何降低空调能耗？"
   - "设备维护周期是多久？"
3. 点击"发送"按钮
4. 查看系统回答

### 6.5 知识库管理

1. 点击左侧菜单的"知识库管理"
2. 查看数据字典、设备手册等内容
3. 可上传自定义文档到知识库

### 6.6 报表导出

1. 点击左侧菜单的"报表导出"
2. 设置报表时间范围
3. 选择报表类型
4. 点击"生成报表"按钮
5. 下载生成的PDF报表

## 7. 常见问题排查

### 7.1 端口被占用

```powershell
# 查看 8001 端口
netstat -ano | findstr :8001

# 查看 3000 端口
netstat -ano | findstr :3000

# 结束进程（替换 PID）
taskkill /PID <进程ID> /F
```

### 7.2 Python 模块未找到

```powershell
cd backend
pip install -r requirements.txt
```

### 7.3 npm 依赖问题

```powershell
cd frontend
npm install
```

### 7.4 数据库连接失败

**SQLite**：自动创建，无需配置

**PostgreSQL**：
1. 确认 PostgreSQL 服务运行
2. 确认数据库已创建
3. 检查 `.env` 文件中的密码

### 7.5 数据导入失败

- 检查文件格式是否正确
- 检查文件编码是否为 UTF-8
- 检查数据字段是否符合要求
- 查看系统日志获取详细错误信息

### 7.6 智能问答无响应

- 确认智能助手服务是否运行
- 检查网络连接
- 查看系统日志获取详细错误信息

## 8. API文档

启动后端服务后访问：
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

### 8.1 主要API端点

| 端点 | 方法 | 功能 |
|------|------|------|
| /api/data/import/csv | POST | 导入CSV数据 |
| /api/data/import/excel | POST | 导入Excel数据 |
| /api/query/data | GET | 查询能耗数据 |
| /api/query/stats | GET | 获取统计数据 |
| /api/intelligence/chat | POST | 智能问答 |
| /api/intelligence/initialize-knowledge-base | POST | 初始化知识库 |
| /api/auth/login | POST | 用户登录 |
| /api/auth/register | POST | 用户注册 |

### 8.2 MCP协议支持

系统支持MCP协议，可通过以下接口调用：

列出可用工具：
```bash
curl http://localhost:8001/api/mcp/tools
```

调用工具示例：
```bash
curl -X POST http://localhost:8001/api/mcp/call-tool \
  -H "Content-Type: application/json" \
  -d '{
    "name": "query_energy_data",
    "arguments": {
      "building_id": "Aral",
      "start_time": "2021-01-01 00:00:00",
      "end_time": "2021-01-31 23:59:59"
    }
  }'
```

## 9. 维护与管理

### 9.1 数据备份

**SQLite**：
- 直接复制 `beims.db` 文件

**PostgreSQL**：
```bash
# 备份整个数据库
pg_dump -U postgres -d building_energy > backup.sql

# 或使用自定义格式（推荐）
pg_dump -U postgres -d building_energy -F c -f backup.dump
```

### 9.2 数据恢复

**SQLite**：
- 替换 `beims.db` 文件

**PostgreSQL**：
```bash
# 从 SQL 文件恢复
psql -U postgres -d building_energy < backup.sql

# 从自定义格式恢复
pg_restore -U postgres -d building_energy backup.dump
```

### 9.3 系统更新

1. 停止当前运行的服务
2. 拉取最新代码
3. 更新依赖：
   - 后端：`pip install -r requirements.txt`
   - 前端：`npm install`
4. 重新启动服务

### 9.4 性能优化

**数据库优化**：
- 为常用查询字段创建索引
- 定期执行 VACUUM 和 ANALYZE 操作
- 调整 PostgreSQL 配置参数

**应用优化**：
- 启用缓存
- 优化查询语句
- 合理设置批处理大小

## 10. 故障处理

### 10.1 系统无法启动

- 检查端口是否被占用
- 检查依赖是否安装完整
- 检查数据库连接是否正常
- 查看系统日志获取详细错误信息

### 10.2 数据丢失

- 从备份恢复数据
- 检查数据库日志
- 联系技术支持

### 10.3 系统响应缓慢

- 检查服务器资源使用情况
- 优化数据库查询
- 检查网络连接
- 考虑增加服务器资源

## 11. 联系方式

如有任何问题或建议，请联系系统管理员或开发团队。

---

**版本**：1.0.0
**更新时间**：2026-04-18
**适用系统**：BEIMS 建筑能源智能管理系统