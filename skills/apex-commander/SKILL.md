---
name: apex-commander
description: >-
  Hierarchical multi-agent orchestration and automated multi-round iterative workflow
  for high-difficulty, complex, architectural, or multi-module tasks across macOS and Windows.
  Activate whenever the user presents a challenging engineering task, system design,
  large feature build, or complex refactor, or asks for a flagship high-reasoning commander model
  to plan and dispatch weaker/faster parallel subagents (`flash` and `flash_lite`) with automated
  global-performance evaluation loops. 当用户提出高难度任务、复杂架构设计、多模块开发重构，或提到
  「指挥官」「总指挥」「上强度」「多子代理并发」「多轮全局迭代」时激活。
---

# Apex Commander: Hierarchical Multi-Agent & Auto-Iterative Workflow

Use this skill to execute complex tasks through a strict **Commander -> Parallel Tiered Workers -> Global Telemetry -> Autonomous Next-Round Iteration** architecture that works identically on **macOS** and **Windows**.

---

## 1. Core Hierarchy & Reasoning Discipline

1. **L0 — Chief Architect & Commander (Strongest Model + Highest Reasoning Effort)**:
   - **You (the Main Agent)** act as the L0 Commander using the user's selected flagship `(High)` reasoning model (and inside `run_workflow`, `commander_model: "inherit"` inherits your exact model; if the main session was started on a lower-tier model, set `commander_model: "pro"` and note that selecting a `(High)` flagship model maximizes Commander reasoning).
   - **Strict Division of Labor**: NEVER spend L0 turns writing bulk implementation code. Reserve L0 reasoning exclusively for:
     - System architecture & shared interface contracts
     - Conflict-free task decomposition (DAG waves + disjoint file ownership)
     - Global multi-dimensional acceptance rubric & final sign-off
2. **L1 — Core Implementation Subagents (`model: "flash"`, 弱一级)**:
   - Assign core modules, algorithms, stateful domain logic, complex integrations, non-trivial bug fixes, and unit/integration test suites.
3. **L2 — Rapid High-Concurrency Subagents (`model: "flash_lite"`, 弱两级)**:
   - Assign repo scouting, project/directory scaffolding, DTOs/types/configs, test fixtures/mocks, documentation, and fast hygiene/cross-platform checks.
   - **Auto-Escalation**: Any `flash_lite` task that fails or leaves defects in Round `r` must be escalated to `flash` in Round `r+1`.

For detailed routing rules, prompt contracts, and fallback patterns, read [worker-prompt-contracts.md](./references/worker-prompt-contracts.md).

---

## 2. Step-by-Step Execution Workflow

### Step 1: Cross-Platform Environment & Codebase Reconnaissance

1. Detect host OS, shell, case-sensitivity, and installed toolchains (`pytest`, `node`, `cargo`, `sbt`, `gradle`, `go`, etc.) by running [env_probe.py](./scripts/env_probe.py):
   - **Windows (`powershell`)**: `python .agents/skills/apex-commander/scripts/env_probe.py` *(or `~/.gemini/config/skills/apex-commander/scripts/env_probe.py` when installed globally; NEVER invoke `python3` on Windows)*
   - **macOS (`zsh`/`bash`)**: `python3 .agents/skills/apex-commander/scripts/env_probe.py`
2. For large existing repositories, fan out read-only `flash_lite` scout subagents in parallel to map relevant modules without bloating L0 context.
3. If the project requires one-time external package installation or network commands that need `BypassSandbox: true` (e.g., `pnpm install`), run that preflight step **before** launching `run_workflow` (see [cross-platform-and-permissions.md](./references/cross-platform-and-permissions.md)).

### Step 2: Freeze Architecture Contracts & Build Master Blueprint

Using full L0 reasoning depth, design the blueprint and write it as UTF-8 JSON to `<ArtifactScratchDir>/blueprint.json` (follow [blueprint_example.json](./examples/blueprint_example.json)):

- **`user_requirements`**: Explicit list of every explicit and implicit requirement (`REQ-1..N`).
- **`architecture_contract`**: Module boundaries, exact shared types/signatures, UTF-8 & `pathlib` cross-platform rules, and error handling invariants.
- **`global_acceptance_criteria`** & **`verification_commands`**: Objective build, typecheck, and test commands appropriate for the detected host OS.
- **`initial_waves`**:
  - **Wave 1**: Shared contracts, interfaces, types, and config skeleton (`owned_files` strictly disjoint).
  - **Wave 2+**: Massive parallel fan-out across `flash` (core modules/tests) and `flash_lite` (scaffolding/DTOs/CLI/fixtures/docs).
  - **Golden Rule**: Two tasks in the same wave MUST NEVER share a file in `owned_files` (case-insensitive on both macOS APFS and Windows NTFS).

### Step 3: Launch the Automated Multi-Round Closed-Loop Engine (`run_workflow`)

Invoke `run_workflow` pointing `ScriptPath` to the resolved absolute path of [auto_orchestrator.py](./scripts/auto_orchestrator.py):

```json
{
  "ScriptPath": "<resolved-skill-dir>/scripts/auto_orchestrator.py",
  "Description": "Multi-round Commander + parallel flash/flash_lite implementation & global iteration",
  "Args": {
    "blueprint_path": "<ArtifactScratchDir>/blueprint.json",
    "report_output_path": "<ArtifactScratchDir>/execution_report.json",
    "commander_model": "inherit",
    "max_rounds": 4,
    "pass_score_threshold": 95
  }
}
```

**What `auto_orchestrator.py` executes automatically**:
1. Validates/partitions waves so parallel workers never collide on case-insensitive macOS/Windows paths, and injects OS-specific shell guardrails (`PowerShell` vs `zsh/bash`).
2. Launches massive parallel `flash` and `flash_lite` subagents (`parallel()`) with fault isolation so a single worker exception never cancels sibling workers.
3. Runs 3 parallel verification subagents after every round: **Build & Test Gatekeeper (`flash`)**, **Requirements & Integration Auditor (`flash`)**, and **macOS/Windows Cross-Platform Inspector (`flash_lite`)**.
4. Feeds all worker outputs + objective gate/audit telemetry to the persistent **Commander (`inherit`/`pro`)**, which scores global performance (0–100) against every user requirement:
   - If `verdict == "PASS"` **and** hard build/test + zero-unmet-requirement gates pass -> finishes early.
   - Otherwise -> **immediately generates Round `r+1` corrective waves** and continues iterating automatically up to `max_rounds`!

After calling `run_workflow`, **stop calling tools and wait reactively** for completion notification (never poll).

### Step 4: Interactive Fallback Mode (When Needed)

If `run_workflow` reports permission-denied tool calls (`ToolError.denied`) or the task requires interactive `browser` verification / mid-round user input:
1. Consult [cross-platform-and-permissions.md](./references/cross-platform-and-permissions.md) if unattended permissions need adjustment.
2. Or execute the exact same wave & multi-round global evaluation loop directly from L0 using parallel `invoke_subagent` calls (`Model="flash"` and `Model="flash_lite"`) per [worker-prompt-contracts.md](./references/worker-prompt-contracts.md).

### Step 5: Final L0 Sign-Off & Delivery

1. Read `<ArtifactScratchDir>/execution_report.json` (and if `final_verdict != "PASS"` after `max_rounds`, run one targeted follow-up workflow or fix remaining edge cases).
2. Run a final sanity check on the verification suite to confirm exit code `0`.
3. Present a concise summary covering: architecture overview, rounds & parallel subagent tiers dispatched, verification proof, and cross-platform compatibility confirmation.
