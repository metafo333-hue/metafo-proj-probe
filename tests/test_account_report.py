"""account_report 确定性报告生成器 · 离线 · @芊妤真数据 fixture · $0 · 零网络。"""
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
        for must in ("综合分析报告", "一句话结论", "满足你问的", "高于你期望", "创作处方", "数据可信度"):
            self.assertIn(must, r, f"报告缺段:{must}")

    def test_multidim_reference(self):
        r = build_report(QIANYU_V, QIANYU_A, AUDIT)
        self.assertIn("0.73", r)        # 8/(10+1)≈0.73 倍
        self.assertIn("账号常态", r)
        self.assertIn("52", r)          # 自己的爆款样本

    def test_anti_copy_value(self):
        # 价值对齐北极星:处方是"放大你的真东西",不是教抄
        self.assertIn("不抄别人", build_report(QIANYU_V, QIANYU_A, AUDIT))

    def test_honesty_blackbox_and_singlesource(self):
        r = build_report(QIANYU_V, QIANYU_A, AUDIT)
        self.assertIn("不编", r)         # 黑盒维诚实标(不冒充)
        self.assertIn("单一来源", r)     # 单源诚实

    def test_satisfy_plus_exceed(self):
        r = build_report(QIANYU_V, QIANYU_A, AUDIT)
        self.assertIn("满足", r)
        self.assertIn("未来可能发生", r)  # 高于期望层


if __name__ == "__main__":
    unittest.main()
