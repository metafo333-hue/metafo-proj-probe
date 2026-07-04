"""形象一致性审计 · identity_audit.py · 人设/品牌一致性诊断。

承 v3.3 阶段1 定位航向——形象就是定位。把账号**全部基础资料**(昵称/简介/认证/属地/标签)
采全,再**交叉比对**:你"对外说的自己"(昵称+简介+认证) vs "数据里真实的你"(内容话题+赛道+
评论认知),判断:
  ① 统一形象度:六信号(昵称/简介/认证/内容/赛道/评论)是否都指向同一身份
  ② 自我匹配:声称的专业/身份,数据有没有印证(简介说"源头工厂"·评论"拿货"=B端采购→印证)
  ③ 简介专业三要素:我是谁 / 做什么 / 凭什么(信任状)——人设规范

⚠️ 纯数据/文本层(昵称/简介/标签/内容词)·头像视觉归视听别处·不碰像素。
诚实:声称无法被数据证伪的(如"36年")只标"声称·数据未否定"·不编造印证。
"""
from __future__ import annotations

import re
from typing import Any

# 身份词(我是谁)/业务词模式(做什么)/信任状词(凭什么)——专业人设三要素
_WHO = ("姐", "哥", "师", "传承人", "老板", "创始人", "厂长", "达人", "博主", "总", "匠人", "掌柜")
_TRUST = ("年", "非遗", "第", "代", "基地", "工厂", "源头", "认证", "专利", "资质", "原产地",
          "厂家", "直供", "实体", "门店", "证书", "传承")
_EMOJI = re.compile(r"[\U0001F000-\U0001FAFF☀-➿]")
_STOP = frozenset("的 了 是 我 你 在 有 与 和 个 这 那 ｜ | · - — / 　".split())


def _terms(text: str, n: int = 2) -> list[str]:
    """从中文文本抽 n-gram 实词(去 emoji/标点/停用词)。"""
    clean = _EMOJI.sub(" ", text or "")
    out = []
    for seg in re.findall(r"[一-鿿]+", clean):
        for i in range(len(seg) - n + 1):
            g = seg[i:i + n]
            if g not in _STOP:
                out.append(g)
        if len(seg) <= 4 and seg not in _STOP:
            out.append(seg)
    return out


def audit_identity(account: dict) -> dict[str, Any]:
    nick = account.get("nickname") or ""
    sig = account.get("signature") or ""
    cv = (account.get("custom_verify") or "")
    ev = (account.get("enterprise_verify_reason") or "")
    ip = account.get("ip_location") or ""
    # ── 全部基础资料(全面采)──
    profile = {
        "nickname": nick, "signature": sig, "unique_id": account.get("unique_id"),
        "ip_location": ip, "custom_verify": cv or None, "enterprise_verify": ev or None,
        "tags": [t.get("text") for t in (account.get("personal_tag_list") or [])
                 if isinstance(t, dict)],
    }
    # ── 声称的身份(昵称+简介+认证 文本)──
    claim_text = " ".join([nick, sig, cv, ev])
    claim_terms = _terms(claim_text)
    from collections import Counter
    claim_top = [w for w, _ in Counter(claim_terms).most_common(8)]
    # ── 真实信号(内容话题 + 赛道 + 评论热词)──
    dna = account.get("content_dna") or {}
    content_tags = (dna.get("topics") or {}).get("top_hashtags") or []
    ex = account.get("extra_signals") or {}
    comment_words = [w["word"] for w in (ex.get("official_comment_words") or [])]
    track_kw = (account.get("track_competition") or {}).get("keyword") or account.get("industry_tag") or ""
    actual_terms = []
    for t in content_tags + comment_words + [track_kw]:
        actual_terms += _terms(str(t))
    actual_set = set(actual_terms)

    # ── 六信号源(空数据源置 None=无法判定·不计入·数据缺失≠形象不一致)──
    src = {
        "昵称": nick or None, "简介": sig or None,
        "认证": (cv + ev) if (cv or ev) else None,
        "内容话题": (" ".join(content_tags) or None), "赛道": (track_kw or None),
        "评论认知": (" ".join(comment_words) or None),
    }

    def _cover(term):
        return sum(1 for v in src.values() if v and term in v)

    # ── 核心身份词 = 声称词里"跨信号覆盖最广"的(非第一个·更准)──
    cand = [w for w in claim_top if _cover(w) >= 1]
    core = max(cand, key=_cover) if cand else (claim_top[0] if claim_top else None)

    # ── 六信号一致性(每路是否提到核心身份)──
    signals = {k: (bool(core and core in v) if v is not None else None)
               for k, v in src.items()}
    present = {k: v for k, v in signals.items() if v is not None}
    aligned = [k for k, v in present.items() if v]
    consistency = round(len(aligned) / len(present) * 100) if present else 0

    # ── 简介专业三要素(我是谁/做什么/凭什么)──
    who = bool(any(w in nick + sig for w in _WHO))
    what = bool(content_tags or track_kw) and bool(_terms(sig))
    trust = bool(any(w in sig for w in _TRUST))
    elements = {"我是谁": who, "做什么": what, "凭什么": trust}
    elem_n = sum(elements.values())

    # ── 自我匹配判定 ──
    if consistency >= 80 and core:
        verdict = f"形象高度统一·六路信号都指向「{core}」"
        match = "高度匹配"
    elif consistency >= 50:
        verdict = f"形象基本统一·核心「{core}」·个别信号弱"
        match = "部分匹配"
    else:
        verdict = "形象分散·对外说的与内容/评论不一致"
        match = "形象不统一"
    # 信任状是否被数据印证(声称专业 vs 评论是否B端采购/认可)
    trust_confirmed = None
    if trust:
        b2b_signal = any(w in " ".join(comment_words) for w in ("拿货", "批发", "厂家", "源头", "供"))
        trust_confirmed = ("评论现 B端采购/源头认知·印证专业信任状" if b2b_signal
                           else "信任状为声称·数据未否定但也未强印证(可补成交/资质佐证)")

    advice = []
    if elem_n < 3:
        miss = [k for k, v in elements.items() if not v]
        advice.append(f"简介补全专业三要素·缺「{'、'.join(miss)}」")
    if consistency < 80:
        weak = [k for k, v in present.items() if not v]
        advice.append(f"统一形象·让「{'、'.join(weak)}」也对齐核心身份")
    if not advice:
        advice.append("形象已统一·维持;可把信任状(年限/非遗/资质)在内容里反复强化")

    return {
        "profile": profile, "core_identity": core,
        "claimed": claim_top[:5], "consistency": consistency,
        "signals": signals, "aligned": aligned,
        "self_match": match, "verdict": verdict,
        "elements": elements, "elements_n": elem_n,
        "trust_confirmed": trust_confirmed,
        "advice": advice,
        "note": "纯文本/数据层(昵称/简介/标签/内容词)·头像视觉归视听·声称类信任状不编造印证",
    }
