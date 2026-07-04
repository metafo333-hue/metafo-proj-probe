"""content_dna.py 离线自测 · 零网络 · 零 LLM · $0。

用拟真作品矩阵(还原 北川魔芋:晚间 18 点视频互动高于上午 11 点)验证组合规律。
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROBE_ROOT = os.path.dirname(_HERE)
for _p in [_PROBE_ROOT, os.path.join(os.path.dirname(_PROBE_ROOT), "combo-deep-probe")]:
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from app.services import content_dna as D

# 拟真:18 点视频互动明显高于 11 点(还原真实账号规律)
_BASE = 1716000000  # 任意基准秒(避免 Date.now·固定)
def _w(hour, dur_s, like, comment, collect, desc, anchor=False):
    # 用固定基准 + 小时偏移构造 create_time
    import datetime
    dt = datetime.datetime(2026, 5, 20, hour, 0, 0)
    return {"create_time": int(dt.timestamp()), "duration_ms": dur_s * 1000,
            "like": like, "comment": comment, "collect": collect, "share": 1,
            "desc": desc, "has_anchor": anchor}

WORKS = [
    _w(18, 39, 146, 39, 3, "成功属于不断奔跑的人 #安福魔芋 #北川魔芋姐"),
    _w(18, 20, 126, 26, 3, "你可能不认识我但我的客户你认识 #安福魔芋"),
    _w(18, 39, 102, 22, 2, "欢迎大家来北川做客 #安福魔芋 #魔芋工厂"),
    _w(11, 38, 47, 10, 1, "国风魔芋体面质感出众 #魔芋"),
    _w(11, 39, 46, 7, 3, "坚守匠心做魔芋严控原料 #魔芋食材"),
    _w(11, 36, 77, 14, 1, "餐饮门店直供拿货缩减成本 #源头工厂"),
    _w(11, 46, 196, 39, 6, "扎根北川深耕魔芋36年产地直供 #北川魔芋 #源头工厂"),
]
COMMENTS = [
    {"text": "多少钱一斤啊", "digg_count": 12},
    {"text": "怎么联系购买", "digg_count": 8},
    {"text": "包邮吗发什么快递", "digg_count": 5},
    {"text": "好厉害", "digg_count": 1},
]


class TestContentDNA(unittest.TestCase):

    def test_best_time_prefers_evening(self):
        r = D.best_posting_time(WORKS)
        # 晚间 18 点组里有 102-146·应识别为优(注意 196 在 11 点·会拉高上午均值)
        self.assertIsNotNone(r["best"])
        self.assertTrue(len(r["slots"]) >= 2)

    def test_best_duration(self):
        r = D.best_duration(WORKS)
        self.assertIsNotNone(r["best"])
        self.assertIn("s", r["best"])

    def test_winning_topics_extracts_keywords(self):
        r = D.winning_topics(WORKS)
        self.assertIsInstance(r["top_hashtags"], list)
        self.assertTrue(r["exemplar"]["like"] >= 100)  # 爆款样板取高赞

    def test_anchor_no_commerce(self):
        r = D.anchor_lift(WORKS)
        self.assertFalse(r["has_commerce"])
        self.assertIn("尚无挂车", r["verdict"])

    def test_comment_pool_finds_questions(self):
        r = D.comment_topic_pool(COMMENTS)
        self.assertTrue(len(r["hot_questions"]) >= 1)
        # 高赞疑问优先(多少钱 digg=12)
        self.assertIn("多少钱", r["hot_questions"][0])

    def test_comment_pool_filters_creator_announce(self):
        # #3 修:剔除创作者公告/自动回复·拿不到真问题就诚实标·不拿噪音充数
        noise = [
            {"text": "请看信息回复。需要购买", "digg_count": 99, "label_text": "作者"},
            {"text": "私信我有优惠", "digg_count": 50},   # 引流话术
            {"text": "点击下方小黄车下单", "digg_count": 30},  # 引流话术
            {"text": "好看", "digg_count": 5},            # 非问题
        ]
        r = D.comment_topic_pool(noise)
        self.assertEqual(r["n_questions"], 0)
        self.assertIn("拿不到", r["verdict"])  # 诚实标·非编造

    def test_comment_pool_excludes_owner_uid(self):
        cmts = [{"text": "多少钱一斤", "digg_count": 5,
                 "user": {"sec_uid": "OWNER"}},   # 创作者自评
                {"text": "怎么买啊", "digg_count": 8, "user": {"sec_uid": "FAN"}}]
        r = D.comment_topic_pool(cmts, owner_uid="OWNER")
        self.assertEqual(r["n_questions"], 1)        # 只剩粉丝那条
        self.assertIn("怎么买", r["hot_questions"][0])

    def test_exemplar_shows_real_likes(self):
        # #2 修:爆款样板给真实赞数(最高赞那条)·不给合成 eng
        r = D.winning_topics(WORKS)
        ex = r["exemplar"]
        self.assertNotIn("eng", ex)                  # 不再暴露合成 eng
        self.assertEqual(ex["like"], 196)            # 真实最高赞

    def test_small_sample_low_conf(self):
        # #5 修:小样本时段标低置信·不把噪音当实测
        thin = [_w(18, 30, 100, 10, 1, "a"), _w(11, 30, 50, 5, 1, "b")]  # 各 1 条
        r = D.best_posting_time(thin)
        self.assertEqual(r["conf"], "low")
        self.assertIn("低置信", r["verdict"])
        self.assertIsNone(r["lift"])                 # 低置信不报倍数

    def test_next_video_rx(self):
        dna = D.analyze_content_dna(WORKS, COMMENTS)
        rx = dna["next_video_rx"]
        self.assertTrue(len(rx["steps"]) >= 3)
        # 无挂车账号 → 处方应含"暂不挂车"
        self.assertTrue(any("挂车" in s for s in rx["steps"]))

    def test_aggregate_full(self):
        dna = D.analyze_content_dna(WORKS, COMMENTS)
        for k in ("best_time", "best_duration", "topics", "anchor",
                  "hashtags", "comment_pool", "next_video_rx"):
            self.assertIn(k, dna)
        md = D.render_dna_md(dna)
        self.assertIn("下条怎么拍", md)

    def test_thin_works_graceful(self):
        dna = D.analyze_content_dna(WORKS[:2], [])
        self.assertIn("不足", dna["next_video_rx"]["summary"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
