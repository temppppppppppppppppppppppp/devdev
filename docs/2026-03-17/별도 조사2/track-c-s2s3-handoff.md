# Track C: S2→S3 핸드오프 정보 충실도

Date: 2026-03-17
3-Pass Audit: 92% → 95% → 97%
Final Confidence: 97%

---

## C-1: constraint_compiler가 operational만 추출 — "왜"가 안 넘어감

### 1. 현황 (코드 경로)

Stage 2→3 핸드오프에 관여하는 Constraint Compiler는 **두 개**:

| 컴파일러 | 역할 | 소비자 |
|----------|------|--------|
| `ConstraintCompiler` (`constraint_compiler.py`) | Arc 간 제약 (이전 Arc→현재 Arc) | Stage 2 Analyst |
| `BlueprintConstraintCompiler` (`blueprint_constraint_compiler.py`) | 에피소드 간 제약 (Arc 내부) | Stage 3 Blueprint |

**ConstraintCompiler** (`constraint_compiler.py`):

- `_collect_all_items()` (line 92-149): `state_constraints.items_acquired`, `joint_docs.physical_inventory` 구조화 필드 + regex 패턴 `획득|얻|받|손에` (line 135) 스캔. **획득 사실만 기록**, 획득 이유/서사적 맥락 없음.
- `_collect_all_grants()` (line 151-187): `state_constraints.grants_received` + regex `하사|수여|받|얻` (line 180). 수여자(grantor) 이름은 추출하지만 **수여 의도/정치적 맥락** 없음.
- `_extract_current_state()` (line 189-242): `state_extractor_result`에서 location, injuries, internal_energy, equipment, world_state 추출. **world_state**는 `next_arc_constraints.must_start_with` (line 214)만 참조 — 단일 문자열, 인과 체인 없음.
- `_generate_constraint_checklist()` (line 244-349+): SECTION 0 (절대 금지), SECTION 1 (MUST NOT DO), SECTION 2 (INHERITED STATE) 구조. **모든 섹션이 operational fact만 나열** — "왜 이 제약이 존재하는가" 설명 없음.

**BlueprintConstraintCompiler** (`blueprint_constraint_compiler.py`):

- `_extract_episode_focus()` (line 181-216): `extract_episode_tactical()` 호출 → 원문 텍스트 반환. `key_events` 리스트는 텍스트 줄 단위 추출 (line 204-210). **이벤트의 서사적 목적 필드 없음**.
- `_summarize_state_changes()` (line 371-455): NPC 사망, 무공 습득, 관계 변화 등을 이모지 + 팩트 문자열로 변환. 예: `"⚠️ 사망 NPC: X(EP5, 원인: 독살) → 이후 등장 금지"` (line 400). **사망의 서사적 의미(복수 동기, 세력 균형 변화 등) 없음**.
- `compile_to_prompt()` (line 98-179): 최종 프롬프트 문자열 생성. `[V63] ARC 제약 (MUST NOT DO)` (line 166)와 `[V63.2] ARC 상태 변화` (line 173)를 포함하지만 **모두 operational fact 포맷**.

### 2. 갭

**핵심 갭: "Rationale Channel" 부재**

1. **인과 체인(Causal Chain) 미전달**: Arc 설계자가 "주인공이 부상 상태로 시작해야 함"이라는 제약을 건 이유(예: "취약성 Arc가 캐릭터 성장의 핵심")가 **어디에도 캡처되지 않음**. Stage 3 Blueprint 생성자는 제약의 존재는 알지만 **의도**를 모름.

2. **테마/블록 맥락 미활용**: `enriched_block`의 `block_theme`, `arc_theme` 필드가 constraint compilation 경로에서 **참조되지 않음**. 이 정보는 Stage 2 내부에서만 소비되고 Stage 3로 넘어가지 않음.

3. **state_extractor_result의 의도 정보 미활용**: `_extract_current_state()` (line 214)가 `next_arc_constraints.must_start_with`만 가져옴. `state_extractor_result`에 담긴 더 풍부한 맥락(예: `next_arc_constraints`의 다른 하위 필드들)이 **무시됨**.

4. **제약의 "유형" 미분류**: 현재 제약은 모두 동일한 포맷으로 나열됨. "Arc 3에서 습득한 교훈 기반 제약(EARNED LIMIT)"인지 "설정 단계의 셋업(SETUP PAYOFF)"인지 구분 불가.

### 3. 영향도

**Critical**

- **Stage 4 산출물 직접 영향**: Chief Writer가 제약의 의도를 모르면 **표면적 준수**(아이템을 안 쓰기)는 하지만 **서사적 준수**(아이템 부재가 만드는 긴장감)는 달성 불가.
- **Director 판단력 약화**: Director가 제약 위반을 감지해도 "왜 이 제약이 중요한지" 설명 불가 → Chief Writer에게 전달하는 수정 지시가 피상적.
- **캐릭터 동기 불일치**: 주인공의 감정 상태/목표의 근거가 제약에 없으면 Stage 4 원고에서 **다른 동기 부여**를 만들어낼 수 있음 (예: 부상 상태인데 용맹하게 행동 vs 신중하게 행동 — 의도에 따라 다름).

### 4. 방향 스케치

**접근법 A: Rationale 필드 추가**
- 각 제약 항목에 `rationale` 필드 추가. `arc_theme` / `block_theme`에서 추출.
- 예: `{ "item_forbidden": "고대검", "rationale": "Arc 3에서 지혜>무력 교훈 확립 — SETUP PAYOFF" }`

**접근법 B: 제약 유형 태깅**
- 제약을 `[EARNED_LIMIT]`, `[THEMATIC_GATE]`, `[SETUP_PAYOFF]`, `[HARD_RULE]`로 분류.
- 프롬프트에서: "❌ 고대검 (Arc 3 교훈: 지혜>무력) — SETUP PAYOFF. 재등장 시 Arc 3의 서사 작업 훼손"

**접근법 C: State Changes → Causal Event Summary**
- `_summarize_state_changes()`에서 각 이벤트에 `why` 필드 추가 (tactical_doc에서 원인 문장 추출).
- 토큰 예산: 이벤트당 50-100자 rationale.

---

## C-2: stop_line 300자 절삭 — 다음 화 정보 제한

### 1. 현황 (코드 경로)

**정지선 추출**: `BlueprintConstraintCompiler._extract_stop_line()` (`blueprint_constraint_compiler.py`:218-259)

세 개의 추출 경로:

1. **episode_details 경로** (line 231-239): `arc_data.episode_details`에서 `next_ep`에 해당하는 항목의 `details` 리스트를 세미콜론으로 join → **`[:300]` 하드 절삭** (line 238).
2. **regex 폴백** (line 241-249): `_EPISODE_HEADER_PATTERNS` 4개 패턴으로 `tactical_doc`에서 다음 화 섹션 매칭 → **`[:300]` 하드 절삭** (line 247).
3. **beat_sequence 폴백** (line 251-258): `beats[arc_position]`을 직접 반환 → **절삭 없음** (단, beat 자체가 짧은 경우 많음).

**프롬프트 주입**: `compile_to_prompt()` (line 131):
```python
lines.append(f"다음 화 예고: {stop_line['content'][:200]}")
```
→ **이중 절삭**: 300자 → 200자. 실질적으로 Stage 3가 받는 정지선은 **최대 200자**.

### 2. 갭

1. **정보 손실 (Quantitative)**: 일반적 에피소드 전술 내용은 500-1000자. 200자 제한은 **2-3개 플롯 비트만 전달 가능**. 복잡한 에피소드(대치+반전+새 인물 등장 등)의 핵심 이벤트가 누락됨.

2. **의미론적 절삭 불가 (Blind Truncation)**: `[:300]`은 문자 수 기반 절삭 → 문장 중간에서 끊길 수 있음. 예: "의원이 비수를 들어 암살 시도 → 주인공이 관광국 부총장으로 외교담" (61자에서 절삭) → 의미 불완전.

3. **정지선 목적(Purpose) 미전달**: 정지선은 "다음 화에서 뭘 하는지"의 **사실(What)**만 전달. "왜 이 이벤트가 다음 화여야 하는지"의 **목적(Why)**은 없음.

4. **Chief Writer 맥락 부족**: 정지선이 모호하면 Chief Writer가 **의도치 않게 다음 화 내용을 일부 소비**할 수 있음. 예: "주인공이 정체를 드러냄"이 정지선인데 200자 절삭으로 "주인공이 드러"만 전달되면 → Chief Writer가 이번 화에서 "주인공이 드러내는" 다른 뭔가를 쓸 수 있음.

### 3. 영향도

**Significant**

- **정지선 위반 위험 증가**: 모호한 정지선은 Chief Writer가 다음 화 영역을 침범할 확률을 높임. Director가 이를 잡아도 **어디까지가 위반인지** 판단 기준이 불명확.
- **Arc 이벤트 배분 왜곡**: 다음 화의 전체 밀도를 모르면 이번 화에 이벤트를 과잉 배치하거나 과소 배치 가능.
- **Director 수정 지시 품질 저하**: Director의 reject 사유가 "정지선 위반"이어도 정지선 자체가 200자밖에 없어서 **구체적 위반 지점 지적 불가**.

### 4. 방향 스케치

**접근법 A: 절삭 한도 상향**
- `_extract_stop_line()`: 300 → 600자. `compile_to_prompt()`: 200 → 400자.
- 최소 비용, 최대 효과. 에피소드 비트 4-5개 수용 가능.

**접근법 B: 구조화된 정지선**
- 원문 절삭 대신 구조화 추출: `{"core_events": ["이벤트1", "이벤트2"], "key_actors": ["인물A"], "stakes": "정치적 위기"}`
- Blueprint에 raw text + structured summary 이중 전달.

**접근법 C: 다층 정지선**
- Primary (600자): 원문 기반 상세 정보.
- Secondary (150자): "핵심 이벤트 3가지: [A], [B], [C]" 형태 요약.
- Chief Writer는 Primary로 정지선 준수, Director는 Secondary로 빠른 검증.

**접근법 D: 절삭 무결성 검증**
- 절삭 후 마지막 문장이 완전한지 검증. 불완전하면 마지막 완전 문장까지로 재절삭.
- 예: "의원이 암살 시도 →" (불완전) → "의원이 암살 시도" (완전)로 조정.

---

## C-3: 씬 수 vs Arc 이벤트 밀도 불일치 미검증

### 1. 현황 (코드 경로)

**사전(Pre-generation) 검증: 없음**

- `BlueprintConstraintCompiler._extract_continuity()` (`blueprint_constraint_compiler.py`:261-309): 이전 Blueprint에서 `scene_breakdown`을 읽지만 **마지막 씬의 location만 추출** (line 287-289). 씬 수, 이벤트 밀도는 무시.
- `BlueprintConstraintCompiler.compile()` (line 35-96): `_extract_episode_focus()`, `_extract_stop_line()`, `_extract_continuity()`, `_extract_inherited_state()` 4개 추출기만 호출. **씬 예산(scene budget) 계산 없음**.
- `stage3_orchestrator.py:_extract_timeline_start_end()` (line 954+): `state_changes.timeline`에서 시작/종료 시간만 추출. 이벤트 밀도와 씬 수의 상관관계 **미계산**.

**사후(Post-generation) 검증: 존재하지만 느림**

- `confidence_calibration.py` (line 340-355 부근): Blueprint 생성 **후** `scene_breakdown`의 씬 수를 체크:
  - 4-7개 씬: confidence +20
  - 3 또는 8개: confidence +15
  - 그 외: confidence +10 + `"씬 개수 부족/과다"` 경고
- **이미 Blueprint가 생성된 후**이므로 씬 재배분이 불가능. 낮은 confidence는 재생성을 트리거할 수 있지만 **근본 원인(이벤트 밀도)을 해결하지 않음**.

**State Changes 이벤트 카운트: 미활용**

- `_summarize_state_changes()` (line 371-455): `npc_deaths`, `skill_acquisitions`, `relationship_changes`, `major_items`, `npc_injuries`, `npc_movements`, `resolved_plots` 7개 카테고리의 이벤트를 **문자열로 변환**. 이벤트 **수**를 세거나 씬 예산에 매핑하는 로직 없음.

### 2. 갭

1. **씬 예산 미제공**: Blueprint 생성 시점에 "이 에피소드에 N개의 주요 이벤트가 있으므로 최소 M개 씬 필요"라는 가이드라인이 **존재하지 않음**. Chief Writer / Blueprint Generator가 자의적으로 씬 수를 결정.

2. **이벤트 분포 미계산**: 다중 에피소드 Arc에서 state_changes 이벤트가 **어떤 에피소드에 집중되는지** 분석하는 로직 없음. Arc 전체 이벤트를 에피소드에 균등/가중 배분하는 메커니즘 부재.

3. **사후 검증의 한계**: `confidence_calibration`의 씬 수 체크는 **절대값 범위**(4-7개 OK)만 판단. "이 에피소드에 9개 이벤트가 있는데 3개 씬"이라는 **상대적 밀도 불일치**를 감지하지 못함.

4. **Blueprint→Chief Writer 피드백 루프 부재**: Blueprint의 씬 수가 이벤트 밀도와 맞지 않아도 Chief Writer에게 재조정 요청하는 메커니즘 없음 → Director가 "페이싱 문제"로 reject → Chief Writer가 같은 Blueprint로 재시도 → **무한 루프 가능성**.

### 3. 영향도

**Significant**

- **이벤트 압축**: 밀도 높은 에피소드에서 씬이 부족하면 각 씬에 이벤트가 몰려 **대화가 얕아지고 전개가 급함**.
- **씬 불균형**: 밀도 낮은 에피소드에서 씬이 과다하면 **늘어지는 느낌**, 불필요한 패딩 발생.
- **Director 거부 루프**: "페이싱 문제" 거부 → 같은 Blueprint로 재시도 → 같은 거부. Blueprint 수준의 문제를 Chief Writer 수준에서 해결 불가.

### 4. 방향 스케치

**접근법 A: 씬 예산 계산기**
- `BlueprintConstraintCompiler`에 `_calculate_scene_budget()` 메서드 추가.
- 입력: `state_changes` 이벤트 수, `ep_count`, `arc_position`.
- 출력: `{"minimum_scenes": N, "recommended_scenes": M, "event_count": K, "reason": "..."}`.
- 경험적 규칙: 이벤트 2개당 씬 1개 (최소 3개 씬).

**접근법 B: Constraint Block에 씬 요구사항 삽입**
- `constraint_block["scene_requirements"]`로 Blueprint Generator에 전달.
- 예: `{"minimum": 4, "recommended": 5, "reason": "주요 이벤트 5건 (NPC사망 2, 무공습득 1, 관계변화 2)"}`

**접근법 C: 사전 검증 게이트**
- Blueprint 생성 전에 이벤트 밀도 vs 기본 씬 수 범위 체크.
- 밀도 > 임계값이면 Blueprint Generator에 경고 주입: "이 에피소드는 이벤트 밀도가 높습니다. 최소 N개 씬을 할당하세요."

**접근법 D: 에피소드별 이벤트 분포 맵**
- Arc의 전체 state_changes를 에피소드에 사전 배분.
- `per_episode_event_budget`: `[{ep: 1, events: 3}, {ep: 2, events: 5}, ...]`
- Blueprint Generator가 이 맵을 참조하여 씬 수 결정.

---

## Track 내 교차 발견

### 교차 발견 1: "왜" 소실의 연쇄 효과 (C-1 × C-2 × C-3)

C-1(제약의 이유 미전달), C-2(정지선 정보 손실), C-3(이벤트 밀도 미반영)은 모두 **동일한 근본 원인**을 공유: **Stage 2의 풍부한 서사 정보가 Stage 3에 도달할 때 operational fact로 축소**됨.

- 제약은 "무엇을 하지 마라"만 전달 (C-1)
- 정지선은 "다음에 무엇이 있다"만 전달 (C-2)
- 이벤트 밀도는 "전달조차 안 됨" (C-3)

→ Stage 3 Blueprint Generator가 받는 정보의 **의미론적 해상도가 낮음**.

### 교차 발견 2: 이중 절삭 패턴

C-2의 300→200자 이중 절삭과 유사한 패턴이 다른 곳에도 존재:
- `compile_to_prompt()`에서 `must_focus.content[:500]` (line 120)
- `continuity.prev_ending[:150]` (line 141)

모든 절삭이 **문자 수 기반 하드 절삭**이며 **의미 보존 절삭**이 아님. 이는 C-1의 "rationale 부재"와 결합하면 이미 부족한 정보가 **추가 손실**되는 구조.

### 교차 발견 3: 사후 검증의 구조적 한계

C-3에서 `confidence_calibration`이 사후 검증만 하는 것처럼, C-1의 제약 충실도, C-2의 정지선 완전성도 **사후 검증 메커니즘이 없음**. 이 3개 이슈 모두 **사전(pre-generation) 검증 강화**가 공통 해결 방향.

---

## 3-Pass 감리 기록

### Pass 1: 사실 정확성 (92%)

- ✅ `_extract_stop_line()` 코드 경로 정확 (line 218-259)
- ✅ 이중 절삭 300→200 확인 (line 238/247 → line 131)
- ✅ `_extract_continuity()`가 마지막 씬 location만 추출 확인 (line 287-289)
- ✅ `_summarize_state_changes()`의 7개 카테고리 확인 (line 384-453)
- ⚠️ `confidence_calibration.py`의 정확한 라인은 코드 버전에 따라 다를 수 있음 → 340-355 부근으로 범위 표기
- ⚠️ `ConstraintCompiler._extract_current_state()`의 `next_arc_constraints` 활용 범위 재확인 필요 → line 214에서 `must_start_with`만 참조하는 것 확인

### Pass 2: 논리 정합성 (95%)

- ✅ C-1: operational 추출 → 서사적 맥락 손실 → Stage 4 품질 영향 — 논리 체인 건전
- ✅ C-2: 하드 절삭 → 정보 손실 → 정지선 위반 위험 — 인과 관계 명확
- ✅ C-3: 이벤트 밀도 미반영 → 씬 불균형 → 페이싱 문제 — 연결 건전
- ✅ 교차 발견의 "operational fact 축소" 진단이 3건 모두를 통합 설명

### Pass 3: 완성도 (97%)

- ✅ 각 항목 4단계(현황/갭/영향도/방향) 완비
- ✅ 코드 경로 주장 모두 file:line 근거 제시
- ✅ 방향 스케치가 구현 제안이 아닌 접근법 수준
- ✅ 영향도 평가에 Stage 4 관점 반영
- ✅ 교차 발견 3건으로 Track 내 상호작용 분석
