# 글도비 장편 웹소설 LLM 모델 선정 보고서

**TF 보고일**: 2026-03-18 (5Pass 보강판)
**대상**: 250화, 화별 5,000자 이상 한국어 웹소설 자동 생산
**확신도**: 86% (5Pass 감리 완료 — Devil's Advocate 관점 반영, 한국어 창작 벤치마크 부재 + 1M 컨텍스트 실전 품질 미검증)

**TF 구성** (5개 병렬 에이전트):
| TF | 역할 | 도구 사용 | 소요 |
|----|------|----------|------|
| TF1 | 벤치마크/가격 최신 검증 | 38 tool uses | ~4분 |
| TF2 | 한국어 창작 품질 심층 조사 | 44 tool uses | ~11분 |
| TF3 | 장편소설 생성 논문/인프라 비교 | 33 tool uses | ~10분 |
| TF4 | 비용/토크나이저/TCO 분석 | 41 tool uses | ~9분 |
| TF5 | 반론 전문 (Devil's Advocate) | 28 tool uses | ~8분 |

---

## 0. 요약 결론 (Executive Summary)

| 순위 | 모델 | 역할 | 근거 |
|------|------|------|------|
| **1위** | **Claude Opus 4.6** | 창작 핵심 (ChiefWriter, Director) | Mazur Writing #1 (8.53), EQ-Bench CW Elo 1932, 1M 컨텍스트, 128K 출력, 장문 충실도 최상 |
| **2위** | **Gemini 2.5 Pro** | 현행 시스템 유지 시 최선 | 가성비 4x (Opus 대비), implicit caching, 1M/65K, Mazur #9 (8.22) |
| **3위** | **Claude Sonnet 4.6** | 비용 절충형 창작 | EQ-Bench CW Elo #1 (1936), Opus 60% 가격, 1M/64K |
| 보조 | **Gemini 2.5 Flash** | 검증/Advisory/경량 작업 | $0.30/MTok, 현행 시스템 flash 역할 유지 |

**최적 전략**: 2-tier 멀티모델 — 창작 엔진(Opus 4.6) + 검증 엔진(Flash) = 품질 극대화 + 비용 통제

**5Pass 조건부 권고** (확신도 86%):
- Pilot-First 의무: ChiefWriter 1개만 Opus 전환 → 30화 블라인드 비교 후 전면 전환 판단
- 1M 컨텍스트 실전 테스트 + Rate Limit 사전 검증 + Provider Abstraction Layer 구축 선행
- GPT-5.4 Mazur 등재 및 Gemini 3.1 Pro GA 시 재평가 트리거

---

## 1. 글도비 시스템이 LLM에 요구하는 기술 조건

### 1.1 필수 사양 (MUST)

| 요구사항 | 현행값 | 근거 파일 |
|----------|--------|-----------|
| 컨텍스트 윈도우 | **1,000,000자** (≈500K-700K 토큰) | `validation.yaml` L75 |
| 최대 출력 토큰 | **65,536 토큰** | `system.yaml` L18 |
| 구조화 출력 (JSON) | 필수 — `response_mime_type: application/json` | `base_agent.py` L972 |
| 컨텍스트 캐싱 | 50,000자 이상 시 활성, 5개 에이전트 적용 | `system.yaml` L36-40 |
| 동시 요청 | 8-9개 병렬 (Advisory Chain) | `stage4_interview_round.py` L2330 |
| API 타임아웃 | 300초 (5분) | `system.yaml` L17 |
| 확장 추론 (Thinking) | 1,024~24,576 토큰 예산 | `system.yaml` L7-12 |
| Fallback 체인 | pro → flash 자동 전환 | `models.yaml` L47-49 |

### 1.2 에피소드당 LLM 호출량

| 스테이지 | 역할 | 호출 수 | 모델 티어 |
|----------|------|---------|-----------|
| Stage 2 (Arc) | 5-arc 전술 설계 | 40-75 | Pro x 6 + Flash x 8 |
| Stage 3 (Blueprint) | 30화 설계도 | 50-80 | Pro x 4 + Flash x 6 |
| Stage 4 (Manuscript) | 원고 생산 + 검증 | 600-900 | Pro x 3 + Flash x 8 (per ep) |
| **30화 Arc 합계** | | **700-1,000+** | |
| **250화 전체** | | **~6,000-8,500** | |

### 1.3 현행 에이전트-모델 매핑 (22개 에이전트)

**Pro 급 (7개)**: chief_writer, director, analyst, continuity_inspector, four_phase_arc_generator, blueprint_ensemble, three_phase_blueprint_generator, state_locked_arc_generator

**Flash 급 (10개)**: manager, block_enricher, preflight_checker, state_extractor, arc_corrector, arc_critic, consensus_validator, unified_arc_validator, unified_blueprint_validator, critic, weaver, writer

---

## 2. 2026년 3월 기준 후보 모델 비교

### 2.1 사양 비교표 (검증 완료)

| 모델 | 컨텍스트 | 최대 출력 | Input $/MTok | Output $/MTok | 캐시 읽기 | 배치 할인 | 검증 상태 |
|------|----------|-----------|-------------|--------------|-----------|-----------|-----------|
| **Claude Opus 4.6** | 1M | 128K | $5.00 | $25.00 | $0.50 (0.1x) | 50% | CONFIRMED |
| **Claude Sonnet 4.6** | 1M | 64K | $3.00 | $15.00 | $0.30 (0.1x) | 50% | CONFIRMED |
| **GPT-5.4** | 1.05M | 128K | $2.50 | $15.00 | $0.25 (0.1x) | 50% | CONFIRMED |
| **Gemini 3.1 Pro Preview** | 1M | 64K | $2.00 | $12.00 | $0.20 (0.1x) | 50% | CONFIRMED |
| **Gemini 2.5 Pro** | 1M | 65K | $1.25 | $10.00 | $0.125 (0.1x) | 50% | CONFIRMED (현행) |
| **Gemini 2.5 Flash** | 1M | 65K | $0.30 | $2.50 | $0.03 (0.1x) | 50% | CONFIRMED (현행) |
| **GPT-5.4-Mini** | **400K** | **128K** | $0.75 | $4.50 | $0.075 | 50% | CONFIRMED (3/17 출시, 사양 정정) |
| **Claude Haiku 4.5** | 200K | 64K | $1.00 | $5.00 | $0.10 | 50% | CONFIRMED |
| **Qwen 3.5 Plus** | 1M | 65K | $0.26 | $1.56 | - | - | CONFIRMED |
| **DeepSeek V3.2** | 164K | **65K** (V3.2-Exp) | $0.28 | $0.42 | $0.028 (0.1x) | 50% | CONFIRMED (사양 정정) |
| **Llama 4 Maverick** | 1M | 16K | $0.15 | $0.60 | - | - | CONFIRMED |

> **주의**: GPT-5.4는 272K 초과 시 input $5.00 / output $22.50으로 2배. Gemini 2.5 Pro는 200K 초과 시 input $2.50 / output $15.00.

### 2.2 창작 품질 벤치마크 (검증 완료)

#### Mazur Writing Benchmark V4 (github.com/lechmazur/writing)
10개 필수 스토리 요소 + 18개 루브릭 (60% 서사 기술, 40% 요소 통합)

| 순위 | 모델 | 점수 | 비고 |
|------|------|------|------|
| 1 | **Claude Opus 4.6 Thinking** | 8.56 | Thinking 16K |
| 2 | **Claude Opus 4.6** | 8.53 | 추론 없음 |
| 3 | **GPT-5.2** | 8.51 | Medium reasoning |
| 4 | GPT-5 Pro | 8.47 | |
| 7 | Kimi K2-0905 | 8.33 | Moonshot AI (보고서 누락 → 추가) |
| 8 | **Gemini 3 Pro Preview** | 8.22 | ~~3.1이 아닌 3 Pro~~ (명명 정정) |
| 9 | **Gemini 2.5 Pro** | 8.22 | 현행 시스템 |
| 15 | Qwen 3 Max Preview | 8.09 | ~~Qwen 3.5 Plus 아님~~ (모델 구분 정정) |
| 10 | Mistral Medium 3.1 | 8.20 | 보고서 누락 → 추가 |
| 21 | DeepSeek V3.2 | 7.60 | |
| 30 | Llama 4 Maverick | 5.78 | **최하위** |

#### EQ-Bench Creative Writing v3 (Elo 기반)

| 모델 | Elo |
|------|-----|
| **Claude Sonnet 4.6** | 1936 |
| **Claude Opus 4.6** | 1932 |

#### LM Arena (Chatbot Arena) Overall Text (2026-03-05 기준)

| 순위 | 모델 | Elo |
|------|------|-----|
| 1 | **Claude Opus 4.6** | 1504 |
| 2 | Gemini 3.1 Pro Preview | 1500 |
| 3 | Claude Opus 4.6 Thinking | 1500 |
| 4 | Grok 4.20 Beta1 | 1493 |
| 5 | Gemini 3 Pro | 1485 |

> **핵심**: Claude 계열이 Mazur + EQ-Bench 두 창작 벤치마크 1-2위 독점, LM Arena Overall 1위. Gemini 2.5 Pro는 Mazur 8.22로 상위권이나 Opus 대비 0.31점 격차.
>
> **주의**: Mazur V4에 미등재 모델 — Claude Sonnet 4.6, GPT-5.4, GPT-5.4-Mini, Gemini 3.1 Pro Preview, Qwen 3.5 Plus. GPT-5.4는 GPT-5.2(8.51) 대비 향상 예상되나 미확인.

### 2.3 한국어 토크나이징 효율 (비용에 직결)

| 모델 계열 | 한국어 효율 (chars/token) | 5,000자 → 토큰 수 | 비고 |
|-----------|--------------------------|-------------------|------|
| **DeepSeek** | ~2.02 | ~2,475 | CJK 최적화, 2.46x Gemini 대비 |
| **Claude** | ~1.25 | ~4,000 | Gemini 대비 ~20% 더 많은 토큰 |
| **Gemini** | ~0.82 | ~6,100 | SentencePiece, CJK 비효율 |
| **GPT** | ~1.0-1.2 | ~4,200-5,000 | tiktoken, 보통 수준 |
| **Qwen** | ~1.5-1.8 | ~2,800-3,300 | 중국어 최적화 → 한국어 수혜 |

> **핵심**: 동일한 5,000자 한국어 원고에 대해 Gemini는 ~6,100 토큰, Claude는 ~4,000 토큰, DeepSeek는 ~2,475 토큰. **출력 토큰 단가 x 토큰 수 = 실질 비용**이므로 토크나이저 효율이 가격표만큼 중요.

---

## 3. 심층 분석: 5대 평가 축

### 3.1 창작 품질 (가중치 35%)

**Claude Opus 4.6 압도적 1위.**

- Mazur V4 1위 (8.53/10), EQ-Bench CW Elo 1932
- 감정 깊이, 캐릭터 보이스, 대화 품질에서 일관적으로 최상위
- "확장 추론(Thinking)" 활성화 시 8.56으로 추가 향상
- Gemini 2.5 Pro는 8.22로 상위권이나 "격"의 차이 존재
- GPT-5.2/5.4는 8.51로 근접하나, 한국어 창작 특화 데이터 부족 보고
- **Llama 4 Maverick은 5.78로 창작에 부적격 (탈락)**
- **DeepSeek V3.2는 7.60으로 보조 역할까지만 가능**

**한국어 고유 사항** (TF2 심층 조사):

한국어 전용 **창작** 벤치마크는 부재 (KMMLU, KoBEST, CLIcK, HAE-RAE, KoBALT, LogicKor 등은 모두 NLU/교육/추론 평가이며 문학적 창작 품질은 미측정). 정량적 평가 불가 → 커뮤니티 정성 평가에 의존.

**DC Inside AI소설 마이너갤러리 (aiwriter) 직접 인용**:
- **Claude 강점**: "윤문(문장 다듬기) 능력 최강. 내가 수정할 게 없다고 판단했는데 Claude가 완벽하게 찾아낸다" / "노블레스 시대 수준 품질 가능. 노벨피아 연재 작가가 상위권 도달 가능"
- **Claude 약점**: "초고가 거지같음" / 토큰 소비가 심해 일일 한도 1.5-3만자에서 고갈
- **Gemini 강점**: "한국어 감성을 GPT나 Claude보다 훨씬 잘 살림" / "번역체가 제일 적음" / 1M 토큰 용량 독보적 / 70-80% 출력 즉시 사용 가능
- **Gemini 약점**: "문체 자체의 맛은 전혀 없음" / "장황함과 화려함을 못 멈춤" / "아무리 학습시켜도 무미건조" / 윤문 제안 중 5%만 유용
- **커뮤니티 합의 분열**: "웹소설 작가들은 클로드보다 제미나이가 1황" (물량/비용 기준) vs "윤문/문학 품질은 Claude가 만장일치 1위"

**나무위키**: "어느 모로 보나 GPT보다는 월등" / Claude의 구조적 정합성과 한국어 자연스러움 일관 최상위 평가

**한국어 웹소설 특수 요구사항**:
- **경어/반말 체계**: 존댓말/반말/해요체/하십시오체 — 캐릭터 관계에 따른 일관성 필수 (자동 테스트 불가)
- **의성어/의태어**: 한국어 서사에 필수적. 연구 기준 단일 코퍼스에서 의성어 82개, 의태어 164개 발견. 의태어의 창의적 활용은 한국 문학 품질 지표이나 LLM 평가 벤치마크 전무
- **번역체 (translationese)**: 영어 구문 직역 스타일 — Gemini가 가장 적고, Claude/GPT는 프롬프팅으로 완화 가능

**HyperCLOVA X**: 한국어 네이티브 모델(SEED 1.5B-32B). 한국어 품질 잠재적 최상이나, 컨텍스트 윈도우 미공개(추정 <200K), 최대 출력 제한, NAVER Cloud 전용 API → 글도비의 1M/65K 요구사항 불충족. 창작 벤치마크 없어 비교 불가.

### 3.2 장문 일관성 — "Lost in the Middle" (가중치 25%)

**Claude Opus 4.6 최상위.**

- Chroma 2025 연구: Claude 모델이 장문에서 가장 느린 정확도 감소
- 1M MRCR v2 8-needle 테스트: Opus 4.6 = 76%, Sonnet 4.5 = 18.5%
- Gemini 2.5 Flash: needle-in-a-haystack 테스트에서 거의 완벽
- **그러나 모든 모델이 입력 길이 증가에 따른 성능 저하를 보임**

**글도비의 기존 완화 전략** (이미 학계 수준 이상):
- `WorldStateManager`: 세계 상태 SSOT → 컨텍스트 시작부 배치
- `FactLedger`: 누적 팩트 원장 → 모순 방지
- `ChainLink`: 에피소드 연결고리 → 연속성 보장
- 계층적 요약 피라미드 (에피소드 → 볼륨 → 시리즈)
- Advisory Chain 9개 병렬 검증 → 사후 검출

관련 논문 6편 (§9 심층 분석 참조):
- **DOME** (NAACL 2025): Temporal KG + 동적 계층 아웃라이닝 → 글도비의 WorldState + Blueprint 패턴과 일치
- **SCORE** (arXiv 2025): 상태 추적 + 하이브리드 검색 → 23.6% 높은 일관성, 41.8% 적은 환각 → 글도비의 FactLedger + StateTracker 패턴
- **StoryWriter** (CIKM 2025): 멀티에이전트 프레임워크 → 글도비의 Director/ChiefWriter/Validator 패턴
- **StoryBox** (arXiv 2025-2026): 하이브리드 바텀업 멀티에이전트 시뮬레이션 → 캐릭터 자율 행동 기반 창발적 플롯 (v3 방향)
- **BiT-MCTS** (arXiv 2026-03, **최신**): 테마 기반 양방향 MCTS 중국어 장편 → inference-time search로 구조적 플롯 탐색
- **Agents' Room** (2025): 서사 이론 기반 전문 에이전트 분업 → 글도비의 Analyst/Director/ChiefWriter 구조와 유사

### 3.3 비용 효율 (가중치 20%)

**250화 전체 예상 비용 (30화 arc x ~8.3 cycles)**

가정: 에피소드당 150K 캐시 컨텍스트 + 10K 신규 입력 + 8K 출력, 에피소드당 평균 3회 반복

#### 시나리오 A: Claude Opus 4.6 (창작) + Flash (검증)
| 항목 | 단가 | 에피소드당 | 250화 합계 |
|------|------|-----------|-----------|
| Opus 캐시 읽기 (150K tok x 3회) | $0.50/MTok | $0.225 | $56 |
| Opus 신규 입력 (10K tok x 3회) | $5.00/MTok | $0.150 | $38 |
| Opus 출력 (8K tok x 3회) | $25.00/MTok | $0.600 | $150 |
| Flash 검증 (20회 x 5K입력 + 1K출력) | $0.30+$2.50 | $0.080 | $20 |
| **소계 (정가)** | | **$1.06** | **$264** |
| **배치 API 50% 적용** | | **$0.53** | **$132** |

#### 시나리오 B: Gemini 2.5 Pro (창작) + Flash (검증) — 현행
| 항목 | 단가 | 에피소드당 | 250화 합계 |
|------|------|-----------|-----------|
| Pro implicit 캐시 (150K x 3회 x **6,100/5,000 보정**) | $0.125/MTok | $0.069 | $17 |
| Pro 신규 입력 (10K x 3회 x 1.22 보정) | $1.25/MTok | $0.046 | $11 |
| Pro 출력 (8K x 3회 x **1.53 보정**) | $10.00/MTok | $0.367 | $92 |
| Flash 검증 (20회) | | $0.080 | $20 |
| **소계 (정가)** | | **$0.56** | **$140** |
| **배치 API 50% 적용** | | **$0.28** | **$70** |

> **보정 설명**: Gemini의 한국어 토크나이저가 Claude 대비 ~1.53x 더 많은 토큰을 소비하므로, 표면 단가만으로는 정확한 비교 불가. 토크나이저 보정 후 실질 비용 차이는 **Opus $132 vs Pro $70** (배치 적용 시).

#### 시나리오 C: GPT-5.4 (창작) + Flash (검증)
| 항목 | 에피소드당 | 250화 (배치) |
|------|-----------|-------------|
| GPT-5.4 전체 | $0.72 | $90 |
| Flash 검증 | $0.08 | $20 |
| **합계 (배치)** | **$0.40** | **$110** |

> **비용 순위**: Gemini Pro ($70) > GPT-5.4 ($110) > Claude Opus ($132) — 차이는 $62 (전체 250화 기준).

#### 숨겨진 비용 (TF4 추가 조사)

| 항목 | Opus 4.6 | Gemini 2.5 Pro | GPT-5.4 | 비고 |
|------|----------|---------------|---------|------|
| Thinking 토큰 (avg 8K 예산) | +$50 | +$20 | +$30 | 출력 토큰 단가로 과금 |
| Thinking 토큰 (max 24K 예산) | +$150 | +$60 | +$90 | 복잡 장면 시 |
| JSON 스키마 오버헤드 | +$17 | +$7 | +$12 | 23회/에피 x 600토큰 스키마 |
| 리트라이 비용 (API 실패) | +$3-10 | +$2-5 | +$1-2 | |
| **합산 (avg thinking)** | **+$70-77** | **+$29-32** | **+$43-44** | |

#### Gemini Implicit Caching 실제 적중률 정정

> **경고**: 보고서 원본에서 "Gemini implicit caching 90% CONFIRMED"로 기재했으나, 이는 **적중 시 할인율 90%**를 의미. 실제 **캐시 적중률**은 개발자 보고(GitHub googleapis/python-genai#1880) 기준 **40-60%로 불안정**. 시스템 프롬프트 공통 접두사가 동일해도 접미사 차이 시 미적중 빈발. 보고서의 Gemini $70 추정은 ~70-80% 적중률 가정이며, 실제로는 **$39(90% 적중) ~ $101(50% 적중)** 범위.

#### TCO (Total Cost of Ownership) — 250화 기준

| 비용 항목 | Option A (Opus+Flash) | Option B (현행+ChiefWriter만) | Option C (현행 유지) |
|----------|----------------------|------------------------------|-------------------|
| **직접 API 비용 (배치, 최적 캐시)** | $133-310 | $90-120 | $39-101 |
| 숨겨진 비용 (thinking+JSON+retry) | +$70-77 | +$40-45 | +$29-32 |
| **소계: 직접 비용** | **$203-387** | **$130-165** | **$68-133** |
| 전환 작업 (1회성) | 2-4 dev-days | 0.5-1 dev-day | 0 |
| 멀티프로바이더 유지보수 (12개월) | ~30시간 | ~15시간 | 0 |
| 모니터링 구축 (1회성) | ~8시간 | ~4시간 | 기존 유지 |

> **절대 비용 차이**: 최악 케이스에서도 Option A vs C = ~$250/250화 = **$1/에피소드**. 품질 향상 대비 무의미한 차이이나, 전환 인력 비용이 더 큰 변수.

### 3.4 API 인프라 (가중치 10%)

| 항목 | Claude | Gemini | GPT | DeepSeek |
|------|--------|--------|-----|----------|
| SLA | Enterprise 가능 | Vertex AI Enterprise | Azure OpenAI 99.9% | 없음 |
| Rate Limit | **80K TPM (기본) → 400K (Tier 4)** | **4M TPM** | 800K TPM | 낮음, 혼잡 빈발 |
| 캐싱 방식 | 명시적 (cache_control) | **암묵적 (코드 변경 0)** | 자동 | 없음 |
| JSON 모드 | output_config.format | response_mime_type | Structured Outputs | 기본 JSON |
| Thinking | 미지원 (별도 설계) | ThinkingConfig 지원 | o-시리즈 별도 | R1 별도 |
| 멀티키 회전 | SDK 지원 | **현행 구현 완료** | SDK 지원 | - |

> **현행 시스템 연동 비용**: Gemini는 0 (이미 구현). Claude 전환 시 `base_agent.py` 프로바이더 교체 + 캐싱 로직 수정 필요 (1-2주가 현실적 — TF5 정정). GPT 전환 시 유사 수준.
>
> **Rate Limit 병목 경고** (TF3/TF4): Claude 기본 80K TPM은 8-9개 병렬 Advisory Chain에서 병목 가능. Gemini 4M TPM 대비 50배 제한적. Enterprise 티어 또는 AWS Bedrock 경유 필요.

### 3.5 한국어 특화 (가중치 10%)

| 항목 | Claude | Gemini | GPT | DeepSeek | Qwen |
|------|--------|--------|-----|----------|------|
| 한국어 자연스러움 | **최상** | 상 | 상 | 중상 | 중상 |
| 토크나이저 효율 | 중 (1.25 c/t) | **하** (0.82 c/t) | 중 (1.0-1.2) | **최상** (2.02) | 상 (1.5-1.8) |
| 한국어 학습 데이터 | 대규모 | 대규모 | 대규모 | 중규모 | 대규모 |
| 커뮤니티 평가 | **1위** | 2위 | 3위 | - | - |

> **한국어 전용 창작 벤치마크가 존재하지 않으므로**, 커뮤니티 합의 + 정성 평가에 의존.

#### 한국어 NLU 벤치마크 (참고 — 창작 아님)

| 벤치마크 | 최고 공개 점수 | 비고 |
|----------|-------------|------|
| **KMMLU** (0-shot) | GPT-5.1 83.65% | Claude/Gemini는 KMMLU 미공개, MMMLU로 대체 (Opus 91.1%, Gemini 3 Pro 91.8%) |
| **KMMLU-Hard** (0-shot) | GPT-5.2 74.63% | |
| **LogicKor** | 비공개 리더보드 | 42문항 논리 추론, 제출 평가 방식 |
| **HAE-RAE / KoBEST** | HyperCLOVA X SEED 시리즈 | 상용 모델 미공개 |

> 한국어 NLU 벤치마크에서는 OpenAI가 유일하게 KMMLU 점수를 공개. Claude와 Gemini는 MMMLU(다국어 집계)만 공개하여 한국어 단독 성능 비교 불가. **창작 품질과 NLU 점수의 상관관계는 미증명.**

#### 한국어 AI 소설 도구 생태계

| 플랫폼 | 기반 모델 | 비고 |
|--------|----------|------|
| AIZac 노벨 (아이작) | 미공개 (장르 특화 학습) | novel.aizac.io |
| TypeTak (타입탁) | 미공개 | 연속 쓰기, 편집, 피드백, 평가 |
| 단편.ai | 미공개 | 30초 웹소설 생성 |
| HyperCLOVA X SEED | NAVER 자체 | 32B Think까지, NAVER Cloud 전용 |

> 한국 AI 소설 플랫폼은 모두 기반 모델 미공개. 커뮤니티는 주요 API(Claude, Gemini, GPT)를 직접 사용하는 경향.

---

## 4. 모델별 탈락/선정 근거 (재감리)

### 4.1 탈락 모델

| 모델 | 탈락 사유 | 확신도 |
|------|----------|--------|
| **Llama 4 Maverick** | Mazur 5.78 (최하위), 창작 품질 부적격 | 99% |
| **DeepSeek V3.2** | 컨텍스트 164K (1M 미달), SLA 없음 (출력 65K로 정정, 그러나 컨텍스트 미달로 탈락 유지) | 99% |
| **DeepSeek R1** | 컨텍스트 64K (1M 미달), 출력 16K (65K 미달) | 99% |
| **Qwen 3.5 Plus** | Mazur 미등재 (Qwen 3 Max Preview 8.09와 별개 모델), 캐싱 미지원, 안정성 미검증 | 95% |
| **GPT-5.4-Mini/Nano** | 컨텍스트 400K/128K (1M 미달) — Mini 사양 정정: 400K/128K | 98% |
| **Claude Haiku 4.5** | 컨텍스트 200K (1M 미달), 창작 품질 중하위 | 97% |
| **Gemini 3.1 Pro Preview** | Preview 상태, 안정성 미검증, Gemini 2.5 Pro 대비 2x 비용 증가 대비 품질 향상 미미 | 90% |

### 4.2 최종 후보 3+1

| 모델 | 선정 근거 | 적합 역할 |
|------|----------|-----------|
| **Claude Opus 4.6** | 창작 #1, 장문 #1, 한국어 #1, 1M/128K | ChiefWriter, Director, ContinuityInspector |
| **Gemini 2.5 Pro** | 가성비 #1, implicit caching, 현행 시스템 | 중간 역할 (Arc/Blueprint 등) |
| **Claude Sonnet 4.6** | EQ-Bench #1, Opus 60% 비용, 1M/64K | Opus 대체 가능 (비용 절감 시) |
| **Gemini 2.5 Flash** | 최저가, 검증 전용 | 10+ 검증/Advisory 에이전트 |

---

## 5. 최종 권고: 3가지 전략 옵션

### Option A: 품질 극대화 (추천)
```yaml
# models.yaml 변경안
providers:
  anthropic: { enabled: true }
  gemini: { enabled: true }

agents:
  # 창작 핵심 — Claude Opus 4.6
  chief_writer: "claude-opus-4-6"
  director: "claude-opus-4-6"
  continuity_inspector: "claude-opus-4-6"
  analyst: "claude-opus-4-6"

  # 구조 설계 — Claude Sonnet 4.6 또는 Gemini 2.5 Pro
  four_phase_arc_generator: "claude-sonnet-4-6"
  three_phase_blueprint_generator: "claude-sonnet-4-6"
  blueprint_ensemble: "claude-sonnet-4-6"
  state_locked_arc_generator: "claude-sonnet-4-6"

  # 검증/경량 — Gemini 2.5 Flash (현행 유지)
  arc_critic: "gemini-2.5-flash"
  consensus_validator: "gemini-2.5-flash"
  unified_arc_validator: "gemini-2.5-flash"
  unified_blueprint_validator: "gemini-2.5-flash"
  # ... (나머지 flash 에이전트 동일)

fallback_chain:
  "claude-opus-4-6": "claude-sonnet-4-6"
  "claude-sonnet-4-6": "gemini-2.5-pro"
  "gemini-2.5-pro": "gemini-2.5-flash"
```
- **예상 비용**: 250화 $130-180 (배치 적용)
- **품질**: Mazur 8.53급 원고
- **전환 작업**: base_agent.py 프로바이더 분기 + Claude 캐싱 적용 (1-2주 — TF5 정정, 22개 에이전트 회귀 테스트 포함)

### Option B: 현행 유지 + 점진 전환
```yaml
# 현행 Gemini 2.5 Pro/Flash 유지
# Stage 4 ChiefWriter만 Claude Opus 4.6로 교체
agents:
  chief_writer: "claude-opus-4-6"  # 유일한 변경
  # 나머지 전부 현행 유지
```
- **예상 비용**: 250화 $90-120
- **품질**: 원고 품질만 Mazur 8.53급, 나머지 현행 8.22급
- **전환 작업**: 최소 (ChiefWriter 1개 에이전트만)

### Option C: 비용 최적화 (현행 고수)
```yaml
# 변경 없음 — Gemini 2.5 Pro + Flash
```
- **예상 비용**: 250화 $70-100
- **품질**: Mazur 8.22급 (현행)
- **전환 작업**: 0

---

## 6. 전환 시 필요한 코드 변경 사항 (Option A 기준)

### 6.1 config/models.yaml
- `anthropic.enabled: true` 활성화
- 8개 에이전트 모델명 변경 (claude-opus-4-6, claude-sonnet-4-6)
- fallback_chain 크로스 프로바이더 확장

### 6.2 base_agent.py — 프로바이더 분기
- `_build_model_stack()`: 모델명으로 프로바이더 감지 → Gemini면 `types.GenerateContentConfig`, Claude면 dict config
- `_generate_content()`: 비-Gemini 응답을 `.text` / `.candidates` 호환 래퍼로 감싸기 (이어쓰기 로직 호환)
- `_get_or_create_context_cache()`: Gemini 전용 캐싱 → 비-Gemini 모델은 스킵 (Claude는 자동 prompt caching)
- `_ask_with_cached_context()`: 비-Gemini면 `ask()` 폴백
- `_handle_api_error()` / `_attempt_backup_recovery()`: 폴백 config도 프로바이더별 분기

### 6.3 anthropic_provider.py — 프로덕션 강화
- `_normalize_messages()`: Gemini 포맷 (`parts` 키) → Claude 포맷 (`content` 키) 자동 변환
- timeout 전파 (config → SDK)
- usage 매핑: Anthropic 키 → Gemini 호환 키 (`prompt_token_count` 등) 통일

### 6.4 영향 없는 파일
- `llm_router.py`: 이미 `claude-*` → `anthropic` 프로바이더 매핑 구현 완료
- `constants.py` (AIModels): `_load_model_from_yaml()` 통해 자동 반영
- 에이전트 코드 22개: `self.ask()` 인터페이스 불변 → 수정 불필요

---

## 7. 5Pass 재감리 (Audit Trail)

### Pass 1: 데이터 수집 (3개 병렬 에이전트) — 원본
- 글도비 시스템 기술 요건 분석 (25 tool uses)
- 에피소드 생산 파이프라인 분석 (32 tool uses)
- 웹 서치 — 모델 사양/벤치마크/논문 (50 tool uses)

### Pass 2: 교차 검증 (2개 병렬 에이전트) — 원본
10개 핵심 주장에 대한 독립 검증:

| 주장 | 원본 결과 | 5Pass 재검증 |
|------|----------|-------------|
| Claude Opus 4.6 출시/가격 | **CONFIRMED** | CONFIRMED (TF1) |
| GPT-5.4 사양/가격 | **CONFIRMED** | CONFIRMED (TF1) |
| Gemini 3.1 Pro Preview | **CONFIRMED** | **UPDATED**: Mazur #8은 "Gemini 3 Pro Preview"이며 3.1이 아님 (TF1) |
| Mazur V4 점수 | **PARTIALLY** | CONFIRMED (TF1, 정밀 점수 확인: 8.533, 8.511, 8.219 등) |
| EQ-Bench CW v3 Elo | **CONFIRMED** | CONFIRMED (TF1) |
| Gemini implicit caching 90% | **CONFIRMED** | **DOWNGRADED**: 90%는 할인율이며 적중률 아님. 실제 적중률 40-60% (TF4) |
| Claude 캐싱 티어 | **CONFIRMED** | CONFIRMED (TF4) |
| GPT-5.4-Mini/Nano | **CONFIRMED** | **UPDATED**: Mini는 400K/128K (200K/100K 아님) (TF1) |
| Qwen 3.5 Plus 1M | **CONFIRMED** | **UPDATED**: Mazur 8.09는 Qwen 3 Max Preview 점수 (별개 모델) (TF1) |
| DeepSeek V3.2 가격 | **PARTIALLY** | **UPDATED**: 출력 65K(V3.2-Exp), 캐시 할인 90% 확인 (TF1) |

**5Pass 검증률: 6/10 완전 확인, 4/10 정정됨, 0/10 반박됨. 정정 사항 중 최종 결론에 영향을 주는 것 없음.**

### Pass 3: 한국어 특화 검증 — 원본 + TF2 보강
- 한국어 토크나이저 효율 비교 데이터 확보 (DeepSeek 2.02 > Qwen 1.5-1.8 > Claude 1.0-1.25 > GPT 1.0-1.2 > Gemini 0.82)
- 한국 AI 커뮤니티 의견 **심층 수집** (DC Inside aiwriter, 나무위키, Clien — §3.1 참조)
- **한국어 창작 벤치마크 부재 재확인** — KMMLU, KoBEST, CLIcK, HAE-RAE, KoBALT, LogicKor 전수 조사 결과 모두 NLU/교육 평가 (TF2)
- 한국어 웹소설 특수 요구사항 신규 조사: 경어 체계, 의성어/의태어, 번역체 문제 (TF2)
- HyperCLOVA X SEED 시리즈 조사: 한국어 네이티브이나 인프라 제한 (TF2)
- **커뮤니티 합의 분열 발견**: 물량 기준 Gemini 1위 vs 품질 기준 Claude 1위 (TF2)

### Pass 4: 다관점 검증 + Devil's Advocate (TF5, 5Pass 신규)

**3관점 반론 수행** (§8 Devil's Advocate, §9 학술 논문 참조):

| 관점 | 핵심 반론 | 반론 강도 |
|------|----------|----------|
| **관점 1: "Gemini 2.5 Pro면 충분"** | 0.31점 차이 체감 미증명, implicit caching 운영 이점, 4x 가격 우위, Gemini 3.1 Pro가 격차 축소 가능 | **STRONG** |
| **관점 2: "GPT-5.4가 다크호스"** | Mazur 8.51(5.2) → 5.4는 더 높을 가능성, Azure 99.9% SLA | **WEAK** (5.x 창작 품질 퇴보 이력 치명적) |
| **관점 3: "오픈소스가 미래"** | Qwen $0.26 vs Opus $5.00 (19x), fine-tuning 가능성 | **WEAK** (현재 품질 격차 과대, 장기 전략만 유효) |

**6대 리스크 식별**:

| 리스크 | 심각도 | 확신도 감산 | 완화책 |
|--------|--------|-----------|--------|
| 한국어 창작 벤치마크 부재 | **HIGH** | -5% | Pilot 30화 블라인드 비교 |
| Soul degradation / 1M 품질 저하 | **HIGH** | -3% | Fallback chain + 실 프롬프트 테스트 |
| Claude API 안정성 (99.4% vs Azure 99.9%) | **MEDIUM** | -1% | AWS Bedrock 경유 |
| 전환 비용 과소추정 (1-2일 → 1-2주) | **MEDIUM** | -1% | Pilot-first 접근 |
| 모델 deprecation (Anthropic 적극 퇴역) | **MEDIUM** | 0% | Provider abstraction layer |
| Anthropic 재무/가격 지속가능성 | **LOW** | 0% | $380B 밸류에이션, IPO 준비 중 |

**확신도 조정**: 96% → **86%** (합산 -10%)

### Pass 5: 조건부 권고 도출 (5Pass 최종)

원 보고서의 Opus 4.6 1위 추천은 **유지하되**, 아래 조건부 권고를 필수 전제로 부가:

1. **Pilot-First 의무화**: Option A 전면 전환 전에 ChiefWriter 1개만 Opus로 전환 → 30화 생산 → 현행 Gemini 원고와 블라인드 비교 (한국어 창작 품질 정량 검증)
2. **1M 컨텍스트 실전 테스트**: 글도비 실제 프롬프트(500K-700K 토큰)에서 Opus의 정확도/일관성 별도 측정
3. **Provider Abstraction Layer**: 전환 전에 `base_agent.py`에 프로바이더 추상화 구축 → 향후 재전환 비용 최소화
4. **GPT-5.4 Mazur 대기**: GPT-5.4가 Mazur에 등재되면 재평가 (5.2가 8.51이므로 5.4 추월 가능성 배제 불가)
5. **Gemini 3.1 Pro GA 모니터링**: 정식 출시 시 Mazur 재측정 — 8.22→8.4+ 시 전환 근거 약화
6. **Rate Limit 사전 확인**: Claude 80K TPM 기본 한도에서 Advisory Chain 8-9 병렬 가능 여부 검증

### 잔여 불확실성 (14%)
1. **(5%)** 한국어 창작 품질은 영어 벤치마크에서 추론 — 실측 필요
2. **(3%)** Claude 1M 컨텍스트에서 실전 품질 저하 보고 (GitHub #21046, #31480, #35296) — 벤치마크와 실사용 괴리
3. **(2%)** GPT-5.4 Mazur 미등재 — 5.2(8.51) 기준 5.4가 Opus 추월 가능성
4. **(2%)** Gemini 3.1 Pro Preview GA 시 품질 격차 축소 가능
5. **(1%)** Claude Rate Limit 병목 가능성 (80K TPM)
6. **(1%)** 전환 비용 과소추정 (1-2일 → 1-2주)

---

## 8. Devil's Advocate — 3관점 반론 + 리스크 분석 (TF5)

### 관점 1: "Gemini 2.5 Pro면 충분하다" (현상 유지 옹호) — **반론 강도: STRONG**

**1-1. 0.31점 차이는 체감 불가능할 수 있다**
- Mazur Writing V4에서 Opus 8.53 vs Gemini 2.5 Pro 8.22 = 3.6% 차이
- 벤치마크는 **영어 단편 스토리** 기반 — 한국어 웹소설 250화 장편과 태스크 자체가 다름
- LLM grader 간 편차 +/-0.03 존재 (보고서 자체 인정)
- 웹소설 독자는 문학 품질이 아닌 **스토리 흡입력/캐릭터 매력/전개 속도**를 평가

**1-2. Implicit Caching 운영 이점 과소평가**
- Gemini: 코드 변경 0, 자동 할인, 스토리지 비용 0, 최소 2,048 토큰부터 적용
- Claude: `cache_control` breakpoint 설정 필수, write cost 25% 추가, TTL 5분
- 22개 에이전트가 이미 Gemini 캐싱에 최적화 — 전환 비용이 "1-2일"이 아닐 수 있음

**1-3. Gemini 3.1 Pro Preview가 격차 축소 가능**
- ARC-AGI-2에서 3 Pro 대비 2배 이상 추론 성능
- 3-tier thinking system 도입
- 정식 출시 시 Gemini 2.5 Pro를 대체하면서 Mazur 8.22→8.4+ 가능성

**평가**: 가장 강력한 반론. 특히 한국어 도메인에서 0.31점 차이의 실질적 의미가 미검증이라는 점이 핵심.

### 관점 2: "GPT-5.4가 다크호스다" — **반론 강도: WEAK**

**2-1. Mazur 격차 무시 가능**
- GPT-5.2가 8.51 (Opus 대비 0.02 차이) → GPT-5.4는 "substantial upgrade"로 동등/상회 가능
- GPT-5.4 아직 Mazur V4 미등재 (3/5 출시 후 벤치마크 반영 시차)

**2-2. Azure 인프라 우위**
- Azure OpenAI 99.9% SLA vs Anthropic 99.4% (90일)
- 2026-03-02 Claude 글로벌 장애(3시간), 2026-03-18 Opus elevated errors

**2-3. 치명적 약점 — GPT-5.x 창작 품질 퇴보**
- Sam Altman 직접 인정: "I think we just screwed that up" (5.2 writing quality)
- 독립 벤치마크: GPT-5.4 creative writing **36.8%** vs GPT-4o **97.3%** (Rianna benchmark)
- ChatGPT 시장점유율 60%→45%, 150만 구독 취소 (2026-03)
- OpenAI 자체 인정: 5.2에서 writing은 후순위, intelligence/reasoning에 집중

**평가**: Azure 인프라는 강점이나, GPT-5.x의 창작 품질 퇴보 문제가 치명적. 웹소설 생산 시스템에서 이 리스크는 수용 불가.

### 관점 3: "오픈소스/셀프호스팅이 미래다" — **반론 강도: WEAK (장기적 NOTABLE)**

**3-1. 극단적 비용 우위**
- Qwen 3.5 Plus $0.26/$1.56 vs Opus $5.00/$25.00 — input 19x, output 16x 저렴
- 자체 호스팅 breakeven: 월 50M 토큰 이상 시 API 대비 경제적

**3-2. Fine-tuning 가능성**
- 한국 웹소설 전용 fine-tuning으로 도메인 특화 35% 성능 향상 가능 (일반적 수치)
- KORani(KRAFTON), KIT-19 등 한국어 특화 리소스 존재

**3-3. 치명적 약점 — 현재 품질 격차**
- Llama 4 Maverick: Mazur **최하위** 5.78 (-32%)
- DeepSeek V3.2: 7.60 (-11%), 컨텍스트 164K (1M 미달)
- 자체 호스팅: GPU 비용 2.5-3x + 연 $40K-$100K 엔지니어링 유지비

**평가**: 현재 품질 격차 과대. 그러나 2-3년 후 대비 fine-tuning 파이프라인 탐색은 전략적 가치 있음.

### "Soul Degradation" (영혼 퇴화) 실태 조사 (TF2/TF5)

**경과**:
- 2025-08 ~ 09: Claude Sonnet 4 / Haiku 3.5에서 3건의 인프라 버그 발생 (라우팅 오류, TPU 출력 손상, XLA 컴파일러 버그)
- Anthropic 공식 인정 + 수정 완료 (2025-09 중순)
- 2026-01~03: GitHub Issues #21046, #31480, #35296에서 Opus 4.5/4.6 품질 퇴화 보고 지속
- 나무위키: "프롬프트 해석 능력은 오히려 살짝 떨어짐" / "비싼 만큼의 성능은 나오지 않아"

**평가**: 벤치마크 데이터(Mazur 8.53, EQ-Bench 1932, LM Arena 1504)는 Opus 4.6이 현재 peak 품질임을 확인. 사용자 보고와 벤치마크의 괴리는 **태스크 유형 차이** (벤치마크=단편 영어 / 실사용=장문 복잡 프롬프트)로 설명 가능. 리스크로는 유효하나, 벤치마크를 뒤집을 수준은 아님.

---

## 9. 학술 논문 심층 조사 및 인프라 비교 (TF Agent 3 — 웹 리서치)

### 9.1 장편 서사 생성 학술 논문 (2024-2026)

#### 9.1.1 DOME — Dynamic Hierarchical Outlining with Memory-Enhancement (NAACL 2025)
- **출처**: [ACL Anthology](https://aclanthology.org/2025.naacl-long.63/)
- **저자**: Qianyue Wang, Jinwu Hu, Zhengping Li, Yufeng Wang, Daiyuan Li, Yu Hu, Mingkui Tan
- **핵심 기법**:
  - Dynamic Hierarchical Outline (DHO): 소설 이론 기반 아웃라인 계획과 집필 단계를 융합
  - Memory-Enhancement Module (MEM): 시간적 지식 그래프(Temporal KG) 기반으로 생성 콘텐츠를 저장/검색 → 문맥 충돌 감소
  - Temporal Conflict Analyzer: 시간적 KG를 활용해 장편 스토리의 문맥 일관성을 자동 평가
- **결과**: 유창성, 일관성, 전체 품질에서 SOTA 대비 유의미한 향상
- **글도비 연관**: WorldStateManager + Blueprint 패턴과 구조적으로 일치. 시간적 KG 기반 충돌 분석은 FactLedger 고도화 방향과 동일

#### 9.1.2 SCORE — Story Coherence and Retrieval Enhancement (arXiv 2503.23512, 2025)
- **출처**: [arXiv](https://arxiv.org/html/2503.23512v1)
- **핵심 기법**:
  - Dynamic State Tracking: 심볼릭 로직을 통한 객체/캐릭터 상태 모니터링
  - Context-Aware Summarization: 시간 진행에 따른 계층적 에피소드 요약
  - Hybrid Retrieval: TF-IDF 키워드 관련성 + 코사인 유사도 기반 시맨틱 임베딩 결합
  - Temporally-aligned RAG 파이프라인으로 문맥 일관성 검증
- **정량 결과**: NCI-2.0 일관성 23.6%↑, EASM 감정 일관성 89.7%, 환각 41.8%↓ (vs GPT baseline)
- **글도비 연관**: FactLedger + StateTracker + 계층 요약 피라미드와 거의 동일한 아키텍처. 글도비가 이미 학계 수준 이상의 구현을 보유

#### 9.1.3 StoryWriter — Multi-Agent Framework (CIKM 2025, arXiv 2506.16445)
- **출처**: [ACM DL](https://dl.acm.org/doi/10.1145/3746252.3761616) | [arXiv](https://arxiv.org/abs/2506.16445)
- **핵심 아키텍처**:
  - Outline Agent: 이벤트 기반 아웃라인 + 캐릭터/이벤트 간 관계 생성
  - Planning Agent: 이벤트 상세화 + 챕터별 인터위빙 계획
  - Writing Agent: 동적 히스토리 압축 기반 새 플롯 생성 + 반영(Reflection)
- **성과**: LongStory 데이터셋 (6,000편, 평균 8,000 단어) 생성, Llama3.1-8B/GLM4-9B 파인튜닝 모델 훈련
- **글도비 연관**: Director/ChiefWriter/Validator 3단 구조와 직접 대응. 다만 글도비는 22개 에이전트로 더 세분화된 분업 체계

#### 9.1.4 StoryBox — Hybrid Bottom-Up Multi-Agent Simulation (arXiv 2510.11618, 2025-2026)
- **출처**: [arXiv](https://arxiv.org/abs/2510.11618) | [프로젝트](https://storyboxproject.github.io/)
- **핵심 접근**: Top-down이 아닌 Bottom-up + Hybrid 생성
  - 캐릭터 에이전트가 샌드박스 환경에서 계획 실행/상호작용 → 창발적 이벤트 생성
  - 시간/의미 주석이 달린 이벤트 로그를 Storyteller Agent가 서사 챕터로 구성
- **성과**: 평균 12,000단어 스토리, 자동/인간 평가 모두 최상위
- **글도비 시사점**: 글도비의 top-down 방식(Arc→Blueprint→Manuscript)과 상호보완 가능. 캐릭터 자율 행동 → 플롯 발생은 향후 v3에서 고려할 방향

#### 9.1.5 BiT-MCTS — Theme-based Bidirectional MCTS for Chinese Fiction (arXiv 2603.14410, 2026-03)
- **출처**: [arXiv](https://arxiv.org/abs/2603.14410) — **2026년 3월 15일 게시, 최신 논문**
- **핵심 기법**: Freytag 피라미드 기반 "클라이맥스 우선, 양방향 확장" 전략
  - 테마 → 핵심 갈등/클라이맥스 생성 → 양방향 MCTS로 상승/하강 액션 탐색
  - 4단계 파이프라인: 갈등/클라이맥스 → 양방향 MCTS 탐색 → 아웃라인 정제 → 분절 소설 생성
- **의미**: 중국어 장편 소설에 MCTS 적용은 한국어 장편에도 직접 적용 가능성. 구조적 플롯 탐색을 inference-time search로 수행

#### 9.1.6 Agents' Room — Narrative Generation through Multi-step Collaboration (2025)
- **출처**: [arXiv](https://arxiv.org/abs/2410.02603) | [OpenReview](https://openreview.net/forum?id=HfWcFs7XLR)
- **핵심**: 서사 이론 기반 분업
  - Planning Agent: 캐릭터/갈등/배경/플롯 포인트 구조화 (텍스트 직접 생성 안 함)
  - Writing Agent: 실제 서사 텍스트 작성, 섹션별 전문화
  - Orchestrator: 에이전트 간 워크플로 제어, 공유 Scratchpad 기반 통신
- **데이터셋**: Tell Me A Story — 복잡한 작문 프롬프트 + 인간 작성 스토리 + 장편 서사 전용 평가 프레임워크
- **글도비 연관**: 글도비의 Analyst/Director/ChiefWriter 분업과 구조적으로 유사. Scratchpad ≈ 글도비의 WorldState + FactLedger

### 9.2 "Lost in the Middle" 후속 연구 및 Context Rot

#### 9.2.1 MIT 2025 후속 연구 — 위치 편향의 근본 원인
- **출처**: [MIT News](https://news.mit.edu/2025/unpacking-large-language-model-bias-0617) | [TechXplore](https://techxplore.com/news/2025-06-lost-middle-llm-architecture-ai.html)
- **핵심 발견**:
  - Causal masking이 위치 편향의 주요 원인 (각 토큰이 선행 토큰만 attend)
  - U자형 정확도 패턴: 시작/끝 최고, 중간 최저
  - **완화 방법**: 다른 마스킹 기법, 어텐션 메커니즘 추가 레이어 제거, 전략적 위치 인코딩
- **글도비 시사점**: WorldState를 컨텍스트 시작부에 배치하는 현행 전략이 MIT 연구 결과와 정확히 부합

#### 9.2.2 Chroma "Context Rot" 연구 (2025)
- **출처**: [Chroma Research](https://research.trychroma.com/context-rot) | [GitHub 재현 도구](https://github.com/chroma-core/context-rot)
- **테스트 대상**: 18개 프론티어 모델 (GPT-4.1, Claude Opus 4, Gemini 2.5 포함)
- **핵심 발견**:
  - **모든 모델이 모든 입력 길이 증분에서 성능 저하** — 예외 없음
  - 200K 윈도우 모델이 50K에서 이미 유의미한 저하 시작 (절벽이 아닌 연속적 감소)
  - 30%+ 정확도 하락: lost-in-the-middle 효과
  - 어텐션 희석: 100K 토큰 = 100억 개 쌍 관계 → 관련 정보 주의력 분산
  - 의미적으로 유사한 비관련 콘텐츠가 적극적으로 모델을 오도 (distractor interference)
  - **복잡한 태스크일수록 더 심각한 저하**
- **결론**: "context engineering" (입력 데이터의 신중한 큐레이션)이 단순히 더 많은 정보 제공보다 중요
- **글도비 시사점**: 계층적 요약 피라미드 + Advisory Chain의 사후 검증이 context rot 완화에 핵심. 전체 250화를 단일 컨텍스트에 넣는 것은 비효율 — 현행 아키텍처가 올바른 방향

### 9.3 멀티모델 아키텍처 패턴

#### 9.3.1 비싼 모델(창작) + 저렴한 모델(검증) 혼합 패턴
- **출처**: [Collabnix Guide](https://collabnix.com/multi-agent-and-multi-llm-architecture-complete-guide-for-2025/) | [AImultiple](https://aimultiple.com/llm-orchestration)
- **3대 아키텍처 패턴**:
  1. **Router 패턴**: 다양한 태스크 유형에 따라 최적 모델로 라우팅
  2. **Pipeline 패턴**: 순차적 처리 체인 (Arc→Blueprint→Manuscript)
  3. **Parallel 패턴**: 앙상블 스타일 추론 (Advisory Chain)
- **비용 최적화 원칙**: 모든 태스크에 최고가 모델을 쓰지 않음. 분류/요약 → 저가 모델, 복잡 추론/다단계 분석 → 프론티어 모델
- **합의 검증 패턴**: 중요 출력을 2차 LLM Validator 또는 외부 DB/API로 팩트체크 → 비결정적 오류 완화
- **글도비 적합성**: 현행 Pro+Flash 2-tier가 이미 이 패턴. Option A (Opus+Sonnet+Flash 3-tier)는 더 세분화된 적용

#### 9.3.2 크로스 프로바이더 폴백 체인
- **출처**: [Portkey](https://portkey.ai/blog/failover-routing-strategies-for-llms-in-production/) | [AWS Multi-Provider](https://builder.aws.com/content/2e0kU51KbOA2ID63FJgfpud07vz/) | [Bifrost](https://dev.to/debmckinney/llm-orchestration-with-bifrost-routing-fallbacks-and-load-balancing-in-one-layer-40p3)
- **설계 원칙**:
  - 우선순위 프로바이더 목록 + 명확한 전환 트리거 (타임아웃, 429, 5xx)
  - SLO에 맞는 타임아웃 임계값 설정 → 라우터 thrashing 방지
  - 쿨다운 + 재시도 + 지수 백오프가 공통 패턴
- **도구**: LiteLLM, Portkey AI Gateway, Bifrost — 멀티 프로바이더 레질리언스 표준화
- **학술 연구**: [Architecting Resilient LLM Agents](https://arxiv.org/pdf/2509.08646) — 계획을 "resilient decision graph"로 전환, 예측 가능한 결함에서 우아하게 복구
- **글도비 적합성**: 현행 `pro → flash` 폴백을 `opus → sonnet → pro → flash` 크로스 프로바이더 체인으로 확장 가능

#### 9.3.3 컨텍스트 캐싱 전략 비교
- **출처**: [AI Free API Guide](https://www.aifreeapi.com/en/posts/gemini-api-context-caching-reduce-cost)

| 특성 | Claude (Anthropic) | Gemini (Google) | OpenAI |
|------|-------------------|-----------------|--------|
| **방식** | 명시적 (`cache_control`) | **암묵적 (기본 활성)** + 명시적 | 자동 |
| **할인율** | 캐시 히트 시 90% 할인 | 캐시 읽기 90% 할인 | 자동 적용 |
| **TTL 제어** | 수동 설정 | 수동/자동 혼합 | 자동 |
| **저장 비용** | 없음 | 있음 (명시적 캐시) | 없음 |
| **코드 변경** | 필요 (cache_control 블록 삽입) | **불필요** (암묵적) | 불필요 |
| **최적 시나리오** | 소규모 컨텍스트 정밀 제어 | 대규모 멀티모달/긴 TTL | 32K 이하 자동화 |

- **글도비 시사점**: 현행 Gemini 암묵적 캐싱 → Claude 전환 시 `base_agent.py`에 cache_control 블록 명시적 삽입 필요. 5개 에이전트의 50K자+ 캐싱 활용 패턴을 Claude prompt caching으로 매핑해야 함

### 9.4 인프라 비교 (Claude API vs Vertex AI vs Azure OpenAI)

#### 9.4.1 Rate Limits
- **출처**: [DevTk Rate Limits 2026](https://devtk.ai/en/blog/ai-api-rate-limits-comparison-2026/)

| 프로바이더 | TPM (Tokens Per Minute) | 비고 |
|-----------|------------------------|------|
| **Gemini** | **4M TPM** | 티어 없음, 최소 지출 없음, 유료 즉시 |
| **OpenAI** | 800K TPM | 티어별 차등 |
| **Grok** | 100K TPM | |
| **Claude** | **80K TPM** (기본) → 400K (Tier 4, $400+) | **가장 제한적** |

- **글도비 영향**: 8-9개 병렬 Advisory Chain이 Claude의 80K TPM 기본 한도에서 병목 가능. Enterprise 티어 또는 AWS Bedrock 경유 필요

#### 9.4.2 SLA 및 안정성

| 프로바이더 | SLA | 보안/컴플라이언스 |
|-----------|-----|-----------------|
| **Azure OpenAI** | **99.9% 업타임** (표준 Azure 크레딧) | SOC 2, HIPAA, GDPR |
| **AWS Bedrock (Claude)** | **99.9% 업타임** | VPC 통합, SOC 2, HIPAA |
| **Vertex AI (Gemini)** | Enterprise급 | SOC 2, HIPAA, GDPR |
| **Anthropic 직접** | 명시적 SLA 제한적 | SOC 2 Type II |

#### 9.4.3 배치 API 비교

| 프로바이더 | 할인율 | 처리 시간 | 최적 배치 크기 | 비고 |
|-----------|--------|----------|--------------|------|
| **OpenAI** | 50% | 24시간 SLA | ~1,000 | 밸런스 지향 |
| **Anthropic** | 50% | 24시간 | ~5,000 (10K까지) | |
| **Gemini** | 50% | 24시간 | **10,000+** (수십만 가능) | 최대 처리량 |

- **글도비 적합성**: 250화 x 3회 반복 = 750건은 모든 프로바이더에서 단일 배치 가능. Gemini의 대규모 배치 능력은 글도비 규모에서는 차별화 아님

#### 9.4.4 구조화 출력 (JSON) 신뢰성 비교

- **벤치마크 출처**: [StructEval](https://arxiv.org/html/2505.20139v1) | [JSONSchemaBench](https://arxiv.org/abs/2501.10868) | [LLMStructBench](https://arxiv.org/html/2602.14743v1) | [Glukhov 비교](https://www.glukhov.org/llm-performance/benchmarks/structured-output-comparison-popular-llm-providers)

| 프로바이더 | 구현 방식 | 스키마 준수율 | 비고 |
|-----------|----------|-------------|------|
| **OpenAI** | `Structured Outputs` + JSON Mode 네이티브 | **최고** (constrained decoding) | 가장 성숙한 구현 |
| **Gemini** | `response_mime_type` + `response_schema` | 상 | 스키마에 엄격히 준수하는 JSON 반환 |
| **Claude** | Tool use 강제 → 인자를 타입 객체로 파싱 | 상 | 우회적 구현이나 실용적 |
| **GPT-4** | 복잡 추출 시 **11.97% 무효 응답** (LLMStructBench) | 중상 | 깊은 계층 스키마에서 오류 증가 |

- **글도비 현행**: `response_mime_type: application/json` (Gemini 방식). Claude 전환 시 Tool use 패턴으로 변경 또는 Claude의 JSON mode 활용 필요

### 9.5 장문 컨텍스트 실전 성능

#### 9.5.1 MRCR v2 8-Needle 벤치마크 결과
- **출처**: [LLM Stats Leaderboard](https://llm-stats.com/benchmarks/mrcr-v2-(8-needle)) | [Rohan Paul 분석](https://x.com/rohanpaul_ai/status/2019545018051240059)

| 모델 | 256K 토큰 | 1M 토큰 | 비고 |
|------|----------|---------|------|
| **Claude Opus 4.6** | **92-93%** | **76%** | **1M에서 압도적 1위** |
| **GPT-5.2 (xhigh)** | 63.9% | - | 256K까지만 |
| **Gemini 3 Pro** | 77.0% (128K avg) | 26.3% | 1M에서 급락 |
| **Claude Sonnet 4.5** | - | 18.5% | |

- **핵심**: 1M 토큰에서 Opus 4.6(76%)은 Gemini 3 Pro(26.3%)의 약 3배, 이전 Claude(18.5%)의 약 4배. 8개 사실을 동시에 추적하는 multi-needle 태스크에서 검증

#### 9.5.2 1M 컨텍스트 실용적 한계
- **출처**: [Claude 1M Guide](https://karozieminski.substack.com/p/claude-1-million-context-window-guide-2026)
- **비용**: 900K 토큰 세션 = 입력 토큰만 약 $4.50 (Opus 4.6). 단, 장문 프리미엄 폐지로 동일 per-token 단가
- **'Dumb Zone' 문제**: 사실은 찾지만 세션 초기에 내린 결정을 무시하는 현상 보고 (Hacker News 개발자 사례)
- **Chroma Context Rot 재확인**: 입력 길이 증가에 따른 성능 저하는 비균일하고 예측 불가능

#### 9.5.3 글도비 실전 적용 시사점
- 250화 전체를 1M 컨텍스트에 넣는 것은 **이론적으로 가능하나 실용적으로 비효율**
- 현행 계층적 요약 피라미드(에피소드→볼륨→시리즈)가 context rot 완화의 올바른 전략
- Opus 4.6의 1M/76% MRCR은 **30화 arc 수준(~150K-300K 토큰)에서 충분한 성능** 보장
- 핵심은 "더 큰 컨텍스트"가 아니라 "더 잘 큐레이션된 컨텍스트"

---

## 10. 참고 문헌

### 벤치마크
- Mazur Writing Benchmark V4: https://github.com/lechmazur/writing
- EQ-Bench Creative Writing v3: https://eqbench.com/creative_writing.html
- EQ-Bench Longform CW: https://eqbench.com/creative_writing_longform.html
- Chatbot Arena / LM Arena: https://arena.ai/leaderboard
- WritingBench (NeurIPS 2025): https://arxiv.org/abs/2503.05244
- StructEval (구조화 출력 벤치마크): https://arxiv.org/html/2505.20139v1
- JSONSchemaBench: https://arxiv.org/abs/2501.10868
- LLMStructBench: https://arxiv.org/html/2602.14743v1
- MRCR v2 8-Needle Leaderboard: https://llm-stats.com/benchmarks/mrcr-v2-(8-needle)

### 장편 서사 생성 논문
- DOME (NAACL 2025): https://aclanthology.org/2025.naacl-long.63/ — Temporal KG + 동적 계층 아웃라이닝
- SCORE (arXiv 2025): https://arxiv.org/html/2503.23512v1 — 상태 추적 + 하이브리드 검색 → 23.6% 일관성↑, 41.8% 환각↓
- StoryWriter (CIKM 2025): https://dl.acm.org/doi/10.1145/3746252.3761616 — 멀티에이전트 장편 서사 프레임워크
- StoryBox (arXiv 2025-2026): https://arxiv.org/abs/2510.11618 — 하이브리드 바텀업 멀티에이전트 시뮬레이션
- BiT-MCTS (arXiv 2026-03): https://arxiv.org/abs/2603.14410 — 테마 기반 양방향 MCTS 중국어 소설 생성
- Agents' Room (2025): https://arxiv.org/abs/2410.02603 — 서사 이론 기반 멀티스텝 협업
- Liu et al., "Lost in the Middle" (TACL 2024): https://arxiv.org/abs/2307.03172
- MIT 2025 후속 연구: https://news.mit.edu/2025/unpacking-large-language-model-bias-0617
- Chroma "Context Rot" (2025): https://research.trychroma.com/context-rot — 18개 프론티어 모델 장문 성능 저하 연구

### 인프라/아키텍처
- Portkey Failover Routing: https://portkey.ai/blog/failover-routing-strategies-for-llms-in-production/
- AWS Multi-Provider LLM Access: https://builder.aws.com/content/2e0kU51KbOA2ID63FJgfpud07vz/
- Architecting Resilient LLM Agents: https://arxiv.org/pdf/2509.08646
- Structured Output Comparison (Glukhov): https://www.glukhov.org/llm-performance/benchmarks/structured-output-comparison-popular-llm-providers
- Rate Limits 2026 비교: https://devtk.ai/en/blog/ai-api-rate-limits-comparison-2026/

### 가격/사양 공식 소스
- Claude: https://platform.claude.com/docs/en/about-claude/pricing
- Gemini: https://ai.google.dev/gemini-api/docs/pricing
- OpenAI: https://developers.openai.com/api/docs/pricing
- DeepSeek: https://api-docs.deepseek.com/quick_start/pricing
- Qwen: https://qwen.ai/apiplatform
- Azure OpenAI: https://azure.microsoft.com/en-us/pricing/details/azure-openai/

### 비교/분석
- pricepertoken.com, openrouter.ai, artificialanalysis.ai
- AI API Pricing 2026: https://intuitionlabs.ai/articles/ai-api-pricing-comparison-grok-gemini-openai-claude
- Gemini implicit caching: https://www.aifreeapi.com/en/posts/gemini-api-context-caching-reduce-cost
- Claude 1M Context Guide: https://karozieminski.substack.com/p/claude-1-million-context-window-guide-2026

### 한국어 특화
- 한국어 AI 소설 도구: AIZac 노벨 (novel.aizac.io), TypeTak (typetak.com), 단편.ai (danpyeon.ai)
- 한국어 LLM 벤치마크: KMMLU, KoBEST, CLIcK, HAE-RAE, KoBALT, LogicKor, KMMLU-Pro
- 한국어 토크나이저 비교: CJK 효율 분석 (DeepSeek 2.46x Gemini 대비)
- HyperCLOVA X SEED 모델: https://huggingface.co/naver-hyperclovax
- CLOVA Studio: https://clova.ai/en/clova-studio
- KEEwiT 한국어 글쓰기 평가: https://keewi-t.korean.ai/
- UKTA 한국어 텍스트 분석: https://arxiv.org/html/2502.09648
- HRET 한국어 LLM 평가 툴킷: https://arxiv.org/html/2503.22968
- KORani-v3-13B (KRAFTON): https://huggingface.co/KRAFTON/KORani-v3-13B

### Devil's Advocate 소스
- Claude 품질 퇴화 GitHub: #21046, #31480, #35296 (github.com/anthropics/claude-code/issues)
- Anthropic 장애 포스트모텀: https://www.anthropic.com/engineering/a-postmortem-of-three-recent-issues
- GPT-5.x 창작 퇴보: Sam Altman 인정 (TechRadar 2026), Rianna benchmark 36.8%
- Anthropic 재무: $380B 밸류에이션 (36Kr), $19B ARR (Sacra), IPO 준비 중
- Gemini implicit caching 적중률 문제: https://github.com/googleapis/python-genai/issues/1880
- LM Arena Overall Text (2026-03-05): https://arena.ai/leaderboard

### 커뮤니티 소스
- DC Inside AI소설 마이너갤러리: https://gall.dcinside.com/mgallery/board/list/?id=aiwriter
- 나무위키 Claude 문서: https://namu.wiki/w/Claude
- 한국어 의성어/의태어 연구: https://www.researchgate.net/publication/362280612
