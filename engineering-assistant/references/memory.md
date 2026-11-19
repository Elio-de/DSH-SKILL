# 项目知识库（memory）

> 目标：让"我之前怎么想的"可查，同时**永远不让它凌驾于代码之上**。
> 加载时机：首次进入项目、代码改动后、被问"之前怎么定的"、知识库体检。

---

## 1 结构与归属

```
<项目根>/.ea/
├── state.json     文件/模块哈希 + 知识覆盖登记（唯一"缓存"）
├── PROJECT_MAP.md 结构、入口、构建、依赖
├── MODULES.md     模块职责、接口、关键文件（带 file:line）
├── DECISIONS.md   决策记录（ADR，只追加）
├── ISSUES.md      已知问题（open/fixed，状态迁移不删条目）
├── PROGRESS.md    进度（滚动最近 15 条）
├── GLOSSARY.md    术语表
├── backup/        改前快照（Git 不可用/未初始化时的安全网）
└── archive/       归档：旧问题、旧进度、被取代的决策
```

**归属规则**：知识库属于**项目**，不进 `~/.dsh/`，不进跨会话记忆。不同项目互不可见。

---

## 2 三条命令就是全部机制

```powershell
# ① 建库 / 更新指纹（首次或代码大改后）
python scripts/project_scan.py --root . --init --update-state

# ② 体检：哪些知识过期、哪些文件消失、哪些超限
python scripts/stale_check.py --root .

# ③ 核对完代码后，登记"这份知识已重新确认"
python scripts/stale_check.py --root . --mark-verified MODULES.md --modules uart,main
```

`state.json` 不记录全项目，只记录**被知识引用过的文件**，所以不会随项目规模膨胀。

---

## 3 建库流程（冷启动）

```
1. python scripts/project_scan.py --root . --json      # 先看事实
2. 读构建文件 + 入口 + 3~8 个关键文件
3. 写 PROJECT_MAP.md（结构/入口/构建/依赖/未分析）
4. 写 MODULES.md（每个模块：职责/接口/依赖/关键文件:行号）
5. python scripts/project_scan.py --root . --init --update-state
6. python scripts/stale_check.py --root . --mark-verified PROJECT_MAP.md --modules <覆盖的模块>
7. 告知用户：已建库，覆盖 X 个模块；**未分析：Y**（诚实边界）
```

冷启动阶段**不要**追求写全。先写"关键路径 + 边界诚实"，后续增量补。

---

## 4 什么时候更新（按改动性质，不是每次都更新）

| 改动 | 更新 | 更新哪份 |
|---|---|---|
| 函数内部实现变化，接口不变 | 否 | 让哈希自然变化即可 |
| 新增/删除模块、职责变化 | 是 | `MODULES.md` + `PROJECT_MAP.md` |
| 改公开接口/数据结构 | 是 | `MODULES.md` + `DECISIONS.md`（若伴随取舍） |
| 修掉已知问题 | 是 | `ISSUES.md` → `fixed` |
| 发现新问题未修 | 是 | `ISSUES.md` 新增 |
| 完成一个阶段 | 是 | `PROGRESS.md` 追加 |
| 新约束（编译器选项/库版本/引脚变更） | 是 | `PROJECT_MAP.md` 构建节 |

**顺序**：改代码 → 编译/测试通过 → 再更新知识。**验证没通过时不得写"已实现"**。

---

## 5 判定过期（三级，从便宜到贵）

| 级 | 检查 | 成本 |
|---|---|---|
| L1 | `updatedAt` 距今 > 30 天 | ~0 |
| L2 | 文件 size/mtime 与记录不符 | 一次 stat |
| L3 | sha256 与记录不符 | 读文件 |

`stale_check.py` 已实现 L2→L3 的自动降级（未变则复用旧哈希），并聚合到模块级。

**过期后必须做的**：
1. 明确告知"这条知识可能过期"；
2. 若当前任务依赖它 → **先读代码**再回答；
3. 核对后 `--mark-verified` 刷新登记。

**禁止**：拿过期知识当事实回答"现在是怎么实现的"。

---

## 6 与代码冲突时

1. **代码赢**，无条件；
2. 当场标 `⚠ 与代码不符（原记录：…；实际：…）`；
3. 修正或删除该条；
4. `PROGRESS.md` 记一条"知识纠错"；
5. 不要"两边都留着"让后来者猜。

---

## 7 防膨胀（硬上限 + 归档）

| 文件 | 上限 | 超额处理 |
|---|---|---|
| `PROJECT_MAP.md` | 400 行 | 合并同类，细节下沉到 `MODULES.md` |
| `MODULES.md` | 400 行（单模块 ≤40 行） | 拆到 `docs/`，此处只留摘要+链接 |
| `DECISIONS.md` | 60 条 | 被取代的移入 `archive/DECISIONS-old.md` |
| `ISSUES.md` | 150 条（open ≤50） | fixed 超 30 天移入 `archive/ISSUES-YYYY.md` |
| `PROGRESS.md` | 最近 15 条 | 更早的按月归入 `archive/PROGRESS-YYYY-MM.md` |
| `GLOSSARY.md` | 80 条 | 合并同义、删废弃 |

`stale_check.py` 会报告超限文件。归档用 `edit`/`write` 移动内容，**移动前确认目标文件内容**。

---

## 8 条目格式（决定可读性与可校验性）

### 模块
```markdown
### uart 串口驱动
- 职责：USART1 中断收发 + 环形缓冲 + 帧解析
- 接口：`uart_init()`, `uart_send()`（非阻塞，返回 0 成功/-1 满）
- 依赖：`ringbuf`, `board_pins`
- 关键文件：`src/uart.c:1-260`、`src/uart.h:1-40`
- 注意：ISR 中不得调用 `uart_send()`（见 ISSUE-007）
- 核实：2026-11-19（模块哈希 e5f6…）
```

### 问题
```markdown
### ISSUE-007 ISR 中调用阻塞发送导致丢帧
- 状态：open（2026-11-19）
- 位置：`src/uart.c:188`
- 影响：高负载丢帧
- 计划：改入环形缓冲，主循环发送
- 关联：ADR-003
```

**每条结论后必须能指到位置**；指不到的不要写进知识库。

---

## 9 各文件写什么（一句话）

| 文件 | 一句话 |
|---|---|
| PROJECT_MAP | 这是什么、怎么编译、从哪进、依赖谁 |
| MODULES | 每个模块对外提供什么、内部依赖谁、哪里危险 |
| DECISIONS | 当时有哪些选项、为什么选这个、什么条件下该改 |
| ISSUES | 已知问题、影响、当前状态、计划 |
| PROGRESS | 最近做了什么、下一步做什么 |
| GLOSSARY | 同一个东西在本项目里叫什么 |

---

## 10 知识库的禁止事项

1. 把 `~/.dsh/` 或跨项目记忆当项目知识库；
2. 在知识库里存密钥、Token、个人路径；
3. 只读知识就回答"现在的实现"；
4. 让知识文件无限增长（超限就归档）；
5. 写入无法溯源（没有 `file:line`）的结论；
6. 代码与文档冲突时"两个都保留"。