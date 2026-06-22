"""付费数据源调用缓存 + 计费埋点统一收口（省重复付费 · 守数据等价）。

挂载点 = 各 adapter 的 HTTP 底层方法（JZL `_post_json`/`_post_form`/read_zan、
TikHub SDK 调用）。在最底层收口，覆盖 l0 取数链 + services 业务链所有付费调用，
且天然端点级（按端点不变性分 TTL）。adapter 业务方法、registry、l0 零改动。

数据等价三道保险（见 docs/3-build/probe-cost-optimization-design-v1.0.md §九）：
1. 端点级 TTL：内容不变型（article_detail/principal_info）长 TTL，时变型（read_zan/
   history）短 TTL，实时型（get_remain_money）TTL=0 不缓存。
2. 默认不缓存：未登记端点 TTL=0，绝不意外缓存影响结果。
3. force_refresh 旁路 + 只缓存成功：fetch_fn 抛异常不缓存、不计费。

进程级缓存（probe-a 常驻服务有效）；跨进程持久化（probe_source_cache 表）留 P1。
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import time
from typing import Any, Callable

# 总开关：PROBE_SOURCE_CACHE=0 全关（回归裸调，用于对照/排障）
_ENABLED = os.getenv("PROBE_SOURCE_CACHE", "1") != "0"

# ── 成本闸（日预算 · 防跑飞）──────────────────────────────────────────────
# PROBE_COST_GATE=0 关闸；PROBE_DAILY_BUDGET_CNY 设日预算上限（¥，默认 10）。
_COST_GATE = os.getenv("PROBE_COST_GATE", "1") != "0"
_DAILY_BUDGET = float(os.getenv("PROBE_DAILY_BUDGET_CNY", "10"))
# 进程内当日累计真实花费（date → ¥）。跨进程精确累计由 probe_cost_daily 聚合兜（P1）。
_spend: dict[str, float] = {}


class BudgetExceeded(RuntimeError):
    """当日付费调用累计将超日预算 → fail-loud 拦截（不返回脏数据）。"""


def _today() -> str:
    return time.strftime("%Y-%m-%d")


def spent_today() -> float:
    """本进程当日已累计真实花费（¥·观测/测试用）。"""
    return _spend.get(_today(), 0.0)


def reset_spend() -> None:
    """清零花费累加器（测试用）。"""
    _spend.clear()

# 端点 → TTL 秒。**未登记端点默认 0（不缓存）**——只对明确安全的端点缓存。
# 可经 env PROBE_TTL_<大写端点名> 覆盖（部署期按新鲜度需求调，不改代码）。
_TTL: dict[str, int] = {
    # 内容不变型 → 30 天（上限防陈旧，文章/主体发布后不变）
    "/article_detail":    2592000,
    "/principal_info":    2592000,
    # 准不变型 → 7 天（账号 fans/avg_read 周级更新）
    "/wx_account/search":  604800,
    # 时变型 → 1 小时（阅读量/评论/历史列表持续增长）
    "/read_zan":             3600,
    "/article_comment2":     3600,
    "/history_by_ghid":      3600,
    # 视频列表 → 6 小时（新视频持续发布）
    "/wxvideo":             21600,
    # TikHub（端点用逻辑名）
    "tikhub:video_data":     3600,
    "tikhub:note_info":      3600,
    "tikhub:douyin_stat":    3600,
    # 实时型 → 不缓存
    "/get_remain_money":         0,
    "/Keyverifycode":            0,
}

_CACHE: dict[str, tuple[Any, float]] = {}


def ttl_for(endpoint: str) -> int:
    """端点 TTL（env 覆盖 > 内置表 > 默认 0 不缓存）。"""
    env_key = "PROBE_TTL_" + endpoint.strip("/").replace("/", "_").replace(":", "_").upper()
    env_val = os.getenv(env_key)
    if env_val is not None:
        try:
            return int(env_val)
        except ValueError:
            pass
    return _TTL.get(endpoint, 0)


def _key(source_id: str, endpoint: str, params: Any) -> str:
    """缓存键 = source|endpoint|规范化参数。参数禁含凭据（调用方传 extra·不含 key）。"""
    try:
        pj = json.dumps(params, sort_keys=True, ensure_ascii=False, default=str)
    except Exception:  # noqa: BLE001
        pj = str(params)
    return f"{source_id}|{endpoint}|{hashlib.sha256(pj.encode('utf-8')).hexdigest()[:20]}"


def _url_hash(params: Any) -> str:
    return hashlib.sha256(json.dumps(params, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]


def cached_call(
    source_id: str,
    endpoint: str,
    params: dict | str,
    fetch_fn: Callable[[], Any],
    *,
    cost_cny: float = 0.0,
    task_id: str = "",
    force_refresh: bool = False,
) -> Any:
    """付费调用统一收口：缓存命中省钱，未命中真调并记账。

    Parameters
    ----------
    source_id : 数据源 id（jzl_wechat_channels / tikhub）
    endpoint  : 端点路径（决定 TTL · 如 "/article_detail"、"tikhub:video_data"）
    params    : 调用参数（**禁含凭据**，仅业务参数，用于缓存键）
    fetch_fn  : 真实调用闭包，返回值即缓存内容；抛异常 → 不缓存不计费并重抛
    cost_cny  : 该端点真实单价（埋点用·桩值，待 P2 对账回填）

    Returns 缓存命中返回深拷贝副本（防调用方改动污染缓存）；否则返回 fetch_fn 结果。
    """
    ttl = ttl_for(endpoint)
    cache_on = _ENABLED and ttl > 0
    k = _key(source_id, endpoint, params) if cache_on else ""

    # 1. 缓存查
    if cache_on and not force_refresh:
        hit = _CACHE.get(k)
        if hit is not None:
            value, expire = hit
            if time.time() < expire:
                _meter(source_id, endpoint, params, status="cached",
                       cache_hit=True, cost_cny=0.0, latency_ms=0, task_id=task_id)
                return copy.deepcopy(value)
            _CACHE.pop(k, None)

    # 2. 成本闸：付费调用（cost>0）真调前检查日预算，超则 fail-loud（不返回脏数据）
    if _COST_GATE and cost_cny > 0 and (spent_today() + cost_cny) > _DAILY_BUDGET:
        _meter(source_id, endpoint, params, status="skipped", cache_hit=False,
               cost_cny=0.0, latency_ms=0, task_id=task_id)
        raise BudgetExceeded(
            f"日预算 ¥{_DAILY_BUDGET:.2f} 将超：已花 ¥{spent_today():.2f} + 本次 ¥{cost_cny:.3f}"
            f"（{source_id}{endpoint}）。调高 PROBE_DAILY_BUDGET_CNY 或关闸 PROBE_COST_GATE=0")

    # 3. 真调（计时）
    t0 = time.perf_counter()
    try:
        result = fetch_fn()
    except Exception:
        _meter(source_id, endpoint, params, status="fail", cache_hit=False,
               cost_cny=0.0, latency_ms=int((time.perf_counter() - t0) * 1000), task_id=task_id)
        raise
    latency = int((time.perf_counter() - t0) * 1000)

    # 4. 记账 + 累计花费 + 缓存
    _meter(source_id, endpoint, params, status="success", cache_hit=False,
           cost_cny=cost_cny, latency_ms=latency, task_id=task_id)
    if cost_cny > 0:
        _spend[_today()] = spent_today() + cost_cny
    if cache_on:
        _CACHE[k] = (copy.deepcopy(result), time.time() + ttl)
    return result


def _meter(source_id: str, endpoint: str, params: Any, *, status: str,
           cache_hit: bool, cost_cny: float, latency_ms: int, task_id: str) -> None:
    """埋点旁路：失败绝不影响主调用。"""
    try:
        from app.services import metering
        metering.record_datasource(
            task_id=task_id, source_id=source_id, kind=endpoint,
            cost_cny=cost_cny, status=status, cache_hit=cache_hit,
            latency_ms=latency_ms, url_hash=_url_hash(params),
        )
    except Exception:  # noqa: BLE001
        pass


def clear() -> None:
    """清空进程缓存（测试用）。"""
    _CACHE.clear()


def stats() -> dict[str, int]:
    """当前缓存条目数（观测用）。"""
    now = time.time()
    live = sum(1 for _, exp in _CACHE.values() if exp > now)
    return {"entries": len(_CACHE), "live": live}
