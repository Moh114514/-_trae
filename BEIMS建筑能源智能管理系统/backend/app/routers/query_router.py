from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
import logging
from time import perf_counter
from collections import defaultdict

from ..models.database import get_db, EnergyData
from ..services.statistics import StatisticsAnalyzer
from ..services.visualization import VisualizationService
from ..config.settings import settings

router = APIRouter(prefix="/query", tags=["查询统计"])
logger = logging.getLogger(__name__)


class QueryRequest(BaseModel):
    building_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    meter_id: Optional[str] = None
    system_status: Optional[str] = None


class StatisticsRequest(BaseModel):
    building_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    period: str = "day"
    threshold: float = 3.0
    top_n: int = 10
    metric: str = "electricity_kwh"
    building_area: float = 1000.0
    building_ids: Optional[List[str]] = None


class AgentReportRequest(BaseModel):
    building_id: Optional[str] = None
    building_ids: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    top_n: int = 10
    carbon_factor: float = 0.785  # kgCO2/kWh


class QueryRequest(BaseModel):
    building_id: Optional[str] = None
    building_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    meter_id: Optional[str] = None
    system_status: Optional[str] = None
    min_electricity: Optional[float] = None
    max_electricity: Optional[float] = None
    min_water: Optional[float] = None
    max_water: Optional[float] = None
    min_hvac: Optional[float] = None
    max_hvac: Optional[float] = None
    min_temp: Optional[float] = None
    max_temp: Optional[float] = None
    min_humidity: Optional[float] = None
    max_humidity: Optional[float] = None
    occupancy_density: Optional[float] = None
    page: int = 1
    page_size: int = 100


def _serialize_for_log(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_serialize_for_log(v) for v in value]
    if isinstance(value, dict):
        return {k: _serialize_for_log(v) for k, v in value.items()}
    return value


def _request_payload(request: StatisticsRequest) -> Dict[str, Any]:
    if hasattr(request, "model_dump"):
        payload = request.model_dump()
    else:
        payload = request.dict()
    return _serialize_for_log(payload)


def _result_summary(result: Any) -> Dict[str, Any]:
    if not isinstance(result, dict):
        return {"result_type": type(result).__name__}
    summary: Dict[str, Any] = {}
    for key, value in result.items():
        if isinstance(value, list):
            summary[key] = f"list(len={len(value)})"
        elif isinstance(value, dict):
            summary[key] = f"dict(keys={len(value)})"
        else:
            summary[key] = value
    return _serialize_for_log(summary)


def _to_number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _label_from_timestamp(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m")
    text = str(value or "")
    if "T" in text:
        return text[:7]
    if len(text) >= 7:
        return text[:7]
    return text


ANOMALY_METRIC_LABELS = {
    "electricity_kwh": "电耗",
    "water_m3": "水耗",
    "hvac_kwh": "空调能耗",
    "outdoor_temp": "室外温度",
    "humidity_pct": "湿度",
    "system_status": "系统状态",
    "hvac_vs_temperature": "空调-温度关系",
    "chw_temp_diff": "冷冻水温差",
    "unknown": "其他",
}

ANOMALY_SEVERITY_LABELS = {
    "high": "高",
    "medium": "中",
    "low": "低",
    "unknown": "未知",
}


def _normalize_metric_key(value: Any) -> str:
    key = str(value or "unknown").strip().lower().strip("_")
    return key or "unknown"


def _metric_label(value: Any) -> str:
    key = _normalize_metric_key(value)
    return ANOMALY_METRIC_LABELS.get(key, key)


def _severity_label(value: Any) -> str:
    key = str(value or "unknown").strip().lower()
    return ANOMALY_SEVERITY_LABELS.get(key, key or "未知")


def _run_statistics(endpoint: str, request: StatisticsRequest, runner):
    payload = _request_payload(request)
    t0 = perf_counter()
    if settings.STATS_DEBUG:
        logger.info("[STATDBG][%s] start payload=%s", endpoint, payload)

    try:
        result = runner()
        elapsed_ms = (perf_counter() - t0) * 1000
        if settings.STATS_DEBUG:
            logger.info(
                "[STATDBG][%s] success elapsed_ms=%.2f result=%s",
                endpoint,
                elapsed_ms,
                _result_summary(result)
            )
        return result
    except Exception as exc:
        elapsed_ms = (perf_counter() - t0) * 1000
        logger.exception(
            "[STATDBG][%s] failed elapsed_ms=%.2f payload=%s error=%s",
            endpoint,
            elapsed_ms,
            payload,
            str(exc)
        )
        raise HTTPException(status_code=500, detail=f"{endpoint} 执行失败: {exc}")


def _build_agent_report(
    request: AgentReportRequest,
    analyzer: StatisticsAnalyzer,
    db: Session
) -> Dict[str, Any]:
    selected_buildings = request.building_ids or []
    if request.building_id and request.building_id not in selected_buildings:
        selected_buildings = [request.building_id] + selected_buildings

    if not selected_buildings:
        all_buildings = db.query(EnergyData.building_id).distinct().all()
        selected_buildings = [r[0] for r in all_buildings if r and r[0]]

    if request.top_n > 0 and len(selected_buildings) > request.top_n:
        selected_buildings = selected_buildings[:request.top_n]

    monthly_raw = analyzer.time_period_aggregation(
        building_id=request.building_id,
        start_time=request.start_time,
        end_time=request.end_time,
        period="month"
    )
    if monthly_raw.get("error"):
        raise HTTPException(status_code=404, detail=f"月度统计失败: {monthly_raw['error']}")

    comparison_raw = analyzer.comparative_analysis(
        building_ids=selected_buildings,
        start_time=request.start_time,
        end_time=request.end_time
    )

    anomalies_raw = analyzer.detect_anomalies(
        building_id=request.building_id,
        start_time=request.start_time,
        end_time=request.end_time,
        threshold=3.0
    )

    cop_raw = analyzer.calculate_cop(
        building_id=request.building_id,
        start_time=request.start_time,
        end_time=request.end_time,
        max_points=None
    )

    savings_raw = analyzer.energy_savings_potential(
        building_id=request.building_id,
        start_time=request.start_time,
        end_time=request.end_time
    )

    monthly_series = []
    for row in monthly_raw.get("data", []):
        monthly_series.append({
            "month": _label_from_timestamp(row.get("timestamp")),
            "electricity_kwh": _to_number(row.get("electricity_kwh")),
            "water_m3": _to_number(row.get("water_m3")),
            "hvac_kwh": _to_number(row.get("hvac_kwh")),
        })

    comparison_map = comparison_raw.get("comparison_data", {}) or {}
    comparison_series = []
    for building, item in comparison_map.items():
        comparison_series.append({
            "building_id": building,
            "total_electricity_kwh": _to_number(item.get("total_electricity")),
            "total_water_m3": _to_number(item.get("total_water")),
            "total_hvac_kwh": _to_number(item.get("total_hvac")),
            "avg_electricity_kwh": _to_number(item.get("avg_electricity")),
        })
    comparison_series.sort(key=lambda x: x["total_electricity_kwh"], reverse=True)

    anomaly_metric_counter: Dict[str, int] = defaultdict(int)
    anomaly_severity_counter: Dict[str, int] = defaultdict(int)
    for item in anomalies_raw.get("anomalies", []):
        anomaly_metric_counter[_metric_label(item.get("metric", "unknown"))] += 1
        anomaly_severity_counter[_severity_label(item.get("severity", "unknown"))] += 1

    anomaly_by_metric = [
        {"name": k, "value": v}
        for k, v in sorted(anomaly_metric_counter.items(), key=lambda kv: kv[1], reverse=True)
    ]
    anomaly_by_severity = [
        {"name": k, "value": v}
        for k, v in sorted(anomaly_severity_counter.items(), key=lambda kv: kv[1], reverse=True)
    ]

    cop_month_bucket: Dict[str, List[float]] = defaultdict(list)
    for item in cop_raw.get("cop_data", []):
        ts = _label_from_timestamp(item.get("timestamp"))
        cop_val = _to_number(item.get("cop"), default=-1)
        if cop_val >= 0:
            cop_month_bucket[ts].append(cop_val)

    cop_trend = []
    for month, values in sorted(cop_month_bucket.items()):
        if not values:
            continue
        cop_trend.append({
            "month": month,
            "avg_cop": round(sum(values) / len(values), 3)
        })

    summary = monthly_raw.get("summary", {}) or {}
    total_electricity = _to_number(summary.get("total_electricity_kwh"))
    total_water = _to_number(summary.get("total_water_m3"))
    total_hvac = _to_number(summary.get("total_hvac_kwh"))
    avg_cop = _to_number(cop_raw.get("average_cop"))
    total_anomalies = int(anomalies_raw.get("total_anomalies", 0) or 0)

    carbon_kg = round(total_electricity * request.carbon_factor, 2)
    carbon_ton = round(carbon_kg / 1000, 3)

    savings_total = _to_number((savings_raw.get("potential_savings") or {}).get("total"))
    savings_pct = _to_number(savings_raw.get("savings_percentage"))

    conclusions: List[str] = []
    if monthly_series:
        first = monthly_series[0]["electricity_kwh"]
        last = monthly_series[-1]["electricity_kwh"]
        if first > 0:
            trend_pct = (last - first) / first * 100
            conclusions.append(f"月度电耗从 {monthly_series[0]['month']} 到 {monthly_series[-1]['month']} 变化 {trend_pct:.1f}% 。")

    if comparison_series:
        top_building = comparison_series[0]
        conclusions.append(
            f"分建筑对比中，{top_building['building_id']} 电耗最高，为 {top_building['total_electricity_kwh']:.2f} kWh。"
        )

    conclusions.append(f"异常能耗检测共识别 {total_anomalies} 个异常点。")
    conclusions.append(f"COP 平均值为 {avg_cop:.3f}。")
    conclusions.append(f"估算碳排放 {carbon_ton:.3f} 吨CO2（排放因子 {request.carbon_factor} kgCO2/kWh）。")

    recommendations = [
        "优先治理异常频发指标对应设备，建立按周复盘机制。",
        "将高耗能建筑纳入重点管控，实施分时段运行策略。",
    ]
    if avg_cop < 3.0:
        recommendations.append("COP 偏低，建议优先进行冷冻水系统与主机工况优化。")
    if savings_pct > 0:
        recommendations.append(f"基于当前工况，节能潜力约 {savings_pct:.1f}%，可先落地非工作时段节能策略。")

    return {
        "report_meta": {
            "generated_at": datetime.now().isoformat(),
            "report_type": "agent_statistics_report",
            "focus_building": request.building_id,
            "comparison_buildings": selected_buildings,
            "time_range": {
                "start_time": request.start_time.isoformat() if request.start_time else None,
                "end_time": request.end_time.isoformat() if request.end_time else None,
            }
        },
        "kpis": {
            "total_electricity_kwh": round(total_electricity, 2),
            "total_water_m3": round(total_water, 2),
            "total_hvac_kwh": round(total_hvac, 2),
            "average_cop": round(avg_cop, 3),
            "anomaly_count": total_anomalies,
            "carbon_emission_ton": carbon_ton,
            "potential_saving_kwh": round(savings_total, 2),
            "potential_saving_pct": round(savings_pct, 2)
        },
        "charts": {
            "monthly_energy": monthly_series,
            "building_comparison": comparison_series,
            "anomaly_distribution": {
                "by_metric": anomaly_by_metric,
                "by_severity": anomaly_by_severity
            },
            "cop_trend": cop_trend
        },
        "analysis": {
            "conclusions": conclusions,
            "recommendations": recommendations,
            "brief": "报表涵盖基础统计、分析诊断与决策支持，支持直接用于运营例会汇报。"
        },
        "decision_support": {
            "carbon_estimation": {
                "factor_kgco2_per_kwh": request.carbon_factor,
                "estimated_kgco2": carbon_kg,
                "estimated_tonco2": carbon_ton
            },
            "energy_saving": {
                "baseline_energy_kwh": _to_number(savings_raw.get("baseline_energy_kwh")),
                "potential_savings_kwh": round(savings_total, 2),
                "potential_savings_pct": round(savings_pct, 2)
            }
        }
    }


@router.post("/data")
async def query_energy_data(
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    analyzer = StatisticsAnalyzer(db)
    result = analyzer.query_data(
        building_id=request.building_id,
        building_type=request.building_type,
        start_time=request.start_time,
        end_time=request.end_time,
        meter_id=request.meter_id,
        system_status=request.system_status,
        min_electricity=request.min_electricity,
        max_electricity=request.max_electricity,
        min_water=request.min_water,
        max_water=request.max_water,
        min_hvac=request.min_hvac,
        max_hvac=request.max_hvac,
        min_temp=request.min_temp,
        max_temp=request.max_temp,
        min_humidity=request.min_humidity,
        max_humidity=request.max_humidity,
        occupancy_density=request.occupancy_density,
        page=request.page,
        page_size=request.page_size
    )
    
    return {
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "data": [{
            "building_id": d.building_id,
            "building_type": d.building_type,
            "timestamp": d.timestamp.isoformat(),
            "electricity_kwh": d.electricity_kwh,
            "water_m3": d.water_m3,
            "hvac_kwh": d.hvac_kwh,
            "chw_supply_temp": d.chw_supply_temp,
            "chw_return_temp": d.chw_return_temp,
            "outdoor_temp": d.outdoor_temp,
            "humidity_pct": d.humidity_pct,
            "occupancy_density": d.occupancy_density,
            "meter_id": d.meter_id,
            "system_status": d.system_status
        } for d in result["data"]]
    }


@router.post("/statistics/time-aggregation")
async def time_period_aggregation(
    request: StatisticsRequest,
    db: Session = Depends(get_db)
):
    analyzer = StatisticsAnalyzer(db)
    return _run_statistics(
        "statistics/time-aggregation",
        request,
        lambda: analyzer.time_period_aggregation(
            building_id=request.building_id,
            start_time=request.start_time,
            end_time=request.end_time,
            period=request.period
        )
    )


@router.post("/statistics/cop")
async def calculate_cop(
    request: StatisticsRequest,
    db: Session = Depends(get_db)
):
    analyzer = StatisticsAnalyzer(db)
    return _run_statistics(
        "statistics/cop",
        request,
        lambda: analyzer.calculate_cop(
            building_id=request.building_id,
            start_time=request.start_time,
            end_time=request.end_time
        )
    )


@router.post("/statistics/anomalies")
async def detect_anomalies(
    request: StatisticsRequest,
    db: Session = Depends(get_db)
):
    analyzer = StatisticsAnalyzer(db)
    return _run_statistics(
        "statistics/anomalies",
        request,
        lambda: analyzer.detect_anomalies(
            building_id=request.building_id,
            start_time=request.start_time,
            end_time=request.end_time,
            threshold=request.threshold
        )
    )


@router.post("/statistics/ranking")
async def energy_consumption_ranking(
    request: StatisticsRequest,
    db: Session = Depends(get_db)
):
    analyzer = StatisticsAnalyzer(db)
    return _run_statistics(
        "statistics/ranking",
        request,
        lambda: analyzer.energy_consumption_ranking(
            start_time=request.start_time,
            end_time=request.end_time,
            top_n=request.top_n
        )
    )


@router.post("/statistics/trend")
async def energy_trend_analysis(
    request: StatisticsRequest,
    db: Session = Depends(get_db)
):
    analyzer = StatisticsAnalyzer(db)
    return _run_statistics(
        "statistics/trend",
        request,
        lambda: analyzer.energy_trend_analysis(
            building_id=request.building_id,
            start_time=request.start_time,
            end_time=request.end_time,
            metric=request.metric
        )
    )


@router.post("/statistics/peak-demand")
async def peak_demand_analysis(
    request: StatisticsRequest,
    db: Session = Depends(get_db)
):
    analyzer = StatisticsAnalyzer(db)
    return _run_statistics(
        "statistics/peak-demand",
        request,
        lambda: analyzer.peak_demand_analysis(
            building_id=request.building_id,
            start_time=request.start_time,
            end_time=request.end_time
        )
    )


@router.post("/statistics/intensity")
async def energy_intensity_analysis(
    request: StatisticsRequest,
    db: Session = Depends(get_db)
):
    analyzer = StatisticsAnalyzer(db)
    return _run_statistics(
        "statistics/intensity",
        request,
        lambda: analyzer.energy_intensity_analysis(
            building_id=request.building_id,
            start_time=request.start_time,
            end_time=request.end_time,
            building_area=request.building_area
        )
    )


@router.post("/statistics/comparison")
async def comparative_analysis(
    request: StatisticsRequest,
    db: Session = Depends(get_db)
):
    if not request.building_ids:
        raise HTTPException(status_code=400, detail="需要提供building_ids参数")
    
    analyzer = StatisticsAnalyzer(db)
    return _run_statistics(
        "statistics/comparison",
        request,
        lambda: analyzer.comparative_analysis(
            building_ids=request.building_ids,
            start_time=request.start_time,
            end_time=request.end_time
        )
    )


@router.post("/statistics/weather-correlation")
async def weather_correlation_analysis(
    request: StatisticsRequest,
    db: Session = Depends(get_db)
):
    analyzer = StatisticsAnalyzer(db)
    return _run_statistics(
        "statistics/weather-correlation",
        request,
        lambda: analyzer.weather_correlation_analysis(
            building_id=request.building_id,
            start_time=request.start_time,
            end_time=request.end_time
        )
    )


@router.post("/statistics/occupancy-impact")
async def occupancy_impact_analysis(
    request: StatisticsRequest,
    db: Session = Depends(get_db)
):
    analyzer = StatisticsAnalyzer(db)
    return _run_statistics(
        "statistics/occupancy-impact",
        request,
        lambda: analyzer.occupancy_impact_analysis(
            building_id=request.building_id,
            start_time=request.start_time,
            end_time=request.end_time
        )
    )


@router.post("/statistics/hourly-pattern")
async def hourly_pattern_analysis(
    request: StatisticsRequest,
    db: Session = Depends(get_db)
):
    analyzer = StatisticsAnalyzer(db)
    return _run_statistics(
        "statistics/hourly-pattern",
        request,
        lambda: analyzer.hourly_pattern_analysis(
            building_id=request.building_id,
            start_time=request.start_time,
            end_time=request.end_time
        )
    )


@router.post("/statistics/weekly-pattern")
async def weekly_pattern_analysis(
    request: StatisticsRequest,
    db: Session = Depends(get_db)
):
    analyzer = StatisticsAnalyzer(db)
    return _run_statistics(
        "statistics/weekly-pattern",
        request,
        lambda: analyzer.weekly_pattern_analysis(
            building_id=request.building_id,
            start_time=request.start_time,
            end_time=request.end_time
        )
    )


@router.post("/statistics/seasonal")
async def seasonal_analysis(
    request: StatisticsRequest,
    db: Session = Depends(get_db)
):
    analyzer = StatisticsAnalyzer(db)
    return _run_statistics(
        "statistics/seasonal",
        request,
        lambda: analyzer.seasonal_analysis(
            building_id=request.building_id,
            start_time=request.start_time,
            end_time=request.end_time
        )
    )


@router.post("/statistics/agent-report")
async def generate_agent_report(
    request: AgentReportRequest,
    db: Session = Depends(get_db)
):
    analyzer = StatisticsAnalyzer(db)

    payload = {
        "building_id": request.building_id,
        "building_ids": request.building_ids,
        "start_time": request.start_time.isoformat() if request.start_time else None,
        "end_time": request.end_time.isoformat() if request.end_time else None,
        "top_n": request.top_n,
        "carbon_factor": request.carbon_factor,
    }
    t0 = perf_counter()
    if settings.STATS_DEBUG:
        logger.info("[STATDBG][statistics/agent-report] start payload=%s", payload)

    try:
        result = _build_agent_report(request=request, analyzer=analyzer, db=db)
        elapsed_ms = (perf_counter() - t0) * 1000
        if settings.STATS_DEBUG:
            logger.info(
                "[STATDBG][statistics/agent-report] success elapsed_ms=%.2f result=%s",
                elapsed_ms,
                _result_summary(result)
            )
        return result
    except HTTPException:
        raise
    except Exception as exc:
        elapsed_ms = (perf_counter() - t0) * 1000
        logger.exception(
            "[STATDBG][statistics/agent-report] failed elapsed_ms=%.2f payload=%s error=%s",
            elapsed_ms,
            payload,
            str(exc)
        )
        raise HTTPException(status_code=500, detail=f"statistics/agent-report 执行失败: {exc}")


@router.post("/statistics/energy-efficiency")
async def energy_efficiency_analysis(
    request: StatisticsRequest,
    db: Session = Depends(get_db)
):
    analyzer = StatisticsAnalyzer(db)
    result = analyzer.energy_efficiency_analysis(
        building_id=request.building_id,
        start_time=request.start_time,
        end_time=request.end_time
    )
    return result


@router.post("/statistics/equipment-performance")
async def equipment_performance_analysis(
    request: StatisticsRequest,
    db: Session = Depends(get_db)
):
    analyzer = StatisticsAnalyzer(db)
    result = analyzer.equipment_performance_analysis(
        building_id=request.building_id,
        start_time=request.start_time,
        end_time=request.end_time
    )
    return result


@router.post("/statistics/energy-prediction")
async def energy_prediction(
    request: StatisticsRequest,
    prediction_days: int = Query(7, description="预测天数"),
    db: Session = Depends(get_db)
):
    analyzer = StatisticsAnalyzer(db)
    result = analyzer.energy_prediction(
        building_id=request.building_id,
        start_time=request.start_time,
        end_time=request.end_time,
        prediction_days=prediction_days
    )
    return result


@router.post("/statistics/energy-savings")
async def energy_savings_potential(
    request: StatisticsRequest,
    db: Session = Depends(get_db)
):
    analyzer = StatisticsAnalyzer(db)
    result = analyzer.energy_savings_potential(
        building_id=request.building_id,
        start_time=request.start_time,
        end_time=request.end_time
    )
    return result


@router.post("/statistics/cost-analysis")
async def cost_analysis(
    request: StatisticsRequest,
    electricity_price: float = Query(0.6, description="电价"),
    water_price: float = Query(5.0, description="水价"),
    db: Session = Depends(get_db)
):
    analyzer = StatisticsAnalyzer(db)
    result = analyzer.cost_analysis(
        building_id=request.building_id,
        start_time=request.start_time,
        end_time=request.end_time,
        electricity_price=electricity_price,
        water_price=water_price
    )
    return result


@router.post("/visualization/line-chart")
async def create_line_chart(request: Dict[str, Any]):
    viz_service = VisualizationService()
    result = viz_service.create_line_chart(
        data=request.get('data', []),
        x_field=request.get('x_field', 'x'),
        y_field=request.get('y_field', 'y'),
        title=request.get('title', '折线图'),
        x_label=request.get('x_label', ''),
        y_label=request.get('y_label', ''),
        color_palette=request.get('color_palette', 'default'),
        theme=request.get('theme', 'light'),
        interactive=request.get('interactive', True),
        show_legend=request.get('show_legend', True),
        annotations=request.get('annotations'),
        range_x=request.get('range_x'),
        range_y=request.get('range_y')
    )
    return result


@router.post("/visualization/multi-line-chart")
async def create_multi_line_chart(request: Dict[str, Any]):
    viz_service = VisualizationService()
    result = viz_service.create_multi_line_chart(
        data=request.get('data', []),
        x_field=request.get('x_field', 'x'),
        y_fields=request.get('y_fields', []),
        title=request.get('title', '多线折线图'),
        x_label=request.get('x_label', ''),
        y_label=request.get('y_label', ''),
        color_palette=request.get('color_palette', 'default'),
        theme=request.get('theme', 'light'),
        interactive=request.get('interactive', True),
        show_legend=request.get('show_legend', True),
        annotations=request.get('annotations'),
        range_x=request.get('range_x'),
        range_y=request.get('range_y')
    )
    return result


@router.post("/visualization/bar-chart")
async def create_bar_chart(request: Dict[str, Any]):
    viz_service = VisualizationService()
    result = viz_service.create_bar_chart(
        data=request.get('data', []),
        x_field=request.get('x_field', 'x'),
        y_field=request.get('y_field', 'y'),
        title=request.get('title', '柱状图'),
        orientation=request.get('orientation', 'v')
    )
    return result


@router.post("/visualization/pie-chart")
async def create_pie_chart(request: Dict[str, Any]):
    viz_service = VisualizationService()
    result = viz_service.create_pie_chart(
        data=request.get('data', []),
        names_field=request.get('names_field', 'names'),
        values_field=request.get('values_field', 'values'),
        title=request.get('title', '饼图')
    )
    return result


@router.post("/visualization/heatmap")
async def create_heatmap(request: Dict[str, Any]):
    viz_service = VisualizationService()
    result = viz_service.create_heatmap(
        data=request.get('data', []),
        x_labels=request.get('x_labels', []),
        y_labels=request.get('y_labels', []),
        title=request.get('title', '热力图')
    )
    return result


@router.post("/visualization/scatter-plot")
async def create_scatter_plot(request: Dict[str, Any]):
    viz_service = VisualizationService()
    result = viz_service.create_scatter_plot(
        data=request.get('data', []),
        x_field=request.get('x_field', 'x'),
        y_field=request.get('y_field', 'y'),
        title=request.get('title', '散点图'),
        color_field=request.get('color_field')
    )
    return result


@router.post("/visualization/box-plot")
async def create_box_plot(request: Dict[str, Any]):
    viz_service = VisualizationService()
    result = viz_service.create_box_plot(
        data=request.get('data', []),
        x_field=request.get('x_field', 'x'),
        y_field=request.get('y_field', 'y'),
        title=request.get('title', '箱线图')
    )
    return result


@router.post("/visualization/gauge-chart")
async def create_gauge_chart(request: Dict[str, Any]):
    viz_service = VisualizationService()
    result = viz_service.create_gauge_chart(
        value=request.get('value', 0),
        title=request.get('title', '仪表盘'),
        min_val=request.get('min_val', 0),
        max_val=request.get('max_val', 100),
        thresholds=request.get('thresholds')
    )
    return result


@router.post("/visualization/radar-chart")
async def create_radar_chart(request: Dict[str, Any]):
    viz_service = VisualizationService()
    result = viz_service.create_radar_chart(
        data=request.get('data', []),
        categories_field=request.get('categories_field', 'categories'),
        values_field=request.get('values_field', 'values'),
        title=request.get('title', '雷达图')
    )
    return result


@router.post("/visualization/area-chart")
async def create_area_chart(request: Dict[str, Any]):
    viz_service = VisualizationService()
    result = viz_service.create_area_chart(
        data=request.get('data', []),
        x_field=request.get('x_field', 'x'),
        y_fields=request.get('y_fields', []),
        title=request.get('title', '面积图')
    )
    return result


@router.post("/visualization/histogram")
async def create_histogram(request: Dict[str, Any]):
    viz_service = VisualizationService()
    result = viz_service.create_histogram(
        data=request.get('data', []),
        title=request.get('title', '直方图'),
        x_label=request.get('x_label', '数值'),
        bins=request.get('bins', 30)
    )
    return result


@router.post("/visualization/treemap")
async def create_treemap(request: Dict[str, Any]):
    viz_service = VisualizationService()
    result = viz_service.create_treemap(
        data=request.get('data', []),
        labels_field=request.get('labels_field', 'labels'),
        values_field=request.get('values_field', 'values'),
        parents_field=request.get('parents_field', ''),
        title=request.get('title', '树状图')
    )
    return result


@router.post("/visualization/animated-line-chart")
async def create_animated_line_chart(request: Dict[str, Any]):
    viz_service = VisualizationService()
    result = viz_service.create_animated_line_chart(
        data=request.get('data', []),
        x_field=request.get('x_field', 'x'),
        y_field=request.get('y_field', 'y'),
        animation_field=request.get('animation_field', 'animation'),
        title=request.get('title', '动画折线图'),
        x_label=request.get('x_label', ''),
        y_label=request.get('y_label', ''),
        color_palette=request.get('color_palette', 'default'),
        theme=request.get('theme', 'light')
    )
    return result


@router.post("/visualization/3d-scatter-plot")
async def create_3d_scatter_plot(request: Dict[str, Any]):
    viz_service = VisualizationService()
    result = viz_service.create_3d_scatter_plot(
        data=request.get('data', []),
        x_field=request.get('x_field', 'x'),
        y_field=request.get('y_field', 'y'),
        z_field=request.get('z_field', 'z'),
        title=request.get('title', '3D散点图'),
        color_field=request.get('color_field'),
        theme=request.get('theme', 'light')
    )
    return result


@router.post("/visualization/polar-chart")
async def create_polar_chart(request: Dict[str, Any]):
    viz_service = VisualizationService()
    result = viz_service.create_polar_chart(
        data=request.get('data', []),
        r_field=request.get('r_field', 'r'),
        theta_field=request.get('theta_field', 'theta'),
        title=request.get('title', '极坐标图'),
        color_field=request.get('color_field'),
        theme=request.get('theme', 'light')
    )
    return result


@router.post("/visualization/export")
async def export_chart(request: Dict[str, Any]):
    viz_service = VisualizationService()
    result = viz_service.export_chart(
        chart_json=request.get('chart_json'),
        format=request.get('format', 'png'),
        width=request.get('width', 1000),
        height=request.get('height', 600)
    )
    return {"image": result}


@router.get("/visualization/options")
async def get_chart_options():
    viz_service = VisualizationService()
    result = viz_service.get_chart_options()
    return result


@router.post("/export/report")
async def export_report(
    request: StatisticsRequest,
    db: Session = Depends(get_db)
):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import inch
    import io
    
    analyzer = StatisticsAnalyzer(db)
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.darkblue,
        spaceAfter=30
    )
    
    story = []
    
    story.append(Paragraph("建筑能源统计报告", title_style))
    story.append(Spacer(1, 0.2 * inch))
    
    story.append(Paragraph(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    
    if request.building_id:
        story.append(Paragraph(f"建筑ID: {request.building_id}", styles['Normal']))
    
    if request.start_time and request.end_time:
        story.append(Paragraph(
            f"统计时段: {request.start_time.strftime('%Y-%m-%d')} 至 {request.end_time.strftime('%Y-%m-%d')}",
            styles['Normal']
        ))
    
    story.append(Spacer(1, 0.3 * inch))
    
    aggregation = analyzer.time_period_aggregation(
        building_id=request.building_id,
        start_time=request.start_time,
        end_time=request.end_time,
        period="day"
    )
    
    if 'summary' in aggregation:
        story.append(Paragraph("能耗汇总", styles['Heading2']))
        summary_data = [
            ['指标', '数值'],
            ['总电力消耗(kWh)', f"{aggregation['summary']['total_electricity_kwh']:.2f}"],
            ['总用水量(m³)', f"{aggregation['summary']['total_water_m3']:.2f}"],
            ['总HVAC能耗(kWh)', f"{aggregation['summary']['total_hvac_kwh']:.2f}"],
            ['平均室外温度(°C)', f"{aggregation['summary']['avg_outdoor_temp']:.2f}"],
            ['平均湿度(%)', f"{aggregation['summary']['avg_humidity']:.2f}"]
        ]
        
        table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
    
    story.append(Spacer(1, 0.3 * inch))
    
    anomalies = analyzer.detect_anomalies(
        building_id=request.building_id,
        start_time=request.start_time,
        end_time=request.end_time
    )
    
    story.append(Paragraph("异常检测结果", styles['Heading2']))
    story.append(Paragraph(f"检测到异常数量: {anomalies.get('total_anomalies', 0)}", styles['Normal']))
    
    doc.build(story)
    
    buffer.seek(0)
    
    from fastapi.responses import StreamingResponse
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=energy_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        }
    )


class NaturalLanguageQueryRequest(BaseModel):
    query: str
    page: int = 1
    page_size: int = 100


@router.post("/natural-language")
async def natural_language_query(
    request: NaturalLanguageQueryRequest,
    db: Session = Depends(get_db)
):
    from ..services.rag_service import KnowledgeBaseService, RAGService
    
    # 初始化知识库和RAG服务
    knowledge_base = KnowledgeBaseService()
    rag_service = RAGService(knowledge_base)
    
    # 分析自然语言查询
    original_query = request.query
    query = original_query.lower()
    
    # 提取查询参数
    params = {}
    
    # 提取建筑ID
    import re
    building_match = re.search(r'建筑([a-zA-Z0-9_]+)', original_query)
    if building_match:
        building_id = building_match.group(1)
        
        # 尝试匹配数据库中实际存在的建筑ID
        from ..models.database import Building, EnergyData
        
        # 先从 EnergyData 表中获取所有建筑ID（因为 buildings 表可能为空）
        energy_data_buildings = db.query(EnergyData.building_id).distinct().all()
        energy_building_ids = [b[0] for b in energy_data_buildings]
        
        # 再从 buildings 表中获取建筑ID
        buildings = db.query(Building).all()
        building_ids = [b.building_id for b in buildings]
        
        # 合并两个列表，去重
        all_building_ids = list(set(energy_building_ids + building_ids))
        
        # 打印调试信息
        print(f"原始建筑ID: {building_id}")
        print(f"数据库中的建筑ID: {all_building_ids}")
        
        # 不区分大小写的匹配
        matched_building_id = None
        for b_id in all_building_ids:
            if b_id.lower() == building_id.lower():
                matched_building_id = b_id
                break
        
        # 如果没有精确匹配，尝试模糊匹配
        if not matched_building_id:
            for b_id in all_building_ids:
                if building_id.lower() in b_id.lower():
                    matched_building_id = b_id
                    break
        
        # 使用匹配到的建筑ID或原始输入
        if matched_building_id:
            params['building_id'] = matched_building_id
            print(f"匹配到的建筑ID: {matched_building_id}")
        else:
            params['building_id'] = building_id
            print(f"未匹配到建筑ID，使用原始输入: {building_id}")
    
    # 提取时间范围
    # 支持多种时间格式
    time_formats = ['%Y-%m-%d', '%Y/%m/%d', '%Y年%m月%d日']
    
    # 尝试匹配时间范围
    time_range_patterns = [
        r'(从|自)(\d{4}[-/年]\d{2}[-/月]\d{2}[日]?)\s*(到|至)(\d{4}[-/年]\d{2}[-/月]\d{2}[日]?)',
        r'(\d{4}[-/年]\d{2}[-/月]\d{2}[日]?)\s*到\s*(\d{4}[-/年]\d{2}[-/月]\d{2}[日]?)'
    ]
    
    for pattern in time_range_patterns:
        time_range_match = re.search(pattern, query)
        if time_range_match:
            # 提取并标准化日期格式
            start_date_str = time_range_match.group(2)
            end_date_str = time_range_match.group(4) if len(time_range_match.groups()) >= 4 else time_range_match.group(2)
            
            # 尝试不同的日期格式
            for fmt in time_formats:
                try:
                    params['start_time'] = datetime.strptime(start_date_str, fmt)
                    params['end_time'] = datetime.strptime(end_date_str, fmt)
                    break
                except ValueError:
                    continue
            break
    
    # 提取单一日期
    if 'start_time' not in params:
        single_date_patterns = [
            r'(在|于)(\d{4}[-/年]\d{2}[-/月]\d{2}[日]?)',
            r'(\d{4}[-/年]\d{2}[-/月]\d{2}[日]?)'
        ]
        
        for pattern in single_date_patterns:
            single_date_match = re.search(pattern, query)
            if single_date_match:
                date_str = single_date_match.group(2) if len(single_date_match.groups()) >= 2 else single_date_match.group(1)
                
                for fmt in time_formats:
                    try:
                        date = datetime.strptime(date_str, fmt)
                        params['start_time'] = date
                        params['end_time'] = date
                        break
                    except ValueError:
                        continue
                break
    
    # 提取监测参数
    # 定义参数映射
    param_mappings = [
        {
            'keywords': ['电力', '用电', 'electricity', '电量', '电能'],
            'min_param': 'min_electricity',
            'max_param': 'max_electricity'
        },
        {
            'keywords': ['水', 'water', '用水量', '水量'],
            'min_param': 'min_water',
            'max_param': 'max_water'
        },
        {
            'keywords': ['空调', 'hvac', '冷气', '供暖'],
            'min_param': 'min_hvac',
            'max_param': 'max_hvac'
        },
        {
            'keywords': ['温度', 'temp', '气温', '室温'],
            'min_param': 'min_temp',
            'max_param': 'max_temp'
        },
        {
            'keywords': ['湿度', 'humidity', '潮湿度'],
            'min_param': 'min_humidity',
            'max_param': 'max_humidity'
        },
        {
            'keywords': ['人员', 'occupancy', '密度', '人数'],
            'min_param': 'occupancy_density',
            'max_param': None
        }
    ]
    
    # 定义比较运算符映射
    comparison_operators = {
        '大于': 'min',
        '超过': 'min',
        '高于': 'min',
        '大于等于': 'min',
        '不小于': 'min',
        '小于': 'max',
        '低于': 'max',
        '不超过': 'max',
        '小于等于': 'max',
        '不大于': 'max'
    }
    
    # 提取监测参数范围
    for mapping in param_mappings:
        for keyword in mapping['keywords']:
            if keyword in query:
                # 构建正则表达式
                pattern = r'(' + keyword + r')\s*(' + '|'.join(comparison_operators.keys()) + r')\s*(\d+\.?\d*)'
                match = re.search(pattern, query)
                if match:
                    operator = match.group(2)
                    value = float(match.group(3))
                    
                    if comparison_operators[operator] == 'min' and mapping['min_param']:
                        params[mapping['min_param']] = value
                    elif comparison_operators[operator] == 'max' and mapping['max_param']:
                        params[mapping['max_param']] = value
                break
    
    # 执行查询
    analyzer = StatisticsAnalyzer(db)
    result = analyzer.query_data(
        **params,
        page=request.page,
        page_size=request.page_size
    )
    
    # 构建响应
    response_data = {
        "original_query": request.query,
        "extracted_params": params,
        "total": result["total"],
        "data": [{
            "building_id": d.building_id,
            "building_type": d.building_type,
            "timestamp": d.timestamp.isoformat(),
            "electricity_kwh": d.electricity_kwh,
            "water_m3": d.water_m3,
            "hvac_kwh": d.hvac_kwh,
            "outdoor_temp": d.outdoor_temp,
            "humidity_pct": d.humidity_pct,
            "occupancy_density": d.occupancy_density,
            "meter_id": d.meter_id,
            "system_status": d.system_status
        } for d in result["data"]]
    }
    
    # 确保返回的建筑ID与数据库中的一致
    if 'building_id' in params:
        # 尝试获取数据库中实际的建筑ID
        from ..models.database import Building
        building = db.query(Building).filter(Building.building_id.ilike(params['building_id'])).first()
        if building:
            response_data['extracted_params']['building_id'] = building.building_id
    
    return response_data
