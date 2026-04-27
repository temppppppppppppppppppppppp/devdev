# T09 Artifact Truth Samples

Date: 2026-04-27
Author: Terminal T09
Mode: read-only investigation, single-PC artifact and DB inspection
GitHub issue: #58 [Stage4] Reduce POST_SELECT_CONFLICT carryover drift in 5-arc runs
Workspace: `C:\Users\wjjo\Desktop\글도비`
Target project (per `docs/2026-04-27/gcp-iam-5arc-live-run-handoff-current.md`): `projects/01_골든카나리아`
Target session_id: `20260427_070604`

This report covers Stage4 ep4-ep9 of the current GCP/Vertex live run. It triangulates artifact truth (file bytes), metadata truth (DB rows) and narrative truth (visible contradiction shape) without overclaiming from any single sample.

## Scope

- Inspect representative Stage4 POST_SELECT_CONFLICT episodes ep4-ep9 from the current GCP/Vertex handoff project.
- For each attempt:
  - confirm artifact file exists, decodes as UTF-8, and capture bytes / sha256 prefix;
  - cross-check DB row in `stage_attempts` and `director_selections` (verdict, content_hash, artifact_path);
  - read Director-rendered `reject_reason` to expose the visible contradiction type.
- Where contradiction is visible in the rejected text itself, search the Stage3 blueprint (DB `blueprints` table) for the same drifted tokens to test whether the carryover error originates upstream.
- Tightly bounded text quotes only. Long manuscript text is summarized.

Out of scope:
- No source/test/doc edits beyond this report.
- No DB writes, no GitHub mutation, no live-run restart.
- No global pytest run.
- No claim of root cause beyond what these samples support.

## Commands / Evidence

All commands were read-only. SQLite was opened with `mode=ro`. Files were read with explicit UTF-8 decode.

### A. DB schema / scope confirmation

```python
import sqlite3, pathlib
db = pathlib.Path('projects/01_골든카나리아/project_data.db')
conn = sqlite3.connect(f'file:{db}?mode=ro', uri=True)
# tables include: stage_attempts, director_selections, manuscripts, blueprints,
# attempt_raw_rationale, context_cache_attempts, episode_meta, ...
```

- `stage_attempts` has columns: `verdict`, `failure_category`, `reject_reason`, `content_hash`, `artifact_path`, `candidate_key`, `session_id`, plus runtime advisory and patch fields.
- `director_selections` has parallel columns: `verdict`, `content_hash`, `artifact_path`, `selection_reason`, `director_thinking`, `final_verdict`.
- `attempt_raw_rationale` has 130 rows for stage=4, ep_num between 4 and 9.
- `context_cache_attempts` has 211 rows (Stage4 cache transport active in this run).

### B. Stage4 attempt rows for ep4-ep9 (current session)

```sql
SELECT ep_num, attempt_num, verdict, failure_category, content_hash, artifact_path
FROM stage_attempts
WHERE stage=4 AND ep_num BETWEEN 4 AND 9 AND session_id='20260427_070604'
ORDER BY ep_num, attempt_num;
```

Result matches `gcp-iam-5arc-live-run-handoff-current.md:81-88` exactly:

| ep | att | verdict | failure_category | candidate_key |
| --- | --- | --- | --- | --- |
| 4 | 1 | REJECT | POST_SELECT_CONFLICT | `C\|balanced` |
| 4 | 2 | PASS | – | `A\|InPlace 수정` |
| 5 | 1 | REJECT | POST_SELECT_CONFLICT | `C\|narrative` |
| 5 | 2 | PASS | – | `C\|최종 수정` |
| 6 | 1 | REJECT | LOGIC_ERROR | `B\|balanced` |
| 6 | 2 | REJECT | CONSTRAINT_VIOLATION | `C\|narrative` |
| 6 | 3 | REJECT | POST_SELECT_CONFLICT | `A\|balanced` |
| 6 | 4 | PASS | – | `A\|InPlace 수정` |
| 7 | 1 | REJECT | POST_SELECT_CONFLICT | `A\|narrative` |
| 7 | 2 | PASS | – | `A\|InPlace 수정` |
| 8 | 1 | REJECT | POST_SELECT_CONFLICT | `B\|narrative` |
| 8 | 2 | REJECT | POST_SELECT_CONFLICT | `A\|narrative` |
| 8 | 3 | PASS | – | `A\|InPlace 수정` |
| 9 | 1 | REJECT | POST_SELECT_CONFLICT | `A\|tension` |
| 9 | 2 | REJECT | POST_SELECT_CONFLICT | `B\|balanced` |

Manuscripts persisted: `ep1`-`ep8`. `ep9` has no PASS row and no manuscript row (`SELECT MAX(ep_num) FROM manuscripts` returns 8). Blueprints exist for ep4-ep9 (sizes 6.3K-8.6K bytes).

### C. Artifact truth: UTF-8 decode and sha256 prefix

All 35 stage4 artifact files for ep4-ep9 decode as UTF-8 cleanly:

```python
for f in stage4_artifacts:
    data = f.read_bytes()
    data.decode('utf-8')          # no UnicodeDecodeError
    h = hashlib.sha256(data).hexdigest()[:12]
```

Sizes range 9.8 KB to 18.3 KB. No `U+FFFD`, no triple-question placeholder in any file body.

### D. Metadata truth: DB content_hash vs file sha256 prefix

```text
ep/att   verdict db_hash[:12]   file_sha256[:12]  match  artifact
ep4/01   REJECT  af3725f04d5e   af3725f04d5e      OK     rejected_best__C_balanced.txt
ep4/02   PASS    d652d3d8392f   d652d3d8392f      OK     patched_after_fix__A_InPlace.txt
ep5/01   REJECT  cb3a2bf6526b   cb3a2bf6526b      OK     rejected_best__C_narrative.txt
ep5/02   PASS    698a8fc76b80   81db5a1134bc      MISMATCH  final_manuscript__C.txt
ep6/01   REJECT  642f5e16b8f2   13a4183ff277      MISMATCH  rejected_best__B_balanced.txt
ep6/02   REJECT  9710f3f4e0e1   10410b6ce3fa      MISMATCH  rejected_best__C_narrative.txt
ep6/03   REJECT  b666f7cdd0b1   b666f7cdd0b1      OK     rejected_best__A_balanced.txt
ep6/04   PASS    0d764cde3464   0d764cde3464      OK     patched_after_fix__A_InPlace.txt
ep7/01   REJECT  02f86e482ac6   02f86e482ac6      OK     rejected_best__A_narrative.txt
ep7/02   PASS    4b05dddb0815   4b05dddb0815      OK     patched_after_fix__A_InPlace.txt
ep8/01   REJECT  805ad72029a7   805ad72029a7      OK     rejected_best__B_narrative.txt
ep8/02   REJECT  f785678e46e8   f785678e46e8      OK     rejected_best__A_narrative.txt
ep8/03   PASS    9bf8ebfa0438   9bf8ebfa0438      OK     patched_after_fix__A_InPlace.txt
ep9/01   REJECT  50ec78d0c622   6bc1c277cd07      MISMATCH  rejected_best__A_tension.txt
ep9/02   REJECT  391593bd08fb   391593bd08fb      OK     rejected_best__B_balanced.txt
```

Sibling artifact files in the same attempt directory have identical content (same sha256), so the mismatches are not "wrong file picked" collisions:

```text
13a4183ff277 ep_0006/attempt_01/rejected_best__B.txt          (10800 bytes)
13a4183ff277 ep_0006/attempt_01/rejected_best__B_balanced.txt (10800 bytes)
10410b6ce3fa ep_0006/attempt_02/rejected_best__C.txt          (13138 bytes)
10410b6ce3fa ep_0006/attempt_02/rejected_best__C_narrative.txt(13138 bytes)
6bc1c277cd07 ep_0009/attempt_01/rejected_best__A_tension.txt  (17253 bytes)
6bc1c277cd07 ep_0009/attempt_01/selected_before_fix__A.txt    (17253 bytes)
81db5a1134bc ep_0005/attempt_02/final_manuscript__C.txt       (17309 bytes)
81db5a1134bc ep_0005/attempt_02/selected_candidate__C.txt     (17309 bytes)
```

The 4 mismatches are real: the DB `content_hash` for those rows differs from the sha256 of the file bytes the same DB row points to via `artifact_path`.

### E. Director rationale (Director-rendered `reject_reason` excerpts)

Excerpts are short and only as long as needed to prove the contradiction shape. The rejected manuscript text itself is summarized further down.

ep4 att1 REJECT POST_SELECT_CONFLICT — duplicated already-completed beat + deadline drift:

> `[V67] History Conflict: 제4화는 제2화 및 제3화에서 이미 완료된 지시 사항(법인 설립을 위한 로펌 수배)을 마치 처음 지시하는 것처럼 중복 묘사하고 있으며, 제3화에서 설정된 엄격한 데드라인('내일 오전')을 무시하고 '며칠 뒤'로 시간적 배경을 미루는 타임라인 충돌이 발생했습니다.`

ep5 att1 REJECT POST_SELECT_CONFLICT — institution-name drift mid-document:

> `[V67] History Conflict: 이전 원고에서 확립된 주거래 증권사의 이름(H&T 증권)이 현재 원고 중반부터 다른 이름(한미증권)으로 표기되는 설정 충돌이 발생했습니다.`

ep6 att3 REJECT POST_SELECT_CONFLICT — capital and date drift:

> `[Continuity Conflict] 현재 원고는 이전 회차들에서 확립된 핵심 설정(초기 자본금 20억 원, 2006년 2월 1일 이란 핵 선언 및 첫 투자 성공)을 완전히 무시하고, 자본금을 15억 원으로 축소시키며 시간적 배경을 4월로 변경하는 등 심각한 설정 충돌을 일으키고 있습니다.`

ep7 att1 REJECT POST_SELECT_CONFLICT — duplicated newsflash event:

> `[Continuity Conflict] 제5화에서 이미 보도되어 수익 실현의 배경이 된 이란 핵 관련 속보가 제7화에서 다시 최초 발생 사건처럼 묘사되는 치명적인 타임라인 오류가 존재하며, 증권사 명칭(H&T 증권 -> 한미증권)의 일관성 누락이 발견되었습니다.`

ep8 att1 / att2 REJECT POST_SELECT_CONFLICT — institution drift again, plus wrong news token at scene-open:

> `... 일관되게 'H&T 증권'으로 설정되었던 핵심 배경 장소의 이름이 현재 원고에서 '한미증권'으로 변경되어 등장하는 설정 충돌이 발생했습니다.`

> `7화 엔딩에서 유가 급등을 촉발한 핵심 뉴스(나이지리아 피격 및 EIA 재고 감소)가 8화 도입부에서 '이란 우라늄 농축 재개 선언'으로 잘못 기재되는 설정 충돌이 발생했습니다.`

ep9 att1 REJECT POST_SELECT_CONFLICT — replayed prior newsflash on a new date plus institution drift:

> `[V67] History Conflict: 이전 회차(제5화)에서 2월 1일에 이미 발생하여 보도된 '이란 우라늄 농축 전면 재개' 속보가 제9화에서 2월 28일에 다시 새로운 속보로 등장하는 타임라인 및 사건 중복 충돌이 발생했습니다.`

ep9 att2 REJECT POST_SELECT_CONFLICT — duplicated continuation beats:

> `[V67] History Conflict: 현재 원고는 이전 회차에서 이미 완료된 두 가지 행동(VIP 예외 승인선 개설, 가죽 노트에 다음 투자처 기록)을 마치 처음 수행하는 것처럼 중복 묘사하여 타임라인 및 상태 충돌이 발생했습니다.`

### F. Narrative truth: token search inside ep9 att1 manuscript text

The rejected text itself was scanned for the contested tokens. Excerpts are short and contextual, used only to prove the contradiction is visibly written into the manuscript and not just a Director hallucination.

```text
ep9 att1 occurrences of 'H&T'         : 4
ep9 att1 occurrences of '한미증권'     : 1   ← drift inside the same chapter
ep9 att1 occurrences of '2월 28'      : 2   ← scene 5: '2월 28일의 뇌관'
ep9 att1 occurrences of '우라늄'       : 1   ← 우라늄 농축 전면 재개 — same event already aired in ep5
ep9 att1 occurrences of 'VIP'         : 4   ← VIP 예외 승인선 (Exception Lane) treated as new
ep9 att1 occurrences of '가죽 노트'    : 2
```

Anchor lines (truncated):

- `여의도 H&T 증권 본사 ...` (offset 1476) — H&T present
- `한미증권 내부 시스템에 SW인베스트먼트 법인 전용 VIP 예외 승인선(Exception Lane)을 개설 완료했습니다.` — 한미증권 inside the same chapter
- `[속보] 이란, 우라늄 농축 전면 재개 공식 선언.` — re-aired event token
- `2006년 2월 28일.` — date moved

### G. Stage3 blueprint pre-contamination check (ep9)

```sql
SELECT data FROM blueprints WHERE ep_num=9;
```

```text
blueprint ep9 contains 이란     : 4 times
blueprint ep9 contains 우라늄   : 0 times
blueprint ep9 contains 2월 28   : 6 times
blueprint ep9 contains 2월 1    : 1 times
blueprint ep9 contains H&T      : 0 times          ← absent at Stage3
blueprint ep9 contains 한미증권 : 6 times          ← already wrong at Stage3
blueprint ep9 contains VIP      : 6 times
blueprint ep9 contains 15억     : 2 times          ← capital downgraded at Stage3
blueprint ep9 contains 23억     : 0 times          ← canonical capital absent
blueprint ep9 contains 20억     : 0 times
```

The Stage3 blueprint for ep9 already encodes "한미증권" 6 times and never mentions "H&T 증권", and already encodes the downgraded "15억" capital. Stage4 manuscript writers partially overwrite the institution name back to "H&T" in 4 places but leave one "한미증권" through, and they replay "이란 우라늄 농축 재개" on 2월 28 as written by Stage3.

### H. Settled fact ledger sample

```python
ep4 settlement.capital = 2,000,000,000   ('SW인베스트먼트 법인 설립 완료, WTI 원유 선물 20억 풀베팅 진입 완료')
ep5 settlement.capital = 2,300,000,000   ('총자산 23억 달성, ... 증권사 시스템 장악 시작')
ep7 settlement.capital = 2,300,000,000
ep8 settlement.capital = 2,300,000,000
```

So the canonical FactLedger value at Stage4 ep9 entry is 23억 (since ep5). The rejected ep9 attempts wrote 15억, matching the Stage3 blueprint text rather than the settled FactLedger.

## Findings

1. **Artifact truth is clean for ep4-ep9.** Every Stage4 artifact file decodes as UTF-8, has reasonable size, and has no `U+FFFD`. There is no encoding-level corruption to chase. (See section C.)
2. **Stage4 attempt rows in DB match the handoff doc exactly.** The 15 ep4-ep9 attempt rows in `stage_attempts` (session `20260427_070604`) reproduce the verdict ladder claimed in `gcp-iam-5arc-live-run-handoff-current.md:81-88`. The handoff is faithful to DB state. (Section B.)
3. **Director PASS is being downgraded by post-select on continuity conflict.** Every POST_SELECT_CONFLICT row in this sample carries a `[Conflict-first retry] post-select hard conflict invalidated the provisional PASS` prefix in `reject_reason`, and the matching `director_selections` rows show an initial `PASS` or `PASS_WITH_FIX` for the same round. The post-select gate is doing its job; the upstream layer let conflicting text through. (Section E.)
4. **Four named bug shapes in #58 are all observable in artifact truth, not just Director rationale.**
   - Institution name drift (`H&T 증권` ↔ `한미증권`) — Director rationale ep5/ep7/ep8/ep9 + raw token grep inside ep9 att1 manuscript shows both names co-existing.
   - Duplicated continuation beat (already-completed actions written as new) — Director rationale ep4/ep9 att2 + token grep shows VIP 예외 승인선 / 가죽 노트 narrated as "first time".
   - Date drift / event timeline collision — Director rationale ep6 (4월 instead of 2월) and ep9 (2월 28일 vs 2월 1일) + ep9 manuscript explicitly carries "2006년 2월 28일".
   - Prior-failure replay of headline event — Director rationale ep7 / ep9 + ep9 manuscript explicitly carries the 이란 우라늄 농축 재개 newsflash that Stage4 ep5 already settled.
5. **At least one bug shape pre-exists in the Stage3 blueprint, not Stage4 generation alone.** Blueprint ep9 contains 한미증권 6 times and zero `H&T`, plus the wrong 15억 capital. Stage4 partly corrects this in some scenes but leaks one 한미증권 and the downgraded capital through. This points at Stage3-to-Stage4 lineage as a real co-conspirator, not just Stage4 hallucination. (Sections F-G-H.)
6. **DB `content_hash` for some rows does not match the file `sha256` of the artifact_path it points to.** 4 of 15 rows mismatch. Sibling artifact files in the same attempt dir share an identical sha256, so it is not a wrong-file-picked collision. The hash appears to be computed against a normalized text representation rather than the artifact bytes, but this report does not verify the producer; it is flagged as a finding. The implication for #58 is that DB content_hash is not a sound oracle for "did this episode reproduce text from earlier?" duplicate-text detection. (Section D.)

## Root-Cause Candidates

These are candidates supported by the artifact-truth and metadata-truth evidence in this report. They are not asserted as the single root cause.

1. **Stage3 blueprint inherits or generates stale entity tokens for institution name and capital figure**, then the contaminated blueprint is consumed by Stage4. Evidence: ep9 blueprint contains 한미증권 6x and 0x H&T; ep9 blueprint contains 15억 not 23억. (Stronger probability for institution drift; medium for capital drift since 15억 may be a Stage3-side leverage explainer.)
2. **The settled FactLedger (capital=23억 since ep5) is not aggressively projected into the Stage4 candidate writer prompt**, so writer text drifts back to the leverage staging value. Evidence: settlement.capital is 23 since ep5, but Stage4 ep6 / ep9 candidates wrote 15.
3. **The "history beat" register (which prior-episode events have already aired) is not strict enough to suppress re-airing**, evidenced by 이란 우라늄 농축 재개 being re-aired at ep7 and ep9 after airing at ep5, and by VIP 예외 승인선 / 가죽 노트 being narrated as new at ep9 after airing earlier.
4. **Cross-stage hash anchoring is partially decoupled from artifact bytes**, which weakens any duplicate-text detector that assumes `content_hash` equality across episodes implies identical text. (Implication for any future regression that relies on hashing.)

## Regression / Test Candidates

Test ideas only. T08 owns concrete test design.

1. **`test_stage3_blueprint_institution_token_carryover`** — for an N-episode arc where Stage3 carries an institution name in the FactLedger, assert the produced blueprint text contains only the canonical token and not legacy variants. Fixture trip is the 한미증권↔H&T 증권 case.
2. **`test_stage4_post_select_no_replay_of_aired_headline_event`** — given a settled "이미 보도된 사건" registry from prior episodes, the Stage4 candidate must not re-air the same event token on a new date in the same arc. Direct seed for ep5/ep7/ep9 사례.
3. **`test_stage4_post_select_no_repeat_of_completed_action_beat`** — `VIP 예외 승인선 개설`, `가죽 노트 다음 투자처 기록` style "completed action" entries must trigger POST_SELECT_CONFLICT if narrated as first-time in a later episode. ep4 att1 + ep9 att2 already make this a natural fixture.
4. **`test_stage4_capital_value_alignment_with_settled_factledger`** — Stage4 candidate must align numeric capital figures with `settlement.capital` from the latest settled episode rather than with the leverage-staging value in the current episode blueprint.
5. **`test_artifact_hash_matches_db_content_hash_in_strict_mode`** — guardrail-style test: optionally verify that DB `content_hash` for a `stage_attempts` row equals sha256 prefix of the file at `artifact_path`. If product intent is normalized hashing, the test should pin the normalization function so that future drift is visible.

## Dependencies On Other Terminals

- **T01 current-run forensics**: T09 reuses the same DB and session id; T01's findings on attempt rows should be consistent with section B here. If T01 inspects different sessions or other Stage4 episodes, the union should remain coherent.
- **T02 post-select conflict route**: T09 only sees `[Conflict-first retry] post-select hard conflict invalidated the provisional PASS` from the Director rationale. T02 should confirm whether that prefix is rendered by `stage4_postselect_runtime` and how it is normalized into `failure_category=POST_SELECT_CONFLICT`.
- **T03 Stage3-to-Stage4 handoff**: directly tied to finding 5 (blueprint pre-contamination). T03 should explain how 한미증권 entered ep9 blueprint and whether ordinal indexing / source lineage failed.
- **T04 continuity authority carriers**: must answer whether the "settled FactLedger" projection (capital=23억) is actually wired into Stage4 candidate prompts.
- **T05 memory/cache side effects**: `context_cache_attempts` is at 211 rows in this DB. T05 should rule whether stale Stage3 ep9 prompt content (with 한미증권) was cached and reused beyond the round in which it was supposed to be invalidated.
- **T06 retry hydration / prior-failure replay**: directly tied to finding 4 (ep9 att1 already named the same contradiction set ep5 named). T06 should rule whether the second ep9 attempt (att2) hydrated text from att1 or rebuilt clean.
- **T07 context-cache lineage**: depends on T05 and T03; if blueprint cache key did not invalidate when FactLedger capital advanced from 20억 to 23억, the duplicate-event beat is partly cache-driven.
- **T08 regression gap design**: should consume the four bug-shape fixtures described in this report and the sample ep9 contradictions as concrete fixture seeds.
- **T10 synthesis**: T09 supports a Stage3-handoff + post-select-detection-strong + factledger-projection-weak shape. T10 should weigh that against T03/T04/T07 conclusions.

## Open Questions

1. **What hash function and what input bytes produce DB `content_hash`?** 4/15 rows mismatch sha256 of the artifact bytes. The hash is likely computed against a normalized text, but the producer was not verified in this report.
2. **Is `final_manuscript__C.txt` the same content the manuscripts table stores for ep5?** Manuscript ep5 in DB has `length(content)=7221` (chars) / `len_utf8=17171 bytes` / `sha256=663e3ab468b6`, while `final_manuscript__C.txt` is 17309 bytes / `sha256=81db5a1134bc`. Close but not identical — implies a final post-trim or header strip happens between artifact write and `manuscripts` write. Worth confirming for hash-anchored regression tests.
3. **Is the "이란 우라늄 농축 전면 재개" event that gets re-aired in ep9 actually the same event Stage4 ep5 settled, or a deliberate "same crisis, second wave" Stage3 design?** Director rationale labels it a History Conflict; Stage3 blueprint ep9 has the 2월 28일 anchor 6 times. If Stage3 intended a second-wave news beat, the failure is description-level (writer worded it as the first announcement); if Stage3 unintentionally re-aired, the failure is blueprint-level. T03 should resolve.
4. **Is the capital=15억 figure inside ep9 blueprint a leverage-staging value (e.g. "원금 15억 + 8억 MMF") that was misinterpreted by the writer as total capital?** ep5 settlement explicitly says `15억 투자, 8억 MMF 보관`. If yes, the Stage3 blueprint may not be wrong, only ambiguous. T04 / T08 should consider asserting on `total_capital` vs `deployed_capital` semantically.
5. **Is `한미증권` a residual from an earlier project iteration whose context was cached and bled across?** `H&T` is the canonical token throughout ep1-ep8 manuscripts. Where is the 한미증권 token first introduced into Stage3 prompts? T05/T07 territory.

## Closure Recommendation

- Treat this report as artifact-truth confirmation, not a fix recommendation. The handoff doc's behavioral summary at line 81-88 is reproducible from raw DB rows and from rejected manuscript text.
- The four bug shapes #58 names are all observable in artifact truth at the ep4-ep9 sample. Two of them (institution drift, capital drift) are already encoded in the Stage3 blueprint, which means this is a Stage3 ↔ Stage4 carryover problem and not a Stage4-only writer hallucination.
- Stage4 post-select gate is detecting these conflicts and recovering in 2-4 attempts; ep9 has not recovered within the 2 attempts captured before the operator-stop, so the gate is correct but the upstream contamination is too frequent.
- Recommend the merge step (T10 + later) treat finding 5 (Stage3 blueprint pre-contamination of ep9 with 한미증권 and 15억) as the most actionable lead, with T03 and T04 as the natural deepening lanes.
- Do not promote this report into an execution SSOT. Do not claim #58 root cause from this evidence alone. Do not restart the live run.
- Estimated investigation confidence for the artifact-truth / metadata-truth claims in sections A-D: ~95%. Estimated confidence for the narrative-truth contradiction-shape claims (sections E-H): ~92% (Director rationale is single-source per row, but token grep on the rejected manuscript directly confirms the same shapes for the ep9 sample).
