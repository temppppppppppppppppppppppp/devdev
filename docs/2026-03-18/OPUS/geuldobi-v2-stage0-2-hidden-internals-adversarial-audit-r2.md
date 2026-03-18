# 글도비 v2 Stage 0-2 딥다이브 — 2차 적대적 감리 결과 (4-6회차)

> **감리일**: 2026-03-18
> **감리 대상**: 정정 완료된 `geuldobi-v2-stage0-2-hidden-internals-deepdive-full-survey.md`
> **감리 방법**: 1차 감리(48건) CONFIRMED 판정 재검증 + 수치 심층 감사 + 누락 경로 완전성 감사
> **코드 수정**: 없음 (감리 전용)

---

## 1. 감리 구성

| 회차 | 초점 | 검증 항목 수 |
|------|------|------------|
| **4차** | 정정 사항 재검증 + 기존 CONFIRMED 재도전 | 15건 |
| **5차** | 전수 수치 심층 감사 | 16건 |
| **6차** | 누락 침묵 실패 완전성 + 기존 SF 재검증 | 16건 |
| **합계** | — | **47건** |

---

## 2. 4차 감리: 정정 재검증 + CONFIRMED 재도전

### 2.1 정정 사항 재검증

| ID | 정정 내용 | 코드 근거 | 판정 |
|----|----------|----------|------|
| C1 | tactical doc min = ep_count * 450 | `constants.py:244` → 450, `arc_ensemble.py:508` → `Stage2Limits.MIN_CHARS_PER_EPISODE` 사용 | **CONFIRMED** |
| C2 | "부분 문자열 포함" 정정 | `constraint_db.py:619` → `item in f or f in item` (폴백 경로) | **INACCURATE** — 정정이 불완전. `SemanticItemRegistry` (주 경로, `constraint_db.py:606`) **는** `semantic_item_registry.py:197`에서 **Jaccard 유사도를 사용**. 폴백 경로만 부분 문자열. 문서가 "Jaccard 미존재"로 과잉 정정 |
| C3 | 무협 금지 용어 130개 (129 고유) | 하드코딩 리스트 130개 확인. 그러나 `config/genres/wuxia.yaml`이 존재하면 **YAML 값 우선 로드** (`cfg.get("forbidden_terms", [...])`) | **INACCURATE** — 런타임에는 YAML(129개) 사용. 130개는 하드코딩 폴백(dead code). 정확한 표현: "런타임 129개 (YAML), 폴백 130개/129 고유 (하드코딩)" |

### 2.2 CONFIRMED 재도전

| ID | 주장 | 코드 근거 | 판정 |
|----|------|----------|------|
| P1 | StageZeroManager 10개 장르 | `__init__.py:61-72` → 10개, `constants.py:62-74` GenreTypes.all() 10개 | **CONFIRMED** |
| P2 | _call_llm 2모델 폴백 | `story_expander.py:61` → `_FALLBACK_MODELS = [SUMMARY_MODEL, V50_MODULE_MODEL]` | **CONFIRMED** |
| P3 | _STAGE0_REVIEW_WINDOW = 3 | `story_expander.py:36` → 정확 | **CONFIRMED** |
| P4 | StyleGuide anti_ai_patterns + exemplary_passages | `style_extractor.py:54,57` → 존재 | **CONFIRMED** |
| P5 | TTR 0.3-0.7 스케일링 | `diversity_sampler.py:164-165` → `(ttr - 0.3) / 0.4 * 100` | **CONFIRMED** |
| P6 | ending_hook 마지막 500자 | `confidence_calibration.py:279` → `manuscript[-500:]` | **CONFIRMED** |
| P7 | ExpertMixture 신뢰도 공식 | `expert_mixture.py:283` → `min(1.0, max_score / max(total_keywords * 0.3, 1))` | **INACCURATE** — 문서에 `max(..., 1)` 0 방지 가드 누락 |
| P8 | 최근 50건 실패 분석 | `dynamic_prompt_weighting.py:160` → `limit=50` | **CONFIRMED** |
| P9 | AdversarialSelfPlay max_rounds=2 | `adversarial_self_play.py:148` → `self.max_rounds = 2` | **CONFIRMED** |
| P10 | rollback_to batch load | `fact_ledger.py:749` → `get_all_episode_bibles()` | **CONFIRMED** |
| P11 | "만" alone → 1만 | `preset_registry.py:577-578` → `current = 1` | **CONFIRMED** |
| P12 | ThreadPoolExecutor (비async) | `arc_ensemble.py:18,414` → `ThreadPoolExecutor` | **CONFIRMED** |

**4차 결과**: CONFIRMED 12 / INACCURATE 3

---

## 3. 5차 감리: 수치 심층 감사

| ID | 주장 | 코드 근거 | 판정 |
|----|------|----------|------|
| N1 | Stage 0 파일 수 "6 (+ __init__.py)" | 실제: spinner, reverse_expander, preset_registry, style_extractor, story_expander = **5개 모듈** + __init__.py = **6개 파일 총합** | **INACCURATE** — "6 (+ __init__.py)" 표현은 7개로 오독 가능. 정확: "5개 모듈 + __init__.py = 6개" |
| N2 | 침묵 실패 16건 | SF1-SF16 각각 코드 확인 완료 | **CONFIRMED** (단, 완전성은 6차에서 별도 검증) |
| N3 | 앙상블 전략 3개 | `arc_ensemble.py:159-178` → 3개 | **CONFIRMED** |
| N4 | 타임아웃 기본값 300/240초 | `config/system.yaml:43-44` → `arc: {ensemble: 300, single: 240}` | **CONFIRMED** |
| N5 | "재시도 루프 최대: 9회" | `four_phase.py:523` → `max_internal_retries=9`, `612` → `range(max_internal_retries + 1)` = **10회 시도** | **INACCURATE** — 파라미터 9이나 루프는 **10회** (0~9). "재시도 최대 9회 (총 10회 시도)"로 명확화 필요 |
| N6 | ArcCorrector 20% | `arc_corrector.py:94` → `max_change_ratio=0.20` | **CONFIRMED** |
| N7 | ArcCritic 7차원 | `arc_critic.py:38-69` → 7개 | **CONFIRMED** |
| N8 | FactLedger 100건 한도 | `fact_ledger.py:72` → `MAX_HISTORY_PER_ENTITY = 100` | **CONFIRMED** |
| N9 | DiversitySampler 4축 | `diversity_sampler.py:218` → 4개 키 | **CONFIRMED** |
| N10 | ConfidenceCalibration 7요인 | `confidence_calibration.py:69-77` → 7개 키 | **CONFIRMED** |
| N11 | DynamicPromptWeighting 10카테고리 | `dynamic_prompt_weighting.py:25-37` → 10개 | **CONFIRMED** |
| N12 | ExpertMixture 8씬유형 | `expert_mixture.py:32-42` → 8개 | **CONFIRMED** |
| N13 | 설계 강점 10건 DS1-DS10 | 각각 코드 근거 확인 | **CONFIRMED** |
| N14 | 미사용 코드 1건 | `_MAX_WORKERS` 외 추가 미사용 상수 미발견 | **CONFIRMED** |
| N15 | 이중 구현 1건 | `preset_registry._parse_korean_number` + `stage2_finalizer._to_num_with_korean` + **`stage2_optimizer._parse_korean_number`** + **`investment_arithmetic_checker._parse_korean_amount`** = **4곳** | **WRONG** — 이중이 아니라 **4중 구현** |
| N16 | ep_count * 450 import 경로 | `arc_ensemble.py:21` → `from constants import Stage2Limits`, `arc_ensemble.py:508` → 사용 확인 | **CONFIRMED** |

**5차 결과**: CONFIRMED 12 / INACCURATE 2 / WRONG 1

---

## 4. 6차 감리: 누락 침묵 실패 완전성 감사

### 4.1 누락된 침묵 실패 — 신규 발견 11건

| ID | 위치 | 동작 | 심각도 | SF1-16 대비 |
|----|------|------|--------|-----------|
| **MSF-A** | `reverse_expander._extract_protagonist():335-338` | LLM 실패 시 `return {}` — 주인공 정보 전무 | **고** | SF3과 유사하나 **역설계 경로** (미기재) |
| **MSF-B** | `reverse_expander._extract_world_state():370-373` | LLM 실패 시 `return {}` — 세계관 전무 | **중** | 미기재 |
| **MSF-C** | `reverse_expander._extract_npcs():351-356` | LLM 실패 시 `return []` — NPC 전무 | **중** | SF4 유사하나 역설계 경로 (미기재) |
| **MSF-D** | `story_expander._generate_skeleton():647-652` | LLM 실패 시 `[]` 확장 — 블록 수 미달 | **중** | 미기재 |
| **MSF-E** | `story_expander._generate_details():712-716` | LLM 실패 시 스켈레톤 블록 그대로 사용 (content 미생성) | **중** | 미기재 |
| **MSF-F** | `constraint_db._load_from_db():76-98` | DB 로드 실패 → `arc_states={}` — **전체 제약 시스템 비활성** | **고** | 미기재 |
| **MSF-G** | `constraint_db.validate_arc_design():587-590` | arc_no 파싱 실패 → `valid=True` 반환 — 검증 우회 | **저** | 미기재 |
| **MSF-H** | `fact_ledger._load():91-102` | DB 로드 실패 → 빈 원장 — **전체 사실 추적 소실** | **고** | 미기재 |
| **MSF-I** | `fact_ledger.save():116-127` | DB 저장 실패 → `False` 반환 — 메모리만 잔존 | **중** | 미기재 |
| **MSF-J** | `analyst.enrich_raw_block_async():1440-1442` | 일반 예외 → 원본 블록 반환 **마커 없이** (SF12와 다른 경로) | **고** | SF12는 JSON 파싱 실패만 커버 |
| **MSF-K** | `four_phase_arc_generator.__init__():427-436` | 장르 감지 실패 → `"wuxia"` 기본값 — 비무협 프로젝트에 무협 제약 적용 | **중** | 미기재 |

### 4.2 기존 SF 재검증

| SF# | 재검증 결과 | 변경 사항 |
|-----|-----------|----------|
| SF5 | 정당 — "stale 연속성 컨텍스트"는 실제 발생 가능 | 저 심각도 유지 |
| SF10 | 경계 사례 — "혼합" 기본값은 합리적 행동이나 사용자 의도와 불일치 가능 | 저 심각도 유지, "휴리스틱 한계"로 재분류 권장 |
| SF13 | 정당, 그러나 **심각도 상향 권장** — 2/3 후보 타임아웃 시 spare pool 고갈 → 전체 재생성 강제 | **저 → 중** 상향 |
| **SF15** | **서술 오류 발견** — 문서: "마지막 생성된 arc를 그대로 반환" → 실제: `return None, pipeline_result` (`None` 반환) | **서술 정정 필요** |
| **SF16** | **메커니즘 오류 발견** — 문서: "원본 Arc 그대로 반환" → 실제: `return None, log` (`None` 반환, 원본 아님) | **서술 정정 필요** |

### 4.3 완전성 판정

| 항목 | 원문 주장 | 실제 |
|------|---------|------|
| 침묵 실패 총 수 | 16건 | **최소 27건** (16 + 11 신규) |
| "미추적 경로 0건" | 원문 PASS 3 결과 | **WRONG** — 11건 누락 |

**6차 결과**: 기존 SF 중 서술 오류 2건 (SF15, SF16), 심각도 변경 1건 (SF13), 누락 11건 발견

---

## 5. 오류 종합 — 2차 감리 전체

### 5.1 전체 집계 (4-6차)

| 판정 | 4차 | 5차 | 6차 | 합계 |
|------|-----|-----|-----|------|
| **CONFIRMED** | 12 | 12 | — | 24 |
| **INACCURATE** | 3 | 2 | 2 (SF15, SF16) | 7 |
| **WRONG** | 0 | 1 | 1 (완전성) | 2 |
| **신규 발견** | — | — | 11 (MSF) | 11 |

### 5.2 정정표

#### WRONG (사실 오류) — 2건

| # | 원문 | 실제 | 정정 |
|---|------|------|------|
| **W4** | "이중 구현 1건" | 4곳에 독립 한국어 숫자 파싱 존재 | **"4중 구현"**: `preset_registry`, `stage2_finalizer`, `stage2_optimizer`, `investment_arithmetic_checker` |
| **W5** | "미추적 경로 0건" (PASS 3 완전성) | 11건 누락 | **"누락 침묵 실패 11건 추가 식별"**으로 정정 |

#### INACCURATE (부정확) — 7건

| # | 원문 | 정정 |
|---|------|------|
| **I13** | "Jaccard 미존재" (과잉 정정) | `SemanticItemRegistry` (주 경로)는 Jaccard 사용 (`semantic_item_registry.py:197`). **폴백 경로만** 부분 문자열. 정확: "주 경로: Jaccard (SemanticItemRegistry), 폴백: 부분 문자열 포함" |
| **I14** | 금지 용어 "130개 (129 고유)" | **런타임**: wuxia.yaml 존재 시 **129개** (YAML 우선). 하드코딩 130개는 폴백(dead code). 정확: "런타임 129개 (YAML), 폴백 하드코딩 130개/129 고유" |
| **I15** | ExpertMixture 신뢰도 공식 누락 | `max(total_keywords * 0.3, **1**)` — 0 방지 가드 누락 |
| **I16** | 파일 수 "6 (+ __init__.py)" | 5개 모듈 + __init__.py = **총 6개** (7개로 오독 가능) |
| **I17** | "재시도 루프 최대 9회" | 파라미터 9이나 루프 **10회** (range(9+1)). "재시도 최대 9회 (총 10회 시도)"로 명확화 |
| **I18** | SF15: "마지막 arc 반환" | 실제: `return None, pipeline_result` — **None 반환** |
| **I19** | SF16: "원본 Arc 그대로 반환" | 실제: `return None, log` — **None 반환, 원본 아님** |

---

## 6. 정정 후 신뢰도 평가

### 1차 감리 (48건) + 2차 감리 (47건) 통합

| 지표 | 1차 | 2차 | 통합 |
|------|-----|-----|------|
| 총 검증 항목 | 48 | 47 | 95 |
| WRONG | 3 | 2 | 5 |
| INACCURATE | 12 | 7 | 19 |
| CONFIRMED | 33 | 24 | 57 |
| 신규 발견 (누락) | — | 11 | 11 |
| 정정 필요 비율 | 31.2% | 19.1% | 25.3% |

### 핵심 메트릭

| 항목 | 값 |
|------|---|
| 팬텀 기능 (1차에서 발견) | 1건 — constraint_db 폴백의 "Jaccard" (실제: 주 경로에는 존재) |
| 수치 오류 | 3건 — 500→450, 154→130→129(런타임), 1중→4중 |
| 서술 오류 | 2건 — SF15/SF16 "반환" 동작 오기재 |
| 완전성 누락 | 11건 — 침묵 실패 미기재 |
| 심각도 오분류 | 1건 — SF13 저→중 |

### 최종 문서 상태

원문 문서 `geuldobi-v2-stage0-2-hidden-internals-deepdive-full-survey.md`에 아직 반영 필요한 항목:

| 우선도 | 항목 | 변경 |
|--------|------|------|
| **P0** | SF15 서술: "마지막 arc 반환" | → "`None` 반환 (pipeline_result에 FAILED 표시)" |
| **P0** | SF16 서술: "원본 Arc 반환" | → "`None` 반환 (호출자가 원본 사용 결정)" |
| **P0** | 모순 탐지 정정 보완 | → "주 경로(SemanticItemRegistry): Jaccard, 폴백: 부분 문자열 포함" |
| **P1** | 금지 용어 수 | → "런타임 129개 (YAML), 폴백 130개/129 고유" |
| **P1** | 이중 구현 수 | → "4중 구현" |
| **P1** | 재시도 횟수 | → "최대 9회 재시도 (총 10회 시도)" |
| **P1** | 침묵 실패 총 수 | → "27건 (기존 16 + 신규 11)" |
| **P2** | 파일 수 표현 | → "5개 모듈 + __init__.py = 총 6개" |
| **P2** | SF13 심각도 | → 저 → 중 |
| **P2** | ExpertMixture 공식 | → `max(..., 1)` 가드 추가 |

---

> **2차 적대적 감리 종결**
> 4-6차 감리 완료. 47건 추가 검증 중 WRONG 2건, INACCURATE 7건, 신규 누락 11건 식별.
> 가장 중대한 발견: **침묵 실패 11건 누락** (MSF-A~K), **SF15/SF16 서술 오류** (None 반환을 arc 반환으로 오기재).
> 1-2차 통합: 95건 검증, 정정 필요 24건 (25.3%), 모두 정정 가능.
