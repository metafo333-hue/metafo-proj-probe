"""L0 环境层 · 确定性框架(规则驱动·能拿就填·拿不到诚实标)。

分析框架"粒度轴 L0 环境层"——账号所在赛道大盘/平台规则/热点,
"先看这号是不是踩中环境风口,防把环境红利当本事"。

合规(详方案 probe-l0-environment-datasource-plan-v1.0.md):
  聚合数据·PIPL 低风险·官方/持牌源·不自建爬虫。
MVP 边界(诚实):
  - 平台禁区规则 = 种子静态(官方明规则·可落库) ✅ 确定能给
  - 账号赛道分层 = 按粉丝量粗分(account-level·非真实赛道排名) ✅ 能给·标估算
  - 赛道大盘趋势 = 🔴 官方无 API·需半自动接抖音指数/研报·MVP 留接口·拿不到诚实标
  - 热点关联 = 有热榜数据(TikHub/天聚数行)则填·无则略
  - 平台算法权重 = ⬛ 永久黑盒·绝不当结论(只标[推测·非官方])
对外报告涉密:数据源只说"合规授权渠道",不点名(承视听六层涉密)。
"""
from __future__ import annotations

from typing import Any

# —— 种子:官方明规则(可落库·源 trust.douyin.com / 视频号运营规范 / 2026-03 AI标注新规) ——
_AI_LABEL_RULE = "AI 生成内容须显著标注（2026-03 新规·未标注会限流 50-80% 甚至下架）"
_FORBIDDEN_COMMON = ["涉政敏感", "虚假宣传/夸大功效", "无资质做医疗·金融荐股",
                     "未标注的 AI 内容", "盗用版权音乐/素材"]
_MUSIC_RULE = "背景音乐用平台曲库的免费商用音乐，别用来路不明的（版权风险会限流）"
# B2B/带货号额外高压线
_BIZ_EXTRA = ["资质宣传（年限/认证/龙头）必须有据可查——虚假宣传是红线",
              "价格、供货/效果承诺别夸大，留好证据"]


def _tier(fol: int) -> tuple[str, str]:
    """按粉丝量粗分赛道位置(account-level·非真实赛道排名→标估算)。"""
    if fol < 1000:
        return "新账号 / 冷启层", "粉丝<1000·刚进场"
    if fol < 10000:
        return "尾部成长层", "有基础但未起量"
    if fol < 100000:
        return "腰部", "已跑出一定规模"
    return "头部", "赛道里的成熟号"


def build_l0_environment(account: dict[str, Any], *, track: str | None = None,
                         is_business: bool = False,
                         hot_topics: list | None = None,
                         track_trend: str | None = None) -> dict:
    """L0 环境数据(按 schema·能填的填·拿不到标 None)。

    track/is_business 由调用方(account_report._track/_is_business)推断后传入。
    track_trend/hot_topics 有数据源(抖音指数/热榜)则传入,无则 None(报告诚实标待接入)。
    """
    fol = account.get("follower") or 0
    tier, tier_basis = _tier(fol)
    forbidden = list(_FORBIDDEN_COMMON) + (_BIZ_EXTRA if is_business else [])
    return {
        "track": {
            "name": track,
            "trend_direction": track_trend,          # None = 待数据源
            "trend_conf": 0.0 if track_trend is None else 0.6,
            "trend_evidence": None if track_trend is None else "官方/研报趋势",
        },
        "platform": {
            "ai_label": _AI_LABEL_RULE,
            "forbidden_zones": forbidden,
            "music": _MUSIC_RULE,
            # ⬛ 算法权重黑盒:不放·避免假装能给
        },
        "macro": {
            "hot_topics_related": list(hot_topics or []),
            "sentiment": None,                        # 待舆情源
        },
        "position_in_track": {
            "subject_tier": tier,
            "tier_basis": tier_basis,
            "note": "按粉丝量粗分·非赛道真实排名(要精确得看竞品·L4)",
        },
        "data_source_meta": {
            "compliance_note": "合规授权渠道·国内不出境",
            "gaps": [k for k, v in (("赛道大盘趋势", track_trend), ("热点关联", hot_topics)) if not v],
        },
    }


def render_l0_section(l0: dict | None) -> str:
    """L0 → 报告"赛道大环境"段(说人话·拿不到诚实标·禁区警告·无裸数字)。"""
    if not l0:
        return ""
    plat = l0.get("platform") or {}
    pos = l0.get("position_in_track") or {}
    track = l0.get("track") or {}
    macro = l0.get("macro") or {}
    L = ["## 你所在赛道的大环境（避坑 + 定位）", ""]

    # 平台规则(种子·确定能给·对创作者最实用)
    L.append("**平台高压线（先看这个，别白做）**")
    if plat.get("ai_label"):
        L.append(f"- {plat['ai_label']}")
    fz = plat.get("forbidden_zones") or []
    if fz:
        L.append(f"- 这些是高压线，碰了会限流/掉号：{'、'.join(fz)}")
    if plat.get("music"):
        L.append(f"- {plat['music']}")
    L.append("")

    # 账号赛道定位(分层·标估算)
    if pos.get("subject_tier"):
        L.append("**你在赛道里大概什么位置**")
        L.append(f"- 你目前属于「**{pos['subject_tier']}**」（{pos.get('tier_basis','')}）。")
        if pos.get("note"):
            L.append(f"- 注：{pos['note']}。")
        L.append("")

    # 赛道趋势(有则讲·无则诚实标·这是关键诚实点)
    L.append("**你赛道现在是涨还是跌**")
    if track.get("trend_direction"):
        L.append(f"- 当前赛道「{track.get('name') or ''}」整体**{track['trend_direction']}**。")
    else:
        L.append("- ⚠️ 这次**没接到赛道大盘趋势数据**——赛道整体在涨还是跌、红利窗口还在不在，"
                 "需要接平台官方趋势/行业研报（官方没开放 API，得半自动补），暂时给不了，"
                 "**宁可告诉你「没接到」也不瞎编**。")
    L.append("")

    # 热点(有则关联)
    ht = macro.get("hot_topics_related") or []
    if ht:
        L.append("**当前和你相关的热点**")
        L.append(f"- {'、'.join(str(t) for t in ht[:5])}")
        L.append("")

    L.append("> 环境数据来自合规授权渠道（国内不出境）。平台规则是官方明文；"
             "赛道趋势属半自动补充，**平台算法的具体权重是黑盒，谁说得精确都是猜的**，不作硬结论。")
    return "\n".join(L)
