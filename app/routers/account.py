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
from app.services import account_chain, diagnosis_cards

router = APIRouter(prefix="/api/v1/account", tags=["account"])


def _build_account_for_diagnosis(sec_uid: str, key: str | None) -> tuple[dict, Any]:
    """采集账号 + 星图(复用P0缓存)→ (account dict, xprof适配dict)。供诊断卡用。"""
    rd = account_chain._harness_collect(sec_uid, key)
    prof = rd.get("profile") or {}
    diag = rd.get("diagnosis") or {}
    account = {
        "nickname": prof.get("nickname"),
        "follower": prof.get("follower_count"),
        "max_follower": prof.get("max_follower_count"),
        "with_commerce_entry": prof.get("with_commerce_entry"),
        "avg_like": (diag.get("like") or {}).get("avg"),
        "max_like": (diag.get("like") or {}).get("max"),
        "vertical_score": diag.get("vertical_score"),
        "burst_ratio": diag.get("burst_ratio"),
        "follower_drawdown": diag.get("follower_drawdown"),
        "engagement_structure": diag.get("engagement_structure"),
        "commerce_density": diag.get("commerce_density"),
    }
    xprof_adapter = None
    try:
        from combo_deep_probe.cache import ResponseCache
        from app.services.xingtu_profile import fetch_xingtu_profile
        xp = fetch_xingtu_profile(sec_uid, key,
                                  cache=ResponseCache(cache_dir="data/cache", ttl_sec=86400))
        if xp.is_xingtu:
            _lsi = xp.link_shopping_index
            xprof_adapter = {
                "expect_vv": xp.expect_vv,
                "industry_tags": xp.industry_tags,
                "industry_tag": (xp.industry_tags or [None])[0],
                "price_info": xp.prices,
                "link_shopping_index": {"avg_value": _lsi.avg_value} if _lsi else None,
                "link_shopping_index_avg": _lsi.avg_value if _lsi else None,
            }
    except Exception:  # noqa: BLE001
        pass
    return account, xprof_adapter


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


@router.post("/diagnose")
def diagnose(payload: dict[str, Any] = Body(...)) -> dict:
    """诊断卡·结构化 JSON（同步快·一个 URL → 掉粉/报价/漏斗/赛道 4 卡）。

    给仪表盘/前端用·区别于 /analyze 的完整叙事报告。复用 P0 harness 缓存·秒级返回。
    请求体: video_url(抖音链接) 或 sec_uid 二选一。
    返回: data={nickname, churn, pricing, funnel, track, render_md}。
    """
    video_url = payload.get("video_url") or ""
    sec_uid = payload.get("sec_uid") or ""
    if not (video_url or sec_uid):
        return {"code": 4001, "data": None, "msg": "需 video_url 或 sec_uid"}
    key = os.getenv("TIKHUB_API_KEY") or os.getenv("PROBE_TIKHUB_KEY")
    try:
        if not sec_uid:
            from combo_deep_probe.cache import ResponseCache
            from combo_deep_probe.harness import run_harness
            aid = account_chain.resolve_douyin(video_url)
            if not aid:
                return {"code": 4002, "data": None, "msg": "无法解析视频链接"}
            hres = run_harness({"aweme_id": aid}, key,
                               cache=ResponseCache(cache_dir="data/cache", ttl_sec=86400))
            sec_uid = (hres.get("seeds") or {}).get("sec_uid")
            if not sec_uid:
                return {"code": 4003, "data": None, "msg": "无法解析账号(视频可能已删/风控)"}
        account, xprof = _build_account_for_diagnosis(sec_uid, key)
        return {"code": 0, "data": {
            "nickname": account.get("nickname"),
            "churn": diagnosis_cards.diagnose_churn(account),
            "pricing": diagnosis_cards.diagnose_pricing(account, xprof),
            "funnel": diagnosis_cards.diagnose_funnel(account),
            "track": diagnosis_cards.diagnose_track(account, xprof),
            "render_md": diagnosis_cards.render_diagnosis_section(account, xprof),
        }, "msg": "ok"}
    except Exception as e:  # noqa: BLE001
        return {"code": 5002, "data": None, "msg": f"{type(e).__name__}: {e}"}
