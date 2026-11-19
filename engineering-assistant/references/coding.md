# 编码与调试（coding）

> 唯一的"会改源文件"的模块。核心不是写得快，是**每一步都可验证、可回退**。
> 加载时机：写/改/重构代码、编译报错、运行崩溃、结果不对、性能可疑。

---

## 1 闭环（顺序不可颠倒）

```
读懂现状 → 说明打算 → 小步修改 → 编译 → 运行/测试 → 读真实输出 → 收敛 → 汇报
```

跳过任何一步都会导致"改了半天不知道哪步生效"。

---

## 2 改前必答 5 问

1. 这段代码**现在**在做什么？（读过，能说出数据从哪来到哪去）
2. 谁在调用它？（`grep` 过，知道影响面）
3. 有没有**既有约定**？（错误码风格、日志宏、命名、内存所有权）
4. 改完怎么**证明**它对了？（具体到命令或用例）
5. 改坏了怎么**退回去**？（Git 可用时用版本控制；不可用时先备份或确保改动可逆）

答不全 → 先补，不要动手。

---

## 3 改动纪律

| 规则 | 做法 |
|---|---|
| 一次只改一件事 | 修 bug 不顺手重构；重构不改行为 |
| 局部优先 | 用 `edit` 精确替换；**禁止**对已存在文件整份 `write` 覆盖 |
| 改前备份 | 大改前复制到 `.ea/backup/<时间戳>/`，并写 `NOTE.md` 说明如何还原 |
| 保持风格 | 跟随文件既有缩进/命名/错误处理，不夹带个人偏好 |
| 不删代码要留证 | 确需删除时说明"删了什么、为什么、如何恢复" |
| 每步可编译 | 改完一个逻辑单元就编译一次，不要攒到最后一起来 |

**PowerShell 关键细节**：PS **不会**为原生命令展开通配符，`gcc src\*.c` 会原样传参而失败。必须：

```powershell
$src = (Get-ChildItem src\*.c).FullName
gcc -std=c11 -Wall -Wextra $src -o build\app.exe
```

---

## 4 编译与静态检查（本机实测命令）

### 主机（MinGW gcc 8.1.0，**无** `-fanalyzer`、无 ASan）

```powershell
# 只查语法与告警，最快
gcc -std=c11 -Wall -Wextra -Wpedantic -Wconversion -fsyntax-only src\x.c -I include

# 编译到对象
gcc -std=c11 -Wall -Wextra -c src\x.c -o build\x.o -I include

# 可执行 + 调试信息（主机跑测试用）
gcc -std=c99 -g -O0 -Wall -Wextra src\main.c src\uart.c test\test_uart.c -o build\tests.exe -I include
```

### 目标板（arm-none-eabi-gcc 15.2.1，**支持** `-fanalyzer`）

```powershell
arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -std=c11 -Wall -Wextra -Wpedantic ^
  -fanalyzer -fstack-usage -c src\uart.c -o build\uart.o -I include -I Drivers\CMSIS\Include

arm-none-eabi-size build\firmware.elf
arm-none-eabi-nm --size-sort -S build\firmware.elf | Select-Object -Last 15
```

`-fanalyzer` 的价值：能抓空指针解引用、重复释放、资源泄漏、部分越界；代价是慢 2–10 倍，只在大文件或可疑文件上开。

**已知误报**（实测）：固件的 `for(;;)` / `while(1)` 主循环会触发 `-Wanalyzer-infinite-loop`。这是主循环的正常形态，**不要**为了消警告去改造循环结构；在报告中说明"属预期误报"即可。同理，`-Wunused-but-set-variable` 对"仅用于占位/对齐"的缓冲区也可能是误报，需人工判断。

### 告警必须清零或显式说明

`-Wall -Wextra` 的每一条都要处理：**修掉**，或**写明为什么可以忽略**。不许"警告太多先不管"。

---

## 5 常见编译错误 → 根因 → 查法

| 报错 | 真实原因（按概率） | 怎么查 |
|---|---|---|
| `undefined reference to 'x'` | 没链接实现文件 / 函数名拼错 / C++ 名字修饰（需 `extern "C"`） / 库顺序不对 | `grep "\bx\s*("` 找定义；`nm` 看目标文件符号 |
| `multiple definition of 'x'` | 头文件里定义了变量（而非 `extern` 声明） | 头文件里找 `int x;` → 改 `extern int x;` + 一个 `.c` 定义 |
| `implicit declaration of function` | 缺 `#include` / 头文件路径未加 `-I` | 补 include，别靠隐式声明（C99 起非法） |
| `conflicting types for 'x'` | 声明与定义签名不一致 / 旧头文件残留 | 对比 `.h` 与 `.c` 的完整签名 |
| `storage size of 'x' isn't known` | 用了未定义完整类型的结构体 | 是否只前置声明了 `struct` 而未 `#include` 定义 |
| `undefined reference to 'sin'` | 缺 `-lm`（数学库） | 链接命令追加 `-lm` |
| `#include <x.h> No such file` | 路径大小写 / 未加 `-I` | `Get-ChildItem -Recurse -Filter x.h` |
| `region RAM overflowed` | 内存不够 | `arm-none-eabi-size` 看哪个段超；查大数组/字符串常量 |
| `undefined reference to '_sbrk'` | 用了 `malloc` 但没提供堆实现 | 嵌入式一般禁用动态内存，改用静态池 |
| linker script 相关 | `.ld` 段名与实际不匹配 | 对照启动文件与 `.ld` 的段定义 |

---

## 6 调试方法序（不要一上来就加 printf）

```
① 复现：给出一组必定触发的输入/操作（不能复现就先造复现条件）
② 定位范围：二分（注释一半/换输入/换模块），把范围缩到最小
③ 观察：断点(gdb) > 断言 > 定向日志（一条能区分两种假设的日志）
④ 提假设：写清"如果是 A 原因，那么 B 现象应该出现"
⑤ 最小验证：只验证这个假设，不同时改别的东西
⑥ 修复 + 回归：修完跑原用例 + 相邻用例
```

### 主机调试（gdb 8.1）

```powershell
gdb -batch -ex "run" -ex "bt" -ex "info locals" --args build\app.exe
```

### 日志纪律

- 一条日志必须**能区分两个假设**，否则是噪音；
- 加日志要能一键关掉（宏/级别），不要散落裸 `printf`；
- 调试完**删掉或降级**调试日志，并在修改报告中说明。

### 嵌入式（无在线调试器时）

| 手段 | 做法 |
|---|---|
| 串口打印 | 最小化输出，避免在 ISR 里打印 |
| 翻转 GPIO + 示波器/逻辑分析仪 | 最可靠的时序证据（需用户硬件配合） |
| 计数/状态变量 | 全局 `volatile` 计数，运行后由调试器或串口读出 |
| HardFault 定位 | 保存 `LR/PC/PSR`，用 `arm-none-eabi-addr2line -e firmware.elf <addr>` 还原行号 |
| `arm-none-eabi-size/nm` | 判断是否内存溢出/栈不够导致的"随机死机" |

---

## 7 通用缺陷模式（C/C++，逐条对照）

| 类别 | 典型错误 | 检查点 |
|---|---|---|
| 边界 | 数组越界 1 个、`<=` 写成 `<` | 循环上下界、缓冲区长度参数 |
| 空指针 | 未判 `malloc`/函数返回值 | 每个指针解引用前 |
| 未初始化 | 局部变量未赋值就使用 | `-Wmaybe-uninitialized`，初始化习惯 |
| 资源 | 每条返回路径都释放了吗 | 早退 `return` 分支 |
| 整数 | 有符号/无符号混用、溢出、移位 | `-Wconversion`、`size_t` vs `int` |
| 字符串 | `strcpy` 越界、缺 `'\0'` | 用 `snprintf`，检查返回值 |
| 格式串 | `%d` 传 `long` | 与类型严格匹配 |
| 返回值 | 忽略 `fwrite/fclose/...` 失败 | 关键路径必须检查 |
| 逻辑 | `=` 与 `==`、`&&`/`||` 优先级 | 编译器告警 + 括号 |
| 重复代码 | 复制粘贴后忘改一处 | 相似块对比 |

---

## 8 重构规则

1. **先有测试再重构**；没有测试就先补最小回归用例（哪怕只是一个 `main` 里的断言）。
2. **一次一种手法**：抽函数 / 改命名 / 移文件，分开做，每步编译。
3. **不改行为**。要改行为，属于"功能变更"，另开一轮。
4. 重构完成对比：`arm-none-eabi-size` 前后差异、关键路径是否变慢。
5. 记录"为什么重构"（可维护性/重复/耦合），不要只写"优化代码"。

---

## 9 收尾（缺一项就不算完成）

- 编译：命令 + 结果（通过/失败 + 关键输出）
- 运行/测试：用例 + 结果 + 证据级别（V3/V4）
- 变更范围：`file:line` 列表；确认没夹带无关改动
- 遗留：未验证的部分、已知限制
- 知识库：接口/职责变了就更新 `MODULES.md`，并 `stale_check.py --mark-verified`

模板见 `templates/change-report.md`。