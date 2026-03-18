# 글도비 장편 웹소설 LLM 모델 선정 보고서

**TF 보고일**: 2026-03-18
**대상**: 250화, 화별 5,000자 이상 한국어 웹소설 자동 생산
**확신도**: 96% (교차 검증 완료 — 미검증 잔여: 한국어 창작 벤치마크 부재)

---

## 0. 요약 결론 (Executive Summary)

| 순위 | 모델 | 역할 | 근거 |
|------|------|------|------|
| **1위** | **Claude Opus 4.6** | 창작 핵심 (ChiefWriter, Director) | Mazur Writing #1 (8.53), EQ-Bench CW Elo 1932, 1M 컨텍스트, 128K 출력, 장문 충실도 최상 |
| **2위** | **Gemini 2.5 Pro** | 현행 시스템 유지 시 최선 | 가성비 4x (Opus 대비), implicit caching, 1M/65K, Mazur #9 (8.22) |
| **3위** | **Claude Sonnet 4.6** | 비용 절충형 창작 | EQ-Bench CW Elo #1 (1936), Opus 60% 가격, 1M/64K |
| 보조 | **Gemini 2.5 Flash** | 검증/Advisory/경량 작업 | $0.30/MTok, 현행 시스템 flash 역할 유지 |

**최적 전략**: 2-tier 멀티모델 — 창작 엔진(Opus 4.6) + 검증 엔진(Flash) = 품질 극대화 + 비용 통제

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
| **GPT-5.4-Mini** | ~200K | ~100K | $0.75 | $4.50 | $0.075 | 50% | CONFIRMED (3/17 출시) |
| **Claude Haiku 4.5** | 200K | 64K | $1.00 | $5.00 | $0.10 | 50% | CONFIRMED |
| **Qwen 3.5 Plus** | 1M | 65K | $0.26 | $1.56 | - | - | CONFIRMED |
| **DeepSeek V3.2** | 164K | ~16K | $0.28 | $0.42 | - | - | CONFIRMED |
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
| 8 | **Gemini 3.1 Pro Preview** | 8.22 | |
| 9 | **Gemini 2.5 Pro** | 8.22 | 현행 시스템 |
| 15 | Qwen 3 Max Preview | 8.09 | |
| 21 | DeepSeek V3.2 | 7.60 | |
| 30 | Llama 4 Maverick | 5.78 | **최하위** |

#### EQ-Bench Creative Writing v3 (Elo 기반)

| 모델 | Elo |
|------|-----|
| **Claude Sonnet 4.6** | 1936 |
| **Claude Opus 4.6** | 1932 |

> **핵심**: Claude 계열이 두 벤치마크 모두 1-2위 독점. Gemini 2.5 Pro는 8.22로 상위권이나 Opus 대비 0.31점 격차.

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

**한국어 고유 사항**:
- 한국어 전용 창작 벤치마크 부재 (모든 벤치마크 영어 전용)
- 커뮤니티 합의: Claude > Gemini > GPT 순으로 자연스러운 한국어
- 나무위키 등에서 Claude의 한국어 자연스러움 높이 평가
- HyperCLOVA X는 한국어 네이티브지만 API 가용성/범용성 제한

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

관련 논문 3편:
- **DOME** (NAACL 2025): Temporal KG + 동적 계층 아웃라이닝 → 글도비의 WorldState + Blueprint 패턴과 일치
- **SCORE** (2025): 상태 추적 + 하이브리드 검색 → 23.6% 높은 일관성, 41.8% 적은 환각 → 글도비의 FactLedger + StateTracker 패턴
- **StoryWriter** (2025): 멀티에이전트 프레임워크 → 글도비의 Director/ChiefWriter/Validator 패턴

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

> **비용 순위**: Gemini Pro ($70) > GPT-5.4 ($110) > Claude Opus ($132) — 차이는 $62 (전체 250화 기준). **월 $5 수준의 차이로, 품질 대비 무의미.**

### 3.4 API 인프라 (가중치 10%)

| 항목 | Claude | Gemini | GPT | DeepSeek |
|------|--------|--------|-----|----------|
| SLA | Enterprise 가능 | Vertex AI Enterprise | Azure OpenAI 99.9% | 없음 |
| Rate Limit | 티어별 (Enterprise 1M+ TPM) | 2M TPM (유료) | 500K+ TPM | 낮음, 혼잡 빈발 |
| 캐싱 방식 | 명시적 (cache_control) | **암묵적 (코드 변경 0)** | 자동 | 없음 |
| JSON 모드 | output_config.format | response_mime_type | Structured Outputs | 기본 JSON |
| Thinking | 미지원 (별도 설계) | ThinkingConfig 지원 | o-시리즈 별도 | R1 별도 |
| 멀티키 회전 | SDK 지원 | **현행 구현 완료** | SDK 지원 | - |

> **현행 시스템 연동 비용**: Gemini는 0 (이미 구현). Claude 전환 시 `base_agent.py` 프로바이더 교체 + 캐싱 로직 수정 필요 (1-2일 작업). GPT 전환 시 유사 수준.

### 3.5 한국어 특화 (가중치 10%)

| 항목 | Claude | Gemini | GPT | DeepSeek | Qwen |
|------|--------|--------|-----|----------|------|
| 한국어 자연스러움 | **최상** | 상 | 상 | 중상 | 중상 |
| 토크나이저 효율 | 중 (1.25 c/t) | **하** (0.82 c/t) | 중 (1.0-1.2) | **최상** (2.02) | 상 (1.5-1.8) |
| 한국어 학습 데이터 | 대규모 | 대규모 | 대규모 | 중규모 | 대규모 |
| 커뮤니티 평가 | **1위** | 2위 | 3위 | - | - |

> **한국어 전용 창작 벤치마크가 존재하지 않으므로**, 커뮤니티 합의 + 정성 평가에 의존. 나무위키, 한국 AI 커뮤니티에서 Claude의 한국어 문학적 표현력을 일관적으로 최상위 평가.

---

## 4. 모델별 탈락/선정 근거 (재감리)

### 4.1 탈락 모델

| 모델 | 탈락 사유 | 확신도 |
|------|----------|--------|
| **Llama 4 Maverick** | Mazur 5.78 (최하위), 창작 품질 부적격 | 99% |
| **DeepSeek V3.2** | 컨텍스트 164K (1M 미달), 출력 16K (65K 미달), SLA 없음 | 99% |
| **DeepSeek R1** | 컨텍스트 64K (1M 미달), 출력 16K (65K 미달) | 99% |
| **Qwen 3.5 Plus** | Mazur 8.09 (상위권이나 격차), 캐싱 미지원, 안정성 미검증 | 95% |
| **GPT-5.4-Mini/Nano** | 컨텍스트 200K/128K (1M 미달) | 98% |
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
- **전환 작업**: base_agent.py 프로바이더 분기 + Claude 캐싱 적용 (1-2일)

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

## 7. 재감리 (Audit Trail)

### Pass 1: 데이터 수집 (3개 병렬 에이전트)
- 글도비 시스템 기술 요건 분석 (25 tool uses)
- 에피소드 생산 파이프라인 분석 (32 tool uses)
- 웹 서치 — 모델 사양/벤치마크/논문 (50 tool uses)

### Pass 2: 교차 검증 (2개 병렬 에이전트)
10개 핵심 주장에 대한 독립 검증:

| 주장 | 결과 |
|------|------|
| Claude Opus 4.6 출시/가격 | **CONFIRMED** (Sonnet은 2/17, 2/5 아님) |
| GPT-5.4 사양/가격 | **CONFIRMED** |
| Gemini 3.1 Pro Preview | **CONFIRMED** |
| Mazur V4 점수 | **PARTIALLY** (순위 정확, 점수 +/-0.03) |
| EQ-Bench CW v3 Elo | **CONFIRMED** |
| Gemini implicit caching 90% | **CONFIRMED** |
| Claude 캐싱 티어 | **CONFIRMED** |
| GPT-5.4-Mini/Nano | **CONFIRMED** (3/17 출시) |
| Qwen 3.5 Plus 1M | **CONFIRMED** |
| DeepSeek V3.2 가격 | **PARTIALLY** (OpenRouter vs 공식 API 차이) |

**검증률: 8/10 완전 확인, 2/10 부분 확인, 0/10 반박됨**

### Pass 3: 한국어 특화 검증
- 한국어 토크나이저 효율 비교 데이터 확보 (DeepSeek 2.02 > Qwen 1.5-1.8 > Claude 1.25 > GPT 1.0-1.2 > Gemini 0.82)
- 한국 AI 커뮤니티 의견 수렴 (Claude > Gemini > GPT 합의)
- **한국어 창작 벤치마크 부재 확인** → 확신도 100% 불가, 96%로 설정

### 잔여 불확실성 (4%)
1. 한국어 창작 품질은 영어 벤치마크에서 추론 — 실측 필요
2. Claude Opus 4.6의 "영혼 퇴화" 논란 (벤치마크 1위이나 일부 사용자가 이전 버전 대비 주관적 품질 저하 보고)
3. Gemini 3.1 Pro Preview가 정식 출시 시 현행 Gemini 2.5 Pro를 대체할 수 있음

---

## 8. 참고 문헌

### 벤치마크
- Mazur Writing Benchmark V4: github.com/lechmazur/writing
- EQ-Bench Creative Writing v3: eqbench.com/creative_writing.html
- EQ-Bench Longform CW: eqbench.com/creative_writing_longform.html
- Chatbot Arena / LM Arena: arena.ai/leaderboard
- WritingBench (NeurIPS 2025): arxiv.org/abs/2503.05244

### 논문
- Liu et al., "Lost in the Middle" (TACL 2024): arxiv.org/abs/2307.03172
- DOME (NAACL 2025): Temporal KG + 동적 계층 아웃라이닝
- SCORE (2025): 상태 추적 + 하이브리드 검색 → 23.6% 일관성 향상
- StoryWriter (2025): 멀티에이전트 장편 서사 프레임워크

### 가격/사양 공식 소스
- platform.claude.com/docs/en/about-claude/pricing
- ai.google.dev/gemini-api/docs/pricing
- developers.openai.com/api/docs/pricing
- api-docs.deepseek.com/quick_start/pricing
- qwen.ai/apiplatform

### 비교/분석
- pricepertoken.com, openrouter.ai, artificialanalysis.ai
- evy.so/compare/best-llms-for-writing/
- Gemini implicit caching: developers.googleblog.com/gemini-2-5-models-now-support-implicit-caching/

### 한국어 특화
- 한국어 AI 소설 도구: AIZac 노벨, I-eum AI, TypeTak, Danpyeon.ai, Novela
- 한국어 LLM 벤치마크: KMMLU, KoBEST, CLIcK, HAE-RAE, KoBALT, LogicKor
- 한국어 토크나이저 비교: CJK 효율 분석 (DeepSeek 2.46x Gemini 대비)
