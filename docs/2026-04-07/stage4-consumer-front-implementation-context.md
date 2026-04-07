# Stage4 Consumer Front Implementation Context

Date: 2026-04-07
Status: final
Document Type: IDE handoff context
Canonical Path: `docs/2026-04-07/stage4-consumer-front-implementation-context.md`
Temp Mirror Path: `(none - context note only; no docs/temp mirror)`
Track: system
Mode: implementation context only; no queue mutation implied
Commit State:
- Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Baseline Dirty Summary: `dirty: active temp roadmap/queue mirrors plus widespread narrative/output/docs deltas; merge audit and four lane survey docs present under docs/2026-04-07`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Docs:
- `docs/2026-04-01/active-temp-execution-roadmap.md`
- `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-07/stage234-handoff-harness-merge-audit.md`
- `docs/2026-04-07/stage234-terminal3-stage4-consumer-handoff-survey.md`
- `docs/2026-04-07/stage234-terminal4-crosscut-authority-matrix-survey.md`
Confidence: `96%`

## 1. Current Priority

로드맵상 현재 구현 1순위는
`0_0-stage4-consumer-contract-normalization-remediation`이다.

현재 front seam 해석:

- broad Stage4 redesign 아님
- new execution lane 필요 아님
- current sharp seam은
  - `numeric carryover baseline promotion`
  - `post-pass state owner-boundary`

즉, 지금 IDE에서 구현할 본선은
`Stage4 consumer lane 안에서 numeric baseline / owner-boundary를 더 명시적으로 닫는 것`
으로 이해하면 된다.

## 2. Problem Statement

현재 시스템은 이미 아래를 할 수 있다:

- FactLedger의 carryover baseline 숫자를 Stage4 writer prompt에 넣는다
- `state_truth_owner_contract`를 만들어 owner/provenance를 저장한다
- contradiction firewall이 `numeric_carryover_authority` mismatch를 감지한다
- fix-pack / repair-contract provenance를 남긴다

하지만 아직 못 하는 것은 이것이다:

- 이번 화 원고와 post-pass 결과로 숫자 truth가 정당하게 바뀌었을 때
  그 truth를 다음 화 carryover baseline 경계로 **autonomous promotion** 하지 못한다
- 그래서 다음 화에서 기존 baseline과 새 truth가 충돌하면
  contradiction firewall / readback이 다시 mismatch로 해석할 수 있다
- 동시에 `final_state_updates`, `actual_truth`, `world_state`가
  각각 남아 있으나 다음 경계에서 어떤 surface가 우선 owner인지
  완전히 자동 정규화되지는 않는다

짧게 말하면:

- `owner is recorded`
- but `owner transition is not fully realized`

## 3. In-Scope

이번 IDE 구현에서 봐야 할 것:

- Stage4 post-pass 시점에서
  `numeric_carryover_authority`를 다음 baseline으로 어떻게 승격시킬지
- 승격 조건이 무엇인지
- 승격된 truth가
  - `fact_ledger`
  - `episode_bible.state_truth_owner_contract`
  - `state_log.state_truth_owner_contract`
  - next-episode Stage4 intake
  에서 일관되게 보이는지
- `final_state_updates / actual_truth / world_state` 중
  high-risk numeric family에서 owner-boundary를 더 명시적으로 닫을 수 있는지

이번 구현에서 보지 말 것:

- Stage2 producer redesign
- Stage3 binding scope 확장
- broad Stage4 prompt retuning
- queue reorder
- 새 execution SSOT 생성
- same-location / same-time hard lock 재개

## 4. Key Evidence

### Roadmap and SSOT

- `docs/2026-04-01/active-temp-execution-roadmap.md`
  - rank 1 item이 `0_0-stage4-consumer-contract-normalization-remediation`
- `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
  - current residual seam을
    `numeric carryover baseline promotion / owner-boundary`로 명시
- `docs/2026-04-07/stage234-handoff-harness-merge-audit.md`
  - 새 lane 없이 existing queue 안에서 처리하라고 merge 결론을 고정

### Code-level Evidence

- `modules/core/stage4_context_builder.py`
  - `_build_numeric_carryover_authority_block()`
  - carryover baseline 숫자를 Stage4 writer prompt에 tiered authority로 주입
  - 핵심 메시지:
    - baseline은 prior-episode authority
    - blueprint target number는 자동 current truth가 아님
    - on-page bridge transaction이 있어야 함

- `modules/core/stage4_post_pass_runtime.py`
  - `_build_state_truth_owner_contract()`
  - `_extract_actual_truth_fact_ledger_carryover_overlay()`
  - `_build_atomic_state_payloads()`
  - 현재는 owner contract와 overlay는 만들지만
    **baseline promotion rule** 자체는 명시적으로 닫지 못함

- `modules/core/fact_ledger.py`
  - asset-family 숫자를 `authority_scope = carryover_baseline`로 다룸
  - 다음 화 context에서 다시 읽히는 baseline source

## 5. Primary Owner Files

이번 작업의 primary owner set:

1. `modules/core/stage4_post_pass_runtime.py`
2. `modules/core/stage4_context_builder.py`
3. `modules/core/fact_ledger.py`

Secondary / adjacent owner set:

4. `modules/core/stage4_interview_round.py`
5. `modules/domain/agents/chief_writer_context_packets.py`
6. `modules/core/numeric_consistency_checker.py`

원칙:

- 먼저 1~3만으로 닫히는지 본다
- 4~6은 readback / advisory / operator wording이 실제 blocker일 때만 확장한다

## 6. Entry Points

### A. Stage4 intake side

파일:

- `modules/core/stage4_context_builder.py`

먼저 볼 함수:

- `_build_numeric_carryover_authority_block()`
- Stage4 mandatory/tier-0 authority assembly call path

현재 역할:

- baseline 숫자를 writer-facing authority로 보여줌
- 이 단계는 **visibility**는 좋지만 **promotion**은 하지 않음

질문:

- 다음 화 intake 시 어떤 숫자를 `settled fact`로 보게 할 것인가
- baseline이 승격된 뒤에도 prompt packet wording이 기존 설계와 충돌하지 않는가

### B. Stage4 post-pass side

파일:

- `modules/core/stage4_post_pass_runtime.py`

먼저 볼 함수:

- `_build_state_truth_owner_contract()`
- `_extract_actual_truth_fact_ledger_carryover_overlay()`
- `_build_atomic_state_payloads()`
- post-pass persistence call path around `bible_delta`, `fact_ledger_changes`,
  `world_state_changes`

현재 역할:

- owner/provenance 기록
- fact ledger overlay용 숫자 추출
- world/fact payload에 반영

현재 부족한 점:

- 어떤 숫자를 `carryover_baseline`로 승격할지 rule이 부족함
- 승격 이후 owner contract와 fact ledger row meaning이 자동으로 맞물리지 않음

### C. Persistence side

파일:

- `modules/core/fact_ledger.py`

먼저 볼 것:

- `authority_scope = carryover_baseline` 의미
- asset-family numeric row가 어떤 기준으로 next baseline이 되는지

질문:

- 승격이 post-pass에서 row overwrite인지
- 기존 row 업데이트인지
- 새 provenance를 가진 baseline refresh인지

## 7. Suggested Implementation Shape

정답 구현을 강제하는 문서는 아니지만,
현재 evidence상 가장 자연스러운 방향은 이 형태다.

1. `promotion trigger`를 post-pass 쪽에서 판정한다.
   - 원고/actual_truth/director state/fix-pack 결과 중
     numeric truth가 baseline보다 높아졌고
     그것이 on-page로 정당화된 경우만 승격

2. `promotion family`를 좁힌다.
   - 처음에는 asset-family carryover 숫자만
   - 예:
     - `capital`
     - `total_assets`
     - 필요 시 `wealth`

3. `promotion provenance`를 남긴다.
   - baseline이 왜 바뀌었는지 owner contract나 fact ledger 쪽에
     최소 provenance가 필요
   - `director_authored` / `runtime_synthesized` / `manuscript_proven` 같은
     현재 분류 체계와 충돌하지 않게 둔다

4. `next-episode intake`가 승격된 truth를 읽게 만든다.
   - context builder가 old baseline을 계속 읽으면 안 됨
   - contradiction firewall이 legitimate change를 다시 mismatch로 치지 않아야 함

5. `split truth`를 더 세게 못 박는다.
   - numeric family에 대해서는
     `actual_truth_surface`
     `final_state_updates`
     `numeric_carryover_authority`
     중 누가 최종 owner인지 contract를 더 선명하게 해둬야 한다

## 8. Guardrails

- `numeric carryover baseline promotion`을
  모든 숫자 field의 일반 규칙으로 바로 확장하지 말 것
- blueprint target number를 자동 current truth로 승격하지 말 것
- contradiction firewall 자체를 약화시켜서 증상을 숨기지 말 것
- `Director 주권주의`를 깨는 hard-coded Python auto-judgement로 가지 말 것
- Stage2/Stage3 redesign로 scope creep 하지 말 것
- same-file 대형 확장보다 bounded helper / boundary normalization 우선

## 9. Minimum Acceptance

이 구현이 끝났다고 말하려면 최소 이 정도는 보여야 한다.

1. 정당한 on-page numeric change가 있으면
   다음 화 carryover baseline이 자동으로 갱신된다
2. 그 다음 화에서 같은 숫자가 baseline mismatch로 다시 튀지 않는다
3. `state_truth_owner_contract`에서 numeric family owner 경계가 더 명시적이다
4. 기존 Stage4 pass/retry/fix-pack 흐름을 깨지 않는다
5. 기존 queue interpretation을 바꿀 필요가 없다

## 10. Minimum Verification

최소 권장 검증:

- `pytest tests/test_stage4_post_processor.py -q`
- `pytest tests/test_stage4_context_builder.py -k "numeric_carryover_authority or carryover" -q`
- `pytest tests/test_a4_failure_pattern.py -q`
- `pytest tests/test_v75c_contradiction_firewall.py -q`

조건부 추가 검증:

- `pytest tests/test_stage4_interview_round.py -k "numeric_carryover_authority" -q`
  - repair contract / provenance를 건드렸다면
- `pytest tests/test_fact_ledger.py -q`
  - baseline row update 의미를 건드렸다면
- `pytest tests/test_chief_writer_context.py -k "numeric_carryover_authority" -q`
  - prompt packet wording / placement을 건드렸다면

정리용 기본 검증:

- `ruff check`
- `python -m py_compile modules/core/stage4_post_pass_runtime.py modules/core/stage4_context_builder.py modules/core/fact_ledger.py`

## 11. Stop / Escalate Rule

계속 구현해도 되는 경우:

- 문제를 `Stage4 post-pass + carryover baseline promotion`으로 닫을 수 있음
- owner set이 여전히 `stage4_post_pass_runtime.py`, `stage4_context_builder.py`,
  `fact_ledger.py` 안에 머묾

멈추고 재정렬해야 하는 경우:

- fix가 Stage3 binding scope 확대를 먼저 요구함
- Stage2 packet redesign 없이는 의미가 없다는 결론이 남
- contradiction firewall 자체를 완화해야만 테스트가 통과함
- numeric family가 아니라 broad world_state reconciliation으로 커짐

그 경우 해석:

- 새 lane를 만들자는 뜻이 아니라
- existing queue item re-audit가 필요하다는 뜻이다

## 12. 3-Pass Audit Note

Pass 1. Structure and scope

- IDE handoff 문서로 범위를 고정
- 새 queue item 생성 지시를 넣지 않음
- current front seam만 다루게 제한

Pass 2. Evidence and consistency

- roadmap rank 1, Stage4 consumer SSOT, merge audit, lane survey를 서로 대조
- owner files / seam 해석이 서로 충돌하지 않음을 확인
- code entrypoint와 existing SSOT 표현을 맞춤

Pass 3. Execution and readability

- IDE에서 바로 열 파일과 함수 기준으로 재구성
- 구현 shape는 힌트만 주고 설계 강요는 피함
- acceptance / verification / stop rule을 명시

Estimated Confidence: `96%`
