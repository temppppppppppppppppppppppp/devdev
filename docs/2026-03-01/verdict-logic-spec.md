# 판정 로직 종합 명세 (Verdict Logic Specification)

> 2026-03-01 기준. Stage 2/3/4 전체 판정 경로 전수 조사 결과.

---

## 1. Verdict 값 목록

| Verdict | 의미 | 생산 Stage | 성격 |
|---------|------|-----------|------|
| **PASS** | 합격 | S2/S3/S4 | 최종 상태 |
| **PASS_WITH_FIX** | 합격 + 국소 수정 | S2/S3/S4 | **과도 상태** — 반드시 PASS 또는 REJECT로 전환 |
| **CONDITIONAL_PASS** | 조건부 합격 | ValidationOrch, DirectorEnsemble | adaptive ≤ 점수 < 85 |
| **REJECT** | 불합격 | 다수 생산자 | retry 경로 진입 |
| **PASS_WITH_WARNING** | 비상 합격 | S3 ThreePhase (L564) | 재시도 소진 + score ≥ REWRITE |
| **FAILED** | 생성 실패 | S2 FourPhase / S3 ThreePhase | 모든 재시도 소진 |

---

## 2. Stage별 판정 흐름

### 2.1 Stage 2 (Arc 생성)

```
FourPhase.generate()
  └─ UnifiedArcValidator.validate()
       └─ Director.audit_strategic_plan()  →  PASS / PASS_WITH_FIX / REJECT

Stage2ValidationPipeline.run_validation()  →  action: proceed / retry

Stage2Finalizer.run_finalize()
  ├─ QualityGate: PASS_WITH_FIX + score<90 → REJECT
  ├─ PASS_WITH_FIX → inplace loop (max 3)
  │   ├─ fix_scope="inplace" → _inplace_patch_arc + 재심사
  │   └─ fix_scope="partial/full" → break → REJECT
  ├─ 성공 → action: "break"
  └─ 실패 → action: "retry" (fix_scope 보존)

Stage2Preflight (재시도 시 3-tier 라우팅)
  ├─ _use_inplace → _inplace_patch_arc()
  ├─ _use_patch   → patch_arc_with_feedback(single_strategy=...)
  └─ else         → generate() (전면 재생성)
```

**핵심 파일·라인**:
- `stage2_finalizer.py` L242-366 — PASS_WITH_FIX 루프
- `stage2_finalizer.py` L245-277 — QualityGate 선검사
- `stage2_preflight.py` L796-892 — 3-tier 재시도 라우팅
- `four_phase_arc_generator.py` L528-581 — `_inplace_patch_arc()`
- `four_phase_arc_generator.py` L587-713 — `patch_arc_with_feedback()`

### 2.2 Stage 3 (Blueprint 생성)

```
ThreePhase.generate()
  └─ UnifiedBlueprintValidator.validate()
       ├─ compare 경로 (다후보): Director.compare_and_select_blueprint()
       └─ audit 경로 (단일):    Director.audit_manuscript()
       → verdict: PASS / PASS_WITH_FIX / REJECT

QualityGate: PASS/PASS_WITH_FIX + score<90 → REJECT

PASS_WITH_FIX → inplace loop (max 3)
  ├─ fix_scope="inplace" → _inplace_patch_blueprint + 재심사
  └─ fix_scope="partial/full" → break → REJECT

재시도 시 3-tier:
  ├─ _use_inplace → _inplace_patch_blueprint()
  ├─ _use_partial → ensemble(single_strategy=...)  ← S3만 독립 변수
  └─ else         → ensemble() (전면 재생성)

비상: 재시도 소진 + score≥REWRITE → PASS_WITH_WARNING
```

**핵심 파일·라인**:
- `three_phase_blueprint_generator.py` L415-420 — QualityGate
- `three_phase_blueprint_generator.py` L427-507 — PASS_WITH_FIX 루프
- `three_phase_blueprint_generator.py` L209-280 — 3-tier 재시도 라우팅
- `unified_blueprint_validator.py` L100-142 — compare 경로 (fix_scope 전파 L133)
- `unified_blueprint_validator.py` L185-314 — audit 경로 (fix_scope 전파 L306)

### 2.3 Stage 4 (원고 생성)

```
InterviewRound.run_interview_round()
  └─ DirectorEnsemble.select_and_judge_ensemble()
       ├─ LLM verdict: PASS / PASS_WITH_FIX / REJECT
       ├─ V60.97 길이 스왑 → CONDITIONAL_PASS (score=50)
       ├─ V75-C 모순 방화벽: CRITICAL≥1 or MAJOR≥2 → REJECT (score≤44)
       └─ Adaptive Decision: 점수 기반 verdict 조정

QualityGate: PASS/PASS_WITH_FIX + score<90 → REJECT
Post-Select 검증: 연속성/이력 충돌 → REJECT

PASS_WITH_FIX → inplace loop (max 3)
  ├─ fix_scope="inplace" → chief_writer.inplace_patch() + 재심사
  └─ fix_scope="partial/full" → break → REJECT

재시도 시 3-tier:
  ├─ _use_inplace → inplace_patch()
  ├─ _use_patch   → patch_with_feedback(single_strategy=...)
  └─ else         → regenerate_with_feedback() (전면 재작성)
```

**핵심 파일·라인**:
- `stage4_interview_round.py` L1127 — Director verdict 추출
- `stage4_interview_round.py` L1206-1213 — QualityGate
- `stage4_interview_round.py` L1277-1281 — Post-Select 충돌 검증
- `stage4_interview_round.py` L1290-1378 — PASS_WITH_FIX 루프
- `stage4_interview_round.py` L155-224 — 3-tier 재시도 라우팅
- `director_ensemble.py` L593 — V60.97 길이 스왑
- `director_ensemble.py` L608-617 — V75-C 모순 방화벽
- `director_ensemble.py` L625-644 — Adaptive Decision

---

## 3. Verdict 전환 규칙 (전체)

| # | 위치 | 원래 | 조건 | 결과 | 근거 |
|---|------|-----|------|------|------|
| 1 | S2 Finalizer L245 | PASS_WITH_FIX | score < 90 | REJECT | QualityGate |
| 2 | S3 ThreePhase L415 | PASS/PASS_WITH_FIX | score < 90 | REJECT | QualityGate |
| 3 | S4 InterviewRound L1207 | PASS/PASS_WITH_FIX | score < 90 | REJECT | QualityGate |
| 4 | S2/S3/S4 patch loop | PASS_WITH_FIX | patch 성공 + 재심사 PASS | **PASS** | 수정 완료 |
| 5 | S2/S3/S4 patch loop | PASS_WITH_FIX | patch 실패 / 재심사 REJECT | **REJECT** | 수정 불가 |
| 6 | S2/S3/S4 patch loop | PASS_WITH_FIX | fix_scope="partial/full" | **REJECT** | inplace 불가 → retry 위임 |
| 7 | S4 DirectorEnsemble L593 | (any) | 후보 길이 부족 → 스왑 | CONDITIONAL_PASS | V60.97 |
| 8 | S4 DirectorEnsemble L615 | (any) | CRITICAL≥1 / MAJOR≥2 | **REJECT** (score≤44) | V75-C 방화벽 |
| 9 | S4 DirectorEnsemble L635 | CONDITIONAL_PASS | 원래 Director REJECT | **REJECT** 유지 | Director 주권 |
| 10 | S4 InterviewRound L1281 | PASS/PASS_WITH_FIX | post-select 충돌 | **REJECT** | 연속성 검증 |
| 11 | S3 ThreePhase L564 | (fallback) | 재시도 소진 + score≥REWRITE | **PASS_WITH_WARNING** | 비상 통과 |
| 12 | ValidationOrch L405 | (any) | unjustifiable 모순 | **REJECT** (score=0) | 즉시 불합격 |
| 13 | ValidationOrch L589 | (any) | Retrospective CRITICAL | **REJECT** (score=0) | 장기 일관성 위반 |

---

## 4. ValidationOrchestrator 점수 산정

### 4.1 Tier 구조

| Tier | 모듈 | sync 라인 | async 라인 | 동작 |
|------|------|----------|-----------|------|
| **0.25** | PreLLMValidator | L317-329 | L1106-1115 | Python 사전검사 (0비용) |
| **0.5** | ContinuityValidator | L334-356 | L1117-1131 | 에피소드 간 연속성 → advisory |
| **1** | BlockingValidator | L361-395 | L1133-1163 | 필수 엔티티 검사 → advisory |
| **1.5** | ConsistencyValidator | L401-427 | L1240-1250 | 내부 모순 → unjustifiable이면 즉시 REJECT |
| **2** | ScoringValidator | L432-474 | L1180-1299 | LLM 채점 (0-100) |
| **2.5** | Catharsis + Action | L490-528 | L1260-1285 | 부가 품질 지표 |
| **3** | AdvisoryValidator | L479-483 | L1189-1190 | 비차단 제안 |
| **Phase3** | RetrospectiveValidator | L566-607 | 없음 | 장기 일관성 (4화+ 전용, sync 전용) |

### 4.2 점수 조정 항목

```
원점수 (LLM Scoring, 0-100)
  │
  ├─ Self-Consistency 투표 (70-85점 구간: 3회, 그 외: 1회)
  │
  ▼
조정 (7개 항목, 순차 적용)
  ├─ Catharsis:        -5 (critical) / -2 (warning) / 0
  ├─ Action:           -3 (score<5) / +2 (score≥8) / 0
  ├─ Consistency:      -N (justifiable 위반 감점)
  ├─ Pre-LLM:         -1 (감점 있을 때) / 0
  ├─ Continuity Adv:  -min(15, 위반수 × 5)
  ├─ Blocking Adv:    -min(20, 실패수 × 5)
  └─ Retrospective:   -10 (HIGH) / -5 (MEDIUM) / 0     ← sync 전용
  │
  ▼
최종 점수 = max(0, min(100, 조정 후 점수))
```

### 4.3 최종 판정

```python
_UNCONDITIONAL_PASS_FLOOR = 85

if score >= max(85, adaptive_threshold):
    → PASS
elif score >= adaptive_threshold:
    → CONDITIONAL_PASS
else:
    → REJECT
```

### 4.4 Adaptive Threshold 산정

```
base (장르별 68-73)
  + episode_type   (+7 volume_finale, +5 opening/arc_finale, +3 climax, -3 transition)
  + streak         (+5 연속실패≥3, +3 연속실패≥2, -3 연속합격≥10, -2 연속합격≥5)
  + pattern        (+4 품질하락, +3 고반복, +2 저다양성, -2 품질상승)
  + arc_position   (+3 arc 끝, +2 arc 시작, -1 arc 중간)
  ──────────────
  = final (floor 60 ~ ceiling 90)
```

**장르별 base 임계값**:

| 장르 | base | 장르 | base |
|------|------|------|------|
| 무협 | 70 | 요리 | 70 |
| 헌터 | 68 | 대체역사 | 72 |
| 투자 | 72 | 배우 | 70 |
| 작곡가 | 71 | 스포츠 | 69 |
| 판타지 | 69 | 의학 | 73 |

### 4.5 sync vs async 차이

| 항목 | sync | async |
|------|------|-------|
| PRE-LLM 실패 | Advisory | **즉시 REJECT** |
| Tier 실행 | 순차 전체 | Stage1 순차, Stage2 병렬 |
| Retrospective | ✅ 포함 | ❌ 미포함 |

---

## 5. PASS_WITH_FIX 상세

### 5.1 생산 조건

- Director LLM이 `DIRECTOR_AUDIT_SCHEMA` / `STRATEGIC_AUDIT_SCHEMA` 스키마로 응답
- `decision` enum: `["PASS", "PASS_WITH_FIX", "REJECT"]`
- `fix_scope` enum: `["inplace", "partial", "full"]`
- 프롬프트 가이드 (`director.yaml`): "총점 90점 이상이면서 모순·어색함이 남아 있는 경우"

### 5.2 소비 흐름

```
Director → PASS_WITH_FIX (score ≥ 90)
  │
  ├─ QualityGate: score < 90 → REJECT (패치 시도 안 함)
  │
  └─ score ≥ 90 → inplace patch loop 진입 (max 3회)
       │
       ├─ fix_scope = "inplace"
       │   ├─ LLM 1회 국소 수정 (temperature=0.3)
       │   ├─ Director 재심사 (동일 audit 메서드)
       │   ├─ PASS → verdict = PASS (확정)
       │   ├─ PASS_WITH_FIX → 다음 반복 (feedback 갱신)
       │   └─ REJECT → verdict = REJECT (탈출)
       │
       └─ fix_scope = "partial" / "full"
           └─ 즉시 break → verdict = REJECT
              → retry 경로에서 fix_scope 기반 3-tier 라우팅
```

### 5.3 3-tier 재시도 라우팅 (REJECT 후)

| 조건 | 전략 | 메서드 | 후보 수 |
|------|------|--------|--------|
| fix_scope="inplace" or (없음 + score≥60) | InPlace | `_inplace_patch_*()` | 1 |
| fix_scope="partial" or inplace 실패 | Partial | `patch_*_with_feedback(single_strategy=...)` | 선택 전략 기준 bounded regenerate 1후보 |
| fix_scope="full" or patch 실패 | Full | `generate()` / `regenerate_with_feedback()` | strategy budget에 따른 다전략 재생성 (보통 2~3후보) |

### 5.4 재심사 메서드

| Stage | 재심사 메서드 | 파일 |
|-------|-------------|------|
| S2 | `Director.audit_strategic_plan()` | `stage2_finalizer.py` L319 |
| S3 | `UnifiedBlueprintValidator.validate(all_candidates=None)` | `three_phase_blueprint_generator.py` L462 |
| S4 | `Director.audit_manuscript()` | `stage4_interview_round.py` L1331 |

---

## 6. DirectorEnsemble 전용 로직 (S4)

### 6.1 V60.97 길이 스왑

- **위치**: `director_ensemble.py` L572-593
- **조건**: LLM이 선택한 후보가 MIN_LENGTH(3,000자) 미만
- **동작**: 가장 긴 적격 후보로 자동 교체, verdict → CONDITIONAL_PASS, score = 50

### 6.2 V75-C 모순 방화벽

- **위치**: `director_ensemble.py` L608-617
- **조건**: CRITICAL ≥ 1건 또는 MAJOR ≥ 2건
- **동작**: verdict → REJECT 강제, score ≤ 44 (adaptive 승격 차단)

### 6.3 Adaptive Decision

- **위치**: `director_ensemble.py` L625-644, `director_grading.py` L549-569
- **동작**:
  - REJECT + score ≥ adaptive floor → CONDITIONAL_PASS (승격 시도)
  - PASS/PASS_WITH_FIX + score < adaptive floor → CONDITIONAL_PASS (강등 시도)
- **Director 주권 규칙** (L635-637):
  - Director 원래 REJECT → adaptive가 CONDITIONAL_PASS 해도 **REJECT 유지**

---

## 7. 경로별 판정 권한

| 검증 경로 | 즉시 REJECT 가능 | Advisory (감점) | 최종 판정자 |
|----------|-----------------|----------------|------------|
| Consistency (unjustifiable) | ✅ | — | Python |
| Retrospective (CRITICAL) | ✅ | HIGH/MEDIUM → 감점 | Python |
| CONTINUITY | ❌ (TF-36) | min(15, v×5) | Director |
| BLOCKING | ❌ (TF-36) | min(20, f×5) | Director |
| V75-C 방화벽 | ✅ (score≤44) | — | Python (S4 전용) |
| 점수 기반 판정 | — | — | ValidationOrchestrator |
| Director LLM 심사 | ✅ | — | Director (최종 권한) |

---

## 8. 대원칙 준수 현황

| 대원칙 | 구현 | 검증 |
|--------|------|------|
| **1. Python은 수집만, 판단은 LLM** | CONTINUITY/BLOCKING → advisory, 즉시 REJECT 없음 | ✅ sync/async 양쪽 |
| **3. Director 주권주의** | Director REJECT → adaptive 번복 불가 (L635) | ✅ |
| **PASS_WITH_FIX 과도 상태** | 전 Stage에서 반드시 PASS/REJECT로 전환 | ✅ |
| **QualityGate** | score<90이면 PASS_WITH_FIX 불허 | ✅ S2/S3/S4 |
| **fix_scope 보존** | REJECT 전환 시 다음 시도에 전파 | ✅ S2 L355, S3 L518, S4 L1370 |

---

## 9. 핵심 상수 참조

```python
# validation_orchestrator.py
_UNCONDITIONAL_PASS_FLOOR = 85

# constants.py
class PatchModeThresholds:
    REWRITE = 50    # < 50: 전면 재작성
    PATCH = 80      # 50-80: 패치 모드
    INPLACE = 60    # ≥ 60: inplace 가능

# validation.yaml
scoring.quality_gate_score: 90
scoring.default_pass_threshold: 70
adaptive_threshold.floor: 60
adaptive_threshold.floor_hit_reset: 3
adaptive_threshold.ambiguous_lower: 70
adaptive_threshold.ambiguous_upper: 85
adaptive_threshold.soft_margin: 2

# response_schemas.py
DIRECTOR_AUDIT_SCHEMA.decision: enum["PASS", "PASS_WITH_FIX", "REJECT"]
DIRECTOR_AUDIT_SCHEMA.fix_scope: enum["inplace", "partial", "full"]
STRATEGIC_AUDIT_SCHEMA.decision: enum["PASS", "PASS_WITH_FIX", "REJECT"]
STRATEGIC_AUDIT_SCHEMA.fix_scope: enum["inplace", "partial", "full"]
```

---

## 10. 스키마 정의

### DIRECTOR_AUDIT_SCHEMA (response_schemas.py L126-147)

```
decision:           PASS | PASS_WITH_FIX | REJECT        (required)
score:              0-100                                  (required)
reason:             string                                 (required)
fix_scope:          inplace | partial | full
fix_scope_reasoning: string
error_category:     QUALITY_ISSUE | LOGIC_ERROR
diagnostic_report:  string
current_beat_achieved: boolean
feedback:           string
```

### STRATEGIC_AUDIT_SCHEMA (response_schemas.py L150-169)

```
decision:           PASS | PASS_WITH_FIX | REJECT        (required)
score:              0-100                                  (required)
loop_detected:      boolean                                (required)
reason:             string                                 (required)
fix_scope:          inplace | partial | full
fix_scope_reasoning: string
re_slice_instruction: string
```
