"""GET /api/v1/task/{id} · 异步任务轮询（02-api §1 status_url）。"""
from __future__ import annotations

from fastapi import APIRouter

from app.core import tasks

router = APIRouter(prefix="/api/v1", tags=["task"])


@router.get("/task/{task_id}")
def get_task(task_id: str) -> dict:
    t = tasks.get_task(task_id)
    if t is None:
        return {"code": 4004, "data": None, "msg": "task 不存在或已过期"}
    # status: pending|running|done|failed · progress 0-100 · deliverable/meta/cost/error
    return {"code": 0, "data": t, "msg": "ok"}
