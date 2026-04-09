# africa_farm_king opening handoff

Date: 2026-04-09
Work ID: `africa_farm_king`
Title: `파병지에 돌아와 농업왕이 되었다`
Purpose: `Opus-safe continuation handoff for ARC-01 opening`

## 1. Read Order

1. `docs/2026-04-09/africa_farm_king_live_status.md`
2. `material_ssot/20_pitch/canon/africa_farm_king.md`
3. `treatments/phase0/africa_farm_king_phase0_design.json`
4. `treatments/africa_farm_king_tr_block_001_draft.json`

## 2. Saved Boundary

- current saved boundary: `Block 10` (**ARC-01 complete 1-10**)
- next legal continuation: `Block 11` (ARC-02 진입, fresh operator order + phase0 ARC-02 slot 확장 필요)
- ARC-01 closed: phase0 exit_function 충족 (루곤도 채소 공급 허브 + 시청 실무자 첫 접점)
- after Block 1-10: full self-audit complete (ALL PASS)

## 3. What Is Already Fixed

- `Block 1 루곤도 복귀` (access / intensity 6)
  - receipt: 폐 NGO 시범농장 장기임차권 + dead well 인벤토리 접근권
- `Block 2 총상과 유예` (protection / intensity 8)
  - receipt: 모세 구조 -> `30일 비개입 유예` + 첫 장비 반입 안전구역
- `Block 3 죽은 우물` (visible_token / intensity 8)
  - receipt: dead well 복구 -> 첫 물 -> first working farm proof
- `Block 4 못난이 상자` (reevaluation / intensity 8)
  - receipt: 시장 바닥 정보망 + 아미나의 첫 신뢰
- `Block 5 첫 납품` (proof / intensity 9)
  - receipt: 병원·호텔·컴파운드 시험 납품 성공 + 첫 현금 회수 + lot sheet 기반 구매선 접점
- `Block 6 모종장` (next_gate_opening / intensity 7)
  - receipt: 등급별 수매표 첫 공개 + 첫 두 농가 시범 계약 (피터 루하카 외 1) + 육묘장 이백 판 + farm-direct 첫 줄
- `Block 7 창고의 밤` (defeat / intensity 9, **locked defeat block** — `has_cider: false / pain_only_exit: true`)
  - receipt: 핵심 자산 전부 보존 (현금/모판/lot sheet 마스터/태양광 컨트롤러), 미끼 본 창고만 손실, 30일 유예 자체 사수
  - structural reveal: 마칼리 본대 vs 하부 라인 분리 구조 첫 노출
  - new permanent ban: 케빈 음와치 (정보 가격으로 lot sheet 옆 영구 기록, 농장 영구 차단)
- `Block 8 수매표` (mass_defection / intensity 8)
  - receipt: 수매표 공공 게시 (마을 회관 + 중앙시장 입구 + 루곤도 병원 외래) + 갱신 영수증 두 장 + 외곽 소농 15가구 마칼리 이탈 + 작물 7종 + farm-direct 5줄 + 익명 코드 lot sheet 데이터 누적
  - structural pivot: 가격 결정권이 비공식 라인에서 공식 라인으로 첫 양적 이동, 마칼리 본대 가격 카드(비공식 수매가 인상) 무력화 → 다시 침묵
  - 아미나 변화: 시장 안 거점화 (직접 거래는 없으나 가격 무너짐 관찰자)
  - 신규 NPC: 도린 무봉가 (외곽 가구 첫 이탈자)
- `Block 9 운송 전쟁` (logistics_breakthrough / intensity 8)
  - receipt: 단일 운송 라인 → 다섯 갈래 매트릭스 (작은 트럭 2 + 오토바이 3 + 자전거 짐꾼 2) + 외곽 15가구 묶음 90% 도착 + 마칼리 하부 라인 단일 점 차단 카드 무력화
  - debt recovery: **B2 모세 30일 시계 회수** — 모세 카반다가 솔로몬 경유 첫 외부 신호 송신 ('본대 침묵은 영원하지 않다, 너희 운송 매트릭스가 본대에게도 데이터로 도착한다')
  - 본대 침묵 의미 전환: '무시하는 침묵' → '데이터 수신 침묵'
  - 신규 NPC: 솔로몬 아바예 (전직 루곤도-나이로비 미니버스 운전사 → 첫 풀타임 driver lead)
- `Block 10 건기의 왕` (institutional_pivot / intensity 9, **ARC-01 exit**)
  - receipt: 첫 건기 시즌 흑자 + 시청 실무자 첫 접점 + 그레이스 lot sheet 건기 안정 공급선 표시 + 루곤도 채소 공급 허브 첫 외부 인식
  - method: 약속하지 않고 lot sheet 익명 코드 누적 데이터 한 장으로 야 곤도르웨에게 전달, 모판 이백 판 출하를 운송 매트릭스에 통합, 건기 가격 폭등 30~50% → 10~15% 양적 감소
  - **ARC-01 자본 목표 충족**: 폐농장 임차인 → 루곤도 채소 공급 허브 + 시청 실무자 첫 접점 (phase0 exit_function 정확 일치)
  - 신규 NPC: 야 곤도르웨 (시청 물가 안정 담당 실무자, 다음 시즌 데이터 패키지 미리 요청 → 첫 시청 실무자 접점)

These ten are current truth and constitute ARC-01 complete. Do not rewrite them unless a concrete schema or consistency issue is found.

## 4. Immediate Target Blocks

ARC-01 closed at Block 10. 다음 작업은 **ARC-02 진입**(Block 11+)이며 별도의 사전 작업이 필요하다:

- **선결 작업 1**: `treatments/phase0/africa_farm_king_phase0_design.json`의 `phase0_design.arcs[1]` (ARC-02) slot 정의 확장 (현재 phase0는 ARC-01만 block_slots 정의)
- **선결 작업 2**: ARC-02 capital_target / entry_function / exit_function / defeat_blocks 락 결정
- **선결 작업 3**: ARC-01의 미회수 부채 (장거리 foreshadow B1→11, B2→34·65, B5→44, B7→35·72, B9→28·91, B10→22·47·88) 중 어떤 것이 ARC-02에서 회수 대상인지 운영자 판단

ARC-02 진입은 **fresh operator order + phase0 ARC-02 slot 확장 완료** 후에만 가능. 현재 보유 자본은 Block 10 capital_after 그대로:
- 첫 건기 흑자 + 시청 실무자 첫 접점 + 정기 공급선 후보 표시 + 루곤도 채소 공급 허브 첫 외부 인식 + ARC-01 자본 목표 충족
- 외곽 15가구 묶음 + 운송 매트릭스 + 솔로몬 driver lead + 모판 이백 판 (재배 사이클 진행 중)
- 모세 카반다 첫 외부 신호 수신 (본대 vs 도윤 정면 충돌 균열점 — ARC-02에서 본격화)
- 본대 침묵 의미 전환 ('무시' → '데이터 수신')

## 5. Opening Doctrine

- Block 1 is setup only. Opening rescue does not start there.
- ARC-01 cider ledger 1-10 satisfied (10 unique types) and Block 7 is the locked defeat exception (`has_cider: false`, `pain_only_exit: true`).
- The full ARC-01 engine:
  - dead asset (B1) -> protection (B2)
  - protection -> water proof (B3)
  - water proof -> market-floor info (B4)
  - info -> first institutional delivery (B5)
  - delivery -> nursery + contract-grower bundle (B6)
  - bundle -> first night attack absorbed by decoy + dispersed storage (B7, locked defeat)
  - absorption -> public price sheet + renewal receipts + first quantitative defection (B8)
  - defection -> logistics matrix dispersing single-point disruption (B9)
  - matrix -> dry-season hub recognized by city hall via data (B10, ARC-01 exit)
- Block 11+ (ARC-02) must not reuse `access` / `protection` / `visible_token` / `reevaluation` / `proof` / `next_gate_opening` / `defeat` / `mass_defection` / `logistics_breakthrough` / `institutional_pivot` as `emotional_beat.type` (모두 ARC-01에서 소진).
- Do not turn this into military-action fiction.
- Do not turn this into NGO-good-deed fiction.
- Do not use `문명화` framing.
- Do not flatten locals into passive background NPCs.

## 6. Character Guardrails

- 강도윤 is not a savior. He is a systems operator.
- 모세 is not a loyal subordinate yet. He is a dangerous debt-bearer with a living calculation. After B7, his 30-day grace expired in spirit but still respected on the surface.
- 아미나 is not a kind helper. She cooperates only if the market flow benefits. After B6, she is a market-side advisor who flagged the 마칼리 perception shift first.
- 그레이스 is not impressed by effort. She trusts records, time, and repeatability. After B6, lot sheet contains its first farm-direct line.
- 조셉 is not comic relief or a simple mechanic. He is the first real infrastructure partner. After B7, he is also the first crisis co-defender.
- 마칼리 라인은 not street-thug caricature. They apply pressure through business, transport, protection, permits, fuel, and theft. B7에서 본대-하부 라인 분리 구조 노출, B8에서 가격 카드 무력화, B9에서 운송 봉쇄 카드 무력화. **본대 침묵의 의미가 '무시'에서 '데이터 수신'으로 바뀌었다.** 본대는 ARC-02에서 새 수익 보전 카드를 꺼내야 하는 동기를 부여받은 상태.
- 피터 루하카 (B6 신규, B8 갱신): 이름 익은 사이에서 첫 정식 계약자 → 셋째 주 갱신 계약자로 굳어짐. 도윤 수매표 첫 신뢰 포인트.
- 케빈 음와치 (B7 신규, 영구 차단): 내부 누수자. 처벌 대신 정보 가격으로 lot sheet 옆 영구 기록. **재등장 금지.**
- 도린 무봉가 (B8 신규, B9 등장): 외곽 가구 첫 마칼리 이탈자. lot sheet 익명 코드로 신규 등록. B9 운송 매트릭스 첫 두 주 안에 자기 첫 묶음 물량 무사 도착을 직접 본 첫 외곽 가구.
- 솔로몬 아바예 (B9 신규): 전직 루곤도-나이로비 미니버스 운전사 → 도윤 농장 첫 풀타임 driver lead. 운송 매트릭스 첫 설계자, 모세 메시지 첫 전달 채널.
- 모세 카반다 (B2/B7 회수, B9 첫 외부 신호): B7 야간 공격 후 처음으로 솔로몬을 통해 메시지를 흘림. 본대 vs 도윤 사이에서 자기 계산을 다시 짜고 있다는 신호. ARC-02 본격 충돌의 첫 균열점.
- 야 곤도르웨 (B10 신규): 루곤도 시청 물가 안정 담당 실무자. 매년 약속을 들고 온 사람들에게 카드를 잃어 온 자리. 도윤이 약속이 아니라 데이터를 들고 온 첫 사례. 다음 시즌 데이터 패키지를 먼저 요청 → 시청 실무자 첫 접점.

## 7. Copy-Paste Order

```text
africa_farm_king / 파병지에 돌아와 농업왕이 되었다

current truth first:
- docs/2026-04-09/africa_farm_king_live_status.md
- docs/2026-04-09/africa_farm_king_opening_handoff.md
- material_ssot/20_pitch/canon/africa_farm_king.md
- treatments/phase0/africa_farm_king_phase0_design.json
- treatments/africa_farm_king_tr_block_001_draft.json

order:
- preserve saved Block 1-10 ARC-01 complete exactly (byte-exact)
- ARC-02 진입 (Block 11+)은 fresh order 필요
- ARC-02 진입 전에 phase0 ARC-02 slot 확장이 선결되어야 함
- ARC-02 emotional_beat.type은 ARC-01에서 사용한 10개 라벨 재사용 금지
- do not start BI or work_guard 아직 (운영자 fresh order 필요)
- 직전 사례: 5블록 단일 패스(Block 6-10)는 한도 초과로 끊긴 적 있음. 1-2블록 패스는 안전.
```

## 8. Carry-forward Debts (ARC-02에서 의식할 것)

### ARC-01 미회수 장거리 foreshadow 부채 (의도적 이월)
- **B1→11**: 도윤 한국 퇴직금/정산금의 마지막 흔적 (ARC-02 자본 추가 투입 단계 단서로 활용 가능)
- **B2→34·65**: 모세 카반다 본격 회수 라인 (ARC-02 mid + ARC-03 long)
- **B5→44**: 그레이스 lot sheet 정기 공급선 본격 계약 단계
- **B7→35·72**: 본대 vs 하부 라인 정면 충돌 + 하부 라인 매트릭스 매뉴얼 회수
- **B9→28·91**: 솔로몬 driver 라인 도시 외곽 도로 네트워크 확장
- **B10→22·47·88**: 학교 급식 + 국가 비상 공급선 첫 입찰 + 도시 간 확장 신뢰 자본

### ARC-01 회수 완료 부채 (참조용)
- **B2 모세 30일 시계**: B7 만기 이틀 전 표면 회수 + B9 모세 첫 외부 신호 송신으로 양 단계 완전 회수
- **B5 그레이스 'lot sheet 먼저 보내 달라'**: B10 건기 안정 공급선 표시로 한 사이클 만에 회수
- **B6 첫 두 농가 시범 계약**: B8 셋째 주 갱신 영수증으로 회수
- **B6 첫 모판 이백 판**: B10 건기 시즌 종자 풀로 회수
- **B7 분산 보관 logic**: B9 운송 매트릭스로 확장 회수
- **B8 양적 전환**: B10 시청 측 첫 외부 신호로 회수
- **B8 익명 코드 lot sheet**: B10 데이터 한 장으로 회수

### ARC-02 진입 시 강제 제약
- ARC-01에서 사용한 10개 cider beat label 재사용 금지: `access` / `protection` / `visible_token` / `reevaluation` / `proof` / `next_gate_opening` / `defeat` / `mass_defection` / `logistics_breakthrough` / `institutional_pivot`
- 케빈 음와치 영구 차단 (재등장 금지)
- 본대-하부 라인 분리 구조 honor (표면 사건 위임 원칙)
- 모세 카반다 본대 vs 도윤 사이 계산 = '데이터 수신 후 새 카드' 단계
- 도윤은 더 이상 outsider가 아니라 '루곤도 건기 안정 공급의 첫 외부 인식 주체'에서 시작

### ARC-02 진입 선결 작업
1. phase0 ARC-02 slot 정의 확장 (현재 phase0는 ARC-01만 block_slots 정의)
2. ARC-02 capital_target / entry_function / exit_function / defeat_blocks 락 결정
3. 위 미회수 장거리 부채 중 ARC-02 회수 대상 선별
