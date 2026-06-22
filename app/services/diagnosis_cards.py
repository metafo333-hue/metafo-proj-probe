"""章三组合诊断地图 · P1/P3/P4/P6 四张高价值诊断卡

每个函数:
  输入 → account dict (来自 account_chain.run_from_video_url 的 account 字段)
          xprof    (可选, XingtuProfile 对象或 dict, 来自 xingtu_profile.fetch_xingtu_profile)
  输出 → 诊断结论 dict {status, severity, advice, ...卡片专属字段}

阈值标注: ⚠️经验值待校准 — 上线前跑 50-100 真实账号建分位基线后替换为实测值。
"""
from __future__ import annotations

from typing import Any


# ──────────────────────────────────────────────────────────────────────────────
# 内部工具
# ──────────────────────────────────────────────────────────────────────────────

def _safe(d: dict | None, *keys, default=None):
    """深层安全取值。"""
    if not isinstance(d, dict):
        return default
    v = d
    for k in keys:
        if not isinstance(v, dict):
            return default
        v = v.get(k, default)
    return v


def _xprof_attr(xprof, attr: str, default=None):
    """兼容 XingtuProfile 对象和 dict 的属性取值。"""
    if xprof is None:
        return default
    if isinstance(xprof, dict):
        return xprof.get(attr, default)
    return getattr(xprof, attr, default)


# ──────────────────────────────────────────────────────────────────────────────
# P1 · 掉粉诊断
# ──────────────────────────────────────────────────────────────────────────────

def diagnose_churn(account: dict[str, Any]) -> dict[str, Any]:
    """P1 掉粉诊断卡 · 链路组合: follower_drawdown + engagement_structure。

    返回字段:
      status: "heavy_churn" | "light_churn" | "normal"
      severity: "red" | "yellow" | "green"
      drawdown_pct: float | None   (已计算的掉粉百分比)
      root_cause: str              (主要根因判断)
      advice: str                  (处方)
    """
    # ── 取字段 ──
    fd = account.get("follower_drawdown") or {}
    if isinstance(fd, (int, float)):
        drawdown_pct = float(fd)
        drawdown_note = None
    elif isinstance(fd, dict):
        drawdown_pct = fd.get("drawdown_pct") or fd.get("pct") or fd.get("value")
        drawdown_pct = float(drawdown_pct) if drawdown_pct is not None else None
        drawdown_note = fd.get("note") or fd.get("label")
    else:
        drawdown_pct = None
        drawdown_note = None

    # 尝试自算 (有 max_follower + follower 时)
    if drawdown_pct is None:
        follower = account.get("follower") or 0
        max_follower = account.get("max_follower") or 0
        if max_follower > 0 and follower >= 0:
            drawdown_pct = (max_follower - follower) / max_follower * 100

    # 互动结构辅助 (若有 engagement_structure 则补充根因)
    es = account.get("engagement_structure") or {}
    if isinstance(es, str):
        es_label = es
    elif isinstance(es, dict):
        es_label = es.get("label") or es.get("type") or ""
    else:
        es_label = ""

    # ── 判据 (⚠️经验值待校准) ──
    if drawdown_pct is None:
        status, severity = "unknown", "gray"
        root_cause = "无法获取历史峰值粉丝数·掉粉率未知"
        advice = "建议确认账号是否开通星图·否则无法获取 max_follower_count 字段"
    elif drawdown_pct >= 15:
        status, severity = "heavy_churn", "red"
        root_cause = f"账号掉粉 {drawdown_pct:.1f}%·超过重度预警线 15%（⚠️经验值待校准）"
        if "断更" in es_label or "inactive" in es_label.lower():
            root_cause += "·主因：更新断档导致算法降权"
            advice = "立即恢复更新，哪怕降低制作质量；设每日发布提醒；连发 3 条最高互动类型内容修复分发信号"
        elif "争议" in es_label or "negative" in es_label.lower():
            root_cause += "·主因：争议内容引发粉丝流失"
            advice = "下架或关闭争议视频评论；发同系列正面内容修复信号；排查最近内容风格偏移"
        else:
            root_cause += "·可能原因：内容方向跑偏或分发规模萎缩"
            advice = "对比历史高互动作品，找风格差异；连发 3 条最高互动类型内容测试；提高 vertical_score（收窄标签至 1-2 个核心话题）"
    elif drawdown_pct >= 5:
        status, severity = "light_churn", "yellow"
        root_cause = f"账号轻度掉粉 {drawdown_pct:.1f}%（5-15% 轻警区间·⚠️经验值待校准）"
        advice = "观察 2 周内容互动趋势；主动互动同赛道评论区；检查内容节奏是否有断档"
    else:
        status, severity = "normal", "green"
        root_cause = f"粉丝波动 {drawdown_pct:.1f}%·正常区间（<5%·⚠️经验值待校准）"
        advice = "保持当前内容频率；专注提高互动率以突破下一增长平台期"

    return {
        "card": "P1",
        "title": "掉粉诊断",
        "status": status,
        "severity": severity,
        "drawdown_pct": round(drawdown_pct, 2) if drawdown_pct is not None else None,
        "drawdown_note": drawdown_note,
        "engagement_structure": es_label,
        "root_cause": root_cause,
        "advice": advice,
    }


# ──────────────────────────────────────────────────────────────────────────────
# P3 · 报价合理性诊断
# ──────────────────────────────────────────────────────────────────────────────

def diagnose_pricing(account: dict[str, Any], xprof=None) -> dict[str, Any]:
    """P3 报价合理性诊断卡 · 非关联三源交叉。

    优先用 xprof 星图数据 (link_shopping_index / price_info / expect_vv)；
    无 xprof 时用粉丝 × 均播估算兜底。

    返回字段:
      status: "fair" | "high" | "low" | "no_xingtu" | "unknown"
      severity: "green" | "yellow" | "red" | "gray"
      star_price_yuan: float | None    (星图定价·元·1-20s 视频)
      actual_cpm: float | None         (实际 CPM·元/千次)
      vv_deviation_pct: float | None   (预期播放 vs 实际偏差%)
      estimated_price_yuan: float | None (粉丝估算报价·无星图时)
      advice: str
    """
    # ── 从 xprof 取星图数据 ──
    star_price_yuan = None
    expected_vv = None
    link_shopping_avg = None

    if xprof is not None:
        # XingtuProfile 对象或 dict 兼容
        pi = _xprof_attr(xprof, "price_info") or []
        if isinstance(pi, list):
            for p in pi:
                vtype = (p.get("video_type") if isinstance(p, dict) else getattr(p, "video_type", None))
                if vtype == 1:  # 1-20s 视频类型
                    raw_price = (p.get("price") if isinstance(p, dict) else getattr(p, "price", None))
                    if raw_price:
                        star_price_yuan = raw_price / 100  # 分→元

        ev = _xprof_attr(xprof, "expect_vv") or {}
        if isinstance(ev, dict):
            expected_vv = ev.get("value")
        elif isinstance(ev, (int, float)):
            expected_vv = ev

        lsi = _xprof_attr(xprof, "link_shopping_index") or {}
        if isinstance(lsi, dict):
            link_shopping_avg = lsi.get("avg_value")
        else:
            link_shopping_avg = _xprof_attr(xprof, "link_shopping_index_avg")

    # ── 实际均播 ──
    avg_like = account.get("avg_like") or 0
    # 均播暂用 avg_like 代理（avg_play 字段若不存在则退化）
    actual_avg_play = account.get("avg_play") or avg_like or 0

    follower = account.get("follower") or 0

    # ── 有星图数据路径 ──
    if star_price_yuan is not None:
        actual_cpm = (star_price_yuan / actual_avg_play * 1000) if actual_avg_play > 0 else None

        vv_deviation_pct = None
        if expected_vv and actual_avg_play > 0:
            vv_deviation_pct = abs(expected_vv - actual_avg_play) / actual_avg_play * 100

        # 判据 (⚠️经验值待校准: CPM 行业均值 5-15 元/千次)
        issues = []
        if vv_deviation_pct is not None and vv_deviation_pct > 50:
            issues.append(f"预期播放 vs 实际偏差 {vv_deviation_pct:.0f}%（>50% 阈值·疑似数据虚高）")
        if actual_cpm is not None and actual_cpm > 15:
            issues.append(f"实际 CPM {actual_cpm:.1f} 元/千次（>15 元行业偏贵·⚠️经验值待校准）")

        if issues:
            status, severity = "high", "red"
            advice = "；".join(issues) + "。建议谨慎合作或要求效果保量条款，可将偏差数据直接发给对方砍价依据"
        elif actual_cpm is not None and actual_cpm < 5:
            status, severity = "low", "green"
            advice = f"CPM 约 {actual_cpm:.1f} 元/千次，低于行业均值 5 元（⚠️经验值待校准），性价比高。可参考星图定价，或上浮 10-20%"
        else:
            status, severity = "fair", "green"
            advice = f"星图定价 {star_price_yuan:.0f} 元（1-20s 视频），CPM {'%.1f' % actual_cpm if actual_cpm else '未知'} 元/千次，处于行业正常水平（5-15 元·⚠️经验值待校准）"

        return {
            "card": "P3",
            "title": "报价合理性诊断",
            "status": status,
            "severity": severity,
            "star_price_yuan": star_price_yuan,
            "actual_cpm": round(actual_cpm, 2) if actual_cpm else None,
            "vv_deviation_pct": round(vv_deviation_pct, 1) if vv_deviation_pct else None,
            "expected_vv": expected_vv,
            "actual_avg_play": actual_avg_play,
            "link_shopping_avg": link_shopping_avg,
            "estimated_price_yuan": None,
            "advice": advice,
        }

    # ── 无星图兜底：粉丝 × 均播估算 ──
    # 估算公式：actual_avg_play × 行业 CPM 均值 8 元/千次 (⚠️经验值待校准)
    INDUSTRY_CPM = 8.0  # 元/千次·⚠️经验值待校准
    estimated_price_yuan = None
    if actual_avg_play > 0:
        estimated_price_yuan = round(actual_avg_play * INDUSTRY_CPM / 1000, 0)
    elif follower > 0:
        # 粉丝估算兜底：100 万粉约 1000 元报价（经验线·⚠️经验值待校准）
        estimated_price_yuan = round(follower / 1000, 0)

    advice_parts = []
    if estimated_price_yuan:
        advice_parts.append(f"无星图数据·按均播 {actual_avg_play} × 行业 CPM {INDUSTRY_CPM} 元/千次估算，1-20s 视频合理报价约 {estimated_price_yuan:.0f} 元（⚠️行业 CPM 经验值待校准）")
    advice_parts.append("建议开通星图获取官方报价数据以提高诊断准确度")

    return {
        "card": "P3",
        "title": "报价合理性诊断",
        "status": "no_xingtu",
        "severity": "gray",
        "star_price_yuan": None,
        "actual_cpm": None,
        "vv_deviation_pct": None,
        "expected_vv": None,
        "actual_avg_play": actual_avg_play,
        "link_shopping_avg": link_shopping_avg,
        "estimated_price_yuan": estimated_price_yuan,
        "advice": "；".join(advice_parts),
    }


# ──────────────────────────────────────────────────────────────────────────────
# P6 · 转化漏斗诊断
# ──────────────────────────────────────────────────────────────────────────────

def diagnose_funnel(account: dict[str, Any]) -> dict[str, Any]:
    """P6 转化漏斗诊断卡 · 链路组合: 互动结构 + 商业密度 + 橱窗状态。

    漏斗四层:
      L1 流量基础 (avg_like / avg_play 代理)
      L2 橱窗开通 (with_commerce_entry)
      L3 商业密度 (commerce_density)
      L4 带货能力 (link_shopping_index via xprof 或 account 预留字段)

    意图信号强弱排序: 点赞 < 收藏 < 转发 < 关注 (章三 P6 公式)

    返回字段:
      funnel_bottleneck: "L1_traffic" | "L2_no_entry" | "L3_low_density" | "L4_low_convert" | "healthy"
      severity: "red" | "yellow" | "green"
      commerce_density_pct: float | None
      intent_tier: str   (意图信号评级)
      bottleneck_desc: str
      advice: str
    """
    # ── L1 流量 ──
    avg_play = account.get("avg_play") or account.get("avg_like") or 0
    L1_ok = avg_play >= 5000  # ⚠️经验值待校准

    # ── L2 橱窗 ──
    with_commerce = account.get("with_commerce_entry")
    L2_ok = bool(with_commerce)

    # ── L3 商业密度 ──
    cd = account.get("commerce_density")
    if isinstance(cd, dict):
        commerce_density_pct = (cd.get("ratio") or cd.get("pct") or cd.get("value") or 0) * 100
    elif isinstance(cd, (int, float)):
        # 如果是 0-1 小数则 ×100；如果是已经是百分比则直接用
        commerce_density_pct = float(cd) * 100 if cd <= 1.0 else float(cd)
    else:
        commerce_density_pct = None

    L3_ok = (commerce_density_pct is not None and commerce_density_pct >= 10)  # ⚠️经验值待校准

    # ── 互动结构意图评分 ──
    es = account.get("engagement_structure") or {}
    if isinstance(es, dict):
        collect = es.get("collect_rate") or es.get("collect") or 0
        share = es.get("share_rate") or es.get("share") or 0
        # 简化意图评分: 收藏×0.5 + 转发×0.3 (⚠️经验值待校准)
        intent_score = collect * 0.5 + share * 0.3
        if intent_score > 0.015:
            intent_tier = "高意图（收藏+转发信号强）"
        elif intent_score > 0.005:
            intent_tier = "中意图"
        else:
            intent_tier = "低意图（点赞为主·商业转化弱）"
    elif isinstance(es, str):
        intent_tier = es if es else "互动结构数据不足"
        intent_score = 0
    else:
        intent_tier = "互动结构数据不足"
        intent_score = 0

    # ── 漏斗堵点判断 ──
    if not L1_ok:
        bottleneck = "L1_traffic"
        severity = "red"
        desc = f"流量基础不足（均播/均赞约 {avg_play}，<5000 阈值·⚠️经验值待校准）·变现前提未达"
        advice = "先解决内容质量问题（参照 P1 掉粉诊断·P2 爆款分析）；带货在流量起量后效率更高"
    elif not L2_ok:
        bottleneck = "L2_no_entry"
        severity = "red"
        desc = "橱窗/带货入口未开通·流量进来等于空店"
        advice = "抖音 APP → 创作者服务中心 → 开通橱窗（≥1000 粉丝或完成实名）；主页简介加购买引导语"
    elif not L3_ok:
        bottleneck = "L3_low_density"
        severity = "yellow"
        density_str = f"{commerce_density_pct:.1f}%" if commerce_density_pct is not None else "未知"
        desc = f"商业密度 {density_str} < 10%（⚠️经验值待校准）·每 10 条内容不到 1 条挂品"
        advice = "排期计划：每 3-5 条日常内容配 1 条带货内容；主页置顶一条带货视频；逐步提升至 20-40% 健康密度"
    else:
        bottleneck = "healthy"
        severity = "green"
        density_str = f"{commerce_density_pct:.1f}%" if commerce_density_pct is not None else "未知"
        desc = f"转化漏斗各层健康（流量·橱窗·商业密度 {density_str}）"
        advice = "维持当前密度；提升内容结构：痛点场景（15s）→ 产品解法（20s）→ 价格优惠（10s）→ 催单（5s）"

    # 过度商业化警告
    over_commercial_warn = None
    if commerce_density_pct is not None and commerce_density_pct > 60:
        over_commercial_warn = f"商业密度 {commerce_density_pct:.1f}% > 60%（⚠️经验值待校准），过度带货可能影响粉丝黏性·建议控制在 40% 以下"

    return {
        "card": "P6",
        "title": "转化漏斗诊断",
        "funnel_bottleneck": bottleneck,
        "severity": severity,
        "avg_play_proxy": avg_play,
        "L1_traffic_ok": L1_ok,
        "L2_commerce_entry_ok": L2_ok,
        "L3_density_ok": L3_ok,
        "commerce_density_pct": round(commerce_density_pct, 1) if commerce_density_pct is not None else None,
        "intent_tier": intent_tier,
        "bottleneck_desc": desc,
        "over_commercial_warn": over_commercial_warn,
        "advice": advice,
    }


# ──────────────────────────────────────────────────────────────────────────────
# P4 · 赛道定位诊断
# ──────────────────────────────────────────────────────────────────────────────

def diagnose_track(account: dict[str, Any], xprof=None) -> dict[str, Any]:
    """P4 赛道定位诊断卡 · 关联组合: vertical_score × link_shopping_index × industry_tags。

    三轴定位:
      自身定位轴: vertical_score (标签集中度)
      赛道商业轴: link_shopping_index.avg_value (0-100分·带货能力)
      行业分位轴: link_shopping_index.rank_percent (越小越靠前)

    赛道价值五档 (⚠️经验值待校准):
      S档: avg_value>70 + rank<2%
      A档: avg_value 60-70 + rank<10%
      B档: avg_value 40-60
      C档: avg_value<40
      D档: 无星图数据

    返回字段:
      vertical_tier: "clear" | "fuzzy" | "chaotic"
      commercial_tier: "S" | "A" | "B" | "C" | "D"
      vertical_score: float | None
      link_shopping_avg: float | None
      link_shopping_rank_pct: float | None
      industry_tags: list[str]
      prescription: str
      advice: str
    """
    # ── 垂直度 ──
    vs = account.get("vertical_score")
    vertical_score = float(vs) if vs is not None else None

    if vertical_score is None:
        vertical_tier = "unknown"
        vertical_desc = "垂直度未知（缺 vertical_score 字段）"
    elif vertical_score >= 0.6:
        vertical_tier = "clear"
        vertical_desc = f"定位清晰（vertical_score={vertical_score:.2f}·≥0.6·算法易分类·⚠️经验值待校准）"
    elif vertical_score >= 0.3:
        vertical_tier = "fuzzy"
        vertical_desc = f"定位模糊（vertical_score={vertical_score:.2f}·0.3-0.6·需聚焦·⚠️经验值待校准）"
    else:
        vertical_tier = "chaotic"
        vertical_desc = f"定位混乱（vertical_score={vertical_score:.2f}·<0.3·泛内容账号·⚠️经验值待校准）"

    # ── 带货商业轴 (优先 xprof·次选 account 内置字段) ──
    link_shopping_avg = None
    link_shopping_rank_pct = None

    if xprof is not None:
        lsi = _xprof_attr(xprof, "link_shopping_index") or {}
        if isinstance(lsi, dict):
            link_shopping_avg = lsi.get("avg_value")
            link_shopping_rank_pct = lsi.get("rank_percent")

    # account 内部可能已有 (未来扩展路径)
    if link_shopping_avg is None:
        link_shopping_avg = account.get("link_shopping_avg") or account.get("link_shopping_index_avg")
    if link_shopping_rank_pct is None:
        link_shopping_rank_pct = account.get("link_shopping_rank_pct")

    # ── 行业标签 ──
    industry_tags: list[str] = []
    if xprof is not None:
        it = _xprof_attr(xprof, "industry_tag") or _xprof_attr(xprof, "industry_tags") or []
        if isinstance(it, list):
            industry_tags = [str(t) for t in it if t]
        elif isinstance(it, str) and it:
            industry_tags = [it]
    if not industry_tags:
        industry_tags = account.get("hashtags") or account.get("platform_tags") or []

    # ── 商业价值档 (⚠️经验值待校准) ──
    if link_shopping_avg is None:
        commercial_tier = "D"
        commercial_desc = "无星图带货数据（未开通星图或未取到）·⚠️无法判断商业价值档"
    elif link_shopping_avg > 70 and (link_shopping_rank_pct or 1.0) < 0.02:
        commercial_tier = "S"
        commercial_desc = f"S档（顶级·带货指数 {link_shopping_avg:.1f}/100·行业前 {(link_shopping_rank_pct or 0)*100:.1f}%·⚠️经验值待校准）"
    elif link_shopping_avg >= 60 and (link_shopping_rank_pct or 1.0) < 0.10:
        commercial_tier = "A"
        commercial_desc = f"A档（高价值·带货指数 {link_shopping_avg:.1f}/100·行业前 {(link_shopping_rank_pct or 0)*100:.1f}%·⚠️经验值待校准）"
    elif link_shopping_avg >= 40:
        commercial_tier = "B"
        commercial_desc = f"B档（中等·带货指数 {link_shopping_avg:.1f}/100·⚠️经验值待校准）"
    else:
        commercial_tier = "C"
        commercial_desc = f"C档（低·带货指数 {link_shopping_avg:.1f}/100·纯流量无清晰变现路径·⚠️经验值待校准）"

    # ── 处方 ──
    if vertical_tier == "chaotic" and commercial_tier in ("C", "D"):
        prescription = "双低危险区：选 1 个细分赛道押注，连发 20 条聚焦内容重塑算法标签"
        advice = "不要同时换赛道+换风格，先聚焦赛道标签；评估向相邻高价值赛道迁移成本"
    elif vertical_tier == "clear" and commercial_tier in ("S", "A"):
        prescription = "黄金组合：定位清晰且赛道高商业价值，加大内容频次扩大商业合作"
        advice = "建立系列化内容模板；主动对接品牌方或开通星图接单；提升带货视频比例"
    elif vertical_tier in ("fuzzy", "chaotic"):
        prescription = "聚焦标签：回看历史播放最高 20 条，提取共同话题作为唯一主标签"
        advice = "每周只发 1-2 个话题下的内容；3 个月后重新评估 vertical_score"
    elif commercial_tier in ("C", "D"):
        prescription = "赛道商业价值偏低：评估向相邻高价值赛道迁移（如搞笑→生活分享→带货）"
        advice = "不要贸然换大赛道；先在当前赛道找细分切口，找到有商业价值的子话题"
    else:
        prescription = "当前定位基本健康"
        advice = "持续深耕细分赛道；关注 link_shopping_index 趋势，避免商业价值滑落"

    return {
        "card": "P4",
        "title": "赛道定位诊断",
        "vertical_tier": vertical_tier,
        "vertical_desc": vertical_desc,
        "commercial_tier": commercial_tier,
        "commercial_desc": commercial_desc,
        "vertical_score": vertical_score,
        "link_shopping_avg": link_shopping_avg,
        "link_shopping_rank_pct": link_shopping_rank_pct,
        "industry_tags": industry_tags,
        "prescription": prescription,
        "advice": advice,
    }


# ──────────────────────────────────────────────────────────────────────────────
# 报告段渲染器
# ──────────────────────────────────────────────────────────────────────────────

_SEVERITY_EMOJI = {
    "red": "🔴",
    "yellow": "🟡",
    "green": "🟢",
    "gray": "⚪",
}


def render_diagnosis_section(account: dict[str, Any], xprof=None) -> str:
    """串联 P1/P3/P6/P4 四卡 → 报告段 Markdown。

    各卡独立降级：单卡异常不影响其他卡输出。
    """
    sections: list[str] = ["## 🔍 章三组合诊断（P1·P3·P6·P4）\n"]

    # P1
    try:
        p1 = diagnose_churn(account)
        emoji = _SEVERITY_EMOJI.get(p1["severity"], "⚪")
        sections.append(
            f"### {emoji} P1 掉粉诊断\n\n"
            f"- **状态**: {p1['root_cause']}\n"
            f"- **掉粉率**: {p1['drawdown_pct']:.1f}%\n" if p1['drawdown_pct'] is not None else
            f"- **掉粉率**: 未知（缺字段）\n"
        )
        sections.append(f"- **处方**: {p1['advice']}\n")
        if p1.get("engagement_structure"):
            sections.append(f"- **互动结构**: {p1['engagement_structure']}\n")
        sections.append("")
    except Exception as e:  # noqa: BLE001
        sections.append(f"### ⚪ P1 掉粉诊断\n\n> 诊断降级: {e}\n")

    # P3
    try:
        p3 = diagnose_pricing(account, xprof)
        emoji = _SEVERITY_EMOJI.get(p3["severity"], "⚪")
        sections.append(f"### {emoji} P3 报价合理性诊断\n\n")
        if p3.get("star_price_yuan"):
            sections.append(f"- **星图定价（1-20s）**: {p3['star_price_yuan']:.0f} 元\n")
        if p3.get("actual_cpm"):
            sections.append(f"- **实际 CPM**: {p3['actual_cpm']:.1f} 元/千次\n")
        if p3.get("vv_deviation_pct"):
            sections.append(f"- **预期 vs 实际播放偏差**: {p3['vv_deviation_pct']:.1f}%\n")
        if p3.get("estimated_price_yuan"):
            sections.append(f"- **估算报价（兜底）**: {p3['estimated_price_yuan']:.0f} 元\n")
        sections.append(f"- **结论**: {p3['advice']}\n\n")
    except Exception as e:  # noqa: BLE001
        sections.append(f"### ⚪ P3 报价合理性诊断\n\n> 诊断降级: {e}\n")

    # P6
    try:
        p6 = diagnose_funnel(account)
        emoji = _SEVERITY_EMOJI.get(p6["severity"], "⚪")
        sections.append(f"### {emoji} P6 转化漏斗诊断\n\n")
        sections.append(f"- **漏斗堵点**: {p6['bottleneck_desc']}\n")
        sections.append(f"- **L1 流量**: {'✅' if p6['L1_traffic_ok'] else '❌'} (均播/均赞约 {p6['avg_play_proxy']})\n")
        sections.append(f"- **L2 橱窗**: {'✅ 已开通' if p6['L2_commerce_entry_ok'] else '❌ 未开通'}\n")
        cd_str = f"{p6['commerce_density_pct']:.1f}%" if p6['commerce_density_pct'] is not None else "未知"
        sections.append(f"- **L3 商业密度**: {'✅' if p6['L3_density_ok'] else '❌'} {cd_str}\n")
        sections.append(f"- **意图信号**: {p6['intent_tier']}\n")
        if p6.get("over_commercial_warn"):
            sections.append(f"- ⚠️ {p6['over_commercial_warn']}\n")
        sections.append(f"- **处方**: {p6['advice']}\n\n")
    except Exception as e:  # noqa: BLE001
        sections.append(f"### ⚪ P6 转化漏斗诊断\n\n> 诊断降级: {e}\n")

    # P4
    try:
        p4 = diagnose_track(account, xprof)
        tier_colors = {"S": "🔴", "A": "🟠", "B": "🟡", "C": "🔵", "D": "⚪"}
        tier_emoji = tier_colors.get(p4["commercial_tier"], "⚪")
        sections.append(f"### {tier_emoji} P4 赛道定位诊断\n\n")
        sections.append(f"- **垂直度**: {p4['vertical_desc']}\n")
        sections.append(f"- **商业价值档**: {p4['commercial_desc']}\n")
        if p4.get("industry_tags"):
            sections.append(f"- **行业标签**: {', '.join(p4['industry_tags'][:5])}\n")
        sections.append(f"- **定位处方**: {p4['prescription']}\n")
        sections.append(f"- **行动建议**: {p4['advice']}\n\n")
    except Exception as e:  # noqa: BLE001
        sections.append(f"### ⚪ P4 赛道定位诊断\n\n> 诊断降级: {e}\n")

    sections.append("> ⚠️ 以上阈值为经验值，上线前需跑 50-100 真实账号建分位基线校准后替换。\n")
    return "".join(sections)
