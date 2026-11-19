# 提交前自检（pre-commit）

> 本机无 Git 时，第 1–4 节仍然有效（用于"该不该把这些文件纳入版本管理"的判断），第 5 节无法执行。

## 一、改动内容

- [ ] 我逐行看过这次 diff（不是只看文件列表）
- [ ] **没有夹带无关改动**（顺手的格式化、无关的重命名）
- [ ] **没有调试残留**：`printf` / `console.log` / `TODO` / `FIXME` / 临时注释
- [ ] 没有注释掉的大段旧代码

## 二、构建产物与临时文件

- [ ] 没有把 `build/`、`*.o`、`*.exe`、`*.elf`、`*.hex`、`*.map` 纳入
- [ ] 没有把 `.venv/`、`node_modules/`、`__pycache__/` 纳入
- [ ] 没有把编辑器/IDE 个人配置纳入（如 `.vscode/settings.json` 里的个人路径）
- [ ] `.gitignore` 覆盖了上述内容

## 三、敏感信息（纯本地扫描，不外发）

```powershell
Get-ChildItem -Recurse -File -Include *.c,*.h,*.py,*.json,*.ini,*.yaml,*.yml,*.md |
  Select-String -Pattern 'api[_-]?key\s*[:=]|secret\s*[:=]|passw(or)?d\s*[:=]',
                          'BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY',
                          'ghp_[A-Za-z0-9]{20,}', 'AKIA[0-9A-Z]{16}', 'sk-[A-Za-z0-9]{20,}' |
  Select-Object Path, LineNumber -First 40
```

- [ ] 扫描无命中，或命中项已确认为示例/占位
- [ ] 没有硬编码的 WiFi 密码 / Token / 服务器地址
- [ ] 没有泄露个人绝对路径（`C:\Users\<name>\...`）

## 四、正确性

- [ ] 编译通过（命令与结果已记录）
- [ ] 测试通过（N/M，证据级别）
- [ ] 新增/修改的接口有文档或注释
- [ ] 行为变更已在变更记录中体现（尤其是破坏性变更）

## 五、Git（仅在 git 可用时）

- [ ] `git status` 里没有不该出现的文件
- [ ] 提交信息符合 Conventional Commits，标题说清"做了什么改变"
- [ ] 一次提交只讲一件事
- [ ] 已获得**明确授权**才执行 commit / push

---

**通过标准**：一至四节全绿；第五节按是否可用 Git 决定。