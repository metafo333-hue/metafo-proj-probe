"""L1 §1 异步 task · task_id → 轮询 status/result（02-api 长任务铁律）。

MVP：进程内 task store（dict）+ FastAPI BackgroundTasks。
生产：切 Redis + RQ（R14：多 worker 禁内存共享态 → 用 Redis）。
失败不扣：task=failed → cost=None（母体 §3 失败不扣费）。
"""
from __future__ import annotations

import secrets
from typing import Any, Callable

# MVP 进程内存储（单 worker 限定·systemd --workers 1；生产换 Redis）
_TASKS: dict[str, dict[str, Any]] = {}


def new_task() -> str:
    # 不可猜 token（闭 IDOR：task 轮询对匿名公开·task_id 不可枚举防越权读他人结果）
    tid = "t_" + secrets.token_urlsafe(24)
    _TASKS[tid] = {
        "status": "pending", "progress": 0,
        "deliverable": None, "meta": None, "cost": None, "error": None,
    }
    return tid


def get_task(tid: str) -> dict[str, Any] | None:
    return _TASKS.get(tid)


def run_task(tid: str, fn: Callable[[str], dict[str, Any]]) -> None:
    """执行任务体 fn(tid)→{deliverable,meta,cost}；异常→failed（不扣费）。"""
    t = _TASKS.get(tid)
    if t is None:
        return
    t["status"], t["progress"] = "running", 10
    try:
        result = fn(tid)
        t.update(status="done", progress=100,
                 deliverable=result.get("deliverable"),
                 meta=result.get("meta"), cost=result.get("cost"), error=None)
    except Exception as e:  # noqa: BLE001 — 任何失败都不扣费
        t.update(status="failed", progress=100,
                 deliverable=None, meta=None, cost=None, error=str(e))
