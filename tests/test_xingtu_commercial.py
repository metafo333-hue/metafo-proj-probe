"""星图达人商业真值模块测试（渲染纯逻辑 + 降级路径·0 网络/0 扣费）。

fixture 取自 2026-06-22 真实端点返回结构（kol_service_price_v1 等）。
"""
import unittest

from app.services import xingtu_commercial as xc


_XINGTU_REAL = {
    "is_real": True, "kolid": "7437565615805562934",
    "prices": [{"desc": "1-20s视频", "price": 8200, "settlement": "固定价格"}],
    "cpm_range": ["2156", "3918"], "expect_vv": 380245,
    "cooperate_index": 75, "cooperate_rank_percent": 0.2137, "cp_index": 64,
    "industry_tags": ["美妆-面部洗护", "传媒资讯-其他传媒资讯"],
}
_FANS_REAL = {
    "is_real": True, "kolid": "7437565615805562934",
    "dimensions": [{"desc": "分布最多的3个省份广东(17%),江苏(6%),浙江(6%)",
                    "top": [("广东", 100), ("江苏", 60)]}],
}


class TestRender(unittest.TestCase):
    def test_render_xingtu_real(self):
        md = xc.render_xingtu_section(_XINGTU_REAL)
        self.assertIn("8,200", md)             # 报价千分位
        self.assertIn("CPM", md)
        self.assertIn("21.37%", md)            # rank_percent 0.2137 → 行业前 21.37%
        self.assertIn("美妆-面部洗护", md)
        self.assertIn("官方真值", md)            # 与"估算"区分

    def test_render_fans_real(self):
        md = xc.render_fans_portrait_section(_FANS_REAL)
        self.assertIn("广东", md)
        self.assertIn("星图官方", md)

    def test_render_none_returns_none(self):
        # 未开星图 → None 不渲染（不污染报告）
        self.assertIsNone(xc.render_xingtu_section(None))
        self.assertIsNone(xc.render_xingtu_section({"is_real": False}))
        self.assertIsNone(xc.render_fans_portrait_section(None))
        self.assertIsNone(xc.render_fans_portrait_section({"dimensions": []}))


class TestDegrade(unittest.TestCase):
    def test_no_kolid_degrades(self):
        # _get 全返回 None（未开星图/网络失败）→ fetch 降级 None
        orig = xc._get
        xc._get = lambda *a, **k: None
        try:
            self.assertIsNone(xc.resolve_kolid("sec_xxx", "key"))
            self.assertIsNone(xc.fetch_xingtu_commercial("sec_xxx", "key"))
            self.assertIsNone(xc.fetch_fans_portrait("sec_xxx", "key"))
        finally:
            xc._get = orig

    def test_kolid_but_empty_commercial_degrades(self):
        # 有 kolid 但商业端点全空 → 仍降级 None（避免空壳卡片）
        orig = xc._get
        xc._get = lambda ep, *a, **k: ({"id": "123"} if "kolid" in ep else {})
        try:
            self.assertIsNone(xc.fetch_xingtu_commercial("sec", "key", kolid="123"))
        finally:
            xc._get = orig


if __name__ == "__main__":
    unittest.main()
