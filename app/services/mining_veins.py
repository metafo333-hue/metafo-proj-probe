"""数据矿脉 ②③ · 纯数据层深挖(零额外采集成本)。

承元矿方法论 30 落地层"未挖矿脉"。**只做数据层**(视频元数据 + 评论数据的组合),
视觉/视听内容分析归 av_sixlayer(别处)·本模块不碰像素。

矿脉② 内容归因(content_attribution · A×A' 控制变量):
  哪个**数据因子**(时长/话题/挂载/时段)驱动了互动差异?单因子隔离分组·算组间落差·
  排出"最该调的旋钮"。区别于 content_dna 给"最优值"——本模块给"哪个维度最重要"。

矿脉③ 口碑演化(sentiment_evolution · C×D 时间线):
  评论按 create_time 切早/晚两段·看采购意向词密度/情感/点赞的演化 → 口碑升温还是降温。
  B端尤其值钱:近期采购意向上升=视频在持续产线索(先行信号)。
  ⚠️ 数据层范围:本视频评论时间线(评论已采·零成本);账号级跨作品口碑需逐视频评论(有成本·不做)。

eng = like + comment*2 + collect*3(与 content_dna/time_series 一致·点赞代理)。
"""
from __future__ import annotations

import re
import statistics as _S
from datetime import datetime
from typing import Any

_HASHTAG_RE = re.compile(r"#([^#\s]{1,20})")

# B端采购/咨询意向词(承 extra_signals)
_INTENT = ("拿货", "批发", "代理", "多少", "价格", "怎么", "联系", "购买", "哪里",
           "包邮", "发货", "加盟", "供货", "进货", "厂家", "合作", "咋卖", "咨询")
# 极简情感词典(正/负·数据层粗判·非NLP)
_POS = ("好", "赞", "支持", "喜欢", "加油", "厉害", "棒", "真", "靠谱", "学到", "感谢")
_NEG = ("假", "骗", "贵", "差", "垃圾", "套路", "水", "无语", "退", "坑")


def _eng(w: dict) -> int:
    return int((w.get("like") or 0) + (w.get("comment") or 0) * 2 + (w.get("collect") or 0) * 3)


def _hour_slot(ts) -> str | None:
    try:
        h = datetime.fromtimestamp(ts).hour
    except Exception:  # noqa: BLE001
        return None
    for name, lo, hi in (("清晨5-9", 5, 9), ("上午9-12", 9, 12), ("午间12-14", 12, 14),
                         ("下午14-18", 14, 18), ("晚间18-22", 18, 22), ("深夜22-5", 22, 29)):
        hh = h if h >= 5 else h + 24
        if lo <= hh < hi:
            return name
    return None


# ── 矿脉② 内容归因:哪个数据因子最驱动互动 ────────────────────────────────────
def content_attribution(works: list[dict]) -> dict[str, Any]:
    works = [w for w in (works or []) if w.get("create_time")]
    if len(works) < 6:
        return {"enough": False,
                "verdict": f"作品 {len(works)} 条(<6)·归因需更多样本", "factors": []}

    def _bucket_duration(w):
        d = (w.get("duration_ms") or 0) / 1000
        if d <= 0:
            return None
        for name, lo, hi in (("≤15s", 0, 15), ("15-30s", 15, 30), ("30-45s", 30, 45),
                             ("45-60s", 45, 60), ("60-90s", 60, 90), (">90s", 90, 1e9)):
            if lo <= d < hi:
                return name
        return None

    def _primary_tag(w):
        tags = _HASHTAG_RE.findall(w.get("desc", ""))
        return tags[0] if tags else None

    # 每个因子:works → {因子值: [eng...]}·算组间落差(max组均/min组均)
    factor_defs = {
        "时长": _bucket_duration,
        "话题": _primary_tag,
        "挂载": lambda w: "有挂车" if w.get("has_anchor") else "无挂车",
        "发布时段": lambda w: _hour_slot(w.get("create_time")),
    }
    results = []
    for fname, fn in factor_defs.items():
        groups: dict[str, list[int]] = {}
        for w in works:
            v = fn(w)
            if v is None:
                continue
            groups.setdefault(v, []).append(_eng(w))
        # 只保留 ≥2 样本的组(防单条噪音)·须 ≥2 组才有对比
        groups = {k: v for k, v in groups.items() if len(v) >= 2}
        if len(groups) < 2:
            continue
        means = {k: _S.mean(v) for k, v in groups.items()}
        best = max(means, key=means.get)
        worst = min(means, key=means.get)
        if means[worst] <= 0:
            continue
        spread = round(means[best] / means[worst], 2)
        results.append({
            "factor": fname, "spread": spread,
            "best": best, "best_eng": round(means[best]),
            "worst": worst, "worst_eng": round(means[worst]),
            "n_groups": len(groups),
            "detail": f"{fname}={best} 均互动 {round(means[best])}·"
                      f"={worst} 仅 {round(means[worst])}·差 {spread}x",
        })
    # 落差越大=越驱动·排序
    results.sort(key=lambda r: -r["spread"])
    top = results[0] if results else None
    return {
        "enough": True, "factors": results,
        "top_driver": top,
        "verdict": (f"互动差异主要由「{top['factor']}」驱动:{top['detail']}" if top
                    else "各数据因子对互动影响相近·无突出驱动"),
        "implication": (f"优先调「{top['factor']}」:多做 {top['best']}(互动比 {top['worst']} 高 {top['spread']}x)"
                        if top and top["spread"] >= 1.5 else
                        "数据因子未现强驱动·内容质量/选题本身可能是主因(看视听分析)"),
        "note": "单因子隔离·控变量近似(组间≥2样本)·样本越多越准",
    }


# ── 矿脉③ 口碑演化:本视频评论时间线的意图/情感趋势 ──────────────────────────────
def sentiment_evolution(comments: list[dict]) -> dict[str, Any]:
    cs = [c for c in (comments or []) if c.get("create_time") and (c.get("text") or "").strip()]
    cs.sort(key=lambda c: c["create_time"])
    n = len(cs)
    if n < 6:
        return {"enough": False,
                "verdict": f"带时间评论 {n} 条(<6)·口碑演化需更多评论"}
    k = max(2, n // 3)
    early, late = cs[:k], cs[-k:]

    def _metrics(seg):
        intent = sum(1 for c in seg if any(w in (c.get("text") or "") for w in _INTENT))
        pos = sum(1 for c in seg if any(w in (c.get("text") or "") for w in _POS))
        neg = sum(1 for c in seg if any(w in (c.get("text") or "") for w in _NEG))
        digg = _S.mean(int(c.get("digg_count") or 0) for c in seg)
        m = len(seg)
        return {"intent_rate": round(intent / m, 2), "pos_rate": round(pos / m, 2),
                "neg_rate": round(neg / m, 2), "avg_digg": round(digg, 1)}
    e, l = _metrics(early), _metrics(late)
    intent_d = round(l["intent_rate"] - e["intent_rate"], 2)
    sent_d = round((l["pos_rate"] - l["neg_rate"]) - (e["pos_rate"] - e["neg_rate"]), 2)

    # 口碑判定(情感净值 + 意向)
    if sent_d > 0.1 or intent_d > 0.1:
        verdict = "口碑升温"
    elif sent_d < -0.1 or l["neg_rate"] > 0.3:
        verdict = "口碑降温"
    else:
        verdict = "口碑稳定"
    # 采购意向趋势(B端线索先行信号)
    if intent_d > 0.05:
        intent_trend = f"采购/咨询意向上升(早{e['intent_rate']}→近{l['intent_rate']})·视频在持续产线索"
    elif intent_d < -0.05:
        intent_trend = f"采购意向下降(早{e['intent_rate']}→近{l['intent_rate']})·热度过了"
    else:
        intent_trend = f"采购意向平稳({l['intent_rate']})"

    return {
        "enough": True, "verdict": verdict,
        "early": e, "late": l,
        "intent_delta": intent_d, "sentiment_delta": sent_d,
        "intent_trend": intent_trend,
        "span": (f"{datetime.fromtimestamp(cs[0]['create_time']).strftime('%m-%d')}→"
                 f"{datetime.fromtimestamp(cs[-1]['create_time']).strftime('%m-%d')}"),
        "implication": (
            "近期评论采购意向在升=这条视频还在产线索·值得追加私域承接/置顶引导" if intent_d > 0.05
            else "口碑降温/出现负面·查近期评论是否有未回的质疑(评论区是信任战场)"
            if verdict == "口碑降温" else "口碑平稳·按节奏运营"),
        "note": "本视频评论时间线(零成本)·账号级跨作品口碑需逐视频评论(有成本·未做)",
    }
