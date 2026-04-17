# BEIMS 建筑能源智能管理系统 - Code Wiki

## 1. 项目概述

BEIMS (Building Energy Intelligent Management System) 是一款集查询统计与智慧运维于一体的建筑能源智能管理系统。系统提供了全面的能源数据管理、分析和智能决策支持功能，帮助建筑管理者实现能源的高效利用和智能化运维。

### 核心功能
- 数据层：能耗数据集构建、清洗与标准化，支持CSV、Excel格式导入
- 查询统计模块：基于MCP协议的数据接入与查询接口，13类核心统计分析功能，12种可视化图表展示
- 智慧运维模块：领域知识库构建，基于RAG技术的智能问答，能耗异常原因分析，设备运行状态查询，节能建议生成
- 系统集成：RESTful API接口，MCP协议支持，Vue.js前端界面，响应式设计

## 2. 目录结构

```
BEIMS建筑能源智能管理系统/
├── backend/                    # 后端代码
│   ├── app/                    # 应用核心
│   │   ├── config/            # 配置文件
│   │   ├── models/            # 数据模型
│   │   ├── routers/           # API路由
│   │   ├── services/          # 业务逻辑
│   │   ├── utils/             # 工具类
│   │   └── main.py            # 主应用
│   ├── uploads/               # 上传文件存储
│   ├── .env.example           # 环境变量示例
│   ├── requirements.txt       # Python依赖
│   └── init_database.py       # 数据库初始化
├── frontend/                   # 前端代码
│   ├── dist/                  # 构建输出
├── Dataset/                    # 数据集
│   └── SHIFDR_Structured_Energy_Dataset.csv
├── database/                   # 数据库相关
│   └── init_postgresql.sql
├── README.md                  # 项目说明
└── OPERATIONS_BASELINE.md     # 运行基线与启动约定
```

## 3. 系统架构

BEIMS系统采用前后端分离的架构设计，主要由以下部分组成：

### 3.1 后端架构

后端基于FastAPI框架构建，采用模块化设计，主要包含以下核心组件：

1. **配置层**：负责系统配置管理，支持环境变量配置
2. **数据模型层**：定义数据库表结构，支持SQLite和PostgreSQL
3. **路由层**：处理HTTP请求，提供API接口
4. **服务层**：实现核心业务逻辑
5. **工具层**：提供通用工具函数

### 3.2 前端架构

前端基于Vue.js 3构建，使用Element Plus组件库，主要包含以下核心功能：

1. **数据可视化**：使用ECharts实现各类图表展示
2. **数据管理**：支持数据导入、查询和导出
3. **智能分析**：集成智能问答和异常分析功能
4. **响应式设计**：适配不同设备屏幕

### 3.3 数据流

1. **数据输入**：通过CSV/Excel文件导入或API接口录入
2. **数据处理**：经过清洗、标准化和验证后存入数据库
3. **数据查询**：通过API接口查询和统计数据
4. **数据分析**：生成各类统计分析结果和可视化图表
5. **智能决策**：基于知识库和RAG技术提供智能建议

## 4. 核心模块

### 4.1 数据层

数据层负责数据的导入、清洗、标准化和存储，主要功能包括：

- **数据导入**：支持CSV和Excel格式的文件导入
- **数据清洗**：处理缺失值、异常值和重复数据
- **数据标准化**：统一数据格式和单位
- **数据验证**：确保数据质量和完整性
- **数据存储**：支持SQLite和PostgreSQL数据库

**核心文件**：
- [data_router.py](file:///workspace/BEIMS建筑能源智能管理系统/backend/app/routers/data_router.py)：数据管理API接口
- [data_processor.py](file:///workspace/BEIMS建筑能源智能管理系统/backend/app/services/data_processor.py)：数据处理核心逻辑
- [database.py](file:///workspace/BEIMS建筑能源智能管理系统/backend/app/models/database.py)：数据模型定义

### 4.2 查询统计模块

查询统计模块提供丰富的数据查询和分析功能，主要包括：

- **多条件查询**：支持按建筑、时间、监测参数等条件查询
- **时间聚合统计**：按日、周、月、年聚合数据
- **能耗分析**：包括趋势分析、峰值需求分析、强度分析等
- **对比分析**：不同建筑、不同时期的能耗对比
- **异常检测**：自动检测能耗异常并分析原因
- **可视化展示**：支持12种不同类型的图表

**核心文件**：
- [query_router.py](file:///workspace/BEIMS建筑能源智能管理系统/backend/app/routers/query_router.py)：查询统计API接口
- [statistics.py](file:///workspace/BEIMS建筑能源智能管理系统/backend/app/services/statistics.py)：统计分析核心逻辑
- [visualization.py](file:///workspace/BEIMS建筑能源智能管理系统/backend/app/services/visualization.py)：可视化服务

### 4.3 智慧运维模块

智慧运维模块基于RAG技术，提供智能问答和决策支持功能，主要包括：

- **知识库管理**：构建和管理领域知识库
- **智能问答**：基于自然语言的智能查询和回答
- **异常分析**：分析能耗异常的原因并提供解决方案
- **设备状态查询**：查询设备运行状态和维护建议
- **节能建议**：基于建筑类型和能耗数据生成节能建议

**核心文件**：
- [intelligence_router.py](file:///workspace/BEIMS建筑能源智能管理系统/backend/app/routers/intelligence_router.py)：智慧运维API接口
- [rag_service.py](file:///workspace/BEIMS建筑能源智能管理系统/backend/app/services/rag_service.py)：RAG服务核心逻辑

### 4.4 系统集成

系统集成模块提供API接口和协议支持，主要包括：

- **RESTful API**：标准RESTful接口设计
- **MCP协议**：支持MCP协议的数据接入和调用
- **CORS支持**：跨域资源共享配置
- **错误处理**：全局异常处理机制

**核心文件**：
- [main.py](file:///workspace/BEIMS建筑能源智能管理系统/backend/app/main.py)：主应用入口
- [mcp_server.py](file:///workspace/BEIMS建筑能源智能管理系统/backend/app/utils/mcp_server.py)：MCP服务器实现

## 5. 数据模型

BEIMS系统定义了以下主要数据模型：

### 5.1 EnergyData

能耗数据模型，存储建筑能耗的详细数据：

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | Integer | 主键，自增 |
| building_id | String(50) | 建筑ID，索引 |
| building_type | String(100) | 建筑类型 |
| timestamp | DateTime | 时间戳，索引 |
| electricity_kwh | Float | 电力消耗(kWh) |
| water_m3 | Float | 水消耗(m³) |
| hvac_kwh | Float | 空调能耗(kWh) |
| chw_supply_temp | Float | 冷冻水供水温度 |
| chw_return_temp | Float | 冷冻水回水温度 |
| outdoor_temp | Float | 室外温度 |
| humidity_pct | Float | 湿度百分比 |
| occupancy_density | Float | 人员密度 |
| meter_id | String(50) | 仪表ID |
| system_status | String(20) | 系统状态 |

### 5.2 Building

建筑信息模型，存储建筑的基本信息：

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | Integer | 主键，自增 |
| building_id | String(50) | 建筑ID，唯一 |
| building_name | String(200) | 建筑名称 |
| building_type | String(100) | 建筑类型 |
| location | String(200) | 位置 |
| total_area | Float | 总面积 |
| floors | Integer | 楼层数 |
| year_built | Integer | 建造年份 |
| description | Text | 描述 |
| is_active | Boolean | 是否激活 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### 5.3 Meter

仪表信息模型，存储计量仪表的基本信息：

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | Integer | 主键，自增 |
| meter_id | String(50) | 仪表ID，唯一 |
| meter_name | String(200) | 仪表名称 |
| meter_type | String(50) | 仪表类型 |
| building_id | String(50) | 所属建筑ID |
| location | String(200) | 位置 |
| installation_date | DateTime | 安装日期 |
| is_active | Boolean | 是否激活 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### 5.4 AnomalyRecord

异常记录模型，存储能耗异常的记录：

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | Integer | 主键，自增 |
| building_id | String(50) | 建筑ID，索引 |
| timestamp | DateTime | 时间戳，索引 |
| anomaly_type | String(50) | 异常类型 |
| severity | String(20) | 严重程度 |
| description | Text | 描述 |
| metric_name | String(100) | 指标名称 |
| metric_value | Float | 指标值 |
| threshold | Float | 阈值 |
| is_resolved | Boolean | 是否已解决 |
| resolved_at | DateTime | 解决时间 |
| resolved_by | String(100) | 解决人 |
| created_at | DateTime | 创建时间 |

### 5.5 KnowledgeDocument

知识库文档模型，存储知识库中的文档：

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | Integer | 主键，自增 |
| title | String(500) | 标题 |
| category | String(100) | 类别 |
| content | Text | 内容 |
| file_path | String(500) | 文件路径 |
| file_type | String(20) | 文件类型 |
| tags | String(500) | 标签 |
| is_active | Boolean | 是否激活 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### 5.6 User

用户模型，存储系统用户信息：

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | Integer | 主键，自增 |
| username | String(100) | 用户名，唯一 |
| email | String(200) | 邮箱，唯一 |
| hashed_password | String(255) | 哈希密码 |
| full_name | String(200) | 全名 |
| role | String(50) | 角色 |
| is_active | Boolean | 是否激活 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

## 6. API接口

### 6.1 数据管理接口

| 接口路径 | 方法 | 功能描述 |
|----------|------|----------|
| `/api/data/import/csv` | POST | 导入CSV格式数据 |
| `/api/data/import/excel` | POST | 导入Excel格式数据 |
| `/api/data/buildings` | GET | 获取建筑列表 |
| `/api/data/meters` | GET | 获取仪表列表 |
| `/api/data/date-range` | GET | 获取数据时间范围 |
| `/api/data/summary` | GET | 获取数据汇总信息 |
| `/api/data/data` | GET | 获取数据列表（分页） |
| `/api/data/aggregated` | GET | 获取聚合数据 |
| `/api/data/validate` | POST | 验证数据文件 |

### 6.2 查询统计接口

| 接口路径 | 方法 | 功能描述 |
|----------|------|----------|
| `/api/query/data` | POST | 查询能耗数据 |
| `/api/query/statistics/time-aggregation` | POST | 时间聚合统计 |
| `/api/query/statistics/cop` | POST | 计算COP（性能系数） |
| `/api/query/statistics/anomalies` | POST | 检测异常 |
| `/api/query/statistics/ranking` | POST | 能耗排名分析 |
| `/api/query/statistics/trend` | POST | 能耗趋势分析 |
| `/api/query/statistics/peak-demand` | POST | 峰值需求分析 |
| `/api/query/statistics/intensity` | POST | 能耗强度分析 |
| `/api/query/statistics/comparison` | POST | 对比分析 |
| `/api/query/statistics/weather-correlation` | POST | 天气相关性分析 |
| `/api/query/statistics/occupancy-impact` | POST | 人员密度影响分析 |
| `/api/query/statistics/hourly-pattern` | POST | 小时模式分析 |
| `/api/query/statistics/weekly-pattern` | POST | 周模式分析 |
| `/api/query/statistics/seasonal` | POST | 季节性分析 |
| `/api/query/statistics/agent-report` | POST | 生成智能报表 |
| `/api/query/statistics/energy-efficiency` | POST | 能源效率分析 |
| `/api/query/statistics/equipment-performance` | POST | 设备性能分析 |
| `/api/query/statistics/energy-prediction` | POST | 能源预测 |
| `/api/query/statistics/energy-savings` | POST | 节能潜力分析 |
| `/api/query/statistics/cost-analysis` | POST | 成本分析 |

### 6.3 可视化接口

| 接口路径 | 方法 | 功能描述 |
|----------|------|----------|
| `/api/query/visualization/line-chart` | POST | 创建折线图 |
| `/api/query/visualization/multi-line-chart` | POST | 创建多线折线图 |
| `/api/query/visualization/bar-chart` | POST | 创建柱状图 |
| `/api/query/visualization/pie-chart` | POST | 创建饼图 |
| `/api/query/visualization/heatmap` | POST | 创建热力图 |
| `/api/query/visualization/scatter-plot` | POST | 创建散点图 |
| `/api/query/visualization/box-plot` | POST | 创建箱线图 |
| `/api/query/visualization/gauge-chart` | POST | 创建仪表盘 |
| `/api/query/visualization/radar-chart` | POST | 创建雷达图 |
| `/api/query/visualization/area-chart` | POST | 创建面积图 |
| `/api/query/visualization/histogram` | POST | 创建直方图 |
| `/api/query/visualization/treemap` | POST | 创建树状图 |
| `/api/query/visualization/animated-line-chart` | POST | 创建动画折线图 |
| `/api/query/visualization/3d-scatter-plot` | POST | 创建3D散点图 |
| `/api/query/visualization/polar-chart` | POST | 创建极坐标图 |
| `/api/query/visualization/export` | POST | 导出图表 |
| `/api/query/visualization/options` | GET | 获取图表选项 |

### 6.4 智慧运维接口

| 接口路径 | 方法 | 功能描述 |
|----------|------|----------|
| `/api/intelligence/initialize-knowledge-base` | POST | 初始化知识库 |
| `/api/intelligence/add-document` | POST | 添加文档到知识库 |
| `/api/intelligence/add-text` | POST | 添加文本到知识库 |
| `/api/intelligence/search` | POST | 搜索知识库 |
| `/api/intelligence/query` | POST | 智能查询 |
| `/api/intelligence/analyze-anomaly` | POST | 分析能耗异常 |
| `/api/intelligence/equipment-status` | POST | 查询设备状态 |
| `/api/intelligence/energy-saving-suggestions` | POST | 获取节能建议 |
| `/api/intelligence/data-dictionary` | GET | 获取能源数据字典 |
| `/api/intelligence/equipment-manuals` | GET | 获取设备手册 |
| `/api/intelligence/health` | GET | 健康检查 |
| `/api/intelligence/documents` | GET | 获取文档列表 |
| `/api/intelligence/documents/{document_id}` | GET | 获取文档详情 |
| `/api/intelligence/categories` | GET | 获取文档类别 |
| `/api/intelligence/tags` | GET | 获取标签 |
| `/api/intelligence/search-by-category` | POST | 按类别搜索 |
| `/api/intelligence/search-by-tags` | POST | 按标签搜索 |

### 6.5 MCP协议接口

| 接口路径 | 方法 | 功能描述 |
|----------|------|----------|
| `/api/mcp/tools` | GET | 列出可用工具 |
| `/api/mcp/call-tool` | POST | 调用工具 |

## 7. 技术栈

### 7.1 后端技术栈

| 技术/库 | 用途 | 版本/说明 |
|---------|------|----------|
| FastAPI | Web框架 | 高性能异步框架 |
| SQLAlchemy | ORM | 数据库对象关系映射 |
| PostgreSQL | 数据库 | 生产环境推荐 |
| SQLite | 数据库 | 开发测试默认 |
| Pandas | 数据处理 | 数据清洗和分析 |
| NumPy | 数值计算 | 科学计算库 |
| Plotly | 可视化 | 交互式图表生成 |
| Matplotlib | 可视化 | 静态图表生成 |
| LangChain | RAG框架 | 构建知识库和问答系统 |
| ChromaDB | 向量数据库 | 存储和检索嵌入向量 |
| Sentence Transformers | 文本嵌入 | 生成文本向量表示 |
| ReportLab | 报表生成 | PDF报表导出 |
| Pydantic | 数据验证 | 数据模型和验证 |

### 7.2 前端技术栈

| 技术/库 | 用途 | 版本/说明 |
|---------|------|----------|
| Vue.js 3 | 前端框架 | 响应式UI开发 |
| Element Plus | UI组件库 | 提供丰富的UI组件 |
| ECharts | 图表库 | 数据可视化图表 |
| Axios | HTTP客户端 | API调用 |
| Pinia | 状态管理 | 前端状态管理 |
| Vite | 构建工具 | 前端项目构建 |

## 8. 部署与运行

### 8.1 环境要求

- Python 3.8+
- Node.js 16+
- PostgreSQL 12+（可选，默认使用SQLite）

### 8.2 数据库配置

#### SQLite（默认，推荐用于开发测试）
- 无需安装数据库软件
- 数据存储在本地文件 `beims.db`
- 开箱即用，适合快速体验

#### PostgreSQL（推荐用于生产环境）
- 性能更好，支持大规模数据
- 支持并发访问
- 功能更强大

### 8.3 启动步骤

#### 一键启动（推荐）

双击运行：
```
start_beims.bat
```

系统会自动：
1. 检查环境（Python、Node.js）
2. 安装依赖（首次运行）
3. 启动后端服务（端口 8000）
4. 启动前端服务（端口 3000）

访问：http://localhost:3000

#### 手动启动

1. **启动后端**
```bash
cd backend
pip install -r requirements.txt
python -m app.main
```

2. **启动前端**
```bash
cd frontend
npm install
npm run dev
```

3. **访问系统**
- 前端界面: http://localhost:3000
- API文档: http://localhost:8000/docs

### 8.4 数据导入

#### 通过前端界面导入
1. 启动系统后访问前端界面
2. 点击"数据管理" → "数据导入"
3. 上传 CSV 或 Excel 文件
4. 等待导入完成

#### 通过 API 导入

```bash
curl -X POST "http://localhost:8000/api/data/import/csv" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@Dataset/SHIFDR_Structured_Energy_Dataset.csv"
```

#### 初始化知识库

```bash
curl -X POST "http://localhost:8000/api/intelligence/initialize-knowledge-base"
```

或通过前端界面的"智能问答"页面点击"初始化知识库"按钮。

## 9. 常见问题与故障排除

### 9.1 端口被占用

```powershell
# 查看 8000 端口
netstat -ano | findstr :8000

# 查看 3000 端口
netstat -ano | findstr :3000

# 结束进程（替换 PID）
taskkill /PID <进程ID> /F
```

### 9.2 Python 模块未找到

```powershell
cd backend
pip install -r requirements.txt
```

### 9.3 npm 依赖问题

```powershell
cd frontend
npm install
```

### 9.4 数据库连接失败

SQLite: 自动创建，无需配置

PostgreSQL:
1. 确认 PostgreSQL 服务运行
2. 确认数据库已创建
3. 检查 `.env` 文件中的密码

### 9.5 数据导入失败

- 检查文件格式是否正确
- 检查数据格式是否符合要求
- 查看日志了解具体错误信息

## 10. 开发与扩展

### 10.1 项目结构扩展

- **添加新模块**：在 `app/services` 中创建新的服务类
- **添加新API**：在 `app/routers` 中创建新的路由文件
- **添加新数据模型**：在 `app/models/database.py` 中定义新模型
- **添加新可视化图表**：在 `app/services/visualization.py` 中实现新图表类型

### 10.2 性能优化

- **数据库索引**：为常用查询字段创建索引
- **缓存机制**：使用Redis缓存频繁访问的数据
- **批量处理**：使用批量导入和查询减少数据库操作
- **异步处理**：使用FastAPI的异步特性提高并发性能

### 10.3 安全措施

- **密码哈希**：使用bcrypt对用户密码进行哈希处理
- **JWT认证**：使用JWT进行用户认证
- **输入验证**：对所有输入进行严格验证
- **CORS配置**：合理配置CORS策略
- **日志记录**：记录关键操作和异常

## 11. 总结

BEIMS建筑能源智能管理系统是一款功能全面、技术先进的建筑能源管理解决方案。系统通过数据采集、分析和智能决策支持，帮助建筑管理者实现能源的高效利用和智能化运维。

### 核心优势

1. **全面的数据管理**：支持多种数据格式导入，提供完整的数据清洗和标准化功能
2. **丰富的分析功能**：13类核心统计分析功能，12种可视化图表展示
3. **智能决策支持**：基于RAG技术的智能问答和异常分析
4. **灵活的部署选项**：支持SQLite和PostgreSQL数据库
5. **良好的扩展性**：模块化设计，易于扩展和定制

### 应用场景

- **商业建筑**：办公楼、商场、酒店等
- **公共建筑**：医院、学校、政府大楼等
- **工业建筑**：工厂、仓库等
- **住宅建筑**：小区、公寓等

BEIMS系统不仅是一个能源管理工具，更是一个智能决策支持系统，通过数据驱动的方法，帮助建筑管理者实现能源的可持续利用和智能化运维。