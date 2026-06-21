"""视听归因模块 · 确定性统计 · 防玄学四铁律 · 零 LLM 判断。

设计依据：probe-audiovisual-attribution-methodology-v1.0.md
  三步统计：分层 → 对照 → 差异提取
  四条防玄学铁律：
    1. 设对照组（爆款 vs 平款双向统计，禁幸存者偏差）
    2. 相关 ≠ 因果（措辞严格用"更常出现/相关"，禁"导致/因为"）
    3. 标置信度（样本量 → confidence 等级；<MIN_SAMPLE 标"参考·样本不足"）
    4. 诚实边界（基于点赞≠完播/流量，结论标"基于点赞"）

输入：works_with_av = [{"like": int, "six_layer": {...六层结构化...}}, ...]
输出：attribution dict + render_attribution_section 报告段
"""
from __future__ import annotations

from collections import Counter
from typing import Any

# ─── 常数 ───────────────────────────────────────────────────────────────────

# 每层提取哪些字段参与归因（与 audiovisual.py LAYERS / 字段名对齐）
_ATTR_FIELDS: dict[str, list[str]] = {
    "auditory": ["bgm_style", "speech_pace"],
    "visual": ["color", "edit_pace"],
    "narrative": ["hook"],
    "persona": ["on_screen"],
}

# 对照组分层：top/bottom 各取样本的 1/3（最少 2 条，避免单条结论）
_TIER_FRAC = 3

# 置信度分级（以最小层样本量为基准）
# 注：分层取 1/_TIER_FRAC，N 条总样本 → 每层 ≈ N/3 条。
#   - 总 N≥18（每层≥6）→ 置信高；总 N≥9（每层≥3）→ 置信中；否则参考·样本不足
_CONF_NONE = 5          # < 此值整体不做归因
_CONF_LOW_MARK = 3      # top 或 bottom 层 < 此值 → 标"参考·样本不足"
_CONF_HIGH_MARK = 6     # top 层 >= 此值 → 置信高

# 差异提取：爆款层频率 - 平款层频率 > 此阈值才列为候选因子
_DIFF_THRESHOLD = 0.20   # 20% 差值

# 每个 field 的 conf 低于此值时忽略（和 audiovisual._fld 类似的诚实过滤）
_MIN_FIELD_CONF = 0.45


# ─── 内部工具 ────────────────────────────────────────────────────────────────

def _fld_val(layer: dict | None, key: str) -> str | None:
    """从六层字段取值；conf < _MIN_FIELD_CONF 返回 None（不可信项不参与归因）。"""
    if not isinstance(layer, dict):
        return None
    f = layer.get(key)
    if not isinstance(f, dict):
        return None
    v = f.get("v")
    try:
        conf = float(f.get("conf", 0))
    except (TypeError, ValueError):
        conf = 0.0
    if not v or conf < _MIN_FIELD_CONF:
        return None
    return str(v).strip()


def _extract_features(work: dict) -> dict[str, str | None]:
    """从单条作品的 six_layer 提取所有参与归因的特征值。
    键格式：{layer}.{field}，值为枚举字符串或 None（不可信/缺失）。
    """
    sl = work.get("six_layer") or {}
    feats: dict[str, str | None] = {}
    for layer_name, fields in _ATTR_FIELDS.items():
        layer = sl.get(layer_name) or {}
        for field in fields:
            feats[f"{layer_name}.{field}"] = _fld_val(layer, field)
    return feats


def _confidence_label(top_n: int, bot_n: int) -> str:
    """根据样本量给出置信度标签（方法论§三 第③条）。"""
    smaller = min(top_n, bot_n)
    if smaller < _CONF_LOW_MARK:
        return "参考·样本不足"
    if smaller >= _CONF_HIGH_MARK:
        return "置信高"
    return "置信中"


def _tier_split(works: list[dict]) -> tuple[list[dict], list[dict]]:
    """按点赞分爆款层(top) vs 平款层(bottom)，各取 1/_TIER_FRAC（向上取整，最少 2 条）。
    对照组铁律：爆款和平款 *都* 统计——防幸存者偏差（方法论§三 第①条）。
    """
    n = len(works)
    seg = max(2, n // _TIER_FRAC)
    sw = sorted(works, key=lambda w: (w.get("like") or 0), reverse=True)
    return sw[:seg], sw[-seg:]


# ─── 主归因函数 ─────────────────────────────────────────────────────────────

def attribute(works_with_av: list[dict]) -> dict[str, Any]:
    """视听批量归因（确定性统计，防玄学四铁律内置）。

    输入：works_with_av = [{"like": int, "six_layer": {六层结构化}}, ...]
    输出：{
        "ok": bool,
        "total_n": int,            # 总样本量
        "top_n": int,              # 爆款层样本量
        "bot_n": int,              # 平款层样本量
        "confidence": str,         # 整体置信度标签
        "honest_boundary": str,    # 诚实边界声明（点赞≠完播≠流量）
        "factors": [               # 候选成功因子列表（差异特征）
            {
                "feature": "auditory.bgm_style",      # 特征键
                "value": "轻快",                        # 爆款层高频值
                "top_count": int, "top_n": int,        # 爆款层: X/N
                "bot_count": int, "bot_n": int,        # 平款层: X/N（对照组）
                "diff": float,                          # 频率差（>0 = 爆款更高）
                "confidence": str,                      # 特征级置信度
            }, ...
        ],
        "error": str | None        # 仅 ok=False 时存在
    }
    """
    # ── 基础校验 ───────────────────────────────────────────────────────────
    works = [w for w in (works_with_av or []) if isinstance(w, dict)]
    if len(works) < _CONF_NONE:
        return {
            "ok": False,
            "total_n": len(works),
            "error": f"样本量 {len(works)} < {_CONF_NONE}，不足以做对照归因（防玄学：小样本结论不可信）",
        }

    # ── 分层（第①步：分层·对照组铁律） ───────────────────────────────────
    top_works, bot_works = _tier_split(works)
    top_n, bot_n = len(top_works), len(bot_works)

    # ── 统计每个特征在两层的值分布（第②步：对照统计） ─────────────────────
    # top_counts[feature][value] = 出现次数
    top_counts: dict[str, Counter] = {}
    bot_counts: dict[str, Counter] = {}

    for layer_name, fields in _ATTR_FIELDS.items():
        for field in fields:
            key = f"{layer_name}.{field}"
            top_counts[key] = Counter()
            bot_counts[key] = Counter()

    for w in top_works:
        for feat_key, val in _extract_features(w).items():
            if val is not None:
                top_counts[feat_key][val] += 1

    for w in bot_works:
        for feat_key, val in _extract_features(w).items():
            if val is not None:
                bot_counts[feat_key][val] += 1

    # ── 差异提取（第③步：候选成功因子） ────────────────────────────────────
    # 找"爆款高频 + 平款低频"的 (特征, 值) 对——频率差 > _DIFF_THRESHOLD
    factors: list[dict] = []

    for feat_key in top_counts:
        t_total = top_n  # 分母：爆款层作品数（不是有效计数，防挑样本）
        b_total = bot_n

        for val, t_cnt in top_counts[feat_key].most_common():
            b_cnt = bot_counts[feat_key].get(val, 0)
            t_rate = t_cnt / t_total if t_total > 0 else 0.0
            b_rate = b_cnt / b_total if b_total > 0 else 0.0
            diff = t_rate - b_rate
            if diff > _DIFF_THRESHOLD:
                factors.append({
                    "feature": feat_key,
                    "value": val,
                    "top_count": t_cnt,
                    "top_n": t_total,
                    "bot_count": b_cnt,
                    "bot_n": b_total,
                    "diff": round(diff, 3),
                    "confidence": _confidence_label(t_cnt, bot_n),
                })

    # 按差异大小排序（最显著的因子排前面）
    factors.sort(key=lambda f: -f["diff"])

    # ── 整体置信度 + 诚实边界（第③④条铁律） ─────────────────────────────
    overall_conf = _confidence_label(top_n, bot_n)
    honest_boundary = (
        "⚠️ 归因基于**点赞数**分层（拿得到的最直接公开指标）。"
        "「高赞」≠「高完播」≠「高流量」——完播率和推流逻辑是算法黑盒，本分析触达不到。"
        "结论严格表述为「与高点赞相关」，不代表「能提升完播或流量」。"
    )

    return {
        "ok": True,
        "total_n": len(works),
        "top_n": top_n,
        "bot_n": bot_n,
        "confidence": overall_conf,
        "honest_boundary": honest_boundary,
        "factors": factors,
    }


# ─── 报告段渲染 ──────────────────────────────────────────────────────────────

_FEATURE_LABELS: dict[str, str] = {
    "auditory.bgm_style": "配乐风格",
    "auditory.speech_pace": "语速",
    "visual.color": "主色调",
    "visual.edit_pace": "剪辑节奏",
    "narrative.hook": "开头钩子",
    "persona.on_screen": "出镜方式",
}


def render_attribution_section(attribution: dict) -> str:
    """归因结果 → 报告"你的爆款视听公式"段（说人话·markdown）。

    防玄学措辞铁律（内置，不可绕过）：
    - 只用"更常出现/相关/建议复制"，禁"导致/因为/会让点赞涨"
    - 每条带 top/bottom 对照数（N/M vs 平款 X/M）
    - 带置信度标签
    - 段末标诚实边界（点赞 ≠ 完播）
    - 样本不足时诚实标注
    """
    if not attribution or not attribution.get("ok"):
        err = attribution.get("error", "样本不足，跳过归因。") if attribution else "无归因数据。"
        return f"### 你的爆款视听公式\n\n> ⚠️ {err}\n"

    total_n = attribution.get("total_n", 0)
    top_n = attribution.get("top_n", 0)
    bot_n = attribution.get("bot_n", 0)
    overall_conf = attribution.get("confidence", "参考·样本不足")
    honest_boundary = attribution.get("honest_boundary", "")
    factors = attribution.get("factors") or []

    lines: list[str] = []
    A = lines.append

    A("### 你的爆款视听公式")
    A("")
    A(f"> 基于 **{total_n} 条**作品对照统计（爆款层 {top_n} 条 vs 平款层 {bot_n} 条）·整体{overall_conf}。")
    A("> 以下特征在你的高点赞作品里**更常出现**（相关性，不是因果·防玄学设计）。")
    A("")

    if not factors:
        A("暂时没找到显著的视听差异特征（高赞和低赞在视听特征上比较均质，或样本中视听数据可信度不足）。")
        A("")
        A("**建议**：积累更多带视听六层的作品数据，或尝试风格上更大胆分化，拉开对比后规律会更明显。")
    else:
        A("**发现的规律（爆款层 vs 平款层对照）**")
        A("")
        for f in factors:
            feat_label = _FEATURE_LABELS.get(f["feature"], f["feature"])
            val = f["value"]
            tc, tn = f["top_count"], f["top_n"]
            bc, bn = f["bot_count"], f["bot_n"]
            conf = f["confidence"]
            diff_pct = int(f["diff"] * 100)

            # 措辞铁律：相关而非因果
            line = (
                f"- **{feat_label}「{val}」**："
                f"你高赞作品中 {tc}/{tn} 条更常用（vs 平款 {bc}/{bn} 条），"
                f"频率差 +{diff_pct}%·{conf}"
            )
            if conf == "参考·样本不足":
                line += "（该条样本偏少，仅作方向参考）"
            lines.append(line)

        A("")
        A("**建议（基于上面你自己的数据·比抄别人靠谱）**")
        A("")
        top_factors = [f for f in factors if f["confidence"] != "参考·样本不足"][:3]
        if top_factors:
            for f in top_factors:
                feat_label = _FEATURE_LABELS.get(f["feature"], f["feature"])
                val = f["value"]
                A(f"- 下一条尝试保留「{feat_label}」用**{val}**风格——这是你自己高赞作品里验证过更常出现的。")
        else:
            A("- 当前所有因子样本量偏少，建议先积累到 10+ 条带视听分析的作品再看规律。")

    A("")
    A(f"> {honest_boundary}")
    A("> 说明：以上分析**只用确定性统计**（频率对照）——不靠 AI 判断「哪个好」；"
      "所有措辞用「更常出现/相关」，这是刻意的防玄学设计（相关性 ≠ 因果）。")

    return "\n".join(lines)
