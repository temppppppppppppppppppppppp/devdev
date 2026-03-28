# Wuxia BI Production Harness
<!-- utf8-hygiene: allow-file rationale: this harness intentionally documents literal mojibake tokens like ??? and � as detection examples. -->

> 인코딩: **UTF-8 only (기본값, 예외 없음)**
> 작성일: 2026-03-24
> 근거: `bi-production-harness-v1.md` (blockguide 표준) + `SSOT_wuxguide-integrated-order.md`
> 목적: **무협/선협 family BI를 MartialHUD 기준으로 생성-동기화-감리하는 전용 하네스**
> 출력: `bible/0_bi_{work_id}.json`
> 선행 문서: `SSOT_wuxguide-integrated-order.md`

---

## 0A. 초저지능 LLM용 빠른 시작

이 문서는 **`TR draft`가 이미 있는 상태에서만** 실행한다.
사용자가 작품명, `work_id`, `다음 스텝`만 줘도 아래 순서를 먼저 수행한다.

1. `SSOT_wuxguide-integrated-order.md`를 **UTF-8로 먼저 읽는다.**
2. `wuxia-production-harness.md`를 다시 확인해 TR이 감리 통과 상태인지, source TR audit snapshot이 있는지 본다.
3. 이 문서를 **UTF-8로 다시 읽는다.**
4. `phase0_design`, `tr_block_070_draft`, 기존 `BI`를 UTF-8로 재오픈한다.
5. `TR draft`가 없으면 BI를 만들지 말고 production 단계로 되돌린다.
6. BI는 새 창작이 아니라 동기화 작업으로 이해한다.
7. 항상 아래 순서로만 진행한다.
   - source TR handoff gate 확인
   - 최소 스켈레톤
   - 결정적 동기화
   - UTF-8 저장
   - 정합성 검증
   - 5-Pass 감리
   - PASS/FAIL 보고 후 정지
8. 하나라도 실패하면 다음 단계로 넘어가지 않는다.

추가 해석:

- TR production의 `5블록 자동 연속 cap`은 source TR 쪽 규칙이다.
- BI 단계는 block count로 환산하지 않는다.
- source TR이 70블록 완료 전이거나, 5블록 창 중간 정지 상태면 BI로 넘어가지 않는다.

금지:

- `TR draft` 없이 BI부터 만들기
- `plot_roadmap`를 기억으로 다시 요약하기
- 감리 전 BI를 완료본으로 부르기
- `FinanceHUD`를 무협 BI의 주 HUD로 사용하기

---

## 0B. SSOT 우산 정의

이 문서의 SSOT 의미는 **무협/선협 family 전용 BI**다.
Blockguide의 `FinanceHUD`(=Resource-Power HUD) 자리를 `MartialHUD`가 대체한다.

핵심 해석:

- `MartialHUD`는 무협 BI의 정식 HUD 루트다.
- `FinanceHUD`는 이 family에서 정식이 아니다. 런타임 브릿지가 명시적으로 요구할 때만 호환 alias를 허용한다.
- 핵심 성장 축은 `realm`(경지), `internal_energy`(내공), `martial_arts`(무공), `faction`(문파/세력), `jianghu_reputation`(강호 평판)이다.
- `capital_before/after`, `deal_type`, `business_lines`, `company_state`는 무협 BI의 주 앵커가 아니다.
- `portfolio_history` 대신 `realm_history`를 사용한다.

## 0C. 공통 용어표

| 용어 | SSOT 의미 |
| ---- | ---- |
| `realm` | 경지. 연마, 돌파, 마경 등으로 변하는 무공 단계 |
| `internal_energy` | 내공. 서술형으로 수준을 기록 |
| `martial_arts` | 습득 무공 목록. 이름, 출처, 숙련도 |
| `faction` | 현재 소속 문파/세력 |
| `jianghu_reputation` | 강호에서의 인지도와 평판 |
| `kill_log` | 사살 기록. 블록, 대상, 방법 |
| `injury_log` | 부상 기록. 블록, 부상, 회복 블록 |
| `foreshadow` | 복선 심기. TR에서 기록한 블록 번호 기준 |
| `callback` | 복선 회수. TR에서 기록한 블록 번호 기준 |

---

## 1. BI 생성 전제조건

### 1.1 TR Gate Pass 필수

BI 생성에 진입하려면 source TR이 아래 조건을 **모두** 통과해야 한다.

- `tr_block_070_draft` 파일이 존재하고 UTF-8 파싱 성공
- TR 블록 수 = 70
- TR 감리 결과가 PASS (skeleton draft, 반복 FAIL, density FAIL이 아님)
- source TR audit snapshot이 존재

무협 TR 전용 gate 항목:

- `martial_density_gate = PASS` (경지/무공/내공 변동이 TR 전체에 걸쳐 추적 가능)
- `realm_progression_coherent` = 경지 변동 순서가 역행하지 않음
- `npc_deceased_coherent` = 사망 NPC가 후속 블록에서 행동하지 않음
- `foreshadow_callback_linked` = 복선 심기/회수 쌍이 블록 번호로 연결됨

### 1.2 Source TR Handoff Snapshot 확인

BI handoff 전에 아래 snapshot 항목을 확인한다.

- `martial_density_gate` 상태
- `avg_bundle_chars` 또는 `avg_chars`
- `realm_transition_count` (경지 변동 횟수)
- `npc_kill_count` (NPC 사살 수)
- `foreshadow_count` / `callback_count`
- `pattern_feedback_snapshot` 또는 동등 반복 경고 요약

규칙:

- 위 항목 중 하나라도 비면 BI 진입 금지
- source TR에 반복 경고가 남아 있으면 BI 감리 보고서에 그 사실을 명시한다
- source TR에 `skeleton draft`, 반복 FAIL, density FAIL이 있으면 production 단계로 되돌린다

---

## 2. MartialHUD 구조 명세

`MartialHUD`는 blockguide의 `FinanceHUD`에 대응하는 무협 전용 HUD다.
주인공의 무공, 경지, 내공, 부상, 사살, 세력, 장비 상태를 단일 루트 아래에 추적한다.

### 2.1 전체 스키마

```json
{
  "MartialHUD": {
    "_description": "무협 전용 HUD - 경지, 내공, 무공, 세력, 장비를 추적",
    "Protagonist": {
      "actual_truth": {
        "name": "주인공 이름",
        "alias": "강호 별호",
        "age": 0,
        "rank": "현재 직위 또는 강호 위치",
        "martial_status": {
          "realm": "현재 경지 (예: 화경, 현경, 절정, 초절정, 선천)",
          "realm_history": [
            {
              "block": 1,
              "realm": "후천초기",
              "event": "입문 시점"
            }
          ],
          "internal_energy": "내공 수준 서술 (예: 삼류 수준의 내공, 일류 수준에 근접한 내력 등)",
          "martial_arts": [
            {
              "name": "무공명",
              "origin": "출처 (비급, 사부, 깨달음 등)",
              "proficiency": "숙련도 (입문/소성/대성/화경)"
            }
          ],
          "injury_log": [
            {
              "block": 0,
              "injury": "부상 내용",
              "recovery_block": 0
            }
          ],
          "kill_log": [
            {
              "block": 0,
              "target": "대상",
              "method": "수단"
            }
          ]
        },
        "faction_status": {
          "current_faction": "현재 소속 문파/세력",
          "faction_history": [
            {
              "block": 1,
              "faction": "문파명",
              "role": "역할 (제자, 장문인, 객경 등)",
              "event": "입문/이탈/승진 사유"
            }
          ],
          "ally_factions": [],
          "enemy_factions": []
        },
        "equipment": {
          "weapons": [
            {
              "name": "무기명",
              "grade": "등급 (범철/보병/신병/천하명병)",
              "origin": "출처"
            }
          ],
          "artifacts": []
        },
        "jianghu_reputation": {
          "jianghu_title": "강호에서 불리는 칭호",
          "feared_by": [],
          "trusted_by": [],
          "rumor_state": "현재 강호에 퍼진 소문"
        },
        "current_objective": "현재 단기 목표",
        "mid_term_goal": "중기 목표",
        "final_goal": "최종 목표",
        "causal_injuries": "과거 상처 / 동기 배경"
      },
      "public_reputation": {
        "identity": "강호에 알려진 정체",
        "perceived_strength": "외부에서 인식하는 무력 수준",
        "perceived_faction": "외부에서 인식하는 소속",
        "jianghu_credit": "강호 신뢰도"
      }
    }
  }
}
```

### 2.2 필드별 SSOT 규칙

#### `realm` (현재 경지)

- 반드시 source TR 마지막 블록의 `martial_ext.realm_after`와 일치해야 한다.
- 경지 표기는 작품 내 용어를 그대로 사용한다 (예: 화경, 현경, 절정, 초절정).
- 경지를 임의 추정하거나 일반 용어로 치환하지 않는다.

#### `realm_history`

- 각 항목은 `{block, realm, event}` 3개 필드를 가진다.
- TR의 `martial_ext.realm_before` → `realm_after` 변동 블록에서 자동 추출한다.
- 수동 재작성 금지. TR에 기록된 블록 번호와 경지만 복사한다.

#### `internal_energy` (내공 수준)

- 서술형 필드다. 숫자 레벨이 아니라 작품 내 내공 표현을 그대로 옮긴다.
- 예: "삼십 년 내공", "선천진기 초입", "음양조화의 내력"

#### `martial_arts` (무공 목록)

- `name`: 무공 이름 (작품 내 명칭 그대로)
- `origin`: 비급, 사부 전수, 깨달음, 탈취 등
- `proficiency`: 입문 / 소성 / 대성 / 화경 / 절정 (작품 내 표현 기준)
- TR 마지막 블록 기준 최종 상태를 기록한다.
- `origin`과 `proficiency`는 작품 내부 사실만 적는다.
- `B43`, `Block 43`, `B19→B46` 같은 제작 추적 문자열을 넣지 않는다.
- `phase0_design.martial_art_path.evolution`은 제작 추적 메모일 수 있으므로 BI에 verbatim 복사하지 않는다.

#### `injury_log`

- `block`: 부상 발생 블록
- `injury`: 부상 내용
- `recovery_block`: 회복된 블록 (미회복 시 `null`)
- TR의 `martial_ext` 또는 서사 내 부상 이벤트에서 추출한다.

#### `kill_log`

- `block`: 사살 발생 블록
- `target`: 대상 이름
- `method`: 사살 수단
- NPC deceased 상태 정합성 검증의 기준 데이터가 된다.

#### `faction_status`

- `current_faction`: TR 마지막 블록 기준 소속
- `faction_history`: 문파 입문, 이탈, 파문, 승진 등 변동 이력
- `ally_factions` / `enemy_factions`: TR 마지막 블록 기준 동맹/적대 세력 목록

#### `equipment`

- `weapons`: 현재 소지 무기. `grade`는 작품 내 등급 체계를 따른다.
- `artifacts`: 비급, 영단, 보물 등 특수 물품

---

## 3. `plot_roadmap` 동기화 규칙

### 3.1 핵심 원칙

`plot_roadmap`는 **창작 대상이 아니라 동기화 대상**이다.

- 반드시 `TR draft`에서 복사 생성한다.
- LLM이 기억에서 다시 요약하거나 재작성하는 것을 금지한다.
- compaction 이후에도 메모리 재구성 금지, 먼저 `TR draft`를 다시 열어 확인한다.

### 3.2 최소 동기화 규칙

- 길이 = 70
- `plot_roadmap[n].title == TR[n].title`
- 가능하면 TR draft의 블록 객체 전체를 그대로 복사한다.
- 요약 필드가 따로 필요하면 `TR[n].content.context`를 사용한다.

### 3.3 무협 전용 동기화 필드

blockguide에서 `capital_before/after`를 동기화하듯, 무협 BI에서는 아래를 동기화한다:

- `realm_before` / `realm_after`: 해당 블록 전후 경지
- `martial_event`: 해당 블록의 무공/내공/경지 관련 핵심 이벤트
- `foreshadow` / `callback`: 복선 심기/회수 블록 번호

이 값들은 TR의 `martial_ext` 섹션에서 복사한다.

### 3.4 금지 사항

- `plot_roadmap`를 수동으로 70개 다시 요약
- 다른 작품 BI의 roadmap을 복붙 후 일부 치환
- 깨진 roadmap을 기준으로 덮어쓰기
- compaction 후 기억으로 roadmap 재조립
- BI 서술 텍스트에 `B숫자`, `Block 숫자`, `블록 숫자`를 그대로 남기기

허용 예외:

- `block_id`
- `block`
- `ref`
- `recovery_block`
- `first_block`

즉 블록 참조는 metadata key에만 남길 수 있다. `martial_arts.origin`, `Seeds.description`, `CommercialCode`, `foreshadow[].event`, `callback[].event` 같은 서술 필드로 흘러들면 FAIL이다.

---

## 4. BI 계약 계층: P0 (최소 계약) vs P1 (확장 계약)

BI 계약은 한 번에 전부 P0로 올리지 않는다.
문서가 실제 생성기/감리보다 앞서가며 거짓 요구를 하지 않도록 최소 계약(P0)과 확장 계약(P1)을 분리한다.

### 4.1 최소 계약 (P0)

- `plot_roadmap` 길이 70
- `plot_roadmap` title sequence가 source `TR draft`와 일치
- `CoreIdentity.protagonist == MartialHUD.Protagonist.actual_truth.name`
- `MasterBible.ProjectData.MetaInfo.title` 정상 한글
- `MartialHUD.Protagonist.actual_truth.martial_status.realm`이 source TR 최종 `martial_ext.realm_after`와 일치
- `MartialHUD.Protagonist.actual_truth.faction_status.current_faction`이 source TR 최종 블록과 충돌하지 않음
- NPC deceased 정합성: `kill_log`에 기록된 NPC가 이후 블록에서 행동하지 않음
- source TR handoff gate PASS
- UTF-8 / JSON 파싱 PASS

### 4.2 확장 계약 (P1)

- `realm_history` 전체 이력
- `martial_arts` 상세 숙련도 추적
- `injury_log` 전체 부상/회복 이력
- `kill_log` 전체 사살 이력
- `equipment` 상세 무기/보물 이력
- `jianghu_reputation` 상세 칭호/소문 추적
- `faction_history` 세력 변동 전체 이력
- `public_reputation` 상세 외부 인식
- `foreshadow_map` / `callback_map` 상세 복선 추적

### 4.3 승격 규칙

P1 필드를 P0로 올리려면 아래 3개를 모두 만족해야 한다:

1. 생성기/빌더가 source TR에서 해당 필드를 결정적으로 채울 수 있어야 한다.
2. 최근 골든 BI 3개 이상이 실제로 그 필드를 안정적으로 채워야 한다.
3. 감리 스크립트/수동 감리가 그 필드를 재현 가능하게 검사할 수 있어야 한다.

---

## 5. BI 생산 아키텍처: 5-Phase + 5-Pass

```text
Phase 0: 원천 고정
  ↓ phase0_design + tr_block_070_draft 확인 + source TR gate
Phase 1: BI 최소 스켈레톤 작성
  ↓ MasterBible / ProjectData / MartialHUD 뼈대
Phase 2: 결정적 동기화
  ↓ plot_roadmap / martial_status / realm_history / faction / npc_timeline / seeds 주입
Phase 3: UTF-8 저장 + 오염 탐지
  ↓ ??? / � / 공백 주인공명 / stale title 탐지
Phase 4: TR↔BI 정합성 검증
  ↓ protagonist / 길이 / realm 동기 / NPC deceased / foreshadow-callback
Phase 5: 5-Pass 감리
  ↓ PASS 1~5 전부 통과 시 확정
```

### 5.1 Phase 0: 원천 고정

BI 생성 전에 아래를 먼저 확인한다:

- `phase0_design` UTF-8 파싱 성공
- `TR draft` UTF-8 파싱 성공
- `phase0_design` 최소 필수 시트(`arcs`, `npc_timeline`, `foreshadow_map`, `opponent_transition_plan`) 존재
- `TR draft` 블록 수 70
- `TR draft` 첫 블록/마지막 블록 title 확인
- source TR handoff gate 전 항목 PASS

### 5.2 Phase 1: BI 최소 스켈레톤

```json
{
  "_schema_version": "2.0",
  "_schema_description": "작품 설명",
  "_last_updated": "YYYY-MM-DD",
  "_genre": "wuxia",
  "MasterBible": {
    "ProjectData": {
      "MetaInfo": {
        "title": "작품명"
      }
    },
    "protagonist_config": {},
    "MartialHUD": {
      "Protagonist": {
        "actual_truth": {
          "name": "",
          "martial_status": { "realm": "" }
        }
      }
    },
    "plot_roadmap": []
  }
}
```

주의: 모든 섹션은 반드시 `MasterBible` 객체 안에 위치해야 한다.
최상위에 놓으면 `bi_wuxguide.schema.json` 위반.

규칙:

- 처음부터 모든 섹션을 장문으로 채우지 않는다.
- 스켈레톤 생성 후 바로 UTF-8/JSON 파싱 검사를 한 번 통과시킨다.
- `_genre`는 반드시 `"wuxia"` 또는 해당 martial-family 코드를 사용한다.

### 5.3 Phase 2: 결정적 동기화

#### `plot_roadmap`

- 길이 = 70
- `TR draft`에서 복사 생성
- 무협 전용 필드(`realm_before`, `realm_after`, `martial_event`, `foreshadow`, `callback`) 포함

#### `MartialHUD` 동기화

- `realm`: TR 마지막 블록의 `martial_ext.realm_after`에서 복사
- `realm_history`: TR 전체의 경지 변동 블록에서 추출
- `martial_arts`: TR 마지막 블록 기준 최종 무공 목록
- `internal_energy`: TR 마지막 블록 기준 내공 서술
- `faction_status`: TR 마지막 블록 기준 세력 상태
- `injury_log`: TR 전체에서 부상 이벤트 추출
- `kill_log`: TR 전체에서 사살 이벤트 추출

#### 파생 섹션 (phase0_design 기반)

최소 필수:

- `npc_timeline`
- `Seeds` (복선)
- `FactionMap` (세력 관계도)
- `opponent_transition_plan`

권장 확장:

- `Treasures` (비급/영단/보물 목록)
- `WorldState` (강호 현황, 시대 배경)
- `GenreRules` (작품 내 무공/경지 체계)

### 5.4 Phase 3: UTF-8 저장 규칙

- 출력 파일명은 ASCII 기준: `bible/0_bi_{work_id}.json`
- 파일 내용은 UTF-8, BOM 없음
- JSON 저장은 Python `-X utf8` 또는 검증된 편집기만 사용
- `json.dumps(..., ensure_ascii=False, indent=2)`

오염 탐지:

- `???`, `�` 0건이어야 PASS
- 한글 필드가 하나라도 깨지면 부분 수선보다 재생성 우선

### 5.5 Phase 4: TR↔BI 정합성 검증

- `BI.plot_roadmap` 길이 = 70
- 첫/마지막 title 일치
- 전 title 리스트 순서 일치
- `MartialHUD.Protagonist.actual_truth.martial_status.realm` == source TR 최종 `realm_after`
- `kill_log`에 기록된 NPC가 후속 블록에서 행동하지 않음
- `foreshadow`/`callback` 블록 번호가 TR과 일치
- source TR audit snapshot 존재

---

## 6. 5-Pass 감리 체크리스트 (무협 특화)

### PASS 1: 인코딩/파싱

통과 조건:

- UTF-8 읽기 성공
- JSON 파싱 성공
- `???`, `�` 0건
- metadata key를 제외한 서술 텍스트에서 `B숫자`, `Block 숫자`, `블록 숫자` 0건

실패 시 조치:

- 손상 필드가 넓으면 부분 수정 금지
- `phase0_design + TR draft` 기준으로 BI 재생성

### PASS 2: 최소 스키마 + plot_roadmap

통과 조건:

- `MasterBible.ProjectData.MetaInfo.title` 존재하고 정상 한글
- `plot_roadmap` 길이 = 70
- `plot_roadmap` title sequence가 source `TR draft`와 **전수 일치**
- `MartialHUD` 루트 키 존재
- `MartialHUD.Protagonist.actual_truth` 존재

### PASS 3: 주인공 경지 최종값 동기화

통과 조건:

- `CoreIdentity.protagonist == MartialHUD.Protagonist.actual_truth.name`
- `MartialHUD.Protagonist.actual_truth.martial_status.realm` == source TR 마지막 블록의 `martial_ext.realm_after`
- `internal_energy` 서술이 TR 마지막 블록과 충돌하지 않음
- `martial_arts` 최종 목록이 TR에서 습득한 무공과 충돌하지 않음
- `faction_status.current_faction`이 TR 마지막 블록과 충돌하지 않음

실패 유형:

- 경지 불일치: `realm`이 TR 최종 블록과 다름 → P0 FAIL
- 내공 모순: TR에서 내공 상실 이벤트가 있는데 BI에 반영 안 됨 → P0 FAIL
- 문파 불일치: TR에서 파문/탈퇴했는데 BI에 여전히 소속 → P0 FAIL

### PASS 4: NPC Deceased 상태 정합성

통과 조건:

- `kill_log`에 기록된 NPC가 해당 `block` 이후의 `plot_roadmap` 블록에서 **행동 주체로 등장하지 않음**
- 사망 NPC가 회상/언급으로만 등장하는 것은 허용
- `npc_timeline`에서 해당 NPC의 `status`가 `deceased`로 표시됨
- 사망 블록 번호가 `kill_log`와 `npc_timeline` 간 일치

검증 방법:

1. `kill_log`에서 `{block, target}` 쌍을 모두 추출한다.
2. `plot_roadmap`에서 해당 `target`이 `block` 이후에 행동 주체로 나오는지 확인한다.
3. `npc_timeline`에서 해당 NPC의 최종 상태가 `deceased`인지 확인한다.
4. 불일치 시 P0 FAIL.

### PASS 5: 복선 심기/회수 블록 번호 정합성

통과 조건:

- BI의 `Seeds` 또는 `foreshadow_map`에 기록된 복선 심기 블록 번호가 TR의 `foreshadow` 기록과 일치
- BI의 복선 회수 블록 번호가 TR의 `callback` 기록과 일치
- 심어진 복선 중 미회수 항목은 `status: open`으로 명시
- 회수된 복선의 `callback_block`이 `foreshadow_block`보다 후순위
- 한국어 필드에 `??`, `???` 없음
- 다른 작품 흔적 없음
- 문파명, NPC 이름, 세력명이 작품 내 표기와 일치

실패 규칙:

- source TR이 `skeleton draft`, 반복 FAIL, density FAIL이면 BI 구조 정합성과 무관하게 `final_verdict = FAIL`
- 복선 블록 번호가 1건이라도 어긋나면 해당 항목 수정 후 재감리

### 감리 결과 형식

```text
=== Wuxia BI 5-Pass Audit ===
Work: {work_id}
Date: {date}

PASS 1 (인코딩/파싱): OK / FAIL
PASS 2 (스키마/roadmap): OK / FAIL
PASS 3 (경지 최종값): OK / FAIL
PASS 4 (NPC deceased): OK / FAIL
PASS 5 (복선 정합성): OK / FAIL

Final Verdict: PASS / FAIL
Notes: ...
```

---

## 7. Minimum BI Sections

무협 BI에 포함되어야 하는 최소 섹션 (모두 `MasterBible` 내부):

- `MasterBible.ProjectData` (MetaInfo, CoreIdentity, CommercialCode)
- `MasterBible.protagonist_config`
- `MasterBible.MartialHUD`
- `MasterBible.plot_roadmap`
- `MasterBible.WorldState`
- `MasterBible.AssetLibrary.KeyNPCs`
- `MasterBible.FactionMap`
- `MasterBible.Treasures`
- `MasterBible.Seeds`

주의: 위 섹션은 **반드시 `MasterBible` 객체 안에** 위치해야 한다.
최상위에 놓으면 스키마(`bi_wuxguide.schema.json`) 위반이며, 빌더/런타임이 읽지 못한다.

---

## 8. Routed Commands

Build:

```bash
python -X utf8 scripts/build_narrative_bi.py --genre wuxia --phase0 treatments/<work_id>_phase0_design.json --draft treatments/<work_id>_tr_block_070_draft.json --output bible/0_bi_<work_id>.json
```

Audit:

```bash
python -X utf8 scripts/audit_narrative_bi.py --genre wuxia --phase0 treatments/<work_id>_phase0_design.json --draft treatments/<work_id>_tr_block_070_draft.json --bi bible/0_bi_<work_id>.json --report bible/audit_reports/<work_id>_wuxia_bi_5pass.md
```

---

## 9. TR→BI Handoff 프로토콜

### 9.1 `다음 스텝` 기반 Handoff

| 사용자 입력 시점 | 기본 행동 | 출력 단위 |
| ---------------- | --------- | --------- |
| TR 70블록 draft 직후 | Phase 0 / TR 원천 재오픈 | handoff 준비 |
| 그다음 `다음 스텝` | BI 최소 스켈레톤 + 결정적 동기화 | `0_bi_{work_id}.json` |
| 그다음 `다음 스텝` | UTF-8 저장 검증 + 5-Pass 감리 | 감리 report |
| 그다음 `다음 스텝` | 중간 산출물 정리 또는 최종 패키징 | 보존본만 남김 |

### 9.1A BI auto-handoff boundary

TR production의 5블록 cap은 BI 단계에 그대로 적용하지 않는다.
BI는 block 단위가 아니라 handoff 단위로 움직인다.

규칙:

1. BI auto-run은 `스켈레톤 -> 결정적 동기화 -> UTF-8 저장 -> 5-Pass 감리` **1사이클**까지만 허용한다.
2. PASS 또는 FAIL 보고가 나오면 그 지점에서 멈춘다. 같은 오더로 BI를 무한 재생성하지 않는다.
3. source TR이 5블록 cap 때문에 중간 정지한 상태라면 BI로 넘어가지 않는다. BI 시작 조건은 `TR 70블록 완료 + source TR handoff gate PASS`다.

### 9.2 강제 정지 게이트

- `TR draft` 또는 `phase0_design` 부재
- source TR audit snapshot 부재
- source TR martial_density/realm FAIL
- `plot_roadmap` title 불일치
- `???` / `�` 탐지
- 감리 FAIL
- NPC deceased 모순 탐지
- PASS/FAIL 보고 완료 후 새 오더 대기

---

## 10. 실패 시 복구 원칙

### 10.1 부분 수선보다 재생성 우선

아래 중 하나면 재생성이 더 빠르다:

- `???`가 10개 이상
- 상단 메타와 NPC/Location까지 넓게 깨짐
- `plot_roadmap` title이 다수 어긋남
- compaction 직후 메모리 기반 수선이 이미 한 번 섞임
- `realm`이나 `faction` 상태가 TR과 전면적으로 어긋남

### 10.2 절대 금지

- 깨진 BI를 기준으로 다시 덮어쓰기
- 깨진 한글을 추측 복원해서 대량 치환
- `plot_roadmap`를 수동으로 70개 다시 요약
- `realm_history`를 기억으로 재구성

### 10.3 정석 복구 순서

1. 손상된 BI 보관 또는 폐기
2. `phase0_design` 확인
3. `TR draft` 확인
4. BI 최소 스켈레톤 재생성
5. `plot_roadmap` 결정적 복사
6. `MartialHUD` 결정적 동기화
7. 5-Pass 감리 재실행

---

## 11. BI Guardrails

- `FinanceHUD`는 이 family에서 정식이 아니다.
- 호환 alias는 런타임 브릿지가 명시적으로 요구할 때만 허용한다.
- `plot_roadmap` title sequence는 TR과 정확히 일치해야 한다.
- `realm`, `internal_energy`, `faction`, `jianghu_reputation` 최종 상태는 TR 마지막 블록과 모순되지 않아야 한다.
- 문파/세력/강호 상태를 일반 placeholder로 남기지 않는다.
- `capital_before/after`, `deal_type`, `business_lines`, `company_state`를 무협 BI의 주 앵커로 강제하지 않는다.
- 사망 NPC가 후속 블록에서 행동 주체로 등장하면 즉시 FAIL.
- 복선 심기/회수 블록 번호가 TR과 어긋나면 즉시 수정 후 재감리.

---

## 12. 수동 운영 체크리스트

- [ ] `phase0_design` UTF-8 파싱 성공
- [ ] `TR draft` UTF-8 파싱 성공
- [ ] `phase0_design` 최소 필수 시트 존재
- [ ] source TR handoff gate 전 항목 PASS
- [ ] BI 파일명 ASCII 사용
- [ ] BI 저장은 UTF-8 only
- [ ] `_genre` = `"wuxia"`
- [ ] `plot_roadmap`는 TR에서 복사 (길이 70, title 전수 일치)
- [ ] `CoreIdentity.protagonist == MartialHUD.Protagonist.actual_truth.name`
- [ ] `realm` == TR 마지막 블록 `martial_ext.realm_after`
- [ ] `internal_energy` TR 마지막 블록과 충돌 없음
- [ ] `martial_arts` TR 습득 무공과 충돌 없음
- [ ] `current_faction` TR 마지막 블록과 충돌 없음
- [ ] NPC deceased 정합성 통과
- [ ] 복선 심기/회수 블록 번호 TR과 일치
- [ ] `???` 0건
- [ ] JSON 파싱 성공
- [ ] 5-Pass 감리 결과 문서 기록
- [ ] BI 생성 직후 수동 감리 메모 1회 작성

---

## 13. 실전 규칙 한 줄 요약

**BI는 생성물이 아니라 동기화 산출물이다.**
한글 장문을 다시 쓰지 말고, `phase0_design`과 `TR draft`를 UTF-8로 읽어 `MartialHUD` 중심으로 구조화해서 저장하고 5-Pass로 감리한다.
