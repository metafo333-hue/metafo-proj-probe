"""mining_veins.py 离线自测 · 零网络 · $0。

矿脉②内容归因(哪个数据因子驱动互动) + 矿脉③口碑演化(评论时间线)。
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROBE_ROOT = os.path.dirname(_HERE)
for _p in [_PROBE_ROOT, os.path.join(os.path.dirname(_PROBE_ROOT), "combo-deep-probe")]:
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from app.services import mining_veins as MV

_BASE = 1716000000


def _w(day, dur_s, like, desc="", anchor=False, comment=0, collect=0):
    return {"create_time": _BASE + day * 86400, "duration_ms": dur_s * 1000,
            "like": like, "comment": comment, "collect": collect,
            "desc": desc, "has_anchor": anchor}


def _c(day, text, digg=0):
    return {"create_time": _BASE + day * 86400, "text": text, "digg_count": digg}


class TestAttribution(unittest.TestCase):

    def test_too_few(self):
        r = MV.content_attribution([_w(i, 30, 100) for i in range(4)])
        self.assertFalse(r["enough"])

    def test_duration_is_top_driver(self):
        # 60-90s 一律高互动·30s 一律低 → 时长应是首要驱动
        works = ([_w(i, 70, 300, "#a") for i in range(4)] +
                 [_w(i + 4, 30, 50, "#a") for i in range(4)])
        r = MV.content_attribution(works)
        self.assertTrue(r["enough"])
        self.assertEqual(r["top_driver"]["factor"], "时长")
        self.assertGreater(r["top_driver"]["spread"], 1.5)
        self.assertIn("时长", r["implication"])

    def test_anchor_factor(self):
        # 挂车视频互动低·无挂车高 → 挂载因子有落差
        works = ([_w(i, 40, 60, "#a", anchor=True) for i in range(3)] +
                 [_w(i + 3, 40, 200, "#a", anchor=False) for i in range(3)])
        r = MV.content_attribution(works)
        factors = [f["factor"] for f in r["factors"]]
        self.assertIn("挂载", factors)


class TestSentimentEvolution(unittest.TestCase):

    def test_too_few(self):
        r = MV.sentiment_evolution([_c(1, "好") for _ in range(4)])
        self.assertFalse(r["enough"])

    def test_intent_rising_warming(self):
        # 早期闲聊→近期问价(采购意向上升)→ 升温 + 产线索
        early = [_c(1, "好看"), _c(2, "厉害"), _c(3, "支持")]
        late = [_c(10, "多少钱一斤"), _c(11, "怎么拿货"), _c(12, "怎么联系购买")]
        r = MV.sentiment_evolution(early + late)
        self.assertTrue(r["enough"])
        self.assertGreater(r["intent_delta"], 0)
        self.assertIn("上升", r["intent_trend"])
        self.assertIn("线索", r["implication"])

    def test_cooling_negative(self):
        early = [_c(1, "好"), _c(2, "赞"), _c(3, "支持")]
        late = [_c(10, "太假了"), _c(11, "骗人的"), _c(12, "垃圾")]
        r = MV.sentiment_evolution(early + late)
        self.assertEqual(r["verdict"], "口碑降温")

    def test_honest_scope_note(self):
        r = MV.sentiment_evolution([_c(i, "多少钱") for i in range(6)])
        self.assertIn("本视频评论时间线", r["note"])
        self.assertIn("账号级跨作品", r["note"])     # 诚实标范围


if __name__ == "__main__":
    unittest.main(verbosity=2)
