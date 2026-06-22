"""星图达人商业人格·整体并行（probe-TikHub 方案 v2.0 章四落地）。

把 xingtu_commercial 的"串行调几个端点"升级为"一次 resolve kolid → asyncio.gather
并发取星图全维 → 组装 XingtuProfile 整体对象 → 内部组合洞察"。

复用 P0 采集引擎的加固成果(combo cache_key 三锚点缓存 + body 信封校验)。
字段全部基于 tikhub-xingtu-kol-sample.json 实测真值(2026-06-22)。
未开星图(resolve_kolid→None)→ is_xingtu=False·上游用 xingtu_commercial.xingtu_price_estimate 兜底。
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

import httpx

try:  # 复用 P0 加固(三锚点缓存键 + 信封校验)
    from combo_deep_probe.cache_key import get_ttl, make_cache_key
    from combo_deep_probe.harness import _is_ok_envelope
except Exception:  # noqa: BLE001 — combo 不在路径时降级(不缓存/简单校验)
    make_cache_key = None
    get_ttl = lambda ep: 86400  # noqa: E731
    def _is_ok_envelope(d):  # type: ignore
        return isinstance(d, dict) and d.get("data") is not None

_log = logging.getLogger(__name__)
_BASE = os.environ.get("TIKHUB_API_BASE", "https://api.tikhub.io")
_XT = "/api/v1/douyin/xingtu"
_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
# 画像维度 origin_type(实测真值)
_PT = {0: "性别", 1: "年龄", 2: "省份", 3: "设备", 5: "城市等级",
       6: "兴趣", 8: "城市", 10: "八大人群", 11: "消费品类", 12: "客单价"}


# ── 数据结构(章四 schema·实测字段) ──────────────────────────────────────────
@dataclass
class IndexItem:
    avg_value: float | None = None     # 指数分值 0-100
    rank_percent: float | None = None  # 行业分位·越小越靠前(0.0118=前1.18%)
    rank: int | None = None


@dataclass
class XingtuProfile:
    sec_uid: str
    kolid: str | None = None
    is_xingtu: bool = False
    # 报价
    prices: list[dict] = field(default_factory=list)
    industry_tags: list[str] = field(default_factory=list)
    price_short: int | None = None    # 1-20s
    price_mid: int | None = None      # 21-60s
    price_long: int | None = None     # 60s+
    # 性价比
    cpm: dict[str, Any] = field(default_factory=dict)   # {cpm_1_20,cpm_21_60,cpm_60}
    cpe: dict[str, Any] = field(default_factory=dict)
    expect_vv: int | None = None
    # 6 商业指数(章四 GPM 修复·个体商业值)
    cooperate_index: IndexItem | None = None
    cp_index: IndexItem | None = None
    link_shopping_index: IndexItem | None = None   # 带货
    link_convert_index: IndexItem | None = None    # 转化
    link_spread_index: IndexItem | None = None     # 传播
    link_star_index: IndexItem | None = None       # 明星
    # 画像
    fans_portrait: list[dict] = field(default_factory=list)      # [{type,display,desc,top5}]
    audience_portrait: list[dict] = field(default_factory=list)
    # 时序/内容
    daily_fans: list[dict] = field(default_factory=list)
    rec_videos: list[dict] = field(default_factory=list)
    fetch_ts: float | None = None
    errors: dict[str, str] = field(default_factory=dict)


# ── 异步取数(复用 P0 缓存键 + 信封校验) ──────────────────────────────────────
def _hdr(key: str) -> dict:
    return {"Authorization": f"Bearer {key}", "User-Agent": _UA, "accept": "application/json"}


async def _aget(client, name, params, key, cache):
    """单星图端点·返回 (name, data|None, from_cache)。失败隔离不外抛。"""
    ep = f"{_XT}/{name}"
    clean = {k: v for k, v in params.items() if v is not None}
    ck = make_cache_key(ep, clean) if make_cache_key else None
    if cache is not None and ck:
        hit = cache.get(ck, {})
        if hit is not None:
            return name, (hit.get("data") if isinstance(hit, dict) else hit), True
    try:
        r = await client.get(f"{_BASE}{ep}", params=clean, headers=_hdr(key), timeout=15.0)
        if r.status_code == 200:
            try:
                d = r.json()
            except ValueError:
                return name, None, False
            if _is_ok_envelope(d):
                if cache is not None and ck:
                    cache.put(ck, {}, d, ttl_sec=get_ttl(ep))
                return name, d.get("data"), False
    except (httpx.TimeoutException, httpx.TransportError) as e:
        _log.info("星图 %s 失败(降级): %s", name, str(e)[:60])
    return name, None, False


def _resolve_kolid_sync_data(d) -> str | None:
    if isinstance(d, dict):
        kid = d.get("id") or d.get("core_user_id")
        return str(kid) if kid else None
    return None


async def fetch_xingtu_profile_async(sec_uid: str, key: str, cache=None,
                                     kolid: str | None = None,
                                     fetch_extended: bool = True) -> XingtuProfile:
    """整体并行取星图全维 → XingtuProfile。未开星图 → is_xingtu=False。"""
    prof = XingtuProfile(sec_uid=sec_uid, fetch_ts=time.time())
    async with httpx.AsyncClient() as client:
        if not kolid:
            _, d, _ = await _aget(client, "get_xingtu_kolid_by_sec_user_id",
                                  {"sec_user_id": sec_uid}, key, cache)
            kolid = _resolve_kolid_sync_data(d)
        if not kolid:
            return prof
        prof.kolid = kolid

        specs = [
            ("kol_service_price_v1", {"kolId": kolid, "platformChannel": 1}),
            ("kol_cp_info_v1", {"kolId": kolid}),
            ("kol_xingtu_index_v1", {"kolId": kolid}),
            ("kol_fans_portrait_v1", {"kolId": kolid, "fansType": 1}),
        ]
        if fetch_extended:
            today = date.today()
            specs += [
                ("kol_audience_portrait_v1", {"kolId": kolid}),
                ("kol_rec_videos_v1", {"kolId": kolid}),
                ("kol_daily_fans_v1", {"kolId": kolid,
                                       "startDate": (today - timedelta(days=30)).strftime("%Y%m%d"),
                                       "endDate": today.strftime("%Y%m%d")}),
            ]
        got = await asyncio.gather(*[_aget(client, n, p, key, cache) for n, p in specs])
    _assemble(prof, {name: data for name, data, _ in got})
    return prof


def fetch_xingtu_profile(sec_uid: str, key: str, cache=None, kolid: str | None = None,
                         fetch_extended: bool = True) -> XingtuProfile:
    """同步包装(account_chain 调此)。已在事件循环中需 nest_asyncio。"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    coro = fetch_xingtu_profile_async(sec_uid, key, cache, kolid, fetch_extended)
    if loop and loop.is_running():
        import nest_asyncio
        nest_asyncio.apply()
        return loop.run_until_complete(coro)
    return asyncio.run(coro)


# ── 组装 ─────────────────────────────────────────────────────────────────────
_VT = {1: "short", 2: "mid", 71: "long"}


def _idx(d) -> IndexItem | None:
    if not isinstance(d, dict):
        return None
    return IndexItem(avg_value=d.get("avg_value"), rank_percent=d.get("rank_percent"),
                     rank=d.get("rank"))


def _portrait_dims(d) -> list[dict]:
    if not isinstance(d, dict) or not d.get("distributions"):
        return []
    out = []
    for dist in d["distributions"]:
        lst = dist.get("distribution_list") or []
        top5 = sorted(((x.get("distribution_key"), _to_int(x.get("distribution_value")))
                       for x in lst if x.get("distribution_key")), key=lambda t: -t[1])[:5]
        ot = dist.get("origin_type")
        out.append({"type": ot, "display": dist.get("type_display") or _PT.get(ot, str(ot)),
                    "desc": dist.get("description", ""), "top5": top5})
    return out


def _assemble(prof: XingtuProfile, m: dict) -> None:
    # 报价
    sp = m.get("kol_service_price_v1")
    if isinstance(sp, dict):
        for it in (sp.get("price_info") or []):
            if it.get("is_open") and it.get("price"):
                prof.prices.append({"desc": it.get("desc", ""), "price": it.get("price"),
                                    "settlement": it.get("settlement_desc", ""),
                                    "video_type": it.get("video_type")})
                slot = _VT.get(it.get("video_type"))
                if slot:
                    setattr(prof, f"price_{slot}", it.get("price"))
        prof.industry_tags = sp.get("industry_tags") or []
    # 性价比
    cp = m.get("kol_cp_info_v1")
    if isinstance(cp, dict):
        prof.cpe = cp.get("expect_cpe") or {}
        prof.cpm = cp.get("expect_cpm") or {}
        prof.expect_vv = (cp.get("expect_vv") or {}).get("value")
    # 6 指数
    xi = m.get("kol_xingtu_index_v1")
    if isinstance(xi, dict):
        prof.cooperate_index = _idx(xi.get("cooperate_index"))
        prof.cp_index = _idx(xi.get("cp_index"))
        prof.link_shopping_index = _idx(xi.get("link_shopping_index"))
        prof.link_convert_index = _idx(xi.get("link_convert_index"))
        prof.link_spread_index = _idx(xi.get("link_spread_index"))
        prof.link_star_index = _idx(xi.get("link_star_index"))
    # 画像
    prof.fans_portrait = _portrait_dims(m.get("kol_fans_portrait_v1"))
    prof.audience_portrait = _portrait_dims(m.get("kol_audience_portrait_v1"))
    # 时序/内容
    df = m.get("kol_daily_fans_v1")
    if isinstance(df, dict):
        prof.daily_fans = df.get("daily_fans_list") or df.get("fans_list") or []
    rv = m.get("kol_rec_videos_v1")
    if isinstance(rv, dict):
        prof.rec_videos = rv.get("masterpiece_videos") or rv.get("video_list") or []

    prof.is_xingtu = bool(prof.prices or prof.cpm or prof.fans_portrait
                          or prof.cooperate_index)


def _to_int(v) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


# ── 内部组合洞察(章四 §4.4) ──────────────────────────────────────────────────
def roi_triangle(prof: XingtuProfile) -> dict | None:
    """投放 ROI 三角: 报价÷预期播放 得实际CPM·与官方CPM对比是否虚高/吻合。"""
    if not (prof.price_short and prof.expect_vv):
        return None
    actual_cpm = prof.price_short / (prof.expect_vv / 1000)   # 元/千次
    # 实测 official cpm 以"分"计(章四确认 2156=¥21.56·与 actual 吻合证实)·/100 对齐元
    official = (_to_int(prof.cpm.get("cpm_1_20")) / 100) or None
    ratio = actual_cpm / official if official else None
    verdict = ("数据吻合可信" if ratio and 0.7 <= ratio <= 1.5
               else "报价偏高存疑" if ratio and ratio > 1.5 else "待核")
    return {"actual_cpm": round(actual_cpm, 1),
            "official_cpm": round(official, 1) if official else None,
            "ratio": round(ratio, 2) if ratio else None, "verdict": verdict}


def breakout_signal(prof: XingtuProfile) -> dict | None:
    """破圈信号: 粉丝画像 vs 观众画像同维 top1 不一致 = 看的人≠粉丝。"""
    if not (prof.fans_portrait and prof.audience_portrait):
        return None
    fan = {d["type"]: (d["top5"][0][0] if d["top5"] else None) for d in prof.fans_portrait}
    aud = {d["type"]: (d["top5"][0][0] if d["top5"] else None) for d in prof.audience_portrait}
    diff = {_PT.get(t, str(t)): {"fans": fan[t], "audience": aud[t]}
            for t in fan if t in aud and fan[t] != aud[t] and fan[t] and aud[t]}
    return {"has_breakout": bool(diff), "dims": diff,
            "signal": "内容破圈(观众≠粉丝)" if diff else "粉丝=观众·精准无破圈"}


def commercial_momentum(prof: XingtuProfile) -> dict | None:
    """商业价值导数: 近期涨粉趋势 × 合作指数行业分位。"""
    rp = prof.cooperate_index.rank_percent if prof.cooperate_index else None
    if rp is None and not prof.daily_fans:
        return None
    adds = [d.get("add_fans_count") or d.get("incr") or 0 for d in prof.daily_fans[-14:]]
    avg = round(sum(adds) / len(adds)) if adds else None
    trend = ("上升" if len(adds) >= 2 and adds[-1] > adds[0]
             else "下降" if len(adds) >= 2 and adds[-1] < adds[0] else "平稳")
    rank_s = f"行业前{rp * 100:.1f}%" if rp is not None else "指数缺失"
    return {"avg_daily_fans": avg, "trend_14d": trend if adds else None, "rank": rank_s}


# ── 渲染 ─────────────────────────────────────────────────────────────────────
def render_xingtu_profile_section(prof: XingtuProfile | None) -> str | None:
    """整体商业人格 → 报告段。未开星图返回 None。"""
    if not prof or not prof.is_xingtu:
        return None
    L = ["### 💼 星图商业人格（巨量星图官方真值·整体并行）", ""]
    if prof.prices:
        items = "；".join(f"{p['desc']} ¥{p['price']:,}" for p in prof.prices[:4])
        L.append(f"- **报价**：{items}")
    if prof.cpm.get("cpm_1_20"):
        vv = f"·预期播放 {prof.expect_vv / 10000:.0f}万" if prof.expect_vv else ""
        lo, hi = _to_int(prof.cpm.get("cpm_1_20")) / 100, _to_int(prof.cpm.get("cpm_60")) / 100
        L.append(f"- **性价比**：CPM ¥{lo:.0f}–{hi:.0f}/千次{vv}")
    # 6 指数(个体商业值·章四 GPM 修复)
    si = prof.link_shopping_index
    if si and si.avg_value is not None:
        rk = f"·行业前{si.rank_percent * 100:.1f}%" if si.rank_percent else ""
        L.append(f"- **带货指数**：{si.avg_value:.0f}/100{rk}"
                 + (f"·转化指数 {prof.link_convert_index.avg_value:.0f}"
                    if prof.link_convert_index and prof.link_convert_index.avg_value else ""))
    if prof.fans_portrait:
        for d in prof.fans_portrait[:4]:
            if d.get("desc"):
                L.append(f"- 粉丝{d['display']}：{d['desc']}")
    # 组合洞察
    roi = roi_triangle(prof)
    if roi:
        L.append(f"- **投放ROI核验**：实际CPM ¥{roi['actual_cpm']} vs 官方 ¥{roi['official_cpm']}→{roi['verdict']}")
    bo = breakout_signal(prof)
    if bo:
        L.append(f"- **破圈信号**：{bo['signal']}")
    L.append("")
    L.append("> 星图官方数据·整体并行一次取全报价/性价比/6商业指数/画像。")
    return "\n".join(L)
