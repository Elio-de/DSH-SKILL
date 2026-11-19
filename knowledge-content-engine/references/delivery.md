# 交付、manifest、转换请求、交接包与版本

> 职责：定义产物布局、`doc_manifest.json` 生成、`delivery.md` 结构、转换请求（仅显式）、交接包、索引、版本与续写。
> 读取时机：S11；写 manifest/交付说明/交接文件前；修订或续写时。
> 不重复：契约字段清单以 SRS DATA-001～008 与 `schemas/doc_manifest.schema.json` 为准；本文给生成步骤。

## 1 产物布局

```text
content/<doc-slug>/
├── main.md                      # 正文（必需）
├── doc_manifest.json            # 机读契约（必需）
├── outline.md                   # 结构/大纲/规格/覆盖矩阵（必需）
├── sources.md                   # 来源台账（必需）
├── claims.md                    # 断言台账（必需）
├── glossary.md                  # 术语表（必需）
├── review.md                    # 自检/门禁/缺陷（必需）
├── delivery.md                  # 交付说明（必需）
├── INTERFACE.md                 # 只读边界与消费说明（必需）
├── CHANGELOG.md                 # 版本（必需）
├── exercises.md / answers.md    # B 模式默认
├── learn/main.md                # 混合派生件
├── history/                     # 历史版本（固定约定）
├── claims.json / sources.json   # manifest >48 KB 时按需分卷
├── assets/                      # .mmd、CSV、图表源（按需）
├── derived/                     # 下游派生（唯一可写区）
└── 按需：research-request.md / conversion-request.md / knowledge-handoff.md /
         review-request.md / interaction-brief.md / extraction-needs.md
```

- 根目录可由用户指定；相对结构不变。
- **混合模式**：主件在 `content/<doc-slug>/`，派生件在 `content/<doc-slug>/learn/` 并拥有**独立** `learn/doc_manifest.json`、`learn/outline.md`、`learn/claims.md` 等；主 manifest 的 `artifacts[]` 记 `{path:"learn/main.md", manifestPath:"learn/doc_manifest.json", mode:"M-LEARN"}`。两件各自校验、各自命名空间。
- 同 slug 不同 `docId` → `<slug>-v2` 递增；同 `docId` → 续写。
- 历史版本放 `history/`，当前版本在根。

**示例索引**（`examples/`）：`mini-doc/` 是**可运行**的最小文档示例（manifest + 必需文件齐全，validator 通过）；`learn-doc.example.md` 与 `tech-doc.example.md` 是格式片段，不是完整产物。

## 2 manifest 生成

**第一步：读契约**。生成前必须读 `schemas/doc_manifest.schema.json`；字段形状以 schema 为准，本文只给生成顺序与要点。`scripts/validate_manifest.py` 读取同一 schema 校验。

1. 从 `brief`、`mode`、`docType` 初始化 `meta`。
2. 写入 `structure`、`coverageMatrix`、`prerequisiteGraph`（B）、`sources`、`claims`、`citations`、`exercises`、`glossary`、`conflicts`、`limitations`、`assumptions`、`incomplete`、`openQuestions`、`risks`、`review`、`artifacts`、`changelog`、`log`。
3. 计算 `meta.completion` 与 `meta.budget.used`。
4. 生成后运行 `scripts/validate_manifest.py`；失败按 §10 修复，**不得跳过或虚报**。
5. 超过 48 KB：`claims`→`claims.json`、`sources`→`sources.json`，manifest 保留索引与 `volumes`。

**必填**：`schemaVersion`、`docId`、`meta`（title/version/createdAt/updatedAt/detailLevel/language/completion/budget/configSources/capabilities）、`brief`（purpose/audience/scope/deliverableFormat/sourcePolicy/successCriteria/constraints）、`mode`、`docType`、`structure`、`coverageMatrix`、`sources`、`claims`、`citations`、`exercises`、`glossary`、`conflicts`、`limitations`、`assumptions`、`incomplete`、`openQuestions`、`risks`、`review`（checklist/gates/defects/rounds）、`conversionRequests`、`knowledgeCandidates`、`artifacts`、`changelog`、`log`（preflight/timeline）。

**契约版本**：本版本固定 `schemaVersion: "1.1"`；`review`（checklist/gates/defects/rounds）与 `log`（preflight/timeline）结构化必填。`1.0` 为历史契约，本 Skill 不承诺兼容读取；旧 1.0 产物须迁移后再消费。

**形状要点（高频踩坑）**：

| 字段 | 形状 |
|---|---|
| `docId` | 字符串，`^DOC-\d{8}-\d{3}$` |
| `meta.version` | `MAJOR.MINOR` 两段式 |
| `docType` | 对象：`primaryType`、`types[]`、`profile`（主）、`profiles[]`（次，≤2） |
| `structure[]` | 对象：`id`（`CH-##`）、`title`、`level`、`purpose`、`acceptance`、`critical` 必填 |
| `coverageMatrix[]` | 对象：`target`、`sectionIds[]`、`status ∈ covered/partial/missing` |
| `incomplete[]` | 对象：`sectionId`、`reason` |
| `openQuestions[]` | 字符串，或对象 `{question, closed}` |
| `conflicts[]` | 对象：`id`、`positions[]`、`attribution{}`、`status`、`impact` |
| `citations[]` | 对象：`id`、`claimId`、`sourceId`、`kind`、`checked` |
| `glossary[]` | 对象：`term`、`definition`、`firstUse`、`translation` |
| `assumptions[]` | 对象：`id`、`statement`、`impact` |
| `artifacts[]` | 对象：`id`、`role`、`mode`、`path`、`completion` |
| `changelog[]` | 对象：`version`、`at`、`reason` |
| `mode` | 对象：`requested`、`primary`、`decidedBy` |
| `budget` | 对象：`tier`、`limits{}`、`used{}` |
| `risks[]` | 对象：`id`、`trigger`、`consequence`、`mitigation` |
| `conversionRequests[]` | 对象；`status` 见 §4 |
| `review` | 必填 `checklist[]`、`gates[]`、`defects[]`、`rounds` |
| `log` | 必填 `preflight{}`、`timeline[]` |
| `exercises[]` | 必填 `id`/`objectiveIds`/`sectionId`/`type`/`difficulty`/`question`/`requirement`（作答要求）/`answer`/`explanation` |

**练习豁免**：只有用户明确要求"不要练习/只要自测/精简版"时，才允许 `brief.constraints.exerciseExempt: true`（并在 `assumptions[]` 记原话）；否则 B 模式必须有 `exercises[]`，校验器会拒绝空练习。

**类型与 profile 一致性**：`types[]` 有 2 个类型时，`profiles[]` 至少写 1 个次 profile；`types` 与 `profile` 不得自相矛盾（如 types 含 teaching 类却给 A profile）。

**ID 命名空间**：`CL-##` 断言、`SRC-###` 来源、`CT-##` 引用、`EX-##` 练习、`CH-##` 章节、`OBJ-CHxx-n` 目标；S01 引用 `R-<researchId>/C-##`、`R-<researchId>/E-###`；冲突 `C-##` 独立。混合模式的两件产物**各自使用独立 manifest 与独立命名空间**，不共用 `CH-##`/`EX-##`。

## 3 delivery.md 结构

1. 产物清单与用途。
2. 阅读顺序。
3. 模式 / 档位 / 文档类型 / 版本 / `asOf`。
4. 能力边界：未生成格式、未验证项、未完成项。
5. 转换请求状态（没有则写"未请求转换"或省略）。
6. 下游交接说明（S03/S04/S10/S14/S15/S16；代码/测试交 `engineering-assistant`；交互 HTML 交 `offline-learning-html`）。
7. 质量结论：自检结果 + 引用完整性（声明"自检，非独立审查"）。
8. 版本与更新建议。

## 4 转换请求（仅显式）

**触发**：用户明确提出"把 Markdown 转成 DOCX/PPTX/PDF/其他格式"。
**默认**：不询问、不生成请求、不调用 office。

`conversionRequests[]` 字段：

| 字段 | 说明 |
|---|---|
| `id` | `CV-01` |
| `target` | docx/pptx/pdf/xlsx/mindmap/html |
| `sourceFiles[]` | 源 Markdown/资产 |
| `requirements` | 版式、章节映射、图表处理、公式、**期望页数/幻灯片数/图表数区间** |
| `priority` | high/normal/low |
| `status` | pending/in-progress/done/failed/unavailable/**retained** |
| `handler` | S03/office/S10/S15 |
| `executedBy` | none/S02-office/S03/S10/S15 |
| `reason` | 状态原因 |

**状态语义**：`done` = 已生成且已验证；`retained` = 已生成但本次不交付/仅保留在磁盘（例如用户只要 PDF，DOCX 仍保留）；`failed` = 尝试失败；`unavailable` = 能力缺失；`pending` = 未执行。

**部分交付**：多格式请求逐项记状态，不得用一项成功代表全部；未交付格式写清原因与磁盘位置。删除已生成文件需用户授权。

**执行与验证**：

1. **先加载 office 技能**（`skill({name:"office"})`），否则 `office_convert/office_render` 不可见；未加载时不得调用或误报"不可用"。
2. 探测 office 能力；未授权不执行。
3. 授权后执行；验证文件存在、大小 >0、可打开、页数/幻灯片数落在声明区间。
4. 通过 → `done`；失败 → `failed` + 原因；能力缺失 → `unavailable`。
5. 未执行保持 `pending`；不得写"已生成"；转换成功后必须更新 `delivery.md §5`、G6 与 `CHANGELOG.md`，并重跑 validator。

## 5 交接包

必需：`main.md`、`doc_manifest.json`、`delivery.md`、`outline.md`、`sources.md`、`claims.md`、`glossary.md`、`INTERFACE.md`、`CHANGELOG.md`、`review.md`；B 模式加 `exercises.md`/`answers.md`；混合加 `learn/main.md`；分卷时加分卷。

按需：`conversion-request.md`、`knowledge-handoff.md`、`review-request.md`、`interaction-brief.md`、`extraction-needs.md`、`assets/`、`research-request.md`。

**消费顺序**：校验 `schemaVersion` → `meta.completion` → `mode/docType` → `structure` → `claims/sources`（或分卷）→ 正文 → 过程看 `review.md`。

## 6 INTERFACE.md（只读边界）

- 只读：`sources.md`、`claims.md`、`CHANGELOG.md`、S01 产物；下游不得修改。
- 可写：本目录 `derived/`。
- 契约版本与降级：`schemaVersion` 不匹配 → 降级读 `main.md`/`delivery.md`。
- 修订请求：提出"新版本请求"，由本 Skill 生成新版本，不直接改旧文件。

## 7 索引

`content/_index.md`：主题、目录、模式、文档类型、版本、完成度、更新时间、状态。每次交付后更新。

## 8 版本与修订

- 版本：`vMAJOR.MINOR`，与 `meta.version` 一致。
- **用户原始文件只读**：修订他提供的文档时，先计算 SHA256 并快照到 `history/<原名>-v<旧版本>.md`；原件不覆盖。修改原件需用户明确授权。
- `CHANGELOG.md` 追加式：版本、时间、原因、变更条目（before/after/type）、影响章节、失效内容。
- 修订类型：勘误（最小改动）/版本升级（版本敏感内容）/重构（结构 + 映射表）/派生更新（同步派生件）。
- 失效内容：标 `stale`/`superseded`，保留并提示替代项；不删除。

## 9 续写

- 同 `docId`：读 manifest/outline，按 `structure[].id` 去重，续写未完成章节。
- 写 `log.resume`；重算完成度与门禁。
- manifest 不可解析：新建版本目录并说明，不覆盖。

## 10 校验脚本使用

```text
python <skill-base>/scripts/validate_manifest.py <doc_manifest.json> --dir <产物目录>
```

- 必须在技能基目录下运行或使用绝对路径；`<skill-base>` 为 SKILL.md 返回的 base directory。

- 退出码：0 通过；1 校验失败；2 输入/运行错误。
- 可选 `--report <path>` 输出 JSON 报告。
- 脚本不可用：按 `quality.md` 人工契约清单核对，并在 `delivery.md` 标注"契约未机器校验"。

**校验失败恢复**（最多 3 轮）：

1. 读第一条错误定位字段；错误按类修：**文件缺失 → 补产物文件**；结构/枚举 → 查 schema；引用 → 补台账或删引；ID → 查命名空间；体积 → 分卷；凭据 → 删除。
2. 每轮只改一类错误，重跑；**不得靠猜字段**，直接读 `schemas/doc_manifest.schema.json`。
3. 3 轮仍失败：停止修复，交付说明写"契约校验失败：<错误数> 项"，完成度降 `CMP-PART`，`limitations[]` 记录；不得写"已通过"。
4. **脚本只校验 manifest**；正文与台账的断链由 S9/`consistency.md` 检查，不能因脚本 PASS 就宣称正文无断链。

## 11 交付前检查表

| 检查 | 判据 |
|---|---|
| 文件齐全 | 必需文件均存在；B 模式练习/答案存在 |
| manifest | 可解析；脚本退出码 0（或已声明人工校验/失败披露） |
| 引用 | 正文与台账断链 0（S9 检查） |
| 完成度 | 与缺口一致 |
| 能力声明 | 未生成/未验证/不可用已声明 |
| 版本 | `CHANGELOG.md` 有记录；用户原件已快照 |
| 转换 | 未请求则不出现"已生成"；请求则逐项状态与文件一致 |
| 索引 | `content/_index.md` 已更新 |