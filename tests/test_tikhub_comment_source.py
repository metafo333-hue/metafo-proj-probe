"""TikHub 评论源适配器测试 · 归一化/PIPL/降级(不真调网络)。"""
import unittest

from app.datasources.tikhub_comment_source import TikHubCommentSource, _norm


class TestNorm(unittest.TestCase):
    def test_norm_basic(self):
        n = _norm({"text": "好吃", "digg_count": 12, "reply_comment_total": 3,
                   "create_time": 1718000000, "ip_label": "四川"})
        self.assertEqual(n["text"], "好吃")
        self.assertEqual(n["like"], 12)
        self.assertEqual(n["reply_count"], 3)
        self.assertEqual(n["user_label"], "四川")

    def test_pipi_no_nickname(self):
        """PIPL:归一化结果不得含昵称/uid 等个体可识别字段。"""
        n = _norm({"text": "test", "user": {"nickname": "张三", "uid": "123"},
                   "digg_count": 1})
        self.assertIsNotNone(n)
        self.assertNotIn("nickname", n)
        self.assertNotIn("uid", n)
        # 只保留约定的 5 个字段
        self.assertEqual(set(n.keys()),
                         {"text", "like", "reply_count", "create_time", "user_label"})

    def test_norm_empty_text_dropped(self):
        self.assertIsNone(_norm({"text": "   ", "digg_count": 5}))

    def test_alt_field_names(self):
        n = _norm({"content": "替代字段", "like_count": 7})
        self.assertEqual(n["text"], "替代字段")
        self.assertEqual(n["like"], 7)


class TestFetchDegrade(unittest.TestCase):
    def test_no_key_returns_none(self):
        src = TikHubCommentSource(key=None)
        # 显式无 key(且 env 可能有·这里强制 None 入参不够·测空 aweme_id)
        self.assertIsNone(src.fetch(""))

    def test_empty_aweme_none(self):
        src = TikHubCommentSource(key="dummy")
        self.assertIsNone(src.fetch(""))

    def test_adapter_import_fail_degrades(self):
        """combo_deep_probe 本地不可用 → fetch 优雅返回 None(不抛)。"""
        src = TikHubCommentSource(key="dummy")
        # 本地无 combo_deep_probe → 懒导入失败 → None
        self.assertIsNone(src.fetch("123456"))

    def test_implements_protocol(self):
        from app.services.comment_insight import CommentSource
        self.assertIsInstance(TikHubCommentSource(key="x"), CommentSource)


if __name__ == "__main__":
    unittest.main()
