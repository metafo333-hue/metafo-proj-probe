"""内容因果链 · content_causal.py · 打通「内容→口碑→势能」(指令2)。

承用户:口碑演化/账号轨迹要深挖·并和整个内容结合出"数据价值"。
单看三块各说各的没价值;价值在串成一条因果链回答——
  做了什么内容(content_dna+归因) → 引发了什么口碑(sentiment) → 带来了什么势能(time_series+二阶导)
并指出**哪一环断了**(内容好口碑弱?口碑好势能没接住?)——断点即最该补的地方。

二阶导(轨迹深挖):time_series 给的是互动斜率(一阶导=在涨还是跌);
本模块再算一阶差分的差分(二阶导=涨得在加速还是放缓)·单次采集用互动代理·
真涨粉二阶导需多次采集(snapshot_store·标"积累中")。
"""
from __future__ import annotations

import statistics as _S
from typing import Any


def _eng(w: dict) -> int:
    return int((w.get("like") or 0) + (w.get("comment") or 0) * 2 + (w.get("collect") or 0) * 3)


# ── 轨迹二阶导:势能在加速还是放缓(互动代理·单次采集)────────────────────────
def acceleration(works: list[dict]) -> dict[str, Any]:
    ws = sorted([w for w in (works or []) if w.get("create_time")],
                key=lambda w: w["create_time"])
    if len(ws) < 9:
        return {"enough": False,
                "verdict": f"作品 {len(ws)} 条(<9)·二阶导需更多样本", "proxy": True}
    t = len(ws) // 3
    early, mid, late = ws[:t], ws[t:2 * t], ws[2 * t:]
    m1, m2, m3 = (_S.mean(_eng(w) for w in seg) for seg in (early, mid, late))
    d1, d2 = m2 - m1, m3 - m2          # 一阶差分(相邻段落差)
    accel = d2 - d1                     # 二阶差分(落差的变化=加速度)
    # 方向判定
    if d2 > 0 and d1 > 0:
        base = "持续上升"
    elif d2 < 0 and d1 < 0:
        base = "持续下滑"
    elif d2 > 0:
        base = "触底回升"
    else:
        base = "见顶回落"
    if abs(accel) < max(1.0, 0.1 * abs(d1)):
        shape = "匀速"
    elif accel > 0:
        shape = "加速" if d2 > 0 else "跌势收窄"
    else:
        shape = "增势放缓" if d2 > 0 else "加速下滑"
    return {
        "enough": True, "proxy": True,
        "seg_means": [round(m1), round(m2), round(m3)],
        "d1": round(d1), "d2": round(d2), "accel": round(accel),
        "base": base, "shape": shape,
        "verdict": f"{base}·{shape}(三段互动 {round(m1)}→{round(m2)}→{round(m3)})",
        "implication": (
            "势能在加速·是加投放/上承接的窗口期" if shape == "加速" else
            "上升但在放缓·钩子/选题需要新鲜度续命" if shape == "增势放缓" else
            "跌势在收窄·近期内容调整起效了·保持" if shape == "跌势收窄" else
            "加速下滑·立即查断更/内容滑坡/限流" if shape == "加速下滑" else
            "势能平稳·按节奏运营"),
        "note": "互动代理(赞+评×2+藏×3)的二阶导·真涨粉二阶导需多次采集(积累中)",
    }


# ── 因果链:内容→口碑→势能 三段串联 + 断点定位 ──────────────────────────────
def build_causal(dna: dict | None, attribution: dict | None,
                 sentiment: dict | None, ts: dict | None,
                 accel: dict | None) -> dict[str, Any]:
    dna = dna or {}
    attribution = attribution or {}
    sentiment = sentiment or {}
    ts = ts or {}
    accel = accel or {}

    # 节点1 内容:做了什么 + 哪个因子驱动
    content_what = dna.get("verdict") or "内容共性待积累"
    driver = (attribution.get("top_driver") or {}).get("factor") if attribution.get("enough") else None
    content_node = {
        "stage": "内容", "icon": "🎬",
        "headline": content_what,
        "detail": (attribution.get("implication") if attribution.get("enough")
                   else "样本不足·暂无强驱动因子"),
        "metrics": {
            "爆款共性": (dna.get("top_hashtags") or dna.get("top_keywords") or [])[:3],
            "样板赞": (dna.get("exemplar") or {}).get("like"),
            "主驱动因子": driver,
        },
        "ok": bool(dna.get("top_hashtags") or dna.get("top_keywords")),
    }

    # 节点2 口碑:引发了什么评价/意向
    s_ok = sentiment.get("enough")
    senti_node = {
        "stage": "口碑", "icon": "💬",
        "headline": sentiment.get("verdict") if s_ok else "口碑样本不足(评论<6)",
        "detail": sentiment.get("intent_trend") if s_ok else "评论数据不够切早晚两段",
        "metrics": ({
            "情感净值Δ": sentiment.get("sentiment_delta"),
            "采购意向Δ": sentiment.get("intent_delta"),
            "时间跨度": sentiment.get("span"),
        } if s_ok else {}),
        "ok": bool(s_ok and sentiment.get("verdict") != "口碑降温"),
    }

    # 节点3 势能:带来了什么趋势 + 加速度
    t_ok = ts.get("enough")
    momentum_node = {
        "stage": "势能", "icon": "📈",
        "headline": (f"{ts.get('stage')}·{ts.get('trend')}" if t_ok else "势能样本不足"),
        "detail": (accel.get("verdict") if accel.get("enough")
                   else (ts.get("rhythm") or "趋势积累中")),
        "metrics": ({
            "互动斜率": ts.get("slope_pct"),
            "二阶导": accel.get("shape") if accel.get("enough") else None,
            "下条预估赞": (ts.get("next_estimate") or {}).get("like_median"),
        } if t_ok else {}),
        "ok": bool(t_ok and "衰退" not in (ts.get("stage") or "")),
    }

    nodes = [content_node, senti_node, momentum_node]

    # 断点定位:第一处 ok→不ok 的跃迁
    broken = None
    if content_node["ok"] and not senti_node["ok"]:
        broken = {"link": "内容→口碑",
                  "say": "内容能跑出爆款·但评论口碑没接住(质疑未回/情感降温)·评论区是信任战场·先补评论运营"}
    elif senti_node["ok"] and not momentum_node["ok"]:
        broken = {"link": "口碑→势能",
                  "say": "口碑在升温、采购意向在涨·但势能没接住(断更/没承接)·这是最可惜的漏斗·立即上私域+提频"}
    elif not content_node["ok"]:
        broken = {"link": "内容源头",
                  "say": "内容还没跑出稳定爆款共性·先解决选题/钩子·上游不通下游无源"}

    # 贯通结论
    if broken:
        chain_verdict = f"链条在「{broken['link']}」断了:{broken['say']}"
    else:
        chain_verdict = (f"链条贯通:做「{(dna.get('top_hashtags') or ['垂直'])[0]}」类内容 → "
                         f"{senti_node['headline']} → {momentum_node['headline']}·"
                         "三环咬合·当前是放大窗口")

    return {
        "nodes": nodes, "broken": broken,
        "chain_verdict": chain_verdict,
        "value": "单看三块各说各话;串成因果链才看出『哪种内容真带来了口碑与势能、哪一环在漏』——这是组合的数据价值",
    }
