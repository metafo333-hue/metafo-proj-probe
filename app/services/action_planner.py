"""行动清单 + 优先级排序 · action_planner.py（确定性·规则驱动·零 LLM）。

来源方法论：04-output-delivery/action-priority-adaptive-research.md
  §二 诊断结论 → 行动项映射（规则表·零 LLM）
  §三 优先级排序 P=(ROI×w)/(难度×w)×(紧急×w) + 硬覆盖（合规置顶/阶段红线）
  §三.3 人群难度系数 + max_actions 强制截断（破拖延·注意力稀缺）
  §三.4 行业/阶段排序差异

诚实铁律（R0.8 防玄学）：
- 诊断→行动映射 🟩 规则确定（查表·禁 LLM 自由发挥·无映射则不生成）
- ROI/难度/紧急权重 🟨「初始经验权重·需校准」（每项输出 score_explain 打分拆解·可解释）
- 完成标准：结构类 🟩 probe 可自动复检 / 效果类 🟥 需投喂后台·禁外推
- 强制 max_actions 截断（2-3 件）·阶段红线项移入「别做」清单·不参与排序

纯函数·零副作用·零网络·零 LLM。本模块只**消费**各诊断模块产出的结论码，不重新诊断。
"""
from __future__ import annotations

from typing import Any

from .account_report import _track, _is_business

# ──────────────────────────────────────────────────────────────────────────────
# §二 诊断结论码 → 行动项模板（规则驱动·单一真源）
# 每条：tmpl 模板（含 {占位符}·运行时填账号数据）+ roi/difficulty/urgency（1-5）
#       + done_std 完成标准 + 可选 hard_top（合规硬置顶）/ industry_gate（行业门控）
#       + kind 排序原则归类（positioning/validate_model/volume/pick_path/convert/
#         private_domain/monetize·对接 §三.4 阶段 prefer/forbid）
# ──────────────────────────────────────────────────────────────────────────────
_DIAGNOSIS_TO_ACTION: dict[str, dict[str, Any]] = {
    "funnel_break_completion": {
        "tmpl": "下条视频删掉前 {head_sec} 秒片头/自我介绍，改成对着「{target_user}」说的痛点句开头",
        "roi": 5, "difficulty": 2, "urgency": 3, "kind": "validate_model",
        "done_std": {"type": "blackbox", "desc": "完播率较均值↑（需后台投喂·🟥黑盒）", "need_feed": True},
    },
    "funnel_break_interaction": {
        "tmpl": "下周拍的 3 条里，每条结尾加一个选择题引评论",
        "roi": 3, "difficulty": 3, "urgency": 3, "kind": "volume",
        "done_std": {"type": "blackbox", "desc": "评论率 ≥3%（需后台投喂·🟥黑盒）", "need_feed": True},
    },
    "homepage_bio_incomplete": {
        "tmpl": "把简介改成：「{who} + 给{whom} + {what}」（5 分钟搞定）",
        "roi": 4, "difficulty": 1, "urgency": 3, "kind": "positioning",
        "done_std": {"type": "structural", "desc": "简介含三要素（probe 可自动复检·🟩）"},
    },
    "homepage_pin_wrong": {
        "tmpl": "置顶换成你转化最高那条（第 {pin_n} 条·美业换前后对比条）",
        "roi": 4, "difficulty": 1, "urgency": 3, "kind": "convert",
        "done_std": {"type": "structural", "desc": "置顶=高互动/对比条（probe 可自动复检·🟩）"},
    },
    "homepage_no_poi": {
        "tmpl": "今天去抖音后台「我的-企业服务」挂上门店 POI 地址",
        "roi": 4, "difficulty": 2, "urgency": 4, "kind": "convert",
        "industry_gate": ["餐饮", "美业", "生活服务"],   # 仅到店类触发
        "done_std": {"type": "structural", "desc": "POI 字段存在（probe 可自动复检·🟩）"},
    },
    "tag_drift": {
        "tmpl": "未来 10 条只发「{focus_topic}」这一个方向，先别东一榔头西一棒",
        "roi": 3, "difficulty": 2, "urgency": 4, "kind": "positioning",
        "done_std": {"type": "structural", "desc": "近 10 条 hashtag 离散度↓（probe 可自动复检·🟩）"},
    },
    "private_domain_missing": {
        "tmpl": "下条结尾加：「想要完整方案，私信我『{keyword}』」+ 开私信自动回复",
        "roi": 4, "difficulty": 2, "urgency": 3, "kind": "private_domain",
        "done_std": {"type": "structural", "desc": "末段有私信钩（文本可测·🟩）/ 私信量↑（🟥需投喂）"},
    },
    "compliance_hit": {
        "tmpl": "把简介/文案里的「{bad_term}」改成「{good_term}」（不改有封号风险）",
        "roi": 3, "difficulty": 1, "urgency": 5, "kind": "positioning",
        "hard_top": True,            # 硬置顶·覆盖打分（封号=转化归零）
        "done_std": {"type": "structural", "desc": "该违规词消失（probe 可复扫·🟩）"},
    },
    "topic_drought": {
        "tmpl": "按你赛道生成的 3 个选题，本周各拍 1 条",
        "roi": 3, "difficulty": 4, "urgency": 2, "kind": "volume",
        "done_std": {"type": "structural", "desc": "本周发 3 条（可测·🟩）"},
    },
    "collection_messy": {
        "tmpl": "把同主题作品整理进 1 个合集，方便新观众一次看够",
        "roi": 2, "difficulty": 2, "urgency": 2, "kind": "convert",
        "done_std": {"type": "structural", "desc": "已建合集（probe 可自动复检·🟩）"},
    },
}

# §三.3 人群 → 难度系数 + 同时给几件 + 语气
# diff_mult：难度系数（<1 = 该人群更怕难·难度放大不利项；语气傻瓜化）
# max_actions：强制截断件数（在职/中年失业带宽窄·只给 2 件）
_PERSONA_ADAPT: dict[str, dict[str, Any]] = {
    "实体店主":  {"diff_mult": 1.0, "max_actions": 3, "tone": "直白·到店导向"},
    "应届生":    {"diff_mult": 1.0, "max_actions": 3, "tone": "鼓励·定位导向"},
    "中年失业":  {"diff_mult": 1.25, "max_actions": 2, "tone": "傻瓜化·去术语·步骤到按钮"},
    "在职转型":  {"diff_mult": 1.2, "max_actions": 2, "tone": "效率·一次配置长期生效优先"},
}
_DEFAULT_PERSONA = {"diff_mult": 1.0, "max_actions": 3, "tone": "通用"}

# §三.4 阶段 → 排序首要原则（prefer 的 kind 加权前置）+ 红线「别做」
_STAGE_PRIORITY: dict[str, dict[str, list[str]]] = {
    "冷启动": {"prefer": ["positioning"], "forbid": ["monetize", "volume", "convert", "private_domain"]},
    "起号期": {"prefer": ["validate_model", "positioning"], "forbid": ["monetize"]},
    "成长期": {"prefer": ["volume", "pick_path"], "forbid": []},
    "成熟期": {"prefer": ["convert", "private_domain"], "forbid": []},
}

# 🟨 初始经验权重·attribution_cache 回测后调（防玄学：标注·非铁律）
_W_ROI, _W_DIFF, _W_URG = 1.0, 1.0, 0.8

# track 名（account_report._track 输出）→ 行业（对接 industry_gate / 排序偏好）
_TRACK_TO_INDUSTRY: list[tuple[tuple[str, ...], str]] = [
    (("美食",), "餐饮"),
    (("美妆", "时尚", "护肤", "穿搭"), "美业"),
    (("母婴", "育儿"), "母婴"),
    (("知识", "科普", "成长", "励志"), "知识IP"),
    (("健身", "运动"), "生活服务"),
    (("供货", "B2B", "产业带"), "B端"),
]


def _industry_of(account: dict[str, Any]) -> str:
    text = (account.get("signature") or "") + " " + \
           " ".join(account.get("hashtags") or []) + " " + (account.get("nickname") or "")
    track_name, _ = _track(text)
    if _is_business(text):
        return "B端"
    probe = track_name + " " + text
    for kws, ind in _TRACK_TO_INDUSTRY:
        if any(k in probe for k in kws):
            return ind
    return "通用"


def _score(roi: int, difficulty: float, urgency: int) -> float:
    """P = (ROI×w_roi) / (难度×w_diff) × (紧急×w_urg)。难度做分母→高ROI低难度的快赢冒头。"""
    denom = max(difficulty * _W_DIFF, 0.1)   # 防除零
    return (roi * _W_ROI) / denom * (urgency * _W_URG)


def plan_actions(diagnoses: list[dict[str, Any]] | None,
                 track: str | None = None,
                 stage: str | None = None,
                 persona: str | None = None,
                 account: dict[str, Any] | None = None,
                 capability: dict[str, Any] | None = None) -> dict[str, Any]:
    """诊断结论码 → 排序后的行动清单。确定性·零 LLM。

    Args:
        diagnoses: 各诊断模块的结构化结论 [{"code": str, "params": {...}}, ...]。
                   code 必须命中 _DIAGNOSIS_TO_ACTION，否则跳过（禁凭空生成）。
        track:     赛道名（来自 _track·用于行业门控/排序偏好；不传则从 account 推断）。
        stage:     账号阶段（冷启动/起号期/成长期/成熟期·驱动 prefer/forbid）。
        persona:   人群（驱动难度系数 + max_actions 截断 + 语气）。
        account:   账号字典（用于推断行业·当 track 未给时）。
        capability:{team, can_on_screen, budget, in_job}·调难度（团队拍视频更易等）。

    Returns:
        {
          top_actions: [{text, kind, done_std, P, score_explain}],  # 已排序·已截断 N 件
          dont_do:     [{text, why}],     # 阶段红线·别做清单（不参与排序）
          backlog:     [...],             # 排在 N 件之后的（折叠）
          max_actions: int,
          persona_tone: str,
          weight_note: str,               # 🟨 权重经验值标注（防玄学）
        }
    """
    diagnoses = diagnoses or []
    pa = _PERSONA_ADAPT.get(persona or "", _DEFAULT_PERSONA)
    diff_mult = pa["diff_mult"]
    max_actions = pa["max_actions"]
    sp = _STAGE_PRIORITY.get(stage or "", {"prefer": [], "forbid": []})
    prefer, forbid = sp["prefer"], sp["forbid"]
    cap = capability or {}

    industry = None
    if account is not None:
        industry = _industry_of(account)

    scored: list[dict[str, Any]] = []
    dont_do: list[dict[str, Any]] = []
    seen: set[str] = set()

    for d in diagnoses:
        if not isinstance(d, dict):
            continue
        code = d.get("code")
        if code not in _DIAGNOSIS_TO_ACTION or code in seen:
            continue   # 无映射 → 不生成（防 LLM 自由发挥）；去重
        seen.add(code)
        spec = _DIAGNOSIS_TO_ACTION[code]

        # 行业门控（如 POI 仅到店类）
        gate = spec.get("industry_gate")
        if gate and industry is not None and industry not in gate:
            continue

        params = d.get("params") or {}
        try:
            text = spec["tmpl"].format(**_safe_params(spec["tmpl"], params))
        except Exception:
            text = spec["tmpl"]   # 占位符缺失 → 优雅降级保留模板

        roi = spec["roi"]
        urgency = spec["urgency"]
        # 难度按 capability + persona 调（§三.3）
        difficulty = _adjust_difficulty(code, spec["difficulty"], cap) * diff_mult
        P = _score(roi, difficulty, urgency)

        item = {
            "code": code,
            "text": text,
            "kind": spec.get("kind", ""),
            "done_std": spec["done_std"],
            "hard_top": spec.get("hard_top", False),
            "P": round(P, 2),
            "score_explain": (
                f"ROI {roi}×{_W_ROI} / 难度 {round(difficulty, 2)}×{_W_DIFF} "
                f"× 紧急 {urgency}×{_W_URG} = {round(P, 2)}（🟨权重经验值·需校准）"
            ),
        }

        # 阶段红线：该 kind 被 forbid → 移入「别做」清单（不参与排序）
        if item["kind"] in forbid and not item["hard_top"]:
            dont_do.append({
                "text": text,
                "why": f"你还在「{stage}」阶段，先打地基——这件事这个月先别做。",
            })
            continue

        scored.append(item)

    # 排序：① hard_top（合规）永远置顶 ② prefer 的 kind 加权 ③ P 降序
    def sort_key(it: dict[str, Any]) -> tuple:
        return (
            0 if it["hard_top"] else 1,
            0 if it["kind"] in prefer else 1,
            -it["P"],
        )

    scored.sort(key=sort_key)

    top = scored[:max_actions]
    backlog = scored[max_actions:]

    return {
        "top_actions": top,
        "dont_do": dont_do,
        "backlog": backlog,
        "max_actions": max_actions,
        "persona_tone": pa["tone"],
        "weight_note": (
            f"⚠️ 排序权重（ROI={_W_ROI} / 难度={_W_DIFF} / 紧急={_W_URG}）是初始经验值，"
            f"非铁律——会用真实回测数据（attribution_cache）持续校准。每件下方都给了打分拆解，"
            f"不是玄学评分。"
        ),
    }


def _safe_params(tmpl: str, params: dict[str, Any]) -> dict[str, Any]:
    """给模板里出现的占位符兜底默认值（缺失数据时不崩·给可读占位）。"""
    import string
    defaults = {
        "head_sec": "3", "target_user": "你的目标客户", "who": "你是谁",
        "whom": "谁", "what": "能帮他什么", "pin_n": "N", "focus_topic": "你的主方向",
        "keyword": "关键词", "bad_term": "违规词", "good_term": "合规说法",
    }
    out = dict(defaults)
    out.update({k: v for k, v in params.items() if v is not None})
    # 只保留模板真用到的键，避免 KeyError
    fields = {f for _, f, _, _ in string.Formatter().parse(tmpl) if f}
    return {k: out.get(k, "{" + k + "}") for k in fields}


def _adjust_difficulty(code: str, base: int, cap: dict[str, Any]) -> float:
    """按 capability 调难度（§三.3）：团队拍视频更易·有预算可投流·在职偏好一次配置。"""
    d = float(base)
    # 拍视频类（多条/选题）：团队号 -2
    if code in ("funnel_break_interaction", "topic_drought") and cap.get("team"):
        d = max(1.0, d - 2)
    return d


def render_action_section(plan: dict[str, Any]) -> str:
    """渲染「明天就能做的 N 件事」报告段（Markdown·最强行动召唤·防玄学标）。

    产出 business_md 同构的 str，由 build_report 收尾插入。空输入优雅降级（出友好提示·不崩）。
    """
    L: list[str] = []
    P = L.append

    top = plan.get("top_actions") or []
    dont = plan.get("dont_do") or []
    backlog = plan.get("backlog") or []
    max_n = plan.get("max_actions", 3)

    P(f"## 🎯 明天就能做的 {min(len(top), max_n) or max_n} 件事（按先后排好了）")
    P("")
    P("> 上面诊断说了一堆，到底**先做哪件**？我按「见效快、最省事、最紧急」排好序了——"
      "**别贪多，先把前几件做完**，攒个快速正反馈再往下走。")
    P("")

    if not top:
        # 空输入优雅降级
        P("- 这次没有识别到明确的待办行动项——可能是诊断信息不足，或你的账号当前没有突出短板。"
          "补上更完整的账号/作品数据后，这里会给你「明天就能做的具体几件事」。")
        P("")
    else:
        for i, a in enumerate(top, 1):
            tag = "⛳合规·必须先改" if a.get("hard_top") else "📌"
            P(f"**{tag} 第 {i} 件：{a['text']}**")
            ds = a.get("done_std") or {}
            done_icon = "🟩可自动复检" if ds.get("type") == "structural" else "🟥需投喂后台数据"
            P(f"- ✅ 怎么算做完：{ds.get('desc', '（完成标准待补）')}（{done_icon}）")
            P(f"- 📊 为什么排这个位置：{a.get('score_explain', '')}")
            P("")

    # ⛔ 别做清单（阶段红线·单列·不混进 3 件）
    if dont:
        P("### ⛔ 这个月先别做（你还在打地基阶段）")
        for d in dont:
            P(f"- {d['text']} —— {d['why']}")
        P("")

    # backlog 折叠提示
    if backlog:
        P(f"> 还有 {len(backlog)} 件次要的，先做完上面的再说——"
          f"**一次只盯几件，注意力是你最稀缺的资源。** 30 天后复诊我帮你检查做完没。")
        P("")

    # 防玄学权重标注
    note = plan.get("weight_note")
    if note:
        P(f"> {note}")
        P("")

    return "\n".join(L)
