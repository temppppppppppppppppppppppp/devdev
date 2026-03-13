# OPUS TF Terminal 3 — Stage 3→4 파이프라인 전량 조사 보고서

> **작성일**: 2026-03-13
> **범위**: Stage 3 (Blueprint) + Stage 4 (원고) + Chief Writer 체인 + adaptive_retry + 관련 테스트
> **파일 수**: 프로덕션 19개 + Config 4개 + 테스트 18개
> **총 라인**: ~27K (프로덕션) + ~15K (테스트)
> **5Pass 감리 완료**: 원본 53건 → 오탐 13건 제거 + severity 조정 9건 → **최종 40건**

---

## 요약

| Severity | 건수 | 비고 |
|----------|------|------|
| **P0** | 0 | - |
| **P1** | 3 | 핸드오프 테스트, Advisory 병렬 테스트, 대원칙 3 위반 |
| **P2** | 4 | scene_keys 정렬, 스레드 경합, Self-Critique 타입 혼재 |
| **P3** | 33 | Dead code, docstring 불일치, 의도적 trade-off 문서화 등 |
| **합계** | **40건** | |
| ~~오탐 제거~~ | ~~13건~~ | 5Pass 감리로 제거 |

**대원칙 준수 현황**: 대원칙 1·2·4 전량 준수. **대원칙 3 위반 의심 1건** (T3-003, continuity pin이 Director PASS를 무효화).

---

## 5Pass 감리 기록

### Pass 1 — P1 4건 실제 코드 검증
- [x] T3-001: **오탐**. `_extract_json_robust()`가 모든 경로에서 dict 반환 확인. 추가로 outer except가 있어 이중 방어.
- [x] T3-002: **오탐**. T3-001과 동일 근거. `self.ask()`는 항상 str 반환 → `isinstance(result, str)` 항상 True → `_extract_json_robust` 항상 호출 → 항상 dict.
- [x] T3-003: **진탐**. 테스트 스위트 전체에서 `handoff`, `cross.*stage`, `blueprint.*stage4` 검색 0건.
- [x] T3-004: **진탐**. `_run_advisory_chain` MagicMock 완전 대체 확인. ThreadPoolExecutor/timeout/부분실패 테스트 0건.

### Pass 2 — P2 Stage3/4 Core 13건 검증
- [x] T3-005: **오탐**. `fail_count`는 "연속 실패 카운터"이며, 에피소드 성공 시 0 리셋은 표준 패턴. L566 초기화 + L1976 증가 확인.
- [x] T3-006: **진탐** (severity LOW). `sorted()` 사전순 → 10+씬에서 오류. 단, `end_location` 폴백 경로 + 추가 검증으로 실피해 낮음.
- [x] T3-007: **진탐** (P2). `enrich_all_blocks_parallel` L693에서 동일 인스턴스 멀티스레드 사용 확인. `[V70]` 코멘트는 단일스레드 예외만 방어.
- [x] T3-008: **오탐**. 주석에 의도적 fail-open 명시 ("Block 자체 문제 아님"). validate=fail-closed vs audit=fail-open 정책 분리 확인.
- [x] T3-009: **부분오탐** → P3 하향. 30자 한국어 우연 일치 확률 극히 낮음. `len > 10` 가드 존재.
- [x] T3-010: **오탐**. `_god1_*`는 매 `run()` 호출 시 L1435-1440에서 새 값 덮어쓰기. `getattr(self, ..., default)` 패턴으로 미할당도 안전.
- [x] T3-011: **부분오탐** → P3 하향. 비용 trade-off 의도적 설계. round 0 conflict → director_feedback 반영 → CW 재작성.
- [x] T3-012: **오탐**. "첫 번째 non-empty만" 가져가는 의도적 패턴. `shared_failure_warnings`는 blocking_validator만 생성.
- [x] T3-013: **부분오탐** → P3 하향. `[V64.P4] OPTIONAL: 비차단` 주석 확인. 내부 개별 except 충분. 340행 범위는 사실이나 최후 안전망.
- [x] T3-014: **오탐**. CLAUDE.md 명시: "PASS_WITH_FIX는 bypass (Director 주권 존중)". 대원칙 3 준수.
- [x] T3-015: **오탐**. `[TF-S4-01]` 태그로 소실 방지 명시. `previous_attempt["state_updates"]`에 보존 → `final_manuscript = None` → Phase 5 미진입.
- [x] T3-016: **오탐**. `_meta_save_failed=True` 시 False 반환 → 오케스트레이터 집필 중단은 fail-safe 의도. `[S4-001]`/`[Sweep46]` 태그 확인.
- [x] T3-017: **부분오탐** → P3 하향. fail-closed 자체는 `[FailClosed:SC:...]` 태그로 의도적. transient 에러 시 불필요 REJECT 1회 가능하나 영구 차단 아님.

### Pass 3 — P2 ChiefWriter + adaptive_retry 8건 검증
- [x] T3-018: **진탐** (P2). L766/L773 string → `i.get("severity")` 에스컬레이션 무시 확인. 다만 `len(issues)` 카운트에는 기여.
- [x] T3-019: **진탐** (P2). T3-018과 동일 패턴 확인.
- [x] T3-020: **오탐**. 30KB guard는 JSON 구조체(Arc/Blueprint) 한정. plain text 원고는 `smart_truncate` 150KB 절단이 합리적. CLAUDE.md 기술도 Arc/Blueprint 문맥.
- [x] T3-021: **진탐** → P3 하향. JSON 파싱 실패 자체가 드문 경로. 과대 계산은 false-negative 방향 (경고 미발생) → Director가 별도 감지.
- [x] T3-022: **오탐**. `FailureLearner._classify_and_record()` L538-548에서 2단계 분류 존재. 3개 신규 타입 키워드 오버라이드 확인.
- [x] T3-023: **부분오탐** → P3 하향. `_check_ending_novelty` 테스트 부재만 진탐. "#11 감정고착" 메서드 자체 미존재 (오탐). 단순 n-gram Jaccard.
- [x] T3-024: **진탐** → P3 하향. 경계 테스트 부재는 사실이나 설정값 경계이므로 실질 버그 가능성 낮음.
- [x] T3-025: **진탐** → P3 하향. `update_from_state_changes` mock 세팅만 있고 `assert_called_with` 부재 확인.
- [x] T3-026: **오탐**. `test_stage4_cv_context.py` 파일 존재 + destroyed/timeline 관련 mock 세팅 확인.

### Pass 4 — P3 핵심 8건 오탐 스팟체크
- [x] T3-028: **진탐**. `build_external_pov_policy_constraint()` 무조건 호출 → L475-484 항상 덮어써짐.
- [x] T3-029: **진탐 + severity 상향 (P3→P1)**. Director PASS 후 `apply_continuity_pins` 미해결 → fail_count+1 + blueprint 미저장. **대원칙 3 위반**: Director가 승인한 Blueprint를 Python 로직이 폐기.
- [x] T3-031: **오탐**. `three_phase_blueprint_generator`가 PASS_WITH_FIX를 항상 PASS/REJECT로 resolve 확인.
- [x] T3-033: **진탐**. `Stage4Context.__slots__`에 `_director_mc_parts` 없음 → `getattr` 항상 None.
- [x] T3-036: **진탐**. `add_episode_emotion` 호출 전 코드베이스에서 1곳뿐. 실 분석 없이 고정값.
- [x] T3-040: **진탐**. 코드 17개 + 분량재검사 1건 = 18개. CLAUDE.md "15개" outdated.
- [x] T3-046: **진탐**. `_CW_GENRE_CODE_MAP` 참조 0건. `normalize_chief_writer_genre_code` import 사용 중.
- [x] T3-047: **부분오탐**. 7개 키 외 fallback으로 원본 text 반환은 의도적 안전 설계. "결함"보다는 방어적 패턴.

### Pass 5 — 최종 정합성 (본 문서)
- [x] 오탐 13건 제거 반영
- [x] severity 조정 9건 반영 (P2→P3: 8건, P3→P1: 1건)
- [x] 번호 재배정 없이 원본 ID 유지 (추적성)
- [x] 액션 플랜 갱신
- [x] 교차 검증 항목 갱신

---

## P1 — IMPORTANT (3건)

### [T3-003] Blueprint→Manuscript 핸드오프 통합 테스트 부재
- **Severity**: P1 (테스트 갭)
- **파일**: 전체 테스트 스위트
- **현상**: Stage 3 출력 blueprint 구조와 Stage 4 입력 요구 필드 간 **end-to-end 교차 검증 테스트 없음**. 각각 서로 다른 stub 사용
- **근거**: `test_stage3_orchestrator.py`는 `{"integrated_scenario": "ok"}`, `test_stage4_context_builder.py`는 `blueprint={}` — 필드 셋 정합성 미검증
- **수정안**: Stage 3 출력 스키마 ↔ Stage 4 입력 스키마 계약 테스트 추가
- **5Pass**: Pass 1 진탐 확정. 테스트 스위트 전체 검색으로 교차 검증 테스트 부재 확인.

### [T3-004] Advisory Chain `_run_advisory_chain` 병렬 실행 직접 테스트 부재
- **Severity**: P1 (테스트 갭)
- **파일**: `tests/test_stage4_interview_round.py`
- **현상**: 8개 advisory ThreadPoolExecutor 병렬 실행, per-advisory timeout 60s, 부분 실패 graceful degradation — 전부 MagicMock으로 대체됨
- **근거**: L288에서 `ir._run_advisory_chain = MagicMock(return_value=[...])` — 실제 병렬 환경 미검증
- **수정안**: advisory 타임아웃 초과, 부분 실패, 전원 성공 3경로 단위 테스트 추가
- **5Pass**: Pass 1 진탐 확정. ThreadPoolExecutor/timeout 테스트 0건 확인.

### [T3-029] `stage3_orchestrator._handle_success` — Director PASS를 continuity pin이 무효화 (**대원칙 3 위반**)
- **Severity**: P1 (P3에서 상향)
- **파일**: `modules/core/stage3_orchestrator.py` L1479-1492
- **현상**: Director가 PASS 판정한 Blueprint를 `apply_continuity_pins`의 `unresolved` 결과가 무효화. `fail_count + 1` 증가 + `success_count` 미증가 + **Blueprint DB 저장 skip** (L1505-1506 미도달)
- **근거**: 대원칙 3 "디렉터 주권주의 — Director가 최종 품질 결정권. Director를 우회하면 안 됨". Python 로직(`apply_continuity_pins`)이 Director PASS를 사후 오버라이드하여 Blueprint를 폐기함.
- **수정안**: Director PASS Blueprint는 저장하되, continuity pin 미해결 경고를 다음 에피소드 컨텍스트에 주입. 또는 continuity pin 결과를 Director 심사 전에 주입하여 Director가 인지한 상태에서 판정.
- **5Pass**: Pass 4 진탐 확정 + severity 상향. L1479-1505 코드 경로에서 Director PASS 후 Python 폐기 확인.

---

## P2 — MODERATE (4건)

### [T3-006] `unified_blueprint_validator` — scene_keys 알파벳 정렬 (숫자 아님)
- **Severity**: P2
- **파일**: `modules/domain/agents/unified_blueprint_validator.py` L413
- **현상**: `sorted(prev_scenes.keys())` — `scene_10`이 `scene_2` 앞에 정렬됨 → "마지막 씬" 추출 오류
- **근거**: `scene_keys[-1]`이 사전순 마지막(`scene_9`)을 반환. 10+ 씬에서 잘못된 씬 참조.
- **수정안**: `blueprint_constraint_compiler.py` L283과 동일한 숫자 정렬 사용
- **5Pass**: Pass 2 진탐 확정. 단, `end_location` 폴백 + 추가 검증으로 실피해 낮음(severity LOW).

### [T3-007] `block_enricher._validate_enrichment` — self.primary_model 변경이 스레드 안전하지 않음
- **Severity**: P2
- **파일**: `modules/domain/agents/block_enricher.py` L480-485
- **현상**: `ThreadPoolExecutor` 병렬 실행 중 `self.primary_model` 인스턴스 변수를 swap → 레이스 컨디션
- **근거**: `enrich_all_blocks_parallel` L693에서 동일 인스턴스를 멀티스레드 사용. `[V70]` 코멘트의 try/finally는 단일스레드 예외만 방어.
- **수정안**: model을 `self.ask()` 파라미터로 전달하거나, per-thread 인스턴스 분리
- **5Pass**: Pass 2 진탐 확정. 실 영향: 잘못된 모델로 ask() 호출 가능.

### [T3-018] Self-Critique #6 `_check_writing_directive` — str/dict 혼재 issues
- **Severity**: P2
- **파일**: `modules/domain/agents/chief_writer_quality.py` L754-789
- **현상**: L766/L773은 plain string append, L781은 dict append → L343 `i.get("severity")` 에서 string은 항상 무시됨
- **근거**: severity 에스컬레이션에서 WritingDirective expression_ban 위반이 카운트되지 않음. 다만 `len(issues)` 카운트에는 기여.
- **수정안**: 전부 dict 형식으로 통일 (`type`, `description`, `severity` 키)
- **5Pass**: Pass 3 진탐 확정. 실질 영향은 LOW — severity 에스컬레이션 누락이나 `len` 기반 임계값에는 기여.

### [T3-019] Self-Critique #7 `_check_expression_freshness` — string-only issues
- **Severity**: P2
- **파일**: `modules/domain/agents/chief_writer_quality.py` L791-803
- **현상**: T3-018과 동일 패턴 — plain string만 반환 → severity 에스컬레이션에서 무시됨
- **수정안**: dict 형식으로 통일
- **5Pass**: Pass 3 진탐 확정. T3-018과 동일 근거.

---

## P3 — MINOR (33건)

### 의도적 설계로 하향된 항목 (P2→P3, 8건)

> 5Pass 감리에서 의도적 설계/trade-off로 확인되어 P2에서 하향. 개선 가치는 있으나 결함은 아님.

| ID | 파일 | 현상 | 하향 사유 |
|----|------|------|----------|
| T3-009 | `unified_blueprint_validator.py` L394 | 30자 substring CRITICAL 경고 — 이론적 오탐 | `len > 10` 가드 + 30자 한국어 우연 일치 극히 낮음 |
| T3-011 | `stage4_interview_round.py` L2470 | post-select round 0만 실행 | 비용 trade-off 의도적 설계. conflict→feedback→CW 재작성 체인 |
| T3-013 | `stage4_post_processor.py` L790 | outer try-except 340행 범위 | `[V64.P4] OPTIONAL: 비차단` 주석. 내부 개별 except 충분 |
| T3-017 | `stage4_interview_round.py` L2519 | fail-closed + round-0-only | `[FailClosed:SC:]` 태그 의도적. transient 에러 시 불필요 REJECT 1회 가능하나 영구 차단 아님 |
| T3-021 | `chief_writer_quality.py` L324 | JSON 파싱 실패 시 len 과대 | 드문 경로 + false-negative 방향 (경고 미발생) → Director 별도 감지 |
| T3-023 | `test_chief_writer_quality.py` | `_check_ending_novelty` 테스트 부재 | "#11 감정고착" 메서드 미존재(오탐). 잔여 `ending_novelty`만 미테스트, 단순 n-gram |
| T3-024 | `test_base_agent.py` | 50K 경계 테스트 부재 | 설정값 경계이므로 실질 버그 가능성 낮음 |
| T3-025 | `test_stage4_post_processor.py` | `update_from_state_changes` 인자 미검증 | mock 세팅 존재, `assert_called_with`만 부재 |

### 원본 P3 (25건)

| ID | 파일 | 현상 |
|----|------|------|
| T3-027 | `blueprint_ensemble.py` L505-552 | 캐시 활성 시 프롬프트 이중 조립 → O(N) 비용 중복 |
| T3-028 | `blueprint_ensemble.py` L473-494 | `_pov_constraint` 첫 번째 할당이 dead code (진탐 확정) |
| T3-030 | `stage3_orchestrator.py` L1099 | arc_idx `>=` 체크 — 현재 safe하나 fragile |
| T3-032 | `blueprint_constraint_compiler.py` L281 | `scene_breakdown` list 타입 시 연속성 추출 전체 skip |
| T3-033 | `stage4_post_processor.py` L1082-1084 | causal graph Director MC 주입 dead code (진탐 확정, `__slots__` 미등록) |
| T3-034 | `stage4_context_builder.py` L1708-1721 | DB 내부 `_lock`/`conn` 직접 접근 → public API 우회 |
| T3-035 | `stage4_post_processor.py` L1148, L1152 | `_state`/`_ledger` private 접근으로 rollback snapshot |
| T3-036 | `stage4_post_processor.py` L487 | EmotionArcTracker 하드코딩 "neutral" 0.5 (진탐 확정, 호출 1곳뿐) |
| T3-037 | `stage4_context_builder.py` L1723-1729 | Tier 2 summary sqlite3.Row vs tuple 타입 미처리 |
| T3-038 | `stage4_interview_round.py` L1318-1319 | `mandatory_context` 변이 체인 불투명 |
| T3-039 | `stage4_interview_round.py` L2594-2596 | docstring 반환 5-tuple ≠ 실제 6-tuple |
| T3-040 | `chief_writer_quality.py` L267-338 | Self-Critique 번호 불일치 — CLAUDE.md 15개 vs 코드 17+1개 (진탐 확정) |
| T3-041 | `chief_writer.py` L677-678 | JSON 파싱 실패 시 무경고 None 반환 |
| T3-042 | `chief_writer.py` L1660 | `_rejected_strategy` 빈 문자열 시 3후보 전체 생성 → 3배 LLM 비용 |
| T3-043 | `chief_writer_quality.py` L169, L298 | `_check_ending_hook_presence` 이중 호출 (gate + critique) |
| T3-044 | `chief_writer_quality.py` L176, L304 | `_check_system_term_exposure` 이중 호출 (gate + critique) |
| T3-045 | `chief_writer_quality.py` L694-696 | `_check_npc_relationship` DOTALL — 전체 원고 범위 매칭 오탐 가능 |
| T3-046 | `chief_writer.py` L37-48 | `_CW_GENRE_CODE_MAP` dead code (진탐 확정, 참조 0건) |
| T3-047 | `chief_writer.py` L1502-1529 | 미인식 JSON 키 시 원본 text 반환 — 의도적 방어 fallback (부분오탐) |
| T3-048 | `writer_template.py` L349-359 | `validate_against_template` scene coverage — 프로덕션 미사용 |
| T3-049 | `chief_writer.py` L1084 | global focus 시 빈 dict 반환 — 의도적이나 debug 로그 없음 |
| T3-050 | `tests/stage3_isolated_test/*.py` | E2E 테스트 CI 가드 없음 (`pytest.mark.skip` 미적용) |
| T3-051 | (없음) | `test_stage4_canary.py` 파일 미존재 |
| T3-052 | `test_stage4_context_builder.py` | prev_text None 폴백 테스트 부재 |
| T3-053 | `test_chief_writer_quality.py` | POV 일관성 체크 경계 조건 미테스트 (단일 케이스만) |

---

## 오탐 제거 기록 (13건)

> 5Pass 감리에서 제거된 항목. 원본 ID 보존하여 추적성 유지.

| 원본 ID | 원본 Severity | 오탐 사유 |
|---------|-------------|----------|
| T3-001 | P1 | `_extract_json_robust()`가 모든 경로에서 dict 반환. outer except도 이중 방어. |
| T3-002 | P1 | T3-001과 동일. `self.ask()` 항상 str → `_extract_json_robust` 항상 호출 → 항상 dict. |
| T3-005 | P2 | `fail_count`는 "연속 실패 카운터". 성공 시 0 리셋은 표준 패턴. |
| T3-008 | P2 | 주석에 의도적 fail-open 명시 ("Block 자체 문제 아님"). validate/audit 정책 분리. |
| T3-010 | P2 | 매 `run()` 호출 시 새 값 덮어쓰기. `getattr(self, ..., default)` 패턴으로 미할당도 안전. |
| T3-012 | P2 | "첫 번째 non-empty만" 가져가는 의도적 패턴. `shared_failure_warnings`는 단일 validator만 생성. |
| T3-014 | P2 | CLAUDE.md 명시: "PASS_WITH_FIX는 bypass (Director 주권 존중)". 대원칙 3 의도적 준수. |
| T3-015 | P2 | `[TF-S4-01]` 태그로 소실 방지 설계 명시. `previous_attempt`에 보존. |
| T3-016 | P2 | `_meta_save_failed` 시 집필 중단은 fail-safe 의도. `[S4-001]`/`[Sweep46]` 태그 확인. |
| T3-020 | P2 | 30KB guard는 JSON 구조체(Arc/Blueprint) 한정. plain text 원고는 150KB truncation이 합리적. |
| T3-022 | P2 | `FailureLearner._classify_and_record()` L538-548에서 2단계 분류 존재. 3개 신규 타입 정상 분류. |
| T3-026 | P2 | `test_stage4_cv_context.py` 파일 존재 + destroyed/timeline mock 세팅 확인. |
| T3-031 | P3 | `three_phase_blueprint_generator`가 PASS_WITH_FIX를 항상 PASS/REJECT로 resolve. |

---

## 우선순위 액션 플랜

### 즉시 수정 (P1, 3건)

| ID | 작업 | 예상 규모 | 긴급도 |
|----|------|----------|--------|
| **T3-029** | continuity pin이 Director PASS를 무효화하지 않도록 수정 — pin 결과를 Director 심사 전 주입 또는 PASS Blueprint 저장 + 경고 주입 | 15줄 | **대원칙 3 위반** |
| T3-003 | Blueprint↔Manuscript 필드 계약 테스트 신규 | ~50줄 | 스키마 불일치 사전 탐지 |
| T3-004 | Advisory Chain 병렬 실행 단위 테스트 신규 (timeout/부분실패/전원성공) | ~80줄 | 병렬 실행 안전성 |

### 1차 배치 (P2 프로덕션, 4건)

| ID | 작업 | 예상 규모 |
|----|------|----------|
| T3-006 | scene_keys 숫자 정렬 (`sorted(keys(), key=lambda k: int(re.search(r"\d+", k).group()) if re.search(r"\d+", k) else 0)`) | 2줄 |
| T3-007 | primary_model swap 대신 ask() 파라미터 전달 또는 per-thread 인스턴스 | 8줄 |
| T3-018 | `_check_writing_directive` issues를 dict 형식으로 통일 | 6줄 |
| T3-019 | `_check_expression_freshness` issues를 dict 형식으로 통일 | 4줄 |

### 2차 배치 (P3, 33건)

P3 33건 중 우선순위 TOP 5:
1. **T3-033** (dead code 제거) — causal graph MC 주입 dead code
2. **T3-046** (dead code 제거) — `_CW_GENRE_CODE_MAP`
3. **T3-040** (문서 정합) — CLAUDE.md Self-Critique 번호 업데이트
4. **T3-028** (dead code 제거) — `_pov_constraint` 첫 번째 할당
5. **T3-036** (기능 누락) — EmotionArcTracker 실 분석 or 제거

나머지 28건 — 마스터 취합 후 일괄 진행

---

## 교차 검증 필요 항목 (T2/T4 터미널 경계)

- **T3-003 ↔ T2**: Stage 2 → Stage 3 핸드오프도 동일 패턴 미검증 가능성
- **T3-004 ↔ T4**: Advisory Chain 조립은 T4 Director 범위와 중첩 — 양쪽 보고서 대조 필요
- **T3-029 ↔ T4**: continuity pin이 Director 주권을 침해하는지 T4(Director 체계) 보고서와 대조 필요

---

## 통계

| 구분 | 건수 |
|------|------|
| 원본 발견 | 53건 |
| 5Pass 오탐 제거 | -13건 |
| 최종 진탐 | **40건** |
| P2→P3 하향 | 8건 |
| P3→P1 상향 | 1건 (T3-029) |
| **오탐률** | 24.5% (13/53) |
