Date: 2026-03-23
Status: final
Document Type: ROL live-merge remediation plan
Canonical Path: `docs/2026-03-23/rol-live-merge-0p01-generation-failure-remediation-plan.md`
Run Scope: `projects/0p-01` bounded partial live-run evidence
Confidence: 97%
Source Survey Docs:
- `docs/2026-03-23/opus/rol-live-merge-t1-runtime-artifact.md`
- `docs/2026-03-23/opus/rol-live-merge-t2-verdict-persistence-operator.md`
- `docs/2026-03-23/opus/rol-live-merge-t3-contracts-context-regression.md`
Evidence Artifacts:
- `docs/2026-03-23/console.txt`
- `projects/0p-01/logs/session_20260323_205346.log`
- `projects/0p-01/logs/session/llm_io.jsonl`
- `projects/0p-01/logs/session/ui_events.jsonl`
- `projects/0p-01/logs/session/decisions.jsonl`
- `projects/0p-01/logs/episode_production.jsonl`
- `projects/0p-01/project_data.db`
Side-Effect Coverage:
- artifact truth: yes
- metadata truth: yes
- console/operator truth: yes
- JSONL/session truth: yes
- persistence truth: yes

---

# ROL Live-Merge 0p-01 Generation Failure Remediation Plan

## 1. Executive Summary

이번 `0p-01` fresh run의 1차 실패는 `Stage 4 quality loop`가 아니라 그보다 앞단인 `ChiefWriter candidate generation`에서 발생했다.

핵심 증거는 세 가지다.

1. `projects/0p-01/logs/session_20260323_205346.log`에서 `ChiefWriter _generate_single_candidate 크래시: 'list' object has no attribute 'get'`가 반복된다.
2. 그 직후 같은 로그에서 `모든 후보 생성 실패` -> `candidates 빈 배열` -> `empty_candidates`로 곧바로 떨어진다.
3. `project_data.db`에는 Stage 4 row가 `EMPTY / score=0 / reject_reason=empty_candidates` 1건만 남았고, Stage 4 `director_selections`와 `attempt_raw_rationale`는 아직 생성되지 않았다.

따라서 이번 run의 현재 주병목은 `CW가 못 쓴다`가 아니라 아래다.

- Chief Writer가 유효한 JSON을 반환해도 payload shape가 `dict`가 아니라 `list`면 현재 single-candidate path가 깨진다.
- `chief_writer_quality.py`의 self-critique가 dict-only parsing을 가정해 즉시 크래시한다.
- 그 결과 Stage 4는 원고 품질 검토 이전에 `empty_candidates`로 탈락한다.

즉 `fix first, rerun second`가 맞고, 이번 우선순위는 기존 `0_0323` 기반 Stage 4 quality debt보다 `candidate payload contract hardening`이 먼저다.

## 2. Current Live State

### 2.1 Run terminal state

- 현재 `main_a.py` live process는 없다.
- `console.txt`는 Stage 4 Round 2 진입까지만 남아 있고 완주 transcript가 아니다.
- 따라서 이 문서는 `bounded partial live-run evidence` 기준 판단이다.

### 2.2 DB truth

`stage_attempts` 현재 상태:

- Stage 2 Ep1: `PASS / 100`
- Stage 3 Ep1: `PASS / 85`
- Stage 3 Ep2: `PASS / 91`
- Stage 3 Ep3: `PASS / 95`
- Stage 4 Ep1 Attempt1: `EMPTY / 0 / failure_category=NULL / reject_reason=empty_candidates`

추가로:

- `director_selections_count = 4`
  - 전부 Stage 2/3
  - Stage 4 director selection 없음
- `attempt_raw_rationale_count = 0`
- `logs/artifacts/stage4/` 아래 현재 run artifact 없음

의미:

- 이번 실패는 Director verdicting 이후가 아니다.
- Stage 4 artifact truth, post-select downgrade, Stage 4 DB parity는 이번 run의 1차 실패 표면이 아니다.

## 3. What Actually Failed

### 3.1 Crash chain

`projects/0p-01/logs/session_20260323_205346.log`에서 반복 확인되는 체인:

1. Chief Writer 호출 성공
2. `thinking_len` 기록
3. `ChiefWriter _generate_single_candidate 크래시: 'list' object has no attribute 'get'`
4. stack trace:
   - `modules/domain/agents/chief_writer.py`, `_generate_single_candidate()`
   - `self.quality_gate.apply_self_critique(...)`
   - `modules/domain/agents/chief_writer_quality.py`, `_self_critique()`
   - `content = data.get("content", "")`
5. 모든 후보 생성 실패
6. 단일 재시도도 동일 실패
7. Stage 4에서 `candidates 빈 배열`
8. UI에서 `모든 후보 생성 실패 -> 다음 면담으로 진행`

이 체인은 Stage 4 Round 1에서 이미 완성된다.

### 3.2 Why the crash happens

현재 코드 경계:

- `chief_writer.py`
  - `_generate_single_candidate()`는 response를 JSON으로 파싱한다.
  - single-candidate path는 사실상 `dict` payload를 전제한다.
  - 그 다음 self-critique로 `manuscript_json`을 넘긴다.
- `chief_writer_quality.py`
  - `_self_critique()`는 `json.loads(manuscript)` 후 바로 `data.get("content", "")`를 호출한다.
  - payload가 `list`면 즉시 크래시한다.

반면 `llm_io.jsonl`에는 Chief Writer response가 실제로 `[` 로 시작하는 array JSON 사례가 남아 있다. 즉 모델 출력이 전부 invalid인 게 아니라, `single-candidate contract`와 `consumer parser`가 shape drift를 견디지 못하는 쪽이 본질이다.

### 3.3 Why "CW가 못 쓴다"로 보면 안 되는가

이번 evidence로 확정 가능한 것은 `writing quality failure`가 아니라 `candidate admission failure`다.

- 유효 JSON response는 존재한다.
- 하지만 pipeline이 그것을 manuscript candidate로 승격하지 못한다.
- 따라서 지금 `Scene structure`, `opening continuity`, `Director PASS/REJECT split`을 1순위로 다시 파는 것은 순서가 틀린다.

## 4. Stale vs Live Corrections

기존 ROL 3 lane 보고서의 구조 진단은 여전히 유효한 부분이 있다. 다만 이번 `0p-01` run에는 stale correction이 필요하다.

### 4.1 Still structurally relevant, but not first-order for 0p-01

- opening-anchor packet priority inversion
- Stage 4 scene/write contract weakness
- post-select downgrade / fix-pack pathology
- `CONDITIONAL_PASS` downstream gap

이 항목들은 live code에서 아직 가치 있는 residual일 수 있다. 하지만 이번 run은 그 단계까지 도달하지 못했다.

### 4.2 Not the current first blocker

- post-select downgrade DB write-back gap
- post-select reject `failure_category` persistence
- Stage 4 retry/fix-pack convergence
- Stage 4 advisory/operator parity

이건 Stage 4 candidate generation이 통과한 뒤에야 다시 의미가 커진다.

### 4.3 Current first blocker

- `ChiefWriter single-candidate payload contract drift`
- `ChiefWriterQuality dict-only self-critique parsing`
- `empty_candidates` escalation before Director review

## 5. Highest-ROI Remediation Order

## 5.1 TF-1. Candidate payload normalization boundary

대상:

- `modules/domain/agents/chief_writer.py`
- `modules/domain/agents/chief_writer_quality.py`

목표:

- single-candidate path가 `dict`뿐 아니라 `list[dict]`도 안전하게 받도록 만든다.
- self-critique 전에 canonical manuscript object로 정규화한다.

구체:

- `ChiefWriter` response가 array면:
  - empty list는 fail
  - `list[dict]`는 single-candidate canonical object로 unwrap
  - list 안 첫 dict 또는 명시 candidate selector 기준으로 normalize
- `_self_critique()`는 `dict`/`list` JSON 둘 다 받아 `content`를 추출할 수 있어야 한다.
- 이미 존재하는 unwrapping helper를 우선 재사용하고, 새 parser를 중복 생성하지 않는다.

완료 기준:

- `list` payload가 더 이상 크래시를 일으키지 않는다.
- Stage 4 Round 1에서 `empty_candidates`로 즉시 떨어지지 않는다.

## 5.2 TF-2. Single-candidate output contract tightening

대상:

- `chief_writer` single-candidate prompt/output contract

목표:

- single-candidate generation은 기본적으로 "단일 JSON object"를 요구한다.
- 다만 parser는 여전히 tolerant하게 유지한다.

원칙:

- prompt tightening은 parser hardening의 대체물이 아니다.
- 출력 계약을 조이되, 런타임은 list-shape drift에 fail-open하지 말고 normalize-first로 처리한다.

## 5.3 TF-3. Empty-candidates observability upgrade

대상:

- Stage 4 candidate admission failure logging
- Chief Writer candidate normalization boundary

목표:

- 다음 번 실패 시 `invalid JSON`, `list payload`, `missing content`, `self-critique crash`가 서로 분리되어 보여야 한다.

구체:

- candidate rejection reason을 structured category로 남긴다.
- DB 최대 보존 정책에 맞춰 raw payload evidence를 가능하면 잃지 않는다.

## 5.4 TF-4. Only after TF-1~3, resume Stage 4 quality-wave residuals

우선순위 재개 대상:

- opening-anchor packet priority
- scene-locked writer contract enforcement
- post-select downgrade / fix-pack sharpening
- `CONDITIONAL_PASS` downstream 처리

이 항목들은 다시 중요하지만, `candidate admission`이 막힌 상태에서는 ROI가 낮다.

## 6. Recommended Rerun Strategy

지금 권장 순서는 이렇다.

1. TF-1 candidate payload normalization
2. TF-2 output contract tightening
3. TF-3 empty-candidates observability
4. Stage 4 Ep1 짧은 sanity rerun
5. 그 후 10-arc fresh run

왜냐하면:

- 이번 실패는 Arc-long quality drift가 아니라 Round-1 generation failure다.
- 그러므로 먼저 `Ep1 candidate admission`만 살려서 pipeline이 다시 흐르는지 보는 것이 가장 빠르다.

## 7. Non-Goals for This Wave

이번 remediation wave의 비목표:

- Stage 2 pacing 재설계
- Stage 3 blueprint density 재평가
- 장기 Q5/Q7 context budget 구조개편
- 새로운 Director policy 변경
- broad Stage 4 retry architecture rewrite

이건 TF-1~3 이후 rerun evidence를 본 다음 다시 판단하는 것이 맞다.

## 8. Final Verdict

이번 `0p-01` run의 주요 병목은 명백하다.

- `ChiefWriter candidate payload contract drift`
- `ChiefWriterQuality self-critique dict-only parsing`
- `empty_candidates` before Stage 4 review

따라서 현재 가장 높은 ROI의 해결 방안은 `Stage 4 quality-wave 추가 보강`이 아니라 `ChiefWriter candidate admission hardening`이다.

한 줄 결론:

`이번 실패는 "CW가 못 쓴다"보다 "유효한 후보를 pipeline이 먹지 못한다"가 더 정확하다.`
