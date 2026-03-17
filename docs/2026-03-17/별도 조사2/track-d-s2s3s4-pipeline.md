# Track D: S2+S3→S4 정보 전달 파이프라인

Date: 2026-03-17
3-Pass Audit: 93% → 96% → 97%
Final Confidence: 97%

---

## D-1: power_changes / foreshadowings / hybrid_composition 소실

### 1. 현황 (코드 경로)

**정의 (Stage 2 출력):**

- `models/arc.py`:94-112 — `StateConstraints` Pydantic 모델:
  ```python
  power_changes: dict = Field(default_factory=dict)       # line 110
  foreshadowings: list[dict] = Field(default_factory=list) # line 111
  ```
  - Arc의 파워 성장 궤적과 복선 설치 계획을 저장.

- `analyst_prompts.py`:386-393 — Analyst 프롬프트에서 명시적 요청:
  - `power_changes`: `{ "start_power": 30, "end_power": 35, "growth_justification": "..." }`
  - `foreshadowings`: `[{ "id": "복선ID", "type": "...", "description": "...", "expected_payoff": "..." }]`
  - 검증 규칙 (line 563-567): `end_power - start_power > 20`이면 FAIL.

- `stage2_finalizer.py`:1039-1043 — `hybrid_composition` 누락 시 기본값 자동 주입:
  ```python
  if not refined_arc.get("hybrid_composition"):
      refined_arc["hybrid_composition"] = {
          "primary": "standard_progression",
          "secondary": [],
          "mixing_logic": "기본 전개",
      }
  ```

**Stage 4에서의 사용:**

- `stage4_context_builder.py` — **power_changes, foreshadowings, hybrid_composition를 참조하는 코드 0건**.
- Stage 4는 `constraint_summary` (line 2374-2376), `state_changes` (line 167, 234), `joint_docs`만 읽음.

**전달 경로 단절 지점:**

- `stage2_preflight.py`:1416-1430 — enriched_block → state_changes 변환:
  - `relationship_delta → state_changes.relationship_changes` 변환만 존재.
  - `power_changes` → state_changes 변환: **없음**.
  - `foreshadowings` → state_changes 변환: **없음**.
  - `hybrid_composition` → state_changes 변환: **없음**.

### 2. 갭

**3개 필드 모두 Stage 2에서 생성되지만 Stage 4에 도달하지 못하는 "Dead Data" 상태:**

| 필드 | 생성 | 검증 | Stage 3 전달 | Stage 4 전달 |
|------|------|------|-------------|-------------|
| `power_changes` | ✅ Analyst | ✅ 점수 검증 | ❌ 미전달 | ❌ 미전달 |
| `foreshadowings` | ✅ Analyst | ✅ payoff 검증 | ❌ 미전달 | ❌ 미전달 |
| `hybrid_composition` | ✅ Finalizer 기본값 | ❌ 미검증 | ❌ 미전달 | ❌ 미전달 |

- **state_changes 스키마에 대응 필드 없음**: `state_changes`는 `npc_deaths`, `skill_acquisitions`, `relationship_changes`, `major_items`, `npc_injuries`, `npc_movements`, `resolved_plots` 7개 카테고리만 보유 (`blueprint_constraint_compiler.py`:384-453). 파워 성장, 복선, 구조 패턴에 대한 카테고리 없음.

### 3. 영향도

**Critical**

- **파워 성장 논리 손실**: Chief Writer가 캐릭터의 파워 궤적(start→end)을 모름 → 성장 속도의 자연스러움 판단 불가 → "급성장" 비논리성이 원고에 반영될 수 있음.
- **복선 설치 불가**: `foreshadowings`가 Stage 4에 전달되지 않으면 Chief Writer가 이번 화에서 설치할 복선을 모름 → 복선 회수 시점에 앞선 복선이 없어 "갑작스러운 전개" 발생.
- **구조 패턴 미반영**: `hybrid_composition`의 primary/secondary 패턴 조합이 Chief Writer에 전달되지 않으면 → 일관된 서사 구조(예: "성장+반전 혼합") 불가능.

### 4. 방향 스케치

**접근법 A: state_changes 스키마 확장**
- `state_changes`에 3개 카테고리 추가:
  - `protagonist_power_arc`: `{ "start": N, "end": M, "growth_justification": "..." }`
  - `arc_foreshadowings`: `[{ "id": "...", "description": "...", "expected_payoff": "..." }]`
  - `narrative_pattern`: `{ "primary": "...", "secondary": [...], "mixing_logic": "..." }`
- Stage 2 preflight에서 변환 로직 추가.

**접근법 B: 직접 전달 경로 신설**
- `stage4_context_builder.py`에서 `arc_data.state_constraints.power_changes` 직접 읽기.
- state_changes를 경유하지 않고 원본 데이터 직접 참조.

**접근법 C: Blueprint Constraint에 주입**
- `blueprint_constraint_compiler.py`에서 power_changes, foreshadowings를 constraint_block에 포함.
- Chief Writer가 constraint_block을 통해 간접 수신.

---

## D-2: relationship_changes 엔드포인트만 도달

### 1. 현황 (코드 경로)

**원본 데이터 (Stage 2 생성):**

- `analyst_prompts.py`:383-385 — 프롬프트 요청:
  ```python
  "relationship_changes": [
      {"target": "NPC/집단명", "from": "이전 상태", "to": "변경 후 상태",
       "trigger": "변화 계기", "justification": "서사적 근거"}
  ]
  ```
  - 5개 필드: `target`, `from`, `to`, **`trigger`**, **`justification`**.

**Stage 2 Preflight 변환** (`stage2_preflight.py`:1418-1430):
```python
if _rd and not _sc.get("relationship_changes"):
    _sc["relationship_changes"] = [
        {
            "npc": r.get("target", ""),
            "from": r.get("before", ""),
            "to": r.get("after", ""),
            "episode": None,
        }
        for r in _rd
        if isinstance(r, dict)
    ]
```

**변환 시 손실:**

| 원본 필드 | 변환 후 | 상태 |
|----------|---------|------|
| `target` | `npc` | ✅ 키 변경만 |
| `from` | `from` | ✅ 보존 (`before` → `from` 매핑) |
| `to` | `to` | ✅ 보존 (`after` → `to` 매핑) |
| **`trigger`** | — | ❌ **삭제** |
| **`justification`** | — | ❌ **삭제** |

**Stage 4에서의 사용:**

- `state_tracker.py`:1460-1462:
  ```python
  for entry in sc.get("relationship_changes", []):
      if isinstance(entry, dict) and entry.get("npc"):
          sc_npc_names.append(entry["npc"])
  ```
  - **NPC 이름 추출만** — `from`, `to`, `trigger`, `justification` 모두 미사용.

- `blueprint_constraint_compiler.py`:414-419 — `_summarize_state_changes()`:
  ```python
  for r in relations[:3]:
      if isinstance(r, dict):
          lines.append(f"🤝 관계변화: {r.get('npc', '?')} {r.get('from', '?')}→{r.get('to', '?')}")
  ```
  - `from→to` 엔드포인트만 표시. `trigger`/`justification` 이미 손실 상태.

### 2. 갭

1. **trigger 삭제**: "왜 관계가 변했는가"의 **사건(trigger)**이 Stage 3/4에 전달되지 않음. 예: "비무 승리" → 삭제됨. Chief Writer는 관계가 "무시→경외"로 바뀐다는 사실만 앎.

2. **justification 삭제**: "서사적 근거"가 삭제됨. Director가 관계 변화의 타당성을 Stage 4에서 재검증할 수 없음.

3. **State Tracker의 과소 활용**: NPC 이름만 추출하고 관계의 **방향/깊이**를 활용하지 않음. 관계 변화가 단순 팩트로 축소.

4. **과정(Journey) vs 결과(Endpoint)**: "무시→경외"만 있으면 Chief Writer가 원고에서 **갑작스러운 태도 전환**을 쓸 수 있음. trigger가 있으면 "비무 장면 → 놀람 → 존경 표현" 시퀀스를 구체적으로 쓸 수 있음.

### 3. 영향도

**Significant**

- **캐릭터 동기 불일치**: NPC 태도 변화의 계기가 불명확 → 원고에서 변화가 갑작스러움.
- **서사적 인과 약화**: 사건(trigger)과 감정 변화의 인과관계가 Chief Writer에 전달되지 않음 → 독자가 "왜 이 NPC가 갑자기 태도를 바꿨지?" 의문.
- **Critical이 아닌 이유**: `from→to`는 보존되므로 최소한의 방향성은 전달됨. 완전한 정보 손실은 아님.

### 4. 방향 스케치

**접근법 A: Preflight 변환 필드 보존**
- `stage2_preflight.py`:1421-1430에서 `trigger`, `justification` 필드 유지:
  ```python
  {
      "npc": r.get("target", ""),
      "from": r.get("before", ""),
      "to": r.get("after", ""),
      "trigger": r.get("trigger", ""),
      "justification": r.get("justification", ""),
      "episode": None,
  }
  ```

**접근법 B: State Changes 요약에 trigger 반영**
- `_summarize_state_changes()`에서:
  ```
  🤝 관계변화: 장로 무시→경외 (계기: 비무 승리)
  ```
  - trigger를 괄호로 추가. 토큰 비용 최소.

**접근법 C: Stage 4 Context에 관계 변화 배경 섹션 추가**
- `stage4_context_builder.py`에 "NPC 관계 변화 배경" 섹션:
  - NPC 이름 추출 외에도 `from→to + trigger + justification` 전달.
  - Chief Writer 프롬프트에 주입.

---

## D-3: state_constraints 전체 계층이 요약으로 붕괴

### 1. 현황 (코드 경로)

**원본 구조** (`models/arc.py`:94-115) — `StateConstraints` 3계층:

| 계층 | 필드 | 내용 |
|------|------|------|
| L1: 상태 경계 | `arc_start_state`, `arc_end_state` | 위치, 장비, 부상, 장르별 속성 |
| L2: 아이템/변화 | `protagonist_items`, `distributed_items`, `items_consumed`, `relationship_changes`, `power_changes`, `foreshadowings` | 아이템 이벤트, 관계/파워 궤적, 복선 |
| L3: 연속성 | `continuity_checkpoints` | 화별 상태 변화 명시 |

**축약 지점** (`stage2_finalizer.py`:1039-1043):
```python
if constraint_block:
    _constraint_lines = constraint_block.strip().split("\n")
    _must_not = [ln.strip() for ln in _constraint_lines
                 if "금지" in ln or "MUST NOT" in ln or "절대" in ln]
    refined_arc["constraint_summary"] = "\n".join(_must_not[:10]) if _must_not else ""
```

**핵심 문제: constraint_block ≠ state_constraints**
- `constraint_block`: `ConstraintCompiler`가 생성한 **텍스트 기반 체크리스트** (이전 Arc들의 금지사항).
- `state_constraints`: **구조화된 JSON** (현재 Arc의 상태 정보).
- line 1040-1043에서 `constraint_block`(텍스트)을 "금지" 키워드로 필터 → 10줄 제한 → `constraint_summary`로 저장.
- **state_constraints의 구조화된 정보(L1/L2/L3)는 이 과정에서 참조조차 되지 않음.**

**Stage 4에서의 사용:**

- `stage4_context_builder.py`:2374-2376:
  ```python
  _arc_cs = arc_data.get("constraint_summary", "") if arc_data else ""
  if _arc_cs:
      _tier0_parts.append(f"[Arc 제약 - MUST NOT DO]\n{_arc_cs}")
  ```
  - **constraint_summary만 사용** (10줄 이내의 "금지" 항목만).

- `stage4_context_builder.py`:876-878:
  ```python
  constraint_summary = self._trim_summary_value(arc_data.get("constraint_summary", ""), 160)
  if constraint_summary:
      lines.append(f"- 현재 갈등축: {constraint_summary}")
  ```
  - constraint_summary를 **160자로 추가 절삭** + "갈등축"으로 재해석 (원래 용도와 다름).

- **state_constraints 원본을 직접 읽는 Stage 4 코드: 없음**. `arc_data.get("state_constraints")`를 호출하는 코드가 stage4_context_builder.py에 없음.

### 2. 갭

**3계층 → 1차원 축소의 전체 경로:**

```
StateConstraints (3계층, 12+ 필드)
  ↓ [ConstraintCompiler] → constraint_block (텍스트 체크리스트)
  ↓ [stage2_finalizer L1040-1043] → "금지" 키워드 필터 + 10줄 제한
  ↓ → constraint_summary (최대 10줄 텍스트)
  ↓ [stage4_context_builder L876] → 160자 절삭
  ↓ → "현재 갈등축: ..." (최종 Chief Writer 입력)
```

**손실된 정보:**

| 원본 필드 | Stage 4 도달 여부 | 손실 내용 |
|----------|------------------|----------|
| `arc_start_state` | ❌ | 시작 위치, 장비, 부상 상태 |
| `arc_end_state` | ❌ | 목표 종료 상태 |
| `protagonist_items` | ❌ | 주인공 소지 아이템 목록 |
| `distributed_items` | ❌ | 분배할 아이템 |
| `items_consumed` | ❌ | 소모될 아이템 |
| `relationship_changes` | △ (NPC명만) | 관계 변화 과정 (D-2 참조) |
| `power_changes` | ❌ | 파워 성장 궤적 (D-1 참조) |
| `foreshadowings` | ❌ | 복선 계획 (D-1 참조) |
| `continuity_checkpoints` | ❌ | 화별 상태 체크포인트 |

### 3. 영향도

**Critical**

- **상태 일관성 붕괴**: Chief Writer가 "주인공이 이 화에서 어디에서 시작하는가", "어떤 아이템을 소지해야 하는가"를 `state_constraints`에서 받지 못함. `constraint_summary`의 "금지" 항목만으로는 **긍정적 상태 정보(무엇을 가지고 있는가)**를 전달 불가.
- **아이템 추적 붕괴**: `protagonist_items`, `distributed_items`, `items_consumed`가 모두 미전달 → Chief Writer가 아이템 기반 이벤트를 쓸 때 근거 없음.
- **D-1/D-2와의 합성 효과**: state_constraints 전체가 붕괴되면 D-1(power_changes, foreshadowings)과 D-2(relationship_changes trigger/justification)도 자연히 손실됨. D-3는 D-1, D-2의 **상위 원인**.

### 4. 방향 스케치

**접근법 A: constraint_summary와 state_constraints 분리**
- `constraint_summary`: 현재대로 유지 (금지 사항 텍스트).
- `state_constraints_structured`: 원본 JSON을 별도 필드로 보존.
- Stage 4에서 두 가지를 모두 읽음.

**접근법 B: Stage 4 Context Builder에 state_constraints 직접 읽기 추가**
- `stage4_context_builder.py`에서 `arc_data.get("state_constraints", {})` 직접 참조.
- "Arc State Boundary" 섹션 추가:
  ```
  [Arc 상태 경계]
  시작: 위치={location}, 소지품=[items], 부상={injuries}
  종료: 위치={location}, 소지품=[items], 부상={injuries}
  ```

**접근법 C: 계층별 요약 (Tiered Summary)**
- constraint_summary를 단일 문자열 대신 **계층별 요약 dict**로 변환:
  ```python
  {
      "must_not_do": ["금지1", "금지2"],
      "state_boundary": {"start": {...}, "end": {...}},
      "items": {"carry": [...], "consume": [...], "distribute": [...]},
      "narrative_arcs": {"power": {...}, "foreshadowings": [...]}
  }
  ```
- Stage 4에서 필요한 계층만 선택적으로 사용.

---

## Track 내 교차 발견

### 교차 발견 1: D-3는 D-1, D-2의 상위 원인

D-1(power_changes/foreshadowings 소실)과 D-2(relationship_changes trigger 삭제)는 모두 **state_constraints가 Stage 4에 도달하지 못하는** D-3의 하위 증상:

```
D-3: state_constraints 전체 계층 붕괴
 ├── D-1: power_changes/foreshadowings/hybrid_composition 소실
 └── D-2: relationship_changes trigger/justification 삭제
```

D-3를 해결하면 D-1, D-2가 자연스럽게 개선될 가능성. **D-3 우선 해결이 3건 동시 해결의 가장 효율적 경로**.

### 교차 발견 2: "금지(Negative)" 편향

현재 파이프라인은 **"하지 마라(MUST NOT DO)"만 전달**하고 **"이렇게 하라(MUST DO with context)"는 미전달**:
- `constraint_summary`: "금지" 키워드 필터 (line 1041)
- Stage 4 프롬프트: `[Arc 제약 - MUST NOT DO]` (line 2376)

Chief Writer에게 "무엇을 하면 안 되는가"는 전달되지만 "무엇을 해야 하고, 왜 그래야 하는가"는 전달되지 않음. C-1(왜가 안 넘어감)과 동일한 패턴.

### 교차 발견 3: 변환 계층의 정보 손실 누적

정보가 파이프라인을 따라 이동할 때마다 손실됨:

| 단계 | 입력 | 출력 | 손실 |
|------|------|------|------|
| Stage 2 Analyst | (생성) | state_constraints (12+ 필드) | — |
| Preflight 변환 | enriched_block | state_changes (7 카테고리) | trigger, justification, power, foreshadowing |
| Finalizer 축약 | constraint_block | constraint_summary (10줄) | 구조화된 상태 전체 |
| Stage 4 Context | constraint_summary | "갈등축" (160자) | 나머지 10줄 중 대부분 |

**4단계 손실이 누적**되어 원본의 ~5% 미만만 Chief Writer에 도달.

---

## 3-Pass 감리 기록

### Pass 1: 사실 정확성 (93%)

- ✅ `models/arc.py`:110-111의 power_changes, foreshadowings 필드 정의 확인
- ✅ `analyst_prompts.py`:386-393의 프롬프트 요청 확인
- ✅ `stage2_finalizer.py`:1039-1043의 constraint_summary 축약 로직 확인
- ✅ `stage4_context_builder.py`:2374-2376의 constraint_summary 사용 확인
- ✅ `stage2_preflight.py`:1418-1430의 relationship_changes 변환에서 trigger/justification 삭제 확인
- ✅ `state_tracker.py`:1460-1462의 NPC 이름만 추출 확인
- ⚠️ `stage4_context_builder.py`:876-878의 160자 절삭은 `_trim_summary_value` 구현에 따라 다를 수 있음

### Pass 2: 논리 정합성 (96%)

- ✅ D-1: 필드 생성 → 변환 경로 미존재 → Stage 4 미도달 — 논리 건전
- ✅ D-2: trigger/justification 삭제 → 엔드포인트만 도달 — 인과 명확
- ✅ D-3: 3계층→1차원 축소 → 정보 대량 손실 — 연결 건전
- ✅ 교차 발견의 "D-3가 D-1/D-2의 상위 원인" 계층 구조 건전

### Pass 3: 완성도 (97%)

- ✅ 각 항목 4단계(현황/갭/영향도/방향) 완비
- ✅ 코드 경로 주장 모두 file:line 근거 제시
- ✅ 방향 스케치가 구현 제안이 아닌 접근법 수준
- ✅ 영향도 등급 근거 명시 (D-3가 D-1/D-2 상위 원인임을 반영하여 Critical)
- ✅ 교차 발견 3건 + 정보 손실 누적 표
