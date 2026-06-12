"""中国法定节假日 · NateScarlet/holiday-cn raw JSON · D15 · 无需 key · 免费。

数据源（实测 2026-06-12 · HTTP 200）：
  fetch_year     https://raw.githubusercontent.com/NateScarlet/holiday-cn/master/{year}.json
                 — 含完整年度假期安排（holiday/workday 字段），年份回填至历史可查

合规：NateScarlet/holiday-cn 采用 MIT License，允许任何用途使用。
     数据来自中国政府官方公告整理，CC 开放数据。
失败返回空，不抛出。
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "holiday_cn",
    "domain": ["D15"],
    "access_type": "free",
    "method": ["W"],
    "kinds": ["holiday", "workday_schedule"],
}

_BASE_URL = "https://raw.githubusercontent.com/NateScarlet/holiday-cn/master"
_TIMEOUT = 20
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com)",
    "Accept": "application/json",
}

# 模块级缓存：{year: [days]}
_cache: dict[int, list[dict[str, Any]]] = {}


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def fetch_year(
    year: int | None = None,
    force_reload: bool = False,
) -> list[dict[str, Any]]:
    """拉取指定年度的节假日与调休数据。

    Args:
        year:         年份，如 2026 / 2025；None = 当前年份
        force_reload: True = 忽略缓存强制重新下载

    Returns:
        [{"date", "name", "is_offday", "is_workday", "year",
          "source_id"}] 或空列表。
        is_offday=True  = 法定节假日（该天可放假）
        is_workday=True = 调休工作日（该天需补班）
    """
    if year is None:
        year = datetime.now().year

    if year in _cache and not force_reload:
        return _cache[year]

    url = f"{_BASE_URL}/{year}.json"
    try:
        r = httpx.get(url, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return []
        raw = r.json()
        days_raw = raw.get("days") or []
        results = [_normalize_day(d, year) for d in days_raw if isinstance(d, dict)]
        _cache[year] = results
        return results
    except Exception:
        return []


def holidays(year: int | None = None) -> list[dict[str, Any]]:
    """返回指定年度的法定节假日列表（is_offday=True）。"""
    return [d for d in fetch_year(year) if d.get("is_offday")]


def workday_adjustments(year: int | None = None) -> list[dict[str, Any]]:
    """返回指定年度的调休工作日列表（is_workday=True，通常为周末补班）。"""
    return [d for d in fetch_year(year) if d.get("is_workday")]


def is_holiday(day: date | str) -> bool | None:
    """判断指定日期是否为法定节假日。

    Args:
        day: date 对象或 "2026-10-01" 格式字符串

    Returns:
        True = 节假日；False = 工作日（或调休班）；None = 数据不可用
    """
    if isinstance(day, str):
        try:
            day = date.fromisoformat(day)
        except ValueError:
            return None
    year_data = fetch_year(day.year)
    if not year_data:
        return None
    date_str = day.isoformat()
    for d in year_data:
        if d.get("date") == date_str:
            if d.get("is_offday"):
                return True
            if d.get("is_workday"):
                return False
    # 未在 days 列表中 → 按自然周推断（周六日默认休，工作日默认班）
    if day.weekday() >= 5:  # Saturday=5, Sunday=6
        return True
    return False


def upcoming_holidays(
    from_date: date | None = None,
    days_ahead: int = 60,
) -> list[dict[str, Any]]:
    """返回从 from_date 起 days_ahead 天内的法定节假日。

    Args:
        from_date:  起始日期（含），None = 今日
        days_ahead: 往后查询天数（1-365）

    Returns:
        按日期升序排列的节假日列表。
    """
    from datetime import timedelta
    if from_date is None:
        from_date = date.today()
    to_date = from_date + timedelta(days=max(1, min(days_ahead, 365)))

    years = set()
    cur = from_date
    while cur <= to_date:
        years.add(cur.year)
        cur = date(cur.year + 1, 1, 1) if cur.month == 12 and cur.day == 31 else cur.replace(day=28)
        # 简化：只加两个年份
        if len(years) >= 2:
            break
    years = {from_date.year, to_date.year}

    all_holidays: list[dict[str, Any]] = []
    for y in sorted(years):
        all_holidays.extend(holidays(y))

    results = [
        h for h in all_holidays
        if from_date.isoformat() <= h.get("date", "") <= to_date.isoformat()
    ]
    return sorted(results, key=lambda x: x.get("date", ""))


# ── 内部规范化 ───────────────────────────────────────────────────────────────

def _normalize_day(d: dict[str, Any], year: int) -> dict[str, Any]:
    return {
        "date": (d.get("date") or "")[:10],
        "name": (d.get("name") or "")[:50],
        "is_offday": bool(d.get("isOffDay", False)),
        "is_workday": not bool(d.get("isOffDay", False)),
        "year": year,
        "source_id": META["id"],
    }
