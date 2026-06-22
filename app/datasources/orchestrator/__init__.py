"""OS1 编排内核 · 单任务多源 Scatter-Gather 扇出。

用法：
    from app.datasources.orchestrator import SourceSpec, fan_out
    from app.datasources.public import wikipedia, github_src

    specs = [
        SourceSpec("wikipedia", wikipedia.search, ("北川魔芋",), domain="D1"),
        SourceSpec("github", github_src.search, ("konjac",), domain="D12"),
    ]
    out = fan_out(specs, default_timeout=8.0)
    print(out.summary())      # {ok, partial, sources_ok, sources_failed, ...}
    for r in out.ok:
        print(r.source_id, r.data)
"""
from app.datasources.orchestrator.core import (
    SourceSpec,
    SourceResult,
    FanOutResult,
    scatter_gather,
    fan_out,
)
from app.datasources.orchestrator.fusion import (
    Claim,
    FusedClaim,
    fuse_claims,
    fuse_fanout,
    to_audit_claims,
    reliability_weight,
)

__all__ = [
    "SourceSpec",
    "SourceResult",
    "FanOutResult",
    "scatter_gather",
    "fan_out",
    # OS3 多源融合
    "Claim",
    "FusedClaim",
    "fuse_claims",
    "fuse_fanout",
    "to_audit_claims",
    "reliability_weight",
]
