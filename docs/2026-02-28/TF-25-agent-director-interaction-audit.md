# TF-25: Agent-Director 상호작용 구조 감사

> **날짜**: 2026-02-28
> **범위**: Stage 2/3/4 에이전트-디렉터 구조적 정합성 분석
> **코드 변경**: 없음 (읽기 전용 분석)
> **조사 항목**: 29건 (B-1: 6, B-2: 5, B-3: 10, C: 8)

---

## A. 요약

글도비 파이프라인은 Stage 2→3→4에서 **내각제**(에이전트 초안 제출 → Director 최종 판정) 구조를 사용한다. TF-24까지 결함 패치를 완료한 시점에서 **구조적 정합성**을 점검하여 발견한 TF 항목:

### TF 발견 요약

| TF ID | 등급 | 카테고리 | 제목 |
|-------|------|----------|------|
| TF-25-01 | **P0** | 구조 결함 | ASP 4번째 후보 — Director 미도달 + latent IndexError |
| TF-25-02 | **P1** | **대원칙 1+3** | QualityGate 90점 — Python이 Director PASS를 REJECT 오버라이드 |
| TF-25-03 | **P1** | 책임 경계 | Post-select (b) history_conflicts — 라운드 게이트 부재 |
| TF-25-04 | **P2** | 설정 위생 | 컨텍스트 Gate 3종 분산 — SSOT 부재 |
| TF-25-05 | **P2** | 주석 불일치 | `stage2_finalizer.py:99` "200K자 절삭" 주석 — 실제 상수 1M |
| TF-25-06 | **Obs** | 구조 분석 | Stage 3 Orchestrator 레벨 재시도 없음 |
| TF-25-07 | **P0** | **대원칙 3** | V60.43 — Python이 Director REJECT를 PASS로 오버라이드 |
| TF-25-08 | **P1** | **대원칙 1+3** | Stage 2 Pre-Director REJECT 체인 — Director 우회 6건 |
| TF-25-09 | **P2** | **대원칙 2** | ArcAutoCorrector — Python이 Arc 데이터 직접 수정 |

### LLM 호출 구조 맵

| Stage | 1회 시도 (LLM 호출) | 최대 재시도 | 에피소드당 최대 |
|-------|---------------------|------------|----------------|
| Stage 2 | 3~10회 | 5회 | 15~50회 |
| Stage 3 | 3~5회 | 10회 (내부) | 50회 |
| Stage 4 | 6~22회 | 5라운드 | ~63회 |
| **합계** | | | ~163회/에피소드 (최악) |

---

## B. 스테이지별 흐름 분석

### B-1. Stage 2 (Arc): FourPhaseArcGenerator ↔ Director

#### B-1-01: Director Audit 컨텍스트 구성

| 항목 | 값 |
|------|-----|
| **파일** | `stage2_finalizer.py:82-109` |
| **데이터** | 최근 30개 Arc의 `tactical_doc` 전문 |
| **추정 크기** | 30 × ~3,500자 = ~105,000자 |
| **Cap** | `ContextLimits.MAX_CONTEXT_CHARS` = 1,000,000자 |
| **부가 컨텍스트** | `story_context` ~5K자 + `last_refined_context` ~10K자 |
| **총합** | ~120,000자 (30 Arc 기준) |

```
구성:
  ┌─ story_context (~5K)
  ├─ last_refined_context (~10K)
  ├─ 30 Arc tactical_docs (~105K)  ← 지배적
  └─ STRATEGIC_AUDIT_PROMPT_V30 (~3K)
  합계: ~123K자
```

**[TF-25-05]** L99 주석과 L101 로그 메시지가 "200K자 절삭"이라고 표기하나, 실제 상수는 `ContextLimits.MAX_CONTEXT_CHARS = 1,000,000` (1M). 주석-코드 불일치.

**구조 평가**: Arc 수가 30 미만이면 자연스럽게 축소. 30 이상에서 성장 정지. 구조적으로 안전.

---

#### B-1-02: Self-Consistency 투표 구조

| 항목 | 값 |
|------|-----|
| **파일** | `director_auditor.py:880-1026` |
| **Ambiguous 구간** | 점수 50~60 (`director.py:45-46`) |
| **Clear PASS** | score > 60 → 1 LLM 호출로 즉시 종료 |
| **Clear REJECT** | score < 50 → 1 LLM 호출로 즉시 종료 |
| **Ambiguous** | 2 추가 LLM 호출 (temperature 0.15, 0.20) → **총 3회** |
| **병렬 처리** | ThreadPoolExecutor(max_workers=2) — 추가 2회 병렬 |

**참고**: Stage 4에는 별도의 Self-Consistency 시스템이 존재 (`validation.yaml:123-125`, `ambiguous_lower: 70`, `ambiguous_upper: 85`, soft_margin: 2). Stage 2와 Stage 4의 ambiguous 구간이 다름.

**구조 평가**: Ambiguous 구간이 11점(50~60)으로 좁아 활성화 빈도 낮음. 추가 2회는 `thinking_level="low"`로 연산량 경감. 설계 건전.

---

#### B-1-03: Pre-Director 검증 vs Director 체크 항목 대조

| # | Pre-Director 검증 (Python/LLM) | 파일:라인 | Director 프롬프트 관계 |
|---|-------------------------------|-----------|----------------------|
| 1 | DraftValidator (1차 수집) | `stage2_validation_pipeline.py:64-86` | 낮은 중복 |
| 2 | SelfReflector (LLM) | `:91-127` | 없음 (Analyst 전용) |
| 3 | Consensus (3× LLM) | `:132-169` | 없음 (사전 투표) |
| 4 | Mapping Validation | `:183-189` | 낮은 중복 |
| 5 | Auto-Corrector | `:192-206` | 없음 (자동 수정) |
| 6 | ConstraintDB 중복 감지 | `:209-226` | **의도적 에스컬레이션** → Director |
| 7 | Flow Guard + NarrativeAnalyzer (LLM) | `:228-294` | Director Step 3,4와 영역 겹침 (서사 파편화, 페이싱) |
| 8 | Duplicate Guard | `:296-309` | Director Step 3와 영역 겹침 (서사 파편화) |
| 9 | DraftValidator (2차 전체) | `:329-465` | 부분 중복 (구조 검증) |
| 10 | ContinuityInspector (LLM) | `:473-657` | Director Step 0,1과 영역 겹침 (내부 모순, 상태 연속성) |

**Director 고유 체크 항목** (Pre-Director에 없는 것):
- Entity 이름 일관성 (L777-791)
- 주인공 이름 하드 가드 (L793-814)
- 종합적 창작 판단 (점수화)

**구조 평가**: ContinuityInspector(LLM)와 Director Step 0-1은 동일 도메인(NPC 생사, 아이템, 관계 일관성)을 각각 독립적으로 검사. "Python은 수집만, 판단은 LLM이" 원칙에 따른 의도적 계층화. ContinuityInspector는 **경고 수집**, Director는 **최종 판정** — 역할이 명확히 분리되어 있으므로 구조적 문제 아님.

---

#### B-1-04: QualityGate 90점 vs Director 프롬프트 PASS 기준

| 항목 | 값 |
|------|-----|
| **파일** | `stage2_finalizer.py:200-217` |
| **QualityGate** | Director PASS + score < 90 + `tactical_doc` ≥ 1,500자 → **REJECT 오버라이드** |
| **Director 프롬프트** | PASS/REJECT에 대한 명시적 점수 임계값 없음. "80% 핵심 맥락 반영 + 치명 오류 없으면 PASS" (관대 지침, `director.yaml:457`) |

```
구조적 불일치:
  Director 프롬프트: score 0~100 출력하되, PASS/REJECT은 정성적 판단
    → "핵심 맥락 80% 반영 + 치명 오류 없으면 PASS" (정성 기준)
  QualityGate (Python): score < 90이면 PASS → REJECT 오버라이드 (정량 기준)

  Director가 PASS + score 75를 출력하면:
    → Python이 REJECT 오버라이드 → Director 판정 무효화
```

**[TF-25-02]** Director 프롬프트에 명시적 점수 임계값이 없어서, Director LLM은 자신의 PASS 판정이 score 90 이상이어야 유효하다는 것을 인지하지 못함. Stage 3은 Director 프롬프트에 "80점 미만 REJECT"을 명시하여 QualityGate(80)와 정렬됨 — 이것이 구조적으로 올바른 패턴.

---

#### B-1-05: 재시도 루프 LLM 호출 추적

| 항목 | 값 |
|------|-----|
| **파일** | `stage2_orchestrator.py:418` |
| **최대 시도** | 5회 (`retry.analyst_max_attempts: 5`) |
| **피드백 라우팅** | Director REJECT → `re_slice_instruction` + `reject_reason` + `intensity_guide` → FourPhaseArcGenerator |

**시도당 LLM 호출:**

| 경로 | 호출 수 | 구성 |
|------|---------|------|
| **최선** (FourPhase + Clear PASS) | **3회** | FourPhase(1) + ContinuityInspector(1) + Director(1) |
| **일반** (FourPhase + 일부 검증) | **4~9회** | FourPhase(1-4) + NarrativeAnalyzer(1) + ContinuityInspector(1) + Director(1-3) |
| **최악** (Analyst + 전체 발동) | **10회** | SelfReflector(1) + Consensus(3) + NarrativeAnalyzer(1) + ArcCorrector(1) + ContinuityInspector(1) + Director SC(3) |

5회 재시도 총합: 15~50 LLM 호출/Arc.

---

#### B-1-06: Entity Registry 캐시 여부

| 항목 | 값 |
|------|-----|
| **파일** | `stage2_preflight.py:652-689` |
| **캐시 키** | `cumulative_state_cache_key = arc_count` |
| **결론** | **캐시됨** — 재시도 루프 내 `all_refined_arcs` 불변 → 캐시 히트 |

```python
if self.ctx.cumulative_state_cache_key == arc_count:
    state_result = self.ctx.cumulative_state_cache       # CACHE HIT
else:
    state_result = state_extractor.extract_cumulative_state(all_refined_arcs)
    self.ctx.cumulative_state_cache = state_result       # CACHE STORE
```

`extract_cumulative_state`는 LLM 호출. 캐싱으로 재시도 간 불필요한 재계산 방지. 정상 설계.

---

### B-2. Stage 3 (Blueprint): BlueprintEnsemble ↔ Director

#### B-2-01: NO-RETRY 설계

| 항목 | 값 |
|------|-----|
| **파일** | `stage3_orchestrator.py:736-795`, `three_phase_blueprint_generator.py:59-470` |
| **내부 재시도** | 10회 (`max_retries=9`, L166) |
| **오케스트레이터 재시도** | **0회** — 실패 시 `break: True` (L791) |
| **설계 의도** | "후속 에피소드는 현재 Blueprint에 의존하므로 건너뛰기 금지" |

**내부 재시도당 LLM 호출:**

| Phase | 호출 | 비고 |
|-------|------|------|
| Phase 1 (Constraint) | 0 | Python 전용, 첫 호출 후 캐시 |
| Phase 2 (Generate) | 3 (앙상블) 또는 1 (InPlace) | score ≥ 60이면 InPlace(1) |
| Phase 3 (Validate) | 2 | 연속성(1) + Director 비교선택(1) |
| **합계** | **3~5회** | |

**비상 폴백** (L455-464): 전 시도 실패 시 최고 점수 Blueprint가 `REWRITE`(50점) 이상이면 `PASS_WITH_WARNING` 반환 — 완전 실패 방지.

**[TF-25-06]** 현재 Orchestrator 레벨 재시도가 없어 내부 10회 전 실패 시 `break: True`. `PASS_WITH_WARNING` 폴백이 완전 실패를 방지하므로 현재 위험도는 낮음. 향후 전략 변경(treatment_block 재조합, constraint 완화 등) 후 1회 재시도 옵션 고려 가능.

---

#### B-2-02: Blueprint Director 판정 컨텍스트 구성

| 항목 | 값 |
|------|-----|
| **파일** | `director_ensemble.py:115-173` |
| **Arc tactical (에피소드 단위)** | ~3,000~6,000자 (L80, `[:6000]` 캡) |
| **이전 엔딩** | ~100~300자 |
| **3개 후보 Blueprint** | 3 × ~3,000~5,000자 = ~9,000~15,000자 |
| **프롬프트 템플릿** | ~3,500자 (고정) |
| **총합** | ~16,000~25,000자 |

`prev_manuscripts_text`가 Blueprint Director에 전달되지 않아 Stage 4 Director 대비 컨텍스트가 10배 이상 가벼움. `thinking_level="high"` 사용.

---

#### B-2-03: QualityGate 80점 vs 90점 — 의도 확인

| 항목 | 값 |
|------|-----|
| **파일** | `validation.yaml:34-35` |
| **Stage 2/4** | `quality_gate_score: 90` |
| **Stage 3** | `blueprint_quality_gate_score: 80` |

```yaml
scoring:
  quality_gate_score: 90              # Stage 2 Arc / Stage 4 원고
  blueprint_quality_gate_score: 80    # Stage 3 Blueprint 전용 — Director 프롬프트 "80점 미만 REJECT" 기준과 일치
```

**의도**: 명시적. Director 프롬프트에 "총점 65점 이상이면 PASS"(`director.yaml` `DIRECTOR_AUDIT_PROMPT_V30`)가 있고, QualityGate는 80점. 프롬프트와 Gate가 각각 역할을 가짐 — **Stage 2/4와 달리 Director 프롬프트에 점수 기준이 명시**되어 있어 구조적으로 정렬됨.

---

#### B-2-04: Treatment Block → Director 경로

| 항목 | 값 |
|------|-----|
| **파일** | `stage3_orchestrator.py:522-579` |
| **소스** | `master_bible.MasterBible.plot_roadmap[arc_idx]` |
| **필드** | title, emotional_beat, foreshadow, power_shift, event_villain, solution, reward, content.*, genre_ext |
| **Director 도달** | **아니오** — Blueprint **생성기**에만 전달 |

```
Treatment Block 경로:
  stage3_orchestrator → three_phase_bp.generate(semantic_context=_tb_text)
    → BlueprintEnsembleGenerator.generate_ensemble(feedback=_tb_text)
      → LLM 후보 생성 [O]
    → Director.compare_and_select_blueprint()
      → Treatment Block 미포함 [X]
```

Treatment Block이 후보 생성에만 영향을 미치고 Director 판정에는 포함되지 않음. Director가 Treatment 이행률을 직접 대조할 수 없으나, 후보 Blueprint에 Treatment 내용이 반영되어 있으므로 간접적으로 검증됨. 현재 구조에서는 의도적 설계.

---

#### B-2-05: 30화 원고 전문 로드

| 항목 | 값 |
|------|-----|
| **파일** | `stage3_orchestrator.py:582-598` |
| **로드** | `db.get_recent_manuscripts(limit=30)` |
| **추정 크기** | 30 × ~5,000~10,000자 = ~150,000~300,000자 |
| **Cap** | `ContextLimits.MAX_CONTEXT_CHARS` = 1,000,000자 |
| **Director 도달** | **아니오** — Blueprint **생성기**에만 전달 |

B-2-04와 동일 패턴 — Director는 생성된 후보만 평가. 원고 전문은 생성기 LLM 컨텍스트에 투입되어 연속성 있는 Blueprint 생성을 지원.

---

### B-3. Stage 4 (Manuscript): ChiefWriter ↔ Director

#### B-3-01: Advisory 6종 LLM 호출 구조

| # | Advisory | LLM 호출 | 조건 | 후보당 | 라운드당 |
|---|---------|---------|------|--------|---------|
| 1 | **TruthGate** | Python 6 + LLM 1 (world_law) | 항상 | 0~1 | 0~3 |
| 2 | **NpcDriftAdvisor** | LLM 1 (batch check) | NPC 스냅샷 존재 시 | 1 | 0~3 |
| 3 | **NumericDriftAdvisor** | LLM 1 (batch check) | **ep % 5 == 0** 시만 | N/A | 0~1 |
| 4 | **FlashbackVerifier** | LLM 1 | 회상 마커 감지 시 | 1 | 0~3 |
| 5 | **InfoParadoxChecker** | LLM 1 | **1인칭 전용** | 1 | 0~3 |
| 6 | **RelationshipDriftAdvisor** | LLM 1 | ep ≥ 5 + 이력 존재 시 | 1 | 0~3 |

```
라운드당 Advisory LLM 호출:
  최소: 0 (ep 1, 3인칭, 회상 없음)
  일반: 9 (TruthGate 3 + NpcDrift 3 + RelDrift 3)
  최대: 16 (전 조건 활성화: 3+3+1+3+3+3)
```

Advisory 호출은 `director.ask(temperature=0.1)`을 사용. 각 Advisory는 조건부 활성화 게이트를 갖추고 있어 불필요한 호출 방지. 설계 건전.

---

#### B-3-02: Director 컨텍스트 구성 (Stage 4)

| 구분 | 컴포넌트 | 추정 크기 | 안정성 |
|------|---------|----------|--------|
| **Stable** | prev_manuscripts_text | ~150K~300K자 | 에피소드 내 불변 |
| | blueprint | ~5K~15K자 | 에피소드 내 불변 |
| | episode_digest | ~2K~5K자 | 에피소드 내 불변 |
| | previous_ending | ~1K~3K자 | 에피소드 내 불변 |
| | story_context | ~5K~20K자 | 프로젝트 내 불변 |
| | 프롬프트 템플릿 | ~1.5K자 | 항상 불변 |
| **Stable 소계** | | **~165K~345K자** | Context Caching 적용 (600초 TTL) |
| **Variable** | 3 후보 원고 | 3 × ~5K~15K = ~15K~45K자 | 매 라운드 변경 |
| | Python 경고 (3후보분) | ~500~3,000자 | 매 라운드 변경 |
| | mandatory_context (advisory + feedback) | ~2K~40K자 | 매 라운드 변경 |
| | ENSEMBLE_VARIABLE_PROMPT 템플릿 | ~8K자 | 고정 |
| **Variable 소계** | | **~26K~96K자** | 캐싱 불가 |
| **총합** | | **~191K~441K자** | |

Stable 부분은 Context Caching으로 에피소드 내 1회만 전송. 이후 라운드는 Variable 부분만 추가 전송. Stable/Variable 분리 구조가 잘 설계됨.

---

#### B-3-03: mandatory_context 조립 구조

`_director_mc_parts` 조립 순서 (`stage4_interview_round.py:824-1053`):

```
조립 순서 (insert(0) = 역순):
  ① mandatory_context (StateTracker 기본)     ~5K-20K자   [base, index 0]
  ② TruthGate 경고                           ~200-1K자    [insert(0)]
  ③ NpcDriftAdvisor 경고                      ~200-500자   [insert(0)]
  ④ NumericDriftAdvisor 경고                  ~200-500자   [insert(0)]
  ⑤ FlashbackVerifier 경고                    ~200-500자   [insert(0)]
  ⑥ InfoParadoxChecker 경고                   ~200-500자   [insert(0)]
  ⑦ RelationshipDriftAdvisor 경고             ~200-500자   [insert(0)]
  ⑧ Python validation 경고 (3후보)            ~500-3K자    [append]
  ⑨ Director feedback (이전 라운드)            ~200-2K자    [append]
  ⑩ Strategy win rates                        ~200-500자   [append]

최종 순서 (insert(0) 역전):
  [0] RelationshipDriftAdvisor
  [1] InfoParadoxChecker
  [2] FlashbackVerifier
  [3] NumericDriftAdvisor
  [4] NpcDriftAdvisor
  [5] TruthGate
  [6] mandatory_context (원본)
  [7] Python validation 경고
  [8] Director feedback
  [9] Strategy win rates

Cap: director_mandatory_max = 40,000자 (director_ensemble.py:433)
```

일반적 총합: ~12K~55K자. Cap(40K) 초과 시 뒤쪽(Python 경고, Director feedback, win rates)부터 절삭 — Advisory 경고(앞쪽 insert)는 보존.

Advisory 경고는 매 라운드 재생성(비누적). `director_feedback`만 라운드 간 누적 가능(L1296-1344).

---

#### B-3-04: Post-select 추가 LLM 호출

| 항목 | 값 |
|------|-----|
| **파일** | `stage4_interview_round.py:1149-1208` |

**2개 검사의 발동 조건이 다름:**

| 검사 | 조건 | 라운드 제한 |
|------|------|-----------|
| **(a) 연속성 검사** `check_manuscript_continuity_with_cache` | `round_num == 0 AND next_ep > 1 AND final_manuscript` | **Round 0만** |
| **(b) 이력 충돌 검사** `check_manuscript_history_conflicts` | `_prev_manuscripts_text AND final_manuscript AND hasattr(director, method)` | **제한 없음** — 매 PASS마다 실행 |

**[TF-25-03]** 검사 (b)는 라운드/에피소드 게이트가 없어 모든 PASS 판정 시 실행됨. Director가 `prev_manuscripts_text`를 포함한 컨텍스트로 이미 판정한 직후 동일 원고를 별도 프롬프트로 재검증하는 구조. 검사 (a)는 Round 0 한정이므로 제한적.

**구조적 논점**: Director 본 판정에서 이미 수행하는 9항목 모순 체크와 (b) 이력 충돌 검사의 책임 경계가 불명확. Director 판정 프롬프트에 이력 충돌 검사 항목을 통합하거나, (b)에도 라운드 게이트를 적용하는 것이 구조적으로 명확함.

---

#### B-3-05: QualityGate 90점 — Director 주권 정합성

| 항목 | 값 |
|------|-----|
| **파일** | `stage4_interview_round.py:1134-1141` |
| **동작** | Director PASS + score < 90 → **Python이 REJECT 오버라이드** |

```python
if verdict == "PASS" and score < _quality_gate_score:
    verdict = "REJECT"  # Python이 Director PASS를 무효화
```

**Stage별 비교**:

| Stage | QualityGate | Director 프롬프트 점수 기준 | 정렬 여부 |
|-------|-------------|--------------------------|----------|
| Stage 2 | 90 | 명시적 임계값 없음 ("80% 핵심 맥락" 정성 기준) | **미정렬** [TF-25-02] |
| Stage 3 | 80 | "총점 65점 이상이면 PASS" 명시 | **정렬됨** (모범 패턴) |
| Stage 4 | 90 | 명시적 임계값 없음 (가중 채점만) | **미정렬** [TF-25-02] |

Stage 3이 QualityGate-Director 프롬프트 정렬의 모범 패턴. Stage 2/4는 Director 프롬프트에 "score 90 이상이어야 PASS가 유효하다"는 정보가 없어, Director LLM이 자신의 PASS 판정 조건을 정확히 인지하지 못하는 구조.

---

#### B-3-06: CW-Director prev_manuscripts 구조

| 수신자 | 전달 경로 | 역할 |
|--------|----------|------|
| CW (3회, 전략별 병렬) | `_common_writer_kwargs["prev_manuscripts_text"]` | 연속성 있는 원고 **생성** 참조 |
| Director (1회) | `select_and_judge_ensemble(prev_manuscripts_text=...)` | 연속성 **검증** 참조 |

CW와 Director가 동일 `prev_manuscripts_text`를 수신하는 것은 구조적으로 불가피 — CW는 연속성 있는 원고를 생성하기 위해, Director는 생성된 원고의 연속성을 검증하기 위해 각각 필요. Director는 Context Caching(600초 TTL)으로 Stable 부분을 에피소드 내 1회만 전송.

**CW의 prev_manuscripts 역할 분석**: CW는 직전 원고의 문체/톤/엔딩을 이어받아 자연스러운 연결을 생성. 30화 전문이 필요한 것은 장기 복선/캐릭터 아크 참조를 위함이나, 실제 생성 시 주로 직전 2~3화를 참조. Director는 장기 모순 검증을 위해 30화가 필요. 역할에 따른 적정 윈도우 크기가 다를 수 있음.

---

#### B-3-07: 3계층 검증 대조표 (Python Validator / Advisory / Director)

| 검증 도메인 | Python Validator | Advisory 체인 | Director 프롬프트 | 계층 수 |
|------------|-----------------|--------------|-----------------|--------|
| **사망 NPC 활동** | `blocking_validator` | `TruthGate` | 항목 3 | 3 |
| **미소유 아이템** | `blocking_validator` | `TruthGate` | 항목 4 | 3 |
| **수치 연속성** | `consistency_validator` (부분) | `NumericDriftAdvisor` | 항목 2,7 | 3 |
| **NPC 속성 표류** | — | `NpcDriftAdvisor` | 항목 1 (일반) | 2 |
| **타임라인 정합성** | `continuity_validator` (부분) | — | 항목 6 | 2 |
| **Blueprint 커버리지** | `manuscript_validator` | — | 채점 기준 2 (20%) | 2 |
| **분량 준수** | `manuscript_validator` | — | 채점 기준 4 (10%) | 2 |
| **파괴된 장소** | — | `TruthGate` | — | 1 |
| **스킬 중복** | — | `TruthGate` | — | 1 |
| **카르마 범위** | — | `TruthGate` | — | 1 |
| **NPC 역할 일관성** | — | `TruthGate` | — | 1 |
| **세계 법칙 위반** | — | `TruthGate` (LLM) | — | 1 |
| **관계 표류** | — | `RelationshipDriftAdvisor` | — | 1 |
| **회상 오염** | — | `FlashbackVerifier` | — | 1 |
| **정보 역설** | — | `InfoParadoxChecker` | — | 1 |
| **문장 품질** | — | — | 채점 기준 3 (20%) | 1 (Director 고유) |

**3계층 검증 항목**: 사망 NPC, 미소유 아이템, 수치 연속성. 각 계층의 역할:
- **Python**: 빠른 결정론적 차단 (blocking), Director 전 단계에서 실행
- **Advisory**: 구조화된 LLM advisory → mandatory_context로 Director에 전달
- **Director**: 전체 컨텍스트를 보고 최종 판정

이는 의도적 방어 심층(defense-in-depth) 구조. Python이 명백한 위반을 먼저 차단하고, Advisory가 구조적 분석을 수행하며, Director가 종합 판단. 각 계층이 다른 방식(결정론적/LLM advisory/LLM 판정)으로 접근하므로 동일 도메인이지만 상호 보완적.

---

#### B-3-08: Patch Mode 3단계 구조

| 단계 | 조건 | LLM 호출 | 방식 |
|------|------|---------|------|
| **InPlace** | `fix_scope == "inplace"` 또는 score ≥ 60 | **1회** | 단일 수정 |
| **Patch** | InPlace 실패 또는 `fix_scope == "partial"` | **3회** | 앙상블 (원본 보존) |
| **Rewrite** | Patch 실패 또는 `fix_scope == "full"` | **3회** | 앙상블 (전면 재작성) |

```
Cascade (1라운드 내):
  InPlace 성공 → 1 LLM
  InPlace 실패 → Patch 시도 → fallback 3 LLM
  Patch 실패 → Rewrite → fallback 3 LLM
```

Director의 `fix_scope` 출력이 Patch 단계를 직접 결정하는 구조. Director 주권을 존중하면서 수정 범위를 최적화. 설계 건전.

---

#### B-3-09: ASP 4번째 후보 — Director 미도달

| 항목 | 값 |
|------|-----|
| **파일** | `stage4_interview_round.py:227-250`, `director_ensemble.py:335-390` |
| **활성화** | Round 3+ (`round_num >= 2`) + previous_attempt 존재 |
| **LLM 호출** | 2~3회 (attacker + defender + merge) |

**[TF-25-01] 구조 결함:**

```
ASP 후보 생성:
  candidates.append({"manuscript": _asp_manuscript, "strategy": "asp_correction"})
  → index 3에 추가

Director 프롬프트 구성 (director_ensemble.py:379-390):
  info_a = get_candidate_info(0)  # 후보 A
  info_b = get_candidate_info(1)  # 후보 B
  info_c = get_candidate_info(2)  # 후보 C
  # index 3 → 참조 안 됨 (하드코딩 A/B/C)

LLM 선택 매핑 (director_ensemble.py:553-554):
  selected_idx = {"A": 0, "B": 1, "C": 2}.get(selected_letter, 0)
  # "D" 매핑 없음 → index 3 선택 불가
```

**추가 발견 — latent IndexError** (`director_ensemble.py:372`):
```python
logging.info(f"... ({[['A', 'B', 'C'][i] for i in qualified_indices]})")
```
`qualified_indices`에 index 3이 포함되면 `['A','B','C'][3]`에서 `IndexError` 발생. ASP 후보가 `MIN_MANUSCRIPT_LENGTH`를 충족하면 이 경로에 진입 가능.

**영향**: ASP 모듈이 LLM 호출(2~3회)을 수행하고 Python Validation도 통과하나, Director에 도달하지 않아 선택될 수 없는 구조. 또한 `qualified_indices` 로깅에서 잠재적 런타임 오류.

**권고**: (a) ASP 후보를 기존 3후보 중 하나(예: 최저 점수)와 교체하여 Director에 전달, 또는 (b) Director를 4후보 지원으로 확장, 또는 (c) ASP 비활성화.

---

#### B-3-10: 라운드 LLM 호출 구조 집계

| 컴포넌트 | Round 0 | Round 1 (InPlace) | Round 3+ |
|---------|---------|-------------------|----------|
| CW 후보 생성 | 3 | 1 | 3 + 2~3 (ASP, 단 미사용) |
| TruthGate (world_law) | 0~3 | 0~3 | 0~3 |
| NpcDriftAdvisor | 0~3 | 0~3 | 0~3 |
| NumericDriftAdvisor | 0~1 | 0~1 | 0~1 |
| FlashbackVerifier | 0~3 | 0~3 | 0~3 |
| InfoParadoxChecker | 0~3 | 0~3 | 0~3 |
| RelationshipDriftAdvisor | 0~3 | 0~3 | 0~3 |
| Director 판정 | 1 | 1 | 1 |
| Post-select (a) | 0~1 | 0 | 0 |
| Post-select (b) | 0~1 | 0~1 | 0~1 |
| ToT/MAD (REJECT 시) | 0~2 | 0~2 | 0~2 |
| **합계** | **5~24** | **2~21** | **5~23** (+ASP 2~3 미사용) |

```
에피소드당 (5라운드, 일반 3인칭 ep 12 기준):
  Round 0: ~15
  Round 1~4: ~12 × 4 = ~48
  총합: ~63 LLM 호출/에피소드
```

---

## C. 크로스 스테이지 구조 분석

### C-1. 컨텍스트 구성

#### C-1-01: 스테이지별 컨텍스트 구성표

| Stage | 컴포넌트 | 추정 크기 (자) | Cap 메커니즘 |
|-------|---------|--------------|-------------|
| **Stage 2** | 30 Arc tactical_doc | ~105K | `ContextLimits.MAX_CONTEXT_CHARS` (1M) |
| | story_context | ~5K-20K | — |
| | last_refined_context | ~5K-15K | — |
| | AUDIT_PROMPT 템플릿 | ~3K | 고정 |
| | **Stage 2 총합** | **~118K-143K** | |
| **Stage 3 생성기** | 30 prev_manuscripts | ~150K-300K | `ContextLimits.MAX_CONTEXT_CHARS` (1M) |
| | treatment_block | ~2K-10K | — |
| | constraint_block | ~5K-15K | — |
| | **Stage 3 생성기 총합** | **~157K-325K** | |
| **Stage 3 Director** | Arc tactical + 3 후보 + 템플릿 | ~16K-25K | — |
| **Stage 4 CW** | prev_manuscripts | ~150K-300K | `smart_truncate` (1M) |
| | blueprint + bible + HUD 등 | ~30K-50K | — |
| | **CW 총합** | **~180K-350K** | |
| **Stage 4 Director** | prev_manuscripts (Stable) | ~150K-300K | `BaseAgent.MAX_CONTEXT_CHARS` (700K, system.yaml) |
| | blueprint + digest + context (Stable) | ~15K-45K | — |
| | 3 후보 + mandatory + template (Variable) | ~26K-96K | `director_mandatory_max` (40K) |
| | **Director 총합** | **~191K-441K** | |

---

#### C-1-02: CW vs Director 컨텍스트 구조 분석

| 항목 | CW | Director | 공통 |
|------|-----|---------|------|
| prev_manuscripts_text | ~150K자 × 3 전략 | ~150K자 × 1 | 동일 원본 |
| blueprint | ~10K | ~10K | 동일 원본 |
| story_context | ~10K | ~10K | 동일 원본 |

CW와 Director가 동일 데이터를 필요로 하는 것은 구조적으로 불가피 — CW는 **생성 참조**, Director는 **검증 참조**로 역할이 다름.

**완화 구조**: Director는 Context Caching(600초 TTL, `director_ensemble.py:505`)으로 Stable 부분을 에피소드 내 1회만 전송. CW는 현재 캐싱 미적용이나, 생성기는 매 라운드 다른 전략을 사용하므로 Variable 부분의 비율이 높아 캐싱 효과가 제한적일 수 있음.

---

#### C-1-03: 컨텍스트 Gate 구조 분석

| Gate | 위치 | 값 | 소스 | 용도 |
|------|------|-----|------|------|
| `ContextLimits.MAX_CONTEXT_CHARS` | `constants.py:132` | 1,000,000 | 하드코딩 | `smart_truncate` 상한 |
| `BaseAgent.MAX_CONTEXT_CHARS` | `base_agent.py:148` | 700,000 | `system.yaml:19` (`api.max_context_chars`) | Director Stable budget |
| `director_mandatory_max` | `director_ensemble.py:433` | 40,000 | `_threshold("context.director_mandatory_max", 40000)` | mandatory_context cap |

```
Gate 체계:
  smart_truncate(1M) → 개별 텍스트 필드 절삭
  BaseAgent(700K) → Director Stable+Variable 합산 budget
  mandatory_max(40K) → mandatory_context 단독 cap
```

**[TF-25-04]** 세 Gate가 서로 다른 위치에 분산 정의되어 있으며 단일 SSOT가 없음:
- `ContextLimits.MAX_CONTEXT_CHARS`는 `constants.py`에 하드코딩
- `BaseAgent.MAX_CONTEXT_CHARS`는 `system.yaml`에서 로드
- `director_mandatory_max`는 `_threshold()`로 `validation.yaml`에서 로드

**위험 시나리오** (ep 200, 원고 평균 15K자):
- 30 × 15K = 450K → `smart_truncate` 미발동 (< 1M)
- Director: 450K(Stable) + 96K(Variable) = 546K → 700K gate 미발동
- 안전하지만 여유 154K만 남음

**결론**: 30화 윈도우로 에피소드 수에 비례한 성장은 방지됨. Gate들이 각각 다른 역할(필드/합산/구간)을 가지므로 값 자체의 통일은 불가하지만, **정의 위치를 SSOT로 통합**하는 것이 설정 관리상 바람직.

---

### C-2. 검증 계층 구조

#### C-2-01: 3계층 검증 매트릭스

```
범례: ■ 검사함  □ 검사 안 함  ▲ 부분 검사

검증 도메인          | Python | Advisory | Director | 계층 수
─────────────────────┼────────┼──────────┼──────────┼────────
사망 NPC 활동        |   ■    |    ■     |    ■     |   3
미소유 아이템        |   ■    |    ■     |    ■     |   3
수치 연속성          |   ▲    |    ■     |    ■     |   3
NPC 속성 표류        |   □    |    ■     |    ▲     |   2
타임라인 정합성      |   ▲    |    □     |    ■     |   2
Blueprint 커버리지   |   ■    |    □     |    ■     |   2
분량 준수            |   ■    |    □     |    ■     |   2
파괴된 장소          |   □    |    ■     |    □     |   1
스킬 중복            |   □    |    ■     |    □     |   1
카르마 범위          |   □    |    ■     |    □     |   1
NPC 역할 일관성      |   □    |    ■     |    □     |   1
세계 법칙 위반       |   □    |    ■     |    □     |   1
관계 표류            |   □    |    ■     |    □     |   1
회상 오염            |   □    |    ■     |    □     |   1
정보 역설            |   □    |    ■     |    □     |   1
문장 품질            |   □    |    □     |    ■     |   1 (고유)
```

3계층 항목(사망 NPC, 미소유 아이템, 수치 연속성)은 각 계층이 다른 방법론으로 접근:
- Python: 패턴 매칭 기반 결정론적 검사 → 확실한 위반 즉시 차단
- Advisory: LLM 기반 구조적 분석 → 맥락 의존적 위반 감지 → 경고 텍스트 생성
- Director: 전체 컨텍스트 포함 LLM 판정 → 최종 판정권

이 구조는 "Python은 수집만, 판단은 LLM이" 대원칙을 준수하면서 방어 심층을 제공.

---

#### C-2-02: Python 경고 → Director 라우팅 구조

```
조립 (stage4_interview_round.py L824-1053):
  _director_mc_parts = [mandatory_context]

  Advisory 6종 → insert(0) (역순으로 앞에 삽입)
  Python 경고   → append (뒤에 추가)
  Director FB   → append
  Strategy rates → append

  → "\n\n".join() → _director_mandatory_context

Director 프롬프트 (director.yaml):
  "Python advisory에서 CRITICAL 경고가 1건이라도 있으면 → auto REJECT"

흐름:
  Python 결정론적 플래그 → mandatory_context에 텍스트 주입
  → Director가 텍스트로 읽고 auto-REJECT 규칙 적용
  → Director 자체 9항목 체크도 독립적으로 동일 이슈 감지 가능
```

**insert(0) 순서 효과**: Advisory 경고가 mandatory_context 앞쪽에 위치하여, 40K cap 적용 시 Advisory가 보존되고 뒤쪽 Python 경고/Director feedback이 절삭됨. Advisory 경고가 Director 판정에 더 높은 우선순위를 가지는 구조.

**구조 평가**: Python 경고를 텍스트로 Director에 전달하고, Director 프롬프트에 auto-REJECT 규칙을 두어 "Python은 수집, Director는 판단" 원칙을 유지. 정상 설계.

---

### C-3. 피드백 루프 구조

#### C-3-01: Stage 2 Director REJECT → FourPhase 피드백 라우팅

| 구성요소 | 소스 | 추정 크기 |
|---------|------|----------|
| `reject_reason` | Director LLM 자유 텍스트 | ~50-200자 |
| `re_slice_instruction` | Director LLM 수정 지시 | ~100-300자 |
| `intensity_guide` | Python 적응형 (시도 횟수 기반) | ~200-400자 |
| **합계** | | **~350-900자** |

```
피드백 경로:
  Director REJECT
    → stage2_finalizer.py L603-642: 피드백 구성
    → stage2_orchestrator.py L507-509: current_feedback 갱신
    → stage2_preflight.py: FourPhaseArcGenerator에 전달
    → FourPhaseArcGenerator.generate(feedback=...)
```

`re_slice_instruction`은 Director LLM이 생성하는 자유 텍스트. 구조화된 템플릿 없이 LLM 재량에 의존. 폴백 기본값 "밀도 보강 필요"(`L603`)는 구체성이 낮으나, Director가 `re_slice_instruction` 필드를 출력하도록 프롬프트에 명시되어 있어 일반적으로는 구체적 지시가 생성됨.

---

#### C-3-02: Stage 4 Director REJECT → CW fix_scope 매핑

| fix_scope | Director 정의 | Patch 단계 | LLM 호출 |
|-----------|-------------|-----------|---------|
| `"inplace"` | "고유명사/수치 오류 등 국소 수정" | InPlace | 1 |
| `"partial"` | "구조 유지 + 일부 씬/문단 재작성" | Patch (앙상블) | 3 |
| `"full"` | "원고 전면 폐기 후 재작성" | Rewrite (앙상블) | 3 |

```
Director REJECT JSON → fix_scope → Patch 단계 결정:
  score ≥ 60: InPlace (1 LLM)
  score ≥ 50: Patch (3 LLM)
  score < 50: Rewrite (3 LLM)
```

3단계 캐스케이드(InPlace → Patch → Rewrite)로 Director의 `fix_scope` 판정이 직접 수정 범위를 결정. Director 주권을 존중하면서 수정 깊이를 최적화하는 구조. 설계 건전.

---

#### C-3-03: Stage 3 내부 재시도 피드백 눈덩이(Snowball) 분석

| 항목 | 값 |
|------|-----|
| **파일** | `three_phase_blueprint_generator.py:164-173` |
| **Anti-snowball** | `[TF-S3-04]` — 명시적 방지 구현 |
| **메커니즘** | 매 재시도 시 `_initial_feedback`으로 리셋 |

```python
_initial_feedback = feedback                    # L164: 초기값 보존
for retry in range(max_retries + 1):            # L166
    _attempt_feedback = _initial_feedback       # L168: 매 시도 리셋
    _strategy_feedback = _build_strategy_feedback()
    if _strategy_feedback:
        _attempt_feedback = f"{_initial_feedback}\n\n{_strategy_feedback}"
```

피드백 크기 추이:
- Retry 0: ~500자 (초기 피드백만)
- Retry 1~9: ~800자 (초기 + 직전 시도 점수/경고, 이전 retry 데이터 미포함)

Anti-snowball 설계 정상 작동. 10회 재시도해도 피드백 크기 ~800자로 일정.

---

## D. TF 상세 및 권고

### TF-25-01 [P0]: ASP 4번째 후보 — Director 미도달 + latent IndexError

**현상**: `stage4_interview_round.py:227-250`에서 ASP가 4번째 후보를 `candidates` 리스트에 추가하나, `director_ensemble.py:379-390`에서 index 0/1/2만 추출하여 Director 프롬프트에 전달. ASP 후보(index 3)는 Director에 도달하지 않음.

**추가 결함**: `director_ensemble.py:372`에서 `['A','B','C'][i]` 로깅 시 `qualified_indices`에 index 3이 포함되면 `IndexError` 발생 가능.

**영향**: ASP 모듈이 LLM 호출(2~3회)을 수행하고 Python Validation까지 통과하나 결과물이 사용되지 않는 dead path. 잠재적 런타임 에러.

**권고** (택 1):
1. ASP 후보를 3후보 중 최저 점수와 교체하여 Director에 전달
2. Director를 4후보 지원으로 확장 (프롬프트 + 매핑 수정)
3. ASP 비활성화 (현재 Round 3+에서만 발동하므로 영향 제한적)

**파일**: `stage4_interview_round.py:227-250`, `director_ensemble.py:335-390,372,553-554`

---

### TF-25-02 [P1]: QualityGate 90점 ↔ Director 프롬프트 PASS 기준 미정렬

**현상**: Stage 2/4에서 QualityGate가 score < 90이면 Director PASS를 REJECT으로 오버라이드하나, Director 프롬프트에는 "score 90 이상이어야 PASS가 유효하다"는 정보가 없음. Director LLM은 자신의 PASS 판정이 Python에 의해 무효화될 수 있다는 것을 인지하지 못함.

**Stage 3과의 비교**: Stage 3은 Director 프롬프트에 "총점 65점 이상이면 PASS" 기준을 명시하고 QualityGate(80)와 역할을 분리. Director가 자신의 PASS/REJECT 기준을 정확히 인지하는 구조.

**구조적 문제**: Director가 PASS + score 75를 출력하면 Python이 REJECT 오버라이드 → Director의 PASS 판정이 체계적으로 무효화. Director 프롬프트의 "관대한 승인" 지침과 Python QualityGate의 엄격한 기준이 정렬되지 않음.

**권고**: Stage 3 패턴을 Stage 2/4에 적용 — Director 프롬프트에 "score 90 이상일 때만 PASS 판정" 기준 명시. 이렇게 하면 Director LLM이 점수와 판정을 일관되게 출력하고, QualityGate와의 충돌이 구조적으로 해소됨.

**파일**: `stage2_finalizer.py:200-217`, `stage4_interview_round.py:1134-1141`, `director.yaml`, `validation.yaml:34`

---

### TF-25-03 [P1]: Post-select (b) history_conflicts — 라운드 게이트 부재

**현상**: Post-select 검사 2건 중 (a) `check_manuscript_continuity_with_cache`는 `round_num == 0 AND next_ep > 1` 조건으로 제한되나, (b) `check_manuscript_history_conflicts`는 라운드/에피소드 게이트가 없어 모든 PASS 판정 시 실행.

```python
# (a) — Round 0 한정
if round_num == 0 and next_ep > 1 and final_manuscript:

# (b) — 제한 없음
if _prev_manuscripts_text and final_manuscript and hasattr(director, "check_manuscript_history_conflicts"):
```

**구조적 논점**: Director 본 판정에서 `prev_manuscripts_text`를 포함한 9항목 모순 체크를 수행한 직후, (b)가 동일 데이터로 별도 프롬프트를 통해 재검증. Round 1+에서도 매 PASS마다 실행되므로 Director 판정과의 책임 경계가 불명확.

**권고** (택 1):
1. (b)에도 `round_num == 0` 게이트 적용 — (a)와 동일 패턴
2. Director 프롬프트에 이력 충돌 검사 항목을 명시적으로 포함하고 (b) 제거
3. (b)를 Director score < 85 조건부로 전환 — 경계선 판정에서만 second opinion

**파일**: `stage4_interview_round.py:1175-1208`

---

### TF-25-04 [P2]: 컨텍스트 Gate 3종 분산 — SSOT 부재

**현상**: 컨텍스트 크기 제한이 3곳에 분산 정의:

| Gate | 위치 | 값 | 정의 방식 |
|------|------|-----|----------|
| `ContextLimits.MAX_CONTEXT_CHARS` | `constants.py:132` | 1,000,000 | 하드코딩 |
| `BaseAgent.MAX_CONTEXT_CHARS` | `base_agent.py:148` | 700,000 | `system.yaml` |
| `director_mandatory_max` | `director_ensemble.py:433` | 40,000 | `_threshold()` → `validation.yaml` |

세 Gate는 각각 다른 역할(필드 절삭 / 합산 budget / 구간 cap)을 가지므로 값의 통일은 불필요하나, **정의 위치가 3곳에 분산**되어 관리 복잡도가 높음.

**권고**: `validation.yaml`에 `context` 섹션 신설:
```yaml
context:
  max_context_chars: 1000000       # smart_truncate 상한
  api_max_context_chars: 700000    # Director stable budget (현재 system.yaml)
  director_mandatory_max: 40000    # mandatory_context cap
```

**파일**: `constants.py:132`, `base_agent.py:148`, `system.yaml:19`, `director_ensemble.py:433`

---

### TF-25-05 [P2]: `stage2_finalizer.py:99` 주석-코드 불일치

**현상**:
```python
# 200K자 상한 (Gemini 대용량 컨텍스트 윈도우 활용)     ← 주석: 200K
if len(_full_arc_history) > ContextLimits.MAX_CONTEXT_CHARS:  # 실제: 1M
    _full_arc_history = _full_arc_history[: ContextLimits.MAX_CONTEXT_CHARS] + "\n... (200K자 절삭)"
    #                                                                              ↑ 로그: 200K
```

주석과 로그 메시지가 "200K"라고 표기하나 실제 상수는 1,000,000(1M). 이전 버전에서 200K였던 값이 업데이트되면서 주석/로그가 동기화되지 않음.

**파일**: `stage2_finalizer.py:99-101`

---

### TF-25-06 [Obs]: Stage 3 Orchestrator 레벨 재시도 없음

**현상**: Stage 3는 내부 10회 재시도만 있고 Orchestrator 레벨 재시도 없음. 전 시도 실패 시 `break: True`.

**비상 폴백**: 최고 점수 ≥ 50이면 `PASS_WITH_WARNING` — 완전 실패 방지.

**구조 평가**: "후속 에피소드가 현재 Blueprint에 의존" 설계 의도로 스킵 금지는 타당. `PASS_WITH_WARNING` 폴백이 완전 실패를 방지하므로 현재 위험도 낮음. 향후 전략 변경(treatment_block 재조합, constraint 완화 등) 후 Orchestrator 레벨 1회 재시도 옵션 고려 가능.

### TF-25-07 [P0]: V60.43 — Python이 Director REJECT를 PASS로 오버라이드

**현상**: `stage2_finalizer.py:176-196`에서 Python 코드가 Director의 REJECT 판정을 PASS로 강제 전환.

```python
# V60.43: API 쿼터 실패 패턴 감지 시 Director REJECT → PASS 오버라이드
if audit.get("decision") == "REJECT" and draft_validator_passed and consensus_passed:
    scores = self_consistency.get("scores", [])
    all_default_50 = len(scores) >= 2 and all(s == 50 for s in scores)
    zero_count = sum(1 for s in scores if s == 0)
    many_zeros = len(scores) >= 2 and zero_count >= len(scores) // 2
    is_quota_failure = all_default_50 or many_zeros

    if is_quota_failure:
        audit["decision"] = "PASS"          # Director REJECT → PASS 강제 전환
        audit["v60_43_override"] = True
```

**대원칙 위반**:
- **원칙 1**: Python이 "이 REJECT은 API 장애에 의한 것인가?"를 판단 — "판단은 LLM이" 위반
- **원칙 3**: Director의 REJECT를 Python이 PASS로 뒤집음 — "Director가 최종 품질 결정권" 직접 위반

**논리적 근거**: DraftValidator + Consensus가 모두 통과했고, Director score가 API 장애 패턴(전부 50 또는 다수 0)이면 Director의 REJECT이 신뢰할 수 없다고 Python이 판단. 취지는 이해되나 **대원칙의 예외가 Python 코드에 하드코딩**된 구조.

**권고**: API 장애 감지 시 Director를 PASS로 오버라이드하는 대신, **다른 temperature로 Director를 재호출**하거나, **Self-Consistency 투표를 강제 발동**하여 LLM이 최종 판단하는 구조로 변경.

**파일**: `stage2_finalizer.py:176-196`

---

### TF-25-08 [P1]: Stage 2 Pre-Director REJECT 체인 — Director 우회 6건

**현상**: `stage2_validation_pipeline.py`에서 6개 검증이 Director에 도달하기 전에 Arc를 REJECT(retry)할 수 있음. Director가 해당 Arc를 한 번도 보지 못하는 경로가 존재.

| # | 검증 | 파일:라인 | 유형 | 대원칙 위반 |
|---|------|----------|------|-----------|
| 1 | **Consensus** (3-LLM 투표) | `:148-161` | LLM | 원칙 3 — Director 아닌 LLM이 REJECT |
| 2 | **Flow Guard** | `:228-294` | **Python** | 원칙 1+3 — Python이 판단 + Director 우회 |
| 3 | **Duplicate Guard** | `:297-309` | **Python** | 원칙 1+3 — Python이 판단 + Director 우회 |
| 4 | **DraftValidator** | `:354-462` | **Python** | 원칙 1+3 — Python이 판단 + Director 우회 |
| 5 | **ArcCorrector 실패** | `:374-452` | Python+LLM | 원칙 3 — Director 우회 |
| 6 | **ContinuityInspector** | `:496-630` | LLM | 원칙 3 — Director 아닌 LLM이 REJECT |

**Stage 4와의 비교**: Stage 4는 `blocking_validator`를 advisory-only로 리팩토링(`[V70.1]` 주석: "대원칙 준수: Python은 수집만, 판단은 Director(LLM)가"). Python 검증 결과가 `mandatory_context`로 Director에 전달되어 Director가 최종 판정. **Stage 2에는 이 리팩토링이 적용되지 않음**.

**구조적 분석**:
- #1(Consensus), #6(ContinuityInspector): LLM이 판단하므로 원칙 1은 준수하나 **Director가 아닌 다른 LLM**이 REJECT 권한을 행사 → 원칙 3(Director 주권) 위반
- #2(Flow Guard), #3(Duplicate Guard), #4(DraftValidator): **순수 Python** REJECT → 원칙 1 + 원칙 3 동시 위반
- Stage 4 모범 패턴(advisory → Director)을 Stage 2에도 적용하는 것이 구조적으로 일관됨

**권고**: Stage 4의 `[V70.1]` 패턴을 Stage 2에 적용:
1. Pre-Director 검증 결과를 advisory(경고)로 전환
2. Director의 `audit_strategic_plan`에 advisory 텍스트를 mandatory_context로 전달
3. Director가 advisory를 참고하여 최종 PASS/REJECT 판정
4. 단, **데이터 무결성 검사**(dict 타입 체크, 필수 키 존재 등)는 Python 차단 유지 가능 — 이는 "판단"이 아닌 "데이터 형식 검증"

**파일**: `stage2_validation_pipeline.py:148-630`

---

### TF-25-09 [P2]: ArcAutoCorrector — Python이 Arc 데이터 직접 수정

**현상**: `stage2_optimizer.py:168-201`의 `auto_correct()` 메서드가 Python 코드로 Arc 데이터를 직접 수정:

```python
def auto_correct(self, arc, prev_arcs):
    arc = self._remove_duplicate_items(arc, prev_arcs)   # 아이템 제거
    arc = self._fix_start_location(arc, prev_arcs)        # 시작 위치 변경
    arc = self._fix_start_state(arc, prev_arcs)           # 시작 상태 변경
    arc = self._fix_joint_docs(arc)                       # joint_docs 수정
    arc = self._sync_final_location(arc)                  # 최종 위치 동기화
    arc = self._ensure_required_fields(arc)               # 필수 필드 보정
    arc = self._normalize_internal_energy(arc)             # 내공 수치 정규화
    return arc, self.corrections_made
```

**대원칙 2 위반**: "팩트시트 수정 권한은 LLM만" — Python이 아이템 제거, 위치 변경, 상태 변경 등 세계 상태에 해당하는 팩트를 직접 수정.

**완화 요소**: 대부분이 이전 Arc의 종료 상태를 현재 Arc의 시작 상태에 동기화하는 **연속성 보존** 작업. 새로운 팩트를 창조하는 것이 아니라 기존 팩트를 이관.

**관련 코드**: `stage2_finalizer.py:274-330` (inventory 상속), `:374-399` (장비 동기화)도 동일 패턴.

**권고**: 현재 구조는 실용적이며 연속성 보존에 기여. 다만, 수정 내역을 Director advisory로 보고하여 Director가 인지하도록 하는 것이 원칙에 더 부합.

**파일**: `stage2_optimizer.py:168-201`, `stage2_finalizer.py:274-399`

---

## F. 대원칙 준수 현황

### F-1. 원칙별 준수 매트릭스

```
원칙                              | Stage 2     | Stage 3     | Stage 4
──────────────────────────────────┼─────────────┼─────────────┼─────────────
1. Python 수집만, 판단은 LLM     | ✗ 위반 4건  | ○ 준수      | △ 부분 위반
   QualityGate PASS→REJECT       | ✗ (L209)    | ○ (정렬됨)  | ✗ (L1134)
   V60.43 REJECT→PASS            | ✗ (L176)    | —           | —
   Pre-Director Python REJECT    | ✗ (3건)     | —           | ○ (advisory)
   Post-select PASS→REJECT       | —           | —           | △ (LLM기반)
──────────────────────────────────┼─────────────┼─────────────┼─────────────
2. 팩트 수정은 LLM만             | △ 부분 위반 | ○ 준수      | ○ 준수
   ArcAutoCorrector              | △ (연속성)  | —           | —
   Equipment/Inventory sync      | △ (이관)    | —           | —
   HUD 수정                      | —           | —           | ○ (V73-B)
──────────────────────────────────┼─────────────┼─────────────┼─────────────
3. Director 주권주의              | ✗ 위반 7건  | ○ 준수      | △ 부분 위반
   QualityGate 오버라이드         | ✗ (양방향)  | ○ (정렬됨)  | ✗ (PASS→REJECT)
   V60.43 오버라이드              | ✗ (REJECT→PASS) | —      | —
   Pre-Director REJECT 체인      | ✗ (6건)     | —           | ○ (advisory)
   Post-select 강등              | —           | —           | △ (LLM기반)
──────────────────────────────────┼─────────────┼─────────────┼─────────────
4. 사망 캐릭터 회상/언급만        | ○ 준수      | ○ 준수      | ○ 준수
   3계층 감지 체인               | —           | —           | ○ (완전)
```

### F-2. Stage별 원칙 준수 성숙도

**Stage 4**: 가장 높은 성숙도. `[V70.1]` 리팩토링으로 Python 검증을 advisory-only로 전환. `[V73-B]`로 HUD 수정을 Director 승인 후 적용. QualityGate와 Post-select (b) 2건만 잔여 위반.

**Stage 3**: 완전 준수. QualityGate(80)가 Director 프롬프트 기준(65+)과 정렬. 내부 재시도는 Director 비교선택(LLM)이 판정. Python은 데이터 전달만.

**Stage 2**: 가장 낮은 성숙도. V60.43(REJECT→PASS 오버라이드), QualityGate(PASS→REJECT 오버라이드), Pre-Director REJECT 체인(6건) 등 원칙 1+3 위반이 집중. Stage 4의 `[V70.1]` advisory 패턴이 아직 적용되지 않은 레거시 구조.

### F-3. 개선 우선순위

| 순위 | TF ID | 대원칙 | 조치 |
|------|-------|--------|------|
| 1 | TF-25-07 | 원칙 3 | V60.43 REJECT→PASS 오버라이드를 Director 재호출로 대체 |
| 2 | TF-25-08 | 원칙 1+3 | Stage 2 Pre-Director REJECT 체인을 advisory로 전환 (Stage 4 [V70.1] 패턴) |
| 3 | TF-25-02 | 원칙 1+3 | QualityGate 90점을 Director 프롬프트에 명시 (Stage 3 패턴) |
| 4 | TF-25-01 | 구조 결함 | ASP 4번째 후보 dead path + latent IndexError 수정 |
| 5 | TF-25-03 | 원칙 3 | Post-select (b) 라운드 게이트 적용 |
| 6 | TF-25-09 | 원칙 2 | ArcAutoCorrector 수정 내역을 Director advisory로 보고 |

---

## E. 부록

### E-1. LLM 호출 맵

```
Stage 2 (Arc 1회 시도):
  ┌─ FourPhaseArcGenerator ──── 1-4 LLM
  ├─ SelfReflector ─────────── 0-1 LLM (Analyst만)
  ├─ Consensus ─────────────── 0-3 LLM (FourPhase 제외)
  ├─ NarrativeStructureAnalyzer 0-1 LLM
  ├─ ArcCorrector ─────────── 0-1 LLM
  ├─ ContinuityInspector ──── 1 LLM
  └─ Director Audit ────────── 1-3 LLM (SC 투표)
  합계: 3-10 LLM / 시도, × 5 시도 = 15-50 LLM / Arc

Stage 3 (Blueprint 1회 시도):
  ┌─ BlueprintEnsemble ────── 3 LLM (또는 InPlace 1)
  ├─ ContinuityCheck ────────  1 LLM
  └─ Director Comparison ──── 1 LLM
  합계: 3-5 LLM / 시도, × 10 시도 = 30-50 LLM / Blueprint (최대)

Stage 4 (원고 1라운드):
  ┌─ CW Ensemble ──────────── 3 LLM (Round 0) / 1-3 (패치)
  ├─ TruthGate world_law ──── 0-3 LLM
  ├─ NpcDriftAdvisor ────────  0-3 LLM
  ├─ NumericDriftAdvisor ──── 0-1 LLM (5화 단위)
  ├─ FlashbackVerifier ─────── 0-3 LLM
  ├─ InfoParadoxChecker ────── 0-3 LLM (1인칭)
  ├─ RelationshipDriftAdvisor  0-3 LLM (ep≥5)
  ├─ Director Judgment ────── 1 LLM
  ├─ Post-select (a) ────────  0-1 LLM (Round 0, ep>1)
  ├─ Post-select (b) ────────  0-1 LLM (PASS 시)
  └─ ToT/MAD (REJECT) ─────── 0-2 LLM
  합계: 5-24 LLM / 라운드, × 5 라운드 = 25-120 LLM / 에피소드 (최대)
```

### E-2. 컨텍스트 구성 요약표

| 컴포넌트 | Stage 2 | Stage 3 생성기 | Stage 3 Director | Stage 4 CW | Stage 4 Director |
|---------|---------|--------------|-----------------|------------|-----------------|
| prev_manuscripts | — | ~150K-300K | — | ~150K-300K | ~150K-300K |
| Arc/Blueprint/Bible | ~105K-120K | ~7K-25K | ~3K-6K | ~30K-50K | ~15K-45K |
| 후보 | — | — | ~9K-15K | — | ~15K-45K |
| mandatory_context | — | — | — | ~5K-20K | ~12K-40K |
| 템플릿 | ~3K | ~3K | ~3.5K | ~5K | ~8K |
| **총합** | **~118K-143K** | **~160K-328K** | **~16K-25K** | **~190K-375K** | **~200K-438K** |

### E-3. 파일 색인

| 파일 | 참조 항목 |
|------|---------|
| `modules/core/stage2_orchestrator.py` | B-1-05, B-1-06 |
| `modules/core/stage2_finalizer.py` | B-1-01, B-1-04, TF-25-02, TF-25-05, C-3-01 |
| `modules/core/stage2_validation_pipeline.py` | B-1-03 |
| `modules/core/stage2_preflight.py` | B-1-06 |
| `modules/domain/agents/director_auditor.py` | B-1-02 |
| `modules/domain/agents/director.py` | B-1-02 (ambiguous thresholds) |
| `modules/core/stage3_orchestrator.py` | B-2-01, B-2-04, B-2-05, TF-25-06 |
| `modules/domain/agents/three_phase_blueprint_generator.py` | B-2-01, B-2-03, C-3-03 |
| `modules/domain/agents/director_ensemble.py` | B-2-02, B-3-02, B-3-06, TF-25-01, C-1-03 |
| `modules/core/stage4_interview_round.py` | B-3-01~10, TF-25-01, TF-25-02, TF-25-03, C-1-02, C-2-02, C-3-02 |
| `modules/domain/agents/chief_writer_context.py` | C-1-02 |
| `modules/core/truth_gate.py` | B-3-01, C-2-01 |
| `modules/core/npc_drift_advisor.py` | B-3-01, C-2-01 |
| `modules/core/numeric_drift_advisor.py` | B-3-01, C-2-01 |
| `modules/core/flashback_verifier.py` | B-3-01, C-2-01 |
| `modules/core/info_paradox_checker.py` | B-3-01, C-2-01 |
| `modules/core/relationship_drift_advisor.py` | B-3-01, C-2-01 |
| `modules/core/constants.py` | C-1-01, C-1-03, TF-25-04, TF-25-05 |
| `modules/domain/agents/base_agent.py` | C-1-03, TF-25-04 |
| `config/settings/validation.yaml` | B-2-03, B-1-04, B-3-05, TF-25-04 |
| `config/settings/system.yaml` | C-1-03, TF-25-04 |
| `config/prompts/director.yaml` | B-1-03, B-1-04, B-3-07, TF-25-02, C-2-01 |
