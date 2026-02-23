# Stage 0~4 통합 감사 보고서 (2026-02-21)

> **소스**: Codex 전수조사 + Antigravity 독립감사 + Opus TF R2~R4 4라운드 감사
> **검증**: 2026-02-21 현행 코드 대조 완료 (커밋 `a89af2d` 기준)

---

## 총괄 요약

| 항목 | 수치 |
|------|------|
| 조사 파일 수 | 23개 (Stage 0~4 + cross-stage) |
| Opus TF 수정 건수 | **24건** (CRITICAL 2, IMPORTANT 21, INSIGHT 1) |
| Opus TF 수정 검증 | **24/24 현행 유지 확인** |
| 미수정 버그 (Codex+Antigravity) | **3건** (CRITICAL 1, MAJOR 2) |
| 미수정 리스크 | **2건** (MEDIUM 1, LOW 1) |
| 해소된 리스크 | **1건** (캐시 무효화 — 정상 구현 확인) |
| 테스트 기준선 | 2,213 passed, 68 xfailed, 0 failures |

---

## Stage 0 — 초기 설정 (세계관/NPC/문체)

### 대상 파일
- `modules/core/stage01_helpers.py`
- `modules/core/stage0/__init__.py`
- `modules/core/stage0/preset_registry.py`
- `modules/core/stage0/reverse_expander.py`
- `modules/core/stage0/story_expander.py`
- `modules/core/stage0/style_extractor.py`
- `modules/core/stage0/spinner.py`

### 구조 평가
- StageZeroManager가 개념생성/역설계/임포트/스타일분석을 통합 관리 (`stage0/__init__.py:39~289`)
- 모드별 핸들러를 명시적 분기 후 단일 경로로 결과 저장 (`stage01_helpers.py:278~320`)
- **구조 건전**: 분기/위임 패턴 정상, 로직 충돌 없음

### 적용된 수정 (Opus TF — 5건, 전량 검증 완료)

| ID | 심각도 | 파일 | 수정 내용 | 검증 |
|----|--------|------|----------|------|
| Fix C | IMPORTANT | `stage0/__init__.py` | Bible 실패 시 Treatment 생성 조기 종료 | ✅ |
| Fix D | IMPORTANT | `style_extractor.py` | 모델명 하드코딩 → AIModels 상수화 | ✅ |
| S0-01 | IMPORTANT | `reverse_expander.py` L108 | UnicodeDecodeError cp949 폴백 | ✅ |
| S0-03 | IMPORTANT | `reverse_expander.py` L166 | load_drafts_from_folder() cp949 폴백 | ✅ |
| S0-04 | IMPORTANT | `reverse_expander.py` L284 | _extract_npcs() dict→list 래핑 | ✅ |
| S0-R4-01 | IMPORTANT | `reverse_expander.py` L277 | _extract_protagonist list→dict 방어 | ✅ |
| S0-R4-02 | IMPORTANT | `reverse_expander.py` L312 | _extract_world_state list→dict 방어 | ✅ |

### 잔여 리스크 (1건)

| ID | 심각도 | 위치 | 내용 |
|----|--------|------|------|
| AG-RISK-02 | LOW | `stage01_helpers.py` 다수 | UIService 미경유 원시 `input()` 산재 — GUI/Headless 전환 시 병목 |

**판정**: Stage 0은 Opus TF 7건 수정 완료 후 **안정**. 잔여 리스크는 향후 UI 추상화 시 일괄 처리 가능.

---

## Stage 1 — 볼륨 플래닝

### 대상 파일
- `modules/core/stage01_helpers.py` (Stage 0과 공유)

### 구조 평가
- skip/진행 분기 후 `plot_roadmap` 복구 시도 → volume planning 루프 (`stage01_helpers.py:498~577`)
- Stage 0과 동일 파일에 통합되어 있으나 로직 경계는 명확

### 적용된 수정
- Stage 0 수정 사항이 공유 파일에 적용 (별도 Stage 1 전용 수정 없음)

### 잔여 이슈
- **없음** — Stage 1 고유 로직에서 결함 미발견

**판정**: Stage 1은 **안정**. 단순 분기 구조로 복잡도 낮음.

---

## Stage 2 — Arc/Blueprint 생성

### 대상 파일
- `modules/core/stage2_context.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage2_preflight.py`
- `modules/core/stage2_validation_pipeline.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/stage2_optimizer.py`

### 구조 평가
- DI context 기반 오케스트레이터 (907줄, 서브모듈 3개 위임)
- preflight/validation/finalizer를 lazy submodule로 분리 (`stage2_orchestrator.py:56~80`)
- 배치 처리 루프에서 enrichment 실패 복구, 재시도, 수동개입 분기까지 안전장치 구비

### 적용된 수정 (Opus TF — 4건, 전량 검증 완료)

| ID | 심각도 | 파일 | 수정 내용 | 검증 |
|----|--------|------|----------|------|
| S2-02 | IMPORTANT | `stage2_finalizer.py` L236 | physical_inventory 문자열→json.loads 리스트 변환 | ✅ |
| S2-03 | IMPORTANT | `stage2_finalizer.py` L260 | items_acquired 비-리스트 타입 방어 | ✅ |
| S2-R4-01 | **CRITICAL** | `stage2_finalizer.py` L190 | PASS+short tactical_doc → REJECT 처리 방지 (조건 분리) | ✅ |
| S2-R4-02 | IMPORTANT | `stage2_validation_pipeline.py` L269 | DraftValidator 폴백 dict "warnings" 키 누락 방어 | ✅ |

### ⛔ 미수정 버그 (1건)

| ID | 심각도 | 위치 | 내용 |
|----|--------|------|------|
| **AG-BUG-01** | **CRITICAL** | `stage2_orchestrator.py` L691, L720, L777 | **async 함수 내 동기 `input()` — Event Loop 전체 블로킹** |

**상세**: `stage_2_arcs_async_logic()`는 `async def` (L86)이나, 에러 복구/수동개입 시 `input()`을 직접 호출. 이벤트 루프가 정지되어 백그라운드 비동기 작업 전량 중단.

**해결 방향**: `await asyncio.to_thread(input, ...)` 래핑 또는 `aioconsole.ainput` 사용.

**판정**: Opus TF 4건 수정으로 데이터 무결성 강화. 단, **async 블로킹 버그 1건 미수정** — CLI 단독 사용 시 체감 영향 낮으나 구조적 결함.

---

## Stage 3 — Blueprint 생성

### 대상 파일
- `modules/core/stage3_context.py`
- `modules/core/stage3_orchestrator.py`
- `modules/domain/agents/three_phase_blueprint_generator.py`

### 구조 평가
- DI context + lazy init (state_tracker/world_state/fact_ledger) 후 episode loop
- arc context 검증 → blueprint 생성 → 성공/실패 핸들러로 닫는 구조
- Entity Registry 캐시: arc_idx 기반 무효화 + 실패 시 `-1` 리셋 — **정상 구현 확인**

### 적용된 수정 (Opus TF — 4건, 전량 검증 완료)

| ID | 심각도 | 파일 | 수정 내용 | 검증 |
|----|--------|------|----------|------|
| Fix E | IMPORTANT | `three_phase_blueprint_generator.py` | stats retry 인플레이션 방지 | ✅ |
| S3-01 | IMPORTANT | `three_phase_blueprint_generator.py` L323 | 연속성 REJECT 후 `_prev_reject_score=0` 리셋 | ✅ |
| S3-02 | IMPORTANT | `three_phase_blueprint_generator.py` L436 | PASS_WITH_WARNING에 score≥REWRITE 게이트 | ✅ |
| S3-R4-01 | IMPORTANT | `three_phase_blueprint_generator.py` L319 | 연속성 REJECT 피드백 전략 변수 설정 | ✅ |
| S3-R4-02 | IMPORTANT | `three_phase_blueprint_generator.py` L433 | stale validation_result → _prev_reject_score + Pydantic 검증 | ✅ |

### ⛔ 미수정 버그 (1건)

| ID | 심각도 | 위치 | 내용 |
|----|--------|------|------|
| **CX-BUG-01** | **MAJOR** | `stage3_orchestrator.py` L113~118 | **입력 범위 역전 — `production_head ≥ total_planned_ep` 시 min>max** |

**상세**: `get_int_input(min_val=production_head+1, max_val=total_planned_ep)` — 모든 블루프린트 완료 시 min=51, max=50처럼 역전. 사용자 입력 불가능 + default 검증 미수행.

**해결 방향**: L113 이전에 `if production_head >= total_planned_ep: return` 조기 종료 가드.

### 해소된 리스크 (1건)

| ID | 원래 심각도 | 판정 |
|----|------------|------|
| AG-RISK-01 | MEDIUM | **해소** — Entity Registry 캐시 무효화 정상 (`_entity_cache_arc_idx = -1` 리셋 L366) |

**판정**: Opus TF 5건 수정 + 캐시 리스크 해소. 단, **입력 범위 역전 버그 1건 미수정** — 블루프린트 전량 완료 후 재진입 시 발현.

---

## Stage 4 — 원고 생성

### 대상 파일
- `modules/core/stage4_context.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/stage4_types.py`

### 구조 평가
- context_builder/interview_round/post_processor lazy init 분리, 메인 루프에서 순차 조립 (883줄)
- interview round: 생성→Python 검증→Director 판정→PASS/REJECT 후속처리
- PASS 후처리: DB 저장/커밋, HUD 업데이트, Episode Bible 및 메타 동기화

### 적용된 수정 (Opus TF — 5건, 전량 검증 완료)

| ID | 심각도 | 파일 | 수정 내용 | 검증 |
|----|--------|------|----------|------|
| Fix F | IMPORTANT | `stage4_interview_round.py` | 빈 원고 후보 Director 전달 차단 | ✅ |
| S4-02 | IMPORTANT | `stage4_post_processor.py` L316 | NPC_Martial_HUD None 방어 | ✅ |
| S4-03 | **CRITICAL** | `stage4_orchestrator.py` L599 | 5회 소진 폴백 시 state_updates 복구 | ✅ |
| S4-R4-01 | IMPORTANT | `stage4_interview_round.py` L759 | REJECT previous_attempt에 state_updates 추가 | ✅ |
| Fix G | IMPORTANT | `chief_writer_quality.py` | 클리셰 카운트에서 현재 원고 제외 | ✅ |

### ⛔ 미수정 버그 (1건)

| ID | 심각도 | 위치 | 내용 |
|----|--------|------|------|
| **CX-BUG-02** | **MAJOR** | `stage4_orchestrator.py` L707~712 | **입력 범위 역전 — `total_planned_ep == 0` 시 min=1, max=0** |

**상세**: `get_int_input(min_val=1, max_val=total_planned_ep)` — 블루프린트 0개 시 범위 역전. `default=None`이므로 빈 입력 시 None 반환 → 후속 로직 불안정.

**해결 방향**: L706 이전에 `if total_planned_ep == 0: return` 조기 종료 가드.

**판정**: Opus TF 5건 수정 (CRITICAL 1건 포함)으로 HUD/사망 데이터 유실 방지 완료. 단, **limit mode 입력 범위 역전 1건 미수정** — 블루프린트 미생성 상태에서 limit mode 진입 시 발현.

---

## Cross-Stage — 공통 인프라

### 대상 파일
- `main_a.py`
- `modules/core/services/ui_service.py`
- `modules/core/db_manager.py`
- `modules/domain/agents/analyst.py`

### 적용된 수정 (Opus TF — 3건, 전량 검증 완료)

| ID | 심각도 | 파일 | 수정 내용 | 검증 |
|----|--------|------|----------|------|
| Fix A | IMPORTANT | `analyst_libraries_composer.json` | 작곡가 장르 라이브러리 신규 (26 archetypes) | ✅ |
| Fix B | IMPORTANT | `analyst.py` | genre_library_map에 composer 등록 | ✅ |
| XC-01 | INSIGHT | `db_manager.py` L289 | ALTER TABLE 마이그레이션 에러 분류 개선 | ✅ |

### 미수정 리스크 (1건)

| ID | 심각도 | 위치 | 내용 |
|----|--------|------|------|
| CX-RISK-01 | MEDIUM | `ui_service.py` L115~117 | `get_int_input()` 빈 입력 시 default를 min/max 검증 없이 즉시 반환 |

**영향**: BUG-01/02와 결합 시 역전 범위의 default가 검증 없이 통과 → 이상 값 전파 가능.

---

## 미수정 이슈 종합 (수정 권고)

### 즉시 수정 필요 (3건)

| 우선순위 | ID | Stage | 심각도 | 요약 |
|----------|-----|-------|--------|------|
| 1 | AG-BUG-01 | 2 | CRITICAL | async 함수 내 동기 `input()` → Event Loop 블로킹 |
| 2 | CX-BUG-01 | 3 | MAJOR | `production_head ≥ total_planned_ep` 시 입력 범위 역전 |
| 3 | CX-BUG-02 | 4 | MAJOR | `total_planned_ep == 0` 시 입력 범위 역전 |

### 개선 권고 (2건)

| 우선순위 | ID | 위치 | 심각도 | 요약 |
|----------|-----|------|--------|------|
| 4 | CX-RISK-01 | UIService | MEDIUM | default 반환 시 min/max 검증 추가 |
| 5 | AG-RISK-02 | Stage 0/1 | LOW | 원시 input() UIService 추상화 |

---

## Opus TF 수정 이력 (24건 전량 검증 완료)

| 라운드 | 커밋 | 건수 | CRITICAL | IMPORTANT | INSIGHT |
|--------|------|------|----------|-----------|---------|
| R2-INSIGHT | `801dff7` | 7 | 0 | 7 | 0 |
| R3 1차 | `62240e2` | 6 | 0 | 5 | 1 |
| R3 2차 | `e5cd941` | 4 | 1 | 3 | 0 |
| R4 | `a114c38` | 7 | 1 | 6 | 0 |
| **합계** | | **24** | **2** | **21** | **1** |

### 오탐 통계

| 라운드 | 초기 보고 | 오탐/스킵 | 실제 수정 | 오탐률 |
|--------|-----------|-----------|-----------|--------|
| R3 1차 | 38 | 32 | 6 | 84% |
| R3 2차 | 21 | 17 | 4 | 81% |
| R4 | 8 | 1 | 7 | 13% |

---

## 최종 판정

| Stage | 상태 | 미수정 건수 | 비고 |
|-------|------|------------|------|
| **Stage 0** | ✅ 안정 | 0 (LOW 리스크 1) | Opus 7건 수정 완료 |
| **Stage 1** | ✅ 안정 | 0 | 고유 결함 없음 |
| **Stage 2** | ⚠️ 주의 | 1 (CRITICAL) | async input() 블로킹 |
| **Stage 3** | ⚠️ 주의 | 1 (MAJOR) | 입력 범위 역전 |
| **Stage 4** | ⚠️ 주의 | 1 (MAJOR) | 입력 범위 역전 |
| **Cross** | ⚠️ 주의 | 1 (MEDIUM 리스크) | UIService default 검증 |

**전체**: Opus TF 24건 수정으로 데이터 무결성·인코딩·타입 안전성 대폭 개선. 잔여 3건은 UX/제어흐름 결함으로 데이터 손실 위험은 낮으나, 엣지 케이스 사용자 경험 저하 및 async 아키텍처 위반 존재.
