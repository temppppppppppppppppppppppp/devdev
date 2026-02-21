# Opus TF R3 전 스테이지 감사 보고서

**날짜**: 2026-02-21
**커밋**: `801dff7` (R2-INSIGHT) → `62240e2` (R3) → `e5cd941` (R3-2)
**테스트**: 2,213 passed, 68 xfailed, 0 failures

---

## 1. R2-INSIGHT 수정 (커밋 `801dff7`)

| ID | 파일 | 수정 내용 |
|----|------|----------|
| Fix A | `analyst_libraries_composer.json` | 작곡가 장르 라이브러리 신규 (26 archetypes) |
| Fix B | `analyst.py` | genre_library_map에 composer 등록 |
| Fix C | `stage0/__init__.py` | Bible 실패 시 Treatment 생성 조기 종료 |
| Fix D | `stage0/style_extractor.py` | 모델명 하드코딩 → AIModels 상수화 |
| Fix E | `three_phase_blueprint_generator.py` | stats retry 인플레이션 방지 |
| Fix F | `stage4_interview_round.py` | 빈 원고 후보 Director 전달 차단 |
| Fix G | `chief_writer_quality.py` | 클리셰 카운트에서 현재 원고 제외 |

---

## 2. R3 1차 감사 (커밋 `62240e2`)

### 2.1 조사 범위

5개 병렬 에이전트로 Stage 0/2/3/4 + Cross-stage 전면 감사.
총 ~20,000줄 조사, 초기 보고 38건 → 오탐 제거 후 10건 → 재검증 후 6건 확정.

### 2.2 오탐 확인 (14건)

| 보고 이슈 | 판정 | 근거 |
|-----------|------|------|
| S0: split IndexError (style_extractor L697) | 오탐 | try-except 내부 |
| S0: max() 빈 리스트 (reverse_expander L813) | 오탐 | L808 가드 |
| S0: shallow copy (story_expander L273) | 오탐 | append만, 기존 수정 없음 |
| S2: recovery index OOB (orchestrator L293) | 오탐 | batch 범위 내 보장 |
| S2: cache key None (finalizer L334) | 오탐 | None==0 → False |
| S4: ternary index (interview_round L251) | 오탐 | Python ternary 조건 우선 |
| S4: validator 길이 불일치 (L323-384) | 오탐 | 가드 존재 |
| XC: RLock 데드락 (db_manager L1125) | 오탐 | RLock 재귀 정상 |
| XC: 리스트 역순 (db_manager L1447) | 설계 | 성능 선호 |
| S4-01: 빈 NPC 이름 사망목록 | 설계 의도 | 하류 필터링 |
| S2-01: arc_context_fallback 빈 리스트 | 호출자 가드 | 모든 호출자 체크 |
| S3-03: feedback 누적 | 수용 가능 | _attempt_feedback 리셋, logging만 |
| S2-03: enriched_block 뮤테이션 | 설계 의도 | 연속성 수정 persistence |

### 2.3 수정 완료 (6건)

| ID | 심각도 | 파일 | 수정 내용 |
|----|--------|------|----------|
| S3-01 | IMPORTANT | `three_phase_blueprint_generator.py` L323 | 연속성 REJECT 후 `_prev_reject_score=0` 리셋 (패치모드 오활성화 차단) |
| S3-02 | IMPORTANT | `three_phase_blueprint_generator.py` L432 | PASS_WITH_WARNING에 `score >= REWRITE(50)` 게이트 (Director 주권주의) |
| S4-02 | IMPORTANT | `stage4_post_processor.py` L316 | NPC_Martial_HUD None 방어 (`or {}` 패턴) |
| S2-02 | IMPORTANT | `stage2_finalizer.py` L236 | physical_inventory 문자열 → json.loads 리스트 변환 |
| S0-01 | IMPORTANT | `reverse_expander.py` L108 | load_drafts_from_file() UnicodeDecodeError cp949 폴백 |
| XC-01 | INSIGHT | `db_manager.py` L289 | ALTER TABLE 마이그레이션: duplicate column/already exists 외 에러 재발생 |

### 2.4 수정 감리 결과

6건 전부 **정상** (별도 에이전트 검증):
- S3-01: 정상 Director REJECT → 패치모드 흐름 미파괴 확인
- S3-02: PatchModeThresholds.REWRITE 스코프 내 import 확인, 50 미만 FAILED 정상
- S4-02: `or {}` 패턴 None + 미존재 키 모두 처리 확인
- S2-02: json.loads 비-리스트 반환 시 L261 isinstance 가드 확인
- S0-01: cp949 폴백 실패 시 정상 예외 전파 확인
- XC-01: f-string SQL 안전 (하드코딩 리터럴), SQLite 버전간 에러 메시지 호환 확인

---

## 3. R3-2 재조사 (커밋 `e5cd941`)

### 3.1 조사 범위

R3 수정 후 6개 병렬 에이전트로 전 스테이지 재조사.
~20,000줄 재조사, 초기 보고 21건 → 오탐 제거 후 4건 확정.

### 3.2 오탐 확인 (17건)

| 보고 이슈 | 판정 | 근거 |
|-----------|------|------|
| S0-02: 따옴표 동일 문자 중복 (style_extractor L364) | 스킵 | 동작 영향 없음 |
| S0-05: _parse_json 반환 타입 어노테이션 | 스킵 | 어노테이션, 런타임 무관 |
| S2-B2: 배치 복구 인덱스 매핑 | 오탐 | 에이전트 자체 정정 (로직 정확) |
| S3-04: 무결성 실패 루프 break | 스킵 | break 후 next_ep 미사용 |
| S3-05: 품질 게이트 패치모드 | 스킵 | 점수 기반 패치 유효한 전략 |
| S3-06: 전략 페널티 | 스킵 | INSIGHT, 설계 트레이드오프 |
| XC-B1: CREATE TABLE 커밋 누락 | 오탐 | SQLite DDL 오토커밋 |
| XC-B2: 다중 CREATE 커밋 | 오탐 | 동일 |
| XC-B3: 캐시 무효화 >= vs > | 오탐 | 의도적 (save=현재포함, delete=현재제외) |
| XC-B4: VecMemory 스키마 분리 | 스킵 | 별도 DB, 런타임 충돌 없음 |
| XC-B5: 컨텍스트 캐시 경합 | 스킵 | 이론적 TOCTOU, 현 사용 패턴에서 미발현 |
| S4-B2: 검증 길이 불일치 로깅 | 스킵 | 가드 존재, 로깅 개선 수준 |
| S4-B3: 폴백 제목 기본값 | 스킵 | INSIGHT |
| S2-B3: 인벤토리 타입 혼재 | 스킵 | 설계 허용 범위 |

### 3.3 수정 완료 (4건)

| ID | 심각도 | 파일 | 수정 내용 |
|----|--------|------|----------|
| S0-03 | IMPORTANT | `reverse_expander.py` L166 | load_drafts_from_folder() cp949 폴백 (S0-01 동일 패턴) |
| S0-04 | IMPORTANT | `reverse_expander.py` L284 | _extract_npcs() dict→list 래핑 (LLM 단일 NPC 대응) |
| S2-03 | IMPORTANT | `stage2_finalizer.py` L260 | items_acquired 비-리스트 타입 방어 |
| S4-03 | CRITICAL | `stage4_orchestrator.py` L598 | 5회 소진 폴백 시 state_updates 복구 (HUD/사망 데이터 유실 방지) |

---

## 4. 전체 요약

### 수정 통계

| 라운드 | 커밋 | 수정 건수 | 파일 수 |
|--------|------|-----------|---------|
| R2-INSIGHT | `801dff7` | 7건 (신규 1 + 수정 6) | 7 |
| R3 1차 | `62240e2` | 6건 | 5 |
| R3 2차 | `e5cd941` | 4건 | 3 |
| **합계** | | **17건** | **15 (중복 제외 12)** |

### 오탐 통계

| 라운드 | 초기 보고 | 오탐/스킵 | 실제 수정 | 오탐률 |
|--------|-----------|-----------|-----------|--------|
| R3 1차 | 38건 | 32건 | 6건 | 84% |
| R3 2차 | 21건 | 17건 | 4건 | 81% |

### 심각도 분포

| 심각도 | R2-INSIGHT | R3 1차 | R3 2차 | 합계 |
|--------|-----------|--------|--------|------|
| CRITICAL | 0 | 0 | 1 | 1 |
| IMPORTANT | 7 | 5 | 3 | 15 |
| INSIGHT | 0 | 1 | 0 | 1 |

### 잔여 이슈

**없음** — 전 스테이지 2회 감사 완료, 수정 가치 있는 이슈 전량 해결.

---

## 5. 수정 대상 파일 전체 목록

| 파일 | R2-I | R3 | R3-2 |
|------|------|----|------|
| `config/prompts/analyst_libraries_composer.json` | 신규 | | |
| `modules/domain/agents/analyst.py` | B | | |
| `modules/core/stage0/__init__.py` | C | | |
| `modules/core/stage0/style_extractor.py` | D | | |
| `modules/core/stage0/reverse_expander.py` | | S0-01 | S0-03, S0-04 |
| `modules/domain/agents/three_phase_blueprint_generator.py` | E | S3-01, S3-02 | |
| `modules/core/stage4_interview_round.py` | F | | |
| `modules/domain/agents/chief_writer_quality.py` | G | | |
| `modules/core/stage4_post_processor.py` | | S4-02 | |
| `modules/core/stage2_finalizer.py` | | S2-02 | S2-03 |
| `modules/core/db_manager.py` | | XC-01 | |
| `modules/core/stage4_orchestrator.py` | | | S4-03 |
