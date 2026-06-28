"""cut_director.py + gallery.py + 阶段1航向 离线自测 · 零网络 · $0。"""
import os
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROBE_ROOT = os.path.dirname(_HERE)
for _p in [_PROBE_ROOT, os.path.join(os.path.dirname(_PROBE_ROOT), "combo-deep-probe")]:
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from app.services import cut_director as CD
from app.services import deep_analysis as DA
from app.services import composite_scores as CS

ACCT = {
    "nickname": "北川魔芋姐", "follower": 4658, "max_follower": 4660,
    "avg_like": 105, "commerce_density": 0.0, "vertical_score": 0.7,
    "industry_tag": "魔芋工厂",
    "engagement_structure": {"comment_per_like": 0.235, "nature": "争议型(高评论)"},
    "content_dna": {
        "topics": {"top_hashtags": ["源头工厂", "北川魔芋", "餐饮食材"],
                   "exemplar": {"desc": "产地直供多少钱"}},
        "best_time": {"best": "晚间18-22", "verdict": "晚间最好·高1.7x"},
        "best_duration": {"best": "60-90s"},
        "next_video_rx": {"steps": ["晚18-22发", "60-90s", "暂不挂车"]}},
    "milestone": {"current": "已过1000", "next": {"at": 5000, "gap": 342, "pct": 93.2,
                  "unlock": "接商单起步线", "verdict": "距5000差342粉"}},
}


class TestCutDirector(unittest.TestCase):

    def setUp(self):
        self.scores = CS.compute_all(ACCT, None)
        self.deep = DA.build_deep(ACCT, None, self.scores)
        self.rx = CD.build_prescription(ACCT, self.deep)

    def test_dual_layer(self):
        self.assertIn("front", self.rx)
        self.assertIn("cut_commands", self.rx)
        f = self.rx["front"]
        for k in ("strategy", "tactic", "execute"):  # 三级层级
            self.assertIn(k, f)

    def test_cut_commands_executable(self):
        nc = self.rx["cut_commands"]["next_clip"]
        self.assertEqual(nc["post_window"], "18:00-22:00")    # 时段→时间窗
        self.assertEqual(nc["duration_s"], [60, 90])          # 时长→区间
        self.assertIn("源头工厂", nc["topic_tags"])
        self.assertEqual(self.rx["cut_commands"]["engine"], "metacut")

    def test_b2b_hook_and_cta(self):
        nc = self.rx["cut_commands"]["next_clip"]
        # desc含"多少钱"→price_reveal钩子
        self.assertEqual(nc["hook"], "price_reveal")
        self.assertIn("私域", nc["cta"])                      # B端导私域

    def test_rationale_traceable(self):
        self.assertTrue(self.rx["cut_commands"]["rationale"])  # 可溯源


class TestGrowthHeading(unittest.TestCase):

    def test_three_segments(self):
        scores = CS.compute_all(ACCT, None)
        h = DA.growth_heading(ACCT, scores)
        for k in ("now", "direction", "endstate", "logic"):
            self.assertIn(k, h)
            self.assertTrue(h[k])
        self.assertIn("源头", h["endstate"])     # B端终态=源头供应IP


class TestGallery(unittest.TestCase):

    def test_register_and_compare(self):
        from app.services import gallery
        with tempfile.TemporaryDirectory() as td:
            os.environ["METABOARD_GALLERY_DIR"] = td
            try:
                board = {"ladders": {"l1": {"heading": {"now": "S档B端·起号期·4658粉"}},
                                     "l3": {"conclusion": "补私域承接"},
                                     "l4": {"stage": "平台期"}},
                         "raw": {"scores": {"c1": {"score": 39}, "c7": {"grade": "D"}}}}
                r = gallery.register(ACCT, board, "<html>报告</html>")
                self.assertIsNotNone(r)
                self.assertEqual(r["count"], 1)
                # gallery.html + index 生成
                self.assertTrue(os.path.exists(os.path.join(td, "gallery.html")))
                self.assertTrue(os.path.exists(os.path.join(td, "gallery-index.json")))
                # 第二个账号 → 对比表 2 行
                acct2 = dict(ACCT); acct2["nickname"] = "另一个号"
                r2 = gallery.register(acct2, board, "<html>2</html>")
                self.assertEqual(r2["count"], 2)
                gh = open(os.path.join(td, "gallery.html")).read()
                self.assertIn("北川魔芋姐", gh)
                self.assertIn("另一个号", gh)
            finally:
                os.environ.pop("METABOARD_GALLERY_DIR", None)


if __name__ == "__main__":
    unittest.main(verbosity=2)
