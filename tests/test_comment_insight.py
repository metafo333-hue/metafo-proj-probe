"""comment_insight 评论区洞察 · 离线测试 · 零网络 · 不真调 LLM($0)。

测:数据源接口可插拔(mock provider) / 样本门 20 条降级(防玄学) / 水军预过滤 /
行业意向词典命中 / 情感只给区间不给百分比 / LLM 失败降级 / 渲染降级。
LLM 全程 monkeypatch,不真调。
"""
import unittest

from app.services import comment_insight
from app.services.comment_insight import (
    CommentSource, load_comments, analyze_comments, render_comment_section,
    _prefilter, _count_intent, _parse_llm_json, INDUSTRY_INTENT_LEXICON,
)


# ── mock 数据源(灰度 feed 占位)──
class MockSource:
    """实现 CommentSource 接口的 mock provider(测可插拔)。"""
    def __init__(self, data):
        self.data = data

    def fetch(self, aweme_id, limit=200):
        return self.data[:limit]


class FailingSource:
    def fetch(self, aweme_id, limit=200):
        raise RuntimeError("源挂了")


def _mk(texts):
    return [{"text": t, "like": 1, "reply_count": 0, "create_time": None} for t in texts]


class TestSourceInterface(unittest.TestCase):
    def test_mock_source_is_protocol(self):
        self.assertIsInstance(MockSource([]), CommentSource)

    def test_load_via_provider(self):
        src = MockSource(_mk(["多少钱", "在哪买"]))
        got = load_comments(src, "aweme1")
        self.assertEqual(len(got), 2)

    def test_load_via_direct_list_no_source(self):
        got = load_comments(None, "aweme1", comments=_mk(["a", "b"]))
        self.assertEqual(len(got), 2)

    def test_load_no_source_no_comments_returns_none(self):
        self.assertIsNone(load_comments(None, "aweme1"))

    def test_load_failing_source_returns_none_not_raise(self):
        self.assertIsNone(load_comments(FailingSource(), "aweme1"))


class TestPrefilter(unittest.TestCase):
    def test_filters_spam_and_emoji_and_dup(self):
        comments = _mk([
            "加微信领福利",        # 引流
            "🔥🔥🔥",              # 纯表情
            "这个多少钱",          # 正常
            "这个多少钱",          # 重复(前缀同)
            "私我进群",            # 引流
            "在哪可以买到呢",      # 正常
        ])
        clean, dropped = _prefilter(comments)
        texts = [c["text"] for c in clean]
        self.assertIn("这个多少钱", texts)
        self.assertIn("在哪可以买到呢", texts)
        self.assertEqual(len(clean), 2)
        self.assertEqual(dropped, 4)


class TestSampleGate(unittest.TestCase):
    """防玄学最重要的硬闸:<20 条只定性,绝不出百分比/情感分布。"""
    def test_below_floor_no_percentage(self):
        comments = _mk(["多少钱"] * 3 + ["在哪买", "怎么报名"])  # 去重后样本极少
        res = analyze_comments(comments, industry="美食", use_llm=False)
        self.assertTrue(res["below_floor"])
        self.assertNotIn("sentiment", res)  # 不出情感分布
        md = render_comment_section(res)
        self.assertNotIn("%", md)  # 渲染也无百分比
        self.assertIn("不给比例", md)

    def test_above_floor_full_analysis(self):
        comments = _mk([f"评论内容第{i}条多少钱" for i in range(25)])
        res = analyze_comments(comments, industry="美食", use_llm=False)
        self.assertFalse(res["below_floor"])
        self.assertEqual(res["sample"], 25)


class TestIndustryLexicon(unittest.TestCase):
    def test_intent_hits_counted(self):
        comments = _mk(["人均多少", "几点关门", "能订位吗", "在哪", "随便聊聊"])
        hits = _count_intent(comments, INDUSTRY_INTENT_LEXICON["美食"]["intent"])
        self.assertIn("几点", hits)
        self.assertIn("订位", hits)
        self.assertGreaterEqual(hits.get("在哪", 0), 1)

    def test_industry_focus_applied(self):
        comments = _mk([f"第{i}条评论多少钱能约吗" for i in range(22)])
        res = analyze_comments(comments, industry="时尚美妆", use_llm=False)
        self.assertIn("预约", res["focus"] + res["advice_tmpl"])

    def test_unknown_industry_uses_generic(self):
        comments = _mk([f"第{i}条评论怎么买" for i in range(22)])
        res = analyze_comments(comments, industry="某不存在赛道", use_llm=False)
        self.assertEqual(res["focus"], "通用意向密度")


class TestLLMPathMocked(unittest.TestCase):
    """LLM 走 mock,验证:成功解析 / 情感剥百分比 / 失败降级。"""
    def setUp(self):
        self.comments = _mk([f"第{i}条评论多少钱有没有用" for i in range(25)])

    def test_llm_success_parsed(self):
        fake = ('{"sentiment":{"tone":"有顾虑","neg_themes":["太贵"]},'
                '"top_questions":[{"q":"多少钱","count":10}],'
                '"objections":["会不会没效果"],"competitor":["隔壁家"],"demand_gap":["能不能出基础版"]}')

        def fake_chat(messages, max_tokens=900):
            return fake

        orig = comment_insight._llm_analyze
        try:
            # monkeypatch llm._chat + is_available
            from app.services import llm
            llm_avail, llm_chat = llm.is_available, llm._chat
            llm.is_available = lambda: True
            llm._chat = fake_chat
            res = analyze_comments(self.comments, industry="知识科普", use_llm=True)
        finally:
            llm.is_available, llm._chat = llm_avail, llm_chat
        self.assertTrue(res["llm_used"])
        self.assertEqual(res["sentiment"]["tone"], "有顾虑")
        self.assertIn("隔壁家", res["competitor"])
        self.assertTrue(res["demand_gap"])

    def test_llm_percentage_stripped(self):
        """防玄学:模型违规返回精确百分比 → 被剥成定性。"""
        bad = '{"sentiment":{"tone":"负面 73%","neg_themes":[]},"top_questions":[],"objections":[]}'
        d = _parse_llm_json(bad)
        self.assertNotIn("%", d["sentiment"]["tone"])

    def test_llm_unavailable_degrades(self):
        """LLM 不可用 → 降级到规则兜底(意向计数仍出·标 degraded·不瞎编情感)。"""
        from app.services import llm
        orig = llm.is_available
        try:
            llm.is_available = lambda: False
            res = analyze_comments(self.comments, industry="美食", use_llm=True)
        finally:
            llm.is_available = orig
        self.assertFalse(res["llm_used"])
        self.assertTrue(res.get("llm_degraded"))
        self.assertIsNone(res["sentiment"])
        md = render_comment_section(res)
        self.assertIn("没瞎编", md)

    def test_llm_garbage_returns_none_then_degrade(self):
        from app.services import llm
        avail, chat = llm.is_available, llm._chat
        try:
            llm.is_available = lambda: True
            llm._chat = lambda m, max_tokens=900: "我无法分析"
            res = analyze_comments(self.comments, industry="美食", use_llm=True)
        finally:
            llm.is_available, llm._chat = avail, chat
        self.assertFalse(res["llm_used"])
        self.assertTrue(res.get("llm_degraded"))


class TestRender(unittest.TestCase):
    def test_render_none_on_empty(self):
        self.assertIsNone(render_comment_section(None))
        self.assertIsNone(analyze_comments(None, "美食"))

    def test_render_sample_bias_disclaimer(self):
        comments = _mk([f"第{i}条评论多少钱" for i in range(25)])
        res = analyze_comments(comments, industry="美食", use_llm=False)
        md = render_comment_section(res)
        self.assertIn("愿意发声", md)  # 样本偏差诚实声明
        self.assertIn("🟩", md)  # 意向计数标确定

    def test_persona_tone_in_render(self):
        comments = _mk([f"第{i}条评论在哪买多少钱" for i in range(25)])
        res = analyze_comments(comments, industry="美食", persona="实体店主", use_llm=False)
        md = render_comment_section(res)
        self.assertIn("潜在到店", md)


if __name__ == "__main__":
    unittest.main()
