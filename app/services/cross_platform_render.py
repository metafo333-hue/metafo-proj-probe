"""跨平台数据组合渲染 · 各平台特性洞察输出（确定性·规则驱动·零 LLM）。

支持平台：bilibili / weibo / kuaishou / xiaohongshu / tiktok
输入：各平台 TikHub 原始响应 dict（或 VideoDataPacket.dimensions 的展开）
输出：各平台专属 markdown 段落

数据来源标注：
  bilibili → yt-dlp 🟩精确值（播放量公开）
  kuaishou → TikHub 🟩（play_count 公开）
  weibo    → TikHub 🟩（转发是核心裂变指标）
  xiaohongshu → TikHub 🟩（收藏是核心转化指标）
  tiktok   → oEmbed(免费) + TikHub(互动)
"""
from __future__ import annotations

from typing import Any


# ──────────────────────────────────────────────────────────────────────────────
# B站 Bilibili
# ──────────────────────────────────────────────────────────────────────────────

def render_bilibili(data: dict[str, Any]) -> str:
    """B站视频特性组合输出。
    data 字段（来自 yt-dlp 或 TikHub）：
      view_count, like_count, comment_count, repost_count, title,
      duration, upload_date, uploader, tags, thumbnail
    """
    view = data.get("view_count") or data.get("play_count") or 0
    like = data.get("like_count") or data.get("digg_count") or 0
    comment = data.get("comment_count") or 0
    repost = data.get("repost_count") or data.get("share_count") or 0
    collect = data.get("collect_count") or 0
    title = data.get("title") or data.get("desc") or ""
    tags = data.get("tags") or []
    duration = data.get("duration") or 0
    uploader = data.get("uploader") or data.get("author_name") or ""
    source = "yt-dlp 🟩精确值" if data.get("_source") == "ytdlp" else "TikHub"

    parts = [f"## B站内容分析（{source}）"]
    if title:
        parts.append(f"**标题**：{title[:80]}")
    if uploader:
        parts.append(f"**UP主**：{uploader}")

    # 核心指标
    parts.append("\n### 传播表现（🟩 B站公开真实数据）")
    if view:
        parts.append(f"播放量 **{view:,}** · 点赞 {like:,} · 评论 {comment:,} · 转发 {repost:,}" +
                     (f" · 收藏 {collect:,}" if collect else ""))

    # 组合：互动率（B站公开播放量才能精确算）
    if view and like:
        like_rate = like / view
        collect_rate = collect / view if collect else None

        parts.append("\n### 互动质量分析")
        rate_icon = "✅" if like_rate > 0.01 else ("🟡" if like_rate > 0.003 else "⚠️")
        rate_desc = "高互动·内容获明确认可" if like_rate > 0.01 else ("正常范围" if like_rate > 0.003 else "互动偏低")
        parts.append(f"互动率（点赞/播放）{rate_icon} **{like_rate:.2%}**（{rate_desc}·行业均值约 0.5%）")

        if collect_rate is not None:
            col_icon = "✅" if collect_rate > 0.02 else ("🟡" if collect_rate > 0.005 else "")
            if col_icon:
                col_desc = "高收藏率·内容有知识/工具价值·用户认为值得二刷" if collect_rate > 0.02 else "正常收藏率"
                parts.append(f"收藏率（收藏/播放）{col_icon} {collect_rate:.2%}（{col_desc}）")

    # 组合：标签 SEO 质量
    if tags:
        tag_count = len(tags) if isinstance(tags, list) else 0
        parts.append("\n### 标签 SEO 诊断")
        tags_str = "、".join(str(t) for t in (tags[:8] if isinstance(tags, list) else []))
        parts.append(f"当前标签（{tag_count}个）：{tags_str}")
        if tag_count > 15:
            parts.append("⚠️ 标签过多（>15）可能稀释权重·建议精选5-10个精准标签")
        elif tag_count < 3:
            parts.append("⚠️ 标签过少（<3）·影响搜索发现·建议补充相关标签")
        else:
            parts.append("✅ 标签数量合适（5-15个）")

    # 时长参考
    if duration:
        dur_min = round(duration / 60, 1)
        if dur_min < 1:
            dur_desc = "极短（<1分钟）·适合信息流但完播率天花板高"
        elif dur_min < 5:
            dur_desc = "短视频（1-5分钟）·B站中等偏短·适合知识速成"
        elif dur_min < 20:
            dur_desc = "中等（5-20分钟）·B站主流时长·适合教程/评测"
        else:
            dur_desc = f"长视频（{dur_min}分钟）·需要强内容撑住完播率"
        parts.append(f"\n**时长诊断** {dur_desc}")

    parts.append("\n---\n*数据来源：yt-dlp（免费·精确）+ TikHub·B站播放量公开真实值*")
    return "\n".join(parts)


# ──────────────────────────────────────────────────────────────────────────────
# 微博 Weibo
# ──────────────────────────────────────────────────────────────────────────────

def render_weibo(data: dict[str, Any]) -> str:
    """微博内容特性组合输出。
    核心：转发是微博独有裂变指标（比点赞更重要）。
    """
    attitudes = (data.get("attitudes_count") or data.get("like_count")
                 or data.get("digg_count") or 0)
    repost = data.get("repost_count") or data.get("share_count") or 0
    comment = data.get("comment_count") or 0
    text = (data.get("text") or data.get("desc") or data.get("title") or "")[:80]
    verified = data.get("verified") or data.get("verification_type")
    verified_reason = data.get("verified_reason") or data.get("enterprise_verify_reason") or ""
    author_fol = (data.get("followers_count") or data.get("author", {}).get("followers_count")
                  or data.get("follower_count") or 0)

    parts = ["## 微博内容分析（TikHub 🟩）"]
    if text:
        parts.append(f"**内容摘要**：{text}")

    # 认证公信力
    if verified or verified_reason:
        cert_type = _weibo_cert_type(verified, verified_reason)
        parts.append(f"**认证**：{cert_type}")

    # 核心组合：传播裂变率（微博最独特指标）
    parts.append("\n### 传播裂变分析（微博专属核心指标）")
    parts.append(f"点赞 {attitudes:,} · 评论 {comment:,} · **转发 {repost:,}**（微博核心扩散指标）")

    if attitudes > 0:
        viral_rate = repost / attitudes
        if viral_rate > 1.0:
            viral_desc = f"🔴 高裂变（{viral_rate:.1f}×）·每个点赞带来超过1次转发·内容触发强分享欲"
        elif viral_rate > 0.3:
            viral_desc = f"✅ 正常传播（{viral_rate:.1f}×）·有一定扩散力"
        elif viral_rate > 0.05:
            viral_desc = f"🟡 扩散力弱（{viral_rate:.1f}×）·以点赞收藏为主·传播链短"
        else:
            viral_desc = f"⚠️ 极低裂变（{viral_rate:.1f}×）·内容缺乏传播动机"
        parts.append(f"**裂变倍率** = 转发/点赞 = **{viral_rate:.2f}×** · {viral_desc}")
        parts.append("💡 微博生态：转发>点赞是高传播内容的特征·与抖音「点赞为主」逻辑不同")

    if author_fol:
        parts.append(f"\n**博主粉丝**：{author_fol:,}")
        if attitudes and author_fol:
            engage = (attitudes + comment + repost) / author_fol
            parts.append(f"综合互动率：{engage:.2%}（{'高' if engage > 0.02 else '正常' if engage > 0.005 else '低'}）")

    parts.append("\n---\n*数据来源：TikHub·微博转发量为核心扩散指标*")
    return "\n".join(parts)


def _weibo_cert_type(verified: Any, reason: str) -> str:
    reason = reason or ""
    if "政府" in reason or "官方" in reason:
        return f"🏛️ 政府/官方账号·{reason}·公信力最高"
    if "媒体" in reason or "传媒" in reason or "新闻" in reason:
        return f"📰 媒体机构·{reason}·内容可信度高"
    if reason:
        return f"🏢 认证账号·{reason}"
    if verified:
        return "✅ 已认证"
    return "未认证"


# ──────────────────────────────────────────────────────────────────────────────
# 快手 Kuaishou
# ──────────────────────────────────────────────────────────────────────────────

def render_kuaishou(data: dict[str, Any]) -> str:
    """快手内容特性组合输出。
    核心：play_count 快手公开真实值（不同于抖音黑盒）。
    """
    play = data.get("play_count") or data.get("view_count") or 0
    like = data.get("digg_count") or data.get("like_count") or 0
    comment = data.get("comment_count") or 0
    share = data.get("share_count") or 0
    reacted = data.get("reacted_count") or 0  # 快手「火苗」互动
    title = data.get("desc") or data.get("title") or ""
    author_fol = (data.get("author", {}).get("fans") or
                  data.get("follower_count") or 0)

    parts = ["## 快手内容分析（TikHub 🟩）"]
    if title:
        parts.append(f"**标题**：{title[:80]}")

    # 核心：播放量展示（区别于抖音）
    parts.append("\n### 传播表现（🟩 快手公开真实数据·不同于抖音黑盒）")
    if play:
        parts.append(f"播放量 **{play:,}**（真实值） · 点赞 {like:,} · 评论 {comment:,} · 转发 {share:,}")
        if reacted:
            parts.append(f"火苗互动 {reacted:,}（快手特有·代表强烈情绪共鸣）")

    # 互动率（可精确计算）
    if play and like:
        rate = like / play
        parts.append(f"\n**互动率** {rate:.2%}（快手平均约 2-5%）"
                     + ("✅" if rate > 0.02 else " ⚠️ 偏低"))

    # 粉丝信息
    if author_fol:
        parts.append(f"**达人粉丝**：{author_fol:,}")
        if like and author_fol:
            parts.append(f"粉丝级互动率：{like/author_fol:.2%}")

    parts.append("\n---\n*数据来源：TikHub·快手播放量为平台公开数据*")
    return "\n".join(parts)


# ──────────────────────────────────────────────────────────────────────────────
# 小红书 Xiaohongshu
# ──────────────────────────────────────────────────────────────────────────────

def render_xiaohongshu(data: dict[str, Any]) -> str:
    """小红书笔记特性组合输出。
    核心：收藏/点赞比是最重要的转化信号（收藏=有购买/实践意向）。
    """
    liked = (data.get("liked_count") or data.get("like_count")
             or data.get("digg_count") or 0)
    collected = (data.get("collected_count") or data.get("collect_count") or 0)
    comment = data.get("comment_count") or 0
    share = data.get("share_count") or 0
    view = data.get("view_count") or data.get("play_count") or 0
    title = data.get("title") or ""
    note_type = data.get("type") or "normal"  # normal=图文/video=视频
    tags = data.get("tag_list") or []
    commerce_tags = [t for t in tags if isinstance(t, dict) and t.get("is_commerce")]
    author_fans = (data.get("author", {}).get("fans") or
                   data.get("fans") or data.get("follower_count") or 0)

    parts = ["## 小红书笔记分析（TikHub 🟩）"]
    if title:
        parts.append(f"**标题**：{title[:80]}")

    # 内容类型诊断
    type_cn = "图文笔记" if note_type == "normal" else "视频笔记"
    type_note = "小红书原生优势格式·搜索权重更高" if note_type == "normal" else "视频格式·需要更强的完播率支撑"
    parts.append(f"**内容类型**：{type_cn}（{type_note}）")

    # 核心组合：收藏/点赞比（小红书最重要指标）
    parts.append("\n### 互动质量（🟩 公开数据）")
    parts.append(f"点赞 {liked:,} · **收藏 {collected:,}**（核心指标） · 评论 {comment:,} · 分享 {share:,}")

    if liked > 0:
        col_ratio = collected / liked
        if col_ratio > 0.3:
            col_desc = f"🟩 高收藏率 {col_ratio:.0%}·内容有实用价值·用户有囤货/实践意向·转化潜力强"
        elif col_ratio > 0.1:
            col_desc = f"✅ 正常收藏率 {col_ratio:.0%}·内容有参考价值"
        else:
            col_desc = f"⚠️ 低收藏率 {col_ratio:.0%}·娱乐型内容为主·带货转化率偏低"
        parts.append(f"**收藏/点赞比** = {col_ratio:.0%} · {col_desc}")
        parts.append("💡 小红书特点：收藏=用户认为「值得实践/购买」·远比点赞更有价值")

    # 话题 SEO 质量
    if tags:
        tag_names = [t.get("name") or t if isinstance(t, dict) else str(t) for t in tags[:10]]
        parts.append(f"\n**话题标签**（{len(tags)}个）：{'、'.join(tag_names[:8])}")
        if len(tags) > 15:
            parts.append("⚠️ 标签过多·小红书算法对标签堆砌不友好·精选5个精准标签优于20个泛标签")
        elif len(tags) < 3:
            parts.append("⚠️ 标签过少·影响搜索发现")
        if commerce_tags:
            ct_names = [t.get("name") if isinstance(t, dict) else str(t) for t in commerce_tags]
            parts.append(f"🏷️ 商业话题：{'、'.join(ct_names)}（商业话题可获得品牌流量加持）")

    # 粉丝信息
    if author_fans:
        parts.append(f"\n**博主粉丝**：{author_fans:,}")

    parts.append("\n---\n*数据来源：TikHub·小红书收藏量为最重要的转化信号*")
    return "\n".join(parts)


# ──────────────────────────────────────────────────────────────────────────────
# TikTok
# ──────────────────────────────────────────────────────────────────────────────

def render_tiktok(data: dict[str, Any]) -> str:
    """TikTok 内容特性组合输出。
    两路数据：oEmbed（免费·仅元数据）+ TikHub（付费·含互动）。
    核心：play_count TikTok 公开真实值（不同于抖音）。
    """
    # 判断数据源
    has_interaction = bool(data.get("digg_count") or data.get("play_count"))

    title = data.get("title") or ""
    author = data.get("author_name") or data.get("author", {}).get("nickname") or ""
    thumbnail = data.get("thumbnail_url") or ""
    play = data.get("play_count") or data.get("view_count") or 0
    like = data.get("digg_count") or data.get("like_count") or 0
    comment = data.get("comment_count") or 0
    share = data.get("share_count") or 0

    # 封面格式判断（oEmbed 返回宽高）
    tw = data.get("thumbnail_width") or 0
    th = data.get("thumbnail_height") or 0
    if tw and th:
        ratio = tw / th
        fmt = "竖屏 9:16 ✅（TikTok 最佳格式）" if ratio < 0.7 else (
              "正方形" if 0.9 < ratio < 1.1 else "横屏 ⚠️（建议转为竖屏）")
    else:
        fmt = None

    parts = ["## TikTok 内容分析"]
    if title:
        parts.append(f"**标题**：{title[:80]}")
    if author:
        parts.append(f"**作者**：@{author}")
    if fmt:
        parts.append(f"**内容格式**：{fmt}")

    if has_interaction:
        parts.append(f"\n### 传播表现（🟩 TikTok 公开真实数据）")
        parts.append(f"播放量 **{play:,}**（真实值·不同于抖音黑盒） · 点赞 {like:,} · 评论 {comment:,} · 转发 {share:,}")

        if play and like:
            rate = (like + comment + share) / play
            rate_desc = "高互动" if rate > 0.05 else ("正常" if rate > 0.02 else "偏低")
            parts.append(f"互动率（赞+评+转/播）{rate:.2%}（{rate_desc}·TikTok 行业均值约 3-5%）")
    else:
        parts.append(f"\n### 内容元数据（免费 oEmbed 数据）")
        parts.append("互动数据需付费采集·当前仅元数据")
        if thumbnail:
            parts.append(f"封面图：{thumbnail[:80]}")

    parts.append("\n---\n*数据来源：TikTok oEmbed（免费）+ TikHub（互动·付费）*")
    return "\n".join(parts)


# ──────────────────────────────────────────────────────────────────────────────
# 路由入口
# ──────────────────────────────────────────────────────────────────────────────

def render_wechat_channels(data: dict[str, Any]) -> str:
    """微信视频号内容特性输出（JZL 数据·确定性·规则驱动）。

    data 字段（来自 JZLChannelsAdapter.fetch_metadata）：
      title, nickname, v2_name, like_count, comment_count, collect_count, share_count,
      fans（仅公众号绑定账号可取）, play_count（永久缺口·平台不公开）
    """
    title = data.get("title") or data.get("desc") or ""
    nickname = data.get("nickname") or data.get("author") or ""
    v2 = data.get("v2_name") or ""
    like = data.get("like_count") or data.get("digg_count") or 0
    comment = data.get("comment_count") or 0
    collect = data.get("collect_count") or 0
    share = data.get("share_count") or 0
    fans = data.get("fans") or data.get("follower_count")
    source = "JZL 极致了·付费" if data.get("_source") == "jzl" else "JZL"

    parts = [f"## 微信视频号内容分析（{source}）"]
    if title:
        parts.append(f"**标题**：{title[:100]}")
    if nickname:
        parts.append(f"**账号**：{nickname}" + (f"（{v2}）" if v2 else ""))

    parts.append("\n### 互动表现")
    metrics = []
    if like:
        metrics.append(f"点赞 **{like:,}**")
    if comment:
        metrics.append(f"评论 {comment:,}")
    if collect:
        metrics.append(f"收藏 {collect:,}")
    if share:
        metrics.append(f"转发 {share:,}")
    if metrics:
        parts.append(" · ".join(metrics))
    else:
        parts.append("互动数据暂未获取")

    if fans:
        parts.append(f"\n**账号粉丝**：{fans:,}")

    parts.append("\n### 播放量说明")
    parts.append("⚠️ **播放量**：微信视频号平台侧永久不公开，任何第三方 API 均无法获取，此为平台架构性缺口。")

    if like and comment:
        comment_rate = comment / like if like > 0 else 0
        quality = "互动质量高·观众参与深" if comment_rate > 0.05 else (
            "正常范围" if comment_rate > 0.01 else "评论偏少·轻互动内容")
        parts.append(f"\n**评论/点赞比**：{comment_rate:.2%}（{quality}）")

    parts.append("\n---\n*数据来源：JZL 极致了数据（付费·微信视频号 13 字段·¥0.2/页）*")
    return "\n".join(parts)


_RENDERERS = {
    "bilibili": render_bilibili,
    "weibo": render_weibo,
    "kuaishou": render_kuaishou,
    "xiaohongshu": render_xiaohongshu,
    "tiktok": render_tiktok,
    "wechat_channels": render_wechat_channels,
}


def render_platform(platform: str, data: dict[str, Any]) -> str | None:
    """平台路由入口：platform → 专属渲染输出（无匹配返回 None）。"""
    fn = _RENDERERS.get(platform.lower())
    if not fn:
        return None
    try:
        return fn(data)
    except Exception as e:
        return f"## {platform} 数据解析异常\n{type(e).__name__}: {str(e)[:200]}"
