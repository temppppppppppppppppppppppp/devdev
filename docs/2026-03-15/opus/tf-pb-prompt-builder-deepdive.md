<!-- [참고자료] -->
# TF-PB: PromptBuilder 딥다이브

| Field | Value |
|-------|-------|
| Baseline | bbb00a77 |
| Date | 2026-03-15 |
| Scope | PromptBuilder: context assembly, item timeline cache, tactical extraction, genre branching, NPC injection, prompt size, error handling |
| Source files | `modules/core/prompt_builder.py` (969줄), `modules/core/tactical_utils.py` (73줄), `modules/core/arc_state_utils.py` (104줄) |
| TF Items | 14 (CRITICAL 2 / IMPORTANT 7 / INSIGHT 5) |

---

## 1. Executive Summary

PromptBuilder는 SovereignApp에서 분리된 15개 프롬프트 생성/컨텍스트 조립 메서드를 캡슐화한다. 전체적으로 방어적 코딩이 잘 되어 있으나, 다음의 구조적 문제가 발견되었다:

1. **`state_constraints` 변수 섀도잉** (CRITICAL): `generate_arc_context_fallback`에서 loop 내부 변수가 외부 변수를 덮어써 `arc_end_state`가 항상 마지막 아크가 아닌 루프 마지막 아크의 것을 사용하게 되는 버그.
2. **`build_validation_context`에서 `app=None` 시 `AttributeError` 크래시** (CRITICAL): `app.sys` 접근이 None guard 없이 수행됨.
3. **`generate_v50_writer_prompt` 및 `generate_self_diagnosis_checklist` Dead Code** (IMPORTANT): 호출 경로가 완전히 끊어졌으나 968줄 중 ~70줄을 차지.
4. **`_decorate_arc_context_for_target`에서 `current_arc_no=0` 시 falsy 판정** (IMPORTANT): Arc #0은 유효하지 않지만, 방어적으로 명시적 `is None` 비교가 더 안전.
5. **NPC 프로필 추출에서 substring false-positive** (IMPORTANT): `json.dumps` 후 `in` 연산자는 NPC 이름이 다른 문자열의 부분문자열일 때 오탐.
6. **`generate_cliche_avoidance_guide`에서 `cliche_check_result` 매개변수 미사용** (IMPORTANT): 선언만 있고 함수 본문에서 사용되지 않음.

---

## 2. Architecture / Data Flow Diagram (ASCII)

```
                         +------------------+
                         |   SovereignApp   |
                         |   (main_a.py)    |
                         +--------+---------+
                                  |
                  self._prompt_builder = PromptBuilder(app=self)
                                  |
                                  v
                    +-------------+---------------+
                    |        PromptBuilder         |
                    |   (prompt_builder.py:969줄)  |
                    +----+-------+--------+-------+
                         |       |        |
          +--------------+   +---+----+   +-------------+
          |                  |        |                  |
  Pure Methods (8)    Arc Context (2) | V50 Plugin (2)  Validation/NPC (3)
  (no app ref)        (app-dep)       | (DEAD CODE)     (app-dep)
          |                  |        |                  |
          v                  v        v                  v
  +----------------+  +----------+  +--------+  +---------------+
  |arc_position    |  |v60 ctx   |  |v50     |  |validation_ctx |
  |high_impact_zone|  |fallback  |  |self_dx |  |npc_profiles   |
  |npc_relationship|  |          |  |        |  |char_traits    |
  |item_timeline   |  +----+-----+  +--------+  +-------+-------+
  |temporal_spatial|       |                             |
  |cliche_avoidance|       v                             v
  |writer_guidance |  StateExtractor             MasterBible/DB
  |self_diagnosis  |  + _cumulative_                     |
  +-------+--------+    state_cache              +-----------+
          |              (app attr)              |AssetLibrary|
          v                   |                  |KeyNPCs     |
  Stage4ContextBuilder        v                  +-----------+
  (context_builder.py)   compute_terminal_
  L2622: writer_guidance  arc_state()
  L1959: item_timeline    (arc_state_utils)
                               |
                               v
                         extract_episode_
                         tactical()
                         (tactical_utils)

  Cache Layer:
  +----------------------------------------------+
  | _item_timeline_cache: dict                   |
  | {up_to_ep: [timeline_lines]}                 |
  | LRU size=3, invalidated on reset/rewind/     |
  | rollback/wipe (4 call sites in main_a.py)    |
  +----------------------------------------------+
  | _cumulative_state_cache: on app object       |
  | keyed by arc_count (len(all_refined_arcs))   |
  | invalidated on reset/rewind/rollback/wipe    |
  +----------------------------------------------+
```

---

## 3. TF Items

### TF-PB-01: `state_constraints` 변수 섀도잉 — arc_end_state 소실 위험 — CRITICAL

- **Location**: `prompt_builder.py:L613-L624`
- **Description**: `generate_arc_context_fallback`에서 L613에서 `state_constraints = last_arc.get("state_constraints", {})`를 설정하고 L614에서 `arc_end_state = state_constraints.get("arc_end_state", {})`를 추출한다. 그러나 L621-624의 `for prev_arc in all_refined_arcs:` 루프 안에서 `state_constraints = prev_arc.get("state_constraints", {})`로 동일한 변수명을 재할당한다. 이 자체는 `arc_end_state`가 이미 L614에서 추출된 후이므로 현재 코드에서는 직접적인 데이터 손실이 없다. 그러나 **`arc_end_state`는 루프 전에 이미 추출되었으므로 실제 동작은 정확하다.** 다만, 이 패턴은 유지보수 시 혼동을 유발할 수 있으며, 코드를 읽는 개발자가 `arc_end_state`가 루프 후 변경된 `state_constraints`에서 온 것으로 오해할 수 있다.
- **Evidence**:
```python
# L613-614: 루프 전
state_constraints = last_arc.get("state_constraints", {})
arc_end_state = state_constraints.get("arc_end_state", {})

# L624: 루프 내부에서 같은 이름 재할당
state_constraints = prev_arc.get("state_constraints", {})
```
- **Impact**: 현재 동작은 정확하나, **`arc_end_state`가 실제로 함수 반환값에 사용되지 않는다** — L659의 `compute_terminal_arc_state()`가 대신 사용되며, L613-614의 `arc_end_state`는 Dead 변수다. 이 Dead 변수와 섀도잉이 결합되어 유지보수 함정을 만든다.
- **Suggested fix direction**: L613-614의 `state_constraints`/`arc_end_state` 할당을 제거하거나, 루프 내 변수를 `prev_state_constraints`로 리네임.
- **Severity reassessment**: 재검토 결과, `arc_end_state`가 실제로 사용되지 않으므로 **IMPORTANT** (Dead 변수)로 하향. 하지만 L679의 `joint_docs`, L680의 `status_shadow`는 L611-612에서 `last_arc`로부터 올바르게 추출되어 실제 사용됨.

**최종 판정: IMPORTANT** (Dead 변수 + 섀도잉 혼동)

---

### TF-PB-02: `build_validation_context`에서 `app=None` 시 `AttributeError` 크래시 — CRITICAL

- **Location**: `prompt_builder.py:L881-L885`
- **Description**: L882에서 `app = self._app`을 할당한 후, L885에서 `hasattr(app.sys, "lore")`를 호출한다. `self._app`이 `None`이면 `app.sys`에서 `AttributeError`가 발생한다. 이 에러는 L921의 `except Exception`으로 잡히므로 크래시는 방지되지만, **`app=None`일 때 step 1-5 전체가 skip되어 빈 context만 반환된다.** 이것은 의도된 동작일 수 있지만, `app`의 존재를 먼저 확인하지 않고 `app.sys`에 접근하는 것은 위험하다.
- **Evidence**:
```python
try:
    app = self._app  # None 가능

    # 1. Encyclopedia 구성
    if hasattr(app.sys, "lore") and app.sys.lore:  # app=None이면 AttributeError
```
- **Impact**: `app=None`이면 L885에서 `AttributeError`가 발생하여 L921의 except로 점프. Step 1-5 전체가 skip되며 빈 context dict가 반환된다. `except` 블록 안에서 `app`을 참조하므로(L923 `if app and ...`) 이중 방어가 있긴 하지만, 정상적으로 `build_validation_context`가 `app=None`인 PromptBuilder에서 호출되는 경로는 없다 (StateService를 통해서만 호출되며, StateService는 항상 app-bound PromptBuilder 사용). 따라서 **실제 크래시 위험은 낮다.**
- **Suggested fix direction**: 함수 초입에 `if not self._app: return context` 가드 추가.

**최종 판정: IMPORTANT** (이론적 크래시, 실제 호출 경로에서는 미발생)

---

### TF-PB-03: `generate_v50_writer_prompt` + `generate_self_diagnosis_checklist` Dead Code — IMPORTANT

- **Location**: `prompt_builder.py:L701-L765` (generate_v50_writer_prompt), `prompt_builder.py:L527-L544` (generate_self_diagnosis_checklist)
- **Description**: `main_a.py:L2420`에 `# [V65] _generate_v50_writer_prompt 삭제 — Stage 4 V2 파이프라인에서 미호출 Dead Code`로 명시되어 있다. PromptBuilder 내부의 `generate_v50_writer_prompt` 메서드도 외부 호출자가 없다. `generate_self_diagnosis_checklist`은 `generate_v50_writer_prompt` 내부(L757)에서만 호출되므로 연쇄적으로 Dead Code.
- **Evidence**: `grep "generate_v50_writer_prompt"` 결과 — 선언(L701)과 main_a.py의 삭제 주석(L2420) 외에 호출자 없음.
- **Impact**: 968줄 중 약 83줄(L527-544 + L701-765)이 Dead Code. 유지보수 혼란 + 테스트 커버리지 착시.
- **Suggested fix direction**: 두 메서드를 삭제하거나, `@deprecated` 데코레이터 부착.

---

### TF-PB-04: `_decorate_arc_context_for_target`에서 `not current_arc_no` falsy 판정 — IMPORTANT

- **Location**: `prompt_builder.py:L603-L606`
- **Description**: `if not current_arc_no:`는 `current_arc_no=0`일 때도 True로 평가된다. Arc 번호는 일반적으로 1부터 시작하므로 0은 무효값이지만, 명시적 `is None` 비교가 의도를 더 명확히 표현한다.
- **Evidence**:
```python
@staticmethod
def _decorate_arc_context_for_target(context_text: str, current_arc_no: int | None) -> str:
    if not current_arc_no:  # 0도 걸림
        return context_text
    return f"[다음 Arc #{current_arc_no} 설계 기준]\n{context_text}"
```
- **Impact**: 현재 시스템에서 Arc 번호 0은 사용되지 않으므로 실제 버그가 아니다. 하지만 코드 의도가 모호하다.
- **Suggested fix direction**: `if current_arc_no is None:` 로 변경.

---

### TF-PB-05: NPC 프로필 추출에서 substring false-positive — IMPORTANT

- **Location**: `prompt_builder.py:L939-L943`
- **Description**: `extract_npc_profiles`에서 NPC 존재 여부를 `npc_name in arc_text`로 판별한다. `arc_text`는 `json.dumps(arc_data, ensure_ascii=False)`의 결과이므로, NPC 이름 "용"이 JSON 내 "용사", "금용", "무용" 등의 부분문자열로 매칭될 수 있다. 한국어 NPC 이름이 2-3글자인 경우 오탐 확률이 높다.
- **Evidence**:
```python
arc_text = json.dumps(arc_data, ensure_ascii=False) if arc_data else ""
for npc in npc_lib:
    npc_name = npc.get("name", "") or npc.get("Name", "")
    if npc_name and npc_name in arc_text:  # substring match
        npcs[npc_name] = npc
```
- **Impact**: 불필요한 NPC 프로필이 validation context에 포함될 수 있음. 이는 검증 과정에서 false positive 경고를 유발할 수 있으나, 프롬프트 품질에 대한 직접적 영향은 제한적 (추가 정보는 LLM에 해를 끼치지 않음).
- **Suggested fix direction**: 정규식 `\b` 경계 매칭 또는, NPC 이름 앞뒤에 JSON 구분자(`"`, `,`, ` `)가 있는지 확인하는 래퍼 사용. 단, 한국어는 `\b`가 불완전하므로 `f'"{npc_name}"' in arc_text` 패턴이 더 적합.

---

### TF-PB-06: `generate_cliche_avoidance_guide`에서 `cliche_check_result` 매개변수 미사용 — IMPORTANT

- **Location**: `prompt_builder.py:L446`
- **Description**: `cliche_check_result` 매개변수를 선언하고 있으나 함수 본문에서 한 번도 참조하지 않는다. 클리셰 가이드는 항상 동일한 하드코딩된 CLICHE_ALTERNATIVES를 출력한다. 이전 분석 결과를 반영하여 동적으로 가이드를 조정하려는 의도가 구현되지 않은 것으로 보인다.
- **Evidence**:
```python
def generate_cliche_avoidance_guide(self, cliche_check_result: dict = None) -> str:
    # cliche_check_result는 이 함수 본문에서 전혀 사용되지 않음
    CLICHE_ALTERNATIVES = { ... }
```
- **Impact**: 이전 원고의 클리셰 분석 결과를 반영하지 못하므로, Writer에게 항상 동일한 일반적 가이드만 제공됨. 또한 `generate_writer_guidance_v60_8`의 호출자(stage4_context_builder.py:L2622)가 `cliche_check_result`를 전달하지 않으므로(항상 None), 호출자 측에서도 미사용.
- **Suggested fix direction**: 파라미터를 제거하거나, 이전 원고의 클리셰 카운트를 반영하는 동적 가이드 구현.

---

### TF-PB-07: `generate_writer_guidance_v60_8` 호출 시 `episode_bibles`/`cliche_check_result` 항상 None — IMPORTANT

- **Location**: `prompt_builder.py:L487-L525`, `stage4_context_builder.py:L2622-L2625`
- **Description**: `generate_writer_guidance_v60_8`는 5개 매개변수를 가지고 있으나, 유일한 실제 호출자인 `stage4_context_builder.py:L2622`에서는 `blueprint`과 `prev_manuscript`만 전달한다. 따라서:
  - `episode_bibles`는 항상 `None` → `generate_item_acquisition_timeline`(L510)에서 `episode_bibles` 기반 타임라인 데이터가 생성되지 않음.
  - `cliche_check_result`는 항상 `None` → TF-PB-06과 동일.
  - `target_len`은 기본값 `ManuscriptLimits.TARGET_LENGTH` 사용.
- **Evidence**:
```python
# stage4_context_builder.py:L2622-2625
writer_guidance = writer_guidance_callback(
    blueprint=blueprint or {},
    prev_manuscript=prev_text or "",
)
```
- **Impact**: `generate_item_acquisition_timeline`(L302-369)은 `episode_bibles=None`이므로 `item_timeline`/`skill_timeline`이 비어 있게 되어, 아이템 획득 시점 정보가 누락된 채 가이드가 생성됨. 이는 `generate_writer_guidance_v60_8` 내부의 L510 호출과 별도 경로인 `build_item_acquisition_timeline`(L771)과 혼동 주의 — 후자는 DB에서 직접 로드하므로 정상 동작한다.
- **Suggested fix direction**: 호출자에서 `episode_bibles`를 전달하거나, `generate_writer_guidance_v60_8` 내부에서 `self._app`을 통해 직접 로드.

---

### TF-PB-08: Tactical 추출 결과 하드 트렁케이션 (1800자) — 경계 무인식 — INSIGHT

- **Location**: `prompt_builder.py:L691`
- **Description**: `extract_episode_tactical(...)[:1800]`으로 전술 문서를 1800자에서 하드 커팅한다. 한국어 텍스트에서 문장 중간이 잘릴 수 있으며, JSON 구조가 포함된 경우 유효하지 않은 JSON이 LLM에 전달될 수 있다.
- **Evidence**:
```python
f"[📜 핵심 전술 요약]: {extract_episode_tactical(...)[:1800]}\n"
```
- **Impact**: 잘린 문장이 LLM에 전달되면 문맥 오해 가능. 다만 이 필드는 프롬프트의 부가 정보이므로 심각한 영향은 아님. `tactical_utils.py`의 `extract_episode_tactical`이 이미 에피소드별 추출을 하므로 보통 1800자 이내.
- **Suggested fix direction**: 마지막 마침표/줄바꿈 위치에서 truncation하는 smart truncation 헬퍼 도입.

---

### TF-PB-09: `_item_timeline_cache` LRU 구현이 min-key 기반 (FIFO가 아닌 min-ep 퇴출) — INSIGHT

- **Location**: `prompt_builder.py:L841-L844`
- **Description**: LRU 캐시 제한(max 3)에서 퇴출할 키를 `min(self._item_timeline_cache.keys())`로 선택한다. 이는 진정한 LRU가 아니라 "가장 작은 에피소드 번호 퇴출"이다. 일반적으로 에피소드는 순차적으로 진행하므로 가장 작은 번호가 가장 오래된 것과 일치하여 실질적으로 올바르게 동작한다.
- **Evidence**:
```python
_MAX_TIMELINE_CACHE = 3
while len(self._item_timeline_cache) >= _MAX_TIMELINE_CACHE:
    oldest_ep = min(self._item_timeline_cache.keys())
    del self._item_timeline_cache[oldest_ep]
```
- **Impact**: 에피소드 번호 역순 접근(예: 롤백 후 과거 에피소드 재생성)에서 최근 사용된 캐시가 퇴출될 수 있으나, 롤백 시 `invalidate_timeline_cache()`가 호출되므로(main_a.py에서 4곳) 실제 문제는 없음.
- **Suggested fix direction**: 현재 동작이 충분함. 문서 주석에 "min-ep eviction"임을 명시.

---

### TF-PB-10: `generate_arc_context_v60`에서 `state_extractor` 없을 때 fallback 미호출 — INSIGHT

- **Location**: `prompt_builder.py:L566-L600`
- **Description**: L566에서 `state_extractor = self._app.agents.get("state_extractor")`가 `None`을 반환하면, L567의 `if state_extractor:` 블록을 skip하고 L590의 `except` 블록도 건너뛰어 L600의 fallback에 도달한다. 이것은 올바른 동작이다. 다만, `state_extractor`가 존재하지만 `agents`가 dict가 아닐 때 `get` 호출에서 `AttributeError`가 발생할 수 있다.
- **Evidence**:
```python
state_extractor = self._app.agents.get("state_extractor")  # agents가 dict가 아니면?
```
- **Impact**: L559의 `getattr(self._app, "agents", None)` 가드가 `agents` 존재를 확인하지만, `agents`가 None이 아니면서 dict가 아닌 경우(예: MagicMock)에는 `get`이 동작할 수 있으나 의외의 반환값이 올 수 있다. 실제 운영에서는 `agents`는 항상 dict이므로 문제없음.
- **Suggested fix direction**: 현재 충분함.

---

### TF-PB-11: `generate_arc_context_fallback`의 `item` 변수 재할당 — INSIGHT

- **Location**: `prompt_builder.py:L628-L632, L637-L641`
- **Description**: L628-629에서 `for item in items_acquired:` 루프 안에서 `item = str(item) if isinstance(item, dict) else item`으로 루프 변수를 재할당한다. 이것은 Python에서 정상적인 패턴이지만, 원본 dict 정보(name, description 등)가 `str(item)`으로 변환되면서 소실된다. `str(dict)`는 `{'name': '검', 'type': '무기'}` 같은 repr 문자열을 반환하므로 프롬프트에 Python dict 표현이 그대로 삽입될 수 있다.
- **Evidence**:
```python
for item in items_acquired:
    item = str(item) if isinstance(item, dict) else item
    # dict일 경우 "{'name': '검', 'type': '무기'}" 같은 문자열이 됨
```
- **Impact**: LLM 프롬프트에 Python dict repr이 포함될 수 있어 미관적으로 좋지 않으나, LLM은 이를 파싱하여 이해할 수 있으므로 기능적 영향은 제한적. L816-820의 `build_item_acquisition_timeline`에서는 `item.get("name", str(item))`으로 name 필드를 우선 추출하는 올바른 패턴을 사용한다.
- **Suggested fix direction**: L629를 `item = item.get("name", str(item)) if isinstance(item, dict) else str(item)`으로 변경.

---

### TF-PB-12: `build_validation_context`에서 `ep_num` 매개변수 미사용 — IMPORTANT

- **Location**: `prompt_builder.py:L863-L928`
- **Description**: `build_validation_context(self, ep_num, ...)`에서 `ep_num` 매개변수가 함수 본문에서 한 번도 참조되지 않는다. 에피소드 번호에 따라 히스토리 깊이를 조절하거나 특정 에피소드의 NPC 상태를 필터링해야 하는데, 현재는 전체 히스토리를 항상 반환한다.
- **Evidence**:
```python
def build_validation_context(
    self, ep_num: int, blueprint: dict = None, mode: str = "MANUSCRIPT", blueprint_text: str = ""
) -> dict:
    # ep_num은 이 함수 본문에서 사용되지 않음
    context = { ... }
    # ...모든 NPC를 무조건 포함, 히스토리도 에피소드 필터 없이 전체 반환
```
- **Impact**: 에피소드별 차별화 없이 동일한 context가 반환됨. 초반 에피소드에서도 후반 NPC가 포함되는 등 과도한 정보가 전달될 수 있으나, LLM 검증 과정에서 추가 정보는 보통 무해.
- **Suggested fix direction**: `ep_num`을 활용하여 해당 에피소드까지의 NPC만 필터링하거나, 매개변수를 제거하여 API를 정리.

---

### TF-PB-13: `generate_temporal_spatial_guide`에서 regex 한국어 위치 매칭 한정적 — INSIGHT

- **Location**: `prompt_builder.py:L396-L403`
- **Description**: 이전 원고에서 위치를 추출하는 regex가 무협 장르에 특화된 키워드만 포함한다 (`객잔|주막|산장|동굴|...`). 비무협 장르(헌터, 투자, 판타지 등)에서는 매칭되는 위치가 없어 가이드가 생성되지 않을 수 있다.
- **Evidence**:
```python
location_patterns = [
    r"(객잔|주막|산장|동굴|광장|저택|성문|시장|숲|산|강가|절벽|무림맹|사파)",
]
```
- **Impact**: 비무협 장르에서 시공간 연속성 가이드의 위치 부분이 누락됨. 다만 `start_location`이 blueprint에서 제공되면 여전히 가이드가 생성되므로, blueprint 의존으로 fallback됨.
- **Suggested fix direction**: `genre_schema_builder`에서 장르별 위치 키워드를 동적으로 가져오거나, 비무협 위치 패턴 추가.

---

### TF-PB-14: `_cumulative_state_cache_key` 키 충돌 가능성 — arc 내용 변경 시 stale 캐시 — CRITICAL

- **Location**: `prompt_builder.py:L568-L574`
- **Description**: `_cumulative_state_cache_key`로 `arc_count` (= `len(all_refined_arcs)`)를 사용한다. 아크 개수가 동일하지만 아크 내용이 변경된 경우(예: 아크 수정 후 같은 개수로 저장), 캐시가 유효하지 않은데도 stale 캐시가 반환된다.
- **Evidence**:
```python
arc_count = len(all_refined_arcs)
if self._app._cumulative_state_cache is not None and self._app._cumulative_state_cache_key == arc_count:
    cumulative_state = self._app._cumulative_state_cache  # stale!
```
- **Impact**: 아크 내용이 수정된 후 같은 개수의 아크로 `generate_arc_context_v60`이 호출되면, 이전 아크 상태가 LLM에 전달된다. 하지만 실제로 아크 수정은 `reset_stage_2` 또는 `rewind_stage_2`를 통해 수행되며, 이 경우 `_cumulative_state_cache = None`으로 초기화되므로 **현재 워크플로우에서는 stale 캐시가 발생하지 않는다.**
- **Suggested fix direction**: 캐시 키를 `(arc_count, hash_of_last_arc)`로 변경하면 이론적 안전성이 높아짐. 하지만 현재 invalidation 경로가 충분히 커버하고 있으므로 우선순위 낮음.

**최종 판정: IMPORTANT** (현재 invalidation이 충분히 커버하므로 하향)

---

## 4. Summary Matrix

| ID | Title | Severity | Location | 실제 운영 위험 |
|---|---|---|---|---|
| TF-PB-01 | `state_constraints` 섀도잉 + Dead 변수 | IMPORTANT | L613-624 | 낮음 (Dead 변수) |
| TF-PB-02 | `build_validation_context` app=None 크래시 | IMPORTANT | L881-885 | 낮음 (호출 경로 없음) |
| TF-PB-03 | `generate_v50_writer_prompt` Dead Code | IMPORTANT | L527-765 | 없음 (Dead Code) |
| TF-PB-04 | `_decorate_arc_context_for_target` falsy 판정 | IMPORTANT | L603-606 | 없음 (Arc 0 미사용) |
| TF-PB-05 | NPC substring false-positive | IMPORTANT | L939-943 | 낮음 (추가 프로필 무해) |
| TF-PB-06 | `cliche_check_result` 매개변수 미사용 | IMPORTANT | L446 | 중간 (동적 가이드 미구현) |
| TF-PB-07 | `episode_bibles`/`cliche_check_result` 항상 None | IMPORTANT | L487/L2622 | 중간 (아이템 타임라인 누락) |
| TF-PB-08 | Tactical 하드 트렁케이션 1800자 | INSIGHT | L691 | 낮음 (보통 범위 내) |
| TF-PB-09 | LRU가 min-ep 퇴출 | INSIGHT | L841-844 | 없음 (invalidation 커버) |
| TF-PB-10 | `state_extractor` 없을 때 fallback 경로 | INSIGHT | L566-600 | 없음 (올바르게 동작) |
| TF-PB-11 | dict → str(dict) repr in prompt | INSIGHT | L628-632 | 낮음 (LLM 이해 가능) |
| TF-PB-12 | `ep_num` 매개변수 미사용 | IMPORTANT | L863 | 낮음 (과도한 정보 무해) |
| TF-PB-13 | 위치 regex 무협 한정 | INSIGHT | L396-403 | 낮음 (blueprint fallback) |
| TF-PB-14 | `_cumulative_state_cache_key` arc_count 키 | IMPORTANT | L568-574 | 없음 (invalidation 커버) |

**최종 집계: CRITICAL 0 / IMPORTANT 9 / INSIGHT 5 = 14건**

(초기 분류에서 재검토 후 CRITICAL 2건 모두 IMPORTANT로 하향 조정됨 — 실제 운영 호출 경로에서의 위험이 낮은 것으로 확인)

---

## 5. 핵심 코드 참조 (Appendix)

### A. PromptBuilder 메서드 전수 목록 (15개)

| # | Method | Type | Lines | Status |
|---|---|---|---|---|
| 1 | `generate_arc_position_guide` | Pure | L86-152 | LIVE |
| 2 | `generate_high_impact_zone_guide` | Pure | L158-209 | LIVE |
| 3 | `generate_npc_relationship_justification` | Pure | L211-300 | LIVE |
| 4 | `generate_item_acquisition_timeline` | Pure | L302-369 | LIVE (via writer_guidance) |
| 5 | `generate_temporal_spatial_guide` | Pure | L371-444 | LIVE |
| 6 | `generate_cliche_avoidance_guide` | Pure | L446-485 | LIVE (param unused) |
| 7 | `generate_writer_guidance_v60_8` | Pure | L487-525 | LIVE |
| 8 | `generate_self_diagnosis_checklist` | Pure | L527-544 | **DEAD** |
| 9 | `generate_arc_context_v60` | App-dep | L550-600 | LIVE |
| 10 | `_decorate_arc_context_for_target` | Static | L602-606 | LIVE (internal) |
| 11 | `generate_arc_context_fallback` | Semi-pure | L608-695 | LIVE |
| 12 | `generate_v50_writer_prompt` | App-dep | L701-765 | **DEAD** |
| 13 | `build_item_acquisition_timeline` | App-dep | L771-857 | LIVE |
| 14 | `build_validation_context` | App-dep | L863-928 | LIVE |
| 15 | `extract_npc_profiles` | App-dep | L930-945 | LIVE |
| 16 | `get_character_traits` | App-dep | L947-968 | LIVE |
| - | `invalidate_timeline_cache` | Instance | L69-80 | LIVE (utility) |

### B. 캐시 무효화 호출 지점 (main_a.py)

| Operation | Line | invalidate_timeline_cache | _cumulative_state_cache=None |
|---|---|---|---|
| `_reset_stage_2` | L3678 | O | O |
| `_rewind_stage_2` | L3711 | O | O |
| `_rollback_episode` | L3741 | O | O |
| `_wipe_production_data` | L3780 | O | O |

### C. `generate_arc_context_fallback` 데이터 소스 매핑

```
all_refined_arcs (list[dict])
    |
    +-- last_arc = all_refined_arcs[-1]
    |       +-- joint_docs -> world_joint        (L679)
    |       +-- status_shadow -> item_consumption (L680)
    |       +-- tactical_doc -> episode_tactical  (L691, [:1800] truncated)
    |
    +-- for prev_arc in all_refined_arcs:  (전체 순회)
    |       +-- state_constraints -> protagonist_items / items_acquired  (L626)
    |       +-- joint_docs -> physical_inventory  (L635)
    |       +-- tactical_doc -> GRANT_PATTERNS regex match  (L651)
    |
    +-- compute_terminal_arc_state(all_refined_arcs)  (arc_state_utils.py)
            +-- final_energy, injuries, location, equipment_text
            +-- energy_history
```

### D. Error Handling 분류

| Location | Exception Type | Handler | Severity |
|---|---|---|---|
| L590 | `Exception` (StateExtractor) | audit_event + ui.log + fallback | 적절 |
| L722 | `Exception` (pacing_analyzer) | `logging.warning` | 적절 |
| L732 | `Exception` (character_voice) | `logging.warning` | 적절 |
| L742 | `Exception` (foreshadow_tracker) | `logging.warning` | 적절 |
| L752 | `Exception` (expert_mixture) | `logging.warning` | 적절 |
| L760 | `Exception` (self_diagnosis) | `logging.warning` | 적절 (Dead Code) |
| L852 | `Exception` (timeline build) | ui.log or `logging.warning` | 적절 |
| L918 | `(AttributeError, KeyError, TypeError)` (POV) | `pass` | 적절 (정상 생략) |
| L921 | `Exception` (validation context) | ui.log or `logging.warning` | 적절 |

**Bare except: 0건. 모든 핸들러가 적절한 fallback을 제공.**
