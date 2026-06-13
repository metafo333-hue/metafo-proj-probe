"""metering · 成本埋点（S1 施工件 · 断层#5）。

记录每次 LLM/数据源调用的 token 消耗和估算成本。
落库策略（守 R28：业务数据入 PG）：
    PG 主写（probe_cost_events）→ 失败/未配置时回落 JSONL（不阻塞主流程）。
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

# 成本日志路径（PG 不可达时的回落兜底）
_LOG_PATH = Path(os.getenv("PROBE_METERING_LOG", "/tmp/probe_metering.jsonl"))

# PG DSN（probe-a 本机 probe_collect · vault 注入 · 未配置则纯 JSONL）
_PG_DSN = os.getenv("PROBE_PG_DSN", "")


def _pg_insert(event: dict[str, Any]) -> bool:
    """写一条 cost_event 到 probe_cost_events。成功 True，任何失败 False（调用方回落 JSONL）。"""
    if not _PG_DSN:
        return False
    try:
        import psycopg  # 延迟导入：未装/未配置不影响 JSONL 路径
    except ImportError:
        return False
    try:
        with psycopg.connect(_PG_DSN, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO probe_cost_events
                      (call_id, task_id, user_id, surface, source_id, kind,
                       units, unit_cost, cost_real, cost_cny, billed, status,
                       cache_hit, retry_seq, fallback_of, url_hash, latency_ms)
                    VALUES
                      (%(call_id)s, %(task_id)s, %(user_id)s, %(surface)s, %(source_id)s, %(kind)s,
                       %(units)s, %(unit_cost)s, %(cost_real)s, %(cost_cny)s, %(billed)s, %(status)s,
                       %(cache_hit)s, %(retry_seq)s, %(fallback_of)s, %(url_hash)s, %(latency_ms)s)
                    """,
                    {
                        "call_id":     event.get("call_id", event.get("task_id", "") + ":" + event.get("operation", "")),
                        "task_id":     event.get("task_id"),
                        "user_id":     event.get("user_id"),
                        "surface":     event.get("surface", "llm"),
                        "source_id":   event.get("provider", event.get("source_id")),
                        "kind":        event.get("operation", event.get("kind")),
                        "units":       json.dumps({"prompt_tokens": event.get("prompt_tokens", 0),
                                                   "completion_tokens": event.get("completion_tokens", 0)}),
                        "unit_cost":   event.get("unit_cost", 0),
                        "cost_real":   event.get("cost_usd", 0),
                        "cost_cny":    event.get("cost_cny", 0),
                        "billed":      event.get("billed", 0),
                        "status":      event.get("status", "success"),
                        "cache_hit":   event.get("cache_hit", False),
                        "retry_seq":   event.get("retry_seq", 0),
                        "fallback_of": event.get("fallback_of"),
                        "url_hash":    event.get("url_hash"),
                        "latency_ms":  event.get("latency_ms"),
                    },
                )
            conn.commit()
        return True
    except Exception:
        return False  # PG 任何异常 → 回落 JSONL，不抛、不阻塞主流程

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

    # 落库：PG 主写（R28）→ 失败回落 JSONL（不阻塞主流程）
    if not _pg_insert(event):
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
