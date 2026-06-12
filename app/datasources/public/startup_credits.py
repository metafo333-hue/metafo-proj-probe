"""创业扶持额度 · awesome-startup-credits Markdown 解析 · D17 · 无需 key · 免费。

数据源（实测 2026-06-12）：
  fetch_credits   dakshshah96/awesome-startup-credits README.md  (MIT License · 200 OK)
                  — 与 cloudcredits.py 使用同一 raw URL，但本模块侧重「额度提取」，
                    尝试从描述文本中解析出金额/时长信息，便于上层额度量化分析。

实测备注：
  - awesome-builder-programs raw URL 404，暂不接入。
  - 本模块专注「扶持额度量化」视角（credit_amount / duration），
    cloudcredits.py 专注「分类浏览」视角，两者互补。

合规：MIT License，允许任何用途使用。失败返回空，不抛出。
"""
from __future__ import annotations

import re
from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "startup_credits",
    "domain": ["D17"],
    "access_type": "free",
    "method": ["W"],
    "kinds": ["startup_credits", "ai_deal"],
}

_TIMEOUT = 20
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com)",
    "Accept": "text/plain, */*",
}

_AWESOME_URL = (
    "https://raw.githubusercontent.com/dakshshah96/"
    "awesome-startup-credits/master/README.md"
)

# 金额正则：匹配 "$50,000" / "$25K" / "€1,000" / "50000 USD" 等
_AMOUNT_RE = re.compile(
    r"(?:USD|US\$|\$|€|£)\s*[\d,]+(?:\.\d+)?[KkMm]?"
    r"|[\d,]+(?:\.\d+)?\s*(?:USD|credits?)",
    re.IGNORECASE,
)
# 时长正则：匹配 "1 year" / "12 months" / "two years" 等
_DURATION_RE = re.compile(
    r"\b(\d+|one|two|three|four|five|six|twelve)\s*(year|month|day)s?\b",
    re.IGNORECASE,
)

_cache: list[dict[str, Any]] | None = None


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def fetch_credits(
    force_reload: bool = False,
    min_amount_usd: float | None = None,
    keyword: str = "",
    top_n: int = 100,
) -> list[dict[str, Any]]:
    """拉取并解析创业扶持额度条目，含金额/时长提取。

    Args:
        force_reload:   True = 强制重新下载
        min_amount_usd: 按提取到的 USD 金额过滤（仅有明确金额的条目）
        keyword:        按公司名 / 描述关键词过滤（大小写不敏感）
        top_n:          最多返回条数（1-500）

    Returns:
        [{"company", "category", "description", "url",
          "credit_amount_raw", "credit_amount_usd", "duration_raw",
          "source_id"}] 或空列表。
    """
    global _cache
    if _cache is None or force_reload:
        try:
            r = httpx.get(_AWESOME_URL, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
            if r.status_code != 200:
                return []
            _cache = _parse_md(r.text)
        except Exception:
            return []

    results = _cache or []

    if min_amount_usd is not None:
        results = [
            i for i in results
            if i.get("credit_amount_usd") is not None
            and i["credit_amount_usd"] >= min_amount_usd
        ]

    if keyword:
        kw = keyword.lower()
        results = [
            i for i in results
            if kw in i.get("company", "").lower() or kw in i.get("description", "").lower()
        ]

    # 按金额降序（无金额排末尾）
    results = sorted(results, key=lambda x: (x.get("credit_amount_usd") or -1), reverse=True)
    return results[:max(1, min(top_n, 500))]


def high_value_credits(min_usd: float = 10000, top_n: int = 30) -> list[dict[str, Any]]:
    """返回高额扶持条目（≥ min_usd），快速筛选高价值资源。"""
    return fetch_credits(min_amount_usd=min_usd, top_n=top_n)


# ── 内部解析 ──────────────────────────────────────────────────────────────────

_WORD_NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "twelve": 12}


def _parse_amount_usd(desc: str) -> float | None:
    """从描述文本中提取最大金额并换算为 USD float。"""
    matches = _AMOUNT_RE.findall(desc)
    if not matches:
        return None
    best = 0.0
    for raw in matches:
        num_str = re.sub(r"[USD$€£,\s]", "", raw, flags=re.IGNORECASE)
        multiplier = 1.0
        if num_str.endswith(("K", "k")):
            multiplier = 1000.0
            num_str = num_str[:-1]
        elif num_str.endswith(("M", "m")):
            multiplier = 1_000_000.0
            num_str = num_str[:-1]
        try:
            val = float(num_str) * multiplier
            if val > best:
                best = val
        except ValueError:
            pass
    return best if best > 0 else None


def _parse_duration(desc: str) -> str:
    """从描述文本中提取时长字符串，如 '1 year' / '12 months'。"""
    m = _DURATION_RE.search(desc)
    if not m:
        return ""
    num_raw = m.group(1).lower()
    num = _WORD_NUM.get(num_raw, num_raw)
    unit = m.group(2).lower()
    return f"{num} {unit}"


def _parse_md(md: str) -> list[dict[str, Any]]:
    """解析 README.md 提取条目并附加金额/时长字段。"""
    items: list[dict[str, Any]] = []
    current_category = ""

    for line in md.splitlines():
        line = line.strip()
        heading_m = re.match(r"^#{2,4}\s+(.+)$", line)
        if heading_m:
            heading = heading_m.group(1).strip()
            if heading not in ("Contents", "Awesome Startup Credits"):
                current_category = heading
            continue

        item_m = re.match(r"^[-*]\s+\[([^\]]+)\]\(([^)]+)\)\s*[-–—]?\s*(.*)$", line)
        if item_m and current_category:
            company = item_m.group(1).strip()
            url = item_m.group(2).strip()
            desc = item_m.group(3).strip()
            desc = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", desc)

            amount = _parse_amount_usd(desc)
            duration = _parse_duration(desc)

            items.append({
                "company": company[:150],
                "category": current_category[:100],
                "description": desc[:400],
                "url": url,
                "credit_amount_raw": _AMOUNT_RE.search(desc).group(0) if _AMOUNT_RE.search(desc) else "",
                "credit_amount_usd": amount,
                "duration_raw": duration,
                "source_id": META["id"],
            })

    return items
