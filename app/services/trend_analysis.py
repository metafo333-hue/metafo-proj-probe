"""趋势轨迹分析 · trend_analysis.py · 确定性·零 LLM·纯统计。

来源方法论：trend-trajectory-adaptive-research.md（02 分析层）
  从「快照诊断」升级为「轨迹诊断」——看导数不看存量。
  核心命题：掉粉号和涨粉号即使当前数据相同，方案应完全相反。

五条趋势曲线（方案§二）：
  A 粉丝增速及拐点 / B 作品表现时间序列 / C 互动率趋势 / D 主题漂移 / E 爆款承接力

day-1 可交付（方案§四关键洞察）：
  作品自带发布时间戳 → 单次采集即可做 B/D/E + 转折点（80% 价值）；
  粉丝增速 A/C 需复访累积快照（标"需复访"）。

防玄学（方案§六/七）：
  - <10 条不下趋势结论（样本门）；单条不做趋势判断。
  - 转折点必须排除外部脉冲（被推荐/蹭热点/大V带飞/违规处罚）才归因到创作动作。
  - 爆款离群值剔除后算基线（不被一条爆款拉偏）。
  - 短期波动≠趋势（Mann-Kendall 显著性检验，非裸眼看斜率）。

纯函数·零网络·零 LLM。works 单条结构对齐 account_report：
  {desc, like, comment, collect, share, create_time(epoch秒)}。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

# ── 样本门（方案§六·防玄学硬门）──────────────────────────────────────────────────
MIN_WORKS_FOR_BASELINE = 10    # <10 不下作品基线趋势结论
RELIABLE_WORKS = 20            # ≥20 可信级
MIN_SNAPSHOTS_FOR_FANS = 4     # 粉丝增速二阶导最低 4 点
MIN_SIDE_FOR_CHANGEPOINT = 5   # 转折点两侧各 ≥5 条

# 外部脉冲倍数门（基线 N 倍以上的单点疑似被推荐/蹭热点·非内容功劳）
_PULSE_MULTIPLE = 4.0

# 行业季节性强度（方案§3.1·去噪前提）
INDUSTRY_SEASONALITY: dict[str, str] = {
    "catering_local": "strong", "ecommerce": "strong", "education": "strong",
    "beauty": "medium", "fitness": "medium",
    "entertainment": "weak", "ip_founder": "weak", "general": "medium",
}

_DIR_CN = {
    "accelerating": "📈 加速涨（增速在变快）",
    "rising": "📈 在涨（稳定上行）",
    "plateau": "➡️ 平稳（缺突破口）",
    "decelerating": "📉 增速放缓（涨，但越涨越慢·留意拐点）",
    "declining": "📉 在掉（基线下行·需诊断）",
}


# ── 数据结构（方案§八.1）────────────────────────────────────────────────────────
@dataclass
class TrendPoint:
    timestamp: float          # epoch 秒
    metric: str
    value: float
    source: str = "work_intrinsic"   # work_intrinsic|snapshot|third_party
    is_outlier: bool = False


@dataclass
class TrendResult:
    metric: str
    direction: str            # accelerating|rising|plateau|decelerating|declining
    slope: float
    second_deriv: float | None
    significance: float       # Mann-Kendall p 近似（越小越显著）
    seasonality_adjusted: bool
    confidence: str           # insufficient|reference|reliable
    note: str = ""


@dataclass
class TurningPoint:
    work_index: int
    timestamp: float
    metric: str
    jump: float               # 基线跃迁幅度（相对·后/前 -1）
    direction: str            # positive|negative
    action_diff: dict[str, Any] = field(default_factory=dict)
    external_pulse: bool = False
    attributable: bool = False
    note: str = ""


@dataclass
class DeclineAlert:
    level: str                # red|yellow|green
    signal: str
    evidence: str
    suggested_action: str


# ── 基础统计（纯函数）──────────────────────────────────────────────────────────
def _median(xs: list[float]) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def mark_outliers(series: list[TrendPoint], k: float = _PULSE_MULTIPLE) -> list[TrendPoint]:
    """标爆款离群（> 中位数×k·基线计算时剔除·方案§七 爆款拉偏护栏）。"""
    vals = [p.value for p in series]
    med = _median(vals)
    thr = med * k if med > 0 else float("inf")
    for p in series:
        p.is_outlier = p.value > thr and med > 0
    return series


def _linreg_slope(xs: list[float], ys: list[float]) -> float:
    """最小二乘斜率（趋势一阶导·x 已归一化）。"""
    n = len(xs)
    if n < 2:
        return 0.0
    mx, my = _mean(xs), _mean(ys)
    den = sum((x - mx) ** 2 for x in xs)
    if den == 0:
        return 0.0
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den


def mann_kendall(ys: list[float]) -> float:
    """Mann-Kendall 趋势显著性 → 近似 p 值（防裸眼看斜率·方案§七）。

    返回双侧 p 近似：越小越显著。样本 <4 返回 1.0（不显著）。
    """
    n = len(ys)
    if n < 4:
        return 1.0
    s = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            s += (ys[j] > ys[i]) - (ys[j] < ys[i])
    var = n * (n - 1) * (2 * n + 5) / 18.0
    if var <= 0:
        return 1.0
    if s > 0:
        z = (s - 1) / math.sqrt(var)
    elif s < 0:
        z = (s + 1) / math.sqrt(var)
    else:
        z = 0.0
    # 双侧 p = 2*(1-Φ(|z|))，用 erfc 算
    p = math.erfc(abs(z) / math.sqrt(2))
    return min(1.0, max(0.0, p))


# ── 作品基线时序（B 维·day-1 可做）──────────────────────────────────────────────
def build_series(works: list[dict], metric: str = "like") -> list[TrendPoint]:
    """按发布时间排序得「作品表现时间序列」（方案§4.1 内生时序）。"""
    pts = []
    for w in works or []:
        if not isinstance(w, dict):
            continue
        ct = w.get("create_time")
        if ct is None:
            continue
        pts.append(TrendPoint(timestamp=float(ct), metric=metric,
                              value=float(w.get(metric, 0) or 0)))
    pts.sort(key=lambda p: p.timestamp)
    return pts


def baseline_trend(series: list[TrendPoint]) -> TrendResult:
    """剔离群求基线趋势 + Mann-Kendall 显著性（方案§8.2）。"""
    kept = [p for p in series if not p.is_outlier]
    n = len(kept)
    conf = _confidence_by_works(len(series))
    if n < 2:
        return TrendResult("work_baseline", "plateau", 0.0, None, 1.0, False,
                           "insufficient", "样本不足")
    # 对数化抗爆款压扁（方案 维度B 防玄学要点）
    ys = [math.log1p(max(0.0, p.value)) for p in kept]
    xs = [float(i) for i in range(n)]
    slope = _linreg_slope(xs, ys)
    sig = mann_kendall(ys)
    half = n // 2
    early, late = _mean(ys[:half]), _mean(ys[half:])

    # 显著性兜底：不显著 → 平稳（短期波动≠趋势·方案§七）
    if sig > 0.10:
        direction = "plateau"
    elif late > early:
        direction = "rising"
    else:
        direction = "declining"
    note = "" if conf != "insufficient" else f"⚠️ 样本{len(series)}<{MIN_WORKS_FOR_BASELINE}·不下趋势结论"
    return TrendResult("work_baseline", direction, round(slope, 6), None,
                       round(sig, 4), False, conf, note)


# ── 粉丝增速（A 维·需复访快照 ≥4 点·含二阶导拐点）─────────────────────────────────
def growth_trend(snapshots: list[dict]) -> TrendResult | None:
    """从复访快照算涨粉率趋势 + 二阶导拐点（方案§8.2·率非绝对·按天归一化）。

    snapshots: [{timestamp(epoch秒), follower}, ...]，需 ≥4 点。
    """
    snaps = sorted([s for s in (snapshots or [])
                    if isinstance(s, dict) and s.get("timestamp") and s.get("follower")],
                   key=lambda s: s["timestamp"])
    if len(snaps) < MIN_SNAPSHOTS_FOR_FANS:
        return None
    rates: list[float] = []
    for a, b in zip(snaps, snaps[1:]):
        d_days = max(1.0, (b["timestamp"] - a["timestamp"]) / 86400.0)
        prev = max(1.0, float(a["follower"]))
        rates.append((float(b["follower"]) - prev) / prev / d_days)  # 日涨粉率·按天归一
    xs = [float(i) for i in range(len(rates))]
    slope = _linreg_slope(xs, rates)         # 增速的变化（≈二阶导）
    sig = mann_kendall(rates)
    net_negative = rates[-1] < 0
    if net_negative:
        direction = "declining"
    elif slope > 0 and sig <= 0.10:
        direction = "accelerating"
    elif slope < 0 and sig <= 0.10:
        direction = "decelerating"
    else:
        direction = "rising" if _mean(rates) > 0 else "plateau"
    conf = "reliable" if len(snaps) >= 8 else "reference"
    return TrendResult("fans_growth", direction, round(slope, 8), round(slope, 8),
                       round(sig, 4), False, conf,
                       note=("⚠️ 净掉粉" if net_negative else ""))


# ── 转折点检测 + 归因（方案§2.2·最高价值）────────────────────────────────────────
def detect_change_points(series: list[TrendPoint],
                         min_jump: float = 0.40) -> list[TurningPoint]:
    """变点检测：基线发生统计显著跃迁的位置（方案§2.2）。

    简化稳健法：滑动比较「前窗中位数 vs 后窗中位数」，相对跃迁 ≥min_jump 记为变点。
    两侧各需 ≥MIN_SIDE_FOR_CHANGEPOINT 条（方案§六 样本门）。
    """
    n = len(series)
    w = MIN_SIDE_FOR_CHANGEPOINT
    if n < 2 * w:
        return []
    tps: list[TurningPoint] = []
    for i in range(w, n - w + 1):
        before = _median([p.value for p in series[i - w:i]])
        after = _median([p.value for p in series[i:i + w]])
        if before <= 0:
            continue
        jump = (after - before) / before
        if abs(jump) >= min_jump:
            tps.append(TurningPoint(
                work_index=i, timestamp=series[i].timestamp, metric=series[i].metric,
                jump=round(jump, 3),
                direction="positive" if jump > 0 else "negative"))
    # 同向相邻去重：保留跃迁绝对值最大的一个
    return _dedup_change_points(tps)


def _dedup_change_points(tps: list[TurningPoint]) -> list[TurningPoint]:
    if not tps:
        return []
    out: list[TurningPoint] = []
    for tp in tps:
        if out and out[-1].direction == tp.direction and tp.work_index - out[-1].work_index < MIN_SIDE_FOR_CHANGEPOINT:
            if abs(tp.jump) > abs(out[-1].jump):
                out[-1] = tp
        else:
            out.append(tp)
    return out


def _hashtags(desc: str) -> set[str]:
    import re
    return set(re.findall(r"#([^#\s]+)", desc or ""))


def diff_actions(works_sorted: list[dict], idx: int,
                 window: int = MIN_SIDE_FOR_CHANGEPOINT) -> dict[str, Any]:
    """变点前后「创作动作差异」（方案§2.2·主题/形式/频次）。"""
    before = works_sorted[max(0, idx - window):idx]
    after = works_sorted[idx:idx + window]
    bt: set[str] = set()
    for w in before:
        bt |= _hashtags(w.get("desc", ""))
    at: set[str] = set()
    for w in after:
        at |= _hashtags(w.get("desc", ""))
    return {
        "new_topics": sorted(at - bt)[:3],     # 新增主题（可能的正向因子）
        "dropped_topics": sorted(bt - at)[:3], # 丢弃主题
        "topic_shift": bool((at - bt) or (bt - at)),
    }


def check_external_pulse(works_sorted: list[dict], tp: TurningPoint,
                         avg_metric: float,
                         window: int = MIN_SIDE_FOR_CHANGEPOINT) -> bool:
    """排除外部脉冲（方案§2.2 防玄学铁律·变点≠因果）。

    判据：变点后窗内若由单条「爆点」(>均值×_PULSE_MULTIPLE) 主导，且该爆点的量级
    远超同窗其余条（中位数×_PULSE_MULTIPLE），则跃迁是「一次性爆款」而非「基线整体
    抬升」——疑似被推荐/蹭热点/大V带飞，不可归因到创作动作。
    变点索引标的是窗口边界，故需扫描后窗（而非只看边界那一条）。
    """
    if not works_sorted:
        return False
    key = tp.metric if tp.metric != "work_baseline" else "like"
    after = works_sorted[tp.work_index:tp.work_index + window]
    if not after:
        return False
    vals = [float(w.get(key, 0) or 0) for w in after]
    peak = max(vals)
    # 后窗内除峰值外的中位数——峰值若远超其余条 = 单点爆款而非整体抬升
    rest = sorted(v for v in vals if v != peak) or [peak]
    rest_med = _median(rest)
    pulse_vs_avg = avg_metric > 0 and peak > avg_metric * _PULSE_MULTIPLE
    pulse_vs_rest = rest_med > 0 and peak > rest_med * _PULSE_MULTIPLE
    return bool(pulse_vs_avg and pulse_vs_rest)


def attribute_turning_points(works_sorted: list[dict], tps: list[TurningPoint],
                             metric: str = "like") -> list[TurningPoint]:
    """对每个变点做动作归因 + 排除外部脉冲（方案§8.2）。"""
    avg = _mean([float(w.get(metric, 0) or 0) for w in works_sorted])
    for tp in tps:
        tp.action_diff = diff_actions(works_sorted, tp.work_index)
        tp.external_pulse = check_external_pulse(works_sorted, tp, avg)
        tp.attributable = (not tp.external_pulse) and tp.action_diff.get("topic_shift", False)
        if tp.external_pulse:
            tp.note = "疑似外部脉冲（被推荐/蹭热点/大V带飞）·不可归因到创作动作"
        elif tp.attributable:
            tp.note = "可归因到创作动作（伴随主题/形式变化）"
        else:
            tp.note = "基线跃迁但无明显动作变化·待复核"
    return tps


# ── 衰退预警（分级·方案§五）─────────────────────────────────────────────────────
def decline_alerts(work_trend: TrendResult, fans_trend: TrendResult | None,
                   series: list[TrendPoint], segment: str = "shop_owner") -> list[DeclineAlert]:
    """分级衰退预警（红/黄/绿·方案§五）。人群轴调敏感度（方案§3.2）。"""
    alerts: list[DeclineAlert] = []

    # 🟥 红·急：净掉粉
    if fans_trend and fans_trend.note and "净掉粉" in fans_trend.note:
        alerts.append(DeclineAlert(
            "red", "净掉粉/可能违规处罚",
            "复访快照显示周净涨粉转负", "立即查违规处罚 + 近期内容，急刹车止损"))

    # 🟥 红·急：作品基线断崖（近段较前段跌 >40%）
    kept = [p.value for p in series if not p.is_outlier]
    if len(kept) >= 2 * MIN_SIDE_FOR_CHANGEPOINT:
        early = _median(kept[:len(kept) // 2])
        late = _median(kept[len(kept) // 2:])
        if early > 0 and (late - early) / early < -0.40:
            alerts.append(DeclineAlert(
                "red", "作品基线断崖",
                f"近段作品基线较前期跌 {abs((late - early) / early) * 100:.0f}%（>40%）",
                "查改版动作（看转折点检测），是不是某次改坏了"))

    # 🟨 黄·警：增速持续衰减
    if fans_trend and fans_trend.direction == "decelerating":
        alerts.append(DeclineAlert(
            "yellow", "增速持续衰减",
            "涨粉率在减速（二阶导转负）", "诊断内容力/主题漂移，趁还在涨补内容"))

    # 🟨 黄·警：作品基线下行（显著）
    if work_trend.direction == "declining" and work_trend.confidence != "insufficient":
        alerts.append(DeclineAlert(
            "yellow", "作品基线持续下行",
            f"作品基线趋势下行（显著性 p={work_trend.significance}）",
            "查审美疲劳/选题重复，需选题创新"))

    # 🟢 绿·观察：平稳但无突破
    if not alerts and work_trend.direction == "plateau":
        alerts.append(DeclineAlert(
            "green", "数据平稳·缺突破口",
            "作品基线无显著趋势", "刻意做几条不同方向，拉开对比找突破点"))

    # 人群敏感度：实体店主对粉丝波动不慌（方案§3.2）→ 降黄为绿（非红线）
    if segment == "shop_owner":
        for a in alerts:
            if a.level == "yellow" and "增速" in a.signal:
                a.level = "green"
                a.suggested_action += "（实体店主：粉丝波动不慌，盯到店/核销趋势才是真预警）"
    return alerts


def _confidence_by_works(n_works: int) -> str:
    if n_works < MIN_WORKS_FOR_BASELINE:
        return "insufficient"
    if n_works < RELIABLE_WORKS:
        return "reference"
    return "reliable"


# ── 主分析（方案§8.2）──────────────────────────────────────────────────────────
def analyze_trend(works: list[dict], snapshots: list[dict] | None = None, *,
                  industry: str = "general", segment: str = "shop_owner",
                  stage: str = "growth", metric: str = "like") -> dict[str, Any]:
    """趋势分析主入口（确定性·纯统计·零 LLM）。

    works：逐条作品（含 create_time）→ 作品基线/转折点/承接力（day-1 可做）。
    snapshots：复访快照（含 timestamp/follower）→ 粉丝增速（需累积·可空）。
    """
    works = [w for w in (works or []) if isinstance(w, dict) and w.get("create_time") is not None]

    # —— 阶段门 / 样本门（方案§8.2）——
    if stage == "cold_start":
        return {"mode": "target_setting", "note": "无趋势数据·走基准目标设定（见对标段）",
                "confidence": "insufficient"}
    if len(works) < MIN_WORKS_FOR_BASELINE:
        return {"mode": "breakthrough_check",
                "note": f"样本 {len(works)}<{MIN_WORKS_FOR_BASELINE} 条·不下趋势结论·"
                        f"先看单条能否破0（再发 {MIN_WORKS_FOR_BASELINE - len(works)} 条可做趋势）",
                "confidence": "insufficient", "n_works": len(works)}

    series = build_series(works, metric=metric)
    series = mark_outliers(series)
    works_sorted = sorted(works, key=lambda w: w["create_time"])

    work_trend = baseline_trend(series)
    fans_trend = growth_trend(snapshots or [])

    tps = detect_change_points(series)
    tps = attribute_turning_points(works_sorted, tps, metric=metric)

    alerts = decline_alerts(work_trend, fans_trend, series, segment=segment)

    seasonality = INDUSTRY_SEASONALITY.get(industry, "medium")

    return {
        "mode": "full",
        "work_baseline": work_trend,
        "fans_trend": fans_trend,
        "turning_points": tps,
        "alerts": alerts,
        "n_works": len(works),
        "n_outliers": sum(1 for p in series if p.is_outlier),
        "seasonality": seasonality,
        "confidence": work_trend.confidence,
        "note": "",
    }


# ── 渲染（说人话·方案§六.1）────────────────────────────────────────────────────
_LEVEL_ICON = {"red": "🟥", "yellow": "🟨", "green": "🟢"}


def render_trend_section(works: list[dict], snapshots: list[dict] | None = None, *,
                         industry: str = "general", segment: str = "shop_owner",
                         stage: str = "growth", metric: str = "like") -> str:
    """渲染"趋势轨迹"报告段（Markdown·看导数不看存量·诚实标）。

    可单独调用，也可由 build_report 经 _md 注入。
    """
    res = analyze_trend(works, snapshots, industry=industry, segment=segment,
                        stage=stage, metric=metric)
    L: list[str] = []
    P = L.append

    P("## 趋势轨迹：你在涨还是在衰（看导数不看存量）")
    P("")
    P("> 同样 4.2 万粉，一个在翻倍涨、一个正在崩——**方案完全相反**。"
      "「现在多少粉」不如「接下来怎么走」重要。")
    P("")

    if res["mode"] == "target_setting":
        P("- 你还没有历史作品（冷启动），没有轨迹可分析。先按对标段的「第一阶段达标目标」起步。")
        P("")
        return "\n".join(L)

    if res["mode"] == "breakthrough_check":
        P(f"- {res['note']}")
        P("> 趋势分析最易玄学——几条作品就下「在衰退」结论多半是噪音。攒够样本再判，是诚实。")
        P("")
        return "\n".join(L)

    # 作品基线趋势（B 维·day-1）
    wt: TrendResult = res["work_baseline"]
    P(f"**① 作品基线趋势**：{_DIR_CN.get(wt.direction, wt.direction)}")
    sig_txt = ("显著（不是随机波动）" if wt.significance <= 0.10
               else "不显著（更可能是短期波动·按平稳处理）")
    P(f"- 把你 {res['n_works']} 条作品按发布时间排开看基线（已剔除 {res['n_outliers']} 条爆款离群，"
      f"避免一条爆款把判断带偏）。趋势{sig_txt}。")
    if wt.confidence == "reference":
        P("- ⚠️ 样本 10–20 条·参考级（再多发几条结论更稳）。")
    P("")

    # 粉丝增速（A 维·需复访）
    P("**② 粉丝增速趋势**")
    ft = res["fans_trend"]
    if ft is None:
        P("- 📦 **需复访**：粉丝增速曲线要至少 2 次诊断（≥4 个时间点）才能画。"
          "这次只有单次快照——下次复诊时会自动补上「加速涨/减速涨/净掉粉」的判断。")
    else:
        P(f"- {_DIR_CN.get(ft.direction, ft.direction)}"
          + (f"　{ft.note}" if ft.note else ""))
    P("")

    # 转折点（最高价值·B/D）
    P("**③ 转折点：哪条作品是分水岭**")
    tps: list[TurningPoint] = res["turning_points"]
    if not tps:
        P("- 没检测到明显转折点——你的作品基线比较平稳，没有某条之后突然起飞或崩盘。")
    else:
        for tp in tps:
            arrow = "正向↑" if tp.direction == "positive" else "负向↓"
            P(f"- 第 **{tp.work_index + 1}** 条附近出现 **{arrow}转折**（基线跃迁 {tp.jump:+.0%}）。")
            nt = tp.action_diff.get("new_topics") or []
            if tp.external_pulse:
                P(f"  - ⚠️ {tp.note}——**别把运气当方法去复制**（这是玄学最大来源）。")
            elif tp.attributable:
                tip = f"（新增方向：{'、'.join(nt)}）" if nt else ""
                verb = "建议复制这个形式" if tp.direction == "positive" else "查这次改动是不是改坏了"
                P(f"  - ✅ {tp.note}{tip}——{verb}。")
            else:
                P(f"  - {tp.note}。")
    P("")

    # 衰退预警（分级）
    P("**④ 衰退预警**")
    alerts: list[DeclineAlert] = res["alerts"]
    if not alerts:
        P("- 暂无衰退信号。")
    else:
        for a in alerts:
            P(f"- {_LEVEL_ICON.get(a.level, '')} **{a.signal}**：{a.evidence} → {a.suggested_action}")
    P("")

    # 防玄学三问（方案§七 总纲）
    seas = {"strong": "强", "medium": "中", "weak": "弱"}.get(res["seasonality"], "中")
    P(f"> ⚠️ **诚实说**：①基于 {res['n_works']} 条作品；②你这赛道季节性**{seas}**"
      + ("（淡旺季会让数据起伏，别把淡季掉量当衰退）" if res["seasonality"] != "weak" else "")
      + "；③转折点已强制排除外部脉冲才归因。短期波动≠趋势，样本不足时我宁可不下结论。")
    if res["seasonality"] in ("strong", "medium"):
        P("> 大盘提醒：若全赛道同期都在跌，那是平台大盘不是你的账号问题（需赛道基准做相对趋势·见对标段）。")
    P("")
    return "\n".join(L)
