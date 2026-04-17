# BEIMS 建筑能源智能管理系统

## 项目简介

BEIMS (Building Energy Intelligent Management System) 是一款集查询统计与智慧运维于一体的建筑能源智能管理系统。

> 运行基线与启动约定请优先查看：`OPERATIONS_BASELINE.md`

## 核心功能模块

### 1. 数据层
- ✅ 能耗数据集构建、清洗与标准化
- ✅ 数据集导入接口（支持CSV、Excel格式）
- ✅ 数据验证和质量检查
- ✅ 支持PostgreSQL数据库

### 2. 查询统计模块
- ✅ 基于MCP协议的数据接入与查询接口
- ✅ 支持按建筑、时间、监测参数等条件精准查询
- ✅ 13类核心统计分析功能
- ✅ 12种可视化图表展示
- ✅ 统计报表自动生成与导出（PDF格式）

### 3. 智慧运维模块
- ✅ 领域知识库构建
  - 能耗数据字典
  - 设备运维手册
  - 自定义文档导入
- ✅ 基于RAG技术的智能问答
- ✅ 能耗异常原因分析
- ✅ 设备运行状态查询
- ✅ 节能建议生成

### 4. 系统集成
- ✅ RESTful API接口
- ✅ MCP协议支持
- ✅ Vue.js前端界面
- ✅ 响应式设计

## 技术栈

### 后端
- **框架**: FastAPI
- **ORM**: SQLAlchemy
- **数据库**: PostgreSQL
- **数据处理**: Pandas, NumPy
- **可视化**: Plotly, Matplotlib
- **RAG**: LangChain, ChromaDB, Sentence Transformers
- **报表**: ReportLab

### 前端
- **框架**: Vue.js 3
- **UI组件**: Element Plus
- **图表**: ECharts
- **HTTP客户端**: Axios
- **状态管理**: Pinia

## 项目结构

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
│   ├── knowledge_base/        # 知识库存储
│   ├── requirements.txt       # Python依赖
│   └── start_beims.bat        # 后端启动脚本
├── frontend/                   # 前端代码
│   ├── src/
│   │   ├── components/        # 组件
│   │   ├── views/             # 视图
│   │   ├── router/            # 路由
│   │   ├── store/             # 状态管理
│   │   ├── api/               # API接口
│   │   └── main.js            # 入口文件
│   ├── package.json           # Node依赖
│   └── vite.config.js         # Vite配置
├── Dataset/                    # 数据集
│   └── SHIFDR_Structured_Energy_Dataset.csv
├── start_beims.bat            # 一键启动脚本
└── README.md                  # 项目说明
```

## 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+（可选，默认使用SQLite）

### 数据库选择

BEIMS 支持两种数据库：

#### 方式一：SQLite（默认，推荐用于开发测试）
- ✅ 无需安装数据库软件
- ✅ 数据存储在本地文件 `beims.db`
- ✅ 开箱即用，适合快速体验

#### 方式二：PostgreSQL（推荐用于生产环境）
- ✅ 性能更好，支持大规模数据
- ✅ 支持并发访问
- ✅ 功能更强大

**PostgreSQL 安装指南**: 请查看下方的 "PostgreSQL 安装与配置指南" 部分

### PostgreSQL 安装与配置指南

#### 一、安装 PostgreSQL

##### Windows 系统

###### 方式一：使用安装包（推荐）

1. **下载 PostgreSQL**
   - 访问官网：https://www.postgresql.org/download/windows/
   - 或直接下载：https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
   - 选择最新版本（推荐 PostgreSQL 16.x）

2. **运行安装程序**
   - 双击下载的 `.exe` 文件
   - 选择安装路径（默认：`C:\Program Files\PostgreSQL\16`）
   - 选择组件（保持默认即可）
   - 设置超级用户密码（**请记住此密码**）
   - 设置端口（默认：5432）
   - 设置区域（默认：Default locale）

3. **完成安装**
   - 安装完成后，PostgreSQL 服务会自动启动
   - 会自动安装 pgAdmin 4（图形化管理工具）

###### 方式二：使用 Chocolatey

```powershell
# 安装 Chocolatey（如果未安装）
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# 安装 PostgreSQL
choco install postgresql -y
```

#### 二、创建数据库

##### 方式一：使用 pgAdmin 4（图形化界面）

1. **打开 pgAdmin 4**
   - 开始菜单 → PostgreSQL 16 → pgAdmin 4

2. **连接到服务器**
   - 左侧树形菜单 → Servers → PostgreSQL 16
   - 输入安装时设置的密码

3. **创建数据库**
   - 右键点击 "Databases"
   - 选择 "Create" → "Database"
   - 输入数据库名称：`building_energy`
   - 点击 "Save"

##### 方式二：使用命令行（psql）

1. **打开 SQL Shell**
   - 开始菜单 → PostgreSQL 16 → SQL Shell (psql)

2. **连接到服务器**
   ```
   Server [localhost]: localhost
   Database [postgres]: postgres
   Port [5432]: 5432
   Username [postgres]: postgres
   Password: [输入安装时设置的密码]
   ```

3. **创建数据库**
   ```sql
   CREATE DATABASE building_energy;
   
   -- 查看数据库列表
   \l
   
   -- 连接到新数据库
   \c building_energy
   
   -- 退出
   \q
   ```

##### 方式三：使用 Windows 命令行

```powershell
# 设置环境变量（如果未添加到PATH）
$env:Path += ";C:\Program Files\PostgreSQL\16\bin"

# 创建数据库
psql -U postgres -c "CREATE DATABASE building_energy;"

# 输入密码后，数据库创建成功
```

#### 三、配置 BEIMS 系统

##### 1. 修改配置文件

在 `backend` 目录下创建 `.env` 文件：

```env
# 数据库配置
DATABASE_URL=postgresql://postgres:你的密码@localhost:5432/building_energy

# 示例（密码是安装时设置的密码）
# DATABASE_URL=postgresql://postgres:123456@localhost:5432/building_energy

# 其他配置
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI配置（可选）
OPENAI_API_KEY=
OPENAI_API_BASE=

# 文件存储路径
UPLOAD_DIR=uploads
EXPORT_DIR=exports
KNOWLEDGE_BASE_DIR=knowledge_base
```

##### 2. 安装 Python 依赖

```bash
cd backend
pip install psycopg2-binary
```

##### 3. 测试数据库连接

创建测试脚本 `test_db.py`：

```python
import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="building_energy",
        user="postgres",
        password="你的密码"
    )
    print("✅ 数据库连接成功！")
    conn.close()
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
```

运行测试：
```bash
python test_db.py
```

#### 四、常用 PostgreSQL 命令

##### 连接数据库

```bash
# 使用 psql 连接
psql -U postgres -d building_energy

# 或指定主机和端口
psql -h localhost -p 5432 -U postgres -d building_energy
```

##### 常用 SQL 命令

```sql
-- 查看所有数据库
\l

-- 连接到数据库
\c building_energy

-- 查看所有表
\dt

-- 查看表结构
\d energy_data

-- 查看表数据
SELECT * FROM energy_data LIMIT 10;

-- 统计记录数
SELECT COUNT(*) FROM energy_data;

-- 退出
\q
```

##### 数据库管理

```sql
-- 创建用户
CREATE USER beims_user WITH PASSWORD 'your_password';

-- 授予权限
GRANT ALL PRIVILEGES ON DATABASE building_energy TO beims_user;

-- 修改密码
ALTER USER postgres WITH PASSWORD 'new_password';

-- 删除数据库
DROP DATABASE building_energy;
```

#### 五、数据备份与恢复

##### 备份数据库

```bash
# 备份整个数据库
pg_dump -U postgres -d building_energy > backup.sql

# 或使用自定义格式（推荐）
pg_dump -U postgres -d building_energy -F c -f backup.dump
```

##### 恢复数据库

```bash
# 从 SQL 文件恢复
psql -U postgres -d building_energy < backup.sql

# 从自定义格式恢复
pg_restore -U postgres -d building_energy backup.dump
```

#### 六、常见问题

##### 1. 连接被拒绝

**问题**: `connection refused` 或 `could not connect to server`

**解决方案**:
```powershell
# 检查 PostgreSQL 服务是否运行
Get-Service postgresql*

# 启动服务
Start-Service postgresql-x64-16

# 或通过服务管理器
services.msc
```

##### 2. 密码认证失败

**问题**: `password authentication failed`

**解决方案**:
1. 确认密码正确
2. 修改 `pg_hba.conf` 文件（位于 `C:\Program Files\PostgreSQL\16\data\`）
   ```
   # 将 METHOD 从 md5 改为 trust（仅用于开发环境）
   host    all    all    127.0.0.1/32    trust
   ```
3. 重启 PostgreSQL 服务

##### 3. 端口被占用

**问题**: `port 5432 is already in use`

**解决方案**:
```powershell
# 查看端口占用
netstat -ano | findstr :5432

# 结束占用进程（替换 PID）
taskkill /PID <进程ID> /F
```

##### 4. 编码问题

**问题**: 中文乱码

**解决方案**:
```sql
-- 创建数据库时指定编码
CREATE DATABASE building_energy 
WITH ENCODING='UTF8' 
LC_COLLATE='Chinese_China.936' 
LC_CTYPE='Chinese_China.936';
```

#### 七、性能优化建议

##### 1. 修改配置文件

编辑 `postgresql.conf`（位于 `C:\Program Files\PostgreSQL\16\data\`）：

```ini
# 内存设置
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB

# 连接设置
max_connections = 100

# 日志设置
logging_collector = on
log_directory = 'pg_log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
```

##### 2. 创建索引

```sql
-- 为常用查询字段创建索引
CREATE INDEX idx_energy_data_building_id ON energy_data(building_id);
CREATE INDEX idx_energy_data_timestamp ON energy_data(timestamp);
CREATE INDEX idx_energy_data_building_timestamp ON energy_data(building_id, timestamp);
```

##### 3. 定期维护

```sql
-- 分析表
ANALYZE energy_data;

-- 清理和优化
VACUUM ANALYZE energy_data;
```

#### 八、使用 pgAdmin 4 管理数据库

##### 1. 打开 pgAdmin 4
- 开始菜单 → PostgreSQL 16 → pgAdmin 4

##### 2. 主要功能
- 📊 数据库管理：创建、删除、备份、恢复
- 📝 SQL 查询工具：编写和执行 SQL
- 📈 性能监控：查看查询性能
- 👥 用户管理：创建和管理用户权限
- 📋 数据导入导出：支持 CSV、Excel 等格式

##### 3. 导入 CSV 数据
1. 右键点击表 → Import/Export Data
2. 选择 Import
3. 选择 CSV 文件
4. 配置字段映射
5. 点击 OK 开始导入

#### 九、卸载 PostgreSQL

##### Windows

1. 控制面板 → 程序和功能
2. 找到 PostgreSQL 16
3. 右键 → 卸载
4. 删除数据目录（可选）：`C:\Program Files\PostgreSQL\16\data`

#### 十、相关链接

- PostgreSQL 官网：https://www.postgresql.org/
- PostgreSQL 文档：https://www.postgresql.org/docs/16/index.html
- pgAdmin 文档：https://www.pgadmin.org/docs/
- PostgreSQL 教程：https://www.runoob.com/postgresql/postgresql-tutorial.html

### 启动步骤

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

## 数据导入

### 通过前端界面导入
1. 启动系统后访问前端界面
2. 点击"数据管理" → "数据导入"
3. 上传 CSV 或 Excel 文件
4. 等待导入完成

### 通过 API 导入

```bash
curl -X POST "http://localhost:8000/api/data/import/csv" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@Dataset/SHIFDR_Structured_Energy_Dataset.csv"
```

### 初始化知识库

```bash
curl -X POST "http://localhost:8000/api/intelligence/initialize-knowledge-base"
```

或通过前端界面的"智能问答"页面点击"初始化知识库"按钮。

## API文档

启动后端服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## MCP协议支持

系统支持MCP协议，可通过以下接口调用：

列出可用工具：
```bash
curl http://localhost:8000/api/mcp/tools
```

调用工具示例：
```bash
curl -X POST http://localhost:8000/api/mcp/call-tool \
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

## 主要功能

### 1. 综合概览
- 数据统计卡片
- 能耗趋势图
- 能耗分布图
- 建筑能耗排名

### 2. 数据查询
- 多条件筛选查询
- 数据表格展示
- 数据导出功能

### 3. 统计分析（13类）
1. 时段汇总统计
2. COP（性能系数）计算
3. 数据异常分析
4. 能耗排名分析
5. 能耗趋势分析
6. 峰值需求分析
7. 能耗强度分析
8. 对比分析
9. 天气相关性分析
10. 人员密度影响分析
11. 小时模式分析
12. 周模式分析
13. 季节性分析

### 4. 可视化图表（12种）
1. 折线图
2. 多线折线图
3. 柱状图
4. 分组柱状图
5. 堆叠柱状图
6. 饼图
7. 环形图
8. 面积图
9. 散点图
10. 热力图
11. 箱线图
12. 雷达图

### 5. 异常检测
- 自动异常检测
- 异常原因分析
- 解决建议生成

### 6. 智能问答
- 自然语言查询
- 基于知识库回答
- 对话历史记录

### 7. 知识库管理
- 数据字典查看
- 设备手册浏览
- 文档上传管理

### 8. 报表导出
- PDF格式报表
- 自定义时间范围
- 一键导出下载

## 故障排除

### 问题 1: 端口被占用

```powershell
# 查看 8000 端口
netstat -ano | findstr :8000

# 查看 3000 端口
netstat -ano | findstr :3000

# 结束进程（替换 PID）
taskkill /PID <进程ID> /F
```

### 问题 2: Python 模块未找到

```powershell
cd backend
pip install -r requirements.txt
```

### 问题 3: npm 依赖问题

```powershell
cd frontend
npm install
```

### 问题 4: 数据库连接失败

SQLite: 自动创建，无需配置

PostgreSQL:
1. 确认 PostgreSQL 服务运行
2. 确认数据库已创建
3. 检查 `.env` 文件中的密码

## 开发团队

BEIMS - Building Energy Intelligent Management System

## 许可证

MIT License
