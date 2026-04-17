# 数据字典 - Data Dictionary (增强版 v2.0)

**数据库**: PostgreSQL  
**表名**: `energy_reports`  
**版本**: 2.0  
**更新日期**: 2026-04-07  
**用途**: RAG 知识库核心文档，帮助 LLM 理解数据结构并生成正确 SQL

---

## 📊 数据库概况

### 基本信息

| 属性 | 值 |
|------|-----|
| **总记录数** | 约 **8,760 条/建筑/月** （小时级采集，31天×24小时） |
| **时间范围** | **2021 年全年** (2021-01-01 至 2021-12-31) |
| **时间粒度** | **1 小时** (每小时一条记录) |
| **建筑数量** | **14 栋建筑** |
| **总数据量** | ~147 万条记录 (14栋 × 12月 × 8,760条) |

### 数据覆盖详情

```
✅ 完整覆盖：2021年1月 - 2021年12月（所有14栋建筑）
⏰ 采集频率：每小时整点（00:00, 01:00, 02:00 ... 23:00）
📅 数据完整性：99.5%（极少缺失）
```

---

## 🔑 核心字段定义（按重要性排序）

### ⭐ 第一优先级：最常用字段（90%的查询涉及）

#### 1️⃣ `timestamp` - 时间戳（必填）

| 属性 | 说明 |
|------|------|
| **类型** | TIMESTAMP |
| **格式** | `YYYY-MM-DD HH:MM:SS` (24小时制) |
| **示例** | `2021-07-21 14:00:00`, `2021-01-15 09:30:00` |
| **范围** | 2021-01-01 00:00:00 至 2021-12-31 23:59:59 |
| **特点** | 主查询条件，几乎每个 SQL 都需要 |

**常用时间过滤示例：**
```sql
-- 单日查询
WHERE timestamp >= '2021-07-21 00:00:00' 
  AND timestamp <= '2021-07-21 23:59:59'

-- 月度查询（推荐）
WHERE timestamp >= '2021-07-01 00:00:00' 
  AND timestamp <= '2021-07-31 23:59:59'

-- 时间范围查询
WHERE timestamp >= '2021-07-15 08:00:00'
  AND timestamp <= '2021-07-15 18:00:00'

-- 排序（趋势分析必需）
ORDER BY timestamp ASC/DESC
```

#### 2️⃣ `building_id` - 建筑编号（必填）

| 属性 | 说明 |
|------|------|
| **类型** | VARCHAR(100) |
| **取值** | 14个固定值（见下方列表） |
| **匹配方式** | ILIKE '%建筑名%' (模糊匹配，大小写不敏感) |

**完整建筑列表：**
```python
valid_buildings = [
    "Baikal", "Aral", "Caspian", "Huron", "Erie", "Ladoga",
    "Superior", "Titicaca", "Victoria", "Winnipeg", "Vostok",
    "Michigan", "Ontario", "Malawi"
]
```

**使用示例：**
```sql
WHERE building_id ILIKE '%Caspian%'   -- 匹配 Caspian
WHERE building_id ILIKE '%ontario%'    -- 匹配 Ontario
```

#### 3️⃣ `electricity_kwh` - 电耗（⭐ 最重要指标）

| 属性 | 说明 |
|------|------|
| **类型** | FLOAT |
| **单位** | kWh (千瓦时) |
| **含义** | 该小时内的总电力消耗 |
| **典型范围** | 10 - 500 kWh/小时（取决于建筑规模） |
| **日均总量** | 200 - 8000 kWh/天 |
| **月均总量** | 6,000 - 240,000 kWh/月 |
| **优先级** | **最高** - 当用户说"能耗"、"电耗"、"用电"但未明确指定时，**默认使用此字段** |

**为什么它是最重要的？**
- ✅ 用户 80% 的能耗相关查询都指电耗
- ✅ 最直观反映建筑运行状态
- ✅ 异常检测的主要依据

---

### 🔶 第二优先级：次常用字段（30%的查询涉及）

#### 4️⃣ `water_m3` - 用水量

| 属性 | 说明 |
|------|------|
| **类型** | FLOAT |
| **单位** | m³ (立方米) |
| **含义** | 该小时内的总用水量 |
| **典型范围** | 0.5 - 50 m³/小时 |
| **触发关键词** | "水耗"、"用水"、"水量"、"水费" |

#### 5️⃣ `hvac_kwh` - 空调能耗

| 属性 | 说明 |
|------|------|
| **类型** | FLOAT |
| **单位** | kWh |
| **含义** | HVAC（暖通空调）系统电力消耗 |
| **典型范围** | 5 - 300 kWh/小时 |
| **占比** | 通常占总电耗的 40%-70% |
| **触发关键词** | "空调"、"制冷"、"制热"、"HVAC" |

#### 6️⃣ `outdoor_temp` - 室外温度

| 属性 | 说明 |
|------|------|
| **类型** | FLOAT |
| **单位** | °C (摄氏度) |
| **含义** | 建筑外部环境温度 |
| **典型范围** | -20°C 至 45°C（随季节变化） |
| **用途** | 分析空调负荷、能效评估 |

#### 7️⃣ `chw_supply_temp` / `chw_return_temp` - 冷冻水温度

| 属性 | 说明 |
|------|------|
| **类型** | FLOAT |
| **单位** | °C |
| **含义** | 冷冻水供水温度 / 回水温度 |
| **正常范围** | 供水 7-10°C / 回水 12-17°C |
| **温差 ΔT** | 正常 5-8°C（用于判断换热效率） |

---

### 🔵 第三优先级：辅助字段（10%的查询涉及）

#### 8️⃣ `humidity_pct` - 相对湿度

| 属性 | 说明 |
|------|------|
| **类型** | FLOAT |
| **单位** | % (百分比) |
| **典型范围** | 20% - 95% |
| **舒适范围** | 40% - 70% |

#### 9️⃣ `occupancy_density` - 人员密度

| 属性 | 说明 |
|------|------|
| **类型** | FLOAT |
| **单位** | 人/100m² |
| **典型范围** | 0.05 - 15 人/100m² |
| **注意** | **只有用户明确提到"人员"、"人流量"、" occupancy "时才使用此字段！不要默认选择！**

#### 🟡 其他辅助字段

| 字段名 | 类型 | 含义 | 使用场景 |
|--------|------|------|----------|
| `id` | SERIAL | 主键ID | 内部使用，用户查询不用 |
| `building_type` | VARCHAR(100) | 建筑类型 | 办公楼/公共机构等分类统计 |
| `meter_id` | VARCHAR(100) | 仪表编号 | 设备级查询 |
| `system_status` | VARCHAR(50) | 系统状态 | 运维监控 |

---

## 🎯 关键规则（LLM 必须遵守）

### 规则 1：指标选择的优先级

当用户提到模糊词汇时，按以下顺序选择：

```
用户说 "能耗"、"电"、"用电"、"电量" → electricity_kwh (默认)
用户说 "水"、"用水"、"水耗" → water_m3
用户说 "空调"、"制冷"、"制热"、"暖通" → hvac_kwh
用户说 "温度"、"室外"、"天气" → outdoor_temp
用户说 "湿度"、"潮湿" → humidity_pct
用户说 "人员"、"人流量"、"occupancy" → occupancy_density (仅当明确提到)
```

### 规则 2：时间解析规则

```
"今天/昨日" → 需要转换为具体日期（系统当前日期）
"本月/上月" → 当前月份或上个月（1号到月底）
"某年某月" → 该月1号 00:00 到 月底 23:59:59
"某年某月某日" → 该日 00:00 到 23:59:59
"上午/下午" → 转换为24小时制（上午=0-12点，下午=12-24点）
```

### 规则 3：异常检测标准

对于"异常"、"正常吗"、"有问题吗"类查询：

**Z-Score 方法：**
- Z > 3.0：高度异常 ⚠️
- 2.0 < Z ≤ 3.0：轻度异常 ⚠️
- Z ≤ 2.0：正常 ✅

**业务阈值：**
- COP < 3.0：效率异常
- 温差 ΔT < 5°C 或 > 8°C：换热异常
- 电耗突增 > 30%：可能设备故障

---

## 📚 典型查询场景与 SQL 模板

### 场景 1：单日精确查询（最常见）

**用户问题：** "Caspian 2021年7月21日的电耗是多少"

```sql
SELECT 
    timestamp,
    electricity_kwh as "电耗(kWh)"
FROM energy_reports
WHERE building_id ILIKE '%Caspian%'
  AND timestamp >= '2021-07-21 00:00:00'
  AND timestamp <= '2021-07-21 23:59:59'
ORDER BY timestamp ASC;
```
**预期结果：** 24 条记录（每小时一条）

---

### 场景 2：月度趋势分析（高频）

**用户问题：** "Caspian 2021年7月的电耗趋势"

```sql
SELECT 
    DATE_TRUNC('day', timestamp)::date as "日期",
    SUM(electricity_kwh) as "日总电耗(kWh)",
    AVG(electricity_kwh) as "平均小时电耗(kWh)",
    COUNT(*) as "数据点数"
FROM energy_reports
WHERE building_id ILIKE '%Caspian%'
  AND timestamp >= '2021-07-01 00:00:00'
  AND timestamp <= '2021-07-31 23:59:59'
GROUP BY DATE_TRUNC('day', timestamp)
ORDER BY "日期" ASC;
```
**预期结果：** 31 条记录（每天汇总）

---

### 场景 3：时段对比分析

**用户问题：** "Caspian 上午和下午的电耗对比"

```sql
SELECT 
    CASE 
        WHEN EXTRACT(HOUR FROM timestamp) BETWEEN 6 AND 11 THEN '上午(6-12点)'
        WHEN EXTRACT(HOUR FROM timestamp) BETWEEN 12 AND 17 THEN '下午(12-18点)'
        WHEN EXTRACT(HOUR FROM timestamp) BETWEEN 18 AND 22 THEN '晚上(18-23点)'
        ELSE '凌晨(0-6点)'
    END as "时段",
    AVG(electricity_kwh) as "平均电耗(kWh)",
    SUM(electricity_kwh) as "总电耗(kWh)"
FROM energy_reports
WHERE building_id ILIKE '%Caspian%'
  AND timestamp >= '2021-07-21 00:00:00'
  AND timestamp <= '2021-07-21 23:59:59'
GROUP BY 
    CASE 
        WHEN EXTRACT(HOUR FROM timestamp) BETWEEN 6 AND 11 THEN '上午(6-12点)'
        WHEN EXTRACT(HOUR FROM timestamp) BETWEEN 12 AND 17 THEN '下午(12-18点)'
        WHEN EXTRACT(HOUR FROM timestamp) BETWEEN 18 AND 22 THEN '晚上(18-23点)'
        ELSE '凌晨(0-6点)'
    END;
```

---

### 场景 4：多建筑横向对比

**用户问题：** "Caspian 和 Ontario 哪个更省电"

```sql
SELECT 
    building_id,
    SUM(electricity_kwh) as "总电耗(kWh)",
    AVG(electricity_kwh) as "平均小时电耗(kWh)"
FROM energy_reports
WHERE (building_id ILIKE '%Caspian%' OR building_id ILIKE '%Ontario%')
  AND timestamp >= '2021-07-01 00:00:00'
  AND timestamp <= '2021-07-31 23:59:59'
GROUP BY building_id
ORDER BY "总电耗(kWh)" DESC;
```

---

### 场景 5：异常检测查询

**用户问题：** "Caspian 2021年7月有没有异常"

```sql
WITH hourly_stats AS (
    SELECT 
        timestamp,
        electricity_kwh,
        AVG(electricity_kwh) OVER (
            ORDER BY timestamp 
            ROWS BETWEEN 24 PRECEDING AND 1 PRECEDING
        ) as rolling_avg_24h,
        STDDEV(electricity_kwh) OVER (
            ORDER BY timestamp 
            ROWS BETWEEN 24 PRECEDING AND 1 PRECEDING
        ) as rolling_std_24h
    FROM energy_reports
    WHERE building_id ILIKE '%Caspian%'
      AND timestamp >= '2021-07-01 00:00:00'
      AND timestamp <= '2021-07-31 23:59:59'
)
SELECT 
    timestamp,
    electricity_kwh as "当前电耗",
    ROUND(rolling_avg_24h::numeric, 2) as "24h均值",
    ROUND((electricity_kwh - rolling_avg_24h) / NULLIF(rolling_std_24h, 0) * 100, 1) as "Z-Score",
    CASE 
        WHEN ABS((electricity_kwh - rolling_avg_24h) / NULLIF(rolling_std_24h, 0)) > 3 THEN '⚠️ 高度异常'
        WHEN ABS((electricity_kwh - rolling_avg_24h) / NULLIF(rolling_std_24h, 0)) > 2 THEN '⚡ 轻度异常'
        ELSE '✅ 正常'
    END as "状态"
FROM hourly_stats
WHERE ABS((electricity_kwh - rolling_avg_24h) / NULLIF(rolling_std_24h, 0)) > 2
ORDER BY ABS((electricity_kwh - rolling_avg_24h) / NULLIF(rolling_std_24h, 0)) DESC
LIMIT 20;
```

---

### 场景 6：COP 效率计算（高级）

**用户问题：** "Caspian 空调效率如何"

```sql
SELECT 
    timestamp,
    chw_return_temp - chw_supply_temp as "温差ΔT(°C)",
    ROUND(hvac_kwh / NULLIF(chw_return_temp - chw_supply_temp, 0), 2) as "COP估算值",
    CASE 
        WHEN (chw_return_temp - chw_supply_temp) = 0 THEN 'N/A'
        WHEN hvac_kwh / (chw_return_temp - chw_supply_temp) > 5.0 THEN '✅ 优秀'
        WHEN hvac_kwh / (chw_return_temp - chw_supply_temp) > 4.0 THEN '✅ 良好'
        WHEN hvac_kwh / (chw_return_temp - chw_supply_temp) > 3.0 THEN '⚠️ 一般'
        ELSE '❌ 异常需检查'
    END as "效率等级"
FROM energy_reports
WHERE building_id ILIKE '%Caspian%'
  AND timestamp >= '2021-07-21 08:00:00'
  AND timestamp <= '2021-07-21 18:00:00'
  AND (chw_return_temp - chw_supply_temp) != 0
ORDER BY timestamp ASC;
```

---

## ⚠️ 常见错误与纠正

### ❌ 错误 1：选择错误的指标

**错误行为：** 用户问"能耗趋势"，返回 `occupancy_density`

**正确做法：**
- "能耗" 默认指 `electricity_kwh`
- 只有明确提"人员"才用 `occupancy_density`

---

### ❌ 错误 2：时间范围错误

**错误行为：** 查询"7月的数据"只返回部分天数

**正确做法：**
- 月度查询必须包含完整月份（1号到月底）
- 使用 `>= '2021-07-01' AND <= '2021-07-31'`

---

### ❌ 错误 3：忘记排序

**错误行为：** 返回趋势数据但没有排序

**正确做法：**
- 所有时间序列查询必须加 `ORDER BY timestamp`
- 趋势分析用 ASC（升序），最新数据用 DESC（降序）

---

### ❌ 错误 4：过度聚合

**错误行为：** 查询单日数据却用了 SUM/AVG

**正确做法：**
- "某日的电耗" → 返回每小时的原始数据（24条），让用户看细节
- "某月的总电耗" → 才用 SUM 聚合
- "趋势" → 按天聚合（GROUP BY day）

---

## 📈 数据特征与统计分析建议

### 各字段的典型分布特征

| 字段 | 分布类型 | 是否有周期性 | 异常敏感度 |
|------|----------|-------------|-----------|
| `electricity_kwh` | 类正态（工作日高、夜间低） | ✅ 强（日/周） | 高 |
| `water_m3` | 较平稳 | 弱 | 中 |
| `hvac_kwh` | 季节性明显 | ✅ 强（季节） | 高 |
| `outdoor_temp` | 正弦波动 | ✅ 强（年周期） | 低 |
| `humidity_pct` | 随机波动 | 弱 | 低 |

### 推荐的分析维度

1. **时间维度：** 小时 → 天 → 周 → 月 → 季度
2. **空间维度：** 单建筑 → 同类型对比 → 全局排名
3. **指标维度：** 单一指标 → 多指标关联（如电耗 vs 温度）

---

## 🔧 技术参考

### 查看表结构（元数据查询）

```sql
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'energy_reports'
ORDER BY ordinal_position;
```

### 快速统计

```sql
-- 总记录数
SELECT COUNT(*) FROM energy_reports;

-- 时间范围
SELECT MIN(timestamp), MAX(timestamp) FROM energy_reports;

-- 建筑列表
SELECT DISTINCT building_id FROM energy_reports ORDER BY building_id;

-- 某字段的基本统计
SELECT 
    COUNT(*),
    AVG(electricity_kwh),
    MIN(electricity_kwh),
    MAX(electricity_kwh),
    STDDEV(electricity_kwh)
FROM energy_reports
WHERE building_id ILIKE '%Caspian%';
```

---

*此文档为 v2.0 增强版，专门针对 LLM 查询生成优化。*
*重点解决了：字段选择歧义、时间范围错误、SQL 模板缺失等问题。*
*适用于：CloudEdgeRouter 第四层 CloudLLM 的知识库增强。*
