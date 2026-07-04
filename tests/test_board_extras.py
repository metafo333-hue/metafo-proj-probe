"""board_extras.py 离线自测 · 零网络 · $0。

补全"采了没接 board"的数据:热评/里程碑/聚类/互动异常。
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROBE_ROOT = os.path.dirname(_HERE)
for _p in [_PROBE_ROOT, os.path.join(os.path.dirname(_PROBE_ROOT), "combo-deep-probe")]:
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from app.services import board_extras as BE


class TestMilestone(unittest.TestCase):
    def test_next_milestone_distance(self):
        m = BE.milestone(4658)
        self.assertEqual(m["next"]["at"], 5000)
        self.assertEqual(m["next"]["gap"], 342)
        self.assertIn("商单起步", m["next"]["unlock"])

    def test_passed(self):
        m = BE.milestone(4658)
        self.assertEqual(m["passed_count"], 1)   # 过了1000
        self.assertIn("已过", m["current"])

    def test_top_account(self):
        m = BE.milestone(2_000_000)
        self.assertIsNone(m["next"])             # 顶格无下一档


class TestHotComments(unittest.TestCase):
    def test_sorted_by_digg(self):
        cs = [{"text": "便宜", "digg_count": 2}, {"text": "多少钱", "digg_count": 50},
              {"text": "好", "digg_count": 5}]
        r = BE.hot_comments(cs)
        self.assertTrue(r["enough"])
        self.assertEqual(r["top"][0]["text"], "多少钱")   # 最高赞在前

    def test_excludes_creator(self):
        cs = [{"text": "感谢支持", "digg_count": 99, "label_text": "作者"},
              {"text": "多少钱", "digg_count": 10}]
        r = BE.hot_comments(cs)
        self.assertEqual(r["top"][0]["text"], "多少钱")   # 作者评论被剔


class TestClusters(unittest.TestCase):
    def test_cluster_questions(self):
        cs = [{"text": "多少钱一斤"}, {"text": "多少钱一份"}, {"text": "怎么购买"}]
        r = BE.comment_clusters(cs)
        self.assertTrue(r["enough"])
        # "多少钱" 前缀聚成一类(count=2)
        themes = {c["theme"]: c["count"] for c in r["clusters"]}
        self.assertTrue(any(v >= 2 for v in themes.values()))


class TestAnomaly(unittest.TestCase):
    def _w(self, like, comment):
        return {"like": like, "comment": comment, "collect": 1, "share": 1}

    def test_natural(self):
        # 赞评比例一致 → 自然
        works = [self._w(100, 20) for _ in range(6)]
        r = BE.engagement_anomaly(works)
        self.assertEqual(r["level"], "green")

    def test_spike_anomaly(self):
        # 5条正常(100赞20评)+ 2条赞暴涨评论不动(1000赞2评)→ 疑刷
        works = [self._w(100, 20) for _ in range(5)] + [self._w(1000, 2) for _ in range(2)]
        r = BE.engagement_anomaly(works)
        self.assertIn(r["level"], ("yellow", "red"))
        self.assertTrue(r["flagged"])

    def test_honest_no_play(self):
        works = [self._w(100, 20) for _ in range(6)]
        r = BE.engagement_anomaly(works)
        self.assertIn("真play", r["note"])    # 诚实标:刷播放做不了


if __name__ == "__main__":
    unittest.main(verbosity=2)
