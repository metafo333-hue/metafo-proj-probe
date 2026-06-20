"""极致了数据(jzl.com) · 微信公众号 + 视频号数据适配器。

实测端点覆盖(2026-06-20 · JZL728b6c6444d8aa9a · 实测余额 ¥91.79):
  视频号端点   POST /wxvideo                 ¥0.2/页(15条)   multipart/form-data
  账号搜索     POST /wx_account/search        ¥0.2/账号       JSON body
  主体信息     POST /principal_info           FREE            JSON body
  文章历史     POST /history_by_ghid          ¥0.2/页(10篇)  JSON body (内嵌 Read/Zan)
  文章阅读量   GET  /read_zan                 ¥0.04/次        查询参数
  文章全文     POST /article_detail           ¥0.045/次       JSON body
  文章热评     POST /article_comment2         ¥0.06/次        JSON body
  余额查询     POST /get_remain_money         FREE            JSON body
  v2_name发现  POST /history_by_ghid+get_finder=1  ¥0.5/次  JSON body (VideoFinderInfo.user_name)
  视频号关键词  POST /wxvideo type=4           ¥0.5/次        JSON body (60账号+50视频)

字段覆盖确认:
  ✅ fans(粉丝数)         — wx_account/search 唯一来源
  ✅ read/zan/looking      — read_zan 端点（实时）；history_by_ghid 内嵌(翻页时)
  ✅ 文章全文 content      — article_detail
  ✅ 公司主体信息          — principal_info（免费）
  ✅ v2_name 发现         — history_by_ghid+get_finder=1 → VideoFinderInfo.user_name
  ❌ play_count(播放量)   — wxvideo 端点永久缺口（平台侧不公开）
  ❌ 视频号粉丝数          — wxvideo 端点未返回

auth 两种格式:
  视频号端点    : multipart/form-data 字段 key=<key> verifycode=
  公众号端点    : JSON body {"key":"...","verifycode":"", ...params}

计费参考(单账号完整画像):
  search(¥0.2) + principal_info(FREE) + history 1页(¥0.2) ≈ ¥0.4/账号
  加全文: +¥0.045/篇; 加阅读量: +¥0.04/篇
"""
from __future__ import annotations

import http.client
import json
import os
import re
import urllib.parse
from codecs import encode
from typing import Any

from app.datasources.base import DataSourceAdapter


def _extract_v2_from_channels_url(url: str) -> str:
    """从视频号 URL 的查询参数或路径中提取 v2_name（v2_xxx@finder 格式）。"""
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)
    for key in ("v", "id", "username"):
        vals = params.get(key, [])
        if vals and vals[0].startswith("v2_") and "@finder" in vals[0]:
            return vals[0]
    m = re.search(r"(v2_[A-Za-z0-9]+@finder)", url)
    if m:
        return m.group(1)
    return ""


class JZLChannelsAdapter(DataSourceAdapter):
    source_id = "jzl_wechat_channels"
    vendor = "极致了数据(jzl.com / dajiala.com)"
    qualified = True              # 正规商业 API 采购·不自建爬取
    supported_kinds = ("wechat_article", "wechat_channels")

    _HOST = "www.dajiala.com"
    _BASE = "/fbmain/monitor/v3"

    def __init__(self) -> None:
        self._key = os.getenv("PROBE_JZL_KEY", "")

    # ──────────────────────────────────────────────────────────────────
    # 满足 DataSourceAdapter 抽象接口
    # ──────────────────────────────────────────────────────────────────

    def fetch_metadata(self, url: str, kind: str) -> dict[str, Any]:
        """url 传 v2_name / 视频号主页 URL / 公众号文章 URL。

        kind='wechat_channels' → 视频号视频列表（¥0.2/15条 · 主线·重点处理）。
        kind='wechat_article'  → 公众号文章全文 + 实时阅读量（¥0.085/篇 · 辅线）。
        """
        if not self._key:
            return {"_needs_key": True}
        # 视频号：直接传 v2_name 字符串（不含 http）
        if url.startswith("v2_") and "@finder" in url:
            raw = self._post_form("/wxvideo", {"v2_name": url, "type": "1", "last_buffer": ""})
            return self._normalize_video_page(raw, url)
        # 视频号：channels.weixin.qq.com 主页 / 视频链接
        if kind == "wechat_channels" or "channels.weixin.qq.com" in url:
            v2_name = _extract_v2_from_channels_url(url)
            if not v2_name:
                return {"_error": f"无法从 channels URL 提取 v2_name: {url[:80]}"}
            raw = self._post_form("/wxvideo", {"v2_name": v2_name, "type": "1", "last_buffer": ""})
            return self._normalize_video_page(raw, v2_name)
        # 公众号文章（辅线）
        if kind == "wechat_article" or "mp.weixin.qq.com" in url:
            return self._fetch_wechat_article(url)
        return {}

    def _fetch_wechat_article(self, url: str) -> dict[str, Any]:
        """公众号文章 URL → 全文 + 实时阅读量 + 账号元数据。
        组合调用: article_detail(¥0.045) + read_zan(¥0.04) = ¥0.085/篇。
        """
        content = self.fetch_article_content(url)         # ¥0.045
        engagement: dict = {}
        try:
            engagement = self.fetch_article_engagement(url)    # ¥0.04
        except Exception:
            pass   # read_zan 失败不阻断全文返回
        full_text = content.get("content", "")
        return {
            "title": content.get("title", ""),
            "text": full_text[:4000] if len(full_text) > 4000 else full_text,
            "platform": "wechat_mp",
            "metadata": {
                "nickname": content.get("nickname"),
                "post_time": content.get("post_time"),
                "author": content.get("author"),
                "gh_id": content.get("gh_id"),
                "wxid": content.get("wxid"),
                "desc": content.get("desc"),
                "copyright": content.get("copyright"),
                "read": engagement.get("read"),        # 实时阅读（微信上限 100001）
                "zan": engagement.get("zan"),
                "looking": engagement.get("looking"),  # 在看数
            },
            "source_id": self.source_id,
        }

    def cost_hint(self) -> dict[str, float]:
        return {"premium_data": 0.2 / 7.3}

    # ──────────────────────────────────────────────────────────────────
    # 公众号：账号发现与画像
    # ──────────────────────────────────────────────────────────────────

    def fetch_account_search(
        self, keyword: str, page: int = 1
    ) -> dict[str, Any]:
        """按关键词搜索公众号。¥4.0/批(20条) = ¥0.2/账号。
        返回字段: name, ghid, biz, wxid, fans, avg_top_read, avg_top_zan, owner_name, qrcode
        """
        if not self._key:
            return {"_needs_key": True}
        raw = self._post_json("/wx_account/search", {
            "keyword": keyword,
            "page": page,
        })
        accounts = raw.get("list") or raw.get("data") or []
        return {
            "accounts": [self._normalize_account_search(a) for a in accounts],
            "total": raw.get("total"),
            "page": page,
        }

    def fetch_principal_info(self, ghid: str) -> dict[str, Any]:
        """查询公众号主体注册信息。FREE。
        返回: company_name, reg_time, verify_customer_type, customer_type, province, auth_3rd_list
        """
        if not self._key:
            return {"_needs_key": True}
        raw = self._post_json("/principal_info", {"ghid": ghid})
        return {
            "company_name": raw.get("company_name", ""),
            "reg_time": raw.get("reg_time", ""),
            "verify_customer_type": raw.get("verify_customer_type", ""),
            "customer_type": raw.get("customer_type", ""),
            "province": raw.get("province", ""),
            "auth_3rd_list": raw.get("auth_3rd_list") or [],
        }

    # ──────────────────────────────────────────────────────────────────
    # 公众号：文章历史
    # ──────────────────────────────────────────────────────────────────

    def fetch_article_history(
        self, ghid: str, max_pages: int = 1
    ) -> dict[str, Any]:
        """按 ghid 拉取文章历史，内嵌阅读量(Read)和点赞数(Zan)。
        ¥0.2/页(约10篇)。max_pages 控制翻页深度。
        """
        if not self._key:
            return {"_needs_key": True}
        articles: list[dict] = []
        for page in range(1, max_pages + 1):
            raw = self._post_json("/history_by_ghid", {"ghid": ghid, "page": page})
            msg_list = raw.get("MsgList") or raw.get("list") or []
            for item in msg_list:
                articles.append(self._normalize_article_history(item))
            # 多数接口无 has_more，通过空列表判断
            if not msg_list:
                break
        return {"ghid": ghid, "articles": articles, "pages_fetched": page}

    # ──────────────────────────────────────────────────────────────────
    # 公众号：文章内容与指标
    # ──────────────────────────────────────────────────────────────────

    def fetch_article_engagement(self, article_url: str) -> dict[str, Any]:
        """实时阅读量+点赞+在看。¥0.04/次。GET 请求。
        article_url: https://mp.weixin.qq.com/s/<hash>
        """
        if not self._key:
            return {"_needs_key": True}
        params = urllib.parse.urlencode({"key": self._key, "url": article_url})
        conn = http.client.HTTPSConnection(self._HOST, timeout=30)
        conn.request("GET", f"{self._BASE}/read_zan?{params}")
        res = conn.getresponse()
        raw = json.loads(res.read().decode("utf-8"))
        if raw.get("code") != 0:
            raise RuntimeError(
                f"jzl read_zan error: {raw.get('msg')} (code={raw.get('code')})"
            )
        return {
            "read": raw.get("read"),           # 微信限制最高显示 100001
            "zan": raw.get("zan"),
            "looking": raw.get("looking"),     # 在看数
            "article_url": article_url,
        }

    def fetch_article_content(self, article_url: str) -> dict[str, Any]:
        """获取文章全文。¥0.045/次。
        article_url: https://mp.weixin.qq.com/s/<hash>
        返回: title, content(全文), nickname, post_time, gh_id, wxid, author, desc, copyright
        """
        if not self._key:
            return {"_needs_key": True}
        raw = self._post_json("/article_detail", {"url": article_url})
        return {
            "title": raw.get("title", ""),
            "content": raw.get("content", ""),   # 全文 HTML/文本
            "nickname": raw.get("nickname", ""),
            "post_time": raw.get("post_time", ""),
            "gh_id": raw.get("gh_id", ""),
            "wxid": raw.get("wxid", ""),
            "author": raw.get("author", ""),
            "desc": raw.get("desc", ""),
            "cover_url": raw.get("cover_url", ""),
            "copyright": raw.get("copyright"),
            "article_url": article_url,
        }

    def fetch_article_comments(
        self, article_url: str, page: int = 1
    ) -> dict[str, Any]:
        """文章热评（含地理信息）。¥0.06/次。
        返回: comments[].{content, nick_name, like_num, create_time, country_name, province_name}
        """
        if not self._key:
            return {"_needs_key": True}
        raw = self._post_json("/article_comment2", {"url": article_url, "page": page})
        comments = raw.get("comment") or raw.get("data") or []
        return {
            "comments": [self._normalize_comment(c) for c in comments],
            "article_url": article_url,
            "page": page,
        }

    # ──────────────────────────────────────────────────────────────────
    # 视频号：v2_name 发现（根因修复：必须加 get_finder=1）
    # ──────────────────────────────────────────────────────────────────

    def fetch_v2_name_by_ghid(self, ghid: str) -> dict[str, Any]:
        """通过公众号 ghid 获取绑定的视频号 v2_name。¥0.5/次。

        调用 history_by_ghid 时加 get_finder=1，才会返回 VideoFinderInfo。
        不加该参数时 VideoFinderInfo 为空——这是之前测试得到空结果的根因。
        返回: {v2_name, nickname, ghid} 或 {_error}
        """
        if not self._key:
            return {"_needs_key": True}
        raw = self._post_json("/history_by_ghid", {"ghid": ghid, "get_finder": 1})
        finder = raw.get("VideoFinderInfo") or {}
        v2_name = finder.get("user_name", "")
        nickname = finder.get("nickname", "")
        if not v2_name:
            return {"_error": f"该公众号({ghid})未绑定视频号或 VideoFinderInfo 为空"}
        return {"v2_name": v2_name, "nickname": nickname, "ghid": ghid}

    def fetch_channel_by_keyword(self, keyword: str) -> dict[str, Any]:
        """关键词搜索视频号。¥0.5/次。

        POST /wxvideo type=4 + JSON body。返回最多 60 个匹配视频号账号。
        两路来源合并: v2_info_list（账号详情）+ video_object_list（视频关联账号）。
        """
        if not self._key:
            return {"_needs_key": True}
        raw = self._post_json("/wxvideo", {"type": 4, "keywords": keyword})
        channels: list[dict] = []
        for item in (raw.get("v2_info_list") or []):
            contact = item.get("contact") or {}
            ext = contact.get("ext_info") or {}
            channels.append({
                "v2_name": contact.get("username", ""),
                "nickname": contact.get("nickname", ""),
                "signature": contact.get("signature", ""),
                "ip_region": ext.get("ip_region", "") if isinstance(ext, dict) else "",
            })
        seen = {c["v2_name"] for c in channels}
        for v in (raw.get("video_object_list") or []):
            v2 = v.get("username", "")
            if v2 and v2 not in seen:
                channels.append({
                    "v2_name": v2,
                    "nickname": v.get("nickname", ""),
                    "signature": "",
                    "ip_region": "",
                })
                seen.add(v2)
        return {"keyword": keyword, "channels": channels, "total": len(channels)}

    # ──────────────────────────────────────────────────────────────────
    # 视频号：视频列表分页（原有功能）
    # ──────────────────────────────────────────────────────────────────

    def fetch_account_videos(
        self, v2_name: str, max_pages: int = 1
    ) -> dict[str, Any]:
        """视频号视频列表分页。每页15条，¥0.2/页。"""
        if not self._key:
            return {"_needs_key": True}
        videos: list[dict] = []
        last_buffer = ""
        raw: dict = {}
        account: dict = {}
        for _ in range(max_pages):
            raw = self._post_form("/wxvideo", {
                "v2_name": v2_name,
                "type": "1",
                "last_buffer": last_buffer,
            })
            if not account:
                account = self._extract_channel_account(raw)
            batch = raw.get("object") or []
            videos.extend(self._normalize_channel_video(v) for v in batch)
            if raw.get("continue_flag") != 1:
                break
            last_buffer = raw.get("last_buffer", "")
            if not last_buffer:
                break
        return {
            "account": account,
            "feeds_count": raw.get("feeds_count"),
            "original_count": raw.get("original_count"),
            "videos": videos,
        }

    # ──────────────────────────────────────────────────────────────────
    # 余额查询
    # ──────────────────────────────────────────────────────────────────

    def fetch_balance(self) -> float | None:
        """查询账户余额（免费）。"""
        try:
            raw = self._post_json("/get_remain_money", {})
            return raw.get("remain_money")
        except Exception:
            return None

    # ──────────────────────────────────────────────────────────────────
    # HTTP 底层方法
    # ──────────────────────────────────────────────────────────────────

    def _post_json(self, path: str, extra: dict) -> dict[str, Any]:
        """公众号端点统一格式: JSON body {"key":..., "verifycode":"", ...extra}"""
        body = json.dumps({"key": self._key, "verifycode": "", **extra}).encode("utf-8")
        conn = http.client.HTTPSConnection(self._HOST, timeout=30)
        conn.request(
            "POST", self._BASE + path, body,
            {"Content-Type": "application/json", "Content-Length": str(len(body))},
        )
        res = conn.getresponse()
        raw = json.loads(res.read().decode("utf-8"))
        if raw.get("code") != 0:
            raise RuntimeError(
                f"jzl {path} error: {raw.get('msg')} (code={raw.get('code')})"
            )
        return raw

    def _post_form(self, path: str, fields: dict[str, str]) -> dict[str, Any]:
        """视频号端点统一格式: multipart/form-data。"""
        boundary = "probe_jzl_boundary_001"

        def _field(name: str, val: str) -> list[bytes]:
            return [
                encode("--" + boundary),
                encode(f"Content-Disposition: form-data; name={name};"),
                encode("Content-Type: text/plain"),
                encode(""),
                encode(val),
            ]

        parts: list[bytes] = []
        for fname, fval in {"key": self._key, "verifycode": "", **fields}.items():
            parts += _field(fname, fval)
        parts.append(encode("--" + boundary + "--"))
        parts.append(encode(""))
        body = b"\r\n".join(parts)

        conn = http.client.HTTPSConnection(self._HOST, timeout=30)
        conn.request(
            "POST", self._BASE + path, body,
            {"Content-type": f"multipart/form-data; boundary={boundary}"},
        )
        res = conn.getresponse()
        raw = json.loads(res.read().decode("utf-8"))
        if raw.get("code") != 0:
            raise RuntimeError(
                f"jzl {path} error: {raw.get('msg')} (code={raw.get('code')})"
            )
        return raw

    # ──────────────────────────────────────────────────────────────────
    # 标准化方法
    # ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _normalize_account_search(a: dict) -> dict:
        return {
            "name": a.get("name", "") or a.get("nickname", ""),
            "ghid": a.get("ghid", ""),
            "biz": a.get("biz", ""),
            "wxid": a.get("wxid", ""),
            "fans": a.get("fans"),               # 粉丝数（唯一来源）
            "avg_top_read": a.get("avg_top_read"),
            "avg_top_zan": a.get("avg_top_zan"),
            "owner_name": a.get("owner_name", ""),
            "head_url": a.get("head_url", ""),
            "qrcode": a.get("qrcode", ""),
        }

    @staticmethod
    def _normalize_article_history(item: dict) -> dict:
        return {
            "title": (item.get("Title") or item.get("title") or "")[:300],
            "content_url": item.get("ContentUrl") or item.get("url", ""),
            "publish_time": item.get("create_time") or item.get("publish_time", ""),
            "read": item.get("Read"),             # 阅读数（内嵌·微信上限 100001）
            "zan": item.get("Zan"),               # 点赞数
            "is_original": item.get("IsOriginal") or item.get("is_original"),
            "finder_export_id": item.get("finder_export_id", ""),  # 关联视频号视频 ID
            "cover_url": item.get("ThumbUrl") or item.get("cover_url", ""),
        }

    @staticmethod
    def _normalize_comment(c: dict) -> dict:
        return {
            "content": c.get("content", "") or c.get("Contents", ""),
            "nick_name": c.get("nick_name", "") or c.get("NickName", ""),
            "like_num": c.get("like_num") or c.get("LikeNum"),
            "create_time": c.get("create_time") or c.get("CreateTime"),
            "country_name": c.get("country_name", ""),
            "province_name": c.get("province_name", ""),
            "reply_count": len(c.get("reply_list") or []),
        }

    @staticmethod
    def _extract_channel_account(raw: dict) -> dict:
        c = raw.get("contact") or {}
        region = (raw.get("ip_region_info") or {}).get("region_text", "")
        auth = c.get("auth_info") or {}
        ext = c.get("ext_info") or {}
        return {
            "v2_name": c.get("username", ""),
            "nickname": c.get("nickname", ""),
            "signature": c.get("signature", ""),
            "head_url": c.get("head_url", ""),
            "region": region,
            "country": ext.get("country", ""),
            "province": ext.get("province", ""),
            "city": ext.get("city", ""),
            "auth_profession": auth.get("auth_profession", "") if isinstance(auth, dict) else "",
            "live_status": c.get("live_status"),
            "follower_count": None,    # ⚠️ wxvideo 端点未返回
            "feeds_count": raw.get("feeds_count"),
            "original_count": raw.get("original_count"),
        }

    @staticmethod
    def _normalize_channel_video(v: dict) -> dict:
        return {
            "object_id": v.get("object_id", ""),
            "title": (v.get("title") or "")[:300],
            "publish_time": v.get("publish_time", ""),
            "media_type": v.get("media_type", ""),
            "duration_sec": v.get("video_play_len"),
            "file_size_bytes": v.get("file_size"),
            "fav_count": v.get("fav_count"),
            "like_count": v.get("like_count"),
            "forward_count": v.get("forward_count"),
            "comment_count": v.get("comment_count"),
            "cover_url": v.get("cover_url", ""),
            "download_url": v.get("download_url", ""),
            "openurl": v.get("openurl", ""),
            "play_count": None,    # ⚠️ 端点未返回，平台侧不公开
        }

    def _normalize_video_page(self, raw: dict, v2_name: str) -> dict[str, Any]:
        account = self._extract_channel_account(raw)
        videos = [self._normalize_channel_video(v) for v in (raw.get("object") or [])[:5]]
        return {
            "title": account.get("nickname", v2_name),
            "text": account.get("signature", ""),
            "platform": "wechat_channels",
            "metadata": {
                "feeds_count": raw.get("feeds_count"),
                "original_count": raw.get("original_count"),
                "region": account.get("region"),
            },
            "recent_videos": videos,
            "source_id": self.source_id,
        }
