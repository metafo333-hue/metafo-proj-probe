"""主页转化承接力诊断 · homepage_diagnose.py · 确定性·规则驱动·零 LLM·零网络。

来源方法论：probe-engine-catalog/02-analysis-dimensions/homepage-conversion-adaptive-research.md
  转化链 = 内容引流 → 主页 → 关注/私域/成交。probe 原只诊断「作品」(引流端),
  本模块补「主页」(承接端)——逐元素确定性体检 + 「引流强×承接弱」漏斗断点检测。

诚实铁律(R0.8·防玄学)：
  - 主页字段大多可直接读 = 确定性高信任输出区(🟩),与「完播率黑盒」互补。
  - 采集端未提供的字段(POI/合集/橱窗) → missing_fields 标灰 + 提示补字段,**禁默认值冒充**。
  - 主页访问率/跳转率/关注转化率 = 🟥 黑盒,一律标「需投喂创作者中心后台截图」,禁外推。
  - 行业权重表 = 🟨 经验排序·需 attribution_cache 回测校准,非平台定数。
  - 头像只做「非默认/是否真人」客观粗判,不做人脸识别(PIPL 红线)。
  - 人群轴可选·缺则只跑行业×阶段两轴·不硬猜人群(猜错比不猜伤害大)。

纯函数·零副作用·零网络·零 LLM(与 commercial.py / conversion.py 同构)。
"""
from __future__ import annotations

import re
from typing import Any

# ──────────────────────────────────────────────────────────────────────────────
# 行业 → 主页元素权重表(track 名复用 account_report._track() 输出)
#   priority : 该行业主页元素重要性排序(经验·🟨)
#   must_have: 缺它=承接弱断点候选(P0)
#   *_hint   : 给建议时的话术钩子
# ──────────────────────────────────────────────────────────────────────────────
_HOMEPAGE_INDUSTRY_WEIGHTS: dict[str, dict[str, Any]] = {
    "美食": {  # 餐饮
        "priority": ["poi", "top_video", "bio"],
        "must_have": ["poi"],
        "bg_hint": "营业时间/招牌菜/地址",
        "top_hint": "招牌菜或探店爆款",
    },
    "时尚美妆": {  # 美业/美妆
        "priority": ["top_video", "bio", "enterprise"],
        "must_have": ["top_video"],
        "top_hint": "最强前后对比那条",
        "bio_cta_hint": "预约/到店",
    },
    "带货电商": {  # 服装/带货
        "priority": ["window", "collection", "top_video", "bio"],
        "must_have": ["window"],
        "top_hint": "真人试穿/上身效果",
    },
    "知识科普": {  # 教育/知识IP
        "priority": ["bio", "collection"],
        "must_have": ["bio", "collection"],
        "bio_hint": "讲清「解决什么问题」",
        "compliance_check": True,  # 禁包过/保过(接 compliance 思路)
    },
    "健身运动": {
        "priority": ["bio", "poi", "top_video"],
        "must_have": ["bio"],
        "bio_cta_hint": "体验课/到店",
    },
    "母婴育儿": {
        "priority": ["window", "bio", "collection"],
        "must_have": ["bio"],
    },
    "产业带货 / B2B供货": {
        "priority": ["enterprise", "bio", "poi"],
        "must_have": ["bio"],
        "bio_hint": "讲清「供什么/给谁/怎么合作」",
    },
}
# 缺省行业(生活记录/泛流量等)：只查地基,不强求 must_have
_GENERIC_WEIGHTS = {"priority": ["nickname", "bio", "avatar"], "must_have": []}

# 创作者人群 → 主页承接目标(人群轴可选·缺则不跑此轴)
_PERSONA_HOMEPAGE_GOAL: dict[str, dict[str, Any]] = {
    "实体店主": {"goal": "到店转化", "key_checks": ["poi", "enterprise", "bio"]},
    "应届生": {"goal": "定位清晰", "key_checks": ["nickname", "bio", "collection"]},
    "中年失业": {"goal": "人设信任", "key_checks": ["bio", "avatar", "top_video"]},
    "在职转型": {"goal": "信任+效率", "key_checks": ["bio", "collection"]},
}

# 阶段 → 诊断深度门(阶段名复用 account_report._stage 的语义·此处用粉丝量推断)
_STAGE_DEPTH: dict[str, dict[str, Any]] = {
    "冷启动": {"check": ["nickname", "bio", "avatar"], "skip": ["window", "collection", "top_video"]},
    "起号期": {"check": ["nickname", "bio", "avatar", "collection", "top_video"], "skip": []},
    "成长期": {"check": "all", "skip": []},
    "成熟期": {"check": "all_plus_score", "skip": []},
}

# Bio 三要素检测正则(确定性·零 LLM)
_BIO_WHO = re.compile(r"(我是|本人|专注|深耕|\d+年|老师|店|工作室|主理|创始|从业)")
_BIO_WHOM = re.compile(r"(给|帮|为|面向|适合|宝妈|新手|老板|学员|想.{0,4}的)")
_BIO_WHAT = re.compile(r"(分享|教|提供|解决|带你|干货|攻略|预约|咨询|合作|课程|带货)")
_NICK_GEO = re.compile(r"(北京|上海|成都|广州|深圳|杭州|重庆|武汉|西安|.{1,3}市|.{1,3}区|本地|同城)")
# 私域明文导流(合规·复用 compliance 思路·单一规则)
_PRIVATE_LEAK_RE = re.compile(r"(微信|加我|vx|wx|v信|薇信|\bqq\b|扣扣|私我领|加v|二维码|手机号|\d{11})", re.I)
# 默认头像/低质头像 URL 特征(粗判·🟨)
_DEFAULT_AVATAR_RE = re.compile(r"(default|aweme-avatar|0e603\w+|placeholder|noavatar)", re.I)

# 元素中文名(渲染用)
_ELEM_CN = {
    "nickname": "昵称", "bio": "简介", "avatar": "头像", "top_video": "置顶视频",
    "collection": "合集", "window": "橱窗", "enterprise": "企业认证", "poi": "地址/POI",
}


# ──────────────────────────────────────────────────────────────────────────────
# 工具
# ──────────────────────────────────────────────────────────────────────────────
def _stage_of(followers: int) -> str:
    """粉丝量 → 阶段(与 account_report._stage 的分档对齐)。"""
    if followers < 500:
        return "冷启动"
    if followers < 5000:
        return "起号期"
    if followers < 50000:
        return "成长期"
    return "成熟期"


def _industry_weights(track: str) -> dict[str, Any]:
    return _HOMEPAGE_INDUSTRY_WEIGHTS.get(track, _GENERIC_WEIGHTS)


def _has_field(account: dict, key: str) -> bool:
    """采集端是否提供了该字段(用于 missing_fields 优雅降级·防玄学)。"""
    return key in account and account.get(key) is not None


# ──────────────────────────────────────────────────────────────────────────────
# 逐元素确定性检测器
# 每个返回 dict: {name, status(🟩/🟨/🟥), found, expected, fix, confidence, key}
#   status: 🟩=健康/确定 · 🟨=待补字段或经验判断 · 🟥=黑盒/缺字段无法检测
# ──────────────────────────────────────────────────────────────────────────────
def _check_nickname(account: dict, track: str) -> dict:
    nick = (account.get("nickname") or "").strip()
    has_geo = bool(_NICK_GEO.search(nick))
    has_track_word = any(w and w in nick for w in re.findall(r"[一-龥]{2,4}", track))
    ok = bool(nick) and (has_track_word or has_geo) and len(nick) <= 20
    return {
        "name": "昵称", "key": "nickname", "status": "🟩",
        "found": nick or "(空)",
        "expected": "含「身份/领域」或「地域」词,非乱码纯网名",
        "fix": None if ok else "昵称加上你的领域或所在城市(如「XX美甲-成都」),让陌生人一眼记住你是谁",
        "confidence": 0.9, "ok": ok,
    }


def _check_bio(account: dict, track: str, weights: dict) -> dict:
    sig = (account.get("signature") or "").strip()
    who, whom, what = bool(_BIO_WHO.search(sig)), bool(_BIO_WHOM.search(sig)), bool(_BIO_WHAT.search(sig))
    n_elem = sum([who, whom, what])
    leak = bool(_PRIVATE_LEAK_RE.search(sig))
    ok = bool(sig) and n_elem >= 2 and not leak
    fix = None
    if not sig:
        fix = "简介现在是空的——补一句话「我是谁+给谁+给什么」,这是承接陌生人的第一道门"
    elif leak:
        # 合规红线优先
        fix = "🟥 简介里有明文微信号/手机号——抖音管控私域导流,限流封号高危,改成「先关注再私信」间接引导"
    elif n_elem < 2:
        miss = []
        if not who:
            miss.append("你是谁")
        if not whom:
            miss.append("给谁")
        if not what:
            miss.append("给什么")
        hint = weights.get("bio_hint") or weights.get("bio_cta_hint")
        fix = f"简介三要素还缺「{'、'.join(miss)}」" + (f",这行重点{hint}" if hint else "")
    return {
        "name": "简介 Bio", "key": "bio", "status": "🟥" if leak else "🟩",
        "found": sig or "(空)",
        "expected": "「你是谁+给谁+给什么」三要素齐·含 CTA·无明文微信号(合规)",
        "fix": fix, "confidence": 0.9, "ok": ok, "leak": leak, "n_elem": n_elem,
    }


def _check_avatar(account: dict) -> dict:
    url = (account.get("avatar_url") or account.get("avatar") or "").strip()
    if not url:
        return {
            "name": "头像", "key": "avatar", "status": "🟨",
            "found": "(采集端未提供头像 URL)",
            "expected": "清晰、与定位一致、非默认头像",
            "fix": "采集端补头像 URL 后可判默认头像", "confidence": 0.3, "ok": True, "missing": True,
        }
    is_default = bool(_DEFAULT_AVATAR_RE.search(url))
    # 只做客观粗判:默认头像 / 是否真人需图像层(标 🟨·不做人脸识别 PIPL)
    return {
        "name": "头像", "key": "avatar", "status": "🟨",
        "found": "疑似默认头像" if is_default else "已设置(清晰度/是否真人需图像层粗判)",
        "expected": "清晰、与定位一致、非默认头像/低清截图",
        "fix": "换成清晰的真人或品牌头像,第一眼信任靠它" if is_default else None,
        "confidence": 0.5 if is_default else 0.3, "ok": not is_default,
    }


def _check_enterprise(account: dict) -> dict:
    if not _has_field(account, "enterprise_verify") and not _has_field(account, "enterprise_verify_reason"):
        return {
            "name": "企业认证", "key": "enterprise", "status": "🟨",
            "found": "(采集端未提供认证字段)", "expected": "实体店/B2B 应做企业认证(解锁地址组件/私信卡片)",
            "fix": "采集端补 enterprise_verify 字段后可检测", "confidence": 0.3, "ok": True, "missing": True,
        }
    verified = bool(account.get("enterprise_verify") or account.get("enterprise_verify_reason"))
    return {
        "name": "企业认证", "key": "enterprise", "status": "🟩",
        "found": "已认证" if verified else "未认证",
        "expected": "实体店/B2B 做企业认证解锁 POI/团购/官网链接组件",
        "fix": None if verified else "做企业认证,解锁地址组件和私信卡片(实体店/B2B 强需)",
        "confidence": 0.7, "ok": verified,
    }


def _check_field_presence(account: dict, key: str, name: str, want_hint: str) -> dict:
    """通用「采集端字段缺失则标灰」检测器(置顶/合集/橱窗/POI)——防玄学:不假装检测拿不到的数据。"""
    field_map = {
        "top_video": ("is_top", "top_aweme_id"),
        "collection": ("mix_count", "mix_list"),
        "window": ("window_product_count",),
        "poi": ("poi", "poi_name", "address"),
    }
    candidates = field_map.get(key, (key,))
    present = next((c for c in candidates if _has_field(account, c)), None)
    if present is None:
        return {
            "name": name, "key": key, "status": "🟨",
            "found": "(采集端未提供该字段)", "expected": want_hint,
            "fix": f"采集端补 {candidates[0]} 字段后可检测{name}",
            "confidence": 0.3, "ok": True, "missing": True,
        }
    val = account.get(present)
    # 数值型(数量)：>0 视为有
    if isinstance(val, (int, float)):
        has = val > 0
    else:
        has = bool(val)
    return {
        "name": name, "key": key, "status": "🟩",
        "found": (f"有({val})" if has else "无"),
        "expected": want_hint,
        "fix": None if has else f"补上{name}:{want_hint}",
        "confidence": 0.8, "ok": has,
    }


# ──────────────────────────────────────────────────────────────────────────────
# 主诊断
# ──────────────────────────────────────────────────────────────────────────────
def diagnose_homepage(
    account: dict,
    works: list[dict] | None = None,
    track: str = "生活记录",
    stage: str | None = None,
    persona: str | None = None,
) -> dict:
    """主页承接力诊断·确定性·零 LLM。

    account: 含 nickname/signature/avatar_url/enterprise_verify/
             (可选)is_top/mix_count/window_product_count/poi。缺字段优雅降级。
    works:   逐条视频(用于 detect_funnel_break 的引流强信号比对)。
    track:   account_report._track() 输出的赛道名。
    stage:   阶段名(冷启动/起号期/成长期/成熟期);缺则从 follower 推断。
    persona: 人群轴(可选);缺则只跑行业×阶段两轴(不硬猜)。

    Returns:
      elements / weak_points / funnel_break / completeness_score /
      blackbox_note / missing_fields / persona_goal
    """
    followers = account.get("follower") or 0
    stage = stage or _stage_of(followers)
    weights = _industry_weights(track)
    depth = _STAGE_DEPTH.get(stage, _STAGE_DEPTH["成长期"])

    # 全量元素检测器
    all_checks = {
        "nickname": lambda: _check_nickname(account, track),
        "bio": lambda: _check_bio(account, track, weights),
        "avatar": lambda: _check_avatar(account),
        "enterprise": lambda: _check_enterprise(account),
        "top_video": lambda: _check_field_presence(account, "top_video", "置顶视频",
                                                    weights.get("top_hint") or "置顶=转化率最高那条"),
        "collection": lambda: _check_field_presence(account, "collection", "合集",
                                                     "≥1 个按主题归类的合集"),
        "window": lambda: _check_field_presence(account, "window", "橱窗",
                                                 "带货号必有橱窗+商品与内容强相关"),
        "poi": lambda: _check_field_presence(account, "poi", "地址/POI",
                                             "实体店必挂 POI(同城流量+团购入口)"),
    }

    # 阶段深度门：决定查哪些元素(防过度诊断)
    if isinstance(depth["check"], str):  # "all" / "all_plus_score"
        want = list(all_checks.keys())
    else:
        want = list(depth["check"])
    skip = set(depth.get("skip", []))
    want = [k for k in want if k not in skip]

    elements: list[dict] = []
    missing_fields: list[str] = []
    for key in want:
        res = all_checks[key]()
        elements.append(res)
        if res.get("missing"):
            missing_fields.append(_ELEM_CN.get(key, key))

    # 承接弱断点：行业 must_have 缺失 / Bio 三要素不全 / 无置顶 / 无合集
    weak_points: list[dict] = []
    elem_by_key = {e["key"]: e for e in elements}
    for mh in weights.get("must_have", []):
        e = elem_by_key.get(mh)
        if e is None:
            continue
        if e.get("missing"):
            # 字段缺失不算断点(诚实:无法判定),只提示采集端补
            continue
        if not e.get("ok"):
            weak_points.append({
                "element": e["name"], "key": mh, "reason": f"行业关键元素「{e['name']}」缺失/不达标",
                "fix": e.get("fix"), "severity": "P0",
            })
    bio_e = elem_by_key.get("bio")
    if bio_e and not bio_e.get("missing") and not bio_e.get("ok"):
        weak_points.append({"element": "简介", "key": "bio",
                            "reason": "Bio 三要素不全或含合规风险", "fix": bio_e.get("fix"), "severity": "P0"})

    # 承接完整度评分(仅成长期以上给分·防早期玄学)
    completeness_score = None
    if depth["check"] in ("all", "all_plus_score"):
        scored = [e for e in elements if not e.get("missing")]
        if scored:
            completeness_score = round(100 * sum(1 for e in scored if e.get("ok")) / len(scored))

    # 漏斗断点(引流强×承接弱)
    funnel = None
    video = (works or [None])[0] if works else None
    if video and isinstance(video, dict):
        funnel = detect_funnel_break(account, video, {"weak_points": weak_points})

    # 人群轴(可选·不硬猜)
    persona_goal = None
    if persona and persona in _PERSONA_HOMEPAGE_GOAL:
        persona_goal = _PERSONA_HOMEPAGE_GOAL[persona]

    return {
        "track": track, "stage": stage, "persona": persona,
        "persona_goal": persona_goal,
        "elements": elements,
        "weak_points": weak_points,
        "funnel_break": funnel,
        "completeness_score": completeness_score,
        "missing_fields": missing_fields,
        "blackbox_note": "主页访问率/跳转率/关注转化率是抖音后台黑盒(🟥),"
                         "需账号主投喂创作者中心后台截图才能诊断——本段只看可读的主页结构。",
    }


# ──────────────────────────────────────────────────────────────────────────────
# 缺口核心：「引流强·承接弱」断点算法
# ──────────────────────────────────────────────────────────────────────────────
_INTENT_WORD_RE = re.compile(r"(怎么买|多少钱|在哪|价格|地址|怎么报名|怎么预约|链接|下单|哪里有)")


def detect_funnel_break(account: dict, video: dict, homepage: dict) -> dict:
    """交叉「内容引流强信号」×「主页承接弱信号」判断断点是否在主页。

    引流强信号(任一):
      - play / follower > 5      (出圈·吸了陌生人)🟨 play 黑盒外推·标注
      - like > avg_like * 2      (这条爆了)
      - 评论区出现成交意图词     🟩 强信号(若 video 含 comment_texts)
    承接弱信号(任一·来自 homepage.weak_points):
      - 行业 must_have 元素缺失 / Bio 三要素不全 / 无置顶 / 无合集

    返回 {break_at, strong_inflow, weak_landing, confidence, evidence, fix, conclusion}
    """
    fol = account.get("follower") or 0
    avg_like = account.get("avg_like") or 0
    like = video.get("like") or 0
    play = video.get("play") or 0

    evidence: list[str] = []
    confidence = 0.5  # 默认中(play 黑盒外推压低置信)

    strong = False
    if play and fol and play / (fol + 1) > 5:
        strong = True
        evidence.append(f"播放/粉丝比 {play / (fol + 1):.1f}>5(出圈·吸了陌生人,🟨 播放外推)")
    if avg_like and like > avg_like * 2:
        strong = True
        evidence.append(f"这条 {like} 赞 > 平时 2 倍({avg_like} 均赞),爆了")
        confidence = 0.7
    # 评论成交意图词(🟩 强信号·若采集端给了评论文本)
    cmt_texts = video.get("comment_texts") or []
    intent_hits = [t for t in cmt_texts if isinstance(t, str) and _INTENT_WORD_RE.search(t)]
    if intent_hits:
        strong = True
        confidence = max(confidence, 0.8)
        evidence.append(f"评论区有 {len(intent_hits)} 条成交意图词(怎么买/多少钱/在哪·🟩 强信号)")

    weak_points = homepage.get("weak_points") or []
    weak = bool(weak_points)
    weak_reasons = [w["reason"] for w in weak_points]

    # 判定
    if strong and weak:
        return {
            "break_at": "主页", "strong_inflow": True, "weak_landing": True,
            "confidence": confidence, "evidence": evidence, "weak_reasons": weak_reasons,
            "fix": ";".join(w["fix"] for w in weak_points if w.get("fix")) or "补齐主页承接元素",
            "conclusion": "⚡ 问题不在内容(内容已出圈/爆了),在主页——陌生人被钩进来,3 秒看不懂你是谁、找不到下单口,流量在落地页漏光了。",
        }
    if not strong and weak:
        return {
            "break_at": "内容", "strong_inflow": False, "weak_landing": True,
            "confidence": 0.5, "evidence": evidence, "weak_reasons": weak_reasons,
            "fix": None,
            "conclusion": "主页虽有可改项,但内容引流还不够强——先把内容做出圈(让位漏斗主线),主页是次要问题。",
        }
    if strong and not weak:
        return {
            "break_at": "下游", "strong_inflow": True, "weak_landing": False,
            "confidence": confidence, "evidence": evidence, "weak_reasons": [],
            "fix": None,
            "conclusion": "主页承接健康——往下游(私域沉淀/成交转化)找卡点。",
        }
    return {
        "break_at": None, "strong_inflow": False, "weak_landing": False,
        "confidence": 0.4, "evidence": evidence, "weak_reasons": [],
        "fix": None, "conclusion": "主页结构基本完整,引流也还在积累——继续做内容,主页保持。",
    }


# ──────────────────────────────────────────────────────────────────────────────
# 渲染层(与 account_report.render_*_section 同构·说人话+三色标注)
# ──────────────────────────────────────────────────────────────────────────────
def render_homepage_section(hp: dict | None, video: dict | None = None) -> str | None:
    """主页诊断 dict → markdown 段(供 build_report 新参数 homepage_md)。
    无诊断结果返回 None(报告自动跳过此段·与 av_md/attribution_md 降级哲学一致)。"""
    if not hp or not hp.get("elements"):
        return None

    L: list[str] = ["## 你的主页接得住流量吗", ""]
    L.append("> 转化链是「内容引流 → 主页 → 关注/成交」。一条视频把陌生人钩进来,他在 **3 秒内**"
             "用你的主页(头像/昵称/简介/置顶/合集/橱窗)判断要不要关注你。主页接不住 = 引来的流量在落地页漏光。")
    L.append("")

    # 逐元素体检表
    L.append("### 逐元素体检(🟩 确定项 / 🟨 待补字段 / 🟥 合规或黑盒)")
    L.append("")
    L.append("| 元素 | 现状 | 该长啥样 | 怎么改 |")
    L.append("|------|------|---------|--------|")
    for e in hp["elements"]:
        fix = e.get("fix") or ("✅ 没问题" if e.get("ok") else "—")
        found = e.get("found", "")
        L.append(f"| {e['status']} {e['name']} | {found} | {e.get('expected','')} | {fix} |")
    L.append("")

    # 漏斗断点(若命中主页)
    fb = hp.get("funnel_break")
    if fb and fb.get("break_at") == "主页":
        L.append(f"### ⚡ 漏斗断点:引流强但主页承接弱(置信度 {fb['confidence']:.0%})")
        L.append("")
        L.append(fb["conclusion"])
        if fb.get("evidence"):
            L.append("")
            L.append("**判断依据**:")
            for ev in fb["evidence"]:
                L.append(f"- {ev}")
        if fb.get("fix"):
            L.append("")
            L.append(f"**立即改**:{fb['fix']}")
        L.append("")
    elif fb and fb.get("conclusion"):
        L.append(f"> {fb['conclusion']}")
        L.append("")

    # 承接弱断点清单(非主页断点时仍列可改项)
    elif hp.get("weak_points"):
        L.append("### 主页承接可改项")
        for w in hp["weak_points"]:
            L.append(f"- **{w['element']}**:{w['reason']}" + (f" → {w['fix']}" if w.get("fix") else ""))
        L.append("")

    # 承接完整度评分(仅成长期以上)
    score = hp.get("completeness_score")
    if score is not None:
        bar = "🟩" if score >= 70 else ("🟨" if score >= 40 else "🟥")
        L.append(f"### 承接完整度:{bar} {score}/100")
        L.append("> (只对采集端可读的主页元素打分;打灰的待补字段不计入,不冒充)")
        L.append("")

    # 人群轴(可选)
    pg = hp.get("persona_goal")
    if pg:
        L.append(f"> 你的主页承接核心目标:**{pg['goal']}**——重点盯 {', '.join(_ELEM_CN.get(k, k) for k in pg['key_checks'])}。")
        L.append("")

    # 字段缺失诚实声明(防玄学)
    if hp.get("missing_fields"):
        L.append(f"> ⚠️ 以下元素采集端暂未提供字段,**没假装检测**:{'、'.join(hp['missing_fields'])}——"
                 "补上对应采集字段后可纳入诊断。")
        L.append("")

    # 黑盒声明(必带)
    L.append(f"> {hp['blackbox_note']}")
    L.append("")
    L.append("> 说明:主页结构属确定性检测(🟩 高信任),但「行业元素权重」是经验排序(🟨 需回测校准);"
             "头像只做「非默认/清晰度」客观粗判,**不做人脸识别**(PIPL 红线)。")
    return "\n".join(L)
