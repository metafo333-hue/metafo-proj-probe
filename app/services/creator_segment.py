"""创作者分层 + 能力适配 · creator_segment.py（确定性·规则驱动·零 LLM·纯函数）。

来源方法论：creator-segmentation-adaptive-research.md（下称 seg-research）
  二、6 类 segment 主表（融合身份矩阵·商业身份×人生处境）
  三、五维能力画像（出镜/剪辑/时间/预算/团队）+ feasibility_filter
  四、三轴适配（人群×阶段 诊断重点矩阵·落规则表）

防玄学铁律（seg-research §六）：
- 信号不足无法判定 → 返回 unknown + 建议人工确认，绝不硬猜。
- confidence < 0.6 → 标 "⚠️人工确认"，不直接当结论出报告。
- 每条规则带 evidence 出处（sme 章节 / 平台规则），可证伪。
- 能力画像由信号 / 引导入参采集，不由模型臆测。
- 阈值 / 阶段切换标 "🟨经验·引sme-research"。
- 方案难度 ≤ 创作者能力天花板（feasibility_filter 自动降级）。

纯函数·零副作用·零网络·零 LLM。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# 置信度防玄学阈值（seg-research §六）
_CONFIDENCE_FLOOR = 0.6


class Segment(str, Enum):
    MERCHANT_LOCAL = "merchant_local"   # 本地商家号
    PRO_TRANSITION = "pro_transition"   # 在职转型 IP
    FRESH_GRAD = "fresh_grad"           # 应届起号
    MIDAGE_RESTART = "midage_restart"   # 中年再就业
    KNOWLEDGE_IP = "knowledge_ip"       # 知识口播 IP
    MCN_MATRIX = "mcn_matrix"           # MCN / 矩阵
    UNKNOWN = "unknown"                 # 信号不足·不硬猜（防玄学）


class Stage(str, Enum):
    COLD_START = "cold_start"   # 0 数据
    SEEDING = "seeding"         # 起号期 <5 条
    GROWTH = "growth"           # 成长期
    MATURE = "mature"           # 成熟期


# segment 中文名 + 核心目标 + 诊断第一重点（seg-research §2.1 主表）
_SEGMENT_META: dict[Segment, dict[str, str]] = {
    Segment.MERCHANT_LOCAL: {
        "name": "本地商家号",
        "goal": "到店转化",
        "focus": "本地流量 + POI 核销归因",
        "tone": "「这条能带多少人到店」",
    },
    Segment.PRO_TRANSITION: {
        "name": "在职转型 IP",
        "goal": "副业 ROI",
        "focus": "人设信任 + 副业投产比",
        "tone": "「省你 3 小时 + ROI 可验证」",
    },
    Segment.FRESH_GRAD: {
        "name": "应届起号号",
        "goal": "低成本起号",
        "focus": "赛道定位 + 差异化",
        "tone": "「告诉你做什么方向，不白走弯路」",
    },
    Segment.MIDAGE_RESTART: {
        "name": "中年再就业号",
        "goal": "稳健变现",
        "focus": "经验垂类 + 傻瓜化执行",
        "tone": "「你的经验 + 我的脚本，先做起来」",
    },
    Segment.KNOWLEDGE_IP: {
        "name": "知识口播 IP",
        "goal": "信任变现",
        "focus": "人格稀缺性 + 方法论独特性",
        "tone": "「你的不可替代在哪」",
    },
    Segment.MCN_MATRIX: {
        "name": "MCN / 矩阵",
        "goal": "规模化",
        "focus": "账号协同 + 单位产出 ROI",
        "tone": "「哪条线该加码 / 该砍」",
    },
    Segment.UNKNOWN: {
        "name": "未识别（信号不足）",
        "goal": "先补采创作者画像信号",
        "focus": "需 3-5 问引导补全身份信号再诊断",
        "tone": "「先确认你是谁，再给方向」",
    },
}


@dataclass
class CapabilityProfile:
    """五维能力画像（seg-research §3.1）。取值缺省 None = 未采集（防臆测）。"""
    on_camera: str | None = None     # "willing" | "voice_only" | "unwilling"
    editing: str | None = None       # "none" | "jianying" | "pro"
    time_budget: str | None = None   # "fragment" | "medium" | "ample"
    budget: str | None = None        # "lt30_monthly" | "50_150_monthly" | "500_1500_onetime"
    team: str | None = None          # "solo" | "couple" | "small" | "mcn"

    def known_dims(self) -> int:
        return sum(1 for v in (self.on_camera, self.editing, self.time_budget,
                               self.budget, self.team) if v)


@dataclass
class SegmentResult:
    segment: Segment
    secondary: Segment | None
    stage: Stage
    confidence: float                 # 0-1 · <0.6 标 ⚠️需人工确认（防玄学）
    evidence: list[str] = field(default_factory=list)  # 判定依据出处（可证伪）
    capability: CapabilityProfile | None = None

    @property
    def needs_human(self) -> bool:
        """confidence < 0.6 或 unknown → 不直接当结论（seg-research §六）。"""
        return self.segment == Segment.UNKNOWN or self.confidence < _CONFIDENCE_FLOOR


# ──────────────────────────────────────────────────────────────────────────────
# 阶段推断（seg-research §四·阶段取值 + cold-start a.5 切换信号）
# ──────────────────────────────────────────────────────────────────────────────

def _infer_stage(signals: dict[str, Any]) -> Stage:
    """🟨经验·引sme-research：按作品数 + 单条曝光判账号阶段。
    冷启动(0数据) / 起号(<5条) / 成长 / 成熟。"""
    works = signals.get("works_count")
    if works is None:
        works = signals.get("aweme_count")
    fol = signals.get("follower") or 0
    max_views = signals.get("max_single_views") or 0

    works = works or 0
    # 真 0 数据（无作品且无曝光）→ 冷启动；有任一作品 → 至少起号期
    if works == 0 and max_views < 1000:
        return Stage.COLD_START
    if works < 5 and max_views < 1000:
        return Stage.SEEDING
    if works < 5:
        # 作品少但已有曝光破千 → 已脱离冷启动，按起号期算
        return Stage.SEEDING
    if fol >= 50_000:
        return Stage.MATURE
    return Stage.GROWTH


# ──────────────────────────────────────────────────────────────────────────────
# segment 分类（规则优先·可解释·非黑盒·每条带 evidence）
# ──────────────────────────────────────────────────────────────────────────────

# 知识口播内容信号（次判定·seg-research §2.1 knowledge_ip）
_KNOWLEDGE_KW = ("口播", "方法论", "干货", "知识", "科普", "财务", "法务",
                 "职场避坑", "认知", "思维", "心法", "课程")


def classify_segment(signals: dict[str, Any]) -> SegmentResult:
    """6 类 segment 识别（融合身份矩阵·seg-research §2.1/§5.3）。

    输入 signals：账号信号 + 可选引导入参，常见键：
      blue_v / poi_bound（商家信号）· bound_accounts（MCN）
      age_band（"35_50" 等）· employ_status（"fresh_grad"|"unemployed"|"in_job"）
      signature / hashtags（内容信号）· works_count / max_single_views / follower（阶段）

    无足够信号 → Segment.UNKNOWN + 建议人工确认（不硬猜·防玄学）。
    """
    ev: list[str] = []
    stage = _infer_stage(signals)

    # 1) 商家信号：蓝V认证 / POI 绑定 / 橱窗 → 本地商家（高置信）
    if signals.get("blue_v") or signals.get("poi_bound"):
        ev.append("blue_v/poi_bound=True → 商家号（龙腾电商账号分类）")
        return SegmentResult(Segment.MERCHANT_LOCAL, None, stage, 0.9, ev)

    # 2) MCN：>=5 绑定账号或矩阵标识（⚠️门槛随平台规则变·seg-research §六）
    if (signals.get("bound_accounts") or 0) >= 5 or signals.get("is_matrix"):
        ev.append("bound_accounts>=5 → MCN（星图 MCN 入驻≥5红人门槛·⚠️门槛随平台规则变·待复核）")
        return SegmentResult(Segment.MCN_MATRIX, None, stage, 0.85, ev)

    # 3) 人生处境：靠引导问采集（age_band / employ_status）判 应届/中年/在职
    age = signals.get("age_band")
    employ = signals.get("employ_status")

    if employ == "fresh_grad":
        ev.append("employ=fresh_grad → 应届起号（sme §5.1）")
        return SegmentResult(Segment.FRESH_GRAD, None, stage, 0.8, ev)

    if age == "35_50" and employ == "unemployed":
        ev.append("35-50 + 失业 → 中年再就业（sme §5.2）")
        return SegmentResult(Segment.MIDAGE_RESTART, None, stage, 0.8, ev)

    # 4) 知识口播：内容形态=口播 + 方法论 → knowledge_ip
    text = (signals.get("signature") or "") + " " + " ".join(signals.get("hashtags") or [])
    hit_kw = [k for k in _KNOWLEDGE_KW if k in text]
    if employ == "in_job":
        # 在职 + 强知识口播信号 → knowledge_ip；否则 → 在职转型副业
        if len(hit_kw) >= 2:
            ev.append(f"在职 + 口播/方法论信号({'/'.join(hit_kw[:3])}) → 知识口播 IP（seg-research §2.1）")
            return SegmentResult(Segment.KNOWLEDGE_IP, Segment.PRO_TRANSITION,
                                 stage, 0.7, ev)
        ev.append("在职 + 副业 → 在职转型（sme §5.3）")
        return SegmentResult(Segment.PRO_TRANSITION, None, stage, 0.75, ev)

    # 无 employ 信号但强知识口播内容 → knowledge_ip 弱判定（置信压到边界·提示人工确认）
    if len(hit_kw) >= 2:
        ev.append(f"口播/方法论内容信号({'/'.join(hit_kw[:3])}) → 疑似知识口播 IP（缺人生处境信号·置信压低）")
        return SegmentResult(Segment.KNOWLEDGE_IP, None, stage, 0.55, ev)

    # 5) 兜底：信号不足 → UNKNOWN + 建议人工确认（绝不硬猜·防玄学 seg-research §六）
    ev.append("无商家/MCN/人生处境/内容信号 → 信号不足，需 3-5 问引导补全身份再判定（不硬猜）")
    return SegmentResult(Segment.UNKNOWN, None, stage, 0.0, ev)


# ──────────────────────────────────────────────────────────────────────────────
# 五维能力画像构建（由信号 + 引导入参·不臆测·seg-research §3.1）
# ──────────────────────────────────────────────────────────────────────────────

def build_capability_profile(signals: dict[str, Any]) -> CapabilityProfile:
    """从引导入参 / 显式信号构建五维能力画像。
    未提供的维度留 None（= 未采集），绝不由内容臆测（防玄学 seg-research §六）。"""
    cap = signals.get("capability") or {}

    def pick(key: str, allowed: set[str]) -> str | None:
        v = signals.get(key)
        if v is None:
            v = cap.get(key)
        return v if v in allowed else None

    return CapabilityProfile(
        on_camera=pick("on_camera", {"willing", "voice_only", "unwilling"}),
        editing=pick("editing", {"none", "jianying", "pro"}),
        time_budget=pick("time_budget", {"fragment", "medium", "ample"}),
        budget=pick("budget", {"lt30_monthly", "50_150_monthly", "500_1500_onetime"}),
        team=pick("team", {"solo", "couple", "small", "mcn"}),
    )


# ──────────────────────────────────────────────────────────────────────────────
# feasibility_filter（方案难度 ≤ 能力天花板·够不着自动降级·seg-research §3.2/§5.4）
# ──────────────────────────────────────────────────────────────────────────────

# 动作 → 所需能力（seg-research §5.4 ACTION_REQ）
ACTION_REQ: dict[str, dict[str, Any]] = {
    "complex_montage": {"editing": {"pro"}, "time_budget": {"ample"}},  # 复杂分镜
    "series_drama": {"editing": {"jianying", "pro"}, "time_budget": {"medium", "ample"}},
    "before_after": {"editing": {"jianying", "pro"}},                   # 美业前后对比
    "voice_over": {"on_camera": {"voice_only", "willing"}},             # 口播
    "image_text": {},                                                  # 图文笔记·零门槛兜底
    "one_click_video": {},                                            # 一键成片·零门槛
}

# 够不着时的次优替代链（seg-research §5.4 DOWNGRADE）
DOWNGRADE: dict[str, str] = {
    "complex_montage": "voice_over",
    "series_drama": "voice_over",
    "before_after": "image_text",
    "voice_over": "image_text",
}


def _meets(req: dict[str, Any], cap: CapabilityProfile) -> bool | None:
    """动作所需能力是否满足。
    返回 True=满足 / False=明确不满足 / None=能力未采集无法判定（防玄学不硬过）。"""
    undetermined = False
    for dim, allowed in req.items():
        have = getattr(cap, dim, None)
        if have is None:
            undetermined = True
            continue
        if have not in allowed:
            return False
    return None if undetermined else True


def feasibility_filter(actions: list[dict[str, Any]],
                       cap: CapabilityProfile) -> list[dict[str, Any]]:
    """过滤够不着的动作 → 自动降级到次优（铁律：方案难度 ≤ 能力天花板）。

    action 形如 {"kind": "complex_montage", "title": "..."}。
    - 满足 → 原样保留。
    - 明确不满足 → 沿 DOWNGRADE 链降级 + 标 note。
    - 能力未采集（无法判定）→ 保留但标 ⚠️待确认能力（不硬过·不硬降·防玄学）。
    """
    out: list[dict[str, Any]] = []
    for a in actions:
        kind = a.get("kind", "")
        verdict = _meets(ACTION_REQ.get(kind, {}), cap)

        if verdict is True:
            out.append(dict(a))
            continue
        if verdict is None:
            item = dict(a)
            item["note"] = "⚠️待确认能力——补全能力画像后才能判是否够得着"
            out.append(item)
            continue

        # 明确不满足 → 沿降级链找够得着的形式
        cur = kind
        seen = {cur}
        downgraded = None
        while cur in DOWNGRADE:
            cur = DOWNGRADE[cur]
            if cur in seen:  # 防环
                break
            seen.add(cur)
            if _meets(ACTION_REQ.get(cur, {}), cap) is not False:
                downgraded = cur
                break
        if downgraded:
            item = dict(a)
            item["kind"] = downgraded
            item["note"] = f"已按能力降级（原 {kind} 够不着 → {downgraded}）"
            out.append(item)
        else:
            item = dict(a)
            item["kind"] = "image_text"
            item["note"] = f"已降到零门槛图文（原 {kind} 及降级链均够不着）"
            out.append(item)
    return out


# ──────────────────────────────────────────────────────────────────────────────
# 三轴适配规则表（人群 × 阶段 · 诊断重点 + 阈值·seg-research §四）
# ──────────────────────────────────────────────────────────────────────────────

# (segment, stage) → {focus 诊断重点, freq 频次阈值, form 推荐形式, evidence}
# 阈值全引 sme-research·标 🟨经验
ADAPT_MATRIX: dict[tuple[Segment, Stage], dict[str, str]] = {
    (Segment.MERCHANT_LOCAL, Stage.COLD_START): {
        "focus": "选行业模板 + 本地定位（城市+特色）",
        "freq": "投流型 1-2 条/周（非 5-7）🟨经验·引sme §2.1",
        "form": "含 POI / 同城话题脚本",
    },
    (Segment.MERCHANT_LOCAL, Stage.SEEDING): {
        "focus": "POI 绑定 + 同城话题",
        "freq": "投流型 1-2 条/周🟨经验·引sme §2.1",
        "form": "行业×本地脚本（29 元/条 or 99/月）",
    },
    (Segment.MERCHANT_LOCAL, Stage.GROWTH): {
        "focus": "到店转化率优化",
        "freq": "1-2 条/周 + 预拍批量🟨经验·引sme §2.1",
        "form": "菜品/服务视觉流（无人出镜可）",
    },
    (Segment.MERCHANT_LOCAL, Stage.MATURE): {
        "focus": "矩阵化 / 投流 ROI",
        "freq": "批量预拍🟨经验·引sme §2.1",
        "form": "多门店矩阵脚本",
    },
    (Segment.FRESH_GRAD, Stage.COLD_START): {
        "focus": "赛道差异化诊断（最痛点·不知做什么）",
        "freq": "不设频次，先定位🟨经验·引sme §8.2",
        "form": "赛道诊断 + 示例脚本（0元体验→29解锁）",
    },
    (Segment.FRESH_GRAD, Stage.SEEDING): {
        "focus": "起号节奏 + 完播",
        "freq": "3-5 条测试🟨经验·引sme §6",
        "form": "差异化标签 + 测试脚本",
    },
    (Segment.FRESH_GRAD, Stage.GROWTH): {
        "focus": "找到差异化标签",
        "freq": "稳定产出🟨经验",
        "form": "细分赛道深耕脚本",
    },
    (Segment.FRESH_GRAD, Stage.MATURE): {
        "focus": "变现路径选择",
        "freq": "稳定产出🟨经验",
        "form": "变现方案",
    },
    (Segment.MIDAGE_RESTART, Stage.COLD_START): {
        "focus": "经验垂类匹配 + 心理破冰（怕镜头）",
        "freq": "不设频次，先破冰🟨经验·引sme §5.2/§8.2",
        "form": "行业垂类脚本包30条（199-499 一次性）",
    },
    (Segment.MIDAGE_RESTART, Stage.SEEDING): {
        "focus": "傻瓜化产出节奏",
        "freq": "傻瓜化低频🟨经验·引sme §5.2",
        "form": "行业干货图文 / 一键成片",
    },
    (Segment.MIDAGE_RESTART, Stage.GROWTH): {
        "focus": "信任沉淀",
        "freq": "稳定低频🟨经验",
        "form": "经验方法论沉淀脚本",
    },
    (Segment.MIDAGE_RESTART, Stage.MATURE): {
        "focus": "一次性变现包",
        "freq": "稳定低频🟨经验",
        "form": "经验产品化方案",
    },
    (Segment.PRO_TRANSITION, Stage.COLD_START): {
        "focus": "对标定位 + ROI 预判",
        "freq": "1-2 条/周试水🟨经验·引sme §5.3",
        "form": "三类对标清单 + 效率方案（99/月试用）",
    },
    (Segment.PRO_TRANSITION, Stage.SEEDING): {
        "focus": "效率工具 + 批量",
        "freq": "3-5 条/周（有 2h）🟨经验·引sme §5.3/§8.2",
        "form": "批量脚本 + 选题库",
    },
    (Segment.PRO_TRANSITION, Stage.GROWTH): {
        "focus": "人设强化 + 数据看板",
        "freq": "3-5 条/周🟨经验·引sme §5.3",
        "form": "批量脚本 + 选题库 + 看板（99 元/月订阅）",
    },
    (Segment.PRO_TRANSITION, Stage.MATURE): {
        "focus": "副业规模化",
        "freq": "批量🟨经验",
        "form": "矩阵/规模化方案",
    },
}

# knowledge_ip / mcn_matrix 无逐阶段细表 → 落 segment 级缺省（仍带诊断重点·不空）
_SEGMENT_FALLBACK_ADAPT: dict[Segment, dict[str, str]] = {
    Segment.KNOWLEDGE_IP: {
        "focus": "人格稀缺性 + 方法论壁垒 + 完播率",
        "freq": "稳定产出·重质不重量🟨经验",
        "form": "口播模板（钩子+亮点+CTA·30 秒可拍）",
    },
    Segment.MCN_MATRIX: {
        "focus": "账号间协同 + 内容复用率 + 单位产出 ROI",
        "freq": "矩阵分发·按号定🟨经验",
        "form": "矩阵 SOP + 复用脚本库",
    },
}


def adapt_focus(segment: Segment, stage: Stage) -> dict[str, str]:
    """三轴适配：取 (人群×阶段) 的诊断重点 + 频次阈值 + 推荐形式。
    无精确命中 → 落 segment 级缺省；UNKNOWN → 提示先补信号。"""
    if segment == Segment.UNKNOWN:
        return {
            "focus": "先补采创作者画像信号（3-5 问引导）再做适配诊断",
            "freq": "—（信号不足，不设阈值）",
            "form": "—（先确认身份）",
        }
    hit = ADAPT_MATRIX.get((segment, stage))
    if hit:
        return dict(hit)
    return dict(_SEGMENT_FALLBACK_ADAPT.get(
        segment, {"focus": _SEGMENT_META[segment]["focus"],
                  "freq": "按账号实际定🟨经验", "form": "按 segment 适配"}))


# ──────────────────────────────────────────────────────────────────────────────
# 渲染（Markdown·说人话·带 segment 标签 + 防玄学置信度·seg-research §5.1）
# ──────────────────────────────────────────────────────────────────────────────

def render_segment_section(signals: dict[str, Any],
                           result: SegmentResult | None = None,
                           actions: list[dict[str, Any]] | None = None) -> str:
    """渲染"创作者分层 + 能力适配"报告段。

    可单独调用，也可由 build_report 作为 segment_md 注入。
    result 不传则内部计算；actions 给定则跑 feasibility_filter 展示降级。
    """
    if result is None:
        cap = build_capability_profile(signals)
        result = classify_segment(signals)
        result.capability = cap

    seg = result.segment
    meta = _SEGMENT_META[seg]
    adapt = adapt_focus(seg, result.stage)
    stage_cn = {
        Stage.COLD_START: "冷启动（0 数据）",
        Stage.SEEDING: "起号期（<5 条）",
        Stage.GROWTH: "成长期",
        Stage.MATURE: "成熟期",
    }[result.stage]

    L: list[str] = []
    P = L.append

    P("## 你是哪类创作者（先认清，才好对症）")
    P("")
    P("> 不同身份的人，诊断重点完全不同——商家看到店、IP 看人设、新人看赛道。"
      "先识别你属于哪一类，后面所有建议才够得着。")
    P("")

    # —— 身份判定（带防玄学置信度）——
    if result.needs_human:
        P(f"**判定结果：{meta['name']} ⚠️人工确认**")
        P("")
        P(f"- 我手头的信号还不足以确定你的身份（置信度 {result.confidence:.0%}，低于 60% 不当结论）。")
        P("- 为什么不硬猜：硬给一个身份，后面整套诊断都会跑偏，不如先问清楚。")
        P("- 建议补这几问：你是实体店主 / 在职转型 / 应届起号 / 中年再就业？主要做什么内容？有没有蓝V或绑定多个号？")
    else:
        conf_tag = "" if result.confidence >= _CONFIDENCE_FLOOR else " ⚠️人工确认"
        P(f"**判定结果：{meta['name']}（置信度 {result.confidence:.0%}{conf_tag}）**")
        if result.secondary:
            P(f"- 次身份：{_SEGMENT_META[result.secondary]['name']}（话术会微调，主诊断按主身份走）")
        P("")
        P(f"- 你的核心目标：**{meta['goal']}**")
        P(f"- 这类号诊断第一重点：**{meta['focus']}**")
        P(f"- 给你的话术调性：{meta['tone']}")
    P("")

    # —— 判定依据（可证伪·防黑盒）——
    if result.evidence:
        P("**怎么判断的（不是拍脑袋，每条都有出处）**")
        for e in result.evidence:
            P(f"- {e}")
        P("")

    # —— 三轴适配：人群 × 阶段 ——
    P(f"**结合你的阶段「{stage_cn}」，这阶段该聚焦：**")
    P(f"- 诊断重点：{adapt['focus']}")
    P(f"- 内容频次：{adapt['freq']}")
    P(f"- 推荐形式：{adapt['form']}")
    P("")

    # —— 能力画像 + feasibility 降级 ——
    cap = result.capability
    if cap is not None and cap.known_dims() > 0:
        P("**你的能力画像（决定方案够不够得着）**")
        dims = [
            ("出镜意愿", cap.on_camera, {"willing": "愿出镜", "voice_only": "口播only", "unwilling": "不愿出镜"}),
            ("剪辑能力", cap.editing, {"none": "不会剪", "jianying": "剪映会", "pro": "专业"}),
            ("时间投入", cap.time_budget, {"fragment": "碎片(<30min/天)", "medium": "中(1-2h)", "ample": "充裕"}),
            ("预算", cap.budget, {"lt30_monthly": "<30/月", "50_150_monthly": "50-150/月", "500_1500_onetime": "500-1500一次性"}),
            ("团队", cap.team, {"solo": "单人", "couple": "夫妻店", "small": "小团队", "mcn": "MCN"}),
        ]
        for label, val, mapping in dims:
            if val:
                P(f"- {label}：{mapping.get(val, val)}")
        P("")
        if actions:
            filtered = feasibility_filter(actions, cap)
            adjusted = [a for a in filtered if a.get("note")]
            if adjusted:
                P("**⚠️ 有几个动作按你的能力做了调整（铁律：不会剪就不给复杂剪辑脚本）**")
                for a in adjusted:
                    title = a.get("title") or a.get("kind")
                    P(f"- {title} → {a['note']}")
                P("")
    else:
        P("**能力画像：未采集**")
        P("- 我还不知道你会不会剪辑、愿不愿出镜、有多少时间——这些决定方案够不够得着。")
        P("- 补上这几项（出镜/剪辑/时间/预算/团队），我才能保证给的方案你真的做得出来，而不是给一堆拍不出的脚本。")
        P("")

    return "\n".join(L)
