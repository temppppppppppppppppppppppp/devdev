# 글도비 Debug Sweep v2 — 100 라운드 완전 자립형 오더

> 이 문서 하나만 읽으면 된다. 다른 문서 참조 불필요.
> 결과는 `docs/codex_findings_v2.md`에 기록한다.
> **코드를 수정(edit)하지 마라. 탐지·보고만 한다.**

---

## 1. 미션

`modules/` + `main_a.py`의 Python 프로덕션 코드(~99,000줄, 210파일)에서 **런타임 크래시 또는 잘못된 결과를 유발하는 실제 버그**를 찾아라.

**보고 금지 항목**: 코드 스타일, 네이밍, 리팩토링 제안, 성능 최적화, 타입 힌트 부재, 테스트 코드(`tests/`) 버그, 문서/주석 품질.

---

## 2. 시스템 개요

AI 웹소설 자동 생성 파이프라인. Python 3.12 + Google Gemini API.

```
Stage 0 (초기 설정) → Stage 2 (Arc 생성) → Stage 3 (Blueprint) → Stage 4 (원고 집필)
```

핵심 설계:
- **Entry point**: `main_a.py` → `SovereignApp` 클래스 (2,997줄)
- **DI 패턴**: `StageNContext.from_app(app)` → Orchestrator는 `self.ctx`로 접근
- **LLM 호출**: 에이전트 `self.ask()` → JSON → `self._extract_json_robust()` 파싱
- **DB**: SQLite (`db_manager.py`), `check_same_thread=False` + RLock
- **Guard 체인**: GenreGuard → WorkGuard → StyleGuard
- **에러 정책**: CRITICAL=re-raise, IMPORTANT=log+safe default, OPTIONAL=pass
- **inventory 데이터**: `items_acquired`, `physical_inventory` 리스트에 string 또는 dict(`{"name": "검", "quantity": 1}`) 혼재 가능

---

## 3. 찾아야 할 버그 패턴

### Tier 1 — 크래시 유발 (CRITICAL)
- `dict.get()` 반환 None에 `.속성` / `[키]` / `.split()` 호출
- `json.loads()` 결과가 list인데 `.get()` 호출
- `int()` / `float()`에 None/빈 문자열 전달
- `str.split()` 후 인덱스 접근 시 원소 부족
- `max()` / `min()`에 빈 시퀀스 전달
- 0으로 나누기 (분모가 `len()`, `count` 등 동적 값)
- `set()` / `set.update()`에 unhashable 타입 (dict 원소) 전달
- `re.compile()` / `re.search()`에 유효하지 않은 패턴 전달 (사용자/LLM 입력 미이스케이프)

### Tier 2 — 잘못된 결과 (HIGH)
- dead store: 값 대입 후 미사용 → 이후 로직이 stale 값 사용
- `.get("key", default)` default 타입이 사용처 기대 타입과 불일치
- dict 기대 위치에 string/list 유입 (또는 반대)
- 조건문 and/or 혼동, not 누락, 비교 방향 반전
- 캐시 변경 후 관련 캐시 무효화(= None) 누락
- f-string/.format() 중괄호 이스케이프 누락
- 하드코딩 값으로 인해 기능이 실질적으로 비활성화된 경우

### Tier 3 — 엣지 케이스 (MEDIUM)
- Episode 1에서 `episode - 1 = 0`이 빈 결과를 만드는 경우
- 단일 Arc 루프/인덱싱 실패
- LLM 응답이 빈 문자열 / None / 예상 밖 구조
- `re.compile()` 패턴에 사용자 입력이 이스케이프 없이 전달
- 문자열 기대 위치에 int/float 유입 (LLM 응답 경유)

---

## 4. ⛔ 오탐 방지 — 아래는 버그가 아니다

아래 10가지를 버그로 보고하면 **오탐**이다. 발견 시 반드시 이 목록과 교차 확인하라.

### FP-1. 비차단 갱신 (Non-blocking updates)
```python
try:
    world_state.save()
except Exception as e:
    logger.warning("저장 실패: %s", e)  # ← 의도된 설계
```
`WorldState`, `FactLedger`, `ChainLink`, `VolumeSummary`, `NPC이력` 저장은 **모두 비차단**. except에서 pass/warning만 하는 것은 정상.

### FP-2. Advisory 시스템 (관측 전용)
`quality_regression`, `npc_overexposure`, `cross_episode_repetition`, `pacing_analyzer`, `diversity_tracker`, `satisfaction_framework` — 로그/경고만 출력, 파이프라인 동작 불변. "결과 미사용"으로 보고 금지.

### FP-3. DI Context 스냅샷
```python
ctx = Stage2Context.from_app(app)
# ctx 수정이 app에 반영 안 되는 것 = 의도된 설계. 콜백만 app 직접 호출.
```

### FP-4. getattr 방어 패턴
```python
tracker = getattr(self.ctx, "state_tracker", None)
if tracker and hasattr(tracker, "npc_registry"): ...
```
lazy init 전 안전 접근. "항상 None" 보고 금지 — init 이후 값 있음.

### FP-5. LLM 응답의 관대한 파싱
```python
result = self._extract_json_robust(response)
if not result or not isinstance(result, dict):
    return fallback
```
LLM 응답 불확실 → 타입 체크 + 폴백은 정상.

### FP-6. JSON string DB 저장
`snapshot_and_reset_scope()` → JSON string 반환 → `save_cost_record()` → SQLite TEXT 저장. 의도된 설계.

### FP-7. `_patch_fallback` 플래그
patch 실패 후 regen 성공 시 `_patch_fallback=True` 유지 = 정상.

### FP-8. pass_threshold 동적 조정
`ScoringValidator.pass_threshold` 런타임 변경 = 적응형 난이도 시스템.

### FP-9. `_check_hud_anomalies` 빈 결과 반환
HUD 데이터 소스 미구현 상태. 항상 `has_anomalies=False` 반환하는 것은 알려진 설계 갭. 버그 아님.

### FP-10. 에러 정책 분류 주석
`# [V64.P4] OPTIONAL:` 주석 + pass/warning은 의도된 에러 정책. "에러 무시" 보고 금지.

---

## 5. ★★★ 라운드별 필수 출력 형식 ★★★

### 모든 라운드에서 파일마다 반드시 아래 4개 섹션을 작성하라.

```markdown
## Round N — [파일명]

### 5-A. 파일 구조 요약 (필수)
이 파일의 클래스/주요 함수를 나열하라. 최소 5개.
각 함수에 **정확한 시그니처**(파라미터명, 기본값)를 포함하라.
예시:
- `class Stage4Orchestrator` — 원고 생성 오케스트레이션
- `def run_interview_loop(self, session, *, limit_mode=False)` (L45) — 메인 루프
- `def _prepare_context(self, arc_data: dict, ep_num: int)` (L120) — 컨텍스트 준비
- `def _handle_rejection(self, round_ctx, feedback: str)` (L200) — REJECT 처리
- `def _finalize_pass(self, result: dict, session)` (L300) — PASS 후처리

### 5-D. 읽기 증명 (필수) ★신규★
파일을 실제로 읽었다는 것을 증명하기 위해 아래 3개를 작성하라.
이 섹션이 비어있거나 부정확하면 **해당 라운드 전체가 무효**다.

1. **마지막 함수**: 파일의 마지막 함수/메서드 이름과 그 시작 라인 번호
   예: `def _cleanup_session(self, ...)` (L782)
2. **특징적 문자열**: 파일 안에 있는 로그 메시지, 에러 메시지, 또는 주석 중 하나를 **정확히** 복사
   예: `logging.warning("⚠️ [V66.1] 시간선 검사 오류: %s", _tc_err)`
3. **import 목록**: 이 파일이 import하는 프로젝트 내부 모듈 (외부 라이브러리 제외) 최소 3개
   예: `from modules.core.stage4_context_builder import Stage4ContextBuilder`
        `from modules.core.stage4_interview_round import InterviewRound`
        `from modules.core.stage4_post_processor import Stage4PostProcessor`

### 5-B. 위험 지점 분석 (필수, 최소 3개)
Tier 1~3 패턴에 해당할 *가능성*이 있는 코드 위치를 최소 3개 찾아서,
각각 **안전한 이유** 또는 **버그인 이유**를 코드를 인용하며 설명하라.

**각 위험 지점마다 반드시 포함할 것:**
1. 정확한 라인의 **코드 원문** (copy-paste)
2. 그 코드의 **호출자(caller)** — 누가 이 함수를 호출하고 어떤 값을 넘기는지
3. 상류/하류의 **다른 라인 번호와 코드** — 가드가 있으면 그 가드 코드, 없으면 없다고 명시

예시 (안전한 경우):
> **위험 지점**: L156 `scores.get("quality")` 반환 None에 비교 연산
> **호출자**: `_evaluate_manuscript()` L89에서 `scores = self._compute_scores(text)` → `_compute_scores`는 항상 dict 반환 (L200~210)
> **판정**: 안전 — L155에서 `if not scores: return default` 가드 존재

예시 (버그인 경우):
> **위험 지점**: L230 `int(arc_data.get("ep_count"))` — None 전달 시 TypeError
> **호출자**: `_stage2_flow_guard()` L597에서 `ep_count = refined_arc.get("ep_count", 0)` → SelfReflector 경로에서 string "5" 유입 가능
> **판정**: BUG — ep_count 키가 없으면 None, int(None) 크래시. L604 이전에 int 캐스트 없음.

### 5-C. 발견된 버그 (있을 때만)
아래 형식으로 기록:

### [CRITICAL/HIGH/MEDIUM] 파일:라인 — 한줄 요약

**문제**: 어떤 입력/상태에서 어떤 에러가 발생하는지 구체적으로
**문제 코드**:
```python
# 해당 코드 복사 (정확히 copy-paste, 줄여쓰기 금지)
```
**호출 체인**: 이 코드가 실행되기까지의 경로 (함수A L100 → 함수B L200 → 여기)
**수정 제안**:
```python
# 수정된 코드
```
**확신도**: HIGH/MEDIUM/LOW
**FP 체크**: FP-1~10 해당 여부 확인 결과

---
## Round N 완료
```

### ❗ "없음" 금지 규칙
- 5-A(파일 구조), 5-D(읽기 증명), 5-B(위험 지점)는 **발견 0건이어도 반드시 작성**한다.
- 5-B에서 위험 지점을 분석한 결과 모두 안전하면, 각각 왜 안전한지 코드를 인용하여 설명한다.
- 5-C(버그)만 0건일 수 있다. 5-A, 5-D, 5-B가 비어있으면 **파일을 안 읽은 것으로 간주**한다.

### ❗ 5-D 검증 기준
검토자는 5-D의 3개 항목을 **실제 파일과 대조**한다:
- **마지막 함수** 이름과 라인이 실제와 ±5줄 이내로 일치하는가?
- **특징적 문자열**이 실제 파일에 존재하는가? (grep으로 검증)
- **import 목록**이 실제 파일의 import와 일치하는가?
→ 3개 중 2개 이상 불일치하면 해당 라운드는 **위조로 판정**, 전체 결과 신뢰도 하락.

### ❗ 5-B 품질 기준
5-B의 위험 지점 분석은 다음을 **반드시** 포함해야 한다:
1. **구체적 라인 번호 + 코드 원문** — `L156`이 아니라 `L156: scores = arc_data.get("quality_scores")` 처럼 해당 줄의 실제 코드를 **copy-paste**
2. **호출자 정보** — 이 코드를 실행시키는 상위 함수와 전달되는 인수. "어디서 호출되는지 모름"이면 그렇게 명시
3. **상류/하류 컨텍스트** — "L155에 가드가 있어서 안전" 같이, 판정 근거가 되는 **다른 라인의 코드 원문**도 인용
4. **구체적 실패 시나리오** — "ep_count가 None이면" 같이, 어떤 입력/상태에서 문제가 되는지 명시

아래는 **불합격 예시** (기계적 패턴 매칭으로 생성된 것):
```
> **위험 지점 1**: `state_service.py:45` `json.loads(data)`
> **판정**: 잠재 위험 — LLM/외부 입력 파싱 결과 shape가 dict/list 혼재 가능
```
↑ 이런 식의 일반론은 **위조로 간주**한다. 실제 코드를 읽었다면 `data`가 어디서 오는지, 후속 코드가 list를 처리하는지 등을 구체적으로 쓸 수 있다.

아래는 **합격 예시**:
```
> **위험 지점 1**: L251 `"ep_end": arc_data.get("ep_start", 1) + arc_data.get("ep_count", VolumeSettings.EPISODES_PER_ARC) - 1`
> Analyst(L430)가 LLM 응답에서 ep_start를 파싱할 때 string "5"가 들어올 수 있음.
> arc_data.get("ep_start", 1)은 키가 존재하면 string을 그대로 반환 → "5" + int = TypeError.
> L255~258의 repair 루프는 이 산술 이후에 실행되므로 보호 불가.
> **판정**: BUG — int() 캐스트 필요
```

---

## 6. 라운드 배정 (100 라운드)

### Phase 1 — Stage 4 원고 파이프라인 (Round 1~18)

| Round | 파일 | 줄수 | 집중 체크리스트 |
|-------|------|------|----------------|
| 1 | `modules/core/stage4_orchestrator.py` | 818 | □ 루프 종료 조건 □ 재시도 카운터 리셋 □ ctx 속성 None 체크 |
| 2 | `modules/core/stage4_interview_round.py` | 655 | □ arc_data 키 접근 □ record_attempt 파라미터 □ 폴백 반환 타입 |
| 3 | `modules/core/stage4_context_builder.py` | 585 | □ dict 조립 시 None 체인 □ 키 누락 폴백 □ 타입 불일치 |
| 4 | `modules/core/stage4_post_processor.py` | 575 | □ DB 저장 후 캐시 무효화 □ safe_commit 반환값 □ state_changes 타입 |
| 5 | `modules/core/stage4_context.py` (134) + `modules/core/pass_rate_monitor.py` (550) | 684 | □ DI 슬롯 vs 실제 사용 □ 0 나누기 □ 빈 리스트 통계 |
| 6 | `modules/domain/agents/chief_writer.py` | 873 | □ ask() 실패 처리 □ 점수 비교 타입 □ manuscript 길이 검증 □ facade 위임 완전성 |
| 7 | `modules/domain/agents/chief_writer_context.py` | 1083 | □ 대형 dict 조립 □ 키 누락 시 폴백 □ list vs string □ NPC 데이터 순회 |
| 8 | `modules/domain/agents/chief_writer_quality.py` | 476 | □ 정규식 이스케이프 □ 점수 타입 □ 빈 리스트 통계 |
| 9 | `modules/domain/agents/chief_writer_prompts.py` | 279 | □ f-string 포맷팅 □ 템플릿 키 정합 □ None 삽입 |
| 10 | `modules/domain/agents/director.py` (329) + `modules/domain/agents/director_ensemble.py` (519) | 848 | □ facade 위임 누락 □ 앙상블 투표 집계 □ 빈 후보 처리 |
| 11 | `modules/domain/agents/director_auditor.py` | 1056 | □ 감사 점수 산출 □ 0 나누기 □ 다중 에이전트 결과 병합 |
| 12 | `modules/domain/agents/director_grading.py` | 654 | □ 채점 가중치 합산 □ 부분 점수 타입 □ 빈 카테고리 |
| 13 | `modules/domain/agents/director_continuity.py` | 763 | □ 연속성 비교 □ 에피소드 경계 □ 캐시 컨텍스트 |
| 14 | `modules/domain/agents/director_prompts.py` (445) + `modules/domain/agents/director_caching.py` (175) | 620 | □ 프롬프트 키 정합 □ 캐시 무효화 □ 타입 캐스트 |
| 15 | `modules/domain/agents/manuscript_validator.py` | 1032 | □ 원고 검증 점수 □ 결과 dict 키 정합 □ 길이 비교 |
| 16 | `modules/domain/agents/block_enricher.py` | 871 | □ 블록 보강 타입 □ LLM 파싱 □ 누락 블록 처리 |
| 17 | `modules/domain/agents/writer.py` (370) + `modules/core/writer_prompt_builders.py` (237) | 607 | □ 외부 진입점 계약 □ HUD 조회 □ 프롬프트 조립 |
| 18 | `modules/core/writer_template.py` (418) + `modules/core/manuscript_enhancer.py` (777) | 1195 | □ 템플릿 치환 □ 텍스트 후처리 □ 정규식 그룹 |

### Phase 2 — Stage 2 Arc 파이프라인 (Round 19~33)

| Round | 파일 | 줄수 | 집중 체크리스트 |
|-------|------|------|----------------|
| 19 | `modules/core/stage2_orchestrator.py` | 807 | □ 상태 전이 □ 에러 복구 경로 □ 루프 탈출 조건 |
| 20 | `modules/core/stage2_preflight.py` | 745 | □ parallel 결과 병합 □ 분석 점수 합산 □ None 분기 |
| 21 | `modules/core/stage2_validation_pipeline.py` | 706 | □ 검증 점수 합산 □ ep_count 타입 □ flow guard 분기 |
| 22 | `modules/core/stage2_finalizer.py` | 619 | □ joint_docs 타입 □ state_changes 구조 □ DB 커밋 에러 □ inventory dict 처리 |
| 23 | `modules/core/stage2_optimizer.py` | 934 | □ 상태 스냅샷 타입 □ 누적 set 연산 □ 프롬프트 조립 |
| 24 | `modules/core/stage2_context.py` (229) + `modules/core/stage3_context.py` (107) + `modules/core/stage4_context.py` (134) | 470 | □ __slots__ vs 실사용 정합 □ from_app 바인딩 누락 □ 콜백 시그니처 |
| 25 | `modules/domain/agents/analyst.py` L1~750 | 750 | □ LLM JSON 파싱 □ 대형 dict 반환 키 정합 □ ep_count/ep_start 타입 |
| 26 | `modules/domain/agents/analyst.py` L751~끝 | 744 | □ NPC 추출 □ 상태 분석 □ arc 결과 조립 |
| 27 | `modules/domain/agents/analyst_prompts.py` (766) + `modules/domain/agents/analyst_prompt_api.py` (91) | 857 | □ 프롬프트 키 정합 □ 파라미터 전달 □ 템플릿 포맷 |
| 28 | `modules/domain/agents/arc_corrector.py` | 578 | □ 교정 비율 계산 □ 텍스트 비교 □ LLM 파싱 |
| 29 | `modules/domain/agents/arc_critic.py` (367) + `modules/domain/agents/arc_ensemble.py` (690) | 1057 | □ 비평 점수 □ 앙상블 투표 집계 □ 빈 결과 처리 |
| 30 | `modules/domain/agents/arc_draft_validator.py` | 858 | □ 검증 다단계 □ 중복 아이템 검사 □ 정규식 패턴 |
| 31 | `modules/domain/agents/four_phase_arc_generator.py` | 743 | □ 4단계 생성 □ 상태 잠금 □ 폴백 반환 |
| 32 | `modules/domain/agents/state_locked_arc_generator.py` | 571 | □ 상태 고정 검증 □ 생성 실패 처리 □ 반환 타입 |
| 33 | `modules/domain/agents/unified_arc_validator.py` (632) + `modules/domain/agents/preflight_checker.py` (492) | 1124 | □ 통합 검증 □ 중복 아이템 □ preflight 체크 |

### Phase 3 — Stage 3 Blueprint (Round 34~38)

| Round | 파일 | 줄수 | 집중 체크리스트 |
|-------|------|------|----------------|
| 34 | `modules/core/stage3_orchestrator.py` | 526 | □ lazy init 동기화 □ ctx 속성 접근 □ 에러 복구 |
| 35 | `modules/domain/agents/blueprint_ensemble.py` | 684 | □ 앙상블 투표 □ POV 처리 □ 빈 후보 |
| 36 | `modules/domain/agents/three_phase_blueprint_generator.py` | 430 | □ 3단계 생성 □ LLM 파싱 □ 폴백 |
| 37 | `modules/domain/agents/unified_blueprint_validator.py` | 440 | □ blueprint 검증 □ 점수 산출 □ 반환 계약 |
| 38 | `modules/domain/agents/blueprint_constraint_compiler.py` (434) + `modules/domain/agents/constraint_compiler.py` (394) | 828 | □ 제약 컴파일 □ 타입 정합 □ 빈 제약 |

### Phase 4 — Validation 모듈 (Round 39~48)

| Round | 파일 | 줄수 | 집중 체크리스트 |
|-------|------|------|----------------|
| 39 | `modules/validation/validation_orchestrator.py` L1~700 | 700 | □ pass/fail 판정 □ 점수 합산 타입 □ 조건부 skip |
| 40 | `modules/validation/validation_orchestrator.py` L701~끝 | 711 | □ 다중 validator 결과 병합 □ 에러 복구 □ 최종 verdict |
| 41 | `modules/validation/scoring_validator.py` L1~500 | 500 | □ 임계값 비교 □ 적응형 조정 □ 빈 점수 |
| 42 | `modules/validation/scoring_validator.py` L501~끝 | 511 | □ 카운터 오버플로 □ 가중치 합산 □ 0 나누기 |
| 43 | `modules/validation/pre_llm_validator.py` | 492 | □ 사전 검증 □ 카운터 □ POV 체크 |
| 44 | `modules/validation/blocking_validator.py` (193) + `blocking_validator_entity_checks.py` (470) + `blocking_validator_scene_checks.py` (455) | 1118 | □ blocking 조건 □ 엔티티 체크 □ 장면 체크 |
| 45 | `modules/validation/blocking_validator_consistency_checks.py` (377) + `modules/validation/consistency_validator.py` (597) | 974 | □ 일관성 체크 □ 에피소드 간 비교 □ 타입 |
| 46 | `modules/validation/continuity_validator.py` | 976 | □ 연속성 검증 □ 에피소드 경계 □ NPC 상태 비교 |
| 47 | `modules/validation/batch_validator.py` (298) + `modules/validation/retrospective_validator.py` (362) + `modules/validation/advisory_validator.py` (181) | 841 | □ 배치 검증 □ 회고 검증 □ 자문 검증 |
| 48 | `modules/validation/action_scene_evaluator.py` (455) + `modules/validation/catharsis_timer.py` (223) + `modules/validation/threshold_helper.py` (22) | 700 | □ 액션 평가 □ 카타르시스 타이머 □ 임계값 헬퍼 |

### Phase 5 — 상태 추적 + 연속성 (Round 49~60)

| Round | 파일 | 줄수 | 집중 체크리스트 |
|-------|------|------|----------------|
| 49 | `modules/domain/agents/state_tracker.py` | 1453 | □ NPC registry dict □ extract 루프 □ 이력 append □ full_extract_from_arcs |
| 50 | `modules/domain/agents/state_tracker_npc.py` L1~1000 | 1000 | □ NPC 등록/갱신 □ 관계 변경 □ 사망 처리 |
| 51 | `modules/domain/agents/state_tracker_npc.py` L1001~끝 | 1005 | □ NPC 검증 □ 이력 조회 □ 정리 로직 |
| 52 | `modules/domain/agents/state_tracker_plots.py` | 942 | □ 플롯 추적 누적 □ resolved 처리 □ 캐시 정합 |
| 53 | `modules/domain/agents/state_extractor.py` | 850 | □ 상태 추출 □ LLM 파싱 □ 캐시 키 |
| 54 | `modules/domain/agents/state_tracker_financial.py` (126) + `modules/core/state_delta_tracker.py` (419) | 545 | □ 재정 추적 □ 델타 비교 □ 타입 |
| 55 | `modules/domain/agents/continuity_inspector.py` | 546 | □ 연속성 facade □ 위임 완전성 □ 에러 전파 |
| 56 | `modules/domain/agents/continuity_manuscript.py` | 1216 | □ 원고 연속성 □ 에피소드 간 비교 □ NPC 상태 |
| 57 | `modules/domain/agents/continuity_arc.py` | 1002 | □ Arc 연속성 □ 상태 비교 □ 빈 이력 |
| 58 | `modules/domain/agents/continuity_blueprint.py` (472) + `modules/domain/agents/continuity_tracker.py` (385) | 857 | □ Blueprint 연속성 □ 추적 누적 □ 타입 |
| 59 | `modules/core/world_state.py` (426) + `modules/core/fact_ledger.py` (540) | 966 | □ 롤백 리플레이 □ 상태 병합 □ entity 이력 제한 |
| 60 | `modules/domain/agents/consensus_validator.py` (453) + `modules/core/cross_agent_verifier.py` (492) | 945 | □ 합의 검증 □ 교차 검증 □ 결과 병합 |

### Phase 6 — 핵심 인프라 (Round 61~72)

| Round | 파일 | 줄수 | 집중 체크리스트 |
|-------|------|------|----------------|
| 61 | `modules/core/db_manager.py` L1~800 | 800 | □ SQL 파라미터 타입 □ RLock 범위 □ 테이블 생성 |
| 62 | `modules/core/db_manager.py` L801~끝 | 864 | □ 조회 결과 파싱 □ 캐시 무효화 □ 마이그레이션 |
| 63 | `modules/domain/agents/base_agent.py` L1~600 | 600 | □ ask() 재시도 □ JSON 파싱 □ 캐시 컨텍스트 |
| 64 | `modules/domain/agents/base_agent.py` L601~끝 | 629 | □ _extract_json_robust □ 응답 타입 분기 □ 에러 처리 |
| 65 | `modules/core/prompt_builder.py` | 957 | □ f-string 이스케이프 □ 캐시 키 □ 타임라인 조립 |
| 66 | `modules/core/prompt_loader.py` (193) + `modules/core/prompt_optimizer.py` (399) | 592 | □ YAML 로드 □ 키 검증 □ 최적화 로직 |
| 67 | `modules/core/project_manager.py` | 940 | □ 롤백 로직 □ 에피소드 관리 □ 파일 I/O |
| 68 | `modules/core/services/state_service.py` (356) + `services/project_service.py` (273) + `services/ui_service.py` (129) + `services/audit_service.py` (92) | 850 | □ 서비스 계약 □ 타입 캐스트 □ 에러 전파 |
| 69 | `modules/core/adaptive_retry.py` | 860 | □ 재시도 상태 리셋 □ 백오프 계산 □ 최대 시도 |
| 70 | `modules/core/feedback_system.py` | 853 | □ 피드백 루프 □ 점수 집계 □ 이력 관리 |
| 71 | `modules/core/quality_dashboard.py` | 1100 | □ 대시보드 집계 □ 0 나누기 □ 빈 데이터 |
| 72 | `modules/core/pattern_tracker.py` | 936 | □ 패턴 추적 카운터 □ 임계값 비교 □ 캐시 |

### Phase 7 — 장르 가드 (Round 73~79)

| Round | 파일 | 줄수 | 집중 체크리스트 |
|-------|------|------|----------------|
| 73 | `modules/core/genre_guards/base_guard.py` | 807 | □ Guard 다형성 □ 정규식 이스케이프 □ deep validation 반환 |
| 74 | `modules/core/genre_guards/wuxia_guard.py` | 661 | □ 무협 금기어 □ 정규식 패턴 □ 오버라이드 |
| 75 | `modules/core/genre_guards/hunter_guard.py` | 863 | □ 헌터 금기어 □ 정규식 패턴 □ 오버라이드 |
| 76 | `modules/core/genre_guards/investment_guard.py` (636) + `fantasy_guard.py` (333) | 969 | □ 투자/판타지 금기어 □ 장르 특화 검증 |
| 77 | `modules/core/genre_guards/cooking_guard.py` (500) + `composer_guard.py` (517) | 1017 | □ 요리/작곡 금기어 □ 특화 검증 |
| 78 | `modules/core/genre_guards/alt_history_guard.py` (491) + `medical_guard.py` (468) + `sports_guard.py` (461) + `actor_guard.py` (457) | 1877 | □ 4개 확장 가드 □ YAML 키 □ 정규식 |
| 79 | `modules/core/genre_guards/work_guard.py` (197) + `style_guard.py` (167) + `__init__.py` (70) | 434 | □ Guard 체인 순서 □ YAML 키 불일치 □ 래퍼 로직 |

### Phase 8 — main_a.py (Round 80~83)

`main_a.py`는 2,997줄 진입점이다. 4개 라운드로 나눠 읽어라.

| Round | 범위 | 줄수 | 집중 체크리스트 |
|-------|------|------|----------------|
| 80 | `main_a.py` L1~750 | 750 | □ `__init__` 초기화 순서 □ Stage 0 진입 □ DI 바인딩 |
| 81 | `main_a.py` L751~1500 | 750 | □ Stage 2 진입 □ 콜백 등록 □ 에러 복구 |
| 82 | `main_a.py` L1501~2250 | 750 | □ Stage 3/4 진입 □ 상태 동기화 □ write-back |
| 83 | `main_a.py` L2251~끝 | 747 | □ 유틸 메서드 □ 출력 포맷팅 □ 설정 관리 |

### Phase 9 — Stage 0 + 초기화 (Round 84~87)

| Round | 파일 | 줄수 | 집중 체크리스트 |
|-------|------|------|----------------|
| 84 | `modules/core/stage0/__init__.py` | 535 | □ Stage 0 진입 □ 사용자 입력 처리 □ 파일 I/O |
| 85 | `modules/core/stage0/reverse_expander.py` | 1061 | □ 역방향 확장 □ LLM 파싱 □ 블록 처리 |
| 86 | `modules/core/stage0/style_extractor.py` (723) + `story_expander.py` (486) | 1209 | □ 스타일 분석 □ 스토리 확장 □ 파싱 |
| 87 | `modules/core/stage0/spinner.py` (664) + `preset_registry.py` (650) + `stage01_helpers.py` (650) | 1964 | □ 스피너 UI □ 프리셋 □ Stage 0→1 전환 |

### Phase 10 — 중형 나머지 모듈 A (Round 88~93)

| Round | 파일 | 줄수 | 집중 체크리스트 |
|-------|------|------|----------------|
| 88 | `modules/core/semantic_item_registry.py` (778) + `modules/core/genre_hud_manager.py` (751) | 1529 | □ 아이템 레지스트리 □ HUD 갱신 □ 캐시 정합 |
| 89 | `modules/core/tree_of_thoughts.py` (724) + `modules/core/agent_intelligence.py` (600) | 1324 | □ ToT 분기 □ 지능 조절 □ 결과 선택 |
| 90 | `modules/core/pre_director_checklist.py` (592) + `modules/core/constitutional_checker.py` (578) | 1170 | □ 체크리스트 누락 □ 헌법 검사 □ 위반 처리 |
| 91 | `modules/core/constraint_db.py` (581) + `modules/core/martial_manager.py` (564) | 1145 | □ 제약 DB 쿼리 □ 전투 시스템 □ 파워 계산 |
| 92 | `modules/core/relationship_tracker_factions.py` (852) + `modules/core/relationship_tracker_npc.py` (406) + `modules/core/relationship_tracker.py` (130) | 1388 | □ 관계 dict 갱신 □ 팩션 추적 □ NPC 관계 |
| 93 | `modules/core/power_scaling.py` (502) + `modules/core/vec_memory.py` (506) | 1008 | □ 파워 스케일링 □ 벡터 메모리 □ 유사도 계산 |

### Phase 11 — 중형 나머지 모듈 B (Round 94~97)

| Round | 파일 | 줄수 | 집중 체크리스트 |
|-------|------|------|----------------|
| 94 | `modules/core/narrative_diversity.py` (529) + `modules/core/diversity_sampler.py` (510) | 1039 | □ 다양성 샘플링 □ 점수 계산 □ 빈 풀 |
| 95 | `modules/core/character_voice.py` (459) + `modules/core/character_voice_profiler.py` (448) | 907 | □ 캐릭터 음성 □ 프로파일링 □ 일관성 |
| 96 | `modules/core/pacing_analyzer.py` (439) + `modules/core/foreshadow_tracker.py` (476) + `modules/core/emotion_tracker.py` (370) | 1285 | □ 페이싱 분석 □ 복선 관리 □ 감정 추적 |
| 97 | `modules/core/information_diffusion.py` (441) + `modules/core/lore_manager.py` (444) + `modules/core/semantic_cache.py` (420) | 1305 | □ 정보 확산 □ 로어 관리 □ 의미 캐시 |

### Phase 12 — 소형 모듈 (Round 98~100)

| Round | 파일 | 줄수 | 집중 체크리스트 |
|-------|------|------|----------------|
| 98 | `modules/core/ab_testing.py` (464) + `modules/core/confidence_calibration.py` (455) + `modules/core/data_collector.py` (457) + `modules/domain/agents/negative_example_injector.py` (274) + `modules/core/semantic_plot_guard.py` (305) | 1955 | □ A/B 테스트 □ 신뢰 보정 □ 데이터 수집 □ 네거티브 주입 □ 플롯 가드 |
| 99 | `modules/core/pre_director_manuscript_checker.py` (476) + `modules/core/pre_director_narrative_checker.py` (370) + `modules/core/pre_director_style_checker.py` (222) + `modules/core/error_helper.py` (351) + `modules/core/reference_anchor.py` (350) | 1769 | □ 사전 검사 3종 □ 에러 헬퍼 □ 앵커 참조 |
| 100 | `modules/core/self_reflection.py` (326) + `modules/core/reflexion_manager.py` (225) + `modules/core/repetition_guard.py` (222) + `modules/core/primitive_guard.py` (285) + `modules/core/escape_utils.py` (167) + `modules/core/hud_utils.py` (265) + `modules/core/arc_summary_utils.py` (82) + `modules/core/logger.py` (287) + `modules/core/spinners.py` (270) + `modules/core/config_manager.py` (168) + `modules/core/perf_timer.py` (69) + 나머지 소형 파일 | ~3000+ | □ 유틸 전수 □ 가드 로직 □ 설정 관리 □ 나머지 미커버 파일 전부 |

---

## 7. 미커버 파일 확인

Round 100에서 위 라운드에 명시적으로 배정되지 않은 모든 `modules/` 하위 `.py` 파일을 찾아 읽어라. 다음 파일들이 포함될 수 있다:

```
modules/core/constants.py (762)
modules/core/response_schemas.py (593)
modules/core/metrics_collector.py (484)
modules/core/finetuning_automation.py (425)
modules/core/quality_amplifier.py (420)
modules/core/multi_agent_deliberation.py (420)
modules/core/progress_manager.py (359)
modules/core/chain_of_verification.py (359)
modules/core/narrative_structure_analyzer.py (305)
modules/core/dynamic_prompt_weighting.py (302)
modules/core/quality_constitution.py (290)
modules/core/justification_patterns.py (318)
modules/core/material_db.py (123)
modules/core/adversarial_self_play.py (391)
modules/core/expert_mixture.py (388)
modules/core/context_compression.py (379)
modules/core/failure_learning.py (367)
modules/core/system.py (83)
modules/core/studio_visualizer.py (89)
modules/core/slack_bot.py (68)
modules/core/karma_service.py (24)
modules/core/jianghu_logic.py (25)
modules/core/technique_weaver.py (42)
modules/models/*.py (arc, blueprint, manuscript, npc, domain models)
modules/protocols/*.py (agents, app_services, db_repository, validators)
modules/domain/agents/manager.py (175)
modules/domain/agents/weaver.py (146)
modules/domain/strategies/*.py (각 장르별 전략)
```

이 파일들도 5-A, 5-B를 작성하되 소형 파일(100줄 미만)은 5-B 1개로 축약 가능.

---

## 8. `codex_findings_v2.md` 전체 구조

```markdown
# Codex Debug Sweep v2 Findings

## 통계
- 총 발견: N건 (CRITICAL: X, HIGH: Y, MEDIUM: Z)
- 라운드 진행: M/100

---

## Round 1 — stage4_orchestrator.py

### 5-A. 파일 구조 요약
(...)

### 5-B. 위험 지점 분석
(...)

### 5-C. 발견된 버그
(있을 때만)

---
## Round 1 완료

(반복...)

---

## 미확인 (LOW confidence)
(확신도 LOW 항목 모음)

---

## 자체 검증 결과
- [ ] 5-A 빈 라운드: 0개
- [ ] 5-D 빈 라운드: 0개
- [ ] 5-B 빈 라운드: 0개
- [ ] FP 체크 누락: 0개
- [ ] 라인 번호 누락: 0개
- [ ] 호출자 미기재: 0개
- [ ] 총 위험 지점: ≥ 300개 (100 라운드 × 최소 3개)
```

---

## 9. 품질 검증 규칙

완료 후 자체 검증:

1. **5-A 빈 라운드 = 0개여야 한다.** 모든 라운드에 파일 구조 요약이 있어야 한다.
2. **5-D 빈 라운드 = 0개여야 한다.** 모든 라운드에 읽기 증명이 있어야 한다.
3. **5-B 빈 라운드 = 0개여야 한다.** 모든 라운드에 위험 지점 분석이 있어야 한다.
4. **FP 체크 누락 = 0개여야 한다.** 모든 버그 보고에 FP-1~10 교차 확인이 있어야 한다.
5. **라인 번호 없는 보고 = 0개여야 한다.** 모든 코드 인용에 라인 번호가 있어야 한다.
6. **호출자 미기재 = 0개여야 한다.** 모든 5-B 위험 지점에 호출자 정보가 있어야 한다.
7. **총 위험 지점 수 ≥ 300개.** (100 라운드 × 최소 3개)

마지막에 이 7개 항목의 충족 여부를 `## 자체 검증 결과` 섹션에 기록하라.

---

## 10. ⛔⛔⛔ 절대 금지 사항 ⛔⛔⛔

### 스크립트/자동화 금지
- **Python 스크립트, 셸 스크립트, grep/regex 자동화로 findings를 생성하지 마라.**
- `re.match(r'class|def')` 같은 패턴으로 5-A를 채우는 것은 **위조**다.
- `risk_patterns = [re.compile(...)]` 같은 자동 패턴 매칭으로 5-B를 채우는 것도 **위조**다.
- 이전 실행 결과를 `confirmed = { 9: [...] }` 같이 하드코딩해서 5-C에 넣는 것도 **위조**다.
- **발각 시 전체 결과가 폐기된다.** 처음부터 다시 해야 한다.

### 올바른 작업 방법
1. **각 파일을 직접 열어서 읽어라** (에디터/뷰어로, 스크립트 생성이 아님).
2. 코드를 읽으며 **함수의 목적, 입력, 출력, 에러 경로**를 이해하라.
3. 이해한 내용을 바탕으로 5-A, 5-B를 **자연어로 직접 작성**하라.
4. 5-B의 라인 번호와 코드 스니펫은 **실제 파일에서 복사**한 것이어야 한다.

### 위조 탐지 방법 (검토자가 확인할 항목)
검토자는 **매 라운드마다** 아래를 샘플 검증한다:

**5-D 대조 (가장 빠른 위조 탐지)**:
- `마지막 함수` 이름+라인을 실제 파일에서 grep → 불일치 시 즉시 위조 판정
- `특징적 문자열`을 실제 파일에서 grep → 불일치 시 즉시 위조 판정
- `import 목록`이 실제 import와 일치하는가?

**5-A 대조**:
- 함수 시그니처(파라미터명, 기본값)가 실제 코드와 일치하는가?
- 라인 번호가 ±5줄 이내로 정확한가?

**5-B 대조**:
- 인용된 코드가 실제 해당 라인에 존재하는가?
- 호출자 정보가 실제 코드의 호출 관계와 일치하는가?
- 가드 코드 인용이 실제로 존재하는가?

**패턴 기반 탐지**:
- 모든 라운드의 문체가 기계적으로 동일하지 않은가?
- 5-D의 로그 메시지가 실제로는 다른 파일의 것이 아닌가?
- 모든 라운드에서 위험 지점이 정확히 3개뿐이면 의심 (기계적 최소 충족)

### 기타
1. **수정(edit)은 절대 하지 마라.** `codex_findings_v2.md` 기록만 한다.
2. **오탐 방지 10개(FP-1~10)를 매 라운드 참조하라.**
3. **Round 98~100은 파일이 많다.** 500줄 이상 파일 우선, 100줄 미만은 5-A 축약 가능.
4. **1번부터 100번까지 순서대로 진행한다.** 라운드를 건너뛰지 마라.
5. **중단되면 이어서 계속한다.** 결과 파일에 마지막 완료 라운드가 기록되어 있으므로 그 다음부터 이어라.

---

## 11. 이전 스윕에서 이미 수정된 패턴 (참고용)

아래는 이미 발견·수정된 패턴이다. **동일 파일·동일 라인**을 다시 보고할 필요 없지만, **다른 파일에서 같은 패턴**이 존재하면 보고하라.

| 커밋 | 수정 내용 |
|------|-----------|
| `92bd92c` | `stage2_finalizer.py` safe_commit_async 반환값 체크, `state_service.py` ep_end int 캐스트 |
| `02e3450` | `analyst.py`, `arc_critic.py`, `arc_draft_validator.py`, `stage2_optimizer.py`, `unified_arc_validator.py`의 set+dict 크래시, `chief_writer_quality.py` re.escape, `stage2_validation_pipeline.py` ep_count int 캐스트 |
| `d82f27e` | `stage2_finalizer.py` summary 동기화, `stage4_interview_round.py` arc 하드코딩, `db_manager.py` JSON 보존, `adaptive_retry.py` 적응 임계값, `validation_orchestrator.py` KeyError |
| `f7cd761` | 스레드 안전성, 롤백 리플레이, JSON 보존, 적응 임계값 |
