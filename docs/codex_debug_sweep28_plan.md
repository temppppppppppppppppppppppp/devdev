# Debug Sweep 28 — 2-pass format 크래시 + LLM 타입 혼동 8건 + 리소스 누수 2건

## Context

Sweep 27(2건) 완료 후, 5-에이전트 병렬 탐색으로 새로운 패턴 탐색:
`.format()` KeyError, mutable default, 인코딩, isinstance 타입 혼동, 리소스 누수.
수동 코드 검증으로 **확인된 실제 버그 11건** 정리.
- mutable default: 0건 (전량 의도적 세션 캐시)
- 인코딩: 0건 (전량 `encoding="utf-8"` 명시)

---

## A-1 (CRITICAL): `analyst.py:747,785` — 2-pass format으로 PLAN_ARC_PROMPT_V25 전면 실패

**파일**: `modules/domain/agents/analyst.py:729,747,785` + `modules/domain/agents/analyst_prompt_api.py:44-45`

**문제**:
```python
# analyst_prompt_api.py:44-45
def get_plan_arc_prompt_v25(**kwargs) -> str:
    return _load_prompt("PLAN_ARC_PROMPT_V25", legacy.PLAN_ARC_PROMPT_V25, **kwargs)
    # → PromptLoader.load("analyst", "PLAN_ARC_PROMPT_V25", ep_count_suggestion="5")
    # → template.format_map(SafeDict(ep_count_suggestion="5"))
    # → {{  →  {  (Python 표준 format 이스케이프 해제)

# analyst.py:729
adjusted_prompt_tpl = get_plan_arc_prompt_v25(ep_count_suggestion=str(target_ep_count))
# ↑ 1차 pass 완료: YAML의 {{...}} JSON 예시 → {...} 베어 브레이스

# analyst.py:747 (캐시 경로) / 785 (폴백 경로)
prompt = adjusted_prompt_tpl.format(**cache_safe_data)
# ↑ 2차 pass: 베어 { 뒤에 줄바꿈/따옴표 → ValueError
```

**YAML 원본** (`analyst.yaml:357-363`):
```yaml
  {{
      "arc_no": "{arc_no}",
      "hybrid_composition": {{
```

**1차 SafeDict 후**:
```
  {
      "arc_no": "{arc_no}",
      "hybrid_composition": {
```

**2차 .format() 시**: `{` 뒤에 `\n    "arc_no": "` → 중첩 `{` → **ValueError: Single '{' encountered in format string**

→ `retry_with_feedback` 3회 재시도 전부 실패 → `(None, 3, False)` 반환
→ `final_arc_data = None` → `None["_actual_ep_count"]` → **TypeError** → Arc 생성 전면 실패

**수정** — 2단계:

**(1) `analyst_prompt_api.py:44-45`** — kwargs 없이 raw 템플릿 반환:
```python
def get_plan_arc_prompt_v25(**kwargs) -> str:
    """YAML raw 반환 (caller가 단일 pass format_map 수행)."""
    raw = _PROMPT_LOADER.get_raw("analyst", "PLAN_ARC_PROMPT_V25")
    if raw is not None:
        return raw
    # legacy 폴백: kwargs 있으면 SafeDict 적용
    if kwargs:
        try:
            class _SafeDict(dict):
                def __missing__(self, k): return "{" + k + "}"
            return legacy.PLAN_ARC_PROMPT_V25.format_map(_SafeDict(**kwargs))
        except Exception:
            return legacy.PLAN_ARC_PROMPT_V25
    return legacy.PLAN_ARC_PROMPT_V25
```

**(2) `analyst.py:695-712`** — `safe_data`에 `ep_count_suggestion` 추가:
```python
safe_data = {
    ...기존 키들...,
    "ep_count_suggestion": str(target_ep_count),  # ← 추가
}
```

**(3) `analyst.py:729`** — kwargs 제거:
```python
adjusted_prompt_tpl = get_plan_arc_prompt_v25()  # kwargs 없이 raw 반환
```

**(4) `analyst.py:747,785`** — `.format()` → `.format_map(SafeDict(...))`:
```python
class _SafeDict(dict):
    def __missing__(self, k):
        return "{" + k + "}"

# L747 (캐시 경로)
prompt = adjusted_prompt_tpl.format_map(_SafeDict(**cache_safe_data))

# L785 (폴백 경로)
prompt = adjusted_prompt_tpl.format_map(_SafeDict(**full_safe_data))
```

**원리**: Raw 템플릿은 `{{`/`}}`를 보존. 단일 `format_map` pass에서:
- `{{` → `{` (JSON 예시 정상 출력)
- `{arc_no}` → 값 치환
- `{unknown}` → SafeDict.__missing__으로 보존 (크래시 방지)

**테스트**: YAML 템플릿 로드 후 `format_map(SafeDict(**safe_data))` 호출 시 ValueError 없이 `{arc_no}` 치환 + JSON 예시 `{` 보존 검증

---

## B-1~B-4 (HIGH): `_parse_result()` — `json.loads` list 반환 시 `.get()` → AttributeError

4개 파일에서 동일 패턴: `json.loads()`가 JSON 배열(`[{...}]`) 반환 시 결과가 list → `.get()` 호출 크래시.

### B-1: `chain_of_verification.py:148-149`
```python
return json.loads(json_match.group(1))  # ← list 가능
# L235: result.get("issues", [])  ← AttributeError
```

### B-2: `cross_agent_verifier.py:145-147`
```python
return json.loads(json_match.group(1))  # ← list 가능
# L302,383: result.get("violations", [])  ← AttributeError
```

### B-3: `stage0/style_extractor.py:245,249`
```python
qualitative = self._deep_llm_analysis(drafts)  # json.loads → list 가능
anti = self._generate_anti_patterns(...)         # 같은 패턴
qualitative.update(anti)  # ← list에 .update() → AttributeError
```

### B-4: `stage0/story_expander.py:119,123`
```python
self.extracted = self._parse_json(self._call_llm(prompt)) or {}
# ↑ non-empty list는 truthy → or {} 미작동
self.genre = self.extracted.get("suggested_genre", "investment")  # ← AttributeError
```

**공통 수정** — `_parse_result` / 결과 수신 지점에 isinstance 가드:
```python
parsed = json.loads(text)
if isinstance(parsed, list):
    parsed = parsed[0] if parsed else {}
if not isinstance(parsed, dict):
    parsed = {fallback_dict}
return parsed
```

**수정 대상**:
| 파일 | 라인 | 수정 |
|------|------|------|
| `chain_of_verification.py` | 148-149 | `_parse_result` 내 isinstance 가드 |
| `cross_agent_verifier.py` | 145-147 | `_parse_result` 내 isinstance 가드 |
| `stage0/style_extractor.py` | 245 | `qualitative` 할당 후 isinstance 가드 (+ 249 `anti` 동일) |
| `stage0/story_expander.py` | 119 | `_parse_json` 결과에 isinstance 가드 |

**테스트**: `_parse_result("[{\"issues\": []}]")` 반환값이 dict인지 검증 (4건)

---

## B-5~B-8 (MEDIUM): LLM 필드 타입 불일치 — string/list 혼동 시 `.get()` on char → AttributeError

4개 파일에서 동일 패턴: LLM이 `"field": "none"` (string) 반환 시 → iterate chars → `.get()` on char 크래시.

### B-5: `consensus_validator.py:339,343`
```python
all_issues.extend(r.get("issues_found", []))  # "none" → extend chars
critical_issues = [i for i in all_issues if i.get("severity") == "CRITICAL"]  # 'n'.get() → crash
```

### B-6: `arc_critic.py:334`
```python
for issue in critique.get("critical_issues", []):  # "none" → iterate chars
    lines.append(f"🚨 [{issue.get('severity', 'HIGH')}] ...")  # 'n'.get() → crash
```

### B-7: `continuity_arc.py:413-429`
```python
violations = result.get("violations", [])  # "none detected" → iterate chars
v.get("type") in [...]  # 'n'.get() → crash
```

### B-8: `analyst.py:828-832`
```python
beats = draft_result.get("beat_sequence", [])  # string → len=문자수
beats[:N - 1] + [f"..."]  # str + list → TypeError
```

**공통 수정** — 필드 추출 직후 isinstance 가드:
```python
field = result.get("field_name", [])
if not isinstance(field, list):
    field = []
```

**수정 대상**:
| 파일 | 라인 | 필드 |
|------|------|------|
| `consensus_validator.py` | 339 전 | `issues_found`, `passed_checks` |
| `arc_critic.py` | 334 전 | `critical_issues` |
| `continuity_arc.py` | 413 | `violations` |
| `analyst.py` | 828 | `beat_sequence` |

**테스트**: 각 필드에 string 값 주입 시 크래시 없이 빈 리스트 폴백 검증 (4건)

---

## C-1 (LOW): `runtime_audit` 무제한 성장 — 장기 세션 메모리 누수

**파일**: `modules/core/services/audit_service.py:49`

**문제**:
```python
self._runtime_audit.append(event)  # 매 이벤트마다 추가, 제한 없음
```
- `_buffer`는 `flush_audit_buffer()` 후 초기화되지만 `_runtime_audit`는 영구 성장
- 200화 생성 시 수천 개 dict → 메모리 증가
- `write_audit_summary()`에서 `[-200:]`만 사용하지만 전체 리스트 유지

**수정**:
```python
self._runtime_audit.append(event)
if len(self._runtime_audit) > 1000:
    self._runtime_audit = self._runtime_audit[-500:]
```

---

## C-2 (LOW): `QualityDashboard` 4개 리스트 무제한 성장

**파일**: `modules/core/quality_dashboard.py:41-44`

**문제**:
```python
self.validation_history: list[dict] = []   # 매 에피소드 검증마다 추가
self.stage_stats[stage]["scores"].append()  # 매 점수마다 추가
self.hud_anomalies: list[dict] = []        # 매 이상 탐지마다 추가
self.blueprint_coverage: list[dict] = []   # 매 에피소드마다 추가
```
- `_load_metrics()`에서 전체 이력 파일 로드 → 시작 시 대량 메모리 사용
- 생성 진행 중 추가 성장, 제한 없음
- 비교: `validation_orchestrator.py`는 `_VALIDATION_HISTORY_MAX = 50`으로 제한

**수정** — `_process_record` 끝에 trim:
```python
_MAX_HISTORY = 500
if len(self.validation_history) > _MAX_HISTORY:
    self.validation_history = self.validation_history[-_MAX_HISTORY:]
if len(self.hud_anomalies) > _MAX_HISTORY:
    self.hud_anomalies = self.hud_anomalies[-_MAX_HISTORY:]
if len(self.blueprint_coverage) > _MAX_HISTORY:
    self.blueprint_coverage = self.blueprint_coverage[-_MAX_HISTORY:]
```

---

## 수정 파일 총괄

| # | 파일 | 변경량 |
|---|------|--------|
| A-1 | `modules/domain/agents/analyst_prompt_api.py` | 함수 리라이트 (~10줄) |
| A-1 | `modules/domain/agents/analyst.py` | 4곳 수정 (safe_data 키추가, kwargs 제거, format_map 전환) |
| B-1 | `modules/core/chain_of_verification.py` | `_parse_result` 가드 2줄 |
| B-2 | `modules/core/cross_agent_verifier.py` | `_parse_result` 가드 2줄 |
| B-3 | `modules/core/stage0/style_extractor.py` | isinstance 가드 2곳 각 2줄 |
| B-4 | `modules/core/stage0/story_expander.py` | isinstance 가드 2줄 |
| B-5 | `modules/domain/agents/consensus_validator.py` | isinstance 가드 2줄 |
| B-6 | `modules/domain/agents/arc_critic.py` | isinstance 가드 2줄 |
| B-7 | `modules/domain/agents/continuity_arc.py` | isinstance 가드 2줄 |
| B-8 | `modules/domain/agents/analyst.py` | isinstance 가드 2줄 |
| C-1 | `modules/core/services/audit_service.py` | trim 2줄 |
| C-2 | `modules/core/quality_dashboard.py` | trim 상수 + 4줄 |

**총 ~45줄 변경**

---

## 오탐 제거 기록

| 보고 | 실제 | 이유 |
|------|------|------|
| mutable default `def f(arg=[])` | ✗ 0건 | 전량 `arg=None` + `or []` 패턴 사용 |
| `BaseAgent._quota_exhausted_models = {}` | ✗ 설계 | 세션 전체 공유 의도. 주석 "세션 전체 공유" 명시 |
| `BaseAgent._api_keys = []` | ✗ 안전 | `cls._api_keys = keys` 재할당 (in-place 변이 아님) |
| `BaseAgent._context_caches = {}` | ✗ 설계 | 세션 캐시. `_CONTEXT_CACHE_MAX=50` 제한 |
| `MaterialDB._loaded_laws = {}` | ✗ 설계 | classmethod 전용, 인스턴스 없음 |
| 모든 `open()` 인코딩 누락 | ✗ 0건 | 209개 파일 전량 `encoding="utf-8"` 명시 |
| `chief_writer.py:677` patch 템플릿 format | ✗ 잠재 | 현재 YAML에 `{{` 없음. 잠재적 리스크만 (동작 정상) |
| `four_phase_arc_generator.py:433` 동일 | ✗ 잠재 | 동일 |
| `three_phase_blueprint_generator.py:360` 동일 | ✗ 잠재 | 동일 |
| `StateDeltaTracker.energy_history` | ✗ LOW | 에피소드 수 × 2~3 수준. 200화에서도 600건 미만 |
| `DBManager __del__` 미구현 | ✗ LOW | 정상 종료 경로에서 `close()` 호출. 크래시 시에만 리스크 |

---

## 검증

```bash
PYTHONIOENCODING=utf-8 python -m pytest tests/test_analyst.py tests/test_sweep28.py -q -x
PYTHONIOENCODING=utf-8 python -m pytest tests/ -q -p no:capture
```

## Sweep28 Execution Status (2026-02-18)

- Implementation: completed (A-1, B-1~B-8, C-1, C-2)
- Added tests: `tests/test_sweep28.py` (11 tests)
- Validation commands run:
  - `python -m pytest tests/test_sweep28.py -q -x` -> `11 passed`
  - `python -m pytest tests/test_audit_service.py tests/test_director_bias.py tests/test_quality_trend.py tests/test_quality_regression.py tests/test_stage01_helpers.py tests/test_sweep18.py -q -x` -> `67 passed`
  - `python -m pytest tests/ -q -p no:capture` -> `2020 passed, 68 xfailed, 1 warning`
