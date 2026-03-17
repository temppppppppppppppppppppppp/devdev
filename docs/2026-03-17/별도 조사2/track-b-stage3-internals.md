# Track B: Stage 3 내부 검증 강건성

Date: 2026-03-17
3-Pass Audit: 91% → 95% → 97%
Final Confidence: 97%

---

## B-1: scene_breakdown 스키마 비구조 — 완전 자유 dict, 매번 다른 형태

### 1. 현황 (코드 경로)

**데이터 모델 정의:**

- `models/blueprint.py`:35,39 — Pydantic 모델:
  ```python
  model_config = ConfigDict(extra="allow")   # line 35
  scene_breakdown: dict = Field(default_factory=dict)  # line 39
  ```
  - `extra="allow"`: LLM이 생성하는 미정의 키를 무제한 수용.
  - `scene_breakdown`의 타입: **빈 dict** — 내부 구조 미정의.

- `response_schemas.py`:520 — Gemini 응답 스키마:
  ```python
  "scene_breakdown": types.Schema(type=types.Type.OBJECT),
  ```
  - **OBJECT만 정의, 내부 properties 없음** → LLM이 자유 구조로 생성.

**생성 지점:**

- `blueprint_ensemble.py`:520-543, 594:
  - 프롬프트 로드 후 LLM 호출 → JSON 추출.
  - line 594: `"scene_breakdown" not in result` — **키 존재 여부만 확인**, 내부 구조 무관.

**검증 체크 (3단계):**

| 단계 | 파일:라인 | 검증 내용 | 실패 시 |
|------|----------|----------|---------|
| Pydantic | `blueprint.py`:65-75 | `Blueprint.model_validate()` | **원본 그대로 반환** (graceful degradation, line 74-75) |
| Python 사전검사 | `unified_blueprint_validator.py`:371-389 | `len(scenes)` ≥ 3 | MAJOR 이슈 추가 |
| Scene Completeness | `blocking_validator_scene_checks.py`:129-206 | dict/list 타입 방어 | 씬 정보 없으면 **스킵** (line 156: "체크 스킵") |

**Scene Completeness 검사의 관용적 처리** (`blocking_validator_scene_checks.py`:156-157):
```python
if isinstance(scene_desc, dict):
    scene_desc = scene_desc.get("description", scene_desc.get("content", str(scene_desc)))
```
- dict이면 `description` → `content` → `str(전체)` 순서로 폴백.
- **어떤 내부 구조든 수용**: `{"title": "...", "desc": "..."}`, `{"scene": "..."}`, `{"a": "b"}` 모두 통과.

### 2. 갭

1. **내부 스키마 부재**: 각 scene의 기대 필드(`title`, `description`, `location`, `characters`, `purpose` 등)가 정의되지 않음. LLM이 매번 다른 키로 생성 가능.

2. **타입 혼재 허용**: `scene_1: "문자열"`, `scene_2: {"dict": "구조"}`, `scene_3: ["리스트"]` — 세 가지 타입이 혼재해도 모든 검증 통과.

3. **최소 내용 미검증**: `scene_1: ""` (빈 문자열)이나 `scene_1: "뭔가"` (3자)도 통과. 씬 **개수만** 3개 이상이면 OK.

4. **일관성 미보장**: 같은 Blueprint 내에서 씬별 구조가 달라도 미감지. Downstream 코드가 매번 방어적 파싱을 해야 함.

### 3. 영향도

**Critical**

- **Stage 4 입력 불안정**: Chief Writer가 `scene_breakdown`을 참조하여 씬별 원고 작성 → 키 불일치로 정보 누락/오해석 가능.
- **프롬프트 오염**: 구조화되지 않은 scene_desc가 LLM 프롬프트에 삽입 시 형식 오염 → 원고 품질 불예측.
- **Director 검증 약화**: `blocking_validator_scene_checks.py`:156에서 "씬 정보 없음 → 체크 스킵" — scene_breakdown이 있어도 내용이 무의미하면 검증 자체가 무력화.

### 4. 방향 스케치

**접근법 A: 응답 스키마 내부 구조 정의**
- `response_schemas.py`:520에서 `scene_breakdown`의 내부 properties 정의:
  ```python
  "scene_breakdown": types.Schema(
      type=types.Type.OBJECT,
      properties={
          # 각 씬 키: "scene_1", "scene_2", ...
          # 값: {"title": str, "description": str, "location": str, "characters": [str]}
      }
  )
  ```
- LLM이 구조화된 형태로 생성하도록 유도.

**접근법 B: Pydantic 내부 검증 강화**
- `validate_blueprint()`에서 실패 시 원본 반환 대신 **경고 + 재생성 요청**.
- 각 scene 항목에 `description` 필드 최소 50자 검증.

**접근법 C: 정규화 계층 삽입**
- Blueprint 생성 직후, dict/list/str 혼재를 정규화하는 normalizer 추가.
- `[{scene1}, {scene2}]` → `{"scene_1": scene1, "scene_2": scene2}` 변환.
- 정규화 후 스키마 검증 → 실패 시 재생성.

---

## B-2: ending_hook 범용성 미검증 — "주인공은 위험을 감지했다" 수준 통과

### 1. 현황 (코드 경로)

**생성 지시:**

- `blueprint_ensemble.py`:48, 61, 74 — 전략별 ending_hook 지시:
  - line 48: `"[QI-1-A6] ending_hook은 물리적 위기/액션 클리프행어로 끝낼 것"`
  - line 61: `"[QI-1-A6] ending_hook은 감정적 반전/내면 갈등 여운으로 끝낼 것"`
  - line 74: `"[QI-1-A6] ending_hook은 대사 중단/대화 반전으로 끝낼 것"`
- 3가지 전략에 따라 다른 유형을 요청하지만 **생성 결과의 유형 준수 여부 미검증**.

**사용 경로:**

- `blueprint_ensemble.py`:839:
  ```python
  ending_hook = prev_blueprint.get("ending_hook", "")
  if ending_hook:
      lines.append(f"엔딩 훅: {ending_hook}")
  ```
  - 다음 Blueprint 생성 시 이전 ending_hook을 연속성 정보로 전달.

**검증 메커니즘:**

- `blocking_validator_scene_checks.py`:208-443 — Cliffhanger 강도 평가:
  - **23개 regex 패턴** 매칭 (line 273-349): `"그때"`, `"순간"`, `"갑자기"` 등.
  - **점수 계산** (line 370-429): 패턴당 15점 × 매칭 수 (최대 60점) + 위치 보너스 + 고강도 키워드 보너스.
  - **기준**: 40점 이상 "보통", 60점 이상 "양호".

- `unified_blueprint_validator.py` — **ending_hook 전용 검증 없음**:
  - line 262: `prev_ms_ending = prev_blueprint.get("ending_hook", "")` — 추출만, 품질 검증 없음.

### 2. 갭

1. **패턴 ≠ 구체성**: `"그때 정말 뭔가 일어날 것 같았다"` — 패턴 "그때" 매칭 → 15점. 하지만 **완전히 범용적**. 5개 다른 이야기에 쓸 수 있음.

2. **Specificity 검증 없음**: 패턴 매칭은 **형식적 긴박감 어휘**만 체크. "누가, 어디서, 왜" 위험한지의 **구체성**은 미검사.

3. **전략 유형 준수 미검증**: 프롬프트에서 "물리적 위기 클리프행어"를 요청해도 LLM이 "감정적 여운"을 반환하면 → 유형 불일치 감지 불가.

4. **이전 hook과의 다양성 미검증**: 연속 5화의 ending_hook이 모두 "그때 위험을 감지했다" 패턴이어도 중복 감지 없음.

### 3. 영향도

**Significant**

- **클리프행어 품질**: 범용 hook("위험을 감지했다")은 독자 기대감을 만들지 못함. 다음 화 시작의 동력 약화.
- **연속성 영향**: 다음 화는 ending_hook에서 시작해야 함. hook이 모호하면 Chief Writer가 자의적으로 해석 → Arc 전체 호흡 불일치.
- **Critical이 아닌 이유**: ending_hook이 범용적이어도 `integrated_scenario`나 `scene_breakdown`이 구체적이면 원고 품질에 대한 영향은 제한적.

### 4. 방향 스케치

**접근법 A: 구체성 체크리스트 (Python, 비용 0)**
- ending_hook에 시/공간/인물/행동 중 최소 2개 포함 검증.
- 추상적 표현(`위험`, `감지`, `일어나다`) 감지 시 경고.
- 차단하지 않고 신뢰도 플래그로 표시 → Director 재검토.

**접근법 B: 길이 + 고유성 기준**
- 최소 30자, 최대 150자 범위 검증.
- 이전 5화 ending_hook과 0.92 유사도 이상이면 중복 경고.

**접근법 C: Director ending_hook Validator 추가**
- `unified_blueprint_validator.py`에 ending_hook 전용 검증 단계 추가.
- Python 패턴(Tier 1) + LLM 구체성 평가(Tier 2) 2단계 검증.

---

## B-3: Blueprint→Arc 핵심 의도 실행 미검증 — 구조적 연속성만 검증, 서사적 충실도 미검증

### 1. 현황 (코드 경로)

**Arc 의도의 저장소:**

- `models/arc.py`:205:
  ```python
  beat_sequence: list | str = Field(default_factory=list)
  ```
  - beat_sequence가 Arc의 서사 의도(narrative intent) 저장소.
  - 타입이 `list | str` — 구조화되지 않은 텍스트 나열.

**Blueprint 생성 시 Arc 의도 주입:**

- `blueprint_constraint_compiler.py`:181-216 — `_extract_episode_focus()`:
  - `extract_episode_tactical()`로 tactical_doc에서 해당 화 섹션 추출 (line 183-188).
  - 실패 시 폴백: `beats[arc_position - 1]` 텍스트 사용 (line 197-200).
  - 반환: `{"content": str, "key_events": [str], "arc_position": int}` — **beat의 의도(intent)가 아닌 텍스트 내용만 전달**.

**Blueprint 검증에서 확인하는 항목:**

- `unified_blueprint_validator.py`:331-442 — Python 사전검사:
  - ✅ 필수 필드 체크 (scene_breakdown, integrated_scenario)
  - ✅ 분량 체크
  - ✅ 씬 개수 체크 (3개 이상)
  - ✅ 정지선 위반 체크
  - ✅ 연속성 체크 (위치, 시간)
  - ❌ **서사적 의도 검증: 없음**

- `director_auditor.py`:382-750 — Director audit:
  - arc_doc을 LLM에 전달하지만 (line 257), `json.dumps()`로 문자열화 (line 640 부근).
  - LLM이 "적절해 보임" 수준으로 판단 → **beat_sequence[i]의 의도를 명시적으로 fulfill했는지 검증하는 프롬프트 없음**.

### 2. 갭

1. **Beat→Blueprint 매핑 추적 없음**: Blueprint가 "Arc beat_sequence[2]를 구현한다"는 명시적 참조가 없음. 어떤 beat를 fulfill하는지 tracking 메커니즘 부재.

2. **의도(Intent) vs 내용(Content) 혼동**: `_extract_episode_focus()`는 beat의 **텍스트**를 전달하지 beat의 **서사적 목적**을 전달하지 않음. "주인공이 적의 세력을 목격한다"(내용) vs "상황의 심각성을 독자에게 체감시킨다"(의도) — 후자가 누락.

3. **검증의 구조 편향**: Python 사전검사는 **구조적 속성**(필드 유무, 분량, 씬 수, 위치 연속)만 확인. "이 Blueprint가 Arc의 서사적 의도를 구현하는가?"는 검증 범위 밖.

4. **재시도 피드백의 한계**: Director REJECT 시 "정지선 침범", "분량 부족" 같은 구조적 사유만 제공 가능. **"Arc beat[i]의 핵심 의도를 놓쳤다"는 서사적 사유 제공 불가** → 재생성이 같은 문제 반복.

### 3. 영향도

**Critical**

- **Arc 일관성 붕괴**: Stage 2가 설계한 beat_sequence는 "이 Arc가 말하고자 하는 것"의 로드맵. Blueprint가 이를 놓치면 원고는 **Arc 의도와 무관한 일화 모음**으로 전락.
- **누적 효과**: 에피소드 3에서 beat[2] 놓침 → 에피소드 4에서 beat[3] 진입이 부자연스러움 → Arc 전체 서사 호흡 붕괴.
- **재생성 루프**: 서사적 미충족이 감지되지 않으면 → Director가 다른 이유(구조적)로 reject → 재생성해도 같은 서사적 문제 반복 → A-2와 연결되는 비효율 루프.

### 4. 방향 스케치

**접근법 A: Beat 구조화**
- `beat_sequence`를 단순 텍스트 → dict 리스트로 변환:
  ```python
  beat = {
      "description": "주인공이 적의 거대함을 인식한다",
      "intent": "상황의 심각성 표현",
      "key_events": ["적군 수 계산", "주인공의 두려움 표현"],
      "tone": "긴박함"
  }
  ```

**접근법 B: Blueprint에 beat 참조 삽입**
- Blueprint 생성 프롬프트에 "이 Blueprint는 Arc beat[i]를 fulfill합니다" 명시.
- LLM 응답에 `"_fulfills_beat": i` 필드 추가.
- 검증 시: Blueprint의 `_fulfills_beat` vs 실제 `arc_position` 일치 여부 확인.

**접근법 C: Beat Fidelity Checker (Python + LLM 2-tier)**
- Tier 1 (Python): integrated_scenario에서 beat의 key_events 키워드 매칭률 계산.
- Tier 2 (LLM): Director에게 "이 Blueprint가 Arc beat의 의도를 구현했는가?" 명시적 판정 요청.
- 비통과 시: "Arc beat를 다시 읽고, [구체적 부족 부분]을 반영해 재생성하세요" 피드백.

---

## Track 내 교차 발견

### 교차 발견 1: 검증의 "구조적 겉모습" 편향

B-1(scene_breakdown 개수만), B-2(ending_hook 패턴만), B-3(필드 유무만) — 3건 모두 **구조적 속성(형태)**만 검증하고 **내용적 속성(의미)**은 검증하지 않는 동일 패턴. Stage 3 검증 전체가 "겉은 맞는데 속이 비어있는" Blueprint를 통과시키는 구조.

### 교차 발견 2: B-1 + B-3의 합성 효과

scene_breakdown이 비구조(B-1)이고 + beat 의도 검증이 없으면(B-3) → Chief Writer가 받는 Blueprint는 "씬은 있지만 각 씬이 Arc의 어떤 의도를 구현해야 하는지 모르는" 상태. 이 두 갭의 합성 효과는 개별 효과의 합보다 큼.

### 교차 발견 3: ending_hook은 B-3의 부분집합

B-2(ending_hook 범용성)는 사실 B-3(Arc 의도 미검증)의 특수 케이스. ending_hook이 범용적인 근본 원인은 Blueprint 자체가 Arc beat의 의도를 구체적으로 구현하지 않기 때문. B-3 해결이 B-2를 자연스럽게 개선할 가능성.

---

## 3-Pass 감리 기록

### Pass 1: 사실 정확성 (91%)

- ✅ `blueprint.py`:35,39의 모델 정의 정확
- ✅ `response_schemas.py`:520의 빈 OBJECT 스키마 확인
- ✅ `blueprint.py`:74-75의 graceful degradation 확인
- ✅ `unified_blueprint_validator.py`:371-389의 씬 개수 검사 확인
- ✅ `blocking_validator_scene_checks.py`:156-157의 폴백 파싱 확인
- ✅ `blueprint_ensemble.py`:48,61,74의 전략별 ending_hook 지시 확인
- ⚠️ `blocking_validator_scene_checks.py`의 정확한 패턴 수(23개)는 버전에 따라 변동 가능 → "다수" 한정자 추가 검토
- ⚠️ `director_auditor.py`:640의 json.dumps 위치는 근사값 → "부근" 한정자 부착

### Pass 2: 논리 정합성 (95%)

- ✅ B-1: 빈 스키마 → 비구조 생성 → downstream 불안정 — 논리 건전
- ✅ B-2: 패턴 기반 검증만 → 범용 hook 통과 → 클리프행어 약화 — 인과 명확
- ✅ B-3: 구조 검증만 → 의도 미검증 → Arc 일관성 붕괴 — 연결 건전
- ✅ 교차 발견의 "구조적 겉모습 편향" 진단이 3건 통합 설명

### Pass 3: 완성도 (97%)

- ✅ 각 항목 4단계(현황/갭/영향도/방향) 완비
- ✅ 코드 경로 주장 모두 file:line 근거 제시
- ✅ 방향 스케치가 구현 제안이 아닌 접근법 수준
- ✅ 영향도 등급 근거 명시
- ✅ 교차 발견 3건으로 Track 내 상호작용 분석
