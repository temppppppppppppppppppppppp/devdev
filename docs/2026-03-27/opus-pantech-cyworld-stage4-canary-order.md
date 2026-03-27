# OPUS Pantech Bounded Stage 4 Canary Order

Date: 2026-03-27
Track: narrative pipeline
Status: active
Scope: single-work OPUS order for `pantech_cyworld_reborn`

## 1. Order Intent

This order fixes the target to `pantech_cyworld_reborn` and asks OPUS to advance exactly one remaining revival-ladder unit.

Current lane truth:
- family: `blockguide`
- entry type: existing `TR + BI` pair revival
- current pair location: **active path** (promoted from `_quarantine` this session)
- smallest remaining unproven step: `bounded Stage 4 canary` (ladder Step 8)

This is not a fresh Planning or fresh TR/BI generation order.

## 2. Non-Negotiable Rules

- UTF-8 only
- read router → family SSOT → revival ladder before doing anything else
- one work, one owner, one unit
- no same-work concurrent editing
- no code or system edits
- do not regenerate TR
- do not redesign BI
- do not modify the active pair files — this is a read-only canary
- this is a canary probe, not a production manuscript run
- do not attempt full-arc or full-work Stage 4 generation

## 3. Canonical Target

- work_id: `pantech_cyworld_reborn`
- BI: `bible/0_bi_pantech_cyworld_reborn.json`
- TR: `treatments/pantech_cyworld_reborn_tr_block_070_draft.json`

These are the promoted active-path files. Quarantine originals are preserved but no longer authoritative.

## 4. Proven Prior Steps

The following steps are already evidenced and should not be re-litigated unless the live files contradict them.

1. Pair consumability survey + repair:
   - `docs/2026-03-26/pantech-cyworld-bi-tr-consumability-survey.md`
   - `docs/2026-03-26/pantech-cyworld-bi-tr-consumability-repair-report.md`
2. TR static audit:
   - `docs/2026-03-27/pantech-cyworld-tr-static-quality-audit.md`
   - verdict: `usable spine but mixed`
3. BI repair:
   - `docs/2026-03-27/pantech-cyworld-bi-repair-note.md`
   - verdict: `pass`
4. Revival canary:
   - `docs/2026-03-27/pantech-cyworld-revival-canary-report.md`
   - verdict: `pass`
5. Revival-stage probe:
   - `docs/2026-03-27/pantech-cyworld-revival-stage-probe-report.md`
   - verdict: `pass`
6. Active promotion:
   - `docs/2026-03-27/pantech-cyworld-promotion-note.md`
   - verdict: `pass` (byte-identical, post-promotion consumability clean)

Interpretation:
- ladder Steps 1-7 are all proven with pass verdicts
- the pair is now an active candidate ready for Stage 4 canary
- this is the final revival-ladder step

## 5. Mandatory Reads

Read these in order:

1. `docs/narrative-router/SSOT_narrative-router-integrated-order.md`
2. `docs/blockguide/SSOT_blockguide-integrated-order.md`
3. `docs/narrative-router/material-revival-ladder-harness.md`
4. `docs/2026-03-27/pantech-cyworld-revival-stage-probe-report.md`
5. `docs/2026-03-27/pantech-cyworld-promotion-note.md`

## 6. Immediate Goal

Execute exactly one bounded `Stage 4 canary` (ladder Step 8) for `pantech_cyworld_reborn`.

The canary must answer:
- does the promoted active pair survive actual manuscript generation through the full Stage 2→3→4 chain?
- does the prose remain scene-grade (장면 수준), not summary-grade (요약 수준)?
- does the genre texture (2006 한국 모바일 전쟁 + 재벌 승계 + 팬택/싸이월드 부활) survive into manuscript prose?
- does the protagonist engine (회귀자 미래지식 기반 판단) still read in prose, not only in metadata?

## 7. Canary Method

### 7.1 Stage 4 Admission

Verify the promoted active pair admits cleanly:
- BI loads from `bible/0_bi_pantech_cyworld_reborn.json`
- TR loads from `treatments/pantech_cyworld_reborn_tr_block_070_draft.json`
- SHA-256 matches promotion note hashes (BI: `7cbbe6ad...`, TR: `d376bfc7...`)
- Stage 2→3→4 pipeline chain completes without intermediate failure

### 7.2 Pipeline Chain

Run the full Stage 2→3→4 chain on a bounded window:
- Stage 2: generate Arc 1 tactical document from BI plot_roadmap (Block 1-10)
- Stage 3: generate Episode 1 blueprint from Arc 1 document + CoreIdentity
- Stage 4: generate Episode 1 manuscript from blueprint + BI + Arc document

This is a single-shot canary — no Director oversight, no ChiefWriter multi-pass, no validation loops. The quality signal is "scene-grade vs summary-grade", not production-ready length.

### 7.3 Manuscript Quality Judgment

Evaluate the generated manuscript on these axes:

| Axis | What to check |
|------|---------------|
| Scene structure | 장면이 ###로 구분되어 있고, 각 장면이 고유 목표·전환점을 갖는가 |
| Dialogue | 실제 인용 대화가 있는가 (요약 서술이 아닌 직접 대사) |
| Sensory markers | 감각 단서가 존재하는가 (시각, 청각, 촉각, 후각 등) |
| Spatial texture | 구체적 장소와 공간 묘사가 있는가 |
| Named characters | 이름이 있는 캐릭터가 등장하고 분리되는가 |
| Character voice | 캐릭터별 말투/어조가 구별되는가 |

### 7.4 Genre-Survival Judgment

These genre anchors must survive into manuscript prose — not just exist in metadata:

| Anchor | What to look for in prose |
|--------|--------------------------|
| 2006~2007 한국 IT 전환기 | 피처폰, 아이폰 전, 통신사 인증, 앱 장터 부재 등 시대 디테일 |
| 팬택 + 싸이월드 이중 부활 | 단말기 + 관계망 결합이 서사의 핵심 엔진으로 작동 |
| 통신사 인증/QA/첫화면/결제 전장 | 기술 병목이 추상 아닌 구체 장면으로 발현 |
| 재벌 승계 압력 | 차우진, 윤재문 등 재벌 내부 정치가 장면에서 읽힘 |
| 회귀자 엔진 | 미래 지식 기반 판단이 행동과 대화로 보여짐, 초능력 설명이 아님 |
| slip-up 의심 | 너무 정확한 미래 예측에 대한 타인의 의심이 장면에서 발현 |

### 7.5 Known Weakness Watch

Revival-stage probe에서 확인된 약화점:
- **slip-up 메타데이터 분리**: regression_hint가 TR 본문이 아닌 regression_ext에 분리 — Stage 4가 이를 장면 안으로 끌어오는지 확인
- **단일 POV**: 1인칭 제한 시점 — 적대자/동맹 내면이 외부 행동으로만 추론되는 한계가 원고에서도 유지되는지 확인
- **숫자 서술 미내재화**: 금액/지분 구체 수치가 원고에 자연스럽게 녹아드는지 확인

## 8. Fixed Creative Constraints

Do not wash out these anchors:

- 2006~2007 Korean IT transition timing
- Pantech + Cyworld dual-revival engine
- telecom certification / QA / first-screen / payment chokepoints
- regression slip-up pressure
- chaebol succession pressure
- capital-structure and audit pressure running in parallel

Canary rule:
- if the generated manuscript drifts into generic business fiction or civic infrastructure abstraction, call that out explicitly
- do not try to repair the drift — report it as a canary finding

## 9. Deliverable

Save exactly one main report:

- `docs/2026-03-27/pantech-cyworld-stage4-canary-report.md`

The report should include:
- active pair paths
- SHA-256 admission verification
- pipeline chain result (Stage 2→3→4)
- manuscript quantitative metrics (char count, scene count, dialogue lines, sensory markers, named characters)
- scene-grade evidence (representative prose excerpts proving scene quality)
- character voice differentiation table
- genre-survival result with prose evidence
- protagonist engine prose moments
- known weakness evaluation (slip-up, POV, number internalization)
- revival readiness assessment
- final verdict: `pass`, `mixed`, or `fail`

Use the same format as `docs/2026-03-27/chaebol-ent-empire-stage4-canary-report.md` for consistency.

## 10. Stop Conditions

Stop immediately and report if any of the following occurs:

- active pair SHA-256 does not match promotion note hashes
- Stage 2→3→4 pipeline chain breaks at any stage
- manuscript generation produces empty or degenerate output
- pair identity becomes ambiguous
- confidence falls below 95% and no smaller bounded next step exists

If the canary produces usable but degraded output (e.g., scene structure present but genre texture washed out), report as `mixed` with specific degradation notes — do not attempt repair.

## 11. Expected Outcome After This Order

- if canary passes: treat `pantech_cyworld_reborn` as an **active blockguide baseline candidate** — the revival ladder is complete
- if canary is mixed: record specific degradation points for future targeted repair
- if canary fails: record failure mode — the pair stays active but is not yet baseline-qualified

## 12. Handoff Format

End with this exact flat report:

```text
work_id: pantech_cyworld_reborn
current_stage: audit_or_repair
finished_unit: bounded Stage 4 canary
changed_files: ...
next_unit: ...
stop_reason: ...
```

## 13. 3-Pass Self Audit

### Pass 1. Contract Alignment

- target is fixed to one `work_id`
- order stays inside router + blockguide + revival-ladder boundaries
- no same-work parallel editing is authorized
- no pair file modification permitted
- this is a read-only canary, not a production run

### Pass 2. Operational Usefulness

- the next unit is singular and concrete: `bounded Stage 4 canary`
- all prior proven steps (1-7) are enumerated so OPUS does not restart the ladder
- deliverable and stop conditions are explicit
- chaebol_ent_empire Stage 4 canary report provides proven format reference
- known weakness watch from revival-stage probe is carried forward

### Pass 3. Integrity

- saved under dated `docs/2026-03-27/`
- UTF-8 only
- no code-edit instructions
- no multi-unit overreach beyond one bounded revival step
- this is the final ladder step — successful canary concludes the revival pipeline

Confidence:
- 97% that `bounded Stage 4 canary` is the correct next OPUS unit for this pair
