# probe · 隐私·数据留存·合规工程设计 v1.0

> 日期：2026-06-10 · 性质：probe 引擎**合规红线工程落地**真源（闭缺口 #3）
> 真源边界：红线**口径**仍以 [feasibility §5](../4-research/probe-github-datasource-feasibility-v1.md) 为准；本文只把口径翻译成「管线哪一环·用什么字段/机制·违反即什么后果」的**可执行工程设计**，不改口径。
> 补缺口 #3：probe 已有合规口径声明，但缺「采集→审核→整合→交付→存储」各环的执行点和硬保障。
> 约束遵从：PIPL 最小必要原则 · 个保法第 53 条 · 刑法 253 之一（人物数据入刑阈值）· server-roles T1/T3 · R28 业务数据入 PG · R27 大文件不入仓。

---

## 〇、一句话 + 已定决策（不再反复议）

**【一句话】** probe 合规工程的核心 = 在管线入口前置判定 `persist_policy`，以 `ephemeral` 作物理开关切断人物 OSINT 落库路径；其余红线（PII 脱敏、AIGC 标识、留存周期、用户权利）分环插拦截点，审计日志指针化不含 PII。

| # | 已定决策 | 依据 |
|---|----------|------|
| D1 | `persist_policy=ephemeral` 是人物 OSINT 不落库的**唯一硬开关**；所有写 PG 路径必须先检查此字段，非 `normal` 禁止写 claim/conclusion | feasibility §5·数据脊柱 §2.4/§2.3 |
| D2 | 合规判定分两阶段：**意图阶段前置判**（MetaAsk 澄清后立即判）+ **L2 采集发现人物可升级**（发现自然人信号即自动升级 ephemeral，不等整合阶段） | feasibility §5 调用方责任边界 #3 |
| D3 | 审计日志（`probe_audit_trace`）永不含 PII 本体，只存指针（task_id + evidence_ref），PII 在指针指向的位置经脱敏管道处理后才可查 | 凭据脱敏精神（L1-governance/credentials.md）|
| D4 | AIGC 标识贯穿全链：采集内容带 `aigc_flag`，probe 自产结论带 `probe_generated=true`，交付物 HTML/PPT 带水印 footer | audit-system 闸3 + feasibility §5 |
| D5 | 监测快照（B6/C4 长期订阅）按敏感度分两档留存：普通监测目标最长 180 天；涉及自然人监测目标**禁写快照**（ephemeral 订阅） | 见 §三 留存矩阵 |
| D6 | 删除权级联：用户删除任务/账户触发 delete_cascade job，7 天内清空 PG + Redis + 对象存储三层 | 见 §四 |

---

## 一、`persist_policy` 判定：什么任务判 ephemeral

### 1.1 判定信号清单

下表任一信号触发，即判 `persist_policy=ephemeral`：

| 信号类别 | 具体信号 | 识别方式 |
|---------|---------|---------|
| **自然人主体** | `task_type` 含 `osint`·`person`·`individual`·`background`；input 中包含中国公民身份证/姓名+手机/住址 | 意图阶段 NER 识别 + task_type 枚举白名单 |
| **敏感组合** | 姓名 + 任意两项（手机/身份证/住址/工作单位）联合查询 | L2 采集前 input 扫描：`sensitive_combo_check()` |
| **高 PIPL 风险 task_type** | `selfmedia.kol_identity_investigation`·`person.osint`·`person.background_check` | task_type 枚举黑名单 → 强制 ephemeral |
| **L2 采集发现人物** | L2 扇出命中人物相关 API（Sherlock/Maigret/社会关系图谱源）且源响应含 `personal_data=true` | L2 适配器返回 `data_category` 字段，值含 `personal_data` → 升级 ephemeral |
| **敏感话题** | 政治人物·涉及未成年人·宗教领袖 OSINT | 意图阶段敏感词过滤 + 主体类型分类模型 |

### 1.2 判定时机与两阶段机制

```
┌─────────────────────────────────────────────────────────────────┐
│  阶段一：意图阶段前置判（MetaAsk 澄清后·扇出计划前）               │
│  输入：归一化意图 + task_type + input_material                     │
│  动作：classify_intent() → persist_policy 写入 probe_task         │
│  结果：ephemeral 任务：扇出计划自动裁剪（剔除无必要字段采集）          │
│                                                                   │
│  阶段二：L2 采集发现人物 → 升级（late escalation）                  │
│  触发：L2 适配器 source_hit 的 data_category 包含 personal_data    │
│  动作：task_updater.escalate_to_ephemeral(task_id)                │
│  保障：escalate 是幂等操作；normal → ephemeral 单向，不可降级        │
│  约束：escalate 后已写入 PG 的 source_hit 行 → 立即触发 PII 脱敏    │
└─────────────────────────────────────────────────────────────────┘
```

> ⚠️ 阶段二升级是**兜底**，不是常规路径。绝大多数人物类任务应在阶段一判出，L2 发现只是防漏。

### 1.3 ephemeral 任务的全链路约束

| 环节 | 约束 | 违反后果 |
|------|------|---------|
| **L2 采集** | L2 源响应缓存允许写（仅做采集中转），但 TTL ≤ 任务生命周期（max 1 小时），缓存键带 `ephem:` 前缀 | TTL 超期自动淘汰；违反即数据残留泄漏 |
| **L3 验证** | claim 审核过程可在内存流转；**禁写 `probe_claim` 表** | 写 claim 触发 DB-level guard（见 §1.4） |
| **L4 整合** | 结论在内存组装后直接 API 返回；**禁写 `probe_conclusion` 表** | 同上 |
| **`probe_source_hit`** | 可写（用于可观测性），但 `raw_ref` 字段置 null（不保留原始响应引用）；`outcome` 字段保留 | raw_ref 若有值 → 脱敏管道覆写 |
| **Redis 缓存** | L1 结论缓存**禁写**；L2 源响应缓存短 TTL（见上），带 `ephem:` 前缀标记 | L1 缓存若有 ephem 结论 → 启动时 SCAN 删除 |
| **日志** | 所有结构化日志中涉人物字段（姓名/手机/身份证）→ 脱敏替换 `[REDACTED]` | 见 §二 PII 脱敏管线 |
| **交付物** | HTML/text 交付物生成后即时推送，不写 `probe_artifact.uri`（无对象存储落盘）| expires_at 为当前时间（即时过期） |
| **审计留痕** | `probe_audit_trace` 正常写，trace_id 贯穿，但 evidence_ref 只指向脱敏后的数据 | 见 §八 |

### 1.4 数据库级硬保障（DB-level guard）

在 PG 层为 `probe_claim` 和 `probe_conclusion` 表建写前触发器：

```sql
-- 触发器：ephemeral 任务禁写 claim
CREATE OR REPLACE FUNCTION guard_ephemeral_claim()
RETURNS TRIGGER AS $$
DECLARE
  policy text;
BEGIN
  SELECT persist_policy INTO policy FROM probe.probe_task WHERE id = NEW.task_id;
  IF policy = 'ephemeral' THEN
    RAISE EXCEPTION 'EPHEMERAL_WRITE_BLOCKED: task_id=% is ephemeral, claim/conclusion禁写PG', NEW.task_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_guard_ephemeral_claim
  BEFORE INSERT ON probe.probe_claim
  FOR EACH ROW EXECUTE FUNCTION guard_ephemeral_claim();

-- probe_conclusion 同理部署相同触发器
```

> ✅ 即便应用层漏判，DB 触发器作为最后一道硬保障，ephemeral 任务写入 claim/conclusion 时 PG 直接抛异常，应用层 catch 后记 Q6 告警日志。

---

## 二、PII 识别与脱敏管线

### 2.1 PII 识别范围

| 类别 | 正则/模型 | 处置 |
|------|---------|------|
| 中国身份证号 | `\b[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b` | 掩码 `1**************5X` |
| 手机号 | `\b1[3-9]\d{9}\b` | 掩码 `138****5678` |
| 银行卡号 | `\b\d{16,19}\b` + Luhn 校验 | 掩码 `6222 **** **** 8888` |
| 邮箱 | `\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b` | 掩码 `foo***@gmail.com` |
| 中文姓名（上下文感知） | NER 模型（`bert-base-chinese-ner`）识别 PER 实体 | 仅在 ephemeral 任务或日志中替换 `[姓名]` |
| 住址 | NER 识别 LOC 细粒度（街道门牌级）| 泛化到区级 `XX区[地址]` |
| IP 地址 | `\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b` | 掩码末位 `192.168.1.***` |

### 2.2 脱敏执行点（逐环插入）

```
采集(L2) → [脱敏点A] → 验证(L3) → [脱敏点B] → 整合(L4) → [脱敏点C] → 日志落盘
```

| 脱敏点 | 位置 | 脱敏对象 | 实现 |
|-------|------|---------|------|
| **点A：采集后即时** | L2 适配器 `normalize()` 返回前 | source_hit.raw_ref 里的 PII（ephemeral 任务直接置 null；normal 任务脱敏后才存引用） | `pii_mask_pipeline(text)` 函数，正则 + NER，耗时 < 50ms |
| **点B：验证后写 claim 前** | L3 验证输出 → PG 写入 `probe_claim.claim` 前 | claim 文本中的 PII（normal 任务脱敏后写；ephemeral 任务不走这路） | 同上，claim 字段经管道输出 |
| **点C：日志落盘前** | 结构化日志 handler，写磁盘前 | 所有日志行中匹配 PII 正则 → sed 风格替换 | `logging.Filter` 子类 `PIIMaskFilter`，注册到所有 logger |

### 2.3 禁止全文回显（凭据脱敏精神延伸到 PII）

对齐 `L1-governance/credentials.md` § 统一管道：

- **禁** `source_hit.raw_ref` 存原始人物数据完整 JSON（复用 § ① grep -c 精神：只存引用/计数，不存全文）
- **必须** 原始响应进 Redis L2 缓存前先过脱敏管道（`point-A`），Redis 里存的是脱敏后的摘要
- **禁** `probe_claim.claim` 字段含未脱敏手机/身份证字符串
- **日志** 使用 `PIIMaskFilter`，stderr/stdout 均注册，防 PII 进 journald

### 2.4 脱敏精度局限（诚实边界）

> ⚠️ 以下脱敏能力待标定，当前保守处理：
> - 中文姓名 NER 召回率约 85-90%（非全覆盖），偏僻名字或混合文本可能漏识别 → 当前策略：ephemeral 任务结论整段丢弃而不依赖 NER 脱敏
> - 住址泛化到区级存在过泛（丢失有用信息）→ 当前接受，精度阈值待实测后调整

---

## 三、数据留存周期矩阵

> 说明：`normal` = 普通任务/监测；`ephemeral` = 人物 OSINT/敏感主体；`sensitive` = 含 PIPL 特殊类型数据（种族/宗教/健康等）。

### 3.1 留存矩阵（各类数据 × 形态 × 留存周期）

| 数据类型 | normal | ephemeral | sensitive | 到期清理机制 |
|---------|--------|-----------|-----------|------------|
| `probe_task` 元数据 | 365 天 | **任务完成后立即标记 expires_at=now+1h；1h 后 cron 删** | 90 天 | `cleanup_job` 按 expires_at 扫表 |
| `probe_claim` | 180 天 | **禁写（DB 触发器硬拦）** | 60 天 | expires_at cron |
| `probe_conclusion` | 180 天 | **禁写（DB 触发器硬拦）** | 60 天 | expires_at cron |
| `probe_source_hit` | 90 天 | 保留（raw_ref=null）· 30 天 | 30 天 | expires_at cron |
| `probe_artifact` 交付物 | flash 7 天 / deep 30 天 | **不落盘（expires_at=now 即时过期）** | 7 天 | expires_at cron + 对象存储 lifecycle rule |
| **监测快照** `probe_monitor_snapshot` | 180 天（普通主体）| **禁写快照（ephemeral 订阅不存快照）** | 30 天 | subscription.expire_policy 驱动 |
| `probe_audit_trace` | 730 天（合规审计需要）| 730 天（指针化不含 PII，留存不违规）| 730 天 | 只有用户账户注销时才删（R34） |
| `probe_feedback` | 365 天 | 30 天（仅保留反馈本身·不含结论内容）| 90 天 | expires_at cron |
| `probe_eval_goldenset` | 永久（评测金标·研究价值）| **禁用人物 OSINT 样本作金标** | 永久但脱敏 | 人工归档，不自动清 |
| Redis L1 结论缓存 | 按信息域 TTL（1h-72h）| **禁写** | 1h | Redis TTL 自动过期 |
| Redis L2 源响应缓存 | 按源时效（15min-24h）| 短 TTL ≤ 1h + `ephem:` 前缀 | 15min | Redis TTL 自动过期 |
| 结构化日志文件 | 7 天滚动 | 7 天（已脱敏）| 7 天 | logrotate |

### 3.2 监测订阅（B6/C4）特殊处理

B6（品牌监控）/C4（竞品追踪）是长期订阅场景，持续写快照。留存策略：

```
订阅创建时 → classify_subscription_target(target)
  ├── 返回 "entity" / "brand" / "topic"  → normal · 快照保留 180 天
  └── 返回 "person"（自然人主体）         → 强制 persist_policy=ephemeral
                                           → subscription 状态写入 "ephemeral_mode=true"
                                           → 禁写 probe_monitor_snapshot
                                           → 每次监测结论只即时推送（webhook/notify），不落库
                                           → ⚠️ 用户端告知：该订阅不保留历史快照
```

> ✅ 这样确保 B6/C4 长期订阅不会把自然人信息持续累积成"数据库"（PIPL/刑法253之一 防批量落库红线）。

### 3.3 cron 清理执行

```python
# cleanup_job.py - 每日 02:00 UTC 执行（tencent-sh cron）
# 遵循 R-EHW 三锁：fcntl.LOCK_EX + atomic write + version 校验

def run_cleanup():
    # 1. PG 按 expires_at 批量删（chunk=1000，防锁表）
    PG.execute("""
        DELETE FROM probe.probe_task WHERE expires_at < NOW() AND expires_at IS NOT NULL LIMIT 1000;
        DELETE FROM probe.probe_claim WHERE expires_at < NOW() AND expires_at IS NOT NULL LIMIT 1000;
        DELETE FROM probe.probe_conclusion WHERE expires_at < NOW() AND expires_at IS NOT NULL LIMIT 1000;
        DELETE FROM probe.probe_source_hit WHERE expires_at < NOW() AND expires_at IS NOT NULL LIMIT 1000;
        DELETE FROM probe.probe_artifact WHERE expires_at < NOW() AND expires_at IS NOT NULL LIMIT 1000;
    """)
    # 2. 对象存储 lifecycle rule：bucket=probe-artifacts，rule: expires_days 对应各类型
    # （对象存储侧独立 rule，不由此脚本控制，此处只确认 rule 已激活）
    # 3. Redis ephem: 前缀键：由 TTL 自动过期，此处 SCAN 做兜底清理
    for key in redis.scan_iter("ephem:*"):
        if redis.ttl(key) < 0:  # no TTL 的漏网
            redis.delete(key)
```

---

## 四、用户权利工程实现

### 4.1 删除权（被遗忘权）

**触发**：用户通过 hub 账户中心发起「删除任务」或「注销账户」。

```
用户请求删除 task_id / user_id
    │
    ▼
delete_cascade_job.enqueue(user_id, task_ids, cascade_level)
    │
    ├── 级别1：单任务删除
    │   ├── PG: DELETE probe_task/claim/conclusion/source_hit/artifact/feedback WHERE task_id=X
    │   ├── Redis: DEL task:{id}:progress; SCAN/DEL concl:{*task_id_含*}
    │   └── 对象存储: delete_object(artifact.uri) for each artifact
    │
    └── 级别2：账户注销（全量删除）
        ├── PG: 上述所有表 WHERE user_id=X（分批 chunk=500）
        ├── PG: probe_monitor_subscription WHERE user_id=X（级联删 snapshot）
        ├── PG: probe_audit_trace WHERE task_id IN (user所有task)  ← 账户注销才删
        ├── Redis: SCAN/DEL user:{id}:* 所有键
        └── 对象存储: 批量删除 user prefix 下所有对象
```

**SLA**：收到删除请求 → 7 天内完成三层清理（PG + Redis + 对象存储）。
**审计**：删除操作本身写入独立的 `probe_deletion_audit` 表（记录：user_id + 操作时间 + 删除范围 + 执行状态），此表数据**不含被删内容本体**（只记删除事实），保留 365 天用于合规证明。

### 4.2 导出权（个人数据可携带）

**触发**：用户请求导出自己的 probe 使用数据。

导出范围（个人数据可携带部分）：

| 数据 | 导出形态 | 备注 |
|------|---------|------|
| `probe_task` 列表 | JSON | 含 intent/task_type/tier/status/created_at，不含 fanout_plan 内部细节 |
| `probe_conclusion` 摘要 | JSON | 七段报告 + 三标签 + 置信度 |
| `probe_artifact` 链接 | JSON | expires_at 内有效的 uri 列表 |
| `probe_feedback` | JSON | 用户自己提交的纠错内容 |
| 监测订阅列表 | JSON | subscription target + schedule |

**不导出**：`probe_audit_trace`（系统内部审计）· `probe_source_hit` 内部细节（非用户数据）· `probe_eval_goldenset`（系统数据）。

导出交付：zip 包 → 对象存储临时链接（48h 有效）→ 站内通知用户下载。

---

## 五、最小必要采集：扇出计划的合规裁剪

### 5.1 裁剪时机

在意图阶段判出 `persist_policy` 后、**生成扇出计划（fanout_plan）之前**，执行 `fanout_trim(intent, persist_policy)`：

```python
def fanout_trim(intent: str, persist_policy: str, proposed_sources: list[str]) -> list[str]:
    """
    最小必要原则：裁掉对本次任务无必要的源，
    ephemeral 任务额外裁掉所有不支持即时单次查询的源。
    """
    necessary = [s for s in proposed_sources if is_necessary_for_intent(s, intent)]
    if persist_policy == "ephemeral":
        # 人物 OSINT：只保留支持即时单次查询的源（禁批量/订阅式）
        necessary = [s for s in necessary if source_registry[s].supports_instant_query]
        # 额外移除：不需要的"背景关联"源（如企业关联图谱）除非意图明确需要
        necessary = [s for s in necessary if not is_enrichment_only(s, intent)]
    return necessary
```

### 5.2 裁剪规则（最小必要清单）

| 意图类型 | 允许采集的信息范围 | 明确禁止采集 |
|---------|----------------|------------|
| 自媒体竞品分析 | 公开账号数据（粉丝数/发文/互动）| 账号主的个人手机/住址/身份证 |
| 企业调研 | 工商公开信息/法人名（公开）+ 财务指标 | 法人私人住址·个人银行流水 |
| 人物 OSINT（ephemeral） | 平台公开账号聚合（仅即时）| 组合超过三项个人信息·家庭成员·未公开信息 |
| 行业情报 | 行业报告/市场数据/公开新闻 | 无关个人信息 |

### 5.3 与编排联动

扇出计划 `probe_task.fanout_plan` 写入后含 `trimmed_sources` 字段（记录被裁剪的源及原因），供后续可观测性和合规审计查阅。

---

## 六、AIGC 标识全链路

### 6.1 三类标识对象

| 对象 | 标识字段 | 赋值时机 |
|------|---------|---------|
| **采集到的外部内容** | `probe_claim.aigc_flag=true/false/unknown` | L3 闸3（Binoculars/C2PA 检测）写入 |
| **probe 自产结论** | `probe_conclusion` 元数据 `probe_generated=true` + `model_id` | L4 整合写结论时强制标注 |
| **交付物** | HTML footer 固定水印 · PPT 封底注释 | 交付物模板内置，不可去除 |

### 6.2 采集内容 AIGC 检测（闸3）

```
L3 闸3 输入：source_hit 的归一化文本
    ├── 文本类：Binoculars（开源·本地）ppl 比值 → aigc_score
    │          阈值：score > 0.85 → aigc_flag=true；0.6-0.85 → unknown
    ├── 图像类：C2PA 凭证核验（有 manifest → 保留来源信息）
    │          无 manifest：DeepfakeBench（CC BY-NC·仅原型阶段）/ 商业 API（S2+）
    └── 写入：probe_claim.aigc_flag；AIGC 内容降权（不直接拒绝，降置信度）
```

> ⚠️ 文本 AIGC 检测精度局限：Binoculars 对短文本（<200 token）可靠性下降；当前保守策略：短文本标 `unknown`，不强判 `true`。

### 6.3 probe 自产结论标识

```json
// probe_conclusion.seven_section 顶层元数据
{
  "probe_generated": true,
  "model_id": "claude-sonnet-4-6",
  "generation_ts": "2026-06-10T14:23:00Z",
  "source_count": 5,
  "aigc_source_ratio": 0.2,   // 采集内容中 aigc_flag=true 的比例
  "incomplete": false
}
```

### 6.4 交付物水印（不可去除）

**HTML 模板末尾固定 footer**（CSS 禁用 `display:none`）：

```html
<footer class="probe-aigc-disclosure" style="font-size:11px;color:#888;margin-top:24px;border-top:1px solid #eee;padding-top:8px;">
  本报告由 probe 情报引擎生成 · AI 辅助综合分析 · 生成时间 {{generated_ts}} · 内容仅供参考，请核实关键信息
  蜀ICP备2026010386号-1
</footer>
```

**PPT 封底**：模板最后一页含相同披露文字，锁定不可删除（PPT XML `spLocks` 属性）。

---

## 七、敏感话题处理

### 7.1 敏感话题分类

| 类别 | 示例 | 处置策略 |
|------|------|---------|
| **政治人物 OSINT** | 领导人私生活·政治人物家庭 | 拒答（返回 `REFUSED_SENSITIVE_POLITICAL`）|
| **暴力/恐怖** | 危险人物追踪·武装组织 | 拒答（返回 `REFUSED_SAFETY_RISK`）|
| **未成年人** | 任何未成年人 OSINT/身份信息 | 强制拒答 + 告警写 Q6 |
| **宗教领袖** | 宗教人物深度画像 | 降级处理（仅返回公开事实·不做人物背调）|
| **中国敏感主题** | 涉及 PIPL 特殊类型（种族/健康/基因）| persist_policy=sensitive；60 天留存；禁出境 |

### 7.2 与 8 闸的关系

敏感话题拦截在**意图阶段**（闸0 之前）执行，早于 8 闸：

```
意图阶段
  ├── classify_sensitivity(intent) → ["SAFE", "POLITICAL", "VIOLENT", "MINOR", "RELIGIOUS", "SENSITIVE_PIPL"]
  ├── SAFE → 正常流入 L2
  ├── POLITICAL/VIOLENT/MINOR → 立即返回拒绝响应，不进入管线
  ├── RELIGIOUS → 降级标记（task.flag="religious_degraded"）→ L4 整合时限制输出深度
  └── SENSITIVE_PIPL → persist_policy=sensitive → 进入管线但收紧留存策略
```

**与 8 闸的分工**：
- 意图阶段：拦截「不该做」的话题（拒答/降级）
- 闸3（抗 AIGC/污染）：处理「可以做但内容有问题」的情况（内容质量问题）
- 两者互补，不重叠

### 7.3 拒答响应格式

```json
{
  "status": "refused",
  "reason_code": "REFUSED_SENSITIVE_POLITICAL",
  "reason_text": "该查询涉及政治人物隐私信息，probe 不支持此类查询",
  "task_id": "T-xxx",
  "persist_policy": "ephemeral",
  "data_retained": false
}
```

> 拒答本身记入 `probe_audit_trace`（闸0 留痕，reason_code 字段），不含用户 input 原文（input 脱敏后只存 task_type + 拒绝原因码）。

---

## 八、合规审计可证

### 8.1 审计日志设计（指针化·不含 PII）

`probe_audit_trace` 表（数据脊柱 §2.11）作为合规可证的核心：

| 字段 | 内容 | PII 风险 |
|------|------|---------|
| `task_id` | FK 到 probe_task | 无（ID 不含 PII）|
| `gate` | 闸号（0-7）+ `persist_policy_check`·`sensitivity_check` 等合规步骤 | 无 |
| `verdict` | `pass/fail/refused/escalated_to_ephemeral` | 无 |
| `evidence_ref` | Langfuse trace URL / 对象存储 WORM 文件指针 | 无（只是指针）|
| `created_at` | 时间戳 | 无 |

**PII 在哪里？** 永远不在 audit_trace 本身，而在 `evidence_ref` 指向的位置——而那个位置在写入时已经过脱敏管道（§二 点B/点C）。

### 8.2 合规可证的覆盖范围

| 合规动作 | 证据点 | 存储位置 |
|---------|-------|---------|
| persist_policy 判定执行 | `gate=persist_policy_check · verdict=ephemeral` | probe_audit_trace |
| ephemeral 任务无结论落库 | DB 触发器异常记录（若触发则告警）+ audit_trace 无 claim/conclusion 写入记录 | probe_audit_trace + application log |
| PII 脱敏执行 | `gate=pii_mask · evidence_ref=<脱敏日志指针>` | probe_audit_trace |
| AIGC 标识写入 | `gate=aigc_detection · verdict=flagged/clean` | probe_audit_trace |
| 敏感话题拒答 | `gate=sensitivity_check · verdict=refused · reason_code=XXX` | probe_audit_trace |
| 数据删除执行 | probe_deletion_audit 表独立记录 | probe_deletion_audit |
| 最小必要裁剪 | fanout_plan.trimmed_sources 字段 | probe_task.fanout_plan (jsonb) |

### 8.3 审计日志防篡改

- `probe_audit_trace` 表：只追加（`INSERT`），禁 `UPDATE`/`DELETE`（PG `RULE` 实现：`CREATE RULE no_update_audit AS ON UPDATE TO probe.probe_audit_trace DO INSTEAD NOTHING`）
- 定期哈希链快照（每日 03:00 UTC）：将当天 audit_trace 哈希值写入独立的 `probe_audit_hash_chain` 表
- 账户注销时 audit_trace 不删除（保留 730 天），作为 probe 合规执行的长期证明

### 8.4 合规报告自动生成

每月首日 04:30 UTC cron 自动汇总：

```
合规月报内容（不含 PII）：
- ephemeral 任务总数 + 占比
- 触发 DB 触发器异常次数（ephemeral 写入尝试·理论应为 0）
- 敏感话题拒答次数 × 原因码分布
- PII 脱敏执行次数
- 用户删除请求执行状态（完成/超期）
- AIGC 标识覆盖率（结论总数 vs 已标注数）
```

---

## 九、诚实边界（当前保守拒绝 · 阈值待标定）

| 能力 | 当前状态 | 暂时边界 |
|------|---------|---------|
| ⚠️ 中文姓名 NER 召回精度 | ~85-90%，短文本偏低 | ephemeral 任务不依赖 NER 脱敏，整段丢弃（保守但安全）|
| ⚠️ AIGC 短文本检测 | <200 token 可靠性下降 | 标 `unknown` 不强判；S2 阶段接商业 API 提升精度 |
| ⚠️ 人物意图识别假阳性 | 企业名含人名（"张伟科技"）可能误判为人物 OSINT | 当前宁可误判 ephemeral（保守）；S2 精调意图分类器 |
| ⚠️ PIPL 出境判定 | 用户是否为中国公民的判定依赖 hub identity 属性，hub 未完全标注 | S1 阶段：凡涉及中文个人信息的查询一律按出境风险处理（保守）|
| ⚠️ 监测订阅人物识别 | `classify_subscription_target` 对复杂目标（"X 公司 CEO"）的人物识别不稳定 | 当前：含人名词的订阅目标一律标 ephemeral_mode=true |
| ⚠️ 敏感拼装自动检测 | 无机器学习模型判断"是否构成人物背调" | 当前：task_type 枚举硬判（黑名单）；灰色区域人工审核（S3 阶段） |

---

## 十、与现有文档接口

| 接面文档 | 本文依赖/关系 |
|---------|-------------|
| [数据脊柱](probe-data-persistence-and-cache-design-v1.0.md) | `persist_policy`·`expires_at`·DB 表结构真源；本文定策略，脊柱定字段 |
| [feasibility §5](../4-research/probe-github-datasource-feasibility-v1.md) | 红线口径真源；本文工程落地不改口径 |
| [audit-system](probe-audit-system-v1.md) | 8 闸与合规审计物理共享 `probe_audit_trace`；闸3 是 AIGC 标识的执行点 |
| [orchestration-engine-solution](probe-orchestration-engine-solution-v1.0.md) | 编排器需在扇出计划前调用 `fanout_trim()`（§五）；意图阶段判定插入编排入口 |
| [source-selection-registry](probe-source-selection-and-capability-registry-v1.0.md) | source_registry 提供 `supports_instant_query` · `data_category` 字段（供 persist_policy 判定和最小必要裁剪） |
| [monitoring-radar](probe-data-dynamic-governance-design-v1.0.md) | B6/C4 监测订阅的 `ephemeral_mode` 策略（§三.3.2）与监测雷达设计联动 |

---

> 落盘路径：`/Users/metafo/Downloads/metafoclaw/probe/docs/3-build/probe-privacy-retention-compliance-engineering-v1.0.md`
> 性质：闭缺口 #3 · 待并入 master-solution-v2 §七（合规与数据治理节）
