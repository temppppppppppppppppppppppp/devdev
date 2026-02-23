# Codex 추가 감리 의견서 (Stage 0~4 개선 반영 기준)

작성일: 2026-02-21  
검토 대상:
- 원안: `docs/2026-02-21/codex_opus_document_overview.md`
- Gemini 의견: `docs/2026-02-21/codex_docs_update_recommendations.md`

---

## 1) 결론
- Gemini 의견의 문제 제기 방향은 타당하지만, "기존 Codex 문서에 반영이 전혀 안 됨"이라는 총평은 **현행 문서/코드 기준으로 과도**합니다.
- 4개 핵심 권고 중 다수는 이미 플랜 문서에 반영되어 있습니다.
- 반면 `codex_patch_retry_extension_plan.md`는 문서가 제안한 변경과 실제 코드 상태가 어긋난 항목이 있어, 이 부분은 **문서 최신화 + 구현 추적 분리**가 필요합니다.

---

## 2) 항목별 판정 (Codex 의견)

### A. `codex_canon_os_v2_plan.md` 관련
판정: **Gemini 제안은 이미 문서 반영됨 (신규 수정 우선순위 낮음)**

근거:
- 비동기 입력/개입 경로 강제 문구가 이미 존재 (`docs/codex_canon_os_v2_plan.md:113`).
- 롤아웃 단계 점검 문구도 이미 존재 (`docs/codex_canon_os_v2_plan.md:151`).
- 따라서 Gemini 문서의 "명세 부족" 평가는 현재 시점에선 일부 해소 상태입니다.

### B. `codex_stage_canon_memory_plan.md` 관련
판정: **문서 반영 완료 + 리스크로 관리 가능**

근거:
- Stale cache invalidate 권고가 문서에 이미 삽입됨 (`docs/codex_stage_canon_memory_plan.md:51`).
- Stage3 캐시 처리도 arc index 변경/예외 시 재추출 경로를 가짐 (`modules/core/stage3_orchestrator.py:345`, `modules/core/stage3_orchestrator.py:373`).
- 현재는 "Major 즉시수정"보다 "운영 리스크 모니터링" 레벨이 적절합니다.

### C. `codex_patch_retry_extension_plan.md` 관련
판정: **Gemini의 Critical 분류 타당. 단, 문서-코드 동기화가 더 큰 이슈**

근거 1: Event loop 블로킹 이슈는 코드에서 이미 완화됨
- Stage2 입력은 동기 `input()` 직접 호출이 아니라 `asyncio.to_thread(input, ...)`로 변경됨 (`modules/core/stage2_orchestrator.py:691`, `modules/core/stage2_orchestrator.py:721`, `modules/core/stage2_orchestrator.py:782`).

근거 2: 문서가 요구한 패치 재시도 확장은 실제 코드에 미완료 구간이 있음
- 플랜 문서는 `MAX_PATCH_RETRIES` 추가를 명시 (`docs/codex_patch_retry_extension_plan.md:775`)하지만, 코드 상수에는 아직 `REWRITE/PATCH`만 존재 (`modules/core/constants.py:538`, `modules/core/constants.py:539`).
- Stage4 패치 경로도 아직 "1회 패치 -> 실패 시 즉시 regenerate" 구조임 (`modules/core/stage4_interview_round.py:136`, `modules/core/stage4_interview_round.py:151`).

근거 3: 문서가 지적한 Stage2 패치 시그니처 불일치 버그는 현행 코드에서도 재현 가능 상태
- 호출부는 `adversarial_self_play`를 전달 (`modules/core/stage2_preflight.py:526`).
- 수신 시그니처에는 해당 파라미터가 없음 (`modules/domain/agents/four_phase_arc_generator.py:451`, `modules/domain/agents/four_phase_arc_generator.py:468`).
- 키워드 전용 시그니처(`*`)라 패치 모드 진입 시 `TypeError` 위험이 있습니다.

### D. `codex_resume_replay_idempotency_sweep100_plan.md` 관련
판정: **Gemini 제안 반영 완료 (유지)**

근거:
- Lazy Init 복원 완결성 검증 항목이 Phase 2에 이미 포함됨 (`docs/codex_resume_replay_idempotency_sweep100_plan.md:12`).

---

## 3) 원안/제미니 문서 자체 수정 필요사항

### 3-1. Gemini 문서 상태값 정정
- `docs/2026-02-21/codex_docs_update_recommendations.md:43`의 "전혀 반영되어 있지 않다" 문구는 현재 기준과 불일치합니다.
- 동일 문서 내 항목별 결과를 `수정 필요` 단일값이 아니라 아래 3상태로 재라벨링 권장:
  - `반영 완료(문서)`
  - `부분 반영(코드 미동기화)`
  - `미반영`

### 3-2. 원안 문서에 "상태 레이어" 추가
- 현재 원안은 목록/분류 중심이며 상태 정보가 없습니다 (`docs/2026-02-21/codex_opus_document_overview.md:8`, `docs/2026-02-21/codex_opus_document_overview.md:60`).
- 각 문서 항목에 최소 `Status(초안/운영/보류)`, `Last Verified Date`, `Code Sync` 3필드 추가를 권장합니다.

### 3-3. 감사 문서 간 불일치 정리
- 통합 감사 문서는 Stage2/3/4 입력 관련 3개 버그를 "미수정"으로 유지 중 (`docs/2026-02-21/consolidated_stage_0_4_audit_report.md:107`, `docs/2026-02-21/consolidated_stage_0_4_audit_report.md:143`, `docs/2026-02-21/consolidated_stage_0_4_audit_report.md:188`)이나,
- 실제 코드는 해당 방어 로직이 반영됨 (`modules/core/stage3_orchestrator.py:114`, `modules/core/stage4_orchestrator.py:707`, `modules/core/services/ui_service.py:114`).
- 감사 문서의 "as-of 코드 기준" 갱신이 필요합니다.

---

## 4) 우선순위 제안

### P0 (즉시)
1. `codex_patch_retry_extension_plan.md`의 "구현 예정"과 "이미 반영"을 분리 표기.
2. Stage2 패치 시그니처 불일치(`adversarial_self_play`)를 이슈로 격상하고 추적.
3. Gemini 요약 문구(총평)와 통합감사의 미수정 목록을 현행 코드 기준으로 업데이트.

### P1 (다음 배치)
1. 원안(`codex_opus_document_overview.md`)에 상태/검증일/코드동기화 컬럼 추가.
2. 패치 재시도 플랜의 절대경로(`file:///c:/Users/User/...`)를 저장소 상대경로로 정리.

---

## 5) 최종 Codex 의견 한줄
- "Gemini 제안은 방향성은 맞다. 다만 현재는 '전면 미반영' 단계가 아니라, **문서 반영은 상당수 완료되고 코드 동기화 일부가 남은 단계**"로 보는 것이 정확합니다.
