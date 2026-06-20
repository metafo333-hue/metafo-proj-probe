"""脊柱核心单测 · 枚举 / ProbeBrief.from_request / RouteDecider。

可 pytest 跑，也可 `python tests/test_spine.py` 直接跑（W4 stub 验收点）。
覆盖：枚举指纹·契约校验·脏输入降级·四路径裁剪·go_no_go 竞品圈铁律。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.schemas.probe_intent_enum import (  # noqa: E402
    IntentEnum, PathEnum, DecisionEnum, ENUM_FINGERPRINT,
)
from app.schemas.brief import ProbeBrief  # noqa: E402
from app.services.route import decide  # noqa: E402


class _P:  # stub principal
    def __init__(self, tier):
        self.tier = tier


def test_enum_fingerprint():
    assert len(IntentEnum) == 5 and len(PathEnum) == 4 and len(DecisionEnum) == 4
    assert ENUM_FINGERPRINT == "intent5:path4:decision4:v1"


def test_is_brief_request():
    assert ProbeBrief.is_brief_request({"contract_version": "probe-brief/v1"}) is True
    assert ProbeBrief.is_brief_request({"instruction": "旧裸dict"}) is False


def test_from_request_D_gonogo():
    req = {
        "contract_version": "probe-brief/v1",
        "intent": "diagnose", "path": "D", "decision": "go_no_go",
        "intent_confidence": 0.86,
        "subject": {"raw": "@Richard29", "kind": "account", "platform": "douyin"},
        "purpose": "判断值不值得投放", "tier": "paid",
        "implicit_needs": [{"value": "【推断】更在意ROI", "confidence": 0.6}],
    }
    b = ProbeBrief.from_request(req)
    assert b.intent == IntentEnum.diagnose and b.path == PathEnum.D
    assert b.decision == DecisionEnum.go_no_go and b.subject.platform == "douyin"
    assert b.implicit_needs[0].confidence == 0.6
    assert b.to_dict()["intent"] == "diagnose"  # 序列化回字符串可 JSON


def test_from_request_illegal_degrades():
    # 非法枚举值降级到安全默认·脊柱不崩（R0.8 健壮性）
    b = ProbeBrief.from_request({"intent": "xxx", "path": "Z", "decision": "??"})
    assert b.intent == IntentEnum.explore and b.path == PathEnum.A
    assert b.decision == DecisionEnum.self_review


def test_from_request_C_no_subject():
    # C 选题路径常无 subject
    b = ProbeBrief.from_request({"path": "C", "decision": "create"})
    assert b.subject is None and b.path == PathEnum.C


def test_route_D_gonogo_paid():
    b = ProbeBrief.from_request({"path": "D", "decision": "go_no_go"})
    rd = decide(b, _P("paid"))
    assert "competitor" in rd.circles
    assert rd.account_crosseval and "lineage_quant" in rd.verify_face
    assert rd.depth == "deep"


def test_route_gonogo_free_still_competitor():
    # go_no_go 铁律：即便免费档也必拉竞品圈（无裸数字）
    b = ProbeBrief.from_request({"path": "D", "decision": "go_no_go"})
    rd = decide(b, _P("free"))
    assert "competitor" in rd.circles


def test_route_self_review_no_competitor():
    b = ProbeBrief.from_request({"path": "A", "decision": "self_review"})
    rd = decide(b, _P("free"))
    assert "competitor" not in rd.circles
    assert rd.circles == ["account", "sibling"]


def test_route_C_discover_beyond():
    b = ProbeBrief.from_request({"path": "C", "decision": "create"})
    rd = decide(b, _P("free"))
    assert rd.circles == ["discover"]
    assert rd.report_sections.get("beyond") is True


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        passed += 1
        print(f"  PASS {fn.__name__}")
    print(f"\n{passed}/{len(fns)} 脊柱核心单测通过")
