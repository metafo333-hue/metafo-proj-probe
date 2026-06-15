"""全局每日调用熔断 · M1 匿名防刷成本护栏（断层#5 配套·Phase3-6）。

per-IP 限流(nginx)挡散户·本模块挡全局总量(分布式刷的兜底天花板)。
MVP：进程内每日计数器（systemd --workers 1 单进程·与 tasks store 同假设）。
生产：切 Redis 全局计数（多 worker/多实例时·R14）。

匿名(free)请求计入每日额度；登录付费用户不受此限（付费有计费账约束）。
"""
from __future__ import annotations

import datetime
import os

# 匿名每日全局调用上限（兜底成本天花板·worst≈cap×单次LLM成本）
_ANON_DAILY_CAP = int(os.getenv("PROBE_ANON_DAILY_CAP", "1000"))

_state = {"day": "", "anon_count": 0}


def _today() -> str:
    return datetime.date.today().isoformat()


def allow_anon() -> bool:
    """匿名请求是否放行（未超每日全局额度）。放行则计数 +1。"""
    today = _today()
    if _state["day"] != today:
        _state["day"] = today
        _state["anon_count"] = 0
    if _state["anon_count"] >= _ANON_DAILY_CAP:
        return False
    _state["anon_count"] += 1
    return True


def stats() -> dict:
    return {"day": _state["day"], "anon_count": _state["anon_count"], "cap": _ANON_DAILY_CAP}
