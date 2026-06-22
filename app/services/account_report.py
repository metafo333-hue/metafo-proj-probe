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
from datetime import date
from typing import Any

# 报告有效期设计（盲点①）：账号状态会变，报告是快照。
# 30天触发复诊提醒——刚好是创作者一个内容周期，也是平台算法完整考核窗口。
_REPORT_VALID_DAYS = 30

_TRACK_HINTS = [
    (("供货", "直供", "源头", "工厂", "批发", "代工", "OEM", "招商", "加盟", "产业带", "货源", "一手货源", "厂家", "餐饮食材"),
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
    (("读书", "毛选", "国学", "历史", "哲学", "认知", "思维", "成事", "心法", "教员", "伟人"), "个人成长 / 知识励志",
     "靠观点和人格吸粉·粉丝忠诚度高·适合卖书单/课程/社群/知识付费·别硬塞带货"),
    (("穿搭", "美妆", "时尚", "护肤"), "时尚美妆", "品牌预算最多,适合带货和品牌合作"),
]
# 注:歧义宽泛词(一手/厂/公司/企业/定制)已收紧为明确 B2B 短语·防知识/MCN 号误判(Q:毛选号"一手修心"曾误判)
_BIZ_KW = ("供货", "直供", "源头", "工厂", "批发", "代工", "OEM", "招商", "加盟", "旗舰", "厂家",
           "产业带", "货源", "一手货源", "批发价", "实体店", "门店", "品牌方",
           "龙头企业", "贴牌", "合作私信", "代工厂")
_HASHTAG_RE = re.compile(r"#([^#\s]+)")

# ① 赛道基准（互动率 = 均赞/粉丝·经验区间·2024-2025年数据）
# 格式：{赛道关键词: {粉丝层: 基准互动率%}}
_TRACK_BENCHMARKS: dict[str, dict[str, float]] = {
    "带货电商":      {"<1w": 6.5, "1w-5w": 4.5, "5w-50w": 3.0, "50w+": 1.8},
    "知识科普":      {"<1w": 7.0, "1w-5w": 5.0, "5w-50w": 3.5, "50w+": 2.2},
    "B2B供货":       {"<1w": 5.0, "1w-5w": 3.8, "5w-50w": 2.5, "50w+": 1.5},
    "时尚美妆":      {"<1w": 5.5, "1w-5w": 4.0, "5w-50w": 2.8, "50w+": 1.6},
    "健身运动":      {"<1w": 6.0, "1w-5w": 4.2, "5w-50w": 2.8, "50w+": 1.8},
    "美食":          {"<1w": 4.5, "1w-5w": 3.2, "5w-50w": 2.0, "50w+": 1.2},
    "女性成长":      {"<1w": 5.5, "1w-5w": 4.0, "5w-50w": 2.8, "50w+": 1.6},
    "母婴育儿":      {"<1w": 6.0, "1w-5w": 4.3, "5w-50w": 2.9, "50w+": 1.7},
    "个人成长":      {"<1w": 5.5, "1w-5w": 4.0, "5w-50w": 2.8, "50w+": 1.7},
    "default":       {"<1w": 5.0, "1w-5w": 3.5, "5w-50w": 2.5, "50w+": 1.5},
}

# ⑤ 里程碑节点（粉丝数 → 解锁的权益）
_MILESTONES: list[tuple[int, str]] = [
    (1_000,   "满足大部分平台基础创作者权益（橱窗/评论置顶/私信）"),
    (5_000,   "接商单起步线，品牌方开始关注小账号合作"),
    (10_000,  "开通更多平台权益，星图接单门槛·万粉是心理分水岭"),
    (50_000,  "稳定商单阶段，单条视频可谈品牌合作"),
    (100_000, "头部跨入门槛，MCN机构主动找上门"),
    (500_000, "大V量级，单粉价值最高时段"),
    (1_000_000, "百万博主，品牌定制合作·顶级流量"),
]


def _fol_tier(fol: int) -> str:
    if fol < 10_000:   return "<1w"
    if fol < 50_000:   return "1w-5w"
    if fol < 500_000:  return "5w-50w"
    return "50w+"


def _benchmark_text(track: str, fol: int, avg_like: int) -> str:
    """① 赛道基准对比：告诉用户他的互动率在同赛道同量级里排在哪。"""
    if fol <= 0 or avg_like is None:
        return ""
    rate_pct = avg_like / fol * 100
    tier = _fol_tier(fol)
    # 找匹配赛道的基准
    bench_map = None
    for kw, bm in _TRACK_BENCHMARKS.items():
        if kw in track:
            bench_map = bm
            break
    if bench_map is None:
        bench_map = _TRACK_BENCHMARKS["default"]
    bench = bench_map.get(tier, 3.5)

    if rate_pct >= bench * 1.5:
        label, emoji = "显著高于同赛道同量级平均水平", "🟢"
        pct_txt = f"约高 {int((rate_pct / bench - 1) * 100)}%"
    elif rate_pct >= bench:
        label, emoji = "高于同赛道同量级平均水平", "🟢"
        pct_txt = f"约高 {int((rate_pct / bench - 1) * 100)}%"
    elif rate_pct >= bench * 0.7:
        label, emoji = "接近同赛道同量级平均水平", "🟡"
        pct_txt = f"约低 {int((1 - rate_pct / bench) * 100)}%"
    else:
        label, emoji = "低于同赛道同量级平均水平", "🔴"
        pct_txt = f"约低 {int((1 - rate_pct / bench) * 100)}%"

    return (
        f"{emoji} 你的互动率约 **{rate_pct:.1f}%**（均赞/粉丝），"
        f"{label}（同赛道{tier}账号基准约 {bench:.1f}%，{pct_txt}）。"
        f"\n> 互动率是「内容对粉丝吸引力」的代理指标——完播率是黑盒拿不到，互动率是最可靠的公开替代。"
    )


def _milestone_md(fol: int, track: str) -> str:
    """⑤ 里程碑：下一个节点是什么，解锁什么权益。"""
    next_m = next((m for m, _ in _MILESTONES if m > fol), None)
    if not next_m:
        return "你已经是百万大V，接下来的关键是品牌定制合作和私域变现。"
    _, unlock = next((m, u) for m, u in _MILESTONES if m == next_m)
    gap = next_m - fol
    gap_txt = f"{gap:,}"
    if gap >= 10000:
        gap_txt = f"{gap // 10000}万{gap % 10000 or ''}"
    return (
        f"**下一个里程碑：{next_m // 10000}万粉**（还差 {gap:,} 个）\n"
        f"解锁：{unlock}\n"
        f"\n"
        f"> 里程碑不是终点，是「系统开始认真对待你」的信号。"
        f"专注内容质量，数字会跟上来。"
    )


def _today_task_md(track: str, biz: bool, fol: int, avg_like: int, vert: float) -> str:
    """③ 今日执行：一件事·30分钟内完成。"""
    if fol < 500:
        task = "先发够 **10条内容**——系统需要样本才能认清你是谁，现在看数据还太早。每天一条，先发够再说。"
        time_est = "每天30分钟·连续10天"
    elif avg_like < 50 or vert < 0.4:
        task = "**把标签收窄到一个方向**：看你最近10条的标签，选最集中的那个，下条只用这个方向的标签。系统需要明确的信号才能精准推流。"
        time_est = "5分钟选标签 + 25分钟拍一条内容"
    elif any(k in track for k in ("带货", "电商", "供货", "B2B")):
        task = "**输入今天要推的产品 → 生成3条带货脚本（¥29）**，选最顺口的那条，今天就能拍完发出去。省下自己写2小时，用这2小时多拍一条。"
        time_est = "生成2分钟 + 拍摄30分钟"
    elif any(k in track for k in ("知识", "科普", "励志", "成长", "财经")):
        task = "**确定今天的口播选题 → 生成一条口播稿（¥29）**，对着稿子读两遍就能拍。口播的核心是「说清楚一个观点」，不是完美。"
        time_est = "生成2分钟 + 拍摄20分钟"
    else:
        task = "**复盘你最近3条高赞视频**：找它们共同的开场方式或话题，下条内容复制这个角度。不要创新，要复制已经验证的东西。"
        time_est = "15分钟复盘 + 30分钟拍一条"
    return f"**📌 今天做这一件事**（{time_est}）\n\n{task}"


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

    # 赞赏密度（钻石粉指标）
    total_like = sum(w.get("like", 0) or 0 for w in works)
    total_admire = sum(w.get("admire", 0) or 0 for w in works)
    admire_density = round(total_admire / max(total_like, 1) * 1000, 2)  # 每千赞的赞赏数

    # ── 组合H：爆款触发因子多维升级 ─────────────────────────────────
    # H1: BGM热度差异（高赞层 vs 低赞层 music_user_count 中位数）
    def _median(lst):
        s = sorted(x for x in lst if x is not None)
        return s[len(s)//2] if s else None

    top_bgm = [w.get("music_user_count") or 0 for w in top]
    bot_bgm = [w.get("music_user_count") or 0 for w in bottom]
    bgm_signal = None
    top_bgm_med = _median(top_bgm)
    bot_bgm_med = _median(bot_bgm)
    if top_bgm_med is not None and bot_bgm_med is not None:
        if top_bgm_med > bot_bgm_med * 2 and top_bgm_med > 100:
            bgm_signal = f"高赞层BGM用热曲（中位使用量{top_bgm_med:,}次）vs低赞层（{bot_bgm_med:,}次）·热曲驱动明显"
        elif bot_bgm_med > top_bgm_med * 2:
            bgm_signal = "高赞层反而用冷门BGM·原声/情绪化音乐更适合此账号"

    # H2: 时长差异（高赞层 vs 低赞层 duration_ms 中位数）
    top_dur = [w.get("duration_ms") or 0 for w in top]
    bot_dur = [w.get("duration_ms") or 0 for w in bottom]
    dur_signal = None
    top_dur_med = _median(top_dur)
    bot_dur_med = _median(bot_dur)
    if top_dur_med and bot_dur_med and top_dur_med > 0 and bot_dur_med > 0:
        ratio_dur = top_dur_med / bot_dur_med
        top_s = round(top_dur_med / 1000)
        bot_s = round(bot_dur_med / 1000)
        if ratio_dur < 0.7:
            dur_signal = f"高赞层更短（中位{top_s}s）vs低赞层（{bot_s}s）·简洁更易完播"
        elif ratio_dur > 1.4:
            dur_signal = f"高赞层更长（中位{top_s}s）vs低赞层（{bot_s}s）·深度内容更受认可"

    # H3: 发布时间规律（高赞层集中在哪几天）
    weekday_signal = None
    weekday_cn = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    top_days = {}
    for w in top:
        ct = w.get("create_time")
        if ct:
            import time as _time
            wd = _time.gmtime(ct).tm_wday  # 0=周一
            top_days[wd] = top_days.get(wd, 0) + 1
    if top_days:
        best_day = max(top_days, key=top_days.get)
        if top_days[best_day] >= len(top) * 0.4:  # 40%以上集中在某天
            weekday_signal = f"高赞作品 {top_days[best_day]}/{len(top)} 条集中在{weekday_cn[best_day]}发布"

    # H4: 平台标签差异（高赞层 video_tag level-2 集中度）
    tag2_signal = None
    top_tag2 = {}
    for w in top:
        for lvl, tname in (w.get("video_tag") or []):
            if lvl == 2 and tname:
                top_tag2[tname] = top_tag2.get(tname, 0) + 1
    if top_tag2:
        best_t2 = max(top_tag2, key=top_tag2.get)
        if top_tag2[best_t2] >= len(top) * 0.5:
            tag2_signal = f"高赞层 {top_tag2[best_t2]}/{len(top)} 条被平台归类为「{best_t2}」"

    trigger_factors = [s for s in [bgm_signal, dur_signal, weekday_signal, tag2_signal] if s]

    # ── 组合E：IP化程度（合集/系列覆盖率）────────────────────────────
    ip_works = sum(1 for w in works if w.get("mix_name") or w.get("series_name"))
    ip_ratio = round(ip_works / n, 2)
    ip_names = list({w.get("mix_name") or w.get("series_name")
                     for w in works if w.get("mix_name") or w.get("series_name")})[:3]

    return {
        "n": n, "bursts": len(bursts), "hot_tags": hot_tags, "diff_tags": diff_tags,
        "inter_gap": inter_gap, "trend": trend,
        "top_desc": (top[0].get("desc", "") or "")[:30], "top_like": top[0].get("like", 0),
        "admire_density": admire_density,
        "trigger_factors": trigger_factors,  # 爆款触发因子列表
        "ip_ratio": ip_ratio,
        "ip_names": ip_names,
    }


def build_report(video: dict[str, Any], account: dict[str, Any],
                 audit: dict[str, Any], works: list | None = None,
                 av_md: str | None = None, compare_md: str | None = None,
                 l0_md: str | None = None, business_md: str | None = None,
                 attribution_md: str | None = None,
                 # —— 11 缺口科学适应方案段(2026-06-22·全可选·None 则跳过·旧调用零影响)——
                 segment_md: str | None = None, cold_start_md: str | None = None,
                 audience_md: str | None = None, comment_md: str | None = None,
                 homepage_md: str | None = None, trend_md: str | None = None,
                 benchmark_md: str | None = None, risk_md: str | None = None,
                 verify_md: str | None = None, action_md: str | None = None,
                 rotation_md: str | None = None,    # 轮动判断（块6）
                 synthesis_md: str | None = None,   # 综合决策层（块新增）
                 ) -> str:
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
    cur_fol = account.get("follower") or 0

    L: list[str] = []
    P = L.append

    today = date.today().isoformat()
    expire = date.today().replace(day=min(date.today().day + _REPORT_VALID_DAYS, 28)) \
        if date.today().day + _REPORT_VALID_DAYS <= 28 \
        else date.fromordinal(date.today().toordinal() + _REPORT_VALID_DAYS)

    # ══════════════════════════════════════════════════════════════════
    # 块0：决策摘要
    # ══════════════════════════════════════════════════════════════════
    P(f"# 📋 账号诊断报告 · @{nick}")
    P("")
    P(f"> 诊断截至 **{today}**（账号数据每天在变，本报告是当日快照）。")
    P(f"> 建议 **{expire}** 前复诊一次，看改变后的数据有没有往对的方向走。")
    P("> 我尽量说人话，你拿着就能照着做。")
    P("")

    P("## 一句话先说重点")
    if 散:
        P("**你的内容是有价值的,真正的问题不是「做得不好」,而是「方向太杂、系统认不清你是谁」。把方向收窄,你这个号能起来。**")
    elif biz:
        P("**你的定位清晰、是认真做生意的号。接下来用内容把「为什么选你」讲透,把流量导到询单/合作上。**")
    else:
        P("**你的方向比较清晰,接下来把已经验证过的内容做深做透就好。**")
    P("")

    # ══════════════════════════════════════════════════════════════════
    # 块1：账号全景
    # ══════════════════════════════════════════════════════════════════
    P("## 一、你现在是什么情况")
    P("")

    # 对象层：认清身份(segment)+冷启动方向（0数据·最前·有则插）
    if segment_md:
        P(segment_md); P("")
    if cold_start_md:
        P(cold_start_md); P("")

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
    # 数据→洞察→行动(原则2):均值vs最高的差距说明什么、所以该干嘛
    if spark:
        P(f"- 👉 **这说明**:你做得出 {mx} 赞的爆款,但没稳下来(平均才 {avg})——**潜力够,缺的是把「偶然爆」变成「稳定爆」**。下面第五段会给你怎么做。")
    P("")

    # ① 赛道基准对比（告诉用户他和同赛道同量级相比在哪）
    _bench = _benchmark_text(track, fol, avg)
    if _bench:
        for _bl in _bench.split("\n"):
            if _bl.startswith(">"):
                P(_bl)
            else:
                P(f"- {_bl}" if not _bl.startswith("-") else _bl)
        P("")

    # 粉丝轨迹（块1·画像之后）
    max_fol = account.get("max_follower")
    if max_fol and max_fol > 0:
        delta = cur_fol - max_fol
        ratio_fol = delta / max_fol
        if ratio_fol < -0.02:
            P(f"- 📉 粉丝轨迹：当前 {cur_fol:,} · 历史峰值 {max_fol:,} · 净掉 {abs(delta):,}（-{abs(ratio_fol):.1%}）")
            if ratio_fol < -0.10:
                P("  ⚠️ 掉粉幅度较大，结合趋势轨迹找拐点原因")
        elif ratio_fol > 0.02:
            P(f"- 📈 粉丝轨迹：当前 {cur_fol:,} · 净增 {delta:,}（+{ratio_fol:.1%}）· 仍在增长")
        else:
            P(f"- ➡️ 粉丝轨迹：当前 {cur_fol:,} · 基本稳定（峰值 {max_fol:,}）")
    # 榜单信号
    dog_rank = account.get("dog_card_rank")
    dog_text = account.get("dog_card_text")
    if dog_rank and dog_text:
        P(f"- 🏆 上榜：{dog_text} 第 {dog_rank} 名（赛道热度信号）")
    P("")

    # 平台定位一致性（F·块1）
    plat_tags = account.get("platform_tags") or []
    user_tags = account.get("hashtags") or []
    if plat_tags and user_tags:
        track_name_p, _ = _track(" ".join(plat_tags))
        if any(pt in " ".join(user_tags) for pt in plat_tags):
            P(f"- 🏷️ 平台定位一致性：平台认定「{plat_tags[0]}」与你写的 #{user_tags[0]} 吻合 ✅ 定位清晰")
        else:
            P(f"- 🏷️ 平台定位一致性：⚠️ 平台把你归类为「{plat_tags[0]}」，但你写的是「#{user_tags[0]}」，建议按平台标签方向调整选题")
        P("")

    # 创作者分层（这条视频）
    P("**你发的这条视频表现怎么样**")
    if title_short:
        P(f"- 这条讲的是:「{title_short}」")
    P(f"- 数据:{like} 个赞、{comment} 条评论、{share} 次转发、{collect} 个收藏。")
    P(f"- 跟你自己比:**{this}**。" + ("别因为这一条数字焦虑——要看的是整体趋势,不是单独一条。" if ratio < 2 else ""))
    if biz:
        P("> 提醒:生意号别只盯点赞——**询单、私信、进店**才是真目标。点赞低不等于没效果,要看后端转化。")
    P("")

    # ══════════════════════════════════════════════════════════════════
    # 块2：内容诊断（L2多条 + 爆款触发因子H + IP化程度E + 置顶诊断I + 视听L1 + 归因）
    # ══════════════════════════════════════════════════════════════════
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

        # 组合H：爆款触发因子
        if L2.get("trigger_factors"):
            factors = L2["trigger_factors"]
            lines = ["\n**🔬 爆款触发因子（你自己数据归纳出的规律）**"]
            for f in factors:
                lines.append(f"  · {f}")
            lines.append("→ 下一条建议：按以上规律组合发布，优先验证最强信号")
            P("\n".join(lines))
            P("")

        # 组合E：IP化程度
        if L2.get("ip_ratio") is not None:
            ir = L2["ip_ratio"]
            ip_names_e = L2.get("ip_names") or []
            if ir >= 0.5:
                ip_desc = f"✅ IP化程度高（{ir:.0%}的作品属于合集/系列）·系列化思维强·适合课程/专辑/付费内容"
            elif ir >= 0.2:
                ip_desc = f"🟡 IP化程度中等（{ir:.0%}）·有部分系列但未成体系"
            else:
                ip_desc = f"⚠️ IP化程度低（{ir:.0%}）·碎片化内容为主·建议建立1-2个固定系列提升粉丝粘性"
            name_str = f"（现有：{'、'.join(ip_names_e)}）" if ip_names_e else ""
            P(f"\n**📚 内容IP化程度** {ip_desc}{name_str}")
            P("")

    else:
        # 没拿到逐条作品(works)→ 诚实标,不假装
        P("## 二、关于「多条规律」(这次没拿到)")
        P("- 这次只拿到了账号的汇总数据,没拿到你逐条作品的明细,所以**没法做「多条横向找规律」**(本该是最有价值的一段)。补上逐条作品数据后,能告诉你:哪类内容是你的爆款、高赞和低赞差在哪、状态在涨还是掉。")
        P("")

    # 置顶内容诊断（I·紧跟L2）
    pinned = account.get("pinned_work")
    if pinned:
        ptags = " / ".join(t[1] for t in (pinned.get("video_tag") or []))
        plike = pinned.get("like", 0)
        pavg = account.get("avg_like") or 1
        perf = "⬆️ 高于均值" if plike > pavg * 1.5 else ("➡️ 接近均值" if plike > pavg * 0.7 else "⬇️ 低于均值")
        P(f"\n**📌 置顶内容诊断**\n「{(pinned.get('desc') or '')[:40]}」"
          f"· 点赞 {plike:,}（{perf}）· 平台标签：{ptags or '未分类'}\n"
          + ("✅ 置顶内容质量高，是好名片" if plike > pavg else
             "⚠️ 置顶内容低于账号均值，建议换一条更有代表性的作品置顶"))
        P("")

    # 视听六层拆解（L1·有则插）
    if av_md:
        P(av_md)
        P("")

    # 归因飞轮（有则插）
    if attribution_md:
        P(attribution_md)
        P("")

    # ══════════════════════════════════════════════════════════════════
    # 块3：受众质量（钻石粉密度B + 评论洞察 + 受众画像）
    # ══════════════════════════════════════════════════════════════════
    P("## 三、你的粉丝有多忠诚")
    P("")

    # 掉粉预警（组合矩阵指标5·历史峰值粉丝 - 当前·实测才发现的 max_follower_count）
    _dd = account.get("follower_drawdown")
    if _dd and _dd.get("drawdown_pct", 0) >= 5:
        _warn = ("⚠️ 回撤明显，建议复盘近期内容方向是否漂移、是否有引发掉粉的争议视频。"
                 if _dd["drawdown_pct"] >= 15 else "🟡 轻微回撤，留意内容稳定性。")
        P(f"**📉 掉粉预警** 历史峰值 {_dd['max']:,} → 现在 {_dd['current']:,}，"
          f"已掉 {_dd['lost']:,}（-{_dd['drawdown_pct']}%）。{_warn}")
        P("")

    # 钻石粉密度（B）
    a_density = (L2.get("admire_density") if L2 else None)
    if a_density is not None:
        if a_density >= 5:
            loyalty = "高忠诚度·适合知识付费/私域变现"
        elif a_density >= 1:
            loyalty = "中等忠诚度·先做互动再变现"
        else:
            loyalty = "待培养·先做内容信任"
        P(f"**💎 钻石粉密度** {a_density}/千赞 · {loyalty}")
        P("")

    if audience_md:
        P(audience_md); P("")
    if comment_md:
        P(comment_md); P("")

    # ══════════════════════════════════════════════════════════════════
    # 块4：变现全景（直播协同J + business_md含商业化状态/接单率/赛道价值/变现矩阵L/转化处方）
    # ══════════════════════════════════════════════════════════════════
    P("## 四、变现能力诊断")
    P("")

    # 直播协同（J）
    live_st = account.get("live_status") or 0
    room = account.get("room_id") or 0
    if live_st != 0 or room != 0:
        P("**🔴 直播协同** 分析时账号正在直播 → 建议直播后24h内发精华剪辑·引流再次进直播")
        P("")
    elif (account.get("mix_count") or 0) == 0 and cur_fol > 10000:
        P("**💡 直播机会** 当前粉丝量已适合开播·短视频+直播双引擎可显著提升变现效率")
        P("")

    if business_md:
        P(business_md); P("")

    # ══════════════════════════════════════════════════════════════════
    # 块5：风险预警（致命置顶 · 合规说法核查）← 从末尾提前到这里
    # ══════════════════════════════════════════════════════════════════
    P("## 五、风险预警（不解决会直接影响变现）")
    P("")

    if risk_md:
        P(risk_md); P("")

    # 合规说法核查
    claims = [k for k in ("年", "非遗", "传承", "龙头", "认证", "省级", "国家级", "专利", "获奖", "冠军", "第一", "唯一") if k in sig]
    if claims:
        P(f"**📋 资质核查提醒**：你简介里有「{'、'.join(claims)}」这类说法，建议晒出实物证据（证书/工厂实拍/媒体报道），口说无凭。")
        if biz:
            P("- 价格、供货/效果承诺别夸大,留好证据。")
        P("")
    P("- 背景音乐用抖音曲库的免费商用音乐，别用来路不明的（版权风险·会限流甚至下架）。")
    P("")

    # ══════════════════════════════════════════════════════════════════
    # 块6：外部参照（趋势轨迹 + 同赛道对标 + 竞品 + L0环境）
    # ══════════════════════════════════════════════════════════════════
    P("## 六、外部参照")
    P("")

    if rotation_md:
        P(rotation_md); P("")
    if trend_md:
        P(trend_md); P("")
    if benchmark_md:
        P(benchmark_md); P("")
    if compare_md:
        P(compare_md); P("")
    if l0_md:
        P(l0_md); P("")

    # ══════════════════════════════════════════════════════════════════
    # 综合决策层（联动分析·时效标注·30天预判·放在外部参照之后·行动之前）
    # ══════════════════════════════════════════════════════════════════
    if synthesis_md:
        P(synthesis_md); P("")

    # ══════════════════════════════════════════════════════════════════
    # 块7：优先行动（垂直度诊断 + 优势 + 具体怎么做 + 阶段判断 + 主页诊断 + 行动清单 + 多平台矩阵K + 已验证建议）
    # ══════════════════════════════════════════════════════════════════
    P("## 七、优先行动")
    P("")

    # 垂直度诊断（最该解决 / 做得对）
    if 散:
        P(f"**你现在最该解决的一件事:账号「太杂」**")
        P("")
        P(f"你最近视频贴的标签是这些:**{tags_str}**。")
        P("")
        P("发现没?**这其实是好几个不同的方向。** 抖音给不给你推流量,全靠它「猜你是做什么的」。你一会儿讲这个、一会儿讲那个,系统就懵了。")
        P("")
        P(f"**你明明有能力做出 {mx} 个赞的内容,但整体起不来,问题不在内容好不好,在「聚不聚焦」。**")
    else:
        P(f"**你做得对的地方**")
        P(f"你的{noun}比较集中,系统能认清你是做「{track}」的——这是好事,接着往深里做。")
    P("")

    # 优势
    P("**你有一个别人抢不走的优势**")
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

    # 具体怎么做（行动分层）
    P("**接下来具体怎么做(照着做就行)**")
    P("**按重要程度排好了——先做 🔴 的,🟡 有余力再做:**")
    P("")
    _n = 1
    if L2 and L2["hot_tags"]:
        P(f"**🔴 第 {_n} 步｜最重要·这个月就做：把你已经验证过的方向做深**")
        P(f"上面看出来了——你的高赞作品集中在 **{'、'.join(L2['hot_tags'])}**。别东一榔头西一棒,接下来一个月就围绕这个方向做深做透,这是你自己数据证明有效的路。")
        P("")
        _n += 1
    if biz:
        P(f"**🔴 第 {_n} 步｜本周就能改：把最戳客户痛点的卖点,放到开头 3 秒**")
        P("客户最关心什么(省钱?稳定供货?品质?)—— 一开口就说那句最戳痛点的话,别埋在中间。")
    else:
        P(f"**🔴 第 {_n} 步｜本周就能改：把最揪心的那句话,放到开头 3 秒**")
        P("抖音前 3 秒决定别人划不划走,一开口就甩出最能戳中人的那句话。")
    P("")
    _n += 1
    if spark:
        P(f"**🟡 第 {_n} 步｜有余力再做：把你那条 {mx} 个赞的视频研究透**")
        P(f"翻出来,看它讲了什么、开头怎么说、戳中了什么 —— 然后多做那个方向。**放大你自己验证过的成功,比抄别人靠谱**。")
        P("")

    # 阶段判断
    P("**你这个号整体判断:处在什么阶段、该往哪走**")
    if fol < 1000:
        lifecycle = "**冷启期**(不到 1000 粉·首要任务是让算法认清你是做什么的,聚焦单一方向、别换)"
    elif fol < 50000:
        if L2 and "掉" in (L2.get("trend") or ""):
            lifecycle = "**成长期·但近期遇瓶颈**(有基础了,但作品数据近期在下滑——回头看早期哪些做对了,把它找回来)"
        elif L2 and "涨" in (L2.get("trend") or ""):
            lifecycle = "**成长期·上升势头**(数据在往上走,保持当前方向加速做)"
        else:
            lifecycle = "**成长期**(把验证过的方向做深、稳定产出是关键)"
    else:
        lifecycle = "**成熟期**(重心可转向私域沉淀和变现,内容维持稳定即可)"
    _trend_txt = ("、近期数据在涨" if (L2 and "涨" in (L2.get("trend") or "")) else
                  "、近期数据在掉" if (L2 and "掉" in (L2.get("trend") or "")) else "")
    P(f"**怎么判断的**(不是拍脑袋)：看你粉丝量({fol:,}){_trend_txt}、方向{'偏散' if 散 else '比较集中'}——综合下来：")
    P(f"- **所处阶段**:{lifecycle}。")
    moat = (f"真实的产品力和源头优势(「{track}」的供应链、专业积累,同行抄不走)" if biz
            else f"你的真实表达和独特视角(「{track}」里你的经历和人格,AI 和别人抄不像)")
    P(f"- **你抄不走的护城河**:{moat}。")
    P(f"- 你做的「**{track}**」是个值钱的方向:{track_why}。")
    if 散:
        P("- 现在的瓶颈是「太散」;一旦聚焦、系统认清你,起量会稳得多。")
    if spark:
        P("- 你有过小爆款,说明天花板不低;关键是把「偶然」变成「稳定」。")
    if biz:
        P("- 变现走「精准」不是「泛流量」:1000 个对的客户 > 10 万泛粉,把内容当获客工具、盯询单转化。")
    P("")

    # ⑤ 下一个里程碑
    _ms = _milestone_md(fol, track)
    if _ms:
        for _ml in _ms.split("\n"):
            P(_ml)
        P("")

    # 主页诊断（有则插）
    if homepage_md:
        P(homepage_md); P("")

    # 行动清单（有则插）
    if action_md:
        P(action_md); P("")

    # 多平台矩阵（K）
    mp_fol = account.get("mplatform_followers")
    if mp_fol and cur_fol and mp_fol > cur_fol * 1.2:
        overflow = (mp_fol - cur_fol) / cur_fol
        P(f"**📱 跨平台矩阵** 多平台汇总 {mp_fol:,} > 抖音 {cur_fol:,}（溢出率 +{overflow:.0%}）→ 检查简介分身账号联动")
        P("")

    # 已验证建议（有则插）
    if verify_md:
        P(verify_md); P("")

    # ══════════════════════════════════════════════════════════════════
    # 块8：数据底座（可信度 + 脚本生成入口 + 复诊钩子）
    # ══════════════════════════════════════════════════════════════════
    P("## 八、这份分析有多可信(实话实说)")
    P("- 上面的数字(粉丝、点赞、作品、标签、规律)**都是你抖音账号的真实公开数据,没有一个是编的**。")
    P("- 但有两个诚实的提醒:")
    P("  1. 这次**只看了你一个号、一个数据来源**,没跟竞品交叉验证,所以给你的是「靠谱的方向」,别当成 100% 精确的结论。")
    P("  2. 有些关键数据抖音**不公开** —— 比如完播率、流量从哪来、有没有转化 —— 这些拿不到,我**宁可告诉你「拿不到」,也绝不瞎编**。")
    P("")

    # ③ 今日执行框（一件事·30分钟内完成·放在脚本入口之前）
    _task = _today_task_md(track, biz, fol, avg, vert)
    P("## 九、今天做这一件事")
    P("")
    for _tl in _task.split("\n"):
        P(_tl)
    P("")

    # 脚本生成入口（分析→生产的核心变现出口）
    P("## 十、下一步：把分析变成内容")
    P("")
    _is_ecom = any(k in blob for k in ("带货", "选品", "好物", "种草", "橱窗", "供货", "直供", "产业带"))
    _is_knowledge = any(k in track for k in ("知识", "励志", "科普", "财经", "考证"))
    _is_local = any(k in blob for k in ("探店", "餐饮", "美发", "美甲", "健身", "培训", "门店", "实体"))
    if _is_ecom or biz:
        P(f"你的账号方向是带货/电商，内容产量直接决定你能覆盖多少选品机会。")
        P(f"以你目前均赞 **{avg}** 的基础，每周至少 5-7 条才能维持算法权重。")
        P("")
        P("**现在可以做的**：输入你今天要推的产品，基于上面的账号分析，")
        P("生成 3 条可以直接用的带货脚本（含开头钩子 / 核心卖点 / 行动号召）。")
        P("")
        P("> ¥29 · 生成3条带货脚本（vs 外包脚本 200-2000元/条）")
        P("> ¥49 · 生成5条 + 竞品爆款角度对比")
    elif _is_knowledge:
        P(f"你的账号方向是知识/口播，内容的核心是「脚本质量」——选题对了，稿子出不来，也白费。")
        P(f"口播脚本自己写：1-2小时/条；外包：500-800元/分钟。")
        P("")
        P("**现在可以做的**：输入今天的选题方向，基于你的口播风格和爆款结构，")
        P("生成 1 条完整口播稿（含开场钩子 / 核心观点 / 金句结尾）。")
        P("")
        P("> ¥29 · 生成口播稿（vs 外包500-800元/分钟）")
    elif _is_local:
        P(f"你的账号方向是本地/实体，内容的核心目标是「让人到店」。")
        P(f"发了内容没转化，通常不是没流量，是钩子和行动号召不对。")
        P("")
        P("**现在可以做的**：输入你的店铺类型和本周活动，")
        P("生成 3 条引流脚本（含同城话题标签 / 到店钩子 / 优惠CTA）。")
        P("")
        P("> ¥29 · 生成3条引流脚本")
    else:
        P(f"基于上面的分析，可以直接生成你下一条视频的内容框架。")
        P("输入你的选题方向，结合账号历史风格，出一条可以直接拍的脚本。")
        P("")
        P("> ¥29 · 生成视频脚本框架")
    P("")

    # 复诊钩子（盲点①：报告时效性 → 订阅转化锚点）
    P(f"## 十、{_REPORT_VALID_DAYS} 天后来复诊")
    P(f"这份报告是 **{today}** 的快照，账号状态会随你的更新在变。")
    P("")
    P("**建议在以下任一情况下回来复诊：**")
    P(f"- 📅 距今满 {_REPORT_VALID_DAYS} 天（约 {expire}）——看执行后有没有往对的方向走")
    P("- 📈 粉丝或均赞出现明显变化（涨了 30%+ 或跌了 20%+）——数据变了，诊断结论也要更新")
    P("- 🎯 换了内容方向，或新发了 10 条以上——积累了新样本才能看出新规律")
    P("- 📝 用生成的脚本拍了视频，想看看数据跟之前比有没有变化——验证效果，下一条更准")
    P("- 💡 照着建议做了一段时间，想验证到底有没有效——验证闭环，让数据说话")
    P("")
    P("> 越用越准：你的视听分析结果会积累到账号归因库——多分析几次，「爆款视听公式」的置信度会越来越高。")

    return "\n".join(L)


_CN = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]


def _cn(n: int) -> str:
    return _CN[n] if 0 <= n < len(_CN) else str(n)
