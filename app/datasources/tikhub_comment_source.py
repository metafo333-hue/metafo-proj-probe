"""TikHub 评论数据源 · 实现 comment_insight.CommentSource 接口(安全·合规·可插拔)。

定位:为 comment_insight 提供**合法持牌源**(TikHub·已裁定保留付费·公开评论数据)的评论。
商业链只持接口(CommentSource Protocol),本适配器是其一个实现;真正的灰色/个人侧通路
另走 register_source 隔离注册点(不在商业链自建抓取·中性指针)。

安全/合规设计(对应元东方"安全接好"):
- **凭据**:key 仅从 env 读(TIKHUB_API_KEY/PROBE_TIKHUB_KEY)·不硬编码·不入日志
- **限量**:默认最多取 limit 条(分页上限 _MAX_PAGES)·控成本与数据量
- **PIPL**:归一化**不留存个体昵称**(user_label 只取 ip 归属地这类粗粒度·个体可识别信息丢弃)
- **数据不出境**:评论文本下游只喂国产 LLM(comment_insight·model_router comment 档)
- **降级**:任何异常/无 key/无数据 → 返回 None·绝不阻塞主报告
- **端点可配**:TIKHUB_COMMENT_ENDPOINT env 覆盖(防 TikHub 端点变更需改码)

用法(account_chain):
    src = TikHubCommentSource(key)
    comments = comment_insight.load_comments(src, aweme_id)
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# TikHub 抖音评论端点(可 env 覆盖·默认 web 版评论列表)
_ENDPOINT = os.getenv("TIKHUB_COMMENT_ENDPOINT",
                      "/api/v1/douyin/web/fetch_video_comments")
_MAX_PAGES = 5          # 分页上限(防 runaway·5 页≈100 条够洞察)
_PAGE_SIZE = 50


def _norm(c: dict[str, Any]) -> dict[str, Any] | None:
    """TikHub 评论 dict → 归一化 {text,like,reply_count,create_time,user_label}。
    PIPL:不取昵称/uid 等个体可识别信息;user_label 只取 ip 归属地(粗粒度)。"""
    text = (c.get("text") or c.get("content") or "").strip()
    if not text:
        return None
    # ip 归属地(粗粒度地域·非个体身份)·不同字段名兼容
    ip = (c.get("ip_label") or c.get("ip_location")
          or (c.get("user") or {}).get("ip_location") or "") or None
    return {
        "text": text,
        "like": int(c.get("digg_count") or c.get("like_count") or 0),
        "reply_count": int(c.get("reply_comment_total")
                           or c.get("reply_count") or 0),
        "create_time": c.get("create_time") or None,
        "user_label": ip,          # 仅地域·无个体身份(PIPL)
    }


class TikHubCommentSource:
    """CommentSource 实现:走 TikHub 持牌 API 取抖音公开评论。"""

    def __init__(self, key: str | None = None,
                 endpoint: str | None = None) -> None:
        # 凭据只从入参/env·不硬编码
        self._key = key or os.getenv("TIKHUB_API_KEY") or os.getenv("PROBE_TIKHUB_KEY")
        self._endpoint = endpoint or _ENDPOINT

    def fetch(self, aweme_id: str, limit: int = 200) -> list[dict] | None:
        """取评论(分页·限量·归一化·失败 None)。商业链不自建抓取——走 TikHub 持牌 API。"""
        if not self._key or not aweme_id:
            return None
        try:
            # 懒导入:combo_deep_probe 仅生产环境可用(与 account_chain 一致)
            from combo_deep_probe.adapters.tikhub_adapter import tikhub_get
        except Exception as e:  # noqa: BLE001
            logger.warning("TikHub adapter 不可用·评论源降级: %s", type(e).__name__)
            return None

        out: list[dict] = []
        cursor = 0
        for _ in range(_MAX_PAGES):
            if len(out) >= limit:
                break
            try:
                raw = tikhub_get(self._endpoint,
                                 {"aweme_id": aweme_id, "cursor": cursor,
                                  "count": _PAGE_SIZE}, self._key)
            except Exception as e:  # noqa: BLE001
                logger.warning("TikHub 评论调用失败·降级: %s", type(e).__name__)
                break
            data = (raw or {}).get("data") or raw or {}
            items = (data.get("comments") or data.get("comment_list")
                     or data.get("aweme_comments") or [])
            if not items:
                break
            for c in items:
                n = _norm(c) if isinstance(c, dict) else None
                if n:
                    out.append(n)
            # 翻页
            has_more = data.get("has_more")
            cursor = data.get("cursor") or (cursor + _PAGE_SIZE)
            if not has_more:
                break
        return out[:limit] or None
