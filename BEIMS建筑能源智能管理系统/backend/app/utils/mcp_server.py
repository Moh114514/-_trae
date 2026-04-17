import asyncio
import json
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MCPServer:
    def __init__(self):
        self.tools = {}
        self.resources = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        self.register_tool(
            name="query_energy_data",
            description="查询建筑能耗数据，支持按建筑、时间范围、仪表等条件筛选",
            parameters={
                "type": "object",
                "properties": {
                    "building_id": {"type": "string", "description": "建筑ID"},
                    "start_time": {"type": "string", "description": "开始时间(YYYY-MM-DD HH:MM:SS)"},
                    "end_time": {"type": "string", "description": "结束时间(YYYY-MM-DD HH:MM:SS)"},
                    "meter_id": {"type": "string", "description": "仪表ID"},
                    "limit": {"type": "integer", "description": "返回记录数限制", "default": 100}
                }
            },
            handler=self._query_energy_data
        )
        
        self.register_tool(
            name="get_statistics",
            description="获取能耗统计数据，支持多种统计类型",
            parameters={
                "type": "object",
                "properties": {
                    "stat_type": {
                        "type": "string",
                        "enum": [
                            "time_aggregation", "cop", "anomalies", "ranking",
                            "trend", "peak_demand", "intensity", "comparison",
                            "weather_correlation", "occupancy_impact", "hourly_pattern",
                            "weekly_pattern", "seasonal"
                        ],
                        "description": "统计类型"
                    },
                    "building_id": {"type": "string", "description": "建筑ID"},
                    "start_time": {"type": "string", "description": "开始时间"},
                    "end_time": {"type": "string", "description": "结束时间"},
                    "period": {"type": "string", "description": "时间周期(hour/day/week/month)", "default": "day"}
                },
                "required": ["stat_type"]
            },
            handler=self._get_statistics
        )
        
        self.register_tool(
            name="create_visualization",
            description="创建可视化图表",
            parameters={
                "type": "object",
                "properties": {
                    "chart_type": {
                        "type": "string",
                        "enum": [
                            "line", "multi_line", "bar", "grouped_bar", "stacked_bar",
                            "pie", "donut", "area", "scatter", "heatmap", "histogram",
                            "box", "gauge", "radar", "treemap"
                        ],
                        "description": "图表类型"
                    },
                    "data": {"type": "array", "description": "图表数据"},
                    "title": {"type": "string", "description": "图表标题"},
                    "x_field": {"type": "string", "description": "X轴字段"},
                    "y_field": {"type": "string", "description": "Y轴字段"}
                },
                "required": ["chart_type", "data"]
            },
            handler=self._create_visualization
        )
        
        self.register_tool(
            name="intelligent_query",
            description="智能问答，基于RAG技术回答能耗相关问题",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "用户问题"},
                    "k": {"type": "integer", "description": "返回相关文档数量", "default": 3}
                },
                "required": ["query"]
            },
            handler=self._intelligent_query
        )
        
        self.register_tool(
            name="analyze_anomaly",
            description="分析能耗异常原因并提供解决建议",
            parameters={
                "type": "object",
                "properties": {
                    "building_id": {"type": "string", "description": "建筑ID"},
                    "anomaly_type": {"type": "string", "description": "异常类型"},
                    "metric": {"type": "string", "description": "异常指标"},
                    "value": {"type": "number", "description": "异常值"}
                },
                "required": ["building_id", "anomaly_type"]
            },
            handler=self._analyze_anomaly
        )
    
    def register_tool(self, name: str, description: str, parameters: Dict, handler):
        self.tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": handler
        }
    
    def register_resource(self, name: str, description: str, handler):
        self.resources[name] = {
            "name": name,
            "description": description,
            "handler": handler
        }
    
    async def _query_energy_data(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        from ..models.database import SessionLocal
        from ..services.statistics import StatisticsAnalyzer
        
        db = SessionLocal()
        try:
            analyzer = StatisticsAnalyzer(db)
            
            start_time = None
            end_time = None
            
            if arguments.get("start_time"):
                start_time = datetime.strptime(arguments["start_time"], "%Y-%m-%d %H:%M:%S")
            if arguments.get("end_time"):
                end_time = datetime.strptime(arguments["end_time"], "%Y-%m-%d %H:%M:%S")
            
            data = analyzer.query_data(
                building_id=arguments.get("building_id"),
                start_time=start_time,
                end_time=end_time,
                meter_id=arguments.get("meter_id")
            )
            
            limit = arguments.get("limit", 100)
            
            return {
                "success": True,
                "total": len(data),
                "data": [{
                    "building_id": d.building_id,
                    "timestamp": d.timestamp.isoformat(),
                    "electricity_kwh": d.electricity_kwh,
                    "water_m3": d.water_m3,
                    "hvac_kwh": d.hvac_kwh,
                    "outdoor_temp": d.outdoor_temp,
                    "system_status": d.system_status
                } for d in data[:limit]]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()
    
    async def _get_statistics(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        from ..models.database import SessionLocal
        from ..services.statistics import StatisticsAnalyzer
        
        db = SessionLocal()
        try:
            analyzer = StatisticsAnalyzer(db)
            
            start_time = None
            end_time = None
            
            if arguments.get("start_time"):
                start_time = datetime.strptime(arguments["start_time"], "%Y-%m-%d %H:%M:%S")
            if arguments.get("end_time"):
                end_time = datetime.strptime(arguments["end_time"], "%Y-%m-%d %H:%M:%S")
            
            stat_type = arguments["stat_type"]
            
            if stat_type == "time_aggregation":
                result = analyzer.time_period_aggregation(
                    building_id=arguments.get("building_id"),
                    start_time=start_time,
                    end_time=end_time,
                    period=arguments.get("period", "day")
                )
            elif stat_type == "cop":
                result = analyzer.calculate_cop(
                    building_id=arguments.get("building_id"),
                    start_time=start_time,
                    end_time=end_time
                )
            elif stat_type == "anomalies":
                result = analyzer.detect_anomalies(
                    building_id=arguments.get("building_id"),
                    start_time=start_time,
                    end_time=end_time
                )
            elif stat_type == "ranking":
                result = analyzer.energy_consumption_ranking(
                    start_time=start_time,
                    end_time=end_time
                )
            elif stat_type == "trend":
                result = analyzer.energy_trend_analysis(
                    building_id=arguments.get("building_id"),
                    start_time=start_time,
                    end_time=end_time
                )
            elif stat_type == "peak_demand":
                result = analyzer.peak_demand_analysis(
                    building_id=arguments.get("building_id"),
                    start_time=start_time,
                    end_time=end_time
                )
            elif stat_type == "intensity":
                result = analyzer.energy_intensity_analysis(
                    building_id=arguments.get("building_id"),
                    start_time=start_time,
                    end_time=end_time
                )
            elif stat_type == "comparison":
                result = analyzer.comparative_analysis(
                    building_ids=arguments.get("building_ids", []),
                    start_time=start_time,
                    end_time=end_time
                )
            elif stat_type == "weather_correlation":
                result = analyzer.weather_correlation_analysis(
                    building_id=arguments.get("building_id"),
                    start_time=start_time,
                    end_time=end_time
                )
            elif stat_type == "occupancy_impact":
                result = analyzer.occupancy_impact_analysis(
                    building_id=arguments.get("building_id"),
                    start_time=start_time,
                    end_time=end_time
                )
            elif stat_type == "hourly_pattern":
                result = analyzer.hourly_pattern_analysis(
                    building_id=arguments.get("building_id"),
                    start_time=start_time,
                    end_time=end_time
                )
            elif stat_type == "weekly_pattern":
                result = analyzer.weekly_pattern_analysis(
                    building_id=arguments.get("building_id"),
                    start_time=start_time,
                    end_time=end_time
                )
            elif stat_type == "seasonal":
                result = analyzer.seasonal_analysis(
                    building_id=arguments.get("building_id"),
                    start_time=start_time,
                    end_time=end_time
                )
            else:
                return {"success": False, "error": f"Unknown stat_type: {stat_type}"}
            
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()
    
    async def _create_visualization(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        from ..services.visualization import VisualizationService
        
        viz_service = VisualizationService()
        
        chart_type = arguments["chart_type"]
        data = arguments["data"]
        title = arguments.get("title", "图表")
        x_field = arguments.get("x_field", "x")
        y_field = arguments.get("y_field", "y")
        
        try:
            if chart_type == "line":
                result = viz_service.create_line_chart(data, x_field, y_field, title)
            elif chart_type == "multi_line":
                result = viz_service.create_multi_line_chart(data, x_field, [y_field], title)
            elif chart_type == "bar":
                result = viz_service.create_bar_chart(data, x_field, y_field, title)
            elif chart_type == "pie":
                result = viz_service.create_pie_chart(data, x_field, y_field, title)
            elif chart_type == "scatter":
                result = viz_service.create_scatter_plot(data, x_field, y_field, title)
            elif chart_type == "heatmap":
                result = viz_service.create_heatmap(data, x_field.split(","), y_field.split(","), title)
            elif chart_type == "histogram":
                result = viz_service.create_histogram(data, title, x_field)
            elif chart_type == "box":
                result = viz_service.create_box_plot(data, x_field, y_field, title)
            elif chart_type == "gauge":
                result = viz_service.create_gauge_chart(data[0] if data else 0, title)
            elif chart_type == "radar":
                result = viz_service.create_radar_chart(data, x_field, y_field, title)
            elif chart_type == "area":
                result = viz_service.create_area_chart(data, x_field, [y_field], title)
            elif chart_type == "treemap":
                result = viz_service.create_treemap(data, x_field, y_field, title)
            else:
                return {"success": False, "error": f"Unknown chart_type: {chart_type}"}
            
            return {"success": True, "chart": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _intelligent_query(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        from ..services.rag_service import KnowledgeBaseService, RAGService
        
        try:
            knowledge_base = KnowledgeBaseService()
            rag_service = RAGService(knowledge_base)
            
            result = rag_service.query_with_rag(
                query=arguments["query"],
                k=arguments.get("k", 3)
            )
            
            return {
                "success": True,
                "query": result["query"],
                "context": result["context"],
                "relevant_documents": result["relevant_documents"]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _analyze_anomaly(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        from ..services.rag_service import KnowledgeBaseService, RAGService
        
        try:
            knowledge_base = KnowledgeBaseService()
            rag_service = RAGService(knowledge_base)
            
            anomaly_data = {
                "type": arguments.get("anomaly_type"),
                "metric": arguments.get("metric"),
                "value": arguments.get("value")
            }
            
            result = rag_service.analyze_energy_anomaly(
                building_id=arguments["building_id"],
                anomaly_data=anomaly_data
            )
            
            return {"success": True, "analysis": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_tools(self) -> List[Dict]:
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"]
            }
            for tool in self.tools.values()
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if name not in self.tools:
            return {"success": False, "error": f"Tool not found: {name}"}
        
        handler = self.tools[name]["handler"]
        
        try:
            result = await handler(arguments)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_resources(self) -> List[Dict]:
        return [
            {
                "name": resource["name"],
                "description": resource["description"]
            }
            for resource in self.resources.values()
        ]
    
    async def read_resource(self, name: str) -> Dict[str, Any]:
        if name not in self.resources:
            return {"success": False, "error": f"Resource not found: {name}"}
        
        handler = self.resources[name]["handler"]
        
        try:
            result = await handler()
            return {"success": True, "content": result}
        except Exception as e:
            return {"success": False, "error": str(e)}


mcp_server = MCPServer()
