"""InsightPacket 接收契约单测 · 指针非桥物理保证（只接洞察不接原片）。

可 pytest 跑，也可 `python tests/test_insight.py` 直接跑。
核心验证：干净洞察接收 · 携带原始媒体字段物理拒收 · 嵌套禁字段也拦。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.schemas.insight import InsightPacket, from_ingest, reject_forbidden  # noqa: E402


def test_clean_packet_accepted():
    clean = {
        "insight_id": "ins-abc123", "platform": "wechat_channels",
        "topic_tags": ["国风", "助眠"], "sentiment": "pos",
        "key_claims": ["该内容主打治愈情绪", "完播率估算偏高"],
        "metrics": {"like_est": "高", "duration_band": "30-60s"},
        "quality_tier": "B", "collected_date": "2026-06-18",
    }
    p, err = from_ingest(clean)
    assert p is not None and err == ""
    assert p.insight_id == "ins-abc123" and p.platform == "wechat_channels"
    assert "国风" in p.topic_tags


def test_forbidden_video_url_rejected():
    # 携带原始媒体引用 → 物理拒收（原片进不了商业链）
    p, err = from_ingest({"insight_id": "x", "video_url": "https://weixin.qq.com/sph/AD16"})
    assert p is None and "video_url" in err


def test_forbidden_account_id_rejected():
    p, err = from_ingest({"insight_id": "x", "account_id": "gh_xxx", "sec_uid": "MS4w"})
    assert p is None
    assert "account_id" in err or "sec_uid" in err


def test_forbidden_nested_rejected():
    # 嵌套一层的禁字段也拦
    p, err = from_ingest({"insight_id": "x", "metrics": {"raw_video": "/path/x.mp4"}})
    assert p is None and "metrics.raw_video" in err


def test_missing_insight_id():
    p, err = from_ingest({"platform": "x"})
    assert p is None and "insight_id" in err


def test_strips_unknown_fields():
    # 未知字段被 strip（不报错·只保留 schema 字段·防注入）
    p, err = from_ingest({"insight_id": "x", "platform": "y", "extra_junk": "z"})
    assert p is not None and not hasattr(p, "extra_junk")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        passed += 1
        print(f"  PASS {fn.__name__}")
    print(f"\n{passed}/{len(fns)} InsightPacket 契约单测通过（指针非桥物理保证）")
