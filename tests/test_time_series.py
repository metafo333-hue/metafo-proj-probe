"""time_series.py + build_ladders 离线自测 · 零网络 · $0。

验证单次采集的时序导数(互动斜率/阶段/下条预估)+ 价值阶梯重投。
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROBE_ROOT = os.path.dirname(_HERE)
for _p in [_PROBE_ROOT, os.path.join(os.path.dirname(_PROBE_ROOT), "combo-deep-probe")]:
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from app.services import time_series as TS

_BASE = 1716000000  # 固定基准秒(避免 Date.now)


def _w(day_offset, like, comment=0, collect=0):
    return {"create_time": _BASE + day_offset * 86400,
            "like": like, "comment": comment, "collect": collect}


class TestTimeSeries(unittest.TestCase):

    def test_too_few_samples(self):
        r = TS.analyze_time_series([_w(i, 100) for i in range(4)])
        self.assertFalse(r["enough"])
        self.assertIn("积累中", r["verdict"])

    def test_rising_trend(self):
        # 早期低(50)→近期高(150)·应判加速上升
        works = [_w(i, 50) for i in range(6)] + [_w(i + 6, 150) for i in range(6)]
        r = TS.analyze_time_series(works)
        self.assertTrue(r["enough"])
        self.assertEqual(r["stage"], "上升期")
        self.assertGreater(r["slope_pct"], 20)

    def test_declining_trend(self):
        # 早期高→近期低·衰退期
        works = [_w(i, 200) for i in range(6)] + [_w(i + 6, 60) for i in range(6)]
        r = TS.analyze_time_series(works)
        self.assertIn("衰退期", r["stage"])   # 可能带"(疑断更触发)"后缀
        self.assertLess(r["slope_pct"], -20)

    def test_next_estimate(self):
        works = [_w(i, 100 + i * 5) for i in range(12)]
        r = TS.analyze_time_series(works)
        self.assertIsNotNone(r["next_estimate"])
        self.assertIn("like_median", r["next_estimate"])
        self.assertIn("代理", r["next_estimate"]["note"])   # 诚实标 proxy

    def test_render_md(self):
        works = [_w(i, 50) for i in range(6)] + [_w(i + 6, 150) for i in range(6)]
        md = TS.render_ts_md(TS.analyze_time_series(works))
        self.assertIn("阶段", md)


class TestLadders(unittest.TestCase):

    def _board(self):
        from app.services import board as B, composite_scores as CS
        acct = {
            "nickname": "测试号", "follower": 4658, "max_follower": 4660,
            "avg_like": 105, "max_like": 383, "burst_ratio": 3.6,
            "vertical_score": 0.7, "commerce_density": 0.0,
            "engagement_structure": {"comment_per_like": 0.235, "collect_per_like": 0.036,
                                     "nature": "争议型(高评论)"},
            "industry_tag": "魔芋工厂",
            "content_dna": {"topics": {"top_hashtags": ["魔芋工厂", "餐饮食材"]},
                            "next_video_rx": {"summary": "x", "steps": ["晚18-22发", "60-90s", "暂不挂车"]}},
            "time_series": TS.analyze_time_series(
                [_w(i, 50) for i in range(6)] + [_w(i + 6, 150) for i in range(6)]),
        }
        s = CS.compute_all(acct, None)
        c = {"churn": {"title": "掉粉", "severity": "green", "advice": "x"},
             "pricing": {"title": "报价", "severity": "yellow"},
             "track": {"title": "赛道", "severity": "green"}}
        return B.build_board(acct, None, scores=s, cards=c)

    def test_four_ladders_present(self):
        b = self._board()
        L = b["ladders"]
        for k in ("l1", "l2", "l3", "l4"):
            self.assertIn(k, L)
            self.assertIn("conclusion", L[k])
            self.assertIn("question", L[k])

    def test_ladder_order_and_moat(self):
        L = self._board()["ladders"]
        self.assertEqual(L["l1"]["name"], "定位航向")   # point6:升级为定位+航向
        self.assertEqual(L["l4"]["name"], "预测")
        self.assertIn("竞品", L["l3"]["moat"])      # 处方=竞品做不到

    def test_ladder4_has_prediction(self):
        L = self._board()["ladders"]
        self.assertTrue(L["l4"]["enough"])           # 12条样本→可预测
        self.assertEqual(L["l4"]["stage"], "上升期")

    def test_ladder_render_html(self):
        from app.services import board_render as R
        html = R.render_ladder_html(self._board())
        self.assertTrue(html.startswith("<!DOCTYPE html>"))
        self.assertIn("一眼答案", html)
        self.assertIn("阶梯4", html)
        self.assertIn("定位航向", html)
        self.assertIn("预测", html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
