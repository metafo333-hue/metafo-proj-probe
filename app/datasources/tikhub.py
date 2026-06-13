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
"""
from __future__ import annotations

import os
import re
from typing import Any

from app.datasources.base import DataSourceAdapter


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
        try:
            if plat == "xiaohongshu":
                raw = c.xiaohongshu_web.get_note_info_v2(share_text=url)
            else:  # douyin / bilibili / kuaishou / weibo → 通用解析
                raw = c.hybrid_parsing.video_data(url=url)
        except Exception as e:
            return {"_error": f"{type(e).__name__}: {str(e)[:160]}"}
        return self._normalize(raw, plat, url)

    # 互动指标在各平台返回里的常见嵌套位置（抖音=statistics·小红书=interact_info 等）
    _STAT_NESTS = ("statistics", "stats", "interact_info", "interactive_info")
    _METRIC_KEYS = ("digg_count", "like_count", "comment_count", "share_count",
                    "collect_count", "play_count", "recommend_count",
                    "admire_count", "download_count", "forward_count")

    def _normalize(self, raw: Any, plat: str, url: str) -> dict[str, Any]:
        """第三方原始数据 → 标准化元数据（原料进结论出：只取元数据，不直吐全量原文）。

        互动指标各平台位置不同（抖音在 data.statistics·小红书在 interact_info 等），
        统一在常见嵌套位置探测，回退顶层；2026-06-13 实测抖音 statistics 校准。
        """
        data = raw.get("data", raw) if isinstance(raw, dict) else {}
        if not isinstance(data, dict):
            data = {}
        stat = {}
        for key in self._STAT_NESTS:
            v = data.get(key)
            if isinstance(v, dict):
                stat = v
                break
        src = {**data, **stat}                     # 嵌套指标优先于顶层同名
        title = (data.get("desc") or data.get("title") or data.get("item_title")
                 or data.get("content") or data.get("caption") or "")
        if not isinstance(title, str):
            title = str(title)
        metrics = {k: src[k] for k in self._METRIC_KEYS
                   if isinstance(src.get(k), (int, float))}
        return {
            "title": title[:200],
            "text": title,                         # 标准化元数据（标题/简介），非原始全文
            "platform": plat,
            "metadata": metrics,
            "source_id": self.source_id,
        }

    def cost_hint(self) -> dict[str, float]:
        return {"premium_data": 0.007}             # TikHub ≈ $0.001/req
