"""模型路由层 · 按任务从周更模型表自适应选型(成本×质量平衡)。

背景(foundation-constraints 铁律一 + 用户 2026-06-21 指示):
  sf-models-index.html 每周更新硅基可用模型+价格+能力 → sync_sf_models.py 转 sf_models.json。
  本层按 probe 各 LLM 任务的"质量需求×成本上限"自动选最优国产模型——
  **模型表周更后路由自动用上最新最优模型,无需改代码**;某模型下架则自动降级同档次替代。

三类任务的选型哲学(既降本又保质):
  - gates(八闸): yes/no 短判断,质量需求低 → **免费模型优先**(Qwen3-8B),省钱不降质
  - polish(润色): 长文重写,质量敏感 → 均衡旗舰(Qwen3.5-122B,质量/成本最优点)
  - vision(视听): 视频深度理解(含语音) → **必须全模态 Omni**(听+看+说)·选思维链版(同价更深)

铁律:
  - 只选国产(govcn=True),海外模型 sync 阶段已剔除,此处双保险
  - env 显式指定模型时优先 env(向后兼容/人工锁定)
  - 注册表缺失(CI/无 HTML)→ 用硬编码国产 fallback,永不阻塞
"""
from __future__ import annotations

import json
import os
import pathlib

_REGISTRY = pathlib.Path(__file__).parent.parent / "data" / "sf_models.json"

# ── 任务选型规格(prefer 是我按 note 列人工择优的有序候选,registry 缺该模型自动跳下一个)──
TASK_SPEC = {
    # 八闸:claim 忠实度判断(非纯 yes/no,需基本判断力)→ 便宜但够用(35B 均衡·非免费小模型)
    # 既降本(¥0.40 vs 旗舰 ¥8·20×)又保质(35B 判断力够).免费 8B 留作降级.
    "gates": {
        "prefer": ["Qwen/Qwen3.5-35B-A3B", "Qwen/Qwen3-30B-A3B-Instruct-2507",
                   "Qwen/Qwen3-14B", "Qwen/Qwen3-8B"],
        "category": {"chat"},
        "max_price_in": 0.7,
        "strategy": "cheapest",
        "env": ("GATES_MODEL", "GATES_LITELLM_MODEL"),
        "fallback": "Qwen/Qwen3.5-35B-A3B",
    },
    # 润色:质量敏感的长文重写,均衡旗舰(质量/成本最优点)
    "polish": {
        "prefer": ["Qwen/Qwen3.5-122B-A10B", "deepseek-ai/DeepSeek-V4-Pro",
                   "Qwen/Qwen3.6-35B-A3B", "Qwen/Qwen3.5-35B-A3B"],
        "category": {"chat", "code"},
        "max_price_in": 4.0,
        "strategy": "best",
        "env": ("REPORT_POLISH_MODEL",),
        "fallback": "Qwen/Qwen3.5-122B-A10B",
    },
    # 评论洞察:评论聚类/情感/意向识别,轻量结构化任务(短文本批量分类)→ 复用 gates 同档便宜国产模型
    # 既降本(35B 均衡·非旗舰)又够用(聚类/分类判断力足).全国产·数据不出境.
    "comment": {
        "prefer": ["Qwen/Qwen3.5-35B-A3B", "Qwen/Qwen3-30B-A3B-Instruct-2507",
                   "Qwen/Qwen3-14B", "Qwen/Qwen3-8B"],
        "category": {"chat"},
        "max_price_in": 0.7,
        "strategy": "cheapest",
        "env": ("COMMENT_MODEL", "COMMENT_LITELLM_MODEL"),
        "fallback": "Qwen/Qwen3.5-35B-A3B",
    },
    # 视听:视频含语音 → 必须全模态 Omni(VL 是纯视觉无听觉,不行);思维链版同价更深
    "vision": {
        "prefer": ["Qwen/Qwen3-Omni-30B-A3B-Thinking",
                   "Qwen/Qwen3-Omni-30B-A3B-Instruct"],
        "must_substr": "omni",        # 必须含 omni(全模态)
        "max_price_in": 1.5,
        "strategy": "best",
        "env": ("AUDIOVISUAL_MODEL",),
        "fallback": "Qwen/Qwen3-Omni-30B-A3B-Thinking",
    },
}

_cache: dict | None = None


def _load() -> dict:
    global _cache
    if _cache is None:
        try:
            _cache = json.loads(_REGISTRY.read_text(encoding="utf-8"))
        except Exception:
            _cache = {"models": []}
    return _cache


def _models() -> list:
    return _load().get("models", [])


def select(task: str) -> str:
    """返回该任务应使用的硅基模型 id。env 优先 → prefer 候选 → 同档自动降级 → fallback。"""
    spec = TASK_SPEC.get(task)
    if not spec:
        return ""
    # 1. env 显式锁定(人工/向后兼容)
    for ev in spec.get("env", ()):
        v = os.getenv(ev)
        if v:
            return v
    models = {m["id"]: m for m in _models() if m.get("govcn")}
    # 2. prefer 有序候选:取第一个仍在表中的(防周更下架)
    for pid in spec["prefer"]:
        if pid in models:
            return pid
    # 3. 注册表自动选:按 category/能力/价格上限过滤 → strategy 排序
    def ok(m):
        if m.get("price_in") is None or m["price_in"] > spec["max_price_in"]:
            return False
        if "category" in spec and m.get("category") not in spec["category"]:
            return False
        if "must_substr" in spec and spec["must_substr"] not in m["id"].lower():
            return False
        return True
    cands = [m for m in models.values() if ok(m)]
    if cands:
        if spec["strategy"] == "cheapest":
            cands.sort(key=lambda m: (m["price_in"], m["price_out"] or 0))
        else:  # best:tier max 优先,再按性价比(out 价低者优)
            rank = {"max": 0, "pro": 1, "standard": 2, "lite": 3}
            cands.sort(key=lambda m: (rank.get(m.get("tier"), 9),
                                      m.get("price_out") or 99))
        return cands[0]["id"]
    # 4. 永不阻塞:硬编码国产 fallback
    return spec["fallback"]


def explain(task: str) -> dict:
    """选型透明化(供日志/审计):选了谁+价格+依据。"""
    mid = select(task)
    m = next((x for x in _models() if x["id"] == mid), None)
    return {"task": task, "model": mid,
            "price_in": (m or {}).get("price_in"),
            "price_out": (m or {}).get("price_out"),
            "free": (m or {}).get("free", False),
            "registry": _REGISTRY.exists()}


if __name__ == "__main__":
    for t in TASK_SPEC:
        print(explain(t))
