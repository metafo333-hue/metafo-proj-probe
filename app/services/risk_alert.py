"""风险/下行预警 · risk_alert.py（确定性·规则驱动·零 LLM）。

来源方法论：02-analysis-dimensions/risk-downside-adaptive-research.md
  §二 五大风险类型（限流/封号红线/赛道衰退/结构性/人设）
  §三 三轴适配（行业切红线库 / 人群升降级 / 阶段侧重）
  §四 三级分级 🔴致命 / 🟡警示 / 🟢提示 + 应对
  §五 机会与风险物理隔离·致命风险置顶
  §七.4 红线库种子（按行业·MVP）

诚实铁律（R0.8 防玄学）：
- 概率非必然：全程「可能/有风险/概率」·禁「一定被封」（possibility 分 high/medium/low）
- 有据可循：每条风险带 source（公约/政策/案例）·禁凭印象列风险
- 黑盒诚实：原创度/搬运/健康分 🟥 拿不到 → 只提示信号·不替平台定论（is_blackbox 标记）
- 不误报：按行业加载红线库（餐饮不查证券资质）
- 不漏报：医疗/金融/法律/教育默认 🔴 起步·缺资质必报
- 时效声明：红线库标 valid_until·「以平台最新规则为准」
- 不替裁决：「可能触发·建议自查」非「你违规了」

纯函数·零副作用·零网络·零 LLM。
"""
from __future__ import annotations

from typing import Any

from .account_report import _track, _is_business

# 级别常量
_FATAL, _WARNING, _NOTICE = "fatal", "warning", "notice"
_LEVEL_ICON = {_FATAL: "🔴", _WARNING: "🟡", _NOTICE: "🟢"}
_LEVEL_CN = {_FATAL: "致命", _WARNING: "警示", _NOTICE: "提示"}
_POSSIBILITY_CN = {"high": "高风险·已有同类封号/处罚案例", "medium": "中风险·可能限流·概率非必然",
                   "low": "低风险·建议关注·非当前问题"}

# 红线库时效（平台规则常变·2025 密集出公约）
_REDLINE_VALID_UNTIL = "2026-12-31"
_REDLINE_CAVEAT = f"⚠️ 平台规则常变（截至 {_REDLINE_VALID_UNTIL}·以抖音最新规则为准）·此处为风险信号提示，不替平台裁决。"

# ──────────────────────────────────────────────────────────────────────────────
# §七.4 行业红线库种子（封号重灾区·缺资质默认 🔴 起步）
# keywords：触发词（文案/简介命中即提示）；qual：所需资质（缺则升级）
# ──────────────────────────────────────────────────────────────────────────────
_REDLINE_SEEDS: dict[str, dict[str, Any]] = {
    "医疗": {
        "keywords": ["疗效", "根治", "包好", "祖传秘方", "治愈", "药到病除"],
        "qual": "医疗机构执业许可证", "level": _FATAL,
        "src": "抖音医疗八类红线 2025·252 名违规医生被清退",
    },
    "财经": {
        "keywords": ["稳赚", "荐股", "财富自由", "保本高收益", "包赚", "内幕消息"],
        "qual": "证券从业资质", "level": _FATAL,
        "src": "抖音财经公约 2025-12（禁非认证账号发财经内容）",
    },
    "法律": {
        "keywords": ["包赢官司", "内部关系", "打点关系", "百分百胜诉"],
        "qual": "律师执业资质", "level": _FATAL,
        "src": "抖音法律治理公约 2025-11（违规永久封禁）",
    },
    "教育": {
        "keywords": ["保过", "包过", "提分", "学科辅导", "押题命中"],
        "qual": "办学许可", "level": _FATAL,
        "src": "双减政策 + 虚假宣传红线",
    },
    "通用": {
        "keywords": ["最好", "第一", "100%", "国家级", "绝无仅有", "全网最低"],
        "qual": None, "level": _WARNING,
        "src": "广告法 + 夸大宣传（67 万主播被扣健康分·gmw 2025-08）",
    },
}

# track 名（account_report._track 输出）→ 行业（决定加载哪套红线库）
_TRACK_TO_INDUSTRY: list[tuple[tuple[str, ...], str]] = [
    (("医", "健康", "养生", "诊"), "医疗"),
    (("财经", "理财", "投资", "股", "基金", "炒"), "财经"),
    (("法律", "律师", "维权", "官司"), "法律"),
    (("考证", "学习", "教育", "辅导", "提分", "课"), "教育"),
    (("美食", "探店", "吃播", "餐"), "餐饮"),
    (("美妆", "护肤", "医美", "美业", "时尚"), "美业"),
    (("穿搭", "服装", "服饰", "衣"), "服装"),
    (("健身", "运动", "家政", "生活服务"), "生活服务"),
]

# §三.1 行业 → 第一高危类型 + 默认起步级别（铁律：医疗/金融/法律/教育 🔴 起步）
_INDUSTRY_RISK_PROFILE: dict[str, dict[str, str]] = {
    "医疗": {"top_risk": "封号红线（资质/疗效）", "default": _FATAL},
    "财经": {"top_risk": "封号红线（无资质荐股/收益承诺）", "default": _FATAL},
    "法律": {"top_risk": "封号红线（无资质法律意见）", "default": _FATAL},
    "教育": {"top_risk": "封号红线（双减/承诺提分）", "default": _FATAL},
    "餐饮": {"top_risk": "限流（低质/同质化）", "default": _NOTICE},
    "美业": {"top_risk": "限流 + 虚假宣传（疗效暗示）", "default": _WARNING},
    "服装": {"top_risk": "同质化/调性错位", "default": _NOTICE},
    "生活服务": {"top_risk": "限流（隐私/夸大）", "default": _WARNING},
    "B端": {"top_risk": "虚假宣传/导流", "default": _WARNING},
    "通用": {"top_risk": "限流为主", "default": _NOTICE},
}


def _industry_of(account: dict[str, Any]) -> str:
    """按 track + 业务性质判定行业（决定红线库）。"""
    text = (account.get("signature") or "") + " " + \
           " ".join(account.get("hashtags") or []) + " " + (account.get("nickname") or "")
    track_name, _ = _track(text)
    probe = track_name + " " + text
    if _is_business(text):
        # B 端可能仍触医疗/财经等红线·先看红线词
        for kws, ind in _TRACK_TO_INDUSTRY:
            if any(k in probe for k in kws):
                return ind
        return "B端"
    for kws, ind in _TRACK_TO_INDUSTRY:
        if any(k in probe for k in kws):
            return ind
    return "通用"


def _account_text(account: dict[str, Any]) -> str:
    return (account.get("signature") or "") + " " + \
           " ".join(account.get("hashtags") or []) + " " + (account.get("nickname") or "")


def _escalate(base: str, industry: str, persona: str | None, stage: str | None,
              risk_type: str) -> tuple[str, str]:
    """三轴升降级（§三）→ (final_level, possibility)。

    - 医疗/金融/法律/教育 + 缺资质 → fatal（行业 profile 已决定 base）
    - 中年失业 + structural → 升 warning（全压单号·sme§5.2 容错极短）
    - 起号期 + limit_flow → 降 notice（冷启动无流量是正常现象·防误判）
    """
    level = base
    # 人群轴：中年失业全压单号·结构性风险升级
    if persona == "中年失业" and risk_type == "structural" and level == _NOTICE:
        level = _WARNING
    # 阶段轴：起号期限流降级 + 附「冷启动正常」解释
    if stage in ("冷启动", "起号期") and risk_type == "limit_flow" and level == _WARNING:
        level = _NOTICE

    possibility = {_FATAL: "high", _WARNING: "medium", _NOTICE: "low"}[level]
    return level, possibility


def scan_risks(account: dict[str, Any],
               video: dict[str, Any] | None = None,
               works: list | None = None,
               persona: str | None = None,
               stage: str | None = None) -> list[dict[str, Any]]:
    """主入口：按账号 (行业×人群×阶段) 扫描五类风险 → 分级 findings（确定性·零 LLM）。

    Returns:
        list[finding]，每条：
          {risk_type, level, possibility, title, evidence, action_advice,
           source, is_blackbox, caveat}
    按 level 严重度降序（致命置顶）。
    """
    findings: list[dict[str, Any]] = []
    text = _account_text(account)
    industry = _industry_of(account)
    profile = _INDUSTRY_RISK_PROFILE.get(industry, _INDUSTRY_RISK_PROFILE["通用"])

    # —— 1. 封号红线（按行业加载红线库·缺资质必报）——
    redline = _REDLINE_SEEDS.get(industry)
    if redline:
        hit = [w for w in redline["keywords"] if w in text]
        if hit:
            base = redline["level"]
            level, poss = _escalate(base, industry, persona, stage, "ban_redline")
            qual = redline.get("qual")
            advice = (f"立即自查：把「{'、'.join(hit)}」这类表述删掉/改成中性陈述；"
                      + (f"若做「{industry}」内容，确保持有《{qual}》并在主页晒资质。"
                         if qual else "确保所有声称有据可查（广告法红线）。")
                      + "先解决合规，再谈增长——封号=转化归零。")
            findings.append({
                "risk_type": "ban_redline",
                "level": level, "possibility": poss,
                "title": f"{industry}行业红线词命中：「{'、'.join(hit)}」",
                "evidence": {"hit_keywords": hit, "qual_required": qual},
                "action_advice": advice,
                "source": redline["src"],
                "is_blackbox": False,
                "caveat": _REDLINE_CAVEAT,
            })

    # —— 2. 限流风险（违规内容·夸大用词·通用红线词）——
    generic = _REDLINE_SEEDS["通用"]
    generic_hit = [w for w in generic["keywords"] if w in text]
    if generic_hit and industry not in ("医疗", "财经", "法律", "教育"):
        # 红线行业已在上面更高级别报过·此处只对非红线行业补限流
        level, poss = _escalate(_WARNING, industry, persona, stage, "limit_flow")
        extra = ""
        if level == _NOTICE and stage in ("冷启动", "起号期"):
            extra = "（你还在起号期·暂时没流量是冷启动正常现象，别误判自己失败）"
        findings.append({
            "risk_type": "limit_flow",
            "level": level, "possibility": poss,
            "title": f"夸大/极限用词可能影响推荐权重：「{'、'.join(generic_hit)}」",
            "evidence": {"hit_keywords": generic_hit},
            "action_advice": f"把「{'、'.join(generic_hit)}」换成可量化的客观陈述，降低限流概率{extra}。",
            "source": generic["src"],
            "is_blackbox": False,
            "caveat": "可能性非必然·健康分是平台黑盒，此处只提示「可能影响健康分的信号」。",
        })

    # —— 3. 搬运/低原创（🟥黑盒·只提示不定论）——
    findings.append({
        "risk_type": "limit_flow",
        "level": _NOTICE, "possibility": "low",
        "title": "原创度/搬运判定（平台黑盒·只能提示）",
        "evidence": {"note": "原创度是平台原始判定·probe 拿不到"},
        "action_advice": "若有二次剪辑/搬运成分，注意搬运类封号率曾超 60%（2024 政策收紧）·建议提高原创占比。",
        "source": "搬运类账号封号率统计 2024",
        "is_blackbox": True,
        "caveat": "🟥 黑盒：无法替平台判定原创度·仅作信号提示·非定论。",
    })

    # —— 4. 结构性风险（单一爆款/单平台/单变现依赖·中年失业全压单号升级）——
    avg = account.get("avg_like") or 0
    mx = account.get("max_like") or 0
    single_burst = mx > avg * 3 and mx > 0
    if single_burst:
        level, poss = _escalate(_NOTICE, industry, persona, stage, "structural")
        msg = "你的数据靠少数几条爆款撑着（最高赞远超均值）·爆款热度衰减后容易断崖。"
        if persona == "中年失业":
            msg += "（你这种情况，把唯一收入押在单个号/单平台/单变现上，容错期太短——建议尽早分散。）"
        findings.append({
            "risk_type": "structural",
            "level": level, "possibility": poss,
            "title": "过度依赖单一爆款（结构性风险）",
            "evidence": {"avg_like": avg, "max_like": mx},
            "action_advice": "把验证过的爆款方向稳定复制成多条·别只靠一条；同步布局第二变现路径。",
            "source": "全域推广·单赛道红利终结 2025（网易/36氪）",
            "is_blackbox": False,
            "caveat": "可能性非必然·结构性是隐患不是即时违规。",
        })

    # —— 5. 赛道衰退（内容同质化·works 重复率高）——
    if works and len(works) >= 4:
        descs = [(w.get("desc") or "")[:10] for w in works if isinstance(w, dict)]
        if descs:
            uniq_ratio = len(set(descs)) / len(descs)
            if uniq_ratio < 0.6:   # 重复率 >40%
                level, poss = _escalate(_WARNING, industry, persona, stage, "sector_decline")
                findings.append({
                    "risk_type": "sector_decline",
                    "level": level, "possibility": poss,
                    "title": "内容同质化偏高（赛道红海信号）",
                    "evidence": {"unique_ratio": round(uniq_ratio, 2)},
                    "action_advice": "选题重复率偏高·红海里破局难·建议找差异化切入角度或细分方向。",
                    "source": "赛道生命周期·影视剪辑等见顶 CSDN 2025",
                    "is_blackbox": False,
                    "caveat": "可能性非必然·赛道衰退是结构性趋势·非即时违规。",
                })

    # 按级别严重度排序（致命置顶·§五）
    order = {_FATAL: 0, _WARNING: 1, _NOTICE: 2}
    findings.sort(key=lambda f: order.get(f["level"], 9))
    return findings


def render_risk_section(account: dict[str, Any],
                        findings: list[dict[str, Any]] | None = None,
                        persona: str | None = None,
                        stage: str | None = None,
                        video: dict[str, Any] | None = None,
                        works: list | None = None) -> str:
    """渲染「风险预警」报告段（Markdown·致命置顶·机会风险物理隔离·全程标可能性）。

    findings 不传则内部 scan_risks。空输入/无风险 → 友好提示（不吓唬·§四「没有红线则跳过」）。
    """
    if findings is None:
        findings = scan_risks(account, video=video, works=works,
                              persona=persona, stage=stage)

    industry = _industry_of(account)
    profile = _INDUSTRY_RISK_PROFILE.get(industry, _INDUSTRY_RISK_PROFILE["通用"])

    L: list[str] = []
    P = L.append

    P("## ⚠️ 风险预警（专业体检·既看机会也看雷）")
    P("")
    P(f"> 你所在「{industry}」赛道，第一要防的是：**{profile['top_risk']}**。")
    P("> 下面每条都标了**可能性**（不是「一定会」），并给了应对——这是概率，不是判决。")
    P("")

    fatal = [f for f in findings if f["level"] == _FATAL]
    warning = [f for f in findings if f["level"] == _WARNING]
    notice = [f for f in findings if f["level"] == _NOTICE]

    # 🔴 致命置顶（§五：缺资质先补·别先谈涨粉）
    if fatal:
        P("### 🔴 致命风险（先解决这个·再谈增长）")
        P("")
        for f in fatal:
            _render_one(P, f)
    # 没有致命 → 不吓唬（§五「没有红线则跳过」）
    elif not warning and not notice:
        P("- ✅ 这次没扫到明显风险信号——继续保持合规、稳定产出就好。"
          "（风险库会随平台规则更新·下次复诊再查一遍。）")
        P("")

    if warning:
        P("### 🟡 警示（可能限流/影响权重·可恢复）")
        P("")
        for f in warning:
            _render_one(P, f)

    if notice:
        P("### 🟢 提示（潜在隐患·暂不紧急·记录关注）")
        P("")
        for f in notice:
            _render_one(P, f)

    # 全局防玄学声明
    P(f"> {_REDLINE_CAVEAT}")
    P("> 风险是**概率不是必然**——专业诊断的标志是看得见雷，不是只画饼，更不是吓唬你。")
    P("")

    return "\n".join(L)


def _render_one(P, f: dict[str, Any]) -> None:
    icon = _LEVEL_ICON.get(f["level"], "")
    bb = "（🟥 平台黑盒·只提示信号·不替平台定论）" if f.get("is_blackbox") else ""
    P(f"**{icon} {f['title']}**{bb}")
    P(f"- 可能性：{_POSSIBILITY_CN.get(f['possibility'], f['possibility'])}")
    P(f"- 怎么办：{f['action_advice']}")
    P(f"- 依据：{f.get('source', '（来源待补）')}")
    if f.get("caveat"):
        P(f"- {f['caveat']}")
    P("")
