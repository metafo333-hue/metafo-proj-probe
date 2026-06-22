"""微信视频号+公众号情报链 · 对标 account_chain.py 的微信专属编排。

主线（视频号·重点）:
  run_from_video_channel(v2_name)            → 视频列表情报（¥0.2/页·15条）
  run_from_account_to_video_channel(keyword) → 公众号名→ghid→v2_name→视频（¥0.9/次）

辅线（公众号·降权处理）:
  run_from_article_url(url)       → 文章全文 + 传播指标 + 发布者画像 + 历史热文
  run_from_account_name(keyword)  → 账号名搜索 → 账号画像 + 历史文章 + 主体信息

成本参考:
  视频号直链:  wxvideo(¥0.2/页·15条)
  视频号发现链: wx_account/search(¥0.2) + history_by_ghid+get_finder(¥0.5) + wxvideo(¥0.2) ≈ ¥0.9
  文章链:      article_detail(¥0.045) + read_zan(¥0.04) + history_by_ghid(¥0.2) ≈ ¥0.285/次
  账号链:      wx_account/search(¥0.2) + history_by_ghid(¥0.2/页) ≈ ¥0.40/次

合规边界: 只调 JZL 授权 API · 不爬微信 DOM · 凭据经 env PROBE_JZL_KEY 注入。
"""
from __future__ import annotations

import os
from typing import Any

from app.datasources.jzl_channels import JZLChannelsAdapter


def _adapter() -> JZLChannelsAdapter:
    return JZLChannelsAdapter()


# ─────────────────────────────────────────────────────────────
# 主线：视频号 v2_name → 视频列表情报（重点处理）
# ─────────────────────────────────────────────────────────────

def run_from_video_channel(
    v2_name: str,
    max_pages: int = 1,
) -> dict[str, Any]:
    """视频号 v2_name → 近期视频列表情报包。

    Args:
        v2_name: 视频号唯一 ID（格式 v2_xxx@finder）
        max_pages: 翻页数（1=最近15条，每多1页+¥0.2）

    Returns:
        {ok, v2_name, account, videos, total_fetched, pages_fetched, cost_rmb, report_md}
    """
    if not os.getenv("PROBE_JZL_KEY"):
        return {"ok": False, "error": "缺 PROBE_JZL_KEY（走 vault 注入）"}
    if not v2_name or not v2_name.startswith("v2_"):
        return {"ok": False, "error": f"无效 v2_name（需 v2_xxx@finder 格式）: {v2_name!r}"}

    ad = _adapter()
    result = ad.fetch_account_videos(v2_name, max_pages=max_pages)

    if result.get("_needs_key"):
        return {"ok": False, "error": "缺 PROBE_JZL_KEY"}
    if result.get("_error"):
        return {"ok": False, "error": result["_error"]}

    videos = result.get("videos") or []
    account = result.get("account") or {}
    report = _build_video_channel_report(v2_name, account, videos)

    return {
        "ok": True,
        "v2_name": v2_name,
        "account": account,
        "videos": videos,
        "total_fetched": len(videos),
        "feeds_count": result.get("feeds_count"),
        "cost_rmb": round(0.2 * max_pages, 3),
        "report_md": report,
    }


# ─────────────────────────────────────────────────────────────
# 主线桥接：公众号名 → ghid → v2_name → 视频列表
# ─────────────────────────────────────────────────────────────

def run_from_account_to_video_channel(
    keyword: str,
    max_video_pages: int = 1,
) -> dict[str, Any]:
    """公众号名搜索 → 绑定视频号 → 近期视频列表。

    三步桥接链（成本约 ¥0.9/次）:
      wx_account/search(¥0.2) → history_by_ghid+get_finder=1(¥0.5) → wxvideo(¥0.2/页)

    根因修复: get_finder=1 才返回 VideoFinderInfo.user_name (v2_name)，
    之前测试为空的原因是漏了该参数。
    """
    if not os.getenv("PROBE_JZL_KEY"):
        return {"ok": False, "error": "缺 PROBE_JZL_KEY（走 vault 注入）"}

    ad = _adapter()

    # 1. 按公众号名搜索 → ghid
    search = ad.fetch_account_search(keyword)
    if search.get("_needs_key"):
        return {"ok": False, "error": "缺 PROBE_JZL_KEY"}
    accounts = search.get("accounts", [])
    if not accounts:
        return {"ok": False, "error": f"公众号搜索无结果: {keyword!r}"}

    best = accounts[0]
    ghid = best.get("ghid", "")
    account_name = best.get("name", "")
    if not ghid:
        return {"ok": False, "error": f"账号 {account_name!r} 无 ghid"}

    # 2. ghid + get_finder=1 → v2_name
    finder = ad.fetch_v2_name_by_ghid(ghid)
    if finder.get("_needs_key"):
        return {"ok": False, "error": "缺 PROBE_JZL_KEY"}
    if finder.get("_error"):
        return {
            "ok": False,
            "error": finder["_error"],
            "account_name": account_name,
            "ghid": ghid,
            "hint": "该公众号可能未绑定视频号",
        }

    v2_name = finder["v2_name"]

    # 3. v2_name → 视频列表
    result = run_from_video_channel(v2_name, max_pages=max_video_pages)
    if not result.get("ok"):
        return result

    return {
        **result,
        "discovered_via": "account_search→ghid→VideoFinderInfo",
        "account_name": account_name,
        "ghid": ghid,
        "cost_rmb": round(0.2 + 0.5 + 0.2 * max_video_pages, 3),
    }


def _build_video_channel_report(v2_name: str, account: dict, videos: list[dict]) -> str:
    nickname = account.get("nickname") or v2_name
    signature = account.get("signature") or ""
    region = account.get("region") or ""
    auth_prof = account.get("auth_profession") or ""

    lines = [f"# 视频号内容情报 · {nickname}\n"]
    if signature:
        lines.append(f"**简介**: {signature}")
    if region or auth_prof:
        lines.append(f"**地区/认证**: {region} {auth_prof}".strip())
    lines.append(f"\n**共获取视频**: {len(videos)} 条\n")

    if not videos:
        lines.append("（无数据·v2_name 可能无权限或账号不存在）")
        lines.append("\n---")
        lines.append("*数据来源: 极致了数据(jzl.com) · 播放量平台不公开*")
        return "\n".join(lines)

    lines.append("| # | 标题 | 点赞 | 评论 | 收藏 | 转发 | 时长(s) |")
    lines.append("|---|------|------|------|------|------|--------|")
    for i, v in enumerate(videos[:20], 1):
        title = (v.get("title") or "（无标题）")[:38]
        like = v.get("like_count") if v.get("like_count") is not None else "—"
        cmt = v.get("comment_count") if v.get("comment_count") is not None else "—"
        fav = v.get("fav_count") if v.get("fav_count") is not None else "—"
        fwd = v.get("forward_count") if v.get("forward_count") is not None else "—"
        dur = v.get("duration_sec") or "—"
        lines.append(f"| {i} | {title} | {like} | {cmt} | {fav} | {fwd} | {dur} |")

    lines.append("")
    lines.append("---")
    lines.append("*数据来源: 极致了数据(jzl.com) · 仅采公开元数据 · 播放量平台侧不公开*")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# 辅线：公众号文章 URL → 全量情报包
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
