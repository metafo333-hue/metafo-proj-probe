"""深度分析层 · 把「光秃秃的分数」变成「结论→拆解→依据→对比→推论」五段式。

解决「不专业·没说服力」:专业分析不是给分,是给**为什么是这个分 + 对标谁 + 会怎样**。
每个深度块结构统一:
  conclusion 结论(一句话)
  breakdown  拆解(分数由哪几项构成·各占多少)
  evidence   数据依据(具体原始数字)
  benchmark  基准对比(对标行业线·带出处)
  implication 后果推论(这意味着什么·不改会怎样)

数据来源:composite_scores 已算的 breakdown/missing + benchmarks 真实基准 + account 原始字段。
全部赛道感知(B端线索游戏 ≠ 泛娱乐流量游戏)。
"""
from __future__ import annotations

from typing import Any

from app.services import benchmarks as BM


def _pct(v, d=1):
    return f"{v*100:.{d}f}%" if isinstance(v, (int, float)) else "—"


def _track_signal(account: dict) -> str:
    """汇总赛道分型信号:industry_tag + 搜索词 + 昵称 + 作品话题/选题关键词。

    B端信号(源头/工厂/食材)多在视频话题与昵称里·非 industry_tag·此前漏读致误判。
    """
    sigs = [
        account.get("industry_tag") or "",
        (account.get("track_competition") or {}).get("keyword") or "",
        account.get("nickname") or "",
    ]
    dna = account.get("content_dna") or {}
    topics = dna.get("topics") or {}
    sigs += list(topics.get("top_hashtags") or [])
    sigs += list(topics.get("top_keywords") or [])
    return " ".join(s for s in sigs if s)


# ── ② 行业层深度:赛道分型 + 身位 + 该玩什么游戏 ───────────────────────────────
def deep_industry(account: dict, xprof: Any, scores: dict) -> dict[str, Any]:
    track = BM.classify_track(_track_signal(account), account.get("industry_tags"))
    stage = BM.fan_stage(account.get("follower"), is_b2b=track.get("is_b2b_leads"))
    c5 = scores.get("c5") or {}
    return {
        "track_tier": track,
        "fan_stage": stage,
        "conclusion": (f"{track['name']}·{stage['stage']}·该玩「{track['game']}」"),
        "breakdown": [
            f"赛道档位:{track['tier']}档({track['name']})·单粉价值 {track['value_per_fan']}",
            f"生命周期:{stage['stage']}({stage['follower']}粉)·本期任务={stage.get('task','')}",
            f"赛道蓝海度 C5={c5.get('score')}·{c5.get('verdict','')}",
        ],
        "evidence": [
            f"匹配关键词「{track.get('matched') or '默认判定'}」→ {track['tier']}档",
            f"变现门槛:{track['monetize_fans']}",
        ],
        "benchmark": f"赛道价值四档 S/A/B/C 单粉价值差 50-500 倍(出处 {track['source']})·"
                     f"{stage['source']}",
        "implication": (
            f"⚠️ 关键:{track['name']}该用「{track['game']}」的尺·"
            + ("B端玩线索游戏——几千精准粉就能变现,不该用泛娱乐的'播放量'评判"
               if track.get("is_b2b_leads") else
               f"该赛道按 {track['monetize_fans']} 节奏变现")),
    }


# ── ③ 账号层深度:健康分拆解 + 商业转化为什么这么低 ─────────────────────────────
_C1_LABELS = {"interaction_quality": "互动质量", "follower_net": "粉丝净增",
              "update_rhythm": "更新节奏", "content_trend": "内容趋势",
              "serialization": "合集化"}


def deep_health(account: dict, scores: dict) -> dict[str, Any]:
    c1 = scores.get("c1") or {}
    bd = c1.get("breakdown") or {}
    eng = BM.engagement_breakdown(
        account.get("avg_like"), account.get("follower"),
        account.get("engagement_structure"), account.get("avg_collect"))
    # 找最拖后腿的子项
    weak = min(bd.items(), key=lambda kv: kv[1]) if bd else None
    return {
        "conclusion": f"健康 {c1.get('score')} 分·{c1.get('phase','')}",
        "breakdown": [f"{_C1_LABELS.get(k,k)} {v}分" for k, v in bd.items()],
        "weakest": (f"{_C1_LABELS.get(weak[0],weak[0])}({weak[1]}分)" if weak else None),
        "evidence": [f"{p['metric']} {p['value']}({p['verdict']})" for p in eng["parts"]],
        "benchmark": "·".join(p["benchmark"] for p in eng["parts"][:2])
                     or BM.ENGAGEMENT["interaction_rate_healthy"]["label"],
        "engagement_nature": eng.get("nature"),
        "implication": (f"最该补:{_C1_LABELS.get(weak[0],weak[0])}" if weak else "各项均衡"),
    }


def deep_commerce(account: dict, xprof: Any, scores: dict, track: dict) -> dict[str, Any]:
    """C3 商业转化为什么是这个分(拆 5 个加权项 + 缺失原因)·纠赛道误判。"""
    c3 = scores.get("c3") or {}
    missing = c3.get("missing") or []
    mon = BM.monetize_readiness(
        account.get("follower"), bool(account.get("with_commerce_entry")),
        account.get("commerce_density"), track)
    return {
        "conclusion": f"商业转化 {c3.get('score')} 分·{mon['gap']}",
        "breakdown": [
            "带货指数 30%(需星图)", "转化指数 25%(需星图)",
            f"商业密度 20%·当前 {_pct(account.get('commerce_density') or 0)}",
            f"橱窗/直播 15%·{'有' if account.get('with_commerce_entry') else '无'}",
            "粉丝消费力 10%(需星图画像)",
        ],
        "evidence": [f"缺失项:{m}" for m in missing[:4]] or ["数据齐全"],
        "benchmark": f"{mon['gate']}(出处 {mon['source']})",
        "implication": (
            f"⚠️ {mon['current_action']}·{mon['recommended_path']}·"
            + ("**关键纠偏:这是 B 端号·低分主因是'没做变现动作'不是'不该变现'·"
               "已过门槛却零承接=漏掉线索**" if track.get("is_b2b_leads")
               and mon["ready"] else mon["gap"])),
    }


# ── 战略判断 v2:赛道感知(纠"用泛娱乐尺判 B 端=先做流量"的误判)───────────────────
def strategic_call_v2(account: dict, xprof: Any, scores: dict) -> dict[str, Any]:
    track = BM.classify_track(_track_signal(account), account.get("industry_tags"))
    stage = BM.fan_stage(account.get("follower"), is_b2b=track.get("is_b2b_leads"))
    mon = BM.monetize_readiness(
        account.get("follower"), bool(account.get("with_commerce_entry")),
        account.get("commerce_density"), track)
    eng = BM.engagement_breakdown(
        account.get("avg_like"), account.get("follower"),
        account.get("engagement_structure"))
    cpl = (account.get("engagement_structure") or {}).get("comment_per_like") or 0

    # B 端 + 已过门槛 + 高评论(潜在线索)+ 零承接 → 该补承接做线索·非追流量
    if track.get("is_b2b_leads") and mon["ready"] and (account.get("commerce_density") or 0) == 0:
        leads_signal = "·评论咨询率高(潜在线索金矿)" if cpl >= 0.15 else ""
        return {
            "call": "补私域承接·把咨询变线索",
            "color": "yellow",
            "why": (f"{track['name']}·{stage['follower']}粉已过 B 端变现门槛"
                    f"(几千精准粉即可){leads_signal}·但商业密度 0=有咨询没承接·"
                    f"该补私域钩子/橱窗把评论咨询导成线索·而非盲目追播放量。"
                    f"B 端玩线索游戏不玩流量游戏(出处 {track['source']})。"),
            "track_aware": True,
        }
    # 泛娱乐/内容档 + 转化基础未建 → 先做流量
    c3 = (scores.get("c3") or {}).get("score") or 0
    if not track.get("is_b2b_leads") and c3 < 25 and not mon["ready"]:
        return {
            "call": "先做流量·暂不带货",
            "color": "red",
            "why": (f"{track['name']}·{stage['stage']}·按 {track['monetize_fans']} 门槛"
                    f"当前粉丝量未到变现线·先把内容互动做起来(出处 {track['source']})。"),
            "track_aware": True,
        }
    if mon["ready"]:
        return {
            "call": "可推变现·主攻承接转化",
            "color": "green",
            "why": f"{stage['stage']}·已过 {track['name']} 变现门槛·{mon['recommended_path']}。",
            "track_aware": True,
        }
    return {
        "call": "攒精准粉·边做边测变现",
        "color": "yellow",
        "why": f"{track['name']}·{stage['stage']}·{mon['gap']}(出处 {stage['source']})。",
        "track_aware": True,
    }


# ── ① 环境层深度:大盘温度 + 蹭热点契合 + 黑马机会 ─────────────────────────────
def deep_env(account: dict, scores: dict) -> dict[str, Any]:
    c9 = scores.get("c9") or {}
    c14 = scores.get("c14") or {}
    follower = account.get("follower") or 0
    avg_like = account.get("avg_like") or 0
    # 曝光地板对比(播放<粉丝×5=卡曝光·无 play 用赞×N 粗代理诚实标)
    exp = BM.ENGAGEMENT["exposure_floor"]
    cur = [x.get("name") for x in (account.get("hot_topics_current") or []) if x.get("name")]
    roc = [x.get("name") for x in (account.get("hot_topics_rocketing") or []) if x.get("name")]
    horse_tags = c14.get("dark_horse_tags") or []
    has_hot = bool(cur or roc)
    c9_score = c9.get("score") or 0
    # 契合度低(<40)= 大盘热点多为跨赛道时事/泛娱乐·按「标签内蹭·禁跨标签」原则
    # 不建议硬蹭(蹭游戏/时事会乱标签·伤垂直度)·这是承基准的诚实推论。
    fit_low = c9_score < 40
    return {
        "conclusion": (f"赛道热点契合 C9={c9.get('score')}·{c9.get('verdict','')}"
                       + (f"·{len(horse_tags)}个黑马选题方向" if horse_tags else "")),
        "breakdown": [
            f"热点契合 C9={c9.get('score')}·{c9.get('verdict','')}",
            f"黑马机会 C14={c14.get('score')}·{c14.get('verdict','')}",
            f"账号身位:{BM.fan_stage(follower).get('stage','')}({follower}粉)",
        ],
        "evidence": ([f"当前大盘热点(全网·多为时事/泛娱乐):{('、'.join(cur[:4]))}" if cur else None,
                      f"飙升风口(全网):{('、'.join(roc[:4]))}" if roc else None,
                      # 黑马标签来自全网低粉爆款榜·非本赛道·只证"低粉可爆"·不作选题推荐
                      (f"全网黑马案例 {len(horse_tags)} 个(证明低粉也能爆·参考其'以小博大'的形式·"
                       "非选题本身·这些标签跟你赛道无关)" if horse_tags else None)]
                     )[:4] if (has_hot or horse_tags)
                    else ["⚠️ L0 热点数据未接通·当前赛道大盘信号拿不到(非编造)"],
        "benchmark": f"{exp['label']}({exp['def']}·出处 {exp['source']})·"
                     "蹭热点铁律:标签内蹭·禁跨标签(跨标签蹭会乱算法标签·伤垂直度)",
        "implication": (
            # 契合度低 = 大盘热点与你赛道不相关 → 诚实劝退跨标签蹭热点
            f"⚠️ 热点契合仅 {c9_score} 分·当前飙升热点全是时事/游戏(与魔芋/食材赛道无关)·"
            "按「标签内蹭」铁律**不建议硬蹭**(蹭游戏热点会乱算法标签·伤垂直度)·"
            "专注赛道内容(源头/工厂/食材选题)比追泛热点更稳。"
            "⚠️ 真正缺口=赛道内热点信号没接通(L0只有全网榜·没有'魔芋赛道'细分热榜)"
            if fit_low else
            "✅ 你的内容踩中了相关热点·可继续顺势加码「" + "、".join((roc or cur)[:2]) + "」"),
    }


# ── ④ 单条层深度:互动质量拆解 + 作品矩阵规律 + 下条怎么拍 ─────────────────────
def deep_video(account: dict, scores: dict) -> dict[str, Any]:
    c4 = scores.get("c4") or {}
    eng = BM.engagement_breakdown(
        account.get("avg_like"), account.get("follower"),
        account.get("engagement_structure"), account.get("avg_collect"))
    dna = account.get("content_dna") or {}
    nature = (account.get("engagement_structure") or {}).get("nature")
    rx = dna.get("next_video_rx") or {}
    return {
        "conclusion": (f"内容力 C4={c4.get('score')}·互动性质:{nature or '—'}"),
        "breakdown": [
            f"内容力 C4={c4.get('score')}(爆款率25%+互动趋势30%+话题质量15%+竞品20%+视听10%)",
            f"爆款率={account.get('burst_ratio')}(最高赞÷均赞·>3 有明显爆款)",
            f"均赞 {account.get('avg_like')}·最高赞 {account.get('max_like')}",
        ],
        "evidence": [f"{p['metric']} {p['value']}({p['verdict']})" for p in eng["parts"]]
                    + ([f"作品规律:{dna['best_time']['verdict']}"] if dna.get("best_time") else []),
        "benchmark": (BM.ENGAGEMENT["interaction_rate_healthy"]["label"]
                      + "·商业信号价值升序:" + "<".join(BM.ENGAGEMENT["signal_priority"])
                      + f"(出处 {BM.ENGAGEMENT['signal_source']})·完播率🔴黑盒需投喂后台"),
        "implication": rx.get("summary") or "作品样本不足·先积累再出规律",
        "next_video_rx": rx,        # 下条怎么拍(具体步骤·已在 content_dna)
    }


def build_deep(account: dict, xprof: Any, scores: dict) -> dict[str, Any]:
    """一次产出各层深度块 + 赛道感知战略判断(四层一样厚)+ 扩展信号组合。"""
    from app.services import extra_signals as ES
    track = BM.classify_track(_track_signal(account), account.get("industry_tags"))
    return {
        "strategic_call": strategic_call_v2(account, xprof, scores),
        "env": deep_env(account, scores),
        "industry": deep_industry(account, xprof, scores),
        "health": deep_health(account, scores),
        "commerce": deep_commerce(account, xprof, scores, track),
        "video": deep_video(account, scores),
        # 扩展信号组合(采集了但没展示的端点·全部组合输出)
        "audience": ES.audience_deep(account),        # ③ 受众洞察(评论热词+粉丝分布+采购意向)
        "competitor": ES.competitor_radar(account),   # ② 竞品雷达(算法关联+粉丝同关)
        "env_hot": ES.env_hot_deep(account),          # ① 大盘热点深化
        "extra_meta": (account.get("extra_signals") or {}),  # 含 _empty/_redundant 诚实账
    }
