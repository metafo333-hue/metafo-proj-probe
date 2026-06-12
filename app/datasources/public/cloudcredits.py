"""云 Credits 库 · 创业公司云资源优惠聚合 · D17 · 无需 key · 免费。

数据源（实测 2026-06-12）：
  fetch_startup_credits  dakshshah96/awesome-startup-credits README.md (MIT)
                         — 200 OK，16556 bytes，Markdown 条目解析提取
  fetch_aws_activate     AWS Activate 官网条款页静态信息（本地 cataloged）

实测备注：
  - t3-sh/cloudcredits.io raw JSON 路径全部 404（/public/credits.json / src/data/ 均无），
    降级到 dakshshah96/awesome-startup-credits 作为主源（MIT License, 200 OK）。
  - cloudcredits.io 网站为 Next.js 服务端渲染，无公开机器可读 JSON 端点，暂 cataloged。

合规：awesome-startup-credits 采用 MIT License，允许任何用途使用。
失败返回空，不抛出。
"""
from __future__ import annotations

import re
from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "cloudcredits",
    "domain": ["D17", "D15"],
    "access_type": "free",
    "method": ["W"],
    "kinds": ["cloud_credits", "startup_deal"],
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

# 模块级缓存
_credits_cache: list[dict[str, Any]] | None = None


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def fetch_startup_credits(
    force_reload: bool = False,
    category: str = "",
    keyword: str = "",
    top_n: int = 100,
) -> list[dict[str, Any]]:
    """拉取 awesome-startup-credits 条目列表。

    Args:
        force_reload: True = 强制重新下载
        category:     按分类过滤，如 "Cloud Computing" / "Email Delivery"（含匹配）
        keyword:      按公司名 / 描述关键词过滤（大小写不敏感）
        top_n:        最多返回条数（1-500）

    Returns:
        [{"company", "category", "description", "url", "source_id"}] 或空列表。
    """
    global _credits_cache
    if _credits_cache is None or force_reload:
        try:
            r = httpx.get(_AWESOME_URL, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
            if r.status_code != 200:
                return []
            _credits_cache = _parse_readme(r.text)
        except Exception:
            return []

    results = _credits_cache or []

    if category:
        cat_lower = category.lower()
        results = [i for i in results if cat_lower in i.get("category", "").lower()]

    if keyword:
        kw = keyword.lower()
        results = [
            i for i in results
            if kw in i.get("company", "").lower() or kw in i.get("description", "").lower()
        ]

    return results[:max(1, min(top_n, 500))]


def categories() -> list[str]:
    """返回所有可用的分类名称列表。"""
    items = fetch_startup_credits()
    return sorted(set(i["category"] for i in items if i.get("category")))


# ── 内部解析 ──────────────────────────────────────────────────────────────────

def _parse_readme(md: str) -> list[dict[str, Any]]:
    """解析 awesome-startup-credits README.md，提取各分类下的条目。

    Markdown 格式：
      ### Category Name
      - [Company Name](url) - Description
    """
    items: list[dict[str, Any]] = []
    current_category = ""

    for line in md.splitlines():
        line = line.strip()

        # 检测分类标题（### Advertising / ### Cloud Computing 等）
        heading_m = re.match(r"^#{2,4}\s+(.+)$", line)
        if heading_m:
            heading = heading_m.group(1).strip()
            # 跳过目录级标题（Contents / Overview 等）
            if heading not in ("Contents", "Awesome Startup Credits") and not heading.startswith("Awesome"):
                current_category = heading
            continue

        # 解析条目行：- [Company](url) - Description
        item_m = re.match(
            r"^[-*]\s+\[([^\]]+)\]\(([^)]+)\)\s*[-–—]?\s*(.*)$", line
        )
        if item_m and current_category:
            company = item_m.group(1).strip()
            url = item_m.group(2).strip()
            desc = item_m.group(3).strip()
            # 去除描述中多余的 markdown 链接
            desc = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", desc)
            items.append({
                "company": company[:150],
                "category": current_category[:100],
                "description": desc[:400],
                "url": url,
                "source_id": META["id"],
            })

    return items
