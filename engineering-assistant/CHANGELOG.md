# 变更记录

## [1.1.0] - 2026-11-19

第四轮实测驱动的修正。全部改动来自真实测试暴露的问题，未放宽任何安全标准。

### 修复

- **`project_scan.py` 把构建产物计入模块哈希**：`.gcno/.gcda/.o/.exe/.elf/.map` 等此前被当作源文件，导致模块哈希随编译行为变化、产生假"知识过期"。新增 `ARTIFACT_EXTS` 过滤。（实测：修复前 18 文件含 5 个 `.gcno`，修复后 13 文件）
- **`env_probe.py` 只信 PATH**：安装 Git 后当前进程 PATH 未刷新，脚本误报"未安装"。改为同时校验标准安装路径（Git / Cppcheck），实测在陈旧 PATH 下仍能正确识别。
- **SKILL.md 硬编码"Git 当前不可用"**：环境一变即成错误陈述。改为"必须实测，缺失才降级"。
- **SKILL.md 称四个脚本"只读"**：`--init` / `--update-state` / `--mark-verified` 实际会写 `.ea/`。改为准确表述。
- **SKILL.md 超出体积预算（12318 > 12288）**：删除与 `git-workflow.md` 重复的 PATH 说明，降至 12190 字节；同时满足"内容不重复"要求。
- **`-fanalyzer` 对固件主循环的误报未记录**：`coding.md` 增加"已知误报"段（`-Wanalyzer-infinite-loop`、`-Wunused-but-set-variable`），避免把正常主循环当缺陷。

### 文档

- `git-workflow.md`：补充"PATH 未刷新"的实际坑与临时补 PATH 的做法；去掉"本机没有 Git"的硬编码表述。

### 实测结论（不改代码，仅记录）

- 已安装 Git 2.56.0.4、Cppcheck 2.22.0、pyserial 3.5、pytest 8.4.2 后，文档中 19 条命令全部可用。
- `cppcheck` 能检出内存泄漏与未初始化变量，**检不出** `strcpy` 越界与除零 → 印证"工具证据 ≠ 全部结论"。

## [1.0.0] - 2026-11-19

首个可用版本。按第三轮开发要求实现：主 Skill + 10 篇参考 + 4 模板 + 3 清单 + 4 脚本。

### 新增

- **SKILL.md**：六条红线（代码为真/不虚构/无证据不下结论/不覆盖未提交工作/高风险先授权/不外发）、四模式自动判定、加载规则 G-1..G-7、权限 R0–R3、流程 L0–L2、证据分级 V0–V5、输出契约、10 模块路由、工具速查、禁止事项、交付前 5 问自检。
- **references/**：
  - `project-analysis.md` 六步法、构建系统识别表、入口定位（含嵌入式启动流程）、调用关系检索纪律、抽样原则、常见陷阱。
  - `coding.md` 改前 5 问、PS 通配符陷阱、主机/目标编译命令、常见编译错误对照表、调试方法序、C 缺陷模式、重构规则。
  - `git-workflow.md` 探测优先、只读/写操作分级、Conventional Commits、Diff 审查、**无 Git 降级路径**、敏感信息扫描命令。
  - `review.md` **四分类**（已确认缺陷/高概率风险/待验证疑点/一般建议）、14 个检查维度、误报控制三问、严重度定义、三种审查深度、能力边界。
  - `testing.md` 四层验证与 V 级映射、用例设计四法、可直接编译的 C assert harness、桩与替身、嵌入式分层、gcov 覆盖率、回归基线。
  - `architecture.md` 决策七步、比较矩阵、嵌入式结构选择表、接口设计检查、成本量级估算、ADR。
  - `documentation.md` 读者决定内容、README/接口/变更/交接文档结构、写作规则、与知识库分工。
  - `memory.md` `.ea/` 结构与三命令机制、冷启动流程、更新时机表、三级过期判定、冲突处理、防膨胀上限、条目格式。
  - `mentor.md` 提示阶梯 L1–L5（含同一问题的五种给法示例）、讲解四段结构、提问设计、收束、**不教学的五种情形**、嵌入式学习路径。
  - `embedded.md` 数据类型与溢出、指针边界、内存与段分析、**volatile 判定表**、临界区、ISR 纪律、栈空间、定时器时钟计算、初始化顺序、GPIO 与硬件匹配、寄存器纪律、实时性、手册使用、常见陷阱、硬边界。
- **templates/**：`review-report.md`、`change-report.md`、`adr.md`、`test-plan.md`，以及 `knowledge-base/` 六份骨架 + `state.json` 占位。
- **checklists/**：`pre-change.md`、`pre-commit.md`、`release.md`。
- **scripts/**：
  - `env_probe.py` 校验路径存在性 + 试运行 `--version`，识别失效 PATH 项；检测主机/目标 `-fanalyzer` 支持；输出能力判定与降级原因。
  - `project_scan.py` 结构/构建系统/入口/模块归类；size+mtime 优先的增量哈希；模块聚合哈希；`--init` 从模板生成 `.ea/` 且不覆盖已有文件。
  - `stale_check.py` 三级时效判定、模块级聚合比对、知识覆盖登记（`--mark-verified`）、超限与文件消失报告、`--strict` 退出码。
  - `complexity.py` C/C++ 与 Python 函数长度/圈复杂度近似排序，用于"从哪读起"。

### 实测

- `env_probe.py`：确认 git 缺失、clang/cppcheck 缺失、ARM gcc 15.2.1 支持 `-fanalyzer`、MIN GW gcc 8.1.0 不支持。
- `project_scan.py`：新建 fixture 建库成功；修改单文件后重扫 `reuse=3 / hashed=1`，模块哈希随内容变化。
- `stale_check.py`：登记 `MODULES.md` 覆盖 `uart,main` 后，修改 `src/uart.c` 即判定模块变化并把该知识标为过期，`--strict` 返回 1。
- `complexity.py`：对已知复杂度的 C 样例输出 6/5/4/1，与人工计算一致；`struct` 定义被正确忽略。

### 已知限制

- 本机无 Git：`git-workflow` 只能降级工作。
- 无 LSP/SAST/ASan：审查类结论上限为 V2，内存与并发类最高到"高概率风险"。
- 硬件验证（V5）不在 AI 能力范围内。

### 设计决策

- 采用**单 Skill + 内部参考**而非多个兄弟 Skill：DSH 不支持嵌套 `SKILL.md`，且平级多 Skill 会增加每个会话的目录开销与路由歧义。
- 安全红线与权限分级写在 `SKILL.md` 而非参考文档：参考文档是可选的，安全规则不能可选。
- 用脚本承载"可机械校验"的部分（建库、时效、复杂度），因为 Skill 本身没有强制力。

### 未实现（留待后续）

- 插件形式的能力层（`git` 工具、环境探测工具、`pre-execute` 风险拦截）。
- 英文版。
- `examples/` 示例项目（首版刻意不做，避免示例被当成规范）。
- 自动化测试套件（T2/T3 用例需真实会话验证，见第四轮）。