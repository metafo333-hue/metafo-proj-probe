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


_HOT_TOPICS_CACHE: dict = {"ts": 0, "data": None}
_HOT_TOPICS_TTL = 3600  # 1小时


def fetch_douyin_hot_topics(tikhub_key: str | None, limit: int = 8) -> list[str] | None:
    """TikHub 抖音热榜(app/v3) → 当前平台热点词(供 L0 蹭热点参考·失败 None 不阻塞)。
    模块级缓存 1 小时·同进程内多次调用不重复打 API。
    """
    import time
    key = tikhub_key or os.getenv("TIKHUB_API_KEY") or os.getenv("PROBE_TIKHUB_KEY")
    if not key:
        return None
    now = time.time()
    if _HOT_TOPICS_CACHE["data"] and now - _HOT_TOPICS_CACHE["ts"] < _HOT_TOPICS_TTL:
        return _HOT_TOPICS_CACHE["data"][:limit] or None
    try:
        _ensure_combo()
        from combo_deep_probe.adapters.tikhub_adapter import tikhub_get
        raw = tikhub_get("/api/v1/douyin/app/v3/fetch_hot_search_list", {}, key)
        tl = (((raw.get("data") or {}).get("data") or {}).get("trending_list")) or []
        words = [w.get("word") for w in tl if isinstance(w, dict) and w.get("word")]
        result = words[:limit] or None
        _HOT_TOPICS_CACHE["ts"] = now
        _HOT_TOPICS_CACHE["data"] = words  # 存全量·按 limit 切片
        return result
    except Exception:  # noqa: BLE001 — 热点是 L0 增强·失败不阻塞主报告
        return None


def _calc_ratio(works: list, key: str) -> float:
    """计算 works 中指定字段为 True 的比例。"""
    if not works:
        return 0.0
    return round(sum(1 for w in works if w.get(key)) / len(works), 3)


def _agg_video_tags(works: list) -> list[str]:
    """聚合 works 中 video_tag 的 level-1 标签，返回出现次数最多的前3个。"""
    counts: dict[str, int] = {}
    for w in works:
        for level, tag_name in (w.get("video_tag") or []):
            if level == 1 and tag_name:
                counts[tag_name] = counts.get(tag_name, 0) + 1
    return [t for t, _ in sorted(counts.items(), key=lambda x: -x[1])[:3]]


def run_from_video_url(url: str, tikhub_key: str | None = None, *,
                       with_audiovisual: bool = True,
                       competitor_urls: list[str] | None = None,
                       _depth: int = 0) -> dict[str, Any]:
    """主入口:抖音视频链接 → {ok, report_md, video, account, audit, works, six_layer}。

    with_audiovisual=True 且有 SILICONFLOW_API_KEY 时,下载视频走 Qwen3-Omni 产视听六层并插入报告。
    competitor_urls 给定时,各采竞品账号 → L4 竞品圈对比段插入报告(三圈参照·竞品不递归采竞品)。
    _depth 内部递归深度计数器（外部调用方不传）：depth>0 时禁止再递归竞品圈，防无限循环。
    """
    if _depth > 1:
        return {"ok": False, "error": "递归深度超限·竞品链路最多一层(depth>1)"}

    # 平台门（实测驱动）：TikHub 仅抖音·非抖音走专属数据源或轻量分析
    platform = _detect_platform(url)
    if platform != "douyin":
        from app.services.cross_platform_render import render_platform
        report_md = None

        # 微信视频号：优先走 JZL 付费数据（13字段·¥0.2/页）
        if platform == "wechat_channels":
            jzl_key = os.getenv("PROBE_JZL_KEY")
            if jzl_key:
                try:
                    from app.datasources.jzl_channels import JZLChannelsAdapter
                    jzl = JZLChannelsAdapter()
                    flat = jzl.fetch_metadata(url, "social")
                    if not flat.get("_error") and not flat.get("_needs_key"):
                        flat["_source"] = "jzl"
                        flat["platform"] = platform
                        report_md = render_platform(platform, flat)
                except Exception:  # noqa: BLE001
                    pass

        # 其他平台（或 JZL 不可用时）：combo-deep-probe 通用轻量分析
        if not report_md:
            try:
                _ensure_combo()
                from combo_deep_probe import build_default
                key = tikhub_key or os.getenv("TIKHUB_API_KEY") or os.getenv("PROBE_TIKHUB_KEY")
                probe = build_default(tikhub_key=key)
                packet = probe.collect(url)
                flat_c: dict[str, Any] = {"_source": "combo", "platform": platform}
                for _dim, fields in (packet.dimensions or {}).items():
                    for name, fld in fields.items():
                        flat_c[name] = fld.value
                report_md = render_platform(platform, flat_c)
            except Exception:  # noqa: BLE001
                pass

        return {
            "ok": bool(report_md),
            "platform": platform,
            "report_md": report_md,
            "error": None if report_md else (
                f"暂仅深度支持抖音·{_PLATFORM_CN.get(platform, platform)} 已出基础报告"
            ),
        }
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
    # 字段契约校验：combo-deep-probe to_dict() 必须返回这四个顶层键（版本漂移早发现）
    _CONTRACT_FIELDS = ("profile", "diagnosis", "works_sample", "works_analyzed")
    _missing_fields = [f for f in _CONTRACT_FIELDS if f not in rd]
    if _missing_fields:
        import logging as _clog
        _clog.getLogger(__name__).warning(
            "combo-deep-probe.to_dict() 字段缺失: %s · 可能版本漂移，请检查两仓字段契约",
            _missing_fields)
    prof = rd.get("profile") or {}
    diag = rd.get("diagnosis") or {}
    works = rd.get("works_sample")  # 提前到 account dict 之前供新字段使用
    account = {
        # ── 身份锚点（三坐标·供案例聚合 + 仪表盘身份字段·B1/B2 修复）──
        "sec_uid": sec_uid,
        "aweme_id": aweme_id,
        # ── 基础档案 ──
        "nickname": prof.get("nickname") or author.get("nickname"),
        "follower": prof.get("follower_count") or author.get("follower_count"),
        "aweme_count": prof.get("aweme_count"),
        "works_analyzed": rd.get("works_analyzed"),
        "signature": prof.get("signature"),
        # ── 诊断指标 ──
        "avg_like": (diag.get("like") or {}).get("avg"),
        "max_like": (diag.get("like") or {}).get("max"),
        "burst_ratio": diag.get("burst_ratio"),
        "vertical_score": diag.get("vertical_score"),
        "hashtags": [t[0] for t in (diag.get("top_hashtags") or []) if t],
        # ── 商业化信号 ──
        "max_follower": prof.get("max_follower_count"),             # 历史峰值粉丝
        "mplatform_followers": prof.get("mplatform_followers_count"),  # 多平台汇总
        "with_commerce_entry": prof.get("with_commerce_entry"),     # 橱窗是否开通
        "live_commerce": prof.get("live_commerce"),                 # 直播带货是否开通
        "commerce_user_level": prof.get("commerce_user_level"),     # 商业化等级
        "star_atlas": prof.get("star_atlas"),                       # 星图状态
        # ── 直播状态 ──
        "live_status": prof.get("live_status"),                     # 直播状态
        "room_id": prof.get("room_id"),                             # 直播间ID
        # ── 账号身份 ──
        "role_id": prof.get("role_id"),                             # 角色ID
        "is_gov_media_vip": prof.get("is_gov_media_vip"),           # 政府/媒体认证
        # ── 内容体系 ──
        "mix_count": prof.get("mix_count"),                         # 合集数
        "series_count": prof.get("series_count"),                   # 系列数
        "dog_card_rank": (prof.get("dog_card_info") or {}).get("rank"),        # 榜单排名
        "dog_card_text": (prof.get("dog_card_info") or {}).get("dog_card_text"),  # 榜单名称
        # ── works 统计指标 ──
        "ads_ratio": _calc_ratio(works, "is_ads") if works else None,
        "anchor_ratio": _calc_ratio(works, "has_anchor") if works else None,
        "pgc_ratio": _calc_ratio(works, "music_is_pgc") if works else None,
        "risk_warned_count": sum(1 for w in (works or []) if w.get("risk_warn")),
        "pinned_work": next((w for w in (works or []) if w.get("is_top")), None),
        "platform_tags": _agg_video_tags(works) if works else [],   # 聚合平台三级标签
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

    # 4.6 归因缓存飞轮（存 → 积累 → 批量归因·零额外 API 成本）
    # 每次 Omni 分析后把 {aweme_id, like, six_layer} 存本地；同账号积累 ≥5 条后自动出归因报告段。
    attribution_md = None
    if av_six and sec_uid and aweme_id:
        from app.services.attribution_cache import (
            save_av, load_account_av, cache_stats, render_attribution_progress)
        from app.services.attribution import attribute, render_attribution_section
        save_av(sec_uid, aweme_id, video.get("like", 0), av_six)
        cached = load_account_av(sec_uid)
        stats = cache_stats(sec_uid)
        if stats["ready"]:
            attr = attribute(cached)
            attribution_md = render_attribution_section(attr)
        else:
            attribution_md = render_attribution_progress(sec_uid)

    # 4.7 L4 竞品圈对比(有竞品链接则各采账号 → 对比段·竞品不递归采竞品/不跑视听省钱)
    compare_md = None
    if competitor_urls and _depth == 0:  # 铁律：只在顶层递归竞品，depth>0 禁止
        comp_accts = []
        for cu in competitor_urls:
            cr = run_from_video_url(cu, tikhub_key, with_audiovisual=False,
                                    _depth=_depth + 1)
            if cr.get("ok") and cr.get("account"):
                comp_accts.append(cr["account"])
        if comp_accts:
            compare_md = compare_accounts(account, comp_accts)

    # 4.8 L0 环境层(赛道大环境·种子平台规则+粉丝分层+TikHub 热榜热点·趋势待半自动)
    _blob = " ".join(account.get("hashtags") or []) + (account.get("signature") or "") + \
            " ".join(account.get("platform_tags") or [])  # 平台三级标签优先增强赛道判断
    _track_name, _ = _track(_blob)
    _hot = fetch_douyin_hot_topics(key)   # 当前平台热点(失败 None·L0 诚实标)
    l0 = build_l0_environment(account, track=_track_name, is_business=_is_business(_blob),
                              hot_topics=_hot)
    l0_md = render_l0_section(l0)

    # 4.9 商业转化诊断(战略主轴·三层诊断+商业数据增强+精准转化方案)
    # works 已在步骤2提前赋值，此处直接使用
    _tv = classify_track_value(account)
    _biz_data = {"commission": category_commission(_track_name),
                 "gmv": category_gmv_tier(_track_name),
                 "xingtu": xingtu_price_estimate(account.get("follower") or 0, _track_name)}
    business_md = "\n\n".join(filter(None, [
        render_commercial_section(account, _tv),
        render_commercial_data_section(account, _track_name, _biz_data),
        render_conversion_section(account, video, works, av_six),
    ]))

    # 4.10 11 缺口科学适应方案段(2026-06-22·确定性为主·全可选·单模块失败独立降级不影响整体报告)
    import logging as _lg
    _log = _lg.getLogger(__name__)
    _signals = {**account, "max_single_views": account.get("max_like") or 0,
                "works_count": account.get("aweme_count") or 0}
    segment_md = cold_start_md = audience_md = comment_md = homepage_md = None
    trend_md = benchmark_md = risk_md = verify_md = action_md = None
    _seg = None
    _risk_findings: list = []
    try:  # 对象层:创作者分层 + 能力适配
        from app.services import creator_segment as _cs
        _seg = _cs.classify_segment(_signals)
        try:
            _seg.capability = _cs.build_capability_profile(_signals)
        except Exception:  # noqa: BLE001
            pass
        segment_md = _cs.render_segment_section(_signals, result=_seg)
    except Exception as _e:  # noqa: BLE001
        _log.warning("creator_segment 降级: %s", _e)
    try:  # 对象层:冷启动(仅 0 数据/起号期触发)
        from app.services import cold_start as _coldmod
        if _coldmod.route_mode(account) in ("cold_start", "hybrid"):
            cold_start_md = _coldmod.render_cold_start_section(
                account, getattr(_seg, "segment", None), target_track=_track_name)
    except Exception as _e:  # noqa: BLE001
        _log.warning("cold_start 降级: %s", _e)
    try:  # 转化承接:主页诊断
        from app.services import homepage_diagnose as _hp
        homepage_md = _hp.render_homepage_section(
            _hp.diagnose_homepage(account, works, _track_name), video)
    except Exception as _e:  # noqa: BLE001
        _log.warning("homepage_diagnose 降级: %s", _e)
    try:  # 分析层:趋势轨迹(作品自带时间戳·单次即可)
        from app.services import trend_analysis as _tr
        trend_md = _tr.render_trend_section(works or [], industry=_track_name, account=account)
    except Exception as _e:  # noqa: BLE001
        _log.warning("trend_analysis 降级: %s", _e)
    try:  # 标准层:同赛道对标(repo 默认经验兜底·灰度feed换 repo=·每次诊断脱敏沉淀自建库)
        from app.services import benchmark as _bm
        _repo = _bm.LocalAccumRepo()
        benchmark_md = _bm.render_benchmark_section(account, _track_name, repo=_repo)
        _bm.ingest_for_benchmark(account, _track_name, _repo)
    except Exception as _e:  # noqa: BLE001
        _log.warning("benchmark 降级: %s", _e)
    try:  # 分析层:风险下行预警
        from app.services import risk_alert as _ra
        _risk_findings = _ra.scan_risks(account, video=video, works=works) or []
        risk_md = _ra.render_risk_section(account, _risk_findings)
    except Exception as _e:  # noqa: BLE001
        _log.warning("risk_alert 降级: %s", _e)
    try:  # 输出层:行动清单+优先级(合规命中→硬置顶整改项)
        from app.services import action_planner as _ap
        _diag = [{"code": "compliance_hit",
                  "params": {"bad_term": "、".join((_f.get("evidence") or {}).get("hit_keywords") or []),
                             "good_term": "合规说法"}}
                 for _f in _risk_findings if _f.get("risk_type") == "ban_redline"]
        action_md = _ap.render_action_section(
            _ap.plan_actions(_diag, track=_track_name, account=account))
    except Exception as _e:  # noqa: BLE001
        _log.warning("action_planner 降级: %s", _e)
    try:  # 闭环层:已验证建议生效(本地积累·首诊为空·复诊渐显)
        from app.services import verify_loop as _vl
        verify_md = _vl.render_verify_section(sec_uid)
    except Exception as _e:  # noqa: BLE001
        _log.warning("verify_loop 降级: %s", _e)
    # 输入层:评论洞察(TikHub 持牌源·安全接入·PROBE_COMMENT_ENABLED 灰度开关·默认开·可一键关)
    if os.getenv("PROBE_COMMENT_ENABLED", "1") == "1":
        try:
            from app.datasources.tikhub_comment_source import TikHubCommentSource
            from app.services import comment_insight as _ci
            _comments = _ci.load_comments(TikHubCommentSource(key), aweme_id, limit=100)
            comment_md = _ci.render_comment_section(
                _ci.analyze_comments(_comments, _track_name))
        except Exception as _e:  # noqa: BLE001
            _log.warning("comment_insight 降级: %s", _e)
    # 受众画像:A路需创作者授权数据·C路(粉丝列表聚合)PIPL 默认关·
    #   真正的灰色/个人侧通路走 audience_source.register_source 隔离注册(不在商业链自建抓取·
    #   中性指针)·当前自动管线无授权数据 → audience_md 留 None(安全·有授权源时在此接)

    # 4.11 轮动分析（行业板块轮动·五维·零 LLM·失败降级 None）
    rotation_result = None
    rotation_md = None
    try:
        from app.services.rotation_analysis import analyze_rotation, render_rotation_section
        rotation_result = analyze_rotation(account, works or [], _hot)
        # 接入历史账本：把三周期历史轮动数据注入轮动段
        ledger_section = None
        try:
            from app.services.rotation_ledger import render_ledger_section
            if sec_uid:
                ledger_section = render_ledger_section(sec_uid)
        except Exception as _le:  # noqa: BLE001
            _log.warning("rotation_ledger 降级: %s", _le)
        base_rotation = render_rotation_section(account, works or [], _hot)
        rotation_md = (base_rotation + "\n\n" + ledger_section) if ledger_section else base_rotation
    except Exception as _e:  # noqa: BLE001
        _log.warning("rotation_analysis 降级: %s", _e)

    # 4.11b 保存轮动快照（每次分析后自动记录·积累历史数据供三周期分析）
    try:
        from app.services.rotation_ledger import save_snapshot
        if sec_uid:
            _rot_phase = (rotation_result or {}).get("phase", "")
            _rot_window = (rotation_result or {}).get("window_open", False)
            save_snapshot(sec_uid, account, rotation_phase=_rot_phase, window_open=_rot_window)
    except Exception as _e:  # noqa: BLE001
        _log.warning("rotation_ledger save_snapshot 降级: %s", _e)

    # 4.12 综合决策层（联动分析·时效标注·30天预判·失败降级 None）
    synthesis_md = None
    try:
        from app.services.synthesis_engine import render_synthesis_section
        from app.services.commercial import _commerce_maturity_score
        synthesis_md = render_synthesis_section(
            account=account,
            works=works,
            risk_findings=_risk_findings,
            rotation_result=rotation_result,
            commerce_maturity=_commerce_maturity_score(account),
        )
    except Exception as _e:  # noqa: BLE001
        _log.warning("synthesis_engine 降级: %s", _e)

    # 5. 确定性报告
    report_md = build_report(video, account, audit, works=works,
                             av_md=av_md, compare_md=compare_md, l0_md=l0_md,
                             business_md=business_md, attribution_md=attribution_md,
                             segment_md=segment_md, cold_start_md=cold_start_md,
                             audience_md=audience_md, comment_md=comment_md,
                             homepage_md=homepage_md, trend_md=trend_md,
                             benchmark_md=benchmark_md, risk_md=risk_md,
                             verify_md=verify_md, action_md=action_md,
                             rotation_md=rotation_md, synthesis_md=synthesis_md)

    # 5.5 LLM 润色(内容方法论原则1真叙事感·REPORT_POLISH=1 启用·默认关·只重组不编造·失败降级原文)
    if os.getenv("REPORT_POLISH") == "1":
        from app.services.report_polish import polish_report
        _pol = polish_report(report_md, must_keep=[
            account.get("follower"), account.get("avg_like"),
            account.get("max_like"), video.get("like")])
        if _pol.get("ok"):
            report_md = _pol["polished"]
    # works/six_layer/attribution 一并返回 → 供 Word 导出做动态图表 + 视听六层 + 归因
    return {"ok": True, "report_md": report_md, "video": video,
            "account": account, "audit": audit, "works": works,
            "six_layer": av_six, "attribution_md": attribution_md,
            # ── 顶层身份锚点 + 来源（B1/B4 修复·供 save_case 入库 + 仪表盘图例）──
            "aweme_id": aweme_id, "sec_uid": sec_uid,
            "platform": "douyin", "source": "tikhub"}
