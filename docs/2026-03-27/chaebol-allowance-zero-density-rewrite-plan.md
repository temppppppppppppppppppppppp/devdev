# Chaebol Allowance Zero — Density-Recovery Rewrite Plan

Date: 2026-03-27
work_id: `chaebol_allowance_zero`
family: `blockguide`
unit: `density-recovery rewrite plan`

---

## 1. Target Pair Paths

| Role | Path | Status |
|------|------|--------|
| TR (live) | `treatments/_quarantine/chaebol_allowance_zero_tr_block_070_draft.json` | **EXISTS** (552 KB, 2026-03-11) |
| BI (live) | `bible/_quarantine/0_bi_chaebol_allowance_zero.json` | **EXISTS** (626 KB, 2026-03-11) |

TR shape: raw JSON list, 70 blocks.
BI shape: roadmap at `MasterBible.plot_roadmap`.

---

## 2. Path-Authority Note

### Stale Root Paths

source_manifest.json과 4축 감사 보고서가 아래 root paths를 여전히 참조하나, **실제로 존재하지 않는다**:

| Referenced Path | Actual Status |
|-----------------|---------------|
| `treatments/chaebol_allowance_zero_tr_block_070_draft.json` | MISSING |
| `treatments/chaebol_allowance_zero_phase0_design.json` | MISSING |
| `bible/0_bi_chaebol_allowance_zero.json` | MISSING |
| `bible/chaebol_allowance_zero_bi.json` | MISSING |

preprocess pipeline 내부에 stale copy가 2건 존재하나 (`04_tr_final/` 하위), 이것은 중간 산출물이지 live authority가 아니다.

**판정**: `_quarantine` pair가 유일한 live authority다. root promotion 전까지 이 사실이 바뀌지 않는다.

---

## 3. Duplicate BI Variants

| File | Size | Hash (MD5) | Status |
|------|------|------------|--------|
| `0_bi_chaebol_allowance_zero.json` | 626 KB | b7753dcf… | **CANONICAL** |
| `02_bi_chaebol_allowance_zero.json` | 435 KB | 1f81c4df… | older variant, reference-only |
| `02_chaebol_allowance_zero_bi.json` | 399 KB | b1d23663… | divergent naming, reference-only |
| `chaebol_allowance_zero_bi.json` | 599 KB | 5873c183… | unshuffled variant, reference-only |

4개 variant 모두 distinct hash. canonical은 626 KB 본체 1건뿐이다.
나머지 3건은 이전 생성 단계 잔여물이며 rewrite 대상이 아니다.

---

## 4. Preserved Strengths (Retry Wave)

retry가 이미 고쳤거나 확립한 것 — rewrite plan이 이것을 파괴해서는 안 된다:

1. **자본 연속성 체인**: 70블록 전체에서 `capital_before == 이전 블록 capital_after` 무예외 성립. 최종 1,318억까지 일관.
2. **복선 정밀 회수**: 6건 seeded foreshadow 전부 지정 블록에서 회수 (유언장 B1→B63, VIP번호표 B3→B12, 셔틀회차표 B5→B46).
3. **사업 도메인 확장 시퀀스**: 장례→호텔→공장→병원→정산→전국→가문 7단계 arc 구조적 건전.
4. **적대자 분산 개선**: retry에서 opponent_unique 4→31로 개선; 서도윤/윤석진/노현주 순환 균형 달성.
5. **번들 밀도 기초 증폭**: 평균 narrative bundle 321→973자로 3배 증가 (다만 이것은 형식 증가이며 실질 밀도와는 별개).

---

## 5. Immediate Blockers

### 5.1 Density Collapse (PRIMARY)

- **Block 7–70 template 반복**: 64블록이 동일 문장 뼈대로 생성됨. 평균 ~321자/블록 (benchmark band 850+자 대비 62% 감소).
- **"재이의 정보 출처를 의심한다"** 70회 반복 — 후속 결과 zero. 거짓 긴장만 생성.
- **solution 방법론 단일화**: Block 7 이후 모든 해결이 "데이터 번들링 → 비용을 통제로 재정의" 한 가지 패턴.

### 5.2 Opponent Intelligence Plateau

- 적대자가 반복 패배해도 전략을 바꾸지 않음. 윤석진이 Block 16, 25, 30, 35에서 동일한 "비용=약점" 오판 반복.
- Block 36–70에서 이름만 바뀌고 동일 archetype 투입 (병원 CFO 오승태, 외부투자자 백도현).

### 5.3 Historical/Market Event Vacuum

- 70블록 중 68블록의 `historical_events`가 null.
- 2018~2022 한국 경제 이벤트(COVID, 공급망, 금리, 부동산)가 거의 미활용.

### 5.4 Specific Factual Blockers

- **2006 regression hint vs 2018 story start**: 시간축 12년 gap 미해소.
- **Block 13 opponent mismatch**: 감사에서 적대자 불일치 지적.

---

## 6. Rewrite-Band Segmentation

### Benchmark Band: Block 1–6 (보존)

핵심 traits:
- solution마다 독립된 전술 (법률 해석, 응급 배식, VIP동선, 계약 반전, 자산화, 포렌식 정산)
- weakness_exploited마다 독립된 적대자 오판
- 블록당 구체적 아이템 3건 이상 (카드, 유언장, 냉각 고장 밥차, VIP번호표 사진…)
- scene_pressure가 시간 압박과 직결 (조문객 첫날 오전, 12시간 window, 48시간 window…)

**이 band는 rewrite 대상이 아니다. 밀도 기준선으로만 사용한다.**

### First Rewrite Band: Block 7–15

- template 반복 진입점. "직전 블록에서 X억까지 맞춰 둔 판이 이번 한 번의 흔들림으로 꺾일 수 있다" 동일 뼈대.
- villain이 항상 "가볍게 본다" → solution이 항상 "데이터 번들링".
- 적대자 유형이 외부 하청업체로 단일화 (가문 권력자 부재).
- **이 band가 첫 rewrite 대상이다.**

### Second Rewrite Band: Block 16–35

- 자본 증감 oscillation이 기계적 (성장/손실 교차). Block 16, 25에서 동일 CFO가 동일 패턴으로 등장.
- 문장이 더 boilerplate화: "린넨 회전율 분석, 호텔 동선 데이터와… 한 장 표로 묶어" 반복.
- 패배 블록이 정확히 5블록 간격 (5/15/25/35/45…) + 기하급수 손실 (-1억~-16억). 결정론적.

### Later Rewrite Band: Block 36–70

- 자본 축적이 기하급수적이나 hollow. 1,000억+ 수준에서 전술 혁신 zero.
- 이름만 바뀐 동일 archetype villain. 대화가 진화하지 않음.
- Block 70 최종 블록에서 원점 회귀 (서도윤) 구조는 있으나, villain 지능이 Block 3 시점과 동일.

---

## 7. Immediate-Fix vs Rewrite-Wave Split

### Immediate Fixes (canonical-path patch 포함)

| # | Item | Type |
|---|------|------|
| 1 | source_manifest.json의 stale root path → _quarantine path로 정정 | path truth |
| 2 | 4축 감사가 참조하는 missing root paths에 stale marker 부착 | path truth |
| 3 | 2006 regression hint → 2018 story start gap 해소 방안 확정 | factual blocker |
| 4 | Block 13 opponent mismatch 수정 방향 확정 | factual blocker |

### Rewrite-Wave Targets (density recovery)

| Wave | Range | Focus |
|------|-------|-------|
| Wave 1 | Block 7–15 | solution 다양성 복원, villain 지능 차등화, 구체적 아이템/이벤트 주입 |
| Wave 2 | Block 16–35 | 기계적 승패 패턴 해체, historical event 최소 5건 삽입, 호텔→공장 전환 밀도 |
| Wave 3 | Block 36–70 | heavyweight 외부 압력(금융당국/재벌 본가/외국자본) 도입, 패배 결과의 실질 위협 강화 |

### Deferred (HUD/Seed-State)

- FinanceHUD / seed-state lag는 density rewrite 이후 정리. TR 내용이 바뀌면 HUD 수치도 재계산 필요하므로 지금 고치면 이중 작업.

---

## 8. First-Wave Rewrite Recommendation

**Target**: Block 7–15 (9블록)

Rewrite 원칙:
1. **solution 전술을 블록마다 독립시킬 것** — benchmark band처럼 각 블록이 고유한 operational 도구를 사용해야 한다.
2. **villain이 패배에서 학습하는 흔적을 넣을 것** — Block 7의 villain이 Block 10에서 다른 전략으로 돌아와야 한다.
3. **구체적 아이템을 블록당 최소 2건 삽입할 것** — 영수증, 계약서, 출입 기록, 식자재 명세서 등 실물.
4. **historical event를 Block 7–15 구간에 최소 2건 배치할 것** — 2018 한국 경제 맥락 (최저임금 인상, 식자재 원가 급등 등).
5. **"재이의 정보 출처를 의심한다" 반복 패턴을 의미 있는 추적 escalation으로 교체할 것**.
6. **support-system cashflow 전제를 유지할 것** — B2B 일상경비 조임점, 장례→호텔 전환의 현금흐름 전쟁이 핵심.

보존 항목:
- 자본 연속성 체인 (capital_before/after 무결성)
- 복선 회수 시점 (Block 12 VIP번호표 payoff)
- 사업 도메인 시퀀스 (장례→호텔 전환 시점이 이 band에 위치)

---

## 9. Creative Drift Guard

이 작품의 정체성을 지키기 위해 rewrite에서 절대 하면 안 되는 것:

- 주식/M&A spectacle로 전환 금지
- 모든 사업을 "운영사업" 하나로 뭉뚱그리기 금지
- B2B 일상경비 조임점 전제 희석 금지
- 가족 무상 구제(bailout) 도입 금지
- 상속이 성장 엔진이 되는 전개 금지
- cashflow warfare를 추상적 권력 게임으로 대체 금지

---

## 10. Final Verdict

**`mixed`**

근거:
- 구조(schema, 자본 연속성, 복선 회수, arc 시퀀스)는 **PASS**
- 밀도(Block 7–70 template 반복, villain 지능 정체, historical event 부재)는 **FAIL**
- path authority는 `_quarantine` 기준으로 **확정 가능** (stale reference 정리만 필요)
- retry wave가 확립한 기반 위에 density recovery를 쌓으면 manuscript-ready까지 도달 가능성 있음
- 그러나 64블록 분량의 rewrite는 경량 작업이 아니며, 낙관적 예단은 부적절

---

## 11. Next Unit

**`rewrite block wave 1`**

이유:
- path truth는 이 보고서에서 확정됨 — `_quarantine` pair가 유일한 live authority
- stale reference 정리는 wave 1 착수 시 병행 가능 (별도 unit 불필요)
- wave segmentation이 명확함 — Block 7–15가 template 진입점이자 가장 작은 bounded scope
- benchmark band(1–6)이 밀도 기준선으로 기능하므로 rewrite 품질 판정 가능

---

```text
work_id: chaebol_allowance_zero
current_stage: audit_or_repair
finished_unit: density-recovery rewrite plan
changed_files: docs/2026-03-27/chaebol-allowance-zero-density-rewrite-plan.md
next_unit: rewrite block wave 1
stop_reason: plan complete — path truth resolved, band segmentation clear, first wave target Block 7-15
```
