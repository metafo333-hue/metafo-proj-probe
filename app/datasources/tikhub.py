"""TikHub 第三方商业数据 API 适配器 · 覆盖五平台（抖音/小红书/微博/B站/快手）。

合规边界（2026-06-04 元东方定调）：
- probe 只调用 TikHub 商业接口，**自身不主动爬取**；TikHub 如何取数是其 ToS/合规责任，probe 仅对「调用行为」负责。
- probe **不调用** TikHub 的 Captcha Solver 等绕反爬工具，仅调数据接口。
- API key 经 env `PROBE_TIKHUB_KEY` 注入（vault）；无 key → 返回 `_needs_key`（上层转占位）。
- R8/R1：注册 + 付费授权由元东方完成，key 配置化。
- 原料进结论出：_normalize 只取标准化元数据，不直吐第三方原始全量数据。

SDK：`pip install tikhub`（官方）。已确认方法：
  hybrid_parsing.video_data(url=)  — 通用 URL 解析（抖音/B站/快手/微博视频）
  xiaohongshu_web.get_note_info_v2(share_text=)  — 小红书笔记

抖音播放量修复（2026-06-22）：
  通用接口不再返回播放量 → fetch_metadata 会追加调用统计专用端点
  /api/v1/douyin/app/v3/fetch_video_statistics 注入真实 play_count。
  批量接口：fetch_batch_douyin_stats(aweme_ids) 每次最多 50 条（$0.025/次）。
"""
from __future__ import annotations

import json as _json
import os
import re
import urllib.parse
import urllib.request
from typing import Any

from app.datasources.base import DataSourceAdapter
from app.datasources import source_cache

_TIKHUB_BASE = os.environ.get("TIKHUB_API_BASE", "https://api.tikhub.io")
_DOUYIN_STAT_EP = "/api/v1/douyin/app/v3/fetch_video_statistics"
_DOUYIN_BATCH_STAT_EP = "/api/v1/douyin/app/v3/fetch_multi_video_statistics"
_DOUYIN_BATCH_SIZE = 50  # 单次最多 50 个，$0.025/次


class TikHubAdapter(DataSourceAdapter):
    source_id = "tikhub"
    vendor = "TikHub.io"
    qualified = True                              # 已按正规商业 API 采购接入（新边界）
    supported_kinds = ("video", "social")

    _PLATFORM = [
        ("douyin", re.compile(r"douyin\.com|iesdouyin\.com")),
        ("bilibili", re.compile(r"bilibili\.com|b23\.tv")),
        ("kuaishou", re.compile(r"kuaishou\.com")),
        ("xiaohongshu", re.compile(r"xiaohongshu\.com|xhslink\.com")),
        ("weibo", re.compile(r"weibo\.(com|cn)")),
    ]

    def __init__(self) -> None:
        self._key = os.getenv("PROBE_TIKHUB_KEY", "")
        self._client = None

    def _platform(self, url: str) -> str | None:
        u = (url or "").lower()
        for name, rx in self._PLATFORM:
            if rx.search(u):
                return name
        return None

    def _get_client(self):
        if self._client is None:
            from tikhub import TikHub  # lazy：模块加载不依赖 SDK
            self._client = TikHub(api_key=self._key)
        return self._client

    def fetch_metadata(self, url: str, kind: str) -> dict[str, Any]:
        if not self._key:
            return {"_needs_key": True}           # 适配器就绪·待 key（R8/R1）
        plat = self._platform(url)
        if plat is None:
            return {}                              # 非五平台 → 本适配器不处理
        c = self._get_client()
        ep = "tikhub:note_info" if plat == "xiaohongshu" else "tikhub:video_data"

        def _do() -> Any:
            if plat == "xiaohongshu":
                return c.xiaohongshu_web.get_note_info_v2(share_text=url)
            return c.hybrid_parsing.video_data(url=url)   # 通用解析（douyin/bilibili/kuaishou/weibo）
        try:
            # source_cache 收口：按 url 端点级缓存（省重复付费）+ 计费埋点
            raw = source_cache.cached_call(self.source_id, ep, {"url": url}, _do, cost_cny=0.001)
        except Exception as e:
            return {"_error": f"{type(e).__name__}: {str(e)[:160]}"}

        result = self._normalize(raw, plat, url)

        # 抖音专项：通用接口不返回播放量，追加统计端点注入真实 play_count
        if plat == "douyin":
            aweme_id = self._extract_aweme_id(raw)
            if aweme_id:
                pc = self._fetch_douyin_play_count(aweme_id)
                if pc and pc > 0:
                    result.setdefault("metadata", {})["play_count"] = pc

        return result

    def _normalize(self, raw: Any, plat: str, url: str) -> dict[str, Any]:
        """第三方原始数据 → 标准化元数据（原料进结论出：只取元数据，不直吐全量原文）。"""
        data = raw.get("data", raw) if isinstance(raw, dict) else {}
        if not isinstance(data, dict):
            data = {}

        if plat == "douyin":
            return self._normalize_douyin(data)

        title = data.get("desc") or data.get("title") or data.get("content") or ""
        if not isinstance(title, str):
            title = str(title)
        metrics = {k: data.get(k) for k in
                   ("digg_count", "like_count", "comment_count",
                    "share_count", "collect_count", "play_count")
                   if k in data}
        return {
            "title": title[:200],
            "text": title,
            "platform": plat,
            "metadata": metrics,
            "source_id": self.source_id,
        }

    def _normalize_douyin(self, data: dict) -> dict[str, Any]:
        """抖音响应按真实 aweme_detail 结构精确提取字段。"""
        detail = data.get("aweme_detail") if isinstance(data, dict) else None
        if not isinstance(detail, dict):
            detail = {}
        st = detail.get("statistics", {}) or {}
        title = detail.get("desc", "") or ""
        if not isinstance(title, str):
            title = str(title)
        metrics: dict[str, Any] = {}
        for k in ("digg_count", "comment_count", "share_count", "collect_count"):
            v = st.get(k)
            if v is not None:
                metrics[k] = v
        pc = st.get("play_count")
        if pc is not None:
            metrics["play_count"] = pc
        return {
            "title": title[:200],
            "text": title,
            "platform": "douyin",
            "metadata": metrics,
            "source_id": self.source_id,
        }

    def _extract_aweme_id(self, raw: Any) -> str | None:
        """从 hybrid_parsing 响应中提取 aweme_id。"""
        data = raw.get("data", raw) if isinstance(raw, dict) else {}
        detail = data.get("aweme_detail") if isinstance(data, dict) else None
        if isinstance(detail, dict):
            return detail.get("aweme_id")
        return None

    def _fetch_douyin_play_count(self, aweme_id: str) -> int | None:
        """调抖音统计接口拿单条 play_count（$0.001/次）。失败返回 None。
        参数名：aweme_ids（复数）；响应：data.statistics_list[0].play_count。
        """
        url = (f"{_TIKHUB_BASE}{_DOUYIN_STAT_EP}?"
               f"{urllib.parse.urlencode({'aweme_ids': aweme_id})}")
        try:
            req = urllib.request.Request(url, headers={
                "Authorization": f"Bearer {self._key}",
                "Accept": "application/json",
                "User-Agent": "probe/1.0 (+https://metafoclaw.com)",
            })
            with urllib.request.urlopen(req, timeout=20) as resp:
                body = _json.loads(resp.read().decode("utf-8"))
            stat_data = (body or {}).get("data", body) or {}
            stat_list = stat_data.get("statistics_list") or []
            pc = stat_list[0].get("play_count") if stat_list else None
            return int(pc) if isinstance(pc, (int, float)) and pc > 0 else None
        except Exception:  # noqa: BLE001
            return None

    def fetch_batch_douyin_stats(self, aweme_ids: list) -> dict:
        """批量拉取抖音视频播放量（最多 50 条/次·$0.025/次）。

        返回 {aweme_id: play_count}，失败项不含于结果。
        超过 50 时自动分批。
        """
        if not self._key or not aweme_ids:
            return {}
        out: dict = {}
        for i in range(0, len(aweme_ids), _DOUYIN_BATCH_SIZE):
            chunk = aweme_ids[i:i + _DOUYIN_BATCH_SIZE]
            url = (f"{_TIKHUB_BASE}{_DOUYIN_BATCH_STAT_EP}?"
                   f"{urllib.parse.urlencode({'aweme_ids': ','.join(str(x) for x in chunk)})}")
            try:
                req = urllib.request.Request(url, headers={
                    "Authorization": f"Bearer {self._key}",
                    "Accept": "application/json",
                    "User-Agent": "probe/1.0 (+https://metafoclaw.com)",
                })
                with urllib.request.urlopen(req, timeout=30) as resp:
                    body = _json.loads(resp.read().decode("utf-8"))
                items_data = (body or {}).get("data", body) or {}
                # 响应结构：{"statistics_list": [{aweme_id, play_count, ...}]}
                stat_list = items_data.get("statistics_list") or []
                if isinstance(stat_list, list):
                    for item in stat_list:
                        if isinstance(item, dict):
                            aid = item.get("aweme_id")
                            pc = item.get("play_count")
                            if aid and isinstance(pc, int) and pc > 0:
                                out[str(aid)] = pc
                elif isinstance(items_data, list):
                    # 兼容：data 本身是 list
                    for item in items_data:
                        if isinstance(item, dict):
                            aid = item.get("aweme_id")
                            pc = item.get("play_count")
                            if aid and isinstance(pc, int) and pc > 0:
                                out[str(aid)] = pc
            except Exception:  # noqa: BLE001
                continue
        return out

    def cost_hint(self) -> dict[str, float]:
        return {"premium_data": 0.007}             # TikHub ≈ $0.001/req（+$0.001/抖音统计追加）
