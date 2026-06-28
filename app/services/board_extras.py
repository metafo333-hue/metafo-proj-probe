"""元板补全信号 · 把"采了但没接进 board"的数据接进价值阶梯(零/低成本)。

审计(2026-06-28)发现已采集却未在 /board 输出的数据:
  热评TOP    评论 digg_count/is_hot 已采·board 没专门输出热评榜      → 阶梯2诊断
  里程碑     _MILESTONES(粉丝→权益)只在 /analyze 报告·没进阶梯       → 阶梯1描述
  评论聚类   comment_insight LLM聚类只在 /analyze·board 走非LLM兜底   → 阶梯2诊断
  互动操纵   作品矩阵互动比例反常(赞高评藏低)·补强④虚假检测(零成本)  → 阶梯2诊断
⚠️ 真play_count 是黑盒(需批量统计端点·有成本)·刷"播放量"无真play 做不了——本模块不碰。
"""
from __future__ import annotations

import re
import statistics as _S
from typing import Any

# 粉丝里程碑(粉丝数→解锁权益·与 account_report._MILESTONES 对齐)
_MILESTONES: list[tuple[int, str]] = [
    (1_000, "橱窗/评论置顶/私信等基础创作者权益"),
    (5_000, "接商单起步线·品牌方开始关注小账号"),
    (10_000, "万粉心理分水岭·星图接单门槛"),
    (50_000, "稳定商单阶段·单条可谈品牌合作"),
    (100_000, "头部门槛·MCN 主动找上门"),
    (500_000, "大V量级·单粉价值最高时段"),
    (1_000_000, "百万博主·品牌定制·顶级流量"),
]
_QUESTION_RE = re.compile(r"[?？]|怎么|多少|哪里|在哪|能不能|有没有|是不是|可以吗|几点|拿货|价格")


# ── 里程碑(阶梯1 描述)──────────────────────────────────────────────────────────
def milestone(follower: int | None) -> dict[str, Any]:
    f = follower or 0
    passed = [m for m in _MILESTONES if f >= m[0]]
    nxt = next((m for m in _MILESTONES if f < m[0]), None)
    cur = passed[-1] if passed else None
    out = {"follower": f,
           "current": (f"已过 {_fmt(cur[0])}·{cur[1]}" if cur else "未过千粉·冷启期"),
           "passed_count": len(passed)}
    if nxt:
        gap = nxt[0] - f
        out["next"] = {"at": nxt[0], "gap": gap,
                       "pct": round(f / nxt[0] * 100, 1),
                       "unlock": nxt[1],
                       "verdict": f"距 {_fmt(nxt[0])} 还差 {_fmt(gap)}粉"
                                  f"({round(f/nxt[0]*100)}%)·解锁:{nxt[1]}"}
    else:
        out["next"] = None
    return out


def _fmt(n: int) -> str:
    return f"{n/10000:.0f}万" if n >= 10000 else str(n)


# ── 热评 TOP(阶梯2 诊断·观众下一个想看的)─────────────────────────────────────
def hot_comments(comments: list[dict], owner_uid: str | None = None,
                 top_n: int = 5) -> dict[str, Any]:
    cs = []
    for c in (comments or []):
        if "作者" in str(c.get("label_text") or ""):       # 剔创作者自评
            continue
        u = c.get("user") or {}
        if owner_uid and (u.get("sec_uid") == owner_uid):
            continue
        txt = (c.get("text") or "").strip()
        if txt:
            cs.append({"text": txt, "digg": int(c.get("digg_count") or 0),
                       "is_hot": bool(c.get("is_hot")),
                       "stick": bool(c.get("stick_position"))})
    if not cs:
        return {"enough": False, "top": [], "verdict": "无可用评论"}
    cs.sort(key=lambda x: -x["digg"])
    top = cs[:top_n]
    return {"enough": True, "top": top,
            "verdict": f"最高赞评论:「{top[0]['text'][:24]}」({top[0]['digg']}赞)",
            "note": "热评=观众最认同的声音·常是下一个选题/异议信号"}


# ── 评论聚类(阶梯2 诊断·非LLM兜底·零成本)──────────────────────────────────────
def comment_clusters(comments: list[dict], owner_uid: str | None = None,
                     top_n: int = 4) -> dict[str, Any]:
    """按疑问/前缀粗聚类(非LLM·零成本)。LLM 精聚类在 /analyze(comment_insight)。"""
    buckets: dict[str, dict] = {}
    for c in (comments or []):
        if "作者" in str(c.get("label_text") or ""):
            continue
        t = (c.get("text") or "").strip()
        if not t or not _QUESTION_RE.search(t):
            continue
        key = t[:4]                                          # 前缀粗聚(4字·"多少钱一"类同归)
        b = buckets.setdefault(key, {"sample": t, "count": 0, "digg": 0})
        b["count"] += 1
        b["digg"] += int(c.get("digg_count") or 0)
    clusters = sorted(buckets.values(), key=lambda x: (-x["count"], -x["digg"]))[:top_n]
    return {"enough": bool(clusters),
            "clusters": [{"theme": c["sample"][:20], "count": c["count"]} for c in clusters],
            "verdict": (f"评论高频诉求:{('、'.join(c['sample'][:10] for c in clusters[:2]))}"
                        if clusters else "评论无明显聚类诉求"),
            "note": "非LLM前缀粗聚(零成本)·精聚类走 /analyze 的国产LLM"}


# ── 互动操纵异常(阶梯2 诊断·补强④虚假检测·作品矩阵零成本)──────────────────────
def engagement_anomaly(works: list[dict]) -> dict[str, Any]:
    """作品矩阵互动比例反常检测(零成本·无真play→不做刷播放·只做互动结构异常)。

    正常账号:赞↑则评/藏/分享按比例↑。某条赞暴涨但评/藏几乎不动 = 疑刷赞/异常加热。
    """
    ws = [w for w in (works or []) if (w.get("like") or 0) > 0]
    if len(ws) < 6:
        return {"enough": False, "verdict": f"作品 {len(ws)} 条(<6)·异常检测需更多样本"}
    likes = [w["like"] for w in ws]
    med_like = _S.median(likes)
    # 评赞比/藏赞比的中位(正常基线)
    c2l = [(w.get("comment") or 0) / w["like"] for w in ws]
    med_c2l = _S.median(c2l)
    flags = []
    for w in ws:
        # 赞远高于中位(≥3x)但评赞比远低于中位(<1/3)= 疑互动操纵
        if w["like"] >= med_like * 3 and med_c2l > 0 and \
                (w.get("comment") or 0) / w["like"] < med_c2l / 3:
            flags.append({"desc": (w.get("desc") or "")[:18], "like": w["like"],
                          "comment": w.get("comment") or 0})
    n_flag = len(flags)
    if n_flag == 0:
        verdict = "互动结构自然(赞评藏比例一致·无操纵迹象)"
        level = "green"
    elif n_flag <= 1:
        verdict = f"{n_flag} 条赞高但评论异常少(疑加热/刷赞·待观察)"
        level = "yellow"
    else:
        verdict = f"{n_flag} 条互动比例反常(赞暴涨评论不动·疑刷量)"
        level = "red"
    return {"enough": True, "level": level, "verdict": verdict,
            "flagged": flags[:3], "median_like": round(med_like),
            "note": "只查互动结构异常(零成本)·真'刷播放量'需真play(黑盒·未做)"}
