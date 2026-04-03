# Planning Candidate / Pre-Phase0 Spec Draft

Date: 2026-04-03  
Workspace: `C:\Users\wjjo\Desktop\글도비_process`  
Branch: `ops/process-standardization`  
Status: draft save before 3-pass audit

## 1. Role

- `planning_candidate`는 `BI/TR 이전`의 기획 후보 단위다.
- 이 레이어의 질문은 `그래서 무슨 이야기를 쓸 것인가`다.
- 이 레이어는 아직 `BI/TR 필드 채우기`가 아니라 `이야기 후보의 성립 여부`를 판정한다.
- `trend_snapshot`이 표면 신호를 주고, `engine_bank`가 구조적 동력을 주며, `planning_candidate`는 둘을 결합해 실제 작품 후보를 만든다.

간단히 자르면:

- `trend_snapshot`: 지금 무엇이 먹히는가
- `engine_bank`: 이야기를 굴리는 핵심 동력은 무엇인가
- `planning_candidate`: 이번 주에 실제로 밀어 볼 이야기 후보는 무엇인가
- `phase0 -> TR -> BI`: 선택된 후보를 생산 규격으로 내리는 단계

## 2. Why This Layer Exists

- 플랫폼 트렌드만 보면 `포장`은 잡히지만 `이야기 뼈대`가 약해진다.
- 엔진 bank만 보면 구조는 강하지만 `왜 지금 이 이야기인가`가 약해질 수 있다.
- 따라서 `planning_candidate`는 `트렌드 적합성`과 `이야기 동력`을 동시에 통과해야 한다.
- 목표는 `주간별로 BI/TR를 바로 찍는 것`이 아니라 `주간별로 기획 후보를 만들고, 그중 일부만 BI/TR로 승격하는 것`이다.

## 3. Candidate Unit Definition

`planning_candidate` 하나는 최소한 아래를 답할 수 있어야 한다.

- 주인공은 무엇을 장기적으로 원하나
- 주인공은 지금 당장 무엇을 단기적으로 원하나
- 주인공만 가진 정보격차 또는 판독 우위는 무엇인가
- 그 우위가 실제 유능함으로 드러나는 과정은 무엇인가
- 이 이야기의 핵심 소재와 전장은 무엇인가
- 초반 1~3화, 혹은 첫 block에서 독자에게 어떤 임팩트를 줄 것인가
- 이 이야기의 장기 성장선은 무엇인가
- 지금 플랫폼에서 왜 이 포장으로 내야 하는가

## 4. Draft Field Set

아래는 `planning_candidate.v0`의 권장 필드다.  
아직 고정 스키마로 잠그기보다는, `이 정도를 빠짐없이 적을 것`이라는 draft contract로 본다.

### 4-1. Metadata

- `candidate_id`
  - 주간 후보 식별자
- `week_of`
  - 어떤 주간 배치에서 나온 후보인지
- `track_family`
  - 예: `modern_business`, `office_power`, `chaebol`, `alt_history_business`
- `status`
  - 예: `draft`, `shortlisted`, `phase0_ready`, `hold`, `drop`
- `source_inputs`
  - 어떤 `trend_snapshot`, 어떤 `engine_bank` 후보를 조합했는지

### 4-2. Trend Fit

- `why_now`
  - 왜 지금 이 포장/소재가 맞는가
- `trend_surface`
  - 플랫폼에서 바로 보이는 표면 신호
  - 예: `천재`, `회귀`, `재벌`, `반도체`, `회사원`, `미국`
- `platform_fit`
  - `문피아 / 카카오 / 네이버` 중 어느 쪽 감각에 가까운가
- `market_position`
  - 이미 많은 것과 무엇이 비슷하고, 무엇이 다른가

### 4-3. Story Core

- `one_line_premise`
  - 작품 후보를 한 줄로 말했을 때의 핵심 문장
- `protagonist_position`
  - 주인공이 서 있는 자리
  - 예: 인턴, 대기업 본사 실무자, 후계 경쟁 탈락자, 좌천 엔지니어
- `long_term_goal`
  - 장기 목적
  - 예: 그룹 승계, 산업 관문 장악, 가문 복구, 제국형 확장
- `short_term_goal`
  - 당장의 목적
  - 예: 이번 주 고객 인증 재심 열기, 해고 회피, 직보권 확보, 첫 정산권 회수
- `information_gap`
  - 주인공만 보는 정보 바깥의 정보
  - 예: 숫자 은폐, 병목 공정, 숨은 돈줄, 규격 문구, 정산 테이블
- `competence_process`
  - 주인공의 유능함이 독자에게 어떻게 증명되는가
  - 권장 형식: `판독 -> 개입 -> 뒤집기 -> 보상`
- `core_engine`
  - 이 후보를 실제로 굴리는 대표 엔진
- `major_materials`
  - 핵심 소재 묶음
  - 예: 반도체 후공정, 장례/급식/호텔 운영망, 항만/보험/재보험, 데이터센터/전력

### 4-4. Reader Promise

- `promise_to_reader`
  - 독자가 이 작품에서 얻는 핵심 대리만족
- `power_fantasy`
  - 정보 우위, 권한 회수, 복수, 승계, 병목 독점 중 어디에 가까운가
- `contamination_guard`
  - 이 후보가 어디로 새면 안 되는가
  - 예: 휴먼드라마화, 일상물화, 투자썰화, 설명충화

### 4-5. Early Impact

- `opening_spike`
  - 1화에서 박아야 하는 첫 인상
- `episodes_1_to_3_impact`
  - 1~3화 안에서 독자에게 체감시킬 임팩트
  - 예: 공개 망신, 직보권 확보, 재심의, 첫 현금흐름, 첫 권한 이동
- `first_block_problem`
  - 첫 block가 해결해야 하는 문제
- `first_block_reward`
  - 첫 block를 통과했을 때 얻는 보상
  - 돈, 사람, 규칙, 직위, 입장권 중 무엇인가
- `early_antagonist`
  - 초반에 바로 부딪히는 적대자/관문
- `proof_scene`
  - 주인공만 할 수 있는 걸 처음 증명하는 장면

### 4-6. Growth Shape

- `power_curve`
  - 작은 승리에서 어떤 확장선으로 가는가
- `sector_expansion_path`
  - 한 섹터에서 끝나는지, 복수 섹터로 번지는지
- `repeatable_loop`
  - 이 작품이 반복 가능한 재미 단위를 갖는가
  - 예: `병목 판독 -> 권한 회수 -> 다음 관문 개방`

### 4-7. Go / No-Go

- `phase0_readiness_note`
  - 지금 바로 Phase0로 올릴 수 있는가
- `known_risks`
  - 약한 점이 무엇인가
- `needs_more_material`
  - 추가 자료 수집이 필요한가
- `director_checkpoints`
  - 사람 판단이 꼭 필요한 지점

## 5. Minimal Example Shape

```json
{
  "candidate_id": "PC-2026-W14-001",
  "week_of": "2026-W14",
  "track_family": "modern_business",
  "status": "draft",
  "source_inputs": {
    "trend_snapshot": ["platform_trend_w14"],
    "engine_bank": ["CAND-064", "CAND-053"]
  },
  "one_line_premise": "좌천된 품질 실무자가 고객 인증 탈락 직전의 후공정 병목을 먼저 읽고, 재심의를 열어 그룹 후계전 입장권을 따낸다.",
  "protagonist_position": "대기업 전자 계열사 품질/전략 실무자",
  "long_term_goal": "관문 섹터를 묶어 그룹 실권을 먹는다.",
  "short_term_goal": "이번 주 고객 인증 재심을 열고 회장 직보권을 확보한다.",
  "information_gap": "진짜 문제는 설계가 아니라 검사 공정의 미세균열과 잘못된 배치다.",
  "competence_process": "병목 판독 -> 사람 재배치 -> 재심 성립 -> 직보권 확보",
  "core_engine": "인증 규격 병목 장악 엔진",
  "major_materials": ["반도체 후공정", "고객 인증", "재무/결재선", "후계전"],
  "opening_spike": "남들은 축하하는 날, 주인공만 다음 주 인증 탈락을 안다.",
  "episodes_1_to_3_impact": "독대권 확보 -> 숨은 원인 폭로 -> 첫 재심의 성립",
  "first_block_problem": "고객 인증 탈락을 막지 못하면 주인공은 다시 구경꾼으로 밀려난다.",
  "first_block_reward": "회장 직보권 + 지휘권 + 인사 이동권",
  "promise_to_reader": "남들이 비용센터로 보던 병목을 주인공만 돈줄과 권력줄로 바꾼다.",
  "contamination_guard": "기술 설명물이나 투자썰로 새지 말고, 항상 권한 이동으로 보상할 것."
}
```

## 6. Judgement Questions

`planning_candidate`는 아래 질문에 답하지 못하면 Phase0로 올리지 않는다.

1. 주인공은 장기적으로 무엇을 원하는가
2. 주인공은 지금 당장 무엇을 원하고, 왜 급한가
3. 주인공만 가진 정보격차는 무엇인가
4. 그 정보격차가 실제 유능함으로 어떻게 증명되는가
5. 이 이야기의 핵심 소재와 전장은 무엇인가
6. 1~3화 안에 독자에게 보여 줄 첫 사이다/첫 임팩트는 무엇인가
7. 첫 block를 통과하면 무엇을 보상으로 얻는가
8. 이 보상이 다음 block나 다음 성장선으로 이어지는가
9. 지금 플랫폼 트렌드와 맞는 포장은 무엇인가
10. 이 후보가 흔한 유사작과 갈라지는 차별점은 무엇인가
11. 어디로 새면 망하는가
12. 지금 바로 Phase0로 올릴 수 있는가, 아니면 재료를 더 캐야 하는가

## 7. Hard Gate

아래 중 하나라도 비면 `hold`다.

- `long_term_goal`
- `short_term_goal`
- `information_gap`
- `competence_process`
- `major_materials`
- `episodes_1_to_3_impact`
- `first_block_reward`
- `promise_to_reader`

이유:

- 장기/단기 목적이 없으면 이야기가 안 굴러간다.
- 정보격차가 없으면 주인공만의 이유가 없다.
- 유능함 증명 과정이 없으면 말뿐인 천재가 된다.
- 주요 소재가 없으면 간판만 있고 실물이 없다.
- 초반 임팩트가 없으면 플랫폼 포장과 맞지 않는다.
- 첫 block 보상이 없으면 다음 블록으로 못 이어진다.

## 8. Weekly Operating Flow

주간 운영은 아래 순서가 가장 안정적이다.

1. `trend_snapshot`를 만든다.
2. 이번 주에 먹히는 표면 신호를 추린다.
3. `engine_bank`에서 구조적으로 강한 엔진을 고른다.
4. `planning_candidate` 10~20개를 만든다.
5. `Judgement Questions`로 1차 컷을 한다.
6. 살아남은 것만 `shortlist`로 올린다.
7. shortlist 중 일부만 `Phase0`로 승격한다.
8. 잘 나온 `Phase0/BI/TR` 결과는 다시 `engine_bank`와 `planning_candidate` 규격에 피드백한다.

## 9. Recommended Working Principle

- `trend`는 뼈대가 아니라 포장과 입구를 정한다.
- `engine`는 실제 이야기 동력이다.
- `planning_candidate`는 `trend x engine x protagonist position x early reward`의 결합물이다.
- 좋은 후보는 `정보 우위`만 있는 게 아니라 `권한 이동`까지 보여 준다.
- 좋은 후보는 `첫 block 보상`이 다음 block 입장권으로 이어진다.

## 10. Immediate Next Use

- 현재 저장된 `modern_business_candidate_engine_bank.draft.json` 100개를 이 spec 기준으로 다시 거른다.
- 각 후보에 대해 최소 `long_term_goal / short_term_goal / information_gap / competence_process / early impact`를 채운다.
- 그다음 상위 후보만 `Phase0-ready shortlist`로 승격한다.

## 11. Explicit Non-Claim

- 이 문서는 `BI/TR 스키마`를 대체하지 않는다.
- 이 문서는 아직 최종 계약이 아니다.
- 이 문서는 `BI/TR 이전의 기획 후보 레이어`를 정리한 draft다.
