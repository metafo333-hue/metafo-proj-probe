"""内容 DNA · 作品矩阵组合分析(无星图也能跑·所有账号通用)。

针对「TikHub 星图数据缺失→分析单调」的根因:把已采集但未充分利用的**作品矩阵**
(每条视频的 desc/话题/时长/发布时间/互动)做跨条组合,挖出单条看不出的规律,
直接产出「下条怎么拍」的具体处方。

组合维度(单字段无结论·跨 N 条作品才出洞察):
  · 最优发布时段   create_time × engagement  → 什么时候发
  · 最优时长区间   duration × engagement     → 拍多长
  · 爆款选题规律   top视频 desc/hashtag 共性 → 拍什么题
  · 标题钩子规律   top视频开头模式           → 怎么起标题
  · 带货 vs 普通   has_anchor 互动差         → 该不该挂车
  · 话题效率       hashtag × engagement      → 用哪些话题
  · 评论选题池     评论高频疑问词            → 观众想看啥

engagement 一律用 like(点赞)作代理(play_count 需逐条统计端点·成本高),
诚实标注 proxy;与诊断卡 play_is_proxy 口径一致。
"""
from __future__ import annotations

import re
import statistics as _S
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any

_HASHTAG_RE = re.compile(r"#([^#\s]{1,20})")
# 口语虚词/通用词停用集(挖选题关键词时剔除)
_STOP = frozenset(
    "的 了 是 我 你 他 她 们 也 都 在 有 和 与 就 不 这 那 个 啊 吧 呢 吗 哦 嗯 "
    "什么 怎么 这个 那个 真的 一个 可以 没有 就是 已经 还是 但是 因为 所以 大家 "
    "我们 你们 一定 这样 那样 然后 还有 不是 这些 一些".split())


def _eng(w: dict) -> int:
    """单条互动代理值(点赞为主·加权评论/收藏)。"""
    return int((w.get("like") or 0) + (w.get("comment") or 0) * 2 + (w.get("collect") or 0) * 3)


def _hour(ts) -> int | None:
    try:
        return datetime.fromtimestamp(ts).hour
    except Exception:  # noqa: BLE001
        return None


# ── 最优发布时段 ──────────────────────────────────────────────────────────────
_SLOTS = [("清晨 5-8", 5, 9), ("上午 9-12", 9, 12), ("午间 12-14", 12, 14),
          ("下午 14-18", 14, 18), ("晚间 18-22", 18, 22), ("深夜 22-5", 22, 29)]


def best_posting_time(works: list[dict]) -> dict[str, Any]:
    by_slot: dict[str, list[int]] = defaultdict(list)
    for w in works:
        h = _hour(w.get("create_time"))
        if h is None:
            continue
        hh = h if h >= 5 else h + 24
        for name, lo, hi in _SLOTS:
            if lo <= hh < hi:
                by_slot[name].append(_eng(w))
                break
    if not by_slot:
        return {"verdict": "发布时间数据不足", "slots": [], "best": None, "proxy": True}
    rows = [{"slot": s, "n": len(v), "avg_eng": round(_S.mean(v))}
            for s, v in by_slot.items() if v]
    rows.sort(key=lambda r: -r["avg_eng"])
    best = rows[0]
    worst = rows[-1]
    lift = (round(best["avg_eng"] / worst["avg_eng"], 1)
            if worst["avg_eng"] else None)
    # 置信度:最优时段样本太少(<3)→ 低置信·只作参考不作结论(防小样本噪音当实测)
    conf = "high" if best["n"] >= 5 else "mid" if best["n"] >= 3 else "low"
    verdict = f"{best['slot']} 时段相对最好(均互动 {best['avg_eng']})"
    if conf == "low":
        verdict += f"·⚠️仅 {best['n']} 条样本·低置信·需更多数据确认"
    elif lift and lift >= 1.5 and len(rows) >= 2:
        verdict += f"·比最差时段高 {lift}x"
    return {"verdict": verdict, "slots": rows, "best": best["slot"],
            "lift": lift if conf != "low" else None, "conf": conf, "proxy": True}


# ── 最优时长区间 ──────────────────────────────────────────────────────────────
_DUR_BUCKETS = [("≤15s", 0, 15), ("15-30s", 15, 30), ("30-45s", 30, 45),
                ("45-60s", 45, 60), ("60-90s", 60, 90), (">90s", 90, 99999)]


def best_duration(works: list[dict]) -> dict[str, Any]:
    by_b: dict[str, list[int]] = defaultdict(list)
    for w in works:
        dur = (w.get("duration_ms") or 0) / 1000
        if dur <= 0:
            continue
        for name, lo, hi in _DUR_BUCKETS:
            if lo <= dur < hi:
                by_b[name].append(_eng(w))
                break
    if not by_b:
        return {"verdict": "时长数据不足", "buckets": [], "best": None, "proxy": True}
    rows = [{"bucket": b, "n": len(v), "avg_eng": round(_S.mean(v))}
            for b, v in by_b.items() if v]
    rows.sort(key=lambda r: -r["avg_eng"])
    best = rows[0]
    conf = "high" if best["n"] >= 5 else "mid" if best["n"] >= 3 else "low"
    verdict = f"{best['bucket']} 时长互动相对最高(均 {best['avg_eng']})"
    if conf == "low":
        verdict += f"·⚠️仅 {best['n']} 条·低置信"
    return {"verdict": verdict, "buckets": rows, "best": best["bucket"],
            "conf": conf, "proxy": True}


# ── 爆款选题规律(top 视频 desc/hashtag 共性)──────────────────────────────────
def _keywords(text: str, n: int = 2) -> list[str]:
    """从一段中文 desc 抽 n-gram 关键词(去 hashtag/停用词/标点)。"""
    clean = _HASHTAG_RE.sub(" ", text)
    clean = re.sub(r"[^一-鿿]", " ", clean)  # 只留中文
    grams: list[str] = []
    for seg in clean.split():
        for i in range(len(seg) - n + 1):
            g = seg[i:i + n]
            if g not in _STOP and not any(ch in _STOP for ch in [g]):
                grams.append(g)
    return grams


def winning_topics(works: list[dict], top_n: int = 5) -> dict[str, Any]:
    if len(works) < 3:
        return {"verdict": "作品数不足·选题规律待积累", "top_keywords": [],
                "top_hashtags": [], "exemplar": None}
    ranked = sorted(works, key=_eng, reverse=True)
    top = ranked[:max(top_n, len(ranked) // 3)]
    bottom = ranked[len(ranked) // 2:]
    # 高赞组关键词/话题 vs 低赞组·算"差异化"关键词
    top_kw = Counter()
    bot_kw = Counter()
    top_tags = Counter()
    for w in top:
        for g in _keywords(w.get("desc", "")):
            top_kw[g] += 1
        for tag in _HASHTAG_RE.findall(w.get("desc", "")):
            top_tags[tag] += 1
    for w in bottom:
        for g in _keywords(w.get("desc", "")):
            bot_kw[g] += 1
    # 在高赞组更突出的词(简单差异)
    diff = [(k, c) for k, c in top_kw.most_common(20) if c >= 2 and top_kw[k] > bot_kw.get(k, 0)]
    # 爆款样板取「最高赞」(用户在抖音看到的就是赞数·非合成 eng·避免给看不懂的数)
    exemplar = max(works, key=lambda w: (w.get("like") or 0))
    # 干净话题(hashtag·人工标)优先作 verdict·n-gram 关键词作补充。
    clean_terms = [t for t, _ in top_tags.most_common(4)] or [k for k, _ in diff[:4]]
    return {
        "verdict": f"爆款共性:{('、'.join(clean_terms) or '暂无显著共性')}",
        "top_keywords": [k for k, _ in diff[:6]],
        "top_hashtags": [t for t, _ in top_tags.most_common(6)],
        "exemplar": {"desc": exemplar.get("desc", "")[:40],
                     "like": exemplar.get("like")},   # 只给真实赞数·不给合成 eng
    }


# ── 带货 vs 普通(挂车互动对比·该不该挂车)──────────────────────────────────────
def anchor_lift(works: list[dict]) -> dict[str, Any]:
    anc = [_eng(w) for w in works if w.get("has_anchor")]
    non = [_eng(w) for w in works if not w.get("has_anchor")]
    if not anc:
        return {"verdict": "尚无挂车视频·当前纯内容曝光", "has_commerce": False,
                "anchor_avg": None, "non_avg": round(_S.mean(non)) if non else None}
    a_avg = round(_S.mean(anc))
    n_avg = round(_S.mean(non)) if non else None
    if n_avg:
        ratio = round(a_avg / n_avg, 2)
        v = (f"挂车视频互动是普通的 {ratio}x" +
             ("·挂车不掉量可放心带货" if ratio >= 0.8 else "·挂车明显掉量·克制带货频率"))
    else:
        v = "全为挂车视频"
        ratio = None
    return {"verdict": v, "has_commerce": True, "anchor_avg": a_avg,
            "non_avg": n_avg, "ratio": ratio}


# ── 话题效率(hashtag × engagement)────────────────────────────────────────────
def hashtag_performance(works: list[dict], top_n: int = 6) -> dict[str, Any]:
    by_tag: dict[str, list[int]] = defaultdict(list)
    for w in works:
        e = _eng(w)
        for tag in set(_HASHTAG_RE.findall(w.get("desc", ""))):
            by_tag[tag].append(e)
    rows = [{"tag": t, "n": len(v), "avg_eng": round(_S.mean(v))}
            for t, v in by_tag.items() if len(v) >= 2]
    rows.sort(key=lambda r: -r["avg_eng"])
    return {"top": rows[:top_n],
            "verdict": (f"高效话题:#{rows[0]['tag']}(均 {rows[0]['avg_eng']})"
                        if rows else "话题样本不足")}


# ── 评论选题池(高频疑问/意图词→下条选题)──────────────────────────────────────
# 真买家疑问信号(需含其一·且非创作者公告)
_QUESTION_HINT = ("多少钱", "怎么买", "哪里买", "能不能", "怎样买", "有没有货",
                  "贵不贵", "包邮", "怎么发货", "多少一", "在哪买", "怎么联系",
                  "可以买", "哪里有", "咋卖", "啥价")
# 创作者公告/自动回复/引流话术(命中即剔除·非观众真实提问)
_ANNOUNCE = ("请看", "私信", "主页", "点击", "下方", "链接", "小黄车", "橱窗",
             "联系方式", "自动回复", "客服", "复制", "抖音号", "微信", "置顶",
             "信息回复", "看简介", "戳", "↓", "进店", "下单戳")


def _is_creator(c: dict, owner_uid: str | None) -> bool:
    """是否创作者自己的评论(置顶/回复)。"""
    u = c.get("user") or {}
    uid = u.get("sec_uid") or u.get("uid") or c.get("sec_uid")
    if owner_uid and uid and uid == owner_uid:
        return True
    # 兜底:label_text 常标"作者"
    return "作者" in str(c.get("label_text") or "")


def comment_topic_pool(comments: list[dict], top_n: int = 8,
                       owner_uid: str | None = None) -> dict[str, Any]:
    if not comments:
        return {"verdict": "评论数据不足·拿不到选题信号", "hot_questions": [],
                "intent_words": [], "n_questions": 0}
    intent = Counter()
    questions = []
    for c in comments:
        if _is_creator(c, owner_uid):          # 剔除创作者自评/公告
            continue
        txt = (c.get("text") or "").strip()
        if not txt or len(txt) > 30:
            continue
        if any(a in txt for a in _ANNOUNCE):   # 剔除引流话术/自动回复
            continue
        # 必须是真买家疑问(含疑问信号 或 以问号收尾)
        is_q = any(h in txt for h in _QUESTION_HINT) or txt.rstrip().endswith(("?", "？"))
        if is_q:
            questions.append((txt, int(c.get("digg_count") or 0)))
        for g in _keywords(txt):
            intent[g] += 1
    questions.sort(key=lambda x: -x[1])
    # 诚实:无真实疑问就标拿不到·不拿噪音充数
    verdict = (f"观众最关心:{questions[0][0]}" if questions
               else "评论里暂无明确购买/咨询提问(拿不到选题信号·非编造)")
    return {
        "verdict": verdict,
        "hot_questions": [q for q, _ in questions[:top_n]],
        "intent_words": [w for w, _ in intent.most_common(8) if w not in _STOP],
        "n_questions": len(questions),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 聚合 + 下条怎么拍处方
# ══════════════════════════════════════════════════════════════════════════════

def analyze_content_dna(works: list[dict],
                        comments: list[dict] | None = None,
                        owner_uid: str | None = None) -> dict[str, Any]:
    """作品矩阵全维组合分析(无星图也满血)。owner_uid 用于剔除创作者自评。"""
    comments = comments or []
    dna = {
        "n_works": len(works),
        "best_time": best_posting_time(works),
        "best_duration": best_duration(works),
        "topics": winning_topics(works),
        "anchor": anchor_lift(works),
        "hashtags": hashtag_performance(works),
        "comment_pool": comment_topic_pool(comments, owner_uid=owner_uid),
        "proxy_note": "互动用点赞代理(play_count 需逐条统计端点·成本高·未拉)",
    }
    dna["next_video_rx"] = _next_video_prescription(dna)
    return dna


def _next_video_prescription(dna: dict) -> dict[str, Any]:
    """把各维组合收口成 1 条「下条怎么拍」的具体处方(可执行)。"""
    if dna["n_works"] < 3:
        return {"summary": "作品样本不足(<3 条)·先积累再出规律", "steps": []}
    bt = dna["best_time"]
    bd = dna["best_duration"]
    tp = dna["topics"]
    pool = dna["comment_pool"]
    steps = []
    if bt.get("best"):
        if bt.get("conf") == "low":
            s = f"发布时段:目前看 {bt['best']} 略好·但样本少·先按此试再用数据校准"
        elif bt.get("lift") and bt["lift"] >= 1.5:
            s = f"发布时段:选 {bt['best']}(实测比最差时段高 {bt['lift']}x)"
        else:
            s = f"发布时段:选 {bt['best']}"
        steps.append(s)
    if bd.get("best"):
        tail = "(样本少·参考)" if bd.get("conf") == "low" else "(你的高互动区间)"
        steps.append(f"视频时长:控制在 {bd['best']}{tail}")
    # 选题方向优先用干净的 hashtag(人工标·无碎词)·n-gram 关键词作兜底。
    topic_terms = tp.get("top_hashtags") or tp.get("top_keywords")
    if topic_terms:
        steps.append(f"选题方向:延续爆款共性「{'、'.join(topic_terms[:3])}」")
    if tp.get("exemplar") and tp["exemplar"].get("like"):
        steps.append(f"对标自己的爆款:「{tp['exemplar']['desc']}」(最高赞 {tp['exemplar']['like']})")
    if pool.get("hot_questions"):
        steps.append(f"回应观众关心:做一条专门答「{pool['hot_questions'][0]}」")
    if not dna["anchor"].get("has_commerce"):
        steps.append("暂不挂车:当前流量基础下先做内容曝光·把单条互动做起来再谈带货")
    summary = "下条怎么拍 = " + " + ".join(
        x.split(":")[1].split("(")[0] for x in steps[:3] if ":" in x)
    return {"summary": summary, "steps": steps}


# ── Markdown 渲染(给报告段/单条层)─────────────────────────────────────────────
def render_dna_md(dna: dict) -> str:
    L = ["### 内容 DNA · 作品矩阵规律(无星图也能挖)"]
    rx = dna.get("next_video_rx") or {}
    if rx.get("steps"):
        L.append("**📌 下条怎么拍:**")
        for s in rx["steps"]:
            L.append(f"- {s}")
    L.append("")
    L.append(f"- ⏰ {dna['best_time'].get('verdict')}")
    L.append(f"- ⏱️ {dna['best_duration'].get('verdict')}")
    L.append(f"- 🎯 {dna['topics'].get('verdict')}")
    L.append(f"- #️⃣ {dna['hashtags'].get('verdict')}")
    L.append(f"- 🛒 {dna['anchor'].get('verdict')}")
    L.append(f"- 💬 {dna['comment_pool'].get('verdict')}")
    L.append(f"\n_{dna.get('proxy_note')}_")
    return "\n".join(L)
