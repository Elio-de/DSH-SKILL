# 文档类型路由（profiles/index）

> 读取时机：S4 选型；S5–S6 写作前（只读命中的 1–2 个 profile）。
> 规则：profile 只放"类型差异"，通用规则在 `tech-doc.md`/`learning.md`；一次最多读 2 个。

## 类型 → profile

| 任务书类别 | profile | 模式 |
|---|---|---|
| 技术手册 / 软件开发手册 / 硬件开发手册 | `manual.md` | A |
| 操作说明书 / 作业指导书 | `sop.md` | A |
| 开发规范 | `spec.md` | A |
| 技术方案 | `design.md` | A |
| 技术研究报告 / 项目技术报告 / 技术分析报告 | `report.md` | A |
| 参考文档（API/参数） | `reference.md` | A |
| 故障排查 / FAQ | `troubleshooting.md` | A |
| 知识点讲解 / 入门材料 / 科普 | `tutorial.md` | B |
| 学习教材 | `textbook.md` | B |
| 学习讲义 | `lecture.md` | B |
| 课程笔记 | `notes.md` | B |
| 学习路线 | `roadmap.md` | B |
| 练习题和答案解析 | `exercise.md` | B |
| 专业知识体系整理 | `knowledge-map.md` | B |

## 组合规则

- 主类型 1 个；次类型最多 1 个（如 manual + troubleshooting）。
- 混合请求（M-HYBRID）：主件 A profile + 派生件 B profile，各读 1 个。
- 类型不明确：取最接近的 profile，写 `fallbackReason`，不得用"通用文档"糊弄。

## fallback 顺序

1. 有操作步骤 → `manual` / `sop`
2. 有规则条文 → `spec`
3. 有方案对比 → `design`
4. 有研究结论与证据 → `report`
5. 以参数/条目为主 → `reference`
6. 以排障为主 → `troubleshooting`
7. 以教学/练习为主 → `tutorial` / `textbook` / `lecture` / `exercise`

## 易混类型边界

| 类型 | 判定要点 |
|---|---|
| `textbook`（教材） | 多章、系统学习、完整练习与复习；篇幅最大 |
| `lecture`（讲义） | 单次课堂/培训配套，节奏与重点优先，目标 2–4 |
| `tutorial`（教程） | 技能入门，围绕一条主线讲清一个主题 |
| `exercise`（题集） | 以题目/答案/解析为主体，不重复教材讲解 |
| `knowledge-map`（体系） | 以结构、关联、索引为主；练习默认仍含 |

## 加载上限

- profile ≤2；模板按正文类型选 1 个；示例只在格式不确定时读。
- 不得因为"多读几个更稳"而加载全部 profile。

## profile 必含内容

每个 profile 文件包含：适用场景、骨架要点、必查维度（A ≥5 / B 教学要点）、常见缺陷、验收锚点、默认参数（档位/预算/练习策略）。

**口径**：profile 的章节数是"标题合并建议"，12 类要素不可缺；要素口径见 `tech-doc.md §1`，判定见 `quality.md` TQ-01。