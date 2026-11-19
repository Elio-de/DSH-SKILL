# 工作流程（S0–S11、门禁 G0–G6、回退与终止）

> 职责：定义每阶段的进入条件、动作、产出、失败处理、门禁与回退上限；维护预算与完成度判定。
> 读取时机：任何任务开始；判断"下一步做什么"；回退或终止时。
> 不重复：模式判定细则见 `mode-selection.md`；简报/澄清见 `intake.md`；清单见 `quality.md`。

## 1 阶段总表

| 阶段 | 名称 | 主责 | 进入条件 | 产出 | 门禁 |
|---|---|---|---|---|---|
| S0 | 预检 | M14 + M00 | 技能已加载 | capabilities、log.preflight、目录 | G0 |
| S1 | 受理 | M02 | G0 通过 | brief、sourcePolicy、gaps、assumptions | — |
| S2 | 模式与类型 | M01 + M04 | brief 就绪 | mode、docType、profile、artifacts | G1 |
| S3 | 资料就绪 | M03 | G1 通过 | sources、claims 草稿、资料处置 | — |
| S4 | 结构规划 | M04 | 资料可支撑 | structure、coverageMatrix、outline、planConfirmed | G2 |
| S5 | 章节规格 | M04 | G2 通过 | 每章 spec（目的/目标/断言计划/验收） | — |
| S6 | 分章编写 | M05 / M06 | 规格齐全 | main.md、exercises/answers（B） | — |
| S7 | 核验 | M07 → M03 | 章节草稿完成 | verification、conflicts、staleWarnings | G3 |
| S8 | 教学法审查（仅 B） | M08 | G3 通过 | cognitiveLoad、objectiveCoverage、readability | G4 |
| S9 | 一致性与格式 | M09 | S7/S8 完成 | glossary、编号/引用/格式检查 | — |
| S10 | 自检与缺陷 | M10 | S9 完成 | review、defects、完成度 | G5 |
| S11 | 交付 | M11 + M12 + M13 | G5 通过 | manifest、delivery、交接、版本 | G6（条件） |

## 2 S0 预检（G0）

1. 探测：`read`/`write`/`edit`/`glob`/`grep`、Web 读取、`read_image`、office（`office_status`）、子代理、`python`（校验器）、S01 产物可读性。
2. 准备输出目录：`content/<doc-slug>/`（根目录可由用户指定；不可写则用工作区临时目录并声明）。
3. 检测同名 `docId`：命中则读 `doc_manifest.json` 与 `outline.md`，进入续写（见 §8）。
4. 部署合规自查（仅首次安装/迁移时）：目录包为 `<root>/knowledge-content-engine/SKILL.md`（一层）、`name` 为 kebab-case、`description` ≤500 字符、迁移后仅一处可见副本。
5. 记录交互能力 `interactive`（能否向用户提问/请求确认）；无交互通道时置 `false`，后续提问与计划确认改为"假设 + 记录跳过理由"。
6. 写 `capabilities[]` 与 `log.preflight`。
7. **G0 通过**：文件写可用 + 输出目录就绪。文件写不可用 → 终止并说明；其他能力缺失 → 降级继续。

**能力缺失处理**：不阻断（除文件写），按 `collaboration.md` §能力降级表 记录并在交付说明声明。

## 3 S1 受理

按 `intake.md`：

1. 抽取 `brief` 九字段；无法抽取标 `unknown`。
2. 确定来源政策：`provided-only` / `provided+verify`（默认）/ `research-request`。
3. 识别交付形态；**只在用户明确说"转成 X 格式"时**记录转换意向。
4. 生成假设 `assumptions[]`、缺口 `gaps[]`；确需提问则合并 ≤3 个。
5. **无交互通道**：不提问；把关键缺失写成假设与 `openQuestions{closed:"no-channel"}`；若缺失会导致无法交付，直接进入降级并声明。
6. 写 `outline.md` 头部与 `log.timeline`。

**G1 在 S2 后判定**，S1 不设门禁。

## 4 S2 模式与文档类型（G1）

1. 按 `mode-selection.md` 判定模式；混合时拆分 `artifacts[]`（primary/derived）。
2. 按 `profiles/index.md` 识别文档类型与 profile（主类型 + 次类型，profile ≤2）。
3. 写 `mode`、`docType`、`profile` 到 manifest 草稿。
4. **G1 通过**：简报可用且 `purpose` **不是 unknown**（缺失时改写为可判定假设并登记，或直接降完成度）、模式有依据、档位明确、来源政策确定。失败 → 回 S1，最多 2 次。

## 5 S3 资料就绪

1. 登记素材来源（`SRC-###`），检查可读性；不可读记录原因并换通道或请用户导出。
2. 消费 S01：校验 16 项必填与 `schemaVersion`；按 `evidence.md` 的映射表转换后写入台账；只读，不改 S01。
3. 建立 `claims` 草稿（计划断言）与来源覆盖。
4. 缺口处置：用户补充 / `research-request.md` / 定向核验 / 标 `unverified`。
5. 缺口影响 critical 章节 → 回 S1 或明确降级。

## 6 S4 结构规划（G2）

1. 选 profile（≤2）并读取；构建 `structure[]`；`docType.profile` 记主 profile，次 profile 记入 `docType.profiles[]`。
2. 生成 `coverageMatrix[]`：行=目标/主题；列=章节/素材/练习；状态 covered/partial/missing。
3. 标记 `critical`：覆盖核心主题、关键参数/安全结论、后续章节根基或必学目标的章节为 critical；其余非 critical。至少 1 个 critical。
4. B 模式构建前置图，检查无环、无悬空、无自环。
5. 判断计划确认：C3 或手册/教材/规范/对外发布物 → 展示大纲与计划（目标、章节、依据、预算、风险、交付形态），取得确认或记录跳过理由；无交互通道则记录跳过。
6. **G2 通过**：结构完整、每章有 `acceptance`、critical 覆盖率 100%（`partial` 不计入 critical）、确认/跳过有记录。失败 → 回 S4，最多 2 次。

## 7 S5 章节规格

每章写 `spec`：

| 字段 | 要求 |
|---|---|
| id/title/level | 稳定编号；层级不跳级 |
| purpose | 本章解决什么问题 |
| objectives[] | B 模式 2–5 条，Bloom 动词 |
| claimsPlanned[] | 计划断言（可先占位为计划文字） |
| evidenceNeeded[] | 需要的资料类型 |
| exercises[] | B 模式默认每目标 ≥1 题的计划 |
| acceptance | 可判定的完成条件 |
| critical | 是否关键章节 |

规格先落盘再写正文。规格不足 → 回 S4。

## 8 S6 分章编写

1. 逐章循环：读 spec → 读台账片段 → 读模板 → 写作 → 本章自检 → 追加落盘 → 更新台账与日志。
2. A 模式按 `tech-doc.md`；B 模式按 `learning.md`；简化标 `[简化]`，类比标 `[类比]`。
3. 每章写完即落盘；不得把整章草稿留在对话。
4. 初稿完成进入 S7；发现结构问题回 S4，规格不足回 S5。

## 9 S7 核验（G3）

1. 抽取技术断言，写 `type` 与 `verification`。
2. 定向核验：单断言 ≤3 次读取；禁跨主题；超限转 `research-request.md`。
3. 冲突登记与归因；时效/版本检查；代码/命令状态；数据口径；引用完整性（断链 0）。
4. **G3 通过**（A）：技术断言可核验、参数/命令/版本齐全、断链 0；（B）：事实部分同标准。失败 → 回 S6 改写；仍不足标 `unverified` 并降完成度。

## 10 S8 教学法审查（仅 B，G4）

1. 认知负荷：单章新概念 ≤7；新概念首次出现给定义与例子。
2. 难度曲线：L1 记忆/理解 → L2 应用/分析 → L3 综合/评价，不倒退。
3. 目标-内容-练习对齐：每条目标有讲解位置与 ≥1 练习。
4. 可读性：中文单句 >80 字须拆分；抽 10 段能指出主题句。
5. **G4 通过**：对齐率 100%、前置无悬空、概念四要素齐全、答案完整。失败 → 回 S6。

## 11 S9 一致性与格式

按 `consistency.md`：术语表、术语一致、编号唯一、交叉引用断链 0、标题层级、代码块语言、表格表头、图表来源、公式变量、无结构性 HTML。缺陷 → 回 S6；机械问题可当场修正并记录。S9 结果供 S10 复用，不重复扫描。

## 12 S10 自检与缺陷（G5）

1. 按 `quality.md` 执行 A 清单（TQ）/ B 清单（LQ）/ 共享清单（SQ）。
2. 缺陷登记：Blocker / Major / Minor；修复 → 复审 → 回归。
3. 判定完成度（§14）与缺口。
4. **G5 通过**：全部清单项 ∈ {通过, 不适用}、缺陷闭环、术语/格式通过、完成度一致、审查轮次未超档位上限。有"受限"项 → G5=受限（不得记通过），完成度 ≤CMP-PART；失败 → 回 S6/S7；无法修复 → `residual[]` 与 `gateWaivers[]` 披露；轮次超限 → 终止并降级。

## 13 S11 交付（G6 条件）

1. 按 `delivery.md` 生成 `doc_manifest.json`（`schemaVersion=1.1`），运行 `scripts/validate_manifest.py`（退出码 0；不可用则人工清单 + 声明）。
2. 写 `delivery.md`、`INTERFACE.md`、`CHANGELOG.md`、索引与按需交接文件。
3. 转换：仅当用户明确提出时生成 `conversionRequests[]`；**先 `skill({name:"office"})` 激活 office**，可用且授权才执行；验证文件存在/可打开/指标在声明区间。否则不生成请求。
4. 更新 `content/_index.md`；必要时 `present`。
5. **G6（条件）**：请求字段完整；执行时产物可打开且指标在区间；失败置 `failed`/`unavailable` 并说明。

## 14 门禁汇总

| 门禁 | 位置 | 通过条件 | 失败处理 |
|---|---|---|---|
| G0 | S0 后 | 文件写可用 + 输出目录就绪 | 终止（文件写不可用）或降级 |
| G1 | S2 后 | 简报可用且 purpose 非 unknown、模式有依据、档位明确、来源政策确定 | 回 S1；≤2 次 |
| G2 | S4 后 | 结构完整、每章 acceptance、critical 覆盖 100%（partial 不计入 critical）、确认/跳过记录 | 回 S4；≤2 次 |
| G3 | S7 后 | 技术断言可核验、参数/命令/版本齐全（或 `[待提供]` 有缺口记录）、断链 0 | 回 S6；仍不足降级 |
| G4 | S8 后（B） | 对齐 100%、前置无悬空、概念四要素、答案完整 | 回 S6；≤2 次 |
| G5 | S10 后 | 全部清单项 ∈ {通过, 不适用}，缺陷闭环、术语/格式通过、完成度一致、轮次未超限 | 有"受限"项 → G5=受限（不得记通过），完成度≤CMP-PART；回 S6/S7；超限终止降级 |
| G6 | S11（条件） | 请求完整；产物可打开且指标在区间 | failed/unavailable + 说明 |

## 15 回退与重试

| 触发 | 目标 | 上限 | 记录 |
|---|---|---|---|
| 结构缺失/规格不足 | S4 | 2 | 缺陷 id + 原因 |
| 断言无依据/需改写 | S6 | 2 | 断言 id + 缺口 |
| 核验冲突不可归因 | S6（并列陈述） | 1 | conflicts |
| 教学缺陷 | S6 | 2 | defects |
| 术语/编号/格式缺陷 | S6 | 2 | defects |
| 自检 Blocker | S6 或 S7 | 2 | defects |
| 资料缺口需补充 | S1 | 1 | gaps |
| 审查轮次超限 | 终止 | — | 降完成度 + 披露 |

同一缺陷连续 2 次修复失败 → 不得继续循环；降完成度、记 `residual[]`、在交付说明披露。

**重试语义**：`上限=2` 指"首次失败后可再试 2 次"；**连续 2 次失败即降级**（不要求凑满预算）。外部约束导致资料根本不存在/不可达时，**首次即可降级**并记录，不强制重试；重试必须有新依据或新通道，不得原样重复。

**无交互通道**下，计划确认/预算上调不可执行：按默认假设继续并记录；若缺口影响 critical → 直接 `CMP-LIMITED`。

## 16 预算（承接 FR-012）

| 预算档 | 资料读取 | 定向核验（检索+读取） | 章节数 | 审查轮次 | 适用 |
|---|---:|---:|---:|---:|---|
| 轻量 C1 | 10 | 5 | 8 | 1 | 速览、科普 |
| 标准 C2 | 25 | 15 | 15 | 2 | 常规文档/讲义 |
| 完整 C3 | 50 | 30 | 20 | 3 | 手册/教材/多章 |

- 计数：一次 `web_search`/`search.run` = 1 检索；一次 `web_fetch`/`read.fetch` = 1 读取；文件读写不计入（另受 NFR-002：读取 ≤ 章节数×3、写文件 ≤ 交付物数+章节数）。
- 80% 预警一次；任一 limit 触顶即终止或申请上调（记录）。
- 耗时建议（非硬性）：C1 ≤10 分钟、C2 ≤30 分钟、C3 ≤60 分钟；超时说明原因。
- **篇幅建议（正文，非硬性）**：C1 300–800 字；C2 1,500–4,000 字；C3 ≥4,000 字。手册/教材可按章节拆分，单章 ≤3,000 字为宜；用户或测试另有限制时从其限制并记录。
- 篇幅与行内标注冲突时：先保关键断言标注与必需章节，再压缩叙述；不得为压篇幅删验证状态/风险/引用。

## 17 终止条件与完成度

**终止条件（命中任一）**：全部 critical 章节达标；连续 2 轮核验无新增依据；任一预算 limit 触顶；关键资料不可达且已按 §15 降级（外部约束首次即可）；用户要求停止。

| 完成度 | 判据 | 必附 |
|---|---|---|
| CMP-DONE | 全部 critical 达标 + G5=通过（无"受限"项）+ `incomplete[]` 为空 + 无资料不足类 limitation | `incomplete: []` |
| CMP-PART | ≥60% critical 达标且无阻断缺口；或存在"受限"项/非关键缺口 | `incomplete[]` |
| CMP-LIMITED | 外部约束（资料不存在/不可达/能力缺失）无法继续且已说明影响 | `incomplete[]` + `limitations[]` + `gateWaivers[]` |
| CMP-NONE | <60% 或缺乏有效依据 | `incomplete[]` |

**强制降级规则**：存在 `[待提供]` 的关键参数/版本且未补齐、关键断言 `unverified`、或 `limitations[]` 含"资料不足"类 → **不得 CMP-DONE**（最高 CMP-PART）；外部不可达导致无法继续 → CMP-LIMITED。仅"无交互通道"本身不自动降 LIMITED。

判定时点：S10 初判，S11 前冻结。

## 18 续写（FR-078）

1. S0 检测到同 `docId` → 读 `doc_manifest.json` 与 `outline.md`。
2. 按 `structure[].id` 判断已完成章节；已完成不重写（修订场景走修订流程）。
3. 从首个未完成章节继续；补齐台账；写 `log.resume{at, fromChapter, completedChapters[], missing[]}`。
4. 重算完成度与受影响门禁。
5. manifest 不可解析 → 新建版本目录并说明，不覆盖旧目录。

## 19 日志字段

```json
{
  "preflight": { "capabilities": [], "outputDir": "", "deployment": {} },
  "timeline": [ { "at": "", "phase": "S0", "note": "" } ],
  "verificationAttempts": [ { "claimId": "", "target": "", "channel": "", "result": "", "count": 1 } ],
  "modeChanges": [ { "at": "", "from": "", "to": "", "reason": "" } ],
  "resume": { "at": "", "fromChapter": "", "completedChapters": [], "missing": [] },
  "termination": { "reason": "", "at": "" }
}
```

**未终止时**：`termination` 写 `null`（schema 允许 object/null），不得省略 `log` 的必填键。