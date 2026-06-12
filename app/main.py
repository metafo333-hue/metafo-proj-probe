"""probe · 链接情报 · metafoclaw 母体「首个远程镶嵌工具」（L1 契约 HTTP 实现）。

母体是铁轨、probe 是列车：内部 L0 零改动，对外只实现 02-api.md 的 4 暗号 + task 轮询。
端点：/api/v1/{invoke,manifest,selftest,task/{id},health}
"""
from __future__ import annotations

from fastapi import FastAPI

from app import config
from app.routers import invoke, manifest, selftest, task

app = FastAPI(title="probe · 链接情报", version=config.CONTRACT_VERSION)

app.include_router(invoke.router)
app.include_router(manifest.router)
app.include_router(selftest.router)
app.include_router(task.router)


@app.get("/api/v1/health")
def health() -> dict:
    return {"code": 0,
            "data": {"service": "probe", "subdomain": config.SUBDOMAIN,
                     "contract_version": config.CONTRACT_VERSION},
            "msg": "ok"}
