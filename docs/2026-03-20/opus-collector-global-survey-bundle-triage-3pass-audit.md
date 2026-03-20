# OPUS Collector Global Survey Bundle Triage — 3Pass Audit

Date: 2026-03-20
Scope: `docs/2026-03-20/opus-collector-*.md` 5개 collector draft
Authority: Codex triage note. Collector draft를 권위 문서로 채택하지 않는다.
Mode: live-code-first re-audit preparation

## 1. Inputs

- `docs/2026-03-20/opus-collector-global-tranche-a-b-macro-runtime-draft.md`
- `docs/2026-03-20/opus-collector-global-tranche-c-domain-agents-draft.md`
- `docs/2026-03-20/opus-collector-global-tranche-d-g-persistence-scripts-draft.md`
- `docs/2026-03-20/opus-collector-global-tranche-e-operator-desktop-ui-draft.md`
- `docs/2026-03-20/opus-collector-global-tranche-f-h-tests-config-crosscut-draft.md`

## 2. Triage Outcome

Collector bundle은 전반적으로 구조는 양호하다. 다만 tranche별로 신뢰도 편차가 크고, 그대로 합쳐 canonical master survey로 올리면 안 된다.

이번 triage 기준:
- live workspace code가 최우선 authority다
- collector draft는 evidence index와 watchlist 초안으로만 쓴다
- `SYNC`, `NO OBSERVED DRIFT`, `well-enforced` 같은 단정 문구는 재검증 전까지 authority로 승격하지 않는다
- terminal 출력에서 보였던 일부 렌더링 깨짐은 source UTF-8 오염으로 확정하지 않는다

## 3. Bundle-Level Findings

### 3.1 재사용 가치가 높은 축

- A/B draft의 `Entrypoints`, `Runtime Spine`, `Side-Effect Sweep`
- C draft의 `Agent Surface Inventory`, `Ownership Seams`, `Retry / Fallback Map`
- D/G draft의 `Persistence Sink Inventory`, `Observability Flow Map`, `Script Classification`
- E draft의 `Operator Surface Inventory`, `Desktop/App Shell Map`, `Preload / Bridge / IPC Boundary Notes`
- F/H draft의 `Test Harness Inventory`, `Prompt / Contract / Config Surface`

### 3.2 바로 의심해야 하는 축

- C draft의 `Director sovereignty is well-enforced` 같은 정리형 inference
- D/G draft의 severity-like watch phrasing
- F/H draft의 `SYNC`, `NO OBSERVED DRIFT`, `No contradictions found` 계열
- F/H draft의 일부 숫자/contract 요약
  현재 live desktop preload method count는 `25`인데 draft는 `26`으로 적은 부분이 있다
- A/B draft의 일부 live count
  Stage 4 advisory chain worker count는 draft 기준 `8`이지만 live code는 현재 `9`다
- C draft의 일부 agent activity 요약
  `Analyst`의 `self.ask()` count 같은 요약은 live code와 직접 다시 대조해야 한다

### 3.3 형식 준수 메모

- A/B draft만 요청한 배너 형식에 가장 가깝다
- C/D/G/E/F/H draft도 `DRAFT / NOT AUTHORITY / COLLECTOR ONLY` 취지는 지키고 있지만, 상단 형식은 제각각이다
- 5개 모두 현재 `commit-state-minimal-contract` 기준의 완전한 resume metadata까지는 못 채웠다
  `Resume Commit`, `Resume Drift Summary`는 공통 누락이다
- source 파일 5개는 `scripts/check_utf8_hygiene.py` 기준 UTF-8 hygiene를 통과했다

## 4. Tranche-by-Tranche Trust Tier

### A/B. Macro Topology + Runtime Core

판정: `T2 reusable with re-check`

좋은 점:
- entrypoint, runtime spine, side-effect 분류가 촘촘하다
- live file/line anchoring이 비교적 많다

주의:
- memory 문구와 과거 sweep 기억을 inference에 섞는 부분이 있다
- 일부 watchlist는 아직 tranche D나 fresh run이 있어야 판단 가능하다
- concrete stale example:
  Stage 4 advisory chain worker count가 draft `8`과 live `9`로 이미 어긋난다

재사용 우선순위:
- 높음: `Entrypoints`, `Runtime Spine`, `Side-Effect Sweep`
- 낮춤: `Inferences`, `Uncertainty`의 historical reference

### C. Domain and Agent Layer

판정: `T2/T3 mixed`

좋은 점:
- agent inventory, retry/fallback map, ownership seam은 재사용 가치가 높다
- Director boundary와 Python vs LLM seam을 구조적으로 정리했다

주의:
- `well-enforced`, `safe only if`, `fail-open by design` 같은 해석이 섞여 있다
- stale memory와 현재 live semantics를 같은 표에 올려 둔 부분이 있다
- watchlist severity가 collector draft치고 약간 강하다
- concrete stale/noise example:
  `Analyst`의 `self.ask()` 회수 요약은 현재 live code와 바로 일치하지 않는다

재사용 우선순위:
- 높음: `Agent Surface Inventory`, `Ownership Seams`, `Retry / Fallback Map`
- 낮춤: `Inferences`, `Contradiction Items`, priority watch phrasing

### D/G. Persistence + Observability + Scripts

판정: `T2 reusable with targeted re-check`

좋은 점:
- sink inventory와 script classification이 잘 정리되어 있다
- persistence/observability split이 canonical survey 초안으로 쓰기 좋다

주의:
- `risk-approval-log.jsonl` authority gap 같은 항목은 실제로는 policy/contract question이다
- watcher severity는 Codex가 다시 낮추거나 높여야 한다
- tools/script 참조 범위 요약은 일부 불완전할 수 있다
  `tools2/` 참조 테스트도 live code로 다시 세야 한다

재사용 우선순위:
- 높음: `Persistence Sink Inventory`, `Observability Flow Map`, `Script Classification`
- 낮춤: `Candidate Watchlist`의 severity wording

### E. Operator Surface + App Shell

판정: `T1/T2`

좋은 점:
- 5개 중 가장 깔끔한 편이다
- desktop/app shell, preload/bridge, operator surface inventory가 구조적으로 유용하다
- contradiction도 비교적 절제되어 있다

주의:
- 일부 숫자는 live code로 한 번 더 확인해야 한다
- desktop는 최근 realization patch가 많아서 count류는 fresh re-check가 필요하다
- baseline dirty summary가 약하다
- contradiction count `0` 같은 문구는 canonical survey로는 그대로 쓰지 않는다

재사용 우선순위:
- 높음: `Desktop/App Shell Map`, `Preload / Bridge / IPC Boundary Notes`, `Prompt / Output Path Notes`

### F/H. Tests + Config + Cross-Cut Contracts

판정: `T3 for drift notes, T2 for inventory`

좋은 점:
- 테스트/설정/프롬프트 표면 inventory 자체는 useful하다
- harness와 config surface 범위를 넓게 잡았다

주의:
- `SYNC`, `NO OBSERVED DRIFT`, `No contradictions found`가 과하다
- 최소 1개 숫자 요약이 stale이다
  live desktop preload method count는 `25`인데 draft는 `26`으로 썼다
- 최근 `quality_risk / revision_required` 의미 분리 이후, drift notes는 live re-check 없이 채택하면 안 된다
- dirty-state metadata도 이미 stale이다

재사용 우선순위:
- 높음: `Test Harness Inventory`, `Prompt / Contract / Config Surface`
- 낮춤: `Cross-Cut Drift Notes`

## 5. Immediate Reuse Rules

canonical survey 작성 시 아래 규칙을 쓴다.

- draft의 inventory/table/map은 재사용 가능
- draft의 inference/severity/resolution wording은 그대로 가져오지 않는다
- `SYNC`, `ALIGNED`, `NO DRIFT`, `well-enforced`, `safe` 같은 표현은 live code 재대조 후에만 사용한다
- 숫자 count, line count, method count는 canonical 문서로 올리기 전 live code로 다시 센다
- TF evidence는 live contract corroboration 용도로만 쓴다

## 6. Recommended Codex Sequence

1. A/B + E를 먼저 canonical skeleton의 backbone으로 사용
2. C와 D/G에서 ownership/persistence maps만 가져오고 해석 문구는 재작성
3. F/H는 inventory만 쓰고 drift notes는 live code 재검증 후 재작성
4. 그다음 canonical master survey를 새로 쓴다
5. action-bearing area가 2개 이상이면 area execution SSOT로 분화한다
6. 실제 realization 전에는 single roadmap 여부를 마지막에 판단한다

## 7. Codex Confidence

현재 confidence: `0.96`

근거:
- 5개 draft 모두 직접 읽고 구조/금지표현/헤더 준수 상태를 확인했다
- UTF-8 hygiene를 실제로 통과시켰다
- 최소 1개 stale count (`25 vs 26 preload methods`)를 live code로 재검증했다
- 이 문서는 collector draft의 triage만 다루고, 아직 canonical survey 결론을 확정하지 않는다
