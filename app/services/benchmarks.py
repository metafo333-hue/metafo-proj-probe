"""行业基准库 · 诊断的「依据」与「对比」来源(带出处·可回溯)。

解决「分析不专业·没说服力」的根因:此前给分不给依据(健康39分→so what?)。
专业分析 = 结论 + 拆解 + 原始数据 + **基准对比** + 后果推论。本模块提供「基准对比」的
真实数字与出处,全部摘自自有方法论文档(非编造),并按**赛道分型**给不同标尺
(B端线索游戏 ≠ 泛娱乐流量游戏——这是此前误判的根因)。

出处文档(运营报告/):
  CM = probe-commercial-conversion-methodology-v1.0.md
  PB = probe-conversion-playbook-and-compliance-v1.0.md
  OPS = social-account-ops-framework-v1.0(metagrow)
  CAT = all-category-track-analysis.md

⚠️ 数据可得性分级(R0.8):🟢实测 / 🟡经验区间(标待校准) / 🔴黑盒(需投喂)。
经验区间数字给范围且标注·不冒充精确。
"""
from __future__ import annotations

from typing import Any

# ── 赛道商业价值四档(单粉价值差 50-500 倍·决定用哪把尺)·出处 CM §二层A ──────────
# 关键:越垂直 B 端越赚钱·"流量大≠赚钱"·B 端玩线索游戏不玩流量游戏。
TRACK_TIERS = {
    "S": {"name": "S档·垂直B端/知识付费", "value_per_fan": "10-50元/粉 或 50-500元/线索",
          "examples": "医美·家装·招商加盟·法律财税·源头供货·知识付费",
          "game": "线索游戏", "monetize_fans": "几千精准粉即可变现(引流私域)",
          "roi": "★★★★★", "source": "CM §二层A"},
    "A": {"name": "A档·电商带货", "value_per_fan": "3-30元/粉",
          "examples": "时尚美妆·母婴·家居·兴趣小众电商",
          "game": "带货游戏", "monetize_fans": "1000粉开橱窗起",
          "roi": "★★★★", "source": "CM §二层A"},
    "B": {"name": "B档·内容消费", "value_per_fan": "1-3元/粉",
          "examples": "美食探店·剧情短剧",
          "game": "流量+恰饭", "monetize_fans": "5万粉接商单起",
          "roi": "★★★", "source": "CM §二层A"},
    "C": {"name": "C档·泛娱乐", "value_per_fan": "0.1-2元/粉(需50万+)",
          "examples": "颜值才艺·泛娱乐搞笑",
          "game": "纯流量游戏", "monetize_fans": "50万+粉才稳定变现",
          "roi": "★★", "source": "CM §二层A"},
}

# 赛道关键词 → 档位(粗分·命中即判·可被星图真值覆盖)
_TIER_KW = {
    "S": ("源头", "工厂", "供货", "供应", "批发", "厂家", "代工", "招商", "加盟",
          "医美", "口腔", "家装", "法律", "财税", "咨询", "课程", "教学", "知识",
          "餐饮食材", "食材", "原料", "B端", "代理"),
    "A": ("好物", "种草", "穿搭", "美妆", "护肤", "母婴", "家居", "测评", "带货"),
    "B": ("探店", "美食", "剧情", "短剧", "vlog", "日常"),
    "C": ("搞笑", "颜值", "才艺", "舞蹈", "段子", "娱乐"),
}

# ── 互动质量基准·出处 PB §A1 + OPS §三 ───────────────────────────────────────
ENGAGEMENT = {
    "interaction_rate_healthy": {"value": 0.03, "label": "互动率健康线 ≥3%",
        "def": "(评论+收藏+转发)÷点赞", "source": "PB §A1环3 · OPS §三"},
    "completion_good": {"value": 0.30, "label": "完播率良好 ≥30%",
        "tier": "≥50% 优秀", "black_box": True, "source": "OPS §三 · 🔴需投喂后台"},
    "exposure_floor": {"value": 5, "label": "曝光地板 = 播放≥粉丝×5",
        "def": "播放 < 粉丝量×5 = 卡曝光(标签漂移/错峰)", "source": "PB §A1环1"},
    # 商业信号价值升序(越后越值钱·私信/搜你=高意向)
    "signal_priority": ["点赞", "完播", "收藏", "评论", "转发", "关注", "私信/搜你/逛主页"],
    "signal_source": "PB §A1 · CM §六",
}

# ── 粉丝生命周期五阶段(泛娱乐)+ B端变体·出处 PB §A2 · CAT §五 ───────────────────
FAN_STAGES = [
    (0, 5000, "冷启动期", "验证内容模型+让算法打标签·禁碰转化", "无(攒信任)"),
    (5000, 50000, "初变现期", "找最适配变现路径+软植入测试", "垂直/知识/带货可变现"),
    (50000, 500000, "成长变现期", "多路径打透+私域沉淀", "商单/带货/卖课稳定"),
    (500000, 5000000, "成熟变现期", "多元变现叠加+矩阵化", "商单+带货+课+私域"),
    (5000000, 10 ** 12, "头部期", "IP商业化+品牌化", "自有品牌/IP授权"),
]
FAN_STAGES_B2B = [   # 垂直B端特殊:几千粉就能变现(引流私域)·出处 CAT §五
    (0, 10000, "B端起号期", "攒信任·建专业人设", "引流私域卖低价货/社群(几千粉即可)"),
    (10000, 50000, "B端初变现", "引流私域成交·低价课/样品", "私域高客单·几千粉月入过万可能"),
    (50000, 500000, "B端成长", "训练营/高价课/1对1/招商", "知识星球·企业培训·招商加盟"),
    (500000, 10 ** 12, "B端成熟", "课程矩阵·IP商业化", "出书·企培·生态变现"),
]
FAN_STAGE_SOURCE = "PB §A2 · CAT §五(B端变体)"

# ── 变现六路径门槛·出处 CM §二层B ────────────────────────────────────────────
MONETIZE_PATHS = {
    "广告合作": {"threshold": "5万粉+", "ceiling": "中高(粉×0.03-0.1元/条)",
                "best": "美妆/数码/财经", "source": "CM §二层B"},
    "带货佣金": {"threshold": "1000粉开橱窗", "ceiling": "高",
                "best": "电商/生活方式", "source": "CM §二层B"},
    "知识付费": {"threshold": "几千精准粉", "ceiling": "极高(9.9→3万+)",
                "best": "职场/健康/育儿/B端", "source": "CM §二层B"},
    "私域变现": {"threshold": "任意阶段", "ceiling": "最高(私域年贡献=公域5-20倍)",
                "best": "B端/知识/情感", "source": "CM §二层B"},
}

# ── 三段式植入比例(掉粉硬红线)·出处 CM §三 · PB §A2 ──────────────────────────
COMMERCE_STAGES = {
    "trust": {"range": "前20-50条", "ad_ratio": "0%", "rule": "纯价值·禁外链/商单/植入"},
    "soft": {"range": "软植入期", "ad_ratio": "≤30%(10条≤3条带货)", "rule": "产品即工具·钩好奇"},
    "explicit": {"range": "显性转化", "ad_ratio": "≤30% 硬红线", "rule": "出现主动询问才启动"},
    "redline": "植入比例>30% → 触发掉粉(硬红线)",
    "source": "CM §三 · PB §A2",
}

# 广告报价估值(粉丝/点赞 × 系数)·出处 CM §二路径①
AD_PRICE_COEF = {"low": 0.03, "high": 0.1, "unit": "元", "base": "粉丝量或点赞量",
                 "source": "CM §二路径①·🟡经验区间"}


# ══════════════════════════════════════════════════════════════════════════════
# 对比函数(账号数据 × 基准 → 拆解+依据+对比+推论)
# ══════════════════════════════════════════════════════════════════════════════

def classify_track(keywords: str | None, industry_tags: list | None = None) -> dict[str, Any]:
    """赛道分型 → S/A/B/C档 + 单粉价值 + 该玩线索还是流量游戏(选哪把尺)。"""
    hay = " ".join(filter(None, [keywords or ""] + [str(t) for t in (industry_tags or [])]))
    for tier in ("S", "A", "B", "C"):     # S 优先(B端识别)
        if any(kw in hay for kw in _TIER_KW[tier]):
            t = dict(TRACK_TIERS[tier])
            t["tier"] = tier
            t["is_b2b_leads"] = tier == "S"
            t["matched"] = next(kw for kw in _TIER_KW[tier] if kw in hay)
            return t
    t = dict(TRACK_TIERS["B"])            # 默认 B 档(中性)
    t.update({"tier": "B?", "is_b2b_leads": False, "matched": None,
              "note": "赛道关键词未命中·默认B档·建议人工确认"})
    return t


def fan_stage(follower: int | None, is_b2b: bool = False) -> dict[str, Any]:
    """粉丝量 → 生命周期阶段 + 该期任务 + 变现就绪度(B端用专属阶梯)。"""
    f = follower or 0
    table = FAN_STAGES_B2B if is_b2b else FAN_STAGES
    for lo, hi, name, task, monetize in table:
        if lo <= f < hi:
            return {"stage": name, "task": task, "monetize": monetize,
                    "follower": f, "is_b2b": is_b2b,
                    "next_threshold": hi if hi < 10 ** 11 else None,
                    "source": FAN_STAGE_SOURCE}
    return {"stage": "未知", "follower": f, "source": FAN_STAGE_SOURCE}


def engagement_breakdown(avg_like: int | None, follower: int | None,
                         structure: dict | None, avg_collect: int | None = None) -> dict[str, Any]:
    """互动质量拆解 + 基准对比(赞粉比/评赞比/收藏比 各对一条基准)。"""
    f = follower or 0
    al = avg_like or 0
    parts = []
    # 赞粉比(粗代理·赞/粉·非赞/播但无 play 时用它)
    if f:
        lpf = al / f
        verdict = ("强" if lpf >= 0.05 else "健康" if lpf >= 0.02 else "偏弱")
        parts.append({"metric": "赞粉比", "value": f"{lpf*100:.2f}%",
                      "benchmark": "≥2% 健康·≥5% 强(赞/粉粗代理)",
                      "verdict": verdict, "source": "PB §A1环3 衍生"})
    # 评论/赞(讨论度·B端=潜在咨询线索)
    s = structure or {}
    cpl = s.get("comment_per_like")
    if cpl is not None:
        v = ("极高(强讨论/潜在咨询)" if cpl >= 0.15 else "正常" if cpl >= 0.05 else "偏低(互动浅)")
        parts.append({"metric": "评论赞比", "value": f"{cpl:.3f}",
                      "benchmark": "≥0.15 = 强讨论·B端意味潜在咨询线索",
                      "verdict": v, "source": "OPS §三 用户分层(高意向=问价/评论)"})
    # 收藏/赞(实用性·B端供货=采购意向)
    kpl = s.get("collect_per_like")
    if kpl is not None:
        v = ("高(强实用/收藏待用)" if kpl >= 0.1 else "正常" if kpl >= 0.03 else "偏低")
        parts.append({"metric": "收藏赞比", "value": f"{kpl:.3f}",
                      "benchmark": "≥0.1 = 强实用内容(教程/采购参考)",
                      "verdict": v, "source": "CM §六 信号优先级(收藏>点赞)"})
    nature = s.get("nature")
    return {"parts": parts, "nature": nature,
            "summary": "·".join(f"{p['metric']}{p['verdict']}" for p in parts)}


def monetize_readiness(follower: int | None, has_commerce: bool,
                       commerce_density: float | None, track: dict) -> dict[str, Any]:
    """变现就绪度:按赛道门槛判该不该变现 + 缺什么(纠"用泛娱乐尺误判B端")。"""
    f = follower or 0
    is_b2b = track.get("is_b2b_leads")
    gates = []
    # B端门槛低(几千精准粉)·泛娱乐门槛高(5万)
    if is_b2b:
        ready = f >= 3000
        gate = "B端几千精准粉即可引流私域变现"
        path = "私域变现/知识付费(门槛:几千精准粉)"
    else:
        ready = f >= 50000
        gate = "泛娱乐需5万粉接商单·1000粉开橱窗带货"
        path = "带货(1000粉)或商单(5万粉)"
    # 当前动作
    cd = commerce_density or 0
    if cd >= 0.3:
        action = "已变现且植入≥30%·⚠️近掉粉红线(CM §三:>30%触发掉粉)"
    elif has_commerce or cd > 0:
        action = "已开始变现动作"
    else:
        action = "完全无变现动作(无橱窗/无商业内容)"
    return {
        "ready": ready, "gate": gate, "recommended_path": path,
        "current_action": action,
        "gap": ("已过门槛但零变现动作·缺承接(私域钩子/橱窗)" if ready and cd == 0
                else "门槛未到·先攒精准粉" if not ready else "变现进行中"),
        "source": "CM §二层B 变现门槛 · §三 植入红线",
    }
