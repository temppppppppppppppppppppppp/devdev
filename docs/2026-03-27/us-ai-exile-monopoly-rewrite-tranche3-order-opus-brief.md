# US AI Exile Monopoly Rewrite Tranche 3 Order-OPUS Brief

Date: 2026-03-27
Audience: OPUS acting as the order/coordinator
Target: `us_ai_exile_monopoly`, Tranche 3 (Block 1-10, ARC-01)

## 1. What You Are

Coordinator OPUS for Tranche 3 — the **opening hook** rewrite.

This is the highest-stakes tranche so far. Block 1's 128TB SSD scene defines the entire work's first impression.

## 2. Fixed Scope

- `TR rewrite — Tranche 3 (Block 1-10, ARC-01)` only

## 3. Hard Constraint

- only one worker writes to TR JSON
- Block 1-10 atomic write

## 4. Recommended Approach: Single Writer

오프닝은 톤/분위기의 일관성이 결정적. 병렬화보다 단일 작성자가 10블록을 연속으로 쓰는 것을 권장.

1. Read Block 1-10 (현재 상태) + Block 11 (ARC-02 컨텍스트)
2. Read BI for ARC-01 reference
3. Rewrite 10 blocks sequentially — Block 1 (128TB SSD 장면)부터
4. Quality gate 7개 self-check
5. Write to TR JSON

## 5. Quality Gate (7 gates)

| # | Gate |
| --- | --- |
| 1 | 금지 문장 0 + ARC-03/04 복사 0 |
| 2 | 전 블록 대화 3+ |
| 3 | 전 블록 감각 2+ |
| 4 | 전 블록 내면 1+ |
| 5 | opponent 약점 = 헬릭스마인드 잔류 라인 고유 |
| 6 | doctrine = ARC-01 고유 |
| 7 | **Block 1에 128TB SSD 귀환 감각 장면 존재** |

## 6. What Must Watch

- 128TB SSD가 추상 언급에 그치면 **실패**
- "고용 거부" 선언이 Block 1-3에 없으면 경고
- 과소평가→반전→경악 패턴이 10블록에 걸쳐 드러나지 않으면 경고
- protagonist 첫인상이 "contract machine"이면 **실패** — 분노/결의/고독이 공존해야 함
- opponent가 단일 엔티티로 취급되면 경고

## 7. Anchor Reminders for ARC-01

| Priority | Anchor |
| ---- | ---- |
| **CRITICAL** | US exile → Korea return (Block 1) |
| **CRITICAL** | 128TB SSD (Block 1 감각 장면) |
| **CRITICAL** | "I refuse employment, pay the fee" (Block 1-3) |
| HIGH | ReasonMesh (암시→드러남) |
| HIGH | Cold-strategist + 추방의 분노/결의 |
| MEDIUM | Contract language as power (첫 계약서) |
| SEED | Standards battlefield (씨앗) |
| SEED | Korea-US AI war (전조) |

## 8. Files To Force Into Context

- `docs/2026-03-27/opus-us-ai-exile-monopoly-tr-rewrite-tranche3-order.md`
- `docs/2026-03-27/us-ai-exile-monopoly-rewrite-tranche3-opus-context-memo.md`
- `docs/2026-03-27/us-ai-exile-monopoly-tr-rewrite-plan.md`
- `docs/2026-03-27/us-ai-exile-monopoly-tr-weakness-triage-report.md`
- `treatments/_quarantine/us_ai_exile_monopoly_tr_block_070_draft.json`
- `bible/_quarantine/0_bi_us_ai_exile_monopoly.json`

## 9. Minimal Prompt

```text
너는 이번 런의 order-OPUS다. `docs/2026-03-27/opus-us-ai-exile-monopoly-tr-rewrite-tranche3-order.md`와 `docs/2026-03-27/us-ai-exile-monopoly-rewrite-tranche3-opus-context-memo.md`, `docs/2026-03-27/us-ai-exile-monopoly-rewrite-tranche3-order-opus-brief.md`를 UTF-8로 읽고, `us_ai_exile_monopoly`의 TR Block 1-10 (ARC-01) 리라이트 1트랜치만 수행하라.
```

Confidence:
- 94% this is the correct delegation shape for Tranche 3
