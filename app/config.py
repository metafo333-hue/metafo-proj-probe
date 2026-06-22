"""probe 配置 · 环境变量（不硬编码凭据）。"""
from __future__ import annotations

import os

# 母体对接
MOTHER_BASE = os.getenv("PROBE_MOTHER_BASE", "https://metafoclaw.com")
MOTHER_VERIFY_URL = os.getenv(
    "PROBE_MOTHER_VERIFY_URL", "https://metafoclaw.com/api/v1/identity/verify")
API_KEY = os.getenv("PROBE_API_KEY", "")  # 母体下发的项目长效 key（vault 注入）

# 身份/域
SUBDOMAIN = "probe"
PUBLIC_BASE = os.getenv("PROBE_PUBLIC_BASE", "https://probe.metafoclaw.com")
COOKIE_DOMAIN = ".metafoclaw.com"

# 存储
STORAGE_DIR = os.getenv("PROBE_STORAGE_DIR", "/tmp/probe-storage")
RESULT_TTL_HOURS = int(os.getenv("PROBE_RESULT_TTL_HOURS", "24"))

# PG（probe-a 本机 probe_collect · 成本明细 metering 落库 · 未配置则 metering 回落 JSONL）
PG_DSN = os.getenv("PROBE_PG_DSN", "")

# 八闸真模型策略（生产默认 live·护城河"对抗证伪"真跑而非中性桩）
#   优先级见 audit/backends.get_backend：GATES_LIVE_MODEL=1 > PROBE_LITELLM_KEY >
#   PROBE_AUDIT_DEFAULT_LIVE=1+国产key兜底(DEEPSEEK/BAILIAN) > stub
#   生产(probe-a)建议设 PROBE_AUDIT_DEFAULT_LIVE=1·无 ufo2 proxy 也用国产模型真跑
AUDIT_DEFAULT_LIVE = os.getenv("PROBE_AUDIT_DEFAULT_LIVE", "0") == "1"

# 契约
CONTRACT_VERSION = "1"
