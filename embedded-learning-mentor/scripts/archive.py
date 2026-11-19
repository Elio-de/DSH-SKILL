#!/usr/bin/env python3
"""嵌入式学习知识库工具：初始化、状态、校验、一致性审计、新建日志。

只用 Python 标准库（本机 Python 3.9 可用）。知识库是纯 Markdown（Obsidian Vault），
插件只做摘要索引；本脚本不碰插件。

用法:
    python archive.py init    --root "<知识库根>" [--force]
    python archive.py status  --root "<知识库根>" [--json]
    python archive.py check   --root "<知识库根>" [--json]
    python archive.py audit   --root "<知识库根>" [--json]
    python archive.py new-log --root "<知识库根>" --topic "GPIO 点灯"

默认根（可用环境变量 EMBEDDED_LEARNING_ROOT 覆盖）:
    C:\\Users\\ouyan\\Documents\\Obsidian Vault\\Embedded_Learning

退出码: 0 = 正常 / 1 = 校验未通过 / 2 = 用法或路径错误
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

VERSION = "0.5.2"  # 随 Skill 版本走

DEFAULT_ROOT = os.environ.get(
    "EMBEDDED_LEARNING_ROOT",
    r"C:\Users\ouyan\Documents\Obsidian Vault\Embedded_Learning",
)

DIRS = [
    "00_个人档案",
    "01_学习路线",
    "02_基础知识",
    "03_嵌入式技术",
    "04_PCB设计",
    "05_项目实践",
    "06_问题与故障记录",
    "07_阶段总结",
    "08_参考资料",
    "09_学习日志",
    "99_模板",
]

# 目标文件 -> 模板文件（模板是唯一内容来源，避免脚本与 templates/ 两处维护）
SEED_FILES = {
    "00_个人档案/个人档案.md": "profile.md",
    "00_个人档案/学习状态.md": "state.md",
    "06_问题与故障记录/错误台账.md": "error-ledger.md",
}

TEMPLATE_INDEX_MD = """---
tags: [elm/参考]
updated: {today}
aliases: [模板说明]
---

# 模板说明

模板本体放在 Skill 的 `templates/`，**此处不放副本**，避免两处不同步。

| 模板 | 用途 | 产出位置 |
|---|---|---|
| `profile.md` | 个人档案 | `00_个人档案/个人档案.md` |
| `state.md` | 学习状态 | `00_个人档案/学习状态.md` |
| `learning-plan.md` | 学习计划 | `01_学习路线/` |
| `session-log.md` | 单次学习记录 | `09_学习日志/` |
| `project-record.md` | 项目档案 | `05_项目实践/<项目>/` |
| `error-ledger.md` | 错误台账 | `06_问题与故障记录/错误台账.md` |
| `error-record.md` | 单条错误详情 | `06_问题与故障记录/ERR-xxx-简述.md` |
| `stage-summary.md` | 阶段总结 | `07_阶段总结/` |
| `assessment.md` | 诊断/测试记录 | `09_学习日志/` |

维护脚本：

```powershell
python scripts/archive.py check   --root "<知识库根>"
python scripts/archive.py audit   --root "<知识库根>"
```
"""

REQUIRED = {
    "00_个人档案/个人档案.md": ["## 2 当前知识基础", "## 3 长期学习目标", "## 5 开发环境", "## 9 当前薄弱环节"],
    "00_个人档案/学习状态.md": ["## 2 领域总览", "## 3 知识单元台账", "## 9 下次开始处"],
    "06_问题与故障记录/错误台账.md": ["## 错误模式", "## 训练与复测"],
}

LOG_SECTIONS = ["## 目标", "## 证据", "## 等级 / 状态变化", "## 下次从哪继续"]
PLAN_SECTIONS = ["## 目标", "## 阶段划分"]
PROJECT_SECTIONS = ["## 1 项目背景", "## 15 下一步任务"]

LOG_NAME_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-.+\.md$")
ERR_ID_RE = re.compile(r"ERR-\d{3}")
SECRET_PATTERNS = [
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"), "疑似 GitHub token"),
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "疑似 API key"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "疑似私钥"),
    (re.compile(r"(?i)\b(password|passwd|api[_-]?key|secret|token)\b\s*[:=]\s*\S+"), "疑似口令/密钥字段"),
]
UNSAFE_NAME_RE = re.compile(r'[\\/:*?"<>|\s]+')


def _utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _write_new(path: Path, text: str, force: bool) -> bool:
    if path.exists() and not force:
        return False
    _write_text(path, text)
    return True


def _templates_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "templates"


def _template(name: str, today: str) -> str:
    path = _templates_dir() / name
    if not path.is_file():
        raise FileNotFoundError("找不到模板: %s" % path)
    text = _read(path)
    return text.replace("YYYY-MM-DD", today)


def ensure_tree(root: Path) -> None:
    for name in DIRS:
        (root / name).mkdir(parents=True, exist_ok=True)


def cmd_init(args) -> int:
    root = Path(args.root).resolve()
    today = date.today().isoformat()
    ensure_tree(root)

    if args.force and not args.confirm:
        print("[拒绝] --force 会覆盖已有文件；须同时加 --confirm（R2：先备份、说明影响）。")
        return 2

    created, skipped = [], []
    for rel, template in SEED_FILES.items():
        path = root / rel
        if _write_new(path, _template(template, today), args.force):
            created.append(rel)
        else:
            skipped.append(rel)

    index = root / "99_模板" / "模板说明.md"
    if _write_new(index, TEMPLATE_INDEX_MD.format(today=today), args.force):
        created.append("99_模板/模板说明.md")
    else:
        skipped.append("99_模板/模板说明.md")

    print("知识库根目录: %s" % root)
    for rel in created:
        print("  [新建] %s" % rel)
    for rel in skipped:
        print("  [跳过] %s（已存在；覆盖用 --force）" % rel)
    print("目录: %s" % " / ".join(DIRS))
    print("下一步: 填 00_个人档案/个人档案.md，再运行 check。")
    return 0


def _md_count(path: Path) -> int:
    return len(list(path.rglob("*.md"))) if path.is_dir() else 0


def _error_stats(root: Path):
    ledger = root / "06_问题与故障记录" / "错误台账.md"
    if not ledger.is_file():
        return 0, 0
    rows = [ln for ln in _read(ledger).splitlines() if ln.startswith("| ERR-")]
    return len(rows), len([ln for ln in rows if "closed" not in ln])


def _latest_log(root: Path):
    logs = sorted((root / "09_学习日志").glob("*.md"), key=lambda p: p.name)
    return logs[-1] if logs else None


def _collect(root: Path) -> dict:
    info = {"root": str(root), "version": VERSION, "exists": root.is_dir()}
    info["notes"] = _md_count(root / "02_基础知识") + _md_count(root / "03_嵌入式技术") \
        + _md_count(root / "04_PCB设计") + _md_count(root / "08_参考资料")
    info["plans"] = _md_count(root / "01_学习路线")
    info["logs"] = _md_count(root / "09_学习日志")
    info["summaries"] = _md_count(root / "07_阶段总结")
    info["projects"] = sorted(p.name for p in (root / "05_项目实践").iterdir() if p.is_dir()) \
        if (root / "05_项目实践").is_dir() else []
    info["errors"], info["errors_open"] = _error_stats(root)

    latest = _latest_log(root)
    info["latest_log"] = latest.name if latest else None
    if latest:
        info["days_since_log"] = (date.today() - datetime.fromtimestamp(latest.stat().st_mtime).date()).days
    else:
        info["days_since_log"] = None

    state = root / "00_个人档案" / "学习状态.md"
    next_step = None
    if state.is_file():
        text = _read(state)
        idx = text.find("## 9 下次开始处")
        if idx >= 0:
            tail = text[idx + len("## 9 下次开始处"):].strip().splitlines()
            body = [ln.strip() for ln in tail if ln.strip() and not ln.startswith(">")]
            next_step = body[0] if body else None
    info["next_step"] = next_step
    return info


def cmd_status(args) -> int:
    root = Path(args.root).resolve()
    info = _collect(root)
    if args.json:
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return 0 if info["exists"] else 2

    print("知识库: %s" % info["root"])
    if not info["exists"]:
        print("  [错误] 目录不存在；先运行 init。")
        return 2
    print("  知识笔记 %d / 计划 %d / 日志 %d / 总结 %d / 项目 %d"
          % (info["notes"], info["plans"], info["logs"], info["summaries"], len(info["projects"])))
    print("  错误模式 %d 条（未关闭 %d）" % (info["errors"], info["errors_open"]))
    if info["latest_log"]:
        print("  最近日志: %s（%s 天前）" % (info["latest_log"], info["days_since_log"]))
    else:
        print("  最近日志: 无")
    if info["next_step"]:
        print("  下次开始: %s" % info["next_step"][:120])
    if info["projects"]:
        print("  项目: %s" % "、".join(info["projects"]))
    return 0


def cmd_check(args) -> int:
    root = Path(args.root).resolve()
    errors, warnings = [], []

    if not root.is_dir():
        print("[错误] 知识库目录不存在: %s" % root)
        return 2

    for name in DIRS:
        if not (root / name).is_dir():
            errors.append("缺少目录 %s/" % name)

    for rel, sections in REQUIRED.items():
        path = root / rel
        if not path.is_file():
            errors.append("缺少核心文件 %s" % rel)
            continue
        text = _read(path)
        for section in sections:
            if section not in text:
                errors.append("%s 缺少小节 %r" % (rel, section))

    state = root / "00_个人档案" / "学习状态.md"
    if state.is_file() and re.search(r"\|\s*L0\s*\|", _read(state)):
        warnings.append("学习状态.md 出现 | L0 |：L0 只是状态标记，不是掌握等级")

    for sub, sections in (("09_学习日志", LOG_SECTIONS),):
        directory = root / sub
        if not directory.is_dir():
            continue
        for path in directory.rglob("*.md"):
            text = _read(path)
            missing = [s for s in sections if s not in text]
            if missing:
                warnings.append("%s 缺少小节: %s" % (path.relative_to(root), "、".join(missing)))
            m = LOG_NAME_RE.match(path.name)
            if not m:
                errors.append("日志命名不合规（应 YYYY-MM-DD-主题.md）: %s" % path.name)
            else:
                try:
                    d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                    if d > date.today():
                        warnings.append("日志日期在未来: %s" % path.name)
                except ValueError:
                    errors.append("日志日期非法: %s" % path.name)

    for path in (root / "01_学习路线").rglob("*.md") if (root / "01_学习路线").is_dir() else []:
        missing = [s for s in PLAN_SECTIONS if s not in _read(path)]
        if missing:
            warnings.append("%s 缺少小节: %s" % (path.relative_to(root), "、".join(missing)))

    for project in (root / "05_项目实践").iterdir() if (root / "05_项目实践").is_dir() else []:
        if not project.is_dir():
            continue
        doc = project / "项目档案.md"
        if not doc.is_file():
            errors.append("项目目录缺少 项目档案.md: %s" % project.name)
            continue
        text = _read(doc)
        missing = [s for s in PROJECT_SECTIONS if s not in text]
        if missing:
            warnings.append("%s/项目档案.md 缺少小节: %s" % (project.name, "、".join(missing)))

    for path in sorted(root.rglob("*.md")):
        text = _read(path)
        for pattern, label in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append("%s 中%s，请删除后再保存" % (path.relative_to(root), label))
                break

    if args.json:
        print(json.dumps({"root": str(root), "errors": errors, "warnings": warnings},
                         ensure_ascii=False, indent=2))
    else:
        print("校验: %s" % root)
        for w in warnings:
            print("  [警告] %s" % w)
        for e in errors:
            print("  [失败] %s" % e)
        print("-" * 60)
        print("结论: %s（错误 %d，警告 %d）"
              % ("通过" if not errors else "未通过", len(errors), len(warnings)))
    return 0 if not errors else 1


def cmd_audit(args) -> int:
    """跨文件一致性：项目/错误/过期/空目录/重复标题。只报告，不改文件。"""
    root = Path(args.root).resolve()
    problems, notes = [], []
    if not root.is_dir():
        print("[错误] 知识库目录不存在: %s" % root)
        return 2

    today = date.today()

    # 1 项目目录与档案
    base = root / "05_项目实践"
    projects = [p for p in base.iterdir() if p.is_dir()] if base.is_dir() else []
    for project in projects:
        if not (project / "项目档案.md").is_file():
            problems.append("项目缺档案: %s" % project.name)
    if not projects:
        notes.append("05_项目实践 为空（还没有项目）")

    # 2 错误台账 <-> 详情文件
    ledger = root / "06_问题与故障记录" / "错误台账.md"
    ledger_ids = set()
    if ledger.is_file():
        ledger_ids = set(ERR_ID_RE.findall(_read(ledger)))
    detail = root / "06_问题与故障记录"
    detail_ids = set()
    if detail.is_dir():
        for path in detail.glob("ERR-*.md"):
            m = ERR_ID_RE.match(path.name)
            if m:
                detail_ids.add(m.group(0))
            else:
                problems.append("错误详情命名不合规（应 ERR-xxx-简述.md）: %s" % path.name)
    for eid in sorted(detail_ids - ledger_ids):
        problems.append("详情存在但台账没有: %s" % eid)
    for eid in sorted(ledger_ids - detail_ids):
        notes.append("台账有 %s 但无详情文件（可接受，详情按需建）" % eid)

    # 3 过期：核心文件与项目档案 >30 天未改
    watch = [root / "00_个人档案" / "个人档案.md", root / "00_个人档案" / "学习状态.md"]
    watch += [p / "项目档案.md" for p in projects]
    for path in watch:
        if not path.is_file():
            continue
        days = (today - datetime.fromtimestamp(path.stat().st_mtime).date()).days
        if days > 30:
            problems.append("%s 已 %d 天未更新" % (path.relative_to(root), days))

    # 4 预留目录（只提示，不要求填满）
    empty = [name for name in DIRS if (root / name).is_dir() and not any((root / name).iterdir())]
    if empty:
        notes.append("预留目录（暂无内容，按需填充）: %s" % "、".join(empty))

    # 5 重复一级标题
    titles = {}
    for path in root.rglob("*.md"):
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        for line in _read(path).splitlines():
            if line.startswith("# "):
                titles.setdefault(line[2:].strip(), []).append(str(path.relative_to(root)))
                break
    for title, files in titles.items():
        if len(files) > 1:
            problems.append("重复标题 %r: %s" % (title, "、".join(files)))

    payload = {"root": str(root), "problems": problems, "notes": notes}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("一致性审计: %s" % root)
        for n in notes:
            print("  [提示] %s" % n)
        for p in problems:
            print("  [问题] %s" % p)
        print("-" * 60)
        print("结论: %s（问题 %d，提示 %d）"
              % ("一致" if not problems else "需处理", len(problems), len(notes)))
    return 0 if not problems else 1


def cmd_new_log(args) -> int:
    root = Path(args.root).resolve()
    logs = root / "09_学习日志"
    if not logs.is_dir():
        print("[错误] 找不到 09_学习日志/；先运行 init。")
        return 2
    today = date.today().isoformat()
    topic = UNSAFE_NAME_RE.sub("-", args.topic.strip()).strip("-") or "未命名"
    path = logs / ("%s-%s.md" % (today, topic))
    if path.exists():
        print("[跳过] 已存在: %s" % path)
        return 0
    text = _template("session-log.md", today).replace("<主题>", args.topic.strip())
    _write_text(path, text)
    print("[新建] %s" % path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="archive.py", description="嵌入式学习知识库工具（只依赖标准库）")
    parser.add_argument("--version", action="version", version="archive.py " + VERSION)
    sub = parser.add_subparsers(dest="command")

    p_init = sub.add_parser("init", help="创建目录骨架与核心文件")
    p_init.add_argument("--root", default=DEFAULT_ROOT)
    p_init.add_argument("--force", action="store_true", help="覆盖已存在的核心文件（需同时 --confirm）")
    p_init.add_argument("--confirm", action="store_true", help="确认覆盖已有文件")
    p_init.set_defaults(func=cmd_init)

    p_status = sub.add_parser("status", help="查看知识库概况")
    p_status.add_argument("--root", default=DEFAULT_ROOT)
    p_status.add_argument("--json", action="store_true")
    p_status.set_defaults(func=cmd_status)

    p_check = sub.add_parser("check", help="结构校验 + 密钥扫描")
    p_check.add_argument("--root", default=DEFAULT_ROOT)
    p_check.add_argument("--json", action="store_true")
    p_check.set_defaults(func=cmd_check)

    p_audit = sub.add_parser("audit", help="跨文件一致性审计")
    p_audit.add_argument("--root", default=DEFAULT_ROOT)
    p_audit.add_argument("--json", action="store_true")
    p_audit.set_defaults(func=cmd_audit)

    p_log = sub.add_parser("new-log", help="新建一条学习日志")
    p_log.add_argument("--root", default=DEFAULT_ROOT)
    p_log.add_argument("--topic", required=True)
    p_log.set_defaults(func=cmd_new_log)

    return parser


def main(argv=None) -> int:
    _utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())