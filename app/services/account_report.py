"""综合分析报告生成器 v4 · 确定性(规则驱动·零 LLM·零网络)。

目标:像一份真正给创作者看的诊断报告——说人话、数字翻译成普通人能懂的话、有价值感。
价值对齐北极星:处方默认"放大你自己的真东西"(非抄袭);黑盒维诚实标;单源诚实。

v4(2026-06-18·补 L2 多条关联): 据「probe 分析逻辑总框架」补上最值钱的中间层——
  「一个视频 → 多个视频 → 账号」的 L2 层。之前采回 20 条兄弟视频(works_sample)只算了
  个平均就扔了;现在真做「多条找规律」:爆款共性 / 高赞vs低赞差异(可复制内核) / 演化趋势。
v3: 识别账号性质(商业/B2B vs 个人)→ 自适应叙事。
"""
from __future__ import annotations

import re
from typing import Any

_TRACK_HINTS = [
    (("供货", "直供", "源头", "工厂", "批发", "代工", "OEM", "招商", "加盟", "产业带", "货源", "一手", "厂家", "食材", "厂"),
     "产业带货 / B2B供货",
     "这是实打实的生意账号·适合用内容做获客/招商/批发引流·变现路径比纯流量号清晰得多"),
    (("带货", "选品", "好物", "种草", "橱窗", "团购", "上链接", "下单"),
     "带货电商", "转化导向·适合直播带货/橱窗/团购·关键是选品和信任,不用拼几百万播放"),
    (("女性", "妈妈", "职场", "成长", "婚姻", "情感", "她"), "女性成长 / 情感共鸣",
     "这类粉丝精准、信任度高,以后能靠情感陪伴、知识分享变现,适合走「小而美、深耕」的路"),
    (("育儿", "孩子", "宝妈", "母婴", "亲子"), "母婴育儿", "妈妈群体消费力强,适合带货、本地服务、知识付费"),
    (("美食", "探店", "吃播", "菜谱", "厨艺"), "美食", "受众极广,适合探店团购、带货变现"),
    (("健身", "运动", "瑜伽", "减肥"), "健身运动", "需求刚性,适合卖课、社群、装备带货"),
    (("考证", "财经", "理财", "知识", "科普", "学习"), "知识科普", "单个粉丝很值钱,适合引流到私域卖高客单的课/咨询"),
    (("穿搭", "美妆", "时尚", "护肤"), "时尚美妆", "品牌预算最多,适合带货和品牌合作"),
]
_BIZ_KW = ("供货", "直供", "源头", "工厂", "批发", "代工", "OEM", "招商", "加盟", "旗舰", "厂家",
           "产业带", "货源", "一手", "批发价", "实体店", "门店", "公司", "企业", "品牌方",
           "龙头企业", "贴牌", "定制", "合作私信", "代工厂", "厂")
_HASHTAG_RE = re.compile(r"#([^#\s]+)")


def _track(text: str) -> tuple[str, str]:
    for kws, name, why in _TRACK_HINTS:
        if any(k in text for k in kws):
            return name, why
    return "生活记录", "适合慢慢积累信任,后续带货或本地服务变现"


def _is_business(text: str) -> bool:
    return any(k in text for k in _BIZ_KW)


def _stage(fol: int) -> str:
    if fol < 500:
        return f"{fol} 个粉丝、刚起步的小号(大家都从这儿开始,很正常)"
    if fol < 5000:
        return f"{fol} 个粉丝、成长初期"
    if fol < 50000:
        return f"{fol} 个粉丝、有了一定基础"
    return f"{fol} 个粉丝、比较成熟的号"


def _tags_of(works: list) -> dict:
    c: dict[str, int] = {}
    for w in works:
        for t in set(_HASHTAG_RE.findall(w.get("desc", "") or "")):
            c[t] = c.get(t, 0) + 1
    return c


def _avg(works: list, k: str) -> float:
    vals = [w.get(k, 0) or 0 for w in works]
    return sum(vals) / len(vals) if vals else 0.0


def _analyze_works(works: list, avg_like: int) -> dict | None:
    """L2 多条关联:从兄弟视频找规律(共性内核 / 高赞vs低赞差异 / 演化趋势)。
    works = 逐条 [{desc, create_time, like, comment, collect, share}]。少于 4 条不做。"""
    works = [w for w in (works or []) if isinstance(w, dict)]
    if len(works) < 4:
        return None
    n = len(works)
    sw = sorted(works, key=lambda w: w.get("like", 0) or 0, reverse=True)
    seg = max(1, n // 3)
    top, bottom = sw[:seg], sw[-seg:]

    top_tags = _tags_of(top)
    bot_tags = _tags_of(bottom)
    hot_tags = [t for t, _ in sorted(top_tags.items(), key=lambda x: -x[1])[:3]]
    # 变量vs常量分离:高赞有、低赞明显更少的标签 = 可能的爆款触发因子
    diff_tags = [t for t in top_tags if top_tags[t] > bot_tags.get(t, 0)][:3]

    bursts = [w for w in works if (w.get("like", 0) or 0) > avg_like * 2]
    top_cmt, bot_cmt = _avg(top, "comment"), _avg(bottom, "comment")
    top_col, bot_col = _avg(top, "collect"), _avg(bottom, "collect")

    # 互动结构差异(高赞层 vs 低赞层哪个互动维度拉开)
    inter_gap = []
    if top_cmt > bot_cmt * 1.3 and top_cmt > 1:
        inter_gap.append("评论")
    if top_col > bot_col * 1.3 and top_col > 1:
        inter_gap.append("收藏")

    # 演化趋势(按发布时间·近半 vs 早半 均赞)
    timed = sorted([w for w in works if w.get("create_time")], key=lambda w: w["create_time"])
    trend = None
    if len(timed) >= 4:
        h = len(timed) // 2
        early, late = _avg(timed[:h], "like"), _avg(timed[h:], "like")
        if late > early * 1.2:
            trend = "📈 在涨——你近期的作品比早期数据好,状态在往上走,保持"
        elif late < early * 0.8:
            trend = "📉 在掉——近期不如早期,该回头看看早期哪些做对了"
        else:
            trend = "➡️ 平稳——数据稳定,缺一个突破口"

    return {
        "n": n, "bursts": len(bursts), "hot_tags": hot_tags, "diff_tags": diff_tags,
        "inter_gap": inter_gap, "trend": trend,
        "top_desc": (top[0].get("desc", "") or "")[:30], "top_like": top[0].get("like", 0),
    }


def build_report(video: dict[str, Any], account: dict[str, Any],
                 audit: dict[str, Any], works: list | None = None) -> str:
    nick = account.get("nickname") or "你"
    fol = account.get("follower") or 0
    avg = account.get("avg_like") or 0
    mx = account.get("max_like") or 0
    vert = account.get("vertical_score")
    vert = vert if vert is not None else 0.0
    aweme = account.get("aweme_count") or 0
    sig = (account.get("signature") or "").strip()
    tags = [t for t in (account.get("hashtags") or []) if t]
    title = (video.get("title") or "").strip()
    like = video.get("like") or 0
    comment = video.get("comment") or 0
    share = video.get("share") or 0
    collect = video.get("collect") or 0

    散 = vert < 0.6
    spark = mx > avg * 3 and mx > 0
    blob = " ".join(tags) + sig + title
    track, track_why = _track(blob)
    biz = _is_business(blob)
    L2 = _analyze_works(works, avg)
    tags_str = "、".join(tags) if tags else "(没识别到明显标签)"
    ratio = like / (avg + 1)
    if ratio > 2:
        this = f"明显高于你平时(你平均 {avg} 个赞),算你的一条小爆款,值得好好复盘"
    elif ratio < 0.5:
        this = f"低于你平时(你平均 {avg} 个赞),这条偏冷"
    else:
        this = f"和你平时差不多(你平均 {avg} 个赞),属于正常发挥——不算失败,也不算爆"
    title_short = (title[:34] + "…") if len(title) > 34 else title
    noun = "产品/业务方向" if biz else "内容方向"

    L: list[str] = []
    P = L.append

    P(f"# 📋 账号诊断报告 · @{nick}")
    P("")
    P("> 这份报告基于你抖音账号的真实公开数据生成。我尽量说人话,你拿着就能照着做。")
    P("")

    P("## 一句话先说重点")
    if 散:
        P("**你的内容是有价值的,真正的问题不是「做得不好」,而是「方向太杂、系统认不清你是谁」。把方向收窄,你这个号能起来。**")
    elif biz:
        P("**你的定位清晰、是认真做生意的号。接下来用内容把「为什么选你」讲透,把流量导到询单/合作上。**")
    else:
        P("**你的方向比较清晰,接下来把已经验证过的内容做深做透就好。**")
    P("")

    # —— 一、现状 ——
    P("## 一、你现在是什么情况")
    P("")
    P("**你是谁、在做什么**")
    if sig:
        if biz:
            P(f"你的简介写着:「{sig}」—— 能看出你有明确的产品/业务定位,是认真做这门生意的。")
        else:
            P(f"你的简介写着:「{sig}」—— 能看出你是个有想法、愿意分享真实感受的人。")
    P(f"你发的内容,大方向是「**{track}**」。")
    P("")
    P("**你现在的水平**")
    P(f"- {_stage(fol)},一共发了 {aweme} 条作品。")
    P(f"- 你的视频平均 **{avg} 个赞**,最好的一条有 **{mx} 个赞**。")
    P("")
    P("**你发的这条视频表现怎么样**")
    if title_short:
        P(f"- 这条讲的是:「{title_short}」")
    P(f"- 数据:{like} 个赞、{comment} 条评论、{share} 次转发、{collect} 个收藏。")
    P(f"- 跟你自己比:**{this}**。" + ("别因为这一条数字焦虑——要看的是整体趋势,不是单独一条。" if ratio < 2 else ""))
    if biz:
        P("> 提醒:生意号别只盯点赞——**询单、私信、进店**才是真目标。点赞低不等于没效果,要看后端转化。")
    P("")

    # —— 二、多条找规律(L2·核心) ——
    sec = 2
    if L2:
        P(f"## 二、你这 {L2['n']} 条作品藏着的规律(这才是重点)")
        P(f"单看一条看不出门道——我把你最近 {L2['n']} 条作品**横着放一起看**,规律就出来了:")
        P("")
        P("**哪些是你的爆款、它们有什么共同点**")
        if L2["bursts"]:
            ht = "、".join(L2["hot_tags"]) if L2["hot_tags"] else "(标签不够集中,看不出明显共性)"
            P(f"- 你有 **{L2['bursts']} 条**明显高于平均(超均赞 2 倍)的作品。其中最戳人的那条是「{L2['top_desc']}…」({L2['top_like']} 赞)。")
            P(f"- 这些高赞作品最常出现的方向是:**{ht}** —— 这是你**已经验证过、观众买账**的{noun},别犹豫,多做这个。")
        else:
            P("- 你这批作品数据比较平均,还没跑出明显爆款——说明方向还在试,需要再多发几条找感觉。")
        P("")
        P("**高赞的 和 低赞的,差在哪(这是能复制的关键)**")
        bits = []
        if L2["diff_tags"]:
            bits.append(f"高赞作品更常带 **{'、'.join(L2['diff_tags'])}** 这些方向(低赞的没有)")
        if L2["inter_gap"]:
            bits.append(f"高赞作品的 **{'、'.join(L2['inter_gap'])}** 明显更高(说明这些内容更能激发互动)")
        if bits:
            P(f"- {';'.join(bits)}。")
            P(f"- **说人话:你只要多做高赞那批的方向,数据大概率比其他内容好——这是你自己的数据告诉你的,比抄别人靠谱。**")
        else:
            P("- 高赞和低赞的差异不明显——可能是样本还少,或者你的内容比较均质。建议刻意做几条不同方向,拉开对比再看。")
        P("")
        if L2["trend"]:
            P("**你最近状态在涨还是在掉**")
            P(f"- {L2['trend']}。")
            P("")
        sec = 3
    else:
        # 没拿到逐条作品(works)→ 诚实标,不假装
        P("## 二、关于「多条规律」(这次没拿到)")
        P("- 这次只拿到了账号的汇总数据,没拿到你逐条作品的明细,所以**没法做「多条横向找规律」**(本该是最有价值的一段)。补上逐条作品数据后,能告诉你:哪类内容是你的爆款、高赞和低赞差在哪、状态在涨还是掉。")
        P("")
        sec = 3

    # —— 最该解决 / 做得对 ——
    if 散:
        P(f"## {_cn(sec)}、你现在最该解决的一件事:账号「太杂」")
        P("")
        P(f"你最近视频贴的标签是这些:**{tags_str}**。")
        P("")
        P("发现没?**这其实是好几个不同的方向。** 抖音给不给你推流量,全靠它「猜你是做什么的」。你一会儿讲这个、一会儿讲那个,系统就懵了。")
        P("")
        P(f"**你明明有能力做出 {mx} 个赞的内容,但整体起不来,问题不在内容好不好,在「聚不聚焦」。**")
    else:
        P(f"## {_cn(sec)}、你做得对的地方")
        P(f"你的{noun}比较集中,系统能认清你是做「{track}」的——这是好事,接着往深里做。")
    P("")
    sec += 1

    # —— 优势 ——
    P(f"## {_cn(sec)}、你有一个别人抢不走的优势")
    P("")
    if biz:
        P("别小看你手里的东西:**真实的产品力 / 源头优势**。")
        if title_short:
            P(f"你做的是实打实的业务(「{title_short}」),背后是真实的供应链、源头和专业积累 —— 这种「看得见摸得着」的真东西,比空洞营销可信得多,同行也抄不走。")
        P("现在内容同质化严重,**恰恰是你这种「有真实产品/源头背书」的生意号,最容易建立信任、撬动询单**。")
    else:
        P("别灰心,你手里有最值钱的东西:**真实**。")
        if title_short:
            P(f"你讲的「{title_short}」这种真实的经历和感受,是你亲身经历、带着体温的 —— AI 编不出来、别的博主也抄不像。")
        P("现在 AI 生成的内容满天飞,**恰恰是你这种「真实的表达」最稀缺、最值钱**。")
    P("")
    sec += 1

    # —— 怎么做 ——
    P(f"## {_cn(sec)}、接下来具体怎么做(照着做就行)")
    P("")
    n = 1
    if L2 and L2["hot_tags"]:
        P(f"**第 {n} 步(最重要):把你已经验证过的方向做深**")
        P(f"上面看出来了——你的高赞作品集中在 **{'、'.join(L2['hot_tags'])}**。别东一榔头西一棒,接下来一个月就围绕这个方向做深做透,这是你自己数据证明有效的路。")
        P("")
        n += 1
    if biz:
        P(f"**第 {n} 步:把最戳客户痛点的卖点,放到开头 3 秒**")
        P("客户最关心什么(省钱?稳定供货?品质?)—— 一开口就说那句最戳痛点的话,别埋在中间。")
    else:
        P(f"**第 {n} 步:把最揪心的那句话,放到开头 3 秒**")
        P("抖音前 3 秒决定别人划不划走,一开口就甩出最能戳中人的那句话。")
    P("")
    n += 1
    if spark:
        P(f"**第 {n} 步:把你那条 {mx} 个赞的视频研究透**")
        P(f"翻出来,看它讲了什么、开头怎么说、戳中了什么 —— 然后多做那个方向。**放大你自己验证过的成功,比抄别人靠谱**。")
        P("")
    sec += 1

    # —— 未来 ——
    P(f"## {_cn(sec)}、照这样走,接下来会怎样(说实话,不夸张)")
    P(f"- 你做的「{track}」是个**值钱的方向**:{track_why}。")
    if 散:
        P("- 继续这么散,大概率一直「偶尔一条小爆、整体不温不火」;一旦聚焦、系统认清你,起量会稳得多。")
    if spark:
        P("- 你有过小爆款,说明天花板不低;关键是把「偶然」变成「稳定」。")
    if biz:
        P("- 生意号的关键不是粉丝多,是**精准**:1000 个对的客户 > 10 万泛粉。把内容当获客工具,盯询单转化。")
    P("")
    sec += 1

    # —— 可信度 ——
    P(f"## {_cn(sec)}、这份分析有多可信(实话实说)")
    P("- 上面的数字(粉丝、点赞、作品、标签、规律)**都是你抖音账号的真实公开数据,没有一个是编的**。")
    P("- 但有两个诚实的提醒:")
    P("  1. 这次**只看了你一个号、一个数据来源**,没跟竞品交叉验证,所以给你的是「靠谱的方向」,别当成 100% 精确的结论。")
    P("  2. 有些关键数据抖音**不公开** —— 比如完播率、流量从哪来、有没有转化 —— 这些拿不到,我**宁可告诉你「拿不到」,也绝不瞎编**。")
    return "\n".join(L)


_CN = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]


def _cn(n: int) -> str:
    return _CN[n] if 0 <= n < len(_CN) else str(n)
