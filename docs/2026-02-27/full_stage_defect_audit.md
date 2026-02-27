# 전 스테이지 결함 감사 보고서

> **감사 일시**: 2026-02-27
> **감사 범위**: Stage 0 ~ Stage 4 전 파이프라인 + Domain Agents + Validation + Infrastructure
> **감사 방법**: 7개 병렬 탐색 에이전트 → 교차 검증(감리) → 오탐 제거
> **기준 커밋**: `bd1c706`

---

## 요약

| 등급 | 건수 | 설명 |
|------|------|------|
| **P0** (크래시/데이터 손실) | **0건** | 교차 검증 후 전량 오탐 판정 또는 하향 |
| **P1** (잘못된 동작) | **12건** | 로직 오류, 타입 미검증, 예외 삼킴 |
| **P2** (경미/코스메틱) | **16건** | 데드 코드, 코드 스멜, 엣지 케이스 |
| **오탐 (FP)** | **5건** | 초기 감사에서 P0로 보고됐으나 검증 시 무해 판정 |
| **합계** | **28건 확정 + 5건 오탐 제거** | |

---

## 오탐(False Positive) 판정 근거

초기 감사에서 P0로 보고된 5건에 대한 교차 검증 결과:

### FP-1: Stage 3 — `phases["generate"]` KeyError (원래 P0-S3-01)
- **파일**: `three_phase_blueprint_generator.py:376`
- **원래 주장**: Phase 2 실패 시 `phases["generate"]`가 `{"status": "failed"}`만 포함 → L376 접근 시 KeyError
- **감리 판정**: **오탐**. L294-298에서 `if not best_blueprint: continue`로 루프 재시작. L376은 Phase 2 성공 후에만 도달. `continue`가 코드 경로를 차단.

### FP-2: Stage 3 — `fail_count` 리셋 (원래 P1-S3-03)
- **파일**: `stage3_orchestrator.py:734`
- **원래 주장**: 성공 시 `fail_count: 0` 반환 → 연속 실패 카운터 깨짐
- **감리 판정**: **오탐**. 연속(consecutive) 실패 추적이 목적. 성공 후 리셋은 **정상 동작**. F→S→F 패턴에서 카운터가 리셋되는 것이 의도된 설계.

### FP-3: Domain — `director_ensemble.py` IndexError (원래 P0)
- **파일**: `director_ensemble.py:351, 354`
- **원래 주장**: `candidates` 빈 리스트 시 `max(lengths)` ValueError
- **감리 판정**: **오탐**. L337-338에서 `if not qualified_indices: if not candidates:` 체크 후 빈 리스트는 L339에서 즉시 반환. L350은 candidates 비어있지 않을 때만 도달. 또한 candidates는 항상 3개 이하 (A,B,C 앙상블).

### FP-4: Stage 4 — Future 레이스 컨디션 (원래 P0)
- **파일**: `stage4_post_processor.py:439-440`
- **원래 주장**: `cancel()` 실패 시 동기 재시도와 비동기 스레드 동시 실행 → 상태 오염
- **감리 판정**: **P2로 하향**. `update_state_and_lore_v20`는 LLM API 호출 후 독립 dict 반환. 공유 가변 상태 없음. 최악의 경우 API 이중 호출(비용 낭비)뿐, 데이터 오염 아님. 동기 재시도 결과만 사용.

### FP-5: Validation — `consistency_validator.py` 데드 문장 (원래 P0)
- **파일**: `consistency_validator.py:242`
- **원래 주장**: `len(unjustifiable) > 0` 결과 미사용 → 로직 누락
- **감리 판정**: **P2로 하향**. L261 `is_passed = len(unjustifiable) == 0`이 실제 검증 수행. L242는 데드 코드일 뿐, 기능적 영향 없음.

---

## P1 확정 결함 (12건)

### P1-01: Stage 2 — "next" 액션 폴스루
- **파일**: `stage2_orchestrator.py:571-590`
- **카테고리**: 로직 오류 / 제어 흐름
- **설명**: Director가 `action="next"` (REJECT, 다음 Arc로 이동) 반환 시, 명시적 핸들러 없음. `retry` 분기의 `continue`를 건너뛰고 L590 `attempt += 1`로 폴스루. 의도는 while 루프 탈출(다음 Arc)이지만, 실제로는 동일 Arc 재시도.
- **트리거**: Director가 "next" 액션 반환 시
- **영향**: Arc 설계가 max_attempts 소진까지 같은 Arc 재시도. 원래 의도는 다음 Arc로 진행.
- **권고**: `if _fin["action"] == "next": break` 추가

### P1-02: Stage 4 — `state_changes` 타입 미검증
- **파일**: `stage4_context_builder.py:812-816`
- **카테고리**: 타입 미스매치 / AttributeError 위험
- **설명**: L812에서 `arc_data.get("state_changes")` truthy 체크 후, L813에서 직접 접근. `state_changes`가 dict가 아닌 list일 경우, L816 `_sc.get(_field)`에서 `AttributeError: 'list' object has no attribute 'get'` 발생.
- **트리거**: Stage 2에서 `state_changes`를 list 형태로 생성한 경우
- **영향**: Stage 4 컨텍스트 빌드 실패 → 벡터 메모리 검색 누락
- **권고**: `if isinstance(_sc, dict):` 타입 가드 추가

### P1-03: Stage 4 — NPC 이력 로드 예외 미처리
- **파일**: `stage4_interview_round.py:366-373`
- **카테고리**: 예외 삼킴 / 검증 누락
- **설명**: `get_npc_change_history()` 호출에 try/except 없음. DB 오류 시 전체 ConsistencyValidator 블록이 실패하고, NPC 이력이 빈 dict로 전달됨. 성격/관계 불일치 원고가 검증 통과.
- **트리거**: DB 연결 오류, StateTracker 미초기화
- **영향**: NPC 성격 불일치 원고가 Director에게 경고 없이 전달

### P1-04: Validation — `retrospective_validator.py` 미검증 dict 접근
- **파일**: `retrospective_validator.py:151, 160, 163`
- **카테고리**: 타입 안전성 / KeyError 위험
- **설명**: L141에서 `if not history: continue`로 빈 리스트 방어. 그러나 `history[-1]`의 요소가 dict가 아니거나 `"state"`, `"ep_num"` 키가 없으면 KeyError/TypeError 발생. 원소 타입 검증 없음.
- **트리거**: `get_relationship_history()`가 비표준 형태의 이력 반환
- **영향**: RetrospectiveValidator 크래시 → 관계 역행 검증 실패

### P1-05: Validation — `continuity_validator.py` 과도한 예외 삼킴
- **파일**: `continuity_validator.py:1014`
- **카테고리**: 예외 삼킴 / 디버깅 어려움
- **설명**: `except Exception: return []` — 프로그래밍 오류(AttributeError, NameError)까지 삼킴. DB 메서드 시그니처 변경 시 버그가 영구적으로 숨겨짐.
- **트리거**: DB 메서드 인터페이스 불일치
- **영향**: 좌절-보상 타이머 영구 비활성화 (빈 리스트 반환)

### P1-06: Validation — `retrospective_validator.py` 예외 삼킴 3건
- **파일**: `retrospective_validator.py:269, 292, 344`
- **카테고리**: 예외 삼킴 / 디버깅 어려움
- **설명**: 3곳에서 `except Exception:` + `_logger.warning(...)` 패턴. 로깅은 있으나 프로그래밍 오류까지 삼킴.
- **트리거**: DB 스키마 변경, 메서드 시그니처 불일치
- **영향**: 과거 영역/아이템/갈등 검증이 조용히 비활성화

### P1-07: Validation — `threshold_helper.py` ConfigManager 초기화 실패 삼킴
- **파일**: `threshold_helper.py:17`
- **카테고리**: 예외 삼킴 / 설정 누락
- **설명**: `except Exception: _threshold._cfg = None` — YAML 파싱 오류, 파일 미발견 등 모든 예외 삼킴. 이후 모든 `_threshold()` 호출이 하드코딩 기본값 사용.
- **트리거**: `validation.yaml` 파일 오류/부재
- **영향**: 전체 검증 임계값이 코드 기본값으로 폴백 — 사용자 설정 무시

### P1-08: Stage 0 — JSON 파싱 체인 인덱싱
- **파일**: `style_extractor.py:749-751`, `story_expander.py:104-106`, `reverse_expander.py:111-113`
- **카테고리**: 계약 위반 / 파싱 실패 경로
- **설명**: `json_str.split("` ``` `json")[1].split("` ``` `")[0]` 패턴. except절이 IndexError를 잡지만, 실패 시 `{}` 반환으로 데이터 조용히 손실. LLM 응답이 코드블록 없이 JSON만 반환하면 원본 데이터 폐기.
- **트리거**: LLM이 ` ```json ``` ` 마크다운 없이 JSON 반환
- **영향**: Bible/Treatment 파싱 결과가 빈 dict → 설정 누락

### P1-09: Stage 0 — `run_reverse_engineering_flow()` 반환 타입 위반
- **파일**: `stage0/__init__.py:257, 269`
- **카테고리**: 계약 위반 / 타입 미스매치
- **설명**: 반환 타입 `tuple[dict, list, StyleGuide]`이나 실제 반환 `(dict, list, None)`. 호출자가 StyleGuide 메서드(`.to_prompt()`) 호출 시 AttributeError.
- **트리거**: 역분석 플로우에서 StyleGuide 생성 실패
- **영향**: 스타일 가이드 기반 원고 생성 시 크래시

### P1-10: Domain — `director_ensemble.py` state_updates 손실
- **파일**: `director_ensemble.py:362`
- **카테고리**: 데이터 손실 / 폴백 누락
- **설명**: 모든 후보 분량 미달 시 `"state_updates": {}` 빈 dict 반환. 정상 경로(L577-579)에서는 `result.get("state_updates") or selected_candidate.get("state_updates")` 캐스케이드. 분량 미달 경로에서만 HUD 업데이트 누락.
- **트리거**: 3개 후보 모두 MIN_MANUSCRIPT_LENGTH 미달
- **영향**: 캐릭터 상태 변경(레벨업, 아이템 획득 등)이 해당 에피소드에서 누락

### P1-11: Domain — `chief_writer_quality.py` 다중 행 regex 미매칭
- **파일**: `chief_writer_quality.py:315`
- **카테고리**: 로직 오류 / 위음성(false negative)
- **설명**: `re.search(f"{esc_name}.*{kw}|{kw}.*{esc_name}", content)` — `.*`은 기본적으로 개행 미매칭. NPC 이름과 비하 키워드가 다른 줄에 있으면 관계 불일치 미감지.
- **트리거**: NPC 관계 위반이 줄을 걸쳐서 발생
- **영향**: NPC 관계 불일치(적대→우호 등) 검증 누락

### P1-12: Infrastructure — SQL 동적 테이블/컬럼명 f-string
- **파일**: `db_manager.py:300,312,383,1631,1667`, `vec_memory.py:1157`
- **카테고리**: 계약 위반 / SQL 안전성
- **설명**: 6곳에서 f-string으로 테이블/컬럼명 주입. 현재는 하드코딩 리스트에서만 선택하므로 안전하나, 리팩토링 시 SQL 인젝션 위험. `# noqa: S608` 억제 2건 존재.
- **트리거**: 현재는 안전 (하드코딩 값만 사용)
- **영향**: 미래 리팩토링 시 보안 취약점 가능성

---

## P2 확정 결함 (16건)

### P2-01: Stage 0 — `_parse_korean_number()` 불완전 입력 처리
- **파일**: `preset_registry.py:570-588`
- **설명**: `"1만5"` 같은 불완전 입력에서 후행 숫자(`5`)가 그대로 가산. 의도 불분명.

### P2-02: Stage 0 — `preset_registry.py` corrupted `discovered_fields`
- **파일**: `preset_registry.py:725`
- **설명**: `enum_values=None`인 FieldDefinition 생성 가능. `default_factory=list` 오버라이드.

### P2-03: Stage 0 — 과도한 예외 삼킴
- **파일**: `reverse_expander.py:54, 701, 722`
- **설명**: `except Exception: pass` 3건. 의도적이나 디버깅 어려움.

### P2-04: Stage 2 — `stage2_finalizer.py` 문자열 `"[]"` 비교
- **파일**: `stage2_finalizer.py:281`
- **설명**: 리스트 정규화 후 `curr_inventory == "[]"` 비교. 도달 불가능한 분기.

### P2-05: Stage 2 — `cumulative_state_cache` 초기화 중복
- **파일**: `stage2_orchestrator.py:227`
- **설명**: L227과 L444에서 이중 초기화. L227은 불필요.

### P2-06: Stage 3 — 사용되지 않는 변수 할당
- **파일**: `three_phase_blueprint_generator.py:325-326`
- **설명**: `_prev_selection_reason`, `_prev_validation_warnings` 할당 후 미사용.

### P2-07: Stage 3 — Entity Registry 캐시 과잉 방어
- **파일**: `stage3_orchestrator.py:402`
- **설명**: 일시적 오류에서도 arc_idx 캐시 → 해당 Arc 재추출 영구 차단.

### P2-08: Stage 4 — Future cancel() 이중 호출 비용
- **파일**: `stage4_post_processor.py:439-440`
- **설명**: 실행 중 Future cancel() 실패 시 동기 재시도 → API 이중 호출 (비용 낭비, 데이터 오염 아님).

### P2-09: Stage 4 — `_InterviewRoundResult` 타입 힌트 불일치
- **파일**: `stage4_types.py:61-70`
- **설명**: `final_manuscript: object`, `final_title: object` — 주석은 `str | None`이나 힌트는 `object`.

### P2-10: Stage 4 — `get_int_input` 반환 타입 미검증
- **파일**: `stage4_orchestrator.py:743`
- **설명**: `get_int_input()` 반환값이 None 또는 비정수일 때 명시적 처리 없음. 기본값 2로 폴백하나 의도 불명확.

### P2-11: Domain — `chief_writer_context.py` 데드 조건
- **파일**: `chief_writer_context.py:759`
- **설명**: `if hud_history else {}` — L757에서 빈 리스트 이미 반환. 도달 불가능.

### P2-12: Domain — `analyst.py` bare except
- **파일**: `analyst.py:89`
- **설명**: `except Exception: protagonist_name = "주인공"` — 로깅 없이 예외 삼킴.

### P2-13: Domain — `chief_writer.py` bare except
- **파일**: `chief_writer.py:337-338`
- **설명**: `except Exception: pass` — 퍼포먼스 타이머 실패 삼킴. 로깅 없음.

### P2-14: Validation — `consistency_validator.py` 데드 문장
- **파일**: `consistency_validator.py:242`
- **설명**: `len(unjustifiable) > 0` — 비교 결과 미사용. L261이 실제 검증 수행.

### P2-15: Validation — `blocking_validator_scene_checks.py` regex 오류 삼킴
- **파일**: `blocking_validator_scene_checks.py:424-429`
- **설명**: `except re.error: continue` — 잘못된 regex 패턴 조용히 건너뜀. 클리프행어 감지 누락 가능.

### P2-16: Infrastructure — `semantic_plot_guard.py` 순서 오류
- **파일**: `semantic_plot_guard.py:293-295`
- **설명**: 빈 키워드 체크가 set 연산 이후에 위치. 기능적으로 안전하나 순서 비논리적.

---

## 스테이지별 분포

| 스테이지 | P1 | P2 | 합계 |
|----------|----|----|------|
| Stage 0 (초기 설정) | 2 | 3 | 5 |
| Stage 2 (Arc/Blueprint) | 1 | 2 | 3 |
| Stage 3 (Blueprint) | 0 | 2 | 2 |
| Stage 4 (원고) | 2 | 3 | 5 |
| Domain Agents | 3 | 3 | 6 |
| Validation | 4 | 2 | 6 |
| Infrastructure | 0 | 1 | 1 |
| **합계** | **12** | **16** | **28** |

---

## 카테고리별 분포

| 카테고리 | 건수 |
|----------|------|
| 예외 삼킴 (silent except) | 8 |
| 타입 미검증 / 계약 위반 | 7 |
| 로직 오류 / 제어 흐름 | 3 |
| 데이터 손실 위험 | 2 |
| 데드 코드 / 도달 불가 | 5 |
| SQL 안전성 | 1 |
| 기타 (코드 스멜) | 2 |

---

## 우선 수정 권고

### 즉시 수정 (P1, 영향도 높음)

1. **P1-01** `stage2_orchestrator.py` — "next" 액션에 `break` 추가 (1줄)
2. **P1-02** `stage4_context_builder.py` — `isinstance(_sc, dict)` 가드 (1줄)
3. **P1-03** `stage4_interview_round.py` — NPC 이력 try/except + WARNING 로깅 (3줄)
4. **P1-10** `director_ensemble.py` — 분량 미달 경로에서 `state_updates` 보존 (후보에서 추출)
5. **P1-11** `chief_writer_quality.py` — `re.DOTALL` 플래그 추가 (1줄)

### 다음 스프린트 (P1, 영향도 중간)

6. **P1-04~07** Validation 예외 삼킴 4건 — 구체적 예외 타입으로 전환
7. **P1-08** Stage 0 JSON 파싱 — 코드블록 없는 JSON 직접 파싱 폴백
8. **P1-09** Stage 0 반환 타입 — `StyleGuide | None` 명시 + 호출자 방어

### 관찰 대기 (P2)

- P2 전량 — 기능적 영향 없음. 코드 리뷰 시 점진적 개선.

---

## 감리 방법론

1. **7개 병렬 에이전트**: Stage 0, Stage 2, Stage 3, Stage 4, Domain Agents, Infrastructure, Validation 각 1개
2. **10개 검사 항목**: 로직 오류, 예외 삼킴, 데이터 오염, 계약 위반, 데드 코드, 리소스 누수, 엣지 케이스, 타입 불일치, null 미검증, off-by-one
3. **교차 검증**: P0/P1 전건 소스 확인 → 5건 오탐 제거, 2건 등급 하향
4. **오탐률**: 초기 보고 33건 중 5건 오탐 (15%) — 감리를 통해 제거

---

*이 문서는 코드 수정 없이 조사/감리만 수행한 결과입니다.*
