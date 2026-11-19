# 交付与契约（M12 合成 / M14 接口）

> 职责：报告骨架、清单文件、`research_result.json`、完成度、可视化源文件、跨 Skill 与只读边界。
> 适用：S14–S15。不适用：评级与证据判据（`sources.md` / `evidence.md`）。

## 1. 交付物清单（DATA-007）

> **模板索引**（`templates/`，逐份对应 §1 的产物）：`report.md`（主报告骨架，R1/R2/R3 通用）、`research-log.md`（日志：配置快照/检索/排除/调整/预算/终止）、`sources.md`（按评级分组）、`evidence.md`（按结论分组）、`changelog.md`（追加式版本记录）、`interface.md`（`INTERFACE.md` 只读声明与消费者顺序）。

> **示例索引**（`examples/`）：`research_result.example.json` 演示契约结构与 R1–R12 引用链；`report-r2.example.md` 演示 R2 报告写法与 `[C-xx]/[E-xxx]/[S-xxx]` 引用；`conflict.example.md` 演示冲突六维归因与"不强行择一"。三者是**格式示范**，编号互不相通（见各文件抬头）。

> **目录命名与 `researchId` 的映射**：目录名用 `topic-slug`（英文小写 + 连字符，≤40 字符，见 `knowledge.md` §3）；`researchId`（`R-YYYYMMDD-NNN`）写在契约 `researchId` 字段与各文件抬头，并登记到 `K4-index/index.md` 与 `research/_index.md`。**两者不得混用**：不要用 `researchId` 当目录名，也不要把 slug 当研究 ID。

```text
research/<topic-slug>/
├── report.md                  # 主报告（必交）
├── research_result.json       # 机读契约（必交）
├── research_result.md         # 人读摘要（可选）
├── INTERFACE.md               # 跨 Skill 使用说明与只读声明（必交）
├── sources.md                 # 来源清单（必交）
├── evidence.md                # 证据记录（必交）
├── research-log.md            # 过程日志（必交）
├── CHANGELOG.md               # 版本记录（追加式，必交）
├── outline.md                 # 大纲（可选）
├── notes/                     # 子问题笔记（研究笔记 ≥1）
├── diagrams/                  # Mermaid 源码 .mmd（按需）
├── derived/                   # 下游派生文件（下游可写区）
├── K1-sources/                # 原始资料快照与元数据（只读）
├── K2-reports/                # 历史版本报告副本（只读）
├── K3-knowledge/              # 结构化知识条目
└── K4-index/index.md          # 索引（必交）
```

## 2. 报告骨架（FR-052）

R1/R2/R3 共用骨架，按级别裁剪，但**不得删除**"来源""局限""不确定性"三部分。

```markdown
# <标题>
> 模式 M-DEEP/M-FAST ｜ 严谨度 L1/L2/L3 ｜ 详细度 R1/R2/R3 ｜ 完成度 CMP-* ｜ 日期 ｜ 研究 ID
> 资料对应版本：<版本/时间范围>（技术类必填）

## 摘要
- 关键结论 1（可信度：高）…[C-01]
- 关键结论 2（可信度：中）…[C-02]
- 重大冲突提示（如有）：…[X-01]

## 范围与方法
- 覆盖 / 不覆盖；检索轮次；主要来源层

## 分析
### 子问题 1：…
…（引用写法：[E-002] → [S-003]）

## 结论
| 编号 | 结论 | 可信度 | 验证等级 | 关键证据 |
|---|---|---|---|---|

## 争议与不确定性
## 研究局限
## 来源清单
## 附录（可选/必含按级别）
- A. 证据表（R3 必含）
- B. 冲突登记（R3 必含）
- C. 复现信息（技术方案类）
- D. 图表与矩阵（Mermaid 源码）
```

**引用写法**：正文用 `[C-01]` / `[E-002]` / `[S-003]` / `[X-01]`，与 `sources.md` / `evidence.md` 编号一致；编号必须能在清单中找到（断链为 0）。

## 3. 清单文件

**`sources.md`**：按评级分组（S→D），每条含编号、标题、URL、发布者、时间、评级、评级依据、tier。

**`evidence.md`**：按结论分组，每条含证据编号、sourceId、claim、quote、locator、depth、strength、status、dataKind（数据类）。

**`research-log.md`** 必含小节：配置快照（模式/严谨度/详细度/预算/语言/输出目录 + 来源）、检索查询与轮次、retrievalAttempts、排除来源及原因、方向调整、预算事件、未决问题。**缺"排除原因"判失败**。

**`CHANGELOG.md`**：追加式，每条 `{version, at, author, reason, changes[], invalidated[]}`；禁止无痕覆盖。

**`INTERFACE.md`**：说明 schemaVersion、字段含义、消费者读取顺序、**只读边界**（K1/日志/CHANGELOG 只读；`derived/` 可写；修订须回 S01 走新版本）。

## 4. `research_result.json` 规则

- 严格按 `schemas/research_result.schema.json`（draft 2020-12 声明，`schemaVersion: "1.0"`）。
- 必填 16 个顶层字段；`additionalProperties: true`（消费者须忽略未知字段）。
- **`artifacts` 必填子字段**（与 Schema 一致）：`report`、`sources`、`evidence`、`log`、`notes`、`diagrams` —— 均为相对路径或路径数组，指向本目录内实际文件；G4 须校验这些文件存在。
- **不含** `summary`、`duplicateOf`（未纳入 v1.0 契约）。
- 生成后自检三层：①JSON 语法；②结构与必填；③R1–R12 语义引用。
- 不得包含凭据/隐私原文（SEC-008 / DATA-009）。

**R1–R12 速查**：R1 `evidence.sourceId∈sources`；R2/R3 结论的证据 ⊆ evidence；R4/R5 冲突的结论与两侧证据；R6 `supersededBy` 指向另一条；R7 `assumptionIds⊆assumptions`；R8 `counterResearch.conclusionId∈conclusions`；R9 `staleWarnings.sourceId∈sources`；R10 `securityEvents.sourceId`（可选）；R11 九类数组内 ID 唯一（**在原始数组上计数，不得先转集合**）；R12 九类 ID 前缀（`S-/E-/C-/X-/A-/CR-/L-/N-/Q`，注意 `Q` 无连字符）。

**R11 的正确实现（禁止先 `set`）**：

```text
for name in ["sources","evidence","conclusions","conflicts","assumptions",
             "counterResearch","limitations","nextSteps","questions"]:
    raw = [o["id"] for o in R.get(name, []) if o.get("id")]   # 原始数组，逐元素
    for oid, n in Counter(raw).items():                        # 频次统计
        if n > 1: report("R11", name, oid, n)                 # 重复 → 违例
```

> 反例：`ids = {o["id"] for o in R[name]}` 之后再判重复——集合已去重，**永远为 0 违例**。
> R12 用固定前缀映射（见上）逐条 `startswith` 判定，不得靠对象名推断。

## 5. 完成度 FR-057

> **定义唯一出处**：`workflow.md` §3.1（判据与"必附内容"）。本节只规定**输出与一致性要求**。

- `meta.completion` 取 `CMP-DONE` / `CMP-PART` / `CMP-LIMITED` / `CMP-NONE` 之一，与 `incomplete[]`、`limitations[]` 一起写出。
- **一致性规则**：`CMP-DONE` ⇒ `incomplete` 必须为空；`CMP-LIMITED` ⇒ `limitations[]` 非空；非 DONE ⇒ `incomplete[]` 必须逐条列出未达标 critical 子问题。
- **报告与契约必须一致**：`report.md` 抬头的完成度、正文"研究局限"、`research_result.json` 三处不得互相矛盾。
- **禁止**：标 CMP-DONE 但存在未达标 critical 子问题；把"未执行/未验证"写成"已完成"。

**后续方向**：`nextSteps[]` **≤5 条**，每条 `{id: N-##, action, value, resources}`；只提建议，**不自动执行**。

## 6. 可视化（FR-056）

- 交付**源码**：Mermaid 围栏/`.mmd`、Markdown 对比矩阵、`outline.md`。
- **不得**声称已渲染图片；环境不支持 Mermaid 渲染、不支持 XMind/FreeMind/`.mm`。
- 数据图表用 Markdown 表格或 CSV 数据源交付。

## 7. 跨 Skill 只读边界（FR-063/FR-064）

| 区域 | 权限 |
|---|---|
| `research_result.json`、`sources.md`、`evidence.md`、`research-log.md`、`CHANGELOG.md`、`K1-sources/` | 只读 |
| `derived/` | 下游可写 |
| 修订结论 | 禁止直接改，须回 S01 走更新流程（S16）生成新版本 |

**诚实说明**：该边界是**契约 + 目录约定 + 流程约束**，不是文件系统强制；只能通过 CHANGELOG 缺失、时间戳与哈希比对发现越权修改。

## 8. G4 交付前校验

1. 文件齐全（对照 §1 必交项）。
2. `research_result.json` 可解析 + 必填齐全。
3. R1–R12 语义零违例。
4. 报告引用编号与清单一致。
任一不过 → 阻断交付，修复后重生成。

## 9. 完成度与"未完成"的表述纪律

- 不得把"设计正确/示例通过"写成"已验证运行"。
- 不得把"子集校验"写成"标准 Schema 校验通过"。
- 不得把"未执行"写成"通过"。