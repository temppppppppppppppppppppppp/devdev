# US AI Exile Monopoly Rewrite Tranche 2 Order-OPUS Brief

Date: 2026-03-27
Audience: OPUS acting as the order/coordinator
Target: `us_ai_exile_monopoly`, Tranche 2 (Block 31-40, ARC-04)

## 1. What You Are

You are the coordinator OPUS for Tranche 2 rewrite execution.

Your job is:

- keep the run bounded to Block 31-40 only
- enforce plan field-level contracts
- enforce scene injection minimums
- enforce repetition kill rules + ARC-03 변별 요건
- verify ARC-03→04 연속성
- run quality gate self-check (7 gates) at the end
- produce rewritten Block 31-40 in the canonical TR JSON

## 2. Fixed Scope

This run is only:

- `TR rewrite — Tranche 2 (Block 31-40, ARC-04)`

## 3. Hard Constraint

- only one worker may write to the TR JSON
- the final write to Block 31-40 must be atomic

## 4. Recommended Approach

### Single Writer (Recommended)

ARC-04는 ARC-03과 같은 난이도 tier. Tranche 1과 동일하게 단일 작성자 접근을 권장.

1. Read Block 30 (Tranche 1 결과) + Block 31-40 (현재 상태) + Block 41 (ARC-05 시작 컨텍스트)
2. Read BI for ARC-04 reference data
3. Rewrite 10 blocks sequentially
4. Run quality gate 7개 self-check
5. Write to TR JSON

## 5. Quality Gate Checklist (7 gates)

| # | Gate | Criterion |
| --- | --- | --- |
| 1 | Template repetition 0 | 6개 금지 문장 없음 |
| 2 | Dialogue minimum | 전 블록 직접 화법 3+ |
| 3 | Sensory minimum | 전 블록 감각 묘사 2+ |
| 4 | Interiority minimum | 전 블록 내면 비트 1+ |
| 5 | Opponent weakness unique | 컨소시엄 고유 약점, ARC-03과 변별 |
| 6 | Doctrine unique | ARC-04 고유 doctrine, ARC-03과 변별 |
| 7 | ARC-03→04 continuity | Block 30→31 자본/맥락/관계 연속 |

## 6. What Order-OPUS Must Watch

- 금지 문장 등장
- ARC-03 문구가 복사/변형 없이 재사용됨
- 컨소시엄이 단일 엔티티로 취급됨 (내부 분화 없음)
- 정부 조달/규격 장면이 추상 요약으로 처리됨
- Block 30→31 연속성 단절
- protagonist가 여전히 contract machine

## 7. Anchor Reminders for ARC-04

- Standards/compliance/audit-log = **이 아크의 핵심 전장**
- Contract language as power = 표준 규격 문서의 문구가 곧 지배력
- ReasonMesh = 추론 엔진 벤치마크가 표준 채택의 근거
- Cold-strategist + 공공 vs 사적 이익 충돌에서 오는 내면 갈등

## 8. Files To Force Into Context

- `docs/2026-03-27/opus-us-ai-exile-monopoly-tr-rewrite-tranche2-order.md`
- `docs/2026-03-27/us-ai-exile-monopoly-rewrite-tranche2-opus-context-memo.md`
- `docs/2026-03-27/us-ai-exile-monopoly-tr-rewrite-plan.md`
- `docs/2026-03-27/us-ai-exile-monopoly-tr-weakness-triage-report.md`
- `treatments/_quarantine/us_ai_exile_monopoly_tr_block_070_draft.json`
- `bible/_quarantine/0_bi_us_ai_exile_monopoly.json`

## 9. Minimal Prompt

```text
너는 이번 런의 order-OPUS다. `docs/2026-03-27/opus-us-ai-exile-monopoly-tr-rewrite-tranche2-order.md`와 `docs/2026-03-27/us-ai-exile-monopoly-rewrite-tranche2-opus-context-memo.md`, `docs/2026-03-27/us-ai-exile-monopoly-rewrite-tranche2-order-opus-brief.md`를 UTF-8로 읽고, `us_ai_exile_monopoly`의 TR Block 31-40 (ARC-04) 리라이트 1트랜치만 수행하라.
```

Confidence:
- 95% this is the correct delegation shape for Tranche 2
