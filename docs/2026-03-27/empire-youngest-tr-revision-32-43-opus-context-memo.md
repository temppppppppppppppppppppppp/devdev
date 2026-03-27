# Empire Youngest TR Revision (Block 32-43) — OPUS Context Memo

Date: 2026-03-27
Purpose: minimal handoff memo for worker OPUS
Target: `empire_youngest_allsector` Block 32-43

## 1. Current Truth

- family: `blockguide`
- mode: targeted TR revision — content expansion of 12 existing blocks
- canonical pair is still in `_quarantine`
- predecessor chain: re-audit (MIXED) → weakness report (gap catalog) → **this unit**
- block count stays 70 — no additions, no deletions

## 2. Canonical Pair Paths

- TR (write target): `treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json`
- BI (reference only): `bible/_quarantine/0_bi_empire_youngest_allsector.json`

## 3. What The Weakness Report Found For Block 32-43

12 blocks, 400-700 chars each. Block 1-5 standard is 2,000+ chars.

공통 결함:
1. 갈등이 1줄로 축약
2. 해결이 메타요약 ("~로 처리한다")
3. 캐릭터 반응, 미시 모먼트 부재
4. tactile detail (장소, 시간, 감각) 부재

Block 36: 타자 POV → 준서 POV merge 필요
이준혁: Block 35-40 중 1곳에 1-beat 삽입 필요

## 4. What You Do

For each block in 32-43:
1. 현재 content 읽기
2. weakness report의 해당 block gap description 확인
3. 기존 4-key JSON 구조(context/event_villain/solution/reward) 내에서 content 확장
4. 1,500-2,500 chars 범위로 확장
5. tactile detail + micro-moment + 대면 대사 최소 1개씩 포함

Block 36 특별: K사 타자 POV → 준서 POV로 전환
Block 35 또는 38: 이준혁 1-beat 삽입 (1-2문장)

## 5. Quality Baseline

Block 1-5를 읽고 톤/밀도/구조를 기준으로 삼을 것.

핵심 기준:
- 장면이 있는가 (장소, 시간, 물리적 행동)
- 캐릭터가 말하는가 (직접 대사 ≥1)
- 준서가 감정을 억제하는가 (low-affect micro-moment ≥1)
- 섹터 고유 언어가 있는가 (SaaS, IP, 방산, 팬덤 등)

## 6. Do Not Do

- Block 44-69 수정
- Block 1-31 수정
- 새 블록 추가
- BI 수정
- status/gate 파일 수정
- 코드 수정
- 2,500자 초과 팽창

## 7. Creative Anchors

- low-affect protagonist: 감정 자극 장면에서도 억제. "4초간 눈 감기" 류 micro-moment.
- "세 개씩. 쉬지 않고.": Block 37, 43에서 "다음." ritual. 톤 차별화 (37=체크, 43=선언).
- independent-capital: 제국그룹 자금 미사용. 자력 성장 톤.
- all-sector: 각 섹터 domain-specific 언어 필수.
- 가족붕괴: 이준혁 1-beat으로 간접 활성화.

## 8. Main Order Doc

- `docs/2026-03-27/opus-empire-youngest-tr-revision-32-43-order.md`

## 9. Expected Deliverables

1. 수정된 TR: `treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json`
2. 변경로그: `docs/2026-03-27/empire-youngest-tr-revision-32-43-changelog.md`

## 10. Suggested One-Line OPUS Prompt

```text
너는 이번 런의 worker-OPUS다. `docs/2026-03-27/opus-empire-youngest-tr-revision-32-43-order.md`와 `docs/2026-03-27/empire-youngest-tr-revision-32-43-opus-context-memo.md`를 UTF-8로 읽고, `empire_youngest_allsector` TR Block 32-43을 weakness report 기반으로 확장 수정하라. 블록 수 70 유지, Block 36 POV merge, 이준혁 1-beat 삽입. 수정 범위 32-43만.
```

Confidence:
- 97% this memo is sufficient for worker OPUS handoff
