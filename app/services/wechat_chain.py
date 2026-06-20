"""微信公众号情报链 · 对标 account_chain.py 的微信专属编排。

两个入口:
  run_from_article_url(url)  → 文章 URL → 全文 + 传播指标 + 发布者画像 + 历史热文
  run_from_account_name(keyword) → 账号名搜索 → 账号画像 + 历史文章 + 主体信息

成本参考:
  文章链:  article_detail(¥0.045) + read_zan(¥0.04) + principal_info(FREE) + history_by_ghid(¥0.2) ≈ ¥0.285/次
  账号链:  wx_account/search(¥0.2) + principal_info(FREE) + history_by_ghid(¥0.2/页) ≈ ¥0.40/次

合规边界: 只调 JZL 授权 API · 不爬微信 DOM · 凭据经 env PROBE_JZL_KEY 注入。
"""
from __future__ import annotations

import os
from typing import Any

from app.datasources.jzl_channels import JZLChannelsAdapter


def _adapter() -> JZLChannelsAdapter:
    return JZLChannelsAdapter()


# ─────────────────────────────────────────────────────────────
# 入口1: 文章 URL → 全量情报包
# ─────────────────────────────────────────────────────────────

def run_from_article_url(
    url: str,
    include_history: bool = True,
    history_pages: int = 1,
) -> dict[str, Any]:
    """公众号文章 URL → 综合情报包。

    Args:
        url: mp.weixin.qq.com/s/<hash> 格式文章链接
        include_history: 是否拉账号历史文章（¥0.2/页·默认1页）
        history_pages: 历史翻页数（1=最近10篇）

    Returns:
        {ok, article, engagement, publisher, history, cost_rmb, report_md}
    """
    ad = _adapter()
    if not os.getenv("PROBE_JZL_KEY"):
        return {"ok": False, "error": "缺 PROBE_JZL_KEY（走 vault 注入）"}
    if not url or "mp.weixin.qq.com" not in url:
        return {"ok": False, "error": f"需 mp.weixin.qq.com 文章 URL，收到: {url!r}"}

    # 1. 文章全文 ¥0.045
    article = ad.fetch_article_content(url)
    if not article.get("title"):
        return {"ok": False, "error": "article_detail 返回空（URL 可能失效）", "url": url}

    # 2. 实时阅读量 ¥0.04
    engagement: dict = {}
    try:
        engagement = ad.fetch_article_engagement(url)
    except Exception as e:
        engagement = {"_error": str(e)[:120]}

    # 3. 账号主体信息 FREE（从文章响应拿 gh_id）
    publisher: dict = {}
    gh_id = article.get("gh_id", "")
    if gh_id:
        try:
            publisher = ad.fetch_principal_info(gh_id)
        except Exception as e:
            publisher = {"_error": str(e)[:120]}

    # 4. 历史文章（内嵌阅读量）¥0.2/页
    history: dict = {}
    if include_history and gh_id:
        try:
            history = ad.fetch_article_history(gh_id, max_pages=history_pages)
        except Exception as e:
            history = {"_error": str(e)[:120]}

    cost = 0.045 + 0.04 + (0.2 * history_pages if include_history and gh_id else 0)
    report = _build_article_report(url, article, engagement, publisher, history)

    return {
        "ok": True,
        "article": article,
        "engagement": engagement,
        "publisher": publisher,
        "history": history,
        "cost_rmb": round(cost, 3),
        "report_md": report,
    }


# ─────────────────────────────────────────────────────────────
# 入口2: 账号名搜索 → 账号画像
# ─────────────────────────────────────────────────────────────

def run_from_account_name(
    keyword: str,
    history_pages: int = 1,
    top_n: int = 1,
) -> dict[str, Any]:
    """账号名/关键词搜索 → 账号情报包。

    Args:
        keyword: 公众号名称关键词
        history_pages: 历史文章翻页数（1=最近10篇）
        top_n: 返回前 N 个匹配账号（1=最佳匹配·¥0.2×top_n 的主体/历史费用）

    Returns:
        {ok, accounts[{account, publisher, history}], cost_rmb, report_md}
    """
    ad = _adapter()
    if not os.getenv("PROBE_JZL_KEY"):
        return {"ok": False, "error": "缺 PROBE_JZL_KEY（走 vault 注入）"}

    # 1. 账号搜索 ¥4/批（最多20条）
    search = ad.fetch_account_search(keyword)
    all_accounts = search.get("accounts", [])
    if not all_accounts:
        return {"ok": False, "error": f"未找到「{keyword}」相关公众号"}

    candidates = all_accounts[:top_n]
    results: list[dict] = []
    total_cost = 4.0  # 搜索固定1批

    for acc in candidates:
        gh_id = acc.get("ghid", "")
        publisher: dict = {}
        history: dict = {}

        # 2. 主体信息 FREE
        if gh_id:
            try:
                publisher = ad.fetch_principal_info(gh_id)
            except Exception as e:
                publisher = {"_error": str(e)[:120]}

        # 3. 历史文章 ¥0.2/页
        if gh_id and history_pages > 0:
            try:
                history = ad.fetch_article_history(gh_id, max_pages=history_pages)
            except Exception as e:
                history = {"_error": str(e)[:120]}
            total_cost += 0.2 * history_pages

        results.append({"account": acc, "publisher": publisher, "history": history})

    report = _build_account_report(keyword, results)

    return {
        "ok": True,
        "keyword": keyword,
        "total_found": len(all_accounts),
        "accounts": results,
        "cost_rmb": round(total_cost, 3),
        "report_md": report,
    }


# ─────────────────────────────────────────────────────────────
# 报告生成（纯文本·确定性·无 LLM）
# ─────────────────────────────────────────────────────────────

def _build_article_report(
    url: str, article: dict, engagement: dict,
    publisher: dict, history: dict,
) -> str:
    title = article.get("title", "(无标题)")
    nickname = article.get("nickname", "")
    author = article.get("author", "")
    post_time = article.get("post_time", "")
    read_n = engagement.get("read", "—")
    zan_n = engagement.get("zan", "—")
    looking_n = engagement.get("looking", "—")
    company = publisher.get("company_name", "—")
    reg_time = publisher.get("reg_time", "—")
    verify_type = publisher.get("verify_customer_type", "—")
    content_preview = (article.get("content") or "")[:400]

    hist_lines = ""
    for a in (history.get("articles") or [])[:5]:
        r = a.get("read") or "—"
        z = a.get("zan") or "—"
        t = (a.get("title") or "")[:40]
        hist_lines += f"  - {t}｜阅 {r}｜赞 {z}\n"

    return f"""# 微信公众号情报报告

## 文章
**标题**: {title}
**账号**: {nickname}{' · ' + author if author else ''}
**发布时间**: {post_time}
**来源**: {url}

## 传播指标
| 阅读 | 点赞 | 在看 |
|------|------|------|
| {read_n} | {zan_n} | {looking_n} |

## 发布者主体
**注册主体**: {company}
**注册时间**: {reg_time}
**认证类型**: {verify_type}

## 内容摘要
{content_preview}{'…' if len(article.get('content','')) > 400 else ''}

## 账号近期文章（内嵌阅读量）
{hist_lines if hist_lines else '  （未拉取历史）'}
---
*数据来源: 极致了数据(jzl.com) · 仅采公开元数据*
"""


def _build_account_report(keyword: str, results: list[dict]) -> str:
    lines = [f"# 公众号账号情报报告 · 搜索词：{keyword}\n"]
    for i, r in enumerate(results, 1):
        acc = r.get("account", {})
        pub = r.get("publisher", {})
        hist = r.get("history", {})
        name = acc.get("name", "(无名)")
        fans = acc.get("fans", "—")
        avg_read = acc.get("avg_top_read", "—")
        avg_zan = acc.get("avg_top_zan", "—")
        wxid = acc.get("wxid", "—")
        company = pub.get("company_name", "—")
        reg_time = pub.get("reg_time", "—")

        lines.append(f"## {i}. {name} (@{wxid})")
        lines.append(f"**粉丝数**: {fans}　**均阅读**: {avg_read}　**均点赞**: {avg_zan}")
        lines.append(f"**注册主体**: {company}　**注册时间**: {reg_time}\n")

        arts = (hist.get("articles") or [])[:5]
        if arts:
            lines.append("**近期文章**:")
            for a in arts:
                t = (a.get("title") or "")[:50]
                r_n = a.get("read") or "—"
                z_n = a.get("zan") or "—"
                lines.append(f"  - {t} ｜阅 {r_n}｜赞 {z_n}")
        lines.append("")

    lines.append("---")
    lines.append("*数据来源: 极致了数据(jzl.com) · 仅采公开元数据*")
    return "\n".join(lines)
