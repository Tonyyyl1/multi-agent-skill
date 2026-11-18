# Cross-Platform (macOS & Windows) Compatibility & Unattended Permissions Guide

## 1. Unattended Permission Configuration (无人值守自动工作流权限设置)

Important: Inside `run_workflow`, **background subagents cannot pop up interactive approval dialogs**. As documented by Antigravity:
> *"The user cannot be asked anything from a workflow: a call that needs user approval that has not already been granted is denied (`ToolError.denied == True`)."*

To let dozens of `flash` and `flash_lite` subagents execute multi-round coding and test loops smoothly without permission blocks on **both macOS and Windows**, configure these settings in **Antigravity Settings** (Global or Project-Level):

1. **Tool Execution Policy / Auto-Execution Policy**:
   - Recommended: **`proceed-in-sandbox`** (auto-runs workspace commands safely inside the sandbox without popups) or **`always-proceed`** (fully unattended execution when your build/test toolchain needs local daemons, compilers, or network access).
   - Avoid `strict` or `request-review` during automated multi-round workflows, otherwise terminal commands inside `run_workflow` subagents will be denied.
2. **File Access Policy**:
   - Workspace files are accessible automatically.
   - Set **Non-Workspace File Access** to **`allow`** (or grant specific paths in **Permission Grants**) only if subagents need to read shared caches/SDKs outside the repository root (e.g., `~/.cargo`, `~/.ivy2`, `~/.sbt`, `~/Library/Caches`, `%LOCALAPPDATA%`) or when installing global skills to `~/.gemini/config/skills/`.
3. **Command Allowlist**:
   - Add your project's recurring build/test binaries (`pytest`, `python`, `python3`, `npm`, `pnpm`, `node`, `cargo`, `go`, `sbt`, `gradle`, `mvn`, `dotnet`) so verification gates execute with zero prompts.

---

## 2. macOS vs. Windows Execution Matrix for Subagents

Weaker/faster models (`flash` and `flash_lite`) frequently fail if they guess the wrong OS shell syntax. `scripts/auto_orchestrator.py` automatically detects `platform.system()` and injects the matching rules below into every worker prompt:

| Dimension | Windows (`Windows`) | macOS (`Darwin`) | Cross-Platform Best Practice |
| :--- | :--- | :--- | :--- |
| **Default `run_command` Shell** | `powershell` | `zsh` / `bash` | Prefer `read_file`, `write_file`, `edit_file` over shell file manipulation |
| **Python CLI Binary** | `python` (or `py -3`) — **NEVER `python3`** (Microsoft Store alias trap!) | `python3` — **NEVER bare `python`** | Probe via `scripts/env_probe.py` or branch on `platform.system()` |
| **`run_workflow` Runtime** | Built-in Python 3 runtime (works out of the box) | Built-in Python 3 runtime (works out of the box) | Keep workflow scripts self-contained (Python 3.8+ stdlib) |
| **Command Chaining** | `cmd1; if ($?) { cmd2 }` (PowerShell 5.1 safe) | `cmd1 && cmd2` | Run one clean command per `run_command` call |
| **Environment Variables** | `$env:FOO = "bar"; cmd` | `FOO="bar" cmd` | Pass CLI flags or config files instead of shell env vars |
| **Recursive Delete / Mkdir** | `Remove-Item -Recurse -Force` / `New-Item -ItemType Directory -Force` | `rm -rf` / `mkdir -p` | Manage directories in Python (`pathlib.Path.mkdir(parents=True, exist_ok=True)`) |
| **In-Place Text Edit** | No `sed` | BSD `sed -i ''` (incompatible with GNU `sed -i`!) | **NEVER use `sed -i`** on either OS — always use `edit_file` |
| **Filesystem Case Sensitivity** | Case-insensitive (NTFS) | Case-insensitive by default (APFS) | Never create two files differing only by case (`Parser.scala` vs `parser.scala`) |
| **Text Encoding** | Legacy codepage risk (GBK / CP1252) if unspecified | UTF-8 default | **Always** pass `encoding="utf-8"` in Python / JVM / Node file I/O |
| **Line Endings** | CRLF (`\r\n`) default | LF (`\n`) required for `#!/usr/bin/env ...` scripts | Include `.gitattributes` (`*.sh text eol=lf`, `*.ps1 text eol=crlf`) |
| **Windows Sandbox Specials** | `pnpm install/add/dlx` needs `BypassSandbox: true`; retry transient Node `EPERM` on `mkdir` up to 2x | Standard sandbox | Run package installs in Main Agent preflight before `run_workflow` |

---

## 3. Global Skill Installation Across macOS & Windows

Antigravity discovers global skills from `~/.gemini/config/skills/<skill-name>/SKILL.md` on all operating systems:

- **Windows PowerShell**:
  ```powershell
  powershell -ExecutionPolicy Bypass -File .agents/skills/apex-commander/scripts/install_win.ps1
  ```
  *(Installs to `C:\Users\<User>\.gemini\config\skills\apex-commander`)*

- **macOS Terminal (`zsh` / `bash`)**:
  ```bash
  bash .agents/skills/apex-commander/scripts/install_mac.sh
  ```
  *(Installs to `/Users/<User>/.gemini/config/skills/apex-commander` and normalizes LF line endings + `+x` permissions)*
