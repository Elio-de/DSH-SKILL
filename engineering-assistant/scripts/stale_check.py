#!/usr/bin/env python3
"""stale_check.py — 判定 .ea/ 知识是否过期、是否超限、是否还有孤儿条目。

核心思路:
  state.json 记录“上次扫描时”每个文件的 sha256 与每个模块的聚合哈希。
  本脚本重新核对磁盘现状:
    1) 只对 size/mtime 变化的文件重算哈希（增量，不重扫全项目）
    2) 重算模块聚合哈希，与 state 中的记录比对
    3) 若某条知识声明的覆盖模块发生变化 → 该知识标记为过期
  代码是唯一事实源: 本脚本只报告，不修改任何源码或知识内容。

用法:
    python stale_check.py                      # 人类可读报告
    python stale_check.py --json               # 机器可读
    python stale_check.py --strict             # 存在过期项时退出码 1
    python stale_check.py --mark-verified MODULES.md --modules uart,main
    python stale_check.py --root D:\\proj

基线时间:
    state.updatedAt 视为“上次扫描时间”。超过 --max-age-days（默认 30）提示复查。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import sys

DEFAULT_MAX_AGE_DAYS = 30
KNOWLEDGE_LINE_CAP = 400
ARCHIVE_DIR = "archive"


def _reconfigure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass


def now_iso() -> str:
    return _dt.datetime.now().astimezone().replace(microsecond=0).isoformat()


def parse_iso(text: str):
    if not text:
        return None
    try:
        return _dt.datetime.fromisoformat(text)
    except ValueError:
        return None


def sha256_of(path: str) -> str:
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return ""


def current_hash(path: str, recorded: dict) -> str:
    """size/mtime 未变则沿用记录值，否则重算。"""
    try:
        stat = os.stat(path)
    except OSError:
        return ""
    mtime = _dt.datetime.fromtimestamp(stat.st_mtime).astimezone().replace(
        microsecond=0).isoformat()
    if recorded and recorded.get("size") == stat.st_size and recorded.get("mtime") == mtime:
        return recorded.get("sha256", "")
    return sha256_of(path)


def aggregate(module_files, hashes):
    parts = []
    for rel in sorted(module_files):
        digest = hashes.get(rel, "")
        if digest:
            parts.append("%s:%s" % (rel, digest))
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest() if parts else ""


def count_lines(path: str) -> int:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return sum(1 for _ in handle)
    except OSError:
        return 0


def load_json(path: str):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


def check(root: str, max_age_days: int) -> dict:
    ea = os.path.join(root, ".ea")
    state_path = os.path.join(ea, "state.json")
    report = {
        "root": root.replace("\\", "/"),
        "checkedAt": now_iso(),
        "initialized": os.path.isfile(state_path),
        "stale": [],
        "changedModules": [],
        "missingFiles": [],
        "oversize": [],
        "overdue": False,
        "ageDays": None,
        "unregisteredKnowledge": True,
        "counts": {},
    }

    if not report["initialized"]:
        report["message"] = "未建立知识库（.ea/state.json 不存在），请先运行 project_scan.py --init --update-state"
        return report

    state = load_json(state_path) or {}
    recorded_files = state.get("files", {}) or {}
    recorded_modules = state.get("modules", {}) or {}
    knowledge = state.get("knowledge", {}) or {}

    current = {}
    for rel, entry in recorded_files.items():
        full = os.path.join(root, rel.replace("/", os.sep))
        if not os.path.isfile(full):
            report["missingFiles"].append(rel)
            continue
        digest = current_hash(full, entry)
        if digest:
            current[rel] = digest

    for name, info in recorded_modules.items():
        files = info.get("files", [])
        new_hash = aggregate(files, current)
        if info.get("hash") and new_hash and new_hash != info.get("hash"):
            report["changedModules"].append(name)

    changed_set = set(report["changedModules"])

    for knowledge_name, info in knowledge.items():
        covers = info.get("covers", [])
        based = info.get("basedOnHash", {}) or {}
        hits = []
        for module in covers:
            if module in changed_set:
                hits.append(module)
            elif module in recorded_modules and based.get(module):
                current_module_hash = aggregate(recorded_modules[module].get("files", []), current)
                if current_module_hash and current_module_hash != based.get(module):
                    hits.append(module)
        if hits:
            report["stale"].append({
                "knowledge": knowledge_name,
                "covers": covers,
                "changed": sorted(set(hits)),
                "verifiedAt": info.get("verifiedAt", ""),
            })

    report["unregisteredKnowledge"] = not bool(knowledge)

    # 知识文件行数上限
    if os.path.isdir(ea):
        for name in sorted(os.listdir(ea)):
            if not name.endswith(".md"):
                continue
            lines = count_lines(os.path.join(ea, name))
            if lines > KNOWLEDGE_LINE_CAP:
                report["oversize"].append({"file": name, "lines": lines, "cap": KNOWLEDGE_LINE_CAP})

    updated = parse_iso(state.get("updatedAt", ""))
    if updated:
        age = (_dt.datetime.now().astimezone() - updated).days
        report["ageDays"] = age
        report["overdue"] = age > max_age_days

    issues_path = os.path.join(ea, "ISSUES.md")
    if os.path.isfile(issues_path):
        text = ""
        try:
            with open(issues_path, "r", encoding="utf-8", errors="replace") as handle:
                text = handle.read()
        except OSError:
            pass
        report["counts"]["issues_open"] = text.count("状态：open")
        report["counts"]["issues_fixed"] = text.count("状态：fixed")

    report["counts"]["filesTracked"] = len(recorded_files)
    report["counts"]["modules"] = len(recorded_modules)
    report["counts"]["knowledgeEntries"] = len(knowledge)
    report["hasProblem"] = bool(
        report["stale"] or report["missingFiles"] or report["oversize"] or report["overdue"])
    return report


def mark_verified(root: str, knowledge_name: str, modules) -> dict:
    state_path = os.path.join(root, ".ea", "state.json")
    state = load_json(state_path)
    if not state:
        return {"ok": False, "message": "state.json 不存在，请先运行 project_scan.py --init --update-state"}

    recorded_modules = state.get("modules", {}) or {}
    recorded_files = state.get("files", {}) or {}
    current = {}
    for rel, entry in recorded_files.items():
        full = os.path.join(root, rel.replace("/", os.sep))
        if os.path.isfile(full):
            digest = current_hash(full, entry)
            if digest:
                current[rel] = digest

    based = {}
    unknown = []
    for module in modules:
        info = recorded_modules.get(module)
        if not info:
            unknown.append(module)
            continue
        based[module] = aggregate(info.get("files", []), current)

    knowledge = state.setdefault("knowledge", {})
    knowledge[knowledge_name] = {
        "covers": [m for m in modules if m not in unknown],
        "verifiedAt": now_iso(),
        "basedOnHash": based,
    }
    state["updatedAt"] = state.get("updatedAt") or now_iso()
    with open(state_path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, ensure_ascii=False, indent=2)
    return {"ok": True, "unknown": unknown, "recorded": sorted(based)}


def render_human(report: dict) -> str:
    lines = ["=" * 74, "知识库时效检查  " + report["root"], "=" * 74]
    if not report["initialized"]:
        lines.append(report.get("message", "未建库"))
        return "\n".join(lines)

    counts = report["counts"]
    lines.append("跟踪文件 %d  模块 %d  知识条目 %d  上次扫描 %s 天前" % (
        counts.get("filesTracked", 0), counts.get("modules", 0),
        counts.get("knowledgeEntries", 0), report["ageDays"] if report["ageDays"] is not None else "?"))

    lines.append("")
    if report["changedModules"]:
        lines.append("[代码已变] 以下模块的文件哈希与记录不一致:")
        for name in report["changedModules"]:
            lines.append("  - " + name)
    else:
        lines.append("[代码未变] 所有已跟踪模块的哈希与记录一致")

    if report["stale"]:
        lines.append("")
        lines.append("[知识过期] 需重新核对代码:")
        for item in report["stale"]:
            lines.append("  - %s（覆盖 %s；变化 %s；上次核实 %s）" % (
                item["knowledge"], ",".join(item["covers"]),
                ",".join(item["changed"]), item["verifiedAt"] or "未知"))
    elif report["unregisteredKnowledge"]:
        lines.append("")
        lines.append("[未登记] 尚无知识覆盖范围记录（用 --mark-verified 登记后可精确判定过期）")
    else:
        lines.append("")
        lines.append("[知识有效] 所有登记知识的覆盖模块均未变化")

    if report["missingFiles"]:
        lines.append("")
        lines.append("[文件消失] 已跟踪但磁盘上不存在（可能被删/改名）:")
        for rel in report["missingFiles"][:20]:
            lines.append("  - " + rel)

    if report["oversize"]:
        lines.append("")
        lines.append("[超限] 建议归档或精简:")
        for item in report["oversize"]:
            lines.append("  - %s（%d 行 > %d 行上限）" % (item["file"], item["lines"], item["cap"]))

    if report["overdue"]:
        lines.append("")
        lines.append("[超期] 距上次扫描 %d 天 > 30 天，建议重扫" % report["ageDays"])

    lines.append("")
    lines.append("结论: " + ("存在问题，回答涉及这些知识时必须先核对代码" if report["hasProblem"]
                              else "无过期迹象"))
    return "\n".join(lines)


def main(argv=None) -> int:
    _reconfigure_stdout()
    parser = argparse.ArgumentParser(description="检查 .ea/ 知识时效（只读，除非 --mark-verified）")
    parser.add_argument("--root", default=".", help="项目根目录")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true", help="存在问题时退出码 1")
    parser.add_argument("--max-age-days", type=int, default=DEFAULT_MAX_AGE_DAYS)
    parser.add_argument("--mark-verified", default="", help="登记某知识文件已核对，如 MODULES.md")
    parser.add_argument("--modules", default="", help="配合 --mark-verified：覆盖的模块名，逗号分隔")
    args = parser.parse_args(argv)

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        sys.stderr.write("不是目录: %s\n" % root)
        return 2

    if args.mark_verified:
        modules = [m.strip() for m in args.modules.split(",") if m.strip()]
        if not modules:
            sys.stderr.write("--mark-verified 需要同时给出 --modules\n")
            return 2
        result = mark_verified(root, args.mark_verified, modules)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok") else 1

    report = check(root, args.max_age_days)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_human(report))

    if args.strict and report.get("hasProblem"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())