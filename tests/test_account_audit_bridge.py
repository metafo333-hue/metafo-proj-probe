"""黄金契约测试 · ②→③ 转换器(account_audit_bridge)。

机制级拦 Q6-L55(派生物不联动):pin 住转换器输出契约 + 证其输出 run_audit 原样可吃。
@Richard29 fixture(真账号量级·trace 实测) · 零网络 · StubBackend · $0 确定性。
"""
import unittest

from app.services.account_audit_bridge import account_to_claims_sources

# @Richard29(Richard_Lawrence·我的世界混剪)trace 实测量级
RICHARD = {
    "profile": {"nickname": "Richard_Lawrence", "unique_id": "Richard29",
                "follower_count": 57665, "total_favorited": 1234567, "aweme_count": 210},
    "diagnosis": {
        "like": {"avg": 6220, "max": 27392, "min": 12},
        "interaction_avg": {"like": 6220, "comment": 88, "collect": 120, "share": 45},
        "burst_ratio": 4.4,
        "top_hashtags": [["我的世界", 10]],
        "vertical_score": 1.0,
        "update": {"span_days": 30.0, "avg_interval_hours": 72.0},
        "like_per_follower": 0.108,
    },
    "works_analyzed": 10, "works_sample": [], "meta": {},
}
URL = "https://www.douyin.com/user/MS4wLjABAAAA_richard29"


class TestBridgeContract(unittest.TestCase):
    def test_contract_shape(self):
        claims, sources = account_to_claims_sources(RICHARD, URL)
        self.assertTrue(4 <= len(claims) <= 7, f"应 4-7 条原子 claim,实得 {len(claims)}")
        self.assertTrue(all(isinstance(c, str) and c for c in claims))
        self.assertEqual(len(sources), 1)
        s = sources[0]
        for k in ("url", "title", "text", "source_type", "reliability_hint", "timestamp"):
            self.assertIn(k, s, f"source 缺契约键 {k}")
        self.assertEqual(s["source_type"], "primary")
        self.assertEqual(s["reliability_hint"], "C")  # 单源诚实 Low

    def test_key_metrics_in_claims(self):
        claims, _ = account_to_claims_sources(RICHARD, URL)
        blob = " ".join(claims)
        self.assertIn("57665", blob)   # 体量
        self.assertIn("6220", blob)    # 均赞
        self.assertIn("4.4", blob)     # 爆款比

    def test_feeds_run_audit_offline(self):
        """证转换器输出 run_audit 原样可吃(regime B 端到端·StubBackend·$0)。"""
        from app.audit.gates import run_audit
        claims, sources = account_to_claims_sources(RICHARD, URL)
        verdict = run_audit(claims, sources, tier="free")
        self.assertIn("conclusion_label", verdict)
        self.assertTrue(verdict.get("gates_run"))

    def test_empty_account_graceful(self):
        claims, sources = account_to_claims_sources({}, URL)
        self.assertGreaterEqual(len(claims), 1)
        self.assertEqual(len(sources), 1)


if __name__ == "__main__":
    unittest.main()
