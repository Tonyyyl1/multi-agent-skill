#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Root Cross-Platform Installer for `multi-agent-skill` (macOS, Windows, Linux).

Features:
  - Installs `skills/apex-commander` into `~/.gemini/config/skills/apex-commander`
  - Normalizes LF line endings on `.sh/.py/.md/.json` and sets `+x` on POSIX scripts
  - Compile-checks all Python workflow & helper scripts (including top-level `await`)
  - Optional `--with-rule`: idempotently injects/updates the high-complexity auto-routing
    rule inside `~/.gemini/config/GEMINI.md` without touching existing user rules
  - Optional `--uninstall`: cleanly removes the global skill and injected rule block
"""

import argparse
import ast
import os
import platform
import re
import shutil
import stat
import sys
from pathlib import Path


SKILL_NAME = "apex-commander"
RULE_START = "<!-- APEX-COMMANDER-RULE:START -->"
RULE_END = "<!-- APEX-COMMANDER-RULE:END -->"
LF_EXTENSIONS = {".sh", ".py", ".md", ".json", ".gitattributes", ".yml", ".yaml"}


def normalize_tree(root: Path) -> None:
    for p in root.rglob("*"):
        if not p.is_file() or ".git" in p.parts:
            continue
        if p.suffix.lower() in LF_EXTENSIONS or p.name in {".gitattributes", ".gitignore"}:
            raw = p.read_bytes()
            cleaned = raw.replace(b"\r\n", b"\n")
            if cleaned != raw:
                p.write_bytes(cleaned)
        if p.suffix.lower() == ".sh" and platform.system() != "Windows":
            mode = p.stat().st_mode
            p.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def verify_skill(skill_dir: Path) -> tuple:
    skill_md = skill_dir / "SKILL.md"
    orchestrator = skill_dir / "scripts" / "auto_orchestrator.py"
    if not skill_md.is_file():
        return False, f"Missing SKILL.md at {skill_md}"
    if not orchestrator.is_file():
        return False, f"Missing auto_orchestrator.py at {orchestrator}"
    content = skill_md.read_text(encoding="utf-8")
    if not content.startswith("---\n") and not content.startswith("---\r\n"):
        return False, "SKILL.md must begin with YAML frontmatter ('---')."
    if "name:" not in content or "description:" not in content:
        return False, "SKILL.md frontmatter requires `name` and `description`."
    for py_file in (skill_dir / "scripts").glob("*.py"):
        src = py_file.read_text(encoding="utf-8")
        compile(src, str(py_file), "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    return True, f"Verified `{SKILL_NAME}` at {skill_dir} (OS={platform.system()})."


def upsert_global_rule(gemini_md: Path, rule_block: str) -> None:
    gemini_md.parent.mkdir(parents=True, exist_ok=True)
    block = rule_block.strip() + "\n"
    if gemini_md.exists():
        existing = gemini_md.read_text(encoding="utf-8")
        pattern = re.compile(
            re.escape(RULE_START) + r".*?" + re.escape(RULE_END) + r"\n?",
            flags=re.DOTALL,
        )
        if pattern.search(existing):
            updated = pattern.sub(block, existing)
        else:
            sep = "" if existing.endswith("\n\n") or not existing else ("\n" if existing.endswith("\n") else "\n\n")
            updated = existing + sep + block
    else:
        updated = block
    gemini_md.write_text(updated, encoding="utf-8")


def remove_global_rule(gemini_md: Path) -> bool:
    if not gemini_md.exists():
        return False
    existing = gemini_md.read_text(encoding="utf-8")
    pattern = re.compile(
        r"\n*" + re.escape(RULE_START) + r".*?" + re.escape(RULE_END) + r"\n?",
        flags=re.DOTALL,
    )
    if not pattern.search(existing):
        return False
    updated = pattern.sub("\n", existing).strip()
    if updated:
        gemini_md.write_text(updated + "\n", encoding="utf-8")
    else:
        gemini_md.unlink()
    return True


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    repo_root = Path(__file__).resolve().parent
    source_skill = repo_root / "skills" / SKILL_NAME
    rule_template = repo_root / "rules" / "apex-commander-routing.md"
    default_config_root = Path.home() / ".gemini" / "config"

    parser = argparse.ArgumentParser(description="Install multi-agent-skill (`apex-commander`) globally.")
    parser.add_argument(
        "--config-dir",
        default=str(default_config_root),
        help="Antigravity global config root (default: ~/.gemini/config)",
    )
    parser.add_argument(
        "--with-rule",
        action="store_true",
        help="Also install/update the always-on high-complexity routing rule in ~/.gemini/config/GEMINI.md",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verify repository skill files and scripts without modifying global config",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Uninstall global `apex-commander` skill and remove its routing rule block if present",
    )
    ns = parser.parse_args()

    config_root = Path(ns.config_dir).expanduser().resolve()
    target_skill = config_root / "skills" / SKILL_NAME
    gemini_md = config_root / "GEMINI.md"

    if ns.uninstall:
        if target_skill.exists():
            shutil.rmtree(target_skill)
            print(f"[OK] Removed global skill: {target_skill}")
        else:
            print(f"[INFO] Global skill not found: {target_skill}")
        if remove_global_rule(gemini_md):
            print(f"[OK] Removed `{SKILL_NAME}` routing block from: {gemini_md}")
        return 0

    normalize_tree(repo_root)
    ok, msg = verify_skill(source_skill)
    if not ok:
        print(f"[ERROR] {msg}", file=sys.stderr)
        return 1

    if ns.verify_only:
        print(f"[OK] {msg}")
        return 0

    target_skill.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        source_skill,
        target_skill,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store", "Thumbs.db"),
    )
    normalize_tree(target_skill)

    ok_target, msg_target = verify_skill(target_skill)
    if not ok_target:
        print(f"[ERROR] Target verification failed: {msg_target}", file=sys.stderr)
        return 1

    print(f"[OK] Installed `{SKILL_NAME}` to: {target_skill}")
    print(f"[OK] {msg_target}")

    if ns.with_rule:
        if not rule_template.is_file():
            print(f"[ERROR] Missing rule template: {rule_template}", file=sys.stderr)
            return 1
        upsert_global_rule(gemini_md, rule_template.read_text(encoding="utf-8"))
        print(f"[OK] Updated always-on routing rule in: {gemini_md}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
