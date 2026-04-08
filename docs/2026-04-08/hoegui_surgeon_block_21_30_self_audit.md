# hoegui_surgeon — Blocks 21-30 10-Block Self-Audit

Date: 2026-04-08
Scope: harness v2 §1.1C 10-block self-audit (Block 30 완료 boundary)
Work ID: `hoegui_surgeon`
Audit class: mandatory pre-next-batch audit (Block 31 생산 금지 해제 조건)
Basis:
- `treatments/hoegui_surgeon_tr_block_020_draft.json` (Blocks 21-30, current)
- `treatments/phase0/hoegui_surgeon_phase0_design.json` (ARC-03 완료 상태 + ARC-04 31-40 예정)
- `work_guards/12_hoegui_surgeon.yaml`
- `docs/2026-04-08/hoegui_surgeon_live_status.md`
- `docs/2026-04-08/hoegui_surgeon_block_21_25_batch_audit.md` (상위 통합 대상, 중복 지적은 참조만)
- `docs/blockguide/treatment-production-harness-v2.md` §1.1C 10-block 자체 감리

Relationship to prior audit:
- 21-25 batch audit는 ARC-03 opening batch의 sub-scope 감리 (CONDITIONAL PASS)
- 본 10-block audit는 21-30 전체를 단일 단위로 재평가하고 31-40 진입 적격성을 판정

## 1. Audit Scope

- primary: Block 21-30 (ARC-03 전체 10블록)
- backward anchor: Block 20 말미 (ARC-02 exit 상태)
- forward anchor: Phase0 ARC-04 slot 31-40 (Block 31 진입 조건)
- out-of-scope: Blocks 1-20 본문, Block 31+ 생산, Phase0/work_guard/harness 본문, BI 일체, live_status 갱신 (별도 `status_sync` 스코프)

## 2. Block-by-Block Summary Table

| Block | Title | auth Δ | beat | tension | opponent | 기능 |
|---|---|---|---|---|---|---|
| 21 | 단독 집도 | +3 | forward_gate | 7 | 없음 (부재) | R1 최초 단독 집도 문서 기록 |
| 22 | 30,000건의 손 | +3 | quiet_dominance | 7 | 없음 (술기) | 수술 성공 데이터 3장 일치 |
| 23 | 심사위 | −2 | institutional_siege | 9 | 강태준 | FS-07 payoff, 유예 |
| 24 | 집도 제한 | −1 | strategic_retreat | 7 | 유예 결정 (구조) | defeat block, 5토큰 분리 |
| 25 | 응급 | +0.5 | on_the_cut | 10 | 유예+시간 | 응급 집도 엔트리, OR door |
| 26 | 증명 | +4 | quiet_confirmation | 4 | 사후 보고 경로 | quiet block, FS-9/11/12 payoff |
| 27 | 헤드헌팅 | +1 | cold_calculation | 4 | 외부 유혹 (최도현) | stay method 잠금 |
| 28 | 학회 증례 | +2 | external_visibility | 5 | 학회 심사위 관행 | 이상훈 원거리 인식 |
| 29 | 특수 수술 추천 | +2 | asset_compounding | 4 | 이식팀 자격 관행 | 정소연 계산 수용 |
| 30 | R2 | +1.5 | institutional_rebalance | 6 | 강태준 평가서 + 병원장 (첫 인지) | ARC-03 exit, FS-02 reverse |

- Total authority delta (21→30): **+14**
- Net curve: 상승(21-22) → 후퇴(23-24) → 전환(25) → 완전 회수(26) → 정착(27-30)
- Max tension: Block 25 (10) — OR door. Min tension: Block 26/27/29 (4) — quiet phase.
- Defeat block: Block 24 (Phase0 지정). Quiet block: Block 26 (Phase0 지정). 두 지정 모두 준수.
- Beat type 중복 0 (10개 전부 다름)
- Opponent 중복 0 (강태준은 Block 23/30 두 번 등장하되 공격 각도 상이: 23 절차 공세 → 30 평가서 기재)

## 3. 6-Axis Check (harness §1.1C)

### Axis 1 — 주인공 우위와 간판 맛

- Block 22 단독 집도 성공 (수술 시간 2:18, 출혈 <150 mL, 합병증 0) / Block 25-26 응급 집도 성공 / Block 27 volume 수치 거절 / Block 28 학회 원고 1저자 / Block 30 평가서 역이용 — 전부 "차트가 먼저 맞는 R1"이라는 간판을 권한 토큰 회수로 이어감.
- 서동혁 발화량 통제: 직접 대사 최소 (Block 22 "첫 단독 집도 맞습니다", Block 27 volume 거절 한 줄 등). 능력 장광설 금지 규칙 준수.
- 간판 피로: 1회 단독 집도(21-22) → 응급(25-26) → 학회(28) → 특수 수술(29) → R2(30). 같은 "수술 성공 → 회수" 패턴이 2회(단독/응급) 반복되나, 각각의 context가 다르고 receipt 형태도 다름 (OR board 기재 vs 응급 보고 시스템 로그). 피로감 경계선이지만 미발생.

**PASS**

### Axis 2 — 성취 직후 보상/인정 리듬

- 모든 성취 블록에 same-block 또는 인접 블록 receipt 존재:
  - Block 21 성취 → Block 22 수술 성공 데이터 확정
  - Block 22 성공 → 서류 3장 일치(same block)
  - Block 25 응급 엔트리 → Block 26 사후 보고 경로 확정
  - Block 27 거절 → same-block stay 잠금
  - Block 28 학회 원고 → same-block R1 1저자 확정
  - Block 29 리스트 등재 → same-block 4축 근거 문서 영구 보관
  - Block 30 R2 진급 → same-block 3축 reward (R2 + 지도 실적 이탈 확정 + 병원장 인지)
- Block 23 후퇴 → Block 24 권한 토큰 분리 유지(defeat 흡수) → Block 25-26 반격 예약. work_guard "반격 예약 없는 손해 금지" 준수.
- Block 24가 defeat block이지만 even there same-block receipt(5토큰 문서 고정)를 지급해 "손해=빈손 후퇴" 패턴 회피.

**PASS**

### Axis 3 — 권한/장악 축 실제 성장

- ARC-02 말 권한 체인: 직보선 / 배정권 / 발표권 / M&M 기재 / 사전 설계권 / 협진 호출권
- ARC-03 말 권한 체인: 위 6개 + 1회 단독 집도 기록(21-22) + 응급 집도 실사례 + 제도적 근거 문서 6종(25-26) + stay method 잠금(27) + 학회 증례 1저자(28) + 특수 수술 리스트 등재(29) + R2 직급 + 강태준 지도 실적 이탈 제도 확정 + 병원장 라인 인지 진입
- 신규 추가 축 = 8개 (1회 단독 집도, 응급 실사례, 6종 문서, stay 잠금, 학회 1저자, 특수 수술 리스트, 지도 실적 이탈, 병원장 인지)
- 단독 집도권 자체는 "잠정 유예" 상태 유지 (공식 철회 아님). 이것은 후퇴가 아니라 승부 회피로 고정.
- 실질 장악 vs 서열: 서열 R1→R2 (한 칸), 실질 권한 축 8칸 확장. work_guard `custom_rules: 서열은 그대로인데 실질적 결정권이 뒤집히는 구조` 준수.

**PASS**

### Axis 4 — Opponent / Method / Deal_type / Stakes 반복 누적

- Opponent 축 10블록 분포: 없음(21,22) / 강태준(23,30) / 구조(24) / 유예+시간(25) / 경로(26) / 외부 유혹(27) / 학회 관행(28) / 이식팀 관행(29) / 강태준+병원장(30). **강태준은 23과 30에서 공격 각도가 다름** (23: 수련교육위 소위 절차 공세 / 30: 지도교수 평가서 기재 + 유예 승부 회피).
- Method 축 10블록: 문서화, 술기, 적중 데이터 방어, 분리 유지, 6종 사전 문서, 사후 보고 경로, volume 수치 거절, 관행 반박 원고, 4축 근거 문서, 평가서 역이용. **전부 다름**.
- Stakes 축: 동일 스테이크(문서 vs 감정 보상)가 반복되지만 실제 대결 대상이 매 블록 다름. 패턴 피로 없음.
- Deal_type 축 (work-local 권한 토큰 종류): 집도 기록 / 수술 데이터 / 유예 / 분리된 5토큰 / 응급 문서 / 사후 보고 경로 / stay 잠금 / 학회 등재 / 특수 수술 리스트 / R2+지도 실적 이탈. **전부 다름**.

**PASS**

### Axis 5 — Continuity & 열린 복선

- 블록 간 `authority_before` → 직전 블록 `authority_after` 의미 체인: 10블록 전부 이어짐. 미세 문자열 접미 차이(Block 20→21의 `(이 호 종결)` 드롭)는 batch audit I-04에서 이미 지적, 의미 동치.
- 열린 복선 → 다음 10블록(31-40 = ARC-04) 연결 상태:
  - **FS-02** 강태준 부교수 딜레마: Block 30 reverse_turn → Phase0 Block 40 payoff (자연 연결)
  - **FS-03-seed** 병원장 라인: Block 30 distant_seed → Phase0 Block 37 직접 개입 (자연 연결)
  - **FS-07** 단독 집도 유예: Block 30 post_payoff_suspension (장기 동결) → ARC-04 전반에 배경 변수
  - **FS-08** 김수현 협진 (Block 20 seed): ARC-04 간이식 라인으로 발전 예정 → Block 31-32 연결
  - **FS-10** 정식 심사 시한 (Block 23 seed): 장기 동결, ARC-04 어디에서도 강제 출현 아님
  - **FS-13** 이상훈 원거리 인식 (Block 28 seed): Phase0 Block 42 첫 대면 = ARC-05 영역, ARC-04에는 출현 안 함, 대기 상태
  - **FS-14** 정소연 관찰 조건부 3rd 보조 (Block 29 seed): Phase0 Block 31 첫 간이식 진입 조건 (**직접 연결**)
  - **FS-15** 강태준 평가서 → 본인 승진 근거 약화 (Block 30 seed): Phase0 Block 33-34 payoff (**직접 연결**)
  - **FS-04** 경험의 한계 (Phase0 seed_block 27): Phase0 정의상 Block 27 seed지만 실제 Block 27 헤드헌팅 본문에서 경험 한계 주제는 언급되지 않음. **주의 요함 (§5 issue로 분리)**
- 완결된 복선: FS-07 payoff(23), FS-09 full_payoff(26), FS-11 full_payoff(26), FS-12 branch_resolution(26). 전부 ARC-03 안에서 회수.
- 새로 심은 복선 수: 7개 (FS-09, 10, 11, 12, 13, 14, 15) + 원거리 seed 1개 (FS-03-seed). 밀도 높지만 중복 없음.

**PASS (1 issue flagged: FS-04 seed 누락)**

### Axis 6 — 다음 10블록 확장축 / 위험축 (ARC-04)

ARC-04 Phase0 정보 (재확인):
- title: 교수의 정치학
- block_range: 31-40
- capital_target: 펠로우 조기 추천 + 수술 교육 위원회 참여 + 교수 연구팀 독립 접근권
- front_sectors: 간이식 / 병원 내 교수 인사
- main_opponents: 강태준 (인사 정치) + 병원장 라인
- new_npcs: 나경태 (병원장) / 정소연 (이미 29에 선등장)
- emotion_curve: 간이식 참여 → 교수 인사 정치 직면 → 강태준 인사 공작 → 수술 실적 반격 → 펠로우 조기 추천 + 교육위 참여
- quiet_blocks: [36]
- defeat_blocks: [34, 35]

확장축:
1. 간이식이라는 새 술기 축 본격 가동 (Block 31 진입, FS-14 activation 조건부 3rd 보조 → 실질 참여 확대)
2. 교수 인사 정치 축 (Block 33-34 인사 공작, FS-15 payoff)
3. 연구/논문 축 (Block 35 연구실 봉쇄 → Block 36 독립 데이터로 우회)
4. 병원장 라인 첫 직접 대결 (Block 37, FS-03 direct entry, 윤지영은 Block 30 원거리 seed에서 이어짐)
5. 교육위 참여라는 제도 축 확장 (Block 39)
6. 강태준 관계 전환 (Block 40 FS-02 full payoff — 적대에서 불편한 공존)

위험축:
- **R1**: 간이식 3rd 보조 관찰 조건이 실질 참여로 확대되는 설득력. Phase0 slot 31은 "공식 참여" 수준이라 Block 29 `관찰 조건부 3rd 보조`에서 한 칸 더 나아가야 함. 진입 명분을 Block 31에서 명시할 것.
- **R2**: Block 33-34 defeat block 2연속은 ARC-04 최저점. ARC-03에서 Block 23-24 2연속 defeat를 Block 25-26 반격으로 흡수한 구조가 있었으므로, ARC-04에서도 Block 35-36의 대응이 Block 33-34 defeat를 흡수하는지 Phase0 설계대로 작동하는지 주의.
- **R3**: 병원장 라인 첫 직접 개입(Block 37)의 캐릭터 프레임. work_guard `role_fit_constraints: 병원장 단순악 금지` 엄수 필요. 나경태는 "병원 운영과 자기 재임 기간의 리스크 관리 차원의 은폐"가 합리적 동기로 허용됨 — ARC-04 Block 37은 아직 은폐 사건 이전이므로 "병원 홍보 가치 계산 + 이용 시도"가 주된 각도.
- **R4**: 정소연이 Block 29에서 "계산 기반 수용"(감화 아님)으로 세팅되었으므로 ARC-04 간이식 라인에서 정소연의 전환이 감화로 미끄러지지 않도록 주의. work_guard `role_fit_constraints: 조력자 감화 금지`.
- **R5**: 강태준이 Block 30에서 "승부 회피 + 평가서 기재"로 이미 한 번 물러섰으므로, ARC-04에서 강태준의 인사 공작(33-34)이 "여전히 합리적 자기 자리 방어"로 유지되어야 함. 단순 악당 미끄러짐 방지.
- **R6**: ARC-04 규모 과시 경계선. work_guard `custom_rules: Arc 3 이전까지 규모 확대 금지` — ARC-04는 Arc 4이므로 규모 확대가 허용 영역에 진입하지만, 여전히 "세계 최초 / 교과서 등재 / 글로벌 뉴스"는 금지. 병원 내부 + 국내 학회 수준으로 한정.
- **R7**: FS-04 "경험의 한계" seed 누락이 ARC-04에서 추가로 심어지지 않으면 Phase0 Block 65 full payoff까지 앵커가 부족.

**PASS, 7개 위험축 식별**

## 4. Additional Checks (work_guard / Phase0 정합)

### 4.1 work_guard forbidden_flattenings (전수 재확인, Block 21-30)

- 무보상 희생 미담 펌프: 0건 ✓
- 감동 의사물 (돈 없는 환자/과로 미담): 0건 ✓
- 환자 구조 자체 첫 승리: 0건 ✓ (Block 26 응급 성공의 receipt는 제도 문서 경로이지 환자 생명 감동이 아님)
- 의료 윤리 딜레마: 0건 ✓
- 규모 과시 (세계 최초/교과서/글로벌): 0건 ✓
- 적대자 멍청한 악당: 0건 ✓
- 능력 장광설: 0건 ✓ (서동혁 최대 발화 = Block 27 volume 거절 논거 3-4줄, 이것도 수치 나열)
- 반격 예약 없는 손해: 0건 ✓ (Block 23-24 defeat가 Block 25-26 반격으로 흡수)
- 보상이 생존/칭찬/감사 수준: 0건 ✓
- 위기 때 빈손/무대응: 0건 ✓

### 4.2 Phase0 ARC-03 exit_function 4축 달성

- R2 진급 ✓ (Block 30)
- 특수 수술 추천 ✓ (Block 29)
- 학회 증례 보고 ✓ (Block 28)
- stay method 유혹 테스트 통과 ✓ (Block 27)

### 4.3 Phase0 NPC 정합성

- 강태준: Phase0 정의 turning points [4, 12, 17, **23**, 34, 40, 68]. Block 23 정확 일치. Block 30 평가서 기재는 Phase0에 없는 추가 표현이지만 Phase0 `summary: 적대 → 인사 공작 → 불편한 공존 → 퇴장 시 인정` 곡선 안쪽.
- 조영채: Phase0 정의 turning points [6, 7, 18, 38, 50]. Block 21-30에서 Block 21(권한 얹음), 24(유예 분리 방어), 25(직보선 응급 승인), 26(사후 보고 제출), 27(stay 확인), 28(학회 추천), 29(정소연 설득), 30(병원장 공문 회신) 등장 — 모두 `summary: 계산으로 움직이는 과장` 결 유지. Phase0 turning points 외 일상적 활동은 ARC-03 과장 재량 범위 내.
- 한정우: Block 21(과장 앞에서 차단), 22(2nd 위치), 24(위계 회복 안도 + 내심 균열) — Phase0 `summary: 서열 질서 수호자 → 점차 실력 인정` 결 유지.
- 박세진: Block 26에서 한 줄 등장 ("그날 밤에 너 혼자 들어갔다는 거"). Phase0 `role: 관찰자 시점 제공` 기능 정상.
- 이상훈: Block 28 원거리 첫 인식. Phase0 `first_block: 28` 지정과 **일치**. Phase0 key_turning_points는 [42 첫 대면, 48 데이터 대결, 62 최종 경쟁]이므로 Block 28 원거리 인식은 first_block 지정의 실질 발현이며 추가 앵커 적절.
- 정소연: Block 29 첫 등장. Phase0 `first_block: 32`와 **불일치** — 3블록 앞당김. 사유: Block 29 특수 수술 리스트 등재가 정소연 교수 재량 영역이므로 그녀의 첫 판단 장면이 자연스럽게 이 지점으로 이동. Phase0 key_turning_points [32 계산 전환 후 팀 요청, 38 펠로우 추천서 공동 작성]은 ARC-04 안쪽이고, Block 29의 "리스트 등재 수용"은 Block 32 "팀 요청"의 사전 단계에 해당. 불일치지만 Phase0 지정 turning point는 침범하지 않음 — **허용 범위 내 편차**.
- 윤지영: Block 30 원거리 첫 등장(비서실 공문). Phase0 `new_npcs` ARC-03에 지정되어 있고 ARC-04 first_block 명시는 없음. ARC-03 말미 원거리 seed로 등장하는 것은 Phase0 설계와 정합.
- 박정민 / 김수현 / 나경태 / 권혁수: Block 21-30 범위 밖. 정상.

### 4.4 Schema 관점 (batch audit I-02 재확인)

- 5블록(26-30) 모두 canonical `genre_ext.block_cider.*` 및 `capital_*` 미탑재. Blocks 1-25 관행 유지.
- Tier B migration debt 누적 상태 유지. 본 감리 스코프 밖 — `schema_backfill` 별도 오더 대기.
- 본 감리에서는 쓰기 금지이므로 지적만.

## 5. Issues Found

| id | severity | 내용 | 발견 시점 |
|---|---|---|---|
| **I-21-30-A** | minor | **FS-04 "경험의 한계" seed 누락**. Phase0는 `seed_block: 27`로 지정했으나 실제 Block 27 `헤드헌팅` 본문은 경험 한계 주제를 건드리지 않았음. volume 수치 거절은 경험 재현 조건을 다루지만 "경험의 한계"와는 결이 다르다. ARC-04에서 추가 앵커가 필요하며, 없으면 Phase0 Block 65 full payoff까지 seed-payoff 체인이 약해짐. | 본 10-block audit |
| **I-21-30-B** | minor | **정소연 first_block 조기 진입** (Phase0 32 → 실제 29). Phase0 turning point 32는 침범하지 않았으나 첫 등장이 3블록 앞당겨짐. ARC-04 Block 31-32 설계 시 "첫 등장이 이미 있었음"을 전제로 장면 재구성 필요. | 본 10-block audit |
| I-01 | minor | live_status doc drift (이미 `status_sync`로 해소됨 2026-04-08) | 21-25 batch audit |
| I-02 | minor | Tier B migration debt (`block_cider.*`, `capital_*` 미탑재) — 여전히 미해소, `schema_backfill` 대기 | 21-25 batch audit + 본 감리 |
| I-03 | micro | Block 25 regression_hint 해설 톤 — 수정 선택 | 21-25 batch audit |
| I-04 | micro | Block 20/21 authority_before 접미 정렬 — 수정 선택 | 21-25 batch audit |

신규 이슈: 2건 (I-21-30-A, I-21-30-B).
기존 이슈: 4건 (I-01 해소, I-02/03/04 미해소).
중대 이슈 0건.

## 6. Repair Targets

본 10-block audit 자체의 쓰기 스코프는 이 메모 파일 1개 뿐이므로 repair는 전부 **deferred**.

| id | 수정 대상 | 권장 envelope | 우선순위 | 차단 여부 |
|---|---|---|---|---|
| I-21-30-A | ARC-04 블록 본문 중 한 지점에서 FS-04 "경험의 한계" 앵커 추가 — Phase0 Block 27 seed 정의와 실제 본문을 맞추는 방법은 두 가지: (a) 후행 블록 본문에 "경험의 한계" 주제를 자연 삽입 후 FS-04 re-seed, (b) Phase0 FS-04 seed_block을 27 → 43(Block 43 "술식 개량"가 자연스러움)으로 변경. (a)는 TR 본문 수정, (b)는 Phase0 본문 수정. 어느 쪽도 본 감리 스코프 밖. | `tr_polish` (a) 또는 `phase0_patch` (b) | 보통 (Block 65 full payoff까지는 여유) | **아님** — Block 31 생산을 차단하지 않음 |
| I-21-30-B | Block 31-32 집필 시 정소연의 "첫 등장"을 이미 Block 29에서 한 사실로 전제 반영 — Phase0 slot 31 본문 설계 시 정소연이 "처음 서동혁의 이식팀 보조를 관찰"하는 장면으로 재구성 | Block 31 생산 오더 자체에서 지시 (guardrail) | 높음 (Block 31 작성 직전 필수) | **아님** — guardrail로 흡수 가능 |
| I-02 | Blocks 1-30 전체 canonical `block_cider.*` + `capital_*` 백필 | `schema_backfill` | 낮음 | 아님 |
| I-03, I-04 | micro polish | `tr_polish` (선택) | 매우 낮음 | 아님 |

## 7. 10-Block Audit Result

**PASS**

- 핵심 6축 전부 PASS
- 추가 체크(forbidden_flattenings, ARC-03 exit 4축, NPC 정합성) 전부 통과
- 발견된 이슈는 전부 minor/micro이며 Block 31 진입을 차단하지 않음
- harness §1.1C "FAIL이면 같은 10블록 구간 안에서 필요한 블록을 먼저 수리" 조항 발동 없음

## 8. Next 10 Focus (Blocks 31-40 = ARC-04 "교수의 정치학")

### 8.1 확장축 우선 순위

1. **간이식 축 본격 가동** (Block 31 진입) — 조영채 4축 근거 문서 + 정소연 관찰 조건부 3rd 보조를 실질 참여로 확대
2. **교수 인사 정치 축** (Block 33-34) — 강태준 인사 공작의 첫 정면 전개, FS-15 payoff
3. **병원장 라인 첫 직접 개입** (Block 37) — Block 30 원거리 seed에서 직접 개입으로, 윤지영·나경태 동시 등장 가능
4. **연구/논문 축** (Block 35-36) — 연구실 봉쇄 → 독립 데이터 우회
5. **교육위 참여 = 제도 축** (Block 39) — 판독 기반 사전 설계의 제도화 시작점
6. **강태준 관계 최종 전환** (Block 40) — FS-02 full payoff, 적대 → 불편한 공존

### 8.2 필수 수위 조절 (위험축 대응)

- **R1 (간이식 진입 명분)**: Block 31에서 "관찰 조건부 3rd 보조 → 공식 참여" 전환 사유를 Block 29의 4축 근거 문서에 한 항목 더 추가하는 형태로 제시 (자기 과시 아니라 조영채/정소연 공동 판단)
- **R2 (Block 33-34 defeat 흡수)**: Block 35-36의 대응이 ARC-03의 Block 25-26 응급 반격과 **같은 수위로 반격**하지 않도록 주의. ARC-04 반격은 "공식 문서 경로"가 아니라 "독립 데이터 우회"(Phase0 Block 36 quiet block)로 결이 달라야 함. 반격 패턴 반복 피로 방지.
- **R3 (나경태 프레임)**: Block 37 첫 등장은 "병원 홍보 가치 계산 + 이용 시도"로 시작, "은폐 사건"은 ARC-06 소관이므로 ARC-04에서는 **단순 악당 프레임 금지**, 합리적 병원 운영자 결 유지
- **R4 (정소연 감화 금지)**: ARC-04 정소연 전환은 "계산의 연속"이어야 하며, 감탄/감사/호의의 미끄러짐 금지. Block 32 "팀 요청"도 "자기 이식 합병증률 데이터 개선"이 주 동기
- **R5 (강태준 합리성 유지)**: Block 33-34 인사 공작 논거는 work_guard 허용 범위(경험 500건 기준 + 수련 체계 위계) 안에서. 본인 지도 실적 관리라는 합리적 자기 자리 방어 축 유지
- **R6 (규모 과시 경계)**: ARC-04는 Arc 4이지만 work_guard는 "규모 과시가 인과보다 앞서면 안 된다"를 Arc 전체에 적용. 학회 데뷔·특수 수술 참여·펠로우 추천은 허용되지만 "해외 학회 초청/국내 최초/교과서 등재"는 ARC-05 이후로 미룰 것
- **R7 (FS-04 seed 보충)**: ARC-04 어딘가에 "경험의 한계" 예고가 한 번 들어가야 Phase0 Block 65 payoff가 작동. Block 43 추천 (ARC-05 술식 개량 지점)이지만 가능하면 ARC-04 말미(Block 40)에도 미세 seed 가능

### 8.3 ARC-04 예상 tension 곡선 (권장)

ARC-03 curve: 7-7-9-7-10-4-4-5-4-6 (peaks 9/10, valleys 4)
ARC-04 권장 curve: 5-6-7-8-8-4-7-6-6-7 (peaks 8, valley 4 @Block 36 quiet)
- ARC-03의 peak 10(응급 OR)을 ARC-04가 재현하면 패턴 피로 발생. ARC-04 최고점은 8 수준으로 유지
- defeat_blocks[33,34] 2연속에서 tension 8로 이어가되 Block 35-36에서 "후퇴 흡수 + quiet 우회"로 내림
- Block 37 병원장 첫 등장은 tension 7 (새 전선의 감각)
- Block 40 FS-02 full payoff는 tension 7 (강태준 관계 최종 전환 = rebalance)

### 8.4 Next immediate action

1. **선행 권장**: `status_sync` 오더 — `docs/2026-04-08/hoegui_surgeon_live_status.md`를 Block 30 경계 + 본 감리 결과(PASS)로 동기화
2. **메인 다음 생산 오더**: `tr_continue` 1-block envelope, 대상 **Block 31 `간이식 수술장`** (Phase0 ARC-04 slot 31)
   - 필수 guardrail (본 감리에서 추가된 것):
     - **I-21-30-B 흡수**: 정소연 "첫 등장"을 Block 29 전제로 재프레이밍, Block 31은 "정소연이 직접 관찰하는 첫 이식 보조"로
     - **R1 흡수**: 관찰 조건부 3rd 보조에서 공식 참여로의 전환 사유를 과장/이식팀 공동 판단으로
     - **R4 흡수**: 정소연 감화 금지, 계산 기반 유지
     - **규모 경계**: 간이식 첫 등장을 "대학병원 정기 이식 일정" 수준으로 (초대형 캠페인 수술 금지)
   - hard stops: Block 32 금지 / BI 금지 / 파일명 변경 금지 / Blocks 1-30 재작성 금지
3. **병행 가능(선택)**: `tr_polish` / `phase0_patch` — I-21-30-A(FS-04 seed) 처리. 긴급하지 않음, Block 43 수준까지 여유.

---

_본 문서의 쓰기 스코프는 본 메모 파일 하나로 한정된다. TR 본문 · Phase0 · work_guard · live_status · harness · BI 일체 미수정._

## 9. Summary

- audit_result: **PASS**
- ready_for_block_31: **yes**
- blocking issues: **none**
- non-blocking issues: 2 new (I-21-30-A FS-04 seed 누락, I-21-30-B 정소연 조기 등장) + 3 carry-over (I-02, I-03, I-04)
- next immediate action: `status_sync` (권장) → `tr_continue` 1-block envelope Block 31
- 10-block self-audit trigger: 다음은 Block 40 완료 시점 (Blocks 31-40 self-audit)
