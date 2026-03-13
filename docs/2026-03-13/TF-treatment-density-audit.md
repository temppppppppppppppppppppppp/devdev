# TF: Treatment 밀도 감사 — 01_tr_투자물_골든_카나리아 테스트

> 대상: `treatments/01_tr_투자물_골든_카나리아 테스트.json`
> 감사일: 2026-03-13
> 목적: Treatment 밀도·완성도 점검 + 보강 아이디어 도출

---

## 1. 기본 스펙

| 항목 | 값 |
|------|-----|
| 블록 수 | 60 |
| 파일 크기 | 286KB (157,311 chars) |
| 블록당 평균 content 길이 | 594 chars |
| 빈/null 필드 비율 | 0.2% (2/900) |
| POV 캐릭터 수 | 1 (한시우 단일 시점) |

---

## 2. 필드별 밀도

### 2.1 content 서브필드

| 필드 | min | avg | max |
|------|-----|-----|-----|
| context | 82 | 158 | 521 |
| event_villain | 64 | 143 | 384 |
| solution | 45 | 190 | 595 |
| reward | 41 | 103 | 398 |
| **stakes** | **9** | **53** | **192** |

### 2.2 서사 장치

| 항목 | 총 개수 | 블록당 평균 |
|------|---------|------------|
| foreshadow | 144 | 2.4 |
| callback | 70 | 1.2 |
| relationship_delta | 97 | 1.6 |

**foreshadow:callback 비율 = 0.49** — 복선의 절반만 회수됨.

### 2.3 장르 확장 (genre_ext)

| 필드 | null/해당없음 비율 |
|------|-------------------|
| opponent | 10/60 (17%) |
| deal_type | 5/60 (8%) |
| historical_event | 4/60 (7%) |
| leverage_used | 3/60 (5%) |

14개 필드 중 대부분 채워짐. opponent가 가장 취약.

### 2.4 회귀 확장 (regression_ext)

| 필드 | null/없음 비율 |
|------|---------------|
| regression_hint.suspicion_from | **60/60 (100%)** — 전 블록 "없음" |
| death_flag.avoided / method | 57/60 (95%) |
| butterfly_effect.ripple_effect | 23/60 (38%) |

---

## 3. 문제점 요약

### P1: Thin Blocks (content < 350 chars) — 8개

| Block | chars | 비고 |
|-------|-------|------|
| Block 24 | 348 | 경계선 |
| Block 26 | 308 | |
| Block 38 | 312 | |
| Block 39 | 349 | 경계선 |
| Block 49 | 341 | |
| Block 53 | 328 | |
| Block 56 | 320 | |
| Block 57 | 320 | |

60블록 중 8블록(13%)이 350자 미만. Block 1(1,368자)의 1/4 수준.
Arc/Blueprint 단계에서 이 블록들은 LLM이 채울 여지가 많아지고, 원작자 의도 반영이 약해질 수 있음.

### P2: Short Stakes — 4개

| Block | chars | 내용 |
|-------|-------|------|
| Block 37 | 18 | "안전. 이미 승리. 정확한 시기." |
| Block 57 | 20 | |
| Block 59 | 12 | "안전. 평화로운 정리." |
| Block 60 | 9 | "없음. 만족이다." |

후반 블록의 stakes가 형식적. 특히 Block 59~60은 클라이맥스 후 해소 구간이라 stakes 자체가 낮은 것은 맞지만, 서사적으로 "과연 이대로 끝날 수 있을까"류의 긴장은 남겨야 함.

### P3: Foreshadow:Callback 불균형 (비율 0.49)

144개 복선 중 70개만 회수. **74개 복선이 미회수 상태**.
이대로 파이프라인에 들어가면 Stage 2~4에서 복선 회수 누락이 고질적으로 발생할 수 있음.

### P4: regression_hint.suspicion_from 전 블록 "없음"

60블록 전부 "아무도 의심 안 함". 회귀물의 핵심 긴장 장치인 "이 사람 어떻게 이걸 알았지?"가 Treatment 수준에서 전혀 설계되지 않음. Stage 2~4가 이걸 자체 생성해야 하는데, Treatment에 힌트가 없으면 일관성 유지가 어려움.

### P5: death_flag 57/60 "없음"

회귀 전 사망을 회피하는 것이 회귀물 핵심인데, 대부분 블록에서 death_flag가 비어 있음. 직접적 생명 위협이 없는 투자물이라 구조적으로는 맞지만, "경제적 사망"(파산, 신용불량, 가문 축출) 같은 비유적 death_flag를 채울 여지가 있음.

### P6: POV 단일 (한시우 only)

60블록 전부 한시우 1인칭/한시우 시점. 적대자 시점, 동료 시점 블록이 0개.
투자물 장르에서 상대방의 판단 과정(왜 졌는지)을 보여주는 블록이 없으면 서사 깊이가 제한됨.

### P7: Tension Curve 후반 급락

```
Block 55~60: 7 → 6 → 5 → 9 → 2 → 1
```

Block 58(tension 9)에서 Block 59(2) → Block 60(1)으로 급락. 해피엔딩 구간이라 텐션이 낮은 건 맞지만, 59~60이 너무 평탄하면 독자 이탈 구간이 됨.

### P8: emotional_beat 타입 과다 분산

42종 emotional_beat 중 대부분이 1회 사용. 반복 사용되는 타입이 4회가 최대(triumph, vindication). 카테고리가 너무 세분화되어 있어서 Stage 2~4에서 감정 흐름을 트래킹하기 어려움.

---

## 4. 강점

1. **genre_ext 14필드 전 블록 채움** — 투자물 특화 정보(자본 변동, 투자 수단, 역사적 이벤트, 리스크 수준)가 촘촘함
2. **regression_ext 구조 완비** — butterfly_effect, timeline_knowledge, future_prep 등 회귀물 전용 필드가 설계됨
3. **빈 필드 0.2%** — 구조적 누락이 거의 없음
4. **relationship_delta 1.6/block** — 관계 변화 추적이 블록 단위로 들어가 있음
5. **60블록 = 250화 커버** — 블록당 약 4화, 전체 스케일에 맞음
6. **Tension curve 전반** — 초반~중반까지는 자연스러운 긴장 곡선

---

## 5. 보강 아이디어

### 5.1 즉시 보강 (Treatment 직접 수정)

| ID | 대상 | 작업 | 우선순위 |
|----|------|------|----------|
| D-1 | Thin blocks 8개 | content 각 필드 최소 100자 이상으로 보강 | P1 |
| D-2 | Short stakes 4개 | stakes를 서사적 긴장 문장으로 재작성 (최소 50자) | P1 |
| D-3 | regression_hint.suspicion_from | 최소 10~15블록에 "누가 의심하는가" 설계 삽입 | P1 |
| D-4 | 미회수 복선 74개 | foreshadow↔callback 매핑 테이블 만들고 회수 블록 지정 | P2 |
| D-5 | emotional_beat 통합 | 42종 → 10~15종으로 정규화 | P2 |

### 5.2 구조 보강 (스키마/파이프라인 수준)

| ID | 아이디어 | 설명 |
|----|----------|------|
| S-1 | **복선 회수율 자동 검사** | Treatment 로드 시 foreshadow→callback 매핑 검사, 미회수 복선 경고 출력 |
| S-2 | **multi-POV 블록** | pov_character를 리스트로 확장하거나, 적대자 시점 서브블록 추가 |
| S-3 | **경제적 death_flag** | death_flag 필드에 "파산/신용불량/가문 축출" 등 비유적 위기 카테고리 추가 |
| S-4 | **블록 밀도 최소 기준** | content 합계 400자 미만 블록은 Stage 2 진입 전 경고 |
| S-5 | **emotional_beat enum** | 자유 텍스트 → 제한된 enum + intensity로 정규화. Stage 4 감정 트래킹 정확도 향상 |
| S-6 | **suspicion_tracker** | regression_hint.suspicion_from이 "없음"인 블록이 연속 N개 이상이면 경고 |
| S-7 | **tension_floor 규칙** | 마지막 3블록이라도 tension 최소 3 유지 (독자 이탈 방지) |

### 5.3 Stage 2 연동 보강

| ID | 아이디어 | 설명 |
|----|----------|------|
| A-1 | **Arc 설계 시 미회수 복선 주입** | Arc 생성 프롬프트에 "이 arc 범위 내 미회수 복선 목록" 첨부 |
| A-2 | **Thin block warning** | Stage 2 Analyst가 thin block을 만나면 "이 블록은 Treatment 밀도가 낮으니 해석 폭이 넓다"고 Director에게 보고 |
| A-3 | **suspicion 이벤트 자동 배치** | regression_hint가 전부 "없음"이면 Stage 2에서 Arc당 최소 1개 suspicion 이벤트를 Director에게 제안 |

---

## 6. 종합 판정

| 항목 | 판정 |
|------|------|
| 전체 밀도 | **양호** — 빈 필드 0.2%, 평균 594자/block |
| 장르 특화 | **우수** — genre_ext 14필드 전량 채움 |
| 서사 장치 | **보통** — foreshadow 풍부하나 callback 회수율 49%가 약점 |
| 회귀물 특화 | **미흡** — suspicion_from 전량 "없음", death_flag 95% 비어 있음 |
| 시점 다양성 | **미흡** — 단일 POV |
| 후반부 밀도 | **취약** — Block 49~60 구간 thin block 집중 + stakes 형식적 |

**결론**: 전체 구조와 장르 확장은 잘 되어 있으나, 회귀물 핵심 장치(suspicion)와 후반부 밀도가 약함. D-1~D-3 즉시 보강 권장.
