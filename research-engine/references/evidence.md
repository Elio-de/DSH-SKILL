# 证据、可信度、冲突与时效（M06 证据管理 / M07 验证）

> 职责：证据字段与强度、结论可信度判据、交叉验证、冲突六维归因、时效规则、写入边界。
> 适用：S9–S11、变更请求。不适用：来源评级（`sources.md`）、报告写法（`delivery.md`）。

## 1. 三层结构与关系

```text
source（S-###）  ──1:N──▶  evidence（E-###）  ──N:M──▶  conclusion（C-##）
   rating S/A/B/C/D          strength/status          confidence 高/中/低/未确定
   tier 1/2/3                depth primary/fulltext/snippet   verification 三档
```

**可追溯链**：结论 → `evidenceIds` → `sourceId` → `source.url` + 版本/时间。断链必须为 0（G4 阻断）。

## 2. 证据字段（必填见 Schema）

| 字段 | 必填 | 要求 |
|---|:--:|---|
| `id` | 是 | `E-###` |
| `sourceId` | 是 | 指向 `sources[].id`（R1） |
| `claim` | 是 | 该证据支持的具体断言，**不是**资料标题 |
| `quote` | 是 | 原文摘录，必须能在来源中定位 |
| `locator` | 是 | 章节/标题/行号/代码位置，空则不得入链 |
| `depth` | 是 | `primary` / `fulltext` / `snippet` |
| `strength` | 是 | `strong` / `medium` / `weak` |
| `status` | 是 | `verified` / `disputed` / `unverified` / `stale` |
| `accessedAt` | 是 | 抓取时间（ISO 8601 带时区） |
| `dataKind` | 数据类必填 | `measured` / `estimated` / `modeled` / `reported` |
| `publishedAt` / `version` | 否 | 资料时间/版本；缺失时报告提示 |

## 3. 强度判据

| 强度 | 判据 |
|---|---|
| strong | 一手/全文、可直接核验、与结论直接对应、时效有效 |
| medium | 全文但二手；或一手但需推断；或时效接近边界 |
| weak | 仅摘要/片段；间接支持；来源层级低；时效存疑 |

`depth = snippet` 的证据**不得**单独支撑"高"可信结论。

## 4. 结论可信度 FR-032（四级，禁止数值）

| 等级 | 判据 |
|---|---|
| 高 | ≥2 条独立 S/A 证据，方向一致，无重大冲突，时效有效 |
| 中 | 1 条 S/A + 1 条 B，或 2 条 A 但有覆盖缺口；或单一 S 来源 |
| 低 | 仅 B/C 级证据；或来源单一但可核验；或存在 `unresolved` 冲突 |
| 未确定 | 证据不足；证据相互矛盾未解决；关键前提是假设 |

**硬规则**：不得出现 `0.87` 之类数值；"高"必须能被第三方点开证据复核。

## 5. 交叉验证 FR-033

| 严谨度 | 要求 | `verification` |
|---|---|---|
| L1 | 关键事实 ≥1 条可核验来源 | `single-source` |
| L2 | 每个关键结论 ≥2 条**独立**来源 | `cross-checked` |
| L3 | ≥2 条独立、其中 ≥1 条一手；时间一致性；反方检索 | `primary-traced` |

独立性见 `sources.md` §5。同一来源族的两条证据**不算**交叉验证。

## 6. 冲突六维归因 FR-034 / FR-035

`conflicts[]` 字段：`id`（`X-##`）、`conclusionIds[]`、`positionA{evidenceIds, statement}`、`positionB{...}`、`attribution{version, scope, timing, primaryBasis, statisticalCaliber, cause}`、`status`（`resolved`/`unresolved`）、`resolution`、`impact`。

| 维度 | 要问的问题 |
|---|---|
| version | 是否两版本文档的差异？ |
| scope | 适用范围是否不同（型号/地区/场景）？ |
| timing | 发布时间先后是否解释差异？ |
| primaryBasis | 双方是否引用同一原始依据？ |
| statisticalCaliber | 统计口径/单位是否不同？ |
| cause | 上述都不成立时，最可能的原因是什么？ |

**处置**：能归因 → `resolved` 并写 `resolution`；不能 → `unresolved`，并列陈述，结论可信度 **≤ 低**，摘要必须提示。**不得**直接选"更新的那版"。

## 7. 时效与版本 FR-036

| 对象 | 必查 |
|---|---|
| 技术资料 | 数据手册版本、勘误（errata）、工具链版本、适用温度/功耗条件 |
| 软件/库 | 主版本区间、发布日、破坏性变更、维护状态 |
| 标准/政策 | 版本号、生效日期、修订记录、是否被替代 |
| 数据统计 | 统计期、发布滞后、口径 |

发现风险 → `evidence[].status = stale` + 写 `log.staleWarnings[]`（`{at, sourceId, issue}`）+ 报告"不确定性"章节提示。**过期证据不得作为当前结论的唯一依据。**

## 8. 证据写入边界（M06 唯一写入口，R2-02/R3-03）

| 谁 | 能做什么 |
|---|---|
| M04/M05/M09/M10 | 提交**证据候选** |
| M07（验证） | 提交**变更请求**（改状态/强度/可信度），**不直接写** |
| M11（审查） | 直接写自有数据 `counterResearch[]`/`qualityReview`/`limitations[]`；证据/结论状态只提交变更请求 |
| M06 | 校验后**应用**候选与变更请求，并在 `research-log.md` 记变更应用记录 |
| M12 | 只读；发现不一致 → 提交变更请求 |

**变更请求格式**：`{targetType, targetId, field, from, to, reason, evidenceRef}`。M06 校验：目标存在、字段可改、来源模块合法、与既有证据不矛盾。

> **说明**：变更应用记录属于**过程审计**，写在 `research-log.md`（不进入 `research_result.json` 契约字段；Schema 无 `changeApplied`）。

> **诚实边界**：以上是**逻辑与流程约束**，不是文件系统级隔离；无法阻止故意绕过，只能事后检测（编号扫描、引用完整性、文件时间戳与 CHANGELOG 比对）。

**语义校验口径**：证据链完整性按 R1–R12 执行（细则见 `delivery.md` §4）。其中 R11（九类数组内 ID 唯一）**必须在原始数组上做频次统计**，不得先转集合；R12（ID 前缀）按固定映射表逐条判定。

## 9. 反例

- 关键结论只有 1 条证据却标"高"→ 违规。
- 冲突双方证据都标 `verified` 且强度相同、却不作说明 → 违规。
- 用 2023 年的旧页面支撑"当前版本行为"→ 必须标 stale 并降级。
- 把 `snippet` 当 `primary` 使用 → 违规。
- M07 直接改写 `evidence[].status` → 职责越界。