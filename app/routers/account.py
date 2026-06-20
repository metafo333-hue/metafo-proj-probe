"""POST /api/v1/account/analyze · 账号综合分析 HTTP API（对内用·无 SSO/计费）。

完整分析(采集 + 下载 + Omni 视听理解)耗时长(可能 >3min)→ **默认异步**(防 HTTP 超时):
  POST /analyze → {task_id, status_url} → 轮询 GET /api/v1/task/{id} 取结果。
  payload sync=true → 同步返回(短任务/调试·长任务可能超时·自担)。
复用 core/tasks 长任务机制(02-api §1 铁律)·不重造基础设施。
"""
from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Body

from app.core import tasks
from app.services import account_chain

router = APIRouter(prefix="/api/v1/account", tags=["account"])


def _run_analysis(video_url: str, tikhub_key: str | None,
                  with_audiovisual: bool, competitor_urls: list[str] | None) -> dict:
    """任务体：跑完整分析 → {deliverable, meta, cost}（失败抛异常→task failed）。"""
    result = account_chain.run_from_video_url(
        video_url, tikhub_key,
        with_audiovisual=with_audiovisual, competitor_urls=competitor_urls)
    if not result.get("ok"):
        raise RuntimeError(result.get("error", "分析失败"))
    return {
        "deliverable": {
            "report_md": result.get("report_md"),
            "account": result.get("account"),
            "six_layer": result.get("six_layer"),
        },
        "meta": {"video_url": video_url},
        "cost": None,
    }


@router.post("/analyze")
def analyze(background: BackgroundTasks, payload: dict[str, Any] = Body(...)) -> dict:
    """账号综合分析（默认异步·复用 task 机制防超时）。

    请求体:
        video_url        str        必填·抖音视频链接
        competitor_urls  list[str]  可选·竞品链接(出 L4 竞品段)
        with_audiovisual bool       可选·跑视听六层(默认 True)
        sync             bool       可选·同步返回(默认 False·长任务可能超时)

    异步(默认): code=0 data={task_id, status_url}·轮询 GET status_url 取结果。
    同步(sync=true): code=0 data={ok, report_md, account, six_layer}。
    """
    video_url = payload.get("video_url") or ""
    if not video_url:
        return {"code": 4001, "data": None, "msg": "未提供 video_url"}

    competitor_urls: list[str] | None = payload.get("competitor_urls") or None
    with_audiovisual: bool = bool(payload.get("with_audiovisual", True))
    tikhub_key = os.getenv("TIKHUB_API_KEY") or os.getenv("PROBE_TIKHUB_KEY")

    # 同步路径(调试/短任务·长任务可能 HTTP 超时·调用方自担)
    if payload.get("sync"):
        try:
            r = _run_analysis(video_url, tikhub_key, with_audiovisual, competitor_urls)
        except Exception as e:  # noqa: BLE001
            return {"code": 5002, "data": None, "msg": f"{type(e).__name__}: {e}"}
        return {"code": 0, "data": {"ok": True, **r["deliverable"]}, "msg": "ok"}

    # 异步路径(默认·防超时)：提交 task → 后台跑 → 轮询
    tid = tasks.new_task()
    background.add_task(
        tasks.run_task, tid,
        lambda _t: _run_analysis(video_url, tikhub_key, with_audiovisual, competitor_urls),
    )
    return {
        "code": 0,
        "data": {"task_id": tid, "status_url": f"/api/v1/task/{tid}"},
        "msg": "已提交·轮询 status_url 取结果（完整分析约 1-3 分钟）",
    }
