# 디테일 서브시스템 TF 통합 SSOT

> Independent Re-Audit (Codex, 2026-03-16)
>
> Status: historical research memo, not live execution SSOT.
>
> Primary caution: this document still carries unsampled items and severity rollups that were not revalidated against the later post-remediation execution closures, so it should not be used as current queue authority.
>
> Operational note: treat the per-item entries as leads for re-audit, not approved fix tickets.
>
> Confidence: 95% for memo-only use. Direct execution confidence is below 95%.

| Field | Value |
|-------|-------|
| **Baseline** | `bbb00a77` |
| **Date** | 2026-03-15 |
| **Scope** | 8개 디테일 서브시스템 딥다이브 (8,964줄) |
| **조사 방법** | Opus TF 에이전트 8개 병렬 전수 조사 — 소스 코드 직접 Read + 라인 번호 확인 |
| **총 발견** | **114건** (16 CRITICAL / 53 IMPORTANT / 45 INSIGHT) |
| **선행 조사** | fix-candidates-ssot 25건 + 거시 서브시스템 109건과 별도 |

---

## 총괄 매트릭스 (8건 × 심각도)

| TF ID | 서브시스템 | 줄수 | CRITICAL | IMPORTANT | INSIGHT | 합계 |
|-------|----------|------|----------|-----------|---------|------|
| **TF-PB** | PromptBuilder | 968 | 0 | 9 | 5 | 14 |
| **TF-SV** | ScoringValidator | 1,274 | 2 | 7 | 5 | 14 |
| **TF-ADV** | ArcDraftValidator | 905 | 3 | 7 | 4 | 14 |
| **TF-FB** | FeedbackSystem | 885 | 2 | 7 | 5 | 14 |
| **TF-DG** | DirectorGrading | 688 | 2 | 6 | 4 | 12 |
| **TF-CA** | ContinuityArc | 1,012 | 3 | 7 | 4 | 14 |
| **TF-PLV** | PreLLMValidator | 515 | 2 | 7 | 5 | 14 |
| **TF-S4CB** | Stage4ContextBuilder | 2,717 | 2 | 9 | 7 | 18 |
| **합계** | | **8,964** | **16** | **59** | **39** | **114** |

---

## 서브시스템별 요약

| TF ID | 핵심 약점 1줄 요약 |
|-------|-------------------|
| **TF-PB** | NPC 이름 substring FP, location regex 무협 전용, dead code 83줄, ep_num 무시 |
| **TF-SV** | LLM에 원고 3,000/15,000자만 전달 (80% 비가시), GENRE_WEIGHTS ±1 캡 무효화 |
| **TF-ADV** | 한국어 복합어 아이템 FP (60% 중첩 임계), 위치 연속성 직전 Arc만 검사, dead-code 마커 루프 |
| **TF-FB** | quantify_reject_feedback가 실제 점수 버리고 하드코딩 수치 사용, 40% 데드코드, 정방향/역방향 피드백 모순 |
| **TF-DG** | 부분 거부를 승인으로 마스킹, category score 이중 계산, ep_type 적응 임계값 미전달 |
| **TF-CA** | NPC 사망 상태 Arc 검증 완전 부재, LLM/JSON 실패 시 무조건 PASS (fail-open) |
| **TF-PLV** | 병렬 경로 dead REJECT 분기, em-dash 대화 미계수 (최대 감점항), 에러 핸들링 0건 |
| **TF-S4CB** | canonical facts substring 오주입, Tier 2 raw SQL 우회, 54개 silent except, 중간 섹션 절삭 |

---

## CRITICAL / P0 항목 전체 목록 (16건)

| # | ID | 서브시스템 | 위치 | 제목 | 거시 TF 연관 |
|---|-----|----------|------|------|-------------|
| 1 | TF-SV-01 | ScoringValidator | scoring_validator.py:_sanitize_manuscript | LLM이 원고 3,000자만 평가 — 80점/100점이 25-80% 비가시 데이터 기반 | 신규 |
| 2 | TF-SV-02 | ScoringValidator | scoring_validator.py:validate_v59 | GENRE_WEIGHTS ±1 캡 → 10개 장르 × 10개 항목 가중치 시스템 전체 무효화 | 신규 |
| 3 | TF-ADV-01 | ArcDraftValidator | arc_draft_validator.py:L779-843 | `_is_same_item()` 60% 중첩 임계 → "비룡검"="천잠비룡검" FP | TF-NPC regex FP 동류 |
| 4 | TF-ADV-02 | ArcDraftValidator | arc_draft_validator.py:L285-310 | 위치 연속성 `prev_arcs[-1]`만 검사 — 다중 Arc 순간이동 미감지 | 신규 |
| 5 | TF-ADV-03 | ArcDraftValidator | arc_draft_validator.py:L710-716 | `_extract_episode_sections` dead-code 마커 루프 — content 미수정 | 신규 |
| 6 | TF-FB-01 | FeedbackSystem | feedback_system.py:L110 | `quantify_reject_feedback` score_breakdown.get() 결과 버림 → 하드코딩 수치 LLM 전달 | 신규 |
| 7 | TF-FB-02 | FeedbackSystem | feedback_system.py:L110-180 | 6개 정량화 섹션 전량 fabricated (15%/35% 등 고정 비율) | 신규 |
| 8 | TF-DG-01 | DirectorGrading | director_grading.py:L686 | `on_approve_workflow` 부분 거부 → 승인 마스킹 (`len(applied)>0`이면 전체 승인) | 신규 |
| 9 | TF-DG-02 | DirectorGrading | director_grading.py:L148-155 | `_extract_category_score` commercial_appeal/emotion_arc 이중 계산 → 비균등 가중치 | TF-DE-06 score inflation 연관 |
| 10 | TF-CA-01 | ContinuityArc | continuity_arc.py (전체) | NPC 사망/생존 상태 Arc 검증 완전 부재 — 사망 NPC 재등장 미감지 | TF-CM-03 STATE_ORDER 연관 |
| 11 | TF-CA-02 | ContinuityArc | continuity_arc.py:L456-474 | LLM 실패 시 무조건 PASS — Python CRITICAL도 warning 다운그레이드 | TF-CM-01 fail-open 동일 패턴 |
| 12 | TF-CA-03 | ContinuityArc | continuity_arc.py:L384-393 | JSON 파싱 실패 시 PASS + confidence=0.0 | TF-CM-02 동일 패턴 |
| 13 | TF-PLV-01 | PreLLMValidator | validation_orchestrator.py:L1185-1188 | 병렬 경로 dead REJECT 분기 — V60.56 변경 후 미정리 | 신규 |
| 14 | TF-PLV-02 | PreLLMValidator | pre_llm_validator.py:_check_dialogue_presence | em-dash `―` 대화 미계수 — 최대 감점(+5) 항목에서 FN | 신규 |
| 15 | TF-S4CB-01 | Stage4ContextBuilder | stage4_context_builder.py:L2407/L2504 | `current_arc_no` cross-try-block NameError 위험 | 신규 |
| 16 | TF-S4CB-02 | Stage4ContextBuilder | stage4_context_builder.py:L1804-1816 | Tier 2 summary raw SQL — DBManager 우회, schema 결합, silent drop | 신규 |

---

## IMPORTANT / P1 항목 전체 목록 (53건)

### TF-PB (PromptBuilder) — 9건

| ID | 위치 | 제목 |
|----|------|------|
| TF-PB-01 | L939-943 | `extract_npc_profiles` substring 매칭 FP (짧은 이름이 다른 단어 부분문자열) |
| TF-PB-02 | L396-403 | location regex 무협 전용 — 비무협 장르 위치 데이터 누락 |
| TF-PB-03 | L691 | tactical extraction 1800자 하드 절삭 (문장 경계 무시) |
| TF-PB-04 | ~L83 | `generate_v50_writer_prompt` dead code 83줄 |
| TF-PB-05 | build_validation_context | `ep_num` 파라미터 무시 |
| TF-PB-06 | generate_cliche_avoidance_guide | `cliche_check_result` 파라미터 미사용 |
| TF-PB-07 | L629 | `str(dict)` → Python repr이 LLM 프롬프트에 포함 |
| TF-PB-08 | 전체 | 프롬프트 총 크기 관리 부재 (단일 1800자 절삭만) |
| TF-PB-09 | 전체 | item_timeline_cache eviction이 min-ep 기반 (true LRU 아님) |

### TF-SV (ScoringValidator) — 7건

| ID | 위치 | 제목 |
|----|------|------|
| TF-SV-03 | LLM fallback | 고정 중간값 fallback → 품질 문제 마스킹 |
| TF-SV-04 | _safe_score | `math.isfinite()` 미사용 → NaN/Infinity 전파 가능 |
| TF-SV-05 | 전체 | `max_score=100` 하드코딩 vs YAML 설정 불일치 |
| TF-SV-06 | 전체 | 미지 장르 → wuxia 무언 fallback (로깅 없음) |
| TF-SV-07 | sensory_balance | "시" 단일 음절 키워드 → 한국어 수천 단어 FP |
| TF-SV-08 | show_dont_tell | `pre_reject` 플래그 산출 후 미소비 |
| TF-SV-09 | guard methods | bare `except Exception: pass` 로깅 없음 |

### TF-ADV (ArcDraftValidator) — 7건

| ID | 위치 | 제목 |
|----|------|------|
| TF-ADV-04 | L312-341 | 부상 연속성 직전 Arc만 + "조식" 회복 키워드 FP |
| TF-ADV-05 | L343-380 | Grant 만료/취소 개념 부재 → 영구 누적 |
| TF-ADV-06 | Pipeline L233 | 1차 호출 시 constraint_block 미전달 |
| TF-ADV-07 | L845-868 | `_locations_compatible` 2글자 한국어 중첩 FP ("객잔", "마을") |
| TF-ADV-08 | L382-523 | tactical doc minimum 키워드만 — 반복 내용으로 통과 가능 |
| TF-ADV-09 | Pipeline L250/565 | 1차 fail-open / 2차 fail-closed 비대칭 |
| TF-ADV-10 | L757-776 | items_acquired + tactical_doc 동시 출현 시 이중 감점 (35+35=70) |

### TF-FB (FeedbackSystem) — 7건

| ID | 위치 | 제목 |
|----|------|------|
| TF-FB-03 | L794 | `classify_rejection_feedback` .lower() 결과 버림 (dormant) |
| TF-FB-04 | get_adaptive_feedback_intensity | 반환값 3개 중 `guidance`만 소비 — threshold/level 미배선 |
| TF-FB-05 | 전체 | 15개 메서드 중 6개(40%, ~350줄) dead code |
| TF-FB-06 | reverse feedback | Stage3→2 역방향 피드백 최소 3회 실패 후 발동 |
| TF-FB-07 | 전체 | 정방향/역방향 피드백 모순 가능 ("씬 단순화" vs "씬 추가") — 중재 없음 |
| TF-FB-08 | build_strong_kind_feedback | `violations[0]`만 처리 — 우선순위 정렬 없음 |
| TF-FB-12 | Stage4→3 reverse | 미지 거부 사유 시 빈 본문 생성 |

### TF-DG (DirectorGrading) — 6건

| ID | 위치 | 제목 |
|----|------|------|
| TF-DG-03 | L555-559 | `apply_adaptive_decision`이 `ep_type` 미전달 → 에피소드 유형 조정 무시 |
| TF-DG-04 | threshold calc | Arc position + ep_type 조정 이중 적용 (현재 TF-DG-03으로 dormant) |
| TF-DG-05 | on_approve_workflow | `ep_num`, `martial_manager` 파라미터 미사용 |
| TF-DG-06 | 전체 | 검증 미수행 카테고리 기본 점수 50 → 실제 점수와 구별 불가 |
| TF-DG-08 | 전체 | NaN/Infinity/음수/100초과 점수 가드 부재 |
| TF-DG-11 | apply_adaptive_decision | `CONDITIONAL_PASS` 생성해도 앙상블이 체계적으로 덮어씀 → 무효 레이어 |

### TF-CA (ContinuityArc) — 7건

| ID | 위치 | 제목 |
|----|------|------|
| TF-CA-04 | 전체 | Python 레벨 공간/시간 검증 부재 — 순간이동 미감지 |
| TF-CA-05 | L438-452 | intra-arc 자동 완화 과도 (`start_state_corrected` 거의 항상 True) |
| TF-CA-06 | _is_same_item | exact-match만 → 한국어 이름 변형 FN ("백근 대도" vs "백근도") |
| TF-CA-07 | 3개소 | 하드코딩 절삭 (50K/4K/4.5K) → 핵심 이벤트 LLM 컨텍스트 소실 |
| TF-CA-08 | L775 | intra-arc 검증 dead code, 제한적 복장 검사 |
| TF-CA-09 | 전체 | ep_start/ep_end 문자열 `"?"` 시 서식 붕괴 |
| TF-CA-10 | acquire_patterns | 한국어 조사 "을/를" 의존 → 조사 생략 표현 FN |

### TF-PLV (PreLLMValidator) — 7건

| ID | 위치 | 제목 |
|----|------|------|
| TF-PLV-03 | L222-224 | 수동 인용 카운트 dead code (count_dialogue_segments가 덮어씀) |
| TF-PLV-04 | 전체 | `[.!?]\s+` 문장 분리 → 한국어 산문 관행 불일치 |
| TF-PLV-05 | sensory check | 장르 분기 무협만 — hunter/investment/fantasy 감각 키워드 없음 |
| TF-PLV-06 | NPC fuzzy matching | 단일 문자 와일드카드 → 단어 경계 없이 조합적 FP |
| TF-PLV-07 | 전체 | 516줄 에러 핸들링 0건 — 임의 예외 시 전체 검증 파이프라인 크래시 |
| TF-PLV-08 | dialogue minimum | `len/700` 임계값 → 장편/액션/내면 묘사 씬에서 과격 |
| TF-PLV-09 | get_summary() | dead REJECT 렌더링 로직 |

### TF-S4CB (Stage4ContextBuilder) — 9건

| ID | 위치 | 제목 |
|----|------|------|
| TF-S4CB-03 | L49 | canonical facts substring 매칭 → 무관한 사실 오주입 |
| TF-S4CB-04 | _extract_npc_tokens | 한국어 조사 미분리 ("의", "이" 등 NPC 토큰에 잔류) |
| TF-S4CB-05 | 전체 | 컨텍스트 절삭 60% head / 40% tail → 중간 섹션 핵심 사실 소실 |
| TF-S4CB-06 | Continuity Packet | 7,000자 예산 → 초기 NPC 우선, 관계/수치 후순위 |
| TF-S4CB-07 | 4+ locations | WorldState/FactLedger private `_state`/`_ledger` 직접 접근 |
| TF-S4CB-08 | 전체 | 54개 silent `except Exception` → 심각 degraded context 무경보 |
| TF-S4CB-09 | Tier 2 row | dict/sqlite3.Row 가정 → tuple 시 파싱 실패 |
| TF-S4CB-10 | _mc_parts | 7+ `insert(0, ...)` → 최종 순서 비직관적/취약 |
| TF-S4CB-11 | 전체 | alive NPC summary 12개 캡 → 대규모 캐스트 정보 누락 |

---

## 크로스커팅 패턴 발견

### 패턴 1: fail-open 전염 (4건)

LLM 또는 JSON 파싱 실패 시 `PASS` 반환하는 패턴이 **3개 서브시스템에서 독립적으로 발견**:

| ID | 서브시스템 | 위치 |
|----|----------|------|
| TF-CM-01 | ContinuityManuscript | L327-355 |
| TF-CM-02 | ContinuityManuscript | L293-305 |
| TF-CA-02 | ContinuityArc | L456-474 |
| TF-CA-03 | ContinuityArc | L384-393 |

**영향**: Director fail-closed 정책과 체계적 모순. 네트워크 불안정 시 모든 연속성 검증이 자동 통과.

### 패턴 2: 한국어 형태소 취약성 (6건)

한국어 부분문자열/조사/복합어 매칭에서 FP/FN 발생:

| ID | 서브시스템 | 구체적 문제 |
|----|----------|-----------|
| TF-NPC-05 | NPC Tracker | `[가-힣]{2,10}` 일반 명사 매칭 |
| TF-ADV-01 | ArcDraftValidator | 60% 중첩 → "비룡검"="천잠비룡검" |
| TF-ADV-07 | ArcDraftValidator | 2글자 위치명 중첩 ("객잔") |
| TF-CA-06 | ContinuityArc | exact-match만 → 이름 변형 FN |
| TF-CA-10 | ContinuityArc | 조사 의존 acquire_patterns |
| TF-S4CB-04 | ContextBuilder | NPC 토큰에 조사 잔류 |

### 패턴 3: LLM 입력 절삭/왜곡 (5건)

LLM에 전달되는 컨텍스트가 절삭/왜곡되어 판단 품질 저하:

| ID | 서브시스템 | 구체적 문제 |
|----|----------|-----------|
| TF-SV-01 | ScoringValidator | 원고 3,000/15,000자만 전달 |
| TF-S4CB-05 | ContextBuilder | 60/40 head-tail 절삭 → 중간 소실 |
| TF-S4CB-06 | ContextBuilder | 7,000자 예산 초기 NPC 편향 |
| TF-CA-07 | ContinuityArc | 50K/4K/4.5K 하드 절삭 |
| TF-PB-03 | PromptBuilder | 1,800자 문장 경계 무시 절삭 |

### 패턴 4: Dead Code / Dormant Code 누적 (5건)

| ID | 서브시스템 | 규모 |
|----|----------|------|
| TF-FB-05 | FeedbackSystem | 6/15 메서드 (40%, ~350줄) |
| TF-PB-04 | PromptBuilder | 83줄 |
| TF-PLV-01 | PreLLMValidator | 병렬 경로 REJECT 분기 |
| TF-PLV-03 | PreLLMValidator | 수동 인용 카운트 |
| TF-ADV-03 | ArcDraftValidator | 마커 루프 |

### 패턴 5: 무효 레이어 (3건)

설계상 존재하지만 실질적으로 효과가 없는 코드 경로:

| ID | 서브시스템 | 구체적 문제 |
|----|----------|-----------|
| TF-SV-02 | ScoringValidator | GENRE_WEIGHTS ±1 캡 → 가중치 시스템 전체 무효 |
| TF-DG-11 | DirectorGrading | CONDITIONAL_PASS → 앙상블이 체계적 덮어씀 |
| TF-FB-04 | FeedbackSystem | adaptive intensity 반환값 3개 중 1개만 소비 |

---

## 전체 조사 누적 건강도 (3회차 통합)

| 조사 회차 | CRITICAL | IMPORTANT | INSIGHT | 합계 |
|----------|----------|-----------|---------|------|
| fix-candidates-ssot | 4 | 10 | 11 | 25 |
| 거시 서브시스템 deepdive | 19 | 52 | 38 | 109 |
| **디테일 서브시스템 deepdive** | **16** | **53** | **45** | **114** |
| **전체 누적** | **39** | **115** | **94** | **248** |

---

## 위험도 Top 10 (디테일 한정)

| 순위 | ID | 제목 | 근거 |
|------|-----|------|------|
| 1 | TF-SV-01 | LLM 원고 3,000자 제한 | 80점 배점의 평가가 25-80% 비가시 데이터 기반 |
| 2 | TF-FB-01/02 | 피드백 정량화 fabricated | 재시도마다 LLM이 허위 수치 기반으로 수정 시도 |
| 3 | TF-CA-01 | NPC 사망 Arc 검증 부재 | 사망 NPC가 새 Arc에 등장해도 미감지 |
| 4 | TF-DG-01 | 부분 거부 → 승인 마스킹 | 위험한 state_update가 1개 유효 항목과 함께 자동 승인 |
| 5 | TF-ADV-01 | 한국어 아이템 FP | 다른 아이템을 동일 아이템으로 오판 → 중복 경고 노이즈 |
| 6 | TF-SV-02 | GENRE_WEIGHTS 무효화 | 10개 장르 가중치 시스템 전체가 ±1점 영향만 |
| 7 | TF-DG-02 | 카테고리 점수 이중 계산 | commercial_appeal/emotion_arc 2배 반영 → 비공개 편향 |
| 8 | TF-S4CB-08 | 54개 silent except | 컨텍스트 심각 degradation 무경보 |
| 9 | TF-PLV-02 | em-dash 대화 미계수 | 최대 감점 항목에서 한국 소설 주요 대화 형식 FN |
| 10 | TF-CA-02 | LLM 실패 시 무조건 PASS | fail-open 전염 패턴의 Arc 레벨 인스턴스 |

---

## 개별 TF 문서 인덱스

| 파일명 | 항목 수 |
|--------|--------|
| [tf-pb-prompt-builder-deepdive.md](tf-pb-prompt-builder-deepdive.md) | 14 (0C/9I/5S) |
| [tf-sv-scoring-validator-deepdive.md](tf-sv-scoring-validator-deepdive.md) | 14 (2C/7I/5S) |
| [tf-adv-arc-draft-validator-deepdive.md](tf-adv-arc-draft-validator-deepdive.md) | 14 (3C/7I/4S) |
| [tf-fb-feedback-system-deepdive.md](tf-fb-feedback-system-deepdive.md) | 14 (2C/7I/5S) |
| [tf-dg-director-grading-deepdive.md](tf-dg-director-grading-deepdive.md) | 12 (2C/6I/4S) |
| [tf-ca-continuity-arc-deepdive.md](tf-ca-continuity-arc-deepdive.md) | 14 (3C/7I/4S) |
| [tf-plv-pre-llm-validator-deepdive.md](tf-plv-pre-llm-validator-deepdive.md) | 14 (2C/7I/5S) |
| [tf-s4cb-stage4-context-builder-deepdive.md](tf-s4cb-stage4-context-builder-deepdive.md) | 18 (2C/9I/7S) |

---

---

## [3PA] 3-Pass Audit 감리 결과 (2026-03-16)

### CRITICAL 항목 감리 (16건 → 9건 생존)

| ID | 판정 | 확신도 | 사유 |
|----|------|--------|------|
| TF-SV-01 | **[3PA] CONFIRMED** | 95% | 3,000자 절삭 확인. `_threshold()` YAML 오버라이드 가능하나 기본값이 과소. |
| TF-SV-02 | **[3PA] RECLASSIFIED→IMPORTANT** | 90% | `±1` 캡은 코드 주석 "대원칙 #1: Python 판단 최소화"로 의도된 설계. |
| TF-ADV-01 | **[3PA] RECLASSIFIED→IMPORTANT** | 90% | advisory-only 검증기 — FP 노이즈 발생하나 Arc 거부 권한 없음. |
| TF-ADV-02 | **[3PA] RECLASSIFIED→IMPORTANT** | 90% | advisory-only 검증기 — 순간이동 미감지이나 거부 불가. |
| TF-ADV-03 | **[3PA] RECLASSIFIED→IMPORTANT** | 95% | Dead code — 에피소드 길이 측정 영향. 검증 정확도와 무관. |
| TF-FB-01 | **[3PA] CONFIRMED** | 99% | 하드코딩 15%/35% 비율로 fabricated. 실제 점수 무시. |
| TF-FB-02 | **[3PA] CONFIRMED** | 100% | `score_breakdown.get()` 반환값 미할당. 교과서적 no-op 버그. |
| TF-DG-01 | **[3PA] CONFIRMED** | 98% | `len(applied)>0`이면 전체 승인. 부분 거부 마스킹. |
| TF-DG-02 | **[3PA] CONFIRMED** | 97% | `commercial_appeal`/`emotion_arc` 2개 카테고리에 중복 등장. 이중 가중. |
| TF-CA-01 | **[3PA] RECLASSIFIED→IMPORTANT** | 88% | `arc_draft_validator.py:L888` + `unified_arc_validator.py:L571`에서 중복 커버리지. |
| TF-CA-02 | **[3PA] CONFIRMED** | 97% | LLM 실패 시 PASS. **[3PA] DEDUP — TF-CM-01과 동일 패턴. TF-CM-01이 canonical.** |
| TF-CA-03 | **[3PA] CONFIRMED** | 98% | JSON 실패 시 PASS. **[3PA] DEDUP — TF-CM-02와 동일 패턴. TF-CM-02가 canonical.** |
| TF-PLV-01 | **[3PA] RECLASSIFIED→IMPORTANT** | 95% | `passed: True` 항상 반환되므로 dead REJECT 분기. 런타임 무영향. |
| TF-PLV-02 | **[3PA] CONFIRMED** | 97% | em-dash `―` 대화 미계수. 동일 파일 L431이 `―` 인식 — 명백한 불일치. |
| TF-S4CB-01 | **[3PA] RECLASSIFIED→INSIGHT** | 90% | L2407 할당은 try 블록 두 번째 줄로 실패 불가. NameError 도달 불가. |
| TF-S4CB-02 | **[3PA] CONFIRMED** | 93% | `_db._lock` + `_db.conn.cursor()` 직접 접근. DBManager 우회. |

### IMPORTANT 항목 감리 (53건 요약)

| 판정 | 건수 | 주요 하향 |
|------|------|----------|
| CONFIRMED | 44 | — |
| RECLASSIFIED→INSIGHT | 3 | TF-SV-04(upstream NaN 차단), TF-CQ-12(prefetch가 캐시 사전 적재), TF-CW-11(self_critique가 Gate 동일 검사 실행) |
| Not sampled | 6 | INSIGHT 미표본 |

### INSIGHT 항목 감리 (45건 중 ~15건 표본)

표본 전량 CONFIRMED (80-99%). 미표본 30건은 deepdive 평가 수용.

### 크로스커팅 패턴 감리

| 패턴 | 판정 |
|------|------|
| fail-open 전염 (4건) | **[3PA] CONFIRMED** — 4건 전량 확인. P0 수정 권고. |
| 한국어 형태소 취약 (6건) | **[3PA] CONFIRMED** — 6건 전량 확인. 중앙화 NLP 유틸리티 권고. |
| LLM 입력 절삭 (5건) | **[3PA] CONFIRMED** — 5건 전량 확인. 시맨틱 기반 절삭 전환 권고. |
| Dead Code (5건) | **[3PA] CONFIRMED** — 5건 전량 확인. 정리 대상. |
| 무효 레이어 (3건) | **[3PA] CONFIRMED** — 3건 전량 확인. |

**요약**: CRITICAL 16건 중 생존 9건 (56.3%). 전체 114건 중 CONFIRMED 83건, RECLASSIFIED 10건, 미표본 21건.

*3-Pass Audit by Claude Opus 4.6 — 2026-03-16*

### [3PA-R2] 대원칙 적용 재감리 (2026-03-16)

대원칙 4개를 감사 렌즈로 추가 적용한 결과, 본 SSOT에서 10건 판정 변경.

#### CRITICAL 항목 R2 변경 (2건)

| ID | R1 판정 | R2 판정 | R2 확신도 | 대원칙 | 사유 |
|----|---------|---------|-----------|--------|------|
| **TF-SV-02** | RECLASSIFIED→IMP (90%) | **CLOSED** | **97%** | **#1** | `scoring_validator.py:L957-961` 코드에 `# [TF-C02] 대원칙 #1: Python 판단 최소화` 명시. ±1 캡은 대원칙 의도적 구현. Feature, not bug. |
| **TF-PLV-01** | RECLASSIFIED→IMP (95%) | **FALSE-POSITIVE** | **99%** | #1 | `pre_llm_validator.py:L133`이 `"passed": True` 항상 반환. `validation_orchestrator.py:L1185`의 REJECT 분기는 dead branch — 런타임 진입 불가. |

#### IMPORTANT 항목 R2 변경 (8건)

| ID | R1 판정 | R2 판정 | R2 확신도 | 대원칙 | 사유 |
|----|---------|---------|-----------|--------|------|
| **TF-ADV-01** | RECLASSIFIED→IMP (90%) | **RECLASSIFIED→INSIGHT** | **98%** | #1 | advisory-only. `arc_draft_validator.py`는 `critical=[]` 반환 (REJECT 불가). 60% FP → LLM advisory 변환 → 실제 영향 0. |
| **TF-ADV-07** | CONFIRMED(IMP) | **RECLASSIFIED→INSIGHT** | **96%** | #1 | advisory-only. `_locations_compatible()` warnings만 생성. `critical=[]` 반환. REJECT 불가. |
| **TF-PLV-05** | CONFIRMED(IMP) | **RECLASSIFIED→INSIGHT** | **96%** | #1 | `passed=True` 항상. sensory check는 `score_deduction`만 영향. LLM 최종 판정. |
| **TF-PLV-06** | CONFIRMED(IMP) | **RECLASSIFIED→INSIGHT** | **96%** | #1 | NPC fuzzy matching FP → advisory 변환 → LLM 판단. `passed=True` 항상. |
| **TF-PLV-08** | CONFIRMED(IMP) | **RECLASSIFIED→INSIGHT** | **97%** | #1 | dialogue minimum `len/700` → advisory. `passed=True` 항상. 최종 REJECT는 LLM. |
| **TF-PB-01** | CONFIRMED(IMP) | **RECLASSIFIED→INSIGHT** | **96%** | #1 | `extract_npc_profiles()` substring FP → prompt building 노이즈. LLM이 컨텍스트에서 필터. |
| **TF-FB-11** | CONFIRMED(IMP) (75%) | **RECLASSIFIED→INSIGHT** | **96%** | #1 | 3000자 절삭 우선순위 역전 → feedback ordering 디테일. LLM 컨텍스트 이해로 보상. |
| **TF-CA-14** | CONFIRMED(INS) (80%) | **RECLASSIFIED→INSIGHT** | **97%** | #1 | brace 이중 에스케이프 → encoding detail. 실제 입력에 pre-escaped 내용 가능성 극히 낮음. |

#### 크로스커팅 패턴 R2 대원칙 평가

| 패턴 | 대원칙 | R2 판정 |
|------|--------|---------|
| fail-open 전염 (4건) | **#3 위반** | Director fail-closed 정책과 체계적 모순. P0 유지. |
| 한국어 형태소 취약 (6건) | **#1 적용** | Python 수집 노이즈. LLM 보정 가능. 심각도 하향 정당. |
| LLM 입력 절삭 (5건) | **#1 위반 가능** | Python이 LLM 판단 기초 차단. 심각도 유지. |
| Dead Code (5건) | N/A | 대원칙 무관. |
| 무효 레이어 (3건) | **#3 적용** | TF-DG-11: CONDITIONAL_PASS 덮어씀 = Director 주권 존중. TF-SV-02: **CLOSED**. |

**R2 CRITICAL 생존**: 9건 → **8건** (-1: TF-SV-02 CLOSED). TF-PLV-01은 FP.
**R2 요약**: 114건 중 CONFIRMED 74건, RECLASSIFIED 18건(+8), FP **1건**(+1), CLOSED **1건**(+1), 미표본 20건.

*3-Pass Audit R2 (대원칙) by Claude Opus 4.6 — 2026-03-16*
