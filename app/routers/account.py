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

# ── 深化数据接通辅助(纯函数·实测字段·2026-06-22) ──────────────────────────────

# 私域意图高频词停用集(口语虚词·表情占位)
_STOPWORDS = frozenset(
    "的 了 是 我 你 他 她 们 也 都 在 有 和 与 就 不 这 那 个 啊 吧 呢 吗 哦 嗯 "
    "什么 怎么 这个 那个 真的 一个 可以 没有 就是 已经 还是 但是 因为 所以".split()
)


def _extract_comments(comments_envelope) -> list[dict]:
    """从 comments 端点信封取评论列表。

    实测真值路径(2026-06-22): envelope["data"]["comments"][]。
    harness 把整个信封(含顶层 code/data)存入 results["comments"]·故须先下钻 .data。
    兼容 comment_list / aweme_comments 别名(防 spec 漂移)。
    """
    if not isinstance(comments_envelope, dict):
        return []
    data = comments_envelope.get("data")
    if not isinstance(data, dict):
        data = comments_envelope  # 已是 data 体(降级兜底)
    cmts = (data.get("comments") or data.get("comment_list")
            or data.get("aweme_comments") or [])
    return [c for c in cmts if isinstance(c, dict)]


def _build_comment_deep(cmts: list[dict]) -> dict:
    """评论列表 → comment_deep(水军/真实性/私域意图 3 子项)。字段全实测。"""
    import re
    from collections import Counter

    n = len(cmts)
    # 地域(ip_label·省份)集中度 + 多元度
    ips = Counter(c.get("ip_label") for c in cmts if c.get("ip_label"))
    ip_total = sum(ips.values())
    ip_concentration = round(max(ips.values()) / ip_total, 2) if ip_total else None
    ip_diversity = round(len(ips) / n, 2) if n else None

    # 评论层级分布(level·int)
    level_dist: dict[str, int] = {}
    for c in cmts:
        lv = c.get("level")
        if lv is not None:
            level_dist[str(lv)] = level_dist.get(str(lv), 0) + 1

    # 作者互动度(is_author_digged True 占比·作者是否回赞评论)
    author_reply_rate = (
        round(sum(1 for c in cmts if c.get("is_author_digged")) / n, 2) if n else None
    )
    # 评论平均点赞(digg_count·异常检测)
    diggs = [int(c.get("digg_count") or 0) for c in cmts]
    avg_digg = round(sum(diggs) / n, 1) if n else None
    # 被回复活跃度(reply_comment_total>0 占比)
    reply_active_rate = (
        round(sum(1 for c in cmts if (c.get("reply_comment_total") or 0) > 0) / n, 2)
        if n else None
    )
    # 高频词 top10(text·私域意图)。无分词依赖→对中文连续串做 2/3/4-gram 滑窗
    # 取词,过停用词;频次≥2 才入(单次出现无聚合意义)。
    words: Counter = Counter()
    for c in cmts:
        for seg in re.findall(r"[一-鿿]+", str(c.get("text") or "")):
            for size in (4, 3, 2):                 # 长词优先(更具体)
                for i in range(len(seg) - size + 1):
                    g = seg[i:i + size]
                    if g not in _STOPWORDS:
                        words[g] += 1
    top_keywords = [{"word": w, "count": ct}
                    for w, ct in words.most_common(30) if ct >= 2][:10]

    return {
        "sample_size": n,
        "ip_concentration": ip_concentration,        # 最高省份占比(0-1·水军)
        "ip_diversity": ip_diversity,                # unique 省份/总评论(0-1)
        "level_dist": level_dist,                    # {层级str: 计数}
        "author_reply_rate": author_reply_rate,      # 作者回赞占比(0-1·互动度)
        "avg_digg": avg_digg,                        # 评论平均点赞(异常检测)
        "reply_active_rate": reply_active_rate,      # 被回复占比(0-1)
        "top_keywords": top_keywords,                # [{word,count}]·私域意图
    }


def _rec_interact_rates(rec_videos) -> list[float]:
    """代表作互动率列表(竞品互动·1 子项)。

    masterpiece_videos[] 实测两形态:
      A 扁平: 顶层 interact_rate / like / play / comment / share。
      B 嵌套: stats{interact_rate, like_cnt, watch_cnt, ...}。
    优先用官方 interact_rate·缺失则 like/play 兜底估算。非法值跳过。
    """
    rates: list[float] = []
    for v in (rec_videos or []):
        if not isinstance(v, dict):
            continue
        st = v.get("stats") if isinstance(v.get("stats"), dict) else {}
        ir = v.get("interact_rate")
        if ir is None:
            ir = st.get("interact_rate")
        if ir is not None:
            try:
                rates.append(round(float(ir), 4))
                continue
            except (TypeError, ValueError):
                pass
        # 兜底: like/play
        like = v.get("like") if v.get("like") is not None else st.get("like_cnt")
        play = v.get("play") if v.get("play") is not None else st.get("watch_cnt")
        try:
            play_f = float(play or 0)
            if play_f > 0:
                rates.append(round(float(like or 0) / play_f, 4))
        except (TypeError, ValueError):
            pass
    return rates


def _track_competition(keyword: str, key: str) -> dict | None:
    """赛道竞争度(赛道蓝海·1 子项)。

    POST /api/v1/douyin/search/fetch_general_search_v1 {keyword,cursor:0}
      → data(list·结果) + has_more + cursor。
    返回 {keyword, result_count, has_more}。失败/无结果返回 None。
    harness 仅 GET·此端点 POST·故直接 httpx 调用。
    """
    import os as _os

    import httpx
    base = _os.environ.get("TIKHUB_API_BASE", "https://api.tikhub.io")
    ua = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
    try:
        r = httpx.post(
            f"{base}/api/v1/douyin/search/fetch_general_search_v1",
            json={"keyword": keyword, "cursor": 0},
            headers={"Authorization": f"Bearer {key}", "User-Agent": ua,
                     "accept": "application/json"},
            timeout=20.0,
        )
        if r.status_code != 200:
            return None
        body = r.json()
        if body.get("code") not in (0, 200, None):
            return None
        data = body.get("data")
        results = data if isinstance(data, list) else (
            data.get("data") if isinstance(data, dict) else None)
        has_more = (data.get("has_more") if isinstance(data, dict)
                    else body.get("has_more"))
        if not isinstance(results, list):
            return None
        return {
            "keyword": keyword,
            "result_count": len(results),       # 当页结果数(竞争密度代理)
            "has_more": bool(has_more),          # 是否海量竞争(红海信号)
        }
    except Exception:  # noqa: BLE001
        return None


def _build_account_for_diagnosis(sec_uid: str, key: str | None,
                                 aweme_id: str | None = None) -> tuple[dict, Any]:
    """采集账号+星图→ (account dict, xprof适配dict)。供诊断卡/复合指标用。

    有 aweme_id → run_full_harvest 全量采集(21端点·含评论/画像)·复合指标满血;
    无 → 降级 _harness_collect(profile/posts)。全程复用 P0 缓存。
    """
    from combo_deep_probe.account_probe import diagnose, parse_profile, parse_works
    from combo_deep_probe.cache import ResponseCache
    cache = ResponseCache(cache_dir="data/cache", ttl_sec=86400)

    results: dict = {}
    seeds: dict = {}
    if aweme_id:
        try:
            from combo_deep_probe.harness import run_full_harvest
            r = run_full_harvest({"aweme_id": aweme_id}, key, cache=cache, tier="full")
            results = r.get("results", {})
            seeds = r.get("seeds") or {}
            sec_uid = sec_uid or seeds.get("sec_uid")
        except Exception:  # noqa: BLE001
            pass

    if results.get("profile") and results.get("posts"):   # 全量路径
        prof = parse_profile(results["profile"])
        works = parse_works(results["posts"])
        diag = diagnose(works, follower_count=prof.get("follower_count"), profile=prof)
    else:                                                  # 降级路径
        rd = account_chain._harness_collect(sec_uid, key)
        prof, diag = rd.get("profile") or {}, rd.get("diagnosis") or {}

    _itv = (diag.get("update") or {}).get("avg_interval_hours")
    account = {
        "nickname": prof.get("nickname"), "follower": prof.get("follower_count"),
        "max_follower": prof.get("max_follower_count"),
        "with_commerce_entry": prof.get("with_commerce_entry"),
        "live_commerce": prof.get("live_commerce"),
        "mix_count": prof.get("mix_count"), "series_count": prof.get("series_count"),
        "aweme_count": prof.get("aweme_count"),
        "avg_like": (diag.get("like") or {}).get("avg"),
        "max_like": (diag.get("like") or {}).get("max"),
        "avg_collect": (diag.get("interaction_avg") or {}).get("collect"),
        "vertical_score": diag.get("vertical_score"),
        "burst_ratio": diag.get("burst_ratio"),
        "follower_drawdown": diag.get("follower_drawdown"),
        "engagement_structure": diag.get("engagement_structure"),
        "commerce_density": diag.get("commerce_density"),
        "update_gap_days": round(_itv / 24, 1) if _itv else None,
    }
    # ── 评论深化(水军/真实性/私域意图·3 子项·满血) ───────────────────────────
    # 真实信封路径: results["comments"]["data"]["comments"][] (实测 2026-06-22)。
    cmts = _extract_comments(results.get("comments"))
    _aid = seeds.get("aweme_id") or aweme_id
    if not cmts and _aid:
        # comments 偶发空(风控/采集失败)→ force_refresh 重取一次(跳缓存)。
        try:
            from combo_deep_probe.harness import run_full_harvest as _rfh
            r2 = _rfh({"aweme_id": _aid}, key, cache=cache, tier="full",
                      force_refresh=True)
            cmts = _extract_comments((r2.get("results") or {}).get("comments"))
        except Exception:  # noqa: BLE001
            pass
    if cmts:
        cd = _build_comment_deep(cmts)
        account["comment_deep"] = cd
        # composite c2 直接读 account["ip_concentration"](0-1·水军风险)·向后兼容。
        if cd.get("ip_concentration") is not None:
            account["ip_concentration"] = cd["ip_concentration"]

    xprof_adapter = None
    try:
        from app.services.xingtu_profile import fetch_xingtu_profile
        xp = fetch_xingtu_profile(sec_uid, key, cache=cache)   # 命中全量缓存
        if xp.is_xingtu:
            _lsi = xp.link_shopping_index

            def _p2c(dims):  # XingtuProfile top5 [(k,v)] → composite 期望 [{name,value}]
                return [{"type": d.get("type"), "origin_type": d.get("type"),
                         "display": d.get("display"),
                         "top5": [{"name": k, "value": v} for k, v in (d.get("top5") or [])]}
                        for d in (dims or [])]

            xprof_adapter = {
                "expect_vv": xp.expect_vv, "industry_tags": xp.industry_tags,
                "industry_tag": (xp.industry_tags or [None])[0], "price_info": xp.prices,
                "link_shopping_index": {"avg_value": _lsi.avg_value} if _lsi else None,
                "link_shopping_index_avg": _lsi.avg_value if _lsi else None,
                "fans_portrait": _p2c(xp.fans_portrait),          # 满血:消费力/地域
                "audience_portrait": _p2c(xp.audience_portrait),  # 满血:双画像破圈
                "rec_videos": xp.rec_videos,                      # 满血:竞品互动(raw·composite c4 直读 interact_rate)
                # 代表作互动率(已算·deepening 直读·robust 兼容 stats 嵌套/扁平两形态)。
                "rec_interact_rates": _rec_interact_rates(xp.rec_videos),
            }
            # ── 赛道竞争度(赛道蓝海·1 子项)·搜行业词看结果海量度 ────────────
            track_kw = (xp.industry_tags or [None])[0]
            if track_kw and key:
                tc = _track_competition(track_kw, key)
                if tc:
                    account["track_competition"] = tc
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
        aid = None
        if not sec_uid:
            aid = account_chain.resolve_douyin(video_url)
            if not aid:
                return {"code": 4002, "data": None, "msg": "无法解析视频链接"}
        # 全量采集(aweme_id 走 run_full_harvest 自举+21端点·复合指标满血)
        account, xprof = _build_account_for_diagnosis(sec_uid, key, aweme_id=aid)
        if not account.get("nickname"):
            return {"code": 4003, "data": None, "msg": "无法解析账号(视频可能已删/风控)"}
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
