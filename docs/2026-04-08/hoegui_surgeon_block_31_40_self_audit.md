# hoegui_surgeon — Blocks 31-40 10-Block Self-Audit

Date: 2026-04-08
Scope: harness v2 §1.1C 10-block self-audit (Block 40 완료 boundary)
Work ID: `hoegui_surgeon`
Audit class: mandatory pre-next-batch audit (Block 41 생산 금지 해제 조건)
Basis:
- `treatments/hoegui_surgeon_tr_block_020_draft.json` (Blocks 31-40, current)
- `treatments/phase0/hoegui_surgeon_phase0_design.json` (ARC-04 완료 + ARC-05 41-50 예정)
- `work_guards/12_hoegui_surgeon.yaml`
- `docs/2026-04-08/hoegui_surgeon_live_status.md`
- `docs/2026-04-08/hoegui_surgeon_block_21_30_self_audit.md` (상위 연속 audit, 권장 사항 검증 대상)
- `docs/blockguide/treatment-production-harness-v2.md` §1.1C

## 1. Audit Scope

- primary: Block 31-40 (ARC-04 전체 10블록)
- backward anchor: Block 30 말미 (ARC-03 exit 상태)
- forward anchor: Phase0 ARC-05 slot 41-50 (Block 41 진입 조건)
- out-of-scope: Blocks 1-30, Block 41+ 생산, Phase0/work_guard/harness 본문, BI, live_status 갱신

## 2. Block-by-Block Summary Table

| Block | Title | auth Δ | beat | tension | opponent | 기능 |
|---|---|---|---|---|---|---|
| 31 | 간이식 수술장 | +2 | constrained_entry | 5 | 이식팀 학습 사다리 관행 | FS-14 activation, 첫 이식 3rd |
| 32 | 정소연의 계산 | +3 | calculated_formalization | 6 | 박기태 (이식팀 전임의) | FS-14/16 full_payoff, 공식 지정 |
| 33 | 교수 인사 | +0.5 | structural_irony | 7 | 강태준 (승진 심사 구조) | FS-15 payoff, FS-02 partial |
| 34 | 인사 공작 | −2 | institutional_hold | 8 | 강태준 | defeat, 펠로우 저지 |
| 35 | 연구실 봉쇄 | −1.5 | contained_siege | 8 | 강태준 (연구실) | defeat, 연구 축 봉쇄 |
| 36 | 독립 데이터 | +1 | quiet_reconstruction | 4 | 없음 (quiet) | FS-18/19 결합, FS-04 seed |
| 37 | 병원장의 눈 | +1 | frame_control | 7 | 나경태 (홍보 이용 시도) | FS-03 direct_entry |
| 38 | 펠로우 추천 | +3 | counter_resolution | 6 | 강태준 | FS-17/18 full_payoff, 34-35 반격 완결 |
| 39 | 교육위 참여 | +2 | institutional_seat | 6 | 위원회 관행 | FS-20 seed (Block 60 교육 재편) |
| 40 | 강태준의 인정 | +2 | structural_coexistence | 7 | 강태준 (재심 구조) | **FS-02 full_payoff**, ARC-04 exit |

- Total ARC-04 authority delta: **+11**
- Tension curve: **5-6-7-8-8-4-7-6-6-7** — prior audit §8.3 권장 곡선과 **정확 일치**
- Max tension: Block 34/35 (8) defeat 2연속. Min tension: Block 36 (4) quiet.
- Defeat blocks: Block 34, 35 (Phase0 `defeat_blocks:[34,35]` 준수)
- Quiet blocks: Block 36 (Phase0 `quiet_blocks:[36]` 준수)
- Beat type 중복 0 (10개 전부 다름)
- Opponent 축: 강태준(33/34/35/38/40) 5회 등장이지만 공격/대응 각도 전부 상이 — 승진 서류(33) → 연차 기준(34) → 연구실 재량(35) → 연차 재반박(38) → 재심 역설(40). 반복 아니라 점증하는 구조 분해.

## 3. 6-Axis Check (harness §1.1C)

### Axis 1 — 주인공 우위와 간판 맛

- "차트가 맞는 R1"이 "차트가 맞는 R2 (특별 카테고리 펠로우)"로 자연 승격. 간판 코어 유지.
- 서동혁 직접 발화량: Block 31 0회 + Block 32 0회 + Block 33 0회 + Block 34 0회 + Block 35 0회 + Block 36 0회(내부 기록만) + Block 37 3-4문장 (면담) + Block 38 0회 + Block 39 1문단 (교육위 제안) + Block 40 "네" 2회. **10블록 총 발화 = 면담 3문장 + 교육위 제안 1문단 + "네" 2회**. 능력 장광설 금지 완벽 준수.
- 간판 피로: ARC-03의 "수술 성공 + 문서 회수" 패턴에서 ARC-04는 "제도 구조 역이용 + 우회 재구성"으로 패턴 축 전환. 같은 성공 반복이 아님.

**PASS**

### Axis 2 — 성취 직후 보상/인정 리듬

- 성취 블록 전부 same-block 또는 연속 블록 receipt:
  - 31(이식 참여) → 32(공식 지정) 연속
  - 32(공식 지정) → same-block 회의록 기재
  - 33(딜레마 노출) → same-block 차트 노트 구조 기록
  - 36(독립 논문) → same-block 발표 일정 + FS-04 기재
  - 37(면담) → same-block 프레임 제어
  - 38(펠로우 승인) → same-block 특별 카테고리 확정
  - 39(교육위) → same-block 제안 접수
  - 40(FS-02 payoff) → same-block 공존 대화
- Defeat 블록 34, 35도 receipt 있음:
  - 34: 반격 seed + 다음 달 발표 일정 예약 (즉각 반격)
  - 35: 재구성 방향 seed + Block 36 이월 예약 (지연 반격)
- work_guard "반격 예약 없는 손해 금지" 준수 ✓

**PASS**

### Axis 3 — 권한/장악 축 실제 성장

- ARC-03 말 권한 체인: 8축 (직보선/배정권/발표권/M&M/사전 설계/협진/집도 기록/응급 실사례/6종 문서/stay/학회 1저자/특수 수술 리스트/R2/지도 실적 이탈/병원장 인지)
- ARC-04 말 권한 체인 신규 추가: 이식팀 공식 사전 판독 보조(32) + 독립 케이스 시리즈 논문(36) + 병원장 면담 프레임 제어(37) + **특별 카테고리 펠로우 자격**(38) + **수술 교육 위원회 레지던트 대표**(39) + **강태준 불편한 공존**(40)
- 신규 축 6개 추가. R2 직급 유지 상태에서 펠로우 자격 별도 트랙 확보는 서열/실질 분리의 ARC-03 대비 한 단계 심화.
- work_guard `custom_rules: 서열은 그대로인데 실질적 결정권이 뒤집히는 구조` — ARC-04에서는 "서열은 R2인데 펠로우 자격이 붙었고 교육 위원회 의석까지 있는 R2"로 분리가 극단화.

**PASS**

### Axis 4 — Opponent / Method / Stakes 반복 누적

- **강태준 5회 등장 분해** (가장 주의할 반복 지점):
  - Block 33: 본인 심사 서류 작성 시 딜레마 직면 (내부 갈등, 서동혁 부재)
  - Block 34: 수련교육위 연차 기준 공세 (정면 공격)
  - Block 35: 연구실 재량 봉쇄 (간접 공격)
  - Block 38: 2차 연차 기준 재반박 (재공격 실패)
  - Block 40: 재심에서 자기모순 감수 후 포함 (역설 수용)
  - 다섯 번 모두 **공격 각도, 대응 결과, 내부 동기가 상이**. 강태준이 계속 등장하지만 같은 장면의 반복이 아니라 점증하는 구조 분해.
- Method 축 10블록 전부 다름: 일정 공백 프레이밍(31), 법적 분리 구조(32), 딜레마 직면(33), 4축 문서 제출(34), 봉쇄 수용 + 재구성 검토(35), 케이스 시리즈 재구성(36), 조건 제한 면담(37), 5축 재제출(38), 시범 운용 단서(39), 자기모순 수용(40)
- Stakes 축: 제도적 귀속 + 승부 지연 + 역프레임 회피의 반복이지만, 각 블록 스테이크 대상이 다름. 반복 피로 경계선이지만 미발생.
- Beat type 10개 전부 다름.

**PASS**

### Axis 5 — Continuity & 열린 복선

- 블록 간 `authority_before` → 직전 블록 `authority_after` 의미 체인: 10블록 전부 이어짐.
- **FS 완결 상태:**
  - FS-14 full_payoff (32) ✓
  - FS-15 payoff (33) ✓
  - FS-16 full_payoff (32) ✓
  - FS-17 payoff (38) ✓
  - FS-18 payoff (38) ✓
  - **FS-02 full_payoff (40)** ✓ — 6블록 체인(21 esc → 23 counter → 30 reverse → 33 partial → 40 full) 완결
  - FS-19 full_activation (36) ✓
  - **FS-04 seed 자연 삽입 (36)** ✓ — 이전 audit I-21-30-A 해소
  - FS-03 direct_entry (37) ✓
  - **I-21-30-B** (정소연 조기 등장) 흡수: Block 31에서 "Block 29 합의 조건 실질 작동"으로 재프레이밍 ✓
- **신규 seed (다음 10블록 연결):**
  - FS-20: 판독 기반 사전 설계 교육 커리큘럼화 제안 (Block 39 seed → Phase0 Block 60 "교육 재편" 원거리)
  - FS-21: 강태준 "초기 지도 방향 설정" 자기 보호 첨언 (Block 40 seed → Phase0 Block 68 퇴장의 사전 해체 지점)
- **장기 동결 / 대기 상태:**
  - FS-07 (단독 집도 유예): 정식 심사 미개최, 사실상 장기 동결. ARC-05-06 중 어디서 해제 여부 재검토 필요.
  - FS-08 (김수현 협진 관계): ARC-04에서 가동 안 됨. Phase0 ARC-04 간이식 맥락에서 가동 기대했으나 실제로는 정소연 라인이 주축이 되어 김수현 라인 비활성. ARC-05 이후 재활성 여지 있음.
  - FS-13 (이상훈 원거리 인식, Block 28 seed): Phase0 Block 42 첫 대면 = ARC-05 Block 42. **직접 연결**.
- Orphaned seed 없음.

**PASS**

### Axis 6 — 다음 10블록 (ARC-05 41-50) 확장축 / 위험축

**Phase0 ARC-05 정보:**
- title: 메스 하나로 올라간다
- time_window: 2027년 10월 ~ 2028년 6월
- capital_target: 펠로우 → 조교수 후보 + 독립 수술팀 + 국내 학회 주목
- front_sectors: 간담도·췌장 고난도 수술 / 수술 술식 개량
- main_opponents: 이상훈 (타 대학 라이벌) / 병원장 라인 (정치적 이용 시도)
- new_npcs: 권혁수 (외과학회 중진)
- emotion_curve: 펠로우 시작 → 이상훈 첫 대면 → 술식 개량 → 병원장 이용 시도 → 독립팀 구축 → 학회 주목
- quiet_blocks: [46]
- defeat_blocks: [44]
- slots: 41 펠로우 첫날 / 42 이상훈 / 43 술식 개량 / 44 병원장의 제안 / 45 후원 없는 길 / 46 팀 빌딩 / 47 이상훈의 도전 / 48 데이터 대결 / 49 학회 주목 / 50 조교수 후보

**확장축:**
1. **펠로우 술기 독립** (Block 41-43) — 특별 카테고리 펠로우의 실질 가동. 자기 외래 + 수술 스케줄 + 술식 개량
2. **이상훈 라이벌 축** (Block 42, 47, 48) — Block 28 원거리 인식에서 직접 대면으로. 데이터 검증 → 정면 대결 → 양립의 구조
3. **병원장 라인 2차 대면** (Block 44-45) — Block 37 1차 면담의 연장. Phase0 slot 44는 defeat block, 후원 제안 거절 + 불이익 흡수
4. **독립 수술팀 빌딩** (Block 46 quiet) — 비공식 독립팀 구성
5. **학회 주목 축** (Block 49) — 권혁수 외과학회 중진의 첫 등장, 학회 중진 라인
6. **조교수 후보 추천** (Block 50) — ARC-05 exit, 조영채의 공식 추천

**위험축 (ARC-05 생산 시 필수 고려):**
- **R1'** (이상훈 캐리커처 방지): Block 42 첫 대면에서 이상훈은 "서동혁의 적중률을 데이터로 파고들려 하는 동세대 최고 외과의". work_guard `role_fit_constraints` 기준이 이상훈에게 별도 항목이 없으나 강태준/조영채/나경태에 준하는 "캐리커처 금지 + 합리적 동기" 선 적용 필요. 이상훈의 동기 = "동세대 최고 외과의 타이틀 유지 + 서동혁 적중률의 비밀 규명".
- **R2'** (병원장 제안 거절 패턴 반복 방지): Block 27 헤드헌팅 거절(수치 기반)과 Block 44 병원장 제안 거절이 **같은 각도면 패턴 피로**. Block 27은 외부 스카웃 수치 거절, Block 44는 내부 후원 조건 거절이어야 결이 달라짐. 후원 제안의 조건이 무엇인지(예: 병원장 라인 지시 따를 것)가 거절 근거가 되어야 하며, Block 37 "제도 경로만 수용" 프레임의 연장선.
- **R3'** (독립팀 빌딩이 조직 이탈로 프레임되지 않도록): Block 46 팀 빌딩은 비공식 구성. 공식 독립이 아니라 "내 수술에 맞는 보조 인력 점진 확보"의 결.
- **R4'** (규모 확대 경계): work_guard `custom_rules: Arc 3 이전까지 규모 확대 금지`는 ARC-05부터 해제되지만, **여전히 "세계 최초/교과서 등재/글로벌 뉴스"는 금지**. 국내 외과학회 수준에서 "중진 주목"과 "국내 학회 발표" 수준으로 한정. 권혁수도 "외과학회 중진"으로 한정되지 "세계 최고 권위자"가 아님.
- **R5'** (FS-04 경험의 한계 보강): Block 36 논문 한계 섹션에 자연 삽입된 seed가 Phase0 Block 65 full payoff까지의 거리가 25블록. 중간 보강 앵커 1-2개 필요. Block 43 "술식 개량"이 자연스러운 보강 지점 — 술식 개량을 시도하다가 "3만 건 경험에도 없는 패턴"과 처음 접촉하는 장면으로. 감리 권장.
- **R6'** (이상훈 데이터 검증 간격 관리): Block 42 첫 대면 → Block 47 도전 → Block 48 데이터 대결 → Block 62 최종 경쟁(ARC-07). 이상훈의 Phase0 key_turning_points [42, 48, 62]를 감안하면 ARC-05 안에서 47-48로 빠르게 올라가는 구조. 관계 발전의 템포가 빠르므로 42-47 사이 5블록 간격에서 "원거리 데이터 감시" 유지 필요.
- **R7'** (Block 44 defeat 흡수 단일 블록): ARC-03 Block 23-24, ARC-04 Block 34-35의 defeat 2연속 패턴과 달리 Phase0 ARC-05 `defeat_blocks:[44]`는 **단일 defeat**. 흡수 블록은 Block 45 "후원 없는 길". 단일 defeat + 단일 흡수 구조가 앞선 두 ARC와 다른 리듬을 만든다. 감리 시 이 리듬 차이를 의도적으로 유지.

**ARC-05 권장 tension 곡선:** 5-6-7-7-6-4-7-8-7-7
- 앞선 ARC 대비 peak 조정: ARC-03 peak 10(Block 25), ARC-04 peak 8(Block 34-35). ARC-05는 peak 8 (Block 48 데이터 대결)로 유지해 피로 방지. 최종 Block 50은 7 (조교수 후보 추천의 structural moment).

**PASS, 7개 위험축 식별**

## 4. Additional Checks

### 4.1 work_guard forbidden_flattenings 10블록 전수 재확인

- 무보상 희생 미담 펌프: 0건 ✓
- 감동 의사물: 0건 ✓ (Block 31 이식 케이스는 환자 사연 0, 기증자 감동 0, 전부 수술 기록과 판독 노트 중심)
- 환자 구조 자체 첫 승리: 0건 ✓
- 의료 윤리 딜레마: 0건 ✓
- 규모 과시: 0건 ✓ (학회 1저자·특별 카테고리 펠로우·교육위 진입 전부 "대학병원 내부 + 국내 수련 체계" 수준)
- 적대자 멍청한 악당: 0건 ✓ (강태준 5회 등장 전부 합리적 논거, 나경태 Block 37 합리적 병원 운영자)
- 능력 장광설: 0건 ✓ (서동혁 발화 극소)
- 반격 예약 없는 손해: 0건 ✓ (34 → 같은 블록 예약, 35 → Block 36 이월 예약)
- 보상이 생존/칭찬/감사 수준: 0건 ✓
- 위기 때 빈손/무대응: 0건 ✓ (34/35 defeat도 반격 seed 기록)

### 4.2 Phase0 ARC-04 exit_function 3축 달성

Phase0 정의: "펠로우 조기 추천 + 교육위 참여. 강태준과의 관계가 적대에서 불편한 공존으로 전환."
- 펠로우 조기 추천 ✓ (Block 38)
- 교육위 참여 ✓ (Block 39)
- 강태준 불편한 공존 ✓ (Block 40)

### 4.3 Phase0 NPC 정합성 확인

- **강태준**: Phase0 turning points [4, 12, 17, 23, **34**, **40**, 68]. Block 34, 40 정확 일치. Block 33(내부 딜레마)과 Block 35(연구실 봉쇄), Block 38(2차 반대)은 Phase0 정의 외 등장이지만 `summary: 적대 → 인사 공작 → 불편한 공존 → 퇴장 시 인정` 곡선의 자연 확장. 허용.
- **조영채**: Phase0 turning points [6, 7, 18, **38**, 50]. Block 38 정확 일치. 그 외 빈번한 등장은 조력자 라인 일상.
- **정소연**: Phase0 turning points [**32**, **38**]. Block 32 팀 요청 정확 일치, Block 38 공동 명의 정확 일치. I-21-30-B(first_block 조기 등장) 흡수 확인.
- **나경태**: Phase0 `first_block: 37` 정확 일치. Phase0 turning points [**44**, 54, 58]은 ARC-05-06 소관.
- **윤지영**: Phase0 new_npcs ARC-04 지정, first_block 미명시. Block 30 원거리 → Block 37 실무 창구 정착. 정상.
- **김재원**: work-local 인물 (Phase0 미등재). Block 31 첫 등장(반대 관찰) → Block 38 공식 지지자 전환. 역할 성장 일관.
- **박기태**: work-local 단발 (Block 32). 정상.

### 4.4 Schema debt (I-02) 상태

- Blocks 31-40 전부 canonical `block_cider.*` 및 `capital_*` 미탑재. Blocks 1-30 관행 유지.
- Tier B migration debt 누적 유지. 본 감리 스코프 밖.

## 5. Issues Found

| id | severity | 내용 | 비고 |
|---|---|---|---|
| **I-31-40-A** | minor | **Block 33에서 5월 심사 결과 미기재 → Block 40에서 "보류 + 재심 권고"였음이 사후 드러남**. 엄밀히는 retcon은 아니지만(Block 33 시점 아직 결과 없음), 독자 입장에서 Block 33-34-35 구간에서 "5월 심사 보류"가 암묵 전제였는지 Block 40에서야 드러나는지 명확도가 낮다. Block 40에서 정렬되므로 본문 모순은 없으나, Block 33 후반에 "심사 결과 보류 통보가 5월 말 도착" 한 줄을 사후 삽입하면 체인 논리가 더 선명해짐. | 본 10-block audit |
| **I-31-40-B** | minor | **FS-08 (김수현 협진 관계) 비활성 상태 지속**. Block 20 seed에서 Phase0 ARC-04 간이식 맥락으로 발전 예정이었으나 실제 ARC-04에서는 정소연 라인이 주축이 되며 김수현 라인이 가동되지 않음. ARC-05 이후 재활성 경로를 열어 둘지, Phase0 정의를 '비활성 seed'로 재분류할지 판단 필요. | 본 10-block audit |
| **I-31-40-C** | micro | **Block 40 "초기 지도 방향 설정" 자기 보호 첨언 (FS-21 seed)**이 Phase0 Block 68 payoff까지 거리가 28블록. 장기 seed이므로 중간 리마인드 앵커(1회)가 ARC-05 또는 ARC-06 어딘가에 필요. 보강 누락 시 Block 68 "네 방식이 맞았다" 한 줄의 사전 해체가 약해짐. | 본 10-block audit |
| I-21-30-A | **closed** | FS-04 경험의 한계 seed 누락 — Block 36 자연 삽입으로 해소 ✓ | 이전 audit에서 식별 |
| I-21-30-B | **closed** | 정소연 first_block 조기 등장 — Block 31에서 "Block 29 조건 실질 작동" 재프레이밍으로 흡수 ✓ | 이전 audit에서 식별 |
| I-02 | minor | Tier B migration debt (`block_cider.*`, `capital_*`) — 여전히 미해소, `schema_backfill` 대기 | carry-over |
| I-03, I-04 | micro | 이전 audit 선택 polish — 미해소 상태, 차단 아님 | carry-over |

신규 이슈: 3건 (I-31-40-A/B/C, 전부 minor/micro)
해소된 이슈: 2건 (I-21-30-A, I-21-30-B)
차단 이슈: 0건

## 6. Repair Targets

| id | 수정 대상 | 권장 envelope | 우선순위 | 차단 여부 |
|---|---|---|---|---|
| I-31-40-A | Block 33 후반에 "5월 심사 결과 보류 통보" 한 줄 삽입 | `tr_polish` (TR 단일 블록 micro patch) | 매우 낮음 (Block 40에서 정렬됨) | 아님 |
| I-31-40-B | FS-08 재활성 여부 판단 — ARC-05 슬롯 중 한 군데(예: Block 43 술식 개량 또는 Block 46 팀 빌딩)에 김수현 협진 한 줄 재출현, 또는 Phase0 handoff doc에 '비활성 seed'로 재분류 | Block 41+ 생산 guardrail 또는 `phase0_patch` 선택 | 낮음 | 아님 |
| I-31-40-C | ARC-05/ARC-06 어딘가에 강태준 "초기 지도 방향 설정" 첨언 리마인드 앵커 1회 | Block 51-67 생산 guardrail | 낮음 | 아님 |
| I-02 | Blocks 1-40 전체 canonical `block_cider.*` + `capital_*` 백필 | `schema_backfill` | 낮음 | 아님 |
| I-03, I-04 | micro polish | `tr_polish` 선택 | 매우 낮음 | 아님 |

본 10-block audit 쓰기 스코프는 본 메모 파일 1개로 한정. 모든 수정 deferred.

## 7. 10-Block Audit Result

**PASS**

- 핵심 6축 전부 PASS
- ARC-04 exit_function 3축 달성
- work_guard forbidden_flattenings 10항목 0건
- Phase0 NPC turning points 정합
- 이전 audit 지적 I-21-30-A, I-21-30-B **전부 해소**
- 신규 이슈 3건 전부 minor/micro, Block 41 진입 차단 없음
- harness §1.1C "FAIL이면 같은 10블록 구간 안에서 필요한 블록을 먼저 수리" 조항 발동 없음

## 8. Next 10 Focus (Blocks 41-50 = ARC-05 "메스 하나로 올라간다")

### 8.1 확장축 우선 순위

1. **펠로우 술기 독립** (Block 41-43) — 특별 카테고리 펠로우 실질 가동, 자기 외래/수술 스케줄
2. **이상훈 라이벌 축** (Block 42, 47, 48) — 원거리 인식 → 직접 대면 → 데이터 대결
3. **술식 개량 축** (Block 43) — 3만 건 경험의 현재 술식 적용, FS-04 중간 보강 가능 지점
4. **병원장 라인 2차 대면** (Block 44-45) — Block 37 1차의 연장, defeat + 흡수 단일 블록 구조
5. **독립 수술팀** (Block 46 quiet) — 비공식 팀 빌딩
6. **학회 중진 라인** (Block 49) — 권혁수 첫 등장, 학회 중진 주목
7. **조교수 후보** (Block 50) — ARC-05 exit

### 8.2 필수 수위 조절 (위험축 대응)

- **R1' (이상훈 캐리커처 방지)**: Block 42 첫 대면에서 이상훈의 동기 = "동세대 최고 외과의 타이틀 유지 + 데이터로 적중률 비밀 규명". work_guard `role_fit_constraints`에 이상훈은 없지만 강태준·나경태 캐리커처 금지와 같은 선 적용. 이상훈이 악의가 아니라 경쟁자의 계산 기반 의심으로 등장.
- **R2' (병원장 제안 거절 패턴 반복 방지)**: Block 27 수치 거절과 다른 각도 필요. Block 44의 거절 근거 = "병원장 라인 지시를 따를 것"이라는 조건 자체의 독립성 침해 → Block 37 "제도 경로만 수용" 프레임의 연장이지 수치 계산 아님. 같은 거절이지만 결이 다름.
- **R3' (독립팀 빌딩이 조직 이탈로 프레임되지 않도록)**: Block 46 quiet block. 비공식 구성, "내 수술에 맞는 보조 인력 점진 확보". 조직 이탈 금지.
- **R4' (규모 확대 경계)**: ARC-05는 work_guard 규모 금지 해제 영역이지만 **세계 최초/교과서 등재/글로벌 뉴스 여전히 금지**. 권혁수 = "외과학회 중진", Block 49 학회 주목 = 국내 외과학회 수준 한정.
- **R5' (FS-04 경험의 한계 중간 보강)**: Block 43 "술식 개량"에서 "3만 건 경험에도 없었던 현재 술식 요소" 또는 "현재 장비·약제 환경에서 과거 경험이 미세하게 어긋나는 지점"을 간접 언급. 전면 활성화 아님, 1-2줄 보강.
- **R6' (이상훈 데이터 검증 간격)**: Block 42 첫 대면 후 Block 47 도전까지 5블록 공백. 그 사이 이상훈의 "원거리 데이터 감시"를 1-2회 간접 언급 (예: 서동혁의 Block 48 학회 발표 참관 등록, 논문 초안 인용 요청 등).
- **R7' (defeat 리듬 차이 유지)**: ARC-05는 단일 defeat(44) + 단일 흡수(45). 앞선 두 ARC의 2연속 defeat와 다른 리듬. 감리 시 의도적 유지 — Block 44가 "중간 크기 후퇴"이고 Block 45가 "감정 아닌 계산으로 흡수"의 결.

### 8.3 ARC-05 권장 tension 곡선

`5-6-7-7-6-4-7-8-7-7`
- peak: Block 48 데이터 대결 (8) — ARC-03 peak 10, ARC-04 peak 8과 동일 수위. 과거 peak 재현 방지.
- valley: Block 46 팀 빌딩 (4) — quiet block.
- ARC-05 exit (Block 50 조교수 후보) tension 7 — structural moment.

### 8.4 이월 권장 guardrails (I-31-40-A/B/C 처리)

- **I-31-40-A**: Block 41+ 생산 중 자연 언급 기회가 없으면 `tr_polish` 별도 envelope로 Block 33 micro patch.
- **I-31-40-B**: Block 43 또는 Block 46에서 김수현 협진 한 줄 재출현 검토. 아니면 ARC-04 종료 시점 Phase0 handoff doc에 '비활성 seed' 재분류.
- **I-31-40-C**: Block 55-60 구간에 강태준 "초기 지도 방향 설정" 리마인드 앵커 1회 자연 삽입.

## 9. Summary

- audit_result: **PASS**
- ready_for_block_41: **yes**
- blocking issues: **none**
- new issues: 3 (I-31-40-A, B, C — 전부 minor/micro)
- resolved issues: 2 (I-21-30-A FS-04 seed 해소, I-21-30-B 정소연 first_block 흡수)
- carry-over issues: 3 (I-02, I-03, I-04 — carry-over, 차단 없음)
- next immediate action: **(선행 권장)** `status_sync` — Block 40 경계로 live_status 동기화 / **(메인)** `tr_continue` 1-block envelope Block 41 `펠로우 첫날`
- 10-block self-audit trigger: 다음은 Block 50 완료 시점 (Blocks 41-50 self-audit)

---

_본 문서의 쓰기 스코프는 본 메모 파일 하나로 한정. TR 본문 · Phase0 · work_guard · live_status · harness · BI 일체 미수정._
