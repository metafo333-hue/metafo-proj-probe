"""星图达人商业真值（kolId 直取·绕开"估算"）· probe 商业转化主轴。

凭 sec_uid → 游客 kolid → 巨量星图官方端点取**真实**报价/性价比/指数/粉丝画像。
开通星图的达人才有；未开通则各端点空 → 返回 None，上游降级到
`commercial_data.xingtu_price_estimate`（公式估算）兜底。

真源端点（2026-06-22 实测通·TikHub /douyin/xingtu/）：
  get_xingtu_kolid_by_sec_user_id  sec_uid → kolid
  kol_service_price_v1  报价 price_info[].{desc,price,settlement_desc}
  kol_cp_info_v1        expect_cpe / expect_cpm / expect_vv（性价比）
  kol_xingtu_index_v1   cooperate_index / cp_index（含 rank_percent 行业分位）
  kol_fans_portrait_v1  distributions[].{description,distribution_list}（官方真画像）
"""
from __future__ import annotations

import logging
from typing import Any

_log = logging.getLogger(__name__)
_BASE = "/api/v1/douyin/xingtu"


def _get(ep: str, params: dict, key: str) -> dict | None:
    """调 TikHub 星图端点·失败返回 None（不阻塞主链）。"""
    try:
        from combo_deep_probe.adapters.tikhub_adapter import tikhub_get
        raw = tikhub_get(f"{_BASE}/{ep}", params, key, timeout=20.0)
        return (raw or {}).get("data") if isinstance(raw, dict) else None
    except Exception as e:  # noqa: BLE001
        _log.info("星图端点 %s 取数失败(降级): %s", ep, str(e)[:80])
        return None


def resolve_kolid(sec_uid: str, key: str) -> str | None:
    """sec_uid → 游客星图 kolid（未开星图则 None）。"""
    d = _get("get_xingtu_kolid_by_sec_user_id", {"sec_user_id": sec_uid}, key)
    if not isinstance(d, dict):
        return None
    kid = d.get("id") or d.get("core_user_id")
    return str(kid) if kid else None


def fetch_xingtu_commercial(sec_uid: str, key: str,
                            kolid: str | None = None) -> dict[str, Any] | None:
    """取达人星图商业真值。未开星图/全空 → None（上游用估算兜底）。"""
    kolid = kolid or resolve_kolid(sec_uid, key)
    if not kolid:
        return None
    out: dict[str, Any] = {"kolid": kolid, "is_real": True}

    # 报价：取视频类报价（video_type 升序·desc 如"1-20s视频"）
    sp = _get("kol_service_price_v1", {"kolId": kolid, "platformChannel": 1}, key)
    if isinstance(sp, dict):
        prices = []
        for it in (sp.get("price_info") or []):
            if it.get("is_open") and it.get("price"):
                prices.append({"desc": it.get("desc", ""), "price": it.get("price"),
                               "settlement": it.get("settlement_desc", "")})
        out["prices"] = prices
        out["industry_tags"] = sp.get("industry_tags") or []

    # 性价比：CPE/CPM/预期播放
    cp = _get("kol_cp_info_v1", {"kolId": kolid}, key)
    if isinstance(cp, dict):
        cpe, cpm = cp.get("expect_cpe") or {}, cp.get("expect_cpm") or {}
        out["cpe_range"] = [cpe.get("cpe_1_20"), cpe.get("cpe_60")]
        out["cpm_range"] = [cpm.get("cpm_1_20"), cpm.get("cpm_60")]
        out["expect_vv"] = (cp.get("expect_vv") or {}).get("value")

    # 星图指数（含行业分位 rank_percent·越小越靠前）
    xi = _get("kol_xingtu_index_v1", {"kolId": kolid}, key)
    if isinstance(xi, dict):
        coop, cpi = xi.get("cooperate_index") or {}, xi.get("cp_index") or {}
        out["cooperate_index"] = coop.get("value")
        out["cooperate_rank_percent"] = coop.get("rank_percent")
        out["cp_index"] = cpi.get("value")

    # 只有 kolid、其余全空 → 视为无效真值（注意 cpm_range=[None,None] 也算空）
    _has = (bool(out.get("prices"))
            or bool((out.get("cpm_range") or [None])[0])
            or out.get("cooperate_index") is not None)
    if not _has:
        return None
    return out


def fetch_fans_portrait(sec_uid: str, key: str, kolid: str | None = None) -> dict[str, Any] | None:
    """粉丝画像官方真值（星图）。返回 {dimensions:[{title,desc,top:[(k,v)]}]}。"""
    kolid = kolid or resolve_kolid(sec_uid, key)
    if not kolid:
        return None
    d = _get("kol_fans_portrait_v1", {"kolId": kolid, "fansType": 1}, key)
    if not isinstance(d, dict) or not d.get("distributions"):
        return None
    dims = []
    for dist in d["distributions"]:
        lst = dist.get("distribution_list") or []
        top = sorted(
            ((x.get("distribution_key"), _to_int(x.get("distribution_value")))
             for x in lst if x.get("distribution_key")),
            key=lambda x: -x[1])[:5]
        dims.append({"desc": dist.get("description", ""), "top": top})
    return {"kolid": kolid, "is_real": True, "dimensions": dims} if dims else None


def _to_int(v: Any) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def render_xingtu_section(data: dict[str, Any] | None) -> str | None:
    """星图商业真值 → 报告段（说人话）。"""
    if not data or not data.get("is_real"):
        return None
    L = ["### 💼 星图商业档案（巨量星图官方真值·非估算）", ""]
    prices = data.get("prices") or []
    if prices:
        items = "；".join(f"{p['desc']} ¥{p['price']:,}（{p['settlement']}）" for p in prices[:4])
        L.append(f"- **接单报价**：{items}")
    cpm = data.get("cpm_range") or []
    if cpm and cpm[0]:
        vv = data.get("expect_vv")
        vv_s = f"·预期播放 {vv/10000:.0f}万" if vv else ""
        L.append(f"- **投放性价比**：CPM ¥{cpm[0]}–{cpm[1]}（每千次播放成本）{vv_s}")
    if data.get("cooperate_index") is not None:
        rp = data.get("cooperate_rank_percent")
        rank_s = f"·行业前 {rp*100:.2f}%" if rp else ""
        L.append(f"- **星图指数**：合作指数 {data['cooperate_index']}{rank_s}"
                 + (f"·性价比指数 {data['cp_index']}" if data.get("cp_index") else ""))
    if data.get("industry_tags"):
        L.append(f"- **官方行业标签**：{'、'.join(data['industry_tags'][:3])}")
    L.append("")
    L.append("> 说明：以上为达人巨量星图后台官方数据，反映真实商业接单能力（比按粉丝量估算准确）。")
    return "\n".join(L)


def render_fans_portrait_section(data: dict[str, Any] | None) -> str | None:
    """粉丝画像官方真值 → 报告段。"""
    if not data or not data.get("dimensions"):
        return None
    L = ["### 👥 粉丝画像（星图官方·真实人群结构）", ""]
    for dim in data["dimensions"][:4]:
        if dim.get("desc"):
            L.append(f"- {dim['desc']}")
    L.append("")
    L.append("> 说明：来自星图官方粉丝画像，非评论区估算，可直接用于投放人群匹配。")
    return "\n".join(L)
