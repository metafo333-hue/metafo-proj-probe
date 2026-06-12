"""央行政策 RSS · Fed / ECB / PBoC 官方 RSS Feed · 无需 key · 免费 · 官方公开。

RSS 端点：
  美联储(Fed)  https://www.federalreserve.gov/feeds/press_all.xml
  欧洲央行(ECB) https://www.ecb.europa.eu/rss/press.html
               https://www.ecb.europa.eu/rss/home.html
  中国人民银行(PBoC) https://www.pbc.gov.cn/rss/rss.xml
                    http://www.pbc.gov.cn/goutongjiaoliu/113456/113469/index.html (RSS)

合规：各国央行官方 RSS 公告，公有领域/新闻发布，无版权限制。
失败返回空，不抛出。
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "cbank_rss",
    "domain": ["D14"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["policy", "announcement", "central_bank"],
}

_TIMEOUT = 20
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; probe@metafoclaw.com)",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

_FEEDS: dict[str, dict[str, str]] = {
    "fed": {
        "name": "U.S. Federal Reserve",
        "url": "https://www.federalreserve.gov/feeds/press_all.xml",
        "country": "US",
    },
    "ecb": {
        "name": "European Central Bank",
        "url": "https://www.ecb.europa.eu/rss/press.html",
        "country": "EU",
    },
    "pboc": {
        "name": "People's Bank of China",
        "url": "https://www.pbc.gov.cn/rss/rss.xml",
        "country": "CN",
    },
}


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def fetch_feed(
    bank: str = "fed",
    limit: int = 20,
) -> list[dict[str, Any]]:
    """拉取单个央行 RSS 公告。

    Args:
        bank:  央行代码，"fed"（美联储）/ "ecb"（欧洲央行）/ "pboc"（人民银行）
        limit: 最多返回条数

    Returns:
        [{"title", "link", "date", "description", "bank", "country",
          "source_id"}] 或空列表。
    """
    feed_info = _FEEDS.get(bank.lower())
    if not feed_info:
        return []
    try:
        r = httpx.get(
            feed_info["url"],
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return []
        return _parse_rss(r.text, feed_info, limit)
    except Exception:
        return []


def fetch_all(limit_per_bank: int = 10) -> list[dict[str, Any]]:
    """并行拉取三家主要央行 RSS（合并后按日期降序）。

    Args:
        limit_per_bank: 每家央行最多条数

    Returns:
        合并 + 排序后的公告列表，含 "bank" 字段区分来源。
    """
    results: list[dict[str, Any]] = []
    for bank_code in _FEEDS:
        items = fetch_feed(bank_code, limit=limit_per_bank)
        results.extend(items)
    # 按日期降序（尽力排序，格式不统一时退化为原顺序）
    try:
        results.sort(key=lambda x: x.get("date", ""), reverse=True)
    except Exception:
        pass
    return results


def _parse_rss(xml_text: str, feed_info: dict[str, str], limit: int) -> list[dict[str, Any]]:
    """解析 RSS/Atom XML，兼容 RSS 2.0 和 Atom 格式。"""
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "content": "http://purl.org/rss/1.0/modules/content/",
        "dc": "http://purl.org/dc/elements/1.1/",
    }
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        # 尝试清理 BOM / 非法字符后重试
        cleaned = re.sub(r"[^\x09\x0A\x0D\x20-퟿-�]", "", xml_text)
        try:
            root = ET.fromstring(cleaned)
        except Exception:
            return []

    items: list[dict[str, Any]] = []
    bank_name = feed_info.get("name", "")
    country = feed_info.get("country", "")

    # RSS 2.0 格式
    for item in root.findall(".//item"):
        if len(items) >= limit:
            break
        title = _text(item.find("title"))
        link = _text(item.find("link"))
        pub_date = _text(item.find("pubDate")) or _text(item.find("dc:date", ns))
        desc = _text(item.find("description"))
        items.append({
            "title": title[:300] if title else "",
            "link": link[:500] if link else "",
            "date": _normalize_date(pub_date),
            "description": (desc or "")[:500],
            "bank": bank_name,
            "country": country,
            "source_id": META["id"],
        })

    # Atom 格式（ECB 使用）
    if not items:
        for entry in root.findall("atom:entry", ns):
            if len(items) >= limit:
                break
            title_el = entry.find("atom:title", ns)
            link_el = entry.find("atom:link", ns)
            updated_el = entry.find("atom:updated", ns)
            summary_el = entry.find("atom:summary", ns)
            title = _text(title_el)
            link = link_el.get("href", "") if link_el is not None else ""
            pub_date = _text(updated_el)
            desc = _text(summary_el)
            items.append({
                "title": title[:300] if title else "",
                "link": link[:500] if link else "",
                "date": _normalize_date(pub_date),
                "description": (desc or "")[:500],
                "bank": bank_name,
                "country": country,
                "source_id": META["id"],
            })

    return items[:limit]


def _text(el: Any) -> str:
    if el is None:
        return ""
    return (el.text or "").strip()


def _normalize_date(raw: str) -> str:
    """尽力提取 YYYY-MM-DD，兼容 RFC 822 / ISO 8601。"""
    if not raw:
        return ""
    # ISO 8601: 2024-06-12T...
    m = re.search(r"(\d{4}-\d{2}-\d{2})", raw)
    if m:
        return m.group(1)
    # RFC 822: 12 Jun 2024
    months = {
        "jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05", "jun": "06",
        "jul": "07", "aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12",
    }
    m2 = re.search(r"(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})", raw)
    if m2:
        day, mon, year = m2.groups()
        mon_num = months.get(mon.lower(), "00")
        return f"{year}-{mon_num}-{day.zfill(2)}"
    return raw[:10]
