"""维度详解知识库 · dimension_guide.py · 八维深度7层(指令4)。

承用户:八维要深度调研·丰富内容逻辑依据。每维从3层(是什么/算法/怎么提高)扩到7层——
  ① 是什么(what)  ② 由什么算(by)  ③ 你的值(score)  ④ 行业基准(bench·经验值待校准)
  ⑤ 你的分位(zone:强/中/弱·score vs zones)  ⑥ 影响什么(impact·为何重要)  ⑦ 怎么提高(how)+ 最快杠杆(lever)
纯知识常量(赛道感知处方)·渲染层引用不重算。出处=自有方法论(CM/PB/OPS)。
⚠️ bench/zones 为经验基准·标"待校准"·非平台官方分布。
"""
from __future__ import annotations

# ── 账号八维 · 7层详解 ────────────────────────────────────────────────────────
# bench=行业中位(经验) · zones=(强阈, 弱阈):≥强阈=强 / 弱阈~强阈=中 / <弱阈=弱
DIM_GUIDE = {
    "c1": {"name": "健康", "what": "账号综合健康分(0-100)·算法给不给量的体检",
           "by": "互动质量30% + 粉丝净增 + 更新节奏 + 内容趋势 + 合集化",
           "bench": 60, "zones": (75, 50),
           "impact": "上游总闸·健康分低=发什么都没初始推荐·一切流量的前提",
           "how": "稳更新节奏(断更扣分最猛)、提互动率(钩讨论)、做合集沉淀、内容别忽冷忽热",
           "lever": "稳住发布节奏(断更是健康分头号杀手)"},
    "c2": {"name": "粉丝质量", "what": "粉丝真实度·有没有水分",
           "by": "水军风险(IP集中/digg异常) + 评论真实性 + 地域多元度",
           "bench": 70, "zones": (80, 55),
           "impact": "决定粉丝资产是否可变现·水分高=粉丝多但转化为零·虚假繁荣",
           "how": "拒买粉刷量、引真实评论互动、内容真实建信任(水军评论会拉低)",
           "lever": "停止任何刷量·让真实评论自然沉淀"},
    "c3": {"name": "商业转化", "what": "把流量变成钱的能力",
           "by": "带货指数30% + 转化指数25% + 商业密度20% + 橱窗/直播15% + 消费力10%",
           "bench": 40, "zones": (60, 30),
           "impact": "直接决定变现天花板·多数账号最弱环·B端零承接=零转化",
           "how": "开橱窗/星图、内容加挂载、B端补私域承接把咨询变成交",
           "lever": "B端先补私域承接装置(主页+评论区钩子)·把已有咨询接住"},
    "c4": {"name": "内容力", "what": "内容本身的竞争力",
           "by": "爆款产出率 + 互动趋势 + 话题质量(垂直度) + 竞品差距",
           "bench": 55, "zones": (70, 45),
           "impact": "增长发动机·内容力是唯一可持续的流量来源·投放只是放大器",
           "how": "复刻自己爆款的结构、强前3秒钩子、对标竞品选题、守垂直别杂",
           "lever": "拆解自己最高赞那条的结构·复刻钩子与节奏"},
    "c5": {"name": "赛道", "what": "你这条赛道的拥挤度/蓝海度",
           "by": "搜索结果海量度(竞争密度代理)",
           "bench": 50, "zones": (65, 40),
           "impact": "决定增长难度系数·红海事倍功半·蓝海事半功倍·选错赛道再努力也累",
           "how": "红海→细分长尾切入+强差异化定位;蓝海→加速卡位、内容供给不足正是机会",
           "lever": "找一个细分长尾定位卡住·别在红海正面刚"},
    "c6": {"name": "破圈", "what": "能不能突破现有粉丝圈层",
           "by": "粉丝画像 vs 受众画像的距离(差距大=正在破圈)",
           "bench": 50, "zones": (65, 35),
           "impact": "决定增长上限·不破圈=粉丝见顶·只能在存量里打转",
           "how": "蹭赛道内相关热点、做泛化选题但守垂直、加可传播的钩子(转发型内容)",
           "lever": "做1条'垂直内核+泛化钩子'的可转发选题试破圈"},
    "c7": {"name": "评级", "what": "综合商业价值评级 A-F",
           "by": "6商业指数(合作/性价比/转化/带货/传播/明星)综合",
           "bench": 50, "zones": (65, 40),
           "impact": "对外报价/接商单的底牌·评级=商务谈判的筹码",
           "how": "综合提升各维·尤其转化与带货(评级低多因商业基础未建)",
           "lever": "优先补转化与带货两项(评级低的主因)"},
    "c8": {"name": "私域", "what": "私域变现成熟度·线索接得住吗",
           "by": "私域意图词密度 + 承接装置(主页钩子/微信/橱窗)",
           "bench": 35, "zones": (55, 25),
           "impact": "B端账号的生死线·有咨询没承接=每天在漏钱·线索接不住一切白做",
           "how": "主页+评论区置顶挂私域钩子、评论引导加微信、建私域承接SOP(黄金2h响应)",
           "lever": "今天就把主页签名+评论区置顶挂上私域钩子(零成本)"},
}

# ── 内容归因因子:每个因子是什么 + 怎么用 ─────────────────────────────────────
ATTR_GUIDE = {
    "发布时段": "不同时段受众活跃度不同。组间落差=这个时段对你互动的影响倍数·越大越该挑时段发。",
    "时长": "不同时长的完播/互动不同。落差大=时长是你的关键变量·控制在高互动时长区间。",
    "话题": "不同话题吸引不同受众。落差大=选题决定你的互动·延续高互动话题方向。",
    "挂载": "带货视频vs普通视频的互动差。落差大=挂车明显影响流量·据此决定带货频率。",
    "发布时段_default": "组间落差(spread)= 最好组均互动 ÷ 最差组均互动·≥1.5 才算这个因子真在驱动。",
}
ATTR_SPREAD_DEF = "组间落差(倍数)= 该因子下「最好取值组的均互动」÷「最差取值组的均互动」。" \
                  "≥1.5x = 这个因子真在驱动你的互动差异·优先调它;<1.5x = 影响不大。"


def _zone(score, zones) -> tuple[str, str]:
    """分位判定 → (档名, level)。"""
    if score is None:
        return "数据不足", "na"
    hi, lo = zones
    if score >= hi:
        return "强", "good"
    if score >= lo:
        return "中", "mid"
    return "弱", "bad"


def dim_detail(code: str, score) -> dict:
    """单维7层详解。"""
    g = DIM_GUIDE.get(code, {})
    bench = g.get("bench")
    zone, level = _zone(score, g.get("zones", (70, 45)))
    vs = None
    if score is not None and bench is not None:
        diff = round(score - bench)
        vs = (f"高于行业基准 {diff} 分" if diff > 0 else
              f"低于行业基准 {abs(diff)} 分" if diff < 0 else "与行业基准持平")
    return {"code": code, "name": g.get("name", code), "score": score,
            "what": g.get("what", ""), "by": g.get("by", ""),
            "bench": bench, "zone": zone, "level": level, "vs_bench": vs,
            "impact": g.get("impact", ""), "how": g.get("how", ""),
            "lever": g.get("lever", "")}


def all_dims(scores: dict) -> list[dict]:
    """8维全详解(按分升序·最弱在前·先补短板)。"""
    out = []
    for code in DIM_GUIDE:
        sc = (scores.get(code) or {}).get("score")
        out.append(dim_detail(code, sc))
    out.sort(key=lambda d: (d["score"] is None, d["score"] if d["score"] is not None else 999))
    return out


def radar_items(scores: dict) -> list[tuple]:
    """雷达图数据(label, value, benchmark)·喂 board_render._radar 增强版。"""
    items = []
    for code, g in DIM_GUIDE.items():
        sc = (scores.get(code) or {}).get("score")
        if sc is not None:
            items.append((g["name"], sc, g.get("bench")))
    return items
