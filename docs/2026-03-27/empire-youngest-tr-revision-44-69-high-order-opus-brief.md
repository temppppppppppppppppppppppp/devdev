# Empire Youngest TR Revision (Block 44-69 HIGH) — Order-OPUS Brief

Date: 2026-03-27
Audience: OPUS acting as the single worker
Target work_id: `empire_youngest_allsector`

## 1. What You Are

Single worker-OPUS. No sub-dispatch needed.

Sequential work: read weakness report → read current blocks → expand each → write changelog.

## 2. Fixed Scope

- 7 blocks only: **54, 58, 59, 61, 63, 64, 66**
- content expansion within existing 4-key JSON
- 최다은 1-beat in Block 66
- 정하윤 1-beat in Block 54
- block count stays 70

## 3. Input Chain

1. `docs/2026-03-27/empire-youngest-weakness-report.md` — Section 2 (inventory) + Section 4 (arc gaps) + Section 6 (priority matrix)
2. `docs/2026-03-27/empire-youngest-tr-revision-32-43-changelog.md` — 톤/밀도 참조
3. `treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json` — 대상 7블록 + Block 1-5 & 32-43 참조
4. `bible/_quarantine/0_bi_empire_youngest_allsector.json` — reference
5. `docs/2026-03-27/opus-empire-youngest-tr-revision-44-69-high-order.md` — full order

## 4. Per-Block Checklist

For each of the 7 blocks, verify after expansion:

- [ ] content chars: 1,500-2,500
- [ ] tactile detail ≥ 1
- [ ] character micro-moment ≥ 1
- [ ] direct dialogue ≥ 1
- [ ] domain-specific language (applicable blocks: 63, 64)
- [ ] conflict shown, not summarized
- [ ] JSON structure intact
- [ ] scene entry point differs from adjacent blocks

## 5. Critical Callbacks

| Block | Must callback to | How |
|-------|-----------------|-----|
| 54 | Block 35 (이준혁 알림 무시) | 무시→통화의 대비 |
| 58 | Block 1 (회귀 기억) | 전생에서 형 구속 → 이번 생 형 방문 |
| 59 | Block 1 ("나 혼자 짓는다") | 내면 → 공개 선언 |
| 61 | Block 41 (공매도 실패) | 실패→자기파괴 경로 |
| 63 | Block 43 ("전부.") | 선언→실행 |
| 64 | Block 62 (정하윤 47분) | 확보→집행 |
| 66 | Block 1 (옥상) | 추락→착석 |

## 6. Tone Distribution

Do NOT let all 7 blocks converge to the same emotional pattern.

- 54: **shock** — 전화벨이 모든 것을 멈춤
- 58: **gravity** — 긴 침묵과 약속
- 59: **declaration** — 행동으로 말함 (도장, 등기)
- 61: **cold observation** — 뉴스를 보며 판단
- 63: **business tension** — 회의실 프레젠테이션
- 64: **weight of execution** — 숫자가 현실이 되는 순간
- 66: **symmetry** — 12년이 한 문장이 됨

## 7. Deliverables

1. 수정된 TR: `treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json`
2. 변경로그: `docs/2026-03-27/empire-youngest-tr-revision-44-69-high-changelog.md`

## 8. Minimal Prompt

```text
너는 이번 런의 worker-OPUS다. `docs/2026-03-27/opus-empire-youngest-tr-revision-44-69-high-order.md`와 `docs/2026-03-27/empire-youngest-tr-revision-44-69-high-opus-context-memo.md`를 UTF-8로 읽고, `empire_youngest_allsector` TR Block 54, 58, 59, 61, 63, 64, 66을 weakness report 기반으로 확장 수정하라. 블록 수 70 유지. 최다은(Block 66) + 정하윤(Block 54) 감정선 gap closer 삽입. 수정 범위 7블록만.
```

Confidence:
- 98% this is the correct delegation shape
