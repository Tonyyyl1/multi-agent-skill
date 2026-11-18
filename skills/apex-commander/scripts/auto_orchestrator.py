# -*- coding: utf-8 -*-
"""
Apex Commander - Multi-Round Hierarchical Orchestration Engine for `run_workflow`.

Architecture:
  - Tier 0 (Commander: `inherit` on Flagship High-Reasoning model, or `pro`):
    Designs/refines task waves, enforces interface contracts, evaluates global
    performance against all user requirements, and plans iterative delta rounds.
  - Tier -1 (`flash`):
    Implements core modules, complex business logic, cross-file integrations,
    and targeted bug fixes / test suites in parallel.
  - Tier -2 (`flash_lite`):
    Executes high-fan-out reconnaissance, scaffolding, DTOs/types, fixtures,
    documentation, and static checks at maximum concurrency.

Cross-Platform Support:
  - Runs identically on macOS (Darwin / zsh / bash) and Windows (PowerShell)
    inside Antigravity's built-in `run_workflow` Python runtime.
  - Note: Keep this script 100% self-contained (stdlib only) because
    `run_workflow` does not import sibling local modules.
"""

import json
import os
import platform
import sys
import traceback
from pathlib import Path, PurePath


# ---------------------------------------------------------------------------
# 1. Host OS Detection & Cross-Platform Worker Guardrails
# ---------------------------------------------------------------------------

HOST_OS = platform.system()  # 'Windows', 'Darwin', or 'Linux'
IS_WINDOWS = HOST_OS == "Windows"
IS_MAC = HOST_OS == "Darwin"
WORKSPACE_ROOT = WORKSPACES[0] if WORKSPACES else os.getcwd()


def build_os_guardrails() -> str:
    if IS_WINDOWS:
        return (
            "HOST ENVIRONMENT: Windows (Shell: PowerShell).\n"
            "- Prefer `read_file`, `write_file`, and `edit_file` over shell file edits.\n"
            "- If running shell commands via `run_command`, use valid PowerShell syntax ONLY:\n"
            "  * Use `python` (or `py -3`), NEVER `python3` (Windows Store alias trap).\n"
            "  * Chain statements with `;` (compatible with all PowerShell versions).\n"
            "  * NEVER use Bash-only syntax (`export VAR=x`, `rm -rf`, `cat << 'EOF'`, `sed -i`, `/dev/null`).\n"
            "  * Always read/write text files with explicit UTF-8 encoding.\n"
            "- Write application code cross-platform (`pathlib.Path` / `os.path`, no hardcoded `C:\\` or `/tmp`)."
        )
    if IS_MAC:
        return (
            "HOST ENVIRONMENT: macOS / Darwin (Shell: POSIX zsh/bash).\n"
            "- Prefer `read_file`, `write_file`, and `edit_file` over shell file edits.\n"
            "- If running shell commands via `run_command`:\n"
            "  * Use `python3`, NEVER bare `python`.\n"
            "  * NEVER use `sed -i` without macOS BSD awareness — always use `edit_file` instead.\n"
            "  * Remember macOS APFS is case-insensitive by default (`Foo.ts` collides with `foo.ts`).\n"
            "- Write application code cross-platform (`pathlib.Path` / `os.path`, no hardcoded `/Users/...` or `/tmp` without `tempfile`)."
        )
    return (
        f"HOST ENVIRONMENT: {HOST_OS} (Shell: POSIX sh/bash).\n"
        "- Prefer `read_file`, `write_file`, and `edit_file` over shell text manipulation.\n"
        "- Use `python3` and write cross-platform code (`pathlib.Path`, UTF-8 encoding)."
    )


OS_GUARDRAILS = build_os_guardrails()


# ---------------------------------------------------------------------------
# 2. Model Routing & Schema Definitions
# ---------------------------------------------------------------------------

VALID_MODELS = {"inherit", "pro", "flash", "flash_lite"}


def resolve_worker_model(tier_value: str) -> str:
    if not tier_value:
        return "flash"
    t = str(tier_value).strip().lower().replace("-", "_")
    if t in {"flash", "tier_1", "t1", "l1", "builder", "weak_1"}:
        return "flash"
    if t in {"flash_lite", "lite", "tier_2", "t2", "l2", "scout", "rapid", "weak_2"}:
        return "flash_lite"
    if t in VALID_MODELS:
        return t
    log(f"[WARN] Unknown model tier '{tier_value}', defaulting to 'flash'.")
    return "flash"


def safe_tokens_used():
    fn = globals().get("tokens_used")
    if callable(fn):
        try:
            return fn()
        except Exception:
            return None
    return None


TASK_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "tier": {
            "type": "string",
            "enum": ["flash", "flash_lite"],
            "description": "'flash' (1 tier weaker: core logic/modules/fixes) or 'flash_lite' (2 tiers weaker: boilerplate/DTOs/fixtures/docs/scouting).",
        },
        "owned_files": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Relative file paths this worker is exclusively permitted to create or edit.",
        },
        "readonly_files": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Contract or reference files this worker must read and obey without editing.",
        },
        "instructions": {
            "type": "string",
            "description": "Self-contained implementation spec, exact signatures/contracts, and edge cases.",
        },
        "acceptance_check": {
            "type": "string",
            "description": "Scoped verification check this worker must confirm before finishing.",
        },
    },
    "required": ["id", "title", "tier", "owned_files", "instructions", "acceptance_check"],
}

WAVE_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "wave_name": {"type": "string"},
        "tasks": {"type": "array", "items": TASK_ITEM_SCHEMA},
    },
    "required": ["wave_name", "tasks"],
}

INITIAL_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "architecture_summary": {"type": "string"},
        "waves": {"type": "array", "items": WAVE_ITEM_SCHEMA},
    },
    "required": ["architecture_summary", "waves"],
}

WORKER_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["completed", "partial", "blocked"],
        },
        "summary": {"type": "string"},
        "files_changed": {"type": "array", "items": {"type": "string"}},
        "verification_done": {"type": "string"},
        "open_issues": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["status", "summary", "files_changed", "verification_done", "open_issues"],
}

GATE_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "all_passed": {"type": "boolean"},
        "commands_executed": {"type": "array", "items": {"type": "string"}},
        "failure_summary": {"type": "string"},
        "raw_error_excerpt": {"type": "string"},
    },
    "required": ["all_passed", "commands_executed", "failure_summary", "raw_error_excerpt"],
}

AUDIT_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "clean": {"type": "boolean"},
        "findings": {"type": "array", "items": {"type": "string"}},
        "missing_or_stubbed": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["clean", "findings", "missing_or_stubbed"],
}

COMMANDER_EVAL_SCHEMA = {
    "type": "object",
    "properties": {
        "global_score": {
            "type": "integer",
            "description": "Global score 0-100 across all user requirements, build/test gates, integration, and cross-platform readiness.",
        },
        "verdict": {
            "type": "string",
            "enum": ["PASS", "ITERATE"],
        },
        "unmet_or_partial_requirements": {
            "type": "array",
            "items": {"type": "string"},
        },
        "global_diagnosis": {"type": "string"},
        "next_round_waves": {
            "type": "array",
            "items": WAVE_ITEM_SCHEMA,
            "description": "Required non-empty corrective/iterative waves when verdict is ITERATE; empty array when verdict is PASS.",
        },
    },
    "required": [
        "global_score",
        "verdict",
        "unmet_or_partial_requirements",
        "global_diagnosis",
        "next_round_waves",
    ],
}


# ---------------------------------------------------------------------------
# 3. Conflict-Free Wave Partitioner (Case-Insensitive Safe for Mac & Windows)
# ---------------------------------------------------------------------------

def normalize_rel_path(p: str) -> str:
    cleaned = str(p).strip().replace("\\", "/")
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    # Case-folded normalization prevents APFS (macOS) & NTFS (Windows) collisions
    return PurePath(cleaned).as_posix().lower()


def split_into_conflict_free_subwaves(tasks: list) -> list:
    """
    Guarantees no two tasks running concurrently in `parallel()` share an owned
    file path (case-insensitive for macOS APFS and Windows NTFS safety).
    """
    subwaves = []
    for task in tasks:
        owned_norm = {normalize_rel_path(f) for f in task.get("owned_files", []) if f}
        placed = False
        for bucket, claimed_paths in subwaves:
            if not (owned_norm & claimed_paths):
                bucket.append(task)
                claimed_paths.update(owned_norm)
                placed = True
                break
        if not placed:
            subwaves.append(([task], set(owned_norm)))
    return [bucket for bucket, _ in subwaves]


# ---------------------------------------------------------------------------
# 4. Configuration Loader
# ---------------------------------------------------------------------------

raw_args = dict(args) if ("args" in globals() and args) else {}
if raw_args.get("blueprint_path"):
    bp_file = Path(raw_args["blueprint_path"])
    if not bp_file.is_absolute():
        bp_file = Path(WORKSPACE_ROOT) / bp_file
    bp_data = json.loads(bp_file.read_text(encoding="utf-8"))
    for k, v in raw_args.items():
        if k != "blueprint_path" and v is not None:
            bp_data[k] = v
    cfg = bp_data
else:
    cfg = raw_args

TASK_TITLE = cfg.get("task_title", "High-Difficulty Hierarchical Engineering Task")
USER_REQUIREMENTS = cfg.get("user_requirements", [])
if isinstance(USER_REQUIREMENTS, str):
    USER_REQUIREMENTS = [USER_REQUIREMENTS]

ARCHITECTURE_CONTRACT = cfg.get("architecture_contract", "")
ACCEPTANCE_CRITERIA = cfg.get(
    "global_acceptance_criteria",
    [
        "All user requirements are completely implemented without TODOs or placeholder stubs.",
        "All build, typecheck, and test commands pass with exit code 0.",
        "Modules integrate cleanly and adhere to cross-platform (macOS + Windows) rules.",
    ],
)
VERIFICATION_COMMANDS = cfg.get("verification_commands", [])
COMMANDER_MODEL = cfg.get("commander_model", "inherit")
if COMMANDER_MODEL not in VALID_MODELS:
    COMMANDER_MODEL = "inherit"

WORKER_WORKSPACE = cfg.get("workspace_mode", "inherit")
if WORKER_WORKSPACE not in {"inherit", "share", "branch"}:
    WORKER_WORKSPACE = "inherit"

MAX_ROUNDS = max(1, int(cfg.get("max_rounds", 3)))
PASS_SCORE_THRESHOLD = int(cfg.get("pass_score_threshold", 95))
REPORT_OUTPUT_PATH = cfg.get("report_output_path", "")
DRY_RUN = bool(cfg.get("dry_run", False))

if not USER_REQUIREMENTS and not cfg.get("initial_waves"):
    raise ValueError(
        "auto_orchestrator requires `user_requirements` (or `blueprint_path` with `user_requirements` / `initial_waves`)."
    )


# ---------------------------------------------------------------------------
# 5. Subagent Runners (Workers + Global Gatekeepers)
# ---------------------------------------------------------------------------

def build_worker_prompt(round_num: int, wave_name: str, task: dict) -> str:
    owned = task.get("owned_files", [])
    readonly = task.get("readonly_files", [])
    owned_block = "\n".join(f"  - {f}" for f in owned) if owned else "  - (Read-only / analysis task — do NOT modify files)"
    readonly_block = "\n".join(f"  - {f}" for f in readonly) if readonly else "  - (Inspect workspace as needed, read-only)"

    return f"""[Round {round_num} | {wave_name} | Task {task.get('id', 'T')}: {task.get('title', 'Worker')}]

You are an implementation subagent executing a scoped assignment from the Chief Architect & Commander.

=== 1. HOST OS & TOOLING RULES ===
{OS_GUARDRAILS}
- Workspace Root: {WORKSPACE_ROOT}

=== 2. GLOBAL ARCHITECTURE CONTRACT ===
{ARCHITECTURE_CONTRACT or '(Follow existing repository conventions and clean modular boundaries.)'}

=== 3. STRICT FILE OWNERSHIP (CRITICAL — PARALLEL EXECUTION) ===
Other subagents are running in parallel right now.
YOU MAY ONLY CREATE OR MODIFY THESE OWNED FILES:
{owned_block}

READ-ONLY CONTRACT / REFERENCE FILES (DO NOT MODIFY):
{readonly_block}

NEVER edit any file outside your OWNED FILES list, and do NOT run full-repo lock-heavy clean/install commands unless explicitly instructed below.

=== 4. YOUR TASK SPECIFICATION ===
{task.get('instructions', '')}

=== 5. SCOPED SELF-VERIFICATION ===
Before calling `finish`, verify your work:
{task.get('acceptance_check', 'Read back edited files to ensure zero syntax errors, zero missing imports, and zero placeholder stubs.')}

Call `finish` with the required JSON report once complete.
"""


async def run_safe_worker(round_num: int, wave_name: str, task: dict) -> dict:
    task_id = str(task.get("id", "task"))
    title = str(task.get("title", task_id))
    model_tier = resolve_worker_model(task.get("tier", "flash"))
    prompt = build_worker_prompt(round_num, wave_name, task)
    role_label = f"[R{round_num}][{model_tier}] {task_id}: {title}"[:80]

    try:
        res = await agent(
            prompt=prompt,
            schema=WORKER_RESULT_SCHEMA,
            role=role_label,
            workspace=WORKER_WORKSPACE,
            model=model_tier,
        )
        return {
            "id": task_id,
            "title": title,
            "tier": model_tier,
            "owned_files": task.get("owned_files", []),
            **res,
        }
    except Exception as exc:
        err_msg = f"{type(exc).__name__}: {exc}"
        log(f"[WARN] Worker {task_id} ({model_tier}) failed: {err_msg}")
        return {
            "id": task_id,
            "title": title,
            "tier": model_tier,
            "owned_files": task.get("owned_files", []),
            "status": "blocked",
            "summary": "Worker raised an exception before completing.",
            "files_changed": [],
            "verification_done": "none",
            "open_issues": [err_msg],
        }


async def run_wave_list(round_num: int, waves: list) -> list:
    all_results = []
    for w_idx, wave in enumerate(waves, start=1):
        wave_name = wave.get("wave_name") or f"Wave {w_idx}"
        tasks = wave.get("tasks") or []
        if not tasks:
            continue

        subwaves = split_into_conflict_free_subwaves(tasks)
        for s_idx, bucket in enumerate(subwaves, start=1):
            suffix = f" (Sub-wave {s_idx}/{len(subwaves)})" if len(subwaves) > 1 else ""
            tier_counts = {}
            for t in bucket:
                m = resolve_worker_model(t.get("tier", "flash"))
                tier_counts[m] = tier_counts.get(m, 0) + 1
            log(
                f"Dispatching {wave_name}{suffix}: {len(bucket)} parallel subagent(s) "
                f"tiers={tier_counts}"
            )
            batch_results = await parallel(
                bucket,
                lambda item, wn=wave_name: run_safe_worker(round_num, wn, item),
            )
            all_results.extend(batch_results)
    return all_results


async def run_global_verification(round_num: int, changed_files: list) -> dict:
    """
    Runs parallel read-only verification subagents:
      1. Build & Test Gatekeeper (`flash`)
      2. Requirements & Integration Auditor (`flash`)
      3. Cross-Platform (Mac/Windows) & Stub Inspector (`flash_lite`)
    """
    cmd_hint = (
        "\n".join(f"  - {c}" for c in VERIFICATION_COMMANDS)
        if VERIFICATION_COMMANDS
        else "  - Auto-detect and run the project's standard build, typecheck, and test suite."
    )
    reqs_block = "\n".join(f"  - {r}" for r in USER_REQUIREMENTS)
    ac_block = "\n".join(f"  - {a}" for a in ACCEPTANCE_CRITERIA)
    files_block = "\n".join(f"  - {f}" for f in changed_files[:80]) or "  - (Inspect workspace files)"

    async def run_gatekeeper():
        prompt = f"""[Round {round_num} | Global Build & Test Gatekeeper]
{OS_GUARDRAILS}
Workspace Root: {WORKSPACE_ROOT}

DO NOT edit application source files. Your sole job is to execute the build/typecheck/test verification commands and report objective results:
{cmd_hint}

Report `all_passed: true` ONLY if every build/test command actually ran and exited with code 0 (unless this is a pure documentation/design project with no executable code or tests). Include exact failing test names and compiler tracebacks in `raw_error_excerpt` if anything failed.
"""
        try:
            return await agent(
                prompt=prompt,
                schema=GATE_RESULT_SCHEMA,
                role=f"[R{round_num}][flash] Build & Test Gate",
                model="flash",
            )
        except Exception as exc:
            return {
                "all_passed": False,
                "commands_executed": [],
                "failure_summary": f"Gatekeeper exception: {exc}",
                "raw_error_excerpt": traceback.format_exc()[-1500:],
            }

    async def run_req_auditor():
        prompt = f"""[Round {round_num} | Global Requirements & Integration Auditor]
{OS_GUARDRAILS}
Workspace Root: {WORKSPACE_ROOT}

Read-only audit — DO NOT modify any files.
Inspect the repository and recently touched files:
{files_block}

Verify against:
1. USER REQUIREMENTS:
{reqs_block}

2. ARCHITECTURE CONTRACT:
{ARCHITECTURE_CONTRACT or '(Check cross-module imports, signatures, data flow, and edge cases.)'}

3. GLOBAL ACCEPTANCE CRITERIA:
{ac_block}

List every unmet requirement, cross-module signature mismatch, unhandled edge case, or stubbed/incomplete implementation (`TODO`, `FIXME`, `NotImplementedError`, dummy return values). Set `clean: true` ONLY if zero issues exist.
"""
        try:
            return await agent(
                prompt=prompt,
                schema=AUDIT_RESULT_SCHEMA,
                role=f"[R{round_num}][flash] Requirements & Integration Audit",
                model="flash",
            )
        except Exception as exc:
            return {
                "clean": False,
                "findings": [f"Requirements auditor exception: {exc}"],
                "missing_or_stubbed": [],
            }

    async def run_xplat_inspector():
        prompt = f"""[Round {round_num} | Cross-Platform (macOS + Windows) & Hygiene Inspector]
{OS_GUARDRAILS}
Workspace Root: {WORKSPACE_ROOT}

Read-only fast inspection — DO NOT modify any files.
Scan the modified/project files:
{files_block}

Check specifically for:
1. macOS & Windows incompatibilities (hardcoded `\\` or `C:\\` or `/tmp/...` paths, missing `encoding='utf-8'`, OS-specific shell calls without platform branching, case-colliding filenames).
2. Leftover syntax errors, broken imports, dead stubs, or missing entrypoint wiring.

Set `clean: true` ONLY if zero cross-platform or hygiene defects are found.
"""
        try:
            return await agent(
                prompt=prompt,
                schema=AUDIT_RESULT_SCHEMA,
                role=f"[R{round_num}][flash_lite] Mac/Win & Hygiene Check",
                model="flash_lite",
            )
        except Exception as exc:
            return {
                "clean": False,
                "findings": [f"Cross-platform inspector exception: {exc}"],
                "missing_or_stubbed": [],
            }

    checks = await parallel(
        [run_gatekeeper, run_req_auditor, run_xplat_inspector],
        lambda fn: fn(),
    )
    return {
        "build_test_gate": checks[0],
        "requirements_audit": checks[1],
        "cross_platform_audit": checks[2],
    }


# ---------------------------------------------------------------------------
# 6. Main Multi-Round Closed-Loop Execution
# ---------------------------------------------------------------------------

async def run_main_orchestration() -> None:
    architecture_contract_local = ARCHITECTURE_CONTRACT
    commander_standing_prompt = f"""You are the Chief System Architect & Orchestration Commander (running at maximum reasoning depth).
You NEVER write bulk implementation files directly during workflow evaluation turns — you lead, architect, audit global telemetry, and dispatch parallel worker waves.

TASK TITLE: {TASK_TITLE}
WORKSPACE ROOT: {WORKSPACE_ROOT}
{OS_GUARDRAILS}

USER REQUIREMENTS:
{json.dumps(USER_REQUIREMENTS, ensure_ascii=False, indent=2)}

GLOBAL ACCEPTANCE CRITERIA:
{json.dumps(ACCEPTANCE_CRITERIA, ensure_ascii=False, indent=2)}

ARCHITECTURE CONTRACT:
{architecture_contract_local or '(Design and enforce clean modular contracts with zero file-ownership collisions.)'}

SUBAGENT TIER ROUTING POLICY:
- Use `tier: "flash"` (1 tier weaker) for core modules, algorithms, stateful logic, cross-file integration fixes, and complex test suites.
- Use `tier: "flash_lite"` (2 tiers weaker) for scaffolding, DTOs/types/configs, test fixtures/mocks, documentation, and simple isolated helpers.
- ESCALATION RULE: If a `flash_lite` task failed or left defects in the prior round, escalate its replacement task to `flash`.
- DISJOINT OWNERSHIP RULE: Within the same wave, two tasks MUST NEVER share any file in `owned_files`. Put shared contract updates in an earlier wave than downstream consumers.
"""

    commander = agent(
        prompt=commander_standing_prompt,
        role="Chief Commander (Architect & Global Evaluator)",
        model=COMMANDER_MODEL,
    )

    current_waves = cfg.get("initial_waves") or []
    if not current_waves:
        phase("Round 1 - Commander Architecture & Sharding")
        log("No pre-built `initial_waves` supplied; requesting Round 1 blueprint & sharded waves from Commander...")
        init_plan = await commander(
            "Inspect the workspace (read-only) if needed, establish the modular architecture contract, and produce Round 1's parallel implementation `waves` covering all user requirements.",
            schema=INITIAL_PLAN_SCHEMA,
        )
        if not architecture_contract_local:
            architecture_contract_local = init_plan.get("architecture_summary", "")
        current_waves = init_plan.get("waves", [])
        log(f"Commander generated {len(current_waves)} wave(s) for Round 1.")

    rounds_history = []
    final_verdict = "ITERATE"
    final_score = 0

    for round_num in range(1, MAX_ROUNDS + 1):
        phase(f"Round {round_num}/{MAX_ROUNDS} - Parallel Implementation")
        worker_reports = await run_wave_list(round_num, current_waves)

        changed_set = []
        seen_files = set()
        for wr in worker_reports:
            for f in wr.get("files_changed", []):
                if f not in seen_files:
                    seen_files.add(f)
                    changed_set.append(f)

        blocked_workers = [w for w in worker_reports if w.get("status") != "completed"]
        log(
            f"Round {round_num} implementation finished: {len(worker_reports)} worker(s), "
            f"{len(changed_set)} file(s) touched, {len(blocked_workers)} non-completed worker(s)."
        )

        phase(f"Round {round_num}/{MAX_ROUNDS} - Global Telemetry & Verification")
        telemetry = await run_global_verification(round_num, changed_set)
        gate_ok = bool(telemetry["build_test_gate"].get("all_passed"))
        req_ok = bool(telemetry["requirements_audit"].get("clean"))
        xplat_ok = bool(telemetry["cross_platform_audit"].get("clean"))
        log(
            f"Round {round_num} telemetry: build_test_gate={gate_ok}, "
            f"requirements_clean={req_ok}, cross_platform_clean={xplat_ok}"
        )

        phase(f"Round {round_num}/{MAX_ROUNDS} - Commander Global Evaluation")
        eval_prompt = f"""Evaluate Global Performance after Round {round_num}/{MAX_ROUNDS}.

1. WORKER EXECUTION REPORTS:
{json.dumps(worker_reports, ensure_ascii=False, indent=2)}

2. GLOBAL TELEMETRY (BUILD/TEST GATE + REQUIREMENTS AUDIT + MAC/WIN AUDIT):
{json.dumps(telemetry, ensure_ascii=False, indent=2)}

STRICT EVALUATION RULES:
- Set `verdict: "PASS"` ONLY if:
  (a) `build_test_gate.all_passed` is true,
  (b) EVERY user requirement and global acceptance criterion is completely satisfied without stubs,
  (c) Cross-platform (macOS + Windows) checks have zero real defects, and
  (d) `global_score >= {PASS_SCORE_THRESHOLD}`.
- Otherwise, set `verdict: "ITERATE"` and construct `next_round_waves` (Round {round_num + 1}) with targeted, disjoint-file `flash` and `flash_lite` tasks that resolve EVERY remaining defect, test failure, integration mismatch, and requirement gap.
"""
        evaluation = await commander(eval_prompt, schema=COMMANDER_EVAL_SCHEMA)

        final_score = int(evaluation.get("global_score", 0))
        verdict = evaluation.get("verdict", "ITERATE")
        unmet = evaluation.get("unmet_or_partial_requirements", [])

        # Deterministic Python safety net against premature PASS
        if verdict == "PASS" and (not gate_ok or unmet or final_score < PASS_SCORE_THRESHOLD):
            log(
                f"[GATE OVERRIDE] Commander returned PASS, but hard checks failed "
                f"(gate_ok={gate_ok}, unmet={len(unmet)}, score={final_score}/{PASS_SCORE_THRESHOLD})."
            )
            verdict = "ITERATE"

        round_record = {
            "round": round_num,
            "workers_dispatched": len(worker_reports),
            "files_changed": changed_set,
            "blocked_workers": len(blocked_workers),
            "telemetry": telemetry,
            "global_score": final_score,
            "verdict": verdict,
            "unmet_or_partial_requirements": unmet,
            "global_diagnosis": evaluation.get("global_diagnosis", ""),
            "tokens_snapshot": safe_tokens_used(),
        }
        rounds_history.append(round_record)

        log(
            f"Round {round_num} Verdict: {verdict} | Global Score: {final_score}/100 | "
            f"Diagnosis: {evaluation.get('global_diagnosis', '')[:240]}"
        )

        if verdict == "PASS":
            final_verdict = "PASS"
            break

        if round_num < MAX_ROUNDS:
            next_waves = evaluation.get("next_round_waves") or []
            if not next_waves:
                log(f"Requesting explicit corrective wave plan for Round {round_num + 1}...")
                replan = await commander(
                    f"Hard gate checks remain open after Round {round_num}. Generate non-empty `waves` for Round {round_num + 1} to fix all build/test failures and unmet requirements.",
                    schema=INITIAL_PLAN_SCHEMA,
                )
                next_waves = replan.get("waves", [])
            if not next_waves:
                log("[STOP] Commander produced no further tasks; ending iteration loop.")
                break
            current_waves = next_waves

    del commander

    phase("Complete - Executive Summary")
    final_report = {
        "task_title": TASK_TITLE,
        "host_os": HOST_OS,
        "rounds_executed": len(rounds_history),
        "max_rounds": MAX_ROUNDS,
        "final_verdict": final_verdict,
        "final_global_score": final_score,
        "total_tokens": safe_tokens_used(),
        "rounds": rounds_history,
    }

    if REPORT_OUTPUT_PATH:
        out_path = Path(REPORT_OUTPUT_PATH)
        if not out_path.is_absolute():
            out_path = Path(WORKSPACE_ROOT) / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(final_report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        log(f"Saved full JSON execution report to: {out_path}")

    log(f"Final Verdict: {final_verdict} (Score: {final_score}/100 across {len(rounds_history)} round(s))")
    print(json.dumps(final_report, ensure_ascii=False, indent=2))


phase(f"Init - {TASK_TITLE}")
log(f"Host OS: {HOST_OS} | Workspace: {WORKSPACE_ROOT}")
log(f"Commander Model: {COMMANDER_MODEL} | Max Rounds: {MAX_ROUNDS} | Pass Threshold: {PASS_SCORE_THRESHOLD}")

if DRY_RUN:
    phase("Dry-Run Validation")
    preview_waves = []
    for w_idx, wave in enumerate(cfg.get("initial_waves") or [], start=1):
        w_name = wave.get("wave_name") or f"Wave {w_idx}"
        buckets = split_into_conflict_free_subwaves(wave.get("tasks") or [])
        preview_waves.append(
            {
                "wave_name": w_name,
                "subwaves": [
                    [
                        {
                            "id": t.get("id"),
                            "tier": resolve_worker_model(t.get("tier", "flash")),
                            "owned_files": t.get("owned_files", []),
                        }
                        for t in b
                    ]
                    for b in buckets
                ],
            }
        )
    dry_summary = {
        "dry_run": True,
        "host_os": HOST_OS,
        "workspace": WORKSPACE_ROOT,
        "task_title": TASK_TITLE,
        "commander_model": COMMANDER_MODEL,
        "max_rounds": MAX_ROUNDS,
        "waves_preview": preview_waves,
    }
    log(f"Dry-run validated {len(preview_waves)} wave(s) successfully.")
    print(json.dumps(dry_summary, ensure_ascii=False, indent=2))
else:
    await run_main_orchestration()
