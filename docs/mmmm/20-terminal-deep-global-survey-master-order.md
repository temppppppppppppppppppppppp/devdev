# 20-Terminal Deep Global Survey — Master Order

**Status**: FINAL (3pass 감리 + 적대적 3pass 감리 통과)
**Date**: 2026-03-20
**Baseline Commit**: `d0fa70f1`
**Codebase Scale**: modules/ 144,000+ lines, tests/ 87,700+ lines, main_a.py 4,891 lines, scripts/ 37 files, desktop/ 15+ source files, config/ 30+ YAML/JSON
**Authority**: 이 문서는 20-Terminal 전역 전수조사의 유일한 마스터 오더다.

---

## 0-A. 빠른 디스패치

사용자가 아래 패턴 중 하나로 지시하면 해당 터미널의 오더를 수행한다:

- **"넌 N번"** (예: "넌 1번", "넌 14번")
- **"넌 N번 터미널"** (예: "넌 1번 터미널")
- **"N번"** (예: "1번", "20번")
- **"N번 터미널"** (예: "1번 터미널")
- **"터미널 N"** (예: "터미널 1", "터미널 20")
- **"TN"** 또는 **"T0N"** (예: "T1", "T01", "T20")

숫자만 다르면 전부 같은 의미다. 위 패턴 외에도 터미널 번호를 특정할 수 있는 자연어는 동일하게 디스패치한다.

**디스패치 규칙:**
1. 이 마스터 오더 문서의 **섹션 1 (전역 운영 규칙)** 전체를 먼저 읽는다.
2. **섹션 2** 에서 자기 터미널 번호(T{NN}) 섹션을 찾아 범위·필수 조사·TF 최소 기대를 확인한다.
3. 섹션 3(의존 관계), 섹션 4(프롬프트 템플릿)을 참고한다.
4. 조사를 수행하고, **docs/mmmm/** 에 산출물을 저장한다.

**매핑표:**

| 단축 지시 | 터미널 | 영역 |
|-----------|--------|------|
| "넌 1번 터미널" / "T01" | T01 | SovereignApp & Bootstrap |
| "넌 2번 터미널" / "T02" | T02 | Stage 2 Orchestration & Context |
| "넌 3번 터미널" / "T03" | T03 | Stage 2 Preflight, Finalizer & Optimizer |
| "넌 4번 터미널" / "T04" | T04 | Stage 3 Pipeline |
| "넌 5번 터미널" / "T05" | T05 | Stage 4 Core Orchestration |
| "넌 6번 터미널" / "T06" | T06 | Stage 4 Interview & Post-Processing |
| "넌 7번 터미널" / "T07" | T07 | Director System |
| "넌 8번 터미널" / "T08" | T08 | ChiefWriter System |
| "넌 9번 터미널" / "T09" | T09 | Arc Generation & Validation |
| "넌 10번 터미널" / "T10" | T10 | Blueprint Generation & Validation |
| "넌 11번 터미널" / "T11" | T11 | Agent Infrastructure & Analyst |
| "넌 12번 터미널" / "T12" | T12 | State Tracking & World State |
| "넌 13번 터미널" / "T13" | T13 | Continuity System |
| "넌 14번 터미널" / "T14" | T14 | Validation Pipeline |
| "넌 15번 터미널" / "T15" | T15 | Quality Intelligence & Advisory Detection |
| "넌 16번 터미널" / "T16" | T16 | Database, Persistence & Logging |
| "넌 17번 터미널" / "T17" | T17 | Config, Constants, Prompts & Schemas |
| "넌 18번 터미널" / "T18" | T18 | Stage 0, Helpers & Narrative Utilities |
| "넌 19번 터미널" / "T19" | T19 | Desktop App & API Bridge |
| "넌 20번 터미널" / "T20" | T20 | Scripts, Tools, Cross-Cut Integrity & Regression |

**복수 터미널 동시 지시:**
- "넌 1번, 2번 터미널" → T01과 T02를 순차 수행
- "T07 T08 T09" → 세 터미널을 순차 수행
- 병렬은 별도 세션으로 분리해야 함 (아래 0-B 참조)

---

## 0-B. 병렬 실행 설계 및 주의사항

이 마스터 오더는 **20개 터미널을 최대 5개씩 병렬 실행**하는 것을 상정한다.

**병렬 실행 전제:**
- 각 터미널은 **독립된 Claude Code 세션** (별도 탭/창)에서 실행한다.
- 하나의 세션에서 20개를 순차 실행하는 것은 context window와 비용 면에서 비효율적이다.
- 최적 구성: 5개 세션 × 4 Phase, 또는 상황에 따라 2~4개 세션 유동 배분

**병렬 실행 시 알려진 위험:**
1. **파일 동시 읽기 — 안전**: 모든 터미널은 read-only이므로 동시 읽기 충돌 없음
2. **docs/mmmm/ 동시 쓰기 — 안전**: 각 터미널의 산출물 파일명이 `T{NN}-` 접두사로 고유하므로 충돌 없음
3. **git status 오염 — 주의**: 여러 세션이 동시에 파일을 생성하면 다른 세션의 `git status`에 untracked 파일이 보일 수 있음. 이는 정상이며 무시할 것
4. **context window 독립성**: 각 세션은 독립 context이므로 다른 터미널의 진행 상황을 볼 수 없음. Cross-Ref TF는 T20에서 사후 수합함
5. **코드 수정 방지**: 병렬 실행에서 하나의 터미널이라도 코드를 수정하면 다른 터미널의 조사 기반이 훼손됨. **코드 수정 절대 금지 규칙이 병렬 안전성의 핵심 전제**다

**단독 세션 실행 시:**
- "넌 N번 터미널" 한 번에 하나씩 순차 실행 가능
- 이 경우 Phase 순서를 따를 필요 없이 원하는 순서로 실행
- 단, T20은 T01~T19 산출물이 존재해야 교차 검증이 가능하므로 마지막에 실행

---

## 0. 용어 정의

| 용어 | 의미 |
|------|------|
| **TF** | Test Finding — 조사 중 발견한 개별 항목. 터미널 접두사 포함 (예: T03-TF-007) |
| **3pass 감리** | Pass 1 구조/범위, Pass 2 증거/일관성, Pass 3 실행가능성/가독성 |
| **적대적 3pass 감리** | 원본 감리자의 결론을 적극 반박하려는 시도로 3pass 재실행. 반박 실패 시에만 저장 허가 |
| **SYNC** | 테스트/문서와 live code가 일치 |
| **DRIFT** | 테스트/문서가 live code와 불일치 |
| **STALE** | 과거 시점에는 정확했으나 현재 유효한지 불확실 |
| **CONTRADICTION** | 두 증거 소스가 상호 모순 |

---

## 1. 전역 운영 규칙

### 1.0 대원칙: 정적 조사 + TF 다수 구성

**정적 조사 기본 원칙:**
- 이 전수조사는 **정적 코드 분석(static analysis)** 을 기본으로 한다.
- `pytest`, `python`, `node`, `npm` 등 **런타임 실행은 하지 않는다.**
- 증거 수집은 Read, Grep, Glob 등 **파일 읽기 도구만** 사용한다.
- 코드의 동작을 **실행해서 확인**하지 않고, **코드를 읽어서 추론**한다.
- 동적 검증이 필요한 항목은 TF의 Uncertainty 필드에 "동적 검증 필요"로 표기하고, 정적 증거 범위 내에서 결론을 낸다.

**TF 다수 구성 원칙:**
- 발견 항목은 **가능한 한 많은 TF로 분리 구성**하는 것이 기본이다.
- "별거 아닌 것 같아서 TF를 안 만들었다"는 허용하지 않는다.
- P4-OBSERVATION이라도 발견했으면 TF로 기록한다.
- TF 수가 적으면 조사가 부실한 것이다. TF 수가 많으면 조사가 충실한 것이다.
- 예상 TF 범위: 터미널당 최소 10개, 일반적으로 15~25개, T06/T14/T15/T20은 20개 이상 기대
- SYNC 확인도 TF다 — "X와 Y가 일치함"도 P4-OBSERVATION SYNC TF로 기록하라.
- 불확실하면 TF를 만들고 Uncertainty를 채워라. TF를 안 만드는 것보다 만들고 불확실하다고 적는 것이 낫다.

### 1.1 모드

- **survey-only** — 코드 수정, 패치, execution SSOT, roadmap, closure 절대 금지
- **정적 조사 기본** — 코드 실행(pytest, python, node 등) 금지. Read/Grep/Glob만 사용
- **side-effects 포함** — file write, DB write, JSONL, log, cache, global state, bootstrap fallback, config/env mutation 조사 포함
- **기존 docs는 참고용** — live workspace evidence가 authority

### 1.2 TF 구성 규칙

각 터미널은 발견 항목을 TF로 구성한다.

```
ID: T{NN}-TF-{NNN}
Severity: P0-CRITICAL | P1-HIGH | P2-MEDIUM | P3-LOW | P4-OBSERVATION
Category: DRIFT | STALE | CONTRADICTION | SIDE-EFFECT | CONTRACT-VIOLATION | COVERAGE-GAP | DEAD-CODE | RACE-CONDITION | SILENT-FAILURE | HARDCODING | UNBOUNDED | ENCODING
Surface: {파일 경로 또는 영역}
Evidence: {아래 코드 근거 규칙 참조}
Inference: {증거 기반 추론}
Uncertainty: {확신 못하는 부분}
Cross-Ref: {관련 다른 TF ID}
```

**TF 코드 근거 규칙 (EVIDENCE POLICY):**

Evidence 필드는 이 전수조사에서 **가장 중요한 필드**다. 코드 근거 없는 TF는 존재 가치가 없다.

모든 TF의 Evidence 필드에는 반드시 **구체적 코드 근거**를 포함해야 한다:

1. **파일:라인 필수** — `modules/core/stage4_interview_round.py:3658` 형식. "어딘가에 있다"식 서술 금지.
2. **코드 스니펫 인용** — 핵심 로직이면 해당 코드 3~10줄을 그대로 인용한다. 요약만으로는 부족하다.
3. **Grep 결과 근거** — 부재 증명(없음 확인)이면 사용한 grep 패턴과 결과를 기록한다. 예: `Grep "def deprecated_method" in modules/ → 0 matches`
4. **비교 근거** — DRIFT/CONTRADICTION이면 양쪽 코드를 나란히 인용한다. "테스트는 X를 기대하지만 live code는 Y다"를 양쪽 파일:라인과 코드로 보여줘야 한다.
5. **수치 근거** — 임계값, 상수, config 값이면 정의 위치(파일:라인)와 실제 값을 기록한다. 예: `validation.yaml:34 quality_gate_score: 90`
6. **호출 경로 근거** — "A가 B를 호출한다"면 호출하는 쪽의 파일:라인을 기록한다. 예: `stage4_interview_round.py:4037에서 quality_gate_score와 비교`
7. **부재 근거** — "X가 없다"면 어디를 찾았는데 없었는지 기록한다. 예: `main_a.py 전체 grep("write_back") → 0 matches, stage2_orchestrator.py grep("sync.*app") → line 847만 존재`

**나쁜 Evidence 예시 (금지):**
- "코드를 확인한 결과 문제가 있다" — 어떤 코드? 어느 라인?
- "테스트와 일치하지 않는다" — 어느 테스트의 어느 assertion? 어느 live code의 어느 라인?
- "여러 곳에서 사용된다" — 구체적으로 몇 곳? 각각 어디?

**좋은 Evidence 예시:**
```
Evidence:
  - modules/core/stage4_interview_round.py:3658-3680
    `_execute_pass_with_fix_loop()` max iteration = 3 (L3660: `for attempt in range(3):`)
  - tests/test_pass_with_fix.py:142
    테스트는 max 3회 루프를 가정: `assert mock_patch.call_count <= 3`
  - 양쪽 일치 확인 → SYNC
```

**TF 기타 요건:**
- Severity는 blast radius 기준 — P0은 데이터 손실/무한루프/보안, P1은 조용한 오동작, P2는 품질 저하, P3은 위생/유지보수, P4는 관측/개선
- 하나의 TF에 여러 이슈 혼합 금지 — 분리하라

### 1.3 문서 저장 규칙

**6pass 감리 후 저장:**

| Pass | 단계 | 내용 |
|------|------|------|
| 1 | 구조/범위 | 스코프 명확한가, 빠진 영역 없나, 섹션 구조 적절한가 |
| 2 | 증거/일관성 | 파일경로 정확한가, 라인번호 맞나, 내부 모순 없나, 수치 일치하나 |
| 3 | 실행가능성 | TF가 actionable한가, severity 적절한가, 과잉/과소 판단 없나 |
| 4 | 적대적 Pass 1 | "이 문서의 스코프는 과잉/누락이다"를 입증 시도 → 실패해야 통과 |
| 5 | 적대적 Pass 2 | "이 TF의 증거는 거짓/오해/과장이다"를 입증 시도 → 실패해야 통과 |
| 6 | 적대적 Pass 3 | "이 TF의 severity는 과대/과소이며 실제로는 무의미하다"를 입증 시도 → 실패해야 통과 |

- 적대적 pass에서 반박 성공 시: 해당 부분 수정 후 1~3 재실행
- 모든 pass 통과 후에만 파일 저장
- 저장 시 문서 상단에 `6PASS-CLEARED` 명시
- 확신도 95% 미달이면 추가 감리 반복

### 1.4 교차 검증 규칙

- 각 터미널은 자기 영역의 **인접 터미널 의존성**을 문서에 명시
- 인접 터미널이 같은 파일을 다룰 때: 각자 자기 관점에서 조사하되, 충돌 발견 시 Cross-Ref TF로 연결
- 터미널 20은 모든 터미널 산출물의 교차 무결성을 검증하는 전용 터미널

### 1.5 기존 TF 활용 규칙

- TF 계열 기존 회귀, 테스트, tagged audit 흔적, test fixtures, smoke/canary 근거가 있으면 적극 활용
- TF를 authority처럼 쓰지 말고, live code와 함께 evidence로만 사용
- TF와 live code가 충돌하면 충돌 자체를 CONTRADICTION TF로 기록

### 1.7 코드 수정 절대 금지 (HARD BLOCK)

**이 규칙은 이 마스터 오더에서 가장 중요한 불변식이다.**

코드 수정은 어떤 상황에서도, 어떤 이유로도, 어떤 형태로도 금지한다:

- **Edit 도구로 소스 코드 파일 수정 금지**
- **Write 도구로 소스 코드 파일 생성/덮어쓰기 금지**
- **Bash에서 sed, awk, echo >, cat << 등으로 소스 코드 변경 금지**
- **git checkout, git stash, git reset 등 working tree 변경 금지**
- **pyproject.toml, package.json, YAML config, .env 등 설정 파일 수정 금지**
- **"사소한 수정", "타이포 수정", "주석 추가", "import 정리"도 전부 금지**
- **"테스트를 위해 잠시 수정"도 금지 — 정적 조사만 수행**

수정 가능한 파일은 **오직 docs/mmmm/ 아래의 조사 산출물 문서뿐**이다.

이 규칙이 존재하는 이유:
1. 20개 터미널이 동일한 코드베이스를 병렬로 읽고 있다.
2. 하나의 터미널이 코드를 수정하면 다른 19개 터미널의 조사 근거가 무효화된다.
3. survey-only 모드의 핵심 전제다.

**위반 시 해당 터미널의 전체 산출물이 무효다.**

### 1.8 기타 절대 금지

- docs/temp/ mirror 생성
- execution SSOT 작성
- execution roadmap 작성
- resolved/regressed/final severity 선언
- policy verdict 확정
- 6pass 미완료 상태 저장
- pytest, python, node 등 런타임 실행 (정적 조사만 허용)

### 1.9 산출물 저장 경로 (단일 집결지)

**모든 터미널의 모든 산출물은 `docs/mmmm/` 에만 저장한다.**

- 산출물 파일: `docs/mmmm/T{NN}-{영역슬러그}-survey.md`
- 마스터 오더: `docs/mmmm/20-terminal-deep-global-survey-master-order.md` (이 파일)
- 다른 경로에 저장 금지 — `docs/2026-XX-XX/`, `docs/temp/`, `docs/implementation/` 등에 생성하지 않는다
- 20개 터미널 산출물 + 마스터 오더 = 최대 21개 파일이 `docs/mmmm/`에 모인다

---

## 2. 20-Terminal 영역 정의

### T01 — SovereignApp & Bootstrap

**범위:**
- `main_a.py` (4,891 lines) — SovereignApp 클래스 전체
- `.env` loading, `genai.Client` 초기화
- Lazy loading 패턴 (`_lazy_load_agents`, `_lazy_load_v50_modules`, `_lazy_load_stage0`)
- DI wiring: Stage2/3/4 orchestrator 생성, PromptBuilder, StateTracker 바인딩
- `_cumulative_state_cache`, `_cumulative_state_cache_key` sentinel
- Bootstrap fallback 경로
- 140+ attribute surface

**관련 테스트:**
- tests/test_integration.py
- tests/test_edge_cases.py
- Stage2/3/4 orchestrator의 `app` 파라미터 가정

**필수 조사:**
1. Lazy init 순서 의존성 — A가 B보다 먼저 init되어야 하는 암묵적 의존 있나
2. `None` → lazy init 사이 window에서 접근 시 AttributeError 경로
3. app 속성 중 dead code (어디서도 읽지 않는 속성)
4. DI context `.from_app(self)` 호출 시점과 lazy init 완료 시점 불일치 가능성
5. `_cumulative_state_cache_key` sentinel vs 0 vs None 혼동
6. Stage 종료 후 app write-back 누락 (Phase 2 교훈 재검증)
7. env var 의존성 전수 — GOOGLE_API_KEY 외 숨은 환경변수

**TF 최소 기대:**
- Dead attribute 목록
- Lazy init 순서 그래프
- Write-back 완전성 검증

---

### T02 — Stage 2 Orchestration & Context

**범위:**
- `modules/core/stage2_orchestrator.py` (1,072 lines)
- `modules/core/stage2_context.py` (44 __slots__)
- `modules/core/stage2_contracts.py`
- `modules/core/stage2_validation_pipeline.py` (1,195 lines)

**관련 테스트:**
- tests/test_stage2_orchestrator.py
- tests/test_stage2_pipeline.py
- tests/test_stage2_context.py (있으면)

**필수 조사:**
1. Stage2Context 44 slots 전수 — 각 slot의 producer(누가 설정), consumer(누가 읽음), 미사용 slot 식별
2. `sync_cache_key_to_app` 콜백 실제 동작 확인
3. orchestrator→app 간 state writeback 완전성 (13개 NPC 카테고리 교훈)
4. `_resolve_arc_number_for_episode()` fallback 로직과 edge case
5. arc_ensemble → orchestrator 간 오류 전파 경로
6. Stage2 validation pipeline의 validator 호출 순서와 단락(short-circuit) 규칙

**TF 최소 기대:**
- Slot 사용 매트릭스 (producer × consumer)
- Write-back 경로 완전성 검증
- Validation pipeline 흐름도

---

### T03 — Stage 2 Preflight, Finalizer & Optimizer

**범위:**
- `modules/core/stage2_preflight.py` (1,801 lines)
- `modules/core/stage2_finalizer.py` (2,165 lines)
- `modules/core/stage2_optimizer.py` (1,213 lines)

**관련 테스트:**
- tests/test_stage2_preflight.py (796 lines)
- tests/test_stage2_preflight_helpers.py (1,194 lines)
- tests/test_stage2_finalizer.py (663 lines)

**필수 조사:**
1. Preflight 체크 항목 전수 — 각 체크의 통과/실패 조건과 결과 action
2. Finalizer가 수행하는 DB write 전수 — 어떤 테이블에 무엇을 쓰나
3. Optimizer의 최적화 전략 목록과 각 전략의 side-effect
4. Preflight 실패 시 finalizer 진입 방지 guard 확인
5. Finalizer에서 예외 발생 시 partial write 상태 복구 여부
6. Optimizer의 score 기반 의사결정과 validation.yaml 임계값 참조

**TF 최소 기대:**
- Preflight 체크 목록
- Finalizer write surface 전수
- Optimizer 전략 분류표

---

### T04 — Stage 3 Pipeline

**범위:**
- `modules/core/stage3_orchestrator.py` (2,257 lines)
- `modules/core/stage3_context.py` (19 __slots__)
- `modules/core/quality_dashboard.py` (1,271 lines)

**관련 테스트:**
- tests/test_stage3_orchestrator.py (1,506 lines)
- tests/chaos/test_stage3_metrics.py (207 lines)
- tests/stage3_isolated_test/ (3 files, 900 lines)
- tests/e2e/test_l3_stage3_smoke.py

**필수 조사:**
1. Stage3Context 19 slots 전수 — lazy init 3메서드의 self.app 유지 패턴 확인
2. quality_dashboard recording 경로 — 어떤 이벤트가 어디에 기록되나
3. Stage3 → Stage4 handoff 데이터 구조
4. Blueprint 생성 실패 시 retry 로직과 fallback
5. stage3_isolated_test의 real API 호출 — 격리 수준 확인
6. quality_dashboard의 thread safety (concurrent recording)

**TF 최소 기대:**
- Stage3Context slot 사용 매트릭스
- QualityDashboard 기록 유형 전수
- Handoff 데이터 구조 문서화

---

### T05 — Stage 4 Core Orchestration

**범위:**
- `modules/core/stage4_orchestrator.py` (1,757 lines)
- `modules/core/stage4_context.py`
- `modules/core/stage4_context_builder.py` (2,975 lines)
- `modules/core/stage4_types.py` (_RoundContext, _InterviewRoundResult)
- `modules/core/stage4_canary_tools.py` (936 lines)

**관련 테스트:**
- tests/test_stage4_orchestrator.py (1,336 lines)
- tests/test_stage4_context_builder.py (1,663 lines)
- tests/test_stage4_context.py
- tests/test_stage4_cv_context.py

**필수 조사:**
1. Stage4Context `conditional_modules: dict` + `get_module(name)` 패턴 (S-13) 검증
2. _RoundContext dataclass 58 slots 전수 — 미사용/미설정 필드 식별
3. context_builder의 조립 순서 — 어떤 컴포넌트가 다른 컴포넌트 결과에 의존하나
4. canary_tools의 실제 호출 경로 — 프로덕션 코드에서 호출되나, 테스트 전용인가
5. Stage4 → quality_dashboard 기록 경로
6. Episode 순회 루프의 종료 조건과 early-exit 경로

**TF 최소 기대:**
- _RoundContext 필드 사용 매트릭스
- Context builder 조립 순서 그래프
- Canary tools 호출 경로 분류 (prod vs test-only)

---

### T06 — Stage 4 Interview & Post-Processing

**범위:**
- `modules/core/stage4_interview_round.py` (6,203 lines — 코드베이스 최대 파일)
- `modules/core/stage4_post_processor.py` (1,874 lines)

**관련 테스트:**
- tests/test_stage4_interview_round.py (3,771 lines)
- tests/test_stage4_post_processor.py (1,350 lines)
- tests/test_pass_with_fix.py (2,537 lines)

**필수 조사:**
1. `_execute_pass_with_fix_loop()` (L3658) — max 3회 루프의 탈출 조건 전수
2. Quality gate (L4037) — score < 90 시 PASS→REJECT 다운그레이드 경로
3. Advisory chain 8개 병렬 실행 (ThreadPoolExecutor, max_workers=8) — 타임아웃, 예외 처리
4. Per-advisory timeout 60s, overall timeout 300s — 타임아웃 발생 시 결과 처리
5. Interview round의 verdict 매핑: director verdict → final verdict 변환 규칙
6. Post-processor의 emotion tracking side-effect
7. EMPTY verdict 발생 조건과 처리 경로
8. 6,203 lines 내 dead code / unreachable path 식별

**TF 최소 기대:**
- PASS_WITH_FIX 루프 흐름도
- Advisory chain 장애 모드별 처리 매트릭스
- Dead code 후보 목록
- Verdict 변환 매핑표

---

### T07 — Director System

**범위:**
- `modules/domain/agents/director.py` (~260 lines, facade)
- `modules/domain/agents/director_auditor.py` (1,282 lines)
- `modules/domain/agents/director_ensemble.py` (1,952 lines)
- `modules/domain/agents/director_continuity.py` (868 lines)
- `modules/domain/agents/director_caching.py`
- `modules/domain/agents/director_grading.py`
- `modules/domain/agents/director_prompts.py`
- `modules/domain/agents/consensus_validator.py`

**관련 테스트:**
- tests/test_director_modules.py (1,699 lines)

**필수 조사:**
1. Facade 패턴 — director.py의 모든 public method가 sub-module로 위임되는가, 직접 구현이 남았나
2. Director audit verdict → PASS_WITH_FIX/REJECT/PASS 결정 로직
3. `_safe_int_score()` 안전 변환 — sweep31에서 수정된 패턴 현재 상태
4. Ensemble 3-way voting — 매칭 알고리즘과 동점 처리
5. Director continuity의 1M context caching (TTL 1800s) — 캐시 무효화 조건
6. Director grading의 graduated penalty (I-10): CRITICAL→max 15/40, MAJOR→-10, MINOR→-3 현재 구현
7. consensus_validator의 ComplianceLevel (FULL/PARTIAL/VIOLATION) 결정 기준

**TF 최소 기대:**
- Facade → sub-module 위임 매트릭스
- Verdict 결정 로직 흐름도
- Caching 무효화 조건 전수

---

### T08 — ChiefWriter System

**범위:**
- `modules/domain/agents/chief_writer.py` (2,015 lines)
- `modules/domain/agents/chief_writer_context.py` (1,362 lines)
- `modules/domain/agents/chief_writer_quality.py` (1,297 lines)
- `modules/domain/agents/chief_writer_prompts.py`
- `modules/domain/agents/writer.py`
- `modules/core/writer_prompt_builders.py`
- `modules/core/writer_template.py`
- `modules/core/writing_directive_generator.py`

**관련 테스트:**
- tests/test_chief_writer.py (1,460 lines)
- tests/test_chief_writer_context.py (341 lines)
- tests/test_chief_writer_quality.py (523 lines)
- tests/test_writer_prompt_builders.py (140 lines)

**필수 조사:**
1. `inplace_patch()` — 반환 구조, 최소 길이 2000자 검증, `[원고_끝]` 마커 제거, wrapper key 풀기
2. Quality gate `apply_self_critique()` — rubric ≥ 3.5 기준과 has_issues 플래그
3. ChiefWriter context caching (50,000자 이상, context cache) — 캐시 히트율 추적 여부
4. Writing directive generator의 반복 회피 패턴 — 이전 N 에피소드 분석 깊이
5. Prompt 조립 순서: COMMON_RULES → WRITING_GUIDELINES → genre-specific → PATCH_MODE
6. writer.py vs chief_writer.py 역할 분담 — 중복 또는 dead code 여부
7. SATISFACTION_GUIDE_SECTION 주입 조건

**TF 최소 기대:**
- inplace_patch 흐름도
- Prompt 조립 순서 다이어그램
- writer.py ↔ chief_writer.py 역할 매트릭스

---

### T09 — Arc Generation & Validation

**범위:**
- `modules/domain/agents/four_phase_arc_generator.py` (2,197 lines)
- `modules/domain/agents/arc_ensemble.py` (1,353 lines)
- `modules/domain/agents/arc_corrector.py`
- `modules/domain/agents/arc_critic.py`
- `modules/domain/agents/arc_draft_validator.py` (940 lines)
- `modules/domain/agents/unified_arc_validator.py` (728 lines)
- `modules/domain/agents/state_locked_arc_generator.py`

**관련 테스트:**
- tests/test_four_phase_arc_generator.py (501 lines)
- tests/test_unified_arc_validator.py
- tests/test_arc_patch_mode.py
- tests/test_arc_difficulty.py

**필수 조사:**
1. Four phase 구조: phase 1→2→3→4 각 phase의 입출력과 실패 시 행동
2. Arc ensemble 전략 생성 — 몇 개의 전략이 생성되고 어떻게 선택되나
3. Patch mode (score ≥ 50) vs full regeneration 분기
4. arc_draft_validator.validate — 3회 호출 패턴 (Phase 4-R1~R3 교훈)
5. Unified arc validator의 검증 항목과 합/불 기준
6. state_locked_arc_generator의 state constraint 고정 메커니즘
7. Arc critic의 int coercion 안전성 (sweep31 패치 확인)
8. tactical_doc 최소 기준 (ep_count × 500자, 1,500자 미만 = CRITICAL REJECT)

**TF 최소 기대:**
- Four phase 흐름도
- Ensemble 전략 목록
- Patch/regeneration 분기 조건표
- Validator 검증 항목 전수

---

### T10 — Blueprint Generation & Validation

**범위:**
- `modules/domain/agents/three_phase_blueprint_generator.py` (973 lines)
- `modules/domain/agents/blueprint_ensemble.py` (1,072 lines)
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/unified_blueprint_validator.py` (771 lines)
- `modules/domain/agents/constraint_compiler.py`
- `modules/core/constraint_db.py`

**관련 테스트:**
- tests/test_blueprint_patch_mode.py (688 lines)
- tests/test_blueprint_preflight.py
- tests/test_canonical_constraints.py

**필수 조사:**
1. Three phase 구조: 각 phase 입출력
2. Blueprint preflight (TF-49b) — numeric self-verification (NS-1 rule) 구현 상태
3. Constraint compiler의 constraint block 생성 — arc state에서 어떤 필드를 추출하나
4. Blueprint ensemble의 전략과 Director 심사 연계
5. Scene breakdown 3-5 scenes 제한 — 초과 시 행동
6. ending_hook mandatory — 누락 시 verdict 영향
7. ConstraintDB의 DB 의존성 — DB unavailable 시 fallback

**TF 최소 기대:**
- Three phase 흐름도
- Preflight 검증 항목 전수
- Constraint block 구조 문서

---

### T11 — Agent Infrastructure & Analyst

**범위:**
- `modules/domain/agents/base_agent.py` (2,213 lines)
- `modules/domain/agents/analyst.py` (1,849 lines)
- `modules/domain/agents/analyst_prompts.py` (747 lines)
- `modules/domain/agents/analyst_prompt_api.py`
- `modules/domain/agents/block_enricher.py` (935 lines)
- `modules/domain/agents/critic.py`
- `modules/domain/agents/weaver.py`
- `modules/domain/agents/manager.py`
- `modules/domain/agents/preflight_checker.py`
- `modules/domain/agents/negative_example_injector.py`

**관련 테스트:**
- tests/test_base_agent.py (993 lines)

**필수 조사:**
1. BaseAgent의 `self.ask()` — LLM 호출 추상화의 retry, timeout, error handling 전수
2. `_extract_json_robust()` — JSON 파싱 fallback 경로 (regex, 부분 추출 등)
3. Context caching (L1599-1820) — `_get_or_create_context_cache()` + `_ask_with_cached_context()`
4. 캐시 최소 요건 50,000자 — 미달 시 자동 skip 확인
5. Analyst의 10+ ask() 호출 패턴 — 반복 컨텍스트 30-50K 비용 문제 (OPT-1 후보)
6. Block enricher의 3x compression 로직
7. Critic/Weaver/Manager의 역할 — dead code 또는 legacy 여부
8. negative_example_injector의 few-shot 주입 메커니즘
9. preflight_checker의 검증 범위

**TF 최소 기대:**
- BaseAgent public API 전수 (ask, extract, cache 등)
- JSON parsing fallback 경로 매트릭스
- Agent별 역할/호출빈도 분류표

---

### T12 — State Tracking & World State

**범위:**
- `modules/domain/agents/state_tracker.py` (1,668 lines)
- `modules/domain/agents/state_tracker_npc.py` (2,204 lines)
- `modules/domain/agents/state_tracker_financial.py`
- `modules/domain/agents/state_tracker_plots.py` (963 lines)
- `modules/domain/agents/state_extractor.py` (868 lines)
- `modules/core/world_state.py` (1,338 lines)
- `modules/core/fact_ledger.py` (852 lines)

**관련 테스트:**
- tests/test_state_tracker.py (525 lines)
- tests/test_npc_history.py (374 lines)
- tests/test_npc_history_fields.py (229 lines)
- tests/test_con2_npc_position_tracking.py (367 lines)
- tests/test_fact_ledger.py

**필수 조사:**
1. StateTracker facade → 3 sub-module 위임 완전성
2. `full_extract_from_arcs()` 통합 메서드 — Stage2/3/4 인라인 루프 제거 검증 (Phase 2 교훈)
3. NPC state 추출: 13개 카테고리 전수 — 누락된 카테고리 없나
4. World state 9개 필드 (`_INIT_STATE`) 전수 — 갱신 경로와 비차단 갱신 확인
5. FactLedger MAX_HISTORY_PER_ENTITY=10, MAX_SUMMARY_CHARS=20000 — 초과 시 eviction 로직
6. State extractor의 `_state_cache` — 캐시 무효화 조건
7. Financial state tracker의 investment-specific 추출 필드
8. Plot tracker의 resolved_plots 추적

**TF 최소 기대:**
- 13개 NPC 카테고리 사용 매트릭스
- World state 갱신 경로 전수
- FactLedger eviction 로직 검증

---

### T13 — Continuity System

**범위:**
- `modules/domain/agents/continuity_inspector.py`
- `modules/domain/agents/continuity_arc.py` (1,026 lines)
- `modules/domain/agents/continuity_blueprint.py`
- `modules/domain/agents/continuity_manuscript.py` (1,234 lines)
- `modules/domain/agents/continuity_tracker.py`
- `modules/core/continuity_pin_guard.py`
- `modules/validation/continuity_validator.py` (1,282 lines)

**관련 테스트:**
- tests/test_continuity_modules.py (1,165 lines)
- tests/test_continuity_packet.py (574 lines)

**필수 조사:**
1. ContinuityInspector facade → 4 sub-module 위임 패턴 확인
2. Arc continuity — 아크 간 상태 연속성 검증 항목 전수
3. Blueprint continuity — 블루프린트↔아크 정합성 검증 항목
4. Manuscript continuity — 원고↔블루프린트 정합성 검증 항목
5. continuity_pin_guard의 pin 고정 메커니즘 — 어떤 값이 pin되나
6. Continuity validator (validation tier 0.5) — violation → -5/violation, cap -15 구현 확인
7. Continuity tracker의 V49.7 feature flag 상태

**TF 최소 기대:**
- Inspector → sub-module 위임 매트릭스
- 검증 항목 전수 (arc, blueprint, manuscript)
- Pin guard 고정 대상 목록

---

### T14 — Validation Pipeline

**범위:**
- `modules/validation/validation_orchestrator.py` (1,702 lines)
- `modules/validation/blocking_validator.py` (208 lines) + entity_checks (511), scene_checks (442), consistency_checks (385)
- `modules/validation/scoring_validator.py` (1,274 lines)
- `modules/validation/consistency_validator.py` (616 lines)
- `modules/validation/pre_llm_validator.py` (515 lines)
- `modules/validation/advisory_validator.py` (235 lines)
- `modules/validation/retrospective_validator.py` (365 lines)
- `modules/validation/batch_validator.py` (299 lines)
- `modules/validation/action_scene_evaluator.py` (455 lines)
- `modules/validation/catharsis_timer.py` (395 lines)
- `modules/validation/threshold_helper.py` (24 lines)
- `modules/validation/dialogue_utils.py` (33 lines)

**관련 테스트:**
- tests/test_validation.py (614 lines)
- tests/test_validation_orchestrator.py (117 lines)
- tests/test_validation_orchestrator_soft_failure.py
- tests/test_pass_with_fix.py (교차: T06)
- tests/chaos/test_validation_degrade.py (121 lines)
- tests/property/test_validation_props.py (246 lines)

**필수 조사:**
1. 6-tier 파이프라인 실행 순서 (`validate_v59()`) — 각 tier의 선행 조건
2. Parallel validation (`validate_parallel_v59()`, 3 workers) — 동시 실행 tier와 격리
3. Self-consistency 3-vote — 조건부 활성화 (50 ≤ score ≤ 60), 비용 절감 검증
4. Adaptive threshold 계산: base + ep_adjust + streak + pattern + arc_position, clamp [60,90]
5. Blocking → advisory 변환 — failures가 score penalty로 변환되는 정확한 경로
6. Retrospective validator — lookback 10 episodes, severity-based penalty (-5 to -15)
7. CatharsisTimer — max_gap=3 초과 시 penalty
8. ActionSceneEvaluator — 0-10 점수 → ±2~±3 조정
9. Pre-LLM 9개 체크 전수
10. Batch validator의 stats Lock (D-2 수정 확인)

**TF 최소 기대:**
- 6-tier 파이프라인 흐름도 (순차 + 병렬 모드)
- Adaptive threshold 공식 검증
- Pre-LLM 9개 체크 목록
- Scoring breakdown 6 dimensions 가중치 검증

---

### T15 — Quality Intelligence & Advisory Detection

**범위:**
- `modules/core/adversarial_self_play.py`
- `modules/core/chain_of_verification.py`
- `modules/core/self_reflection.py`
- `modules/core/cross_agent_verifier.py`
- `modules/core/constitutional_checker.py`
- `modules/core/tree_of_thoughts.py`
- `modules/core/multi_agent_deliberation.py`
- `modules/core/agent_intelligence.py`
- `modules/core/confidence_calibration.py`
- `modules/core/expert_mixture.py`
- `modules/core/reflexion_manager.py`
- `modules/core/truth_gate.py`
- `modules/core/info_paradox_checker.py`
- `modules/core/npc_drift_advisor.py`
- `modules/core/numeric_drift_advisor.py`
- `modules/core/numeric_consistency_checker.py` (1,000 lines)
- `modules/core/relationship_drift_advisor.py`
- `modules/core/flashback_verifier.py`
- `modules/core/long_term_repetition_advisor.py`
- `modules/core/investment_math_verifier.py`
- `modules/core/investment_arithmetic_checker.py`
- `modules/core/semantic_query_broker.py`

**관련 테스트:**
- tests/test_truth_gate.py, test_info_paradox_checker.py, test_npc_drift_advisor.py
- tests/test_numeric_consistency_checker.py, test_numeric_drift_advisor.py
- tests/test_flashback_verifier.py, test_relationship_drift_advisor.py
- tests/test_semantic_query_broker.py
- tests/test_context_advisor.py

**필수 조사:**
1. Advisory chain 8개 중 LLM 7개 + Python-only 1개 (NumericConsistencyChecker) 구분 확인
2. 각 advisory의 입력/출력 contract — 어떤 데이터를 받고 어떤 형태의 suggestion을 반환하나
3. Constitutional checker 조항 전수: Stage 2 (A1-A6), Stage 3 (B1-B5), Stage 4 (M1-M8)
4. AdversarialSelfPlay 결정: PASS/REVISE/REJECT — Director와 중복/충돌 여부
5. ChainOfVerification severity: NONE/MINOR/MAJOR/CRITICAL — 각 severity 트리거 조건
6. SelfReflection improvement_score (0-1) — 임계값과 재생성 결정
7. CrossAgentVerifier compliance: FULL/PARTIAL/VIOLATION — Arc→Blueprint, Blueprint→Manuscript
8. TreeOfThoughts, MultiAgentDeliberation, ExpertMixture — 실제 프로덕션 코드에서 호출되나
9. Investment math verifier — leverage ROI formula 검증 정확성

**TF 최소 기대:**
- Advisory 8개 입출력 contract 매트릭스
- Constitutional checker 조항 전수표
- Quality intelligence 모듈별 프로덕션 호출 여부 분류

---

### T16 — Database, Persistence & Logging

**범위:**
- `modules/core/db_manager.py` (3,986 lines)
- `modules/core/vec_memory.py` (1,331 lines)
- `modules/core/session_logger.py`
- `modules/core/services/audit_service.py` (316 lines)
- `modules/core/artifact_logging.py`
- `modules/core/jsonl_io.py`
- `modules/core/data_collector.py`
- `modules/core/material_db.py`
- `modules/core/metrics_collector.py`
- `modules/core/soft_failure.py`

**관련 테스트:**
- tests/test_db_manager.py (759 lines)
- tests/test_db_utilization.py (311 lines)
- tests/test_db_efficiency_transactions.py (65 lines)
- tests/test_db_integrity_recovery.py (27 lines)
- tests/test_db_merge.py (136 lines)
- tests/test_db_cursor_live_inventory.py (115 lines)
- tests/test_vec_memory.py (819 lines)
- tests/test_audit_service.py (454 lines)
- tests/test_artifact_logging.py

**필수 조사:**
1. DB manager — 모든 CREATE TABLE 스키마 전수
2. DB write surface — INSERT/UPDATE/DELETE 전수 (어떤 메서드가 어떤 테이블에 쓰나)
3. DB 트랜잭션 — 명시적 BEGIN/COMMIT/ROLLBACK 여부
4. VecMemory sqlite-vec 의존성 — 미설치 시 fallback 경로
5. Session logger — 로그 파일 경로, 로테이션 정책 (max_file_mb=100, max_rotations=10)
6. Audit service — runtime_audit.jsonl, runtime_audit_summary.json 쓰기 경로
7. Artifact logging — 저장 경로, 파일명 패턴, 정리 정책 유무
8. JSONL I/O — 읽기/쓰기 원자성, 파일 잠금 여부
9. Soft failure — soft_failures.jsonl 쓰기 경로와 구조
10. `_cumulative_bible_cache` 캐시 무효화 경로

**TF 최소 기대:**
- DB 스키마 전수
- Write surface 매트릭스 (메서드 × 테이블)
- 모든 파일 I/O 경로 전수

---

### T17 — Config, Constants, Prompts & Schemas

**범위:**
- `modules/core/config_manager.py`
- `modules/core/models_config.py`
- `modules/core/constants.py` (893 lines)
- `modules/core/prompt_builder.py` (968 lines)
- `modules/core/prompt_loader.py`
- `modules/core/response_schemas.py` (923 lines)
- `modules/core/llm_schema.py`
- `modules/core/llm_router.py`
- `modules/core/llm_provider.py`
- `modules/core/llm_generate.py`
- `modules/core/providers/` (4 provider files)
- `config/system.yaml`, `config/models.yaml`
- `config/settings/validation.yaml`
- `config/settings/item_suffixes.yaml`
- `config/prompts/` (9 YAML files)
- `config/genres/` (10 YAML files)
- `config/smart_retrieval/genre_hints.yaml`
- `config/tone_presets.json`
- `config/settings.json`

**관련 테스트:**
- tests/test_llm_schema.py
- tests/test_genre_schema_builder.py
- tests/test_prompt_builder.py (524 lines)
- tests/test_context_window_utilization.py (406 lines)

**필수 조사:**
1. _LazyThreshold 디스크립터 — 모든 인스턴스 전수와 fallback default 값
2. ConfigManager → validation.yaml 키 전수 — 코드에서 참조하는 키 vs YAML에 정의된 키 불일치
3. PromptLoader singleton — 스레드 안전성, 캐시 무효화
4. Response schemas — Gemini response_schema 포맷 호환성 (enum, required, nullable 등)
5. LLM router — provider 선택 로직, fallback chain (pro→flash)
6. Provider별 (gemini, anthropic, openai, vertex) 구현 상태 — 비활성 provider가 dead code인가
7. 9 prompt YAML V70 버전 — 각 YAML 내 template key가 코드에서 실제 참조되는가
8. 10 genre YAML — forbidden_terms 전수가 guard 코드와 일치하나
9. validation.yaml 50+ 키 — 각 키의 코드 참조 전수 (미참조 키 = dead config)

**TF 최소 기대:**
- _LazyThreshold 인스턴스 전수표
- validation.yaml 키 참조 매트릭스
- Provider 활성/비활성 분류
- Prompt template key ↔ 코드 참조 매핑

---

### T18 — Stage 0, Helpers & Narrative Utilities

**범위:**
- `modules/core/stage0/` (6 files, 5,688 lines): __init__.py, preset_registry.py, reverse_expander.py, story_expander.py, style_extractor.py, spinner.py
- `modules/core/stage0_handoff.py`
- `modules/core/stage01_helpers.py` (924 lines)
- `modules/core/genre_guards/` (14 files, 7,608 lines)
- `modules/core/narrative_context_formatter.py`
- `modules/core/narrative_diversity.py`
- `modules/core/narrative_structure_analyzer.py`
- `modules/core/pattern_tracker.py` (1,209 lines)
- `modules/core/emotion_tracker.py`
- `modules/core/character_voice.py`, `character_voice_profiler.py`
- `modules/core/pacing_analyzer.py`
- `modules/core/feedback_system.py` (931 lines)
- `modules/core/failure_analyzer.py` (1,962 lines)
- `modules/core/failure_learning.py`
- `modules/core/adaptive_retry.py` (858 lines)
- `modules/core/foreshadow_tracker.py`
- `modules/core/repetition_guard.py`
- `modules/core/diversity_sampler.py`
- `modules/core/power_scaling.py`
- `modules/core/jianghu_logic.py`
- `modules/core/primitive_guard.py`
- `modules/core/dynamic_prompt_weighting.py`

**관련 테스트:**
- tests/test_stage0_fixes.py
- tests/test_stage01_helpers.py (690 lines)
- tests/test_feedback_system.py (647 lines)
- tests/test_failure_analyzer.py (1,178 lines)
- tests/test_genre_guard.py, test_genre_guards_extended.py, test_style_guard.py, test_work_guard.py (741 lines)
- tests/test_narrative_context_formatter.py (359 lines)
- tests/test_repetition_guard.py (198 lines)
- tests/test_cross_episode_repetition.py (163 lines)
- tests/test_long_term_repetition.py (182 lines)

**필수 조사:**
1. Stage 0 초기화 흐름 — genre 선택 → bible 생성 → treatment 로드 → style guide
2. Genre guard chain: GenreGuard → WorkGuard(optional) → StyleGuard(optional) — 체인 누락/중복
3. WorkGuard YAML 오버레이 — work_guard.yaml 구조와 base guard 확장 메커니즘
4. Pattern tracker lookback_episodes=5 — 패턴 감지 정확도와 false positive 가능성
5. Failure analyzer 1,962 lines — 분석 카테고리 전수
6. Adaptive retry 전략 전수 — default, two_phase, tot, asp, mad
7. Repetition guard — 감지 임계값과 advisory 출력 구조
8. Emotion tracker — 3+ episodes 연속 부정/긍정 감지 → 권고 생성
9. Stage0 SPINNER_AVAILABLE flag 상태

**TF 최소 기대:**
- Genre guard chain 흐름도
- Failure analyzer 카테고리 전수
- Retry 전략 분류표
- Stage 0 초기화 흐름도

---

### T19 — Desktop App & API Bridge

**범위:**
- `geuldobi-desktop/src/main.js`
- `geuldobi-desktop/src/preload.js`
- `geuldobi-desktop/src/index.html`
- `geuldobi-desktop/src/console_relay.js`
- `geuldobi-desktop/src/desktop_control_plane_contract.js`
- `geuldobi-desktop/src/desktop_bridge_client.js`
- `geuldobi-desktop/src/quality_page_bootstrap.js`
- `geuldobi-desktop/src/quality_react_helpers.js`
- `geuldobi-desktop/src/quality_react_runtime.js`
- `geuldobi-desktop/src/renderer_state_bootstrap.js`
- `geuldobi-desktop/src/renderer_state_react_helpers.js`
- `geuldobi-desktop/src/splash/` (3 files)
- `geuldobi-desktop/package.json`
- `geuldobi-desktop/DESKTOP-GUIDE.md`
- `modules/api/bridge_server.py` (2,320 lines)
- `modules/api/process_runner.py` (808 lines)
- `modules/api/prompt_broker.py` (205 lines)
- `modules/api/prompt_classifier.py` (172 lines)
- `modules/api/run_validator.py` (95 lines)
- `modules/api/risk_approval.py` (214 lines)
- `modules/api/control_plane_contract.py` (92 lines)
- `modules/core/services/` (4 service files, 1,678 lines)
- `docs/implementation/desktop-ipc-surface-contract-v1.json`
- `docs/implementation/event-schema-v1.json`
- `docs/implementation/surface-containment-contract-v1.json`
- `docs/implementation/desktop-runtime-contract-v1.json`

**관련 테스트:**
- tests/test_desktop_direct_surface_contract.py (400 lines)
- tests/test_desktop_contract_refresh.py (223 lines)
- tests/test_desktop_transport_contract.py (232 lines)
- tests/test_desktop_shadow_hygiene.py (68 lines)
- tests/test_desktop_packaging_contract.py (95 lines)
- tests/test_desktop_backend_restart_guard.py (124 lines)
- tests/test_desktop_project_name_sanitization.py (untracked)
- tests/test_desktop_settings_recovery.py (untracked)
- tests/test_desktop_preload_bridge_behavior.js
- tests/test_bridge_quality_summary.py (944 lines)
- tests/test_shipping_reality_live_surface_guide.py (59 lines)

**필수 조사:**
1. 26 IPC preload methods — 각 method의 구현 경로 (preload → main → bridge_server)
2. Dead candidate methods — contract에 0이지만 실제 dead method 없는지 검증
3. Shadow surface 2개 — 진짜 stale인가, 아직 참조되는가
4. Bridge server route 전수 — HTTP + WebSocket 엔드포인트
5. Process runner — Python backend 시작/중지/재시작 로직
6. Prompt broker — desktop ↔ CLI 프롬프트 연결
7. Event schema v1 — 8 event types 실제 emission 경로
8. Desktop build 설정 — package.json extraResources 경로와 실제 파일 존재 확인
9. React runtime — vendor files 존재, bundle 전략
10. Service layer (audit, project, state, ui) — bridge_server와의 연결

**TF 최소 기대:**
- IPC method ↔ 구현 매핑표 (26개)
- Bridge route 전수
- Event emission 경로 매핑
- Build artifact 존재 검증

---

### T20 — Scripts, Tools, Cross-Cut Integrity & Regression

**범위:**
- `scripts/` (37 Python files)
- `tools2/` (20 Python files)
- `pyproject.toml`
- `.editorconfig`, `.gitattributes`
- `modules/protocols/` (4 files)
- `modules/models/` (4 files)
- `modules/core/runtime_paths.py`
- `modules/core/studio_visualizer.py`
- `modules/core/system.py`
- `modules/core/perf_timer.py`
- `modules/core/spinners.py`
- `modules/core/smoke_fixture_tools.py`
- `modules/core/escape_utils.py`
- `modules/core/error_helper.py`
- `modules/core/logging_keys.py`
- `modules/core/hud_utils.py`
- `modules/core/tactical_utils.py`
- `modules/core/arc_state_utils.py`
- `modules/core/arc_summary_utils.py`
- `modules/core/inventory_state.py`
- `modules/core/lore_manager.py`
- `modules/core/martial_manager.py`
- `modules/core/semantic_item_registry.py`
- `modules/core/semantic_plot_guard.py`
- `modules/core/information_diffusion.py`
- `modules/core/justification_patterns.py`
- `modules/core/karma_service.py`
- `modules/core/genre_hud_manager.py`
- `modules/core/genre_schema_builder.py`
- `modules/core/quality_amplifier.py`
- `modules/core/quality_constitution.py`
- `modules/core/quality_sidecar_bootstrap.py`
- `modules/core/quality_signal_metrics.py`
- `modules/core/reference_anchor.py`
- `modules/core/context_compression.py`
- `modules/core/pre_director_checklist.py`
- `modules/core/pre_director_manuscript_checker.py`
- `modules/core/pre_director_narrative_checker.py`
- `modules/core/pre_director_style_checker.py`
- `modules/core/state_delta_tracker.py`
- `modules/core/state_text_verifier.py`
- `modules/core/stagewise_manuscript_truth_report.py`
- `modules/core/technique_weaver.py`
- `modules/core/slack_bot.py`
- 전 터미널 교차 무결성 검증

**관련 테스트:**
- tests/test_sweep{3-39}.py (26 sweep files)
- tests/test_opus_tf5_e6_regressions.py
- tests/test_legacy_reentry_reaudit.py
- tests/test_tools2_cost_tables.py
- tests/test_pass_rate_monitor_rol.py
- tests/test_tier4_ensemble_caching.py
- tests/test_v55_modules.py
- tests/e2e/ 전체
- tests/chaos/ 전체
- tests/property/ 전체

**필수 조사:**

A. Scripts 분류:
1. 모든 scripts/ 파일 분류 — 운영(ops), 스모크(smoke), 빌드(build), 데이터(data), 검증(validation)
2. 각 script의 side-effect — 파일 쓰기, DB 변경, 외부 호출
3. tools2/ 분류 — production-useful vs legacy vs one-off
4. Dead script 식별 — 어디서도 호출되지 않는 script

B. Cross-Cut Integrity:
5. Encoding guardrails — .editorconfig UTF-8 pin + check_utf8_hygiene.py 실행 경로
6. Protocol/Model 정의 — modules/protocols/*.py, modules/models/*.py 사용 범위
7. Config ↔ code alignment — validation.yaml 키 전수 vs 코드 참조
8. Prompt template key ↔ PromptLoader 참조 정합성
9. Genre guard YAML ↔ guard Python 정합성

C. Regression Verification:
10. 26 sweep test 전수 — 각 sweep이 어떤 버그를 고정하는가, 여전히 유효한가
11. Feature flag 양방향 테스트 여부 — V50=True/False, STAGE0=True/False
12. 테스트 fixture와 runtime bootstrap 가정 차이
13. E2E/chaos/property 테스트의 환경 의존성

D. 교차 무결성:
14. T01~T19 산출물에서 보고된 Cross-Ref TF를 수합하여 교차 검증
15. 터미널 간 중복 발견 정리
16. 터미널 간 모순 발견 분리

**TF 최소 기대:**
- Script 분류표 (37개)
- Tools2 분류표 (20개)
- Dead code 후보 목록
- Config↔code alignment 매트릭스
- 26 sweep TF 유효성 검증표
- 교차 무결성 매트릭스

---

## 3. 터미널 간 의존 관계

```
T01 (SovereignApp)
├─ T02, T03 (Stage 2)
├─ T04 (Stage 3)
├─ T05, T06 (Stage 4)
├─ T12 (State Tracking) — app write-back
└─ T17 (Config) — bootstrap config loading

T02 (Stage 2 Orch) ↔ T03 (Stage 2 Preflight/Finalizer)
T04 (Stage 3) → T05 (Stage 4 Orch) — handoff
T05 (Stage 4 Orch) ↔ T06 (Stage 4 Interview)
T06 (Stage 4 Interview) → T07 (Director) — verdict
T06 (Stage 4 Interview) → T08 (ChiefWriter) — manuscript
T07 (Director) ↔ T15 (Quality Intelligence) — quality feedback
T09 (Arc Gen) → T10 (Blueprint Gen) — arc→blueprint
T09, T10 → T13 (Continuity) — continuity check
T11 (BaseAgent) → T07, T08, T09, T10, T15 — agent infrastructure
T12 (State) ↔ T13 (Continuity) — state/continuity data
T14 (Validation) ↔ T06 (Interview) — validation results
T14 (Validation) ↔ T15 (Quality Intel) — advisory integration
T16 (DB) → T01, T02, T04, T05, T12 — persistence layer
T17 (Config) → ALL — config/constants/prompts
T18 (Stage 0/Helpers) → T01, T02 — initialization/utilities
T19 (Desktop/API) → T16 (DB) — bridge→DB
T20 (Cross-Cut) ← ALL — receives all cross-refs
```

---

## 4. 터미널별 공통 프롬프트 템플릿

각 터미널에 아래 프롬프트를 기반으로 지시한다. `{변수}`를 터미널별로 치환한다.

**간편 실행**: 사용자가 "넌 N번 터미널"이라고만 하면, 이 마스터 오더를 읽고 아래 프롬프트를 자동 적용한다.

```
시스템 트랙 오더다. narrative pipeline으로 해석하지 마라.

반드시 먼저 읽을 것:
- AGENTS.md
- docs/mmmm/20-terminal-deep-global-survey-master-order.md
  → 섹션 0-A (디스패치), 0-B (병렬 주의사항), 1 (전역 운영 규칙) 전체
  → 섹션 2 에서 자기 터미널(T{NN}) 섹션

너는 Terminal {NN}이다. 영역: {영역명}.

=== 너의 역할 ===
- 기초 자료 수집자, evidence organizer, TF constructor
- execution SSOT 작성자가 아니다
- 코드 수정 권한이 없다

=== 조사 방식 ===
- 정적 조사만 수행한다 (Read, Grep, Glob 도구만 사용)
- pytest, python, node 등 런타임 실행 금지
- 코드의 동작을 실행해서 확인하지 않고, 코드를 읽어서 추론한다
- survey-only mode — 구현, 패치, execution SSOT, roadmap, closure 하지 않는다
- side-effects 조사를 기본 포함한다
- 기존 docs는 참고용일 뿐 authority가 아니다
- live workspace evidence를 우선한다

=== 코드 수정 절대 금지 (HARD BLOCK) ===
Edit, Write, Bash(sed/awk/echo) 등 어떤 수단으로든 소스 코드/설정 파일 수정 금지.
"사소한 수정", "타이포 수정", "주석 추가"도 전부 금지.
수정 가능한 파일은 docs/mmmm/ 아래의 조사 산출물 문서뿐이다.
위반 시 전체 산출물이 무효다. 20개 터미널이 동일 코드베이스를 병렬로 읽고 있다.

=== TF 구성 규칙 (핵심 원칙) ===
- 모든 발견은 TF로 구성한다 (T{NN}-TF-NNN)
- TF를 많이 만드는 것이 좋다. TF가 적으면 조사가 부실한 것이다.
- P4-OBSERVATION이라도 TF로 기록한다. SYNC 확인도 TF다.
- 불확실하면 TF를 만들고 Uncertainty를 채워라
- Severity: P0-CRITICAL | P1-HIGH | P2-MEDIUM | P3-LOW | P4-OBSERVATION
- Category: DRIFT | STALE | CONTRADICTION | SIDE-EFFECT | CONTRACT-VIOLATION | COVERAGE-GAP | DEAD-CODE | RACE-CONDITION | SILENT-FAILURE | HARDCODING | UNBOUNDED | ENCODING
- 인접 터미널과 겹치는 발견은 Cross-Ref로 연결
- 터미널당 최소 10개 TF, 일반적으로 15~25개 기대

=== TF 코드 근거 규칙 (가장 중요) ===
- Evidence 없는 TF 금지. 코드 근거 없으면 TF가 아니다.
- 반드시 파일:라인 형식으로 기록 (예: modules/core/stage4_interview_round.py:3658)
- 핵심 로직이면 해당 코드 3~10줄을 그대로 인용
- 부재 증명이면 grep 패턴과 0 matches를 기록
- DRIFT/CONTRADICTION이면 양쪽 코드를 나란히 인용
- 임계값/상수면 정의 위치(파일:라인)와 실제 값을 기록
- "확인한 결과 문제가 있다" 같은 모호한 서술 금지 — 어떤 파일 어느 라인인지 써라

=== 문서 저장 규칙 ===
- 6pass 감리 (3pass 표준 + 적대적 3pass) 통과 후에만 저장
- 파일: docs/mmmm/T{NN}-{영역슬러그}-survey.md (이 경로에만 저장!)
- 상단에 6PASS-CLEARED / COLLECTOR ONLY / NO EXECUTION AUTHORITY 명시
- facts, inferences, uncertainty를 분리해 쓸 것
- 확신도 95% 미달이면 추가 감리 반복

=== 범위 ===
{범위 파일 목록}

=== 필수 조사 항목 ===
{필수 조사 항목 전체}

=== 산출물 최소 구조 ===
1. Scope & Files
2. TF Registry (전체 TF 목록 — 최소 10개)
3. Evidence Inventory
4. Side-Effect Surface
5. Facts
6. Inferences
7. Uncertainty / Contradictions
8. Cross-Ref to Adjacent Terminals
9. Candidate Watchlist
10. 6Pass Audit Log (각 pass 결과 기록)

=== 절대 금지 ===
- 소스 코드/설정 파일 수정 (HARD BLOCK)
- pytest/python/node 등 런타임 실행
- docs/temp/ mirror 생성
- execution SSOT 작성
- resolved/regressed/final severity 선언
- policy verdict 확정
- 6pass 미완료 상태 저장
```

---

## 5. 실행 순서 권장

### Phase 1 — Foundation (병렬 5개)
T01 (SovereignApp), T11 (BaseAgent), T16 (DB), T17 (Config), T20 (Cross-Cut 사전 준비)

### Phase 2 — Stage Pipeline (병렬 5개)
T02 (Stage 2 Orch), T03 (Stage 2 Preflight), T04 (Stage 3), T05 (Stage 4 Orch), T06 (Stage 4 Interview)

### Phase 3 — Domain Agents (병렬 5개)
T07 (Director), T08 (ChiefWriter), T09 (Arc Gen), T10 (Blueprint Gen), T12 (State Tracking)

### Phase 4 — Quality & Auxiliary (병렬 5개)
T13 (Continuity), T14 (Validation), T15 (Quality Intel), T18 (Stage 0/Helpers), T19 (Desktop/API)

### 최종 — Cross-Cut 통합
T20 (교차 무결성 최종 수합) — Phase 1~4 산출물 전량 수합 후 교차 검증

**각 Phase 내에서는 5개 터미널을 완전 병렬 실행한다.**
**Phase 간에는 순차 실행이 이상적이나, 독립적인 터미널은 Phase 경계 없이 시작 가능하다.**

---

## 6. 산출물 인벤토리 (예상)

| 터미널 | 파일명 | 예상 TF 수 |
|--------|--------|-----------|
| T01 | T01-sovereign-app-bootstrap-survey.md | 10-20 |
| T02 | T02-stage2-orch-context-survey.md | 8-15 |
| T03 | T03-stage2-preflight-finalizer-survey.md | 10-18 |
| T04 | T04-stage3-pipeline-survey.md | 8-15 |
| T05 | T05-stage4-orch-context-survey.md | 10-18 |
| T06 | T06-stage4-interview-postproc-survey.md | 15-25 |
| T07 | T07-director-system-survey.md | 10-18 |
| T08 | T08-chief-writer-system-survey.md | 10-18 |
| T09 | T09-arc-generation-validation-survey.md | 10-15 |
| T10 | T10-blueprint-generation-validation-survey.md | 8-15 |
| T11 | T11-agent-infra-analyst-survey.md | 10-18 |
| T12 | T12-state-tracking-world-state-survey.md | 10-18 |
| T13 | T13-continuity-system-survey.md | 8-15 |
| T14 | T14-validation-pipeline-survey.md | 15-25 |
| T15 | T15-quality-intel-advisory-survey.md | 15-25 |
| T16 | T16-database-persistence-logging-survey.md | 12-20 |
| T17 | T17-config-constants-prompts-schemas-survey.md | 12-20 |
| T18 | T18-stage0-helpers-narrative-utils-survey.md | 12-20 |
| T19 | T19-desktop-api-bridge-survey.md | 12-20 |
| T20 | T20-crosscut-regression-integrity-survey.md | 20-30 |
| **합계** | **20 문서** | **220-370 TF** |

---

## 7. 품질 게이트

### 7.1 개별 터미널 게이트

- [ ] 6pass 감리 완료 (3pass + 적대적 3pass)
- [ ] 확신도 95% 이상
- [ ] 모든 TF에 Evidence 필드 존재
- [ ] 인접 터미널 Cross-Ref 명시
- [ ] Side-effect surface 조사 포함 (또는 비적용 명시)
- [ ] 문서 상단에 6PASS-CLEARED 명시

### 7.2 전체 번들 게이트 (T20 책임)

- [ ] 20개 문서 전량 수합
- [ ] 터미널 간 TF 중복 제거
- [ ] 터미널 간 모순 식별 및 CONTRADICTION TF 발행
- [ ] 커버리지 갭 식별 (어떤 파일도 조사하지 않은 영역)
- [ ] 전체 TF 수합 및 severity 분포 보고

---

## 8. 마스터 오더 자체 감리 기록

### Rev 2 (2026-03-20) — 사용자 피드백 반영

추가된 내용:
- 섹션 0-A: 빠른 디스패치 — "넌 N번 터미널" 매핑표 + 복수 터미널 지시 규칙
- 섹션 0-B: 병렬 실행 설계 — 전제, 위험, 단독 세션 실행 안내
- 섹션 1.0: 대원칙 — 정적 조사 기본 + TF 다수 구성 원칙 (최소 10개/터미널, SYNC도 TF)
- 섹션 1.1: 정적 조사 기본 모드 추가
- 섹션 1.7: 코드 수정 절대 금지 (HARD BLOCK) — 10개 항목 구체 나열, 위반 시 산출물 무효
- 섹션 1.8: 런타임 실행 금지 추가
- 섹션 1.9: 단일 집결지 규칙 — docs/mmmm/ 외 저장 금지
- 섹션 4: 프롬프트 템플릿 강화 — 코드 수정 HARD BLOCK, 정적 조사, TF 다수 구성, 런타임 금지 반영

### Pass 1 (구조/범위)
- 20개 터미널이 코드베이스 전체를 빈틈없이 커버하는가: modules/ 160+ files 전수 배정됨, tests/ 관련 테스트 배정됨, config/ T17 배정, scripts/tools2 T20 배정, desktop T19 배정, main_a.py T01 배정 → **PASS**
- 영역 중복: T14(validation) ↔ T15(advisory detection)에서 advisory_validator 경계 확인 필요 → advisory_validator는 T14(파이프라인 tier)에 배정, 개별 advisory detector(truth_gate 등)는 T15에 배정 → 명확히 분리 → **PASS**
- 문서 구조: 디스패치, 병렬 주의, 용어 정의, 대원칙, 운영 규칙, 영역 정의, 의존 관계, 템플릿, 실행 순서, 산출물, 품질 게이트 → **PASS**
- 빠른 디스패치 매핑표: 20개 터미널 전수 포함, 단축 지시 3종 이상 → **PASS**
- 코드 수정 금지 강도: HARD BLOCK, 10개 구체 항목, 위반 시 무효 선언, 병렬 안전성 근거 → **PASS**
- 정적 조사 원칙 명시: 1.0, 1.1, 1.8, 프롬프트 템플릿 4곳에 반복 → **PASS**
- TF 다수 구성 원칙 명시: 1.0에 원칙, 프롬프트에 "최소 10개" + "많을수록 충실" → **PASS**
- 단일 집결지: 1.9에 docs/mmmm/ 외 저장 금지 명시 → **PASS**

### Pass 2 (증거/일관성)
- 라인 수 정확성: `wc -l` 결과 기반 — main_a.py 4,891, stage4_interview_round 6,203, db_manager 3,986 → **PASS**
- 파일 경로 정확성: `find` 결과 기반, 모든 경로 실존 확인 → **PASS**
- 터미널 간 의존 그래프 내부 일관성: T05↔T06 교차, T07→T06 verdict, T11→all agents → **PASS**
- TF numbering scheme 일관성: T{NN}-TF-{NNN} 형식 → **PASS**
- 디스패치 매핑표 ↔ 섹션 2 영역명 일치 → **PASS**

### Pass 3 (실행가능성)
- 실행 순서 Phase 1~4: 5개씩 4 phase → 총 4 round + T20 최종 → 실행 가능 → **PASS**
- 프롬프트 템플릿: "넌 N번 터미널"만으로 즉시 실행 가능하도록 자족적 → **PASS**
- 품질 게이트: 개별 + 전체 체크리스트 → **PASS**
- 병렬 실행 가이드: 5개 세션 × 4 Phase 구성, 위험 5가지 명시 → **PASS**

### 적대적 Pass 4 (스코프 과잉/누락 반박 시도)
- "T20이 너무 많은 것을 담고 있다" → T20은 의도적으로 잡다한 utility + 교차 검증을 합쳤음. Cross-Cut은 T20의 핵심 역할이며 scripts/tools2는 다른 터미널에 맞지 않음 → **반박 실패, PASS**
- "modules/ui/ 가 누락되었다" → modules/ui/__init__.py만 존재 (빈 모듈), UI/ 디렉토리는 binary assets → 코드 없음 → **반박 실패, PASS**
- "tests/ 하위 디렉토리(e2e, chaos 등)가 특정 터미널에 배정 안됨" → 각 터미널에 관련 테스트 배정됨 + T20에 e2e/chaos/property 전체 배정 → **반박 실패, PASS**
- "정적 조사만으로 충분한가, 런타임 실행이 필요하지 않은가" → TF Uncertainty 필드로 동적 검증 필요 항목을 별도 표기하도록 설계됨. 정적 증거 범위 내에서 결론 가능 → **반박 실패, PASS**

### 적대적 Pass 5 (증거 거짓/오해 반박 시도)
- "라인 수가 dirty state 기준이라 정확하지 않다" → `wc -l`은 현재 working tree 기준이며 이 문서의 baseline과 일치 → **반박 실패, PASS**
- "일부 파일이 Stage 2와 Stage 4에 중복 배정되었다" → 각 터미널의 범위 파일 목록은 중복 없이 배정됨 (검증 완료) → **반박 실패, PASS**
- "코드 수정 금지가 너무 과하다" → 병렬 조사의 무결성 전제이며, survey-only 모드의 본질. 사용자 명시 요청 → **반박 실패, PASS**

### 적대적 Pass 6 (severity/의의 반박 시도)
- "20개 터미널은 과잉이다, 10개면 충분하다" → 사용자가 명시적으로 20개를 요청함. modules/ 160+ files + tests/ 328 files 규모에서 20개는 10-15 files/터미널로 적정 → **반박 실패, PASS**
- "예상 TF 220-370개는 과대 추정이다" → TF 다수 구성이 원칙. P4-OBSERVATION + SYNC 포함 시 파일당 1-2개는 보수적 추정 → **반박 실패, PASS**
- "TF 최소 10개가 너무 높다" → 10개 TF는 파일 5-10개 범위에서 파일당 1-2개 수준. 정적 조사로 발견 가능한 항목(dead code, 미사용 import, 경계값, side-effect 등) 감안 시 합리적 → **반박 실패, PASS**

**6PASS-CLEARED** — 확신도 97%
