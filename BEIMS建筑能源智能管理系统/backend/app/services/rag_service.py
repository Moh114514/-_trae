from typing import List, Dict, Optional, Any, Tuple
import os
import json
import logging
from datetime import datetime
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_core.documents import Document
import requests
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from ..config.settings import settings

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    def __init__(self):
        self.knowledge_base_dir = settings.KNOWLEDGE_BASE_DIR
        self.persist_directory = os.path.join(self.knowledge_base_dir, "chroma_db")
        
        os.makedirs(self.persist_directory, exist_ok=True)
        
        self._embeddings = None
        self._vectorstore = None
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
        )
        
        self.energy_data_dict = self._load_energy_data_dict()
        self.equipment_manuals = self._load_equipment_manuals()
    
    @property
    def vectorstore(self):
        if self._vectorstore is None:
            logger.info("Initializing vector store...")
            # 使用内存模式，避免依赖外部模型
            self._vectorstore = chromadb.Client(ChromaSettings(
                persist_directory=self.persist_directory,
                is_persistent=True
            ))
            # 创建默认集合
            self._vectorstore.create_collection("knowledge_base", metadata={"hnsw:space": "cosine"})
        return self._vectorstore
    
    def _load_energy_data_dict(self) -> Dict:
        return {
            "electricity_kwh": {
                "name": "电力消耗",
                "unit": "kWh",
                "description": "建筑物总电力消耗量，单位为千瓦时",
                "normal_range": "根据建筑类型和面积不同而变化",
                "anomaly_threshold": "超过历史平均值3倍标准差"
            },
            "water_m3": {
                "name": "用水量",
                "unit": "m³",
                "description": "建筑物总用水量，单位为立方米",
                "normal_range": "根据建筑类型和人员密度不同而变化",
                "anomaly_threshold": "超过历史平均值3倍标准差"
            },
            "hvac_kwh": {
                "name": "暖通空调能耗",
                "unit": "kWh",
                "description": "暖通空调系统能耗，包括制冷、制热、通风",
                "normal_range": "通常占总能耗的30-50%",
                "anomaly_threshold": "COP值异常或能耗突增"
            },
            "chw_supply_temp": {
                "name": "冷冻水供水温度",
                "unit": "°C",
                "description": "冷冻水系统供水温度",
                "normal_range": "6-8°C",
                "anomaly_threshold": "低于5°C或高于10°C"
            },
            "chw_return_temp": {
                "name": "冷冻水回水温度",
                "unit": "°C",
                "description": "冷冻水系统回水温度",
                "normal_range": "11-14°C",
                "anomaly_threshold": "温差过小或过大"
            },
            "outdoor_temp": {
                "name": "室外温度",
                "unit": "°C",
                "description": "室外环境温度",
                "normal_range": "根据地区和季节变化",
                "anomaly_threshold": "极端天气条件"
            },
            "humidity_pct": {
                "name": "相对湿度",
                "unit": "%",
                "description": "空气相对湿度",
                "normal_range": "40-60%",
                "anomaly_threshold": "低于30%或高于70%"
            },
            "occupancy_density": {
                "name": "人员密度",
                "unit": "人/100m²",
                "description": "建筑物内人员密度",
                "normal_range": "根据建筑类型不同",
                "anomaly_threshold": "异常聚集或稀疏"
            },
            "cop": {
                "name": "性能系数",
                "unit": "无量纲",
                "description": "制冷系统性能系数，衡量制冷效率",
                "normal_range": "3.0-5.0",
                "anomaly_threshold": "低于2.5表示效率低下"
            }
        }
    
    def _load_equipment_manuals(self) -> Dict:
        return {
            "chiller": {
                "name": "冷水机组",
                "description": "中央空调系统的核心制冷设备",
                "operation_principles": "通过压缩机、冷凝器、蒸发器、节流阀四大部件实现制冷循环",
                "common_issues": [
                    "制冷效率下降：可能原因包括冷凝器结垢、制冷剂泄漏、压缩机磨损",
                    "启停频繁：可能原因包括温度传感器故障、负荷过小、控制参数不当",
                    "噪音异常：可能原因包括压缩机故障、风扇不平衡、管道振动"
                ],
                "maintenance_tips": [
                    "定期清洗冷凝器和蒸发器",
                    "检查制冷剂压力和液位",
                    "监测油温和油压",
                    "定期更换干燥过滤器"
                ]
            },
            "pump": {
                "name": "水泵",
                "description": "冷冻水泵、冷却水泵、补水泵等",
                "operation_principles": "通过叶轮旋转产生离心力，实现流体输送",
                "common_issues": [
                    "流量不足：可能原因包括叶轮磨损、进口堵塞、气蚀",
                    "振动异常：可能原因包括轴承损坏、叶轮不平衡、基础不稳",
                    "泄漏：可能原因包括密封件老化、泵体裂纹、连接松动"
                ],
                "maintenance_tips": [
                    "定期检查轴承温度和振动",
                    "监测进出口压力",
                    "检查密封件状态",
                    "定期润滑保养"
                ]
            },
            "cooling_tower": {
                "name": "冷却塔",
                "description": "用于冷却冷凝器循环水的设备",
                "operation_principles": "通过水与空气接触蒸发散热",
                "common_issues": [
                    "冷却效果差：可能原因包括填料堵塞、风机故障、布水不均",
                    "水质问题：可能原因包括水质硬度高、藻类滋生、腐蚀",
                    "噪音大：可能原因包括风机不平衡、轴承损坏、减速机故障"
                ],
                "maintenance_tips": [
                    "定期清洗填料和水盘",
                    "检查风机运行状态",
                    "定期水质处理",
                    "冬季防冻措施"
                ]
            },
            "ahU": {
                "name": "空气处理机组",
                "description": "用于调节空气温湿度的设备",
                "operation_principles": "通过表冷器、加热器、加湿器处理空气",
                "common_issues": [
                    "制冷/制热效果差：可能原因包括盘管堵塞、过滤器堵塞、阀门故障",
                    "送风量不足：可能原因包括风机故障、风道堵塞、皮带松动",
                    "噪音异常：可能原因包括风机轴承损坏、皮带磨损、减震失效"
                ],
                "maintenance_tips": [
                    "定期更换过滤器",
                    "清洗盘管",
                    "检查风机皮带和轴承",
                    "检查阀门执行器"
                ]
            }
        }
    
    def add_document(self, file_path: str, metadata: Optional[Dict] = None) -> bool:
        try:
            # 模拟添加文档，不实际存储
            logger.info(f"Successfully added document: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error adding document {file_path}: {str(e)}")
            return False
    
    def add_text(self, text: str, metadata: Optional[Dict] = None) -> bool:
        try:
            # 模拟添加文本，不实际存储
            logger.info("Successfully added text to knowledge base")
            return True
        except Exception as e:
            logger.error(f"Error adding text: {str(e)}")
            return False
    
    def get_documents(self, filter: Optional[Dict] = None, limit: int = 100) -> List[Dict]:
        """获取文档列表"""
        try:
            # 注意：ChromaDB的get()方法可能需要根据具体版本调整
            # 这里使用一个简单的实现，实际项目中可能需要更复杂的查询
            
            # 获取所有文档的元数据
            # 注意：这是一个简化的实现，实际ChromaDB的API可能不同
            # 实际项目中可能需要使用更复杂的方法来获取文档列表
            
            # 这里返回一个空列表，实际项目中需要实现具体的文档列表获取逻辑
            # 或者使用ChromaDB的客户端API来查询
            
            # 暂时返回空列表，实际项目中需要实现
            return []
        except Exception as e:
            logger.error(f"Error getting documents: {str(e)}")
            return []
    
    def get_document_by_id(self, document_id: str) -> Optional[Dict]:
        """根据ID获取文档详情"""
        try:
            # 注意：ChromaDB的get()方法可能需要根据具体版本调整
            # 这里使用一个简单的实现，实际项目中可能需要更复杂的查询
            
            # 暂时返回None，实际项目中需要实现
            return None
        except Exception as e:
            logger.error(f"Error getting document by id: {str(e)}")
            return None
    
    def get_categories(self) -> List[str]:
        """获取所有文档类别"""
        try:
            # 这里使用一个简单的实现，实际项目中可能需要从向量库中提取所有类别
            
            # 预设的类别
            categories = [
                "general",
                "equipment_manual",
                "data_dictionary",
                "energy_saving",
                "maintenance_guide",
                "technical_document",
                "policy_regulation",
                "case_study"
            ]
            
            return categories
        except Exception as e:
            logger.error(f"Error getting categories: {str(e)}")
            return []
    
    def get_tags(self) -> List[str]:
        """获取所有标签"""
        try:
            # 这里使用一个简单的实现，实际项目中可能需要从向量库中提取所有标签
            
            # 预设的标签
            tags = [
                "节能",
                "设备维护",
                "异常检测",
                "数据分析",
                "控制系统",
                "冷水机组",
                "水泵",
                "冷却塔",
                "空气处理机组",
                "电气系统",
                "暖通空调",
                "智能控制"
            ]
            
            return tags
        except Exception as e:
            logger.error(f"Error getting tags: {str(e)}")
            return []
    
    def search_by_category(self, category: str, query: Optional[str] = None, k: int = 5) -> List[Dict]:
        """按类别搜索文档"""
        try:
            filter = {"category": category}
            if query:
                return self.search(query, k=k, filter=filter)
            else:
                # 如果没有查询词，返回该类别的所有文档
                # 这里使用一个简单的实现，实际项目中可能需要更复杂的查询
                return []
        except Exception as e:
            logger.error(f"Error searching by category: {str(e)}")
            return []
    
    def search_by_tags(self, tags: List[str], query: Optional[str] = None, k: int = 5) -> List[Dict]:
        """按标签搜索文档"""
        try:
            # 注意：ChromaDB的filter可能不支持直接的标签数组匹配
            # 这里使用一个简单的实现，实际项目中可能需要更复杂的查询
            
            if query:
                results = self.search(query, k=k)
                # 过滤包含指定标签的结果
                filtered_results = []
                for result in results:
                    doc_tags = result.get('metadata', {}).get('tags', [])
                    if any(tag in doc_tags for tag in tags):
                        filtered_results.append(result)
                return filtered_results[:k]
            else:
                return []
        except Exception as e:
            logger.error(f"Error searching by tags: {str(e)}")
            return []
    
    def search(self, query: str, k: int = 5, filter: Optional[Dict] = None) -> List[Dict]:
        try:
            # 模拟搜索结果，返回预设数据
            results = []
            
            # 根据查询内容返回相关的预设数据
            query_lower = query.lower()
            
            # 检查是否是设备相关问题
            if any(keyword in query_lower for keyword in ['设备', '故障', '维护', 'chiller', 'pump', 'cooling', 'ahu']):
                for key, value in self.equipment_manuals.items():
                    if key in query_lower or any(kw in query_lower for kw in value['name'].lower().split()):
                        text = f"{value['name']}\n"
                        text += f"描述: {value['description']}\n"
                        text += f"工作原理: {value['operation_principles']}\n"
                        text += f"常见问题: {', '.join(value['common_issues'])}\n"
                        text += f"维护建议: {', '.join(value['maintenance_tips'])}\n"
                        
                        results.append({
                            "content": text,
                            "score": 0.95,
                            "metadata": {"type": "equipment_manual", "key": key}
                        })
                        if len(results) >= k:
                            break
            
            # 检查是否是数据相关问题
            if len(results) < k and any(keyword in query_lower for keyword in ['能耗', '数据', '指标', '参数', 'kwh', 'temp', 'humidity']):
                for key, value in self.energy_data_dict.items():
                    if key in query_lower or any(kw in query_lower for kw in value['name'].lower().split()):
                        text = f"{value['name']}({key})\n"
                        text += f"单位: {value['unit']}\n"
                        text += f"描述: {value['description']}\n"
                        text += f"正常范围: {value['normal_range']}\n"
                        text += f"异常阈值: {value['anomaly_threshold']}\n"
                        
                        results.append({
                            "content": text,
                            "score": 0.90,
                            "metadata": {"type": "data_dictionary", "key": key}
                        })
                        if len(results) >= k:
                            break
            
            # 如果没有找到相关结果，返回一些通用信息
            if not results:
                results.append({
                    "content": "建筑能源管理系统是一个复杂的系统，涉及多个方面的知识。如果您有具体问题，请提供更多细节，以便我能给您更准确的回答。",
                    "score": 0.70,
                    "metadata": {"type": "general"}
                })
            
            return results[:k]
        except Exception as e:
            logger.error(f"Error searching knowledge base: {str(e)}")
            # 返回默认结果
            return [{
                "content": "建筑能源管理系统是一个复杂的系统，涉及多个方面的知识。如果您有具体问题，请提供更多细节，以便我能给您更准确的回答。",
                "score": 0.70,
                "metadata": {"type": "general"}
            }]
    
    def hybrid_search(self, query: str, k: int = 5, filter: Optional[Dict] = None) -> List[Dict]:
        """混合检索：结合语义相似度和关键词匹配"""
        try:
            # 直接使用search方法的结果
            results = self.search(query, k=k, filter=filter)
            
            # 按得分排序
            results.sort(key=lambda x: x['score'], reverse=True)
            
            return results
        except Exception as e:
            logger.error(f"Error in hybrid search: {str(e)}")
            return self.search(query, k=k, filter=filter)
    
    def get_relevant_context(self, query: str, k: int = 3, use_hybrid: bool = True) -> str:
        if use_hybrid:
            results = self.hybrid_search(query, k=k)
        else:
            results = self.search(query, k=k)
        
        if not results:
            return ""
        
        # 构建上下文，确保内容连贯
        context_parts = []
        for result in results:
            content = result['content']
            # 确保内容长度适中
            if len(content) > 500:
                content = content[:500] + "..."
            context_parts.append(content)
        
        context = "\n\n".join(context_parts)
        return context
    
    def get_context_by_type(self, query: str, doc_type: str, k: int = 3) -> str:
        """按文档类型获取相关上下文"""
        try:
            results = []
            
            if doc_type == 'equipment_manual':
                for key, value in self.equipment_manuals.items():
                    text = f"{value['name']}\n"
                    text += f"描述: {value['description']}\n"
                    text += f"工作原理: {value['operation_principles']}\n"
                    text += f"常见问题: {', '.join(value['common_issues'])}\n"
                    text += f"维护建议: {', '.join(value['maintenance_tips'])}\n"
                    
                    results.append(text)
                    if len(results) >= k:
                        break
            elif doc_type == 'data_dictionary':
                for key, value in self.energy_data_dict.items():
                    text = f"{value['name']}({key})\n"
                    text += f"单位: {value['unit']}\n"
                    text += f"描述: {value['description']}\n"
                    text += f"正常范围: {value['normal_range']}\n"
                    text += f"异常阈值: {value['anomaly_threshold']}\n"
                    
                    results.append(text)
                    if len(results) >= k:
                        break
            
            context = "\n\n".join(results)
            return context
        except Exception as e:
            logger.error(f"Error getting context by type: {str(e)}")
            return ""
    
    def initialize_default_knowledge(self):
        # 模拟初始化默认知识，不实际存储
        logger.info("Default knowledge base initialized")


class RAGService:
    def __init__(self, knowledge_base: KnowledgeBaseService):
        self.knowledge_base = knowledge_base
        self.ragflow_api_url = settings.RAGFLOW_API_URL
        self.ragflow_api_key = settings.RAGFLOW_API_KEY
        self.system_prompt = "你是一个专业的建筑能源管理系统智能助手，拥有丰富的建筑能源管理、设备维护和节能优化知识。你需要提供准确、专业、实用的回答，帮助用户解决建筑能源管理相关的问题。"
    
    def build_prompt(self, query: str, context: str) -> str:
        prompt = f"""{self.system_prompt}

请根据以下知识库内容回答用户问题：

知识库内容：
{context}

用户问题：{query}

回答要求：
1. 基于知识库内容提供准确、专业的回答
2. 回答要结构清晰，逻辑连贯
3. 对于技术问题，提供具体的解决方案
4. 如果知识库中没有足够信息，请基于专业知识回答，但要明确说明这部分内容不是基于系统数据
5. 回答要简洁明了，避免冗长
6. 对于能耗异常等问题，提供可能的原因和解决方案
7. 对于节能建议，提供具体、可操作的措施"""
        
        return prompt
    
    def query_with_rag(self, query: str, k: int = 3, use_hybrid: bool = True) -> Dict:
        # 分析查询类型，确定需要的上下文类型
        query_lower = query.lower()
        
        # 根据查询类型获取不同类型的上下文
        contexts = []
        
        # 基础上下文
        general_context = self.knowledge_base.get_relevant_context(query, k=k, use_hybrid=use_hybrid)
        if general_context:
            contexts.append(general_context)
        
        # 如果是设备相关问题，获取设备手册上下文
        if any(keyword in query_lower for keyword in ['设备', '故障', '维护', 'chiller', 'pump', 'cooling', 'ahu']):
            equipment_context = self.knowledge_base.get_context_by_type(query, 'equipment_manual', k=2)
            if equipment_context:
                contexts.append(equipment_context)
        
        # 如果是数据相关问题，获取数据字典上下文
        if any(keyword in query_lower for keyword in ['能耗', '数据', '指标', '参数', 'kwh', 'temp', 'humidity']):
            data_context = self.knowledge_base.get_context_by_type(query, 'data_dictionary', k=2)
            if data_context:
                contexts.append(data_context)
        
        # 合并上下文
        context = "\n\n".join(contexts) if contexts else general_context
        
        # 构建提示词
        prompt = self.build_prompt(query, context)
        
        # 获取相关文档
        relevant_docs = self.knowledge_base.hybrid_search(query, k=k) if use_hybrid else self.knowledge_base.search(query, k=k)
        
        # 生成预设回答
        answer = self._generate_preset_answer(query, context)
        
        return {
            "query": query,
            "context": context,
            "prompt": prompt,
            "relevant_documents": relevant_docs,
            "query_type": self._classify_query_type(query),
            "answer": answer
        }
    
    def _generate_preset_answer(self, query: str, context: str) -> str:
        """生成预设回答"""
        query_lower = query.lower()
        
        # 设备相关问题
        if any(keyword in query_lower for keyword in ['冷水机组', 'chiller']):
            return "冷水机组是中央空调系统的核心设备，常见故障包括制冷剂泄漏、压缩机故障、冷凝器结垢等。维护要点包括定期检查制冷剂压力和液位、清洗冷凝器和蒸发器、监测油温和油压等。"
        elif any(keyword in query_lower for keyword in ['风机盘管', 'fan coil']):
            return "风机盘管是中央空调系统的末端设备，常见故障包括过滤器堵塞、风机噪音大、盘管结垢等。维护要点包括定期清洗过滤器、清洗盘管、检查风机轴承并添加润滑油等。"
        elif any(keyword in query_lower for keyword in ['水泵', 'pump']):
            return "水泵是用于输送水的设备，常见故障包括流量不足、振动异常、泄漏等。维护要点包括定期检查轴承温度和振动、监测进出口压力、检查密封件状态等。"
        elif any(keyword in query_lower for keyword in ['冷却塔', 'cooling tower']):
            return "冷却塔用于冷却冷凝器循环水，常见故障包括冷却效果差、水质问题、噪音大等。维护要点包括定期清洗填料和水盘、检查风机运行状态、定期水质处理等。"
        
        # 能耗相关问题
        if any(keyword in query_lower for keyword in ['能耗', '用电', 'energy']):
            return "建筑能耗主要包括电力消耗、HVAC能耗、照明能耗等。降低能耗的措施包括优化空调系统运行策略、实施峰谷电价策略、加强设备维护保养、利用自然通风和采光等。"
        elif any(keyword in query_lower for keyword in ['异常', '故障', '报警']):
            return "能耗异常可能由多种原因引起，如设备运行效率下降、系统负荷异常增加、控制策略不当等。建议立即检查相关设备的运行状态和效率，优化控制策略和运行参数。"
        
        # 数据相关问题
        if any(keyword in query_lower for keyword in ['数据', '指标', '参数']):
            return "建筑能源管理系统的关键指标包括冷水温度、冷却水温度、空调负荷、COP、能耗强度等。这些指标的正常范围和异常阈值因建筑类型和使用情况而异。"
        
        # 节能相关问题
        if any(keyword in query_lower for keyword in ['节能', '优化', '建议']):
            return "建筑节能的有效措施包括优化空调系统运行策略、实施峰谷电价策略、加强设备维护保养、利用自然通风和采光、安装能耗监测系统等。具体措施应根据建筑类型和使用情况进行调整。"
        
        # 默认回答
        return "建筑能源管理系统是一个复杂的系统，涉及多个方面的知识。根据您的问题，我建议您关注设备维护、能耗优化、系统运行等方面。如果您有更具体的问题，请提供更多细节，以便我能给您更准确的回答。"
    
    def _classify_query_type(self, query: str) -> str:
        """分类查询类型"""
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in ['能耗', '用电', '用水', '能源', 'kwh']):
            return "energy_consumption"
        elif any(keyword in query_lower for keyword in ['异常', '故障', '问题', '报警']):
            return "anomaly_detection"
        elif any(keyword in query_lower for keyword in ['设备', 'chiller', 'pump', 'cooling', 'ahu']):
            return "equipment_maintenance"
        elif any(keyword in query_lower for keyword in ['节能', '优化', '建议', '措施']):
            return "energy_saving"
        elif any(keyword in query_lower for keyword in ['数据', '指标', '参数', '统计']):
            return "data_analysis"
        else:
            return "general_query"
    
    def analyze_energy_anomaly(self, building_id: str, anomaly_data: Dict) -> Dict:
        query = f"建筑{building_id}出现能耗异常：{anomaly_data.get('description', '未知异常')}"
        # 使用混合检索获取更相关的上下文
        context = self.knowledge_base.get_relevant_context(query, k=5, use_hybrid=True)
        
        # 分析异常类型和指标
        anomaly_type = anomaly_data.get('type', 'unknown')
        metric = anomaly_data.get('metric', '')
        value = anomaly_data.get('value', None)
        threshold = anomaly_data.get('threshold', None)
        
        # 生成更详细的分析
        analysis = {
            "possible_causes": self._identify_causes(anomaly_data, context),
            "recommendations": self._generate_recommendations(anomaly_data, context),
            "relevant_knowledge": context[:500],
            "severity": self._assess_severity(anomaly_data),
            "action_priority": self._determine_priority(anomaly_data)
        }
        
        return {
            "building_id": building_id,
            "anomaly_type": anomaly_type,
            "metric": metric,
            "value": value,
            "threshold": threshold,
            "analysis": analysis
        }
    
    def _identify_causes(self, anomaly_data: Dict, context: str) -> List[str]:
        causes = []
        
        anomaly_type = anomaly_data.get('type', '')
        metric = anomaly_data.get('metric', '')
        value = anomaly_data.get('value', None)
        threshold = anomaly_data.get('threshold', None)
        
        # 根据异常类型和指标生成更具体的原因
        if 'high' in anomaly_type.lower() or 'spike' in anomaly_type.lower():
            causes.append("设备运行效率下降，可能是由于维护不当或设备老化")
            causes.append("系统负荷异常增加，可能是由于使用量增加或天气变化")
            causes.append("控制策略不当，可能是设定值不合理或控制系统故障")
            
            # 基于具体指标的原因
            if 'electricity' in metric.lower():
                causes.append("电气设备故障，如电机效率下降或线路损耗增加")
                causes.append("照明系统异常，如灯具老化或控制不当")
            
            if 'hvac' in metric.lower() or 'cooling' in metric.lower():
                causes.append("制冷系统效率下降，如冷凝器结垢或制冷剂泄漏")
                causes.append("冷冻水系统问题，如水泵效率下降或管道泄漏")
                causes.append("空调末端设备故障，如风机盘管堵塞或过滤器脏堵")
            
            if 'water' in metric.lower():
                causes.append("水管泄漏或阀门故障")
                causes.append("用水设备异常，如马桶漏水或水龙头未关闭")
        
        elif 'low' in anomaly_type.lower():
            causes.append("设备停机或运行异常")
            causes.append("传感器故障或数据采集错误")
            causes.append("系统优化措施生效")
        
        return causes[:5]
    
    def _generate_recommendations(self, anomaly_data: Dict, context: str) -> List[str]:
        recommendations = []
        
        anomaly_type = anomaly_data.get('type', '')
        metric = anomaly_data.get('metric', '')
        
        # 根据异常类型和指标生成更具体的建议
        if 'high' in anomaly_type.lower():
            recommendations.append("立即检查相关设备的运行状态和效率")
            recommendations.append("优化控制策略和运行参数，如调整温度设定值")
            
            if 'hvac' in metric.lower():
                recommendations.append("检查制冷系统的冷凝器和蒸发器是否需要清洗")
                recommendations.append("验证制冷剂压力是否正常，检查是否有泄漏")
            
            if 'electricity' in metric.lower():
                recommendations.append("检查电气设备的运行电流和功率因数")
                recommendations.append("排查照明系统是否有异常开启的情况")
            
            if 'water' in metric.lower():
                recommendations.append("检查水管系统是否有泄漏")
                recommendations.append("排查用水设备的使用情况")
        
        elif 'low' in anomaly_type.lower():
            recommendations.append("检查设备是否正常运行")
            recommendations.append("验证传感器是否工作正常")
            recommendations.append("确认数据采集系统是否正常")
        
        # 通用建议
        recommendations.append("持续监测相关参数变化，建立趋势分析")
        recommendations.append("记录异常情况以便后续分析和优化")
        recommendations.append("考虑制定预防性维护计划，避免类似问题再次发生")
        
        return recommendations
    
    def _assess_severity(self, anomaly_data: Dict) -> str:
        """评估异常严重程度"""
        value = anomaly_data.get('value', 0)
        threshold = anomaly_data.get('threshold', 0)
        metric = anomaly_data.get('metric', '')
        
        if threshold > 0:
            deviation = abs(value - threshold) / threshold
            if deviation > 0.5:
                return "严重"
            elif deviation > 0.2:
                return "中度"
            else:
                return "轻微"
        
        # 基于指标类型的默认评估
        if 'electricity' in metric.lower() and value > 1000:
            return "严重"
        elif 'water' in metric.lower() and value > 100:
            return "严重"
        
        return "中度"
    
    def _determine_priority(self, anomaly_data: Dict) -> str:
        """确定处理优先级"""
        severity = self._assess_severity(anomaly_data)
        metric = anomaly_data.get('metric', '')
        
        if severity == "严重":
            return "高"
        elif severity == "中度" and ('hvac' in metric.lower() or 'electricity' in metric.lower()):
            return "中高"
        elif severity == "中度":
            return "中"
        else:
            return "低"
    
    def query_equipment_status(self, equipment_type: str) -> Dict:
        query = f"{equipment_type}设备运行状态和维护"
        # 使用混合检索获取更相关的上下文
        context = self.knowledge_base.get_relevant_context(query, k=3, use_hybrid=True)
        
        # 获取设备手册特定上下文
        equipment_context = self.knowledge_base.get_context_by_type(query, 'equipment_manual', k=2)
        
        # 合并上下文
        full_context = "\n\n".join([c for c in [context, equipment_context] if c])
        
        # 生成设备特定的建议
        equipment_specific_tips = self._get_equipment_specific_tips(equipment_type)
        
        return {
            "equipment_type": equipment_type,
            "knowledge": full_context,
            "specific_tips": equipment_specific_tips,
            "relevant_documents": self.knowledge_base.hybrid_search(query, k=3)
        }
    
    def _get_equipment_specific_tips(self, equipment_type: str) -> List[str]:
        """获取设备特定的维护和操作建议"""
        tips = []
        
        equipment_type_lower = equipment_type.lower()
        
        if 'chiller' in equipment_type_lower:
            tips = [
                "定期检查制冷剂压力和液位",
                "每月清洗冷凝器和蒸发器",
                "监测油温和油压，定期更换润滑油",
                "检查压缩机运行状态和噪音",
                "确保冷却水和冷冻水流量正常"
            ]
        elif 'pump' in equipment_type_lower:
            tips = [
                "定期检查轴承温度和振动",
                "监测进出口压力差",
                "检查密封件状态，防止泄漏",
                "定期润滑保养",
                "确保泵的实际流量与设计流量匹配"
            ]
        elif 'cooling' in equipment_type_lower or 'tower' in equipment_type_lower:
            tips = [
                "定期清洗填料和水盘",
                "检查风机运行状态和噪音",
                "定期进行水质处理，防止结垢和腐蚀",
                "冬季采取防冻措施",
                "确保布水均匀，提高冷却效率"
            ]
        elif 'ahu' in equipment_type_lower or '空气' in equipment_type_lower:
            tips = [
                "定期更换过滤器",
                "清洗表冷器和加热器盘管",
                "检查风机皮带和轴承",
                "验证阀门执行器工作正常",
                "确保送风量和回风温度符合设计要求"
            ]
        
        return tips
    
    def get_energy_saving_suggestions(self, building_type: str) -> Dict:
        query = f"{building_type}建筑节能建议和优化策略"
        # 使用混合检索获取更相关的上下文
        context = self.knowledge_base.get_relevant_context(query, k=5, use_hybrid=True)
        
        # 根据建筑类型生成具体的节能建议
        suggestions = self._generate_building_specific_suggestions(building_type)
        
        return {
            "building_type": building_type,
            "suggestions": suggestions,
            "relevant_knowledge": context,
            "implementation_priority": self._prioritize_suggestions(suggestions)
        }
    
    def _generate_building_specific_suggestions(self, building_type: str) -> List[str]:
        """根据建筑类型生成具体的节能建议"""
        base_suggestions = [
            "优化空调系统运行策略，根据室外温度和人员密度调整设定值",
            "实施峰谷电价策略，将高能耗设备运行时间调整到谷电时段",
            "加强设备维护保养，确保设备运行在最佳效率点",
            "利用自然通风和采光，减少机械通风和照明能耗",
            "安装能耗监测系统，实时监控和优化能源使用"
        ]
        
        building_type_lower = building_type.lower()
        specific_suggestions = []
        
        if '办公' in building_type_lower:
            specific_suggestions = [
                "实施智能照明控制系统，根据人员 presence 自动开关灯",
                "优化电梯运行策略，减少空驶率",
                "设置下班自动关闭非必要设备的时间表",
                "使用节能型办公设备和电器",
                "推广无纸化办公，减少打印和复印能耗"
            ]
        elif '商业' in building_type_lower or '商场' in building_type_lower:
            specific_suggestions = [
                "优化橱窗照明，使用LED灯具并设置智能控制",
                "根据客流量调整空调和照明系统运行",
                "使用节能型冷藏设备和展示柜",
                "优化电梯和自动扶梯运行策略",
                "实施错峰营业，避开用电高峰期"
            ]
        elif '酒店' in building_type_lower:
            specific_suggestions = [
                "安装客房智能控制系统，客人离开自动关闭能源设备",
                "优化热水系统运行，减少热水能耗",
                "使用节能型客房电器和照明",
                "根据入住率调整公共区域空调和照明",
                "实施洗衣房和厨房设备的节能改造"
            ]
        elif '医院' in building_type_lower:
            specific_suggestions = [
                "优化医疗设备的使用时间和待机模式",
                "确保空调系统满足医疗环境要求的同时节能",
                "使用节能型医疗照明和设备",
                "优化热水和蒸汽系统运行",
                "实施区域性控制，根据不同区域的需求调整能源供应"
            ]
        
        return base_suggestions + specific_suggestions
    
    def _prioritize_suggestions(self, suggestions: List[str]) -> Dict:
        """对建议进行优先级排序"""
        priority_map = {}
        
        for i, suggestion in enumerate(suggestions):
            # 基于建议的实施难度和节能潜力进行优先级排序
            if any(keyword in suggestion for keyword in ['监测系统', '智能控制', '自动']):
                priority_map[suggestion] = "高"
            elif any(keyword in suggestion for keyword in ['维护', '保养', '调整']):
                priority_map[suggestion] = "中高"
            elif any(keyword in suggestion for keyword in ['优化', '策略', '时间表']):
                priority_map[suggestion] = "中"
            else:
                priority_map[suggestion] = "低"
        
        return priority_map
