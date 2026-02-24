# 글도비 마스터 실행 가이드 -- 컨텍스트 컴팩트 대비

> 최종 업데이트: 2026-02-24
> 이 문서 하나로 전체 상황 파악 및 재개 가능

---

## 0. 즉시 파악 요약 (30초 버전)

- **글도비**는 AI 웹소설 자동 생성 시스템 (Python + Gemini API). Stage 0(설정) -> 2(Arc) -> 3(Blueprint) -> 4(원고) 파이프라인.
- **현재 상태**: 시스템 안정화 완료 (2,583 tests passed, ruff 0 violations). Treatment 콘텐츠 보강 + Bible 동기화 완료.
- **다음 할 일**: TF-11 게이트웨이 설계 -> TF-10 Phase 0~1 (episode_details 스키마 추가) -> 게이트웨이 구현 -> TF-10 Phase 2~4 (소비 코드 + 검증 + 테스트).
- **TF-11 게이트웨이 설계 문서는 아직 미작성 상태** (OPUS TF 진행 중이었으나 문서 미생성). 이 작업부터 재개.
- **절대 주의**: 4대 원칙 (Python=수집만, 팩트시트 수정=LLM만, Director 주권, 사망 캐릭터 제한) 위반 금지.

---

## 1. 시스템 개요

### 1-1. 글도비란

AI 웹소설 자동 생성 시스템. Python으로 데이터 수집/포맷팅/전달, Gemini API(LLM)로 판단/집필을 수행한다.

### 1-2. 파이프라인 구조

```
Stage 0 (초기 설정)  ->  Stage 2 (Arc/Blueprint)  ->  Stage 4 (원고)
세계관 바이블 추출       Analyst -> Arc -> Blueprint     Chief Writer -> Director 심사
NPC 등록                앙상블 + 검증 체인              합격/불합 -> 재작성 루프
문체 분석                연속성 검사                    카카오/네이버 포맷 출력
```

### 1-3. 4대 원칙 (절대 위반 금지)

1. **Python은 수집만, 판단은 LLM이** -- Python은 데이터 수집/포맷팅/전달만. 판단은 LLM 에이전트가 담당.
2. **팩트시트 수정 권한은 LLM만** -- NPC 속성, 세계관 설정, 관계도를 수정하는 건 LLM뿐.
3. **디렉터 주권주의 (내각제)** -- Director가 최종 품질 결정권. Director를 우회하면 안 됨.
4. **사망 캐릭터는 회상/언급만 허용** -- `deceased=True` NPC가 행동/대사로 등장하면 REJECT.

### 1-4. DB 구조

- 단일 파일 SSOT: `project_data.db` (SQLite)
- Arc 데이터: `data_anchors` 테이블에 `stage="arcs"` 키로 JSON TEXT 저장
- Pydantic `extra="allow"` -- 추가 키 안전 수용
- VecMemory: `vec_memory.py`가 DBManager 커넥션 공유 (FTS5 + RRF 하이브리드 검색)

---

## 2. 현재 완료된 작업

### 2-1. 완료된 커밋 (전체)

| 커밋 | 내용 |
|------|------|
| `099d91c` | Work A: `config/settings/validation.yaml` -- `stage3_enabled: true` (L174) |
| `099d91c` | Work B: `modules/core/stage3_orchestrator.py` -- Treatment Block 직접 주입 |
| `9fb7a36` | 인덱스 버그 수정: `arc_idx` 사용 + 시간적 게이팅 안내문 |
| (미커밋) | TF-10 P2: `four_phase_arc_generator.py` L376, L651 -- ASP episode_details 복원 |
| (미커밋) | TF-10 P3: `arc_corrector.py` 3곳 -- tactical_doc 수정 시 해당 화 episode_details 삭제 |
| (미커밋) | TF-11 Section 11 -- 3-시각 리뷰 종합 + 경량 대안 채택 결정 |

### 2-2. 시스템 전체 상태

- **테스트**: 2,583 passed + 0 xfailed (2026-02-24 최신)
- **Ruff**: 0 violations (P2/P3 코드는 미사용 변수 없음 확인)
- **모듈 분할**: stage4(-64%), chief_writer(-62%), stage2(-66%) 완료
- **DI 전환**: Stage2(44슬롯) + Stage3(19슬롯) + Stage4(24슬롯) 전량 완료
- **TF-10 분석 문서**: `docs/TF-10_episode_detail_map_analysis.md` 작성 완료 (Section 11 포함)
- **TF-11 설계 문서**: `docs/TF-11_output_gateway_design.md` 작성 완료 (Section 11 포함)
- **TF-10 Phase 0**: P1(확인완료) + P2(구현완료) + P3(구현완료)

---

## 3. 진행 중/예정 작업 (1->4 실행 순서)

### 작업 1: TF-11 게이트웨이 설계 문서화

**상태**: ✅ 완료

**완료된 것**:
- TF-11 설계 문서: `docs/TF-11_output_gateway_design.md` (487줄 → 570줄)
- 3-시각 리뷰: A(회의론) `TF-11_devils_advocate_review.md`, B(아키텍처), C(구현 리스크) `TF-11_risk_review.md`
- **결정**: 경량 대안 채택 (POC 기간). Gateway 전면 도입 → 후순위.
- TF-10 P2+P3 구현 완료 (TF-11 리뷰 결과의 ASP 위험 대응)

---

### 작업 2: TF-10 Phase 0~1 구현 (episode_details 스키마 추가)

**상태**: 미시작

#### Phase 0: 선결 조건 (3건)

| # | 조건 | 파일:위치 | 변경 내용 | 완료 확인 방법 |
|---|------|-----------|-----------|----------------|
| P1 | Gemini `response_schema` 사용 여부 확인 | `modules/domain/agents/arc_ensemble.py`, `modules/domain/agents/four_phase_arc_generator.py` | 코드 확인만. `response_schema=ARC_DESIGN_SCHEMA` 호출 경로 파악 | 사용 경로 문서화 |
| P2 | ASP 경로 map 복원 로직 | `modules/domain/agents/four_phase_arc_generator.py` L376 부근 | ASP 교체 전 원본 `episode_details` 백업, ASP 결과에 없으면 복원 (~5줄) | ASP 경로에서 `episode_details` 소실 안 되는 것 확인 |
| P3 | ArcCorrector 동기화 전략 A | `modules/domain/agents/arc_corrector.py` | `tactical_doc` 수정 성공 시 해당 화 `episode_details` 항목 삭제 -> regex 폴백 강제 (~3줄) | ArcCorrector 수정 후 불일치 미발생 확인 |

**P2 구체 코드 위치**: `four_phase_arc_generator.py` L376-378:
```python
if isinstance(_asp_arc, dict) and _asp_arc.get("tactical_doc"):
    best_arc = _asp_arc  # <-- 여기서 원본 episode_details 소실
    pipeline_result["asp_used"] = True
```
변경: `best_arc = _asp_arc` 전에 원본 map 백업, 이후 없으면 복원.

**P3 구체 코드 위치**: `arc_corrector.py` -- 수정 성공 시점에서 해당 ep_num의 episode_details 항목 삭제.

#### Phase 1: 스키마 + 프롬프트 (4건)

| # | 작업 | 파일:위치 | 변경 내용 | 줄수 | 완료 확인 방법 |
|---|------|-----------|-----------|------|----------------|
| 1-1 | Pydantic 모델에 필드 추가 | `modules/models/arc.py` L193 이후 | `episode_details: list[dict] = Field(default_factory=list)` | 1줄 | `ArcData(arc_no=1, ep_start=1, ep_end=5).episode_details == []` |
| 1-2 | Gemini API 스키마 추가 (선택 필드) | `modules/core/response_schemas.py` L279 이후 | `episode_details` ARRAY[OBJECT] 추가. **required 배열에 추가하지 않음** | 2줄 | 스키마 빌드 에러 없음 |
| 1-3 | LLM 프롬프트에 생성 지시 추가 | `config/prompts/ensemble.yaml` L92 이후 | episode_details 생성 지시 (~20줄) | 20줄 | YAML 파싱 정상 |
| 1-4 | Patch Mode 보존 지시 | `config/prompts/arc_generator.yaml` L12 이후 | `episode_details` 보존 지시 1줄 | 1줄 | Patch Mode 시 episode_details 유지 |

**핵심 설계 결정 (변경 금지)**:
- 필드명: `episode_details` (NOT `episode_detail_map`)
- 타입: `list[dict]` (NOT `dict[str, list[str]]`)
- 예시: `[{"ep_num": 4, "details": ["사건1", "사건2"]}, ...]`
- Gemini Schema에 동적 키 OBJECT 미지원 -> ARRAY[OBJECT] 형태 사용

#### Phase 1.5: 검증 게이트

**완료 조건**: 실제 Gemini 출력 1~2개 수집 후 `episode_details` 생성률 확인. **70% 미만이면 프롬프트 재조정 후 재진행**.

---

### 작업 3: TF-11 게이트웨이 구현 (경량 대안)

**상태**: 부분 완료 (P2+P3 완료, response_schema 확대 미시작)

**채택된 경량 조치**:
- [x] TF-10 P2: ASP episode_details 복원 (`four_phase_arc_generator.py`)
- [x] TF-10 P3: ArcCorrector episode_details 동기화 (`arc_corrector.py`)
- [ ] `response_schema` 확대 적용 (arc_ensemble.py + four_phase_arc_generator.py, ~5줄)
- [ ] `episode_details` Pydantic 필드 추가 (TF-10 Phase 1과 병합)

**Gateway 전면 도입**: 후순위 (process_node 평탄화 opt-in 전환 후 재검토)

---

### 작업 4: TF-10 Phase 2~4 구현 (소비 코드 + 검증 + 테스트)

**상태**: 미시작 (작업 2+3 완료 후 진행)

#### Phase 2: Stage 3 소비 코드 (4건, 순차 진행)

| # | 작업 | 파일:위치 | 변경 내용 | 줄수 | 완료 확인 방법 |
|---|------|-----------|-----------|------|----------------|
| 2-1 | `_extract_episode_focus()` 개선 | `modules/domain/agents/blueprint_constraint_compiler.py` L188 | `episode_details` 우선 참조 분기 추가 (기존 regex 폴백 유지) | ~10줄 | ep_num에 해당하는 details가 정확히 반환되는지 단위 테스트 |
| 2-2 | `_extract_stop_line()` 개선 | `modules/domain/agents/blueprint_constraint_compiler.py` L236 | 동일 패턴 (episode_details 우선 참조) | ~8줄 | 다음 화 정지선이 episode_details에서 추출되는지 확인 |
| 2-3 | `arc_focus` 보강 | `modules/domain/agents/blueprint_ensemble.py` L148 | episode_details 있으면 현재 화 세부 사건을 arc_focus 앞에 주입 | ~8줄 | arc_focus에 "[이번 화 핵심 사건]" 헤더 포함 확인 |
| 2-4 | TF9 조건 추가 (선택적) | `modules/core/stage3_orchestrator.py` L512 | `episode_details` 존재 시 TF9 보완 경로 스킵 가능 조건 추가. **episode_details와 TF9 독립 유지** | ~5줄 | TF9 코드가 episode_details 유무와 무관하게 정상 동작 |

**2-4 주의**: episode_details와 TF9 Treatment Block 주입은 **정보 원천이 다르다**. episode_details는 Arc LLM이 생성한 화별 사건, TF9는 Treatment Block 원본 필드. 둘은 보완 관계이며 대체 관계가 아니다.

#### Phase 3: 검증 체인 (3건, Phase 2 완료 후 순차)

| # | 작업 | 파일 | 변경 내용 | 줄수 |
|---|------|------|-----------|------|
| 3-1 | Arc 검증에 map 정합성 체크 | `modules/domain/agents/unified_arc_validator.py` | `episode_details` 키 존재 + ep_start~ep_end 범위 검증 (advisory) | ~10줄 |
| 3-2 | DraftValidator에 map 체크 | `modules/domain/agents/arc_draft_validator.py` | `episode_details`과 `tactical_doc` 정합성 체크 (advisory) | ~8줄 |
| 3-3 | ContinuityInspector map 참조 | `modules/domain/agents/continuity_inspector.py` | 이전 Arc 마지막 화와 현재 첫 화 연속성 참조 (선택적) | ~5줄 |

**주의**: 모두 advisory/선택적 검증. 기존 PASS/REJECT 로직에 영향 없어야 함.

#### Phase 4: 테스트 (14개)

원안 6개:
1. `test_episode_details_pydantic` -- ArcData에 episode_details 포함/미포함 검증
2. `test_extract_episode_focus_with_details` -- ConstraintCompiler가 details 우선 참조 확인
3. `test_extract_stop_line_with_details` -- 정지선이 details에서 정확히 추출되는지
4. `test_episode_details_fallback` -- details 비어있을 때 기존 regex 폴백 확인
5. `test_arc_validate_with_details` -- validate_arc()가 details 포함 dict 정상 처리
6. `test_stage3_uses_detail_details` -- Stage 3가 details를 Blueprint 제약에 반영하는지

3-시각 재검토 추가 8개:
7. `test_arc_corrector_preserves_details` -- ArcCorrector 수정 후 details 잔존 확인
8. `test_arc_corrector_details_sync_warning` -- tactical_doc 수정 후 불일치 감지
9. `test_asp_preserves_details` -- ASP 경로 details 복원 확인
10. `test_patch_mode_regenerates_details` -- Patch Mode 후 details 포함 여부
11. `test_detail_type_normalization` -- 값이 str일 때 list[str]로 정규화
12. `test_detail_int_key_fallback` -- int 키 접근 시 str 폴백
13. `test_evaluate_candidate_details_bonus` -- details 있는 후보 채점 보너스
14. `test_tactical_doc_details_consistency_reject` -- 불일치 시 REJECT 트리거

**완료 조건**: `pytest tests/ -q` 전체 통과 (2,583 + 14 = 2,597 이상)

---

## 4. 핵심 설계 결정사항 (변경 금지)

| # | 결정 | 이유 |
|---|------|------|
| D1 | 필드명 `episode_details` (NOT `episode_detail_map`) | 3-시각 재검토 결과 수렴 |
| D2 | 타입 `list[dict]` (NOT `dict[str, list[str]]`) | Gemini Schema가 동적 키 OBJECT 미지원. ARRAY[OBJECT]는 정확히 표현 가능 |
| D3 | 예시: `[{"ep_num": 4, "details": ["사건1"]}]` | ep_num을 명시적 필드로 가져가서 키 해석 모호성 제거 |
| D4 | TF9 Treatment Block 주입과 `episode_details`는 독립 유지 | 정보 원천이 다름 (Treatment 원본 vs Arc LLM 생성) |
| D5 | Phase 2+3은 순차 진행 (병렬 아님) | 키 해석 규칙 확정 후 검증 체인 작성해야 정합성 보장 |
| D6 | ArcCorrector 전략 A: 수정 시 해당 화 `episode_details` 항목 삭제 -> regex 폴백 | tactical_doc 수정 후 불일치 방지 (최소 코드, ~3줄) |
| D7 | ASP 경로: 교체 전 map 백업, 없으면 복원 | ASP LLM 출력에 episode_details 없을 수 있음 |
| D8 | `episode_details`는 선택 필드 (required 아님) | 점진적 도입, 기존 프로젝트 하위 호환 |
| D9 | `tactical_doc`은 그대로 유지 (병행) | LLM 간 서사 전달용. episode_details는 Python 코드용 구조화 인덱스 |

---

## 5. 재개 방법

새 세션에서 이 문서를 읽은 후:

### Step 1: 상태 확인
```bash
cd "C:\Users\wjjo\Desktop\글도비"
pytest tests/ -q                    # 2,583 passed 확인
git log --oneline -5                # 최근 커밋 확인
```

### Step 2: 현재 작업 확인
1. **작업 1(TF-11 설계)이 완료됐는지 확인** -- `docs/` 하위에 TF-11 관련 문서가 있는지 확인
2. **TF-10 Phase 0 선결조건이 완료됐는지 확인** -- `modules/models/arc.py`에 `episode_details` 필드가 있는지 확인
3. 미완료 작업부터 순차 재개

### Step 3: 순서대로 진행
```
미완료 작업 확인 후:
1. TF-11 게이트웨이 설계 (미완료 시)
   -> 설계 문서 작성 -> 3-시각 재검토 -> 통과 후 다음
2. TF-10 Phase 0~1 (미완료 시)
   -> P1 확인 -> P2 구현 -> P3 구현 -> 1-1~1-4 구현 -> Phase 1.5 검증
3. TF-11 게이트웨이 구현
4. TF-10 Phase 2~4
```

### Step 4: 매 작업 후 확인
```bash
pytest tests/ -q                    # 전체 테스트 통과
ruff check .                        # 0 violations
```

---

## 6. 주요 파일 경로

### 6-1. 이번 작업에서 수정할 파일

| 파일 (절대 경로) | 역할 | 수정 Phase |
|------|------|-----------|
| `C:\Users\wjjo\Desktop\글도비\modules\models\arc.py` | ArcData Pydantic 모델 (L163-193) | Phase 1 (1-1) |
| `C:\Users\wjjo\Desktop\글도비\modules\core\response_schemas.py` | Gemini API 강제 스키마 (L260-298) | Phase 1 (1-2) |
| `C:\Users\wjjo\Desktop\글도비\config\prompts\ensemble.yaml` | Arc 생성 LLM 프롬프트 (L86-217) | Phase 1 (1-3) |
| `C:\Users\wjjo\Desktop\글도비\config\prompts\arc_generator.yaml` | Patch Mode 프롬프트 (L1-20) | Phase 1 (1-4) |
| `C:\Users\wjjo\Desktop\글도비\modules\domain\agents\four_phase_arc_generator.py` | ASP 경로 (L376) | Phase 0 (P2) |
| `C:\Users\wjjo\Desktop\글도비\modules\domain\agents\arc_corrector.py` | Arc 부분 수정 | Phase 0 (P3) |
| `C:\Users\wjjo\Desktop\글도비\modules\domain\agents\blueprint_constraint_compiler.py` | episode_focus/stop_line 추출 (L188, L236) | Phase 2 (2-1, 2-2) |
| `C:\Users\wjjo\Desktop\글도비\modules\domain\agents\blueprint_ensemble.py` | arc_focus 추출 (L148) | Phase 2 (2-3) |
| `C:\Users\wjjo\Desktop\글도비\modules\core\stage3_orchestrator.py` | TF9 Treatment Block 주입 (L512) | Phase 2 (2-4) |
| `C:\Users\wjjo\Desktop\글도비\modules\domain\agents\unified_arc_validator.py` | Arc 통합 검증 | Phase 3 (3-1) |
| `C:\Users\wjjo\Desktop\글도비\modules\domain\agents\arc_draft_validator.py` | Arc 사전 검증 | Phase 3 (3-2) |
| `C:\Users\wjjo\Desktop\글도비\modules\domain\agents\continuity_inspector.py` | 연속성 검증 | Phase 3 (3-3) |

### 6-2. 핵심 시스템 파일 (참조용, 수정 대상 아님)

| 파일 | 역할 |
|------|------|
| `C:\Users\wjjo\Desktop\글도비\CLAUDE.md` | 시스템 인수인계 문서 (대원칙, 현재 상태) |
| `C:\Users\wjjo\Desktop\글도비\docs\TF-10_episode_detail_map_analysis.md` | TF-10 전체 분석 + Section 11 (3-시각 재검토) |
| `C:\Users\wjjo\Desktop\글도비\modules\core\db_manager.py` | SQLite DB 매니저 |
| `C:\Users\wjjo\Desktop\글도비\modules\core\stage2_orchestrator.py` | Arc 오케스트레이터 (907줄) |
| `C:\Users\wjjo\Desktop\글도비\modules\core\stage2_validation_pipeline.py` | Stage2 검증 파이프라인 |
| `C:\Users\wjjo\Desktop\글도비\modules\core\stage2_finalizer.py` | Stage2 Finalizer |
| `C:\Users\wjjo\Desktop\글도비\modules\core\stage4_orchestrator.py` | 원고 오케스트레이터 (883줄) |
| `C:\Users\wjjo\Desktop\글도비\modules\core\stage4_context_builder.py` | Stage4 컨텍스트 빌더 |
| `C:\Users\wjjo\Desktop\글도비\modules\core\context_advisor.py` | Smart Context Retrieval |
| `C:\Users\wjjo\Desktop\글도비\modules\core\truth_gate.py` | 메모리 오염 방지 검증기 |
| `C:\Users\wjjo\Desktop\글도비\config\settings\validation.yaml` | 검증 임계값 설정 (stage3_enabled: true @ L174) |
| `C:\Users\wjjo\Desktop\글도비\modules\core\project_manager.py` | 프로젝트 관리 (Arc 저장: `save_v20_anchor("arcs", ...)`) |

### 6-3. 문서 파일

| 파일 | 내용 |
|------|------|
| `C:\Users\wjjo\Desktop\글도비\docs\MASTER_EXECUTION_GUIDE.md` | 이 문서 (마스터 실행 가이드) |
| `C:\Users\wjjo\Desktop\글도비\docs\TF-10_episode_detail_map_analysis.md` | TF-10 설계 분석 + 3-시각 재검토 |
| `C:\Users\wjjo\Desktop\글도비\docs\2026-02-23\next_steps_plan.md` | 후순위 관찰 대기 항목 |
| `C:\Users\wjjo\Desktop\글도비\docs\system_architecture.md` | 시스템 아키텍처 |
| `C:\Users\wjjo\Desktop\글도비\docs\pipeline_data_flow.md` | 파이프라인 데이터 흐름 |

---

## 7. 테스트 기준선

| 항목 | 값 |
|------|-----|
| pytest 통과 기준 | **2,583 passed + 0 xfailed** |
| 마지막 검증 | 2026-02-24 |
| Ruff | 0 violations |
| checkpoint 커밋 | `42e3954` |
| 테스트 명령어 | `pytest tests/ -q` |
| Ruff 명령어 | `ruff check .` |

**주의**: 작업 4(Phase 4) 완료 후 테스트 수는 2,597 이상이어야 한다 (기존 2,583 + 신규 14).

---

## 8. 후순위 항목 (관찰 대기)

다음 항목들은 현재 작업(TF-10/TF-11)이 모두 완료된 후 검토한다:

| 순위 | 항목 | 상세 |
|------|------|------|
| 2차 | 동적 장르 | 스토리 진행 중 장르 프리셋 추가 |
| 4차 | 캐시 | 컨텍스트 캐싱 최적화 |
| 5차 | 설정 SSOT | 설정 값 단일 소스화 |
| 후순위 | 근본 구조 개선 | Pydantic 전경계 강제, 계약 기반 테스트, 암묵적 계약 전수 제거 |

상세: `docs/2026-02-23/next_steps_plan.md`

---

## 9. 리스크 체크리스트

TF-10 구현 시 주의할 리스크 (TF-10 Section 10 + Section 11에서 도출):

| # | 리스크 | 등급 | 완화 방안 |
|---|--------|------|-----------|
| EC-1 | ArcCorrector 수정 후 episode_details 불일치 | HIGH | P3에서 해당 화 항목 삭제 구현 (전략 A) |
| EC-2 | ASP 경로 전체 Arc 교체로 details 소실 | HIGH | P2에서 교체 전 백업 + 복원 구현 |
| R1 | LLM이 episode_details 생성 실패 | MED | 선택 필드 + regex 폴백 유지 |
| R2 | episode_details와 tactical_doc 불일치 | MED | 프롬프트에 "tactical_doc에서 추출" 지시 |
| R6 | Gemini Schema 동적 키 미지원 | MED | list[dict] 타입으로 해결 완료 (D2 결정) |
| R3 | 토큰 비용 증가 | LOW | ~200토큰 수준, 무시 가능 |
| R4 | 기존 프로젝트 데이터 비호환 | LOW | default_factory=list + .get() 폴백 |

---

**문서 끝**
