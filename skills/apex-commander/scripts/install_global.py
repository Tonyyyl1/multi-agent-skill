#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cross-platform Global Skill Installer for Apex Commander (macOS, Windows, Linux).

Installs or syncs `apex-commander` into Antigravity's global skill discovery directory:
  - macOS / Linux: ~/.gemini/config/skills/apex-commander
  - Windows:       C:\\Users\\<user>\\.gemini\\config\\skills\\apex-commander

Usage:
  Windows: python .agents/skills/apex-commander/scripts/install_global.py
  macOS:   python3 .agents/skills/apex-commander/scripts/install_global.py
"""

import argparse
import ast
import os
import platform
import shutil
import stat
import sys
from pathlib import Path


SKILL_NAME = "apex-commander"
LF_EXTENSIONS = {".sh", ".py", ".md", ".json", ".gitattributes"}


def normalize_file_endings(root: Path) -> None:
    """Ensures .sh/.py/.md/.json files use clean LF endings so macOS/Linux never fail on CRLF."""
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() in LF_EXTENSIONS or p.name == ".gitattributes":
            raw = p.read_bytes()
            cleaned = raw.replace(b"\r\n", b"\n")
            if cleaned != raw:
                p.write_bytes(cleaned)
        if p.suffix.lower() == ".sh" and platform.system() != "Windows":
            mode = p.stat().st_mode
            p.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def verify_skill_dir(skill_dir: Path) -> tuple:
    skill_md = skill_dir / "SKILL.md"
    orchestrator = skill_dir / "scripts" / "auto_orchestrator.py"
    if not skill_md.is_file():
        return False, f"Missing SKILL.md at {skill_md}"
    if not orchestrator.is_file():
        return False, f"Missing auto_orchestrator.py at {orchestrator}"
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return False, "SKILL.md does not start with YAML frontmatter ('---')."
    if "name:" not in text or "description:" not in text:
        return False, "SKILL.md frontmatter is missing required `name` or `description`."
    # Compile-check Python scripts (allow top-level `await` used by `run_workflow`)
    for py_file in (skill_dir / "scripts").glob("*.py"):
        source = py_file.read_text(encoding="utf-8")
        compile(source, str(py_file), "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    return True, f"Verified `{SKILL_NAME}` at {skill_dir} (OS={platform.system()})."


def is_within(child: Path, parent: Path) -> bool:
    """True if `child` is `parent` itself or lives somewhere underneath it."""
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def looks_like_installed_skill(directory: Path) -> bool:
    """True only if `directory` holds a SKILL.md whose frontmatter declares `name: apex-commander`."""
    skill_md = directory / "SKILL.md"
    if not skill_md.is_file():
        return False
    try:
        parts = skill_md.read_text(encoding="utf-8").split("---")
    except (OSError, UnicodeDecodeError):
        return False
    if len(parts) < 3:
        return False
    return any(line.strip() == f"name: {SKILL_NAME}" for line in parts[1].splitlines())


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Install or verify Apex Commander skill globally.")
    parser.add_argument(
        "--target",
        default=str(Path.home() / ".gemini" / "config" / "skills" / SKILL_NAME),
        help="Target skill installation directory (default: ~/.gemini/config/skills/apex-commander)",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify the source skill bundle (read-only: nothing is copied or rewritten).",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Remove the global installation directory.",
    )
    ns = parser.parse_args()

    source_dir = Path(__file__).resolve().parent.parent
    target_dir = Path(ns.target).expanduser().resolve()

    if ns.uninstall:
        if not target_dir.exists():
            print(f"[INFO] Global skill directory does not exist: {target_dir}")
            return 0
        # Never rmtree an arbitrary --target: it must really be an installed apex-commander skill.
        if not looks_like_installed_skill(target_dir):
            print(
                f"[ERROR] Refusing to remove {target_dir}: it has no SKILL.md declaring "
                f"`name: {SKILL_NAME}`, so it does not look like an installed `{SKILL_NAME}` skill.",
                file=sys.stderr,
            )
            return 1
        shutil.rmtree(target_dir)
        print(f"[OK] Removed global skill at: {target_dir}")
        return 0

    # --verify-only must stay read-only, so only rewrite line endings when actually installing.
    if not ns.verify_only:
        normalize_file_endings(source_dir)
    ok, msg = verify_skill_dir(source_dir)
    if not ok:
        print(f"[ERROR] Source verification failed: {msg}", file=sys.stderr)
        return 1

    if ns.verify_only:
        print(f"[OK] {msg}")
        return 0

    if source_dir == target_dir:
        print(f"[OK] Source is already at target location: {target_dir}")
        return 0

    if is_within(target_dir, source_dir):
        print(
            f"[ERROR] Target {target_dir} is inside the source bundle {source_dir}; "
            "refusing to copy a directory into itself.",
            file=sys.stderr,
        )
        return 1

    target_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        source_dir,
        target_dir,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
    )
    normalize_file_endings(target_dir)

    ok_target, msg_target = verify_skill_dir(target_dir)
    if not ok_target:
        print(f"[ERROR] Installed target verification failed: {msg_target}", file=sys.stderr)
        return 1

    print(f"[OK] Installed `{SKILL_NAME}` globally to: {target_dir}")
    print(f"[OK] {msg_target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
