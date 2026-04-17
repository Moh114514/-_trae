"""
建筑能源管理系统 - FastAPI 后端 v2

提供 REST API 接口：
- POST /chat - 智能对话接口（本地模型 + 云端模型 + 知识库 + 上下文记忆）
- POST /query - 数据查询接口
- GET /export - 报表导出接口
- WebSocket /ws/monitor - 实时监测推送
"""

import os
import sys
import json
import re
import asyncio
import requests
import chromadb
import psycopg2
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# 设置编码
sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(r'E:\openclaw-project\workspace\Fuwu')
from energy_analyzer import EnergyAnalyzer
from realtime_monitor import RealTimeMonitor
from cloud_edge_router import CloudEdgeRouter
import cloud_edge_router

print(f"[STARTUP] CloudEdgeRouter version: {cloud_edge_router.__doc__[:50] if cloud_edge_router.__doc__ else 'unknown'}")

# DEBUG: Test regex patterns at startup
import re
test_query = 'Caspian 2021年7月21日的电耗'
print(f"[REGEX-TEST] Testing: {test_query}")
date_pattern = r'^([A-Za-z]+)\s*(\d{4})[年\-](\d{1,2})[月\-](\d{1,2})日?'
m = re.search(date_pattern, test_query, re.IGNORECASE)
if m:
    print(f"[REGEX-TEST] ✅ date_query MATCH: {m.groups()}")
else:
    print(f"[REGEX-TEST] ❌ date_query NO MATCH!")

# DEBUG: Check StaticRuleEngine patterns
from cloud_edge_router import StaticRuleEngine
test_engine = StaticRuleEngine()
print(f"[PATTERN-CHECK] date_query pattern: {test_engine.DATA_QUERY_PATTERNS[3]['pattern'][:60]}...")
if r'\s*' in test_engine.DATA_QUERY_PATTERNS[3]['pattern']:
    print("[PATTERN-CHECK] ✅ Contains \\s* (space allowed)")
else:
    print("[PATTERN-CHECK] ❌ Missing \\s* (NO space allowed)!")

# DEBUG: Print ALL patterns
print("[PATTERN-LIST] All DATA_QUERY_PATTERNS:")
for i, p in enumerate(test_engine.DATA_QUERY_PATTERNS):
    print(f"  [{i}] {p['name']}: {p['pattern'][:50]}...")

# ==================== 配置 ====================

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "building_energy",
    "user": "postgres",
    "password": "416417"
}

OLLAMA_URL = "http://localhost:11434/api/generate"
LOCAL_MODEL = "qwen2.5:7b"

CLOUD_API_KEY = "sk-a803c04cb57c40daa7f7aede38bb3469"
CLOUD_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
CLOUD_MODEL = "qwen-plus"

CHROMA_PATH = r"E:\openclaw-project\workspace\Fuwu\chroma_db"

BUILDINGS = ["Baikal", "Aral", "Caspian", "Huron", "Erie", "Ladoga", "Superior", 
             "Titicaca", "Victoria", "Winnipeg", "Vostok", "Michigan", "Ontario", "Malawi"]

# ==================== 数据字典 ====================
# 根据 BEIMS 数据字典定义
# 数据库字段名 -> 标准信息

DATA_DICT = {
    # 基本信息
    "building_id": {"name": "建筑编号", "unit": "", "type": "String", 
                    "standard_name": "Building_ID", "keywords": ["建筑编号", "建筑id", "哪个建筑"]},
    "building_type": {"name": "建筑类型", "unit": "", "type": "String",
                      "standard_name": "Building_Type", "keywords": ["建筑类型", "类型"]},
    "timestamp": {"name": "时间戳", "unit": "", "type": "DateTime",
                  "standard_name": "Timestamp", "keywords": ["时间", "日期", "时候"]},
    
    # 能耗数据
    "electricity_kwh": {"name": "电耗", "unit": "kWh", "type": "Float",
                        "standard_name": "Electricity_Consumption_kWh", "keywords": ["电耗", "用电量", "电量", "电力", "电"]},
    "water_m3": {"name": "水耗", "unit": "m³", "type": "Float",
                 "standard_name": "Water_Consumption_m3", "keywords": ["水耗", "用水量", "水量", "水"]},
    
    # 影响因素
    "hvac_kwh": {"name": "空调能耗", "unit": "kWh", "type": "Float",
                 "standard_name": "HVAC_Energy_kWh", "keywords": ["空调能耗", "空调用电", "hvac"]},
    "chw_supply_temp": {"name": "冷冻水供水温度", "unit": "°C", "type": "Float",
                        "standard_name": "CHW_Supply_Temp", "keywords": ["供水温度", "冷冻水供水", "供水温"]},
    "chw_return_temp": {"name": "冷冻水回水温度", "unit": "°C", "type": "Float",
                        "standard_name": "CHW_Return_Temp", "keywords": ["回水温度", "冷冻水回水", "回水温"]},
    "outdoor_temp": {"name": "室外温度", "unit": "°C", "type": "Float",
                     "standard_name": "Outdoor_Temp", "keywords": ["室外温度", "室外气温", "环境温度", "气温"]},
    "humidity_pct": {"name": "湿度", "unit": "%", "type": "Float",
                     "standard_name": "Humidity_Pct", "keywords": ["湿度", "相对湿度"]},
    "occupancy_density": {"name": "人员密度", "unit": "人/100m²", "type": "Float",
                          "standard_name": "Occupancy_Density", "keywords": ["人员密度", "人数", "人密度"]},
    
    # 设备信息
    "meter_id": {"name": "仪表编号", "unit": "", "type": "String",
                 "standard_name": "Meter_ID", "keywords": ["仪表编号", "仪表id"]},
    "system_status": {"name": "系统状态", "unit": "", "type": "String",
                      "standard_name": "System_Status", "keywords": ["系统状态", "运行状态", "状态"]}
}

# 数据库表结构（供模型参考）
# 重要：SQL 查询必须使用数据库字段名（第一列）
DB_SCHEMA = """
表名：energy_reports

数据库字段（SQL必须用这些）:
- timestamp: 时间戳 (TIMESTAMP)
- building_id: 建筑编号 (VARCHAR)，可选值：Baikal, Aral, Caspian, Huron, Erie, Ladoga, Superior, Titicaca, Victoria, Winnipeg, Vostok, Michigan, Ontario, Malawi
- building_type: 建筑类型 (VARCHAR)
- electricity_kwh: 电耗 (FLOAT, 单位kWh)
- water_m3: 水耗 (FLOAT, 单位m³)
- hvac_kwh: 空调能耗 (FLOAT, 单位kWh)
- chw_supply_temp: 冷冻水供水温度 (FLOAT, 单位°C)
- chw_return_temp: 冷冻水回水温度 (FLOAT, 单位°C)
- outdoor_temp: 室外温度 (FLOAT, 单位°C)
- humidity_pct: 湿度 (FLOAT, 单位%)
- occupancy_density: 人员密度 (FLOAT, 单位人/100m²)
- meter_id: 仪表编号 (VARCHAR)
- system_status: 系统状态 (VARCHAR)

重要规则：
1. SQL 查询必须使用上述数据库字段名，不要改名！
2. 例如查电耗用 electricity_kwh，不是 electricity_consumption_kwh
3. 时间范围：2019-2021年夏季数据
4. building_id 使用 ILIKE 进行模糊匹配
"""

COMPLEX_KEYWORDS = ["为什么", "建议", "分析", "怎么", "如何", "优化", "改进", "原因", "趋势", "预测", "对比", "比较", "高吗", "低吗", "正常吗", "怎么样", "如何看", "有没有问题", "有什么", "有没有", "异常"]
BUILDING_LIST_KEYWORDS = ["哪些建筑", "建筑列表", "有哪些建筑", "建筑名字", "建筑名称", "都有哪些", "可查询"]
FOLLOWUP_KEYWORDS = ["这", "那", "它", "这个", "那个", "怎么样", "呢", "吗", "如何", "怎样"]


# ==================== 智能对话机器人 ====================

class SmartBot:
    """智能对话机器人 - 支持上下文记忆"""
    
    def __init__(self):
        self.knowledge_base = None
        self.hist = []  # 对话历史 [(role, content), ...]
        self.last_building = None
        self.last_date = None
        self.last_result = None
        self._init_knowledge_base()
    
    def _init_knowledge_base(self):
        try:
            self.chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
            self.knowledge_base = self.chroma_client.get_collection("fuwu_knowledge")
            print(f"[知识库] 已加载 {self.knowledge_base.count()} 个文档块")
        except Exception as e:
            self.knowledge_base = None
            print(f"[知识库] 加载失败：{e}")
    
    def ask(self, question: str) -> str:
        """处理用户问题 - 本地模型分析意图后执行操作"""
        # 记录用户问题
        self.hist.append(("用户", question))
        
        # 特殊查询：建筑列表
        if any(kw in question for kw in BUILDING_LIST_KEYWORDS):
            print(f"[调试] 建筑列表查询 → 无需模型")
            reply = f"可查询的建筑有：{'、'.join(BUILDINGS)}，共 {len(BUILDINGS)} 个建筑。"
            self.hist.append(("助手", reply))
            return reply
        
        # 识别建筑
        building = self._find_building(question)
        if building:
            self.last_building = building
        elif self.last_building and self._is_followup(question):
            building = self.last_building
        
        # 追问 + 有上次结果 → 直接走云端分析
        if self._is_followup(question) and self.last_result:
            print(f"[调试] 追问分析 → 使用上次结果 + 云端模型")
            context = self._inject_context(question)
            kb_context, kb_sources = self._search_knowledge(question)
            reply = self._call_cloud_with_data(context, self.last_result, kb_context, kb_sources)
            self.hist.append(("助手", reply))
            return reply
        
        # 让本地模型分析意图
        intent = self._analyze_intent(question)
        print(f"[调试] 意图分析结果: {intent}")
        
        # 根据意图执行
        if intent["action"] == "analyze":
            # 分析类问题 → 先查数据，再交给云端
            date = self._parse_date(question)
            if date:
                self.last_date = date
            result = self._local_query_data_only(question)
            if result is None:
                reply = "查询无结果。数据覆盖 2019-2021 年夏季，可查询建筑：" + "、".join(BUILDINGS[:5]) + " 等。"
            else:
                kb_context, kb_sources = self._search_knowledge(question)
                reply = self._call_cloud_with_data(question, result, kb_context, kb_sources)
        
        elif intent["action"] == "query":
            # 纯数据查询 → 查完直接返回
            date = self._parse_date(question)
            if date:
                self.last_date = date
            result = self._local_query_data_only(question)
            if result is None:
                reply = "查询无结果。数据覆盖 2019-2021 年夏季，可查询建筑：" + "、".join(BUILDINGS[:5]) + " 等。"
            else:
                reply = self._format_query_result(question, result)
        
        elif intent["action"] == "answer":
            # 纯回答 → 直接云端
            kb_context, kb_sources = self._search_knowledge(question)
            reply = self._call_cloud_with_data(question, "", kb_context, kb_sources)
        
        else:
            # 默认：先查数据再分析
            date = self._parse_date(question)
            if date:
                self.last_date = date
            result = self._local_query_data_only(question)
            if result is None:
                reply = "查询无结果。"
            else:
                reply = self._format_query_result(question, result)
        
        self.hist.append(("助手", reply))
        return reply
    
    def _analyze_intent(self, question: str) -> dict:
        """用本地模型分析用户意图，返回结构化决策"""
        context_info = ""
        if self.last_result:
            context_info = f"\n上次查询结果: {self.last_result}"
        
        prompt = f"""# 角色
你是一个意图分类器，负责分析用户问题的意图类型。

# 分类规则
请根据以下规则判断用户问题的意图：

## analyze（分析类）
当问题包含以下任一特征时，归类为 analyze：
- 包含评价词：异常、正常吗、高吗、低吗、合理吗、有问题吗、怎么样
- 包含分析词：为什么、原因、趋势、对比、比较、分析
- 包含建议词：建议、优化、改进、怎么办
- 同时包含"查询数据"和"评价分析"（如"XX是多少，有没有异常"）

## query（查询类）
当问题仅要求查询具体数据，不包含评价或分析时：
- 如"XX建筑XX时间的电耗是多少"
- 如"XX的用水量"

## answer（回答类）
当问题不需要查数据库，可以直接回答时：
- 如"建筑有哪些"、"COP是什么"、"系统怎么用"

# 示例
问题："Michigan 5月7日的电耗是多少" → {{"action": "query"}}
问题："这个数值正常吗" → {{"action": "analyze"}}
问题："Caspian的电耗是多少，有没有异常" → {{"action": "analyze"}}
问题："建筑有哪些" → {{"action": "answer"}}

# 当前问题
问题：{question}{context_info}

# 输出
请只返回JSON，不要其他内容：
{{"action": "query或analyze或answer"}}"""
        
        try:
            response = self._call_ollama(prompt)
            import json
            # 提取 JSON
            match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:
            pass
        
        # 降级：检查问题中是否包含分析关键词
        if any(kw in question for kw in ["异常", "正常吗", "高吗", "低吗", "为什么", "分析", "建议", "合理吗", "有问题吗", "怎么样"]):
            return {"action": "analyze"}
        
        # 默认查询
        return {"action": "query"}
    
    def _is_followup(self, question: str) -> bool:
        """判断是否是追问"""
        # 短问题 + 追问关键词
        if len(question) < 20 and any(kw in question for kw in FOLLOWUP_KEYWORDS):
            return True
        # 包含评价性关键词但没有具体建筑/日期
        has_eval_kw = any(kw in question for kw in ["高吗", "低吗", "正常吗", "怎么样", "如何看"])
        has_building = any(b.lower() in question.lower() for b in BUILDINGS)
        if has_eval_kw and not has_building:
            return True
        return False
    
    def _inject_context(self, question: str) -> str:
        """注入上下文到问题中"""
        context_parts = []
        if self.last_building:
            context_parts.append(f"建筑：{self.last_building}")
        if self.last_date:
            context_parts.append(f"日期：{self.last_date}")
        if self.last_result:
            context_parts.append(f"上次查询结果：{self.last_result}")
        
        if context_parts:
            return f"[上下文：{'; '.join(context_parts)}] {question}"
        return question
    
    def _find_building(self, text: str) -> str:
        for b in BUILDINGS:
            if b.lower() in text.lower():
                return b
        return None
    
    def _parse_date(self, text: str) -> str:
        """解析日期"""
        cn_map = {'零': '0', '一': '1', '二': '2', '三': '3', '四': '4', 
                  '五': '5', '六': '6', '七': '7', '八': '8', '九': '9', '十': '10'}
        converted = text
        for cn, num in cn_map.items():
            converted = converted.replace(cn, num)
        
        match = re.search(r'(\d{4})[年\-](\d{1,2})[月\-](\d{1,2})', converted)
        if match:
            return f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
        
        match = re.search(r'(\d{1,2})月(\d{1,2})', converted)
        if match:
            return f"2021-{int(match.group(1)):02d}-{int(match.group(2)):02d}"
        return None
    
    def _parse_hour(self, text: str) -> int:
        """解析小时"""
        cn_map = {'零': '0', '一': '1', '二': '2', '三': '3', '四': '4', 
                  '五': '5', '六': '6', '七': '7', '八': '8', '九': '9', '十': '10',
                  '十一': '11', '十二': '12'}
        converted = text
        for cn, num in cn_map.items():
            converted = converted.replace(cn, num)
        
        patterns = [
            (r'上午\s*(\d{1,2})\s*点', False),
            (r'下午\s*(\d{1,2})\s*点', True),
            (r'早上\s*(\d{1,2})\s*点', False),
            (r'晚上\s*(\d{1,2})\s*点', True),
            (r'(\d{1,2})\s*点', False),
        ]
        for pattern, add_12 in patterns:
            match = re.search(pattern, converted)
            if match:
                hour = int(match.group(1))
                if add_12 and hour < 12:
                    hour += 12
                return hour
        return None
    
    def _local_query(self, question: str) -> str:
        """本地模型生成 SQL 并查询"""
        print(f"[调试] 开始本地模型查询 (qwen2.5:7b)")
        try:
            # 解析日期和小时
            date = self._parse_date(question)
            hour = self._parse_hour(question)
            
            if date:
                self.last_date = date
            
            # 生成 SQL（用 7B 模型，结果直接格式化不调用二次 LLM）
            extra_info = []
            if date:
                extra_info.append(f"日期: {date}")
            if hour is not None:
                extra_info.append(f"小时: {hour}")
            info_str = "\n".join(extra_info) if extra_info else "无特定时间要求"
            
            sql_prompt = f"""你是 SQL 专家。根据问题生成 PostgreSQL 查询。

表结构：{DB_SCHEMA}

问题：{question}
解析信息：{info_str}

要求：
1. 只返回 SQL，不要解释
2. building_id 用 ILIKE 模糊匹配
3. 时间用 timestamp 字段，具体日期用 timestamp >= 'YYYY-MM-DD HH:00:00' AND timestamp <= 'YYYY-MM-DD HH:59:59'
4. 如果指定了小时，加上 EXTRACT(HOUR FROM timestamp) = 小时值

SQL:"""

            sql = self._call_ollama(sql_prompt).strip()
            sql = self._extract_sql(sql)
            
            if not sql:
                return "无法生成查询，请提供更具体的信息（如建筑名称、日期）。"
            
            print(f"[SQL] {sql}")
            
            # 执行查询
            result = self._execute_sql(sql)
            
            if not result:
                return "查询无结果。数据覆盖 2019-2021 年夏季，可查询建筑：" + "、".join(BUILDINGS[:5]) + " 等。"
            
            # 保存结果用于上下文
            self.last_result = result
            
            # 直接格式化结果，不调用 LLM 汇总
            return self._format_query_result(question, result)
            
        except Exception as e:
            return f"查询失败：{str(e)}"
    
    def _local_query_data_only(self, question: str) -> str:
        """本地模型生成 SQL 并查询，返回原始结果供云端分析或前端格式化"""
        print(f"[调试] 开始本地模型查询 (qwen2.5:7b)")
        try:
            # 解析日期和小时
            date = self._parse_date(question)
            hour = self._parse_hour(question)
            
            if date:
                self.last_date = date
            
            extra_info = []
            if date:
                extra_info.append(f"日期: {date}")
            if hour is not None:
                extra_info.append(f"小时: {hour}")
            info_str = "\n".join(extra_info) if extra_info else "无特定时间要求"
            
            sql_prompt = f"""你是 SQL 专家。根据问题生成 PostgreSQL 查询。

表结构：{DB_SCHEMA}

问题：{question}
解析信息：{info_str}

要求：
1. 只返回 SQL，不要解释
2. building_id 用 ILIKE 模糊匹配
3. 时间用 timestamp 字段，具体日期用 timestamp >= 'YYYY-MM-DD HH:00:00' AND timestamp <= 'YYYY-MM-DD HH:59:59'
4. 如果指定了小时，加上 EXTRACT(HOUR FROM timestamp) = 小时值

SQL:"""

            sql = self._call_ollama(sql_prompt).strip()
            sql = self._extract_sql(sql)
            
            if not sql:
                print(f"[SQL] 无法生成 SQL")
                return None
            
            print(f"[SQL] {sql}")
            
            # 执行查询
            result = self._execute_sql(sql)
            
            # 保存结果用于上下文
            self.last_result = result
            return result
            
        except Exception as e:
            print(f"[SQL] 查询失败：{e}")
            return None
    
    def _extract_sql(self, text: str) -> str:
        match = re.search(r'```sql\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        match = re.search(r'(SELECT\s+.*?;?)$', text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        if text.upper().startswith('SELECT'):
            return text
        
        return None
    
    def _execute_sql(self, sql: str) -> str:
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute(sql)
            
            col_names = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            
            cur.close()
            conn.close()
            
            if not rows:
                return None
            
            # 将字段名映射为中文名+单位
            display_names = []
            for col in col_names:
                dict_info = DATA_DICT.get(col, {})
                cn_name = dict_info.get("name", col)
                unit = dict_info.get("unit", "")
                if unit:
                    display_names.append(f"{cn_name}({unit})")
                else:
                    display_names.append(cn_name)
            
            if len(rows) == 1 and len(rows[0]) == 1:
                return f"{display_names[0]}: {rows[0][0]}"
            
            result = "| " + " | ".join(display_names) + " |\n"
            result += "|" + "|".join(["---" for _ in display_names]) + "|\n"
            for row in rows[:10]:
                result += "| " + " | ".join(str(v) if v is not None else "NULL" for v in row) + " |\n"
            
            if len(rows) > 10:
                result += f"\n（共 {len(rows)} 条记录）"
            
            return result
                
        except Exception as e:
            return f"SQL 错误：{str(e)}"
    
    def _format_query_result(self, question: str, result: str) -> str:
        """将查询结果格式化为自然语言回答（纯文本，不用表格）"""
        if result.startswith("SQL 错误："):
            return result
        
        # 单值结果：映射为中文名+单位
        if ": " in result and "\n" not in result:
            parts = result.split(": ", 1)
            field_name = parts[0].strip()
            value = parts[1].strip()
            dict_info = DATA_DICT.get(field_name, {})
            cn_name = dict_info.get("name", field_name)
            unit = dict_info.get("unit", "")
            if unit:
                return f"{value} {unit}（{cn_name}）"
            return f"{value}（{cn_name}）"
        
        # 多行结果：生成统计摘要（不再用表格）
        lines = result.strip().split("\n")
        if len(lines) < 3:
            return f"查询结果：共 {len(data_lines)} 条记录"
        
        header = lines[0]
        data_lines = lines[2:]
        cols = [c.strip() for c in header.strip("|").split("|")]
        col_idx = {name: i for i, name in enumerate(cols)}
        
        # 提取数值列
        value_col = None
        for col in cols:
            if col not in ("timestamp", "building_id", "meter_id", "system_status", "building_type"):
                value_col = col
                break
        
        if value_col is None:
            return f"查询结果：共 {len(data_lines)} 条记录"
        
        dict_info = DATA_DICT.get(value_col, {})
        cn_name = dict_info.get("name", value_col)
        unit = dict_info.get("unit", "")
        
        values = []
        timestamps = []
        for line in data_lines:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= len(cols):
                if "timestamp" in col_idx:
                    timestamps.append(cells[col_idx["timestamp"]])
                try:
                    values.append(float(cells[col_idx[value_col]]))
                except (ValueError, TypeError):
                    pass
        
        if not values:
            return f"查询结果：共 {len(data_lines)} 条记录"
        
        avg = sum(values) / len(values)
        mn = min(values)
        mx = max(values)
        unit_str = f" {unit}" if unit else ""
        
        summary = f"**{cn_name}** 查询结果（共 {len(data_lines)} 条记录）：\n\n"
        summary += f"• 平均值：**{avg:.2f}{unit_str}**\n"
        summary += f"• 最小值：**{mn:.2f}{unit_str}**\n"
        summary += f"• 最大值：**{mx:.2f}{unit_str}**"
        
        return summary
    
    def _search_knowledge(self, query: str, n_results: int = 3) -> tuple:
        if not self.knowledge_base:
            return "", []
        try:
            results = self.knowledge_base.query(query_texts=[query], n_results=n_results)
            if results['documents']:
                context = "\n\n---\n\n".join(results['documents'][0])
                sources = [m.get('source', '未知') for m in results['metadatas'][0]]
                return context, sources
        except Exception as e:
            print(f"[知识库] 搜索失败：{e}")
        return "", []
    
    def _build_context(self, building: str, question: str) -> str:
        if not building:
            return ""
        
        context_parts = [f"建筑：{building}"]
        
        try:
            with EnergyAnalyzer(DB_CONFIG) as analyzer:
                df = analyzer.get_data(building)
                if df.empty:
                    return "\n".join(context_parts)
                
                context_parts.append(f"\n=== 总体概况 ===")
                context_parts.append(f"总电耗：{round(df['electricity_kwh'].sum(), 2)} kWh")
                context_parts.append(f"总空调能耗：{round(df['hvac_kwh'].sum(), 2)} kWh")
                context_parts.append(f"平均电耗：{round(df['electricity_kwh'].mean(), 2)} kWh/小时")
                
                cop_df = analyzer.analyze_cop_trend(building)
                if not cop_df.empty:
                    context_parts.append(f"平均 COP：{round(cop_df['cop'].mean(), 2)}")
                    
        except Exception as e:
            context_parts.append(f"数据获取失败：{str(e)}")
        
        return "\n".join(context_parts)
    
    def _call_ollama(self, prompt: str, model: str = None) -> str:
        model_name = model or LOCAL_MODEL
        try:
            print(f"[调试] 调用本地模型: {model_name}")
            response = requests.post(OLLAMA_URL, json={
                "model": model_name,
                "prompt": prompt,
                "stream": False
            }, timeout=60)
            return response.json().get("response", "").strip()
        except requests.exceptions.ConnectionError:
            return "[错误] 本地模型未启动，请运行 ollama serve"
        except Exception as e:
            return f"[错误] {str(e)}"
    
    def _call_cloud(self, question: str, context: str = "", kb_context: str = "", kb_sources: list = None) -> str:
        """调用云端模型，失败时降级到本地模型"""
        # 构建完整上下文
        full_context = context
        if kb_context:
            full_context += f"\n\n=== 知识库参考 ===\n{kb_context}"
        
        # 尝试云端模型
        try:
            print(f"[调试] 调用云端模型: {CLOUD_MODEL}")
            if full_context:
                prompt = f"""你是建筑能源管理专家。根据数据回答问题。

{full_context}

问题：{question}

要求：专业、简洁、有数据支撑。"""
            else:
                prompt = question
            
            response = requests.post(CLOUD_API_URL,
                headers={"Authorization": f"Bearer {CLOUD_API_KEY}"},
                json={"model": CLOUD_MODEL, "messages": [{"role": "user", "content": prompt}]},
                timeout=60
            )
            
            # 检查响应状态
            if response.status_code != 200:
                raise Exception(f"API 返回错误码: {response.status_code}")
            
            result = response.json()
            if "choices" not in result or not result["choices"]:
                raise Exception("API 返回格式异常")
            
            reply = result["choices"][0]["message"]["content"]
            
            # 添加知识库来源
            if kb_sources:
                reply += f"\n\n📚 **知识库来源**：{', '.join(kb_sources)}"
            
            return reply
            
        except Exception as e:
            print(f"[云端模型] 调用失败：{e}，降级到本地模型")
            
            # 降级到本地模型 + 知识库
            return self._fallback_to_local(question, full_context, kb_sources)
    
    def _call_cloud_with_data(self, question: str, raw_data: str, kb_context: str = "", kb_sources: list = None) -> str:
        """调用云端模型，传入原始查询数据进行分析"""
        full_prompt = f"""你是建筑能源管理专家。请根据以下数据回答用户问题。

=== 原始查询数据 ===
{raw_data}
"""
        if kb_context:
            full_prompt += f"\n=== 知识库参考 ===\n{kb_context}\n"
        
        full_prompt += f"\n=== 用户问题 ===\n{question}\n\n要求：专业、简洁、基于数据回答。"
        
        print(f"[调试] 调用云端模型: {CLOUD_MODEL}")
        try:
            response = requests.post(CLOUD_API_URL,
                headers={"Authorization": f"Bearer {CLOUD_API_KEY}"},
                json={"model": CLOUD_MODEL, "messages": [{"role": "user", "content": full_prompt}]},
                timeout=60
            )
            
            if response.status_code != 200:
                raise Exception(f"API 返回错误码: {response.status_code}")
            
            result = response.json()
            if "choices" not in result or not result["choices"]:
                raise Exception("API 返回格式异常")
            
            reply = result["choices"][0]["message"]["content"]
            
            if kb_sources:
                reply += f"\n\n📚 **知识库来源**：{', '.join(kb_sources)}"
            
            return reply
            
        except Exception as e:
            print(f"[云端模型] 调用失败：{e}，降级到本地模型")
            # 降级：用本地模型分析
            fallback_prompt = f"原始数据：\n{raw_data}\n\n问题：{question}\n\n请简洁回答："
            response = requests.post(OLLAMA_URL, json={
                "model": LOCAL_MODEL,
                "prompt": fallback_prompt,
                "stream": False
            }, timeout=120)
            if response.status_code == 200:
                reply = response.json().get("response", "").strip()
                if sources:
                    reply += f"\n\n📚 **知识库来源**：{', '.join(kb_sources)}"
                return reply
            return f"[错误] 所有模型都不可用：{str(e)}"
    
    def _fallback_to_local(self, question: str, context: str, sources: list = None) -> str:
        """降级到本地模型回答"""
        print(f"[调试] 云端模型失败，降级到本地模型: {LOCAL_MODEL}")
        # 检查本地模型是否可用
        try:
            # 构建提示词
            if context:
                prompt = f"""根据以下信息回答问题。如果信息不足，请说明。

{context}

问题：{question}

请简洁回答："""
            else:
                prompt = f"""请回答以下问题。如果不确定，请说明。

问题：{question}

请简洁回答："""
            
            # 调用本地模型
            response = requests.post(OLLAMA_URL, json={
                "model": LOCAL_MODEL,
                "prompt": prompt,
                "stream": False
            }, timeout=120)
            
            if response.status_code != 200:
                return f"[错误] 云端模型和本地模型都不可用。云端错误已记录，本地模型返回：{response.status_code}"
            
            reply = response.json().get("response", "").strip()
            
            if not reply:
                return "[错误] 本地模型返回空结果，请稍后重试"
            
            # 添加来源和降级提示
            if sources:
                reply += f"\n\n📚 **知识库来源**：{', '.join(sources)}"
            
            reply += "\n\n⚠️ *注：云端模型暂时不可用，已使用本地模型回答*"
            
            return reply
            
        except requests.exceptions.ConnectionError:
            return "[错误] 云端模型不可用，本地模型未启动。请运行 `ollama serve` 或稍后重试。"
        except requests.exceptions.Timeout:
            return "[错误] 云端模型不可用，本地模型响应超时。请稍后重试。"
        except Exception as e:
            return f"[错误] 所有模型都不可用：{str(e)}"
    
    def clear(self):
        """清空对话历史"""
        self.hist = []
        self.last_building = None
        self.last_date = None
        self.last_result = None


# 初始化云边协同路由分发器
router = CloudEdgeRouter(config={
    "ollama_url": "http://localhost:11434",
    "local_model": "qwen2.5:7b",
    "cloud_api_key": CLOUD_API_KEY,
    "cloud_api_url": CLOUD_API_URL,
    "cloud_model": CLOUD_MODEL
})

# 保留旧版机器人用于兼容
bot = SmartBot()


# ==================== FastAPI 应用 ====================

app = FastAPI(title="建筑能源管理系统 API v2", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 数据模型 ====================

class ChatRequest(BaseModel):
    message: str
    building_id: Optional[str] = None
    clear_history: Optional[bool] = False  # 是否清空历史
    history: Optional[List[Dict[str, str]]] = None  # 🔥 新增：完整对话历史 [{"role": "user/assistant", "content": "..."}]
    session_id: Optional[str] = None  # 🔥 新增：会话标识（用于多会话支持）


class ChatResponse(BaseModel):
    response: str
    context: Optional[Dict] = None  # 返回当前上下文
    history: Optional[List[Dict[str, str]]] = None  # 🔥 新增：返回更新后的完整历史


# ==================== API 路由 ====================

@app.get("/")
async def root():
    return {
        "name": "建筑能源管理系统 API v2",
        "version": "2.0.0",
        "features": ["智能对话", "上下文记忆", "SQL 自动生成", "知识库检索"]
    }


@app.get("/buildings")
async def list_buildings():
    return {"buildings": BUILDINGS, "count": len(BUILDINGS)}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    智能对话接口 - 云边协同路由 v3 (增强版上下文记忆)
    
    四层过滤逻辑：
    1. 硬规则过滤 - 毫秒级响应高频查询
    2. 语义路由 - Embedding 向量匹配
    3. 本地推理 - 7B 模型意图解析
    4. 云端增强 - 复杂分析任务
    
    ✨ 新增：完整多轮对话上下文记忆
    - 支持最多 20 轮对话历史
    - 自动提取关键实体（建筑、时间、指标）
    - 智能上下文压缩和总结
    
    示例：
    1. "Michigan 5月7日上午6点的电耗是多少？"
    2. "这个数值算高吗？"  ← 会记住上一次的查询结果
    3. "对比一下 Caspian 和 Ontario"  ← 会记住之前讨论的建筑
    """
    try:
        # 🔥 新增：处理会话和历史
        if request.clear_history:
            router.clear_context()
            bot.clear()
        elif request.history:
            # 🔥 关键：从请求中恢复历史到 router.context
            router.restore_history(request.history)
        
        # 构建问题
        question = request.message
        if request.building_id:
            question = f"[建筑: {request.building_id}] {question}"
        
        # DEBUG: Test match() directly before routing
        if 'Caspian 2021' in question or '7月21' in question:
            direct_match = router.static_rule.match(question)
            print(f"[DIRECT-MATCH-TEST] query='{question}'")
            print(f"[DIRECT-MATCH-TEST] result={direct_match.action if direct_match else None}")
            print(f"[DIRECT-MATCH-TEST] params={direct_match.params if direct_match else None}")
        
        # 使用云边协同路由分发器（自动传入 context）
        result = router.route(question)
        reply = result.get("response", "处理失败")
        
        # 🔥 更新上下文（记录本轮交互）
        router.update_context(
            user_message=request.message,
            assistant_reply=reply,
            layer=result.get("layer"),
            action=result.get("action")
        )
        
        # 返回增强的上下文信息
        context = {
            "last_building": router.context.get("last_building"),
            "last_date": router.context.get("last_date"),
            "last_result": router.context.get("last_result"),
            "layer": result.get("layer", "unknown"),
            "system_mode": router.get_status().get("mode", "normal"),
            "history_count": len(router.context.get("history", [])),
            "session_id": request.session_id or "default",
            # 🔥 新增：提取的关键实体（便于前端展示）
            "extracted_entities": {
                "buildings": router.context.get("mentioned_buildings", []),
                "dates": router.context.get("mentioned_dates", []),
                "metrics": router.context.get("mentioned_metrics", [])
            }
        }
        
        print(f"[调试] 请求完成 → 用户: {request.message[:50]} → 路由层: {result.get('layer')} → 历史轮数: {context['history_count']}")
        
        # 🔧 修复：清理history中的None值，避免Pydantic验证失败
        raw_history = router.context.get("history", [])
        cleaned_history = []
        for entry in raw_history:
            if isinstance(entry, dict):
                cleaned_entry = {}
                for k, v in entry.items():
                    # 将None转换为空字符串
                    cleaned_entry[k] = str(v) if v is not None else ""
                cleaned_history.append(cleaned_entry)
            else:
                cleaned_history.append(entry)
        
        return ChatResponse(
            response=reply,
            context=context,
            history=cleaned_history  # 🔥 返回清理后的历史
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/clear")
async def clear_chat():
    """清空对话历史"""
    router.clear_context()
    bot.clear()
    return {"status": "ok", "message": "对话历史已清空"}


@app.get("/router/status")
async def get_router_status():
    """获取路由分发器状态"""
    return router.get_status()


@app.get("/buildings/{building_id}/summary")
async def get_summary(building_id: str):
    with EnergyAnalyzer(DB_CONFIG) as analyzer:
        report = analyzer.generate_report(building_id)
    if "error" in report:
        raise HTTPException(status_code=404, detail=report["error"])
    return report


@app.get("/buildings/{building_id}/cop")
async def analyze_cop(building_id: str):
    with EnergyAnalyzer(DB_CONFIG) as analyzer:
        cop_df = analyzer.analyze_cop_trend(building_id)
    if cop_df.empty:
        raise HTTPException(status_code=404, detail="无数据")
    return {
        "building_id": building_id,
        "avg_cop": round(cop_df['cop'].mean(), 2),
        "rating_distribution": cop_df['cop_rating'].value_counts().to_dict()
    }


@app.get("/buildings/{building_id}/anomalies")
async def detect_anomalies(building_id: str, threshold: float = 3.0):
    with EnergyAnalyzer(DB_CONFIG) as analyzer:
        result = analyzer.analyze_anomalies(building_id, threshold=threshold)
    return result


# ==================== 实时监测 ====================

# 初始化监测服务
monitor = RealTimeMonitor()

@app.get("/monitor/status")
async def get_monitor_status():
    """获取监测状态"""
    return monitor.get_summary()

@app.get("/monitor/alerts")
async def get_monitor_alerts(building_id: Optional[str] = None, limit: int = 50):
    """获取告警列表"""
    return {"alerts": monitor.get_alerts(building_id, limit)}

@app.post("/monitor/start")
async def start_monitor(speed: float = 60.0, start_date: str = "2021-07-01"):
    """启动监测"""
    if monitor.is_running:
        return {"status": "already_running", "message": "监测已在运行中"}
    
    monitor.load_historical_data(start_date)
    
    # 在后台启动监测任务
    asyncio.create_task(monitor.start_monitoring(speed))
    
    return {
        "status": "started",
        "speed": speed,
        "start_date": start_date
    }

@app.post("/monitor/stop")
async def stop_monitor():
    """停止监测"""
    monitor.stop_monitoring()
    return {"status": "stopped"}

@app.post("/monitor/pause")
async def pause_monitor():
    """暂停监测"""
    monitor.pause_monitoring()
    return {"status": "paused", "simulation_time": monitor.simulation_current_time.isoformat() if monitor.simulation_current_time else None}

@app.post("/monitor/resume")
async def resume_monitor():
    """继续监测"""
    monitor.resume_monitoring()
    return {"status": "resumed"}

@app.post("/monitor/reset")
async def reset_monitor():
    """重置监测"""
    monitor.reset_monitoring()
    return {"status": "reset"}

@app.post("/monitor/speed")
async def set_speed(speed: float = Query(..., ge=1, le=3600)):
    """动态调整速度"""
    monitor.speed = speed
    print(f"[监测] 速度已更新: {speed}x")
    return {"status": "ok", "speed": speed}

@app.post("/monitor/clear-alerts")
async def clear_alerts():
    """清除所有告警"""
    monitor.clear_alerts()
    return {"status": "ok", "message": "所有告警已清除"}

@app.post("/monitor/simulation")
async def set_simulation(settings: dict):
    """设置模拟参数"""
    monitor.simulation_settings = settings
    return {"status": "ok", "settings": settings}

@app.post("/monitor/trigger-anomaly")
async def trigger_anomaly(params: dict):
    """手动触发异常"""
    building = params.get("building", "all")
    anomaly_type = params.get("type", "electricity_high")
    intensity = params.get("intensity", 5)
    
    triggered = monitor.trigger_anomaly(building, anomaly_type, intensity)
    
    return {
        "status": "triggered",
        "building": building,
        "type": anomaly_type,
        "intensity": intensity,
        "triggered_count": len(triggered)
    }

@app.websocket("/ws/monitor")
async def websocket_monitor(websocket: WebSocket):
    """WebSocket 实时监测推送"""
    await websocket.accept()
    await monitor.connect(websocket)
    
    try:
        while True:
            # 接收客户端消息（心跳或其他指令）
            data = await websocket.receive_text()
            
            # 处理指令
            if data == "ping":
                await websocket.send_json({"type": "pong"})
            elif data == "status":
                await websocket.send_json({
                    "type": "status",
                    "data": monitor.get_summary()
                })
    except WebSocketDisconnect:
        monitor.disconnect(websocket)
    except Exception as e:
        print(f"[WebSocket] 错误: {e}")
        monitor.disconnect(websocket)


# ==================== 启动 ====================

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("建筑能源管理系统 API v2 - 支持上下文记忆")
    print("=" * 60)
    print("\n🚀 http://localhost:8082")
    print("📖 http://localhost:8082/docs\n")
    uvicorn.run(app, host="0.0.0.0", port=8082)