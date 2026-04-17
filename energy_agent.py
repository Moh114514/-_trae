"""
建筑能源管理 AI Agent

整合本地模型 + 百炼 API + MCP 工具调用
"""

import os
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

# ==================== 配置 ====================

# 百炼 API 配置
BAILIAN_API_KEY = os.getenv("BAILIAN_API_KEY", "")  # 从环境变量获取
BAILIAN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# 本地模型配置（可选）
LOCAL_MODEL_PATH = None  # 如果部署本地模型，设置 GGUF 文件路径


# ==================== 百炼 API 客户端 ====================

class BailianClient:
    """阿里云百炼 API 客户端"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = BAILIAN_BASE_URL
        
    def chat(self, 
             messages: List[Dict], 
             model: str = "qwen-plus",
             tools: Optional[List[Dict]] = None) -> Dict:
        """
        调用百炼 Chat API
        
        Args:
            messages: 对话消息列表
            model: 模型名称 (qwen-plus / qwen-max / qwen-turbo)
            tools: 工具列表（可选）
        
        Returns:
            API 响应
        """
        import httpx
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages
        }
        
        if tools:
            payload["tools"] = tools
        
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    def chat_with_tools(self,
                        user_message: str,
                        system_prompt: str,
                        tools: List[Dict],
                        tool_executor: callable,
                        model: str = "qwen-plus") -> str:
        """
        带工具调用的对话
        
        Args:
            user_message: 用户消息
            system_prompt: 系统提示
            tools: 工具定义
            tool_executor: 工具执行函数
            model: 模型名称
        
        Returns:
            最终回复
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # 第一次调用
        response = self.chat(messages, model, tools)
        message = response["choices"][0]["message"]
        
        # 处理工具调用
        if message.get("tool_calls"):
            messages.append(message)
            
            for tool_call in message["tool_calls"]:
                tool_name = tool_call["function"]["name"]
                tool_args = json.loads(tool_call["function"]["arguments"])
                
                # 执行工具
                tool_result = tool_executor(tool_name, tool_args)
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(tool_result, ensure_ascii=False)
                })
            
            # 再次调用获取最终回复
            final_response = self.chat(messages, model)
            return final_response["choices"][0]["message"]["content"]
        
        return message["content"]


# ==================== 能源管理 Agent ====================

class EnergyManagementAgent:
    """建筑能源管理智能代理"""
    
    SYSTEM_PROMPT = """你是建筑能源管理系统的智能助手。

你的职责是帮助用户查询和分析建筑能耗数据，包括：
- 查询建筑能耗（电力、水、空调）
- 分析 COP 制冷效率
- 检测能耗异常
- 对比同比环比数据
- 提供节能建议

当用户提问时，使用提供的工具查询数据，然后给出清晰的分析和建议。

当前可用的建筑包括：Baikal, Aral, Caspian, Huron, Erie, Ladoga, Superior, Titicaca, Victoria, Winnipeg, Vostok, Michigan, Ontario, Malawi

数据时间范围：2021年全年
"""
    
    # MCP 工具定义（OpenAI 格式）
    TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "list_buildings",
                "description": "获取所有建筑列表",
                "parameters": {"type": "object", "properties": {}}
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_energy_summary",
                "description": "获取建筑能耗汇总",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "building_id": {"type": "string", "description": "建筑ID"},
                        "start_date": {"type": "string", "description": "开始日期 YYYY-MM-DD"},
                        "end_date": {"type": "string", "description": "结束日期 YYYY-MM-DD"}
                    },
                    "required": ["building_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "query_electricity",
                "description": "查询建筑电耗数据",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "building_id": {"type": "string", "description": "建筑ID"},
                        "start_date": {"type": "string", "description": "开始日期 YYYY-MM-DD"},
                        "end_date": {"type": "string", "description": "结束日期 YYYY-MM-DD"}
                    },
                    "required": ["building_id", "start_date", "end_date"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "analyze_cop",
                "description": "分析建筑 COP 制冷效率",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "building_id": {"type": "string", "description": "建筑ID"},
                        "start_date": {"type": "string", "description": "开始日期 YYYY-MM-DD"},
                        "end_date": {"type": "string", "description": "结束日期 YYYY-MM-DD"}
                    },
                    "required": ["building_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "detect_anomalies",
                "description": "检测建筑能耗异常",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "building_id": {"type": "string", "description": "建筑ID"},
                        "threshold": {"type": "number", "description": "Z-Score 阈值，默认 3.0"}
                    },
                    "required": ["building_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "compare_energy",
                "description": "对比分析建筑能耗（同比、环比）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "building_id": {"type": "string", "description": "建筑ID"},
                        "metric": {"type": "string", "description": "指标：electricity_kwh / water_m3 / hvac_kwh"}
                    },
                    "required": ["building_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_daily_trend",
                "description": "获取每日能耗趋势",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "building_id": {"type": "string", "description": "建筑ID"},
                        "start_date": {"type": "string", "description": "开始日期 YYYY-MM-DD"},
                        "end_date": {"type": "string", "description": "结束日期 YYYY-MM-DD"}
                    },
                    "required": ["building_id", "start_date", "end_date"]
                }
            }
        }
    ]
    
    def __init__(self, api_key: str):
        self.client = BailianClient(api_key)
        self._init_tools()
    
    def _init_tools(self):
        """初始化工具执行器"""
        import sys
        sys.path.append(r'E:\openclaw-project\workspace\Fuwu')
        from energy_analyzer import EnergyAnalyzer
        
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "database": "building_energy",
            "user": "postgres",
            "password": "416417"
        }
        self.analyzer_class = EnergyAnalyzer
    
    def _execute_tool(self, tool_name: str, tool_args: Dict) -> Any:
        """执行工具"""
        from datetime import datetime
        
        with self.analyzer_class(self.db_config) as analyzer:
            if tool_name == "list_buildings":
                df = analyzer.get_data()
                return df['building_id'].unique().tolist()
            
            elif tool_name == "get_energy_summary":
                building_id = tool_args.get("building_id")
                start_date = tool_args.get("start_date")
                end_date = tool_args.get("end_date")
                
                start_time = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
                end_time = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
                
                report = analyzer.generate_report(building_id, start_time, end_time)
                return {
                    "building_id": report.get("building_id"),
                    "statistics": report.get("statistics"),
                    "temperature": report.get("temperature")
                }
            
            elif tool_name == "query_electricity":
                building_id = tool_args["building_id"]
                start_time = datetime.strptime(tool_args["start_date"], "%Y-%m-%d")
                end_time = datetime.strptime(tool_args["end_date"], "%Y-%m-%d")
                
                df = analyzer.get_data(building_id, start_time, end_time)
                return {
                    "total_kwh": round(df['electricity_kwh'].sum(), 2),
                    "avg_daily_kwh": round(df['electricity_kwh'].mean() * 24, 2),
                    "records": len(df)
                }
            
            elif tool_name == "analyze_cop":
                building_id = tool_args["building_id"]
                start_date = tool_args.get("start_date")
                end_date = tool_args.get("end_date")
                
                start_time = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
                end_time = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
                
                cop_trend = analyzer.analyze_cop_trend(building_id, start_time, end_time)
                return {
                    "avg_cop": round(cop_trend['cop'].mean(), 2),
                    "rating_distribution": cop_trend['cop_rating'].value_counts().to_dict()
                }
            
            elif tool_name == "detect_anomalies":
                building_id = tool_args["building_id"]
                threshold = tool_args.get("threshold", 3.0)
                result = analyzer.analyze_anomalies(building_id, threshold=threshold)
                return result
            
            elif tool_name == "compare_energy":
                building_id = tool_args["building_id"]
                metric = tool_args.get("metric", "electricity_kwh")
                yoy = analyzer.calculate_yoy(building_id, metric)
                mom = analyzer.calculate_mom(building_id, metric)
                return {
                    "yoy": yoy.get("data", [])[:3],
                    "mom": mom.get("data", [])[-3:]
                }
            
            elif tool_name == "get_daily_trend":
                building_id = tool_args["building_id"]
                start_time = datetime.strptime(tool_args["start_date"], "%Y-%m-%d")
                end_time = datetime.strptime(tool_args["end_date"], "%Y-%m-%d")
                
                daily = analyzer.get_daily_summary(building_id, start_time, end_time)
                return daily.to_dict("records")[:10]  # 限制返回数量
        
        return {"error": f"Unknown tool: {tool_name}"}
    
    def chat(self, user_message: str, model: str = "qwen-plus") -> str:
        """
        与 Agent 对话
        
        Args:
            user_message: 用户消息
            model: 模型名称
        
        Returns:
            Agent 回复
        """
        return self.client.chat_with_tools(
            user_message=user_message,
            system_prompt=self.SYSTEM_PROMPT,
            tools=self.TOOLS,
            tool_executor=self._execute_tool,
            model=model
        )


# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 从环境变量获取 API Key
    api_key = os.getenv("BAILIAN_API_KEY")
    
    if not api_key:
        print("请设置环境变量 BAILIAN_API_KEY")
        print("示例: set BAILIAN_API_KEY=your-api-key")
        exit(1)
    
    agent = EnergyManagementAgent(api_key)
    
    print("=" * 50)
    print("建筑能源管理 AI Agent")
    print("=" * 50)
    print("\n输入问题进行对话，输入 'quit' 退出")
    print("示例问题：")
    print("  - Baikal 建筑的总电耗是多少？")
    print("  - 分析 Aral 的 COP 效率")
    print("  - 检测 Baikal 的能耗异常")
    print()
    
    while True:
        user_input = input("用户: ").strip()
        
        if user_input.lower() == 'quit':
            break
        
        if not user_input:
            continue
        
        print("\n思考中...")
        response = agent.chat(user_input)
        print(f"\n助手: {response}\n")