"""POST /api/v1/selfmedia/* · 自媒体采集面(方案B 独立验证面)。

断层1 接线:把 video_collector(combo-deep-probe 合规 wrapper)接进 probe HTTP 面。
断层2 解法:量化采集结果过 audit.lineage 数据血缘验证(非文本八闸),输出担保等级。
红线:只走 video_collector(TikHub 授权源 + 投喂),不自爬;与现有 invoke/pipeline 解耦、零改动。

⚠ 上线前须过 R30 新服务门(SSO 强校验 / 计费 / 限流 / R13 UX);本文件为草案接线,
  SSO 取匿名→免费档,计费未接(采集面默认免费,深探计费仍走 invoke)。
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body

from app.audit import lineage
from app.core import sso
from app.services import video_collector

router = APIRouter(prefix="/api/v1/selfmedia", tags=["selfmedia"])


def _req(payload: dict[str, Any]) -> dict[str, Any]:
    inner = payload.get("request")
    return inner if isinstance(inner, dict) else payload


@router.post("/video")
def video(payload: dict[str, Any] = Body(...)) -> dict:
    """单条短视频:采集 7 维 → 数据血缘验证 → 带担保等级返回。"""
    req = _req(payload)
    url = req.get("url") or ""
    if not url:
        return {"code": 4001, "data": None, "msg": "未提供视频 URL"}
    principal = sso.verify(req.get("user_token"), req.get("billing_context"))
    try:
        collected = video_collector.collect_video(url)
    except Exception as e:  # 采集失败不崩,返回错误码(R15 兜底)
        return {"code": 5001, "data": None, "msg": f"采集失败:{type(e).__name__}"}
    collected["lineage"] = lineage.verify(collected)
    return {"code": 0, "data": collected, "msg": "ok",
            "tier": getattr(principal, "tier", "free")}


@router.post("/account")
def account(payload: dict[str, Any] = Body(...)) -> dict:
    """账户:画像+作品矩阵+诊断 → 数据血缘验证 → 带担保等级返回。"""
    req = _req(payload)
    sec_user_id = req.get("sec_user_id") or ""
    if not sec_user_id:
        return {"code": 4001, "data": None, "msg": "未提供 sec_user_id"}
    principal = sso.verify(req.get("user_token"), req.get("billing_context"))
    try:
        count = int(req.get("count", 20))
        report = video_collector.collect_account(sec_user_id, count=count)
    except Exception as e:
        return {"code": 5001, "data": None, "msg": f"账户分析失败:{type(e).__name__}"}
    report["lineage"] = lineage.verify(report)
    return {"code": 0, "data": report, "msg": "ok",
            "tier": getattr(principal, "tier", "free")}
