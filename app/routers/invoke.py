"""POST /api/v1/invoke · ① 入口/出口契约（异步默认 · 02-api §1）。

长任务铁律：默认 mode=async → 立即返 {task_id, status_url}，轮询 /api/v1/task/{id}。
失败不扣：task 体异常 → task=failed、cost=None（计费由母体在 task done 后按 cost 扣）。
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Body

from app.core import budget, sso, tasks
from app.l0 import find_url
from app.services import pipeline

router = APIRouter(prefix="/api/v1", tags=["invoke"])


@router.post("/invoke")
def invoke(bg: BackgroundTasks, payload: dict[str, Any] = Body(...)) -> dict:
    # 兼容 {"request": {...}} 与裸 {...}
    req = payload.get("request") if isinstance(payload.get("request"), dict) else payload

    # probe 以链接为核心：同步快速校验有无 URL，无则 4001（不浪费 task）
    if not find_url(req.get("instruction"), req.get("context"), req.get("attachments")):
        return {"code": 4001, "data": None, "msg": "未提供链接 URL"}

    # SSO：校验母体 short-lived user_token（匿名→免费档）
    principal = sso.verify(req.get("user_token"), req.get("billing_context"))

    # M1 匿名防刷：全局每日额度兜底（nginx per-IP 限流挡散户·此挡分布式总量）
    if principal.is_anonymous() and not budget.allow_anon():
        return {"code": 4290, "data": None,
                "msg": "今日免费核查额度已满，请登录或明日再试"}

    # 起异步 task
    tid = tasks.new_task()
    bg.add_task(tasks.run_task, tid,
                lambda task_id: pipeline.process(req, principal, task_id))
    return {"code": 0,
            "data": {"task_id": tid, "status_url": f"/api/v1/task/{tid}"},
            "msg": "accepted"}
