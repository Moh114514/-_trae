"""
云边协同路由分发器 - Cloud-Edge Router [v2.1-fix-sql-date]

实现四层过滤逻辑：
1. 硬规则过滤 (Static Rule Layer) - 毫秒级响应
2. 语义路由层 (Semantic Router Layer) - Embedding 向量匹配
3. 本地推理层 (Local SLM Layer) - 简单逻辑判断
4. 云端增强层 (Cloud LLM Layer) - 复杂分析

支持断网容灾降级机制
"""

import re
import json
import time
from datetime import datetime
import requests
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum


# ==================== 数据模型 ====================

class RouteLayer(Enum):
    """路由层级枚举"""
    STATIC_RULE = "static_rule"      # 第一层：硬规则
    SEMANTIC = "semantic"            # 第二层：语义路由
    LOCAL_SLM = "local_slm"          # 第三层：本地推理
    CLOUD_LLM = "cloud_llm"          # 第四层：云端增强


@dataclass
class RouteResult:
    """路由结果"""
    layer: RouteLayer
    action: str                      # 执行动作
    confidence: float = 1.0          # 置信度
    data: Dict[str, Any] = field(default_factory=dict)  # 附加数据
    response: str = ""               # 直接返回的响应（硬规则层）
    need_cloud: bool = False         # 是否需要云端处理
    sql: str = ""                    # 生成的 SQL（如果有）
    params: Dict[str, Any] = field(default_factory=dict)  # 提取的参数


@dataclass
class SystemStatus:
    """系统状态"""
    mode: str = "normal"             # normal / fallback
    cloud_available: bool = True
    last_cloud_check: float = 0.0
    total_requests: int = 0
    layer_stats: Dict[str, int] = field(default_factory=lambda: {
        "static_rule": 0,
        "semantic": 0,
        "local_slm": 0,
        "cloud_llm": 0
    })


# ==================== 第一层：硬规则过滤引擎 ====================

class StaticRuleEngine:
    """
    硬规则过滤引擎 - 毫秒级响应高频查询
    
    职责：
    - 匹配建筑列表查询
    - 匹配标准数据查询格式
    - 匹配系统控制指令
    - 匹配清空历史指令
    """
    
    # 建筑列表关键词 - 🔥 大幅扩展以支持更多表达方式
    BUILDING_LIST_KEYWORDS = [
        # 直接询问类
        "哪些建筑", "建筑列表", "有哪些建筑", "建筑名字",
        "建筑名称", "都有哪些", "可查询", "支持哪些",
        "所有建筑", "全部建筑", "列出建筑", "建筑有哪些",
        # 数量/统计类
        "几个建筑", "多少建筑", "14个建筑", "多少栋楼",
        "建筑数量", "建筑总数",
        # 模糊查询类
        "可以查什么", "能查什么", "有什么数据", "有哪些数据"
    ]

    # 🔥 新增：元数据查询关键词（字段、时间范围等）
    METADATA_QUERY_KEYWORDS = [
        # 字段相关
        "哪些字段", "什么字段", "有哪些指标", "可查的指标",
        "数据字段", "字段列表", "测量参数", "监控项",
        # 时间相关
        "时间范围", "多久的数据", "从什么时候到什么时候",
        "数据起止", "最早数据", "最新数据",
        # 系统信息
        "系统信息", "数据库信息", "表结构", "schema"
    ]

    # 清空历史关键词
    CLEAR_KEYWORDS = ["清空", "清除历史", "重新开始", "重置对话", "新对话"]
    
    # 数据查询正则模式
    DATA_QUERY_PATTERNS = [
        # 跨日格式：建筑 + X月Y日和/到Z日 + 指标
        {
            "name": "multi_day_query",
            "pattern": r"^([A-Za-z]+)\s*(\d{4})[年\-](\d{1,2})[月\-](\d{1,2})日?(?:和|至|到|[-~])(?:同月)?(\d{1,2})日?",
            "groups": ["building", "year", "month", "day_start", "day_end"]
        },
        # 时间范围格式：建筑 + 日期 + X点[上下午]到Y点[上下午]
        {
            "name": "time_range_query",
            "pattern": r"^([A-Za-z]+)\s*(\d{4})[年\-](\d{1,2})[月\-](\d{1,2})日?\s*(上午|下午|早上|晚上)?\s*([零一二三四五六七八九十\d]{1,2})点(?:到|至|-)(?:上午|下午|早上|晚上)?\s*([零一二三四五六七八九十\d]{1,2})点?",
            "groups": ["building", "year", "month", "day", "period", "hour_start", "hour_end"]
        },
        # 完整格式：建筑 + 日期 + 时间
        {
            "name": "full_query",
            "pattern": r"^([A-Za-z]+)\s*(\d{4})[年\-](\d{1,2})[月\-](\d{1,2})日?\s*(上午|下午|早上|晚上)?\s*([零一二三四五六七八九十\d]{1,2})点",
            "groups": ["building", "year", "month", "day", "period", "hour"]
        },
        # 简化格式：建筑 + 日期
        {
            "name": "date_query",
            "pattern": r"^([A-Za-z]+)\s*(\d{4})[年\-](\d{1,2})[月\-](\d{1,2})日?",
            "groups": ["building", "year", "month", "day"]
        },
        # 🔥 修复：月份级查询（建筑 + 年月 + 可选指标/趋势词）
        # ⚠️ 必须放在 date_query/full_query 之后，避免错误匹配具体日期查询
        # 匹配："Caspian 2021年7月的能耗趋势"、"Ontario 上个月的用电情况"
        # ❌ 不应匹配："Aral2021年8月3日上午6点的电耗多少" (这应该由 full_query 处理)
        {
            "name": "month_trend_query",
            # 修改正则：确保不会匹配包含"日"或具体时间的查询
            # 使用负向前瞻排除包含"日"字的查询
            "pattern": r"^([A-Za-z]+)\s*(\d{4})?[年\-]?(\d{1,2})月(?!.*日)(?:的|之)?([^日\d]+(?:趋势|变化|走势|分析|情况|如何|怎么样|正常|异常|明细|汇总|统计|报告))?$",
            "groups": ["building", "year", "month", "metric_or_action"],
            "is_monthly_trend": True
        },
        # 相对时间汇总查询（如"查询今日能耗"、"昨日电耗"、"本周用水"）
        # ⚠️ 必须放在具体日期查询之后，避免错误匹配包含具体日期的查询
        {
            "name": "relative_time_summary",
            # 🔥 修复：添加^锚点确保只匹配以相对时间开头的查询，避免误匹配包含具体日期的查询
            "pattern": r"^(?:查询|查看|显示|统计|汇总)?\s*(今日|今天|当日|昨天|昨日|本周|这周|上周|本月|这个月|上月)\s*(.+)?",
            "groups": ["time_expr", "metric_hint"],
            "is_relative_time": True
        },
        # 最简格式：只有建筑名（纯字母）- 兜底选项
        {
            "name": "simple_query",
            "pattern": r"^([A-Za-z]+)",
            "groups": ["building"]
        }
    ]
    
    # 中文数字转阿拉伯数字映射
    CN_NUM_MAP = {
        '零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
        '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
        '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15,
        '十六': 16, '十七': 17, '十八': 18, '十九': 19, '二十': 20,
        '二十一': 21, '二十二': 22, '二十三': 23
    }
    
    # 指标关键词映射（全面的同义词和表达方式）- 🔥 统一使用数据库字段名作为 key
    METRIC_KEYWORDS = {
        "electricity_kwh": [  # 电耗
            "电耗", "用电量", "电量", "电力", "电", "用电",
            "耗电", "电能", "度数", "多少度电", "用了多少电",
            "能耗", "能源消耗", "总能耗", "耗能"
        ],
        "water_m3": [  # 水耗
            "水耗", "用水量", "水量", "水", "用水",
            "耗水", "水费", "吨水", "用了多少水"
        ],
        "hvac_kwh": [  # 空调能耗
            "空调能耗", "空调用电", "hvac", "空调", "空调耗电",
            "制冷", "制热", "空调耗能", "暖通"
        ],
        "chw_supply_temp": [  # 冷冻水供水温度
            "供水温度", "冷冻水供水", "供水温", "进水温度",
            "供水", "进水", "冷水供水"
        ],
        "chw_return_temp": [  # 冷冻水回水温度
            "回水温度", "冷冻水回水", "回水温", "出水温度",
            "回水", "出水", "冷水回水"
        ],
        "outdoor_temp": [  # 室外温度
            "室外温度", "室外气温", "环境温度", "气温",
            "外界温度", "外部温度", "外面温度", "户外温度",
            "室外", "外面多热", "外面多少度", "天气温度"
        ],
        "humidity_pct": [  # 湿度
            "湿度", "相对湿度", "空气湿度",
            "潮湿", "干燥", "湿度多少"
        ],
        "occupancy_density": [  # 人员密度
            "人员密度", "人数", "人密度", "人员",
            "多少人", "人在哪", "occupancy"
        ]
    }
    
    def match(self, query: str) -> Optional[RouteResult]:
        """
        匹配硬规则
        
        Returns:
            RouteResult 或 None（未匹配时返回 None，进入下一层）
        """
        print(f"[调试-HARD-RULE] 开始匹配查询: '{query}'")
        print(f"[调试-HARD-RULE] query repr: {repr(query)}")  # 🔥 打印精确内容
        print(f"[调试-HARD-RULE] query type: {type(query)}, len={len(query)}")
        
        # 🔥 检查每个字符的Unicode码点
        if len(query) > 10:
            sample_chars = query[5:15]
            char_codes = [f'{c}({ord(c):04X})' for c in sample_chars]
            print(f"[调试-HARD-RULE] 字符码点(5-14): {char_codes}")
        
        print(f"[RULE-DEBUG] match() called with query='{query}' (len={len(query)})")
        
        # 规则 1：建筑列表查询
        bl_match = any(kw in query for kw in self.BUILDING_LIST_KEYWORDS)
        print(f"[RULE-DEBUG] Rule1 (building_list): matched={bl_match}")
        if bl_match:
            return RouteResult(
                layer=RouteLayer.STATIC_RULE,
                action="list_buildings",
                confidence=1.0,
                response="building_list"
            )

        # 🔥 规则 1.5：元数据/系统信息查询（字段、时间范围、schema等）
        md_match = any(kw in query for kw in self.METADATA_QUERY_KEYWORDS)
        print(f"[RULE-DEBUG] Rule1.5 (metadata_query): matched={md_match}")
        if md_match:
            # 判断具体是哪类元数据查询
            if any(kw in query for kw in ["字段", "指标", "参数", "监控"]):
                metadata_type = "fields"
            elif any(kw in query for kw in ["时间", "范围", "起止", "最早", "最新", "多久"]):
                metadata_type = "timerange"
            elif any(kw in query for kw in ["系统", "数据库", "表结构", "schema", "信息"]):
                metadata_type = "system_info"
            else:
                metadata_type = "general"

            return RouteResult(
                layer=RouteLayer.STATIC_RULE,
                action="metadata_query",
                confidence=0.95,
                params={"query_type": metadata_type, "original_query": query},
                response="metadata"
            )
        
        # 规则 2：清空历史
        cl_match = any(kw in query for kw in self.CLEAR_KEYWORDS)
        print(f"[RULE-DEBUG] Rule2 (clear_history): matched={cl_match}")
        if cl_match:
            return RouteResult(
                layer=RouteLayer.STATIC_RULE,
                action="clear_history",
                confidence=1.0,
                response="history_cleared"
            )
        
        # 规则 3：知识库查询检测（优先于数据查询，避免"这个数据有问题吗"被误匹配）
        kq_result = self._is_knowledge_query(query)
        print(f"[RULE-DEBUG] Rule3 (knowledge_check): matched={kq_result}")
        if kq_result:
            return None  # 返回 None 让路由器走第零层知识库处理
        
        # 规则 4：追问判断（优先于数据查询）
        fu_result = self._is_followup(query)
        print(f"[RULE-DEBUG] Rule4 (followup): matched={fu_result}")
        if fu_result:
            return RouteResult(
                layer=RouteLayer.STATIC_RULE,
                action="followup",
                confidence=0.9,
                params={"is_followup": True}
            )
        
        # 规则 5：数据查询（正则匹配）- 选择最具体的匹配（参数最多的）
        best_match = None
        best_params_count = 0

        for idx, pattern_config in enumerate(self.DATA_QUERY_PATTERNS):
            print(f"[调试-LOOP] [{idx}] Checking pattern: {pattern_config['name']}")
            print(f"[调试-LOOP] [{idx}] Regex: {pattern_config['pattern'][:80]}...")  # 打印正则前80字符
            match = re.search(pattern_config["pattern"], query, re.IGNORECASE)
            
            # 🔥 调试：对于 full_query 和 date_query，额外打印匹配结果
            if pattern_config['name'] in ['full_query', 'date_query']:
                print(f"[调试-LOOP] [{idx}] 🔍 re.search result: {match}")
                if match:
                    print(f"[调试-LOOP] [{idx}] 📋 match.groups(): {match.groups()}")
                else:
                    # 尝试不使用 IGNORECASE 标志
                    match2 = re.search(pattern_config["pattern"], query)
                    print(f"[调试-LOOP] [{idx}] 🔍 re.search (no flag): {match2}")
            
            if match:
                print(f"[调试-LOOP] [{idx}] ✅ Pattern '{pattern_config['name']}' MATCHED!")
                groups = match.groups()
                params = {}
                for i, group_name in enumerate(pattern_config["groups"]):
                    if group_name != "_" and i < len(groups):
                        params[group_name] = groups[i]

                metric = self._identify_metric(query)
                if metric:
                    params["metric"] = metric

                print(f"[调试] 正则模式 '{pattern_config['name']}' 匹配成功，参数: {params}")

                # 🔥 特殊处理：相对时间汇总查询（如"今日能耗"）→ 直接引导澄清
                if pattern_config.get("is_relative_time"):
                    print(f"[调试] 🔍 检测到相对时间查询，需要澄清")
                    time_expr = params.get("time_expr", "")
                    metric_hint = params.get("metric_hint", "")

                    return RouteResult(
                        layer=RouteLayer.STATIC_RULE,
                        action="clarification_needed",
                        confidence=0.3,
                        params={
                            "query_type": "relative_time_summary",
                            "time_expr": time_expr,
                            "metric_hint": metric_hint,
                            "original_query": query
                        },
                        response="clarification_needed"
                    )

                # 🔥 特殊处理：月份级趋势/分析查询 → 直接交给 LLM 智能处理
                if pattern_config.get("is_monthly_trend"):
                    print(f"[调试] 🔍 检测到月份级查询，检查是否包含趋势/分析意图")

                    building = params.get("building", "")
                    metric_or_action = params.get("metric_or_action", "")  # 如 "能耗趋势"

                    # 定义趋势/分析关键词
                    trend_analysis_keywords = [
                        "趋势", "变化", "走势", "分析", "情况", "如何",
                        "怎么样", "正常吗", "异常", "对比", "比较",
                        "汇总", "统计", "报告", "明细"
                    ]

                    # 检查是否包含趋势/分析意图
                    # 🔥 修复：确保 metric_or_action 不是 None
                    safe_metric_or_action = metric_or_action or ""
                    has_trend_intent = any(kw in safe_metric_or_action for kw in trend_analysis_keywords) or \
                                       any(kw in query for kw in trend_analysis_keywords)

                    if has_trend_intent and building:
                        # ✅ 有建筑名 + 趋势/分析意图 → 直接交给 LLM 处理
                        print(f"[调试] ✅ 检测到趋势/分析意图 ('{metric_or_action}')，提交给 LLM 智能处理")

                        return RouteResult(
                            layer=RouteLayer.STATIC_RULE,
                            action="llm_smart_query",  # 🔥 新动作：LLM 智能查询
                            confidence=0.7,  # 中等置信度，让 LLM 决定具体怎么做
                            params={
                                "building": building,
                                "year": params.get("year", ""),
                                "month": params.get("month", ""),
                                "raw_query": query,
                                "user_intent": metric_or_action.strip() if metric_or_action else "数据查询",
                                "processing_hint": "需要智能解析指标并生成聚合查询或分析"
                            }
                        )
                    elif has_trend_intent and not building:
                        # ❌ 有趋势意图但无建筑名 → 引导澄清
                        return RouteResult(
                            layer=RouteLayer.STATIC_RULE,
                            action="clarification_needed",
                            confidence=0.3,
                            params={
                                "query_type": "trend_without_building",
                                "raw_expression": metric_or_action,
                                "original_query": query
                            },
                            response="clarification_needed"
                        )
                    else:
                        # 无趋势意图，可能是简单查询（如"Caspian 2021年7月的数据"）
                        # 尝试识别指标，如果可以就硬规则处理
                        identified_metric = self._identify_metric(query)
                        if identified_metric:
                            params["metric"] = identified_metric
                            if not params.get("year"):
                                from datetime import datetime
                                params["year"] = str(datetime.now(). year)

                            return RouteResult(
                                layer=RouteLayer.STATIC_RULE,
                                action="query_data",
                                confidence=0.8,
                                params=params
                            )
                        else:
                            # 无法识别指标，也交给 LLM
                            return RouteResult(
                                layer=RouteLayer.STATIC_RULE,
                                action="llm_smart_query",
                                confidence=0.6,
                                params=params
                            )

                # 验证是否真的是有效的建筑名
                building = params.get("building", "")
                known_buildings = ["Baikal", "Aral", "Caspian", "Huron", "Erie", "Ladoga",
                                  "Superior", "Titicaca", "Victoria", "Winnipeg", "Vostok",
                                  "Michigan", "Ontario", "Malawi"]

                # 常见的非建筑名前缀/词汇（这些词不可能是建筑名）
                non_building_prefixes = [
                    "帮我", "查一下", "查询", "请", "我想", "我要", "能否",
                    "可以", "怎么", "如何", "什么", "哪个", "哪些", "这个",
                    "那个", "最近", "上一周", "本周", "今天", "昨天", "说明",
                    "解释", "分析", "看看", "告诉我", "列出", "显示", "给出",
                    "对比", "比较", "统计", "汇总", "计算"
                ]

                # 判断是否为有效建筑名
                is_valid_building = self._validate_building_name(
                    building, known_buildings, non_building_prefixes, pattern_config["name"]
                )

                print(f"[调试] 建筑名验证: building='{building}', valid={is_valid_building}")

                if not is_valid_building:
                    continue

                # 🔥 关键修复：选择参数最多的匹配（最具体的模式）
                current_params_count = len([v for v in params.values() if v])
                if current_params_count > best_params_count:
                    best_match = (pattern_config, params)
                    best_params_count = current_params_count
                    print(f"[调试] ✅ 更优匹配: {pattern_config['name']} ({current_params_count}个参数)")
        
        if best_match:
            pattern_config, params = best_match
            print(f"[调试] ✅ 硬规则最终匹配: {pattern_config['name']}")
            
            # 🔥 新增：低置信度查询检测 - 需要澄清的场景
            if self._needs_clarification(pattern_config["name"], params, query):
                print(f"[调试] ⚠️ 低置信度查询，需要用户澄清")
                return RouteResult(
                    layer=RouteLayer.STATIC_RULE,
                    action="clarification_needed",
                    confidence=0.3,  # 低置信度
                    params=params  # 传递已提取的参数（如建筑名）
                )
            
            return RouteResult(
                layer=RouteLayer.STATIC_RULE,
                action="query_data",
                confidence=0.95,
                params=params
            )
        else:
            print(f"[调试-HARD-RULE] ⚠️ 未找到有效匹配，返回 None")
            return None
    
    def _identify_metric(self, query: str) -> Optional[str]:
        """识别查询的指标类型"""
        for metric, keywords in self.METRIC_KEYWORDS.items():
            if any(kw in query for kw in keywords):
                return metric
        return None
    
    def _is_followup(self, query: str) -> bool:
        """判断是否是追问（针对上次查询结果的评价）"""
        
        # 如果包含知识库查询关键词，不是追问（直接引用类变量）
        if any(kw in query for kw in self.KNOWLEDGE_KEYWORDS):
            return False
        
        # 追问必须是短问题（< 15 字）且包含指代词
        followup_pronouns = ["这个", "那个", "它", "这数据", "那数据", "这个数", "那个数"]
        if len(query) < 15 and any(kw in query for kw in followup_pronouns):
            return True
        
        # 包含评价性关键词 + 指代词，且没有具体建筑名
        eval_keywords = ["高吗", "低吗", "正常吗", "异常", "有问题吗", "合理吗", "怎么样"]
        has_eval = any(kw in query for kw in eval_keywords)
        has_pronoun = any(kw in query for kw in ["这", "那", "它"])
        has_building = any(b.lower() in query.lower() for b in 
                          ["Baikal", "Aral", "Caspian", "Huron", "Erie", "Ladoga", "Superior",
                           "Titicaca", "Victoria", "Winnipeg", "Vostok", "Michigan", "Ontario", "Malawi"])
        
        return has_eval and has_pronoun and not has_building
    
    def _needs_clarification(self, pattern_name: str, params: dict, query: str) -> bool:
        """
        检测是否需要用户澄清查询意图
        
        触发条件：
        1. simple_query 模式且缺少关键信息（日期/指标）
        2. 输入过于简短或模糊
        3. 可能导致返回大量无关数据
        
        Args:
            pattern_name: 匹配的模式名称
            params: 提取的参数
            query: 原始查询文本
        
        Returns:
            True 如果需要澄清，False 否则
        """
        
        # 场景1: simple_query 模式 - 只有建筑名，没有日期和具体指标
        if pattern_name == "simple_query":
            building = params.get("building", "")
            metric = params.get("metric")
            
            # 只有建筑名，没有任何其他信息
            has_date_info = any(kw in query for kw in [
                "年", "月", "日", "今天", "昨天", "最近", 
                "上午", "下午", "晚上", "本周", "上月"
            ])
            
            # 如果输入只是建筑名（或建筑名+很少的修饰词）
            query_length = len(query.strip())
            
            # 条件A：纯建筑名（如"Ontario"、"Caspian"）
            if query_length <= 15 and building and not metric and not has_date_info:
                print(f"[调试-CLARIFY] 场景A: 纯建筑名查询 '{query}' (长度={query_length})")
                return True
            
            # 条件B：建筑名+模糊词但无具体需求（如"Caspian的数据"、"Ontario情况"）
            vague_keywords = ["数据", "情况", "信息", "详情", "记录", "的"]
            has_vague = any(kw in query for kw in vague_keywords)
            if query_length <= 20 and building and has_vague and not metric and not has_date_info:
                print(f"[调试-CLARIFY] 场景B: 模糊查询 '{query}' (长度={query_length})")
                return True
        
        # 场景2: 有日期但无指标（可能返回大量字段）
        if pattern_name in ["date_query", "full_query"]:
            metric = params.get("metric")
            if not metric:
                # 检查是否有明确的指标关键词
                metric_keywords = ["电耗", "用电", "电量", "水耗", "用水", "水量", 
                                  "COP", "效率", "制冷", "温度", "能耗"]
                has_metric = any(kw in query for kw in metric_keywords)
                if not has_metric:
                    print(f"[调试-CLARIFY] 场景C: 有日期但无指标 '{query}'")
                    return True  # 可选：也可以允许这种情况
        
        # 默认：不需要澄清
        return False
    
    # 知识库查询关键词（全面的运维/操作/故障场景）
    KNOWLEDGE_KEYWORDS = [
        # 故障处理类
        "怎么处理", "如何处理", "怎么办", "怎么解决", "如何解决",
        "出了点问题", "有问题", "坏了", "不工作", "失效",
        "报警", "异常", "报错", "错误", "故障",
        
        # 设备相关
        "空调", "外机", "冷水机组", "水泵", "风机",
        "设备", "机器", "系统", "机组", "控制器",
        
        # 操作咨询类
        "怎么操作", "如何操作", "怎么做", "该怎么办",
        "操作步骤", "流程", "方法", "步骤",
        
        # 维护保养类
        "维修", "维护", "保养", "检查", "检修",
        "漏水", "漏电", "过热", "噪音", "振动",
        
        # 概念定义类
        "是什么", "什么是", "定义", "概念", "原理",
        "为什么", "原因", "怎么回事", "如何",
        
        # 标准规范类
        "标准", "规范", "要求", "规定", "参数",
        
        # 优化建议类
        "建议", "优化", "改进", "节能", "省电",
        "降低", "提高", "调整", "设置"
    ]
    
    def _is_knowledge_query(self, query: str) -> bool:
        """判断是否是知识库查询"""
        return any(kw in query for kw in self.KNOWLEDGE_KEYWORDS)
    
    def _validate_building_name(self, building: str, known_buildings: list, 
                                non_building_prefixes: list, pattern_name: str) -> bool:
        """
        验证提取的建筑名称是否有效
        
        Args:
            building: 正则提取的建筑名字符串
            known_buildings: 已知建筑名列表
            non_building_prefixes: 非建筑名前缀/词汇列表
            pattern_name: 当前匹配的模式名称
        
        Returns:
            True 如果是有效的建筑名，False 否则
        """
        
        # 规则 1：长度检查 - 建筑名不能太长（simple_query 模式下）
        if pattern_name == "simple_query":
            # 对于 simple_query 模式，提取的字符串应该就是建筑名本身
            # 真正的建筑名通常不会超过 15 个字符
            if len(building) > 15:
                return False
        
        # 规则 2：检查是否包含非建筑名前缀/词汇
        building_lower = building.lower()
        for prefix in non_building_prefixes:
            if prefix in building_lower:
                return False
        
        # 规则 3：对于 simple_query 模式，要求精确或近似匹配已知建筑名
        if pattern_name == "simple_query":
            # 方案 A：精确匹配（忽略大小写）
            if building_lower in [b.lower() for b in known_buildings]:
                return True
            
            # 方案 B：known_buildings 中的某个建筑名是提取字符串的前缀
            # 例如：提取 "Caspian最近一周" → "Caspian" 是前缀 ✓
            for known in known_buildings:
                if building_lower.startswith(known.lower()):
                    # 但要确保提取的字符串不会太长（最多比建筑名多2-3个字符）
                    if len(building) <= len(known) + 3:
                        return True
            
            # 方案 C：首字母大写的英文单词（3-10个字符），看起来像建筑名
            if (len(building) >= 3 and len(building) <= 10 and 
                building[0].isupper() and building.isalpha() and
                not any(kw in building_lower for kw in ["这个", "那个", "什么", "怎么", "如何"])):
                return True
            
            # 其他情况都不算有效建筑名
            return False
        
        # 规则 4：对于其他模式（full_query, date_query 等），验证相对宽松
        # 因为这些模式已经通过正则约束了格式（建筑+日期+时间）
        if len(building) < 2:
            return False
        
        # 必须以大写字母开头 或 包含已知建筑名
        if not (building[0].isupper() or 
                any(b.lower() in building_lower for b in known_buildings)):
            return False
        
        # 不能包含明显的非建筑名词汇
        invalid_keywords = ["这个", "那个", "什么", "怎么", "如何", "帮我", "查一下"]
        if any(kw in building_lower for kw in invalid_keywords):
            return False
        
        return True


# ==================== 第二层：语义路由层 ====================

class SemanticRouter:
    """
    语义路由层 - 基于 Embedding 的意图匹配
    
    职责：
    - 计算查询的意图向量
    - 匹配预定义的意图库
    - 高置信度匹配直接路由到对应处理函数
    """
    
    # 预定义意图模板（带示例）
    INTENT_TEMPLATES = {
        "data_analysis": {
            "description": "数据分析/异常检测/趋势分析",
            "examples": [
                "这个数据正常吗",
                "有没有异常",
                "为什么这么高",
                "分析一下趋势",
                "对比两个建筑",
                "数据有什么问题",
                "合理吗",
                "怎么样"
            ],
            "action": "analyze_data",
            "need_cloud": True
        },
        "knowledge_query": {
            "description": "知识库查询/概念解释",
            "examples": [
                "COP是什么",
                "什么是力调电费",
                "解释一下",
                "什么是异常检测",
                "标准是什么"
            ],
            "action": "query_knowledge",
            "need_cloud": True
        },
        "report_generation": {
            "description": "报告生成/策略建议",
            "examples": [
                "生成报告",
                "节能建议",
                "优化方案",
                "下个月策略",
                "改进建议"
            ],
            "action": "generate_report",
            "need_cloud": True
        },
        "simple_calculation": {
            "description": "简单计算/汇总统计",
            "examples": [
                "平均电耗",
                "总用水量",
                "最大值",
                "最小值",
                "统计一下"
            ],
            "action": "calculate",
            "need_cloud": False
        }
    }
    
    def __init__(self):
        self.embedder = None
        self.intent_vectors = {}
        self._init_embedder()
    
    def _init_embedder(self):
        """初始化 Embedding 模型"""
        try:
            from sentence_transformers import SentenceTransformer
            self.embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            self._build_intent_vectors()
            print("[语义路由] Embedding 模型加载成功")
        except ImportError:
            print("[语义路由] sentence-transformers 未安装，使用关键词匹配降级")
            self.embedder = None
        except Exception as e:
            print(f"[语义路由] Embedding 模型加载失败：{e}，使用关键词匹配降级")
            self.embedder = None
    
    def _build_intent_vectors(self):
        """构建意图向量库"""
        if not self.embedder:
            return
        
        for intent_name, template in self.INTENT_TEMPLATES.items():
            examples = template["examples"]
            vectors = self.embedder.encode(examples)
            self.intent_vectors[intent_name] = vectors
    
    def route(self, query: str) -> RouteResult:
        """
        语义路由
        
        Returns:
            RouteResult（置信度 < 0.75 时返回 None，进入下一层）
        """
        if not self.embedder:
            # 降级：使用关键词匹配
            return self._keyword_fallback(query)
        
        try:
            query_vec = self.embedder.encode(query)
            
            best_intent = None
            best_score = 0
            
            for intent_name, vectors in self.intent_vectors.items():
                # 计算与所有示例的平均相似度
                scores = self._cosine_similarity(query_vec, vectors)
                avg_score = scores.mean()
                max_score = scores.max()
                
                # 使用加权分数（平均 + 最大）
                combined_score = 0.4 * avg_score + 0.6 * max_score
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_intent = intent_name
            
            # 阈值判断
            if best_score >= 0.75 and best_intent:
                template = self.INTENT_TEMPLATES[best_intent]
                return RouteResult(
                    layer=RouteLayer.SEMANTIC,
                    action=template["action"],
                    confidence=best_score,
                    need_cloud=template["need_cloud"],
                    params={"intent": best_intent}
                )
            
            return None
            
        except Exception as e:
            print(f"[语义路由] 计算失败：{e}")
            return self._keyword_fallback(query)
    
    def _cosine_similarity(self, a, b):
        """计算余弦相似度"""
        import numpy as np
        if b.ndim == 1:
            b = b.reshape(1, -1)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b, axis=1)
        return np.dot(b, a) / (norm_b * norm_a)
    
    def _keyword_fallback(self, query: str) -> Optional[RouteResult]:
        """关键词匹配降级方案 - 🔥 优化版：区分查询和分析"""
        
        # 🔥 新增：先检查是否包含明确的查询要素（建筑/日期/指标）
        # 如果有明确查询要素，即使包含分析词，也优先作为数据查询
        has_building = any(b.lower() in query.lower() for b in 
                          ["Baikal", "Aral", "Caspian", "Huron", "Erie", "Ladoga",
                           "Superior", "Titicaca", "Victoria", "Winnipeg", "Vostok",
                           "Michigan", "Ontario", "Malawi"])
        has_date = any(kw in query for kw in ["年", "月", "日", "今天", "昨天", "本周", "上月"])
        has_metric = any(kw in query for kw in 
                       ["电耗", "用电", "电量", "水耗", "用水", "空调", "能耗", 
                        "温度", "湿度", "COP", "效率", "人员"])
        
        # 🔥 关键修复：如果有明确查询要素，强制作为数据查询
        if has_building and (has_date or has_metric):
            print(f"[语义路由-降级] 检测到明确查询要素 (building={has_building}, date={has_date}, metric={has_metric})")
            print(f"[语义路由-降级] 强制归类为 data_query，忽略分析关键词")
            
            return RouteResult(
                layer=RouteLayer.SEMANTIC,
                action="query_data",  # ✅ 明确的数据查询
                confidence=0.8,
                need_cloud=False,
                params={"intent": "data_query_with_analysis_hint", "method": "keyword_fallback"}
            )
        
        # 原有的分析类关键词检测（只在无明确查询要素时生效）
        analysis_keywords = ["异常", "正常吗", "高吗", "低吗", "为什么", "分析", 
                           "趋势", "对比", "比较", "合理吗", "问题", "怎么样"]
        if any(kw in query for kw in analysis_keywords):
            return RouteResult(
                layer=RouteLayer.SEMANTIC,
                action="analyze_data",
                confidence=0.7,
                need_cloud=True,
                params={"intent": "data_analysis", "method": "keyword_fallback"}
            )
        
        # 知识类关键词
        knowledge_keywords = ["是什么", "解释", "定义", "概念", "标准", "规范"]
        if any(kw in query for kw in knowledge_keywords):
            return RouteResult(
                layer=RouteLayer.SEMANTIC,
                action="query_knowledge",
                confidence=0.7,
                need_cloud=True,
                params={"intent": "knowledge_query", "method": "keyword_fallback"}
            )
        
        return None


# ==================== 第三层：本地推理层 ====================

class LocalSLMRouter:
    """
    本地推理层 - 使用 7B 模型进行意图解析和参数提取
    
    职责：
    - 解析复杂查询意图
    - 提取查询参数（建筑、时间、指标）
    - 生成 SQL 查询语句
    - 简单数据计算和汇总
    
    注意：SLM 只负责"意图解析+参数提取"，实际计算走 Python 函数
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "qwen2.5:7b"):
        self.ollama_url = ollama_url
        self.model = model
    
    def process(self, query: str, context: dict = None) -> RouteResult:
        """
        本地模型处理
        
        Returns:
            RouteResult
        """
        # 构建结构化提示词
        prompt = self._build_intent_prompt(query, context)
        
        try:
            response = self._call_ollama(prompt)
            result = self._parse_response(response)
            
            if result:
                return RouteResult(
                    layer=RouteLayer.LOCAL_SLM,
                    action=result.get("action", "query_data"),
                    confidence=0.8,
                    sql=result.get("sql", ""),
                    params=result.get("params", {}),
                    need_cloud=result.get("need_cloud", False)
                )
            
            # 解析失败，默认查询
            return RouteResult(
                layer=RouteLayer.LOCAL_SLM,
                action="query_data",
                confidence=0.5,
                params={"raw_query": query}
            )
            
        except Exception as e:
            print(f"[本地推理] 处理失败：{e}")
            return RouteResult(
                layer=RouteLayer.LOCAL_SLM,
                action="query_data",
                confidence=0.3,
                params={"raw_query": query, "error": str(e)}
            )
    
    def _build_intent_prompt(self, query: str, context: dict = None) -> str:
        """构建意图分析提示词 - 🔥 优化版：强化指标识别"""
        context_info = ""
        if context and context.get("last_result"):
            context_info = f"\n上次查询结果：{context['last_result']}"

        prompt = f"""# 角色
你是一个建筑能源管理系统的智能查询解析器。

# 任务
分析用户问题，提取关键信息，生成正确的 SQL 查询。

# 数据库表结构 (energy_reports)
- timestamp: 时间戳 (格式: 'YYYY-MM-DD HH:MM:SS')
- building_id: 建筑编号
- electricity_kwh: 电耗 (单位: kWh) - ⭐ 最常用
- water_m3: 水耗 (单位: m³)
- hvac_kwh: 空调能耗 (单位: kWh)
- chw_supply_temp: 冷冻水供水温度 (°C)
- chw_return_temp: 冷冻水回水温度 (°C)
- outdoor_temp: 室外温度 (°C)
- humidity_pct: 湿度 (%)
- occupancy_density: 人员密度 (人/100m²)

# 关键规则（必须遵守）
1. **默认指标**: 如果用户提到"能耗"、"电"、"用电"但未明确指定，**默认使用 electricity_kwh**
2. **趋势/分析查询**: 如果用户问"趋势"、"变化"、"情况"，需要：
   - 选择最相关的指标（优先级：electricity_kwh > water_m3 > hvac_kwh）
   - 生成按时间排序的 SQL（ORDER BY timestamp）
   - 不要选择 occupancy_density 除非用户明确提到"人员"
3. **时间范围**: 
   - "某年某月" → 该月1号到月底
   - "今天/昨日" → 具体日期
   - 无日期 → 使用最近的数据

# 输出格式
只返回 JSON，不要其他内容：
{{
    "action": "query_data",
    "sql": "SELECT timestamp, [正确字段名] FROM energy_reports WHERE building_id ILIKE '%[建筑名]%' AND timestamp >= '[开始时间]' AND timestamp <= '[结束时间]' ORDER BY timestamp",
    "params": {{
        "building": "建筑名",
        "date": "YYYY-MM-DD" 或 null,
        "metric": "[数据库字段名]"
    }},
    "need_cloud": false
}}

# 示例

## 示例 1: 能耗趋势查询
问题："Caspian 2021年7月的能耗趋势"
{{"action": "query_data", "sql": "SELECT timestamp, electricity_kwh FROM energy_reports WHERE building_id ILIKE '%Caspian%' AND timestamp >= '2021-07-01 00:00:00' AND timestamp <= '2021-07-31 23:59:59' ORDER BY timestamp", "params": {{"building": "Caspian", "date": "2021-07", "metric": "electricity_kwh"}}, "need_cloud": false}}

## 示例 2: 单日具体查询
问题："Michigan 5月7日上午6点的电耗是多少"
{{"action": "query_data", "sql": "SELECT timestamp, electricity_kwh FROM energy_reports WHERE building_id ILIKE '%Michigan%' AND timestamp >= '2021-05-07 06:00:00' AND timestamp <= '2021-05-07 06:59:59'", "params": {{"building": "Michigan", "date": "2021-05-07", "hour": 6, "metric": "electricity_kwh"}}, "need_cloud": false}}

## 示例 3: 分析类问题
问题："这个数据正常吗"
{{"action": "analyze_data", "sql": "", "params": {{}}, "need_cloud": true}}

# 当前问题
问题：{query}{context_info}

JSON:"""
        return prompt
    
    def _call_ollama(self, prompt: str) -> str:
        """调用 Ollama 本地模型"""
        try:
            print(f"[本地推理] 开始调用 Ollama (model={self.model})...")
            start_time = time.time()
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.1,  # 🔥 修复：改回 0.1（0 可能导致某些模型卡住）
                    "num_predict": 500   # 🔥 新增：限制输出长度防止过长响应
                },
                timeout=15  # 🔥 关键修复：从 60s 改为 15s 快速超时
            )
            
            elapsed = time.time() - start_time
            result = response.json().get("response", "")
            print(f"[本地推理] Ollama 调用成功 ({elapsed:.2f}s), 响应长度: {len(result)}")
            
            return result
            
        except requests.exceptions.Timeout:
            print(f"[本地推理] ❌ Ollama 超时 (>15秒)，跳过本地推理")
            raise Exception("Ollama 超时")
        except Exception as e:
            print(f"[本地推理] ❌ Ollama 调用失败：{e}")
            raise Exception(f"Ollama 调用失败：{e}")
    
    def _parse_response(self, response: str) -> Optional[dict]:
        """解析模型响应"""
        try:
            # 提取 JSON
            match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:
            pass
        return None


# ==================== 第四层：云端增强层 ====================

class CloudLLMRouter:
    """
    云端增强层 - 处理复杂分析任务
    
    职责：
    - 长周期能源分析
    - 复杂自动化场景规划
    - 知识库检索增强回答
    - 数据异常深度分析
    """
    
    def __init__(self, api_key: str, api_url: str, model: str = "qwen-plus"):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
    
    def process(self, query: str, data: str = "", kb_context: str = "", 
                kb_sources: list = None) -> str:
        """
        云端模型处理
        
        Args:
            query: 用户问题
            data: 查询到的数据
            kb_context: 知识库上下文
            kb_sources: 知识库来源
        
        Returns:
            云端模型的回答
        """
        # 构建提示词
        prompt = self._build_prompt(query, data, kb_context)
        
        try:
            response = requests.post(
                self.api_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=60
            )
            
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
            raise Exception(f"云端模型调用失败：{e}")
    
    def _build_prompt(self, query: str, data: str, kb_context: str) -> str:
        """构建云端提示词"""
        prompt = """你是建筑能源管理专家。请根据以下数据回答用户问题。

重要要求：
1. 只返回纯文本，不要使用任何 HTML 标签（如 <sub>、<sup>、<br> 等）
2. 使用 Markdown 格式（**加粗**、*斜体*、### 标题）
3. 公式用纯文本表示，如 COP_cooling = Q_c / W_net
4. 专业、简洁、基于数据回答

"""
        if data:
            prompt += f"=== 查询数据 ===\n{data}\n\n"
        
        if kb_context:
            prompt += f"=== 知识库参考 ===\n{kb_context}\n\n"
        
        prompt += f"=== 用户问题 ===\n{query}\n\n"
        
        return prompt


# ==================== Fail-safe 保护机制 ====================

class FailSafeGuard:
    """
    安全失败保护机制
    
    职责：
    - 监控云端服务健康状态
    - 自动降级到本地模式
    - 记录系统状态
    """
    
    def __init__(self, cloud_health_url: str = None, check_interval: int = 60):
        self.cloud_health_url = cloud_health_url
        self.check_interval = check_interval
        self.cloud_available = True
        self.fallback_mode = False
        self.last_check_time = 0
        self.status = SystemStatus()
    
    def check_cloud_health(self) -> bool:
        """检查云端服务健康状态"""
        current_time = time.time()
        
        # 避免频繁检查
        if current_time - self.last_check_time < self.check_interval:
            return self.cloud_available
        
        self.last_check_time = current_time
        
        if not self.cloud_health_url:
            # 没有健康检查 URL，默认云端可用
            return True
        
        try:
            response = requests.get(self.cloud_health_url, timeout=5)
            self.cloud_available = response.status_code == 200
        except Exception:
            self.cloud_available = False
        
        self._update_status()
        return self.cloud_available
    
    def execute_with_fallback(self, primary_func, fallback_func, *args, **kwargs):
        """
        带降级的执行逻辑
        
        Args:
            primary_func: 主要执行函数（云端）
            fallback_func: 降级执行函数（本地）
        
        Returns:
            执行结果
        """
        if self.cloud_available:
            try:
                result = primary_func(*args, **kwargs)
                self.cloud_available = True  # 成功则标记可用
                return result
            except Exception as e:
                print(f"[FailSafe] 云端执行失败：{e}，降级到本地模式")
                self.cloud_available = False
        
        # 本地降级模式
        self.fallback_mode = True
        self._update_status()
        return fallback_func(*args, **kwargs)
    
    def get_system_mode(self) -> str:
        """获取当前系统模式"""
        if self.fallback_mode:
            return "本地降级模式"
        elif self.cloud_available:
            return "云边协同模式"
        else:
            return "正常模式"
    
    def get_status(self) -> dict:
        """获取系统状态"""
        return {
            "mode": self.get_system_mode(),
            "cloud_available": self.cloud_available,
            "fallback_mode": self.fallback_mode,
            "total_requests": self.status.total_requests,
            "layer_stats": self.status.layer_stats
        }
    
    def record_request(self, layer: RouteLayer):
        """记录请求统计"""
        self.status.total_requests += 1
        self.status.layer_stats[layer.value] = self.status.layer_stats.get(layer.value, 0) + 1
    
    def _update_status(self):
        """更新系统状态"""
        self.status.cloud_available = self.cloud_available
        self.status.mode = self.get_system_mode()


# ==================== 云边协同路由分发器（主入口） ====================

class CloudEdgeRouter:
    """
    云边协同路由分发器
    
    整合四层路由逻辑，提供统一的查询入口
    """
    
    def __init__(self, config: dict = None):
        # 🔥 版本标识：确认新代码已加载
        print("\n" + "="*60)
        print("🚀 CloudEdgeRouter v2.3-ENHANCED-CONTEXT 已加载")
        print("   ✅ 新功能：完整多轮对话上下文记忆 (最多20轮)")
        print("   ✅ 新功能：智能实体提取（建筑/时间/指标）")
        print("   ✅ 新功能：上下文压缩和总结")
        print("   ✅ 优化：Ollama Prompt 强化指标识别")
        print("   ✅ 修复：字段映射统一化")
        print("="*60 + "\n")

        config = config or {}

        # 初始化各层路由器
        self.static_rule = StaticRuleEngine()
        self.semantic_router = SemanticRouter()
        self.local_slm = LocalSLMRouter(
            ollama_url=config.get("ollama_url", "http://localhost:11434"),
            model=config.get("local_model", "qwen2.5:7b")
        )
        self.cloud_llm = CloudLLMRouter(
            api_key=config.get("cloud_api_key", ""),
            api_url=config.get("cloud_api_url", ""),
            model=config.get("cloud_model", "qwen-plus")
        )

        # 初始化 Fail-safe
        self.failsafe = FailSafeGuard(
            cloud_health_url=config.get("cloud_health_url"),
            check_interval=config.get("health_check_interval", 60)
        )

        # 初始化知识库
        self.knowledge_base = None
        self._init_knowledge_base(config.get("chroma_path", r"E:\openclaw-project\workspace\Fuwu\chroma_db"))

        # 🔥 增强版上下文记忆系统 v2.0
        self.MAX_HISTORY_LENGTH = 20       # 最大保存历史轮数
        self.MAX_CONTEXT_TOKENS = 2000     # 注入 LLM 的最大 token 数
        self.context = {
            # 基础信息（保持向后兼容）
            "last_building": None,
            "last_date": None,
            "last_result": None,
            # 🔥 新增：完整对话历史
            "history": [],  # [{"role": "user/assistant", "content": "...", "timestamp": "..."}]
            # 🔥 新增：提取的实体（用于智能上下文）
            "mentioned_buildings": [],  # 所有提及的建筑（去重）
            "mentioned_dates": [],      # 所有提及的日期/时间
            "mentioned_metrics": [],     # 所有提及的指标
            # 🔥 新增：查询结果缓存（支持多次引用）
            "query_results": {},        # {index: {query, result, timestamp}}
            # 🔥 新增：会话元数据
            "session_start": datetime.now().isoformat(),
            "message_count": 0,
            "session_id": None
        }

        # 🔥 实体提取模式（用于从对话中自动识别）
        self.ENTITY_PATTERNS = {
            'buildings': [
                "Baikal", "Aral", "Caspian", "Huron", "Erie", "Ladoga",
                "Superior", "Titicaca", "Victoria", "Winnipeg", "Vostok",
                "Michigan", "Ontario", "Malawi"
            ],
            'metrics': [
                "electricity_kwh", "water_m3", "hvac_kwh",
                "chw_supply_temp", "chw_return_temp", "outdoor_temp",
                "humidity_pct", "occupancy_density",
                # 中文关键词
                "电耗", "用电量", "电量", "电力", "用电",
                "水耗", "用水量", "水量", "用水",
                "空调能耗", "空调用电", "制冷", "制热",
                "供水温度", "回水温度", "室外温度",
                "湿度", "相对湿度", "人员密度", "人数"
            ],
            'date_patterns': [
                r'\d{4}年\d{1,2}月\d{1,2}日',  # 2021年7月21日
                r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',  # 2021-07-21
                r'(?:今|昨|前|大前)天',  # 昨天、前天
                r'(?:上|这|本|下)个?月',  # 上个月、本月
                r'\d{1,2}月',  # 7月
                r'上午|下午|晚上|凌晨',  # 时段
                r'\d{1,2}[::]\d{2}(?:\s*(?:AM|PM|点))?',  # 14:00, 14:30, 2PM
            ]
        }
        
        print("[云边路由] ✅ 增强版上下文记忆系统已初始化")
        print(f"[云边路由]    - 最大历史轮数: {self.MAX_HISTORY_LENGTH}")
        print(f"[云边路由]    - 最大上下文 Token: {self.MAX_CONTEXT_TOKENS}")
        print("[云边路由] 初始化完成")
    
    def _init_knowledge_base(self, chroma_path: str):
        """初始化 ChromaDB 知识库"""
        try:
            import chromadb
            client = chromadb.PersistentClient(path=chroma_path)
            self.knowledge_base = client.get_collection("fuwu_knowledge")
            print(f"[知识库] 已加载 {self.knowledge_base.count()} 个文档块")
        except Exception as e:
            self.knowledge_base = None
            print(f"[知识库] 加载失败：{e}")
    
    def _search_knowledge(self, query: str, n_results: int = 3) -> tuple:
        """搜索知识库，返回 (上下文文本, 来源列表)"""
        if not self.knowledge_base:
            return "", []
        
        try:
            results = self.knowledge_base.query(
                query_texts=[query],
                n_results=n_results
            )
            
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            
            if not documents:
                return "", []
            
            # 构建上下文
            context_parts = []
            sources = []
            for i, (doc, meta) in enumerate(zip(documents, metadatas)):
                source = meta.get("source", f"文档{i+1}") if meta else f"文档{i+1}"
                context_parts.append(f"[{source}] {doc}")
                if source not in sources:
                    sources.append(source)
            
            return "\n\n".join(context_parts), sources
            
        except Exception as e:
            print(f"[知识库] 搜索失败：{e}")
            return "", []
    
    def route(self, query: str) -> dict:
        """
        主路由方法 - 四层过滤逻辑
        
        Args:
            query: 用户查询
        
        Returns:
            处理结果
        """
        start_time = time.time()
        
        # 第零层：知识库查询检测（优先处理）
        if self.static_rule._is_knowledge_query(query):
            print(f"[路由] 第零层：知识库查询")
            return self._handle_knowledge_query(query)
        
        # 第一层：硬规则过滤
        print(f"[路由] 第一层：硬规则过滤")
        rule_result = self.static_rule.match(query)
        if rule_result:
            self.failsafe.record_request(RouteLayer.STATIC_RULE)
            elapsed = time.time() - start_time
            print(f"[路由] 命中硬规则: {rule_result.action} ({elapsed:.3f}s)")
            return self._handle_static_rule(rule_result, query)
        
        # 第二层：语义路由
        print(f"[路由] 第二层：语义路由")
        semantic_result = self.semantic_router.route(query)
        if semantic_result and semantic_result.confidence >= 0.75:
            self.failsafe.record_request(RouteLayer.SEMANTIC)
            elapsed = time.time() - start_time
            print(f"[路由] 命中语义路由: {semantic_result.action} (置信度: {semantic_result.confidence:.2f}, {elapsed:.3f}s)")
            return self._handle_semantic(semantic_result, query)
        
        # 第三层：本地推理
        print(f"[路由] 第三层：本地推理")
        try:
            local_result = self.local_slm.process(query, self.context)
            self.failsafe.record_request(RouteLayer.LOCAL_SLM)
            elapsed = time.time() - start_time
            print(f"[路由] 本地推理完成: {local_result.action} ({elapsed:.3f}s)")
            
            # 判断是否需要降级到云端
            should_use_cloud = False
            
            # 条件1：本地模型明确要求使用云端
            if local_result.need_cloud:
                should_use_cloud = True
                print(f"[路由] 本地模型请求云端协助")
            
            # 条件2：本地结果无效（无SQL、无有效参数、action为fallback）
            is_local_valid = (
                local_result.action in ("query_data", "knowledge", "analysis") and
                (local_result.sql or local_result.params.get("building") or 
                 local_result.params.get("raw_query"))
            )
            
            if not is_local_valid:
                should_use_cloud = True
                print(f"[路由] ⚠️ 本地结果无效，强制降级到云端")
                print(f"[调试]   action={local_result.action}, sql={local_result.sql}, params={local_result.params}")
            
            # 执行降级或本地处理
            if should_use_cloud and self.failsafe.cloud_available:
                return self._handle_cloud(local_result, query)
            elif should_use_cloud and not self.failsafe.cloud_available:
                print(f"[路由] ❌ 云端不可用，返回本地最佳结果")
                return self._handle_local(local_result, query)
            else:
                return self._handle_local(local_result, query)
                
        except Exception as e:
            print(f"[路由] ❌ 本地推理异常: {e}")
            # 本地推理完全失败，尝试云端
            if self.failsafe.cloud_available:
                print(f"[路由] 降级到云端LLM")
                fallback_result = RouteResult(
                    layer=RouteLayer.LOCAL_SLM,
                    action="cloud_fallback",
                    confidence=0.0,
                    params={"raw_query": query, "error": str(e)},
                    need_cloud=True
                )
                return self._handle_cloud(fallback_result, query)
            else:
                return {
                    "response": "抱歉，当前服务繁忙，请稍后重试。",
                    "context": {"layer": "error", "error": str(e)}
                }
    
    def _handle_knowledge_query(self, query: str) -> dict:
        """处理知识库查询"""
        # 搜索知识库
        kb_context, kb_sources = self._search_knowledge(query)
        
        if kb_context:
            print(f"[知识库] 找到 {len(kb_sources)} 个相关文档")
        else:
            print(f"[知识库] 未找到相关文档，使用通用回答")
        
        # 调用云端模型，基于知识库回答
        try:
            reply = self.cloud_llm.process(
                query=query,
                data="",
                kb_context=kb_context,
                kb_sources=kb_sources
            )
            
            return {
                "response": reply,
                "layer": "knowledge_base",
                "action": "knowledge_query",
                "kb_sources": kb_sources
            }
        except Exception as e:
            return {
                "response": f"知识库查询失败：{str(e)}",
                "layer": "error"
            }
    
    def _handle_static_rule(self, result: RouteResult, query: str) -> dict:
        """处理硬规则匹配结果"""
        if result.action == "list_buildings":
            # 🔥 增强版：返回格式化的建筑列表
            buildings = [
                ("Baikal", "贝加尔湖", "办公/商业"),
                ("Aral", "咸海", "工业"),
                ("Caspian", "里海", "综合"),
                ("Huron", "休伦湖", "教育"),
                ("Erie", "伊利湖", "医疗"),
                ("Ladoga", "拉多加湖", "住宅"),
                ("Superior", "苏必利尔湖", "政府"),
                ("Titicaca", "的喀喀湖", "酒店"),
                ("Victoria", "维多利亚湖", "零售"),
                ("Winnipeg", "温尼伯湖", "物流"),
                ("Vostok", "沃斯托克", "研发"),
                ("Michigan", "密歇根湖", "制造"),
                ("Ontario", "安大略湖", "科技"),
                ("Malawi", "马拉维", "文化")
            ]

            # 构建美观的 Markdown 表格响应
            response = f"""🏢 **系统支持查询的建筑列表** (共 {len(buildings)} 栋)

| 编号 | 建筑代码 | 中文名称 | 类型 | 可用数据 |
|------|---------|--------|------|---------|
"""

            for i, (code, name_cn, type_cn) in enumerate(buildings, 1):
                available_data = "✅ 电耗/水耗/空调/温度"
                response += f"| {i} | **{code}** | {name_cn} | {type_cn} | {available_data} |\n"

            response += f"""
💡 **使用示例：**
• 查询单个建筑：`{buildings[2][0]} 今日电耗`
• 对比两栋建筑：`对比 {buildings[0][0]} 和 {buildings[5][0]} 的用水量`
• 批量查询：`所有建筑的 COP 效率`

📊 **快速统计：**
• 总建筑数：**{len(buildings)}** 栋
• 数据时间范围：**2021年全年**
• 采集频率：**每小时** (8,760 条/建筑/年)
"""
            return {
                "response": response,
                "layer": "static_rule",
                "action": "list_buildings",
                "params": {"building_count": len(buildings)}
            }

        elif result.action == "metadata_query":
            # 🔥 新增：处理元数据查询（字段、时间范围等）
            query_type = result.params.get("query_type", "general")

            if query_type == "fields":
                response = """📋 **energy_reports 表可用字段**

| 字段名 | 类型 | 单位 | 说明 | 优先级 |
|--------|------|------|------|--------|
| `timestamp` | TIMESTAMP | - | 时间戳 (YYYY-MM-DD HH:MM:SS) | ⭐⭐⭐ |
| `building_id` | VARCHAR | - | 建筑编号 (14栋) | ⭐⭐⭐ |
| `electricity_kwh` | FLOAT | kWh | **电耗 (最常用)** | ⭐⭐⭐ |
| `water_m3` | FLOAT | m³ | 用水量 | ⭐⭐ |
| `hvac_kwh` | FLOAT | kWh | 空调能耗 | ⭐⭐ |
| `chw_supply_temp` | FLOAT | °C | 冷冻水供水温度 | ⭐ |
| `chw_return_temp` | FLOAT | °C | 冷冻水回水温度 | ⭐ |
| `outdoor_temp` | FLOAT | °C | 室外温度 | ⭐ |
| `humidity_pct` | FLOAT | % | 相对湿度 | ⭐ |
| `occupancy_density` | FLOAT | 人/100m² | 人员密度 | ⭐ |

💡 **常用查询示例：**
• 电耗类：`Caspian 今日电耗`、`Ontario 月度用电趋势`
• 水耗类：`Baikal 昨天用水量`、`Erie 本周水耗统计`
• 温度类：`Huron 室外温度趋势`、`Ladoga 冷冻水温差分析`
"""

            elif query_type == "timerange":
                response = """📅 **数据时间范围信息**

📊 **基础信息**
- **总时间范围：** 2021年1月1日 ~ 2021年12月31日
- **采集粒度：** 每小时 1 条记录
- **建筑数量：** 14 栋
- **总数据量：** 约 147 万条记录

📆 **各月份数据详情**

| 月份 | 天数 | 记录数/建筑 | 说明 |
|------|------|-------------|------|
| 1月 | 31 | 744 | ✅ 完整 |
| 2月 | 28 | 672 | ✅ 完整 |
| ... | ... | ... | ... |
| 7月 | 31 | 744 | ✅ 完整 |
| ... | ... | ... | ... |
| 12月 | 31 | 744 | ✅ 完整 |

💡 **时间查询技巧：**
• 具体日期：`Caspian 2021-07-21 的电耗`
• 月份范围：`Ontario 2021年7月的用水量`
• 季度查询：`Baikal 上午(6-12点) vs 下午(12-18点) 对比`
• 相对时间：`昨日`、`本周`、`上月`（自动转换）
"""

            elif query_type == "system_info":
                response = """🖥️ **BEIMS 建筑能源管理系统 - 系统信息**

📦 **数据库配置**
- **数据库类型：** PostgreSQL
- **主表名称：** `energy_reports`
- **总记录数：** ~1,470,000 条

🏗️ **系统架构**
```
用户请求 → [Vite 前端 :3000]
         ↓
   [FastAPI 后端 :8082]
         ↓
   ┌─────────────────────────┐
   │  CloudEdgeRouter v2.3    │
   │  ├─ 第0层：知识库检测     │
   │  ├─ 第1层：硬规则引擎     │
   │  ├─ 第2层：语义路由       │
   │  ├─ 第3层：本地推理(Ollama)│
   │  └─ 第4层：云端增强(阿里云) │
   └─────────────────────────┘
         ↓
   [PostgreSQL 数据库]
```

🔧 **技术栈**
- **前端：** Vue.js + Vite + AI 聊天浮窗
- **后端：** Python FastAPI + Uvicorn
- **AI 引擎：** Ollama (qwen2.5:7b) + 阿里云 qwen-plus
- **知识库：** ChromaDB 向量数据库
- **内网穿透：** ngrok / Cloudflare Tunnel

📚 **知识库文档**
- Data_Dictionary.md (v2.0)
- 操作手册 & FAQ
"""
            else:
                # general 类型：综合回答
                response = """📚 **BEIMS 系统元数据概览**

**可查询的建筑：** 14 栋 (Baikal, Aral, Caspian, Huron, Erie, Ladoga, Superior, Titicaca, Victoria, Winnipeg, Vostok, Michigan, Ontario, Malawi)

**可用指标：** 电耗(kWh)、用水量(m³)、空调能耗、冷冻水温度、室外温度、湿度、人员密度

**时间范围：** 2021年全年数据，每小时采集

**详细查询：**
- 发送 `有哪些字段` 查看完整字段列表
- 发送 `时间范围是多少` 查看数据时间详情
- 发送 `系统信息` 查看技术架构
"""

            return {
                "response": response,
                "layer": "static_rule",
                "action": "metadata_query",
                "params": {"query_type": query_type}
            }
        
        elif result.action == "clear_history":
            self.context = {
                "last_building": None,
                "last_date": None,
                "last_result": None,
                "history": []
            }
            return {
                "response": "对话历史已清空",
                "layer": "static_rule",
                "action": "clear_history"
            }
        
        elif result.action == "query_data":
            # 硬规则匹配到查询，但仍需生成 SQL
            print(f"[调试] 硬规则参数: {result.params}")
            return self._execute_query(result.params, query)
        
        elif result.action == "followup":
            # 追问，使用上下文
            return self._handle_followup(query)
        
        elif result.action == "clarification_needed":
            # 🔥 新增：需要用户澄清的模糊查询
            return self._generate_clarification_message(result.params, query)

        elif result.action == "llm_smart_query":
            # 🔥 新增：趋势/分析类查询 → 直接交给 LLM 智能处理
            print(f"[路由] 🔥 检测到 llm_smart_query，转交给 LLM 层处理")
            print(f"[路由] 参数: {result.params}")

            # 优先使用 LocalSLM (第三层)，如果失败则降级到 CloudLLM (第四层)
            try:
                if hasattr(self, 'local_slm') and self.local_slm:
                    print(f"[路由] → 尝试 LocalSLM (本地推理)")
                    llm_result = self.local_slm.process(query, self.context)
                    if llm_result and llm_result.action in ["query_data", "analyze_data"]:
                        # LLM 返回了有效结果，继续处理
                        if llm_result.action == "query_data" and llm_result.params.get("sql"):
                            # LLM 生成了 SQL，执行它
                            print(f"[路由] ✅ LocalSLM 生成了 SQL，执行查询")
                            return self._execute_sql(llm_result.params["sql"])
                        else:
                            # 需要云端分析或 LLM 直接返回了答案
                            print(f"[路由] → 需要 CloudLLM 进一步处理")
                            if hasattr(self, 'cloud_llm') and self.cloud_llm:
                                cloud_result = self.cloud_llm.process(query)
                                return {"response": cloud_result, "layer": "cloud_llm", "action": "analyze"}
                    raise Exception("LocalSLM 未返回有效结果")
                else:
                    raise Exception("LocalSLM 不可用")
            except Exception as e:
                print(f"[路由] ❌ LocalSLM 失败: {e}，尝试 CloudLLM")
                try:
                    if hasattr(self, 'cloud_llm') and self.cloud_llm:
                        cloud_result = self.cloud_llm.process(query)
                        return {"response": cloud_result, "layer": "cloud_llm", "action": "analyze"}
                    else:
                        # 云端也不可用，返回友好提示
                        return {
                            "response": f"🤔 您的查询 '{query}' 需要智能分析，但当前 AI 服务暂时不可用。\n\n请尝试：\n• 更具体地指定指标（如'电耗'、'用水量'）\n• 提供更精确的时间范围",
                            "layer": "static_rule",
                            "action": "fallback"
                        }
                except Exception as cloud_err:
                    return {
                        "response": f"❌ AI 服务暂时不可用：{cloud_err}",
                        "layer": "static_rule",
                        "action": "error"
                    }

        return {"response": "无法处理", "layer": "static_rule"}
    
    def _generate_clarification_message(self, params: dict, query: str) -> dict:
        """
        生成友好的澄清消息

        当用户查询过于模糊时（如只输入建筑名），返回友好的提示，
        引导用户提供更具体的信息。

        Args:
            params: 已提取的参数（如建筑名）
            query: 原始查询文本

        Returns:
            包含澄清消息的字典
        """

        # 🔥 新增：处理相对时间查询（如"今日能耗"、"昨日电耗"）
        query_type = params.get("query_type", "")
        if query_type == "relative_time_summary":
            time_expr = params.get("time_expr", "")  # 如"今日"、"昨天"
            metric_hint = params.get("metric_hint", "")  # 如"能耗"

            # 构建时间映射
            time_map = {
                "今日": "今天",
                "今天": "今天",
                "当日": "今天",
                "昨天": "昨天",
                "昨日": "昨天",
                "本周": "本周",
                "这周": "本周",
                "上周": "上周",
                "本月": "本月",
                "这个月": "本月",
                "上月": "上个月"
            }
            time_display = time_map.get(time_expr, time_expr or "某个时间段")

            message = f"""🤔 **您想查询 {time_display} 的数据，但我还需要更多信息才能帮您精确查询**

✅ **我已经理解到：**
• 查询时间：{time_display}
• 查询指标：{metric_hint.strip() if metric_hint else '未明确（可能是电耗/水耗/空调等）'}

❓ **请补充以下信息：**

**1️⃣ 建筑名称（必填）**
可选项：Caspian、Baikal、Huron、Erie、Ontario、Michigan 等
• 例如："Caspian {time_display}的{metric_hint.strip() if metric_hint else '电耗'}"

**2️⃣ 具体指标（可选，如果上面已明确可跳过）**
可选指标：
• 电耗 (kWh) - 电力消耗
• 用水量 (m³) - 水资源消耗
• 空调能耗 - HVAC系统用电
• COP效率 - 制冷效率
• 温度 - 室内/室外温度

💡 **您可以这样问我：**
• "Caspian {time_display}{metric_hint.strip() if metric_hint else '的电耗'}是多少？"
• "查一下 Baikal {time_display} 的所有能耗数据"
• "{time_display} Ontario 和 Huron 的用水量对比"
"""
            return {
                "response": message,
                "layer": "static_rule",
                "action": "clarification_needed",
                "params": params
            }

        # 🔥 新增：处理月份级趋势查询（如"Caspian 2021年7月的XXX趋势"，但无法识别具体指标）
        if query_type == "monthly_trend":
            building = params.get("building", "")
            year = params.get("year", "")
            month = params.get("month", "")
            raw_expression = params.get("raw_expression", "")  # 如 "能耗趋势"

            time_display = f"{year}年{month}月" if (year and month) else (year or month or "某个月份")

            message = f"""🤔 **您想查看 {building} {time_display} 的数据趋势，但我需要确认具体指标**

✅ **我已经理解到：**
• 建筑：{building}
• 时间：{time_display}
• 查询意图：{raw_expression.strip() if raw_expression else '数据趋势'}

❓ **请明确您想查看哪个指标的 trend：**

**可选指标：**
• 🔌 **电耗 (electricity_kwh)** - 最常用，单位 kWh
• 💧 **用水量 (water_m3)** - 单位 m³
• ❄️ **空调能耗 (hvac_kwh)** - HVAC 系统用电
• 🌡️ **温度数据** - 室外温度、冷冻水供回水温度
• 💨 **湿度 (humidity_pct)** - 相对湿度百分比
• 👥 **人员密度 (occupancy_density)** - 人/100m²

💡 **示例问题：**
• "{building} {time_display} 的**电耗**趋势如何？"
• "看看 {building} {time_display} **用电量**的变化"
• "{building} {time_display} **空调能耗** 正常吗"
"""
            return {
                "response": message,
                "layer": "static_rule",
                "action": "clarification_needed",
                "params": params
            }

        building = params.get("building", "")

        # 根据是否有建筑名生成不同的提示
        if building:
            message = f"""🤔 **我不是很清楚您想了解 {building} 的哪方面信息**

我可以帮您查询以下内容：

📊 **能耗数据**
• 电耗、用水量、空调能耗
• 例如："{building} 2021年7月21日的电耗"

📈 **分析报告**
• 能耗趋势、异常检测、节能建议
• 例如："{building} 上个月的能耗异常吗"

🔧 **运维知识**
• 设备故障排查、操作指南
• 例如："{building} 空调外机出了问题怎么办"

💡 **您可以试着说得更具体一点，比如：**
• "{building} 今天的用电情况"
• "{building} 2021年7月的总电耗"
• "对比一下 {building} 和 Caspian 的能耗"
"""
        else:
            message = """🤔 **我不是很清楚您的意思，可以再说得具体一点吗？**

您可以告诉我：

🏢 **想查询哪个建筑？**
可选项：Caspian, Baikal, Huron, Ontario 等

📅 **想查什么时间的数据？**
例如：今天、昨天、2021年7月21日、上个月

📊 **想了解什么指标？**
例如：电耗(kWh)、用水量(m³)、COP效率、温度

💡 **示例问题：**
• "Caspian 今天的电耗是多少？"
• "Baikal 2021年7月21日的用水量"
• "Huron 的空调效率怎么样"
"""
        
        print(f"[CLARIFICATION] 生成澄清消息 for query='{query}', building={building}")
        
        return {
            "response": message,
            "layer": "static_rule",
            "action": "clarification_needed",
            "params": params,
            "needs_clarification": True
        }
    
    def _handle_semantic(self, result: RouteResult, query: str) -> dict:
        """处理语义路由结果"""
        if result.need_cloud and self.failsafe.cloud_available:
            return self._handle_cloud(result, query)
        else:
            return self._handle_local(result, query)
    
    def _handle_local(self, result: RouteResult, query: str) -> dict:
        """处理本地可完成的请求"""
        if result.sql:
            return self._execute_query(result.params, query, result.sql)
        else:
            return self._execute_query(result.params, query)
    
    def _handle_cloud(self, result: RouteResult, query: str) -> dict:
        """处理需要云端的请求"""
        # 先执行本地查询获取数据
        if result.sql:
            query_result = self._execute_sql(result.sql)
        else:
            query_result = self._execute_query_from_params(result.params)
        
        # 调用云端分析
        try:
            cloud_response = self.cloud_llm.process(
                query=query,
                data=query_result or "",
                kb_context="",
                kb_sources=None
            )
            
            self.context["last_result"] = query_result
            self.failsafe.record_request(RouteLayer.CLOUD_LLM)
            
            return {
                "response": cloud_response,
                "layer": "cloud_llm",
                "action": result.action,
                "data": query_result
            }
        except Exception as e:
            print(f"[路由] 云端调用失败，降级到本地：{e}")
            return self._handle_local(result, query)
    
    def _handle_followup(self, query: str) -> dict:
        """处理追问"""
        if not self.context.get("last_result"):
            return {
                "response": "请先查询一些数据，我才能帮您分析。",
                "layer": "static_rule"
            }
        
        # 追问走云端分析
        try:
            cloud_response = self.cloud_llm.process(
                query=query,
                data=self.context["last_result"],
                kb_context="",
                kb_sources=None
            )
            
            return {
                "response": cloud_response,
                "layer": "cloud_llm",
                "action": "followup_analysis",
                "data": self.context["last_result"]
            }
        except Exception as e:
            return {
                "response": f"分析失败：{str(e)}",
                "layer": "error"
            }
    
    def _execute_query(self, params: dict, query: str, sql: str = None) -> dict:
        """执行数据查询"""
        # 如果没有 SQL，需要生成
        if not sql:
            sql = self._generate_sql(params)
        
        print(f"[调试] 生成 SQL: {sql}")
        print(f"[调试] 查询参数: {params}")
        
        if not sql:
            return {
                "response": "无法生成查询语句，请提供更具体的信息。",
                "layer": "local_slm"
            }
        
        # 执行 SQL
        result = self._execute_sql(sql)
        print(f"[调试] SQL 执行结果: {result}")
        
        if result:
            self.context["last_result"] = result
            if params.get("building"):
                self.context["last_building"] = params["building"]
            if params.get("date"):
                self.context["last_date"] = params["date"]
            
            return {
                "response": self._format_result(result),
                "layer": "local_slm",
                "action": "query_data",
                "data": result,
                "sql": sql
            }
        else:
            return {
                "response": "查询无结果。数据覆盖 2019-2021 年夏季，可查询建筑：Baikal、Aral、Caspian、Huron、Erie 等。",
                "layer": "local_slm"
            }
    
    def _generate_sql(self, params: dict) -> str:
        """根据参数生成 SQL"""
        building = params.get("building", "")
        
        year = params.get("year", "")
        month = params.get("month", "")
        
        # 处理跨日查询
        day_start = params.get("day_start")
        day_end = params.get("day_end")
        
        # 🔥 调试：打印所有传入的参数
        print(f"[SQL生成] 📥 收到完整参数: {params}")
        
        # 构建日期范围
        date_start = None
        date_end = None
        
        if day_start and day_end:
            # 跨日查询：X月Y日到Z日
            if year and month:
                date_start = f"{year}-{int(month):02d}-{int(day_start):02d}"
                date_end = f"{year}-{int(month):02d}-{int(day_end):02d}"
            elif year and not month:
                date_start = f"{year}-{int(day_start):02d}-01"
                date_end = f"{year}-{int(day_end):02d}-01"
        else:
            # 单日查询
            date = params.get("date", "")
            if not date:
                day = params.get("day", "")
                if year and month and day:
                    date = f"{year}-{int(month):02d}-{int(day):02d}"
            
            if date:
                date_start = date
                date_end = date
        
        print(f"[SQL生成] 📅 日期范围: start={date_start}, end={date_end}")
        
        # 处理时间范围（X点到Y点）
        hour_start = params.get("hour_start")
        hour_end = params.get("hour_end")
        
        # 🔥 关键修复：确保 hour 参数被正确提取
        if hour_start is None and hour_end is None:
            hour = params.get("hour")
            if hour is not None:
                hour_start = hour
                hour_end = hour
                print(f"[SQL生成] ⏰ 从hour参数设置时间: hour={hour}")
        
        print(f"[SQL生成] ⏰ 时间范围: start={hour_start}, end={hour_end}")
        
        def cn_to_num(val):
            if val is None:
                return None
            val_str = str(val).strip()
            cn_map = {
                '零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
                '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
                '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15,
                '十六': 16, '十七': 17, '十八': 18, '十九': 19, '二十': 20,
                '二十一': 21, '二十二': 22, '二十三': 23
            }
            if val_str in cn_map:
                return cn_map[val_str]
            try:
                return int(val_str)
            except (ValueError, TypeError):
                return None
        
        hour_start = cn_to_num(hour_start)
        hour_end = cn_to_num(hour_end)
        
        period = params.get("period", "")
        if period in ("下午", "晚上"):
            if hour_start is not None and hour_start < 12:
                hour_start += 12
            if hour_end is not None and hour_end < 12:
                hour_end += 12
        
        metric = params.get("metric", "")

        if not building:
            return None

        # 🔥 关键修复：metric_map 统一使用数据库字段名作为 key
        # 与 METRIC_KEYWORDS 保持一致，避免映射失败
        metric_map = {
            "electricity_kwh": "electricity_kwh",
            "water_m3": "water_m3",
            "hvac_kwh": "hvac_kwh",
            "chw_supply_temp": "chw_supply_temp",
            "chw_return_temp": "chw_return_temp",
            "outdoor_temp": "outdoor_temp",
            "humidity_pct": "humidity_pct",
            "occupancy_density": "occupancy_density"
        }

        # 🔥 兼容旧格式：如果传入的是中文名，也支持
        legacy_metric_map = {
            "电耗": "electricity_kwh",
            "水耗": "water_m3",
            "空调能耗": "hvac_kwh",
            "冷冻水供水温度": "chw_supply_temp",
            "冷冻水回水温度": "chw_return_temp",
            "室外温度": "outdoor_temp",
            "湿度": "humidity_pct",
            "人员密度": "occupancy_density"
        }

        # 优先使用新格式，fallback 到旧格式
        select_field = metric_map.get(metric) or legacy_metric_map.get(metric, "electricity_kwh")

        print(f"[SQL生成] metric参数: '{metric}', 选择字段: '{select_field}'")

        sql = f"SELECT timestamp, {select_field} FROM energy_reports WHERE building_id ILIKE '%{building}%'"
        
        # 🔥 关键修复：确保日期和时间过滤正确应用
        print(f"[SQL生成] 🔍 准备添加过滤条件: date_start={date_start}, date_end={date_end}, hour_start={hour_start}, hour_end={hour_end}")
        
        if date_start and date_end:
            if hour_start is not None and hour_end is not None:
                start_time = f"{date_start} {int(hour_start):02d}:00:00"
                end_time = f"{date_end} {int(hour_end):02d}:59:59"
                sql += f" AND timestamp >= '{start_time}' AND timestamp <= '{end_time}'"
                print(f"[SQL生成] ✅ 添加日期+时间过滤: {start_time} ~ {end_time}")
            else:
                start_time = f"{date_start} 00:00:00"
                end_time = f"{date_end} 23:59:59"
                sql += f" AND timestamp >= '{start_time}' AND timestamp <= '{end_time}'"
                print(f"[SQL生成] ✅ 添加日期过滤(全天): {start_time} ~ {end_time}")
        elif date_start:
            if hour_start is not None:
                sql += f" AND timestamp >= '{date_start} {int(hour_start):02d}:00:00' AND timestamp <= '{date_start} {int(hour_start):02d}:59:59'"
                print(f"[SQL生成] ✅ 添加单日+时间过滤: {date_start} {int(hour_start):02d}")
            else:
                sql += f" AND timestamp >= '{date_start} 00:00:00' AND timestamp <= '{date_start} 23:59:59'"
                print(f"[SQL生成] ✅ 添加单日过滤(全天): {date_start}")
        else:
            # ⚠️ 警告：没有日期范围限制
            print(f"[SQL生成] ⚠️ 警告: 没有日期过滤条件！可能返回大量数据")
        
        print(f"[SQL生成] 📤 最终SQL: {sql}")
        
        return sql
    
    def _execute_sql(self, sql: str) -> Optional[str]:
        """执行 SQL 查询"""
        import psycopg2
        
        DB_CONFIG = {
            "host": "localhost",
            "port": 5432,
            "database": "building_energy",
            "user": "postgres",
            "password": "416417"
        }
        
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
            
            # 字段名映射
            DATA_DICT = {
                "electricity_kwh": {"name": "电耗", "unit": "kWh"},
                "water_m3": {"name": "水耗", "unit": "m³"},
                "hvac_kwh": {"name": "空调能耗", "unit": "kWh"},
                "chw_supply_temp": {"name": "冷冻水供水温度", "unit": "°C"},
                "chw_return_temp": {"name": "冷冻水回水温度", "unit": "°C"},
                "outdoor_temp": {"name": "室外温度", "unit": "°C"},
                "humidity_pct": {"name": "湿度", "unit": "%"},
                "occupancy_density": {"name": "人员密度", "unit": "人/100m²"}
            }
            
            # 构建显示列名（包含 timestamp）
            display_names = []
            value_col_idx = -1
            # 优先级字段列表（按重要性排序）
            priority_fields = [
                "electricity_kwh", "water_m3", "hvac_kwh",
                "chw_supply_temp", "chw_return_temp",
                "outdoor_temp", "humidity_pct", "occupancy_density"
            ]
            
            for i, col in enumerate(col_names):
                if col == "timestamp":
                    display_names.append("时间")
                elif col in ("building_id", "meter_id", "system_status", "building_type"):
                    # 元数据字段：添加到 display_names 但标记为跳过
                    display_names.append(None)  # 用 None 标记
                else:
                    info = DATA_DICT.get(col, {})
                    name = info.get("name", col)
                    unit = info.get("unit", "")
                    display_names.append(f"{name}({unit})" if unit else name)
                    
                    # 只在优先级字段或第一个数值字段时设置 value_col_idx
                    if value_col_idx == -1 or col in priority_fields:
                        value_col_idx = i
            
            # 如果没有找到合适的数值列，使用最后一个非timestamp列（兜底）
            if value_col_idx == -1:
                for i, col in enumerate(col_names):
                    if col != "timestamp":
                        value_col_idx = i
            
            # 单值结果
            if len(rows) == 1 and len(rows[0]) == 1:
                return f"{display_names[0]}: {rows[0][0]}"
            
            # 返回原始数据（包含 timestamp 和数值列）
            result_data = {
                "col_names": col_names,
                "display_names": display_names,
                "rows": rows,
                "value_col_idx": value_col_idx,
                "has_timestamp": "timestamp" in col_names
            }
            
            return result_data
                
        except Exception as e:
            print(f"[SQL] 执行失败：{e}")
            return None
    
    def _execute_query_from_params(self, params: dict) -> Optional[str]:
        """从参数执行查询"""
        sql = self._generate_sql(params)
        if sql:
            return self._execute_sql(sql)
        return None
    
    def _format_result(self, result) -> str:
        """格式化查询结果"""
        if not result:
            return "无结果"
        
        # 处理字典格式（新格式）
        if isinstance(result, dict):
            return self._format_result_dict(result)
        
        # 兼容旧格式：单值结果
        if isinstance(result, str) and ": " in result and "\n" not in result:
            return result
        
        # 兼容旧格式：多行结果 - 生成摘要
        if isinstance(result, str):
            lines = result.strip().split("\n")
            if len(lines) < 3:
                return result
            
            data_lines = lines[2:]
            header = lines[0]
            cols = [c.strip() for c in header.strip("|").split("|")]
            
            # 找数值列
            value_col = None
            for col in cols:
                if col not in ("timestamp", "building_id", "meter_id", "system_status", "building_type"):
                    value_col = col
                    break
            
            if not value_col:
                return f"查询结果：共 {len(data_lines)} 条记录"
            
            # 提取数值
            col_idx = {name: i for i, name in enumerate(cols)}
            values = []
            for line in data_lines:
                cells = [c.strip() for c in line.strip("|").split("|")]
                if len(cells) > col_idx.get(value_col, 0):
                    try:
                        values.append(float(cells[col_idx[value_col]]))
                    except (ValueError, TypeError):
                        pass
            
            if not values:
                return f"查询结果：共 {len(data_lines)} 条记录"
            
            avg = sum(values) / len(values)
            mn = min(values)
            mx = max(values)
            
            # 提取单位
            unit = ""
            if "(" in value_col and ")" in value_col:
                unit = value_col.split("(")[1].split(")")[0]
            
            unit_str = f" {unit}" if unit else ""
            
            summary = f"**{value_col}** 查询结果（共 {len(data_lines)} 条记录）：\n\n"
            summary += f"• 平均值：**{avg:.2f}{unit_str}**\n"
            summary += f"• 最小值：**{mn:.2f}{unit_str}**\n"
            summary += f"• 最大值：**{mx:.2f}{unit_str}**"
            
            return summary
        
        return str(result)
    
    def _format_result_dict(self, data: dict) -> str:
        """格式化字典格式的查询结果（包含时间序列数据）"""
        rows = data.get("rows", [])
        display_names = data.get("display_names", [])
        col_names = data.get("col_names", [])
        value_col_idx = data.get("value_col_idx", -1)
        has_timestamp = data.get("has_timestamp", False)
        
        if not rows:
            return "无结果"
        
        # 获取指标名称和单位
        value_col_name = display_names[value_col_idx] if value_col_idx >= 0 else "数值"
        unit = ""
        if "(" in value_col_name and ")" in value_col_name:
            unit = value_col_name.split("(")[1].split(")")[0]
            value_col_name = value_col_name.split("(")[0]
        unit_str = f" {unit}" if unit else ""
        
        # 提取所有数值
        values = []
        for row in rows:
            if value_col_idx >= 0 and len(row) > value_col_idx:
                try:
                    values.append(float(row[value_col_idx]))
                except (ValueError, TypeError):
                    pass
        
        if not values:
            return f"**{value_col_name}** 查询结果：共 {len(rows)} 条记录"
        
        # 计算统计值
        total = sum(values)
        avg = total / len(values)
        mn = min(values)
        mx = max(values)
        
        # 构建输出
        output = f"**{value_col_name}({unit})** 查询结果（共 {len(rows)} 条记录）：\n\n"
        
        # 如果有时间戳，分时段列出
        if has_timestamp:
            ts_idx = col_names.index("timestamp") if "timestamp" in col_names else -1
            
            if ts_idx >= 0:
                output += "### 分时段数据\n\n"
                for row in rows:
                    ts = row[ts_idx]
                    val = row[value_col_idx] if value_col_idx >= 0 else "N/A"
                    
                    # 格式化时间
                    if hasattr(ts, "strftime"):
                        time_str = ts.strftime("%H:%M")
                    elif isinstance(ts, str):
                        # 提取时间部分
                        if " " in ts:
                            time_str = ts.split(" ")[1][:5]
                        else:
                            time_str = ts[:5]
                    else:
                        time_str = str(ts)
                    
                    val_str = f"{val:.2f}" if isinstance(val, (int, float)) else str(val)
                    output += f"• **{time_str}**：{val_str}{unit_str}\n"
                
                output += "\n"
        
        # 统计摘要
        output += "### 统计摘要\n\n"
        output += f"• **总量**：**{total:.2f}{unit_str}**\n"
        output += f"• **平均值**：**{avg:.2f}{unit_str}**\n"
        output += f"• **最小值**：**{mn:.2f}{unit_str}**\n"
        output += f"• **最大值**：**{mx:.2f}{unit_str}**"
        
        return output
    
    def clear_context(self):
        """清空上下文（重置为初始状态）- 🔥 增强版"""
        self.context = {
            "last_building": None,
            "last_date": None,
            "last_result": None,
            "history": [],
            # 重置所有增强字段
            "mentioned_buildings": [],
            "mentioned_dates": [],
            "mentioned_metrics": [],
            "query_results": {},
            "session_start": datetime.now().isoformat(),
            "message_count": 0,
            "session_id": None
        }
        print("[云边路由] ✅ 上下文已完全重置")

    def update_context(self, user_message: str, assistant_reply: str,
                       layer: str = None, action: str = None):
        """🔥 新增：更新上下文（记录每轮交互）"""
        from datetime import datetime
        
        now = datetime.now().isoformat()
        
        # 1️⃣ 添加到历史记录
        history_entry_user = {
            "role": "user",
            "content": user_message,
            "timestamp": now
        }
        history_entry_assistant = {
            "role": "assistant",
            "content": assistant_reply[:500] if assistant_reply else "",  # 截断长回复
            "timestamp": now,
            "layer": layer,
            "action": action
        }
        
        self.context["history"].append(history_entry_user)
        self.context["history"].append(history_entry_assistant)
        
        # 2️⃣ 限制历史长度（保留最近 N 轮）
        if len(self.context["history"]) > self.MAX_HISTORY_LENGTH * 2:
            # 保留最近的对话，删除旧的
            excess = len(self.context["history"]) - (self.MAX_HISTORY_LENGTH * 2)
            self.context["history"] = self.context["history"][excess:]
        
        # 3️⃣ 提取实体（建筑、日期、指标）
        self._extract_entities(user_message + " " + assistant_reply)
        
        # 4️⃣ 更新消息计数
        self.context["message_count"] += 1
        
        # 5️⃣ 更新基础信息（保持向后兼容）
        building_match = re.search(r'\b(Baikal|Aral|Caspian|Huron|Erie|Ladoga|Superior|Titicaca|Victoria|Winnipeg|Vostok|Michigan|Ontario|Malawi)\b', user_message, re.IGNORECASE)
        if building_match:
            self.context["last_building"] = building_match.group(1).capitalize()
        
        date_match = re.search(r'(\d{4})[年\-](\d{1,2})[月\-](\d{1,2})日?', user_message)
        if date_match:
            self.context["last_date"] = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
        
        # 保存最近的结果（截断避免过长）
        self.context["last_result"] = assistant_reply[:1000] if assistant_reply else None
        
        # 6️⃣ 缓存查询结果
        result_index = len(self.context["query_results"])
        self.context["query_results"][result_index] = {
            "query": user_message,
            "result_summary": assistant_reply[:300],
            "timestamp": now,
            "layer": layer
        }

    def _extract_entities(self, text: str):
        """🔥 新增：从文本中提取关键实体"""
        import re
        
        # 提取建筑名
        for building in self.ENTITY_PATTERNS['buildings']:
            if building.lower() in text.lower() and building not in self.context['mentioned_buildings']:
                self.context['mentioned_buildings'].append(building)
        
        # 提取指标关键词
        for metric in self.ENTITY_PATTERNS['metrics']:
            if metric in text and metric not in self.context['mentioned_metrics']:
                self.context['mentioned_metrics'].append(metric)
        
        # 提取日期模式
        for pattern in self.ENTITY_PATTERNS['date_patterns']:
            matches = re.findall(pattern, text)
            for match in matches:
                date_str = match if isinstance(match, str) else str(match)
                if date_str not in self.context['mentioned_dates'] and len(date_str) > 1:
                    self.context['mentioned_dates'].append(date_str)

    def restore_history(self, history: List[Dict]):
        """🔥 新增：从历史列表恢复上下文（用于会话恢复）"""
        if not history:
            return
        
        self.context["history"] = []
        
        for entry in history:
            role = entry.get("role", "unknown")
            content = entry.get("content", "")
            timestamp = entry.get("timestamp", datetime.now().isoformat())
            
            self.context["history"].append({
                "role": role,
                "content": content,
                "timestamp": timestamp
            })
            
            # 重新提取实体
            self._extract_entities(content)
        
        # 更新消息计数
        self.context["message_count"] = len(self.context["history"]) // 2  # 用户+助手算一轮
        
        # 如果有历史，恢复最后的基础信息
        if self.context["history"]:
            last_entry = self.context["history"][-1]
            if last_entry.get("role") == "assistant":
                self.context["last_result"] = last_entry.get("content", "")
        
        print(f"[云边路由] ✅ 已从历史恢复 {len(history)} 条记录，提取到:")
        print(f"   - 建筑: {self.context['mentioned_buildings']}")
        print(f"   - 日期: {self.context['mentioned_dates']}")
        print(f"   - 指标: {self.context['mentioned_metrics']}")

    def get_context_for_llm(self, max_tokens: int = None) -> str:
        """🔥 新增：生成适合注入 LLM 的上下文字符串"""
        max_tokens = max_tokens or self.MAX_CONTEXT_TOKENS
        
        if not self.context["history"]:
            return ""
        
        # 构建上下文字符串
        context_parts = ["\n\n# 对话历史上下文"]
        context_parts.append(f"(当前已进行 {len(self.context['history']) // 2} 轮对话)\n")
        
        # 只包含最近几轮（按 token 预算）
        recent_history = self.context["history"][-10:]  # 最近 5 轮
        
        for i, entry in enumerate(recent_history):
            role_label = "用户" if entry["role"] == "user" else "助手"
            content_preview = entry["content"][:200]  # 截断长内容
            
            context_parts.append(f"{i//2 + 1}. [{role_label}]: {content_preview}")
        
        # 添加提取的关键实体摘要
        if self.context['mentioned_buildings'] or self.context['mentioned_dates']:
            context_parts.append("\n# 关键信息摘要")
            
            if self.context['mentioned_buildings']:
                context_parts.append(f"- 讨论过的建筑: {', '.join(self.context['mentioned_buildings'][-5:])}")
            
            if self.context['mentioned_dates']:
                context_parts.append(f"- 涉及的时间: {', '.join(self.context['mentioned_dates'][-5:])}")
            
            if self.context['mentioned_metrics']:
                context_parts.append(f"- 相关指标: {', '.join(self.context['mentioned_metrics'][-5:])}")
        
        # 添加上一次查询结果（如果存在且有意义）
        if self.context.get("last_result") and len(self.context["last_result"]) > 50:
            context_parts.append(f"\n# 上一次查询结果摘要:\n{self.context['last_result'][:500]}")
        
        result = "\n".join(context_parts)
        
        # 粗略估算 token 数（中文约 1.5 字/token，英文约 4 字/token）
        estimated_tokens = len(result) // 2
        
        if estimated_tokens > max_tokens:
            # 截断以符合 token 限制
            ratio = max_tokens / estimated_tokens
            cutoff = int(len(result) * ratio)
            result = result[:cutoff] + "\n... [上下文已截断]"
        
        return result

    def get_context_summary(self) -> dict:
        """🔥 新增：获取当前上下文的完整摘要（用于调试和展示）"""
        return {
            "session_info": {
                "start_time": self.context.get("session_start"),
                "duration_minutes": (datetime.now() - datetime.fromisoformat(
                    self.context.get("session_start", datetime.now().isoformat())
                )).total_seconds() / 60 if self.context.get("session_start") else 0,
                "total_messages": self.context.get("message_count", 0),
                "history_rounds": len(self.context.get("history", [])) // 2
            },
            "entities": {
                "buildings": self.context.get("mentioned_buildings", []),
                "dates": self.context.get("mentioned_dates", []),
                "metrics": self.context.get("mentioned_metrics", [])
            },
            "recent_activity": {
                "last_building": self.context.get("last_building"),
                "last_date": self.context.get("last_date"),
                "has_last_result": bool(self.context.get("last_result"))
            },
            "usage_stats": {
                "history_length": len(self.context.get("history", [])),
                "query_results_cached": len(self.context.get("query_results", {})),
                "max_history_limit": self.MAX_HISTORY_LENGTH
            }
        }
    
    def get_status(self) -> dict:
        """获取系统状态"""
        return self.failsafe.get_status()
