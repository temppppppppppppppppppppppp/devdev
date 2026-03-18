# OPUS → SSOT 통합 방법론

> **작성일**: 2026-03-18
> **목적**: OPUS 24개 문서(10,012행)의 중복을 제거하고 영역별 SSOT로 통합
> **산출물 위치**: `docs/2026-03-18/OPUS/ssot/`

---

## 1. 현황 분석

### 1.1 원본 문서 인벤토리 (24개, 10,012행)

| # | 파일 | 행수 | 주제 | 유형 |
|---|------|------|------|------|
| 1 | geuldobi-codebase-full-survey-2026-03-18.md | 301 | 코드베이스 전체 개관 | 조사 |
| 2 | geuldobi-stage23-deepdive-hidden-areas-survey.md | 432 | Stage 2-3 숨은 영역 | 조사 |
| 3 | geuldobi-v2-be-fe-connectivity-deepdive-full-survey.md | 815 | BE-FE 연결성 | 조사 |
| 4 | geuldobi-v2-be-fe-connectivity-frontend-improvement-survey.md | 473 | BE-FE 개선점 | 조사 |
| 5 | geuldobi-v2-crosscut-deepdive-hidden-seams-3pass-audit.md | 386 | 크로스컷 이음매 | 감리 |
| 6 | geuldobi-v2-devils-advocate-pass3-audit.md | 336 | 악마의 변호인 감리 | 감리 |
| 7 | geuldobi-v2-frontend-deepdive-3pass-audit.md | 368 | FE 딥다이브 | 감리 |
| 8 | geuldobi-v2-frontend-deepdive-adversarial-3pass-audit.md | 585 | FE 적대적 감리 1차 | 감리 |
| 9 | geuldobi-v2-frontend-deepdive-adversarial-3pass-audit-r2.md | 446 | FE 적대적 감리 2차 | 감리 |
| 10 | geuldobi-v2-llm-deepdive-adversarial-3pass-correction.md | 456 | LLM 적대적 감리 교정 | 감리 |
| 11 | geuldobi-v2-llm-deepdive-final-6pass-verdict.md | 244 | LLM 최종 판정 | 감리 |
| 12 | geuldobi-v2-llm-integration-deepdive-3pass-audit.md | 651 | LLM 통합 딥다이브 | 감리 |
| 13 | geuldobi-v2-llm-model-selection-report.md | 829 | LLM 모델 선정 | 보고서 |
| 14 | geuldobi-v2-rol-deepdive-full-survey.md | 677 | ROL 전역 조사 | 조사 |
| 15 | geuldobi-v2-stage0-2-hidden-internals-adversarial-audit.md | 201 | Stage 0-2 적대적 감리 1차 | 감리 |
| 16 | geuldobi-v2-stage0-2-hidden-internals-adversarial-audit-r2.md | 195 | Stage 0-2 적대적 감리 2차 | 감리 |
| 17 | geuldobi-v2-stage0-2-hidden-internals-deepdive-full-survey.md | 963 | Stage 0-2 숨은 내부 구현 | 조사 |
| 18 | geuldobi-v2-static-improvement-discovery-3pass-audit.md | 653 | 정적 개선 발견 감리 | 감리 |
| 19 | geuldobi-v2-static-improvement-discovery-evidence-manifest.md | 131 | 정적 개선 근거 목록 | 근거 |
| 20 | geuldobi-v2-static-improvement-discovery-full-survey-audit-order.md | 285 | 정적 개선 조사 지시 | 지시 |
| 21 | geuldobi-v2-static-improvement-discovery-operator-prompt.md | 48 | 정적 개선 프롬프트 | 지시 |
| 22 | real-manuscript-quality-corpus-usage-direction-3pass-audit.md | 306 | 실물 원고 활용 방향 | 감리 |
| 23 | stage34-deep-dive-underexplored-areas-3pass-audit.md | 231 | Stage 3-4 비표면 영역 | 감리 |
| 24 | (ssot-consolidation-methodology.md) | — | 본 문서 | 방법론 |

### 1.2 중복 구조 분석

```
문서 유형 분포:
  조사(원본)   : 7개 (4,661행) — 사실 데이터의 1차 소스
  감리(검증)   : 13개 (4,663행) — 조사 결과를 검증·정정
  보고서       : 1개 (829행) — 독립 보고서
  근거/지시    : 3개 (464행) — 보조 문서
```

**핵심 문제**: 감리 문서가 조사 문서의 내용을 반복 인용 + 정정하므로, 동일 사실이 2-4곳에 흩어져 있고 **어느 것이 최종 정정본인지 불명확**.

---

## 2. SSOT 영역 분류

### 2.1 영역 정의

24개 문서를 **7개 SSOT 영역**으로 통합:

| SSOT ID | 영역명 | 소스 문서 | 핵심 내용 |
|---------|--------|----------|----------|
| **S1** | **아키텍처 개관** | #1 | 전체 구조, 규모, 기술 스택, 디렉토리 맵 |
| **S2** | **BE-FE 연결성** | #3, #4 | IPC 채널, REST/WS, 계약, 전송 프로토콜, 보안 경계 |
| **S3** | **프론트엔드** | #7, #8, #9 | Electron 내부, 렌더러, 스플래시, 설정 영속화 |
| **S4** | **LLM 통합** | #12, #10, #11, #13 | BaseAgent, 모델 선정, 프롬프트, 토큰 추적, 스키마 |
| **S5** | **Stage 0-2 내부 구현** | #17, #15, #16, #2 | Bible/Treatment/Style, Arc 앙상블, 제약, 침묵 실패 27건 |
| **S6** | **Stage 3-4 + 교차 계층** | #23, #5, #6 | Blueprint, 원고 생성, 검증 파이프라인, 크로스컷 이음매 |
| **S7** | **ROL + 정적 개선** | #14, #18, #19, #20, #21, #22 | 비용 추적, 통과율, ROI, 개선 후보, 실물 원고 활용 |

### 2.2 소스 문서 → SSOT 매핑 상세

```
S1 아키텍처 개관
  ← #1  geuldobi-codebase-full-survey (301행) [전량 흡수]

S2 BE-FE 연결성
  ← #3  be-fe-connectivity-deepdive-full-survey (815행) [주 소스]
  ← #4  be-fe-connectivity-frontend-improvement-survey (473행) [개선점 섹션 병합]

S3 프론트엔드
  ← #7  frontend-deepdive-3pass-audit (368행) [주 소스]
  ← #8  frontend-deepdive-adversarial-3pass-audit (585행) [정정 반영]
  ← #9  frontend-deepdive-adversarial-3pass-audit-r2 (446행) [최종 정정 반영]

S4 LLM 통합
  ← #12 llm-integration-deepdive-3pass-audit (651행) [주 소스]
  ← #10 llm-deepdive-adversarial-3pass-correction (456행) [정정 반영]
  ← #11 llm-deepdive-final-6pass-verdict (244행) [최종 판정 반영]
  ← #13 llm-model-selection-report (829행) [별도 섹션으로 포함]

S5 Stage 0-2 내부 구현
  ← #17 stage0-2-hidden-internals-deepdive-full-survey (963행) [주 소스, 6회 감리 반영 완료]
  ← #15 stage0-2-hidden-internals-adversarial-audit (201행) [감리 이력으로 부록화]
  ← #16 stage0-2-hidden-internals-adversarial-audit-r2 (195행) [감리 이력으로 부록화]
  ← #2  stage23-deepdive-hidden-areas-survey (432행) [Stage 2 부분 병합]

S6 Stage 3-4 + 교차 계층
  ← #23 stage34-deep-dive-underexplored-areas (231행) [주 소스]
  ← #5  crosscut-deepdive-hidden-seams (386행) [교차 계층 섹션 병합]
  ← #6  devils-advocate-pass3-audit (336행) [정정 반영]

S7 ROL + 정적 개선
  ← #14 rol-deepdive-full-survey (677행) [주 소스]
  ← #18 static-improvement-discovery-3pass-audit (653행) [개선 후보 병합]
  ← #19 static-improvement-discovery-evidence-manifest (131행) [근거 부록]
  ← #20 static-improvement-discovery-full-survey-audit-order (285행) [폐기 — 지시 문서]
  ← #21 static-improvement-discovery-operator-prompt (48행) [폐기 — 지시 문서]
  ← #22 real-manuscript-quality-corpus-usage-direction (306행) [별도 섹션으로 포함]
```

---

## 3. 통합 규칙

### 3.1 정보 우선순위 (최신 정정이 최우선)

```
감리 정정본 > 조사 원본 > 보조 문서
  ↓ 구체적으로:
  적대적 감리 2차(R2) > 적대적 감리 1차 > 3PASS 감리 > 조사 원본
```

**충돌 시**: 가장 늦은 감리에서 CONFIRMED/정정된 값을 채택.

### 3.2 중복 제거 원칙

| 원칙 | 설명 |
|------|------|
| **사실 1회 기재** | 동일 코드 근거(파일:행)를 참조하는 서술은 SSOT에 1회만 기재 |
| **감리 이력 부록화** | 감리 과정(CONFIRMED/WRONG/INACCURATE 목록)은 SSOT 본문이 아닌 **부록**에 요약 |
| **지시/프롬프트 문서 폐기** | 작업 지시(audit-order, operator-prompt)는 SSOT에 포함하지 않음 |
| **수치는 최종 정정값만** | 예: 500→450, 154→129(런타임) — SSOT에는 450, 129만 기재 |
| **코드 근거 필수** | 모든 사실 서술에 `파일:행` 근거 유지 |

### 3.3 SSOT 문서 표준 구조

각 SSOT 문서는 동일한 섹션 구조를 따름:

```markdown
# {영역명} SSOT

> **최종 갱신**: 2026-03-18
> **소스 문서**: (원본 목록)
> **감리 이력**: (감리 문서 목록 + 최종 정확도)

---

## 1. 개관
   (영역의 범위, 핵심 구성요소, 아키텍처 위치)

## 2. 상세 분석
   (영역별 세부 내용 — 코드 근거 포함)

## 3. 침묵 실패 / 엣지 케이스
   (해당 영역의 숨은 위험 경로)

## 4. 수치 요약표
   (핵심 수치를 한 테이블에 집약)

## 5. 발견 사항
   (강점, 사각지대, 관리 주의점)

## [부록 A] 감리 이력 요약
   (N회 감리, CONFIRMED/INACCURATE/WRONG 집계, 주요 정정 이력)

## [부록 B] 근거 파일 인벤토리
   (참조된 소스 파일 목록)
```

---

## 4. 통합 작업 절차

### 4.1 단계별 워크플로

```
[1단계] 주 소스 추출
  각 SSOT 영역의 "주 소스" 문서에서 사실 서술만 추출
  (감리 과정 서술, 방법론 서술, 중간 결과는 제외)

[2단계] 감리 정정 반영
  해당 영역의 감리 문서에서 WRONG/INACCURATE 정정을 주 소스에 적용
  → 최종 정정값만 SSOT에 기재

[3단계] 교차 영역 중복 제거
  여러 SSOT에 걸치는 주제(예: MetricsCollector는 S4+S7)를
  1개 SSOT에만 상세 기재, 나머지는 "→ S4 참조" 포인터

[4단계] 수치 요약표 생성
  각 SSOT의 핵심 수치를 한 테이블로 집약

[5단계] 부록 생성
  감리 이력 요약 + 근거 파일 인벤토리
```

### 4.2 교차 영역 소유권 결정

동일 주제가 여러 영역에 걸칠 때의 **소유 영역**:

| 주제 | 소유 SSOT | 참조하는 SSOT |
|------|----------|-------------|
| MetricsCollector (비용 추적) | S7 (ROL) | S4 (LLM 통합) |
| BaseAgent (LLM 호출) | S4 (LLM 통합) | S5 (Stage 0-2) |
| WebSocket /events | S2 (BE-FE) | S3 (프론트엔드) |
| response_schemas.py | S4 (LLM 통합) | S5, S6 |
| PassRateMonitor | S7 (ROL) | S6 (Stage 3-4) |
| ConstraintDB | S5 (Stage 0-2) | S6 (Stage 3-4) |
| GenreGuards | S5 (Stage 0-2) | S6 (Stage 3-4) |
| PresetRegistry | S5 (Stage 0-2) | — |
| Director Auditor | S6 (Stage 3-4) | S5 (Stage 2 판정) |
| bridge_server.py | S2 (BE-FE) | S7 (대시보드) |

### 4.3 폐기 문서 목록

통합 후 SSOT에 흡수되어 **독립 문서로 불필요**해지는 항목:

| 문서 | 사유 |
|------|------|
| #20 static-improvement-discovery-full-survey-audit-order.md | 작업 지시 (SSOT에 미포함) |
| #21 static-improvement-discovery-operator-prompt.md | 프롬프트 (SSOT에 미포함) |
| #15 stage0-2-hidden-internals-adversarial-audit.md | 감리 이력 → S5 부록으로 흡수 |
| #16 stage0-2-hidden-internals-adversarial-audit-r2.md | 감리 이력 → S5 부록으로 흡수 |
| #10 llm-deepdive-adversarial-3pass-correction.md | 감리 이력 → S4 부록으로 흡수 |
| #11 llm-deepdive-final-6pass-verdict.md | 최종 판정 → S4 부록으로 흡수 |
| #6 devils-advocate-pass3-audit.md | 감리 이력 → S6 부록으로 흡수 |
| #8 frontend-deepdive-adversarial-3pass-audit.md | 감리 이력 → S3 부록으로 흡수 |
| #9 frontend-deepdive-adversarial-3pass-audit-r2.md | 감리 이력 → S3 부록으로 흡수 |

**폐기 대상**: 9개 (3,404행) → 전량 SSOT 부록으로 흡수

### 4.4 산출물 예상 규모

| 항목 | 원본 | SSOT 예상 |
|------|------|----------|
| 문서 수 | 24개 | **7개** + 본 방법론 1개 |
| 총 행수 | 10,012행 | **~4,000-5,000행** (50-60% 압축) |
| 중복 제거 | — | ~3,000-4,000행 제거 |
| 감리 이력 | 본문에 혼재 | 부록으로 분리 |

---

## 5. SSOT 파일명 규약

```
ssot/
├── s1-architecture-overview.md          # 아키텍처 개관
├── s2-be-fe-connectivity.md             # BE-FE 연결성
├── s3-frontend-electron.md              # 프론트엔드
├── s4-llm-integration.md                # LLM 통합
├── s5-stage0-2-internals.md             # Stage 0-2 내부 구현
├── s6-stage3-4-crosscut.md              # Stage 3-4 + 교차 계층
└── s7-rol-static-improvement.md         # ROL + 정적 개선
```

---

## 6. 품질 게이트

### 6.1 SSOT 기재 전 체크리스트

- [ ] 모든 수치에 `파일:행` 코드 근거 존재
- [ ] 최종 감리 정정값만 기재 (구값 미포함)
- [ ] 교차 영역 주제는 소유 SSOT에만 상세, 나머지는 포인터
- [ ] 감리 이력은 부록에만 존재 (본문 미혼재)
- [ ] 지시/프롬프트 문서 내용 미포함

### 6.2 완성 후 검증

- [ ] 원본 24개 문서의 모든 CONFIRMED 사실이 SSOT 7개에 1회 이상 존재
- [ ] WRONG 정정 5건 모두 반영 확인 (W1-W5)
- [ ] INACCURATE 정정 19건 모두 반영 확인 (I1-I19)
- [ ] 신규 발견 11건 (MSF-A~K) 모두 S5/S6에 포함 확인
- [ ] 교차 참조 포인터 10건 양방향 확인

---

## 7. 작업 순서 권장

```
1. S5 (Stage 0-2) — 가장 큰 소스(963행) + 감리 가장 많음(6회)
2. S4 (LLM 통합) — 두 번째 큰 영역(829+651행) + 감리 3회
3. S2 (BE-FE) — 세 번째(815+473행), 감리 반영 적음
4. S7 (ROL + 정적 개선) — 다수 소스(677+653+306행)
5. S3 (프론트엔드) — 감리 3회 반영
6. S6 (Stage 3-4) — 소스 상대적 소규모
7. S1 (아키텍처 개관) — 가장 작음, 마지막 통합
```

---

## 8. 5회 반복 검증 프로토콜

### 8.1 원칙

**각 SSOT 문서당 최소 5회 반복** — 작성 1회 + 검증 4회로 누락 0건을 목표.

### 8.2 반복 정의

```
[R1] 초안 작성
  소스 문서에서 사실 추출 + 감리 정정 반영 + 표준 구조 적용
  산출: SSOT 초안

[R2] 소스 대조 (누락 검증)
  원본 소스 문서를 처음부터 끝까지 다시 읽으며
  SSOT에 빠진 CONFIRMED 사실이 있는지 1건씩 대조
  체크: 소스 문서의 모든 테이블·목록·수치가 SSOT에 존재하는가
  산출: 누락 항목 목록 → SSOT 보완

[R3] 감리 정정 전수 대조 (정정 반영 검증)
  해당 영역의 감리 문서(WRONG/INACCURATE 정정표)를 1건씩 확인
  SSOT에 구값이 남아있지 않은지 검증
  체크: W1-W5, I1-I19, MSF-A~K 중 해당 영역 항목이 모두 최종값으로 기재
  산출: 미반영 정정 목록 → SSOT 보완

[R4] 교차 영역 포인터 검증 (중복·단절 검증)
  §4.2 교차 영역 소유권 테이블 기준으로
  - 소유 SSOT에 상세 내용 존재하는가
  - 참조 SSOT에 "→ SN 참조" 포인터가 정확한가
  - 양방향 포인터가 끊기지 않았는가
  산출: 끊긴 포인터 목록 → SSOT 보완

[R5] 적대적 최종 감리 (반증 시도)
  SSOT 완성본의 수치·상수·동작 설명을 코드에서 직접 반증 시도
  "대략 맞음" 불합격 — 정확한 값만 통과
  산출: CONFIRMED/INACCURATE/WRONG 판정 → SSOT 최종 정정
```

### 8.3 반복 흐름도

```
  R1 초안 작성
       ↓
  R2 소스 대조 → 누락 발견? → Yes → 보완 후 R2 재실행
       ↓ No                          (누락 0건까지)
  R3 감리 정정 대조 → 미반영? → Yes → 보완 후 R3 재실행
       ↓ No                          (미반영 0건까지)
  R4 교차 포인터 검증 → 끊김? → Yes → 보완 후 R4 재실행
       ↓ No                          (끊김 0건까지)
  R5 적대적 감리 → WRONG? → Yes → 정정 후 R5 재실행
       ↓ No                          (WRONG 0건까지)
  ✅ SSOT 확정
```

**핵심**: R2-R5 각 단계에서 문제 발견 시 해당 단계를 **0건 달성까지 반복**. 따라서 실제 반복 횟수는 5회 이상이 될 수 있음. 5회는 **최소 하한선**.

### 8.4 단계별 기록 의무

각 반복마다 다음을 SSOT 부록에 기록:

```markdown
## [부록 A] 검증 이력

### R1 초안 (날짜)
- 소스 문서 N개에서 사실 M건 추출

### R2 소스 대조 (날짜)
- 1차: 누락 K건 발견 → 보완
- 2차: 누락 0건 확인 ✅

### R3 감리 정정 대조 (날짜)
- 정정 항목 N건 중 미반영 K건 → 보완
- 재확인: 미반영 0건 ✅

### R4 교차 포인터 검증 (날짜)
- 포인터 N건 중 끊김 K건 → 보완
- 재확인: 끊김 0건 ✅

### R5 적대적 감리 (날짜)
- 검증 N건: CONFIRMED M / INACCURATE K / WRONG J
- 정정 후 재검증: WRONG 0건 ✅
```

### 8.5 SSOT 확정 조건

하나의 SSOT가 확정되려면 **모든 조건 충족 필수**:

| 조건 | 기준 |
|------|------|
| R2 누락 | **0건** |
| R3 미반영 정정 | **0건** |
| R4 끊긴 포인터 | **0건** |
| R5 WRONG | **0건** |
| R5 INACCURATE | 정정 후 **0건** |
| 총 반복 횟수 | **≥ 5회** |

### 8.6 7개 SSOT × 5회 = 전체 작업 규모

| SSOT | 소스 행수 | 감리 정정 건수 | 교차 포인터 수 | 예상 난이도 |
|------|----------|-------------|-------------|-----------|
| S5 | 2,753 | 24건 (W1-5, I1-19) | 3 | 최고 |
| S4 | 2,180 | ~8건 | 3 | 고 |
| S2 | 1,288 | ~2건 | 2 | 중 |
| S7 | 2,100 | ~4건 | 2 | 고 |
| S3 | 1,399 | ~5건 | 1 | 중 |
| S6 | 953 | ~3건 | 4 | 중 |
| S1 | 301 | 0건 | 0 | 저 |

---

> **방법론 문서 종결**
> 24개 OPUS 문서 → 7개 영역 SSOT 통합 방법론 수립 완료.
> 예상 압축률: 50-60% (10,012행 → ~4,000-5,000행).
> **최소 5회 반복 검증 프로토콜** 적용 — R1 초안 + R2 누락 + R3 정정 + R4 포인터 + R5 적대적, 각 단계 0건 달성까지 반복.
> 다음 단계: 위 작업 순서에 따라 S5부터 SSOT 작성 착수.
