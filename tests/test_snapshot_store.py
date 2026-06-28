"""snapshot_store.py 离线自测 · 零网络 · $0。

验证跨快照轨迹(涨粉/互动/健康趋势)+ 历史不足诚实标。
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROBE_ROOT = os.path.dirname(_HERE)
for _p in [_PROBE_ROOT, os.path.join(os.path.dirname(_PROBE_ROOT), "combo-deep-probe")]:
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from app.services import snapshot_store as SS


def _snap(date, follower, avg_like=100, health=None):
    return {"date": date, "ts": date, "follower": follower,
            "avg_like": avg_like, "health": health}


class TestTrajectory(unittest.TestCase):

    def test_too_few(self):
        r = SS.trajectory([_snap("2026-06-21", 4645)])
        self.assertFalse(r["enough"])
        self.assertIn("积累中", r["verdict"])

    def test_real_beichuan_trajectory(self):
        # 还原北川魔芋真实历史:6天 4645→4658(+13·停滞)
        hist = [_snap("2026-06-21", 4645), _snap("2026-06-22", 4645),
                _snap("2026-06-27", 4658)]
        r = SS.trajectory(hist)
        self.assertTrue(r["enough"])
        self.assertEqual(r["follower_delta"], 13)
        self.assertEqual(r["span_days"], 6)
        self.assertIn("停滞", r["verdict"])      # 日增0.04%→平台期
        self.assertEqual(len(r["follower_path"]), 3)

    def test_rapid_growth(self):
        hist = [_snap("2026-06-01", 10000), _snap("2026-06-11", 15000)]
        r = SS.trajectory(hist)
        self.assertIn("涨粉", r["verdict"])
        self.assertEqual(r["follower_delta"], 5000)

    def test_churn(self):
        hist = [_snap("2026-06-01", 50000), _snap("2026-06-11", 45000)]
        r = SS.trajectory(hist)
        self.assertEqual(r["verdict"], "掉粉")
        self.assertLess(r["follower_delta"], 0)

    def test_like_and_health_trend(self):
        hist = [_snap("2026-06-01", 10000, avg_like=100, health=50),
                _snap("2026-06-11", 11000, avg_like=130, health=60)]
        r = SS.trajectory(hist)
        self.assertIn("均赞", r["like_trend"])
        self.assertIn("健康", r["health_trend"])

    def test_backfill_from_real_cases(self):
        # 真实回填:data/cases 里有北川历史 → load_history 应≥2(若环境有 case)
        hist = SS.load_history("北川魔芋姐｜赵娟")
        # 不强断条数(环境可能无 case)·但结构须正确
        self.assertIsInstance(hist, list)
        for h in hist:
            self.assertIn("date", h)


if __name__ == "__main__":
    unittest.main(verbosity=2)
