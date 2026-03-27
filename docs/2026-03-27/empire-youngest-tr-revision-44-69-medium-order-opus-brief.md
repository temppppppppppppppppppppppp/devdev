# Empire Youngest TR Revision (Block 44-69 MEDIUM) — Order-OPUS Brief

Date: 2026-03-27
Audience: OPUS acting as the single worker (fresh context session)
Target work_id: `empire_youngest_allsector`

## 1. What You Are

Single worker-OPUS. No sub-dispatch needed.
This is a **fresh context session** — previous revision sessions are not in your context.

Your job: expand 9 MEDIUM-priority blocks with sector domain texture.

## 2. Critical: What Not To Touch

These blocks have been expanded in previous sessions. **Do NOT modify them.**

- Block 32-43: expanded in session 1
- Block 54, 58, 59, 61, 63, 64, 66: expanded in session 2

Also do NOT modify:
- Block 1-31 (original full narrative)
- Block 46, 50, 52, 62, 65 (original full narrative)
- Block 48, 49, 51, 68, 69 (LOW priority — intentional skip)
- Block 70 (original full narrative)

## 3. Your 9 Blocks

**44, 45, 47, 53, 55, 56, 57, 60, 67**

## 4. Input Chain

1. `docs/2026-03-27/opus-empire-youngest-tr-revision-44-69-medium-order.md` — full order with per-block guide + sector language lists
2. `docs/2026-03-27/empire-youngest-tr-revision-44-69-medium-opus-context-memo.md` — context memo
3. `docs/2026-03-27/empire-youngest-weakness-report.md` — Section 2 MEDIUM table + Section 5 sector texture list
4. `treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json` — 대상 9블록 현재 상태
5. `bible/_quarantine/0_bi_empire_youngest_allsector.json` — reference

## 5. Per-Block Checklist

For each of the 9 blocks, verify after expansion:

- [ ] content chars: 1,200-2,000
- [ ] domain-specific language ≥ 2 (섹터 고유 용어)
- [ ] tactile detail ≥ 1
- [ ] direct dialogue ≥ 1
- [ ] scene entry differs from adjacent blocks
- [ ] not a "미팅→협상→성사" repetition
- [ ] JSON 4-key structure intact

## 6. Scene Entry Diversity (must not repeat)

| block_id | recommended scene entry |
|----------|----------------------|
| 44 | 투자심의위원회 회의실 (LP 질문 응대) |
| 45 | 금감원 서류 제출 (오승아 단독) |
| 47 | 파리 패션위크 런웨이 (visual spectacle) |
| 53 | 원자로 설계실 or 기술 실사 (heavy-tech) |
| 55 | 시험 비행장 드론 시연 (야외) |
| 56 | 서해안 현장 or 입찰 발표장 (자연/에너지) |
| 57 | TV 뉴스 or 원안위 통보 (좌절의 수신) |
| 60 | 파일럿 라인 or 창업자 연구실 (기술 설득) |
| 67 | 노사 협의 회의실 (인간 대면) |

## 7. Key Anchors For This Run

- **Block 57이 가장 중요**: 준서의 첫 타이밍 실패. "기다리지 않는다" 교리의 시험.
- **Block 53이 가장 많은 확장 필요**: 105자 → 1,200자+. SMR heavy-tech domain texture.
- **Block 67은 Block 66의 직접 후속**: "정리하겠습니다" → 실행.

## 8. Deliverables

1. `treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json` (9블록만 수정)
2. `docs/2026-03-27/empire-youngest-tr-revision-44-69-medium-changelog.md`

## 9. After This

Next unit: **revival-stage probe** (LOW 5블록은 의도적 스킵).

## 10. Minimal Prompt

```text
너는 이번 런의 worker-OPUS다. `docs/2026-03-27/opus-empire-youngest-tr-revision-44-69-medium-order.md`와 `docs/2026-03-27/empire-youngest-tr-revision-44-69-medium-opus-context-memo.md`를 UTF-8로 읽고, `empire_youngest_allsector` TR Block 44, 45, 47, 53, 55, 56, 57, 60, 67을 weakness report 기반으로 확장 수정하라. 핵심은 sector domain texture 복원. 블록 수 70 유지. 수정 범위 9블록만. 이전 확장 결과(32-43, HIGH 7블록) 절대 수정 금지.
```

Confidence:
- 98% this is the correct delegation shape for fresh-context MEDIUM revision
