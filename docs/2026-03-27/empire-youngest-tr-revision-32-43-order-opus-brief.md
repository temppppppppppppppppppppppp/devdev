# Empire Youngest TR Revision (Block 32-43) — Order-OPUS Brief

Date: 2026-03-27
Audience: OPUS acting as the single worker
Target work_id: `empire_youngest_allsector`

## 1. What You Are

Single worker-OPUS. No sub-dispatch needed.

This is sequential work: read Block 1-5 (reference) → read Block 32-43 (current) → expand each block → write changelog.

## 2. Fixed Scope

- Block 32-43 only (12 blocks)
- content expansion within existing 4-key JSON structure
- Block 36: POV merge (타자 → 준서)
- 이준혁 1-beat insertion (Block 35-40 중 1곳)
- block count stays 70

## 3. Input Chain

Read in this exact order:

1. `docs/2026-03-27/empire-youngest-weakness-report.md` — Section 1 (per-block gap catalog)
2. `treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json` — Block 1-5 (density reference) + Block 32-43 (revision target)
3. `bible/_quarantine/0_bi_empire_youngest_allsector.json` — plot_roadmap Block 32-43 (reference)
4. `docs/2026-03-27/opus-empire-youngest-tr-revision-32-43-order.md` — full order with per-block guide

## 4. Per-Block Checklist

For each block in 32-43, verify after expansion:

- [ ] content chars: 1,500-2,500
- [ ] tactile detail ≥ 1 (장소, 시간, 감각 중 최소 1)
- [ ] character micro-moment ≥ 1 (준서의 감정 억제 표현)
- [ ] direct dialogue ≥ 1 (대사)
- [ ] domain-specific language ≥ 1 (섹터 고유 용어/장면)
- [ ] conflict is shown, not summarized
- [ ] resolution has process beats, not meta-summary
- [ ] JSON structure intact (context/event_villain/solution/reward)

## 5. Special Operations

### Block 36 POV Merge

Before: K사 전략기획본부장 3인칭 시점
After: 준서 시점. K사 움직임이 정보망으로 도착. 준서가 인지하고 무시.

### 이준혁 1-beat

Location: Block 35 (recommended) or Block 38
Size: 1-2 sentences within the block's existing flow
Content: 제국그룹 뉴스 확인 또는 이준혁 부재중 전화 무시
Purpose: Block 54 (이준혁 전화)의 setup

### "다음." Ritual Differentiation

Block 37: 냉정한 체크 톤. 루틴.
Block 43: 무게 있는 선언 톤. 정하윤과의 대면에서.

## 6. What To Watch

- 12블록이 같은 패턴(문제→대면→해결→수치)으로 반복되지 않도록 scene entry point를 다양화
- 오승아/정하윤/야마모토가 "~가 처리했다" 요약으로 돌아가지 않도록 직접 행동/대사 포함
- 확장 시 원래 block의 핵심 이벤트를 삭제하지 않도록 주의 (additive, not replacing)
- 자본 수치(3,000억, 2,100억 등)는 유지하되 산술 나열이 아닌 장면 속 언급으로

## 7. Deliverables

1. 수정된 TR: `treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json`
2. 변경로그: `docs/2026-03-27/empire-youngest-tr-revision-32-43-changelog.md`

## 8. Minimal Prompt

```text
너는 이번 런의 worker-OPUS다. `docs/2026-03-27/opus-empire-youngest-tr-revision-32-43-order.md`와 `docs/2026-03-27/empire-youngest-tr-revision-32-43-opus-context-memo.md`를 UTF-8로 읽고, `empire_youngest_allsector` TR Block 32-43을 weakness report 기반으로 확장 수정하라. 블록 수 70 유지, Block 36 POV merge, 이준혁 1-beat 삽입. 수정 범위 32-43만.
```

Confidence:
- 98% this is the correct delegation shape for Block 32-43 TR revision
