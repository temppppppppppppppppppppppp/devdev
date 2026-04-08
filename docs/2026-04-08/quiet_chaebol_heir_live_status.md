# quiet_chaebol_heir live status

Date: 2026-04-08
Status: current operator truth
Work ID: `quiet_chaebol_heir`
Family: `blockguide`

## 1. Operator Reading

- inventory role: `active_tr_live`
- operational state: `tr_block_1_25_serialized_arc03_first_half_complete`
- schema status: `pass` (Stage 0 4-pack validated by `scripts/stage0_handoff_validator.py`)
- benchmark alias: `not_applicable`
- benchmark freshness: `not_applicable`
- current authority anchor:
  - `material_ssot/20_pitch/canon/quiet_chaebol_heir.md` (pitch authority, unchanged)
  - `treatments/phase0/quiet_chaebol_heir_phase0_design.json` (Phase0 authority, unchanged)
  - `treatments/quiet_chaebol_heir_tr_block_001_draft.json` (live TR, Block 1-25 serialized, ARC-01 + ARC-02 완료 + ARC-03 전반 진행 중)
  - `docs/2026-04-08/quiet_chaebol_heir_block_001_010_audit.md` (Block 1-10 self-audit, PASS)
  - `docs/2026-04-08/quiet_chaebol_heir_block_011_020_audit.md` (Block 11-20 self-audit, PASS)
  - `docs/2026-04-08/quiet_chaebol_heir_capital_allocation_guard.md` (§6 limited_guarded_release for Block 21-30, 2026-04-08 적용)

## 2. Current Live Artifacts

- canonical pitch (pitch authority):
  - `material_ssot/20_pitch/canon/quiet_chaebol_heir.md`
- selection-ready candidate of record (promoted from, historical):
  - `material_ssot/20_pitch/intake/fresh_20260408_batch01/01_quiet_chaebol_heir.md`
- raw memo archive:
  - `material_ssot/20_pitch/archive/raw_idea_memos/2026-04-08_new_idea_batch01.md`
- preprocess bundle (Stage 0 4-pack):
  - `treatments/preprocess/quiet_chaebol_heir/source_manifest.json`
  - `treatments/preprocess/quiet_chaebol_heir/profile_lock.json`
  - `treatments/preprocess/quiet_chaebol_heir/material_bundle_summary.json`
  - `treatments/preprocess/quiet_chaebol_heir/phase0_ready_snapshot.json`
- root Phase0:
  - `treatments/phase0/quiet_chaebol_heir_phase0_design.json` (7 ARCs × 10 blocks = 70 block slots, locked sibling axes + round order + 4-step internal ladder embedded)
- live TR:
  - `treatments/quiet_chaebol_heir_tr_block_001_draft.json`
  - saved live boundary: **Block 1-25 (ARC-01 + ARC-02 완료 + ARC-03 Block 21-25)**
  - `_total_blocks` = 25, `_saved_block_boundary` = 25, `_next_continuation_boundary` = 26
  - blocks serialized (Block 1-10, ARC-01): `Block 1 조용한 좌천` → `Block 2 첫 현장 순회` → `Block 3 하루짜리 실험` (첫 cider, protection) → `Block 4 지역본부장의 첫 견제` → `Block 5 리베이트 라인` → `Block 6 긴급 MD 교체권` (authority_shift) → `Block 7 본사 직보 주간 보고선` (weighted_reevaluation) → `Block 8 임대 재협상권` (authority_shift_extension) → `Block 9 다른 매장 비교` → `Block 10 권역 파일럿 검토권` (next_gate, ARC-01 출구)
  - blocks serialized (Block 11-15): `Block 11 두 번째 매장` → `Block 12 협력 점장` (collaborative_alignment) → `Block 13 보수파 저항` (defeat block) → `Block 14 권역 예산 발언권` (authority_shift) → `Block 15 리베이트 정리의 출구` (조용한 블록 4/4)
  - blocks serialized (Block 16-20, ARC-02 후반): `Block 16 국내 조달선 조정권` (authority_shift, 매장 A +22% 검증) → `Block 17 권역 단위 운영권` (authority_shift_major, ARC-02 핵심 reward, 지역본부장 보조 라인 전환, Stage 2→3 임계점) → `Block 18 그룹 레벨 재무 라인의 신호` (signal-only buildup, ARC-03 사전 신호) → `Block 19 권역 보고 공개` (quiet signal, 장남 라인 비서실 시야 진입, 다축 압력 사전 신호) → `Block 20 권역 본진 (ARC-02 출구)` (next_gate, ARC-03 간접 예고, Stage 3 임계점 돌파 준비)
  - blocks serialized (Block 21-25, ARC-03 전반): `Block 21 재무팀 호출` (first_division_floor_access, 사업부 자본배분 사전 검토 회의 배석권 + 5분 발화 기록) → `Block 22 사업부 보수파의 벽` (tactical_authority_shift, 보수파 `시기상조` 논리를 검증 요청으로 전환, 사업부 5곳 진단 권한 한시 수령) → `Block 23 보고선 차단` (defeat_block_structural, 절차 vs 결과 분리, 3주 대기 → 검증 강화 전환) → `Block 24 회장의 첫 호명` (weighed_recognition, 회장 본인 첫 등장 비공식 30분 자리, `네 절차로 풀어라` 룰 외적 확인) → `Block 25 장남의 한 마디` (axis_preservation quiet block, 강도윤 본인 첫 발화 메시지, 회신 없음으로 본인 축 보존)
  - current stop boundary: **Block 025 (5의 배수 경계, harness §1.1B 5-block auto-run cap 자동 정지). Block 030 도달 시 §1.1C 세 번째 10-block self-audit gate 발동 예정 (Block 21-30 window)**
  - Block 1-10 self-audit gate: **PASS**
  - Block 11-20 self-audit gate: **PASS**
  - capital_allocation_guard §6 limited_guarded_release: 2026-04-08 적용 (운영 오더 `ㄱㄱㄱㄱ` 해석). Block 21-30 한정 인물 whitelist 확장(본사 기획실장·그룹 재무팀 차장·사업부장·사업부 보수파 임원·회장·강도윤), 본격 의결 장면 금지 유지
  - filename note: container filename은 `_tr_block_001_draft.json`으로 시작하지만, saved boundary는 파일명이 아니라 `_saved_block_boundary` 메타와 이 doc의 명시값이 authoritative다
- published work_guard:
  - not present
- live BI:
  - not present

## 3. Boundary Rule

- the current saved truth ends at **Block 20** inside the live TR file `treatments/quiet_chaebol_heir_tr_block_001_draft.json`. ARC-01 + ARC-02 모두 완료.
- canon pitch `material_ssot/20_pitch/canon/quiet_chaebol_heir.md` remains the upstream pitch authority; TR must not silently override it
- Phase0 `treatments/phase0/quiet_chaebol_heir_phase0_design.json` remains the plan authority; live TR is the serialized saved boundary
- intake candidate at `fresh_20260408_batch01/01_quiet_chaebol_heir.md` remains as historical promotion source only
- saved boundary timeline on 2026-04-08:
  - Phase0 (70 slots) → 1st envelope Block 1-3 → 2nd envelope Block 4-5 → 3rd envelope Block 6-10 → Block 1-10 self-audit **PASS** → 4th envelope Block 11-15 → 5th envelope Block 16-20 (운영 오더 `ㄱㄱㄱㄱ`) → Block 020 자동 정지 → Block 11-20 self-audit **PASS** → ARC-03 진입 대기
- `_saved_block_boundary` inside the live TR file equals 20 and must match this doc
- do not infer a larger saved boundary from Phase0 slot text or from this current-truth doc's later sections
- do not infer a smaller saved boundary from the unchanged container filename `..._tr_block_001_draft.json`
- ARC-02 reward chain (ARC-01 6/6 이후 별도 카운트): **5단 + ARC-02 핵심 reward 완결**
  - ARC-02 1단: 매장 A 점장 협력 합류 (Block 12, collaborative_alignment)
  - ARC-02 2단: 권역 예산 발언권 + 편성 2줄 (Block 14, authority_shift, Block 13 defeat 전환)
  - ARC-02 3단: 국내 조달선 조정권 + 보조 업체 + 매장 A +22% 검증 (Block 16, authority_shift)
  - ARC-02 핵심: **권역 단위 운영권 (Block 17, authority_shift_major)** + 지역본부장 보조 라인 전환
  - ARC-02 출구: ARC-02 공식 완성 + ARC-03 간접 예고 (Block 20, next_gate)
  - 누적 자산 (ARC-01+ARC-02): 공식 권한 12건 + 협력 라인 3건 + 명분 자산 4건 + 현장 검증 2건 + 신호 자산 2건 = 23 자산
- ARC-01 reward chain: **6/6 수령 완료** (유지):
  1. 폐점 결재 30일 보류 (Block 3, protection)
  2. 현장 운영대행 직함 (Block 3, protection)
  3. 긴급 MD 교체권 지속적 (Block 6+7, authority_shift)
  4. 소액 예산 인장 (Block 6, authority_shift)
  5. 본사 직보 주간 보고선 (Block 7, weighted_reevaluation)
  6. 임대 재협상권 (Block 8, authority_shift_extension)
  7. 권역 파일럿 검토권 (Block 10, next_gate)
- internal ladder status: **Stage 2 → Stage 3 임계점 돌파 준비 완료** (Block 10 Stage 2 진입 선언 → Block 11-16 6단계 외적 증명 → Block 17 `이제는 여기가 내 자리다` 자기 인정 → Block 20 `이제 멈출 수 없다` + `책임감` 첫 언어화). 공식 Stage 3 전환은 ARC-03 안에서 집행 예약 (`경영의 재미` 차원 첫 등장 시점)
- canon ledger drift note: canon material-benchmark-readiness-harness의 strict 2-6 cider window 요구와 Phase0 Block 4/5/9 buildup 재매핑 사이의 드리프트가 §3A에서 lock된 상태로 유지. Block 1-10 self-audit §3 top_risk #5에 공식 기록됨
- BI는 아직 미진입 상태다

## 3A. Canon Locks Frozen (TR 착수 전 변경 금지)

아래 항목은 canon + Phase0 + Stage0 4-pack이 이미 잠근 내용이다. TR 착수 시 이 줄들은 출발선이자 계약이며, 변경은 `canon_tighten` 또는 `phase0_build` 별도 task를 통해서만 가능하다.

- **First arena lock**: Block 1 오프닝 무대는 본사 전략실·HQ 회의실이 아니라 지방 생활몰 `문하 생활관` 현장이다. 후계 회피형 막내가 좌천처럼 받은 첫 자리.
- **Block 2 첫 현장 순회 lock**: Block 2는 서준이 첫날 현장 순회를 도는 블록으로, `닫혀 있는 측면 출입구 + 엉망인 푸드코트 좌석 회전 + 병원 셔틀 동선과 안 맞는 영업시간 + 지역본부 판촉비 누수`가 동시에 서준의 눈에 읽히는 구조를 지킨다. 첫 개입은 `조용히 넘어가려던 걸 못 참고` 하루짜리 실험을 강행하는 식으로 일어난다.
- **Block 3 첫 cider lock + canon-locked 6-item reward chain 시작**: Block 3는 하루짜리 운영 실험이 당일 POS 점심 매출과 푸드코트 회전율을 즉시 반전시키는 블록이다. 같은 블록 안에서 `폐점 결재 30일 보류`와 `현장 운영대행 직함`이 붙는다. 이 지점부터 canon 6종 reward chain이 가동된다:
  1. Block 3 — 폐점 결재 30일 보류 + 현장 운영대행 직함 (protection)
  2. Block 6 — 긴급 MD 교체권 + 소액 예산 인장 (authority_shift, 누수 노출로부터)
  3. Block 7 — 본사 직보 주간 보고선 (weighted_reevaluation)
  4. Block 8 — 임대 재협상권 (추가 권한)
  5. Block 10 — 권역 파일럿 검토권 (next_gate, ARC-02 입장권)
  - 6종 중 어느 것도 칭찬·호감·친분·미담으로 대체될 수 없다.
- **Internal ladder 4단계 lock**:
  - Stage 1 (ARC-01~02): `쉬고 싶다` — 일부러 손을 눌러 두는 모드
  - Stage 2 (ARC-03): `계속 성공한다` — 본인은 피곤한데 권한은 계속 붙는다
  - Stage 3 (ARC-04~05): `책임감 + 경영의 재미` — 형/누나 라운드 옆에서 자각
  - Stage 4 (ARC-06~07): `의미 창출 + 승부욕` — 처음으로 능동 진입
  - 초반(ARC-01~02) `후계 경쟁 회피` 자기이익을 중반까지 절대 잃지 않는다.
- **3축 non-overlap rule**:
  - 형 강도윤 = `생존과 안정` (원칙·숫자·리스크)
  - 누나 강민서 = `브랜드와 대외전` (여론·협상·사람)
  - 서준 = `죽은 사업의 재생과 확장` (현장·구조 읽기·자본배분)
  - 한 축이 다른 축을 침범하지 않는다. 서준이 ARC-04/05 안에서 자기 축의 일을 대신 해 버리면 축 구조가 무너지고 ARC-06~07이 공허해진다.
- **후계 라운드 순서 lock**: ARC-04 형 라운드 → ARC-05 누나 라운드 → ARC-06 서준 라운드 → ARC-07 세 축 결합 파이널. 이 순서는 뒤집을 수 없다. 서준 라운드는 `형이 그은 선 안쪽 + 누나가 열어 둔 판 위`라는 조건을 시각적으로 남겨야 한다.
- **do_not_fake / 축 비침범 / 미담화 금지 / 형·누나 경쟁자 가드**:
  - 생활몰 동선·POS 매출·임대차 계약·판촉비 누수·리베이트 구조·원가·환율·국제 물류·국가 리스크는 추상 교양처럼 흘리지 않고 실제 판단 근거로 써야 한다
  - 상권 회생은 감동·미담·입소문·기적이 아니라 `구조 읽기 → 운영 수정 → 같은 블록 안에서 숫자 반전` 3단으로만 증명한다
  - 블록 간 권한 연쇄: 다음 전장은 직전 블록에서 회수한 권한으로만 열려야 한다
  - 형·누나는 존중 가능한 경쟁자다. 관계 파탄·증오·복수 엔진 금지, 바보 악역 금지
  - 지역본부장과 형제들은 `이전 시대의 정답으로 버티는 사람들`로 그려진다
  - 가족 멜로·가족 막장이 현장 business-power를 덮으면 안 된다
- **Provisional canon name lock**: 그룹명 `대륜그룹`, 생활몰 실명 `문하 생활관`, 지역 도시명은 미지정 상태로 잠정 고정한다. 별도 operator 지시 없이 임의 작명으로 확장 금지. TR 본문에서는 지역 도시명을 특정하지 말고 `지방 도시`, `권역 내 상권` 수준으로 유지한다.

## 3B. Remaining Risks Triage (`phase0_ready_snapshot.remaining_risks` 재분류)

| # | 리스크 | 분류 | 첫 관련 블록 |
|---|--------|------|--------------|
| a | 그룹명·생활몰 실명·지역 도시명 | `hard_gate_before_block1` (provisional codename lock으로 해소) | Block 1 |
| b | 그룹 자본배분 회의 메커니즘 최소 현실성 | `deferred_gate_block31` (Block 1-10 금지선은 별도 guard 문서) | Block 21 (ARC-03 첫 접점), Block 31 (ARC-04 본격 발동) |
| c | 해외 조달선 국가 후보 + 환율/원자재 민감도 표 | `deferred_gate_block50` | Block 50 (ARC-05 글로벌 소싱 파일럿권 진입) |
| d | 형/누나/서준 각자의 대표 승부 1건 구체 안건 | `deferred_gate_block31` | Block 31 (형의 라운드 첫 블록) |

### Risk (a) — provisional canon name lock
- 왜 지금 닫는가: Block 1 오프닝이 `대륜그룹 막내가 문하 생활관에 내려가는` 장면이라 그룹명·생활몰명이 첫 문장부터 필요하다.
- 해소 방식: 확정 근거가 없으므로 임의 작명하지 않고 현재 codename(`대륜그룹`, `문하 생활관`)을 provisional canon name으로 잠근다. 지역 도시명은 특정하지 않는다.
- 미이행 시 초반 TR 금지사항: TR 본문 안에서 새로운 그룹명·생활몰명·지역 도시명을 발명하거나 기존 codename과 다른 이름으로 바꿔 쓰기 금지.

### Risk (b) — 자본배분 회의 메커니즘
- 왜 뒤로 미뤄도 되는가: ARC-01(Block 1-10)은 전적으로 생활몰 현장·지역본부·본사 기획실 직보선 범위 안에서 움직인다. 그룹 자본배분 회의는 ARC-03 Block 21(재무팀 호출)에서 처음 접점이 생기고, ARC-04 Block 31의 형 라운드 차입 재편에서 본격 발동된다.
- 최소 현실성 가드 문서: `docs/2026-04-08/quiet_chaebol_heir_capital_allocation_guard.md` 참조. Block 1-10에서 다루면 안 되는 본사·투자·예산 의사결정 표현 금지선을 명시한다.
- 미이행 시 초반 TR 금지사항: Block 1-10에서 `그룹 자본배분`, `차입 구조`, `이사회 의결`, `사업부 간 배분`, `비핵심 자산 정리`, `전무·대표이사급 예산 의결`, `그룹 재무팀 안건` 표현 사용 금지. Block 1-10의 본사 관련 서술은 `본사 기획실 직보 주간 보고선` 범위로 제한한다.

### Risk (c) — 해외 조달선·환율/원자재 민감도
- 왜 뒤로 미뤄도 되는가: 해외 조달선·국가 리스크·환율 민감도는 ARC-05 Block 50(글로벌 소싱 파일럿권 진입)에서 처음 등장한다. ARC-01~02는 국내 조달·권역 운영만 다루며, ARC-03도 사업부 단위 진단일 뿐 해외 라인 미진입이다.
- 미이행 시 초반 TR 금지사항: Block 1-49에서 해외 조달·국제 물류·국가 리스크·환율 민감도를 장면의 판단 근거로 쓰지 말 것. Block 16(권역 단위 조달선 조정권)은 `국내` 범위로 명시되어 있으니 이 경계를 지킨다.

### Risk (d) — 형/누나/서준 각자의 대표 승부 1건 구체 안건
- 왜 뒤로 미뤄도 되는가: 형·누나·서준의 대표 승부는 각각 ARC-04·ARC-05·ARC-06의 라운드 본체다. ARC-01~03(Block 1-30)은 서준이 자기 축 안에서 권한을 쌓는 단계로, 형·누나는 Block 19·25·27·30에서 `시야 진입`과 `짧은 대화` 수준으로만 등장한다.
- 미이행 시 초반 TR 금지사항: Block 1-30에서 형 강도윤의 구체적 구조조정 사건, 누나 강민서의 구체적 해외 합작/리브랜딩 사건, 서준의 사업부 단위 재생 사건을 본격적으로 서술하지 말 것. Block 19·25·27·30은 `보고서가 형 비서실로 넘어갔다`, `형이 사석에서 짧게 물었다`, `누나 보좌관이 요청을 보냈다` 수준의 윤곽만 허용.

## 3C. Pre-Block1 Hard Gates (TR 착수 직전 마지막 체크)

- [x] canon pitch locked (`material_ssot/20_pitch/canon/quiet_chaebol_heir.md`)
- [x] Phase0 serialized (`treatments/phase0/quiet_chaebol_heir_phase0_design.json`, 7 ARCs × 10 blocks)
- [x] Stage 0 4-pack validator PASS (`scripts/stage0_handoff_validator.py`)
- [x] Risk (a) resolved via provisional canon name lock (본 문서 §3A 마지막 항목)
- [x] Risk (b) guard 문서 작성 (`docs/2026-04-08/quiet_chaebol_heir_capital_allocation_guard.md`)
- [x] 첫 envelope 확정 (`docs/2026-04-08/quiet_chaebol_heir_operator_schedule.md`)
- [x] TR 파일 생성 완료 (`treatments/quiet_chaebol_heir_tr_block_001_draft.json`, Block 1-3 serialized, stop gate 5/5 PASS, 2026-04-08)

## 4. Next Allowed Tasks

- 직전 게이트 결과 (history, not pending):
  - 1st envelope (Block 1-3) PASS / 2nd (Block 4-5) PASS / 3rd (Block 6-10) PASS
  - Block 1-10 self-audit: **PASS**
  - 4th envelope (Block 11-15) PASS / 5th (Block 16-20) PASS (운영 오더 `ㄱㄱㄱㄱ`)
  - Block 11-20 self-audit: **PASS** (`docs/2026-04-08/quiet_chaebol_heir_block_011_020_audit.md`)
  - ARC-01 완료 (reward chain 6/6) + ARC-02 완료 (핵심 reward = 권역 단위 운영권 Block 17, 지역본부장 보조 라인 전환, ARC-02 출구 Block 20)
  - Stage 1 → Stage 2 전환 공식 + Stage 2 6단계 외적 증명 + Stage 2 → Stage 3 임계점 돌파 준비 완료
  - capital guard 위반: **0건** (Block 1-20 전수 sweep)
  - group-level 금지 인물: **0명** (Block 1-20 전수 sweep, 본사 기획실장만 whitelist Block 6·7·8·10·14·16·17·20 등장)
  - sibling 본인 (강도윤·강민서·회장·부회장·전무) 장면 등장 0건 (Block 19 장남 라인 비서실은 라인 수준 메모, 인물 미등장)
  - same-turn repair: 메타 필드 2건 스크럽 (`강도윤` 문자열 → `장남`으로 우회, `그룹 자본배분 회의` → `그룹 레벨 배분 라인`으로 우회). 장면 본문은 처음부터 클린.

- `tr_continue` into Block 21-25 또는 Block 21-30 — 현재 다음 작업 후보:
  - **운영자 차원의 사전 결정 1건 필수**: capital_allocation_guard §5 `deferred_gate_block31` 해제 결정 (limited_guarded_release / full_release / 추가 조사 후 결정 중 하나). 미해제 시 ARC-03 본문에 그룹 레벨 자본배분 표현이 등장해야 하는 블록(Block 21·26·29·30)이 매번 HOLD
  - 새 operator 오더가 범위를 명시해야 진행
  - same live TR file 유지 (`treatments/quiet_chaebol_heir_tr_block_001_draft.json`), rename 금지
  - harness §1.1B 5-block auto-run cap 적용 → 다음 정지선은 Block 025 (5의 배수 경계)
  - Block 030 도달 시 §1.1C 세 번째 10-block self-audit gate (Block 21-30 window) 즉시 발동
  - ARC-03 진입: Phase0 ARC-03 슬롯 21-30 참조
    - Block 21 재무팀 호출 (Block 18 신호 실체화)
    - Block 22 사업부 보수파의 벽
    - Block 23 보고선 차단 (defeat block, Block 13과 다른 패배 형태 필요)
    - Block 24 회장의 첫 호명 (회장 본인 등장 — capital guard scene 제한 해제 필요)
    - Block 25 강도윤의 한 마디 (형 본인 등장 — Block 19 신호 실체화)
    - Block 26 사업부 안건 진입
    - Block 27 강민서의 첫 접점 (누나 본인 등장)
    - Block 28 보수파의 역공 (defeat block)
    - Block 29 사업부 자본배분 발언권 (ARC-03 핵심 reward)
    - Block 30 세 자녀가 한 테이블 (ARC-03 출구)
  - Block 21-30 audit top_risks (Block 11-20 audit §3): deferred_gate 해제 / villain dignity (회장·형·누나 첫 등장) / Stage 3 의미 중복 회피 / defeat block 변주 / canon ledger drift / 보고서 형식 ARC-03 변형
- `tr_self_audit` (Block 21-30 10-block self-audit gate) — Block 030 도달 직후 필수
- `tr_continue` into Block 31+:
  - blocked until the Block 21-30 self-audit gate returns PASS
  - ARC-04 형의 라운드 진입 영역 (Phase0 ARC-04 슬롯 31-40)
- `canon_tighten` / `phase0_build` (bounded revision): canon 또는 Phase0가 TR과 어긋날 때만
- `bi_refresh`: TR이 더 쌓인 뒤 별도 스케줄
- `work_guard`: 별도 task, 자동 추론 금지
- **Forbidden in this slot**:
  - Block 21 이후 생산 (운영자 새 오더 없이 + capital_allocation_guard §5 해제 결정 없이)
  - BI / work_guard / Phase0 story 본문 확장 / canon 재작성
  - capital guard §3.1 금지 용어·§3.2 금지 장면 (해제 전까지)
  - Block 30 self-audit gate 스킵
  - provisional canon name을 실제 그룹명·도시명·인물 실명으로 임의 교체
  - 5-block cap 초과 연속 진행

## 5. Known Non-Truth Docs

- the raw idea memo is archive context, not current pitch authority
- the intake candidate file is the promotion source of record, not the current pitch authority

## 6. Delegation Rule

- use this file, `material_ssot/20_pitch/README.md`, `material_ssot/20_pitch/material-benchmark-readiness-harness-v1.md`, and the canon file as the current entry set
- the intake candidate file may be read as a historical reference, but any new downstream task must treat the canon file as the authority anchor
- do not fabricate preprocess, `Phase0`, `TR`, `BI`, or `work_guard` artifacts in a `canon_tighten` task
