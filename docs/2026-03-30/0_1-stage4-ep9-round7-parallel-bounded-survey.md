# 0_1 Stage4 EP9 Round7 Parallel Bounded Survey

Date: 2026-03-30
Status: final
Canonical Path: `docs/2026-03-30/0_1-stage4-ep9-round7-parallel-bounded-survey.md`
Doc Type: bounded survey
Topic Slug: `0_1-stage4-ep9-round7`
Question:
- 왜 `0_1` 프로젝트의 Stage 4 `제9화`가 `7차 면담`까지 진입하는가?

Commit State:
- Baseline Commit: `229b85c655c32366818c2278462b51f3ad490913`
- Baseline Dirty Summary: `dirty: tracked changes in 0_temp.txt, stage4 runtime files, project 0_1 logs/db, tests; multiple untracked docs/scripts/artifacts already present`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

Temp Queue Context:
- `docs/temp/execution-roadmap.md` present
- existing Stage 4 related execution SSOT mirrors already active
- this document is survey-only and does not create or refresh any temp execution mirror

Source Docs:
- `docs/2026-03-29/stage4-retry-loop-compression-full-survey.md`
- `docs/2026-03-28/stage4-feedback-windowing-full-survey.md`
- `docs/2026-03-29/stage4-provider-fallback-observability-gap-full-survey.md`

Evidence Artifacts:
- `docs/2026-03-30/0_1-stage4-ep9-round7-parallel-evidence.json`
- `projects/0_1/project_data.db`
- `projects/0_1/logs/session/ui_events.jsonl`
- `projects/0_1/logs/session/decisions.jsonl`
- `projects/0_1/logs/episode_production.jsonl`
- `projects/0_1/logs/artifacts/stage4/ep_0009/`

Navigational Only Inputs:
- `0_temp.txt`

Included Scope:
- Stage 4 retry budget source
- EP9 live DB rows
- EP9 JSONL/operator log sinks
- EP9 artifact truth
- adjacent prior Stage 4 survey docs

Excluded Scope:
- provider routing redesign
- broad Stage 4 refactor
- blueprint authoring redesign
- immediate code patching
- temp queue realization

## Executive Answer

`제9화`가 `7차 면담`까지 가는 직접 이유는 버그성 무한루프라기보다, 현재 live Stage 4 round budget이 `10`으로 설정되어 있고, EP9의 앞선 `1`~`6`차가 모두 `REJECT`로 닫혔기 때문이다.

핵심 체인은 다음과 같다.

1. Stage 4 오케스트레이터는 live 값 기준 `max_rounds=10`을 읽는다.
2. EP9의 `1`~`3`차는 Director가 사실상 통과 가능한 점수를 냈지만, `strong_advisory_escalation_non_local_fix`와 빈 `patch_targets` 때문에 최종 `REJECT`로 뒤집힌다.
3. `4`차는 `PASS_WITH_FIX`까지 갔지만 patch 재심사에서 `patch_reaudit_fail`로 다시 `REJECT`가 된다.
4. `5`~`6`차도 다시 `strong_advisory_escalation_non_local_fix`로 막힌다.
5. 각 라운드 뒤 `REJECT -> 다음 라운드`가 찍히고, budget이 아직 남아 있으므로 `[Round 7/10]`이 시작된다.

즉 `7차 면담 진입`은 "10회 예산 + 6회 연속 최종 REJECT"의 합성 결과다.

## Pass 1 - Inventory

### Lane A. Code

- `modules/core/stage4_orchestrator.py:519-526`
  - `_get_stage4_max_rounds()`는 `interview_round.max_rounds` 또는 `_threshold("retry.director_max_attempts", 5)`를 읽는다.
- `config/settings/validation.yaml:96`
  - live `retry.director_max_attempts: 10`
- `modules/core/stage4_orchestrator.py:1601-1603`
  - 실제 loop는 `for interview_round in range(_max_rounds)`로 돈다.
- `modules/core/stage4_outcome_runtime.py:461-466`
  - REJECT 시 operator surface에 `"[Round n/max] REJECT -> 다음 라운드"`를 남긴다.
- `modules/core/stage4_interview_round.py:2093-2108`
  - strong advisory escalation이 `PASS_WITH_FIX` 상태여도 local fix contract가 준비되지 않으면 final verdict를 `REJECT`로 강등한다.
- `modules/core/stage4_retry_runtime.py:872-915`
  - non-ready `fix_pack`는 patch lane을 막고 rewrite 경로로 떨어진다.
- `modules/core/stage4_retry_runtime.py:725-733`, `805-816`
  - `PASS_WITH_FIX` patch 재심사 실패 시 `patch_reaudit_fail`로 다시 `REJECT`

### Lane B. DB / Persistence

- project DB path: `projects/0_1/project_data.db`
- authoritative Stage 4 persistence surfaces
  - `stage_attempts`
  - `director_selections`
  - `attempt_raw_rationale`
  - `ui_events`
- EP9 live counts
  - `stage_attempts WHERE stage=4 AND ep_num=9`: `6 rows`
  - `director_selections WHERE stage=4 AND ep_num=9`: `6 rows`
  - `attempt_raw_rationale WHERE stage=4 AND ep_num=9`: `6 rows`
- terminal persistence absence
  - `manuscripts.ep_num=9`: `0 rows`
  - `episode_quality_labels/observations/signals ep_num=9`: `0 rows`

### Lane C. Log / Operator Sinks

- `projects/0_1/logs/session/decisions.jsonl`
  - Stage 4 `ep_num=9` decision rows `6개`
- `projects/0_1/logs/session/ui_events.jsonl`
  - `제9화, 1차`부터 `제9화, 6차` Director 면담 시작이 순서대로 보임
  - `2026-03-30T20:07:52`에 `[Round 6/10] REJECT -> 다음 라운드`
  - `2026-03-30T20:08:13`에 `[7차 면담] Chief Writer 앙상블 생성 중...`
- `projects/0_1/logs/episode_production.jsonl`
  - EP9 attempt records와 gate basis가 round별로 저장됨

### Lane D. Artifact Truth

- artifact folder: `projects/0_1/logs/artifacts/stage4/ep_0009/attempt_01..06`
- `attempt_04`만 patch artifact를 가짐
  - `selected_before_fix__C_asp_correction.txt`
  - `rejected_best__C_inplace_patch.txt`
- hash grouping상 동일 원고 재순환이 관찰됨
  - attempt `02/03/04(selected_before_fix)` 동일 hash
  - attempt `05/06` 동일 hash

### Lane E. Prior Survey Context

- `stage4-retry-loop-compression-full-survey`
  - 기존 extreme retry 사례는 `continuity_firewall/post_select_conflict` 진동이 핵심
- `stage4-feedback-windowing-full-survey`
  - retry feedback snowball risk는 이미 별도 문제군으로 식별됨
- `stage4-provider-fallback-observability-gap-full-survey`
  - provider observability gap이 retry budget을 오염시킬 수는 있으나, 이번 EP9의 1차 설명력은 더 낮음

## Pass 2 - Semantic Classification

### 1. `7차 진입` 자체는 live config 결과다

이 현상은 우선 `max_rounds=10`을 코드가 정상적으로 읽고 있다는 뜻이다. 이전 문서들에서 이미 `retry.director_max_attempts` live 값이 `10`이라는 점이 확인되어 있었고, 이번 EP9 operator log도 `[Round 7/10]`로 정확히 합치한다.

추가로 `config/settings/stage4_policy_digest.json`의 `shadow_mode.max_rounds=8`은 telemetry compare 용도일 뿐 outer loop를 멈추지 않는다. 따라서 "`shadow가 8인데 왜 아직도 더 도느냐`"는 의문이 생길 수 있지만, 실제 control authority는 `retry.director_max_attempts=10` 쪽에 있다.

따라서 "`왜 7차까지 가냐`"의 1차 답은 "`5회 제한`이 아니라 `10회 제한`으로 돌고 있기 때문"이다.

### 2. EP9의 주된 reject family는 `strong_advisory_escalation_non_local_fix`다

EP9의 `1, 2, 3, 5, 6`차는 공통적으로:

- `director_verdict = PASS`
- `final_verdict = REJECT`
- `gate_basis = strong_advisory_escalation_non_local_fix`
- `authoritative_fix_scope = inplace`
- `patch_targets_len = 0`

즉 Director 자체의 선택 품질은 높게 나오지만, advisory escalation 이후 local-fix contract가 성립하지 않아 Python runtime이 최종 verdict를 다시 `REJECT`로 바꾸고 있다.

### 3. `4차`는 다른 실패 family다

`4차`는 유일하게:

- `initial_verdict = PASS_WITH_FIX`
- `patch_targets_len = 2`
- patch artifact 생성

까지 갔지만, 그 후속 재심사 경로에서 `patch_reaudit_fail`로 떨어졌다. 즉 EP9는 "빈 fix_pack 때문에 시작도 못 한 round들"과 "실제 patch를 했지만 재심사에 실패한 round"가 섞여 있다.

### 4. `TF-4 full rewrite 전환`이 반복되어도 loop는 멈추지 않는다

`session/ui_events.jsonl`에는 EP9 session `20260330_193026`에서:

- `19:43:57`
- `19:48:58`
- `20:02:32`
- `20:08:13`

시점에 `[TF-4] patch_targets 연속 부재 -> full rewrite로 전환`이 보인다.

이건 retry lane이 patch를 포기하고 rewrite로 떨어진다는 뜻이지, round budget을 줄이거나 loop를 중단한다는 뜻은 아니다. 그래서 `TF-4`가 떠도 budget이 남아 있으면 다음 round가 계속 열린다.

### 5. artifact layer에서는 "완전 무진전"만 있는 것은 아니다

hash truth를 보면:

- attempt `02/03/04(selected_before_fix)`는 동일 hash
- attempt `04 rejected patch`는 별도 hash
- attempt `05/06`는 또 다른 동일 hash

즉 EP9는 완전히 다른 원고가 매번 나오기보다는, 몇 개의 원고 덩어리가 round 사이에서 재활용되거나 국소 수정 후 다시 되돌아오는 패턴을 보인다.

이는 "라운드는 늘어나는데 실질 탐색 폭은 좁다"는 신호다.

### 6. advisory의 일부는 artifact keyword 부재만으로 설명되지 않는다

blueprint_0009와 attempt 05/06 rejected manuscript를 직접 UTF-8 read-back한 결과, 아래 anchor는 모두 존재한다.

- `로스터리 카페`
- `대표실`
- `한미증권 본사 파생상품 데스크`
- `박성호 PB`
- `에콰도르`

따라서 이번 advisory/NpcDrift의 일부는 "키워드가 빠져서"가 아니라, 장면 배치/역할 해석/관계 서술 같은 semantic classification 문제일 가능성이 높다. 즉 경고가 모두 허상이라고 단정할 수도 없지만, 단순 누락 경고로 축약해서도 안 된다.

## Side-Effect Map

Applicable categories only:

- file writes
  - `projects/0_1/logs/artifacts/stage4/ep_0009/attempt_01..06`
- DB writes
  - `director_selections`
  - `stage_attempts`
  - `attempt_raw_rationale`
  - `ui_events`
- JSONL/log sinks
  - `logs/session/decisions.jsonl`
  - `logs/session/ui_events.jsonl`
  - `logs/episode_production.jsonl`
- operator-visible output
  - `Director 면담 시작`
  - `REJECT -> 다음 라운드`
  - `[TF-4] patch_targets 연속 부재 -> full rewrite로 전환`
  - `[7차 면담] Chief Writer 앙상블 생성 중...`
- rollback/recovery/retry
  - `patch_reaudit_fail`
  - `TF-4 full rewrite fallback`
- cache/global state
  - not directly proven as primary driver in this survey
- config/env mutation
  - no live mutation observed

## Pass 3 - Execution Consequence

이번 조사 결과만으로 바로 말할 수 있는 운영 결론은 아래와 같다.

### Hard Conclusions

- EP9가 `7차 면담`까지 가는 것은 live round budget이 `10`이기 때문이다.
- EP9의 앞선 `6`개 round는 모두 최종적으로 `REJECT`로 닫혔다.
- REJECT family는 주로 `strong_advisory_escalation_non_local_fix`, 예외적으로 `patch_reaudit_fail`이다.
- `TF-4 full rewrite`는 retry lane 선택 변경일 뿐, loop 중단 조건이 아니다.
- EP9는 아직 `manuscripts`나 episode quality tables에 terminal success row를 남기지 못했다.

### Medium-Confidence Conclusions

- 이번 case는 prior `retry-loop-compression` 문서의 `continuity_firewall/post_select_conflict` 진동과 완전히 동일한 재발은 아니다.
- 이번 case의 더 직접적인 pain point는 `advisory escalation -> non-ready local fix contract -> REJECT 재개방` 체인이다.
- advisory/NpcDrift의 일부는 실제 semantic mismatch일 수 있지만, blueprint/manuscript 양쪽에 주요 anchor가 다 살아 있으므로 경고의 precision 자체도 별도 점검 가치가 있다.

### Suggested Next Patch Investigation Order

survey-only 기준 다음 실전 조사 우선순위:

1. `strong_advisory_escalation_non_local_fix`에서 `fix_pack`이 왜 빈 배열로 끝나는지
2. `attempt_04` patch path가 `PASS_WITH_FIX` 이후 왜 `patch_reaudit_fail`로 닫히는지
3. repeated same-hash manuscript가 나올 때 round를 더 쓰는 게 유의미한지
4. `NpcDrift/location` advisory가 blueprint truth 대비 과민한지

## Open Questions

- EP9의 advisory 중 어느 항목이 진짜 서사 불일치이고 어느 항목이 과민 탐지인지, 이 survey는 전량 판정하지 않았다.
- `attempt_raw_rationale`가 live ep9에서 `advisory_warnings_raw`만 보존하는데, patch 재심사 실패 상세가 별도 payload로 남아야 하는지 여부는 추가 관찰이 필요하다.

## 3-Pass Audit Record

### Pass 1. Structure and Scope

- bounded survey로 고정
- active temp queue 존재를 명시
- included/excluded scope를 질문 중심으로 축소
- execution SSOT 미생성 방침 명시

### Pass 2. Evidence and Consistency

- live code, project DB, JSONL, artifact hashes, prior surveys를 교차 확인
- `0_temp.txt`는 navigational only로 격하
- `7차 진입` 근거는 config, code loop, UI log 세 축으로 고정
- terminal success absence는 DB row absence로 확인

### Pass 3. Execution and Readability

- answer-first 구조로 정리
- next patch seam을 4개로 제한
- queue authority와 구현 착수는 일부러 분리

Final Confidence:
- `96%`

Confidence Notes:
- core claim "`왜 7차까지 가냐`"는 high confidence
- advisory precision 자체에 대한 평가는 medium confidence
