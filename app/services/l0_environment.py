"""L0 环境层 · 确定性框架(规则驱动·能拿就填·拿不到诚实标)。

规则覆盖：若 data/l0_platform_rules.json 存在则由 _load_rules_override() 加载。
覆盖规则来自 scripts/l0_rules_fetch.py（定期抓取官方公开规则页），
不存在时自动回退到本文件下方种子常量（向后兼容·现有测试不受影响）。

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

import json
import logging
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)

# 数据目录（相对本文件往上两级 = repo root/data/）
_DATA_DIR = Path(__file__).parent.parent.parent / "data"
_RULES_OVERRIDE_FILE = _DATA_DIR / "l0_platform_rules.json"

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

    # 热点(当前平台热榜·通用·诚实标非赛道专属)
    ht = macro.get("hot_topics_related") or []
    if ht:
        L.append("**当前平台热点（可蹭·但先看跟你赛道搭不搭）**")
        L.append(f"- {'、'.join(str(t) for t in ht[:6])}")
        L.append("- 注：这是当前抖音热榜（实时拉取），不是你赛道专属——能自然结合的才蹭，硬蹭反而违和。")
        L.append("")

    L.append("> 环境数据来自合规授权渠道（国内不出境）。平台规则是官方明文；"
             "赛道趋势属半自动补充，**平台算法的具体权重是黑盒，谁说得精确都是猜的**，不作硬结论。")
    return "\n".join(L)


# ── 可选规则覆盖（由 scripts/l0_rules_fetch.py 产出·不破坏现有接口） ─────────────

def _load_rules_override() -> dict | None:
    """加载 data/l0_platform_rules.json（由 l0_rules_fetch.py 定期更新）。

    返回值结构（与种子对齐）：
        {
            "ai_label":       str,            # 覆盖 _AI_LABEL_RULE
            "forbidden_zones": list[str],     # 覆盖 _FORBIDDEN_COMMON
            "music":          str,            # 覆盖 _MUSIC_RULE
            "fetched_at":     str,            # ISO 时间戳（调试用）
            "fetch_coverage": str,            # "N/M 目标成功"
        }

    若文件不存在/损坏/schema 不符，返回 None（调用方使用种子）。
    设计为幂等：每次调用重新读文件（cron 更新后下一次调用即生效·无缓存）。
    """
    if not _RULES_OVERRIDE_FILE.exists():
        return None
    try:
        with open(_RULES_OVERRIDE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        plat = data.get("platform", {})
        # 校验最低 schema：至少有 forbidden_zones
        if not plat.get("forbidden_zones"):
            _log.warning("l0_platform_rules.json 缺少 forbidden_zones，忽略覆盖文件")
            return None
        return {
            "ai_label": plat.get("ai_label") or _AI_LABEL_RULE,
            "forbidden_zones": list(plat["forbidden_zones"]),
            "music": plat.get("music") or _MUSIC_RULE,
            "fetched_at": data.get("fetched_at", ""),
            "fetch_coverage": data.get("fetch_coverage", ""),
        }
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        _log.warning("l0_platform_rules.json 解析失败: %s，回退种子", e)
        return None
