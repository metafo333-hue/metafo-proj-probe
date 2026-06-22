"""测 audit.lineage 数据血缘验证(断层2)· 纯逻辑 · 零网络 · stub 数据。

爬梯 L1/L2:验证量化结果的「担保等级/精度分布/过期/黑盒缺失」判定正确,不连真模型/真网络。
"""
import unittest
from datetime import datetime, timezone, timedelta

from app.audit import lineage


def _packet(exposure_precision="measured", ts=None, missing_bb=None, coverage=1.0):
    ts = ts or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    return {
        "dimensions": {
            "exposure": {
                "play_count": {"value": 10000, "source": "tikhub",
                               "precision": exposure_precision, "ts": ts},
            },
            "metadata": {
                "title": {"value": "x", "source": "tikhub", "precision": "measured", "ts": ts},
            },
        },
        "coverage_score": coverage,
        "missing_blackbox": missing_bb or [],
    }


class TestLineage(unittest.TestCase):
    def test_clean_high_grade(self):
        r = lineage.verify(_packet())
        self.assertEqual(r["lineage_grade"], "高")
        self.assertEqual(r["precision_mix"]["measured"], 2)
        self.assertEqual(r["stale_fields"], [])
        self.assertEqual(r["field_total"], 2)

    def test_estimated_lowers_grade(self):
        r = lineage.verify(_packet(exposure_precision="estimated", coverage=0.5))
        self.assertIn(r["lineage_grade"], ("中", "低"))
        self.assertEqual(r["precision_mix"]["estimated"], 1)

    def test_missing_blackbox_flagged(self):
        r = lineage.verify(_packet(missing_bb=["retention", "conversion"]))
        self.assertTrue(any("黑盒" in f for f in r["flags"]))
        self.assertEqual(r["missing_blackbox"], ["retention", "conversion"])

    def test_stale_data_flagged(self):
        old = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%dT%H:%M:%S")
        r = lineage.verify(_packet(ts=old))
        self.assertGreaterEqual(len(r["stale_fields"]), 1)
        self.assertTrue(any("重验" in f for f in r["flags"]))

    def test_empty_packet_low_grade(self):
        r = lineage.verify({"dimensions": {}, "coverage_score": 0.0})
        self.assertEqual(r["lineage_grade"], "低")
        self.assertEqual(r["field_total"], 0)


if __name__ == "__main__":
    unittest.main()
