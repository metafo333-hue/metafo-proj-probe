"""benchmark.py 离线测试 · 零网络 · 零 LLM · $0

覆盖：
  - 分位计算：percentile_of / percentile_value / percentile_value_from_sorted 数学正确
  - N_min 门：样本不足 → experience 级·不冒充精确分位
  - 数据源接口可插拔：mock Repo / ExpertSeedRepo / LocalAccumRepo 回退
  - 自建库脱敏沉淀：ingest → 过 N_min 切真实分位
  - 行业差异化分桶 / 行业归一化
  - 短板高亮（is_weakest = 最低分位）
  - 渲染：分位带表达 + 冷启动目标设定 + 诚实标
  - 防玄学：参考级标注 / 只用中位数锚
"""
import tempfile
import unittest
import pathlib

from app.services.benchmark import (
    benchmark, render_benchmark_section, resolve_industry, resolve_bucket,
    percentile_of, percentile_value, percentile_value_from_sorted, to_band,
    BenchmarkProfile, BenchmarkRepo, ExpertSeedRepo, LocalAccumRepo,
    extract_account_metrics, ingest_for_benchmark, confidence_of,
    N_REFERENCE, N_RELIABLE, METRIC_DICT_VERSION,
)


# ── Fixtures ────────────────────────────────────────────────────────────────
EDU_ACCOUNT = {
    "nickname": "财税老王", "follower": 8000, "aweme_count": 60,
    "signature": "财税知识科普·考证干货", "avg_like": 400, "max_like": 1500,
    "hashtags": ["财税", "知识", "考证"],
}
ENT_ACCOUNT = {
    "nickname": "舞蹈小美", "follower": 200000, "aweme_count": 120,
    "signature": "舞蹈才艺颜值", "avg_like": 8000, "max_like": 50000,
    "hashtags": ["舞蹈", "颜值", "才艺"],
}


class _StubRepo:
    """mock 基准数据源（灰度 feed 在此接口接入的验证）。"""
    def __init__(self, pcts, n):
        self._pcts = pcts
        self._n = n

    def get(self, industry, bucket, metric):
        if metric != "interaction_rate":
            return None
        return BenchmarkProfile(
            industry=industry, fans_bucket=bucket, metric=metric,
            percentiles=dict(self._pcts), sample_size=self._n,
            source="third_party", captured_at="2026-06-22T00:00:00Z")


# ── 分位计算 ─────────────────────────────────────────────────────────────────
class TestPercentileMath(unittest.TestCase):
    def test_percentile_value_from_sorted_median(self):
        self.assertEqual(percentile_value_from_sorted([1, 2, 3, 4, 5], 50), 3.0)

    def test_percentile_value_from_sorted_interp(self):
        # 0–10 区间 P25 = 2.25（线性插值，5 点 [0,..,10]）
        v = percentile_value_from_sorted([0, 2.5, 5, 7.5, 10], 25)
        self.assertAlmostEqual(v, 2.5, places=2)

    def test_percentile_of_at_median(self):
        pcts = {10: 1.0, 25: 2.0, 50: 4.0, 75: 8.0, 90: 16.0}
        self.assertAlmostEqual(percentile_of(4.0, pcts), 50.0, places=1)

    def test_percentile_of_between_anchors(self):
        pcts = {10: 1.0, 25: 2.0, 50: 4.0, 75: 8.0, 90: 16.0}
        # 6.0 在 P50(4)–P75(8) 之间 → 应在 50–75
        p = percentile_of(6.0, pcts)
        self.assertTrue(50 < p < 75, f"got {p}")

    def test_percentile_of_clamped(self):
        pcts = {10: 1.0, 50: 4.0, 90: 16.0}
        self.assertLessEqual(percentile_of(100.0, pcts), 100.0)
        self.assertGreaterEqual(percentile_of(-100.0, pcts), 0.0)

    def test_percentile_value_target(self):
        pcts = {10: 1.0, 25: 2.0, 50: 4.0, 75: 8.0, 90: 16.0}
        self.assertEqual(percentile_value(pcts, 75), 8.0)
        # 插值 P60 在 P50(4)–P75(8) 之间
        self.assertTrue(4.0 < percentile_value(pcts, 60) < 8.0)

    def test_to_band_five_levels(self):
        self.assertEqual(to_band(5), "垫底")
        self.assertEqual(to_band(30), "偏弱")
        self.assertEqual(to_band(50), "中位")
        self.assertEqual(to_band(70), "中上")
        self.assertEqual(to_band(95), "头部")
        self.assertEqual(to_band(100), "头部")  # 不越界


# ── 行业归一化 / 分桶 ────────────────────────────────────────────────────────
class TestResolve(unittest.TestCase):
    def test_resolve_industry(self):
        self.assertEqual(resolve_industry("知识科普"), "education")
        self.assertEqual(resolve_industry("颜值才艺"), "entertainment")
        self.assertEqual(resolve_industry("不知道什么"), "general")

    def test_bucket_industry_differs(self):
        # 教培 8000 粉 = small；泛娱乐 8000 粉 = micro（分桶按行业调）
        self.assertEqual(resolve_bucket("education", 8000), "small")
        self.assertEqual(resolve_bucket("entertainment", 8000), "micro")

    def test_confidence_of(self):
        self.assertEqual(confidence_of(0), "experience")
        self.assertEqual(confidence_of(N_REFERENCE), "reference")
        self.assertEqual(confidence_of(N_RELIABLE), "reliable")


# ── N_min 门：样本不足不冒充 ─────────────────────────────────────────────────
class TestNMinGate(unittest.TestCase):
    def test_stub_low_sample_is_experience(self):
        repo = _StubRepo({10: 0.01, 25: 0.02, 50: 0.03, 75: 0.05, 90: 0.08}, n=10)
        metrics = {"interaction_rate": 0.04}
        res = benchmark(metrics, "education", 8000, repo=repo)
        ir = next(r for r in res if r.metric == "interaction_rate")
        self.assertEqual(ir.confidence, "experience")
        self.assertIn("样本不足", ir.note)

    def test_stub_high_sample_is_reliable(self):
        repo = _StubRepo({10: 0.01, 25: 0.02, 50: 0.03, 75: 0.05, 90: 0.08}, n=150)
        metrics = {"interaction_rate": 0.04}
        res = benchmark(metrics, "education", 8000, repo=repo)
        ir = next(r for r in res if r.metric == "interaction_rate")
        self.assertEqual(ir.confidence, "reliable")
        # 0.04 在 P50(0.03)–P75(0.05) 之间 → 中上区
        self.assertTrue(50 < ir.percentile <= 75, ir.percentile)


# ── 接口可插拔（mock 基准） ──────────────────────────────────────────────────
class TestPluggableRepo(unittest.TestCase):
    def test_expert_seed_gives_experience(self):
        repo = ExpertSeedRepo()
        prof = repo.get("education", "small", "interaction_rate")
        self.assertIsNotNone(prof)
        self.assertEqual(prof.confidence, "experience")
        self.assertEqual(prof.source, "expert")
        self.assertEqual(prof.sample_size, 0)

    def test_custom_repo_injected(self):
        # 灰度 feed：传入自定义 provider，benchmark 直接用其分位
        repo = _StubRepo({10: 1, 25: 2, 50: 3, 75: 4, 90: 5}, n=200)
        res = benchmark({"interaction_rate": 3.0}, "education", 8000, repo=repo)
        ir = next(r for r in res if r.metric == "interaction_rate")
        self.assertEqual(ir.source, "third_party")
        self.assertAlmostEqual(ir.percentile, 50.0, delta=2)


# ── 自建库脱敏沉淀 ──────────────────────────────────────────────────────────
class TestLocalAccumRepo(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_fallback_when_insufficient(self):
        repo = LocalAccumRepo(root=self.root)
        prof = repo.get("education", "small", "interaction_rate")
        # 空库 → 回退 ExpertSeedRepo
        self.assertEqual(prof.source, "expert")

    def test_ingest_crosses_nmin_to_self_built(self):
        repo = LocalAccumRepo(root=self.root)
        # 喂入 N_REFERENCE 个样本 → 切真实分位
        for i in range(N_REFERENCE + 5):
            repo.ingest("education", "small", {"interaction_rate": 0.02 + i * 0.001})
        prof = repo.get("education", "small", "interaction_rate")
        self.assertEqual(prof.source, "self_built")
        self.assertGreaterEqual(prof.sample_size, N_REFERENCE)
        # 真实中位数应落在喂入区间内
        self.assertTrue(0.02 <= prof.percentiles[50] <= 0.06)

    def test_ingest_for_benchmark_helper(self):
        repo = LocalAccumRepo(root=self.root)
        info = ingest_for_benchmark(EDU_ACCOUNT, "知识科普", repo)
        self.assertEqual(info["industry"], "education")
        self.assertIn("interaction_rate", info["ingested"])
        # 文件落盘
        files = list(self.root.glob("*.json"))
        self.assertTrue(files)

    def test_ingest_anonymized_no_identity(self):
        repo = LocalAccumRepo(root=self.root)
        ingest_for_benchmark(EDU_ACCOUNT, "知识科普", repo)
        content = list(self.root.glob("*.json"))[0].read_text(encoding="utf-8")
        # 脱敏：不存账号身份（昵称/签名）
        self.assertNotIn("财税老王", content)
        self.assertNotIn("财税知识科普", content)


# ── 指标抽取 ─────────────────────────────────────────────────────────────────
class TestExtractMetrics(unittest.TestCase):
    def test_interaction_rate_proxy(self):
        m = extract_account_metrics(EDU_ACCOUNT)
        self.assertAlmostEqual(m["interaction_rate"], 400 / 8001, places=4)

    def test_growth_rate_needs_revisit(self):
        # 无 prev_follower → 不放入涨粉率（标"需复访"·不冒充）
        m = extract_account_metrics(EDU_ACCOUNT)
        self.assertNotIn("growth_rate", m)
        m2 = extract_account_metrics(EDU_ACCOUNT, prev_follower=6000)
        self.assertIn("growth_rate", m2)
        self.assertAlmostEqual(m2["growth_rate"], (8000 - 6000) / 6000, places=4)

    def test_blackbox_not_faked(self):
        # 无 completion_rate / fan_unit_value 字段 → 不冒充
        m = extract_account_metrics(EDU_ACCOUNT)
        self.assertNotIn("completion_rate", m)
        self.assertNotIn("fan_unit_value", m)


# ── 短板高亮 ─────────────────────────────────────────────────────────────────
class TestWeakest(unittest.TestCase):
    def test_marks_lowest_percentile(self):
        repo = _StubRepo({10: 0.01, 25: 0.02, 50: 0.03, 75: 0.05, 90: 0.08}, n=150)
        # 互动率很低（P 低）→ 应是短板
        res = benchmark({"interaction_rate": 0.005}, "education", 8000, repo=repo)
        ir = next(r for r in res if r.metric == "interaction_rate")
        self.assertTrue(ir.is_weakest)


# ── 渲染 ────────────────────────────────────────────────────────────────────
class TestRender(unittest.TestCase):
    def test_render_growth_has_band_and_honesty(self):
        md = render_benchmark_section(EDU_ACCOUNT, "知识科普")
        self.assertIn("同赛道对标", md)
        # 分位带表达（五档之一）
        self.assertTrue(any(b in md for b in ("垫底", "偏弱", "中位", "中上", "头部")))
        # 诚实标（经验带·参考级）
        self.assertIn("参考级", md)
        self.assertIn(METRIC_DICT_VERSION, md)

    def test_render_cold_start_target_setting(self):
        md = render_benchmark_section(EDU_ACCOUNT, "知识科普", stage="cold_start")
        self.assertIn("冷启动", md)
        self.assertIn("达标", md)
        # 冷启动不给裸分位，给目标
        self.assertIn("目标", md)

    def test_render_uses_median_not_mean(self):
        # 防玄学：渲染中应声明用中位数做锚
        md = render_benchmark_section(ENT_ACCOUNT, "颜值才艺")
        self.assertIn("中位数", md)


if __name__ == "__main__":
    unittest.main()
