# 10pair True Benchmark — Terminal 10 / Pair 10 Report

Date: 2026-04-07
Status: read-only true benchmark audit (re-graded against `production-pair-benchmark-spec-v1`)
Canonical Path: `docs/2026-04-07/10pair_true_benchmark_terminal10_pair10_report.md`
Parent Order: `docs/2026-04-07/10pair_true_benchmark_10terminal_opus_order.md`
Source Prompt: `docs/2026-04-07/10pair_true_benchmark_terminal10_pair10_prompt.md`
Prior Pass: evidence scouting pass (same file, prior revision) — ledger and defeat-reservation evidence reused below; scoring rebuilt from scratch under spec v1.

## Pair Identity

- pair id: `10`
- slug: `jaebeol3se_loss_line`
- family: `blockguide`
- BI: `bible/10_bi_jaebeol3se_loss_line.json` (424 lines, schema v2.0, last_updated 2026-04-06)
- TR: `treatments/10_jaebeol3se_loss_line_tr_block_070_draft.json` (6704 lines, 70 blocks)
- WG: `work_guards/10_jaebeol3se_loss_line.yaml`
- collision note: `work_guards/10_permit_window_grade9.yaml` is **not** the canonical pair 10 — confirmed against `docs/2026-04-07/01_10_canonical_pair_manifest.md`. This audit benchmarks `jaebeol3se_loss_line` only.
- one_line_truth (WG): 오너 일가에서 밀려 말석에 박힌 재벌 3세가 각 부서 숫자를 한 줄의 손실선으로 먼저 읽어, 회사 안 권한과 시장 바깥 수익을 함께 독식한다.

## Evidence Anchor Table

| Anchor | Source | Location | Substance |
| ---- | ---- | ---- | ---- |
| early promise | BI MetaInfo.grand_objective | `bible/10_bi_jaebeol3se_loss_line.json:17` | 말석 → 배석 → 서명 → 의결, 손실선으로 권한+외부 수익 동시 독식 |
| success_device | BI CommercialCode | `bible/10_bi_jaebeol3se_loss_line.json:36` | trigger set A (분리막 스크랩률 / 해상보험 갱신률 / 항만 슬롯 취소율) 한 장 표 |
| cider_point | BI CommercialCode | `bible/10_bi_jaebeol3se_loss_line.json:35` | 사촌 형 '관리 범위' 보고를 한 장 표로 뒤집고 18일 손실선을 먼저 그음 |
| CommercialCode equivalent | BI MasterBible.ProjectData.CommercialCode | `bible/10_bi_jaebeol3se_loss_line.json:34-38` | cider_point + success_device + attitude (비굴하지 않음·공개 데이터입니다) |
| one_line_truth | WG work_identity.one_line_truth | `work_guards/10_jaebeol3se_loss_line.yaml:5` | 같은 한 줄, BI 와 정합 |
| mandatory_scene_engines | WG | `work_guards/10_jaebeol3se_loss_line.yaml:55-58` | (1) 한 장 표 회의실 역전 (2) 공개 데이터로 숨은 리스크 적중 (3) 평가 수정 → 권한 보상 |
| evaluation_thresholds | WG protagonist_evaluation.evaluation_thresholds | `work_guards/10_jaebeol3se_loss_line.yaml:79-83` | 첫 사이다 = trigger set A 역전 / 18일 적중 → 배석·서명·열람 / 각 ARC 권한 1단계 / 반격 예약 없는 손해 금지 |
| custom_rules | WG custom_rules | `work_guards/10_jaebeol3se_loss_line.yaml:106-112` | 평가 → 권한 → 자본 절대 / dual-lane 출처 분리 / 위기는 우선순위 선택권 / 반격 예약 / 관제탑 |
| tracking_slots | WG tracking_slots | `work_guards/10_jaebeol3se_loss_line.yaml:50-54` | 저평가→고평가, 권한 축, 파일럿 운용금, 사촌 형 경계 수위 |
| forbidden_flattenings | WG | `work_guards/10_jaebeol3se_loss_line.yaml:34-49` | 회개물·자기연민·insider-trading·dual-lane 혼선·asset-first·사촌형 캐리커처·운빨 포장 |
| defeat_blocks (BI) | BI defeat_blocks | `bible/10_bi_jaebeol3se_loss_line.json:292-303` | 5, 10, 18, 24, 33, 39, 48, 54, 63, 67 |
| capital_curve | BI capital_curve | `bible/10_bi_jaebeol3se_loss_line.json:246-291` | 0 → 50 → 47 → 53 → 65 → 200 → 230 → 250 → 500 → 420 → 600 |

## P0 Hard Gates

**Strict evidence window: TR blocks 2~6 only (per spec §2.1).**

| # | Gate (spec §4.1) | Result | TR Anchor (within 2~6) | Substance |
| ---- | ---- | ---- | ---- | ---- |
| G1 | first-block visible cider | **PASS** | TR `Block 4` (`emotional_beat.type = "first_saida"`, intensity 9) | 도진우가 한 장 표를 꺼내 사촌 형 '관리 범위' 결론을 회의실에서 침묵 철회시킴. reader-countable 즉시 payback. |
| G2 | protagonist-only proof | **PASS** | TR `Block 4` solution + `genre_ext.leverage_used` | 손실선 = 말석 자리에서 세 부서 보고를 동시에 듣는 구조적 정보 우위 + 도진우의 손실 연쇄 판독 감각. 도현석은 같은 숫자를 따로 봤기 때문에 못 묶음 ("저건 쟤라서 가능했다" 명시적). |
| G3 | evaluation revision | **PASS** | TR `Block 4` reward + TR `Block 6` reward | B4: CFO 강태호 "이건 보고가 아니라 손실선을 먼저 그린 거네" / 회장 도경일 "이번 건은 네 선에서 먼저 잡아". B6: 회장 직보 주간 메모 라인 정식 개방 + emotional_beat `recognition_receipt`. weighted reevaluators (CFO + 회장). |
| G4 | visible reward token | **PASS** | TR `Block 6` reward + TR `Block 4` reward | B6 직보 주간 메모 라인 = blockguide 토큰 카탈로그의 `report line` (concrete + 권한축). B4 = `name call` (회장 인식 진입). 두 토큰 모두 2~6 윈도우 내. |
| G5 | block1 → block2 gate linkage | **PASS** | TR `Block 6` token → TR `Block 7` 결재선 등록 (downstream confirmation) | B6 직보 라인이라는 토큰이 같은 윈도우 안에서 발생, B7 에서 도진우 이름이 결재선에 처음 등록되며 권한 사다리 두 번째 칸을 자연스럽게 연다. B7+ 는 confirmation 으로만 인용, retro-fill 아님. |
| G6 | BI/TR early conversion alignment | **PASS** | TR `Block 1~3` vs BI CommercialCode + grand_objective | early promise (말석→배석→서명→의결): TR B1 말석 도련님 self-tag. success_device (trigger set A): TR B2 한 장 표로 명시 작성. cider_point (한 장 표 역전): trigger 자체가 B2 도진우 손에 들어와 있고 B3 발언 타이밍 대기로 살아 있음. 세 BI 자산 모두 TR 1~3 안에 visibly alive. |

**P0 종합: 6 / 6 PASS.** 윈도우 외 인용 없음. opening innocence rule (§4.3) 도 PASS — 도진우의 opening fall = `wrong seat / inherited bad frame` (오너 일가 결재선 밖 말석), 게으름·무책임·자기 붕괴 아님.

## Full-Block Cider Scan

**Method: each TR block individually marked `has_cider: true/false` per spec §2.3 — true 는 같은 블록 안에서 reader-countable payback 1건 이상 (token / weighted reevaluation / 보호 receipt / authority shift / recovery offset / next-card receipt).**

- total TR blocks: **70**
- no-cider blocks: **22**
- no-cider block numbers: **B1, B2, B3, B5, B8, B16, B18, B20, B22, B24, B28, B33, B35, B39, B41, B48, B50, B54, B56, B63, B65, B67**
- longest no-cider drought: **3 consecutive (B1 → B2 → B3, opening drought)**. 다른 모든 no-cider 블록은 isolated 1-block 구간이며 즉시 다음 블록에서 cider 가 회복된다.

### Window summary

| Window | No-cider blocks | Cider blocks | Notes |
| ---- | ---- | ---- | ---- |
| 1~10 | 5 (B1, B2, B3, B5, B8) | 5 (B4, B6, B7, B9, B10) | opening 3블록 drought + B5 defeat + B8 외부 레인 quiet-prep. cider spine: B4 first_saida → B6 직보 라인 → B7 결재선 → B9 18일 적중 → B10 회수 논의 차단. |
| 11~20 | 3 (B16, B18, B20) | 7 (B11~B15, B17, B19) | 권한 축 폭발 (배석 B11 / 열람 B12 / 서명 B13 / 자본 50억 B14). B18 보험 실무 한계 노출 defeat 지만 역지적 reservation. |
| 21~30 | 3 (B22, B24, B28) | 7 (B21, B23, B25~B27, B29, B30) | B24 외부 -3억 defeat → B25 내부 방어 실적 회수, B29 외부 두 번째 적중, B30 위원 추천. |
| 31~40 | 3 (B33, B35, B39) | 7 (B31, B32, B34, B36~B38, B40) | dual-lane separation 실전 구간. B39 insider 의심 → B40 사후 감사 통과 봉쇄. |
| 41~50 | 3 (B41, B48, B50) | 7 (B42~B47, B49) | B48 의결 집행 보류 defeat → B49 회장 합동 지시 회복. B44 200억 확대도 의결권 뒤. |
| 51~60 | 2 (B54, B56) | 8 (B51~B53, B55, B57~B60) | 가장 강한 구간. 전략적 분업 (B55), 세 축 동시 방어 (B58), 정식 펀드 500억 (B59), 관제탑 입구 (B60). |
| 61~70 | 3 (B63, B65, B67) | 7 (B61, B62, B64, B66, B68~B70) | B63 후계 후퇴 + B67 방어 비용 -80억 (둘 다 BI defeat_blocks 등재). B68 600억 최종 영수증 + 신용 등급 상향. |

### Defeat block × reservation 점검 (재사용)

BI `defeat_blocks` = 5, 10, 18, 24, 33, 39, 48, 54, 63, 67. 전 블록에서 같은 블록 또는 다음 1블록 안에 반격 예약이 명시되어 있다 — `반격 예약 없는 손해 금지` 룰 충족, 따라서 spec §6 의 "major defeat without next card in the same or next block → YELLOW ceiling" 룰은 미발동.

| Defeat | Reservation Anchor |
| ---- | ---- |
| B5 | 같은 블록 solution: 헤지안·선매입안 조용히 준비 → B7 정식 검토 안건 등록 |
| B10 | 같은 블록 reward: CFO "전체 순기여는 플러스" 공식 인정 → B11 배석권 |
| B18 | 같은 블록 reward: 도진우 역지적 → CFO 머릿속 잔존 → B19 갱신 12%→8.5% |
| B24 | 같은 블록 명시 reservation: "Block 25에서 같은 기간 내부 손실 방어 실적으로 순기여" |
| B33 | B34 dual-lane separation 실전 증명 |
| B39 | B40 공개 데이터 출처 검증 통과로 의심 봉쇄 |
| B48 | B49 회장 합동 지시 / 역할 분담 공식 인정 |
| B54 | B55 전략적 분업 공식 합의 |
| B63 | B64 손실선 먼저 읽음 + 회장 긴급 회의 첫 의제 |
| B67 | B68 600억 최종 영수증 + 신용 등급 상향 |

## Active Cap Rules

| Spec §6 Cap Rule | Status | Anchor |
| ---- | ---- | ---- |
| no visible cider inside block 1 (`TR 2~6` window) | not active | G1 PASS at TR B4 |
| first concrete token lands at TR block 7+ | not active | G4 token at TR B6 |
| **any no-cider block in the full-block cider scan → YELLOW ceiling** | **ACTIVE — primary cap** | 22 no-cider blocks (B1, B2, B3, B5, B8, B16, B18, B20, B22, B24, B28, B33, B35, B39, B41, B48, B50, B54, B56, B63, B65, B67) |
| rewardless pain blocks 2 in a row → GREEN ceiling | not active | B1~B3 opening drought 의 성격은 no-cider / setup / wait (B1 humiliation+observation, B2 한 장 표 quiet-prep, B3 발언 타이밍 wait) 이며 spec §6 의 `rewardless pain blocks` 정의 (지속적 고통·굴욕 누적 블록) 에 해당하지 않는다. ledger 의 no-cider 22블록 안에 포함되어 상위 YELLOW cap 에서 이미 다뤄짐. |
| no-cider drought 6+ blocks → YELLOW ceiling | not active | longest drought = 3 (B1~B3) |
| major defeat without next card in same/next block → YELLOW ceiling | not active | all 10 BI defeat_blocks have explicit reservations (table above) |
| BI is summary echo only → GREEN ceiling | not active | BI seeds + opponent_transition_plan + capital_curve materially sharpen TR |
| early reward asset-only → GREEN ceiling | not active | B6 early reward = 직보 라인 (status/authority), 자본은 B14 |
| wins rely on stupid opposition → GREEN ceiling | not active | 도현석 era-valid resistance, 4-phase 전이 |
| domain texture generic → GREEN ceiling | not active | dual-lane separation + 보험 갱신률·스크랩률·슬롯 취소율 + 직보 라인은 blockguide-specific |
| protagonist passive across key arc → YELLOW ceiling | not active | 도진우는 매 ARC 진입함수에서 self-driven trigger 감지 |

**Single binding cap (primary, sole): `any no-cider block → YELLOW ceiling`** (spec §6, line 176; restated §8.3). 활성 cap 은 이 한 건뿐이며, opening drought B1~B3 는 보조 리스크로만 기록되고 ledger 의 22 no-cider blocks 안에 흡수된다. cap 의 근거는 ledger 전체이지 opening drought 자체가 아니다.

## P1 Score Table

Spec §5 — each axis `0 / 1 / 2`, total 20.

| # | Axis | Score | Anchor / Rationale |
| ---- | ---- | ---- | ---- |
| 1 | protagonist innocence | **2** | opening fall = 오너 일가 결재선 밖 말석 (wrong seat / inherited bad frame). 도진우의 게으름·무책임·자기 붕괴 아님. clearly defendable. |
| 2 | protagonist-only proof clarity | **2** | 손실선 = 말석 자리의 구조적 정보 우위 + 손실 연쇄 판독 감각. 도현석이 같은 숫자를 따로 봤기 때문에 못 묶었다는 것이 B3·B4·B23 본문에서 명시. unmistakably protagonist-only. |
| 3 | evaluation revision visibility | **2** | B4 CFO + 회장 동시 reweight → B6 직보 라인 정식 개방 → B9 평가 한 칸 더 상승 ("손실선을 먼저 그린 사람" → "손실을 실제로 묶은 사람"). explicit + weighted (CFO·회장 무게). |
| 4 | visible reward token strength | **2** | B6 직보 주간 메모 라인 (concrete report line) + B11~B13 배석/열람/서명 권한축 토큰. blockguide 카탈로그 상위 토큰 4종 동시. emotional only 가 아니라 force-bearing. |
| 5 | block1 → block2 linkage | **2** | B6 직보 토큰 → B7 결재선 등록 → B9 적중 → B11 배석권. clean next-gate opening, B7+ 는 confirmation 으로만 작동. |
| 6 | rational opposition | **2** | 도현석 4-phase 전이 (`opponent_transition_plan` Phase 1~4: 무시→경계→본격 대응→전략적 공존). incentive-driven, era-valid ("이전 시대의 정답을 믿은 사람"), 캐리커처 회피 명시. |
| 7 | domain truth density | **2** | 손실선 어휘 = 보험 갱신률·스크랩률·슬롯 취소율·헤지·선매입·갱신안·클레임 준비금·dual-lane separation. blockguide 외 다른 lane 으로 swap 불가. |
| 8 | repeatable loop clarity | **2** | 감지 → 한 장 표 → 회의실 역전 → 평가 수정 → 권한 영수증 → (선택) 자본 → 다음 trigger 감지. 루프가 B4 / B23 / B32 / B42 / B57 에서 가시적으로 반복. |
| 9 | BI amplification power | **2** | BI = 5 seeds (모두 payoff_block 명시), 5 opponent_transition phases, 11 capital checkpoints, 10 defeat blocks, 6 npc_timeline arcs, ContaminationGuard 10항. summary echo 가 아니라 TR 의 약속을 sharpen. |
| 10 | blockwise cider continuity | **0** | 22 no-cider blocks. spec axis-0 정의 ("one or more no-cider blocks") 에 정확히 해당. |

**Total P1 score: 18 / 20.**

- score band per spec §8: `17~20` 은 GREENPLUS 후보 구간이지만, axis 10 = 0 + cap rule (any no-cider block) 이 동시에 발동하므로 score 만으로는 GREENPLUS 도달 불가.

## Provisional Grade

- raw P1 score: **18 / 20**
- active primary cap: **`any no-cider block → YELLOW ceiling`** (spec §6 line 176, §8.3)
- subordinate risk: opening drought B1~B3 (rewardless pain 2-in-a-row 에 해당하는 GREEN-ceiling 사유; 상위 YELLOW cap 에 흡수됨)
- **final provisional grade: `YELLOW`**
- ceiling 유지 조건: full-block cider scan 의 no-cider block count 가 **0** 이 될 때까지 본 페어는 YELLOW ceiling 을 유지한다. 22 → 0 으로 떨어지지 않는 한 score 가 18/20 이든 20/20 이든 grade 는 GREEN/GREENPLUS 로 올라가지 않는다. 부분 수리 (예: opening drought 만 압축) 로는 cap 이 해제되지 않는다 — spec §6 의 룰은 "any" 다.

## Top 3 Repair Units

> repair scope = bounded top 3 (spec §8.3). 단, 어떤 단일 unit 도 cap 을 단독으로 해제하지 않는다 — cap 해제는 ledger 전체 22 → 0 도달 시점에서만 일어난다. 아래 3 unit 는 그 도달까지의 우선순위 묶음이다.

1. **Quiet-prep 8블록 micro-cider 삽입 (B8 / B20 / B28 / B35 / B41 / B50 / B56 / B65).** 이 8개는 모두 reward = "아직 없다" 의 조용한 준비 블록이며, 정의상 cap 사유에 직접 해당하지만 작품 구조상 reservation 자체는 이미 깔려 있다. 각 블록 reward 한 줄에 spec §2.3 의 cider 정의 6종 중 가장 가벼운 것 (관찰자 시선 micro-recognition / next-card receipt / authority access flicker) 1비트를 추가한다 — 권한 사다리·자본 곡선·dual-lane separation 을 건드리지 않으면서 ledger 에서 8건 즉시 차감. cap 해제 진척도: 22 → 14.
2. **Defeat-block reservation 가시화 (B5 / B22 / B33 / B54).** 이 4개는 reservation 이 다음 블록에 있지만 같은 블록 안에서는 reader 가 receipt 를 체감할 수 없는 구조다. 같은 블록 closing beat 으로 "다음 카드의 첫 두 줄" / 노트 닫힘 / 조용한 1초 결심 / 옆자리 관찰자의 반 박자 늦은 메모 를 1비트 추가하여 spec §2.3 의 `next-card receipt the reader can feel now` 항을 만족시킨다. ledger 에서 4건 차감. cap 해제 진척도: 14 → 10.
3. **Opening 1~3 + 중반 잔여 10블록 ledger sweep (B1 / B2 / B3 / B16 / B18 / B24 / B39 / B48 / B63 / B67).** 보조 리스크로 기록된 opening drought 를 포함, 잔여 10개의 no-cider 블록을 한 패스로 sweep 한다. opening (B1~B3) 은 first_saida 를 B3 로 1블록 당기거나 B1~B3 각각에 micro-recognition 을 심어 drought 를 0~1블록으로 압축. 중반 7블록 은 이미 reservation 이 명시된 블록들이라 receipt 가시화 1비트씩이면 충분. 이 unit 가 끝나는 시점에 ledger 가 22 → 0 에 도달하고, cap 해제와 grade 재산정이 가능해진다. 그 전까지는 ceiling 이 유지된다.

## Concise Rationale

P0 6 gates 는 strict window TR 2~6 안에서 모두 PASS — first-block cider (B4 first_saida), protagonist-only proof, evaluation revision (CFO + 회장), visible reward token (B6 직보 라인 = report line), block1→block2 linkage (B6→B7→B11), BI/TR early conversion alignment (success_device·cider_point seed·early promise 모두 TR 1~3 안에 alive). opening innocence rule 도 통과한다 — 도진우의 fall 은 wrong seat / inherited bad frame.

P1 10 axes 중 9개가 2점, 1개 (blockwise cider continuity) 가 0점으로 18/20. score 만 보면 GREENPLUS 후보 구간이지만, spec §6 의 `any no-cider block → YELLOW ceiling` 룰이 ledger 전체 22개 no-cider 블록에 의해 발동하여 grade 를 YELLOW 로 cap 한다. 이 cap 은 점수와 무관하게 작동하며, opening drought B1~B3 는 그 22블록 ledger 의 일부이자 보조 리스크일 뿐 cap 의 일차 근거가 아니다. 일차 근거는 ledger 자체다.

따라서 본 페어는 ledger 의 no-cider count 가 **0** 이 될 때까지 YELLOW ceiling 을 유지한다. 부분 수리 — opening 만 정리하거나 quiet-prep 만 정리 — 로는 cap 이 풀리지 않는다. spec §6 의 룰은 "any" 이며, 전수 sweep 만이 cap 을 해제할 수 있다. underlying discipline (dual-lane separation, 평가→권한→자본 순서, 사촌형 합리적 견제, defeat 반격 예약, BI amplification, repeatable loop) 은 모두 GREENPLUS-tier 로 살아 있지만, grade 는 그것과 별개로 ledger 가 0 에 도달할 때까지 YELLOW 다.

본 보고서는 단일 페어 read-only 감리이며, full-wave surgery 는 제안하지 않는다. 수리 단위는 위 top 3 묶음으로 한정되고, 그 이상은 별도 오더가 필요하다.

read-only true benchmark audit complete; no pair files mutated
