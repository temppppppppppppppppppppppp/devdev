# Gotchas

> Read this before using stage_map for debugging or remediation work.

## G-1. Stage 3 now uses the shared 90-point QualityGate
**현상**: Stage 3도 더 이상 별도 Blueprint 전용 gate를 쓰지 않는다.  
**원인**: `three_phase_blueprint_generator.py`가 `scoring.quality_gate_score`를 읽도록 정렬됐다.  
**실제 영향**: 예전 `80 gate`를 전제로 논의하면 retry, PASS_WITH_FIX, PASS_WITH_WARNING 해석이 틀어진다.  
**확인 위치**: `modules/domain/agents/three_phase_blueprint_generator.py`, `config/settings/validation.yaml`

## G-2. PASS_WITH_FIX는 최초 QualityGate를 bypass하지만 영구 면제는 아니다
**현상**: `PASS_WITH_FIX`는 첫 진입에서 즉시 gate 강등되지 않지만, patch 재심사에서 `PASS`가 나오면 다시 90점 gate를 탄다.  
**원인**: Director 주권을 보존하면서도 최종 PASS는 gate를 다시 통과시키는 구조다.  
**실제 영향**: `PASS_WITH_FIX`를 "무조건 통과"로 읽으면 안 된다. patch loop 안에서 다시 실패할 수 있다.  
**확인 위치**: `modules/domain/agents/three_phase_blueprint_generator.py`, `modules/core/stage4_interview_round.py`

## G-3. PASS_WITH_WARNING은 여전히 저장 가능한 degraded outcome이다
**현상**: Stage 3 재시도 소진 후 마지막 점수가 `rewrite_below(50)` 이상이면 `PASS_WITH_WARNING`으로 저장될 수 있다.  
**원인**: 긴급 폴백 경로가 남아 있고 `_stage3_meta.quality_risk`가 함께 붙는다.  
**실제 영향**: "저장됐다 = 깨끗한 PASS"가 아니다. Stage 4는 `_stage3_meta`를 보고 경고 강도를 높일 수 있다.  
**확인 위치**: `modules/domain/agents/three_phase_blueprint_generator.py`, `modules/core/stage4_orchestrator.py`

## G-4. Blueprint txt와 draft txt는 사람용 export이고 DB가 SSOT다
**현상**: `plans/blueprints/*.txt`, `drafts/ep_XXXX.txt`를 고쳐도 stage handoff truth가 바뀌지 않을 수 있다.  
**원인**: Stage 4는 `current_project.get_blueprint(next_ep)` -> DB `blueprints`를 읽고, 원고 SSOT도 `manuscripts` 테이블이다.  
**실제 영향**: export 파일만 수정해서는 다음 stage 입력을 고친 것이 아니다.  
**확인 위치**: `modules/core/project_manager.py`, `modules/core/db_manager.py`, `modules/core/stage4_orchestrator.py`

## G-5. Stage 4 patch routing의 live branch key는 legacy 중간 임계값이 아니다
**현상**: 현재 Stage 4 분기는 `fix_scope`, `inplace_below`, `rewrite_below` 중심이다.  
**원인**: 예전 문서에 남은 80점대 중간 patch threshold 설명은 더 이상 live branch key가 아니다.  
**실제 영향**: 구 문서 기준으로 Stage 4 retry를 설명하면 잘못된 remediation이 나온다.  
**확인 위치**: `modules/core/stage4_interview_round.py`, `config/settings/validation.yaml`

## G-6. Stage 4 EMPTY와 attempt sink의 ERROR는 같은 사건을 다른 표면에서 본 것이다
**현상**: Interview round는 caller에 `verdict="EMPTY"`를 돌려주지만, `stage_attempts`에는 `verdict="ERROR"` + `reject_reason="empty_candidates"`가 찍힌다.  
**원인**: caller-facing semantics와 observability sink labeling이 완전히 동일하지 않다.  
**실제 영향**: 운영 로그, DB 집계, canary proof를 섞어 볼 때 label mismatch를 오탐으로 읽지 말아야 한다.  
**확인 위치**: `modules/core/stage4_interview_round.py`

## G-7. Stage2Context에는 아직 `world_state` 슬롯이 없다
**현상**: Stage 2 오케스트레이터는 `getattr(ctx, "world_state", None)`로 bind를 시도하지만, Stage2Context는 dedicated `world_state` 속성을 제공하지 않는다.  
**원인**: Stage 2 DI surface가 확장되는 중인데 context slot과 consumer가 완전히 맞물리지는 않았다.  
**실제 영향**: Stage 2 WorldState 배선이 있다고 가정하고 문서를 쓰거나 테스트를 설계하면 틀릴 수 있다.  
**확인 위치**: `modules/core/stage2_context.py`, `modules/core/stage2_orchestrator.py`

## G-8. `validate_arc_data_fields`는 live repair seam이다
**현상**: `main_a.py` facade -> `Stage2Context` -> `Stage2Finalizer` -> `Stage3Orchestrator`로 이어지는 실제 repair hook가 있다.  
**원인**: Arc 구조 복구가 여러 stage에서 재사용되도록 callback seam으로 묶여 있다.  
**실제 영향**: mock-only context tests는 이 seam의 live binding drift를 가릴 수 있다.  
**확인 위치**: `main_a.py`, `modules/core/stage2_context.py`, `modules/core/stage2_finalizer.py`, `modules/core/stage3_orchestrator.py`

## G-9. Stage 1 `_show_volume_table()`는 live지만 강한 계약 surface는 아니다
**현상**: Stage 1 완료 후 `_show_volume_table(final_volumes)`가 호출되지만, `Stage01Helpers`는 `hasattr(app, "_show_volume_table")`로 optional seam처럼 다룬다.  
**원인**: data commit과 operator-facing presentation이 느슨하게 결합돼 있다.  
**실제 영향**: UI 출력은 저장 확인용 힌트이지, Stage 1 무결성 자체를 보장하는 계약은 아니다.  
**확인 위치**: `modules/core/stage01_helpers.py`, `main_a.py`, `modules/core/services/ui_service.py`

## G-10. Stage 0 `reference_excerpt`는 50,000자까지 커질 수 있고 Stage 4에 raw 주입된다
**현상**: Stage 0는 `reference_excerpt`를 최대 50,000자로 만들고, Chief Writer 공통 프롬프트는 이를 별도 추가 절삭 없이 붙인다.  
**원인**: Stage 0 cap과 Stage 4 prompt budgeting이 별개 레이어다.  
**실제 영향**: 큰 reference excerpt는 context pressure를 키우지만 Stage 0 alone만 보고는 그 영향을 체감하기 어렵다.  
**확인 위치**: `modules/core/stage0/style_extractor.py`, `modules/domain/agents/chief_writer_context.py`

## G-11. Stage 4 NPC profile sourcing은 facade-first, AssetLibrary fallback이다
**현상**: 현재 `_build_cv_context()`는 `npc_profiles={}` 고정이 아니라 `extract_npc_profiles` seam을 먼저 보고, 실패하면 MasterBible AssetLibrary 필터로 폴백한다.  
**원인**: earlier bypass 문제를 줄이기 위해 facade-or-fallback 구조가 들어갔다.  
**실제 영향**: NPC validation 문제를 볼 때는 "무조건 빈 dict"라는 옛 전제를 버려야 한다. 대신 facade failure와 fallback precision을 구분해야 한다.  
**확인 위치**: `modules/core/stage4_context.py`, `modules/core/stage4_interview_round.py`

## Last Verified
- Date: 2026-03-13
- Commit: `e18f9910`
- Workspace State: dirty
- Code Sync (Yes/No): Yes
- Verified By: Codex
