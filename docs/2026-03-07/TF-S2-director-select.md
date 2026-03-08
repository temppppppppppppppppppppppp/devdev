# TF: Stage 2 Arc 앙상블 — Director 선택 주체 일원화

> 작성일: 2026-03-07
> 근거: Stage 3/4는 Director가 후보 비교 선택, Stage 2는 Python 자동 채점 선택 후 Director 단일 심사
> 목표: Stage 2의 Python 자동 선택을 제거하고, Director가 유효 후보를 직접 비교·선택하도록 일원화

---

## 1. 현황

### Stage별 앙상블 선택 방식 비교

| Stage | 앙상블 | 후보 수 | Python 역할 | 선택 주체 | 상태 |
|-------|--------|---------|-------------|-----------|------|
| Stage 2 (Arc) | `ArcEnsembleGenerator` | 3 | `_evaluate_candidate()` 자동 채점 → **최고점 선택** | **Python** | **변경 필요** |
| Stage 3 (Blueprint) | `BlueprintEnsembleGenerator` | 3 | 구조 필터 (씬 4개+, 500자+) → 유효 후보 전달 | **Director** | 정상 |
| Stage 4 (Manuscript) | `ChiefWriter._generate_candidates()` | 3 | `ManuscriptValidator` Python 검증 | **Director** | 정상 |

### Stage 2 현재 흐름 (문제)

```
arc_ensemble.generate_ensemble()
  → 3전략 병렬 생성 (conservative, balanced, creative)
  → Python _evaluate_candidate() 자동 채점 (구조적 점수)
  → scored_candidates.sort() → best = scored_candidates[0]  ← Python이 선택
  → return (best, all_candidates)

four_phase_arc_generator.generate_arc()
  → best_arc, all_candidates = ensemble.generate_ensemble()
  → SpareCandidate: best_arc 제외한 나머지를 _spare_candidates에 보존
  → Phase 2.6 [TF-47]: if len(all_candidates) >= 2 → director.compare_and_select_arc()
    → Director가 비교 선택 (PASS/REJECT/PASS_WITH_FIX)
    → PASS → return best_arc  (Director 선택한 arc로 교체됨)
    → REJECT → retry loop (continue)
  → Phase 3 Validator 폴백: director 미사용 or 단일 후보 시

stage2_finalizer.run_finalize()
  → refined_arc (= 이미 1개 선택된 Arc) 수신
  → director.audit_strategic_plan() — 단일 심사 (PASS/REJECT/PASS_WITH_FIX)
```

### 기존 코드 현황 정리

| 위치 | 코드 | 역할 |
|------|------|------|
| `arc_ensemble.py` L374-376 | `scored_candidates.sort()` + `best = scored_candidates[0]` | **Python이 최고점 선택** |
| `four_phase_arc_generator.py` L560 | `best_arc, all_candidates = self.ensemble.generate_ensemble()` | 반환값 소비 |
| `four_phase_arc_generator.py` L579-583 | SpareCandidate 보존 (`best_arc` 제외 나머지) | `best_arc` 참조에 의존 |
| `four_phase_arc_generator.py` L666-728 | **Phase 2.6: `director.compare_and_select_arc()`** | **이미 존재하는 Director 비교 선택** |
| `director_ensemble.py` L324-420 | `compare_and_select_arc()` 메서드 | **이미 구현 완료** (테스트 7개) |
| `stage2_finalizer.py` L430 | `director.audit_strategic_plan()` | 단일 심사 (선택 아님) |

### 핵심 문제

1. **이중 선택**: Python이 먼저 `best`를 고르고(L376), 그 후에 Director가 다시 비교(L671) — 역할 중복
2. **SpareCandidate 오작동 위험**: `best_arc`가 Python 선택이므로, Director가 다른 후보를 선택해도 SpareCandidate에는 Python 기준 차순위가 남음
3. **`stage2_finalizer` 단일 심사**: Director 비교 선택이 `four_phase_arc_generator` Phase 2.6에 있고, `stage2_finalizer`에 도달할 때는 이미 1개 → `audit_strategic_plan()` 단일 심사만 수행
4. **Stage 3/4와 비대칭**: Stage 3는 `blueprint_ensemble.py`가 구조 필터만 수행 후 "Python은 선택하지 않음" (L318 주석)

---

## 2. 변경 계획

### 목표 흐름

```
arc_ensemble.generate_ensemble()
  → 3전략 병렬 생성 (conservative, balanced, creative)
  → Python _evaluate_candidate() 구조 필터 (탈락 기준 미달만 제거)
  → 유효 후보 전부 반환 (best_arc=None, all_candidates=[valid...])
  → "Python은 선택하지 않음 - Director에게 전체 전달" (Stage 3 패턴)

four_phase_arc_generator.generate_arc()
  → best_arc=None, all_candidates = ensemble.generate_ensemble()
  → best_arc=None 처리: SpareCandidate 로직 조정
  → Phase 2.6 [TF-47]: director.compare_and_select_arc() — 기존 코드 유지
    → Director가 비교 선택 + 심사 동시 수행
    → PASS → return selected_arc
    → REJECT → retry loop
  → Phase 3 Validator 폴백: 단일 후보 or Director 실패 시
```

### 핵심 변경

#### 2-A. `arc_ensemble.py` — Python 선택 제거, 전 후보 반환 [P1]

**현재** (`arc_ensemble.py` L373-398):
```python
scored_candidates.sort(key=lambda x: x.get("_score", 0), reverse=True)
best = scored_candidates[0]  # ← Python이 선택
# ... 로깅 ...
return best, scored_candidates  # best + all
```

**변경**:
```python
scored_candidates.sort(key=lambda x: x.get("_score", 0), reverse=True)

# [TF-S2] 구조 필터 — 서사적 선택은 Director에게 위임
# ※ 글자수 하드 필터는 L320-357에서 이미 적용됨 (ep_count × 450자/화)
#   → scored_candidates는 글자수 충족 후보만 포함 (전부 미달 시 최장 1개 폴백)
STRUCTURAL_MIN_SCORE = 50
valid = [c for c in scored_candidates if c.get("_score", 0) >= STRUCTURAL_MIN_SCORE]

if not valid:
    valid = scored_candidates[:1]  # 최소 1개 보장

# [TF-S2] Python은 선택하지 않음 — Director에게 전체 전달 (Stage 3 패턴)
return None, valid  # best_arc=None
```

- **글자수 하드 필터 (기존, L320-357)**: `ep_count × MIN_CHARS_PER_EPISODE(450)` 미만 → 채점 전 즉시 탈락. **이미 구현 완료** — 추가 코드 불필요
  - 글자수 채우고 → `_evaluate_candidate()` 채점 → `STRUCTURAL_MIN_SCORE` 필터 → Director 앞에 가는 구조
- **구조 점수 필터 (신규)**: `STRUCTURAL_MIN_SCORE = 50` — 필수 필드 누락·금지 아이템 위반 등 객관적 결함만 필터
- `_evaluate_candidate()` 자체는 유지 — 점수를 Director 참고 정보로 전달
- 서사적 품질 비교는 Director에게 위임

#### 2-B. `four_phase_arc_generator.py` — `best_arc=None` 처리 [P1]

**영향 지점 3곳**:

**(1) L560 — `generate_ensemble()` 반환값 소비** (일반 경로):
```python
# 현재:
best_arc, all_candidates = self.ensemble.generate_ensemble(...)
# SpareCandidate: best_arc 제외한 나머지 보존
if all_candidates and len(all_candidates) > 1:
    for _c in all_candidates:
        if _c is not best_arc and _c not in _spare_candidates:
            _spare_candidates.append(_c)

# 변경:
best_arc, all_candidates = self.ensemble.generate_ensemble(...)
# [TF-S2] best_arc=None → SpareCandidate 보존 스킵, Director가 선택
# SpareCandidate는 Director REJECT 후 차순위 재활용에만 사용
```

**(2) L587-588 — `best_arc` null check**:
```python
# 현재:
if best_arc:
    logging.info(f"✅ [Phase 2] Ensemble 완료 — 선택 전략: {best_arc.get('strategy', '?')}")

# 변경:
if all_candidates:
    logging.info(f"✅ [Phase 2] Ensemble 완료 — {len(all_candidates)}개 후보 → Director 선택 대기")
```

**(3) L666-668 — Phase 2.6 Director 선택 조건**:
```python
# 현재:
if director and len(all_candidates) >= 2:
    _valid_for_director = [c for c in all_candidates if c.get("tactical_doc")]
    if len(_valid_for_director) >= 2:

# 변경: best_arc=None이면 무조건 Director 선택 (단일 후보도 Director 심사)
if director and all_candidates:
    _valid_for_director = [c for c in all_candidates if c.get("tactical_doc")]
    if _valid_for_director:
```

**(4) L1032 — Patch Mode 경로**: 동일 패턴 적용

#### 2-C. SpareCandidate 로직 조정 [P1]

**현재**: `best_arc` 제외한 나머지를 `_spare_candidates`에 보존 → Director REJECT 시 차순위 재활용
**변경**: `best_arc=None`이므로 Director REJECT 후 `_spare_candidates`에 `all_candidates` 중 Director가 선택하지 않은 후보를 보존

```python
# Phase 2.6 Director REJECT 경로 (L706-724):
# 현재:
_prev_rejected_arc = best_arc
_spare_candidates.clear()
continue

# 변경: Director가 선택+REJECT한 arc만 _prev_rejected_arc에, 나머지는 spare로 보존
# [TF-S2-B] _dir_arc=None 방어 — Director 파싱 실패 시 _valid_for_director[0] 폴백
_prev_rejected_arc = _dir_arc or _valid_for_director[0]
_spare_candidates = [c for c in _valid_for_director if c is not _prev_rejected_arc]
continue
```

**[TF-S2-B 발견] L708 `best_arc = _dir_arc or best_arc` edge case**:
- 변경 후 `best_arc`는 Phase 2.6 진입 시 **항상 None**
- `_dir_arc`도 None (Director 파싱 실패) → `best_arc = None or None = None`
- L721 `_prev_rejected_arc = None` → 다음 retry에서 패치 모드 진입 불가
- **대응**: L708을 `best_arc = _dir_arc or _valid_for_director[0]`로 변경 (위 코드 블록에 반영됨)

#### 2-D. `stage2_finalizer.py` — 변경 없음

- `stage2_finalizer.run_finalize()`는 `refined_arc` (= 이미 선택된 1개)를 수신
- `four_phase_arc_generator` Phase 2.6에서 Director가 선택한 Arc가 `refined_arc`로 전달됨
- `audit_strategic_plan()` 단일 심사는 **유지** — Director가 Phase 2.6에서 이미 비교 선택했으므로, Finalizer에서는 추가 심사(NC-1 advisory, 플롯 중복, 연속성 등)만 수행
- **단, `director` 인자 미사용 시(Phase 2.6 스킵 시)**: Phase 3 Validator 폴백 → Finalizer에서 단일 심사

#### 2-E. `director_ensemble.py` — tactical_doc 절삭 제거 [P1]

- `compare_and_select_arc()` 메서드 이미 완비 (L324-420+)
- 프롬프트, 파싱, 폴백, 에러 처리 모두 구현 완료
- 테스트 7개 존재 (`test_director_modules.py` L999-1192)
- **변경**: L391 `tactical[:8000]` → `tactical` (절삭 제거)
  - Director가 선택 주체가 되므로 **전문을 봐야 공정한 비교**
  - 7화 Arc 3개 기준 tactical_doc 합계 ~15K자 → Gemini 1M 컨텍스트 여유 충분
  - `sc_str[:1000]`, `joint_str[:1000]`, `prev_arc_context[:6000]`, `block_summary[:4000]`은 현행 유지 (보조 정보, 절삭 영향 미미)

---

## 3. 분량 기준

### 글자수 기준 (SSOT: `constants.py`)

| 상수 | 값 | 비고 |
|------|-----|------|
| `Stage2Limits.MIN_CHARS_PER_EPISODE` | **450** | 화당 최소 (TF-59에서 500→450 하향) |
| `Stage2Limits.RECOMMENDED_CHARS_PER_EPISODE` | 600 | 화당 권장 |
| `compare_and_select_arc()` 절삭 | ~~8,000자~~ → **전문** | Director 선택 주체 일원화에 따라 절삭 제거 (L391) |

### 하드 필터 적용 (§2-A Step 1)

| ep_count | 최소 글자수 | 계산 |
|----------|-----------|------|
| 3화 (Blitz) | 1,350자 | 3 × 450 |
| 5화 (Standard) | 2,250자 | 5 × 450 |
| 7화 (Epic) | 3,150자 | 7 × 450 |

- **하드 필터 (기존 L320-357)**: `len(tactical_doc) < ep_count × 450` → 채점 전 즉시 탈락 (**이미 구현 완료**)
- **소프트 필터 (신규)**: `_evaluate_candidate()` 점수 기반 (`STRUCTURAL_MIN_SCORE = 50`)

### `_evaluate_candidate()` 기존 분량 감점 (유지)

```python
# arc_ensemble.py L740-770 (변경 없음)
min_length = ep_count * Stage2Limits.MIN_CHARS_PER_EPISODE  # 하드 필터와 동일 기준
if len(tactical) < min_length:
    score -= 40  # CRITICAL — 하드 필터 통과 못한 후보는 이미 제거됨
elif len(tactical) < ep_count * 600:
    score -= 10  # 권장 미달
elif len(tactical) < ep_count * 700:
    score -= 5   # 보통
```

- 하드 필터(Step 1)로 글자수 미달 후보가 이미 제거되므로, `score -= 40` 감점은 사실상 사문화
- 하드 필터 통과 후 소프트 필터(Step 2)에서 다른 구조 결함만 평가

---

## 4. Stage 3 참조 분석

Stage 3는 **이미 올바른 패턴으로 구현**되어 있으며, Stage 2 변경의 참조 모델.

### Stage 3 핵심 코드

**`blueprint_ensemble.py` L290-341:**
```python
# Python 구조 필터만 수행
qualified_candidates = []
for c in candidates:
    scenes = c.get("scene_breakdown", {})
    integrated = c.get("integrated_scenario", "")
    if len(scenes) >= 4 and len(str(integrated)) >= 500:
        qualified_candidates.append(c)

# 전부 반환 — "Python은 선택하지 않음 - Director에게 전체 전달" (L318)
return qualified_candidates[0], qualified_candidates
```

**`three_phase_blueprint_generator.py` L382-402:**
```python
# Director에게 전체 후보 전달
result = self.validator.validate(
    ...,
    all_candidates=all_candidates,  # 3후보 전부
)

# Director 선택 결과 반영
if result.get("selected_blueprint"):
    best_blueprint = result["selected_blueprint"]
```

### Stage 2가 Stage 3과 다른 점 (변경 전)
| 항목 | Stage 3 (정상) | Stage 2 (변경 필요) |
|------|---------------|-------------------|
| Python 역할 | 구조 필터만 (씬 수, 분량) | **채점 + 정렬 + 최고점 선택** |
| Director 역할 | 비교 선택 + 심사 | Python 선택 후 재비교 (이중 선택) |
| Director 비교 메서드 | `validate(all_candidates=...)` | `compare_and_select_arc()` (이미 존재) |
| 반환 | `(대표, 전체 후보)` | `(최고점 1개, 전체)` |

---

## 5. 사이드이펙트 분석

### 5-A. SpareCandidate 로직 [영향: 중]

**현재**: `best_arc` 기준으로 나머지를 spare에 보존
**변경 후**: `best_arc=None`이므로 SpareCandidate 보존 로직 변경 필요

- L555-557: `_spare_candidates.pop(0)` → `best_arc = spare` (Director 미사용 시 폴백) — **변경 불필요** (단일 후보로 처리)
- L579-583: `if _c is not best_arc` → `best_arc=None`이면 모든 후보가 spare에 들어감 — **변경 필요**: best_arc=None일 때 spare 보존 스킵

### 5-B. Phase 2.5 Auto-Sanitize + Location 주입 [영향: 높음]

**현재** (L642-654):
- L642: `best_arc = self._check_arc_end_state(best_arc)` — advisory only (로깅만, arc 불변)
- L644-654: `arc_start_state.location` 강제 주입 — **mutative** (`setdefault`로 location 채움, TF-22-01)

**변경 후**: `best_arc=None` → `_check_arc_end_state(None)` → L1446 `arc.get()` → **AttributeError 크래시**

**추가 위험 (감리 14 발견)**: L644-654 location 주입은 **mutative**이므로 Phase 2.6 이후로 이동하면 Director PASS/PASS_WITH_FIX 조기 return(L691, L704) 시 **location 주입 누락** → TF-22-01 Arc 경계 공간 연속성 패치 무력화

- **대응 (2단계 분리)**:
  1. **L644-654 location 주입 → Phase 2.6 이전 위치 유지 + 대상 변경** (`best_arc` 단일 → `for _cand in all_candidates:` 전 후보 루프)
  2. **L642 `_check_arc_end_state` → Phase 2.6 이후 이동** (advisory-only, Validator 폴백 경로에서만 실행)
- **필수 조건**: Phase 2.6 이후 이동하는 코드(auto-sanitize + NS-3-B)는 Director 스킵/예외 경로에서 `best_arc = all_candidates[0]`이 **선행 할당**되어야 함.
- **구현 패턴**:
  ```python
  # Phase 2.5: location 주입 — 모든 후보에 사전 적용 (Phase 2.6 이전)
  if prev_arcs:
      _last_end = prev_arcs[-1].get("state_constraints", {}).get("arc_end_state", {})
      _plan_loc = _last_end.get("location") if isinstance(_last_end, dict) else None
      _exec_state = self._load_execution_state(prev_arcs[-1])
      _forced_loc = (_exec_state.get("protagonist_location") if _exec_state else None) or _plan_loc
      if _forced_loc:
          for _cand in all_candidates:
              _sc = _cand.setdefault("state_constraints", {})
              _as = _sc.setdefault("arc_start_state", {})
              if not _as.get("location"):
                  _as["location"] = _forced_loc

  # ... Phase 2.6 Director 선택 ...

  # Phase 2.6 직후, auto-sanitize 직전 (Validator 폴백 경로)
  if best_arc is None and all_candidates:
      best_arc = all_candidates[0]  # Director 미사용/실패 시 폴백
  best_arc = self._check_arc_end_state(best_arc)
  ```

### 5-C. NS-3-B Treatment Check [영향: 소]

**현재** (L657): `_check_arc_vs_block_targets(best_arc, curr_block, arc_no)`
**변경 후**: `best_arc=None` → 체크 불가

- **대응**: Director 선택 후 또는 `all_candidates[0]`으로 대표 체크

### 5-D. Phase 2.6 Director 선택 조건 완화 [영향: 소]

**현재**: `len(all_candidates) >= 2` 조건
**변경 후**: `all_candidates` 존재 시 무조건 Director 선택 (단일 후보도)

- **이점**: 단일 후보도 Director가 심사 → Stage 3/4와 동일 패턴
- **이중 심사**: Phase 2.6 compare + `stage2_finalizer` audit → 유지 (defense-in-depth, §5-I 참조)

### 5-E. Patch Mode 경로 [영향: 높음]

**현재** (L1032): `best_arc, all_candidates = ensemble.generate_ensemble(...)` → `if not best_arc: return FAILED`
**문제**: `best_arc=None` 항상 → L1055에서 무조건 FAILED → Patch Mode 완전 불통
**추가 문제**: L1061 `_check_arc_end_state(best_arc)`, L1070 `best_arc.setdefault(...)` → NoneType 크래시
**원인**: Patch Mode에는 Director 비교 단계 없음 (`director` 인자 미수신). `single_strategy`로 1개 전략만 생성하므로 비교 불필요.

**대응**:
```python
# L1055 변경:
if not all_candidates:
    logging.warning("[Patch Mode] Arc ensemble 후보 없음 → 폴백 필요")
    ...
    return None, pipeline_result
# Patch Mode: Director 비교 없음 → 첫 후보를 best_arc로 사용
best_arc = all_candidates[0]
```

### 5-F. ASP 교정 경로 [영향: 중]

**현재** (L598-626): `if retry >= 2 and adversarial_self_play and best_arc` → ASP에 `best_arc` 전달
**문제**: ASP 블록(L598)이 Phase 2.6(L666) **이전에** 실행됨. `best_arc=None`이면 ASP 조건이 False → ASP 완전 스킵
**대응**: ASP 블록을 Phase 2.6 이후(Director 선택 후)로 이동 — `best_arc`가 Director에 의해 할당된 후 ASP 실행

**⚠️ ASP 이동 트레이드오프** (감리 22 시나리오 8 발견):
1. **Director REJECT 시 ASP 미실행**: Phase 2.6 REJECT → `continue` → ASP 도달 불가. 현재는 Phase 2.6 이전에 ASP 실행 → REJECT 시에도 ASP 교정 적용됨. 이동 후 ASP 실행 빈도 감소.
2. **"검증 후 변경" 문제**: Director PASS → ASP 교정 → return 시, **Director가 검증하지 않은 Arc가 반환**됨. 대원칙 3(Director 주권주의) 관점에서 문제 가능성.
3. **대안 검토**: ASP를 Phase 2.6 이전에 유지하되, `best_arc` 대신 `all_candidates[0]` (최고 점수 후보)로 ASP 실행 → Director에게 교정된 후보 전달. 또는 ASP를 Phase 2.6 PASS 경로에서만 실행하고 **Director 재심사**(audit) 단계에서 검증.
4. **권장**: ASP는 Phase 2.6 **이전** 유지, `if retry >= 2 and adversarial_self_play and all_candidates:` + `all_candidates[0]`으로 대상 변경. Director가 ASP 교정 결과를 포함한 후보를 비교 선택하므로 대원칙 3 준수.

### 5-G. EnsembleFB 전략 기록 [영향: 중]

**현재** (L631): `_current_strategy = best_arc.get("_ensemble_meta", {}).get("best_strategy", "unknown")`
**문제**: L631이 Phase 2.6(L666) **이전에** 실행됨. `best_arc=None`이면 `NoneType.get()` → **AttributeError 크래시**
**대응**: L631-637 블록 전체를 Phase 2.6 이후(Director 선택 후)로 이동 필수.
**추가 대응**: Phase 2.6 PASS/PASS_WITH_FIX → 즉시 return(L691/L704) 경로에서 `pipeline_result["phases"]["generate"]` 키 미기록 위험. **L683-688 Director 선택 기록과 함께 EnsembleFB 기록도 return 직전에 삽입** 필요:
```python
# Phase 2.6 PASS return 직전 (L689-691):
_current_strategy = best_arc.get("_ensemble_meta", {}).get("best_strategy", "unknown")
pipeline_result["phases"]["generate"] = {"selected_strategy": _current_strategy, ...}
return best_arc, pipeline_result
```

### 5-H. Phase 3 Validator 폴백 — `best_arc=None` 크래시 [영향: 높음]

**현재** (L728→L735): Director 예외 시 Phase 3 Validator 도달 → `validator.validate(arc=best_arc)`
**문제**: `best_arc=None` → Validator에 None 전달 → **크래시**
**발생 조건**: Phase 2.6 `compare_and_select_arc()` 내부 예외 (API 장애 등)
**대응**: Phase 2.6 예외 catch 내부에서 `best_arc = all_candidates[0]` 폴백 설정

```python
# L727-728 변경:
except Exception as e:
    logging.warning(f"[TF-47] Director 비교 실패, Validator 폴백: {str(e)[:100]}")
    best_arc = all_candidates[0]  # [TF-S2] Validator 폴백용 대표 후보
```

**downstream 안전 보장**: 이 폴백 이후 L810 `negative_injector.record_rejection(best_arc, ...)` (Validator REJECT 경로)에서도 `best_arc`가 dict로 보장됨. Phase 2.6 예외 catch에서 폴백 누락 시 L810에서 NoneType 크래시 → **이 폴백은 필수**.

**참고 (이중 폴백 구조)**: `compare_and_select_arc()` 내부에도 자체 try/except가 있어 `_fallback_arc_selection(decision="PASS", candidates[0])` 반환. 따라서 외부 except(L727) 도달은 `compare_and_select_arc()` 호출 **이전** 단계(인자 구성 등)의 예외로 한정됨.

### 5-I. `stage2_finalizer` 이중 심사 — 유지 (defense-in-depth) [영향: 소, P2 최적화]

- Phase 2.6 `compare_and_select_arc()` PASS → `stage2_finalizer`의 `audit_strategic_plan()` 재심사
- 동일 Director가 같은 Arc를 2번 심사 → LLM 2-4회 호출 (compare 1 + audit 1-3)

**TF-S2-E 조사 결론: 이중 심사는 정당하며 유지**:
- `audit_strategic_plan()`은 `compare_and_select_arc()`에 **없는** 검사 수행:
  - Entity consistency (V61, Python+LLM)
  - Protagonist name hard guard (Python)
  - NC-1-S2 산술 advisory
  - Cross-Arc 자산 연속성
  - Self-Consistency voting (SC)
  - Contradiction Firewall (Python 후처리)
- 중복 영역: LLM 모순 감지 일부 겹침 → **보완적 (defense-in-depth)**
- **`director_already_compared` 플래그는 P2 최적화** (1-2 LLM 호출 절감) → 이번 TF에서 구현 안 함

**[TF-S2-E GAP]** `pipeline_result`가 `stage2_finalizer`에 전달되지 않음 → Phase 2.6 상태 전파 경로 없음. P2 최적화 시 `run_finalize()` 시그니처 확장 필요.

### 5-J. Phase 2.6 PASS_WITH_FIX — InPlace 실행 경로 [영향: 중, 기존 문제]

**TF-S2-C 발견**: Phase 2.6에서 `PASS_WITH_FIX` 반환 시 L693-704에서 **즉시 return** → InPlace 패치 루프 없이 `pipeline_result["final_verdict"] = "PASS"` 설정

```python
# 현재 코드 L693-704:
elif _dir_decision == "PASS_WITH_FIX" and _dir_arc:
    best_arc = _dir_arc
    pipeline_result["final_verdict"] = "PASS"  # ← 즉시 PASS
    return best_arc, pipeline_result  # ← InPlace 없이 탈출
```

**Stage 3과의 차이**:
- Stage 3 `three_phase_blueprint_generator.py`: PASS_WITH_FIX → generate 루프 내에서 `_inplace_patch_blueprint()` + Director 재심사 (최대 3회)
- Stage 2: PASS_WITH_FIX → 즉시 return → `stage2_finalizer`의 `audit_strategic_plan()`에서 별도로 PASS_WITH_FIX 판정 시에만 InPlace 진입

**이것은 기존 문제 (TF-47 설계)이며 이번 TF-S2 변경과 무관**. 현재 코드에서도 Phase 2.6 PASS_WITH_FIX는 InPlace 없이 return됨. `stage2_finalizer`의 audit이 InPlace 기회를 제공하므로 **§5-I의 이중 심사 유지가 이 경로의 InPlace를 보장**.

**stage2_finalizer InPlace 루프 세부**: audit에서 PASS_WITH_FIX 판정 시 `_inplace_patch_arc()` 최대 3회 패치 + Director 재심사 반복. PF-3 소진(3회 모두 실패) 시 최종 패치본 채택 (`stage2_finalizer.py` L531-692).

**주의**: §5-I에서 audit 스킵을 구현하면 이 경로의 InPlace 기회도 소멸. 따라서 §5-I의 P2 최적화 시 PASS_WITH_FIX 경로는 반드시 audit 유지 필요.

---

## 6. 트레이드오프

| 항목 | 현재 | 변경 후 |
|------|------|---------|
| 선택 주체 | Python (구조적 점수) + Director (이중 비교) | Director만 (일원화) |
| Python 역할 | 채점 + 선택 | 구조 필터만 |
| LLM 호출 | compare 1회 + audit 1-3회 = 2-4회 | compare 1회 + audit 1-3회 = 2-4회 (유지, §5-I) |
| 컨텍스트 크기 | Arc 3개 (compare) + Arc 1개 (audit) | 동일 (audit 유지) |
| 시간 | ~70s | ~70s (audit 유지로 동일) |
| 비용 | ~$0.06/Arc | ~$0.06/Arc (audit 유지로 동일) |
| 품질 | Python 선택 후 Director 재확인 | Director 직접 선택 (**서사적 최적**) + audit defense-in-depth |

### 비용 영향
- **현재**: Python 선택(무료) + Director compare(1회) + Director audit(1-3회) = 2-4회 LLM
- **변경 후**: Director compare(1회, 선택 주체) + Director audit(1-3회, 유지) = 2-4회 LLM
- **비용 변경 없음** — audit 유지 (§5-I TF-S2-E 결론: defense-in-depth 정당)
- **품질 개선**: Python 이중 선택 제거 → Director 일원화로 서사적 최적 선택
- P2 최적화: 향후 `director_already_compared` 플래그로 audit SC 투표 경량화 가능 (1-2 LLM 절감)

---

## 7. 영향 파일

| 파일 | 변경 내용 | 규모 |
|------|-----------|------|
| `arc_ensemble.py` | `generate_ensemble()` 반환값 변경 (`best=None`, 구조 필터) | 중 |
| `four_phase_arc_generator.py` | `best_arc=None` 처리 + SpareCandidate 조정 + Phase 2.5/2.6 순서 | 대 |
| `director_ensemble.py` | L391 `tactical[:8000]` → `tactical` (절삭 제거) | 소 |
| `director.yaml` | **변경 없음** — 프롬프트 이미 존재 | - |
| `stage2_finalizer.py` | **변경 없음** — 이중 심사 유지 (defense-in-depth, §5-I/TF-S2-E 결론). P2 최적화 후순위 | - |
| `stage2_orchestrator.py` | L629 `_ensemble_meta.best_strategy` 참조 — Director 선택 후 meta 키 갱신 | 소 |

### 호출자 변경
- `four_phase_arc_generator.generate_arc()` L560, L1032 — `best_arc=None` 처리
- `four_phase_arc_generator` L579-583 — SpareCandidate 로직 조정
- `four_phase_arc_generator` L587-588, L631 — `best_arc` null check 보강
- `four_phase_arc_generator` L642, L657 — Phase 2.5 auto-sanitize/NS-3-B 순서 조정
- `stage2_finalizer.run_finalize()` — **변경 없음** (이중 심사 유지, §5-I)

---

## 8. 테스트 계획

| # | 테스트 | 검증 내용 |
|---|--------|-----------|
| 1 | `test_ensemble_returns_none_best_all_valid` | `generate_ensemble()` → `(None, valid_candidates)` 반환 확인 |
| 2 | `test_ensemble_structural_filter` | STRUCTURAL_MIN_SCORE 미달 후보 제외, 1개 보장 |
| 3 | `test_four_phase_best_arc_none_handling` | `best_arc=None` 시 Phase 2.6 Director 선택 진입 확인 |
| 4 | `test_spare_candidate_after_director_reject` | Director REJECT 시 미선택 후보가 spare에 보존 |
| 5 | `test_auto_sanitize_after_director_select` | Phase 2.5 auto-sanitize가 Director 선택 후 실행 |
| 6 | `test_patch_mode_best_arc_none` | Patch Mode에서 `all_candidates` 기반 판단 |
| 7 | `test_single_candidate_director_select` | 단일 후보도 Director `compare_and_select_arc()` 경유 |
| 8 | `test_location_injection_all_candidates` | 모든 후보에 `arc_start_state.location` 사전 주입 확인 (§5-B) |
| 9 | `test_existing_compare_and_select_arc_tests_pass` | 기존 7개 테스트 회귀 없음 확인 |
| 10 | `test_asp_runs_with_top_candidate_before_director` | ASP 블록이 Phase 2.6 이전에 `all_candidates[0]` 기반으로 실행 (§5-F) |
| 11 | `test_ensemble_fb_strategy_after_director` | EnsembleFB `_current_strategy`가 Director 선택 후 취득 (§5-G) |
| 12 | `test_audit_runs_after_phase26_pass` | Phase 2.6 PASS 후에도 `audit_strategic_plan()` 실행 확인 (§5-I) |
| 13 | `test_pass_with_fix_reaches_finalizer_audit` | Phase 2.6 PASS_WITH_FIX → `stage2_finalizer` audit 도달 확인 (§5-J) |

---

## 9. 제약 사항

- **대원칙 3 준수**: Director가 선택 + 심사 동시 수행 → 주권 강화
- **대원칙 1 준수**: Python은 구조 필터만 (분량, 필수 필드), 서사 판단은 Director
- **`compare_and_select_arc()` 재사용**: 신규 메서드 불필요 — 이미 `director_ensemble.py` L324에 완비
- **Stage 3 변경 없음**: Stage 3는 이미 Director 비교 선택 구현 완료
- **InPlace 경로 유지**: PASS_WITH_FIX 시 Director가 선택한 Arc 기반 inplace patch

---

## 10. 리스크

| 리스크 | 대응 |
|--------|------|
| **L590 `if not best_arc` → 무한 retry** | `if not all_candidates:`로 변경 필수 — 미수정 시 Phase 2.5/2.6 절대 도달 불가 |
| `best_arc=None` 전파 — downstream NoneType 에러 | `four_phase_arc_generator` 내 모든 `best_arc` 참조 전수 점검 (§5 사이드이펙트 분석 완료) |
| Phase 2.5 auto-sanitize 순서 변경 | Director 선택 후 실행으로 이동 — 로직 불변, 위치만 변경 |
| SpareCandidate 동작 변경 | Director REJECT 시에만 spare 보존 — 기존보다 단순화 |
| `stage2_finalizer` 이중 심사 | **유지** (defense-in-depth, §5-I). P2 최적화 시 SC 경량화만 검토 |
| 3개 Arc 전문이 컨텍스트 초과 | tactical_doc 절삭 제거 → 전문 전달. 7화 Arc 3개 기준 ~15K자, Gemini 1M 컨텍스트 여유 충분 |

---

## 11. 코덱스 오더

### 전제
- `compare_and_select_arc()` 이미 완비 (director_ensemble.py L324-420+, 테스트 7개)
- Stage 3 `blueprint_ensemble.py` 패턴 참조

### 작업 순서

#### Step 1: `arc_ensemble.py` — Python 선택 제거 [P1]

**파일**: `modules/domain/agents/arc_ensemble.py`

1. `generate_ensemble()` 반환부 수정 (L373-410 근방):
   - `best = scored_candidates[0]` 제거
   - ※ 글자수 하드 필터는 L320-357에서 **이미 적용됨** — 추가 코드 불필요
   - **구조 점수 필터**: `STRUCTURAL_MIN_SCORE = 50` 상수 추가 → `_score >= 50` 후보만 통과
   - 최소 1개 보장: `if not valid: valid = scored_candidates[:1]`
   - 반환: `return None, valid`
   - 로깅: "Python은 선택하지 않음 — Director에게 전체 전달" (Stage 3 L318 패턴)

2. `_ensemble_meta` 보존 — `best_arc=None`이므로 `best["_ensemble_meta"]` 설정 불가
   - **변경**: 각 후보에 `_ensemble_meta`를 설정 (Stage 3 `blueprint_ensemble.py` L325 패턴)
   - `best_strategy` 키 제거, `candidate_index`/`strategy`/`score` 저장
   - **downstream 참조**: `stage2_orchestrator.py` L629, `four_phase_arc_generator.py` L631, `test_pass_with_fix.py` L1637 — `best_strategy` 키 사용중
   - **키 이름 주의**: Stage 3는 `_ensemble_meta.strategy`, Stage 2는 `_ensemble_meta.best_strategy` — 비일관이나 downstream 호환 유지 필요
   - **결론**: 이번 TF에서는 `best_strategy` 키 유지 (Stage 2/3 통일은 P2 후순위). 각 후보에 `_ensemble_meta = {"best_strategy": c.get("_strategy"), "score": c.get("_score"), ...}` 설정 → downstream `.get("best_strategy")` 호환 유지

#### Step 2: `four_phase_arc_generator.py` — `best_arc=None` 처리 [P1]

**파일**: `modules/domain/agents/four_phase_arc_generator.py`

1. **L560 반환값 소비**: `best_arc=None` 허용
2. **L579-583 SpareCandidate**: `best_arc=None`일 때 spare 보존 스킵 (Director가 선택 전이므로)
   ```python
   if best_arc is not None and all_candidates and len(all_candidates) > 1:
       for _c in all_candidates:
           if _c is not best_arc and _c not in _spare_candidates:
               _spare_candidates.append(_c)
   ```
3. **L587-588**: `if best_arc:` → `if all_candidates:`로 변경, 메시지 조정
4. **L590**: `if not best_arc:` → `if not all_candidates:` (생성 실패 판단) — **최우선 수정** (미수정 시 Phase 2.5/2.6 절대 도달 불가, 무한 retry)
5. **L598-626 ASP 블록**: Phase 2.6 **이전**에 유지 (§5-F 권장). `best_arc` → `all_candidates[0]`으로 대상 변경. `if retry >= 2 and adversarial_self_play and all_candidates:` 조건 + ASP 결과를 `all_candidates[0]`에 반영 → Director가 교정 후보를 비교 선택 (대원칙 3 준수)
6. **L631-637 EnsembleFB 블록**: `_current_strategy = best_arc.get(...)` + `pipeline_result["phases"]["generate"]` 기록 → Phase 2.6 **이전**에 있음 → **Phase 2.6 이후로 이동 필수** (best_arc=None → AttributeError 크래시). **주의**: Phase 2.6 PASS/PASS_WITH_FIX → 즉시 return(L691/L704)이므로, 이동 후 이 블록은 **Phase 3 Validator 폴백 경로에서만 실행**됨. Phase 2.6 PASS 경로에서 `pipeline_result["phases"]["generate"]` 키 미기록 → **L683-688 Director 선택 기록 직전에 EnsembleFB 기록도 추가** 필요 (또는 Phase 2.6 PASS return 직전에 삽입).
7. **L642 `_check_arc_end_state`**: advisory-only → Phase 2.6 이후로 이동. **이동 전 `if best_arc is None and all_candidates: best_arc = all_candidates[0]` 폴백 필수** (Director 스킵/예외 시 None 방지)
7b. **L644-654 `arc_start_state.location` 주입**: **mutative — Phase 2.6 이전 유지 필수** (모든 후보에 사전 적용). Phase 2.6 이후로 이동하면 Director PASS 조기 return(L691) 시 location 주입 누락 → TF-22-01 무력화. `best_arc` 대신 `for _cand in all_candidates:` 루프로 전 후보 적용.
8. **L657**: NS-3-B `_check_arc_vs_block_targets(best_arc, ...)` → Phase 2.6 이후로 이동 (auto-sanitize 폴백 이후이므로 best_arc 보장됨)

**블록 배치 순서 (Phase 2.5 → 2.6 → Validator 전)**:
```
# --- Phase 2.5 이전 (best_arc=None) ---

# (A) ASP — Phase 2.6 이전 유지 (§5-F 권장, 대원칙 3 준수)
if retry >= 2 and adversarial_self_play and all_candidates:
    _asp_input = json.dumps(all_candidates[0], ...)  # best_arc 대신 최고점 후보
    ...
    all_candidates[0] = _asp_arc  # 교정 결과를 후보에 반영

# (B) location 주입 — Phase 2.6 이전 유지 (mutative, 전 후보에 적용)
for _cand in all_candidates:
    _sc = _cand.setdefault("state_constraints", {})
    ...

# --- Phase 2.6 Director 선택 ---
if director and all_candidates:
    ...  # Director PASS → return (EnsembleFB 기록 포함)

# --- Phase 2.6 이후 (Validator 폴백 경로) ---

# (C) 폴백 — Director 미사용/예외 시 best_arc 보장
if best_arc is None and all_candidates:
    best_arc = all_candidates[0]

# (D) auto-sanitize — best_arc 필요 (advisory-only)
best_arc = self._check_arc_end_state(best_arc)

# (E) NS-3-B — best_arc 필요
_ns3b_warning = _check_arc_vs_block_targets(best_arc, curr_block, arc_no)

# (F) EnsembleFB — best_arc 필요 (_current_strategy 기록)
_current_strategy = best_arc.get("_ensemble_meta", {}).get("best_strategy", "unknown")
pipeline_result["phases"]["generate"] = {...}

# Phase 3 Validator
```
9. **L666-668**: Phase 2.6 조건 완화: `if director and all_candidates:` + `if _valid_for_director:`
10. **L706-724**: Director REJECT 시 SpareCandidate 보존 로직 조정

11. **L1032 Patch Mode**: `best_arc=None` 수신 후 `if not all_candidates:` → FAILED 반환
12. **L1055 이후**: `best_arc = all_candidates[0]` 폴백 추가 (Patch Mode는 Director 비교 없음, `single_strategy`로 1개만 생성)
13. **L1061, L1070**: `best_arc` 할당 이후이므로 변경 불필요

#### Step 2b: `director_ensemble.py` — tactical_doc 절삭 제거 [P1]

**파일**: `modules/domain/agents/director_ensemble.py`

1. L391 `tactical[:8000]` → `tactical` (절삭 제거)
   - Director가 선택 주체이므로 전문 비교 필요
   - 보조 필드 절삭(`sc_str[:1000]`, `joint_str[:1000]` 등)은 현행 유지

#### Step 3: `stage2_finalizer.py` — 변경 없음 (이중 심사 유지) [P2 후순위]

**TF-S2-E 조사 결론**: `audit_strategic_plan()`은 `compare_and_select_arc()`와 **보완적** 검사 수행 (entity검사, NC-1, SC투표, Contradiction Firewall). audit 유지가 defense-in-depth 보장.

**P2 최적화 (향후)**:
1. `run_finalize()` 시그니처에 `director_already_compared: bool = False` 인자 추가
2. True 시 SC 투표 횟수 경감 (3→1) 또는 `thinking_level` 하향 (medium→low)
3. **주의**: PASS_WITH_FIX 경로(§5-J)는 audit 유지 필수 — 스킵 시 InPlace 기회 소멸

#### Step 4: 기존 테스트 수정 [P1]

**Arc ensemble mock 반환값 변경** — `(best_arc, all)` → `(None, all)`:

| 파일 | 라인 | 현재 | 변경 |
|------|------|------|------|
| `test_four_phase_arc_generator.py` | L31 | `({"_ensemble_meta": ...}, [{}])` | `(None, [{"_ensemble_meta": ..., "tactical_doc": "..."}])` |
| `test_arc_patch_mode.py` | L54 | `(patched_arc, [patched_arc])` | `(None, [patched_arc])` |
| `test_arc_patch_mode.py` | L82 | `(None, [])` | 변경 없음 (이미 None) |
| `test_arc_patch_mode.py` | L107 | `(patched_arc, [patched_arc])` | `(None, [patched_arc])` |
| `test_arc_patch_mode.py` | L136 | `(patched_arc, [patched_arc])` | `(None, [patched_arc])` |

**실제 `generate_ensemble()` 호출 테스트** (mock 아닌 real call):

| 파일 | 라인 | 현재 | 변경 |
|------|------|------|------|
| `test_tier4_ensemble_caching.py` | L47-58 | `best, _ = agent.generate_ensemble(...)` + `assert best is not None` | `_, candidates = agent.generate_ensemble(...)` + `assert len(candidates) > 0` |
| `test_tf10_episode_details.py` | L75-106 | `best_arc` 변수 직접 사용 (ASP 단위 테스트) | `best_arc = all_candidates[0]` 폴백 추가 또는 mock 조정 |

**Stage 4 테스트**: `chief_writer.generate_ensemble` → `list[dict]` 반환 (tuple 아님) → **영향 없음**

#### Step 5: 신규 테스트 [P1]

**파일**: `tests/test_s2_director_select.py` (신규)

- §8 테스트 계획 13개 전량 구현
- 기존 `test_director_modules.py` TestDirectorArcComparison 7개 회귀 확인

### 검증 기준
- `pytest tests/ -q` 전량 PASS (기존 3,530+ 회귀 없음)
- `ruff check` 0 violations
- 실파이프라인에서 Stage 2 Arc 앙상블 → Director 비교 선택 로그 확인

### 주의 사항
- `compare_and_select_arc()` 신규 생성 불필요 — 이미 존재
- `director.yaml` 프롬프트 추가 불필요 — 이미 `compare_and_select_arc()` 내부에 프롬프트 구성
- auto-sanitize(`_check_arc_end_state`) / NS-3-B / EnsembleFB 블록은 Phase 2.6 **이후**로 이동. **ASP는 Phase 2.6 이전 유지** (§5-F, 대원칙 3 준수). 블록 배치 순서는 Step 2 참조.
- `_ensemble_meta.best_strategy` 참조하는 downstream 코드 전수 점검
