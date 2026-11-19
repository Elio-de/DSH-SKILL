# 项目理解（project-analysis）

> 目标：把"一堆文件"变成"一张有证据的地图"。
> 加载时机：首次接触项目、被问结构/入口/依赖/模块职责、或任何修改任务开始前上下文未知时。
> 前提：本机**无 LSP**，所有调用关系结论都是**文本检索 + 人工阅读**的结果，必须标注 V2 而非更高。

---

## 1 六步法（每步都有可执行动作）

### 步骤 1：拿到结构事实（不要靠猜）

```powershell
python scripts/project_scan.py --root . --json
```

它给出：文件数、源码数、构建系统与依据、入口候选、模块划分（含文件清单与聚合哈希）、按扩展名统计。
比 `Get-ChildItem -Recurse` 可靠，因为它已排除 `build/ .git/ node_modules/ .venv/` 等噪声。

**若项目很大**（`truncated: true`），先看摘要再决定深入哪一块，不要盲目加 `--max-files` 重扫。

### 步骤 2：定位构建系统（决定"怎么编译"）

| 发现 | 含义 | 下一步读什么 |
|---|---|---|
| `CMakeLists.txt` | CMake | 顶层 + 各子目录的 `add_executable/add_library` |
| `Makefile` / `mingw32-make` | Make（本机无 GNU make，用 `mingw32-make`） | `all:`、`CC`、`CFLAGS`、`-I` 路径 |
| `platformio.ini` | PlatformIO | `[env:*]`、`board`、`framework`、`build_flags` |
| `*.ioc` | STM32CubeMX | 引脚分配、时钟树、外设使能（**这是硬件事实源**） |
| `*.uvprojx` | Keil MDK | Target 选项、器件型号、包含路径 |
| `*.ewp` | IAR | 同上 |
| 无任何构建文件 | 可能靠 IDE 或手工命令 | 问用户"平时怎么编译"，不要编一个 |

### 步骤 3：找入口

```powershell
# C/C++
grep  pattern: "\bmain\s*\("            include: "*.c"
# C++ 类构造/初始化入口
grep  pattern: "int\s+main|void\s+setup|void\s+loop"  include: "*.{c,cpp,ino}"
# Python
grep  pattern: "if\s+__name__\s*==|def\s+main\s*\("   include: "*.py"
```

嵌入式注意：真正的"入口"往往不是 `main`，而是 **复位后 → `SystemInit` → `main` → 外设初始化 → 主循环**。
所以还要找：`HAL_Init`、`SystemClock_Config`、`MX_*_Init`、`while (1)`、中断服务函数 `*_IRQHandler`。

### 步骤 4：归类模块（按目录 + 依赖，不按文件名）

```powershell
python scripts/project_scan.py --root . --json   # 已给 modules
```

补强判定（仅在有疑问时做）：

```powershell
grep pattern: "#include\s+\""  include: "*.h"      # 头文件自包含程度
grep pattern: "extern\s+"      include: "*.h"      # 跨模块共享状态（耦合信号）
```

**判定职责的方法**：读该模块**对外头文件**的声明列表 → 能说清"它提供什么能力"，比读实现更快。
只有当结论要写进知识库时，才需要读实现确认。

### 步骤 5：梳理依赖与调用关系（现实可行的做法）

本机没有调用图工具，可用：

```powershell
# 谁包含了谁（构建 include 图）
grep pattern: "#include\s+\"([^\"]+)\""  include: "*.{c,h}"
# 谁调用了某函数（以 uart_send 为例）
grep pattern: "\buart_send\s*\("
# 谁在改某个全局变量
grep pattern: "\bg_uart_state\b"
```

**结论措辞纪律**：
- 可以说："在 `src/*.c` 中检索到 3 处调用（V2）"；
- 不可以说："全项目只有这 3 处调用"（除非确认检索覆盖了所有源文件，且无宏/函数指针间接调用）；
- 涉及函数指针、宏展开、中断向量表时，必须补一句"可能存在间接调用，未覆盖"。

### 步骤 6：写地图（落到 `.ea/PROJECT_MAP.md`）

```markdown
# 项目地图
## 一句话
<这个项目是做什么的，证据：README/主函数行为>
## 构建
- 系统：CMake / Make / CubeMX
- 编译命令：<真实可用的命令>
- 产物：<elf/hex/bin 路径>
## 入口与主流程
1. <复位/启动> → 2. <初始化> → 3. <主循环>（file:line）
## 目录职责
| 目录 | 职责 | 证据 |
## 模块与依赖
| 模块 | 职责 | 依赖 | 关键文件 |
## 未分析
- <目录>（N 个文件）：未读，原因：与本任务无关/超出预算
```

**"未分析"这一节是强制的**——它防止你（和用户）把"没看"误当成"没问题"。

---

## 2 抽样原则（大项目不炸上下文）

| 优先级 | 读什么 | 为什么 |
|---|---|---|
| 1 | 构建文件 | 决定怎么编译、有哪些宏 |
| 2 | 入口 + 主循环 | 决定执行流程 |
| 3 | 配置/引脚/时钟文件 | 决定硬件事实 |
| 4 | 当前任务直接相关的模块 | 任务需要 |
| 5 | 公共基础设施（日志、缓冲、错误处理） | 影响面大 |

> 3–8 个文件通常够写出第一版地图。**不要追求 100% 覆盖**，要追求"关键路径正确 + 边界诚实"。

---

## 3 常见陷阱（都踩过）

| 陷阱 | 表现 | 应对 |
|---|---|---|
| 文件名骗人 | `utils.c` 里其实有核心逻辑 | 看头文件声明与调用点，不看名字 |
| 生成的代码混入 | `Drivers/`、`Middlewares/` 是 ST 生成的 | 标记为"第三方/生成"，不审不建议改 |
| 多处 `main` | 测试工程、示例工程各有一个 | 用构建系统确认"哪个是产品入口" |
| 条件编译 | `#ifdef USE_HAL_DRIVER` 导致两条路径 | 读构建宏，再判断哪条生效 |
| 旧代码残留 | `old/`、`backup/` 目录 | 确认是否参与构建，不参与则不分析 |
| 头文件即接口，但实现分散 | 一个模块跨 5 个 .c | 以头文件为契约，逐个实现核对 |

---

## 4 输出检查（交付前）

1. 每条结构结论都能指到**文件或命令输出**吗？
2. "未分析"部分写了吗？
3. 构建命令是**实际验证过**的，还是抄的？（没验证就标 V1）
4. 入口是否区分了"启动流程"与"业务主循环"？
5. 有没有把第三方库当自己的代码来分析？