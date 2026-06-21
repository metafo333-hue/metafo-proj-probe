"""评论区洞察 · comment_insight.py · 国产 LLM 聚类 + 意向识别 · 按行业科学适应。

来源方法论：probe-engine-catalog/01-input-data/comment-mining-adaptive-research.md
  probe 原只分析「账号在说什么」(视频内容),没挖「用户在说什么」(评论区)。
  本模块补这条最高 ROI 新数据源:六类信号(情感/高频问题/购买意向/异议/竞品/需求缺口),
  按【行业 × 人群 × 阶段】科学适应。

数据源可插拔(关键·灰度方案)：
  本模块**不自建抓取**。定义 CommentSource Protocol(评论数据源接口),
  实际灰度 feed(TikHub 授权源等)在接口后接入——商业链不自建爬虫。
  无数据源/无评论 → 优雅返回 None,报告自动跳过此段。

防玄学铁律(R0.8)：
  - 样本门 20 条:低于此**只定性不出百分比**(本方案最重要的防玄学硬闸)。
  - 情感只给区间("偏正/有顾虑"),禁返回精确百分比。
  - 水军/引流评规则预过滤(可验证·🟩),过滤后才进 LLM。
  - 评论代表「愿意发声的那部分人」≠ 全部观众(🟨 样本偏差),报告明示。
  - 采到的非全量·热评经平台算法排序(🟥 平台黑盒)。
  - LLM 走 model_router.select("comment") 国产模型,数据不出境(禁海外)。
  - LLM 不可用/无评论 → 降级跳过(确定性意向计数仍可出)。
"""
from __future__ import annotations

import json
import re
from typing import Any, Protocol, runtime_checkable

_SAMPLE_FLOOR = 20  # 防玄学样本门：低于此不出百分比,只定性

# ──────────────────────────────────────────────────────────────────────────────
# 评论数据源接口(Protocol)——可插拔·灰度 feed 在接口后接入
# ──────────────────────────────────────────────────────────────────────────────
@runtime_checkable
class CommentSource(Protocol):
    """评论数据源接口。实现方(TikHub adapter / 灰度 feed / mock)返回归一化评论列表。

    归一化评论 dict 形态:
      {text:str, like:int, reply_count:int, create_time:int|None, user_label:str|None}

    无数据/失败时返回 None 或 [](不抛异常·不阻塞主报告)。
    商业链不自建爬虫——实际抓取在接口实现侧,本模块只消费接口。
    """

    def fetch(self, aweme_id: str, limit: int = 200) -> list[dict] | None:
        ...


def load_comments(
    source: CommentSource | None,
    aweme_id: str,
    comments: list[dict] | None = None,
    limit: int = 200,
) -> list[dict] | None:
    """统一取评论入口。两种灰度接入方式(择一):
      1) 直接传入 comments 列表(测试/已有数据/外部灰度 feed 先采好)→ 直接用。
      2) 传入实现了 CommentSource 的 source(provider)→ 调 source.fetch。
    都没有 → None(报告跳过此段)。**本模块不自建抓取**。
    """
    if comments is not None:
        return comments or None
    if source is None:
        return None
    try:
        got = source.fetch(aweme_id, limit=limit)
        return got or None
    except Exception:
        return None  # 数据源失败不阻塞主报告


# ──────────────────────────────────────────────────────────────────────────────
# 行业意向词典(科学适应核心·行业→{意向词, 诊断重点, 建议模板})
# 行业名复用 account_report._track() 输出
# ──────────────────────────────────────────────────────────────────────────────
INDUSTRY_INTENT_LEXICON: dict[str, dict[str, Any]] = {
    "美食": {  # 餐饮
        "intent": ["在哪", "几点", "订位", "包间", "人均", "团购", "外卖", "地址"],
        "focus": "到店意向密度 + 营业信息缺失率",
        "advice": "评论高频问到店信息 → 主页置顶 POI + 营业时间;问人均 → 拍一条「人均X吃到撑」",
    },
    "时尚美妆": {  # 美业
        "intent": ["多少钱", "能约", "多久", "副作用", "维持", "痛", "预约"],
        "focus": "价格异议率 + 预约转化阻塞",
        "advice": "价格问得多却无转化 = 不是贵是「不敢」→ 补真实客户见证 + 效果维持内容",
    },
    "带货电商": {  # 服装/带货
        "intent": ["多少钱", "尺码", "大码", "掉色", "材质", "色差", "链接", "实体店"],
        "focus": "线下转化链路(种草→到店)断点",
        "advice": "问「实体店在哪」多 → 线上种草已成、卡在到店,主页强化门店导航",
    },
    "知识科普": {  # 教育/知识 IP
        "intent": ["多少钱", "零基础", "报名", "包过", "有没有用", "退费", "完整版", "出课", "求资料", "教程", "收徒"],
        "focus": "知识付费意向密度 + 信任壁垒",
        "advice": "求教程/求完整版多 = 私域/课程信号 → 引导主页找联系方式;疑虑集中「有没有用」→ 补学员成果证据链",
    },
    "健身运动": {
        "intent": ["私教", "年卡", "体验", "离", "近", "新手", "多少"],
        "focus": "体验课钩子转化 + 位置匹配",
        "advice": "问体验课多 → 主页挂体验课钩子;问位置多 → 标 POI",
    },
    "母婴育儿": {
        "intent": ["多少钱", "哪里买", "链接", "几个月", "安全吗", "成分"],
        "focus": "安全异议 + 购买意向",
        "advice": "安全顾虑高 → 补成分/资质内容;问链接多 → 主页橱窗承接",
    },
}
_GENERIC = {
    "intent": ["多少钱", "在哪", "怎么", "能不能", "有没有", "链接"],
    "focus": "通用意向密度",
    "advice": "看高频问题 = 用户真需求 = 下条选题",
}

# 创作者人群 → 建议口径(同评论·人群不同→翻译口径不同)
_PERSONA_TONE: dict[str, str] = {
    "实体店主": "把评论意向翻译成生意语言:「这条带来 N 条问地址/价格的评论 = 潜在到店客」",
    "应届生": "把高频问题翻译成选题:「评论在问 X,说明这是你受众的真需求,下条就拍 X」",
    "中年失业": "先给正反馈:「有 N 个人认可你的经验」,傻瓜化口径、先信心后行动",
    "在职转型": "按 ROI 排:「评论里这个问题热度最高,优先拍它,省你试错时间」",
}

# ──────────────────────────────────────────────────────────────────────────────
# 水军/引流预过滤(规则·可验证·🟩)
# ──────────────────────────────────────────────────────────────────────────────
_SPAM_RE = re.compile(r"(加微信?|私我|wx[:：]|vx|扣\d|进群|领取|福利|http|主页有|二维码|加我)")
_EMOJI_ONLY_RE = re.compile(r"^[^一-龥a-zA-Z0-9]+$")


def _prefilter(comments: list[dict]) -> tuple[list[dict], int]:
    """去重 + 滤引流 + 滤纯表情。返回 (干净评论, 过滤掉数)。"""
    seen: set[str] = set()
    clean: list[dict] = []
    dropped = 0
    for c in comments:
        t = (c.get("text") or "").strip()
        if not t or _EMOJI_ONLY_RE.match(t) or _SPAM_RE.search(t):
            dropped += 1
            continue
        key = t[:20]  # 粗粒度判重(同款开头视为模板水军)
        if key in seen:
            dropped += 1
            continue
        seen.add(key)
        clean.append(c)
    return clean, dropped


# ──────────────────────────────────────────────────────────────────────────────
# 确定性信号(意向词命中=可验证计数·🟩) + 高频问题(无 LLM 也能出)
# ──────────────────────────────────────────────────────────────────────────────
def _count_intent(comments: list[dict], intent_words: list[str]) -> dict[str, int]:
    """意向词命中计数(🟩 事实·可验证)。"""
    hits: dict[str, int] = {}
    for c in comments:
        t = c.get("text") or ""
        for w in intent_words:
            if w in t:
                hits[w] = hits.get(w, 0) + 1
    return {k: v for k, v in sorted(hits.items(), key=lambda x: -x[1]) if v > 0}


_QUESTION_RE = re.compile(r"[?？]|怎么|多少|哪里|在哪|能不能|有没有|是不是|可以吗|几点")


def _top_questions_rule(comments: list[dict], top_n: int = 3) -> list[dict]:
    """无 LLM 时的兜底高频问题:抽含疑问特征的评论,按前缀粗聚类。"""
    buckets: dict[str, int] = {}
    samples: dict[str, str] = {}
    for c in comments:
        t = (c.get("text") or "").strip()
        if t and _QUESTION_RE.search(t):
            key = t[:8]
            buckets[key] = buckets.get(key, 0) + 1
            samples.setdefault(key, t)
    ranked = sorted(buckets.items(), key=lambda x: -x[1])[:top_n]
    return [{"q": samples[k], "count": v} for k, v in ranked]


# ──────────────────────────────────────────────────────────────────────────────
# LLM 聚类/情感/异议(走 model_router.select("comment") 国产·数据不出境)
# 失败/不可用 → 返回 None,上层降级到规则兜底
# ──────────────────────────────────────────────────────────────────────────────
def _comment_model() -> str:
    """评论分析模型 = 模型路由层按周更表选(国产·便宜均衡)。路由不可用回退,永不阻塞。"""
    try:
        from app.services.model_router import select
        return select("comment") or "Qwen/Qwen3.5-35B-A3B"
    except Exception:
        return "Qwen/Qwen3.5-35B-A3B"


_LLM_PROMPT = """你是短视频评论区分析专家。下面是某条视频的评论(已滤掉水军/引流评)。
只输出 JSON,不要任何额外文字。情感**只给定性**(偏正/中性/有顾虑),**禁止给精确百分比**(样本不代表全部观众)。

分析四件事:
1. sentiment: {"tone":"偏正|中性|有顾虑","neg_themes":["负面集中的主题,最多3个"]}
2. top_questions: [{"q":"高频问题(归并同义)","count":粗略条数}] 最多3条
3. objections: ["转化阻塞类异议/顾虑句,最多4条"]
4. competitor: ["评论里点名提到的别家品牌/店名,没有则空数组"]
5. demand_gap: ["「能不能也做X/要是有Y就好了」类需求建议,最多3条"]

严格按此结构:
{"sentiment":{"tone":"","neg_themes":[]},"top_questions":[],"objections":[],"competitor":[],"demand_gap":[]}

评论列表:
{comments}"""


def _llm_analyze(comments: list[dict], max_send: int = 80) -> dict | None:
    """走国产 LLM 做聚类/情感/异议/竞品/需求缺口。失败/不可用返回 None。"""
    try:
        from app.services import llm
    except Exception:
        return None
    if not llm.is_available():
        return None
    texts = [(c.get("text") or "").strip() for c in comments[:max_send]]
    texts = [t for t in texts if t]
    if not texts:
        return None
    joined = "\n".join(f"- {t}" for t in texts)
    messages = [
        {"role": "system", "content": "你是评论区分析专家,只输出 JSON,情感只给定性不给百分比。"},
        {"role": "user", "content": _LLM_PROMPT.replace("{comments}", joined)},
    ]
    try:
        raw = llm._chat(messages, max_tokens=900)
    except Exception:
        return None
    if not raw:
        return None
    return _parse_llm_json(raw)


def _parse_llm_json(raw: str) -> dict | None:
    """容错解析 LLM JSON(可能裹 ```json 或前后有解释文字)。"""
    if not raw:
        return None
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group())
    except Exception:
        return None
    if not isinstance(d, dict):
        return None
    # 防玄学:若模型违规返回精确百分比,剥掉(只保留定性 tone)
    sent = d.get("sentiment")
    if isinstance(sent, dict):
        tone = sent.get("tone")
        if isinstance(tone, str) and re.search(r"\d+\s*%", tone):
            sent["tone"] = "有顾虑" if "顾虑" in tone or "负" in tone else "偏正"
    return d


# ──────────────────────────────────────────────────────────────────────────────
# 主入口
# ──────────────────────────────────────────────────────────────────────────────
def analyze_comments(
    comments: list[dict] | None,
    industry: str = "生活记录",
    persona: str | None = None,
    *,
    use_llm: bool = True,
) -> dict | None:
    """评论区六类信号洞察。

    comments: load_comments 输出(已从数据源接口取好的归一化评论)。
    industry: account_report._track() 输出的赛道名。
    persona:  人群轴(可选·影响建议口径)。
    use_llm:  关闭则纯规则(测试/无 LLM 环境)。

    返回 None = 无评论/样本不足且无任何可出内容(报告跳过此段)。
    """
    if not comments:
        return None
    clean, dropped = _prefilter(comments)
    n = len(clean)
    if n == 0:
        return None

    lex = INDUSTRY_INTENT_LEXICON.get(industry, _GENERIC)
    persona_tone = _PERSONA_TONE.get(persona) if persona else None

    # 样本门:低于 20 条只定性,绝不出百分比/情感分布(防玄学硬闸)
    if n < _SAMPLE_FLOOR:
        return {
            "sample": n, "filtered_spam": dropped, "below_floor": True,
            "industry": industry, "focus": lex["focus"], "advice_tmpl": lex["advice"],
            "persona_tone": persona_tone,
            "intent_hits": _count_intent(clean, lex["intent"]),  # 🟩 计数仍可出
            "top_questions": _top_questions_rule(clean),
            "note": f"评论较少(采到 {n} 条),只给方向不给比例",
        }

    intent_hits = _count_intent(clean, lex["intent"])  # 🟩 可验证计数
    out: dict[str, Any] = {
        "sample": n, "filtered_spam": dropped, "below_floor": False,
        "industry": industry, "focus": lex["focus"], "advice_tmpl": lex["advice"],
        "persona_tone": persona_tone,
        "intent_hits": intent_hits,
        "llm_used": False,
    }

    llm_res = _llm_analyze(clean) if use_llm else None
    if llm_res:
        out["llm_used"] = True
        out["sentiment"] = llm_res.get("sentiment")          # 🟨 区间,不给精确百分比
        out["top_questions"] = llm_res.get("top_questions") or _top_questions_rule(clean)
        out["objections"] = llm_res.get("objections") or []
        out["competitor"] = llm_res.get("competitor") or []
        out["demand_gap"] = llm_res.get("demand_gap") or []
    else:
        # LLM 不可用/失败 → 降级到规则兜底(只出确定性能出的:意向计数+高频问题)
        out["llm_used"] = False
        out["sentiment"] = None
        out["top_questions"] = _top_questions_rule(clean)
        out["objections"] = []
        out["competitor"] = []
        out["demand_gap"] = []
        out["llm_degraded"] = True
    return out


# ──────────────────────────────────────────────────────────────────────────────
# 渲染层(与 account_report.render_*_section 同构·三色标注)
# ──────────────────────────────────────────────────────────────────────────────
def render_comment_section(insight: dict | None) -> str | None:
    """评论洞察 dict → markdown 段(供 build_report 新参数 comment_md)。
    None / 无内容 → None(报告自动跳过·与 av_md/attribution_md 降级哲学一致)。"""
    if not insight:
        return None

    L: list[str] = ["## 💬 用户在评论区说了什么(这是最真实的反馈)", ""]

    # —— 样本不足:只定性,绝不出百分比 ——
    if insight.get("below_floor"):
        L.append(f"> 这条评论还不多(采到 {insight['sample']} 条),先看大方向、不给比例(样本太小给比例会误导):")
        L.append("")
        hits = insight.get("intent_hits") or {}
        if hits:
            top = "、".join(f"「{k}」{v} 次" for k, v in list(hits.items())[:5])
            L.append(f"- **有人在问**:{top}(🟩 命中计数)")
        tq = insight.get("top_questions") or []
        if tq:
            L.append("- **高频问题(下条选题方向)**:")
            for q in tq:
                L.append(f"  - {q['q']}（约 {q['count']} 条）")
        if not hits and not tq:
            L.append("- 暂未识别到明显意向词/高频问题——继续积累评论。")
        L.append("")
        L.append("> ⚠️ 评论代表「愿意发声的那部分人」,不等于全部观众(🟨 样本偏差)。")
        return "\n".join(L)

    # —— 正常样本 ——
    L.append(f"> 采到 {insight['sample']} 条评论(已滤掉 {insight['filtered_spam']} 条疑似引流/水军 🟩)。")
    L.append("> ⚠️ 评论代表「愿意发声的那部分人」,不等于全部观众(🟨 样本偏差);采到的非全量、热评经平台算法排序(🟥 平台黑盒)。")
    L.append("")

    # 购买意向(🟩 事实计数·最高优先级)
    hits = insight.get("intent_hits") or {}
    if hits:
        top = "、".join(f"「{k}」{v} 次" for k, v in list(hits.items())[:6])
        L.append(f"### 🎯 购买意向信号(🟩 计数·热度即转化前兆)")
        L.append(f"- 评论里反复在问:{top}")
        L.append(f"- **诊断重点**:{insight['focus']}")
        L.append(f"- **怎么接**:{insight['advice_tmpl']}")
        L.append("")

    # 情感(🟨 只给定性·LLM)
    sent = insight.get("sentiment")
    if sent and isinstance(sent, dict) and sent.get("tone"):
        L.append(f"### 口碑基线(🟨 只给方向不给精确比例)")
        L.append(f"- 整体口碑:**{sent['tone']}**")
        neg = sent.get("neg_themes") or []
        if neg:
            L.append(f"- 负面集中在:{'、'.join(neg)}（这是该补的信任内容方向）")
        L.append("")

    # 高频问题(下条选题)
    tq = insight.get("top_questions") or []
    if tq:
        L.append("### ❓ 高频问题 = 下一条选题")
        for q in tq:
            cnt = q.get("count")
            L.append(f"- {q['q']}" + (f"（约 {cnt} 条）" if cnt else ""))
        L.append("")

    # 异议(转化阻塞点)
    obj = insight.get("objections") or []
    if obj:
        L.append("### 🚧 异议/顾虑(转化阻塞点 → 该补的信任内容)")
        for o in obj[:4]:
            L.append(f"- {o}")
        L.append("")

    # 竞品提及
    comp = insight.get("competitor") or []
    if comp:
        L.append(f"### 👀 评论里提到的别家:{'、'.join(comp[:5])}（用户在比价,差异化机会）")
        L.append("")

    # 需求缺口(新选题机会)
    gap = insight.get("demand_gap") or []
    if gap:
        L.append("### 💡 需求缺口(用户主动求的新内容)")
        for g in gap[:3]:
            L.append(f"- {g}")
        L.append("")

    # 人群口径
    if insight.get("persona_tone"):
        L.append(f"> 给你的话:{insight['persona_tone']}")
        L.append("")

    # LLM 降级诚实声明
    if insight.get("llm_degraded"):
        L.append("> 说明:本次评论聚类/情感分析未接到分析模型,只输出了可直接计数的意向信号与高频问题(确定项),"
                 "情感/异议留待模型可用时补全——**没瞎编**。")
    return "\n".join(L)
