# TF: DB 로깅 무결성 감사 보고서

> **날짜**: 2026-03-23
> **감사 범위**: `modules/core/db_manager.py`, `db_bootstrap_runtime.py`, Stage 2/3/4 전 파이프라인
> **목적**: DB에 저장되어야 할 런타임 데이터가 절삭(truncation)되거나 아예 미저장되는 전수 조사

---

## 1. 절삭(Truncation) — 총 23건

SQLite TEXT 컬럼은 길이 제한이 없다. 아래 절삭은 전부 Python 하드코딩이며 DB 제약이 아님.

### 1-A. 500자 절삭 (15건)

| # | 테이블 | 컬럼 | 위치 (db_manager.py) | 비고 |
|---|--------|------|---------------------|------|
| 1 | `director_selections` | `selection_reason` | L2177 | INSERT |
| 2 | `director_selections` | `verdict_reason` | L2181 | INSERT |
| 3 | `director_selections` | `firewall_reason` | L2184 | INSERT |
| 4 | `director_selections` | `selection_reason` | L2220 | UPDATE |
| 5 | `director_selections` | `verdict_reason` | L2221 | UPDATE |
| 6 | `episode_quality_labels` | `open_review` | L2246 | INSERT |
| 7 | `episode_quality_observations` | `note` | L2333 | UPSERT |
| 8 | `stage_attempts` | `reject_reason` | L2913 | INSERT |
| 9 | `stage_attempts` | `selection_reason` | L2924 | INSERT |
| 10 | `stage_attempts` | `verdict_reason` | L2925 | INSERT |
| 11 | `stage_attempts` | `open_review` | L2926 | INSERT |
| 12 | `stage_attempts` | `fix_scope_reasoning` | L2927 | INSERT |
| 13 | `stage_attempts` | `runtime_advisory` | L2928 | INSERT |
| 14 | `stage_attempts` | `retry_directives` | L2929 | INSERT |
| 15 | `ui_events` | `selection_value` | L3001 | INSERT |

### 1-B. 기타 절삭 (8건)

| # | 테이블 | 컬럼 | 한도 | 위치 | 비고 |
|---|--------|------|------|------|------|
| 16 | `episode_quality_labels` | `selection_reason` | **300자** | L2245 | 다른 테이블은 500인데 여기만 300 |
| 17 | `episode_quality_observations` | `operator_label` | **40자** | L2333 | 레이블이라 40이면 충분할 수 있음 |
| 18 | `llm_calls` | `prompt_snippet` | **3,000자** | L2812 | 실패 호출만 저장 |
| 19 | `llm_calls` | `thinking_snippet` | **5,000자** | L2815 | [TF-58] 성공도 저장, 그러나 Director thinking은 5K~30K |
| 20 | `llm_calls` | `error_msg` | **80자** | L2839 | 에러 메시지 80자는 심각하게 짧음 |
| 21 | `ui_events` | `message` | **4,000자** | L2999 | |
| 22 | `ui_events` | `prompt_id` | **200자** | L3002 | |
| 23 | `ui_events` | `artifact_path` | **1,000자** | L3003 | |

### 절삭 심각도 평가

| 등급 | 대상 | 이유 |
|------|------|------|
| **CRITICAL** | `thinking_snippet` 5,000자 | Director thinking은 통상 5K~30K자. 80%+ 손실 |
| **CRITICAL** | `error_msg` 80자 | Python traceback은 수백~수천 자. 디버깅 불가 |
| **HIGH** | `verdict_reason` 500자 | Director 판정 근거가 500자에 담기지 않는 경우 빈번 |
| **HIGH** | `fix_scope_reasoning` 500자 | 수정 범위 결정 논거가 잘림 |
| **MEDIUM** | `selection_reason` 300자 (quality_labels) | 다른 곳은 500인데 여기만 300 — 불일치 |
| **LOW** | `operator_label` 40자 | 레이블 용도이므로 적정 |
| **LOW** | `artifact_path` 1,000자 | Windows 경로 최대 260자이므로 충분 |

---

## 2. 미저장(Not Persisted) — 총 12개 카테고리

### 2-A. CRITICAL: Director Thinking 전량 미저장

| 항목 | 내용 |
|------|------|
| **데이터** | `_last_thinking` (LLM extended thinking 전문) |
| **생성 위치** | `director_ensemble.py` L1191, L1215, L1599, L1614, L1862, L1877 |
| **현재 흐름** | `getattr(self._d, "_last_thinking", "")` → `_operator_log()` → 콘솔 출력 → **버려짐** |
| **크기** | 1~30KB/결정 |
| **DB 컬럼** | `director_selections`에 `director_thinking` 컬럼 자체가 없음 |
| **손실률** | **100%** |
| **영향** | 콘솔 로그에서만 볼 수 있고, 회고 분석·품질 추적 불가 |

Stage 2에서는 `director_auditor.py` L1152/1161/1316/1359에서 `_director_thinking` 키를 결과 dict에 넣고, `stage2_finalizer.py` L1830-1833에서 UI 출력하지만 **DB 저장 코드 없음**.

### 2-B. CRITICAL: Advisory Chain 상세 결과 미저장

Stage 4 `stage4_interview_round.py` L4406-4950에서 9개 advisory를 병렬 실행:

| Advisory | 생성 데이터 | DB 저장 | 손실 |
|----------|------------|---------|------|
| TruthGate | structured_warnings (증거+심각도) | 상위 10건 문자열만 Director에 전달 | ~80% |
| NpcDrift | drift 분석 {npc, field, expected, found} | 상위 8건 문자열만 | ~70% |
| NumericDrift | {key, issue} 전수 | 상위 6건만 | ~60% |
| Flashback | 경고 객체 리스트 | 상위 5건만 | ~50% |
| InfoParadox | 모순 증거 리스트 | 상위 5건만 | ~50% |
| RelDrift | 관계 변동 리스트 | 상위 5건만 | ~50% |
| LongTermRep | 장기 반복 패턴 | 상위 5건만 | ~50% |
| NumericConsistency | 수치 불일치 전수 | 상위 위반만 | ~60% |
| StyleSignal | 문체 이탈 분석 | 요약만 | ~70% |

**현재**: 문자열 요약이 Director의 mandatory_context에 전달되고, `advisory_warnings` JSON blob에 플래그 카운트만 저장.
**미저장**: 개별 advisory의 structured_warnings 원본, 증거 텍스트, 심각도 분류.
**에피소드당 손실**: ~50-100KB

### 2-C. HIGH: Ensemble 비교 분석 미저장

| Stage | 생성 위치 | 데이터 | DB 저장 |
|-------|----------|--------|---------|
| Stage 4 | `director_ensemble.py` L1180-1265 | 후보 간 비교 분석, 개별 score_breakdown | `selection_reason[:500]`만 |
| Stage 3 | `director_ensemble.py` L1350-1650 | Blueprint 후보 비교 | 동일 |
| Stage 2 | `director_ensemble.py` L1750-1900 | Arc 후보 비교 | 동일 |

**손실**: 후보별 점수 분해(characterization, pacing, consistency 등), 왜 A가 B보다 나은지 전문 → 500자 요약으로 압축.

### 2-D. HIGH: error_category 파라미터 누락

| 항목 | 내용 |
|------|------|
| **생성** | `stage4_interview_round.py` L4033 — `_record_s4_attempt(error_category=...)` 호출 |
| **문제** | `save_stage_attempt()` 시그니처에 `error_category` 파라미터 없음 |
| **결과** | 값이 전달되지만 **조용히 무시됨** — 실패 분류 불가 |

### 2-E. HIGH: Pre-LLM Validator 상세 결과

| 항목 | 내용 |
|------|------|
| **생성** | `pre_llm_validator.py` — 10개 Python 검증 (단어반복, 문장길이, 대화비율, 감각묘사, 물리, 시간, 문장끝, NPC명, 구조반복, POV) |
| **현재** | Director advisory로만 전달, DB 테이블 없음 |
| **손실률** | 100% |

### 2-F. HIGH: Arc Draft Validator 상세 결과

| 항목 | 내용 |
|------|------|
| **생성** | `arc_draft_validator.py` L86-195 — critical_issues, advisory_issues, warnings, suggestions |
| **현재** | Director advisory로만 전달 |
| **손실률** | 100% |
| **크기** | 2-5KB/Arc |

### 2-G. HIGH: initial_verdict vs final_verdict 차이

| 항목 | 내용 |
|------|------|
| **생성** | `stage4_interview_round.py` L5253-5256 |
| **현재** | DB에는 `verdict`(최종)만 저장. Firewall이 PASS→REJECT로 바꾼 경우 원래 verdict 소실 |
| **영향** | "Firewall이 몇 번 개입했는가?" 쿼리 불가 |

### 2-H. MEDIUM: Patch 컨텍스트 개별 컬럼 없음

| 필드 | 생성 | DB 저장 |
|------|------|---------|
| `is_patch` | L4010 | `advisory_flags` JSON 내부 (쿼리 어려움) |
| `is_patch_fallback` | L4011 | 동일 |
| `patch_strategy` | L4023 | 동일 |
| `prev_score` | L4012 | 동일 |
| `structural_attempted` | L4022 | 동일 |

→ "패치 성공률", "풀백 비율" 등 집계 쿼리가 JSON decode 없이 불가.

### 2-I. MEDIUM: Action Items 미저장

| 항목 | 내용 |
|------|------|
| **생성** | `stage4_interview_round.py` L5032-5034 — Director가 발행하는 수정 지시 목록 |
| **현재** | UI 로그 + `_RoundOutcomeTracePayload`에만 존재 |
| **영향** | "Director 피드백을 실제로 반영했는가?" 추적 불가 |

### 2-J. MEDIUM: Score Breakdown per Attempt

| 항목 | 내용 |
|------|------|
| **생성** | `stage4_interview_round.py` L3955 — `{characterization, pacing, consistency, ...}` |
| **현재** | `episode_quality_labels` 테이블에만 저장 (최종 에피소드 단위) |
| **미저장** | `stage_attempts`에는 총점(`score`)만 있고 breakdown 없음 |
| **영향** | "어느 차원에서 가장 많이 실패하는가?" 시도별 분석 불가 |

### 2-K. MEDIUM: Constitutional Checker 결과

| 항목 | 내용 |
|------|------|
| **생성** | `constitutional_checker.py` — 원칙별 위반 여부, 증거, 심각도 |
| **현재** | Director advisory로만 전달 |
| **손실률** | 100% |

### 2-L. LOW-MEDIUM: Quality Dashboard → JSONL 전용

| 항목 | 내용 |
|------|------|
| **생성** | `quality_dashboard.py` L127-239 |
| **현재** | JSONL 파일에만 기록, DB 테이블 없음 |
| **영향** | 구조화된 쿼리 불가 (파일 파싱 필요) |

---

## 3. 미저장 영향 요약

| 카테고리 | 에피소드당 손실 | 손실률 | 심각도 |
|----------|----------------|--------|--------|
| Director Thinking | 1~30 KB | 100% | CRITICAL |
| Advisory Chain 상세 | 50~100 KB | 80-90% | CRITICAL |
| Ensemble 비교 전문 | 3~10 KB | ~80% | HIGH |
| error_category 누락 | 수십 바이트 | 100% | HIGH (파라미터 버그) |
| Pre-LLM Validator | 0.5~2 KB | 100% | HIGH |
| Arc Draft Validator | 2~5 KB | 100% | HIGH |
| initial vs final verdict | 수십 바이트 | 100% | HIGH |
| Patch 컨텍스트 | 0.5~1 KB | JSON 매몰 | MEDIUM |
| Action Items | 0.5~2 KB | 100% | MEDIUM |
| Score Breakdown/attempt | 0.5~1 KB | 시도별 100% | MEDIUM |
| Constitutional Checker | 1~3 KB | 100% | MEDIUM |
| Quality Dashboard | 가변 | DB 0% | LOW-MEDIUM |

**100 에피소드 기준 추정**:
- 생성되는 분석 데이터: ~10-15 MB
- 실제 DB 저장: ~1-2 MB
- **총 손실: ~85-90%**

---

## 4. 절삭 전수 목록 (db_manager.py 기준)

```
L2177  director_selections.selection_reason    [:500]
L2181  director_selections.verdict_reason      [:500]
L2184  director_selections.firewall_reason     [:500]
L2220  director_selections.selection_reason    [:500]  (UPDATE)
L2221  director_selections.verdict_reason      [:500]  (UPDATE)
L2245  episode_quality_labels.selection_reason [:300]  ← 불일치
L2246  episode_quality_labels.open_review      [:500]
L2333  episode_quality_observations.operator_label [:40]
L2333  episode_quality_observations.note       [:500]
L2812  llm_calls.prompt_snippet               [:3000] (실패만)
L2815  llm_calls.thinking_snippet             [:5000]
L2839  llm_calls.error_msg                    [:80]   ← 심각
L2913  stage_attempts.reject_reason           [:500]
L2924  stage_attempts.selection_reason        [:500]
L2925  stage_attempts.verdict_reason          [:500]
L2926  stage_attempts.open_review             [:500]
L2927  stage_attempts.fix_scope_reasoning     [:500]
L2928  stage_attempts.runtime_advisory        [:500]
L2929  stage_attempts.retry_directives        [:500]
L2999  ui_events.message                      [:4000]
L3001  ui_events.selection_value              [:500]
L3002  ui_events.prompt_id                    [:200]
L3003  ui_events.artifact_path                [:1000]
```

---

## 5. 버그: 파라미터 전달 누락

`stage4_interview_round.py` L4033에서 `_record_s4_attempt(error_category=error_category)`를 호출하지만, `db_manager.py`의 `save_stage_attempt()` 시그니처에 `error_category` 인자가 **없다**. Python kwargs이므로 에러 없이 조용히 무시됨. 실패 분류 데이터가 완전히 소실되는 **사일런트 버그**.

---

*Generated by Opus TF Audit — 읽기 전용 감사, 코드 수정 없음*
