"""POST /api/v1/invoke · ① 入口/出口契约（异步默认 · 02-api §1）。

长任务铁律：默认 mode=async → 立即返 {task_id, status_url}，轮询 /api/v1/task/{id}。
失败不扣：task 体异常 → task=failed、cost=None（计费由母体在 task done 后按 cost 扣）。
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Body

from app.core import sso, tasks
from app.l0 import find_url
from app.schemas.brief import ProbeBrief
from app.services import pipeline
from app.services import route as route_svc

router = APIRouter(prefix="/api/v1", tags=["invoke"])


@router.post("/invoke")
def invoke(bg: BackgroundTasks, payload: dict[str, Any] = Body(...)) -> dict:
    # 兼容 {"request": {...}} 与裸 {...}
    req = payload.get("request") if isinstance(payload.get("request"), dict) else payload

    # SSO：校验母体 short-lived user_token（匿名→免费档）
    principal = sso.verify(req.get("user_token"), req.get("billing_context"))

    # ── ask-first 脊柱：收到结构化 ProbeBrief（contract_version=probe-brief/v1）──
    if ProbeBrief.is_brief_request(req):
        brief = ProbeBrief.from_request(req)
        brief.tier = getattr(principal, "tier", "free")  # tier 由 probe 从 SSO 填·不信 ask
        # 解 URL 硬门：brief 有意图就不强制 URL（C 选题/B 找借鉴等无 URL 路径放行）
        has_url = bool(
            find_url(brief.instruction, brief.context, brief.attachments)
            or (brief.subject and brief.subject.resolved_url)
        )
        if not has_url and brief.intent.value not in ("ideate", "compare", "amplify"):
            return {"code": 4001, "data": None, "msg": "未提供链接 URL 或可路由意图"}
        route_decision = route_svc.decide(brief, principal)
        tid = tasks.new_task()
        bg.add_task(tasks.run_task, tid,
                    lambda task_id: pipeline.process_brief(brief, route_decision, principal, task_id))
        return {"code": 0,
                "data": {"task_id": tid, "status_url": f"/api/v1/task/{tid}"},
                "msg": "accepted"}

    # ── 向后兼容：旧裸 dict 路径（probe 以链接为核心·完全不动）──
    if not find_url(req.get("instruction"), req.get("context"), req.get("attachments")):
        return {"code": 4001, "data": None, "msg": "未提供链接 URL"}
    tid = tasks.new_task()
    bg.add_task(tasks.run_task, tid,
                lambda task_id: pipeline.process(req, principal, task_id))
    return {"code": 0,
            "data": {"task_id": tid, "status_url": f"/api/v1/task/{tid}"},
            "msg": "accepted"}
