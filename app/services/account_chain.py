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
from app.services.account_report import build_report

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


def run_from_video_url(url: str, tikhub_key: str | None = None) -> dict[str, Any]:
    """主入口:抖音视频链接 → {ok, report_md, video, account, audit}。"""
    _ensure_combo()
    from combo_deep_probe import build_account_probe
    from combo_deep_probe.adapters.tikhub_adapter import tikhub_get

    key = tikhub_key or os.getenv("TIKHUB_API_KEY")
    if not key:
        return {"ok": False, "error": "缺 TIKHUB_API_KEY(走 vault)"}

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

    # 4. 确定性报告
    report_md = build_report(video, account, audit)
    return {"ok": True, "report_md": report_md, "video": video, "account": account, "audit": audit}
