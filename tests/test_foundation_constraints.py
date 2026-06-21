"""底层架构铁律测试 · 全国产大模型(数据不出境)。

铁律一(probe-foundation-architecture-constraints-v1.0.md)：probe 所有 LLM 调用走国产
(Qwen/DeepSeek/GLM/Kimi 等·硅基/ufo2)，禁 Claude/GPT/Gemini。本测试扫描代码里的
model 配置行，断言没有海外模型——防未来误用海外模型造成数据出境/不合规。
"""
import pathlib
import re
import unittest

_SVC = pathlib.Path(__file__).parent.parent / "app"
# 海外模型标识(禁)
_FORBIDDEN = ("cc-sonnet", "cc-haiku", "claude", "gpt-3", "gpt-4", "gpt-5", "gemini", "o1-", "o3-")
# model 配置行特征(排除注释/docstring 举例)
_MODEL_LINE = re.compile(r'("model"\s*:|_MODEL\s*=|MODEL\s*=|model\s*=)')


class TestFoundationConstraints(unittest.TestCase):

    def test_no_foreign_model_in_code(self):
        """扫描 app/ 下所有 .py 的 model 配置行·断言无海外模型(数据不出境铁律)。"""
        violations = []
        for f in _SVC.rglob("*.py"):
            if "test" in f.name or f.name.startswith("_"):
                continue
            for i, ln in enumerate(f.read_text(encoding="utf-8").split("\n"), 1):
                stripped = ln.strip()
                # 跳过注释行(举例说明允许提海外名·只查真实配置)
                if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'"):
                    continue
                if not _MODEL_LINE.search(ln):
                    continue
                low = ln.lower()
                for bad in _FORBIDDEN:
                    if bad in low:
                        violations.append(f"{f.name}:{i} 用海外模型「{bad}」: {stripped[:70]}")
        self.assertEqual(violations, [],
                         "违反国产大模型铁律(数据出境风险):\n  " + "\n  ".join(violations))

    def test_default_models_are_govcn(self):
        """关键默认模型必须国产(llm_caller 八闸默认 + report_polish 润色默认)。"""
        govcn = ("bl-", "qwen", "deepseek", "glm", "kimi", "minimax", "doubao", "ernie", "siliconflow")
        for rel in ("app/audit/llm_caller.py", "app/services/report_polish.py"):
            p = _SVC.parent / rel
            if not p.exists():
                continue
            text = p.read_text(encoding="utf-8")
            # 找 getenv(...,"默认值") 里的默认模型
            for m in re.finditer(r'_MODEL\s*=\s*os\.getenv\([^)]*?,\s*"([^"]+)"\)', text):
                default = m.group(1).lower()
                self.assertTrue(any(g in default for g in govcn),
                                f"{rel} 默认模型「{m.group(1)}」非国产·违反铁律")
            for m in re.finditer(r'_?MODEL\s*=\s*os\.getenv\([^,]+,\s*"([^"]+)"\)', text):
                default = m.group(1).lower()
                self.assertTrue(any(g in default for g in govcn),
                                f"{rel} 默认模型「{m.group(1)}」非国产·违反铁律")


if __name__ == "__main__":
    unittest.main(verbosity=2)
