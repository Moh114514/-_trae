import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from ..models.database import EnergyData
import logging
from ..config.settings import settings

logger = logging.getLogger(__name__)


class StatisticsAnalyzer:
    def __init__(self, db: Session):
        self.db = db

    def _debug(self, method: str, message: str, **fields):
        if not settings.STATS_DEBUG:
            return
        logger.info("[STATDBG][service.%s] %s %s", method, message, fields)

    def _summarize_result(self, result: Dict) -> Dict:
        summary = {}
        for key, value in result.items():
            if isinstance(value, list):
                summary[key] = f"list(len={len(value)})"
            elif isinstance(value, dict):
                summary[key] = f"dict(keys={len(value)})"
            else:
                summary[key] = value
        return summary
    
    def query_data(
        self,
        building_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        meter_id: Optional[str] = None,
        system_status: Optional[str] = None,
        building_type: Optional[str] = None,
        min_electricity: Optional[float] = None,
        max_electricity: Optional[float] = None,
        min_water: Optional[float] = None,
        max_water: Optional[float] = None,
        min_hvac: Optional[float] = None,
        max_hvac: Optional[float] = None,
        min_temp: Optional[float] = None,
        max_temp: Optional[float] = None,
        min_humidity: Optional[float] = None,
        max_humidity: Optional[float] = None,
        occupancy_density: Optional[float] = None,
        page: int = 1,
        page_size: Optional[int] = 100
    ) -> Dict:
        query = self.db.query(EnergyData)
        
        if building_id:
            query = query.filter(EnergyData.building_id == building_id)
        if building_type:
            query = query.filter(EnergyData.building_type == building_type)
        if start_time:
            query = query.filter(EnergyData.timestamp >= start_time)
        if end_time:
            query = query.filter(EnergyData.timestamp <= end_time)
        if meter_id:
            query = query.filter(EnergyData.meter_id == meter_id)
        if system_status:
            query = query.filter(EnergyData.system_status == system_status)
        if min_electricity is not None:
            query = query.filter(EnergyData.electricity_kwh >= min_electricity)
        if max_electricity is not None:
            query = query.filter(EnergyData.electricity_kwh <= max_electricity)
        if min_water is not None:
            query = query.filter(EnergyData.water_m3 >= min_water)
        if max_water is not None:
            query = query.filter(EnergyData.water_m3 <= max_water)
        if min_hvac is not None:
            query = query.filter(EnergyData.hvac_kwh >= min_hvac)
        if max_hvac is not None:
            query = query.filter(EnergyData.hvac_kwh <= max_hvac)
        if min_temp is not None:
            query = query.filter(EnergyData.outdoor_temp >= min_temp)
        if max_temp is not None:
            query = query.filter(EnergyData.outdoor_temp <= max_temp)
        if min_humidity is not None:
            query = query.filter(EnergyData.humidity_pct >= min_humidity)
        if max_humidity is not None:
            query = query.filter(EnergyData.humidity_pct <= max_humidity)
        if occupancy_density is not None:
            query = query.filter(EnergyData.occupancy_density == occupancy_density)

        self._debug(
            "query_data",
            "filters_applied",
            building_id=building_id,
            building_type=building_type,
            start_time=start_time.isoformat() if start_time else None,
            end_time=end_time.isoformat() if end_time else None,
            meter_id=meter_id,
            system_status=system_status,
            page=page,
            page_size=page_size
        )
        
        total = query.count()

        if page_size is None or page_size <= 0:
            data = query.order_by(EnergyData.timestamp).all()
            effective_page = 1
            effective_page_size = total
        else:
            offset = (page - 1) * page_size
            data = query.order_by(EnergyData.timestamp).offset(offset).limit(page_size).all()
            effective_page = page
            effective_page_size = page_size
        
        return {
            "total": total,
            "data": data,
            "page": effective_page,
            "page_size": effective_page_size
        }
    
    def time_period_aggregation(
        self,
        building_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        period: str = "hour"
    ) -> Dict:
        result = self.query_data(
            building_id=building_id,
            start_time=start_time,
            end_time=end_time,
            page=1,
            page_size=None
        )
        data = result.get('data', [])
        
        if not data:
            return {"error": "No data found"}
        
        df = pd.DataFrame([{
            'timestamp': d.timestamp,
            'electricity_kwh': d.electricity_kwh,
            'water_m3': d.water_m3,
            'hvac_kwh': d.hvac_kwh,
            'outdoor_temp': d.outdoor_temp,
            'humidity_pct': d.humidity_pct
        } for d in data])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        
        if period == "hour":
            freq = 'H'
        elif period == "day":
            freq = 'D'
        elif period == "week":
            freq = 'W'
        elif period == "month":
            freq = 'M'
        else:
            freq = 'H'
        
        aggregated = df.resample(freq).agg({
            'electricity_kwh': 'sum',
            'water_m3': 'sum',
            'hvac_kwh': 'sum',
            'outdoor_temp': 'mean',
            'humidity_pct': 'mean'
        }).reset_index()
        
        return {
            "period": period,
            "data": aggregated.to_dict('records'),
            "summary": {
                "total_electricity_kwh": float(aggregated['electricity_kwh'].sum()),
                "total_water_m3": float(aggregated['water_m3'].sum()),
                "total_hvac_kwh": float(aggregated['hvac_kwh'].sum()),
                "avg_outdoor_temp": float(aggregated['outdoor_temp'].mean()),
                "avg_humidity": float(aggregated['humidity_pct'].mean())
            }
        }
    
    def calculate_cop(
        self,
        building_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        max_points: Optional[int] = 100
    ) -> Dict:
        result = self.query_data(
            building_id=building_id,
            start_time=start_time,
            end_time=end_time,
            page=1,
            page_size=None
        )
        data = result.get('data', [])
        
        if not data:
            return {"error": "No data found"}
        
        cop_values = []
        for d in data:
            if d.hvac_kwh and d.hvac_kwh > 0 and d.chw_supply_temp and d.chw_return_temp:
                delta_t = d.chw_return_temp - d.chw_supply_temp
                if delta_t > 0:
                    cop = delta_t / (d.hvac_kwh / 1000) if d.hvac_kwh > 0 else 0
                    cop_values.append({
                        "timestamp": d.timestamp.isoformat(),
                        "cop": cop,
                        "chw_supply_temp": d.chw_supply_temp,
                        "chw_return_temp": d.chw_return_temp,
                        "hvac_kwh": d.hvac_kwh
                    })
        
        if cop_values:
            avg_cop = np.mean([c['cop'] for c in cop_values])
            max_cop = np.max([c['cop'] for c in cop_values])
            min_cop = np.min([c['cop'] for c in cop_values])
        else:
            avg_cop = max_cop = min_cop = 0
        
        if max_points is None or max_points <= 0:
            cop_data = cop_values
        else:
            cop_data = cop_values[:max_points]

        return {
            "average_cop": float(avg_cop),
            "max_cop": float(max_cop),
            "min_cop": float(min_cop),
            "cop_data": cop_data,
            "total_points": len(cop_values)
        }
    
    def detect_anomalies(
        self,
        building_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        threshold: float = 3.0
    ) -> Dict:
        """增强的异常检测功能"""
        result = self.query_data(
            building_id=building_id,
            start_time=start_time,
            end_time=end_time,
            page=1,
            page_size=None
        )
        data = result.get('data', [])
        
        if not data:
            return {"error": "No data found"}
        
        df = pd.DataFrame([{
            'timestamp': d.timestamp,
            'electricity_kwh': d.electricity_kwh,
            'water_m3': d.water_m3,
            'hvac_kwh': d.hvac_kwh,
            'outdoor_temp': d.outdoor_temp,
            'humidity_pct': d.humidity_pct,
            'occupancy_density': d.occupancy_density,
            'chw_supply_temp': d.chw_supply_temp,
            'chw_return_temp': d.chw_return_temp,
            'system_status': d.system_status
        } for d in data])
        
        anomalies = []
        anomaly_details = []
        
        # 1. 统计异常检测 (Z-score方法)
        numeric_columns = ['electricity_kwh', 'water_m3', 'hvac_kwh', 'outdoor_temp', 'humidity_pct']
        for col in numeric_columns:
            if col in df.columns and not df[col].isnull().all():
                mean = df[col].mean()
                std = df[col].std()
                
                if std > 0:
                    z_scores = np.abs((df[col] - mean) / std)
                    anomaly_indices = df[z_scores > threshold].index
                    
                    for idx in anomaly_indices:
                        anomaly = {
                            "timestamp": df.loc[idx, 'timestamp'].isoformat(),
                            "metric": col,
                            "value": float(df.loc[idx, col]),
                            "mean": float(mean),
                            "std": float(std),
                            "z_score": float(z_scores[idx]),
                            "type": "statistical_outlier",
                            "severity": "high" if z_scores[idx] > threshold * 1.5 else "medium",
                            "building_id": building_id
                        }
                        anomalies.append(anomaly)
                        
                        # 添加异常详情和分析
                        detail = self.analyze_anomaly_detail(anomaly, df, idx)
                        anomaly_details.append(detail)
        
        # 2. 系统状态异常
        status_anomalies = df[df['system_status'] != 'Normal']
        for idx, row in status_anomalies.iterrows():
            anomaly = {
                "timestamp": row['timestamp'].isoformat(),
                "metric": "system_status",
                "value": row['system_status'],
                "type": "system_anomaly",
                "severity": "high",
                "building_id": building_id
            }
            anomalies.append(anomaly)
            
            detail = {
                "timestamp": row['timestamp'].isoformat(),
                "metric": "system_status",
                "value": row['system_status'],
                "type": "system_anomaly",
                "severity": "high",
                "description": f"系统状态异常: {row['system_status']}",
                "suggestion": "检查系统运行状态，可能需要维护或维修"
            }
            anomaly_details.append(detail)
        
        # 3. 时间序列异常检测 (基于趋势和季节性)
        time_based_anomalies = self.detect_time_based_anomalies(df, building_id)
        anomalies.extend(time_based_anomalies)
        
        # 4. 关系异常检测 (如HVAC与温度的关系)
        relationship_anomalies = self.detect_relationship_anomalies(df, building_id)
        anomalies.extend(relationship_anomalies)
        
        # 5. 计算异常统计信息
        anomaly_stats = self.calculate_anomaly_stats(anomalies)
        
        return {
            "total_anomalies": len(anomalies),
            "anomalies": anomalies[:100],
            "anomaly_details": anomaly_details[:50],
            "threshold": threshold,
            "statistics": anomaly_stats,
            "detection_time": datetime.now().isoformat()
        }
    
    def detect_time_based_anomalies(self, df: pd.DataFrame, building_id: Optional[str] = None) -> List[Dict]:
        """检测基于时间序列的异常"""
        time_anomalies = []
        
        # 检查时间序列的趋势和季节性异常
        if 'electricity_kwh' in df.columns and len(df) > 7:
            # 计算移动平均值
            df['electricity_ma7'] = df['electricity_kwh'].rolling(window=7).mean()
            df['electricity_std7'] = df['electricity_kwh'].rolling(window=7).std()
            
            # 检测趋势异常
            for i in range(7, len(df)):
                current = df.iloc[i]['electricity_kwh']
                ma = df.iloc[i]['electricity_ma7']
                std = df.iloc[i]['electricity_std7'] or 1
                
                if std > 0:
                    deviation = abs(current - ma) / std
                    if deviation > 3:
                        time_anomalies.append({
                            "timestamp": df.iloc[i]['timestamp'].isoformat(),
                            "metric": "electricity_kwh",
                            "value": float(current),
                            "mean": float(ma),
                            "std": float(std),
                            "type": "time_series_anomaly",
                            "severity": "medium",
                            "building_id": building_id
                        })
        
        return time_anomalies
    
    def detect_relationship_anomalies(self, df: pd.DataFrame, building_id: Optional[str] = None) -> List[Dict]:
        """检测基于关系的异常"""
        relationship_anomalies = []
        
        # 检查HVAC与温度的关系
        if 'hvac_kwh' in df.columns and 'outdoor_temp' in df.columns:
            # 计算相关性
            if len(df) > 10:
                corr = df['hvac_kwh'].corr(df['outdoor_temp'])
                
                # 对于夏季，HVAC消耗应该随温度升高而增加
                # 对于冬季，HVAC消耗也应该随温度降低而增加
                summer_df = df[df['timestamp'].dt.month.isin([6,7,8])]
                if len(summer_df) > 5:
                    summer_corr = summer_df['hvac_kwh'].corr(summer_df['outdoor_temp'])
                    if summer_corr < 0:
                        # 夏季HVAC消耗与温度负相关，可能异常
                        relationship_anomalies.append({
                            "timestamp": df.iloc[-1]['timestamp'].isoformat(),
                            "metric": "hvac_vs_temperature",
                            "value": float(summer_corr),
                            "type": "relationship_anomaly",
                            "severity": "medium",
                            "building_id": building_id,
                            "description": "夏季HVAC消耗与温度负相关，可能存在异常"
                        })
        
        # 检查CHW温度差
        if 'chw_supply_temp' in df.columns and 'chw_return_temp' in df.columns:
            df['chw_temp_diff'] = df['chw_return_temp'] - df['chw_supply_temp']
            valid_diff = df[df['chw_temp_diff'] > 0]
            if len(valid_diff) > 0:
                avg_diff = valid_diff['chw_temp_diff'].mean()
                std_diff = valid_diff['chw_temp_diff'].std()
                
                if std_diff > 0:
                    for i, row in valid_diff.iterrows():
                        diff = row['chw_temp_diff']
                        z_score = abs((diff - avg_diff) / std_diff)
                        if z_score > 3:
                            relationship_anomalies.append({
                                "timestamp": row['timestamp'].isoformat(),
                                "metric": "chw_temp_diff",
                                "value": float(diff),
                                "mean": float(avg_diff),
                                "std": float(std_diff),
                                "type": "temperature_diff_anomaly",
                                "severity": "high",
                                "building_id": building_id
                            })
        
        return relationship_anomalies
    
    def analyze_anomaly_detail(self, anomaly: Dict, df: pd.DataFrame, index: int) -> Dict:
        """分析异常详情并提供建议"""
        detail = anomaly.copy()
        
        # 添加异常描述
        if anomaly['type'] == 'statistical_outlier':
            detail['description'] = f"{anomaly['metric']}值异常，偏离平均值{anomaly['z_score']:.2f}个标准差"
            
            # 基于指标类型提供建议
            if anomaly['metric'] == 'electricity_kwh':
                detail['suggestion'] = "检查电气设备是否有故障或过度使用"
            elif anomaly['metric'] == 'water_m3':
                detail['suggestion'] = "检查是否有水管泄漏或异常用水"
            elif anomaly['metric'] == 'hvac_kwh':
                detail['suggestion'] = "检查HVAC系统是否运行正常，可能需要维护"
            elif anomaly['metric'] == 'outdoor_temp':
                detail['suggestion'] = "检查温度传感器是否正常工作"
            elif anomaly['metric'] == 'humidity_pct':
                detail['suggestion'] = "检查湿度传感器是否正常工作"
        
        # 添加上下文信息
        if index > 0 and index < len(df) - 1:
            prev_value = df.iloc[index-1][anomaly['metric']]
            next_value = df.iloc[index+1][anomaly['metric']]
            detail['context'] = {
                "previous_value": float(prev_value) if pd.notna(prev_value) else None,
                "next_value": float(next_value) if pd.notna(next_value) else None
            }
        
        return detail
    
    def calculate_anomaly_stats(self, anomalies: List[Dict]) -> Dict:
        """计算异常统计信息"""
        if not anomalies:
            return {
                "by_severity": {},
                "by_type": {},
                "by_metric": {}
            }
        
        # 按严重程度统计
        severity_counts = {}
        for anomaly in anomalies:
            severity = anomaly.get('severity', 'medium')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # 按类型统计
        type_counts = {}
        for anomaly in anomalies:
            anomaly_type = anomaly.get('type', 'unknown')
            type_counts[anomaly_type] = type_counts.get(anomaly_type, 0) + 1
        
        # 按指标统计
        metric_counts = {}
        for anomaly in anomalies:
            metric = anomaly.get('metric', 'unknown')
            metric_counts[metric] = metric_counts.get(metric, 0) + 1
        
        return {
            "by_severity": severity_counts,
            "by_type": type_counts,
            "by_metric": metric_counts
        }
    
    def energy_consumption_ranking(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        top_n: int = 10
    ) -> Dict:
        query = self.db.query(
            EnergyData.building_id,
            func.sum(EnergyData.electricity_kwh).label('total_electricity'),
            func.sum(EnergyData.water_m3).label('total_water'),
            func.sum(EnergyData.hvac_kwh).label('total_hvac')
        )
        
        if start_time:
            query = query.filter(EnergyData.timestamp >= start_time)
        if end_time:
            query = query.filter(EnergyData.timestamp <= end_time)
        
        results = query.group_by(EnergyData.building_id).all()
        
        ranking = sorted(results, key=lambda x: x.total_electricity or 0, reverse=True)[:top_n]
        
        return {
            "ranking": [{
                "building_id": r.building_id,
                "total_electricity_kwh": float(r.total_electricity or 0),
                "total_water_m3": float(r.total_water or 0),
                "total_hvac_kwh": float(r.total_hvac or 0)
            } for r in ranking]
        }
    
    def energy_trend_analysis(
        self,
        building_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        metric: str = "electricity_kwh"
    ) -> Dict:
        allowed_metrics = {
            "electricity_kwh",
            "water_m3",
            "hvac_kwh",
            "outdoor_temp",
            "humidity_pct",
            "occupancy_density"
        }
        if metric not in allowed_metrics:
            return {"error": f"Unsupported metric: {metric}"}

        result = self.query_data(
            building_id=building_id,
            start_time=start_time,
            end_time=end_time,
            page=1,
            page_size=None
        )
        data = result.get('data', [])
        
        if not data:
            return {"error": "No data found"}
        
        df = pd.DataFrame([{
            'timestamp': d.timestamp,
            metric: getattr(d, metric)
        } for d in data])

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df[metric] = pd.to_numeric(df[metric], errors='coerce').fillna(0.0)
        df = df.set_index('timestamp')

        daily = df.resample('D').sum(numeric_only=True)
        if metric not in daily.columns:
            daily[metric] = 0.0

        rolling_mean = daily[metric].rolling(window=7, min_periods=1).mean()

        daily_data = [
            {
                "timestamp": ts.isoformat(),
                metric: float(row.get(metric, 0.0))
            }
            for ts, row in daily.iterrows()
        ]
        rolling_data = [
            {
                "timestamp": ts.isoformat(),
                metric: float(val) if pd.notna(val) else None
            }
            for ts, val in rolling_mean.items()
        ]

        return {
            "metric": metric,
            "daily_data": daily_data,
            "rolling_mean": rolling_data
        }
    
    def peak_demand_analysis(
        self,
        building_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict:
        result = self.query_data(
            building_id=building_id,
            start_time=start_time,
            end_time=end_time,
            page=1,
            page_size=None
        )
        data = result.get('data', [])
        self._debug("peak_demand_analysis", "query_loaded", total=result.get('total'), rows=len(data))
        
        if not data:
            self._debug("peak_demand_analysis", "no_data")
            return {"error": "No data found"}
        
        df = pd.DataFrame([{
            'timestamp': d.timestamp,
            'electricity_kwh': d.electricity_kwh
        } for d in data])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        
        hourly_avg = df.groupby('hour')['electricity_kwh'].mean()
        peak_hour = hourly_avg.idxmax()
        
        daily_peak = df.groupby(df['timestamp'].dt.date)['electricity_kwh'].max()
        
        response = {
            "peak_hour": int(peak_hour),
            "peak_hour_avg_consumption": float(hourly_avg[peak_hour]),
            "hourly_profile": hourly_avg.to_dict(),
            "daily_peak_data": [{"date": str(k), "peak": float(v)} for k, v in daily_peak.items()]
        }
        self._debug("peak_demand_analysis", "result_ready", **self._summarize_result(response))
        return response
    
    def energy_intensity_analysis(
        self,
        building_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        building_area: float = 1000.0
    ) -> Dict:
        result = self.query_data(
            building_id=building_id,
            start_time=start_time,
            end_time=end_time,
            page=1,
            page_size=None
        )
        data = result.get('data', [])
        self._debug("energy_intensity_analysis", "query_loaded", total=result.get('total'), rows=len(data), building_area=building_area)
        
        if not data:
            self._debug("energy_intensity_analysis", "no_data")
            return {"error": "No data found"}
        
        df = pd.DataFrame([{
            'timestamp': d.timestamp,
            'electricity_kwh': d.electricity_kwh,
            'occupancy_density': d.occupancy_density
        } for d in data])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        
        daily_energy = df.groupby('date')['electricity_kwh'].sum()
        daily_intensity = daily_energy / building_area
        
        avg_occupancy = df.groupby('date')['occupancy_density'].mean()
        
        response = {
            "building_area_sqm": building_area,
            "daily_intensity_kwh_per_sqm": [{"date": str(k), "intensity": float(v)} for k, v in daily_intensity.items()],
            "average_intensity": float(daily_intensity.mean()),
            "occupancy_correlation": float(daily_intensity.corr(avg_occupancy)) if len(daily_intensity) > 1 else 0
        }
        self._debug("energy_intensity_analysis", "result_ready", **self._summarize_result(response))
        return response
    
    def comparative_analysis(
        self,
        building_ids: List[str],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict:
        results = {}
        self._debug("comparative_analysis", "start", building_ids=building_ids, start_time=start_time.isoformat() if start_time else None, end_time=end_time.isoformat() if end_time else None)
        
        for building_id in building_ids:
            result = self.query_data(
                building_id=building_id,
                start_time=start_time,
                end_time=end_time,
                page=1,
                page_size=None
            )
            data = result.get('data', [])
            self._debug("comparative_analysis", "building_loaded", building_id=building_id, total=result.get('total'), rows=len(data))
            
            if data:
                df = pd.DataFrame([{
                    'electricity_kwh': d.electricity_kwh,
                    'water_m3': d.water_m3,
                    'hvac_kwh': d.hvac_kwh
                } for d in data])
                
                results[building_id] = {
                    "total_electricity": float(df['electricity_kwh'].sum()),
                    "total_water": float(df['water_m3'].sum()),
                    "total_hvac": float(df['hvac_kwh'].sum()),
                    "avg_electricity": float(df['electricity_kwh'].mean()),
                    "avg_water": float(df['water_m3'].mean()),
                    "avg_hvac": float(df['hvac_kwh'].mean())
                }
        
        response = {
            "comparison_data": results,
            "building_count": len(results)
        }
        self._debug("comparative_analysis", "result_ready", **self._summarize_result(response))
        return response
    
    def weather_correlation_analysis(
        self,
        building_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict:
        result = self.query_data(
            building_id=building_id,
            start_time=start_time,
            end_time=end_time,
            page=1,
            page_size=None
        )
        data = result.get('data', [])
        self._debug("weather_correlation_analysis", "query_loaded", total=result.get('total'), rows=len(data))
        
        if not data:
            self._debug("weather_correlation_analysis", "no_data")
            return {"error": "No data found"}
        
        df = pd.DataFrame([{
            'electricity_kwh': d.electricity_kwh,
            'hvac_kwh': d.hvac_kwh,
            'outdoor_temp': d.outdoor_temp,
            'humidity_pct': d.humidity_pct
        } for d in data])
        
        df = df.dropna()
        
        correlations = {}
        if len(df) > 1:
            correlations['electricity_vs_temp'] = float(df['electricity_kwh'].corr(df['outdoor_temp']))
            correlations['electricity_vs_humidity'] = float(df['electricity_kwh'].corr(df['humidity_pct']))
            correlations['hvac_vs_temp'] = float(df['hvac_kwh'].corr(df['outdoor_temp']))
            correlations['hvac_vs_humidity'] = float(df['hvac_kwh'].corr(df['humidity_pct']))
        
        response = {
            "correlations": correlations,
            "data_points": len(df)
        }
        self._debug("weather_correlation_analysis", "result_ready", **self._summarize_result(response))
        return response
    
    def occupancy_impact_analysis(
        self,
        building_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict:
        result = self.query_data(
            building_id=building_id,
            start_time=start_time,
            end_time=end_time,
            page=1,
            page_size=None
        )
        data = result.get('data', [])
        self._debug("occupancy_impact_analysis", "query_loaded", total=result.get('total'), rows=len(data))
        
        if not data:
            self._debug("occupancy_impact_analysis", "no_data")
            return {"error": "No data found"}
        
        df = pd.DataFrame([{
            'electricity_kwh': d.electricity_kwh,
            'hvac_kwh': d.hvac_kwh,
            'occupancy_density': d.occupancy_density
        } for d in data])
        
        df = df.dropna()
        
        if len(df) > 1:
            correlation = float(df['electricity_kwh'].corr(df['occupancy_density']))
            
            df['occupancy_level'] = pd.cut(df['occupancy_density'], bins=3, labels=['Low', 'Medium', 'High'])
            occupancy_impact = df.groupby('occupancy_level')['electricity_kwh'].mean().to_dict()
        else:
            correlation = 0
            occupancy_impact = {}
        
        response = {
            "correlation": correlation,
            "occupancy_impact": occupancy_impact
        }
        self._debug("occupancy_impact_analysis", "result_ready", **self._summarize_result(response))
        return response
    
    def hourly_pattern_analysis(
        self,
        building_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict:
        result = self.query_data(
            building_id=building_id,
            start_time=start_time,
            end_time=end_time,
            page=1,
            page_size=None
        )
        data = result.get('data', [])
        self._debug("hourly_pattern_analysis", "query_loaded", total=result.get('total'), rows=len(data))
        
        if not data:
            self._debug("hourly_pattern_analysis", "no_data")
            return {"error": "No data found"}
        
        df = pd.DataFrame([{
            'timestamp': d.timestamp,
            'electricity_kwh': d.electricity_kwh,
            'water_m3': d.water_m3,
            'hvac_kwh': d.hvac_kwh
        } for d in data])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        
        hourly_pattern = df.groupby('hour').agg({
            'electricity_kwh': 'mean',
            'water_m3': 'mean',
            'hvac_kwh': 'mean'
        }).to_dict('index')
        
        response = {
            "hourly_pattern": {str(k): v for k, v in hourly_pattern.items()}
        }
        self._debug("hourly_pattern_analysis", "result_ready", **self._summarize_result(response))
        return response
    
    def weekly_pattern_analysis(
        self,
        building_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict:
        result = self.query_data(
            building_id=building_id,
            start_time=start_time,
            end_time=end_time,
            page=1,
            page_size=None
        )
        data = result.get('data', [])
        self._debug("weekly_pattern_analysis", "query_loaded", total=result.get('total'), rows=len(data))
        
        if not data:
            self._debug("weekly_pattern_analysis", "no_data")
            return {"error": "No data found"}
        
        df = pd.DataFrame([{
            'timestamp': d.timestamp,
            'electricity_kwh': d.electricity_kwh,
            'water_m3': d.water_m3,
            'hvac_kwh': d.hvac_kwh
        } for d in data])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        
        weekly_pattern = df.groupby('day_of_week').agg({
            'electricity_kwh': 'mean',
            'water_m3': 'mean',
            'hvac_kwh': 'mean'
        }).to_dict('index')
        
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        response = {
            "weekly_pattern": {day_names[k]: v for k, v in weekly_pattern.items()}
        }
        self._debug("weekly_pattern_analysis", "result_ready", **self._summarize_result(response))
        return response
    
    def seasonal_analysis(
        self,
        building_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict:
        result = self.query_data(
            building_id=building_id,
            start_time=start_time,
            end_time=end_time,
            page=1,
            page_size=None
        )
        data = result.get('data', [])
        self._debug("seasonal_analysis", "query_loaded", total=result.get('total'), rows=len(data))
        
        if not data:
            self._debug("seasonal_analysis", "no_data")
            return {"error": "No data found"}
        
        df = pd.DataFrame([{
            'timestamp': d.timestamp,
            'electricity_kwh': d.electricity_kwh,
            'hvac_kwh': d.hvac_kwh,
            'outdoor_temp': d.outdoor_temp
        } for d in data])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['month'] = df['timestamp'].dt.month
        
        def get_season(month):
            if month in [3, 4, 5]:
                return 'Spring'
            elif month in [6, 7, 8]:
                return 'Summer'
            elif month in [9, 10, 11]:
                return 'Autumn'
            else:
                return 'Winter'
        
        df['season'] = df['month'].apply(get_season)
        
        seasonal_pattern = df.groupby('season').agg({
            'electricity_kwh': 'mean',
            'hvac_kwh': 'mean',
            'outdoor_temp': 'mean'
        }).to_dict('index')
        
        response = {
            "seasonal_pattern": seasonal_pattern
        }
        self._debug("seasonal_analysis", "result_ready", **self._summarize_result(response))
        return response
    
    def energy_efficiency_analysis(
        self,
        building_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict:
        """能耗效率分析"""
        result = self.query_data(
            building_id=building_id,
            start_time=start_time,
            end_time=end_time,
            page=1,
            page_size=None
        )
        data = result.get('data', [])
        
        if not data:
            return {"error": "No data found"}
        
        df = pd.DataFrame([{
            'timestamp': d.timestamp,
            'electricity_kwh': d.electricity_kwh,
            'hvac_kwh': d.hvac_kwh,
            'outdoor_temp': d.outdoor_temp,
            'chw_supply_temp': d.chw_supply_temp,
            'chw_return_temp': d.chw_return_temp
        } for d in data])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['month'] = df['timestamp'].dt.month
        
        # 计算能耗效率指标
        df['hvac_efficiency'] = df.apply(lambda row: 
            (row['chw_return_temp'] - row['chw_supply_temp']) / row['hvac_kwh'] if row['hvac_kwh'] > 0 else 0,
            axis=1
        )
        
        monthly_efficiency = df.groupby('month').agg({
            'hvac_efficiency': 'mean',
            'electricity_kwh': 'mean',
            'hvac_kwh': 'mean'
        }).to_dict('index')
        
        overall_efficiency = {
            'avg_hvac_efficiency': float(df['hvac_efficiency'].mean()),
            'total_electricity': float(df['electricity_kwh'].sum()),
            'total_hvac': float(df['hvac_kwh'].sum()),
            'hvac_percentage': float(df['hvac_kwh'].sum() / df['electricity_kwh'].sum() * 100) if df['electricity_kwh'].sum() > 0 else 0
        }
        
        return {
            "monthly_efficiency": monthly_efficiency,
            "overall_efficiency": overall_efficiency
        }
    
    def equipment_performance_analysis(
        self,
        building_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict:
        """设备性能分析"""
        result = self.query_data(
            building_id=building_id,
            start_time=start_time,
            end_time=end_time,
            page=1,
            page_size=None
        )
        data = result.get('data', [])
        
        if not data:
            return {"error": "No data found"}
        
        df = pd.DataFrame([{
            'timestamp': d.timestamp,
            'chw_supply_temp': d.chw_supply_temp,
            'chw_return_temp': d.chw_return_temp,
            'hvac_kwh': d.hvac_kwh
        } for d in data])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        
        # 计算设备性能指标
        df['temp_diff'] = df['chw_return_temp'] - df['chw_supply_temp']
        df['cop'] = df.apply(lambda row: 
            row['temp_diff'] / (row['hvac_kwh'] / 1000) if row['hvac_kwh'] > 0 and row['temp_diff'] > 0 else 0,
            axis=1
        )
        
        daily_performance = df.groupby('date').agg({
            'cop': 'mean',
            'temp_diff': 'mean',
            'hvac_kwh': 'sum'
        }).reset_index()
        
        equipment_health = {
            'avg_cop': float(df['cop'].mean()),
            'max_cop': float(df['cop'].max()),
            'min_cop': float(df['cop'].min()),
            'avg_temp_diff': float(df['temp_diff'].mean()),
            'total_hvac_energy': float(df['hvac_kwh'].sum())
        }
        
        return {
            "daily_performance": daily_performance.to_dict('records'),
            "equipment_health": equipment_health
        }
    
    def energy_prediction(
        self,
        building_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        prediction_days: int = 7
    ) -> Dict:
        """能耗预测"""
        result = self.query_data(
            building_id=building_id,
            start_time=start_time,
            end_time=end_time,
            page=1,
            page_size=None
        )
        data = result.get('data', [])
        
        if not data:
            return {"error": "No data found"}
        
        df = pd.DataFrame([{
            'timestamp': d.timestamp,
            'electricity_kwh': d.electricity_kwh,
            'hvac_kwh': d.hvac_kwh,
            'outdoor_temp': d.outdoor_temp
        } for d in data])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        
        # 按天聚合
        daily_data = df.resample('D').agg({
            'electricity_kwh': 'sum',
            'hvac_kwh': 'sum',
            'outdoor_temp': 'mean'
        })
        
        # 简单移动平均预测
        daily_data['electricity_pred'] = daily_data['electricity_kwh'].rolling(window=7).mean()
        daily_data['hvac_pred'] = daily_data['hvac_kwh'].rolling(window=7).mean()
        
        # 生成未来预测
        last_date = daily_data.index[-1]
        predictions = []
        
        for i in range(1, prediction_days + 1):
            pred_date = last_date + timedelta(days=i)
            pred_electricity = float(daily_data['electricity_pred'].iloc[-1])
            pred_hvac = float(daily_data['hvac_pred'].iloc[-1])
            
            predictions.append({
                "date": pred_date.isoformat(),
                "predicted_electricity_kwh": pred_electricity,
                "predicted_hvac_kwh": pred_hvac
            })
        
        return {
            "historical_data": daily_data.reset_index().to_dict('records'),
            "predictions": predictions,
            "prediction_days": prediction_days
        }
    
    def energy_savings_potential(
        self,
        building_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict:
        """节能潜力分析"""
        result = self.query_data(
            building_id=building_id,
            start_time=start_time,
            end_time=end_time,
            page=1,
            page_size=None
        )
        data = result.get('data', [])
        
        if not data:
            return {"error": "No data found"}
        
        df = pd.DataFrame([{
            'timestamp': d.timestamp,
            'electricity_kwh': d.electricity_kwh,
            'hvac_kwh': d.hvac_kwh,
            'outdoor_temp': d.outdoor_temp
        } for d in data])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        
        # 分析不同时段的能耗
        hourly_pattern = df.groupby('hour')['electricity_kwh'].mean().to_dict()
        weekday_pattern = df.groupby('day_of_week')['electricity_kwh'].mean().to_dict()
        
        # 计算基准能耗
        baseline_energy = float(df['electricity_kwh'].sum())
        
        # 计算节能潜力
        # 1. 调整非工作时间的能耗
        non_working_hours = [0, 1, 2, 3, 4, 5, 6, 7, 18, 19, 20, 21, 22, 23]
        working_hours_energy = df[~df['hour'].isin(non_working_hours)]['electricity_kwh'].sum()
        non_working_hours_energy = df[df['hour'].isin(non_working_hours)]['electricity_kwh'].sum()
        
        # 假设非工作时间能耗可以降低50%
        potential_savings_non_working = non_working_hours_energy * 0.5
        
        # 2. 调整周末能耗
        weekend_days = [5, 6]  # 周六和周日
        weekday_energy = df[~df['day_of_week'].isin(weekend_days)]['electricity_kwh'].sum()
        weekend_energy = df[df['day_of_week'].isin(weekend_days)]['electricity_kwh'].sum()
        
        # 假设周末能耗可以降低30%
        potential_savings_weekend = weekend_energy * 0.3
        
        # 3. HVAC优化
        hvac_energy = float(df['hvac_kwh'].sum())
        potential_savings_hvac = hvac_energy * 0.2  # 假设HVAC可以节能20%
        
        total_potential_savings = potential_savings_non_working + potential_savings_weekend + potential_savings_hvac
        savings_percentage = (total_potential_savings / baseline_energy) * 100 if baseline_energy > 0 else 0
        
        return {
            "baseline_energy_kwh": baseline_energy,
            "potential_savings": {
                "non_working_hours": float(potential_savings_non_working),
                "weekend": float(potential_savings_weekend),
                "hvac_optimization": float(potential_savings_hvac),
                "total": float(total_potential_savings)
            },
            "savings_percentage": float(savings_percentage),
            "hourly_pattern": hourly_pattern,
            "weekday_pattern": weekday_pattern
        }
    
    def cost_analysis(
        self,
        building_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        electricity_price: float = 0.6,
        water_price: float = 5.0
    ) -> Dict:
        """成本分析"""
        result = self.query_data(
            building_id=building_id,
            start_time=start_time,
            end_time=end_time,
            page=1,
            page_size=None
        )
        data = result.get('data', [])
        
        if not data:
            return {"error": "No data found"}
        
        df = pd.DataFrame([{
            'timestamp': d.timestamp,
            'electricity_kwh': d.electricity_kwh,
            'water_m3': d.water_m3,
            'hvac_kwh': d.hvac_kwh
        } for d in data])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['month'] = df['timestamp'].dt.month
        
        # 计算成本
        df['electricity_cost'] = df['electricity_kwh'] * electricity_price
        df['water_cost'] = df['water_m3'] * water_price
        df['hvac_cost'] = df['hvac_kwh'] * electricity_price
        df['total_cost'] = df['electricity_cost'] + df['water_cost']
        
        monthly_cost = df.groupby('month').agg({
            'electricity_cost': 'sum',
            'water_cost': 'sum',
            'hvac_cost': 'sum',
            'total_cost': 'sum'
        }).to_dict('index')
        
        total_cost = {
            'electricity': float(df['electricity_cost'].sum()),
            'water': float(df['water_cost'].sum()),
            'hvac': float(df['hvac_cost'].sum()),
            'total': float(df['total_cost'].sum())
        }
        
        return {
            "monthly_cost": monthly_cost,
            "total_cost": total_cost,
            "prices": {
                "electricity_price": electricity_price,
                "water_price": water_price
            }
        }
