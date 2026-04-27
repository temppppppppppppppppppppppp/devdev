# Issue #56 Ensemble Genre Alignment 10-Terminal Parallel Investigation Order

Date: 2026-04-27
Status: final - investigation order
GitHub Issue: `#56 [Ensemble] Genre-align Stage3/Stage4 action and tension strategies`
Canonical Path: `docs/2026-04-27/issue-56-ensemble-genre-alignment-10terminal-order.md`
Track: system order
Mode: survey / audit / order-pack only
Baseline Commit: `a3d826978d530ab61d3765e5e095890fa6533ea7`
Baseline Dirty Summary: existing untracked directories observed and not touched: `docs/2026-04-27/security-parallel-investigation/`, `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/`

## Purpose

Create a 10-terminal parallel investigation order for Issue #56. The investigation target is not the tactical vehicle/intrusion guard itself. The target is the deeper genre-alignment problem: in investment / business-power works, Stage3 and Stage4 ensemble strategy terms such as `action`, `tension`, `escalation`, and `conflict` must mean business pressure, institutional stakes, relationship risk, negotiation leverage, reputational exposure, and deal timing rather than physical chase, violence, or thriller intrusion.

This document is an order pack only. Terminals must not edit code, docs, DB, or GitHub issues unless a later operator explicitly opens an implementation wave.

## Source Evidence

- `docs/2026-04-27/gcp-iam-5arc-live-run-handoff-current.md:119-120` says the vehicle guard is still firewall-style mitigation and names the deeper root improvement: genre-align Stage3 and Stage4 ensemble strategies so investment / business-power works do not interpret action or tension as physical chase, violence, or thriller intrusion.
- `docs/2026-04-27/gcp-iam-5arc-cleanrun-prep-context.md:18` records the current target as `genre=investment`.
- `modules/domain/agents/blueprint_ensemble.py:61` defines `action_focused`.
- `modules/domain/agents/blueprint_ensemble.py:317-318` maps tension/action prose to suspense/action-climax language.
- `tests/test_blueprint_ensemble_generate_ensemble.py:700+` covers tactical action-focused guard behavior but does not prove a full genre strategy contract.
- `docs/2026-04-27/gcp-iam-5arc-live-run-handoff-current.md:80-93` records current Stage4 `POST_SELECT_CONFLICT` recovery rows.
- Issue #56 is a GitHub visibility mirror; repo docs and live evidence remain SSOT.

## Global Rules For All 10 Terminals

- Read-only only. Do not modify files, run formatters, write temp docs, create commits, or update GitHub.
- Use UTF-8 reads. If console rendering looks broken, do not claim corruption from terminal output alone.
- Search with `rg` first.
- Keep findings bounded to inspected evidence.
- Distinguish evidence from inference.
- Do not treat Python validators or heuristics as the final narrative judge. Director remains final quality authority.
- Do not recommend removing the current tactical guard until a genre-aligned contract has targeted or live proof.
- Each terminal returns a compact report with:
  - `Finding Summary`
  - `Evidence`
  - `Risk / Gap`
  - `Suggested Contract Or Test`
  - `Implementation Owner Surface`
  - `Open Questions`

## Parallel Terminal Map

| Terminal | Lane | Primary Question |
| --- | --- | --- |
| T01 | Stage3 blueprint ensemble strategy surface | Where does Stage3 currently define action/tension strategy meaning, and what exactly biases toward physical action? |
| T02 | Stage4 manuscript/director ensemble surface | Where does Stage4 interpret action/tension/continuity/firewall feedback, and can genre semantics be preserved through manuscript selection? |
| T03 | Genre/domain semantics | What should investment/business-power action and tension mean as a reusable contract? |
| T04 | Prompt/config/style/work_guard ingress | Which prompt/config/material surfaces already carry genre identity, and where is that signal dropped or weakened? |
| T05 | Tactical guard vs root fix boundary | What current guard blocks vehicle/intrusion symptoms, and why is it insufficient as a root fix? |
| T06 | Live-run evidence and failure taxonomy | Which 2026-04-27 run artifacts prove the symptom shape and recovery pattern? |
| T07 | Regression test design | What focused tests should pin genre-aligned action/tension without overfitting to one project? |
| T08 | Benchmark / metric design | How will we know the root fix improved behavior and did not merely hide rejects? |
| T09 | Authority and governance audit | What guardrails prevent genre alignment from becoming Python quality judgment or fact rewriting? |
| T10 | Synthesis / implementation readiness | What minimal implementation tranches should follow if the investigation confirms the contract? |

## Terminal Orders

### T01 - Stage3 Blueprint Ensemble Strategy Surface

Read targets:

- `modules/domain/agents/blueprint_ensemble.py`
- `tests/test_blueprint_ensemble_generate_ensemble.py`
- `modules/core/scene_obligation_heuristics.py`
- Issue #56 evidence lines from `docs/2026-04-27/gcp-iam-5arc-live-run-handoff-current.md`

Questions:

- Where are strategy names, descriptions, tone directives, tension ranges, scene-type templates, or retry directives defined?
- Which exact strings or defaults imply chase, combat, suspense, violence, physical crisis, or thriller intrusion?
- Does Stage3 receive genre/family/material identity strongly enough to remap strategy terms?
- What is the narrowest Stage3 contract change that would redefine action/tension by genre?

Return:

- A table of Stage3 action/tension surfaces with file path and line.
- Suggested `investment/business_power` semantic replacements.
- Tests needed at Stage3 only.

### T02 - Stage4 Manuscript / Director Ensemble Surface

Read targets:

- `modules/domain/agents/director_ensemble.py`
- `modules/core/stage4_outcome_runtime.py`
- `modules/core/stage4_orchestrator.py` if present
- `tests/test_stage4_orchestrator.py`
- `tests/test_tf29_open_review.py`

Questions:

- Where do Stage4 candidate strategy names, action items, firewall reasons, or fix packs preserve or distort action/tension semantics?
- Does Stage4 know the genre is `investment` at the point of candidate selection and post-select conflict handling?
- Can a Stage3 genre-aligned strategy survive into Stage4 selection and retry?
- Which Stage4 tests should pin "business action" versus "physical action" distinction?

Return:

- Stage4 surfaces that consume or rewrite action/tension language.
- Risk list for `PASS_WITH_FIX`, firewall, and action_items paths.
- Proposed Stage4 regression tests.

### T03 - Genre / Domain Semantics Contract

Read targets:

- `config/style_references/investment/style_guide.json`
- `projects/01_골든카나리아/stage0_output/style_guide.json` if present
- `projects/01_골든카나리아/config/work_guard.yaml` if present
- `docs/2026-04-27/gcp-iam-5arc-cleanrun-prep-context.md`
- Any material-side or work_guard docs only if directly referenced by the above files

Questions:

- What concrete investment/business-power conflict vocabulary already exists?
- What should `action`, `tension`, `escalation`, and `stakes` mean for this family?
- Which terms should be banned or heavily constrained for this genre unless explicitly material-supported?
- Is "business-power" an existing category in config/docs, or an issue-level working term?

Return:

- A reusable genre semantics mini-contract.
- Positive examples and forbidden examples.
- Any uncertainty about source authority.

### T04 - Prompt / Config / Material Identity Ingress

Read targets:

- `modules/core/models_config.py`
- `modules/core/llm_router.py`
- prompt loader / prompt contract code found by `rg "prompt_contract|prompt_loader|ENSEMBLE|strategy"`
- `modules/api/bridge_server.py` only for prompt contract references
- Stage0 handoff/style/work_guard ingress code found by `rg "work_guard|style_guide|genre|selected_genre"`

Questions:

- Where does genre identity enter Stage3 and Stage4 prompts?
- Is style/work_guard genre identity injected before strategy selection or only after candidate generation?
- Are there hidden default prompts that still frame action as physical spectacle?
- What existing prompt contract should carry the genre semantics contract?

Return:

- Prompt/config ingress map.
- Missing or weak propagation points.
- Suggested prompt contract owner.

### T05 - Tactical Guard vs Root Fix Boundary

Read targets:

- PR #54 summary if available through GitHub or local merge commit context
- `docs/2026-04-27/gcp-iam-5arc-live-run-handoff-current.md`
- Code/tests mentioning vehicle, intrusion, physical, chase, guard, firewall, and tactical
- `tests/test_blueprint_ensemble_generate_ensemble.py`
- `tests/test_stage4_orchestrator.py`

Questions:

- What exactly did the tactical guard prevent?
- Which symptom classes remain possible because the root semantics are still wrong?
- Which guard behavior must remain until replacement proof exists?
- Where could guard output accidentally mask rather than solve the root cause?

Return:

- Tactical guard inventory.
- "Do not remove yet" conditions.
- Root-fix acceptance criteria.

### T06 - Live-Run Evidence And Failure Taxonomy

Read targets:

- `docs/2026-04-27/gcp-iam-5arc-live-run-handoff-current.md`
- `docs/2026-04-27/auto-frontier-lag-5arc-runtime-analysis-ssot.md`
- `projects/01_골든카나리아/logs/` summaries only; avoid dumping huge logs
- `projects/01_골든카나리아/project_data.db` read-only only if needed
- `docs/2026-04-26/frontier-lag-5arc-post-run-merge-audit.md`

Questions:

- Which reject/failure categories are plausibly tied to action/tension genre drift?
- Did the current run show recovery after guard insertion, or merely a different bottleneck?
- Which evidence is terminal, provisional, or stopped-run only?
- What DB/log queries would be needed for a later benchmark issue?

Return:

- Evidence table by episode / attempt / category.
- Clear provisional-vs-terminal marking.
- Candidate metrics for T08.

### T07 - Regression Test Design

Read targets:

- `tests/test_blueprint_ensemble_generate_ensemble.py`
- `tests/test_stage4_orchestrator.py`
- `tests/test_viewpoint_primary_external_policy.py`
- `tests/test_work_guard.py`
- `tests/test_unified_blueprint_validator_lane_c.py`

Questions:

- What new tests would fail on current semantics but pass after a genre-aligned contract?
- Which tests belong to Stage3, Stage4, prompt/config, and live-run analysis?
- How can tests avoid hardcoding one project while still using investment/business-power examples?
- What small fake contexts can prove action/tension remapping without live LLM calls?

Return:

- Proposed test list with file owners.
- Minimal fixtures.
- Risk of brittle tests.

### T08 - Benchmark / Metric Design

Read targets:

- `benchmarks/README.md`
- `benchmarks/benchmark_index.csv`
- Issues #62, #63, #64, #65 if available
- `docs/2026-04-27/gcp-iam-5arc-live-run-handoff-current.md`

Questions:

- Which metrics show that genre alignment improved behavior?
- Which metrics could be misleading because the run was stopped/provisional?
- How should action/tension misfire be counted: reject category, manual annotation, or semantic artifact audit?
- What minimum benchmark packet should accompany any implementation PR?

Return:

- Benchmark acceptance criteria.
- Required evidence fields.
- Suggested before/after comparison windows.

### T09 - Authority And Governance Audit

Read targets:

- `AGENTS.md`
- `docs/2026-04-26/authority-alignment-execution-ssot.md`
- `docs/2026-04-26/current-pipeline-truth-locks-execution-ssot.md`
- `docs/2026-04-26/frontier-lag-clean-5arc-stabilization-execution-ssot.md`
- `modules/core/advisory_authority.py`

Questions:

- How can genre-aligned routing remain advisory/contractual without Python judging narrative quality?
- Which fields must be Director-owned versus runtime-route-owned?
- Could a genre guard become another hidden veto or factsheet rewrite?
- What authority labels should accompany any new advisory or retry payload?

Return:

- Authority risk list.
- Required payload labels / provenance fields.
- Governance acceptance gates for implementation.

### T10 - Synthesis / Implementation Readiness

Read targets:

- All terminal returns when available
- Issue #56
- Issues #57, #58, #62, #63, #64 if available
- This order document

Questions:

- What is the smallest safe implementation tranche?
- Which findings are confirmed, inferred, or blocked on missing evidence?
- Which tests should land before prompt/config/code changes?
- What should remain out of scope for the first PR?

Return:

- One synthesis memo with:
  - confirmed root-cause surfaces
  - proposed implementation tranches
  - test plan
  - benchmark plan
  - authority guardrails
  - open questions

## Copy-Paste Terminal Prompts

### Prompt T01

You are Terminal T01 for Issue #56. Work read-only in `c:\Users\wjjo\Desktop\글도비`. Investigate Stage3 blueprint ensemble strategy surfaces. Do not edit files or create issues. Read `modules/domain/agents/blueprint_ensemble.py`, `tests/test_blueprint_ensemble_generate_ensemble.py`, `modules/core/scene_obligation_heuristics.py`, and Issue #56 evidence in `docs/2026-04-27/gcp-iam-5arc-live-run-handoff-current.md:119-120`. Find every Stage3 place where `action`, `tension`, `action_focused`, scene type, strategy directive, or retry text may bias investment/business-power works toward physical chase, violence, or thriller intrusion. Return a compact report with evidence paths/lines, exact risky language, proposed investment/business-power semantic replacement, and Stage3-only tests. Mark evidence vs inference.

### Prompt T02

You are Terminal T02 for Issue #56. Work read-only in `c:\Users\wjjo\Desktop\글도비`. Investigate Stage4 manuscript/director ensemble surfaces. Do not edit files or create issues. Read `modules/domain/agents/director_ensemble.py`, `modules/core/stage4_outcome_runtime.py`, Stage4 orchestrator code if present, `tests/test_stage4_orchestrator.py`, and `tests/test_tf29_open_review.py`. Determine where Stage4 consumes, preserves, rewrites, or distorts `action`, `tension`, `action_items`, firewall reasons, fix packs, and genre identity. Return evidence paths/lines, risks around `PASS_WITH_FIX`/firewall/action_items, whether genre=`investment` is available at decision time, and proposed Stage4 regression tests.

### Prompt T03

You are Terminal T03 for Issue #56. Work read-only in `c:\Users\wjjo\Desktop\글도비`. Investigate the investment/business-power genre semantics contract. Do not edit files or create issues. Read `config/style_references/investment/style_guide.json`, `projects/01_골든카나리아/stage0_output/style_guide.json` if present, `projects/01_골든카나리아/config/work_guard.yaml` if present, and `docs/2026-04-27/gcp-iam-5arc-cleanrun-prep-context.md`. Build a compact mini-contract defining what `action`, `tension`, `escalation`, `conflict`, and `stakes` should mean for investment/business-power works. Include positive examples, forbidden examples, source evidence, and uncertainty about whether `business-power` is canonical or issue-level shorthand.

### Prompt T04

You are Terminal T04 for Issue #56. Work read-only in `c:\Users\wjjo\Desktop\글도비`. Investigate prompt/config/material identity ingress. Do not edit files or create issues. Use `rg` for `prompt_contract`, `prompt_loader`, `ENSEMBLE`, `strategy`, `work_guard`, `style_guide`, `genre`, and `selected_genre`. Read only relevant files such as `modules/core/models_config.py`, `modules/core/llm_router.py`, prompt loader code, `modules/api/bridge_server.py` references, and Stage0 handoff/style/work_guard ingress code. Return a map of where genre identity enters Stage3/Stage4 prompts, where it is weak or missing, and which prompt/config contract should carry genre-aligned action/tension semantics.

### Prompt T05

You are Terminal T05 for Issue #56. Work read-only in `c:\Users\wjjo\Desktop\글도비`. Investigate tactical guard versus root-fix boundary. Do not edit files or create issues. Read the local PR #54 context if available, `docs/2026-04-27/gcp-iam-5arc-live-run-handoff-current.md`, and code/tests found by searching vehicle, intrusion, physical, chase, guard, firewall, tactical, action_focused, and POST_SELECT_CONFLICT. Explain what the current tactical guard prevents, what it does not solve, what must not be removed until replacement proof exists, and where guard output could mask rather than fix root semantics. Return evidence paths/lines and acceptance criteria for replacing guard reliance.

### Prompt T06

You are Terminal T06 for Issue #56. Work read-only in `c:\Users\wjjo\Desktop\글도비`. Investigate live-run evidence and failure taxonomy. Do not edit files or create issues. Read `docs/2026-04-27/gcp-iam-5arc-live-run-handoff-current.md`, `docs/2026-04-27/auto-frontier-lag-5arc-runtime-analysis-ssot.md`, `docs/2026-04-26/frontier-lag-5arc-post-run-merge-audit.md`, and only compact summaries from `projects/01_골든카나리아/logs/` or read-only DB queries if needed. Identify which failure/reject categories are plausibly linked to genre drift, which evidence is provisional because the run was stopped, and what DB/log metrics should feed later benchmarks. Return an episode/attempt/category evidence table and mark evidence vs inference.

### Prompt T07

You are Terminal T07 for Issue #56. Work read-only in `c:\Users\wjjo\Desktop\글도비`. Investigate regression test design. Do not edit files or create issues. Read `tests/test_blueprint_ensemble_generate_ensemble.py`, `tests/test_stage4_orchestrator.py`, `tests/test_viewpoint_primary_external_policy.py`, `tests/test_work_guard.py`, and `tests/test_unified_blueprint_validator_lane_c.py`. Propose tests that would fail under physical-action-biased semantics and pass after investment/business-power genre alignment. Separate Stage3, Stage4, prompt/config, and analysis tests. Prefer fake contexts and deterministic tests over live LLM calls. Return file owners, fixture sketches, expected assertions, and brittleness risks.

### Prompt T08

You are Terminal T08 for Issue #56. Work read-only in `c:\Users\wjjo\Desktop\글도비`. Investigate benchmark and metric design. Do not edit files or create issues. Read `benchmarks/README.md`, `benchmarks/benchmark_index.csv`, Issues #62-#65 if accessible, and `docs/2026-04-27/gcp-iam-5arc-live-run-handoff-current.md`. Define how to measure whether genre alignment improved behavior: reject rates, attempt counts, POST_SELECT_CONFLICT rate, physical-action misfire annotations, runtime/cost/token changes, and before/after windows. Mark metrics that are unsafe because the run is stopped/provisional. Return benchmark acceptance criteria and required evidence fields.

### Prompt T09

You are Terminal T09 for Issue #56. Work read-only in `c:\Users\wjjo\Desktop\글도비`. Investigate authority/governance risks. Do not edit files or create issues. Read `AGENTS.md`, `docs/2026-04-26/authority-alignment-execution-ssot.md`, `docs/2026-04-26/current-pipeline-truth-locks-execution-ssot.md`, `docs/2026-04-26/frontier-lag-clean-5arc-stabilization-execution-ssot.md`, and `modules/core/advisory_authority.py`. Determine how genre-aligned routing can remain a contract/advisory surface without Python becoming narrative quality judge or factsheet owner. Return required authority labels, provenance fields, veto boundaries, and implementation gates.

### Prompt T10

You are Terminal T10 for Issue #56. Work read-only in `c:\Users\wjjo\Desktop\글도비`. You are the synthesis lane. Do not edit files or create issues. After T01-T09 reports are available, synthesize them against Issue #56 and this order document. Produce one compact implementation-readiness memo with confirmed root-cause surfaces, inferred-only risks, blocked/missing evidence, minimal safe implementation tranches, test plan, benchmark plan, authority guardrails, and out-of-scope items for the first PR. Do not invent evidence; cite terminal reports and repo paths.

## Synthesis Protocol

1. Run T01-T09 in parallel.
2. Do not let T10 start final synthesis until at least T01, T02, T03, T07, and T09 return.
3. If any terminal finds a direct contradiction with Issue #56, T10 must list it as `CONTRADICTION` rather than smoothing it away.
4. If findings are split between prompt-only and code-contract changes, prefer the smallest testable tranche.
5. Do not promote this order pack into implementation authority without a new execution SSOT or explicit operator instruction.

## 3-Pass Save Audit

Pass 1 - Structure and scope: PASS. The document is an investigation order pack, not an execution SSOT. It names Issue #56, source evidence, global rules, 10 terminal lanes, copy-paste prompts, and synthesis protocol.

Pass 2 - Evidence and consistency: PASS. The order is based on Issue #56 and local evidence lines from 2026-04-27 handoff/prep docs plus relevant Stage3/Stage4 code/test surfaces. It does not claim implementation readiness or final root-cause proof.

Pass 3 - Actionability and guardrails: PASS. Each terminal has bounded read targets, questions, and return format. Read-only and Director-authority guardrails are explicit.

Estimated confidence: 96%.
