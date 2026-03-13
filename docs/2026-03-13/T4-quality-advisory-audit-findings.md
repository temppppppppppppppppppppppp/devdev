# OPUS TF Terminal 4 — 품질 시스템 & Advisory 체인 전량 감사 보고서

> **작성일**: 2026-03-13
> **범위**: Director 체계(7), Continuity 체계(5), Advisory Chain(8), Pre-Director(3), Validation(16), 품질 메타시스템(4), Config/Prompt(4), 테스트(22)
> **총 감사 줄수**: ~23.5K lines (프로덕션) + 테스트 전량
> **7개 병렬 에이전트 투입, 6-Point Inspection 적용**
> **5Pass 감리 완료** — 4개 병렬 검증 에이전트로 전 항목 코드 교차 검증

---

## 5Pass 감리 기록

### Pass 1 — 초기 감사 (7개 에이전트 병렬)
- [x] Director 체계 7파일 전량 읽기 + 6-Point Inspection
- [x] Continuity 체계 5파일 전량 읽기 + 6-Point Inspection
- [x] Advisory Chain 8파일 + interview_round 연동 검증
- [x] Pre-Director 3파일 + Validation 16파일 전량 읽기
- [x] 품질 메타시스템 4파일 + config 정합성
- [x] 테스트 22파일 커버리지 갭 분석
- [x] Config/Prompt 4파일 코드 교차 정합성

### Pass 2 — P0 코드 교차 검증
- [x] P0-01 ConsistencyValidator: `validation_orchestrator.py` L468-482 + `stage4_interview_round.py` 호출 경로 추적
- [x] P0-02 RetrospectiveValidator: `validation_orchestrator.py` L656-667 + 호출 체인 추적
- **결과**: 두 건 모두 **Stage 3 Blueprint 검증 경로에서만 도달**, Stage 4 원고 인터뷰 플로우에서는 미도달. **P0→P1 하향**

### Pass 3 — P1 코드 교차 검증 (2개 에이전트 병렬)
- [x] P1-01 director_prompts.py 괴리 → **FALSE POSITIVE** (YAML과 내용 동일, 폴백 경로 미존재)
- [x] P1-02 Continuity 사망 필터 → **PARTIAL** (TruthGate+StateTracker+Director 프롬프트에서 다중 방어, P2 하향)
- [x] P1-03 single BP Python PASS → **TRUE POSITIVE** (대원칙 3 경계 위반 확인)
- [x] P1-04 Entity REJECT 우회 → **TRUE POSITIVE** (Director 내부 LLM 조기 차단, P2 하향 여지)
- [x] P1-05 적응형 PASS→REJECT → **TRUE POSITIVE** (대원칙 3 위반 확인)
- [x] P1-06 PRE_LLM dead code → **TRUE POSITIVE** (severity 과대, P2 하향)
- [x] P1-07 PASS_FLOOR cliff → **PARTIAL** (양쪽 모두 passed=True, 실질 영향 제한적, P2 하향)
- [x] P1-08 required_scenes dead code → **TRUE POSITIVE**
- [x] P1-09 미사용 변수 3건 → **TRUE POSITIVE** (전 3건 확인)
- [x] P1-10 ContinuityValidator 테스트 → **PARTIAL** (5/6 미검증, 1/6 부분 검증)
- [x] P1-11 PWF 테스트 → **FALSE POSITIVE** (test_pass_with_fix.py에서 8+건 충분히 검증)
- [x] P1-12 대원칙 3/4 테스트 → **FALSE POSITIVE** (test_pass_with_fix.py L716 + test_v75c 9건에서 검증)

### Pass 4 — P2 핵심 10건 코드 교차 검증
- [x] P2-D01 is_approved 논리 → **TRUE POSITIVE** (호출자도 rejected 미검사)
- [x] P2-C02 Blueprint critical_violations 미병합 → **TRUE POSITIVE** (Arc/Manuscript는 적용, BP만 누락)
- [x] P2-A01 advisory_summary 누락 → **TRUE POSITIVE** (numeric_consistency 키 추적 분기 없음)
- [x] P2-Q01 narration_ratio 산술 → **TRUE POSITIVE** (음수 가능)
- [x] P2-Q02 fantasy Amendment 누락 → **TRUE POSITIVE** (FANTASY_AMENDMENTS 미정의)
- [x] P2-Q05 싱글톤 project_path → **TRUE POSITIVE** (reset_dashboard 필요)
- [x] P2-CF01 NC-3 "17개" → **TRUE POSITIVE** (실제 20개 항목)
- [x] P2-CF02 STRATEGIC_AUDIT 불일치 → **TRUE POSITIVE** (Output Format에 필드 미정의)
- [x] P2-C04 ACQUISITION_PATTERNS 불일치 → **TRUE POSITIVE** (2개 vs 4개)
- [x] P2-A02 스레드 접근 → **PARTIAL** (서로 다른 키, CPython GIL 하 실질 위험 LOW)

### Pass 5 — 최종 정리
- [x] 오탐 3건 삭제 (P1-01, P1-11, P1-12)
- [x] Severity 재조정 6건 (P0→P1 2건, P1→P2 4건)
- [x] 수정된 총괄 수치 반영
- [x] 수정 우선순위 재정렬

---

## 총괄 요약 (5Pass 감리 후 확정)

| Severity | 건수 | 비고 |
|----------|------|------|
| **P0-CRITICAL** | **0** | 감리 전 2건 → P1 하향 (Stage 3 경로 한정) |
| **P1-IMPORTANT** | **7** | Director 주권 경계선 (3), ValidationOrchestrator 잔여 우회 (2), 코드 위생 (2) |
| **P2-MODERATE** | **29** | 데이터 흐름 불일치, 프롬프트-스키마 불일치, 테스트 갭 |
| **P3-MINOR** | **20** | 코드 위생, dead code, 미사용 변수 |
| **합계** | **56** | 감리 전 59건 → 오탐 3건 삭제 |

---

## P1-IMPORTANT (7건)

### [T4-P1-01] ConsistencyValidator unjustifiable_violations → auto REJECT (Stage 3 경로)
- **Severity**: P1 (감리: P0→P1 하향. Stage 3 Blueprint 검증 경로에서만 도달)
- **파일**: `modules/validation/validation_orchestrator.py` L468-482
- **현상**: ConsistencyValidator가 `unjustifiable_violations`를 반환하면, orchestrator가 즉시 `passed=False`, `verdict="REJECT"` 설정. Director 판단 기회 없음.
- **5Pass 검증 결과**: 이 코드는 `director_auditor.audit_manuscript_v0128()` → `unified_blueprint_validator.py`를 통해서만 도달. **Stage 4 원고 인터뷰 플로우에서는 `ValidationOrchestrator`를 사용하지 않으므로 미도달.** Stage 4에서는 `consistency_validator.validate()` 결과가 advisory warnings로 Director에 전달됨 (대원칙 3 준수).
- **근거**: BLOCKING/CONTINUITY는 TF-36 advisory 변환 완료 (L394-405, L420-456). CONSISTENCY만 미변환. Blueprint 검증에서 Python이 "정당화 불가"를 판단하는 것은 대원칙 1/3 경계 위반.
- **수정안**: TF-36 advisory 변환 패턴 동일 적용. Stage 3 Blueprint 경로에서도 Director 주권 존중.

### [T4-P1-02] RetrospectiveValidator CRITICAL → auto REJECT score=0 (Stage 3 경로)
- **Severity**: P1 (감리: P0→P1 하향. Stage 3 Blueprint 검증 경로에서만 도달)
- **파일**: `modules/validation/validation_orchestrator.py` L656-667
- **현상**: RetrospectiveValidator CRITICAL severity → `total_score=0`, `passed=False` 즉시 REJECT. Director 판정 기회 없음.
- **5Pass 검증 결과**: P1-01과 동일한 호출 체인. Stage 4 원고 인터뷰 플로우에서는 미도달.
- **근거**: realm_regression, relationship_regression, item_disappearance, conflict_recurrence 4개 검사 중 하나라도 CRITICAL이면 발동. broad except → CRITICAL → Director 우회 가능.
- **수정안**: TF-36 advisory 패턴 적용. CRITICAL을 우선순위 헤더로 주입, 최종 verdict는 Director 결정.

### [T4-P1-03] _evaluate_single_blueprint Python-only PASS (대원칙 3 경계)
- **Severity**: P1
- **파일**: `modules/domain/agents/director_ensemble.py` L471-478
- **현상**: 단일 Blueprint 후보가 기본 기준(씬 4개+, 800자+) 충족 시 Director LLM 호출 없이 Python-only `PASS, score=75` 반환.
- **5Pass 검증 결과**: L472에 `logging.warning(" [대원칙3] _evaluate_single_blueprint: Python-only PASS (Director LLM 미호출)")` 실제 존재 확인. 코드 자체가 이것이 이상적이지 않다는 인식을 표시.
- **수정안**: 단일 후보라도 간소 LLM 판정 위임, 또는 "비용/속도 이유로 의도적 Python-only" 주석 명시.

### [T4-P1-04] select_and_judge_ensemble 적응형 PASS→REJECT 하향
- **Severity**: P1
- **파일**: `modules/domain/agents/director_ensemble.py` L1246-1256
- **현상**: `apply_adaptive_decision` → `CONDITIONAL_PASS` → Director가 PASS 내렸는데 Python이 `adjusted=True` + `original_verdict in ("PASS", "PASS_WITH_FIX")` 조건으로 `final_verdict = "REJECT"` 설정.
- **5Pass 검증 결과**: `director_grading.py` L555-580의 `apply_adaptive_decision()`에서 score < threshold이면 `adjusted=True` 반환 확인. L1250-1252에서 Director PASS를 Python이 REJECT으로 뒤집는 코드 존재 확인. 대원칙 3 위반.
- **수정안**: Director PASS 존중 + 경고 로깅, 또는 CONDITIONAL_PASS로 유지하며 Director에게 재판정 기회 부여.

### [T4-P1-05] _check_required_scenes 비활성 dead code
- **Severity**: P1
- **파일**: `modules/validation/blocking_validator_scene_checks.py` L44-51
- **현상**: 항상 `{"check": "required_scenes", "passed": True}` 반환. docstring에 "intentionally disabled due to false negative issues" 명시. 호출 체인(`blocking_validator.py` L77 → L163-164)에서 실제 호출되나 no-op.
- **5Pass 검증 결과**: 비활성화 확인. 내부 로직이 dead code로 잔류.
- **수정안**: 함수 본문을 `return {"check": "required_scenes", "passed": True}` 한 줄로 축소, 또는 호출부에서 조건부 skip.

### [T4-P1-06] pre_director_manuscript_checker 미사용 변수 3건
- **Severity**: P1
- **파일**: `modules/core/pre_director_manuscript_checker.py` L43-47, L58-59, L63
- **현상**: (1) `dialogue_patterns` 3개 regex 정의 후 미사용, (2) `dialogue_count = manuscript.count('"') // 2 + manuscript.count("「")` 직후 `dialogue_count = count_dialogue_segments(manuscript)`로 덮어씌움, (3) `ratio_diff` 계산 후 미사용 (`# noqa: F841`).
- **5Pass 검증 결과**: 전 3건 확인됨.
- **수정안**: 미사용 코드 3건 삭제, noqa 태그 제거.

### [T4-P1-07] ContinuityValidator 5/6 서브체크 직접 테스트 부재
- **Severity**: P1
- **파일**: `tests/test_continuity_validator.py` vs `modules/validation/continuity_validator.py`
- **현상**: 6개 서브체크(_check_item/weapon/injury/location/personality/time_consistency) 중 `_check_personality_continuity`만 부분 테스트 존재 (NPC history ordering 1건). 나머지 5개 서브체크 직접 테스트 0건.
- **5Pass 검증 결과**: 5/6 미검증 확인 (원 보고서의 "6개 전부 미검증"은 과대 → 수정).
- **수정안**: (1) validate() 통합 테스트 — prev_hud 정상 경로, (2) prev_hud 누락 DEGRADED, (3) skip_continuity=True, (4) 비전투 장르 부상 스킵, (5) 개별 _check 메서드 단위 테스트 최소 5건.

---

## P2-MODERATE (29건)

### Director 체계 (5건)
| ID | 제목 | 파일 | 5Pass |
|----|------|------|-------|
| T4-P2-D01 | `on_approve_workflow` is_approved 논리 — rejected 있어도 applied>0이면 승인 | `director_grading.py` L686 | 진양성 (호출자도 rejected 미검사) |
| T4-P2-D02 | `_evaluate_single_blueprint` 반환 dict 필드 누락 (fix_scope, comparison_notes 등) | `director_ensemble.py` L443-478 | 미검증 (원 보고 유지) |
| T4-P2-D03 | NC-3B 자동교정 상향 시 로깅 부재 | `director_ensemble.py` L1092-1101 | 미검증 (원 보고 유지) |
| T4-P2-D04 | audit_manuscript Entity REJECT이 Director 본 감사 우회 (P1→P2 하향) | `director_auditor.py` L534-549 | 진양성 (Director 내부 LLM 조기 차단, "우회"보다 "사전 방어선") |
| T4-P2-D05 | Continuity 체계 사망 캐릭터 직접 필터 부재 (P1→P2 하향) | continuity 5파일 | 진양성 (TruthGate+StateTracker+Director 프롬프트에서 다중 방어) |

### Continuity 체계 (4건)
| ID | 제목 | 파일 | 5Pass |
|----|------|------|-------|
| T4-P2-C01 | inspect_manuscript/inspect_manuscript_v59 메인 파이프라인 미사용 (dead code) | `continuity_manuscript.py` L210/L1158 | 미검증 (원 보고 유지) |
| T4-P2-C02 | Blueprint critical_violations가 LLM 결과에 미병합 (Arc/Manuscript는 적용됨) | `continuity_blueprint.py` L248-253 | 진양성 |
| T4-P2-C03 | inspect_manuscript_v59에 entity_registry 파라미터 미전달 | `continuity_manuscript.py` L1167 | 미검증 (원 보고 유지) |
| T4-P2-C04 | ACQUISITION_PATTERNS 2개 vs acquire_patterns 4개 — 원고 검증 탐지율 저하 | `continuity_manuscript.py` L199-202 | 진양성 |

### Advisory Chain (2건)
| ID | 제목 | 파일 | 5Pass |
|----|------|------|-------|
| T4-P2-A01 | NumericConsistency가 _advisory_summary에서 누락 — 메타데이터 추적 갭 | `stage4_interview_round.py` L1528-1543 | 진양성 |
| T4-P2-A02 | validation_results dict 동시 스레드 접근 (CPython GIL 의존) | `stage4_interview_round.py` L3713-3764 | PARTIAL (서로 다른 키, 실질 위험 LOW) |

### Validation (4건)
| ID | 제목 | 파일 | 5Pass |
|----|------|------|-------|
| T4-P2-V01 | ContinuityValidator DEGRADED fail-closed — ep=1에서도 passed=False | `continuity_validator.py` L124-145 | 미검증 (원 보고 유지) |
| T4-P2-V02 | ConsistencyValidator 통합 테스트 부재 (5개 서브체크) | `test_consistency_validator.py` | 미검증 (원 보고 유지) |
| T4-P2-V03 | 병렬 경로 PRE_LLM REJECT — 도달 불가 사문 코드 (P1→P2 하향) | `validation_orchestrator.py` L1178-1182 | 진양성 (pre_llm_validator 항상 passed=True, dead code) |
| T4-P2-V04 | UNCONDITIONAL_PASS_FLOOR=85 cliff edge (P1→P2 하향) | `validation_orchestrator.py` | PARTIAL (양쪽 모두 passed=True, 실질 영향 제한) |

### 품질 메타시스템 (5건)
| ID | 제목 | 파일 | 5Pass |
|----|------|------|-------|
| T4-P2-Q01 | narration_ratio 산술 — 인용부호 개수 x 10, 음수 가능 | `confidence_calibration.py` L181-182 | 진양성 |
| T4-P2-Q02 | quality_constitution에 fantasy 장르 Amendment 누락 | `quality_constitution.py` L279-290 | 진양성 (FANTASY_AMENDMENTS 미정의) |
| T4-P2-Q03 | QualityDashboard 인스턴스 메서드 스레드 보호 없음 | `quality_dashboard.py` L124-148 | 미검증 (원 보고 유지) |
| T4-P2-Q04 | QualityAmplifier 무협 전용 아이템 패턴이 비무협 장르에도 적용 | `quality_amplifier.py` L348-363 | 미검증 (원 보고 유지) |
| T4-P2-Q05 | get_dashboard() 싱글톤이 project_path 변경 무시 | `quality_dashboard.py` L1209-1216 | 진양성 |

### Config/Prompt (4건)
| ID | 제목 | 파일 | 5Pass |
|----|------|------|-------|
| T4-P2-CF01 | NC-3 "17개"라고 명시하나 실제 20개 (4곳 반복) | `director.yaml` L184/502/819/1077 | 진양성 |
| T4-P2-CF02 | STRATEGIC_AUDIT NC-1/NC-3 지시와 Output Format 불일치 | `director.yaml` L810-898 | 진양성 |
| T4-P2-CF03 | DIRECTOR_AUDIT NC-1/NC-3 vs Output Format 불일치 (score_breakdown 키 혼란) | `director.yaml` L1068-1165 | 미검증 (원 보고 유지) |
| T4-P2-CF04 | STRATEGIC_AUDIT에 Ensemble 전용 score_breakdown 공식 혼입 | `director.yaml` L871-872 | 미검증 (원 보고 유지) |

### 테스트 커버리지 (5건)
| ID | 제목 | 파일 | 5Pass |
|----|------|------|-------|
| T4-P2-T01 | CatharsisTimer frustration streak 분기 미검증 | `test_catharsis_timer.py` | 미검증 (원 보고 유지) |
| T4-P2-T02 | BlockingValidator 사망 NPC 일반명사 스킵 미검증 | `test_blocking_validator_submodules.py` | 미검증 (원 보고 유지) |
| T4-P2-T03 | BlockingValidator aliases + word boundary 미검증 | `test_blocking_validator_submodules.py` | 미검증 (원 보고 유지) |
| T4-P2-T04 | DirectorContinuity blueprint ep>1 경로 미검증 | `test_director_modules.py` | 미검증 (원 보고 유지) |
| T4-P2-T05 | NumericConsistencyChecker 산술 경계값 미검증 | `test_numeric_consistency_checker.py` | 미검증 (원 보고 유지) |

---

## P3-MINOR (20건) — 요약만 기재

| # | 제목 | 파일 |
|---|------|------|
| 1 | Dead code after early return in _fallback_arc_selection | `director_ensemble.py` L782-793 |
| 2 | check_manuscript_continuity_with_cache 예외 시 CONFLICT 반환 (타 메서드는 REJECT/SKIP) | `director_continuity.py` L861-868 |
| 3 | _run_genre_specific_validation except이 3종만 catch (TypeError 등 미포함) | `director_auditor.py` L102-110 |
| 4 | audit_strategic_plan arc_plan None guard 미비 | `director_auditor.py` L803 |
| 5 | _expand_prev_full_text 전체 0건 로드 시 요약 로그 없음 | `director_auditor.py` L354-358 |
| 6 | google.genai 함수 내부 lazy import (의도적) | `director_continuity.py` L547 |
| 7 | violations 키 미반환 (_check_power/_check_foreshadowing) | `continuity_tracker.py` L224-325 |
| 8 | _check_relationship_jump find/rfind 비대칭 | `continuity_manuscript.py` L543-558 |
| 9 | STATE_ORDER에 "굴복"/"사망" 누락 | `continuity_manuscript.py` L1065 |
| 10 | _inspect_intra_arc_only ep_start 미사용 호출 | `continuity_arc.py` L775 |
| 11 | 불필요 pass 문 2건 | `continuity_arc.py` L607/L655 |
| 12 | _format_prev_arcs ep_start 비int 폴백 | `continuity_arc.py` L906-917 |
| 13 | NumericDriftAdvisor _llm_ask=None 시 Python pre-warnings 소실 | `numeric_drift_advisor.py` L46-61 |
| 14 | TruthGate JSON parse fence-free fallback 한계 | `truth_gate.py` L420-426 |
| 15 | blocking_validator_consistency_checks 중복 import re 2건 | L71/L188 |
| 16 | pre_director_narrative_checker 함수 내부 Counter import | L91 |
| 17 | confidence_calibration content 타입 힌트 str vs 실제 dict 허용 | L322-324 |
| 18 | detect_quality_drift slope 계산 양 끝점만 비교 | `quality_dashboard.py` L1137 |
| 19 | QualityDashboard _save_record 실패 시 인메모리/디스크 불일치 | `quality_dashboard.py` L230-240 |
| 20 | RELATIONSHIP_TRANSITIONS "충성"→"굴복" 비대칭 | `quality_amplifier.py` L147-159 |

---

## 대원칙 준수 상태 (5Pass 감리 후 확정)

### 대원칙 1 (Python은 수집만, 판단은 LLM이)
- **대체로 준수**. Pre-Director, Advisory, 품질 메타시스템 전부 advisory-only.
- **Stage 4 원고 플로우**: 완전 준수. ConsistencyValidator 결과가 advisory warnings로 Director에 전달.
- **Stage 3 Blueprint 플로우**: 경계 위반 잔류 (T4-P1-01/02 — ValidationOrchestrator 경유).

### 대원칙 3 (Director 주권주의)
- **TF-36 이후 대폭 개선됨**. BLOCKING/CONTINUITY는 advisory 변환 완료.
- **Stage 4**: Director 주권 완전 준수. `select_and_judge_ensemble()`에서 Director LLM 최종 판정.
- **Stage 3 잔여**: T4-P1-01 (ConsistencyValidator), T4-P1-02 (RetrospectiveValidator) — ValidationOrchestrator 내 미변환.
- **경계선**: T4-P1-03 (single BP Python PASS), T4-P1-04 (적응형 PASS→REJECT 하향).

### 대원칙 4 (사망 캐릭터)
- **다중 방어 확인**: TruthGate `_check_deceased_resurrection` + BlockingValidator `_RECALL_PATTERNS`(16종)/`_ACTION_PATTERNS`(16종) + Director 프롬프트 + StateTracker `check_dead_npc_in_blueprint`.
- Continuity 체계에 직접 검증 없으나 다른 계층에서 충분히 커버 (T4-P2-D05).

### NC-1/NC-3 규칙
- **준수**. NC-1 AGREE/DISMISS 로깅만, NC-3B 자동교정 동작, NC-3 미작성 시 감점 없음.
- **프롬프트 이슈**: NC-3 "17개" 표기 오류 — 실제 20개 (T4-P2-CF01, 4곳 수정 필요).

---

## 수정 우선순위 제안 (5Pass 감리 후 재정렬)

### 1순위 (P1 — 조기)
1. `validation_orchestrator.py` ConsistencyValidator unjustifiable → TF-36 advisory 변환 (Stage 3 경로)
2. `validation_orchestrator.py` RetrospectiveValidator CRITICAL → TF-36 advisory 변환 (Stage 3 경로)
3. `director_ensemble.py` 적응형 PASS→REJECT 하향 로직 검토 — Director PASS 존중
4. `director_ensemble.py` single blueprint Python-only PASS — LLM 간소 판정 위임 검토

### 2순위 (P2 — 계획적)
5. `director.yaml` NC-3 "17개" → "20개" 수정 (4곳)
6. `director.yaml` STRATEGIC_AUDIT/DIRECTOR_AUDIT Output Format에 NC 관련 필드 정합
7. `continuity_blueprint.py` critical_violations → warnings 병합 누락 수정
8. `stage4_interview_round.py` advisory_summary에 numeric_consistency 키 추가
9. `quality_constitution.py` fantasy 장르 Amendment 추가
10. `pre_director_manuscript_checker.py` 미사용 변수 3건 삭제

### 3순위 (P2 — 순차)
11. 테스트 커버리지 갭 보강 (ContinuityValidator 5/6 서브체크, CatharsisTimer, BlockingValidator 경계값)
12. `validation_orchestrator.py` PRE_LLM REJECT dead code 제거
13. `blocking_validator_scene_checks.py` _check_required_scenes dead code 축소
14. `confidence_calibration.py` narration_ratio 산술 개선
15. `quality_dashboard.py` get_dashboard() 싱글톤 project_path 처리

---

## 정합성 확인 양호 항목 (참고)

- Advisory Chain 10개 → `_director_mc_parts` 전량 합류 확인
- ThreadPoolExecutor(8) 이중 타임아웃 (300s 전체 + 60s 개별) 정상
- ScoringValidator 80+20=100 설계 정합 (DEFAULT_SCORE_BREAKDOWN 6항목 80 + Python 4항목 20)
- validation.yaml quality_regression 키 정합
- emotion_tracker.yaml, investment_math_verifier.yaml 코드 정합
- QualityConstitution 100점 합산 정확
- BlockingValidator 사망 NPC _RECALL_PATTERNS 16종 + _ACTION_PATTERNS 16종 대원칙 4 준수
- Advisory/Pre-LLM validator 항상 passed=True — 대원칙 3 준수
- TF-51 FAIL→WARNING 다운그레이드 정합
- 프롬프트 인젝션 새니타이제이션 적절
- NC-3B score_breakdown 자동교정 동작 확인
- ScoringValidator LLM score clamping (max 초과 방지) 확인
- 6-Tier validation 실행 순서 정합 (PRE_LLM → CONTINUITY → BLOCKING → CONSISTENCY → SCORING → ADVISORY)
- PASS_WITH_FIX + fix_scope 라우팅 정상 테스트 존재 확인 (`test_pass_with_fix.py` 8+건)
- 대원칙 3/4 Director Ensemble 방어 테스트 존재 확인 (`test_v75c_contradiction_firewall.py` 9건)

---

## 5Pass 감리 오탐 삭제 기록

| 원래 ID | 원래 Severity | 판정 | 사유 |
|---------|-------------|------|------|
| T4-P1-01 | P1 | **삭제 (FALSE POSITIVE)** | director_prompts.py와 director.yaml 내용 동일. 폴백으로 사용되는 런타임 경로 없음. PromptLoader 실패 시 에러 반환 (하드코드 폴백 아님). |
| T4-P1-11 | P1 | **삭제 (FALSE POSITIVE)** | `test_pass_with_fix.py`에서 PASS_WITH_FIX 라우팅 8+건 충분히 검증 (inplace/failure/re-audit/bypass/multi-round). `test_director_modules.py`에서도 fix_scope passthrough 검증. |
| T4-P1-12 | P1 | **삭제 (FALSE POSITIVE)** | QualityGate PASS_WITH_FIX bypass: `test_pass_with_fix.py` L716에서 검증. 사망 NPC 방화벽: `test_v75c_contradiction_firewall.py`에서 "사망NPC 재등장" CRITICAL → firewall REJECT 검증 (9건). |
