# 证据、引用与不确定性管理

> 职责：维护来源台账与断言台账；消费 S01 成果；执行定向核验；处理冲突与时效；保证引用完整性。
> 读取时机：S3 建台账；S7 核验；出现来源冲突/版本争议时；交付前引用检查。
> 不重复：S01 的完整研究流程不在本 Skill 内实现；只消费其成果 + 有限定向核验。

## 1 来源台账

每条来源字段：

| 字段 | 必填 | 说明 |
|---|:--:|---|
| `id` | 是 | `SRC-###`（本文命名空间，不复用） |
| `title` | 是 | 标题（英文原标题保留） |
| `locator` | 是 | URL / 文件路径 / 章节 |
| `publisher` | 是 | 发布机构/作者 |
| `publishedAt` / `accessedAt` | 是/否 | ISO 8601；无法确认置 null 并提示 |
| `version` | 否 | 文档/软件/标准版本 |
| `type` | 是 | official_doc/spec/repo/paper/book/community/report/news/blog/statistics/other |
| `language` | 是 | BCP-47 |
| `rating` | 是 | S/A/B/C/D（沿用 S01） |
| `ratingBasis` | 是 | 评级依据（发布主体/可核验性/时间/用途匹配） |
| `status` | 是 | active/stale/excluded/unreachable |
| `excludeReason` | 条件 | 排除时必填 |
| `origin` | 是 | user/s01/web-verify/extraction |
| `originId` | 否 | 来自 S01 时：`R-<researchId>/S-###` |

**规则**：同一来源多入口去重；镜像/转载指回原始出处；来源不重复计数制造"多来源印证"。

## 2 来源评级（S/A/B/C/D）

| 等级 | 定义 | 典型 |
|---|---|---|
| S | 一手权威 | 官方文档/规范/标准原文/维护者发布/同行评审原始论文/官方仓库代码 |
| A | 高质量二手，可回溯一手 | 权威教材、机构综述、官方博客二次说明 |
| B | 专业来源，方法可核查 | 行业报告（有方法）、高质量技术社区、政府统计 |
| C | 一般来源，仅辅助 | 新闻、个人博客、经验分享、聚合站 |
| D | 不可核验 | 匿名帖、无出处转载、AI 生成内容、营销软文 |

- 按"具体资料 + 具体用途"评级，不按域名永久映射。
- C/D 不得单独支撑安全提示、参数结论、规范条文。
- 技术断言优先 S/A；关键结论至少 1 条第一层来源，或说明为何不存在。

## 3 断言台账

| 字段 | 必填 | 说明 |
|---|:--:|---|
| `id` | 是 | `CL-##` |
| `statement` | 是 | 可判真假的陈述 |
| `type` | 是 | 断言性质：fact/inference/recommendation/opinion；**无来源且无法归类的陈述才用 unverified** |
| `verification` | 是 | 证据状态：verified/documented/unverified/conflicting |
| `sourceIds[]` | 是 | 本文 `SRC-###`；fact/verified 不得为空 |
| `evidenceIds[]` | 否 | S01 证据：`R-<researchId>/E-###` |
| `sourceResearch` | 否 | S01 研究 ID |
| `originId` | 否 | S01 原始编号（如 `R-20261118-002/C-01`） |
| `sourceConfidence` | 否 | S01 置信度：高/中/低/未确定 |
| `locator` | 条件 | 直接引用的定位 |
| `sectionId` | 是 | 所属章节 |
| `asOf` | 否 | 有效时点 |
| `versionRange` | 否 | 适用版本 |
| `codeStatus` | 否 | tested/compiled/untested |
| `dataKind` | 否 | measured/estimated/modeled/reported |
| `status` | 是 | active/superseded/disputed |
| `supersededBy` | 否 | 新断言 id |

**唯一写入者**：证据台账模块；写作模块只能提交"断言候选"，核验模块只能提交"核验结果/变更请求"。

**`type` 与 `verification` 不重叠**：

- `type` 回答"这句话是什么性质"；`verification` 回答"证据到什么程度"。
- 有来源但未实测：`type=fact` + `verification=documented`；无来源：`type=unverified`（或 inference/opinion）+ `verification=unverified`。
- `verified` 必须有来源；`type=unverified` 不得同时 `verification=verified`。
- `unverified` 是**状态**，不得用来表达"未执行/未实测"（那属于 `verification=documented/untested` 或 `codeStatus`）。

**四类断言判据与例子**：

| 类型 | 判句 | 正例 | 反例 |
|---|---|---|---|
| fact | 可被证据判真假的陈述 | "该寄存器默认值为 0x1F" | "这个设计很优雅" |
| inference | 由事实推出、需给推理链 | "因此该配置在高并发下可能超时" | "官方说它很快" |
| recommendation | 建议/取舍，含条件 | "若目标是低延迟，建议启用 DMA" | "必须用 DMA" |
| opinion | 主观评价，不承担事实责任 | "这种写法可读性较差" | "该 API 存在竞态"（应为 fact） |

**`[CL-##]` 只是可追溯标记，不替代类别标注**；关键断言（参数/命令/版本/安全）必须同时有类别标记（或正文明确判句）并在台账有对应 claim。

## 4 从 S01 消费（映射表）

| S01 字段 | 本 Skill 字段 | 规则 |
|---|---|---|
| `conclusions[].id`（C-##） | `originId` | 命名空间化：`R-<researchId>/C-##`；禁止直接复用 C-## |
| `statement` | `statement` | 直接映射 |
| `verification` | `verification` | single-source→documented；cross-checked→verified（需 ≥2 独立来源证据）；primary-traced→verified；unverified→unverified；disputed→conflicting |
| `confidence` | `sourceConfidence` | 原样保留，不丢失 |
| `evidenceIds[]` | `evidenceIds[]` | 命名空间化 `R-<researchId>/E-###` |
| `sources[].id`（S-##） | `originId` | 命名空间化；本 Skill 来源另用 `SRC-###` |
| `sources[].rating/ratingBasis` | 同名字段 | 沿用，不重新评级 |
| `evidence[]` | `locator`/`quote` | 摘录与定位；直接引用进 `citations[]` |
| `counterResearch[]` | `conflicts[]` 或 `limitations[]` | 形成对抗证据→冲突；未形成→局限 |
| `limitations[]` | `limitations[]` | 必须传递 |
| `schemaVersion` | 校验 | 不匹配 → 降级读 `report.md` 并声明 |

**只读**：不修改 S01 的 `research_result.json`、`report.md`、`sources.md`、`evidence.md`、`K1-sources/`、`research-log.md`、`CHANGELOG.md`；不写 S01 的 `derived/`。

**S01 必填 16 项（校验清单）**：`schemaVersion`、`researchId`、`meta`、`brief`、`scope`、`questions`、`sources`、`evidence`、`conclusions`、`conflicts`、`assumptions`、`limitations`、`qualityReview`、`artifacts`、`log`、`changelog`。缺项或版本不匹配 → 降级读 `report.md` 并声明；不得假设已校验。

## 5 定向核验（不做研究）

| 项 | 规则 |
|---|---|
| 优先 | 参数/命令/接口/版本/标准条款/安全条件 |
| 硬门槛 | 单条断言 ≤3 次读取/检索；不得同时核对 ≥2 个新主题 |
| 超限 | 转 `research-request.md`，停止核验 |
| 检索降级 | `search.run` → `web_search` → 直接读已知 URL → 标 `unverified` |
| 读取降级 | `read.fetch` → `web_fetch` → 替代来源 → 标 `unreachable` |
| 记录 | 每次：断言 id、目标、通道、结果、计数 |
| 失败 | 不阻断任务；标 `unverified` 并披露 |

**禁止**：把核验扩展成"顺便调研一个新主题"；无目的重复检索；凭记忆补全。

## 6 验证状态判定

| 状态 | 判定 | 正文写法 |
|---|---|---|
| verified | 官方文档明确 / 实际运行 / 可复现验证 | `[事实]` |
| documented | 有文档依据但未实测 | `[事实]`（注明"文档依据"） |
| unverified | 未核实/证据不足 | `[未验证]` + 核实途径 |
| conflicting | 来源冲突 | 并列陈述 + 冲突登记 |
| input-limited | 输入缺失（参数/版本/素材未提供） | `[待提供]` + 缺口条目；不得虚填 |
| illustrative | 演示/虚构数据 | `[示例]` + "仅演示，不代表真实数据" |

> `input-limited`/`illustrative` 是**正文标注状态**，不是 `verification` 枚举值；台账 `verification` 仍为 verified/documented/unverified/conflicting，配套用 `type` 与 `limitations[]` 表达。

**规则**：`verified` 必须有证据；未运行不得写"已验证"；估算不得写成实测。

## 7 冲突处理

1. 触发：同一事实多来源不一致。
2. 登记 `conflicts[]`：

| 字段 | 形状 | 说明 |
|---|---|---|
| `id` | `C-##` | 冲突编号 |
| `positions[]` | `[{stance, sourceId, quote}]` | 双方陈述与证据 |
| `attribution{}` | 对象 | 归因：version/scope/time/env/metric/error |
| `status` | `resolved/unresolved` | 是否可裁决 |
| `impact` | 字符串 | 影响章节/断言 |
3. 可解：给裁决与依据；正文用一致结论。
4. 不可解：`unresolved`；正文并列；标 `[未验证]`；局限披露；给验证建议。
5. 禁止：隐藏冲突；强行择一；删除一方来源。
6. **冲突必须落到断言**：存在 `unresolved` 冲突时，正文相关断言至少一条标 `verification=conflicting`；否则视为未登记（G3 不通过）。

## 8 时效与版本

- 文档级：`asOf` + `versionRange`；技术文档必填。
- 来源级：`publishedAt`/`updatedAt`/`version`；过期标 `stale`。
- 断言级：`asOf`/`versionRange`；版本敏感内容逐条标。
- 版本变化导致失效：标 `superseded` + 替代项 + 更新建议；不删除。

## 9 引用与转引

- 直接引用：短摘录 + 出处 + 定位（章节/条款/行号）；写入 `citations[]` 且 `kind=direct`。
- 转述：`kind=paraphrase`；仍需定位。
- 转引：`kind=secondary` + "转引自"；不得伪装一手；转引最高 `documented`，除非已回溯到一手原文。
- 大段复制禁止；引用图表注明来源与许可。

## 10 引用完整性检查

1. 扫描正文 `[CL-##]`、`[SRC-###]`、`§x.y`、`EX-##`、`CH-##`。
2. 每个标记必须在台账/结构中存在。
3. 直接引用必须有定位与摘录。
4. 转引必须有"转引自"。
5. 统计断链数与重号；**断链 0** 才能过 G3/G5。
6. 结果写入 `review.md` 与 `delivery.md`。

## 11 不确定性表达

| 情形 | 写法 |
|---|---|
| 无来源 | `[未验证]` + "未找到可靠来源；建议核实：…" |
| 冲突 | "两种说法并存：A（来源）/B（来源）；未确定" |
| 版本不确定 | "适用于 X 版本；Y 版本可能不同（未验证）" |
| 外部受限 | "因网络/权限/配额限制，未能核验" + 影响范围 |
| 推导 | `[推论]` + 依赖的事实断言 + 推理说明 |
| 输入缺失 | `[待提供]` + 缺少什么、影响哪章、如何补 |
| 演示数据 | `[示例]` + 明确"虚构/仅演示" |
| 教学简化 | `[简化]` + 简化边界 |
| 类比 | `[类比]` + 不成立处 |

**禁止**：众所周知/一般来说/据说；用模糊限定词掩盖未知。