"""OS1 编排内核回归测试（Scatter-Gather·离线确定性·无网络）。

覆盖设计判据：
- 并发扇出（总耗时 ≈ 最慢源，而非各源之和）
- 单源失败隔离（一源 error/timeout 不影响其它源）
- 三态完成（ok / empty / timeout / error）+ partial 显式标注
"""
from __future__ import annotations

import time

from app.datasources.orchestrator import SourceSpec, fan_out, scatter_gather
import asyncio


def _ok_source(q):
    return [{"title": f"result for {q}"}]


def _empty_source(q):
    return []


def _slow_source(q):
    time.sleep(2.0)        # 超过 timeout
    return [{"title": "too late"}]


def _boom_source(q):
    raise RuntimeError("源端炸了")


def test_fan_out_three_states_and_isolation():
    specs = [
        SourceSpec("ok1", _ok_source, ("北川魔芋",), domain="D1"),
        SourceSpec("empty1", _empty_source, ("x",), domain="D5"),
        SourceSpec("slow1", _slow_source, ("y",), timeout=0.3, domain="D12"),
        SourceSpec("boom1", _boom_source, ("z",), domain="D6"),
    ]
    out = fan_out(specs, default_timeout=5.0, max_concurrency=8)
    s = out.summary()

    assert s["total"] == 4
    assert s["ok"] == 1            # ok1
    assert s["empty"] == 1         # empty1
    assert s["timeout"] == 1       # slow1（被 0.3s 超时切断）
    assert s["error"] == 1         # boom1（隔离·不波及其它）
    assert s["partial"] is True
    assert "ok1" in s["sources_ok"]
    assert any("boom1:error" == x for x in s["sources_failed"])

    # 隔离证明：ok1 的数据完好返回，未被 boom1/slow1 影响
    ok = [r for r in out.results if r.source_id == "ok1"][0]
    assert ok.usable and ok.data == [{"title": "result for 北川魔芋"}]


def test_fan_out_is_concurrent_not_serial():
    """3 个各 sleep 0.4s 的源并发跑，总耗时应 ≈0.4s 而非 1.2s。"""
    def _sleeper(q):
        time.sleep(0.4)
        return [{"q": q}]

    specs = [SourceSpec(f"s{i}", _sleeper, (i,)) for i in range(3)]
    start = time.monotonic()
    out = fan_out(specs, default_timeout=5.0, max_concurrency=8)
    wall = time.monotonic() - start

    assert out.summary()["ok"] == 3
    assert wall < 0.9, f"并发应 ≈0.4s，实际 {wall:.2f}s（疑似串行）"


def test_empty_specs():
    out = fan_out([])
    assert out.summary()["total"] == 0
    assert out.partial is False


def test_concurrency_cap_respected():
    """max_concurrency=1 时退化为串行，总耗时 ≈ 各源之和。"""
    def _sleeper(q):
        time.sleep(0.2)
        return [1]
    specs = [SourceSpec(f"s{i}", _sleeper, (i,)) for i in range(3)]
    start = time.monotonic()
    fan_out(specs, default_timeout=5.0, max_concurrency=1)
    wall = time.monotonic() - start
    assert wall >= 0.55, f"并发=1 应串行 ≈0.6s，实际 {wall:.2f}s"
