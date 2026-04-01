# office_checkup_next_day Concept Upgrade — Order-OPUS Brief

Date: 2026-04-01  
Audience: OPUS acting as reviewer  
Target: `office_checkup_next_day`

## 1. What You Are

이번 런의 OPUS는 `전면 재기획자`가 아니라  
**existing pair commercial-strength reviewer**다.

목표는 현재 작품을 갈아엎는 것이 아니라:

- 현재 엔진이 살아 있는지 확인하고
- 더 세게 읽히게 만드는 최소 변경 방향을 고르고
- 실제 패치 세트를 제시하는 것

## 2. Fixed Scope

- `office_checkup_next_day` 1작품만 본다
- review only
- full rewrite 금지
- fresh ideation spree 금지

## 3. Hard Constraint

- `건강검진 다음 날` 엔진 유지
- `조직 병목/숫자 은닉/결재선 읽기` 유지
- 오피스 파워 손맛 유지
- no-romance 유지
- 회귀/빙의/시스템/재벌3세 회귀 엔진 주입 금지

## 4. The Real Question

지금 질문은 이것 하나다.

> 이 작품을 더 세게 만들려면  
> `유통사 코어를 유지한 채 그룹 외피만 붙이는 것`이 맞는가,  
> 아니면 `전장 자체를 옮기는 것`이 맞는가?

## 5. Candidate Options

- `Option A` 유통사 코어 유지 + 그룹 외피 추가
- `Option B` 그룹 전략실/재벌 전략 라인으로 반이동
- `Option C` 엔진 유지 + 섹터 교체

## 6. Preferred Evaluation Standard

아래 기준으로 보면 된다.

1. 카카오/네이버/문피아에서 제목과 한 줄 피치가 더 세게 읽히는가
2. 현재 pair를 최대한 보존할 수 있는가
3. 손맛이 유지되는가
4. 판돈/스케일이 커지는가
5. 수정 비용 대비 효율이 높은가

## 7. Expected Output

아래 구조로 답하면 가장 유용하다.

1. `Verdict`
- A/B/C 중 최종 선택 1개

2. `Commercial Reason`
- 플랫폼 핏 기준 설명

3. `Minimal Patch Set`
- 실제 수정할 필드 3~7개

4. `Sharpened Copy`
- logline
- group_background
- grand_objective
- end-state promise

5. `Do Not Overdo`
- 과수정 방지 경고

## 8. Minimal Prompt

```text
너는 이번 런의 review-OPUS다. `docs/2026-04-01/opus-office_checkup_next_day-concept-upgrade-order.md`, `docs/2026-04-01/office_checkup_next_day-opus-context-memo.md`, `docs/2026-04-01/office_checkup_next_day-order-opus-brief.md`를 UTF-8로 읽고, `office_checkup_next_day` existing pair의 컨셉 강화 방향을 판정하라. 전면 재기획 금지, review only. A/B/C 중 하나를 고르고 minimal patch set과 sharpened copy를 제시하라.
```

Confidence:
- 95% this is the correct delegation shape for the current question
