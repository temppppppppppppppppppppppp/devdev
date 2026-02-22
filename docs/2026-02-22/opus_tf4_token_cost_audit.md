# Opus TF4: LLM Token Usage & Cost Structure Audit

> Auditor: Claude Opus 4.6
> Date: 2026-02-22
> Scope: Stage 2 / Stage 3 / Stage 4 full pipeline LLM call analysis
> Codebase: 글도비 V63+ (commit 5c762b6 이후)

---

## 1. 에피소드당 LLM 호출 횟수

### 1.1 Stage 2 (Arc 설계) -- 1 Arc 기준

| # | 호출 위치 | 에이전트 | 모델 | 비고 |
|---|----------|---------|------|------|
| 1 | Analyst.enrich_raw_block_async | Analyst | gemini-3-pro-preview | 배치 5개 병렬, Arc당 1회 |
| 2 | Analyst.stitch_joints | Analyst | gemini-3-pro-preview | 배치 내 Arc 쌍당 1회 (최대 4회/배치) |
| 3 | PreflightChecker.analyze | PreflightChecker | gemini-3-flash-preview | 이전 Arc 전체 분석, 첫 시도만 (이후 캐시) |
| 4 | ArcEnsembleGenerator._generate_single x3 | ArcEnsemble | gemini-2.5-pro | **3개 전략 병렬** (conservative/balanced/creative) |
| 5 | UnifiedArcValidator.validate (LLM 파트) | UnifiedArcValidator | gemini-2.5-flash | Python 사전검증 후 LLM 문맥 검증 1회 |
| 6 | Director.audit_strategic_plan | Director | gemini-2.5-pro | Self-Consistency 투표 시 **3회** (기본값) |
| 7 | Director.validate_entity_consistency | Director | gemini-2.5-pro | Entity Registry 있을 때 1회 |
| 8 | Director.validate_protagonist_config | Director | gemini-2.5-pro | protagonist_config 있을 때 1회 |

**Stage 2 합계 (1 Arc, 1차 시도 PASS 시):**
- 최소: **10회** (enrich 1 + preflight 1 + ensemble 3 + validator 1 + director audit 3 + entity 1)
- 재시도 시(max 5회): 최대 **~40회** (ensemble 3 + validator 1 + director 4 = 8회/attempt x 5)
- Analyst stitch: 배치당 0~4회 추가

### 1.2 Stage 3 (Blueprint 설계) -- 1 에피소드 기준

| # | 호출 위치 | 에이전트 | 모델 | 비고 |
|---|----------|---------|------|------|
| 1 | BlueprintEnsembleGenerator._generate_single x3 | BlueprintEnsemble | gemini-3-pro-preview | **3개 전략 병렬** (action/emotion/dialogue) |
| 2 | Director.check_blueprint_continuity_with_cache | Director | gemini-2.5-pro | 연속성 검사 1회 (ep > 1), 캐시 재사용 가능 |
| 3 | Director.compare_and_select_blueprint | Director | gemini-2.5-pro | 3개 후보 비교 선택 + PASS/REJECT 판정 1회 |

**Stage 3 합계 (1 에피소드, 1차 시도 PASS 시):**
- 최소: **5회** (ensemble 3 + continuity 1 + compare 1)
- 재시도 시(max 3회 = retry 0,1,2): 최대 **~15회** (ensemble 3 + continuity 1 + compare 1 = 5회/attempt x 3)
- AdversarialSelfPlay: retry >= 2 시 추가 2회 (critic + corrector)

### 1.3 Stage 4 (원고 집필) -- 1 에피소드 기준

| # | 호출 위치 | 에이전트 | 모델 | 비고 |
|---|----------|---------|------|------|
| 1 | ChiefWriter._generate_single_candidate x3 | ChiefWriter | gemini-3-pro-preview | **3개 전략 병렬** (balanced/narrative/tension) |
| 2 | ManuscriptValidator.validate_all_candidates | ManuscriptValidator | - | **Python only** (LLM 없음) |
| 3 | ConsistencyValidator.validate x3 | ConsistencyValidator | - | **Python only** (LLM 없음) |
| 4 | BlockingValidator.validate x3 | BlockingValidator | - | **Python only** (LLM 없음) |
| 5 | ContinuityValidator.validate x3 | ContinuityValidator | - | **Python only** (LLM 없음) |
| 6 | Director.check_manuscript_continuity_with_cache x3 | Director | gemini-2.5-pro | 후보별 연속성 검사 (round 0만, 캐시 가능) |
| 7 | Director.check_manuscript_history_conflicts x3 | Director | gemini-2.5-pro | 후보별 역사 충돌 검사 (V67 30화 전문) |
| 8 | Director.select_and_judge_ensemble | Director | gemini-2.5-pro | 3개 후보 선택 + PASS/REJECT 판정 **1회** |
| 9 | ChainOfVerification.verify | CoVe | gemini-2.5-pro | PASS 시 사후검증 (quick_verify 실패 시만 LLM) |
| 10 | Stage4Orchestrator._extract_chain_link | Director | gemini-2.5-pro | PASS 확정 후 연결고리 추출 1회 |
| 11 | Manager.update_state_and_lore_v20 | Manager | gemini-3-pro-preview | PASS 확정 후 서사 정산 **1회** |

**Stage 4 합계 (1 에피소드, 1차 시도 PASS 시):**
- 최소: **11~14회** (ensemble 3 + continuity 3 + history 3 + judge 1 + chain_link 1 + manager 1 = 12회)
- 재시도 시(max 5회): 최대 **~50회** (라운드당 ensemble 3 + judge 1 + continuity/history 6 = ~10회/round x 5)
- CoVe LLM: 조건부 1회 추가
- patch_with_feedback: 재시도 시 ensemble 대신 1회 호출

### 1.4 전체 에피소드 파이프라인 요약 (1화 = 1/5 Arc + Blueprint + 원고)

| Stage | 최소 호출 | 일반적 호출 | 최대 호출 (재시도 포함) |
|-------|----------|-----------|---------------------|
| Stage 2 (1 Arc / 5ep 분담) | 10 | 12~15 | 40 |
| Stage 3 | 5 | 5~8 | 15 |
| Stage 4 | 12 | 12~16 | 50 |
| **합계 (1 에피소드)** | **~27** | **~30-39** | **~105** |

---

## 2. 호출당 추정 토큰 크기

### 2.1 토큰 추정 기준
- 한글 1자 = ~2 토큰 (Gemini tokenizer 기준)
- 한글 1,000자 = ~2,000 토큰
- 영어/JSON 혼합 시 1자 = ~1.2 토큰

### 2.2 Stage 2 호출별 프롬프트 크기

| 호출 | 프롬프트 구성 | 추정 글자 수 | 추정 Input 토큰 |
|------|-------------|------------|----------------|
| Analyst.enrich_raw_block | 블록 DNA + 이전 블록 + 맥락 | ~5,000자 | ~10K |
| PreflightChecker.analyze | 이전 Arc 전체 (N개 x tactical_doc) | ~30,000자 (10 Arc) | ~60K |
| ArcEnsemble._generate_single | 제약블록 + 이전맥락 + 전략지시 + 블록DNA + Entity Registry | ~40,000자 | ~80K |
| UnifiedArcValidator.validate | Arc 데이터 + 이전 Arc 요약 + 제약 + Python 결과 | ~15,000자 | ~30K |
| Director.audit_strategic_plan (x3) | Arc 전술서 + 이전 30개 Arc 전문(V67) + Entity | ~200,000자 | **~400K** |
| Director.validate_entity | Entity Registry + 컨텐츠 5,000자 | ~8,000자 | ~16K |

**Stage 2 V67 "30화 전문" 영향:**
- Director.audit_strategic_plan이 이전 30개 Arc의 tactical_doc 전문을 전달 (L82-100, stage2_finalizer.py)
- Arc당 tactical_doc = ~5,000-15,000자, 30개 = **~150,000-450,000자 (300K-900K 토큰)**
- ContextLimits.MAX_CONTEXT_CHARS = 800,000자 상한 적용
- **Self-Consistency 3회 투표 시 이 대형 컨텍스트를 3번 반복 전송**

### 2.3 Stage 3 호출별 프롬프트 크기

| 호출 | 프롬프트 구성 | 추정 글자 수 | 추정 Input 토큰 |
|------|-------------|------------|----------------|
| BlueprintEnsemble._generate_single | Arc tactical + 이전 BP 30개 전문 + 이전 원고 30화 전문 + 제약 + HUD + Entity | ~300,000자 | **~600K** |
| Director.compare_and_select_blueprint | Arc tactical 2,000자 + 3개 BP 요약 각 1,500자 | ~7,000자 | ~14K |
| Director.check_blueprint_continuity | 이전 BP 10개 + 신규 BP | ~20,000자 | ~40K |

**Stage 3 V67 "30화 전문" 영향:**
- BlueprintEnsemble이 `prev_manuscripts_text` (이전 30화 원고 전문)과 `prev_blueprints` (이전 30개 BP 전문) 수신
- stage3_orchestrator.py L488-496: 최대 30화 원고 로드, ContextLimits.MAX_CONTEXT_CHARS (800K자) 상한
- **3개 전략에 동일 대형 컨텍스트 3번 전송**

### 2.4 Stage 4 호출별 프롬프트 크기

| 호출 | 프롬프트 구성 | 추정 글자 수 | 추정 Input 토큰 |
|------|-------------|------------|----------------|
| ChiefWriter._generate_single (x3) | common_context (Blueprint+Arc+이전원고30화+HUD+Guard+스타일+mandatory) | ~300,000자 | **~600K** |
| Director.check_manuscript_continuity (x3) | 이전 원고 10화 + 현재 후보 + story_context + memory_context | ~100,000자 | ~200K |
| Director.check_manuscript_history (x3) | 이전 30화 원고 + 현재 후보 + story_context | ~200,000자 | **~400K** |
| Director.select_and_judge_ensemble | 3개 원고 전문 + BP + 이전 원고 전문 + mandatory_context | ~300,000자 | **~600K** |
| Manager.update_state_and_lore | 원고 전문 + 현재 HUD + NPC 목록 + 활성 복선 | ~20,000자 | ~40K |
| chain_link 추출 | 원고 마지막 3,000자 + 프롬프트 | ~4,000자 | ~8K |

**Stage 4 mandatory_context 상한:**
- `_threshold("context.mandatory_context_max", 80000)` = 80,000자 상한 (stage4_orchestrator.py L432)
- 초과 시 섹션 단위 제거 (뒤에서부터)

### 2.5 V67 "30화 전문" 주입 비중 분석

| 컴포넌트 | 30화 전문 크기 (추정) | 전체 프롬프트 대비 비중 |
|---------|---------------------|---------------------|
| Stage 2 Director audit | ~300K자 (600K 토큰) | **~85-95%** |
| Stage 3 BP Ensemble | ~250K자 (500K 토큰) | **~80-90%** |
| Stage 4 CW Ensemble | ~250K자 (500K 토큰) | **~80-90%** |
| Stage 4 Director judge | ~200K자 (400K 토큰) | **~65-75%** |
| Stage 4 history check | ~200K자 (400K 토큰) | **~80-90%** |

**결론: 모든 주요 LLM 호출에서 "30화 전문" 컨텍스트가 프롬프트의 80-95%를 차지.**

---

## 3. 중복 LLM 호출 분석

### 3.1 확인된 중복 패턴

#### (A) Stage 2 Director Self-Consistency 3회 투표
- **파일**: `director_auditor.py` -> `_strategic_audit_with_self_consistency()`
- **패턴**: 동일 프롬프트 (~400K 토큰)를 3회 전송하여 투표
- **비용 영향**: x3 배 증폭, 가장 비싼 호출을 3회 반복
- **절감 기회**: Self-Consistency 비활성화 또는 투표 수 축소 (3→1, 점수 불안정 시에만 2회차 투표)

#### (B) Stage 3 Blueprint 앙상블 3회 병렬 생성
- **파일**: `blueprint_ensemble.py` -> `generate_ensemble()`
- **패턴**: 동일 대형 컨텍스트 (Arc + 30화 원고 + 30개 BP)를 3개 전략에 개별 전송
- **비용 영향**: ~600K 토큰 x 3 = ~1.8M 입력 토큰
- **절감 기회**: Context Caching 활성화 시 2/3 절감 가능

#### (C) Stage 4 ChiefWriter 앙상블 3회 병렬 생성
- **파일**: `chief_writer.py` -> `generate_ensemble()`
- **패턴**: 동일 common_context (~300K자)를 3개 전략에 개별 전송
- **절감**: Context Caching **이미 구현** (`_get_or_create_context_cache`, TTL 600초)
- **실효성**: 50K자 이상만 캐싱 (L1184 base_agent.py) -- 대부분 조건 충족
- **주의**: 캐싱 성공 시 3회 중 2회의 입력 토큰 비용 **75% 절감** (Gemini 캐시 가격 = 입력의 1/4)

#### (D) Stage 4 Director 후보별 반복 검사
- **파일**: `stage4_interview_round.py` L527-612
- **패턴**: `check_manuscript_continuity_with_cache` + `check_manuscript_history_conflicts`를 후보 3개에 대해 각각 호출
  - 연속성 검사: 동일 이전 원고 컨텍스트 + 다른 후보 원고 = 3회 LLM 호출
  - 역사 충돌: 동일 이전 30화 원고 + 다른 후보 원고 = 3회 LLM 호출
- **비용 영향**: ~200K-400K 토큰 x 후보 수 x 2 검사 = ~1.2M-2.4M 입력 토큰
- **절감 기회**: 이전 원고 부분을 캐싱하고 후보 원고만 새로 전송 (검사별 1회만 캐시 생성)

#### (E) Stage 2 Analyst.stitch_joints 배치 내 반복
- **파일**: `stage2_orchestrator.py` L321-354
- **패턴**: 인접 Arc 쌍마다 stitch 호출 (배치 5개 = 최대 4회)
- **비용 영향**: 비교적 작음 (joint_docs만 전송, ~5K 토큰/회)

### 3.2 비중복이지만 비효율적인 패턴

#### (F) 동일 이전 원고를 여러 Stage에서 독립 로드
- Stage 3에서 `get_recent_manuscripts(before_ep, limit=30)` 1회
- Stage 4 context_builder에서 동일 쿼리 1회
- Stage 4 interview_round에서 history_conflicts용으로 재파싱
- **이유**: DB 쿼리는 빠르므로 실제 비용 영향은 미미. LLM 토큰 비용이 핵심 문제

---

## 4. 캐싱 효과 분석

### 4.1 BaseAgent._context_caches (Gemini Context Caching)

**구현 위치**: `base_agent.py` L1131-1300

**동작 방식**:
1. 콘텐츠 MD5 해시 생성
2. TTL 내 동일 해시 → 기존 캐시 재사용
3. Gemini Context Caching API 호출 → 서버 캐시 생성
4. 이후 호출에서 `cached_content` 파라미터로 참조

**캐싱 조건**:
- 콘텐츠 50,000자 이상만 캐싱 (L1184: `len(content) < 50000` → 스킵)
- TTL 기본 1800초(30분), ChiefWriter는 600초(10분)

**실제 재사용 패턴**:

| 사용처 | 캐시 타입 | TTL | 재사용 시나리오 |
|--------|---------|-----|--------------|
| ChiefWriter.generate_ensemble | manuscript | 600s | 같은 에피소드 3개 전략 + 재시도 (동일 common_context) |
| Director.check_manuscript_continuity_with_cache | blueprint | 1800s | ep 변경 안 되면 재사용 |
| Director.check_manuscript_history_with_cache | manuscript | 1800s | ep 변경 안 되면 재사용 |

**ChiefWriter 캐시 효과 (가장 큰 절감)**:
- 3개 전략 병렬 생성 시 common_context (~300K자) 캐싱
- 첫 전략: full input 비용 + 캐시 생성 비용
- 2-3번째 전략: **캐시 input 비용 = 원래의 25%** (Gemini 캐시 할인)
- 재시도 시에도 동일 캐시 재사용 (TTL 10분 내)
- **절감 효과**: 3전략 기준 입력 토큰 비용 **~50% 절감**

**TTL 30분 적절성 평가**:
- Stage 2 (Arc 1개): 소요 시간 2-5분 → 10분이면 충분, 30분은 여유로움
- Stage 3 (1 에피소드): 소요 시간 1-3분 → 10분이면 충분
- Stage 4 (1 에피소드 5라운드): 소요 시간 5-15분 → 30분 적절
- **결론**: TTL 30분은 Stage 4 재시도 시나리오에 맞춰 적절. ChiefWriter의 10분도 적절.

### 4.2 Director 원고 캐시 (DirectorCachingManager)

**구현 위치**: `director_caching.py`

**동작**: Director가 이전 원고 이력을 Context Cache로 만들어 연속 검증에 재사용
- `_cached_manuscript_ep`: 마지막 캐시 생성 ep
- ep 변경 시에만 새 캐시 생성 → 같은 ep 5라운드 동안 재사용

**절감 효과**:
- Stage 4에서 Director가 select_and_judge_ensemble + continuity + history를 최대 5라운드 실행
- 이전 원고 이력 부분 (~200K자)이 캐시되면 라운드 2-5에서 **75% 입력 토큰 절감**

### 4.3 캐싱 미적용 영역 (절감 기회)

| 영역 | 현재 상태 | 캐싱 가능성 |
|------|----------|-----------|
| Stage 2 ArcEnsemble 3전략 | 캐싱 없음 | **높음** -- 동일 이전 Arc 맥락 3회 전송 |
| Stage 3 BlueprintEnsemble 3전략 | 캐싱 없음 | **높음** -- 동일 30화 원고+BP 3회 전송 |
| Stage 2 Director Self-Consistency | 캐싱 없음 | **높음** -- 동일 프롬프트 3회 전송 |
| Stage 4 Director continuity x3 후보 | 부분 캐싱 | **중간** -- 이전 원고는 캐시, 후보만 다름 |

---

## 5. 비용 절감 기회

### 5.1 모델 다운그레이드 가능 호출

현재 `config/models.yaml` 기준:

| 에이전트 | 현재 모델 | 다운그레이드 후보 | 절감 예상 | 위험도 |
|---------|---------|----------------|---------|-------|
| Analyst (enrich_raw_block) | gemini-3-pro-preview | gemini-2.5-flash | **-75%** | 중간 -- 블록 농축은 창의성 요구 적음 |
| PreflightChecker | gemini-3-flash-preview | (이미 Flash) | - | - |
| ArcEnsembleGenerator | gemini-2.5-pro | gemini-2.5-flash | **-75%** | **높음** -- 핵심 생성 품질 직결 |
| UnifiedArcValidator | gemini-2.5-flash | (이미 Flash) | - | - |
| BlueprintEnsembleGenerator | gemini-3-pro-preview | gemini-2.5-pro 또는 Flash | **-50~75%** | 높음 |
| UnifiedBlueprintValidator | gemini-2.5-flash | (이미 Flash) | - | - |
| Director (audit/compare) | gemini-2.5-pro | gemini-2.5-flash | **-75%** | **매우 높음** -- 품질 게이트키퍼 |
| Manager (정산) | gemini-3-pro-preview | gemini-2.5-flash | **-80%** | 중간 -- JSON 추출 작업, 구조화 요구 |
| StateExtractor | gemini-3-flash-preview | (이미 Flash) | - | - |
| BlockEnricher | gemini-3-flash-preview | (이미 Flash) | - | - |

**안전한 다운그레이드 추천 (품질 영향 최소)**:
1. **Manager (gemini-3-pro → gemini-2.5-flash)**: 정산은 JSON 추출 작업이므로 Flash도 충분. 절감 ~80%
2. **Analyst.enrich_raw_block (gemini-3-pro → gemini-2.5-flash)**: 블록 농축은 구조화 작업. 절감 ~75%
3. **Director Self-Consistency 투표 2-3차 (gemini-2.5-pro → gemini-2.5-flash)**: 1차만 Pro, 나머지 Flash

### 5.2 불필요한 호출 제거

| 호출 | 조건 | 절감 방법 |
|------|------|---------|
| Director Self-Consistency 3회 투표 | 매 Arc | 1차 점수가 명확하면 (>75 또는 <40) 투표 스킵 → **2회 절감/Arc** |
| Director.validate_entity_consistency | Entity Registry 있을 때 | Python 레벨에서 exact match 먼저 체크, 불일치 시에만 LLM 호출 |
| Director.check_manuscript_history x3 후보 | 매 에피소드 | Director 선택 후 당선 후보에만 history check 수행 → **2회 절감/에피소드** |
| Director.check_manuscript_continuity x3 후보 | 매 에피소드 round 0 | Director 선택 후 당선 후보에만 검사 → **2회 절감/에피소드** |

### 5.3 프롬프트 압축 기회

| 대상 | 현재 크기 | 압축 방법 | 압축 후 | 절감 |
|------|---------|---------|--------|------|
| 30화 원고 전문 | ~250K자 | 요약본 사용 (5화당 1 요약 = 6개 요약) | ~30K자 | **~88%** |
| 30개 Arc tactical_doc | ~200K자 | 최근 5개만 전문 + 나머지 요약 | ~50K자 | **~75%** |
| 30개 BP 전문 | ~150K자 | 최근 3개만 전문 + 나머지 scene_breakdown만 | ~40K자 | **~73%** |
| mandatory_context | ~80K자 | 우선순위 기반 동적 예산 배분 (이미 구현, L432) | ~50K자 | **~38%** |

**핵심 제안: "30화 전문" 전략을 "3단계 하이브리드 + SC 검색" 방식으로 전환**

| 단계 | 구간 | 방식 | 자수 (200화 시) |
|------|------|------|----------------|
| 1단계 | 최근 10화 | **원고 전문** | 50,000자 |
| 2단계 | 11~30화 전 | **화별 요약** (500자/화) | 10,000자 |
| 3단계 | 31화~ 이전 전체 | **Arc 단위 요약** (1,000자/Arc) | ~34,000자 |
| **합계** | | | **~94,000자** |

- 현재 30화 전문 대비: **-37% (200화)**, **-57% (50화)**
- SC(Smart Context Retrieval) 벡터 검색으로 31화 이전 디테일 온디맨드 정밀 검색
- 현재 30화 전문은 31화 이전 정보를 **완전히 소실**하지만, 3단계 방식은 전체 이력 커버
- 10화 전문 = 2개 Arc 분량 → 직전 Arc의 대사/묘사/감정 변화까지 정확히 참조 가능

### 5.4 구조적 절감 기회 요약

| 절감 항목 | 예상 토큰 절감 (1 에피소드 기준) | 난이도 |
|----------|-------------------------------|-------|
| Self-Consistency 조건부 스킵 | ~800K input 토큰 | 낮음 |
| 후보 선택 후 단일 후보만 검증 | ~1.2M input 토큰 | 낮음 |
| ArcEnsemble Context Caching 추가 | ~100K input 토큰 | 중간 |
| BlueprintEnsemble Context Caching 추가 | ~1M input 토큰 | 중간 |
| 30화 전문 → 3단계 하이브리드 + SC 검색 | ~1.5~3M input 토큰 | 높음 |
| Manager Flash 다운그레이드 | 가격 절감만 (토큰 불변) | 낮음 |

---

## 6. 에피소드당 총 비용 추정

### 6.1 Gemini 가격 표 (2026-02 기준, 무료 티어 제외)

| 모델 | Input ($/1M 토큰) | Output ($/1M 토큰) | Cached Input ($/1M 토큰) |
|------|-------------------|-------------------|------------------------|
| gemini-3-pro-preview | $1.25 | $10.00 | $0.3125 |
| gemini-2.5-pro | $1.25 | $10.00 | $0.3125 |
| gemini-2.5-flash | $0.15 | $0.60 | $0.0375 |
| gemini-3-flash-preview | $0.15 | $0.60 | $0.0375 |

> Note: Thinking 토큰은 별도 과금 (output 가격 적용). MAX_OUTPUT_TOKENS = 8192.

### 6.2 Stage 2 비용 추정 (1 Arc = 5 에피소드분)

| 호출 | 모델 | Input 토큰 | Output 토큰 | 비용 |
|------|------|-----------|-----------|------|
| Analyst.enrich x5 (병렬) | 3-pro | 5 x 10K = 50K | 5 x 5K = 25K | $0.31 |
| Analyst.stitch x4 | 3-pro | 4 x 10K = 40K | 4 x 3K = 12K | $0.17 |
| Preflight.analyze x1 | 3-flash | 60K | 8K | $0.014 |
| ArcEnsemble x3 | 2.5-pro | 3 x 80K = 240K | 3 x 8K = 24K | $0.54 |
| UnifiedArcValidator x1 | 2.5-flash | 30K | 5K | $0.008 |
| Director.audit x3 (SC) | 2.5-pro | 3 x 400K = **1,200K** | 3 x 8K = 24K | **$1.74** |
| Director.entity x1 | 2.5-pro | 16K | 5K | $0.07 |
| Director.protagonist x1 | 2.5-pro | 10K | 3K | $0.04 |
| **Stage 2 합계 (1 Arc)** | | **~1,646K** | **~106K** | **~$2.91** |
| **Stage 2 (1 에피소드 분담분)** | | ~329K | ~21K | **~$0.58** |

### 6.3 Stage 3 비용 추정 (1 에피소드)

| 호출 | 모델 | Input 토큰 | Output 토큰 | 비용 |
|------|------|-----------|-----------|------|
| BPEnsemble x3 | 3-pro | 3 x 600K = **1,800K** | 3 x 8K = 24K | **$2.49** |
| Director.continuity x1 | 2.5-pro | 40K | 5K | $0.10 |
| Director.compare x1 | 2.5-pro | 14K | 5K | $0.07 |
| **Stage 3 합계** | | **~1,854K** | **~34K** | **~$2.66** |

### 6.4 Stage 4 비용 추정 (1 에피소드, 1차 PASS)

| 호출 | 모델 | Input 토큰 | Output 토큰 | 비용 |
|------|------|-----------|-----------|------|
| CW.ensemble x3 (캐시 적용) | 3-pro | 600K + 2 x 150K = **900K** | 3 x 8K = 24K | **$1.17** |
| Director.continuity x3 | 2.5-pro | 3 x 200K = 600K | 3 x 5K = 15K | $0.90 |
| Director.history x3 | 2.5-pro | 3 x 400K = **1,200K** | 3 x 5K = 15K | **$1.65** |
| Director.judge x1 | 2.5-pro | 600K | 8K | $0.83 |
| CoVe (조건부) | 2.5-pro | 20K | 5K | $0.08 |
| chain_link x1 | 2.5-pro | 8K | 3K | $0.04 |
| Manager x1 | 3-pro | 40K | 8K | $0.13 |
| **Stage 4 합계 (1차 PASS)** | | **~3,368K** | **~78K** | **~$4.80** |

### 6.5 에피소드당 총 비용 요약

| Stage | 입력 토큰 | 출력 토큰 | 비용 (USD) | 비중 |
|-------|---------|---------|-----------|------|
| Stage 2 (1/5 Arc) | ~329K | ~21K | $0.58 | 7% |
| Stage 3 | ~1,854K | ~34K | $2.66 | 33% |
| Stage 4 (1차 PASS) | ~3,368K | ~78K | $4.80 | 60% |
| **총합 (1 에피소드)** | **~5,551K (~5.5M)** | **~133K** | **~$8.04** | 100% |

### 6.6 재시도 시 비용 증가

| 시나리오 | 추가 비용 (USD) | 총 비용 |
|---------|---------------|--------|
| 1차 PASS (최적) | +$0 | $8.04 |
| Stage 4 2차 PASS | +$4.80 | $12.84 |
| Stage 4 5차 PASS (최악) | +$19.20 | $27.24 |
| Stage 2 2차 PASS | +$2.33 | $10.37 |
| 전체 최악 (S2 5차 + S3 3차 + S4 5차) | +$36 | $44+ |

### 6.7 월간 비용 추정 (30화/월 연재 기준)

| 시나리오 | 1화 비용 | 30화 비용 | 연간 비용 |
|---------|---------|---------|---------|
| 최적 (1차 PASS) | $8.04 | $241 | $2,892 |
| 평균 (1.5회 PASS) | $12 | $360 | $4,320 |
| 불안정 (3회 PASS) | $20 | $600 | $7,200 |

---

## 7. 비용 절감 로드맵 (우선순위순)

### Phase A: 즉시 적용 가능 (코드 변경 최소)

| # | 조치 | 예상 절감 | 위험 |
|---|------|---------|------|
| A-1 | Manager 모델 gemini-3-pro → gemini-2.5-flash | $0.10/ep | 낮음 |
| A-2 | Director Self-Consistency: 점수 명확 시 투표 스킵 | $1.16/ep | 낮음 |
| A-3 | Director 후보별 검증 → 선택 후 단일 검증으로 변경 | $2.55/ep | 중간 |

**Phase A 총 절감: ~$3.81/ep (47% 절감)**

### Phase B: 중기 (Context Caching 확대)

| # | 조치 | 예상 절감 | 위험 |
|---|------|---------|------|
| B-1 | ArcEnsemble에 Context Caching 추가 | $0.36/ep | 낮음 |
| B-2 | BlueprintEnsemble에 Context Caching 추가 | $1.66/ep | 낮음 |
| B-3 | Director history/continuity 캐싱 강화 | $1.28/ep | 낮음 |

**Phase B 총 절감: ~$3.30/ep (추가 41% 절감)**

### Phase C: 장기 (아키텍처 변경)

| # | 조치 | 예상 절감 | 위험 |
|---|------|---------|------|
| C-1 | 30화 전문 → 3단계 하이브리드 (10화 전문 + 20화 요약 + Arc 요약) + SC 검색 연동 | $1.50~3.00/ep | 중간 |
| C-2 | 선 Python 검증 → 조건부 LLM 호출 | $1.00/ep | 중간 |

**Phase C 총 절감: ~$2.50~4.00/ep (추가 31~50% 절감, 화수에 따라 변동)**

### 전체 절감 로드맵 요약

| Phase | 적용 후 비용 | 절감율 |
|-------|------------|-------|
| 현재 | $8.04/ep | - |
| Phase A 후 | $4.23/ep | -47% |
| Phase A+B 후 | $0.93/ep | -88% |
| Phase A+B+C 후 | ~$0.50/ep | -94% |

---

## 8. 결론

### 8.1 핵심 발견

1. **비용의 80-95%가 "30화 전문" 컨텍스트 전송에 의한 입력 토큰**: V67에서 도입된 30화 원고/Arc/Blueprint 전문 주입은 모순 방지에 효과적이나 토큰 비용을 극적으로 증가시켰다.

2. **동일 컨텍스트의 반복 전송이 최대 비용 요인**: 3개 전략 병렬 생성 + 3개 후보 개별 검증 = 6~9배 중복 전송. Context Caching이 ChiefWriter에만 적용되어 있고 ArcEnsemble/BlueprintEnsemble에는 미적용.

3. **Director Self-Consistency 3회 투표가 Stage 2 비용의 60% 차지**: ~400K 토큰 프롬프트를 3번 보내는 것이 단일 Arc 비용의 핵심. 점수 명확 시 스킵 로직 부재.

4. **출력 토큰(8K 상한)보다 입력 토큰이 40배 이상**: 비용 최적화는 **입력 토큰 절감**에 집중해야 함. 모델 다운그레이드보다 프롬프트 압축/캐싱이 더 효과적.

5. **Context Caching이 가장 ROI 높은 절감 수단**: Gemini 캐시 가격은 일반 입력의 25%. 이미 ChiefWriter에 구현되어 검증됨. ArcEnsemble/BlueprintEnsemble에 동일 패턴 확장만으로 ~$3.30/ep 절감 가능.

### 8.2 코드 경로 참조 요약

| 파일 | 핵심 호출 |
|------|---------|
| `modules/core/stage2_orchestrator.py` L245 | Analyst.enrich_raw_block_async |
| `modules/core/stage2_orchestrator.py` L325 | Analyst.stitch_joints |
| `modules/core/stage2_preflight.py` | Smart Context Retrieval + preflight |
| `modules/core/stage2_finalizer.py` L82-100 | Director audit + 30 Arc 전문 전달 |
| `modules/domain/agents/four_phase_arc_generator.py` L226-330 | Phase 1-2-3 (Preflight+Ensemble+Validate) |
| `modules/domain/agents/three_phase_blueprint_generator.py` L159-449 | Phase 1-2-3 (Constraint+Ensemble+Validate) |
| `modules/domain/agents/blueprint_ensemble.py` L111-200 | 3전략 병렬 생성 |
| `modules/domain/agents/chief_writer.py` L115-350 | 3전략 병렬 생성 + Context Caching |
| `modules/core/stage4_interview_round.py` L527-612 | Director continuity + history x3 후보 |
| `modules/domain/agents/director_ensemble.py` L245-350 | select_and_judge_ensemble |
| `modules/domain/agents/director_auditor.py` L101-175 | assess_character_logic |
| `modules/domain/agents/director_continuity.py` L41-100 | validate_entity_consistency |
| `modules/core/stage4_post_processor.py` L162-207 | Manager 비동기 정산 |
| `modules/domain/agents/base_agent.py` L1131-1300 | Context Caching 인프라 |
| `config/models.yaml` | 에이전트별 모델 배정 |
