# Desktop Style Reference Major LLM Propagation Deep Survey

- Date: 2026-03-16
- Track: system
- Mode: deep survey only
- Baseline Commit: `5a0177666e6877070d726d983d3c3e1d03e812d2`
- Baseline Dirty Summary: existing tracked modifications in desktop/runtime/style files and tests; existing untracked docs under `docs/2026-03-16/`, `docs/temp/`, DB copies, and temp notes; this survey added documentation only
- Resume Commit: `5a0177666e6877070d726d983d3c3e1d03e812d2`
- Resume Drift Summary: no code patch during this survey; only new survey docs added
- Source Evidence: `docs/2026-03-16/desktop-style-reference-major-llm-propagation-deep-survey-evidence.txt`

## Findings

### High — Desktop Stage 0 style analysis does reach major downstream LLM generation paths, but not uniformly

The desktop click path for `Stage 0 -> 스타일 레퍼런스 분석` is real, durable, and reaches at least two major generation corridors:

1. `Stage 3` blueprint generation, via compact style-guide advisory prepended to `semantic_context`
2. `Stage 4` Chief Writer generation, via full `style_guide` prompt text plus `reference_excerpt`

This is not hypothetical. The desktop frontend emits `stage0_style_cache_mode`, `ProcessRunner` preloads the style-analysis confirmation and cache choice, Stage 0 persists the result into both project-local `stage0_output/style_guide.json` and DB `anchors.style_guide`, and downstream orchestrators load that state back into major generation prompts.

Concrete code path:

- Desktop run trigger:
  - `geuldobi-desktop/src/index.html:2846`
  - `geuldobi-desktop/src/index.html:2855`
  - `geuldobi-desktop/src/index.html:6930`
  - `modules/api/process_runner.py:682`
  - `modules/api/process_runner.py:726`
- Persistence:
  - `modules/core/stage0/__init__.py:637`
  - `modules/core/stage0/__init__.py:762`
  - `modules/core/stage01_helpers.py:585`
  - `modules/core/stage01_helpers.py:590`
- Stage 3 propagation:
  - `modules/core/project_support.py:184`
  - `modules/core/stage3_orchestrator.py:221`
  - `modules/core/stage3_orchestrator.py:1202`
  - `modules/core/stage3_orchestrator.py:1309`
- Stage 4 propagation:
  - `modules/core/stage4_orchestrator.py:1578`
  - `modules/core/stage4_orchestrator.py:1599`
  - `modules/core/stage4_context_builder.py:2661`
  - `modules/core/stage4_interview_round.py:1334`
  - `modules/domain/agents/chief_writer.py:289`
  - `modules/domain/agents/chief_writer_context.py:471`
  - `modules/domain/agents/chief_writer_prompts.py:164`

Concrete live evidence:

- `projects/00/logs/session_20260316_164527.log:144`
  - `StyleGuide DB 저장 완료 (anchor: style_guide)`
- `projects/00/logs/session_20260316_164607.log:792`
  - `저장된 스타일 가이드 로드됨 (톤: 진지, 시점: 혼합)`
- `projects/00/logs/session_20260316_164607.log:533`
  - Stage 3 summary includes `primary_pov`, `external_pov_insert_policy`, `style_guide_extracted_pov`, `effective_pov`
- `projects/00/logs/session_20260316_164607.log:1321`
  - Stage 4 summary includes the same POV-style contract fields

### High — Stage 4 Chief Writer receives the strongest form of propagation: full StyleGuide prompt text and reference excerpt

The richest propagation target is not the Director. It is the Chief Writer path.

`Stage4Orchestrator` loads the saved style-guide anchor, resolves POV overrides, serializes it with `to_prompt()`, carries that string in the session config and round context, and then hands it into `ChiefWriter.generate_ensemble(...)`. The Chief Writer context builder injects:

- the full `style_guide`
- the `reference_excerpt_section`

into the main manuscript-generation prompt template.

This means the desktop-produced style reference is not merely metadata. It becomes explicit prompt payload for the manuscript-writing LLM.

Direct evidence:

- load and session carry:
  - `modules/core/stage4_orchestrator.py:1581`
  - `modules/core/stage4_orchestrator.py:1599`
  - `modules/core/stage4_orchestrator.py:1645`
- round propagation:
  - `modules/core/stage4_context_builder.py:2698`
  - `modules/core/stage4_interview_round.py:1380`
  - `modules/core/stage4_interview_round.py:1546`
- prompt assembly:
  - `modules/domain/agents/chief_writer_context.py:471`
  - `modules/domain/agents/chief_writer_context.py:499`
  - `modules/domain/agents/chief_writer_prompts.py:164`
  - `modules/domain/agents/chief_writer_prompts.py:167`

Patch and retry flows also preserve the style guide:

- `modules/domain/agents/chief_writer.py:1228`
- `modules/domain/agents/chief_writer.py:1412`
- `modules/domain/agents/chief_writer.py:1621`
- `modules/core/stage4_interview_round.py:3090`
- `modules/core/stage4_interview_round.py:3818`

### Medium — Stage 3 blueprint generation also receives style-reference content, but in compact advisory form

`Stage 3` does not inject the full `StyleGuide.to_prompt()` string. Instead it builds a compact summary through `build_style_guide_summary(...)` and prepends that summary into `_bp_semantic_ctx`, which is then passed to `three_phase_bp.generate(...)` alongside the `director` agent.

This means the style reference does reach Stage 3 major LLM work, but as compressed advisory context rather than full DNA prompt text.

Direct code evidence:

- `modules/core/project_support.py:184`
- `modules/core/stage3_orchestrator.py:221`
- `modules/core/stage3_orchestrator.py:1202`
- `modules/core/stage3_orchestrator.py:1322`

Live evidence:

- `projects/00/logs/session_20260316_164607.log:533`
- `projects/00/logs/session_20260316_164607.log:646`
- `projects/00/logs/session_20260316_164607.log:764`

These logs show that the Stage 3 runtime carried the style-derived POV contract through actual episode blueprint runs after a desktop style-analysis run.

### Medium — Stage 4 Director review does not directly receive the full style guide

This is the main negative finding.

The Stage 4 Director review call `select_and_judge_ensemble(...)` receives:

- `mandatory_context`
- `prev_manuscripts_text`
- `story_context`

but not a `style_guide` argument.

The only style-adjacent direct injection observed in the Director review path is `MasterBible.protagonist_config` POV and external POV policy, not the full style-guide prompt or reference excerpt.

Direct code evidence:

- POV/policy advisory only:
  - `modules/core/stage4_interview_round.py:1744`
  - `modules/core/stage4_interview_round.py:1752`
- Director call without `style_guide`:
  - `modules/core/stage4_interview_round.py:1958`
  - `modules/core/stage4_interview_round.py:3184`

Implication:

- If the question is “does the desktop style reference reach the Stage 4 Director prompt directly?” the answer is currently **no**.
- If the question is “does the Director see downstream style consequences at all?” the answer is **indirectly yes**, through manuscripts and POV/policy metadata, but not through full direct style-guide prompt injection.

### Medium — Stage 2 contains a style-guide summary builder, but it is not proven active in the current generation path

There is real Stage 2 code for style-guide summary injection:

- `modules/core/stage2_preflight.py:337`
- `modules/core/stage2_preflight.py:808`

However, the helper containing that assembly is `_preflight_arc_analysis(...)`, and repo-wide search found no call site for that function. The active visible Stage 2 generation path calls `four_phase.generate(...)` with `vector_context`, `director_feedback`, `director`, and other inputs, but no visible `style_guide` or `enhanced_context` parameter.

Direct code evidence:

- style summary helper:
  - `modules/core/stage2_preflight.py:337`
  - `modules/core/stage2_preflight.py:808`
- no observed call site:
  - repo-wide search for `_preflight_arc_analysis(`
- active visible generation call:
  - `modules/core/stage2_preflight.py:1341`
  - `modules/core/stage2_preflight.py:1355`

Implication:

- We cannot honestly claim that desktop style reference is reaching the active Stage 2 FourPhase generation LLM path.
- The current evidence supports a stronger statement: the Stage 2 style-guide injection code exists, but is not proven live in the present runtime.

### Low — Stage 4 Python validators do not receive the style guide directly

The manuscript, consistency, blocking, and continuity validators operate on manuscripts plus validation contexts. No direct `style_guide` parameter is passed into those validator calls.

Direct code evidence:

- `modules/core/stage4_interview_round.py:2496`
- `modules/core/stage4_interview_round.py:2512`
- `modules/core/stage4_interview_round.py:2543`
- `modules/core/stage4_interview_round.py:2583`

This matters because some observed downstream style contract fields in logs come from orchestration and summary layers, not from validator prompts.

## Propagation Matrix

| Target | 전달 여부 | 형태 | 근거 |
| --- | --- | --- | --- |
| Desktop Stage 0 extractor | Yes | cache choice + analysis run | `index.html`, `process_runner.py`, Stage 0 session log |
| Project durable state | Yes | workspace cache + project-local file + DB anchor | cache JSON, `stage0_output/style_guide.json`, `anchors.style_guide` |
| Stage 2 FourPhase/Analyst | Not proven active | dormant summary helper only | `stage2_preflight.py` helper exists, but no proven active call path |
| Stage 3 blueprint generator | Yes | compact summary in `semantic_context` | `stage3_orchestrator.py:1202`, `:1322` |
| Stage 3 Director inside BP flow | Yes, indirect via `semantic_context` | compact summary | same call path as above |
| Stage 4 Chief Writer | Yes | full `style_guide` + `reference_excerpt` | `stage4_orchestrator.py`, `chief_writer_context.py`, `chief_writer_prompts.py` |
| Stage 4 Director review | No direct full style guide | POV/policy only via Bible | `stage4_interview_round.py:1744`, `:1958` |
| Stage 4 validators | No direct full style guide | manuscript/context only | `stage4_interview_round.py:2496-2583` |

## Open Questions

1. `Stage 2` style-guide helper deadness is strongly suggested but not proven by live runtime tracing. The current conclusion is “not proven active,” not “guaranteed dead.”
2. `Stage 3` semantic-context injection is proven in code and strongly supported by runtime summaries, but the exact prompt body inside `three_phase_bp` was not re-opened in this survey because the injection boundary was already explicit at the orchestrator call site.
3. `Stage 4 Director review` may still infer style from manuscripts produced by the Chief Writer. That is materially different from direct style-guide injection and should not be conflated.

## Conclusion

The answer to the user’s question is:

- **Yes**, the desktop-produced style reference really does reach major downstream LLM generation paths.
- The strongest confirmed propagation is:
  - `Desktop Stage 0 -> DB/file persistence -> Stage 3 semantic_context -> Stage 4 Chief Writer prompt`
- **No**, it does **not** reach every major LLM uniformly.
  - `Stage 4 Director review` does not receive the full style guide directly.
  - `Stage 2` has style-guide helper code, but its active runtime wiring is not proven in the current path.

So the precise claim that the evidence supports is:

> Desktop style reference is genuinely propagated into major downstream generation LLMs, especially Stage 3 blueprint generation and Stage 4 Chief Writer manuscript generation, but the propagation is partial rather than universal across all major LLM agents.
