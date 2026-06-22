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


# ── 画像/评论 取值工具（兼容上游两种 top5 形态） ──────────────────────────────
# origin_type 实测映射(2026-06-22)：0性别 1年龄 2省份 3设备 5城市等级
#   6兴趣 8城市 10八大人群 11消费品类 12客单价
_OT_GENDER, _OT_AGE, _OT_PROVINCE, _OT_DEVICE = 0, 1, 2, 3
_OT_CITY_LEVEL, _OT_INTEREST, _OT_CITY, _OT_CROWD8 = 5, 6, 8, 10
_OT_CATEGORY, _OT_AOV = 11, 12


def _top5_pairs(item: dict) -> list[tuple[str, float]]:
    """归一化一个画像维度的 top5 为 [(name, value)]·兼容两种上游形态。

    上游两形态(实测)：
      A XingtuProfile.fans_portrait → top5 = [(distribution_key, int_value)]  (元组)
      B account.py _p2c 适配后        → top5 = [{"name":k,"value":v}]          (字典)
    value 为百分比整数(distribution_value)·非法值跳过。
    """
    out: list[tuple[str, float]] = []
    for t5 in (item.get("top5") or []):
        if isinstance(t5, dict):
            name, val = t5.get("name"), t5.get("value")
        elif isinstance(t5, (list, tuple)) and len(t5) >= 2:
            name, val = t5[0], t5[1]
        else:
            continue
        if name is None:
            continue
        try:
            out.append((str(name), float(val or 0)))
        except (TypeError, ValueError):
            continue
    return out


def _portrait_dim(xprof, attr: str, origin_type: int) -> list[tuple[str, float]] | None:
    """从 fans_portrait / audience_portrait 取指定 origin_type 维的 [(name,value)]。

    attr ∈ {"fans_portrait","audience_portrait"}。维度不存在 → None。
    """
    dims = _xattr(xprof, attr) or []
    for item in dims:
        if not isinstance(item, dict):
            continue
        ot = item.get("origin_type")
        if ot is None:
            ot = item.get("type")
        if ot == origin_type:
            pairs = _top5_pairs(item)
            return pairs if pairs else None
    return None


def _herfindahl(pairs: list[tuple[str, float]]) -> float | None:
    """集中度 HHI 代理：返回归一化占比的平方和(0-1)·越高越集中。

    pairs 的 value 为百分比·内部按和归一化(只取到 top5 故和可能 <100)。
    返回 None 当无有效项。
    """
    total = sum(v for _, v in pairs if v > 0)
    if total <= 0:
        return None
    return sum((v / total) ** 2 for _, v in pairs if v > 0)


def _comment_deep(account: dict) -> dict | None:
    """安全取 account['comment_deep']（评论深化·account.py _build_comment_deep 产出）。"""
    cd = account.get("comment_deep")
    return cd if isinstance(cd, dict) else None


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
      水军风险    25%  多维综合(IP集中/多样/digg异常/作者互动/回复活跃)
      评论真实性  15%  level_dist 真实评论占比(level1 主楼占比·楼层结构)
      消费力等级  20%  iPhone占比 * (1 - 低客单价占比) (星图画像)
      地域多元度  10%  省份集中度 + 城市层级分布 (星图画像)
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

    # 2. 水军风险：多维综合（account.comment_deep·满血评论深化）
    bot = _bot_risk(account)
    s_bot = bot["score"]
    if bot.get("degraded"):
        missing.append(bot["missing"])

    # 3. 评论层级真实性：comment_deep.level_dist 真实评论占比
    creal = _comment_realness(account)
    s_comment = creal["score"]
    if creal.get("degraded"):
        missing.append(creal["missing"])

    # 4. 消费力等级：从 xprof 粉丝画像取 iPhone 占比 × (1-低客单占比)
    iphone_pct: float | None = None
    device = _portrait_dim(xprof, "fans_portrait", _OT_DEVICE)
    if device:
        for name, val in device:
            if "iPhone" in name or "苹果" in name:
                iphone_pct = val
                break
    low_aov_pct: float | None = None
    aov = _portrait_dim(xprof, "fans_portrait", _OT_AOV)
    if aov:
        for name, val in aov:
            if "0-50" in name or "50以下" in name or "0~50" in name:
                low_aov_pct = val
                break
    if iphone_pct is not None:
        s_consume = _clamp(iphone_pct * (1 - (low_aov_pct or 0) / 100))
    else:
        s_consume = 40.0
        missing.append("fans_portrait.device #需全量数据(消费力等级)")

    # 5. 地域多元度：省份集中度(HHI) + 城市层级分布
    geo = _geo_diversity(xprof)
    s_geo = geo["score"]
    if geo.get("degraded"):
        missing.append(geo["missing"])

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

    return {
        "score": score,
        "label": label,
        "bot_risk": bot,        # 水军风险多维细项+证据+结论
        "comment_realness": creal,
        "geo_diversity": geo,   # 地域多元多维细项+结论
        "missing": missing,
    }


# ── C2 子项算法：水军风险（多维综合·评论深化） ───────────────────────────────

def _bot_risk(account: dict[str, Any]) -> dict[str, Any]:
    """水军风险多维评分（0-100·越高越健康）。

    维度(comment_deep·account.py _build_comment_deep 实测真值)：
      ip_concentration  最高省份占比(0-1)·越高越像集中刷量      权重 0.30(反向)
      ip_diversity      unique省份/总评论(0-1)·越高越自然        权重 0.25(正向)
      avg_digg          评论平均点赞·异常高(>50)疑刷赞           权重 0.15(异常惩罚)
      author_reply_rate 作者回赞占比(0-1)·适度=真实运营          权重 0.15(正向·过高也疑)
      reply_active_rate 被回复占比(0-1)·有真实讨论               权重 0.15(正向)
    无 comment_deep → 降级用 engagement_structure 标签代理。
    ⚠️阈值(ip_concentration>0.6疑/avg_digg>50疑)待真实样本校准。
    """
    cd = _comment_deep(account)
    evidence: list[str] = []
    dims: dict[str, Any] = {}

    if not cd or not cd.get("sample_size"):
        # 降级：engagement_structure 标签
        es = account.get("engagement_structure") or {}
        es_label = (es if isinstance(es, str)
                    else _g(es, "label") or _g(es, "type") or "")
        ip_c = account.get("ip_concentration")  # account.py 镜像(0-1)
        if ip_c is not None:
            s = _clamp((1 - float(ip_c)) * 100)
            evidence.append(f"评论IP最高省份占比 {float(ip_c) * 100:.0f}%(仅此一维)")
            return {"score": round(s), "dims": {"ip_concentration": ip_c},
                    "evidence": evidence,
                    "verdict": _bot_verdict(s),
                    "degraded": True,
                    "missing": "comment_deep #需全量数据(水军风险其余4维)"}
        s = 40.0 if ("争议" in es_label or "risk" in es_label.lower()) else 60.0
        return {"score": round(s), "dims": {}, "evidence": ["无评论深化·用互动结构标签代理"],
                "verdict": _bot_verdict(s), "degraded": True,
                "missing": "comment_deep #需全量数据(水军风险·评论IP/digg/回复)"}

    n = cd.get("sample_size") or 0
    parts: list[tuple[float, float]] = []  # (score, weight)

    ip_c = cd.get("ip_concentration")
    if ip_c is not None:
        # 0.6+ 高度集中疑刷·0.2- 自然
        s_ipc = _clamp((1 - _clamp(float(ip_c), 0, 1)) * 100)
        dims["ip_concentration"] = round(float(ip_c), 2)
        parts.append((s_ipc, 0.30))
        if float(ip_c) > 0.6:
            evidence.append(f"⚠️IP高度集中:最高省份占 {float(ip_c) * 100:.0f}%(>60%疑刷)")
        else:
            evidence.append(f"IP分布:最高省份占 {float(ip_c) * 100:.0f}%")

    ip_d = cd.get("ip_diversity")
    if ip_d is not None:
        s_ipd = _clamp(float(ip_d) * 100)
        dims["ip_diversity"] = round(float(ip_d), 2)
        parts.append((s_ipd, 0.25))
        evidence.append(f"IP多样性:约 {int(float(ip_d) * n)} 个省份/{n} 评论({float(ip_d) * 100:.0f}%)")

    avg_digg = cd.get("avg_digg")
    if avg_digg is not None:
        ad = float(avg_digg)
        # 正常评论点赞 0-20·>50 疑刷赞·线性惩罚
        if ad <= 20:
            s_digg = 100.0
        elif ad >= 100:
            s_digg = 10.0
        else:
            s_digg = _clamp(100 - (ad - 20) / 80 * 90)
        dims["avg_digg"] = ad
        parts.append((s_digg, 0.15))
        if ad > 50:
            evidence.append(f"⚠️评论平均点赞 {ad:.0f}(>50疑刷赞)")

    arr = cd.get("author_reply_rate")
    if arr is not None:
        a = float(arr)
        # 0.1-0.5 健康运营·0=冷漠·>0.8 疑自导自演
        if 0.1 <= a <= 0.5:
            s_arr = 100.0
        elif a < 0.1:
            s_arr = _clamp(a / 0.1 * 70)
        else:  # >0.5
            s_arr = _clamp(100 - (a - 0.5) / 0.5 * 50)
        dims["author_reply_rate"] = round(a, 2)
        parts.append((s_arr, 0.15))
        if a > 0.8:
            evidence.append(f"⚠️作者回赞率 {a * 100:.0f}%偏高(疑自导自演)")

    rar = cd.get("reply_active_rate")
    if rar is not None:
        s_rar = _clamp(float(rar) * 200)  # 0.5 → 满分
        dims["reply_active_rate"] = round(float(rar), 2)
        parts.append((s_rar, 0.15))
        evidence.append(f"评论被回复活跃度 {float(rar) * 100:.0f}%")

    if parts:
        tw = sum(w for _, w in parts)
        s = sum(sc * w for sc, w in parts) / tw if tw else 50.0
    else:
        s = 50.0
    s = round(_clamp(s))
    return {"score": s, "dims": dims, "evidence": evidence,
            "verdict": _bot_verdict(s), "sample_size": n, "degraded": False}


def _bot_verdict(s: float) -> str:
    if s >= 70:
        return "健康(无明显水军特征)"
    if s >= 45:
        return "可疑(部分维度异常·建议二次核验)"
    return "高风险(多维异常·疑刷量/控评)"


# ── C2 子项算法：评论层级真实性 ──────────────────────────────────────────────

def _comment_realness(account: dict[str, Any]) -> dict[str, Any]:
    """评论层级真实性(0-100)·comment_deep.level_dist。

    level=1 为主楼真实评论·level≥2 为楼中楼(回复)。
    主楼占比适中(0.6-0.9)=自然讨论；过低=灌水回复堆叠；过高(=1.0)=无互动深度。
    返回 {score, level_dist, level1_ratio, evidence, verdict}。
    """
    cd = _comment_deep(account)
    if not cd or not cd.get("level_dist"):
        return {"score": 50.0, "level1_ratio": None, "evidence": [],
                "verdict": "待评论数据", "degraded": True,
                "missing": "comment_deep.level_dist #需全量数据(评论层级真实性)"}
    ld = cd["level_dist"]
    total = sum(int(v) for v in ld.values()) or 0
    if total <= 0:
        return {"score": 50.0, "level1_ratio": None, "evidence": [],
                "verdict": "评论层级缺失", "degraded": True,
                "missing": "comment_deep.level_dist #需全量数据(评论层级真实性)"}
    l1 = int(ld.get("1", 0))
    l1_ratio = l1 / total
    # 0.6-0.9 健康区·线性偏离惩罚
    if 0.6 <= l1_ratio <= 0.9:
        s = 90.0 + (1 - abs(l1_ratio - 0.75) / 0.15) * 10
    elif l1_ratio < 0.6:
        s = _clamp(l1_ratio / 0.6 * 90)
    else:  # >0.9·无楼中楼深度互动
        s = _clamp(90 - (l1_ratio - 0.9) / 0.1 * 30)
    s = round(_clamp(s))
    ev = [f"主楼评论(level1)占 {l1_ratio * 100:.0f}%({l1}/{total})·楼层分布 {dict(sorted(ld.items()))}"]
    if l1_ratio > 0.95:
        verdict = "几乎无楼中楼·互动深度浅"
    elif l1_ratio < 0.5:
        verdict = "回复堆叠多·疑控评/水楼"
    else:
        verdict = "评论层级自然·真实讨论"
    return {"score": s, "level_dist": ld, "level1_ratio": round(l1_ratio, 2),
            "evidence": ev, "verdict": verdict, "degraded": False}


# ── C2 子项算法：地域多元度 ──────────────────────────────────────────────────

def _geo_diversity(xprof) -> dict[str, Any]:
    """地域多元度(0-100)·星图省份分布(origin_type=2) + 城市层级(origin_type=5)。

    多维：
      省份集中度(HHI)  越低越分散·1-HHI 映射                权重 0.65
      城市层级分布     高线(一二线)占比·分布越均衡越多元    权重 0.35
    结论：全国型 / 区域型 / 本地型。
    返回 {score, top_province, province_hhi, city_levels, evidence, verdict}。
    """
    prov = _portrait_dim(xprof, "fans_portrait", _OT_PROVINCE)
    city_lvl = _portrait_dim(xprof, "fans_portrait", _OT_CITY_LEVEL)
    if not prov and not city_lvl:
        return {"score": 55.0, "evidence": [], "verdict": "待画像数据",
                "degraded": True,
                "missing": "fans_portrait.province #需全量数据(地域多元度)"}

    evidence: list[str] = []
    parts: list[tuple[float, float]] = []
    top_province = None
    province_hhi = None
    if prov:
        top_province, top_val = prov[0]
        hhi = _herfindahl(prov)
        province_hhi = round(hhi, 3) if hhi is not None else None
        if hhi is not None:
            # HHI: 0.05(极分散)~0.5(单省主导)·1-归一化
            s_prov = _clamp((1 - _score_range(hhi, 0.05, 0.5) / 100) * 100)
            parts.append((s_prov, 0.65))
            evidence.append(
                f"省份分布:top1={top_province}({top_val:.0f}%)·集中度HHI={province_hhi}")

    city_levels: dict[str, float] = {}
    if city_lvl:
        city_levels = {k: v for k, v in city_lvl}
        # 高线(新一线/一线/二线)占比·越高消费力越强·分布均衡=多元
        hhi_c = _herfindahl(city_lvl)
        if hhi_c is not None:
            s_city = _clamp((1 - _score_range(hhi_c, 0.2, 0.6) / 100) * 100)
            parts.append((s_city, 0.35))
            evidence.append(f"城市层级:{'·'.join(f'{k}{v:.0f}%' for k, v in city_lvl[:3])}")

    if parts:
        tw = sum(w for _, w in parts)
        s = sum(sc * w for sc, w in parts) / tw if tw else 55.0
    else:
        s = 55.0
    s = round(_clamp(s))

    # 结论：基于省份集中度
    if province_hhi is not None:
        if province_hhi <= 0.12:
            verdict = "全国型(粉丝地域高度分散)"
        elif province_hhi <= 0.30:
            verdict = "区域型(若干省份主导)"
        else:
            verdict = f"本地型(以{top_province}为核心)"
    else:
        verdict = "城市层级多元(省份维缺失)"

    return {"score": s, "top_province": top_province, "province_hhi": province_hhi,
            "city_levels": city_levels, "evidence": evidence, "verdict": verdict,
            "degraded": False}


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

    # 4. 竞品互动率差距（多维·xprof.rec_interact_rates 已算·robust）
    comp = _competitor_gap(account, xprof)
    s_comp = comp["score"]
    if comp.get("degraded"):
        missing.append(comp["missing"])

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
    return {"score": score, "weak": weak, "competitor_gap": comp, "missing": missing}


# ── C4 子项算法：竞品互动差（多维 + 归因） ───────────────────────────────────

def _competitor_gap(account: dict[str, Any], xprof) -> dict[str, Any]:
    """竞品互动差(0-100)·xprof.rec_interact_rates(星图代表作互动率·已算) vs 自身。

    多维：
      相对差距   self_rate / 竞品中位数·>1 占优             权重 0.55
      绝对水平   自身互动率落在 [0.01,0.08] 行业带的位置     权重 0.25
      离散惩罚   竞品互动率方差大→赛道波动·稳定性参考        权重 0.20
    归因：领先/持平/落后 + 落后归因(互动率/分发)。
    返回 {score, self_rate, comp_median, ratio, evidence, verdict, attribution}。
    ⚠️阈值(行业互动带[0.01,0.08])待按行业细分校准。
    """
    rates = _xattr(xprof, "rec_interact_rates")
    if not rates:
        # 兼容旧 raw rec_videos(interact_rate 字段)
        rec = _xattr(xprof, "rec_videos") or []
        rates = []
        for v in rec:
            if isinstance(v, dict):
                r = v.get("interact_rate")
                if r is None and isinstance(v.get("stats"), dict):
                    r = v["stats"].get("interact_rate")
                if r is not None:
                    try:
                        rates.append(float(r))
                    except (TypeError, ValueError):
                        pass
    valid = []
    for r in (rates or []):
        try:
            valid.append(float(r))
        except (TypeError, ValueError):
            continue
    if not valid:
        return {"score": 40.0, "self_rate": None, "comp_median": None,
                "evidence": [], "verdict": "无竞品代表作数据",
                "attribution": None, "degraded": True,
                "missing": "rec_interact_rates #需星图数据(竞品互动率)"}

    valid.sort()
    m = len(valid)
    comp_median = valid[m // 2] if m % 2 else (valid[m // 2 - 1] + valid[m // 2]) / 2

    avg_like = account.get("avg_like")
    follower = account.get("follower") or 0
    self_rate = (float(avg_like) / follower) if (avg_like and follower > 0) else None

    evidence: list[str] = [
        f"竞品代表作互动率中位数 {comp_median * 100:.2f}%(n={m}·区间 "
        f"{valid[0] * 100:.2f}%–{valid[-1] * 100:.2f}%)"]
    parts: list[tuple[float, float]] = []
    ratio = None
    attribution = None
    verdict = "待自身互动率"

    if self_rate is not None:
        ratio = self_rate / max(comp_median, 1e-4)
        # 相对差距：ratio 0.5→落后 / 1→持平 / 1.5+→领先
        s_rel = _clamp(min(ratio, 2.0) / 2.0 * 100)
        parts.append((s_rel, 0.55))
        # 绝对水平
        s_abs = _score_range(self_rate, 0.01, 0.08)
        parts.append((s_abs, 0.25))
        evidence.append(f"自身互动率 {self_rate * 100:.2f}%·相对竞品 {ratio:.2f}×")
        if ratio >= 1.2:
            verdict = "互动领先竞品"
            attribution = "内容互动效率高于赛道代表作"
        elif ratio >= 0.8:
            verdict = "与竞品持平"
            attribution = "互动效率赛道中游"
        else:
            verdict = "互动落后竞品"
            # 归因：绝对值低=内容力·分发足但互动差
            if self_rate < 0.01:
                attribution = "绝对互动率偏低·内容钩子/完播待提升"
            else:
                attribution = "互动率尚可但低于赛道头部·选题/封面差异化不足"
    else:
        evidence.append("缺自身 avg_like/follower·仅给竞品基准")

    # 离散惩罚：竞品方差大说明赛道波动·给中性偏高(机会多)
    if m >= 2:
        mean_v = sum(valid) / m
        var = sum((x - mean_v) ** 2 for x in valid) / m
        cv = (var ** 0.5) / mean_v if mean_v > 0 else 0
        s_disp = _clamp(50 + min(cv, 1.0) * 30)  # 波动大→机会分
        parts.append((s_disp, 0.20))

    if parts:
        tw = sum(w for _, w in parts)
        s = round(_clamp(sum(sc * w for sc, w in parts) / tw)) if tw else 40
    else:
        s = 40

    return {"score": s, "self_rate": round(self_rate, 4) if self_rate else None,
            "comp_median": round(comp_median, 4), "ratio": round(ratio, 2) if ratio else None,
            "evidence": evidence, "verdict": verdict, "attribution": attribution,
            "degraded": False}


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

    # 2. 赛道蓝海度（account.track_competition·搜行业词结果密度）
    blue = _blue_ocean(account)
    s_blue_ocean = blue["score"]
    if blue.get("degraded"):
        missing.append(blue["missing"])

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

    return {"score": score, "track": track_label, "blue_ocean": blue, "missing": missing}


# ── C5 子项算法：赛道蓝海度（搜索结果密度） ──────────────────────────────────

def _blue_ocean(account: dict[str, Any]) -> dict[str, Any]:
    """赛道蓝海度(0-100·越高越蓝海)·account.track_competition。

    track_competition(account.py _track_competition 实测)：
      result_count  当页结果数(竞争密度代理·满页通常 18)
      has_more      是否还有更多(海量竞争=红海信号)
    多维：
      结果密度   result_count 越少越蓝海·满页 18 → 红海           权重 0.6
      海量信号   has_more=True → 红海惩罚                          权重 0.4
    结论：蓝海/平衡/红海 + 机会窗口提示。
    ⚠️阈值(满页18·result_count分档)待跨赛道采样校准。
    """
    tc = account.get("track_competition")
    if not isinstance(tc, dict) or tc.get("result_count") is None:
        return {"score": 50.0, "evidence": [], "verdict": "待赛道搜索数据",
                "degraded": True,
                "missing": "track_competition #需全量数据(赛道蓝海度·搜索结果密度)"}
    rc = int(tc.get("result_count") or 0)
    has_more = bool(tc.get("has_more"))
    kw = tc.get("keyword") or "行业词"

    # 结果密度：0 结果→蓝海满分·18 满页→红海低分
    s_density = _clamp((1 - min(rc, 18) / 18) * 100)
    # 海量信号
    s_more = 30.0 if has_more else 100.0
    s = round(_clamp(s_density * 0.6 + s_more * 0.4))

    if s >= 70:
        verdict = "蓝海(竞争稀疏·有先发机会窗口)"
        window = "建议加速卡位·内容供给不足"
    elif s >= 45:
        verdict = "平衡(竞争适中)"
        window = "差异化定位可突围"
    else:
        verdict = "红海(竞争饱和)"
        window = "需强差异化或细分长尾切入"

    evidence = [
        f"搜索'{kw}':当页 {rc} 条结果·{'有更多(海量竞争)' if has_more else '无更多页'}"]
    return {"score": s, "keyword": kw, "result_count": rc, "has_more": has_more,
            "evidence": evidence, "verdict": verdict, "window": window,
            "degraded": False}


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

    # 2. 粉-观年龄错位（双画像同维比对·破圈方向）
    age_gap = _portrait_mismatch(xprof, _OT_AGE, "年龄")
    s_age_gap = age_gap["score"]
    if age_gap.get("degraded"):
        missing.append(age_gap["missing"])

    # 3. 粉-观地域错位（省份维）
    geo_gap = _portrait_mismatch(xprof, _OT_PROVINCE, "省份")
    s_geo_gap = geo_gap["score"]
    if geo_gap.get("degraded"):
        missing.append(geo_gap["missing"])

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

    # 破圈方向汇总（向哪类人群破圈）
    directions = []
    for g in (age_gap, geo_gap):
        if not g.get("degraded") and g.get("breakout_to"):
            directions.append(g["breakout_to"])

    return {"score": score, "type": breakout_type,
            "age_mismatch": age_gap, "geo_mismatch": geo_gap,
            "breakout_directions": directions, "missing": missing}


# ── C6 子项算法：粉-观画像错位（破圈方向） ───────────────────────────────────

def _portrait_mismatch(xprof, origin_type: int, dim_name: str) -> dict[str, Any]:
    """粉丝画像 vs 观众画像同维错位度(0-100·错位越大破圈分越高)。

    fans_portrait(粉丝) vs audience_portrait(实际观看者) 同 origin_type 维。
    错位 = 两分布的 L1 距离(各 key 占比差绝对值和 / 2·范围 0-1)。
    多维：
      分布错位度  L1 距离·越大说明观众≠粉丝(破圈)        权重 0.7
      top1 异同   top1 人群是否切换                       权重 0.3
    破圈方向 = 观众侧占比显著高于粉丝侧的 top 人群。
    返回 {score, l1_distance, fans_top, aud_top, breakout_to, evidence, verdict}。
    """
    fans = _portrait_dim(xprof, "fans_portrait", origin_type)
    aud = _portrait_dim(xprof, "audience_portrait", origin_type)
    if not fans or not aud:
        return {"score": 50.0, "evidence": [], "verdict": f"待双画像({dim_name})",
                "degraded": True,
                "missing": f"fans_portrait/audience_portrait.{dim_name} #需全量数据({dim_name}错位)"}

    fan_map = {k: v for k, v in fans}
    aud_map = {k: v for k, v in aud}
    keys = set(fan_map) | set(aud_map)
    # L1 距离(占比差·百分比→0-1)
    l1 = sum(abs(fan_map.get(k, 0) - aud_map.get(k, 0)) for k in keys) / 200.0
    l1 = min(l1, 1.0)
    s_dist = _clamp(_score_range(l1, 0.05, 0.5))

    fans_top = fans[0][0]
    aud_top = aud[0][0]
    top_switch = fans_top != aud_top
    s_top = 100.0 if top_switch else 20.0

    s = round(_clamp(s_dist * 0.7 + s_top * 0.3))

    # 破圈方向：观众占比 - 粉丝占比 最大正差的人群
    gains = sorted(((k, aud_map.get(k, 0) - fan_map.get(k, 0)) for k in keys),
                   key=lambda t: -t[1])
    breakout_to = None
    if gains and gains[0][1] > 3:  # 观众侧高出>3pct 才算方向
        breakout_to = f"{dim_name}:{gains[0][0]}(+{gains[0][1]:.0f}pct)"

    evidence = [f"{dim_name} 粉丝top={fans_top}·观众top={aud_top}·分布错位 L1={l1:.2f}"]
    if breakout_to:
        evidence.append(f"破圈方向→{breakout_to}")
    if top_switch:
        verdict = f"{dim_name}破圈(观众主力≠粉丝主力)"
    elif l1 > 0.25:
        verdict = f"{dim_name}部分外溢(top一致但结构偏移)"
    else:
        verdict = f"{dim_name}精准(观众≈粉丝)"

    return {"score": s, "l1_distance": round(l1, 2), "fans_top": fans_top,
            "aud_top": aud_top, "top_switch": top_switch, "breakout_to": breakout_to,
            "evidence": evidence, "verdict": verdict, "degraded": False}


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

    # 3. 私域意图评论率（comment_deep.top_keywords 命中私域意图词）
    intent = _private_intent(account)
    s_intent = intent["score"]
    if intent.get("degraded"):
        missing.append(intent["missing"])

    # 4. 城市集中度（私域偏好本地集中·星图城市维 origin_type=8）
    city = _portrait_dim(xprof, "fans_portrait", _OT_CITY)
    if city:
        hhi_city = _herfindahl(city)
        if hhi_city is not None:
            # 私域：城市集中(HHI高)反而利于本地社群·正向映射
            s_city = _clamp(_score_range(hhi_city, 0.05, 0.4))
        else:
            s_city = 50.0
    else:
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

    return {"score": score, "path": path, "private_intent": intent, "missing": missing}


# ── C8 子项算法：私域意图评论率 ──────────────────────────────────────────────

# 私域意图词典(分类·命中即计私域意图评论)。⚠️词典待按行业扩充校准。
_INTENT_LEXICON = {
    "导流加微": ["加微", "微信", "vx", "v信", "威信", "+v", "薇信", "联系方式", "怎么联系"],
    "咨询购买": ["怎么买", "哪里买", "多少钱", "价格", "链接", "求购", "想要", "下单", "购买",
                "怎么卖", "店铺", "橱窗"],
    "求课求教": ["求教程", "教程", "课程", "报名", "怎么学", "求带", "拜师", "想学"],
    "私信意向": ["私信", "发我", "扣1", "扣我", "求", "蹲", "想问"],
}


def _private_intent(account: dict[str, Any]) -> dict[str, Any]:
    """私域意图评论率(0-100)·comment_deep.top_keywords 命中私域意图词。

    top_keywords = [{word,count}]（account.py 中文 n-gram 高频词·频次≥2）。
    多维：
      意图词覆盖   命中意图词的去重词数 / top 词数               权重 0.5
      意图词词频   命中词总频次 / 全部 top 词频次                权重 0.5
    分类拆分(导流加微/咨询购买/求课求教/私信意向)·导流加微权重最高。
    返回 {score, hit_categories, hit_words, intent_ratio, evidence, verdict}。
    ⚠️词典与阈值待真实评论样本校准。
    """
    cd = _comment_deep(account)
    if not cd or not cd.get("top_keywords"):
        return {"score": 40.0, "evidence": [], "verdict": "待评论关键词",
                "degraded": True,
                "missing": "comment_deep.top_keywords #需全量数据(私域意图评论率)"}
    kws = cd["top_keywords"]
    total_words = len(kws)
    total_freq = sum(int(k.get("count") or 0) for k in kws) or 0

    hit_words: list[dict] = []
    hit_categories: dict[str, int] = {}
    hit_freq = 0
    for k in kws:
        w = str(k.get("word") or "")
        ct = int(k.get("count") or 0)
        for cat, lex in _INTENT_LEXICON.items():
            if any(token in w for token in lex):
                hit_words.append({"word": w, "count": ct, "category": cat})
                hit_categories[cat] = hit_categories.get(cat, 0) + 1
                hit_freq += ct
                break

    if total_words == 0:
        return {"score": 40.0, "evidence": [], "verdict": "评论无高频词",
                "degraded": True,
                "missing": "comment_deep.top_keywords #需全量数据(私域意图评论率)"}

    cover = len(hit_words) / total_words
    freq_ratio = (hit_freq / total_freq) if total_freq else 0.0
    base = (_clamp(cover * 100) * 0.5 + _clamp(freq_ratio * 100) * 0.5)
    # 导流加微出现 → 强私域信号·加成
    if "导流加微" in hit_categories:
        base = min(base + 15, 100)
    s = round(_clamp(base))

    cats = "·".join(f"{c}×{n}" for c, n in hit_categories.items()) or "无"
    evidence = [
        f"top{total_words}高频词命中私域意图 {len(hit_words)} 个(覆盖 {cover * 100:.0f}%·"
        f"词频占 {freq_ratio * 100:.0f}%)·分类:{cats}"]
    if hit_words:
        evidence.append("命中词:" + "、".join(
            f"{h['word']}({h['count']})" for h in hit_words[:5]))

    if "导流加微" in hit_categories or s >= 60:
        verdict = "强私域意图(评论区有主动加微/购买诉求)"
    elif s >= 35:
        verdict = "中等私域意图(有咨询/求教倾向)"
    else:
        verdict = "弱私域意图(评论以泛互动为主)"

    return {"score": s, "hit_categories": hit_categories, "hit_words": hit_words,
            "intent_ratio": round(cover, 2), "freq_ratio": round(freq_ratio, 2),
            "evidence": evidence, "verdict": verdict, "degraded": False}


# ── 汇总接口 ──────────────────────────────────────────────────────────────────

# ══ C9-C13：MetaIntake L0 环境层 + 批A 粉丝洞察驱动的环境/机会类指标 ══════════
# 数据源: account 由 _parse_intake_extras 注入(hot_topic/hot_words/creator_hotspot/
#         fans_interest_*/mission_task/acc_item_analysis)。空维度 graceful 降级。


def _fmt_w(n) -> str:
    """粉丝数 → 万 缩写。"""
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "?"
    return f"{n / 10000:.1f}w" if n >= 10000 else str(int(n))


def _kw_tokens(text) -> set[str]:
    """中文文案/话题 → 2-4 gram token 集(粗匹配热点·无分词依赖)。"""
    if not text:
        return set()
    s = "".join(ch for ch in str(text) if "一" <= ch <= "鿿" or ch.isalnum())
    toks: set[str] = set()
    for n in (2, 3, 4):
        for i in range(len(s) - n + 1):
            toks.add(s[i:i + n])
    return toks


def _hot_hit(seed_tokens: set[str], names: list) -> list:
    """seed_tokens 命中 names(热点名列表) → 返回命中的热点名。"""
    return [nm for nm in names if nm and (seed_tokens & _kw_tokens(nm))]


def score_c9_hot_fit(account: dict[str, Any], xprof=None) -> dict[str, Any]:
    """C9 热点契合度(0-100)：视频话题/赛道 × 全局热点榜命中。
    踩中飙升榜=风口·命中热榜/热搜=蹭热点·全不中=偏离(小众未必差)。
    """
    # 种子只用话题标签+行业标签(提炼词)·不用 desc 全文(2-gram 噪音误撞热榜)
    seeds: set[str] = set()
    for h in (account.get("video_hashtags") or []):
        seeds |= _kw_tokens(h)
    for t in (_xattr(xprof, "industry_tags") or []):
        seeds |= _kw_tokens(t)

    cur = [x.get("name") for x in (account.get("hot_topics_current") or [])]
    roc = [x.get("name") for x in (account.get("hot_topics_rocketing") or [])]
    words = [x.get("word") for x in (account.get("hot_words") or [])]
    if not (cur or roc or words):
        return {"score": 50.0, "verdict": "待 L0 热点数据", "evidence": [],
                "degraded": True, "missing": "hot_topic/hot_words #需L0环境层"}
    if not seeds:
        return {"score": 40.0, "verdict": "无视频话题种子·无法匹配热点",
                "evidence": [], "degraded": False, "missing": []}

    hit_roc = _hot_hit(seeds, roc)
    hit_cur = _hot_hit(seeds, cur)
    hit_word = _hot_hit(seeds, words)
    raw = len(hit_roc) * 40 + len(hit_cur) * 20 + len(hit_word) * 15
    score = round(_clamp(min(100, raw) if raw else 25.0))
    if hit_roc:
        verdict = f"踩中飙升风口({len(hit_roc)}个)"
    elif hit_cur or hit_word:
        verdict = "蹭到当前热点"
    else:
        verdict = "偏离热点(小众赛道或选题保守)"
    ev = []
    if hit_roc:
        ev.append("飙升榜命中:" + " ".join(hit_roc[:3]))
    if hit_cur:
        ev.append("热榜命中:" + " ".join(hit_cur[:3]))
    if hit_word:
        ev.append("热搜词命中:" + " ".join(hit_word[:3]))
    if not ev:
        tags = account.get("video_hashtags") or []
        ev.append(f"视频话题「{'·'.join(tags[:3]) or '无'}」未命中当前热榜/飙升/热搜")
    return {"score": score, "verdict": verdict, "evidence": ev,
            "hit_rocketing": hit_roc, "hit_current": hit_cur, "missing": []}


def score_c10_topic_opp(account: dict[str, Any], xprof=None) -> dict[str, Any]:
    """C10 选题机会(0-100)：创作者热点榜(赛道匹配·上升) + 粉丝搜索词(未满足需求)。
    输出可直接拍的选题方向。
    """
    hotspots = account.get("creator_hotspots") or []
    searches = account.get("fans_interest_searches") or []
    if not hotspots and not searches:
        return {"score": 50.0, "verdict": "待选题数据", "evidence": [], "topics": [],
                "degraded": True, "missing": "creator_hotspot/fans_interest_search #需L0+批A"}

    track_tokens: set[str] = set()
    for t in (_xattr(xprof, "industry_tags") or []):
        track_tokens |= _kw_tokens(t)
    for h in (account.get("video_hashtags") or []):
        track_tokens |= _kw_tokens(h)

    # rank_diff 实测常为0·按 hot_score 排序取热点·diff>0 仅作上升标注
    ranked = sorted([h for h in hotspots if (h.get("score") or 0) > 0],
                    key=lambda h: -(h.get("score") or 0))
    matched = [h for h in ranked
               if track_tokens and (_kw_tokens(h.get("cat") or "") & track_tokens)]
    def _tp(h):
        up = f"·↑{h['diff']}" if (h.get("diff") or 0) > 0 else ""
        return f"{h.get('cat')}(热度{h.get('score')}{up})"
    # 全局热点多为泛大类(旅行/财经)·只推赛道匹配的·避免给垂类账号推无关大类
    topics = [_tp(h) for h in matched[:5]]

    top_search = sorted(searches, key=lambda x: -(x.get("hot") or 0))[:8]
    fan_words = [s.get("word") for s in top_search if s.get("word")]

    raw = len(matched) * 15 + min(len(fan_words), 20) * 3 + (20 if ranked else 0)
    score = round(_clamp(min(100, raw) if (ranked or fan_words) else 30.0))
    verdict = (f"{len(matched)}个赛道内选题机会" if matched
               else f"{len(ranked)}个全局热点·{len(fan_words)}个粉丝搜索需求")
    ev = []
    if topics:
        ev.append("推荐选题:" + " / ".join(topics[:3]))
    if fan_words:
        ev.append("粉丝在搜:" + " ".join(fan_words[:5]))
    return {"score": score, "verdict": verdict, "evidence": ev,
            "topics": topics, "fan_searches": fan_words, "missing": []}


def score_c11_fans_insight(account: dict[str, Any], xprof=None) -> dict[str, Any]:
    """C11 粉丝洞察深度(0-100)：粉丝同关账号+搜索词+兴趣话题的可挖掘度。
    深度=能挖出多少可行动信息(竞品/需求)。
    """
    accts = account.get("fans_interest_accounts") or []
    searches = account.get("fans_interest_searches") or []
    topics = account.get("fans_interest_topics") or []
    if not (accts or searches or topics):
        return {"score": 40.0, "verdict": "粉丝洞察数据空(粉丝量小或风控)",
                "evidence": [], "degraded": True,
                "missing": "fans_interest_* #需批A粉丝洞察"}

    dims = sum(1 for x in (accts, searches, topics) if x)
    raw = len(accts) * 3 + min(len(searches), 30) * 1.5 + dims * 10
    score = round(_clamp(min(100, raw)))
    top_acct = sorted(accts, key=lambda x: -(x.get("fans") or 0))[:5]
    top_search = sorted(searches, key=lambda x: -(x.get("hot") or 0))[:6]
    ev = []
    if top_acct:
        ev.append("粉丝还关注:" + " ".join(
            f"{a.get('name')}({_fmt_w(a.get('fans'))})" for a in top_acct[:4]))
    if top_search:
        ev.append("粉丝搜索需求:" + " ".join(s.get("word") for s in top_search if s.get("word")))
    verdict = f"{dims}/3维可洞察·{len(accts)}同关账号·{len(searches)}搜索词"
    return {"score": score, "verdict": verdict, "evidence": ev,
            "competitor_accounts": top_acct, "missing": []}


def score_c12_monetize(account: dict[str, Any], xprof=None) -> dict[str, Any]:
    """C12 变现机会(0-100)：商单生态密度 + 账号互动对标 + 星图报价/带货指数。"""
    mission = account.get("mission_total")
    bench = account.get("item_benchmark") or {}
    lsi = _idx(xprof, "link_shopping_index", "avg_value")
    has_price = bool(_xattr(xprof, "price_info"))
    if mission is None and not bench and lsi is None:
        return {"score": 50.0, "verdict": "待变现数据", "evidence": [],
                "degraded": True, "missing": "mission_task/acc_item_analysis #需批A+L3"}

    parts, ev = [], []
    if mission is not None:
        parts.append(_clamp(min(100, mission * 2)))
        ev.append(f"可接商单 {mission} 个" if mission
                  else "当前无可接商单(赛道商单稀疏或账号未达准入)")
    my_like, bench_like = account.get("avg_like"), bench.get("avg_like")
    if bench_like and my_like:
        ratio = my_like / bench_like
        parts.append(_clamp(min(100, ratio * 50)))
        ev.append(f"赞均值 {my_like:.0f} vs 同类 {bench_like:.0f}"
                  f"({'高' if ratio >= 1 else '低'}于均值 {ratio:.1f}x)")
    if lsi is not None:
        parts.append(_clamp(float(lsi)))
        ev.append(f"星图带货指数 {float(lsi):.0f}")
    if has_price:
        ev.append("已有星图报价(可商接)")

    score = round(_clamp(sum(parts) / len(parts))) if parts else 50.0
    verdict = ("变现就绪(有报价+承接力)" if has_price and score >= 60
               else "变现潜力中等" if score >= 45 else "变现待培育")
    return {"score": score, "verdict": verdict, "evidence": ev, "missing": []}


def score_c13_competitor_pos(account: dict[str, Any], xprof=None) -> dict[str, Any]:
    """C13 竞品位置(0-100)：粉丝同关账号(竞品)粉丝量对标 + 互动 vs 赛道均值。
    输出账号在赛道的相对位置(领先/腰部/追赶)。
    """
    comps = account.get("fans_interest_accounts") or []
    bench = account.get("item_benchmark") or {}
    my_fans = account.get("follower")
    if not comps and not bench:
        return {"score": 50.0, "verdict": "待竞品数据", "evidence": [], "competitors": [],
                "degraded": True, "missing": "fans_interest_account/acc_item_analysis #需批A"}

    parts, ev = [], []
    comp_fans = [c.get("fans") for c in comps if c.get("fans")]
    if comp_fans and my_fans:
        below = sum(1 for f in comp_fans if f < my_fans)
        pct = below / len(comp_fans) * 100
        parts.append(_clamp(pct))
        pos = "领先" if pct >= 66 else "跟随" if pct >= 33 else "落后"
        ev.append(f"粉丝量超过 {below}/{len(comp_fans)} 同关竞品({pos}·{pct:.0f}%位)")
    my_like, bench_like = account.get("avg_like"), bench.get("avg_like")
    if bench_like and my_like:
        ratio = my_like / bench_like
        parts.append(_clamp(min(100, ratio * 50)))
        ev.append(f"互动 {ratio:.1f}x 赛道均值")
    top_comp = sorted(comps, key=lambda x: -(x.get("fans") or 0))[:5]
    if top_comp:
        ev.append("主要竞品:" + " ".join(
            f"{c.get('name')}({_fmt_w(c.get('fans'))})" for c in top_comp[:4]))

    score = round(_clamp(sum(parts) / len(parts))) if parts else 50.0
    verdict = ("赛道领先" if score >= 66 else "赛道腰部" if score >= 40 else "赛道追赶")
    return {"score": score, "verdict": verdict, "evidence": ev,
            "competitors": top_comp, "missing": []}


def compute_all(account: dict[str, Any], xprof=None) -> dict[str, Any]:
    """一次性计算13个复合指标·返回 {c1..c13} 字典。

    C1-C8: 账号自身诊断(健康/粉丝/转化/内容/赛道/破圈/评级/私域)。
    C9-C13: MetaIntake 环境层驱动(热点契合/选题机会/粉丝洞察/变现/竞品位置)。
    """
    return {
        "c1": score_c1_health(account),
        "c2": score_c2_fans_quality(account, xprof),
        "c3": score_c3_commerce(account, xprof),
        "c4": score_c4_content(account, xprof),
        "c5": score_c5_track(account, xprof),
        "c6": score_c6_breakout(account, xprof),
        "c7": score_c7_grade(account, xprof),
        "c8": score_c8_private(account, xprof),
        "c9": score_c9_hot_fit(account, xprof),
        "c10": score_c10_topic_opp(account, xprof),
        "c11": score_c11_fans_insight(account, xprof),
        "c12": score_c12_monetize(account, xprof),
        "c13": score_c13_competitor_pos(account, xprof),
    }


# ── 报告段渲染 ────────────────────────────────────────────────────────────────

_GRADE_EMOJI = {"A": "🏆", "B": "✅", "C": "⚠️", "D": "🔴", "F": "❌"}


def render_composite_section(account: dict[str, Any], xprof=None) -> str:
    """串13个复合指标成 markdown 报告段·供 account_report 调用。"""
    r = compute_all(account, xprof)

    c1, c2, c3, c4 = r["c1"], r["c2"], r["c3"], r["c4"]
    c5, c6, c7, c8 = r["c5"], r["c6"], r["c7"], r["c8"]
    c9, c10, c11, c12, c13 = r["c9"], r["c10"], r["c11"], r["c12"], r["c13"]

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
        f"| C9 热点契合度 | **{c9['score']}分** | {c9['verdict']} |",
        f"| C10 选题机会 | **{c10['score']}分** | {c10['verdict']} |",
        f"| C11 粉丝洞察深度 | **{c11['score']}分** | {c11['verdict']} |",
        f"| C12 变现机会 | **{c12['score']}分** | {c12['verdict']} |",
        f"| C13 竞品位置 | **{c13['score']}分** | {c13['verdict']} |",
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

    # 深化子项洞察（仅渲染已接通真实数据·非降级的子项）
    insight_specs = [
        ("C2 水军风险", c2.get("bot_risk")),
        ("C2 评论层级真实性", c2.get("comment_realness")),
        ("C2 地域多元度", c2.get("geo_diversity")),
        ("C4 竞品互动差", c4.get("competitor_gap")),
        ("C5 赛道蓝海度", c5.get("blue_ocean")),
        ("C6 年龄破圈", c6.get("age_mismatch")),
        ("C6 地域破圈", c6.get("geo_mismatch")),
        ("C8 私域意图", c8.get("private_intent")),
    ]
    rendered = [(t, d) for t, d in insight_specs
                if isinstance(d, dict) and not d.get("degraded")]
    if rendered:
        lines.append("### 深化子项洞察（接通真实数据）")
        for title, d in rendered:
            sc = d.get("score")
            verdict = d.get("verdict", "")
            head = f"- **{title}** {sc}分 · {verdict}"
            lines.append(head)
            for ev in (d.get("evidence") or [])[:3]:
                lines.append(f"  - {ev}")
        # 破圈方向汇总
        dirs = c6.get("breakout_directions") or []
        if dirs:
            lines.append(f"- **破圈方向汇总**：{' / '.join(dirs)}")
        lines.append("")

    # MetaIntake 环境/机会洞察（C9-C13·接通真实环境数据才渲染）
    env_specs = [
        ("C9 热点契合", c9), ("C10 选题机会", c10), ("C11 粉丝洞察", c11),
        ("C12 变现机会", c12), ("C13 竞品位置", c13),
    ]
    env_rendered = [(t, d) for t, d in env_specs
                    if isinstance(d, dict) and not d.get("degraded") and d.get("evidence")]
    if env_rendered:
        lines.append("### 环境/机会洞察（MetaIntake 环境层）")
        for title, d in env_rendered:
            lines.append(f"- **{title}** {d.get('score')}分 · {d.get('verdict', '')}")
            for ev in (d.get("evidence") or [])[:3]:
                lines.append(f"  - {ev}")
        lines.append("")

    # 降级说明汇总
    all_missing: list[str] = []
    for k in ("c1", "c2", "c3", "c4", "c5", "c6", "c8",
              "c9", "c10", "c11", "c12", "c13"):
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
