"""一条命令出综合报告 · 抖音链接 → 多维采集 → 担保 → 报告(account_chain)。

编排:resolve 短链 → 视频详情(指标+作者) → 账号+兄弟视频 → 多维 → 八闸担保 → account_report。
合规:只走 TikHub 授权源;无 LLM(报告确定性);key 由调用方传/环境变量。
"""
from __future__ import annotations

import os
import pathlib
import re
import sys
import urllib.request
from typing import Any

from app.audit.gates import run_audit
from app.services.account_audit_bridge import account_to_claims_sources
from app.services.account_report import build_report, _track, _is_business
from app.services.audiovisual import analyze_douyin_video, render_av_section
from app.services.competitor_compare import compare_accounts
from app.services.l0_environment import build_l0_environment, render_l0_section
from app.services.commercial import classify_track_value, render_commercial_section
from app.services.conversion import render_conversion_section
from app.services.commercial_data import (category_commission, category_gmv_tier,
                                          xingtu_price_estimate, render_commercial_data_section)

_MOBILE_UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
              "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1")


def _ensure_combo() -> None:
    p = pathlib.Path(__file__).resolve().parents[3] / "combo-deep-probe"
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))


def resolve_douyin(url: str) -> str | None:
    """抖音链接/短链 → aweme_id(跟跳转)。"""
    m = re.search(r"/video/(\d+)", url)
    if m:
        return m.group(1)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _MOBILE_UA})
        with urllib.request.urlopen(req, timeout=15) as r:
            final = r.geturl()
        m = re.search(r"/video/(\d+)", final)
        return m.group(1) if m else None
    except Exception:
        return None


def _detect_platform(url: str) -> str:
    """识别链接平台（probe 现状仅支持抖音·其余友好报错·实测驱动 2026-06-18）。"""
    u = (url or "").lower()
    if "douyin.com" in u or "iesdouyin" in u:
        return "douyin"
    if "weixin.qq.com/sph" in u or "channels.weixin" in u or "/sph/" in u:
        return "wechat_channels"
    if "kuaishou" in u or "kwai" in u:
        return "kuaishou"
    if "xiaohongshu" in u or "xhslink" in u:
        return "xiaohongshu"
    return "unknown"


_PLATFORM_CN = {
    "wechat_channels": "微信视频号", "kuaishou": "快手",
    "xiaohongshu": "小红书", "unknown": "未识别平台",
}


def fetch_douyin_hot_topics(tikhub_key: str | None, limit: int = 8) -> list[str] | None:
    """TikHub 抖音热榜(app/v3) → 当前平台热点词(供 L0 蹭热点参考·失败 None 不阻塞)。"""
    key = tikhub_key or os.getenv("TIKHUB_API_KEY") or os.getenv("PROBE_TIKHUB_KEY")
    if not key:
        return None
    try:
        _ensure_combo()
        from combo_deep_probe.adapters.tikhub_adapter import tikhub_get
        raw = tikhub_get("/api/v1/douyin/app/v3/fetch_hot_search_list", {}, key)
        tl = (((raw.get("data") or {}).get("data") or {}).get("trending_list")) or []
        words = [w.get("word") for w in tl if isinstance(w, dict) and w.get("word")]
        return words[:limit] or None
    except Exception:  # noqa: BLE001 — 热点是 L0 增强·失败不阻塞主报告
        return None


def run_from_video_url(url: str, tikhub_key: str | None = None, *,
                       with_audiovisual: bool = True,
                       competitor_urls: list[str] | None = None) -> dict[str, Any]:
    """主入口:抖音视频链接 → {ok, report_md, video, account, audit, works, six_layer}。

    with_audiovisual=True 且有 SILICONFLOW_API_KEY 时,下载视频走 Qwen3-Omni 产视听六层并插入报告。
    competitor_urls 给定时,各采竞品账号 → L4 竞品圈对比段插入报告(三圈参照·竞品不递归采竞品)。
    """
    # 平台门（实测驱动）：probe 现状 TikHub 仅抖音·非抖音友好报错·不浪费付费调用
    platform = _detect_platform(url)
    if platform != "douyin":
        return {"ok": False, "platform": platform,
                "error": f"暂仅支持抖音链路（TikHub 抖音源）·{_PLATFORM_CN.get(platform, platform)}待接入。"
                         f"请提供抖音视频链接（www.douyin.com/video/... 或 v.douyin.com 短链）。"}
    _ensure_combo()
    from combo_deep_probe import build_account_probe
    from combo_deep_probe.adapters.tikhub_adapter import tikhub_get

    key = tikhub_key or os.getenv("TIKHUB_API_KEY") or os.getenv("PROBE_TIKHUB_KEY")
    if not key:
        return {"ok": False, "error": "缺 TIKHUB_API_KEY/PROBE_TIKHUB_KEY(走 vault)"}

    aweme_id = resolve_douyin(url)
    if not aweme_id:
        return {"ok": False, "error": "无法从链接解析 aweme_id"}

    # 1. 视频详情 → 指标 + 作者 sec_uid
    raw = tikhub_get("/api/v1/douyin/web/fetch_one_video", {"aweme_id": aweme_id}, key)
    detail = (raw.get("data") or {}).get("aweme_detail") or {}
    if not detail:
        return {"ok": False, "error": "视频详情为空(响应结构变化?)"}
    st = detail.get("statistics") or {}
    author = detail.get("author") or {}
    sec_uid = author.get("sec_uid")
    video = {
        "title": detail.get("desc") or "",
        "like": st.get("digg_count") or 0,
        "comment": st.get("comment_count") or 0,
        "share": st.get("share_count") or 0,
        "collect": st.get("collect_count") or 0,
        "duration_s": round((detail.get("video") or {}).get("duration", 0) / 1000),
    }
    if not sec_uid:
        return {"ok": False, "error": "拿不到作者 sec_uid(无法多维)", "video": video}

    # 2. 账号 + 兄弟视频(works)
    rep = build_account_probe(tikhub_key=key).analyze(sec_user_id=sec_uid, count=20)
    rd = rep.to_dict()
    prof = rd.get("profile") or {}
    diag = rd.get("diagnosis") or {}
    account = {
        "nickname": prof.get("nickname") or author.get("nickname"),
        "follower": prof.get("follower_count") or author.get("follower_count"),
        "aweme_count": prof.get("aweme_count"),
        "works_analyzed": rd.get("works_analyzed"),
        "signature": prof.get("signature"),
        "avg_like": (diag.get("like") or {}).get("avg"),
        "max_like": (diag.get("like") or {}).get("max"),
        "burst_ratio": diag.get("burst_ratio"),
        "vertical_score": diag.get("vertical_score"),
        "hashtags": [t[0] for t in (diag.get("top_hashtags") or []) if t],
    }

    # 3. 担保:账号 → 转换器 → 八闸
    claims, sources = account_to_claims_sources(rd, "https://www.douyin.com/user/" + sec_uid)
    audit_raw = run_audit(claims, sources, tier="paid")
    cl = audit_raw.get("conclusion_label") or {}
    audit = {
        "source_reliability": cl.get("source_reliability"),
        "confidence_level": cl.get("confidence_level"),
        "evidence_strength": cl.get("evidence_strength"),
    }

    # 4.5 视听六层(L1·真"看+听"视频·走硅基 Qwen3-Omni·下载中转·失败不阻塞主报告)
    av_md, av_six = None, None
    if with_audiovisual and os.getenv("SILICONFLOW_API_KEY"):
        play_urls = ((detail.get("video") or {}).get("play_addr") or {}).get("url_list") or []
        # max_frames=10/fps=1/timeout=180:大视频(30MB+)16帧会 Omni 超时·降帧平衡质量与速度(实测 8 帧通)
        av_out = analyze_douyin_video(play_urls, max_frames=10, fps=1, timeout=180)
        if av_out.get("ok"):
            av_six = av_out.get("six_layer")
            av_md = render_av_section(av_six)

    # 4.7 L4 竞品圈对比(有竞品链接则各采账号 → 对比段·竞品不递归采竞品/不跑视听省钱)
    compare_md = None
    if competitor_urls:
        comp_accts = []
        for cu in competitor_urls:
            cr = run_from_video_url(cu, tikhub_key, with_audiovisual=False)
            if cr.get("ok") and cr.get("account"):
                comp_accts.append(cr["account"])
        if comp_accts:
            compare_md = compare_accounts(account, comp_accts)

    # 4.8 L0 环境层(赛道大环境·种子平台规则+粉丝分层+TikHub 热榜热点·趋势待半自动)
    _blob = " ".join(account.get("hashtags") or []) + (account.get("signature") or "")
    _track_name, _ = _track(_blob)
    _hot = fetch_douyin_hot_topics(key)   # 当前平台热点(失败 None·L0 诚实标)
    l0 = build_l0_environment(account, track=_track_name, is_business=_is_business(_blob),
                              hot_topics=_hot)
    l0_md = render_l0_section(l0)

    # 4.9 商业转化诊断(战略主轴·三层诊断+商业数据增强+精准转化方案)
    works = rd.get("works_sample")
    _tv = classify_track_value(account)
    _biz_data = {"commission": category_commission(_track_name),
                 "gmv": category_gmv_tier(_track_name),
                 "xingtu": xingtu_price_estimate(account.get("follower") or 0, _track_name)}
    business_md = "\n\n".join(filter(None, [
        render_commercial_section(account, _tv),
        render_commercial_data_section(account, _track_name, _biz_data),
        render_conversion_section(account, video, works, av_six),
    ]))

    # 5. 确定性报告(works→L2;av_md→L1视听;compare_md→L4竞品;l0_md→L0;business_md→商业转化主轴)
    report_md = build_report(video, account, audit, works=works,
                             av_md=av_md, compare_md=compare_md, l0_md=l0_md,
                             business_md=business_md)

    # 5.5 LLM 润色(内容方法论原则1真叙事感·REPORT_POLISH=1 启用·默认关·只重组不编造·失败降级原文)
    if os.getenv("REPORT_POLISH") == "1":
        from app.services.report_polish import polish_report
        _pol = polish_report(report_md, must_keep=[
            account.get("follower"), account.get("avg_like"),
            account.get("max_like"), video.get("like")])
        if _pol.get("ok"):
            report_md = _pol["polished"]
    # works/six_layer 一并返回 → 供 Word 导出做动态图表 + 视听六层呈现
    return {"ok": True, "report_md": report_md, "video": video,
            "account": account, "audit": audit, "works": works, "six_layer": av_six}
