"""metering · 成本埋点（S1 施工件）。

记录每次 LLM 调用的 token 消耗和估算成本，写入本地 JSONL 日志。
调用方：
    from app.services.metering import record, summarize

LiteLLM proxy (cc-sonnet) 定价参考：cc-sonnet ≈ $3/MTok in · $15/MTok out
（实际单位：分 · ¥，换算按 7.2 汇率）
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

# 成本日志路径（probe-a 生产时改为 /var/log/probe/metering.jsonl）
_LOG_PATH = Path(os.getenv("PROBE_METERING_LOG", "/tmp/probe_metering.jsonl"))

# 每千 token 成本（美分 · cc-sonnet · 2026-06 参考价）
_PRICE_PER_1K: dict[str, dict[str, float]] = {
    "cc-sonnet":  {"in": 0.3,  "out": 1.5},
    "cc-haiku":   {"in": 0.025, "out": 0.125},
    "cc-opus":    {"in": 1.5,  "out": 7.5},
    "deepseek-chat": {"in": 0.014, "out": 0.028},
    "qwen-plus":  {"in": 0.04,  "out": 0.12},
    "_default":   {"in": 0.3,   "out": 1.5},
}


def _cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """估算单次调用成本（美元）。"""
    price = _PRICE_PER_1K.get(model, _PRICE_PER_1K["_default"])
    return (prompt_tokens / 1000 * price["in"] +
            completion_tokens / 1000 * price["out"]) / 100  # 分 → 美元


def record(
    task_id:           str,
    operation:         str,
    usage:             dict[str, Any],
    extra:             dict[str, Any] | None = None,
) -> dict[str, Any]:
    """写入一条成本事件到 JSONL 日志。

    Parameters
    ----------
    task_id   : probe 任务 ID
    operation : 操作名（如 "faithfulness", "fact_check", "structure_analyze"）
    usage     : llm._chat_with_usage() 返回的 usage dict
    extra     : 可选附加字段（如 gate_id, tier）
    """
    if not usage:
        return {}

    model     = usage.get("model", "_default")
    pt        = usage.get("prompt_tokens", 0)
    ct        = usage.get("completion_tokens", 0)
    cost_usd  = _cost_usd(model, pt, ct)
    cost_cny  = round(cost_usd * 7.2, 6)

    event: dict[str, Any] = {
        "ts":         time.time(),
        "task_id":    task_id,
        "operation":  operation,
        "provider":   usage.get("provider", "unknown"),
        "model":      model,
        "prompt_tokens":     pt,
        "completion_tokens": ct,
        "total_tokens":      pt + ct,
        "cost_usd":   round(cost_usd, 6),
        "cost_cny":   cost_cny,
    }
    if extra:
        event.update(extra)

    try:
        _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        pass  # 写日志失败不影响主流程

    return event


def summarize(task_id: str | None = None) -> dict[str, Any]:
    """从日志汇总指定 task 或全局的 token/cost 统计。"""
    if not _LOG_PATH.exists():
        return {"total_events": 0, "total_tokens": 0, "total_cost_usd": 0.0}

    events: list[dict] = []
    try:
        with _LOG_PATH.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    e = json.loads(line)
                    if task_id is None or e.get("task_id") == task_id:
                        events.append(e)
    except Exception:
        pass

    total_tokens = sum(e.get("total_tokens", 0) for e in events)
    total_cost   = sum(e.get("cost_usd", 0.0) for e in events)
    total_cny    = sum(e.get("cost_cny", 0.0) for e in events)

    return {
        "total_events":   len(events),
        "total_tokens":   total_tokens,
        "total_cost_usd": round(total_cost, 6),
        "total_cost_cny": round(total_cny, 4),
        "breakdown":      {
            op: {"events": sum(1 for e in events if e["operation"] == op),
                 "tokens": sum(e.get("total_tokens", 0) for e in events if e["operation"] == op)}
            for op in {e["operation"] for e in events}
        },
    }
