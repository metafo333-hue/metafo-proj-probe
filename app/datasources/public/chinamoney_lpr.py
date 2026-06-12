"""央行 LPR · 中国货币网官方贷款市场报价利率 · 无需 key · 免费 · 官方数据。

端点：
  LPR 历史  GET https://www.chinamoney.com.cn/ags/ms/cm-u-bk-ylzs/LprHisDate
  LPR 当前  GET https://www.chinamoney.com.cn/ags/ms/cm-u-bk-ylzs/GetLprHisData

合规：中国货币网（chinamoney.com.cn）是中国人民银行官方认可的人民币基准利率信息发布平台，
LPR 数据属于官方公开监管数据，无版权限制。
Mac 直连可达。失败返回空，不抛出。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "chinamoney_lpr",
    "domain": ["D13", "D14"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["rate", "lpr", "macro"],
}

_BASE = "https://www.chinamoney.com.cn/ags/ms/cm-u-bk-ylzs"
_TIMEOUT = 20
_HEADERS = {
    "User-Agent": "Mozilla/5.0 probe-intel/1.0 (metafoclaw.com)",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.chinamoney.com.cn/chinese/lpr/",
}


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def latest() -> dict[str, Any]:
    """获取最新 LPR 报价（1年期 + 5年期以上）。

    Returns:
        {"date", "lpr_1y", "lpr_5y", "source_id"} 或空 dict。
    """
    try:
        r = httpx.get(
            f"{_BASE}/LprHisDate",
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return {}
        data = r.json()
        # 返回 {"data": [{"lprDate": "2025-01-20", "lpr1y": "3.10", "lprOver5y": "3.60"}, ...]}
        records = data.get("data") or []
        if not isinstance(records, list) or not records:
            return {}
        latest_rec = records[0]
        return {
            "date": latest_rec.get("lprDate", ""),
            "lpr_1y": latest_rec.get("lpr1y") or latest_rec.get("lpr_1y"),
            "lpr_5y": latest_rec.get("lprOver5y") or latest_rec.get("lpr_5y"),
            "source_id": META["id"],
        }
    except Exception:
        return {}


def history(
    start_date: str = "",
    end_date: str = "",
    limit: int = 24,
) -> list[dict[str, Any]]:
    """获取 LPR 历史数据。

    Args:
        start_date: 起始日期 "YYYY-MM-DD"（空=不限）
        end_date:   结束日期 "YYYY-MM-DD"（空=不限）
        limit:      最多返回条数（默认 24 期）

    Returns:
        [{"date", "lpr_1y", "lpr_5y", "source_id"}] 或空列表。
    """
    params: dict[str, str] = {}
    if start_date:
        params["startDate"] = start_date
    if end_date:
        params["endDate"] = end_date
    try:
        r = httpx.get(
            f"{_BASE}/LprHisDate",
            params=params,
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        records = data.get("data") or []
        if not isinstance(records, list):
            return []
        results: list[dict[str, Any]] = []
        for rec in records[:limit]:
            if not isinstance(rec, dict):
                continue
            results.append({
                "date": rec.get("lprDate", ""),
                "lpr_1y": rec.get("lpr1y") or rec.get("lpr_1y"),
                "lpr_5y": rec.get("lprOver5y") or rec.get("lpr_5y"),
                "source_id": META["id"],
            })
        return results
    except Exception:
        return []
