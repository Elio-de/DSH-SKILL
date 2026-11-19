#!/usr/bin/env python3
"""project_scan.py — 项目结构与指纹扫描（只读，除非显式 --init / --update-state）。

用途:
  1) 冷启动时快速建立项目地图所需的事实（目录、构建系统、入口、模块）
  2) 计算文件 sha256，供 .ea/state.json 做“知识是否过期”的判定
  3) 增量：只重算 size/mtime 变化的文件，其余沿用旧哈希

用法:
    python project_scan.py                          # 只看摘要
    python project_scan.py --json                   # 机器可读
    python project_scan.py --init                   # 创建 .ea/ 骨架（若不存在）
    python project_scan.py --update-state           # 写入/更新 .ea/state.json
    python project_scan.py --root D:\\proj --max-files 3000

安全:
  * 默认不写任何文件；--init / --update-state 才写，且只写 .ea/ 下。
  * 不跟随符号链接，避免环。
  * 不读取 >2MB 的文件内容（只记大小），防止卡死。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import sys

SKIP_DIRS = {
    ".git", ".hg", ".svn", ".ea", ".dsh", ".agents", ".venv", "venv", "env",
    "node_modules", "bower_components", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "build", "dist", "out", "output", "Debug",
    "Release", "target", "obj", "bin", ".idea", ".vs", ".settings", "CMakeFiles",
    ".cache", "coverage", "htmlcov", ".tox", "site-packages", "Pods",
}

SOURCE_EXTS = {
    ".c", ".h", ".cc", ".cpp", ".cxx", ".hpp", ".hh", ".hxx", ".ino",
    ".s", ".S", ".asm", ".ld", ".py", ".js", ".ts", ".java", ".cs",
    ".go", ".rs", ".vb", ".m",
}

# 构建/覆盖率副产物：不参与模块哈希，否则会制造假"过期"
ARTIFACT_EXTS = {
    ".o", ".obj", ".a", ".lib", ".exe", ".dll", ".so", ".dylib",
    ".elf", ".hex", ".bin", ".map", ".lst", ".su", ".d",
    ".gcno", ".gcda", ".gcov", ".pyc", ".pyo", ".pdb", ".ilk", ".exp",
}

CONFIG_NAMES = {
    "CMakeLists.txt", "Makefile", "makefile", "GNUmakefile",
    "platformio.ini", "pyproject.toml", "setup.py", "requirements.txt",
    "package.json", "tsconfig.json", "Cargo.toml", "go.mod",
    ".clang-format", ".clang-tidy", ".editorconfig", ".gitignore",
    "Kconfig", "meson.build", "SConstruct", "wscript",
}

BUILD_HINT_EXT = {
    ".ioc": "STM32CubeMX",
    ".uvprojx": "Keil MDK",
    ".uvproj": "Keil MDK",
    ".ewp": "IAR EWARM",
    ".cproject": "Eclipse CDT",
    ".mcp": "MPLAB X",
}

ENTRY_NAMES = {
    "main.c", "main.cpp", "main.cc", "main.py", "__main__.py",
    "app.py", "index.js", "main.go", "Program.cs", "main.rs",
}

MAX_HASH_BYTES = 2 * 1024 * 1024


def _reconfigure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass


def now_iso() -> str:
    return _dt.datetime.now().astimezone().replace(microsecond=0).isoformat()


def rel_posix(path: str, root: str) -> str:
    return os.path.relpath(path, root).replace("\\", "/")


def sha256_of(path: str) -> str:
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return ""


def walk_files(root: str, max_files: int):
    """返回 (files, skipped_dirs, truncated)。files 为绝对路径列表。"""
    files = []
    skipped = []
    truncated = False
    for current, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            full = os.path.join(current, name)
            if os.path.splitext(name)[1].lower() in ARTIFACT_EXTS:
                continue
            try:
                if os.path.islink(full) or not os.path.isfile(full):
                    continue
            except OSError:
                continue
            files.append(full)
            if len(files) >= max_files:
                truncated = True
                remaining = [d for d in dirnames]
                skipped.extend(remaining)
                return files, skipped, truncated
    return files, skipped, truncated


def detect_build(files, root):
    hints = []
    seen = set()
    for full in files:
        name = os.path.basename(full)
        rel = rel_posix(full, root)
        if name in CONFIG_NAMES and rel not in seen:
            seen.add(rel)
            hints.append(rel)
        ext = os.path.splitext(name)[1]
        if ext in BUILD_HINT_EXT and rel not in seen:
            seen.add(rel)
            hints.append(rel)

    systems = []
    joined = " ".join(hints)
    if "CMakeLists.txt" in hints:
        systems.append("CMake")
    if "Makefile" in hints or "makefile" in hints or "GNUmakefile" in hints:
        systems.append("Make")
    if "platformio.ini" in hints:
        systems.append("PlatformIO")
    if any(h.endswith(".ioc") for h in hints):
        systems.append("STM32CubeMX")
    if "pyproject.toml" in hints or "setup.py" in hints:
        systems.append("Python packaging")
    if "package.json" in hints:
        systems.append("npm/node")
    if "Cargo.toml" in hints:
        systems.append("Cargo")
    if "go.mod" in hints:
        systems.append("Go modules")
    if any(h.endswith(".uvprojx") or h.endswith(".uvproj") for h in hints):
        systems.append("Keil MDK")
    if any(h.endswith(".ewp") for h in hints):
        systems.append("IAR")
    if not systems:
        systems.append("未识别（可能靠 IDE 工程文件或手工命令）")

    return {"systems": systems, "hint_files": hints[:20]}


def detect_entries(files, root):
    entries = []
    for full in files:
        if os.path.basename(full) in ENTRY_NAMES:
            entries.append(rel_posix(full, root))
    return sorted(entries)[:10]


def group_modules(files, root):
    """按 src/ 或顶层目录归类模块。返回 {module: [rel paths]}"""
    modules = {}
    for full in files:
        rel = rel_posix(full, root)
        parts = rel.split("/")
        if len(parts) == 1:
            module = "(root)"
        elif parts[0] in ("src", "source", "sources", "app", "lib", "core", "driver", "drivers"):
            module = parts[1] if len(parts) > 2 else os.path.splitext(parts[1])[0]
        else:
            module = parts[0]
        modules.setdefault(module, []).append(rel)
    return modules


def module_hash(paths_rel, root):
    joined = "\n".join(sorted(paths_rel))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def load_state(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def scan(root: str, max_files: int, reuse_state: dict):
    files, skipped, truncated = walk_files(root, max_files)

    old_files = (reuse_state or {}).get("files", {}) or {}
    file_index = {}
    hashed = 0
    reused = 0

    for full in files:
        rel = rel_posix(full, root)
        try:
            stat = os.stat(full)
        except OSError:
            continue
        entry = {
            "size": stat.st_size,
            "mtime": _dt.datetime.fromtimestamp(stat.st_mtime).astimezone().replace(
                microsecond=0).isoformat(),
            "sha256": "",
        }
        previous = old_files.get(rel)
        if previous and previous.get("size") == entry["size"] and previous.get("mtime") == entry["mtime"]:
            entry["sha256"] = previous.get("sha256", "")
            reused += 1
        elif stat.st_size <= MAX_HASH_BYTES:
            entry["sha256"] = sha256_of(full)
            hashed += 1
        file_index[rel] = entry

    by_ext = {}
    total_bytes = 0
    for rel, entry in file_index.items():
        ext = os.path.splitext(rel)[1].lower() or "(none)"
        by_ext[ext] = by_ext.get(ext, 0) + 1
        total_bytes += entry["size"]

    modules_raw = group_modules(files, root)
    modules = {}
    for name, rels in sorted(modules_raw.items()):
        hashes = []
        for rel in sorted(rels):
            digest = file_index.get(rel, {}).get("sha256", "")
            if digest:
                hashes.append("%s:%s" % (rel, digest))
        modules[name] = {
            "files": sorted(rels),
            "hash": hashlib.sha256("\n".join(hashes).encode("utf-8")).hexdigest() if hashes else "",
        }

    source_files = [r for r in file_index if os.path.splitext(r)[1] in SOURCE_EXTS]
    return {
        "root": root.replace("\\", "/"),
        "scannedAt": now_iso(),
        "fileCount": len(file_index),
        "sourceFileCount": len(source_files),
        "totalBytes": total_bytes,
        "byExt": dict(sorted(by_ext.items(), key=lambda kv: -kv[1])),
        "build": detect_build(files, root),
        "entries": detect_entries(files, root),
        "modules": modules,
        "files": file_index,
        "truncated": truncated,
        "skippedDirs": sorted(set(skipped))[:20],
        "hashStats": {"hashed": hashed, "reused": reused},
    }


def render_human(result: dict) -> str:
    lines = []
    lines.append("=" * 74)
    lines.append("项目扫描  %s" % result["root"])
    lines.append("=" * 74)
    lines.append("文件 %d（源码 %d）  体积 %.1f KB  截断=%s  新哈希=%d 复用=%d" % (
        result["fileCount"], result["sourceFileCount"],
        result["totalBytes"] / 1024.0, result["truncated"],
        result["hashStats"]["hashed"], result["hashStats"]["reused"]))

    build = result["build"]
    lines.append("")
    lines.append("构建系统: " + ", ".join(build["systems"]))
    if build["hint_files"]:
        lines.append("  依据: " + ", ".join(build["hint_files"][:8]))

    lines.append("")
    lines.append("入口候选: " + (", ".join(result["entries"]) or "未发现 main/index 类入口"))
    lines.append("")
    lines.append("模块（%d）:" % len(result["modules"]))
    for name, info in list(result["modules"].items())[:25]:
        lines.append("  %-22s %3d 个文件  hash=%s" % (
            name, len(info["files"]), (info["hash"] or "-")[:12]))
    if len(result["modules"]) > 25:
        lines.append("  ... 其余 %d 个模块省略" % (len(result["modules"]) - 25))

    lines.append("")
    lines.append("按扩展名: " + ", ".join(
        "%s=%d" % (k, v) for k, v in list(result["byExt"].items())[:12]))
    if result["truncated"]:
        lines.append("")
        lines.append("[警告] 达到 --max-files 上限，结果不完整，结论需标注“未覆盖全部文件”")
    return "\n".join(lines)


EA_SKELETON = {
    "PROJECT_MAP.md": "# 项目地图（待填写）\n\n> 由 engineering-assistant 生成，请以实际代码为准。\n",
    "MODULES.md": "# 模块清单（待填写）\n",
    "DECISIONS.md": "# 技术决策记录\n\n> 只追加，不改写历史。\n",
    "ISSUES.md": "# 已知问题\n",
    "PROGRESS.md": "# 开发进度\n",
    "GLOSSARY.md": "# 术语表\n",
}


def template_dir():
    """优先使用随包模板，保证骨架只有一份定义。"""
    here = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.join(here, "..", "templates", "knowledge-base")
    return candidate if os.path.isdir(candidate) else ""


def ensure_ea(root: str, result: dict, update_state: bool):
    ea = os.path.join(root, ".ea")
    created = []
    if not os.path.isdir(ea):
        os.makedirs(ea, exist_ok=True)
        created.append(".ea/")

    templates = template_dir()
    for name in sorted(EA_SKELETON):
        path = os.path.join(ea, name)
        if os.path.exists(path):
            continue
        body = EA_SKELETON[name]
        source = os.path.join(templates, name) if templates else ""
        if source and os.path.isfile(source):
            try:
                with open(source, "r", encoding="utf-8") as handle:
                    body = handle.read()
            except OSError:
                pass
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(body)
        created.append(".ea/" + name)

    state_path = os.path.join(ea, "state.json")
    existing = load_state(state_path) or {}
    state = {
        "schemaVersion": 1,
        "createdAt": existing.get("createdAt") or now_iso(),
        "updatedAt": now_iso(),
        "root": result["root"],
        "toolchain": existing.get("toolchain") or {},
        "files": result["files"],
        "modules": result["modules"],
        "knowledge": existing.get("knowledge") or {},
        "scan": {
            "fileCount": result["fileCount"],
            "sourceFileCount": result["sourceFileCount"],
            "buildSystems": result["build"]["systems"],
            "entries": result["entries"],
            "truncated": result["truncated"],
        },
    }
    if update_state:
        with open(state_path, "w", encoding="utf-8") as handle:
            json.dump(state, handle, ensure_ascii=False, indent=2, sort_keys=False)
        created.append(".ea/state.json")
    return created, state


def main(argv=None) -> int:
    _reconfigure_stdout()
    parser = argparse.ArgumentParser(description="项目结构与指纹扫描（只读）")
    parser.add_argument("--root", default=".", help="项目根目录，默认当前目录")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--init", action="store_true", help="创建 .ea/ 骨架（不覆盖已有文件）")
    parser.add_argument("--update-state", action="store_true", help="写入 .ea/state.json")
    parser.add_argument("--max-files", type=int, default=4000, help="扫描文件数上限")
    args = parser.parse_args(argv)

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        sys.stderr.write("不是目录: %s\n" % root)
        return 2

    state_path = os.path.join(root, ".ea", "state.json")
    previous = load_state(state_path)
    result = scan(root, args.max_files, previous)

    created = []
    if args.init or args.update_state:
        created, _ = ensure_ea(root, result, args.update_state)
        result["eaCreated"] = created

    if args.json:
        printable = dict(result)
        printable.pop("files", None)  # 文件级明细过大，只在写入 state 时使用
        print(json.dumps(printable, ensure_ascii=False, indent=2))
    else:
        print(render_human(result))
        if created:
            print("")
            print("已写入: " + ", ".join(created))
        if not os.path.isdir(os.path.join(root, ".ea")):
            print("")
            print("提示: 尚无 .ea/ 知识库，可用 --init 建立骨架")
    return 0


if __name__ == "__main__":
    sys.exit(main())