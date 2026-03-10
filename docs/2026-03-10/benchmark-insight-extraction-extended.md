# 벤치마크 인사이트 추출 (확장판) — 추가 전수조사

> 작성일: 2026-03-10
> 1차 문서: `benchmark-insight-extraction.md` (10종 벤치마크 → 17개 아이디어)
> 본 문서: 5개 병렬 조사 에이전트 결과 종합 — **신규 40+ 소스** 추가 분석
> 목적: 1차 문서에서 누락된 벤치마크·메트릭·상용 도구·학술 연구 전수 발굴

---

## 신규 발굴 소스 총괄

### A. 신규 벤치마크/프레임워크 (18종)

| # | 이름 | 기관/저자 | 발표 | 핵심 기여 | 신뢰도 |
|---|------|----------|------|----------|--------|
| 1 | **LongStoryEval + NovelCritique** | Dingyi Yang (ACL 2025) | 2025-12 | 100K+ 토큰 서적 평가, 8차원 20하위 — 340K 리뷰 기반 8B 평가 모델 | **A** (ACL main) |
| 2 | **NarraBench** | Cornell+McGill | 2025-10 | 서사학 기반 50개 태스크 — Big-4(Story/Narration/Discourse/Situatedness), 78벤치 메타분석 | **A-** |
| 3 | **Story Theory Benchmark** | clchinkc/GitHub | 2024-25 | Hero's Journey 등 5대 이론 × 34태스크 × 25모델 — $42 재현 비용 | **B+** |
| 4 | **SCORE** | Qiang Yi et al. | 2025-03 | 에피소드 서사 일관성 — Dynamic State Tracking + Hybrid Retrieval + EASM 89.7% | **B+** |
| 5 | **"Novel" Benchmark** | ACL Findings 2025 | 2025 | Macro/Meso/Micro 3단계 10메트릭, EN+CN 이중언어 | **A-** (ACL Findings) |
| 6 | **GrAImes** | Applied Sciences | 2025-06 | 스페인어 마이크로픽션, 편집자 수락/거절 프로토콜 | **B** |
| 7 | **ASE (HANNA)** | TACL 2024 | 2024-05 | 6차원(Relevance/Coherence/Empathy/Surprise/Engagement/Complexity) × 1,056편 × 19,008 주석 | **A** (TACL) |
| 8 | **EvolvR** | arXiv | 2025-08 | 자기진화 쌍별 비교 CoT — StoryER/HANNA/OpenMEVA SOTA | **B+** |
| 9 | **CreativityPrism** | arXiv | 2025-10 | 창의성 3차원(품질/참신성/다양성) × 17모델 — 참신성↔품질 약/음 상관 확인 | **B+** |
| 10 | **"The Reader is the Metric"** | ACL Findings 2025 | 2025-06 | 17 텍스트 특징 × 101 평가자 → 2개 독자 프로필(표면/총체) 발견 | **A-** (ACL Findings) |
| 11 | **CollabStory** | NAACL Findings 2025 | 2025 | 32,000+ 멀티LLM 협작 스토리 — 연속성 테스트 | **A-** (NAACL) |
| 12 | **Narrative Planning Bench** | Autodesk+Midjourney | 2025-06 | ASP 기반 인과 건전성/캐릭터 의도/극적 갈등 3차원 자동 검증 | **B+** |
| 13 | **StoryBench (Memory)** | arXiv | 2025-06 | 인터랙티브 픽션 기반 장기 기억 + 분기 의사결정 테스트 | **B** |
| 14 | **AI Creativity Framework** | arXiv | 2026-01 | 4차원 11하위(Adherence/Novelty/Technical/Resonance), Spike Prompting + 115명 크라우드 | **B** |
| 15 | **CHARACTERBENCH** | AAAI 2025 | 2025 | 22,859 주석 — 캐릭터 커스터마이징 EN+CN | **A** (AAAI) |
| 16 | **TIMECHARA** | ACL 2024 | 2024 | 시점별 캐릭터 할루시네이션 — "ep5 캐릭터가 ep10 정보를 아는가?" | **A** (ACL) |
| 17 | **CheckEval** | EMNLP 2025 | 2025 | 이진 체크리스트 분해 — IAA +0.45, 분산 감소 | **A** (EMNLP) |
| 18 | **RLMR** | arXiv | 2025-08 | 주관적 보상 + 객관적 제약 혼합 강화학습, WritingBench 72.75% 승률 | **B+** |

### B. 신규 NLG 메트릭/방법론 (12종)

| # | 이름 | 출처 | 무엇을 측정 | LLM 호출 |
|---|------|------|-----------|---------|
| 1 | **gzip 압축률** | Standardized Diversity 2024 | 구조적 반복성 (높은 압축 = 반복적) | 0 |
| 2 | **Burstiness** | AI 탐지 연구 다수 | 문장 길이 표준편차 (낮으면 단조로운 구조) | 0 |
| 3 | **POS 템플릿 비율** | EMNLP 2024 Shaib | 구문 구조 반복 (76% LLM 템플릿 = 사전훈련 데이터 유래) | 0 |
| 4 | **Sui Generis Score** | PNAS 2025 MS Research | 플롯 요소 고유성 (동일 프롬프트 다중 생성 간 에코 비율) | 0 |
| 5 | **EASM** | SCORE 2025 | 감정 아크 정합성 (계획 vs 실제 감정 궤적) | 0~1 |
| 6 | **CEEval-Full** | Finding Flawed Fictions 2025 | 플롯홀 5유형 탐지+위치 확인 2단계 | 1 |
| 7 | **감정 궤적 VAD** | NRC-VAD 다수 | Valence-Arousal-Dominance 3차원 감정 추적 | 0 |
| 8 | **Tension Vector** | 서사 평가 서베이 2024 | 서사 긴장도 수치 벡터 (장면별 점수화) | 0 |
| 9 | **Narrative Reversal Count** | Knight, Science Advances 2024 | 감정 반전 빈도+진폭 (많을수록 성공) | 0 |
| 10 | **Dialogue Percentage** | AutoCrit/Marlowe | 대화:서술 비율 (인기작 25-35%) | 0 |
| 11 | **Complexity Score** | AutoCrit | 문장 길이 분포 기반 (인기작 2.0-3.0) | 0 |
| 12 | **Slop Score** | EQ-Bench v3 | AI 상투어 빈도 ("a symphony of" 등) | 0 |

### C. 학술 연구 — 아키텍처/기법 (11종)

| # | 이름 | 발표처 | 핵심 기법 | 글도비 대응 |
|---|------|--------|----------|-----------|
| 1 | **DOC** | ACL 2023 | 계층적 아웃라인 + Controller 정합 검사 | Treatment→Arc→Blueprint 유사, Controller=Director |
| 2 | **DOME** | NAACL 2025 | 동적 아웃라인 + 시간 지식 그래프 + 시간 충돌 분석기 | PASS_WITH_FIX가 동적 아웃라인 역할 |
| 3 | **Agents' Room** | ICLR 2025 DeepMind | 멀티에이전트 + 공유 스크래치패드 | DI Context 유사, mc_parts = scratchpad |
| 4 | **StoryBox** | arXiv 2025 | 바텀업 캐릭터 에이전트 + 계층적 윈도우 요약 | episode_chain_links 유사 |
| 5 | **CritiCS** | EMNLP 2024 | 역할 다양화 비평가 (사회학자/미래학자 등) | Director Ensemble 유사, 역할 차별화 아이디어 |
| 6 | **StoryWriter** | CIKM 2025 | NLN(비선형 서사) + ReIO(동적 히스토리 압축) | FlashbackVerifier가 감지만, 생성은 미지원 |
| 7 | **RecurrentGPT** | arXiv 2023 | LSTM 모사 — 장/단기 기억 자연어 분리 | VecMemory + chain_links 유사 |
| 8 | **Zep/Graphiti** | arXiv 2025 | 이중 시간축 지식그래프 (스토리 시간 vs 처리 시간) | cumulative_elapsed(스토리 시간만) |
| 9 | **NCP** | COLM 2025 | 다음 장 예측 + 검증 보상(VR-CLI) | Stage4 구조와 유사 |
| 10 | **CONCOCT** | EMNLP 2023 | 페이싱 균일성 — 구체성 평가기 + 가장 모호한 것 먼저 확장 | Blueprint 블록 상세도 균일성 |
| 11 | **LTSG** | arXiv 2025 | 문학 이론 기반 테마-장애물 프레임워크 + 지식그래프 | core_tension 유사 |

### D. 상용 도구 인사이트 (8종)

| # | 도구 | 추출 가능 아이디어 |
|---|------|-----------------|
| 1 | **AutoCrit** | 대화 비율 25-35% 타겟, 복잡도 2.0-3.0, 장르별 비교 |
| 2 | **Marlowe (Authors.AI)** | 캐릭터 성격 프로파일링, 클리셰 탐지, 베스트셀러 대비 |
| 3 | **Trilogy Manuscript AI** | 100점 원고 점수 = 예측 평점 + 장르 적합성 + 스타일 적합성 |
| 4 | **Novelcrafter** | Progressions(시간축 상태 덮어쓰기), Codex(자동 인덱싱) |
| 5 | **Sudowrite** | 단계별 창의성 온도 조절, 음성 매칭(1000자+ 샘플) |
| 6 | **AI Dungeon/SCORE** | NCI-2.0 + EASM 공표 벤치마크, 아키텍처 글도비와 직접 비교 가능 |
| 7 | **Inkitt/Galatea** | 플롯 A/B 테스트 (독자 참여도 기반 승자 선택) |
| 8 | **EQ-Bench v3** | Slop Score + Repetition Score + 열화 패널티(단문 과용) |

### E. 독자 참여/한국 웹소설 연구 (6종)

| # | 연구 | 핵심 발견 | 신뢰도 |
|---|------|----------|--------|
| 1 | **Knight 2024 (서사 반전)** | 반전 多+大 = 2배+ 다운로드. 30,000작품 검증 | **A** (Science Advances) |
| 2 | **Jing 2025 (유사성 vs 참신성)** | 장르 관습 준수→유입, 전략적 참신성→만족 (U자 아님, 단조 감소) | **A-** (Nature HSS) |
| 3 | **문피아 흥행작 연구** | 일일 연재 기본, 댓글↑+추천↓=위험 신호, 회귀/상태창/헌터 태그 | **B** (KCI) |
| 4 | **Fong & Gui 2024 (기대 모델링)** | LLM 계속 생성으로 기대/불확실성/놀라움 추출 — 설명력 +31% | **B** |
| 5 | **Reagan 2016 (감정 아크 6형)** | Icarus(상승-하락), Oedipus(하락-상승-하락) 최인기 | **A** (2000+ 인용) |
| 6 | **EMNLP 2024 (심리적 깊이)** | 진정성/서사복잡성/공감/몰입/감정유발 5차원 | **A** (EMNLP) |

---

## §1. 1차 문서와 중복 제거

1차 문서에서 이미 다룬 소스/아이디어:
- ConStory-Bench CED → IDEA-01 (기존)
- EQ-Bench Slop → IDEA-02 (기존)
- WritingBench 동적 기준 → IDEA-04 (기존)
- ConStory 19-type 매핑 → §6 (기존)

**본 문서에서는 1차와 중복되지 않는 아이디어만 번호 부여.**

---

## §2. 신규 아이디어 — 1차 전수조사 (28개)

### EXT-01: gzip 압축률 기반 반복성 탐지
- **출처**: Standardized Text Diversity (arXiv 2403.00553), 2024
- **정의**: `compression_ratio = len(gzip.compress(text.encode())) / len(text.encode())`
- **글도비 적용**: 원고 생성 후 압축률 계산. 인간 웹소설 기준치 대비 낮은 압축률(=높은 반복성) → PatternTracker advisory로 Director에 전달
- **구현**: Python 2줄. LLM 0회. `chief_writer_quality`에 `_check_compression_ratio()` 추가
- **우선순위**: **P0** — 극저비용, 즉시 구현 가능

### EXT-02: Burstiness (문장 길이 변동성) 메트릭
- **출처**: AI 탐지 연구 다수, 2024-2025
- **정의**: `burstiness = std_dev(sentence_lengths)` — 인간은 자연스럽게 짧은 문장과 긴 문장을 섞어 씀. LLM은 균일한 문장 길이 경향
- **글도비 적용**: 원고의 문장 길이 표준편차 계산. 임계값 미달 시 "단조로운 문장 구조" advisory
- **구현**: Python 5줄. LLM 0회. `pattern_tracker`에 통합
- **우선순위**: **P0** — 극저비용

### EXT-03: 서사 반전 빈도 최적화
- **출처**: Knight et al., *Science Advances* 2024 — 30,000작품 N 검증
- **정의**: 감정 가의 급격한 방향 전환 횟수. 반전 多+大 = 다운로드 2배+
- **글도비 적용**: VADER/NRC-VAD 한국어 어휘 사전으로 에피소드별 감정 궤적 계산 → 반전 포인트 탐지 → 반전 0개 에피소드에 "감정 반전 부재" advisory
- **구현**: 중간 (한국어 감성 어휘 사전 필요). LLM 0회
- **우선순위**: **P1** — 한국어 어휘 사전 확보 필요

### EXT-04: 대화 비율 25-35% 타겟 체크
- **출처**: AutoCrit, Marlowe — 인기 소설 수백 편 분석
- **정의**: `dialogue_ratio = dialogue_chars / total_chars` — 인기작 기준 25-35%
- **글도비 적용**: 원고에서 대사 마커(따옴표/큰따옴표) 내 텍스트 비율 계산. 범위 이탈 시 advisory
- **구현**: Python. LLM 0회. `chief_writer_quality._check_dialogue_ratio()`
- **우선순위**: **P0** — 극저비용, 한국어 대사 마커 `"` `"` `「` `」` regex

### EXT-05: CheckEval 이진 분해 — NC-3 체크리스트 고도화
- **출처**: CheckEval (EMNLP 2025) — IAA +0.45, 분산 감소
- **정의**: 단일 차원을 5-7개 이진(Yes/No) 하위 질문으로 분해하면 평가 신뢰도 대폭 향상
- **글도비 적용**: NC-3 `consistency_checklist` 17개 항목 중 핵심 5개를 3-5개 하위 질문으로 분해. 예: `character_consistency` → "주인공 말투가 일관적인가?", "NPC 직함이 변경되지 않았는가?", "사망 캐릭터가 행동하지 않는가?" 등
- **구현**: 프롬프트 변경만. LLM 추가 호출 0회
- **우선순위**: **P1** — Director 프롬프트 변경만, 채점 신뢰도 직접 향상

### EXT-06: Deduction/Bonus 분류 체계 — Director 피드백 구조화
- **출처**: "Evaluating Literary Fiction with LLMs" (ACL Findings 2025)
- **정의**: 점수 대신 구체적 감점(deduction)과 가점(bonus) 식별. "3단락 캐릭터 음성 불일치" vs "은유 효과적 사용"
- **글도비 적용**: Director `rejection_reason`과 `action_items`를 deduction/bonus 분류로 구조화. CW retry 루프에서 "무엇을 고치고, 무엇을 보존할지" 명시적 전달
- **구현**: Director 프롬프트 + 스키마 변경. LLM 추가 0회
- **우선순위**: **P1** — Director 피드백 품질 직접 향상

### EXT-07: TIMECHARA 방식 시점별 캐릭터 지식 검증
- **출처**: TIMECHARA (ACL 2024) — 시점별 캐릭터 할루시네이션 탐지
- **정의**: "에피소드 5의 캐릭터가 에피소드 10에서 밝혀진 정보를 알고 있는가?"
- **글도비 적용**: InfoParadoxChecker(LM-F) 강화 — 현재는 1인칭 전용이나, TIMECHARA 방식으로 3인칭에서도 "캐릭터별 지식 범위" 추적 가능. `episode_bibles`에서 캐릭터별 지식 누적 테이블 구축
- **구현**: 높음. DB 스키마 확장 + LLM 1회
- **우선순위**: **P2** — InfoParadoxChecker가 1인칭은 이미 커버

### EXT-08: POS 템플릿 반복률 — 한국어 형태소 분석
- **출처**: EMNLP 2024 Shaib — LLM의 76% 구문 템플릿이 사전훈련 데이터 유래
- **정의**: 문장을 POS 태그 시퀀스로 변환 후, 동일 패턴 재사용 빈도 측정
- **글도비 적용**: KoNLPy/Mecab으로 원고 문장 POS 추출 → 템플릿 빈도 계산 → 상위 5개 패턴이 50%+ 차지하면 "구문 단조로움" advisory
- **구현**: 중간 (KoNLPy 의존성). LLM 0회
- **우선순위**: **P2** — 외부 의존성(형태소 분석기) 필요

### EXT-09: Sui Generis Score — 앙상블 후보 다양성 측정
- **출처**: PNAS 2025 Microsoft Research — GPT-4 스토리 50/100편에 동일 랜드마크 등장
- **정의**: 동일 프롬프트의 다중 생성물에서 플롯 요소 에코 비율 측정
- **글도비 적용**: Director Ensemble 3후보 간 주요 플롯 요소(이름/장소/이벤트) 겹침 비율 계산. 3후보가 "같은 이야기 3편"이면 경고 → 전략 다양화 강제
- **구현**: 중간. LLM 0회 (키워드 추출 기반)
- **우선순위**: **P1** — Ensemble 다양성 보장

### EXT-10: 감정 아크 VAD 정합성 — Blueprint vs 원고
- **출처**: NRC-VAD 어휘 사전 + SCORE EASM
- **정의**: Blueprint의 `emotional_arc` 계획과 실제 원고의 감정 궤적(VAD 3차원) 간 정합성 측정
- **글도비 적용**: NRC-VAD 한국어 어휘 사전으로 장면별 감정 벡터 계산 → Blueprint 감정 계획과 코사인 유사도 비교 → 괴리 시 advisory
- **구현**: 중간 (NRC-VAD 한국어 확보 필요). LLM 0회
- **우선순위**: **P2** — 한국어 감정 어휘 사전 품질이 관건

### EXT-11: Tension Vector — 장면별 긴장도 수치화
- **출처**: 서사 평가 서베이 2024 다수
- **정의**: 장면 단위 긴장도를 수치 벡터로 표현. 변동 없음=페이싱 불량, 과다 변동=비일관
- **글도비 적용**: 감성 어휘 기반 장면별 긴장도 계산 → DB-1 pacing advisory와 결합
- **구현**: 중간. LLM 0회
- **우선순위**: **P2** — EXT-03/EXT-10과 같은 한국어 어휘 의존

### EXT-12: 역할 다양화 Director Ensemble
- **출처**: CritiCS (EMNLP 2024) — 역할별 비평가가 단일 심판보다 우수
- **정의**: 앙상블 각 Director 인스턴스에 다른 평가 렌즈 부여 (연속성 전문가 / 감정 아크 전문가 / 페이싱 전문가)
- **글도비 적용**: Director SC 투표 시 각 투표자에 `system` 프롬프트로 전문 영역 지정. "당신은 캐릭터 연속성 전문가입니다" vs "당신은 감정 아크 전문가입니다"
- **구현**: 프롬프트 변경. LLM 추가 0회 (기존 SC 투표 수 유지)
- **우선순위**: **P1** — SC 투표 품질 향상 기대

### EXT-13: LongStoryEval 8차원 평가 차원 도입
- **출처**: LongStoryEval (ACL 2025) — 340K 리뷰 분석 → 8차원 20하위
- **정의**: plot_structure, characters, writing_language, themes, world_building, emotional_impact, enjoyment_engagement, expectation_fulfillment
- **글도비 적용**: NC-3 `consistency_checklist` 17항목 중 누락된 차원 보충. 특히 `emotional_impact`(현재 `emotional_authenticity`만), `expectation_fulfillment`(현재 미보유), `world_building`(현재 `spatial_continuity`만)
- **구현**: 프롬프트 변경. LLM 추가 0회
- **우선순위**: **P2** — 체크리스트 확장은 Director 프롬프트 크기 증가

### EXT-14: 플롯홀 5유형 분류 체계 — TruthGate 확장
- **출처**: Finding Flawed Fictions (arXiv 2504.11900, 2025)
- **정의**: ①연속성 오류 ②캐릭터 탈선 ③사실 오류(시대착오) ④불가능 사건 ⑤미해결 스토리라인
- **글도비 적용**: TruthGate 7검사 + NpcDrift + Advisory 체인을 이 5유형에 매핑 → 커버리지 갭 확인. 특히 ⑤미해결 스토리라인은 B-4(동기/약속 방치)로 부분 커버되나, 보다 체계적 추적 가능
- **구현**: 분류 매핑만. 코드 변경 최소
- **우선순위**: **P3** — 분류 체계 정리, 기능 변경 없음

### EXT-15: CONCOCT 블록 구체성 균일화
- **출처**: CONCOCT (EMNLP 2023) — 페이싱 균일성 57%+ 인간 선호
- **정의**: Blueprint 블록들의 상세도(구체성) 편차 측정. 모호한 블록부터 먼저 확장
- **글도비 적용**: Blueprint 블록별 "구체성 점수" 계산 (고유명사/수치/행동 동사 밀도). 편차가 크면 "블록 N은 지나치게 모호합니다" advisory
- **구현**: Python. LLM 0회
- **우선순위**: **P2** — Stage 3 품질 향상

### EXT-16: 유사성-참신성 균형 모니터링
- **출처**: Jing 2025, Nature HSS Communications — 장르 관습 준수→유입, 참신성→만족
- **정의**: 장기 연재에서 장르 관습 준수도와 전략적 참신성의 균형 추적
- **글도비 적용**: GenreGuard 적합도 + PatternTracker 반복도를 결합한 "혁신 지수" — 너무 관습적이면 "정형화 경고", 너무 벗어나면 GenreGuard가 이미 잡음. 중간 밸런스 최적점 추적
- **구현**: 기존 메트릭 조합. LLM 0회
- **우선순위**: **P3** — 기존 시스템 조합으로 충분

### EXT-17: 공유 스크래치패드 통합
- **출처**: Agents' Room (ICLR 2025, DeepMind) — 에이전트 간 누적 문서
- **정의**: 모든 에이전트가 읽고 추가하는 단일 누적 컨텍스트 문서
- **글도비 적용**: 현재 `_director_mc_parts` + `_reference_only_parts` + 각종 advisory를 단일 구조화된 JSON 스크래치패드로 통합. 에이전트 간 정보 누락 방지
- **구현**: 아키텍처 리팩터링. 코드 변경 대
- **우선순위**: **P3** — 현재 DI Context가 역할을 수행 중

### EXT-18: SCORE EASM 벤치마크 타겟
- **출처**: SCORE (arXiv 2503.23512) — 89.7% 감정 일관성
- **정의**: 에피소드 간 감정 아크 정합성 수치. 89.7%가 SCORE의 달성치
- **글도비 적용**: 글도비의 감정 아크 정합성을 EASM 방법론으로 측정하여 SCORE 대비 벤치마킹
- **구현**: EASM 구현 필요. 중간
- **우선순위**: **P3** — 벤치마킹용, 기능 개선은 아님

### EXT-19: 심리적 깊이 5차원 자기비평
- **출처**: EMNLP 2024 — 진정성/서사복잡성/공감/몰입/감정유발
- **정의**: 기존 self-critique에 심리적 깊이 차원 추가
- **글도비 적용**: `chief_writer_quality` self-critique에 "등장인물의 감정이 진정성 있게 묘사되었는가?" 체크 추가. 현재 `emotional_authenticity`보다 구체적
- **구현**: 프롬프트 추가 1줄. LLM 0회
- **우선순위**: **P2** — self-critique 16번째 체크 (현재 15개)

### EXT-20: 동적 아웃라인 — Arc 실행 중 수정
- **출처**: DOME (NAACL 2025) — 아웃라인이 생성 중 적응
- **정의**: Arc/Blueprint가 에피소드 생성 결과에 따라 동적으로 수정됨
- **글도비 적용**: TF-48(Arc 실행 상태 연속성)이 부분 구현. PASS_WITH_FIX가 국소 수정 제공. 하지만 Blueprint 자체를 에피소드 결과에 따라 re-plan하는 메커니즘은 미보유
- **구현**: 높음. Arc re-planning 로직 신규
- **우선순위**: **P3** — 현재 PASS_WITH_FIX + retry로 충분히 대응

### EXT-21: Suspense = 탈출 경로 축소
- **출처**: Xie & Riedl (EACL 2024) — 인지심리학 기반 서스펜스 정의
- **정의**: 서스펜스 = 주인공의 탈출 경로가 줄어드는 것. Blueprint에서 의도적으로 탈출 옵션을 제거하며 긴장감 구축
- **글도비 적용**: Blueprint 생성 시 "주인공 선택지 축소" 지시를 core_tension에 연결. Arc 중반부에서 의도적 선택지 제한
- **구현**: 프롬프트 변경. LLM 0회
- **우선순위**: **P2** — Blueprint 프롬프트 강화

### EXT-22: 장르 적합성 구조 검증
- **출처**: Trilogy Manuscript AI — 100점 원고 점수 3요소 중 "Genre Fit"
- **정의**: 장르 핵심 요소가 예상 위치 범위에 등장하는지 구조적 검증. 예: 로맨스에서 관심인물 등장 위치가 전체의 30% 이전이어야
- **글도비 적용**: Treatment/Arc 단계에서 장르별 필수 요소의 예상 위치를 정의하고, Blueprint/원고에서 실제 위치 검증
- **구현**: 장르별 규칙 정의 필요. Python. LLM 0회
- **우선순위**: **P2** — GenreGuard 확장

### EXT-23: 비선형 서사 생성 지원
- **출처**: StoryWriter (CIKM 2025) — NLN(Non-Linear Narration)
- **정의**: 회상/플래시백을 "감지"뿐 아니라 "의도적으로 생성"하는 기능
- **글도비 적용**: FlashbackVerifier(LM-E)가 감지는 하지만, Blueprint에서 의도적으로 비선형 구조를 계획하는 기능은 미보유. Treatment에 "회상 삽입 블록" 유형 추가 가능
- **구현**: Treatment 스키마 + Blueprint 생성 확장. 높음
- **우선순위**: **P3** — 현재 선형 서사가 웹소설 주류

### EXT-24: 이중 시간축 — 스토리 시간 vs 처리 시간
- **출처**: Zep/Graphiti (arXiv 2025) — 이중 시간축 지식 그래프
- **정의**: 스토리 내 시간(T)과 데이터 처리 시간(T')을 분리 추적. 소급 수정 지원
- **글도비 적용**: 현재 `cumulative_elapsed`(스토리 시간)만 추적. 처리 시간 추가 시 "에피소드 5에서 설정했지만 에피소드 8에서 수정된" 팩트 이력 추적 가능
- **구현**: DB 스키마 확장. 중간
- **우선순위**: **P3** — npc_history가 부분적으로 역할

### EXT-25: 6대 감정 아크 형태 활용
- **출처**: Reagan 2016 (Science Advances, 2000+ 인용) — 가장 인기 있는 아크: Icarus(상승→하락), Oedipus(하락→상승→하락)
- **정의**: Treatment/Arc 설계 시 6대 감정 아크 형태 중 하나를 명시적으로 선택하여 감정 궤적 계획
- **글도비 적용**: Treatment 설계 단계에서 `emotional_arc_type: "icarus"` 등 명시 지정. Blueprint에서 해당 형태에 맞는 감정 전환점 배치
- **구현**: 스키마 + 프롬프트 변경. LLM 0회
- **우선순위**: **P2** — Treatment 설계 고도화

### EXT-26: 문피아 위험 신호 — 댓글↑+추천↓ 패턴
- **출처**: 문피아 흥행작 연구 (KCI)
- **정의**: 댓글 급증 + 추천 감소 = 독자 이탈 위험 신호
- **글도비 적용**: 실제 플랫폼 연동 시 독자 반응 신호 수집 가능하나, 현재는 파이프라인 내부 품질 신호로 대체. `episode_quality_labels` 추세 분석에서 유사 패턴(점수↓+advisory↑) 감지
- **구현**: 기존 FL-5 품질 추세 경고에 통합 가능
- **우선순위**: **P3** — 외부 데이터 의존

### EXT-27: 복잡도 점수 — 문장 길이 분포
- **출처**: AutoCrit — 인기작 기준 2.0-3.0
- **정의**: 문장 길이 분포의 가중 평균. 인기 소설은 짧은 문장과 긴 문장의 균형
- **글도비 적용**: EXT-02 Burstiness와 결합하여 "문장 복잡도 + 변동성" 이중 메트릭
- **구현**: Python 5줄. LLM 0회
- **우선순위**: **P1** — EXT-02와 함께 구현

### EXT-28: NarraBench 서사학 갭 매핑
- **출처**: NarraBench (arXiv 2025) — 78벤치 메타분석 결과 27%만 적합 커버
- **정의**: 서사학 Big-4(Story/Narration/Discourse/Situatedness) 중 Narration(시점/스타일/비유)과 Discourse(서스펜스/놀라움/호기심)가 기존 벤치마크의 73%에서 미측정
- **글도비 적용**: Discourse 차원 — 서스펜스(EXT-21)와 놀라움(현재 미측정)을 명시적 평가 차원으로 추가. Narration 차원 — 비유적 표현 다양성을 PatternTracker에 추가
- **구현**: 프롬프트 + PatternTracker 확장
- **우선순위**: **P2** — 서사학적 완전성 향상

---

## §3. 2차 전수조사 — 교차 검증 + 중복 제거

### 하향 조정 (5건)
| ID | 이유 |
|----|------|
| EXT-10 | EXT-03(반전)과 EXT-11(긴장도)과 모두 한국어 감성 어휘 의존. 3개를 묶어 "한국어 감정 분석 패키지"로 통합 → 개별 P2, 패키지 P1 |
| EXT-13 | NC-3 체크리스트가 이미 17개. 추가 확장은 Director 프롬프트 비대화 위험 → P3으로 하향 |
| EXT-17 | DI Context가 이미 스크래치패드 역할. 아키텍처 리팩터링 ROI 낮음 → P3 유지 |
| EXT-24 | npc_history + FactLedger가 이미 이력 추적. 이중 시간축은 과잉설계 → P3 유지 |
| EXT-26 | 외부 플랫폼 데이터 없이는 구현 불가 → P3 유지 |

### 상향 조정 (3건)
| ID | 이유 |
|----|------|
| EXT-05 | CheckEval의 IAA +0.45 개선은 매우 강력. NC-3 핵심 5개 항목만 이진 분해해도 Director 채점 신뢰도 대폭 향상 → **P0** 상향 |
| EXT-09 | 3후보 다양성 문제는 실파이프라인에서 실제로 발생. Sui Generis 간이 버전(키워드 겹침률)은 Python-only 즉시 구현 가능 → **P0** 상향 |
| EXT-12 | Director SC 투표 역할 다양화는 프롬프트 변경만으로 구현. CritiCS의 EMNLP 결과가 강력 → **P0** 상향 |

### 통합 (2건)
| 통합 결과 | 원본 |
|----------|------|
| **EXT-EMOTION** (한국어 감정 분석 패키지) | EXT-03 + EXT-10 + EXT-11 → 한국어 NRC-VAD 어휘 확보 1회로 3개 메트릭 동시 활성화 |
| **EXT-STRUCT** (문장 구조 분석 패키지) | EXT-02 + EXT-27 → Burstiness + Complexity 동시 계산 |

---

## §4. 3차 전수조사 — 최종 우선순위

### P0 (즉시 구현, Python-only, ROI 최고) — 6건

| ID | 아이디어 | 구현 비용 | LLM | 효과 |
|----|---------|----------|-----|------|
| **EXT-01** | gzip 압축률 반복성 탐지 | 2줄 | 0 | 구조적 반복 캐치 |
| **EXT-STRUCT** | Burstiness + Complexity 이중 메트릭 | 10줄 | 0 | 문장 단조로움 캐치 |
| **EXT-04** | 대화 비율 25-35% 체크 | 15줄 | 0 | 서술/대화 밸런스 |
| **EXT-05** | CheckEval 이진 분해 (NC-3 핵심 5개) | 프롬프트 | 0 | Director 채점 신뢰도 +0.45 IAA |
| **EXT-09** | 앙상블 후보 다양성 (키워드 겹침률) | 30줄 | 0 | "같은 이야기 3편" 방지 |
| **EXT-12** | 역할 다양화 Director SC | 프롬프트 | 0 | SC 투표 품질 |

### P1 (중단기, 높은 ROI) — 5건

| ID | 아이디어 | 구현 비용 | LLM | 효과 |
|----|---------|----------|-----|------|
| **EXT-06** | Deduction/Bonus Director 피드백 구조화 | 프롬프트+스키마 | 0 | CW retry 정확도 |
| **EXT-EMOTION** | 한국어 감정 분석 패키지 (반전+VAD+긴장도) | 중간 | 0 | 감정 아크 3대 메트릭 동시 |
| **EXT-21** | Suspense = 탈출 경로 축소 (프롬프트) | 프롬프트 | 0 | Blueprint 긴장감 |
| **EXT-25** | 6대 감정 아크 형태 Treatment 활용 | 스키마+프롬프트 | 0 | 감정 구조 계획 |
| **EXT-22** | 장르 적합성 구조 검증 | 장르별 규칙 | 0 | 구조적 장르 준수 |

### P2 (후순위, 외부 의존성 또는 큰 변경) — 6건

| ID | 아이디어 | 비고 |
|----|---------|-----|
| EXT-07 | TIMECHARA 3인칭 캐릭터 지식 검증 | DB 확장, LM-F 1인칭 이미 커버 |
| EXT-08 | POS 템플릿 반복률 | KoNLPy 의존성 |
| EXT-15 | Blueprint 블록 구체성 균일화 | Stage 3 프롬프트 |
| EXT-19 | 심리적 깊이 self-critique | 16번째 체크 추가 |
| EXT-28 | NarraBench Discourse 차원 추가 | 서스펜스/놀라움 명시 평가 |
| EXT-20 | 동적 아웃라인 (Arc re-planning) | 아키텍처 변경 대 |

### P3 (관찰/참고, 현재 불필요) — 5건

| ID | 아이디어 | 비고 |
|----|---------|-----|
| EXT-14 | 플롯홀 5유형 분류 매핑 | 분류 체계만, 코드 변경 없음 |
| EXT-16 | 유사성-참신성 균형 모니터링 | GenreGuard가 이미 역할 |
| EXT-17 | 공유 스크래치패드 | DI Context가 이미 역할 |
| EXT-23 | 비선형 서사 생성 | 웹소설 주류가 선형 |
| EXT-24 | 이중 시간축 | npc_history가 이미 역할 |

---

## §5. 신뢰도 평가 — 소스별

### Tier 1: 최고 신뢰 (A~A+)
- **LongStoryEval** (ACL 2025 main) — 600권, 340K 리뷰, NovelCritique 8B 모델
- **ASE/HANNA** (TACL 2024) — 19,008 인간 주석, 6차원 표준
- **CheckEval** (EMNLP 2025) — IAA +0.45 개선 실증
- **CHARACTERBENCH** (AAAI 2025) — 22,859 주석
- **TIMECHARA** (ACL 2024) — 시점별 할루시네이션 정형화
- **Knight 2024 서사 반전** (Science Advances) — 30,000작품 교차 도메인 검증
- **Reagan 2016 감정 아크** — 2,000+ 인용, 후속 연구 다수 확인

### Tier 2: 높은 신뢰 (A-~B+)
- **NarraBench** (Cornell/McGill) — 78벤치 메타분석, 서사학 이론 기반
- **CollabStory** (NAACL 2025) — 32,000+ 스토리
- **CritiCS** (EMNLP 2024) — 멀티에이전트 비평 검증
- **DOC** (ACL 2023) — +22.5% 일관성 인간 평가
- **DOME** (NAACL 2025) — 동적 아웃라인 검증
- **Agents' Room** (ICLR 2025, DeepMind) — 최상위 학회
- **CONCOCT** (EMNLP 2023) — 페이싱 57%+ 선호
- **Jing 2025 유사성/참신성** (Nature HSS) — 대규모 AO3 데이터
- **SCORE** (arXiv, 6버전) — 아키텍처 직접 비교 가능
- **PNAS 2025 Sui Generis** — 최상위 저널
- **EMNLP 2024 POS 템플릿** — 76% 발견 강력

### Tier 3: 보통 신뢰 (B~B-)
- **Story Theory Benchmark** (GitHub) — 재현 가능하나 미피어리뷰
- **GrAImes** — 스페인어 한정
- **AI Creativity Framework** (arXiv 2026-01) — 115명 크라우드
- **Fong & Gui 기대 모델링** — 미피어리뷰 프리프린트
- **AutoCrit/Marlowe 메트릭** — 상용 도구, 비공개 검증
- **문피아 흥행작 연구** — KCI, 단일 플랫폼

### Tier 4: 참고용 (C+~)
- **StoryBench Memory** — 인터랙티브 픽션 특화
- **RecurrentGPT** — 2023, 컨텍스트 창 한계 시대 기법
- **LTSG** — 지식그래프 아이디어는 유효하나 검증 약함

---

## §6. 글도비 기존 시스템 대비 커버리지 매트릭스 (확장)

### 1차 문서의 ConStory 19-subtype + 신규 차원 통합

| 차원 | 글도비 대응 | 커버리지 | 신규 강화 방안 |
|------|-----------|---------|-------------|
| 서사 반전/감정 변동 | PatternTracker (부분) | 🟡 30% | **EXT-03** 반전 빈도 메트릭 |
| 감정 아크 정합성 | Blueprint emotional_arc (계획만) | 🟡 40% | **EXT-10** VAD 정합성 검증 |
| 긴장도/서스펜스 | 없음 | 🔴 0% | **EXT-11** Tension Vector + **EXT-21** 탈출 경로 |
| 놀라움/기대 위반 | 없음 | 🔴 0% | **EXT-28** NarraBench Discourse |
| 대화 비율 밸런스 | chief_writer.yaml 규칙13 (일부) | 🟡 50% | **EXT-04** 25-35% 타겟 |
| 문장 구조 다양성 | _check_paragraph_structure (일부) | 🟡 40% | **EXT-STRUCT** Burstiness+Complexity |
| 구조적 반복성 | PatternTracker 2-gram (일부) | 🟡 50% | **EXT-01** gzip 압축률 |
| 앙상블 후보 다양성 | 없음 (3후보 생성만) | 🔴 0% | **EXT-09** Sui Generis 간이판 |
| Director 채점 신뢰도 | SC 투표 + NC-3B 합산 검증 | 🟢 70% | **EXT-05** 이진 분해 + **EXT-12** 역할 다양화 |
| CW retry 피드백 품질 | rejection_reason + action_items | 🟢 60% | **EXT-06** Deduction/Bonus |
| 캐릭터 지식 범위 | InfoParadoxChecker (1인칭만) | 🟡 50% | **EXT-07** TIMECHARA 3인칭 |
| 장르 구조 적합성 | GenreGuard 10종 (내용만) | 🟡 50% | **EXT-22** 구조적 위치 검증 |
| Blueprint 상세도 균일성 | 없음 | 🔴 0% | **EXT-15** CONCOCT 구체성 |
| 심리적 깊이 | emotional_authenticity (1항목) | 🟡 30% | **EXT-19** 5차원 |
| 감정 아크 형태 계획 | emotional_arc 자유 텍스트 | 🟡 40% | **EXT-25** 6대 형태 명시 |

**전체 커버리지**: 기존 15개 차원 중 🟢 2개(13%) / 🟡 9개(60%) / 🔴 4개(27%)

---

## §7. 구현 로드맵 (1차 문서 Phase A/B/C에 추가)

### Phase A+ (P0 즉시 구현, 1-2일)
1. **EXT-01** `chief_writer_quality._check_compression_ratio()` — gzip 2줄
2. **EXT-STRUCT** `pattern_tracker._compute_burstiness()` + `_compute_complexity()` — 10줄
3. **EXT-04** `chief_writer_quality._check_dialogue_ratio()` — regex 15줄
4. **EXT-09** `director_ensemble._check_candidate_diversity()` — 키워드 겹침 30줄
5. **EXT-05** `director.yaml` NC-3 핵심 5개 항목 이진 분해 — 프롬프트 변경
6. **EXT-12** `director_auditor.py` SC 투표자 역할 프롬프트 분화 — 프롬프트 변경

### Phase B+ (P1, 1주)
1. **EXT-06** Director 피드백 Deduction/Bonus 스키마
2. **EXT-EMOTION** 한국어 NRC-VAD 어휘 확보 → 반전+VAD+긴장도 3메트릭
3. **EXT-21** Blueprint core_tension → "탈출 경로 축소" 프롬프트
4. **EXT-25** Treatment emotional_arc_type 6형태 스키마
5. **EXT-22** 장르별 구조 필수 요소 위치 규칙

### Phase C+ (P2, 후순위)
- EXT-07/08/15/19/20/28 — 외부 의존성 또는 큰 변경 필요

---

## §8. 참고 문헌 (전량)

### 벤치마크/프레임워크
- LongStoryEval: arXiv 2512.12839
- NarraBench: arXiv 2510.09869
- Story Theory Benchmark: github.com/clchinkc/story-bench
- SCORE: arXiv 2503.23512
- "Novel" Benchmark: ACL Findings 2025 (aclanthology.org/2025.findings-acl.1114)
- GrAImes: arXiv 2506.08172
- ASE/HANNA: TACL 2024 (aclanthology.org/2024.tacl-1.62)
- EvolvR: arXiv 2508.06046
- CreativityPrism: arXiv 2510.20091
- "The Reader is the Metric": arXiv 2506.03310
- CollabStory: NAACL 2025 (aclanthology.org/2025.findings-naacl.203)
- Narrative Planning: arXiv 2506.10161
- StoryBench Memory: arXiv 2506.13356
- AI Creativity Framework: arXiv 2601.03698
- CHARACTERBENCH: AAAI 2025
- TIMECHARA: ACL 2024
- CheckEval: EMNLP 2025 (arXiv 2403.18771)
- RLMR: arXiv 2508.18642

### NLG 메트릭/방법론
- Standardized Text Diversity: arXiv 2403.00553
- POS Templates: EMNLP 2024 (arXiv 2407.00211)
- Sui Generis: PNAS 122(35) 2025
- Finding Flawed Fictions: arXiv 2504.11900
- G-Eval: EMNLP 2023 (arXiv 2303.16634)
- X-Eval: NAACL 2024
- Themis: EMNLP 2024
- InstructScore: EMNLP 2023

### 아키텍처/기법
- DOC: ACL 2023 (aclanthology.org/2023.acl-long.190)
- DOME: NAACL 2025 (arXiv 2412.13575)
- Agents' Room: ICLR 2025 (arXiv 2410.02603)
- StoryBox: arXiv 2510.11618
- CritiCS: EMNLP 2024 (aclanthology.org/2024.emnlp-main.1046)
- StoryWriter: CIKM 2025 (arXiv 2506.16445)
- RecurrentGPT: arXiv 2305.13304
- Zep/Graphiti: arXiv 2501.13956
- NCP: COLM 2025 (arXiv 2503.22828)
- CONCOCT: EMNLP 2023 (arXiv 2311.04459)
- LTSG: arXiv 2508.03137

### 독자 참여/시장 연구
- Knight 2024 서사 반전: Science Advances 10.1126/sciadv.adl2013
- Jing 2025 유사성/참신성: Nature HSS Communications 10.1038/s41599-025-05166-3
- Reagan 2016 감정 아크: arXiv 1606.07772
- Fong & Gui 기대 모델링: arXiv 2412.15239
- 문피아 흥행작: KCI ART002726821
- EMNLP 2024 심리적 깊이: aclanthology.org/2024.emnlp-main.953
- Xie & Riedl 서스펜스: EACL 2024 (arXiv 2402.17119)
- CONCOCT 페이싱: EMNLP 2023 (arXiv 2311.04459)
- Causal Reasoning Failure: arXiv 2410.23884

### 상용 도구
- AutoCrit: autocrit.com
- Marlowe: authors.ai/marlowe
- Trilogy: publishersweekly.com
- Sudowrite: sudowrite.com
- Novelcrafter: novelcrafter.com
- EQ-Bench v3: eqbench.com/creative_writing_longform.html
- AI Dungeon SCORE: arXiv 2503.23512
