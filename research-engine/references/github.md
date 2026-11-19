# GitHub 专项研究（M09）

> 职责：九维分析、端点与配额、License/依赖/安全口径、维护状态判定、披露话术。
> 适用：识别到 GitHub 仓库为研究对象时。不适用：通用来源评级（`sources.md`）。

## 1. 九维分析表（FR-040）

| # | 维度 | 要取什么 | 常用端点/来源 |
|---|---|---|---|
| 1 | 维护状态 | 最近提交、Release 节奏、Issue 响应、贡献者集中度 | `/repos/{o}/{r}`、`/commits`、`/releases`、`/issues` |
| 2 | License | SPDX 标识、对商用的限制与义务 | `/repos/{o}/{r}` → `license.spdx_id`、`LICENSE` 文件 |
| 3 | 架构 | 模块划分、入口、关键设计 | 仓库树、根 README、`src/` 结构（`web_fetch` 网页版） |
| 4 | 依赖 | 清单、锁定文件、已知风险 | `package.json`/`requirements.txt`/`go.mod` 等 |
| 5 | Release | 语义化版本、破坏性变更、变更日志 | `/releases`、`CHANGELOG.md` |
| 6 | Issue | 未解决比例、类型分布、是否有维护者回复 | `/issues?state=open` |
| 7 | 测试 | CI 配置、测试目录、覆盖信号 | `.github/workflows/`、`tests/` |
| 8 | 安全 | `SECURITY.md`、安全公告、依赖漏洞 | `/security/advisories`、仓库 SECURITY.md |
| 9 | 复现性 | 构建步骤、固定版本、环境要求 | README 的 Build/Install 段、Dockerfile |

**验收**：九维至少覆盖 **7 维**并说明未覆盖原因；缺 License 与维护状态 → 判失败。

## 2. 端点与配额（LIM-005 / IF-008）

- 只用**匿名 REST**：`https://api.github.com/repos/{owner}/{repo}` 等公开端点，经 `web_fetch` 获取。
- 匿名配额 **60 次/小时**（按 IP）。必须在 `log.queries[]` 记录调用次数与目标。
- 无 `git`/`gh` CLI；`mcp__github__*` **未认证、不可用**（不得声称已使用）。
- 配额策略：**先取决策必需的端点**（repo 元数据、releases、近期 issues），再取补充项；超预算时停止并标注覆盖不足。
- 配额耗尽 → 标"受限完成"（FR-057），说明未覆盖维度。

**建议顺序（≤8 次）**：`/repos/{o}/{r}` → `/releases?per_page=5` → `/commits?per_page=10` → `/issues?state=open&per_page=20` → `LICENSE` 原文 → `SECURITY.md` → `README`（网页）→ 依赖清单。

## 3. 维护状态判定（FR-041）

| 判定 | 参考判据（至少 3 个指标支撑） |
|---|---|
| 活跃 | 近 90 天有提交；近 6 个月有 Release；Issue 有维护者回复 |
| 维护中 | 近 12 个月有提交；有 Release；Issue 响应较慢 |
| 低活跃 | 近 12 个月提交零星；Release 稀疏 |
| 停滞 | 近 12 个月无提交或无 Release；Issue 无响应 |
| unknown | 数据不足，**不得猜测** |

必须给出指标值（提交频次、最近 Release 日期、open issue 数、贡献者数），不能只写结论词。

## 4. License 与供应链（FR-042）

- 明确 SPDX（如 MIT / Apache-2.0 / GPL-3.0），并说明**义务**（保留版权声明、披露修改、传染性范围）。
- 列关键依赖与版本；检查是否有已知漏洞公告（有则记录来源与日期）。
- 结论必须标注：**"基于公开信息，非法律意见"**。
- 不得在无检索依据时声称"无安全风险"。

## 5. 禁止以 Star 为单一判据（FR-043）

- Star **只能作为背景指标之一**。
- 结论须由 ≥2 类非 Star 依据支撑（维护状态、测试、文档、Issue 质量、发布记录、依赖健康度）。
- "Star 多所以质量好" → 直接判失败。
- 数据不足判断时明说"数据不足"，不要把流行度当质量。

## 6. 生产可用性评估的写法

```markdown
### 生产可用性（基于公开信息，非法律意见）
| 维度 | 结论 | 依据 |
|---|---|---|
| License | MIT，允许商用，需保留版权与许可声明 | repo.license.spdx_id = MIT [E-0xx] |
| 维护 | 维护中：近 90 天 12 次提交、最近 Release 2026-09 | /commits、/releases [E-0xx] |
| 依赖 | 8 个直接依赖，无已知高危公告（检索日期 2026-11-18） | 依赖清单 + 公告检索 [E-0xx] |
| 测试 | 有 CI，含 3 个 workflow | .github/workflows [E-0xx] |
| 风险 | Issue 积压 240+ 未解决；维护者为少量核心贡献者 | /issues、贡献者分布 [E-0xx] |
```

## 7. 披露话术（避免夸大）

- 可以说："截至 <日期>，公开信息显示……"
- 不可以说："该项目一定适合生产""绝无安全风险""已被广泛验证"。
- 覆盖不足时必须写："本次未覆盖 X 维，原因是 <配额/端点不可达>"。

## 8. 反例

- 只看 Star 与 README 就下结论 → FR-043 违规。
- 无 License 结论 → 判失败。
- 声称使用 MCP GitHub 工具 → 虚构能力。
- 配额超限未说明 → LIM-005 违规。
- 把"活跃"直接等同"生产就绪" → 逻辑越界。