# CHANGELOG

## v1.0.4 — 2026-11-18

最终验收阶段发现的健壮性修复（不改变任何规则）：

- **`scripts/selftest.py` 在不可写环境抛栈**：当工作目录与 Skill 目录都不可写、且系统临时目录禁止建子目录时，此前会 `PermissionError` 崩溃；现改为逐个候选目录做真实可写探测，全部失败时打印明确指引并以 **exit 3** 退出（不抛栈）。
- 单个用例目录创建失败时记 `FAIL` 并继续，不再中断整轮自测。
- 验证：在工作区可写目录运行 `selftest.py` → **9/9 通过，exit 0**；在不可写目录运行 → 明确提示 + exit 3（不再 traceback）。

## v1.0.3 — 2026-11-18

最终交付补齐（无规则变更）：

- **新增模板** `templates/验收报告（ACCEPTANCE_REPORT）.md`：逐条 AC 证据与三态（已验证/未验证/无法验证）、交付物核对、独立审核意见、遗留整改、G4 用户签认区。
- `references/acceptance.md` 引用该模板（此前验收报告只有骨架描述、无独立模板）。
- 其余文件未改；核心契约（阶段/门禁/档位/29 项/13 段提示词/档案字段）保持不变。
- 验证：`selftest.py` 9/9 通过；`examples/small-L1 --lite --strict` 与 `examples/small-L2 --strict` 均 exit 0；安装目录同步后逐文件哈希一致，加载版本 v1.0.3。

## v1.0.2 — 2026-11-18

第四轮功能测试与质量审查后的修复（规则增强 + 能力基线补全 + 示例自洽性）。**不改变**阶段、门禁、档位、29 项、13 段提示词等核心契约。

### 校验脚本（`scripts/check_project.py`）

1. **C9 全档模式可通过"定级造假"**：此前全档不返回声明等级，结构性问题（如覆盖缺口）存在时仍可声明 A 级通过。现改为全档也解析声明等级，并在 `BLOCKER>0` 且声明 A/B 时判 BLOCKER（首命中规则①②）。
2. **C5 过松**：此前只要任务号在 PROGRESS 任意行出现即通过；现要求 Done 任务必须有**状态为 Done 的**记录。
3. **C7 新增"执行完成≠验收通过"检查**：交付清单验收结论为"不通过/退回/不合格"、而来源任务为 Done 时判 BLOCKER（对应测试十一的漏洞）。
4. **执行者自审从 `--strict` 提升为默认检查**：执行者=审核者 → MAJOR（PQ-E3）。
5. **`--strict` 增强**：`—`/空视为字段缺失；单任务估算 >3 人天 → MAJOR（PQ-C3）。
6. **C1 增强**：新增"每条 RQ 至少 1 条 AC"的覆盖检查。

### 能力基线（`references/capabilities.md`）

7. 补入**嵌入式工具链**实测项（此前缺失，会误判 STM32 项目不可行）：`arm-none-eabi-gcc 15.2.1`、`arm-none-eabi-gdb 14.3.1`、`cmake 3.31.6`、`ninja 1.12.1`、`STM32_Programmer_CLI 2.23.0`、STM32Cube bundles（gnu-tools/stlink/pack-manager 等）；同时明确**未做编译与烧录冒烟**，不得承诺"能编译能烧录"。
8. 新增《2.3 嵌入式项目探测》5 步（编译器版本、器件包、编译冒烟、烧录冒烟、观测手段）。

### 规则澄清

9. `references/workflow.md`：Done 必须有状态为 Done 的进度记录；验收不通过必须回 `In Progress` + 开 `IS`，不得置 Done。
10. `references/archive.md`：C5/C6/C7 规则同步（自审、Done 记录、不通过不得 Done）。
11. `references/acceptance.md`：新增"脚本可查的硬规则"三条。
12. `references/plan-quality.md`：反形式化第 1 条明确"结论必须逐格从字段取证，不得照抄上一版报告或模板结论"。
13. `references/requirements.md`：示例命令改为不存在的通用脚本名，避免被误读为真实脚本。

### 示例自洽性（`examples/small-L2`）

14. 补齐 `工作文档/` 过程证据 8 个文件（文档清单、元数据表、主题归类表、主题判定规则、check_index.py、自检记录、验收记录、README），使 TASKS 产出与交付清单证据位置**真实存在**；`check_index.py` 实测退出码 0。

### 测试发现的环境事实

15. 本机具备可用的 STM32 工具链（GCC/CMake/Ninja/GDB/Programmer/ST-Link），此前 `capabilities.md` 未记录，属**能力基线缺失**而非环境缺陷；已在 v1.0.2 补入并标注未冒烟部分。

### 验证（v1.0.2）

| 检查 | 结果 |
|---|---|
| `py -3 scripts/selftest.py` | **9/9 通过**（新增"执行者=审核者""验收不通过却标 Done"两个用例） |
| `examples/small-L1 --lite --strict` | exit 0 |
| `examples/small-L2 --strict` | exit 0 |
| 第四轮 T3 缺陷档案 | exit 1：C1/C2/C4/C7/C9/C10/C11 命中（含定级造假） |
| 第四轮 T11-A（Done + 交付不通过） | exit 1：C7 报"执行完成 ≠ 验收通过" |
| 第四轮 T5-B / T9 / T11-B / T13 | exit 2（仅 MAJOR）/ 0 / 0 / 0，符合预期 |

## v1.0.1 — 2026-11-18

安装验证阶段的路径修复（不改变任何规则与契约）：

- **修复**：`SKILL.md` 资源路由表与正文中的参考文件引用存在裸文件名（如 `intake.md`、`plan-quality.md`），按 Skill 资源基目录解析会指向不存在的路径；统一改为 `references/xxx.md`（共 27 处）。
- **修复**：`references/archive.md`、`references/plan-quality.md`、`examples/small-L2/项目说明（README）.md` 中同类裸引用各 1–2 处，已统一前缀。
- **修复**：`scripts/selftest.py` 增加 UTF-8 输出强制（Windows 非 UTF-8 控制台下不再乱码），并在临时目录不可写时给出明确提示而不是抛异常。
- **验证**：安装目录 50 个文件逐一 SHA256 比对一致；14 份 reference 全部可解析；`check_project.py` 在安装位置对 L1/L2 样例分别 exit 0；`selftest.py` 7/7 通过。

## v1.0.0 — 2026-11-18

首个可安装版本。基于第一轮（R1）确认的架构实现；产物为纯 Markdown 指令 + 模板 + 校验脚本，不含插件代码，不需要编译。

### 交付内容（50 个文件 / 约 5470 行）

| 类别 | 数量 | 内容 |
|---|---|---|
| 主干 | 1 | `SKILL.md`（144 行）：定位、四条不变量、权限分级、阶段与门禁、档位、资源路由、核心能力要点、红线、自检、完成定义 |
| 参考文件 | 14 | `workflow`（阶段/门禁/回退）、`intake`（意图/档位/访谈）、`research`、`requirements`、`planning`、`plan-quality`（核心）、`prompts`（核心）、`context`、`archive`、`risk-change`、`collaboration`、`acceptance`、`retrospective`、`capabilities` |
| 模板 | 18 | 档案 12 件 + L1 项目卡 + 评分卡 + 派发/审查 + 项目群索引/共享资源 + 单任务提示词 |
| 脚本 | 2 | `scripts/check_project.py`（700 行，C1–C12 一致性校验，`--lite`/`--strict`/`--json`）；`scripts/selftest.py`（146 行，7 个负例回归） |
| 示例 | 13 | `examples/small-L1/`（单文件 L1，99 行）；`examples/small-L2/`（11 件档案 + 2 个真实交付文件，全档校验通过） |

### 相对 R1 设计的调整（均有理由）

1. **任务状态改用英文六态**：`Pending / In Progress / Review / Done / Blocked / Cancelled`（与用户第二轮要求一致，R1 使用的旧状态名作废）。
2. **任务卡 17 字段，新增「审核者」**：落实"执行者不能单独宣布自己成果合格"；审核者必须 ≠ 执行者。
3. **风险权限四级**（低/中/高/极高）+ 不可逆操作必须明确授权。
4. **规划质量分组改为用户 8 维 A–H**（29 项逐项唯一归属），并按用户四档标签输出：A 优秀 / B 良好（=有条件通过）/ C 需返工 / D 不通过。
5. **新增 L4 项目群档案契约**（PORTFOLIO + SHARED_RESOURCES）。
6. **13 段提示词在所有档位保留**（L1 压缩为要素句、L2 内嵌 6–8 行、L3 独立文件），只压字数不删段。
7. **管理开销唯一口径**：独立管理段 M02–M09、M15–M17 的估算工时 ÷ 项目总估算工时；M10–M12 为执行内嵌开销（执行工时 10%），不计入分子。

### 关键契约

- 阶段 `S0–S8`；门禁 `G0–G5`（G0/G1/G2/G4 用户确认，L3+ 含 G5；G3 主 AI 判定并知会）。
- 档位 `L1–L4`；档案 `1 / 11 / 13 / 2+N` 件；确认点 `2 / 4 / 5 / 5`；管理开销上限 `8% / 15% / 20% / 25%`。
- 规划质量：29 项检查（10 项 BLOCKER）、首命中定级 A/B/C/D、最多 2 轮自动修复、差异重检 + 回归集、L2+ 独立复检、报告 10 要素、8 条反形式化护栏。
- 提示词：13 段结构；质检 9 条；L2 内嵌 `TASKS` 的「执行提示词」字段，L3 独立 `PROMPTS/TK-xxx.md`；无法直连外部 AI 时必须写"未调用"声明。
- 验收：任务/阶段/项目/最终四级；独立审核；已验证/未验证/无法验证三态；用户最终验收权。
- ID：`RQ / AC / MS / TK / PQ-vX.Y-NN / D / RK / IS / CH / DL`；任务编号唯一不复用。

### 第二轮内部评审与修复

完成初稿后经**两轮独立对抗性评审**（`subagent`，只读、以"找毛病"为目标）：

| 轮次 | 结论 | 处理 |
|---|---|---|
| 第 1 轮 | 3 BLOCKER / 18 MAJOR / 9 MINOR | 逐条修复：13 段提示词全档保留；L1 闭环（RQ/审核者/提示词/交付来源/CLOSED 内嵌项目卡）；校验脚本补 29/13 项完整性、待确认判负、RK/IS/D/CH 引用集、ID 唯一性、C8 接受 CLOSED；模板字段与 reference 对齐（RISKS 四档 P/I/敞口、ISSUES 根因/关闭条件、PROGRESS 预计/实际人天/延期、README 流程说明与 G5、缓冲 10–30%、L4 两份契约等） |
| 第 2 轮（复核） | 仍不通过（3 BLOCKER 等在首轮之后发现的新问题） | 已全部修复；修复过程本身也做了交叉检查（见下"验证记录"） |

> 诚实说明：评审者与本 Skill 使用同一模型，独立性来自上下文隔离与对抗提示，不来自模型差异。第二轮后未再做第三次独立评审，最终一致性由下方可复现命令与自测套件保障。

### 验证记录（可在 Skill 根目录复现）

| 检查 | 命令 | 结果 |
|---|---|---|
| L1 样例（精简） | `py -3 scripts/check_project.py "examples/small-L1" --lite` | 退出码 **0**，BLOCKER 0 |
| L1 样例（严格） | `py -3 scripts/check_project.py "examples/small-L1" --lite --strict` | 退出码 **0** |
| L2 样例（全档） | `py -3 scripts/check_project.py "examples/small-L2"` | 退出码 **0**，13 条规则全通过 |
| L2 样例（严格） | `py -3 scripts/check_project.py "examples/small-L2" --strict` | 退出码 **0** |
| 负例回归 | `py -3 scripts/selftest.py` | **7/7 通过**（L1/L2 基线、PQ 结论表删半、待确认、CH 引用不存在、TK 重复、交付文件为空） |
| 结构审计 | 内部审计脚本（50 文件、18 模板、29 项集合、A–H 计数、13 项 L1、关键口径、禁用词） | 全部 PASS |
| 语法 | `py -3 -m py_compile scripts/check_project.py` | 通过 |

**未覆盖**：真实 DSH 加载测试（属第三轮安装验证）；Office 冒烟、`workflow`/`team_*` 全流程、`present` 交付卡（见 `references/capabilities.md` 的受限项与降级路径）。

### 已知限制（不承诺、不绕过）

- 外部异构模型不可用（仅 1 条模型路由 `deepseek-v4.1-flash`）；
- 浏览器自动化/截图、中文社区平台、git/GitHub 推送、pandoc、系统 node、Mnemon 长期记忆均不可用；
- `workflow` / `team_task_*` 已挂载但未端到端验证；`office-kit` 运行时健康但未实测生成/渲染/重算；`present` 未验证；
- 工作区外写入被沙箱拒绝；安装默认由用户手动复制，审批升级路径未验证；
- `check_project.py` 为 700 行（超出初版 400 行预算），因覆盖 13 条规则、三种模式与中文字典级诊断；已由 `selftest.py` 做定向回归。

### 安装

把本目录（`project-orchestrator/`）整体复制到 `~/.dsh/skills/` 下，保持 `SKILL.md` 位于目录根。文件监听会自动生效：新会话或下一步即可在 Skill 目录中看到 `project-orchestrator`。卸载即删除该目录（纯文本，无残留）。