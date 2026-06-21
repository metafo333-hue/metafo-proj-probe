"""验证闭环 · verify_loop.py · 建议→执行→回测→科学归因→反哺权重（确定性·零 LLM）。

来源方法论：verification-loop-adaptive-research.md
  把 probe 从「开环建议机」升级为「闭环诊断引擎」——
  ① 建议落库（suggestion + 当时账号基线快照 baseline_snapshot）
  ② 标记执行（executed + 执行视频；<3 条标弱样本，不进强回测）
  ③ 到期回测（重采 result_snapshot → 算 Δ指标）
  ④ 科学归因（剔除大盘 / 季节 / 成长三层干扰 → correlated/no_effect/...）
  ⑤ 反哺权重（贝叶斯累积 feature_weight·禁单次翻转·N 次配对才升权重）

存储：本地 JSON（参 attribution_cache 范式·跨会话积累「建议-结果」配对库 = 护城河）。
  ~/.probe_cache/verify/{account_safe}/suggestions.json   # 建议台账 + 回测结果
  ~/.probe_cache/verify/_weights/feature_weights.json     # 全局经验库（行业×人群×阶段×特征）

防玄学四铁律（§4.3·内置 attribute）：
  1. 措辞 "相关/可能" 不用 "导致/因为"（不替平台算法下因果断言）
  2. 必标剔除了什么没剔除什么（method 决定 caveat）
  3. 样本门：执行视频 < 3 / 配对 < N → 不下结论·标 "趋势参考"
  4. 防单点偶然：权重贝叶斯累积·单次命中不翻转·须 N 次同类配对

PIPL/合规：「建议-结果」库脱敏存储·账号级聚合·赛道级沉淀（不存可识别个人敏感信息）。
  account_id 由调用方传脱敏 ID；feature_weight 库只存「行业×人群×阶段×特征」聚合，无账号身份。

纯函数·零网络·零 LLM（重采新数据由调用方注入 result_snapshot，本模块不抓取）。
"""
from __future__ import annotations

import json
import pathlib
from datetime import date, datetime, timezone
from typing import Any

# ──────────────────────────────────────────────────────────────────────────────
# 存储根（可被测试 monkeypatch 覆盖 → 用临时目录·不污染真库）
# ──────────────────────────────────────────────────────────────────────────────

_CACHE_ROOT = pathlib.Path.home() / ".probe_cache" / "verify"

# 防单点偶然：配对样本 < 此值，权重不进推荐池、置信度标"参考"（§九·防单点偶然）
_MIN_PAIRS_FOR_CONFIDENCE = 5
# 执行视频 < 此值 → 弱样本，回测不下强结论（§4.3 铁律3）
_MIN_EXEC_VIDEOS = 3
# 回测样本门（执行后产出视频）< 此值 → insufficient_sample
_MIN_BACKTEST_SAMPLE = 3

# 三轴默认回测周期（天）·按账号阶段差异化（§3.3）
_STAGE_CYCLE_DAYS = {
    "冷启动": 0,      # 不回测·先建基线
    "起号期": 14,     # 仅趋势提示
    "成长期": 21,     # 弱归因
    "成熟期": 30,     # 强归因
}

# 行业 → 主回测指标键（§3.1·黑盒指标退用公开代理）
_INDUSTRY_EXPECT_METRIC = {
    "餐饮": "homepage_visit",       # 核销黑盒→退 POI/主页代理
    "美业": "homepage_visit",       # 私信黑盒→主页→咨询漏斗代理
    "教育培训": "play_proxy",       # 完播无后台→平均播放时长代理
    "知识科普": "play_proxy",
    "服装零售": "homepage_visit",
    "生活服务": "homepage_visit",
    "知识IP": "followers",
}
_DEFAULT_EXPECT_METRIC = "followers"


# ──────────────────────────────────────────────────────────────────────────────
# 存储路径辅助
# ──────────────────────────────────────────────────────────────────────────────

def _safe(s: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in (s or ""))[:64]


def _account_file(account_id: str) -> pathlib.Path:
    return _CACHE_ROOT / _safe(account_id) / "suggestions.json"


def _weights_file() -> pathlib.Path:
    return _CACHE_ROOT / "_weights" / "feature_weights.json"


def _load_json(path: pathlib.Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — 损坏视为空·不阻塞
        return default


def _write_json(path: pathlib.Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _axis_key(axis: dict) -> str:
    return "|".join([
        axis.get("industry", "?"),
        axis.get("audience_seg", "?"),
        axis.get("account_stage", "?"),
    ])


# ──────────────────────────────────────────────────────────────────────────────
# ① 建议落库
# ──────────────────────────────────────────────────────────────────────────────

def record_suggestion(report_id: str, account_id: str, axis: dict,
                      feature_key: str, suggestion_text: str,
                      baseline_snapshot: dict) -> int:
    """诊断时调用·写台账 + 基线快照 + 按三轴算 expect_metric/expect_cycle。

    axis = {"industry", "audience_seg", "account_stage"}（三轴标签·科学适应 key）。
    baseline_snapshot = {followers, avg_play, avg_like, interaction_rate, homepage_visit, ...}。
    返回 suggestion id（账号内自增整数）。

    PIPL：account_id 须为调用方脱敏 ID；baseline_snapshot 只放聚合指标，不放粉丝个体信息。
    """
    if not account_id or not feature_key:
        raise ValueError("account_id 和 feature_key 必填")
    stage = axis.get("account_stage", "成长期")
    industry = axis.get("industry", "")
    path = _account_file(account_id)
    store = _load_json(path, {"suggestions": []})
    sug_id = (max((s["id"] for s in store["suggestions"]), default=0) + 1)
    store["suggestions"].append({
        "id": sug_id,
        "report_id": report_id,
        "account_id": account_id,
        "industry": industry,
        "audience_seg": axis.get("audience_seg", ""),
        "account_stage": stage,
        "feature_key": feature_key,
        "suggestion_text": suggestion_text,
        "baseline_snapshot": dict(baseline_snapshot or {}),
        "baseline_date": date.today().isoformat(),
        "expect_metric": _INDUSTRY_EXPECT_METRIC.get(industry, _DEFAULT_EXPECT_METRIC),
        "expect_cycle_days": _STAGE_CYCLE_DAYS.get(stage, 21),
        "executed": False,
        "executed_date": None,
        "executed_video_ids": [],
        "backtest": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    _write_json(path, store)
    return sug_id


# ──────────────────────────────────────────────────────────────────────────────
# ② 标记执行
# ──────────────────────────────────────────────────────────────────────────────

def mark_executed(account_id: str, sug_id: int, executed_date: str,
                  video_ids: list[str]) -> bool:
    """用户回传·标 executed=true + 执行视频。

    executed_video_ids < 3 → weak_sample=True（不进强回测·§4.3 铁律3）。
    返回 True=标记成功；False=未找到该建议。
    """
    path = _account_file(account_id)
    store = _load_json(path, {"suggestions": []})
    for s in store["suggestions"]:
        if s["id"] == sug_id:
            vids = list(video_ids or [])
            s["executed"] = True
            s["executed_date"] = executed_date
            s["executed_video_ids"] = vids
            s["weak_sample"] = len(vids) < _MIN_EXEC_VIDEOS
            _write_json(path, store)
            return True
    return False


# ──────────────────────────────────────────────────────────────────────────────
# ④ 科学归因（防玄学核心·先于 run_backtest 定义供单测直接打靶）
# ──────────────────────────────────────────────────────────────────────────────

def attribute(delta_raw: float, market_baseline: float, season_factor: float,
              sample_size: int, method: str) -> dict:
    """剔三层干扰 → 判定 verdict + confidence + caveat（防玄学四铁律内置）。

    delta_excess = delta_raw - market_baseline - season_factor
      （剔除大盘自然增长 + 季节性；成长曲线在 market_baseline 内一并代理）。
    method ∈ {self_pre_post, market_adjusted, did, scm} → 决定剔了什么、caveat 措辞。

    样本门（铁律3）：sample_size < _MIN_BACKTEST_SAMPLE → insufficient_sample（不下结论）。
    措辞（铁律1）：verdict 用 correlated_*，render 层用"相关/可能"不用"导致"。
    """
    method = method or "self_pre_post"
    # 铁律3：样本不足不下结论
    if sample_size < _MIN_BACKTEST_SAMPLE:
        return {
            "verdict": "insufficient_sample",
            "confidence": "参考",
            "delta_raw": round(float(delta_raw), 4),
            "delta_excess": None,
            "attribution_method": method,
            "caveat": (f"执行后产出视频仅 {sample_size} 条（<{_MIN_BACKTEST_SAMPLE}）"
                       "·样本不足·只作趋势参考·不下相关结论"),
        }

    # 剔除干扰：self_pre_post 拿不到大盘/季节 → 不剔，明示参考级
    if method == "self_pre_post":
        delta_excess = float(delta_raw)
        caveat = "仅自身前后对比·未剔除大盘/季节·结论为参考级（非定论）"
    else:
        delta_excess = float(delta_raw) - float(market_baseline or 0) - float(season_factor or 0)
        if method == "market_adjusted":
            caveat = "已剔除同赛道大盘·未剔除季节性（DiD 思想代理）·参考级"
        elif method == "did":
            caveat = "已剔大盘+季节（处理组−对照组·需平行趋势假设成立）"
        else:  # scm
            caveat = "合成对照·已加权合成反事实账号（单处理单元最优·仍为相关非因果）"

    # 判定（铁律1·相关措辞）
    if delta_excess > 0:
        verdict = "correlated_up"
    elif delta_excess < 0:
        verdict = "correlated_down"
    else:
        verdict = "no_effect"

    # 置信度：method 强度 × 样本量（成长曲线/季节剔得越多越高）
    if method in ("did", "scm") and sample_size >= 5:
        confidence = "high"
    elif method == "market_adjusted" and sample_size >= 5:
        confidence = "medium"
    elif sample_size >= _MIN_BACKTEST_SAMPLE:
        confidence = "low"
    else:
        confidence = "参考"

    return {
        "verdict": verdict,
        "confidence": confidence,
        "delta_raw": round(float(delta_raw), 4),
        "delta_excess": round(delta_excess, 4),
        "attribution_method": method,
        "caveat": caveat,
    }


# ──────────────────────────────────────────────────────────────────────────────
# ③ 到期回测
# ──────────────────────────────────────────────────────────────────────────────

def run_backtest(account_id: str, sug_id: int, result_snapshot: dict,
                 *, sample_size: int, market_baseline: float = 0.0,
                 season_factor: float = 0.0, method: str = "self_pre_post",
                 result_date: str | None = None) -> dict | None:
    """到期触发·result_snapshot=调用方重采的同结构指标 → 归因 → 写库 → 反哺。

    result_snapshot 须含与 baseline 同名的 expect_metric 键（如 followers）。
    delta_raw = result[metric] − baseline[metric]（自身前后差）。
    method 默认 self_pre_post（MVP）；有大盘基准时传 market_adjusted + market_baseline。
    返回 backtest dict（含 verdict）；未找到建议返回 None。

    冷启动/起号期防玄学：account_stage=冷启动 → 拒绝回测（§六·任何变化都是噪声）。
    """
    path = _account_file(account_id)
    store = _load_json(path, {"suggestions": []})
    sug = next((s for s in store["suggestions"] if s["id"] == sug_id), None)
    if sug is None:
        return None
    if sug["account_stage"] == "冷启动":
        bt = {
            "verdict": "no_backtest_cold_start",
            "confidence": "参考",
            "caveat": "冷启动账号无历史基线·算法未建标签·任何变化都是噪声·不回测（改走赛道经验库借库）",
            "result_date": result_date or date.today().isoformat(),
        }
        sug["backtest"] = bt
        _write_json(path, store)
        return bt

    metric = sug["expect_metric"]
    base_v = float((sug["baseline_snapshot"] or {}).get(metric, 0) or 0)
    res_v = float((result_snapshot or {}).get(metric, 0) or 0)
    delta_raw = res_v - base_v

    attr = attribute(delta_raw, market_baseline, season_factor, sample_size, method)
    bt = {
        "result_snapshot": dict(result_snapshot or {}),
        "result_date": result_date or date.today().isoformat(),
        "metric": metric,
        "sample_size": sample_size,
        "market_baseline": market_baseline,
        "season_factor": season_factor,
        **attr,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    sug["backtest"] = bt
    _write_json(path, store)

    # ⑤ 反哺（仅在有结论时·insufficient/cold_start 不喂权重·防噪声进飞轮）
    if attr["verdict"] in ("correlated_up", "correlated_down", "no_effect"):
        feed_back({
            "industry": sug["industry"],
            "audience_seg": sug["audience_seg"],
            "account_stage": sug["account_stage"],
        }, sug["feature_key"], attr["verdict"], sample_size)
    return bt


# ──────────────────────────────────────────────────────────────────────────────
# ⑤ 反哺权重（飞轮核心·贝叶斯累积·禁单次翻转）
# ──────────────────────────────────────────────────────────────────────────────

def feed_back(axis: dict, feature_key: str, verdict: str, sample_size: int) -> dict:
    """贝叶斯更新 feature_weight·hit/miss 累积·禁单次翻转权重。

    权重 = (hit + α) / (total + α + β)（Beta 后验均值·α=β=1 拉普拉斯平滑）。
    单次命中不把权重翻到 1，须 N 次同类配对累积。
    total_pairs < _MIN_PAIRS_FOR_CONFIDENCE → confidence='参考'·不进推荐池。
    """
    wfile = _weights_file()
    store = _load_json(wfile, {})
    key = _axis_key(axis) + "::" + feature_key
    rec = store.get(key) or {
        "industry": axis.get("industry", ""),
        "audience_seg": axis.get("audience_seg", ""),
        "account_stage": axis.get("account_stage", ""),
        "feature_key": feature_key,
        "hit_count": 0, "miss_count": 0, "total_pairs": 0,
        "weight": 0.5, "confidence": "参考",
    }
    if verdict == "correlated_up":
        rec["hit_count"] += 1
    else:  # no_effect / correlated_down 计 miss
        rec["miss_count"] += 1
    rec["total_pairs"] += 1

    # Beta 后验均值（拉普拉斯平滑·防单点翻转）
    a, b = 1.0, 1.0
    rec["weight"] = round((rec["hit_count"] + a) /
                          (rec["total_pairs"] + a + b), 4)
    if rec["total_pairs"] >= _MIN_PAIRS_FOR_CONFIDENCE * 2:
        rec["confidence"] = "high"
    elif rec["total_pairs"] >= _MIN_PAIRS_FOR_CONFIDENCE:
        rec["confidence"] = "medium"
    else:
        rec["confidence"] = "参考"  # 不进推荐池
    rec["last_updated"] = datetime.now(timezone.utc).isoformat()
    store[key] = rec
    _write_json(wfile, store)
    return rec


def cold_start_recommend(axis: dict, *, min_confidence: str = "medium") -> list[dict]:
    """冷启动借库·返回该 axis 已验证（confidence≥medium 且 weight>0.5）的高权重建议。

    新号无自身回测 → 借同（行业×人群×阶段）经验库已沉淀的高权重特征（§六）。
    confidence='参考'（配对不足）一律不返回·防把未验证的当定论推。
    """
    store = _load_json(_weights_file(), {})
    order = {"参考": 0, "medium": 1, "high": 2}
    floor = order.get(min_confidence, 1)
    out = []
    target = _axis_key(axis)
    for rec in store.values():
        if _axis_key(rec) != target:
            continue
        if order.get(rec.get("confidence", "参考"), 0) < floor:
            continue
        if rec.get("weight", 0) <= 0.5:  # 仅推命中倾向的特征
            continue
        out.append(rec)
    out.sort(key=lambda r: r.get("weight", 0), reverse=True)
    return out


# ──────────────────────────────────────────────────────────────────────────────
# 查询辅助
# ──────────────────────────────────────────────────────────────────────────────

def list_suggestions(account_id: str) -> list[dict]:
    """返回账号所有建议台账（含执行/回测状态）。"""
    return _load_json(_account_file(account_id), {"suggestions": []})["suggestions"]


def verified_suggestions(account_id: str) -> list[dict]:
    """返回已回测出结论的建议（供 render·correlated_*/no_effect）。"""
    out = []
    for s in list_suggestions(account_id):
        bt = s.get("backtest")
        if bt and bt.get("verdict") in ("correlated_up", "correlated_down", "no_effect"):
            out.append(s)
    return out


# ──────────────────────────────────────────────────────────────────────────────
# 渲染层（与 commercial.render_*_section 同构·说人话·全程相关措辞）
# ──────────────────────────────────────────────────────────────────────────────

_VERDICT_LABEL = {
    "correlated_up": ("📈", "相关上升"),
    "correlated_down": ("📉", "相关下降"),
    "no_effect": ("➡️", "未见明显相关变化"),
    "insufficient_sample": ("🟨", "样本不足·趋势参考"),
    "no_backtest_cold_start": ("🧊", "冷启动·暂不回测"),
}


def render_verify_section(account_id: str) -> str | None:
    """渲染"建议生效情况"报告段·展示已验证建议的回测结果（相关措辞·诚实标）。

    无任何已回测建议 → 返回 None（build_report 自动跳过）。
    """
    sugs = [s for s in list_suggestions(account_id) if s.get("backtest")]
    if not sugs:
        return None

    L: list[str] = []
    P = L.append
    P("## 上次给你的建议，照做后效果怎么样（验证闭环）")
    P("")
    P("> 这是 probe 的闭环：上次诊断给你的建议，你照做后我**重采你的真实数据回测**——"
      "并剔除大盘/季节干扰，只说**「相关」不说「因为」**（不替平台算法下因果断言）。")
    P("")

    for s in sugs:
        bt = s["backtest"]
        icon, label = _VERDICT_LABEL.get(bt.get("verdict"), ("·", bt.get("verdict", "")))
        P(f"**{icon} 建议：{s.get('suggestion_text', '(无)')}**")
        if not s.get("executed"):
            P("- ⏳ 你还没回传执行情况——照做后告诉我，我才能回测。")
            P("")
            continue
        if s.get("weak_sample"):
            P(f"- ⚠️ 执行后只产出 {len(s.get('executed_video_ids') or [])} 条视频"
              f"（<{_MIN_EXEC_VIDEOS}）·弱样本·下面结论仅趋势参考。")
        metric = bt.get("metric", s.get("expect_metric", ""))
        excess = bt.get("delta_excess")
        if excess is not None:
            P(f"- 回测判定：**{label}**（指标「{metric}」剔干扰后超额 Δ={excess}·"
              f"置信度 {bt.get('confidence')}）")
        else:
            P(f"- 回测判定：**{label}**（置信度 {bt.get('confidence')}）")
        P(f"- 诚实标注：{bt.get('caveat', '')}")
        P("")

    P("> ⚠️ 单次命中≠规律——须同类账号 N 次配对累积才升权重（防单点偶然）。"
      "整体建立在「视听<50%准确 + 多为公开代理指标」之上·为**参考级闭环·非定论**。")
    return "\n".join(L)
