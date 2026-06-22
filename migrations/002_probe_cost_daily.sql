-- probe_cost_daily · 成本日聚合视图（cost-metering 设计 §八.③ 落码）
-- 守 R28（业务数据入 PG）· 目标库：probe-a 本机 probe_collect（不跨机·守 server-roles 机6 数据边界）
-- 用视图而非物化表/定时 job：永远最新、零调度、幂等（CREATE OR REPLACE）。
-- 维度：日 × surface × source_id × status；含缓存命中数（量化省费效果）。

CREATE OR REPLACE VIEW probe_cost_daily AS
SELECT
    date_trunc('day', ts)::date              AS day,
    surface,                                  -- datasource | llm
    source_id,                                -- jzl_wechat_channels | tikhub | <llm provider>
    status,                                   -- success | cached | fail | skipped | degraded
    count(*)                                  AS calls,
    count(*) FILTER (WHERE cache_hit)         AS cache_hits,
    count(*) FILTER (WHERE status = 'skipped') AS skipped,        -- 成本闸拦截数
    sum(cost_real)                            AS cost_real,        -- 供应商真实/估算消耗（原币种·桩值）
    sum(cost_cny)                             AS cost_cny,
    sum(billed)                               AS billed,           -- 向用户计费
    round(avg(latency_ms))                    AS avg_latency_ms
FROM probe_cost_events
GROUP BY 1, 2, 3, 4;

COMMENT ON VIEW probe_cost_daily IS
  'probe 付费调用日聚合（cost-optimization v1.0）· 看缓存命中率/省费/闸拦截 · 喂 ops 用量看板';
