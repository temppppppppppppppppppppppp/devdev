# legacy_import 042 Material Benchmark REJECT Example

Date: 2026-04-07
Status: active
Document Type: material benchmark report example
Mode: read-only archive/reference audit
Example Type: operator-training REJECT exemplar

## Pitch Identity

- target id: `legacy_import_042_nakyang_merchant_daughter`
- family: `wuxia`
- source pitch: `material_ssot/20_pitch/intake/legacy_import/20260320/컨셉기획_042_무협_낙양상단막내딸.md`
- source state: legacy import / archive-reference only
- benchmark intent: operator training for an immediate `REJECT` case
- example note:
  - this file demonstrates a case that must not enter the active promotion lane
  - the source is a legacy import, uses a female protagonist under the current active operator lane, and does not contain the required machine-readable first-block ledger
- validator snapshot:
  - `material_readiness_validator.py`: not applicable
  - reason: `legacy_import/` is outside validator promotion scope by design

## Material Compliance Self-Check

- `strict first-block window uses 2~6 only`: no
- `block 1 is not used as opening cider proof`: no
- `block 7+ is not used as opening rescue`: unknown -> treat as no
- `ledger contains exact rows 2, 3, 4, 5, 6`: no
- `no ledger row is blank`: no
- `every selection-ready row has has_cider true`: no
- `bridge_or_payback_note is not used to rescue a false row`: unknown -> treat as no
- `block 6 is not pain_only_exit`: unknown -> treat as no
- `promotion verdict matches the ledger`: yes

## First-Block Cider Ledger Review

- source file does not contain the required machine-readable `First-Block Cider Ledger`
- source file does not contain exact rows `2, 3, 4, 5, 6`
- opening proof is described in legacy prose only
- no exact same-block receipt grammar is present
- no exact `pain_only_exit` declaration is present

Ledger verdict:

- ledger is missing
- readiness cannot be audited under the current material harness
- missing ledger alone is enough to block promotion

## Planning Candidate 7 Questions

1. `장기 목표가 선명한가`: PASS
   상단과 무림 경제 질서를 장악하는 방향성 자체는 분명하다.
2. `단기 목표가 선명한가`: PASS
   금의상단 내부 자금 유출과 흑풍방 연결을 해결하는 초반 임무는 이해 가능하다.
3. `주인공만의 정보격차가 선명한가`: PASS
   장부술을 통한 수리적 직관과 경제 흐름 판독은 선명하다.
4. `유능함의 과정이 보이는가`: PASS
   장부 분석 -> 자금 흐름 추적 -> 상업 전쟁 개입의 뼈대는 있다.
5. `핵심 소재와 전장이 살아 있는가`: PASS
   상단, 사파, 관부, 무림 경제 질감은 흥미롭다.
6. `1~3화 임팩트가 체감형인가`: FAIL
   legacy prose는 있으나 current harness 기준의 exact `2~6` block contract로 잠겨 있지 않다.
7. `첫 block 안 visible 사이다가 분명한가`: FAIL
   machine-readable ledger와 exact same-block receipt가 없어 current promotion 기준으로는 증명 불가다.

## Work-Guard Freeze Check

- `one_line_truth`가 고통보다 상승을 약속하는가: PASS
  상업 장악 판타지 자체는 분명하다.
- `mandatory_scene_engines`에 protagonist-only proof와 visible reevaluation이 같이 있는가: FAIL
  current runtime-safe translation으로 압축된 active `work_guard`가 없다.
- `tracking_slots` 또는 `custom_rules`가 첫 블록 보상을 다음 관문 개방으로 연결하는가: FAIL
  upstream ledger result가 없으므로 translation freeze를 걸 수 없다.
- `evaluation_thresholds`가 visible reward token을 요구하는가: FAIL
  active-lane compatible `work_guard` 기준점이 없다.
- `forbidden_flattenings`가 failure-only / humiliation-only / success -> pure punishment spiral을 금지하는가: FAIL
  legacy import prose만으로는 current freeze check를 통과할 수 없다.

Freeze verdict:

- `WG-V2` or equivalent freeze is not eligible
- legacy import reference는 active runtime translation 대상이 아니다

## Promotion Verdict

`REJECT`

Rationale:

- source is outside the active promotion lane
- source is a `legacy_import` file, not a current candidate/canon/working-synthesis promotion target
- source lacks the required machine-readable first-block ledger
- source lacks the required readiness claim/declaration
- under the current operator policy, female-protagonist ideas do not enter active selection, canon, or downstream handoff lanes

Boundary note:

- this `REJECT` is an active-lane promotion verdict, not a claim that the idea has zero research value
- the source may remain as archive or reference material
- the source must not be presented to an external model as a live promotion target under the current rules

## Fix Queue

- `none` for active-lane promotion
- allowed follow-up options only:
  - keep as archive/reference material
  - mine as research input for a future active-lane candidate
  - if policy changes in the future, rebuild as a new active candidate with exact ledger rows `2~6`, readiness claim, and a fresh benchmark

read-only material benchmark audit complete; no pitch files mutated
