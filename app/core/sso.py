"""L1 §6 鉴权 + 跨子域 SSO · 校验母体下发的 short-lived user_token。

母体 identity 端点尚未就绪（api-core/routers/identity.py 为 TODO），故本层：
- 契约就绪：定义 Principal + verify() 接口，与 02-api.md §6 一致
- 远程校验预留：_verify_remote() 调母体 /api/v1/identity/verify（母体上线即切真）
- MVP 桩：无 token/anon → 匿名（仅免费档）；非空 token → 信任 billing_context.tier

铁律：probe 永不碰用户真凭据（穿透 R8/R1），只认母体短时 token。
"""
from __future__ import annotations

from typing import Any


class Principal:
    """调用主体。"""

    def __init__(self, user_id: str, tier: str, token: str | None):
        self.user_id = user_id
        self.tier = tier          # free | paid | member
        self.token = token

    @property
    def is_anonymous(self) -> bool:
        return self.user_id == "anon"

    @property
    def is_paid(self) -> bool:
        return self.tier in ("paid", "member")


def verify(user_token: str | None, billing_context: dict | None) -> Principal:
    """校验 user_token，返回 Principal。"""
    if not user_token or user_token == "anon":
        # 匿名（无 token）→ 最浅 public 深度层（仅公开结论）
        return Principal("anon", "anon", None)
    tier = (billing_context or {}).get("tier", "free")
    # 母体 identity 就绪后切此分支：
    #   info = _verify_remote(user_token)
    #   return Principal(info["user_id"], info["tier"], user_token)
    uid = _decode_stub(user_token)
    return Principal(uid, tier, user_token)


def _verify_remote(user_token: str) -> dict[str, Any]:  # pragma: no cover (母体未就绪)
    """调母体 identity 校验端点（预留 · 母体上线即启用）。"""
    import urllib.request
    import json
    from app import config
    req = urllib.request.Request(
        config.MOTHER_VERIFY_URL,
        headers={"Authorization": f"Bearer {config.API_KEY}",
                 "X-User-Token": user_token},
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())


def _decode_stub(token: str) -> str:
    """MVP 桩：从 token 派生稳定匿名化 user_id（不解析真凭据）。"""
    return f"u_{abs(hash(token)) % 10**8}"
