Date: 2026-03-23
Status: final
Document Type: evidence manifest
Terminal: T3
Parent Report: `docs/2026-03-23/opus/pre-rerun-root-cause-t3-stage3-contract.md`

---

# T3 Evidence Manifest: Stage 3 Blueprint Contract and Context Static

## 1. Source Files Inspected

| File | LOC | Lines Read | Key Anchors |
|------|-----|------------|-------------|
| `modules/core/stage3_orchestrator.py` | 2,756 | Full | L478 class, L547 main entry, L660 episode loop, L1013 smart retrieval, L1218 finalize bundle, L1407 generation handoff, L1579 _generate_blueprint, L1645 _handle_success, L2441 _handle_failure |
| `modules/domain/agents/three_phase_blueprint_generator.py` | 278 | Full | L35 class, L113 generate() (thin shell), L158 _inplace_patch_blueprint, L254 get_stats() |
| `modules/domain/agents/blueprint_ensemble.py` | 1,151 | Full | L184 class, L310 _run_workers, L427 _qualify_candidates, L450 _finalize_candidates (L475 `[0]`), L477 generate_ensemble, L558 _generate_single |
| `modules/domain/agents/three_phase_blueprint_runtime.py` | 1,382 | Via agent | L147 pipeline_result init, L1043 terminal failure, L1208 Phase 1, L1219 Phase 2, L1251 Phase 3, L1299 generate() entry, L1335 retry loop |
| `modules/domain/agents/unified_blueprint_validator.py` | 904 | Via agent | L266 compare mode, L468 python_warnings truncation, L570 validate() entry, L844 python prevalidation |
| `modules/domain/agents/blueprint_constraint_compiler.py` | 606 | Via agent | L43 compile(), L108 compile_to_prompt() |
| `modules/core/stage3_context.py` | 129 | Via agent | 19 __slots__, L100 from_app() |

## 2. DB Evidence

### 2.1 stage_attempts (stage=3)

| ep_num | attempt_num | verdict | score | failure_category | candidate_key |
|--------|-------------|---------|-------|------------------|---------------|
| 1 | 2 | PASS | 92 | None | emotion_focused |
| 2 | 1 | PASS | 95 | None | emotion_focused |
| 3 | 1 | PASS | 95 | None | action_focused |
| 4 | 1 | PASS | 98 | None | dialogue_focused |

**Notable**: ep1 starts at attempt=2. No attempt=1 REJECT record exists in this table.

### 2.2 director_selections (stage=3)

| ep_num | round_num | verdict | score | strategy | candidates | fix_scope |
|--------|-----------|---------|-------|----------|------------|-----------|
| 1 | 2 | PASS | 92 | emotion_focused | 1 | (empty) |
| 2 | 1 | PASS | 95 | emotion_focused | 3 | inplace |
| 3 | 1 | PASS | 95 | action_focused | 3 | inplace |
| 4 | 1 | PASS | 98 | dialogue_focused | 3 | inplace |

**Notable**: ep1 had only 1 candidate (retry context). ep2-4 had 3 candidates with fix_scope=inplace. selection_reason/verdict_reason have mojibake in raw query output (terminal encoding issue).

### 2.3 Missing Data

- No `pass_rate_attempts` table exists — pass_rate_monitor data is in-memory only
- No Stage 3 REJECT records in `stage_attempts` — intermediate retries not persisted
- `runtime_audit.jsonl` has 0 Stage 3 entries — Stage 3 does not emit runtime audit events

## 3. Artifact Evidence

### 3.1 Blueprint Artifacts (Stage 3 output)

| Path | Status |
|------|--------|
| `projects/0_0323/logs/artifacts/stage3/ep_0001/attempt_02/final_blueprint__emotion_focused.json` | Exists |
| `projects/0_0323/logs/artifacts/stage3/ep_0002/attempt_01/final_blueprint__emotion_focused.json` | Exists |
| `projects/0_0323/logs/artifacts/stage3/ep_0003/attempt_01/final_blueprint__action_focused.json` | Exists |
| `projects/0_0323/logs/artifacts/stage3/ep_0004/attempt_01/final_blueprint__dialogue_focused.json` | Exists |

### 3.2 Saved Blueprints

| Path | Status |
|------|--------|
| `projects/0_0323/plans/blueprints/blueprint_0001.txt` | Exists |
| `projects/0_0323/plans/blueprints/blueprint_0002.txt` | Exists |
| `projects/0_0323/plans/blueprints/blueprint_0003.txt` | Exists |
| `projects/0_0323/plans/blueprints/blueprint_0004.txt` | Exists |

## 4. Console Evidence

### 4.1 Stage 3 Console Section (lines 401-461)

Key excerpts:
```
📐 [Stage 3] Blueprint frontier 동기화 (target <= ep 4)...
      🌍 [V68] WorldStateManager 초기화 (신규)
      📋 [V68] 팩트 원장 초기화 (신규)
📂 [Fresh Start] 기존 데이터 없음 - 1화부터 시작
📊 [V60.80] 현재 총 5화까지 설계가 가능합니다.

🎯 [V60.80] Three Phase Blueprint Generator 시작
   범위: 제1화 ~ 제4화 (4개)

      ⏳ Entity Registry 추출 중... (Arc 0, 첫 호출)
      📋 [V61] Entity Registry 추출: 43개 엔티티
```

Per-episode heartbeats:
```
ep1: anchors=0, window=0, semantic_ctx=2605자 → PASS score=92 emotion_focused
ep2: anchors=0, window=1, semantic_ctx=2605자 → PASS score=95 emotion_focused
ep3: anchors=0, window=2, semantic_ctx=2605자 → PASS score=95 action_focused
ep4: anchors=0, window=3, semantic_ctx=2605자 → PASS score=98 dialogue_focused
```

Summary:
```
📊 [V60.80] Stage 3 완료 통계
   성공: 4개 | 실패: 0개
   통과율: 83.3%
```

### 4.2 Key Console Observations

- `anchors=0` for all episodes: no previous manuscripts available (expected on first arc)
- `semantic_ctx=2605자` constant: minimal advisory context on fresh project
- `window` grows 0→1→2→3: blueprint history accumulates correctly
- `통과율: 83.3%`: terminal pass/reject ratio (5 pass / 1 intermediate reject for ep1 attempt 1)
- Entity Registry: 43 entities extracted once, cached for all 4 episodes

## 5. Cross-Document References

| Document | Finding | Relevance to T3 |
|----------|---------|-----------------|
| `fresh-run-3pass-audit-report.md` P3-2 | Pass rate >100% in test project | STALE in live code; fresh run shows 83.3% |
| `generation-coherence-deep-dive-report.md` GQ-1 | `qualified[0]` hardcoded P0 | OVERRIDDEN by Director compare; downgraded to P1 structural risk |
| `q1-q8-current-state-merge-audit.md` §3.1 | Q1 H-2 pass rate stale | Confirmed stale; live denominator is correct |
| `director-pipeline-7axis-deep-dive.md` §2 | Verdict ownership map | Stage 3 Director interactions confirmed at 4 integration points |

## 6. Schema Reference

### 6.1 pipeline_result Structure (from runtime)

```python
{
    "ep_num": int, "arc_no": int, "retries": int,
    "patch_fallback": bool, "asp_used": bool,
    "quality_gate_failed": bool, "quality_risk": bool,
    "revision_required": bool,
    "final_verdict": "PASS|PASS_WITH_FIX|PASS_WITH_WARNING|FAILED",
    "last_score": int, "failure_reason": str,
    "phases": {
        "constraint": {"status": str, "cached": bool, "arc_no": int},
        "generate": {"status": str, "candidates_count": int, "selected_strategy": str, "selected_score": int},
        "validate": {"status": str, "verdict": str, "score": int, "issues_count": int,
                      "fix_scope": str, "selection_reason": str, "verdict_reason": str,
                      "candidate_count": int, "contradictions": list}
    }
}
```

### 6.2 constraint_block Structure (from compiler)

```python
{
    "ep_num": int, "arc_no": int, "arc_position": str,
    "must_focus": {"content": str, "key_events": list, "arc_position": int, "arc_title": str},
    "stop_line": {"content": str|None, "is_arc_finale": bool, "next_ep": int},
    "continuity": {"prev_ending": str, "location": str, "time_context": str,
                    "ongoing_conflicts": list, "active_characters": list},
    "inherited_state": {"equipment": list, "injuries": str, "companions": list,
                         "mood": str, "internal_energy": str},
    "arc_constraint_summary": str,
    "state_changes_summary": str,
    "semantic_carryover": dict
}
```

### 6.3 Key Thresholds

| Threshold | Value | Source | Purpose |
|-----------|-------|--------|---------|
| Quality gate score | 90 | `validation.yaml` via `_threshold()` | Force REJECT if PASS + score < 90 |
| Emergency fallback | 60 | `PatchModeThresholds.REWRITE` | Allow PASS_WITH_WARNING if score >= 60 after all retries |
| Scene count minimum | 4 | `blueprint_ensemble.py:438` | Candidate qualification |
| Integrated scenario minimum | 500 chars | `blueprint_ensemble.py:438` | Candidate qualification |
| Max retries | 9 | `three_phase_blueprint_generator.py:119` | 10 total attempts (0-indexed) |
| PASS_WITH_FIX max patches | 3 | `runtime.py:731` | Inplace patch iterations |
| Context truncation | MAX_CONTEXT_CHARS | `constants.py` | prev_manuscripts_text cap |
| Python warnings forwarded | 4 items | `validator.py:468` | Director prevalidation header |
| Warning message length | 160 chars | `validator.py:472` | Per-warning truncation |
