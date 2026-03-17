# 축 10: 잘 읽고 (Comprehension)

Date: 2026-03-17
Bundle: B (아키텍처 효율)
3-Pass Audit: 88% → 93% → 96%
Final Confidence: 96%

## 1. 핵심 질문

LLM에 전달된 컨텍스트가 실제로 활용되고 있는가? 정보 전달 ≠ 정보 활용.

---

## 2. 현황 인벤토리

### 2.1 의도적 구현

| # | 파일/모듈 | 능력 | 의도/부수 | 상세 |
|---|----------|------|----------|------|
| 1 | `stage4_context_builder.py` `build_mandatory_context()` | 컨텍스트 조립 | 의도적 | 3-tier 구조 (tier0=canonical/world_state/fact_ledger, tier1=work_focus/slot_summary, tier2=failure_context/ambient_hints/volume_summaries). 2,200줄+ 전담 모듈 |
| 2 | `chief_writer_prompts.py` `build_chief_writer_main_prompt()` | 프롬프트 템플릿 | 의도적 | 30+ named parameters, 6-STEP 구조 (Blueprint분석→연속성→현재상태→Arc전술→세계관→문체DNA). 173줄 템플릿 |
| 3 | `context_advisor.py` `ContextAdvisor` | 검색 계획 | 의도적 | Stage별 budget (stage2=20K, stage3=30K, stage4=50K, director=20K chars). 장르 힌트, work_focus 추적, NPC roster 정규화. 892줄 |
| 4 | `context_advisor.py` `ContextBudgetTracker` | 예산 추적 | 의도적 | 섹션별 사용량 추적, `get_compression_targets()` — 초과 시 큰 섹션부터 압축 대상 식별 |
| 5 | `stage4_context_builder.py` `_build_continuity_packet()` | 엔티티 지목 조회 | 의도적 | 이번 화 관련 NPC/아이템/플롯/위치의 상세 이력을 budget(7,000자) 내에서 패킷 조립 |
| 6 | `stage4_context_builder.py` `_build_condensed_world_state_summary()` | 중복 억제 | 의도적 | CP가 이미 상세 주입한 엔티티는 "[CP 상세 참조]"로 대체, 비포함 엔티티만 상세 표기 |
| 7 | `stage4_context_builder.py` `_build_condensed_fact_ledger_summary()` | 중복 억제 | 의도적 | CP 포함 인물/아이템/수치는 압축, 비포함만 상세. 동일 패턴 |
| 8 | `stage4_context_builder.py` `_build_npc_boundary_block()` | NPC 지식 범위 | 의도적 | 상위 10 NPC의 knowledge_era, expertise_domain, secrets_known, dual_identity 주입 |
| 9 | `stage4_context_builder.py` `_build_retrieval_coverage_warning_section()` | 검색 누락 경고 | 의도적 | 4개 코드 기반 경고 (missing_work_slot_summary, work_focus_without_slots, trimmed_work_slot_summary, missing_relation_slice) |
| 10 | `director_ensemble.py` | Director 프롬프트 분리 | 의도적 | stable context + variable prompt 분리로 캐싱 효율화. 명시적 모순 체크 9개 항목 |
| 11 | `context_compression.py` `ContextCompressor` | 컨텍스트 압축 | 의도적 | `_smart_trim()` — slot_max_chars 초과 시 지능적 절삭 |
| 12 | `stage4_context_builder.py` `_apply_context_budget()` | 전체 예산 적용 | 의도적 | 총 budget 초과 시 큰 섹션부터 순차 압축. O(n) 최적화 완료 |
| 13 | `stage4_context_builder.py` `_prioritize_summaries_by_work_focus()` | 우선순위 재정렬 | 의도적 | work_focus tracking_slots/scene_engines와 관련도가 높은 요약을 상위로 재정렬 |
| 14 | `stage4_context_builder.py` `_filter_state_tracker_summaries_for_authority()` | 권위 우선 | 의도적 | persisted canonical layer(world_state, fact_ledger)가 arc-derived state_tracker 요약보다 우선 |
| 15 | `config/prompts/director.yaml` | Director stable/variable 분리 | 의도적 | V67.1 story context, V69.1 중복 서술 금지, V74 treatment 장르 정합 등 명시적 체크리스트 |

### 2.2 부수적 기여

| # | 파일/모듈 | 부수적 기여 내용 |
|---|----------|----------------|
| 1 | `negative_example_injector.py` | 40개 부정 예시 → "이렇게 쓰지 마"로 간접 우선순위 신호 |
| 2 | `dynamic_prompt_weighting.py` | 실패 기반 가중 지시문 → 최근 실패 패턴에 대한 암묵적 우선순위 |
| 3 | `chief_writer.py` self-critique | 자기 검토 루프 → CW가 자체적으로 컨텍스트 재확인하는 부수 효과 |
| 4 | `validation_orchestrator.py` 6-tier | 검증 결과가 재시도 feedback으로 전달 → 간접적으로 "어디를 다시 봐라" 신호 |

---

## 3. 갭 식별

### G10-1: 정보 활용률 측정 메커니즘 완전 부재

**유형**: 완전 부재

**증거**: 코드베이스 전체에서 "CW에 준 정보 X가 원고에 반영되었는가?"를 사후 검증하는 경로가 없다.

- `ContextBudgetTracker`는 **chars 단위 예산만** 추적한다 (context_advisor.py:130~165). 정보가 *전달*되었는지는 알지만 *활용*되었는지는 알 수 없다.
- Director의 모순 체크 9개 항목(director.yaml)은 "잘못 쓴 것"을 잡지만 "안 쓴 것"은 blueprint_coverage 20% 가중치에 간접 의존.
- `_build_retrieval_coverage_warning_section()`은 검색 **plan** 단계 누락만 감지하며, 실제 원고에서의 활용 여부는 검사하지 않는다.

**갭의 구체적 형태**: "NPC 장비 요약을 5,000자 주입했는데 원고에서 언급 0건" 같은 상황이 발생해도, 시스템이 이를 인지하지 못한다.

### G10-2: 프롬프트 내 명시적 우선순위 신호 부재

**유형**: 부분 구현

**증거**: `build_chief_writer_main_prompt()`의 6-STEP 구조는 암묵적 순서로 우선순위를 표현하지만:

- roadmap-v2 Theme N에서 이미 식별: `reader_satisfaction_guide`가 position 41 (하위 7%)에 위치.
- `prev_manuscripts_section` (V67, 이전 30화 전문)이 프롬프트 **말미**(recency zone)를 점유 — 실제로는 "참고용"이지 "최우선"이 아님.
- `satisfaction_guide_section`이 STEP 6(문체 DNA) 아래에 위치하여 Gemini의 attention middle attrition에 취약.
- 어떤 섹션에도 `[PRIORITY: CRITICAL]` 같은 명시적 중요도 마커가 없다.

**기존 대응**: `_prioritize_summaries_by_work_focus()`가 retrieval 요약의 순서를 재정렬하지만, 이는 retrieval 섹션 내부에서만 작동하며 프롬프트 전체 레이아웃에는 영향을 주지 않는다.

### G10-3: 프롬프트 크기 증가에 따른 활용률 감소 인식 부재

**유형**: 완전 부재

**증거**: `ContextBudgetTracker`가 budget 초과를 감지하고 압축 대상을 식별하지만:

- "budget 내이므로 괜찮다" → "but 50K chars prompt에서 LLM attention이 실제로 커버하는 범위는?" 에 대한 추정이 없다.
- Stage4 total budget이 50,000자(context_advisor.py:883)지만, `build_mandatory_context()`에서 주입되는 canonical constraints + world_state + fact_ledger + retrieval 결과의 합산이 budget을 얼마나 차지하는지만 추적하고, 이것이 LLM의 실제 comprehension capacity와 어떤 관계인지는 모델링되어 있지 않다.
- 에피소드 30화 이후 NPC/아이템/수치가 누적되면 context budget이 점점 더 빡빡해지지만(roadmap-v2 Theme K), 이에 따른 활용률 감소가 시스템에 피드백되지 않는다.

### G10-4: 정보 모순 감지 (프롬프트 내부 섹션 간)

**유형**: 부분 구현

**증거**:

- `_filter_state_tracker_summaries_for_authority()`가 canonical layer와 arc-derived summary 간 권위 충돌을 해소한다 — 이것은 존재하는 유일한 프롬프트 내부 모순 방지 메커니즘.
- 그러나 world_state 요약과 fact_ledger 요약 사이, 또는 retrieval 결과와 mandatory_context 사이의 모순은 감지하지 않는다.
- 같은 NPC의 상태가 world_state에서는 "부상"이고 retrieval 결과에서는 "회복"으로 나올 수 있는 시점 불일치 위험이 있다.

### G10-5: "무시했다" vs "안 줬다" 사후 구분 불가

**유형**: 완전 부재

**증거**: 원고에서 특정 NPC가 누락되었을 때:

- "CW 프롬프트에 해당 NPC가 있었는가?" → `episode_production.jsonl`에 프롬프트 전문이 기록되지 않으므로 역추적 불가.
- 프롬프트에 있었지만 CW가 무시한 건지, 애초에 retrieval에서 빠진 건지 사후에 판단할 수 없다.
- Director의 `blueprint_coverage` 차원이 이 갭을 **부분적으로** 커버하지만, Blueprint에 없는 context(NPC 장비, 수치 변화 이력 등)에 대해서는 커버리지 개념 자체가 없다.

### G10-6: Director 프롬프트의 정보 활용 구조

**유형**: 형식적 존재

**증거**: Director의 stable_context(~180K chars capacity)에 9개 명시적 모순 체크 항목이 있지만:

- 항목 8 "수학적 정확성"은 investment 장르에서만 작동.
- 항목 9 "중복 서술 금지 V69.1"은 이전/현재 화 간 중복만 감지.
- Director가 3개 후보 원고 **전문**을 비교하므로 variable prompt 크기가 매우 큼 → stable context의 디테일한 체크 항목이 attention 경쟁에서 밀릴 위험.

---

## 4. 영향도 추정

| 갭 ID | 갭 | 직접 영향 | 간접 영향 | 등급 |
|-------|------|---------|---------|------|
| G10-1 | 정보 활용률 측정 부재 | 원고에 NPC/아이템/설정 누락 반복 가능 → 세계관 밀도 저하 | 활용률 데이터 없이는 context 최적화 방향 결정 불가 | **critical** |
| G10-2 | 명시적 우선순위 신호 부재 | reader_satisfaction 같은 고가치 정보가 낮은 attention → 상업성/재미 저하 | context 재배치 실험의 A/B 비교 기준 부재 | **significant** |
| G10-3 | 크기-활용률 관계 무인식 | 장기 연재 시 context 비대 → 활용률 하락 → 품질 저하 (Theme K) | 비용 증가 대비 품질 향상 한계효용 판단 불가 | **significant** |
| G10-4 | 프롬프트 내부 모순 감지 부재 | 상충 정보 → CW가 임의 선택 → 모순 원고 생성 | Director가 잡지 못하면 영속화 | **significant** |
| G10-5 | 무시 vs 미제공 구분 불가 | 디버깅 시 원인 특정 불가 → 수정 방향 오판 | 학습/개선 루프 단절 | **significant** |
| G10-6 | Director 정보 구조 한계 | 3후보 전문 비교 시 stable context 디테일 약화 | 검증 누수 → 모순 원고 PASS | **nice-to-have** |

---

## 5. 방향 스케치

| # | 접근법 | 난이도 | 새 LLM 호출 | 기존 인프라 활용 | 리스크/부작용 |
|---|--------|--------|-------------|----------------|-------------|
| 1 | **엔티티 활용률 사후 감사** — 프롬프트에 주입된 NPC/아이템/수치 목록 vs 원고 등장 비율을 Python으로 자동 계산. episode_production.jsonl에 기록. | 소 | 불필요 | `_extract_blueprint_entities()` + 원고 텍스트 매칭으로 즉시 구현 가능 | 오탐: NPC가 다른 이름으로 언급될 수 있음 |
| 2 | **섹션별 priority 마커** — CW 프롬프트 각 STEP/섹션에 `[PRIORITY: CRITICAL/HIGH/MEDIUM/LOW]` 태그 추가. | 소 | 불필요 | `build_chief_writer_main_prompt()` 템플릿 수정만 | Gemini가 priority 태그를 실제로 존중하는지 검증 필요 |
| 3 | **프롬프트 레이아웃 A/B 실험 프레임** — satisfaction_guide 위치 변경 등의 효과를 측정할 수 있는 간단한 실험 인프라. | 중 | 불필요 | `PassRateMonitor` + `quality_dashboard`에 레이아웃 variant 태그 추가 | 실험 설계가 주관적일 수 있음 |
| 4 | **프롬프트 내부 모순 스캔** — `build_mandatory_context()` 마지막에 Python 기반 엔티티 교차 검증 (같은 NPC의 상태가 섹션 간 불일치하면 경고). | 중 | 불필요 | `_extract_blueprint_entities()` + `_build_continuity_packet()` 교차 대조 | 처리 시간 증가. False positive 관리 필요 |
| 5 | **컨텍스트 provenance 로깅** — 프롬프트 조립 시 각 섹션의 출처/크기/priority를 구조화하여 JSONL 기록. 사후 디버깅과 활용률 분석 기반 마련. | 소 | 불필요 | `ContextBudgetTracker.get_usage_report()` 확장 | 로그 크기 증가 |
| 6 | **attention-aware 레이아웃** — Gemini의 primacy/recency bias를 고려하여 critical 정보를 프롬프트 상단과 하단에 배치, 참고 정보를 중간에 배치하는 레이아웃 규칙 도입. | 중 | 불필요 | `build_chief_writer_main_prompt()` 구조 변경 | 모델 버전 변경 시 최적 배치가 달라질 수 있음 |

**당장 할 수 있는 것**: #1 (엔티티 활용률), #2 (priority 마커), #5 (provenance 로깅)
**설계가 필요한 것**: #3 (A/B 실험), #4 (모순 스캔), #6 (attention-aware 레이아웃)

---

## 6. 묶음 내 교차 발견

축 10이 묶음 B의 첫 축이므로 앞 축 교차 발견은 없다. 이후 축 조사에서 이 축의 발견을 참조한다.

**축 11(조율)에 전달할 발견**:
- G10-1의 활용률 미측정은 에이전트 간 정보 전달 효율 판단도 불가능하게 만든다.
- G10-4의 프롬프트 내부 모순은 서로 다른 에이전트가 생성한 정보가 합쳐질 때 발생 가능성이 높다.

**축 12(흐름)에 전달할 발견**:
- G10-5의 "무시 vs 미제공" 구분 불가는 REJECT 후 재시도 시 어디를 고쳐야 하는지 판단을 방해한다.
- G10-3의 context 비대는 장기 연재 resilience에 직결된다.

---

## 7. 3-Pass 감리 기록

### Pass 1: 사실 정확성 (88%)

- **수정**: 초기 draft에서 "41개 정보원"이라는 master-order의 숫자를 그대로 인용했으나, 실제 `build_chief_writer_main_prompt()` 파라미터 수는 30+개이고 "정보원"의 정의가 모호했음. 파라미터 수 기반으로 재서술.
- **수정**: `ContextBudgetTracker`를 "활용률 추적"으로 오해한 초기 서술 → "chars 단위 예산 추적"으로 정확하게 교정.
- **수정**: Director comparison_notes 240자 절삭 → `_short_text(comparison_notes, 240)` (director_ensemble.py:396) 코드로 확인. 원래 master-order 가이드에 언급된 "comparison_notes 240자 절삭"은 축 13(Explainability) 범위이나 사실 확인은 완료.
- **확인**: Stage4 total budget 50,000자 → `context_advisor.py:883` `defaults = {"stage4": 50000}` 확인.
- 확신도: 88% (프롬프트 실제 런타임 조립 결과는 코드만으로는 검증 한계)

### Pass 2: 논리 정합성 (93%)

- **검증**: G10-1 → 영향도 critical 판단 — "측정 불가 → 개선 불가" 논리 연결 건전. 반론: Director의 blueprint_coverage 20% 가중치가 부분 커버 → 그러나 이것은 "Blueprint 씬 반영률"이지 "프롬프트 정보 전반의 활용률"이 아니므로 gap 존재 유효.
- **검증**: G10-2 → significant 판단 — attention middle attrition은 Transformer 모델의 알려진 특성이므로 논리적 근거 충분. 다만 Gemini 구체 모델의 attention 프로파일은 공개 문헌 기반 추정이므로 "추정"임을 명시.
- **수정**: G10-3에서 "budget을 넘어서면" → 실제로는 `_apply_context_budget()`이 budget 초과를 감지하고 압축함. 갭은 "압축 후에도 남는 50K chars가 LLM이 실제로 소화할 수 있는 양인가"에 대한 무인식. 표현 교정.
- 확신도: 93%

### Pass 3: 완성도 (96%)

- **보완**: 현황 인벤토리에 #13 `_prioritize_summaries_by_work_focus()`, #14 `_filter_state_tracker_summaries_for_authority()` 추가 — 정보 활용 관련 부수적이지만 의도적인 메커니즘을 놓치고 있었음.
- **보완**: 방향 스케치 #6 "attention-aware 레이아웃" 추가 — G10-2에 대한 방향이 #2(마커)만으로는 불충분.
- **보완**: 교차 발견 섹션에 축 12 전달 내용 추가.
- **확인**: 모든 갭이 코드 경로 기반 근거를 가지고 있는지 재확인 완료.
- 확신도: 96%
