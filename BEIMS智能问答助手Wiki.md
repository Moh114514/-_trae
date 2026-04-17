# BEIMS 智能问答助手 - 完整Wiki文档

## 📋 目录

1. [项目概述](#1-项目概述)
2. [核心组件](#2-核心组件)
3. [系统架构](#3-系统架构)
4. [云边协同路由](#4-云边协同路由)
5. [前端交互系统](#5-前端交互系统)
6. [实时监测服务](#6-实时监测服务)
7. [API接口文档](#7-api接口文档)
8. [部署与运行](#8-部署与运行)
9. [常见问题与故障排除](#9-常见问题与故障排除)

---

## 1. 项目概述

### 1.1 项目简介

BEIMS智能问答助手是一个基于自然语言处理的建筑能源管理智能问答系统，旨在通过对话式界面让非技术人员也能便捷地查询和分析建筑能耗数据。

**版本**: v2.3-with-clarification  
**最后更新**: 2026-04-16

### 1.2 核心功能

| 功能类别 | 具体能力 | 用户价值 |
|---------|---------|---------|
| **数据查询** | 自然语言查询能耗数据 | 无需SQL，降低使用门槛 |
| **知识库检索** | 设备故障排查、操作指南 | 快速获取运维知识 |
| **智能分析** | 异常检测、趋势分析、节能建议 | 数据驱动的决策支持 |
| **交互体验** | 打字机效果、停止按钮、澄清引导 | 类ChatGPT的流畅体验 |
| **实时监测** | 模拟实时数据流、异常告警 | 实时监控建筑能耗状态 |

### 1.3 技术特色

✅ **4层云边协同路由**: 从规则到LLM的渐进式处理，平衡速度与智能  
✅ **混合存储方案**: PostgreSQL(结构化) + ChromaDB(向量) + Ollama(本地推理)  
✅ **前端智能化**: 自适应打字机、截断停止、智能澄清  
✅ **容错降级机制**: 本地失败自动切换云端，确保服务可用性  
✅ **实时监测**: WebSocket推送、模拟数据、异常检测

---

## 2. 核心组件

### 2.1 核心文件列表

| 文件 | 功能 | 位置 | 代码量 |
|------|------|------|--------|
| [`api_server.py`](file:///workspace/api_server.py) | FastAPI应用主入口，提供API接口 | /workspace/ | ~1000行 |
| [`cloud_edge_router.py`](file:///workspace/cloud_edge_router.py) | 核心路由引擎，实现4层云边协同路由 | /workspace/ | ~1400行 |
| [`energy_agent.py`](file:///workspace/energy_agent.py) | 建筑能源管理AI Agent | /workspace/ | ~400行 |
| [`energy_analyzer.py`](file:///workspace/energy_analyzer.py) | 建筑能耗分析引擎 | /workspace/ | ~500行 |
| [`realtime_monitor.py`](file:///workspace/realtime_monitor.py) | 实时监测服务 | /workspace/ | ~600行 |
| [`ai-chat-widget.js`](file:///workspace/BEIMS建筑能源智能管理系统/frontend/dist/resources/scripts/ai-chat-widget.js) | 前端聊天组件 | /workspace/BEIMS建筑能源智能管理系统/frontend/dist/resources/scripts/ | ~720行 |

### 2.2 主要数据模型

#### ChatRequest
```python
class ChatRequest(BaseModel):
    message: str
    building_id: Optional[str] = None
    clear_history: Optional[bool] = False  # 是否清空历史
    history: Optional[List[Dict[str, str]]] = None  # 完整对话历史
    session_id: Optional[str] = None  # 会话标识
```

#### ChatResponse
```python
class ChatResponse(BaseModel):
    response: str
    context: Optional[Dict] = None  # 返回当前上下文
    history: Optional[List[Dict[str, str]]] = None  # 返回更新后的完整历史
```

#### RouteResult
```python
@dataclass
class RouteResult:
    layer: RouteLayer
    action: str                      # 执行动作
    confidence: float = 1.0          # 置信度
    data: Dict[str, Any] = field(default_factory=dict)  # 附加数据
    response: str = ""               # 直接返回的响应（硬规则层）
    need_cloud: bool = False         # 是否需要云端处理
    sql: str = ""                    # 生成的 SQL（如果有）
    params: Dict[str, Any] = field(default_factory=dict)  # 提取的参数
```

---

## 3. 系统架构

### 3.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      用户浏览器 (Frontend)                    │
│  ┌──────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │ 浮动按钮  │→ │ 聊天窗口UI   │→ │ 打字机/停止/澄清    │   │
│  └──────────┘  └──────────────┘  └─────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP POST /chat (JSON)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   API Server (FastAPI :8082)                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              CloudEdgeRouter (路由分发器)               │   │
│  │                                                      │   │
│  │  Layer 0: 知识库检测 → ChromaDB向量检索                │   │
│  │  Layer 1: 静态规则 → 正则匹配 (ms级响应)             │   │
│  │  Layer 2: 语义路由 → Embedding相似度                   │   │
│  │  Layer 3: 本地推理 → Ollama qwen2.5:7b               │   │
│  │  Layer 4: 云端增强 → 通义千问(qwen-plus)              │   │
│  │                                                      │   │
│  │  FailSafeGuard: 自动降级 + 熔断保护                  │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
┌─────────────────┐ ┌─────────────┐ ┌──────────────────┐
│ PostgreSQL      │ │ ChromaDB    │ │ Ollama/Cloud LLM │
│ (结构化数据)    │ │ (1649文档)  │ │ (语义理解/生成)   │
│ • energy_reports│ │ • 运维知识  │ │ • 意图解析        │
│ • 8760条/年/建筑│ │ • 操作手册  │ │ • SQL生成         │
└─────────────────┘ └─────────────┘ └──────────────────┘
```

### 3.2 服务部署拓扑

```
Port 8081: Frontend (HTTP Static Server)
  ↓ 提供静态HTML/JS/CSS文件
  
Port 8082: Backend API (FastAPI + Uvicorn)
  ↓ RESTful API: /chat, /router/status, /buildings/{id}/summary
  
Port 11434: Local LLM (Ollama)
  ↓ 运行 qwen2.5:7b 模型 (7B参数量)
  
Local Files:
  - cloud_edge_router.py (核心路由逻辑, ~1400行)
  - api_server.py (API接口层, ~1000行)
  - ai-chat-widget.js (前端组件, ~720行)
```

---

## 4. 云边协同路由

### 4.1 设计理念

**核心思想**: 不是所有问题都需要AI，简单问题应该毫秒级响应。

```
用户输入: "Caspian 2021年7月21日的电耗"
        ↓
Layer 0: 包含知识库关键词? ❌ 
        ↓
Layer 1: 匹配正则 date_query ✅ → 直接执行SQL (耗时<50ms)
        ↓
返回: 24条电耗数据 (无需调用任何LLM)

对比: 如果所有请求都走LLM → 单次查询需要2-5秒
```

### 4.2 各层职责与性能特征

| 层级 | 名称 | 处理方式 | 响应时间 | 适用场景 | 示例 |
|------|------|---------|---------|---------|------|
| **Layer 0** | 知识库优先 | ChromaDB向量检索 | 100-300ms | 故障/操作/概念类 | "空调外机坏了怎么办" |
| **Layer 1** | 静态规则 | Python正则匹配 | **1-10ms** ⚡ | 结构化数据查询 | "XX建筑YY日的电耗" |
| **Layer 2** | 语义路由 | Sentence-BERT嵌入 | 200-500ms | 模糊意图匹配 | "帮我看看用电情况" |
| **Layer 3** | 本地推理 | Ollama qwen2.5:7b | 1-3s | 复杂SQL生成+分析 | "为什么上周能耗异常?" |
| **Layer 4** | 云端增强 | 通义千问API | 3-8s | 高级分析和长文本 | "生成年度节能报告" |

### 4.3 路由流程伪代码

```python
def route(query):
    # Layer 0: 知识库检测 (最高优先级)
    if is_knowledge_query(query):
        return handle_knowledge(query)  # 向量检索
    
    # Layer 1: 静态规则匹配
    rule_result = static_rule.match(query)
    if rule_result:
        if rule_result.action == "clarification_needed":
            return generate_clarification()  # 新增: 智能澄清
        if rule_result.action == "query_data":
            return execute_sql(rule_result.params)  # 直接查数据库
    
    # Layer 2: 语义路由
    semantic_result = semantic_router.route(query)
    if semantic_result.confidence >= 0.75:
        return handle_semantic(semantic_result)
    
    # Layer 3: 本地LLM推理
    local_result = local_slm.process(query)
    
    # 降级检查: 本地结果是否有效?
    if not is_valid(local_result):
        # Layer 4: 降级到云端
        if cloud_available:
            return handle_cloud(local_result)
    
    # 使用本地最佳结果
    return handle_local(local_result)
```

### 4.4 FailSafeGuard 容错机制

```python
class FailSafeGuard:
    def __init__(self):
        self.cloud_available = True
        self.failure_count = 0
        self.last_failure_time = None
        self.circuit_breaker_threshold = 3  # 连续失败3次触发熔断
        self.recovery_timeout = 60  # 60秒后尝试恢复
    
    def check_cloud_health(self):
        """检查云端可用性"""
        if self.failure_count >= self.circuit_breaker_threshold:
            if time.now() - self.last_failure_time < self.recovery_timeout:
                return False  # 熔断中
        return True
    
    def on_cloud_failure(self):
        """云端失败回调"""
        self.failure_count += 1
        self.last_failure_time = time.now()
```

**熔断保护**: 当云端连续失败3次，自动进入60秒冷却期，避免无效重试浪费资源。

### 4.5 智能澄清机制

#### 业务背景

**问题场景**:
```
用户输入: "Ontario"
期望行为: 友好提示 "您想了解 Ontario 的什么信息?"
实际行为(修复前): 返回8760条人员密度数据 (错误!)
```

**根本原因**: `simple_query` 模式过于宽松，只提取建筑名就执行全表查询

#### 检测算法

```python
def _needs_clarification(self, pattern_name, params, query):
    """
    三层检测逻辑
    """
    
    if pattern_name == "simple_query":
        building = params.get("building", "")
        metric = params.get("metric")
        query_length = len(query.strip())
        
        # 场景A: 纯建筑名 (≤15字符)
        has_date_info = any(kw in query for kw in [
            "年", "月", "日", "今天", "昨天", "最近"
        ])
        
        if query_length <= 15 and building and not metric and not has_date_info:
            return True  # ← "Ontario", "Caspian"
        
        # 场景B: 模糊查询 (≤20字符)
        vague_keywords = ["数据", "情况", "信息", "详情"]
        has_vague = any(kw in query for kw in vague_keywords)
        
        if query_length <= 20 and building and has_vague and not metric:
            return True  # ← "Caspian的数据", "Baikal情况"
    
    return False
```

---

## 5. 前端交互系统

### 5.1 架构设计模式

采用 **IIFE (Immediately Invoked Function Expression)** 模式:

```javascript
(function() {
  'use strict';
  
  // 私有状态变量
  var isOpen = false;
  var isLoading = false;
  var currentTypewriter = null;  // 打字机控制对象
  var currentAbortController = null; // HTTP请求控制
  
  // 公共API
  window.AIChat = {
    sendMessage: sendMessage,
    stopResponse: stopResponse,
    // ...
  };
  
  // 初始化
  init();
})();
```

**优势**:
- 全局命名空间污染最小 (`window.AIChat` 仅暴露必要方法)
- 封装私有状态，避免外部篡改
- 可直接嵌入任何页面 (无需框架依赖)

### 5.2 打字机效果引擎 (typeWriter)

#### 核心算法

```javascript
function typeWriter(element, htmlContent) {
  var textContent = extractText(htmlContent);
  var MAX_TYPING_LENGTH = 2000;
  
  // 🔥 关键决策: 长度自适应策略
  if (textContent.length > MAX_TYPING_LENGTH) {
    // 超长文本: 直接淡入 (<1秒)
    element.style.opacity = '0';
    element.innerHTML = htmlContent;
    requestAnimationFrame(() => element.style.opacity = '1');
    return { cancel: () => {} };
  }
  
  // 正常文本: 逐字打字
  var charIndex = 0;
  var speed = calculateAdaptiveSpeed(textContent.length);
  // 1ms (短文本) ~ 20ms (中等长度)
  
  function type() {
    if (isStopped) return;  // 截断标志检查
    
    if (charIndex < textContent.length) {
      element.innerHTML = escapeHtml(textContent.substring(0, ++charIndex));
      setTimeout(type, speed);  // 递归调度
    } else {
      onComplete();  // 打字完成回调
    }
  }
  
  setTimeout(type, 100);  // 启动延迟
  
  return {
    cancel: () => { charIndex = textContent.length; },  // 完整显示
    truncate: () => { isStopped = true; }  // 截断显示
  };
}
```

#### 速度自适应算法

```javascript
function calculateAdaptiveSpeed(textLength) {
  if (textLength <= 500)  return 1;    // 短文本: 1ms/字 (快速)
  if (textLength <= 1000) return 20;   // 中等: 20ms/字 (适中)
  return 15;                             // 较长: 15ms/字 (略快)
}
```

### 5.3 停止按钮机制 (truncate mode)

#### 双模式设计

```javascript
// 模式1: cancel() - 完整显示 (用于"跳过等待")
cancel: function() {
  charIndex = textContent.length;  // 强制跳到末尾
  element.innerHTML = fullHtmlContent;  // 显示全部内容
},

// 模式2: truncate() - 截断显示 (用于"停止输出") ⭐
truncate: function() {
  isStopped = true;  // 设置停止标志
  element.classList.remove('typing-cursor');
  // 当前已显示的内容就是最终内容!
}
```

---

## 6. 实时监测服务

### 6.1 功能概述

实时监测服务提供以下功能：
- 模拟实时数据流（从历史数据）
- 实时异常检测
- WebSocket 推送告警
- 模拟异常触发

### 6.2 核心数据模型

#### Alert（告警）
```python
@dataclass
class Alert:
    id: str
    building_id: str
    timestamp: str
    field: str
    value: float
    threshold: dict
    level: AlertLevel
    message: str
    simulated: bool = False  # 是否为模拟异常
```

#### BuildingStatus（建筑状态）
```python
@dataclass
class BuildingStatus:
    building_id: str
    status: str  # "normal", "warning", "critical"
    last_update: str
    current_data: dict
    active_alerts: int
```

### 6.3 监测阈值配置

```python
THRESHOLDS = {
    "electricity_kwh": {"min": 50, "max": 500, "zscore": 3.0},
    "water_m3": {"min": 0.1, "max": 50, "zscore": 3.0},
    "hvac_kwh": {"min": 10, "max": 300, "zscore": 3.0},
    "chw_supply_temp": {"min": 5, "max": 12, "zscore": 3.0},
    "chw_return_temp": {"min": 10, "max": 18, "zscore": 3.0},
    "outdoor_temp": {"min": -40, "max": 50, "zscore": 3.0},
}
```

---

## 7. API接口文档

### 7.1 聊天接口

#### POST /chat
智能对话接口 - 云边协同路由

**请求参数**:
```json
{
  "message": "Caspian 2021年7月21日的电耗",
  "building_id": null,
  "clear_history": false,
  "history": [],
  "session_id": null
}
```

**响应参数**:
```json
{
  "response": "电耗查询结果：...",
  "context": {
    "last_building": "Caspian",
    "last_date": "2021-07-21",
    "layer": "static_rule",
    "history_count": 1
  },
  "history": [...]
}
```

#### POST /chat/clear
清空对话历史

**响应**:
```json
{
  "status": "ok",
  "message": "对话历史已清空"
}
```

### 7.2 建筑信息接口

#### GET /buildings
获取可查询的建筑列表

**响应**:
```json
{
  "buildings": ["Baikal", "Aral", "Caspian", ...],
  "count": 14
}
```

#### GET /buildings/{building_id}/summary
获取建筑能耗汇总

#### GET /buildings/{building_id}/cop
分析建筑COP效率

#### GET /buildings/{building_id}/anomalies
检测建筑能耗异常

### 7.3 路由状态接口

#### GET /router/status
获取路由分发器状态

### 7.4 实时监测接口

#### WebSocket /ws/monitor
WebSocket实时监测推送

#### GET /monitor/status
获取监测状态

#### GET /monitor/alerts
获取告警列表

#### POST /monitor/start
启动监测

#### POST /monitor/stop
停止监测

#### POST /monitor/pause
暂停监测

#### POST /monitor/resume
继续监测

#### POST /monitor/reset
重置监测

#### POST /monitor/speed
动态调整速度

---

## 8. 部署与运行

### 8.1 环境要求

- **Python**: 3.8+
- **Node.js**: 16+（如需构建前端）
- **PostgreSQL**: 12+（或SQLite用于开发测试）
- **Ollama**: 本地LLM运行时（可选，用于Layer 3）
- **GPU**: 推荐（用于运行7B模型，≥8GB VRAM）

### 8.2 快速启动

#### 使用启动脚本

Windows系统使用提供的批处理脚本：

```bash
# 启动所有服务
启动所有服务.bat

# 或启动前后端穿透
启动穿透_前后端.bat

# 或启动Cloudflare隧道
start-cloudflare-tunnel.bat
```

#### 手动启动

**1. 启动后端API服务器**

```bash
cd /workspace
python api_server.py
```

后端将在 http://localhost:8082 启动

**2. 启动前端服务器**

```bash
cd /workspace/BEIMS建筑能源智能管理系统/frontend
# 使用任何HTTP服务器，例如：
python -m http.server 8081
```

前端将在 http://localhost:8081 启动

**3. 启动Ollama（可选，用于本地推理）**

```bash
# 拉取模型
ollama pull qwen2.5:7b

# 启动服务
ollama serve
```

### 8.3 配置文件

#### 数据库配置

在 `api_server.py` 中配置：

```python
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "building_energy",
    "user": "postgres",
    "password": "416417"
}
```

#### 云端API配置

在 `cloud_edge_router.py` 和 `api_server.py` 中配置：

```python
CLOUD_API_KEY = "your-api-key"
CLOUD_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
CLOUD_MODEL = "qwen-plus"
```

#### Ollama配置

```python
OLLAMA_URL = "http://localhost:11434/api/generate"
LOCAL_MODEL = "qwen2.5:7b"
```

---

## 9. 常见问题与故障排除

### 9.1 浮窗不显示

**问题**: 访问前端后右下角没有AI按钮

**解决方案**:
1. 检查浏览器控制台 (F12) 是否有JavaScript错误
2. 确认 `ai-chat-widget.js` 文件已正确加载
3. 检查HTML中是否正确引入了脚本

### 9.2 聊天无响应

**问题**: 发送消息后没有回复

**解决方案**:
1. 检查后端API是否正常运行 (访问 http://localhost:8082/docs)
2. 查看后端日志了解具体错误
3. 确认数据库连接正常
4. 如果使用云端模型，检查API Key是否正确

### 9.3 本地模型不可用

**问题**: Ollama模型无法加载或响应慢

**解决方案**:
1. 确认Ollama服务正在运行
2. 检查是否有足够的GPU/内存资源
3. 考虑使用更小的模型（如 qwen2.5:3b）
4. 系统会自动降级到云端模型

### 9.4 数据库连接失败

**问题**: 无法连接到PostgreSQL数据库

**解决方案**:
1. 确认PostgreSQL服务正在运行
2. 检查数据库配置参数（主机、端口、用户名、密码）
3. 确认数据库 `building_energy` 已创建
4. 检查防火墙设置

### 9.5 数据量异常（8760 vs 24）

**问题**: 查询单日数据返回全年数据

**根因**: 正则匹配到错误的模式

**解决方案**: 系统已内置三重防护：
1. 最佳匹配算法（选参数最多的模式）
2. 澄清机制（拦截纯建筑名查询）
3. 调试日志（可定位问题）

---

## 附录

### A. 可查询建筑列表

系统支持以下14个建筑：
- Baikal
- Aral
- Caspian
- Huron
- Erie
- Ladoga
- Superior
- Titicaca
- Victoria
- Winnipeg
- Vostok
- Michigan
- Ontario
- Malawi

### B. 相关文档

- [TECHNICAL_REPORT.md](file:///workspace/TECHNICAL_REPORT.md) - 详细技术报告
- [TEST_CASES.md](file:///workspace/TEST_CASES.md) - 测试用例
- [README_WIDGET.md](file:///workspace/README_WIDGET.md) - 组件说明

---

**文档维护者**: AI Assistant  
**最后更新**: 2026-04-17  
**版本**: v2.3