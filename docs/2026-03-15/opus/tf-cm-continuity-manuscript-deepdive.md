# TF-CM: Continuity Manuscript 딥다이브

| Field | Value |
|-------|-------|
| Baseline | bbb00a77 |
| Date | 2026-03-15 |
| Scope | Continuity Manuscript: item timeline, relationship tracking, BP compliance, Director feedback |
| Source files | continuity_manuscript.py:1226줄 |
| TF Items | 16 (CRITICAL 3 / IMPORTANT 8 / INSIGHT 5) |

## 1. Executive Summary

`ContinuityManuscriptValidator`는 ContinuityInspector God Object에서 분리된 원고 수준 연속성 검증 모듈이다. Stage 4에서 Writer가 생성한 원고가 이전 에피소드와 논리적으로 연결되고 Blueprint 설계를 준수하는지 검증한다.

핵심 발견:

1. **LLM 실패 시 fail-open (PASS)**: LLM 검증이 실패해도 `decision: PASS`를 반환하여, 원고 모순이 미검출 상태로 통과될 수 있다. 이는 Director 측 `check_manuscript_continuity_with_cache`의 fail-closed (CONFLICT/REJECT) 정책과 대비된다.
2. **원고 절단 경계 정보 소실**: `_format_prev_manuscripts`가 1,500자 초과 원고를 700+500자로 잘라 중간 300자를 버리며, 버려지는 영역에 핵심 아이템 획득/관계 전환 이벤트가 있으면 LLM이 이를 인식 불가.
3. **관계 추적 중복 + 불일치**: `_check_relationship_jump`와 `_track_relationship_history`가 동일한 목적의 코드를 서로 다른 상태 모델로 수행하여, 같은 관계 변화에 대해 상충하는 판정을 낼 수 있다.
4. **"사망"과 "굴복" 상태가 STATE_ORDER에 누락**: `_track_relationship_history`에서 STATE_KEYWORDS에는 7개 상태가 정의되나, STATE_ORDER에는 6개만 포함되어 "사망"/"굴복" 관계 변화는 jump_distance 비교를 건너뛴다.
5. **Blueprint 준수 키워드 매칭의 취약성**: `_extract_keywords`가 stopwords 14개만 필터하는 단순 `[가-힣]{2,}` 패턴으로 핵심 씬 반영 여부를 판단하여, 오탐/미탐 비율이 높다.

## 2. Architecture / Data Flow Diagram (ASCII)

```
Stage 4 Interview Round
  |
  +-- [경로 A] ContinuityInspector.inspect_manuscript()
  |     |     (facade -> ContinuityManuscriptValidator.inspect_manuscript)
  |     |
  |     +-- Phase 1: Python 사전 필터링
  |     |     |-- _manuscript_python_precheck()
  |     |     |     |-- 1. ACQUISITION_PATTERNS 으로 이전 원고 아이템 추출
  |     |     |     |-- 2. POSSESSION_PATTERNS 으로 현재 원고 사용 아이템 추출
  |     |     |     |-- 3. _is_item_acquired() 미획득 아이템 체크
  |     |     |     |-- 4. 부상 상태 연속성 (키워드 매칭)
  |     |     |     |-- 5. Blueprint 핵심 씬 반영 (_extract_keywords)
  |     |     |     |-- 6. _check_relationship_jump()       <-- 관계 추적 #1
  |     |     |     |-- 7. _check_villain_intelligence()
  |     |     |     |-- 8. _check_time_flow()
  |     |     |     +-- 9. _check_reader_immersion()
  |     |     |
  |     |     +-- critical_violations, warnings, timeline
  |     |
  |     +-- Phase 2: LLM 정밀 검증
  |     |     |-- _format_prev_manuscripts()  <-- 원고 절단 (1500자 -> 700+500)
  |     |     |-- MANUSCRIPT_CONTINUITY_PROMPT (L19-L141)
  |     |     |-- LLM ask() + _extract_json_robust()
  |     |     +-- Python warnings 병합 -> 최종 result
  |     |
  |     +-- 실패 시: decision="PASS", degraded=True  <-- FAIL-OPEN
  |
  +-- [경로 B] Director.check_manuscript_continuity_with_cache()
  |     |     (DirectorContinuityValidator)
  |     |-- DB에서 최근 30화 원고 조회
  |     |-- Context Cache (1800s TTL)
  |     |-- MANUSCRIPT_HISTORY_CONFLICT_PROMPT
  |     +-- 실패 시: decision="CONFLICT"              <-- FAIL-CLOSED
  |
  +-- [경로 C] inspect_manuscript_v59()
        |-- inspect_manuscript() 호출 (경로 A)
        |-- _check_skill_timeline()              <-- 스킬 타임라인
        |-- _track_relationship_history()        <-- 관계 추적 #2
        +-- 병합: violations + warnings -> 최종 decision

주의:
- 경로 A의 _check_relationship_jump (L509) 와
  경로 C의 _track_relationship_history (L1043) 는
  서로 다른 상태 모델을 사용하는 중복 구현
- 경로 A는 fail-open, 경로 B는 fail-closed (상충)
- hud_history 파라미터는 모든 경로에서 미사용
```

## 3. TF Items

### TF-CM-01: LLM 실패 시 fail-open PASS 반환 — CRITICAL

- **Location**: `continuity_manuscript.py:L327-L355`
- **Description**: `inspect_manuscript()`에서 LLM 호출(`self._ci.ask()`)이 예외를 발생시키면, `decision: "PASS"`를 반환한다. 이는 연속성 모순이 있는 원고가 검증 없이 통과될 수 있음을 의미한다.
- **Evidence**:
```python
# L327-L355
except Exception as e:
    logging.warning(f" [ContinuityInspector] 원고 LLM 검증 실패: {e}")
    if python_check.get("warnings"):
        # ...
        return {
            "decision": "PASS",        # <-- fail-open
            "severity": "MINOR",
            "degraded": True,
            # ...
        }
    return {
        "decision": "PASS",            # <-- fail-open
        "severity": "MINOR",
        "degraded": True,
        # ...
    }
```
- **Impact**: LLM API 장애, 쿼터 초과, 타임아웃 시 원고가 연속성 검증 없이 Stage 4를 통과한다. `degraded=True` 플래그가 설정되지만, 이를 소비하는 호출자가 이 플래그를 확인하여 REJECT로 전환하는 로직이 확인되지 않는다. Director 측 `check_manuscript_continuity_with_cache`(director_continuity.py:L861-L868)는 동일 상황에서 `decision: "CONFLICT"`(fail-closed)를 반환하므로, 시스템 내 fail-closed/fail-open 정책이 불일치한다.
- **Suggested fix direction**: `decision: "PASS"` 대신 `decision: "REJECT"` + `"degraded": True`로 변경하여 fail-closed 정책으로 통일. 또는 호출자(stage4_interview_round 등)에서 `degraded=True` 시 자동 재시도 로직 추가.

---

### TF-CM-02: JSON 파싱 실패 시에도 PASS 반환 — CRITICAL

- **Location**: `continuity_manuscript.py:L293-L305`
- **Description**: LLM 응답에서 JSON 파싱이 실패하면(`not isinstance(result, dict)`), `decision: "PASS"`를 반환한다.
- **Evidence**:
```python
# L293-L305
if not isinstance(result, dict):
    logging.warning(" [V60.74] JSON 파싱 실패 - 수동 검수 권장")
    result = {
        "decision": "PASS",        # <-- 파싱 실패에도 PASS
        "severity": "NONE",
        # ...
        "confidence": 0.0,
        "parsing_error": True,
    }
```
- **Impact**: LLM이 JSON이 아닌 자연어로 "이 원고에는 심각한 모순이 있습니다"라고 응답해도 PASS 처리된다. `parsing_error: True` 플래그가 설정되지만 소비자 측에서 이를 차단하는 로직이 확인되지 않는다.
- **Suggested fix direction**: 파싱 실패 시 `decision: "REJECT"` 반환. `confidence: 0.0`은 적절하지만 PASS와 모순된다.

---

### TF-CM-03: "사망"/"굴복" 상태가 STATE_ORDER에 누락 — CRITICAL

- **Location**: `continuity_manuscript.py:L1055-L1065`
- **Description**: `_track_relationship_history`의 `STATE_KEYWORDS`에는 7개 상태가 정의되어 있으나 (`사망`, `굴복`, `충성`, `경외`, `의심`, `무시`, `적대`), `STATE_ORDER`에는 6개만 포함되어 있다 (`적대`, `무시`, `의심`, `중립`, `경외`, `충성`). "사망"과 "굴복"은 STATE_ORDER에 없으므로 L1125의 `if prev_state in STATE_ORDER and curr_state in STATE_ORDER` 조건을 통과하지 못해, 사망한 NPC가 부활하거나 굴복 상태에서 급변하는 경우 관계 급변 경고가 발생하지 않는다.
- **Evidence**:
```python
# L1055-L1063: STATE_KEYWORDS - 7개 상태
STATE_KEYWORDS = {
    "사망": ["죽었", "숨이 끊", "사망", ...],   # <-- STATE_ORDER에 없음
    "굴복": ["굴복", "용서를", ...],             # <-- STATE_ORDER에 없음
    "충성": [...], "경외": [...], "의심": [...], "무시": [...], "적대": [...]
}

# L1065: STATE_ORDER - 6개만
STATE_ORDER = ["적대", "무시", "의심", "중립", "경외", "충성"]
#  "중립"은 STATE_KEYWORDS에 없고, "사망"/"굴복"은 STATE_ORDER에 없음

# L1125: 비교 시 양쪽 다 STATE_ORDER에 있어야 함
if prev_state in STATE_ORDER and curr_state in STATE_ORDER:
```
- **Impact**: 사망한 NPC(사병, 부하들 등)가 다음 원고에서 아무런 설명 없이 재등장하는 경우, `prev_state="사망"`이 STATE_ORDER에 없으므로 비교 로직을 건너뛴다. 이는 가장 심각한 연속성 오류(죽은 NPC 부활)를 Python 사전 검증에서 놓치는 결과를 초래한다. 또한 `"중립"`은 STATE_ORDER에만 있고 STATE_KEYWORDS에는 없어, `infer_state_from_context` fallback으로 "중립"이 반환되지만 이에 대한 키워드 탐지 경로가 없는 비대칭이 있다.
- **Suggested fix direction**: STATE_ORDER에 "사망"과 "굴복"을 적절한 위치에 추가. "사망"은 특수 상태로 별도 처리(사망 후 재등장 = 무조건 CRITICAL)하는 것이 이상적.

---

### TF-CM-04: 원고 절단 경계에서 정보 소실 — IMPORTANT

- **Location**: `continuity_manuscript.py:L841-L843`
- **Description**: `_format_prev_manuscripts`에서 1,500자 초과 원고를 `content[:700] + "...(중략)..." + content[-500:]`로 절단한다. 중간 부분(701~len-500)이 완전히 소실된다. 평균 원고 길이가 5,000자(ManuscriptLimits.TARGET)인 점을 감안하면, 약 3,800자(76%)가 손실된다.
- **Evidence**:
```python
# L841-843
if len(content) > 1500:
    excerpt = content[:700] + "\n...(중략)...\n" + content[-500:]
else:
    excerpt = content
```
- **Impact**: 원고 중반에 발생하는 아이템 획득, 관계 변화, 중요 설정 등이 LLM에 전달되지 않아, LLM 기반 연속성 검증의 정확도가 저하된다. Python 사전 검증(`_manuscript_python_precheck`)은 전체 원고를 사용하지만, LLM 검증에서는 절단된 버전만 전달된다.
- **Suggested fix direction**: (1) 원고 요약(summary)이 있다면 full text 대신 요약 전달, (2) 절단 시 핵심 이벤트 키워드가 포함된 문단을 우선 보존하는 smart truncation 적용, (3) 절단 비율을 원고 크기에 비례하여 조정.

---

### TF-CM-05: 관계 추적 중복 구현 + 상태 모델 불일치 — IMPORTANT

- **Location**: `continuity_manuscript.py:L509-L579` vs `L1043-L1156`
- **Description**: `_check_relationship_jump`(L509)과 `_track_relationship_history`(L1043)는 동일한 목적(NPC 관계 급변 탐지)의 코드이나, 서로 다른 상태 모델을 사용한다.

| 항목 | `_check_relationship_jump` (L509) | `_track_relationship_history` (L1043) |
|------|----------------------------------|--------------------------------------|
| 상태 수 | 5 (멸시/무시/의심/경외/충성) | 7 (사망/굴복/충성/경외/의심/무시/적대) |
| 전환 규칙 | ALLOWED_TRANSITIONS (명시적 허용 목록) | STATE_ORDER (선형 거리 기반) |
| NPC 범위 | GROUP_KEYWORDS 8개 | NPC_KEYWORDS 14개 |
| 호출 경로 | inspect_manuscript → _manuscript_python_precheck | inspect_manuscript_v59 |

- **Evidence**:
```python
# _check_relationship_jump (L519-L527):
RELATIONSHIP_KEYWORDS = {"멸시": ..., "무시": ..., "의심": ..., "경외": ..., "충성": ...}
STATE_PRIORITY = {"멸시": 0, "무시": 1, "의심": 2, "경외": 3, "충성": 4}
ALLOWED_TRANSITIONS = {"멸시": ["무시", "의심"], ...}

# _track_relationship_history (L1055-L1065):
STATE_KEYWORDS = {"사망": ..., "굴복": ..., "충성": ..., "경외": ..., "의심": ..., "무시": ..., "적대": ...}
STATE_ORDER = ["적대", "무시", "의심", "중립", "경외", "충성"]
```
- **Impact**: (1) `inspect_manuscript_v59` 경로에서는 `inspect_manuscript`(경로 A 포함)를 먼저 호출하므로, `_check_relationship_jump` 결과가 먼저 포함되고 이어서 `_track_relationship_history` 결과가 병합된다. 같은 NPC에 대해 상충하는 판정이 동시에 반환될 수 있다. (2) `"적대"` 상태가 `_check_relationship_jump`에는 없고 `_track_relationship_history`에만 있어, 적대→충성 같은 극단적 전환은 후자에서만 탐지된다.
- **Suggested fix direction**: 두 메서드를 하나로 통합하고, 확장된 상태 모델(사망/적대/무시/의심/중립/경외/충성/굴복)을 단일 SSOT로 사용.

---

### TF-CM-06: `hud_history` 파라미터 미사용 (데드 파라미터) — IMPORTANT

- **Location**: `continuity_manuscript.py:L216, L1164`
- **Description**: `inspect_manuscript`와 `inspect_manuscript_v59` 모두 `hud_history: list[dict] = None` 파라미터를 받지만, 함수 본문 어디에서도 사용하지 않는다. `inspect_manuscript_v59`는 이 값을 `inspect_manuscript`에 전달하지만, 거기서도 사용되지 않는다.
- **Evidence**:
```python
# L210-218:
def inspect_manuscript(
    self,
    current_ep: int,
    manuscript: str,
    blueprint: dict,
    prev_manuscripts: list[dict],
    hud_history: list[dict] = None,    # <-- 받기만 하고 미사용
    entity_registry: dict = None,
) -> dict:
    # ... hud_history는 본문에서 한 번도 참조되지 않음
```
- **Impact**: HUD 스냅샷에는 캐릭터의 HP, 아이템 인벤토리, 스킬 목록 등 구조화된 상태 정보가 있을 수 있다. 이 데이터를 활용하면 Python 사전 검증(아이템/상태 연속성)의 정확도가 크게 향상될 수 있으나, 현재는 완전히 무시되고 있다.
- **Suggested fix direction**: HUD 데이터가 실제로 전달되는 경우가 있다면 `_manuscript_python_precheck`에서 활용. 전달되지 않는다면 파라미터 시그니처에서 제거하여 API 혼란 방지.

---

### TF-CM-07: 원고 excerpt 4,000자 절단 (LLM 입력) — IMPORTANT

- **Location**: `continuity_manuscript.py:L275`
- **Description**: LLM에 전달되는 현재 원고가 4,000자로 절단된다. `ManuscriptLimits.TARGET`이 5,000자이므로, 평균적으로 원고의 마지막 1,000자가 LLM 검증에서 빠진다.
- **Evidence**:
```python
# L275
manuscript_excerpt = manuscript[:4000] if len(manuscript) > 4000 else manuscript
```
- **Impact**: 원고 후반부에 위치하는 Cliffhanger 엔딩, 상태 변화, 아이템 획득/소실 장면이 LLM에 전달되지 않아, Blueprint 준수 검증(`cliffhanger_implemented`)과 아이템/상태 연속성 검증의 정확도가 저하된다. 특히 Blueprint 검증 항목에 "Cliffhanger 엔딩이 원고 끝에 구현되었는가?" (L51)가 있으나, 원고 끝 부분이 절단될 수 있다.
- **Suggested fix direction**: smart_truncate(중요 부분 보존)를 사용하거나, 최소한 앞뒤를 분리하여 (처음 2000자 + 마지막 2000자) 형태로 전달.

---

### TF-CM-08: `_is_item_acquired` 부분매칭 오탐 위험 — IMPORTANT

- **Location**: `continuity_manuscript.py:L496-L507`
- **Description**: `_is_item_acquired`에서 부분 문자열 매칭(`shorter in longer`)과 길이 비율 50% 기준으로 동일 아이템을 판정한다. 이는 ContinuityInspector의 `_is_same_item`(L248-L264)이 완전 일치만 허용하는 초보수적 접근과 대비된다.
- **Evidence**:
```python
# L503-506 (_is_item_acquired - 느슨한 매칭)
if len(item) >= 2 and len(acquired) >= 2:
    shorter, longer = (item, acquired) if len(item) <= len(acquired) else (acquired, item)
    if shorter in longer and len(shorter) / len(longer) >= 0.5:
        return True

# continuity_inspector.py:L248-264 (_is_same_item - 엄격한 매칭)
# 100% 확실한 경우만 True, 조금이라도 다르면 False
# 정규화 후 완전 일치만 허용
```
- **Impact**: `_is_item_acquired`는 "천잠검" 획득 시 "천잠"이 사용된 것으로 판정하여 오탐을 발생시킬 수 있다. 반대로 "검"이 2자이므로 다른 "검" 포함 아이템과 매칭될 수 있다. 예: "혈광검"(획득) vs "검"(사용) → len("검")/len("혈광검") = 0.33 < 0.5 → 통과하지만, "혈검"(획득) vs "혈광검"(사용) → "혈검" in "혈광검" = True, 2/3 = 0.67 ≥ 0.5 → 같은 아이템으로 판정(오탐 가능).
- **Suggested fix direction**: `_is_same_item`의 보수적 매칭을 사용하도록 통일. 부분 매칭이 필요하면 최소 길이 기준을 3자 이상으로 상향.

---

### TF-CM-09: `inspect_manuscript_v59`에서 entity_registry 미전달 — IMPORTANT

- **Location**: `continuity_manuscript.py:L1158-L1167`
- **Description**: `inspect_manuscript_v59`는 `entity_registry` 파라미터를 받지 않으며, 내부에서 `inspect_manuscript`를 호출할 때 `entity_registry=None`이 기본값으로 전달된다.
- **Evidence**:
```python
# L1158-1167
def inspect_manuscript_v59(
    self,
    current_ep: int,
    manuscript: str,
    blueprint: dict,
    prev_manuscripts: list[dict],
    hud_history: list[dict] = None,
    # entity_registry 파라미터 없음!
) -> dict:
    base_result = self.inspect_manuscript(
        current_ep, manuscript, blueprint, prev_manuscripts, hud_history
        # entity_registry 미전달 → None
    )
```
- **Impact**: `inspect_manuscript_v59` 경로를 사용하면 Entity 명칭 일관성 검증(MANUSCRIPT_CONTINUITY_PROMPT Step 5)이 항상 빈 레지스트리로 실행된다. V59 강화 검증이 V49.1 기본 검증보다 Entity 검증 면에서 더 약해지는 역설이 발생한다.
- **Suggested fix direction**: `inspect_manuscript_v59` 시그니처에 `entity_registry: dict = None` 추가 후 `inspect_manuscript` 호출 시 전달.

---

### TF-CM-10: Blueprint 준수 검증의 키워드 매칭 허점 — IMPORTANT

- **Location**: `continuity_manuscript.py:L445-L464, L805-L830`
- **Description**: Blueprint 핵심 씬 반영 여부를 `_extract_keywords`로 추출한 한글 2자 이상 단어가 원고에 존재하는지로 판정한다. `_extract_keywords`의 stopwords 목록이 14개로 매우 제한적이며, 일반적인 한국어 불용어(무협 장르의 "무공", "전투", "경지" 등 고빈도 용어)가 포함되지 않는다.
- **Evidence**:
```python
# L805-830 (_extract_keywords)
pattern = r"[가-힣]{2,}"
words = re.findall(pattern, text)
stopwords = {"것이다", "있다", "없다", "하다", "되다", "이다",
             "그", "저", "이", "그것", "저것", "이것", "때문", "그래서", "하지만", "그러나"}
keywords = [w for w in words if w not in stopwords and len(w) >= 2]
return keywords[:max_keywords]

# L451-455 (Blueprint 씬 반영 체크)
for scene_key in core_scenes:
    scene_desc = scene_breakdown.get(scene_key, "")
    keywords = self._extract_keywords(scene_desc)
    if any(kw in manuscript for kw in keywords if kw):
        reflected_count += 1
```
- **Impact**: (1) "전투 장면"이라는 씬 설명에서 키워드 "전투", "장면"이 추출되는데, 원고에 "전투"라는 단어가 한 번이라도 등장하면 해당 씬이 반영된 것으로 판정된다 (높은 오탐률). (2) Blueprint에 "검문소에서 은밀한 거래"라는 핵심 씬이 있을 때, 키워드 "검문소", "은밀한", "거래" 중 하나만 있어도 PASS — 실제로는 해당 씬이 누락되었을 수 있다. (3) max_keywords=5이므로 씬 설명이 길어도 상위 5개 키워드만 사용.
- **Suggested fix direction**: (1) 장르별 고빈도 불용어 추가, (2) 키워드 AND 조건(최소 2개 이상 동시 출현 요구) 검토, (3) 핵심 씬 매칭은 LLM에 위임하는 것이 더 정확.

---

### TF-CM-11: `_check_relationship_jump` 첫 등장(first occurrence) 탐지 문제 — IMPORTANT

- **Location**: `continuity_manuscript.py:L543-L549, L551-L558`
- **Description**: `_check_relationship_jump`에서 이전 원고의 NPC 상태를 `rfind`로 마지막 등장 위치에서 탐지하지만(L544), 현재 원고는 `find`로 첫 등장 위치에서 탐지한다(L554). 이 비대칭으로 인해, 이전 원고에서 NPC가 여러 번 등장하며 관계가 변화한 경우 마지막 상태만 캡처되고, 현재 원고에서는 첫 등장 상태만 캡처된다.
- **Evidence**:
```python
# L543-548 (이전 원고: rfind = 마지막 등장)
for group in GROUP_KEYWORDS:
    if group in content:
        idx = content.rfind(group)  # <-- 마지막
        context = content[max(0, idx - 300):min(len(content), idx + 300)]

# L552-557 (현재 원고: find = 첫 등장)
for group in GROUP_KEYWORDS:
    if group in manuscript:
        idx = manuscript.find(group)  # <-- 처음
        context = manuscript[max(0, idx - 300):min(len(manuscript), idx + 300)]
```
- **Impact**: 현재 원고에서 NPC가 처음에는 의심 상태이다가 후반에 충성으로 전환되는 경우, 첫 등장(의심)만 캡처되어 이전 의심→현재 의심으로 판정(정상)되지만, 실제로는 의심→충성 전환이 발생했다. 반대로 이전 원고에서 마지막 상태만 캡처하므로, 원고 전반부의 중요한 관계 맥락이 누락된다.
- **Suggested fix direction**: 모든 등장을 순회하여 관계 변화 히스토리를 구축하거나, 최소한 이전/현재 모두 `rfind`(마지막 상태)로 통일하여 최종 상태 비교의 일관성 확보.

---

### TF-CM-12: `_check_villain_intelligence` 글로벌 키워드 스캔 — INSIGHT

- **Location**: `continuity_manuscript.py:L620-L631`
- **Description**: 악역 지능 보호 검증에서 "의심", "경계", "감시" 등의 `VIGILANT_KEYWORDS`를 원고 전체에서 검색한다. 이 키워드들이 악역이 아닌 다른 캐릭터의 맥락에서 등장해도 악역이 경계하는 것으로 판정된다.
- **Evidence**:
```python
# L624-625
if any(kw in content for kw in VIGILANT_KEYWORDS):
    vigilant_found = True
# "주인공이 의심했다" → vigilant_found = True (오탐)
```
- **Impact**: 주인공이나 동료가 "의심"하는 묘사가 있으면 악역의 학습이 있는 것으로 간주되어, 실제로는 어리석은 악역 패턴이 반복되어도 경고가 발생하지 않을 수 있다.
- **Suggested fix direction**: 악역 캐릭터 주변 문맥에서만 키워드를 검색하도록 scope 제한. Entity Registry에서 악역 캐릭터를 식별하여 문맥 창(context window)을 적용.

---

### TF-CM-13: `_is_same_skill` 과도한 부분매칭 — INSIGHT

- **Location**: `continuity_manuscript.py:L1015-L1037`
- **Description**: `_is_same_skill`에서 `skill1 in skill2 or skill2 in skill1`(L1023)로 부분 문자열 매칭을 수행하고, 한글 2자 이상 키워드 교집합이 1개 이상이면 같은 스킬로 판정한다(L1034). 단, stopwords가 1자 한글만 포함(`"법", "공", "결", "술", "식", "초"`)하여 효과가 제한적이다.
- **Evidence**:
```python
# L1023
if skill1 in skill2 or skill2 in skill1:
    return True
# "태극검법" in "태극혼원검법" → True (합리적)
# "검법" in "태극검법" → True (오탐 — 모든 검법이 같은 스킬)

# L1029-1034
stopwords = {"법", "공", "결", "술", "식", "초"}
# 1자 stopword만 → "검법"(2자)은 제거되지 않음
```
- **Impact**: "검법"이 모든 검법 스킬과 동일하게 판정되어, 미습득 스킬 사용 경고가 발생하지 않을 수 있다. 동시에 "태극검법"과 "청풍검법"은 "검법" 키워드를 공유하므로 같은 스킬로 오판될 수 있다.
- **Suggested fix direction**: 부분 문자열 매칭에 최소 길이 기준(예: 3자 이상) 추가. 2자 stopwords("검법", "권법", "장법" 등 일반적 접미어) 추가. 또는 `_is_same_item`과 유사한 보수적 접근 채택.

---

### TF-CM-14: `_format_prev_manuscripts`의 prev_manuscripts 순서 의존성 — INSIGHT

- **Location**: `continuity_manuscript.py:L832-L850`
- **Description**: `_format_prev_manuscripts`는 입력 리스트를 순서대로 순회하며, 정렬이나 중복 제거를 수행하지 않는다. `get_prev_manuscripts`(L357-376)에서는 `range(start_ep, current_ep)`로 순서가 보장되지만, 외부에서 직접 `prev_manuscripts`를 전달하는 경우 순서가 보장되지 않을 수 있다.
- **Evidence**:
```python
# L832-850: 입력 순서 그대로 포맷
for ms in prev_manuscripts:
    ep_num = ms.get("ep_num", 0)
    content = ms.get("content", "")
    # ... 정렬 없이 순서대로 출력
```
- **Impact**: 경미. `get_prev_manuscripts`를 통해 조회하면 에피소드 순서가 보장되나, 외부에서 역순이나 무순서 리스트가 전달되면 LLM이 시간순서를 오해할 수 있다.
- **Suggested fix direction**: `sorted(prev_manuscripts, key=lambda m: m.get("ep_num", 0))`로 정렬 보장.

---

### TF-CM-15: Python 사전 검증 critical_violations가 LLM 판정에 영향 미침 — INSIGHT

- **Location**: `continuity_manuscript.py:L262-L323`
- **Description**: Python 사전 검증의 `critical_violations`는 LLM에 전달되지 않고, LLM 판정 후 `warnings`로 병합된다(L315-323). "advisory"라는 명칭과 달리 Python이 CRITICAL로 판정한 아이템도 warnings 레벨로 다운그레이드된다.
- **Evidence**:
```python
# L262-263: Python advisory는 로깅만
python_advisory = python_check.get("critical_violations", [])
if python_advisory:
    logging.info(f" [V60.56] Python advisory 발견 {len(python_advisory)}건 - LLM에게 전달")
    # 실제로는 LLM 프롬프트에 전달되지 않음!

# L315-323: LLM 결과에 warnings로 병합
if python_check.get("critical_violations"):
    result.setdefault("warnings", [])
    for _cv in python_check["critical_violations"]:
        result["warnings"].append(f"[Python advisory] {_cv_desc}")
        # "critical_violations"가 "warnings"로 다운그레이드
```
- **Impact**: (1) 로그 메시지 "LLM에게 전달"은 오해를 유발 — 실제로는 프롬프트에 포함되지 않는다. (2) Python이 CRITICAL로 판정한 미획득 아이템 사용이 경고(warnings)로만 기록되어, LLM이 PASS를 반환하면 CRITICAL 문제가 있어도 최종 decision이 PASS가 된다. (3) `inspect_manuscript_v59`에서는 violations를 별도로 병합하는 로직이 있어 다소 보완되지만, 기본 `inspect_manuscript` 경로에서는 Python CRITICAL이 완전히 무시된다.
- **Suggested fix direction**: Python critical_violations가 존재하면 LLM 결과의 decision에 관계없이 최소 MAJOR severity를 보장하거나, LLM 프롬프트에 Python 사전 검증 결과를 첨부하여 LLM이 이를 참조하도록 변경.

---

### TF-CM-16: `get_prev_manuscripts` window=5 vs Director limit=30 불일치 — INSIGHT

- **Location**: `continuity_manuscript.py:L357-L376` vs `director_continuity.py:L755`
- **Description**: `get_prev_manuscripts`의 기본 window는 5화이나, `check_manuscript_continuity_with_cache`의 기본 limit은 30화이다. 동일한 원고 연속성 검증 목적이지만 참조 범위가 6배 차이난다.
- **Evidence**:
```python
# continuity_manuscript.py L357
def get_prev_manuscripts(self, current_ep: int, window: int = 5) -> list[dict]:

# director_continuity.py L755
def check_manuscript_continuity_with_cache(self, ..., limit: int = 30, ...):
```
- **Impact**: ContinuityManuscriptValidator 경로에서는 최근 5화만 참조하므로, 6화 이전에 획득한 아이템이나 관계 변화를 추적하지 못한다. 특히 장기 연재에서 초반에 설정된 관계나 아이템이 후반에 참조될 때 누락될 수 있다. Director 경로는 30화를 참조하므로 동일 상황에서 더 정확한 검증이 가능하다.
- **Suggested fix direction**: window 기본값을 10-15로 상향하거나, PromptBuilder의 아이템 타임라인 캐시(`_item_timeline_cache`)와 통합하여 전체 에피소드 아이템 이력을 효율적으로 참조.


## 4. Summary Matrix

| ID | Title | Severity | Location | Category |
|----|-------|----------|----------|----------|
| TF-CM-01 | LLM 실패 시 fail-open PASS | CRITICAL | L327-L355 | Error Handling |
| TF-CM-02 | JSON 파싱 실패 시 PASS | CRITICAL | L293-L305 | Error Handling |
| TF-CM-03 | 사망/굴복 STATE_ORDER 누락 | CRITICAL | L1055-L1065 | Relationship Tracking |
| TF-CM-04 | 원고 절단 경계 정보 소실 | IMPORTANT | L841-L843 | Previous Manuscript Truncation |
| TF-CM-05 | 관계 추적 중복 + 상태 모델 불일치 | IMPORTANT | L509/L1043 | Relationship Tracking |
| TF-CM-06 | hud_history 데드 파라미터 | IMPORTANT | L216, L1164 | Cache/State |
| TF-CM-07 | 원고 excerpt 4,000자 절단 | IMPORTANT | L275 | Previous Manuscript Truncation |
| TF-CM-08 | _is_item_acquired 부분매칭 오탐 | IMPORTANT | L496-L507 | Item Timeline |
| TF-CM-09 | v59에서 entity_registry 미전달 | IMPORTANT | L1158-L1167 | Blueprint Compliance |
| TF-CM-10 | BP 키워드 매칭 허점 | IMPORTANT | L445-L464 | Blueprint Compliance |
| TF-CM-11 | find/rfind 비대칭 관계 탐지 | IMPORTANT | L543-L558 | Relationship Tracking |
| TF-CM-12 | 악역 키워드 글로벌 스캔 오탐 | INSIGHT | L620-L631 | Relationship Tracking |
| TF-CM-13 | _is_same_skill 과도한 부분매칭 | INSIGHT | L1015-L1037 | Item Timeline (Skill) |
| TF-CM-14 | prev_manuscripts 순서 미보장 | INSIGHT | L832-L850 | Cache/State |
| TF-CM-15 | Python CRITICAL → warnings 다운그레이드 | INSIGHT | L262-L323 | Error Handling |
| TF-CM-16 | window=5 vs limit=30 범위 불일치 | INSIGHT | L357/L755 | Cache/State |


## 5. 핵심 코드 참조 (Appendix)

### A. fail-open 반환 구조 (L327-355)

```python
except Exception as e:
    logging.warning(f" [ContinuityInspector] 원고 LLM 검증 실패: {e}")
    # ... (두 가지 분기 모두)
    return {
        "decision": "PASS",          # fail-open
        "severity": "MINOR",
        "degraded": True,
        "degraded_reason": str(e),
        # ...
    }
```

### B. 원고 절단 (L841-843)

```python
if len(content) > 1500:
    excerpt = content[:700] + "\n...(중략)...\n" + content[-500:]
else:
    excerpt = content
```

### C. STATE_KEYWORDS vs STATE_ORDER 불일치 (L1055-1065)

```python
STATE_KEYWORDS = {
    "사망": [...],     # STATE_ORDER에 없음
    "굴복": [...],     # STATE_ORDER에 없음
    "충성": [...],
    "경외": [...],
    "의심": [...],
    "무시": [...],
    "적대": [...]
}

STATE_ORDER = ["적대", "무시", "의심", "중립", "경외", "충성"]
#              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#  "중립"은 STATE_KEYWORDS에 없고, "사망"/"굴복"은 STATE_ORDER에 없음
```

### D. 두 관계 추적 메서드의 상태 모델 비교

| 속성 | `_check_relationship_jump` (L509) | `_track_relationship_history` (L1043) |
|------|----------------------------------|--------------------------------------|
| 상태 | 멸시/무시/의심/경외/충성 (5) | 사망/굴복/충성/경외/의심/무시/적대 (7) |
| 전환 | ALLOWED_TRANSITIONS (화이트리스트) | STATE_ORDER 거리 (선형) |
| 판정 | jump_distance ≥ 2 → MAJOR | jump_distance ≥ 2 → MAJOR, == 1 → INFO |
| NPC | GROUP_KEYWORDS (8) | NPC_KEYWORDS (14) |
| 회귀자 | `_regressor_suffix` 지원 | `_regressor_suffix` 지원 |
| fallback | 없음 (매칭 안 되면 skip) | "중립" (L1092) |

### E. 호출 경로별 검증 범위 비교

| 검증 항목 | `inspect_manuscript` | `inspect_manuscript_v59` | Director 경로 |
|-----------|---------------------|------------------------|---------------|
| Python 아이템 체크 | O | O (via base) | X |
| Python 관계 급변 | O (_check_relationship_jump) | O (base + _track_relationship_history) | X |
| Python 시간 흐름 | O | O (via base) | X |
| Python 악역 지능 | O | O (via base) | X |
| Python 몰입도 | O | O (via base) | X |
| LLM 연속성 검증 | O | O (via base) | O (별도 프롬프트) |
| Entity Registry | O (전달 시) | X (미전달) | X |
| 스킬 타임라인 | X | O | X |
| 참조 범위 | 외부 전달 (보통 5화) | 외부 전달 (보통 5화) | 30화 |
| fail 정책 | PASS (fail-open) | PASS (fail-open) | CONFLICT (fail-closed) |
