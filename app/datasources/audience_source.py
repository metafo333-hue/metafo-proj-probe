"""粉丝画像取数 · 三档分级（授权/对标/谨慎）· 数据不出境（可插拔接口·灰度方案）。

来源方法论：audience-profile-adaptive-research.md §四 + §七.1
  A 路 · 创作者后台授权（official_authorized·🟩 最准最合规·默认走）
  B 路 · 第三方达人分析（对标·🟨 经验区间·非本号粉丝隐私）——预留接口
  C 路 · 粉丝列表反推聚合（self_inferred·🟥 自建推断·默认关·待元东方拍板）

PIPL 合规铁律：
  - 性别/年龄/地域=个人信息；人脸/声音=敏感个人信息（出境不可逆）。
  - 默认走 A（创作者本人授权数据·本人提供）；不自建爬取并落库粉丝个体信息。
  - C 路（粉丝列表聚合）默认关闭（ENABLE_FOLLOWER_AGGREGATION=False）：
    开启需 ① 元东方拍板放行 ② 创作者明确授权分析自己粉丝 ③ 只出聚合统计·不落个体。
  - 全程国产 LLM·数据不出境。

可插拔（灰度）：商业链不自建抓取；A 路授权 / 灰度 feed 在 register_source 接口后接。
"""
from __future__ import annotations

from typing import Any, Callable

# C 路总开关·默认关·🟥 待元东方拍板（合规审慎）
ENABLE_FOLLOWER_AGGREGATION = False

# 灰度可插拔注册表：source_name → callable(ctx) -> dict|None
# 商业链默认不注册任何自建抓取源；A 路授权数据走 from_creator_export（不入注册表，直解析）。
_REGISTRY: dict[str, Callable[..., dict | None]] = {}


def register_source(name: str, fn: Callable[..., dict | None]) -> None:
    """灰度注册画像数据源（如授权 feed / 对标源）。商业链禁注册自建爬粉丝源。"""
    _REGISTRY[name] = fn


def get_source(name: str) -> Callable[..., dict | None] | None:
    return _REGISTRY.get(name)


def from_creator_export(payload: dict | None) -> dict | None:
    """A 路：解析创作者中心后台粉丝画像（用户主动提供的截图 OCR / 导出 JSON）。

    最准最合规·标 source='official_authorized'（→ 🟩）。
    payload 为空 → None（调用方走 target_only 兜底）。
    """
    if not payload:
        return None
    return {
        "source": "official_authorized",          # → 🟩
        "gender": payload.get("gender"),           # {"male": x, "female": y}
        "age": payload.get("age"),                 # {"18-24": .., "25-30": ..}
        "geo": payload.get("geo"),                 # {"本地": .., "省内": .., "全国": ..}
        "active_hours": payload.get("active_hours"),
        "interests": payload.get("interests"),
    }


def from_benchmark(payload: dict | None) -> dict | None:
    """B 路：第三方达人画像估算（对标用·非本号粉丝·🟨 经验区间）。

    标 source='benchmark_estimate'·不碰本号粉丝隐私·仅作对标参照。
    """
    if not payload:
        return None
    return {
        "source": "benchmark_estimate",            # → 🟨
        "gender": payload.get("gender"),
        "age": payload.get("age"),
        "geo": payload.get("geo"),
        "active_hours": payload.get("active_hours"),
        "interests": payload.get("interests"),
    }


def from_follower_list(sec_uid: str, tikhub_key: str | None = None,
                       *, creator_authorized: bool = False) -> dict | None:
    """C 路：TikHub 粉丝列表 → 聚合（自建推断·非官方维度·🟥）。

    默认禁用（合规审慎）。开启需同时满足：
      ① ENABLE_FOLLOWER_AGGREGATION=True（元东方拍板放行）
      ② creator_authorized=True（创作者明确授权分析自己粉丝）
    只出聚合统计·不落个体（实现时聚合后即丢弃个体记录）。
    任一不满足 → None（合规默认关·🟥）。
    """
    if not ENABLE_FOLLOWER_AGGREGATION:
        return None  # 🟥 合规默认关·待元东方拍板
    if not creator_authorized:
        return None  # 未授权分析自己粉丝 → 不做
    # … 实现时：拉粉丝列表 → 聚合性别/年龄/地域分布 → 只回聚合·个体即丢弃
    #    标 source='self_inferred'（→ 🟥 自建推断·非官方）
    return None
