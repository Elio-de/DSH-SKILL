# 版本控制（git-workflow）

> 这个模块的第一职责不是执行，而是**诚实地判断能不能执行**：先探测，再动作。
> 加载时机：提交、分支、合并、冲突、回滚、"改了哪些"、提交前检查。

---

## 1 第一动作永远是探测

```powershell
python scripts/env_probe.py --tools git
```

或在 pwsh 里直接：

```powershell
Get-Command git -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
git rev-parse --show-toplevel 2>$null
```

- 都无输出 → **Git 不可用**，走 §6 降级。
- 有输出 → 走 §2–§5。

**PATH 未刷新的坑**：刚装完 Git 时，正在运行的终端/进程不会自动获得新的 PATH，`Get-Command git` 会误报缺失。`env_probe.py` 会直接校验安装路径（`C:\Program Files\Git\cmd\git.exe`），因此优先信它。命令行里临时补 PATH：

```powershell
$env:PATH = "$env:PATH;C:\Program Files\Git\cmd"
```

**绝不可以在未探测的情况下写出 `git status` 的结果。** 这是本模块最高优先级的一条。

---

## 2 只读操作（R0，可直接做）

| 目的 | 命令 |
|---|---|
| 工作区状态 | `git status --short --branch` |
| 最近提交 | `git log --oneline -15` |
| 改动概览 | `git diff --stat` |
| 未暂存改动 | `git diff` |
| 已暂存改动 | `git diff --cached` |
| 分支 | `git branch -vv`（本地）、`git branch -a`（含远端） |
| 某提交内容 | `git show <sha> --stat`、`git show <sha> -- <file>` |
| 文件历史 | `git log --follow -p -- <file>`（大文件加 `-5` 限条数） |
| 谁改的 | `git blame -L <start>,<end> <file>` |
| 忽略规则核对 | `git check-ignore -v <file>` |

输出纪律：**贴关键片段 + 行号**，不整段倾倒 `git log`。

---

## 3 写操作（R2：需明确授权）

| 操作 | 风险 | 授权要求 |
|---|---|---|
| `git add` | 低（仅暂存） | 说明要加哪些文件 |
| `git commit` | 中（产生历史） | **必须授权**；先给信息草稿 |
| `git merge` / `rebase` | 中高（可能冲突、改历史） | **必须授权** + 说明回退方式 |
| `git push` | 高（对外可见） | **必须授权**，且说明推哪个分支 |
| `git reset --hard` / `clean -fdx` | 极高（丢工作） | **必须授权** + 备份 + 说明不可逆 |
| `git push --force` / 改历史 | 极高 | 默认拒绝，除非明确要求并说明影响 |

**任何时候都不做**：未授权的 commit/push；对用户未提交改动的覆盖。

---

## 4 生成提交信息（这是本机最能交付的 Git 能力）

流程：

```powershell
git status --short          # 有哪些文件
git diff --stat             # 规模
git diff                    # 逐行看（或只读关键文件）
```

然后按 **Conventional Commits** 起草：

```
<type>(<scope>): <一句话说明为什么>

<可选正文：背景、取舍、影响面>
<可选脚注：BREAKING CHANGE / 关联 issue>
```

| type | 用于 |
|---|---|
| `feat` | 新功能 |
| `fix` | 修缺陷 |
| `refactor` | 不改变行为的重构 |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `docs` | 文档 |
| `build` / `ci` | 构建、流水线 |
| `chore` | 杂项 |
| `revert` | 回滚 |

**写信息的三条纪律**：
1. 标题写"做了什么改变"，不写"改了哪些文件"；
2. 一次提交只讲一件事；如果 diff 里有两件事，建议拆分；
3. 不写"修复了一些问题"这种无法检索的话。

---

## 5 Diff 审查（提交前必做）

| 检查 | 怎么看 |
|---|---|
| 有没有夹带无关改动 | `git diff --stat` 里出现预期外的文件 → 查 |
| 有没有调试残留 | 搜 `printf/console.log/TODO/FIXME/XXX` 的新增行 |
| 有没有敏感信息 | 见 §7 扫描 |
| 有没有生成物 | `build/`、`*.o`、`*.hex`、`*.exe` 是否被加进来 |
| 空白/换行污染 | 全文件重排会让你看不到真实改动 → 提醒 |
| 删除是否合理 | `git diff --diff-filter=D` 看被删文件 |

---

## 6 无 Git 时的降级

**明确告知用户**："本机未安装 Git，无法执行 status/diff/log/分支/回滚。"

仍然能做的：

| 能力 | 做法 |
|---|---|
| 变更清单 | 用 `.ea/state.json` 的哈希对比，列出"哪些文件变了" |
| 变更规模 | `git diff --stat` 不可用 → 用文件大小/行数变化近似 |
| 提交信息 | 基于变更清单 + 代码阅读起草（信息本身有效，等有 Git 再用） |
| 提交前检查 | 敏感信息扫描、生成物检查、调试残留检查（纯本地） |
| 回滚 | 只能依赖 `.ea/backup/` 快照（改前备份） |
| 合并/冲突 | 只能讲方法与步骤，不能执行 |

`stale_check.py` 可给出模块级改动，是最接近 `diff --stat` 的替代：

```powershell
python scripts/stale_check.py --root .
```

**安装建议**（需用户批准）：`winget install --id Git.Git -e`。装好后本模块自动升级为完整能力，无需改 Skill。

---

## 7 提交前敏感信息扫描（本地，不外发）

```powershell
Get-ChildItem -Recurse -File -Include *.c,*.h,*.cpp,*.py,*.json,*.ini,*.yaml,*.yml,*.md,*.env* |
  Select-String -Pattern 'api[_-]?key\s*[:=]|secret\s*[:=]|passw(or)?d\s*[:=]',
                          'BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY',
                          'ghp_[A-Za-z0-9]{20,}', 'AKIA[0-9A-Z]{16}',
                          'sk-[A-Za-z0-9]{20,}' |
  Select-Object Path, LineNumber, Line -First 40
```

命中后：**只报告"哪个文件第几行像密钥"，绝不复述完整值**；建议改用环境变量或本地配置文件并加入忽略。

---

## 8 冲突解决（有 Git 时）

```
1. git status 看冲突文件
2. 逐个打开，理解 <<<<<<< ======= >>>>>>> 三段
3. 判断"两边为什么都改了这里"（先看各自提交信息）
4. 合并出正确结果（不是简单选一边）
5. 删除冲突标记，编译，测试
6. git add + 继续 merge/rebase
7. 实在解不了 → git merge --abort 回到干净状态（要说明）
```

**原则**：冲突解决后**必须重新编译并跑测试**，因为语义冲突不会报错。

---

## 9 禁止

1. 未探测就输出 git 结果（最严重）；
2. 未授权 commit / push；
3. 建议 `reset --hard` 而不说不可逆；
4. 把 `.env`、密钥、构建产物加入提交；
5. 用 `--force` 掩盖"推不上去"的真实原因；
6. 冲突解决后不验证就继续。