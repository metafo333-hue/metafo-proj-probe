"""probe · 链接情报 · metafoclaw 母体「首个远程镶嵌工具」（L1 契约 HTTP 实现）。

母体是铁轨、probe 是列车：内部 L0 零改动，对外只实现 02-api.md 的 4 暗号 + task 轮询。
端点：/api/v1/{invoke,manifest,selftest,task/{id},health}
"""
from __future__ import annotations

from fastapi import FastAPI

from app import config
from app.routers import (invoke, manifest, selftest, task, selfmedia, account,
                         rotation, cost, scenario)

app = FastAPI(title="probe · 链接情报", version=config.CONTRACT_VERSION)

app.include_router(invoke.router)
app.include_router(manifest.router)
app.include_router(selftest.router)
app.include_router(task.router)
app.include_router(selfmedia.router)  # 自媒体采集面(方案B 独立验证面·断层1接线)
app.include_router(account.router)    # 账号综合分析(对内用·无 SSO/计费)
app.include_router(rotation.router)   # 轮动看板(日/周/月快照追踪·共用数据)
app.include_router(cost.router)       # 付费数据源用量/省费聚合(喂 ops 用量看板·只读对内)
app.include_router(scenario.router)   # B/C/D/E 四赛道多源情报场景(OS1扇出+八闸·对内演示)


@app.get("/api/v1/health")
def health() -> dict:
    from app.audit.backends import backend_status
    return {"code": 0,
            "data": {"service": "probe", "subdomain": config.SUBDOMAIN,
                     "contract_version": config.CONTRACT_VERSION,
                     "audit_backend": backend_status()},  # 八闸 live/stub 可观测
            "msg": "ok"}
