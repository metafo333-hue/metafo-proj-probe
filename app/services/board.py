"""元板 · 四层下钻数据板块 (MetaBoard)。

把已落地的 14 复合指标(composite_scores) + 4 诊断卡(diagnosis_cards) + 星图
(xingtu_profile) + L0 环境层(l0_environment) 重新组织成「环境 → 行业 → 账号 →
单条」四级坐标下钻视图,并附「算账」层(每层成本 + 全局 ROI)。

承 v3.2 短视频商业转化方案「骨·四级坐标」(环境/行业/账号/单条) + 算账视角:
  · 输出层次 = 四级坐标 zoom(从大盘到单条)
  · 每层独立算账(这层花多少 / 得什么 / 值在哪)
  · 一句话结论前置(最高 severity 卡)·处方 <=3 条
  · 成本/价值错位是定价合理性的核心(环境≈0/账号最贵/单条最便宜但高频)

本模块不重算任何指标,只做「组织 + 算账 + 分层渲染」,数据全部读自既有服务。
"""
from __future__ import annotations

from typing import Any

from app.services import composite_scores, diagnosis_cards, l0_environment

# ── 真实实测单价(2026-06-22 · $1=¥7.3)─────────────────────────────────────────
# 来源:运营报告/probe-tikhub-cost-time-statistics-v1.0.md(13次API实扣)。
# 按四级坐标做诚实成本归因(总和 ≈ ¥1.07 开星图 / ¥0.044 无星图)。
_RATE = 7.3
COST_LAYER_YUAN = {
    "env": 0.0073,       # ① 环境:热搜/billboard 共享缓存·跨账号摊薄≈0
    "industry": 0.146,   # ② 行业:星图指数(rank_percent)·2 端点
    "account": 0.876,    # ③ 账号:星图全量(报价/画像/完成率)+ 基础画像·成本主体
    "video": 0.044,      # ④ 单条:基础采集(video/stats/comments/posts)
}
COST_NO_XINGTU_YUAN = 0.044   # 无星图账号:只有基础采集
COST_CACHE_YUAN = 0.0         # 当日复诊:全缓存命中

# ROI 等效价值(运营报告 ROI 账·让用户感知"赚了")
ROI_EQUIV = {
    "manual_hours": 4,           # 等效手动分析工时
    "expert_review": "3 位运营会诊一轮",
    "outsource_yuan": "500-2000",
}

_SEV_RANK = {"red": 3, "yellow": 2, "green": 1, None: 0}


def _g(d: dict | None, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
    return default if cur is None else cur


# ══════════════════════════════════════════════════════════════════════════════
# 四层下钻组装
# ══════════════════════════════════════════════════════════════════════════════

def build_board(account: dict[str, Any], xprof: Any = None, *,
                cache_hit: bool = False,
                scores: dict | None = None,
                cards: dict | None = None) -> dict[str, Any]:
    """组装四级坐标下钻板块 + 算账层。

    Args:
        account: _build_account_for_diagnosis 产出的 account dict。
        xprof:   xprof_adapter dict(开星图)或 None。
        cache_hit: 是否当日复诊全缓存命中(算账用)。
        scores:  预算好的 compute_all 结果(省一次重算);None 则现算。
        cards:   预算好的 4 卡;None 则现算。
    Returns:
        {headline, layers:{env,industry,account,video}, accounting, raw:{scores,cards}}
    """
    is_xingtu = xprof is not None
    s = scores or composite_scores.compute_all(account, xprof)
    c = cards or {
        "churn": diagnosis_cards.diagnose_churn(account),
        "pricing": diagnosis_cards.diagnose_pricing(account, xprof),
        "funnel": diagnosis_cards.diagnose_funnel(account),
        "track": diagnosis_cards.diagnose_track(account, xprof),
    }

    from app.services import deep_analysis, stage_journey, basics_judge, content_causal
    deep = deep_analysis.build_deep(account, xprof, s)
    heading = deep_analysis.growth_heading(account, s)   # 阶段1 航向(你是什么→成为什么)
    journey = stage_journey.build_journey(account, deep)  # 运营阶段旅程(阶段×维度矩阵+链条)
    basics_j = basics_judge.judge_basics(account)         # 基础数据档位标尺(指令1)
    causal = content_causal.build_causal(                 # 内容→口碑→势能因果链(指令2)
        account.get("content_dna"), account.get("content_attribution"),
        account.get("sentiment_evolution"), account.get("time_series"),
        account.get("acceleration"))

    layers = {
        "env": _layer_env(account, s, deep),
        "industry": _layer_industry(account, xprof, s, is_xingtu, deep),
        "account": _layer_account(account, xprof, s, c, is_xingtu, deep),
        "video": _layer_video(account, s, deep),
    }
    accounting = _accounting(is_xingtu, cache_hit)
    # 层成本对齐实际归因(无星图→②③层失败不扣费;复诊→全 0)。
    # list_price_yuan 保留满价(开星图)作参照·cost_yuan 反映本次实扣。
    actual = accounting["per_layer_yuan"]
    for k, ly in layers.items():
        ly["list_price_yuan"] = COST_LAYER_YUAN[k]
        ly["cost_yuan"] = actual.get(k, COST_LAYER_YUAN[k])
    headline = _headline(c, s, deep)
    return {
        "nickname": account.get("nickname"),
        "headline": headline,
        "layers": layers,                                  # v1.3 四级坐标(保留·供对比)
        "journey": journey,                               # 运营阶段旅程(阶段×维度矩阵+链条)
        "basics": {                                       # 账号基础数据原值(指令3)
            "nickname": account.get("nickname"), "signature": account.get("signature"),
            "unique_id": account.get("unique_id"), "ip_location": account.get("ip_location"),
            "custom_verify": account.get("custom_verify"),
            "enterprise_verify": account.get("enterprise_verify_reason"),
            "follower": account.get("follower"), "max_follower": account.get("max_follower"),
            "aweme_count": account.get("aweme_count"),
            "total_favorited": account.get("total_favorited"),
            "following_count": account.get("following_count"),
            "avg_like": account.get("avg_like"), "max_like": account.get("max_like"),
            "burst_ratio": account.get("burst_ratio"),
            "update_gap_days": account.get("update_gap_days"),
            "vertical_score": account.get("vertical_score"),
        },
        "basics_judge": basics_j,                         # 基础数据档位标尺(判断+依据·指令1)
        "basics_summary": basics_judge.summary(basics_j),
        "causal": causal,                                 # 内容→口碑→势能因果链(指令2)
        "ladders": build_ladders(account, s, c, deep, headline, heading),  # v2.0 价值四阶梯
        "accounting": accounting,
        "data_coverage": _data_coverage(account, deep),   # 采集/展示/空 诚实账
        "raw": {"scores": s, "cards": c},
    }


# ══════════════════════════════════════════════════════════════════════════════
# v2.0 价值四阶梯(描述→诊断→处方→预测)·把同一份数据按"用户要什么"重投
# 不重算·全部读自 headline/scores/cards/deep + account.time_series。
# ══════════════════════════════════════════════════════════════════════════════

def build_ladders(account: dict, s: dict, c: dict, deep: dict,
                  headline: dict, heading: dict | None = None) -> dict[str, Any]:
    deep = deep or {}
    di = deep.get("industry") or {}
    track = di.get("track_tier") or {}
    stage = di.get("fan_stage") or {}
    sc = headline.get("strategic_call") or {}
    tc = headline.get("top_concern") or {}
    au = deep.get("audience") or {}
    ts = account.get("time_series") or {}
    rx = (account.get("content_dna") or {}).get("next_video_rx") or {}

    # ── 阶梯1 定位+航向(你是什么 → 该往哪 → 成为什么)point6 ──
    heading = heading or {}
    ladder1 = {
        "rung": 1, "name": "定位航向", "question": "你是什么·该成为什么",
        "moat": "竞品也能做",
        "conclusion": (f"{track.get('name', '赛道待定')}·{stage.get('stage', '')}·"
                       f"{account.get('follower', '?')}粉"),
        "heading": {                              # 三段论述:现状→航向→终态
            "now": heading.get("now"),
            "direction": heading.get("direction"),
            "endstate": heading.get("endstate"),
            "logic": heading.get("logic", []),
        },
        "details": [
            f"赛道分型:{track.get('tier', '?')}档·{track.get('name', '')}·"
            f"单粉价值 {track.get('value_per_fan', '—')}",
            f"生命周期:{stage.get('stage', '')}·本期任务={stage.get('task', '')}",
            f"该玩:{track.get('game', '—')}({'线索游戏' if track.get('is_b2b_leads') else '流量游戏'})",
        ],
        "milestone": account.get("milestone"),    # 里程碑(粉丝→权益·距下一档)
        "identity": _identity(account),            # 形象一致性审计(资料全采+自我匹配)
        "source": heading.get("source") or track.get("source", ""),
    }

    # ── 阶梯2 诊断(为什么这样)──
    ladder2 = {
        "rung": 2, "name": "诊断", "question": "为什么这样",
        "moat": "竞品部分能做",
        "conclusion": (f"健康 {_g(s, 'c1', 'score')}({_g(s, 'c7', 'grade')}级)·"
                       f"商业转化 {_g(s, 'c3', 'score')}·"
                       f"{(account.get('engagement_structure') or {}).get('nature', '')}"),
        "deep_health": deep.get("health"),
        "deep_commerce": deep.get("commerce"),
        "attribution": account.get("content_attribution"),  # 矿脉②:哪个数据因子驱动互动
        "hot_comments": account.get("hot_comments"),         # 热评TOP(采了没接·补)
        "comment_clusters": account.get("comment_clusters"), # 评论聚类(非LLM·补)
        "engagement_anomaly": account.get("engagement_anomaly"),  # 互动操纵异常(补强④)
        "engagement_structure": account.get("engagement_structure"),  # 互动结构(评/藏/转比)
        "chain": _diag_chain(account, s, deep),              # 诊断链(流量→互动→口碑→转化→真实)
        "top_concern": tc,
        "radar": _radar(s),
        "details": [_card_brief(c.get("churn")), _card_brief(c.get("pricing")),
                    _card_brief(c.get("track"))],
    }

    # ── 阶梯3 处方(该怎么做)·双层:前端三级人话 + 后端 cut 命令(point4)──
    from app.services import cut_director
    rx_steps = rx.get("steps") or []
    rx_pkg = cut_director.build_prescription(account, deep)
    ladder3 = {
        "rung": 3, "name": "处方", "question": "该怎么做",
        "moat": "竞品做不到",
        "conclusion": sc.get("call", "—"),
        "strategic_why": sc.get("why"),
        "strategic_color": sc.get("color"),
        "this_week": rx_steps[:3],            # 本周≤3件
        "next_video": rx_steps,
        "audience_intent": au.get("intent_signal"),
        "audience_implication": au.get("implication"),
        "front": rx_pkg["front"],             # 前端三级层级(战略/战术/执行)
        "cut_commands": rx_pkg["cut_commands"],  # 后端 MetaCut 执行命令
    }

    # ── 阶梯4 预测(做了/接下来会怎样)──
    ladder4 = {
        "rung": 4, "name": "预测", "question": "接下来会怎样",
        "moat": "★ 护城河·竞品做不到",
        "enough": ts.get("enough", False),
        "conclusion": (ts.get("verdict") if ts.get("enough")
                       else (ts.get("verdict") or "时序数据积累中")),
        "stage": ts.get("stage"),
        "trend": ts.get("trend"),
        "rhythm": ts.get("rhythm"),
        "decay": ts.get("decay"),
        "next_estimate": ts.get("next_estimate"),
        "rx_eta": ts.get("rx_eta"),
        "conf": ts.get("conf"),
        "sentiment_evo": account.get("sentiment_evolution"),  # 矿脉③:口碑演化(先行信号)
        "acceleration": account.get("acceleration"),          # 轨迹二阶导(势能加速/放缓)
        # 需多次采集才算的那半·诚实标"积累中"
        "trajectory_pending": "账号涨粉轨迹/处方前后真实对照·需多次采集存历史(积累中)",
    }

    return {"l1": ladder1, "l2": ladder2, "l3": ladder3, "l4": ladder4}


def _data_coverage(account: dict, deep: dict) -> dict:
    """数据覆盖诚实账:采集了哪些·展示了哪些·哪些空(及原因)。"""
    ex = (deep or {}).get("extra_meta") or {}
    # 新接入并有数据展示的扩展信号
    shown = [name for name, key in [
        ("官方评论热词", "official_comment_words"), ("算法竞品", "related_competitors"),
        ("上升热点", "env_rising"), ("实时热搜", "env_hot_search"),
        ("热门挑战", "env_challenges"), ("平台选题洞察", "topic_insights"),
        ("热门配乐", "hot_music"), ("粉丝分布", "fan_distribution")]
        if ex.get(key)]
    return {
        "new_signals_shown": shown,
        "empty_this_account": [{"ep": e, "reason": r} for e, r in ex.get("_empty", [])],
        "redundant_or_niche": [{"ep": e, "reason": r} for e, r in ex.get("_redundant", [])],
        "note": "本轮把「采集了但没展示」的端点全部接入·有数据的组合输出·"
                "空返回的诚实标原因·不编造。",
    }


# ── ① 环境层(大盘风向)·成本≈0·价值=方向感 ────────────────────────────────────
def _layer_env(account: dict, s: dict, deep: dict | None = None) -> dict:
    l0 = l0_environment.build_l0_environment(
        account,
        track=_g(account, "track_competition", "keyword") or account.get("industry_tag"),
        hot_topics=account.get("hot_topics_related"))
    c9 = s.get("c9") or {}
    c14 = s.get("c14") or {}
    return {
        "coord": "① 环境",
        "zoom": "最大盘 · 舆情/热点/赛道温度",
        "user_question": "我这行现在什么温度?该追什么风口?",
        "cost_yuan": COST_LAYER_YUAN["env"],
        "value": "方向感——避免逆风做内容",
        "level": "描述级",
        "subject_tier": _g(l0, "position_in_track", "subject_tier"),
        "hot_fit": {"score": c9.get("score"), "verdict": c9.get("verdict"),
                    "hit_current": c9.get("hit_current")},
        "dark_horse": {"score": c14.get("score"), "verdict": c14.get("verdict")},
        "gaps": _g(l0, "data_source_meta", "gaps", default=[]),
        "deep": (deep or {}).get("env"),     # ①环境层五段式深度
        "env_hot": (deep or {}).get("env_hot"),   # 大盘热点深化(hot_rise/total/challenge/insight)
    }


# ── ② 行业层(赛道身位)·成本¥0.02·价值=定位 ──────────────────────────────────
def _layer_industry(account: dict, xprof: Any, s: dict, is_xingtu: bool,
                    deep: dict | None = None) -> dict:
    c5 = s.get("c5") or {}
    rank_pct = composite_scores._idx(xprof, "link_shopping_index", "rank_percent")
    # #6 诚实降级:无星图→商业分位取不到·明说·别留空让用户以为系统没算
    if is_xingtu and rank_pct is not None:
        status = "完整(开星图)"
        rank_txt = rank_pct
    else:
        status = "未开星图·行业商业分位取不到(需星图授权)·下方为可见数据估算"
        rank_txt = None
    return {
        "coord": "② 行业",
        "zoom": "赛道盘 · 你在赛道里排第几",
        "user_question": "我在赛道里排第几?这赛道值不值得深耕?",
        "cost_yuan": COST_LAYER_YUAN["industry"],
        "value": "定位——头部/腰部/长尾 + 赛道天花板",
        "level": "诊断级",
        "star_status": status,
        "track_keyword": c5.get("keyword"),
        "track_verdict": c5.get("verdict"),         # C5 赛道蓝海·无星图也能算(走搜索)
        "track_window": c5.get("window"),
        "blue_ocean_score": c5.get("score"),
        "industry_rank_percent": rank_txt,           # 行业商业分位(仅星图真值)
        "deep": (deep or {}).get("industry"),        # 赛道分型+身位+该玩什么游戏(五段式)
        "competitor": (deep or {}).get("competitor"),  # 竞品雷达(算法关联+粉丝同关)
    }


# ── ③ 账号层(你的身价)·成本¥1.07·价值最高 ──────────────────────────────────
def _layer_account(account: dict, xprof: Any, s: dict, c: dict,
                   is_xingtu: bool, deep: dict | None = None) -> dict:
    c1, c2, c3 = s.get("c1") or {}, s.get("c2") or {}, s.get("c3") or {}
    c6, c7, c8 = s.get("c6") or {}, s.get("c7") or {}, s.get("c8") or {}
    c12 = s.get("c12") or {}
    # #6 诚实:无星图→报价/真粉丝画像/商业指数取不到·但健康/粉丝质量/内容/私域仍可算
    status = ("完整(开星图·含报价/真画像/商业指数)" if is_xingtu else
              "未开星图·商业身价(报价/真画像)取不到·以下为可见数据诊断(健康/粉丝/内容/私域)")
    return {
        "coord": "③ 账号",
        "zoom": "主体盘 · 账号资产负债表",
        "user_question": "我这号值多少钱?健康吗?能接多大广告?",
        "cost_yuan": COST_LAYER_YUAN["account"],
        "value": "身家底——商业身价/健康/掉粉预警/真实带货力",
        "level": "诊断+处方级",
        "star_status": status,
        "health": {"score": c1.get("score"), "phase": c1.get("phase")},
        "grade": {"grade": c7.get("grade"), "desc": c7.get("desc"), "score": c7.get("score")},
        "fans_quality": {"score": c2.get("score")},
        "commerce": {"score": c3.get("score"), "path": c3.get("path")},
        "breakout": {"score": c6.get("score"), "verdict": c6.get("verdict")},
        "private": {"score": c8.get("score")},
        "monetize": {"score": c12.get("score"), "verdict": c12.get("verdict")},
        # 账号层挂 3 张诊断卡(账号主体级问题)
        "cards": {
            "churn": _card_brief(c.get("churn")),
            "pricing": _card_brief(c.get("pricing")),
            "track": _card_brief(c.get("track")),
        },
        "radar": _radar(s),   # 14 指标雷达(全景一眼看)
        "deep_health": (deep or {}).get("health"),      # 健康分五段式拆解
        "deep_commerce": (deep or {}).get("commerce"),  # 商业转化为什么这个分(纠赛道误判)
        "audience": (deep or {}).get("audience"),       # 受众洞察(评论热词+粉丝分布+采购意向)
    }


# ── ④ 单条层(每条决策)·成本¥0.001·复利发动机 ──────────────────────────────
def _layer_video(account: dict, s: dict, deep: dict | None = None) -> dict:
    c4 = s.get("c4") or {}
    dna = account.get("content_dna") or {}
    return {
        "coord": "④ 单条",
        "zoom": "最小盘 · 每条 vs 自身基线",
        "user_question": "刚发这条行不行?要追加吗?下条怎么拍?",
        "cost_yuan": COST_LAYER_YUAN["video"],
        "value": "日常油——从感觉驱动变数据驱动(高频/低价/累积)",
        "level": "处方+预测级",
        "content_score": c4.get("score"),
        "content_weak": c4.get("weak"),
        "burst_ratio": account.get("burst_ratio"),       # 爆款率(vs 自身中位)
        "avg_like": account.get("avg_like"),
        "max_like": account.get("max_like"),
        "update_gap_days": account.get("update_gap_days"),
        "engagement_structure": account.get("engagement_structure"),
        # ④ 单条层核心:内容 DNA「下条怎么拍」(作品矩阵组合·无星图也满血)
        "next_video_rx": dna.get("next_video_rx"),
        "dna": {
            "best_time": (dna.get("best_time") or {}).get("verdict"),
            "best_duration": (dna.get("best_duration") or {}).get("verdict"),
            "topics": (dna.get("topics") or {}).get("verdict"),
            "hashtags": (dna.get("hashtags") or {}).get("verdict"),
            "anchor": (dna.get("anchor") or {}).get("verdict"),
            "comment_pool": (dna.get("comment_pool") or {}).get("verdict"),
        } if dna else None,
        "deep": (deep or {}).get("video"),   # ④单条层五段式深度
    }


def _identity(account: dict) -> dict | None:
    try:
        from app.services import identity_audit
        return identity_audit.audit_identity(account)
    except Exception:  # noqa: BLE001
        return None


def _diag_chain(account: dict, s: dict, deep: dict) -> list[dict]:
    """诊断链(point3):流量→互动→口碑→转化→真实·5层因果·14指标+所有信号全织入·层层联想。

    每层:数据(指标/信号) + 一句诊断 + 连到下一层的因果('为什么留不住→看互动')。
    """
    es = account.get("engagement_structure") or {}
    attr = account.get("content_attribution") or {}
    clusters = account.get("comment_clusters") or {}
    se = account.get("sentiment_evolution") or {}
    c1, c2, c3, c4 = s.get("c1") or {}, s.get("c2") or {}, s.get("c3") or {}, s.get("c4") or {}
    c8, c12 = s.get("c8") or {}, s.get("c12") or {}
    anom = account.get("engagement_anomaly") or {}

    def L(name, color, metrics, diagnosis, link):
        return {"layer": name, "color": color, "metrics": metrics,
                "diagnosis": diagnosis, "link": link}

    chain = [
        L("流量层", "#0891B2",
          [f"健康 C1={c1.get('score')}({c1.get('phase','')})",
           f"内容力 C4={c4.get('score')}",
           (f"互动主要由「{attr.get('top_driver',{}).get('factor','')}」驱动"
            if attr.get("enough") else "归因待样本")],
          (f"流量基础:{c1.get('phase','')}·内容力 {c4.get('score')}分"),
          "→ 流量进来了为什么留不住?看互动层"),
        L("互动层", "#7C3AED",
          [f"评论赞比 {es.get('comment_per_like','—')}({es.get('nature','')})",
           f"收藏赞比 {es.get('collect_per_like','—')}",
           f"粉丝质量 C2={c2.get('score')}"],
          (f"互动性质={es.get('nature','—')}·"
           + ("高评论=讨论型(适合话题·难直接带货)" if (es.get('comment_per_like') or 0) >= 0.15
              else "互动结构常规")),
          "→ 观众到底在说什么?看口碑层"),
        L("口碑层", "#DB2777",
          [(f"高频诉求:{('、'.join(c['theme'] for c in (clusters.get('clusters') or [])[:2]))}"
            if clusters.get("enough") else "评论聚类待数据"),
           (f"口碑{se.get('verdict','')}·{se.get('intent_trend','')}" if se.get("enough")
            else "口碑演化待数据")],
          ("评论暴露真实诉求:" +
           ("有采购意向但问'哪里下单'=承接断点" if clusters.get("enough") else "诉求平稳")),
          "→ 这些意向能不能转成钱?看转化层"),
        L("转化层", "#D97706",
          [f"商业转化 C3={c3.get('score')}", f"变现机会 C12={c12.get('score')}",
           f"私域潜力 C8={c8.get('score')}"],
          (deep.get("commerce", {}).get("conclusion", f"商业转化 {c3.get('score')}分")),
          "→ 这些数据真不真?看真实层"),
        L("真实层", "#059669",
          [f"粉丝质量 C2={c2.get('score')}",
           (anom.get("verdict", "互动结构检测") if anom.get("enough") else "互动检测待样本")],
          (anom.get("verdict", "真实性待检") if anom.get("enough") else "真实性:样本不足"),
          ""),
    ]
    return chain


def _radar(s: dict) -> dict[str, list]:
    """指标雷达·分两组(#4 修):

    account_self  C1-C8 = **账号自身实力**(可作短板/亮点判断)
    env_intel     C9-C14 = **环境/机会情报**(大盘共享驱动·非账号得分·不当亮点)

    环境组标 degraded 与「大盘情报」属性·防把 C14(榜单数据丰富度)误读成账号优势。
    """
    self_labels = {"c1": "健康", "c2": "粉丝质量", "c3": "商业转化", "c4": "内容力",
                   "c5": "赛道蓝海", "c6": "破圈", "c7": "评级", "c8": "私域"}
    env_labels = {"c9": "热点契合", "c10": "选题机会", "c11": "粉丝洞察",
                  "c12": "变现机会", "c13": "竞品位置", "c14": "黑马选题"}

    def _row(k, label, is_env):
        d = s.get(k) or {}
        sc = d.get("score")
        row = {"key": k.upper(), "label": label, "score": sc,
               "degraded": bool(d.get("degraded"))}
        if is_env:
            row["note"] = "大盘情报·非账号得分"
        # 顶格(≥98)且非账号核心→标待核实(防 clamp 撞顶被当真实力)
        if isinstance(sc, (int, float)) and sc >= 98 and is_env:
            row["note"] = "顶格·疑标度撞顶·仅作情报参考"
        return row

    return {
        "account_self": [_row(k, v, False) for k, v in self_labels.items()],
        "env_intel": [_row(k, v, True) for k, v in env_labels.items()],
    }


def _card_brief(card: dict | None) -> dict | None:
    if not card:
        return None
    sev = card.get("severity")
    return {
        "title": card.get("title"),
        "severity": sev,
        "conclusion": (card.get("root_cause") or card.get("bottleneck_desc")
                       or card.get("vertical_desc") or card.get("commercial_desc") or ""),
        "advice": card.get("advice") or card.get("prescription"),
    }


# ── 一句话结论(最高 severity 卡前置)──────────────────────────────────────────
def _headline(c: dict, s: dict, deep: dict | None = None) -> dict:
    """挑最该关注的 1 件事(最高 severity)+ 健康分 + 评级。

    去重(#1):战略判断已是「先做流量/可带货」时,top_concern 跳过与之同义的卡
    (漏斗/流量基础),改挑下一个**不同主题**的最该关注项·避免第一屏自我重复。
    """
    # 优先用赛道感知战略判断(deep)·回退旧版
    sc = (deep or {}).get("strategic_call") or _strategic_call(s)
    skip = {"funnel"} if sc.get("color") == "red" else set()  # 红=先做流量·漏斗卡同义→跳
    ranked = sorted(c.items(), key=lambda kv: -_SEV_RANK.get(kv[1].get("severity"), 0))
    worst = None
    for name, card in ranked:
        if name in skip:
            continue
        worst = card
        break
    if worst is None:                       # 全被跳过(极端)→ 回退取最高
        worst = ranked[0][1] if ranked else {}
    health = _g(s, "c1", "score")
    grade = _g(s, "c7", "grade")
    return {
        "health_score": health,
        "grade": grade,
        "strategic_call": sc,                # 战略判断:先做流量 vs 可以带货(第一主张)
        "top_concern": {
            "title": (worst or {}).get("title"),
            "severity": (worst or {}).get("severity"),
            "what": ((worst or {}).get("root_cause") or (worst or {}).get("bottleneck_desc")
                     or (worst or {}).get("vertical_desc") or "暂无其他突出问题·保持节奏"),
            "advice": (worst or {}).get("advice") or (worst or {}).get("prescription"),
        },
    }


def _strategic_call(s: dict) -> dict:
    """核心战略判断:这账号当下该「先做流量」还是「可以带货变现」。

    判据(组合多指标·不靠单一):C1健康 + C3商业转化 + C8私域 + 内容力 C4。
    流量基础不足(转化/私域低)→ 先做流量;基础够(健康+转化均达标)→ 可推变现。
    """
    c1 = _g(s, "c1", "score") or 0
    c3 = _g(s, "c3", "score") or 0
    c8 = _g(s, "c8", "score") or 0
    if c3 < 25 or (c1 < 50 and c8 < 30):
        return {
            "call": "先做流量·暂不带货",
            "color": "red",
            "why": f"商业转化仅 {round(c3)} 分、私域 {round(c8)} 分——流量与承接两头未建,"
                   f"此时挂车带货也卖不动。第一优先级是把单条互动做起来。",
        }
    if c3 < 50:
        return {
            "call": "边做流量·边轻量试水变现",
            "color": "yellow",
            "why": f"转化 {round(c3)} 分处于成长期·可小步挂车测试·主力仍在内容曝光。",
        }
    return {
        "call": "可推变现·主攻转化",
        "color": "green",
        "why": f"健康 {round(c1)}、转化 {round(c3)} 均达标·商业基础已就绪·可加码成交布局。",
    }


# ── 算账层(每层成本 + 全局 ROI)────────────────────────────────────────────────
def _accounting(is_xingtu: bool, cache_hit: bool) -> dict:
    if cache_hit:
        per_layer = {k: 0.0 for k in COST_LAYER_YUAN}
        total = COST_CACHE_YUAN
        mode = "复诊(全缓存命中)"
    elif is_xingtu:
        per_layer = dict(COST_LAYER_YUAN)
        total = round(sum(per_layer.values()), 3)
        mode = "首次(开星图·完整商业诊断)"
    else:
        # 无星图:环境/单条照采·行业星图分位取不到(¥0)。
        # ③账号仍采了 profile(基础画像)·成本归到 ③(诚实·非 0)·单条留 video/stats/comments。
        _basic = COST_LAYER_YUAN["video"]            # ¥0.044 基础采集总额
        per_layer = {"env": COST_LAYER_YUAN["env"], "industry": 0.0,
                     "account": round(_basic * 0.4, 4),   # profile/posts 归 ③
                     "video": round(_basic * 0.6, 4)}     # video/stats/comments 归 ④
        total = round(sum(per_layer.values()), 3)
        mode = "首次(无星图·基础诊断)"
    return {
        "mode": mode,
        "per_layer_yuan": {k: round(v, 4) for k, v in per_layer.items()},
        "total_yuan": total,
        "total_usd": round(total / _RATE, 4),
        "roi": {
            "equiv_manual_hours": ROI_EQUIV["manual_hours"],
            "equiv_expert": ROI_EQUIV["expert_review"],
            "equiv_outsource_yuan": ROI_EQUIV["outsource_yuan"],
            "you_paid_yuan": total,
        },
        "compound_note": ("第一次买的是『账号体检基线』(地基);从第二次起每次≈¥0.1,"
                          "买的是『我在进步还是退步/这条该不该追/下条会不会火』的确定答案。"
                          "体检只做一次,陪跑天天发生。"),
    }
