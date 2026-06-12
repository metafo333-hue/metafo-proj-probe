"""闸0 过程留痕 · append-only 事件 + SHA-256 哈希链 + run_snapshot。

设计依据：probe-audit-system-v1.md § 二（闸0 过程留痕）

五原则
------
① 完整溯源链（W3C PROV 三元组）
② 不可篡改（SHA-256 哈希链，每条链入前条哈希）
③ 确定性可复现（prompt 哈希 + 版本固定 + 参数快照）
④ 独立可验证（事件独立可 replay）
⑤ 过程与结论物理分离（trace 层不持有结论文本，只持有元数据）

依赖：stdlib only（json + hashlib + uuid + datetime）
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


# ---------------------------------------------------------------------------
# 事件类型常量
# ---------------------------------------------------------------------------

class EventKind:
    RUN_START      = "run_start"
    GATE_START     = "gate_start"
    GATE_END       = "gate_end"
    SOURCE_FETCHED = "source_fetched"
    MODEL_CALL     = "model_call"
    CLAIM_SCORED   = "claim_scored"
    RUN_END        = "run_end"
    ERROR          = "error"


# ---------------------------------------------------------------------------
# 单条审计事件
# ---------------------------------------------------------------------------

@dataclass
class AuditEvent:
    """一条 append-only 审计事件（W3C PROV 三元组骨架）。

    Attributes
    ----------
    kind        : EventKind 常量
    actor       : 执行者（gate_id / model_id / "system"）
    entity      : 操作对象（claim_id / source_url / "run"）
    payload     : 事件元数据（不含原始模型输出全文）
    timestamp   : UTC ISO 8601
    prev_hash   : 前一条事件的 SHA-256 哈希（哈希链头 = "0"*64）
    event_hash  : 本条事件内容的 SHA-256（由 __post_init__ 计算）
    """
    kind:       str
    actor:      str
    entity:     str
    payload:    dict        = field(default_factory=dict)
    timestamp:  str         = ""
    prev_hash:  str         = "0" * 64
    event_hash: str         = field(default="", init=False)

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        # 计算本条哈希（prev_hash 已确定，保证链完整性）
        self.event_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """SHA-256(kind + actor + entity + payload_json + timestamp + prev_hash)。"""
        content = json.dumps(
            {
                "kind":      self.kind,
                "actor":     self.actor,
                "entity":    self.entity,
                "payload":   self.payload,
                "timestamp": self.timestamp,
                "prev_hash": self.prev_hash,
            },
            sort_keys=True,
            ensure_ascii=False,
        )
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict:
        return {
            "kind":       self.kind,
            "actor":      self.actor,
            "entity":     self.entity,
            "payload":    self.payload,
            "timestamp":  self.timestamp,
            "prev_hash":  self.prev_hash,
            "event_hash": self.event_hash,
        }


# ---------------------------------------------------------------------------
# AuditTrace：一次 run 的 append-only 事件链 + run_snapshot
# ---------------------------------------------------------------------------

class AuditTrace:
    """一次 probe audit run 的完整过程记录。

    每次 run_audit 调用创建一个 AuditTrace 实例。
    事件以 append-only 方式写入（禁止修改已写事件）。
    哈希链保证顺序不可篡改：每条事件的 event_hash 链入下一条的 prev_hash。

    用法
    ----
        trace = AuditTrace(job_id="job-001")
        trace.log(EventKind.GATE_START, actor="gate1", entity="run")
        snapshot = trace.run_snapshot(...)
        chain = trace.export_chain()
    """

    def __init__(self, job_id: Optional[str] = None) -> None:
        self.trace_id: str = str(uuid.uuid4())
        self.job_id:   str = job_id or self.trace_id
        self._events:  list[AuditEvent] = []
        self._snapshot: Optional[dict] = None

    # ------------------------------------------------------------------
    # 追加事件
    # ------------------------------------------------------------------

    def log(
        self,
        kind:    str,
        actor:   str,
        entity:  str,
        payload: Optional[dict] = None,
    ) -> AuditEvent:
        """追加一条事件，自动链接前条哈希。"""
        prev_hash = self._events[-1].event_hash if self._events else "0" * 64
        event = AuditEvent(
            kind      = kind,
            actor     = actor,
            entity    = entity,
            payload   = payload or {},
            prev_hash = prev_hash,
        )
        self._events.append(event)
        return event

    # ------------------------------------------------------------------
    # run_snapshot（可复现性锚点）
    # ------------------------------------------------------------------

    def run_snapshot(
        self,
        prompt_version:  str,
        model_versions:  dict[str, str],
        tier:            str,
        source_urls:     list[str],
        params:          Optional[dict] = None,
    ) -> dict:
        """记录 run 可复现参数快照（prompt 哈希 + 版本固定 + 数据源列表）。

        Parameters
        ----------
        prompt_version  : prompt 模板版本号（语义版本字符串）
        model_versions  : {gate_id: model_id}（非 alias，精确版本）
        tier            : 审核强度档（free/preview/paid）
        source_urls     : 所有参与本次 run 的数据源 URL 列表
        params          : 其他任意可复现参数（温度、seed 等）

        Returns
        -------
        dict：run_snapshot 字典，同时写入 _snapshot 属性。
        """
        snapshot = {
            "trace_id":       self.trace_id,
            "job_id":         self.job_id,
            "prompt_version": prompt_version,
            "prompt_hash":    hashlib.sha256(
                prompt_version.encode("utf-8")
            ).hexdigest()[:16],
            "model_versions": model_versions,
            "tier":           tier,
            "source_urls":    source_urls,
            "params":         params or {},
            "created_at":     datetime.now(timezone.utc).isoformat(),
        }
        self._snapshot = snapshot
        # 同时写一条 run_start 事件
        self.log(
            EventKind.RUN_START,
            actor   = "system",
            entity  = "run",
            payload = {"snapshot_hash": hashlib.sha256(
                json.dumps(snapshot, sort_keys=True).encode()
            ).hexdigest()[:16]},
        )
        return snapshot

    # ------------------------------------------------------------------
    # 导出与验证
    # ------------------------------------------------------------------

    def export_chain(self) -> list[dict]:
        """导出完整事件链（供审计 / 回放使用）。"""
        return [e.to_dict() for e in self._events]

    def verify_chain(self) -> bool:
        """验证哈希链完整性（用于外部审计）。

        Returns True 若链头到链尾每条 prev_hash 都与前条 event_hash 一致。
        """
        for i, event in enumerate(self._events):
            expected_prev = self._events[i - 1].event_hash if i > 0 else "0" * 64
            if event.prev_hash != expected_prev:
                return False
        return True

    def __len__(self) -> int:
        return len(self._events)

    def __repr__(self) -> str:
        return f"<AuditTrace trace_id={self.trace_id} events={len(self._events)}>"
