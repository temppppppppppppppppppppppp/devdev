# Codex Comment on `harness_3pass_audit_and_patch.md`

> 인코딩: **UTF-8 only**
> 작성일: 2026-03-12
> 대상 원문: `docs/blockguide/harness_3pass_audit_and_patch.md`
> 기준 문서:
> - `docs/blockguide/SSOT_blockguide-integrated-order.md`
> - `docs/blockguide/treatment-planning-harness.md`
> - `docs/blockguide/treatment-production-harness-v2.md`
> - `docs/blockguide/bi-production-harness-v1.md`
> 목적: OPUS 문서를 **3-pass 기준으로 재감리**하고, 실제 하네스 패치에 바로 쓸 수 있는 Codex 보정 의견을 남긴다.

---

## 0. 한 줄 판정

원문 진단 방향은 **대체로 맞다**.  
다만 지금 상태 그대로는 "좋은 분석 문서"에 가깝고, **하네스 본문에 곧바로 넣을 실행 명세**로 쓰기엔 몇 가지 계약 충돌과 설명 누락이 있다.

Codex 최종 판정:

- **P-3 패턴 피드백 주입**: 즉시 채택
- **P-1 opponent 배분 강화**: 수정 후 채택
- **P-2 weakness 사전 설계 강화**: 수정 후 채택
- **P-4 opponent 교체 선언**: 완화 후 채택
- **P-5 3블록 안전 배치 강화**: 저지능/저신뢰 모드 기본값으로 채택

즉, **원문은 폐기 대상이 아니라 "수정 채택" 대상**이다.

---

## PASS 1. 사실 감리

### 1.1 맞는 진단

원문이 짚은 아래 축은 정확하다.

1. 실패의 핵심은 "검증 함수가 없어서"만이 아니라, **생성 시점에 다양성을 주입하는 장치가 약한 것**이다.
2. `Phase 0`가 opponent 이름 목록만 만들고, **아크별 분배 계획**을 충분히 강제하지 않으면 Production은 그대로 복제한다.
3. `weakness_exploited`가 사후 검증에서는 보이지만, **기획 단계에서 강하게 설계되지 않으면** 결국 opponent 이름만 바뀐 같은 약점으로 수렴한다.
4. Production의 차이 행렬과 출고 게이트는 강하지만, 여전히 **사후 탐지 비중이 높다**.
5. `us_ai_exile_monopoly` 사례는 "구조 PASS와 본문 다양성 PASS는 다르다"는 걸 잘 보여준다.

### 1.2 보정이 필요한 표현

원문 일부는 취지는 맞지만, 지금 하네스 상태를 기준으로는 표현을 조금 좁혀야 한다.

1. "`weakness_exploited` 설계 자체가 Planning에 없다"는 문장은 과하다.
설명:
Planning 문서에는 적대자 합리성과 적대자 이득 구조가 이미 있다. 문제는 **그 개념이 `Phase 0` 슬롯 수준으로 구조화되지 않았다**는 것이다.
권장 표현:
`Planning에는 적대자 합리성 원칙은 있지만, weakness_exploited를 아크/배치 단위로 강제하는 운영 규칙이 약하다.`

2. "`validate_v3`가 없어서 놓친다"는 식의 독해는 이제 틀리다.
설명:
현재 [treatment-production-harness-v2.md](c:/Users/wjjo/Desktop/글도비/docs/blockguide/treatment-production-harness-v2.md)에는 이미 `Pattern Q~U`, `의무 수치 출력`, `avg_bundle_chars < 350`, `opponent_unique`, `weakness_exploited`, `R31-Hard/Soft`가 들어가 있다.
정확한 문제는 **v3가 있어도 그 결과가 다음 생성 프롬프트에 되먹임되지 않으면 늦다**는 것이다.
권장 표현:
`검증 함수 자체보다, 검증 결과를 다음 배치 생성에 되먹임하는 루프가 약하다.`

3. BI 쪽 원인은 "원인 본체"가 아니라 "증상 운반"에 가깝다.
설명:
현재 [bi-production-harness-v1.md](c:/Users/wjjo/Desktop/글도비/docs/blockguide/bi-production-harness-v1.md)에는 이미 `source TR handoff gate`가 들어 있다.
따라서 BI 문서 패치는 보조 축이고, **핵심 패치 대상은 Planning/Production**이다.

### 1.3 PASS 1 판정

| 항목 | 판정 | Codex 의견 |
| ---- | ---- | ---- |
| 실패 진단 방향 | PASS | 실제 사례와 부합 |
| 현재 하네스 이해도 | PASS | 큰 구조는 정확히 읽음 |
| 현재 하네스 반영 상태 서술 | PARTIAL | 이미 들어간 규칙과 아직 없는 규칙을 더 분리해야 함 |

---

## PASS 2. 계약 충돌 감리

이 pass는 "좋은 아이디어인가?"가 아니라, **지금 SSOT와 충돌 없이 들어갈 수 있는가**를 본다.

### 2.1 P-1 opponent 배분 매트릭스

원문 제안:

- `opponent_block_allocation`를 새 필수 시트로 추가
- 아크별 opponent 수와 점유율을 정량화

Codex 판정:

- **의도는 채택**
- **형태는 수정 필요**

이유:

1. 현재 SSOT 최소 `Phase 0` 계약은 `arcs`, `npc_timeline`, `foreshadow_map`, `opponent_transition_plan` 4시트다.
2. 여기서 `opponent_block_allocation`를 새 **필수 top-level 시트**로 올리면, 최근에 정리한 "최소 계약 축소"와 다시 충돌한다.
3. 따라서 배분 정보는 새 시트가 아니라 **기존 `opponent_transition_plan` 내부 필수 하위 슬롯**으로 넣는 게 맞다.

Codex 권장안:

```text
새 top-level 시트를 만들지 말고,
`opponent_transition_plan[*].arc_allocation` 또는 동등 하위 구조로 의무화한다.
```

권장 필드:

```json
{
  "arc_id": "ARC-01",
  "primary_opponent": "A",
  "secondary_opponents": ["B"],
  "blocks": [1, 10],
  "max_share_guard": "단일 opponent 30% 초과 금지",
  "local_conflict_channels": ["가격", "규제", "공급망"]
}
```

### 2.2 P-2 weakness 사전 설계

원문 제안:

- `sector_roadmap.unique_weaknesses`를 필수 승격

Codex 판정:

- **의도는 채택**
- **대상 위치는 수정 필요**

이유:

1. `sector_roadmap`는 현재 SSOT 최소 계약이 아니다.
2. 모든 작품이 섹터형으로 깔끔하게 나뉘는 것도 아니다. 재벌/조직 권력전, 회사원 권력전은 sector보다 `arc`가 더 자연스럽다.
3. 따라서 weakness 설계는 `sector_roadmap` 강제가 아니라, **`arcs` 또는 `opponent_transition_plan` 내부 필수 슬롯**으로 두는 편이 범용적이다.

Codex 권장안:

```text
모든 작품 공통:
- `arcs[*].weakness_pool` 필수
- `opponent_transition_plan[*].forbidden_repeats` 권장

섹터형 작품 추가:
- `sector_roadmap[*].unique_weaknesses`는 확장 시트로 권장
```

나쁜 weakness 예시:

- `"CFO가 기술보다 고용, 인수, 규제 프레임에 먼저 매달린다"`
- `"회장이 기술보다 고용, 인수, 규제 프레임에 먼저 매달린다"`

좋은 weakness 예시:

- `"원가를 CAPEX로 숨겨 운영 손실을 늦게 본다"`
- `"현장 승인권이 본사 결재보다 느려 긴급 교체 비용을 과소평가한다"`
- `"대체 공급망이 없는데도 단가 협상력을 과신한다"`

### 2.3 P-3 패턴 피드백 주입

원문 제안:

- 생성 프롬프트에 opponent/weakness/solution tail 피드백을 넣는다.

Codex 판정:

- **가장 중요한 패치**
- **즉시 채택**

이유:

1. 이 제안은 현재 하네스의 가장 큰 빈칸을 찌른다.
2. Planning 품질이 다소 부족해도, Production 생성 시점에서 "지금까지 뭐가 반복됐는지"를 보여주면 템플릿 반복을 크게 줄일 수 있다.
3. 지금 하네스는 차이 행렬과 출고 게이트가 강하지만, **생성 전에 경고를 먹이는 장치가 약하다**.

Codex 보강 의견:

1. 피드백 블록은 **현재 스키마 경로를 정확히 따라야 한다.**
   - `content.solution`
   - `genre_ext.opponent.name`
   - `genre_ext.opponent.weakness_exploited`
2. `solution_tail`은 단독 P0가 아니라, **현재 `R31-Hard/Soft` 규칙과 정렬**돼야 한다.
3. 피드백은 단순 경고가 아니라, 프롬프트 하단에 **"이번 배치에서 금지할 패턴"**으로 재기입돼야 한다.

즉시 채택할 문장:

```text
패턴 피드백:
- 지금까지 가장 많이 나온 opponent 3개
- 지금까지 가장 많이 나온 weakness 3개
- 최근 10블록에서 반복된 solution 골격 경고
- 위 항목과 겹치는 패턴을 이번 배치에서 다시 쓰면 무효
```

### 2.4 P-4 opponent 교체 선언

원문 제안:

- 같은 opponent 연속 5블록 이상 금지

Codex 판정:

- **그대로는 과함**
- **완화 후 채택**

이유:

1. 좋은 작품도 한 아크에서 같은 macro opponent를 오래 끌 수 있다.
2. 문제는 "같은 이름이 나온다"가 아니라 **같은 적대축, 같은 weakness, 같은 해법, 같은 전장**이 함께 반복되는 것이다.

Codex 권장안:

```text
같은 macro opponent의 재등장은 허용한다.
다만 5블록 이상 이어질 경우 아래 4개 중 최소 2개가 바뀌어야 한다.
- proxy/front 인물
- weakness_exploited
- deal_type
- conflict arena(location/sector/regulatory front)
```

이렇게 바꾸면 "윤석진이라는 큰 적은 그대로인데, 이번엔 CFO가 아니라 하청 대표/감사팀/사돈가가 전면에 나온다" 같은 설계가 가능해진다.

### 2.5 P-5 3블록 안전 배치

원문 제안:

- 첫 아크 3→4→3
- 아크 전환 시 3블록 재강등
- 10블록 일괄 금지

Codex 판정:

- **저지능/저신뢰 모드에는 매우 좋다**
- **전 모델 공통 하드룰로는 과하다**

이유:

1. 사용자는 "Gemini 2.0 Pro도 알아먹게"를 원한다. 이 요구에는 매우 잘 맞는다.
2. 다만 고성능 모델까지 전부 10블록 금지로 묶으면 운영 속도가 지나치게 느려질 수 있다.

Codex 권장안:

```text
기본 안전 모드:
- 첫 아크: 3→4→3
- 아크 전환 직후: 3블록 재강등

확장 허용 조건:
- 직전 2개 배치 연속 P0=0
- opponent/weakness 반복 경고 0
- avg_bundle_chars 기준 안정 통과
```

즉, "**기본은 느리게, 검증되면 확장**"으로 쓰면 된다.

### 2.6 BI 측 보강

원문은 거의 TR 중심이라 BI 언급이 약하다.  
이건 나쁜 게 아니라 우선순위가 맞는 것이다. 다만 한 줄은 추가하는 게 좋다.

Codex 권장안:

```text
BI는 source TR audit snapshot에
`pattern_feedback_summary` 또는 동등 경고 요약이 없으면 PASS 보고서에서 이를 명시적으로 기록한다.
```

이건 BI가 원인을 고치는 용도는 아니고, **문제 TR이 BI에서 "깔끔해 보이는" 착시**를 줄이는 용도다.

### 2.7 PASS 2 판정

| 항목 | 판정 | Codex 의견 |
| ---- | ---- | ---- |
| P-1 | 수정 후 채택 | 새 top-level 필수 시트화는 피해야 함 |
| P-2 | 수정 후 채택 | `sector_roadmap` 강제 대신 `arcs/opponent_transition_plan` 쪽이 맞음 |
| P-3 | 즉시 채택 | 가장 효과 큼 |
| P-4 | 완화 후 채택 | 이름 교체 강제가 아니라 갈등축 교체 강제가 맞음 |
| P-5 | 조건부 채택 | Gemini-safe 기본값으로 매우 좋음 |

---

## PASS 3. 실행 가능성 감리

원문은 분석과 방향 제시는 좋지만, **실제 패치 파일로 쓰기엔 아직 한 단계 부족**하다.

### 3.1 빠진 것 1: exact anchor

원문은 "어디를 고쳐야 하는지"는 잘 말하지만, **각 문서의 어느 섹션 뒤에 넣을지**가 충분히 고정돼 있지 않다.

Codex 권장 anchor:

| 대상 문서 | 삽입 위치 | 넣을 것 |
| ---- | ---- | ---- |
| `treatment-planning-harness.md` | `### 14.1A 초세분화 안전 모드` 직후 | `Phase 0 완료 금지 조건` |
| `treatment-planning-harness.md` | `## 13. 통합 기획 검증 체크리스트` 하단 | opponent/weakness 출고 게이트 |
| `treatment-production-harness-v2.md` | `## 필수 설계 항목`의 `적대자 변천사` 바로 뒤 | `arc allocation` / `weakness pool` 요구 |
| `treatment-production-harness-v2.md` | `### 3.1 생성 프롬프트 구조` | 패턴 피드백 블록 |
| `treatment-production-harness-v2.md` | `### 3.3 사전 선언 프로토콜` | opponent 재사용/갈등축 변화 선언 |
| `treatment-production-harness-v2.md` | `### 3.4 차이 행렬` | pattern feedback 재확인 항목 |
| `treatment-production-harness-v2.md` | `### 1.5 모델별 배치 크기` | Gemini-safe 3→4→3 규칙 |
| `SSOT_blockguide-integrated-order.md` | `### 5.2 Production 시작 전` | 느린 안전 모드 진입 조건 |
| `bi-production-harness-v1.md` | `### 3.1A source TR handoff gate` | pattern feedback snapshot 확인 1줄 |

### 3.2 빠진 것 2: 바보 모델용 예시

사용자 요구는 "지나가는 멍청한 Gemini 2.0 Pro도 이해하게"다.  
그러려면 규칙만 있으면 부족하고, **나쁜 예시/좋은 예시**를 붙여야 한다.

반드시 추가할 예시:

1. 나쁜 opponent 설계 예시

```text
ARC-01: 윤석진
ARC-02: 윤석진
ARC-03: 윤석진
설명: 이름만 있지, 배분 설계가 아니다.
```

2. 좋은 opponent 설계 예시

```text
ARC-01 primary: 윤석진 / secondary: 노현주
ARC-02 primary: 서도윤 / secondary: 물류 하청 대표
ARC-03 primary: 윤석진 / secondary: 감사실 파견 팀장
설명: 같은 macro villain이 살아 있어도 front와 전장이 달라진다.
```

3. 나쁜 weakness 예시

```text
윤석진이 기술보다 고용, 인수, 규제 프레임에 먼저 매달린다.
서도윤이 기술보다 고용, 인수, 규제 프레임에 먼저 매달린다.
```

4. 좋은 weakness 예시

```text
장례식장 회전율을 인건비보다 낮게 계산한다.
호텔 객실 점유율만 보고 세탁 외주 병목을 놓친다.
병원은 의약품 정산주기와 현금흐름 사이의 틈을 숨긴다.
```

### 3.3 빠진 것 3: nested JSON 경로 설명

원문 코드 예시는 맞는 방향이지만, 이 repo의 TR은 종종 평면형이 아니라 **중첩형**이다.  
저지능 모델은 여기서 자주 틀린다.

반드시 문서에 넣을 한 줄:

```text
이 repo 기준 TR은 평면 키가 아니라 아래 nested 경로를 우선한다.
- solution: `content.solution`
- opponent name: `genre_ext.opponent.name`
- weakness: `genre_ext.opponent.weakness_exploited`
- sector: `genre_ext.business_sector`
- arc/rotation: `genre_ext.section_rotation`
```

### 3.4 빠진 것 4: 비섹터형 예외 처리

원문은 sector형 사업물에는 매우 좋다.  
하지만 재벌/조직 권력전처럼 sector보다 `arc`와 `authority chain`이 핵심인 경우도 있다.

반드시 추가할 예외 문장:

```text
sector가 약한 작품에서는 `sector_roadmap`를 강제하지 않는다.
이 경우 `arc`, `authority chain`, `approval line`, `company_state`를 기준으로 weakness와 opponent를 배분한다.
```

### 3.5 빠진 것 5: 즉시 정지 조건

저지능 모델 친화 문서라면 "이 조건이면 다음 단계 금지" 문장이 반복해서 나와야 한다.

반드시 들어가야 하는 문장:

```text
아래 중 하나라도 비면 Phase 0 완료 금지:
- 아크별 opponent 분배표
- 아크별 weakness pool
- 고유 opponent 수 / 단일 점유율 / 아크별 최소 opponent 수
```

```text
아래 중 하나라도 경고가 뜨면 다음 배치 생성 금지:
- 같은 weakness 3회 이상
- 같은 opponent+weakness 4회 이상
- solution 골격 경고
- 직전 배치와 opponent/front 변화 설명 불가
```

### 3.6 PASS 3 판정

| 항목 | 판정 | Codex 의견 |
| ---- | ---- | ---- |
| 분석 문서로서의 완성도 | PASS | 좋음 |
| 바로 패치 가능한 실행 명세 | PARTIAL | anchor와 예시가 더 필요 |
| Gemini-safe 설명력 | PARTIAL | 개념은 좋지만 bad/good 예시와 중첩 경로 설명이 더 필요 |

---

## 4. Codex 권장 보강안

아래는 OPUS 문서에 바로 덧붙이면 좋은 보정 블록이다.

### 4.1 문서 최상단에 넣을 보정

```text
이 문서는 기존 하네스를 부정하는 문서가 아니다.
현재 하네스에 이미 존재하는 사후 검증 규칙(v3, density gate, source TR gate)을 유지한 채,
생성 이전과 생성 중간의 피드백 루프를 보강하는 문서다.
```

### 4.2 Planning용 느린 지시문

```text
적대자를 "목록"으로만 쓰지 말고 "배분표"로 써라.
각 아크는 primary opponent 1명, secondary opponent 1명 이상을 가진다.
같은 macro villain이 재등장해도 front 인물, 약점, 전장이 달라야 한다.
weakness는 opponent 이름만 바꾼 같은 문장을 금지한다.
```

### 4.3 Production용 느린 지시문

```text
다음 배치를 쓰기 전에 먼저 이전 배치의 반복 경고를 읽어라.
가장 많이 나온 opponent, weakness, solution 골격을 적고,
이번 배치에서는 그 패턴을 피한다고 자연어로 먼저 선언하라.
그 선언이 없으면 JSON 출력은 무효다.
```

### 4.4 Gemini-safe 배치 규칙

```text
Gemini류 모델 기본값:
- 새 작품 첫 배치: 3블록
- 아크 전환 첫 배치: 3블록
- 반복 경고 1건 이상: 다음 배치도 3블록 유지
- 연속 2배치 P0=0, 반복 경고 0건일 때만 4~5블록으로 확장
```

### 4.5 BI용 한 줄 보강

```text
BI 감리 보고서에는 source TR의 pattern feedback snapshot 유무를 기록한다.
TR이 구조 PASS라도 패턴 경고가 누적된 상태라면 BI 보고서에 이를 명시한다.
```

---

## 5. 최종 결론

원문 [harness_3pass_audit_and_patch.md](c:/Users/wjjo/Desktop/글도비/docs/blockguide/harness_3pass_audit_and_patch.md)는 **방향이 좋은 진단 문서**다.  
특히 `P-3 패턴 피드백 블록`과 `P-5 느린 배치 기본값`은 지금 하네스가 가장 필요로 하는 보강안이다.

다만 아래 3가지는 반드시 보정해야 한다.

1. 새 top-level 필수 시트를 늘려 SSOT 최소 계약을 다시 무겁게 만들지 말 것
2. `sector_roadmap`를 전 작품 공통 필수로 승격하지 말 것
3. 규칙만 말하지 말고, Gemini-safe bad/good 예시와 nested JSON 경로를 함께 적을 것

Codex 최종 verdict:

- **문서 품질**: 높음
- **즉시 패치 가능성**: 수정 후 가능
- **권장 처리**: `P-3 즉시 반영`, `P-1/P-2/P-4/P-5는 Codex 보정안으로 다듬어 반영`

