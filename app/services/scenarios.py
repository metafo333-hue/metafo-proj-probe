"""B/C/D/E 四赛道 MVP 场景 · 复用 OS1 编排把已建适配器扇出成多源情报包。

落地范围（设计↔落地 SSOT P1-b·把「27 场景」从纯设计变可演示）：
  B1 企业全景    （商业·D11/D4）: opencorporates + edgar + wikipedia
  C5 制裁合规扫描（尽调·D8·非 PIPL 实体筛查）: ofac_sdn + opencorporates
  D2 技术情报    （调研·D12）: github repo 健康 + osv CVE
  E3 信息源可信度（核查·D6/D5）: wikipedia + gdelt + openalex 多源交叉

每个场景 = 绑定适配器 → OS1 fan_out 并发扇出 → 组装情报包（含 partial 标注 + 多源
交叉可信度提示）。适配器 callable 可注入（_xxx 参数）便于离线测试；生产用真适配器。
情报包形态：{scenario, query, ok, partial, sources(扇出摘要), findings(带源溯源), credibility_note}。
"""
from __future__ import annotations

from typing import Any, Callable

from app.datasources.orchestrator import SourceSpec, fan_out, FanOutResult


# 源权威度映射（喂闸1 Admiralty reliability_hint·官方/权威源高分）
_SOURCE_RELIABILITY = {
    "edgar": "A", "ofac_sdn": "A", "osv": "A",          # 官方/权威披露
    "opencorporates": "B", "github": "B", "openalex": "B",
    "wikipedia": "C", "gdelt": "C",                      # 二手/聚合
}


def _to_audit_inputs(packet: dict[str, Any]) -> tuple[list[str], list[dict]]:
    """情报包 findings → 八闸输入(claims + sources)。"""
    sources = []
    for f in packet["findings"]:
        sid = f["source"]
        sources.append({
            "url": f"probe://source/{sid}",
            "title": f"{sid}·{f.get('domain', '')}",
            "text": str(f.get("data"))[:600],
            "timestamp": "",
            "reliability_hint": _SOURCE_RELIABILITY.get(sid, "C"),
            "source_type": "api",
        })
    n = len(sources)
    claim = (f"{packet['query']}·{packet['scenario']}：经 {n} 个授权源采集"
             + ("（部分源缺失）" if packet["partial"] else "（全源命中）"))
    return [claim], sources


def enrich_with_audit(packet: dict[str, Any], *, tier: str = "paid") -> dict[str, Any]:
    """情报包 → 过八闸 → 附「可信度三标签」(probe 护城河：带可信度的结论)。

    失败降级：审核异常不阻塞情报包，标 conclusion_label.error。
    """
    claims, sources = _to_audit_inputs(packet)
    if not sources:
        packet["conclusion_label"] = {
            "source_reliability": None, "confidence_level": "无源·不可出",
            "evidence_strength": None}
        return packet
    try:
        from app.audit.gates import run_audit
        res = run_audit(claims, sources, tier=tier)
        cl = res.get("conclusion_label") or {}
        packet["conclusion_label"] = {
            "source_reliability": cl.get("source_reliability"),
            "confidence_level": cl.get("confidence_level"),
            "evidence_strength": cl.get("evidence_strength"),
            "trace_id": res.get("trace_id"),
        }
        packet["audit_flags"] = res.get("flags", [])
    except Exception as e:  # noqa: BLE001
        packet["conclusion_label"] = {"error": f"{type(e).__name__}: {e}"}
    return packet


# ── 组装 + 可信度提示 ────────────────────────────────────────────
def _credibility_note(out: FanOutResult) -> str:
    n = len(out.ok)
    if n >= 2:
        return f"{n} 源交叉印证 · 可信度较高" + ("（部分源缺失·见 sources_failed）" if out.partial else "")
    if n == 1:
        return "单源命中 · 建议补充印证后采信"
    return "无可用源 · 结论不可出（须人工或换源）"


def _assemble(scenario: str, query: str, domains: list[str],
              out: FanOutResult, *, audit: bool = True,
              tier: str = "paid") -> dict[str, Any]:
    findings = [
        {"source": r.source_id, "domain": r.domain,
         "elapsed_ms": r.elapsed_ms, "data": r.data}
        for r in out.ok
    ]
    packet = {
        "scenario": scenario,
        "query": query,
        "domains": domains,
        "ok": bool(out.ok),
        "partial": out.partial,
        "sources": out.summary(),
        "findings": findings,
        "credibility_note": _credibility_note(out),
    }
    # 过八闸出可信度三标签（probe 价值：带可信度的结论·非裸数据堆）
    if audit:
        packet = enrich_with_audit(packet, tier=tier)
    return packet


# ── B1 企业全景（商业）───────────────────────────────────────────
def scenario_b1_company(name: str, *, jurisdiction: str = "", audit: bool = True,
                        _oc: Callable | None = None,
                        _edgar: Callable | None = None,
                        _wiki: Callable | None = None,
                        timeout: float = 8.0) -> dict[str, Any]:
    """公司名 → 工商(OpenCorporates)+SEC披露(EDGAR)+百科(Wikipedia) 多源全景。"""
    if _oc is None:
        from app.datasources.public import opencorporates as _m
        _oc = lambda q: _m.search_company(q, jurisdiction=jurisdiction) if jurisdiction \
            else _m.search_company(q)
    if _edgar is None:
        from app.datasources.public import edgar as _m2
        _edgar = _m2.company_filings
    if _wiki is None:
        from app.datasources.public import wikipedia as _m3
        _wiki = lambda q: _m3.search(q, limit=3)

    specs = [
        SourceSpec("opencorporates", _oc, (name,), domain="D11", timeout=timeout),
        SourceSpec("edgar", _edgar, (name,), domain="D4", timeout=timeout),
        SourceSpec("wikipedia", _wiki, (name,), domain="D1", timeout=timeout),
    ]
    return _assemble("B1·企业全景", name, ["D11", "D4", "D1"],
                     fan_out(specs, default_timeout=timeout), audit=audit)


# ── C5 制裁/合规风险扫描（尽调·实体筛查·非 PIPL 个人数据）────────────
def scenario_c5_compliance(entity: str, *, audit: bool = True,
                           _ofac: Callable | None = None,
                           _oc: Callable | None = None,
                           timeout: float = 8.0) -> dict[str, Any]:
    """实体名 → OFAC 制裁名单筛查 + 工商存续，输出合规风险信号（不涉个人隐私）。"""
    if _ofac is None:
        from app.datasources.public import ofac_sls as _m
        _ofac = _m.search_sdn
    if _oc is None:
        from app.datasources.public import opencorporates as _m2
        _oc = _m2.search_company

    specs = [
        SourceSpec("ofac_sdn", _ofac, (entity,), domain="D8", timeout=timeout),
        SourceSpec("opencorporates", _oc, (entity,), domain="D11", timeout=timeout),
    ]
    out = fan_out(specs, default_timeout=timeout)
    pkt = _assemble("C5·制裁合规扫描", entity, ["D8", "D11"], out, audit=audit)
    # 制裁命中 = 高风险信号（OFAC 源有非空结果）
    sanction_hit = any(r.source_id == "ofac_sdn" and r.data for r in out.ok)
    pkt["risk_flag"] = "🔴 制裁名单疑似命中" if sanction_hit else "🟢 制裁名单未命中"
    return pkt


# ── D2 技术/开源情报（调研）──────────────────────────────────────
def scenario_d2_tech(repo: str, *, ecosystem: str = "PyPI", package: str = "",
                     audit: bool = True,
                     _gh: Callable | None = None,
                     _osv: Callable | None = None,
                     timeout: float = 8.0) -> dict[str, Any]:
    """repo → GitHub 健康度 + OSV 已知漏洞(CVE)，输出技术选型情报。"""
    if _gh is None:
        from app.datasources.public import github_src as _m
        _gh = _m.repo_info
    if _osv is None:
        from app.datasources.public import osv as _m2
        _osv = lambda pkg: _m2.query_package(pkg, ecosystem)

    pkg = package or repo.rstrip("/").split("/")[-1]
    specs = [
        SourceSpec("github", _gh, (repo,), domain="D12", timeout=timeout),
        SourceSpec("osv", _osv, (pkg,), domain="D8", timeout=timeout),
    ]
    return _assemble("D2·技术情报", repo, ["D12", "D8"],
                     fan_out(specs, default_timeout=timeout), audit=audit)


# ── E3 信息源可信度（核查·多源交叉）──────────────────────────────
def scenario_e3_source(topic: str, *, audit: bool = True,
                       _wiki: Callable | None = None,
                       _gdelt: Callable | None = None,
                       _openalex: Callable | None = None,
                       timeout: float = 8.0) -> dict[str, Any]:
    """主题 → 百科 + 全球新闻(GDELT) + 学术(OpenAlex) 三源交叉评估可信度。"""
    if _wiki is None:
        from app.datasources.public import wikipedia as _m
        _wiki = lambda q: _m.search(q, limit=3)
    if _gdelt is None:
        from app.datasources.public import gdelt as _m2
        _gdelt = _m2.search
    if _openalex is None:
        from app.datasources.public import openalex as _m3
        _openalex = _m3.search_works

    specs = [
        SourceSpec("wikipedia", _wiki, (topic,), domain="D1", timeout=timeout),
        SourceSpec("gdelt", _gdelt, (topic,), domain="D6", timeout=timeout),
        SourceSpec("openalex", _openalex, (topic,), domain="D5", timeout=timeout),
    ]
    return _assemble("E3·信息源可信度", topic, ["D1", "D6", "D5"],
                     fan_out(specs, default_timeout=timeout), audit=audit)


# ── 声明式简单场景（真适配器支撑·批量扩 27 场景广度）──────────────
# 每条 source: (source_id, module, func, domain, pass_query)
# pass_query=False → 适配器无 query 参数（宏观数据类·调用忽略 query）
import importlib

_SIMPLE_SCENARIOS: dict[str, dict[str, Any]] = {
    "A4": {"label": "A4·趋势雷达", "domains": ["D6", "D7"], "sources": [
        ("gdelt", "gdelt", "search", "D6", True),
        ("hackernews", "hackernews", "search", "D7", True),
        ("searxng", "searxng", "search", "D6", True)]},
    "B3": {"label": "B3·行业赛道扫描", "domains": ["D4", "D5", "D1"], "sources": [
        ("gdelt", "gdelt", "search", "D4", True),
        ("openalex", "openalex", "search_works", "D5", True),
        ("wikipedia", "wikipedia", "search", "D1", True)]},
    "B6": {"label": "B6·品牌舆情监测", "domains": ["D6", "D7"], "sources": [
        ("gdelt", "gdelt", "search", "D6", True),
        ("reddit", "reddit_rss", "search", "D7", True)]},
    "C1": {"label": "C1·企业背调", "domains": ["D4", "D6"], "sources": [
        ("opencorporates", "opencorporates", "search_company", "D4", True),
        ("edgar", "edgar", "company_filings", "D6", True)]},
    "D1": {"label": "D1·深度调研", "domains": ["D1", "D5", "D6"], "sources": [
        ("searxng", "searxng", "search", "D1", True),
        ("wikipedia", "wikipedia", "search", "D5", True),
        ("hackernews", "hackernews", "search", "D6", True)]},
    "D3": {"label": "D3·学术专利情报", "domains": ["D5"], "sources": [
        ("openalex", "openalex", "search_works", "D5", True),
        ("arxiv", "arxiv", "search", "D5", True)]},
    "D4": {"label": "D4·政策宏观情报", "domains": ["D6", "D10"], "sources": [
        ("worldbank", "worldbank", "indicators_search", "D6", True),
        ("us_treasury", "us_treasury", "avg_interest_rates", "D10", False),
        ("frankfurter", "frankfurter", "latest", "D10", False)]},
    "E1": {"label": "E1·事实核查", "domains": ["D6", "D1"], "sources": [
        ("searxng", "searxng", "search", "D6", True),
        ("wikipedia", "wikipedia", "search", "D1", True),
        ("gdelt", "gdelt", "search", "D6", True)]},
    "E4": {"label": "E4·谣言钓鱼识别", "domains": ["D3", "D6"], "sources": [
        ("virustotal", "virustotal", "lookup", "D3", True),
        ("searxng", "searxng", "search", "D6", True)]},
}


def _bind_adapter(module: str, func: str, query: str, pass_query: bool) -> Callable:
    """惰性绑定 public 适配器为无参 callable（导入失败由 OS1 隔离为 error）。"""
    def _call() -> Any:
        m = importlib.import_module(f"app.datasources.public.{module}")
        f = getattr(m, func)
        return f(query) if pass_query else f()
    return _call


def run_simple_scenario(key: str, query: str, *, audit: bool = True,
                        timeout: float = 8.0) -> dict[str, Any]:
    """声明式简单场景统一运行器（复用 OS1 扇出 + 八闸）。"""
    cfg = _SIMPLE_SCENARIOS[key]
    specs = [
        SourceSpec(sid, _bind_adapter(mod, fn, query, pq), domain=dom, timeout=timeout)
        for (sid, mod, fn, dom, pq) in cfg["sources"]
    ]
    return _assemble(cfg["label"], query, cfg["domains"],
                     fan_out(specs, default_timeout=timeout), audit=audit)


def _make_simple(key: str) -> Callable:
    def _fn(query: str, *, audit: bool = True, timeout: float = 8.0) -> dict[str, Any]:
        return run_simple_scenario(key, query, audit=audit, timeout=timeout)
    _fn.__name__ = f"scenario_{key.lower()}"
    return _fn


# 场景注册表（详细场景 + 声明式简单场景·供路由/MetaAsk 意图路由按 key 调度）
REGISTRY: dict[str, Callable] = {
    "B1": scenario_b1_company,
    "C5": scenario_c5_compliance,
    "D2": scenario_d2_tech,
    "E3": scenario_e3_source,
    **{k: _make_simple(k) for k in _SIMPLE_SCENARIOS},
}


# ── 27 场景诚实覆盖账（真源·防"宣称全覆盖"）──────────────────────
# status: backed=多源场景已跑通 · atrack=A赛道抖音管线(account_chain) · blocked=缺适配器/PIPL
COVERAGE_27 = {
    # A 自媒体（A1-A7 走 account_chain 抖音管线·已建）
    "A1": "atrack", "A2": "atrack", "A3": "atrack", "A4": "backed",
    "A5": "atrack", "A6": "atrack", "A7": "atrack",
    # B 商业
    "B1": "backed", "B2": "blocked:builtwith/similarweb 无适配器", "B3": "backed",
    "B4": "blocked:keepa 无适配器", "B5": "blocked:appstore 无顶层函数", "B6": "backed",
    # C 尽调
    "C1": "backed", "C2": "blocked:人物背调涉PIPL·暂不开", "C3": "blocked:文档上传未接",
    "C4": "blocked:批量端点未建", "C5": "backed",
    # D 调研
    "D1": "backed", "D2": "backed", "D3": "backed", "D4": "backed",
    "D5": "blocked:docling 文档上传未接",
    # E 核查
    "E1": "backed", "E2": "blocked:反向图搜无适配器", "E3": "backed", "E4": "backed",
}


def coverage_summary() -> dict[str, Any]:
    from collections import Counter
    c = Counter(v.split(":")[0] for v in COVERAGE_27.values())
    return {"total": len(COVERAGE_27), **dict(c),
            "addressed": c["backed"] + c["atrack"],
            "multi_source_backed": [k for k, v in COVERAGE_27.items() if v == "backed"]}
