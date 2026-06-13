# probe 新增行业（垂直赛道）对接 SOP v1.3

> 日期：2026-06-13 · 定位：把「在 probe 增加一个行业并对接进去」的全流程收敛成一份**可执行 checklist**。
> 真源依据：[track-registry v1.1](probe-track-registry-architecture-v1.0.md)（分类/权重/展示）· [compliance-gates v1.1](probe-compliance-gates-v1.md)（准入门）· `app/datasources/ledger.yaml`（赛道/域/源 单一真源）· [SSOT 仲裁](../records/probe-ssot-master-reconciliation-v1.0.md)。
> 一句话铁律：**加赛道 = 改数据不改架构**。代码量集中在「数据源适配器」，赛道本身只是 ledger 里加一条。
> **v1.1（2026-06-13）**：经「医药 J-pharma」全流程实跑硬化，补 5 处实战教训（正文标 🔬）。
> **v1.2（2026-06-13）**：新增**第 3.5 步「赛道分解矩阵」**——先分解后找源，端口×品类树驱动 API 广度覆盖；附 C 给可复用 `_matrix.yaml` 模板。
> **v1.3（2026-06-13）**：第 4 步新增 **4.1.5「付费源 → 免费平替/自动获取探查」R1 前置门**——命中付费 API 必先跑免费平替探查（开源 API 目录/开源项目采集层/合规自动获取），无果才升 R1；第 9 步自检门同步加该判据。

---

## 依赖序（先后不能乱 · 实跑验证）

```
0 立项 → 1 命名 → 2 信息域 → 3 合规门 → 3.5 分解矩阵 → 4 数据源 ─┐
                                          (端口×品类树)  (逐格填源) ├→ 5 注册(依赖2/3/4) → 6 细化深挖 → 7 展示 → 8 inventory → 9 自检门
                                                                  ┘
```

> 🔬 **顺序铁律（v1.2 修正）**：分解(3.5)**前置于**找源(4)。先画出「端口×品类树」覆盖矩阵 → 矩阵的每个格子就是一个 API 蹲位 → 找源是「逐格填空」，缺口一眼可见。**先找源后分解 = 广度靠运气；先分解后找源 = 广度靠清单。**
> 🔬 第 5 步「注册赛道」引用第 2、3 步产物，**2、3 必须先于 5**，第 5 步内置防悬空守卫。

---

## 0. 先判定：这个行业要不要做成独立赛道？（EG 式触发门）

不是每个行业都该升为独立 `vertical` 赛道。先过下面四问，**任一命中才升级**，否则挂在已有 horizontal 业务域（A–E）下当一个 `capabilities` 即可：

| 触发条件 | 含义 |
|----------|------|
| ① 专属信息域 | 该行业有 A–E 通用域覆盖不到的专属数据（如金融的行情 D13、元惠的促销 D15、医药的药械 D18） |
| ② 专属合规边界 | 有自己的法律/平台 ToS 红线，需独立 `verify_profile`（如任务系统的灰产防火墙、医药的健康敏感） |
| ③ 独立商业模式 | 变现方式不同于平台统一档位（如 CPS 返利、按件交付） |
| ④ 成套打包价值 | 把多个横向能力打包成「行业解决方案」，价值高于单一能力 |

**输出**：一句话立项结论 + 命中的触发条件 → 提交元东方拍板 `status: incubating`。

---

## 1. 命名登记（商业命名轨）

- 英文对外名 `Meta` + 能力词（如 `MetaXxx`）+ 中文俗名，**双名并存**。
- 写入 `asset-registry`（英文名 + 中文俗名两字段），走商业命名轨（metafoclaw 名下一切走此轨）。
- 文案禁用语自检：禁「元帅」一律 metafo；内部哲学话术不对外。

**判据**：asset-registry 两字段齐全，缺一不可。

---

## 2. 信息域落真源（消除悬空引用）

赛道 `owned/shared` 引用的每个 `D*` 必须先在 `ledger.yaml` `domains:` 段有定义（当前已落 D1–D18）。

- 若该行业需要**全新信息域** → 先在 `domains:` 加 `Dxx: "域语义"`，再被赛道引用。
- 若复用现有域 → 直接引用，不复制。

> 🔬 **实跑教训（域语义广度）**：定义新域时，语义要**一次覆盖赛道未来全部子领域**（按第 3.5 步的端口 × 品类树预想），否则后续返工扩语义。医药 D18 初版只写「药械情报」太窄，漏了医院诊疗/保健品/中医 → 应一步到位写「大健康（药品·器械·医院·保健品·中西医）」。

**判据**：赛道引用的所有 `D*` 在 `domains:` 段可查到；无悬空引用；域语义覆盖该赛道全部子领域。
**改码量**：0（YAML 加行）。

---

## 3. 合规门建档（准入前必过 · 必须先于第 5 步）

新赛道立项前必须有一个 `verify_profile`（合规门 profile），**实际落档**到 [compliance-gates](probe-compliance-gates-v1.md) 成一节，含三件：①准入五问 ②红线清单 `redlines[]` ③排除品类 `exclude_categories[]`。

**赛道准入合规门五问（全过才允许 `incubating→building`）**：
1. 数据是否公开合规获取（非代爬）？
2. 是否存在为违规行为导流的风险？
3. 个保法（PIPL）最小必要？
4. 是否触碰持牌/资质红线？
5. `exclude_categories` 是否已在品类层落标记？

> 🔬 **实跑教训（合规分级到品类）**：合规风险高的行业，`exclude_categories` 要**下沉到第 3.5 步品类树的每个叶子**分别裁定，不能只在赛道层一句带过。医药案例：保健品（虚假功效/蓝帽子）、中医（虚假神医偏方）、医院（号源黄牛/莆田系）、医美 风险各异，须逐品类进黑名单。

**判据**：compliance-gates 文档**确有该 profile 节**（不是只在 ledger 引用了 id）；五问逐项 ✅ + 证据。
**关联**：Guardian 引擎在「选源预检」时读此门挡掉不合规候选源。

---

## 3.5 赛道分解矩阵（端口 × 品类树 → API 覆盖清单 · v1.2 新增 · 找源的前置地图）

**目的**：在找源之前，先把赛道分解成一张**覆盖矩阵**，让 API 广度从「碰运气」变成「清单驱动」。这是支柱①「数据源越专越不可替代」的工程落地。

### 3.5.1 两个生长操作（分解 = 在品类树上反复做这两件事）

| 操作 | 方向 | 作用 | 医药例子 |
|------|------|------|---------|
| **加平级（兄弟节点）** | 横向 → **广度** | 同层多铺品类，扩 API 覆盖面 | 西医 ▸ 旁加 中医 / 医院 / 保健品 / 医美 / 口腔 / 康复 |
| **加下级（子节点）** | 纵向 ↓ **深度** | 把品类下钻成子类，扩专业度、精准匹配专业源 | 中医 → 中药 / 针灸 / 推拿；中药 → 中药材 / 中成药 / 处方中药 / OTC |

> 这两个操作正好对应 track-registry 已有的**三级目录（目录→分类→品类）**：**下级** = 顺着三级往下钻（树的深度链）；**平级** = 在每一层多挂兄弟节点（树的宽度）。

### 3.5.2 矩阵 = 端口（行） × 品类树叶子（列）

覆盖单元 = **叶子节点 × 端口**。8 端口（情报机制，按 track-registry §4 该行业定制）打头，品类树叶子做列：

```
                 西医    中医▸中药材  中医▸针灸  医院▸公立  保健品   医美
端口①审批资质     openFDA  药智网(R1)   器械注册   卫健委    蓝帽子   ?
端口②安全风险     openFDA  ?            ?          莆田名单  ?        ?
端口③疗效证据     PubMed   古籍方证?    临床循证   ?         ?        ?
...（8 端口）
```

- **每个格子**：要么填 ≥1 候选源（标 status），要么显式标 `gap`（缺口）。
- **加一个平级品类** → 凭空多出 8 个新蹲位（×8 端口）→ 广度 +1 层。
- **加一个下级子类** → 把粗蹲位裂成 N 个精准蹲位 → 挂更专业的源 → 深度/专业度 +1 层。
- **持续生长**：赛道上线后发现新平台/新细分，继续往树上加节点补源（对应「源的源」思路），矩阵永远是活的。

### 3.5.3 落盘：建 `_matrix.yaml` 骨架（模板见附 C）

- 路径：`metafoclaw-git/docs/engines/probe/1-inventory/<track>/_matrix.yaml`（机器可读，喂引擎 + 第 8 步同一文件，此处建骨架、第 4 步填充）。
- 同时落人读版 `ports/*.md`（逐端口逐叶子记真实平台）。

**判据**：① 品类树 ≥2 层（有平级铺开 + 有下级下钻）；② 矩阵每个格子要么有候选源、要么显式标 `gap`；③ `_matrix.yaml` 骨架已建。**禁留隐性空白格（看不见的缺口）。**
**改码量**：0（YAML/MD 文档）。

---

## 4. 数据源对接（逐格填矩阵 · gate19 逐源核验）

行业价值 = 喂给它的信息域有多专业/全/真。**按第 3.5 步矩阵的格子逐个找源、填空**：

### 4.1 候选源盘点 → 选型（矩阵驱动）
- **遍历矩阵每个 `gap` 格子**，为它找候选源：官方 API 优先 > 合规商业 API > 公开数据。
- 选型若命中**付费 API**，先走 4.1.5「免费平替探查」，证实无免费方案才升 R1。
- 禁逆向/抓包/模拟登录/群控/换代理对抗（数据来源铁律）。

### 4.1.5 付费源命中 → 免费平替/自动获取探查（R1 前置门）
**触发**：4.1 选型时某格子的最优候选是**付费 API**（命中 R1）。
**铁律**：付费源接入前**必须先跑一轮免费平替探查**，证实确无免费方案才升 R1 报价——禁不探查就直接拿付费源占格子（省 R1 成本 + 降单点供应商依赖）。

**探查顺序**（择优命中即停 · 全程守上面数据来源铁律）：
1. **开源/公共 API 目录**：`public-apis`、GitHub `awesome-*` 清单、RapidAPI 免费档、各国 open data portal（data.gov 类）、官方开放数据门户 → 找同信息域的免费官方/开放 API。
2. **开源项目自带采集层**：GitHub 搜该领域开源项目（如 akshare/tushare 这类已封装免费数据接口的库）→ 借鉴其封装的免费端点/适配器思路（**借鉴非照搬**，license 合规、不引入 copyleft 污染）。
3. **合规自动获取方案**：仅限**公开页面 + 官方导出/RSS/sitemap/开放数据集**，遵守 robots.txt 与 ToS。**禁逆向/抓包/模拟登录/群控/换代理**（同数据来源铁律，自动获取不得越线）。

**落盘判定**：
- 找到免费平替 → 该格子按免费源走 4.3/4.4，`status` 升 `live`，**零 R1**（最快路径，见 4.4 教训）。
- 探查无果（确无免费方案）→ ledger 该源条目标 `gap_paid` + 备注「已探免费平替无果（探查范围：目录/开源项目/合规自动获取）」→ 才升 R1（见 4.4 line「付费源命中 R1」）。

> 🔬 **实跑印证**：J 医药赛道 openFDA/ClinicalTrials/PubChem/PubMed 均为**免费官方 API**，直接填满审批资质/疗效证据/成分溯源多格，零 R1 升 live；仅 NMPA 无 API、且免费平替无果 → 才转商业源（药智网/米内网 R1）。**先探免费、后报付费**是该赛道 90% 格子零成本上线的关键。

**判据**：每个**付费源条目必须带「免费平替探查结论」**（找到平替 / 探查无果二选一），**禁跳过本门直接升 R1**。

### 4.2 逐源过标准19核验（gate19）
ledger `sources.<id>.gate19` 七维必查：`mature / verified / data_authentic / vendor_qualified / authorized / license_ok / security_ok`。

> 🔬 **实跑教训（verified 必须实测）**：`verified` 维度 = **真用 curl 打一次端点、确认返回有效数据**，不是填了 `api_base` URL 就算。医药案例：openFDA/ClinicalTrials/PubChem/PubMed 实测 HTTP200 + 抓到 `total`/`studies`/`CID2244` 才标 verified✅；NMPA 实测只有 HTML 首页、无 API → verified❌ 转商业源。**未实测的端点禁标 verified。**

### 4.3 写适配器模块
1. 复制 `app/datasources/_template.py` → 改名实现（参照 `tikhub.py` / `public/wikipedia.py`）。
2. 免费官方源放 `app/datasources/public/<id>.py`；商业授权源放 `app/datasources/<id>.py`。
3. 在 `app/datasources/registry.py` 的 `_ADAPTERS` 注册（商业源）。

### 4.4 登 ledger.yaml `sources:` 段 + 回填矩阵
每源必填：`domain / access_type / method / authority_score / freshness / cost / license / status`；同时把源回填到 `_matrix.yaml` 对应格子。

> 🔬 **实跑教训（cataloged ≠ 接入）**：`status` 三态分明——
> - `cataloged`＝**只登记占位、模块未写、不能调用**（登台账≠接入，别当完成）；
> - `pending`＝模块/凭据就绪，待 key；
> - `live`＝模块已写 + 实测可调用。
> **免费无 key 的官方源（如 openFDA/ClinicalTrials/PubChem）写完适配器即可零成本升 live，不触 R1/R8**——这是最快让赛道真能跑的路径，优先做。

- 付费源命中 **R1**：先出报价清单 → 元东方密码授权 → 才接。
- 含 key 命中 **R8**：真值入 `~/vault/credentials/`，仓内 `PLACEHOLDER`。

**判据**：① 至少 1 个源 **`status: live`**（cataloged 不算）喂该赛道的 owned 域；② **矩阵覆盖率达标**（核心端口×主品类无遗漏；剩余 `gap` 已显式标注为「待 R1」或「无源」，不留隐性空白）；③ 付费/带 key 源已过 R1/R8。
**改码量**：每源约 1 个适配器文件 + 1 段 ledger 条目 + 矩阵回填。

---

## 5. 赛道注册（ledger.yaml `tracks:` 段 · 核心一步）

在 `tracks:` 加一条，字段来自 track-registry §2 schema：

```yaml
  X-yourtrack: { type: vertical, tier: flagship, weight: 72, status: incubating,
                 intent: <意图终点>, owned: [Dxx], shared: [Dyy],
                 verify_profile: <第3步已建档的门 id> }
```

- `type`：`vertical`（垂直行业）/ `horizontal`（通用业务域）。
- `tier`：`standard` / `flagship` / `incubating`。
- `weight`（0–100）：**必走四维打分卡**，禁拍脑袋 → `客单价潜力(0-25) + 需求频次规模(0-25) + 合规可控度(0-25) + 数据护城河(0-25)`。
  > 🔬 **实跑教训（合规反向压权重）**：合规可控度低会直接拉低 weight，让风险反向约束资源倾斜。医药因健康敏感、合规可控仅 14/25 → weight=72，低于 F90/G85/H80/I82，符合预期。
- `intent`（= primary_intent）：意图终点，用于串台裁定，避免与已有赛道重叠双算（见 track-registry §8.2）。
- `status`：与 tier 正交的生命周期 `incubating→building→active→paused→deprecated→retired`。

**防悬空守卫（注册前必查）**：① `owned/shared` 的每个 `D*` 已在第 2 步落 `domains:`；② `verify_profile` 指向的门已在第 3 步**落档到 compliance-gates**（不是只写了个 id）。

**注册后实测验证（实跑可用 · 直接套用）**：
```bash
cd ~/Downloads/metafoclaw/probe && python3 -c "
from app.datasources import catalog; catalog.reload()
print('v', catalog.ledger_version(), '| domains', len(catalog.list_domains()))
print('new track:', __import__('yaml').safe_load(open('app/datasources/ledger.yaml').read())['tracks'].get('X-yourtrack'))
print('owned域的live源:', [s['id'] for s in catalog.list_sources(domain='Dxx', status='live')])
"
```

**判据**：ledger 加载无报错（YAML 合法 + `catalog` 可查）；weight 有打分卡支撑；intent 不与现有赛道冲突；防悬空两查全过。
**改码量**：0（YAML 加一条）。

---

## 6.（旗舰专属）细化深挖：端口定制 × 品类树细化 × 专属验证闸

第 3.5 步已搭好「端口 × 品类树」骨架；本步做**细化与定制**（仅 `tier: flagship`）：
- **8 端口定制**：把通用端口名替换为该行业的真实情报机制（参照 track-registry §4 G 元惠 / H 任务）。
- **品类树继续下钻**：对高价值叶子继续「加下级」到可对接专业 API 的粒度。
- **专属验证闸**：该行业的护城河校验（元惠「这优惠是不是真的」防虚标闸；医药「批准文号真伪」闸）。

> 🔬 **端口 ≠ 交叉轴/品类（最易错）**：
> - **端口 = 情报机制**（审批资质 / 安全风险 / 疗效证据 / 价格可及 / 机构服务 / 企业管线 / 成分溯源 / 政策监管）——跨子领域通用，8 个，是矩阵的**行**。
> - **品类树 = 领域分支**（中西医 / 药品·器械·医院·保健品·医美 …）——是矩阵的**列**，靠平级+下级生长。
> - **禁把品类当端口平铺**：把「中医/西医/医院/保健品」直接列成端口，会和「药品审批/不良事件」机制维度混在一起，采集与呈现都打架。
> - 定位法：一条真实情报 = **1 端口 × 品类树叶子 × 时效**。例：「某中成药批准文号真伪」= 端口①审批 × 中医▸中成药 × 静态。

standard 横向域跳过本步——它的「目录」= design-v1 §5.1 既有场景表的注册表视图。

---

## 7. 展示层接入（数据驱动 · 0 hardcode）

`tracks` 条目可带 `presentation` 段，UI 读字段渲染，复用现有 hub 底座，**不写死、不另起**：

| 需求 | 字段 | 复用底座 |
|------|------|---------|
| 徽标/置顶 | `badge` + `prominence` | HubBoard + `tokens-brand.css`（`--mfc-flagship`）|
| 暗示/组合推荐 | `hint.affordance` / `combo_hint` | 卡片角标 + MetaFlow |
| 提醒 | `reminders[]` | hub-whatsnew `changelog.json` |
| 快捷入口 | `quick_entry[]` | hub registry + 导航路由 + MetaFlow preset |

- 颜色禁内联硬编码 → 走 `tokens-brand.css` 真源 token。
- 仅 `status: active` 的赛道 `presentation` 才生效出快捷入口。

**判据**：UI 自动出徽标/入口，无新增硬编码色值；改动走 `publish-design.sh` 上 hub。

---

## 8. inventory 镜像层盘点（SSOT 合规）

赛道「真实平台/数据源家底」属现状盘点，落镜像层，**源层不复制**：
- 路径：`metafoclaw-git/docs/engines/probe/1-inventory/<track>/`，含 `ports/*.md`（逐端口逐叶子填）+ `_matrix.yaml`（即第 3.5 步建骨架、第 4 步填充的同一文件，此处做最终校对）。
- probe 源层 `docs/1-inventory/` 保持占位。

---

## 9. 上线自检门（status: incubating → building → active）

| 门 | 检查 |
|----|------|
| 命名 | asset-registry 双名齐全 |
| 信息域 | owned/shared 的 D* 全部落 domains 真源，无悬空；语义覆盖全子领域 |
| 合规门 | verify_profile **已落档 compliance-gates**（非仅 id）+ 准入五问全过 + 品类级 exclude |
| **分解矩阵** | 品类树 ≥2 层（平级+下级）；矩阵无隐性空白格（缺口已显式标注）|
| 数据源 | ≥1 源 **live**（cataloged 不算）喂 owned 域；矩阵覆盖率达标；**付费源均带「免费平替探查结论」**（4.1.5）；付费/key 源过 R1/R8 |
| 注册 | ledger tracks 加载无错；weight 有打分卡；intent 不串台；防悬空两查过 |
| 自检 | `GET /selftest` 的 `double_helix` 两轴真实派生（非硬编码）通过 |
| 展示 | presentation 数据驱动，0 hardcode 色值 |

全绿 → 元东方拍板推进 status 升级。

---

## 附 A：最小路径 vs 完整路径

- **挂 horizontal 域下做 capability**（最轻）：第 2 + 4 步即可，不新增赛道。
- **新增 standard 垂直赛道**：第 0–5 + 7–9 步，跳过 3.5/6 深挖（用 §5.1 场景表）。
- **新增 flagship 旗舰赛道**：全 0–9 步（含 3.5 分解矩阵 + 6 细化深挖）。

**关键认知**：90% 的工作量在第 4 步（数据源对接 + gate19 + R1/R8 授权），但**广度由第 3.5 步矩阵决定**；第 5 步赛道注册本身是 0 改码的 YAML 一行。

## 附 B：实跑案例（J 医药 · 本 SOP 的 worked example）

- 第 2 步：`ledger.yaml` 加 `D18 医药与健康`。
- 第 3 步：`compliance-gates` 加 `pharma-compliance-gate`（与任务 H 并列最高合规等级）。
- 第 3.5 步：端口（审批资质…政策监管 8 个）× 品类树（西医 / 中医▸中药▸中药材·针灸 / 医院▸公立·民营 / 保健品 / 医美）→ 覆盖矩阵。
- 第 4 步：openFDA/ClinicalTrials/PubChem/PubMed 端点实测 verified✅（cataloged，模块待写）；NMPA 无 API 转商业源（药智网/米内网 R1）填中药材/批准文号格子。
- 第 5 步：`tracks` 加 `J-pharma`（vertical/flagship/weight 72/owned D18）。
- 验证：`catalog.reload()` → v9 / 18 域 / J-pharma 就位、YAML 合法。
- 印证铁律：全程**只改 ledger + 文档，0 行 Python 即把赛道接进去**。

## 附 C：`_matrix.yaml` 可复用模板（第 3.5 步建骨架 · 直接拷改）

```yaml
# probe 赛道覆盖矩阵 · <track-id>
# 端口(行) × 品类树叶子(列) → 每个叶子格子 = 一个 API 蹲位
# 路径: metafoclaw-git/docs/engines/probe/1-inventory/<track>/_matrix.yaml
track: J-pharma
ports:                       # 8 端口 = 情报机制(矩阵的行) · 按 track-registry §4 定制
  - 审批资质
  - 安全风险
  - 疗效证据
  - 价格可及
  - 机构服务
  - 企业管线
  - 成分溯源
  - 政策监管
category_tree:               # 品类树(矩阵的列) · 平级=兄弟 / 下级=缩进子节点
  西医: {}
  中医:
    中药: [中药材, 中成药, 处方中药, OTC中药]
    针灸: []
    推拿: []
  医院:
    公立: []
    民营: []
  保健品: {}
  医美: {}
coverage:                    # 叶子 × 端口 → 源/状态;第 4 步逐格回填
  - { port: 审批资质, leaf: 西医,            source: openFDA,  status: verified }   # 端点实测✅·模块待写
  - { port: 审批资质, leaf: 中医/中药/中药材, source: 药智网,    status: gap_paid }   # 待 R1 授权
  - { port: 安全风险, leaf: 西医,            source: openFDA,  status: verified }
  - { port: 疗效证据, leaf: 西医,            source: PubMed,   status: verified }
  # ... 逐格填到核心端口×主品类无遗漏
gaps:                        # 自动汇总未覆盖格子(广度缺口·禁隐性空白)
  - { port: 安全风险, leaf: 保健品, reason: 无公开源, plan: 待调研 }
```
