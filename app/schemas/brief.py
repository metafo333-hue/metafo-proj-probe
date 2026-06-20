"""ProbeBrief 契约 · ask→probe 脊柱传递的结构体（probe-brief/v1）。

ask 侧映射器产出（枚举为字符串）→ POST /invoke → ProbeBrief.from_request 校验转枚举。
废"spec_to_instruction 拍平字符串当唯一桥"；instruction 降级为冗余兼容字段。
范式：dataclass（沿用 app/audit/standards.py 风格·不引入 pydantic 新依赖）。

注：本契约的 contract_version 是**请求侧**契约版本（probe-brief/v1），
与 invoke.schema.json 响应 meta 侧的 contract_version 语义不同（一请求一响应·不冲突）。
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional

from app.schemas.probe_intent_enum import (
    IntentEnum, PathEnum, DecisionEnum,
    coerce_intent, coerce_path, coerce_decision,
)

CONTRACT_VERSION = "probe-brief/v1"


@dataclass
class SubjectStruct:
    """分析对象（C 选题路径可为 None）。"""
    raw: str = ""                       # 原始输入 "@Richard29" / 赛道词
    kind: Optional[str] = None          # account / url / track / None
    platform: str = ""                  # douyin / youtube / bilibili ...
    resolved_url: Optional[str] = None  # ask 阶段常 None·probe resolve_douyin 回填
    sec_uid: Optional[str] = None

    @classmethod
    def from_dict(cls, d) -> "Optional[SubjectStruct]":
        if not d:
            return None
        return cls(
            raw=d.get("raw", ""), kind=d.get("kind"),
            platform=d.get("platform", ""),
            resolved_url=d.get("resolved_url"), sec_uid=d.get("sec_uid"),
        )


@dataclass
class ImplicitNeed:
    """隐性意图（只做加法·来自 ask spec.L2_implicit）。"""
    value: str = ""        # 前缀 "【推断】"
    confidence: float = 0.0


@dataclass
class ProbeBrief:
    contract_version: str = CONTRACT_VERSION
    intent: IntentEnum = IntentEnum.explore
    path: PathEnum = PathEnum.A
    intent_confidence: float = 0.0
    subject: Optional[SubjectStruct] = None
    purpose: str = ""
    decision: DecisionEnum = DecisionEnum.self_review
    audience: str = ""
    implicit_needs: list = field(default_factory=list)  # list[ImplicitNeed]
    tier: str = "free"                  # free / paid / member（probe 从 SSO 覆盖·不信 ask）
    instruction: str = ""               # 冗余兼容（spec_to_instruction 降级产物·喂旧链路）
    context: dict = field(default_factory=dict)
    attachments: list = field(default_factory=list)

    @staticmethod
    def is_brief_request(req: dict) -> bool:
        """判断 invoke 收到的是否 ask 的结构化 ProbeBrief（vs 旧裸 dict）。"""
        return isinstance(req, dict) and req.get("contract_version") == CONTRACT_VERSION

    @classmethod
    def from_request(cls, req: dict) -> "ProbeBrief":
        """probe 入口契约校验：ask 传来的 dict（枚举为字符串）→ ProbeBrief（枚举）。
        非法枚举值降级到安全默认（脊柱不因脏输入崩·对齐 R0.8 健壮性）。"""
        needs = []
        for n in (req.get("implicit_needs") or []):
            if isinstance(n, dict):
                needs.append(ImplicitNeed(n.get("value", ""), float(n.get("confidence") or 0.0)))
        return cls(
            contract_version=req.get("contract_version", CONTRACT_VERSION),
            intent=coerce_intent(req.get("intent")),
            path=coerce_path(req.get("path")),
            intent_confidence=float(req.get("intent_confidence") or 0.0),
            subject=SubjectStruct.from_dict(req.get("subject")),
            purpose=req.get("purpose", ""),
            decision=coerce_decision(req.get("decision")),
            audience=req.get("audience", ""),
            implicit_needs=needs,
            tier=req.get("tier", "free"),
            instruction=req.get("instruction", ""),
            context=req.get("context") or {},
            attachments=req.get("attachments") or [],
        )

    def to_dict(self) -> dict:
        """序列化（枚举回字符串·可 JSON）。"""
        d = asdict(self)
        d["intent"] = self.intent.value
        d["path"] = self.path.value
        d["decision"] = self.decision.value
        return d
