"""扩展信号 · 把「采集了但没展示」的端点全部接进来 + 组合输出(深度分析)。

针对盘点发现的 15 个「采回来却扔了」的端点·逐个按真实字段路径(2026-06-28 force_refresh
实测·非编造)解析,空返回诚实标原因,再做跨端点组合产出新洞察。

字段路径全部 live 实测确认:
  comment_word      .data.data[]{word_seg,value}            官方评论热词(优于自造n-gram)
  related           .data.aweme_list[]{author,statistics}   算法关联视频=真实竞品
  hot_rise          .data.data.objs[]{sentence,hot_score}   上升热点(全网)
  hot_total         .data.data.word_list[]                  实时热搜词(全网)
  hot_challenge     .data.data.objs[]{sentence,video_count} 热门挑战(全网)
  insight_rec       .data[]{category,title,summary}         平台选题洞察
  creator_music     .data.item_list[]{music,hot_involve}    创作者热门配乐
  acc_fans_portrait .data.data.portrait.portrait_data[]     粉丝分布(option维度·语义见下)
空返回(此账号)：video_audience(作品超时)/video_trend(参数不合法code5)/danmaku(无弹幕)/
              creator_challenge(空)。redundant：profile_v4(=web profile)。niche：xv2_*短剧榜。
"""
from __future__ import annotations

from collections import Counter
from typing import Any


def _env(results: dict, ep: str):
    """剥 TikHub 外层信封 → 业务 data(自动下钻二次信封)。"""
    v = results.get(ep)
    if not isinstance(v, dict):
        return v
    d = v.get("data", v)
    if isinstance(d, dict) and "data" in d:   # 二次信封(comment_word/acc_fans/hot_*)
        d = d["data"]
    return d


# ══════════════════════════════════════════════════════════════════════════════
# 解析:15 端点 → 结构化字段(真实路径·空返回诚实标)
# ══════════════════════════════════════════════════════════════════════════════

def parse_extra_signals(results: dict) -> dict[str, Any]:
    out: dict[str, Any] = {"_empty": [], "_redundant": []}

    # 1. 官方评论热词(comment_word.data.data[]{word_seg,value})——优于自造 n-gram
    cw = _env(results, "comment_word")
    if isinstance(cw, list) and cw:
        out["official_comment_words"] = [
            {"word": x.get("word_seg"), "count": x.get("value")}
            for x in cw if x.get("word_seg")][:15]
    else:
        out["_empty"].append(("comment_word", "无评论热词数据"))

    # 2. 算法竞品(related.data.aweme_list[]{author,statistics})——抖音把你和谁归一类
    rel = _env(results, "related")
    aweme_list = rel.get("aweme_list") if isinstance(rel, dict) else None
    if aweme_list:
        comps = {}
        for v in aweme_list:
            a = (v.get("author") or {})
            nick = a.get("nickname")
            if not nick:
                continue
            st = v.get("statistics") or {}
            # 去重·保最高赞那条
            prev = comps.get(nick)
            likes = st.get("digg_count") or 0
            if not prev or likes > prev["top_like"]:
                comps[nick] = {"nickname": nick, "fans": a.get("follower_count"),
                               "top_like": likes, "desc": (v.get("desc") or "")[:20]}
        out["related_competitors"] = sorted(
            comps.values(), key=lambda c: -(c["fans"] or 0))[:8]
    else:
        out["_empty"].append(("related", "无算法关联视频"))

    # 3-5. 大盘热点深化(hot_rise/hot_total/hot_challenge)
    hr = _env(results, "hot_rise")
    rising = hr.get("objs") if isinstance(hr, dict) else None
    if rising:
        out["env_rising"] = [{"topic": o.get("sentence"), "heat": o.get("hot_score")}
                             for o in rising if o.get("sentence")][:10]
    ht = _env(results, "hot_total")
    words = ht.get("word_list") if isinstance(ht, dict) else None
    if words:
        out["env_hot_search"] = [
            {"word": (w.get("word") or w.get("sentence") or w.get("hotlist_param")),
             "heat": w.get("hot_value")} for w in words][:12]
    hc = _env(results, "hot_challenge")
    chs = hc.get("objs") if isinstance(hc, dict) else None
    if chs:
        out["env_challenges"] = [
            {"challenge": o.get("sentence"), "video_count": o.get("video_count"),
             "heat": o.get("hot_score")} for o in chs if o.get("sentence")][:10]

    # 6. 平台选题洞察(insight_rec.data[]{category,title})
    ir = _env(results, "insight_rec")
    if isinstance(ir, list) and ir:
        out["topic_insights"] = [{"category": x.get("category"), "title": x.get("title")}
                                 for x in ir if x.get("title")][:12]
        out["topic_insight_cats"] = [c for c, _ in
                                     Counter(x.get("category") for x in ir
                                             if x.get("category")).most_common(6)]

    # 7. 热门配乐(creator_music.data.item_list[]{music,hot_involve_ratio})
    cm = _env(results, "creator_music")
    items = cm.get("item_list") if isinstance(cm, dict) else None
    if items:
        out["hot_music"] = [
            {"title": (it.get("music") or {}).get("title"),
             "heat_ratio": it.get("hot_involve_ratio")}
            for it in items if (it.get("music") or {}).get("title")][:8]

    # 8. 粉丝分布(acc_fans_portrait.data.data.portrait.portrait_data)
    #    ⚠️ option 维度语义 TikHub 未在返回里明确给出·数值为占比·诚实标注不强行命名维度。
    afp = _env(results, "acc_fans_portrait")
    portrait = (afp or {}).get("portrait") if isinstance(afp, dict) else None
    pdata = portrait.get("portrait_data") if isinstance(portrait, dict) else None
    if pdata:
        top = sorted(pdata, key=lambda x: -(x.get("value") or 0))[:5]
        out["fan_distribution"] = {
            "option": (afp or {}).get("option"),
            "dist": [{"name": x.get("name"), "pct": round((x.get("value") or 0) * 100, 1)}
                     for x in top],
            "note": "粉丝分布(billboard·维度=option·TikHub未明确返回维度名·"
                    "数值为占比·按数值区间疑似'粉丝量级/消费段'·待文档确认)",
        }

    # 空返回端点(诚实记录·非编造有数据)
    for ep, reason in [("video_audience", "作品超过可查看时间(热榜画像仅对新热门作品有)"),
                       ("video_trend", "返回 code5 参数不合法(端点待修)"),
                       ("danmaku", "此账号视频无弹幕"),
                       ("creator_challenge", "空返回")]:
        v = results.get(ep)
        d = _env(results, ep)
        empty = (not d) or (isinstance(d, dict) and not any(
            isinstance(x, list) and x for x in d.values()))
        if v is not None and empty:
            out["_empty"].append((ep, reason))
    out["_redundant"] = [("profile_v4", "=web handler_user_profile·重复·不单列"),
                         ("xv2_playlet_rank", "短剧作者榜·非通用账号场景"),
                         ("xv2_ranking_catalog", "星图V2榜单目录·非通用场景")]
    return out


# ══════════════════════════════════════════════════════════════════════════════
# 组合分析:跨端点组合出新洞察(深度)
# ══════════════════════════════════════════════════════════════════════════════

# B端采购/咨询意向词(评论热词命中=潜在线索信号)
_INTENT_WORDS = ("拿货", "批发", "代理", "多少", "价格", "怎么", "联系", "购买",
                 "哪里", "包邮", "发货", "加盟", "供货", "进货", "厂家", "合作")


def audience_deep(account: dict) -> dict[str, Any]:
    """受众洞察组合:官方评论热词 + 粉丝分布 + 评论地域 → 受众是谁 + 采购意向。"""
    ex = account.get("extra_signals") or {}
    words = ex.get("official_comment_words") or []
    intent_hits = [w["word"] for w in words
                   if any(k in (w["word"] or "") for k in _INTENT_WORDS)]
    fd = ex.get("fan_distribution")
    cd = account.get("comment_deep") or {}
    words_str = "、".join(f"{w['word']}({w['count']})" for w in words[:6])
    fd_str = ("、".join(f"{d['name']}({d['pct']}%)" for d in fd["dist"][:3])
              if fd else "")
    return {
        "conclusion": ("官方评论热词 TOP:" +
                       "、".join(w["word"] for w in words[:5]) if words
                       else "无官方评论热词"),
        "breakdown": [
            f"评论热词:{words_str}" if words else "评论热词:无",
            f"粉丝地域集中度:最高省份占比 {round((cd.get('ip_concentration') or 0)*100)}%"
            if cd.get("ip_concentration") else "粉丝地域:数据不足",
            (fd["note"] + " → " + fd_str) if fd else "粉丝分布:无",
        ],
        "intent_signal": intent_hits,
        "implication": (
            f"⚠️ 评论里出现采购/咨询意向词「{'、'.join(intent_hits)}」="
            "潜在 B 端线索·应主动私信承接(这是变现入口)" if intent_hits
            else "评论热词无明显采购意向·先做内容拉互动"),
    }


def competitor_radar(account: dict) -> dict[str, Any]:
    """竞品雷达组合:算法关联视频作者(related) + 粉丝同关账号(fans_interest)
    → 抖音眼里你的真实竞品圈 + 你在其中的身位。"""
    ex = account.get("extra_signals") or {}
    algo = ex.get("related_competitors") or []
    fans_int = account.get("fans_interest_accounts") or []
    my_fans = account.get("follower") or 0
    # 合并两路竞品·去重
    pool = {}
    for c in algo:
        pool[c["nickname"]] = {"name": c["nickname"], "fans": c.get("fans"),
                               "via": "算法关联"}
    for c in fans_int:
        nm = c.get("name")
        if nm and nm not in pool:
            pool[nm] = {"name": nm, "fans": c.get("fans"), "via": "粉丝同关"}
    comps = sorted(pool.values(), key=lambda c: -(c["fans"] or 0))
    # 诚实:只对「有粉丝数」的竞品排位·related 常不返回 follower_count→未知不当 0
    known = [c for c in comps if c.get("fans")]
    bigger = [c for c in known if c["fans"] > my_fans]
    if comps and known:
        rank_txt = (f"·在有粉丝数的 {len(known)} 个里你超过 {len(known)-len(bigger)} 个")
    elif comps:
        rank_txt = "·竞品粉丝数未返回·只识别出是谁·暂无法排位(诚实)"
    else:
        rank_txt = ""
    return {
        "conclusion": (f"抖音关联到 {len(comps)} 个同类账号{rank_txt}" if comps
                       else "无算法竞品数据"),
        "competitors": comps[:8],
        "breakdown": [
            f"算法关联竞品:{len(algo)} 个(抖音把你的视频和他们归一类)",
            f"粉丝同关账号:{len(fans_int)} 个(你粉丝还关注谁)",
            (f"你的身位:{my_fans}粉·" + ("领先多数" if len(bigger) < len(known) / 2
                                        else "追赶中") if known
             else f"你的身位:{my_fans}粉·竞品粉丝数未知·无法精确排位") if comps else "",
        ],
        "implication": ("这些是抖音眼里和你同类的真实账号·可拆解他们的选题/钩子做对标"
                        if comps else "算法竞品数据未取到·建议补 related/fans_interest 种子"),
    }


def env_hot_deep(account: dict) -> dict[str, Any]:
    """大盘热点深化组合:上升热点+实时热搜+热门挑战+平台选题洞察 → 全景环境情报。"""
    ex = account.get("extra_signals") or {}
    rising = ex.get("env_rising") or []
    search = ex.get("env_hot_search") or []
    chs = ex.get("env_challenges") or []
    insights = ex.get("topic_insights") or []
    cats = ex.get("topic_insight_cats") or []
    return {
        "conclusion": (f"大盘情报:{len(rising)}上升热点/{len(search)}实时热搜/"
                       f"{len(chs)}热门挑战/{len(insights)}平台选题"),
        "rising_top": [r["topic"] for r in rising[:5]],
        "challenges_top": [c["challenge"] for c in chs[:5]],
        "insight_cats": cats,
        "breakdown": [
            f"上升热点:{'、'.join(r['topic'] for r in rising[:4])}" if rising else "上升热点:无",
            f"热门挑战:{'、'.join(c['challenge'] for c in chs[:3])}" if chs else "热门挑战:无",
            f"平台选题类目:{'、'.join(cats[:5])}" if cats else "平台选题:无",
        ],
        "implication": "以上为全网大盘(非你赛道细分)·蹭热点须标签内·跨标签蹭会乱垂直度",
    }
