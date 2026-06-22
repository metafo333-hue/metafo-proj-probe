"""复合数据结果指标 C1-C8 · probe 全量数据组合矩阵 v1.0 § 四

每个指标为纯函数·输入 account dict + xprof(可选 XingtuProfile 对象或 dict)。
缺字段时降级(标注 #需全量数据)·不崩。

指标列表:
  C1 账号综合健康分    0-100
  C2 粉丝质量分        0-100
  C3 商业转化潜力分    0-100
  C4 内容竞争力分      0-100
  C5 赛道竞争力分      0-100
  C6 破圈能力分        0-100
  C7 商业价值评级      A/B/C/D/F
  C8 私域变现成熟度    0-100
"""
from __future__ import annotations

from typing import Any

# ── 内部工具 ──────────────────────────────────────────────────────────────────

def _g(d: dict | None, *keys, default=None):
    """深层安全取值·dict or object 兼容。"""
    if d is None:
        return default
    v = d
    for k in keys:
        if isinstance(v, dict):
            v = v.get(k, default)
        else:
            v = getattr(v, k, default)
        if v is None:
            return default
    return v


def _xattr(xprof, attr: str, default=None):
    """兼容 XingtuProfile 对象和 dict。"""
    if xprof is None:
        return default
    if isinstance(xprof, dict):
        return xprof.get(attr, default)
    return getattr(xprof, attr, default)


def _idx(xprof, name: str, field: str = "avg_value", default=None):
    """取星图指数字段(IndexItem or dict)。"""
    item = _xattr(xprof, name)
    if item is None:
        return default
    if isinstance(item, dict):
        return item.get(field, default)
    return getattr(item, field, default)


def _clamp(v: float | None, lo: float = 0.0, hi: float = 100.0) -> float:
    if v is None:
        return 0.0
    return max(lo, min(hi, float(v)))


def _score_range(v: float | None, lo: float, hi: float) -> float:
    """将值 v 线性映射到 [0, 100]·超出范围截断。"""
    if v is None:
        return 0.0
    return _clamp((v - lo) / (hi - lo) * 100)


# ── C1：账号综合健康分 ────────────────────────────────────────────────────────

def score_c1_health(account: dict[str, Any]) -> dict[str, Any]:
    """C1 账号综合健康分 (0-100)。

    子项:
      互动率质量  25%  (avg_like + avg_collect?) / follower
      粉丝净值    20%  1 - drawdown_pct/100
      更新节奏    20%  update_gap_days (days_since_last or avg_gap) 越短越好
      内容趋势    20%  burst_ratio 归一化 (爆款能力代理)
      系列化率    15%  (mix_count + series_count) / aweme_count

    Notes:
      update_gap_days / engagement slope 需全量时序数据才能精算;
      此处用 burst_ratio 作互动趋势代理，avg_like/follower 作互动率代理。
    """
    missing: list[str] = []
    weights: dict[str, float] = {
        "interaction_quality": 0.25,
        "follower_net": 0.20,
        "update_rhythm": 0.20,
        "content_trend": 0.20,
        "serialization": 0.15,
    }

    # 1. 互动率质量：avg_like / follower·[0.005, 0.08] → 满分
    avg_like: float | None = account.get("avg_like")
    follower: float | None = account.get("follower")
    if avg_like is not None and follower and follower > 0:
        lpf = avg_like / follower
        s_interaction = _score_range(lpf, 0.005, 0.08)
    else:
        s_interaction = 0.0
        missing.append("avg_like/follower(互动率质量)")

    # 2. 粉丝净值：1 - drawdown_pct/100
    fd = account.get("follower_drawdown") or {}
    if isinstance(fd, (int, float)):
        drawdown_pct: float | None = float(fd)
    elif isinstance(fd, dict):
        drawdown_pct = fd.get("drawdown_pct") or fd.get("pct") or fd.get("value")
        drawdown_pct = float(drawdown_pct) if drawdown_pct is not None else None
    else:
        drawdown_pct = None
    # 自算 fallback
    if drawdown_pct is None:
        mf = account.get("max_follower")
        cur = account.get("follower") or 0
        if mf and mf > 0:
            drawdown_pct = (mf - cur) / mf * 100
    s_follower_net: float = _clamp((1 - (drawdown_pct or 0) / 100) * 100) if drawdown_pct is not None else 50.0
    if drawdown_pct is None:
        missing.append("max_follower/follower_drawdown(粉丝净值)")

    # 3. 更新节奏：combo-deep-probe 暂无 avg_gap_days·用 burst_ratio 存在性作代理
    #    #需全量数据 — works 时序 create_time diff
    update_gap = account.get("update_gap_days")  # 如有则用
    if update_gap is not None:
        s_rhythm = _score_range(float(update_gap), 0.5, 7.0)
        s_rhythm = 100 - s_rhythm  # 间隔越短得分越高
    else:
        # 降级：有 works_analyzed 时假设近期有更新·给中间分
        s_rhythm = 50.0
        missing.append("update_gap_days #需全量数据(更新节奏)")

    # 4. 内容趋势：burst_ratio [1, 20] → 0-100
    burst = account.get("burst_ratio")
    if burst is not None:
        s_trend = _score_range(float(burst), 1.0, 20.0)
    else:
        s_trend = 30.0
        missing.append("burst_ratio(内容趋势代理)")

    # 5. 系列化率
    mix_c = account.get("mix_count") or 0
    series_c = account.get("series_count") or 0
    aweme_c = account.get("aweme_count") or 0
    if aweme_c > 0:
        serial_rate = (mix_c + series_c) / aweme_c
        s_serial = _clamp(serial_rate * 500)  # 20% → 满分
    else:
        s_serial = 0.0
        missing.append("aweme_count(系列化率)")

    raw = (
        s_interaction * weights["interaction_quality"]
        + s_follower_net * weights["follower_net"]
        + s_rhythm * weights["update_rhythm"]
        + s_trend * weights["content_trend"]
        + s_serial * weights["serialization"]
    )
    score = round(_clamp(raw))

    # 三期判断
    if score >= 70:
        phase = "上升"
    elif score >= 45:
        phase = "平台"
    else:
        phase = "衰退"

    return {
        "score": score,
        "phase": phase,
        "missing": missing,
        "breakdown": {
            "interaction_quality": round(s_interaction),
            "follower_net": round(s_follower_net),
            "update_rhythm": round(s_rhythm),
            "content_trend": round(s_trend),
            "serialization": round(s_serial),
        },
    }


# ── C2：粉丝质量分 ────────────────────────────────────────────────────────────

def score_c2_fans_quality(account: dict[str, Any], xprof=None) -> dict[str, Any]:
    """C2 粉丝质量分 (0-100)。

    子项:
      互动真实度  30%  like_per_follower [0.01, 0.05]
      水军风险    25%  1 - IP集中度 (需评论数据·降级)  #需全量数据
      评论真实性  15%  engagement_structure 中 level1_pct (需评论)  #需全量数据
      消费力等级  20%  iPhone占比 * (1 - 低客单价占比) (需星图画像)  #需全量数据
      地域多元度  10%  1 - 单省份最高占比 (需星图画像)  #需全量数据
    """
    missing: list[str] = []

    # 1. 互动真实度
    avg_like = account.get("avg_like")
    follower = account.get("follower") or 0
    if avg_like is not None and follower > 0:
        lpf = avg_like / follower
        # 0.01~0.05 满分区间
        if lpf < 0.001:
            s_real = 10.0  # 极低=刷量风险
        elif lpf <= 0.05:
            s_real = _score_range(lpf, 0.001, 0.05)
        else:
            s_real = 100.0
    else:
        s_real = 0.0
        missing.append("avg_like/follower(互动真实度)")

    # 2. 水军风险：需评论 IP 数据·此处从 engagement_structure 推断
    es = account.get("engagement_structure") or {}
    es_label = (es if isinstance(es, str) else _g(es, "label") or _g(es, "type") or "")
    ip_concentration = None  # #需全量数据
    if ip_concentration is not None:
        s_bot = _clamp((1 - ip_concentration / 100) * 100)
    else:
        # 有争议标签时降低
        s_bot = 40.0 if ("争议" in es_label or "risk" in es_label.lower()) else 60.0
        missing.append("ip_concentration #需全量数据(水军风险·评论IP)")

    # 3. 评论真实性：#需全量数据
    s_comment = 50.0
    missing.append("level1_pct #需全量数据(评论层级真实性)")

    # 4. 消费力等级：从 xprof 粉丝画像取 iPhone 占比
    iphone_pct: float | None = None
    low_aov_pct: float | None = None
    if xprof is not None:
        fp: list = _xattr(xprof, "fans_portrait") or []
        for item in fp:
            if not isinstance(item, dict):
                continue
            # origin_type=3 设备分布
            if item.get("type") == 3 or item.get("origin_type") == 3:
                top5 = item.get("top5") or []
                for t5 in top5:
                    if "iPhone" in str(t5.get("name", "")):
                        try:
                            iphone_pct = float(t5.get("value") or 0)
                        except (ValueError, TypeError):
                            pass
            # origin_type=12 客单价·0-50占比
            if item.get("type") == 12 or item.get("origin_type") == 12:
                top5 = item.get("top5") or []
                for t5 in top5:
                    name = str(t5.get("name", ""))
                    if "0-50" in name or "50以下" in name:
                        try:
                            low_aov_pct = float(t5.get("value") or 0)
                        except (ValueError, TypeError):
                            pass
    if iphone_pct is not None:
        s_consume = _clamp(iphone_pct * (1 - (low_aov_pct or 0) / 100))
    else:
        s_consume = 40.0
        missing.append("fans_portrait #需全量数据(消费力等级)")

    # 5. 地域多元度：需画像数据
    s_geo = 55.0
    missing.append("fans_portrait.province #需全量数据(地域多元度)")

    raw = (
        s_real * 0.30
        + s_bot * 0.25
        + s_comment * 0.15
        + s_consume * 0.20
        + s_geo * 0.10
    )
    score = round(_clamp(raw))

    if score >= 75:
        label = "高质量粉"
    elif score >= 50:
        label = "含水"
    else:
        label = "刷量风险"

    return {"score": score, "label": label, "missing": missing}


# ── C3：商业转化潜力分 ────────────────────────────────────────────────────────

def score_c3_commerce(account: dict[str, Any], xprof=None) -> dict[str, Any]:
    """C3 商业转化潜力分 (0-100)。

    子项:
      带货指数    30%  link_shopping_index.avg_value / 100
      转化指数    25%  link_convert_index.avg_value / 100
      商业密度    20%  min(commerce_density/0.4, 1.0)
      橱窗/直播   15%  with_commerce_entry + live_commerce
      粉丝消费力  10%  客单价100+占比 #需全量数据
    """
    missing: list[str] = []

    # 1. 带货指数
    shopping_v = _idx(xprof, "link_shopping_index", "avg_value")
    if shopping_v is None:
        # 尝试直接 value
        shopping_v = _idx(xprof, "link_shopping_index", "value")
    if shopping_v is not None:
        s_shopping = _clamp(float(shopping_v))
    else:
        s_shopping = 0.0
        missing.append("link_shopping_index #需星图数据")

    # 2. 转化指数
    convert_v = _idx(xprof, "link_convert_index", "avg_value")
    if convert_v is None:
        convert_v = _idx(xprof, "link_convert_index", "value")
    if convert_v is not None:
        s_convert = _clamp(float(convert_v))
    else:
        s_convert = 0.0
        missing.append("link_convert_index #需星图数据")

    # 3. 商业密度
    cd = account.get("commerce_density")
    if isinstance(cd, dict):
        cd = cd.get("ratio") or cd.get("value")
    if cd is not None:
        s_density = _clamp(min(float(cd) / 0.4, 1.0) * 100)
    else:
        s_density = 0.0
        missing.append("commerce_density(带货作品占比)")

    # 4. 橱窗/直播基础（各7.5分·满共15分→归一化到100分子项）
    ecom = 1 if account.get("with_commerce_entry") else 0
    live = 1 if account.get("live_commerce") else 0
    s_infra = float((ecom + live) / 2 * 100)

    # 5. 粉丝消费力 100+ 客单占比·#需全量数据
    high_aov_pct: float | None = None
    if xprof is not None:
        fp: list = _xattr(xprof, "fans_portrait") or []
        for item in fp:
            if not isinstance(item, dict):
                continue
            if item.get("type") == 12 or item.get("origin_type") == 12:
                top5 = item.get("top5") or []
                hi = 0.0
                for t5 in top5:
                    name = str(t5.get("name", ""))
                    if any(x in name for x in ["100-200", "200-500", "500+"]):
                        try:
                            hi += float(t5.get("value") or 0)
                        except (ValueError, TypeError):
                            pass
                if hi > 0:
                    high_aov_pct = hi
    if high_aov_pct is not None:
        s_consume = _clamp(high_aov_pct)
    else:
        s_consume = 30.0
        missing.append("fans_portrait.aov #需全量数据(粉丝消费力)")

    raw = (
        s_shopping * 0.30
        + s_convert * 0.25
        + s_density * 0.20
        + s_infra * 0.15
        + s_consume * 0.10
    )
    score = round(_clamp(raw))

    # 推荐变现路径
    if s_shopping > 60:
        path = "带货/星图广告"
    elif s_infra >= 100:
        path = "直播带货"
    elif score >= 50:
        path = "星图广告"
    else:
        path = "私域先行"

    return {"score": score, "path": path, "missing": missing}


# ── C4：内容竞争力分 ──────────────────────────────────────────────────────────

def score_c4_content(account: dict[str, Any], xprof=None) -> dict[str, Any]:
    """C4 内容竞争力分 (0-100)。

    子项:
      爆款产出    25%  burst_ratio 归一化
      互动趋势    20%  avg_like/max_like 稳定性代理
      视听质量    20%  #需全量数据(probe六层)
      竞品互动差  20%  #需全量数据(rec_videos interact_rate vs 自身)
      话题质量    15%  vertical_score 代理
    """
    missing: list[str] = []

    # 1. 爆款产出
    burst = account.get("burst_ratio")
    if burst is not None:
        s_burst = _score_range(float(burst), 1.0, 20.0)
    else:
        s_burst = 20.0
        missing.append("burst_ratio(爆款产出能力)")

    # 2. 互动趋势：用 avg_like/max_like 比值(越接近1=稳定·越低=依赖爆款)
    avg_like = account.get("avg_like")
    max_like = account.get("max_like")
    if avg_like is not None and max_like and max_like > 0:
        stability = float(avg_like) / float(max_like)
        # stability [0.05, 0.5] → 映射·越稳定越好
        s_trend = _score_range(stability, 0.05, 0.5)
    else:
        s_trend = 30.0
        missing.append("avg_like/max_like(互动趋势代理)")

    # 3. 视听质量·#需全量数据(probe六层 av_six)
    s_av = 50.0
    missing.append("av_six #需全量数据(probe视听六层质量)")

    # 4. 竞品互动率差距·#需全量数据(xingtu rec_videos)
    rec = _xattr(xprof, "rec_videos") or []
    if rec:
        rates = []
        for v in rec:
            if isinstance(v, dict):
                r = v.get("interact_rate")
                if r is not None:
                    try:
                        rates.append(float(r))
                    except (ValueError, TypeError):
                        pass
        if rates:
            avg_rate = sum(rates) / len(rates)
            # 自身代理：avg_like / follower
            follower = account.get("follower") or 1
            self_rate = (float(avg_like) / follower) if avg_like else 0.01
            ratio = self_rate / max(avg_rate, 0.001)
            s_comp = _clamp(min(ratio, 2.0) / 2.0 * 100)
        else:
            s_comp = 40.0
            missing.append("rec_videos.interact_rate #需星图数据")
    else:
        s_comp = 40.0
        missing.append("rec_videos #需星图数据(竞品互动率)")

    # 5. 话题选择质量：vertical_score [0,1]
    vs = account.get("vertical_score")
    if vs is not None:
        try:
            s_topic = _clamp(float(vs) * 100)
        except (ValueError, TypeError):
            s_topic = 40.0
    else:
        s_topic = 40.0
        missing.append("vertical_score(话题选择质量代理)")

    raw = (
        s_burst * 0.25
        + s_trend * 0.20
        + s_av * 0.20
        + s_comp * 0.20
        + s_topic * 0.15
    )
    score = round(_clamp(raw))

    # 短板识别
    parts = {
        "爆款": s_burst, "互动稳定性": s_trend,
        "视听质量": s_av, "竞品差距": s_comp, "话题质量": s_topic,
    }
    weak = min(parts, key=parts.get)
    return {"score": score, "weak": weak, "missing": missing}


# ── C5：赛道竞争力分 ──────────────────────────────────────────────────────────

def score_c5_track(account: dict[str, Any], xprof=None) -> dict[str, Any]:
    """C5 赛道竞争力分 (0-100)。

    子项:
      垂直度      25%  vertical_score
      赛道蓝海度  25%  #需全量数据(话题 competition_density)
      赛道商业价值 30%  link_shopping_index.avg_value(行业均值)
      账号赛道排名 20%  link_shopping_index.rank_percent(越小得分越高)
    """
    missing: list[str] = []

    # 1. 垂直度
    vs = account.get("vertical_score")
    s_vertical = _clamp(float(vs) * 100) if vs is not None else 50.0
    if vs is None:
        missing.append("vertical_score(垂直度)")

    # 2. 赛道蓝海度·#需全量数据
    s_blue_ocean = 50.0
    missing.append("competition_density #需全量数据(赛道蓝海度·话题内容数)")

    # 3. 赛道商业价值：avg_value 为行业均值指数
    shopping_avg = _idx(xprof, "link_shopping_index", "avg_value")
    if shopping_avg is not None:
        s_industry = _clamp(float(shopping_avg))
    else:
        s_industry = 30.0
        missing.append("link_shopping_index.avg_value #需星图数据(行业带货均值)")

    # 4. 账号赛道内排名：rank_percent 越小得分越高
    rank_pct = _idx(xprof, "link_shopping_index", "rank_percent")
    if rank_pct is not None:
        # rank_percent 是小数如 0.0118 = 前1.18%
        rp = float(rank_pct)
        if rp <= 1.0:  # 小数形式
            rp *= 100
        s_rank = _clamp((1 - rp / 100) * 100)
    else:
        s_rank = 30.0
        missing.append("link_shopping_index.rank_percent #需星图数据")

    raw = (
        s_vertical * 0.25
        + s_blue_ocean * 0.25
        + s_industry * 0.30
        + s_rank * 0.20
    )
    score = round(_clamp(raw))

    if score >= 75:
        track_label = "蓝海"
    elif score >= 45:
        track_label = "红海"
    else:
        track_label = "无路"

    return {"score": score, "track": track_label, "missing": missing}


# ── C6：破圈能力分 ────────────────────────────────────────────────────────────

def score_c6_breakout(account: dict[str, Any], xprof=None) -> dict[str, Any]:
    """C6 破圈能力分 (0-100)。

    子项:
      分发放大倍数  30%  avg_play / follower
      粉-观年龄错位 20%  #需全量数据(双画像)
      粉-观地域错位 20%  #需全量数据(双画像)
      传播率        15%  avg_like / follower (share 代理)
      情绪弧度传播  15%  #需全量数据(probe情绪弧度)
    """
    missing: list[str] = []

    # 1. 分发放大倍数：avg_play / follower
    avg_like = account.get("avg_like")  # avg_play 未在 account dict·用 avg_like 代理
    follower = account.get("follower") or 1
    # avg_play 更准·如有直接用
    avg_play = account.get("avg_play")
    if avg_play is not None:
        ratio = float(avg_play) / follower
    elif avg_like is not None:
        # 粗估：播放通常是点赞10-30倍
        ratio = float(avg_like) / follower
    else:
        ratio = None
    if ratio is not None:
        # ratio > 0.5 说明非粉丝也在看(算法推荐)
        s_distrib = _score_range(ratio, 0.01, 2.0)
    else:
        s_distrib = 20.0
        missing.append("avg_play/avg_like(分发放大倍数)")

    # 2. 粉-观年龄错位·#需全量数据(双画像比对)
    s_age_gap = 50.0
    missing.append("fans_portrait/audience_portrait #需全量数据(年龄错位)")

    # 3. 粉-观地域错位·#需全量数据
    s_geo_gap = 50.0
    missing.append("fans_portrait/audience_portrait #需全量数据(地域错位)")

    # 4. 传播率：avg_like/follower [0.005, 0.1]
    if avg_like is not None and follower > 0:
        lpf = float(avg_like) / follower
        s_share = _score_range(lpf, 0.005, 0.1)
    else:
        s_share = 20.0
        missing.append("avg_like/follower(传播率代理)")

    # 5. 情绪弧度传播力·#需全量数据(probe六层)
    s_emotion = 50.0
    missing.append("av_six.emotion_arc #需全量数据(情绪弧度)")

    raw = (
        s_distrib * 0.30
        + s_age_gap * 0.20
        + s_geo_gap * 0.20
        + s_share * 0.15
        + s_emotion * 0.15
    )
    score = round(_clamp(raw))

    if score >= 70:
        breakout_type = "跨赛道破圈"
    elif score >= 45:
        breakout_type = "爆款型破圈"
    else:
        breakout_type = "账号级内循环"

    return {"score": score, "type": breakout_type, "missing": missing}


# ── C7：商业价值评级 ──────────────────────────────────────────────────────────

def score_c7_grade(account: dict[str, Any], xprof=None) -> dict[str, Any]:
    """C7 达人综合商业价值评级 (A/B/C/D/F)。

    聚合: C2(粉丝质量) + C3(变现潜力) + 数据真实性 + 星图综合指数
    子项权重:
      粉丝质量分    25%  C2.score
      商业转化潜力  30%  C3.score
      数据真实性    25%  派生自C2水军项(engagement真实度)
      星图综合指数  20%  link_star_index.value
    """
    c2 = score_c2_fans_quality(account, xprof)
    c3 = score_c3_commerce(account, xprof)
    missing = list(set(c2["missing"] + c3["missing"]))

    # 数据真实性：从 engagement_structure 推断
    es = account.get("engagement_structure") or {}
    es_label = (es if isinstance(es, str) else _g(es, "label") or _g(es, "type") or "")
    if "water" in es_label.lower() or "刷量" in es_label or "异常" in es_label:
        s_real = 20.0
    elif "争议" in es_label:
        s_real = 50.0
    else:
        s_real = float(c2["score"])  # 粉丝质量代理真实性

    # 星图综合指数
    star_v = _idx(xprof, "link_star_index", "value")
    if star_v is None:
        star_v = _idx(xprof, "link_star_index", "avg_value")
    if star_v is not None:
        s_star = _clamp(float(star_v))
    else:
        s_star = 30.0
        missing.append("link_star_index #需星图数据(综合指数)")

    raw = (
        float(c2["score"]) * 0.25
        + float(c3["score"]) * 0.30
        + s_real * 0.25
        + s_star * 0.20
    )
    composite = _clamp(raw)

    if composite >= 85:
        grade, desc = "A", "优质商业达人·可溢价合作"
    elif composite >= 70:
        grade, desc = "B", "良好·标准价合作"
    elif composite >= 50:
        grade, desc = "C", "中等·加保量条款"
    elif composite >= 30:
        grade, desc = "D", "风险较高·大幅折扣或观察"
    else:
        grade, desc = "F", "数据严重异常·放弃"

    return {
        "grade": grade,
        "score": round(composite),
        "desc": desc,
        "missing": missing,
    }


# ── C8：私域变现成熟度 ────────────────────────────────────────────────────────

def score_c8_private(account: dict[str, Any], xprof=None) -> dict[str, Any]:
    """C8 私域变现成熟度 (0-100)。

    子项:
      合集系列化率     20%  (mix_count+series_count)/aweme_count
      收藏粉丝比       25%  avg_collect/follower  #需全量数据(avg_collect)
      私域意图评论率   25%  #需全量数据(评论关键词)
      城市集中度       15%  #需全量数据(粉丝城市分布)
      高互动内容占比   15%  #需全量数据(collect_rate>1%的作品)
    """
    missing: list[str] = []

    # 1. 合集系列化率
    mix_c = account.get("mix_count") or 0
    series_c = account.get("series_count") or 0
    aweme_c = account.get("aweme_count") or 0
    if aweme_c > 0:
        serial_rate = (mix_c + series_c) / aweme_c
        s_serial = _clamp(serial_rate * 500)
    else:
        s_serial = 0.0
        missing.append("mix_count/series_count/aweme_count(系列化率)")

    # 2. 收藏粉丝比：#需全量数据
    avg_collect = account.get("avg_collect")
    follower = account.get("follower") or 1
    if avg_collect is not None:
        collect_per_fan = float(avg_collect) / follower
        s_collect = _score_range(collect_per_fan, 0.001, 0.03)
    else:
        # 用 avg_like 的20%估算收藏
        avg_like = account.get("avg_like")
        if avg_like is not None:
            est = float(avg_like) * 0.2 / follower
            s_collect = _score_range(est, 0.001, 0.03)
        else:
            s_collect = 20.0
            missing.append("avg_collect #需全量数据(收藏粉丝比)")

    # 3. 私域意图评论率·#需全量数据
    s_intent = 40.0
    missing.append("comment_keywords #需全量数据(私域意图评论率)")

    # 4. 城市集中度·#需全量数据
    s_city = 50.0
    missing.append("fans_portrait.city #需全量数据(粉丝城市集中度)")

    # 5. 高互动内容占比·#需全量数据
    s_high_engage = 40.0
    missing.append("works.collect_rate #需全量数据(高互动内容占比)")

    raw = (
        s_serial * 0.20
        + s_collect * 0.25
        + s_intent * 0.25
        + s_city * 0.15
        + s_high_engage * 0.15
    )
    score = round(_clamp(raw))

    # 推荐路径
    if score >= 70:
        path = "会员订阅/知识付费"
    elif score >= 50:
        path = "本地社群/电商私域"
    else:
        path = "先建内容积累·私域尚早"

    return {"score": score, "path": path, "missing": missing}


# ── 汇总接口 ──────────────────────────────────────────────────────────────────

def compute_all(account: dict[str, Any], xprof=None) -> dict[str, Any]:
    """一次性计算8个复合指标·返回 {c1..c8} 字典。"""
    return {
        "c1": score_c1_health(account),
        "c2": score_c2_fans_quality(account, xprof),
        "c3": score_c3_commerce(account, xprof),
        "c4": score_c4_content(account, xprof),
        "c5": score_c5_track(account, xprof),
        "c6": score_c6_breakout(account, xprof),
        "c7": score_c7_grade(account, xprof),
        "c8": score_c8_private(account, xprof),
    }


# ── 报告段渲染 ────────────────────────────────────────────────────────────────

_GRADE_EMOJI = {"A": "🏆", "B": "✅", "C": "⚠️", "D": "🔴", "F": "❌"}


def render_composite_section(account: dict[str, Any], xprof=None) -> str:
    """串8个复合指标成 markdown 报告段·供 account_report 调用。"""
    r = compute_all(account, xprof)

    c1, c2, c3, c4 = r["c1"], r["c2"], r["c3"], r["c4"]
    c5, c6, c7, c8 = r["c5"], r["c6"], r["c7"], r["c8"]

    grade_icon = _GRADE_EMOJI.get(c7["grade"], "")

    lines = [
        "## 复合指标综合评估",
        "",
        f"| 指标 | 得分/评级 | 结论 |",
        f"|------|----------|------|",
        f"| C1 账号综合健康 | **{c1['score']}分** | {c1['phase']}期 |",
        f"| C2 粉丝质量 | **{c2['score']}分** | {c2['label']} |",
        f"| C3 商业转化潜力 | **{c3['score']}分** | 推荐路径: {c3['path']} |",
        f"| C4 内容竞争力 | **{c4['score']}分** | 短板: {c4['weak']} |",
        f"| C5 赛道竞争力 | **{c5['score']}分** | {c5['track']} |",
        f"| C6 破圈能力 | **{c6['score']}分** | {c6['type']} |",
        f"| C7 商业价值评级 | **{grade_icon}{c7['grade']}级**({c7['score']}分) | {c7['desc']} |",
        f"| C8 私域成熟度 | **{c8['score']}分** | {c8['path']} |",
        "",
    ]

    # C1 细项
    bd = c1["breakdown"]
    lines += [
        "### C1 健康分细项",
        f"互动率质量 {bd['interaction_quality']}分 · "
        f"粉丝净值 {bd['follower_net']}分 · "
        f"更新节奏 {bd['update_rhythm']}分 · "
        f"内容趋势 {bd['content_trend']}分 · "
        f"系列化率 {bd['serialization']}分",
        "",
    ]

    # 降级说明汇总
    all_missing: list[str] = []
    for k in ("c1", "c2", "c3", "c4", "c5", "c6", "c8"):
        all_missing.extend(r[k].get("missing", []))
    # C7 已是C2+C3的聚合·不重复列

    unique_missing = sorted(set(m for m in all_missing if "#需全量数据" in m))
    other_missing = sorted(set(m for m in all_missing if "#需全量数据" not in m))

    if unique_missing or other_missing:
        lines.append("### 待全量数据项（当前降级）")
        if unique_missing:
            lines.append("需接通采集链路后精算：")
            for m in unique_missing:
                lines.append(f"- {m}")
        if other_missing:
            lines.append("\n当前账号数据缺失（可补采）：")
            for m in other_missing:
                lines.append(f"- {m}")
        lines.append("")

    return "\n".join(lines)
