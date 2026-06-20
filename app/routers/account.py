"""POST /api/v1/account/analyze · 账号综合分析 HTTP API（对内用·无 SSO/计费）。

调 account_chain.run_from_video_url → 抖音视频链接 → 多维采集 → 综合报告。
返回裁剪版（去掉过大的中间数据 works）：{ok, report_md, account, six_layer}。
"""
from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Body

from app.services import account_chain

router = APIRouter(prefix="/api/v1/account", tags=["account"])


@router.post("/analyze")
def analyze(payload: dict[str, Any] = Body(...)) -> dict:
    """账号综合分析：抖音视频链接 → report_md + account + six_layer。

    请求体:
        video_url       str           必填，抖音视频链接
        competitor_urls list[str]     可选，竞品视频链接列表
        with_audiovisual bool         可选，是否跑视听六层（默认 True）

    返回:
        code=0   data={ok, report_md, account, six_layer}
        code!=0  data=None, msg=错误描述
    """
    video_url = payload.get("video_url") or ""
    if not video_url:
        return {"code": 4001, "data": None, "msg": "未提供 video_url"}

    competitor_urls: list[str] | None = payload.get("competitor_urls") or None
    with_audiovisual: bool = bool(payload.get("with_audiovisual", True))

    tikhub_key = os.getenv("TIKHUB_API_KEY") or os.getenv("PROBE_TIKHUB_KEY")

    try:
        result = account_chain.run_from_video_url(
            video_url,
            tikhub_key,
            with_audiovisual=with_audiovisual,
            competitor_urls=competitor_urls,
        )
    except Exception as e:
        return {"code": 5001, "data": None, "msg": f"账号分析异常:{type(e).__name__}: {e}"}

    if not result.get("ok"):
        return {"code": 5002, "data": None, "msg": result.get("error", "分析失败")}

    # 裁剪：不暴露过大的 works/video/audit 中间数据
    return {
        "code": 0,
        "data": {
            "ok": True,
            "report_md": result.get("report_md"),
            "account": result.get("account"),
            "six_layer": result.get("six_layer"),
        },
        "msg": "ok",
    }
