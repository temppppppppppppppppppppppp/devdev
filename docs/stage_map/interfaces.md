# Interfaces

Purpose:
- Capture caller-callee contracts across stages.
- Keep stage boundaries explicit and testable.

## Contract Matrix

| From | To | Input Contract | Output Contract | Failure Contract | Owner |
|---|---|---|---|---|---|
| Stage 0 | Stage 1 | `ProjectContext.save_v20_anchor("bible", dict)`로 `anchors.key='bible'` 저장. Stage 1 미사용 시 Stage 2가 직접 소비 | Stage 1 사용 시 `anchors.key='volumes'`(list) 기대 | 앵커 JSON 파싱 실패 시 `{}`/기본값 폴백 (`load_anchor`) | Stage 0 (`ProjectContext`) |
| Stage 1 | Stage 2 | (현재 파이프라인에서 선택적) `anchors.key='volumes'` + `anchors.key='bible'` | Stage 2 완료 시 `anchors.key='arcs'`에 Arc 리스트 JSON 저장 (`save_v20_anchor("arcs", ...)`) | Stage 1 산출물 부재 시 Stage 2는 Bible 기반 최소 동작 가능 | Stage 1/2 |
| Stage 2 | Stage 3 | `anchors.key='arcs'` (list[ArcData-compatible dict]), `anchors.key='bible'` | ArcData 계약: `arc_no/global_arc_no`, `ep_start`, `ep_end`, `tactical_doc`, `beat_sequence`, `state_constraints`, `state_changes`, `episode_details` 등 | Arc dict 스키마 불일치 시 `validate_arc()`가 원본 dict 유지 (graceful degradation) | Stage 2 + `modules/models/arc.py` |
| Stage 3 | Stage 4 | `db_manager.get_blueprint(ep_num)` -> `blueprints.data` JSON(dict), 이전 회차는 `get_previous_blueprint` | Stage 4 입력 Blueprint dict: `episode_number(ep_num alias)`, `scene_breakdown`, `integrated_scenario`, `pacing_notes`, `target_beat`, `relationship_changes`, `time_flow`, `core_tension`, `expected_ending` | Blueprint JSON 파싱 실패 시 `None` 반환 (`get_blueprint`) | Stage 3/4 + `modules/models/blueprint.py` |

## Shared Invariants
- Invariant 1: Stage 간 영속 계약은 `project_data.db` 중심. `anchors`/`blueprints`/`manuscripts`/`episode_bibles`가 핵심 전달 경로.
- Invariant 2: Stage 4 후속 상태는 DB anchor 기반 누적 저장:
  - `world_state` (`WorldStateManager`, anchor key)
  - `fact_ledger` (`FactLedger`, anchor key)
  - `npc_history` (append-only table)
  - `npc_relationship_history` (append-only, sorted key — LM-D)
  - `episode_meta`/`vec_episodes`/`episode_fts` (VecMemory 검색 인덱스)
- Invariant 3: JSON 계약 실패는 fail-closed보다 비차단 폴백 우선:
  - `load_anchor()` 실패 시 기본값 반환
  - `get_blueprint()` JSON 파싱 실패 시 `None`
  - Arc/Blueprint Pydantic 검증 실패 시 원본 dict 유지
- Invariant 5: **Director verdict 3종** — `PASS`, `REJECT`, `PASS_WITH_FIX` (TF-27):
  - PASS_WITH_FIX는 `fix_scope` 필드(`inplace`/`partial`/`full`)와 `feedback.action_items`를 반드시 동반
  - QualityGate는 PASS일 때만 score < 90이면 REJECT 전환. **PASS_WITH_FIX는 QualityGate bypass** (TF-46)
- Invariant 6: **state_updates 전파 우선순위** — Director 보정값 > CW 생성값 > {} (TF-R4):
  - Director 프롬프트가 CW state_updates를 "기반으로 보정" → superset 반환
  - InPlace patch 시 `{**final_state_updates, **_patch_state}` merge 후 Director 재심사
- Invariant 4: `db_manager.py` 부트스트랩 기준 테이블 목록:
  - `sync_status`, `surgery_logs`, `anchors`, `blueprints`, `state_logs`, `causal_graph`, `karma_status`, `manuscripts`, `reflexion_memory`, `martial_tracker`, `seeds`, `encyclopedia`, `episode_bibles`, `npc_history`, `episode_sentence_hashes`, `episode_satisfaction_tags`, `director_selections`, `cost_log`, `episode_meta`, `episode_fts`, `episode_pacing`, `character_voice`, `foreshadow` (+ `vec_episodes` 가상 테이블, sqlite-vec 사용 시)

## Breaking Change Checklist
- Was any input field added/removed/renamed?
- Was any output field added/removed/renamed?
- Were default values changed?
- Were failure codes/messages changed?
- Were fallback paths changed?

## Last Verified
- Date: 2026-03-02
- Commit: `8476bc2`
- Code Sync (Yes/No): Yes
- Verified By: Opus

