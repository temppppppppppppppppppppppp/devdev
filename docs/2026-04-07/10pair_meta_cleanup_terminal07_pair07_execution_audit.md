# 10-Pair TR/BI Legacy Meta Cleanup — Terminal 07 / Pair 07 Execution Audit

- Date: 2026-04-07
- Status: cleanup applied
- Document Type: post-execution audit note
- Canonical Path: `docs/2026-04-07/10pair_meta_cleanup_terminal07_pair07_execution_audit.md`
- Owner: Terminal 07 (Opus)
- Order: `docs/2026-04-07/10pair_tr_bi_legacy_meta_cleanup_execution_order.md`
- Survey: `docs/2026-04-07/10pair_meta_cleanup_terminal07_pair07.md`
- Family Overlay: `blockguide`
- Mode: `bounded narrative cleanup / artifact edits applied`
- Baseline Commit: `5c71b81a36ab2cbae824c630bb63219354b913a8`

## 1. Scope of Execution

Bounded narrative cleanup for pair `07` only, per the merged execution order tranches `1` (`section_rotation` labels), `2` (prose normalization), and `3` (BI-only tail). No `evolution` field touched. No `block_id` / `block_no` rewritten. No `docs/temp/` mutation. No system / queue / runtime files touched.

Touched files (only):

- `treatments/07_office_checkup_next_day_tr_block_070_draft.json`
- `bible/07_bi_office_checkup_next_day.json`

## 2. Result Summary

### 2.1 Tranche 1 — `section_rotation` labels

- TR `blocks[0..40].genre_ext.section_rotation`: leading `ARC-0N ` prefix stripped (`ARC-01 검진 다음 날` → `검진 다음 날`, `ARC-04 감각의 흔들림` → `감각의 흔들림`, etc.).
- BI `MasterBible.plot_roadmap[*].genre_ext.section_rotation`: mirrored from cleaned TR (BI plot_roadmap is a 1:1 mirror of TR `blocks`).

### 2.2 Tranche 2 — prose normalization

Cleaned in TR `blocks[*]` (and mirrored into BI `plot_roadmap[*]`):

- `callback[*]`: `129` strings; legacy `Block N에서 ...` / `(BNN) ...` / `ARC-NN에서 ...` wording removed; structural anchors lifted into `callback_sources` (newly populated structural array — on the §6.1 allow list, so allowed to write).
- `foreshadow[*]`: `68` strings; same treatment, structural anchors lifted into `foreshadow_targets`.
- `content.context / event_villain / solution / reward`: explicit `Block N` / `ARC-NN` / `Phase 0 design` / `Phase 0 opponent_transition_plan` references rewritten into natural language (`다음 단계에서`, `그 시점의`, `초기 설계`, `초기 적대 계획`, `아크 출구`, etc.).
- `genre_ext.section_rotation / method / success_pattern / knowledge_used / capital_before / capital_after / profit_loss / risk_level / historical_event / leverage_used (string and list)`: same.
- `relationship_delta[*].before / after`, `power_shift.protagonist / antagonist`, `stakes`: same.

### 2.3 Tranche 3 — BI-only tail

Cleaned in BI only:

- `_schema_description`: `phase0` token rewritten to `초기`.
- `MasterBible.AssetLibrary.KeyNPCs[*].desc` (`4` hits): `Block 1부터` / `Block 3부터` / `Block 7부터` → `이후부터`.
- `MasterBible.AssetLibrary.KeyNPCs[*].key_turning_points[*].event` (`1` hit on `KeyNPCs[0]`): `ARC-01` prefix stripped from per-event labels.
- `MasterBible.AssetLibrary.Partners[*].cadence` (`2` hits): `Phase 1: ...` → natural label.
- `MasterBible.WorldState.opponent_transition_plan[*].phase` (`5` hits): `Phase 1: 공 가로채기` → `공 가로채기`, `Phase 2: 본격 견제` → `본격 견제`, etc. Structural numbering survives in sibling fields `block_range`, `entry_block`, `transition_block` (already present and untouched).
- `MasterBible.WorldState.opponent_transition_plan[*].methods` / `goal` / `weakness`: scrubbed where the rare meta token leaked.
- `MasterBible.WorldState.starter_company.state / liabilities`, `FinanceHUD.Protagonist.actual_truth.financial_status.debt`, `protagonist_config.start_point.context`: scrubbed.
- `MasterBible.HistoricalEvents[*].summary` (`2` hits): `Block 1의 B0` → `그 시점의 B0` (HR rating `B0` preserved in-world), `ARC-05에서 시작된` → `그 단계에서 시작된`.

## 3. Validation (per execution order §8)

1. Byte-level UTF-8 read-back: both files decode cleanly, no BOM, trailing newline preserved.
2. JSON parse pass: both files parse, top-level shape unchanged (`TR._total_blocks=70`, `BI.MasterBible.plot_roadmap` length `70`, `opponent_transition_plan` length `5`).
3. Forbidden-pattern grep on touched human-readable fields (excluding `block_id`, `block_no`, `arc_id`, `arc_no`, `phase_no`, `stage_no`, `foreshadow_targets`, `callback_sources`, `evolution`):
   - `Block \d+`, `블록 \d+`, `ARC[-\s]?\d+`, `Phase \d+`, `Stage \d+`, `\bB[1-9]\d?\b`, `phase0`, `Phase0`
   - TR hits: `0`
   - BI hits: `0`
4. Allowed structural fields preserved:
   - `TR.blocks[0..69].block_id == "Block 1".."Block 70"` (`70/70`)
   - `TR.blocks[*].block_no == 1..70` (`70/70`)
   - `TR.blocks[*].title` non-empty (`70/70`)
   - `callback_sources` / `foreshadow_targets` newly populated where source prose carried block references (e.g. `blocks[1].callback_sources = [1]`, `blocks[5].foreshadow_targets = [21..30]`, `blocks[51].callback_sources = [21..30, 48]`)
   - `BI MasterBible.plot_roadmap == TR.blocks` (full byte-equality of mirrored 70 entries)
   - `evolution` field: not present in this BI to begin with, still not present (the wuxguide-only field — n/a here, but explicitly checked)

## 4. Borderline Policy Calls

1. `B0`, `B+`, `C+` (in-world HR ratings) preserved everywhere they appear. The `Bnn` shorthand strip rule was scoped to `\bB[1-9]\d?\b` only — i.e. `B1..B70` ⇒ block-ref strip, `B0` and `B+/B-/C+` ⇒ in-world content kept. Verified manually on `blocks[17].content.reward`, `HistoricalEvents[9].summary`, `financial_status.debt`.
2. `LvN` (in-world ability tiers `Lv1..Lv7+`) preserved everywhere. They are not on the meta-language-leak lexicon and they are clearly in-world content.
3. `spike` token (jargon for the in-world `Block 1 spike` template) is left in cleaned strings as a bare word — the meta prefix was stripped (`Block 1 spike` → `spike`), but `spike` itself is in-world jargon and not a meta token per the handoff.
4. `(Block N - Label)` parenthetical jargon (e.g. `Block 32(감각 흔들림)`) was rewritten to `다음 단계` / `그 시점`, with the parenthetical label dropped to keep the prose readable; the structural anchor is preserved via `callback_sources` / `foreshadow_targets`.
5. `Phase 0 design` and `Phase 0 opponent_transition_plan` (story-design pipeline tokens) were rewritten to `초기 설계` and `초기 적대 계획`. These are not in-world stage names, they are generation-pipeline labels, so the cleanup is policy-correct.
6. `ARC-NN` references that disambiguated relative position (e.g. `ARC-01에서 시작 / ARC-07에서 완결`) were collapsed to `그 단계에서`, which loses some of the early-vs-late contrast. This is a deliberate choice — the policy treats `ARC-NN` as forbidden and the structural arc disambiguation was already implicit in `block_no` ordering. No pair truth lost.
7. `_schema_description` `phase0/TR draft 동기화 산출물` → `초기/TR draft 동기화 산출물`: slightly awkward administrative header but inside the cleanup scope (per the order, `_schema_description` is human-readable header text).
8. `KeyNPCs[8]` and similar are out of survey scope — no `_creation_note` / `_schema_description` style fields are present in pair `07` BI other than the top-level `_schema_description`, so the pair `08`-style guardrail is moot here.

## 5. Pair-Truth Separability

Per the survey §5.4, the prior `P2` truth blockers from `2026-04-06` (`incarnation_type=회귀자` vs `is_regressor=false`; start-state vs end-state mixup) were already silently corrected upstream and were not observable in the baseline `5c71b81a`. This cleanup wave is therefore strictly meta-wording only and did not need to touch `protagonist_config`, `regression_ext`, or `FinanceHUD` actual-truth fields beyond the in-scope `financial_status.debt` line that carried legacy `Block 40~60` numbering.

No pair truth was rewritten by this wave.

## 6. Stop Gates Encountered

None. All five stop gates from order §9 were checked:

- UTF-8 read-back agrees with file content.
- No wording fix changed pair truth (verified by spot-check on `block 17` defeat reward, `block 50` calmare cross-affiliate finding, `block 64` 정밀검사 reveal — all narrative beats preserved).
- No supposedly human-readable field turned out to be the authoritative structural carrier (the structural carriers `block_id`, `block_no`, `block_range`, `entry_block`, `transition_block` are all separate sibling fields, untouched).
- Pair `07` is not the late-block-truth-unstable case (that's pair `10`); fresh UTF-8 byte read-back of late blocks `60-70` showed stable content.
- `evolution` not present in pair `07` BI, so the pair `09` guardrail does not apply.

## 7. Deferred / Not Done

- `docs/temp/` execution-queue mirror: not created (per order §11 explicit instruction).
- Stage 2/3/4 runtime probe: not in scope; not done.
- Pair-quality rewrite, NPC redesign, arc redesign: not in scope; not done.

## 8. Confidence

`97%` — bounded mechanical cleanup with full pre/post grep verification. The remaining `3%` reflects editorial subjectivity in a small number of `ARC-NN`-collapse points where the original prose used arc numbering for relative-position contrast; these were collapsed to neutral `그 단계` phrasing. If a subsequent reviewer wants the contrast restored, the structural anchors are still available via `callback_sources` / `foreshadow_targets` and the surrounding `block_no` ordering.

Confidence: `97%`

## 9. Post-Cleanup 정합성 보정 (cross-cut + individual)

클린업 직후 페어 크로스컷/개별 정합성 검사에서 다음 문제가 발견되어 별도 보정 패스로 처리했다. 계획 파일: `~/.claude/plans/tranquil-roaming-codd.md` (사용자 승인 완료).

### 9.1 발견 사항

1. **NPC 카탈로그 크로스컷 불일치 — 동일 인물 다른 표기**: BI `AssetLibrary.ArcSheets[*].new_npcs` 가 일반 역할 라벨(`재무팀 차장 (숫자 검증 협력자)`, `법무팀 변호사`, `그룹 전략실장` 등 8건)을 들고 있는 반면, TR `relationship_delta[*].target` 은 이미 `서정민(재무팀 차장)`, `최수연(법무팀 변호사)`, `강민호(그룹 전략실장)` 처럼 고유명사를 사용하고 있었다. 같은 캐릭터가 두 파일에서 다르게 불리는 상태.
2. **NPC 누락**: `정태호(한일그룹 경영지원실 팀장)` (블록 41–68, 11회 등장, 후반 핵심 적대축) 와 `정기철(용인센터 현장소장)` (블록 12) 두 명은 어떤 ArcSheet `new_npcs` 에도 들어 있지 않았다.
3. **`KeyNPCs[1..4].desc` 클린업 부수효과**: `오세진 / 장현태 / 박전무 / 김대표` 4건의 `desc` 가 직전 클린업의 결과로 `이후부터 본격적으로 영향력을 행사한다.` 라는 빈 한 줄로 축소돼 있었다(원본은 `Block 1부터 ...` `Block 3부터 ...` 와 같이 진입 블록 번호를 산문에 포함하던 형태). 구조적 진입 정보는 같은 객체의 `first_block` 필드에 이미 있으므로 산문은 캐릭터 설명으로 다시 써야 했다.
4. **`장현태` 후반 소속 전이 누락**: `KeyNPCs[2].role = "적대자(사업부장)"` 만 있고, TR 후반(블록 51–60)의 `장현태(경영관리본부)` 전이가 어디에도 명시돼 있지 않았다.

### 9.2 적용한 수정

수정 파일: `bible/07_bi_office_checkup_next_day.json` (단 1개). TR/`plot_roadmap` 미러는 절대 손대지 않음.

**Fix 1 — `ArcSheets[*].new_npcs` 고유명사 정규화 (7개 ArcSheet 중 5개 갱신)**

| ARC | 변경 후 (TR canonical) |
|---|---|
| ARC-02 | `최부장(물류팀장, TF 주재)`, `윤재환(MD사업부 파견 기획과장)`, `정기철(용인센터 현장소장)` (정기철 신규 추가) |
| ARC-03 | `서정민(재무팀 차장)`, `외부 감사인` |
| ARC-05 | `윤재경(계열사 전략기획 상무)`, `이도현(그룹 전략실 과장)`, `정태호(한일그룹 경영지원실 팀장)` (정태호 신규 추가) |
| ARC-06 | `최수연(법무팀 변호사)`, `정호진(사외이사)` |
| ARC-07 | `강민호(그룹 전략실장)`, `그룹 구조조정 상무` (이름 없음, 단역) |

ARC-01 (이미 고유명사), ARC-04 (`HR팀장`/`장현태 측근 부장` — TR 측에도 고유명사 없음) 는 그대로 둠.

**Fix 2 — `KeyNPCs` 조연 9명 추가 (5명 → 14명, 후속 보정 후 최종 15명)**

추가된 항목 (각 `name` / `role` / `desc` / `first_block` / `final_status` / `key_turning_points[]` 6필드 풀 스키마):

`윤재환(9)`, `최부장(9)`, `정기철(12)`, `서정민(21)`, `정태호(41)`, `윤재경(43)`, `이도현(45)`, `최수연(52)`, `정호진(54)`, `강민호(62)` — 총 10명. `key_turning_points` 는 TR 산문에서 추출한 실제 전환점 1–4건씩.

(실제 작업 중 9명 계획 → 정태호 별도 누락 발견으로 10명 추가, 한시혁 포함 최종 KeyNPCs 15엔트리.)

**Fix 3 — 기존 `KeyNPCs[1..4].desc` 산문 복원**

`오세진 / 장현태 / 박전무 / 김대표` 4건의 `desc` 를 1–3 문장의 캐릭터 설명으로 다시 작성. `장현태` desc 에 `MD사업부장 → 경영관리본부` 전이를 명시(Fix 4 는 이로써 흡수). `first_block` / `final_status` / `key_turning_points` 는 미수정.

### 9.3 검증

1. **UTF-8 / JSON parse / no BOM**: 양 파일 통과.
2. **TR ↔ BI plot_roadmap 미러 무결성**: `TR.blocks == BI.MasterBible.plot_roadmap` (70/70 deep-equal). Fix 패스가 미러를 건드리지 않았음을 보증.
3. **NPC 이름 레지스트리 교차 비교**: TR 등장 고유명사 15명 (`강민호 / 김대표 / 박전무 / 서정민 / 오세진 / 윤재경 / 윤재환 / 이도현 / 장현태 / 정기철 / 정태호 / 정호진 / 최부장 / 최수연 / 한시혁`) **모두** `BI.AssetLibrary.KeyNPCs[*].name` 에 등장. `set(tr_chars) - set(bi_keynpc_names) = ∅`.
4. **금칙 패턴 grep**: `Block \d+ / 블록 \d+ / ARC[-\s]?\d+ / Phase \d+ / Stage \d+ / \bB[1-9]\d?\b / phase0` — 수정 필드(`KeyNPCs[*].desc / role / final_status / key_turning_points[*].event`, `ArcSheets[*].new_npcs`) 0건. 전체 BI 풀 walk 0건 (`§3` 의 0건 결과 유지).
5. **스키마 보존**: `KeyNPCs[*]` 15건 모두 6필수 필드 보유, `key_turning_points[*]` 모두 `{block, event}` 형태.
6. **미수정 섹션**: `Seeds(5)`, `HistoricalEvents(20)`, `WorldState.opponent_transition_plan(5)`, `plot_roadmap(70)` 길이/내용 불변.
7. **편집 발견 결함**: 첫 적용 직후 `KeyNPCs[강민호].desc` 에 `ARC-07` 토큰이 한 곳 잔존(직접 작성한 산문에서 발생). `마지막 아크` 로 즉시 교체 후 재적용 → 0건 통과.

### 9.4 범위 외 (의도적 제외)

- `HistoricalEvents[*].block_reference` 신규 필드 — 스키마 확장, 별건.
- `foreshadow_targets ↔ callback_sources` 비대칭 58건 — 산문 자체가 원래 비대칭(예: 블록 37–40 callback 이 `Block N에서` 형식이 아닌 암묵적 회수). 강제 대칭화는 데이터 날조.
- `그 단계 / 다음 단계 / 그 시점` 30+곳 — 메타 토큰 자리에 들어간 자연어 치환의 정상 결과, 의미 손실 없음.
- TR 측 어떤 변경 — 미러 깨짐 위험.
- 페어 진실(능력 등급 `Lv1→Lv8` 진행, 시간선 `2025.03→2026.10`, `opponent_transition_plan` 5엔트리 적대 구조) — 사전 점검에서 이미 정합.

### 9.5 결과 요약

| 항목 | 수정 전 | 수정 후 |
|---|---|---|
| `KeyNPCs` 엔트리 수 | 5 | 15 |
| `ArcSheets[*].new_npcs` 일반 라벨 | 8건 | 0건 |
| `ArcSheets[*].new_npcs` 누락 NPC | 정태호, 정기철 | 모두 등재 |
| 빈 `desc` ("이후부터 본격적으로 영향력을 행사한다") | 4건 | 0건 |
| TR 등장 NPC 중 BI `KeyNPCs.name` 에 부재 | 10명 | 0명 |
| BI 전체 금칙 패턴 grep | 0건 | 0건 |
| TR ↔ plot_roadmap 미러 | 일치 | 일치 |

Confidence (정합성 보정): `98%` — 보정은 mechanical 매핑이 대부분이고 검증으로 모든 invariant 가 통과. 남은 `2%` 는 새로 작성한 9개 `desc` 산문의 사실관계 미세 디테일(예: `서정민` 이 정말 `재무팀 차장` 이 맞고 `재무팀 부장` 이 아닌가 등) 정도이며, 모두 TR `relationship_delta[*].target` 과 산문 첫 등장 문장에서 직접 인용한 표기를 사용했다.

## 10. 실전 투입 폴리싱 (audit 권장 사항 적용)

별도 감사(`실전 가능 audit`, 8개 변곡 블록 풀독 + 곡선/자본/장르 적합성 점검) 결과를 받아 권장 사항 6건을 페어 07에 추가 적용했다.

### 10.1 적용한 항목

| Item | 대상 | 내용 |
|---|---|---|
| 6 | TR `blocks[3,4,9].genre_ext.capital_*` | Lv 표기 chain 정규화 — `block N.before == block N-1.after` 동기화 (4건 불일치 → 0건). `block 4.after` 는 CC 라인 정보 보존 형태로 다시 적음 (`Lv2 배석권 (CC 라인 비공식 + 견제 인지)`) |
| 5 | TR `blocks[0,3,6,9,17,27,31,69].content.*` + `blocks[6].genre_ext.capital_after / success_pattern` | 디자이너 메타 노트 정리 — `이 블록은 opening humiliation이다`, `보상은 다음 블록에서`, `이것이 작품의 간판 장면이다`, `이 블록은 defeat다`, `독자도 안다`, `마지막 블록`, 트레일링 ` 끝.` 등 9건 제거/리프레이즈 |
| 4 | TR `blocks[25].content.context` | Block 26 (감사 보고서) 산문 +200자 확장 — 김대표·박전무 추가 문답 + 장현태 첫 반응 (소명 요청 공문 받는 정적 비트). 240자 → 564자. |
| 3 | TR `blocks[54].content.event_villain / solution / reward` | Block 55 (조용한 서류전) 에 정태호 카운터 1발 추가 — 정태호가 윤재경에게 사적 채널 메모로 시혁의 동기를 흔들려 시도하고, 시혁은 보고서 한 줄을 비우는 무대응으로 자기 모순화. 정태호 ARC 의 자멸 라인이 너무 매끄럽다는 audit 지적 보정 |
| 7 | TR `blocks[66].content.context / event_villain` | Block 67 (라인 제안들) 강민호 저항 1박자 추가 — 첫 만남에서 강민호가 시혁의 직급/이력을 한 번 견제하는 비트, 시혁은 침묵으로 받음. ARC-07 클라이맥스 톤이 너무 mutual cooperation 으로 흐른다는 audit 지적 보정 |
| 2 | BI `MasterBible.AssetLibrary._anonymous_role_npcs` | Stage 2 산문 생성기 지시 메타 필드 추가 — `HR팀장 / 외부 감사인 / 장현태 측근 부장 / 그룹 구조조정 상무` 4명에 대해 `naming_policy: 고유명사 부여 금지` 명시. roster 4엔트리 (`role / first_block / function / naming_policy`) |

### 10.2 시행 중 발생한 결함과 복구

폴리싱 스크립트(`/tmp/p07/polish_pair07.py`) 가 처음 실행될 때 BI 잔존 ARC 토큰 하나를 발견해 즉시 패치 후 재실행했는데, 일부 변경이 `cur + addition` 형태(누적적 — 멱등하지 않음)였기 때문에 5개 필드(블록 26 context, 블록 55 event_villain/solution/reward, 블록 67 event_villain) 에서 텍스트가 두 번 삽입됨. dedupe 스크립트(`/tmp/p07/dedupe_pair07.py`) 로 처리했으나, 블록 67 event_villain 은 `cur.replace(old, new_with_old_inside)` 패턴이라 dedupe 가 너무 공격적으로 잘려 원본 6문장이 사라졌고, 별도 수동 복원으로 처리. 모든 텍스트 invariant 통과 확인.

### 10.3 최종 검증 (스크린샷)

```
TR forbidden hits: 0
BI forbidden hits: 0
Designer meta remaining: 0
Lv chain breaks: 0
KeyNPCs count: 15
Anonymous NPCs roster: 4
TR chars missing from BI KeyNPCs: (none)
Seeds: 5, HistoricalEvents: 20, opponent_transition_plan: 5
Mirror integrity: TR.blocks == BI.plot_roadmap
```

### 10.4 적용 안 함 (audit 권장 중 보류)

- **장르 톤 결정 (필수 R1)** — 카카오 메인 슬롯 vs Munpia/Naver 사회파 슬롯 결정은 데이터 작업이 아니라 사용자 결정 사항. 현재 상태는 사회파 톤(절제된 사이다, 학습형 패배, 권고사직 결말)이며, 즉시 사이다 슬롯에 넣으려면 별도 톤 조정 필요.
- **블록 33·35 약밀도** — 의도된 quiet/recovery 비트(audit 결과 양호 판정), 그대로 둠.
- **HistoricalEvents `block_reference` 필드** — 스키마 확장이라 별건.

### 10.5 결과 요약

| 지표 | 보정 전 | §9 후 | §10 후 |
|---|---|---|---|
| 금칙 패턴 (TR/BI) | 0/0 | 0/0 | 0/0 |
| 디자이너 메타 노트 | 9 | 9 | 0 |
| Lv chain breaks | 4 | 4 | 0 |
| KeyNPCs | 5 | 15 | 15 |
| 익명 NPC 정책 명시 | 없음 | 없음 | 4건 (`_anonymous_role_npcs.roster`) |
| Block 26 context (자) | 240 | 240 | 564 |
| 정태호 카운터 비트 | 1발 (block 58) | 1발 | 2발 (block 55 추가) |
| 강민호 저항 톤 | 무 | 무 | 1박자 (block 67) |

Confidence (실전 폴리싱): `97%` — 정태호 카운터(item 3)와 강민호 저항(item 7)의 산문은 기존 톤과 인물 동기에서 직접 도출했고 기존 전개와 충돌하지 않음. 남은 `3%` 는 추가한 산문의 미세한 어휘 선택 차원(예: 정태호의 메모 톤이 기존 정태호 캐릭터의 사용 어휘와 정확히 일치하는지)이며, Stage 2 생성 시 자동 통합 가능 수준.
