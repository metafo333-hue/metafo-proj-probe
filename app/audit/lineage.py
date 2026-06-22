"""数据血缘验证 · 自媒体量化结果的「敢担保」机制(断层2 · 方案B 独立验证面)。

为什么不走 8 闸(gates.py):
  8 闸是「文本声明 + 来源」的验证(溯源/多源交叉/抗污染/NLI/CRAAP/对抗证伪),对象是 claims。
  自媒体采集出的是「计算指标」(播放量/coverage/完播率),要验的是**数据血缘**——
  每个数字取自哪个源、什么精度、什么时点、缺没缺,而非来源三角。
  本模块是「量化数据的审核闸」,与 gates.py 平行:不替代、不改它。
  产出的 lineage_grade 可被上层「处方依据强度」引用(对外信任表达)。
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

# precision → 可信权重(对齐 combo_deep_probe.schema.Precision)
PRECISION_WEIGHT = {"measured": 1.0, "estimated": 0.6, "fed": 0.4, "missing": 0.0}
FRESH_WARN_DAYS = 30  # 字段数据时点超过此天数 → 标「需重验」


def _parse_ts(ts: str) -> datetime | None:
    if not ts:
        return None
    raw = ts.strip()
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw[:19], fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def verify(collected: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    """对 collect_video / collect_account 的输出做数据血缘验证。

    入参:collected —— 含 dimensions{维度:{字段:{value,source,precision,ts}}} +
                       coverage_score / coverage + missing_blackbox。
    返回:数据血缘报告(grade 高/中/低 + 精度分布 + 过期字段 + 人读 flags)。
    """
    now = now or datetime.now(timezone.utc)
    dims = collected.get("dimensions") or {}
    mix = {"measured": 0, "estimated": 0, "fed": 0, "missing": 0}
    weighted, total = 0.0, 0
    stale: list[dict[str, Any]] = []

    for dim, fields in dims.items():
        if not isinstance(fields, dict):
            continue
        for fname, f in fields.items():
            if not isinstance(f, dict):
                continue
            p = str(f.get("precision") or "missing").lower()
            mix[p] = mix.get(p, 0) + 1
            weighted += PRECISION_WEIGHT.get(p, 0.0)
            total += 1
            dt = _parse_ts(str(f.get("ts") or ""))
            if dt is not None:
                age = (now - dt).days
                if age > FRESH_WARN_DAYS:
                    stale.append({"dim": dim, "field": fname, "age_days": age})

    lineage_score = round(weighted / total, 3) if total else 0.0
    coverage = float(collected.get("coverage_score") or collected.get("coverage") or 0.0)
    missing_bb = list(collected.get("missing_blackbox") or [])
    grade = _grade(lineage_score, coverage, len(stale))

    return {
        "lineage_grade": grade,              # 高/中/低 —— 量化结果的担保等级
        "lineage_score": lineage_score,      # 0-1 精度加权
        "coverage": coverage,                # 透传:数据多全
        "precision_mix": mix,                # 各精度字段计数
        "field_total": total,
        "missing_blackbox": missing_bb,      # 缺失黑盒维度(完播/流量来源/转化)
        "stale_fields": stale,               # 超 FRESH_WARN_DAYS 的字段
        "flags": _flags(mix, missing_bb, stale),
        "note": "数据血缘验证(量化·非文本八闸)·grade 供处方依据强度引用",
    }


def _grade(lineage_score: float, coverage: float, n_stale: int) -> str:
    if lineage_score >= 0.8 and coverage >= 0.7 and n_stale == 0:
        return "高"
    if lineage_score >= 0.5 and coverage >= 0.4:
        return "中"
    return "低"


def _flags(mix: dict[str, int], missing_bb: list, stale: list) -> list[str]:
    out: list[str] = []
    if mix.get("fed"):
        out.append(f"{mix['fed']}个字段为投喂值(半可信·防伪需交叉校验)")
    if mix.get("estimated"):
        out.append(f"{mix['estimated']}个字段为第三方估算(非实测)")
    if missing_bb:
        out.append(f"黑盒维度缺失:{','.join(missing_bb)}(完播/流量来源/转化需投喂补)")
    if stale:
        out.append(f"{len(stale)}个字段数据已过{FRESH_WARN_DAYS}天·需重验")
    if not out:
        out.append("全字段实测且新鲜·血缘干净")
    return out
