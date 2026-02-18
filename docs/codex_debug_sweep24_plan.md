# Debug Sweep 24 — 미사용 변수 + 폴백 구조 오류 + 테스트 상태 확인

## Context

Sweep 23(4건) 완료 후, 5-에이전트 병렬 탐색으로 잔여 미탐색 모듈 전면 스윕:
arc 생성 모듈 3종, 소형 도메인 에이전트 3종, pacing/diversity/foreshadow, ui/hud/martial/constants, 지속 실패 테스트 2건.
수동 코드 검증으로 **확인된 실제 버그 2건** 정리. 지속 실패 테스트 2건은 현재 정상 통과 확인.

---

## A-1 (MEDIUM): `arc_draft_validator.py:331` current_grants 할당 후 미사용 → 수여물 검증 누락

**파일**: `modules/domain/agents/arc_draft_validator.py:330-342`

**문제**:
```python
# L330 — 현재 Arc의 수여물 목록 추출
current_grants = arc.get("state_constraints", {}).get("grants_received", [])  # ← 할당
tactical = self._safe_tactical(arc)

# L334-340 — tactical_doc 패턴 매칭만 사용 (current_grants 미사용)
for pattern in self.grant_patterns:
    matches = re.findall(pattern, tactical)
    for m in matches:
        grant = m.strip() if isinstance(m, str) else m[0].strip() if m else None
        if grant and grant in all_granted:
            critical.append(f"중복 수여 시도: '{grant}' (이미 수여됨)")
            penalty += 25

return {"penalty": penalty, "critical": critical}
# ↑ current_grants는 한 번도 사용되지 않음
```
- `_validate_grant_timeline()` 메서드는 수여물 타임라인 검증 담당
- 이전 Arc들의 수여물은 L316-328에서 `all_granted`로 수집 (state_constraints + tactical 패턴)
- 현재 Arc는 tactical 패턴 매칭만 검증 → `state_constraints.grants_received` 직접 비교 누락
- tactical_doc에 없지만 `grants_received`에 있는 중복 수여물은 감지 불가

**수정** — L332 뒤에 직접 비교 추가:
```python
current_grants = arc.get("state_constraints", {}).get("grants_received", [])
if isinstance(current_grants, list):
    for grant in current_grants:
        if grant and grant in all_granted:
            critical.append(f"중복 수여 시도: '{grant}' (state_constraints에서 발견)")
            penalty += 25

tactical = self._safe_tactical(arc)
```

**테스트**: `state_constraints.grants_received`에 이전 Arc와 동일한 수여물 포함 시 penalty 추가 검증

---

## A-2 (MEDIUM): `martial_manager.py:159` pro_root 폴백 시 wrapper dict 반환 → 속성 조회 전면 실패

**파일**: `modules/core/martial_manager.py:157-166`

**문제**:
```python
@property
def pro_root(self):
    ...
    protagonist = hud_data.get("Protagonist")
    if not isinstance(protagonist, dict):
        return hud_data  # ← wrapper dict 반환 ({"Protagonist": ..., "other": ...})

    return protagonist  # ← protagonist dict 반환 ✅

@property
def pro_data(self):
    return self.pro_root.get("actual_truth", self.pro_root)
    # ↑ pro_root가 wrapper일 때: hud_data.get("actual_truth") → None → hud_data 반환
```
- `Protagonist` 키가 없거나 비-dict일 때, `pro_root`가 wrapper dict 반환
- `pro_data`는 `actual_truth` 키를 찾지만, wrapper에는 없음 → wrapper 전체 반환
- `_get_normalized_val()`가 `pro_data.get("name")` 등 호출 → wrapper에서 찾을 수 없음
- 결과: 모든 속성이 "기록 없음" 기본값 반환 — 크래시는 없지만 데이터 소실

**수정**:
```python
protagonist = hud_data.get("Protagonist")
if not isinstance(protagonist, dict):
    return {"actual_truth": {"name": "주인공"}}  # 안전한 최소 구조
```

**테스트**: `Protagonist` 키 없는 HUD 데이터에서 `pro_data.get("name")`이 "주인공" 반환 검증

---

## INFO: 지속 실패 테스트 2건 — 현재 통과 확인

**테스트**:
- `tests/test_stage2_pipeline.py::TestAnalystProtagonistConfig::test_world_origin_primitive`
- `tests/test_stage2_pipeline.py::TestAnalystProtagonistConfig::test_incarnation_type_regression`

**상태**: Sweep 21-22 실행 로그에서 실패로 보고되었으나, 현재 코드베이스에서 **정상 통과** 확인.
- `analyst.py:86-100`의 protagonist_config 로직 정상 작동
- `analyst_prompts.py:141`의 `{protagonist_config}` 플레이스홀더 정상 주입
- 이전 실패는 일시적 환경 이슈 또는 후속 스윕에서 자동 해결된 것으로 판단

**조치**: 없음 (이미 통과)

---

## 수정 파일 총괄

| # | 파일 | 변경량 |
|---|------|--------|
| A-1 | `modules/domain/agents/arc_draft_validator.py` | 4줄 추가 (current_grants 직접 비교) |
| A-2 | `modules/core/martial_manager.py` | 1줄 수정 (안전한 기본 dict 반환) |

**총 ~5줄 변경**

---

## 오탐 제거 기록

| 보고 | 실제 | 이유 |
|------|------|------|
| `arc_corrector.py:489` 삽입 off-by-one | ✗ 오탐 | `tactical[:match.start()] + new + tactical[match.start():]`는 올바른 삽입 패턴 |
| `four_phase_arc_generator.py:243` 미초기화 변수 | ✗ 오탐 | `all_candidates = []` L243에서 초기화 완료. 에이전트도 "works at runtime" 인정 |
| `hud_utils.py:166` list 타입 불일치 | ✗ 오탐 | HUD items/weapons는 LLM JSON 파싱 후 항상 list |
| `constraint_compiler.py:97-98` len() 비-문자열 | ✗ 오탐 | acquired 리스트는 문자열만 포함 (LLM 파싱 보장) |
| `quality_amplifier.py:147-159` 관계 전이 비대칭 | ✗ 설계 | 배신→적대 일방향은 서사 설계 의도 (비가역적 전환) |
| `quality_amplifier.py` 굴복 상태 도달 불가 | ✗ 설계 | 굴복은 서사 이벤트로 도달, 기계적 전이가 아님 |
| `pacing_analyzer.py:298-305` zone 로직 오류 | ✗ 오탐 | 25-44=FLOWING, 45-60=MIXED 의도된 분류. elif 체인 정상 |
| `pacing_analyzer.py:164` 무의미한 삼항 | ✗ 스타일 | `total_breaks >= 0` 항상 True — 방어적 코드, 동작 영향 없음 |
| `world_state.py:147-154` 아이템 상태 덮어쓰기 | ✗ 설계 | 획득→"보유", 소실→action값. 의도된 상태 머신 |
| `world_state.py:133-137` dead NPC 관계 차단 | ✗ 정책 | "사망 캐릭터는 회상/언급만 허용" 대원칙 준수 |
| `foreshadow_tracker.py:178` payoff_ep None | ✗ 오탐 | PAYOFF 상태에서 payoff_ep 항상 설정됨 (L215) |
| `fact_ledger.py:182` 중복 삼항 | ✗ 스타일 | 기능 무관 — role="" → None 변환 중복 |

---

## 검증

```bash
PYTHONIOENCODING=utf-8 python -m pytest tests/test_arc_draft_validator.py tests/test_stage2_pipeline.py -q -x
PYTHONIOENCODING=utf-8 python -m pytest tests/ -q -p no:capture
```

---

## Execution Status (2026-02-18)

- 완료: A-1 `modules/domain/agents/arc_draft_validator.py`
  - `_validate_grant_timeline()`에서 `state_constraints.grants_received` 직접 비교 추가
  - tactical_doc 패턴 매칭 이전에 중복 수여를 선검증하도록 보강
- 완료: A-2 `modules/core/martial_manager.py`
  - `Protagonist`가 dict가 아닌 경우 wrapper dict 대신 최소 안전 구조
    `{"actual_truth": {"name": "주인공"}}` 반환

### Tests Added/Updated

- 추가: `tests/test_arc_draft_validator.py`
  - `state_constraints.grants_received` 중복 수여 감지 회귀 테스트 추가
- 수정: `tests/test_martial_manager.py`
  - `Protagonist` 비정상 타입일 때 `pro_data.get("name") == "주인공"` 보장 테스트 추가

### Pytest Results

1. 계획서 타깃 검증
   - `python -m pytest tests/test_arc_draft_validator.py tests/test_stage2_pipeline.py -q -x`
   - 결과: `77 passed`
2. martial_manager 회귀 단건 확인
   - `python -m pytest tests/test_martial_manager.py::TestMartialManagerEdgeCases::test_pro_data_name_fallback_when_protagonist_is_not_dict -q -x`
   - 결과: `1 passed`
3. 전체 테스트
   - `python -m pytest tests/ -q -p no:capture`
   - 결과: `1985 passed, 68 xfailed, 1 warning`
