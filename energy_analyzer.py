"""
建筑能源分析引擎 - Building Energy Analyzer

功能：
1. COP 制冷效率计算
2. 同比环比分析
3. 异常识别（Z-Score）
4. 报表生成（Excel + 图表）
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor


class EnergyAnalyzer:
    """建筑能耗分析器"""

    def __init__(self, db_config: dict):
        """
        初始化分析器

        Args:
            db_config: 数据库配置
                {
                    "host": "localhost",
                    "port": 5432,
                    "database": "building_energy",
                    "user": "postgres",
                    "password": "xxx"
                }
        """
        self.db_config = db_config
        self.conn = None

    def connect(self):
        """连接数据库"""
        self.conn = psycopg2.connect(**self.db_config)
        return self

    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ==================== 数据查询 ====================

    def get_data(self,
                  building_id: Optional[str] = None,
                  start_time: Optional[datetime] = None,
                  end_time: Optional[datetime] = None) -> pd.DataFrame:
        """
        查询能耗数据

        Args:
            building_id: 建筑ID，None表示全部
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            DataFrame 包含能耗数据
        """
        query = "SELECT * FROM energy_reports WHERE 1=1"
        params = []

        if building_id:
            query += " AND building_id = %s"
            params.append(building_id)

        if start_time:
            query += " AND timestamp >= %s"
            params.append(start_time)

        if end_time:
            query += " AND timestamp <= %s"
            params.append(end_time)

        query += " ORDER BY timestamp"

        df = pd.read_sql(query, self.conn, params=params)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        return df

    def get_daily_summary(self,
                          building_id: Optional[str] = None,
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None) -> pd.DataFrame:
        """
        获取每日能耗汇总

        Returns:
            DataFrame 包含每日汇总数据
        """
        df = self.get_data(building_id, start_time, end_time)

        if df.empty:
            return pd.DataFrame()

        daily = df.groupby([df['timestamp'].dt.date, 'building_id']).agg({
            'electricity_kwh': 'sum',
            'water_m3': 'sum',
            'hvac_kwh': 'sum',
            'outdoor_temp': 'mean',
            'humidity_pct': 'mean',
            'occupancy_density': 'mean'
        }).reset_index()

        daily.rename(columns={'timestamp': 'date'}, inplace=True)

        return daily

    # ==================== COP 计算 ====================

    def calculate_cop(self,
                      cooling_capacity_kwh: float,
                      compressor_power_kwh: float) -> float:
        """
        计算 COP (制冷效率)

        COP = 制冷量 / 压缩机功耗

        Args:
            cooling_capacity_kwh: 制冷量 (kWh)
            compressor_power_kwh: 压缩机功耗 (kWh)

        Returns:
            COP 值
        """
        if compressor_power_kwh <= 0:
            return 0.0
        return round(cooling_capacity_kwh / compressor_power_kwh, 2)

    def estimate_cop_from_temp(self,
                               chw_supply: float,
                               chw_return: float,
                               flow_rate_m3h: float = 100) -> Tuple[float, Dict]:
        """
        根据温度估算 COP

        简化计算：
        - 制冷量 = 流量 × 比热容 × 温差
        - 假设压缩机功耗为制冷量的 20-25%

        Args:
            chw_supply: 冷冻水供水温度 (°C)
            chw_return: 冷冻水回水温度 (°C)
            flow_rate_m3h: 水流量 (m³/h)

        Returns:
            (COP值, 详细信息字典)
        """
        # 水的比热容: 4.18 kJ/(kg·°C)
        # 水的密度: 1000 kg/m³
        WATER_SPECIFIC_HEAT = 4.18  # kJ/(kg·°C)
        WATER_DENSITY = 1000  # kg/m³

        delta_t = chw_return - chw_supply

        # 制冷量 (kW) = 流量 × 密度 × 比热容 × 温差 / 3600
        # 转换单位: kJ → kWh (除以 3600)
        cooling_capacity_kw = (flow_rate_m3h * WATER_DENSITY *
                               WATER_SPECIFIC_HEAT * delta_t) / 3600

        # 估算压缩机功耗 (假设 COP ≈ 4-5 的典型工况)
        # 反推压缩机功耗
        estimated_cop = 4.5  # 初始假设
        compressor_power_kw = cooling_capacity_kw / estimated_cop

        # 根据温差修正 COP
        if delta_t < 3:
            estimated_cop *= 0.7  # 温差太小，效率下降
        elif delta_t > 10:
            estimated_cop *= 0.8  # 温差过大，可能有问题

        info = {
            "delta_t": round(delta_t, 2),
            "cooling_capacity_kw": round(cooling_capacity_kw, 2),
            "estimated_compressor_power_kw": round(compressor_power_kw, 2),
            "cop_rating": self.rate_cop(estimated_cop)
        }

        return round(estimated_cop, 2), info

    def rate_cop(self, cop: float) -> str:
        """
        COP 评级

        Args:
            cop: COP 值

        Returns:
            评级字符串
        """
        if cop >= 5.0:
            return "优秀"
        elif cop >= 4.0:
            return "良好"
        elif cop >= 3.0:
            return "一般"
        else:
            return "异常"

    def analyze_cop_trend(self,
                          building_id: str,
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None) -> pd.DataFrame:
        """
        分析 COP 趋势

        Returns:
            DataFrame 包含时间序列的 COP 分析结果
        """
        df = self.get_data(building_id, start_time, end_time)

        if df.empty:
            return pd.DataFrame()

        # 计算温差
        df['delta_t'] = df['chw_return_temp'] - df['chw_supply_temp']

        # 估算 COP (简化版，使用 hvac_kwh 作为功耗参考)
        results = []
        for _, row in df.iterrows():
            if row['hvac_kwh'] > 0 and row['delta_t'] > 0:
                # 简化估算
                cop = self.calculate_cop(
                    row['delta_t'] * 100,  # 假设制冷量与温差成正比
                    row['hvac_kwh'] / 24  # 小时级功耗
                )
            else:
                cop = 0

            results.append({
                'timestamp': row['timestamp'],
                'delta_t': row['delta_t'],
                'hvac_kwh': row['hvac_kwh'],
                'cop': cop,
                'cop_rating': self.rate_cop(cop)
            })

        return pd.DataFrame(results)

    # ==================== 同比环比分析 ====================

    def calculate_yoy(self,
                      building_id: str,
                      metric: str = 'electricity_kwh',
                      period: str = 'month') -> Dict:
        """
        计算同比 (Year-over-Year)

        Args:
            building_id: 建筑ID
            metric: 指标字段
            period: 周期 (month/quarter)

        Returns:
            同比分析结果
        """
        df = self.get_data(building_id)

        if df.empty:
            return {"error": "无数据"}

        # 按月汇总
        df['year'] = df['timestamp'].dt.year
        df['month'] = df['timestamp'].dt.month

        monthly = df.groupby(['year', 'month'])[metric].sum().reset_index()

        if len(monthly['year'].unique()) < 2:
            return {"error": "数据不足，需要至少两年数据"}

        # 获取最近两年的数据
        years = sorted(monthly['year'].unique())[-2:]
        this_year = years[-1]
        last_year = years[-2]

        this_year_data = monthly[monthly['year'] == this_year]
        last_year_data = monthly[monthly['year'] == last_year]

        # 计算同比
        results = []
        for month in this_year_data['month'].unique():
            this_val = this_year_data[this_year_data['month'] == month][metric].values[0]
            last_val = last_year_data[last_year_data['month'] == month][metric].values

            if len(last_val) > 0:
                last_val = last_val[0]
                yoy_rate = (this_val - last_val) / last_val * 100
            else:
                yoy_rate = None

            results.append({
                'month': month,
                'this_year': this_val,
                'last_year': last_val if len(last_val) > 0 else None,
                'yoy_rate': round(yoy_rate, 2) if yoy_rate else None
            })

        return {
            'building_id': building_id,
            'metric': metric,
            'this_year': this_year,
            'last_year': last_year,
            'data': results
        }

    def calculate_mom(self,
                      building_id: str,
                      metric: str = 'electricity_kwh') -> Dict:
        """
        计算环比 (Month-over-Month)

        Args:
            building_id: 建筑ID
            metric: 指标字段

        Returns:
            环比分析结果
        """
        df = self.get_data(building_id)

        if df.empty:
            return {"error": "无数据"}

        # 按月汇总
        df['year_month'] = df['timestamp'].dt.to_period('M')
        monthly = df.groupby('year_month')[metric].sum().reset_index()

        if len(monthly) < 2:
            return {"error": "数据不足，需要至少两个月数据"}

        # 计算环比
        monthly['mom_rate'] = monthly[metric].pct_change() * 100

        results = []
        for _, row in monthly.iterrows():
            results.append({
                'period': str(row['year_month']),
                'value': row[metric],
                'mom_rate': round(row['mom_rate'], 2) if not pd.isna(row['mom_rate']) else None
            })

        return {
            'building_id': building_id,
            'metric': metric,
            'data': results
        }

    # ==================== 异常识别 ====================

    def detect_anomalies_zscore(self,
                                df: pd.DataFrame,
                                columns: List[str],
                                threshold: float = 3.0) -> pd.DataFrame:
        """
        使用 Z-Score 检测异常值

        Args:
            df: 数据
            columns: 要检测的列
            threshold: Z-Score 阈值

        Returns:
            包含异常标记的 DataFrame
        """
        result_df = df.copy()

        for col in columns:
            if col not in df.columns:
                continue

            mean = df[col].mean()
            std = df[col].std()

            if std == 0:
                continue

            z_scores = np.abs((df[col] - mean) / std)
            result_df[f'{col}_zscore'] = z_scores
            result_df[f'{col}_anomaly'] = z_scores > threshold

        return result_df

    def analyze_anomalies(self,
                          building_id: str,
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None,
                          threshold: float = 3.0) -> Dict:
        """
        综合异常分析

        Args:
            building_id: 建筑ID
            start_time: 开始时间
            end_time: 结束时间
            threshold: Z-Score 阈值

        Returns:
            异常分析报告
        """
        df = self.get_data(building_id, start_time, end_time)

        if df.empty:
            return {"error": "无数据"}

        # 检测数值型字段的异常
        numeric_cols = ['electricity_kwh', 'water_m3', 'hvac_kwh',
                        'chw_supply_temp', 'chw_return_temp', 'outdoor_temp']

        df_with_anomaly = self.detect_anomalies_zscore(df, numeric_cols, threshold)

        # 汇总异常
        anomalies = []
        for col in numeric_cols:
            anomaly_col = f'{col}_anomaly'
            if anomaly_col in df_with_anomaly.columns:
                anomaly_count = df_with_anomaly[anomaly_col].sum()
                if anomaly_count > 0:
                    anomalies.append({
                        'field': col,
                        'count': int(anomaly_count),
                        'percentage': round(anomaly_count / len(df) * 100, 2)
                    })

        # 检测异常记录
        anomaly_records = df_with_anomaly[
            df_with_anomaly[[f'{c}_anomaly' for c in numeric_cols
                            if f'{c}_anomaly' in df_with_anomaly.columns]].any(axis=1)
        ]

        return {
            'building_id': building_id,
            'total_records': len(df),
            'anomaly_records': len(anomaly_records),
            'anomaly_rate': round(len(anomaly_records) / len(df) * 100, 2),
            'anomalies_by_field': anomalies,
            'top_anomaly_records': anomaly_records.head(10).to_dict('records')
        }

    # ==================== 综合报告 ====================

    def generate_report(self,
                        building_id: str,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None) -> Dict:
        """
        生成综合分析报告

        Returns:
            包含所有分析结果的字典
        """
        df = self.get_data(building_id, start_time, end_time)

        if df.empty:
            return {"error": "无数据"}

        report = {
            'report_time': datetime.now().isoformat(),
            'building_id': building_id,
            'data_range': {
                'start': str(df['timestamp'].min()),
                'end': str(df['timestamp'].max()),
                'records': len(df)
            },

            # 基础统计
            'statistics': {
                'electricity_total': round(df['electricity_kwh'].sum(), 2),
                'electricity_avg': round(df['electricity_kwh'].mean(), 2),
                'water_total': round(df['water_m3'].sum(), 2),
                'hvac_total': round(df['hvac_kwh'].sum(), 2),
                'hvac_ratio': round(df['hvac_kwh'].sum() / df['electricity_kwh'].sum() * 100, 2)
                           if df['electricity_kwh'].sum() > 0 else 0
            },

            # 温度分析
            'temperature': {
                'avg_outdoor_temp': round(df['outdoor_temp'].mean(), 2),
                'avg_delta_t': round((df['chw_return_temp'] - df['chw_supply_temp']).mean(), 2),
                'min_supply_temp': round(df['chw_supply_temp'].min(), 2),
                'max_return_temp': round(df['chw_return_temp'].max(), 2)
            },

            # 同比分析
            'yoy_analysis': self.calculate_yoy(building_id),

            # 环比分析
            'mom_analysis': self.calculate_mom(building_id),

            # 异常分析
            'anomaly_analysis': self.analyze_anomalies(building_id, start_time, end_time)
        }

        # COP 分析
        cop_trend = self.analyze_cop_trend(building_id, start_time, end_time)
        if not cop_trend.empty:
            report['cop_analysis'] = {
                'avg_cop': round(cop_trend['cop'].mean(), 2),
                'min_cop': round(cop_trend['cop'].min(), 2),
                'max_cop': round(cop_trend['cop'].max(), 2),
                'cop_distribution': cop_trend['cop_rating'].value_counts().to_dict()
            }

        return report


# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 数据库配置
    db_config = {
        "host": "localhost",
        "port": 5432,
        "database": "building_energy",
        "user": "postgres",
        "password": "your_password"
    }

    # 使用分析器
    with EnergyAnalyzer(db_config) as analyzer:
        # 获取数据
        df = analyzer.get_data("BLD001")
        print(f"数据量: {len(df)}")

        # 生成报告
        report = analyzer.generate_report("BLD001")
        print(report)