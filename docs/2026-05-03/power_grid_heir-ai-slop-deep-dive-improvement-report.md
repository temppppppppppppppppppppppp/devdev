# power_grid_heir AI-slop Deep Dive Improvement Report

Date: 2026-05-03
Work ID: `power_grid_heir`
Title: `전력망 상속자`
Mode: read-only deep dive survey and improvement report
Manuscript edits: none

## 1. Executive Verdict

`power_grid_heir` is not conceptually broken. The macro hook remains strong:

- no-system 회귀 재벌 권한물
- AI boom is actually power-grid control
- current-document proof, authority receipt, rational opposition, and bounded authority gains

However, the current manuscripts show real AI-slop risk at Stage 4 prose level. The dominant failure is not TR/BI collapse. It is that proof-surface compliance has been mistaken for scene-grade prose health.

Current verdict:

- `TR/BI/work_guard` macro canon: keep
- `ep_001-ep_020`: usable base with targeted slop and phrase cleanup
- `ep_021-ep_029`: repair needed due responsible-owner procedure loop
- `ep_031-ep_045`: promotion should be blocked until fresh manuscript audit and prose repair
- existing manuscript audits: too permissive for artifact leakage and procedural flattening

## 2. Survey Sources

Parallel read-only deep dives were run on:

1. Manuscript prose/style AI-slop signals across `ep_001.txt` through `ep_045.txt`
2. Structure, pacing, scene-grade quality, payoff, antagonist pressure, and fatigue points
3. Artifact alignment across `source_inputs/tr.json`, `source_inputs/bi.json`, `config/work_guard.yaml`, `tmp_review_*.json`, and manuscripts

Additional local collection checked:

- exact repeated lines and dialogue tags
- English/code-like standalone lines
- procedural labels such as `Owner`, `Source`, `External send`, `Review Only`, `Next Agenda`
- literal production references such as `ep\d+`, `Arc`, `전 화`
- missing manuscript review artifacts for `ep_031-ep_045`

All manuscript reads used UTF-8 decode. No manuscript file was edited.

## 3. Key Findings

### Finding 1. Production/meta language leaks into manuscript text

This is the highest severity issue because it breaks immersion immediately. Some lines appear to reference the production pipeline or episode numbering rather than in-world documents.

Evidence:

- `projects/power_grid_heir/manuscripts/ep_014.txt:233`
  - `"ep13 technical verification note에 dependency가 남아 있습니다."`
- `projects/power_grid_heir/manuscripts/ep_019.txt:479`
  - `도윤은 ep18 고객사 메일을 다시 띄웠다.`
- `projects/power_grid_heir/manuscripts/ep_031.txt:17`
  - `김라희가 ep30 access packet을 불러왔다.`
- `projects/power_grid_heir/manuscripts/ep_032.txt:2`
  - `전 화에서 열린 certificate issue date column은 화면 왼쪽에 남아 있었다.`
- `projects/power_grid_heir/manuscripts/ep_032.txt:762`
  - `Arc 11의 빈칸은 닫혔다.`
- `projects/power_grid_heir/manuscripts/ep_035.txt:1`
  - `review line opened.`
- `projects/power_grid_heir/manuscripts/ep_035.txt:597`
  - `ep35의 보상은 그 줄 앞에서 끝났다.`
- `projects/power_grid_heir/manuscripts/ep_040.txt:1`
  - `김라희는 ep39 receipt를 먼저 열었다.`
- `projects/power_grid_heir/manuscripts/ep_042.txt:1`
  - `김라희가 회의실 화면을 열자 ep41의 마지막 줄이 먼저 보였다.`

Collected signal:

- `ep\d+` pattern found 51 times across manuscripts
- `Arc ` found 2 times
- `receipt` found 44 times
- `Next Agenda` found 9 times
- `pending review` found 3 times
- `unresolved` found 7 times

Judgment:

Some `ep##` strings may have been intended as internal packet IDs, but many read as visible pipeline residue. These need a hard gate before any publication-facing export.

### Finding 2. Procedure voice often replaces dramatized prose

The work's core strength is document warfare, but too many scenes become screens, packets, logs, receipts, owner fields, and next agenda queues. The reader sees the accounting of power more often than the felt pressure of power.

Evidence examples:

- `ep_010.txt` uses `relevance candidate`, `verification owner: unassigned`, and repeated issue labels as scene payload.
- `ep_021-ep_024` repeatedly circle `Integrated risk owner`, `agenda candidate`, `Risk Committee: 빈 책임자 칸`, and `Responsible Owner: Blank`.
- `ep_036-ep_045` repeat a table-to-table relay grammar: open receipt, split row, save sheet, queue next agenda.

Judgment:

This is not a reason to abandon the premise. The premise depends on documents. The repair target is to make every document produce a human consequence: who loses room, who must answer, what authority moves, what budget is trapped, what opponent action becomes irreversible.

### Finding 3. Repeated action and dialogue templates create mechanical rhythm

The prose uses many exact repeated tags and body beats.

Collected examples:

- `도윤이 말했다.` - 37 occurrences
- `도윤은 고개를 끄덕였다.` - 20 occurrences
- `김라희가 물었다.` - 20 occurrences
- `도윤은 바로 답했다.` - 17 occurrences
- `김라희가 말했다.` - 15 occurrences
- `도윤이 답했다.` - 15 occurrences
- `회의실이 조용해졌다.` - 9 occurrences
- `김라희가 저장 버튼을 눌렀다.` - 7 occurrences

Judgment:

Plain tags are not inherently wrong, but here they compound the procedural voice. They make the manuscript feel generated from a scene beat sheet instead of rewritten into character-specific behavior.

### Finding 4. Existing audits are too permissive

The existing review artifacts often PASS because required proof-surface terms exist. They do not reliably catch visible production references or scene flattening.

False-pass evidence:

- `tmp_review_manuscript_ep14.json` claims repeated/meta and flattening checks are clear, but `ep_014.txt:233` contains a literal `ep13` reference.
- `tmp_review_manuscript_ep19.json` claims `flattenings_clear: true`, but `ep_019.txt:479` contains `ep18 고객사 메일`.
- There are no detailed `tmp_review_manuscript_ep31.json` through `tmp_review_manuscript_ep45.json` artifacts, while manuscripts `ep_031.txt` through `ep_045.txt` exist and contain the densest leakage.

Judgment:

The manuscript QA gate needs a new AI-slop/prose leak layer. Current review asks, "Is the proof-surface present?" It also needs to ask, "Does the proof-surface still read as a scene?"

### Finding 5. Antagonist pressure softens after the opening

The early material is stronger because opposition is active and reader-readable. In later sections, rivals too often become people who do not object, do not close a screen, or accept a condition after a wording adjustment.

Strong model:

- Early episodes visibly stop a signature, open original files, and start a 72-hour clock.

Weak later pattern:

- opposition becomes non-objection
- payoff becomes file-state label
- next episode hook becomes another table or agenda queue

Judgment:

Repair should give 서민재, 서강준, legal, purchasing, or customer-side actors concrete wins inside episodes. Examples: budget freeze, customer ultimatum, leaked framing, forced public sentence, signed memo that narrows 도윤's room.

### Finding 6. Scene texture declines after the opening

`ep_001` has corridor, clock, pen, body memory, social position, and a clear signature countdown. Later episodes often open on screens and receipts.

Judgment:

The story needs periodic re-grounding in physical and social pressure:

- factory floor
- customer video call
- board member walking out
- paper copy being withheld
- tired engineer refusing a line
- procurement staff realizing a signature creates personal liability

## 4. Priority Improvement Queue

### P0. Hard leak sweep before any promotion/export

Scope:

- `ep\d+`
- `Arc ##`
- `전 화`, `지난 화`, `이전 화`
- raw `receipt`, `review line opened`, `Next Agenda`, `pending review`, `unresolved`
- raw UI/status phrases that are not clearly diegetic document titles

Rule:

- If the phrase is meant as an in-world document ID, rename it into a stable in-world label.
- If it refers to episode production state, remove or dramatize it.

Primary targets:

- `ep_014`, `ep_019`, `ep_031`, `ep_032`, `ep_035`, `ep_040`, `ep_041`, `ep_042`, `ep_044`

### P1. Re-audit and repair `ep_031-ep_045`

Reason:

- detailed manuscript review artifacts are missing for `ep_031-ep_045`
- late manuscripts contain the densest metadata leakage
- table-to-table relay fatigue is highest here

Minimum repair goal:

- each episode ending must land a human-readable consequence, not only a file-state receipt
- each episode must include active opposition or an irreversible cost
- each document/table must change someone’s power, budget, access, deadline, or liability

### P1. Compress the `ep_021-ep_029` responsible-owner loop

Current issue:

- the arc repeats the same blank-owner discovery in multiple officialized forms

Recommended compression:

1. owner gap exposed
2. risk committee threatens rollback
3. archive or original source opens
4. 30-day price is demanded
5. factory descent begins

Cut or merge variants where the only reward is "blank remains, but now official."

### P1. Add antagonist wins

Required pattern:

- every 2-3 episodes, an opponent should win something real

Possible wins:

- 서민재 forces a customer-friendly public sentence
- 서강준 freezes a prepayment or memo line
- legal blocks export or narrows wording
- purchasing refuses firm quote without deposit
- customer procurement sets a clock that 도윤 cannot ignore

### P2. Prose texture and phrase-watch pass

Watchlist:

- `공기가 바뀌었다`
- `고개를 끄덕였다`
- `손이 멈췄다`
- `저장 버튼`
- `owner gap`
- `External send`
- `Read Only Granted`
- `relevance test`
- repeated `말했다` / `물었다` chains

Rule:

- keep plain tags where invisible
- replace mechanical repeats where they carry emotion, pressure, or turn-taking
- add physical handling, interrupted speech, screen glare, paper weight, seat movement, voice pressure, fatigue, and misread gestures

## 5. What Not To Do

Do not regenerate TR/BI first.

Reason:

- macro canon survives
- work_guard premise is still visible
- the unique hook is strong
- the problem is manuscript-level prose QA and late-stage flattening

Do not remove all English/domain terms.

Reason:

- domain texture is part of the hook
- the issue is overexposure and raw label substitution, not bilingual terminology itself

Do not solve this by only polishing sentences.

Reason:

- `ep_021-ep_029` and `ep_036-ep_045` have structural fatigue, not just phrasing fatigue
- some episodes need compression or rebuilt payoff logic

## 6. Proposed Repair Order

1. Run P0 leak sweep over all 45 manuscripts.
2. Re-audit `ep_031-ep_045` with a new AI-slop gate.
3. Repair `ep_031-ep_045` first because leakage and missing review coverage are worst there.
4. Compress/repair `ep_021-ep_029` responsible-owner loop.
5. Run phrase-watch and scene-texture pass over `ep_001-ep_020`.
6. Re-run manuscript audit with proof-surface plus scene-grade checks.

## 7. New Audit Gate Proposal

Add a manuscript gate named `scene_grade_ai_slop_gate`.

Hard fail patterns:

- visible production references: `ep\d+`, `Arc ##`, `전 화`, `지난 화`, `이전 화`
- visible planning terms: `blueprint`, `scene`, `reward`, `보상` when used as production reward
- raw status labels used as prose payload: `pending review`, `unresolved`, `Next Agenda`, `review line opened`

Soft fail patterns:

- three or more consecutive standalone table/status lines without human consequence
- repeated "open screen -> split row -> save receipt -> next agenda" scene grammar
- repeated body beats used as emotional substitute
- opposition that only "does not object"

Pass requirements:

- each proof-surface changes a human-facing stake
- each episode ending states or dramatizes a concrete power/cost/authority movement
- rational opposition remains active
- document labels are diegetic and necessary
- scene has at least one physical/social pressure anchor

## 8. 3-Pass Report Audit Ledger

Pass 1 - Evidence integrity:

- Checked key manuscript line references with UTF-8 reads.
- Confirmed `ep_031-ep_045` review artifacts are missing.
- Confirmed meta-reference examples are present in manuscript text.
- Result: PASS.

Pass 2 - Overreach control:

- Separated macro-canon health from Stage 4 prose failure.
- Avoided recommending TR/BI regeneration.
- Preserved domain-English as allowed texture while flagging raw label overuse.
- Result: PASS.

Pass 3 - Actionability:

- Converted findings into P0/P1/P2 repair order.
- Identified false-pass samples and a new audit gate.
- Kept scope read-only and did not prescribe immediate manuscript edits.
- Result: PASS.

Final confidence: 95%+

## 9. Final Recommendation

Treat `power_grid_heir` as a salvageable, high-concept manuscript with a Stage 4 prose QA failure.

The next work unit should not be a rewrite of the whole project. It should be a bounded repair wave:

1. P0 leak sweep
2. late-episode re-audit
3. `ep_031-ep_045` repair
4. `ep_021-ep_029` compression
5. whole-manuscript phrase and scene texture pass

The guiding sentence for repair:

`Proof-surface compliance is not enough; every proof must become lived pressure, visible cost, or changed authority on the page.`
