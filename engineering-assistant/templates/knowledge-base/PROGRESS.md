# 开发进度

> 滚动窗口：只保留最近 15 条，更早的按月归入 `archive/PROGRESS-YYYY-MM.md`。
> 一条 = 一次可验证的进展（不是"今天很忙"）。

---

## 模板

```markdown
### <YYYY-MM-DD> <做什么>
- 改动：<file:line>
- 验证：<编译/测试结果，证据级别 V?>
- 影响：<接口/数据/行为是否变化>
- 下一步：<…>
```

---

## 记录

### `<YYYY-MM-DD>` `<初始化知识库>`

- 改动：新建 `.ea/`（PROJECT_MAP / MODULES / DECISIONS / ISSUES / PROGRESS / GLOSSARY）
- 验证：`project_scan.py --init --update-state` 成功；`stale_check.py` 无异常
- 影响：无代码改动
- 下一步：`<补全 MODULES.md 的 X 模块>`

<!-- 新记录追加在下方 -->