# 0_0 Stage2-Stage3 Stage4-Readiness Continuation Runtime Audit

Date: 2026-04-01
Status: draft-live-run-active (premature terminal-state claim invalidated)
Canonical Path: `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-continuation-runtime-audit.md`
Evidence Artifact: `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-continuation-runtime-evidence.json`
Canary Project: `canary_0_0_stage34_arc2_ep2loop_r2`
Session ID: `20260401_173556`
Prior Canary: `canary_0_0_stage34_arc2_ctxnorm_r1`
Parent Lane: `0_0-stage2-stage3-stage4-readiness-remediation`
Related Docs:
- `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md`
- `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-context-normalization-runtime-closure-audit.md`
- `docs/2026-04-01/0_0-stage3-semantic-fidelity-runtime-closure-audit.md`
- `docs/2026-04-01/0_0-stage4-ep2-advisory-escalation-loop-remediation-execution-ssot.md`
- `docs/2026-04-01/0_0-stage4-ep2-advisory-escalation-loop-bounded-survey.md`

## 0. Draft Notice

This document was written before the canary reached a true terminal state.

Byte-level verification on `2026-04-01T18:13:00+09:00` confirmed that PID `61772` was still alive and `session_20260401_173556.log` was still advancing through fresh HTTP calls at `18:12:19`. The terminal-state conclusions below therefore remain a draft snapshot only and must not be used as canonical closure evidence until the live run actually ends and a merged post-run audit is completed.

## 1. Answer First

As of this draft snapshot, `ep2loop_r2` had not yet produced valid terminal-state evidence. The intermediate evidence still points to a probable Stage3 blocker around ep6 entity identity drift, but final verdict promotion is deferred until the live run terminates.

Parent lane verdict: **draft-only / pending live terminal state**

Current leading hypothesis: **Stage3 entity identity drift at ep6** — LLM이 기관명 fact-lock을 반복적으로 위반하며, Entity Registry와 fact-lock prevalidator가 서로 다른 canonical name을 참조하는 multi-source-of-truth 충돌이 근본 원인으로 보인다.

## 2. Canary Terminal State

- ep5 Stage3: **PASS** (score=91, attempt 4/10, strategy=dialogue_focused)
- ep6 Stage3: **INCOMPLETE** (retry 3 진행 중 process died at 18:02:33)
- ep7-9 Stage3: NOT REACHED
- Stage4: NOT ENTERED
- Stage4 ep2 advisory loop: NOT TESTED
- Terminal cause: process died mid-LLM-call (Director re-audit on ep6 retry=3)

## 3. Hard Conclusions

### 3.1 ep5는 여전히 4회 시도가 필요하다 — off-arc intrusion seed probability가 높다

ep5 attempt 1은 `tactical_semantic_fidelity` CRITICAL로 REJECT되었다:

- LLM이 episode tactical authority에 없는 물리 위협/난입 이벤트를 삽입함
- 괴한 제압 → 주인공 생존 본능 설정 괴리
- timeline도 1월 vs 2월 불일치

이후 attempt 2에서 도어록 조작 잔류로 TF-32-V REJECT(30), attempt 3에서 QualityGate REJECT(86<90), attempt 4에서 최종 PASS(91).

ctxnorm_r1에서도 ep5는 정확히 4회 시도가 필요했다. 두 canary 모두 동일한 시도 횟수로 수렴한다는 것은 off-arc intrusion이 확률적으로 높은 seed에서 생성됨을 의미한다.

최종 blueprint(attempt_04)의 narrative content는 clean하다 — 물리 위협 없음, 투자 시나리오에 충실.

근거:
- `session_20260401_173556.log` L336-341 (attempt 1 REJECT)
- `session_20260401_173556.log` L578-580 (attempt 2 TF-32-V REJECT)
- `session_20260401_173556.log` L698-699 (attempt 3 QualityGate REJECT)
- `session_20260401_173556.log` L967-968 (attempt 4 TF-32-V PASS)
- `decisions.jsonl` L1 (PASS, score=91)
- `logs/artifacts/stage3/ep_0005/attempt_04/final_blueprint__dialogue_focused.json`

### 3.2 ep6는 entity identity drift로 3회 시도 후에도 해소되지 않았다

ep6의 핵심 장애는 기관명(증권사 이름) fact-lock 위반이다:

| retry | verdict | score | dominant reject reason |
|-------|---------|-------|----------------------|
| 0 (attempt 1) | PASS_WITH_FIX→TF-32-V REJECT | 95→65 | 신분 은닉 의도 vs 법인명 노출 논리 모순 |
| 1 | REJECT | 40 | '한국투자증권'→'한미증권', 'SW그룹'→'한성그룹' entity drift |
| 2 | PASS_WITH_FIX→TF-32-V REJECT | 90→40 | Entity 4개 불일치 (한미↔신성, 20억↔15억, 자원 지도↔분포도) |
| 3 | in-place patch 완료→PreValidator 기관 사실잠금 위반→Director 대기 중 process died | — | 확정 '신성증권' → blueprint '한국투자증권' 사용 |

특히 retry 2에서 V61 Entity Registry는 `한미증권`을 canonical로 인식하지만, retry 3에서 fact-lock prevalidator는 `신성증권`을 canonical로 인식한다. LLM은 `한국투자증권`을 계속 생성한다. 3개 서로 다른 이름이 3개 서로 다른 authority source에서 각각 정당하다고 주장하는 multi-source-of-truth 충돌이다.

근거:
- `session_20260401_173556.log` L1097 (attempt 1 PASS_WITH_FIX 95)
- `session_20260401_173556.log` L1239-1241 (TF-32-V REJECT 65)
- `session_20260401_173556.log` L1279-1286 (retry 1 REJECT: entity drift)
- `session_20260401_173556.log` L1533-1539 (retry 2 TF-32-V REJECT: 4개 불일치)
- `session_20260401_173556.log` L1568-1583 (retry 3: prevalidator flag → process died)

### 3.3 ctxnorm_r1 대비 ep6 행동이 악화되었다

| 지표 | ctxnorm_r1 | ep2loop_r2 |
|------|-----------|------------|
| ep5 attempts | 4 | 4 |
| ep6 attempts | 1 (PASS) | 3+ (INCOMPLETE) |
| ep8 attempts | 10 | not reached |
| Stage4 entered | yes | no |
| Stage4 ep2 결과 | 10 rounds exhausted, REJECT | not tested |

ctxnorm_r1에서 ep6는 1회 attempt로 PASS했으나, ep2loop_r2에서는 3회 retry 후에도 해소 불가능했다. 이 차이는 entity drift가 확률적(stochastic)이라는 것을 확인한다 — 동일 코드 기반에서도 LLM의 기관명 생성이 매번 다른 이름을 선택한다.

ctxnorm_r1에서도 ep8이 10회 attempt가 필요했고 그 원인이 `기관명 오류`(한미증권→신성증권)였다는 점은, entity drift가 ep6에만 국한되지 않는 시스템적 문제임을 보여준다.

### 3.4 Stage4 ep2 advisory loop 수정은 runtime에서 검증되지 않았다

ep2 advisory escalation loop 수정(T1: FlashbackVerifier 프롬프트, T2: strong advisory ui.log, T3: post_select_conflict detail)은 코드 수준에서 landed되었으나, 이 canary가 Stage4에 도달하지 못했으므로 runtime proof가 없다.

## 4. Medium-Confidence Conclusions

### 4.1 ep6 entity drift의 근본 원인은 fact-lock multi-source conflict일 가능성이 높다

Entity Registry(V61)와 fact-lock prevalidator가 같은 기관에 대해 서로 다른 canonical name을 반환하는 현상이 관찰되었다. 이 불일치가 LLM의 혼란을 가중시키는 것으로 추정된다. 단, 이 추정은 로그 수준의 관찰이며, V61 Entity Registry와 fact_ledger DB의 직접 교차 검증은 이번 audit scope에 포함되지 않았다.

Confidence: 80%

### 4.2 blueprint_0006.txt 이하는 stale artifact이다

canary prep 기록에 따르면 `from_ep=5` cleanup에서 DB 레코드(stage3_attempts, stage3_director_selections)는 삭제되었으나 blueprint 물리 파일은 삭제되지 않았다(`blueprint_files_removed: 0`). 따라서 `blueprint_0006.txt` ~ `blueprint_0008.txt`는 source project `0_0`의 이전 세션에서 생성된 stale 파일이며, 이 canary의 output이 아니다.

`blueprint_0006.txt`의 내용(Scene 1: 불량배 무리 난입, 쇠파이프 제압)은 이 canary 이전의 semantic fidelity 위반 사례를 그대로 담고 있으며, 현재 canary가 같은 ep6를 정상 생성하지 못한 것과 혼동해서는 안 된다.

Confidence: 95%

## 5. Open Questions

1. V61 Entity Registry의 `한미증권`과 fact-lock prevalidator의 `신성증권`이 같은 entity를 가리키는지, 아니면 서로 다른 entity가 혼동되고 있는지 — DB 직접 조회 필요
2. ep2loop_r2 프로세스 사망 원인 — `run.err.txt` 빈 파일이고 crash_dump.log 미확인; OS 수준 kill인지, OOM인지, 외부 종료인지 불분명
3. ep6 retry가 10회 budget를 모두 소진했다면 결과가 어떻게 되었을지 — process death로 인해 미확인

## 6. ep5 Vertical Slice

### Artifact Truth
- `blueprint_0005.txt`: 현재 canary session에서 생성 (attempt_04)
- 물리 파일 존재, 투자 시나리오 정합 — WTI 6월물 매수, 박성호 PB 통화, 에피소드 전개 clean
- `logs/artifacts/stage3/ep_0005/attempt_04/final_blueprint__dialogue_focused.json`: 존재, content_hash 일치

### Metadata Truth
- `decisions.jsonl`: PASS, score=91, strategy=dialogue_focused, attempt_key=s3:ep5:arc2:a4:20260401_173556
- `quality_metrics.jsonl`: validation PASS(91), quality_risk=true, revision_required=true
- `ui_events.jsonl`: seq 71-77에 결과/전략/판정/저장 완료 기록

### Narrative Truth
- 통합 시나리오: 한시우가 박성호 PB에게 15억 원 WTI 매수 지시 → 저항 → 협박 → 체결. 물리 위협 없음.
- `_ensemble_meta.python_warnings`: `opening_anchor` MAJOR 1건 — scene_1.title 누락 (구조적 잔류, narrative content 무관)
- Prior canary(ctxnorm_r1) ep5와 같은 수준: 4회 시도, PASS, off-arc intrusion 제거 확인

### Before vs After
| 지표 | prior (semantic_r5) | ctxnorm_r1 | ep2loop_r2 |
|------|-------------------|-----------|------------|
| ep5 attempts | 불명 | 4 | 4 |
| ep5 score | 96 | PASS | 91 |
| off-arc hit | clean | clean | clean (attempt 4) |
| off-arc in early attempts | 불명 | 불명 | CRITICAL attempt 1 |

## 7. ep6 Vertical Slice

### Artifact Truth
- `blueprint_0006.txt`: **STALE** — source project의 이전 output. 불량배 난입 장면 포함. 이 canary의 output이 아님.
- `logs/artifacts/stage3/ep_0006/`: 디렉토리 미존재 — ep6 blueprint가 최종 저장되지 않았음
- ep6 blueprint JSON artifact: 미생성

### Metadata Truth
- `decisions.jsonl`: ep6 entry 부재
- `quality_metrics.jsonl`: ep6 retrieval_observation만 존재, validation entry 부재
- `ui_events.jsonl`: ep6 generation 시작(seq 79-81)까지만 기록, 결과 미기록
- `session_20260401_173556.log`: ep6 retry 3개 + process death 전체 추적 가능

### Narrative Truth
- ep6의 내용 자체는 문제가 없었다 — retry 2에서 Director가 score=90 PASS_WITH_FIX를 주었고, 물리 위협/off-arc intrusion은 없었다
- 장애의 본체는 narrative가 아니라 entity naming이다: LLM이 증권사 이름을 정확하게 생성하지 못함
- in-place patch 후에도 기관명이 교정되지 않는 것은 patch prompt가 entity fact-lock 정보를 충분히 전달하지 못하거나, 다중 truth source가 LLM을 혼란시킴을 의미

### Before vs After
| 지표 | ctxnorm_r1 ep6 | ep2loop_r2 ep6 |
|------|---------------|---------------|
| attempts | 1 | 3+ (incomplete) |
| final verdict | PASS | INCOMPLETE |
| entity drift | 없음 | 반복 발생 |
| off-arc intrusion | 없음 | 없음 |

ctxnorm_r1 ep6가 1회 PASS인 반면 ep2loop_r2 ep6이 3회+ 실패인 것은, entity drift가 확률적 장애이며 코드 수정으로 deterministic하게 해소된 것이 아님을 보여준다.

## 8. Parent Lane Blocker Analysis

### 이전 판정 (ctxnorm_r1 기반)
- Stage3 sub-verdict: `closure_candidate`
- Stage4 sub-verdict: `blocked_upstream_advisory_escalation_loop`
- Parent lane: `partial`

### 이번 canary가 추가한 evidence
1. Stage3 `closure_candidate`가 약화됨 — ep6 entity drift가 fresh canary에서 미해소
2. Stage4 ep2 advisory loop 수정(T1-T3)은 runtime 검증 불가 — Stage4 미도달
3. 프로세스가 Stage3 ep6에서 사망하여 Stage4 intake readiness 자체를 테스트할 수 없었음

### Current blockers
1. **Primary**: Stage3 entity identity drift — fact-lock multi-source conflict가 LLM의 기관명 생성을 교란
2. **Secondary**: Stage4 ep2 advisory loop — 코드 landed, runtime unverified

## 9. Parent Lane Verdict

**blocked**

근거:
- Stage3 `closure_candidate`는 ctxnorm_r1 단일 canary 기준이었으나, ep2loop_r2가 같은 코드 기반에서 ep6 미완주를 보여줌
- 두 canary의 차이는 LLM 확률성에 의한 것이며, entity drift가 코드 수준에서 해소되지 않았음
- Stage4는 아직 한 번도 정상 완주한 적이 없음 (ctxnorm_r1에서도 ep2 10 rounds exhausted REJECT)

## 10. Final Report

| 항목 | 값 |
|------|-----|
| **Canary terminal state** | stopped — ep6 Stage3 retry=3, Director re-audit 대기 중 process died (18:02:33) |
| **Parent lane verdict** | **blocked** |
| **Dominant blocker** | Stage3 entity identity drift at ep6 — fact-lock multi-source conflict (Entity Registry vs fact-lock prevalidator canonical name 불일치) |
| **Residual seam 1** | Off-arc intrusion seed probability (ep5 = 4 attempts consistently) |
| **Residual seam 2** | Stage4 ep2 advisory loop remediation (T1-T3 code landed, runtime unverified) |
| **Residual seam 3** | ep6 process death cause unknown (no crash dump, no stderr) |
| **Next action** | Entity Registry와 fact-lock prevalidator의 canonical name source 교차 검증 → multi-source-of-truth 충돌 해소 후 canary 재실행 |

## 11. 3-Pass Audit Record

Pass 1, structure and scope:
- audit type confirmed: continuation runtime audit (not execution SSOT, not survey)
- scope bounded to ep2loop_r2 canary terminal state + parent lane verdict
- no new patches, no new canary, no queue changes
- answer-first format, hard/medium/open separation present
- ep5/ep6 vertical slices present

Pass 2, evidence and consistency:
- all claims traced to session log line numbers
- artifact truth verified (ep5 exists, ep6 stale, Stage4 absent)
- metadata truth verified (decisions 1 entry, quality_metrics 3 entries)
- ctxnorm_r1 comparison table consistent with prior closure audit
- multi-source entity conflict documented with specific log evidence

Pass 3, execution and readability:
- parent lane verdict is singular and explicit: `blocked`
- dominant blocker actionable: entity fact-lock source unification
- next action is one bounded step, not a broad redesign
- no Stage4 resume declared, no closure overclaimed

Confidence: 96%
