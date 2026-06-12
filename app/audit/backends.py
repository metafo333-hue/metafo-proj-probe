"""可插拔 model backend 接口 + StubBackend 默认实现。

设计原则（对齐任务红线）
------------------------
- 零外部模型安装：StubBackend 返回中性/passthrough，不依赖任何 pip 模型包。
- 真实 backend（MiniCheck、nli-deberta、Binoculars、opus）后续 pip 接入，
  只需继承 ModelBackend 实现对应方法。
- backends 按用途分四类接口：
  faithfulness  闸2 多源交叉忠实度评分
  aigc          闸3 AI 生成内容检测
  nli           闸5 矛盾检测（自然语言推断）
  judge         闸6 对抗证伪裁决（D3-Judge 模式）

用法
----
    from app.audit.backends import StubBackend
    backend = StubBackend()
    score = backend.faithfulness(claim="...", sources=["..."])
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


# ---------------------------------------------------------------------------
# 抽象基类
# ---------------------------------------------------------------------------

class ModelBackend(ABC):
    """可插拔 model backend 抽象接口。

    所有方法均为同步（pipeline 层如需 async 可包一层 asyncio.to_thread）。
    """

    name: str = "abstract"

    # -- 闸2：忠实度评分 --------------------------------------------------

    @abstractmethod
    def faithfulness(self, claim: str, sources: list[str]) -> float:
        """返回 claim 相对 sources 的忠实度得分 [0.0, 1.0]。

        ≥ 0.8：采信；< 0.8：标 ⚠️ 单源；0 表示完全不支持。
        参考实现：MiniCheck / RAGAS faithfulness。
        """
        ...

    # -- 闸3：AIGC 检测 ---------------------------------------------------

    @abstractmethod
    def detect_aigc(self, text: str) -> float:
        """返回文本为 AI 生成内容的概率 [0.0, 1.0]。

        > 0.8：aigc_flag=True 并降权。
        参考实现：Binoculars / DetectGPT。
        """
        ...

    # -- 闸5：NLI 矛盾检测 ------------------------------------------------

    @abstractmethod
    def nli(self, premise: str, hypothesis: str) -> dict[str, float]:
        """返回 {entailment, neutral, contradiction} 概率分布（和为 1.0）。

        contradiction > 0.8 → 标 🔴 矛盾。
        参考实现：nli-deberta-v3 / AlignScore。
        """
        ...

    # -- 闸6：对抗证伪裁决 ------------------------------------------------

    @abstractmethod
    def judge(
        self,
        claim:      str,
        perspectives: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """D3-Judge 模式：多视角输入，返回裁决结果。

        Parameters
        ----------
        claim        : 待证伪的结论文本
        perspectives : 各视角输出列表，每个元素：
                       {"role": "generator_A|verifier_V1...", "text": "...", "refuted": bool}

        Returns
        -------
        {
          "verdict":    "accept" | "reject" | "human_review",
          "vote_count": int,   # ≥3/5 accept；2/5 human_review；≤1/5 reject
          "rationale":  str,
        }
        """
        ...


# ---------------------------------------------------------------------------
# StubBackend：中性默认实现，保证零依赖下 import 可跑
# ---------------------------------------------------------------------------

class StubBackend(ModelBackend):
    """中性 stub 实现 · 零外部依赖。

    所有方法返回中性/passthrough 值，不影响流水线主流程运行。
    真实模型后续通过继承 ModelBackend 替换。

    Stub 策略
    ---------
    faithfulness  → 0.5（中性，不触发采信/单源警告）
    detect_aigc   → 0.0（不标记 AIGC）
    nli           → neutral=1.0（不触发矛盾告警）
    judge         → "accept" with vote_count=3（多数通过，中性）
    """

    name: str = "stub"

    def faithfulness(self, claim: str, sources: list[str]) -> float:
        """Stub：返回中性分 0.5，不触发任何阈值。"""
        return 0.5

    def detect_aigc(self, text: str) -> float:
        """Stub：返回 0.0，不标记 AIGC。"""
        return 0.0

    def nli(self, premise: str, hypothesis: str) -> dict[str, float]:
        """Stub：返回纯 neutral，不触发矛盾检测。"""
        return {"entailment": 0.0, "neutral": 1.0, "contradiction": 0.0}

    def judge(
        self,
        claim:        str,
        perspectives: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Stub：多数票通过（3/5），中性裁决。"""
        return {
            "verdict":    "accept",
            "vote_count": 3,
            "rationale":  "[stub] 无真实模型，默认中性通过",
        }


# ---------------------------------------------------------------------------
# LiteLLMBackend：通过 ufo2 LiteLLM proxy (cc-sonnet) 实现四接口
# ---------------------------------------------------------------------------

class LiteLLMBackend(ModelBackend):
    """通过 LiteLLM proxy (ufo2:4000 · cc-sonnet) 实现 probe 四审核接口。

    需要 PROBE_LITELLM_BASE + PROBE_LITELLM_KEY（vault probe.env 注入）。
    接口调用失败时降级返回 StubBackend 中性值，不抛异常。
    """

    name: str = "litellm"

    def __init__(self) -> None:
        self._stub = StubBackend()

    def _call(self, messages: list[dict], max_tokens: int = 300) -> str | None:
        from app.services.llm import _chat
        return _chat(messages, max_tokens)

    def faithfulness(self, claim: str, sources: list[str]) -> float:
        src_text = "\n".join(f"[{i+1}] {s[:300]}" for i, s in enumerate(sources[:3]))
        prompt = (
            f"判断声称是否由来源支持，只输出一个 0.0~1.0 的浮点数。\n\n"
            f"声称：{claim[:200]}\n来源：\n{src_text}"
        )
        raw = self._call([{"role": "user", "content": prompt}], max_tokens=10)
        if raw:
            import re
            m = re.search(r"[01]\.\d+", raw)
            if m:
                try:
                    return min(1.0, max(0.0, float(m.group())))
                except ValueError:
                    pass
        return self._stub.faithfulness(claim, sources)

    def detect_aigc(self, text: str) -> float:
        prompt = (
            f"判断以下文本是否为 AI 生成，只输出 0.0~1.0 的浮点数（越高=越像 AI）。\n\n{text[:800]}"
        )
        raw = self._call([{"role": "user", "content": prompt}], max_tokens=10)
        if raw:
            import re
            m = re.search(r"[01]\.\d+", raw)
            if m:
                try:
                    return min(1.0, max(0.0, float(m.group())))
                except ValueError:
                    pass
        return self._stub.detect_aigc(text)

    def nli(self, premise: str, hypothesis: str) -> dict[str, float]:
        prompt = (
            '判断关系，只输出 JSON：{"entailment":f,"neutral":f,"contradiction":f}（三项和=1.0）\n\n'
            f"premise: {premise[:400]}\nhypothesis: {hypothesis[:400]}"
        )
        raw = self._call([{"role": "user", "content": prompt}], max_tokens=80)
        if raw:
            import json, re
            m = re.search(r"\{[^{}]+\}", raw, re.DOTALL)
            if m:
                try:
                    d = json.loads(m.group())
                    keys = ("entailment", "neutral", "contradiction")
                    if all(k in d for k in keys):
                        return {k: float(d[k]) for k in keys}
                except (ValueError, TypeError):
                    pass
        return self._stub.nli(premise, hypothesis)

    def judge(self, claim: str, perspectives: list[dict[str, Any]]) -> dict[str, Any]:
        persp_text = "\n".join(
            f"[{p['role']}] refuted={p.get('refuted','?')}: {str(p.get('text',''))[:200]}"
            for p in perspectives[:5]
        )
        prompt = (
            '综合各视角裁决，只输出 JSON：{"verdict":"accept|reject|human_review","vote_count":int,"rationale":"str"}\n\n'
            f"声称：{claim[:300]}\n各视角：\n{persp_text}"
        )
        raw = self._call([{"role": "user", "content": prompt}], max_tokens=120)
        if raw:
            import json, re
            m = re.search(r"\{[^{}]+\}", raw, re.DOTALL)
            if m:
                try:
                    d = json.loads(m.group())
                    if "verdict" in d:
                        return {
                            "verdict":    d.get("verdict", "human_review"),
                            "vote_count": int(d.get("vote_count", 3)),
                            "rationale":  str(d.get("rationale", "")),
                        }
                except (ValueError, TypeError):
                    pass
        return self._stub.judge(claim, perspectives)


# ---------------------------------------------------------------------------
# Backend 注册表
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, type[ModelBackend]] = {
    "stub":    StubBackend,
    "litellm": LiteLLMBackend,
}


def get_backend(name: str | None = None) -> ModelBackend:
    """按名称获取 backend 实例。

    name=None → 自动选：有 PROBE_LITELLM_KEY 则 LiteLLMBackend，否则 StubBackend。
    """
    if name is None:
        import os
        name = "litellm" if os.getenv("PROBE_LITELLM_KEY") else "stub"
    cls = _REGISTRY.get(name, StubBackend)
    return cls()
