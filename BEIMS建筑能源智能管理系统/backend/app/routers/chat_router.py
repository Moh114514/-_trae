"""
智能聊天路由

阶段3目标：主后端统一承载聊天入口。
- 优先代理到独立智能助手服务（默认 http://localhost:8082）
- 代理失败时自动回退到本地 CloudEdgeRouter
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from calendar import monthrange
import importlib
import logging
import os
import re
from pathlib import Path

import httpx

from ..config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["智能聊天"])

_local_router = None

_KNOWN_BUILDINGS = [
    "Baikal", "Aral", "Caspian", "Huron", "Erie", "Ladoga", "Superior",
    "Titicaca", "Victoria", "Winnipeg", "Vostok", "Michigan", "Ontario", "Malawi"
]
_REPORT_HINT_KEYWORDS = (
    "报表", "可视化", "图表", "趋势图", "统计图", "看板", "统计分析", "分析报告", "报告",
    "report", "dashboard", "visualization", "chart"
)
_EXPORT_HINT_KEYWORDS = (
    "导出", "下载", "保存", "html", "网页", "web", "export", "download"
)


def _build_time_range(year: int, start_month: int, end_month: int) -> Dict[str, str]:
    start = datetime(year, start_month, 1, 0, 0, 0)
    end_day = monthrange(year, end_month)[1]
    end = datetime(year, end_month, end_day, 23, 59, 59)
    return {
        "start_time": start.strftime("%Y-%m-%d %H:%M:%S"),
        "end_time": end.strftime("%Y-%m-%d %H:%M:%S"),
    }


def _extract_buildings(message: str) -> List[str]:
    hits: List[str] = []
    lowered = message.lower()

    for name in _KNOWN_BUILDINGS:
        pattern = rf"\\b{re.escape(name.lower())}\\b"
        if re.search(pattern, lowered) or name.lower() in lowered:
            hits.append(name)

    # 保持顺序并去重
    unique_hits: List[str] = []
    for item in hits:
        if item not in unique_hits:
            unique_hits.append(item)
    return unique_hits


def _extract_time_range(message: str) -> Dict[str, str]:
    text = message.strip()
    lower = text.lower()

    year_match = re.search(r"(20\\d{2})年", text)
    year = int(year_match.group(1)) if year_match else 2021

    if "全年" in text or "整年" in text:
        return _build_time_range(year, 1, 12)

    quarter_tokens = {
        "q1": (1, 3),
        "q2": (4, 6),
        "q3": (7, 9),
        "q4": (10, 12),
        "第一季度": (1, 3),
        "第二季度": (4, 6),
        "第三季度": (7, 9),
        "第四季度": (10, 12),
    }
    for token, (start_month, end_month) in quarter_tokens.items():
        if token in lower or token in text:
            return _build_time_range(year, start_month, end_month)

    month_range_match = re.search(
        r"(?:([12]\\d{3})年)?\\s*(1[0-2]|0?[1-9])月\\s*(?:到|至|~|－|-)\\s*(1[0-2]|0?[1-9])月",
        text,
    )
    if month_range_match:
        matched_year = int(month_range_match.group(1)) if month_range_match.group(1) else year
        start_month = int(month_range_match.group(2))
        end_month = int(month_range_match.group(3))
        if start_month > end_month:
            start_month, end_month = end_month, start_month
        return _build_time_range(matched_year, start_month, end_month)

    month_match = re.search(r"(?:([12]\\d{3})年)?\\s*(1[0-2]|0?[1-9])月", text)
    if month_match:
        matched_year = int(month_match.group(1)) if month_match.group(1) else year
        month = int(month_match.group(2))
        return _build_time_range(matched_year, month, month)

    return {
        "start_time": "2021-01-01 00:00:00",
        "end_time": "2021-12-31 23:59:59",
    }


def _detect_report_ui_action(message: str) -> Optional[Dict[str, Any]]:
    text = (message or "").strip()
    if not text:
        return None

    has_report_hint = any(token in text for token in _REPORT_HINT_KEYWORDS)
    has_export_hint = any(token in text.lower() for token in _EXPORT_HINT_KEYWORDS)

    if not has_report_hint and not has_export_hint:
        return None

    buildings = _extract_buildings(text)
    time_range = _extract_time_range(text)

    top_n = 8
    top_n_match = re.search(r"(?:前|top\\s*)(\\d{1,2})", text.lower())
    if top_n_match:
        parsed_top_n = int(top_n_match.group(1))
        if 1 <= parsed_top_n <= 20:
            top_n = parsed_top_n

    carbon_factor = 0.785
    carbon_match = re.search(r"碳(?:排放)?因子\\s*([0-9]+(?:\\.[0-9]+)?)", text)
    if carbon_match:
        carbon_factor = float(carbon_match.group(1))

    payload = {
        "building_id": buildings[0] if buildings else "",
        "building_ids": buildings,
        "start_time": time_range["start_time"],
        "end_time": time_range["end_time"],
        "top_n": top_n,
        "carbon_factor": carbon_factor,
    }
    if has_export_hint:
        payload["auto_export"] = "html"

    return {
        "type": "open_report",
        "payload": payload,
    }


def _build_report_action_reply(ui_action: Dict[str, Any]) -> str:
    payload = ui_action.get("payload", {}) if isinstance(ui_action, dict) else {}
    building_id = payload.get("building_id") or "全部建筑"
    start_time = payload.get("start_time", "2021-01-01 00:00:00")
    end_time = payload.get("end_time", "2021-12-31 23:59:59")
    auto_export = payload.get("auto_export") == "html"

    action_text = "我将打开报表工作台，并自动生成可视化报表"
    if auto_export:
        action_text += "，随后自动导出 HTML 报表"

    return (
        f"已识别报表指令。{action_text}。\\n"
        f"统计对象：{building_id}\\n"
        f"时间范围：{start_time} ~ {end_time}"
    )


def _workspace_root() -> Path:
    # .../BEIMS建筑能源智能管理系统/backend/app/routers/chat_router.py -> workspace root
    return Path(__file__).resolve().parents[4]


def _assistant_url(path: str) -> str:
    return f"{settings.ASSISTANT_BASE_URL.rstrip('/')}{path}"


def _proxy_payload(request: "ChatRequest") -> Dict[str, Any]:
    return {
        "message": request.message,
        "building_id": request.building_id,
        "clear_history": request.clear_history,
        "history": request.history,
        "session_id": request.session_id,
    }


def _init_local_router():
    """按需初始化本地 CloudEdgeRouter，避免启动时硬依赖失败。"""
    global _local_router
    if _local_router is not None:
        return _local_router

    root = str(_workspace_root())
    if root not in os.sys.path:
        os.sys.path.insert(0, root)

    module = importlib.import_module("cloud_edge_router")
    _local_router = module.CloudEdgeRouter(
        config={
            "ollama_url": "http://localhost:11434",
            "local_model": "qwen2.5:7b",
            "cloud_api_key": os.environ.get("CLOUD_API_KEY", ""),
            "cloud_api_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            "cloud_model": "qwen-plus",
        }
    )
    logger.info("Local CloudEdgeRouter initialized as fallback")
    return _local_router


async def _proxy_chat(request: "ChatRequest") -> Optional[Dict[str, Any]]:
    """返回 dict 表示代理成功，返回 None 表示应回退本地。"""
    if not settings.ASSISTANT_PROXY_ENABLED:
        return None

    try:
        async with httpx.AsyncClient(timeout=settings.ASSISTANT_PROXY_TIMEOUT) as client:
            resp = await client.post(_assistant_url("/chat"), json=_proxy_payload(request))
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict) and "response" in data:
                return data
            logger.warning("Assistant proxy returned unexpected payload")
            return None
    except Exception as exc:
        logger.warning("Assistant proxy failed, fallback to local router: %s", exc)
        return None


async def _proxy_clear() -> Optional[Dict[str, Any]]:
    if not settings.ASSISTANT_PROXY_ENABLED:
        return None

    try:
        async with httpx.AsyncClient(timeout=settings.ASSISTANT_PROXY_TIMEOUT) as client:
            resp = await client.post(_assistant_url("/chat/clear"))
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict):
                return data
            return None
    except Exception as exc:
        logger.warning("Assistant clear proxy failed, fallback to local router: %s", exc)
        return None


async def _proxy_status() -> Optional[Dict[str, Any]]:
    if not settings.ASSISTANT_PROXY_ENABLED:
        return None

    async with httpx.AsyncClient(timeout=settings.ASSISTANT_PROXY_TIMEOUT) as client:
        # 优先尝试子项目约定，再兼容独立助手约定
        for status_path in ("/chat/status", "/router/status"):
            try:
                resp = await client.get(_assistant_url(status_path))
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, dict):
                    return data
            except Exception:
                continue

    logger.warning("Assistant status proxy failed on /chat/status and /router/status")
    return None


def _assert_fallback_allowed(detail: str):
    if not settings.ASSISTANT_FALLBACK_LOCAL:
        raise HTTPException(status_code=503, detail=detail)


class ChatRequest(BaseModel):
    message: str
    building_id: Optional[str] = None
    clear_history: Optional[bool] = False
    history: Optional[List[Dict[str, str]]] = None
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    context: Optional[Dict] = None
    history: Optional[List[Dict[str, str]]] = None


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    智能对话统一入口。
    流程：代理独立助手 -> 本地 CloudEdgeRouter 回退。
    """
    try:
        ui_action = _detect_report_ui_action(request.message)
        if ui_action is not None:
            return {
                "response": _build_report_action_reply(ui_action),
                "context": {
                    "source": "chat-router-ui-action",
                    "action": "report-automation",
                    "ui_action": ui_action,
                },
                "history": request.history,
            }

        proxied = await _proxy_chat(request)
        if proxied is not None:
            proxy_context = proxied.get("context") if isinstance(proxied, dict) else None
            merged_context = {
                "source": "assistant-proxy",
                "assistant_base_url": settings.ASSISTANT_BASE_URL,
                **(proxy_context if isinstance(proxy_context, dict) else {}),
            }
            return {
                "response": proxied.get("response", "处理失败"),
                "context": merged_context,
                "history": proxied.get("history"),
            }

        _assert_fallback_allowed("智能助手代理不可用，且已禁用本地回退")

        # fallback: 本地路由
        local = _init_local_router()
        if request.clear_history:
            local.clear_context()
        elif request.history:
            local.restore_history(request.history)

        question = request.message
        if request.building_id:
            question = f"[建筑: {request.building_id}] {question}"

        result = local.route(question)
        reply = result.get("response", "处理失败")

        local.update_context(
            user_message=request.message,
            assistant_reply=reply,
            layer=result.get("layer"),
            action=result.get("action"),
        )

        return {
            "response": reply,
            "context": {
                "source": "local-fallback",
                "layer": result.get("layer"),
                "action": result.get("action"),
            },
            "history": None,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"聊天服务异常: {str(e)}")


@router.post("/clear")
async def clear_history():
    """清空对话历史"""
    proxied = await _proxy_clear()
    if proxied is not None:
        return {
            "success": True,
            "message": proxied.get("message", "对话历史已清空"),
            "source": "assistant-proxy",
        }

    _assert_fallback_allowed("智能助手清理接口不可用，且已禁用本地回退")

    local = _init_local_router()
    local.clear_context()
    return {"success": True, "message": "对话历史已清空", "source": "local-fallback"}


@router.get("/status")
async def get_chat_status():
    """获取聊天服务状态"""
    proxied = await _proxy_status()
    if proxied is not None:
        return {
            "status": proxied.get("status", "running"),
            "mode": "assistant-proxy",
            "assistant_base_url": settings.ASSISTANT_BASE_URL,
            "proxy_enabled": settings.ASSISTANT_PROXY_ENABLED,
            "fallback_local_enabled": settings.ASSISTANT_FALLBACK_LOCAL,
            "upstream": proxied,
        }

    _assert_fallback_allowed("智能助手状态接口不可用，且已禁用本地回退")

    return {
        "status": "running",
        "mode": "local-fallback",
        "proxy_enabled": settings.ASSISTANT_PROXY_ENABLED,
        "assistant_base_url": settings.ASSISTANT_BASE_URL,
        "router_version": "CloudEdgeRouter v2.3",
        "features": ["硬规则过滤", "语义路由", "本地推理", "云端增强", "上下文记忆"],
    }
