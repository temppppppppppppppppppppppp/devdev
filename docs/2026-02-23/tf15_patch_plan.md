# TF-15 Patch Plan / Execution Log

> 집계 소스: `tf10_findings.md`, `tf11_findings.md`, `tf12_findings.md`, `tf13_findings.md`, `tf14_findings.md`

---

## P0 적용 내역

| ID | 출처 | 리스크 | 조치 파일 | 상태 |
|---|---|---|---|---|
| P0-01 | TF-12 A-1 | save 실패 후 commit로 부분 저장 | `modules/core/project_manager.py` | Done |
| P0-02 | TF-12 D-1 | enrich 실패 후 arc 번호 오염 | `modules/core/stage2_orchestrator.py` | Done |
| P0-03 | TF-12 B-1 | hybrid miss 시 빈 컨텍스트 | `modules/core/vec_memory.py` | Done |
| P0-04 | TF-12 C-1 | key rotation client 생성 예외 전파 | `modules/domain/agents/base_agent.py` | Done |
| P0-05 | TF-12 D-2 | CoVe 런타임 예외 silent pass | `modules/core/stage4_orchestrator.py` | Done |
| P0-06 | TF-12 E-1 | prev_hud 누락 시 continuity PASS | `modules/validation/continuity_validator.py` | Done |
| P0-07 | TF-12 E-2 | consistency validator 예외 시 무위반 처리 | `modules/validation/validation_orchestrator.py` | Done |
| P0-08 | TF-11 C-1 | Stage4Context.from_app emotion_tracker 누락 | `modules/core/stage4_context.py` | Done |

---

## 구현 요약

1. 트랜잭션/상태 무결성
   - `save_v20_anchor`는 `result=True`일 때만 commit, 실패면 rollback 시도.
2. 인덱스 정합성
   - Stage2 enrich 배치를 `(source_arc_idx, item)` 튜플로 유지해 실패/복구 후에도 원래 arc 번호 보존.
3. fail-open 제거
   - CoVe 예외는 REJECT 라운드로 전환.
   - `prev_hud` 누락은 `passed=False` + `BLOCKING` 위반 반환.
   - 병렬 consistency 예외는 CRITICAL 위반으로 fail-closed.
4. 복원력/DI 보강
   - hybrid retrieval miss 시 keyword fallback.
   - key rotation client 생성 실패 시 회전 상태 롤백.
   - Stage4Context.from_app에서 `emotion_tracker` 주입.

---

## 검증 결과

1. Lint
   - `python -m ruff check ...` (변경 파일 대상) 통과.
2. Syntax
   - `python -m compileall ...` (변경 파일 대상) 통과.
3. Targeted tests
   - `python -m pytest -q tests/test_continuity_validator.py tests/test_base_agent.py tests/test_vec_memory.py tests/test_validation_orchestrator.py tests/test_stage4_orchestrator.py tests/test_stage4_context.py tests/test_stage4_context_builder.py tests/test_continuity_modules.py tests/e2e/test_npc_continuity_e2e.py`
   - 결과: `308 passed`.

---

## P1 백로그 (미적용)

1. TF-13 MED: `MANUSCRIPT_HISTORY_CONFLICT_PROMPT` fail-open 정책.
2. TF-13 LOW: `PromptLoader` 캐시 키에 `PROMPT_DIR` 축 미반영.
3. TF-10/11/12 LOW~MED: nullable callback callable guard 일관화.
