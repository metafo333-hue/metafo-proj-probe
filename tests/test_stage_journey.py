"""stage_journey.py 离线自测 · 零网络 · $0。

运营阶段旅程:已走/当前/接下来 + 进阶条件(赛道感知 B端/泛娱乐)。
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROBE_ROOT = os.path.dirname(_HERE)
for _p in [_PROBE_ROOT, os.path.join(os.path.dirname(_PROBE_ROOT), "combo-deep-probe")]:
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from app.services import stage_journey as SJ

# 北川:B端·4658粉·零承接 → 当前"起号·建信任"·已过"冷启"·下一站"初变现"
B2B = {"nickname": "北川魔芋姐", "follower": 4658, "commerce_density": 0.0,
       "vertical_score": 0.7, "industry_tag": "魔芋工厂"}
GEN = {"nickname": "搞笑日常", "follower": 3000, "industry_tag": "搞笑"}


class TestJourney(unittest.TestCase):

    def test_b2b_positioning(self):
        j = SJ.build_journey(B2B)
        self.assertTrue(j["is_b2b"])
        self.assertEqual(j["current"], "起号·建信任")
        self.assertIn("冷启·打标签", j["done"])        # 已走过
        self.assertEqual(j["next"], "初变现")           # 接下来

    def test_advance_gaps(self):
        # B端起号·零承接 → 进阶缺口含"私域承接"(硬条件)
        j = SJ.build_journey(B2B)
        self.assertTrue(j["advance_gaps"])
        self.assertTrue(any("承接" in g for g in j["advance_gaps"]))

    def test_nodes_states(self):
        j = SJ.build_journey(B2B)
        states = [n["state"] for n in j["nodes"]]
        self.assertIn("done", states)
        self.assertIn("current", states)
        self.assertIn("future", states)
        # 当前只有一个
        self.assertEqual(states.count("current"), 1)

    def test_b2b_vs_gen_different_stages(self):
        jb, jg = SJ.build_journey(B2B), SJ.build_journey(GEN)
        # B端 3000粉=起号(可变现阶段);泛娱乐 3000粉=冷启(禁变现)
        self.assertNotEqual(jb["current"], "冷启·打标签")   # B端已起号
        self.assertEqual(jg["current"], "冷启·打标签")       # 泛娱乐还冷启

    def test_verdict(self):
        j = SJ.build_journey(B2B)
        self.assertIn("起号", j["verdict"])
        self.assertIn("初变现", j["verdict"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
