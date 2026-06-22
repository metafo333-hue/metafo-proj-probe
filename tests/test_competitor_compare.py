"""competitor_compare L4 竞品圈 · 离线测试 · 零网络 · $0。

测确定性对比逻辑:排名/相对定位/无裸数字/领先 vs 落后处方/空竞品安全。
"""
import unittest

from app.services.competitor_compare import compare_accounts, _rank

TARGET = {"nickname": "北川魔芋姐", "follower": 4645, "avg_like": 105,
          "max_like": 383, "vertical_score": 0.7}
COMP_STRONG = {"nickname": "魔芋大王", "follower": 50000, "avg_like": 800,
               "max_like": 5000, "vertical_score": 0.9}
COMP_WEAK = {"nickname": "小魔芋", "follower": 800, "avg_like": 30,
             "max_like": 90, "vertical_score": 0.4}


class TestCompetitorCompare(unittest.TestCase):

    def test_empty_competitors_safe(self):
        self.assertEqual(compare_accounts(TARGET, []), "")
        self.assertEqual(compare_accounts(TARGET, None), "")

    def test_rank_helper(self):
        sv, rank = _rank([TARGET, COMP_STRONG, COMP_WEAK], "avg_like")
        self.assertEqual(sv[0][0], "魔芋大王")          # 均赞最高
        self.assertEqual(rank["北川魔芋姐"], 2)          # target 居中

    def test_compare_has_ranking(self):
        md = compare_accounts(TARGET, [COMP_STRONG, COMP_WEAK])
        self.assertIn("同行里你站在哪", md)
        self.assertIn("第 2", md)                       # 均赞排第2(强的在前)

    def test_compare_behind_points_to_leader(self):
        md = compare_accounts(TARGET, [COMP_STRONG])
        self.assertIn("魔芋大王", md)                    # 指出该学谁
        self.assertIn("倍", md)                          # 差距倍数(无裸数字)
        self.assertIn("补差距", md)

    def test_compare_target_leads(self):
        md = compare_accounts(COMP_STRONG, [TARGET, COMP_WEAK])  # 强号做 target
        self.assertIn("第 1", md)
        self.assertIn("领先", md)

    def test_no_naked_numbers_disclaimer(self):
        md = compare_accounts(TARGET, [COMP_STRONG])
        self.assertIn("相对参考", md)                    # 诚实:非全行业排名

    def test_filters_invalid_competitor(self):
        md = compare_accounts(TARGET, [COMP_STRONG, {}, {"x": 1}])  # 脏数据
        self.assertIn("1 个同类号", md)                  # 只算有效的1个


if __name__ == "__main__":
    unittest.main(verbosity=2)
