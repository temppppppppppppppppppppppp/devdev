# TF-S4-LOG: Stage 4 로깅 체계 전수조사 및 보강 방안

> 상태: **CONFIRMED** (11-Pass 감리 완료 2026-03-13)
> 작성일: 2026-03-13
> 범위: Stage 4 전체 (orchestrator, interview_round, post_processor, director_ensemble, advisory chain)
> 제약: **코드 수정 절대 금지** (보강 방안 제안만)
> 감리 기준: 95% 확신도 — 오탐 7건 제거, Director 판정 데이터 생명주기 추가 감리 3-Pass, 사실 검증 3-Pass (5건 수정)

---

## 0. Executive Summary

### 현행 로깅 아키텍처 (4-Tier)

```
Tier 1: logging 모듈 → session_<timestamp>.log (텍스트, DEBUG~ERROR)
Tier 2: self.ctx.ui.log() → 콘솔 + UI (휘발성, 비영속)
Tier 3: episode_production.jsonl (구조화, JSON Lines, per-attempt)
Tier 4: pass_rate_monitor.json + soft_failures.json + metrics_*.json (집계)
```

### 현황 수치

| 파일 | logging 호출 | print() 호출 | ui.log() 호출 |
|------|:---:|:---:|:---:|
| stage4_interview_round.py | 100 (debug:36, info:20, warning:43, error:1) | 20 | 다수 |
| director_ensemble.py | ~15 | **29** | 다수 |
| stage4_orchestrator.py | ~20 | 3 | 다수 |
| stage4_post_processor.py | ~40 | 0 | 다수 |

### 발견 요약

| 카테고리 | 건수 | HIGH | MEDIUM | LOW |
|----------|:---:|:---:|:---:|:---:|
| A. print() 비영속 (Director 판정 프레임) | 3개 영역 | 2 | 1 | 0 |
| B. 상관 ID 부재 | 3 | 2 | 1 | 0 |
| C. Advisory 심각도 미표기 | 2 | 0 | 2 | 0 |
| D. 로깅 레벨 부적합 | 4 | 0 | 3 | 1 |
| E. 로그 싱크 분산 | 1 | 1 | 0 | 0 |
| F. 비용 추적 단절 | 2 | 1 | 1 | 0 |
| G. Director 판정 데이터 소실 | 5 | 3 | 2 | 0 |
| H. 앙상블 후보 비보존 | 1 | 0 | 1 | 0 |
| I. PASS_WITH_FIX 반복 이력 분산 + 수정 전략 상세 누락 | 1 | 0 | 1 | 0 |
| **합계** | **22** | **9** | **12** | **1** |

**핵심 판정:** 기능적 로깅은 충분. 운영·사후 감사(post-mortem) 관점에서 5가지 구조적 gap 존재: (A) Director 판정 프레임 비영속, (B) 상관 ID 부재, (E) 6개 싱크 분산, (G) Director 판정 데이터 12개 카테고리 소실, (I) PASS_WITH_FIX 반복 이력 분산 + 수정 전략 상세 누락.

---

## 1. 현행 로깅 양호 항목

감리 과정에서 확인된 설계의도 준수 및 양호 패턴:

| 항목 | 근거 |
|------|------|
| **출력 절단 복구** | `base_agent.py:1192` finish_reason 감지 + 이어쓰기 + Circuit Breaker |
| **fail-open preflight** | `_preflight_validate_blueprint()` 전체가 fail-open 설계 (A-3 백업). 7개 except pass 전부 의도적. |
| **telemetry setattr** | `_set_agent_telemetry_context()` — 실패해도 파이프라인 무영향. silent pass 의도적. |
| **post_processor 비차단** | 대부분의 except 블록이 `logging.warning()` + ui.log() 포함. 진정한 silent pass 4건뿐 (HUD snapshot, feature flag, state record ×2). |
| **episode_production.jsonl** | 구조화된 per-attempt 기록. verdict, score, error_category 포함. |
| **PerfTimer 계측** | generate/director 호출에 timing 측정 존재 |
| **soft_failure 리포팅** | 별도 싱크로 품질 저하 추적 |
| **rejected_best 아티팩트** | `snapshot_logged_artifact(artifact_kind="rejected_best")` — REJECT 시 최선 원고 디스크 보존 |
| **fix_scope_reasoning 순환 전달** | Director → prev_attempt dict → Chief Writer 피드백 (다음 반복에 사용됨) |

### 오탐 제거 내역 (7건)

| 원래 ID | 원래 등급 | 내용 | 제거 사유 |
|---|---|---|---|
| L-S4-001~006 | HIGH | stage4_orch L258~360 silent swallows | 텔레메트리 setattr(2건) + preflight fail-open(4건). 전부 의도적 설계. |
| L-S4-044 | HIGH | post_processor L340 DB 저장 silent | 실제로는 `ui.log("🚨 DB 저장 실패")` + `return False`. silent 아님. |

---

## 2. 발견된 Gap 상세

### A. Director 판정 프레임 비영속 — **HIGH**

**현상:** Director의 최종 판정(verdict, score, feedback, fix_scope)이 `print()`로만 출력. `session_*.log` 파일에 기록되지 않음.

| 위치 | print() 수 | 내용 |
|------|:---:|------|
| `director_ensemble.py:1212-1237` | 11 | Stage4 Director 판정 프레임 (verdict, score, contradictions, fix_scope) |
| `director_ensemble.py:315-332, 655-671` | 18 (9+9) | Stage2/3 Director 판정 프레임 |
| `stage4_interview_round.py:1242-1251, 1546-1554` | 15 | 면담 시작/종료 + verdict 결과 |

**영향:**
- 운영자가 사후에 "왜 이 원고가 PASS/REJECT되었는지" 추적 불가
- `session_*.log`에 판정 사유 없음 → post-mortem 시 재실행 필요
- `episode_production.jsonl`에 verdict/score는 있으나 **Director의 구체적 판정 사유(contradictions, fix_scope_reasoning)**는 누락

**보강 방안:**
```python
# 현재
print(f"   📋 판정: {verdict} ({score}점)")

# 개선: logging.info + print 병행
logging.info("[Director:S4] ep=%d verdict=%s score=%d fix_scope=%s reason=%s",
             ep_num, verdict, score, fix_scope, reason[:200])
print(f"   📋 판정: {verdict} ({score}점)")
```

**예상 작업량:** ~15줄 수정 (print 옆에 logging.info 추가)

---

### B. 상관 ID 부재 — **HIGH**

**현상:** `logging_keys.py`에 `attempt_key` 생성 함수가 정의되어 있으나, `logging.info/warning/error` 100건에서 **단 한 곳도 사용하지 않음**. `attempt_key`는 `episode_production.jsonl` 기록에만 사용.

**결과:** 6개 로그 싱크 간 교차 참조 불가.

| 로그 싱크 | 상관 ID | 상태 |
|----------|---------|------|
| session_*.log | 없음 | ❌ 에피소드 번호조차 불규칙 |
| episode_production.jsonl | attempt_key 있음 | ✅ |
| pass_rate_monitor.json | 없음 | ❌ 타임스탬프만 |
| soft_failures.json | component+operation | ⚠️ 에피소드 연결 약함 |
| metrics_*.json | session_id | ⚠️ attempt 연결 없음 |
| artifacts/ | 에피소드별 폴더 | ✅ |

**보강 방안:**
```python
# interview_round.py 상단에서 1회 생성
_attempt_key = build_attempt_key(stage=4, ep=next_ep, attempt=round_num+1)

# 모든 logging 호출에 prefix
logging.info("[%s] Director verdict: %s score=%d", _attempt_key, verdict, score)
logging.warning("[%s] Advisory TruthGate: %d warnings", _attempt_key, len(warnings))
```

**예상 작업량:** ~30분 (attempt_key 변수 전파 + 100건 logging 호출 prefix 추가)

---

### C. Advisory 심각도 미표기 — MEDIUM

**현상:** CLAUDE.md에 Advisory 우선순위 정의됨:
- TruthGate = CRITICAL
- NpcDrift/NumericDrift/Flashback/InfoParadox = MAJOR
- RelDrift/LongTermRep/NumericConsistency = INFO

그러나 모든 Advisory 결과가 `logging.debug()` 또는 `logging.info()`로 동일하게 기록됨. 로그 파일에서 CRITICAL advisory와 INFO advisory 구분 불가.

**보강 방안:**
```python
# 현재
logging.debug("[Advisory] %s 완료 (%d건)", _name, len(result))

# 개선: advisory별 심각도 반영
_ADVISORY_LEVEL = {"TruthGate": "CRITICAL", "NpcDrift": "MAJOR", ...}
_level = _ADVISORY_LEVEL.get(_name, "INFO")
logging.info("[Advisory:%s:%s] %d건 경고", _level, _name, len(result))
```

**예상 작업량:** ~10줄 (매핑 dict + 로깅 포맷 변경)

---

### D. 로깅 레벨 부적합 — MEDIUM

| ID | 위치 | 현재 | 권장 | 사유 |
|---|---|---|---|---|
| D-1 | interview_round.py:3438 | `logging.debug` | `logging.warning` | Advisory 실패는 운영 가시성 필요 |
| D-2 | interview_round.py:152 | `logging.debug` | `logging.warning` | scope metrics 손실은 운영 blind spot |
| D-3 | post_processor.py:702 | `logging.debug` | `logging.info` | TruthGate 검증 실패 결과 |
| D-4 | post_processor.py:1045 | `logging.debug` | `logging.debug` | causal_graph 저장 실패 — 현행 유지 |

**레벨 분포 분석 (interview_round.py):**

| 레벨 | 건수 | 비율 | 평가 |
|------|:---:|:---:|------|
| debug | 36 | 36% | **과다** — 운영 이벤트가 debug에 매몰 |
| info | 20 | 20% | 적정 |
| warning | 43 | 43% | 적정 |
| error | 1 | 1% | **과소** — critical failure에 error 미사용 |
| critical | 0 | 0% | 미사용 (CRITICAL advisory가 있으나 logging.critical 0건) |

---

### E. 로그 싱크 분산 — **HIGH**

**현상:** 1개 에피소드의 전체 생명주기를 추적하려면 **6개 파일**을 열어야 함.

```
1. session_*.log          — 텍스트 로그 (DEBUG~ERROR)
2. episode_production.jsonl — 구조화 기록 (verdict, score, attempt)
3. pass_rate_monitor.json  — 합격률 집계
4. soft_failures.json      — 품질 저하 기록
5. metrics_*.json          — 토큰/비용 집계
6. artifacts/stage4/       — 원고 스냅샷
```

**교차 참조 불가:** session_*.log의 "Director verdict REJECT" 줄과 episode_production.jsonl의 해당 attempt를 연결할 키가 없음.

**보강 방안:** 상관 ID(§B)가 해결되면 자동으로 개선됨. 추가로:

```python
# 에피소드 완료 시 통합 요약 1줄 기록
logging.info("[EPISODE_SUMMARY] ep=%d attempts=%d verdict=%s score=%d cost=%.4f duration=%.1fs",
             ep_num, attempt_count, final_verdict, final_score, total_cost, total_duration)
```

**예상 작업량:** ~5줄 (에피소드 종료 지점에 summary 로깅 1건)

---

### F. 비용 추적 단절 — **HIGH / MEDIUM**

| ID | 내용 | 심각도 |
|---|---|---|
| F-1 | `metrics_collector.snapshot_and_reset_scope()` 결과가 episode_production.jsonl의 attempt_key에 연결되지 않음 | HIGH |
| F-2 | `_token_cost` 계산 실패 시 silent fallback to 0.0 (bare except, 로깅 호출 없음) | MEDIUM |

**보강 방안:**
```python
# episode_production.jsonl 엔트리에 cost 필드 추가
entry["token_cost"] = _token_cost
entry["token_usage"] = {"input": ..., "output": ..., "cached": ...}
```

---

### G. Director 판정 데이터 소실 — **HIGH** (신규)

**배경:** 개발 단계에서 "Director가 언제 어디서 무슨 판정을 내렸는지" 추적이 핵심. Director verdict dict에는 ~30개 필드가 있으나, 이 중 상당수가 영속화되지 않음.

#### G-1. Director Thinking 소실 — **HIGH**

**위치:** `director_ensemble.py:329, 668, 1234`

```python
_thinking = getattr(self._d, "_last_thinking", "")
if _thinking:
    print(f"      💭 [Director Thinking]\n{_thinking}")
```

**현상:** Director LLM이 생성한 thinking (추론 과정)이 `print()`로만 콘솔 출력. `_last_thinking`은:
- `session_*.log`에 기록 안 됨 (logging 호출 없음)
- `episode_production.jsonl`에 저장 안 됨
- DB에 저장 안 됨
- `director_result` dict에 포함 안 됨

**영향:** Director가 "왜 이 판정을 내렸는지"의 가장 원초적 사고 과정이 콘솔 휘발. 개발 단계에서 판정 품질 분석 불가.

#### G-2. Director LLM 원시 응답 소실 — **HIGH**

**현상:** Director의 LLM `ask()` 호출 결과에서 필드를 추출한 뒤, 원시 응답 전체는 폐기됨. `director_ensemble.py:1060-1150`에서 `_extract_json_robust()`로 파싱 후 개별 필드만 추출.

**영향:** LLM이 JSON 구조 외에 부가 텍스트를 반환해도 무시됨. 파싱 오류 시 원본 복구 불가.

#### G-3. Advisory 조합 프롬프트 소실 — **HIGH**

**위치:** `stage4_interview_round.py:1257-1488`

**현상:** 8개 Advisory 결과 + WritingDirective + POV directive + timeline + scene similarity + preflight 등 20여 개 소스에서 조립된 `_director_mandatory_context`가 Director에 전달되지만, **이 조립 결과 자체는 어디에도 저장되지 않음**.

**포함 소스 (L1260-1488):**
1. `_mandatory_text` (기본 필수 컨텍스트)
2. `_shared_failure_warnings` (공유 실패 경고)
3. `_s3_meta` quality risk warnings
4. WritingDirective
5. POV directive
6. Advisory 결과 8개 (TruthGate~NumericConsistency)
7. Timeline 정보
8. Arc time markers
9. Scene similarity
10. Candidate diversity
11. Preflight advisory
12. Python validation warnings
13. Director feedback/conflicts
14. Reference-only blocks
15. Work review advisory

**영향:** Director가 어떤 정보를 받고 판정했는지 사후 재구성 불가. "Advisory가 경고했는데 왜 PASS했는가?" 분석 시 입력 데이터 부재.

#### G-4. NC-1/NC-3 체크리스트 JSONL 미기록 — MEDIUM

**위치:** `stage4_interview_round.py:2620-2627`

**현상:**
- `consistency_checklist` (NC-3): `_director_quality_labels` dict에 저장 → HUD snapshot으로만 전달 → **episode_production.jsonl에 미기록**
- `numeric_consistency_review` (NC-1): `_director_quality_labels`에 저장되나 **JSONL에 미기록**

**영향:** 20개 카테고리 OK/ISSUE 체크 결과가 영속적으로 남지 않음. 품질 추세 분석 불가.

#### G-5. fix_scope_reasoning JSONL 미기록 — MEDIUM

**위치:** `director_ensemble.py:1187-1195, 1263`, `stage4_interview_round.py:583`

**현상:** `fix_scope_reasoning`은:
- Director가 생성 ✅
- `director_result` dict에 포함 ✅
- `prev_attempt` dict에 전달 (다음 반복용) ✅
- Chief Writer 피드백에 사용 ✅
- **episode_production.jsonl에 미기록** ❌

**영향:** "왜 inplace/partial/full을 선택했는지" 최종 기록에 남지 않음.

#### Director 판정 데이터 영속성 종합표

| 필드 | JSONL | state_updates | DB | print | prev_attempt |
|------|:---:|:---:|:---:|:---:|:---:|
| verdict | ✅ | ✅ | ✅ | ✅ | — |
| score | ✅ | ✅ | ✅ | ✅ | ✅ |
| score_breakdown | ✅ | ✅ | — | — | — |
| selection_reason | ✅ | ✅ | — | ✅ | — |
| verdict_reason | ✅ | — | — | ✅ | — |
| open_review | ✅(300자) | ✅ | — | — | ✅(200자) |
| action_items | ✅(5건) | — | — | — | ✅(3건) |
| error_category | ✅ | — | — | — | — |
| fix_scope | ✅ | — | — | ✅ | ✅ |
| fix_scope_reasoning | ❌ | — | — | — | ✅(200자) |
| consistency_checklist | ❌ | ✅ | — | — | — |
| numeric_consistency_review | ❌ | ✅ | — | — | — |
| Director thinking | ❌ | ❌ | ❌ | ✅ | ❌ |
| LLM 원시 응답 | ❌ | ❌ | ❌ | ❌ | ❌ |
| Advisory 조합 프롬프트 | ❌ | ❌ | ❌ | ❌ | ❌ |
| 앙상블 B/C 후보 원고 | ❌ | ❌ | ❌ | ❌ | ❌ |

**보강 방안:**
```python
# G-1: Director Thinking 영속화
logging.info("[Director:S4:thinking] ep=%d\n%s", ep_num, _thinking[:2000])

# G-3: Advisory 조합 프롬프트 저장 (개발 모드)
if _dev_mode:
    logging.debug("[Director:S4:assembled_prompt] ep=%d len=%d", ep_num, len(_director_mandatory_context))
    # 또는 artifact로 저장
    snapshot_logged_artifact(artifact_kind="director_input", content=_director_mandatory_context)

# G-4/G-5: JSONL 엔트리에 필드 추가
entry["consistency_checklist"] = director_result.get("consistency_checklist", {})
entry["fix_scope_reasoning"] = director_result.get("fix_scope_reasoning", "")[:300]
```

---

### H. 앙상블 후보 비보존 — MEDIUM (신규)

**현상:** Stage4 앙상블에서 3후보(A/B/C) 생성 시:
- **선택된 후보**: `artifact_kind="selected_candidate"` 또는 `"selected_before_fix"`로 디스크 저장 ✅
- **REJECT 시 최선 후보**: `artifact_kind="rejected_best"`로 저장 ✅
- **FIX 후 패치본**: `artifact_kind="patched_after_fix"` 또는 `"final_manuscript"`로 저장 ✅
- **탈락 후보 B/C**: **어디에도 저장되지 않음** ❌

**영향:** "Director가 왜 A를 골랐는지" 사후 비교 불가. 후보 간 품질 차이 분석 불가. 개발 단계에서 앙상블 전략 튜닝 시 데이터 부족.

**참고:** `episode_production.jsonl`에 `candidate_key`(첫 후보)와 `selection_candidate_key`(선택된 후보)가 기록되므로 "어떤 전략이 선택되었는지"는 추적 가능. 그러나 **원고 내용 자체**는 선택된 것만 보존.

**보강 방안:**
```python
# 개발 모드에서 전 후보 아티팩트 저장
for idx, candidate in enumerate(candidates):
    snapshot_logged_artifact(
        artifact_kind=f"ensemble_candidate_{idx}",
        content=candidate["manuscript"],
        metadata={"strategy": candidate.get("strategy", "")}
    )
```

**예상 작업량:** ~10줄 (앙상블 완료 후 루프 저장)

---

### I. PASS_WITH_FIX 반복 이력 분산 + 수정 전략 상세 누락 — **MEDIUM** (신규, 재평가)

**위치:** `stage4_interview_round.py:_append_episode_log()` (L3951-4093)

**현상:** PASS_WITH_FIX로 원고가 2~3회 수정 반복될 때:
- 각 라운드마다 `_append_episode_log()`가 호출되어 **새 JSONL 엔트리를 append** (덮어쓰기가 아닌 추가)
- 각 엔트리에 `initial_verdict`/`initial_score`(해당 라운드 1차 판정)와 `final_verdict`/`final_score`(해당 라운드 최종 판정)가 기록됨
- 그러나 **라운드 간 연결 정보가 없음** — 각 엔트리는 독립적이며, "이전 라운드에서 어떤 fix_scope/reasoning이었는지" 기록하지 않음
- `prev_attempt` dict에 직전 반복 정보가 있으나, 이는 **다음 반복 입력용**이지 JSONL에 기록되지 않음
- **반복 이력 배열(`iteration_history`)이 존재하지 않음** — 전체 반복 과정을 한눈에 보려면 같은 에피소드의 JSONL 엔트리 여러 개를 수동 취합해야 함

**예시 (3라운드 반복 시 JSONL 상태):**
```
JSONL 엔트리 1 (round=1): initial=PASS_WITH_FIX/72, final=PASS_WITH_FIX/72, fix_scope 없음
JSONL 엔트리 2 (round=2): initial=PASS_WITH_FIX/81, final=PASS_WITH_FIX/81, fix_scope 없음
JSONL 엔트리 3 (round=3): initial=PASS/89, final=PASS/89

→ 각 라운드 결과는 있으나, "round 1에서 왜 fix가 필요했고 어떤 fix_scope였는지" 등
  라운드 간 인과 연결 정보와 fix_scope_reasoning이 JSONL에 없음.
  전체 반복 이력을 하나의 구조로 조회하려면 ep 기준으로 엔트리들을 수동 취합해야 함.
```

**영향:** 라운드별 엔트리는 존재하나 fix_scope/reasoning 등 수정 전략 상세가 누락되어 수정 전략 효과 분석이 제한됨.

**보강 방안:**
```python
# episode_production.jsonl 엔트리에 반복 이력 추가
entry["iteration_history"] = [
    {"round": 1, "verdict": "PASS_WITH_FIX", "score": 72, "fix_scope": "partial"},
    {"round": 2, "verdict": "PASS_WITH_FIX", "score": 81, "fix_scope": "inplace"},
    {"round": 3, "verdict": "PASS", "score": 89, "fix_scope": None},
]
```

**예상 작업량:** ~20줄 (반복 루프에 이력 리스트 누적 + JSONL 엔트리에 추가)

---

## 3. 보강 우선순위

### Tier 0: 개발 단계 필수 (신규, 1~2시간)

| 순위 | 항목 | 작업량 | 효과 |
|------|------|--------|------|
| 0-1 | **G-1: Director Thinking 영속화** — print() 옆에 logging.info 추가 | 5분 | 판정 근거 추적 |
| 0-2 | **I: 반복 이력 보강** — JSONL 엔트리에 fix_scope/reasoning 추가 + 에피소드별 취합 뷰 | 20분 | 수정 전략 효과 분석 |
| 0-3 | **G-4/G-5: JSONL 필드 추가** — consistency_checklist + fix_scope_reasoning | 10분 | 판정 상세 영속화 |

### Tier 1: 즉시 효과 (1~2시간)

| 순위 | 항목 | 작업량 | 효과 |
|------|------|--------|------|
| 1 | **B: 상관 ID** — attempt_key를 logging 호출에 전파 | 30분 | 6개 싱크 교차 참조 가능 |
| 2 | **A: Director 프레임** — print() 옆에 logging.info 추가 | 15분 | 판정 사유 영속화 |
| 3 | **E: Episode Summary** — 에피소드 종료 시 1줄 요약 | 5분 | 통합 뷰 |

### Tier 2: 운영 개선 (2~4시간)

| 순위 | 항목 | 작업량 | 효과 |
|------|------|--------|------|
| 4 | **C: Advisory 심각도** — CRITICAL/MAJOR/INFO 태깅 | 10분 | 로그 필터링 |
| 5 | **D: 레벨 조정** — debug→warning 3건 | 5분 | 운영 가시성 |
| 6 | **F: 비용 연결** — episode_production에 cost 필드 | 30분 | 비용 추적 |

### Tier 3: 개발 심화 + 장기 (선택)

| 순위 | 항목 | 작업량 | 효과 |
|------|------|--------|------|
| 7 | **G-3: Advisory 조합 프롬프트** — 개발 모드 아티팩트 저장 | 15분 | Director 입력 재현 |
| 8 | **H: 앙상블 전후보 저장** — 개발 모드 3후보 스냅샷 | 10분 | 전략 비교 분석 |
| 9 | **G-2: LLM 원시 응답** — 파싱 전 원본 로깅 | 10분 | 파싱 오류 디버깅 |
| 10 | 로그 통합 CLI (`gldobi logs --episode 5`) | 4시간+ | 통합 타임라인 |
| 11 | logging.critical 도입 (TruthGate P1+ 시) | 10분 | 알림 연동 가능 |
| 12 | post_processor silent pass 4건에 debug 추가 | 5분 | 완전성 |

---

## 4. 설계의도 준수 확인

| 원칙 | 현행 준수 | 보강 시 주의 |
|------|:---:|------|
| Python 수집, LLM 판단 | ✅ | 로깅 추가는 수집 강화이므로 원칙 위반 없음 |
| 디렉터 주권주의 | ✅ | Director 판정 로깅은 관찰(observation)만. 판정 변경 금지. |
| 비차단 원칙 | ✅ | 모든 logging 추가는 비차단. 로깅 실패가 파이프라인에 영향 주면 안 됨. |
| fail-open preflight | ✅ | preflight 내 except pass는 **의도적**. 로깅 추가 시에도 fail-open 유지. |
| 아티팩트 디스크 용량 | ⚠️ | G-3/H/G-2는 **개발 모드 한정** 권장. 프로덕션에서 전후보+조합프롬프트 저장 시 디스크 사용량 급증 가능 (후보당 ~30KB × 3 × 에피소드). |

---

## 5. Director 판정 데이터 생명주기 (참조)

### 5.1 Director Verdict 생성 흐름

```
director_ensemble.py:select_and_judge_ensemble()
  ├─ ask() → LLM 원시 응답 (폐기됨)
  ├─ _extract_json_robust() → verdict dict (~30 필드)
  ├─ getattr(self._d, "_last_thinking") → print()만 (폐기됨)
  ├─ 판정 프레임 11줄 print() (폐기됨)
  └─ return director_result dict
```

### 5.2 Director Result 소비 경로

```
stage4_interview_round.py:run()
  ├─ director_result 수신
  ├─ verdict/score/fix_scope 추출 → 분기 로직
  ├─ _director_quality_labels에 subset 저장 → state_updates
  │   └─ consistency_checklist, score_breakdown, open_review 포함
  ├─ prev_attempt에 subset 저장 → 다음 반복 입력
  │   └─ fix_scope_reasoning[:200], open_review[:200], action_items[:3]
  ├─ _append_episode_log() → episode_production.jsonl
  │   └─ verdict, score, selection_reason, verdict_reason, open_review[:300], action_items[:5]
  │   └─ ❌ thinking, fix_scope_reasoning, consistency_checklist, NC-1
  └─ snapshot_logged_artifact() → 선택된 원고만 디스크 저장
```

### 5.3 JSONL 엔트리 필드 목록 (현행, 전량)

`_append_episode_log()` (interview_round.py:4035-4087)에서 기록되는 **35개 top-level 필드**:

**메타데이터 (7)**

| 필드 | 출처 | 절삭 |
|------|------|------|
| `ts` | 타임스탬프 | — |
| `ep` | 에피소드 번호 | — |
| `round` | 라운드 번호 | — |
| `ep_attempt_total` | 에피소드 누적 시도 횟수 | — |
| `attempt_key` | `build_attempt_key()` | — |
| `model` | 사용 모델명 | — |
| `duration_ms` | 라운드 소요시간 | — |

**후보/아티팩트 (6)**

| 필드 | 출처 | 절삭 |
|------|------|------|
| `candidate_key` | 첫 후보 키 | — |
| `content_hash` | 후보 해시 | — |
| `artifact_path` | 아티팩트 경로 | — |
| `selection_candidate_key` | 선택된 후보 키 | — |
| `selection_content_hash` | 선택 후보 해시 | — |
| `selection_artifact_path` | 선택 아티팩트 경로 | — |

**Director 판정 (11)**

| 필드 | 출처 | 절삭 |
|------|------|------|
| `verdict` | director_result["verdict"] (=initial) | — |
| `score` | director_result["score"] (=initial) | — |
| `initial_verdict` | 1차 판정 | — |
| `initial_score` | 1차 점수 | — |
| `final_verdict` | 최종 판정 (FIX 후) | — |
| `final_score` | 최종 점수 (FIX 후) | — |
| `selected` | director_result["selected"] | — |
| `strategy` | 선택된 전략명 | — |
| `selection_reason` | director_result["selection_reason"] | — |
| `verdict_reason` | director_result["verdict_reason"] | — |
| `error_category` | director_result["error_category"] | — |

**Director 상세 (3)**

| 필드 | 출처 | 절삭 |
|------|------|------|
| `action_items` | director_result["action_items"] | **5건** |
| `score_breakdown` | director_result["score_breakdown"] | — |
| `open_review` | director_result["open_review"] | **300자** |

**비용/토큰 (4)**

| 필드 | 출처 | 절삭 |
|------|------|------|
| `round_total_calls` | 라운드 내 LLM 호출 수 | — |
| `round_total_tokens` | 라운드 내 토큰 합계 | — |
| `round_total_cost_usd` | 라운드 내 비용 합계 | — |
| `round_model_breakdown` | 모델별 비용 분해 | — |

**플래그 (nested dict, 1)**

| 필드 | 내용 |
|------|------|
| `flags` | `patch_mode`, `patch_fallback`, `tot`, `mad`, `asp`, `strategy_budget`, `strategy_count`, `reject_bucket` |

**패치 추적 (nested dict, 1)**

| 필드 | 내용 |
|------|------|
| `patch_trace` | `patch_strategy`, `patch_targets`, `unchanged_ratio`, `fallback_reason`, `focus`, `structural_attempted` |

**기타 (2)**

| 필드 | 출처 | 절삭 |
|------|------|------|
| `reason` | 에러/거부 사유 | — |
| `warnings` | 검증 경고 목록 | — |

**JSONL에 미기록 (확인됨)**

| 필드 | 대안 저장 위치 |
|------|--------------|
| `fix_scope_reasoning` | prev_attempt dict (메모리, 200자) |
| `consistency_checklist` | state_updates._director_quality_labels |
| `numeric_consistency_review` | state_updates._director_quality_labels |
| Director thinking | print()만 |
| Advisory 조합 프롬프트 | 없음 |
| 앙상블 B/C 후보 원고 | 없음 |

---

## 부록: 감리 과정

| Pass | 작업 | 결과 |
|------|------|------|
| 1차 | Explore 에이전트 전수조사 (60건 원시 발견) | 카테고리별 분류 |
| 2차 | 코드 직접 대조 — silent swallow 검증 | 7건 오탐 제거 (fail-open + 텔레메트리 + DB logging 확인) |
| 3차 | print/logging/ui.log 수치 교차 검증 | 수치 확정 |
| 4차 | 설계의도 대조 (CLAUDE.md Advisory 심각도, preflight fail-open, base_agent 절단 복구) | 양호 항목 확인 |
| 5차 | 최종 보강 방안 ROI 산정 + 수치 정합성 | **15건 최종 확정** |
| 6차 | Director 판정 데이터 생명주기 심층 조사 (Explore 에이전트 37 tool 사용) | 12개 소실 카테고리 식별 |
| 7차 | 코드 직접 대조 — _last_thinking 경로, snapshot_logged_artifact 종류, _append_episode_log 필드, _director_mc_parts 조립 경로, fix_scope_reasoning 전파 체인 | 전 항목 file:line 확인 |
| 8차 | 영속성 종합표 교차 검증 + 보강 우선순위 재산정 | **22건 최종 확정 (기존 15 + 신규 7)** |
| 9차 | 사실 검증 Pass 1 — G/H/I/A/B/D/F 전 항목 3-agent 병렬 코드 대조 | 5건 오류 발견 |
| 10차 | 사실 검증 Pass 2 — 오류 5건 수정: print 수치(14→11, 16→18), F-2 표현(logging.debug→bare except), I 메커니즘(덮어쓰기→append), §5.3 필드(11→35개 전량 기재) | 수정 완료 |
| 11차 | 사실 검증 Pass 3 — 수정 후 문서 정합성 확인, 감리 부록 갱신 | **22건 유지, 사실 오류 0건** |
