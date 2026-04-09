# Stage234 Handoff Format Static Survey

Date: 2026-04-09
Status: final (static parallel survey completed; document 3-pass completed; confidence `97%`)
Canonical Path: `docs/2026-04-09/stage234-handoff-format-static-survey.md`
Evidence Path: `docs/2026-04-09/stage234-handoff-format-evidence.json`
Mode: system-track, survey-only, static-only
Commit State:
- Baseline Commit: `b94390cb508a298a28349152bb15876f36662c65`
- Baseline Dirty Summary: `dirty: active roadmap/SSOT docs plus narrative/material/project artifacts were already modified or deleted; this survey stayed read-only except for its own dated outputs`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `.planning/PROJECT.md`
- `contracts/artifact_contracts.json`
- `contracts/sequential_run_status.schema.json`
- `전처리_ssot/contracts/handoff_rules.json`
- `docs/2026-04-09/stage2-static-parallel-3pass-audit.md`
- `docs/2026-04-09/stage3-static-parallel-3pass-audit.md`
Evidence Basis:
- live code readback from `modules/core/project_manager.py`
- live code readback from `modules/core/db_manager.py`
- live code readback from `modules/core/stage2_finalizer.py`
- live code readback from `modules/core/stage3_orchestrator.py`
- live code readback from `modules/core/stage4_orchestrator.py`
- live code readback from `modules/core/stage4_post_processor.py`
- live code readback from `modules/core/stage4_post_pass_runtime.py`
- live code readback from `modules/core/stage4_interview_round.py`
- live code readback from `modules/core/artifact_logging.py`
- live code readback from `modules/core/feedback_system.py`
- live code readback from `main_a.py`
3-Pass Audit: `completed`

## 1. Answer First

질문에 바로 답하면:

- Stage2와 Stage3는 이미 `canonical JSON handoff`가 있다.
- Stage4는 `Stage2 arc`나 `Stage3 blueprint`처럼 단일한 `canonical JSON handoff packet`을 내지 않는다.
- Stage4의 주 산출물은 `human-facing manuscript text`다.
- 다만 Stage4에 JSON이 아예 없는 것은 아니다. `episode_bible`, `state_log`, `episode_production.jsonl`, attempt artifact/meta 같은 구조화 sidecar는 꽤 많이 남긴다.

그래서 정의를 나눠서 보면:

- `단일한 다음 단계용 canonical handoff packet` 기준: 없는 스테이지는 `Stage4`
- `구조화된 machine-readable carryover` 기준: `Stage4도 있다`, 다만 `분산되어 있고 보조적`이다

실무 결론:

- LLM 친화성을 더 끌어올리고 싶다면 개선 타깃은 `Stage4`
- Stage2/3는 이미 `JSON-first`
- Stage4는 `human-facing 원고 + 분산 JSON sidecar` 구조라서, 여기를 `canonical settlement packet`으로 묶는 게 가장 효과가 크다

## 2. Parallel Survey Layout

이번 정적 병렬 조사는 세 갈래로 나눠서 봤다.

1. Stage2 producer/handoff slice
2. Stage3 producer/handoff slice
3. Stage4 terminal-output/post-pass slice

공통 확인 항목:

- canonical 저장소가 무엇인지
- human-facing export가 무엇인지
- 다음 스테이지 또는 다음 회차가 실제로 어디를 읽는지
- structured sidecar가 canonical인지 보조인지

## 3. Pass 1. Inventory

### 3.1 Stage2

핵심 저장 경로:

- `Stage2Finalizer._persist_stage2_pass_arc_commit()`가 `refined_arc`를 `all_refined_arcs`에 넣고 `current_project.save_v20_anchor("arcs", all_refined_arcs)`를 호출한다. (`modules/core/stage2_finalizer.py:1784`)
- `ProjectContext.save_v20_anchor()`는 최종적으로 `db.save_anchor()`를 호출하고, `arcs`일 때는 `_save_arc_payload_collection()`으로 내려가 `anchors.arc_payload_*`와 aggregate `anchors.arcs`를 JSON으로 저장한다. (`modules/core/project_manager.py:187`, `modules/core/db_manager.py:1069`)

human-facing export:

- 같은 `save_v20_anchor("arcs", ...)` 경로에서 `_save_arcs_to_txt()`가 함께 돌고, `plans/arcs/*.txt`를 만든다. (`modules/core/project_manager.py:404`)
- 코드 주석이 이 txt를 `export 전용`, `DB primary source가 authority`라고 명시한다. 즉 txt는 canonical handoff가 아니다. (`modules/core/project_manager.py:405-406` 개념)

structured sidecar:

- Stage2 attempt artifact는 `snapshot_logged_artifact()`로 저장된다. payload가 dict면 `.json`, 문자열이면 `.txt`로 저장된다. (`modules/core/stage2_finalizer.py:3430`, `modules/core/artifact_logging.py:40`, `modules/core/artifact_logging.py:92`)
- `save_stage_attempt()`와 `save_director_selection()`도 linkage meta를 함께 적재한다. (`modules/core/stage2_finalizer.py:3473-3546`)

정리:

- Stage2의 canonical handoff는 `JSON`
- txt는 읽기 편한 보조 export다

### 3.2 Stage3

핵심 저장 경로:

- `Stage3Orchestrator._persist_stage3_success_blueprint()`가 `current_project.save_episode_blueprint(working_ep, blueprint)`를 호출한다. (`modules/core/stage3_orchestrator.py:2235`)
- `ProjectContext.save_episode_blueprint()`는 `db.save_blueprint()`로 `blueprints.data`에 JSON 저장 후 `_save_blueprint_to_txt()`를 같이 호출한다. (`modules/core/project_manager.py:286`, `modules/core/db_manager.py:1434`)

실제 소비 경로:

- Stage4는 `_prepare_current_episode_inputs()`에서 `current_project.get_blueprint(next_ep)`로 blueprint를 다시 읽는다. (`modules/core/stage4_orchestrator.py:1202`)
- 즉 Stage3 -> Stage4의 canonical machine handoff는 DB blueprint JSON이다.

human-facing export:

- `_save_blueprint_to_txt()`가 `plans/blueprints/blueprint_XXXX.txt`를 만든다. (`modules/core/project_manager.py:442`)
- 이 경로도 Stage2와 동일하게 export 성격이고, canonical source는 DB JSON이다.

structured sidecar:

- Stage3도 `final_blueprint` attempt snapshot을 남긴다. (`modules/core/stage3_orchestrator.py:1962`, `modules/core/artifact_logging.py:40`)
- `save_stage_attempt()`와 `save_director_selection()` observability가 붙는다. (`modules/core/stage3_orchestrator.py:2001-2108`)

정리:

- Stage3의 canonical handoff도 `JSON`
- txt는 reference export다

### 3.3 Stage4

입력 경로:

- Stage4는 `current_project.get_blueprint(next_ep)`로 Stage3 JSON blueprint를 읽고, `current_project.arcs`에서 Stage2 arc를 참조한다. (`modules/core/stage4_orchestrator.py:1202`, `main_a.py:3139`)

주 산출물:

- PASS 저장은 `_save_pass_result_primary_db()`에서 `db.save_manuscript(ep_num, title, content, hud_snapshot)`로 들어간다. (`modules/core/stage4_post_processor.py:639`, `modules/core/db_manager.py:535`)
- 여기서 manuscript body는 `content TEXT`로 저장된다. manuscript 전체를 JSON packet으로 저장하는 경로는 현재 canonical path가 아니다.

human-facing export:

- `_run_pass_result_local_side_effects()`가 `drafts/ep_XXXX.txt`에 `# title + manuscript` 형태로 바로 쓴다. (`modules/core/stage4_post_processor.py:738`)
- Stage4 session 환경 자체도 `output_dir = current_project.paths.drafts`로 잡는다. (`modules/core/stage4_orchestrator.py:2522`)
- `_normalize_reader_facing_manuscript()` 주석도 최종 reader-facing artifact 정리를 전제로 한다. (`modules/core/stage4_post_processor.py:144`)

structured carryover / sidecar:

- `episode_bible`는 `bible_delta` dict를 만들어 `save_episode_bible()`로 저장하고, 내부에서 개별 컬럼들을 JSON 문자열로 넣는다. (`modules/core/stage4_post_pass_runtime.py:1015-1044`, `modules/core/db_manager.py:635`)
- `state_log`도 `state_log_data` dict를 `save_state_log_with_summary()`로 저장하고, 내부에서 JSON 직렬화한다. (`modules/core/stage4_post_pass_runtime.py:1193-1206`, `modules/core/db_manager.py:1459`)
- `episode_production.jsonl` 로그가 남는다. (`modules/core/stage4_interview_round.py:6600`)
- Stage4 attempt artifact meta 역시 `snapshot_logged_artifact()`를 통해 저장된다. (`modules/core/stage4_interview_round.py:6857`, `modules/core/artifact_logging.py:40`)
- Stage4는 추가로 `world_state.save()`와 `fact_ledger.save()`도 호출하지만, 이 조사에서는 그 on-disk encoding까지는 추적하지 않았다. (`modules/core/stage4_post_pass_runtime.py:1416-1451`, `:1531`)

reverse feedback:

- `Stage4 -> 3`, `Stage3 -> 2`, `Stage4 -> 2` 역방향 피드백 helper는 모두 `문자열 텍스트`를 만든다. (`modules/core/feedback_system.py:600`, `:650`, `:691`)
- 즉 이것도 canonical JSON handoff라기보다 runtime guidance text에 가깝다.

정리:

- Stage4의 `주 산출물`은 human-facing manuscript text
- Stage4의 `structured output`은 많지만, 하나의 canonical handoff packet으로 정리돼 있지 않다

## 4. Pass 2. Semantic Classification

| Stage | Canonical machine handoff | Human-facing export | Structured sidecars | 판정 |
| --- | --- | --- | --- | --- |
| Stage2 | `anchors.arc_payload_*`, `anchors.arcs` JSON | `plans/arcs/*.txt` | attempt artifacts, stage attempts, director selections | `JSON-first` |
| Stage3 | `blueprints.data` JSON | `plans/blueprints/*.txt` | attempt artifacts, stage attempts, director selections | `JSON-first` |
| Stage4 | `manuscripts.title/content` TEXT가 주 산출물 | `drafts/ep_XXXX.txt` | `episode_bibles`, `state_logs`, `episode_production.jsonl`, attempt artifacts | `human-facing primary + fragmented structured sidecars` |

핵심 semantic distinction:

- Stage2/3는 `next-stage producer`
- Stage4는 `terminal writer + post-pass settlement`

그래서 Stage2/3는 naturally `canonical JSON handoff`가 있고, Stage4는 `reader artifact`가 먼저다.

## 5. Pass 3. Execution Consequence

사용자 질문을 운영 관점으로 바꾸면:

- `LLM이 더 잘 읽게 만들고 싶다`
- `어느 스테이지를 JSON packet으로 더 정리해야 효과가 큰가`

정답은 `Stage4`다.

이유:

- Stage2는 이미 arc dict가 canonical이다
- Stage3도 blueprint dict가 canonical이다
- Stage4만 `최종 원고 TEXT`와 `carryover JSON sidecar`가 분리되어 있어, LLM이 후속 작업을 하려면 여러 sink를 다시 모아야 한다

따라서 가장 자연스러운 개선안은:

- manuscript 본문 자체를 억지로 JSON으로 감싸는 것이 아니라
- `manuscript text + carryover state + verdict/meta + artifact refs`를 한 번에 묶는 `Stage4 canonical settlement packet`을 추가하는 것

권장 packet 예시:

- `ep_num`
- `title`
- `manuscript_path`
- `manuscript_content_hash`
- `arc_no`
- `blueprint_ep`
- `stage4_verdict`
- `attempt_key`
- `episode_bible`
- `state_log`
- `quality_labels`
- `quality_signals`
- `selection_artifact`
- `final_artifact`
- `carryover_contracts`

이렇게 하면:

- human-facing 원고는 그대로 보존되고
- LLM/도구는 packet 하나만 읽어도 후속 판단을 할 수 있다
- 지금처럼 `manuscript + episode_bible + state_log + jsonl + attempt meta`를 흩어 읽는 비용이 줄어든다

## 6. Final Conclusion

`JSON handoff를 안 내는 stage`를 하나 고르라면 `Stage4`다. 정확히는 `Stage4의 primary artifact가 human-facing manuscript이고, JSON은 sidecar로는 많지만 canonical packet으로는 묶여 있지 않다`.

즉, `Stage2/3는 이미 JSON-first`, `Stage4는 human-facing-first + structured-sidecar-second` 구조다. LLM 친화성을 더 높이려면 손봐야 할 곳은 Stage4다.
