# Gemini 컨텍스트 윈도우 활용도 전수조사

> 작성일: 2026-03-09 (2차 보완: 2026-03-10)
> 상태: 조사 완료 — 구현 대기
> 모델: gemini-2.5-pro (1M 토큰 ≈ 400~500K 한국어 문자), gemini-2.5-flash (동일)
> 감사: 전수조사 3회 + 감리 3pass 완료 (오탐 7건 제거)

---

## 요약

| Stage | 추정 최대 사용량 | 모델 용량 대비 | 핵심 병목 |
|-------|-----------------|---------------|----------|
| Stage 0 | ~55K 문자 | **~5%** | 50K 하드캡, 배치당 10K, 에피소드당 6K |
| Stage 2 | ~35K 문자 | **~3%** | vol_strategy 6K, assets 6K, feedback 9K |
| Stage 3 | ~25K 문자 | **~2.5%** | arc_focus 15K, Director 비교 시 constraint 4K |
| Stage 4 CW | ~270K 문자 | **~27%** | Tier2 화별 2K, lookback_total 40K |
| Stage 4 Director | ~370K 문자 (피크) | **~37%** | 캐시 경로 시 variable만 전송 |
| Advisory 체인 | ~30-50K 문자 (전체 합) | **~5%** | 원고 3-4K, VecMemory n_results=2 |

**결론: Stage 0~3은 용량의 2~5%만 사용. Stage 4도 피크 37%로 60%+ 유휴.**

---

## 현재 설정값 (validation.yaml SSOT)

```yaml
context:
  max_context_chars: 1,000,000      # 전체 상한
  mandatory_context_max: 400,000    # CW advisory 상한
  director_mandatory_max: 400,000   # Director advisory 상한 (Python 폴백 40K이나 YAML 우선)
  lookback_excerpt_chars: 5,000     # 화별 요약 상한 (extended lookback용)
  lookback_total_chars: 40,000      # extended lookback 총량 상한
  timeline_budget: 3,000            # 타임라인 예산

smart_retrieval:
  stage2_total_budget: 50,000
  stage3_total_budget: 80,000
  stage4_total_budget: 300,000
  director_total_budget: 300,000
```

> **⚠️ 감리 교정**: `director_mandatory_max`는 YAML에서 **400,000**. Python 코드의 `_threshold(..., 40000)` 폴백은 YAML 로드 실패 시에만 적용되며, 정상 운용 시 항상 400K.

---

## Stage 0: StyleExtractor / StoryExpander / ReverseExpander

### 하드캡 절삭 지점

| # | 파일 | 라인 | 대상 | 현재 상한 | LLM 전송 여부 | 비고 |
|---|------|------|------|----------|-------------|------|
| S0-1 | style_extractor.py | L628 | front_sample_text | **50,000자** | ✅ LLM | 전반부 3배치 합산 |
| S0-2 | style_extractor.py | L629 | back_sample_text | **50,000자** | ✅ LLM | 후반부 3배치 합산 |
| S0-3 | style_extractor.py | L711 | Anti-AI sample | **8,000자** | ✅ LLM | 모범 문단 5개 or 첫 에피소드 |
| S0-4 | style_extractor.py | L875 | _sample_batches batch_size | **10,000자/배치** | 간접 | 에피소드 당 10K |
| S0-5 | style_extractor.py | L270 | MAX_ANALYSIS_CHARS | **1,000,000자** | 간접 | Python 통계 분석 범위 (적정) |
| S0-6 | reverse_expander.py | L306 | protagonist sample | **4,000자** | ✅ LLM | 에피소드 3개 합산 |
| S0-7 | reverse_expander.py | L328 | NPC sample | **5,000자** | ✅ LLM | |
| S0-8 | reverse_expander.py | L346 | world_state sample | **3,000자** | ✅ LLM | **가장 공격적 절삭** |
| S0-9 | reverse_expander.py | L368 | episode content | **6,000자** | ✅ LLM | 화별 Bible 추출 |
| S0-10 | reverse_expander.py | L371 | prev_state | **1,000자** | ✅ LLM | 이전 HUD 상태 |
| S0-11 | story_expander.py | L421 | concept | **500자** | ✅ LLM | NPC/Skeleton 생성 |
| S0-12 | story_expander.py | L306,342 | block context | **100자/블록** | ✅ LLM | Treatment 확장 |

### 컨텍스트 캐싱 상태
- **Gemini Context Caching: 미사용** (파일 기반 JSON 캐시만 사용)
- Stage 0는 1회성 실행이므로 컨텍스트 캐싱 ROI 낮음

### 개선 후보

| ID | 대상 | 현재 | 제안 | 난이도 | ROI |
|----|------|------|------|--------|-----|
| S0-A | front/back_sample_text | 50K | 100K | LOW (1줄) | MED — 더 넓은 문체 샘플링 |
| S0-B | Anti-AI sample | 8K | 20K | LOW (1줄) | MED — 더 정확한 패턴 감지 |
| S0-C | reverse: world_state | 3K | 10K | LOW (1줄) | HIGH — 세계관 추출 정밀도 ↑ |
| S0-D | reverse: episode content | 6K | 15K | LOW (1줄) | HIGH — Bible 추출 커버리지 ↑ |
| S0-E | story_expander: concept | 500 | 2K | LOW (1줄) | LOW — 컨셉은 대개 짧음 |
| S0-F | story_expander: block context | 100 | 500 | LOW (1줄) | MED — Treatment 연결성 ↑ |

---

## Stage 2: Arc 생성 / Analyst / Arc Ensemble

### 하드캡 절삭 지점

| # | 파일 | 라인 | 대상 | 현재 상한 | LLM 전송 여부 | 비고 |
|---|------|------|------|----------|-------------|------|
| S2-1 | arc_ensemble.py | L614 | vol_strategy | **6,000자** | ✅ LLM (캐시 HIT) | 권수 전략 문서 |
| S2-2 | arc_ensemble.py | L615 | assets JSON | **6,000자** | ✅ LLM (캐시 HIT) | AssetLibrary 전체 |
| S2-3 | arc_ensemble.py | L616 | feedback | **9,000자** | ✅ LLM | 이전 시도 피드백 |
| S2-4 | arc_ensemble.py | L643 | vol_strategy (폴백) | **4,000자** | ✅ LLM (캐시 MISS) | 캐시 실패 시 축소 |
| S2-5 | arc_ensemble.py | L646 | assets (폴백) | **4,000자** | ✅ LLM (캐시 MISS) | 캐시 실패 시 축소 |
| S2-6 | analyst.py | L1167 | treatment_content | **50,000자** | ✅ LLM | Treatment 전체 |
| S2-7 | director_ensemble.py | L399 | block_summary | **4,000자** | ✅ LLM | 현재 블록 요약 |
| S2-8 | director_ensemble.py | L410 | prev_arc_context | **6,000자** | ✅ LLM | 이전 Arc 컨텍스트 |
| S2-9 | director_ensemble.py | L413 | constraint_block | **4,000자** | ✅ LLM | 제약 조건 블록 |
| S2-10 | director_ensemble.py | L416 | advisory | **4,000자** | ✅ LLM | NS-3-B 등 advisory |
| S2-11 | stage2_finalizer.py | L171 | tactical_doc parsing | **2,000자** | Python | 자본 참조 스캔 범위 |

### 컨텍스트 캐싱 상태
- **Arc Ensemble**: `_get_or_create_context_cache(cache_type="arc_ensemble")` — prev_arc_context + constraint_block 캐시
- 캐시 HIT: vol_strategy 6K, assets 6K
- **캐시 MISS: 4K로 축소** — **역인센티브 (캐시 실패 시 오히려 정보 손실)**

### 개선 후보

| ID | 대상 | 현재 | 제안 | 난이도 | ROI |
|----|------|------|------|--------|-----|
| S2-A | vol_strategy | 6K/4K | **30K** | LOW (2줄) | HIGH — 전략 전체 전달 |
| S2-B | assets JSON | 6K/4K | **40K** | LOW (2줄) | HIGH — 전체 자산 가시성 |
| S2-C | feedback | 9K | **50K** | LOW (1줄) | HIGH — 시도 이력 전달 |
| S2-D | 폴백 캡 역인센티브 | 4K (캐시 MISS) | **캐시 HIT와 동일** | LOW (2줄) | HIGH — 캐시 실패 시 품질 저하 방지 |
| S2-E | block_summary | 4K | **10K** | LOW (1줄) | MED — 블록 상세 전달 |
| S2-F | prev_arc_context | 6K | **20K** | LOW (1줄) | MED — 이전 Arc 풍부화 |
| S2-G | constraint_block | 4K | **10K** | LOW (1줄) | MED — 제약 전체 전달 |
| S2-H | advisory | 4K | **10K** | LOW (1줄) | MED — NS-3-B 전체 전달 |

---

## Stage 3: Blueprint Ensemble / Validator

### 하드캡 절삭 지점

| # | 파일 | 라인 | 대상 | 현재 상한 | LLM 전송 여부 | 비고 |
|---|------|------|------|----------|-------------|------|
| S3-1 | blueprint_ensemble.py | L172 | arc_focus | **15,000자** | ✅ LLM (캐시) | 에피소드별 전술 문서 |
| S3-2 | blueprint_ensemble.py | L812 | prev_blueprints | **400,000자** | ✅ LLM (캐시) | 이전 Blueprint 전문 |
| S3-3 | blueprint_ensemble.py | L825 | prev_manuscripts | **400,000자** | ✅ LLM (캐시) | 이전 원고 전문 |
| S3-4 | director_ensemble.py | L81 | arc_tactical_ep (BP비교) | **6,000자** | ✅ LLM | 에피소드 전술 |
| S3-5 | director_ensemble.py | L390 | state_constraints | **1,000자** | ✅ LLM | 상태 제약 JSON |
| S3-6 | director_ensemble.py | L391 | joint_docs | **1,000자** | ✅ LLM | 공동 문서 |

### 컨텍스트 캐싱 상태
- **Blueprint Ensemble**: `_get_or_create_context_cache(cache_type="blueprint_ensemble")` — TTL 600초
- stable: arc_focus + constraints + prev_info + hud = ~400K+ 캐시됨
- 3개 병렬 전략 스레드가 공유 (네트워크 3× 절감)

### 개선 후보

| ID | 대상 | 현재 | 제안 | 난이도 | ROI |
|----|------|------|------|--------|-----|
| S3-A | arc_focus | 15K | **30K** | LOW (1줄) | MED — 12화 Arc 전체 커버 |
| S3-B | state_constraints (BP비교) | 1K | **5K** | LOW (1줄) | MED — 상태 JSON 전체 |
| S3-C | joint_docs (BP비교) | 1K | **5K** | LOW (1줄) | MED — 공동 문서 전체 |

---

## Stage 4: Chief Writer / Director / Advisory

### 하드캡 절삭 지점

| # | 파일 | 라인 | 대상 | 현재 상한 | LLM 전송 여부 | 비고 |
|---|------|------|------|----------|-------------|------|
| S4-1 | stage4_context_builder.py | L610 | Tier 2 화별 요약 | **2,000자 (하드코딩)** | ✅ CW/Director | EP(N-60)~(N-31) 요약 |
| S4-2 | chief_writer.py | L813 | InPlace original_ms | **150,000자** | ✅ CW | head 20K + tail 130K |
| S4-3 | director_ensemble.py | L1092 | quick_judge ms | **6,000자** | ✅ Director | 긴급 심사용 |
| S4-4 | director_ensemble.py | L1095 | quick_judge bp | **5,000자** | ✅ Director | 긴급 심사용 |
| S4-5 | validation.yaml | L79 | lookback_total_chars | **40,000자** | 간접→CW | extended lookback 총량 |
| S4-6 | validation.yaml | L78 | lookback_excerpt_chars | **5,000자** | 간접→CW | extended lookback 화별 |
| S4-7 | validation.yaml | L84 | timeline_budget | **3,000자** | 간접→Director | 타임라인 예산 |
| S4-8 | stage4_context_builder.py | L497 | 미래 BP scenario | **200자** | ✅ CW/Director | 남은 에피소드 시나리오 |
| S4-9 | stage4_context_builder.py | L520 | 다음 Arc tactical | **500자** | ✅ CW/Director | 다음 Arc 전술 스니펫 |
| S4-10 | stage4_context_builder.py | L519 | 다음 Arc beats | **6개** | ✅ CW/Director | beat_sequence 절삭 |

### Stage 4 Director 캐시 전략 (현재 구현)

```
stable_context (캐시됨, TTL=600s):
  - Blueprint 전문
  - episode_digest
  - previous_ending
  - prev_manuscripts_text (smart_truncate → 1M 상한)
  - story_context

variable_prompt (매번 전송):
  - 3개 후보 원고 (각 ~5K)
  - 전략별 메타데이터
  - mandatory_context (YAML 400K 상한, Python 폴백 40K)

→ 캐시 HIT: variable만 전송 (~100K) = 90%+ 토큰 절감
→ 캐시 MISS: full_fallback = stable + variable (~370K)
```

### 개선 후보

| ID | 대상 | 현재 | 제안 | 난이도 | ROI |
|----|------|------|------|--------|-----|
| S4-A | lookback_total_chars | 40K | **150K** | LOW (yaml 1줄) | **HIGH** — extended lookback 확장 |
| S4-B | lookback_excerpt_chars | 5K | **10K** | LOW (yaml 1줄) | MED — 화별 요약 풍부화 |
| S4-C | timeline_budget | 3K | **15K** | LOW (yaml 1줄) | MED — 장기 시간 추적 |
| S4-D | Tier 2 화별 하드코딩 | 2K | **5K** | LOW (1줄) | **HIGH** — EP31~60 요약 2.5배 |
| S4-E | quick_judge manuscript | 6K | **전체 원고** | LOW (1줄 제거) | MED — 긴급 심사 정확도 ↑ |
| S4-F | quick_judge blueprint | 5K | **전체 BP** | LOW (1줄 제거) | MED |
| S4-G | 미래 BP scenario | 200자 | **1K** | LOW (1줄) | MED — 남은 에피소드 가시성 ↑ |
| S4-H | 다음 Arc tactical | 500자 | **3K** | LOW (1줄) | MED — Arc 전환 인지 ↑ |

---

## Advisory 체인: TruthGate ~ NC-2

### 하드캡 절삭 지점

| # | 파일 | 대상 | 현재 상한 | 비고 |
|---|------|------|----------|------|
| AD-1 | truth_gate.py | manuscript | **3,000자** | 원고 극소량만 검사 |
| AD-2 | npc_drift_advisor.py | manuscript | **4,000자** | NPC 최대 5명, 속성 12개/명 |
| AD-3 | info_paradox_checker.py | manuscript | **4,000자** | 지식 총량 5,000자 |
| AD-4 | long_term_repetition_advisor.py | manuscript | **3,000자** | 20화 윈도우 |
| AD-5 | flashback_verifier.py | VecMemory | **n_results=2** | 에피소드 2개만 검색 |
| AD-6 | numeric_drift_advisor.py | metrics | MAX_ITEMS=30 | 최근 30개 지표만 |
| AD-7 | relationship_drift_advisor.py | timeline | **5,000자** | NPC 쌍 최대 20개 |

### 문제점
1. **원고 절삭 비표준화**: 3,000자 vs 4,000자 (통일 기준 없음)
2. **VecMemory n_results=2**: 플래시백 검증에 2개 에피소드만 참조 → 오탐/누락 위험
3. **Advisory 독립 호출**: 8개 advisory가 각자 VecMemory/DB 호출 → 공유 컨텍스트 없음

### 개선 후보

| ID | 대상 | 현재 | 제안 | 난이도 | ROI |
|----|------|------|------|--------|-----|
| AD-A | 원고 절삭 표준화 | 3~4K | **8K 통일** | LOW (7파일) | MED — 검사 정밀도 ↑ |
| AD-B | FlashbackVerifier VecMemory | n_results=2 | **n_results=5** | LOW (1줄) | HIGH — 회상 검증 정확도 ↑ |
| AD-C | NPC Drift 속성 수 | 12 | **20** | LOW (1줄) | LOW — 현재도 충분 |

---

## 장기 기억 개선 방안: 과거 확장

### Lookback Tier 현황 (3-Tier 하이브리드)

```
EP(N-30) ~ EP(N-1)     Tier 1: 전문 (제한 없음)        ~162K tokens
EP(N-60) ~ EP(N-31)    Tier 2: 요약 (2,000자/화)        ~72K tokens
EP(N-60) 이전           Tier 3: Arc 요약 (4,000자/Arc)   ~30K tokens
                                                        ─────────────
                                                        합계 ~264K tokens (26%)
```

### 에피소드별 메모리 윈도우

| 현재 화수 | Tier 1 (전문) | Tier 2 (요약) | Tier 3 (Arc 요약) | 세부 손실 시작 |
|----------|-------------|-------------|-----------------|-------------|
| EP 50 | EP 20~49 | (불활성) | (불필요) | 없음 (전체 커버) |
| EP 100 | EP 70~99 | EP 40~69 | Arc 1~4 (EP 1~39) | **EP 1~39: 98% 손실** |
| EP 200 | EP 170~199 | EP 140~169 | Arc 1~14 (EP 1~139) | **EP 1~139: 98% 손실** |
| EP 500 | EP 470~499 | EP 440~469 | Arc 1~30+ (EP 1~439) | **EP 1~439: 99% 손실** |

### 점진적 품질 저하 구조

```
EP1-30: 100% (전문)
EP31-60: ~13% (2K/15K 원고)  ← 핵심 병목: Tier 2 화별 2,000자 하드코딩
EP61+: ~2% (4K/Arc ≈ 20~40화 분량)
EP120+: ~0.1% (Arc 요약 + canonical facts만)
```

### DB에 존재하지만 LLM에 미전달되는 과거 데이터

| # | 데이터 | DB 위치 | 현재 LLM 전달 | 개선 가능성 |
|---|--------|---------|-------------|-----------|
| P-1 | NPC 관계 변화 이력 | npc_relationship_history | 최신 20개 엣지만 (canonical) | TOP 50 엣지 전달 → +5K |
| P-2 | NPC 속성 변화 이력 | npc_history (100건/NPC) | 현재값만 (WorldState) | 주요 10 NPC × 10 변경 → +10K |
| P-3 | 타임라인 세부 | timeline_entries | 최근 5개만 (WorldState) | 15~20개 → +2K |
| P-4 | ~~causal_graph~~ | ~~미사용~~ | ✅ **LM-post-1에서 사용 중** | (감리 교정: 이미 활용됨) |
| P-5 | ~~karma_status~~ | karma_status 테이블 | **0% (dead data)** | 유일한 미사용 테이블 |
| P-6 | ~~foreshadow seeds~~ | seeds/foreshadow 테이블 | ✅ **ForeshadowTracker 활용 중** | (감리 교정: 이미 활용됨) |
| P-7 | ~~character_voice~~ | character_voice 테이블 | ✅ **CW style_guide에 주입** | (감리 교정: 이미 활용됨) |
| P-8 | ~~knowledge_map~~ | episode_bibles 컬럼 | ✅ **InfoParadoxChecker(LM-F) 사용** | (감리 교정: 이미 활용됨) |
| P-9 | ~~satisfaction_tags~~ | episode_satisfaction_tags | ✅ **Stage 2 Analyst에 전달** | (감리 교정: 이미 활용됨) |
| P-10 | episode_pacing 지표 | episode_pacing 테이블 | 0% (Python 로깅만) | Director 피드백 참고 → +1K |

> **감리 결과**: 1차 조사에서 "미사용"으로 분류된 6건(P-4~P-9) 중 **5건이 이미 활용 중** 확인. 실제 미사용은 `karma_status`(P-5)와 `episode_pacing`(P-10) 2건만.

### 과거 확장 개선 후보

| ID | 대상 | 현재 | 제안 | 난이도 | ROI |
|----|------|------|------|--------|-----|
| LM-P1 | Tier 2 화별 요약 | 2K 하드코딩 | **5K** (validation.yaml 외부화) | LOW | **HIGH** — EP31~60 정밀도 2.5× |
| LM-P2 | Tier 3 Arc 요약 | 4K/Arc | **8K/Arc** | LOW | MED — 장기 Arc 정밀도 2× |
| LM-P3 | NPC 관계 이력 | 최신 20 엣지 | **50 엣지** (상위 변동) | LOW | MED — 관계 추적 2.5× |
| LM-P4 | NPC 속성 이력 | 현재값만 | **주요 변경 10건/NPC** | MED | MED — 성장 궤적 가시화 |
| LM-P5 | 타임라인 세부 | 최근 5건 | **15건** | LOW | MED — 시간 추적 3× |
| LM-P6 | Volume/Series 요약 | ±2 볼륨만 | **전체 볼륨** | LOW | MED — 장기 방향 인지 |
| LM-P7 | Extended Lookback | 40K 총량 | **150K 총량** | LOW (yaml) | HIGH — 10→30화 참조 |

---

## 장기 기억 개선 방안: 미래 확장

### 미래 컨텍스트 현황

| 범위 | CW 가시성 | Director 가시성 | 절삭 |
|------|----------|---------------|------|
| 현재 Arc 남은 EP | ✅ BP scenario 200자 + core_tension 80자 | ✅ 동일 | scenario 200자 제한 |
| 다음 Arc (N+1) | ✅ beats 6개 + tactical 500자 | ✅ 동일 | tactical 500자 제한 |
| Arc N+2 이후 | ❌ 미전달 | ❌ 미전달 | **완전 차단** |
| Treatment genre_ext | ✅ V74 mandatory_context 주입 | ✅ NS-2 advisory | (감리 교정: CW도 수신) |
| vol_strategy | ❌ Stage 2에만 존재 | ❌ Stage 4 미도달 | Stage 2 전용 |

### 미래 데이터 흐름

```
Treatment (Stage 0)
  ├→ genre_ext (수치 목표) → Stage 2 Arc 설계 → Stage 4 mandatory_context (V74)
  └→ block 구조/이벤트     → Stage 2 tactical_doc → Stage 4 arc_doc

Arc (Stage 2)
  ├→ tactical_doc (전략)   → Stage 4 CW/Director (전문)
  ├→ beat_sequence         → Stage 4 미래 참조 (최대 6개)
  ├→ arc_end_state         → NS-3-B 괴리 검증 (Director advisory)
  └→ 다음 Arc ↓

다음 Arc (Stage 2)
  ├→ beats[:6]            → Stage 4 미래 참조 (500자)
  └→ Arc N+2 이후         → ❌ 미전달
```

### 미래 확장 개선 후보

| ID | 대상 | 현재 | 제안 | 난이도 | ROI |
|----|------|------|------|--------|-----|
| LM-F1 | 남은 EP scenario | 200자 | **1K** | LOW (1줄) | **HIGH** — CW가 후속 EP 상세 인지 |
| LM-F2 | 다음 Arc tactical | 500자 | **3K** | LOW (1줄) | MED — Arc 전환 준비 |
| LM-F3 | 다음 Arc beats | 6개 | **전체** (대개 4~8) | LOW (1줄 제거) | LOW — 대부분 6개 이내 |
| LM-F4 | Arc N+2 가시성 | 0 | **beats + title만** | MED (5줄 추가) | MED — 장기 방향 인지 |
| LM-F5 | vol_strategy Stage4 전달 | Stage 2 전용 | **mandatory_context 주입** | MED (10줄 추가) | HIGH — CW/Director 장기 전략 인지 |

### LM-F5 상세: vol_strategy Stage 4 주입

현재 `vol_strategy`는 `arc_ensemble.py` (Stage 2)에서만 사용되며 Stage 4에 도달하지 않음.
이는 CW/Director가 "이 작품이 어디로 가고 있는지"를 모르는 근본 원인.

**구현 경로**:
1. `_prepare_stage4_session()`에서 `load_v20_anchor("vol_strategy")` 로드
2. `_SessionConfig`에 `vol_strategy: str = ""` 필드 추가
3. `_build_common_writer_kwargs()`에서 `mandatory_context`에 prepend
4. **상한**: 10K (vol_strategy 전체가 대개 3~8K)

---

## 장기 기억 개선 방안: Director 심사 강화

### Director가 현재 받는 장기 기억

| 데이터 | 경로 | 크기 | 품질 |
|--------|------|------|------|
| 최근 30화 원고 | stable_context (Tier 1) | ~162K | 100% |
| EP31~60 요약 | stable_context (Tier 2) | ~60K | 13% |
| 이전 Arc 요약 | stable_context (Tier 3) | ~30K | 2% |
| Advisory 결과 | mandatory_context | ~50-100K | 가공됨 |
| FactLedger 요약 | mandatory_context | ~25K | 요약 |
| WorldState 요약 | mandatory_context | ~50K | 요약 |
| 인과 관계 | LM-post-1 (post-select) | ~2K | 10화 윈도우 |

### Director 심사 갭

| 갭 | 원인 | 영향 | 해결 |
|----|------|------|------|
| EP31~60 세부 손실 | Tier 2 화별 2K | 중기 모순 미탐지 | LM-P1: 5K로 확대 |
| 60화+ 세부 완전 손실 | Tier 3 Arc 4K | 장기 캐릭터 성장 단절 | LM-P2: 8K로 확대 |
| NPC 성장 궤적 미가시 | 현재값만 전달 | 성격 표류 미인지 | LM-P4: 주요 변경 이력 추가 |
| 타임라인 5건 한정 | WorldState 절삭 | 시간 흐름 혼동 | LM-P5: 15건 확대 |
| Arc N+2+ 미가시 | 미구현 | 장기 복선 무시 | LM-F4: 최소 정보 전달 |
| vol_strategy 미전달 | Stage 2 전용 | 전략적 일관성 부재 | LM-F5: mandatory_context 주입 |

---

## 전체 절삭 지점 요약 (LLM 전송 대상만)

총 **41개** 하드캡 절삭 지점 발견 (장기 기억 포함).

### Tier 1: HIGH ROI (1줄 변경, 즉시 효과)

| ID | 파일 | 현재 | 제안 | 효과 |
|----|------|------|------|------|
| S2-A | arc_ensemble.py:614 | vol_strategy 6K | 30K | Arc 전략 풍부화 |
| S2-B | arc_ensemble.py:615 | assets 6K | 40K | 자산 가시성 |
| S2-C | arc_ensemble.py:616 | feedback 9K | 50K | 시도 이력 |
| S2-D | arc_ensemble.py:643,646 | 폴백 4K | 30K/40K 동일 | 캐시 실패 품질 보전 |
| S4-A | validation.yaml:79 | lookback_total 40K | 150K | extended lookback 확장 |
| S4-D | stage4_context_builder.py:610 | Tier 2 화별 2K | 5K | **EP31~60 정밀도 2.5×** |
| LM-F1 | stage4_context_builder.py:497 | 미래 BP scenario 200자 | 1K | 후속 EP 가시성 5× |

### Tier 2: MED ROI (1줄 변경, 보조 효과)

| ID | 파일 | 현재 | 제안 | 효과 |
|----|------|------|------|------|
| S0-C | reverse_expander.py:346 | world_state 3K | 10K | 세계관 추출 ↑ |
| S0-D | reverse_expander.py:368 | episode 6K | 15K | Bible 추출 ↑ |
| S3-A | blueprint_ensemble.py:172 | arc_focus 15K | 30K | 12화 Arc 커버 |
| S4-B | validation.yaml:78 | lookback_excerpt 5K | 10K | 화별 풍부화 |
| S4-C | validation.yaml:84 | timeline 3K | 15K | 시간 추적 |
| S4-E | director_ensemble.py:1092 | quick_judge ms 6K | 전체 | 긴급 심사 ↑ |
| LM-P2 | stage4_context_builder.py:657 | Tier 3 Arc 4K | 8K | 장기 Arc 정밀도 |
| LM-P5 | world_state 타임라인 | 5건 | 15건 | 시간 추적 3× |
| LM-F2 | stage4_context_builder.py:520 | 다음 Arc tactical 500자 | 3K | Arc 전환 인지 |
| AD-A | advisory 7파일 | 원고 3~4K | 8K 통일 | 검사 정밀도 ↑ |
| AD-B | flashback_verifier | n_results=2 | 5 | 회상 정확도 ↑ |

### Tier 3: MED 난이도 (구조 변경 필요)

| ID | 파일 | 현재 | 제안 | 효과 |
|----|------|------|------|------|
| LM-P3 | canonical constraints | 20 엣지 | 50 엣지 | NPC 관계 추적 ↑ |
| LM-P4 | WorldState | 현재값만 | +주요 변경 이력 | 캐릭터 성장 가시화 |
| LM-F4 | _build_future_arc_context | Arc N+1만 | Arc N+1~N+2 | 장기 복선 |
| LM-F5 | Stage 4 전달 없음 | vol_strategy | mandatory_context 주입 | 전략적 일관성 |

### Tier 4: LOW ROI (효과 미미 또는 이미 적정)

| ID | 파일 | 현재 | 비고 |
|----|------|------|------|
| S0-E | story_expander concept | 500 | 컨셉은 대개 짧음 |
| S3-2,3 | prev_bp/ms 400K | 이미 400K — 충분 |
| S0-5 | MAX_ANALYSIS_CHARS 1M | Python 통계 — 적정 |
| AD-C | NPC drift attrs 12 | 현재도 충분 |
| LM-F3 | beats 6개 | 대부분 4~8개 — 거의 무절삭 |

---

## 변경하면 안 되는 것 (안전장치)

| 항목 | 위치 | 이유 |
|------|------|------|
| max_context_chars 1M | validation.yaml:75 | Gemini API 상한 안전망 |
| mandatory_context_max 400K | validation.yaml:76 | 프롬프트 전체의 40% — 합리적 비율 |
| director_mandatory_max 400K | validation.yaml:77 | Writer와 동일 — 이미 충분 |
| InPlace 30K JSON 절단 방지 | four_phase_arc_generator | JSON 구조 손상 방지 목적 |
| smart_truncate 기본 1M | constants.py:156 | 전역 안전망 |
| prev_bp/ms 400K | blueprint_ensemble | 이미 용량의 40% — 확대 불필요 |
| 로깅/표시용 절삭 ([:50], [:100] 등) | 전역 40+ 곳 | 콘솔 출력용, LLM 미전송 |

---

## 감리 교정 기록 (3pass)

### 오탐 제거 7건

| 1차 주장 | 감리 결과 | 근거 |
|----------|----------|------|
| causal_graph 완전 미사용 | **FALSE** — LM-post-1에서 활용 | stage4_post_processor.py:963 `get_recent_causal_links()` |
| foreshadow seeds 완전 미사용 | **FALSE** — ForeshadowTracker 활용 | stage4_context_builder.py:1216, prompt_builder.py:767 |
| character_voice 미사용 | **FALSE** — CW style_guide에 주입 | stage4_orchestrator.py:1376 `get_writer_injection()` |
| knowledge_map 미검색 | **PARTIAL** — InfoParadoxChecker 사용 | info_paradox_checker.py:74 (인덱스 없으나 직접 조회) |
| satisfaction_tags LLM 미전달 | **FALSE** — Stage 2 Analyst에 전달 | blueprint_ensemble.py:534 (Stage 4에는 미전달) |
| CW가 genre_ext 미수신 | **FALSE** — V74 mandatory_context 주입 | stage4_context_builder.py:1039-1062 |
| director_mandatory_max 40K | **FALSE** — YAML 400K (Python 폴백이 40K) | validation.yaml:77 `400000` |

### 수치 교정

| 항목 | 1차 문서 | 교정 | 이유 |
|------|---------|------|------|
| S4-1 mandatory_context 상한 | 40K | **400K (YAML SSOT)** | Python _threshold 폴백 값과 혼동 |
| S4-D 제안 | "40K → 100K" | **삭제** (이미 400K) | 개선 불필요 |
| Tier 2 화별 | "lookback_excerpt_chars 5K" | **2K 하드코딩** (별도) | 5K는 extended lookback용 |

---

## 구현 계획 (제안)

### Phase A: Quick Wins — 절삭 확대 (Tier 1, ~30분)
- validation.yaml 3줄 수정 (lookback_total 150K, lookback_excerpt 10K, timeline 15K)
- arc_ensemble.py 6줄 수정 (vol_strategy 30K, assets 40K, feedback 50K, 폴백 동일)
- stage4_context_builder.py 1줄 수정 (Tier 2 화별 2K → 5K)
- stage4_context_builder.py 1줄 수정 (미래 BP scenario 200→1K)
- 테스트 실행으로 기존 3,698 passed 유지 확인

### Phase B: 과거 확장 (Tier 2, ~40분)
- stage4_context_builder.py Tier 3 Arc 요약 4K → 8K
- WorldState 타임라인 5건 → 15건
- reverse_expander.py 절삭 확대 (world_state 10K, episode 15K)
- 다음 Arc tactical 500자 → 3K

### Phase C: 미래 확장 (Tier 3, ~1시간)
- _build_future_arc_context에 Arc N+2 최소 정보 추가
- vol_strategy Stage 4 mandatory_context 주입 파이프라인
- Advisory 원고 절삭 8K 통일 + flashback n_results=5

### Phase D: Stage 3 미세 조정 (Tier 2, ~10분)
- blueprint_ensemble arc_focus 30K
- director_ensemble state_constraints/joint_docs 5K

---

## 체크리스트

### Phase A: Quick Wins
- [ ] S2-A: arc_ensemble.py L614 vol_strategy 6K → 30K
- [ ] S2-B: arc_ensemble.py L615 assets 6K → 40K
- [ ] S2-C: arc_ensemble.py L616 feedback 9K → 50K
- [ ] S2-D: arc_ensemble.py L643 vol_strategy 폴백 4K → 30K
- [ ] S2-D: arc_ensemble.py L646 assets 폴백 4K → 40K
- [ ] S4-A: validation.yaml lookback_total_chars 40K → 150K
- [ ] S4-B: validation.yaml lookback_excerpt_chars 5K → 10K
- [ ] S4-C: validation.yaml timeline_budget 3K → 15K
- [ ] S4-D: stage4_context_builder.py L610 Tier 2 화별 2K → 5K
- [ ] LM-F1: stage4_context_builder.py L497 미래 BP scenario 200자 → 1K

### Phase B: 과거 확장
- [ ] LM-P2: stage4_context_builder.py L657 Tier 3 Arc 4K → 8K
- [ ] LM-P5: WorldState 타임라인 5건 → 15건
- [ ] S0-C: reverse_expander.py world_state 3K → 10K
- [ ] S0-D: reverse_expander.py episode content 6K → 15K
- [ ] LM-F2: stage4_context_builder.py L520 다음 Arc tactical 500자 → 3K

### Phase C: 미래 확장
- [ ] LM-F4: _build_future_arc_context Arc N+2 beats+title 추가
- [ ] LM-F5: vol_strategy Stage 4 mandatory_context 주입
- [ ] AD-A: advisory 7파일 원고 절삭 → 8K 통일
- [ ] AD-B: flashback_verifier n_results 2 → 5

### Phase D: Stage 3
- [ ] S3-A: blueprint_ensemble.py arc_focus 15K → 30K
- [ ] S3-B: director_ensemble.py state_constraints 1K → 5K
- [ ] S3-C: director_ensemble.py joint_docs 1K → 5K
- [ ] 테스트: 3,698 passed 유지
