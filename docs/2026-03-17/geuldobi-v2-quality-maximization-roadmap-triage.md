# Geuldobi V2 Quality Maximization Roadmap Triage

Date: 2026-03-17
Status: final
Canonical Path: `docs/2026-03-17/geuldobi-v2-quality-maximization-roadmap-triage.md`
Document Type: triage note
Commit State:
- Baseline Commit: `2352b26a293ac330a0ff24da320363f9abdbbba1`
- Baseline Dirty Summary: `dirty: stage-pipeline lane1~3 code/tests/docs edits, temp execution mirror deletions, 1 runtime log, 1 untracked roadmap draft; preserve as-is`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Seed:
- `docs/roadmap-v2.md`

## 1. Intent
- normalize `docs/roadmap-v2.md` before launching the repo-wide deep survey
- remove duplicate or superseded seeds
- avoid spending `10 terminals` on low-ROI or out-of-scope ideas
- attach logging requirements only where lack of observability would make the survey or later implementation invalid

## 2. Triage Rule
Each roadmap seed must be placed into one of five buckets.

| Bucket | Meaning | Action |
| --- | --- | --- |
| `already-landed` | core semantics already landed in code | validate in live run or merged survey; do not keep as fresh invention item |
| `keep` | still high-ROI and survey-worthy | keep as a primary survey theme |
| `merge` | same root problem as another stronger theme | fold into the stronger theme and do not track separately |
| `defer` | plausible but too expensive/speculative before live-run evidence | keep as later option, not front-line survey priority |
| `out-of-scope` | outside `v2.0.0 closure` or current survey target | exclude from this cycle |

## 3. Triage Matrix

| Seed | Disposition | Reason | Survey Handling |
| --- | --- | --- | --- |
| Phase 1 `A-1 CW 컨텍스트 계층화` | `already-landed` | lane-1 core already landed | validate under live run; do not re-invent |
| Phase 1 `B-1 Director 판단 핵심 분리` | `already-landed` | lane-2 core already landed | validate under live run |
| Phase 1 `B-3 PASS_WITH_FIX 범위 축소` | `already-landed` | lane-3 core already landed | validate fail-closed behavior under live run |
| Phase 1 `B-4 Retry 예산 명시화` | `already-landed` | lane-3 added budget axes and retry semantics skeleton | validate clarity and routing usefulness under live run |
| `A-2 Few-shot 성공 예시 주입` | `defer` | content-heavy and hard to evaluate before upstream/context audit finishes | revisit only if prompt/context fixes are insufficient |
| `A-3 만족도 가이드 상위 이동` | `merge` | prompt-order issue, not a standalone lane | fold into `테마 N` |
| `A-4 씬 페이싱 자동 배분` | `merge` | overlaps with blueprint structure quality and prompt execution guidance | fold into `테마 L` + `테마 N` |
| `A-5 Arc→에피소드 목적 문장 주입` | `merge` | upstream intent-handoff problem, not a separate lane | fold into `테마 D` + `테마 L` |
| `A-6 CW 2단계 호출` | `defer` | large cost and architecture expansion before proving simpler fixes insufficient | keep off the front line |
| `A-7 NPC 대사 샘플 뱅크` | `defer` | content authoring burden and genre sensitivity are high | revisit after prompt/input audit only if voice remains weak |
| `B-1 피드백 절삭 한도 완화` | `merge` | belongs to repo-wide truncation and information-loss survey | fold into `절삭 하드코딩 전수조사` + `테마 H` |
| `B-2 모순 구조화 전달` | `merge` | lane-3 Fix Pack and lane-2 semantics already cover the same direction | validate/log instead of treating as a new lane |
| `B-3 재시도 횟수별 피드백 에스컬레이션` | `merge` | retry-policy tuning should follow live-run evidence, not pre-survey speculation | fold into lane-3 validation and `테마 J` |
| `B-4 Director→CW 수정 지시서 포맷` | `merge` | same root as structured repair contract already landed | validate Fix Pack quality instead |
| `B-5 피드백 손실 감사 로그` | `keep` | this is an observability gap, not a cosmetic add-on | attach as logging requirement, not a separate product feature |
| `C-1 Pre-flight Director` | `defer` | costly, architecture-heavy, and easy to overbuild before evidence | only revisit if upstream/context fixes fail |
| `C-2 실패 패턴 DB → CW 사전 주입` | `keep` | existing `failure_learner` suggests a narrow, low-cost win may already exist | survey current Stage 4 gap first |
| `C-3 CW 자체 체크리스트 삽입` | `merge` | prompt-structure and constraint-block problem | fold into `테마 N` |
| `절삭 하드코딩 전수조사` | `keep` | repo-wide, measurable, and high-ROI | primary survey theme |
| `테마 D Stage 2→3→4 정보 소실 복구` | `keep` | directly tied to manuscript quality and upstream intent survival | primary survey theme |
| `테마 G Director 사전 경고 체계` | `keep` | narrow enough to survey and may already have infrastructure leverage | treat as `failure-learning reuse` audit, not a grand new subsystem |
| `테마 H 보조 검증 LLM 원고 절삭 문제` | `keep` | likely high false-negative source with low conceptual ambiguity | primary survey theme |
| `테마 I Taxonomy/중간단계 소실` | `keep` | cross-cut semantic-loss theme with strong process impact | primary survey theme |
| `테마 J 비용/지연 중복` | `keep` | cost and duplicate analysis can materially reorder later work | primary survey theme |
| `테마 K 장기 연재 품질 열화` | `keep` | repo-wide quality ceiling issue, not a local Stage 4 bug | primary survey theme |
| `테마 L 상류 설계 품질` | `keep` | upstream quality can dominate downstream fixes | primary survey theme |
| `테마 M 장르별 성능 편차` | `out-of-scope` | roadmap itself marks it outside `v2.0.0` | exclude from this cycle |
| `테마 N 프롬프트 구조 최적화` | `keep` | still high-ROI after lane-1~3 and absorbs several smaller prompt ideas | primary survey theme |

## 4. Primary Survey Set After Triage
The repo-wide deep survey should treat these as the front-line themes:

1. `절삭 하드코딩 전수조사`
2. `테마 D Stage 2→3→4 정보 소실`
3. `테마 G failure-learning / 사전 경고 재사용성`
4. `테마 H 보조 검증 LLM 가시성`
5. `테마 I taxonomy and intermediate-step loss`
6. `테마 J cost / latency duplication`
7. `테마 K long-run degradation`
8. `테마 L upstream Stage 2/3 design quality`
9. `테마 N prompt structure optimization`

Already-landed lane items should be handled as:
- live-run validation targets
- regression-watch targets
- observability adequacy checks

## 5. Logging Attachment Rule
Logging is required only when the idea cannot be judged reliably from final outputs plus static code reading.

Attach logging requirements when one or more of these are true:
- the problem is hidden inside routing, truncation, or fallback behavior
- the decision boundary is threshold-driven or multi-stage
- the claim depends on what information survived to the next stage
- the claim depends on retry path, repair scope, or model-routing economics
- the claim depends on long-run drift, sampling, FIFO eviction, or cache behavior

Do not attach blanket verbose logging for simple static design issues.

## 6. Minimal Logging Packs To Require

### Pack A. Information-Loss Logging
Needed for:
- truncation sweep
- Stage 2→3→4 handoff loss
- advisor visibility gaps

Minimum fields:
- source surface
- pre-trim size
- post-trim size
- dropped item count or dropped line count
- survival summary by tier or field
- destination surface

### Pack B. Repair and Gate Logging
Needed for:
- PASS_WITH_FIX validation
- retry-policy validation
- taxonomy/gate-semantics audit

Minimum fields:
- `director_verdict`
- `final_verdict`
- `gate_basis`
- `repair_scope`
- `fix_pack.target_kind`
- `fix_pack.patch_targets`
- `retry_budget_axes`

### Pack C. Upstream-Intent Survival Logging
Needed for:
- `테마 D`
- `테마 L`

Minimum fields:
- whether key Arc/Blueprint intent fields were present at Stage 2
- whether they survived Stage 3 transformation
- whether they reached Stage 4 prompt inputs
- if dropped, the drop point and representation change

### Pack D. Cost and Duplication Logging
Needed for:
- `테마 J`

Minimum fields:
- stage
- agent or validator name
- model route
- attempt count
- cache hit or miss when available
- token, char, or prompt-size proxy
- duplicated analysis candidate group if detected

### Pack E. Long-Run Degradation Logging
Needed for:
- `테마 K`

Minimum fields:
- tier transition point
- FIFO eviction or sampling count
- entity/history visibility caps triggered
- digest source type
- summary compression count

## 7. Logging Non-Goals
- no repo-wide logging rewrite before the survey finishes
- no dashboard expansion just because a field is interesting
- no second observability authority beside existing JSONL, audit, dashboard, and bridge surfaces
- prefer reusing existing sinks such as:
  - `episode_production.jsonl`
  - `quality_dashboard`
  - `pass_rate_monitor`
  - session decision logs
  - audit-service artifacts

## 8. Consequence For The 10-Terminal Survey
- `T05` must assess whether repair/gate logging is sufficient for lane-1~3 live validation
- `T06` must assess durable log and artifact-truth linkage
- `T07` must assess whether operator-visible surfaces expose the right process state
- `T09` must assess whether prompt/config/model-routing/cost logging is adequate
- `T10` must decide whether a finding is action-bearing partly on logging adequacy, not just behavior gap

## 9. Immediate Operating Consequence
- do not launch the full 10-terminal survey from raw `roadmap-v2.md`
- launch it from:
  - this triage doc
  - the canonical audit-order doc
- treat `merge`, `defer`, and `out-of-scope` seeds as filtered unless new evidence revives them

## 10. Confidence Statement
- estimated confidence in this triage note as an operator document: `96%`
- rationale:
  - it removes obvious duplicates from already-landed lane work
  - it keeps the survey centered on measurable repo-wide quality risks
  - it limits logging expansion to cases where observability is required for validity
- remaining risk:
  - some `defer` items may come back if the live-run shows prompt/context fixes are insufficient
