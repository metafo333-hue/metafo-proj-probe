"""时序导数引擎 · 阶梯4 预测层(单次采集可算的那半)。

元矿方法论矿脉①:现状只看"现在多少"(零阶),没看"在加速还是减速"(一阶导)。
本模块从**单次采集的作品矩阵**(每条带 create_time + 互动)算时序导数——不需多次采集、
不重采、边际成本≈0,把系统从"诊断级"推到"预测级"。

可单次算(本模块):
  互动斜率   近N条 vs 前N条 eng 均值 → 加速/减速/平稳 + 幅度
  爆款衰减   峰值视频之后的回落速度 → 守得住/接不住
  节奏趋势   发布间隔 近期 vs 早期 → 加快/放缓/断更
  阶段判定   上升期/平台期/衰退期(综合斜率+节奏)
  下条预估   近期均值 ± 波动(诚实标 proxy·like 代理非 play)
  处方见效   若衰退因断更 → 恢复日更见效预估(启发式·标待校准)

需多次采集才算(留给完整 B·本模块标"积累中"):
  账号涨粉轨迹曲线 / 跨期画像漂移 / 处方前后真实对照。

⚠️ eng = like + comment*2 + collect*3(与 content_dna 一致·点赞代理·play 需逐条统计端点)。
样本 <6 条无法切两半 → 标低置信"积累中"·不硬给趋势。
"""
from __future__ import annotations

import statistics as _S
from datetime import datetime
from typing import Any


def _eng(w: dict) -> int:
    return int((w.get("like") or 0) + (w.get("comment") or 0) * 2 + (w.get("collect") or 0) * 3)


def _days_between(t1, t2) -> float | None:
    try:
        return abs(t2 - t1) / 86400.0
    except Exception:  # noqa: BLE001
        return None


def analyze_time_series(works: list[dict]) -> dict[str, Any]:
    """作品矩阵 → 时序导数 + 阶段判定 + 下条预估(单次可算)。"""
    ts = [w for w in (works or []) if w.get("create_time")]
    ts.sort(key=lambda w: w["create_time"])           # 旧→新
    n = len(ts)
    if n < 6:
        return {"enough": False, "conf": "low",
                "verdict": f"作品样本 {n} 条(<6)·时序趋势积累中·需更多作品才能算导数",
                "stage": None, "next_estimate": None}

    half = n // 2
    earlier, recent = ts[:half], ts[half:]
    e_avg = _S.mean(_eng(w) for w in earlier)
    r_avg = _S.mean(_eng(w) for w in recent)
    slope_pct = round((r_avg - e_avg) / e_avg * 100, 1) if e_avg else None

    # 互动斜率方向
    if slope_pct is None:
        trend = "无法判定"
    elif slope_pct >= 20:
        trend = f"加速上升(近期互动 +{slope_pct}%)"
    elif slope_pct <= -20:
        trend = f"减速下滑(近期互动 {slope_pct}%)"
    else:
        trend = f"平稳({'+' if slope_pct >= 0 else ''}{slope_pct}%)"

    # 节奏趋势(发布间隔近期 vs 早期)
    def _intervals(seg):
        d = []
        for i in range(1, len(seg)):
            gap = _days_between(seg[i - 1]["create_time"], seg[i]["create_time"])
            if gap is not None:
                d.append(gap)
        return _S.mean(d) if d else None
    e_int, r_int = _intervals(earlier), _intervals(recent)
    rhythm = None
    if e_int and r_int:
        if r_int > e_int * 1.5:
            rhythm = f"更新放缓(间隔 {e_int:.1f}天→{r_int:.1f}天·变慢)"
        elif r_int < e_int * 0.67:
            rhythm = f"更新加快(间隔 {e_int:.1f}天→{r_int:.1f}天·变快)"
        else:
            rhythm = f"节奏稳定(约 {r_int:.1f}天/条)"
    # 断更检测:最近一条距今
    last_gap = None
    if ts:
        try:
            last_gap = _days_between(ts[-1]["create_time"],
                                    datetime.now().timestamp())  # noqa: DTZ005
        except Exception:  # noqa: BLE001
            last_gap = None

    # 爆款衰减:峰值视频后续回落
    peak_i = max(range(n), key=lambda i: _eng(ts[i]))
    decay = None
    if peak_i < n - 2:
        after = [_eng(w) for w in ts[peak_i + 1:peak_i + 4]]
        peak_v = _eng(ts[peak_i])
        if peak_v and after:
            hold = round(_S.mean(after) / peak_v * 100)
            decay = (f"爆款后守住 {hold}%" +
                     ("·接得住(可复制)" if hold >= 40 else "·接不住(爆款是偶发)"))

    # 阶段判定(综合)
    if slope_pct is not None and slope_pct >= 20:
        stage = "上升期"
    elif slope_pct is not None and slope_pct <= -20:
        stage = "衰退期" if not (last_gap and last_gap > 14) else "衰退期(疑断更触发)"
    else:
        stage = "平台期"

    # 下条预估(近期均值±波动·诚实标 proxy)
    r_engs = [_eng(w) for w in recent]
    r_likes = [w.get("like") or 0 for w in recent]
    next_est = None
    if r_likes:
        lo = round(min(r_likes))
        hi = round(max(r_likes))
        mid = round(_S.median(r_likes))
        next_est = {"like_median": mid, "like_range": [lo, hi],
                    "note": "基于近期作品赞数中位(代理·非play·实际看选题/钩子)"}

    # 处方见效预估(仅衰退+断更场景·启发式·待校准)
    rx_eta = None
    if stage.startswith("衰退") and last_gap and last_gap > 7:
        rx_eta = (f"近 {round(last_gap)} 天未更=衰退主因·恢复日更后通常 7-14 天算法"
                  "重新给量(经验值·待校准)")

    conf = "high" if n >= 12 else "mid"
    return {
        "enough": True, "conf": conf,
        "stage": stage,
        "trend": trend, "slope_pct": slope_pct,
        "rhythm": rhythm, "last_post_days": round(last_gap) if last_gap else None,
        "decay": decay,
        "next_estimate": next_est,
        "rx_eta": rx_eta,
        "verdict": f"{stage}·{trend}",
        "sample": n,
        "proxy_note": "互动=赞+评×2+藏×3 代理·单次采集算导数·账号涨粉轨迹需多次采集(积累中)",
    }


def render_ts_md(ts: dict) -> str:
    if not ts.get("enough"):
        return f"- ⏳ {ts.get('verdict')}"
    L = [f"- 📈 **阶段:{ts['stage']}** · {ts['trend']}"]
    if ts.get("rhythm"):
        L.append(f"- ⏱️ {ts['rhythm']}" + (f"·最近 {ts['last_post_days']} 天未更" if ts.get("last_post_days") else ""))
    if ts.get("decay"):
        L.append(f"- 💥 {ts['decay']}")
    if ts.get("next_estimate"):
        ne = ts["next_estimate"]
        L.append(f"- 🔮 下条预估:赞约 {ne['like_median']}(区间 {ne['like_range'][0]}-{ne['like_range'][1]}·{ne['note']})")
    if ts.get("rx_eta"):
        L.append(f"- ⚡ 处方见效:{ts['rx_eta']}")
    return "\n".join(L)
