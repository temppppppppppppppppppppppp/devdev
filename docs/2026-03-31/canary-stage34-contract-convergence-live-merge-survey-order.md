Date: 2026-03-31
Status: draft-live-run-pending (3-pass audited survey order)
Document Type: live-merge survey order
Canonical Path: `docs/2026-03-31/canary-stage34-contract-convergence-live-merge-survey-order.md`
Temp Mirror Path: none
Audience: parallel survey operator
Mode: `ROL live-merge`
Live Run Status Snapshot:
- project: `canary_0_1_stage34_ep14_cw_hierarchy`
- current phase: `Stage 3 Blueprint generation in progress`
- current position: `EP10 Blueprint generation`
- designed frontier: `Arc 3 complete, BP/manuscript through EP9 already present`
- backlog target: `S3->14 / S4->14`
- current loaded state: `WorldState EP9`, `FactLedger EP9`
Scope:
- active canary run과 병행되는 Stage 3/4 contract-convergence bounded survey
- context hierarchy, Director contract, retry convergence, persistence continuity 한정
- canary 종료 후 post-run merge audit까지 고려한 조사 오더
Excluded Scope:
- repo-wide global survey
- broad Stage 0/1 refactor
- immediate code patch
- final closure claim while the run is still active
- `docs/temp/` execution SSOT mirror creation
Evidence Basis:
- `docs/implementation/live-run-merge-survey-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
- `docs/2026-03-27/frontier-lag-soak-canary-wave1-execution-ssot.md`
- `scripts/run_auto_frontier_lag_harness.py`
- `scripts/run_stage34_canary.py`
- operator-provided live run status snapshot from the current canary session
Side-Effect Coverage:
- code edits: excluded
- temp queue mutation: excluded while run active
- raw evidence capture: allowed
- final execution SSOT creation: deferred until run terminal state

# Canary Stage34 Contract-Convergence Live-Merge Survey Order

## 1. Intent

이 문서는 canary가 아직 실행 중인 상태에서, 별도 터미널의 read-only 조사자가 따라야 할 bounded live-merge 조사 오더다.

이번 조사의 목적은 새 문제를 넓게 찾는 것이 아니라, 이미 진행 중인 canary가 증명하려는 핵심 주제인 아래 네 가지를 구조적으로 검증하는 것이다.

1. context hierarchy authority가 실제 런타임에서 섞이지 않는가
2. Director contract가 retry lane에서 실행 가능한 계약으로 내려오는가
3. retry / patch / regenerate / reroute가 수렴 경로를 유지하는가
4. persistence 결과가 다음 화 입력 컨텍스트와 정합하게 이어지는가

## 2. Operating Rule

이 조사는 `ROL live-merge` 모드다. 즉 `static survey + live run evidence capture + post-run merge audit`의 3-lane 운영으로 이해해야 한다.

중요한 제한은 다음과 같다.

- canary가 도는 터미널은 건드리지 않는다
- 조사자는 별도 터미널에서 read-only로만 움직인다
- run이 끝나기 전에는 final resolution claim을 저장하지 않는다
- mid-run mismatch는 provisional hypothesis로만 남긴다
- `docs/temp/` mirror나 closure 문서는 run 종료 후에만 만든다

## 3. Current Live Baseline

현재 라이브 기준점은 아래와 같다.

- boot 완료
- 프로젝트 `canary_0_1_stage34_ep14_cw_hierarchy` 정상 로드
- Arc 3개 설계 완료
- Blueprint와 원고는 EP9까지 존재
- 현재 실행 지점은 `EP10 Blueprint 생성`
- semantic context 길이 보고는 약 `6,151자`
- 상태 기준점은 `WorldState EP9`, `FactLedger EP9`

이 baseline은 operator-provided snapshot이므로, 조사자는 별도 터미널에서 raw evidence와 비교하되, 충돌이 생기면 completed live evidence를 더 높은 권한으로 취급한다.

## 4. Survey Boundaries

이번 조사 범위는 Stage 3과 Stage 4의 contract-convergence에 한정한다.

포함:

- Stage 3 blueprint generation -> validate gate
- Stage 4 writer ensemble -> director interview -> retry routing
- context builder의 계층형 주입
- director verdict / fix_scope / repair_scope / fix_pack 계열
- stage_attempts / director_selections / episode_bible / world_state / fact_ledger 연결성
- canary harness의 live evidence capture 및 post-run analysis seam

제외:

- unrelated canary/dashboard work
- broad benchmark lane
- global model policy redesign
- 새 orchestration engine 제안
- 코드 수정

## 5. Core Survey Questions

조사자는 아래 네 가지 질문에만 답하면 된다.

### Q1. Context Hierarchy

- 상위 제약과 하위 문맥의 권한 순서가 무너지지 않는가
- `world_state`, `fact_ledger`, `episode_bible`, `stage_attempts`, `current blueprint`가 writer 입력으로 들어갈 때 역할이 섞이지 않는가
- retry pathology나 previous attempt 정보가 current blueprint authority를 오염시키지 않는가

### Q2. Director Contract

- Stage 3/4에서 `final_verdict`, `fix_scope`, `repair_scope`, `authoritative_fix_scope`, `fix_pack`이 실제 runtime lane으로 연결되는가
- `PASS_WITH_FIX`가 local patch 가능한 계약으로 유지되는가
- invalid or blank scope contract가 fail-closed 되는가

### Q3. Retry Convergence

- `PASS_WITH_FIX -> local patch -> re-audit` 경로가 실제로 수렴하는가
- `REJECT -> retry routing` 이후 `inplace`, `reduced regenerate`, `full regenerate`, `blueprint regenerate`, `full rewrite reroute`가 의도대로 선택되는가
- repeated plateau나 pathology repeat가 local retry를 계속 늘리는 대신 상위 재생성으로 escalate되는가

### Q4. Persistence Continuity

- PASS 후 `episode_bible`, `world_state`, `fact_ledger`, `stage_attempts`, `director_selections`가 기록되는가
- 그 기록이 다음 화 context rebuild와 연결되는가
- 저장 truth와 prompt truth가 어긋나는 seam이 보이지 않는가

## 6. Allowed Outputs During The Run

run이 active인 동안 허용되는 산출물은 아래뿐이다.

- preflight watchlist
- raw evidence txt/json
- sink map
- bounded hypothesis note
- live-run evidence manifest
- draft post-run merge skeleton

허용되지 않는 산출물:

- final closure note
- final survey conclusion
- execution SSOT mirror in `docs/temp/`
- queue cleanup decision
- resolved/regressed 선언

## 7. Evidence Collection Checklist

조사자는 아래 evidence를 우선 수집한다.

### Static Read-Only Evidence

- Stage 3 validate gate owner
- Stage 4 interview / pass-fix / retry owner
- context builder tier assembly seam
- post-pass persistence seam
- canary harness analysis seam

### Live Evidence During Run

- session log tail
- current poll snapshots
- blueprint artifact creation 여부
- draft artifact creation 여부
- `stage_attempts` 증가 패턴
- `director_selections` 증가 패턴
- runtime audit summary 변화
- prompt-blocked 여부

### Post-Run Merge Inputs

- completed worker result
- canary harness analysis json
- stage3/stage4 sink alignment summary
- relevant DB row snapshots
- persisted artifacts on disk

## 8. Recommended Working Notes Structure

조사자는 메모를 다음 네 묶음으로 유지한다.

1. `hierarchy_authority_watchlist`
2. `director_contract_watchlist`
3. `retry_convergence_watchlist`
4. `persistence_continuity_watchlist`

각 메모에는 아래만 남긴다.

- evidence
- hypothesis
- pending live confirmation

해결 선언이나 severity 확정은 run 종료 후 merge audit에서만 한다.

## 9. Post-Run Merge Procedure

run이 terminal state에 들어가면 다음 순서로 merge audit를 수행한다.

1. pre-run static watchlist를 다시 읽는다
2. live-run raw evidence를 terminal snapshot 기준으로 정리한다
3. Stage 3/4 static seam을 completed evidence와 다시 대조한다
4. provisional hypothesis를 `confirmed / contradicted / inconclusive`로 분류한다
5. action-bearing finding이 있으면 그때 execution SSOT 생성 여부를 결정한다
6. human-facing merged audit는 3-pass 후 confidence 95% 이상에서만 final save 한다

## 10. Deliverable Shape

이번 조사 턴의 권장 산출물은 아래다.

- `docs/YYYY-MM-DD/canary-stage34-contract-convergence-preflight-watchlist.md`
- `docs/YYYY-MM-DD/canary-stage34-contract-convergence-live-run-evidence-manifest.md`
- `docs/YYYY-MM-DD/canary-stage34-contract-convergence-post-run-merge-audit.md`

주의:

- 첫 두 문서는 run 중에도 생성 가능
- `post-run-merge-audit`는 run 종료 전 final claim으로 저장하지 않는다
- execution SSOT가 필요해도 run 종료 후 merge audit 다음이다

## 11. Operator Prompt

아래 문구를 병렬 조사자에게 바로 전달해도 된다.

```text
ROL live-merge로 진행.
현재 canary_0_1_stage34_ep14_cw_hierarchy가 Stage 3 EP10 Blueprint 생성 중이므로, canary 터미널은 건드리지 말고 별도 터미널에서 read-only bounded survey를 수행.

범위는 Stage 3/4 contract-convergence 한정:
1) context hierarchy authority
2) director contract executability
3) retry convergence
4) persistence continuity

run active 중에는 raw evidence, watchlist, hypothesis만 남기고 final resolution claim은 금지.
run 종료 후 static survey + live evidence merge audit로 confirmed / contradicted / inconclusive를 정리.
```

## 12. 3-Pass Audit Record

- Pass 1 완료
  live-run active 상태에서 필요한 문서 타입을 `final survey`가 아니라 `live-merge survey order`로 제한했고, canary를 건드리지 않는 별도 터미널 read-only 조사로 범위를 명시했다.
- Pass 2 완료
  live-run harness 규칙, temp queue 규칙, canary SSOT, 현재 harness 상태를 대조했다. soak override contract는 이미 일부 구현돼 있으므로 이번 문서는 broad canary SSOT가 아니라 Stage 3/4 contract-convergence bounded survey order로 좁혔다.
- Pass 3 완료
  조사자가 바로 실행할 수 있도록 intent, 질문, evidence checklist, 금지사항, post-run merge 순서, operator prompt를 한 문서에 모았다.
- Confidence: 97%
