"""同赛道百分位对标基准 · benchmark.py · 确定性·零 LLM·纯统计。

来源方法论：benchmark-percentile-adaptive-research.md（03 标准层）
  把诊断从「绝对快照」升级为「相对坐标」——单粉 6438 赞 → 同赛道同体量 P62。
  五维对标：A 体量 / B 互动 / C 内容力 / D 成长 / E 商业。

数据源接口可插拔（方案§四·灰度核心）：
  - 不自建抓取赛道样本（商业链不自建爬虫·D-据 decision_probe_tikhub_keep_paid）。
  - 定义 BenchmarkRepo 接口——基准画像（行业×体量桶×指标）由 provider 提供。
  - 内置 ExpertSeedRepo 经验带兜底（day-1 可用·标"参考级"）。
  - LocalAccumRepo 像 attribution_cache 一样本地脱敏沉淀（每次诊断喂样本）；
    过 N_min 切真实分位，不足时回退传入兜底基准并标来源/置信。

防玄学（方案§七）：N<30 标"参考·样本不足"只给经验带；分位结论可回答三问
  （多少样本/何时采/什么口径）；只用中位数+分位带做锚，不用均值。

纯函数·零网络·零 LLM。
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Any, Protocol

# ── 防玄学样本门（方案§七 N_min 门）─────────────────────────────────────────────
N_RELIABLE = 100   # ≥100 → '可信级'
N_REFERENCE = 30   # 30–99 → '参考级'；<30 → '经验级'（不给精确分位）

# 口径字典版本（方案§七·防口径漂移：互动率=赞+评+转/播放）
METRIC_DICT_VERSION = "v1"

# ── 五维指标键（A 体量不进分位·作分桶前提；B/C/D/E 进分位）────────────────────────
METRICS = ("interaction_rate", "completion_rate", "play_fan_ratio",
           "growth_rate", "fan_unit_value")

_METRIC_CN = {
    "interaction_rate": "互动率",
    "completion_rate": "完播率",
    "play_fan_ratio": "播粉比",
    "growth_rate": "涨粉率",
    "fan_unit_value": "单粉价值",
}

# 维度组归属（方案§二·五组锚点）
_METRIC_GROUP = {
    "interaction_rate": "B 互动质量",
    "completion_rate": "C 内容力",
    "play_fan_ratio": "C 内容力",
    "growth_rate": "D 成长速度",
    "fan_unit_value": "E 商业",
}

# ── 行业归一化（_track 赛道名 → benchmark 行业键）─────────────────────────────────
# 与 account_report._track 输出对齐；未命中归 'general'
_INDUSTRY_HINTS: list[tuple[tuple[str, ...], str]] = [
    (("B2B", "供货", "产业带", "招商", "加盟", "工厂", "源头"), "catering_local"),
    (("美食", "探店", "吃播", "菜谱", "厨艺", "餐饮"), "catering_local"),
    (("医美", "美业", "护肤", "美妆", "时尚", "整形"), "beauty"),
    (("知识", "科普", "考证", "财经", "理财", "成长", "励志", "职场", "教培", "课"), "education"),
    (("带货", "电商", "选品", "好物", "种草", "橱窗", "母婴", "育儿", "家居"), "ecommerce"),
    (("健身", "运动", "瑜伽", "兴趣"), "fitness"),
    (("颜值", "才艺", "舞蹈", "唱歌", "搞笑", "泛娱乐"), "entertainment"),
    (("IP", "创始人", "人设"), "ip_founder"),
]


def resolve_industry(track_name: str) -> str:
    """赛道名 → benchmark 行业键（与方案§三 行业画像对齐）。"""
    t = track_name or ""
    for kws, ind in _INDUSTRY_HINTS:
        if any(k in t for k in kws):
            return ind
    return "general"


# ── 行业差异化体量分桶（方案§五）────────────────────────────────────────────────
# 各行业边界 [micro_max, small_max, mid_max, large_max]，超 large_max → top
_BUCKET_EDGES: dict[str, tuple[int, int, int, int]] = {
    "education":     (2_000, 10_000, 50_000, 200_000),   # 垂直B端/教培/IP下移
    "ip_founder":    (2_000, 10_000, 50_000, 200_000),
    "beauty":        (5_000, 30_000, 100_000, 500_000),  # 本地号天花板低
    "catering_local": (5_000, 30_000, 100_000, 500_000),
    "ecommerce":     (10_000, 50_000, 300_000, 1_000_000),
    "fitness":       (10_000, 50_000, 300_000, 1_000_000),
    "entertainment": (50_000, 300_000, 1_000_000, 5_000_000),  # 流量盘大上移
    "general":       (5_000, 30_000, 100_000, 500_000),
}
_BUCKETS = ("micro", "small", "mid", "large", "top")


def resolve_bucket(industry: str, fans: int) -> str:
    """行业差异化分桶（方案§五·同体量对标的前提）。"""
    edges = _BUCKET_EDGES.get(industry, _BUCKET_EDGES["general"])
    f = max(0, int(fans or 0))
    for name, edge in zip(_BUCKETS, edges):
        if f < edge:
            return name
    return "top"


# ── 经验健康带（方案§三·🟨经验区间；及格锚🟩有出处）────────────────────────────────
# 每行业每指标 → (下沿, 上沿)；据此构造经验五档分位（无真实样本时的兜底）
_EXPERIENCE_BANDS: dict[str, dict[str, tuple[float, float]]] = {
    "catering_local": {"interaction_rate": (0.04, 0.07), "completion_rate": (0.25, 0.40),
                       "play_fan_ratio": (3.0, 10.0), "growth_rate": (0.01, 0.08),
                       "fan_unit_value": (1.0, 3.0)},
    "beauty":         {"interaction_rate": (0.03, 0.06), "completion_rate": (0.30, 0.45),
                       "play_fan_ratio": (2.0, 6.0), "growth_rate": (0.01, 0.06),
                       "fan_unit_value": (5.0, 30.0)},
    "education":      {"interaction_rate": (0.03, 0.05), "completion_rate": (0.20, 0.35),
                       "play_fan_ratio": (1.0, 4.0), "growth_rate": (0.01, 0.05),
                       "fan_unit_value": (10.0, 50.0)},
    "ecommerce":      {"interaction_rate": (0.03, 0.05), "completion_rate": (0.30, 0.40),
                       "play_fan_ratio": (1.5, 5.0), "growth_rate": (0.01, 0.06),
                       "fan_unit_value": (3.0, 10.0)},
    "fitness":        {"interaction_rate": (0.04, 0.06), "completion_rate": (0.35, 0.50),
                       "play_fan_ratio": (1.5, 5.0), "growth_rate": (0.01, 0.06),
                       "fan_unit_value": (5.0, 30.0)},
    "entertainment":  {"interaction_rate": (0.05, 0.08), "completion_rate": (0.40, 0.60),
                       "play_fan_ratio": (5.0, 20.0), "growth_rate": (0.02, 0.12),
                       "fan_unit_value": (0.1, 2.0)},
    "ip_founder":     {"interaction_rate": (0.03, 0.06), "completion_rate": (0.30, 0.45),
                       "play_fan_ratio": (1.0, 3.0), "growth_rate": (0.005, 0.03),
                       "fan_unit_value": (50.0, 500.0)},
    "general":        {"interaction_rate": (0.03, 0.05), "completion_rate": (0.30, 0.45),
                       "play_fan_ratio": (1.5, 5.0), "growth_rate": (0.01, 0.06),
                       "fan_unit_value": (1.0, 5.0)},
}

# 冷启动绝对及格门（方案§六.2·🟩有出处锚点）
_COLD_START_GATE: dict[str, dict[str, float]] = {
    "_default": {"completion_rate": 0.30, "interaction_rate": 0.03, "play_fan_ratio": 3.0},
    "catering_local": {"completion_rate": 0.30, "interaction_rate": 0.04, "play_fan_ratio": 3.0},
    "education": {"completion_rate": 0.20, "interaction_rate": 0.03, "play_fan_ratio": 1.0},
    "entertainment": {"completion_rate": 0.40, "interaction_rate": 0.05, "play_fan_ratio": 5.0},
}

# 人群轴目标分位（方案§3.2）
_SEGMENT_TARGET_PCT = {"shop_owner": 60, "fresh_grad": 50, "midage": 50, "sidehustle": 65}

# 五档分位带（方案§六.1）
_BAND_LABELS = ("垫底", "偏弱", "中位", "中上", "头部")


# ── 数据结构（方案§八.1）────────────────────────────────────────────────────────
@dataclass
class BenchmarkProfile:
    """基准画像：行业×体量桶×指标 的分位分布。"""
    industry: str
    fans_bucket: str
    metric: str
    percentiles: dict[int, float]   # {10:..,25:..,50:..,75:..,90:..}
    sample_size: int
    source: str                     # 'self_built'|'third_party'|'platform_rank'|'sampling'|'expert'
    captured_at: str
    confidence: str = "experience"  # reliable|reference|experience
    metric_dict_version: str = METRIC_DICT_VERSION

    def __post_init__(self) -> None:
        self.confidence = confidence_of(self.sample_size)


@dataclass
class BenchmarkResult:
    """单账号单指标对标结果。"""
    metric: str
    account_value: float | None
    percentile: float | None
    band: str | None
    is_weakest: bool
    target_value: float | None
    confidence: str
    source: str
    note: str = ""


# ── 数据源接口（方案§四·可插拔灰度核心）────────────────────────────────────────
class BenchmarkRepo(Protocol):
    """基准数据源接口——灰度 feed 在此接口后接入（第三方/榜单/抽样/自建）。

    商业链不自建爬虫：实现方负责喂分位画像，benchmark() 只做统计对标。
    """

    def get(self, industry: str, bucket: str, metric: str) -> BenchmarkProfile | None:
        ...


def confidence_of(n: int) -> str:
    if n >= N_RELIABLE:
        return "reliable"
    if n >= N_REFERENCE:
        return "reference"
    return "experience"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _experience_percentiles(lo: float, hi: float) -> dict[int, float]:
    """把经验健康带 [下沿,上沿] 摊成五档经验分位（线性·仅供兜底）。

    约定：P25=下沿、P75=上沿、P50=中点；P10/P90 外推半带宽。
    """
    span = hi - lo
    mid = (lo + hi) / 2
    return {10: round(lo - span * 0.5, 6), 25: round(lo, 6), 50: round(mid, 6),
            75: round(hi, 6), 90: round(hi + span * 0.5, 6)}


class ExpertSeedRepo:
    """经验带兜底基准源（方案§四 阶段一·day-1 可用·confidence=experience）。

    sample_size=0 → 永远经验级；分位由 _EXPERIENCE_BANDS 摊出。
    """

    def get(self, industry: str, bucket: str, metric: str) -> BenchmarkProfile | None:
        band = _EXPERIENCE_BANDS.get(industry, _EXPERIENCE_BANDS["general"]).get(metric)
        if band is None:
            return None
        lo, hi = band
        return BenchmarkProfile(
            industry=industry, fans_bucket=bucket, metric=metric,
            percentiles=_experience_percentiles(lo, hi),
            sample_size=0, source="expert", captured_at=_now_iso(),
        )


# ── 自建库脱敏沉淀（方案§四 路径①·§8.3·像 attribution_cache）─────────────────────
_REPO_ROOT = pathlib.Path.home() / ".probe_cache" / "benchmark"


class LocalAccumRepo:
    """本地脱敏样本库（路径①·每次诊断喂样本·过 N_min 切真实分位）。

    存储：~/.probe_cache/benchmark/{industry}__{bucket}.json
      {metric: [value, ...]}  仅存脱敏后的指标值（不存账号身份）。
    不足 N_min 时 get() 回退 fallback（默认 ExpertSeedRepo）并标来源。
    """

    def __init__(self, root: pathlib.Path | None = None,
                 fallback: BenchmarkRepo | None = None) -> None:
        self._root = root or _REPO_ROOT
        self._fallback = fallback or ExpertSeedRepo()

    def _path(self, industry: str, bucket: str) -> pathlib.Path:
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in f"{industry}__{bucket}")
        return self._root / f"{safe[:96]}.json"

    def _load(self, industry: str, bucket: str) -> dict[str, list[float]]:
        p = self._path(industry, bucket)
        if not p.exists():
            return {}
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
            return raw if isinstance(raw, dict) else {}
        except Exception:  # noqa: BLE001
            return {}

    def ingest(self, industry: str, bucket: str, metrics: dict[str, float]) -> None:
        """脱敏沉淀一个账号的归一化指标（方案§8.3 ingest_for_benchmark）。"""
        self._root.mkdir(parents=True, exist_ok=True)
        store = self._load(industry, bucket)
        for m, v in (metrics or {}).items():
            if m not in METRICS or v is None:
                continue
            store.setdefault(m, []).append(round(float(v), 6))
        self._path(industry, bucket).write_text(
            json.dumps(store, ensure_ascii=False), encoding="utf-8")

    def get(self, industry: str, bucket: str, metric: str) -> BenchmarkProfile | None:
        vals = sorted(self._load(industry, bucket).get(metric, []))
        if len(vals) < N_REFERENCE:
            # 样本不足 → 回退兜底（诚实标来源·方案§四阶段一）
            return self._fallback.get(industry, bucket, metric)
        pcts = {p: percentile_value_from_sorted(vals, p) for p in (10, 25, 50, 75, 90)}
        return BenchmarkProfile(
            industry=industry, fans_bucket=bucket, metric=metric,
            percentiles=pcts, sample_size=len(vals),
            source="self_built", captured_at=_now_iso(),
        )


# ── 分位计算（纯统计）──────────────────────────────────────────────────────────
def percentile_value_from_sorted(sorted_vals: list[float], pct: float) -> float:
    """已排序样本求 pct 分位值（线性插值·与 numpy 默认一致）。"""
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    rank = (pct / 100.0) * (len(sorted_vals) - 1)
    lo_i = int(rank)
    hi_i = min(lo_i + 1, len(sorted_vals) - 1)
    frac = rank - lo_i
    return float(sorted_vals[lo_i] + (sorted_vals[hi_i] - sorted_vals[lo_i]) * frac)


def percentile_of(value: float, percentiles: dict[int, float]) -> float:
    """给定分位锚点表，反查 value 落在第几百分位（线性插值·钳 0–100）。"""
    if not percentiles:
        return 50.0
    pts = sorted(percentiles.items())  # [(10,v10),...]
    # 低于最低锚 / 高于最高锚 → 端点外插（钳到 [0,100]）
    if value <= pts[0][1]:
        return float(max(0.0, pts[0][0] - (pts[0][1] - value)))  # 朝 0 收
    if value >= pts[-1][1]:
        return float(min(100.0, pts[-1][0] + (value - pts[-1][1])))  # 朝 100 收
    for (p_lo, v_lo), (p_hi, v_hi) in zip(pts, pts[1:]):
        if v_lo <= value <= v_hi:
            if v_hi == v_lo:
                return float(p_lo)
            frac = (value - v_lo) / (v_hi - v_lo)
            return float(p_lo + (p_hi - p_lo) * frac)
    return 50.0


def percentile_value(percentiles: dict[int, float], pct: int) -> float:
    """从分位锚点表取目标分位的值（用于目标设定·线性插值）。"""
    if not percentiles:
        return 0.0
    if pct in percentiles:
        return float(percentiles[pct])
    pts = sorted(percentiles.items())
    if pct <= pts[0][0]:
        return float(pts[0][1])
    if pct >= pts[-1][0]:
        return float(pts[-1][1])
    for (p_lo, v_lo), (p_hi, v_hi) in zip(pts, pts[1:]):
        if p_lo <= pct <= p_hi:
            frac = (pct - p_lo) / (p_hi - p_lo)
            return float(v_lo + (v_hi - v_lo) * frac)
    return float(pts[-1][1])


def to_band(pct: float) -> str:
    """百分位 → 五档带（方案§六.1）。"""
    return _BAND_LABELS[min(int(pct // 20), 4)]


# ── 账号指标抽取（从 account dict 归一化为五维口径）────────────────────────────────
def extract_account_metrics(account: dict[str, Any],
                            prev_follower: int | None = None) -> dict[str, float]:
    """从 account 提取五维口径指标（统一口径字典·方案§七）。

    互动率代理 = avg_like/(follower+1)（无评论/转发明细时的保守代理）。
    完播率/单粉价值多为黑盒——拿不到则不放入（不冒充）。
    涨粉率需 prev_follower（复访累积·无则不放入·标"需复访"）。
    """
    fol = account.get("follower") or 0
    avg_like = account.get("avg_like") or 0
    out: dict[str, float] = {}
    if fol > 0:
        out["interaction_rate"] = avg_like / (fol + 1)
        # 播粉比：单条均播/粉。无 play_count（黑盒/jzl 缺口）→ 用 avg_like 的保守放大代理仅当显式给出
        if account.get("avg_play"):
            out["play_fan_ratio"] = (account["avg_play"]) / (fol + 1)
    cr = account.get("completion_rate")
    if cr is not None:
        out["completion_rate"] = float(cr)
    fuv = account.get("fan_unit_value")
    if fuv is not None:
        out["fan_unit_value"] = float(fuv)
    if prev_follower and prev_follower > 0 and fol > prev_follower:
        out["growth_rate"] = (fol - prev_follower) / prev_follower
    return out


# ── 核心对标（方案§八.2）────────────────────────────────────────────────────────
def benchmark(account_metrics: dict[str, float], industry: str, fans: int,
              segment: str = "shop_owner", stage: str = "growth",
              repo: BenchmarkRepo | None = None) -> list[BenchmarkResult]:
    """五维对标主函数（确定性·纯统计·零 LLM）。

    repo：基准数据源（默认 ExpertSeedRepo 经验兜底·灰度 feed 在此接口接入）。
    stage：cold_start（目标设定）/ startup（只判及格门）/ growth/mature（全维分位）。
    """
    repo = repo or ExpertSeedRepo()
    bucket = resolve_bucket(industry, fans)
    results: list[BenchmarkResult] = []

    for metric in METRICS:
        value = account_metrics.get(metric)
        prof = repo.get(industry, bucket, metric)

        # —— 冷启动：不对标自身，给目标设定（方案§六.2）——
        if stage == "cold_start":
            target = _cold_start_target(metric, industry)
            if target is None:
                continue
            results.append(BenchmarkResult(
                metric, value, None, None, False, target,
                "experience", "expert", note="冷启动·目标设定模式·达标即进小号池"))
            continue

        if value is None:
            continue  # 拿不到该指标不冒充（黑盒/需复访）

        # —— 起号期：只判绝对及格门，不给分位（方案§3.3）——
        if stage == "startup":
            gate = _cold_start_target(metric, industry)
            if gate is None:
                continue
            ok = value >= gate
            results.append(BenchmarkResult(
                metric, value, None, None, False, gate, "experience", "expert",
                note=("及格门已达✅" if ok else f"未达及格门（目标 {gate:g}）·起号期先冲门")))
            continue

        # —— 防玄学门：无画像 或 样本<N_min → 经验带（不给精确分位）——
        if prof is None:
            continue
        if prof.sample_size < N_REFERENCE:
            pct = percentile_of(value, prof.percentiles)
            band = to_band(pct)
            note = "⚠️ 参考·样本不足（经验带·非真实分位）"
            conf = "experience"
        else:
            pct = percentile_of(value, prof.percentiles)
            band = to_band(pct)
            note = "" if prof.confidence == "reliable" else "⚠️ 参考级（样本累积中）"
            conf = prof.confidence

        target_pct = _SEGMENT_TARGET_PCT.get(segment, 60)
        target = percentile_value(prof.percentiles, target_pct)

        results.append(BenchmarkResult(
            metric, value, round(pct, 1), band, False,
            round(target, 6), conf, prof.source, note))

    _mark_weakest(results)
    return results


def _cold_start_target(metric: str, industry: str) -> float | None:
    gate = _COLD_START_GATE.get(industry, _COLD_START_GATE["_default"])
    return gate.get(metric)


def _mark_weakest(results: list[BenchmarkResult]) -> None:
    """标短板（最低分位维度·木桶高亮·方案§六.1）。"""
    scored = [r for r in results if r.percentile is not None]
    if not scored:
        return
    weakest = min(scored, key=lambda r: r.percentile)
    weakest.is_weakest = True


# ── 渲染（说人话·分位带表达·方案§六.1）────────────────────────────────────────────
def render_benchmark_section(account: dict[str, Any], track_name: str,
                             *, segment: str = "shop_owner", stage: str = "growth",
                             repo: BenchmarkRepo | None = None,
                             prev_follower: int | None = None) -> str:
    """渲染"同赛道对标"报告段（Markdown·分位带+短板高亮+诚实标）。

    可单独调用，也可由 build_report 经 _md 注入。
    """
    industry = resolve_industry(track_name)
    fans = account.get("follower") or 0
    bucket = resolve_bucket(industry, fans)
    metrics = extract_account_metrics(account, prev_follower=prev_follower)
    results = benchmark(metrics, industry, fans, segment=segment, stage=stage, repo=repo)

    L: list[str] = []
    P = L.append
    bucket_cn = {"micro": "微号", "small": "小号", "mid": "中号",
                 "large": "大号", "top": "头部"}.get(bucket, bucket)

    P("## 同赛道对标：你在同行里排第几")
    P("")
    P(f"> 绝对数字（比如「平均 {account.get('avg_like') or 0} 赞」）脱离赛道没意义——"
      f"餐饮号 6438 赞可能垫底，知识号 6438 赞可能头部。这一段把你换算成**相对坐标**。")
    P(f"> 对标范围：**{track_name}**赛道 · **{bucket_cn}**体量段（{fans:,} 粉）。")
    P("")

    if stage == "cold_start":
        P("**你还没有自己的数据（冷启动）——所以不跟自己比，而是给你「第一阶段达标目标」：**")
        P("")
        for r in results:
            if r.target_value is None:
                continue
            P(f"- {_METRIC_CN.get(r.metric, r.metric)}目标 ≥ **{_fmt(r.metric, r.target_value)}**")
        P("")
        P("> 达到=进入小号池有戏；连续 3 条达标=可进成长期做分位对标。"
          "（目标值为赛道经验门🟨，及格锚有出处🟩）")
        P("")
        return "\n".join(L)

    scored = [r for r in results if r.percentile is not None]
    if not scored and stage == "startup":
        P("**你处在起号期（样本不足做分位）——先看是否触及最低及格线：**")
        P("")
        for r in results:
            if r.target_value is None or r.account_value is None:
                continue
            P(f"- {_METRIC_CN.get(r.metric, r.metric)}：你 {_fmt(r.metric, r.account_value)}"
              f" → {r.note}")
        P("")
        P("> 起号期单条分位不可信，只看是否过门。过门后再做分位对标。")
        P("")
        return "\n".join(L)

    if not scored:
        P("- 这次只拿到汇总数据，可对标的维度不足（完播率/单粉价值是平台黑盒，涨粉率需复访累积）。"
          "补上后能告诉你：你在同赛道同体量号里每个维度排 P 几、短板是哪个。")
        P("")
        return "\n".join(L)

    # 维度雷达（方案§六.1·③）
    P("**你在同赛道同体量号里的各维度位次（分位越高越好）：**")
    P("")
    for r in scored:
        flag = " 🔴**（主短板·先补这个）**" if r.is_weakest else ""
        src = {"self_built": "自建库", "third_party": "第三方", "platform_rank": "平台榜",
               "sampling": "定向抽样", "expert": "行业经验"}.get(r.source, r.source)
        note = f" · {r.note}" if r.note else ""
        P(f"- **{_METRIC_CN.get(r.metric, r.metric)}**（{_METRIC_GROUP.get(r.metric, '')}）："
          f"你 {_fmt(r.metric, r.account_value)} → **P{r.percentile:.0f}（{r.band}）**"
          f"{flag}　〔基准来源：{src}{note}〕")
    P("")

    weakest = next((r for r in scored if r.is_weakest), None)
    if weakest:
        P(f"👉 **一句话**：你最拖后腿的是 **{_METRIC_CN.get(weakest.metric, weakest.metric)}**"
          f"（{weakest.band}），木桶水位由它决定——**先补这块**，比哪儿都强。")
        if weakest.target_value is not None:
            P(f"目标：把它冲到 **{_fmt(weakest.metric, weakest.target_value)}**"
              f"（同赛道 P{_SEGMENT_TARGET_PCT.get(segment, 60)} 水平）。")
        P("")

    # 诚实三问（方案§七 防玄学总纲）
    sample_levels = {r.confidence for r in scored}
    if "reliable" not in sample_levels:
        P("> ⚠️ **诚实说**：当前基准多为行业经验带（自建样本库累积中），分位是**参考级**不是精确级。"
          "等同赛道同体量样本攒过 100 个，会自动升级为可信级真实分位。")
    P(f"> 口径统一：互动率=赞+评+转/播放（口径字典 {METRIC_DICT_VERSION}）；只用中位数+分位带做锚，不用易被爆款拉偏的均值。")
    P("")
    return "\n".join(L)


def _fmt(metric: str, value: float | None) -> str:
    if value is None:
        return "—"
    if metric in ("interaction_rate", "completion_rate", "growth_rate"):
        return f"{value * 100:.1f}%"
    if metric == "fan_unit_value":
        return f"{value:.1f}元/粉"
    if metric == "play_fan_ratio":
        return f"{value:.1f}×"
    return f"{value:g}"


def ingest_for_benchmark(account: dict[str, Any], track_name: str,
                         repo: LocalAccumRepo,
                         prev_follower: int | None = None) -> dict[str, Any]:
    """每次诊断后调用：脱敏 + 归一化口径 + 入自建库累积分布（方案§8.3）。

    返回 {industry, bucket, ingested:[metric...]} 供调用方记录。
    """
    industry = resolve_industry(track_name)
    bucket = resolve_bucket(industry, account.get("follower") or 0)
    metrics = extract_account_metrics(account, prev_follower=prev_follower)
    repo.ingest(industry, bucket, metrics)
    return {"industry": industry, "bucket": bucket, "ingested": sorted(metrics.keys())}
