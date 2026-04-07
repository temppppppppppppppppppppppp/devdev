# 10-Pair Meta Cleanup — Terminal 02 / Pair 02 Execution Audit

- Date: 2026-04-07
- Status: final
- Document Type: post-execution audit note (single pair)
- Canonical Path: `docs/2026-04-07/10pair_meta_cleanup_terminal02_pair02_execution_audit.md`
- Parent Order: `docs/2026-04-07/10pair_tr_bi_legacy_meta_cleanup_execution_order.md`
- Survey Source: `docs/2026-04-07/10pair_meta_cleanup_terminal02_pair02.md`
- Baseline Commit: `5c71b81a36ab2cbae824c630bb63219354b913a8`
- Touched Pair: `02 — chaebol_allowance_zero` (`blockguide` family)

## 1. Scope Realized

Bounded narrative meta-cleanup on the live pair `02` artifacts only:

- `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json`
- `bible/02_bi_chaebol_allowance_zero.json`

Tranches executed (per parent execution order):

- Tranche 1: shared label cleanup
- Tranche 2: shared prose normalization
- Tranche 3: BI-only tail cleanup + BOM strip

No `docs/temp/` mutation, no system-track touches, no other pair files touched.

## 2. Patch Surfaces (mirrored TR.blocks ⇄ BI.MasterBible.plot_roadmap)

| Field | Action |
| --- | --- |
| `genre_ext.section_rotation` | strip leading `ARC-0X - `, `ARC-0X exit - ` (→ `아크 종료 — …`), `ARC-0X endgame - ` (→ `엔드게임 — …`) |
| `genre_ext.capital_delta` | drop trailing ` (ARC-0X)` and ` + ARC-0X 입장권` |
| `genre_ext.profit_loss` | drop trailing ` (ARC-0X)` and ` + ARC-0X 입장권` |
| `foreshadow[*]` | extract `Block N` numbers into `foreshadow_targets`; rewrite prose with `후속 분기` / `후속 아크`; collapse ARC chains |
| `callback[*].note` | rewrite prose to `선행 분기`; populate/extend `callback_sources` from existing `target_block` ints + any extra `Block N` references in note prose |
| `content.context` / `content.solution` / `content.reward` / `content.event_villain` | drop inline `(Block N)` parens; replace `Block N` with `해당 분기`; replace `ARC-0X` with `이번 아크` |
| `stakes` | same as `content.*` |
| `power_shift.protagonist` / `power_shift.antagonist` | same prose cleaner |
| `regression_ext.butterfly_effect.ripple_effect` | same prose cleaner |
| `regression_ext.death_flag.avoided` | same prose cleaner |
| `regression_ext.future_prep.target_event` | same prose cleaner |
| `regression_ext.regression_hint.slip_up` | same prose cleaner |

## 3. Patch Surfaces (BI-only)

| Field | Action |
| --- | --- |
| `MasterBible.WorldState.opponent_transition_plan[*].phase` | strip leading `Phase N: ` (`Phase 1: 초기 감시·차단` → `초기 감시·차단`) |
| `MasterBible.WorldState.expansion_order_locked[*]` | drop bare ` (ARC-0X)` and inner `ARC-0X ` prefixes; preserve descriptive content (`급식 (ARC-01 장례 밥차 + ARC-03 공장 구내식당)` → `급식 (장례 밥차 + 공장 구내식당)`) |
| `MasterBible.AssetLibrary.BusinessAxis.expansion_order[*]` | same as `expansion_order_locked` |
| `MasterBible.AssetLibrary.CapitalCurve[*].event` | replace leading `ARC-0X exit — ` with `아크 종료 — `; arc identity is still derivable from sibling `block` index |
| `MasterBible.AssetLibrary.ArcSheets[*].operational_power_gain[*]` | replace `(ARC-0X 입장권)` parenthetical with `(다음 아크 입장권)` |
| `MasterBible.AssetLibrary.OperationalPowerByArc[*].operational_power_gain[*]` | same as ArcSheets |
| `MasterBible.Defeats[*].summary` | particle-aware ARC replacement (`ARC-0X과` → `이번 아크와`, `ARC-0X` → `이번 아크`) |
| `MasterBible.SingleHeirPolicy.final_resolution` | `Block 70` → `최종 분기` (final-block resolution prose) |

BOM: BI's leading UTF-8 BOM stripped during write (file is now strict UTF-8 without BOM).

## 4. Allowed Structural Metadata Preserved

Confirmed unchanged after the patch:

- `TR.blocks[*].block_id` — still `Block 1 .. Block 70`
- `TR.blocks[*].block_no` — still 1..70
- `BI.MasterBible.plot_roadmap[*].block_id` / `block_no` — same
- `BI.MasterBible.AssetLibrary.ArcSheets[*].arc_id` — `ARC-01 .. ARC-07`
- `BI.MasterBible.AssetLibrary.OperationalPowerByArc[*].arc_id` — same
- `BI.MasterBible.AssetLibrary.CapitalCurve[*].block` — still int
- `BI.MasterBible.WorldState.opponent_transition_plan[*].entry_block` / `transition_block` — still int
- `BI.MasterBible.AssetLibrary.ForeshadowMap[*].seed_block` / `hint_blocks` / `payoff_block` — still int / list of int
- `BI.MasterBible.Defeats[*].block` — still int
- `BI.MasterBible.WorldState.opponent_transition_plan[*].main_actors` / `block_range` — untouched (allowed structural)
- `evolution`-keyed strings — none present in pair 02 (no false positive risk)

New structural fields populated (per the execution order's allowed list):

- `TR.blocks[*].foreshadow_targets`: per-block list of `int` block numbers extracted from prior foreshadow prose (was `null`)
- `TR.blocks[*].callback_sources`: per-block list of `int` block numbers consolidated from prior `callback[*].target_block` and any extra `Block N` references in note prose (was `null`)
- Same population mirrored on `BI.MasterBible.plot_roadmap[*]`

## 5. Borderline Policy Calls

Three explicit calls were made during execution:

### 5.1 `TR._draft_status` left untouched

Field value: `"ARC-01~07 complete (blocks 1-70). TR draft full."`

Reasoning: this is a TR-root admin/manifest field tracking draft progress. The execution order's Tranche 3 §3.3 carve-out for pair `08` explicitly excludes `_creation_note` and `_schema_description` as out-of-scope administrative metadata. By analogy, `_draft_status` is the same kind of administrative manifest field. Touching it would risk drifting it out of sync with whoever generates draft-status strings. Left as-is.

Validation impact: a single forbidden-pattern hit remains in `TR._draft_status`. This is intentional and is not a touched human-readable narrative field, so it does not violate the order's §8 acceptance rule (`zero hits required in touched human-readable fields`).

### 5.2 `MasterBible.LongArcForeshadowPayoffs[*]` left untouched

This top-level structure has only two string keys per entry: `seed` and `payoff`. Both contain `Block N` tokens (e.g., `seed: "유언장 7항 (Block 1)"`, `payoff: "Block 63 ... + Block 68 ... + Block 70 ..."`).

Reasoning: these strings are the **authoritative structural carrier** of the seed→payoff block mapping for this pair. The structure has no parallel `seed_blocks` / `payoff_blocks` int-list keys, so the `Block N` tokens **are** the data, not decoration. Per the execution order's §9 stop gate (`a field thought to be human-readable is actually the authoritative structural carrier`), this surface was not rewritten. A future structural pass could promote these to typed int lists; that is out of scope for narrative cleanup.

Note: a parallel structure `MasterBible.AssetLibrary.ForeshadowMap` already uses proper structural keys (`seed_block`, `hint_blocks`, `payoff_block`, `payoff_meaning`) for the same kind of data, so the canonical structural carrier already exists in BI.

### 5.3 Foreshadow / callback prose neutral phrasing

The prose substitution uses three neutral phrases corresponding to temporal direction:

- `후속 분기` for forward references in `foreshadow[*]`
- `선행 분기` for backward references in `callback[*].note`
- `해당 분기` for inline `content.*` / `stakes` references
- `이번 아크` / `후속 아크` / `해당 아크` for ARC-token chains

Particle agreement is enforced (vowel-ending phrase: `는`/`를`/`로`/`와`/`가`). Pair-truth precision is preserved by the structural anchors (`foreshadow_targets`, `callback_sources`, `target_block`), not by the prose. Some sentences read more abstract than the original (e.g., a multi-block parenthetical `(Block 12, Block 63)` collapses into the surrounding sentence), but no causal relation or callback target is lost.

## 6. Validation

Per the execution order's §8 contract, after the patch:

1. **Byte-level UTF-8 read-back**: both files re-read as raw bytes; TR has no BOM (393,764 bytes), BI no BOM (502,053 bytes).
2. **JSON parse pass**: both files parse cleanly as `dict`. TR has 70 blocks; BI `MasterBible.plot_roadmap` has 70 entries.
3. **Forbidden-pattern grep on touched human-readable fields**: zero hits, except the one intentional borderline carve-out (`TR._draft_status`).
4. **Allowed structural fields still numeric**: confirmed (see §4).
5. **Pair-truth integrity**: untouched. `_work_id` matches across TR/BI; protagonist, arc count (7), block count (70), expansion order, and CFO/family conflict architecture all unchanged.
6. **TR/BI mirror parity** for narrative fields: maintained — both files received identical `clean_block` transforms applied in the same order to mirrored objects.

## 7. Stop Gates Status

Per the execution order's §9, no stop gate was tripped:

- UTF-8 read-back agrees with editor preview (BI BOM removed, payload bytes intact)
- no wording fix changed pair truth
- one field (`LongArcForeshadowPayoffs`) was identified as the authoritative structural carrier and skipped (gate respected, not violated)
- pair `02` is not pair `10`, so the late-block stability gate does not apply
- pair `02` is not pair `09`, so the `evolution` gate does not apply

## 8. Deliverables

- modified `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json` (BOM-free, indent=2 UTF-8)
- modified `bible/02_bi_chaebol_allowance_zero.json` (BOM-free, indent=2 UTF-8, trailing newline added)
- helper script: `docs/2026-04-07/_pair02_cleanup.py` (the deterministic transform used; preserved alongside this audit for review)
- this audit note

## 9. Pair-Level Outcome

- Pair `02`: **completed** (Tranches 1, 2, 3 all applied; one borderline carve-out documented)
- Deferred items: none for pair `02`
- Remaining work for the broader 10-pair wave: pair `02` is one terminal of the 10-terminal split; other pairs are owned by their own terminals per the parent order.

## 10. 정합성 후속 수정 (post-cleanup consistency fix)

직전 클린업 직후 사용자 요청으로 수행한 종합 정합성 점검·수정 결과.

### 10.1 점검 범위

- **TR ⇔ BI 미러 파리티** (블록 단위 모든 키 비교)
- **개별 정합성**: `block_id ↔ block_no ↔ index`, `arc_id` 일관성, `callback target_block ⊆ callback_sources`, `foreshadow_targets` 방향성·범위
- **Cross-cut**: `ArcSheets ↔ block_slots`, `time_window ↔ time_span`, `front_sector_by_arc ↔ ArcSheets.front_sectors`, `ForeshadowMap ↔ blocks foreshadow_targets`, `LongArcForeshadowPayoffs ↔ blocks foreshadow_targets`, `KeyNPCs ↔ Partners ↔ relationship_delta`, NPC 첫 등장 vs `ArcSheets.new_npcs`, 회사·그룹 명칭 변형, `LocationPool` / `DealTypeRotation` 길이, `CapitalCurve` / `Defeats` / `opponent_transition_plan` 블록 참조 유효성
- **클린업 부산물 검출**: 잔여 `phrase + ·N` / `~N` / `Block N` 토큰

### 10.2 수정 항목

#### A. 클린업 부산물 — 잔여 multi-ref 패턴 13건 (TR + BI 미러)

직전 cleanup의 정규식이 `Block N·M` / `Block N~M` 같은 다중 인접 참조에서 첫 토큰만 치환하고 뒤의 `·M` / `~M` 또는 인접 단어를 고립 상태로 남긴 경우. baseline (HEAD) 대조로 원본 토큰을 정확히 확인한 뒤, 케이스별 명시적 string 매핑으로 정밀 치환:

| 블록 | 필드 | baseline 원본 | 수정 후 |
|---|---|---|---|
| B7 | `stakes` | `복제된다(Block 11~12). 반장을` | `복제된다. 반장을` |
| B12 | `content.solution` | `한유림(Block 2·6)에게` | `한유림에게` |
| B15 | `content.solution` | `Block 8·14 모델을 합성해` | `앞선 청소팀·세제 통제 모델을 합성해` |
| B18 | `foreshadow[0]` | `Block 41~50 정산 시스템 장악의 기본 설계` | `정산 시스템 장악 단계의 기본 설계` |
| B47 | `content.context` | `Block 7 ... → Block 17·32 ... → Block 18 ...` | `장례식장 세탁실 출입카드 기록 → 배정호 세탁 공장 → 영수증 실시간 분리 설계안까지` |
| B48 | `content.context` | `Block 43 14분 주기 + Block 47 출입-정산 연동` | `14분 주기 + 출입-정산 연동` |
| B49 | `content.solution` | `Block 43 14분 주기 통제 + Block 47 출입 연동` | `14분 주기 통제 + 출입 연동` |
| B50 | `content.solution` | `(1) Block 12·44 유령업체·4417 장부` | `(1) 유령업체·4417 장부` |
| B57 | `content.context` | `공장 급식(Block 28·29) 매출채권` | `공장 급식 매출채권` |
| B61 | `foreshadow[0]` | `Block 62·68 표준계약서의 원형` | `표준계약서의 원형` |
| B63 | `content.context` | `유령업체 장부(Block 12·44)를 맞물려` | `유령업체 장부를 맞물려` |
| B64 | `content.solution` | `Block 56·60 공급망 대출 원장을 즉시 가동` | `공급망 대출 원장을 즉시 가동` |
| B67 | `foreshadow[0]` | `Block 68·69·70의 직접 무기` | `엔드게임의 직접 무기` |

**정보 손실 평가**: 12건은 인접 자연어 단서(노드 이름, 단계명)가 이미 충분해 의미 보존. 1건(B15 합성 모델)은 자연어로 더 풍부해짐. 0건이 인과 관계나 callback 타깃을 잃지 않음.

#### B. `LongArcForeshadowPayoffs` ↔ blocks `foreshadow_targets` 5건 머지 (총 9개 number 추가)

LAF가 명시한 다중 페이오프 블록 numbers 중 해당 seed 블록의 `foreshadow_targets`에 빠져 있던 항목을 머지(중복 제외, 기존 순서 보존, 추가는 append):

| seed block | merge 전 ft | merge 후 ft | 추가된 |
|---|---|---|---|
| B1 | `[63]` | `[63, 68, 70]` | `+68, +70` |
| B12 | `[63, 20]` | `[63, 20, 16, 25, 35]` | `+16, +25, +35` |
| B28 | `[46, 43]` | `[46, 43, 49]` | `+49` |
| B44 | `[50]` | `[50, 63]` | `+63` |
| B56 | `[67]` | `[67, 60, 69]` | `+60, +69` |

본문 미터치, 정보 무손실, foreshadow_targets 방향성(forward) 모두 보존.

### 10.3 미수정 항목 (사유)

- **D. ArcSheets ARC-01 `main_opponents` 에 윤석진 미포함**: B4 첫 등장은 보조 적대(`event_villain`의 꽃값 사후 정산 명분), 본격 주적 부상은 ARC-02. 작가 의도로 판단. §3.3 `redesign arcs` 금지.
- **E. 백도현 B17 첫 언급**: 본문에 `사모펀드(백도현 라인 전신)`로 명시. 본인이 아닌 라인 전신. 본격 등장은 ARC-06. 미수정.
- **F. `protagonist_config.name = None`**: pair 01, pair 05도 None — 페어별 schema variance. §3.3 `normalize unrelated schema naming` 금지. `start_point.context`에 "윤재이(26세)" 명시되어 정보 자체는 보존.
- **G. `LongArcForeshadowPayoffs` (8) ↔ `ForeshadowMap` (6) 부분 동기화**: BI 안에 두 카드 시스템 공존 — 설계 차원 redundancy. §3.3 `redesign arcs` 및 §9 stop gate (authoritative structural carrier). 본 cleanup의 책임 외.
- **H. `LocationPool` (69) ≠ blocks(70)**: 검사 결과 LocationPool은 per-block index가 아닌 단순 location 풀. 인덱스가 블록 번호와 무관(예: LocationPool[0]="CFO 집무실" vs B1.location="윤성가 장례식장 운영실"). 블록 location은 `block.location.{place,type}`에 별도 저장. **drift 아님**.
- **NPC roster, 회사명 변형, callback target/source, ArcSheets/CapitalCurve/Defeats/opponent_transition_plan 블록 참조, time_window/time_span, ArcSheets.front_sectors==front_sector_by_arc.front, ForeshadowMap seed/payoff inclusion, KeyNPCs/Partners 세트, relationship_delta unknown counterparty**: 모두 사전 점검 통과. 수정 불필요.

### 10.4 검증 결과 (재확인)

| 검사 | 결과 |
|---|---|
| TR ⇔ BI 미러 파리티 (블록 단위 모든 키 비교) | **0 차이** |
| 잔여 multi-ref 패턴 (`phrase·N` / `phrase~N` / `phrase\d`) | **0건** |
| 잔여 금지 메타 토큰 (carve-out 제외) | **TR 0 / BI 0** |
| `LongArcForeshadowPayoffs` payoffs ⊆ blocks `foreshadow_targets` | **통과 (누락 0)** |
| `callback[*].target_block ⊆ callback_sources` | **통과** |
| `foreshadow_targets` forward 방향성 (1≤n≤70, n>block_no) | **통과** |
| `callback_sources` backward 방향성 (1≤n≤70, n<block_no) | **통과** |
| JSON parse + UTF-8 + BOM 없음 | **TR 393,637 bytes / BI 501,944 bytes** |
| pair-truth (`_work_id`, 70 blocks, 7 arcs) | **무손상** |

### 10.5 추가 산출물

- `docs/2026-04-07/_pair02_consistency_fix.py` — 정합성 후속 수정 헬퍼 스크립트 (명시적 string 매핑 + LAF→ft 머지)

### 10.6 최종 상태

- Pair `02` narrative meta cleanup + 정합성 후속 수정 **모두 완료**.
- 클린업이 만든 drift: **0건**.
- pre-existing structural drift (LAF↔FM 부분 동기화): **1건 잔존, audit 문서화만, redesign 금지**.
- 실전 사용 가능 상태.

## 11. 본문 통독 audit + Prose ship-readiness 수정

§10까지는 **구조적 무결성**까지만 검증했다. 사용자 요청으로 70개 블록 본문을 arc 단위로 통독해 **모순/사실 불일치/표현 모호성**을 추가 점검하고 수정했다.

### 11.1 통독 audit 범위

- **자동 검사**: 시간 stamp 단조성, 자본 chain 단조성·연결, NPC 등장 분포·갭, 회사명/엔티티 변형, 핵심 사실 (숫자·비율·인원) 일관성, callback note ↔ source 정합, foreshadow_targets ↔ ForeshadowMap inclusion
- **수동 통독**: ARC-01 (B1~B10) 본문 6개 필드(context/event_villain/solution/reward/stakes/foreshadow/callback) 전수, ARC-02 (B11~B20) 동일, ARC-03~07은 spot-check + 자동 검사 결합

### 11.2 검출된 진짜 모순 — 수정

#### M-1. **B40 ↔ B59 ↔ B70 매출 합계 수치 일관성 위반** (baseline 부터 존재)

| 블록 | baseline | 수정 후 |
|---|---|---|
| B40 reward | `월 반복매출 합계 약 12.8억/월 (연환산 154억 포지션)` | (그대로 — ARC-04 시점 누적치) |
| B59 reward | `월 반복매출 합계 약 8.3억/월 추가 (연환산 100억 규모)` | (그대로) |
| **B70 reward** | `최종 포지션: 연환산 반복 현금흐름 약 154억` | **`약 254억`** |
| **B70 profit_loss** | `연환산 154억 포지션 + 가문 일상 지배권` | **`연환산 254억 포지션 + 가문 일상 지배권`** |

**원인**: baseline 작가/생성 도구가 B40 라벨(154억)을 B70 최종 라벨에 그대로 반복 사용하면서 ARC-06 추가분(+100억)을 잊은 것. 자본 chain(B40 19.2 → B70 100억+)은 깨끗하게 일관해서 추가 매출 자체는 발생했음. 누적 합계 라벨링만 잘못. 154 + 100 = 254로 복원.

**중요**: 이 모순은 cleanup 부산물이 아니라 **baseline부터 존재**하던 작가/생성 도구의 수치 오류. cleanup이 만든 모순이 아님.

#### M-2. **B16 reward 표현 모순** (자본 chain 가독성 저해)

baseline:
- reward: `자본은 감소 없음(0.5억 방어 비용만 지출)`
- capital_delta: `-0.5억 (방어비)`

본문 reward와 구조 필드 capital_delta가 표현 충돌. "감소 없음"은 본업 흐름 기준이고 -0.5억은 실제 지출이라는 작가 의도지만, 자본 chain 검사기와 독자 모두 혼동. **`자본 2.2억 → 1.7억 (방어비 0.5억)`**으로 명시화.

검증: B15 after 2.2 → B16 1.7 → B17 before 1.7. chain 일관 ✓

### 11.3 표현 정밀화 — 단일 Block ref 자연어 치환 (target 필드 80건)

직전 cleanup이 단일 `Block N` ref를 일률 `해당 분기 X` / `이번 아크` 같은 generic phrase로 치환하면서 **시간 방향성과 구체성**을 잃은 80건. 본문 의미는 보존됐지만 prose 품질 저하.

**적용 범위**: `content.{context, solution, reward, event_villain}`, `stakes`, `power_shift.{protagonist, antagonist}` (target 필드)

**제외**: `foreshadow[*]`, `callback[*].note` — 이미 `foreshadow_targets`/`callback_sources` 구조 캐리어가 있고 본문은 generic phrase로 충분.

**정밀화 룰** (baseline에서 시간 방향 판단):
- `Block N`, N < 현재 → **`앞 블록`**
- `Block N`, N > 현재 → **`이후 블록`**
- `Block N`, N == 현재 → **`이번 블록`**
- 한국어 조사 자동 일치 (자음 종결 `블록`: 은/을/으로/과/이)
- `(Block N X)` paren 패턴: backward → `(앞 블록의 X)`, forward → `(이후 X)`, self → `(X)`
- `(Block N)` paren 단독: 통째 삭제
- `ARC-NN`: 같은 arc → `이번 아크`, 미래 arc → `다음 아크`, 과거 arc → `이전 아크`
- ARC chains `ARC-N·M`: 첫 arc 기준 동일 룰

### 11.4 Multi-ref 11건 명시 매핑 (이전 §10 매핑 + B49 추가)

§10에서 처리한 12건 multi-ref + B49 (`Block 43 14분 주기 + Block 47 출입 연동`) 1건을 fix2 스크립트에 통합. baseline에서 다시 시작하므로 §10의 별도 patch도 흡수.

### 11.5 B10 arc-exit 패턴 통일

다른 5개 arc-exit 블록(B20/30/40/50/60)은 모두 `이번 아크 exit — X 입장권 확보` 패턴인데 B10만 `이번 아크 입장권 확보`로 다름.

수정: B10 reward → `이번 아크 exit — 호텔 백오브하우스(린넨실) 진입 입장권 확보.`

### 11.6 검증 결과 (재확인)

| 검사 | 결과 |
|---|---|
| TR ⇔ BI 미러 파리티 | **0 차이** |
| 잔여 금지 메타 토큰 (carve-out 제외) | **TR 0 / BI 0** |
| 잔여 multi-ref 패턴 | **0건** |
| **자본 chain 단조성·연결 (B1~B70)** | **0 위반** (B16 수정 반영) |
| **시간 stamp 단조성 (B1~B70)** | **0 위반** |
| LAF payoffs ⊆ blocks foreshadow_targets | **통과** |
| callback target_block ⊆ callback_sources | **통과** |
| foreshadow_targets forward 방향성 | **통과** |
| callback_sources backward 방향성 | **통과** |
| **B40 ↔ B59 ↔ B70 매출 합계 정합성** | **통과** (M-1 수정) |
| 회사명·NPC 이름·핵심 사실 일관성 | 통과 |
| JSON parse + UTF-8 + BOM 없음 | TR 393,577 / BI 501,884 bytes |

### 11.7 통독 audit에서 모순 아닌 것으로 판정한 항목

- **F-1**. B70 자본 100억 vs 유언장 100억: 본문이 명시적으로 분리(`주식 평가액이 아니라 매일 돌아가는 현금흐름`). 자본(운영) ≠ 순자산(주식 기준). 일관.
- **F-2**. 한유림 B28→B49 21블록 갭: 한유림은 백오피스 시스템 설계자, 작가가 ARC-04 팬데믹 동안 정채린·문태준에게 현장 액션 위임한 것으로 해석. 모순 아닌 작가 의도.
- **F-3**. 협력사 30곳 → 50곳 확장 시퀀스 (B48→B56→B60→B64→B69): B60에서 명시적 30→50 확장. 일관.
- **F-4**. NPC 등장 갭 (배정호·최문갑·정채린·문태준·민가온·백도현): 모두 본인 arc 활약 후 자연스러운 휴면 + ARC-07 클라이맥스 재등장. 모순 아닌 작가 의도.
- **F-5**. ARC-03 → ARC-04 9개월 갭 (B30 2019.4 → B31 2020.1): ArcSheets ARC-04 time_window (`2020년 1월~2020년 8월`)와 일치. 팬데믹 도입 전 시간 압축 의도. 일관.
- **F-6**. 백도현 B17 첫 언급 (`사모펀드(백도현 라인 전신)`): 본인이 아닌 라인 전신. 본격 등장은 ARC-06. 일관.

### 11.8 추가 산출물

- `docs/2026-04-07/_pair02_consistency_fix2.py` — 본문 통독 audit 후속 수정 헬퍼
  - target 필드 baseline 정밀화 (refine_text)
  - multi-ref 11건 명시 매핑
  - M-1 / M-2 / B10 명시 수정

### 11.9 최종 상태

- Pair `02`는 **structural ship-ready + prose ship-ready** 모두 충족.
- 클린업이 만든 drift: **0건**
- baseline부터 존재하던 작가 수치 오류: **1건 발견·수정 완료** (M-1)
- 표현 모순 (작가 의도 모호): **1건 발견·수정 완료** (M-2)
- prose 품질 저하 (단일 ref generic 치환): **80건 정밀화 완료**
- arc-exit 패턴 일관성: **6/6 통일 완료**
- pre-existing structural drift (LAF↔FM 부분 동기화): **1건 잔존, redesign 금지로 미수정**

**Pair 02는 본문 통독 audit까지 통과 — 인간 검수자에게 넘길 수 있는 상태.**
