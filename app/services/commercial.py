"""商业转化诊断 · commercial.py · 三层商业诊断（确定性·规则驱动·零 LLM）。

来源方法论：probe-commercial-conversion-methodology-v1.0.md
  层A: 赛道商业价值五档（S/A/B/C）
  层B: 变现路径六路径（门槛/天花板/适配·R-C1·R-M1/M2/M3）
  层C: ROI 估算（LTV-CAC·经验区间·必须标"需真实数据校准"）

诚实铁律：
- 单粉价值 / LTV / CAC 是「经验区间」，不是精确值，必须标"需校准"
- 黑盒维（完播/流量来源/真实成交）不冒充——诚实标引导投喂
- 所有数值注脚带"经验区间·需真实数据校准"

纯函数·零副作用·零网络·零 LLM。
"""
from __future__ import annotations

from typing import Any

from .account_report import _track, _is_business

# ──────────────────────────────────────────────────────────────────────────────
# 层A: 赛道商业价值档（方法论§二·层A·表）
# ──────────────────────────────────────────────────────────────────────────────

# 各赛道关键词 → (档位, 单粉价值区间描述, 投产比★数, 备注)
# 顺序从高到低——先命中先返回
_TRACK_VALUE_TABLE: list[tuple[list[str], str, str, str, str]] = [
    # (赛道关键词片段, 档位, 单粉价值描述, 投产比★, 说明)
    (
        ["医美", "整形", "家装", "装修", "招商", "加盟", "法律", "律师",
         "会计", "财税", "B2B供货", "产业带", "B端", "产业带货", "直供", "工厂"],
        "S",
        "极高（50–500元/线索 · 10–50元/粉·经验区间·需校准）",
        "★★★★★",
        "垂直B端/知识付费/IP人设·越垂单粉越贵·2万粉即可回本"
    ),
    (
        ["知识付费", "知识科普", "个人成长", "知识励志", "IP", "咨询", "职场",
         "副业", "投资", "理财", "考证"],
        "S",
        "极高（精准粉价值高·课程单价9.9–30,000元区间·经验区间·需校准）",
        "★★★★★",
        "知识付费赛道·几千精准粉就能起步·私域天花板最高"
    ),
    (
        ["带货电商", "时尚美妆", "母婴育儿", "家居", "穿搭", "美妆", "护肤",
         "健身运动", "兴趣小众", "带货", "橱窗", "好物", "种草", "选品"],
        "A",
        "高（3–30元/粉·经验区间·需校准）",
        "★★★★☆",
        "电商带货/时尚美妆/母婴/家居·品牌预算充足·带货佣金可观"
    ),
    (
        ["美食", "探店", "吃播", "菜谱", "厨艺"],
        "B",
        "中（1–3元/粉·经验区间·需校准）",
        "★★★☆☆",
        "美食探店·受众广但消费意愿分散·探店团购是主路径"
    ),
    (
        ["剧情", "短剧", "情感", "女性成长", "情感共鸣", "女性智慧", "婚姻"],
        "B",
        "中（1–3元/粉·经验区间·需校准）",
        "★★★☆☆",
        "剧情/情感·转化靠故事信任积累·私域变现潜力大但路径长"
    ),
    (
        ["颜值", "才艺", "舞蹈", "唱歌", "搞笑", "泛娱乐", "直播打赏", "颜值才艺"],
        "C",
        "低（0.1–2元/粉·需50万+粉才有规模·经验区间·需校准）",
        "★★☆☆☆",
        "颜值/才艺/泛娱乐·单粉价值低·投产比差·月投1万需50万粉回本"
    ),
    (
        ["生活记录", "日常", "vlog", "记录"],
        "C",
        "低（0.1–2元/粉·泛流量难变现·经验区间·需校准）",
        "★★☆☆☆",
        "生活记录·赛道宽泛·变现须先垂直化"
    ),
]

# R-M3 赛道付费意愿等级（用于路径匹配权重）
_TRACK_PAY_INTENT: dict[str, str] = {
    "S": "极高（职场/副业可达数万元·健康/育儿数千元）",
    "A": "高（品类消费意愿强·单笔百元至千元）",
    "B": "中（情感/生活·百元以内·需多次培育）",
    "C": "低（娱乐注意力消耗型·付费意愿弱）",
}

# ──────────────────────────────────────────────────────────────────────────────
# 层B: 六路径门槛/天花板/适配（方法论§二·层B）
# ──────────────────────────────────────────────────────────────────────────────

# R-M2 内容类型 → 主路径方向
# 通过关键词从账号内容识别内容类型
_CONTENT_TYPE_HINTS: list[tuple[list[str], str]] = [
    (["知识", "科普", "教", "学", "课", "干货", "方法", "技巧", "成长", "副业", "考证", "咨询", "律师", "财税", "育儿", "健康", "职场"], "教"),
    (["颜值", "才艺", "舞蹈", "唱歌", "搞笑", "日常", "vlog", "生活", "美食", "吃播", "探店"], "秀"),
    (["测评", "评测", "种草", "好物", "分享", "推荐", "带货", "选品", "橱窗", "比较", "开箱"], "评"),
    (["情感", "陪伴", "婚姻", "女性", "妈妈", "育儿", "宝妈", "暖心", "陪你"], "陪"),
    (["探店", "到店", "门店", "实体", "B端", "招商", "加盟", "工厂", "产业带", "源头", "直供"], "引"),
]

# R-M1 粉丝关系深度（按互动率/粉丝量推断）
def _relationship_depth(account: dict[str, Any]) -> str:
    """推断粉丝关系深度：浅/中/深。
    用 avg_like / (follower+1) 作为互动率代理指标。
    """
    fol = account.get("follower") or 0
    avg_like = account.get("avg_like") or 0
    aweme = account.get("aweme_count") or 0
    # 互动率 = 均赞 / (粉丝+1)
    rate = avg_like / (fol + 1) if fol > 0 else 0.0
    # 深：互动率高（>3%）且粉丝量中等（不是泛流量爆量） → 说明粉丝真的关注
    if rate >= 0.03 and fol < 500_000:
        return "深"
    # 中：有一定互动率 or 发了一定量内容
    if rate >= 0.01 or (fol > 1000 and aweme > 20):
        return "中"
    return "浅"


def _content_type(account: dict[str, Any]) -> str:
    """R-M2：从账号内容推断内容类型（教/秀/评/陪/引）。"""
    sig = (account.get("signature") or "")
    tags = " ".join(account.get("hashtags") or [])
    text = sig + " " + tags
    for kws, ctype in _CONTENT_TYPE_HINTS:
        if any(k in text for k in kws):
            return ctype
    return "秀"  # 默认：无明确标记则当作才艺/生活展示


# 六路径完整定义
_SIX_PATHS = {
    "广告合作": {
        "门槛": "5万粉+",
        "天花板": "中高（粉×0.03–0.1元/条·经验区间·需校准）",
        "适配赛道": ["美妆", "数码", "财经", "知识"],
        "适配内容类型": ["秀", "评"],
        "适配档位": ["A", "B"],
    },
    "带货佣金": {
        "门槛": "1000粉开橱窗",
        "天花板": "高（依选品·GMV=播放×进店率×成交率×客单×佣金·经验公式·需校准）",
        "适配赛道": ["电商", "带货", "生活方式", "美妆", "母婴", "家居"],
        "适配内容类型": ["评", "秀"],
        "适配档位": ["A", "B"],
    },
    "知识付费": {
        "门槛": "几千精准粉即可",
        "天花板": "极高（9.9→3万+·私域课程/咨询·经验区间·需校准）",
        "适配赛道": ["知识", "职场", "健康", "育儿", "个人成长"],
        "适配内容类型": ["教"],
        "适配档位": ["S", "A"],
    },
    "直播打赏": {
        "门槛": "开通直播即可",
        "天花板": "中低（平台抽成30–55%·经验区间·需校准）",
        "适配赛道": ["颜值", "才艺", "情感"],
        "适配内容类型": ["秀", "陪"],
        "适配档位": ["B", "C"],
    },
    "平台激励": {
        "门槛": "1万粉",
        "天花板": "极低（不作核心变现路径·建议只作补充）",
        "适配赛道": ["全赛道"],
        "适配内容类型": ["教", "秀", "评", "陪", "引"],
        "适配档位": ["A", "B", "C", "S"],
    },
    "私域变现": {
        "门槛": "任意阶段均可起步",
        "天花板": "最高（私域年贡献≈公域5–20倍·经验区间·需校准）",
        "适配赛道": ["B端", "知识", "情感", "职场"],
        "适配内容类型": ["教", "陪", "引"],
        "适配档位": ["S", "A", "B"],
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# 公共函数
# ──────────────────────────────────────────────────────────────────────────────

def _build_text(account: dict[str, Any]) -> str:
    """拼接账号文本用于识别。"""
    sig = account.get("signature") or ""
    tags = " ".join(account.get("hashtags") or [])
    nick = account.get("nickname") or ""
    return sig + " " + tags + " " + nick


def classify_track_value(account: dict[str, Any]) -> dict[str, Any]:
    """层A: 赛道商业价值档（S/A/B/C 五档·零 LLM·规则驱动）。

    复用 account_report._track 识别赛道名称，再按本模块表映射到商业价值档。

    Returns:
        {
            "grade": "S"|"A"|"B"|"C",
            "track_name": str,          # 来自 _track()
            "fan_unit_value": str,      # 单粉价值描述（经验区间）
            "roi_stars": str,           # 投产比★数
            "grade_reason": str,        # 说明
            "calibration_note": str,    # 必须标"需校准"
        }
    """
    text = _build_text(account)
    track_name, _track_why = _track(text)
    is_biz = _is_business(text)

    # B2B/产业带货直接 S 档
    if is_biz:
        return {
            "grade": "S",
            "track_name": track_name,
            "fan_unit_value": "极高（50–500元/线索 · 10–50元/粉·经验区间·需校准）",
            "roi_stars": "★★★★★",
            "grade_reason": "B端/产业带货号·垂直业务明确·精准引流变现效率高·2万粉即可回本",
            "calibration_note": "⚠️ 单粉价值为行业经验区间（需校准）——请结合你的真实成交数据校准。",
        }

    # 按 _TRACK_VALUE_TABLE 逐条匹配（track_name 或 text 含关键词）
    combined = track_name + " " + text
    for kws, grade, fan_unit, stars, reason in _TRACK_VALUE_TABLE:
        if any(k in combined for k in kws):
            return {
                "grade": grade,
                "track_name": track_name,
                "fan_unit_value": fan_unit,
                "roi_stars": stars,
                "grade_reason": reason,
                "calibration_note": "⚠️ 单粉价值为行业经验区间（需校准）——请结合你的真实成交数据校准。",
            }

    # 默认 C 档（匹配不到）
    return {
        "grade": "C",
        "track_name": track_name,
        "fan_unit_value": "低（0.1–2元/粉·经验区间·需校准）",
        "roi_stars": "★★☆☆☆",
        "grade_reason": "赛道方向未能识别为高商业价值细分·建议明确赛道定位",
        "calibration_note": "⚠️ 单粉价值为行业经验区间，需结合你的真实成交数据校准。",
    }


def match_monetization_path(account: dict[str, Any],
                            track: dict[str, Any]) -> dict[str, Any]:
    """层B + R-C1: 变现路径推荐（主/次/禁忌·门槛达成判断）。

    依据三子规则：
      R-M1 粉丝关系深度（浅/中/深）
      R-M2 内容类型（教/秀/评/陪/引）
      R-M3 赛道付费意愿（由档位代理）

    Returns:
        {
            "primary": str,             # 主路径
            "primary_reason": str,
            "secondary": str,           # 次路径
            "secondary_reason": str,
            "forbidden": str,           # 禁忌路径
            "forbidden_reason": str,
            "threshold_met": bool,      # 当前粉丝是否达主路径门槛
            "threshold_note": str,
            "relationship_depth": str,  # R-M1
            "content_type": str,        # R-M2
            "pay_intent": str,          # R-M3
        }
    """
    fol = account.get("follower") or 0
    grade = track.get("grade", "C")
    depth = _relationship_depth(account)
    ctype = _content_type(account)
    pay_intent = _TRACK_PAY_INTENT.get(grade, "低")
    is_biz = _is_business(_build_text(account))

    # —— 主路径决策树（R-M1 × R-M2 × R-M3 × 档位）——
    # 规则顺序：高价值优先、已达门槛优先、适配 ctype
    if grade == "S" and ctype == "教":
        primary = "知识付费"
        primary_reason = "S档高付费意愿赛道+教型内容·几千精准粉可起步·天花板极高"
        secondary = "私域变现"
        secondary_reason = "知识付费引流私域后沉淀·年贡献比公域高5–20倍"
        forbidden = "直播打赏"
        forbidden_reason = "S档内容溢价依靠专业深度·打赏模式是颜值/才艺赛道天花板·资源错配"
    elif grade == "S" and (ctype == "引" or is_biz):
        primary = "私域变现"
        primary_reason = "B端/到店型内容·私域变现天花板最高·粉丝=潜在合作客户"
        secondary = "知识付费"
        secondary_reason = "B端账号可封装「选品/供应链」经验做课·增加变现维度"
        forbidden = "直播打赏"
        forbidden_reason = "B端账号打赏路径不匹配受众属性·浪费信任资产"
    elif grade == "S":
        # S 档 ctype 为秀/陪/评
        primary = "私域变现"
        primary_reason = "S档付费意愿极高·先建信任再引私域·天花板最高"
        secondary = "知识付费"
        secondary_reason = "S档内容深度适合知识付费·可后续叠加"
        forbidden = "平台激励"
        forbidden_reason = "S档账号做平台激励是资源错配·天花板极低"
    elif grade == "A" and ctype == "评":
        primary = "带货佣金"
        primary_reason = "A档电商赛道+评测内容·天花板高·1000粉即可开橱窗"
        secondary = "广告合作"
        secondary_reason = "A档达5万粉后品牌预算丰富·粉×0.03–0.1元/条"
        forbidden = "直播打赏"
        forbidden_reason = "评测内容受众消费导向·打赏模式不匹配"
    elif grade == "A" and ctype == "教":
        primary = "知识付费"
        primary_reason = "A档知识/美妆专业内容·知识付费是性价比最高路径"
        secondary = "带货佣金"
        secondary_reason = "可边讲干货边带产品·自然嵌入"
        forbidden = "直播打赏"
        forbidden_reason = "A档内容溢价点在专业知识·打赏浪费信任资产"
    elif grade == "A":
        # A 档其他 ctype
        primary = "带货佣金"
        primary_reason = "A档电商赛道·带货佣金门槛低（1000粉）·天花板高"
        secondary = "广告合作"
        secondary_reason = "粉丝积累至5万+可开商单·品牌预算充足"
        forbidden = "平台激励"
        forbidden_reason = "A档账号平台激励天花板极低·不作核心路径"
    elif grade == "B" and ctype == "陪":
        primary = "私域变现"
        primary_reason = "情感/陪伴内容粉丝黏性高·引私域信任转化强"
        secondary = "广告合作"
        secondary_reason = "B档情感账号达5万粉可接相关品牌商单"
        forbidden = "带货佣金"
        forbidden_reason = "情感赛道硬推带货掉粉·信任关系受损"
    elif grade == "B":
        primary = "广告合作"
        primary_reason = "B档内容适合本地/生活类商单·门槛5万粉"
        secondary = "带货佣金"
        secondary_reason = "美食/探店可带食品/厨具等相关品·自然转化"
        forbidden = "知识付费"
        forbidden_reason = "B档赛道付费意愿中等·知识付费路径变现周期长"
    else:
        # C 档
        primary = "直播打赏"
        primary_reason = "C档颜值/才艺/娱乐内容·打赏是最直接路径"
        secondary = "广告合作"
        secondary_reason = "C档需50万+粉才有规模·达到后可接泛娱乐商单"
        forbidden = "知识付费"
        forbidden_reason = "C档赛道付费意愿低·知识付费路径不匹配受众"

    # 深度修正（R-M1·关系深→升级私域）
    if depth == "深" and primary != "私域变现" and grade in ("S", "A", "B"):
        secondary = "私域变现"
        secondary_reason = "你的互动率显示粉丝关系深（私信/追更型）·私域变现天花板已开·建议叠加"

    # 浅关系修正（R-M1·浅→远离知识付费）
    if depth == "浅" and primary == "知识付费":
        primary_reason += "（注：互动率偏低·先提升粉丝关系深度·再做知识付费转化·信任铺垫期≥20条）"

    # 门槛判断（主路径）
    threshold_met = False
    threshold_note = ""
    if primary == "知识付费":
        threshold_met = fol >= 1000  # 几千精准粉·宽松判定
        threshold_note = f"你现在 {fol:,} 粉。知识付费主看精准度不看量·1000精准粉可尝试·但需先建立专业权威形象。"
    elif primary == "带货佣金":
        threshold_met = fol >= 1000
        threshold_note = f"你现在 {fol:,} 粉。1000粉可开橱窗·门槛已达✅" if threshold_met else f"你现在 {fol:,} 粉。还需 {1000-fol} 粉到达开橱窗门槛。"
    elif primary == "广告合作":
        threshold_met = fol >= 50000
        threshold_note = f"你现在 {fol:,} 粉。广告合作通常需要5万粉+。" + ("门槛已达✅" if threshold_met else f"还差 {50000-fol} 粉。")
    elif primary == "私域变现":
        threshold_met = True
        threshold_note = "私域变现无硬门槛·任意阶段均可开始建私域·越早越好。"
    elif primary == "直播打赏":
        threshold_met = True
        threshold_note = "直播打赏开通直播即可·门槛低·但天花板也低（平台抽成30–55%）。"
    else:  # 平台激励
        threshold_met = fol >= 10000
        threshold_note = f"你现在 {fol:,} 粉。平台激励通常需1万粉。" + ("门槛已达✅" if threshold_met else f"还差 {10000-fol} 粉。")

    return {
        "primary": primary,
        "primary_reason": primary_reason,
        "secondary": secondary,
        "secondary_reason": secondary_reason,
        "forbidden": forbidden,
        "forbidden_reason": forbidden_reason,
        "threshold_met": threshold_met,
        "threshold_note": threshold_note,
        "relationship_depth": depth,
        "content_type": ctype,
        "pay_intent": pay_intent,
    }


def estimate_roi(account: dict[str, Any],
                 path: dict[str, Any]) -> dict[str, Any]:
    """层C: ROI 估算（经验区间·必须标"需真实数据校准"）。

    严格诚实：所有数值都是经验公式的区间，不是精确预测。
    禁止冒充精确数字——必须带免责标注。

    Returns:
        {
            "ltv_cac_range": str,       # LTV/CAC 区间描述
            "payback_months": str,      # 回本周期描述
            "monthly_output_formula": str,  # 月产出估算公式
            "health_threshold": str,    # 健康判据（LTV/CAC>3）
            "calibration_note": str,    # 必须标"需校准"
            "black_box_gaps": list[str],# 拿不到的数据项
        }
    """
    fol = account.get("follower") or 0
    avg_like = account.get("avg_like") or 0
    primary = path.get("primary", "")
    grade = path.get("_grade", "C")  # 内部透传

    # 互动率代理（avg_like / follower）
    engagement_proxy = avg_like / (fol + 1) if fol > 0 else 0.0
    eng_desc = "高互动率（>3%）" if engagement_proxy >= 0.03 else \
               "中互动率（1–3%）" if engagement_proxy >= 0.01 else "低互动率（<1%）"

    # 按路径给出经验公式和区间
    if primary == "知识付费":
        formula = (
            f"月产出 ≈ 粉丝数({fol:,}) × 引流到私域率(5–15%·黑盒) × 付费率(3–10%) × 课程单价(9.9–3000元)。"
            f"保守估算：{fol:,} × 5% × 3% × 99元 ≈ {int(fol * 0.05 * 0.03 * 99):,}元/月"
            f"（极度粗估·⚠️ 引流率/付费率是行业均值·你的真实值可能差10倍以上）"
        )
        payback = "知识付费投入产出：内容成本低·一门课多次售卖·通常2–6个月回本（经验区间）"
        ltv_cac = "LTV/CAC 通常 5–20（健康·知识付费低获客成本·高复购）·经验区间·需校准"
    elif primary == "带货佣金":
        formula = (
            f"月产出 ≈ 月播放量 × 进店率(1–3%·黑盒) × 成交率(1–5%·黑盒) × 客单价 × 佣金率(5–30%)。"
            f"简化：若月均播放50万 × 1% 进店 × 2% 成交 × 客单价100元 × 15%佣金 ≈ 1,500元/月。"
            f"（⚠️ 进店率/成交率是平台黑盒·需你自己后台数据校准）"
        )
        payback = "带货佣金：选品和信任是关键·前期0粉到1000粉阶段建议只打磨内容·不急转化·通常3–9个月形成稳定产出（经验区间）"
        ltv_cac = "LTV/CAC：带货靠单次成交·复购依选品·LTV/CAC 在2–8之间浮动（经验区间·需校准）"
    elif primary == "广告合作":
        est_price = int(fol * 0.05)  # 粉×0.05元 粗估中位
        formula = (
            f"商单报价参考：粉丝数({fol:,}) × 0.03–0.1元 ≈ {int(fol*0.03):,}–{int(fol*0.1):,}元/条。"
            f"中位参考：约 {est_price:,}元/条（经验公式·需巨量星图实际报价校准）。"
            f"月产出 ≈ 商单数 × 单条报价（商单数由你粉丝量/互动率/赛道决定·黑盒）"
        )
        payback = "广告合作：达5万粉后品牌才主动找；前期主动投稿/星图报价·通常6–12个月稳定商单流（经验区间）"
        ltv_cac = "LTV/CAC：单次商单LTV低·靠持续合作积累·通常在3–6（经验区间·需校准）"
    elif primary == "私域变现":
        formula = (
            f"私域年贡献 ≈ 公域的5–20倍（方法论结论·经验区间）。"
            f"核心公式：月产出 ≈ 私域人数 × 月活率(20–40%) × 月付费率(5–15%) × 客单价。"
            f"（⚠️ 私域人数/月活率需你实际沉淀后才能估·现在无法给精确值）"
        )
        payback = "私域变现：前期建社群/引流周期长（3–12个月）·但复购率最高·一旦启动回本快（经验区间）"
        ltv_cac = "LTV/CAC：私域最高·LTV/CAC 可达10–50（高复购·低获客成本·经验区间·需校准）"
    elif primary == "直播打赏":
        formula = (
            f"月收入 ≈ 直播时长 × 在线人数 × 人均打赏（行业均值极低·0.1–1元/人·平台抽成30–55%）。"
            f"需每天直播2–4小时维持·天花板取决于才艺/情感吸引力·黑盒。"
        )
        payback = "直播打赏：起步快·天花板低·平台抽成重·不建议作唯一路径（经验评估）"
        ltv_cac = "LTV/CAC：打赏LTV低·依赖高频在线·通常 1–3（偏低·需多路变现）·经验区间·需校准"
    else:  # 平台激励
        formula = "平台激励：按播放量分成·通常极低（每千次播放0.1–0.5元·经验区间）·不作核心路径。"
        payback = "平台激励：不建议作回本核心路径（天花板极低）"
        ltv_cac = "LTV/CAC：极低·不作参考"

    # 健康判据（方法论§二·层C）
    health = "LTV/CAC > 3 = 健康 · < 1 = 亏损 · 回本周期 < 6个月为优"

    return {
        "ltv_cac_range": ltv_cac,
        "payback_months": payback,
        "monthly_output_formula": formula,
        "health_threshold": health,
        "calibration_note": (
            "⚠️ 以上所有数值均为「行业经验区间」，不是对你账号的确切数字承诺。"
            "进店率/完播率/成交率/粉丝画像/真实销量是平台黑盒，需用你自己的后台数据校准。"
            "相对量级参考有效；具体账单请结合真实运营数据。"
        ),
        "black_box_gaps": [
            "完播率（平台黑盒·需后台截图投喂）",
            "流量来源分布（黑盒）",
            "真实进店率/成交率（黑盒）",
            "粉丝画像（黑盒·影响付费率估算）",
        ],
    }


def render_commercial_section(account: dict[str, Any],
                              track_value: dict[str, Any] | None = None) -> str:
    """渲染"商业转化诊断"报告段（Markdown·说人话·三层串起·诚实标）。

    可单独调用，也可由 build_report 在末尾追加。
    track_value = classify_track_value(account) 的结果；若不传则内部计算。
    """
    if track_value is None:
        track_value = classify_track_value(account)

    path = match_monetization_path(account, track_value)
    # 透传档位给 ROI 估算
    path["_grade"] = track_value.get("grade", "C")
    roi = estimate_roi(account, path)

    fol = account.get("follower") or 0
    nick = account.get("nickname") or "你"
    grade = track_value["grade"]
    track_name = track_value["track_name"]

    L: list[str] = []
    P = L.append

    P("## 商业转化诊断（三层）")
    P("")
    P("> 这是三层商业诊断：赛道值不值做 → 你该走哪条路变现 → 大概能赚多少。")
    P("> 所有数字都是**行业经验区间，不是对你账号的精确预测**——说完你知道方向就够了。")
    P("")

    # —— 层A：赛道商业价值 ——
    P("### 层A · 你所在赛道值多少钱")
    P("")
    grade_label = {
        "S": "S档（顶级·单粉极贵）",
        "A": "A档（高价值）",
        "B": "B档（中等价值）",
        "C": "C档（低价值·量大才行）",
    }.get(grade, grade)
    P(f"**你的赛道「{track_name}」商业价值：{grade_label}**")
    P("")
    P(f"- 单粉价值参考：{track_value['fan_unit_value']}")
    P(f"- 投产比：{track_value['roi_stars']}")
    P(f"- 为什么这样判断：{track_value['grade_reason']}")
    P("")

    # 剪刀差警示（C档）
    if grade == "C":
        P("⚠️ **流量大≠赚钱**：同样每月投入6000–1万元，搞笑/颜值赛道需要50万粉才能回本；"
          "而医美/知识付费只需2万粉——**流量盘越大的赛道，投产比反而越差。**")
        P("建议：考虑向更垂直、付费意愿更高的细分方向转型。")
        P("")

    P(f"> {track_value['calibration_note']}")
    P("")

    # —— 层B：变现路径推荐 ——
    P("### 层B · 你该走哪条路变现")
    P("")
    P(f"**粉丝关系深度（R-M1）：「{path['relationship_depth']}」** · "
      f"内容类型（R-M2）：「{path['content_type']}」 · "
      f"赛道付费意愿（R-M3）：{path['pay_intent'][:20]}…")
    P("")

    threshold_icon = "✅" if path["threshold_met"] else "⏳"
    P(f"**主路径 {threshold_icon}：{path['primary']}**")
    P(f"- 为什么：{path['primary_reason']}")
    P(f"- 门槛情况：{path['threshold_note']}")
    P("")

    P(f"**次路径：{path['secondary']}**")
    P(f"- 为什么：{path['secondary_reason']}")
    P("")

    P(f"**❌ 禁忌路径：{path['forbidden']}**")
    P(f"- 不建议走这条：{path['forbidden_reason']}")
    P("")

    # 过渡设计提示（方法论§三·三段式）
    P("**从内容到转化的关键纪律：**")
    P("- 前20–50条：纯价值内容，禁止过早变现（信任铺垫期）")
    P("- 之后：3:7 内容比植入（产品即工具·钩好奇心，不是购买欲）")
    P("- 只有粉丝主动询问才启动显性转化·广告≤30%红线")
    P("> 铁律：买单是顺理成章，不是说服；需要费力说服 = 上游信任/精准出了问题。")
    P("")

    # —— 层C：ROI 估算 ——
    P("### 层C · 大概能赚多少（经验区间·诚实说）")
    P("")
    P(f"**月产出估算（{path['primary']}路径）：**")
    P(f"{roi['monthly_output_formula']}")
    P("")
    P(f"**回本周期参考：** {roi['payback_months']}")
    P("")
    P(f"**LTV/CAC 参考：** {roi['ltv_cac_range']}")
    P("")
    P(f"**健康判据：** {roi['health_threshold']}")
    P("")

    # 黑盒诚实标
    P("**⚠️ 以下数据平台不公开（黑盒），上面的估算无法精确——想要更准确的诊断，把后台截图传给我：**")
    for gap in roi["black_box_gaps"]:
        P(f"- {gap}")
    P("")
    P(f"> {roi['calibration_note']}")
    P("")

    return "\n".join(L)
