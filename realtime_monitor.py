"""
实时监测服务
- 模拟实时数据流（从历史数据）
- 实时异常检测
- WebSocket 推送告警
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum

import pandas as pd
import numpy as np

try:
    from fastapi import WebSocket
    WEBSOCKET_AVAILABLE = True
except:
    WEBSOCKET_AVAILABLE = False

import sys
sys.path.append(r'E:\openclaw-project\workspace\Fuwu')
from energy_analyzer import EnergyAnalyzer


# ==================== 配置 ====================

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "building_energy",
    "user": "postgres",
    "password": "416417"
}

BUILDINGS = ["Baikal", "Aral", "Caspian", "Huron", "Erie", "Ladoga", "Superior", 
             "Titicaca", "Victoria", "Winnipeg", "Vostok", "Michigan", "Ontario", "Malawi"]

# 监测阈值
THRESHOLDS = {
    "electricity_kwh": {"min": 50, "max": 500, "zscore": 3.0},
    "water_m3": {"min": 0.1, "max": 50, "zscore": 3.0},
    "hvac_kwh": {"min": 10, "max": 300, "zscore": 3.0},
    "chw_supply_temp": {"min": 5, "max": 12, "zscore": 3.0},
    "chw_return_temp": {"min": 10, "max": 18, "zscore": 3.0},
    "outdoor_temp": {"min": -40, "max": 50, "zscore": 3.0},
}


# ==================== 数据模型 ====================

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    """告警信息"""
    id: str
    building_id: str
    timestamp: str
    field: str
    value: float
    threshold: dict
    level: AlertLevel
    message: str
    simulated: bool = False  # 是否为模拟异常
    
    def to_dict(self):
        return {
            "id": self.id,
            "building_id": self.building_id,
            "timestamp": self.timestamp,
            "field": self.field,
            "value": self.value,
            "threshold": self.threshold,
            "level": self.level.value,
            "message": self.message,
            "simulated": self.simulated
        }


@dataclass
class BuildingStatus:
    """建筑状态"""
    building_id: str
    status: str  # "normal", "warning", "critical"
    last_update: str
    current_data: dict
    active_alerts: int
    
    def to_dict(self):
        return asdict(self)


# ==================== 实时监测服务 ====================

class RealTimeMonitor:
    """实时监测服务"""
    
    def __init__(self):
        self.active_connections: Set = set()
        self.alerts: List[Alert] = []
        self.building_status: Dict[str, BuildingStatus] = {}
        self.historical_data: Dict[str, pd.DataFrame] = {}
        self.current_index: Dict[str, int] = {}
        self.is_running = False
        self.simulation_start_time: Optional[datetime] = None
        self.simulation_current_time: Optional[datetime] = None
        
        # 模拟设置
        self.simulation_settings = {
            "enabled": False,
            "building": "all",
            "type": "electricity_high",
            "intensity": 5
        }
        self.simulated_buildings: Set[str] = set()  # 正在模拟的建筑
        self.speed = 60  # 默认速度
        self.is_paused = False  # 暂停状态
        self.accumulated_minutes = 0  # 累计分钟数（用于判断是否推进到下一条数据）
        
        # 初始化建筑状态
        for building in BUILDINGS:
            self.building_status[building] = BuildingStatus(
                building_id=building,
                status="normal",
                last_update="",
                current_data={},
                active_alerts=0
            )
    
    async def connect(self, websocket):
        """WebSocket 连接"""
        self.active_connections.add(websocket)
        # 发送当前状态
        await self._send_status(websocket)
    
    def disconnect(self, websocket):
        """WebSocket 断开"""
        self.active_connections.discard(websocket)
    
    async def _send_status(self, websocket):
        """发送当前状态"""
        status = {
            "type": "status",
            "is_running": self.is_running,
            "simulation_time": self.simulation_current_time.isoformat() if self.simulation_current_time else None,
            "buildings": {k: v.to_dict() for k, v in self.building_status.items()},
            "total_alerts": len(self.alerts)
        }
        await websocket.send_json(status)
    
    async def _broadcast(self, message: dict):
        """广播消息"""
        if not self.active_connections:
            return
        dead_connections = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                dead_connections.add(connection)
        self.active_connections -= dead_connections
    
    async def _broadcast_alert(self, alert: Alert):
        """广播告警"""
        await self._broadcast({
            "type": "alert",
            "data": alert.to_dict()
        })
    
    def load_historical_data(self, start_date: str = "2021-07-01"):
        """加载历史数据用于模拟"""
        print(f"[监测] 加载历史数据，起始日期: {start_date}")
        
        self.simulation_start_time = datetime.strptime(start_date, "%Y-%m-%d")
        self.simulation_current_time = self.simulation_start_time
        
        # 使用上下文管理器
        with EnergyAnalyzer(DB_CONFIG) as analyzer:
            for building in BUILDINGS:
                try:
                    df = analyzer.get_data(building)
                    if not df.empty:
                        # 按时间排序
                        df = df.sort_values('timestamp')
                        # 筛选起始日期之后的数据
                        df = df[df['timestamp'] >= self.simulation_start_time]
                        self.historical_data[building] = df
                        self.current_index[building] = 0
                        print(f"  {building}: {len(df)} 条记录")
                except Exception as e:
                    print(f"  {building}: 加载失败 - {e}")
        
        print(f"[监测] 数据加载完成，共 {len(self.historical_data)} 个建筑")
    
    def _check_anomaly(self, building_id: str, data: dict) -> List[Alert]:
        """检测异常"""
        alerts = []
        
        for field, thresholds in THRESHOLDS.items():
            if field not in data:
                continue
            
            value = data[field]
            if value is None:
                continue
            
            # 检查阈值
            if value < thresholds["min"] or value > thresholds["max"]:
                level = AlertLevel.CRITICAL if abs(value - thresholds["min"]) > thresholds["min"] * 0.5 or \
                        abs(value - thresholds["max"]) > thresholds["max"] * 0.5 else AlertLevel.WARNING
                
                alert = Alert(
                    id=f"{building_id}_{field}_{datetime.now().isoformat()}",
                    building_id=building_id,
                    timestamp=data.get('timestamp', ''),
                    field=field,
                    value=value,
                    threshold=thresholds,
                    level=level,
                    message=f"[{data.get('timestamp', '')}] {building_id} {field} 异常: {value:.2f} (正常范围: {thresholds['min']} - {thresholds['max']})"
                )
                alerts.append(alert)
        
        return alerts
    
    async def start_monitoring(self, speed: float = 60.0):
        """
        启动监测
        
        Args:
            speed: 模拟速度（1 = 实时，60 = 1秒模拟1分钟）
        """
        if self.is_running:
            print("[监测] 已在运行中，跳过")
            return
        
        if not self.historical_data:
            print("[监测] 加载历史数据...")
            self.load_historical_data()
        
        if not self.historical_data:
            print("[监测] 错误：无历史数据")
            return
        
        self.is_running = True
        self.speed = speed  # 保存速度
        print(f"[监测] 开始监测，速度: {speed}x，建筑数: {len(self.historical_data)}")
        print(f"[监测] 时间推进: 1秒 = {speed}分钟 = {speed/60:.1f}小时")
        
        # 通知前端
        try:
            await self._broadcast({
                "type": "monitoring_started",
                "speed": speed,
                "start_time": self.simulation_start_time.isoformat() if self.simulation_start_time else None
            })
        except Exception as e:
            print(f"[监测] 广播启动消息失败: {e}")
        
        loop_count = 0
        try:
            while self.is_running:
                loop_count += 1
                
                # 检查暂停状态
                while self.is_paused and self.is_running:
                    await asyncio.sleep(0.5)
                
                if not self.is_running:
                    break
                
                # 模拟时间推进 - 根据速度推进相应分钟数
                # speed=1: 推进1分钟, speed=60: 推进60分钟(1小时), speed=300: 推进5小时
                minutes_to_advance = self.speed
                self.simulation_current_time += timedelta(minutes=minutes_to_advance)
                self.accumulated_minutes += minutes_to_advance
                
                if loop_count % 10 == 0:  # 每10次循环打印一次
                    print(f"[监测] 循环 #{loop_count}, 时间: {self.simulation_current_time.strftime('%Y-%m-%d %H:%M')}, 速度: {self.speed}x")
                
                # 只有累计满60分钟才推进数据索引（因为数据是小时级的）
                should_advance_data = self.accumulated_minutes >= 60
                if should_advance_data:
                    self.accumulated_minutes = self.accumulated_minutes % 60
                
                # 检查每个建筑
                for building_id, df in self.historical_data.items():
                    try:
                        idx = self.current_index.get(building_id, 0)
                        
                        if idx >= len(df):
                            if loop_count % 100 == 0:
                                print(f"[监测] {building_id} 数据已用完")
                            continue
                        
                        # 只有累计满60分钟才推进索引
                        if should_advance_data:
                            self.current_index[building_id] = idx + 1
                            idx = self.current_index[building_id]
                            
                            if idx >= len(df):
                                continue
                        
                        row = df.iloc[idx]
                        data = {
                            'timestamp': str(row['timestamp']),
                            'electricity_kwh': float(row['electricity_kwh']) if pd.notna(row['electricity_kwh']) else None,
                            'water_m3': float(row['water_m3']) if pd.notna(row['water_m3']) else None,
                            'hvac_kwh': float(row['hvac_kwh']) if pd.notna(row['hvac_kwh']) else None,
                            'chw_supply_temp': float(row['chw_supply_temp']) if pd.notna(row['chw_supply_temp']) else None,
                            'chw_return_temp': float(row['chw_return_temp']) if pd.notna(row['chw_return_temp']) else None,
                            'outdoor_temp': float(row['outdoor_temp']) if pd.notna(row['outdoor_temp']) else None,
                        }
                        
                        # 检测异常
                        alerts = self._check_anomaly(building_id, data)
                        
                        # 更新建筑状态
                        status = "normal"
                        if len(alerts) > 0:
                            status = "critical" if any(a.level == AlertLevel.CRITICAL for a in alerts) else "warning"
                            self.alerts.extend(alerts)
                            
                            # 广播告警
                            for alert in alerts:
                                try:
                                    await self._broadcast_alert(alert)
                                except Exception as e:
                                    print(f"[监测] 广播告警失败: {e}")
                        
                        self.building_status[building_id] = BuildingStatus(
                            building_id=building_id,
                            status=status,
                            last_update=data['timestamp'],
                            current_data=data,
                            active_alerts=len([a for a in self.alerts if a.building_id == building_id])
                        )
                        
                    except Exception as e:
                        print(f"[监测] 处理建筑 {building_id} 出错: {e}")
                        continue
                
                # 广播状态更新
                try:
                    await self._broadcast({
                        "type": "update",
                        "is_running": True,
                        "speed": self.speed,
                        "simulation_time": self.simulation_current_time.isoformat(),
                        "buildings": {k: v.to_dict() for k, v in self.building_status.items()}
                    })
                except Exception as e:
                    print(f"[监测] 广播状态更新失败: {e}")
                
                # 控制模拟速度
                # speed=60: 每秒推进60分钟，即sleep 1秒
                # speed=1: 每秒推进1分钟，即sleep 1秒
                # sleep_time = 1秒（固定间隔，时间推进由 speed 控制）
                await asyncio.sleep(1.0)
                
        except asyncio.CancelledError:
            print("[监测] 任务被取消")
        except Exception as e:
            print(f"[监测] 发生错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.is_running = False
            print(f"[监测] 监测已停止，共运行 {loop_count} 次循环")
    
    def stop_monitoring(self):
        """停止监测"""
        self.is_running = False
        self.is_paused = False
        print("[监测] 停止监测")
    
    def pause_monitoring(self):
        """暂停监测"""
        if self.is_running and not self.is_paused:
            self.is_paused = True
            print(f"[监测] 已暂停，当前时间: {self.simulation_current_time}")
    
    def resume_monitoring(self):
        """继续监测"""
        if self.is_running and self.is_paused:
            self.is_paused = False
            print(f"[监测] 继续运行，从 {self.simulation_current_time} 开始")
    
    def reset_monitoring(self):
        """重置监测"""
        self.is_running = False
        self.is_paused = False
        self.accumulated_minutes = 0
        self.alerts = []
        self.historical_data = {}
        self.current_index = {}
        self.simulation_start_time = None
        self.simulation_current_time = None
        
        # 重置建筑状态
        for building in BUILDINGS:
            self.building_status[building] = BuildingStatus(
                building_id=building,
                status="normal",
                last_update="",
                current_data={},
                active_alerts=0
            )
        
        print("[监测] 已重置")
    
    def clear_alerts(self):
        """清除所有告警"""
        self.alerts = []
        # 重置所有建筑的告警计数
        for building_id in self.building_status:
            self.building_status[building_id].active_alerts = 0
        print("[监测] 已清除所有告警")
    
    def get_summary(self) -> dict:
        """获取监测摘要"""
        normal = sum(1 for s in self.building_status.values() if s.status == "normal")
        warning = sum(1 for s in self.building_status.values() if s.status == "warning")
        critical = sum(1 for s in self.building_status.values() if s.status == "critical")
        
        return {
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "speed": self.speed,
            "simulation_time": self.simulation_current_time.isoformat() if self.simulation_current_time else None,
            "buildings": {
                "total": len(BUILDINGS),
                "normal": normal,
                "warning": warning,
                "critical": critical
            },
            "alerts": {
                "total": len(self.alerts),
                "critical": sum(1 for a in self.alerts if a.level == AlertLevel.CRITICAL),
                "warning": sum(1 for a in self.alerts if a.level == AlertLevel.WARNING)
            }
        }
    
    def get_alerts(self, building_id: str = None, limit: int = 50) -> List[dict]:
        """获取告警列表"""
        alerts = self.alerts
        if building_id:
            alerts = [a for a in alerts if a.building_id == building_id]
        return [a.to_dict() for a in alerts[-limit:]]
    
    def trigger_anomaly(self, building: str, anomaly_type: str, intensity: int) -> List[Alert]:
        """
        手动触发异常
        
        Args:
            building: 建筑名称或 "all"
            anomaly_type: 异常类型
            intensity: 强度 (1-10)
        
        Returns:
            触发的告警列表
        """
        triggered_alerts = []
        target_buildings = BUILDINGS if building == "all" else [building]
        
        for building_id in target_buildings:
            if building_id not in self.building_status:
                continue
            
            # 标记为模拟
            self.simulated_buildings.add(building_id)
            
            # 根据异常类型生成异常数据
            anomaly_data = self._generate_anomaly_data(anomaly_type, intensity)
            
            # 创建告警
            for field, value in anomaly_data.items():
                threshold = THRESHOLDS.get(field, {})
                level = AlertLevel.CRITICAL if intensity >= 7 else AlertLevel.WARNING
                
                alert = Alert(
                    id=f"{building_id}_{field}_sim_{datetime.now().isoformat()}",
                    building_id=building_id,
                    timestamp=self.simulation_current_time.isoformat() if self.simulation_current_time else datetime.now().isoformat(),
                    field=field,
                    value=value,
                    threshold=threshold,
                    level=level,
                    message=f"[模拟] {building_id} {field} 异常: {value:.2f}"
                )
                alert.simulated = True  # 标记为模拟
                triggered_alerts.append(alert)
                self.alerts.append(alert)
            
            # 更新建筑状态
            status = self.building_status[building_id]
            status.status = "critical" if intensity >= 7 else "warning"
            status.active_alerts += len(anomaly_data)
        
        return triggered_alerts
    
    def _generate_anomaly_data(self, anomaly_type: str, intensity: int) -> dict:
        """根据异常类型生成异常数据"""
        multiplier = intensity / 5  # 标准化到 0.2-2.0
        
        if anomaly_type == "electricity_high":
            return {"electricity_kwh": THRESHOLDS["electricity_kwh"]["max"] * (1 + multiplier)}
        elif anomaly_type == "electricity_low":
            return {"electricity_kwh": THRESHOLDS["electricity_kwh"]["min"] * (1 - multiplier * 0.5)}
        elif anomaly_type == "temp_high":
            return {"outdoor_temp": THRESHOLDS["outdoor_temp"]["max"] * multiplier}
        elif anomaly_type == "temp_low":
            return {"outdoor_temp": THRESHOLDS["outdoor_temp"]["min"] * multiplier}
        elif anomaly_type == "cop_low":
            return {"hvac_kwh": THRESHOLDS["hvac_kwh"]["max"] * (1 + multiplier)}
        elif anomaly_type == "random":
            import random
            fields = ["electricity_kwh", "water_m3", "hvac_kwh", "outdoor_temp"]
            field = random.choice(fields)
            if random.random() > 0.5:
                return {field: THRESHOLDS[field]["max"] * (1 + multiplier * 0.5)}
            else:
                return {field: THRESHOLDS[field]["min"] * (1 - multiplier * 0.3)}
        
        return {}


# 单例
monitor = RealTimeMonitor()