# 术语表

> 目的：防止同一样东西有多个叫法，导致检索失效、口头沟通错位。
> 上限 80 条；合并同义、删除废弃。

## 约定

| 规范叫法 | 别称/易混 | 定义 | 首次出现 |
|---|---|---|---|
| `<环形缓冲>` | `<ring buffer, 循环队列>` | `<固定容量、head/tail 下标的 FIFO>` | `<src/ringbuf.c>` |
| `<帧>` | `<包, packet, frame>` | `<本项目中统一称"帧"，含头+载荷+校验>` | `<src/protocol.c>` |

## 缩写

| 缩写 | 全称 | 说明 |
|---|---|---|
| `<ISR>` | Interrupt Service Routine | `<中断服务函数，命名 *_IRQHandler>` |
| `<BSP>` | Board Support Package | `<板级支持，位于 bsp/>` |

## 命名约定

- 模块前缀：`<uart_ / ring_ / proto_>`
- 全局变量：`<g_ 前缀>`
- 静态函数：`<static + 小写下划线>`
- 宏：`<全大写；常量用 #define 还是 enum 的约定>`

<!-- 新术语追加在下方 -->