"""GET/POST /api/v1/scenario · B/C/D/E 四赛道多源情报场景（对内用·无 SSO/计费）。

复用 OS1 编排 + 八闸审核：单 query → 多源并发扇出 → 可信度三标签情报包。
对内调试/演示面，与 /invoke（对外异步契约）分开，不走计费。

  GET  /api/v1/scenario              → 列出可用场景
  POST /api/v1/scenario/{key}        → 跑场景（key ∈ B1/C5/D2/E3）
       body: {"query": "公司名/repo/主题", "audit": true, "tier": "paid"}
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body

from app.services import scenarios

router = APIRouter(prefix="/api/v1", tags=["scenario"])

_DESC = {
    "B1": "企业全景（工商+SEC披露+百科）",
    "C5": "制裁合规扫描（OFAC+工商·实体筛查）",
    "D2": "技术情报（GitHub健康+OSV漏洞）",
    "E3": "信息源可信度（百科+新闻+学术交叉）",
}


@router.get("/scenario")
def list_scenarios() -> dict:
    return {"code": 0, "msg": "ok",
            "data": {"scenarios": [{"key": k, "desc": _DESC.get(k, "")}
                                   for k in scenarios.REGISTRY]}}


@router.post("/scenario/{key}")
def run_scenario(key: str, payload: dict[str, Any] = Body(...)) -> dict:
    fn = scenarios.REGISTRY.get(key.upper())
    if fn is None:
        return {"code": 4040, "data": None,
                "msg": f"未知场景 {key}·可用: {list(scenarios.REGISTRY)}"}
    query = (payload or {}).get("query", "").strip()
    if not query:
        return {"code": 4001, "data": None, "msg": "缺 query（公司名/repo/主题）"}

    kwargs: dict[str, Any] = {}
    if "audit" in (payload or {}):
        kwargs["audit"] = bool(payload["audit"])   # 透传给场景（默认过八闸出可信度标签）
    try:
        packet = fn(query, **kwargs)
    except Exception as e:  # noqa: BLE001
        return {"code": 5000, "data": None, "msg": f"场景执行异常: {type(e).__name__}: {e}"}
    return {"code": 0, "msg": "ok", "data": packet}
