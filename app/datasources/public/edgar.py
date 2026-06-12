"""SEC EDGAR · 无需 key · 免费 · 美国公共记录。

端点：
  submissions  https://data.sec.gov/submissions/CIK{cik:010d}.json
  ticker map   https://www.sec.gov/files/company_tickers.json
合规：SEC EDGAR 官方数据 API，公共记录，须带 User-Agent（SEC 要求）。
失败返回空，不抛出。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "edgar",
    "domain": ["D11", "D4"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["filing", "company"],
}

_SUBMISSIONS_BASE = "https://data.sec.gov/submissions"
_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
_TIMEOUT = 20
# SEC EDGAR 要求 User-Agent 包含公司名和邮件
_HEADERS = {
    "User-Agent": "probe-intel/1.0 metafoclaw.com probe@metafoclaw.com",
    "Accept": "application/json",
}

# 内存缓存 ticker→CIK 映射（进程生命周期有效）
_ticker_cache: dict[str, str] | None = None


def _get_ticker_map() -> dict[str, str]:
    """返回 {ticker_upper: cik_padded_10} 映射。失败返回空字典。"""
    global _ticker_cache
    if _ticker_cache is not None:
        return _ticker_cache
    try:
        r = httpx.get(_TICKERS_URL, timeout=_TIMEOUT, headers=_HEADERS)
        if r.status_code == 200:
            data = r.json()
            mapping: dict[str, str] = {}
            for _idx, entry in data.items():
                ticker = str(entry.get("ticker", "")).upper()
                cik = str(entry.get("cik_str", "")).zfill(10)
                if ticker:
                    mapping[ticker] = cik
            _ticker_cache = mapping
            return _ticker_cache
    except Exception:
        pass
    return {}


def _resolve_cik(cik_or_ticker: str) -> str | None:
    """将 ticker 或 CIK 统一转为 10 位补零 CIK 字符串。失败返回 None。"""
    val = cik_or_ticker.strip()
    if val.isdigit():
        return val.zfill(10)
    # 尝试 ticker → CIK
    mapping = _get_ticker_map()
    return mapping.get(val.upper())


def company_filings(
    cik_or_ticker: str,
    form_types: list[str] | None = None,
    max_items: int = 20,
) -> dict[str, Any]:
    """查询公司最新 SEC 申报文件。

    Args:
        cik_or_ticker: 公司 CIK（数字）或 ticker（如 "AAPL"）
        form_types:    过滤表单类型，如 ["10-K", "10-Q"]，None 表示不过滤
        max_items:     返回最多文件数，默认 20

    Returns:
        {
          "cik": "...",
          "name": "...",
          "tickers": [...],
          "sic_description": "...",
          "filings": [{form, accessionNumber, filingDate, primaryDocument, url}]
        }
        失败返回空字典。
    """
    cik = _resolve_cik(cik_or_ticker)
    if not cik:
        return {}
    url = f"{_SUBMISSIONS_BASE}/CIK{cik}.json"
    try:
        r = httpx.get(url, timeout=_TIMEOUT, headers=_HEADERS)
        if r.status_code != 200:
            return {}
        data = r.json()
        company_name = data.get("name", "")
        tickers = data.get("tickers") or []
        sic_desc = data.get("sicDescription", "")

        recent = (data.get("filings") or {}).get("recent") or {}
        forms = recent.get("form") or []
        acc_nums = recent.get("accessionNumber") or []
        dates = recent.get("filingDate") or []
        primary_docs = recent.get("primaryDocument") or []

        filings: list[dict[str, Any]] = []
        for form, acc, date, doc in zip(forms, acc_nums, dates, primary_docs):
            if form_types and form not in form_types:
                continue
            # 构造 EDGAR viewer URL
            acc_clean = acc.replace("-", "")
            filing_url = (
                f"https://www.sec.gov/Archives/edgar/data/{int(cik)}"
                f"/{acc_clean}/{doc}"
            )
            filings.append({
                "form": form,
                "accessionNumber": acc,
                "filingDate": date,
                "primaryDocument": doc,
                "url": filing_url,
            })
            if len(filings) >= max_items:
                break

        return {
            "cik": cik,
            "name": company_name,
            "tickers": tickers,
            "sic_description": sic_desc,
            "filings": filings,
            "source_id": META["id"],
        }
    except Exception:
        return {}
