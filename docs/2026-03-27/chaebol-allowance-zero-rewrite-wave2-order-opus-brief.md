# Chaebol Allowance Zero Rewrite Wave 2 Executor-OPUS Brief

Date: 2026-03-27
Audience: executor-OPUS (dispatched by order-OPUS)
Target work_id: `chaebol_allowance_zero`

## 1. What You Are

You are the executor OPUS that may dispatch sub-OPUS workers.

Your job is:

- keep the run bounded to Wave 2 (Block 16-35)
- kill all 18 template patterns — zero survivors
- ensure opponent roster rebalancing (윤석진 ≤5, unique opponents ≥6)
- ensure 호텔→공장→병원 domain transitions are narrative events, not template swaps
- verify capital continuity chain after rewrite
- return one coherent quality gate result (9 gates)

## 2. Fixed Scope

This run is only:

- `TR rewrite — Wave 2 (Block 16-35)`

This run is not:

- Block 1-15 modification (Wave 1 result is locked)
- Block 36-70 modification
- BI modification
- planning or re-planning
- promotion or probe

## 3. Hard Constraint

Inside one `work_id`, there must be exactly one editing owner at a time.

That means:

- parallel read-only investigation is allowed
- only one worker may write the final TR JSON
- the executor must merge all sub-OPUS outputs before committing to TR

## 4. Recommended Sub-OPUS Layout

### Executor-OPUS (You)

Own:

- orchestration
- domain transition continuity check (B15→B16, B20→B21, B30→B31, B35→B36)
- opponent roster validation
- quality gate verification (9 gates)
- final TR JSON merge
- handoff

### Sub-OPUS-A: Block 16-25 Rewrite (호텔 마무리 → 공장 진입)

Task:

- rewrite Block 16-25 content fields following §6 contract
- 호텔 백오브하우스(B16-20) → 공장/제조 진입(B21-25)
- B21 전환 블록에서 operational 논리 명시 (왜 공장으로 가는가)
- 공장 도메인 신규 적대자 도입 시작
- benchmark reference: Block 1-6 + Block 7-15 (Wave 1)
- return 10 rewritten block objects

### Sub-OPUS-B: Block 26-35 Rewrite (공장 확장 → 병원 진입)

Task:

- rewrite Block 26-35 content fields following §6 contract
- 공장/제조 확장(B26-30) → 병원 진입(B31-35)
- B31 전환 블록에서 operational 논리 명시 (왜 병원으로 가는가)
- COVID-19(B31) historical event 활용하되 템플릿이 아닌 서사적 활용
- benchmark reference: Block 1-6 + Block 7-15 (Wave 1)
- return 10 rewritten block objects

### Sub-OPUS-C: Quality Gate Checker

Task:

- after A and B complete, run all 9 quality gates
- 18개 kill rule 전수 검사
- capital continuity 검증
- opponent roster 검증 (윤석진 ≤5, unique ≥6, 공장 신규 ≥3)
- scene injection minimum 전수 검사
- solution 독립성 검증 (20개 unique)
- historical event 최소 5건 확인
- return pass/fail per gate

## 5. Parallelism Rule

Safe parallel start:

- Sub-OPUS-A and Sub-OPUS-B may run in parallel (different block ranges, no overlap)
- Sub-OPUS-C must wait for A and B to complete

Structure:

- `A || B`
- then `C` (quality check)
- then executor merge + handoff

**Critical**: A와 B 사이의 domain transition 이음새(B25→B26)를 executor가 merge 시 검증. 공장 도메인이 두 sub에 걸쳐 있으므로 opponent 배분과 전술 중복 여부를 executor가 최종 확인.

## 6. What Executor-OPUS Must Watch

If any of these appear, stop and do not force a salvage narrative:

- §6.4 kill rule 18개 중 어떤 것이든 생존
- solution이 동일 operational 전술을 2+ 블록에서 사용
- villain이 동일 실수를 2+ 연속 등장에서 반복
- capital_before/after chain broken
- 호텔→공장 전환이 template 치환에 불과 (장소명만 바뀌고 구조 동일)
- 공장→병원 전환이 점프 (operational 연결고리 없음)
- historical_event가 5건 미만
- 윤석진이 6블록 이상 등장
- creative anchors washed out

## 7. Anchor Reminders

Do not let sub-OPUS workers wash out:

- the support-system cashflow ladder (호텔 위생/정산 → 공장 급식/폐기물/세탁 → 병원)
- the "moneyline before inheritance" engine
- B2B daily-expense choke points
- no family bailout
- concrete operational detail (not skeleton plot)
- domain transitions as narrative events, not template swaps

## 8. Files To Force Into Context

- `docs/2026-03-27/opus-chaebol-allowance-zero-rewrite-wave2-order.md`
- `docs/2026-03-27/chaebol-allowance-zero-rewrite-wave2-opus-context-memo.md`
- `docs/2026-03-27/chaebol-allowance-zero-density-rewrite-plan.md`
- `docs/2026-03-24/chaebol_allowance_zero_4axis_audit_report.md`
- `treatments/_quarantine/chaebol_allowance_zero_tr_block_070_draft.json`
- `bible/_quarantine/0_bi_chaebol_allowance_zero.json`
- `docs/2026-03-27/opus-chaebol-allowance-zero-rewrite-wave1-order.md` (Wave 1 quality reference)

## 9. Coordinator Output Requirement

The executor must produce:

- merged TR JSON with Block 16-35 rewritten
- quality gate results (9 gates, pass/fail each)
- handoff block

## 10. Worker Prompt Snippets

### Prompt A

```text
너는 Sub-OPUS-A다. `chaebol_allowance_zero` TR의 Block 16-25(호텔 마무리→공장 진입 band)를 density rewrite하라. §6 contract를 따르고, Block 1-15 수준의 밀도를 만들어라. 18개 kill rule을 전부 준수하라. B21에서 호텔→공장 전환의 operational 논리를 서사적으로 처리하라. 보존 필드(capital, title, time_span)는 건드리지 마라. 10개 블록 JSON object를 반환하라.
```

### Prompt B

```text
너는 Sub-OPUS-B다. `chaebol_allowance_zero` TR의 Block 26-35(공장 확장→병원 진입 band)를 density rewrite하라. §6 contract를 따르고, Block 1-15 수준의 밀도를 만들어라. 18개 kill rule을 전부 준수하라. B31에서 공장→병원 전환의 operational 논리를 서사적으로 처리하라. 보존 필드(capital, title, time_span)는 건드리지 마라. 10개 블록 JSON object를 반환하라.
```

### Prompt C

```text
너는 Sub-OPUS-C다. Block 16-35 rewrite 결과를 받아 §10의 9개 quality gate를 검증하라. 특히 18개 kill rule 전수 검사, opponent roster 검증(윤석진 ≤5, unique ≥6, 공장 신규 ≥3), solution 독립성(20개 unique), historical event ≥5를 엄격히 적용하라. gate별 pass/fail과 실패 시 구체적 위반 내용을 반환하라.
```

## 11. Minimal Prompt To Give Executor-OPUS

```text
너는 이번 런의 executor-OPUS다. `docs/2026-03-27/opus-chaebol-allowance-zero-rewrite-wave2-order.md`와 `docs/2026-03-27/chaebol-allowance-zero-rewrite-wave2-opus-context-memo.md`, `docs/2026-03-27/chaebol-allowance-zero-rewrite-wave2-order-opus-brief.md`를 UTF-8로 읽고, `chaebol_allowance_zero` TR의 Block 16-35를 density rewrite하라. `A(B16-25) || B(B26-35)` 병렬 후 `C(quality gate)` 순차. 최종 TR JSON merge는 너만 수행. 수정 대상은 TR JSON 1건뿐이다.
```

Confidence:
- 95% this is the correct delegation shape for Wave 2
