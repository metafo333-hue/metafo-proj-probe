"""巨潮资讯 · 上市公司公告/财务数据 · 官方公开端点 · 无需 key · 免费。

端点（官方公开 JSON，无需登录）：
  公告列表  POST https://www.cninfo.com.cn/new/hisAnnouncement/query
  公司基本信息  GET https://www.cninfo.com.cn/new/commonsse/getStockInfoByCode?scode={code}
  财务快报  GET https://www.cninfo.com.cn/new/disclosure/detail?stockCode={code}&announcementId={id}

注意：只用官方公开端点，禁模拟登录/反爬。
巨潮为中国证监会官方信息披露平台，数据合规，属公开监管数据。
Mac 直连可达。失败返回空，不抛出。
"""
from __future__ import annotations

import time
from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "cninfo",
    "domain": ["D11"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["announcement", "company", "filing"],
}

_BASE = "https://www.cninfo.com.cn"
_TIMEOUT = 20
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 probe-intel/1.0 (metafoclaw.com)",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.cninfo.com.cn/new/commonDisclosure/index",
    "Origin": "https://www.cninfo.com.cn",
}


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def announcements(
    stock_code: str,
    plate: str = "sh",
    category: str = "",
    page: int = 1,
    per_page: int = 20,
) -> list[dict[str, Any]]:
    """查询上市公司公告列表（官方公开接口）。

    Args:
        stock_code: 股票代码，如 "600519"（茅台·沪市）/ "000001"（平安·深市）
        plate:      板块，"sh"（沪市）/ "sz"（深市）/ "bj"（北交所）/ "hk"（港股）
        category:   公告分类（空=全部）；"category_ndbg_szsh"=年报 / "category_bndbg_szsh"=半年报
        page:       页码（从 1 起）
        per_page:   每页条数（最大 30）

    Returns:
        [{"ann_id", "title", "date", "stock_code", "stock_name",
          "source_id"}] 或空列表。
    """
    url = f"{_BASE}/new/hisAnnouncement/query"
    # 巨潮公告查询接口 POST form
    # 注：stock 按 "代码,股票名" 格式传，但 Mac 直连时 stock 过滤不生效（需 probe-a 代理执行精确过滤）
    # 全库模式（stock=""）在 Mac 上可达，返回全市场最新公告流，stock_code 用于结果后过滤
    payload = {
        "stock": "",  # 全库查询；精确股票过滤需 probe-a 代理
        "tabName": "fulltext",
        "pageSize": str(min(per_page, 30)),
        "pageNum": str(page),
        "column": "szse" if plate.lower() == "sz" else "sse",
        "category": category,
        "plate": plate.upper(),
        "seDate": "",
        "sortName": "time",
        "sortType": "desc",
        "isHLtitle": "true",
    }
    try:
        r = httpx.post(
            url,
            data=payload,
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        ann_list = data.get("announcements") or []
        if not isinstance(ann_list, list):
            return []
        results: list[dict[str, Any]] = []
        for ann in ann_list:
            # 客户端 stock_code 过滤（服务端过滤在 Mac 直连下不生效时的兜底）
            if stock_code and ann.get("secCode", "") != stock_code:
                continue
            if not isinstance(ann, dict):
                continue
            # 时间戳转日期
            ts = ann.get("announcementTime")
            date_str = ""
            if ts:
                try:
                    date_str = time.strftime("%Y-%m-%d", time.localtime(int(ts) / 1000))
                except Exception:
                    date_str = str(ts)
            results.append({
                "ann_id": ann.get("announcementId", ""),
                "title": (ann.get("announcementTitle") or "")[:200],
                "date": date_str,
                "stock_code": ann.get("secCode", stock_code),
                "stock_name": ann.get("secName", ""),
                "url": f"{_BASE}/new/disclosure/detail?announcementId={ann.get('announcementId','')}",
                "source_id": META["id"],
            })
        return results
    except Exception:
        return []


def stock_info(
    stock_code: str,
) -> dict[str, Any]:
    """查询上市公司基本信息（股票代码→公司名/板块/行业）。

    Args:
        stock_code: 股票代码，如 "600519" / "000001"

    Returns:
        {"code", "name", "plate", "industry", "source_id"} 或空 dict。
    """
    url = f"{_BASE}/new/commonsse/getStockInfoByCode"
    try:
        r = httpx.get(
            url,
            params={"scode": stock_code},
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return {}
        data = r.json()
        if not isinstance(data, dict):
            return {}
        return {
            "code": data.get("scode", stock_code),
            "name": data.get("sname", ""),
            "plate": data.get("plate", ""),
            "industry": data.get("industry", ""),
            "source_id": META["id"],
        }
    except Exception:
        return {}
