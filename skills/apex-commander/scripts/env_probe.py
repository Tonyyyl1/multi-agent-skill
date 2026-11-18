#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cross-platform (macOS + Windows + Linux) workspace & toolchain probe for Apex Commander.
Outputs structured JSON so the Chief Commander can quickly detect available compilers,
test runners, shell environment, and filesystem case-sensitivity.
"""

import json
import os
import platform
import shutil
import sys
import tempfile
from pathlib import Path


def check_case_sensitive(directory: Path) -> bool:
    try:
        with tempfile.NamedTemporaryFile(dir=directory, prefix="agyCaseTest_", delete=True) as tmp:
            p = Path(tmp.name)
            swapped = p.with_name(p.name.swapcase())
            return not swapped.exists()
    except Exception:
        # macOS APFS and Windows NTFS default to case-insensitive
        return platform.system() not in {"Windows", "Darwin"}


def detect_tools() -> dict:
    candidates = [
        "git",
        "python",
        "python3",
        "py",
        "pytest",
        "node",
        "npm",
        "pnpm",
        "yarn",
        "bun",
        "cargo",
        "rustc",
        "go",
        "java",
        "javac",
        "mvn",
        "gradle",
        "sbt",
        "scala",
        "scalac",
        "dotnet",
    ]
    found = {}
    for cmd in candidates:
        resolved = shutil.which(cmd)
        if resolved:
            # Skip Windows Store execution alias stubs (0-byte shims in Microsoft\WindowsApps)
            if platform.system() == "Windows" and "microsoft\\windowsapps" in resolved.lower():
                try:
                    if Path(resolved).stat().st_size == 0:
                        continue
                except OSError:
                    continue
            found[cmd] = resolved
    return found


def main() -> int:
    cwd = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
    host_os = platform.system()
    default_shell = (
        "powershell"
        if host_os == "Windows"
        else os.environ.get("SHELL", "/bin/zsh" if host_os == "Darwin" else "/bin/bash")
    )
    python_cmd = "python" if host_os == "Windows" else "python3"

    top_entries = []
    if cwd.exists() and cwd.is_dir():
        for entry in sorted(cwd.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))[:50]:
            top_entries.append(f"{entry.name}/" if entry.is_dir() else entry.name)

    report = {
        "host_os": host_os,
        "os_release": platform.release(),
        "arch": platform.machine(),
        "default_shell": default_shell,
        "recommended_python_cli": python_cmd,
        "python_runtime": sys.version.split()[0],
        "workspace": str(cwd),
        "filesystem_case_sensitive": check_case_sensitive(cwd if cwd.exists() else Path.cwd()),
        "available_tools": detect_tools(),
        "top_level_entries": top_entries,
    }
    sys.stdout.reconfigure(encoding="utf-8") if hasattr(sys.stdout, "reconfigure") else None
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
