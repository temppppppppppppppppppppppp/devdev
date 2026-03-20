# 글도비 코드 패치 ROI 요약

**작성일**: 2026-03-18
**대상**: 커밋 `52420a28` 코드 패치 3건
**근거**: 3회 전면 재조사 + 적대적 3-pass 감리 완료된 ssot_execution 문서

---

## 패치 3건 요약

### 패치 1. Blueprint 스키마 호환성 수정

**파일**: `response_schemas.py` (+71/-11), `three_phase_blueprint_generator.py` (+21), `blueprint_ensemble.py` (+1), `base_agent.py` (+4)

**문제**:
- Gemini API가 `additionalProperties`를 지원하지 않아 Blueprint 생성이 `schema_incompatible` 에러로 실패
- Stage 3 전체가 PATCHING 상태 — Blueprint를 만들 수 없으면 원고도 못 만듦

**수정 내용**:
- `scene_breakdown`: `additionalProperties` → `scene_1`~`scene_5` 고정 키로 전환
- `BLUEPRINT_SCENE_ENTRY_SCHEMA`: type, title, description, tension_level 필드 추가
- `BLUEPRINT_PROTAGONIST_STATE_SCHEMA`, `BLUEPRINT_ENDING_STATE_SCHEMA` 신규 정의
- `BLUEPRINT_SCHEMA`: title, start_location, end_location, ending_hook, protagonist_state, ending_state 추가
- `AgentErrorType.SCHEMA_INCOMPATIBLE` 에러 분류 추가
- `schema_incompatible` 감지 시 재시도 루프 즉시 중단 (9회 헛 재시도 방지)

**개선 효과**:
- Stage 3 정상 가동 복구 — Blueprint 생성 가능
- 스키마 에러 시 즉시 중단 → **재시도 비용 최대 9배 절감**
- Blueprint에 title/ending_hook/protagonist_state 포함 → Stage 4 원고 품질 상승 (설계도에 더 많은 정보)

**테스트**: `test_blueprint_patch_mode.py` +54줄 (schema_incompatible 즉시 실패, 긴급 폴백 미발동 검증)

---

### 패치 2. Director Facade 시그니처 정합

**파일**: `director.py` (+8/-1)

**문제**:
- Director의 `select_and_judge_ensemble()` facade가 하위 모듈(`DirectorEnsembleSelector`)에 `decision_core`, `candidate_evidence`, `reference_appendix` 3개 파라미터를 전달하지 않음
- Stage 4에서 Director가 후보 원고를 평가할 때, 판단 근거(decision_core)와 후보 증거(candidate_evidence)가 누락 → Director가 불완전한 정보로 판정

**수정 내용**:
- facade에 `decision_core=""`, `candidate_evidence=""`, `reference_appendix=""` 3개 파라미터 추가
- 하위 `_ensemble.select_and_judge_ensemble()`에 그대로 전달

**개선 효과**:
- Director가 **판단 근거 + 후보 증거 + 참조 부록** 전부를 보고 판정 → 판정 정확도 향상
- "왜 이 원고를 선택했나"의 근거가 명확해짐

**테스트**: `test_director_modules.py` +13줄 (3개 파라미터 전달 검증)

---

### 패치 3. Stage 4 무진척 자동 차단

**파일**: `main_a.py` (+60/-1)

**문제**:
- FrontierLag 자동 연속 생산에서 Stage 4가 backlog 상태인데 원고가 하나도 안 나와도 다음 Arc로 자동 진행
- 결과: LLM 비용만 쓰고 원고는 0 → 다음 Arc도 실패 → 비용 폭증

**수정 내용**:
- `_is_stage4_zero_progress_blocked()` 정적 메서드 추가
- Stage 4 backlog에서 `ms_max_after <= ms_max_before`이면 (원고 진척 0) 즉시 중단
- Final close 경로 + Arc 진행 경로 2곳 모두에 가드 적용
- Stage 4 에러 시 "최선 결과 수용" → **즉시 중단 + stop_reason 기록**으로 변경

**개선 효과**:
- 무한 비용 소비 방지 — Stage 4 실패 시 즉시 멈춤
- `stop_reason` 기록으로 "왜 멈췄나" 추적 가능 (`stage4_final_close_no_progress`, `stage4_no_progress_blocked`, `stage4_error`)

**테스트**: `test_one_stop_frontier_lag_auto_continue.py` +90줄 (final close 차단, arc advance 차단 2개 시나리오)

---

## 패치 3건 종합 ROI

| 지표 | 패치 전 | 패치 후 |
|------|--------|--------|
| Stage 3 가동 | **불가** (schema_incompatible) | 정상 |
| 스키마 에러 재시도 | 최대 9회 (비용 9x) | **1회 후 즉시 중단** |
| Director 판단 근거 | 3개 중 0개 전달 | **3개 전부 전달** |
| Stage 4 무진척 대응 | 다음 Arc 자동 진행 (비용 폭증) | **즉시 중단 + 이유 기록** |
| Blueprint 정보량 | 3필드 (episode_number, scene_breakdown, integrated_scenario) | **+8필드** (title, ending_hook, protagonist_state 등) |

**핵심**: Stage 3 복구 + 비용 폭증 방지 + Director 판정 정확도 향상. 이 3건이 없으면 250화 생산 자체가 불가능했음.

---

## 패치 의도 vs 현재 상태 (역산 검증)

### 흐름: 미리 잘 쓰기 → 잘 평가하기 → 피드백으로 잘 고치기

```
[1. 미리 잘 쓰기]          [2. 잘 평가하기]          [3. 피드백으로 잘 고치기]
Blueprint 설계도 생성  →   Director 후보 판정   →   CW 재작성/패치
   │                         │                         │
   패치 1: 스키마 호환       패치 2: 시그니처 정합     패치 3: 무진척 차단
   │                         │                         │
   ✅ HOLDING               ⚠️ 95% (재심사 갭)        ✅ HOLDING
```

### 각 단계 현재 상태

**1단계 — 미리 잘 쓰기 (Blueprint): HOLDING**
- 스키마 에러 즉시 중단 → 헛 재시도 9회 → 1회로 감소
- 프로덕션 Blueprint에 title, ending_hook, protagonist_state 정상 포함
- 설계도 정보량 3필드 → 11필드 — Stage 4 원고 품질 기반 강화

**2단계 — 잘 평가하기 (Director): 95% HOLDING, 재심사 갭 1건**
- 첫 평가: decision_core + candidate_evidence + reference_appendix 3개 팩 정상 전달
- Director가 action_items, score_breakdown, fix_scope, fix_pack으로 구조적 피드백 반환
- **재심사 갭**: `stage4_interview_round.py:3728`의 TF-35 재심사 루프에서 3개 팩 미전달
  - 영향: 패치 후 원고를 재평가할 때 "원래 왜 거부했는지" 컨텍스트 누락
  - 심각도: MEDIUM — 첫 평가는 정상, 재심사만 불완전

**3단계 — 피드백으로 잘 고치기 (CW 재작성): HOLDING + 검증 완료**
- CW는 랜덤 재생성이 **아님**. 3가지 구조적 수정 경로:
  - **inplace**: fix_pack 기반 외과적 장면 수정
  - **patch**: 원본 90% 보존 + 지적사항만 수정 (selected-strategy bounded regenerate 1후보)
  - **full**: 점수 분해 + action_items + "100% 미반영 시 재REJECT" 경고
- 프로덕션 실증: ep_0005에서 패치가 특정 장면만 변경, 나머지 보존
- Stage 4 무진척 시 즉시 중단 → 비용 폭증 방지

### 개악 여부: 개악 아님

3건 패치 모두 의도대로 작동 중. 유일한 잔여 이슈:
- Director 재심사 경로(L3728)에서 판단 근거 3개 파라미터 미전달 — **신규 발견, 별도 패치 대상**
