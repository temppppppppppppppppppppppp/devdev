# TF Runtime Diagnosis — Stage 3 Blueprint 4연속 REJECT 원인 분석

> 날짜: 2026-02-25
> 로그: 투자물 25화 Arc, 1화에서 4회 REJECT → 5회차 PASS, 6화에서 3회 REJECT 후 수동 중단
> 총 비용: $1.08 / 296K tokens / 25분

---

## TF-1: Constitutional AI `deadline 1s` API 타임아웃

### 위치
`modules/validation/scoring_validator.py` L255-259

### 코드
```python
timeout_seconds = int(_threshold("retry.api_timeout_seconds", 300))
config = types.GenerateContentConfig(
    temperature=0.3,
    response_mime_type="application/json",
    http_options=types.HttpOptions(timeout=max(1, timeout_seconds)),
)
```

### 원인
- `_threshold("retry.api_timeout_seconds", 300)` → config에서 300 반환 (정상)
- **그런데 로그에 1초 에러 발생** → config 오버라이드 또는 런타임에서 다른 값이 들어옴
- `max(1, ...)` 패턴이 Gemini 최소 10초 제한을 위반
- 대조: `base_agent.py` L265-273은 `if timeout <= 0: return None` 패턴 (안전)

### 영향
- Constitutional AI 평가 **매번 실패** → `_fallback_llm_scores()` 휴리스틱으로 전환
- 휴리스틱: 길이 기반 추정, 구두점 카운팅, 인용부호 기반 — LLM 평가 대비 품질 저하
- 코드베이스 전체에서 `HttpOptions(timeout=)` 사용처: **딱 2곳** (scoring_validator, base_agent)

### 심각도: P1
- config가 300이면 실제로 이 에러가 발생할 수 없음
- **추가 확인 필요**: 런타임에서 `_threshold` 해석이 달라지는 경로가 있는지, 또는 config 파일이 세션 중 변경되었는지

---

## TF-2: REJECT 피드백 미전달 (핵심 — P0)

### 위치
`modules/domain/agents/three_phase_blueprint_generator.py`

### 피드백 변수 5개 — 전체 맵

| 변수 | 선언 | 역할 | 스코프 |
|------|------|------|--------|
| `feedback` | L123 | 메인 피드백 누적기 — ensemble에 매 retry 전달 | 모듈 레벨 |
| `_initial_feedback` | L157 | **초기값 보존** — retry간 누적 방지용 | retry 루프 |
| `_attempt_feedback` | L161 | **per-retry 피드백** — `_initial_feedback` + `_strategy_feedback` | retry 루프 |
| `_strategy_feedback` | L162 | `_build_strategy_feedback()` 산출물 | retry 루프 |
| `_prev_reject_feedback` | L136 | **REJECT 시 캡처** — Director/validator 피드백 저장 | 모듈 레벨 |

### 피드백 흐름 (현재)

```
Director REJECT
  ↓
L393: feedback = validation_result.get("feedback")    ← Director 피드백 캡처
L396: _prev_reject_feedback = feedback                ← 변수에 저장
L403: _prev_selection_reason = validation_result.get("summary") or ...("comparison_notes") or ...("feedback")
  ↓
[다음 retry]
L161: _attempt_feedback = _initial_feedback           ← ⚠️ 리셋! Director 피드백 소실
L162: _strategy_feedback = _build_strategy_feedback()  ← _prev_selection_reason + score + warnings
L164: _attempt_feedback = _initial_feedback + _strategy_feedback
  ↓
L222: ensemble.generate_ensemble(feedback=_attempt_feedback, strategy_specific_feedback=_strategy_feedback)
```

### 버그 3중 구조

**1. `_prev_reject_feedback` 고아 변수 (L396)**
- Director 피드백이 `_prev_reject_feedback`에 저장됨
- **`_build_strategy_feedback()`는 이 변수를 참조하지 않음** (L142-155)
- `_prev_selection_reason`에 fallback으로 들어갈 수 있지만, `summary`나 `comparison_notes`가 있으면 `feedback`은 무시됨

**2. `_attempt_feedback` 매 retry 리셋 (L161)**
- `_attempt_feedback = _initial_feedback` — 매번 초기값으로 리셋
- Director가 "아버지 독대 직후 시작해야"라고 해도, 다음 retry에서 이 피드백은 `_initial_feedback`에 없으므로 소실
- `_strategy_feedback`에 부분적으로 들어가지만 불완전

**3. `_strategy_feedback` 구성 불완전 (L142-155)**
```python
def _build_strategy_feedback() -> str:
    _parts = []
    if _prev_selection_reason:       # ← summary/comparison_notes 우선, feedback은 3순위 fallback
        _parts.append(f"[이전 선택/거절 사유]\n{_prev_selection_reason}")
    if _prev_score_breakdown:        # ← 숫자 점수
        _parts.append(...)
    if _prev_validation_warnings:    # ← 검증 경고 리스트
        _parts.append(...)
    return "\n\n".join(_parts)
```
- `_prev_reject_feedback` **직접 참조 없음**
- `_prev_selection_reason`이 Director의 `reason` (짧은 요약)을 가져오면, 상세 `feedback`은 누락

### Ensemble 내 피드백 수신 경로 (확인됨 — 여기는 정상)

`blueprint_ensemble.py` L352-371:
```python
_merged_feedback = feedback or ""
if strategy_feedback:
    _merged_feedback = f"{_merged_feedback}\n\n[전략별 보정 피드백]\n{strategy_feedback}"
if _merged_feedback:
    extra_directive = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 [CRITICAL] Director REJECT 피드백 - 이전 시도 실패 원인
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{_merged_feedback}
"""
```
→ 피드백이 `_attempt_feedback`에 제대로 들어오면, LLM 프롬프트까지는 정상 전달됨

### 전략별 피드백 분배 (L214-219)
```python
if strategy.get("name") == rejected_strategy and strategy_specific_feedback:
    _strategy_feedback = strategy_specific_feedback     # rejected 전략만 상세 피드백
elif strategy_specific_feedback:
    _strategy_feedback = f"[이전 시도 문제 요약]\n{strategy_specific_feedback}"  # 나머지는 요약
```
→ 3개 전략 모두 피드백 받지만, rejected 전략이 가장 상세

### 연속성 REJECT 경로 (L308-326) — 이건 정상
```python
if continuity_result.get("decision") == "REJECT":
    _prev_reject_feedback = continuity_feedback
    _prev_selection_reason = continuity_feedback      # ← 직접 대입
    _prev_validation_warnings = [continuity_feedback] # ← 직접 대입
```
→ 연속성 피드백은 3개 변수에 모두 직접 대입 — `_build_strategy_feedback()`에서 정상 전달

### 결론
- **Director comparison 피드백만 누락** — `compare_and_select_blueprint()` → `unified_blueprint_validator` → `three_phase_blueprint_generator` 경로에서 `feedback` 필드가 `_strategy_feedback`에 불완전하게 전달
- **연속성 피드백은 정상** — 직접 대입 패턴
- **근본 원인**: `_build_strategy_feedback()`가 `_prev_reject_feedback`를 참조하지 않음

---

## TF-3: `reputation: 0` BLOCKING 오발동

### 위치
`modules/validation/blocking_validator_consistency_checks.py` L155-167

### 코드
```python
reputation = actual_truth.get("reputation", 0)       # ← 기본값: 0 (int)
try:
    reputation = int(reputation) if not isinstance(reputation, int | float) else reputation
except (ValueError, TypeError):
    reputation = 0                                    # ← dict → int 변환 실패 → 0

has_low_reputation = reputation < 20                  # ← 0 < 20 = True → BLOCKING
```

### 타입 충돌 — 근본 원인

| 소스 | 타입 | 값 |
|------|------|-----|
| `preset_registry.py` COMMON_PRESET L36 | `dict` | `{}` |
| `preset_registry.py` Composer L117 | `dict` | `{"public": 0, "industry": 0, "critic": 0}` |
| `preset_registry.py` Investment L43-61 | (상속) | `{}` (COMMON에서 상속) |
| **blocking_validator L155** | **`int` 기대** | `int(dict)` → ValueError → 0 |

### 장르별 영향

| 장르 | reputation 타입 | `int()` 변환 | `< 20` 결과 | BLOCKING |
|------|----------------|-------------|-------------|----------|
| 무협 | int (직접 설정) | 성공 | 값에 따라 | 정상 |
| 투자 | dict `{}` (상속) | ValueError→0 | True | **오발동** |
| 작곡 | dict `{...}` (프리셋) | ValueError→0 | True | **오발동** |
| 요리 | `reputation_score` (int) | 성공 | 값에 따라 | 정상 |
| 헌터 | 미정 | ? | ? | ? |

### BLOCKING 체인
```
blocking_validator.py L118-126:
  authority_check = self._check_authority_exercise(manuscript, validation_context)
  if not authority_check["passed"]:
      failures.append(authority_check)        # ← BLOCKING 실패 목록에 추가

L140-143:
  "passed": len(failures) == 0               # ← 1건이라도 있으면 REJECT
```

### 4개 consistency check 메서드
1. `_check_physical_capability()` L28-133 — 약한 육체 + 강한 행동
2. **`_check_authority_exercise()` L135-238 — reputation 사용 ← 여기**
3. `_check_relationship_consistency()` L240-295 — NPC 관계 역전
4. `_check_information_consistency()` L297+ — NPC 지식 일관성

### 결론
- reputation 필드의 **정의(dict)와 소비(int)가 불일치**
- "진짜 낮은 평판" vs "필드 미초기화/타입 불일치" 구분 불가
- 투자물·작곡가 장르에서 **정상 원고가 점수 0으로 REJECT**

---

## TF-4: Blueprint 검증에 NPC/HUD 컨텍스트 미주입

### 위치
`modules/domain/agents/unified_blueprint_validator.py` L243

### 코드
```python
director_result = director.audit_manuscript(
    ...
    validation_context={"skip_continuity": True},  # ← 이것만 전달
)
```

### Stage 4 대비 (정상 구현)
`modules/core/stage4_interview_round.py` L275-340:
```python
_cv_context = {
    "mode": "MANUSCRIPT",
    "martial_hud": {},
    "npc_profiles": {},
    "prev_episode_events": [],
    ...
}

# prev_hud 주입 (L286-299)
if next_ep > 1:
    _prev_hud = self.ctx.sys.hud.pro_root
_cv_context["prev_hud"] = _prev_hud
_cv_context["martial_hud"] = _prev_hud

# encyclopedia 주입 (L310-322)
_encyclopedia_npcs = []
if self.ctx.state_tracker:
    for _npc_name, _npc_info in getattr(self.ctx.state_tracker, "npc_registry", {}).items():
        _encyclopedia_npcs.append({...})
_cv_context["encyclopedia"] = {"npcs": _encyclopedia_npcs}
```

### 미주입 필드 3개

| 필드 | Stage 4 | Blueprint (현재) | 영향 |
|------|---------|-----------------|------|
| `prev_hud` | `sys.hud.pro_root` | 없음 | ContinuityValidator DEGRADED (경고만, skip_continuity=True라 PASS) |
| `encyclopedia.npcs` | `state_tracker.npc_registry` | 없음 | NPC 일관성 검증 무력화 |
| `npc_profiles` | `master_bible.AssetLibrary.KeyNPCs` | 없음 | NPC 프로필 검증 스킵 |

### Validator 반응

**ContinuityValidator** (continuity_validator.py L108-138):
```python
if not prev_hud:
    skip = validation_context.get("skip_continuity", False)
    # skip_continuity=True → PASS (Blueprint 모드)
    return {"passed": bool(skip), "degraded": True, ...}
```
→ Blueprint 모드에서는 **PASS 반환** (경고만 로그)

**V0128 Orchestrator** (director_auditor.py L224-231):
```python
_encyclopedia = validation_context.get("encyclopedia") or {}
_npcs = _encyclopedia.get("npcs") or {}
_degraded = not bool(_npcs)
if _degraded:
    logging.warning("[V0128] encyclopedia.npcs 누락 — NPC 일관성 검증 DEGRADED.")
```
→ 경고만 로그, **계속 진행** (degraded 모드)

### 접근 가능한 리소스 확인

`three_phase_blueprint_generator.py` L57-75 파라미터:
- `state_tracker=None` → **전달받음** (L70)
- `db=None` → **전달받음**
- `director=None` → **전달받음**

**UnifiedBlueprintValidator** 인스턴스도 state_tracker를 받음 (L338)
→ 리소스는 있는데 validation_context 구축에 사용하지 않는 것

### ep 1 경고는 정상
- ep 1은 이전 데이터 없음 → prev_hud 누락은 당연
- ContinuityValidator L96-105: `if current_ep <= 1: return PASS`

### ep 6 경고는 버그
- 5화분 HUD 데이터 존재
- state_tracker.npc_registry에 NPC 데이터 존재
- **validation_context에 주입하지 않아서 미전달**

---

## 종합 판정

| TF | 심각도 | 수정 복잡도 | 효과 |
|----|--------|-----------|------|
| TF-1 | P1 | 1줄 (`max(1,...)` → `max(10,...)`) | Constitutional AI 정상 작동 |
| TF-2 | **P0** | 중간 (`_build_strategy_feedback`에 `_prev_reject_feedback` 추가) | REJECT 피드백 전달 → 재시도 성공률 향상 |
| TF-3 | **P0** | 중간 (reputation 타입 정규화 또는 validator 방어) | 투자물·작곡가 오발동 제거 |
| TF-4 | P1 | 중간 (Stage 4 패턴 복제 → unified_blueprint_validator) | NPC/HUD 검증 정상화 |

### 의존성
- TF-3과 TF-4는 독립
- TF-2가 해결되면 REJECT 재시도 감소 → TF-1/3/4 영향도 줄어듦
- TF-4는 TF-3의 영향을 증폭시킴 (martial_hud 미주입 → reputation 더 자주 0)
