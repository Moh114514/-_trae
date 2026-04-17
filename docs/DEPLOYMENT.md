# BEIMS 实时监测系统 - 部署指南

## 目录

- [系统架构](#系统架构)
- [后端部署](#后端部署)
- [前端集成](#前端集成)
- [API 接口文档](#api-接口文档)
- [WebSocket 消息格式](#websocket-消息格式)
- [数据格式要求](#数据格式要求)
- [Vue.js 组件集成](#vuejs-组件集成)
- [配置说明](#配置说明)
- [注意事项](#注意事项)

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                         前端层                               │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │  Vue.js 组件     │  │  静态 HTML 页面  │                  │
│  │ RealTimeMonitor │  │   monitor.html   │                  │
│  └────────┬────────┘  └────────┬────────┘                  │
│           │                    │                            │
│           │  WebSocket + REST  │                            │
└───────────┼────────────────────┼────────────────────────────┘
            │                    │
            ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                        后端层                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │               FastAPI + WebSocket                     │   │
│  │  - api_server.py (API 端点)                          │   │
│  │  - realtime_monitor.py (监测核心)                     │   │
│  │  - energy_analyzer.py (能耗分析)                      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                        数据层                                │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │   PostgreSQL    │  │    ChromaDB     │                  │
│  │   (能耗数据)     │  │   (知识库)      │                  │
│  └─────────────────┘  └─────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 后端部署

### 1. 环境要求

| 依赖 | 版本要求 | 说明 |
|------|----------|------|
| Python | ≥ 3.8 | 运行环境 |
| PostgreSQL | ≥ 12 | 能耗数据存储 |
| Redis | 可选 | 用于分布式部署 |

### 2. Python 依赖

```bash
pip install fastapi uvicorn websockets pandas psycopg2-binary numpy
```

### 3. 核心文件

| 文件 | 用途 |
|------|------|
| `api_server.py` | FastAPI 主程序，API 端点定义 |
| `realtime_monitor.py` | 实时监测核心逻辑 |
| `energy_analyzer.py` | 能耗分析模块 |

### 4. 数据库配置

```python
# 在 api_server.py 和 realtime_monitor.py 中修改
DB_CONFIG = {
    "host": "your-db-host",
    "port": 5432,
    "database": "building_energy",
    "user": "your-user",
    "password": "your-password"
}
```

### 5. 启动后端

```bash
# 开发环境
python api_server.py

# 生产环境
uvicorn api_server:app --host 0.0.0.0 --port 8080 --workers 4
```

### 6. Docker 部署（可选）

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

## 前端集成

### 方式一：静态 HTML 页面

直接使用 `monitor.html`：

```html
<!-- 在任何 HTML 页面中引入 -->
<script src="path/to/monitor-standalone.js"></script>
<div id="monitor-root"></div>
<script>
  initMonitor({
    apiBase: 'http://localhost:8080',
    buildings: ['Building1', 'Building2']
  });
</script>
```

### 方式二：Vue.js 组件

详见 [Vue.js 组件集成](#vuejs-组件集成)

---

## API 接口文档

### 基础信息

- **Base URL**: `http://localhost:8080`
- **Content-Type**: `application/json`

### 接口列表

#### 1. 获取监测状态

```
GET /monitor/status
```

**响应：**
```json
{
  "is_running": true,
  "is_paused": false,
  "speed": 60,
  "simulation_time": "2021-07-01T06:00:00",
  "buildings": {
    "total": 14,
    "normal": 12,
    "warning": 1,
    "critical": 1
  },
  "alerts": {
    "total": 5,
    "critical": 2,
    "warning": 3
  }
}
```

---

#### 2. 启动监测

```
POST /monitor/start?speed=60&start_date=2021-07-01
```

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| speed | float | 否 | 时间加速倍率，默认 60 |
| start_date | string | 否 | 起始日期，格式 YYYY-MM-DD |

**响应：**
```json
{
  "status": "started",
  "speed": 60,
  "start_date": "2021-07-01"
}
```

---

#### 3. 停止监测

```
POST /monitor/stop
```

**响应：**
```json
{
  "status": "stopped"
}
```

---

#### 4. 暂停监测

```
POST /monitor/pause
```

**响应：**
```json
{
  "status": "paused",
  "simulation_time": "2021-07-01T06:00:00"
}
```

---

#### 5. 继续监测

```
POST /monitor/resume
```

**响应：**
```json
{
  "status": "resumed"
}
```

---

#### 6. 重置监测

```
POST /monitor/reset
```

**响应：**
```json
{
  "status": "reset"
}
```

---

#### 7. 动态调速

```
POST /monitor/speed?speed=300
```

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| speed | float | 是 | 速度倍率，范围 1-3600 |

**响应：**
```json
{
  "status": "ok",
  "speed": 300
}
```

---

#### 8. 清除告警

```
POST /monitor/clear-alerts
```

**响应：**
```json
{
  "status": "ok",
  "message": "所有告警已清除"
}
```

---

#### 9. 触发异常

```
POST /monitor/trigger-anomaly
```

**请求体：**
```json
{
  "building": "Baikal",
  "type": "electricity_high",
  "intensity": 5
}
```

**参数说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| building | string | 建筑名称，"all" 表示所有建筑 |
| type | string | 异常类型 |
| intensity | int | 异常强度，1-10 |

**异常类型：**

| 值 | 说明 |
|------|------|
| electricity_high | 电耗过高 |
| electricity_low | 电耗过低 |
| temp_high | 温度异常高 |
| temp_low | 温度异常低 |
| cop_low | COP 效率低 |
| random | 随机异常 |

**响应：**
```json
{
  "status": "triggered",
  "building": "Baikal",
  "type": "electricity_high",
  "intensity": 5,
  "triggered_count": 1
}
```

---

#### 10. 获取告警列表

```
GET /monitor/alerts?building_id=Baikal&limit=50
```

**响应：**
```json
{
  "alerts": [
    {
      "id": "Baikal_electricity_2021-07-01T06:00:00",
      "building_id": "Baikal",
      "timestamp": "2021-07-01T06:00:00",
      "field": "electricity_kwh",
      "value": 520.0,
      "level": "critical",
      "message": "[2021-07-01 06:00:00] Baikal electricity_kwh 异常: 520.00",
      "simulated": false
    }
  ]
}
```

---

## WebSocket 消息格式

### 连接地址

```
ws://localhost:8080/ws/monitor
```

### 服务端推送消息

#### 1. 状态更新

```json
{
  "type": "update",
  "is_running": true,
  "is_paused": false,
  "speed": 60,
  "simulation_time": "2021-07-01T06:00:00",
  "buildings": {
    "Baikal": {
      "building_id": "Baikal",
      "status": "normal",
      "last_update": "2021-07-01 06:00:00",
      "current_data": {
        "electricity_kwh": 230.5,
        "water_m3": 0.2,
        "hvac_kwh": 120.3,
        "outdoor_temp": 25.3
      },
      "active_alerts": 0
    }
  }
}
```

#### 2. 告警推送

```json
{
  "type": "alert",
  "data": {
    "id": "Baikal_electricity_2021-07-01T06:00:00",
    "building_id": "Baikal",
    "timestamp": "2021-07-01T06:00:00",
    "field": "electricity_kwh",
    "value": 520.0,
    "level": "critical",
    "message": "[2021-07-01 06:00:00] Baikal electricity_kwh 异常: 520.00",
    "simulated": false
  }
}
```

#### 3. 监测启动通知

```json
{
  "type": "monitoring_started",
  "speed": 60,
  "start_time": "2021-07-01T00:00:00"
}
```

### 客户端发送消息

```javascript
// 心跳
ws.send("ping");

// 请求状态
ws.send("status");
```

---

## 数据格式要求

### 数据库表结构

```sql
CREATE TABLE energy_reports (
    building_id VARCHAR(50) NOT NULL,
    building_type VARCHAR(50),
    timestamp TIMESTAMP NOT NULL,
    electricity_kwh FLOAT,
    water_m3 FLOAT,
    hvac_kwh FLOAT,
    chw_supply_temp FLOAT,
    chw_return_temp FLOAT,
    outdoor_temp FLOAT,
    humidity_pct FLOAT,
    occupancy_density FLOAT,
    meter_id VARCHAR(50),
    system_status VARCHAR(50),
    PRIMARY KEY (building_id, timestamp)
);

CREATE INDEX idx_timestamp ON energy_reports(timestamp);
CREATE INDEX idx_building ON energy_reports(building_id);
```

### 字段说明

| 字段 | 中文名 | 类型 | 单位 | 说明 |
|------|--------|------|------|------|
| building_id | 建筑编号 | VARCHAR | - | 唯一标识 |
| building_type | 建筑类型 | VARCHAR | - | 如：办公楼、商场 |
| timestamp | 时间戳 | TIMESTAMP | - | 数据采集时间 |
| electricity_kwh | 电耗 | FLOAT | kWh | 电力消耗 |
| water_m3 | 水耗 | FLOAT | m³ | 用水量 |
| hvac_kwh | 空调能耗 | FLOAT | kWh | 空调系统耗电 |
| chw_supply_temp | 冷冻水供水温度 | FLOAT | °C | 冷冻水系统参数 |
| chw_return_temp | 冷冻水回水温度 | FLOAT | °C | 冷冻水系统参数 |
| outdoor_temp | 室外温度 | FLOAT | °C | 环境温度 |
| humidity_pct | 湿度 | FLOAT | % | 环境湿度 |
| occupancy_density | 人员密度 | FLOAT | 人/100m² | 建筑内人数 |
| meter_id | 仪表编号 | VARCHAR | - | 采集设备标识 |
| system_status | 系统状态 | VARCHAR | - | 运行状态标识 |

---

## Vue.js 组件集成

### 1. 安装组件

将组件文件复制到项目：

```bash
cp RealTimeMonitor.vue src/components/
```

### 2. 基本使用

```vue
<template>
  <RealTimeMonitor 
    api-base="http://localhost:8080"
    :buildings="['Baikal', 'Aral', 'Caspian']"
  />
</template>

<script setup>
import RealTimeMonitor from '@/components/RealTimeMonitor.vue'
</script>
```

### 3. 全局注册

```javascript
// main.js
import { createApp } from 'vue'
import RealTimeMonitor from '@/components/RealTimeMonitor.vue'

const app = createApp(App)
app.component('RealTimeMonitor', RealTimeMonitor)
app.mount('#app')
```

### 4. Props 配置

| Prop | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| apiBase | String | `http://localhost:8080` | 后端 API 地址 |
| buildings | Array | `['Building1', ...]` | 监测建筑列表 |

### 5. 完整示例

```vue
<template>
  <div class="dashboard-page">
    <h1>能耗监测中心</h1>
    
    <RealTimeMonitor 
      :api-base="config.apiBase"
      :buildings="buildingList"
    />
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import RealTimeMonitor from '@/components/RealTimeMonitor.vue'

const config = reactive({
  apiBase: import.meta.env.VITE_API_BASE || 'http://localhost:8080'
})

const buildingList = ref([
  'Baikal', 'Aral', 'Caspian', 'Huron', 'Erie',
  'Ladoga', 'Superior', 'Titicaca', 'Victoria'
])
</script>
```

---

## 配置说明

### 后端配置

```python
# api_server.py

# 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "building_energy",
    "user": "postgres",
    "password": "your-password"
}

# 监测建筑列表
BUILDINGS = ["Baikal", "Aral", "Caspian", ...]

# 异常检测阈值
THRESHOLDS = {
    "electricity_kwh": {"min": 50, "max": 500, "zscore": 3.0},
    "water_m3": {"min": 0.1, "max": 50, "zscore": 3.0},
    "hvac_kwh": {"min": 10, "max": 300, "zscore": 3.0},
    "chw_supply_temp": {"min": 5, "max": 12, "zscore": 3.0},
    "chw_return_temp": {"min": 10, "max": 18, "zscore": 3.0},
    "outdoor_temp": {"min": -40, "max": 50, "zscore": 3.0}
}
```

### 前端配置

```javascript
// Vue 组件
const config = {
  apiBase: 'http://your-server:8080',
  buildings: ['Building1', 'Building2']
}
```

### 环境变量

```bash
# .env
VITE_API_BASE=http://localhost:8080
```

---

## 注意事项

### 1. 跨域配置

后端需配置 CORS：

```python
# api_server.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

### 2. WebSocket 连接

- 开发环境：`ws://localhost:8080/ws/monitor`
- 生产环境：`wss://your-domain/ws/monitor`

### 3. 性能优化

| 场景 | 建议 |
|------|------|
| 建筑数量 > 50 | 分批加载，使用虚拟滚动 |
| 告警数量 > 1000 | 分页加载，限制前端显示 |
| 高并发 | 使用 Redis 缓存 + 多 Worker |

### 4. 安全建议

| 项目 | 建议 |
|------|------|
| API 认证 | 添加 JWT 或 API Key |
| HTTPS | 生产环境必须启用 |
| 数据库 | 使用连接池，限制查询量 |
| 输入验证 | 验证所有用户输入 |

### 5. 错误处理

```javascript
// 前端错误处理示例
try {
  await fetch(`${apiBase}/monitor/start`)
} catch (error) {
  if (error.name === 'TypeError') {
    console.error('网络错误，请检查后端服务')
  } else {
    console.error('启动失败:', error.message)
  }
}
```

---

## 故障排查

### 1. WebSocket 连接失败

```
检查项：
1. 后端是否启动
2. 端口是否开放
3. 防火墙是否阻止 WebSocket
4. 是否使用正确的协议（ws/wss）
```

### 2. 数据库连接失败

```
检查项：
1. PostgreSQL 服务是否运行
2. 连接参数是否正确
3. 数据库用户是否有权限
4. 表结构是否已创建
```

### 3. 实时数据不更新

```
检查项：
1. WebSocket 是否正常连接
2. 后端监测是否启动
3. 查看后端日志是否有错误
```

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | 2026-03-11 | 初始版本，支持实时监测、告警、异常模拟 |

---

## 联系方式

如有问题，请联系开发团队。