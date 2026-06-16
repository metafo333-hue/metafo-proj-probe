"""account_report v2 确定性报告生成器 · 离线 · @芊妤真数据 fixture · $0 · 零网络。"""
import unittest

from app.services.account_report import build_report

QIANYU_V = {"title": "是全心全意陪伴孩子，还是花80%在工作上呢？ #孩子事业到底应该怎么选",
            "like": 8, "comment": 2, "share": 1, "collect": 0, "duration_s": 58}
QIANYU_A = {"nickname": "芊妤不是芊妤", "follower": 277, "aweme_count": 19, "works_analyzed": 16,
            "signature": "🔥有一种英雄主义，依然选择热爱生活，珍惜生命。",
            "avg_like": 10, "max_like": 52, "burst_ratio": 4.7, "vertical_score": 0.5,
            "hashtags": ["女性智慧", "女性力量", "努力成为更好的自己", "感情共鸣", "生活感悟"]}
AUDIT = {"source_reliability": "C", "confidence_level": "Low", "evidence_strength": "Weak"}


class TestAccountReport(unittest.TestCase):
    def test_has_all_sections(self):
        r = build_report(QIANYU_V, QIANYU_A, AUDIT)
        for must in ("账号诊断报告", "一句话先说重点", "你现在是什么情况",
                     "最该解决", "优势", "具体怎么做", "接下来会怎样", "可信"):
            self.assertIn(must, r, f"报告缺段:{must}")

    def test_plain_language_no_raw_jargon(self):
        # 说人话:不能直接甩"垂直度0.5/爆款比"等术语给用户看
        r = build_report(QIANYU_V, QIANYU_A, AUDIT)
        self.assertNotIn("垂直度 0.5", r)   # 已翻译成"太杂"
        self.assertIn("太杂", r)
        self.assertIn("和你平时差不多", r)  # 8赞 vs 均值10 → 大白话

    def test_uses_real_specifics(self):
        # 价值感:引用真实标签/数字,像真看了她的号
        r = build_report(QIANYU_V, QIANYU_A, AUDIT)
        self.assertIn("女性智慧", r)        # 真实标签
        self.assertIn("52", r)              # 自己的爆款样本

    def test_anti_copy_value(self):
        self.assertIn("比抄别人靠谱", build_report(QIANYU_V, QIANYU_A, AUDIT))

    def test_honesty(self):
        r = build_report(QIANYU_V, QIANYU_A, AUDIT)
        self.assertIn("绝不瞎编", r)
        self.assertIn("只看了你一个号", r)
        self.assertIn("真实公开数据", r)


if __name__ == "__main__":
    unittest.main()
