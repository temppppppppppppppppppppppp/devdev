# Wuxia Planning Harness

Date: 2026-03-20
Status: active
Family: `wuxguide`

Delegation bootstrap note:

- external or delegated models should read `docs/wuxguide/delegation-bootstrap.md` first
- work-level current-truth docs override older handoff summaries for task start
- saved boundary beats filename shape

## 1. When To Use

Use this harness when:

- family is `wuxguide`
- `phase0_design` does not exist yet
- Stage 0 preprocess artifacts exist and `phase0_ready_snapshot.manual_audit_pass == true`

If preprocess artifacts are missing or not audited, return to Stage 0 preprocess first.

## 2. Required Inputs

- canonical pitch / onboarding / user notes
- work-level current-truth doc when it exists
- `treatments/preprocess/{work_id}/source_manifest.json`
- `treatments/preprocess/{work_id}/profile_lock.json`
- `treatments/preprocess/{work_id}/material_bundle_summary.json`
- `treatments/preprocess/{work_id}/phase0_ready_snapshot.json`

## 3. Operator Start

Check readiness first:

```bash
python -X utf8 scripts/narrative_router.py --genre wuxia --work-id <work_id> --json
```

Only continue when:

- `stage == planning`
- `artifact_state.preprocess_ready == true`
- `artifact_state.manual_audit_pass == true`

## 3A. Stage 0 핸드오프 확인

Planning 진입 전 반드시 아래 스크립트를 실행한다:

```bash
python scripts/stage0_handoff_validator.py --work-id {work_id}
```

exit 0이 아니면 Planning 진입 금지. 실패 시 Stage 0으로 복귀하여 산출물을 보완한다.

Pitch-side promotion gate:

```bash
python -X utf8 scripts/material_promotion_gate.py --stage phase0 --path <pitch-md> --work-id <work_id>
```

이 gate가 pass하지 않으면 해당 pitch를 `Phase0-ready`로 부르지 않는다.

핸드오프 검증 항목:

- `source_manifest.json` 존재 및 정본/참고본 구분 여부
- `profile_lock.json` 존재 및 `primary_profile == "wuxia"` 확인
- `material_bundle_summary.json` 존재 및 Phase 0에 옮길 사건/NPC/위기 재료 포함 여부
- `phase0_ready_snapshot.json` 존재 및 `manual_audit_pass == true`
- `source_manifest.manual_audit_note` 비어 있지 않음

좋은 핸드오프 예:

- `source_manifest`에 정본(원작 기획안)과 참고본(레퍼런스 작품)이 명확히 구분되어 있다
- `profile_lock`에 경지축, 무공축, 세력축, 복수축이 잠겨 있다
- `material_bundle_summary`에 Phase 0에 바로 배치할 적대자, 비급, 문파 재료가 있다

나쁜 핸드오프 예:

- `source_manifest` 없이 "무협은 다 비슷하니까"로 Phase 0를 시작하려 함
- 프로파일이 비어 있거나 `business_growth_profile`로 잘못 잠겨 있음
- material summary가 "전형적인 무협 세계관"처럼 추상적 일반론뿐임

## 3B. `First-Block Cider Ledger` 의무

무협도 신규 기획안 단계에서는 `first_block_cider_ledger`를 반드시 만든다.

정의:

- `TR blocks 2~6` 각각에 대해 사이다 유무와 영수증을 기록하는 5줄 ledger
- wuxguide에서는 `rank`, `elder protection`, `manual access`, `realm step`, `reputation`, `inheritance clue` 같은 토큰이 핵심이다

필수 필드:

| 키 | 의미 |
| --- | --- |
| `block_no` | `2`, `3`, `4`, `5`, `6` |
| `has_cider` | `true / false` |
| `cider_elements` | `proof`, `reevaluation`, `reward_token`, `protection`, `realm_shift`, `manual_access`, `next_gate`, `recovery_asset` |
| `visible_reward_token` | 공인 의원 자격, 장로 보호, 서고 접근권, 비급 단서 같은 구체 토큰 |
| `bridge_or_payback_note` | `has_cider = false` 블록의 허용 이유 |
| `pain_only_exit` | 고통만 남기고 닫히는지 |

Planning hard rule:

- 5줄이 정확히 다 있어야 한다
- exploratory draft에서는 false row를 hole marker로 남길 수 있지만 기본값은 `hold`
- `selection-ready` 또는 `Phase0-ready`로 넘길 때는 blocks `2~6` 다섯 줄이 모두 `has_cider = true`
- `visible_reward_token`은 같은 블록 안 payback chain에서 느껴져야 한다
- `block 6 pain_only_exit = true` 금지
- `block 7+` 비무 승리나 사사 보상으로 `2~6` 빈칸을 메우면 invalid

특히 무협에서 자주 생기는 오판:

- `고수와 만났다`만으로 사이다 처리
- `비급 단서만 얻었다`고 쓰고 토큰을 안 적음
- `block 7`의 공개 승리로 `2~6`의 무보상 opening을 구제

이 세 가지는 모두 금지다.
또한 false row를 `bridge_or_payback_note`로 구제해서 selection-ready라 우기는 것도 금지다.

## 4. 대원칙: 자기이익 우선 원칙의 Phase 0 적용

Phase 0 설계에서 주인공의 매 대단원 목표가 자기이익(경지 상승, 비급 획득, 세력 확장, 원수 제거)에 연결되어야 한다. 대의명분만 있는 대단원은 REJECT.

### 4.1 무협 자기이익의 정의

무협에서 자기이익이란 아래 중 최소 하나를 의미한다:

1. **경지 상승** — 다음 경지로의 돌파, 내공 증가, 깨달음 획득
2. **비급/보물 획득** — 무공 비급, 영약, 신병이기 등 실질 자산
3. **세력 확장** — 문파 내 지위 상승, 휘하 세력 증가, 영토 확보
4. **원수 제거** — 원한 관계 청산, 위협 요소 제거
5. **정보 획득** — 비밀 무공의 단서, 적의 약점, 보물 위치

### 4.2 좋은 예시와 나쁜 예시

**좋은 예시:**

1. "대단원 3에서 사파 교주와 충돌 -> 목표: 교주의 비급을 빼앗아 경지 돌파"
   - 자기이익: 비급 획득 + 경지 상승
   - 충돌의 이유가 주인공의 실질적 성장에 직결

2. "대단원 5에서 천마신교 장로들과 연합 -> 목표: 연합 대가로 천마공 심법 전수권 확보"
   - 자기이익: 무공 획득 + 세력 기반 확보
   - 연합 자체가 목적이 아니라 연합의 대가가 목적

3. "대단원 2에서 개방 장로를 구출 -> 목표: 구출 대가로 개방 정보망 접근권 획득 + 숨겨진 지하 금고 위치 정보"
   - 자기이익: 정보 획득 + 장기 세력 기반
   - 구출이 선의가 아니라 거래

**나쁜 예시:**

1. "대단원 3에서 강호의 평화를 위해 사파와 싸움"
   - 결함: 주인공이 얻는 것이 없음. 대의명분만 존재
   - 수정: 사파와의 충돌에서 구체적 전리품(비급, 영토, 정보)을 설계해야 함

2. "대단원 5에서 스승의 유언을 지키기 위해 무림맹을 돕는다"
   - 결함: 감정적 동기만 존재. 주인공의 경지/세력/자산에 변화 없음
   - 수정: 무림맹을 돕는 대가(맹주의 비급 열람권, 특정 자원 접근권)를 명시해야 함

3. "대단원 7에서 무고한 마을 사람들을 구한다"
   - 결함: 성인군자형 호구 패턴. 구출 자체가 최종 목표
   - 수정: 마을에 숨겨진 고대 유적의 열쇠가 있다 등 실질 이익을 연결해야 함

### 4.3 대단원별 자기이익 검증 체크리스트

매 대단원(ARC) 설계 시 아래를 통과해야 한다:

| # | 질문 | 실패 시 |
|---|------|---------|
| 1 | 이 대단원에서 주인공의 경지/무공/세력/자산 중 무엇이 증가하는가? | 증가 항목 없으면 REJECT |
| 2 | 이 증가 없이도 주인공이 같은 행동을 할까? | "예"이면 이득이 허위 |
| 3 | 대의명분이 있다면, 그 뒤에 숨은 실질 이득은? | 실질 이득 없으면 REJECT |
| 4 | 적대자를 처리한 뒤 전리품(비급/영토/세력/정보)이 있는가? | 없으면 밀도 부족 |
| 5 | 이 대단원의 성과가 다음 대단원의 자기이익에 연결되는가? | 단절되면 구조 결함 |

## 5. Phase 0 Focus

`wuxguide` planning must lock the martial-family progression frame before TR starts.

Minimum Phase 0 concerns:

- protagonist opening lack and pressure
- realm path / breakthrough ladder
- internal-energy curve
- martial-art acquisition path
- sect / clan / alliance map
- enemy ladder and grievance chain
- jianghu reputation path
- treasure / manual / elixir path
- taboo rules and irreversible costs
- npc timeline and foreshadow map

## 6. Phase 0 필수 설계 항목 (무협 특화)

### 6.1 경지 로드맵 (7대단원별 경지)

7개 대단원(ARC-01 ~ ARC-07) 각각에서 주인공이 도달하는 경지를 사전에 확정한다.

```
ARC-01: 후천초기 -> 후천중기
ARC-02: 후천중기 -> 후천절정
ARC-03: 후천절정 -> 선천 진입
ARC-04: 선천초기 -> 선천중기
ARC-05: 선천중기 -> 선천절정
ARC-06: 선천절정 -> 화경 진입
ARC-07: 화경 -> 최종 경지
```

위는 예시이며, 작품별 경지 체계에 맞춰 조정한다. 핵심 규칙:

- 대단원당 최대 2단계 상승 (급성장 방지)
- 경지 정체 대단원이 최소 1개 존재해야 함 (긴장감 유지)
- 돌파 블록은 해당 대단원의 후반부에 배치 (축적 -> 돌파 리듬)

### 6.2 무공 획득 계획 (블록별)

각 대단원에서 주인공이 습득/강화하는 무공을 사전에 배치한다:

| 대단원 | 획득 무공 | 획득 경위 | 선행 조건 |
|--------|-----------|-----------|-----------|
| ARC-01 | 기본 내공심법 | 사부 전수 | 입문 |
| ARC-02 | 핵심 검법 | 비급 발견 | 후천중기 이상 |
| ARC-03 | 보조 경공/신법 | 적대자 패배 후 전리품 | 검법 숙련 |
| ... | ... | ... | ... |

규칙:

- 미습득 무공 사용 금지 (martial_art_logic_failure 방지)
- 봉인/부상으로 사용 불가한 무공은 상태 추적 필수
- 블록 내에서 습득과 실전 투입 사이에 최소 1블록 간격 권장

### 6.3 적대자 교체 타이밍

적대자 교체는 대단원 경계에서 이루어진다. Phase 0에서 아래를 확정한다:

| 적대자 단계 | 대단원 범위 | 주요 적대자 | 교체 트리거 |
|-------------|-------------|-------------|-------------|
| 초기 | ARC-01~02 | 문파 내 경쟁자/선배 | 문파 내 지위 확보 |
| 중기 | ARC-03~04 | 타 문파/사파 세력 | 강호 진출 |
| 후기 | ARC-05~06 | 거대 세력/숨은 흑막 | 경지 돌파로 위협 대상 변경 |
| 최종 | ARC-07 | 최종 보스 | 전체 서사 귀결 |

규칙:

- 같은 적대자가 3대단원 이상 연속하면 밀도 점검 (density_failure 위험)
- 적대자 교체 시 이전 적대자의 잔여 세력/복선이 처리되어야 함
- 최종 적대자는 ARC-04 이전에 복선으로 등장해야 함

### 6.4 문파/세력 변동 계획

대단원별 세력 지도 변화를 사전에 설계한다:

- 주인공 소속 문파의 내부 권력 변동
- 동맹/적대 문파의 흥망
- 강호 전체 세력 균형의 이동
- 주인공의 세력 내 위치 변화 (제자 -> 핵심 제자 -> 장로급 -> 독립 세력)

faction_drift 방지를 위해, 문파 소속 변경은 반드시 서사적 사건과 연결해야 한다.

## 7. Recommended Phase 0 Shape

- `project`
  - title, genre code, logline, core premise
- `protagonist`
  - name, age_at_start, opening_status, initial_goal, mid_goal, final_goal, true_strength, true_weakness
- `setting`
  - era, region, jianghu_order, starting_faction, martial_doctrine
- `phase0_design`
  - arcs
  - realm_path
  - internal_energy_curve
  - martial_art_path
  - faction_map
  - npc_timeline
  - foreshadow_map
  - opponent_transition_plan
  - treasure_path
  - taboo_rules
  - do_not_fake

Output target:

```text
treatments/phase0/{work_id}_phase0_design.json
```

## 8. Stop/Go 기준 (무협 특화)

Phase 0 완료 전 아래 Stop/Go 게이트를 통과해야 한다.

### 8.1 Go 조건 (전부 충족 시 TR 진입 가능)

| # | 항목 | 기준 |
|---|------|------|
| 1 | 경지 로드맵 | 7대단원 전체의 경지 진행이 확정됨 |
| 2 | 무공 획득 계획 | 주요 무공의 습득 블록과 경위가 배치됨 |
| 3 | 적대자 교체 | 최소 3단계 적대자 교체가 설계됨 |
| 4 | 복선 지도 | foreshadow_map에 최소 5개 복선이 seed/payoff 쌍으로 존재 |
| 5 | NPC 타임라인 | 핵심 NPC 5명 이상의 등장/퇴장/전환점이 확정됨 |
| 6 | 자기이익 검증 | 모든 대단원이 자기이익 체크리스트를 통과함 |
| 7 | 금기/비가역 | taboo_rules에 최소 2개 금기가 정의됨 |
| 8 | 패배 블록 | 대단원당 최소 1개 defeat_block 존재 |
| 9 | 조용한 블록 | 대단원당 최소 1개 quiet_block 존재 |
| 10 | 핸드오프 검증 | stage0_handoff_validator.py exit 0 |

### 8.2 Stop 조건 (하나라도 해당 시 TR 진입 금지)

| # | 항목 | 증상 |
|---|------|------|
| 1 | 경지 미확정 | ARC 중 하나라도 시작/종료 경지가 비어 있음 |
| 2 | 대의명분 대단원 | 자기이익 없이 대의명분만으로 구성된 대단원 존재 |
| 3 | 적대자 부재 | 대단원에 main_opponents가 비어 있음 |
| 4 | 무공 모순 | 습득 전 사용이 계획에 포함됨 |
| 5 | 세력 점프 | 서사 없이 문파 소속이 변경되는 대단원 존재 |
| 6 | 복선 고아 | seed만 있고 payoff가 없는 복선 존재 |
| 7 | 밀도 과부하 | 같은 적대자/무공이 3대단원 연속 |
| 8 | Stage 0 부실 | stage0_handoff_validator.py exit != 0 |

## 9. Continue / Next Step

After Phase 0 is saved, rerun the router:

```bash
python -X utf8 scripts/narrative_router.py --genre wuxia --work-id <work_id>
```

Expected next stage: `production`.

## 10. Planning Guardrails

- Do not force business-power vocabulary into wuxia planning.
- Do not use `starter_company` as the primary world anchor.
- If the dominant engine is unclear, stop at router classification rather than drafting a hybrid Phase 0 blindly.
- `capital_target` 대신 경지 진행과 무공 획득을 성장 축으로 사용한다.
- `deal_type` 대신 전투, 비급 쟁탈, 세력전, 문파 정치를 핵심 진행 액션으로 사용한다.
- 현대 비즈니스 용어(매출, 정산, 운영권 등)를 무협 Phase 0에 강제하지 않는다.
- 경지 체계가 작품마다 다르므로, Phase 0 초반에 해당 작품의 경지 체계를 먼저 확정한다.
- 무공 이름과 효과를 Phase 0에서 확정하되, 상세 묘사는 TR 단계에 위임한다.
