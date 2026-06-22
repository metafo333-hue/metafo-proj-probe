"""OS1 编排内核 · Scatter-Gather 多源扇出（probe 设计 orchestration-engine-solution-v1.0）。

落地范围（OS1·零成本单机·与 Wave1-3 同期）：
  ✅ Scatter-Gather 内核：单任务扇出到 N 个源，并发采集
  ✅ 元数据驱动扇出计划：source_id + callable 组装 SourceSpec
  ✅ 结构化并发 + per-source 超时预算（asyncio.wait_for·避免慢源拖垮整体）
  ✅ 单源失败隔离：一个源 timeout/error 不影响其它源（三态完成 + partial 标注）
  ✅ 并发上限（Semaphore·protect 第三方限流）

不含（后续 OS2-OS4）：反应式对冲、真值发现融合、Redis 分布式限流。
内核 callable 无关：适配器入口不统一（search/repo_info/summary…），由场景层绑定具体函数。
纯 stdlib·无外部依赖。
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class SourceSpec:
    """一个待扇出的数据源任务。

    source_id : 台账 id（仅作标识/日志，扇出不依赖它能解析）
    fn        : 同步可调用（适配器函数，如 wikipedia.search / github_src.repo_info）
    args/kwargs: 传给 fn 的参数
    timeout   : 本源超时预算（秒）·None 用扇出默认值
    domain    : 可选信息域代号（D1-D17·仅标注）
    """
    source_id: str
    fn: Callable[..., Any]
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    timeout: float | None = None
    domain: str = ""


@dataclass
class SourceResult:
    """单源采集结果（三态：ok / empty / timeout / error）。"""
    source_id: str
    status: str               # ok | empty | timeout | error
    data: Any = None
    elapsed_ms: int = 0
    error: str | None = None
    domain: str = ""

    @property
    def usable(self) -> bool:
        return self.status == "ok"


@dataclass
class FanOutResult:
    """扇出聚合结果（partial 显式标注·慢源不阻塞）。"""
    results: list[SourceResult]
    elapsed_ms: int

    @property
    def ok(self) -> list[SourceResult]:
        return [r for r in self.results if r.status == "ok"]

    @property
    def failed(self) -> list[SourceResult]:
        return [r for r in self.results if r.status in ("timeout", "error")]

    @property
    def partial(self) -> bool:
        """有任一源未成功 → partial（呈现层须如实标注「部分源缺失」）。"""
        return any(r.status != "ok" for r in self.results)

    def summary(self) -> dict[str, Any]:
        return {
            "total": len(self.results),
            "ok": len(self.ok),
            "empty": sum(1 for r in self.results if r.status == "empty"),
            "timeout": sum(1 for r in self.results if r.status == "timeout"),
            "error": sum(1 for r in self.results if r.status == "error"),
            "partial": self.partial,
            "elapsed_ms": self.elapsed_ms,
            "sources_ok": [r.source_id for r in self.ok],
            "sources_failed": [f"{r.source_id}:{r.status}" for r in self.failed],
        }


async def _run_one(spec: SourceSpec, default_timeout: float,
                   sem: asyncio.Semaphore) -> SourceResult:
    """单源执行 · 超时/异常全捕获 → 永不向上抛（保证隔离）。"""
    async with sem:
        start = time.monotonic()
        timeout = spec.timeout if spec.timeout is not None else default_timeout
        try:
            data = await asyncio.wait_for(
                asyncio.to_thread(spec.fn, *spec.args, **spec.kwargs), timeout)
            elapsed = int((time.monotonic() - start) * 1000)
            # 空结果（[]/{}/None/""）单列一态，便于呈现层区分「采到但无内容」
            empty = data is None or (hasattr(data, "__len__") and len(data) == 0)
            return SourceResult(spec.source_id, "empty" if empty else "ok",
                                data, elapsed, None, spec.domain)
        except asyncio.TimeoutError:
            elapsed = int((time.monotonic() - start) * 1000)
            return SourceResult(spec.source_id, "timeout", None, elapsed,
                                f"超时 >{timeout}s", spec.domain)
        except Exception as e:  # noqa: BLE001 · 隔离：任一源失败不波及其它源
            elapsed = int((time.monotonic() - start) * 1000)
            return SourceResult(spec.source_id, "error", None, elapsed,
                                f"{type(e).__name__}: {e}", spec.domain)


async def scatter_gather(specs: list[SourceSpec], *,
                         default_timeout: float = 8.0,
                         max_concurrency: int = 8) -> FanOutResult:
    """异步扇出：N 源并发采集，三态聚合，单源失败隔离。"""
    if not specs:
        return FanOutResult([], 0)
    start = time.monotonic()
    sem = asyncio.Semaphore(max_concurrency)
    results = await asyncio.gather(
        *[_run_one(s, default_timeout, sem) for s in specs])
    elapsed = int((time.monotonic() - start) * 1000)
    return FanOutResult(list(results), elapsed)


def fan_out(specs: list[SourceSpec], *,
            default_timeout: float = 8.0,
            max_concurrency: int = 8) -> FanOutResult:
    """同步入口（非 async 调用方用）·内部跑 asyncio event loop。"""
    return asyncio.run(scatter_gather(
        specs, default_timeout=default_timeout, max_concurrency=max_concurrency))
