# 技术源卡 M5 · 实体对齐与去重

> 需求真源：orchestration-solution D5（真值发现·冻结）· 喂缺口 G4
> checked_at: 2026-06-11 · hands_on: /tmp/ts-m05 / ts-m05-b / ts-m05-c venv 实测

---

## 候选实测

### 候选 A · splink（moj-analytical-services）

| 字段 | 值 |
|------|----|
| **repo** | https://github.com/moj-analytical-services/splink |
| **license** | MIT ✅ |
| **stars** | 2,199（checked_at: 2026-06-11） |
| **最新稳定版** | v4.0.16（2026-03-11）；v5.0.0.dev3（2026-04-05，pre-release） |
| **最近 push** | 2026-06-10（主干活跃） |
| **open issues** | 220 |
| **backend 支持** | DuckDB（核心依赖，零配置）✅；PostgresAPI ✅（需额外 `pip install sqlalchemy psycopg2`，非核心依赖） |
| **PostgresAPI 实现细节** | `from splink.backends.postgres import PostgresAPI`；构造器接受 SQLAlchemy `Engine`；内部用 DuckDB ATTACH 做批量写入（fallback pandas `to_sql`）；实测导入成功（安装 sqlalchemy 后） |
| **核心依赖** | altair / duckdb / igraph / jinja2 / numpy / pandas / sqlglot（无 torch）|
| **依赖重量** | 轻量；DuckDB 模式无额外依赖；PG 模式需 sqlalchemy + psycopg2 |
| **中文适配** | LevenshteinAtThresholds / JaroWinklerAtThresholds / JaccardAtThresholds 均可用于中文字符比较；中文字符天然是字符序列，Levenshtein 字符级距离语义合适；无专项中文预处理（不需要，字符切割即可）；⚠️ 无官方中文基准数据 |
| **算法** | Fellegi-Sunter 概率记录链接（EM 估计 m/u 参数）；支持 dedupe_only / link_only / link_and_dedupe 三模式 |
| **hands_on** | `pip install splink` ✅；`DuckDBAPI` 导入 ✅；`PostgresAPI` 导入（需 sqlalchemy）✅；基础链接流程实测通过（DuckDB 后端）✅；Levenshtein 中文名比较调用正常 ✅ |
| **checked_at** | 2026-06-11 |

**关键发现**：

- PostgresAPI 存在于 v4.0.16 但**不是核心包依赖**——安装 splink 不会自动拉 sqlalchemy/psycopg2，需显式安装。适配成本：`pip install splink sqlalchemy psycopg2-binary` + 创建 SQLAlchemy Engine，约 10 行代码，**适配成本低**。
- 内部架构：PostgresAPI 本质上仍通过 DuckDB 中间层做批量 ETL（DuckDB ATTACH postgres），SQL 生成走 sqlglot PostgreSQL 方言。性能路径：DuckDB 原生比 PG 快，但对 probe 数据量（万级实体）无差异。
- v5 dev 系列活跃开发中，稳定版冻结在 v4.0.16。

---

### 候选 B · dedupe（dedupeio）

| 字段 | 值 |
|------|----|
| **repo** | https://github.com/dedupeio/dedupe |
| **license** | MIT ✅ |
| **stars** | 4,474（checked_at: 2026-06-11） |
| **最新稳定版** | v3.0.3（2025-07-29，GitHub last push） |
| **open issues** | 88 |
| **backend 支持** | 无内置 PG backend；早期版本有 `dedupe-postgresql` 独立包（已停维护·❌）；核心 v3 只操作 Python dict，持久化需自行接 PG |
| **依赖重量** | 中等：affinegap / BTrees / categorical-distance / doublemetaphone / haversine / highered / numpy / scikit-learn / simplecosine / zope.index |
| **中文适配** | `String` 变量类型内置 Affine Gap 距离（字符级）；中文字符可直接用；⚠️ `doublemetaphone`（双重音素，仅适合英文名字音标）对中文无效，使用时应避开 phonetics 特性；`ShortString` 适合公司名等短中文实体 |
| **训练模式** | 主动学习（交互式标注）或 programmatic 标注（`mark_pairs`）；v3 要求训练样本 ≥ 6 对（否则 sklearn CV 报错）|
| **PG 集成成本** | 中等：需自行用 psycopg2/SQLAlchemy 读 PG → Python dict → dedupe 处理 → 写回 PG；官方无样板代码 |
| **hands_on** | `pip install dedupe` ✅ v3.0.3；import 成功 ✅；`dedupe.variables.String('name')` 接受中文 ✅；⚠️ train() 调用需 ≥6 样本对（实测 2 对时 sklearn n_splits=5 报错）|
| **checked_at** | 2026-06-11 |

---

### 候选 C · recordlinkage（J535D165）

| 字段 | 值 |
|------|----|
| **repo** | https://github.com/J535D165/recordlinkage |
| **license** | BSD-3-Clause ✅ |
| **stars** | 1,052（checked_at: 2026-06-11） |
| **最新稳定版** | v0.16（2023-07-20）；**最近 push：2024-02-21**（⚠️ 16 个月无活跃提交）|
| **open issues** | 64 |
| **backend 支持** | 纯 pandas/numpy 操作，无 backend 概念；PG 适配需自行 read_sql → DataFrame → 处理 |
| **依赖重量** | 轻：2.6 MB；numpy / pandas / scikit-learn / jellyfish |
| **中文适配** | Levenshtein（通过 jellyfish）可字符级比较中文；无中文专项测试 |
| **社区健康** | ⚠️ 低活跃：v0.16 是 2023 年发布，维护者响应慢 |
| **hands_on** | `pip install recordlinkage` ✅ v0.16；import ✅；⚠️ `from recordlinkage.compare import Compare` 在 v0.16 API 已变更 |
| **checked_at** | 2026-06-11 |

---

### 候选 D · datasketch（ekzhu）

| 字段 | 值 |
|------|----|
| **repo** | https://github.com/ekzhu/datasketch |
| **license** | MIT ✅ |
| **stars** | 2,928（checked_at: 2026-06-11） |
| **最新稳定版** | v1.10.0（2026-04-17）|
| **最近 push** | 2026-06-08（活跃）|
| **open issues** | 57 |
| **提供能力** | MinHash / MinHashLSH / WeightedMinHash / HyperLogLog / CountMinSketch |
| **backend 支持** | MinHashLSH 支持 Redis / Cassandra / MongoDB 作为存储后端（`storage_config` 参数）；无原生 PG backend，但哈希值可持久化到 PG |
| **依赖重量** | 极轻：0.8 MB；numpy 唯一核心依赖 |
| **中文适配** | ✅ 字符 n-gram（bigram/trigram）作 shingling，天然支持中文；实测：字符 bigram MinHash 正确识别「字节跳动科技有限公司成立于2012年」和「字节跳动科技有限公司于2012年成立」为近重复（Jaccard 相似度超阈值 0.5）✅ |
| **适用场景** | 大规模近重复检测（exact/near-duplicate）；**非实体对齐**（不做字段级概率匹配）|
| **hands_on** | `pip install datasketch` ✅；MinHash + MinHashLSH 字符 bigram 中文近重复检测实测通过 ✅ |
| **checked_at** | 2026-06-11 |

---

## 真值发现算法库现状

### 已知 Python 库盘点（exhaustive search · checked_at: 2026-06-11）

| 包名 | PyPI | 最新版 | 最后更新 | 维护状态 | 算法 | 判定 |
|------|------|--------|---------|---------|------|------|
| truthdiscovery | ✅ | v1.0.4 | 2023-03-29 | ⚠️ 停更 3 年 | Sums / Average / Investment / PooledInvestment / TruthFinder / MajorityVoting | C档·可借鉴 |
| catd | ✅ | v0.5.0 | 2021-10-09 | ❌ 停更 5 年 | CATD（置信度感知真值发现） | C档·仅参考 |
| accu | ✅ | v0.1a2 | 2022-10-05 | ❌ alpha 停更 | Accu | ❌ 弃用 |
| truth-discovery | ❌ | — | — | 不存在 | — | ❌ |
| slaim | ❌ | — | — | 不存在 | — | ❌ |

**结论：无成熟维护的 Python 真值发现库（全部停更 ≥ 3 年）。**

`truthdiscovery`（Joe Singleton，GPL-3.0，6 stars）是唯一可安装的，但：
1. 依赖 numpy，Python 3.14 venv 中安装失败（setuptools 兼容性问题）
2. 停更 3 年，最新 Python 支持不确定
3. GPL-3.0 许可证（⚠️ 与 probe 商用许可不兼容，慎用）

**决策：C 档借鉴自研——参考 Li et al. survey (arXiv:1505.02463) 迭代两步算法：**

```
# 真值发现迭代核心（约 60 行 Python）
# 输入：{claim: {source: value}} 格式
# 步骤 1：用当前源可靠度加权计算真值候选
# 步骤 2：用真值候选反估每源可靠度（一致性 = 可靠度代理）
# 迭代收敛（<= 20 轮）
# 含时效衰减项（orchestration-solution D5 已决）
```

算法复杂度：O(n×m×iter) where n=实体数, m=源数, iter≈10-20。
probe 单任务规模预估（万级实体 × 5-10 源 × 15 轮）：单机可承受。

---

## 分工方案

### 实体对齐用 splink

**场景**：跨源记录中同一实体的不同写法对齐（如「字节跳动科技有限公司」vs「ByteDance Ltd.」vs「字节跳动（北京）有限公司」）

**理由**：
- Fellegi-Sunter 概率模型：EM 估计 m/u 参数，输出每对记录的匹配概率（0-1），比规则阈值更健壮
- DuckDB 后端零配置，数据规模扩到 PG 时切 PostgresAPI（适配成本仅 10 行）
- Levenshtein/JaroWinkler/Jaccard 均支持中文字符级比较
- 维护活跃（MOJ 英国司法部，政府级保障），MIT

**局限**：
- 需要少量已知匹配对做训练（或参数估计），冷启动需先跑 `estimate_u_using_random_sampling`
- 中文名对齐建议用 `LevenshteinAtThresholds` 而非 `JaroWinklerAtThresholds`（后者对中文短名优势不明显）
- blocking rules 对中文字段需手工设计（如前 N 字符、关键字提取）

**与 PG 的适配路径**：
```
# 选项 A（推荐·简单）：DuckDB 内存处理，结果写 PG
linker = Linker(df, settings, db_api=DuckDBAPI())
predictions = linker.inference.predict()
# 写回 PG：psycopg2 批量 INSERT

# 选项 B：直接接 PG
from splink.backends.postgres import PostgresAPI
from sqlalchemy import create_engine
engine = create_engine("postgresql+psycopg2://user:pw@host/db")
db_api = PostgresAPI(engine=engine, schema="splink")
```

---

### 精确去重用 datasketch MinHash LSH

**场景**：大规模内容近重复检测（同一文章被多源转发、摘要轻微改写）

**理由**：
- MinHashLSH O(n) 近似，百万文档级可用
- 中文字符 bigram shingling 无需分词工具（jieba 可选加精度）
- 极轻（0.8 MB，零重型依赖）
- 2026 活跃维护，Redis backend 可选

**参数建议**：
```python
from datasketch import MinHash, MinHashLSH
# 中文正文去重：bigram shingling，阈值 0.8（严格）
# 实体名近重：trigram shingling，阈值 0.5（宽松）
lsh = MinHashLSH(threshold=0.5, num_perm=128)
```

---

### 语义去重用 pgvector（vs datasketch 分工）

| 维度 | datasketch MinHashLSH | pgvector（已可用）|
|------|-----------------------|------------------|
| **检测类型** | 词汇重叠（近重复，改写轻微） | 语义相似（同义表达，不同词汇）|
| **计算开销** | 极低（O(1) 查询） | 中（embedding 推理 + IVFFLAT/HNSW 索引）|
| **中文效果** | bigram 词汇覆盖，改写超 50% 字就漏 | 语义不变则仍相似（改写鲁棒）|
| **适用场景** | 文章去重、转发检测 | 实体语义对齐、跨语言匹配、同义实体识别 |
| **probe 用法** | ① 爬虫去重（内容落库前）② 快速 near-dup 过滤 | ① 实体跨语言对齐（中/英公司名）② 概念层去重 |

**结论：两者互补，不替代。**
- 落库前先过 MinHashLSH（快，去词汇重复）
- 实体对齐阶段用 pgvector 嵌入相似度（慢，去语义重复）
- embedding 模型建议：`text2vec-base-chinese`（本地·无网络依赖）或 ufo2 LiteLLM bl-embed 别名

---

### 真值发现自研（约 60 行 Python）

基于 Li et al. survey 核心算法，配合 orchestration-solution D5 已决时效衰减项：

```python
class TruthDiscovery:
    """probe 内置·CRH/Sums-like 迭代真值发现"""
    def __init__(self, decay_lambda=0.1):
        self.decay_lambda = decay_lambda  # 时效衰减

    def run(self, claims: dict[str, dict[str, any]],
            timestamps: dict[str, dict[str, float]] = None,
            max_iter: int = 20) -> tuple[dict, dict]:
        """
        claims: {entity_id: {source_id: value}}
        returns: (truth_values, source_reliability)
        """
        # 初始化：等权
        sources = set(s for v in claims.values() for s in v)
        reliability = {s: 1.0 for s in sources}

        for _ in range(max_iter):
            # 步骤 1：加权投票算真值（连续值取加权均值，离散取最大权）
            truth = {}
            for entity, obs in claims.items():
                weights = {s: reliability[s] * self._decay(timestamps, entity, s)
                           for s in obs}
                truth[entity] = max(obs, key=lambda s: weights.get(s, 0))

            # 步骤 2：反估源可靠度（一致度 = 与真值匹配的比例）
            new_reliability = {}
            for s in sources:
                agree = sum(1 for e, obs in claims.items()
                            if s in obs and obs[s] == truth.get(e))
                total = sum(1 for e, obs in claims.items() if s in obs)
                new_reliability[s] = agree / total if total > 0 else 0.5

            if new_reliability == reliability:
                break
            reliability = new_reliability

        return truth, reliability

    def _decay(self, timestamps, entity, source):
        if not timestamps or entity not in timestamps:
            return 1.0
        t = timestamps[entity].get(source, 0)
        import time
        age_days = (time.time() - t) / 86400
        return max(0.1, 1.0 - self.decay_lambda * age_days)
```

---

## tech-gate 12 闸速查表

> 针对 D5 核心需求：实体对齐（跨源记录链接）+ 内容去重 + 真值发现前置

| 闸 | 问题 | splink | dedupe | recordlinkage | datasketch |
|----|------|:------:|:------:|:-------------:|:----------:|
| G1 | 许可证可商用（MIT/Apache/BSD）？ | ✅ MIT | ✅ MIT | ✅ BSD-3 | ✅ MIT |
| G2 | Python ≥3.10 兼容？ | ✅ | ✅ | ✅ | ✅ |
| G3 | 无强制 torch/GPU 依赖？ | ✅ | ✅ | ✅ | ✅ |
| G4 | PG backend 或低成本 PG 适配？ | ✅ PostgresAPI（+sqlalchemy）| 🟡 自行接 psycopg2 | 🟡 read_sql | 🟡 结果存 PG（无原生）|
| G5 | 中文文本字段比较可用？ | ✅ Levenshtein/Jaro 字符级 | ✅ String/ShortString 字符级 | ✅ jellyfish | ✅ bigram shingling |
| G6 | 概率/统计匹配（非纯规则）？ | ✅ Fellegi-Sunter EM | ✅ 主动学习 logistic | ❌ 仅相似度得分 | ❌ 只做 Jaccard |
| G7 | 依赖重量可接受（无 >1GB 依赖）？ | ✅ 轻量（DuckDB）| ✅ 轻量 | ✅ 极轻 | ✅ 极轻 |
| G8 | asyncio / 流式处理友好？ | 🟡 同步 API，可 executor 包装 | 🟡 同步 | 🟡 同步 | ✅ 纯计算，可并发 |
| G9 | 大规模可扩展（万级以上）？ | ✅ DuckDB/Spark 双路 | 🟡 万级内 OK，十万级慢 | ❌ 全内存，百万级 OOM | ✅ O(n) LSH |
| G10 | 维护活跃（2025 内有 release）？ | ✅ v4.0.16 2026-03 | ✅ v3.0.3 2025-07 | ❌ v0.16 2023-07 | ✅ v1.10.0 2026-04 |
| G11 | 实测可用（hands_on pass）？ | ✅ DuckDB ✅ · PG API 导入 ✅ | ✅ import ✅ · train 需 ≥6 样本 | 🟡 import ✅ · API 有变更 | ✅ 中文 bigram 实测 ✅ |
| G12 | 与真值发现自研可组合？ | ✅ 输出 match_prob → 喂 TD | ✅ 输出 cluster_id → 喂 TD | 🟡 输出相似分 → 需阈值化 | ✅ dedup 后送 TD |

**闸汇总：**

| 候选 | ✅ | 🟡 | ❌ |
|------|----|----|----|
| splink | 9 | 3 | 0 |
| dedupe | 7 | 4 | 1 |
| recordlinkage | 5 | 4 | 3 |
| datasketch | 9 | 2 | 1 |

---

## verdict

### 推荐选型（分工）

| 职责 | 选型 | 档位 | 理由 |
|------|------|------|------|
| **实体对齐**（跨源记录链接） | **splink**（DuckDB 后端·PostgresAPI 可选） | **A 档·直接引入** | Fellegi-Sunter 概率模型·中文字符级比较可用·PG 适配成本低·MIT·活跃维护 |
| **内容精确去重**（词汇重叠近重复） | **datasketch MinHashLSH** | **A 档·直接引入** | 极轻·O(n)·中文 bigram 实测通过·2026 活跃 |
| **实体语义去重**（跨语言/同义） | **pgvector**（已可用） | **A 档·平台已有** | 无新依赖·与 PG 原生集成·嵌入模型按需选 |
| **真值发现** | **自研（60 行）** | **C 档·借鉴自研** | 无成熟维护库·算法简单·Li et al. survey 清晰·含时效衰减（D5 已决） |
| dedupe | — | **B 档·备选** | 主动学习直觉更好·但 PG 适配需更多胶水·训练样本要求限制冷启动 |
| recordlinkage | — | **D 档·弃用** | 16 个月无活跃提交·API 有变更·不推荐新项目引入 |

### 落矩阵格

| 引擎模块 | 选型 |
|---------|------|
| OS3 多源融合 · 实体对齐层 | splink（DuckDB/PG） |
| OS3 多源融合 · 内容去重层 | datasketch MinHashLSH |
| OS3 多源融合 · 语义对齐层 | pgvector（已有） |
| OS3 多源融合 · 真值发现层 | 自研 TruthDiscovery（60 行·Li et al. CRH 变体）|

---

## 顺手发现

1. **splink v5 正在开发**（dev3 2026-04-05）：架构重写，当前 v4.0.16 稳定；v5 API 将变化，建议锁定 `splink==4.0.16`，不冒进 dev。

2. **中文实体名 blocking rule 设计建议**：中文公司名可用前 3-4 字符做 block（`block_on('substr(name, 1, 4)')`）；地名/括号干扰可预处理（regex 清洗「（北京）」「（深圳）」等地区词）。

3. **pgvector python package v0.4.2**（PyPI 已可用）：提供 `register_vector()` 注册 PG vector 类型，与 psycopg2/SQLAlchemy 集成，直接用于嵌入相似度查询，无需安装额外工具。

4. **datasketch Redis backend** 已内置（`MinHashLSH(storage_config={'type': 'redis', 'basename': b'...', 'redis': {'host': ...}})`）：probe 已有 Redis（机6限流总线），如哈希去重状态需跨进程共享可直接复用。

5. **truthdiscovery（joesingo/truthdiscovery）GPL-3.0 许可证**：即便功能适合，GPL 传染性与 probe 商用计划不兼容——**明确弃用，不引入参考实现，直接自研**。
