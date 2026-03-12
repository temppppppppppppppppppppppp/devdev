# 벤치마크 인사이트 추출 — 글도비 적용 가능 아이디어

> 작성일: 2026-03-10
> 대상 벤치마크 6종 + 보조 4종 = 총 10종 전수 분석
> 목적: 글도비 파이프라인에 흡수 가능한 아이디어 디테일 추출

---

## 분석 대상 벤치마크

| # | 이름 | 기관 | 핵심 기여 | 신뢰도 |
|---|------|------|----------|--------|
| 1 | **WebNovelBench** | 개인/소규모 | 웹소설 8차원 + PCA 백분위 랭킹 | B |
| 2 | **ConStory-Bench** | Microsoft + SUTD | 일관성 오류 5×19 분류 + 자동 탐지 | B+ |
| 3 | **Mazur Writing V4** | 개인(lechmazur) | 18문항 루브릭 + 7 LLM 채점단 | A- |
| 4 | **WritingBench** | Alibaba + 인민대 | 동적 쿼리별 평가 기준 생성 | B+ |
| 5 | **EQ-Bench Longform** | 개인(eqbench.com) | 8챕터 열화 추적 + 14차원 + Slop 탐지 | B- |
| 6 | **LitBench** | Stanford | 인간 선호 2,480쌍 + 보상모델 78% | A |
| 7 | lars76/story-evaluation | 개인 | 15차원 × 15모델 × 8,520편 | C+ |
| 8 | DramaBench | 학술 | 스크립트 연속성 6차원 | B |
| 9 | CS4 | 학술 | 제약 수↑ = 창의성 측정 | B |
| 10 | Coherence Framework | 학술 | Cohesion/Consistency/Relevance 3축 | B |

---

## §1. 글도비가 이미 앞서는 영역

벤치마크들이 "평가"만 하는 것을 글도비는 "생성 + 평가 + 수정" 루프로 운영 중.

| 벤치마크 차원 | 글도비 대응 시스템 | 상태 |
|-------------|-----------------|------|
| 캐릭터 일관성 (WNB-D5, ConStory-Cat2, Mazur-Q1) | TruthGate 7검사 + NpcDriftAdvisor + NC-1 + consistency_checklist 17항목 | ✅ 운영 중 |
| 타임라인 모순 (ConStory-Cat1) | NC-2 timeline + NS-4 Arc 시간 연속성 + cumulative_elapsed | ✅ 운영 중 |
| 수치 불일치 (ConStory-Cat4-Quantitative) | NC-1 9개 검사 (FactLedger 교차/산술/레버리지 등) | ✅ 운영 중 |
| 세계관 규칙 위반 (ConStory-Cat3) | TruthGate _check_world_law_violation + GenreGuard 10종 | ✅ 운영 중 |
| 시점 혼선 (ConStory-Cat5-Perspective) | pre_llm_validator V70 POV + InfoParadoxChecker 1인칭 | ✅ 운영 중 |
| 이름 혼동 (ConStory-Cat4-Nomenclature) | NC-2 NPC 동명이인 감지 + M-4 괄호 정규화 | ✅ 운영 중 |
| 멀티 채점자 앙상블 (Mazur 7-grader) | Director SC 투표 + Ensemble 3후보 + 재심사 루프 | ✅ 운영 중 |
| 요소 제약 준수 (Mazur 9A-9J) | Treatment 블록 수치 목표 + NS-3-B 교차검증 + TF-B 블록 경계 규칙 | ✅ 운영 중 |
| 장르별 평가 분화 | GenreGuard 10종 + WorkGuard YAML + StyleGuard | ✅ 운영 중, 벤치마크들은 장르 무분별 |

---

## §2. 흡수 가능 아이디어 — 1차 전수조사

### IDEA-01: CED (Consistency Error Density) 메트릭 도입
- **출처**: ConStory-Bench
- **정의**: `CED = 오류_수 / (글자_수 / 10,000)`
- **글도비 적용**: 에피소드별 NC-1 + TruthGate + Advisory 경고 총합을 글자수로 정규화. `episode_quality_labels` 테이블에 `ced_score` 컬럼 추가. Arc 단위/전체 작품 단위 CED 추세 추적 가능.
- **구현 난이도**: 낮음 (Python-only, advisory 카운트 집계)
- **ROI**: 높음 — 작품 간/모델 간 일관성 품질을 단일 숫자로 비교 가능
- **우선순위**: **P0**

### IDEA-02: 서사 중반 집중 검증 (Middle Slump Detection)
- **출처**: ConStory-Bench — 모순은 서사 40-60% 지점에 집중
- **글도비 적용**: Arc 내 에피소드 위치(arc_pos / ep_count)가 40-60% 구간일 때 Director advisory에 `[Middle Slump 경고]` 주입. 해당 구간에서 TruthGate/NC-1 검사 임계값을 하향 (더 엄격하게).
- **구현 난이도**: 낮음 (arc_pos 비율 계산 + advisory 문자열 추가)
- **ROI**: 중간 — 실파이프라인 검증 필요
- **우선순위**: **P1**

### IDEA-03: 동적 쿼리별 평가 기준 생성 (Director 프롬프트)
- **출처**: WritingBench — 정적 기준 65% vs 동적 기준 87% 인간 정합
- **글도비 적용**: Director AUDIT 프롬프트에서 Blueprint의 core_tension/emotional_arc/장르 특성을 기반으로 **에피소드별 5개 맞춤 평가 기준**을 LLM이 생성하게 하고, 해당 기준으로 채점. 현재 고정 17항목 체크리스트와 병행.
- **구현 난이도**: 중간 (Director 프롬프트 수정 + 응답 파싱)
- **ROI**: 높음 — WritingBench가 정적 대비 +22%p 정합 향상을 보여줌
- **우선순위**: **P1**
- **주의**: 대원칙 3(Director 주권) 존중 — 동적 기준은 Director가 직접 생성, Python이 생성하면 안 됨

### IDEA-04: 8차원 서사 품질 점수 (WebNovelBench 차원 채택)
- **출처**: WebNovelBench 8차원 (수사법/감각묘사/캐릭터균형/대사독특성/캐릭터일관성/분위기정합/맥락적절성/씬전환)
- **글도비 적용**: `episode_quality_labels`에 8차원 점수를 Director가 채점하도록 추가. PCA 가중치 적용하여 단일 composite score 산출. 한국 웹소설 기준 백분위 산출은 레퍼런스 코퍼스 필요.
- **현재 커버리지 갭**:
  - **D1 수사법(Literary Devices)**: 미커버 → PatternTracker에 은유/상징 빈도 추적 추가
  - **D2 감각묘사(Sensory Detail)**: 미커버 → self-critique 신규 체크
  - **D3 캐릭터균형(Character Balance)**: 부분 커버 → 대사 비율/심리묘사 분포 측정 추가
  - **D6 분위기정합(Atmospheric Alignment)**: 부분 커버 (QM-1 체크14) → Blueprint emotional_arc 대비 톤 교차검증 강화
- **구현 난이도**: 높음 (Director 스키마 확장 + PCA 가중치 캘리브레이션)
- **ROI**: 높음 — 웹소설 도메인 직격, 품질 추적 다차원화
- **우선순위**: **P1**

### IDEA-05: 챕터별 열화 추적 (Quality Degradation Sparkline)
- **출처**: EQ-Bench Longform — 8챕터 걸쳐 품질 열화 패턴 시각화
- **글도비 적용**: `episode_quality_labels`의 score 시계열로 Arc 내/전체 작품 열화 곡선 산출. `FailureAnalyzer`에 `quality_degradation_report()` 메서드 추가. 단조 하락 3화 연속 감지 시 Arc 생성 단계에 경고 주입 (현재 FL-5가 5화 lookback인데, 이를 시각화 가능하게 확장).
- **구현 난이도**: 낮음 (이미 FL-5 인프라 존재)
- **ROI**: 중간 — 운영자 가시성 향상
- **우선순위**: **P2**

### IDEA-06: Slop 탐지 (AI 특유 표현 필터)
- **출처**: EQ-Bench — AI-ism 마스터 리스트 + bigram/trigram 빈도 매칭
- **글도비 적용**: `chief_writer_quality`에 `_check_ai_slop()` 추가. "심장이 두근거렸다", "눈빛이 흔들렸다", "주먹을 불끈 쥐었다" 같은 한국어 AI 클리셰 리스트 기반 빈도 체크. 임계값 초과 시 self-critique advisory.
- **구현 난이도**: 중간 (한국어 클리셰 리스트 구축 필요)
- **ROI**: 높음 — 웹소설 독자가 가장 싫어하는 것이 "AI 냄새"
- **우선순위**: **P0**

### IDEA-07: 토큰 엔트로피 기반 조기 경보
- **출처**: ConStory-Bench — 오류 구간에서 토큰 엔트로피 12-19% 상승
- **글도비 적용**: Gemini API logprobs가 지원되면 `_generate_content()` 반환에서 per-token entropy 계산. 문장 평균 엔트로피가 전체 평균 대비 15%+ 초과 구간을 `[Entropy Alert]`로 Director에 전달.
- **구현 난이도**: 높음 (Gemini API logprobs 지원 여부 확인 필요, 현재 미지원 가능성)
- **ROI**: 높음 — 모순 사전 탐지의 본질적 해결
- **우선순위**: **P2** (API 제약으로 즉시 구현 불가 시 보류)

### IDEA-08: Power Mean 채점 집계 (Holder Mean, p=0.5)
- **출처**: Mazur V4 — p=0.5 power mean으로 약점 차원에 가중 페널티
- **글도비 적용**: Director `score_breakdown` 합산 시 현재 단순 합산 → power mean (p=0.5) 변환. 약점 차원이 전체 점수를 더 크게 끌어내림. "평균적으로 좋은데 한 곳이 심각한" 원고를 더 정확하게 거름.
- **구현 난이도**: 낮음 (수학 공식 1줄)
- **ROI**: 중간 — NC-3B에서 이미 breakdown 합산 교정 중이므로 증분 개선
- **우선순위**: **P2**

### IDEA-09: 실패 패턴 근본 원인 클러스터링
- **출처**: Mazur V4 — `prompt_poor_writing_themes.txt`로 실패를 표면 증상이 아닌 근본 메커니즘으로 클러스터링
- **글도비 적용**: `FailureAnalyzer`에 `cluster_failure_mechanisms()` 추가. `stage_attempts`의 `reject_reason` + `failure_category` + `contradiction_types`를 LLM으로 근본 원인 클러스터링. "캐릭터 역량 과잉"(Mazur의 hyper-competent protagonist), "반영 과다"(reflection overwhelming momentum), "진단 라벨링"(diagnostic labels in peak beats = tell-don't-show) 같은 메커니즘 수준 패턴 식별.
- **구현 난이도**: 중간 (LLM 1회 호출 + 기존 DB 데이터 활용)
- **ROI**: 높음 — Arc 생성 시 반복 실패 근본 원인을 직접 주입
- **우선순위**: **P1**

### IDEA-10: 요소 통합 품질 분리 채점 (Craft vs Element)
- **출처**: Mazur V4 — Craft(60%) vs Element Integration(40%) 분리, 상관 0.836
- **글도비 적용**: Director `score_breakdown`을 두 그룹으로 분리:
  - **Craft** (서사 기교): 캐릭터 깊이, 플롯 구조, 분위기, 긴장도, 독창성, 톤, 시점, 문체
  - **Constraint** (제약 준수): Treatment 블록 목표, 수치 정합, 아이템 획득, 시간 연속성
  - 각각 독립 점수 산출 → 전체 점수에 가중 합산
- **구현 난이도**: 중간 (Director 스키마 확장)
- **ROI**: 중간 — "글은 잘 쓰는데 설정을 안 지킨다" vs "설정은 지키는데 글이 재미없다" 진단 분리
- **우선순위**: **P2**

### IDEA-11: 대사 자연스러움 전용 체크
- **출처**: lars76 q10 (Natural Dialogue) + EQ-Bench "Weak Dialogue" 차원 + Mazur Q1 대사 정책
- **글도비 적용**: `chief_writer_quality`에 `_check_dialogue_naturalness()` 추가. 대사 비율 측정 (전체 대비 %), 연속 서술문 5줄+ 경고 (이미 QM-1 체크13이 유사), 대사 태그 반복 ("~라고 말했다" 연속 사용) 감지.
- **구현 난이도**: 낮음 (regex 기반)
- **ROI**: 중간
- **우선순위**: **P2**

### IDEA-12: 제약 개수 vs 창의성 트레이드오프 측정
- **출처**: CS4 — 제약 증가 시 LLM 창의성 저하 측정
- **글도비 적용**: Treatment 블록의 제약 밀도(필수 이벤트 수, 수치 목표 수, NPC 등장 수)와 Director 점수의 상관 분석. 특정 임계값 이상의 제약 밀도에서 품질 하락이 관찰되면, Arc 생성 시 제약 분산(블록 당 제약 수 상한) 권고.
- **구현 난이도**: 낮음 (통계 분석, DB 데이터 활용)
- **ROI**: 낮음 — 인사이트 수준
- **우선순위**: **P3**

### IDEA-13: 외관 불일치 자동 감지
- **출처**: ConStory-Bench Cat4 — Appearance Mismatches (외모 묘사 불일치)
- **글도비 적용**: `npc_history` known_attrs에 `appearance` 필드 추가. NpcDriftAdvisor가 원고 내 NPC 외모 묘사를 스냅샷과 대조. "검은 머리"→"금발" 같은 변경 감지.
- **구현 난이도**: 중간 (LLM 추출 + 비교)
- **ROI**: 중간 — 장기 연재에서 발생 빈도 높음
- **우선순위**: **P2**

### IDEA-14: 망각된 능력 감지 (Forgotten Abilities)
- **출처**: ConStory-Bench Cat2 — 캐릭터가 확립된 능력을 갈등 해결에 미사용
- **글도비 적용**: `WorldState` known_attrs의 skills/abilities를 추적하여, 위기 상황에서 해당 능력이 언급/사용되지 않으면 advisory 생성. "주인공이 X 능력을 보유하고 있으나 이번 위기에서 미활용"
- **구현 난이도**: 높음 (위기 상황 탐지 + 능력 활용 여부 판단 = LLM 필요)
- **ROI**: 중간 — 독자 불만의 주요 원인
- **우선순위**: **P2**

### IDEA-15: 원인 없는 결과 감지 (Causeless Effects)
- **출처**: ConStory-Bench Cat1 — 사전 설정 없이 갑자기 나타나는 능력/자원/결과
- **글도비 적용**: NC-1의 "처음" 이벤트 모순 검사 확장. `items_acquired`에 없는 아이템이 사용되거나, `skills`에 없는 능력이 발휘되면 MAJOR 경고. 현재 BUG-A/BUG-F로 부분 커버 중이나, "능력" 차원은 미커버.
- **구현 난이도**: 중간
- **ROI**: 높음 — 독자가 "데우스 엑스 마키나"로 느끼는 핵심 요인
- **우선순위**: **P1**

### IDEA-16: 방치된 플롯 요소 감지 강화 (Abandoned Plot Elements)
- **출처**: ConStory-Bench Cat1 — 설정된 후 해결/언급 없이 사라지는 플롯 요소
- **글도비 적용**: 현재 B-4(동기/약속 방치 감지)가 CW self-critique 5번째 체크로 존재. 이를 **DB 기반 정량 추적**으로 강화: `foreshadow_tracker`의 pending 씨앗 중 20화+ 경과 시 `[Stale Plot Element]` MAJOR advisory 자동 생성 (현재 DB-4가 유사하나 임계값/심각도 강화).
- **구현 난이도**: 낮음 (기존 인프라 활용)
- **ROI**: 중간
- **우선순위**: **P2**

### IDEA-17: 인간 선호 기반 보상 모델 캘리브레이션
- **출처**: LitBench — 인간 선호 레이블로 학습한 보상모델이 78% 정확도, 단독 LLM judge 73% 초과
- **글도비 적용**: Director 점수와 실제 독자 반응(플랫폼 업로드 후 조회수/좋아요) 상관 분석. 높은 괴리가 관찰되면 Director 프롬프트 캘리브레이션. 당장은 데이터 부족이나, 장기적으로 가장 가치 있는 방향.
- **구현 난이도**: 높음 (외부 데이터 수집 필요)
- **ROI**: 최고 — 궁극적 품질 지표
- **우선순위**: **P3** (데이터 축적 후)

---

## §3. 2차 전수조사 — 교차 검증 및 중복 제거

| IDEA | 중복/기존 대응 여부 | 최종 판정 |
|------|-------------------|----------|
| 01-CED | 신규. 기존 advisory 카운트는 있으나 정규화 메트릭 없음 | ✅ 유지 |
| 02-Middle Slump | 신규. arc_pos 기반 검증 강화 없었음 | ✅ 유지 |
| 03-동적 기준 | 신규. 현재 Director는 고정 17항목 체크리스트 | ✅ 유지 |
| 04-8차원 | 부분 중복. D5/D7/D8은 이미 커버. D1/D2/D3/D6 갭 존재 | ✅ 갭 부분만 유지 |
| 05-열화 추적 | 부분 중복. FL-5가 5화 하락 감지 중. 시각화만 추가 | ⬇️ P2→P3 하향 |
| 06-Slop | 신규. `_check_system_term_exposure`가 유사하나 AI 클리셰와는 다른 목적 | ✅ 유지 |
| 07-엔트로피 | 신규. API 제약으로 즉시 구현 불가 | ⬇️ 보류 (API 의존) |
| 08-Power Mean | 부분 중복. NC-3B 합산 교정과 유사한 효과 | ⬇️ P2→P3 하향 |
| 09-실패 클러스터 | 부분 중복. A-4 contradiction_types 수렴 추적 존재. 근본 원인 수준은 신규 | ✅ 유지 |
| 10-Craft/Constraint 분리 | 신규. 현재 단일 score | ✅ 유지 |
| 11-대사 | 부분 중복. QM-1 체크13(벽돌 문단) + QM-2 dialogue_naturalness 존재 | ⬇️ P2→P3 하향 |
| 12-제약 밀도 | 신규. 통계 분석 수준 | 유지 (P3) |
| 13-외관 불일치 | 신규. NpcDriftAdvisor가 4필드(injury/location/permanent_injuries/relation) 추적 중이나 appearance 미포함 | ✅ 유지 |
| 14-망각 능력 | 신규. 현재 능력 활용 여부 추적 없음 | ✅ 유지 |
| 15-원인 없는 결과 | 부분 중복. BUG-A(금지 아이템) + NC-1("처음" 이벤트). 능력 차원 미커버 | ✅ 갭 부분만 유지 |
| 16-방치 플롯 | 부분 중복. B-4 + DB-4. 임계값/심각도 강화만 추가 | ⬇️ P2 유지하되 범위 축소 |
| 17-보상모델 | 신규. 데이터 축적 필요 | 유지 (P3) |

---

## §4. 3차 전수조사 — 최종 우선순위 확정

### P0 (즉시 구현 가능, 높은 ROI)

| # | 아이디어 | 구현 범위 | 예상 영향 |
|---|---------|----------|----------|
| **01** | **CED 메트릭 도입** | `episode_quality_labels`에 `ced_score` 컬럼 + `FailureAnalyzer.compute_ced()` | 작품 간 일관성 품질 단일 숫자 비교 |
| **06** | **AI Slop 탐지** | `chief_writer_quality._check_ai_slop()` + 한국어 클리셰 리스트 YAML | "AI 냄새" 제거, 독자 이탈 방지 |

### P1 (다음 배치, 중간 구현 난이도)

| # | 아이디어 | 구현 범위 | 예상 영향 |
|---|---------|----------|----------|
| **02** | **Middle Slump 검증 강화** | arc_pos 40-60% 구간 advisory + 검사 임계값 하향 | 서사 중반 모순 사전 포착 |
| **03** | **동적 평가 기준 생성** | Director AUDIT 프롬프트에 에피소드별 5개 맞춤 기준 생성 지시 추가 | 정적 대비 +22%p 정합 (WritingBench 수치 기반) |
| **04** | **서사 품질 4차원 갭 해소** | D1 수사법 빈도 + D2 감각묘사 체크 + D3 캐릭터 대사비율 + D6 분위기 교차검증 | 품질 다차원 측정 |
| **09** | **실패 근본 원인 클러스터** | `FailureAnalyzer.cluster_failure_mechanisms()` LLM 1회 | Arc 생성 시 반복 실패 메커니즘 직접 주입 |
| **15** | **원인 없는 결과 감지** | 능력/자원 출현 vs WorldState/FactLedger 교차검증 | 데우스 엑스 마키나 방지 |

### P2 (후순위, 낮은 긴급성)

| # | 아이디어 | 비고 |
|---|---------|------|
| **10** | Craft/Constraint 분리 채점 | Director 스키마 확장 필요 |
| **13** | 외관 불일치 감지 | NpcDriftAdvisor appearance 필드 추가 |
| **14** | 망각된 능력 감지 | LLM 필요, 높은 구현 비용 |
| **16** | 방치 플롯 강화 | DB-4 임계값/심각도 조정 수준 |

### P3 (장기/보류)

| # | 아이디어 | 비고 |
|---|---------|------|
| **05** | 열화 추적 시각화 | FL-5 인프라 존재, 시각화만 추가 |
| **07** | 토큰 엔트로피 조기 경보 | Gemini API logprobs 미지원 시 불가 |
| **08** | Power Mean 집계 | NC-3B 교정과 중복 |
| **11** | 대사 전용 체크 | QM-1/QM-2에서 부분 커버 |
| **12** | 제약 밀도 분석 | 인사이트 수준 |
| **17** | 인간 선호 보상모델 | 독자 데이터 축적 후 |

---

## §5. 벤치마크별 핵심 수치/방법론 레퍼런스

### ConStory-Bench 오류 분류 전체 (19 유형)

**Category 1: Timeline & Plot Logic (6)**
1. Absolute Time Contradictions — 날짜/요일/계절 충돌
2. Duration Contradictions — 동일 사건 시간 측정 불일치
3. Simultaneity Contradictions — 캐릭터/오브젝트 동시 다중 위치
4. Causeless Effects — 사전 설정 없는 능력/자원/결과
5. Causal Logic Violations — 확립된 스토리 규칙과 모순되는 인과
6. Abandoned Plot Elements — 해결/언급 없이 사라지는 플롯 요소

**Category 2: Characterization (4)**
7. Memory Contradictions — 캐릭터가 본인 정보를 잊거나 없는 기억을 가짐
8. Knowledge Contradictions — 배경을 초월하는 지식/어휘/기술 표시
9. Skill/Power Fluctuations — 설명 없는 능력 급변
10. Forgotten Abilities — 확립된 능력을 갈등 해결에 미사용

**Category 3: World-building & Setting (3)**
11. Core Rules Violations — 작가가 명시한 세계 법칙 위반
12. Social Norms Violations — 확립된 사회 체계와 모순되는 행동
13. Geographical Contradictions — 지리적 속성/상대 위치 불일치

**Category 4: Factual & Detail Consistency (3)**
14. Appearance Mismatches — 동일 캐릭터/오브젝트 외모 묘사 변경
15. Nomenclature Confusions — 이름 혼동/불일치
16. Quantitative Mismatches — 수치 정보 수학적 불일치

**Category 5: Narrative & Style (3)**
17. Perspective Confusions — 시점 혼선 (국소적, 4.7% 갭)
18. Tone Inconsistencies — 설명 없는 톤 전환
19. Style Shifts — 동일 서사 내 문체 불일치

### ConStory-Bench 핵심 수치
- **Factual & Detail Consistency가 지배적 실패 모드** (전 모델 CED 최고)
- **Timeline & Plot Logic이 2위**
- **Narrative & Style은 거의 0에 가까움** (LLM이 문체 일관성은 잘 유지)
- **모순 위치**: 팩트 설정 20-24%, 모순 발생 34-49% (중앙값 40-60%)
- **Factual↔Characterization 상관 0.304**, Factual↔World 0.255 (팩트 오류가 허브)
- **ConStory-Checker F1=0.678** (인간 F1=0.229의 3배)

### Mazur V4 핵심 수치
- **18문항 (8 Craft 60% + 10 Element 40%)**
- **Power mean p=0.5** (약점 페널티 강화)
- **7 LLM 채점자** (Claude Sonnet 4.5, DeepSeek V3.2, Gemini 3 Pro, GPT-5.1, Grok 4.1, Kimi K2, Qwen 3 Max)
- **Leave-One-Grader-Out**: 최대 ±3 랭크 변동 (안정적)
- **Craft↔Element 상관 0.836** (높지만 완전하지 않음 → 분리 채점 의미 있음)
- **실패 패턴**: Under-pressurized narrative, Hyper-competent protagonist, Reflection overwhelming momentum, Diagnostic labels in peak beats

### WritingBench 핵심 수치
- **동적 기준 87% 인간 정합** (정적 글로벌 65%, 정적 도메인별 40%)
- **Critic 모델 (Qwen-2.5-7B) 83% 정합**
- **Literature & Arts가 전 모델 최저 점수 도메인**
- **CoT 모델이 창작에서도 우위** (8.66 vs 8.49)
- **길이 제약 준수가 가장 약한 차원**

### WebNovelBench 핵심 수치
- **4,000 중국 웹소설 코퍼스**
- **PCA 1차 주성분 75.6% 분산 설명** (단일 "품질" 인자)
- **D5 캐릭터 일관성 가중치 최고 (0.1377)**
- **8차원 가중치 범위 0.1152-0.1377** (거의 균등)
- **평가: DeepSeek-V3 단일 모델, 1-5 스케일, 레벨별 루브릭 없음**

### EQ-Bench Longform 핵심 수치
- **13단계 생성 파이프라인** (5 계획 + 8 챕터)
- **14 챕터 레벨 차원** (8 긍정 + 6 결함)
- **0-20 스케일**, Forced Poetry에 **5x 가중치 (^1.7 지수)**
- **500 부트스트랩 리샘플** 95% CI
- **Claude Sonnet 4 단일 채점자** (v1.11, 2026-02-19)

---

## §6. 글도비 vs 벤치마크 커버리지 매트릭스

```
ConStory 19유형 vs 글도비 커버리지:

[✅ 완전 커버]
 1. Absolute Time        → NC-2 timeline + NS-4
 5. Causal Logic          → TruthGate + Director AUDIT
11. Core Rules            → TruthGate _check_world_law_violation
15. Nomenclature          → NC-2 NPC 동명이인 + M-4
16. Quantitative          → NC-1 9개 검사
17. Perspective           → pre_llm_validator V70 + InfoParadoxChecker

[⚠️ 부분 커버]
 2. Duration              → cumulative_elapsed (시간량 추적은 하나 지속시간 교차검증 미약)
 3. Simultaneity          → 미커버 (동시 위치 모순 전용 검사 없음)
 6. Abandoned Plot        → B-4 + DB-4 (있으나 임계값 약함)
 7. Memory                → NpcDriftAdvisor (LLM advisory, 완전 자동 아님)
 8. Knowledge             → InfoParadoxChecker (1인칭 전용, 3인칭 미커버)
12. Social Norms          → GenreGuard (장르 규칙은 잡으나 사회 규범 전용은 아님)
13. Geographical          → NC-2 공간연속성 (프롬프트 수준, Python 자동검증 아님)
14. Appearance            → NpcDriftAdvisor 4필드 (appearance 미포함)
18. Tone Inconsistencies  → QM-1 체크14 (부분)
19. Style Shifts          → StyleGuard (있으나 에피소드 내 변동 미탐지)

[❌ 미커버]
 4. Causeless Effects     → 능력/자원 출현 교차검증 없음
 9. Skill/Power Fluct.    → 능력 수준 추적 없음
10. Forgotten Abilities   → 능력 활용 여부 추적 없음
```

---

## §7. 구현 로드맵 제안

```
Phase A (P0, 즉시): CED 메트릭 + AI Slop 탐지
  → 2개 파일 수정 (failure_analyzer.py, chief_writer_quality.py)
  → 1개 YAML 추가 (ai_slop_patterns.yaml)
  → episode_quality_labels 1컬럼 추가

Phase B (P1, 다음 배치): Middle Slump + 동적 기준 + 4차원 갭 + 실패 클러스터 + Causeless Effects
  → Director 프롬프트 수정 3곳
  → stage4_interview_round advisory 1곳
  → FailureAnalyzer 1메서드
  → chief_writer_quality 2체크 추가
  → NC-1 또는 신규 모듈에 능력/자원 교차검증

Phase C (P2, 후순위): Craft/Constraint 분리 + 외관 + 망각능력 + 방치플롯
  → Director 스키마 확장
  → NpcDriftAdvisor appearance 필드
  → LLM advisory 신규 1종
```

---

## 참고 문헌

1. WebNovelBench — [arXiv:2505.14818](https://arxiv.org/abs/2505.14818) / [GitHub](https://github.com/OedonLestrange42/webnovelbench)
2. ConStory-Bench — [arXiv:2603.05890](https://arxiv.org/abs/2603.05890) / [HuggingFace](https://huggingface.co/datasets/jayden8888/ConStory-Bench)
3. Mazur Writing V4 — [GitHub](https://github.com/lechmazur/writing)
4. WritingBench — [arXiv:2503.05244](https://arxiv.org/html/2503.05244v2)
5. EQ-Bench Longform — [Leaderboard](https://eqbench.com/creative_writing_longform.html) / [GitHub](https://github.com/EQ-bench/longform-writing-bench)
6. LitBench — [arXiv:2507.00769](https://arxiv.org/abs/2507.00769)
7. lars76/story-evaluation — [GitHub](https://github.com/lars76/story-evaluation-llm)
8. DramaBench — [arXiv:2512.19012](https://arxiv.org/abs/2512.19012)
9. CS4 — [arXiv:2410.04197](https://arxiv.org/abs/2410.04197)
10. Coherence Framework — [arXiv:2310.00598](https://arxiv.org/abs/2310.00598)
