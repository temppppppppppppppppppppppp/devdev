# 실파이프라인 감사 03_20260307 — 03_2727 프로젝트 전수조사

> 대상: `projects/03_2727` (투자물, 골든루트 60블록, Arc 1~5)
> 실행 시각: 2026-03-07 02:19 ~ 03:08 (49분, Stage 2 Only)
> LLM 호출: 83회 (실패 0), 토큰 938,556, 비용 $1.39
> 테스트 기준선: 3,588 passed

---

## 1. 전수 이슈 목록

### BUG-A: 위치 핑퐁 — auto_correct + LLM 생성 간 SSOT 충돌 [P1]

**현상**: Arc 3~5에서 사무실 위치가 반복적으로 오락가락하여 REJECT 2회 발생.

| Arc | LLM 생성 위치 | auto_correct 교정 | 결과 |
|-----|-------------|-----------------|------|
| 1 | 강남 테헤란로 소형오피스 | end→오피스텔(joint_docs 기준) | PASS_WITH_FIX |
| 2 | 강남 테헤란로 | end→여의도(joint_docs) | PASS |
| 3 | 여의도 | end→삼성동(joint_docs) | PASS_WITH_FIX (강남→여의도 불일치) |
| 4 | **삼성동**(stale) | end→강남 테헤란로 | **REJECT** (여의도→삼성동 회귀) |
| 5 | **강남**(stale) | end→강남 테헤란로 | **REJECT** (위치+시간 정체) |

**근본 원인 분석**:

1. `_sync_final_location()`: `joint_docs.final_location` → `arc_end_state.location` 동기화. joint_docs가 SSOT.
2. `_fix_start_location()`: 다음 Arc 생성 시 `prev_arcs[-1]`의 `joint_docs.final_location` → `arc_start_state.location` 교정.
3. **문제**: LLM이 `joint_docs.final_location`을 생성할 때 tactical_doc 내용과 불일치하는 경우가 빈번. tactical_doc은 "여의도로 이전"이라 쓰면서 joint_docs에는 "삼성동"을 기재 → auto_correct가 삼성동으로 교정 → 다음 Arc도 삼성동에서 시작.
4. **Phase 2.5 location 강제 주입** (`four_phase_arc_generator.py`): `_load_execution_state()`는 Stage 2에서 WorldState가 아직 없으므로 `None` 반환 → `_plan_loc` (= `arc_end_state.location`, auto_correct 후 값)에 의존. 이 값 자체가 joint_docs 기준으로 이미 잘못된 경우 주입도 잘못됨.
5. **핵심 갭**: `joint_docs.final_location`이 tactical_doc의 서사와 불일치할 때 이를 탐지/교정하는 메커니즘이 없음. auto_correct는 joint_docs를 맹목적으로 신뢰.

**패치 계획**:
- `_sync_final_location()`에서 `joint_docs.final_location`과 `tactical_doc` 마지막 에피소드의 위치 텍스트를 교차 검증
- 불일치 시 tactical_doc에서 위치를 regex 추출하여 joint_docs 교정 (tactical_doc이 더 상세하므로 SSOT 우위)
- 교차 검증 실패 시(둘 다 추출 불가) 기존 joint_docs 유지 (현상 유지 폴백)

**영향 파일**: `modules/core/stage2_optimizer.py` (`_sync_final_location`)

---

### BUG-B: NS-2 자본 괴리 — Treatment 목표 대비 2~3배 과잉 성장 [P2]

**현상**: 전 Arc에서 arc_end_state.total_assets가 Treatment genre_ext.capital_after 대비 120~240% 괴리.

| Arc | Treatment 목표 | Arc 실제 | 괴리 |
|-----|-------------|---------|------|
| 2 | 23억 | 78억 | 239% |
| 3 | 30억 | 102억 | 240% |
| 4 | 45억 | 111.7억 | 148% |
| 5 | 50억 | 110억 | 120% |

**근본 원인**: NS-2는 advisory-only (대원칙 3 준수). LLM이 Treatment 수치 목표를 과도하게 초과하는 자산 성장을 설계해도 Director가 허용하면 통과. NS-3-B(`_check_arc_vs_block_targets`)는 Phase 2.55에서 30% 괴리 경고를 생성하지만, LLM이 이를 무시할 수 있음.

**판정**: **P2 — advisory 강화만 가능**. 대원칙 1(판단은 LLM) + 대원칙 3(Director 주권) 상 Python이 자본 수치를 강제할 수 없음. 다만 현재 30% 임계값이 사실상 무력화(전부 초과)되므로, Director 프롬프트에 capital_after 목표를 더 강하게 주입하는 것은 가능.

**패치 계획**: Director compare_and_select_arc() story_context에 `[NS-2 주의] Treatment 목표 자본 vs Arc 설계 자본 괴리` 문구를 advisory로 주입. 기존 NS-2 로그는 finalizer에서만 출력되므로 Director가 선택 시점에 볼 수 없음.

**영향 파일**: `modules/core/stage2_finalizer.py` (Director story_context 주입 위치)

---

### BUG-C: XC-002 NPC LLM 검증 반복 실패 [P2]

**현상**: 3회 발생 (Arc 1, 5-1차, 5-2차). LLM 응답이 빈 문자열이거나 JSON 파싱 실패.

```
[XC-002] NPC LLM 검증 예외 → fail-closed: Expecting value: line 1 column 1 (char 0)
[XC-002] NPC LLM 검증 응답 없음 → fail-closed: []
[XC-002] NPC LLM 검증 응답 없음 → fail-closed: []
```

**근본 원인**: `state_tracker_npc.py`에서 NPC 이름 후보를 LLM에 검증 요청할 때 빈 응답 수신. fail-closed 동작(빈 리스트 반환)이므로 안전하나, NPC 오탐 필터링이 스킵됨.

**판정**: **P2 — fail-closed 정상 동작, 안전성 확보됨**. 다만 5회 중 3회(60%) 실패는 높은 비율. 원인은 모델 응답 불안정(빈 응답)으로, 1회 retry 추가가 ROI 있을 수 있음.

**패치 계획**: `_verify_npcs_with_llm()`에 1회 retry 추가 (기존: 즉시 fail-closed). 빈 응답 시 1회만 재시도 후 여전히 실패면 fail-closed 유지.

**영향 파일**: `modules/domain/agents/state_tracker_npc.py`

---

### BUG-D: internal_energy 비무협 오염 잔류 [P2]

**현상**: Arc 1, 2에서 `state_constraints`에 `internal_energy: 100` 포함. Director가 모순으로 지적.

```
state_constraints의 'internal_energy' 필드 사용은 '내공, 정신력, 마나 등의 수치화된 능력치를 사용하지 말라'는 제약 조건 위반입니다.
state_constraints에 제약 조건으로 금지된 수치화 능력치 'internal_energy'가 포함됨.
```

**근본 원인**: TF-45에서 비무협 장르의 `build_state_constraints_schema()`가 `internal_energy` 대신 장르별 키를 사용하도록 변경했으나, LLM이 여전히 `internal_energy`를 생성. 스키마에서 제거해도 LLM이 학습된 패턴으로 추가하는 경우를 차단하지 못함.

**판정**: **P2 — auto_correct에서 후처리 제거 가능**. Director가 이미 모순으로 감지하여 PASS_WITH_FIX 발급하므로 안전. 다만 auto_correct 단계에서 비무협 장르일 때 `internal_energy` 필드를 자동 제거하면 Director 부담 감소.

**패치 계획**: `ArcAutoCorrector.auto_correct()`에 비무협 장르 판별 후 `state_constraints`에서 `internal_energy` 키 자동 제거 + corrections 기록.

**영향 파일**: `modules/core/stage2_optimizer.py` (`auto_correct` 메서드)

---

### BUG-E: items_consumed 추상 개념 기재 [P2]

**현상**: Arc 1에서 `items_consumed`에 "가족의 무관심이라는 방패막", "첫 거래의 기회비용" 등 추상적 개념 기재. 해당 필드는 물리적 소모 아이템 전용.

**근본 원인**: LLM이 items_consumed의 의미를 잘못 해석. 프롬프트에서 "물리적으로 소모된 아이템"이라는 제약이 충분하지 않거나, 투자물 장르에서 "소모"를 추상적으로 해석.

**판정**: **P2 — auto_correct 후처리로 해결 가능**. `items_consumed` 항목 중 추상 패턴(조사/비유) 매칭 시 제거. 15자 초과 항목도 제거 (물리 아이템은 보통 짧음).

**패치 계획**: `ArcAutoCorrector`에 `_filter_abstract_items_consumed()` 추가. 간단한 regex 기반 필터 (조사 패턴 "~라는", "~으로 인한", "~의 기회비용" 등 매칭 시 제거).

**영향 파일**: `modules/core/stage2_optimizer.py`

---

### BUG-F: JSON Parser fallback + 정규식 추출 실패 [P2]

**현상**: 4회 발생. `ast.literal_eval` 실패 후 정규식 fallback 사용. 이 중 2회는 정규식도 실패하여 RAW 반환.

```
[JSON Parser] ast.literal_eval 실패, 정규식 fallback 사용 (길이: 1029자)
[JSON Parser] ast.literal_eval 실패, 정규식 fallback 사용 (길이: 5898자)
[JSON Parser] ast.literal_eval 실패, 정규식 fallback 사용 (길이: 5064자)
→ 정규식 추출 실패, RAW 반환
[JSON Parser] ast.literal_eval 실패, 정규식 fallback 사용 (길이: 4446자)
→ 정규식 추출 실패, RAW 반환
```

**근본 원인**: LLM 응답이 순수 JSON이 아닌 마크다운 코드블록이나 설명 텍스트를 포함. 기존 파서(`_extract_json_robust`)가 처리 못하는 포맷.

**판정**: **P2 — 기존 파서 폴백 체인 동작 중, 최종 RAW 반환 시에도 상위 코드에서 처리됨**. 2회 RAW 반환은 Stage 2 패치 모드(attempt 2)에서 발생 — 패치 후 auto_correct 결과가 정상 처리되었으므로 실제 영향 없음. 단, RAW 반환 빈도가 높으면 향후 문제 가능.

**패치 계획**: 없음 (P2, 현재 영향 없음). 향후 RAW 반환 빈도가 증가하면 파서 강화 검토.

---

### BUG-G: V61 Entity 일관성 불일치 반복 [P2]

**현상**: 7회 WARNING 발생. 1~3개 Entity 불일치.

```
[V61] Entity 일관성 검증: PASS (1개 불일치)        — Arc 3
[V61] Entity 일관성 검증: WARNING (2개 불일치)      — Arc 4-1차
[V61] Entity 일관성 검증: WARNING (3개 불일치)      — Arc 4-2차 attempt1
[V61] Entity 일관성 검증: WARNING (2개 불일치)      — Arc 4-2차 attempt2
[V61] Entity 일관성 검증: WARNING (2개 불일치)      — Arc 5-1차
[V61] Entity 일관성 검증: WARNING (2개 불일치)      — Arc 5-2차
[V61] Entity 일관성 검증: WARNING (2개 불일치)      — Arc 5-2차 재심사
```

**근본 원인**: StateTracker의 NPC 레지스트리와 Arc tactical_doc 내 NPC 이름이 미세하게 불일치 (예: 성+이름 vs 이름만, 직함 포함 vs 미포함). advisory-only이므로 동작 영향 없음.

**판정**: **P2 — advisory 정상 동작**. Entity 불일치는 Director가 이미 모순 검사에서 커버. 추가 패치 불필요.

---

### BUG-H: F-2 InPlace 변경 비율 초과 [P2]

**현상**: 3회 발생. Arc 1(30.0%), Arc 3(30.4%), Arc 5(36.5%) — 30% 임계값 초과.

**근본 원인**: PASS_WITH_FIX → InPlace patch 시 수정 범위가 넓어짐. 특히 위치 관련 수정은 tactical_doc 전체에서 위치 문자열을 치환하므로 diff 비율이 높아짐.

**판정**: **P2 — 경고만 출력, 동작 불변**. F-2는 advisory 로깅 전용. InPlace가 30% 초과해도 Director 재심사에서 PASS 받으면 문제 없음. 실제로 3건 모두 재심사 PASS(100점).

**패치 계획**: 없음. 현재 동작 정상.

---

### BUG-I: Arc 5 시간 정체 — 복수 에피소드 동일 타임스탬프 [P1]

**현상**: Arc 5 1차 시도에서 19화, 20화, 21화의 시작/종료 상태 시간이 모두 "2006년 8월 18일 금요일, 오후 4시 30분"으로 고정. 서사상 수개월이 경과하는데 시간 정보 미갱신.

**근본 원인**: auto_correct의 `_fix_start_location()`이 위치와 함께 시간 정보가 포함된 location 문자열을 통째로 복사. Arc 4 종료 위치가 "서울 강남구 테헤란로, SW인베스트먼트 오피스. 시계는 2006년 8월 18일 금요일, 오후 4시 30분, 장 마감 직후를 가리킨다."이므로, 이 전체 문자열이 Arc 5의 시작 위치로 주입됨. LLM이 이 시간 정보를 그대로 복사하여 이후 에피소드에도 전파.

**핵심 갭**: `arc_end_state.location`에 시간 정보가 포함되어 있으면 안 됨. 위치와 시간은 분리되어야 하나, auto_correct가 joint_docs.final_location(서사적 묘사 포함)을 그대로 location에 주입.

**패치 계획**: `_sync_final_location()`에서 `joint_docs.final_location` 값을 정규화 — 시간/날짜 정보("시계는...", "N월 N일", "오후 N시" 등) 제거 후 location에 저장. 시간 정보는 별도 필드(`arc_end_state.time_marker`) 또는 무시.

**영향 파일**: `modules/core/stage2_optimizer.py` (`_sync_final_location`)

---

### BUG-K: 정신적 피로 자연 회복 경로 부재 [P1] → NR-1 패치 완료

**현상**: Arc 4 2차 시도에서 `status_shadow`의 부상 항목이 "정신적 마모(Mental Abrasion)"로 잔류. 투자물에서 정신적 마모는 Arc 내에서 누적만 되고 회복 경로가 없음 — 병원씬이 없는 장르에서 부상 연속성 규칙("회복 장면 없이 유지/악화만")이 정신적 피로에도 동일 적용되어 스트레스가 무한 누적.

**근본 원인**: 시스템 전반에서 "부상"을 물리적 부상과 정신적 피로를 구분하지 않음. writer_rules 규칙5, analyst.yaml 3곳 모두 "회복 장면 필수"를 일괄 적용.

**NR-1 패치 (완료)**:
1. `arc_ensemble.py` `_build_non_wuxia_energy_block()` — `[NR-1] 정신적 피로 자연 회복 원칙` 블록 추가 (수면/식사/대화 1문장이면 충분, 3화 연속 누적 금지)
2. `analyst.yaml` L211, L264, L545 — 정신적 피로 일상 회복 예외 3곳 추가
3. `writer_rules.json` 규칙5 — 비물리적 부상 자연 회복 허용 단서 추가
4. `genre_schema_builder.py` `build_status_shadow_schema()` — 비무협 expected_injuries에 회복 경로 힌트
5. `four_phase_arc_generator.py` `_check_arc_end_state()` I-12 — 정신적 피로 감지 시 advisory 레벨 분리 + 자연 회복 가능 메시지

---

### BUG-J: Director 오탐 — power_changes "비표준 필드" 지적 [P3]

**현상**: Arc 1에서 Director가 "`power_changes`가 비표준 필드"라고 모순 지적.

**사실**: `power_changes`는 `modules/models/arc.py:108`에 `Field(default_factory=dict)`로 정의된 **표준 필드**. `analyst_prompts.py`에서도 스키마에 포함. Director LLM이 잘못 판단한 것.

**판정**: **P3 — Director LLM 오탐, 코드 이슈 아님**. Director 프롬프트에 `power_changes`가 표준 필드임을 명시하면 해소 가능하나, 발생 빈도 1회로 ROI 낮음.

**패치 계획**: 없음.

---

## 2. 이슈 우선순위 요약

| ID | 이슈 | 등급 | 패치 필요 | 영향 |
|----|------|------|----------|------|
| BUG-A | 위치 핑퐁 (auto_correct SSOT 충돌) | **P1** | **YES** | REJECT 2/5 (40% 실패) |
| BUG-I | 시간 정체 (location에 시간 혼입) | **P1** | **YES** | REJECT 사유 일부 |
| BUG-B | NS-2 자본 괴리 240% | P2 | YES (advisory) | 장기 설정 붕괴 위험 |
| BUG-C | XC-002 NPC 검증 실패 60% | P2 | YES (1회 retry) | NPC 필터링 스킵 |
| BUG-D | internal_energy 비무협 오염 | P2 | YES (auto strip) | Director 부담 |
| BUG-E | items_consumed 추상 개념 | P2 | YES (auto filter) | 데이터 오염 |
| BUG-F | JSON Parser RAW 반환 2회 | P2 | NO | 현재 영향 없음 |
| BUG-G | V61 Entity 불일치 7회 | P2 | NO | advisory 정상 |
| BUG-H | F-2 InPlace 30% 초과 3회 | P2 | NO | advisory 정상 |
| BUG-K | 정신적 피로 자연 회복 부재 | **P1** | **YES → NR-1 완료** | 무한 누적 위험 |
| BUG-J | Director power_changes 오탐 | P3 | NO | 1회, LLM 오탐 |

---

## 3. 코덱스 오더

### Step 1: BUG-A + BUG-I 통합 패치 — location SSOT 정합성

**파일**: `modules/core/stage2_optimizer.py`

**변경 1-A**: `_sync_final_location()` 내부에 시간 정보 제거 정규화 추가.

```python
def _sync_final_location(self, arc: dict) -> dict:
    """joint_docs.final_location -> arc_end_state.location 동기화 (시간 정보 분리)"""
    joint_loc = arc.get("joint_docs", {}).get("final_location", "")
    if not joint_loc:
        return arc

    # [BUG-I] 시간/날짜 정보 제거 — location은 순수 장소만
    import re
    # 실제 데이터: "...오피스. 시계는 2006년 8월 18일 금요일, 오후 4시 30분, 장 마감 직후를 가리킨다."
    # 구분자가 마침표 또는 쉼표일 수 있으므로 [.,] 사용. 문장 끝까지 탐욕 매칭.
    _time_pattern = re.compile(
        r"[.,]\s*시계는.+$"              # "시계는"부터 문자열 끝까지 제거
        r"|[.,]\s*\d{4}년\s*\d+월.+$"    # "2006년 8월..."부터 끝까지
        r"|[.,]\s*[오전후]+\s*\d+시.+$", # "오후 4시..."부터 끝까지
        re.DOTALL,
    )
    cleaned_loc = _time_pattern.sub("", joint_loc).rstrip("., ").strip()
    if not cleaned_loc:
        cleaned_loc = joint_loc  # 폴백

    state = arc.get("state_constraints", {})
    arc_end = state.get("arc_end_state", {})
    current_loc = arc_end.get("location", "")

    if current_loc != cleaned_loc:
        self.corrections_made.append(
            f"arc_end_state 위치 동기화: '{current_loc}' -> '{cleaned_loc}'"
        )
        arc_end["location"] = cleaned_loc
        state["arc_end_state"] = arc_end
        arc["state_constraints"] = state

    return arc
```

**변경 1-B**: `_fix_start_location()` 내부에 tactical_doc 마지막 에피소드 위치 교차 검증 추가.

```python
def _fix_start_location(self, arc: dict, prev_arcs: list[dict]) -> dict:
    """시작 위치를 이전 Arc 종료 위치로 수정"""
    if not prev_arcs:
        return arc

    prev_arc = prev_arcs[-1]

    # [BUG-A] 위치 SSOT: arc_end_state.location 우선 (auto_correct 후 값)
    # joint_docs.final_location은 LLM 생성값이라 stale 가능
    prev_location = None
    end_state = prev_arc.get("state_constraints", {}).get("arc_end_state", {})
    prev_location = end_state.get("location")
    if not prev_location:
        joint = prev_arc.get("joint_docs", {})
        prev_location = joint.get("final_location")

    if not prev_location:
        return arc

    # ... 이하 기존 로직 동일
```

**변경 의도**: `auto_correct()` 내 실행 순서는 `_fix_start_location` (L184) → `_fix_start_state` (L187) → `_fix_joint_docs` (L190) → `_sync_final_location` (L193). `_sync_final_location`이 `joint_docs` → `arc_end_state` 동기화를 수행하므로, `prev_arcs[-1]`의 `arc_end_state.location`은 이전 회차 `_sync_final_location`이 교정한 최신값. 따라서 `_fix_start_location`에서 `arc_end_state.location`을 1순위로 참조하는 것이 올바름. 이렇게 하면 auto_correct로 교정된 값이 다음 Arc에 정확히 전파됨.

**구현 노트**: `_time_pattern`은 `_sync_final_location` 호출마다 컴파일됨. 모듈 레벨 상수 `_LOCATION_TIME_RE`로 이동 권장 (성능 이슈 미미하나 관례상).

**테스트 계획**:
1. `test_fix_start_location_uses_arc_end_state_priority` — arc_end_state와 joint_docs가 다를 때 arc_end_state 우선
2. `test_sync_final_location_strips_time_info` — 시간 포함 location에서 시간 제거 (실제 데이터: "시계는 2006년...")
3. `test_sync_final_location_preserves_pure_location` — 시간 없는 location은 변경 없음
4. `test_location_pipeline_no_pingpong` — 3개 Arc 연속 생성 시 위치 일관성
5. `test_sync_final_location_various_time_formats` — 다양한 시간 포맷 제거 ("12월 25일", "오전 9시" 등)

---

### Step 2: BUG-D — internal_energy 비무협 자동 제거

**파일**: `modules/core/stage2_optimizer.py`

**변경**: `auto_correct()` 메서드에 비무협 장르 `internal_energy` 제거 단계 추가.

```python
def auto_correct(self, arc: dict, prev_arcs: list[dict], *, genre: str = "") -> tuple[dict, list[str]]:
    # ... 기존 단계 ...

    # [BUG-D] 비무협 장르 internal_energy 자동 제거
    if genre and not is_wuxia(genre):
        arc = self._strip_wuxia_fields(arc)

    # ... 이하 동일
```

```python
def _strip_wuxia_fields(self, arc: dict) -> dict:
    """비무협 장르에서 무협 전용 필드 제거"""
    _wuxia_keys = {"internal_energy", "realm", "qi_nature", "martial_arts"}
    state = arc.get("state_constraints", {})
    for section_key in ("arc_start_state", "arc_end_state"):
        section = state.get(section_key, {})
        if isinstance(section, dict):
            removed = [k for k in _wuxia_keys if k in section]
            for k in removed:
                del section[k]
            if removed:
                self.corrections_made.append(
                    f"{section_key}에서 무협 전용 필드 제거: {removed}"
                )
    arc["state_constraints"] = state
    return arc
```

**호출측 변경**: `stage2_validation_pipeline.py` L323에서 `post_process_arc()` 호출 시 `genre` 인자 전달 필요. `post_process_arc()` 시그니처에 `genre=""` 추가.

**테스트 계획**:
6. `test_strip_wuxia_fields_investment` — 투자물에서 internal_energy 제거
7. `test_strip_wuxia_fields_wuxia_preserved` — 무협에서는 유지

---

### Step 3: BUG-E — items_consumed 추상 개념 필터링

**파일**: `modules/core/stage2_optimizer.py`

**변경**: `auto_correct()` 에 `_filter_abstract_items_consumed()` 단계 추가.

```python
def _filter_abstract_items_consumed(self, arc: dict) -> dict:
    """items_consumed에서 추상적 개념 제거"""
    import re
    state = arc.get("state_constraints", {})
    items = state.get("items_consumed", [])
    if not isinstance(items, list):
        return arc

    _abstract_patterns = re.compile(
        r"(이라는|으로 인한|의 기회비용|의 대가|라는 방패|심리적|정신적|감정적|추상적)"
    )
    filtered = []
    removed = []
    for item in items:
        if isinstance(item, str) and (len(item) > 15 or _abstract_patterns.search(item)):
            # 길이 15초과 OR 추상 패턴 매칭 → 제거 (물리 아이템은 보통 짧고 조사 미포함)
            removed.append(item)
        else:
            filtered.append(item)

    if removed:
        state["items_consumed"] = filtered
        arc["state_constraints"] = state
        self.corrections_made.append(
            f"items_consumed 추상 개념 {len(removed)}건 제거: {removed[:3]}"
        )
    return arc
```

**테스트 계획**:
8. `test_filter_abstract_items_consumed` — 추상 개념 제거, 물리적 아이템 유지

---

### Step 4: BUG-C — XC-002 NPC 검증 1회 retry

**파일**: `modules/domain/agents/state_tracker_npc.py`

**변경**: `_verify_npcs_with_llm()` 내 빈 응답 시 1회 retry.

```python
# 기존: 즉시 fail-closed
# 변경: 1회 retry 후 fail-closed

for _attempt in range(2):  # 최대 2회 시도
    try:
        response = self._ask_llm(...)
        _resp_text = response.text
        if not _resp_text:
            if _attempt == 0:
                logging.debug("[XC-002] 빈 응답, 1회 재시도")
                continue
            logging.warning("[XC-002] NPC LLM 검증 응답 없음 -> fail-closed: []")
            return []
        result = json.loads(_resp_text)
        # ... 정상 처리
        break
    except Exception as e:
        if _attempt == 0:
            logging.debug("[XC-002] 예외 발생, 1회 재시도: %s", str(e)[:60])
            continue
        logging.warning("[XC-002] NPC LLM 검증 예외 -> fail-closed: %s", str(e)[:60])
        return []
```

**테스트 계획**:
9. `test_xc002_retry_on_empty_response` — 1차 빈 응답 → 2차 성공
10. `test_xc002_retry_exhausted_fail_closed` — 2차도 실패 → fail-closed

---

### Step 5: BUG-B — NS-2 advisory Director 주입

**파일**: `modules/core/stage2_finalizer.py`

**변경**: `stage2_finalizer.py`의 `_story_context` 조립부(L351~368 부근, `_story_context = ""` 초기화 → `_sc_parts` 조립 → `_story_context = "\n".join(_sc_parts)` 이후)에 NS-2 경고를 Director story_context에 선제 주입.

현재 NS-2는 finalizer에서 Arc 확정 **후** 로깅만 하는데, Director가 Arc를 선택하는 **시점**에 Treatment 목표 자본을 볼 수 있어야 함.

```python
# stage2_finalizer.py L365 직후 (story_context 조립 완료 후):
if enriched_block and isinstance(enriched_block, dict):
    _ge = enriched_block.get("genre_ext", {})
    _target_cap = _ge.get("capital_after")
    if _target_cap:
        _story_context += (
            f"\n\n[NS-2 참고] Treatment 블록 목표 자본: {_target_cap}. "
            f"Arc 설계 시 이 목표에서 크게 벗어나지 않도록 주의하십시오."
        )
```

**테스트 계획**:
11. `test_ns2_advisory_injected_to_director_context` — story_context에 NS-2 참고 포함

---

### Step 6: genre 인자 배선

**변경**: `auto_correct()` 시그니처에 `genre` 추가 → 호출측 전달.

**파일**:
- `modules/core/stage2_optimizer.py`: `post_process_arc(arc, prev_arcs, *, genre="")` → `auto_correct(arc, prev_arcs, genre=genre)`
- `modules/core/stage2_validation_pipeline.py` L323: `post_process_arc(arc=..., prev_arcs=..., genre=_genre)` — `_genre`는 `self.ctx.selected_genre.get("type", "") if self.ctx.selected_genre else ""`
- `modules/core/stage2_context.py`: `selected_genre` 슬롯은 이미 존재 (L54). `selected_genre_type`은 없으므로 `.get("type", "")` 사용.

**테스트 계획**:
12. `test_genre_passed_to_auto_correct` — genre 인자가 정상 전파되는지

---

### Step 7: BUG-K — NR-1 정신적 피로 자연 회복 [패치 완료]

**상태**: ✅ 구현 완료 (3,588 passed)

**변경 내역**:

| 파일 | 변경 |
|------|------|
| `modules/domain/agents/arc_ensemble.py` | `_build_non_wuxia_energy_block()`에 `[NR-1] 정신적 피로 자연 회복 원칙` 블록 추가 — 수면/식사/대화 1문장이면 충분, 3화 연속 누적 금지, 병원 방문은 선택 |
| `config/prompts/analyst.yaml` L211, L264, L545 | "물리적 부상 = 치료 필수" vs "정신적 피로 = 일상 회복 가능" 구분 3곳 |
| `config/prompts/writer_rules.json` 규칙5 | 비물리적 부상(정신적 피로/스트레스) 자연 회복 허용 단서 추가 |
| `modules/core/genre_schema_builder.py` | `build_status_shadow_schema()` 비무협 expected_injuries에 "(정신적 피로는 일상 휴식으로 자연 회복 가능)" 힌트 |
| `modules/domain/agents/four_phase_arc_generator.py` | `_check_arc_end_state()` I-12 advisory에서 정신적 피로 키워드 감지 시 "자연 회복 가능" 레벨 분리 메시지 |

**핵심 규칙**: 정신적 피로/스트레스는 물리적 부상이 아님. 수면·식사·산책·대화 등 일상 활동 1문장이면 자연 회복 가능. Arc 내 3화 연속 악화만 하면 REJECT 사유.

**테스트**: 기존 테스트 전량 통과 (3,588 passed). NR-1은 프롬프트/advisory 변경이므로 신규 단위 테스트 불필요 — 실파이프라인에서 검증.

---

## 4. 영향 범위 요약

| 파일 | 변경 내용 |
|------|---------|
| `modules/core/stage2_optimizer.py` | `_sync_final_location` 시간 제거 + `_fix_start_location` SSOT 우선순위 변경 + `_strip_wuxia_fields` + `_filter_abstract_items_consumed` + `auto_correct`/`post_process_arc` genre 인자 |
| `modules/core/stage2_validation_pipeline.py` | `post_process_arc` 호출에 genre 전달 |
| `modules/core/stage2_finalizer.py` | NS-2 advisory Director story_context 주입 |
| `modules/domain/agents/state_tracker_npc.py` | `_verify_npcs_with_llm` 1회 retry |
| `modules/domain/agents/arc_ensemble.py` | NR-1: `_build_non_wuxia_energy_block()` 정신적 피로 자연 회복 블록 추가 |
| `config/prompts/analyst.yaml` | NR-1: 정신적 피로 일상 회복 예외 3곳 |
| `config/prompts/writer_rules.json` | NR-1: 규칙5 비물리적 부상 자연 회복 단서 |
| `modules/core/genre_schema_builder.py` | NR-1: 비무협 status_shadow 회복 경로 힌트 |
| `modules/domain/agents/four_phase_arc_generator.py` | NR-1: I-12 정신적 피로 advisory 레벨 분리 |

**테스트**: Step 1~6 신규 12개 + Step 7(NR-1) 기존 테스트 커버 (프롬프트/advisory 변경)

---

## 5. 제약 사항

1. **대원칙 1 준수**: 모든 패치는 Python 수집/정제만. 판단(REJECT/수정 결정)은 LLM이 담당.
2. **대원칙 3 준수**: NS-2 자본 괴리는 advisory만. Director가 허용하면 통과.
3. **BUG-A 근본 해결 한계**: `joint_docs.final_location`이 LLM 생성값이므로 완전한 정합성 보장 불가. auto_correct가 최선의 교정을 시도하되, LLM이 서사적으로 일관된 위치를 생성하도록 프롬프트 개선은 별도 작업.
4. **BUG-F/G/H 미패치 사유**: 현재 동작에 실질적 영향 없음. F는 상위 코드에서 처리, G/H는 advisory 정상.

---

## 6. 리스크

| 리스크 | 확률 | 완화 |
|--------|------|------|
| `_fix_start_location` SSOT 변경으로 기존 무협 위치 전파 회귀 | 낮음 | auto_correct 후 arc_end_state가 항상 최신이므로 우위 변경은 논리적으로 올바름. 무협 테스트 포함 |
| 시간 제거 regex가 유효한 위치 정보까지 삭제 | 낮음 | 폴백: cleaned_loc이 빈 문자열이면 원본 유지 |
| `_strip_wuxia_fields`가 장르 오판 시 무협 데이터 삭제 | 낮음 | `is_wuxia()` 함수는 이미 검증된 장르 판별 로직 사용 |
| NPC 검증 retry로 Stage 2 시간 증가 | 무시 | 1회 retry (약 30초), 전체 49분 대비 무시 수준 |
| NR-1 자연 회복 규칙이 무협 장르에 오적용 | 없음 | `_build_non_wuxia_energy_block()`은 비무협 전용 함수. 무협은 `_WUXIA_ENERGY_BLOCK` 상수 사용 (분기 완전 분리) |
