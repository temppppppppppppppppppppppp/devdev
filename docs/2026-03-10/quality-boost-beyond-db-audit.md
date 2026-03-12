# 퀄리티 부스트 — DB 활용 외 3대 방향성 전수조사

> 작성: 2026-03-10
> 상태: 감리 완료 (3pass + 실행 전 보강 반영 — FL-1 additive 방식 확정 / FL-2 소비 경로로 정정 / QM-2 score axis 보정 / QM-4 sidecar 방향 확정)
> 전제: `TF-DB-quality-boost-audit.md`(DB 활용 극대화)와 독립. DB 활용은 해당 문서 참조.
> 목표: DB 활용 **외** 방향에서 퀄리티 상승 경로 전량 식별

---

## 공통 원칙

- **대원칙 1**: Python은 수집만, 판단은 LLM이
- **대원칙 3**: Director 주권주의 — advisory만 제공, REJECT 강제 금지
- 기존 동작 불변 — 추가/보강만, 기존 로직 변경 금지
- LLM 호출 최소화 — Python-only 우선, 필요 시 Flash 1회

> `Codex 메모`
> 방향성은 전반적으로 좋다. 다만 `QI-FL-1`, `QI-FL-2`, `QI-FL-5`, `QI-QM-2`, `QI-QM-4`는 "완전 부재"보다 "부분 존재하지만 소비 경로가 약함"에 가깝다.
> 실행 문서로 쓸 때는 이 차이를 분리해 두는 편이 안전하다.

---

## 방향 1: 프롬프트 신호 대 잡음비 (Signal-to-Noise)

### 현황 진단

Stage 4 CW 프롬프트 입출력 비율 **10~40:1** (37K 토큰 입력 → 1~3K 출력).
mandatory_context + Director MC 합산 ~47K 토큰. 이 중 **약 30%가 비게이팅 또는 중복 콘텐츠**.

### QI-SNR-1. NPC 정보 5중 중복

**현황** — 동일 NPC 정보가 5개 독립 소스에서 중복 주입:

| 소스 | 파일 | 내용 |
|------|------|------|
| WorldState.get_summary() | `world_state.py` | 역할, 관계, 성격, 위치 |
| FactLedger.to_summary() | `fact_ledger.py` | NPC 이벤트, 수치 |
| StateTracker 16종 요약 | `state_tracker.py` | NPC 카테고리별 상세 |
| Continuity Packet | `stage4_context_builder.py` | Blueprint 지목 NPC 상세 |
| CW episode digest | `chief_writer_context.py` | 직전 화 NPC 변경사항 |

**갭**: "박성호"의 현재 상태가 5곳에서 각기 다른 추상 수준으로 반복. LLM이 어느 것을 신뢰해야 하는지 불명확. 약 **5K 토큰 낭비**.

**해법**:
- CP가 Blueprint 지목 NPC를 상세 조회하므로, 해당 NPC는 WorldState/FactLedger 요약에서 **간략화** (이름만 표시 + "상세는 CP 참조")
- StateTracker NPC 요약은 CP 미포함 NPC만 출력
- 예상 절감: ~3K 토큰

**우선순위**: P1
**파일**: `stage4_context_builder.py` (build_mandatory_context 조립 로직)

> `Codex`
> 방향은 동의한다. 다만 실제 절감 우선순위는 `CP + WorldState + FactLedger` 쪽이 더 크다.
> `StateTracker` 요약은 `mandatory_context` 후반에 append되고, 현재 Stage 4는 컨텍스트 초과 시 뒤에서부터 섹션을 제거하므로 이미 먼저 탈락하는 편이다.
> 즉 "5중 중복 전부 동등"으로 보기보다, 상단 고정 주입되는 중복부터 정리하는 쪽이 효과 대비 비용이 좋다.

---

### QI-SNR-2. HUD 5중 중복

**현황** — HUD 관련 정보가 5개 섹션에서 중복:

| 섹션 | 내용 |
|------|------|
| HUD report (snapshot) | 주인공 전체 상태 스냅샷 |
| High-density HUD | 주인공 상세 (위의 확장) |
| HUD trend (5화 rolling) | 최근 5화 추세 |
| HUD anomaly (alerts) | 이상치 경고 |
| StateTracker summary | 동일 데이터의 카테고리별 분해 |

**갭**: 동일 주인공 상태가 5가지 뷰로 반복. 약 **5K 토큰 낭비**.

**해법**:
- **2섹션 통합**: snapshot(현재 상태) + anomaly(경고만). trend는 anomaly에 흡수.
- StateTracker NPC 요약 중 주인공 관련은 HUD에 위임
- 예상 절감: ~5K 토큰

**우선순위**: P2 (HUD 코드 구조 변경 필요)
**파일**: `stage4_context_builder.py`, `chief_writer_context.py`

---

### QI-SNR-3. Advisory 간 모순 미감지

**현황** — 15종 advisory가 독립적으로 Director MC에 주입:

| 티어 | Advisory | 검사 수 |
|------|----------|---------|
| CRITICAL | TruthGate | 7개 Python 검사 |
| MAJOR | NpcDrift, RelDrift, Flashback, InfoParadox | 각 1개 LLM 판정 |
| INFO | NumericDrift, LongTermRepetition, NC-1~4, SceneSimilarity, Timeline | 각 Python/LLM |

**갭**: Advisory 간 모순 가능. 예:
- NumericDrift: "자본금 20% 하락 경고" vs NC-1: "±30% 허용 범위"
- NpcDrift: "박성호 성격 변화 감지" vs RelDrift: "박성호 관계 변화는 정상"
- Director가 상반된 advisory를 동시 수신하면 판정 정확도 저하

**해법**:
- Advisory 주입 직전 **모순 감지 로직** 추가 (Python-only)
- 동일 NPC/수치에 대한 상반 advisory → 상위 티어 우선 + 하위 supppress + 로깅
- 약 30~50줄 추가

**우선순위**: P1
**파일**: `stage4_interview_round.py` (advisory 주입 루프)

---

### QI-SNR-4. 비게이팅 콘텐츠 분리

**현황** — Director MC에 판정에 영향 없는 정보 포함:
- `get_fix_scope_stats()` 결과 (~200토큰)
- `get_strategy_win_rates()` 결과 (~300토큰)
- DB analytics (pacing, satisfaction) from §1/§2 (~500토큰)

**갭**: 총 ~1K 토큰이 Director 판정에 영향 없이 주의 분산.

**해법**:
- 비게이팅 콘텐츠를 `[참고 — 판정 무관]` 헤더로 분리
- Director 프롬프트에 "참고 섹션은 판정 근거로 사용하지 말 것" 지시
- 또는 별도 metadata 영역으로 이동

**우선순위**: P2
**파일**: `stage4_interview_round.py`, `director.yaml`

---

## 방향 2: 피드백 루프 단절 해소

### 현황 진단

시스템이 **순방향 전용(feed-forward only)** 아키텍처. 후속 단계 실패가 이전 단계 설계에 영향 못 줌.

```
Stage 2 → Stage 3 → Stage 4
  ↓          ↓          ↓
Arc 설계   Blueprint   원고
  ×          ×          ×
  ←──────────←──────────←── (피드백 없음)
```

### QI-FL-1. CW 재시도 누적 피드백 미합성

**현황**:
- `previous_attempt` dict로 직전 시도 피드백만 전달
- CW `regenerate_with_feedback()` (chief_writer.py L621-773): 직전 시도의 rejection_reason, score_breakdown, validation_warnings 수신
- **시도 1~3의 누적 패턴 미합성** — 시도 4가 시도 1~2의 실패 이유를 모름

**갭**: 3회 연속 "continuity 실패"인데 시도 4는 직전 시도(3)의 피드백만 보고, 시도 1~2에서 반복된 근본 원인 미인지.

**해법**:
- `previous_attempt` dict는 유지하고, 그 안에 `history` 또는 `prior_attempts`를 additive하게 추가 (최대 3건)
- CW 재생성 시 누적 실패 합성: "시도 1~3 공통 실패: continuity — 위치 이동 묘사 누락"
- 합성은 Python-only (rejection_reason 키워드 교집합)

**우선순위**: P1
**파일**: `stage4_interview_round.py` (_process_verdict), `chief_writer.py` (regenerate_with_feedback)

> `Codex`
> 문제 인식은 맞다. 다만 구현은 `previous_attempt` 시그니처 자체를 바꾸기보다, 기존 dict 안에 `history`나 `prior_attempts`를 추가하는 additive 방식이 안전하다.
> 현재 `previous_attempt`는 재생성, patch mode, ASP 경로까지 넓게 퍼져 있어서, 타입 자체를 바꾸면 호출부 영향이 예상보다 커진다.

---

### QI-FL-2. Cross-Arc 실패 전파 부재

**현황**:
- `stage_rejection_history`는 Stage 2 내부에서만 기록 (stage2_finalizer.py L1506)
- Stage 3/4 rejection은 DB `stage_attempts` 테이블에 **이미 기록됨** (reject_reason, failure_category, advisory_flags)
- 그러나 Arc 생성기(`four_phase_arc_generator.py`)가 이 영속 로그를 **소비하지 않음**
- Arc N 완료 → Arc N+1 설계 시 Stage 3/4 실패 이유 **전달 없음**

**갭**: Arc 5의 에피소드들이 전부 "주인공 위치 텔레포트"로 실패해도, Arc 6 설계 시 이 교훈이 전달 안 됨. 같은 실수 반복. 기록은 되지만 소비 경로가 없는 것이 근본 원인.

**해법**:
- Arc N+1 `_generate_prev_context()`에서 `stage_attempts` 테이블의 직전 Arc rejection 로그 조회
- 직전 Arc의 Stage 3/4 실패 요약 주입: "직전 Arc 주요 실패: {top 3 rejection reasons}" 1~3줄
- 신규 기록 추가 불필요 — 기존 영속 로그 소비 경로만 추가

**우선순위**: P1
**파일**: `four_phase_arc_generator.py` (_generate_prev_context — stage_attempts 조회 추가)

> `Codex`
> 여기엔 보정이 필요하다. `stage_rejection_history`에는 Stage 3/4가 안 쌓이지만, Stage 3/4 REJECT 자체는 이미 DB `stage_attempts`에 저장된다.
> 즉 진짜 갭은 "기록 안 됨"이 아니라 "Arc 생성기가 그 영속 로그를 읽어 다음 Arc에 반영하지 않음"이다.
> 실행 문구도 `rejection 기록 추가`보다는 `persisted reject 로그 소비 경로 추가` 쪽이 현재 코드와 더 잘 맞는다.

---

### QI-FL-3. FailureAnalyzer 미소비

**현황**:
- `FailureAnalyzer(db)` — 11개 분석 메서드 구현:
  - `.top_failure_categories()`, `.failure_prompt_patterns()`, `.advisory_reject_correlation()`
  - `.most_failed_agents()`, `.stage_pass_rates()`, `.model_performance()`
- **소비자 0개** — 생성 파이프라인 어디에서도 호출 안 됨
- llm_calls(18컬럼), stage_attempts(17컬럼) 테이블에 풍부한 데이터 축적 중

**갭**: "대시보드를 만들어놓고 안 보는" 상황. 반복 실패 패턴을 사후 분석할 수 있지만 사전 예방에 활용 안 됨.

**해법**:
- Arc N+1 생성 전 `FailureAnalyzer.summary()` 호출
- 결과를 Stage 2 `_generate_prev_context()`에 주입:
  ```
  [이전 Arc 실패 분석]
  평균 에피소드 점수: 82점
  주요 실패 원인: continuity(40%), pacing(30%), numeric(15%)
  가장 실패 빈번한 에이전트: chief_writer(68%)
  ```
- Python-only, LLM 0회

**우선순위**: P1
**파일**: `four_phase_arc_generator.py` (_generate_prev_context), `failure_analyzer.py`

---

### QI-FL-4. 고득점 에피소드 학습 부재

**현황**:
- 에피소드 점수는 `director_selections.score`에 저장
- 95점 에피소드가 "왜 좋았는지" 분석/저장 안 됨
- 다음 Arc 설계 시 "잘한 것"을 반복하라는 신호 없음

**갭**: 실패에서만 배우고 성공에서는 안 배움. "에피소드 42가 95점 — 대화 비율 높고 긴장감 유지" 같은 성공 패턴 미추출.

**해법**:
- score ≥ 90 에피소드의 `selection_reason`은 `director_selections` DB에 저장 중. `score_breakdown`은 DB가 아닌 `episode_production.jsonl`에만 존재 — DB 적재 추가 또는 JSONL 소비 유틸 필요
- Arc N+1 생성 시 "직전 Arc 고득점 에피소드 특성" 1~2줄 주입
- `FailureAnalyzer`에 `top_success_patterns()` 메서드 추가

**우선순위**: P2
**파일**: `failure_analyzer.py`, `four_phase_arc_generator.py`

> `Codex`
> `selection_reason`은 DB에 저장되지만, `score_breakdown`은 현재 DB가 아니라 `logs/episode_production.jsonl`에만 남는다.
> 그래서 "이미 저장 중"이라고 쓰면 과장이다. 성공 패턴 학습을 정말 자동화하려면 DB 적재를 추가하거나, 최소한 JSONL 소비 유틸을 별도로 두는 쪽으로 문구를 고치는 편이 맞다.

---

### QI-FL-5. 에피소드 품질 추세 미감지

**현황**:
- 에피소드 점수: 95→88→75→68 하락 추세 가능
- Stage 2 preflight에서 `quality_dashboard.get_score_trend_summary(stage=2)` 경로로 추세 블록 주입됨 (부분 존재)
- Stage 4 post-processor에서도 점수 회귀 감지 존재
- 그러나 Arc 생성기 `_generate_prev_context()`에는 **추세 정보 미전달**

**갭**: Stage 2/4 내부에서는 추세를 보지만, Arc N+1 설계 시점(`_generate_prev_context()`)에는 이어지지 않음. 전체 에피소드 추세 기반 Arc 사전 설계 불가.

**해법**:
- Arc 종료 시 해당 Arc 에피소드 점수 rolling average 계산
- 하락 추세 감지 (3연속 하락 or 평균 80 미만) → Arc N+1 advisory
- Python-only

**우선순위**: P2
**파일**: `four_phase_arc_generator.py`, `db_manager.py` (점수 조회 메서드)

> `Codex`
> 이 항목도 부분 보정이 필요하다. Stage 2 preflight는 이미 `quality_dashboard.get_score_trend_summary(stage=2)`를 읽어 품질 추세 블록을 주입하고, Stage 4 post-processor도 점수 회귀를 감지한다.
> 따라서 완전 미감지라기보다, "Stage 4/전체 에피소드 추세가 Arc N+1 `_generate_prev_context()`까지 이어지지 않는다"가 더 정확하다.

---

## 방향 3: 품질 측정 사각지대

### 현황 진단

모순 감지는 강함 (NC-1~4 9개 검사, TruthGate 7개, consistency_checklist 13개).
**구조적 서사 품질**은 측정 안 됨.

```
강함: 모순 감지 (수치, NPC, 시간, 공간, 팩트)
약함: 서사 구조 (패이싱, POV, 감정 아크, 대화 품질)
없음: 장르별 긍정 품질 (딜 구조, 경기 흐름, 시술 순서)
```

### QI-QM-1. Self-Critique 누락 체크 3건

**현황** — 현재 self-critique 11개 체크:
1. HUD 정합성
2. 클리셰 과용
3. 정당화 갭
4. NPC 관계
5. 동기/약속 일관성
6. WritingDirective 준수
7. 표현 신선도
8. ending_hook 존재
9. 산술 정합성
10. 시스템 용어 노출
11. 결말 참신성

**갭** — 부분 존재하지만 CW self-critique 루프 내부에는 없는 3건:

#### 12번째: 시간 논리 (Temporal Logic)

- `pre_llm_validator._check_time_progression()` (L96-100)에 **이미 존재** — 시간 흐름 비논리 감지
- 그러나 pre_llm은 **사전 검증**(CW 생성 전). self-critique 루프(CW 생성 후 자가 수정) 내부에는 없음
- **추가 가치**: CW가 self-critique 단계에서 시간 비약을 스스로 수정할 기회 부여

#### 13번째: 문단 구조 (Paragraph Structure)

- `pre_llm_validator._check_sentence_endings()` (L102-106) + 문장 길이 변동 + 대화 비율 검사 **이미 존재** (L188-238)
- 그러나 역시 pre_llm 사전 경로. self-critique 내부에서 "5줄+ 벽돌 문단" 자가 감지는 없음
- **추가 가치**: 재생성 없이 CW가 줄바꿈 삽입으로 즉시 수정 가능 (저비용)

#### 14번째: 톤 일관성 (Tonal Consistency)

- `chief_writer_quality._check_writing_directive()` (L667-687)에서 WritingDirective 톤 체크 **부분 존재**
- Blueprint `core_tension`/`emotional_arc` 대비 원고 톤 교차 검증은 미구현
- **추가 가치**: Blueprint 지시와 원고 톤 간 괴리 감지 (기존은 WritingDirective 한정)

**우선순위**: P2 (3건 모두 pre_llm_validator 또는 WritingDirective에 부분 존재. self-critique 내부 추가는 보강 수준)
**파일**: `chief_writer_quality.py`

> `Codex`
> self-critique 기준으로는 유효한 제안이다. 다만 시스템 전체 기준으로 보면 `시간 진행`, `극단적 문장 길이`, `대사 부족`, `페이싱`은 이미 `PreLLMValidator`/`AdvisoryValidator`에 부분 구현돼 있다.
> 즉 이 항목의 가치는 "완전 신규 검사"보다 "CW self-critique 루프 안으로 당겨와서 수정 가능하게 만든다"에 가깝다. 문구를 그렇게 낮춰 쓰면 더 정확하다.

---

### QI-QM-2. Director 미측정 품질 차원

**현황** — Director `score_breakdown` 5개 차원:
- continuity_contradiction (40%)
- blueprint_coverage (20%)
- quality_engagement (20%)
- length (10%)
- python_warnings (10%)

**갭** — 부분 존재하지만 1급 score axis나 per-scene 구조로 다루지 않는 차원:

| 차원 | 설명 | 현재 상태 |
|------|------|-----------|
| 패이싱 품질 | 씬 길이 분포, 긴장-이완 리듬 | `consistency_checklist`에 `scene_variety` 포함. 별도 score axis 아님 |
| 대화 자연스러움 | 캐릭터별 말투 일관성, 정보 전달 대화 vs 캐릭터 대화 | pre_llm_validator에 대화 비율 검사 존재. per-character 톤 검사 없음 |
| POV 내부 일관성 | 씬 내 시점 누출 (타인 내면 침범) | V70 존재 + `consistency_checklist`에 포함. per-scene 미적용 |
| 감정 아크 진정성 | 자극 대비 반응 비례, 회복 시간 현실성 | 미측정 (유일하게 완전 부재) |

**해법 (단계적)**:
- **Phase 1**: `consistency_checklist`에 pacing/dialogue/pov 3개 카테고리 추가 (Director에게 체크 요청만, 자동감점 없음)
- **Phase 2**: Python-only 사전 감지 → Director advisory 주입

**우선순위**: P2 (Director 프롬프트 변경 + 스키마 확장)
**파일**: `config/prompts/director.yaml`, `modules/domain/agents/director_ensemble.py`

> `Codex`
> 이 항목은 현황 서술을 보정하는 편이 좋다. Director 쪽은 이미 `consistency_checklist` 13개 항목에 `event_ordering`, `space_continuity`, `scene_variety`가 있고, POV는 `PreLLMValidator` 경로가 존재한다.
> 그래서 진짜 갭은 "측정 0"이 아니라 "pacing/dialogue/pov/emotion을 1급 score axis나 per-scene 구조로 다루지 않는다" 쪽이다.
> 파일 경로도 실제 구현체는 `modules/domain/agents/director_ensemble.py`다.

---

### QI-QM-3. 장르별 긍정 품질 검사 부재

**현황** — Genre Guard 10종 전부 **부정 검사만** (금지어, 불가능 행동):

| 장르 | 현재 검사 | 미검사 (긍정 품질) |
|------|-----------|-------------------|
| 투자물 | 금융 용어 오용, 비현실 금액 | 딜 구조 현실성, 분석 프레임워크 적정성, 시장 메커니즘 타당성 |
| 스포츠 | 종목 규칙 위반, 비현실 체력 | 경기 흐름 자연스러움, 부상 회복 현실성, 팀 역학 |
| 의료 | 시술 용어 오류 | 시술 순서 타당성, 회복 타임라인, 의료 윤리 |
| 배우물 | 업계 용어 오류 | 오디션 프로세스 현실성, 캐스팅 역학, 연기 묘사 |
| 요리 | 식재료 오류 | 조리법 순서, 화학적 타당성 (마이야르 반응 등) |

**갭**: Guard가 "이건 틀렸다"만 잡고 "이건 현실적인가"는 안 봄. 투자물에서 "직감으로 M&A 결정" 같은 비현실적 의사결정 미감지.

**해법**:
- 장르별 **긍정 품질 체크리스트** YAML 정의
- Guard의 `run_deep_validation()`에 advisory 레벨 긍정 검사 추가
- Director에게 "[장르 품질 참고]" advisory로 전달

**우선순위**: P2 (장르별 도메인 지식 필요, 높은 구현 비용)
**파일**: `genre_guards/*.py`, `config/prompts/genre_quality_checklists.yaml` (신규)

---

### QI-QM-4. 에피소드 품질 라벨링 시스템 부재

**현황**:
- PASS 후 저장: manuscripts, martial_tracker, cost_record, character_voice, foreshadow_tracker
- **분산 저장**: `selection_reason` → `director_selections` DB, `reject_reason`/`advisory_flags` → `stage_attempts` DB, `score_breakdown`/`open_review` → `episode_production.jsonl`
- **미달**: 정규화된 조회 가능한 품질 라벨이 없음. "왜 이 점수인지" 요약을 단일 쿼리로 추출 불가

**갭**: 데이터는 분산 존재하나 정규화 저장이 없어, 100+ 에피소드 축적 후에도 단일 쿼리로 "좋은 에피소드의 공통점"을 추출할 수 없음.

**해법**:
- `episode_quality_labels` sidecar 테이블 신설 (manuscripts 스키마 변경 회피, 마이그레이션 안전)
- PASS 시 score_breakdown + consistency_checklist 요약을 JSON으로 저장
- FailureAnalyzer에 `quality_distribution()` 메서드 추가

**우선순위**: P2 (스키마 변경 필요)
**파일**: `modules/core/db_manager.py`, `modules/core/stage4_post_processor.py`

> `Codex`
> "미저장"도 다소 과하다. `selection_reason`은 `director_selections`에 저장되고, `reject_reason`/`advisory_flags`는 `stage_attempts`에 저장되며, `score_breakdown`/`open_review`는 `episode_production.jsonl`에 남는다.
> 부족한 건 "조회 가능한 정규화 저장"이다. 그래서 `manuscripts` 컬럼 확장보다 `episode_quality_labels` 같은 sidecar 테이블 신설이 분석/마이그레이션 면에서 더 안전할 수 있다.

---

### QI-QM-5. 씬 전환 품질 미측정

**현황**:
- 공간 연속성은 Director 체크리스트(space_continuity)에 포함
- **씬 전환 자체의 품질**은 미측정:
  - 위치 전환 시 도착지 명시 여부
  - 시간 전환 표지 존재 여부
  - 감정 톤 전환의 급격함 (긴장 → 코미디 갑전환)

**해법**:
- Self-critique 15번째 체크: 씬 전환 마커 존재 확인
- Python-only: `\n\n` 또는 `***` 기준 씬 분리 → 각 씬 첫 3문장에서 장소/시간 키워드 존재 확인

**우선순위**: P2
**파일**: `chief_writer_quality.py`

---

## 우선순위 요약

### P1 (즉시 효과 — 저비용 고효과)

| ID | 항목 | 효과 | 비용 |
|----|------|------|------|
| QI-SNR-1 | NPC 정보 5중복 통합 | ~3K 토큰 절감, 신호 집중 | 중 |
| QI-SNR-3 | Advisory 모순 감지 | Director 판정 정확도↑ | 낮 (30~50줄) |
| QI-FL-1 | CW 재시도 누적 피드백 | 반복 실패 패턴 근절 | 낮 |
| QI-FL-2 | Cross-Arc 실패 소비 경로 추가 | Arc 단위 반복 실패 방지 | 낮~중 |
| QI-FL-3 | FailureAnalyzer 소비 | 실패 패턴 사전 예방 | 낮 |

### P2 (중기 효과 — 중비용)

| ID | 항목 | 효과 | 비용 |
|----|------|------|------|
| QI-SNR-2 | HUD 5중복 통합 | ~5K 토큰 절감 | 중 |
| QI-SNR-4 | 비게이팅 콘텐츠 분리 | ~1K 토큰 절감 | 낮 |
| QI-FL-4 | 고득점 에피소드 학습 | 성공 패턴 반복 | 중 |
| QI-FL-5 | 품질 추세 Arc 전달 | 하락 사전 대응 | 낮~중 |
| QI-QM-1 | Self-critique 12~14번째 보강 | pre_llm 경로 보완 (부분 존재→self-critique 내부화) | 낮 |
| QI-QM-2 | Director 품질 차원 확대 | 서사 구조 품질↑ (부분 존재→per-scene 확장) | 중 |
| QI-QM-3 | 장르별 긍정 품질 검사 | 장르 몰입도↑ | 높 |
| QI-QM-4 | 품질 라벨링 시스템 | 장기 학습 기반 (분산→정규화) | 중 |
| QI-QM-5 | 씬 전환 품질 체크 | 구조적 품질↑ (부분 존재) | 낮 |

---

## TF-DB 문서와의 관계

| 본 문서 | TF-DB | 관계 |
|---------|-------|------|
| QI-SNR-1~4 | — | **독립** (프롬프트 구조 최적화, DB 무관) |
| QI-FL-1~5 | G1/G2 | **보완** — G1/G2는 FailureAnalyzer DB 미소비 식별, 본 문서는 소비 방법 명세 |
| QI-QM-1~5 | — | **독립** (측정 확대, DB 무관) |

---

## 파일 변경 목록 (예상)

| 파일 | 변경 | ID |
|------|------|-----|
| `modules/core/stage4_context_builder.py` | NPC/HUD 중복 통합 로직 | QI-SNR-1, QI-SNR-2 |
| `modules/core/stage4_interview_round.py` | Advisory 모순 감지 + 비게이팅 분리 + `previous_attempt.history` 누적 피드백 | QI-SNR-3, QI-SNR-4, QI-FL-1 |
| `modules/domain/agents/chief_writer_quality.py` | Self-critique 12~14번째 + 씬 전환 체크 | QI-QM-1, QI-QM-5 |
| `modules/domain/agents/chief_writer.py` | 누적 피드백 수신 | QI-FL-1 |
| `modules/domain/agents/four_phase_arc_generator.py` | stage_attempts 소비 + FailureAnalyzer 주입 + 품질 추세 + 성공 패턴 | QI-FL-2, QI-FL-3, QI-FL-4, QI-FL-5 |
| `modules/core/failure_analyzer.py` | top_success_patterns() + quality_distribution() | QI-FL-4, QI-QM-4 |
| `config/prompts/director.yaml` | 품질 차원 확대 (checklist 추가) | QI-QM-2 |
| `modules/domain/agents/director_ensemble.py` | checklist 키 확대 | QI-QM-2 |
| `modules/core/genre_guards/*.py` | 긍정 품질 체크 추가 | QI-QM-3 |
| `modules/core/db_manager.py` | `episode_quality_labels` sidecar 테이블 추가 | QI-QM-4 |
| `modules/core/stage4_post_processor.py` | 품질 라벨 저장 | QI-QM-4 |

> `Codex 메모`
> 경로 보정 2건:
> - `chief_writer_quality.py` 실제 위치는 `modules/domain/agents/chief_writer_quality.py`
> - `director_ensemble.py` 실제 위치는 `modules/domain/agents/director_ensemble.py`

---

## 절대 하지 말 것

- Director score_breakdown 가중치(40/20/20/10/10)를 변경하지 말 것
- 기존 advisory 체인 순서를 변경하지 말 것
- Self-critique 기존 11개 체크의 로직을 수정하지 말 것
- Genre Guard 기존 금지어 목록을 변경하지 말 것
- LLM 호출을 2회 이상 추가하지 말 것 (Python-only 우선)
- mandatory_context 총량을 현재 대비 증가시키지 말 것 (절감만 허용)

---

## 검증 기준

- `pytest --collect-only -q tests` 기준 전체 테스트 **3,756개 수집 유지** (2026-03-10 확인)
- `pytest tests/ -q` 전체 회귀 PASS
- `ruff check` 변경 파일 전량 0 violations
- mandatory_context 토큰 수: 변경 전 ≥ 변경 후 (증가 금지)
- Director PASS rate: 변경 전 ≥ 변경 후 (하락 금지)
- Self-critique 신규 체크: false positive rate < 10% (실파이프라인 검증 필요)
