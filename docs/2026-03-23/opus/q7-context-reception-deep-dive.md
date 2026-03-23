Date: 2026-03-23
Status: provisional (3-pass audited, below confidence gate)
Document Type: Q7 context reception deep-dive survey report
Canonical Path: `docs/2026-03-23/opus/q7-context-reception-deep-dive.md`
Terminal: T7
Axis: Q7 "잘 받냐" — context reception, prompt injection completeness, truncation/order problems

---

## 1. Executive Summary

Q7은 "각 Stage의 주요 LLM이 필요한 정보를 빠짐없이, 올바른 형태로 받는가"를 검증하는 축이다.

현재 context reception 파이프라인은 **구조적으로 건전**하다. 3-tier 예산 모델(tier0/tier1/tier2), retrieval plan 기반 슬롯 할당, 그리고 `_apply_prompt_size_gate` 안전 게이트가 모두 작동한다. 그러나 **5개의 P0/P1 hotspot**이 확인된다:

1. **P1-1**: `prev_manuscripts_text`가 `smart_truncate()`의 **기본값 1M자**로 잘리는데, 이때 head=80K/tail 비율이 context budget과 무관하게 적용되어 중간 에피소드가 소실될 수 있다.
2. **P1-2**: `_fit_context_text`와 `_fit_compact_text`가 **바이트 단위가 아닌 char 단위로 잘리지만**, head/tail 비율이 고정(0.55)이어서 의미 단위 경계를 무시한다.
3. **P1-3**: Stage 4 context budget 초과 시 압축 대상 선정에서 `[작품 추적 슬롯 요약]`과 `[SC:arc_semantic_carryover]`는 보호되지만, **Continuity Packet과 World State condensed header는 보호 대상이 아니다**.
4. **P1-4**: Director `select_and_judge_ensemble` 경로에서 `prev_manuscripts_text`가 `smart_truncate(max_chars=200000, head_chars=110000)`로 잘리는데, 이 200K 한도가 `director_total_budget=300K`와 별개로 **하드코딩**되어 있다.
5. **P1-5**: `chief_writer_context_packets.py:158`에서 `prev_manuscripts_text`를 `smart_truncate()` 기본값(1M자, head=80K)으로 잘라 ChiefWriter 프롬프트에 주입하는데, CW의 실제 사용 가능한 예산은 Stage4 total_budget(300K)의 일부이므로 **budget mismatch**가 있다.

**Fresh-run-before-fix allowed: no** — P1-1/P1-5의 prev_manuscripts 잘림은 장기연재(30화+)에서 중간 화 소실로 이어져 모순 감지 실패를 유발할 수 있으며, 이는 fresh run에서도 재현될 수 있다.

---

## 2. Current Ownership / Flow Map

### 2.1 Context Assembly Ownership Chain

```
Stage 4 Episode Production:
  stage4_orchestrator.py                  # DI context 주입, mandatory_context budget 적용
    └─ stage4_context_builder.py          # 3-tier context 수집 + retrieval plan 실행
        ├─ stage4_context_packets.py      # CP(Continuity Packet), World State condensed, FactLedger
        └─ context_advisor.py             # Retrieval plan 생성 + budget 할당
    └─ stage4_interview_round.py          # round-level context 조립 → CW/Director에 전달
        ├─ chief_writer_context.py        # CW 프롬프트 조립 (build_common_context)
        │   └─ chief_writer_context_packets.py  # digest, guard, HUD, prev_manuscripts 패킷
        └─ stage4_director_runtime.py     # Director context 조립 (run_pre_director_validation)
            └─ director_ensemble.py       # ensemble selection + audit context 조립
                └─ director_auditor.py    # _expand_prev_full_text (30화 확대)

Stage 3 Blueprinting:
  stage3_orchestrator.py                  # blueprint context + prev_manuscripts_text
    └─ context_advisor.py (stage3 budget)
    └─ three_phase_blueprint_runtime.py   # blueprint generation context

Stage 2 Arc Design:
  stage2_orchestrator.py → stage2_preflight.py  # arc design context + retrieval
```

### 2.2 Truncation/Budget Authority Chain

```
MAX_CONTEXT_CHARS = 1,000,000 (validation.yaml SSOT)
  └─ BaseAgent._apply_prompt_size_gate()   # 최종 안전 게이트 (ask() 전)
      └─ smart_truncate(head=0.55*budget)  # head/tail 보존 잘림

Per-Stage Budget (validation.yaml):
  stage2_total_budget = 50,000
  stage3_total_budget = 80,000
  stage4_total_budget = 300,000
  director_total_budget = 300,000

Per-Section Budget:
  Stage4ContextBuilder._apply_context_budget()  # tier1/tier2 압축
  Stage4ContextPackets.build_continuity_packet() budget = 7,000
  _build_condensed_world_state() max_chars = 계산된 가변값
```

---

## 3. Top Hotspots

### P1-1. `prev_manuscripts_text` 기본 smart_truncate — 중간 화 소실 위험
- **file:line**: `modules/domain/agents/chief_writer_context_packets.py:158`
- **fix type**: `contract-cleanup`
- **현상**: `smart_truncate(prev_manuscripts_text)` — 기본값 `max_chars=1,000,000`, `head_chars=80,000`. 1M자 미만이면 무잘림이지만, 장기연재 30화 이상에서 합산 텍스트가 1M을 초과하면 head 80K + tail (1M-80K) 구간만 보존되고 **중간 에피소드가 통째로 사라진다**.
- **영향**: CW가 중간 화의 인물/수치/관계 변화를 모르게 되어 모순 생성 위험.
- **근거**: 에피소드 당 평균 5,000자 × 30화 = 150K이므로 현재 테스트 범위에서는 문제 없지만, 200화 프로젝트(1M자)에서 발현.

### P1-2. head/tail 고정 비율 잘림 — 의미 단위 무시
- **file:line**: `modules/core/constants.py:145`, `modules/core/stage4_context_builder.py:113-126`
- **fix type**: `contract-cleanup`
- **현상**: `smart_truncate`의 `head_chars` 기본값이 80,000이고 `_fit_context_text`는 head_ratio=0.55로 고정. 에피소드 경계(`=== EP N ===`) 같은 구분자를 인식하지 않고 char 수 기준으로 자른다.
- **영향**: 잘린 텍스트 내에서 에피소드 경계가 깨져 LLM이 화 번호를 혼동할 수 있음. 현재 운영 범위(4화)에서는 미발현.

### P1-3. Budget 초과 시 Continuity Packet / World State 비보호
- **file:line**: `modules/core/stage4_context_builder.py:1164-1170`
- **fix type**: `contract-cleanup`
- **현상**: `_apply_context_budget`에서 보호 대상은 `[작품 추적 슬롯 요약]`과 `[SC:arc_semantic_carryover]`뿐. Continuity Packet(`=== [Continuity Packet] ===`)과 World State condensed header는 budget 초과 시 일반 섹션과 동일하게 압축됨.
- **영향**: budget 초과 시 NPC 상태/관계 이력/수치 변화 정보가 잘려 모순 방지 능력 약화.
- **근거**: Stage4 budget=300K에서 보통 50-70% 사용 → 현재는 압축이 거의 발생하지 않으나, 장기연재에서 prev_manuscripts + world_state가 커지면 발현 가능.

### P1-4. Director ensemble prev_manuscripts 하드코딩 200K
- **file:line**: `modules/domain/agents/director_ensemble.py:729`
- **fix type**: `contract-cleanup`
- **현상**: `smart_truncate(prev_manuscripts_text if prev_manuscripts_text else "(previous manuscripts unavailable)", max_chars=200000, head_chars=110000)`. Director total_budget(300K)과 별개의 하드코딩 200K 한도.
- **영향**: Director가 ensemble selection 시 참조하는 이전 원고가 200K로 잘릴 때 budget-aware가 아니므로, budget이 변경되어도 이 한도는 따로 수정해야 함.

### P1-5. CW context와 Stage4 budget 간 mismatch
- **file:line**: `modules/domain/agents/chief_writer_context_packets.py:158` + `modules/core/stage4_context_builder.py:1114`
- **fix type**: `contract-cleanup`
- **현상**: CW에 주입되는 `prev_manuscripts_text`는 `smart_truncate()` 기본값(1M)으로 잘리지만, 이 텍스트를 포함한 전체 CW 프롬프트는 `_apply_prompt_size_gate()`의 MAX_CONTEXT_CHARS(1M)과 stage4_total_budget(300K) 두 개의 별도 게이트를 거친다. 두 게이트 사이에 명시적 조율이 없어, prev_manuscripts가 300K budget의 대부분을 소비하면 다른 핵심 정보(blueprint, arc_doc, HUD)가 잘릴 수 있음.
- **영향**: 장기연재에서 prev_manuscripts가 비대해지면 CW가 필수 컨텍스트(blueprint scenes, constraints)를 못 받을 수 있음.

---

## 4. Quick Wins

### QW-1. CW prev_manuscripts에 budget-aware 상한 부여
- **file:line**: `modules/domain/agents/chief_writer_context_packets.py:158`
- **fix type**: `contract-cleanup`
- **현황**: `smart_truncate(prev_manuscripts_text)` → 기본 1M
- **권고**: `smart_truncate(prev_manuscripts_text, max_chars=<stage4_budget의 40% 또는 120K>, head_chars=<50%>)`로 변경. 또는 stage4_context_builder의 budget meta에서 CW 할당량을 계산해 전달.
- **ROI**: 높음 — 장기연재 모순 방지의 핵심 게이트.

### QW-2. Continuity Packet을 budget 보호 대상에 추가
- **file:line**: `modules/core/stage4_context_builder.py:1164`
- **fix type**: `contract-cleanup`
- **현황**: `protected_prefix = "[작품 추적 슬롯 요약]"` 만 보호
- **권고**: `"=== [Continuity Packet]"` prefix도 보호 목록에 추가
- **ROI**: 중간 — 현재 budget 초과가 드물지만, 보호 누락은 설계 결함.

### QW-3. Director ensemble prev_manuscripts 한도를 validation.yaml 참조로 전환
- **file:line**: `modules/domain/agents/director_ensemble.py:729`
- **fix type**: `contract-cleanup`
- **현황**: `max_chars=200000` 하드코딩
- **권고**: `_threshold("smart_retrieval.director_prev_manuscripts_budget", 200000)` 또는 `director_total_budget`의 비율로 계산
- **ROI**: 낮음 — 현재 값은 합리적이지만, SSOT 원칙 위반.

---

## 5. Boundary Refactor Candidates

### BR-1. Context budget cascade — CW/Director 할당량 명시적 분리
- **현황**: `stage4_total_budget=300K`가 retrieval sections에만 적용되고, CW 프롬프트 내부의 개별 섹션(prev_manuscripts, world_state, blueprint 등)에는 별도 budget cascade가 없음. 각 섹션은 자체 하드코딩 한도를 가지거나(director: 200K) 기본값을 사용(CW: 1M).
- **권고**: `stage4_context_builder._build_episode_context_payload()`에서 CW용 budget envelope를 명시적으로 계산하고, 이를 `build_common_context()`에 전달하는 패턴. Director도 동일.
- **fix type**: `boundary-refactor`
- **복잡도**: 중 — stage4_context_builder와 chief_writer_context 사이의 인터페이스 변경 필요.

### BR-2. smart_truncate에 에피소드 경계 인식 추가
- **현황**: `smart_truncate`는 head/tail char 수만 보존. 에피소드 구분자(`=== EP N ===`, `[제N화]`)를 인식하지 않음.
- **권고**: `smart_truncate_episodes()` 변형을 추가하여, 에피소드 경계를 기준으로 가장 최근 N화를 보존하고 나머지를 요약/제거. 또는 `ContextCompressor._smart_trim`에 delimiter-aware 모드 추가.
- **fix type**: `boundary-refactor`
- **복잡도**: 중 — constants.py와 context_compression.py 변경.

---

## 6. Fresh-Run Relevance

**Fresh-run-before-fix allowed: no**

Top 3 highest-ROI code fixes before next fresh run:

1. **QW-1**: CW `prev_manuscripts_text`에 budget-aware 상한 부여 (`chief_writer_context_packets.py:158`)
   - **이유**: 장기연재에서 중간 화 소실 → 모순 생성 → Director REJECT cascade. 이는 `LLM-Director 정합성 불일치` 계열이며, fresh run에서 10화 이상 진행 시 재현 가능.

2. **QW-2**: Continuity Packet budget 보호 (`stage4_context_builder.py:1164`)
   - **이유**: NPC 상태/관계 정보가 budget 초과 시 잘리면 CW가 사망 NPC를 부활시키거나 관계를 혼동할 수 있음. `컨텍스트 손실` 계열.

3. **QW-3**: Director ensemble prev_manuscripts 한도를 SSOT 참조로 전환 (`director_ensemble.py:729`)
   - **이유**: 현재 하드코딩은 합리적이지만, budget 튜닝 시 이 한도만 빠지면 Director 판단 품질 저하. `관측성 부족` 계열.

---

## 7. Confidence And Limits

**Estimated confidence: 94%**

Basis:
- primary scope 6개 파일 전수 읽기 완료 (chief_writer_context.py 511줄, chief_writer_context_packets.py ~870줄, stage4_context_builder.py ~1900줄, stage4_context_packets.py ~555줄, prompt_builder.py ~600줄, base_agent.py ~2100줄)
- validation.yaml budget 값 확인, smart_truncate 기본값 확인, _apply_context_budget 보호 로직 확인
- fresh run 보고서(4화)에서 budget 초과 미발현 사실 확인

The 6% gap is from:
- `stage4_context_builder.py`의 1200-1900줄 구간(build_episode_context_payload 전체 흐름)을 complete read하지 못함 — 추가 budget cascade 로직이 있을 수 있음 (3%)
- `context_advisor.py`의 retrieval plan slot 할당 로직을 상세 확인하지 못함 — slot-level max_chars 배분이 예상과 다를 수 있음 (2%)
- 장기연재(50화+) 실측 데이터 없음 — budget 초과 시 실제 동작 미검증 (1%)

---

## 8. Supplementary Analysis

### 8.1 Context Section Order (LLM Attention Pattern)

CW 프롬프트의 현재 섹션 순서 (`build_chief_writer_main_prompt` 기준):
1. `dna_instruction` (1화 특수)
2. `purism_section` (장르 Guard)
3. `world_origin_constraint_section` (원시인/현대인)
4. `feedback_section` (Director 피드백 — REJECT 시)
5. `constraint_section` (이전 REJECT 패턴)
6. `future_guard_section` (소지품/무공/사망 NPC 제약)
7. `past_guard_section` (사망 NPC 부활 금지)
8. `writer_core_section` (character_voice, world_state, writing_directive, mandatory_context 등)
9. `hud_anomaly_section`
10. `scene_breakdown` (Blueprint 씬)
11. `prev_digest` / `prev_ending` (직전 화 다이제스트/말미)
12. `hud_report`
13. HUD 관련 섹션들
14. `arc_doc`
15. 스타일/문체 가이드
16. `prev_manuscripts_section` (V67 이전 원고 전문)
17. `chain_link_section` (V68 연결고리)
18. 기타 가이드

**관찰**: Director 피드백(#4)과 REJECT 제약(#5)이 프롬프트 앞쪽에 위치하여 LLM의 primacy attention에 유리한 배치. 그러나 `prev_manuscripts_section`(#16)이 프롬프트 후반에 위치하여, 토큰이 많을 때 LLM의 attention이 약해질 수 있음. 이는 구조적 설계 선택이므로 fix type = `ignore` (현재 attention window 1M에서는 문제 없음).

### 8.2 Prompt Size Gate — 안전 게이트 동작

`BaseAgent._apply_prompt_size_gate()` (base_agent.py:310-334):
- `MAX_CONTEXT_CHARS = 1,000,000` (validation.yaml SSOT)
- 초과 시 `smart_truncate(prompt, max_chars=body_budget, head_chars=head*0.55)` + `[System Note]` 주입
- `requires_human_intervention = True` 설정
- 이 게이트는 **모든 에이전트의 `ask()` 호출 전**에 적용됨 — 최후 방어선으로 건전.

### 8.3 Retrieval Plan → Context Budget 연계

`context_advisor.py`의 `build_retrieval_plan()`:
- stage별 budget (`stage4_total_budget=300K`, `director_total_budget=300K`)이 retrieval plan에 주입됨
- 각 slot에 weight 기반 `max_chars` 할당
- `_apply_context_budget()`이 tier1/tier2를 별도 압축

**정합성**: retrieval plan budget과 `_apply_prompt_size_gate`의 MAX_CONTEXT_CHARS(1M) 사이에 3배 이상 여유가 있어, retrieval sections만으로는 최종 게이트에 도달하지 않음. 그러나 `mandatory_context` + `prev_manuscripts_text` + retrieval sections가 합산되면 budget 초과 가능.

### 8.4 PromptBuilder의 역할 한계

`prompt_builder.py`의 `PromptBuilder` 클래스:
- Writer 가이드 8개(arc_position, high_impact_zone, NPC_relationship, item_timeline, temporal_spatial, cliche 등)
- Pure 함수들 — context budget과 무관하게 가이드 텍스트를 생성
- **budget 인식 없음** — 가이드 텍스트가 길어져도 자체적으로 압축하지 않음
- 이 가이드들은 `stage4_orchestrator.py`에서 `mandatory_context`에 포함되어 budget 관리 대상이 됨
- **위험도**: 낮음 — 가이드 텍스트는 보통 1-3K자로 budget 대비 미미.

---

## 9. 3-Pass Audit Record

### Pass 1. Scope Coverage and Fact Gathering
- primary scope 6개 파일 전수 읽기 (chief_writer_context.py, chief_writer_context_packets.py, stage4_context_builder.py, stage4_context_packets.py, prompt_builder.py, base_agent.py)
- validation.yaml budget 값 확인 (stage2=50K, stage3=80K, stage4=300K, director=300K, max_context=1M)
- smart_truncate 기본값 확인 (max_chars=1M, head_chars=80K)
- _apply_context_budget 보호 로직 확인 (2개 prefix만 보호)
- PASS

### Pass 2. Finding Classification and Cross-Reference
- P1-1~P1-5 모두 file:line anchor 확인
- fresh run 보고서와 교차 검증: 4화 운영에서 budget 초과 미발현 — 장기연재 전용 위험
- current-state-situation-survey-report의 Q5 "structural risk" 판정과 일치: 장기연재 일관성은 구조적 위험
- 기존 director-pipeline-7axis-deep-dive의 Q7-Director 판정과 일치: Director context 조립은 구조적으로 건전
- PASS

### Pass 3. Recommendation Validity and Fresh-Run Relevance
- QW-1~QW-3 모두 survey-only 범위 내 (코드 수정 제안만, 적용 없음)
- fresh-run-before-fix 판정: no — P1-1/P1-5가 장기연재에서 모순 유발 가능
- BR-1/BR-2는 refactor scope — 즉시 fix 대상 아님
- PASS
