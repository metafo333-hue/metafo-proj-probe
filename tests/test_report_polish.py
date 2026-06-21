"""report_polish 单元测试 · 离线 · $0 · 覆盖已发现并修复的 4 个护栏 bug。

测试策略:用 mock 替换 LLM API 调用 → 离线可跑 → 验证 polish_report 护栏逻辑正确。
mock 场景:各测试独立注入 LLM 响应,断言护栏的进/退/降级是否符合预期。
"""
import re
import unittest
from unittest.mock import patch, MagicMock
import json


def _make_mock_response(content: str):
    """构造 SiliconFlow 格式的 mock 响应。"""
    return json.dumps({
        "choices": [{"message": {"content": content}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 200}
    }).encode("utf-8")


class TestPolishGuards(unittest.TestCase):

    def setUp(self):
        # 基础原始报告(含所有护栏关键词·充当真实报告骨架)
        self.base_md = """# 📋 账号诊断报告 · @测试账号

## 一句话先说重点
**结论：这个账号潜力够，缺方向。**

## 一、你现在是什么情况
- 220000 个粉丝、52000 作品量测试数
- 你的视频平均 **38000 个赞**，最好的一条有 **790105 个赞**。

## 二、你这 10 条作品藏着的规律
规律：高赞内容集中在科普方向。比抄别人靠谱。

## 三、你现在最该解决的一件事
方向太散，专注已验证的内容。

## 四、这个号整体判断
成长期。

## 七、这份分析有多可信
数字全部公开真实，拿不到的我**绝不瞎编**。
"""

    def _call_polish(self, mock_content: str, base_md: str = None):
        """注入 mock LLM 响应 → 调用 polish_report → 返回结果。"""
        from app.services.report_polish import polish_report
        md = base_md or self.base_md
        raw_resp = _make_mock_response(mock_content)
        mock_resp = MagicMock()
        mock_resp.read.return_value = raw_resp
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            return polish_report(md, sf_key="test-key-xxx")

    # ── 修复 1: max_tokens 动态扩展(通过 payload 验证) ──────────────────────
    def test_max_tokens_dynamic_for_long_report(self):
        """长报告 max_tokens 必须 > 6000(动态扩展)。"""
        from app.services.report_polish import _PROMPT
        import json as _json, urllib.request as _ur
        long_md = self.base_md * 4   # ~3000 字，触发动态扩展
        captured = {}

        def capture(req, timeout=None):
            body = _json.loads(req.data.decode("utf-8"))
            captured["max_tokens"] = body.get("max_tokens", 0)
            # 返回一个充分长的润色稿(保留所有关键词)
            full_polish = long_md * 4 + "\n\n> 📝 AI润色"
            raw = _make_mock_response(full_polish)
            mock_r = MagicMock(); mock_r.read.return_value = raw
            mock_r.__enter__ = lambda s: s; mock_r.__exit__ = MagicMock(return_value=False)
            return mock_r

        with patch("urllib.request.urlopen", side_effect=capture):
            try:
                from app.services.report_polish import polish_report
                polish_report(long_md, sf_key="test-key")
            except Exception:
                pass

        expected_min = max(8000, int(len(long_md) * 2))
        self.assertGreaterEqual(captured.get("max_tokens", 0), 8000,
                                f"max_tokens 应 >= 8000，实际 {captured.get('max_tokens')}")
        self.assertEqual(captured.get("max_tokens"), expected_min,
                         f"max_tokens 应为 {expected_min}")

    # ── 修复 2: 4 位数字不强求(模板说教词) ────────────────────────────────────
    def test_small_number_not_required(self):
        """4 位数字(如 1000、4200)不应成为硬护栏·润色允许重述。"""
        # 原文含 1000(来自模板说教) 和 4200(小互动数)，但无 5 位+大数字
        md_small = """# 📋 账号诊断报告 · @小账号

## 一句话先说重点
**结论：对的。**

## 一、你现在是什么情况
- 你的视频平均 **4200 个赞**。

## 小贴士
变现走精准：1000 个对的客户 > 10 万泛粉。

## 七、这份分析有多可信
拿不到的我**绝不瞎编**。
"""
        # 润色稿用"四千多"代替 4200、用"精准客户"代替 "1000 个对的客户" → 应该通过
        polished_no_small = md_small.replace("4200", "四千多").replace(
            "1000 个对的客户", "精准客户") + "\n\n> 📝 AI润色"
        result = self._call_polish(polished_no_small, base_md=md_small)
        # 不应该因为"1000"/"4200"不在润色稿而失败
        self.assertNotIn("1000", result.get("error", ""))
        self.assertNotIn("4200", result.get("error", ""))

    # ── 修复 3: 5 位+大数字必须保留 ────────────────────────────────────────────
    def test_large_number_must_be_preserved(self):
        """5 位+大数字(如粉丝 220000)不得被润色删除或改写为中文单位。"""
        # 场景 A: 润色后保留 220000 → ok
        polished_ok = self.base_md + "\n\n> 📝 AI润色"
        result_ok = self._call_polish(polished_ok)
        self.assertTrue(result_ok.get("ok"), f"保留大数字时应润色成功: {result_ok.get('error')}")

        # 场景 B: 润色把 220000 改成 22万 → 应降级
        polished_bad = self.base_md.replace("220000", "22万") + "\n\n> 📝 AI润色"
        result_bad = self._call_polish(polished_bad)
        self.assertFalse(result_bad.get("ok"),
                         "把 220000 改成 22万 时应降级(核心数字丢失)")
        self.assertIn("220000", result_bad.get("error", ""))

    # ── 修复 4: "瞎编" 子串检查兼容措辞变化 ─────────────────────────────────
    def test_honesty_phrase_anchor_by_substring(self):
        """锚点 '瞎编' 应接受 '绝不瞎编'/'不瞎编'/'没有瞎编' 等措辞。"""
        # '绝不' 被去掉，变成 '不瞎编' → 仍包含 '瞎编' → 应通过
        polished_shortened = self.base_md.replace("绝不瞎编", "不瞎编") + "\n\n> 📝 AI润色"
        result = self._call_polish(polished_shortened)
        self.assertTrue(result.get("ok"),
                        f"'不瞎编' 含 '瞎编' 子串·应视为保留: {result.get('error')}")

    def test_honesty_phrase_fully_removed_fails(self):
        """如果润色完全去掉 '瞎编' → 应降级。"""
        polished_removed = self.base_md.replace("绝不瞎编", "数据都是真的") + "\n\n> 📝 AI润色"
        result = self._call_polish(polished_removed)
        self.assertFalse(result.get("ok"), "完全删除'瞎编'应降级")
        self.assertIn("瞎编", result.get("error", ""))

    # ── 修复 5: 合规段 "晒证据"/"虚假宣传" 必须保留 ─────────────────────────
    def test_compliance_anchor_preserved(self):
        """含资质声称时报告有 '晒证据'/'虚假宣传'，润色删除这些必须降级。"""
        compliance_md = self.base_md + "\n## 合规提醒\n晒证据是必要的。虚假宣传是红线。\n"
        # 润色稿删除合规段 → 降级
        polished_no_compliance = self.base_md + "\n\n> 📝 AI润色"
        result = self._call_polish(polished_no_compliance, base_md=compliance_md)
        self.assertFalse(result.get("ok"), "润色删除合规段时应降级")
        self.assertIn("晒证据", result.get("error", "") + str(result.get("fallback", "")))

    def test_compliance_anchor_kept_passes(self):
        """合规段被保留时润色应成功。"""
        compliance_md = self.base_md + "\n## 合规提醒\n晒证据是必要的。虚假宣传是红线。\n"
        polished_with_compliance = compliance_md + "\n\n> 📝 AI润色"
        result = self._call_polish(polished_with_compliance, base_md=compliance_md)
        self.assertTrue(result.get("ok"),
                        f"保留合规段时应润色成功: {result.get('error')}")

    # ── 长报告 40% 阈值 ─────────────────────────────────────────────────────
    def test_length_threshold_40_pct(self):
        """润色稿 >= 40%(含所有锚点)应通过 · 允许 LLM 归纳商业数据段。"""
        # 生成一个包含大量结构化数据的原始报告
        struct_md = self.base_md + "\n商业数据：" + "{'x': 1}\n" * 50
        # 润色稿：保留所有锚点(220000/790105/瞎编/拿不到) + 归纳商业数据 → 约 42% 长度
        # 用原文锚点段 + 填充确保 >= 40%
        target_len = int(len(struct_md) * 0.42)
        polished_condensed = (self.base_md   # 含所有锚点
                              + "\n商业数据摘要：行业经验区间，具体请校准。\n"   # 归纳裸dict
                              + "\n> 📝 AI润色\n")
        # 确保长度 >= 40%
        while len(polished_condensed) < target_len:
            polished_condensed += "（润色后的商业总结补充内容）\n"
        result = self._call_polish(polished_condensed, base_md=struct_md)
        self.assertTrue(result.get("ok"),
                        f">=40%含所有锚点时应通过 · 实际错误: {result.get('error')}")

    def test_length_below_40_pct_fails(self):
        """润色稿 < 40% 原文应降级(可能是截断)。"""
        short_polished = "太短了" + "\n> 📝 AI润色\n"
        result = self._call_polish(short_polished)
        self.assertFalse(result.get("ok"), "< 40% 应降级")
        self.assertIn("过短", result.get("error", ""))


class TestNumsExtraction(unittest.TestCase):
    """_nums 函数单元测试。"""

    def test_5plus_digits_extracted(self):
        from app.services.report_polish import _nums
        text = "220000 粉丝，38000 个赞，4200 收藏，1000 个客户"
        nums = _nums(text)
        self.assertIn("220000", nums)
        self.assertIn("38000", nums)
        self.assertIn("4200", nums)
        self.assertIn("1000", nums)

    def test_comma_normalized(self):
        from app.services.report_polish import _nums
        text = "6,438,222 个粉丝 790,105 个赞"
        nums = _nums(text)
        self.assertIn("6438222", nums)
        self.assertIn("790105", nums)


if __name__ == "__main__":
    unittest.main(verbosity=2)
