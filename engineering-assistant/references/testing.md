# 测试与验证（testing）

> 核心一句话：**没有实际执行的测试，不得声称通过。**
> 加载时机：设计测试、写测试、跑测试、回归、需要"证明它是对的"。

---

## 1 四层验证与证据级别（一一对应）

| 层 | 做什么 | 能达到的证据级别 | 本机可行性 |
|---|---|---|---|
| 1 静态分析 | 编译器告警、`-fanalyzer`、人工规则 | 至多 **V2–V3** | ✅（ARM 侧有 analyzer） |
| 2 编译验证 | 能编过、链接通过、段不溢出 | **V3** | ✅ |
| 3 软件测试 | 主机运行用例 | **V4** | ✅（C：自建 harness；Python：unittest） |
| 4 硬件验证 | 目标板实测 | **V5** | ❌ AI 不可执行，需用户 |

**禁止跨层冒充**：编译过 ≠ 功能对；主机测过 ≠ 板子上对（时钟、外设、中断都不同）。

---

## 2 先看现有测试体系（不要另起一套）

```powershell
glob  pattern: "**/*{test,tests,spec}*"
grep  pattern: "assert|TEST_|UNITY_BEGIN|def test_"  include: "*.{c,cpp,py}"
```

判定：
| 发现 | 做法 |
|---|---|
| 有框架（Unity/CMock/CppUTest/pytest） | 沿用其约定，不引入第二套 |
| 只有零散 `assert` 的 `main` | 沿用，逐步补 |
| 完全没有 | 先建"最小可跑"的 harness，别一上来搭大框架 |

本机现状：**无 pytest、无 Unity** → Python 用 `unittest`（标准库）；C 用自建 harness（见 §4）。

---

## 3 用例设计四法（覆盖"想得到"和"想不到"）

| 方法 | 用法 | 例 |
|---|---|---|
| 等价类 | 每个输入域取一个代表 | 合法/非法/空 |
| 边界值 | 用**边界的三个点**：下界-1、下界、上界、上界+1 | 缓冲区长度 15/16/17 |
| 异常路径 | 每个错误分支至少一例 | 参数 NULL、超时、校验失败 |
| 状态迁移 | 有状态机的，测非法跳转 | IDLE→RUN 合法；RUN→IDLE 需复位 |

**覆盖优先级**：错误处理分支 > 边界 > 主流程。主流程往往已经手工验过，错误分支才是 bug 聚集地。

---

## 4 C 主机测试骨架（零依赖，可直接用）

思路：**把可测逻辑从硬件访问中抽出来**，在主机编译运行。

```c
/* test/test_uart.c —— 主机可跑的回归测试 */
#include <stdio.h>
#include <string.h>
#include "uart_frame.h"     /* 被剥离出来的纯逻辑 */

static int failures = 0;

#define CHECK(cond, msg) do {                         \
    if (!(cond)) { printf("[FAIL] %s (line %d)\n", msg, __LINE__); failures++; } \
    else { printf("[ ok ] %s\n", msg); }              \
} while (0)

static void test_frame_checksum(void)
{
    uint8_t buf[8] = {0xAA, 0x01, 0x02, 0x00};
    buf[3] = frame_checksum(buf, 3);
    CHECK(frame_verify(buf, 4) == 0, "checksum accepts valid frame");
    buf[3] ^= 0xFF;
    CHECK(frame_verify(buf, 4) != 0, "checksum rejects corrupt frame");
}

static void test_ring_buffer_boundary(void)
{
    ring_t r; ring_init(&r);
    for (int i = 0; i < RING_CAP; i++) { CHECK(ring_push(&r, (uint8_t)i) == 0, "push until full"); }
    CHECK(ring_push(&r, 0xEE) != 0, "push fails when full");
    for (int i = 0; i < RING_CAP; i++) { uint8_t v; CHECK(ring_pop(&r, &v) == 0, "pop until empty"); }
    CHECK(ring_pop(&r, NULL) != 0, "pop fails when empty");
}

int main(void)
{
    test_frame_checksum();
    test_ring_buffer_boundary();
    printf("\n%s (%d failure(s))\n", failures ? "FAILED" : "PASSED", failures);
    return failures ? 1 : 0;
}
```

编译运行（PS 不展开通配符，注意用数组）：

```powershell
$src = (Get-ChildItem src\*.c | Where-Object { $_.Name -notmatch 'main\.c' }).FullName
gcc -std=c11 -Wall -Wextra -g -O0 -I include -I test $src test\test_uart.c -o build\tests.exe
.\build\tests.exe
"EXIT=$LASTEXITCODE"
```

> 用退出码判定成败，便于 CI/脚本化。**不要用"看输出像是对的"判定。**

---

## 5 硬件相关代码怎么测（桩与替身）

| 依赖 | 手段 | 注意事项 |
|---|---|---|
| 寄存器读写 | 桩函数替代 `HAL_GPIO_ReadPin` 等 | 桩里记录调用次数/参数，断言"是否按预期访问" |
| 时间/延时 | 注入 `now_ms()` 而非直接调用 | 测试里用假时钟，能测超时逻辑 |
| 中断 | 直接调用 ISR 函数并检查共享状态 | 不能模拟真实抢占时序，只能测逻辑 |
| 外设状态机 | 用状态表驱动 | 覆盖"忙/错误/就绪"分支 |

**措辞纪律**：桩测结论只能写"逻辑在模拟条件下正确（V4，桩测）"，**不得**写"硬件已验证"。

---

## 6 嵌入式分层建议（可测性的前提）

```
应用逻辑（纯函数，可主机测试）
      ↑
设备抽象（接口 + 桩可替换）
      ↑
HAL / 寄存器（不可测，只能审查 + 硬件验证）
```

如果代码把业务逻辑写死在 `HAL_` 调用之间 → 先说明"当前不可测"，再建议抽取；**不要为了测试擅自大改结构**（属重构，另开一轮）。

---

## 7 Python 测试

```powershell
python -m unittest discover -s tests -v
```

- 用标准库 `unittest`（本机无 pytest）；
- 断言要具体（`assertEqual(actual, expected, msg)`），不要只 `assertTrue(x)`；
- 外部依赖用 `unittest.mock` 替换，不真的连硬件/网络。

---

## 8 回归（改完之后必做）

```
1. 先跑一遍现有测试，记录基线：N 通过 / M 失败（失败项先确认是既有问题）
2. 做改动
3. 全量重跑，与基线对比
4. 任何"原本通过现在失败"= 回归，必须处理或明确说明原因
5. 把结果写进修改报告的"验证情况"
```

没有基线就没法谈回归——**改动前先跑一次**，这一步最常被跳过。

---

## 9 覆盖率（有 gcc 就能用）

```powershell
gcc -std=c11 --coverage -O0 -I include src\*.c test\test_uart.c -o build\tests_cov.exe
.\build\tests_cov.exe
gcov src\uart.c
```

`gcov` 为 gcc 自带（本机 gcc 8.1 可用）。可给"行覆盖/分支覆盖"的真实数字，比"我觉得覆盖够了"有意义。
嵌入式目标代码无法直接跑覆盖率——只能在主机测移植后的逻辑。

---

## 10 结果记录（写进报告，缺项即不合格）

```markdown
### 测试结果
- 环境：gcc 8.1.0 / Windows，主机测试（非硬件）
- 命令：gcc … && .\build\tests.exe
- 结果：12 通过 / 0 失败，退出码 0
- 证据级别：V4（主机软件测试）
- 未覆盖：真实中断时序、硬件寄存器行为、上电初始化
```

---

## 11 禁止

1. 没跑就写"测试通过"；
2. 跑了一个用例就代表全部；
3. 跳过失败用例不提；
4. 把主机测试结论写成硬件验证；
5. 为了提高覆盖率写"无断言测试"；
6. 为了测试擅自改动被测代码的结构而不说明。