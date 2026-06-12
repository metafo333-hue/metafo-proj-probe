"""8 闸 audit pipeline · Gate 基类 + 闸0-闸7 + run_audit()。

设计依据：probe-audit-system-v1.md § 一（审核体系总览）+ § 五（强度分档）

强度分档
--------
free     : 闸0 + 闸1 + 闸2 + 闸7（轻审：留痕+溯源+交叉+置信）
preview  : free 基础上 + 闸3 + 闸5（加抗污染+矛盾）
paid     : 闸0-7 全开 + 四眼 + 对抗证伪

模型相关闸（闸2/闸3/闸5/闸6）均接受 backend 参数（默认 StubBackend），
保证零模型依赖下 import 可跑，真实模型后续替换 backend 即可。
"""
from __future__ import annotations

import hashlib
import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional

from app.audit.backends import ModelBackend, StubBackend, get_backend
from app.audit.standards import (
    ConclusionLabel,
    ConfidenceLevel,
    EvidenceStrength,
    InfoCredibility,
    SourceReliability,
)
from app.audit.trace import AuditTrace, EventKind


# ---------------------------------------------------------------------------
# 辅助类型
# ---------------------------------------------------------------------------

class GateResult:
    """单个闸的执行结果。"""

    def __init__(
        self,
        gate_id:  str,
        passed:   bool,
        score:    Optional[float] = None,
        flags:    Optional[list]  = None,
        details:  Optional[dict]  = None,
    ) -> None:
        self.gate_id = gate_id
        self.passed  = passed
        self.score   = score
        self.flags   = flags or []
        self.details = details or {}

    def to_dict(self) -> dict:
        return {
            "gate_id": self.gate_id,
            "passed":  self.passed,
            "score":   self.score,
            "flags":   self.flags,
            "details": self.details,
        }


# ---------------------------------------------------------------------------
# Gate 基类
# ---------------------------------------------------------------------------

class Gate(ABC):
    """审核闸基类。

    每个具体闸继承此类，实现 run() 方法。
    run() 接收统一上下文 ctx（包含 claims/sources/trace 等），
    返回 GateResult。
    """

    gate_id: str = "base"

    def __init__(self, backend: Optional[ModelBackend] = None) -> None:
        self.backend = backend or StubBackend()

    @abstractmethod
    def run(self, ctx: dict[str, Any]) -> GateResult:
        """执行审核逻辑，返回 GateResult。

        ctx 键
        ------
        claims  : list[str] — 待审核的结论原子化列表
        sources : list[dict] — 来源列表，每项 {url, title, text, timestamp, reliability_hint}
        trace   : AuditTrace — 本次 run 的 trace 实例
        tier    : str — free/preview/paid
        """
        ...


# ---------------------------------------------------------------------------
# 闸0：过程留痕
# ---------------------------------------------------------------------------

class Gate0Trace(Gate):
    """闸0 · 过程留痕（贯穿全程的元前提）。

    职责
    ----
    - 初始化 run_snapshot（prompt/model/源版本锚点）
    - 记录 run_start 事件
    - 生成并返回贯穿全流水线的 trace_id

    本闸总是 passed=True（不做判定，只做记录）。
    """

    gate_id = "gate0"

    def run(self, ctx: dict[str, Any]) -> GateResult:
        trace: AuditTrace = ctx["trace"]
        sources = ctx.get("sources", [])
        tier    = ctx.get("tier", "free")

        source_urls = [s.get("url", "") for s in sources]

        # 生成 run_snapshot（温度=0 + prompt 版本 + 数据源列表）
        snapshot = trace.run_snapshot(
            prompt_version = ctx.get("prompt_version", "v1.0"),
            model_versions = ctx.get("model_versions", {"gate0": "stub"}),
            tier           = tier,
            source_urls    = source_urls,
            params         = {"temperature": 0, "seed": 42},
        )

        trace.log(
            EventKind.GATE_END,
            actor   = self.gate_id,
            entity  = "run",
            payload = {
                "trace_id":    trace.trace_id,
                "source_count": len(source_urls),
                "tier":         tier,
            },
        )

        return GateResult(
            gate_id = self.gate_id,
            passed  = True,
            details = {"trace_id": trace.trace_id, "snapshot": snapshot},
        )


# ---------------------------------------------------------------------------
# 闸1：溯源 + 源可靠性分级
# ---------------------------------------------------------------------------

class Gate1Provenance(Gate):
    """闸1 · 溯源 + 源可靠性分级（Admiralty A-F）。

    判定规则
    --------
    - 每个来源必须有 url（无 URL → reliability_hint 降 F）
    - E/F 级源自动降级拦截（标 flag，不直接拒，但降整体置信）
    - 来源分层：primary / secondary / tertiary（按 source_type 字段）
    - 返回整体最弱源可靠性（取 rank 最大值）
    """

    gate_id = "gate1"

    # 简单规则：已知权威域 → B 级；普通 URL → C 级；无 URL → F 级
    _AUTHORITATIVE_DOMAINS = {
        "wikipedia.org", "github.com", "arxiv.org",
        "nih.gov", "nature.com", "sciencedirect.com",
        "reuters.com", "apnews.com", "bbc.com",
    }

    def run(self, ctx: dict[str, Any]) -> GateResult:
        trace:   AuditTrace  = ctx["trace"]
        sources: list        = ctx.get("sources", [])

        trace.log(EventKind.GATE_START, actor=self.gate_id, entity="run")

        source_ratings: list[dict] = []
        flags: list[str] = []

        for i, src in enumerate(sources):
            url = src.get("url", "")
            hint = src.get("reliability_hint", "")

            # 优先使用调用方提供的 hint
            if hint and hint.upper() in SourceReliability._value2member_map_:
                rel = SourceReliability(hint.upper())
            elif not url:
                rel = SourceReliability.F
                flags.append(f"source[{i}] 缺 URL，降 F 级")
            else:
                domain = self._extract_domain(url)
                if any(auth in domain for auth in self._AUTHORITATIVE_DOMAINS):
                    rel = SourceReliability.B
                else:
                    rel = SourceReliability.C

            if rel.auto_downgrade:
                flags.append(f"source[{i}] {rel.value} 级自动拦截降权")

            source_ratings.append({
                "index":       i,
                "url":         url,
                "reliability": rel.value,
                "rank":        rel.rank,
            })

            trace.log(
                EventKind.SOURCE_FETCHED,
                actor   = self.gate_id,
                entity  = url or f"source[{i}]",
                payload = {"reliability": rel.value},
            )

        # 整体取最弱源（rank 最大）
        worst_rank = max((r["rank"] for r in source_ratings), default=6)
        worst_rel  = SourceReliability(
            next(r["reliability"] for r in source_ratings if r["rank"] == worst_rank)
        ) if source_ratings else SourceReliability.F

        passed = not any(SourceReliability(r["reliability"]).auto_downgrade for r in source_ratings)

        trace.log(
            EventKind.GATE_END,
            actor   = self.gate_id,
            entity  = "run",
            payload = {"worst_reliability": worst_rel.value, "flags": flags},
        )

        return GateResult(
            gate_id = self.gate_id,
            passed  = passed,
            flags   = flags,
            details = {
                "source_ratings":   source_ratings,
                "worst_reliability": worst_rel.value,
            },
        )

    @staticmethod
    def _extract_domain(url: str) -> str:
        """简单提取域名（不依赖 urllib，兼容脏数据）。"""
        url = url.lower().split("?")[0]
        for prefix in ("https://", "http://", "//"):
            if url.startswith(prefix):
                url = url[len(prefix):]
                break
        return url.split("/")[0]


# ---------------------------------------------------------------------------
# 闸2：多源交叉 + 忠实度（模型相关，backend 可插拔）
# ---------------------------------------------------------------------------

class Gate2CrossCheck(Gate):
    """闸2 · 多源交叉 + 忠实度评分（Admiralty 信息可信度 1-6）。

    判定规则
    --------
    - 每条 claim 对所有 sources 取 faithfulness 均值
    - ≥2 独立源 + score ≥ 0.8 → 信息可信度 1（经多源确认）
    - 1 源 + score ≥ 0.8 → 信息可信度 2（可能为真），标 ⚠️
    - score < 0.8 → 信息可信度 4（存疑）
    - 模型相关：backend.faithfulness()，默认 StubBackend 返 0.5
    """

    gate_id = "gate2"
    FAITHFULNESS_THRESHOLD = 0.8

    def run(self, ctx: dict[str, Any]) -> GateResult:
        trace:   AuditTrace = ctx["trace"]
        claims:  list[str]  = ctx.get("claims", [])
        sources: list       = ctx.get("sources", [])

        trace.log(EventKind.GATE_START, actor=self.gate_id, entity="run")

        source_texts = [s.get("text", s.get("url", "")) for s in sources]
        results: list[dict] = []
        flags:   list[str]  = []
        credibilities: list[int] = []

        for i, claim in enumerate(claims):
            scores = [
                self.backend.faithfulness(claim=claim, sources=[text])
                for text in source_texts
            ] if source_texts else [0.0]

            avg_score      = sum(scores) / len(scores)
            independent_ok = sum(1 for s in scores if s >= self.FAITHFULNESS_THRESHOLD)

            if independent_ok >= 2 and avg_score >= self.FAITHFULNESS_THRESHOLD:
                cred = InfoCredibility.ONE
            elif independent_ok >= 1 and avg_score >= self.FAITHFULNESS_THRESHOLD:
                cred = InfoCredibility.TWO
                flags.append(f"claim[{i}] 单源印证，标 ⚠️")
            else:
                cred = InfoCredibility.FOUR
                flags.append(f"claim[{i}] 忠实度低（avg={avg_score:.2f}），标存疑")

            credibilities.append(cred.rank)
            results.append({
                "claim_index":    i,
                "avg_score":      round(avg_score, 4),
                "source_scores":  [round(s, 4) for s in scores],
                "info_credibility": cred.value,
            })

            trace.log(
                EventKind.CLAIM_SCORED,
                actor   = self.gate_id,
                entity  = f"claim[{i}]",
                payload = {"info_credibility": cred.value, "avg_score": round(avg_score, 4)},
            )

        # 整体取最弱信息可信度（rank 最大）
        worst_cred_rank = max(credibilities, default=6)
        worst_cred = InfoCredibility(str(worst_cred_rank))

        passed = worst_cred_rank <= 3  # 1/2/3 算通过；4/5/6 需警告

        trace.log(
            EventKind.GATE_END,
            actor   = self.gate_id,
            entity  = "run",
            payload = {"worst_credibility": worst_cred.value, "flags": flags},
        )

        return GateResult(
            gate_id = self.gate_id,
            passed  = passed,
            flags   = flags,
            details = {
                "claim_results":    results,
                "worst_credibility": worst_cred.value,
            },
        )


# ---------------------------------------------------------------------------
# 闸3：抗循环 / 抗污染 / 抗AIGC（模型相关，backend 可插拔）
# ---------------------------------------------------------------------------

class Gate3Dedup(Gate):
    """闸3 · 抗循环引用 / 抗污染 / 抗AIGC。

    判定规则
    --------
    - 同源循环检测：sources 的 url domain 去重，同域 > 80% → 循环引用告警
    - AIGC 检测：backend.detect_aigc()，> 0.8 → aigc_flag=True 降权
    - 伪权威检测：无 timestamp / 纯个人博客 → 标低权威
    """

    gate_id = "gate3"
    AIGC_THRESHOLD    = 0.8
    CIRCULAR_RATIO    = 0.8  # 同域来源占比 > 此值触发告警

    def run(self, ctx: dict[str, Any]) -> GateResult:
        trace:   AuditTrace = ctx["trace"]
        sources: list       = ctx.get("sources", [])
        claims:  list[str]  = ctx.get("claims", [])

        trace.log(EventKind.GATE_START, actor=self.gate_id, entity="run")

        flags:    list[str] = []
        aigc_flag = False

        # 1. 循环引用检测（同域去重）
        if sources:
            domains = [Gate1Provenance._extract_domain(s.get("url", "")) for s in sources]
            from collections import Counter
            domain_counts = Counter(domains)
            top_domain, top_count = domain_counts.most_common(1)[0]
            ratio = top_count / len(domains)
            if ratio > self.CIRCULAR_RATIO:
                flags.append(f"循环引用告警：{top_domain} 占 {ratio:.0%}（>{self.CIRCULAR_RATIO:.0%}）")

        # 2. AIGC 检测（对所有 sources 文本 + claims 文本）
        all_texts = [s.get("text", "") for s in sources] + list(claims)
        aigc_scores = [self.backend.detect_aigc(t) for t in all_texts if t]
        if aigc_scores:
            max_aigc = max(aigc_scores)
            if max_aigc > self.AIGC_THRESHOLD:
                aigc_flag = True
                flags.append(f"AIGC 告警：最高得分 {max_aigc:.2f}（>{self.AIGC_THRESHOLD}）")

        # 3. 伪权威检测（无 timestamp 视为低权威）
        no_ts_count = sum(1 for s in sources if not s.get("timestamp"))
        if no_ts_count > 0:
            flags.append(f"{no_ts_count} 个来源缺少时间戳（疑伪权威）")

        passed = not aigc_flag and len([f for f in flags if "循环引用" in f]) == 0

        trace.log(
            EventKind.GATE_END,
            actor   = self.gate_id,
            entity  = "run",
            payload = {"aigc_flag": aigc_flag, "flags": flags},
        )

        return GateResult(
            gate_id = self.gate_id,
            passed  = passed,
            flags   = flags,
            details = {
                "aigc_flag":   aigc_flag,
                "aigc_scores": [round(s, 4) for s in aigc_scores],
            },
        )


# ---------------------------------------------------------------------------
# 闸4：时效 × 权威（CRAAP 五维加权）
# ---------------------------------------------------------------------------

class Gate4CRAAP(Gate):
    """闸4 · 时效 × 权威（CRAAP 五维评分）。

    CRAAP 五维：Currency / Relevance / Authority / Accuracy / Purpose
    本实现基于结构字段打分（无需外部模型），加权求和 [0, 1]。

    简化策略
    --------
    C (Currency)    : timestamp 新鲜度（≤30天=1.0, ≤180天=0.7, >180天=0.3, 无=0.0）
    R (Relevance)   : 来源 title/text 含 claim 关键词比例（近似）
    A (Authority)   : 域名权威性（与闸1一致）
    Ac (Accuracy)   : 闸2 faithfulness 分数（从 ctx 借用）
    P (Purpose)     : 无广告 URL 标识（无 ?utm / /ad/ → 1.0；有 → 0.5）

    权重：C=0.25, R=0.15, A=0.3, Ac=0.2, P=0.1
    """

    gate_id = "gate4"
    WEIGHTS = {"C": 0.25, "R": 0.15, "A": 0.30, "Ac": 0.20, "P": 0.10}
    PASS_THRESHOLD = 0.4

    def run(self, ctx: dict[str, Any]) -> GateResult:
        trace:   AuditTrace = ctx["trace"]
        sources: list       = ctx.get("sources", [])
        claims:  list[str]  = ctx.get("claims", [])
        # 从 gate2 结果借用 faithfulness 均值（若有）
        gate2_result = ctx.get("gate_results", {}).get("gate2", {})
        claim_results = gate2_result.get("claim_results", [])
        avg_faithfulness = (
            sum(r["avg_score"] for r in claim_results) / len(claim_results)
            if claim_results else 0.5
        )

        trace.log(EventKind.GATE_START, actor=self.gate_id, entity="run")

        source_scores: list[dict] = []
        flags:         list[str]  = []

        for i, src in enumerate(sources):
            c_score  = self._currency(src.get("timestamp", ""))
            r_score  = self._relevance(src.get("text", "") + src.get("title", ""), claims)
            a_score  = self._authority(src.get("url", ""))
            ac_score = avg_faithfulness
            p_score  = self._purpose(src.get("url", ""))

            weighted = (
                c_score  * self.WEIGHTS["C"]  +
                r_score  * self.WEIGHTS["R"]  +
                a_score  * self.WEIGHTS["A"]  +
                ac_score * self.WEIGHTS["Ac"] +
                p_score  * self.WEIGHTS["P"]
            )

            if weighted < self.PASS_THRESHOLD:
                flags.append(f"source[{i}] CRAAP 得分低（{weighted:.2f}），降权")

            source_scores.append({
                "index":    i,
                "C":        round(c_score,  3),
                "R":        round(r_score,  3),
                "A":        round(a_score,  3),
                "Ac":       round(ac_score, 3),
                "P":        round(p_score,  3),
                "weighted": round(weighted, 3),
            })

        avg_weighted = (
            sum(s["weighted"] for s in source_scores) / len(source_scores)
            if source_scores else 0.0
        )
        passed = avg_weighted >= self.PASS_THRESHOLD

        trace.log(
            EventKind.GATE_END,
            actor   = self.gate_id,
            entity  = "run",
            payload = {"avg_craap": round(avg_weighted, 3), "flags": flags},
        )

        return GateResult(
            gate_id = self.gate_id,
            passed  = passed,
            flags   = flags,
            score   = round(avg_weighted, 3),
            details = {"source_scores": source_scores},
        )

    @staticmethod
    def _currency(timestamp: str) -> float:
        if not timestamp:
            return 0.0
        try:
            # 支持 ISO 8601 前缀
            ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            days = (datetime.now(timezone.utc) - ts).days
            if days <= 30:
                return 1.0
            if days <= 180:
                return 0.7
            return 0.3
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _relevance(text: str, claims: list[str]) -> float:
        if not text or not claims:
            return 0.5
        all_keywords = set()
        for claim in claims:
            # 简单按空格/标点分词取词
            words = re.findall(r'\w+', claim.lower())
            all_keywords.update(words)
        if not all_keywords:
            return 0.5
        text_lower = text.lower()
        hit = sum(1 for kw in all_keywords if kw in text_lower)
        return min(hit / len(all_keywords), 1.0)

    @staticmethod
    def _authority(url: str) -> float:
        domain = Gate1Provenance._extract_domain(url)
        auth_domains = Gate1Provenance._AUTHORITATIVE_DOMAINS
        if any(a in domain for a in auth_domains):
            return 0.9
        if domain.endswith((".gov", ".edu", ".ac.cn", ".ac.uk")):
            return 0.8
        return 0.5

    @staticmethod
    def _purpose(url: str) -> float:
        url_lower = url.lower()
        if any(ad in url_lower for ad in ("utm_", "/ad/", "/ads/", "affiliate")):
            return 0.5
        return 1.0


# ---------------------------------------------------------------------------
# 闸5：矛盾检测（NLI，backend 可插拔）
# ---------------------------------------------------------------------------

class Gate5NLI(Gate):
    """闸5 · 矛盾检测（NLI）。

    判定规则
    --------
    - 每对 (claim_i, claim_j) 做 NLI 判断
    - contradiction > 0.8 → 标 🔴 矛盾，passed=False
    - 同时对 (claim, source_text) 检测
    """

    gate_id = "gate5"
    CONTRADICTION_THRESHOLD = 0.8

    def run(self, ctx: dict[str, Any]) -> GateResult:
        trace:   AuditTrace = ctx["trace"]
        claims:  list[str]  = ctx.get("claims", [])
        sources: list       = ctx.get("sources", [])

        trace.log(EventKind.GATE_START, actor=self.gate_id, entity="run")

        flags:       list[str]  = []
        contradictions: list[dict] = []

        # claim × claim 矛盾检测
        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                nli = self.backend.nli(premise=claims[i], hypothesis=claims[j])
                if nli["contradiction"] > self.CONTRADICTION_THRESHOLD:
                    flags.append(
                        f"🔴 claim[{i}] vs claim[{j}] 矛盾（{nli['contradiction']:.2f}）"
                    )
                    contradictions.append({
                        "type":  "claim_vs_claim",
                        "i":     i,
                        "j":     j,
                        "score": round(nli["contradiction"], 4),
                    })

        # claim × source 矛盾检测
        for i, claim in enumerate(claims):
            for k, src in enumerate(sources):
                src_text = src.get("text", "")
                if not src_text:
                    continue
                nli = self.backend.nli(premise=src_text, hypothesis=claim)
                if nli["contradiction"] > self.CONTRADICTION_THRESHOLD:
                    flags.append(
                        f"🔴 claim[{i}] vs source[{k}] 矛盾（{nli['contradiction']:.2f}）"
                    )
                    contradictions.append({
                        "type":  "claim_vs_source",
                        "i":     i,
                        "k":     k,
                        "score": round(nli["contradiction"], 4),
                    })

        passed = len(contradictions) == 0

        trace.log(
            EventKind.GATE_END,
            actor   = self.gate_id,
            entity  = "run",
            payload = {"contradictions": len(contradictions), "flags": flags},
        )

        return GateResult(
            gate_id = self.gate_id,
            passed  = passed,
            flags   = flags,
            details = {"contradictions": contradictions},
        )


# ---------------------------------------------------------------------------
# 闸6：对抗证伪（D3-Judge 模式，backend 可插拔）
# ---------------------------------------------------------------------------

class Gate6Judge(Gate):
    """闸6 · 对抗证伪（D3-Judge 模式）。

    D3-Judge 三阶段
    ---------------
    ① 生成路（视角互异，stub 模拟）
    ② 证伪路（默认 refuted=True）
    ③ 裁决层（多数票 ≥3/5 采信）

    结果映射
    --------
    ≥3/5 accept    → passed=True
    2/5 human_review → passed=False + flag
    ≤1/5 reject    → passed=False + flag
    """

    gate_id = "gate6"

    # D3-Judge 三类视角（固化，stub 无法真正区分，但结构正确）
    PERSPECTIVES = [
        {"role": "generator_A", "desc": "证据最大化（列原始来源）"},
        {"role": "generator_B", "desc": "漏洞猎取（假设结论错·找反证）"},
        {"role": "generator_C", "desc": "误读风险（用户会怎么错用）"},
        {"role": "verifier_V1", "desc": "CRITIC 模式（对矛盾点做工具核查）"},
        {"role": "verifier_V2", "desc": "纯语言推翻（给最有力反证）"},
    ]

    def run(self, ctx: dict[str, Any]) -> GateResult:
        trace:  AuditTrace = ctx["trace"]
        claims: list[str]  = ctx.get("claims", [])

        trace.log(EventKind.GATE_START, actor=self.gate_id, entity="run")

        all_verdicts: list[dict] = []
        flags: list[str] = []

        for i, claim in enumerate(claims):
            perspectives = [
                {
                    "role":    p["role"],
                    "text":    f"[{p['desc']}] stub 视角 for: {claim[:60]}",
                    "refuted": p["role"].startswith("verifier"),  # 证伪路默认 refuted=True
                }
                for p in self.PERSPECTIVES
            ]

            verdict = self.backend.judge(claim=claim, perspectives=perspectives)

            trace.log(
                EventKind.MODEL_CALL,
                actor   = self.gate_id,
                entity  = f"claim[{i}]",
                payload = {
                    "verdict":    verdict["verdict"],
                    "vote_count": verdict["vote_count"],
                },
            )

            all_verdicts.append({"claim_index": i, **verdict})

            if verdict["verdict"] == "human_review":
                flags.append(f"claim[{i}] 需人工复核（2/5 票）")
            elif verdict["verdict"] == "reject":
                flags.append(f"claim[{i}] 被证伪拒绝（≤1/5 票）")

        # 整体：有任何 reject → failed；有 human_review → 部分通过
        has_reject       = any(v["verdict"] == "reject"       for v in all_verdicts)
        has_human_review = any(v["verdict"] == "human_review" for v in all_verdicts)

        passed = not has_reject and not has_human_review

        trace.log(
            EventKind.GATE_END,
            actor   = self.gate_id,
            entity  = "run",
            payload = {
                "verdicts_count": len(all_verdicts),
                "has_reject":     has_reject,
                "flags":          flags,
            },
        )

        return GateResult(
            gate_id = self.gate_id,
            passed  = passed,
            flags   = flags,
            details = {"verdicts": all_verdicts},
        )


# ---------------------------------------------------------------------------
# 闸7：置信标注 + 证据分级 + 四眼复核
# ---------------------------------------------------------------------------

class Gate7ConfidenceLabel(Gate):
    """闸7 · 置信标注 + 证据强度分级 + 四眼复核。

    汇总前 0-6 闸结果，生成最终 ConclusionLabel 列表（每条 claim 一个）。

    证据强度规则
    -----------
    Strong    : gate1 passed + gate2 worst_cred ≤2 + source_count ≥2
    Moderate  : 以上任一不满足 but gate2 worst_cred ≤3
    Weak      : gate2 worst_cred ≥4 或 source_count < 1
    Contested : gate5 存在矛盾（contradictions > 0）

    四眼原则
    --------
    reviewer_count 由 tier 决定：
    - paid：reviewer_count=2（满足四眼）
    - 其他：reviewer_count=1（标记需人工复核）
    """

    gate_id = "gate7"

    def run(self, ctx: dict[str, Any]) -> GateResult:
        trace:   AuditTrace = ctx["trace"]
        claims:  list[str]  = ctx.get("claims", [])
        sources: list       = ctx.get("sources", [])
        tier:    str        = ctx.get("tier", "free")
        gate_results        = ctx.get("gate_results", {})

        trace.log(EventKind.GATE_START, actor=self.gate_id, entity="run")

        # 从前序闸提取关键指标
        gate1 = gate_results.get("gate1", {})
        gate2 = gate_results.get("gate2", {})
        gate3 = gate_results.get("gate3", {})
        gate5 = gate_results.get("gate5", {})

        worst_rel_str  = gate1.get("worst_reliability", "F")
        worst_cred_str = gate2.get("worst_credibility", "6")
        aigc_flag      = gate3.get("aigc_flag", False)
        contradictions = gate5.get("contradictions", [])
        source_count   = len(sources)

        worst_rel  = SourceReliability(worst_rel_str)
        worst_cred = InfoCredibility(worst_cred_str)
        reviewer_count = 2 if tier == "paid" else 1

        # 计算置信度
        confidence = self._compute_confidence(
            worst_rel   = worst_rel,
            worst_cred  = worst_cred,
            source_count= source_count,
            aigc_flag   = aigc_flag,
        )

        # 计算证据强度
        evidence = self._compute_evidence(
            gate1_passed     = gate_results.get("gate1_passed", True),
            worst_cred       = worst_cred,
            source_count     = source_count,
            has_contradiction= len(contradictions) > 0,
        )

        # 汇总 verification_methods
        verification_methods = []
        if "gate1" in gate_results:
            verification_methods.append("gate1_provenance")
        if "gate2" in gate_results:
            verification_methods.append("gate2_crosscheck")
        if "gate3" in gate_results:
            verification_methods.append("gate3_dedup")
        if "gate5" in gate_results:
            verification_methods.append("gate5_nli")
        if "gate6" in gate_results:
            verification_methods.append("gate6_judge")

        # 推断来源类型（简化）
        source_types = list({
            s.get("source_type", "secondary")
            for s in sources
        }) or ["secondary"]

        flags: list[str] = []
        if reviewer_count < 2:
            flags.append("四眼不足（reviewer_count=1），需付费档激活")
        if aigc_flag:
            flags.append("aigc_flag=True，结论含 AI 生成内容降权")

        label = ConclusionLabel(
            source_reliability   = worst_rel,
            info_credibility     = worst_cred,
            confidence_level     = confidence,
            source_count         = source_count,
            source_types         = source_types,
            evidence_strength    = evidence,
            verification_methods = verification_methods,
            reviewer_count       = reviewer_count,
            aigc_flag            = aigc_flag,
            trace_id             = trace.trace_id,
            gate_results         = {
                k: v for k, v in gate_results.items()
                if isinstance(v, dict)
            },
        )

        trace.log(
            EventKind.GATE_END,
            actor   = self.gate_id,
            entity  = "run",
            payload = {
                "confidence":      confidence.value,
                "evidence":        evidence.value,
                "reviewer_count":  reviewer_count,
            },
        )

        return GateResult(
            gate_id = self.gate_id,
            passed  = True,  # 闸7 总是返回，只是标签强度不同
            flags   = flags,
            details = {"conclusion_label": label.to_dict()},
        )

    @staticmethod
    def _compute_confidence(
        worst_rel:    SourceReliability,
        worst_cred:   InfoCredibility,
        source_count: int,
        aigc_flag:    bool,
    ) -> ConfidenceLevel:
        if aigc_flag:
            return ConfidenceLevel.LOW
        if worst_rel.rank <= 2 and worst_cred.rank <= 2 and source_count >= 2:
            return ConfidenceLevel.HIGH
        if worst_rel.rank <= 3 and worst_cred.rank <= 3:
            return ConfidenceLevel.MODERATE
        return ConfidenceLevel.LOW

    @staticmethod
    def _compute_evidence(
        gate1_passed:      bool,
        worst_cred:        InfoCredibility,
        source_count:      int,
        has_contradiction: bool,
    ) -> EvidenceStrength:
        if has_contradiction:
            return EvidenceStrength.CONTESTED
        if gate1_passed and worst_cred.rank <= 2 and source_count >= 2:
            return EvidenceStrength.STRONG
        if worst_cred.rank <= 3:
            return EvidenceStrength.MODERATE
        return EvidenceStrength.WEAK


# ---------------------------------------------------------------------------
# run_audit：串联全流水线
# ---------------------------------------------------------------------------

# 强度分档：各档开启的闸
TIER_GATES = {
    "free":    {"gate0", "gate1", "gate2", "gate7"},
    "preview": {"gate0", "gate1", "gate2", "gate3", "gate5", "gate7"},
    "paid":    {"gate0", "gate1", "gate2", "gate3", "gate4", "gate5", "gate6", "gate7"},
}


def run_audit(
    claims:  list[str],
    sources: list[dict],
    tier:    str = "free",
    backend: Optional[ModelBackend] = None,
    job_id:  Optional[str]          = None,
) -> dict[str, Any]:
    """执行完整 audit pipeline，返回结构化结果。

    Parameters
    ----------
    claims  : 待审核结论列表（原子化，每条一个陈述句）
    sources : 来源列表，每项:
              {url, title, text, timestamp, reliability_hint, source_type}
    tier    : 审核强度档（free/preview/paid）
    backend : ModelBackend 实例（默认 StubBackend）
    job_id  : 可选 job id（用于 trace 溯源）

    Returns
    -------
    {
        "trace_id":        str,
        "tier":            str,
        "gates_run":       list[str],
        "gate_results":    dict[gate_id → result_dict],
        "all_passed":      bool,
        "flags":           list[str],
        "conclusion_label": dict,  # ConclusionLabel.to_dict()
        "chain_valid":     bool,   # 哈希链完整性
    }
    """
    if tier not in TIER_GATES:
        tier = "free"

    # S1·断层#1 收口：默认走 get_backend()——有 PROBE_LITELLM_KEY 即真模型,
    # 无 key 自动回落 stub;LiteLLMBackend 单次调用失败也降级中性值,不抛异常
    _backend = backend or get_backend()
    active_gate_ids = TIER_GATES[tier]

    trace = AuditTrace(job_id=job_id)

    # 构建上下文（gate_results 随流水线累积）
    ctx: dict[str, Any] = {
        "claims":         claims,
        "sources":        sources,
        "tier":           tier,
        "trace":          trace,
        "prompt_version": "v1.0",
        "model_versions": {"default": "stub"},
        "gate_results":   {},
    }

    # 闸实例映射（按顺序执行）
    gate_instances: list[Gate] = [
        Gate0Trace(backend=_backend),
        Gate1Provenance(backend=_backend),
        Gate2CrossCheck(backend=_backend),
        Gate3Dedup(backend=_backend),
        Gate4CRAAP(backend=_backend),
        Gate5NLI(backend=_backend),
        Gate6Judge(backend=_backend),
        Gate7ConfidenceLabel(backend=_backend),
    ]

    gates_run:     list[str]   = []
    all_flags:     list[str]   = []
    all_passed     = True
    gate_result_dicts: dict    = {}

    for gate in gate_instances:
        if gate.gate_id not in active_gate_ids:
            continue

        result: GateResult = gate.run(ctx)

        gates_run.append(gate.gate_id)
        gate_result_dicts[gate.gate_id] = result.to_dict()
        all_flags.extend(result.flags)

        if not result.passed:
            all_passed = False

        # 将本闸详情回写到 ctx，供后续闸参考
        ctx["gate_results"][gate.gate_id] = result.details
        ctx["gate_results"][f"{gate.gate_id}_passed"] = result.passed

    # 提取 ConclusionLabel（由闸7 生成）
    conclusion_label: dict = {}
    gate7_details = ctx["gate_results"].get("gate7", {})
    if "conclusion_label" in gate7_details:
        conclusion_label = gate7_details["conclusion_label"]

    return {
        "trace_id":        trace.trace_id,
        "tier":            tier,
        "gates_run":       gates_run,
        "gate_results":    gate_result_dicts,
        "all_passed":      all_passed,
        "flags":           all_flags,
        "conclusion_label": conclusion_label,
        "chain_valid":     trace.verify_chain(),
    }
