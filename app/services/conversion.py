"""精准转化方案 · 确定性·规则驱动·零 LLM · v1.0

方法论真源:运营报告/probe-commercial-conversion-methodology-v1.0.md §三
  - R-C2 转化就绪信号(粉丝量+互动信号 → 三段式过渡阶段)
  - R-C3 漏斗诊断(从上往下找第一卡点·完播是黑盒)
  - R-C4 钩子配置(结合视听六层·一条最多3钩)
  - R-C5 过渡红线(前20-50条禁显性转化·广告≤30%)

诚实标注:
  - 完播率是黑盒(抖音不对外开放)·用互动率代理·报告诚实标"需投喂"
  - 视听六层依赖 Qwen3-Omni(外部 LLM)·置信度<0.5 的字段不参与钩子推断
  - 漏斗从完播开始·黑盒的用互动率代理并标注
"""
from __future__ import annotations

from typing import Any

# ──────────────────────────────────────────────────────────────────────────────
# 一、过渡阶段诊断(R-C2 · R-C5)
# ──────────────────────────────────────────────────────────────────────────────

# 三段式阈值(方法论 §三 过渡设计)
_STAGE_TRUST_MAX_WORKS = 50     # 信任铺垫期:发布总数 < 这个
_STAGE_TRUST_MAX_FOL = 5_000    # 信任铺垫期:粉丝 < 这个
_STAGE_SOFT_MAX_FOL = 50_000    # 软植入期:粉丝 < 这个

# 互动信号:用评论/收藏判断粉丝关系深度(R-M1)
# 完播是黑盒·用评论率和收藏率代理"有没有留"
_COMMENT_RATE_DEEP = 0.05   # 评论 / 点赞 ≥ 5% → 深互动信号
_COLLECT_RATE_DEEP = 0.10   # 收藏 / 点赞 ≥ 10% → 深互动信号


def _avg(works: list[dict], key: str) -> float:
    vals = [(w.get(key) or 0) for w in works if isinstance(w, dict)]
    return sum(vals) / len(vals) if vals else 0.0


def _interaction_depth(account: dict, works: list[dict]) -> str:
    """从账号均值和视频样本判断粉丝关系深度(浅/中/深)。
    浅=刷了就走 · 中=回访/留言 · 深=私信/追更"""
    avg_like = account.get("avg_like") or 0
    if avg_like == 0:
        return "浅"
    avg_comment = _avg(works, "comment") if works else 0.0
    avg_collect = _avg(works, "collect") if works else 0.0
    comment_rate = avg_comment / avg_like if avg_like else 0.0
    collect_rate = avg_collect / avg_like if avg_like else 0.0
    if comment_rate >= _COMMENT_RATE_DEEP or collect_rate >= _COLLECT_RATE_DEEP:
        return "深"
    if comment_rate >= 0.02 or collect_rate >= 0.04:
        return "中"
    return "浅"


def diagnose_transition_stage(
    account: dict[str, Any],
    works: list[dict[str, Any]],
) -> dict[str, Any]:
    """判断账号当前所处的三段式过渡阶段。

    三段式(方法论 §三 过渡设计 · R-C5 红线):
      ① 信任铺垫 — 前20-50条纯价值·禁过早变现
      ② 软植入   — 3:7内容比·产品即工具·钩好奇非购买欲
      ③ 显性转化 — 主动询问才启动·广告≤30%·只接强相关

    Args:
        account: 账号数据。需含 follower / aweme_count(发布总数)。
        works:   逐条视频样本列表(用于互动深度)。

    Returns:
        {stage, reason, next_step, interaction_depth, hard_limit}
    """
    fol = account.get("follower") or 0
    aweme = account.get("aweme_count") or 0
    depth = _interaction_depth(account, works)

    # ① 信任铺垫(双判：发布数 OR 粉丝数任一未达阈值)
    if aweme < _STAGE_TRUST_MAX_WORKS or fol < _STAGE_TRUST_MAX_FOL:
        return {
            "stage": "信任铺垫期",
            "reason": (
                f"发布 {aweme} 条、{fol} 个粉丝——"
                + ("发布量还不足(建议先发满50条)" if aweme < _STAGE_TRUST_MAX_WORKS else "")
                + ("粉丝积累不足(建议先到5000)" if fol < _STAGE_TRUST_MAX_FOL else "")
                + "，还没到植入时机"
            ),
            "next_step": (
                "先把内容做扎实、发够量、让系统认清你是谁。"
                "这阶段每条都要服务「他为什么关注我」，不碰转化，稳住。"
            ),
            "interaction_depth": depth,
            "hard_limit": "❌ R-C5红线：禁止显性转化·不接商单·不放外链·不植入产品",
        }

    # ② 软植入(粉丝 < 5万 且 已过信任期)
    if fol < _STAGE_SOFT_MAX_FOL:
        return {
            "stage": "软植入期",
            "reason": (
                f"发布 {aweme} 条、{fol} 个粉丝——有了基础，"
                f"互动深度「{depth}」，粉丝开始认可你"
            ),
            "next_step": (
                "内容:转化比例控制在 3:7(10条里最多3条带产品/业务)。"
                "植入逻辑：产品是工具不是主角，勾好奇而非购买欲。"
                "评论区出现「在哪买/怎么联系」才是往显性转化走的信号。"
            ),
            "interaction_depth": depth,
            "hard_limit": "⚠️ R-C5红线：广告比例≤30%·只接强相关品牌·不用高压销售话术",
        }

    # ③ 显性转化(≥5万粉 且 已过信任期)
    return {
        "stage": "显性转化期",
        "reason": (
            f"发布 {aweme} 条、{fol} 个粉丝——"
            f"互动深度「{depth}」，已具备成交基础"
        ),
        "next_step": (
            "主动评论区/私信引导成交。"
            "广告硬红线：单条广告比例≤30%、只接和内容强相关品牌。"
            "买单是顺理成章——如果粉丝要被说服才买，说明上游信任或精准度出了问题。"
        ),
        "interaction_depth": depth,
        "hard_limit": "⚠️ R-C5红线：广告≤30%·禁接弱相关品牌·禁硬推销",
    }


# ──────────────────────────────────────────────────────────────────────────────
# 二、单条视频转化钩子建议(R-C4 + 视听六层)
# ──────────────────────────────────────────────────────────────────────────────

# 视听六层字段的转化相关性映射
# 只用置信度 ≥ 0.5 的字段(黑盒字段诚实不用)
_SL_CONF_MIN = 0.5


def _sl_val(six_layer: dict | None, layer: str, field: str) -> tuple[str | None, float]:
    """安全取视听六层某字段的 (值, 置信度)。置信度<阈值返回 (None, conf)。"""
    if not six_layer:
        return None, 0.0
    v = (six_layer.get(layer) or {}).get(field) or {}
    val = v.get("v") if isinstance(v, dict) else None
    conf = float(v.get("conf", 0)) if isinstance(v, dict) else 0.0
    if conf < _SL_CONF_MIN:
        return None, conf
    return val, conf


def _edit_pace(six_layer: dict | None) -> str | None:
    val, _ = _sl_val(six_layer, "visual", "edit_pace")
    return val  # 快|中|慢|None


def _speech_pace(six_layer: dict | None) -> str | None:
    val, _ = _sl_val(six_layer, "auditory", "speech_pace")
    return val  # 快|中|慢|无口播|None


def _hook_text(six_layer: dict | None) -> str | None:
    """叙事层开头钩子(narrative.hook)——辅助判断需求激活钩是否已有。"""
    val, _ = _sl_val(six_layer, "narrative", "hook")
    return val


def _on_screen(six_layer: dict | None) -> bool | None:
    """是否有人出镜(persona.on_screen)——影响信任钩选口播证据型。"""
    val, conf = _sl_val(six_layer, "persona", "on_screen")
    if val is None:
        return None
    return "有" in str(val)


def _resonance(six_layer: dict | None) -> str | None:
    val, _ = _sl_val(six_layer, "psychology", "resonance")
    return val


def suggest_hooks(
    video: dict[str, Any],
    six_layer: dict[str, Any] | None,
) -> dict[str, Any]:
    """建议单条视频的三钩配置。

    三钩(方法论 §三 单条视频转化钩子·R-C4):
      1. 需求激活钩 — 前3秒痛点(完播前置)
      2. 信任建立钩 — 中段证据/软CTA
      3. 行动引导钩(CTA) — 末段

    一条最多3钩·超过即失效(铁律)。
    视听六层置信度<0.5的字段不参与推断(诚实不冒用黑盒)。

    Args:
        video:     单条视频数据。需含 like/comment/collect/share。
        six_layer: 视听六层结构(可为 None 或 analyze_audiovisual 返回的 six_layer)。

    Returns:
        {demand_hook, trust_hook, cta_type, cta_note,
         six_layer_used, six_layer_ceiling_note}
    """
    like = video.get("like") or 0
    comment = video.get("comment") or 0
    collect = video.get("collect") or 0
    share = video.get("share") or 0

    sl_used = bool(six_layer)
    sl_ceiling_note = None

    # ── 需求激活钩(前3秒痛点) ──
    hook_in_sl = _hook_text(six_layer)
    if hook_in_sl:
        demand_hook = f"开头已有「{hook_in_sl[:30]}」式钩子——验证能抓人后可复制到同系列视频"
    else:
        demand_hook = "前3秒补一句对着目标用户说的痛点句：讲「你遇过这个问题吗？」比「今天分享一个方法」完播率更高"

    # ── 信任建立钩(中段证据) ──
    on_screen = _on_screen(six_layer)
    resonance = _resonance(six_layer)

    if on_screen is True:
        # 有人出镜 → 口播证据型更有力
        trust_hook = (
            "有人出镜·中段用口播说「我自己用的就是这个」"
            "（比「这产品很好用」信任度高）"
            "——第一人称亲历比广告话术信任度高3-5倍"
        )
    elif on_screen is False:
        trust_hook = "无人出镜·中段用数字/对比/前后效果画面建立信任(字幕+画面双层叠加)"
    else:
        # 视听层没有该字段 or 置信度低
        trust_hook = "中段补证据帧：真实使用画面/对比截图/评论截图(任选一)，比口说更可信"
        if sl_used:
            sl_ceiling_note = "⚠️ 视听六层置信度不足·出镜字段未用·上限<50%准确率·仅供参考"

    # 互动结构辅助判断(商业信号优先级:收藏>评论>转发·完播黑盒)
    total_inter = comment + collect + share
    inter_rate = total_inter / (like + 1)

    if collect > comment and collect > 0:
        trust_hook += "（这条收藏量占优·说明内容有「以后用得上」属性·信任钩要强化「结果」而非「过程」）"

    # ── CTA 行动引导(末段·按阶段) ──
    # 用数据信号推断最合适的 CTA 类型
    if collect > like * 0.15:
        cta_type = "私信钩"
        cta_note = "收藏率高说明已有意向·末段加「私信我获取完整方案」比「关注」成交更近"
    elif comment > like * 0.05:
        cta_type = "评论钩"
        cta_note = "评论活跃·末段用问题引评论(「你遇到过吗？评论区告诉我」)·顺带建立讨论社区"
    elif share > like * 0.05:
        cta_type = "转发钩"
        cta_note = "转发比例高·这条内容有传播性·末段可直接说「觉得有用就转发给需要的朋友」"
    else:
        cta_type = "关注钩"
        cta_note = "互动信号不强·先做关注钩·下一条同主题发出时收到推送才有累积效应"

    if sl_used and sl_ceiling_note is None:
        # 编辑节奏影响 CTA 时机
        ep = _edit_pace(six_layer)
        if ep == "快":
            cta_note += "（剪辑快·CTA字幕要在最后3秒单帧停留·不然看不见）"
        elif ep == "慢":
            cta_note += "（剪辑慢·CTA可在倒数10秒左右埋入·给观众思考余地）"

    return {
        "demand_hook": demand_hook,
        "trust_hook": trust_hook,
        "cta_type": cta_type,
        "cta_note": cta_note,
        "six_layer_used": sl_used,
        "six_layer_ceiling_note": sl_ceiling_note,
    }


# ──────────────────────────────────────────────────────────────────────────────
# 三、转化漏斗诊断(R-C3)
# ──────────────────────────────────────────────────────────────────────────────

# 方法论漏斗阈值
# 完播≥30% / 互动≥3%（互动率 = (comment+collect+share)/like·完播是黑盒用互动代理）
_FUNNEL_ENGAGE_THRESHOLD = 0.03    # 互动率(comment+collect+share)/like 阈值
_FUNNEL_COMMENT_RATE = 0.02        # 评论/点赞 阈值(互动高进主页少·需主页优化)
_FUNNEL_COLLECT_RATE = 0.03        # 收藏/点赞 阈值
_FUNNEL_SHARE_RATE = 0.02          # 转发/点赞 阈值


def diagnose_funnel(
    account: dict[str, Any],
    video: dict[str, Any],
) -> dict[str, Any]:
    """转化漏斗诊断：从上往下找第一个卡点，不往下游打补丁。

    漏斗(方法论 §三 转化漏斗诊断·R-C3):
      曝光 → 完播(≥30%) → 互动(≥3%) → 进主页 → 关注 → 私信 → 成交 → 复购

    诚实约束:
      完播率是黑盒(抖音不对外开放)·无法直接测量。
      若账号未投喂(无完播数据)→ 用互动率代理完播层·标"需投喂"。

    Args:
        account: 账号数据。需含 avg_like / follower / aweme_count。
        video:   单条视频数据。需含 like/comment/collect/share/play(可选)。

    Returns:
        {
          first_bottleneck,   # 第一卡点名称
          root_cause,         # 根因
          action,             # 优化动作
          funnel_blackbox,    # 是否完播黑盒(True=需投喂)
          funnel_note,        # 诚实标注
        }
    """
    like = video.get("like") or 0
    comment = video.get("comment") or 0
    collect = video.get("collect") or 0
    share = video.get("share") or 0
    # play 是可选的·有则用·无则黑盒
    play = video.get("play") or video.get("play_count") or 0

    avg_like = account.get("avg_like") or 0
    fol = account.get("follower") or 0
    aweme = account.get("aweme_count") or 0

    # 计算互动率(comment+collect+share)/like
    total_inter = comment + collect + share
    inter_rate = total_inter / (like + 1)

    # 完播层：黑盒判断
    # 有 play 数据(理论上是第三方外推·抖音不开放真完播)→ 用来做相对参考
    # 无 play → 纯黑盒·用互动率代理
    if play > 0:
        # play 是黑盒外推值·不精确·只做参考
        finish_proxy = like / (play + 1) if play else 0.0
        completion_blackbox = False
        bb_note = (
            "⚠️ 完播率黑盒：此处 play_count 是第三方外推值·非抖音后台真实完播率。"
            "真完播率需账号主在抖音创作者中心查阅并投喂。"
        )
    else:
        finish_proxy = None
        completion_blackbox = True
        bb_note = (
            "⚠️ 完播率黑盒：抖音不对外开放完播数据·无法直接测量。"
            "以下用互动率代理。如需精准诊断，账号主需投喂抖音创作者中心后台截图。"
        )

    # ── 从上往下找第一卡点(方法论铁律：找到第一个就停·不往下游补丁) ──

    # [层1] 完播层(≥30%)
    # 无法直接测完播·用"互动率极低"作为完播差的信号
    # 互动率<0.5% 且 like 很少 → 大概率完播就差(没看完的人不会互动)
    if finish_proxy is not None and finish_proxy < 0.05:
        # 点赞/播放 < 5% → 完播不足信号
        return {
            "first_bottleneck": "完播率(第一层卡点)",
            "root_cause": "开头没抓住·大量用户几秒就划走(点赞/播放比<5%)",
            "action": (
                "改前3秒：用痛点句/悬念/反常识开头；"
                "前3秒不能有片头Logo/黑屏/自我介绍。"
                "检查：「如果只看前3秒，这条值不值得看完？」"
            ),
            "funnel_blackbox": completion_blackbox,
            "funnel_note": bb_note,
        }

    # 用互动率代理完播·低互动=大概率完播不够
    if inter_rate < 0.005 and like < avg_like * 0.3:
        return {
            "first_bottleneck": "完播层代理(互动极低·需投喂确认)",
            "root_cause": (
                "互动率极低+点赞明显低于均值·大概率完播不够·"
                "真完播率是黑盒·需后台数据才能确认"
            ),
            "action": (
                "先改前3秒(最高收益)·同时在账号后台查完播数据投喂·"
                "完播<20%优先改开头；完播高但互动低才改中段内容。"
            ),
            "funnel_blackbox": True,
            "funnel_note": bb_note,
        }

    # [层2] 互动层(≥3%)
    if inter_rate < _FUNNEL_ENGAGE_THRESHOLD:
        return {
            "first_bottleneck": "互动层(完播还行·但留不下互动)",
            "root_cause": "没讨论点·用户看完了但没有「想说点什么」的冲动",
            "action": (
                "中段加一个问题/选择/争议：「你是A派还是B派？」"
                "或者末段用「评论告诉我你的情况」替代「关注我」。"
                "评论驱动的视频更容易进精选和二次推荐。"
            ),
            "funnel_blackbox": completion_blackbox,
            "funnel_note": bb_note,
        }

    # [层3] 进主页(互动高·但主页没留住关注)
    # 代理信号：评论高 but 账号粉丝/发布数比例偏低
    comment_rate = comment / (like + 1)
    if comment_rate >= _FUNNEL_COMMENT_RATE:
        # 有评论信号·看主页是否留住了
        follow_proxy = fol / (aweme + 1) if aweme else 0
        if follow_proxy < 50:  # 均粉/作品 < 50 → 主页留存差
            return {
                "first_bottleneck": "主页留存层(有人进来·但没关注)",
                "root_cause": "主页人设不清·Bio没说清「你是谁+给什么+怎么做」·置顶不是最能代表你的那条",
                "action": (
                    "Bio改成一句话：「[你是谁] + [给什么人] + [给他们什么]」；"
                    "置顶换成转化率最高那条(不是播放最高)；"
                    "合集按主题归类让陌生人一眼看懂你的方向。"
                ),
                "funnel_blackbox": completion_blackbox,
                "funnel_note": bb_note,
            }

    # [层4] 关注→私信/成交(互动好·主页也不差·但没私信/询单)
    if collect >= comment and collect > 0:
        # 收藏 > 评论 → 用户"先存着"但没有行动意愿
        return {
            "first_bottleneck": "关注→成交层(有收藏意愿·但无行动路径)",
            "root_cause": "缺明确路径钩：用户想要但不知道「下一步怎么得到」",
            "action": (
                "末段加私信钩：「想要完整方案/资料，私信我「关键词」」；"
                "开启私信自动回复(关键词触发)；"
                "置顶一条专门讲「怎么找到你/怎么购买/怎么合作」的视频。"
            ),
            "funnel_blackbox": completion_blackbox,
            "funnel_note": bb_note,
        }

    # [层5] 成交不复购(所有指标都不差·但业务没转化)
    return {
        "first_bottleneck": "成交层(内容层看起来健康·卡点在转化承接或产品交付)",
        "root_cause": (
            "内容信号不差·卡点可能在："
            "①转化承接(私信无人回/慢回)·"
            "②产品价值承诺与实际交付不对齐·"
            "③缺复购设计"
        ),
        "action": (
            "检查私信响应速度(黄金2小时)；"
            "回访已成交用户问「哪里没达到期望」；"
            "设计复购钩(下单后加微信/社群·不靠平台推送依赖)。"
        ),
        "funnel_blackbox": completion_blackbox,
        "funnel_note": bb_note,
    }


# ──────────────────────────────────────────────────────────────────────────────
# 四、报告段渲染
# ──────────────────────────────────────────────────────────────────────────────

def render_conversion_section(
    account: dict[str, Any],
    video: dict[str, Any],
    works: list[dict[str, Any]] | None,
    six_layer: dict[str, Any] | None,
) -> str:
    """生成报告"精准转化方案"段落(Markdown·说人话)。

    串起三段式过渡 + 钩子建议 + 漏斗诊断，给出一体化转化方案。
    """
    works = works or []

    stage_result = diagnose_transition_stage(account, works)
    hook_result = suggest_hooks(video, six_layer)
    funnel_result = diagnose_funnel(account, video)

    stage = stage_result["stage"]
    depth = stage_result["interaction_depth"]
    next_step = stage_result["next_step"]
    hard_limit = stage_result["hard_limit"]
    stage_reason = stage_result["reason"]

    demand_hook = hook_result["demand_hook"]
    trust_hook = hook_result["trust_hook"]
    cta_type = hook_result["cta_type"]
    cta_note = hook_result["cta_note"]
    sl_ceiling = hook_result.get("six_layer_ceiling_note")

    bottleneck = funnel_result["first_bottleneck"]
    root_cause = funnel_result["root_cause"]
    action = funnel_result["action"]
    funnel_bb_note = funnel_result["funnel_note"]

    L: list[str] = []
    P = L.append

    P("## 精准转化方案")
    P("")
    P("> 不是泛泛「你可以带货」——这是根据你这个号的真实数据，定制的从内容到成交路径。")
    P("")

    # ── A. 你现在在哪个阶段 ──
    P(f"### A. 你的转化阶段：{stage}")
    P("")
    P(f"**判断依据**：{stage_reason}。")
    if depth == "深":
        depth_detail = "评论/收藏比率高，说明已有一批真正认可你的粉丝，转化窗口打开。"
    elif depth == "中":
        depth_detail = "有回访互动，关系在建立中，继续养信任。"
    else:
        depth_detail = "大多数人看完就走，这阶段先专注「让人关注」，不急变现。"
    P(f"**粉丝关系深度**：{depth}互动——{depth_detail}")
    P("")
    P(f"**现阶段该怎么做**：{next_step}")
    P("")
    P(f"{hard_limit}")
    P("")

    # ── B. 这条视频的转化钩子建议 ──
    P("### B. 这条视频的转化钩子（最多3个）")
    P("")
    P("| 钩子 | 建议 |")
    P("|------|------|")
    P(f"| 🎣 需求激活钩（前3秒） | {demand_hook} |")
    P(f"| 🤝 信任建立钩（中段） | {trust_hook} |")
    P(f"| 📣 行动引导钩（末段CTA） | **{cta_type}**：{cta_note} |")
    P("")
    if sl_ceiling:
        P(f"> {sl_ceiling}")
        P("")
    if not six_layer:
        P("> ⚠️ 视听六层未传入——钩子建议基于互动数据推断，无视听维度加持。传入视频URL分析视听六层可提升推断准确性。")
        P("")
    P("> **铁律：一条视频最多3个钩，超过反而失效——用户注意力是稀缺资源。**")
    P("")

    # ── C. 漏斗诊断：第一卡点 ──
    P("### C. 转化漏斗：你的第一卡点在哪")
    P("")
    P("`曝光 → 完播 → 互动 → 进主页 → 关注 → 私信 → 成交 → 复购`")
    P("")
    P(f"**⚡ 第一卡点**：{bottleneck}")
    P("")
    P(f"**根因**：{root_cause}")
    P("")
    P(f"**优化动作**：{action}")
    P("")
    P(f"> {funnel_bb_note}")
    P("")

    # ── D. 一句话提醒 ──
    P("### D. 最重要的一件事")
    P("")
    if stage == "信任铺垫期":
        P("**现在不是变现的时候，是打地基的时候。** 地基没打好就急着变现，粉丝跑了连地基都没了。把内容做扎实，变现自然来。")
    elif stage == "软植入期":
        P("**买单是顺理成章，不是说服。** 如果你需要费劲说服粉丝买，说明上游信任或精准度还有问题——先解决信任，再谈转化。")
    else:
        P("**最贵的转化路径是私域。** 平台内的成交是一次性的，把成交用户引导进私域（微信/社群），才能做复购和口碑裂变——这才是长线钱。")
    P("")

    return "\n".join(L)
