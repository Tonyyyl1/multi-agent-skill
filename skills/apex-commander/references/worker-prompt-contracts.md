# Subagent Tier Routing, Prompt Contracts & Fallback Mode

## 1. Three-Tier Model Hierarchy

| Tier | Role Title | `model` Value | Responsibilities | Never Use For |
| :--- | :--- | :--- | :--- | :--- |
| **L0 (Commander)** | Chief Architect & Global Evaluator | `"inherit"` (when main session is Flagship High) or `"pro"` | Problem framing, system architecture, interface contract freeze, conflict-free task DAG sharding, global multi-criteria scoring, iterative replanning | Writing boilerplate, repetitive CRUD, formatting, mechanical multi-file edits |
| **L1 (弱一级)** | Core Implementation Builder | `"flash"` | Core algorithms, domain/business logic, complex stateful modules, cross-file integration glue, non-trivial bug root-causing, comprehensive test suites | Top-level architectural redesign without Commander approval |
| **L2 (弱两级)** | High-Concurrency Rapid Worker | `"flash_lite"` | Parallel repo reconnaissance, scaffolding, DTOs/types/configs, mocks/fixtures, docs/comments, static hygiene & cross-platform scans | Subtle concurrency algorithms or ambiguous cross-module coupling |

### Automatic Tier Escalation Rule
- If an **L2 (`flash_lite`)** task fails, times out, or introduces subtle bugs in Round `r`, escalate its corrective task in Round `r+1` to **L1 (`flash`)**.
- If an **L1 (`flash`)** task fails twice on the same algorithmic or architectural bottleneck, **L0 (Commander)** writes out the exact algorithm steps / pseudocode invariants inside the task's `instructions` before dispatching L1 again.

---

## 2. Conflict-Free Parallel Sharding Rules

Parallel subagents achieve near-linear speedup **only** when write collisions are eliminated by design:

1. **Freeze Shared Contracts in Wave 1**:
   - Shared headers, AST/DTO definitions, database schemas, protobuf/OpenAPI specs, and barrel exports (`index.ts`, `__init__.py`, `mod.rs`) belong in **Wave 1** before parallel module workers start in **Wave 2**.
2. **Disjoint `owned_files` Within Every Wave**:
   - Every task specifies `owned_files` (exclusive create/edit permission) and `readonly_files` (contracts it reads and obeys).
   - Both **macOS (APFS)** and **Windows (NTFS)** are case-insensitive by default: treat `src/User.ts` and `src/user.ts` as the same file!
3. **Defer Lock-Contending Global Commands to the Gatekeeper**:
   - Parallel workers in `workspace="inherit"` must **not** simultaneously run repo-wide lock-contending commands (`cargo build`, `gradle build`, `sbt test`, `npm ci`, `git commit`).
   - Workers validate syntax/imports locally; the **Global Build & Test Gatekeeper** runs full build/test commands once after the parallel wave finishes (or workers use `workspace="share"` / `"branch"` when isolated concurrent compilation is essential).

---

## 3. Mode B: Interactive Multi-Subagent Fallback (`invoke_subagent`)

Use **Mode A (`run_workflow` + `scripts/auto_orchestrator.py`)** by default because it automates multi-round evaluation without manual turn handoffs.

Switch to **Mode B (Direct `invoke_subagent` Waves from Main Commander)** ONLY when:
- A step requires `BypassSandbox: true` (e.g., network package installation like `pnpm install`, `cargo fetch`, Docker/port binding) — remember `run_workflow` denies unapproved interactive prompts; OR
- A round requires live UI verification via the `browser` subagent (`Model="flash"`); OR
- Mid-round user product decisions are needed.

### Hybrid Best Practice (Recommended for Network/Install Projects)
1. **Preflight in Main Agent**: Run dependency installation / codegen / sandbox-bypass setup once in the Main Agent (`run_command`).
2. **Automated Core Rounds in `run_workflow`**: Run `scripts/auto_orchestrator.py` for multi-round parallel `flash` + `flash_lite` coding, testing, and global iteration.
3. **Optional Post-Workflow UI Check**: Delegate visual verification to `invoke_subagent(TypeName="browser", Model="flash", ...)` if a web UI is involved.

### Mode B Direct Dispatch Pattern (When Not Using `run_workflow`)
In a single turn, the Main Commander (L0) calls `invoke_subagent` multiple times in parallel:
- Core module tasks -> `invoke_subagent(TypeName="self", Model="flash", Role="...", Prompt="...")`
- Lightweight/boilerplate/scout tasks -> `invoke_subagent(TypeName="self", Model="flash_lite", Role="...", Prompt="...")`
- Read-only research scouts -> `invoke_subagent(TypeName="research", Model="flash_lite", Role="...", Prompt="...")`

Then **end your turn immediately** (do not poll!). When all subagents return, run the Global Acceptance Rubric in your own thinking, run build/test verification, and if global score < threshold, immediately dispatch Round `r+1` subagents!
