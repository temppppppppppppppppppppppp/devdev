# Codex Stage-Wise Canon Memory Plan

## Goal
- Preserve long-term continuity facts (for example NPC title changes) without forcing infinite schema expansion.
- Keep flexibility for work-specific worldbuilding while preventing critical regressions.
- Run continuously even if context compaction happens during long sweeps.

## Non-Goals
- No full hard-reject automation by Python validators.
- No write access to canon memory outside Stage4.
- No requirement to model every lore attribute as a fixed column.

## Core Policy
- `Hard Fact`: small mandatory canon set.
- `Open Fact`: extensible key-value facts for project-specific traits.
- `Warning-Only Python`: validators can flag, not auto-reject.
- `Director Sovereignty`: final accept/reject decision stays with LLM Director.

## Hard Fact Scope (Minimum)
- Character life state: alive/dead/unknown.
- Character title or rank: current authoritative title.
- Core affiliation: organization/faction membership.
- Core relationship state: ally/enemy/family/mentor level facts.

## Open Fact Scope (Extensible)
- Namespaced keys such as `career.title_history`, `magic.circle`, `hunter.rank`, `politics.office_term`.
- Versioned updates through event records, not schema explosion.

## Stage Ownership Matrix
| Stage | Canon Read | Canon Write | Validator Mode | Decision Owner |
|---|---|---|---|---|
| Stage1 | Yes (summary) | No | Warning | Director |
| Stage2 | Yes (read-only snapshot) | No | Warning | Director |
| Stage3 | Yes (strong read) | No | Warning | Director |
| Stage4 | Yes (full) | Yes (final commit only) | Warning + final flagging | Director |

## Runtime Flow
1. Load canon snapshot at stage start from persistent store.
2. Inject snapshot into prompt context for relevant stage.
3. Produce candidate changes only in Stage2 and Stage3.
4. In Stage4, consolidate candidates and manuscript evidence.
5. Director approves or rejects candidate canon updates.
6. Commit approved updates as both current snapshot and append-only events.
7. Run post-check validator and emit warnings for unresolved conflicts.

## Context Compaction Guard (No-Stop)
- Canon must be persisted in DB/event store every committed episode.
- On any restart or context compaction, rebuild state from persistent snapshot plus events.
- Never rely only on in-context chat memory for canon facts.
- Sweep resumes from last committed round index and canonical checkpoint id.
- **[Gemini 3.1 Pro / Antigravity 권고사항]**: `Stale Cache` 방어. 수동 개입이나 Director Override로 인해 현재 Arc나 이전 Stage의 상태가 수정될 경우, 메모리에 상주 중인 Entity Registry(Stage 3 등) 캐시를 즉각 `Invalidate`(무효화)하는 트리거 연동이 필수적입니다.

## Minimal Integration Points
- Write and commit: `modules/core/stage4_post_processor.py`
- Canon store and merge: `modules/core/fact_ledger.py`, `modules/core/db_manager.py`
- Context injection: `modules/core/stage4_context_builder.py`, `modules/core/writer_prompt_builders.py`
- Validation warnings: `modules/validation/continuity_validator.py`

## Validation Policy
- Python checker output levels: `info`, `warning`, `high_warning`.
- No `reject` from Python layer.
- Director prompt must include warning summary and explicit final judgment request.

## False Positive Control
- Before flagging bug, check declared design intent first.
- If behavior is plausible by intended world rule, classify as `intent_candidate`, not bug.
- Require evidence fields in findings: file path, line clue, intent-check note, counter-evidence note.

## Acceptance Criteria
- Promotion test: `A -> B` title change remains consistent for at least 10 subsequent episodes.
- Conflict recovery test: after forced context compaction, canon reload restores latest title and affiliation.
- Drift test: random episode generation does not revert committed Hard Fact unless explicit reversal event exists.

## Rollout Plan
1. Implement Stage4 canonical write gate.
2. Add read-only canonical injection to Stage2 and Stage3.
3. Switch validator to warning-only enforcement.
4. Add continuity regression scenarios to CI or nightly checks.
5. Run pilot on one project and compare drift rate before rollout.

## Operational Notes
- This plan is designed for uninterrupted manual sweep operations.
- Manual review remains mandatory for final finding classification.
- Automated search tools can assist navigation, but canon judgment must be evidence-based and manually verified.
