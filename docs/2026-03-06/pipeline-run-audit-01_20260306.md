# Pipeline Run Audit 01 — 001_260306 (2026-03-06)

> 프로젝트: `001_260306` (투자물, 1인칭, 회귀자)
> 로그: `session_20260306_212608.log`
> Arc 범위: 1~5 (ep 1~20)
> 총 소요: 약 35분 (21:26~22:01)

---

## 1. 실행 요약

| Arc | 에피소드 | Director 판정 | 비고 |
|-----|---------|---------------|------|
| 1 | 1~4 | PASS_WITH_FIX(95) -> InPlace -> PASS | IFC 시대착오 수정 |
| 2 | 5~8 | PASS(90+) | 금지 아이템 오탐으로 후보 2개 70점 |
| 3 | 9~12 | REJECT(88) -> InPlace -> PASS_WITH_FIX(95) -> InPlace -> PASS | 여의도->강남 위치 연속성 |
| 4 | 13~16 | PASS(90+) | 금지 아이템 오탐으로 후보 1개 0점 |
| 5 | 17~20 | PASS(100) | 완벽 통과 |

- InPlace-Diff 로그: Arc 1(37줄), Arc 3(28줄) — 금회 추가한 diff 로깅이 실전 첫 가동
- 총 LLM 호출: Enrich 5회 + Ensemble 5세트(15회) + Director 심사/SC 약 15회 + InPlace 3회

---

## 2. 발견 이슈

### BUG-A (P1): 금지 아이템 오탐 — 기존 소지품을 신규 획득으로 잘못 판정

**심각도**: P1 (후보 점수 왜곡, 4/5 Arc에서 발생)

**증상**:
```
Arc 2: creative: 70점 - 금지 아이템 획득 시도: 블랙베리 스마트폰
       conservative: 70점 - 금지 아이템 획득 시도: 블랙베리 스마트폰
Arc 3: balanced: 0점 - 금지 아이템 획득 시도: 2006년식 피처폰
       conservative: 0점 - 금지 아이템 획득 시도: 2006년식 피처폰
       creative: 0점 - 금지 아이템 획득 시도: 2006년식 피처폰
Arc 4: conservative: 85점 - 금지 아이템 획득 시도: 블랙베리 스마트폰
       balanced: 85점 - 금지 아이템 획득 시도: 블랙베리 스마트폰
       creative: 0점 - 금지 아이템 획득 시도: SW인베스트먼트 법인 서류 일체
Arc 5: creative: 85점 - 금지 아이템 획득 시도: 블랙베리 스마트폰
       conservative: 0점 - 금지 아이템 획득 시도: 2006년식 피처폰
       balanced: 0점 - 금지 아이템 획득 시도: 2006년식 피처폰
```

**근본 원인**: `arc_ensemble.py` L650의 판정 조건:
```python
if item in _acq_strs or ("획득" in tactical and item in tactical):
```
두 번째 조건 `"획득" in tactical and item in tactical`이 문제:
- `tactical_doc` 전문에서 "획득"이라는 단어가 **어디든** 존재하고 (거의 항상 존재)
- 동시에 해당 아이템명이 **어디든** 존재하면 (기존 소지품 목록에 당연히 있음)
- → 금지 아이템 획득 시도로 오판

예: Arc 3 tactical_doc에 `장비: 블랙베리 스마트폰` (시작 상태에 기존 소지품 나열)과 `획득/소모: 금 선물 숏 포지션 진입` (전혀 다른 맥락의 "획득")이 각각 존재 → "블랙베리 스마트폰을 획득 시도"로 오탐

**영향**:
- 후보 점수에서 -15점 감산 (items별 누적)
- Arc 3에서 3후보 전부 0점 처리 → 최저점 후보가 강제 선택됨
- Arc 5에서 2/3 후보 0점 처리 → 실질적 앙상블 비교 불가
- Director가 사후 재심사로 구제하므로 최종 Arc 품질에는 영향 제한적이나, 앙상블 비교 기능이 사실상 무력화

**수정 방안**:
`arc_ensemble.py` L650에서 tactical 전문 검색 조건을 정밀화:
1. `item in tactical` → "획득"과 item이 **같은 문장/줄** 안에 있는지 확인 (줄 단위 검색)
2. 또는 기존 소지품(prev_equipment + arc_start_state.equipment)에 포함된 아이템은 forbidden 체크에서 제외

**추천**: 방안 2 (화이트리스트 방식) — 기존 소지품은 금지 대상이 될 수 없으므로 구조적으로 올바름

```python
# 수정 전
for item in forbidden_items:
    if item in _acq_strs or ("획득" in tactical and item in tactical):

# 수정 후
_existing_equip = set()
_start_eq = candidate.get("state_constraints", {}).get("arc_start_state", {}).get("equipment", [])
if isinstance(_start_eq, list):
    _existing_equip.update(str(e).strip() for e in _start_eq)
if prev_equipment:
    _existing_equip.update(str(e).strip() for e in prev_equipment)

for item in forbidden_items:
    if item in _existing_equip:
        continue  # 이미 보유 중인 아이템은 스킵
    if item in _acq_strs or ("획득" in tactical and item in tactical):
        score -= 15
        issues.append(f"금지 아이템 획득 시도: {item}")
```

---

### BUG-B (P2): NS-3-B 자본금 괴리 경고 과다

**심각도**: P2 (advisory 전용, Arc 품질 미영향)

**증상**:
```
Arc 1: arc_end_state.total_assets=38.0억 vs treatment target=20억 (90%)
Arc 2: arc_end_state.total_assets=50.0억 vs treatment target=23억 (117%)
Arc 3: arc_end_state.total_assets=52.0억 vs treatment target=30억 (73%)
```

**근본 원인**: Treatment의 `capital_after` 값이 보수적으로 설정되어 있으나, LLM이 Arc를 생성할 때 극적 효과를 위해 수익률을 높게 잡음. NS-3-B의 30% 괴리 임계값을 초과.

**영향**: advisory 로그만 발생. Director가 최종 판정 시 자본금 일관성을 별도 검증하므로 이중 안전망. 최종 Arc에는 Director 판정 기준 수치가 반영됨.

**수정 방안**: 현상 유지(P2 유보). Treatment 자체의 수치가 보수적인 경우 괴리는 불가피. NS-3-B 임계값을 투자물 장르에서만 50%로 상향하는 것은 과잉 설계.

---

### BUG-C (P2): internal_energy 필드 LLM 자발적 생성

**심각도**: P2 (Director가 정확히 감지/경고)

**증상**:
```
Arc 1 PASS_WITH_FIX 사유: "제약 조건에서 명시적으로 금지한 'internal_energy'
수치화 능력치를 state_constraints에 사용함"
```

**근본 원인**: LLM이 비무협 장르임에도 `state_constraints`에 `internal_energy` 필드를 자발적으로 생성. 프롬프트에는 `_build_non_wuxia_energy_block()`으로 장르 중립 스키마가 주입되지만, LLM 학습 데이터에 내재된 패턴이 간섭.

**영향**: Director가 PASS_WITH_FIX로 감지하고 InPlace에서 제거. 최종 Arc에는 잔류하지 않음. 기존 TF-45 3단계 방어가 정상 동작 중.

**수정 방안**: 현상 유지(P2 유보). Director 감지 + InPlace 제거로 자동 치유 중. 추가 조치 시 프롬프트에 negative example 삽입 가능하나 ROI 낮음.

---

### BUG-D (P3): XC-002 NPC LLM 검증 빈 응답

**심각도**: P3 (fail-closed 처리, 안전)

**증상**:
```
Arc 3: [XC-002] NPC LLM 검증 응답 없음 -> fail-closed: []
Arc 3 InPlace 후: [XC-002] NPC LLM 검증 응답 없음 -> fail-closed: []
```

**근본 원인**: Cross-Agent Verifier의 NPC 검증 LLM 호출이 빈 응답 반환. 네트워크/API 일시 장애 또는 프롬프트 길이 초과 가능성.

**영향**: fail-closed 처리로 검증 결과가 빈 리스트로 반환. NPC 검증이 스킵되지만 Director가 별도 검증하므로 실질적 위험 없음.

**수정 방안**: 현상 유지(P3). fail-closed가 올바른 동작.

---

## 3. 정상 동작 확인 항목

| 기능 | 상태 | 근거 |
|------|------|------|
| InPlace-Diff 로깅 | OK | Arc 1(37줄), Arc 3(28줄) unified diff 정상 기록 |
| InPlace 패치 품질 | OK | Arc 1: IFC→한미증권 정확 치환, Arc 3: 여의도→강남 전량 치환 |
| 공간 연속성 감지 | OK | Arc 3에서 "강남→여의도" 모순 Director REJECT |
| Self-Consistency | OK | Arc 3에서 3투표 중 PASS 1/REJECT 2 → REJECT 판정 |
| PASS_WITH_FIX 루프 | OK | Arc 1, 3에서 InPlace → 재심사 → PASS 정상 수렴 |
| Equipment 동기화 | OK | Arc 5 시작 시 12개 아이템 동기화 확인 |
| NC-3 체크리스트 | OK | Arc 5 Director thinking에 12개 카테고리 전량 OK |
| Entity 일관성 | OK | V61 약칭 필터 정상 동작 (금 선물(Long)→금 선물 롱 등) |

---

## 4. 패치 우선순위

| 순서 | ID | 심각도 | 작업 | 예상 변경 |
|------|----|--------|------|-----------|
| 1 | BUG-A | P1 | 금지 아이템 오탐 수정 — 기존 소지품 화이트리스트 | `arc_ensemble.py` L642-652, 약 10줄 |
| - | BUG-B | P2 유보 | NS-3-B 투자물 괴리 | 현상 유지 |
| - | BUG-C | P2 유보 | internal_energy LLM 자발 생성 | 현상 유지 (Director 자동 치유) |
| - | BUG-D | P3 유보 | XC-002 NPC 검증 빈 응답 | 현상 유지 (fail-closed 정상) |

---

## 5. 테스트 계획 (BUG-A)

```
1. test_forbidden_item_skip_existing_equipment:
   - arc_start_state.equipment에 "블랙베리 스마트폰" 포함
   - forbidden_items에 "블랙베리 스마트폰" 포함
   - tactical_doc에 "획득" + "블랙베리 스마트폰" 둘 다 존재
   -> 금지 아이템 오탐이 발생하지 않아야 함

2. test_forbidden_item_new_acquisition_still_caught:
   - arc_start_state.equipment에 없는 "비밀 장부"
   - forbidden_items에 "비밀 장부" 포함
   - items_acquired에 "비밀 장부" 포함
   -> 여전히 금지 아이템 획득 시도로 감지되어야 함

3. test_forbidden_item_tactical_mention_existing:
   - prev_equipment에 "법인인감" 포함
   - forbidden_items에 "법인인감" 포함
   - tactical에 "법인인감을 획득" 문장 존재
   -> 이미 보유 중이므로 오탐 없어야 함

4. test_forbidden_item_arc1_no_prev_equipment:
   - prev_equipment=[] (첫 Arc)
   - arc_start_state.equipment=[] (초기 상태)
   - forbidden_items에 "비밀 장부" 포함
   - items_acquired에 "비밀 장부" 포함
   -> 화이트리스트 비어있으므로 정상 감지

5. test_forbidden_item_items_acquired_override:
   - arc_start_state.equipment에 "법인인감" 포함
   - forbidden_items에 "법인인감" 포함
   - items_acquired에 "법인인감" 명시적 포함 (LLM 오류)
   -> items_acquired 경로에서 여전히 감지되어야 하는가?
   -> 아니오: 이미 보유 중인 아이템이므로 화이트리스트로 스킵이 맞음
   -> items_acquired에 기존 소지품이 들어가는 것 자체가 LLM 오류이나,
      이는 별도 검증(arc_draft_validator)에서 처리
```
