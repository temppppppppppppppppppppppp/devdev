# jaebeol3se_loss_line — Cross-PC Handoff Context

Date: 2026-04-08
Status: mid-ARC-02 TR production, Block 25/70 saved, defeat_blocks [18, 24] 통과
Work ID: `jaebeol3se_loss_line`
Family: `blockguide`
Profiles: `investment_market_profile` + `office_power_profile`

## 0. One-Line State

현재 TR Block 25 저장 완료. ARC-01(1-15) cap 완주 + ARC-02(16-30) partial 10/15. 1-10/11-20 감리 모두 PASS. 다음 작업: `tr_continue` Block 26 only.

## 1. Read Order (다른 PC에서 이어받을 때 이 순서대로 읽기)

1. **이 문서** (`docs/2026-04-08/jaebeol3se_loss_line_cross_pc_handoff_2026-04-08.md`)
2. **Current-truth doc**: `docs/2026-04-08/jaebeol3se_loss_line_live_status.md` — 살아있는 boundary·NPC 상태·Next Allowed Tasks
3. **Canon 앵커**: `material_ssot/20_pitch/canon/jaebeol3se_loss_line.md` — 피치 원본, contamination guard, 보상 순서
4. **Phase0 설계**: `treatments/phase0/jaebeol3se_loss_line_phase0_design.json` — 5 ARCs × 70 blocks 설계
5. **Work guard**: `work_guards/investment/jaebeol3se_loss_line.yaml`
6. **Current-root TR**: `treatments/jaebeol3se_loss_line_tr_block_005_draft.json` — `_saved_block_boundary: 25`, 블록 본문 25개
7. **감리 노트 2건 (순서대로)**:
   - `treatments/preprocess/jaebeol3se_loss_line/05_audits/block_001_010_audit_2026-04-08.md`
   - `treatments/preprocess/jaebeol3se_loss_line/05_audits/block_011_020_audit_2026-04-08.md`
8. **하네스**: `docs/blockguide/treatment-production-harness-v2.md` (특히 §1.1C 10-block 자체 감리, §1.2 quality-first 1블록 단위)
9. **Envelope 스펙**: `material_ssot/00_governance/delegation-envelope-spec-v1.md` — envelope 분리 원칙

## 2. Quarantine — 절대 근거로 쓰지 말 것

아래 항목들은 **historical/unresolved**로 격리 상태. 디스크 위 사실과 충돌하거나 검증 불가. 어떤 envelope에서도 입력으로 사용 금지.

- `treatments/preprocess/jaebeol3se_loss_line/context_handoff_20260406.md` 의 `Block 1~57 저장` 주장 (실제 legacy 파일은 Block 1-5만 존재, 현재-루트 TR은 25블록)
- 같은 handoff §11 `Block 58/59/60 사전 선언 본문`
- 같은 handoff의 `230억 capital path` (0→50→47→53→65→200→230)
- 같은 handoff의 `Block 51~60 감리 PASS` 표 주장
- 같은 handoff의 `Block 57 NPC state` / `Block 57 open foreshadows`
- 구식 BI: `bible/10_bi_jaebeol3se_loss_line.json` (현재-루트 BI 파일 미존재 전제)
- 미존재 파일: `material_ssot/20_pitch/synthesis/investment_dokshik_jaebeol3se_working_synthesis.md`
- 구식 경로 주장: `treatments/10_jaebeol3se_loss_line_tr_block_070_draft.json` (이 경로는 디스크에 없음)

## 3. Hard Rules (canon 및 하네스 강제 조항)

### 3.1 보상 순서 (절대 뒤집지 않음)

`평가 수정 → 권한 → 자본`

- reward 첫 문장에 자본 수치가 먼저 오면 즉시 **asset-first 위반**
- 자본 등장 지점(B14 운용 권한 / B24 외부 포지션 / B25 장부)은 모두 첫 문장 양식이 `권한 위탁` 또는 `두 레인 분리` 또는 `집행 단위 재산정`으로 활자화됨 — 이 양식 재사용 강제

### 3.2 Dual-lane separation

- **내부 레인**: 사내 결재 데이터(보험 대시보드 B12 / 사내 결재 시스템 / 운용 권한 페이지 B14) — **사내 손실 방어 + 권한 회수에만 사용**
- **외부 레인**: 공개 데이터만(로이즈 인덱스, 공개 손해율 통계, 공개 해운 지표, 공개 공급망 뉴스) — **외부 포지션에만 사용**
- 두 레인 간 데이터 0줄 크로스 오버 엄수 — **insider-trading 구조 절대 금지**
- 외부 레인 폴더는 도진우 본가 서재 집 노트북에 있으며 출처 룰 5줄 + 출처 로그 5건이 물리적으로 분리되어 기록 (B8 신설, B15/B17/B20/B24에서 진화)
- **자본 경로도 분리**: 사내 운용금 50억 한도(B14) vs 개인 외부 자금(B24 첫 집행). 두 경로 완전 분리가 B25에서 사내 결재 시스템 표준 양식으로 공식 고정

### 3.3 Antagonist 처리

- 사촌 형 **도현석**: "숫자를 따로 봤기 때문에 연결을 못 본 사람" — 무능 캐리커처 **0건** 연속 25블록 유지, 계속 지킬 것
- 보험 담당 임원 **임재훈**: "자존심 상하지만 숫자가 맞으니 입을 다문 사람" — 자발적 전환은 점진적 분할, 화해 미끄럼 금지
- 적대자는 **"이전 시대의 정답을 믿은 사람들"** — 합리적 경쟁 라인 유지

### 3.4 Envelope 분리 원칙

- 한 턴 = 하나의 envelope (`tr_continue` 1블록 / `block_audit_10` 1회 / 기타)
- 감리와 tr_continue는 같은 턴에 묶지 않음
- 감리 게이트는 Block 010, 020, 030, ... (treatment-production-harness-v2 §1.1C 필수)
- 감리 FAIL 시 같은 10블록 구간 수리 선행, PASS 전까지 다음 블록 금지

## 4. Current State Snapshot (Block 25 기준)

### 4.1 Serialized boundary

- Current-root TR: `treatments/jaebeol3se_loss_line_tr_block_005_draft.json` (파일명 suffix는 legacy, 내용은 25블록)
- `_schema`: `tr.v1`
- `_saved_block_boundary`: 25
- `_next_continuation_boundary`: 26
- `_total_blocks`: 70
- `_arcs_covered`: `["ARC-01 (complete 1-15 of 1-15)", "ARC-02 (partial 16-25 of 16-30)"]`

### 4.2 Block titles 1-25

ARC-01 (1-15 complete):
1. 리스크 표 만드는 도련님
2. 세 개의 숫자
3. 관리 범위입니다
4. 18일
5. 도련님이 감히
6. 회장의 메모
7. 손실선 카운트다운
8. 조용한 준비
9. 마진이 꺾이다
10. 선매입의 대가 (ARC-01 defeat_block)
11. 배석권
12. 대시보드 (ARC-01 quiet_block)
13. 공동 서명
14. 파일럿 50억 (자본 첫 등장, asset-first 차단 양식 등록)
15. 다음 손실선 (ARC-01 cap)

ARC-02 (16-25 partial):
16. 보험 테이블 (외부 협상 첫 동석)
17. 갱신안의 숨은 리스크 (dual-lane 첫 본격 발언)
18. 보험 담당의 반격 (ARC-02 defeat_block)
19. 숫자가 맞으니까 (임재훈 침묵 진입)
20. 실사 공문 (ARC-02 quiet_block)
21. 실사 서명
22. 사촌 형의 대안 (도현석 본격 재등장)
23. 두 장의 표 (회장 재등장, 두 체계 공존 등록)
24. 외부 포지션 실패 (ARC-02 defeat_block, 자본 첫 거래)
25. 손실의 영수증 (자발 보고 양식 사내 표준 채택)

### 4.3 누적 핵심 지표

- **사내 좌표 7건**: 결재선 직보(B6) / 회의실 자리(B11) / 시스템 권한(B12) / 결재선 서명(B13) / 운용 권한(B14) / 원가 연쇄 책임자(B21) / 자발 보고 표준 양식 발행자(B25)
- **외부 카운터파티 2인**: 보험사 협상 대표(B16) / 고객사 실사 담당자(B21)
- **dual-lane separation 행위 차원 작동 11회**: B8/B9·B10/B12/B14/B15/B16/B17/B20/B21/B24/B25
- **자본 집행**: 사내 운용금 50억 한도 거래 **25블록 전 구간 0건** / 개인 외부 자금 **첫 집행 + 첫 손실(B24) → 분기 순기여 플러스 산정(B25)**
- **감리**: Block 001~010 PASS, Block 011~020 PASS (모두 2026-04-08)
- **defeat_blocks**: ARC-01 [5, 10] 통과, ARC-02 [18, 24] 통과 — 네 개 전부 `부인 없이 인정 + 양식 등록` 양식
- **quiet_blocks**: ARC-01 [8, 12] 통과, ARC-02 [20] 통과 / [26] 예정

### 4.4 NPC 현재 상태

| NPC | 현재 상태 | 다음 예정 |
|-----|---------|---------|
| 도진우 (주인공) | ARC-02 partial, 사내 좌표 7 + 외부 좌표 2, 자발 보고 표준 양식 발행자 | B26 임재훈 협조 수령 |
| 도현석 (사촌 형) | Phase0 opponent transition 4단계 본격 대응 완료, 공존 구조 4단 완주 검증자, 전략적 공존 직전 | B43 최종 인정 예약 |
| 강태호 (CFO) | 표준 양식 등록 집행자 | B30 리스크 위원회 추천 발의자 예정 |
| 도경일 (회장) | 자발 보고 양식 표준화 지시자 (ARC-02 재등장 완료 B23/B25) | ARC-03 의결 단계 |
| 임재훈 (보험 담당 임원) | 분할 7단계 침묵 진입 (`먼저 자료를 가져옴` 직전) | **B26 최종 완주 예정** (분할 8단계) |
| 박동수 (구매실장) | 자발적 협조 직전 단계 | B27 `구매실장의 전화` 예약 |
| 정우진 (생산관리 상무) | 자발적 협조 직전 단계 | ARC-02 후반~ARC-03 |
| 보험사 협상 대표 | 숫자 공식 인정 후 재협상 진행 중 | B26 재협상 완료 |
| 고객사 실사 담당자 | 원가 연쇄 방어 구조 수용 | ARC-02 후반 |

### 4.5 자세 사슬 (7단 변주)

1. B11~16 발언 0회 (사내 회의 → 외부 협상 룸까지 확장)
2. B17 첫 외부 발언 + 공개 데이터 강제
3. B18 첫 반격에 대한 비반박 + 역할 분업 제안
4. B19 발언 신용을 분업 라인에 귀속
5. B20 감지 + 초안 보존
6. B22 받은 문서 정합성 인정 + 상호 보완 역제안 + 회의 프레임 사전 조정
7. B24~B25 첫 실전 defeat 자발 보고 → 양식의 사내 표준 업그레이드

### 4.6 열린 복선 (B26+ 회수 예약)

| Plant | Expected payoff | 거리 |
|-------|----------------|------|
| B18 실무 변수 가이드 v1 + B19 침묵 | B26 임재훈 `먼저 자료를 가져옴` 최종 완주 | 1블록 |
| B19 해상 라인 A/B/D 재조정 제안 | B26 보험 재협상 완료 | 1블록 |
| B21 박동수·정우진 자발적 협조 직전 단계 | B27 구매실장의 전화 | 2블록 |
| B20 trigger set 후보 2번 + 3번 | B28 공개 해운 지표 이상 신호 | 3블록 |
| B24 외부 포지션 실패 | B29 두 번째 적중 (재설계 수익) | 5블록 |
| B23 두 체계 공존 구조 | B30 리스크 위원회 정식 위원 추천 (ARC-02 cap) | 5블록 |
| B17 공개 발행처 활자화 + B25 표준 양식 | ARC-03 B39~40 도현석 내부 정보 사용 의심 방어 | 14~15블록 |
| B22~25 도현석 공존 구조 | ARC-03 B43 사촌 형의 인정 (전략적 공존 최종) | 18블록 |
| B10/B25 `집행 단위 재산정` 회계 어휘 | ARC-03 B42 세 번째 손실선 + ARC-04 B58 안팎 동시 방어 | 17~33블록 |

## 5. 다음 즉시 Action

### 5.1 Current envelope

**`tr_continue` Block 26 only**

- Phase0 ARC-02 Block 26 — title `보험 재협상 완료`, function: "도진우가 주도한 보험 재협상이 유리한 조건으로 마무리된다. 보험 담당 임원이 처음으로 도진우에게 먼저 자료를 가져온다." (`quiet_blocks: [20, 26]`)
- **핵심**: 임재훈 분할 8단계 최종 완주 — 침묵(B19) → `먼저 자료를 가져옴`(B26). 감리 next_10_focus #5/#6 완주 지점
- 직접 근거: B17~19 공개 데이터 대조표 + B19 임재훈 침묵 진입 + B25 자발 보고 양식 표준 채택
- quiet_block 톤 유지, 화해 미끄럼 금지 (분업 축 내부 자기 영역 방어 양식)
- dual-lane 12번째 작동 유지
- 사내 운용금 50억 한도 거래 0건 유지
- Write scope: TR 1개 + live_status 1개
- 하드스톱: handoff §11 / quarantine / canon·phase0·work_guard·BI/governance/harness 본문 / Block 27 이상 선행 작성 / 임재훈 화해 양식 전환 / 자본 집행 서두르기 — 전부 금지

### 5.2 남은 ARC-02 5블록 예고 (B26~B30)

| Block | Title | Type | 핵심 |
|-------|-------|------|------|
| B26 | 보험 재협상 완료 | quiet_block | 임재훈 분할 8단계 최종 완주 |
| B27 | 구매실장의 전화 | production | 박동수 자발적 연락 (B21 사전 토대 payoff) |
| B28 | 공개 해운 지표 | production | 새 이상 신호 감지, 외부 레인 재설계 (trigger 후보 2번 payoff) |
| B29 | 두 번째 적중 | production | B24 실패 회수, 외부 포지션 첫 수익 |
| B30 | 리스크 위원회 추천 | **ARC-02 cap** | CFO가 도진우를 리스크 위원회 정식 위원으로 추천, ARC-03 입장권 |

### 5.3 감리 게이트 (하네스 강제)

- 다음 필수 감리: **Block 030 저장 후 Block 021~030 자체 감리** (treatment-production-harness-v2 §1.1C)
- 감리 범위 예정: B21 원가 연쇄 / B22~23 도현석 공존 / B24 외부 실패 삼중 검증 / B25 표준 양식 / B26 임재훈 완주 / B27 박동수 / B28~29 외부 재설계 / B30 ARC-02 cap
- 감리 노트 저장 경로: `treatments/preprocess/jaebeol3se_loss_line/05_audits/block_021_030_audit_YYYY-MM-DD.md`

## 6. 주의: 다른 PC에서 이어받을 때 체크리스트

1. [ ] 이 문서 읽고 read order 순서대로 §1 전체 읽기
2. [ ] `treatments/jaebeol3se_loss_line_tr_block_005_draft.json` parse 확인 (boundary 25, len(blocks) 25)
3. [ ] live_status.md의 §2 current-root 경로와 §3 serialized boundary 일치 확인
4. [ ] 두 감리 노트 PASS 상태 확인 (1-10, 11-20)
5. [ ] quarantine 목록(§2) 숙지 — 절대 입력으로 쓰지 말 것
6. [ ] 첫 action: `tr_continue` Block 26 only (위 §5.1)
7. [ ] 한 번에 여러 블록 건드리지 말 것 — envelope 분리 원칙 (§3.4)
8. [ ] Block 30 저장 후 반드시 감리 envelope 1회 삽입 (tr_continue B31 금지)

## 7. 알려진 보수 작업 (여유 되면)

- **파일명 rename**: `treatments/jaebeol3se_loss_line_tr_block_005_draft.json` → 실제 boundary 반영한 suffix로 변경 가능 (예: `..._tr_block_070_draft.json`). 현재 suffix는 root_admit 시점 legacy, 기능상 문제 없음. rename 시 live_status §2 경로도 동시 수정 필요.
- **missing synthesis file**: `material_ssot/20_pitch/synthesis/investment_dokshik_jaebeol3se_working_synthesis.md` 복구는 현재 우선순위 낮음(canon anchor 정상 작동 중, 감리 2회 PASS). 원할 때 별도 envelope로 처리.

## 8. Hardstops (어떤 envelope에서도 절대 위반 금지)

- canon/phase0/work_guard/BI/governance/harness 본문 수정 금지 (단일 envelope 쓰기 스코프 위반)
- quarantine 목록 입력 사용 금지
- insider-trading 구조 (내부 데이터로 외부 포지션 근거) 금지
- asset-first reward narration (reward 첫 문장에 자본 수치) 금지
- 도현석 무능 캐리커처 금지
- 한 턴에 감리 + tr_continue 묶기 금지
- Block 030 저장 후 감리 없이 Block 031 진행 금지
- `Block 1~57 저장` 주장을 truth로 취급 금지
