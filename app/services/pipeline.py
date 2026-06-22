"""核心管线 · req → 意图(公开提取/深探) → L0 → 成品 + meta + cost + guards。

task 体调用：tasks.run_task(tid, lambda task_id: pipeline.process(req, principal, task_id))
- 公开提取（A线·免费档）：正文/来源落对象存储，aigc_flag=False
- 深探（B线·付费档·三层深度线）：评级+结构+竞品+二创，aigc_flag=True
"""
from __future__ import annotations

import datetime
import json
import time
from typing import Any

from app import config
from app.core import billing, guards, storage
from app.l0 import deep_probe, extract_public, find_url

_DEEP_WORDS = ("深探", "调研", "靠谱", "二创", "对标", "拍板", "评级", "值不值", "深度分析")


def _is_deep(instruction: str) -> bool:
    return any(w in (instruction or "") for w in _DEEP_WORDS)


def _meta(models: list, sources: list, confidence: float, t0: float,
          aigc: bool, geo: bool = False, extra: dict | None = None) -> dict:
    m = {
        "models_used": models, "data_sources": sources,
        "confidence": confidence, "duration_ms": int((time.perf_counter() - t0) * 1000),
        "aigc_flag": aigc, "geo_publishable": geo,
        "tool_id": "probe", "contract_version": config.CONTRACT_VERSION,
    }
    if extra:
        m.update(extra)
    return m


def _src_json(url: str, data: dict) -> str:
    return json.dumps({
        "url": url, "kind": data.get("kind"), "title": data.get("title", ""),
        "extractor": data.get("extractor", ""),
        "copyright_status": "未核实 · 复用需过版权门",
        "collected_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }, ensure_ascii=False, indent=2)


def process(req: dict, principal, task_id: str) -> dict[str, Any]:
    """task 体：解析意图 → 提取/深探 → 出口契约（含 guards）。"""
    t0 = time.perf_counter()
    instruction = req.get("instruction", "")
    url = find_url(instruction, req.get("context"), req.get("attachments"))
    if not url:
        raise ValueError("未找到链接 URL")
    if _is_deep(instruction):
        return _deep(url, principal, task_id, t0)
    return _public(url, task_id, t0)


def process_brief(brief, route_decision, principal, task_id: str) -> dict[str, Any]:
    """脊柱路径：按 route_decision.path 走（替代 _is_deep 关键词二分）。
    首版映射：A→_public · B/D→_deep · C→_discover_stub（W5 填实四路径 handler）。"""
    t0 = time.perf_counter()
    path = route_decision.path.value if route_decision else brief.path.value
    url = (brief.subject.resolved_url if brief.subject else None) \
        or find_url(brief.instruction, brief.context, brief.attachments)
    if path in ("B", "D"):
        if not url:
            raise ValueError(f"{path} 路径需 URL（subject 未解析）")
        return _deep(url, principal, task_id, t0)
    if path == "C":
        return _discover_stub(brief, route_decision, task_id, t0)
    # A 原创放大
    if not url:
        raise ValueError("A 路径需 URL")
    return _public(url, task_id, t0)


def _discover_stub(brief, route_decision, task_id: str, t0: float) -> dict:
    """C 选题发现 · 搜索驱动版（SearXNG + HackerNews · W5 接 L2 发现层后可升为完整四路径）。"""
    keyword = ""
    if brief and brief.subject:
        keyword = (getattr(brief.subject, "resolved_url", None) or
                   getattr(brief.subject, "raw", None) or "")
    if not keyword and brief:
        keyword = (brief.instruction or "")[:60]

    ideas: list[str] = []

    # 路径1：SearXNG 联网搜索
    try:
        from app.datasources.public.searxng import search as sx_search
        results = sx_search(keyword, max_results=5) if keyword else []
        for r in results[:5]:
            title = r.get("title") or ""
            url = r.get("url") or ""
            if title:
                ideas.append(f"- [{title[:60]}]({url})")
    except Exception:  # noqa: BLE001
        pass

    # 路径2：HackerNews 热帖兜底（无 key 全免费）
    if not ideas:
        try:
            from app.datasources.public.hackernews import search as hn_search
            hn_results = hn_search(keyword or "trending", max_results=5)
            for r in hn_results[:5]:
                title = r.get("title") or ""
                url = r.get("url") or r.get("story_url") or ""
                if title:
                    ideas.append(f"- [{title[:60]}]({url})")
        except Exception:  # noqa: BLE001
            pass

    if ideas:
        content = f"## 选题发现（C 路径）\n\n关键词：**{keyword[:50]}**\n\n" + \
                  "### 相关内容线索\n" + "\n".join(ideas) + \
                  "\n\n> 数据来源：SearXNG 联网搜索 · 完整选题四路径(L2发现层)待 W5 实现"
        is_stub = False
    else:
        content = (f"选题发现（C 路径）· 关键词：{keyword[:50] or '未指定'}\n"
                   "当前搜索层无结果或未配置·完整四路径 L2 发现层待 W5 实现。")
        is_stub = True

    return {
        "deliverable": {
            "type": "discover", "kind": "discover", "depth": guards.DEPTH_PUBLIC,
            "content": content,
            "_path": "C", "_circles": route_decision.circles if route_decision else [],
            "_stub": is_stub,
        },
        "meta": _meta([], [], 0.0, t0, aigc=False,
                      extra={"path": "C", "stub": is_stub, "ideas_count": len(ideas)}),
        "cost": billing.cost_public(),
    }


def _public(url: str, task_id: str, t0: float) -> dict:
    """A 线公开提取（免费档）。"""
    data = extract_public(url)
    if data.get("needs_authorized_api"):
        deliverable = {
            "type": "notice", "kind": data["kind"], "depth": guards.DEPTH_PUBLIC,
            "content": f"{data['kind']} 取数需第三方授权 API（合规整改：已停用自建爬取）。"
                       f"数据源选型 + R1 授权 + 标准19核验后开通，见 app/datasources/ledger.yaml。",
            "_compliance": "不自建爬虫·只用第三方授权 API（probe 数据来源铁律）",
        }
        resp = {"deliverable": deliverable,
                "meta": _meta([], [url], 0.0, t0, aigc=False,
                              extra={"needs_authorized_api": True}),
                "cost": billing.cost_public()}
    elif data.get("failed"):
        raise RuntimeError(f"提取失败（{data['kind']}，降级链已尽）")
    else:
        files = {"正文.md": data["text"], "来源.json": _src_json(url, data)}
        stored = storage.put_deliverable(task_id, files)
        deliverable = {
            "type": "extraction", "kind": data["kind"], "depth": guards.DEPTH_PUBLIC,
            "title": data["title"], "files": stored,
            "preview": data["text"][:500],
            "_aigc_notice": "内容为原链接提取，非 AI 生成",
        }
        # TikHub 等适配器产生真实数据成本时合入 billing（B2 修复）
        cost = billing.cost_public()
        if data.get("cost_hint", {}).get("premium_data", 0) > 0:
            cost = {"base": cost["base"],
                    "premium_data": data["cost_hint"]["premium_data"]}
        resp = {"deliverable": deliverable,
                "meta": _meta([], [url], 0.9, t0, aigc=False),
                "cost": cost}
    guards.check_response(resp)
    return resp


def _audit_tier(principal) -> str:
    """principal.tier → run_audit 档（极速版 free / 深度版 paid）。"""
    t = getattr(principal, "tier", "free")
    return "paid" if t in ("paid", "member") else "free"


def _build_audit_input(report: dict, public: dict, url: str) -> tuple[list[str], list[dict]]:
    """把 deep_probe 结论原子化为 8 闸 run_audit 的 claims + sources。"""
    claims: list[str] = [
        c["claim"] for c in report.get("fact_check", {}).get("claims", [])
        if c.get("claim")
    ]
    sf = report.get("structure_formula", "")
    if sf and "待" not in sf:
        claims.append(f"内容结构公式：{sf}")
    if not claims:
        claims = [report.get("headline") or url]
    sources: list[dict] = [{
        "url": url, "title": public.get("title", ""),
        "text": (public.get("text") or "")[:1000], "source_type": "primary",
    }]
    for s in report.get("fact_sources", []):
        if s.get("url"):
            sources.append({"url": s["url"], "title": s.get("title", ""),
                            "text": s.get("title", ""), "source_type": "secondary"})
    return claims, sources


def _deep(url: str, principal, task_id: str, t0: float) -> dict:
    """B 线深探（付费档 · 三层深度线）。"""
    public = extract_public(url)
    if public.get("needs_authorized_api") or public.get("failed"):
        raise RuntimeError(f"深探需先取数，但 {public.get('kind')} 需第三方授权 API（合规整改：已停用自建爬取）")
    report = deep_probe(url, public)
    # MVP 桩阶段：B线为占位实现，不向用户收 premium 费用（D4/B2 修复）
    is_stub = report.get("_stub", False)
    # ── 接 8 闸审核（护城河·"敢担保"兑现）+ 确定性自评（信号C·智能界定）──
    from app.audit.gates import run_audit
    from app.audit import certainty
    claims, sources = _build_audit_input(report, public, url)
    audit = run_audit(claims, sources, tier=_audit_tier(principal))
    cert = certainty.assess(audit)
    layered = guards.redact_by_tier(report, principal.tier)
    deliverable = {
        "type": "deep_report", "kind": public["kind"], "report": layered,
        "conclusion_label": audit["conclusion_label"],     # 敢担保标识·各档都给
        "audit": {"trace_id": audit["trace_id"], "gates_run": audit["gates_run"],
                  "all_passed": audit["all_passed"], "tier": audit["tier"],
                  "flags": audit["flags"][:5]},
        "certainty": cert,                                  # 信号C·极速版是否需升级深度版
        "_aigc_notice": "本报告含 AI 生成分析（深探结论）",
        **({"_stub_notice": "深探为 MVP 预览，完整 LLM 分析上线前不计付费"} if is_stub else {}),
    }
    resp = {
        "deliverable": deliverable,
        "meta": _meta(["probe-deep-stub"] if is_stub else ["probe-deep"], [url], 0.7, t0,
                      aigc=True, geo=True,
                      extra={"conclusion_block": {
                          "headline": report["headline"],
                          "key_points": [report["structure"]],
                          "brand_anchor": "probe.metafoclaw.com"}}),
        "cost": billing.cost_deep(False) if is_stub else billing.cost_deep(principal.is_paid),
    }
    guards.check_response(resp)
    return resp
