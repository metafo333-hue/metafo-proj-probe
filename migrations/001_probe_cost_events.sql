-- probe_cost_events · 成本明细表（断层#5 · cost-metering 设计 §三/§四.1 落码）
-- 守 R28（业务数据入 PG·禁 SQLite）· R27（CREATE 改列必补 ALTER ADD COLUMN IF NOT EXISTS）
-- 目标库：probe-a 本机 probe_collect（bind 127.0.0.1+100.64.0.5·不跨机·守 server-roles 机6 数据边界）
-- 幂等：可重复执行（CREATE IF NOT EXISTS + DO 块 ALTER IF NOT EXISTS）

CREATE TABLE IF NOT EXISTS probe_cost_events (
    id           BIGSERIAL PRIMARY KEY,
    call_id      TEXT        NOT NULL,                    -- 本次调用唯一 id（幂等/重试关联）
    task_id      TEXT,                                    -- 归属任务
    user_id      TEXT,                                    -- 脱敏 hash（守 R2/PIPL·不存明文）
    surface      TEXT        NOT NULL,                    -- datasource | llm
    source_id    TEXT,                                    -- 数据源 id 或 LLM provider
    kind         TEXT,                                    -- video | deep | faithfulness ...
    units        JSONB       NOT NULL DEFAULT '{}'::jsonb,-- {req:1} 或 {input_tokens,output_tokens}
    unit_cost    NUMERIC(14,8) DEFAULT 0,                 -- 真实单价（回填·非桩值）
    cost_real    NUMERIC(14,8) DEFAULT 0,                 -- 本次真实供应商消耗
    cost_cny     NUMERIC(14,6) DEFAULT 0,                 -- 人民币估算
    billed       NUMERIC(14,8) DEFAULT 0,                 -- 向用户计费（失败=0）
    status       TEXT        DEFAULT 'success',           -- success|fail|cached|degraded|skipped
    cache_hit    BOOLEAN     DEFAULT FALSE,
    retry_seq    INTEGER     DEFAULT 0,                    -- C3 重试雪崩可见
    fallback_of  TEXT,                                     -- M1 fallback 双扣可见
    url_hash     TEXT,                                     -- 规范化 URL hash（守 U3/R2·不存全 URL）
    latency_ms   INTEGER,
    ts           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- R27 DO 块：存量表不会自动迁移，新增列必在此补 ALTER ADD COLUMN IF NOT EXISTS
DO $$
BEGIN
    ALTER TABLE probe_cost_events ADD COLUMN IF NOT EXISTS call_id     TEXT;
    ALTER TABLE probe_cost_events ADD COLUMN IF NOT EXISTS task_id     TEXT;
    ALTER TABLE probe_cost_events ADD COLUMN IF NOT EXISTS user_id     TEXT;
    ALTER TABLE probe_cost_events ADD COLUMN IF NOT EXISTS surface     TEXT;
    ALTER TABLE probe_cost_events ADD COLUMN IF NOT EXISTS source_id   TEXT;
    ALTER TABLE probe_cost_events ADD COLUMN IF NOT EXISTS kind        TEXT;
    ALTER TABLE probe_cost_events ADD COLUMN IF NOT EXISTS units       JSONB DEFAULT '{}'::jsonb;
    ALTER TABLE probe_cost_events ADD COLUMN IF NOT EXISTS unit_cost   NUMERIC(14,8) DEFAULT 0;
    ALTER TABLE probe_cost_events ADD COLUMN IF NOT EXISTS cost_real   NUMERIC(14,8) DEFAULT 0;
    ALTER TABLE probe_cost_events ADD COLUMN IF NOT EXISTS cost_cny    NUMERIC(14,6) DEFAULT 0;
    ALTER TABLE probe_cost_events ADD COLUMN IF NOT EXISTS billed      NUMERIC(14,8) DEFAULT 0;
    ALTER TABLE probe_cost_events ADD COLUMN IF NOT EXISTS status      TEXT DEFAULT 'success';
    ALTER TABLE probe_cost_events ADD COLUMN IF NOT EXISTS cache_hit   BOOLEAN DEFAULT FALSE;
    ALTER TABLE probe_cost_events ADD COLUMN IF NOT EXISTS retry_seq   INTEGER DEFAULT 0;
    ALTER TABLE probe_cost_events ADD COLUMN IF NOT EXISTS fallback_of TEXT;
    ALTER TABLE probe_cost_events ADD COLUMN IF NOT EXISTS url_hash    TEXT;
    ALTER TABLE probe_cost_events ADD COLUMN IF NOT EXISTS latency_ms  INTEGER;
    ALTER TABLE probe_cost_events ADD COLUMN IF NOT EXISTS ts          TIMESTAMPTZ DEFAULT now();
END $$;

-- 聚合查询索引（per-task / per-source / per-day 看板维度·cost-metering §4.2）
CREATE INDEX IF NOT EXISTS idx_cost_events_task   ON probe_cost_events (task_id);
CREATE INDEX IF NOT EXISTS idx_cost_events_source ON probe_cost_events (source_id);
CREATE INDEX IF NOT EXISTS idx_cost_events_ts     ON probe_cost_events (ts);
