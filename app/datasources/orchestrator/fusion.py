"""OS3 多源融合 · 真值发现（probe 设计 orchestration-engine-solution-v1.0 §OS3）。

落地范围（OS3·零成本·喂八闸前的多源冲突消解）：
  ✅ 真值发现而非简单多数票：源按可信度加权投票，最高加权支持的值胜出
  ✅ 实体/字段对齐去重：同 key 的多源值聚到一起比对
  ✅ 冲突检测：同 key 出现 ≥2 个不同值 → conflict=True（喂八闸 NLI/对抗证伪）
  ✅ 佐证度：支持胜出值的独立源数量（corroboration）
  ✅ 置信度：胜出值加权支持 / 总加权支持

不含（OS3 完整体）：时效衰减权重、冷启动先验喂值（后续）。
纯 stdlib·无外部依赖。设计「喂 8 闸」：fuse 输出可直接转 claims/sources 交 run_audit。
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

from app.datasources.orchestrator.core import FanOutResult, SourceResult


# 源可信度字母 → 加权（喂真值发现的投票权重·A 官方权威 > C 二手聚合）
_RELIABILITY_WEIGHT = {"A": 1.0, "B": 0.7, "C": 0.4, "D": 0.2}
_DEFAULT_WEIGHT = 0.5


@dataclass
class Claim:
    """单源对某 key 的一条主张。"""
    key: str
    value: Any
    source_id: str
    weight: float = _DEFAULT_WEIGHT


@dataclass
class FusedClaim:
    """融合后对某 key 的真值判定。"""
    key: str
    value: Any                       # 加权胜出值
    confidence: float                # 胜出值加权支持 / 总加权支持 [0,1]
    corroboration: int               # 支持胜出值的独立源数
    conflict: bool                   # 是否多源给出不同值
    sources: list[str] = field(default_factory=list)         # 支持胜出值的源
    alternatives: list[dict] = field(default_factory=list)   # 落败值 [{value, support, sources}]


def reliability_weight(letter: str | None) -> float:
    return _RELIABILITY_WEIGHT.get((letter or "").upper(), _DEFAULT_WEIGHT)


def fuse_claims(claims: Iterable[Claim]) -> list[FusedClaim]:
    """真值发现：按 key 分组 → 同值加权聚合 → 加权胜出 + 冲突/佐证标注。"""
    by_key: dict[str, list[Claim]] = defaultdict(list)
    for c in claims:
        by_key[c.key].append(c)

    fused: list[FusedClaim] = []
    for key, cs in by_key.items():
        # 按 value（转 str 作可哈希键）聚合加权支持 + 源
        support: dict[str, float] = defaultdict(float)
        srcs: dict[str, list[str]] = defaultdict(list)
        repr_val: dict[str, Any] = {}
        for c in cs:
            vk = str(c.value)
            support[vk] += c.weight
            srcs[vk].append(c.source_id)
            repr_val.setdefault(vk, c.value)

        total = sum(support.values()) or 1.0
        ranked = sorted(support.items(), key=lambda kv: kv[1], reverse=True)
        win_vk, win_support = ranked[0]
        fused.append(FusedClaim(
            key=key,
            value=repr_val[win_vk],
            confidence=round(win_support / total, 3),
            corroboration=len(set(srcs[win_vk])),
            conflict=len(ranked) > 1,
            sources=sorted(set(srcs[win_vk])),
            alternatives=[
                {"value": repr_val[vk], "support": round(sup, 3),
                 "sources": sorted(set(srcs[vk]))}
                for vk, sup in ranked[1:]
            ],
        ))
    return fused


# 默认抽取器：把 source.data（dict 或 list[dict]）的标量字段铺成 (key, value) 主张
def default_extractor(r: SourceResult) -> list[tuple[str, Any]]:
    out: list[tuple[str, Any]] = []
    items = r.data if isinstance(r.data, list) else [r.data]
    for it in items:
        if isinstance(it, dict):
            for k, v in it.items():
                if isinstance(v, (str, int, float, bool)) and v != "":
                    out.append((k, v))
    return out


def fuse_fanout(out: FanOutResult, *,
                reliability: dict[str, str] | None = None,
                extractor: Callable[[SourceResult], list[tuple[str, Any]]] = default_extractor
                ) -> list[FusedClaim]:
    """FanOutResult → 融合真值。reliability: {source_id: 'A'/'B'/'C'} 决定投票权重。"""
    reliability = reliability or {}
    claims: list[Claim] = []
    for r in out.ok:
        w = reliability_weight(reliability.get(r.source_id))
        for k, v in extractor(r):
            claims.append(Claim(k, v, r.source_id, w))
    return fuse_claims(claims)


def to_audit_claims(fused: list[FusedClaim]) -> tuple[list[str], list[str]]:
    """融合结果 → (高置信 claims, 冲突 flags)·供 run_audit 与呈现层。"""
    claims = [f"{f.key} = {f.value}（{f.corroboration} 源佐证·置信 {f.confidence}）"
              for f in fused if not f.conflict and f.corroboration >= 1]
    conflicts = [f"⚠️ {f.key} 多源冲突：{f.value} vs " +
                 ", ".join(str(a['value']) for a in f.alternatives)
                 for f in fused if f.conflict]
    return claims, conflicts
