#!/usr/bin/env python3
"""complexity.py — 粗略圈复杂度与函数长度扫描（只读）。

为什么需要它:
  本机没有 cppcheck / clang-tidy / LSP，无法直接拿到度量。
  这个脚本用轻量词法扫描给出“哪里最该读”的排序，不等于专业工具结论，
  但在大项目里能显著降低“从哪下手”的成本。

支持: C / C++ / Python。其它后缀跳过。
口径: 复杂度 = 1 + 决策点(if/elif/for/while/case/catch/&&/||/?:/and/or/except) 出现次数。
      这是 McCabe 的近似值，用于排序，不用于给出精确数字。

用法:
    python complexity.py --root .                 # 最复杂的 15 个函数
    python complexity.py --root . --top 30 --json
    python complexity.py --file src/uart.c        # 单文件
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

C_EXTS = {".c", ".h", ".cc", ".cpp", ".cxx", ".hpp", ".hh", ".hxx"}
PY_EXTS = {".py"}
SKIP_DIRS = {
    ".git", ".ea", ".venv", "venv", "node_modules", "build", "dist", "out",
    "__pycache__", ".pytest_cache", ".idea", ".vs", "CMakeFiles", "target",
}
MAX_FILE_BYTES = 1024 * 1024

C_DECISION_RE = re.compile(r"\b(if|else\s+if|elif|for|while|case|catch|switch)\b|&&|\|\||\?")
PY_DECISION_RE = re.compile(r"\b(if|elif|for|while|except|and|or)\b")


def _reconfigure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass


def strip_c_noise(text: str) -> str:
    """去掉注释与字符串，保留换行（保持行号一致）。"""
    out = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
        elif ch == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                if text[i] == "\n":
                    out.append("\n")
                i += 1
            i += 2
        elif ch in ("'", '"'):
            quote = ch
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == quote:
                    i += 1
                    break
                if text[i] == "\n":
                    out.append("\n")
                i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def scan_c(text: str, path: str):
    clean = strip_c_noise(text)
    results = []
    depth = 0
    block_start = None
    header_start = 0
    header = ""

    for index, ch in enumerate(clean):
        if ch == "{":
            if depth == 0:
                block_start = index
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and block_start is not None:
                    body = clean[block_start + 1:index]
                    name = guess_c_name(header)
                    if name:
                        start_line = clean.count("\n", 0, header_start) + 1
                        end_line = clean.count("\n", 0, index) + 1
                        decisions = len(C_DECISION_RE.findall(body))
                        results.append({
                            "file": path,
                            "function": name,
                            "startLine": start_line,
                            "lines": max(1, end_line - start_line + 1),
                            "complexity": 1 + decisions,
                        })
                    block_start = None
                    header = ""
                    header_start = index + 1
            if depth == 0:
                header_start = index + 1
        elif depth == 0:
            header += ch
    return results


def guess_c_name(header: str) -> str:
    text = header.strip()
    if not text or "(" not in text:
        return ""
    if re.match(r"^(struct|union|enum|typedef|namespace|class)\b", text):
        return ""
    if "=" in text.split("(")[0]:
        return ""
    match = re.search(r"([A-Za-z_]\w*)\s*\([^()]*\)\s*$", text, re.S)
    if not match:
        return ""
    name = match.group(1)
    if name in ("if", "for", "while", "switch", "return", "sizeof"):
        return ""
    return name


def scan_py(text: str, path: str):
    lines = text.splitlines()
    results = []
    index = 0
    total = len(lines)
    while index < total:
        line = lines[index]
        match = re.match(r"^(\s*)(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(", line)
        if not match:
            index += 1
            continue
        indent = len(match.group(1).expandtabs(4))
        name = match.group(2)
        start = index
        end = index
        cursor = index + 1
        while cursor < total:
            raw = lines[cursor]
            if raw.strip():
                current = len(raw.expandtabs(4)) - len(raw.expandtabs(4).lstrip())
                if current <= indent:
                    break
                end = cursor
            cursor += 1
        body = "\n".join(lines[start:end + 1])
        decisions = len(PY_DECISION_RE.findall(body))
        results.append({
            "file": path,
            "function": name,
            "startLine": start + 1,
            "lines": end - start + 1,
            "complexity": 1 + decisions,
        })
        index = max(index + 1, end + 1)
    return results


def iter_source_files(root: str, single: str):
    if single:
        yield os.path.abspath(single)
        return
    for current, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            ext = os.path.splitext(name)[1].lower()
            if ext in C_EXTS or ext in PY_EXTS:
                yield os.path.join(current, name)


def analyse(root: str, single: str):
    findings = []
    errors = []
    skipped = 0
    for full in iter_source_files(root, single):
        try:
            if os.path.getsize(full) > MAX_FILE_BYTES:
                skipped += 1
                continue
            with open(full, "r", encoding="utf-8", errors="replace") as handle:
                text = handle.read()
        except OSError as error:
            errors.append("%s: %s" % (full, error))
            continue
        ext = os.path.splitext(full)[1].lower()
        rel = (os.path.relpath(full, root) if not single else os.path.basename(full)).replace("\\", "/")
        try:
            if ext in C_EXTS:
                findings.extend(scan_c(text, rel))
            elif ext in PY_EXTS:
                findings.extend(scan_py(text, rel))
        except Exception as error:  # 解析失败不应中断整次扫描
            errors.append("%s: %s" % (rel, error))
    return findings, errors, skipped


def render_human(findings, errors, skipped, top):
    ranked = sorted(findings, key=lambda item: (-item["complexity"], -item["lines"]))[:top]
    lines = ["=" * 76, "复杂度扫描（近似值，用于排序而非定论）", "=" * 76]
    lines.append("函数总数 %d  跳过(>1MB) %d  解析失败 %d" % (len(findings), skipped, len(errors)))
    lines.append("")
    lines.append("%-30s %-24s %-7s %-7s %s" % ("文件", "函数", "起始行", "行数", "复杂度"))
    lines.append("-" * 76)
    for item in ranked:
        lines.append("%-30s %-24s %-7d %-7d %d" % (
            item["file"][:30], item["function"][:24], item["startLine"],
            item["lines"], item["complexity"]))

    if ranked:
        worst = ranked[0]
        lines.append("")
        lines.append("建议优先阅读: %s:%d  %s()（复杂度 %d，%d 行）" % (
            worst["file"], worst["startLine"], worst["function"],
            worst["complexity"], worst["lines"]))
        heavy = [f for f in findings if f["complexity"] >= 15 or f["lines"] >= 120]
        if heavy:
            lines.append("高复杂/超长函数 %d 个（复杂度≥15 或行数≥120），建议拆分或重点审查" % len(heavy))
    if errors:
        lines.append("")
        lines.append("解析失败（需人工确认）:")
        for item in errors[:10]:
            lines.append("  - " + item)
    lines.append("")
    lines.append("注意: 该数值是词法近似，循环展开/宏/函数指针会低估复杂度；结论需人工复核。")
    return "\n".join(lines)


def main(argv=None) -> int:
    _reconfigure_stdout()
    parser = argparse.ArgumentParser(description="粗略圈复杂度与函数长度扫描（只读）")
    parser.add_argument("--root", default=".", help="项目根目录")
    parser.add_argument("--file", default="", help="只分析单个文件")
    parser.add_argument("--top", type=int, default=15)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = os.path.abspath(args.root)
    if not args.file and not os.path.isdir(root):
        sys.stderr.write("不是目录: %s\n" % root)
        return 2

    findings, errors, skipped = analyse(root, args.file)
    if args.json:
        payload = {
            "root": root.replace("\\", "/"),
            "functionCount": len(findings),
            "skipped": skipped,
            "errors": errors,
            "ranking": sorted(findings, key=lambda i: (-i["complexity"], -i["lines"]))[:args.top],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_human(findings, errors, skipped, args.top))
    return 0


if __name__ == "__main__":
    sys.exit(main())