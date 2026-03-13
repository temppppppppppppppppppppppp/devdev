# S2D-T3: Preflight & State Management — 3pass Audit Findings

**감사 일자**: 2026-03-13
**트랙**: S2D-T3 (Stage 2 Deep Dive)
**대상 파일**:
- `modules/core/stage2_preflight.py`
- `modules/core/stage2_context.py`
- `modules/domain/agents/analyst.py`
- `modules/domain/agents/four_phase_arc_generator.py`
- `modules/domain/agents/arc_ensemble.py`
- `modules/domain/agents/unified_arc_validator.py`
- `modules/domain/agents/state_tracker.py`
- `modules/domain/agents/state_tracker_npc.py`
- `modules/domain/agents/preflight_checker.py`
- `modules/domain/agents/block_enricher.py`
- `modules/core/response_schemas.py`

---

## 요약 테이블

| Finding ID | 제목 | Severity | 판정 |
|---|---|---|---|
| S2D-T3-001 | response_schemas npc_deaths 스키마 타입 불일치 (STRING vs OBJECT) | P2 | 확정 |
| S2D-T3-002 | response_schemas에 skill_acquisitions 필드 누락 | P2 | 확정 |
| S2D-T3-003 | major_items 추출에 전용 extract 메서드 없음 (raw passthrough) | P3 | 확정 |
| S2D-T3-004 | cumulative_state_cache 키 비교 arc_count 기반 — 롤백 후 stale 위험 | P3 | 보류 |
| S2D-T3-005 | PreflightChecker.analyze()의 next_arc_guidance가 대원칙1 위반 가능성 | P3 | 오탐 |
| S2D-T3-006 | _build_genre_placeholders 10개 장르 정상 커버 확인 | -- | 오탐 |
| S2D-T3-007 | enriched_block FourPhaseArcGenerator에 직접 전달되지 않음 | P3 | 보류 |
| S2D-T3-008 | state_changes timeline.start/end 스키마가 STRING이지만 소비자는 dict 기대 | P2 | 확정 |

---

## 상세 Findings

### [S2D-T3-001] response_schemas npc_deaths 스키마 타입 불일치 (STRING vs OBJECT)

- **Severity**: P2
- **위치**: `modules/core/response_schemas.py:L414-417`
- **근거**:
```python
# response_schemas.py L414-417
"npc_deaths": types.Schema(
    type=types.Type.ARRAY,
    items=types.Schema(type=types.Type.STRING),   # ← STRING 배열
),
```
그런데 state_tracker_npc.py의 소비자(L672-710)는 dict 형태도 처리:
```python
# state_tracker_npc.py L679-683
for death in npc_deaths:
    if isinstance(death, dict):          # ← dict 분기 존재
        npc_name = death.get("name", "")
    elif isinstance(death, str):         # ← str도 처리
        npc_name = death
```
MEMORY.md의 state_changes 스키마 계약에는 `npc_deaths: [{name, episode, cause}]` (dict 배열)로 정의되어 있다. response_schemas의 Gemini 스키마가 STRING 배열로 되어 있어 LLM이 `["NPC이름"]` 형태로만 반환하게 강제되고, `episode`/`cause` 필드가 유실된다.

- **판정**: 확정
- **권장 조치**: response_schemas.py의 npc_deaths를 relationship_changes처럼 OBJECT 배열 (`{name, episode, cause}`)로 변경. 소비자 코드는 이미 양쪽 모두 처리하므로 하위 호환 무관.

---

### [S2D-T3-002] response_schemas에 skill_acquisitions 필드 누락

- **Severity**: P2
- **위치**: `modules/core/response_schemas.py:L378-430`
- **근거**: state_changes 스키마(L378-430)에 정의된 하위 필드:
  - `timeline` — 있음
  - `relationship_changes` — 있음
  - `major_items` — 있음
  - `npc_deaths` — 있음
  - `npc_introductions` — 있음
  - **`skill_acquisitions` — 없음**

MEMORY.md 계약 (`{name, episode, source}`)에 포함되어 있고, arc_ensemble.py L1000-1009의 ensure 로직에서 `skill_acquisitions: []`로 폴백하지만, Gemini structured output 스키마에 해당 필드가 없으므로 LLM이 자발적으로 생성하지 않는다. 결과적으로 항상 Python 폴백(빈 배열)이 사용되며, state_tracker_npc.py의 1순위 경로(L830-847)가 활성화되지 못하고 regex 폴백(L849-866)에 의존하게 된다.

- **판정**: 확정
- **권장 조치**: response_schemas.py state_changes에 `skill_acquisitions` OBJECT 배열 (`{name, episode, source}`)을 추가하여 LLM이 구조적으로 반환하도록 유도.

---

### [S2D-T3-003] major_items 추출에 전용 extract 메서드 없음 (raw passthrough)

- **Severity**: P3
- **위치**: `modules/domain/agents/state_tracker.py:L1600`
- **근거**:
```python
# state_tracker.py L1600
"major_items": (arc.get("state_changes") or {}).get("major_items", []),  # [V70] None 방어
```
npc_deaths, skill_acquisitions, relationship_changes는 각각 전용 `extract_*_from_arc` 메서드가 있어 state_changes 1순위 + regex 2순위 폴백 패턴을 구현한다. 반면 major_items는 raw passthrough만 존재하여:
  1. state_changes가 None/비어있으면 빈 리스트 반환 (regex 폴백 없음)
  2. 유효성 검증(name 필드 존재, 중복 제거 등)이 생략됨

item_state_registry 채워넣기는 `_populate_genre_registries_from_arc`(L1615-1625)에서 수행하지만, full_extract_from_arcs 호출 체인에서 major_items 전용 extract는 누락되어 있다.

- **판정**: 확정
- **권장 조치**: 향후 `extract_major_items_from_arc` 메서드를 만들어 regex 폴백 경로 추가 고려. 현재는 state_changes 스키마(response_schemas.py)에 major_items가 정의되어 있어 LLM 반환률이 높으므로 운영 영향은 낮음.

---

### [S2D-T3-004] cumulative_state_cache 키 비교 arc_count 기반 — 롤백 후 stale 위험

- **Severity**: P3
- **위치**: `modules/core/stage2_preflight.py:L700-716`
- **근거**:
```python
# stage2_preflight.py L700-716
arc_count = len(all_refined_arcs)
if (
    self.ctx.cumulative_state_cache is not None
    and self.ctx.cumulative_state_cache_key == arc_count
):
    state_result = self.ctx.cumulative_state_cache     # ← 캐시 히트
else:
    state_result = self.ctx.agents["state_extractor"].extract_cumulative_state(all_refined_arcs)
    self.ctx.cumulative_state_cache = state_result
    self.ctx.cumulative_state_cache_key = arc_count
```
캐시 키가 `len(all_refined_arcs)` (정수)다. 만약 Arc 5를 롤백하고 새 Arc 5를 생성하면, arc_count가 동일(5)하므로 이전 Arc 5의 cumulative_state가 반환될 수 있다.

단, main_a.py의 롤백 경로(L3232, L3262, L3295, L3334)에서 `_cumulative_state_cache = None` + `_cumulative_state_cache_key = None`으로 명시 초기화하고, sync_cache_key_to_app 콜백으로 app 레벨도 동기화하므로 실제 stale 발생은 방지된다.

- **판정**: 보류 — 현재 롤백 경로의 무효화가 모든 케이스를 커버하는지 확인 필요. 배치 내 중간 실패→동일 arc_count 재진입 시나리오는 미검증.

---

### [S2D-T3-005] PreflightChecker.analyze()의 next_arc_guidance가 대원칙1 위반 가능성

- **Severity**: P3
- **위치**: `modules/domain/agents/preflight_checker.py:L101-108`
- **근거**: PreflightChecker 프롬프트(L22-111)에 `next_arc_guidance` 섹션이 있어 LLM이 "recommended_focus", "potential_new_acquisitions" 등의 판단을 내린다.

그러나 이 결과는:
1. `_cached_preflight_result`로 저장되어 constraint_block에 주입됨 (stage2_preflight.py L597-609)
2. 최종 Arc 생성 자체는 ArcEnsembleGenerator가 수행
3. PreflightChecker 결과는 "advisory" 성격으로 LLM 에이전트(FourPhaseArcGenerator → ArcEnsemble)에 참고 컨텍스트로 전달

대원칙1은 "Python이 판단하면 안 된다"는 원칙이고, PreflightChecker는 LLM이 판단하는 것이므로 위반이 아님. injuries 값만 Python으로 arc_end_state에서 강제 덮어쓰지만(L600-607) 이는 "데이터 수집/포맷팅" 범주.

- **판정**: 오탐

---

### [S2D-T3-006] _build_genre_placeholders 10개 장르 정상 커버 확인

- **Severity**: --
- **위치**: `modules/domain/agents/analyst.py:L1714-1759`
- **근거**: `_build_genre_placeholders`는 `is_wuxia()` 분기로 무협/비무협을 나누고, 비무협은 `get_genre_label()` + `build_state_constraints_schema()`로 동적 생성한다.

`is_wuxia(genre)`: `genre in ("wuxia", "무협", "")` — 빈 문자열도 무협으로 처리 (하위 호환)

비무협 10개 장르(hunter, investment, fantasy, cooking, actor, sports, medical, alt_history, composer + romance): `genre_schema_builder.py`의 `_GENRE_LABELS`, `_GENRE_DESCRIPTIONS` 딕셔너리에 모두 등록됨. 미등록 장르는 `genre` 문자열 자체를 라벨로 사용하는 폴백이 있어 crash하지 않음.

`_GENRE_DETECT_MAP` (analyst.py L1672-1695): 10개 장르 + 한국어 별칭 모두 등록. `genre_library_map` (L1769-1780)도 10개 매핑 완비.

- **판정**: 오탐 — 모든 장르 정상 커버됨.

---

### [S2D-T3-007] enriched_block이 FourPhaseArcGenerator.generate()에 직접 전달되지 않음

- **Severity**: P3
- **위치**: `modules/domain/agents/four_phase_arc_generator.py:L515-531` (generate 시그니처)
- **근거**: `FourPhaseArcGenerator.generate()` 시그니처에는 `curr_block: dict`만 있고, `enriched_block`은 별도 파라미터로 존재하지 않는다. 오케스트레이터(stage2_orchestrator.py L539)에서 `enriched_batch[idx]` → `(source_arc_idx, enriched_block)`으로 풀어 쓰지만, 이 enriched_block은 `_preflight_arc_generation` 메서드(stage2_preflight.py)의 호출 체인에서 `curr_block` 파라미터로 전달된다.

stage2_orchestrator.py L623-627 확인:
```python
enriched_block=enriched_block,
```
이 값이 실제로 FourPhaseArcGenerator.generate()의 `curr_block`에 매핑되는 흐름을 추적하면, stage2_preflight.py의 `_preflight_arc_generation` 내부에서 `enriched_block`을 FourPhase에 `curr_block`으로 전달하는 것으로 확인됨. 별도의 "enriched_block" 파라미터가 없지만, curr_block 자체가 enriched_block이므로 데이터 손실은 없음.

- **판정**: 보류 — enriched_block의 `enrichment_metadata` 필드(added_npcs, added_locations 등)가 Arc 생성 프롬프트에서 활용되는지 추가 확인 필요. 현재는 curr_block 내 content 필드만 사용되고 enrichment_metadata는 소비되지 않을 가능성이 높음.

---

### [S2D-T3-008] state_changes timeline.start/end 스키마가 STRING이지만 소비자는 dict 기대

- **Severity**: P2
- **위치**: `modules/core/response_schemas.py:L382-387`, `modules/domain/agents/unified_arc_validator.py:L293-330`
- **근거**:
```python
# response_schemas.py L382-387
"timeline": types.Schema(
    type=types.Type.OBJECT,
    properties={
        "start": types.Schema(type=types.Type.STRING, description="Arc 시작 시점"),
        "end": types.Schema(type=types.Type.STRING, description="Arc 종료 시점"),
    },
),
```
Gemini 스키마에서 start/end는 STRING 타입이다. 그러나 arc_ensemble.py의 ensure 로직(L1013-1020)은:
```python
sc["timeline"] = {"start": {}, "end": {}}  # ← dict로 초기화
```
unified_arc_validator.py L296-330도:
```python
timeline = state_changes.get("timeline", {})
# ...
start = timeline.get("start", {})
end = timeline.get("end", {})
if not start or not isinstance(start, dict):   # ← dict 기대
```
LLM은 스키마에 따라 `"start": "2024년 3월"` (문자열)을 반환하지만, 소비자들은 `isinstance(start, dict)` 체크로 MINOR 이슈를 발행한다. 실질적 영향은 MINOR 이슈 노이즈 발생 + timeline 데이터 유실 수준이다.

- **판정**: 확정
- **권장 조치**: response_schemas.py의 timeline.start/end를 OBJECT로 변경하거나(`{year, month, day}`), 소비자 쪽에서 STRING 반환도 허용하도록 수정. 둘 중 하나 택일.

---

## 3pass 최종 정리

**확정 3건 (P2)**: S2D-T3-001, S2D-T3-002, S2D-T3-008 — response_schemas와 소비자 간 스키마 불일치. state_changes 구조적 필드의 핵심 가치(~98% 정확도)를 저해하는 요인.

**확정 1건 (P3)**: S2D-T3-003 — major_items regex 폴백 부재. 현재 운영 영향 낮음.

**보류 2건**: S2D-T3-004 (캐시 stale 시나리오 미검증), S2D-T3-007 (enrichment_metadata 소비 여부)

**오탐 2건**: S2D-T3-005, S2D-T3-006

**총평**: state_changes 계약의 핵심 설계(구조적 필드 우선 + regex 폴백)는 잘 구현되어 있으나, Gemini response_schemas(ARC_DESIGN_SCHEMA)가 MEMORY.md의 계약 스키마와 3곳에서 불일치한다. 특히 npc_deaths(STRING vs OBJECT)와 skill_acquisitions(필드 자체 누락)는 구조적 추출 경로의 활성화를 방해하여 regex 폴백 의존도를 높인다. 이는 state_changes 도입 시 ~70%→~98% 정확도 향상의 이득을 부분적으로 상쇄한다.
