"""LLM 调用层 · probe 分析引擎。

优先级：LiteLLM proxy (ufo2:4000) → DeepSeek (xh.v1api.cc) → Qwen (dashscope)
key 从服务器 /root/.model-keys.env 或 vault probe.env 注入，本地无 key 走降级桩。

原料进结论出：LLM 仅做加工/分析，不直接返回第三方原始数据。
"""
from __future__ import annotations

import os
from typing import Any, Optional

import httpx

# 部署时服务器注入 key，本地开发时若无 key 走桩降级
_LITELLM_BASE = os.getenv("PROBE_LITELLM_BASE", "")
_LITELLM_KEY  = os.getenv("PROBE_LITELLM_KEY", "")
_DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "")
_QWEN_KEY     = os.getenv("BAILIAN_API_KEY", "")

_PROVIDERS = [
    # LiteLLM proxy 优先（ufo2 Tailscale 内网 · cc-sonnet）
    {
        "name": "litellm",
        "base": lambda: _LITELLM_BASE,
        "model": "cc-sonnet",
        "key": lambda: _LITELLM_KEY,
    },
    {
        "name": "deepseek",
        "base": lambda: "https://xh.v1api.cc/v1",
        "model": "deepseek-chat",
        "key": lambda: _DEEPSEEK_KEY,
    },
    {
        "name": "qwen",
        "base": lambda: "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",
        "key": lambda: _QWEN_KEY,
    },
]

_TIMEOUT = 30


def _chat(messages: list[dict], max_tokens: int = 1500) -> str | None:
    """尝试各 provider，返回第一个成功的回复文本。"""
    text, _ = _chat_with_usage(messages, max_tokens)
    return text


def _chat_with_usage(
    messages: list[dict],
    max_tokens: int = 1500,
) -> tuple[Optional[str], dict]:
    """尝试各 provider，返回 (文本, usage_dict)。

    usage_dict: {"provider": str, "model": str, "prompt_tokens": int, "completion_tokens": int}
    失败返回 (None, {})。
    """
    for p in _PROVIDERS:
        base = p["base"]()
        key  = p["key"]()
        if not base or not key:
            continue
        try:
            r = httpx.post(
                f"{base}/chat/completions",
                headers={"Authorization": f"Bearer {key}",
                         "Content-Type": "application/json"},
                json={"model": p["model"], "messages": messages,
                      "max_tokens": max_tokens, "temperature": 0.3},
                timeout=_TIMEOUT,
            )
            if r.status_code == 200:
                body = r.json()
                text = body["choices"][0]["message"]["content"]
                usage_raw = body.get("usage", {})
                usage = {
                    "provider":          p["name"],
                    "model":             p["model"],
                    "prompt_tokens":     usage_raw.get("prompt_tokens", 0),
                    "completion_tokens": usage_raw.get("completion_tokens", 0),
                }
                return text, usage
        except Exception:
            continue
    return None, {}


def is_available() -> bool:
    """检查 LLM 是否可用（有任意 provider key）。"""
    return bool(_LITELLM_KEY or _DEEPSEEK_KEY or _QWEN_KEY)


# ─────────────────── D2 结构拆解 ───────────────────

D2_SYSTEM = """你是内容策略师，专门分析自媒体内容的结构与可复用模式。
任务：拆解内容骨架，识别节奏拐点，归纳可复用的结构公式。
输出格式（JSON）：
{
  "structure_formula": "一句话结构公式，如「痛点开场 + 反转证据 + 行动CTA」",
  "hook": {"type": "悬念/痛点/数字/反常识等", "text": "开场钩子文案（原文摘录，30字内）"},
  "body_nodes": [{"node": "节点名", "emotion": "情绪走向", "transition": "过渡技巧"}],
  "cta": {"position": "位置描述", "style": "措辞方式"},
  "reuse_tags": ["可复用爆款结构标签1", "标签2"],
  "aigc_flag": false
}"""


def analyze_structure(text: str, title: str = "") -> dict[str, Any]:
    """D2 结构拆解：分析文章/视频文案的钩子/正文/CTA结构，输出结构公式。

    无 LLM 时返回降级桩。
    """
    if not is_available() or len(text) < 100:
        return _stub_structure(title, text)
    excerpt = text[:3000]
    messages = [
        {"role": "system", "content": D2_SYSTEM},
        {"role": "user", "content": f"标题：{title}\n\n内容文案（节选）：\n{excerpt}\n\n请分析结构，按JSON格式输出。"},
    ]
    raw = _chat(messages, max_tokens=800)
    if not raw:
        return _stub_structure(title, text)
    import json, re
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        try:
            d = json.loads(m.group())
            d["aigc_flag"] = True
            d["_source"] = "llm"
            return d
        except Exception:
            pass
    return {"structure_formula": raw[:200], "aigc_flag": True, "_source": "llm-raw"}


def _stub_structure(title: str, text: str) -> dict:
    wc = len(text)
    return {
        "structure_formula": "钩子 → 正文 → CTA（结构分析待 LLM 接入）",
        "hook": {"type": "待分析", "text": title[:30] or text[:30]},
        "body_nodes": [{"node": f"正文约 {wc} 字", "emotion": "未分析", "transition": "—"}],
        "cta": {"position": "末尾", "style": "待分析"},
        "reuse_tags": [],
        "aigc_flag": False,
        "_source": "stub",
        "_stub": True,
    }


# ─────────────────── D7 二创路径 ───────────────────

D7_SYSTEM = """你是创意策略师，专门为自媒体创作者设计二创方案。
基于内容分析结论，设计「借换串」三路二创方案，每路标注投入与版权风险。
输出格式（JSON）：
{
  "borrow": {"desc": "借路方案（借用结构/节奏，换主题）", "input": "低/中/高", "copyright_risk": "低/中/高"},
  "adapt": {"desc": "换路方案（保留观点，换表达形式）", "input": "低/中/高", "copyright_risk": "低/中/高"},
  "remix": {"desc": "串路方案（与其他内容混剪/重组）", "input": "低/中/高", "copyright_risk": "低/中/高"},
  "priority": "借路/换路/串路",
  "priority_reason": "推荐优先级的理由（1句话）",
  "aigc_flag": true
}"""


def generate_recreation_paths(structure: dict, title: str, rating: str,
                               compliance_note: str = "") -> dict[str, Any]:
    """D7 二创路径：基于结构分析和合规评估，给出借/换/串三路方案。"""
    if not is_available():
        return _stub_recreation()
    formula = structure.get("structure_formula", "")
    messages = [
        {"role": "system", "content": D7_SYSTEM},
        {"role": "user", "content":
         f"内容标题：{title}\n评级：{rating}\n结构公式：{formula}\n合规情况：{compliance_note or '未评估'}\n\n请给出借换串三路二创方案，JSON格式输出。"},
    ]
    raw = _chat(messages, max_tokens=600)
    if not raw:
        return _stub_recreation()
    import json, re
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        try:
            d = json.loads(m.group())
            d["aigc_flag"] = True
            d["_source"] = "llm"
            return d
        except Exception:
            pass
    return {"priority": "借路", "priority_reason": raw[:100], "aigc_flag": True, "_source": "llm-raw"}


def _stub_recreation() -> dict:
    return {
        "borrow": {"desc": "借用结构公式换内容主题（待 LLM 精化）", "input": "低", "copyright_risk": "低"},
        "adapt": {"desc": "保留核心观点换表达形式（待 LLM 精化）", "input": "中", "copyright_risk": "低"},
        "remix": {"desc": "与同类内容混剪重组（待 LLM 精化）", "input": "高", "copyright_risk": "中"},
        "priority": "借路",
        "priority_reason": "投入最低，结构公式可直接复用",
        "aigc_flag": False,
        "_source": "stub",
        "_stub": True,
    }


# ─────────────────── D1 真相核查（联网增强）───────────────────

D1_SYSTEM = """你是事实核查员，任务是核查内容中的可核查声称。
对每条声称：以「✅ 属实 / ⚠️ 部分属实 / ❌ 失实 / ❓ 无法核实」判定，并说明依据。
输出格式（JSON）：
{
  "claims": [{"claim": "声称内容", "verdict": "✅/⚠️/❌/❓", "reason": "判定理由（引用搜索结果）", "source_url": "来源URL或空"}],
  "overall_credibility": "低风险/中风险/高风险",
  "aigc_flag": true
}"""


def fact_check(text: str, search_results: list[dict] | None = None) -> dict[str, Any]:
    """D1 真相核查：提取可核查声称，结合 AnySearch 搜索结果判定。"""
    if not is_available():
        return {"claims": [], "overall_credibility": "未评估（LLM 未接入）",
                "aigc_flag": False, "_stub": True, "_source": "stub"}
    excerpt = text[:2000]
    search_ctx = ""
    if search_results:
        for r in search_results[:3]:
            search_ctx += f"\n- {r.get('title', '')}：{r.get('snippet', '')[:200]}"
    messages = [
        {"role": "system", "content": D1_SYSTEM},
        {"role": "user", "content":
         f"内容文案（节选）：\n{excerpt}\n\n搜索核查参考：{search_ctx or '（无联网数据）'}\n\n请核查声称，JSON格式输出。"},
    ]
    raw = _chat(messages, max_tokens=800)
    if not raw:
        return {"claims": [], "overall_credibility": "未评估",
                "aigc_flag": True, "_source": "llm-error"}
    import json, re
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        try:
            d = json.loads(m.group())
            d["aigc_flag"] = True
            d["_source"] = "llm"
            return d
        except Exception:
            pass
    return {"claims": [], "overall_credibility": "未评估",
            "aigc_flag": True, "_source": "llm-raw", "_raw": raw[:200]}
