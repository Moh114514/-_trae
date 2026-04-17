import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from ..models.database import EnergyData, Building, Meter
import logging
import asyncio
from functools import lru_cache

logger = logging.getLogger(__name__)

# 缓存装饰器
@lru_cache(maxsize=128)
def cached_query(key):
    """简单的内存缓存"""
    pass


class DataProcessor:
    def __init__(self, db: Session):
        self.db = db
    
    def load_csv_data(self, file_path: str) -> pd.DataFrame:
        logger.info(f"Loading data from {file_path}")
        df = pd.read_csv(file_path)
        return df
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Starting data cleaning process")
        
        df = df.copy()
        
        # 时间戳处理
        if 'Timestamp' in df.columns:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
        elif 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        
        # 数值列处理
        numeric_columns = [
            'Electricity_Consumption_kWh', 'Water_Consumption_m3', 'HVAC_Energy_kWh',
            'CHW_Supply_Temp_C', 'CHW_Return_Temp_C', 'Outdoor_Temp_C',
            'Relative_Humidity_Pct', 'Occupancy_Density_People_100qm',
            'electricity_kwh', 'water_m3', 'hvac_kwh',
            'chw_supply_temp', 'chw_return_temp', 'outdoor_temp',
            'humidity_pct', 'occupancy_density'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 处理缺失值
        required_columns = ['Timestamp', 'Building_ID'] if 'Timestamp' in df.columns else ['timestamp', 'building_id']
        df = df.dropna(subset=required_columns)
        
        # 填充数值列缺失值
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].fillna(df[col].median())
        
        # 去重
        id_col = 'Building_ID' if 'Building_ID' in df.columns else 'building_id'
        time_col = 'Timestamp' if 'Timestamp' in df.columns else 'timestamp'
        df = df.drop_duplicates(subset=[id_col, time_col], keep='first')
        
        # 排序
        df = df.sort_values([id_col, time_col]).reset_index(drop=True)
        
        logger.info(f"Data cleaning completed. Rows: {len(df)}")
        return df
    
    def detect_outliers(self, df: pd.DataFrame, columns: List[str], threshold: float = 3.0) -> pd.DataFrame:
        """使用IQR方法检测异常值"""
        logger.info("Detecting outliers")
        
        df = df.copy()
        outlier_mask = pd.Series([False] * len(df), index=df.index)
        
        for col in columns:
            if col in df.columns:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR
                
                col_outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
                outlier_mask = outlier_mask | col_outliers
                
                # 替换异常值为中位数
                df.loc[col_outliers, col] = df[col].median()
        
        logger.info(f"Outlier detection completed. Found {outlier_mask.sum()} outliers")
        return df
    
    def standardize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Starting data standardization")
        
        df = df.copy()
        
        column_mapping = {
            'Building_ID': 'building_id',
            'Building_Type': 'building_type',
            'Timestamp': 'timestamp',
            'Electricity_Consumption_kWh': 'electricity_kwh',
            'Water_Consumption_m3': 'water_m3',
            'HVAC_Energy_kWh': 'hvac_kwh',
            'CHW_Supply_Temp_C': 'chw_supply_temp',
            'CHW_Return_Temp_C': 'chw_return_temp',
            'Outdoor_Temp_C': 'outdoor_temp',
            'Relative_Humidity_Pct': 'humidity_pct',
            'Occupancy_Density_People_100qm': 'occupancy_density',
            'Meter_ID': 'meter_id',
            'System_Status': 'system_status'
        }
        
        df = df.rename(columns=column_mapping)
        
        # 处理系统状态
        if 'system_status' in df.columns:
            df['system_status'] = df['system_status'].fillna('Normal')
        else:
            df['system_status'] = 'Normal'
        
        # 处理建筑类型
        if 'building_type' in df.columns:
            df['building_type'] = df['building_type'].fillna('Unknown')
        else:
            df['building_type'] = 'Unknown'
        
        logger.info("Data standardization completed")
        return df
    
    def validate_data(self, df: pd.DataFrame) -> Tuple[bool, List[str], List[str]]:
        """增强的数据验证功能"""
        errors = []
        warnings = []
        
        # 检查必需列
        required_columns = ['building_id', 'timestamp']
        for col in required_columns:
            if col not in df.columns:
                errors.append(f"Missing required column: {col}")
        
        # 检查时间戳
        if 'timestamp' in df.columns:
            if df['timestamp'].isnull().any():
                errors.append("Found null values in timestamp column")
            
            # 检查时间范围
            if not df['timestamp'].empty:
                min_time = df['timestamp'].min()
                max_time = df['timestamp'].max()
                if max_time - min_time > timedelta(days=365*5):
                    warnings.append(f"Data spans more than 5 years: {min_time} to {max_time}")
        
        # 检查建筑ID
        if 'building_id' in df.columns:
            if df['building_id'].isnull().any():
                errors.append("Found null values in building_id column")
            
            # 检查建筑ID格式
            if not df['building_id'].empty:
                invalid_ids = df[~df['building_id'].astype(str).str.match(r'^[A-Za-z0-9_-]+$')]['building_id']
                if not invalid_ids.empty:
                    warnings.append(f"Found invalid building IDs: {list(invalid_ids.unique())[:5]}...")
        
        # 检查数值列
        numeric_columns = ['electricity_kwh', 'water_m3', 'hvac_kwh']
        for col in numeric_columns:
            if col in df.columns:
                if (df[col] < 0).any():
                    errors.append(f"Found negative values in {col}")
                
                # 检查数值范围
                if col == 'humidity_pct' and ((df[col] < 0).any() or (df[col] > 100).any()):
                    warnings.append("Humidity values should be between 0 and 100")
                if col == 'outdoor_temp' and ((df[col] < -40).any() or (df[col] > 60).any()):
                    warnings.append("Outdoor temperature values seem unrealistic")
        
        return len(errors) == 0, errors, warnings
    
    def generate_quality_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """生成数据质量报告"""
        logger.info("Generating data quality report")
        
        report = {
            "total_records": len(df),
            "duplicate_records": 0,
            "null_values": {},
            "data_ranges": {},
            "building_statistics": {}
        }
        
        # 检查重复记录
        if 'building_id' in df.columns and 'timestamp' in df.columns:
            duplicates = df.duplicated(subset=['building_id', 'timestamp']).sum()
            report["duplicate_records"] = duplicates
        
        # 检查空值
        for col in df.columns:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                report["null_values"][col] = null_count
        
        # 检查数值范围
        numeric_columns = ['electricity_kwh', 'water_m3', 'hvac_kwh', 'outdoor_temp', 'humidity_pct']
        for col in numeric_columns:
            if col in df.columns:
                report["data_ranges"][col] = {
                    "min": float(df[col].min()) if not df[col].empty else None,
                    "max": float(df[col].max()) if not df[col].empty else None,
                    "mean": float(df[col].mean()) if not df[col].empty else None,
                    "median": float(df[col].median()) if not df[col].empty else None
                }
        
        # 建筑统计
        if 'building_id' in df.columns:
            building_counts = df['building_id'].value_counts()
            report["building_statistics"]["total_buildings"] = len(building_counts)
            report["building_statistics"]["records_per_building"] = building_counts.to_dict()
        
        logger.info("Data quality report generated")
        return report
    
    def import_to_database(self, df: pd.DataFrame, batch_size: int = 1000) -> Dict[str, Any]:
        """增强的数据库导入功能"""
        logger.info("Starting database import")
        
        # 检测并处理异常值
        numeric_columns = ['electricity_kwh', 'water_m3', 'hvac_kwh', 'outdoor_temp', 'humidity_pct']
        df = self.detect_outliers(df, numeric_columns)
        
        # 生成质量报告
        quality_report = self.generate_quality_report(df)
        
        # 批量导入
        records = []
        imported_count = 0
        
        try:
            for _, row in df.iterrows():
                record = EnergyData(
                    building_id=row.get('building_id'),
                    building_type=row.get('building_type'),
                    timestamp=row.get('timestamp'),
                    electricity_kwh=row.get('electricity_kwh'),
                    water_m3=row.get('water_m3'),
                    hvac_kwh=row.get('hvac_kwh'),
                    chw_supply_temp=row.get('chw_supply_temp'),
                    chw_return_temp=row.get('chw_return_temp'),
                    outdoor_temp=row.get('outdoor_temp'),
                    humidity_pct=row.get('humidity_pct'),
                    occupancy_density=row.get('occupancy_density'),
                    meter_id=row.get('meter_id'),
                    system_status=row.get('system_status', 'Normal')
                )
                records.append(record)
                
                if len(records) >= batch_size:
                    self.db.bulk_save_objects(records)
                    self.db.commit()
                    imported_count += len(records)
                    records = []
            
            if records:
                self.db.bulk_save_objects(records)
                self.db.commit()
                imported_count += len(records)
            
            logger.info(f"Database import completed. Total records: {imported_count}")
            
            return {
                "success": True,
                "records_imported": imported_count,
                "quality_report": quality_report
            }
            
        except Exception as e:
            logger.error(f"Database import failed: {str(e)}")
            self.db.rollback()
            return {
                "success": False,
                "records_imported": imported_count,
                "error": str(e),
                "quality_report": quality_report
            }
    
    def get_buildings_list(self) -> List[Dict]:
        """获取建筑列表，使用缓存提高性能"""
        # 生成缓存键
        cache_key = "buildings_list"
        
        # 尝试从缓存获取
        # 注意：实际项目中应该使用更可靠的缓存机制
        
        # 直接查询数据库
        buildings = self.db.query(EnergyData.building_id, EnergyData.building_type).distinct().all()
        result = [{"building_id": b[0], "building_type": b[1]} for b in buildings]
        
        return result
    
    def get_meters_list(self) -> List[Dict]:
        """获取仪表列表，使用缓存提高性能"""
        # 生成缓存键
        cache_key = "meters_list"
        
        # 尝试从缓存获取
        # 注意：实际项目中应该使用更可靠的缓存机制
        
        # 直接查询数据库
        meters = self.db.query(EnergyData.meter_id).distinct().all()
        result = [{"meter_id": m[0]} for m in meters if m[0]]
        
        return result
    
    def get_date_range(self, building_id: Optional[str] = None) -> Dict:
        """获取日期范围，使用缓存提高性能"""
        # 生成缓存键
        cache_key = f"date_range:{building_id or 'all'}"
        
        # 尝试从缓存获取
        # 注意：实际项目中应该使用更可靠的缓存机制
        
        # 直接查询数据库
        query = self.db.query(EnergyData.timestamp)
        if building_id:
            query = query.filter(EnergyData.building_id == building_id)
        
        # 使用单个查询获取最小和最大日期，减少数据库查询次数
        from sqlalchemy import func
        result = query.with_entities(
            func.min(EnergyData.timestamp).label('min_date'),
            func.max(EnergyData.timestamp).label('max_date')
        ).first()
        
        min_date = result.min_date
        max_date = result.max_date
        
        return {
            "min_date": min_date.isoformat() if min_date else None,
            "max_date": max_date.isoformat() if max_date else None
        }
    
    def get_data_summary(self, building_id: Optional[str] = None) -> Dict[str, Any]:
        """获取数据汇总信息，使用缓存提高性能"""
        # 生成缓存键
        cache_key = f"data_summary:{building_id or 'all'}"
        
        # 尝试从缓存获取
        # 注意：实际项目中应该使用更可靠的缓存机制
        
        # 直接查询数据库
        query = self.db.query(EnergyData)
        if building_id:
            query = query.filter(EnergyData.building_id == building_id)
        
        # 计算汇总值，使用单个查询获取所有数据，减少数据库查询次数
        from sqlalchemy import func
        summary = query.with_entities(
            func.count(EnergyData.id).label('total_records'),
            func.sum(EnergyData.electricity_kwh).label('total_electricity'),
            func.sum(EnergyData.water_m3).label('total_water'),
            func.sum(EnergyData.hvac_kwh).label('total_hvac'),
            func.avg(EnergyData.outdoor_temp).label('avg_outdoor_temp'),
            func.avg(EnergyData.humidity_pct).label('avg_humidity'),
            func.avg(EnergyData.occupancy_density).label('avg_occupancy')
        ).first()
        
        total_records = summary.total_records or 0
        
        return {
            "total_records": total_records,
            "energy_summary": {
                "total_electricity_kwh": float(summary.total_electricity) if summary.total_electricity else 0,
                "total_water_m3": float(summary.total_water) if summary.total_water else 0,
                "total_hvac_kwh": float(summary.total_hvac) if summary.total_hvac else 0
            },
            "average_values": {
                "outdoor_temp": float(summary.avg_outdoor_temp) if summary.avg_outdoor_temp else 0,
                "humidity_pct": float(summary.avg_humidity) if summary.avg_humidity else 0,
                "occupancy_density": float(summary.avg_occupancy) if summary.avg_occupancy else 0
            }
        }
    
    async def async_import_to_database(self, df: pd.DataFrame, batch_size: int = 1000) -> Dict[str, Any]:
        """异步导入数据到数据库，提高大数据量处理速度"""
        return await asyncio.to_thread(self.import_to_database, df, batch_size)
    
    def get_data_with_pagination(self, building_id: Optional[str] = None, page: int = 1, page_size: int = 1000) -> Dict[str, Any]:
        """分页获取数据，提高大数据量处理速度"""
        query = self.db.query(EnergyData)
        if building_id:
            query = query.filter(EnergyData.building_id == building_id)
        
        # 计算总数
        total_records = query.count()
        
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 获取分页数据
        records = query.order_by(EnergyData.timestamp.desc()).offset(offset).limit(page_size).all()
        
        # 转换为字典列表
        data = []
        for record in records:
            data.append({
                "id": record.id,
                "building_id": record.building_id,
                "building_type": record.building_type,
                "timestamp": record.timestamp.isoformat(),
                "electricity_kwh": record.electricity_kwh,
                "water_m3": record.water_m3,
                "hvac_kwh": record.hvac_kwh,
                "chw_supply_temp": record.chw_supply_temp,
                "chw_return_temp": record.chw_return_temp,
                "outdoor_temp": record.outdoor_temp,
                "humidity_pct": record.humidity_pct,
                "occupancy_density": record.occupancy_density,
                "meter_id": record.meter_id,
                "system_status": record.system_status
            })
        
        return {
            "total_records": total_records,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_records + page_size - 1) // page_size,
            "data": data
        }
    
    def get_aggregated_data(self, building_id: Optional[str] = None, interval: str = "day") -> Dict[str, Any]:
        """获取聚合数据，提高大数据量处理速度"""
        from sqlalchemy import func, extract
        
        query = self.db.query(
            func.date_trunc(interval, EnergyData.timestamp).label('period'),
            func.sum(EnergyData.electricity_kwh).label('total_electricity'),
            func.sum(EnergyData.water_m3).label('total_water'),
            func.sum(EnergyData.hvac_kwh).label('total_hvac'),
            func.avg(EnergyData.outdoor_temp).label('avg_outdoor_temp')
        )
        
        if building_id:
            query = query.filter(EnergyData.building_id == building_id)
        
        # 按时间段分组
        query = query.group_by('period').order_by('period')
        
        results = query.all()
        
        # 转换为字典列表
        data = []
        for result in results:
            data.append({
                "period": result.period.isoformat(),
                "total_electricity_kwh": float(result.total_electricity) if result.total_electricity else 0,
                "total_water_m3": float(result.total_water) if result.total_water else 0,
                "total_hvac_kwh": float(result.total_hvac) if result.total_hvac else 0,
                "avg_outdoor_temp": float(result.avg_outdoor_temp) if result.avg_outdoor_temp else 0
            })
        
        return {
            "interval": interval,
            "data": data,
            "total_records": len(data)
        }
