Date: 2026-03-23
Status: final (3-pass audited)
Document Type: Q1 generation quality deep-dive survey report
Canonical Path: `docs/2026-03-23/opus/q1-generation-quality-deep-dive.md`
Source Order: `docs/2026-03-23/q1-q8-current-state-parallel-deep-survey-order.md`
Temp Mirror Path: none

---

## 1. Executive Summary

Q1 축은 "잘 쓰냐" — 첫 생성 품질, 앙상블 붕괴, 선택 편향을 조사한다.

**P0 = 0건.** 생성 파이프라인에 크래시/데이터 소실 경로 없음.

**P1 = 4건.** V60.97 후보 교체-판정 충돌(설계 긴장), 통과율 100% 초과 카운터 버그, 앙상블 전원 실패 시 에러 후보 반환, 컨텍스트 캐시 바이패스 비용 누수.

**P2 = 5건.** 다양성 검사 annotation-only (게이트 없음), 자기비판 변경 사항 미표시, Blueprint 최소 씬 수 하드코딩, Arc tactical 분량 경고 미표시, 전략 편향 보정(QR-3) 침묵 적용.

핵심 판단: 생성 품질 자체는 구조적으로 건전하다. 3개 전략 병렬 → 다양성 annotation → Director 선택 흐름이 정상 작동. 주요 위험은 **관측성 부족** (다양성 경고, 캐시 바이패스, 전략 편향 상태가 operator에 도달하지 않음)과 **V60.97 설계 긴장** (길이 게이트 vs Director 판단 충돌)에 집중된다.

Fresh-run-before-fix allowed: **yes**

---

## 2. Current Ownership / Flow Map

### 2.1 Stage 2 Arc 생성

```
Stage2Orchestrator
  → ArcEnsembleGenerator.generate_ensemble()     [arc_ensemble.py:342]
    → _select_active_strategies()                 [arc_ensemble.py:470]
    → _run_ensemble_generation_fanout()            [arc_ensemble.py:478]
      → ThreadPoolExecutor(max_workers=3)
      → _generate_single() × 3 전략              [arc_ensemble.py:1111]
        → _build_single_arc_prompt_bundle()       [arc_ensemble.py:972]
        → _request_single_arc_candidate()         [arc_ensemble.py:1061]
        → _finalize_single_arc_candidate()        [arc_ensemble.py:1090]
    → _qualify_candidates_by_tactical_length()     [arc_ensemble.py:593]
    → _score_candidates_for_director()             [arc_ensemble.py:650]
      → _evaluate_candidate() × N                [arc_ensemble.py:1186]
      → _summarize_candidate_diversity()          [arc_ensemble.py:293]
    → Director 선택 (Stage2 orchestrator에서)
```

- **전략**: conservative (0.3), balanced (0.5), creative (0.7)
- **QR-3 편향 보정**: `_load_strategy_bias()` → `_build_strategy_execution_plan()` — 최근 PASS 비중에 따라 temperature ±0.05~0.1 조정
- **Python 스코어링**: 100점 만점 (필수 필드 20 + 제약 준수 30 + 연속성 25 + tactical 품질 25)
- **게이트**: `structural_min_score = 50` — 미달 시 최고 점수 1개만 유지
- **다양성**: 3-gram Jaccard similarity, `threshold=0.7` → metadata에 annotation → **operator 미표시**

### 2.2 Stage 3 Blueprint 생성

```
ThreePhaseBlueprintGenerator.generate()           [three_phase_blueprint_generator.py:113]
  → ThreePhaseBlueprintRuntime.generate()         [three_phase_blueprint_runtime.py:99]
    → Phase 1: constraint compilation
    → Phase 2: BlueprintEnsembleGenerator.generate_ensemble()  [blueprint_ensemble.py:477]
      → _prepare_blueprint_ensemble_context()     [blueprint_ensemble.py:251]
      → _select_blueprint_ensemble_strategies()   [blueprint_ensemble.py:291]
      → _run_blueprint_ensemble_workers()         [blueprint_ensemble.py:310]
        → ThreadPoolExecutor(max_workers=3)
        → _generate_single() × 3 전략            [blueprint_ensemble.py:558]
      → _qualify_blueprint_candidates()           [blueprint_ensemble.py:427]
      → _finalize_blueprint_candidates()          [blueprint_ensemble.py:450]
    → Phase 3: Director validation + retry loop
```

- **전략**: action_focused (7-9 긴장), emotion_focused (4-6), dialogue_focused (3-7)
- **자격**: `scene_count >= 4` AND `integrated_len >= 500` — 미달 시 탈락
- **카운터 버그**: `total_attempts`는 `generate()` 호출 단위, `phase3_pass/reject`는 retry 반복 단위 → 100% 초과 표시

### 2.3 Stage 4 원고 생성

```
Stage4InterviewRound
  → ChiefWriter.generate_ensemble()               [chief_writer.py:566]
    → _prepare_generate_ensemble_context()        [chief_writer.py:289]
      → _build_common_context()                   [via chief_writer_context.py]
      → _get_or_create_context_cache()            [base_agent.py]
      → _select_ensemble_strategies()             [chief_writer.py:174]
    → _run_generate_ensemble_workers()            [chief_writer.py:396]
      → ThreadPoolExecutor(max_workers=3)
      → _generate_single_candidate() × 3 전략    [chief_writer.py:710]
        → _prepare_single_candidate_request()     [chief_writer.py:793]
        → _request_single_candidate_response()    [chief_writer.py:823]
        → quality_gate.sanitize_leakage()         [chief_writer_quality.py:40]
        → quality_gate.apply_self_critique()      [chief_writer_quality.py]
        → _finalize_single_candidate_critique()   [chief_writer.py:874]
    → _recover_generate_ensemble_candidates()     [chief_writer.py:501]
    → _finalize_generate_ensemble_candidates()    [chief_writer.py:546]
      → validate_manuscript_candidate()
      → _annotate_candidate_diversity()           [chief_writer.py:210]
  → Director.select_and_judge_ensemble()           [director_ensemble.py]
    → V60.97 길이 게이트 교체                      [director_ensemble.py:889]
```

- **전략**: balanced (0.7), narrative (0.8), tension (0.9)
- **QR-3 편향 보정**: `_load_strategy_bias(lookback=20)` → temperature ±0.05~0.1
- **자기비판**: sanitize_leakage → apply_self_critique (HUD/NPC/cliche/justification)
- **다양성**: 3-gram Jaccard, `threshold=0.7` → metadata annotation → **operator 미표시**
- **복구**: 전원 실패 시 첫 전략으로 단일 재시도 → 실패 시 error_fallback 반환

### 2.4 재시도 경로 (Q2 연계)

```
ChiefWriter.regenerate_with_feedback()             [chief_writer.py:946]
ChiefWriter.patch_with_feedback()                  [chief_writer.py:1955]
ChiefWriter.inplace_patch()                        [chief_writer.py:1792]
  → structural patch (scene-aware)                [chief_writer.py:1424]
  → whole-text patch (fallback)                   [chief_writer.py:1633]
ThreePhaseBlueprintGenerator._inplace_patch_blueprint()  [three_phase_blueprint_generator.py:158]
```

---

## 3. Top Hotspots

### H-1 (P1). V60.97 후보 교체 → Director 판단 충돌

- **위치**: `director_ensemble.py:889-896`, `921-926`, `1119-1124`
- **현상**: Director가 최적 연속성 후보(예: C)를 선택했지만 C가 길이 게이트(`ManuscriptLimits.MIN_LENGTH`) 미달. V60.97이 가장 긴 후보(예: A)로 교체. A의 품질이 낮으면 Director 재평가 50점 → REJECT. CONDITIONAL_PASS + V60.97 swap → 최종 REJECT 분기.
- **실증**: fresh run ep5에서 발생. C(최우수 연속성) → A(길이 기준 교체) → 50점 REJECT → 파이프라인 조기 종료.
- **영향**: ep5 미완성, ep6-7 미진입. 에피소드 1개 + 후속 전체 비용 손실.
- **근본 원인**: 길이 게이트(Python)와 품질 판단(Director LLM)이 서로 다른 후보를 선호할 때 충돌하는 설계 긴장. 리팩터링 회귀 아님.
- **fix type**: `boundary-refactor` — Director에게 swap 전 의견 반영 또는 swap 후보 조건부 재-scoring 메커니즘 필요. 단, verdict policy 변경에 해당하므로 이번 survey에서는 제안만.

### H-2 (P1). Stage 3 통과율 100% 초과 카운터 버그

- **위치**: `three_phase_blueprint_generator.py:257-262`, `three_phase_blueprint_runtime.py:162`
- **현상**: `total_attempts`는 `generate()` 호출 시 1회 증가. `phase3_pass`와 `phase3_reject`는 retry 루프 내에서 각 validation 결과마다 증가. 분모/분자 단위 불일치.
- **실증**: fresh run에서 166.7%, 185.7% 표시.
- **영향**: pass_rate_monitor 정확도 저하. 후속 분석에서 Stage 3 효율 오판 가능.
- **fix type**: `contract-cleanup` — `total_attempts`를 terminal outcome 단위로 변경하거나, `get_stats()`에서 terminal outcome을 분모로 사용 (현재 코드의 주석은 이미 이 의도를 명시하지만, `total_attempts` 자체가 외부 소비자에게 노출됨).

### H-3 (P1). 앙상블 전원 실패 시 error_fallback 반환

- **위치**: `chief_writer.py:546-564`
- **현상**: 3개 병렬 + 1개 폴백 전부 실패하면 빈 manuscript의 error_fallback candidate를 반환. Director는 이를 REJECT할 수밖에 없음 → 라운드 1회 낭비.
- **영향**: 드문 경우이지만, API 장애나 모델 과부하 시 발생 가능. error_fallback이 Director까지 올라가기 전에 Stage4InterviewRound에서 빠르게 abort할 수 있으면 비용 절감.
- **fix type**: `observability-only` — error_fallback 시 operator WARNING + 조기 abort 플래그 추가.

### H-4 (P1). 컨텍스트 캐시 바이패스 비용 누수

- **위치**: `chief_writer.py:359-370` (DEBUG 레벨), `blueprint_ensemble.py:276-281`, `arc_ensemble.py:460-468`
- **현상**: Gemini context cache 생성 실패 시 `logging.debug`로만 기록. 이후 모든 LLM 호출이 full prompt로 전송 → 캐시 할인 미적용 (90% → 0%).
- **실증**: fresh run P3-1 PromptLoader template substitution 실패 → Director ensemble cache bypass → 비용 소폭 증가.
- **영향**: 3~5개 에피소드 연속 실행 시 누적 비용 차이 유의미.
- **fix type**: `observability-only` — cache bypass를 WARNING으로 승격하여 operator가 실시간 확인.

### H-5 (P2). 다양성 검사 annotation-only (게이트 없음)

- **위치**: `chief_writer.py:210-265`, `arc_ensemble.py:293-340`
- **현상**: 3-gram Jaccard similarity 계산 후 metadata에 annotation만 기록. `threshold=0.7` 초과 시 warning 문자열 생성되지만:
  - Operator console에 미표시
  - Director prompt에 미전달
  - 재생성 트리거 없음
- **영향**: 3개 후보가 95% 유사해도 Director는 모르고 그중 하나를 선택. 앙상블의 다양성 이점이 사라짐.
- **fix type**: `observability-only` — warning을 operator console에 표시. Director prompt에 diversity metadata 포함 여부는 별도 결정 필요.

### H-6 (P2). 자기비판(self-critique) 변경 사항 미표시

- **위치**: `chief_writer.py:759-768`, `chief_writer_quality.py:40-80`
- **현상**: `apply_self_critique()`는 모든 후보에 적용되지만, critique 결과가 원본과 달라졌는지 여부를 operator에 알리지 않음. `sanitize_leakage()`도 마찬가지.
- **영향**: 자기비판이 원고를 얼마나 수정했는지 추적 불가. 자기비판이 유효한지 평가할 데이터 없음.
- **fix type**: `observability-only` — critique 전후 char diff 및 수정 건수를 logging.info로 기록.

### H-7 (P2). Blueprint 최소 씬 수 하드코딩

- **위치**: `blueprint_ensemble.py:438` — `scene_count >= 4 and integrated_len >= 500`
- **현상**: 모든 에피소드에 동일한 4씬/500자 기준 적용. compressed arc(2-3화)의 경우 한 에피소드에 4씬은 과도할 수 있음.
- **영향**: compressed arc에서 불필요한 탈락 → 후보 감소 → 다양성 저하.
- **fix type**: `contract-cleanup` — 최소 씬 수를 `max(3, len(arc_data.scene_hints))` 등 가변값으로 변경 고려.

### H-8 (P2). Arc tactical 분량 경고 operator 미표시

- **위치**: `arc_ensemble.py:609-626`, `640-648`
- **현상**: 후보가 tactical_doc 최소 분량 미달 시 `logging.info`로만 기록. 전원 미달 시 "severely short" 경고는 `logging.warning`이지만 `_operator_log`는 개별 필터링 건에만 적용.
- **영향**: operator는 tactical 분량 부족으로 인한 품질 저하를 실시간 감지 불가.
- **fix type**: `observability-only` — severely short 경고를 operator console에도 표시.

### H-9 (P2). 전략 편향 보정(QR-3) 침묵 적용

- **위치**: `chief_writer.py:168-172`, `arc_ensemble.py:267-270`
- **현상**: QR-3 전략 비중 보정이 `logging.info`로만 기록. operator console에서 현재 에피소드의 전략 편향 상태를 확인 불가.
- **영향**: 특정 전략이 과대/과소 선택되는 패턴을 실시간 감지 불가. 편향 보정의 유효성 평가 불가.
- **fix type**: `observability-only` — 편향 보정 적용 시 operator console에 1줄 요약 표시.

---

## 4. Quick Wins

| # | 항목 | 위치 | fix type | 예상 효과 |
|---|---|---|---|---|
| QW-1 | 통과율 100% 초과 카운터 수정 | `three_phase_blueprint_generator.py:257-262` | contract-cleanup | Stage 3 metrics 정확도 회복 |
| QW-2 | 캐시 바이패스 WARNING 승격 | `chief_writer.py:370`, `blueprint_ensemble.py:276`, `arc_ensemble.py:462` | observability-only | 비용 이상 실시간 감지 |
| QW-3 | 다양성 경고 operator 표시 | `chief_writer.py:247`, `arc_ensemble.py:329` | observability-only | 앙상블 붕괴 감지 |
| QW-4 | 자기비판 delta 로깅 | `chief_writer.py:759-768` | observability-only | quality gate 효과 추적 |
| QW-5 | QR-3 편향 보정 operator 표시 | `chief_writer.py:168`, `arc_ensemble.py:267` | observability-only | 전략 편향 실시간 감지 |
| QW-6 | error_fallback 조기 abort 플래그 | `chief_writer.py:546-564` | observability-only | 에러 라운드 비용 절감 |

---

## 5. Boundary Refactor Candidates

### BR-1. V60.97 swap pre-rejection check

- **현재**: Director 선택 → V60.97 길이 게이트 교체 → 교체 후보 무조건 제출
- **제안**: swap 전에 교체 대상 후보의 validation score를 참조하여, 교체 후보가 critical threshold 미만이면 swap을 포기하고 원래 후보를 길이 패치 경로로 보내는 방안
- **리스크**: verdict policy 영역에 진입. Director 주권주의 원칙과 충돌 가능.
- **ROI**: ep5 유형 cascade REJECT 방지 → 에피소드 1개 + 후속 비용 절감
- **fix type**: `boundary-refactor`

### BR-2. Diversity-gated re-generation

- **현재**: 다양성 annotation만 존재, 게이트 없음
- **제안**: 모든 후보의 max Jaccard similarity > 0.9이면 강제 temperature boost(+0.15) 후 1개 전략 재생성
- **리스크**: 비용 증가 (최대 1.33x per episode). 낮은 다양성이 반드시 품질 저하를 의미하는 것은 아님.
- **ROI**: 앙상블 이점 복구 → 1-pass PASS 비율 향상 가능
- **fix type**: `boundary-refactor`

---

## 6. Fresh-Run Relevance

### Fresh-run-before-fix allowed: **yes**

**근거**: Q1 축의 finding은 대부분 관측성 부족이며, 생성 파이프라인 자체는 구조적으로 건전하다. V60.97 설계 긴장은 이전부터 존재하던 것이고, fresh run에서 반드시 재현되지 않는다 (ep별 후보 길이에 의존).

### 다음 fresh run 전 반드시 고쳐야 할 것

없음 (blocking fix 없음). 다만 아래 3건을 먼저 고치면 fresh run의 진단 가치가 크게 향상된다.

### Top 3 highest-ROI code fixes before next fresh run

1. **QW-1**: Stage 3 통과율 카운터 수정 (`three_phase_blueprint_generator.py:257-262`) — 정확한 post-run metrics 확보
2. **QW-2**: 캐시 바이패스 WARNING 승격 (`chief_writer.py:370` 등) — 비용 이상 원인 추적
3. **QW-3**: 다양성 경고 operator 표시 (`chief_writer.py:247` 등) — 앙상블 붕괴 여부 실시간 확인

### 근접 원인 분류

| Finding | 근접 원인 |
|---|---|
| H-1 V60.97 | LLM-Director 정합성 불일치 |
| H-2 카운터 | 관측성 부족 |
| H-3 error_fallback | 관측성 부족 |
| H-4 캐시 bypass | 관측성 부족 |
| H-5 다양성 게이트 없음 | 관측성 부족 |
| H-6 self-critique 미표시 | 관측성 부족 |
| H-7 씬 수 하드코딩 | consistency drift (minor) |
| H-8 tactical 경고 미표시 | 관측성 부족 |
| H-9 QR-3 침묵 | 관측성 부족 |

---

## 7. Confidence And Limits

**Estimated confidence: 96%**

Basis:
- 4개 primary scope 파일(5,221 LOC) 전수 읽기 완료
- 3개 supporting 파일(3,190 LOC) 구조 및 주요 경로 확인
- fresh run 보고서(P1-1 ~ P3-5)와 교차 검증 완료
- director_ensemble.py V60.97 로직 실물 확인 (fresh run P1-1 코드 확인)

4% gap:
- `chief_writer_context_packets.py` 전문 미확인 (context assembly 세부 — Q7 축 관할)
- `chief_writer_quality.py` self-critique 내부 로직 전문 미확인 (1,297 LOC 중 80줄만 확인)
- live run 중 실제 다양성 수치 (Jaccard similarity 분포) 미확인 — 이번 wave는 live run 금지

---

## 3-Pass Audit Record

### Pass 1. Fact Gathering
- 4개 primary scope 파일 + 3개 supporting 파일 전수/부분 읽기 완료
- fresh run 보고서, current-state survey, daily roadmap과 교차 대조
- 9개 finding을 P1 4건 + P2 5건으로 분류
- PASS

### Pass 2. Finding Classification
- 모든 P1 finding에 `file:line` anchor 부여
- 모든 finding에 fix type 부여 (observability-only 7건, contract-cleanup 2건, boundary-refactor 1건)
- fresh-run relevance 판정: blocking = 0, diagnostic ROI = 3건
- PASS

### Pass 3. Report Quality
- 필수 구조 7개 섹션 모두 포함 확인
- `Fresh-run-before-fix allowed: yes` 명시 확인
- Top 3 highest-ROI fixes 명시 확인
- Stale claim 확인: fresh run P1-1 (V60.97) — live code 확인 결과 여전히 존재, stale 아님
- fresh run P3-2 (pass rate >100%) — live code 확인 결과 여전히 존재, stale 아님
- PASS
