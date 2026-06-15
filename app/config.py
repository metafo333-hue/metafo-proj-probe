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

# 契约
CONTRACT_VERSION = "1"
