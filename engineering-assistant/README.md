# engineering-assistant

面向真实软件工程开发（尤其嵌入式）的**协作 + 教学** Skill。装一次，全局可用。

- 版本：**1.1.0**
- 适配 DSH：**0.2.2-rc.3**（Desktop profile）
- 形态：单个 Skill + 10 篇按需加载的参考文档 + 4 个只读脚本

---

## 安装

```powershell
# 全局安装（Windows，本机路径）
Copy-Item -Recurse -Force .\engineering-assistant "$env:USERPROFILE\.dsh\skills\engineering-assistant"

# 验证：新会话中应能列出并加载
```

安装位置对应 DSH 的 `user-dsh` 发现根（rank 400），**任意项目、任意工作目录都可用**，无需改配置、无需重启。

---

## 目录

```
SKILL.md                  主入口：红线、模式判定、权限、证据分级、输出契约、模块路由
references/               10 篇专业参考（一次最多加载 2 篇）
  project-analysis.md     项目理解         coding.md       编码与调试
  git-workflow.md         版本控制（含缺失降级）
  review.md               审查与质量       testing.md      测试与四层验证
  architecture.md         方案与架构       documentation.md 工程文档
  memory.md               知识库维护       mentor.md       学习引导
  embedded.md             嵌入式专项
templates/                审查报告 / 修改报告 / ADR / 测试计划 + knowledge-base 骨架
checklists/               改前 / 提交前 / 交付前 自检
scripts/                  env_probe / project_scan / stale_check / complexity（只读）
```

---

## 四个脚本

| 脚本 | 作用 | 会写文件吗 |
|---|---|---|
| `env_probe.py` | 探测工具链真实可用性（含失效 PATH 校验、`-fanalyzer` 支持） | 否 |
| `project_scan.py` | 结构/构建/入口/模块 + 文件与模块哈希 | 仅 `--init`/`--update-state` 时写 `.ea/` |
| `stale_check.py` | 判定知识是否过期、文件消失、超限 | 仅 `--mark-verified` 时写 `state.json` |
| `complexity.py` | 函数长度与圈复杂度近似排序（C/C++/Python） | 否 |

```powershell
python scripts/env_probe.py
python scripts/project_scan.py --root . --json
python scripts/project_scan.py --root . --init --update-state
python scripts/stale_check.py --root .
python scripts/stale_check.py --root . --mark-verified MODULES.md --modules uart,main
python scripts/complexity.py --root . --top 15
```

---

## 项目知识库（三步）

```powershell
# 1 建库 / 更新指纹
python scripts/project_scan.py --root . --init --update-state
# 2 体检（哪些知识因代码变化而过期）
python scripts/stale_check.py --root .
# 3 核对完代码后登记
python scripts/stale_check.py --root . --mark-verified MODULES.md --modules <模块名>
```

- 知识库在**项目内** `.ea/`，不同项目天然隔离，不写入跨项目记忆。
- **代码是唯一事实源**：`state.json` 记录哈希，代码一变即标记知识过期。
- 硬上限 + `archive/` 归档，防止无限增长。

---

## 已知限制（实测）

| 限制 | 影响 |
|---|---|
| 无 LSP | 无跳转定义/调用图；调用关系靠 `grep` + 人工，结论标 V2 |
| cppcheck 覆盖有限 | 能查内存泄漏/未初始化；**查不出** `strcpy` 越界与除零，需人工推理 |
| 无 ASan/Valgrind | 内存越界/踩踏只能"待验证" |
| 无 profiler | 性能只给复杂度与热点假设 |
| 无 openocd / JLink | 烧录与在线调试需用户手动（STM32CubeProgrammer 可用） |
| 无 SDCC / Unity | 51 只能审查不能编译；C 用自建 assert harness（Python 已有 pytest） |

> Git 已安装（2.56.0.4），但**当前会话 PATH 可能未刷新**：`env_probe.py` 会直接校验安装路径；命令行可用绝对路径或 `$env:PATH += ';C:\Program Files\Git\cmd'`。

---

## 维护

- 改 `SKILL.md` 的红线/权限 → 升 MAJOR；加模块/参考 → MINOR；措辞 → PATCH。
- 每次改动后自检：
  1. frontmatter 合法（`name` kebab-case、`description` ≤500 字符、无废弃键）
  2. `SKILL.md` ≤12 KB，单篇 reference ≤15 KB
  3. 所有相对引用路径真实存在，无孤儿文件
  4. 新规则是否与既有文件重复（重复即删，保留一处）
- 变更记入 `CHANGELOG.md`。

## 设计取舍（为什么这样）

- **单 Skill 而非多 Skill**：DSH 不发现嵌套 `SKILL.md`；平级多 Skill 会让每个会话都多背目录项。
- **红线写在 SKILL.md**：参考文档可选，安全规则不能可选。
- **脚本代替口号**：Skill 无强制力，把"该检查的"变成可执行命令。
- **不追求功能数量**：所有结论分级，能力边界显式声明。