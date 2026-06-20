"""脊柱意图轴枚举 · probe 单仓自包含（契约消费方为权威）。

为什么单仓不跨仓共享：`packages/shared` 是 JS 包（@mfc/shared·无 Python import 机制），
设计原案"落 shared 共享"工程不通。改为 probe 自定义枚举 = 字符串校验真源；
ask 侧映射器只输出**约定字符串值**（"diagnose"/"D"/...），不 import 本文件。
probe 入口（ProbeBrief.from_request）用本文件的 coerce_* 把字符串校验转枚举。
→ 两仓零文件共享，靠"字符串契约 + probe 端校验"防漂移（绕开跨仓 Python 共享隘口）。
"""
from __future__ import annotations
from enum import Enum


class IntentEnum(str, Enum):
    """5 意图（ask 识别的心理动作）。"""
    explore = "explore"      # 探索·最模糊·ask 须追问收敛
    diagnose = "diagnose"    # 诊断
    compare = "compare"      # 对比（选号合作/找对标）
    ideate = "ideate"        # 构思（不知做什么）
    amplify = "amplify"      # 放大（放大自己的真东西）


class PathEnum(str, Enum):
    """4 路径（probe 处理器·收敛后执行通道·可扩展）。"""
    A = "A"  # 原创放大
    B = "B"  # 二创借鉴
    C = "C"  # 选题灵感
    D = "D"  # 对标诊断


class DecisionEnum(str, Enum):
    """决策类型（反向定采集预算）。"""
    go_no_go = "go_no_go"        # 判断合作（高 blast·必拉竞品圈）
    self_review = "self_review"  # 复盘自己（只自身 2 圈）
    find_target = "find_target"  # 找目标
    create = "create"            # 求灵感（触发发现层）


# 漂移检测指纹：ask/probe 两侧任一改枚举须同步更新此串（CI 比对真源）
ENUM_FINGERPRINT = "intent5:path4:decision4:v1"


def coerce_intent(v, default: IntentEnum = IntentEnum.explore) -> IntentEnum:
    """字符串 → IntentEnum，非法值降级到安全默认（脊柱不因脏输入崩）。"""
    try:
        return IntentEnum(v)
    except (ValueError, KeyError):
        return default


def coerce_path(v, default: PathEnum = PathEnum.A) -> PathEnum:
    try:
        return PathEnum(v)
    except (ValueError, KeyError):
        return default


def coerce_decision(v, default: DecisionEnum = DecisionEnum.self_review) -> DecisionEnum:
    try:
        return DecisionEnum(v)
    except (ValueError, KeyError):
        return default
