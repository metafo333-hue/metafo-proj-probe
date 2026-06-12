# 技术源卡 M7 · 限流/熔断/重试

> 需求真源：orchestration-solution D6（冻结：Redis token-bucket per-source + 429 退避 + 熔断）· 喂缺口 G6
> checked_at: 2026-06-11 · hands_on: /tmp/ts-m07 venv 实测

---

## 候选实测

### 1. throttled-py

| 字段 | 值 |
|------|-----|
| repo | https://github.com/ZhuoZhuoCrayon/throttled-py |
| license | MIT |
| stars | 635 |
| 最近活跃 | 2026-05-17（v3.3.1） |
| Python 要求 | >=3.10 |
| asyncio 支持 | ✅ 原生：`from throttled.asyncio import Throttled`，API 与同步版完全一致 |
| Redis backend | ✅ `store.RedisStore(server="redis://...")` 开箱即用；支持 standalone/sentinel/cluster |
| Token Bucket | ✅ `RateLimiterType.TOKEN_BUCKET.value`，多算法（FW/SW/TB/LB/GCRA） |
| per-source 键 | ✅ `throttle.limit("source-key", cost=1)` 第一参数即 per-source key |
| Lua 原子写 | ✅ Lua 脚本占 repo 2.6%，Redis 操作原子保证无竞态 |
| 依赖重量 | 极轻：核心零依赖；`redis` extra 按需装 |
| hands_on | `pip install throttled-py`（无额外依赖）→ Token Bucket in-mem 7 连发：5 ok/2 limited ✅；asyncio 同结果 ✅ |

**关键证据**：
```python
# 同步
@Throttled(key="/source/twitter", using=RateLimiterType.TOKEN_BUCKET.value,
           quota="100/s burst 50", store=store.RedisStore("redis://localhost:6379/0"))
def fetch_twitter(): ...

# 异步（drop-in 替换）
from throttled.asyncio import RateLimiterType, Throttled
throttle = Throttled(using=RateLimiterType.TOKEN_BUCKET.value, quota="100/s burst 50")
result = await throttle.limit("source-twitter", cost=1)
if result.limited: raise TooManyRequests()
```

---

### 2. pyrate-limiter

| 字段 | 值 |
|------|-----|
| repo | https://github.com/vutran1710/PyrateLimiter |
| license | MIT |
| stars | 503 |
| 最近活跃 | 2026-06-01（v4.2.0） |
| Python 要求 | >=3.10（v4.x） |
| asyncio 支持 | ✅ `try_acquire_async()`、`BucketAsyncWrapper`、`await bucket.method()` |
| Redis backend | ✅ `RedisBucket.init(rates, redis_db, bucket_key)` 支持 `redis.asyncio.Redis` |
| 算法 | ⚠️ Leaky Bucket（非 Token Bucket）— 用 Sorted-Set 存时间戳 |
| per-source 键 | ✅ `bucket_key` 参数即 per-source；`BucketFactory.get()` 可动态路由 |
| 依赖重量 | 轻：可选 `redis`/`psycopg[pool]`/`filelock` |
| hands_on | 安装无异常；in-mem per-source 两桶独立限流 ✅；asyncio context ✅ |

**注意**：算法是 Leaky Bucket 而非 Token Bucket，突发容量语义与 D6 Token Bucket 略有差异（无 burst 蓄积）。若 D6 坚持 Token Bucket 语义，需用 throttled-py 或自实现。

---

### 3. aiolimiter

| 字段 | 值 |
|------|-----|
| repo | https://github.com/mjpieters/aiolimiter |
| license | MIT |
| stars | 772 |
| 最近活跃 | 2024-12-08（v1.2.1） |
| Python 要求 | >=3.10 |
| asyncio 支持 | ✅ 专为 asyncio 设计 |
| Redis backend | ❌ 无 — 纯内存单进程 |
| 算法 | Leaky Bucket（in-process） |
| per-source 键 | ❌ 每个 `AsyncLimiter` 实例即一个限流器，per-source 需手动 dict 管理实例 |
| hands_on | ⏭ 跳过（无 Redis，不满足 D6 分布式要求） |

**结论**：单机辅助可用，不满足 D6 Redis 分布式要求，S2 阶段会缺位。

---

### 4. asyncio-redis-rate-limit（wemake-services）

| 字段 | 值 |
|------|-----|
| repo | https://github.com/wemake-services/asyncio-redis-rate-limit |
| license | MIT |
| stars | 53 |
| 最近活跃 | 2025-09-15（v1.1.0） |
| Python 要求 | 3.7+（但 redis >= 7.0 要求较新） |
| asyncio 支持 | ✅ 纯异步 |
| Redis backend | ✅ redis.asyncio 原生 |
| 算法 | 固定窗口计数（非 Token Bucket） |
| per-source 键 | ✅ 装饰器/context manager 接 key |
| 依赖重量 | 轻，仅 redis |
| hands_on | ⏭ 跳过（算法不匹配 Token Bucket；社区规模偏小） |

---

### 5. redis-rate-limiters（otovo）

| 字段 | 值 |
|------|-----|
| repo | https://github.com/otovo/redis-rate-limiters |
| license | BSD-4-Clause |
| stars | ⚠️ PyPI 未显示（小众） |
| 最近活跃 | 2026-01-23（v0.5.0） |
| Python 要求 | >=3.11 |
| asyncio 支持 | ✅ AsyncTokenBucket context manager |
| Redis backend | ✅ Lua 脚本原子操作 |
| Token Bucket | ✅ 明确支持 |
| per-source 键 | ✅ `name` 参数 |
| 依赖重量 | 轻 |
| hands_on | ⏭ 跳过（版本号 0.5.0 pre-stable；社区极小；BSD-4-Clause 含"广告条款"风险） |

---

### 6. tenacity（重试件）

| 字段 | 值 |
|------|-----|
| repo | https://github.com/jd/tenacity |
| license | Apache 2.0 |
| stars | 8.6k |
| 最近活跃 | 2026-02-07（v9.1.4） |
| Python 要求 | >=3.10（v9.x） |
| asyncio 支持 | ✅ `@retry` 装饰 async def 自动异步 sleep；支持 asyncio/Trio/Tornado |
| Redis backend | N/A（重试逻辑件，不做限流） |
| 依赖重量 | 零依赖 |
| hands_on | async retry 3 次成功 ✅；wait_exponential + retry_if_exception_type 实测通过 ✅ |

**429 退避模式**：
```python
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

@retry(
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(TooManyRequests)
)
async def fetch_with_backoff(source: str): ...
```

---

### 7. circuitbreaker（熔断件）

| 字段 | 值 |
|------|-----|
| repo | https://github.com/fabfuel/circuitbreaker |
| license | BSD-3-Clause |
| stars | ~519（PyPI 列 Critical 项目，top 1%） |
| 最近活跃 | 2025-03-31（v2.1.3） |
| Python 要求 | 3.8–3.10 声明支持 |
| asyncio 支持 | ✅ v2.0.0+ `@circuit` 直接装饰 async def ✅ 实测熔断在第 4 次调用开路 ✅ |
| Redis backend | N/A（熔断状态 in-process，无持久化） |
| 依赖重量 | 零依赖 |
| hands_on | async + 失败阈值 3 → 第 4 次调用抛 CircuitBreakerError ✅ |

---

### 8. pybreaker（熔断件备选）

| 字段 | 值 |
|------|-----|
| repo | https://github.com/danielfm/pybreaker |
| license | BSD-3-Clause |
| stars | 677 |
| 最近活跃 | 2025-09-21（v1.4.1） |
| Python 要求 | >=3.9（实测 3.14 ✅） |
| asyncio 支持 | ⚠️ 官方文档提 Tornado，未明确 native asyncio；`call_async()` 存在但文档模糊 |
| Redis backend | N/A |
| 依赖重量 | 零依赖 |
| hands_on | 同步熔断 ✅；async 未实测（文档不清，circuitbreaker 更优） |

---

## tech-gate 12 闸速查表

> 针对 D6 核心需求：Redis token-bucket per-source + asyncio + 429 退避 + 熔断

| 闸 | 问题 | throttled-py | pyrate-limiter | tenacity | circuitbreaker |
|----|------|:---:|:---:|:---:|:---:|
| G1 | 开源许可证可商用？ | ✅ MIT | ✅ MIT | ✅ Apache-2.0 | ✅ BSD-3 |
| G2 | Python ≥3.10 兼容？ | ✅ | ✅ | ✅ | ✅（3.8+ 声明）|
| G3 | asyncio 原生支持？ | ✅ | ✅ | ✅ | ✅ |
| G4 | Redis backend？ | ✅ 原生 | ✅ 原生 | N/A | N/A |
| G5 | Token Bucket 算法？ | ✅ 明确 | ⚠️ Leaky Bucket | N/A | N/A |
| G6 | per-source key 限流？ | ✅ first arg | ✅ bucket_key | N/A | N/A |
| G7 | Lua 原子写（无竞态）？ | ✅ | ⚠️ Sorted-Set | N/A | N/A |
| G8 | 429/异常触发退避？ | ⚠️ 需配合 tenacity | ⚠️ 需配合 tenacity | ✅ 核心功能 | N/A |
| G9 | 熔断（Circuit Breaker）？ | ❌ | ❌ | ❌ | ✅ |
| G10 | 依赖重量可接受（<5 transitive）？ | ✅ 零强依赖 | ✅ 零强依赖 | ✅ 零依赖 | ✅ 零依赖 |
| G11 | 社区活跃（2026 内有 release）？ | ✅ 2026-05 | ✅ 2026-06 | ✅ 2026-02 | ⚠️ 2025-03 |
| G12 | 实测可用（hands_on pass）？ | ✅ | ✅ | ✅ | ✅ |

**全闸通过**：throttled-py(11/12)、tenacity(9/12)、circuitbreaker(9/12)
pyrate-limiter(10/12，G5 Leaky Bucket 扣分)

---

## 组合方案

### 推荐组合（与 D6 逐条对齐）

```
限流层（G6 per-source Redis Token Bucket）：throttled-py[redis]
重试件（G8 429 退避 + 指数等待）：tenacity
熔断件（G9 源宕自动开路）：circuitbreaker
```

#### D6 决策逐条对齐

| D6 决策点 | 实现件 | 对齐说明 |
|-----------|--------|---------|
| Redis token-bucket | throttled-py `TOKEN_BUCKET` + `RedisStore` | ✅ 算法精确匹配；Lua 原子；无竞态 |
| per-source 限流 | `throttle.limit("source-twitter", cost=1)` | ✅ key 即 source name，天然隔离 |
| 429 退避 | tenacity `retry_if_exception_type(TooManyRequests)` + `wait_exponential` | ✅ 指数退避；async sleep 不阻塞事件循环 |
| 熔断 | circuitbreaker `@circuit(failure_threshold=5, recovery_timeout=30)` | ✅ async 函数直接装饰；源连续 5 次失败开路 |
| S1 单机 asyncio | throttled-py in-memory backend（无需 Redis） → S2 切 RedisStore | ✅ S1 先用内存 backend 开发，S2 一行换 store 即分布式 |
| S2 可分布式 | throttled-py RedisStore（sentinel/cluster 全支持） | ✅ 升级无代码改动 |

#### 调用堆栈示意

```python
# probe/engine/governor.py
from throttled.asyncio import RateLimiterType, Throttled
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from circuitbreaker import circuit

# 全局 per-source 限流器（S1 内存/S2 换 RedisStore）
_throttle = Throttled(
    using=RateLimiterType.TOKEN_BUCKET.value,
    quota="100/s burst 50",  # 按 source 配置
    # store=store.RedisStore("redis://localhost:6379/0"),  # S2 解注释
)

def make_fetcher(source_id: str):
    @circuit(failure_threshold=5, recovery_timeout=60)  # 熔断：横切整个 source
    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(TooManyRequests),
    )
    async def fetch():
        result = await _throttle.limit(source_id, cost=1)
        if result.limited:
            raise TooManyRequests(f"rate limit hit: {source_id}")
        return await _do_fetch(source_id)
    return fetch
```

#### 备选：pyrate-limiter 替换 throttled-py

若对 Leaky Bucket 语义（平滑无突发）更合适某些 source（如需严格恒速），可用 `pyrate-limiter` 的 `RedisBucket` 替换 throttled-py 的 `RedisStore`，两者 API 并不互斥，可按 source 类型选算法。

---

## verdict

**档位：A — 推荐三件套直接落地**

| 件 | 档位 | 理由 |
|----|------|------|
| throttled-py 3.3.1 | **A** | 唯一同时满足 Token Bucket + Redis + asyncio + per-source key + Lua 原子的成熟件；MIT；2026-05 活跃；S1→S2 零代码升级路径 |
| tenacity 9.1.4 | **A** | 8.6k stars 业界标准重试件；Apache-2.0；async 原生；零依赖；最近 release 2026-02 |
| circuitbreaker 2.1.3 | **A-** | async 支持 v2.0+ 实测通过；zero-dep；BSD-3；最近 release 2025-03（稍旧但稳定） |

**替换出口**：
- throttled-py 若出现不可修复 bug → 备选 `pyrate-limiter 4.2.0`（Leaky Bucket，需接受算法差异）或手写 40 行 Lua + redis-py（见 D6 冻结设计附录）
- circuitbreaker 若需持久化熔断状态（跨进程共享断路器）→ 换 `purgatory`（Redis backend 熔断状态，但 4 stars 极小众，需评估）

**落 L×四引擎矩阵格**：

Governor（横切）L1–L4：
- **L1 接入层**：circuitbreaker 装饰 L1 source adapter，源宕即开路防雪崩
- **L2 采集层**：throttled-py per-source 限流（`throttle.limit(source_id)`）保证不超源 quota
- **L3 验证层**：tenacity 重试（验证 API 偶发 429/503 时指数退避）
- **L4 整合层**：无需额外限流件（整合层读 L3 结果，不对外发请求）

---

## 顺手发现

1. **throttled-py 的 `burst` 语法**：quota 支持 `"100/s burst 50"` — burst 值控制令牌桶初始容量，正好对应 D6「突发容量」需求，无需额外配置。

2. **pyrate-limiter v4.2.0 算法标注需注意**：README 标题写"Leaky-Bucket Algorithm Family"，但内部实现用 Sorted-Set 按时间戳滑动，语义上更接近滑动窗口而非严格漏桶。D6 如果未来要改算法类型，pyrate-limiter 的算法标签可能让人误判。

3. **aiobreaker（arlyon/aiobreaker）已停更（last release 2021-05）**：搜索时多次出现，需明确排除，避免团队误引。

4. **circuitbreaker 2.1.3 Python 版本声明至 3.10**：实测在 3.14 环境安装运行无问题，PyPI 元数据未更新 classifiers，不影响使用。

5. **Redis 版本门槛**：throttled-py 依赖 redis-py（对应 Redis server >=5.0），probe 当前 Redis 是 6.x/7.x（D6 规划），兼容。
