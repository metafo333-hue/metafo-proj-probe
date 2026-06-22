"""冷启动 0 数据诊断 + AI 护城河 · cold_start.py（确定性·规则驱动·零 LLM·纯函数）。

来源方法论：cold-start-and-ai-moat-research.md（下称 cs-research）
  a.2 冷启动四支柱（赛道/对标/标杆拆解/起号节奏·外部参照系）
  a.3 按人群冷启动路径差异 + a.4 三段心理拖延陷阱干预
  a.5 何时从冷启动切常规（作品≥5 或单条≥1000 曝光）
  b 节 AI 时代差异化护城河（四维同质化评分 + 按人群护城河引导）

防玄学铁律（cs-research §防玄学纪律）：
- 「0 播放=内容差」误判 → 显式告知冷启动期算法未建标签=正常（sme §6.3）。
- 流量层级数值（200-500/3000/万级）标 🟨「随算法变·待外部验证」。
- 同质化四维拆解可解释·每维可证伪；置信不足标 ⚠️人工确认。
- 切换阈值标 🟨经验·引sme-research。

依赖 creator_segment.Segment（先分层再冷启动）。纯函数·零网络·零 LLM。
"""
from __future__ import annotations

from typing import Any

from .creator_segment import Segment

# 置信度防玄学阈值（与 creator_segment 对齐）
_CONFIDENCE_FLOOR = 0.6


# ──────────────────────────────────────────────────────────────────────────────
# 模式路由（冷启动 vs 混合 vs 常规·cs-research a.5）
# ──────────────────────────────────────────────────────────────────────────────

def route_mode(account: dict[str, Any]) -> str:
    """判 0 数据 → 冷启动模式（cs-research a.5 切换信号）。

    返回 "cold_start" | "hybrid" | "regular"。
      regular：作品 ≥5 条 或 任一条曝光 ≥1000（有自身样本，走常规诊断）🟨经验
      hybrid：作品 <5 但已有 1 条小爆（≥1000 曝光）→ 冷启动主框架叠真实数据
      cold_start：0 数据，两眼一抹黑
    入参容错多种键名（works_count / aweme_count / max_single_views / max_view）。
    """
    n = account.get("works_count")
    if n is None:
        n = account.get("aweme_count")
    n = n or 0
    max_views = (account.get("max_single_views")
                 or account.get("max_view") or account.get("max_like") or 0)

    if n >= 5 or max_views >= 1000:
        return "regular"
    if 1 <= n < 5 and max_views >= 1000:
        return "hybrid"  # 注：上一条已被 max_views>=1000 命中 regular，此处保留语义兜底
    return "cold_start"


# ──────────────────────────────────────────────────────────────────────────────
# 四支柱（赛道/对标/标杆拆解/起号节奏·cs-research a.2）
# ──────────────────────────────────────────────────────────────────────────────

# 对标三分类（业内共识·cs-research a.2）
BENCHMARK_TYPES = [
    ("粉丝对标", "粉丝画像相同的号（用于投流达人定向）"),
    ("形式对标", "确定视频呈现形式（口播/剧情/图文）"),
    ("内容对标", "确定内容方向/选题"),
]

# 起号节奏（🟨经验·随算法变·待外部验证·cs-research a.2）
SEEDING_RHYTHM = [
    "Day1-3：模拟真实用户刷同领域 ≥1h/天，帮算法建账号标签🟨经验·随算法变",
    "Day4-7：发 3-5 条测试视频，测不同选题/开头的反馈🟨经验",
]

# 流量层级跃迁（🟨数值随算法变·待外部验证·cs-research a.2/防玄学）
TRAFFIC_TIERS = (
    "200-500 基础池 → 点击率>8% → 3000 池 → 完播>45% → 万级池 → 互动>10% → 更高池"
    "🟨数值随算法变·待外部验证（替代「百分位对标」当冷启动诊断标尺）"
)

# 按人群的冷启动路径差异（cs-research a.3）
COLD_START_PATH: dict[Segment, dict[str, str]] = {
    Segment.FRESH_GRAD: {
        "first_block": "赛道过饱和 / 无差异化（不知做什么）",
        "first_deliver": "差异化赛道诊断（最痛点）",
        "track_lean": "避开校园/知识红海，找细分🟩(sme §5.1/§6.4)",
    },
    Segment.MIDAGE_RESTART: {
        "first_block": "技能零 + 心理重建（怕镜头）",
        "first_deliver": "经验垂类匹配 + 心理破冰路径",
        "track_lean": "行业干货（财务/法务/职场避坑）🟩(sme §5.2)",
    },
    Segment.PRO_TRANSITION: {
        "first_block": "时间碎片 + 持续输出难",
        "first_deliver": "对标定位 + ROI 预判 + 效率工具",
        "track_lean": "自身行业垂类副业🟩(sme §5.3)",
    },
    Segment.MERCHANT_LOCAL: {
        "first_block": "不懂平台机制（POI/同城）",
        "first_deliver": "行业模板 + 本地定位（城市+特色）",
        "track_lean": "本店所在行业（餐饮/美业…）🟩(sme §2/§4.3)",
    },
    Segment.KNOWLEDGE_IP: {
        "first_block": "方法论尚未提炼成独家壁垒",
        "first_deliver": "人格稀缺性定位 + 方法论独特性诊断",
        "track_lean": "把一手经验沉淀为独家方法论🟩(sme §七)",
    },
}

# 三段心理拖延陷阱干预（cs-research a.4·sme §6.1）
PSYCH_INTERVENTION: dict[Segment, str] = {
    Segment.FRESH_GRAD: "纠结期：给「够得着」的单一赛道结论，降决策焦虑（别反复横跳平台/赛道）",
    Segment.MIDAGE_RESTART: "恐惧期：推不出镜形式 + 小号/分流策略，破「怕熟人看到」的社交曝光羞耻🟨",
    Segment.PRO_TRANSITION: "完美主义锁：给「先发再说」的最低可行第一条模板，别等设备/状态/准备好",
    Segment.MERCHANT_LOCAL: "完美主义锁：用现成菜品/服务素材先发一条，别等「拍得完美」",
    Segment.KNOWLEDGE_IP: "完美主义锁：先讲一个你最熟的小知识点，别等「体系完整」再开口",
}

# 0 播放归因（防玄学铁律·sme §6.3）
ZERO_VIEW_EXPLAIN = (
    "0 播放 / 低播放在冷启动期是**正常现象，不是你的错**——"
    "新账号算法还没建立内容标签，需要几条视频喂给它认你是做什么的（sme §6.3·达观数据："
    "3 个月内流失率 ~60%，多数人误以为是自己内容差而崩溃，其实是算法机制问题）。"
)


def first_video_template(segment: Segment) -> str:
    """破完美主义锁的「最低可行第一条」模板（cs-research a.4）。"""
    base = COLD_START_PATH.get(segment, {})
    deliver = base.get("first_deliver", "先定一个你最熟的方向，拍一条 30 秒讲清楚")
    return f"最低可行第一条：围绕「{deliver}」，30-60 秒，钩子+1 个亮点+1 句 CTA，今天就发，别等准备好。"


def cold_start_diagnose(segment: Segment,
                        target_track: str | None = None) -> dict[str, Any]:
    """冷启动四支柱诊断 + 心理干预 + 0 播放解释（cs-research 代码落地设计）。

    segment 来自 creator_segment.classify_segment（先分层再冷启动）。
    target_track 为目标赛道名（可来自 _track 识别或引导问）。
    """
    path = COLD_START_PATH.get(segment, {})
    return {
        # ① 赛道选择
        "track_fit": {
            "target_track": target_track or "（未指定，先帮你定）",
            "track_lean": path.get("track_lean", "找付费意愿高、不撞车的细分🟨"),
            "saturation_note": "赛道饱和度评估须用同赛道大盘当期数据，不缓存过期🟨",
        },
        # ② 对标三类
        "benchmarks": [{"type": t, "desc": d} for t, d in BENCHMARK_TYPES],
        # ③ 标杆拆解
        "viral_teardown": "拆 30 个对标爆款的选题/开头话术/评论互动（须用当期公开数据·不缓存过期爆款）",
        # ④ 起号节奏
        "rhythm": list(SEEDING_RHYTHM),
        "traffic_tiers": TRAFFIC_TIERS,
        # 破完美主义锁
        "first_video": first_video_template(segment),
        # 破纠结/恐惧（心理干预）
        "psych_block": PSYCH_INTERVENTION.get(
            segment, "先发再说：给最低可行第一条，降决策焦虑"),
        "first_block": path.get("first_block", "（需先识别人群再定第一卡点）"),
        # 0 播放是正常
        "zero_view_explain": ZERO_VIEW_EXPLAIN,
    }


# ──────────────────────────────────────────────────────────────────────────────
# AI 时代差异化护城河（四维同质化评分·cs-research b.2/b.3/b.4）
# ──────────────────────────────────────────────────────────────────────────────

# 按行业 AI 抄不走的护城河抓手（cs-research b.4）
MOAT_HOOKS: dict[str, list[str]] = {
    "餐饮": ["老板人格", "手艺/工艺真实性", "本店故事"],
    "美食": ["老板人格", "手艺/工艺真实性", "本店故事"],
    "美业": ["真实客户前后对比", "技师手法真实性"],
    "教培": ["独特方法论", "一手教学成果（学员成果）"],
    "知识": ["不可复制的方法论", "行业内幕经验"],
    "服装": ["个人穿搭审美", "话语风格（潮牌人设）"],
    "穿搭": ["个人穿搭审美", "话语风格（潮牌人设）"],
    "实体店": ["本地信任感（实体店唯一壁垒）", "老板人格"],
}

# AI 能替代 / 不能替代（cs-research b.3·参考 sme §四）
AI_CAN_REPLACE = [
    "选题挖掘、脚本框架、文案润色（教培接受度最高·sme §2.4）",
    "标题/标签/CTA 生成",
    "批量改稿、矩阵分发",
    "数据分析、趋势识别",
]
AI_CANNOT_REPLACE = [
    "老板出镜的情感/工艺内容（餐饮·sme §2.1）",
    "真实人格、价值观、态度（72% 用户要共鸣·搜狐）",
    "一手经验、亲历案例、手艺真实性",
    "客户真实见证 / 前后对比真实素材（美业·sme §2.2）",
]

# 按人群护城河引导重点（cs-research b.5）
MOAT_GUIDE_BY_SEGMENT: dict[Segment, str] = {
    Segment.FRESH_GRAD: "找「只有你能讲」的细分（个人经历/校园细分），避开知识红海🟩",
    Segment.MIDAGE_RESTART: "把多年行业经验沉淀为独家方法论（你最大的资产·sme §5.2）",
    Segment.PRO_TRANSITION: "用本职专业建壁垒（行业 know-how 是天然护城河）",
    Segment.MERCHANT_LOCAL: "强化老板人格 + 本地真实感，不做通用模板内容",
    Segment.KNOWLEDGE_IP: "把不可复制的方法论 + 行业内幕经验产品化",
}


def _level(risk: float) -> str:
    """同质化风险分 → 等级（cs-research b.2）。"""
    if risk >= 0.66:
        return "high"
    if risk >= 0.33:
        return "mid"
    return "low"


def _match_industry(track: str | None) -> str | None:
    """赛道名 → 护城河抓手行业键（取首个命中）。"""
    if not track:
        return None
    for key in MOAT_HOOKS:
        if key in track:
            return key
    if "店" in track or "本地" in track or "探店" in track:
        return "实体店"
    return None


def moat_score(metrics: dict[str, Any] | None,
               track: str | None = None,
               segment: Segment | None = None) -> dict[str, Any]:
    """AI 护城河四维评分（cs-research b.2 代码落地）。

    metrics 四维各取值 0-1（越高=该维越「同质化/可替代」越危险），缺则视为未采集：
      topic_collision   选题撞车度（↑=风险）
      template_ratio    表达模板化程度（↑=风险）
      persona_scarcity  人格稀缺性（↓=风险·会取 1-x）
      experience_barrier 真实经验壁垒（↓=风险·会取 1-x）

    四维都未采集 → 不算分，标 ⚠️人工确认（防玄学黑盒）。
    """
    m = metrics or {}
    dims = {
        "topic_collision": m.get("topic_collision"),
        "template_ratio": m.get("template_ratio"),
        "persona_scarcity": m.get("persona_scarcity"),
        "experience_barrier": m.get("experience_barrier"),
    }
    known = {k: v for k, v in dims.items() if isinstance(v, (int, float))}

    industry = _match_industry(track)
    hooks = MOAT_HOOKS.get(industry, []) if industry else []
    guide = MOAT_GUIDE_BY_SEGMENT.get(segment) if segment else None

    base = {
        "dims": dims,
        "hooks": hooks,
        "industry": industry,
        "segment_guide": guide,
        "ai_do": list(AI_CAN_REPLACE),
        "human_do": list(AI_CANNOT_REPLACE),
    }

    # 防玄学：不足 3 维有真值 → 不出风险分（避免拍脑袋当结论）
    if len(known) < 3:
        base.update({
            "risk_score": None,
            "risk_level": "unknown",
            "confidence": 0.0,
            "needs_human": True,
            "note": "⚠️人工确认：同质化四维信号不足（<3 维），不给风险等级——"
                    "需投喂选题/表达/人格/经验维度后再评，绝不拍脑袋。",
        })
        return base

    risk = (known.get("topic_collision", 0.0)
            + known.get("template_ratio", 0.0)
            + (1 - known.get("persona_scarcity", 1.0))
            + (1 - known.get("experience_barrier", 1.0))) / 4
    confidence = len(known) / 4
    base.update({
        "risk_score": round(risk, 3),
        "risk_level": _level(risk),
        "confidence": round(confidence, 2),
        "needs_human": confidence < _CONFIDENCE_FLOOR,
        "note": ("" if confidence >= _CONFIDENCE_FLOOR
                 else f"⚠️人工确认：仅 {len(known)}/4 维有真值，结论参考为主。"),
    })
    return base


# ──────────────────────────────────────────────────────────────────────────────
# 渲染（Markdown·说人话·防玄学标·cs-research 代码落地设计）
# ──────────────────────────────────────────────────────────────────────────────

def render_cold_start_section(account: dict[str, Any],
                              segment: Segment,
                              target_track: str | None = None,
                              moat_metrics: dict[str, Any] | None = None) -> str:
    """渲染"冷启动诊断 + AI 护城河"报告段。

    可单独调用，也可由 build_report 作为 cold_start_md 注入。
    仅在 route_mode == cold_start/hybrid 时插入（常规模式由现有分析接管）。
    """
    mode = route_mode(account)
    diag = cold_start_diagnose(segment, target_track)
    moat = moat_score(moat_metrics, target_track, segment)

    L: list[str] = []
    P = L.append

    P("## 冷启动诊断（0 数据起号·你正处在最关键的窗口）")
    P("")
    if mode == "hybrid":
        P("> 你已经发了内容、还有一条小有起色——按冷启动主框架走，"
          "同时叠加那条的真实数据看（混合模式·不一刀切）。")
    else:
        P("> 你还没有足够作品数据，现有的「爆款拆解/趋势对标」都喂不动。"
          "但 0 数据不等于没法诊断——靠「外部参照系」四支柱照样给你方向。")
    P("")

    # —— 0 播放归因（防玄学·最先安抚）——
    P("**先说一句最重要的：**")
    P(f"> {diag['zero_view_explain']}")
    P("")

    # —— 第一卡点 + 心理破冰 ——
    P("**你这类创作者的第一卡点 + 怎么破**")
    P(f"- 第一卡点：{diag['first_block']}")
    P(f"- 心理破冰：{diag['psych_block']}")
    P(f"- 第一条怎么发：{diag['first_video']}")
    P("")

    # —— 四支柱 ——
    P("**冷启动四支柱（没有自身数据，就用外部参照系）**")
    tf = diag["track_fit"]
    P(f"- ① 赛道选择：目标赛道「{tf['target_track']}」 · 倾向 {tf['track_lean']}")
    P("- ② 对标三类（别自己瞎找，按这三类拉清单）：")
    for b in diag["benchmarks"]:
        P(f"    - {b['type']}：{b['desc']}")
    P(f"- ③ 标杆拆解：{diag['viral_teardown']}")
    P("- ④ 起号节奏：")
    for r in diag["rhythm"]:
        P(f"    - {r}")
    P(f"    - 流量层级跃迁标尺：{diag['traffic_tiers']}")
    P("")

    # —— AI 护城河 ——
    P("## AI 时代你的护城河（AI 抄不走的，才是你的命）")
    P("")
    P("> AI 内容泛滥、同质化飙升。诊断你「哪里会被 AI 抄走、哪里抄不走」，"
      "把省下的时间投到抄不走的核。")
    P("")
    if moat["needs_human"]:
        P(f"**同质化风险：暂不评级 ⚠️人工确认**")
        P(f"- {moat['note']}")
    else:
        level_cn = {"low": "低（差异化不错）", "mid": "中（有同质化苗头）",
                    "high": "高（同质化严重·危险）"}.get(moat["risk_level"], moat["risk_level"])
        P(f"**同质化风险等级：{level_cn}**（风险分 {moat['risk_score']}·置信度 {moat['confidence']:.0%}）")
        if moat["note"]:
            P(f"- {moat['note']}")
    P("")

    if moat["hooks"]:
        P(f"**你的行业（{moat['industry']}）里，AI 抄不走的护城河抓手：**")
        for h in moat["hooks"]:
            P(f"- {h}")
        P("")
    if moat["segment_guide"]:
        P(f"**给你这类创作者的护城河重点：** {moat['segment_guide']}")
        P("")

    P("**大胆用 AI 做这些（效率层·壳）：**")
    for x in moat["ai_do"]:
        P(f"- {x}")
    P("")
    P("**这些必须你本人来（护城河·核·AI 永远抄不走）：**")
    for x in moat["human_do"]:
        P(f"- {x}")
    P("")
    P("> 核心：AI 做「壳」，人做「核」。胜利属于「让 AI 闪耀人性光芒」的创作者——"
      "用 AI 省时间，把时间投到 AI 抄不走的真实人格与一手经验上。")
    P("")

    return "\n".join(L)
