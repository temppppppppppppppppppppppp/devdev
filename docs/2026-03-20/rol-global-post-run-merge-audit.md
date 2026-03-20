# ROL Global Post-Run Merge Audit

Date: 2026-03-20
Status: final
Canonical Path: `docs/2026-03-20/rol-global-post-run-merge-audit.md`
Related Evidence Manifest: `docs/2026-03-20/rol-global-live-run-evidence-manifest.md`
Related Survey Backbone: `docs/2026-03-20/rol-global-integrity-survey-3pass-audit.md`
Related Watchlist: `docs/2026-03-20/rol-global-live-run-preflight-watchlist.md`

## 1. Scope

이번 merge audit는 bounded live-run 4-lane 결과를 static survey backbone과 합쳐서 해석한다.

Covered lanes:
- R1 desktop spike
- R2 Stage 2 smoke
- R3 Stage 3 smoke
- R4 Stage 4 smoke

## 2. Run Summary

### Stable pass

- `desktop spike`
  - boot / bridge / main window idle 전환 확인
- `Stage 4 smoke`
  - seed-based disposable fixture에서 정상 완료
  - manuscript outputs 3건 생성

### Partial / degraded

- `Stage 2 smoke`
  - command 자체는 완료
  - 하지만 seed-based fixture 기준 실제 arc export는 2건만 생성
  - 동시에 `arc_3_failure_report.txt`가 남았다
  - 따라서 단순 PASS가 아니라 degraded completion으로 보는 게 맞다

### Fixture mismatch surfaced

- `Stage 3 smoke`
  - seed-based fixture에서는 `arcs >= 3` 전제를 못 맞춰 fail
  - richer disposable clone으로 rerun했을 때는 정상 완료

## 3. Merged Interpretation

### 3.1 What static survey got right

- desktop/operator surface는 bounded spike로 실제 boot 확인이 가능했다
- Stage4 smoke는 seed-based sample fixture와 정렬된다
- smoke lanes는 real project-like disposable fixture가 필요하다는 static reading은 맞았다

### 3.2 What live run clarified

- packaged/seed sample인 `investment_canary_demo`는 `desktop spike`와 `Stage4 smoke`에는 충분하지만, `Stage3 smoke` default contract에는 충분하지 않다
- `Stage2 smoke`도 같은 seed fixture에서는 3-block proof로 읽기 어렵다
- 따라서 현재 smoke suite는 nominally 같은 target name(`코덱스_테스트`)을 기대하지만, 실제로는 lane별 fixture richness requirement가 다르다

## 4. Main Finding

### F-1. Smoke fixture contract is misaligned

현재 가장 분명한 action-bearing finding은 이것이다.

- smoke scripts는 모두 `projects/코덱스_테스트`를 hardcoded target으로 기대한다
- 하지만 reusable seed lineage는 현재 `investment_canary_demo`
- 그리고 그 seed sample은 `Stage3 smoke` 전제(`arcs >= 3`)를 만족하지 않는다

즉 문제는 단순히 `DB missing`이 아니라:

- smoke fixture naming
- packaged seed lineage
- Stage2/3/4 lane별 richness expectation

이 서로 완전히 정렬되어 있지 않다는 점이다.

## 5. Non-Findings

이번 run으로 새로 확인되지 않은 것:

- desktop boot/bridge 자체의 즉시 중대 결함
- seed-based fixture에서 Stage4 smoke를 막는 구조 결함
- richer disposable clone으로도 Stage3 smoke가 실패하는 문제

## 6. Severity / Action Map

### Action-bearing

- `smoke-fixture-alignment`
  - type: focused execution candidate
  - why:
    same target name contract와 actual seeded sample richness가 맞지 않는다

### Not yet action-bearing

- desktop spike boot path
- Stage4 smoke path 자체
- broader runtime/control-plane authority

## 7. Recommended Next Step

다음 추천은 새 global survey를 더 늘리는 게 아니라 focused execution SSOT 하나로 내려가는 것이다.

추천 topic:
- `smoke-fixture-alignment`

다루어야 할 질문:
- `코덱스_테스트`를 공식 smoke fixture로 계속 유지할지
- `investment_canary_demo`를 smoke fixture contract에 맞게 강화할지
- Stage2/3/4 smoke가 서로 다른 fixture richness를 요구하는 현재 상태를 허용할지
- hardcoded target name을 parameterized contract로 바꿀지

## 8. Confidence

현재 confidence: `0.96`

근거:
- desktop spike와 Stage2/3/4 smoke를 실제로 실행했다
- fixture lineage와 artifact outputs를 파일시스템 기준으로 재확인했다
- degraded completion과 fixture mismatch를 실제 terminal state와 output files로 확인했다
- 결론을 bounded finding 하나로 제한했다
