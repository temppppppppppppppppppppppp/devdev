# office_checkup_next_day TR Sync — Order-OPUS Brief

Date: 2026-04-02
Audience: OPUS acting as reviewer
Target: `office_checkup_next_day`

## 1. What You Are

이번 런의 OPUS는
`컨셉 판정자`가 아니라
`post-sync spot auditor`다.

## 2. Fixed Scope

- existing pair 1개만 본다
- `TR sync 이후` 남은 미세 정합성만 본다
- review only
- full rewrite 금지

## 3. Hard Constraint

- `Option A/B/C` 재논쟁 금지
- 새 엔진 주입 금지
- 새 섹터 제안 금지
- broad TR surgery 금지

## 4. Real Question

질문은 이것 하나다.

> 지금 남은 어긋남이  
> `지금 바로 고칠 만한 진짜 이슈`인가,  
> 아니면 `무시 가능한 추상화/약식 표현`인가?

## 5. Findings Under Review

- `A` 그룹 구조조정 상무 도입 시점 drift
- `B` phase0 final-status ceiling 약함
- `C` late seed 일부 옛 표현 잔존

## 6. Preferred Evaluation Standard

아래 기준으로 보면 된다.

1. 나중에 감리 noise를 유발하는가
2. harness drift를 만들 수 있는가
3. 지금 patch cost가 충분히 작은가
4. leave가 더 깔끔한가

## 7. Expected Output

1. `Verdict`
- `Patch all / Patch only A/B/C / Leave as-is`

2. `Finding-by-Finding`
- A/B/C 각각 `patch` 또는 `leave`

3. `Minimal Patch Set`
- 필요한 경우만

4. `Over-Repair Risk`
- 왜 더 건드리면 과한지

## 8. Minimal Prompt

```text
너는 이번 런의 review-OPUS다. `docs/2026-04-02/opus-office_checkup_next_day-tr-sync-order.md`, `docs/2026-04-02/office_checkup_next_day-tr-sync-opus-context-memo.md`, `docs/2026-04-02/office_checkup_next_day-tr-sync-order-opus-brief.md`를 UTF-8로 읽고, `office_checkup_next_day` pair의 TR sync 이후 남은 미세 정합성 이슈만 spot audit하라. 전면 재기획 금지, review only. A/B/C 각 finding에 대해 patch or leave를 판정하고, 필요하면 minimal patch set만 제시하라.
```
