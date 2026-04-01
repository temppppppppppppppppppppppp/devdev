# office_checkup_next_day OPUS Context Memo

Date: 2026-04-01  
Audience: OPUS  
Target: `office_checkup_next_day`

## 1. 이번에 OPUS에게 묻고 싶은 핵심

이 작품은 이미 `phase0 + TR + BI`가 있는 진행 중 pair다.  
지금 필요한 것은 새 작품 발명이나 전면 재기획이 아니라:

> **현재 엔진을 유지한 채, 카카오/네이버/문피아 기준으로 더 세게 읽히게 만드는 최소 변경 방향이 무엇인가**

를 판단하는 것이다.

## 2. 현재 작품 진실

현재 작품의 코어:

- 제목: `검진 다음 날, 터질 게 보인다`
- work_id: `office_checkup_next_day`
- 주인공: 한시혁
- 장르 축: `office_power_profile`
- 기본 premise:
  - 3년차 말단 사원이 건강검진 다음 날부터
  - 어떤 프로젝트가 터질지
  - 누가 숫자를 숨기는지
  - 결재가 어디서 막히는지
  - 먼저 읽기 시작한다

현재 살아 있는 강점:

- 말단 사원 + 오피스 파워 손맛
- 굴욕 -> 각성 -> 첫 사이다 -> 전사급 대표 스파이크
- 숫자 은닉 / 결재 병목 / 프로젝트 붕괴 지점
- Block 7 간판 장면 + Block 8 보상 4종
- 회귀/빙의/시스템 없이도 능력물로 서는 타입

## 3. 현재 로컬 판단

로컬 쪽 현재 판단은 이렇다.

- 작품 엔진은 살아 있다
- 문제는 엔진이 아니라 `간판 스케일`이 조금 작게 읽힌다는 점이다
- 따라서 추천은 `유통사 코어 유지 + 재벌/그룹 외피 추가`

즉:

- `섹터 자체를 갈아타는 것`보다
- `한일유통을 그룹 핵심 계열사로 재규정`하는 쪽이 낫다고 본다

## 4. 플랫폼/재료 쪽 근거

플랫폼 trend corpus와 business-only slice를 만든 상태다.

핵심 해석:

- broad corpus top cue: `천재 / 회귀 / 재벌 / 돈 / 미국`
- business slice work bucket top:
  - `office_operator 37`
  - `chaebol_power 30`
  - `money_game 26`
  - `industry_scale 21`

현재 로컬 해석:

- `순수 재벌가 신분`보다 `회사 안에서 권한을 먹는 실무형`이 더 안정적
- 하지만 `재벌 외피`는 여전히 강한 포장력과 판돈을 준다
- 따라서 `오피스 파워 + 재벌 외피` 결이 가장 유력하다

## 5. Option Set

### Option A. 유통사 코어 유지 + 그룹 외피 추가  **로컬 추천**

- 한일유통을 `한일그룹 유통 핵심 계열사`로 재규정
- 물류센터 통합안을 그룹급 비용절감/승계 시그널 사업으로 확장
- 전무/대표 의미를 계열사 임원 수준에서 그룹 구조조정 축으로 상향

### Option B. 그룹 전략실/재벌 전략 라인으로 반쯤 갈아타기

- 주인공 시작점을 그룹 전략실 파견 3년차로 변경
- 유통 계열사 하나가 아니라 계열사 간 자원배분 전장으로 확장

### Option C. 엔진 유지, 섹터 교체

후보:

- 반도체
- 제약
- OTT / 미디어
- 데이터센터 / 전력

## 6. Hard Constraints

- `건강검진 다음 날부터 읽힌다`는 발현 트리거 유지
- `조직 역학 조감 감각` 유지
- 말단 사원에서 시작하는 오피스 파워 손맛 유지
- 회귀 / 빙의 / 상태창 / 시스템 / 재벌3세 회귀물로의 전환 금지
- no-romance 유지
- 전면 재기획 금지
- 가능하면 `minimal-change patch set` 우선

## 7. What OPUS Must Decide

아래 셋을 명확히 판단해주면 된다.

1. `Option A / B / C` 중 무엇이 가장 상업적으로 강한가
2. 현재 작품을 살리는 기준에서 `최소 변경`은 어디까지인가
3. 실제 수정해야 할 필드는 무엇인가

## 8. Ideal OPUS Output

OPUS의 답은 아래 구조면 가장 좋다.

1. **Verdict**
- A/B/C 중 최종 선택 1개

2. **Why**
- 왜 그 선택이 플랫폼 핏상 유리한지
- 왜 나머지 선택은 덜 좋은지

3. **Minimal Patch Set**
- 수정할 필드 3~7개
- 각 필드에서 무엇을 어떻게 바꿀지

4. **Sharpened Copy**
- `logline`
- `group_background`
- `grand_objective`
- `status_end` 또는 최종 promise

5. **Risk**
- 이 수정이 과하면 무엇이 망가지는지

## 9. Files To Read

- `docs/2026-04-01/modern-business-material-context-handoff.md`
- `docs/2026-04-01/office_checkup_next_day-concept-upgrade-options.md`
- `bible/0_bi_office_checkup_next_day.json`
- `treatments/office_checkup_next_day_phase0_design.json`
- `treatments/preprocess/office_checkup_next_day/source_manifest.json`
- `narrative_ssot/10_reference_bank/source_corpora/platform_trends/kr_serial_platforms/business_trend_slice/business_trend_rollup.json`

## 10. Local Baseline Recommendation

로컬 기본 추천은 `Option A`다.

이유:

- 현재 작품의 오피스 파워 손맛을 거의 보존할 수 있다
- 재벌 외피만 추가하면 판돈과 제목 인지가 커진다
- 반도체/제약 등으로 갈아타는 것보다 수정 비용이 훨씬 낮다

하지만 이번 문서는 **로컬 결론 강요용이 아니라**,  
OPUS가 이 추천을 깨도 되는 상태에서 두 번째 판단을 받기 위한 컨텍스트 메모다.
