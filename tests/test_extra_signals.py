"""extra_signals.py 离线自测 · 零网络 · $0。

用真实字段路径(2026-06-28 force_refresh 实测)构造拟真 results·验证:
  - 解析 8 个有数据端点(评论热词/竞品/热点/选题/配乐/粉丝分布)
  - 空返回诚实标(video_audience/danmaku 等)
  - 组合分析:采购意向识别·竞品雷达·大盘热点
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROBE_ROOT = os.path.dirname(_HERE)
for _p in [_PROBE_ROOT, os.path.join(os.path.dirname(_PROBE_ROOT), "combo-deep-probe")]:
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from app.services import extra_signals as ES

# 拟真 results(真实信封结构·北川魔芋实测路径)
RESULTS = {
    "comment_word": {"data": {"data": [
        {"word_seg": "魔芋", "value": 4}, {"word_seg": "拿货", "value": 2},
        {"word_seg": "美女", "value": 2}, {"word_seg": "花魔芋", "value": 1}]}},
    "related": {"data": {"aweme_list": [
        {"author": {"nickname": "竞品A", "follower_count": 12000},
         "statistics": {"digg_count": 300}, "desc": "魔芋工厂直供"},
        {"author": {"nickname": "竞品B", "follower_count": 3000},
         "statistics": {"digg_count": 50}, "desc": "魔芋美食"}]}},
    "hot_rise": {"data": {"data": {"objs": [
        {"sentence": "某上升热点", "hot_score": 9000}]}}},
    "hot_total": {"data": {"data": {"word_list": [
        {"word": "实时热搜词", "hot_value": 8000}]}}},
    "hot_challenge": {"data": {"data": {"objs": [
        {"sentence": "某挑战", "video_count": 1000, "hot_score": 7000}]}}},
    "insight_rec": {"data": [
        {"category": "美食", "title": "选题A"}, {"category": "三农", "title": "选题B"}]},
    "creator_music": {"data": {"item_list": [
        {"music": {"title": "热门BGM"}, "hot_involve_ratio": 0.8}]}},
    "acc_fans_portrait": {"data": {"data": {"option": "1", "portrait": {
        "portrait_data": [{"name": "1000~1999", "value": 0.3},
                          {"name": "2000~2999", "value": 0.24}]}}}},
    # 空返回
    "video_audience": {"data": {"code": 1, "message": "此作品超过可查看时间，暂无数据"}},
    "danmaku": {"danmaku_list": [], "total_count": 0},
}


class TestParse(unittest.TestCase):

    def setUp(self):
        self.ex = ES.parse_extra_signals(RESULTS)

    def test_official_comment_words(self):
        w = self.ex["official_comment_words"]
        self.assertEqual(w[0]["word"], "魔芋")
        self.assertTrue(any(x["word"] == "拿货" for x in w))  # 含采购意向词

    def test_related_competitors_sorted(self):
        c = self.ex["related_competitors"]
        self.assertEqual(c[0]["nickname"], "竞品A")   # 粉丝多的在前
        self.assertEqual(c[0]["fans"], 12000)

    def test_env_hot_parsed(self):
        self.assertTrue(self.ex.get("env_rising"))
        self.assertTrue(self.ex.get("env_hot_search"))
        self.assertTrue(self.ex.get("env_challenges"))

    def test_topic_insights(self):
        self.assertEqual(len(self.ex["topic_insights"]), 2)
        self.assertIn("美食", self.ex["topic_insight_cats"])

    def test_fan_distribution_honest_label(self):
        fd = self.ex["fan_distribution"]
        self.assertEqual(fd["dist"][0]["name"], "1000~1999")
        self.assertIn("待文档确认", fd["note"])     # 语义不明诚实标

    def test_empty_endpoints_flagged(self):
        empty_eps = [e for e, _ in self.ex["_empty"]]
        self.assertIn("video_audience", empty_eps)
        self.assertIn("danmaku", empty_eps)


class TestCombine(unittest.TestCase):

    def _acct(self):
        return {"follower": 4658, "extra_signals": ES.parse_extra_signals(RESULTS),
                "comment_deep": {"ip_concentration": 0.5},
                "fans_interest_accounts": [{"name": "同关号", "fans": 8000}]}

    def test_audience_detects_purchase_intent(self):
        d = ES.audience_deep(self._acct())
        # "拿货" 是采购意向 → intent_signal 命中 + implication 含"线索"
        self.assertIn("拿货", d["intent_signal"])
        self.assertIn("线索", d["implication"])

    def test_competitor_radar_merges_two_sources(self):
        d = ES.competitor_radar(self._acct())
        names = [c["name"] for c in d["competitors"]]
        self.assertIn("竞品A", names)        # 算法关联
        self.assertIn("同关号", names)        # 粉丝同关

    def test_env_hot_deep(self):
        d = ES.env_hot_deep(self._acct())
        self.assertTrue(d["rising_top"])
        self.assertIn("标签内", d["implication"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
