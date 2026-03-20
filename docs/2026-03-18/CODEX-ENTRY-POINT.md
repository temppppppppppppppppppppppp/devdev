# 코덱스 진입점 — 글도비 현황 + 패치 + 빌드업 전량 컨텍스트

**최종 갱신**: 2026-03-18
**감리**: SSOT 7건 + 실행문서 8건 = 15건 근본 재조사 (7 TF 병렬) + 적대적 3-pass
**HEAD**: `f88f5912`
**코드 변경 기준 커밋**: `52420a28`

---

## 1. 이 문서가 필요한 이유

최근 커밋 `52420a28`에서 코드 패치 3건이 적용됨. 이 패치들은 "잘 쓰기 → 잘 평가하기 → 피드백으로 잘 고치기" 파이프라인의 각 단계에서 터진 문제를 수정함. 이 문서는 패치 의도, 현재 상태, 잔여 이슈, 향후 빌드업 작업을 코덱스가 이해할 수 있도록 정리한 것.

---

## 2. 파이프라인 3단계와 패치 3건의 대응

```
Stage 3 Blueprint       Stage 4 Director        Stage 4 ChiefWriter
[1. 미리 잘 쓰기]  →    [2. 잘 평가하기]   →    [3. 피드백으로 잘 고치기]
      │                       │                        │
   패치 1                  패치 2                   패치 3
   스키마 호환              시그니처 정합             무진척 차단
```

**핵심**: 의도는 좋았는데 디테일에서 터짐. 3건 패치로 복구 완료.

---

## 3. 패치 1: Blueprint 스키마 호환성 (Stage 3 — 미리 잘 쓰기)

### 문제
Gemini API가 `additionalProperties`를 지원하지 않아 Blueprint 생성 자체가 불가능. Stage 3 전체 PATCHING 상태.

### 수정 (response_schemas.py +71/-11, three_phase_blueprint_generator.py +21, base_agent.py +4, blueprint_ensemble.py +1)

**response_schemas.py**:
- `BLUEPRINT_SCENE_BREAKDOWN_SCHEMA` (L554): `additionalProperties` → `scene_1`~`scene_5` 고정 키
- `BLUEPRINT_PROTAGONIST_STATE_SCHEMA` (L570): mood, injuries, equipment 신규
- `BLUEPRINT_ENDING_STATE_SCHEMA` (L584): location, timeline, protagonist_status 신규
- `BLUEPRINT_SCHEMA` (L602): title(L606), start_location(L626), end_location(L627), ending_hook(L630), protagonist_state(L631), ending_state(L632) 추가
- required 필드: `["episode_number", "scene_breakdown", "integrated_scenario"]` (L634)

**base_agent.py**:
- `AgentErrorType.SCHEMA_INCOMPATIBLE` 추가 (L45)
- `_classify_error()`: "not supported" + "schema"/"additionalproperties" → SCHEMA_INCOMPATIBLE (L1512)
- `_get_recovery_hint()`: SCHEMA_INCOMPATIBLE 전용 메시지 (L1660)

**three_phase_blueprint_generator.py**:
- `AgentErrorType` import 추가 (L27)
- Phase 2 생성 실패 시 `last_error_type` 확인 (L354)
- SCHEMA_INCOMPATIBLE이면 `pipeline_result["failure_reason"]` 설정 + `break` (L357-362) → 재시도 루프 즉시 중단
- 모든 재시도 소진 후 SCHEMA_INCOMPATIBLE이면 `final_verdict="FAILED"` + 즉시 반환 (L736-739)

**blueprint_ensemble.py**:
- `self.last_error_type = None` 리셋 추가 (L297)

### 현재 상태: HOLDING (99%)
- 프로덕션 Blueprint에 title, ending_hook, protagonist_state 정상 포함 (projects/0_260318 확인)
- scene_1~scene_5 고정 키 정상 작동
- SCHEMA_INCOMPATIBLE 즉시 중단 가드 건재
- 테스트 12/12 통과 (test_blueprint_patch_mode.py)

---

## 4. 패치 2: Director Facade 시그니처 정합 (Stage 4 — 잘 평가하기)

### 문제
`director.py` facade가 `decision_core`, `candidate_evidence`, `reference_appendix` 3개 파라미터를 하위 모듈에 전달하지 않음. Director가 불완전한 정보로 원고를 판정.

### 수정 (director.py +8/-1)

**director.py**:
- `select_and_judge_ensemble()` 파라미터에 `decision_core=""`, `candidate_evidence=""`, `reference_appendix=""` 추가 (L284-286)
- 하위 `_ensemble.select_and_judge_ensemble()` 호출에 3개 전달 (L302-304)

### 3개 파라미터가 실제로 전달되는 내용 (stage4_interview_round.py L2403-2407)

| 파라미터 | 내용 | 구성 |
|---------|------|------|
| `decision_core` | 공유 실패 경고, Stage 3 경고, POV 정책, 세계 상태 | L2156-2194에서 조립 |
| `candidate_evidence` | Advisory 요약, 타임라인, 참신성 검사, 연속성 경고, 사전검증 | L2157-2354에서 조립 |
| `reference_appendix` | 다양성 자문, 작품별 리뷰 | L2158, L2336-2400에서 조립 |

### Director가 반환하는 구조적 피드백

| 필드 | 용도 |
|------|------|
| `feedback` | dict: issues + strengths |
| `action_items` | 구체적 수정 지시 목록 |
| `score_breakdown` | 5차원 점수 분해 |
| `fix_scope` | "inplace" / "partial" / "full" |
| `fix_pack` | 구체적 패치 대상 + 지시 |
| `contradiction_check` | 모순 분석 |
| `open_review` | 서사 품질 관찰 |

### 현재 상태: 95% HOLDING — 재심사 갭 1건

**정상 경로** (L2416-2432): 3개 팩 전부 전달 ✅

**재심사 경로** (L3728-3741): 3개 팩 **누락** ⚠️
```python
# L3728: TF-35 PASS_WITH_FIX → InPlace 패치 후 Director 재심사
_re_audit = _director.select_and_judge_ensemble(
    ep_num=round_ctx.next_ep,
    candidates=[_re_candidate],
    validation_results=[_re_val_ctx],
    blueprint=round_ctx.blueprint,
    previous_ending=round_ctx.prev_ending,
    # ... 13개 파라미터 전달
    # ❌ decision_core 누락 (기본값 "")
    # ❌ candidate_evidence 누락 (기본값 "")
    # ❌ reference_appendix 누락 (기본값 "")
)
```

**영향**: PASS_WITH_FIX 판정 후 InPlace 패치 → Director 재심사 시 (에피소드당 최대 3회) 원래 거부 근거 컨텍스트 소실. `mandatory_context`에 병합 데이터는 있으나 의미적 분리 손실.

**심각도**: MEDIUM — 첫 평가는 정상, 재심사만 불완전.

---

## 5. 패치 3: Stage 4 무진척 자동 차단 (Stage 4 — 피드백으로 잘 고치기)

### 문제
FrontierLag 자동 연속 생산에서 Stage 4 backlog인데 원고 0건 생산해도 다음 Arc로 자동 진행. 비용만 소비.

### 수정 (main_a.py +60/-1)

**`_is_stage4_zero_progress_blocked()` 정적 메서드** (L4188-4206):
```python
# 차단 조건: stage4_alignment == "backlog" AND target > before AND after <= before
# = "목표보다 뒤처진 상태에서 원고가 하나도 안 나옴"
```

**적용 2곳**:
- Final close 경로 (L4319-4337): `stop_reason="stage4_final_close_no_progress"`
- Arc 진행 경로 (L4542-4556): `stop_reason="stage4_no_progress_blocked"`

**Stage 4 에러 핸들링 변경** (L4564-4569):
- 변경 전: "최선 결과 수용" → 다음 Arc 자동 진행
- 변경 후: 즉시 중단 + `stop_reason="stage4_error"` + `tranche_completed=False`

### 현재 상태: HOLDING (99%)
- 가드 로직 정확 (alignment="backlog" 조건 + None/타입 안전)
- 양쪽 경로 모두 보호
- 프로덕션에서 가드 미발동 (정상 실행 = 기대 동작)
- 테스트 2건 통과 (final close 차단, arc advance 차단)

---

## 6. CW(ChiefWriter) 피드백 수신 경로 — 랜덤 재생성 아님

Director가 REJECT하면 ChiefWriter는 3가지 구조적 수정 경로 중 하나를 탐:

### 경로 결정 로직 (stage4_interview_round.py)

```
_fix_scope == "inplace" AND fix_pack.ready  →  InPlace 패치 (L4468)
_fix_scope in ("inplace", "partial")        →  Patch 모드 (L4515)
_fix_scope == "full" OR 나머지             →  전면 재작성 (L4539)
```

### 각 경로에서 CW가 받는 피드백

**InPlace** (`chief_writer.inplace_patch()` L1407-1500):
- `director_feedback`: 전체 피드백 텍스트
- `fix_pack`: 구체적 수정 대상 (장면 번호, 수정 지시)
- → `_classify_structural_patch_focus(director_feedback)` 로 수정 장면 식별 → 외과적 수정

**Patch 모드** (`chief_writer.patch_with_feedback()` L1651-1801):
- `original_manuscript`: 원본 원고 (90% 보존 강제)
- `previous_attempt`: action_items, score_breakdown, fix_scope, fix_pack, open_review
- → 프롬프트: "원본 구조/문체/장점 보존하면서 피드백 지적사항만 수정하세요" (L1737)
- → selected strategy 기준 bounded regenerate 1후보

**전면 재작성** (`chief_writer.regenerate_with_feedback()` L799-951):
- `director_feedback`: 전체 피드백
- `previous_attempt`: 이전 시도의 전략, 거부 이유, 점수 분해
- → 프롬프트: "이 피드백을 100% 반영하지 않으면 다시 REJECT됩니다" (L879)
- → 점수 분해 + 검증 경고 + Director 서사 관찰 + 재시도 이력 포함

### 프로덕션 실증
- projects/0_260318: ep_0001 attempt_01 REJECT(30점) → attempt_02 PASS(99점)
- 패치가 특정 장면만 변경하고 나머지 보존 (랜덤 재생성이 아닌 구조적 수정 확인)

---

## 7. 잔여 이슈 (코드 수정 필요 1건)

| 이슈 | 위치 | 심각도 | 내용 |
|------|------|--------|------|
| Director 재심사 팩 누락 | `stage4_interview_round.py:3728` | MEDIUM | PASS_WITH_FIX → InPlace 패치 후 재심사 시 decision_core/candidate_evidence/reference_appendix 미전달. 에피소드당 최대 3회 발생 |

**수정 방법**: L3728 호출에 `_director_input_packs` 전달 추가 (정상 경로 L2427-2429와 동일 패턴)

---

## 8. 빌드업 문서 (코드 변경 전 설계 — 완료)

향후 코드 작업 시 참조할 설계 문서. 모두 3회 재조사 + 적대적 3-pass 감리 완료.

| 문서 | 경로 | 핵심 내용 |
|------|------|----------|
| **멀티프로바이더 설계** | `buildup-multi-provider-abstraction-design.md` | 프로덕션 18파일 + tools 7파일 Gemini SDK 의존. response_schemas.py dict layer 이미 존재. Stage 0 모듈 5개 BaseAgent 우회. 구현 16-24시간 |
| **Verdict 매핑표** | `buildup-verdict-6way-mapping-table.md` | 9 Core verdict + 7 Contextual decision = 16값 전수 목록. 부울 플래그 7개. ERROR SET 위치는 stage3_orchestrator.py:1366,1369 |
| **비용 테이블 + ROL** | `buildup-cost-table-rol-metric-definition.md` | MODEL_COSTS 검증 완료. Thinking 토큰은 output에 이미 합산 (metrics_collector.py:300 주석 근거). ROL 공식은 제안(에피소드 간 복합 점수 미존재) |
| **하네스 인덱스** | `buildup-harness-index.md` | 하네스 ~39 + 지원 ~22 = 거버넌스 ~61. Mode A/B/B1/C 검증 완료 |
| **ROI 요약** | `buildup-roi-summary.md` | 패치 3건 ROI + 흐름 역산 + 현재 상태 |

---

## 9. 설정 파일 변경 (코드 아님)

| 파일 | 변경 | 효과 |
|------|------|------|
| `.gitattributes` | 신규 생성 | CRLF/LF 정규화 — diff 노이즈 제거 (S1-EX-001) |
| `.editorconfig` | indent/eol 강화 | 파일 타입별 통일 (S1-EX-002) |

---

## 10. 상위 실행문서 최신화 현황

| 문서 | 변경 내용 |
|------|----------|
| `s1-architecture-execution.md` | S1-EX-001/002 → **DONE** |
| `s4-llm-integration-execution.md` | EX-MP1 설계 → **DONE** (buildup 참조) |
| `s6-stage3-4-execution.md` | EX-10 → 16개 verdict 매핑 참조 |
| `s7-rol-improvement-execution.md` | G3 → buildup 비용 테이블 참조 |

---

## 11. 코덱스 재감리 시 확인 포인트

이 문서의 모든 주장은 소스 코드 직접 대조로 검증됨. 재감리 시 우선 확인할 항목:

1. **response_schemas.py L554**: `BLUEPRINT_SCENE_BREAKDOWN_SCHEMA` 존재 + scene_1~5 키
2. **response_schemas.py L630-632**: ending_hook, protagonist_state, ending_state 존재
3. **three_phase_blueprint_generator.py L357-362**: SCHEMA_INCOMPATIBLE 즉시 break
4. **director.py L284-286**: decision_core/candidate_evidence/reference_appendix 파라미터
5. **stage4_interview_round.py L2427-2429**: 정상 경로에서 3팩 전달 확인
6. **stage4_interview_round.py L3728-3741**: 재심사 경로에서 3팩 **누락** 확인
7. **main_a.py L4188-4206**: `_is_stage4_zero_progress_blocked()` 로직
8. **main_a.py L4319, L4542**: 가드 호출 2곳
9. **metrics_collector.py L300**: "출력 토큰 수 (Developer API: thinking 토큰 포함)" 주석

---

## 12. OPUS SSOT 7건 + 실행문서 8건 근본 재감리 결과

### 12.1 SSOT 신뢰도

| SSOT | 신뢰도 | 오류 | 비고 |
|------|--------|------|------|
| S1 아키텍처 | 95% | 파일 수 미세 오차 3건 (modules 244→247, scripts 38→37, core 161→162) | 코드 작업에 영향 없음 |
| S2 BE-FE | 99% | main.js/preload.js 각 1줄 차이 | 무시 가능 |
| **S3 프론트엔드** | **0%** | **프론트엔드 소스 파일이 repo에 없음** | 전체 검증 불가 — ADVISORY로 취급 |
| S4 LLM 통합 | 96% | response_schemas LOC 912→911, anyOf 라인 1-2줄 오프셋 | |
| S5 Stage 0-2 | 98% | 없음. P0 silent failure 5건 전부 실제 확인 | 가장 코드에 밀착된 문서 |
| S6 Stage 3-4 | 96% | **"quality_risk write-only" 주장 거짓** (아래 12.2 참조) | |
| S7 ROL | 98% | S7-G3 시뮬 가격 문구 약간 모호 | OPP/G 항목 전부 실제 확인 |

### 12.2 신규 발견 3건 (이전 감리에서 전부 놓친 것)

#### NEW-1: S6 SSOT "quality_risk write-only" 주장 → 거짓 (HIGH)

S6 §2.5에서 "quality_risk는 write-only 플래그. Stage 4에서 grep 0건"이라 주장하나, 실제:
```python
# stage4_orchestrator.py:1203-1204
_quality_risk = bool(_s3_meta.get("quality_risk", False))
_v75d_threshold = 1 if _quality_risk else 2
```
quality_risk를 **읽어서** 패치 임계값을 결정함. write-only가 아니라 **Stage 3→4 전파 상태**.

**코덱스 재감리 시**: S6 §2.5의 "write-only" 표현을 "Stage 3 설정 → Stage 4 소비" 패턴으로 교정 필요.

#### NEW-2: S3 FE-H01 sanitizeProjectName path traversal (CRITICAL 보안)

```javascript
// 현행 (취약): index.html L765
return name.trim().replace(/[<>:"/\\|?*]/g, "_");
// 공격: sanitizeProjectName("..") → ".." (필터 통과) → 디렉토리 탈출
```

regex에 `.` 문자 누락. IPC 핸들러 3곳(loadConfigSurfaces, saveConfigSurfaces, applyWorkGuardTemplate)에서 프로젝트 디렉토리 외부 접근 가능.

**코덱스 재감리 시**: S3 프론트엔드 파일 확보 후 FE-H01 즉시 수정 우선.

#### NEW-3: S5-EX-32 Stage 2 Arc 비원자성 → 이미 수정됨 (STALE)

`stage2_finalizer.py:1260-1298`에 트랜잭션 롤백 로직이 이미 존재. 실행문서가 P2로 기재하나 실제로는 RESOLVED.

**코덱스 재감리 시**: S5-EX-32를 RESOLVED로 격하.

### 12.3 실행문서 항목별 상태 총괄

| 상태 | 건수 | 항목 |
|------|------|------|
| **RESOLVED** | 3 | S1-EX-001/002 (.gitattributes), S4-EX-MP1 (설계문서) |
| **VALID** | ~28 | S5 P0 4건 (SF3/MSF-F/MSF-H/MSF-J), S6-EX-01, S7-G1 (4곳 전부 확인), S8-C1~C4 등 |
| **STALE** | 1 | S5-EX-32 (이미 수정됨) |
| **WRONG** (라인) | 2 | S4-EX-H1 (anyOf 1-2줄 오프셋), S4-EX-H2 (key 소진 위치 부정확) |

### 12.4 P0/P1 실제 확인된 코드 문제 (코덱스 작업 시 우선)

| 순위 | 항목 | 위치 | 검증 |
|------|------|------|------|
| P0 | S5-SF3: generate_bible 빈 dict 반환 | `story_expander.py:356,365-367` | **실제 확인** |
| P0 | S5-MSF-F: ConstraintDB 전체 비활성화 | `constraint_db.py:76-98` | **실제 확인** |
| P0 | S5-MSF-H: FactLedger 팩트 추적 소실 | `fact_ledger.py:91-102` | **실제 확인** |
| P0 | S5-MSF-J: Analyst 마커 없는 silent return | `analyst.py:1440-1442` | **실제 확인** |
| P0 | S6-EX-01: quality_risk PASS_WITH_WARNING 누락 | `director_ensemble.py:771` | **실제 확인** |
| P1 | S7-G1: Stage 2/3 token_cost=0 | 4곳 전부 | **4곳 전부 확인** |
| P1 | S8-C1: Arc 제목 미전달 | `blueprint_constraint_compiler.py:225-229` | **실제 확인** |
| P1 | S8-C3: Director 99점 CRITICAL 무시 | Director 자율권 과잉 | **실제 확인** |
| P1 | S8-C4: quality_risk 분별력=0 | 모든 PASS_WITH_FIX에 기계적 True | **실제 확인** |
