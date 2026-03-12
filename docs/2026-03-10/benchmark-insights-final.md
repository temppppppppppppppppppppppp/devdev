# 벤치마크 인사이트 — 글도비 적용 최종 통합본

> 작성일: 2026-03-10
> 소스: 벤치마크 10종 + 학술 연구 28종 + 상용 도구 8종 + 독자 연구 6종 = **50+ 소스** 전수 분석
> 감리 기준: 95% 확신도 — 글도비 탑다운 아키텍처 정합성 + 대원칙 4개 준수 필터

## CODEX 코멘트 (3-pass 감리)

### 총평

- **유용함은 있음**: 벤치마크 아이디어를 글도비 아키텍처에 맞게 걸러낸 리서치 메모로는 가치가 높다.
- **단, 실행 문서로는 보정 필요**: 일부 P0/P1 항목이 "완전 신규"처럼 적혀 있으나, 실제 코드는 이미 **부분 구현/인접 구현**을 갖고 있다.
- **권장 용도**: 그대로 구현 오더로 쓰기보다, **백로그 우선순위 회의용 참고 문서**로 사용하는 것이 안전하다.

### 핵심 이견

1. **P0/P1 일부는 0→1 신규 기능이 아니다**
   - `대화 비율`, `능력/자원`, `중반부 arc 위치 기반 조정`은 현재 코드에 이미 부분 구현이 존재한다.
   - 따라서 "도입"보다 **기존 검사의 통합/정교화/승격**으로 보는 편이 정확하다.

2. **IDEA-07 "Gemini API logprobs 미지원. 구현 불가"는 단정이 과하다**
   - 감리 시점 기준으로는 "API 차원 불가"보다는 **모델 지원 편차/운영 리스크가 커서 현시점 보류** 정도가 더 정확하다.
   - 즉, 이 항목은 `부록(API대기)`보다 `부록(운영대기)` 성격에 가깝다.

3. **P0 공수 추정은 낙관적이다**
   - `~50줄 + 1 YAML`은 gzip/Burstiness 수준에는 가깝지만, `CED`처럼 DB 저장/조회/소비면을 함께 건드리는 항목까지 합친 총공수로는 작게 잡혀 있다.

4. **논문 수치를 글도비 예상 효과처럼 읽으면 안 된다**
   - `WritingBench 87% vs 65%`, `CheckEval IAA +0.45` 등은 **원 논문 조건의 결과**다.
   - 글도비에는 "구조 아이디어 차용"까지만 안전하며, **동일 개선폭을 기대효과로 읽는 것은 과장**이다.

### 실무적으로 건질 것

- **CED 메트릭**: 게이트 규칙이 아니라 `대시보드/추세 지표`로 도입하면 유용하다.
- **CheckEval 이진 분해**: NC-3 전체가 아니라 **핵심 3~5개 축에 한정**하면 ROI가 있다.
- **실패 메커니즘 클러스터링**: 강한 자동 판단보다 `FailureAnalyzer advisory`로 파일럿하는 쪽이 맞다.

### 그대로 받지 말아야 할 것

- `대화 비율 25-35%`를 절대 타깃처럼 쓰는 것
- 상용 도구 유래 `복잡도 2.0-3.0` 같은 불투명 임계값을 바로 규칙화하는 것
- `능력/자원 출현 교차검증 = 현재 0% 미커버`라고 보는 것
- `Gemini logprobs = 구현 불가`로 못 박는 것

### 실행용 재분류 권장

- **P0 유지 가능**: `CED`, `gzip`, `Burstiness/Complexity`, `AI Slop`
- **표현 수정 필요**: `대화 비율`, `능력/자원`, `Middle Slump`
- **효과 과장 주의**: `동적 기준`, `CheckEval 이진 분해`

---

## 분석 대상 소스 (50+종)

### 벤치마크/프레임워크 (28종)

| # | 이름 | 기관 | 핵심 기여 | 신뢰도 |
|---|------|------|----------|--------|
| 1 | **WebNovelBench** | 개인 | 웹소설 8차원 + PCA 백분위 랭킹 | B |
| 2 | **ConStory-Bench** | Microsoft+SUTD | 일관성 오류 5×19 분류 + CED 메트릭 | B+ |
| 3 | **Mazur Writing V4** | 개인 | 18문항 루브릭 + 7 LLM 채점단 + Power Mean | A- |
| 4 | **WritingBench** | Alibaba+인민대 | 동적 쿼리별 평가 기준 생성 | B+ |
| 5 | **EQ-Bench Longform** | 개인 | 8챕터 열화 추적 + Slop 탐지 | B- |
| 6 | **LitBench** | Stanford | 인간 선호 2,480쌍 + 보상모델 78% | A |
| 7 | **lars76** | 개인 | 15차원 × 15모델 × 8,520편 | C+ |
| 8 | **DramaBench** | 학술 | 스크립트 연속성 6차원 | B |
| 9 | **CS4** | 학술 | 제약 수↑ = 창의성↓ 측정 | B |
| 10 | **Coherence Framework** | 학술 | Cohesion/Consistency/Relevance 3축 | B |
| 11 | **LongStoryEval** | ACL 2025 | 100K+ 토큰 서적 8차원 20하위 + NovelCritique 8B | **A** |
| 12 | **NarraBench** | Cornell+McGill | 서사학 Big-4 × 50태스크 메타분석 | **A-** |
| 13 | **SCORE** | arXiv 2025 | 에피소드 일관성 — State Tracking + Hybrid Retrieval | B+ |
| 14 | **"Novel" Benchmark** | ACL Findings 2025 | Macro/Meso/Micro 3단계, EN+CN | A- |
| 15 | **ASE (HANNA)** | TACL 2024 | 6차원 × 1,056편 × 19,008 주석 | **A** |
| 16 | **CheckEval** | EMNLP 2025 | 이진 체크리스트 분해, IAA +0.45 | **A** |
| 17 | **CHARACTERBENCH** | AAAI 2025 | 캐릭터 커스터마이징 22,859 주석 | **A** |
| 18 | **TIMECHARA** | ACL 2024 | 시점별 캐릭터 할루시네이션 | **A** |
| 19 | **CollabStory** | NAACL 2025 | 32,000+ 멀티LLM 연속성 테스트 | A- |
| 20 | **CritiCS** | EMNLP 2024 | 역할 다양화 비평가 | A- |
| 21 | **CreativityPrism** | arXiv 2025 | 창의성 3차원(품질/참신성/다양성) | B+ |
| 22 | **EvolvR** | arXiv 2025 | 자기진화 쌍별 비교 — HANNA SOTA | B+ |
| 23 | **Story Theory Bench** | GitHub 2024 | 5대 이론 × 34태스크 × 25모델 | B+ |
| 24 | **Narrative Planning** | Autodesk+Midjourney | ASP 기반 인과 건전성 자동 검증 | B+ |
| 25 | **RLMR** | arXiv 2025 | 주관적 보상 + 객관적 제약 혼합 RL | B+ |
| 26 | **Finding Flawed Fictions** | arXiv 2025 | 플롯홀 5유형 + CEEval-Full | B+ |
| 27 | **"The Reader is the Metric"** | ACL Findings 2025 | 17텍스트 특징 × 101평가자 → 2독자 프로필 | A- |
| 28 | **ACL Findings 2025 Literary** | ACL 2025 | Deduction/Bonus 평가 프로토콜 | A- |

### NLG 메트릭 (12종)

| # | 이름 | 무엇을 측정 | LLM | 신뢰도 |
|---|------|-----------|-----|--------|
| 1 | gzip 압축률 | 구조적 반복성 | 0 | B+ |
| 2 | Burstiness | 문장 길이 변동성 | 0 | B |
| 3 | POS 템플릿 비율 | 구문 구조 반복 (EMNLP 2024) | 0 | A- |
| 4 | Sui Generis Score | 다중 생성물 간 에코 (PNAS 2025) | 0 | A |
| 5 | EASM | 감정 아크 정합성 | 0~1 | B+ |
| 6 | CEEval-Full | 플롯홀 5유형 탐지+위치 | 1 | B+ |
| 7 | 감정 궤적 VAD | Valence-Arousal-Dominance 3D | 0 | B+ |
| 8 | Tension Vector | 장면별 긴장도 수치화 | 0 | B |
| 9 | Narrative Reversal Count | 감정 반전 빈도+진폭 (Science Advances) | 0 | **A** |
| 10 | Dialogue Percentage | 대화:서술 비율 (인기작 25-35%) | 0 | B |
| 11 | Complexity Score | 문장 길이 분포 | 0 | B |
| 12 | Slop Score | AI 상투어 빈도 | 0 | B |

### 독자 참여/시장 연구 (6종)

| # | 연구 | 핵심 발견 | 신뢰도 |
|---|------|----------|--------|
| 1 | Knight 2024 | 반전 多+大 = 다운로드 2배+ (30,000작품) | **A** |
| 2 | Jing 2025 | 장르 관습→유입, 참신성→만족 (단조 감소) | A- |
| 3 | 문피아 흥행작 | 일일 연재 기본, 회귀/상태창/헌터 | B |
| 4 | Reagan 2016 | 6대 감정 아크 — Icarus/Oedipus 최인기 | **A** |
| 5 | EMNLP 2024 심리적 깊이 | 진정성/복잡성/공감/몰입/감정유발 | A |
| 6 | CONCOCT 페이싱 | 구체성 균일 57%+ 선호 | A- |

### 상용 도구 (8종)

| # | 도구 | 추출 가능 아이디어 |
|---|------|-----------------|
| 1 | AutoCrit | 대화 비율 25-35%, 복잡도 2.0-3.0 |
| 2 | Marlowe | 캐릭터 성격 프로파일링, 베스트셀러 대비 |
| 3 | Trilogy AI | 장르 적합성 구조 검증 |
| 4 | Novelcrafter | Progressions(시간축 상태 덮어쓰기) |
| 5 | Sudowrite | 단계별 창의성 온도 조절 |
| 6 | AI Dungeon/SCORE | NCI-2.0 + EASM 공표 벤치마크 |
| 7 | Inkitt | 플롯 A/B 테스트 |
| 8 | EQ-Bench v3 | Slop Score + 열화 패널티 |

---

## §1. 글도비가 이미 앞서는 영역

벤치마크들이 "평가"만 하는 것을 글도비는 "생성 + 평가 + 수정" 루프로 운영 중.

| 벤치마크 차원 | 글도비 대응 시스템 | 상태 |
|-------------|-----------------|------|
| 캐릭터 일관성 | TruthGate 7검사 + NpcDriftAdvisor + NC-1 + consistency_checklist 17항목 | ✅ |
| 타임라인 모순 | NC-2 timeline + NS-4 Arc 시간 연속성 + cumulative_elapsed | ✅ |
| 수치 불일치 | NC-1 9개 검사 (FactLedger 교차/산술/레버리지 등) | ✅ |
| 세계관 규칙 위반 | TruthGate _check_world_law_violation + GenreGuard 10종 | ✅ |
| 시점 혼선 | pre_llm_validator V70 + InfoParadoxChecker 1인칭 | ✅ |
| 이름 혼동 | NC-2 NPC 동명이인 + M-4 괄호 정규화 | ✅ |
| 멀티 채점자 앙상블 | Director SC 투표 + Ensemble 3후보 + 재심사 루프 | ✅ |
| 요소 제약 준수 | Treatment 블록 목표 + NS-3-B 교차검증 + TF-B 블록 경계 규칙 | ✅ |
| 장르별 평가 분화 | GenreGuard 10종 + WorkGuard + StyleGuard | ✅ |

---

## §2. 아키텍처 정합성 필터

글도비의 아키텍처 특성상 모든 벤치마크 아이디어가 적용 가능하지는 않음. 아래 기준으로 전수 필터링:

### 필터 기준

| # | 기준 | 설명 |
|---|------|------|
| F1 | **탑다운 구조** | Treatment→Arc→Blueprint→원고. 전개는 확정 후 캐릭터를 올림. 캐릭터가 전개를 만드는 바텀업/롤링스토리 방식 아이디어는 부적합 |
| F2 | **대원칙 1** | Python은 수집·포맷·전달만. "이게 오류인가?" 판단은 LLM(Director)이 함 |
| F3 | **대원칙 3** | Director가 최종 품질 결정권. Director를 우회하거나 다른 채점 주체를 세우면 안 됨 |
| F4 | **SC 자기일관성** | SC 투표는 "동일 평가자가 같은 판정을 내리는가" 테스트. 다른 역할의 다른 평가자를 세우는 것과는 목적이 다름 |
| F5 | **앙상블 = 같은 설계도의 다른 실행** | 3후보는 같은 Blueprint를 실행. 플롯 다양성이 아닌 실행 품질 경쟁. 플롯 키워드 겹침은 높아야 정상 |

### 필터 결과 — 제외/부록 이동 항목

| 원본 ID | 아이디어 | 제외 사유 | 이동 |
|---------|---------|----------|------|
| EXT-09 | 앙상블 후보 키워드 다양성 측정 | **F5 위반**: 3후보는 같은 Blueprint 실행이므로 플롯 키워드 겹침이 높아야 정상. "같은 이야기 3편"이 맞는 것. 다양성은 문체/표현에서 나와야 하며, 이는 Director가 quality로 선택하는 과정에서 자연 처리됨 | 부록 |
| EXT-12 | Director SC 투표 역할 다양화 | **F4 위반**: SC는 자기일관성 테스트(같은 기준으로 같은 결론을 내는가). 역할을 다양화하면 다른 관점에서 다른 결론을 내는 게 당연해져 SC 목적 자체가 무력화됨. **F3 위반**: 복수의 전문가 위원회는 Director 주권주의와 충돌 | 부록 |
| EXT-17 | 공유 스크래치패드 통합 | 현 DI Context + mc_parts가 이미 역할. 아키텍처 리팩터링 ROI 부족 | 부록 |
| EXT-20 | 동적 아웃라인 (Arc re-plan) | **F1 위반**: 탑다운 확정 구조에서 Arc 실행 중 Arc 자체를 변경하면 Treatment→Arc 계약 파괴. PASS_WITH_FIX는 원고 수준 국소 수정이지 Arc re-plan이 아님 | 부록 |
| EXT-23 | 비선형 서사 생성 | 웹소설 주류가 선형 서사. 생성 복잡도 대비 ROI 낮음 | 부록 |
| EXT-24 | 이중 시간축 지식그래프 | npc_history + FactLedger가 이미 이력 추적. 과잉설계 | 부록 |
| EXT-25 | 6대 감정 아크 형태 | Treatment는 인간 작가가 설계. 시스템이 감정 아크 형태를 강제하면 Treatment 주권 침해. Treatment 작성 가이드라인으로는 유효하나 코드 기능은 아님 | 부록(가이드) |
| EXT-16 | 유사성-참신성 균형 모니터링 | GenreGuard가 이미 장르 이탈을 잡고, PatternTracker가 반복을 잡음. 별도 "혁신 지수"는 측정 기준 모호 | 부록 |
| EXT-18 | SCORE EASM 벤치마킹 | 벤치마킹용이지 기능 개선이 아님 | 부록 |
| EXT-26 | 문피아 위험 신호 | 외부 플랫폼 데이터 없이 구현 불가 | 부록 |
| IDEA-07 | 토큰 엔트로피 조기 경보 | Gemini API logprobs 미지원. 구현 불가 | 부록(API대기) |
| IDEA-08 | Power Mean 채점 집계 | NC-3B 합산 교정과 효과 중복 | 부록 |
| IDEA-11 | 대사 전용 체크 | QM-1 체크13 + QM-2 dialogue_naturalness와 대부분 중복 | 부록 |
| IDEA-12 | 제약 밀도 vs 창의성 분석 | 인사이트 수준, 코드 기능 아님 | 부록(분석) |
| IDEA-17 | 인간 선호 보상모델 | 독자 데이터 축적 필요. 현재 불가 | 부록(장기) |

---

## §3. 최종 아이디어 목록 — 3차 전수조사 완료

### P0: 즉시 구현 (Python-only, LLM 0회, 극저비용)

| # | ID | 아이디어 | 출처 | 구현 | 효과 |
|---|-----|---------|------|------|------|
| 1 | **IDEA-01** | **CED (Consistency Error Density) 메트릭** | ConStory-Bench | `FailureAnalyzer.compute_ced()` + `episode_quality_labels.ced_score` | 작품 간 일관성 품질 단일 숫자 비교 |
| 2 | **IDEA-06** | **AI Slop 탐지 (한국어 AI 상투어 필터)** | EQ-Bench v3 | `chief_writer_quality._check_ai_slop()` + `ai_slop_kr.yaml` | "AI 냄새" 제거 — 독자 이탈 1순위 원인 |
| 3 | **EXT-01** | **gzip 압축률 반복성 탐지** | Standardized Diversity 2024 | `chief_writer_quality._check_compression_ratio()` — 2줄 | n-gram으로 못 잡는 구조적 반복 캐치 |
| 4 | **EXT-STRUCT** | **Burstiness + Complexity 이중 메트릭** | AI 탐지 연구 + AutoCrit | `pattern_tracker._compute_burstiness()` + `_compute_complexity()` — 10줄 | 문장 길이 단조로움 + 문장 복잡도 동시 측정 |
| 5 | **EXT-04** | **대화 비율 참고 범위 체크** | AutoCrit, Marlowe (인기 소설 수백 편) | `chief_writer_quality._check_dialogue_ratio()` — regex 15줄. 25-35%는 **참고 범위**(영어권 인기 소설 기준)이며 절대 임계값이 아님. 장르·작풍에 따라 유동적 | 서술/대화 밸런스 정량 모니터링 (advisory, 자동감점 아님) |

> **P0 소계**: 5건. 전부 Python-only, LLM 0회, 합계 ~50줄 코드 + 1 YAML

### P1: 다음 배치 (프롬프트 변경 또는 중간 구현)

| # | ID | 아이디어 | 출처 | 구현 | 효과 |
|---|-----|---------|------|------|------|
| 6 | **IDEA-02** | **Middle Slump 검증 강화** | ConStory-Bench (모순 40-60% 집중) | `arc_pos` 40-60% 구간 advisory + 검사 임계값 하향 | 서사 중반 모순 사전 포착 |
| 7 | **IDEA-03** | **동적 에피소드별 평가 기준** | WritingBench (동적 87% vs 정적 65%) | Director AUDIT에 Blueprint 기반 5개 맞춤 기준 생성 지시 | +22%p 인간 정합 (WritingBench 수치) |
| 8 | **IDEA-04** | **서사 품질 4차원 갭 해소** | WebNovelBench 8차원 중 미커버 | D1 수사법 빈도 + D2 감각묘사 + D3 캐릭터 대사비율 + D6 분위기 교차검증 | 품질 다차원 측정 |
| 9 | **IDEA-09** | **실패 근본 원인 클러스터링** | Mazur V4 실패 패턴 분류 | `FailureAnalyzer.cluster_failure_mechanisms()` LLM 1회 | Arc 생성 시 반복 실패 메커니즘 주입 |
| 10 | **IDEA-15** | **원인 없는 결과 감지 (능력/자원 추적)** | ConStory Cat1-Causeless Effects | 원고 내 **능력(스킬)/자원** 사용 vs WorldState/FactLedger 교차검증. NC-1은 수치 정합성(금액·레버리지), TruthGate는 아이템/장소/NPC 사망을 검사 — **능력 레벨·기술 습득 여부·자원 보유 여부**는 미커버 | 데우스 엑스 마키나 방지 (미습득 기술 사용, 미보유 자원 투입) |
| 11 | **EXT-05** | **CheckEval 이진 분해 (NC-3 핵심 5개)** | CheckEval EMNLP 2025 (IAA +0.45) | `director.yaml` NC-3 핵심 5개 항목을 3-5개 이진 하위질문으로 분해 | Director 채점 신뢰도 대폭 향상 |
| 12 | **EXT-06** | **Deduction/Bonus 피드백 구조화** | ACL Findings 2025 Literary Eval | Director `rejection_reason` → 구체적 감점/가점 분류 | CW retry "무엇을 고치고 보존할지" 명시 |
| 13 | **EXT-21** | **Suspense = 탈출 경로 축소 프롬프트** | Xie & Riedl EACL 2024 | Blueprint 생성 프롬프트에 "위기 심화 시 선택지 축소" 지시 | Arc 중반 긴장감 구축 가이드 |

> **P1 소계**: 8건. 프롬프트 변경 5건 + 코드 변경 3건

### P2: 후순위 (외부 의존성 또는 큰 변경)

| # | ID | 아이디어 | 비고 |
|---|-----|---------|-----|
| 14 | **IDEA-05** | 챕터별 열화 추적 시각화 | FL-5 인프라 존재, 시각화만 추가 |
| 15 | **IDEA-10** | Craft/Constraint 분리 채점 | Director 스키마 확장 필요 |
| 16 | **IDEA-13** | 외관 불일치 감지 (appearance) | NpcDriftAdvisor 필드 추가 |
| 17 | **IDEA-14** | 망각된 능력 감지 | LLM 필요, 높은 구현 비용 |
| 18 | **IDEA-16** | 방치 플롯 강화 | DB-4 임계값/심각도 조정 수준 |
| 19 | **EXT-07** | TIMECHARA 3인칭 캐릭터 지식 | DB 확장, LM-F 1인칭 이미 커버 |
| 20 | **EXT-08** | POS 템플릿 반복률 | KoNLPy 의존성 필요 |
| 21 | **EXT-15** | Blueprint 블록 구체성 균일화 | CONCOCT 방식, Stage 3 프롬프트 |
| 22 | **EXT-19** | 심리적 깊이 self-critique (16번째) | 프롬프트 1줄 추가 |
| 23 | **EXT-22** | 장르 적합성 구조 검증 | 장르별 규칙 정의 필요 |
| 24 | **EXT-28** | NarraBench Discourse 차원 | 서스펜스/놀라움 명시 평가 |
| 25 | **EXT-EMOTION** | 한국어 감정 분석 패키지 | NRC-VAD 한국어 확보 시 반전+VAD+긴장도 3메트릭 동시 활성화. 어휘 품질이 관건 |

> **P2 소계**: 12건

---

## §4. ConStory 19-type 커버리지 매트릭스 (최종)

```
[✅ 완전 커버] 6/19
 1. Absolute Time        → NC-2 timeline + NS-4
 5. Causal Logic          → TruthGate + Director AUDIT
11. Core Rules            → TruthGate _check_world_law_violation
15. Nomenclature          → NC-2 NPC 동명이인 + M-4
16. Quantitative          → NC-1 9개 검사
17. Perspective           → pre_llm_validator V70 + InfoParadoxChecker

[⚠️ 부분 커버] 10/19
 2. Duration              → cumulative_elapsed (지속시간 교차검증 미약)
 3. Simultaneity          → 동시 위치 모순 전용 검사 없음
 6. Abandoned Plot        → B-4 + DB-4 (임계값 약함) → IDEA-16으로 강화 가능
 7. Memory                → NpcDriftAdvisor (LLM advisory)
 8. Knowledge             → InfoParadoxChecker (1인칭 전용) → EXT-07(P2)로 3인칭 확장 가능
12. Social Norms          → GenreGuard (장르 규칙은 잡으나 사회 규범 전용 아님)
13. Geographical          → NC-2 공간연속성 (프롬프트 수준)
14. Appearance            → NpcDriftAdvisor 4필드 (appearance 미포함) → IDEA-13(P2)
18. Tone Inconsistencies  → QM-1 체크14 (부분)
19. Style Shifts          → StyleGuard (에피소드 내 변동 미탐지)

[❌ 미커버] 3/19
 4. Causeless Effects     → IDEA-15(P1)로 해소 예정 — NC-1(수치)/TruthGate(아이템·NPC)와 비중복: 능력/자원 출현 추적 특화
 9. Skill/Power Fluct.    → 능력 수준 추적 없음
10. Forgotten Abilities   → IDEA-14(P2)로 해소 가능
```

**P1 완료 시**: ❌ 3→2개 (Causeless Effects 해소)
**P2 완료 시**: ❌ 2→0개, ⚠️ 10→7개

---

## §5. 글도비 신규 품질 차원 커버리지 (확장 벤치마크 기준)

| 차원 | 현재 커버리지 | 해소 아이디어 | 우선순위 |
|------|-------------|-------------|---------|
| 구조적 반복성 | 🟡 50% (PatternTracker 2-gram) | **EXT-01** gzip 압축률 | P0 |
| 문장 구조 다양성 | 🟡 40% (_check_paragraph_structure) | **EXT-STRUCT** Burstiness+Complexity | P0 |
| AI 상투어/클리셰 | 🔴 0% | **IDEA-06** Slop 탐지 | P0 |
| 대화 비율 밸런스 | 🟡 50% (규칙13 일부) | **EXT-04** 25-35% 정량 체크 | P0 |
| 일관성 밀도 정규화 | 🔴 0% | **IDEA-01** CED 메트릭 | P0 |
| Director 채점 신뢰도 | 🟢 70% (SC + NC-3B) | **EXT-05** CheckEval 이진 분해 | P1 |
| CW retry 피드백 품질 | 🟢 60% (rejection_reason) | **EXT-06** Deduction/Bonus | P1 |
| 서사 중반 집중 검증 | 🔴 0% | **IDEA-02** Middle Slump | P1 |
| 긴장감/서스펜스 구축 | 🔴 0% | **EXT-21** 탈출 경로 축소 | P1 |
| 능력/자원 출현 교차검증 | 🔴 0% | **IDEA-15** Causeless Effects | P1 |
| 감정 아크 정합성 | 🟡 40% (Blueprint 계획만) | **EXT-EMOTION** VAD 패키지 | P2 |
| 캐릭터 지식 범위(3인칭) | 🟡 50% (1인칭만) | **EXT-07** TIMECHARA | P2 |
| Blueprint 상세도 균일성 | 🔴 0% | **EXT-15** CONCOCT | P2 |

---

## §6. 핵심 수치 레퍼런스

### ConStory-Bench
- **Factual & Detail Consistency가 지배적 실패 모드** (전 모델 CED 최고)
- 팩트 설정 20-24%, 모순 발생 34-49% (중앙값 40-60%)
- ConStory-Checker F1=0.678 (인간 F1=0.229의 3배)

### Mazur V4
- 18문항 (Craft 60% + Element 40%), Power mean p=0.5
- Craft↔Element 상관 0.836
- 실패 패턴: Under-pressurized narrative, Hyper-competent protagonist, Reflection overwhelming momentum

### WritingBench
- 동적 기준 87% 인간 정합 (정적 65%)

### CheckEval
- 이진 분해 시 IAA +0.45, 점수 분산 감소

### Knight 2024 (서사 반전)
- 반전 多+大 = 다운로드 2배+ (30,000작품, 영화/TV/소설/크라우드펀딩 교차 검증)

### AutoCrit/Marlowe (인기 소설)
- 대화 비율 25-35%, 복잡도 점수 2.0-3.0

---

## §7. 구현 로드맵

```
Phase A (P0, 1-2일): CED + AI Slop + gzip + Burstiness/Complexity + 대화 비율
  → chief_writer_quality.py 3체크 추가
  → pattern_tracker.py 2메트릭 추가
  → failure_analyzer.py 1메서드 추가
  → episode_quality_labels 1컬럼 추가
  → ai_slop_kr.yaml 신규

Phase B (P1, 1주): Middle Slump + 동적 기준 + 4차원 갭 + 실패 클러스터 + Causeless Effects + CheckEval 이진 분해 + Deduction/Bonus + Suspense 프롬프트
  → director.yaml 프롬프트 수정 3곳
  → director_ensemble.py 스키마/파싱 변경
  → stage4_interview_round.py advisory 2곳
  → FailureAnalyzer 1메서드
  → chief_writer_quality 2체크 추가
  → NC-1 또는 신규 모듈에 능력/자원 교차검증
  → blueprint_generator.yaml 프롬프트 1곳

Phase C (P2, 후순위):
  → 12건, 외부 의존성(NRC-VAD, KoNLPy) 또는 스키마 확장 필요
```

---

## 부록 A: 아키텍처 부적합으로 제외된 아이디어

### A-1. EXT-09: 앙상블 후보 키워드 다양성 측정
- **출처**: PNAS 2025 Sui Generis Score
- **제외 사유**: 글도비의 3후보는 같은 Blueprint를 실행하는 "같은 이야기의 다른 실행". 플롯 키워드 겹침이 높아야 정상. 다양성은 문체/표현에서 나오며, Director가 quality 기준으로 선택하는 과정에서 자연 처리됨. 플롯 키워드 다양성을 강제하면 Blueprint 이탈을 조장하는 롤링스토리 방향이 됨.
- **Sui Generis 본래 용도**: "다른 프롬프트에서 같은 플롯이 나오는가"를 측정하는 것이지, "같은 프롬프트에서 다른 플롯이 나오는가"를 요구하는 것이 아님.

### A-2. EXT-12: Director SC 투표 역할 다양화
- **출처**: CritiCS (EMNLP 2024)
- **제외 사유**: (1) SC 투표는 **자기일관성** 테스트 — "같은 기준으로 같은 결론을 내는가"를 검증. 역할을 다양화하면 다른 관점에서 다른 결론이 나오는 게 당연해져 SC 목적이 무력화됨. (2) 복수 전문가 위원회는 **Director 주권주의**(대원칙 3)와 충돌 — Director는 단일 주권자로서 최종 판정. 여러 전문가 합의로 결정하는 건 다른 아키텍처.
- **CritiCS의 본래 맥락**: CritiCS는 생성 품질 향상을 위한 멀티 비평가 + 리더 구조. 글도비의 Director는 이미 리더 역할이며, 비평가들(Analyst, Advisory Chain, NC-1 등)이 이미 다양한 관점을 공급. 즉 CritiCS 패턴은 글도비에 **이미 구현되어 있음** — Director가 다양한 소스의 피드백을 종합하여 단독 판정.

### A-3. EXT-17: 공유 스크래치패드 통합
- **출처**: Agents' Room (ICLR 2025, DeepMind)
- **제외 사유**: DI Context(Stage2Context/3/4) + `_director_mc_parts` + `_reference_only_parts`가 이미 동일 역할. 단일 JSON으로 통합하는 리팩터링의 ROI가 기능 개선 대비 낮음.

### A-4. EXT-20: 동적 아웃라인 (Arc 실행 중 re-plan)
- **출처**: DOME (NAACL 2025)
- **제외 사유**: Treatment→Arc→Blueprint는 **확정된 계약**. 에피소드 생성 중 Arc 자체를 변경하면 Treatment 설계 의도가 파괴됨. PASS_WITH_FIX는 원고 수준 국소 수정이며 Arc re-plan이 아님. TF-48(실행 상태 연속성)은 Arc N+1이 Arc N의 실제 결과를 반영하는 것이지 Arc N 자체를 변경하는 것이 아님.

### A-5. EXT-23: 비선형 서사 생성
- **출처**: StoryWriter (CIKM 2025) NLN
- **제외 사유**: 한국 웹소설 주류가 선형 서사. 비선형 구조(회상/시간 도약 등)의 의도적 생성은 Treatment 설계 영역이며, 파이프라인이 자동으로 결정할 영역이 아님. FlashbackVerifier(LM-E)가 비의도적 회상 오염은 이미 감지.

### A-6. EXT-25: 6대 감정 아크 형태 Treatment 활용
- **출처**: Reagan 2016 (2,000+ 인용)
- **제외 사유**: Treatment는 인간 작가가 설계. 시스템이 감정 아크 형태를 강제하면 Treatment 주권 침해. **Treatment 작성 가이드라인**으로는 유효하나 코드 기능으로 구현할 대상은 아님.
- **활용 방안**: `docs/` 또는 Treatment 템플릿에 "6대 아크 형태 참고 자료"로 문서화하여 작가 참조용 제공.

### A-7. EXT-24: 이중 시간축 지식그래프
- **출처**: Zep/Graphiti (arXiv 2025)
- **제외 사유**: `npc_history`(append-only + reason) + `FactLedger`(이력 추적) + `cumulative_elapsed`(스토리 시간)가 이미 필요한 시간축 추적을 수행. 별도 그래프 DB는 과잉설계.

### A-8. 기타 제외

| ID | 이름 | 사유 |
|----|------|------|
| EXT-16 | 유사성-참신성 균형 | GenreGuard + PatternTracker가 이미 커버. "혁신 지수" 측정 기준 모호 |
| EXT-18 | SCORE EASM 벤치마킹 | 벤치마킹용, 기능 개선 아님 |
| EXT-26 | 문피아 위험 신호 | 외부 데이터 없이 구현 불가 |
| IDEA-07 | 토큰 엔트로피 조기 경보 | Gemini API logprobs 미지원 |
| IDEA-08 | Power Mean 채점 | NC-3B 합산 교정과 중복 |
| IDEA-11 | 대사 전용 체크 | QM-1/QM-2와 대부분 중복 |
| IDEA-12 | 제약 밀도 분석 | 인사이트 수준, 코드 기능 아님 |
| IDEA-17 | 인간 선호 보상모델 | 독자 데이터 축적 필요 |

---

## 부록 B: 신뢰도 평가

### Tier 1: 최고 신뢰 (피어리뷰 최상위 학회 + 대규모 검증)
LongStoryEval(ACL), ASE/HANNA(TACL), CheckEval(EMNLP), CHARACTERBENCH(AAAI), TIMECHARA(ACL), Knight 2024(Science Advances), Reagan 2016(2000+ 인용)

### Tier 2: 높은 신뢰 (피어리뷰 + 중규모 검증)
NarraBench, CollabStory(NAACL), CritiCS(EMNLP), DOC(ACL), DOME(NAACL), Agents' Room(ICLR), CONCOCT(EMNLP), Jing 2025(Nature HSS), SCORE, Sui Generis(PNAS), POS Templates(EMNLP)

### Tier 3: 보통 (arXiv 프리프린트 또는 상용 도구)
Story Theory Bench, GrAImes, AI Creativity Framework, Fong & Gui, AutoCrit/Marlowe, 문피아 연구

### Tier 4: 참고용
StoryBench Memory, RecurrentGPT, LTSG

---

## 부록 C: 참고 문헌 (전량)

### 벤치마크
- ConStory-Bench: arXiv 2603.05890
- WebNovelBench: arXiv 2505.14818
- Mazur Writing V4: github.com/lechmazur/writing
- WritingBench: arXiv 2503.05244
- EQ-Bench Longform: eqbench.com/creative_writing_longform.html
- LitBench: arXiv 2507.00769
- DramaBench: arXiv 2512.19012
- CS4: arXiv 2410.04197
- Coherence Framework: arXiv 2310.00598
- LongStoryEval: arXiv 2512.12839
- NarraBench: arXiv 2510.09869
- SCORE: arXiv 2503.23512
- "Novel" Benchmark: aclanthology.org/2025.findings-acl.1114
- ASE/HANNA: TACL 2024
- CheckEval: EMNLP 2025
- CHARACTERBENCH: AAAI 2025
- TIMECHARA: ACL 2024
- CollabStory: NAACL 2025
- CritiCS: EMNLP 2024
- CreativityPrism: arXiv 2510.20091
- EvolvR: arXiv 2508.06046
- Story Theory Bench: github.com/clchinkc/story-bench
- Narrative Planning: arXiv 2506.10161
- RLMR: arXiv 2508.18642
- Finding Flawed Fictions: arXiv 2504.11900
- "The Reader is the Metric": arXiv 2506.03310
- ACL Findings 2025 Literary: aclanthology.org/2025.findings-acl.1114

### 메트릭/방법론
- Standardized Text Diversity: arXiv 2403.00553
- POS Templates: EMNLP 2024 (arXiv 2407.00211)
- Sui Generis: PNAS 122(35) 2025
- G-Eval: EMNLP 2023
- X-Eval: NAACL 2024
- Themis: EMNLP 2024

### 아키텍처
- DOC: ACL 2023
- DOME: NAACL 2025 (arXiv 2412.13575)
- Agents' Room: ICLR 2025 (arXiv 2410.02603)
- StoryBox: arXiv 2510.11618
- StoryWriter: CIKM 2025 (arXiv 2506.16445)
- RecurrentGPT: arXiv 2305.13304
- Zep/Graphiti: arXiv 2501.13956
- NCP: COLM 2025 (arXiv 2503.22828)
- CONCOCT: EMNLP 2023 (arXiv 2311.04459)

### 독자 참여
- Knight 2024: Science Advances 10.1126/sciadv.adl2013
- Jing 2025: Nature HSS 10.1038/s41599-025-05166-3
- Reagan 2016: arXiv 1606.07772
- Fong & Gui: arXiv 2412.15239
- 문피아 흥행작: KCI ART002726821
- EMNLP 2024 심리적 깊이: aclanthology.org/2024.emnlp-main.953
- Xie & Riedl 서스펜스: EACL 2024

### 상용 도구
- AutoCrit: autocrit.com
- Marlowe: authors.ai/marlowe
- Trilogy: publishersweekly.com
- EQ-Bench v3: eqbench.com
- AI Dungeon SCORE: arXiv 2503.23512
