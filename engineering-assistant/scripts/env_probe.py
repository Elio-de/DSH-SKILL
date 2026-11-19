#!/usr/bin/env python3
"""env_probe.py — 探测本机真实可用的工程工具链（只读，不安装任何东西）。

用法:
    python env_probe.py              # 人类可读表格
    python env_probe.py --json       # 机器可读 JSON（供 Skill 判定降级路径）
    python env_probe.py --tools git,gcc,openocd

为什么要这个脚本:
  PATH 里可能存在“指向已删除目录”的失效项（本机实测有 5 条），
  直接用 Get-Command / where 会误判“已安装”。本脚本对每个候选:
    1) 校验路径真实存在
    2) 试运行 --version 并抓首行
    3) 记录可解析的版本号
  只有三步都过才算 available。

退出码: 0 = 探测完成（不论是否缺工具）；2 = 参数错误。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys

TIMEOUT_SECONDS = 20

# name -> (version_args, extra_candidate_paths, capability_kind)
TOOL_SPECS = {
    "git": (["--version"], [
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files\Git\bin\git.exe",
        r"C:\Program Files (x86)\Git\cmd\git.exe",
    ], "vcs"),
    "gcc": (["--version"], [], "host-cc"),
    "g++": (["--version"], [], "host-cxx"),
    "gdb": (["--version"], [], "debugger"),
    "make": (["--version"], [], "build"),
    "mingw32-make": (["--version"], [], "build"),
    "cmake": (["--version"], [], "build"),
    "ninja": (["--version"], [], "build"),
    "arm-none-eabi-gcc": (["--version"], [], "target-cc"),
    "arm-none-eabi-gdb": (["--version"], [], "target-debugger"),
    "openocd": (["--version"], [
        r"C:\openocd\bin\openocd.exe",
        r"C:\Program Files\OpenOCD\bin\openocd.exe",
    ], "flasher"),
    "STM32_Programmer_CLI": (["--version"], [], "flasher"),
    "cppcheck": (["--version"], [
        r"C:\Program Files\Cppcheck\cppcheck.exe",
        r"C:\Program Files (x86)\Cppcheck\cppcheck.exe",
        r"C:\Program Files\Cppcheck\cppcheck-core.exe",
    ], "static-analysis"),
    "clang": (["--version"], [], "compiler"),
    "clang-tidy": (["--version"], [], "static-analysis"),
    "python": (["--version"], [], "scripting"),
    "node": (["--version"], [], "scripting"),
    "pytest": (["--version"], [], "test"),
}

VERSION_RE = re.compile(r"(\d+\.\d+(?:\.\d+)?(?:[-+][0-9A-Za-z.\-]+)?)")


def _reconfigure_stdout() -> None:
    """Windows 控制台常为 GBK，避免打印中文时抛 UnicodeEncodeError。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass


def _run(args, timeout=TIMEOUT_SECONDS):
    """返回 (exit_code, stdout+stderr)，失败时 exit_code 为 None。"""
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except (OSError, subprocess.SubprocessError):
        return None, ""


def _extract_version(output: str) -> str:
    match = VERSION_RE.search(output or "")
    return match.group(1) if match else ""


def resolve_tool(name: str, candidates, version_args):
    """校验存在性 + 可执行性。返回记录 dict。"""
    record = {
        "name": name,
        "available": False,
        "path": "",
        "version": "",
        "note": "",
    }

    hits = []
    on_path = shutil.which(name)
    if on_path:
        hits.append(on_path)
    for candidate in candidates:
        if os.path.isfile(candidate):
            hits.append(candidate)

    # 去重并保持顺序
    seen = set()
    unique_hits = []
    for hit in hits:
        key = os.path.normcase(os.path.abspath(hit))
        if key not in seen:
            seen.add(key)
            unique_hits.append(hit)

    if not unique_hits:
        record["note"] = "未找到可执行文件"
        return record

    failures = []
    for hit in unique_hits:
        code, output = _run([hit] + list(version_args))
        if code is None:
            failures.append(f"{hit}: 无法启动")
            continue
        record["available"] = True
        record["path"] = hit
        record["version"] = _extract_version(output)
        first_line = ""
        for line in (output or "").splitlines():
            if line.strip():
                first_line = line.strip()
                break
        record["note"] = first_line[:120]
        return record

    record["path"] = unique_hits[0]
    record["note"] = "; ".join(failures) or "已找到但无法执行"
    return record


def probe_fanalyzer(gcc_path: str) -> dict:
    """检查编译器是否支持 -fanalyzer（GCC 10+ 才有）。"""
    result = {"supported": False, "detail": ""}
    if not gcc_path:
        result["detail"] = "编译器不可用"
        return result
    code, output = _run([gcc_path, "-Q", "--help=common"])
    if code is None:
        result["detail"] = "无法查询编译选项"
        return result
    if "fanalyzer" in output:
        result["supported"] = True
        result["detail"] = "支持 -fanalyzer（可做过程间静态分析）"
    else:
        result["detail"] = "不支持 -fanalyzer（GCC < 10）"
    return result


def probe_git_state(git_path: str = "") -> dict:
    """git 是否可用，以及当前目录是否在仓库内。

    优先使用 resolve_tool() 已经探测到的绝对路径（Git 不在 PATH 时也能工作）；
    只有未传入路径时才回退到 shutil.which()。
    """
    state = {"binary": False, "repo": False, "root": ""}
    git = git_path if git_path and os.path.isfile(git_path) else shutil.which("git")
    if not git:
        return state
    state["binary"] = True
    code, output = _run([git, "rev-parse", "--show-toplevel"], timeout=10)
    if code == 0 and output.strip():
        state["repo"] = True
        state["root"] = output.strip().splitlines()[-1]
    return state


def collect(selected=None) -> dict:
    tools = {}
    for name, (version_args, candidates, kind) in TOOL_SPECS.items():
        if selected and name not in selected:
            continue
        record = resolve_tool(name, candidates, version_args)
        record["kind"] = kind
        tools[name] = record

    capabilities = {
        "git": probe_git_state(tools.get("git", {}).get("path", "")),
        "fanalyzer_host": probe_fanalyzer(tools.get("gcc", {}).get("path", "")),
        "fanalyzer_target": probe_fanalyzer(tools.get("arm-none-eabi-gcc", {}).get("path", "")),
        "cwd": os.getcwd(),
    }

    available = sorted(n for n, t in tools.items() if t["available"])
    missing = sorted(n for n, t in tools.items() if not t["available"])

    return {
        "schemaVersion": 1,
        "cwd": os.getcwd(),
        "available": available,
        "missing": missing,
        "tools": tools,
        "capabilities": capabilities,
        "verdict": build_verdict(tools, capabilities),
    }


def build_verdict(tools: dict, capabilities: dict) -> dict:
    """把工具事实翻译成“哪些工作流可以走，哪些必须降级”。"""
    def ok(name):
        return bool(tools.get(name, {}).get("available"))

    has_host_cc = ok("gcc") or ok("clang")
    has_target_cc = ok("arm-none-eabi-gcc")
    has_git = capabilities["git"]["binary"] or ok("git")
    has_repo = capabilities["git"]["repo"]

    return {
        "compile_host": has_host_cc,
        "compile_target": has_target_cc,
        "static_analysis": bool(
            ok("cppcheck") or ok("clang-tidy")
            or capabilities["fanalyzer_target"]["supported"]
            or capabilities["fanalyzer_host"]["supported"]
        ),
        "static_analysis_detail": (
            "cppcheck/clang-tidy" if (ok("cppcheck") or ok("clang-tidy"))
            else ("仅 -fanalyzer（target）" if capabilities["fanalyzer_target"]["supported"]
                  else ("仅 -fanalyzer（host）" if capabilities["fanalyzer_host"]["supported"]
                        else "无独立静态分析器，只能依赖编译器警告"))
        ),
        "git_usable": has_git,
        "git_repo": has_repo,
        "git_degrade_reason": "" if has_git else "未找到 git：无法 status/diff/log/分支/回滚，必须降级并明确告知",
        "debug_online": ok("openocd") or ok("STM32_Programmer_CLI"),
        "test_runner": ok("pytest") or has_host_cc,
        "realtime_trace": False,
        "hardware_verification": "AI 不可执行，必须由用户完成",
    }


def render_human(data: dict) -> str:
    lines = []
    lines.append("=" * 78)
    lines.append("工程环境探测（只读）  cwd = %s" % data["cwd"])
    lines.append("=" * 78)

    width = max(len(t["name"]) for t in data["tools"].values()) + 2
    lines.append("%-*s %-12s %-38s %s" % (width, "工具", "状态", "版本/说明", "路径"))
    lines.append("-" * 78)
    for name in sorted(data["tools"]):
        item = data["tools"][name]
        status = "OK" if item["available"] else "缺失"
        version = item["version"] or item["note"]
        lines.append("%-*s %-12s %-38s %s" % (
            width, name, status, version[:38], item["path"] or "-"))

    caps = data["capabilities"]
    verdict = data["verdict"]
    lines.append("")
    lines.append("-" * 78)
    lines.append("能力判定")
    lines.append("-" * 78)
    rows = [
        ("主机编译", verdict["compile_host"]),
        ("目标板交叉编译", verdict["compile_target"]),
        ("静态分析", verdict["static_analysis"]),
        ("Git 可用", verdict["git_usable"]),
        ("当前在 Git 仓库内", caps["git"]["repo"]),
        ("在线调试/烧录", verdict["debug_online"]),
    ]
    for label, value in rows:
        lines.append("  %-18s %s" % (label, "是" if value else "否"))

    lines.append("  %-18s %s" % ("静态分析手段", verdict["static_analysis_detail"]))
    if caps["git"]["root"]:
        lines.append("  %-18s %s" % ("仓库根", caps["git"]["root"]))
    if verdict["git_degrade_reason"]:
        lines.append("")
        lines.append("  [降级] " + verdict["git_degrade_reason"])
    lines.append("  %-18s %s" % ("硬件验证", verdict["hardware_verification"]))
    lines.append("")
    lines.append("缺失工具: " + (", ".join(data["missing"]) or "无"))
    return "\n".join(lines)


def main(argv=None) -> int:
    _reconfigure_stdout()
    parser = argparse.ArgumentParser(
        description="探测本机工程工具链（只读）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例: python env_probe.py --json --tools git,gcc,arm-none-eabi-gcc",
    )
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--tools", default="", help="只探测指定工具，逗号分隔")
    parser.add_argument("--out", default="", help="把 JSON 同时写入指定文件")
    args = parser.parse_args(argv)

    selected = [t.strip() for t in args.tools.split(",") if t.strip()] or None
    unknown = [t for t in (selected or []) if t not in TOOL_SPECS]
    if unknown:
        sys.stderr.write("未知工具: %s\n可用: %s\n" % (
            ", ".join(unknown), ", ".join(sorted(TOOL_SPECS))))
        return 2

    data = collect(selected)

    if args.json:
        text = json.dumps(data, ensure_ascii=False, indent=2)
        print(text)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as handle:
                handle.write(text + "\n")
    else:
        print(render_human(data))
        if args.out:
            with open(args.out, "w", encoding="utf-8") as handle:
                handle.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())