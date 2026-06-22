"""GET /api/v1/cost/datasource · 付费数据源用量/省费聚合（喂 ops 用量看板）。

只读·对内用。数据来自 metering（probe_cost_daily 视图优先 / JSONL 回落），
含每源调用数、缓存命中率、省费估算、成本闸拦截数。ops-brain 经 HTTP 拉取
（与取 LiteLLM 同模式·解耦·不反向连 probe-a 内网库）。
"""
from __future__ import annotations

from fastapi import APIRouter

from app.services import metering

router = APIRouter(prefix="/api/v1/cost", tags=["cost"])


@router.get("/datasource")
def datasource_cost(day: str | None = None) -> dict:
    """付费数据源成本聚合。day='YYYY-MM-DD' 过滤当日；省略=全部。"""
    data = metering.summarize_datasource(day)
    return {"code": 0, "data": data, "msg": "ok"}
