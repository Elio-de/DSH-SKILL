# 与其他 Skill 的协作（文件契约）

> 职责：定义与 S01/S03/S04/S06/S10/S14/S15/S16 的只读/交接契约、能力缺失降级、交接包消费说明。
> 读取时机：S0 能力探测；S11 生成交接文件；涉及下游时。
> 原则：Skill 之间不能互调；只通过工作区文件交接；不冒充"已调用"。

## 1 通用原则

1. 无运行时互调：不调用、不假设其他 Skill 已执行。
2. 只读上游：S01 产物只读；不改写、不覆盖。
3. 文件即接口：交接包 + manifest + 说明文件。
4. 能力诚实：下游缺失时声明"未执行/需下游完成"。
5. 显式触发：转换只在用户明确要求时发生。

## 2 S01 research-engine（上游，已安装）

| 项 | 规则 |
|---|---|
| 读取 | `research_result.json`（16 项必填：schemaVersion、researchId、meta、brief、scope、questions、sources、evidence、conclusions、conflicts、assumptions、limitations、qualityReview、artifacts、log、changelog）、`report.md`、`sources.md`、`evidence.md`、`INTERFACE.md` |
| 校验 | 缺项/版本不匹配 → 降级读 `report.md` 并声明；不得假设"已校验" |
| 映射 | 按 `evidence.md` §4；保留命名空间；传递 `limitations[]` |
| 只读 | 不修改 S01 任何文件；不写 S01 `derived/` |
| 不足 | 生成 `research-request.md`；不自行做开放式研究 |
| 版本 | 不匹配 → 降级读 `report.md` 并声明 |
| 更新 | S01 更新后不自动重写本文；走修订流程（新版本） |

## 3 S03 document-converter（下游，未安装）

| 项 | 规则 |
|---|---|
| 默认 | 不转换、不生成请求、不主动询问 |
| 触发 | 用户明确提出格式转换 |
| 请求 | `conversionRequests[]` + `conversion-request.md`（字段见 `delivery.md` §4） |
| 执行 | S03 未安装；若 office 可用且用户授权，可由本 Skill **先 `skill({name:"office"})` 激活**后驱动 office 执行一次，`executedBy=S02-office` |
| 验证 | 文件存在、可打开、指标在声明区间；否则 `failed`/`unavailable` |
| 禁止 | 声称已生成但无文件；Markdown 冒充 DOCX/PPTX/PDF |

## 4 S04 knowledge-management（下游，未安装）

- 输出 `knowledgeCandidates[]`（标题/摘要/标签/关联/来源/建议路径）+ `knowledge-handoff.md`。
- 不写 Obsidian、不建双链、不执行入库。
- 声明"待 S04 处理"。

## 5 S06 quality-assurance（下游，未安装）

- 输出 `review-request.md`（范围/标准/已知缺陷/重点风险）+ 只读交接包。
- 本 Skill 自检 ≠ 独立审查；不得写"已通过独立审查"。
- 可用 `subagent` 内部复核，记录 `review.internalReview[]`，性质写"内部复核"。
- S06 意见回传 → 按缺陷闭环处理（`quality.md` §5）。

## 6 S10 / S14（下游，未安装）

- 输出 `interaction-brief.md`：学习目标、知识难点、建议交互点（可视化/仿真/测验/分步引导）、数据需求。
- 不生成 HTML、不做交互实现；声明 S10/S14 未安装。
- 已安装的 `offline-learning-html` 属相邻能力；仅当用户明确要求时使用，本 Skill 不冒充其实现。

## 7 S15 思维导图（下游，未安装）

- 输出 `outline.md` + `assets/mindmap-source.mmd`（Mermaid 源码）。
- 不生成 `.xmind`/FreeMind；声明无该能力。

## 8 S16 资料提取（上游/旁路，未安装）

- 接收已提取文本/表格/公式；`extraction-needs.md` 描述缺口。
- PDF 文本可经 office 读取；扫描件/图片无 OCR 承诺。
- 提取结果须标注来源与可信度。

## 9 能力缺失降级

| 缺失 | 降级 | 声明位置 |
|---|---|---|
| S01 产物不可读 | 只用用户素材；缺口标 `unverified`；生成 `research-request.md` | `delivery.md`、`limitations[]` |
| office 不可用 | 只交 Markdown + 转换请求 `unavailable` | `delivery.md`、`conversionRequests[]` |
| 子代理不可用 | 不做内部复核；自检照常 | `review.internalReview[]` |
| 文档读取不可用（DOCX/PPTX） | 请用户导出 Markdown/PDF；或标不可读 | `gaps[]`、`delivery.md` |
| Web 不可用 | 标 `unverified`；不编造 | `limitations[]` |
| 图片/OCR 缺失 | 只引用可读信息；请用户提供文本 | `limitations[]` |
| Mermaid 渲染缺失 | 只交源码 + "未渲染" | `delivery.md` |
| `python`/校验脚本不可用 | 人工契约清单；AC-014 记 LIMITED | `delivery.md`、`review.md` |

## 10 交接包

见 `delivery.md` §5。核心：下游只凭交接包即可消费，不需要读内部过程文件。

## 11 禁止事项

- 不调用其他 Skill；不写其他 Skill 目录。
- 不修改 DSH 配置、不安装插件。
- 不声称"已交给 S03/S04/S06"除非文件真实生成。
- 不把自检包装为独立审查。