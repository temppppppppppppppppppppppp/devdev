Date: 2026-03-23
Status: final (3-pass investigation complete)
Document Type: deep-dive report
Source Order: `docs/2026-03-23/director-verdict-deep-dive-order.md`
Axes Covered: Q2 (잘 고치냐), Q3 (잘 판단하냐), Q4 (잘 설명하냐), Q7-Director (잘 받냐)

---

# Director Pipeline 7-Axis Deep-Dive

## 1. Executive Summary

Director 판정 파이프라인은 **LLM 초기 판정 → 5단계 게이트 → 피드백 합성 → 재시도 스냅샷** 구조로 동작한다.

**Q3 (잘 판단하냐)**: 판정 소유권은 명확하다. LLM이 초기 verdict를 생산하고, 5개 Python 게이트가 순차 적용된다 (모순 방화벽 → 적응 임계값 → 품질 바닥 → PASS_WITH_FIX 계약 → 사후 연속성 검증). 게이트 간 우선순위와 override 규칙은 일관성 있다.

**Q2 (잘 고치냐)**: fix_scope/fix_pack이 LLM → 방화벽 override → 계약 검증 → reject guidance를 거치며 정제된다. 구조적으로 건전하나, REJECT 경로에서 `rejection_reason` 필드가 원본 `reject_reason` 대신 merged `director_feedback` 문자열로 대체되는 **필드 손실** 1건 발견.

**Q4 (잘 설명하냐)**: verdict_reason/selection_reason이 DB까지 전달되나, 중간에 **500자 절삭** 다수 존재. 특히 contradiction_details가 5→3건으로 축소되며, feedback dict→string 변환 시 구조 정보가 소실된다.

**Q7-Director (잘 받냐)**: Director 입력 팩은 decision_core + candidate_evidence + reference_appendix 3계층으로 조립된다. 8개 병렬 advisory, 30+60화 lookback, per-candidate validation이 모두 도달한다. 컨텍스트 캐싱(600s TTL)으로 안정 컨텍스트는 재사용. **필수 필드 누락 없음**.

**핫스팟 요약**: P0 0건, P1 3건 (feedback 필드 손실, contradiction 축소, verdict_reason 절삭), P2 4건.

---

## 2. Verdict Ownership Map

| 판정 결정 | 소유자 | 파일 | 메서드 | 라인 |
|-----------|--------|------|--------|------|
| **후보 선택** (A/B/C) | DirectorEnsembleSelector | director_ensemble.py | `select_and_judge_ensemble` → `_resolve_ensemble_selection_state` | L1981-2093, L2072-2076 |
| **초기 verdict** (LLM) | DirectorEnsembleSelector | director_ensemble.py | `select_and_judge_ensemble` (LLM 호출 + 파싱) | L2030-2086 |
| **모순 방화벽** | DirectorEnsembleSelector | director_ensemble.py | `_apply_ensemble_quality_gates` | L962-1004 |
| **적응 임계값** | DirectorGradingSystem | director_grading.py | `apply_adaptive_decision` (via L1075) | (참조) |
| **품질 바닥 게이트** | Stage4InterviewRound | stage4_interview_round.py | `_process_verdict` | L3687-3699 |
| **PASS_WITH_FIX 계약** | Stage4InterviewRound | stage4_interview_round.py | `_enforce_pass_with_fix_contract` | L1688-1733 |
| **최종 verdict 정규화** | Stage4InterviewRound | stage4_interview_round.py | `_normalize_director_gate_semantics` | L1764-1798 |
| **점수 계산** | DirectorEnsembleSelector | director_ensemble.py | `_apply_ensemble_quality_gates` | L945-1093 |
| **gate_basis 결정** | director_ensemble | director_ensemble.py | `_derive_gate_basis` | L264-281 |
| **fix_scope 결정** | DirectorEnsembleSelector | director_ensemble.py | `_build_ensemble_decision_payload` | L1095-1265 |
| **fix_pack 정규화** | director_ensemble | director_ensemble.py | `_normalize_fix_pack` | L216-261 |
| **fix_pack 검증** | Stage4InterviewRound | stage4_interview_round.py | `_evaluate_pass_with_fix_contract` | L1696 |
| **PASS_WITH_FIX 실행** | Stage4RetryRuntime | stage4_retry_runtime.py | `execute_pass_with_fix_loop` | L90-200+ |
| **REJECT 처리** | Stage4RejectRuntime | stage4_reject_runtime.py | `handle_reject` | L54-194 |

**Shell vs Semantic Core 경계**:
- **Shell** (배관): `Stage4DirectorRuntime` (L349-622) — 호출 조율, 로깅, 아티팩트
- **Semantic Core** (의미): `DirectorEnsembleSelector.select_and_judge_ensemble()` — 프롬프트 구성, LLM 호출, 응답 파싱, 게이트 적용

---

## 3. Gate Basis / Override Map

### 게이트 흐름도

```
Director LLM 출력
  ↓
_resolve_ensemble_selection_state() — 후보 추출 (A/B/C)
  ↓
_apply_ensemble_quality_gates()
  ├─→ [1. 모순 방화벽] CRITICAL/MAJOR 모순?
  │     YES → PASS_WITH_FIX (수리가능) 또는 REJECT (불가)
  │     score ≤ 44 강제
  ├─→ [2. 단일 후보 캡] 적격 1건 & score≥95?
  │     score → 90
  └─→ [3. 적응 임계값] apply_adaptive_decision(score, verdict, arc_pos...)
        → final_verdict
  ↓
_build_ensemble_decision_payload() — 최종 dict 조립
  ↓
_normalize_director_gate_semantics() — verdict 필드 정규화
  ↓
_process_verdict()
  ├─→ [4. 품질 바닥] PASS but score<90?
  │     PASS → REJECT (gate_basis: quality_floor_fail)
  └─→ if PASS/PASS_WITH_FIX:
        [5. PASS_WITH_FIX 계약] fix_pack 불완전?
          PASS_WITH_FIX → REJECT
        ↓
        _process_positive_verdict()
          ├─→ _run_post_select_checks() — 연속성/차단 검증
          └─→ if PASS_WITH_FIX:
                execute_pass_with_fix_loop() (최대 3회 패치)
```

### 게이트 상세

| 게이트 | 유형 | 위치 | 트리거 | 동작 |
|--------|------|------|--------|------|
| **모순 방화벽** | verdict 변환 | director_ensemble.py L962-1004 | CRITICAL≥1 또는 MAJOR≥2 | REJECT 또는 PASS_WITH_FIX, score≤44 |
| **단일 후보 캡** | score 제한 | director_ensemble.py L957-960 | 적격 1건 + score≥95 | score→90 |
| **적응 임계값** | score/verdict 조정 | director_grading.py (via L1075) | arc 위치, 에피소드 수, 재시도 횟수 | 임계값 기반 pass/fail |
| **품질 바닥** | verdict 하향 | stage4_interview_round.py L3687-3699 | PASS but score<90 | PASS→REJECT |
| **PASS_WITH_FIX 계약** | verdict 하향 | stage4_interview_round.py L1688-1733 | fix_pack 불완전 | PASS_WITH_FIX→REJECT |
| **사후 연속성** | verdict 하향 | stage4_interview_round.py L3831-3845 | 연속성/차단 검증 실패 | verdict→REJECT |

### Verdict 추출 우선순위
1. `director_result.get("final_verdict")`
2. `director_result.get("verdict")`
3. `director_result.get("director_verdict")`
4. 기본값: `"REJECT"` (L1773-1778)

### 수리가능 모순 유형 (방화벽 fixable)
고유명사, 이름, 직급, 호칭, 위치명, 지명, 장소, 금지표현 — director_ensemble.py L313-343

### 수리불가 → 자동 REJECT 조건
- fixable 유형 아님 AND fixable 텍스트 마커 없음
- 모순 총 ≥3건
- continuity_score < 30
- 원래 verdict가 PASS/PASS_WITH_FIX 아님

### gate_basis 매핑 (L264-281)
| 조건 | gate_basis |
|------|-----------|
| 방화벽 발동 | `continuity_firewall` |
| LLM PASS but 게이트 REJECT | `quality_floor_fail` |
| 최종 PASS | `director_primary_pass` |
| 최종 PASS_WITH_FIX | `director_primary_pass_with_fix` |
| 그 외 | `director_primary_reject` |

---

## 4. Fix / Retry Feedback Flow

### 4.1 필드별 생산→소비 추적

#### `reject_reason` → `rejection_reason`

| 단계 | 위치 | 변환 |
|------|------|------|
| 생산 | director_ensemble.py L1237 | `verdict_reason`의 alias |
| **P1-HOT** 소비 | stage4_reject_runtime.py L342 | `rejection_reason = director_feedback` (merged 문자열로 대체) |

> **[P1] 필드 손실**: retry snapshot의 `rejection_reason`이 원본 구조화된 `reject_reason`이 아닌 합성된 `director_feedback` 문자열을 담고 있다. 원본 LLM reject_reason은 이 시점에서 복구 불가.

#### `verdict_reason`

| 단계 | 위치 | 변환 |
|------|------|------|
| 생산 | director_ensemble.py L1111 | LLM `verdict_reason` → fallback: `firewall_reason` → first issue |
| 중간 | stage4_director_runtime.py L643 | `reason = verdict_reason` (alias) |
| **P1-HOT** 소비 | stage4_interview_round.py L400 | `_compact_text(verdict_reason, limit=500)` — 500자 절삭 |
| DB 저장 | stage4_interview_round.py L2251 | 절삭된 값 저장 |

> **[P1] 절삭**: 500자 초과 verdict_reason은 비가역적으로 잘린다. 긴 모순 설명 시 핵심 정보 유실 가능.

#### `fix_scope` / `fix_scope_reasoning`

| 단계 | 위치 | 변환 |
|------|------|------|
| 생산 | director_ensemble.py L1121-1122 | LLM 응답에서 추출 |
| 방화벽 override | director_ensemble.py L1132-1137 | 방화벽 active & scope∉{partial,full} → `"inplace"` 강제 |
| 연속성 replay | stage4_reject_runtime.py L430-431 | scope=="" 또는 "inplace" → `"partial"` 승격 |
| 계약 검증 | stage4_reject_runtime.py L444-459 | `"inplace"` & fix_pack 불완전 → `"partial"` 확대 |

> 방화벽 override 시 원래 fix_scope 값이 별도 보존되지 않음 (관찰 전용 위험).

#### `contradiction_details`

| 단계 | 위치 | 변환 |
|------|------|------|
| 생산 | director_ensemble.py L965 | `_compact_contradiction_details(entries, limit=5)` — **5건 제한** |
| **P1-HOT** 소비 | stage4_reject_runtime.py L365 | `[:3]` — **3건으로 추가 축소** |
| 피드백 합성 | stage4_interview_round.py L600-609 | 행당 80자 절삭 |

> **[P1] 정보 축소**: 모순이 6건 이상이면 5건으로 잘리고, retry snapshot에선 3건만 전달. 다중 모순 시나리오에서 ChiefWriter가 일부 모순만 교정할 위험.

#### `director_feedback` (합성 피드백)

합성 경로:
1. **director_ensemble.py L1100-1242**: LLM feedback dict + 모순 요약 + action_items + open_review
2. **stage4_interview_round.py L556-658** `_build_retry_feedback_provenance()`:
   - system_lines (이전 라운드 시스템 접두사)
   - evidence_summary (검증 근거, 500자)
   - director_feedback_text (LLM 피드백 + 이슈)
   - retry_directives (이전 라운드 일반 피드백, 500자)
   - runtime_advisory (advisory 다이제스트)
3. **stage4_reject_runtime.py L413**: `merged_feedback` 사용

> 각 섹션 500자 독립 절삭. feedback dict→string 변환 시 필드 경계 소실.

#### `action_items`

| 단계 | 위치 | 변환 |
|------|------|------|
| 생산 | director_ensemble.py L1149-1158 | LLM items + 모순 hint 자동 추가, **5건 제한**, 자동생성 시 160자/건 |
| 소비 | stage4_reject_runtime.py L415 | 그대로 전달 |
| 로깅 | stage4_interview_round.py L403 | 20건 제한 (원본 이미 5건이라 무영향) |

#### `retry_directives`

| 단계 | 위치 | 변환 |
|------|------|------|
| 생산 | stage4_interview_round.py L636-637 | 이전 director_feedback에서 시스템 접두사 아닌 행 추출, `" / "` 결합, **500자** |
| 소비 | stage4_reject_runtime.py L370 | retry snapshot에 저장 |

> 줄바꿈→`" / "` 변환으로 구조 정보 소실. 시스템 접두사 필터링이 정규식 기반이라 오분류 가능.

#### `feedback_provenance`

```python
{
  "merged_feedback": str,      # 합성 피드백 전체
  "system_feedback": str,      # 시스템 접두사만
  "evidence_summary": str,     # 검증 근거 (500자)
  "director_feedback_text": str, # LLM 피드백+이슈
  "runtime_advisory": str,     # advisory 다이제스트
  "retry_directives": str,     # 이전 라운드 지시 (500자)
}
```

provenance dict 자체는 온전하나 구성 필드들이 개별 절삭됨.

### 4.2 피드백 흐름 요약도

```
LLM 응답
  │
  ├─ verdict_reason ──────────────────────────────── DB (500자 절삭)
  ├─ feedback.issues ─┐
  ├─ action_items ────┤
  ├─ open_review ─────┤
  └─ contradiction ───┤
                      ↓
         _build_ensemble_selection_result()
                      │
                      ├─ director_result dict ────── Stage4DirectorRuntime
                      │                               │
                      │                    _build_retry_feedback_provenance()
                      │                               │
                      │                    ┌──────────┼──────────┐
                      │                    │          │          │
                      │              system_lines  evidence  director_text
                      │                    │          │          │
                      │                    └──→ merged_feedback ←┘
                      │                               │
                      └─────────────────→ _build_reject_guidance_payload()
                                                      │
                                           ┌──────────┼──────────┐
                                           │          │          │
                                      reject_bucket  fix_scope  director_feedback
                                           │          │          │
                                           └──→ retry_snapshot ←─┘
                                                      │
                                                      ↓
                                                next round ChiefWriter
```

---

## 5. Director Context Reception Map

### 5.1 입력 팩 구조

```python
@dataclass
class _DirectorInputPackResult:
    mandatory_context: str       # decision_core + candidate_evidence + reference_appendix
    decision_core: str           # 필수 컨텍스트 + POV + 작성 지시 + 공유 실패
    candidate_evidence: str      # 8 advisory + temporal + validation
    reference_appendix: str      # DB 통계 + 가드 규칙
    advisory_summary: dict       # {"truth_gate": 1, "npc_drift": 0, ...}
```

### 5.2 조립 파이프라인

```
Stage4InterviewRound.run()
  → Stage4DirectorRuntime.run_director_review_phase()
    → build_director_input_pack()
      ├─ _build_director_decision_core_parts()
      │    ├─ mandatory_context (필수)
      │    ├─ shared_failure_warnings (있으면)
      │    ├─ POV 설정 (있으면)
      │    ├─ writing_directive (있으면)
      │    └─ S3-META advisory (있으면)
      │
      ├─ _build_director_candidate_evidence_parts()
      │    ├─ _run_advisory_chain() → 8 병렬 advisory (300s timeout)
      │    ├─ _build_director_temporal_evidence_parts() → timeline + arc 마커
      │    └─ _build_director_validation_feedback_evidence_parts() → per-candidate warnings
      │
      └─ _build_director_reference_appendix_parts()
           ├─ 후보 다양성 advisory
           ├─ DB pacing/satisfaction/reveals/reflexion
           ├─ 전략 승률
           ├─ fix_scope 통계
           └─ WorkGuard 규칙
```

### 5.3 프롬프트 2분할 (컨텍스트 캐싱)

| 파트 | 내용 | 캐싱 | 크기 |
|------|------|------|------|
| **STABLE_CONTEXT** | story_context, blueprint(JSON), previous_ending, prev_manuscripts(30+60화), episode_digest, decision_core | 600s TTL | ~180K |
| **VARIABLE_PROMPT** | 3 manuscripts(A/B/C) + per-candidate warnings + candidate_evidence + reference_appendix | 매번 새로 | ~5-20K |

### 5.4 필수/선택 필드 현황

| 필드 | 필수? | 절삭 | 빈 값 가능? | 비고 |
|------|-------|------|------------|------|
| `mandatory_context` | YES | 400K 기본 | NO | — |
| `blueprint` | YES | 프롬프트 내장 | NO | stable 캐시 |
| `previous_ending` | YES | 프롬프트 내장 | YES | "(unavailable)" 대체 |
| `candidates` (3건) | YES | 없음 | NO | <3이면 패딩 |
| `validation_results` (3건) | YES | 건당 30개 경고 | NO | <3이면 패딩 |
| `episode_digest` | YES | 프롬프트 내장 | YES | "(unavailable)" 대체 |
| `prev_manuscripts_text` | 선택 | Tier1: 전문, Tier2: 5K/화, Tier3: 8K/arc | YES | DB 실패 시 비차단 |
| `candidate_evidence` | 선택 | 220K | YES | advisory 전부 "이상 없음" 가능 |
| `reference_appendix` | 선택 | 120K | YES | DB 통계 없으면 생략 |
| `pov_config` | 선택 | 없음 | YES | master_bible 없으면 생략 |
| `writing_directive` | 선택 | 없음 | YES | 빈 값이면 생략 |

### 5.5 8 Advisory 병렬 체인

```
ThreadPoolExecutor(max_workers=8, timeout=300s)
  ├─ TruthGate       (LLM, 60s)   — 팩트/플롯 일관성
  ├─ NpcDrift         (LLM, 60s)   — NPC 성격 이탈
  ├─ NumericDrift     (LLM, 60s)   — 수치 불일치
  ├─ Flashback        (LLM, 60s)   — 허위 회상
  ├─ InfoParadox      (LLM, 60s)   — 논리 역설
  ├─ RelDrift         (LLM, 60s)   — 관계 이탈
  ├─ LongTermRep      (LLM, 60s)   — 평판 추적
  └─ NumericConsistency(Python, 60s) — 수치 정합성
```

### 5.6 필수 필드 누락 여부

**누락 없음**. 모든 판정 필수 컨텍스트가 Director 도달 시점에 존재하거나, 명시적 fallback이 있다.

---

## 6. Top Hotspots

### P1 (3건)

| ID | 위치 | 설명 | 축 |
|----|------|------|----|
| **H-1** | stage4_reject_runtime.py L342 | `rejection_reason`이 원본 `reject_reason` 대신 merged `director_feedback`로 대체. retry snapshot에서 구조화된 거부 사유 복구 불가 | Q4 |
| **H-2** | stage4_reject_runtime.py L365 + director_ensemble.py L374 | contradiction_details 5→3건 축소. 다중 모순 시 ChiefWriter가 일부만 교정할 위험 | Q2 |
| **H-3** | stage4_interview_round.py L400 | verdict_reason 500자 절삭. 복합 모순 시나리오에서 핵심 설명 유실 가능 | Q4 |

### P2 (4건)

| ID | 위치 | 설명 | 축 |
|----|------|------|----|
| **H-4** | stage4_interview_round.py L637 | retry_directives 줄바꿈→`" / "` 변환. 구조 정보 소실 | Q2 |
| **H-5** | director_ensemble.py L1133 | 방화벽 fix_scope override 시 원래 값 미보존 (관측성 한계) | Q4 |
| **H-6** | stage4_interview_round.py L632 | evidence_summary 500자 절삭. 검증 근거 다수 시 후행 근거 유실 | Q2 |
| **H-7** | director_ensemble.py L1158 | action_items 5건 제한. 복합 문제 시 일부 수정 지시 누락 가능 | Q2 |

---

## 7. Quick Wins

| ID | 유형 | 설명 | 예상 효과 |
|----|------|------|-----------|
| **QW-1** | observability-only | retry snapshot에 `original_reject_reason` 필드 추가 (H-1) | 원본 거부 사유 추적 가능 |
| **QW-2** | observability-only | 방화벽 override 시 `original_fix_scope` 로깅 (H-5) | override 빈도/패턴 관측 |
| **QW-3** | comment-only | retry_directives 결합 시 `" / "` 대신 `"\n"` 사용 검토 주석 (H-4) | 구조 보존 여부 평가 기초 |
| **QW-4** | observability-only | contradiction_details 5→3 축소 시 drop_count 로깅 (H-2) | 정보 손실 빈도 관측 |

---

## 8. Refactor Candidates

| ID | 유형 | 설명 | 복잡도 |
|----|------|------|--------|
| **RC-1** | contract-cleanup | `rejection_reason` vs `reject_reason` 필드 네이밍 통일. retry snapshot이 원본 reject_reason을 보존하도록 수정 | 낮음 |
| **RC-2** | boundary-refactor | contradiction_details 축소 한도를 retry snapshot에서 5건으로 통일 (현재 5→3 이중 축소) | 낮음 |
| **RC-3** | contract-cleanup | verdict_reason 절삭 한도를 500→1000자로 상향 (복합 모순 시나리오 커버) | 낮음 |
| **RC-4** | boundary-refactor | feedback dict→string 변환을 구조화된 섹션 dict로 유지하고, 최종 프롬프트 조립 시점에만 string화 | 중간 |
| **RC-5** | ignore | action_items 5건 제한 — 현실적으로 5건 초과 시 ChiefWriter 주의력 분산. 현행 유지 권장 | — |

---

## 9. Confidence And Limits

**전체 신뢰도: 95%**

### 근거
- 7개 in-scope 파일 전수 조사 (3-pass)
- verdict 소유권, 게이트 체인, 피드백 흐름, 컨텍스트 수신 모두 라인 앵커 기반 매핑
- reject/retry 경로 데이터 흐름 전수 추적

### 한계
- `director_grading.py`의 `apply_adaptive_decision` 내부 로직은 참조만 확인 (직접 조사 범위 외)
- `_build_retry_advisory_digest()` 내부 구현은 호출부만 확인
- Director 프롬프트 YAML 템플릿(`director.yaml`)의 텍스트 수준 분석은 수행하지 않음 (프롬프트 품질은 별도 축)
- 실제 런타임 로그 기반 검증 미수행 (코드 정적 분석만)

### Director-side vs Generator-side 분리
본 보고서의 모든 발견사항은 **Director-side** 판정/피드백/컨텍스트에 한정된다. ChiefWriter 생성 품질, WorldState/FactLedger 내부 로직, 메모리 시스템은 의도적으로 제외하였다.
