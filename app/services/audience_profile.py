"""受众画像匹配 v1 · audience_profile.py · 内容↔粉丝错位诊断（确定性·零 LLM 主路径）。

来源方法论：audience-profile-adaptive-research.md
  核心算法（§五）：
    步骤1 内容侧目标画像 ← _track() 赛道 → INDUSTRY_TARGET_PROFILE 查目标画像
    步骤2 实际粉丝画像   ← A 路授权 / B 路对标 / C 路（谨慎·默认关）
    步骤3 逐维度对比错位 ← 关键维度（按行业权重）算偏离度
    步骤4 错位翻译成行动 ← 偏离最大的维度 → 对应内容调整建议

防玄学（§三/§六·样本门是最重要的硬闸）：
  - 粉丝 < 100 不拉画像（小样本必失真）→ 只给「目标画像设定」(target_only)
  - 粉丝 < 1000 只定性·不出精确百分比
  - 目标画像全 🟨 经验推断（INDUSTRY_TARGET_PROFILE·依 sme-research·非实测真值）
  - 来源决定颜色：A 路 official=🟩 / B 路 benchmark=🟨 / C 路 self_inferred=🟥
  - 错位结论颜色 = min(目标🟨, 实际来源色)·取更不确定的一方

PIPL 合规：
  - 性别/年龄/地域=个人信息·人脸/声音=敏感信息。本模块只吃聚合统计·不碰个体。
  - 数据从 audience_source 三档接口来（可插拔灰度）；C 路默认关·待元东方拍板。
  - 全程国产 LLM·数据不出境（本模块零 LLM·错位为规则计算）。

纯函数·零网络·零 LLM。
"""
from __future__ import annotations

from typing import Any

# 样本门（防玄学硬闸·§3.3 + §六）
_PROFILE_FLOOR = 100       # 低于此不拉画像（小样本失真）→ target_only
_DEFINITE_FLOOR = 1000     # 低于此只定性·不出百分比

# 来源 → 防玄学颜色（A=🟩 / B=🟨 / C=🟥）
_SOURCE_COLOR = {
    "official_authorized": "🟩",
    "benchmark_estimate": "🟨",
    "self_inferred": "🟥",
}
# 颜色不确定度排序（取 min = 更不确定者）
_COLOR_RANK = {"🟩": 2, "🟨": 1, "🟥": 0}


# —— 行业目标画像（科学适应核心·全 🟨 经验推断·依 sme-research·作对标基准非真值）——
INDUSTRY_TARGET_PROFILE: dict[str, dict] = {
    "餐饮": {
        "key_dims": ["geo"],
        "target": {"geo_local_min": 0.5},
        "advice": {"geo": "本地粉占比低→强化 POI/同城话题/本地梗，让算法推给本地"},
    },
    "美业": {
        "key_dims": ["gender", "geo", "age"],
        "target": {"female_min": 0.7, "geo_local_min": 0.6, "age_core": "25-45"},
        "advice": {
            "gender": "男性偏多=内容跑偏→弃猎奇梗，回归效果对比+真实见证",
            "geo": "本地占比低=泛流量→强打同城话题/POI",
            "age": "偏年轻=消费力不足→内容口吻成熟化",
        },
    },
    "服装零售": {
        "key_dims": ["age", "gender"],
        "target": {"female_min": 0.6, "age_core": "18-40"},
        "advice": {
            "age": "年龄/价位心智错位→显性传递品质/价位锚点",
            "gender": "性别跑偏→选题对齐目标性别",
        },
    },
    "教育培训": {
        "key_dims": ["age"],
        "target": {"age_core": "25-45", "consume": "high"},
        "advice": {"age": "吸来学生白嫖党→定位决策者痛点（家长焦虑/职场晋升）"},
    },
    "知识科普": {
        "key_dims": ["age", "consume"],
        "target": {"age_core": "25-45", "consume": "high"},
        "advice": {
            "age": "学生粉多=叫好不叫座→口吻对齐付费人群",
            "consume": "低消费力粉多→内容引私域筛付费意愿",
        },
    },
    "知识IP": {
        "key_dims": ["age", "consume"],
        "target": {"age_core": "30-45", "consume": "high"},
        "advice": {
            "age": "学生白嫖粉占比高→内容口吻对齐付费人群（非取悦学生）",
            "consume": "消费力不足→引私域沉淀高意愿用户",
        },
    },
    "生活服务": {
        "key_dims": ["geo", "age"],
        "target": {"geo_local_min": 0.5, "age_core": "18-45"},
        "advice": {
            "geo": "全国泛粉看不到店→强化本地+体验课钩子",
            "age": "年龄错位→对齐本地家庭/消费场景",
        },
    },
}


def _local_ratio(geo: dict | None) -> float | None:
    if not isinstance(geo, dict):
        return None
    total = sum(v for v in geo.values() if isinstance(v, (int, float)))
    if total <= 0:
        return None
    local = geo.get("本地", 0) or 0
    # 若已是占比（总和≈1）直接取，否则归一化
    return float(local) / float(total)


def _female_ratio(gender: dict | None) -> float | None:
    if not isinstance(gender, dict):
        return None
    total = sum(v for v in gender.values() if isinstance(v, (int, float)))
    if total <= 0:
        return None
    return float(gender.get("female", 0) or 0) / float(total)


def _young_ratio(age: dict | None) -> float | None:
    """18-24 等年轻段占比（错位判：目标要 25-45 但年轻段过半 = 偏年轻）。"""
    if not isinstance(age, dict):
        return None
    total = sum(v for v in age.values() if isinstance(v, (int, float)))
    if total <= 0:
        return None
    young = 0.0
    for k, v in age.items():
        if not isinstance(v, (int, float)):
            continue
        if any(seg in str(k) for seg in ("17", "18", "19", "20", "21", "22", "23", "24", "<18", "18-24")):
            young += v
    return young / total


def _result_color(target_color: str, actual_color: str) -> str:
    """结论颜色 = 更不确定的一方（§五诊断诚实原则）。"""
    if _COLOR_RANK.get(actual_color, 0) <= _COLOR_RANK.get(target_color, 0):
        return actual_color
    return target_color


def _detect_mismatch(profile: dict, spec: dict, definite: bool,
                     actual_color: str) -> list[dict]:
    """对关键维度算错位（关键维度优先）。结论颜色 = min(目标🟨, 实际来源色)。"""
    target = spec.get("target", {})
    advice = spec.get("advice", {})
    key_dims = spec.get("key_dims", [])
    target_color = "🟨"  # 目标画像恒为经验推断
    out: list[dict] = []

    for dim in key_dims:
        actual_val = target_val = None
        severity = None
        if dim == "geo" and "geo_local_min" in target:
            r = _local_ratio(profile.get("geo"))
            if r is None:
                continue
            actual_val, target_val = r, target["geo_local_min"]
            if r < target_val * 0.5:
                severity = "🔴 严重错位"
            elif r < target_val:
                severity = "⚠️ 错位"
        elif dim == "gender" and "female_min" in target:
            r = _female_ratio(profile.get("gender"))
            if r is None:
                continue
            actual_val, target_val = r, target["female_min"]
            if r < target_val * 0.6:
                severity = "🔴 严重错位"
            elif r < target_val:
                severity = "⚠️ 错位"
        elif dim == "age" and "age_core" in target:
            y = _young_ratio(profile.get("age"))
            if y is None:
                continue
            actual_val, target_val = y, target.get("age_core")
            if y >= 0.5:                     # 年轻段过半 = 偏年轻错位
                severity = "🔴 严重错位" if y >= 0.65 else "⚠️ 错位"
        elif dim == "consume":
            # consume 维度无结构化字段时跳过（黑盒·只在有 interests/age 推断时提示）
            continue

        if severity:
            out.append({
                "dim": dim,
                "actual": round(actual_val, 3) if isinstance(actual_val, float) else actual_val,
                "target": target_val,
                "severity": severity,
                "advice": advice.get(dim, "（按行业回归目标人群定位）"),
                "color": _result_color(target_color, actual_color),
                "definite": definite,
            })
    return out


def diagnose(profile: dict | None, industry: str, followers: int) -> dict | None:
    """主入口·内容侧目标画像 vs 实际粉丝画像错位诊断。

    profile = audience_source 输出（official/benchmark/self_inferred）或 None。
    返回 dict（mode=target_only / diagnose）；followers 非法时返回 None。

    样本门（防玄学）：
      followers < 100 → target_only（不拉画像·给目标画像设定作内容锚点）
      followers < 1000 → definite=False（只定性·不出百分比）
    """
    if followers is None or followers < 0:
        return None
    spec = INDUSTRY_TARGET_PROFILE.get(industry)

    # 样本门1：粉丝太少不拉画像（小样本必失真）
    if followers < _PROFILE_FLOOR:
        return {
            "mode": "target_only", "industry": industry, "target": spec,
            "note": "粉丝还少（<100），先按这行该瞄准的人设定方向（🟨 行业经验），别急着看画像。",
        }
    # 无画像数据 → 目标画像兜底
    if not profile:
        return {
            "mode": "target_only", "industry": industry, "target": spec,
            "note": "没拿到你的粉丝画像数据——可上传创作者中心后台「粉丝画像」截图，能拿到最准的（🟩 官方）。",
        }

    src = profile.get("source", "self_inferred")
    actual_color = _SOURCE_COLOR.get(src, "🟥")
    definite = followers >= _DEFINITE_FLOOR
    spec = spec or {"key_dims": [], "target": {}, "advice": {}}
    mismatches = _detect_mismatch(profile, spec, definite, actual_color)
    return {
        "mode": "diagnose", "industry": industry,
        "source": src, "source_color": actual_color,
        "definite": definite, "key_dims": spec.get("key_dims", []),
        "mismatches": mismatches,
        "note": "实际画像 vs 这行该瞄准的人 → 看错位（结论颜色取更不确定的一方）。",
    }


# ──────────────────────────────────────────────────────────────────────────────
# 渲染层（与 commercial.render_*_section 同构·说人话·诚实标颜色）
# ──────────────────────────────────────────────────────────────────────────────

_SRC_DESC = {
    "official_authorized": "你的账号后台数据（最准）",
    "benchmark_estimate": "第三方对标估算（非本号·参考）",
    "self_inferred": "自建推断·非官方",
}


def render_audience_section(diag: dict | None) -> str | None:
    """渲染"你的内容吸来的是不是对的人"段·供 build_report 新参数 audience_md。

    无诊断 → None（build_report 自动跳过·零侵入降级）。
    """
    if not diag:
        return None
    L: list[str] = []
    P = L.append
    P("## 👥 你的内容，吸引来的是不是「对的人」（受众画像匹配）")
    P("")

    if diag["mode"] == "target_only":
        P(f"> {diag['note']}")
        P("")
        tgt = diag.get("target")
        if tgt:
            P(f"**你这行（{diag['industry']}）该瞄准谁**（🟨 行业经验·作内容方向锚点）：")
            for dim, adv in (tgt.get("advice") or {}).items():
                P(f"- 关键维度「{dim}」：{adv}")
            P("")
        P("> ⚠️ 以上「目标受众」是依行业经验的推断（🟨），不是你的实测画像——作方向参考。")
        return "\n".join(L)

    # diagnose 模式
    src = diag["source"]
    P(f"> 画像来源：{diag['source_color']} {_SRC_DESC.get(src, src)}")
    if not diag["definite"]:
        P("> ⚠️ 粉丝还不算多（<1000），以下只给方向不给精确比例（🟨 小样本易波动）。")
    P("")

    mismatches = diag.get("mismatches") or []
    if not mismatches:
        P("**好消息**：在你这行的关键维度上，没发现明显的「内容↔粉丝」错位——"
          "实际来的人和这行该瞄准的人大致对得上。")
        P("")
    else:
        P("**发现错位**（你内容吸来的人，和这行该瞄准的人对不上）：")
        P("")
        for m in mismatches:
            actual = m["actual"]
            actual_str = f"{actual:.0%}" if (diag["definite"] and isinstance(actual, float)) else "偏离目标"
            P(f"**{m['severity']} · 维度「{m['dim']}」** {m['color']}")
            P(f"- 实际：{actual_str}（目标参考：{m['target']}）")
            P(f"- 建议：{m['advice']}")
            P("")

    P("> ⚠️ 诚实标注：目标画像是行业经验推断（🟨）；实际画像来源见上方颜色。"
      "结论颜色取更不确定的一方——**绝不冒充官方精确画像**。")
    return "\n".join(L)
