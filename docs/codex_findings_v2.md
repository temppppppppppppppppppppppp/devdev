# Codex Debug Sweep v2 Findings

## 통계
- 총 발견: 97건 (CRITICAL: 0, HIGH: 68, MEDIUM: 29)
- 라운드 진행: 100/100

---
## Round 1 — modules/core/stage4_orchestrator.py

### 진행 통계 업데이트
- 총 발견: 0건 (CRITICAL: 0, HIGH: 0, MEDIUM: 0)
- 라운드 진행: 1/100

### 5-A. 파일 구조 요약
- `modules/core/stage4_orchestrator.py:214` `class Stage4Orchestrator` — Stage4 집필 루프 오케스트레이션.
- `modules/core/stage4_orchestrator.py:329` `_run_interview_loop(self, session: _SessionConfig) -> bool` — 에피소드 메인 루프.
- `modules/core/stage4_orchestrator.py:567` `_handle_round_outcome(self, *, round_ctx: _RoundContext) -> _RoundOutcome` — PASS/REJECT 분기.
- `modules/core/stage4_orchestrator.py:616` `_prepare_stage4_session(self, *, limit_mode: bool = False) -> dict | None` — 세션 준비.
- `modules/core/stage4_orchestrator.py:787` `stage_4_v2_chief_writer(self, limit_mode: bool = False) -> None` — Stage4 진입점.

### 5-D. 읽기 증명
1. 마지막 함수: `def stage_4_v2_chief_writer(self, limit_mode: bool = False) -> None` (`modules/core/stage4_orchestrator.py:787`)
2. 특징 문자열: `self.ctx.ui.log("🛑 [Safety] 루프 제한 도달. 중단합니다.")` (`modules/core/stage4_orchestrator.py:363`)
3. import 목록:
- `from modules.core.stage4_context_builder import Stage4ContextBuilder` (`modules/core/stage4_orchestrator.py:14`)
- `from modules.core.stage4_interview_round import Stage4InterviewRound` (`modules/core/stage4_orchestrator.py:15`)
- `from modules.core.stage4_post_processor import Stage4PostProcessor` (`modules/core/stage4_orchestrator.py:16`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `1, min((target_ep or total_planned_ep) - self.ctx.current_project.get_latest_episode_number() + 5, 100)` (`modules/core/stage4_orchestrator.py:351`)
- 호출자: `stage_4_v2_chief_writer()` → `_run_interview_loop()` (`modules/core/stage4_orchestrator.py:801`, `modules/core/stage4_orchestrator.py:805`)
- 상류/하류 컨텍스트:
- 상류: `target_ep = self.ctx.get_int_input(...)` (`modules/core/stage4_orchestrator.py:700`)
- 하류: `if loop_guard > max_loops:` (`modules/core/stage4_orchestrator.py:362`)
- 실패 시나리오: `target_ep`/`total_planned_ep`에 비정수 값이 유입되면 산술 TypeError.
- 판정: 안전(상류 입력 정수화 계약 의존).

2. 위험 지점
- 코드 원문: `if isinstance(a, dict) and a.get("ep_start", 0) <= next_ep <= a.get("ep_end", 0)` (`modules/core/stage4_orchestrator.py:383`)
- 호출자: `_run_interview_loop()` 내부 Arc 선택 루프 (`modules/core/stage4_orchestrator.py:379`)
- 상류/하류 컨텍스트:
- 상류: `arc_data = next((a for a in self.ctx.current_project.arcs ...), None)` (`modules/core/stage4_orchestrator.py:379`)
- 하류: `_ep_ctx = self.context_builder.prepare_episode_context(next_ep, arc_data, chief_writer)` (`modules/core/stage4_orchestrator.py:392`)
- 실패 시나리오: `ep_start`/`ep_end`가 문자열이면 비교 TypeError.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `reference_anchor_prompt = _ctx_prompts["reference_anchor_prompt"]` (`modules/core/stage4_orchestrator.py:432`)
- 호출자: `_run_interview_loop()` mandatory context 구성 직후 (`modules/core/stage4_orchestrator.py:419`)
- 상류/하류 컨텍스트:
- 상류: `_ctx_prompts = self.context_builder.build_mandatory_context(...)` (`modules/core/stage4_orchestrator.py:419`)
- 하류: `_round_ctx = self.context_builder.build_round_context(..., ctx_prompts=_ctx_prompts, ...)` (`modules/core/stage4_orchestrator.py:507`)
- 실패 시나리오: builder 반환 dict 키 누락 시 KeyError.
- 판정: 안전(builder에서 고정 키 반환 계약).

### 5-C. 발견된 버그
- 없음

---
## Round 1 완료

## Round 2 — modules/core/stage4_interview_round.py

### 진행 통계 업데이트
- 총 발견: 0건 (CRITICAL: 0, HIGH: 0, MEDIUM: 0)
- 라운드 진행: 2/100

### 5-A. 파일 구조 요약
- `modules/core/stage4_interview_round.py:8` `class Stage4InterviewRound` — 단일 면담 라운드 실행.
- `modules/core/stage4_interview_round.py:15` `run(...)` — 후보 생성/검증/감독 판정 처리.
- `modules/core/stage4_interview_round.py:103` `_prev_score` 계산 및 patch 모드 분기.
- `modules/core/stage4_interview_round.py:253` `manuscript_validator.validate_all_candidates(...)` 호출.
- `modules/core/stage4_interview_round.py:626` `_record_s4_attempt(...)` — PassRateMonitor 기록.

### 5-D. 읽기 증명
1. 마지막 함수: `def _record_s4_attempt(` (`modules/core/stage4_interview_round.py:626`)
2. 특징 문자열: `logging.warning(f"[D-4] Director 선택 기록 실패 (비차단): {e!s:.100}")` (`modules/core/stage4_interview_round.py:550`)
3. import 목록:
- `from modules.core.stage4_orchestrator import _PATCH_REWRITE_THRESHOLD, _InterviewRoundResult` (`modules/core/stage4_interview_round.py:25`)
- 프로젝트 모듈 import는 파일 구조상 위 1개(단일 의존).
- 추가 프로젝트 import 없음(파일 전수 확인).

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `_prev_score = int(previous_attempt.get("score", 0)) if previous_attempt else 0` (`modules/core/stage4_interview_round.py:103`)
- 호출자: `run()` 내부 round>0 분기 (`modules/core/stage4_interview_round.py:101`)
- 상류/하류 컨텍스트:
- 상류: `previous_attempt`는 orchestrator에서 전달 (`modules/core/stage4_orchestrator.py:520`)
- 하류: `_use_patch = _prev_score >= _PATCH_REWRITE_THRESHOLD and _prev_manuscript` (`modules/core/stage4_interview_round.py:107`)
- 실패 시나리오: 점수가 비수치 문자열이면 ValueError.
- 판정: 안전(바로 아래 예외 처리로 0 보정, `modules/core/stage4_interview_round.py:104`).

2. 위험 지점
- 코드 원문: `final_manuscript = selected_candidate.get("manuscript", "")` (`modules/core/stage4_interview_round.py:549`)
- 호출자: `if verdict == "PASS":` 블록 (`modules/core/stage4_interview_round.py:547`)
- 상류/하류 컨텍스트:
- 상류: `selected_candidate = director_result.get("selected_candidate", {})` (`modules/core/stage4_interview_round.py:548`)
- 하류: `_time_warnings = self.ctx.state_tracker.check_time_consistency(final_manuscript, ...)` (`modules/core/stage4_interview_round.py:556`)
- 실패 시나리오: `selected_candidate`가 dict가 아니면 `.get` 크래시.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `"best_manuscript": director_result.get("selected_candidate", {}).get("manuscript", ""),` (`modules/core/stage4_interview_round.py:599`)
- 호출자: REJECT 분기 `previous_attempt` 구성 (`modules/core/stage4_interview_round.py:593`)
- 상류/하류 컨텍스트:
- 상류: `feedback = director_result.get("feedback") or {}` (`modules/core/stage4_interview_round.py:586`)
- 하류: 다음 라운드에서 `_prev_manuscript`로 사용 (`modules/core/stage4_interview_round.py:106`)
- 실패 시나리오: `selected_candidate`가 dict가 아니면 체인 `.get`에서 AttributeError.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 2 완료

## Round 3 — modules/core/stage4_context_builder.py

### 진행 통계 업데이트
- 총 발견: 0건 (CRITICAL: 0, HIGH: 0, MEDIUM: 0)
- 라운드 진행: 3/100

### 5-A. 파일 구조 요약
- `modules/core/stage4_context_builder.py:20` `class Stage4ContextBuilder` — Stage4 컨텍스트 조립 전담.
- `modules/core/stage4_context_builder.py:63` `build_extended_lookback_digest(self, next_ep: int) -> str`.
- `modules/core/stage4_context_builder.py:112` `prepare_episode_context(self, next_ep: int, arc_data: dict, chief_writer) -> dict`.
- `modules/core/stage4_context_builder.py:206` `build_mandatory_context(...)`.
- `modules/core/stage4_context_builder.py:526` `build_round_context(...)`.

### 5-D. 읽기 증명
1. 마지막 함수: `def build_round_context(` (`modules/core/stage4_context_builder.py:526`)
2. 특징 문자열: `logging.warning(f"[SilentPass:ContextBuilder] SemanticPlotGuard 경고 주입 실패: {e!s:.100}")` (`modules/core/stage4_context_builder.py:479`)
3. import 목록:
- `from modules.core.writer_prompt_builders import build_anti_trope_instructions as _build_anti_trope` (`modules/core/stage4_context_builder.py:9`)
- `from modules.core.writer_prompt_builders import build_justification_guidance as _build_justification` (`modules/core/stage4_context_builder.py:12`)
- `from modules.core.writer_prompt_builders import build_mandatory_context as _build_writer_mandatory_context` (`modules/core/stage4_context_builder.py:15`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `arc_pos = next_ep - arc_data.get("ep_start", next_ep) + 1` (`modules/core/stage4_context_builder.py:114`)
- 호출자: orchestrator의 episode context 준비 (`modules/core/stage4_orchestrator.py:392`)
- 상류/하류 컨텍스트:
- 상류: Arc 선택 시 범위 비교 사용 (`modules/core/stage4_orchestrator.py:383`)
- 하류: `arc_pos=ep_ctx["arc_pos"]`로 라운드 컨텍스트 전달 (`modules/core/stage4_context_builder.py:559`)
- 실패 시나리오: `ep_start`가 문자열/None이면 산술 TypeError.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `mandatory_context = "\n\n".join(_mc_parts)` (`modules/core/stage4_context_builder.py:497`)
- 호출자: `build_mandatory_context()` 내부 (`modules/core/stage4_context_builder.py:206`)
- 상류/하류 컨텍스트:
- 상류: `_mc_parts.append(_narrative_summaries)` (`modules/core/stage4_context_builder.py:491`)
- 하류: 반환 dict의 `mandatory_context`로 사용 (`modules/core/stage4_context_builder.py:520`)
- 실패 시나리오: `_mc_parts`에 비문자열 원소 혼입 시 join TypeError.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `reference_anchor_prompt=ctx_prompts["reference_anchor_prompt"],` (`modules/core/stage4_context_builder.py:579`)
- 호출자: orchestrator에서 `build_round_context(..., ctx_prompts=_ctx_prompts, ...)` (`modules/core/stage4_orchestrator.py:507`)
- 상류/하류 컨텍스트:
- 상류: `ctx_prompts`는 `build_mandatory_context` 반환값 (`modules/core/stage4_orchestrator.py:419`)
- 하류: round 실행 시 chief writer 입력으로 사용 (`modules/core/stage4_interview_round.py:54`)
- 실패 시나리오: dict key 누락 시 KeyError.
- 판정: 안전(초기 키 기본값 구성 후 반환, `modules/core/stage4_context_builder.py:220`~`modules/core/stage4_context_builder.py:234`).

### 5-C. 발견된 버그
- 없음

---
## Round 3 완료

## Round 4 — modules/core/stage4_post_processor.py

### 진행 통계 업데이트
- 총 발견: 1건 (CRITICAL: 0, HIGH: 1, MEDIUM: 0)
- 라운드 진행: 4/100

### 5-A. 파일 구조 요약
- `modules/core/stage4_post_processor.py:14` `class Stage4PostProcessor` — PASS 후처리 전담.
- `modules/core/stage4_post_processor.py:20` `process_pass_result(...) -> bool` — 저장/상태 반영/부가 처리.
- `modules/core/stage4_post_processor.py:210` state audit 기반 delta 계산.
- `modules/core/stage4_post_processor.py:478` 크로스-에피소드 반복 감지 블록.
- `modules/core/stage4_post_processor.py:557` `run_post_episode_tasks(self) -> None`.

### 5-D. 읽기 증명
1. 마지막 함수: `def run_post_episode_tasks(self) -> None:` (`modules/core/stage4_post_processor.py:557`)
2. 특징 문자열: `logging.warning("[Phase 3-B] 크로스 에피소드 반복 감지 실패 (비차단): %s", _cr_err)` (`modules/core/stage4_post_processor.py:515`)
3. import 목록:
- `from modules.core.metrics_collector import get_metrics_collector` (`modules/core/stage4_post_processor.py:9`)
- `from modules.validation.threshold_helper import _threshold` (`modules/core/stage4_post_processor.py:440`)
- `from modules.core.repetition_guard import RepetitionGuard` (`modules/core/stage4_post_processor.py:484`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `self.ctx.current_project.db.save_manuscript(ep_num=next_ep, title=final_title, content=final_manuscript)` (`modules/core/stage4_post_processor.py:40`)
- 호출자: orchestrator PASS 처리 (`modules/core/stage4_orchestrator.py:545`)
- 상류/하류 컨텍스트:
- 상류: `if final_manuscript:` 분기 후 호출 (`modules/core/stage4_orchestrator.py:544`)
- 하류: 동일 try 블록 내 `self.ctx.current_project.db.conn.commit()` (`modules/core/stage4_post_processor.py:46`)
- 실패 시나리오: save 성공 후 중간 단계(예: `update_martial_tracker`)에서 예외 발생 시 rollback 없이 반환되어 원자성 붕괴.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `prev_equipment = set(prev_actual.get("equipment", []) if isinstance(prev_actual.get("equipment"), list) else [])` (`modules/core/stage4_post_processor.py:220`)
- 호출자: state audit 병합 구간 (`modules/core/stage4_post_processor.py:210`)
- 상류/하류 컨텍스트:
- 상류: `prev_actual = self.ctx.current_project.latest_state.get("actual_truth", {})` (`modules/core/stage4_post_processor.py:218`)
- 하류: `new_items_from_equip = list(curr_equipment - prev_equipment)` (`modules/core/stage4_post_processor.py:233`)
- 실패 시나리오: list 내부 dict 혼입 시 `set(...)`에서 `unhashable type: 'dict'`.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `all_new_items = list(set(new_items_from_equip + key_item_names + new_martial_arts))` (`modules/core/stage4_post_processor.py:276`)
- 호출자: Bible delta 조립 구간 (`modules/core/stage4_post_processor.py:278`)
- 상류/하류 컨텍스트:
- 상류: `new_items_from_equip`/`key_item_names`/`new_martial_arts`가 외부 추출 결과 병합 (`modules/core/stage4_post_processor.py:233`, `modules/core/stage4_post_processor.py:262`, `modules/core/stage4_post_processor.py:235`)
- 하류: `bible_delta = {"new_items": all_new_items, ...}` (`modules/core/stage4_post_processor.py:279`)
- 실패 시나리오: 병합 리스트에 dict 혼입 시 set 변환 크래시.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/core/stage4_post_processor.py:40 — DB 부분 저장 후 롤백 누락

**문제**: `save_manuscript()`는 성공했지만 같은 try 안에서 후속 처리 중 예외가 나면 rollback 없이 `False` 반환되어, 호출자는 실패로 인지하지만 트랜잭션은 부분 상태가 남을 수 있음.

**문제 코드**:
```python
self.ctx.current_project.db.save_manuscript(ep_num=next_ep, title=final_title, content=final_manuscript)

if final_state_updates:
    self.ctx.current_project.db.update_martial_tracker(next_ep, final_state_updates)
    self.ctx.ui.log(f"      🧤 제{next_ep}화 15대 지표 트래커 업데이트 완료")

self.ctx.current_project.db.conn.commit()
```

**호출 체인**: `stage_4_v2_chief_writer()` → `_run_interview_loop()` → `process_pass_result()` (`modules/core/stage4_orchestrator.py:801`, `modules/core/stage4_orchestrator.py:329`, `modules/core/stage4_orchestrator.py:545`)

**수정 제안**:
```python
try:
    self.ctx.current_project.db.save_manuscript(...)
    if final_state_updates:
        self.ctx.current_project.db.update_martial_tracker(...)
    self.ctx.current_project.db.conn.commit()
except Exception as db_err:
    self.ctx.current_project.db.conn.rollback()
    self.ctx.ui.log(f"   ❌ DB 저장 실패: {db_err}")
    return False
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 4 완료

## Round 5 — modules/core/stage4_context.py + modules/core/pass_rate_monitor.py

### 진행 통계 업데이트
- 총 발견: 1건 (CRITICAL: 0, HIGH: 1, MEDIUM: 0)
- 라운드 진행: 5/100

### 5-A. 파일 구조 요약
- `modules/core/stage4_context.py:4` `class Stage4Context` — Stage4 DI 컨텍스트.
- `modules/core/stage4_context.py:106` `from_app(cls, app)` — app 속성/콜백 바인딩.
- `modules/core/pass_rate_monitor.py:66` `class PassRateMonitor` — 시도/합격률 기록기.
- `modules/core/pass_rate_monitor.py:176` `get_stage_stats(self, stage: int, recent_n: int = None) -> StageStats`.
- `modules/core/pass_rate_monitor.py:283` `get_patch_effectiveness(...) -> dict[str, Any]`.
- `modules/core/pass_rate_monitor.py:546` `reset_monitor() -> None`.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def from_app(cls, app):` (`modules/core/stage4_context.py:106`)
- `def reset_monitor() -> None:` (`modules/core/pass_rate_monitor.py:546`)
2. 특징 문자열:
- `flush_audit_buffer=getattr(app, "_flush_audit_buffer", None),` (`modules/core/stage4_context.py:132`)
- `monitor.record_attempt(stage=4, success=True, attempt_num=1)` (`modules/core/pass_rate_monitor.py:17`)
3. import 목록:
- Stage4Context 파일: 프로젝트 모듈 import 없음(파일 전수 확인).
- PassRateMonitor 파일: 프로젝트 모듈 import 없음(파일 전수 확인).
- 외부 의존은 stdlib/dataclass만 사용.

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `get_int_input=getattr(app, "_get_int_input", None),` (`modules/core/stage4_context.py:127`)
- 호출자: `Stage4Context.from_app()` 결과를 orchestrator가 사용 (`modules/core/stage4_orchestrator.py:237`)
- 상류/하류 컨텍스트:
- 상류: `ctx = Stage4Context.from_app(app)` (`modules/core/stage4_orchestrator.py:237`)
- 하류: `target_ep = self.ctx.get_int_input(...)` (`modules/core/stage4_orchestrator.py:700`)
- 실패 시나리오: 콜백이 None 바인딩되면 호출 시 TypeError.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `first_attempt_rate = first_attempt_pass / total_episodes if total_episodes > 0 else 0` (`modules/core/pass_rate_monitor.py:244`)
- 호출자: `get_stage_stats()` (`modules/core/pass_rate_monitor.py:176`)
- 상류/하류 컨텍스트:
- 상류: `total_episodes = len(episodes)` (`modules/core/pass_rate_monitor.py:243`)
- 하류: `return StageStats(... first_attempt_rate=first_attempt_rate, ...)` (`modules/core/pass_rate_monitor.py:258`)
- 실패 시나리오: total_episodes=0 시 0나누기.
- 판정: 안전(조건식 가드 존재).

3. 위험 지점
- 코드 원문: `sum(float(getattr(r, "prev_score", 0) or 0) for r in patch_records) / patch_attempts` (`modules/core/pass_rate_monitor.py:300`)
- 호출자: `get_patch_effectiveness()` (`modules/core/pass_rate_monitor.py:283`)
- 상류/하류 컨텍스트:
- 상류: `patch_records = [r for r in records if getattr(r, "is_patch", False)]` (`modules/core/pass_rate_monitor.py:291`)
- 하류: 반환 dict의 `avg_prev_score` (`modules/core/pass_rate_monitor.py:305`)
- 실패 시나리오: `prev_score`가 숫자형 변환 불가 문자열이면 ValueError.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 5 완료

## Round 6 — modules/domain/agents/chief_writer.py

### 진행 통계 업데이트
- 총 발견: 2건 (CRITICAL: 0, HIGH: 2, MEDIUM: 0)
- 라운드 진행: 6/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/chief_writer.py:34` `class ChiefWriter(BaseAgent)` — Stage4 원고 생성 핵심 에이전트.
- `modules/domain/agents/chief_writer.py:114` `generate_ensemble(...) -> list[dict]` — 3전략 병렬 생성.
- `modules/domain/agents/chief_writer.py:361` `_generate_single_candidate(...)` — 단일 후보 생성/정규화.
- `modules/domain/agents/chief_writer.py:512` `regenerate_with_feedback(...)` — REJECT 피드백 기반 재생성.
- `modules/domain/agents/chief_writer.py:630` `patch_with_feedback(...)` — patch 모드 재생성.

### 5-D. 읽기 증명
1. 마지막 함수: `def _build_justification_guidance(self, *args, **kwargs):` (`modules/domain/agents/chief_writer.py:867`)
2. 특징 문자열: `logging.error("[ChiefWriter] generate_ensemble: 앙상블 + 단일 폴백 모두 실패 — 에러 후보 반환")` (`modules/domain/agents/chief_writer.py:343`)
3. import 목록:
- `from modules.models.manuscript import validate_manuscript_candidate` (`modules/domain/agents/chief_writer.py:24`)
- `from .chief_writer_context import ChiefWriterContextBuilder` (`modules/domain/agents/chief_writer.py:27`)
- `from .chief_writer_quality import ChiefWriterQualityGate` (`modules/domain/agents/chief_writer.py:31`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `final_content = critiqued_data.get("content") or manuscript_content` (`modules/domain/agents/chief_writer.py:461`)
- 호출자: `_generate_single_candidate()` self-critique 후처리 (`modules/domain/agents/chief_writer.py:454`)
- 상류/하류 컨텍스트:
- 상류: 1차 content 정규화는 `manuscript_content`에만 적용 (`modules/domain/agents/chief_writer.py:432`~`modules/domain/agents/chief_writer.py:444`)
- 하류: 반환 candidate의 `"manuscript": final_content` (`modules/domain/agents/chief_writer.py:472`), 이후 validator 체인 입력 (`modules/core/stage4_interview_round.py:253`)
- 실패 시나리오: self-critique 결과 `content`가 dict/list면 문자열 계약 위반.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `final_state = critiqued_data.get("state_updates", data.get("state_updates", {}))` (`modules/domain/agents/chief_writer.py:463`)
- 호출자: `_generate_single_candidate()` (`modules/domain/agents/chief_writer.py:361`)
- 상류/하류 컨텍스트:
- 상류: `critiqued_data = json.loads(critiqued_manuscript)` (`modules/domain/agents/chief_writer.py:460`)
- 하류: 반환 candidate의 `"state_updates": final_state` (`modules/domain/agents/chief_writer.py:474`)
- 실패 시나리오: `state_updates`가 dict가 아니면 후속 상태 반영 로직 계약 위반.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `valid_candidates = [c for c in candidates if not c.get("error")]` (`modules/domain/agents/chief_writer.py:323`)
- 호출자: `generate_ensemble()` 병렬 결과 정리 (`modules/domain/agents/chief_writer.py:114`)
- 상류/하류 컨텍스트:
- 상류: `result = future.result(...)` 후 `if result: candidates.append(result)` (`modules/domain/agents/chief_writer.py:265`~`modules/domain/agents/chief_writer.py:267`)
- 하류: fallback 분기 및 반환 (`modules/domain/agents/chief_writer.py:324`~`modules/domain/agents/chief_writer.py:350`)
- 실패 시나리오: `result`가 dict가 아닌 truthy 값이면 `c.get`에서 AttributeError.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/domain/agents/chief_writer.py:461 — self-critique content 재정규화 누락

**문제**: 1차 파싱에서 content를 문자열로 정규화했지만, self-critique 결과에서 다시 꺼낸 `content`는 타입 강제가 없어 dict/list가 그대로 downstream으로 전파될 수 있음.

**문제 코드**:
```python
critiqued_data = json.loads(critiqued_manuscript)
final_content = critiqued_data.get("content") or manuscript_content
final_title = critiqued_data.get("title", data.get("title", f"제{ep_num}화"))
final_state = critiqued_data.get("state_updates", data.get("state_updates", {}))
```

**호출 체인**: `generate_ensemble()` → `_generate_single_candidate()` → `validate_all_candidates()` (`modules/domain/agents/chief_writer.py:114`, `modules/domain/agents/chief_writer.py:361`, `modules/core/stage4_interview_round.py:253`)

**수정 제안**:
```python
final_content = critiqued_data.get("content")
if isinstance(final_content, list):
    final_content = "\n".join(str(x) for x in final_content)
elif isinstance(final_content, dict):
    final_content = final_content.get("text") or final_content.get("content") or json.dumps(final_content, ensure_ascii=False)
elif not isinstance(final_content, str):
    final_content = manuscript_content
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 6 완료
## Round 7 — modules/domain/agents/chief_writer_context.py

### 진행 통계 업데이트
- 총 발견: 2건 (CRITICAL: 0, HIGH: 2, MEDIUM: 0)
- 라운드 진행: 7/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/chief_writer_context.py:31` `class ChiefWriterContextBuilder` — ChiefWriter 컨텍스트 조립/분석 헬퍼.
- `modules/domain/agents/chief_writer_context.py:41` `build_common_context(...) -> str` — 원고 생성용 대형 프롬프트 조립.
- `modules/domain/agents/chief_writer_context.py:690` `_check_hud_anomalies(self, current_ep: int) -> dict` — HUD 급변 감지.
- `modules/domain/agents/chief_writer_context.py:931` `_build_mandatory_context(self, current_ep: int) -> str` — 필수 맥락 텍스트 구성.
- `modules/domain/agents/chief_writer_context.py:1031` `_build_justification_guidance(self, hud_report: str, genre_name: str) -> str`.

### 5-D. 읽기 증명
1. 마지막 함수: `def _build_justification_guidance(self, hud_report: str, genre_name: str) -> str:` (`modules/domain/agents/chief_writer_context.py:1031`)
2. 특징 문자열: `logging.warning(f"⚠️ [V64.P4] 플롯 이벤트 추출 실패: {str(e)[:60]}")` (`modules/domain/agents/chief_writer_context.py:986`)
3. import 목록:
- `from modules.core.constants import ContextLimits` (`modules/domain/agents/chief_writer_context.py:9`)
- `from modules.core.hud_utils import build_hud_context as _build_hud_context_shared` (`modules/domain/agents/chief_writer_context.py:10`)
- `from modules.core.hud_utils import get_hud_trend_safe as _get_hud_trend_safe_shared` (`modules/domain/agents/chief_writer_context.py:11`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `if int(ep_num) == 1:` (`modules/domain/agents/chief_writer_context.py:895`)
- 호출자: `build_common_context()` 내부 `dna_instruction = self._get_dna_instruction(ep_num, intro_dna)` (`modules/domain/agents/chief_writer_context.py:263`)
- 상류/하류 컨텍스트:
- 상류: chief writer에서 `build_common_context(ep_num=ep_num, ...)` 호출 (`modules/domain/agents/chief_writer.py:182`)
- 하류: `build_chief_writer_main_prompt(..., dna_instruction=dna_instruction, ...)` (`modules/domain/agents/chief_writer_context.py:298`)
- 실패 시나리오: `ep_num`이 비정수 문자열/None이면 `int(ep_num)`에서 ValueError/TypeError.
- 판정: RISK (Design Check Needed, 호출 계약은 int지만 내부 가드 없음).

2. 위험 지점
- 코드 원문: `for ep in range(max(1, current_ep - 3), current_ep):` (`modules/domain/agents/chief_writer_context.py:700`)
- 호출자: `_check_hud_anomalies(current_ep)` (`modules/domain/agents/chief_writer_context.py:690`), 상위 `build_common_context()`에서 호출 (`modules/domain/agents/chief_writer_context.py:256`)
- 상류/하류 컨텍스트:
- 상류: `hud_anomalies = self._check_hud_anomalies(ep_num)` (`modules/domain/agents/chief_writer_context.py:256`)
- 하류: `if hud_anomalies.get("has_anomalies") ...` (`modules/domain/agents/chief_writer_context.py:257`)
- 실패 시나리오: `current_ep`가 숫자형이 아니면 range 산술 TypeError.
- 판정: RISK (Design Check Needed, 실패 시 except로 빈 결과 반환되어 탐지 누락 가능).

3. 위험 지점
- 코드 원문: `if isinstance(last_appearance, int) and 0 < last_appearance < current_ep:` (`modules/domain/agents/chief_writer_context.py:1011`)
- 호출자: `_build_mandatory_context()`에서 `npc_states = self._extract_npc_last_states(current_ep)` (`modules/domain/agents/chief_writer_context.py:946`)
- 상류/하류 컨텍스트:
- 상류: `last_appearance = npc.get("last_appearance_ep", 0)` (`modules/domain/agents/chief_writer_context.py:1009`)
- 하류: `mandatory_parts.append(f"- {npc_name}: {state_info['relationship']} ...")` (`modules/domain/agents/chief_writer_context.py:951`)
- 실패 시나리오: `last_appearance_ep`가 문자열 숫자(`"12"`)면 상태가 누락되어 연속성 제약 문맥이 약화.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 7 완료
## Round 8 — modules/domain/agents/chief_writer_quality.py

### 진행 통계 업데이트
- 총 발견: 3건 (CRITICAL: 0, HIGH: 3, MEDIUM: 0)
- 라운드 진행: 8/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/chief_writer_quality.py:12` `class ChiefWriterQualityGate` — Self-Critique/품질 게이트.
- `modules/domain/agents/chief_writer_quality.py:20` `sanitize_leakage(self, text: str) -> str` — 출력 누출 필터링.
- `modules/domain/agents/chief_writer_quality.py:67` `apply_self_critique(...) -> str` — 다중 라운드 자가비평.
- `modules/domain/agents/chief_writer_quality.py:354` `_evaluate_with_rubric(self, manuscript: str, genre_name: str) -> float`.
- `modules/domain/agents/chief_writer_quality.py:441` `_count_recent_cliches(self, ep_num: int, manuscript: str, window: int = 10) -> dict`.

### 5-D. 읽기 증명
1. 마지막 함수: `def _count_recent_cliches(self, ep_num: int, manuscript: str, window: int = 10) -> dict:` (`modules/domain/agents/chief_writer_quality.py:441`)
2. 특징 문자열: `logging.info(f"[ChiefWriter] Self-Critique R{round_num}: 완료 ({total_issues_fixed}건 수정)")` (`modules/domain/agents/chief_writer_quality.py:102`)
3. import 목록:
- `from .chief_writer_prompts import get_fix_issues_prompt` (`modules/domain/agents/chief_writer_quality.py:9`)
- 프로젝트 모듈 import는 파일 구조상 위 1개(단일 의존).
- 추가 프로젝트 import 없음(파일 전수 확인).

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `content = data.get("content", "")` (`modules/domain/agents/chief_writer_quality.py:363`)
- 호출자: `apply_self_critique()`의 사전/중간 루브릭 평가 (`modules/domain/agents/chief_writer_quality.py:94`, `modules/domain/agents/chief_writer_quality.py:111`)
- 상류/하류 컨텍스트:
- 상류: `data = json.loads(manuscript)` (`modules/domain/agents/chief_writer_quality.py:362`)
- 하류: `sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", content) ...]` (`modules/domain/agents/chief_writer_quality.py:389`)
- 실패 시나리오: JSON의 `content`가 list/dict면 `re.split`/`.count` 단계에서 TypeError/AttributeError.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `clean_text = re.sub(r"```json\s*|\s*```", "", text).strip()` (`modules/domain/agents/chief_writer_quality.py:31`)
- 호출자: `_generate_single_candidate()`에서 `response = self.quality_gate.sanitize_leakage(response)` (`modules/domain/agents/chief_writer.py:424`)
- 상류/하류 컨텍스트:
- 상류: `response = self.ask(...)` (`modules/domain/agents/chief_writer.py:417`)
- 하류: `data = self._extract_json_robust(response)` (`modules/domain/agents/chief_writer.py:426`)
- 실패 시나리오: `response`가 str이 아닌 truthy 객체면 `re.sub` 단계 TypeError.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `for i in range(max(1, ep_num - window), ep_num):` (`modules/domain/agents/chief_writer_quality.py:465`)
- 호출자: `_check_cliche_overuse()`에서 `_count_recent_cliches(ep_num, content, ...)` (`modules/domain/agents/chief_writer_quality.py:205`)
- 상류/하류 컨텍스트:
- 상류: `_check_cliche_overuse(self, content: str, genre_name: str, ep_num: int = None)` (`modules/domain/agents/chief_writer_quality.py:199`)
- 하류: `counts[keyword] += content.count(keyword)` (`modules/domain/agents/chief_writer_quality.py:470`)
- 실패 시나리오: `ep_num`이 None/비정수면 산술 TypeError.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/domain/agents/chief_writer_quality.py:363 — rubric 평가 전 content 타입 정규화 누락

**문제**: `_evaluate_with_rubric()`는 JSON 파싱 후 `content`를 문자열로 강제하지 않고 바로 문자열 전용 연산(`.count`, `re.split`)을 수행한다.

**문제 코드**:
```python
data = json.loads(manuscript)
content = data.get("content", "")
...
direct_count = sum(content.count(e) for e in direct_emotions)
...
sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", content) if len(s.strip()) > 5]
```

**호출 체인**: `_generate_single_candidate()` → `apply_self_critique()` → `_evaluate_with_rubric()` (`modules/domain/agents/chief_writer.py:454`, `modules/domain/agents/chief_writer_quality.py:67`, `modules/domain/agents/chief_writer_quality.py:354`)

**수정 제안**:
```python
content = data.get("content", "")
if isinstance(content, list):
    content = "\n".join(str(x) for x in content)
elif isinstance(content, dict):
    content = content.get("text") or content.get("content") or json.dumps(content, ensure_ascii=False)
elif not isinstance(content, str):
    content = str(content) if content is not None else ""
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 8 완료
## Round 9 — modules/domain/agents/chief_writer_prompts.py

### 진행 통계 업데이트
- 총 발견: 3건 (CRITICAL: 0, HIGH: 3, MEDIUM: 0)
- 라운드 진행: 9/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/chief_writer_prompts.py:81` `_load_prompt(key: str, fallback: str) -> str` — PromptLoader 래퍼.
- `modules/domain/agents/chief_writer_prompts.py:86` `get_prompt_template_output() -> str`.
- `modules/domain/agents/chief_writer_prompts.py:106` `build_chief_writer_main_prompt(...) -> str` — 메인 프롬프트 조립.
- `modules/domain/agents/chief_writer_prompts.py:221` `get_fix_issues_prompt(...) -> str` — 교정 프롬프트 조립.
- `modules/domain/agents/chief_writer_prompts.py:249` `get_anti_trope_instructions(*, genre_name: str) -> str`.

### 5-D. 읽기 증명
1. 마지막 함수: `def get_anti_trope_instructions(*, genre_name: str) -> str:` (`modules/domain/agents/chief_writer_prompts.py:249`)
2. 특징 문자열: `[Role] 웹소설 1타 작가 (Chief Writer)` (`modules/domain/agents/chief_writer_prompts.py:142`)
3. import 목록:
- `from modules.core.prompt_loader import PromptLoader` (`modules/domain/agents/chief_writer_prompts.py:7`)
- 프로젝트 모듈 import는 파일 구조상 위 1개(단일 의존).
- 추가 프로젝트 import 없음(파일 전수 확인).

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `return loaded if loaded is not None else fallback` (`modules/domain/agents/chief_writer_prompts.py:83`)
- 호출자: `get_prompt_template_output()` (`modules/domain/agents/chief_writer_prompts.py:86`)
- 상류/하류 컨텍스트:
- 상류: `loaded = _PROMPT_LOADER.load("chief_writer", key)` (`modules/domain/agents/chief_writer_prompts.py:82`)
- 하류: `PROMPT_TEMPLATE_OUTPUT = get_prompt_template_output()` (`modules/domain/agents/chief_writer.py:90`)
- 실패 시나리오: loader가 dict/list를 반환해도 타입 검증 없이 통과되어 하류에서 문자열 API 사용 시 실패.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `{self.PROMPT_TEMPLATE_OUTPUT.format(strategy=strategy)}` (`modules/domain/agents/chief_writer.py:393`)
- 호출자: `_generate_single_candidate()` prompt 구성 (`modules/domain/agents/chief_writer.py:361`)
- 상류/하류 컨텍스트:
- 상류: `PROMPT_TEMPLATE_OUTPUT`는 prompt 파일에서 로드 (`modules/domain/agents/chief_writer.py:90`)
- 하류: `response = self.ask(prompt=full_prompt, ...)` (`modules/domain/agents/chief_writer.py:417`)
- 실패 시나리오: 로드된 템플릿에 `{strategy}` 외 미정의 placeholder가 있으면 `.format(...)` KeyError.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `loaded = _PROMPT_LOADER.load("chief_writer", key)` (`modules/domain/agents/chief_writer_prompts.py:82`)
- 호출자: `_load_prompt()` → 다수 getter (`modules/domain/agents/chief_writer_prompts.py:86`, `modules/domain/agents/chief_writer_prompts.py:90`, `modules/domain/agents/chief_writer_prompts.py:94`)
- 상류/하류 컨텍스트:
- 상류: `_PROMPT_LOADER = PromptLoader()` (`modules/domain/agents/chief_writer_prompts.py:78`)
- 하류: `build_chief_writer_main_prompt(..., common_rules=get_common_rules_section(), ...)` (`modules/domain/agents/chief_writer_context.py:320`)
- 실패 시나리오: YAML 키가 존재해도 값이 빈 문자열이면 fallback이 아닌 빈 문자열이 채택되어 핵심 제약 문구가 사라짐.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 9 완료
## Round 10 — modules/domain/agents/director.py + modules/domain/agents/director_ensemble.py

### 진행 통계 업데이트
- 총 발견: 4건 (CRITICAL: 0, HIGH: 4, MEDIUM: 0)
- 라운드 진행: 10/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/director.py:19` `class Director(BaseAgent)` — Director facade, 하위 모듈 위임.
- `modules/domain/agents/director.py:241` `select_and_judge_ensemble(...)` — 앙상블 선택 엔트리.
- `modules/domain/agents/director.py:325` `check_manuscript_continuity_with_cache(...) -> dict` — 연속성 검증 위임.
- `modules/domain/agents/director_ensemble.py:24` `class DirectorEnsembleSelector` — 앙상블 선택/판정 코어.
- `modules/domain/agents/director_ensemble.py:244` `select_and_judge_ensemble(...) -> dict` — 후보 비교 + 최종 verdict.
- `modules/domain/agents/director_ensemble.py:470` `quick_judge_single(...) -> dict` — 긴급 단일 원고 판정.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def check_manuscript_continuity_with_cache(` (`modules/domain/agents/director.py:325`)
- `def quick_judge_single(` (`modules/domain/agents/director_ensemble.py:470`)
2. 특징 문자열:
- `logging.warning("[Director] ENSEMBLE_SELECTION_PROMPT not found in prompt loader")` (`modules/domain/agents/director_ensemble.py:361`)
- `logging.warning(f"⚠️ [V60.97] LLM 선택 {old_selection} -> {selected_letter}로 교체 (분량 기준)")` (`modules/domain/agents/director_ensemble.py:413`)
3. import 목록:
- `from .director_ensemble import DirectorEnsembleSelector` (`modules/domain/agents/director.py:8`)
- `from .director_grading import DirectorGradingSystem` (`modules/domain/agents/director.py:9`)
- `from modules.core.prompt_loader import PromptLoader` (`modules/domain/agents/director_ensemble.py:13`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `_existing_issues = feedback.get("issues", [])` + `_existing_issues.append(f"[자유 리뷰] {_open_review}")` (`modules/domain/agents/director_ensemble.py:450`, `modules/domain/agents/director_ensemble.py:451`)
- 호출자: `stage4_interview_round.run()`에서 director 판정 호출 (`modules/core/stage4_interview_round.py:495`)
- 상류/하류 컨텍스트:
- 상류: `feedback = result.get("feedback", {})` (`modules/domain/agents/director_ensemble.py:442`)
- 하류: `return { ..., "feedback": feedback, ... }` (`modules/domain/agents/director_ensemble.py:462`)
- 실패 시나리오: `feedback["issues"]`가 문자열이면 `.append`에서 AttributeError.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `ms_len = len(c.get("manuscript") or "")` (`modules/domain/agents/director_ensemble.py:281`)
- 호출자: `select_and_judge_ensemble()` 후보 자격 필터 (`modules/domain/agents/director_ensemble.py:244`)
- 상류/하류 컨텍스트:
- 상류: `candidates`는 interview_round에서 전달 (`modules/core/stage4_interview_round.py:497`)
- 하류: `qualified_indices.append(idx)` (`modules/domain/agents/director_ensemble.py:283`)
- 실패 시나리오: 후보 원소가 dict가 아닌 타입이면 `.get` 호출 크래시.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `"warnings": "\n".join(v.get("warnings", [])) or "(경고 없음)",` (`modules/domain/agents/director_ensemble.py:329`)
- 호출자: 내부 헬퍼 `get_candidate_info(idx)` (`modules/domain/agents/director_ensemble.py:323`)
- 상류/하류 컨텍스트:
- 상류: `v = validation_results[idx] if idx < len(validation_results) else {}` (`modules/domain/agents/director_ensemble.py:325`)
- 하류: prompt 로더 인자 `warnings_a/b/c`로 주입 (`modules/domain/agents/director_ensemble.py:352`, `modules/domain/agents/director_ensemble.py:355`, `modules/domain/agents/director_ensemble.py:358`)
- 실패 시나리오: `warnings`가 문자열이면 문자 단위 join으로 의미 손실(오판 가능).
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/domain/agents/director_ensemble.py:451 — feedback.issues 타입 미검증 append

**문제**: `feedback`이 dict여도 `issues`가 리스트라는 보장이 없는데 `.append()`를 직접 호출한다.

**문제 코드**:
```python
_existing_issues = feedback.get("issues", [])
_existing_issues.append(f"[자유 리뷰] {_open_review}")
feedback["issues"] = _existing_issues
```

**호출 체인**: `Stage4InterviewRound.run()` → `Director.select_and_judge_ensemble()` → `DirectorEnsembleSelector.select_and_judge_ensemble()` (`modules/core/stage4_interview_round.py:495`, `modules/domain/agents/director.py:257`, `modules/domain/agents/director_ensemble.py:244`)

**수정 제안**:
```python
_existing_issues = feedback.get("issues", [])
if not isinstance(_existing_issues, list):
    _existing_issues = [str(_existing_issues)] if _existing_issues else []
_existing_issues.append(f"[자유 리뷰] {_open_review}")
feedback["issues"] = _existing_issues
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 10 완료

## 10라운드 오탐 재검증

- 재검증 대상: `[HIGH] modules/core/stage4_post_processor.py:40`, `[HIGH] modules/domain/agents/chief_writer.py:461`, `[HIGH] modules/domain/agents/chief_writer_quality.py:363`, `[HIGH] modules/domain/agents/director_ensemble.py:451`
- 판정 변경: 없음.
- 유지 사유:
- `stage4_post_processor.py:40`은 동일 try 블록 내 커밋 이전 예외에서 rollback 부재가 확인됨.
- `chief_writer.py:461`은 self-critique 경로의 content 재정규화 누락이 재확인됨.
- `chief_writer_quality.py:363`은 content 타입 미정규화 상태로 문자열 전용 연산 수행이 재확인됨.
- `director_ensemble.py:451`은 feedback.issues 리스트 보장 없이 append 호출이 재확인됨.

## Round 11 — modules/domain/agents/director_auditor.py

### 진행 통계 업데이트
- 총 발견: 5건 (CRITICAL: 0, HIGH: 4, MEDIUM: 1)
- 라운드 진행: 11/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/director_auditor.py:31` `class DirectorQualityAuditor` — Director 품질감사 코어.
- `modules/domain/agents/director_auditor.py:58` `_run_genre_specific_validation(...) -> dict` — 장르 심화 검증.
- `modules/domain/agents/director_auditor.py:322` `audit_manuscript(...) -> dict` — 원고 감사 메인.
- `modules/domain/agents/director_auditor.py:681` `audit_strategic_plan(...) -> dict` — 전략(Arc) 감사.
- `modules/domain/agents/director_auditor.py:798` `_strategic_audit_with_self_consistency(...) -> dict`.
- `modules/domain/agents/director_auditor.py:934` `validate_protagonist_config_compliance(...) -> dict`.

### 5-D. 읽기 증명
1. 마지막 함수: `def validate_protagonist_config_compliance(self, manuscript: str, ep_num: int = 0) -> dict:` (`modules/domain/agents/director_auditor.py:934`)
2. 특징 문자열: `logging.info(f"✅ [V49.3] Self-Consistency 완료: {final_decision} (PASS {pass_votes}/{len(evaluations)}, median={median_score})")` (`modules/domain/agents/director_auditor.py:879`)
3. import 목록:
- `from modules.core.prompt_loader import PromptLoader` (`modules/domain/agents/director_auditor.py:19`)
- `from modules.validation.threshold_helper import _threshold` (`modules/domain/agents/director_auditor.py:20`)
- `from modules.validation.validation_orchestrator import ValidationOrchestrator` (`modules/domain/agents/director_auditor.py:21`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `with ThreadPoolExecutor(max_workers=min(3, len(vote_tasks))) as executor:` (`modules/domain/agents/director_auditor.py:823`)
- 호출자: `audit_strategic_plan()`에서 self-consistency 경로 진입 (`modules/domain/agents/director_auditor.py:746`)
- 상류/하류 컨텍스트:
- 상류: `vote_tasks = [(i, 0.1 + (i * 0.05)) for i in range(1, self._d.consistency_votes)]` (`modules/domain/agents/director_auditor.py:818`)
- 하류: `for future in as_completed(futures, timeout=VOTE_ENSEMBLE_TIMEOUT):` (`modules/domain/agents/director_auditor.py:828`)
- 실패 시나리오: `self._d.consistency_votes == 1`이면 `vote_tasks`가 비어 `max_workers=0`, 즉시 ValueError.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `matches = re.findall(pattern, manuscript, re.IGNORECASE)` (`modules/domain/agents/director_auditor.py:943`)
- 호출자: `validate_protagonist_config_compliance()` (`modules/domain/agents/director_auditor.py:934`)
- 상류/하류 컨텍스트:
- 상류: `if world_origin == "원시시대":` 분기 (`modules/domain/agents/director_auditor.py:928`)
- 하류: `violations.append(...)` (`modules/domain/agents/director_auditor.py:945`)
- 실패 시나리오: `manuscript`가 None/non-str이면 `re.findall` TypeError.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `except (ValueError, KeyError, IndexError) as e:` (`modules/domain/agents/director_auditor.py:90`)
- 호출자: `_run_genre_specific_validation()` (`modules/domain/agents/director_auditor.py:58`)
- 상류/하류 컨텍스트:
- 상류: `result = self._d.guard.run_deep_validation(manuscript, current_state)` (`modules/domain/agents/director_auditor.py:82`)
- 하류: 정상 경로 `return result` (`modules/domain/agents/director_auditor.py:88`)
- 실패 시나리오: guard 내부 `TypeError`/`AttributeError`는 미포착으로 상위 전파 가능.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [MEDIUM] modules/domain/agents/director_auditor.py:823 — Self-Consistency 투표수 1일 때 ThreadPoolExecutor(0)

**문제**: 추가 투표 수가 0일 수 있는 경계조건(`consistency_votes=1`)을 고려하지 않아 `max_workers=0`으로 크래시.

**문제 코드**:
```python
vote_tasks = [(i, 0.1 + (i * 0.05)) for i in range(1, self._d.consistency_votes)]
...
with ThreadPoolExecutor(max_workers=min(3, len(vote_tasks))) as executor:
```

**호출 체인**: `audit_strategic_plan()` → `_strategic_audit_with_self_consistency()` (`modules/domain/agents/director_auditor.py:746`, `modules/domain/agents/director_auditor.py:798`)

**수정 제안**:
```python
if not vote_tasks:
    first_eval["self_consistency"] = {"votes": 1, "reason": "single_vote_config", "pass_votes": int(first_decision == "PASS")}
    return first_eval
with ThreadPoolExecutor(max_workers=min(3, len(vote_tasks))) as executor:
    ...
```

**확신도**: MEDIUM

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 11 완료
## Round 12 — modules/domain/agents/director_grading.py

### 진행 통계 업데이트
- 총 발견: 6건 (CRITICAL: 0, HIGH: 5, MEDIUM: 1)
- 라운드 진행: 12/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/director_grading.py:14` `class DirectorGradingSystem` — Director 등급/판정 로직.
- `modules/domain/agents/director_grading.py:68` `grade_manuscript_v59(...) -> dict` — 품질 등급화.
- `modules/domain/agents/director_grading.py:141` `_extract_category_score(...) -> float`.
- `modules/domain/agents/director_grading.py:456` `get_adaptive_threshold(...) -> dict`.
- `modules/domain/agents/director_grading.py:550` `apply_adaptive_decision(...) -> dict`.
- `modules/domain/agents/director_grading.py:577` `on_approve_workflow(...) -> dict`.

### 5-D. 읽기 증명
1. 마지막 함수: `def on_approve_workflow(self, ep_num, state_updates, current_hud, martial_manager=None) -> dict:` (`modules/domain/agents/director_grading.py:577`)
2. 특징 문자열: `"Writer가 state_updates를 제출하지 않음 - 상태 변경 없음"` (`modules/domain/agents/director_grading.py:588`)
3. import 목록:
- `from modules.core.constants import ManuscriptLimits` (`modules/domain/agents/director_grading.py:12`)
- 프로젝트 모듈 import는 파일 구조상 위 1개(단일 의존).
- 추가 프로젝트 import 없음(파일 전수 확인).

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `if isinstance(value, str) and (value.startswith("+") or value.startswith("-")):` (`modules/domain/agents/director_grading.py:606`)
- 호출자: `Stage4PostProcessor.process_pass_result()`의 승인 워크플로우 (`modules/core/stage4_post_processor.py:57`)
- 상류/하류 컨텍스트:
- 상류: `approved = self.ctx.agents["director"].on_approve_workflow(..., state_updates=final_state_updates, ...)` (`modules/core/stage4_post_processor.py:57`)
- 하류: 검증 후 `applied[key] = value` (`modules/domain/agents/director_grading.py:650`)
- 실패 시나리오: `state_updates`가 정수/실수 값으로 오면 한계치 검증이 완전히 건너뛰어 비정상 대규모 변동이 그대로 적용됨.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `base_score = validation_result.get("total_score", 0)` (`modules/domain/agents/director_grading.py:89`)
- 호출자: `Director.grade_manuscript_v59()` 위임 (`modules/domain/agents/director.py:226`)
- 상류/하류 컨텍스트:
- 상류: `return self._grading.grade_manuscript_v59(ep_num, manuscript, validation_result)` (`modules/domain/agents/director.py:226`)
- 하류: `breakdown = validation_result.get("breakdown", {})` (`modules/domain/agents/director_grading.py:90`)
- 실패 시나리오: `validation_result`가 None이면 즉시 AttributeError.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `scores.append((score / max_score) * 100 if max_score > 0 else 0)` (`modules/domain/agents/director_grading.py:161`)
- 호출자: `grade_manuscript_v59()`에서 `_extract_category_score()` 반복 호출 (`modules/domain/agents/director_grading.py:95`)
- 상류/하류 컨텍스트:
- 상류: `score = item_data.get("score", 0)` + `max_score = item_data.get("max", 1)` (`modules/domain/agents/director_grading.py:159`, `modules/domain/agents/director_grading.py:160`)
- 하류: 카테고리별 `weighted_score` 계산 (`modules/domain/agents/director_grading.py:96`)
- 실패 시나리오: `score/max`가 문자열 타입이면 산술/비교에서 TypeError.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/domain/agents/director_grading.py:606 — 비문자열 state 업데이트가 한계치 검증 우회

**문제**: 증가/감소 한계 검증이 문자열 `+/-` 포맷에서만 수행되어 숫자형 입력은 무검증 적용된다.

**문제 코드**:
```python
if isinstance(value, str) and (value.startswith("+") or value.startswith("-")):
    ...
applied[key] = value
```

**호출 체인**: `Stage4PostProcessor.process_pass_result()` → `Director.on_approve_workflow()` → `DirectorGradingSystem.on_approve_workflow()` (`modules/core/stage4_post_processor.py:57`, `modules/domain/agents/director.py:220`, `modules/domain/agents/director_grading.py:577`)

**수정 제안**:
```python
if isinstance(value, (int, float)) and key in LIMITS:
    change = int(value)
elif isinstance(value, str) and (value.startswith("+") or value.startswith("-")):
    change = int(re.match(r"^([+-]?\d+)", value).group(1)) if re.match(...) else None
else:
    change = None
# change가 있으면 LIMITS 공통 검증 적용
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 12 완료
## Round 13 — modules/domain/agents/director_continuity.py

### 진행 통계 업데이트
- 총 발견: 6건 (CRITICAL: 0, HIGH: 5, MEDIUM: 1)
- 라운드 진행: 13/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/director_continuity.py:15` `class DirectorContinuityValidator` — 연속성/충돌 검증.
- `modules/domain/agents/director_continuity.py:41` `validate_entity_consistency(...) -> dict`.
- `modules/domain/agents/director_continuity.py:338` `check_manuscript_history_conflicts(...) -> dict`.
- `modules/domain/agents/director_continuity.py:445` `check_manuscript_history_with_cache(...) -> dict`.
- `modules/domain/agents/director_continuity.py:560` `check_blueprint_continuity_with_cache(...) -> dict`.
- `modules/domain/agents/director_continuity.py:664` `check_manuscript_continuity_with_cache(...) -> dict`.

### 5-D. 읽기 증명
1. 마지막 함수: `def check_manuscript_continuity_with_cache(` (`modules/domain/agents/director_continuity.py:664`)
2. 특징 문자열: `"Prompt loading failed: MANUSCRIPT_HISTORY_CONFLICT_PROMPT"` (`modules/domain/agents/director_continuity.py:399`)
3. import 목록:
- `from modules.core.constants import ContextLimits` (`modules/domain/agents/director_continuity.py:10`)
- `from modules.core.prompt_loader import PromptLoader` (`modules/domain/agents/director_continuity.py:11`)
- 프로젝트 모듈 import는 파일 구조상 위 2개.

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `h_ep = h.get("ep_num", "?")` (`modules/domain/agents/director_continuity.py:374`)
- 호출자: `check_manuscript_history_conflicts()` (`modules/domain/agents/director_continuity.py:338`)
- 상류/하류 컨텍스트:
- 상류: `recent_history = manuscript_history[-30:]` (`modules/domain/agents/director_continuity.py:369`)
- 하류: `history_parts.append(f"[제{h_ep}화]\n{h_text}")` (`modules/domain/agents/director_continuity.py:378`)
- 실패 시나리오: `manuscript_history` 원소가 dict가 아니면 `.get` AttributeError.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `prev_data = prev_bp.get("data", {})` (`modules/domain/agents/director_continuity.py:605`)
- 호출자: `check_blueprint_continuity_with_cache()` (`modules/domain/agents/director_continuity.py:560`)
- 상류/하류 컨텍스트:
- 상류: `prev_bp = recent_blueprints[-1] if recent_blueprints else {}` (`modules/domain/agents/director_continuity.py:604`)
- 하류: `prev_end_location = prev_data.get("end_location", "")` (`modules/domain/agents/director_continuity.py:612`)
- 실패 시나리오: `recent_blueprints` 원소 타입 드리프트 시 `.get` 실패 후 전체 UNKNOWN 경로.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `new_start_location = new_blueprint.get("start_location", "")` (`modules/domain/agents/director_continuity.py:617`)
- 호출자: `check_blueprint_continuity_with_cache()` (`modules/domain/agents/director_continuity.py:560`)
- 상류/하류 컨텍스트:
- 상류: 함수 시그니처 `new_blueprint: dict` (`modules/domain/agents/director_continuity.py:560`)
- 하류: 위치 불연속 판정 `if prev_end_location not in new_start_location ...` (`modules/domain/agents/director_continuity.py:625`)
- 실패 시나리오: 비dict 입력이면 `.get` 실패, except 처리로 UNKNOWN 반환되어 검증 품질 저하.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 13 완료
## Round 14 — modules/domain/agents/director_prompts.py + modules/domain/agents/director_caching.py

### 진행 통계 업데이트
- 총 발견: 6건 (CRITICAL: 0, HIGH: 5, MEDIUM: 1)
- 라운드 진행: 14/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/director_prompts.py:10` `ENSEMBLE_SELECTION_PROMPT` — Stage4 앙상블 선택 프롬프트.
- `modules/domain/agents/director_prompts.py:154` `MANUSCRIPT_HISTORY_CONFLICT_PROMPT` — 원고 이력 충돌 프롬프트.
- `modules/domain/agents/director_prompts.py:206` `STRATEGIC_AUDIT_PROMPT_V30` — 전략 감사 프롬프트.
- `modules/domain/agents/director_prompts.py:285` `DIRECTOR_AUDIT_PROMPT_V30` — Director 감사 프롬프트.
- `modules/domain/agents/director_caching.py:13` `class DirectorCachingManager` — 캐시 관리.
- `modules/domain/agents/director_caching.py:66` `create_manuscript_cache(...) -> str`.
- `modules/domain/agents/director_caching.py:160` `get_protagonist_config(self) -> dict`.

### 5-D. 읽기 증명
1. 마지막 함수/선언:
- `director_prompts.py`는 함수/클래스 없이 상수 선언 파일, 마지막 주요 선언은 `DIRECTOR_AUDIT_PROMPT_V30` (`modules/domain/agents/director_prompts.py:285`)
- `def get_protagonist_config(self) -> dict:` (`modules/domain/agents/director_caching.py:160`)
2. 특징 문자열:
- `[Role] 웹소설 1타 편집장 (Chief Director)` (`modules/domain/agents/director_prompts.py:11`)
- `logging.warning(f"⚠️ [V60.87] 원고 히스토리 로드 실패: {e}")` (`modules/domain/agents/director_caching.py:62`)
3. import 목록:
- `from .base_agent import BaseAgent` (`modules/domain/agents/director_caching.py:10`)
- `director_prompts.py` 프로젝트 import 없음(상수 전용 파일).
- 추가 프로젝트 import 없음.

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `if ms_data and ms_data.get("content"):` (`modules/domain/agents/director_caching.py:57`)
- 호출자: `build_manuscript_history_for_check()` (`modules/domain/agents/director_caching.py:42`)
- 상류/하류 컨텍스트:
- 상류: `ms_data = db_manager.get_manuscript(prev_ep)` (`modules/domain/agents/director_caching.py:56`)
- 하류: `history.append({"ep_num": prev_ep, "text": ..., "summary": ...})` (`modules/domain/agents/director_caching.py:59`)
- 실패 시나리오: DB 반환이 dict가 아니면 `.get` 실패, except로 루프 전체가 중단되어 이력이 비정상 축소.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `cache = self.client.caches.create(` (`modules/domain/agents/director_caching.py:130`)
- 호출자: `create_manuscript_cache()` (`modules/domain/agents/director_caching.py:66`)
- 상류/하류 컨텍스트:
- 상류: `if not self.manuscript_cache_enabled: return None` (`modules/domain/agents/director_caching.py:78`)
- 하류: `self.manuscript_cache_name = cache.name` (`modules/domain/agents/director_caching.py:140`)
- 실패 시나리오: client 초기화 이상/권한 문제 시 예외 후 None 반환, 후속 연속성 검증 캐시 경로 비활성.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `for ep_num in range(1, current_ep):` (`modules/domain/agents/director_caching.py:89`)
- 호출자: `create_manuscript_cache(db_manager, current_ep, ...)` (`modules/domain/agents/director_caching.py:66`)
- 상류/하류 컨텍스트:
- 상류: 함수 입력 `current_ep` (외부 주입)
- 하류: `compiled_text` 조립 및 캐시 생성 (`modules/domain/agents/director_caching.py:107`, `modules/domain/agents/director_caching.py:130`)
- 실패 시나리오: `current_ep`가 정수가 아니면 range TypeError, 캐시 생성 실패로 degrade.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 14 완료
## Round 15 — modules/domain/agents/manuscript_validator.py

### 진행 통계 업데이트
- 총 발견: 6건 (CRITICAL: 0, HIGH: 5, MEDIUM: 1)
- 라운드 진행: 15/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/manuscript_validator.py:18` `class ManuscriptValidator` — Python 사전검증기.
- `modules/domain/agents/manuscript_validator.py:71` `validate_candidate(...) -> dict`.
- `modules/domain/agents/manuscript_validator.py:196` `validate_all_candidates(...) -> list[dict]`.
- `modules/domain/agents/manuscript_validator.py:611` `_llm_verify_warnings(...) -> list[str]`.
- `modules/domain/agents/manuscript_validator.py:688` `format_warnings_for_director(...) -> str`.
- `modules/domain/agents/manuscript_validator.py:951` `_check_financial_numbers(...) -> dict`.

### 5-D. 읽기 증명
1. 마지막 함수: `def _check_financial_numbers(` (`modules/domain/agents/manuscript_validator.py:951`)
2. 특징 문자열: `lines.append("⚠️ 경고는 참고용입니다. 최종 판단은 Director가 내립니다.")` (`modules/domain/agents/manuscript_validator.py:710`)
3. import 목록:
- `from modules.core.constants import ManuscriptLimits` (`modules/domain/agents/manuscript_validator.py:15`)
- 프로젝트 모듈 import는 파일 구조상 위 1개(단일 의존).
- 추가 프로젝트 import 없음.

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `manuscript = candidate.get("manuscript", "")` (`modules/domain/agents/manuscript_validator.py:219`)
- 호출자: `validate_all_candidates()` (`modules/domain/agents/manuscript_validator.py:196`)
- 상류/하류 컨텍스트:
- 상류: `for candidate in candidates:` (`modules/domain/agents/manuscript_validator.py:218`)
- 하류: `result = self.validate_candidate(...)` (`modules/domain/agents/manuscript_validator.py:243`)
- 실패 시나리오: candidate 원소가 dict가 아니면 `.get` AttributeError.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `strategy = result.get("strategy", f"후보{i + 1}")` (`modules/domain/agents/manuscript_validator.py:694`)
- 호출자: `format_warnings_for_director(validation_results)` (`modules/domain/agents/manuscript_validator.py:688`)
- 상류/하류 컨텍스트:
- 상류: `for i, result in enumerate(validation_results):` (`modules/domain/agents/manuscript_validator.py:693`)
- 하류: `warning_count = result.get("warning_count", 0)` (`modules/domain/agents/manuscript_validator.py:695`)
- 실패 시나리오: validation_results 원소 타입 드리프트 시 `.get` 크래시.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `ep_num = prev.get("ep_num", "?")` / `prev_text = prev.get("content", "")` (`modules/domain/agents/manuscript_validator.py:999`)
- 호출자: `_check_financial_numbers(manuscript, recent_manuscripts)` (`modules/domain/agents/manuscript_validator.py:951`)
- 상류/하류 컨텍스트:
- 상류: `if recent_manuscripts:` (`modules/domain/agents/manuscript_validator.py:992`)
- 하류: 과거 대비 경고 append (`modules/domain/agents/manuscript_validator.py:1011`, `modules/domain/agents/manuscript_validator.py:1022`)
- 실패 시나리오: recent_manuscripts 원소가 dict가 아니면 `.get` 실패.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 15 완료

## Round 16 — modules/domain/agents/block_enricher.py

### 진행 통계 업데이트
- 총 발견: 6건 (CRITICAL: 0, HIGH: 5, MEDIUM: 1)
- 라운드 진행: 16/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/block_enricher.py:192` `class BlockEnricher(BaseAgent)` — Treatment Block 농축 전담 에이전트.
- `modules/domain/agents/block_enricher.py:214` `analyze_block_density(self, block: dict) -> dict` — 블록 정보량/결핍 요소 분석.
- `modules/domain/agents/block_enricher.py:287` `enrich_block(self, current_block: dict, reference_block: dict, prev_block: dict | None = None, next_block: dict | None = None, protagonist_name: str = "주인공", genre: str = "wuxia") -> dict` — 단일 블록 농축.
- `modules/domain/agents/block_enricher.py:571` `enrich_all_blocks_parallel(self, treatment_blocks: list, protagonist_name: str = "주인공", genre: str = "wuxia", reference_block_index: int = 0, batch_size: int = 5, ui=None) -> dict` — 배치 병렬 농축 + 인과 검증.
- `modules/domain/agents/block_enricher.py:730` `_check_causal_errors(self, enriched_blocks: list) -> list` — 농축 결과 인과 오류 점검.
- `modules/domain/agents/block_enricher.py:801` `_re_enrich_with_causal_fix(self, current_block: dict, enriched_prev_block: dict, next_block: dict | None, reference_block: dict, causal_issue: str, protagonist_name: str, genre: str) -> dict` — 인과 오류 블록 재농축.

### 5-D. 읽기 증명
1. 마지막 함수: `def _re_enrich_with_causal_fix(` (`modules/domain/agents/block_enricher.py:801`)
2. 특징 문자열: `logging.warning(f"[BlockEnricher] validate_causal_chain 실패 (non-blocking): {e}")` (`modules/domain/agents/block_enricher.py:798`)
3. import 목록:
- `from .base_agent import BaseAgent` (`modules/domain/agents/block_enricher.py:13`)
- 프로젝트 내부 import는 위 1개이며, 나머지는 stdlib/local import(`json`, `re`, `concurrent.futures`) 중심.
- 파일 전수 확인 결과 추가 내부 모듈 import 없음.

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `reference_block = treatment_blocks[reference_block_index]` (`modules/domain/agents/block_enricher.py:590`)
- 호출자: `main_a.py`의 `_enrich_treatment_blocks()`에서 `enrich_all_blocks_parallel(..., reference_block_index=0, ...)` 호출 (`main_a.py:1251`)
- 상류/하류 컨텍스트:
- 상류: `if not treatment_blocks or len(treatment_blocks) < 2: ... return treatment_file` (`main_a.py:1188`)
- 하류: `enriched_blocks[reference_block_index] = treatment_blocks[reference_block_index]` (`modules/domain/agents/block_enricher.py:592`)
- 실패 시나리오: 외부에서 빈 리스트/잘못된 index로 직접 호출 시 IndexError.
- 판정: 안전(현재 공식 호출 경로에 길이/인덱스 가드 존재), API 오용 리스크는 존재.

2. 위험 지점
- 코드 원문: `for batch_start in range(0, len(enrich_targets), batch_size):` (`modules/domain/agents/block_enricher.py:636`)
- 호출자: `enrich_all_blocks_parallel()` 내부 배치 루프 진입.
- 상류/하류 컨텍스트:
- 상류: 함수 시그니처 `batch_size: int = 5` (`modules/domain/agents/block_enricher.py:577`)
- 하류: `with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:` (`modules/domain/agents/block_enricher.py:641`)
- 실패 시나리오: `batch_size <= 0`이면 `range(..., step=0)` 또는 thread pool 생성에서 예외.
- 판정: RISK (Design Check Needed) — 현재 `main_a.py`는 `batch_size=5`로 호출하지만 공용 함수 자체 가드는 없음.

3. 위험 지점
- 코드 원문: `return result.get("issues", [])` (`modules/domain/agents/block_enricher.py:793`)
- 호출자: `enrich_all_blocks_parallel()`의 `causal_issues = self._check_causal_errors(enriched_blocks)` (`modules/domain/agents/block_enricher.py:682`)
- 상류/하류 컨텍스트:
- 상류: `if isinstance(result, str): result = self._extract_json_robust(result)` (`modules/domain/agents/block_enricher.py:790`)
- 하류: 예외 시 `return []  # 검증 실패 시 빈 리스트` (`modules/domain/agents/block_enricher.py:799`)
- 실패 시나리오: `result`가 dict가 아니면 `.get` AttributeError → except로 흡수되어 인과 오류를 전부 놓치는 fail-open.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 16 완료

## Round 17 — modules/domain/agents/writer.py + modules/core/writer_prompt_builders.py

### 진행 통계 업데이트
- 총 발견: 7건 (CRITICAL: 0, HIGH: 6, MEDIUM: 1)
- 라운드 진행: 17/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/writer.py:33` `class Writer(BaseAgent)` — ChiefWriter 실패 시 폴백 집필 에이전트.
- `modules/domain/agents/writer.py:56` `write_v20_manuscript(self, ep_num, breakdown_doc, master_bible, hud_report, purism_prompt, style_mode="", intro_dna="CYNICAL", feedback="", prev_full_manuscript="", arc_doc="", tactical_references="", protagonist_name="주인공", entity_registry=None)` — 폴백 원고 생성 메인.
- `modules/domain/agents/writer.py:238` `_fallback_full_request(self, dynamic_prompt)` — 캐시 미사용 경로 전체 요청.
- `modules/domain/agents/writer.py:255` `_sanitize_leakage(self, text)` — JSON 누수 필드 제거/정리.
- `modules/core/writer_prompt_builders.py:14` `build_mandatory_context(db, master_bible, current_ep: int) -> str` — 강제 맥락 빌드.
- `modules/core/writer_prompt_builders.py:55` `build_justification_guidance(hud_report: str, genre_name: str) -> str` — HUD 기반 정당화 패턴 주입.
- `modules/core/writer_prompt_builders.py:182` `_extract_recent_events(db, current_ep: int, n_episodes: int = 3) -> list` — 최근 사건 추출.
- `modules/core/writer_prompt_builders.py:214` `_extract_npc_last_states(master_bible: dict, current_ep: int) -> dict` — NPC 최근 관계 상태 추출.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def _format_entity_registry_for_writer(self, entity_registry: dict) -> str` (`modules/domain/agents/writer.py:346`)
- `def _extract_npc_last_states(master_bible: dict, current_ep: int) -> dict` (`modules/core/writer_prompt_builders.py:214`)
2. 특징 문자열:
- `# [V70] ask()가 dict를 직접 반환할 수 있음 → re.sub TypeError 방어` (`modules/domain/agents/writer.py:259`)
- `"[Sweep5-D] recent events extraction failed (ep=%s): %s"` (`modules/core/writer_prompt_builders.py:207`)
3. import 목록:
- `from modules.core.hud_utils import get_hud_trend_safe as _get_hud_trend_safe_shared` (`modules/domain/agents/writer.py:18`)
- `from modules.core.writer_prompt_builders import build_mandatory_context as _build_mandatory_context_shared` (`modules/domain/agents/writer.py:25`)
- `from .base_agent import BaseAgent` (`modules/domain/agents/writer.py:31`)
- `from modules.core.justification_patterns import get_justification_guide` (함수 내부 import, `modules/core/writer_prompt_builders.py:58`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `bible_root = master_bible.get("MasterBible", master_bible)` (`modules/domain/agents/writer.py:83`)
- 호출자: `write_v20_manuscript()` 진입 시 master_bible 사용.
- 상류/하류 컨텍스트:
- 상류: 함수 입력 `master_bible`는 타입 강제가 없음 (`modules/domain/agents/writer.py:60`)
- 하류: `core_identity = bible_root.get("ProjectData", {}).get("CoreIdentity", {})` (`modules/domain/agents/writer.py:84`)
- 실패 시나리오: `master_bible=None` 또는 dict 외 타입이면 `.get`에서 AttributeError.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `if any(constraint in hud_report for constraint in physical_constraints):` (`modules/core/writer_prompt_builders.py:64`)
- 호출자: `writer.py`에서 `justification_guidance = _build_justification_guidance_shared(hud_report, ...)` (`modules/domain/agents/writer.py:157`)
- 상류/하류 컨텍스트:
- 상류: `hud_report`는 외부 입력(함수 시그니처상 타입 고정 없음) (`modules/domain/agents/writer.py:61`)
- 하류: `hud_lower = hud_report.lower()` (`modules/core/writer_prompt_builders.py:67`)
- 실패 시나리오: `hud_report=None`이면 `in`/`.lower()`에서 TypeError/AttributeError.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `filtered = [line for line in text.splitlines() if not re.search(r'"(Beat \d+|continuation_text)":', line)]` (`modules/domain/agents/writer.py:275`)
- 호출자: `_fallback_full_request()`가 `self._sanitize_leakage(self.ask(...))`를 반환 (`modules/domain/agents/writer.py:251`, `modules/domain/agents/writer.py:253`)
- 상류/하류 컨텍스트:
- 상류: dict만 별도 분기 처리 (`modules/domain/agents/writer.py:260`)
- 하류: 반환값이 Stage4 폴백 원고로 직결 (`modules/domain/agents/writer.py:236`)
- 실패 시나리오: `ask()`가 list/기타 비문자열을 반환하면 `splitlines()` 호출에서 AttributeError.
- 판정: BUG.

### 5-C. 발견된 버그
### [HIGH] modules/domain/agents/writer.py:275 — `_sanitize_leakage()`가 list 응답에서 크래시

**문제**: `_sanitize_leakage()`는 `dict`만 예외 처리하고, list/tuple 같은 비문자열 응답은 그대로 `splitlines()`를 호출한다. LLM 응답이 JSON 배열일 때 폴백 경로 전체가 AttributeError로 중단될 수 있다.

**문제 코드**:
```python
if isinstance(text, dict):
    banned_keys = ["Beat 3", "Beat 4", "continuation_text", "scene_summary"]
    for key in banned_keys:
        text.pop(key, None)
    return json.dumps(text, ensure_ascii=False, indent=4)
...
filtered = [line for line in text.splitlines() if not re.search(r'"(Beat \d+|continuation_text)":', line)]
return "\n".join(filtered)
```

**호출 체인**: `write_v20_manuscript()` → `_fallback_full_request()` → `_sanitize_leakage()` (`modules/domain/agents/writer.py:236`, `modules/domain/agents/writer.py:251`, `modules/domain/agents/writer.py:255`)

**수정 제안**:
```python
if isinstance(text, dict):
    ...
    return json.dumps(text, ensure_ascii=False, indent=4)
if isinstance(text, list):
    return json.dumps(text, ensure_ascii=False, indent=4)
if not isinstance(text, str):
    text = str(text)
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 17 완료

## Round 18 — modules/core/writer_template.py + modules/core/manuscript_enhancer.py

### 진행 통계 업데이트
- 총 발견: 8건 (CRITICAL: 0, HIGH: 6, MEDIUM: 2)
- 라운드 진행: 18/100

### 5-A. 파일 구조 요약
- `modules/core/writer_template.py:69` `class WriterTemplate` — Blueprint 기반 집필 템플릿 생성기.
- `modules/core/writer_template.py:115` `generate_template(self, blueprint: dict[str, Any], prev_ending: str = "", inventory: list[str] = None) -> ManuscriptTemplate` — 씬 슬롯 템플릿 생성.
- `modules/core/writer_template.py:207` `generate_prompt_injection(self, template: ManuscriptTemplate) -> str` — 프롬프트 주입 문자열 변환.
- `modules/core/writer_template.py:327` `validate_against_template(self, manuscript: str, template: ManuscriptTemplate) -> dict[str, Any]` — 원고-템플릿 정합성 검증.
- `modules/core/manuscript_enhancer.py:561` `class DialogueBeatInjector` — 대화 비트/환경 앵커 분석기.
- `modules/core/manuscript_enhancer.py:567` `analyze_dialogues(self, text: str) -> dict[str, Any]` — 연속 대화 이슈 탐지.
- `modules/core/manuscript_enhancer.py:146` `check_overdue(self, current_ep: int) -> list[dict]` — 복선 기한 초과 체크.
- `modules/core/manuscript_enhancer.py:681` `analyze(self, manuscript: str, scenes: list[dict] = None, current_ep: int = 1) -> EnhancementResult` — 통합 품질 분석.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def create_writer_template(genre: str = "wuxia") -> WriterTemplate` (`modules/core/writer_template.py:416`)
- `def create_enhancer(genre: str = "wuxia") -> ManuscriptEnhancer` (`modules/core/manuscript_enhancer.py:775`)
2. 특징 문자열:
- `lines.append("⚠️ 각 씬을 순서대로 빠짐없이 작성하세요.")` (`modules/core/writer_template.py:274`)
- `lines.append("[V55.7 대화 비트 삽입 필요]")` (`modules/core/manuscript_enhancer.py:628`)
3. import 목록:
- `from modules.core.constants import ManuscriptLimits` (`modules/core/writer_template.py:25`)
- `manuscript_enhancer.py`는 프로젝트 내부 import 없이 stdlib(`re`, `dataclass`, `typing`)만 사용.
- 두 파일 전수 확인 결과 추가 내부 모듈 import 없음.

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `ep_num = blueprint.get("ep_num", 0)` (`modules/core/writer_template.py:129`)
- 호출자: `generate_template()` 외부 진입.
- 상류/하류 컨텍스트:
- 상류: 함수 시그니처는 `blueprint: dict[str, Any]`지만 런타임 강제 없음 (`modules/core/writer_template.py:116`)
- 하류: `scene_breakdown = blueprint.get("scene_breakdown", {})` (`modules/core/writer_template.py:130`)
- 실패 시나리오: blueprint가 None/문자열이면 `.get`에서 AttributeError.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `total_max_chars=min(12000, total_max)` (`modules/core/writer_template.py:181`)
- 호출자: `generate_template()` 반환 `ManuscriptTemplate`.
- 상류/하류 컨텍스트:
- 상류: `scene_breakdown`이 비어 있으면 `total_max`는 0 유지 (`modules/core/writer_template.py:136`, `modules/core/writer_template.py:140`)
- 하류: 검증에서 `elif length > template.total_max_chars * 1.2:` (`modules/core/writer_template.py:345`)
- 실패 시나리오: 빈 씬 입력 시 `min_chars > max_chars` 범위가 만들어져 템플릿 검증이 왜곡됨.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `deadline = f.planted_ep + self.DEADLINES[f.importance]` (`modules/core/manuscript_enhancer.py:152`)
- 호출자: `generate_feedback()` → `check_overdue(current_ep)` (`modules/core/manuscript_enhancer.py:166`)
- 상류/하류 컨텍스트:
- 상류: `add_foreshadow(..., importance: str = "minor")` (`modules/core/manuscript_enhancer.py:134`)
- 하류: `if current_ep > deadline:` (`modules/core/manuscript_enhancer.py:153`)
- 실패 시나리오: importance가 정의되지 않은 문자열이면 KeyError.
- 판정: RISK (Design Check Needed).

4. 위험 지점
- 코드 원문: `for i, between in enumerate(parts[1:], 1): ... return {"total_dialogues": len(dialogues), "max_consecutive": max_consecutive, "issues": issues}` (`modules/core/manuscript_enhancer.py:578`, `modules/core/manuscript_enhancer.py:594`)
- 호출자: `ManuscriptEnhancer.analyze()`에서 `dialogue = self.dialogue_injector.analyze_dialogues(manuscript)` (`modules/core/manuscript_enhancer.py:738`)
- 상류/하류 컨텍스트:
- 상류: 이슈 추가는 `else` 분기에서만 수행 (`modules/core/manuscript_enhancer.py:583`)
- 하류: `result.dialogue_issues = len(dialogue["issues"]) + ...` (`modules/core/manuscript_enhancer.py:740`)
- 실패 시나리오: 텍스트 끝까지 연속 대화가 이어지면 루프 종료 후 flush가 없어 마지막 연속 구간이 누락됨.
- 판정: BUG.

### 5-C. 발견된 버그
### [MEDIUM] modules/core/manuscript_enhancer.py:578 — `analyze_dialogues()` 마지막 연속 대화 구간 누락

**문제**: 연속 대화 카운트는 `else` 분기에서만 확정되기 때문에, 텍스트 끝에서 연속 대화가 끝나는 경우 `issues`/`max_consecutive`에 반영되지 않는다. 결과적으로 대화 비트 이슈를 과소탐지한다.

**문제 코드**:
```python
for i, between in enumerate(parts[1:], 1):  # 첫 부분 제외
    if len(between.strip()) < 20:
        consecutive_count += 1
    else:
        if consecutive_count >= 3:
            issues.append(
                {
                    "position": i,
                    "consecutive": consecutive_count,
                    "suggestion": "대화 비트 삽입 (행동, 표정, 환경 반응)",
                }
            )
        max_consecutive = max(max_consecutive, consecutive_count)
        consecutive_count = 0

return {"total_dialogues": len(dialogues), "max_consecutive": max_consecutive, "issues": issues}
```

**호출 체인**: `ManuscriptEnhancer.analyze()` → `DialogueBeatInjector.analyze_dialogues()` (`modules/core/manuscript_enhancer.py:738`, `modules/core/manuscript_enhancer.py:567`)

**수정 제안**:
```python
for i, between in enumerate(parts[1:], 1):
    ...
if consecutive_count >= 3:
    issues.append(
        {
            "position": len(parts) - 1,
            "consecutive": consecutive_count,
            "suggestion": "대화 비트 삽입 (행동, 표정, 환경 반응)",
        }
    )
max_consecutive = max(max_consecutive, consecutive_count)
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 18 완료

## Round 19 — modules/core/stage2_orchestrator.py

### 진행 통계 업데이트
- 총 발견: 9건 (CRITICAL: 0, HIGH: 7, MEDIUM: 2)
- 라운드 진행: 19/100

### 5-A. 파일 구조 요약
- `modules/core/stage2_orchestrator.py:19` `class Stage2Orchestrator` — Stage2 Arc 설계 오케스트레이터.
- `modules/core/stage2_orchestrator.py:26` `__init__(self, app, *, context=None) -> None` — app/context 주입.
- `modules/core/stage2_orchestrator.py:80` `stage_2_arcs_async_logic(self)` — Stage2 메인 비동기 파이프라인.
- `modules/core/stage2_orchestrator.py:756` `_preflight_state_setup(self, **kwargs)` — preflight 래퍼.
- `modules/core/stage2_orchestrator.py:788` `_is_tactical_doc_duplicate(self, candidate_text: str, reference_texts: list, threshold: float = 0.98) -> bool` — 중복 전술서 래퍼.
- `modules/core/stage2_orchestrator.py:801` `_stage2_flow_guard(self, refined_arc: dict) -> dict` — flow guard 래퍼.
- `modules/core/stage2_orchestrator.py:805` `_stage2_flow_guard_legacy(self, normalized: str) -> dict` — 레거시 flow guard 래퍼.

### 5-D. 읽기 증명
1. 마지막 함수: `def _stage2_flow_guard_legacy(self, normalized: str) -> dict` (`modules/core/stage2_orchestrator.py:805`)
2. 특징 문자열: `self.ctx.ui.log("✨ [Success] 0124 매니페스토 기반 전술 설계 전 공정 완료.")` (`modules/core/stage2_orchestrator.py:748`)
3. import 목록:
- `from modules.core.stage2_context import Stage2Context` (`modules/core/stage2_orchestrator.py:42`)
- `from modules.core.stage2_validation_pipeline import Stage2ValidationPipeline` (`modules/core/stage2_orchestrator.py:55`)
- `from modules.core.stage2_preflight import Stage2PreflightAnalysis` (`modules/core/stage2_orchestrator.py:64`)
- `from modules.core.stage2_finalizer import Stage2Finalizer` (`modules/core/stage2_orchestrator.py:73`)
- `from modules.domain.agents.state_tracker import StateTracker` (`modules/core/stage2_orchestrator.py:97`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `next_b_safe = {"block_id": arcs_source[idx + 1].get("block_id", f"Block {idx + 2}"), "title": arcs_source[idx + 1].get("title", "미정")}` (`modules/core/stage2_orchestrator.py:250`)
- 호출자: `stage_2_arcs_async_logic()` 내부 `throttled_enrich(idx)` (`modules/core/stage2_orchestrator.py:244`)
- 상류/하류 컨텍스트:
- 상류: `curr_b = arcs_source[idx]` (`modules/core/stage2_orchestrator.py:247`)
- 하류: `enrich_raw_block_async(curr_b, prev_b, next_b_safe, ...)` (`modules/core/stage2_orchestrator.py:256`)
- 실패 시나리오: `arcs_source[idx+1]`가 dict가 아니면 `.get` AttributeError.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `_fin["action"]` (`modules/core/stage2_orchestrator.py:734` 인접 블록에서 반복 사용: `if _fin["action"] == "break":`, `if _fin["action"] in {"retry", "next"}:`)
- 호출자: `self.finalizer.run_finalize(...)` 결과 `_fin` 처리 (`modules/core/stage2_orchestrator.py:526`)
- 상류/하류 컨텍스트:
- 상류: `_fin = await self.finalizer.run_finalize(...)` (`modules/core/stage2_orchestrator.py:518`)
- 하류: retry/break 분기와 캐시 무효화 (`modules/core/stage2_orchestrator.py:545`, `modules/core/stage2_orchestrator.py:560`)
- 실패 시나리오: 하위 모듈 계약 위반으로 `action` 누락 시 KeyError.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: 
`_skip_ep = (arcs_source[global_arc_no - 1].get("ep_count", 5) if global_arc_no <= len(arcs_source) else 5)`  
`current_ep_start += _skip_ep` (`modules/core/stage2_orchestrator.py:682`, `modules/core/stage2_orchestrator.py:687`)
- 호출자: Arc 실패 후 사용자 선택 `"1"` 또는 `"4"+"skip"` 분기 (`modules/core/stage2_orchestrator.py:680`, `modules/core/stage2_orchestrator.py:704`)
- 상류/하류 컨텍스트:
- 상류: 실패 처리 루프에서 수동 선택 입력 (`modules/core/stage2_orchestrator.py:678`)
- 하류: 다음 Arc 시작 에피소드 계산 (`modules/core/stage2_orchestrator.py:733`)
- 실패 시나리오: `ep_count`가 문자열이면 `int + str` TypeError로 실패 복구 루프 자체가 중단됨.
- 판정: BUG.

### 5-C. 발견된 버그
### [HIGH] modules/core/stage2_orchestrator.py:687 — skip 경로에서 `ep_count` 타입 미정규화

**문제**: 실패 후 건너뛰기 경로에서 `ep_count`를 정수로 정규화하지 않고 누적한다. Arc 원본의 `ep_count`가 `"5"` 같은 문자열이면 `current_ep_start += _skip_ep`에서 TypeError가 발생해 복구 동작이 깨진다.

**문제 코드**:
```python
_skip_ep = (
    arcs_source[global_arc_no - 1].get("ep_count", 5)
    if global_arc_no <= len(arcs_source)
    else 5
)  # [V70] 하드코딩 5 → 실제 ep_count
current_ep_start += _skip_ep
```

**호출 체인**: `stage_2_arcs_async_logic()` → Arc 실패 분기 → 사용자 선택 `"건너뛰고 계속"` 처리 (`modules/core/stage2_orchestrator.py:80`, `modules/core/stage2_orchestrator.py:672`, `modules/core/stage2_orchestrator.py:680`)

**수정 제안**:
```python
raw_skip_ep = (
    arcs_source[global_arc_no - 1].get("ep_count", 5)
    if global_arc_no <= len(arcs_source)
    else 5
)
try:
    _skip_ep = int(raw_skip_ep)
except (TypeError, ValueError):
    _skip_ep = 5
current_ep_start += max(1, _skip_ep)
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 19 완료

## Round 20 — modules/core/stage2_preflight.py

### 진행 통계 업데이트
- 총 발견: 9건 (CRITICAL: 0, HIGH: 7, MEDIUM: 2)
- 라운드 진행: 20/100

### 5-A. 파일 구조 요약
- `modules/core/stage2_preflight.py:7` `class Stage2PreflightAnalysis` — Stage2 preflight(상태 준비/분석/생성 보강) 담당.
- `modules/core/stage2_preflight.py:17` `_preflight_state_setup(self, *, all_refined_arcs: list, arcs_source: list, arc_idx: int, lack_report: dict, grand_obj: str, global_arc_no: int, constraint_db) -> dict` — 시도 루프 초기 상태 세팅.
- `modules/core/stage2_preflight.py:40` `_compute_arc_drive() -> dict` (중첩) — Weaver 욕망 드라이브 생성.
- `modules/core/stage2_preflight.py:66` `_compute_preflight() -> tuple` (중첩) — preflight 분석 캐시 생성.
- `modules/core/stage2_preflight.py:195` `_preflight_arc_analysis(self, *, attempt: int, current_feedback: str, constraint_block: str, last_refined_context: str, all_refined_arcs: list, protagonist_name: str, global_arc_no: int, cached_preflight_injection: str, cached_preflight_result) -> dict` — 시도별 분석 컨텍스트 구축.
- `modules/core/stage2_preflight.py:417` `_preflight_enrichment(self, *, attempt: int, global_arc_no: int, current_ep_start: int, current_vol_strategy: dict, enriched_block: dict, all_refined_arcs: list, bible_root: dict, protagonist_name: str, director_feedback_for_fourphase: str, entity_registry_for_director, genre_for_tracker: str, previous_attempt: dict | None = None) -> dict` — FourPhase 생성 + state tracker 반영.

### 5-D. 읽기 증명
1. 마지막 함수: `def _preflight_enrichment(` (`modules/core/stage2_preflight.py:417`)
2. 특징 문자열: `f"[V64.P4] CRITICAL: extract_cumulative_state 실패 (NPC 검증 약화): {e}"` (`modules/core/stage2_preflight.py:151`)
3. import 목록:
- `from modules.core.constants import Emojis, RetryLimits` (`modules/core/stage2_preflight.py:216`)
- `from modules.core.spinners import V50_MODULES_AVAILABLE` (`modules/core/stage2_preflight.py:217`)
- `from modules.core.spinners import StageSpinner` (`modules/core/stage2_preflight.py:440`)
- `from modules.core.constants import PatchModeThresholds` (`modules/core/stage2_preflight.py:474`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `arc_drive = _fut_drive.result(timeout=300)` / `_cached_preflight_injection, _cached_preflight_result = _fut_preflight.result(timeout=300)` (`modules/core/stage2_preflight.py:103`, `modules/core/stage2_preflight.py:104`)
- 호출자: `_preflight_state_setup()` 병렬 프리플라이트 구간.
- 상류/하류 컨텍스트:
- 상류: `with concurrent.futures.ThreadPoolExecutor(max_workers=2) as _parallel_exec:` (`modules/core/stage2_preflight.py:100`)
- 하류: 예외 시 `arc_drive = {}`로 강등 (`modules/core/stage2_preflight.py:107`)
- 실패 시나리오: 둘 중 하나만 타임아웃이어도 둘 다 기본값으로 강등되어 품질 저하 발생.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `if four_phase_arc and pipeline_result.get("final_verdict") == "PASS":` (`modules/core/stage2_preflight.py:531`)
- 호출자: `_preflight_enrichment()` 내 FourPhase 결과 판정.
- 상류/하류 컨텍스트:
- 상류: `four_phase_arc, pipeline_result = self.ctx.agents["four_phase"].generate(...)` (`modules/core/stage2_preflight.py:512`)
- 하류: 성공 시 `pipeline_result.get('retries', 0)` 참조 (`modules/core/stage2_preflight.py:541`)
- 실패 시나리오: 하위 generate가 dict 외 타입을 반환하면 `.get` AttributeError, except로 전체 FourPhase 시도 실패 처리.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `_st = self.ctx.state_tracker` + `_copy.deepcopy(_st.npc_registry)` (`modules/core/stage2_preflight.py:546`, `modules/core/stage2_preflight.py:548`)
- 호출자: `_preflight_enrichment()` PASS 분기에서 스냅샷 생성.
- 상류/하류 컨텍스트:
- 상류: PASS 조건 `if four_phase_arc and pipeline_result.get("final_verdict") == "PASS"` (`modules/core/stage2_preflight.py:531`)
- 하류: 동일 블록에서 상태 추출 연쇄 호출 (`modules/core/stage2_preflight.py:569` 이후)
- 실패 시나리오: state_tracker가 None/불완전 초기화면 deep copy 단계에서 AttributeError.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 20 완료

## 20라운드 오탐 재검증

- 재검증 대상: `[HIGH] modules/domain/agents/writer.py:275`, `[MEDIUM] modules/core/manuscript_enhancer.py:578`, `[HIGH] modules/core/stage2_orchestrator.py:687`
- 판정 변경: 없음.
- 유지 사유:
- `writer.py:275`는 `dict` 외 비문자열(list 등)에 대한 `splitlines()` 호출 경로가 그대로 남아 있음.
- `manuscript_enhancer.py:578`은 루프 종료 후 trailing `consecutive_count` flush가 없어 마지막 연속 대화 구간이 누락됨.
- `stage2_orchestrator.py:687`은 skip 분기 `ep_count`를 정수화하지 않고 누적하는 코드가 유지됨.

## Round 21 — modules/core/stage2_validation_pipeline.py

### 진행 통계 업데이트
- 총 발견: 10건 (CRITICAL: 0, HIGH: 8, MEDIUM: 2)
- 라운드 진행: 21/100

### 5-A. 파일 구조 요약
- `modules/core/stage2_validation_pipeline.py:13` `class Stage2ValidationPipeline` — Stage2 사전 검증 체인.
- `modules/core/stage2_validation_pipeline.py:23` `run_validation(self, *, refined_arc, four_phase_passed: bool, all_refined_arcs: list, entity_registry_for_director, global_arc_no: int, current_ep_start: int, current_feedback: str, generation_method: str, constraint_block: str, enriched_block: dict, draft_validator_passed: bool, consensus_passed: bool, attempt: int, protagonist_name: str, constraint_db) -> dict` — DraftValidator/Consensus/Flow/Continuity 검증 메인.
- `modules/core/stage2_validation_pipeline.py:552` `_normalize_tactical_text(self, text: str) -> str` — 전술서 정규화.
- `modules/core/stage2_validation_pipeline.py:563` `_is_tactical_doc_duplicate(self, candidate_text: str, reference_texts: list, threshold: float = 0.98) -> bool` — 전술서 중복 판정.
- `modules/core/stage2_validation_pipeline.py:597` `_stage2_flow_guard(self, refined_arc: dict) -> dict` — 서사 구조 기반 flow guard.
- `modules/core/stage2_validation_pipeline.py:684` `_stage2_flow_guard_legacy(self, normalized: list) -> dict` — 레거시 flow guard 폴백.

### 5-D. 읽기 증명
1. 마지막 함수: `def _stage2_flow_guard_legacy(self, normalized: list) -> dict` (`modules/core/stage2_validation_pipeline.py:684`)
2. 특징 문자열: `self.ctx.ui.log(f"      🔍 [V49] Arc {global_arc_no} 연속성 검증 중...")` (`modules/core/stage2_validation_pipeline.py:384`)
3. import 목록:
- `from modules.core.constants import AIModels` (`modules/core/stage2_validation_pipeline.py:9`)
- `from modules.core.semantic_plot_guard import SemanticPlotGuard` (`modules/core/stage2_validation_pipeline.py:10`)
- `from modules.core.narrative_structure_analyzer import NarrativeStructureAnalyzer` (함수 내부 import, `modules/core/stage2_validation_pipeline.py:645`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문:
`draft_result = self.ctx.arc_draft_validator.validate(...)`  
`if not draft_result["valid"]:` (`modules/core/stage2_validation_pipeline.py:256`, `modules/core/stage2_validation_pipeline.py:269`)
- 호출자: Stage2 메인 루프에서 `_val = self.validation_pipeline.run_validation(...)` (`modules/core/stage2_orchestrator.py:486`)
- 상류/하류 컨텍스트:
- 상류: 앞선 DraftValidator 정보수집 블록은 try/except로 감싸져 있음 (`modules/core/stage2_validation_pipeline.py:60` 부근)
- 하류: `draft_result["critical_issues"]`/`draft_result["score"]` 직접 인덱싱 (`modules/core/stage2_validation_pipeline.py:270`, `modules/core/stage2_validation_pipeline.py:271`)
- 실패 시나리오: validator 내부 예외/비정상 반환 시 run_validation 전체가 예외로 탈출해 Stage2 루프가 깨짐.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `for v in violations[:3]: v_type = v.get("type", "unknown")` (`modules/core/stage2_validation_pipeline.py:454`, `modules/core/stage2_validation_pipeline.py:455`)
- 호출자: ContinuityInspector REJECT 처리 분기 (`modules/core/stage2_validation_pipeline.py:394`)
- 상류/하류 컨텍스트:
- 상류: `violations = continuity_result.get("violations", [])` (`modules/core/stage2_validation_pipeline.py:397`)
- 하류: `strong_kind_feedback = self.ctx.build_strong_kind_feedback(violations=violations, ...)` (`modules/core/stage2_validation_pipeline.py:499`)
- 실패 시나리오: violations 원소가 dict가 아닌 문자열이면 `.get` AttributeError.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `except Exception as e: ... return {"status": "PASS", "fallback": True}` (`modules/core/stage2_validation_pipeline.py:680`, `modules/core/stage2_validation_pipeline.py:682`)
- 호출자: `run_validation()` 내부 `flow_guard = self._stage2_flow_guard(refined_arc)` (`modules/core/stage2_validation_pipeline.py:227`)
- 상류/하류 컨텍스트:
- 상류: `result = analyzer.analyze(normalized[:5])` (`modules/core/stage2_validation_pipeline.py:650`)
- 하류: 호출부는 `status == "REJECT"`일 때만 재시도 분기 (`modules/core/stage2_validation_pipeline.py:228`)
- 실패 시나리오: 분석기 예외가 나면 PASS 폴백으로 통과되어 정체/반복 아크가 검증을 우회.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/core/stage2_validation_pipeline.py:256 — DraftValidator 2차 호출 예외 미처리

**문제**: 동일 함수 내 1차 DraftValidator 호출은 try/except 보호가 있는데, 2차 호출(실제 게이트)은 예외 처리가 없어 validator 오류가 그대로 전파된다. 결과적으로 `run_validation()`이 중단되어 Stage2 오케스트레이션이 크래시할 수 있다.

**문제 코드**:
```python
if not four_phase_passed and self.ctx.arc_draft_validator:
    draft_result = self.ctx.arc_draft_validator.validate(
        arc=refined_arc,
        prev_arcs=all_refined_arcs,
        constraint_block=constraint_block or "",
        state_tracker=self.ctx.state_tracker,
    )
...
if not draft_result["valid"]:
```

**호출 체인**: `stage_2_arcs_async_logic()` → `run_validation()` → `arc_draft_validator.validate()` (`modules/core/stage2_orchestrator.py:486`, `modules/core/stage2_validation_pipeline.py:23`, `modules/core/stage2_validation_pipeline.py:256`)

**수정 제안**:
```python
try:
    draft_result = self.ctx.arc_draft_validator.validate(...)
except Exception as dv_err:
    logging.warning(f"[DraftValidator] critical validation failed: {dv_err}")
    return {"action": "retry", "current_feedback": "DraftValidator 실행 오류. 입력 스키마를 정규화하라."}
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 21 완료

## Round 22 — modules/core/stage2_finalizer.py

### 진행 통계 업데이트
- 총 발견: 11건 (CRITICAL: 0, HIGH: 9, MEDIUM: 2)
- 라운드 진행: 22/100

### 5-A. 파일 구조 요약
- `modules/core/stage2_finalizer.py:10` `class Stage2Finalizer` — Director 심사 및 PASS/REJECT 후처리 전담.
- `modules/core/stage2_finalizer.py:20` `run_finalize(self, *, refined_arc: dict, enriched_block: dict, arc_drive: dict, all_refined_arcs: list, global_arc_no: int, current_ep_start: int, current_feedback: str, protagonist_name: str, suspected_duplicates: list, entity_registry_for_director, constraint_block: str, draft_validator_passed: bool, consensus_passed: bool, attempt: int, generation_method: str, st_snapshot, director_feedback_for_fourphase: str, last_refined_context: str, bible_root: dict, genre: str, constraint_db, is_patch: bool = False, prev_score: float = 0.0, patch_fallback: bool = False) -> dict` — Director 대면 및 DB 커밋 처리.
- `modules/core/stage2_finalizer.py:225` `_item_name(it)` (중첩) — 인벤토리 dict/str 통합 이름 추출.
- `modules/core/stage2_finalizer.py:493` `_record_s2_pass_metrics(self, *, global_arc_no: int, attempt: int, generation_method: str, audit: dict, is_patch: bool = False, prev_score: float = 0.0, patch_fallback: bool = False) -> None` — PASS 메트릭 기록.
- `modules/core/stage2_finalizer.py:551` `_record_s2_reject_metrics(self, *, global_arc_no: int, attempt: int, generation_method: str, audit: dict, is_patch: bool = False, prev_score: float = 0.0, patch_fallback: bool = False) -> None` — REJECT 메트릭 기록.

### 5-D. 읽기 증명
1. 마지막 함수: `def _record_s2_reject_metrics(` (`modules/core/stage2_finalizer.py:551`)
2. 특징 문자열: `self.ctx.ui.log("      ✅ [V60.43] DraftValidator + Consensus 통과로 PASS 오버라이드")` (`modules/core/stage2_finalizer.py:158`)
3. import 목록:
- `from modules.core.metrics_collector import get_metrics_collector` (`modules/core/stage2_finalizer.py:6`)
- `from modules.models.arc import validate_arc` (`modules/core/stage2_finalizer.py:7`)
- `from modules.core.constants import ContextLimits, RecoveryLimits` (함수 내부 import, `modules/core/stage2_finalizer.py:50`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `audit = self.ctx.agents["director"].audit_strategic_plan(...)` (`modules/core/stage2_finalizer.py:131`)
- 호출자: Stage2 오케스트레이터에서 `_fin = await self.finalizer.run_finalize(...)` (`modules/core/stage2_orchestrator.py:513`)
- 상류/하류 컨텍스트:
- 상류: `try: self.ctx.perf_timer.start(...)`는 있지만 director 호출 자체는 try/except 없음 (`modules/core/stage2_finalizer.py:71`)
- 하류: `if audit.get("decision") == "REJECT" ...` (`modules/core/stage2_finalizer.py:148`)
- 실패 시나리오: director 호출 예외(API/파싱/키오류) 시 run_finalize가 즉시 예외 전파되고 Stage2 루프가 중단됨.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `constraint_db.update_arc_state(refined_arc)` (`modules/core/stage2_finalizer.py:310`)
- 호출자: PASS 분기, DB 커밋 성공 직후.
- 상류/하류 컨텍스트:
- 상류: `safe_commit_async` 성공 후 상태 캐시 해제 (`modules/core/stage2_finalizer.py:306`)
- 하류: `last_refined_context = self.ctx.generate_arc_context_v60(...)` (`modules/core/stage2_finalizer.py:313`)
- 실패 시나리오: ConstraintDB 업데이트 예외 시 PASS 직후 파이프라인이 비정상 중단(커밋된 Arc와 런타임 상태 불일치 가능).
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `self.ctx.stage_rejection_history.append({...})` (`modules/core/stage2_finalizer.py:602`)
- 호출자: `_record_s2_reject_metrics()` (`modules/core/stage2_finalizer.py:551`)
- 상류/하류 컨텍스트:
- 상류: PassRateMonitor/QualityDashboard 기록은 try/except 보호 (`modules/core/stage2_finalizer.py:562`, `modules/core/stage2_finalizer.py:582`)
- 하류: stage2_optimizer 실패메모리 기록 (`modules/core/stage2_finalizer.py:611`)
- 실패 시나리오: `stage_rejection_history`가 None/초기화 누락이면 append에서 AttributeError.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/core/stage2_finalizer.py:131 — Director 심사 예외 미처리로 Stage2 중단

**문제**: `audit_strategic_plan()` 호출이 try/except 없이 직접 실행된다. Director 에이전트가 예외를 던지면 `run_finalize()` 전체가 실패하며, 상위 Stage2 루프도 복구 분기 없이 끊긴다.

**문제 코드**:
```python
audit = self.ctx.agents["director"].audit_strategic_plan(
    refined_arc,
    _expanded_prev_context,
    curr_block=enriched_block,
    protagonist_name=protagonist_name,
    suspected_duplicates=suspected_duplicates,
    entity_registry=entity_registry_for_director,
    story_context=_story_context,
)
```

**호출 체인**: `stage_2_arcs_async_logic()` → `run_finalize()` → `director.audit_strategic_plan()` (`modules/core/stage2_orchestrator.py:513`, `modules/core/stage2_finalizer.py:20`, `modules/core/stage2_finalizer.py:131`)

**수정 제안**:
```python
try:
    audit = self.ctx.agents["director"].audit_strategic_plan(...)
except Exception as dir_err:
    logging.warning(f"[Stage2Finalizer] director audit failed: {dir_err}")
    return {
        "action": "retry",
        "current_feedback": f"Director 심사 오류: {str(dir_err)[:120]}",
        "last_refined_context": last_refined_context,
        "current_ep_start": current_ep_start,
        "director_feedback_for_fourphase": director_feedback_for_fourphase,
        "st_snapshot": st_snapshot,
    }
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 22 완료

## Round 23 — modules/core/stage2_optimizer.py

### 진행 통계 업데이트
- 총 발견: 12건 (CRITICAL: 0, HIGH: 10, MEDIUM: 2)
- 라운드 진행: 23/100

### 5-A. 파일 구조 요약
- `modules/core/stage2_optimizer.py:29` `class StateSnapshotInjector` — 이전 Arc 상태 스냅샷 추출/주입.
- `modules/core/stage2_optimizer.py:66` `_collect_all_items(self, arc: dict) -> list[str]` — 획득/보유 아이템 통합 수집.
- `modules/core/stage2_optimizer.py:158` `class ArcAutoCorrector` — 자동 보정(중복아이템/상태/joint_docs) 수행.
- `modules/core/stage2_optimizer.py:426` `class NegativeConstraintAmplifier` — 금지 제약 강화 프롬프트 생성.
- `modules/core/stage2_optimizer.py:476` `_build_item_history(self, prev_arcs: list[dict]) -> list[dict]` — 아이템 획득 이력 구성.
- `modules/core/stage2_optimizer.py:650` `class FailureRecord` / `modules/core/stage2_optimizer.py:661` `class SessionFailureMemory` — 실패 패턴 메모리.
- `modules/core/stage2_optimizer.py:820` `class Stage2Optimizer` — 통합 최적화기(few-shot/feedback/autocorrect).
- `modules/core/stage2_optimizer.py:843` `generate_optimized_prompt(self, prev_arcs: list[dict], protagonist_name: str = "주인공", include_examples: bool = True) -> str` — 최적화 프롬프트 조립.
- `modules/core/stage2_optimizer.py:932` `create_stage2_optimizer() -> Stage2Optimizer` — 팩토리 함수.

### 5-D. 읽기 증명
1. 마지막 함수: `def create_stage2_optimizer() -> Stage2Optimizer` (`modules/core/stage2_optimizer.py:932`)
2. 특징 문자열: `logging.info("\n[V60.25 Stage 2 Optimizer 통계]")` (`modules/core/stage2_optimizer.py:920`)
3. import 목록:
- `stage2_optimizer.py`는 프로젝트 내부 모듈 import 없이 stdlib(`logging`, `re`, `dataclass`, `typing`)만 사용.
- 내부 모듈과의 연결은 호출자(`stage2_preflight.py`)를 통해 이뤄짐.
- 직접 내부 import 선언은 파일 전수 확인 결과 없음.

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `items.extend(state.get("items_acquired", []))` (`modules/core/stage2_optimizer.py:70`)
- 호출자: `extract_snapshot()`에서 `items_acquired_total = self._collect_all_items(prev_arc)` (`modules/core/stage2_optimizer.py:56`)
- 상류/하류 컨텍스트:
- 상류: `state = arc.get("state_constraints", {})` (`modules/core/stage2_optimizer.py:69`)
- 하류: `return list({_ikey(i) for i in items if i})` (`modules/core/stage2_optimizer.py:84`)
- 실패 시나리오: `items_acquired`가 문자열이면 `extend`가 문자 단위로 분해되어 아이템 히스토리가 조용히 오염됨.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `match = re.search(rf".{{0,50}}{re.escape(item)}.{{0,50}}", tactical)` (`modules/core/stage2_optimizer.py:491`)
- 호출자: `generate_optimized_prompt()` → `amplify_constraints()` → `_build_item_history()` (`modules/core/stage2_optimizer.py:843`, `modules/core/stage2_optimizer.py:451`, `modules/core/stage2_optimizer.py:476`)
- 상류/하류 컨텍스트:
- 상류: `items = state.get("items_acquired", [])` (`modules/core/stage2_optimizer.py:483`)
- 하류: `history.append({"item": item, ...})` (`modules/core/stage2_optimizer.py:502`)
- 실패 시나리오: `items_acquired` 원소가 dict/int면 `re.escape(item)`에서 TypeError로 크래시.
- 판정: BUG.

3. 위험 지점
- 코드 원문: `grants = state.get("grants_received", [])` + `for grant in grants:` (`modules/core/stage2_optimizer.py:513`, `modules/core/stage2_optimizer.py:516`)
- 호출자: `amplify_constraints()` 내 `grant_history = self._build_grant_history(prev_arcs)` (`modules/core/stage2_optimizer.py:454`)
- 상류/하류 컨텍스트:
- 상류: grant 타입 정규화 없음.
- 하류: `history.append({"grant": grant, ...})` (`modules/core/stage2_optimizer.py:526`)
- 실패 시나리오: `grants_received`가 문자열이면 문자 단위 분해로 히스토리 품질이 붕괴(비정상 제약 프롬프트 생성).
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/core/stage2_optimizer.py:491 — `_build_item_history()`의 비문자열 item에서 `re.escape` 크래시

**문제**: `items_acquired` 원소 타입을 보정하지 않고 바로 `re.escape(item)`를 호출한다. dict/list/int가 섞이면 `TypeError: decoding to str: need a bytes-like object`류 예외로 Stage2 optimizer 프롬프트 생성이 중단된다.

**문제 코드**:
```python
items = state.get("items_acquired", [])
...
for item in items:
    context = ""
    if tactical:
        match = re.search(rf".{{0,50}}{re.escape(item)}.{{0,50}}", tactical)
        if match:
            context = match.group(0)
```

**호출 체인**: `_preflight_arc_analysis()` → `stage2_optimizer.generate_optimized_prompt()` → `NegativeConstraintAmplifier.amplify_constraints()` → `_build_item_history()` (`modules/core/stage2_preflight.py:246`, `modules/core/stage2_optimizer.py:843`, `modules/core/stage2_optimizer.py:436`, `modules/core/stage2_optimizer.py:476`)

**수정 제안**:
```python
for raw_item in items:
    if isinstance(raw_item, dict):
        item = raw_item.get("name", raw_item.get("item", ""))
    else:
        item = str(raw_item) if raw_item is not None else ""
    if not item:
        continue
    if tactical:
        match = re.search(rf".{{0,50}}{re.escape(item)}.{{0,50}}", tactical)
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 23 완료

## Round 24 — modules/core/stage2_context.py + modules/core/stage3_context.py + modules/core/stage4_context.py

### 진행 통계 업데이트
- 총 발견: 12건 (CRITICAL: 0, HIGH: 10, MEDIUM: 2)
- 라운드 진행: 24/100

### 5-A. 파일 구조 요약
- `modules/core/stage2_context.py:4` `class Stage2Context` — Stage2 오케스트레이터 DI 컨텍스트.
- `modules/core/stage2_context.py:82` `def __init__(..., sync_cache_key_to_app=None)` — Stage2 속성/콜백 주입.
- `modules/core/stage2_context.py:180` `@classmethod def from_app(cls, app)` — `SovereignApp`에서 속성/콜백 추출.
- `modules/core/stage3_context.py:4` `class Stage3Context` — Stage3 오케스트레이터 DI 컨텍스트.
- `modules/core/stage3_context.py:41` `def __init__(..., safe_commit=None, validate_blueprint_integrity=None, fix_entity_registry_protagonist=None)` — Stage3 의존성 주입.
- `modules/core/stage3_context.py:84` `@classmethod def from_app(cls, app)` — Stage3 콜백 바인딩.
- `modules/core/stage4_context.py:4` `class Stage4Context` — Stage4 오케스트레이터 DI 컨텍스트.
- `modules/core/stage4_context.py:48` `def __init__(..., get_int_input=None, flush_audit_buffer=None, safe_commit=None)` — Stage4 의존성 주입.
- `modules/core/stage4_context.py:105` `@classmethod def from_app(cls, app)` — Stage4 콜백 바인딩.

### 5-D. 읽기 증명
1. 마지막 함수:
- `modules/core/stage2_context.py`: `def from_app(cls, app)` (`modules/core/stage2_context.py:180`)
- `modules/core/stage3_context.py`: `def from_app(cls, app)` (`modules/core/stage3_context.py:84`)
- `modules/core/stage4_context.py`: `def from_app(cls, app)` (`modules/core/stage4_context.py:105`)
2. 특징 문자열:
- `"""[Phase 4C-3] Stage2 DI 컨텍스트 — 속성·콜백 의존 주입"""` (`modules/core/stage2_context.py:1`)
- `"""[Phase 4C-4] Stage3 DI context: explicit attributes + callbacks."""` (`modules/core/stage3_context.py:1`)
- `"""[Phase 4C-2a/2b/2c] Stage4 DI 컨텍스트 — 속성·콜백 의존 주입"""` (`modules/core/stage4_context.py:1`)
3. import 목록:
- 세 파일 모두 프로젝트 내부 import 선언 없음 (컨텍스트 객체 정의 전용 파일).

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `get_int_input=getattr(app, "_get_int_input", None),` (`modules/core/stage4_context.py:127`)
- 호출자: `target_ep = self.ctx.get_int_input(...)` (`modules/core/stage4_orchestrator.py:700`)
- 상류/하류 컨텍스트:
- 상류: `def _get_int_input(...)`가 앱에 정의되어 있음 (`main_a.py:2278`)
- 하류: `target_ep`는 집필 루프 상한 계산에 사용 (`modules/core/stage4_orchestrator.py:351`)
- 실패 시나리오: 앱이 부분 초기화된 테스트 하네스에서 `_get_int_input` 미탑재 시 `NoneType` 호출 예외.
- 판정: 안전(메인 앱 계약에서는 메서드 존재), RISK (Design Check Needed for partial harness).

2. 위험 지점
- 코드 원문: `safe_commit=getattr(app, "_safe_commit", None),` (`modules/core/stage3_context.py:103`)
- 호출자: `if not ctx.safe_commit():` (`modules/core/stage3_orchestrator.py:479`)
- 상류/하류 컨텍스트:
- 상류: 앱에 `def _safe_commit(self) -> bool` 정의 (`main_a.py:279`)
- 하류: 실패 시 blueprint 저장 실패 분기 (`modules/core/stage3_orchestrator.py:480`)
- 실패 시나리오: 컨텍스트를 `from_app()` 아닌 수동 생성으로 쓰고 `safe_commit=None`이면 즉시 크래시.
- 판정: 안전(메인 앱 경로), RISK (Design Check Needed for manual DI usage).

3. 위험 지점
- 코드 원문: `stage_rejection_history=getattr(app, "stage_rejection_history", None),` (`modules/core/stage2_context.py:199`)
- 호출자: `self.ctx.stage_rejection_history.append(...)` (`modules/core/stage2_finalizer.py:602`)
- 상류/하류 컨텍스트:
- 상류: 앱 초기화 시 `self.stage_rejection_history = []` 설정 (`main_a.py:180`)
- 하류: Stage2 REJECT 히스토리 누적 (`modules/core/stage2_finalizer.py:603`)
- 실패 시나리오: 비표준 앱 인스턴스에서 `stage_rejection_history` 누락/None이면 append 크래시.
- 판정: 안전(메인 앱 경로), RISK (Design Check Needed for partial app lifecycle).

### 5-C. 발견된 버그
- 없음

---
## Round 24 완료

## Round 25 — modules/domain/agents/analyst.py (L1~750)

### 진행 통계 업데이트
- 총 발견: 12건 (CRITICAL: 0, HIGH: 10, MEDIUM: 2)
- 라운드 진행: 25/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/analyst.py:50` `class Analyst(BaseAgent)` — Stage1/레거시 Stage2 설계 에이전트.
- `modules/domain/agents/analyst.py:64` `def plan_single_volume_v20(self, vol_no, master_bible, treatment_raw_part, previous_volumes_context="", structured_context="", protagonist_name: str = None)` — 권 단위 전략 설계.
- `modules/domain/agents/analyst.py:166` `def _validate_arc_state_continuity_v60(self, current_arc: dict, prev_arc: dict) -> dict` — Arc 상태 계승 검증.
- `modules/domain/agents/analyst.py:271` `def _validate_tactical_doc_continuity_v60(self, tactical_doc: str, ep_count: int) -> dict` — 화 단위 모순 탐지.
- `modules/domain/agents/analyst.py:361` `def _auto_correct_joint_docs_v60(self, tactical_doc: str, arc_data: dict) -> dict` — joint_docs 자동 보정.
- `modules/domain/agents/analyst.py:439` `def plan_single_arc_v20(self, arc_no, vol_strategy, prev_block, curr_block, next_block, ep_start, prev_arc_context="", assets=None, full_roadmap="", assigned_seeds=None, feedback="", recent_patterns=None, protagonist_name=None, state_tracker=None)` — 단일 Arc 설계.
- `modules/domain/agents/analyst.py:742` `def _arc_attempt_func(attempt, retry_feedback)` — Arc 시도 루프 내부 실행 함수.

### 5-D. 읽기 증명
1. 마지막 함수(이번 구간 기준): `def _arc_attempt_func(attempt, retry_feedback)` (`modules/domain/agents/analyst.py:742`)
2. 특징 문자열: `logging.warning(f"⚠️ [Analyst] treatment 데이터 JSON 파싱 실패: {str(e)[:50]}")` (`modules/domain/agents/analyst.py:108`)
3. import 목록:
- `from modules.core.constants import HUDKeys` (`modules/domain/agents/analyst.py:22`)
- `from .analyst_prompt_api import (...)` (`modules/domain/agents/analyst.py:25`)
- `from .base_agent import BaseAgent` (`modules/domain/agents/analyst.py:36`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `prev_joint = prev_constraints.get("joint_docs", {})` (`modules/domain/agents/analyst.py:191`)
- 호출자: `continuity_result = self._validate_arc_state_continuity_v60(final_arc_data, prev_arc_data)` (`modules/domain/agents/analyst.py:965`)
- 상류/하류 컨텍스트:
- 상류: Arc 저장 경로는 top-level `joint_docs`를 기본으로 사용 (`modules/core/stage2_finalizer.py:174`)
- 하류: 위치/소지품 연속성 판단 (`modules/domain/agents/analyst.py:198`, `modules/domain/agents/analyst.py:207`)
- 실패 시나리오: 이전 Arc의 `joint_docs`가 top-level에만 있을 때 일부 연속성 점검 누락 가능.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `for i in range(1, ep_count + 1):` (`modules/domain/agents/analyst.py:297`)
- 호출자: `doc_continuity = self._validate_tactical_doc_continuity_v60(tactical_doc, final_ep_count)` (`modules/domain/agents/analyst.py:998`)
- 상류/하류 컨텍스트:
- 상류: `final_ep_count = final_arc_data.get("_actual_ep_count", target_ep_count)` (`modules/domain/agents/analyst.py:920`)
- 하류: 화별 섹션 정규식 탐색 (`modules/domain/agents/analyst.py:299`)
- 실패 시나리오: 비표준 호출로 `ep_count`에 비정수 전달 시 `TypeError`.
- 판정: 안전(내부 호출 경로에서는 정수화됨), RISK (Design Check Needed for external calls).

3. 위험 지점
- 코드 원문: `hud_lines.append(f"  보유 아이템: {', '.join(items[:8])}")` (`modules/domain/agents/analyst.py:700`)
- 호출자: `plan_single_arc_v20()` HUD 컨텍스트 구축 (`modules/domain/agents/analyst.py:683`)
- 상류/하류 컨텍스트:
- 상류: `items = state_dict.get("items", [])` (`modules/domain/agents/analyst.py:698`)
- 하류: `safe_data["protagonist_hud_state"]` 프롬프트에 주입 (`modules/domain/agents/analyst.py:724`)
- 실패 시나리오: `items` 리스트에 비문자열(dict 등) 혼입 시 `join`에서 TypeError.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 25 완료

## Round 26 — modules/domain/agents/analyst.py (L751~end)

### 진행 통계 업데이트
- 총 발견: 14건 (CRITICAL: 0, HIGH: 11, MEDIUM: 3)
- 라운드 진행: 26/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/analyst.py:742` `def _arc_attempt_func(attempt, retry_feedback)` — Arc 생성/재시도 단위 실행(후반부 포함).
- `modules/domain/agents/analyst.py:1043` `def _normalize_arc_output(self, arc_data, ep_start, ep_count)` — 회차/분량 메타 정규화.
- `modules/domain/agents/analyst.py:1101` `def total_absolute_recovery_v20(self, draft_contents, treatment_content="")` — Bible 복구.
- `modules/domain/agents/analyst.py:1153` `async def enrich_raw_block_async(self, raw_block, prev_block=None, next_block=None, assigned_seeds=None, transfused_history="")` — Raw block 농축.
- `modules/domain/agents/analyst.py:1202` `def analyze_context(self, mode="GENERAL", **kwargs) -> dict` — 수술 모드/일반 모드 분석.
- `modules/domain/agents/analyst.py:1301` `def perform_v35_calibration(self, current_hud, target_arc)` — 물리 수치 보정.
- `modules/domain/agents/analyst.py:1338` `def get_lack_report(self, martial_hud) -> dict` — 결핍 분석.
- `modules/domain/agents/analyst.py:1460` `def get_state_constraint_prompt(self, arc_no: int) -> str` — 이전 Arc 기반 상태 제약 프롬프트 생성.

### 5-D. 읽기 증명
1. 마지막 함수: `def get_state_constraint_prompt(self, arc_no: int) -> str` (`modules/domain/agents/analyst.py:1460`)
2. 특징 문자열: `logging.warning(f"⚠️ [Analyst] 상태 제약 프롬프트 생성 실패: {e}")` (`modules/domain/agents/analyst.py:1493`)
3. import 목록:
- `from modules.core.constants import HUDKeys` (`modules/domain/agents/analyst.py:22`)
- `from .analyst_prompt_api import (...)` (`modules/domain/agents/analyst.py:25`)
- `from .base_agent import BaseAgent` (`modules/domain/agents/analyst.py:36`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `if arcs_anchor and isinstance(arcs_anchor, dict):` (`modules/domain/agents/analyst.py:958`)
- 호출자: `plan_single_arc_v20()` 후반 연속성 검증 블록 (`modules/domain/agents/analyst.py:953`)
- 상류/하류 컨텍스트:
- 상류: Arc 저장은 list 형태로 앵커 저장 (`modules/core/stage2_finalizer.py:282`)
- 하류: 이전 Arc가 없다고 간주되면 상태 계승 검증 전체 스킵 (`modules/domain/agents/analyst.py:964`)
- 실패 시나리오: `load_anchor("arcs")`가 list일 때 이전 Arc 로드가 항상 누락되어 연속성 검증이 무력화.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `final_arc_data["tactical_doc"] = warning_text + tactical_doc` (`modules/domain/agents/analyst.py:1008`)
- 호출자: `if doc_continuity["issues"]:` 분기 (`modules/domain/agents/analyst.py:999`)
- 상류/하류 컨텍스트:
- 상류: `_validate_tactical_doc_continuity_v60()`는 dict `tactical_doc`도 허용/처리 (`modules/domain/agents/analyst.py:287`)
- 하류: 경고 주입 후 Arc 반환 (`modules/domain/agents/analyst.py:1039`)
- 실패 시나리오: `tactical_doc`가 dict이고 연속성 이슈가 발생하면 `str + dict`로 TypeError 발생.
- 판정: BUG.

3. 위험 지점
- 코드 원문: `start_state["equipment"] = list(set(existing))` (`modules/domain/agents/analyst.py:989`)
- 호출자: 연속성 자동 보정(`missing_items`) 적용 분기 (`modules/domain/agents/analyst.py:984`)
- 상류/하류 컨텍스트:
- 상류: `existing = start_state.get("equipment", [])` (`modules/domain/agents/analyst.py:985`)
- 하류: 보정 후 `start_state` 반영 (`modules/domain/agents/analyst.py:990`)
- 실패 시나리오: `existing`에 비해시형 원소(dict 등)가 섞여 있으면 set 변환에서 TypeError.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/domain/agents/analyst.py:958 — `arcs` 앵커 타입 오판으로 이전 Arc 로드가 상시 누락

**문제**: `load_anchor("arcs")`를 dict로 가정하지만 실제 저장 경로는 list다. 이 조건 때문에 `prev_arc_data`가 비어 연속성 검증(`_validate_arc_state_continuity_v60`)이 스킵된다.

**문제 코드**:
```python
arcs_anchor = self.context.db.load_anchor("arcs")
if arcs_anchor and isinstance(arcs_anchor, dict):
    prev_arc_data = arcs_anchor.get(f"arc_{clean_arc_no - 1}")
```

**호출 체인**: `plan_single_arc_v20()` 내부 연속성 검증 진입 → `load_anchor("arcs")` 타입 검사 실패 → `if prev_arc_data:` 블록 미진입 (`modules/domain/agents/analyst.py:953`, `modules/domain/agents/analyst.py:957`, `modules/domain/agents/analyst.py:964`)

**수정 제안**:
```python
arcs_anchor = self.context.db.load_anchor("arcs")
if isinstance(arcs_anchor, list):
    prev_arc_data = next(
        (a for a in reversed(arcs_anchor) if isinstance(a, dict) and a.get("arc_no") == clean_arc_no - 1),
        None,
    )
elif isinstance(arcs_anchor, dict):
    prev_arc_data = arcs_anchor.get(f"arc_{clean_arc_no - 1}")
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [MEDIUM] modules/domain/agents/analyst.py:1008 — dict `tactical_doc` 경고 주입 시 문자열 결합 크래시

**문제**: `tactical_doc`가 dict일 수 있는 경로를 함수가 직접 허용하면서, 경고 주입에서는 문자열 결합을 강제한다. 이슈가 발생한 경우 `TypeError`로 종료될 수 있다.

**문제 코드**:
```python
tactical_doc = final_arc_data.get("tactical_doc", "")
if tactical_doc:
    doc_continuity = self._validate_tactical_doc_continuity_v60(tactical_doc, final_ep_count)
    if doc_continuity["issues"]:
        warning_text = "\n\n⚠️ [V60 CONTINUITY WARNING]:\n"
        ...
        final_arc_data["tactical_doc"] = warning_text + tactical_doc
```

**호출 체인**: `plan_single_arc_v20()` → `_validate_tactical_doc_continuity_v60()`(dict 허용) → 이슈 분기에서 경고 주입 (`modules/domain/agents/analyst.py:996`, `modules/domain/agents/analyst.py:998`, `modules/domain/agents/analyst.py:1008`)

**수정 제안**:
```python
if isinstance(tactical_doc, dict):
    tactical_doc_text = tactical_doc.get("tactical_doc", "") or json.dumps(tactical_doc, ensure_ascii=False)
else:
    tactical_doc_text = str(tactical_doc) if tactical_doc is not None else ""
...
final_arc_data["tactical_doc"] = warning_text + tactical_doc_text
```

**확신도**: MEDIUM

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 26 완료

## Round 27 — modules/domain/agents/analyst_prompts.py + modules/domain/agents/analyst_prompt_api.py

### 진행 통계 업데이트
- 총 발견: 14건 (CRITICAL: 0, HIGH: 11, MEDIUM: 3)
- 라운드 진행: 27/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/analyst_prompts.py:7` `POST_STITCH_REPAIR_PROMPT` — Arc 접합부 용접 프롬프트 상수.
- `modules/domain/agents/analyst_prompts.py:33` `ENRICH_BLOCK_PROMPT_V30` — Block 농축 프롬프트 상수.
- `modules/domain/agents/analyst_prompts.py:611` `def get_recovery_prompt() -> str` — 복구 프롬프트 팩토리.
- `modules/domain/agents/analyst_prompts.py:696` `def get_surgery_prompt(*, prev_arc_json: str, curr_arc_json: str, next_arc_json: str, feedback: str) -> str` — ARC_RECONSTRUCTION 수술 프롬프트.
- `modules/domain/agents/analyst_prompts.py:742` `def get_calibration_prompt(*, calibration_msg: str, current_hud_json: str, arc_tactical: str) -> str` — 캘리브레이션 프롬프트.
- `modules/domain/agents/analyst_prompt_api.py:10` `def _load_prompt(key: str, fallback: str, **kwargs) -> str` — PromptLoader 우선 로딩 + fallback 포맷.
- `modules/domain/agents/analyst_prompt_api.py:44` `def get_plan_arc_prompt_v25(**kwargs) -> str` — Arc 템플릿 raw/legacy fallback.
- `modules/domain/agents/analyst_prompt_api.py:86` `def get_calibration_prompt(*, calibration_msg: str, current_hud_json: str, arc_tactical: str) -> str` — API 래퍼.

### 5-D. 읽기 증명
1. 마지막 함수:
- `modules/domain/agents/analyst_prompts.py`: `def get_calibration_prompt(...) -> str` (`modules/domain/agents/analyst_prompts.py:742`)
- `modules/domain/agents/analyst_prompt_api.py`: `def get_calibration_prompt(...) -> str` (`modules/domain/agents/analyst_prompt_api.py:86`)
2. 특징 문자열:
- `"""[V65] Analyst 프롬프트 템플릿 외부화."""` (`modules/domain/agents/analyst_prompts.py:1`)
- `# Return raw template to avoid brace-collapse across multi-pass formatting.` (`modules/domain/agents/analyst_prompt_api.py:45`)
3. import 목록:
- `from modules.core.prompt_loader import PromptLoader` (`modules/domain/agents/analyst_prompt_api.py:3`)
- `from . import analyst_prompts as legacy` (`modules/domain/agents/analyst_prompt_api.py:5`)
- `analyst_prompts.py`는 import 없이 템플릿 상수/팩토리 함수 중심 구성.

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `raw = _PROMPT_LOADER.get_raw("analyst", "PLAN_ARC_PROMPT_V25"); if raw is not None: return raw` (`modules/domain/agents/analyst_prompt_api.py:46`)
- 호출자: `adjusted_prompt_tpl = get_plan_arc_prompt_v25()` (`modules/domain/agents/analyst.py:746`)
- 상류/하류 컨텍스트:
- 상류: raw 템플릿은 변수 치환 없는 원문.
- 하류: 호출측에서 별도 `format_map` 수행 (`modules/domain/agents/analyst.py:764`, `modules/domain/agents/analyst.py:802`)
- 실패 시나리오: 외부 호출자가 `get_plan_arc_prompt_v25(**kwargs)`에 즉시 치환을 기대하면 placeholder가 남을 수 있음.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `except Exception: return fallback` (`modules/domain/agents/analyst_prompt_api.py:23`)
- 호출자: `_load_prompt(...)` 공통 경로 (`modules/domain/agents/analyst_prompt_api.py:27`, `modules/domain/agents/analyst_prompt_api.py:36`, `modules/domain/agents/analyst_prompt_api.py:40`)
- 상류/하류 컨텍스트:
- 상류: `fallback.format_map(...)` 예외 발생 가능.
- 하류: 예외 시 미치환 fallback 원문 반환.
- 실패 시나리오: 템플릿 치환 실패가 조용히 숨겨져 운영 중 placeholder 누락 탐지가 어려워짐.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `"[제 {ep_start}+1화 전술 설계]"` (`modules/domain/agents/analyst_prompts.py:477`)
- 호출자: `PLAN_ARC_PROMPT_V25` 템플릿 렌더링 경로 (`modules/domain/agents/analyst.py:764`, `modules/domain/agents/analyst.py:802`)
- 상류/하류 컨텍스트:
- 상류: 템플릿 치환은 문자열 치환만 수행.
- 하류: LLM이 예시 텍스트를 그대로 모방할 수 있음.
- 실패 시나리오: 산술이 계산되지 않은 표현(`{ep_start}+1`)이 출력 예시로 남아 회차 포맷 혼선을 유발할 수 있음.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 27 완료

## Round 28 — modules/domain/agents/arc_corrector.py

### 진행 통계 업데이트
- 총 발견: 14건 (CRITICAL: 0, HIGH: 11, MEDIUM: 3)
- 라운드 진행: 28/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/arc_corrector.py:81` `class ArcCorrector(BaseAgent)` — Stage2 Arc 부분 수정기.
- `modules/domain/agents/arc_corrector.py:94` `def can_correct(self, issues: list[dict]) -> tuple[bool, list[dict], list[dict]]` — 수정 가능성 분류.
- `modules/domain/agents/arc_corrector.py:125` `def correct(self, arc: dict, issues: list[dict], prev_arcs: list[dict] = None) -> tuple[dict | None, dict]` — 이슈 기반 부분 수정 실행.
- `modules/domain/agents/arc_corrector.py:465` `def _replace_episode_section(self, tactical: str, ep_num: int, new_content: str) -> str | None` — 화 섹션 교체.
- `modules/domain/agents/arc_corrector.py:495` `def _validate_change_ratio(self, original: dict, corrected: dict) -> bool` — 변경 비율 검증.
- `modules/domain/agents/arc_corrector.py:531` `def _generate_joint_docs_from_tactical(self, tactical: str, arc: dict) -> dict` — joint_docs 추출.
- `modules/domain/agents/arc_corrector.py:576` `def create_arc_corrector(context, client, model_tier: str = "gemini-2.5-flash")` — 팩토리 함수.

### 5-D. 읽기 증명
1. 마지막 함수: `def create_arc_corrector(...)` (`modules/domain/agents/arc_corrector.py:576`)
2. 특징 문자열: `logging.info(f"⚠️ [Corrector] 변경 범위 초과 (>{self.max_change_ratio * 100}%) - 원본 복원")` (`modules/domain/agents/arc_corrector.py:191`)
3. import 목록:
- `from .base_agent import BaseAgent` (`modules/domain/agents/arc_corrector.py:23`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `diff_len = abs(len(corrected_str) - original_len)` + `change_ratio = diff_len / max(original_len, 1)` (`modules/domain/agents/arc_corrector.py:502`, `modules/domain/agents/arc_corrector.py:505`)
- 호출자: `correct()`의 변경 범위 검증 (`modules/domain/agents/arc_corrector.py:190`)
- 상류/하류 컨텍스트:
- 상류: `original_str`/`corrected_str`는 JSON 문자열 길이 기반.
- 하류: 임계치 초과 시 수정 전체 폐기 (`modules/domain/agents/arc_corrector.py:193`)
- 실패 시나리오: 길이 변화가 작아도 의미 변경이 큰 수정을 통과시킬 수 있음.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `original_eps = len(re.findall(r"\[제\s*\d+\s*화", original_tactical))` (`modules/domain/agents/arc_corrector.py:522`)
- 호출자: `_validate_structure_preserved()` (`modules/domain/agents/arc_corrector.py:508`)
- 상류/하류 컨텍스트:
- 상류: tactical 헤더 포맷은 브라켓 없는 변형도 존재.
- 하류: 화 수 감소 여부 판단 (`modules/domain/agents/arc_corrector.py:526`)
- 실패 시나리오: 헤더 변형 포맷에서 화 수 계산이 0으로 잡혀 구조 손상 검출이 약해질 수 있음.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `def _correct_generic_issue(...): result = {"success": False, "reason": "범용 수정 미지원"}` (`modules/domain/agents/arc_corrector.py:440`)
- 호출자: `_correct_single_issue()`의 기본 분기 (`modules/domain/agents/arc_corrector.py:231`)
- 상류/하류 컨텍스트:
- 상류: 키워드 매칭 실패 이슈는 범용 분기로 이동.
- 하류: `correct()`에서 실패 로그만 남기고 수정 중단 (`modules/domain/agents/arc_corrector.py:180`)
- 실패 시나리오: 이슈 표현 변형에 취약하여 수정 가능한 케이스도 미수정으로 종료될 수 있음.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 28 완료

## Round 29 — modules/domain/agents/arc_critic.py + modules/domain/agents/arc_ensemble.py

### 진행 통계 업데이트
- 총 발견: 14건 (CRITICAL: 0, HIGH: 11, MEDIUM: 3)
- 라운드 진행: 29/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/arc_critic.py:123` `class ArcCritic(BaseAgent)` — Arc 즉시 비평/자동수정.
- `modules/domain/agents/arc_critic.py:135` `def critique(self, generated_arc: dict, prev_arcs: list[dict], constraints: str = "") -> tuple[dict, dict]` — 비평 + auto_fix 적용.
- `modules/domain/agents/arc_critic.py:219` `def _apply_auto_fixes(self, arc: dict, critique: dict) -> dict` — 비평 결과 기반 자동 수정.
- `modules/domain/agents/arc_ensemble.py:58` `class ArcEnsembleGenerator(BaseAgent)` — 다중 전략 병렬 Arc 생성기.
- `modules/domain/agents/arc_ensemble.py:77` `def generate_ensemble(self, ..., retry: int = 0) -> tuple[dict | None, list[dict]]` — 후보 생성/평가/선택.
- `modules/domain/agents/arc_ensemble.py:287` `def _generate_single(self, ..., retry: int = 0) -> dict | None` — 단일 전략 생성.
- `modules/domain/agents/arc_ensemble.py:401` `def _evaluate_candidate(self, candidate: dict, prev_arc_context: str, constraint_block: str) -> tuple[int, list[str]]` — 후보 점수화.
- `modules/domain/agents/arc_ensemble.py:502` `def _ensure_required_fields(self, result: dict, arc_no: int, ep_start: int, ep_end: int) -> dict` — 필수 필드 보정.

### 5-D. 읽기 증명
1. 마지막 함수:
- `modules/domain/agents/arc_critic.py`: `def create_arc_critic(...)` (`modules/domain/agents/arc_critic.py:365`)
- `modules/domain/agents/arc_ensemble.py`: `def create_ensemble_generator(...)` (`modules/domain/agents/arc_ensemble.py:688`)
2. 특징 문자열:
- `logging.warning(f"⚠️ [Critic] 비평 오류: {str(e)[:50]}")` (`modules/domain/agents/arc_critic.py:172`)
- `logging.warning("🏆 [Ensemble] 후보 비교:")` (`modules/domain/agents/arc_ensemble.py:260`)
3. import 목록:
- `from modules.core.arc_summary_utils import generate_prev_arc_summary` (`modules/domain/agents/arc_critic.py:16`)
- `from modules.core.constants import Stage2Limits` (`modules/domain/agents/arc_ensemble.py:21`)
- `from modules.core.prompt_loader import PromptLoader` (`modules/domain/agents/arc_ensemble.py:22`)
- `from .base_agent import BaseAgent` (`modules/domain/agents/arc_critic.py:18`, `modules/domain/agents/arc_ensemble.py:24`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `sc = result["state_changes"]` 후 `sc["timeline"] = ...` (`modules/domain/agents/arc_ensemble.py:544`, `modules/domain/agents/arc_ensemble.py:546`)
- 호출자: `_generate_single()`에서 필수 필드 보정 (`modules/domain/agents/arc_ensemble.py:389`)
- 상류/하류 컨텍스트:
- 상류: LLM 출력의 `state_changes` 타입은 비정형.
- 하류: 예외 발생 시 `_generate_single`이 `None` 반환 (`modules/domain/agents/arc_ensemble.py:399`)
- 실패 시나리오: `state_changes`가 list/str이면 후보가 조용히 폐기될 수 있음.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `items = fixed.get("state_constraints", {}).get("items_acquired", [])` + `items.remove(item_to_remove)` (`modules/domain/agents/arc_critic.py:247`, `modules/domain/agents/arc_critic.py:250`)
- 호출자: `critique()` 내부 `_apply_auto_fixes()` (`modules/domain/agents/arc_critic.py:167`)
- 상류/하류 컨텍스트:
- 상류: `items_acquired`가 list가 아닐 가능성 존재.
- 하류: 예외 시 `critique()` 전체가 fallback 비평으로 전환 (`modules/domain/agents/arc_critic.py:172`, `modules/domain/agents/arc_critic.py:174`)
- 실패 시나리오: 비표준 타입에서 auto_fix 단계 예외로 LLM 비평 결과가 폐기될 수 있음.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `return "\n".join(str(v) for v in tactical.values() if v)` (`modules/domain/agents/arc_ensemble.py:588`)
- 호출자: `generate_ensemble()` 후보 정규화 (`modules/domain/agents/arc_ensemble.py:208`)
- 상류/하류 컨텍스트:
- 상류: dict tactical_doc를 평탄화.
- 하류: 분량/화수 평가 및 최종 후보 선택 (`modules/domain/agents/arc_ensemble.py:210`, `modules/domain/agents/arc_ensemble.py:495`)
- 실패 시나리오: 구조가 무시된 평탄화 문자열이 평가를 통과해 품질 저하 후보가 선택될 수 있음.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 29 완료

## Round 30 — modules/domain/agents/arc_draft_validator.py

### 진행 통계 업데이트
- 총 발견: 16건 (CRITICAL: 0, HIGH: 13, MEDIUM: 3)
- 라운드 진행: 30/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/arc_draft_validator.py:28` `class ArcDraftValidator` — Stage2 Arc 초안 사전 검증기.
- `modules/domain/agents/arc_draft_validator.py:70` `def validate(self, arc: dict, prev_arcs: list[dict], constraint_block: str = "", state_tracker=None) -> dict[str, Any]` — 종합 검증 엔트리포인트.
- `modules/domain/agents/arc_draft_validator.py:287` `def _validate_injury_continuity(self, arc: dict, prev_arc: dict) -> dict` — 부상 연속성 점검.
- `modules/domain/agents/arc_draft_validator.py:355` `def _validate_tactical_doc(self, arc: dict) -> dict` — 전술 문서 분량/구조 점검.
- `modules/domain/agents/arc_draft_validator.py:495` `def _validate_state_checkpoints(self, episode_sections: dict[int, str], arc: dict) -> dict` — 화간 상태 체크포인트 점검.
- `modules/domain/agents/arc_draft_validator.py:634` `def _extract_episode_sections(self, tactical: str, ep_start: int, ep_count: int) -> dict[int, str]` — 화 섹션 추출.
- `modules/domain/agents/arc_draft_validator.py:856` `def create_draft_validator() -> ArcDraftValidator` — 팩토리 함수.

### 5-D. 읽기 증명
1. 마지막 함수: `def create_draft_validator() -> ArcDraftValidator` (`modules/domain/agents/arc_draft_validator.py:856`)
2. 특징 문자열: `logging.warning(f"💀 [V60.94] REJECT: Arc {death_arc}에서 사망한 '{npc_name}'이 Arc {arc_no}에서 등장!")` (`modules/domain/agents/arc_draft_validator.py:851`)
3. import 목록:
- `from modules.core.constants import Stage2Limits` (`modules/domain/agents/arc_draft_validator.py:25`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `tactical = arc.get("tactical_doc", "")` + `has_recovery = any(kw in tactical[:1000] for kw in ["회복", "치료", "조식", "휴식", "요양"])` (`modules/domain/agents/arc_draft_validator.py:307`, `modules/domain/agents/arc_draft_validator.py:308`)
- 호출자: `validate()` → `_validate_injury_continuity()` (`modules/domain/agents/arc_draft_validator.py:135`)
- 상류/하류 컨텍스트:
- 상류: 같은 파일에 `_safe_tactical()`이 dict tactical 처리 로직 제공 (`modules/domain/agents/arc_draft_validator.py:58`)
- 하류: 검증 결과 penalty/warnings 누적 (`modules/domain/agents/arc_draft_validator.py:311`)
- 실패 시나리오: `tactical_doc`가 dict일 때 slice 접근으로 TypeError.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `ep_count = arc.get("ep_count", 5)` + `min_length = ep_count * Stage2Limits.MIN_CHARS_PER_EPISODE` (`modules/domain/agents/arc_draft_validator.py:387`, `modules/domain/agents/arc_draft_validator.py:390`)
- 호출자: `validate()` → `_validate_tactical_doc()` (`modules/domain/agents/arc_draft_validator.py:146`)
- 상류/하류 컨텍스트:
- 상류: `ep_count` 타입 정규화 없음.
- 하류: `if length < warn_length:` 비교 (`modules/domain/agents/arc_draft_validator.py:393`)
- 실패 시나리오: `ep_count`가 문자열이면 `warn_length`가 문자열이 되어 int 비교에서 TypeError.
- 판정: BUG.

3. 위험 지점
- 코드 원문: `for item in current_items: ... if self._is_same_item(item, prev_item):` (`modules/domain/agents/arc_draft_validator.py:249`, `modules/domain/agents/arc_draft_validator.py:253`)
- 호출자: `validate()` → `_validate_duplicate_acquisition()` (`modules/domain/agents/arc_draft_validator.py:121`)
- 상류/하류 컨텍스트:
- 상류: `current_items`는 list 원소 타입 정규화 없음 (`modules/domain/agents/arc_draft_validator.py:235`)
- 하류: `_is_same_item()`는 `.strip()` 호출 전제 (`modules/domain/agents/arc_draft_validator.py:752`)
- 실패 시나리오: dict 원소 혼입 시 문자열 API 호출에서 예외 가능.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/domain/agents/arc_draft_validator.py:308 — dict `tactical_doc`에서 슬라이싱 TypeError

**문제**: `_validate_injury_continuity()`가 `tactical_doc`를 문자열 전제(`tactical[:1000]`)로 사용한다. 하지만 파일 내 다른 경로는 dict tactical을 허용하고 있어 타입 충돌로 검증 단계 크래시가 발생할 수 있다.

**문제 코드**:
```python
tactical = arc.get("tactical_doc", "")
has_recovery = any(kw in tactical[:1000] for kw in ["회복", "치료", "조식", "휴식", "요양"])
```

**호출 체인**: `validate()` → `_validate_injury_continuity()` (`modules/domain/agents/arc_draft_validator.py:135`, `modules/domain/agents/arc_draft_validator.py:287`)

**수정 제안**:
```python
tactical = self._safe_tactical(arc)
has_recovery = any(kw in tactical[:1000] for kw in ["회복", "치료", "조식", "휴식", "요양"])
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [HIGH] modules/domain/agents/arc_draft_validator.py:390 — `ep_count` 비정수 입력 시 분량 검증 타입 크래시

**문제**: `_validate_tactical_doc()`에서 `ep_count`를 정수로 정규화하지 않고 곱셈/비교에 사용한다. 문자열 입력이 들어오면 `warn_length` 타입이 문자열이 되어 int 비교에서 실패한다.

**문제 코드**:
```python
ep_count = arc.get("ep_count", 5)
min_length = ep_count * Stage2Limits.MIN_CHARS_PER_EPISODE
warn_length = ep_count * 400
if length < warn_length:
    ...
```

**호출 체인**: `validate()` → `_validate_tactical_doc()` (`modules/domain/agents/arc_draft_validator.py:146`, `modules/domain/agents/arc_draft_validator.py:355`)

**수정 제안**:
```python
ep_count = arc.get("ep_count", 5)
try:
    ep_count = int(ep_count)
except (ValueError, TypeError):
    ep_count = 5
min_length = ep_count * Stage2Limits.MIN_CHARS_PER_EPISODE
warn_length = ep_count * 400
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 30 완료

## Round 31 — modules/domain/agents/four_phase_arc_generator.py

### 진행 통계 업데이트
- 총 발견: 18건 (CRITICAL: 0, HIGH: 15, MEDIUM: 3)
- 라운드 진행: 31/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/four_phase_arc_generator.py:31` `class FourPhaseArcGenerator(BaseAgent)` — Stage2 FourPhase Arc 생성 파이프라인.
- `modules/domain/agents/four_phase_arc_generator.py:59` `def _determine_ep_count(self, curr_block: dict, arc_no: int, prev_arcs: list[dict]) -> tuple[int, str]` — 화수 동적 결정.
- `modules/domain/agents/four_phase_arc_generator.py:113` `def generate(self, arc_no: int, ep_start: int, vol_strategy: str, curr_block: dict, prev_arcs: list[dict], assets: dict = None, max_internal_retries: int = 2, protagonist_name: str = "주인공", director_feedback: str = "", entity_registry: dict = None, state_tracker=None, vector_context: str = "") -> tuple[dict | None, dict]` — 메인 생성 루프.
- `modules/domain/agents/four_phase_arc_generator.py:393` `def patch_arc_with_feedback(self, original_arc: dict, director_feedback: str, attempt_number: int, arc_no: int, ep_start: int, vol_strategy: str, curr_block: dict, prev_arcs: list[dict], assets: dict = None, protagonist_name: str = "주인공", state_tracker=None) -> tuple[dict | None, dict]` — Patch Mode 부분 수정.
- `modules/domain/agents/four_phase_arc_generator.py:553` `def _generate_prev_context(self, prev_arcs: list[dict], preflight_result: dict) -> str` — 이전 Arc 컨텍스트 조립.
- `modules/domain/agents/four_phase_arc_generator.py:682` `def _auto_sanitize_injuries(self, arc: dict) -> dict` — injury 자동 세정.
- `modules/domain/agents/four_phase_arc_generator.py:741` `def create_four_phase_generator(context, client, model_tier: str = "gemini-2.5-pro")` — 팩토리 함수.

### 5-D. 읽기 증명
1. 마지막 함수: `def create_four_phase_generator(context, client, model_tier: str = "gemini-2.5-pro")` (`modules/domain/agents/four_phase_arc_generator.py:741`)
2. 특징 문자열: `logging.warning(f"⚠️ [Patch Mode] Arc {arc_no} 패치 검증 실패 → 폴백 필요")` (`modules/domain/agents/four_phase_arc_generator.py:549`)
3. import 목록:
- `from modules.core.constants import ContextLimits, Stage2Limits` (`modules/domain/agents/four_phase_arc_generator.py:21`)
- `from .arc_ensemble import ArcEnsembleGenerator` (`modules/domain/agents/four_phase_arc_generator.py:23`)
- `from .base_agent import BaseAgent, _get_sub_component_models` (`modules/domain/agents/four_phase_arc_generator.py:24`)
- `from .preflight_checker import PreflightChecker` (`modules/domain/agents/four_phase_arc_generator.py:27`)
- `from .unified_arc_validator import UnifiedArcValidator` (`modules/domain/agents/four_phase_arc_generator.py:28`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `_pre_items.update(i.strip() for i in _acq if i)` (`modules/domain/agents/four_phase_arc_generator.py:181`)
- 호출자: `Stage2Preflight.run()`에서 `self.ctx.agents["four_phase"].generate(...)` 호출 (`modules/core/stage2_preflight.py:512`) 후 `generate()` 내부 사전 수집 루프 (`modules/domain/agents/four_phase_arc_generator.py:178`).
- 상류/하류 컨텍스트:
- 상류: `_acq = _prev.get("state_constraints", {}).get("items_acquired", [])` (`modules/domain/agents/four_phase_arc_generator.py:179`)
- 하류: `self.validator.validate(..., pre_collected_items=_pre_items, ...)` (`modules/domain/agents/four_phase_arc_generator.py:328`, `modules/domain/agents/four_phase_arc_generator.py:333`)
- 실패 시나리오: `items_acquired`가 dict 원소를 포함하면 `.strip()`에서 `AttributeError`로 생성 파이프라인 중단.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `_pre_grants.update(g.strip() for g in _grt if g)` (`modules/domain/agents/four_phase_arc_generator.py:184`) / 동일 패턴 재사용 (`modules/domain/agents/four_phase_arc_generator.py:527`)
- 호출자: `generate()` 본 경로 (`modules/domain/agents/four_phase_arc_generator.py:178`) + `patch_arc_with_feedback()` 검증 경로 (`modules/domain/agents/four_phase_arc_generator.py:519`)
- 상류/하류 컨텍스트:
- 상류: `_grt = _prev.get("state_constraints", {}).get("grants_received", [])` (`modules/domain/agents/four_phase_arc_generator.py:182`, `modules/domain/agents/four_phase_arc_generator.py:525`)
- 하류: `self.validator.validate(..., pre_collected_grants=_pre_grants, ...)` (`modules/domain/agents/four_phase_arc_generator.py:334`, `modules/domain/agents/four_phase_arc_generator.py:535`)
- 실패 시나리오: 문자열이 아닌 grant 원소(dict 등) 유입 시 `.strip()` 예외로 retry/pipeline 실패.
- 판정: BUG.

3. 위험 지점
- 코드 원문: `_arc_history_lines.append(f"━━━ Arc {_pa_no} (제{_pa_ep_s}화~제{_pa_ep_e}화) ━━━\n{_pa_td}")` (`modules/domain/agents/four_phase_arc_generator.py:634`)
- 호출자: `_generate_prev_context()` (`modules/domain/agents/four_phase_arc_generator.py:553`)
- 상류/하류 컨텍스트:
- 상류: `for _pa in prev_arcs[_prev_start:]:` (`modules/domain/agents/four_phase_arc_generator.py:624`)
- 하류: `if len(_full_history) > ContextLimits.MAX_CONTEXT_CHARS: _full_history = _full_history[: ContextLimits.MAX_CONTEXT_CHARS] + ...` (`modules/domain/agents/four_phase_arc_generator.py:638`)
- 실패 시나리오: 컨텍스트 비대화 위험은 있으나 상한 절삭 가드가 존재.
- 판정: 안전(가드 존재).

### 5-C. 발견된 버그
### [HIGH] modules/domain/agents/four_phase_arc_generator.py:181 — pre_collected_items 수집 시 dict 원소에서 `.strip()` 크래시

**문제**: 이전 Arc의 `items_acquired`가 dict 원소를 포함하면 `.strip()` 호출로 `AttributeError`가 발생한다.

**문제 코드**:
```python
_acq = _prev.get("state_constraints", {}).get("items_acquired", [])
if isinstance(_acq, list):
    _pre_items.update(i.strip() for i in _acq if i)
```

**호출 체인**: `Stage2Preflight.run()` (`modules/core/stage2_preflight.py:512`) → `generate()` (`modules/domain/agents/four_phase_arc_generator.py:113`) → pre-collect 루프 (`modules/domain/agents/four_phase_arc_generator.py:178`)

**수정 제안**:
```python
if isinstance(_acq, list):
    _pre_items.update(
        (i.get("name", i.get("item", "")) if isinstance(i, dict) else str(i).strip())
        for i in _acq
        if i
    )
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [HIGH] modules/domain/agents/four_phase_arc_generator.py:184 — pre_collected_grants 수집 시 비문자열 원소 예외

**문제**: `grants_received` 원소를 문자열로 단정하고 `.strip()`을 호출한다. 비문자열 원소(dict 등) 유입 시 예외 발생.

**문제 코드**:
```python
_grt = _prev.get("state_constraints", {}).get("grants_received", [])
if isinstance(_grt, list):
    _pre_grants.update(g.strip() for g in _grt if g)
```

**호출 체인**: `generate()` (`modules/domain/agents/four_phase_arc_generator.py:113`) 및 `patch_arc_with_feedback()` (`modules/domain/agents/four_phase_arc_generator.py:393`) → pre-collect 루프 (`modules/domain/agents/four_phase_arc_generator.py:182`, `modules/domain/agents/four_phase_arc_generator.py:525`)

**수정 제안**:
```python
if isinstance(_grt, list):
    _pre_grants.update(
        (g.get("grant", g.get("name", "")) if isinstance(g, dict) else str(g).strip())
        for g in _grt
        if g
    )
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 31 완료

## Round 32 — modules/domain/agents/state_locked_arc_generator.py

### 진행 통계 업데이트
- 총 발견: 21건 (CRITICAL: 0, HIGH: 18, MEDIUM: 3)
- 라운드 진행: 32/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/state_locked_arc_generator.py:160` `class StateLockedArcGenerator(BaseAgent)` — 상태 잠금 기반 Arc 생성기.
- `modules/domain/agents/state_locked_arc_generator.py:175` `def generate(self, arc_no: int, ep_start: int, prev_arc: dict | None, arc_direction: str, episode_beats: list[str], assets: dict = None, protagonist_name: str = "주인공") -> tuple[dict | None, dict]` — 메인 생성 루프.
- `modules/domain/agents/state_locked_arc_generator.py:301` `def _lock_start_state(self, prev_arc: dict | None) -> dict` — 시작 상태 잠금.
- `modules/domain/agents/state_locked_arc_generator.py:345` `def _generate_episode(self, ep_num: int, start_state: dict, arc_direction: str, episode_beat: str, prev_episode: dict | None = None) -> dict | None` — 단일 화 생성.
- `modules/domain/agents/state_locked_arc_generator.py:428` `def _extract_state(self, episode_text: str, start_state: dict) -> dict` — 종료 상태 추출.
- `modules/domain/agents/state_locked_arc_generator.py:475` `def _synthesize_arc(self, arc_no: int, ep_start: int, ep_end: int, episodes: list[dict], start_state: dict, end_state: dict) -> dict | None` — Arc 통합.
- `modules/domain/agents/state_locked_arc_generator.py:569` `def create_state_locked_generator(context, client, model_tier: str = "gemini-3-pro-preview")` — 팩토리 함수.

### 5-D. 읽기 증명
1. 마지막 함수: `def create_state_locked_generator(context, client, model_tier: str = "gemini-3-pro-preview")` (`modules/domain/agents/state_locked_arc_generator.py:569`)
2. 특징 문자열: `logging.info(f"✅ [V60.14] Arc {arc_no} 생성 완료!")` (`modules/domain/agents/state_locked_arc_generator.py:297`)
3. import 목록:
- `from .base_agent import BaseAgent` (`modules/domain/agents/state_locked_arc_generator.py:16`)
- 프로젝트 내부 import는 위 1개만 존재(파일 전수 확인).

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `"equipment": current_state.get("equipment", []) + end_state.get("items_acquired", []),` (`modules/domain/agents/state_locked_arc_generator.py:254`)
- 호출자: `generate()`의 화별 상태 전이 루프 (`modules/domain/agents/state_locked_arc_generator.py:175`, `modules/domain/agents/state_locked_arc_generator.py:218`)
- 상류/하류 컨텍스트:
- 상류: `end_state = self._extract_state(episode["text"], current_state)` (`modules/domain/agents/state_locked_arc_generator.py:237`)
- 하류: 다음 화 `_generate_episode(..., start_state=current_state, ...)` (`modules/domain/agents/state_locked_arc_generator.py:223`)
- 실패 시나리오: `items_acquired`가 문자열/딕셔너리면 list 덧셈에서 TypeError.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `"items_acquired": list(set(all_acquired)),` / `"items_consumed": list(set(all_consumed)),` (`modules/domain/agents/state_locked_arc_generator.py:528`, `modules/domain/agents/state_locked_arc_generator.py:529`) 및 `"item_consumption": list(set(all_consumed)),` (`modules/domain/agents/state_locked_arc_generator.py:539`)
- 호출자: `generate()` → `_synthesize_arc()` (`modules/domain/agents/state_locked_arc_generator.py:269`, `modules/domain/agents/state_locked_arc_generator.py:475`)
- 상류/하류 컨텍스트:
- 상류: `all_acquired.extend(ep.get("end_state", {}).get("items_acquired", []))` (`modules/domain/agents/state_locked_arc_generator.py:490`)
- 하류: Arc 결과 dict 반환 (`modules/domain/agents/state_locked_arc_generator.py:506`)
- 실패 시나리오: 리스트에 dict 원소가 있으면 set 변환에서 `unhashable type: 'dict'`.
- 판정: BUG.

3. 위험 지점
- 코드 원문: `equipment_str = ", ".join(start_state.get("equipment", [])) or "없음"` (`modules/domain/agents/state_locked_arc_generator.py:359`)
- 호출자: `generate()` → `_generate_episode()` (`modules/domain/agents/state_locked_arc_generator.py:223`, `modules/domain/agents/state_locked_arc_generator.py:345`)
- 상류/하류 컨텍스트:
- 상류: `start_state["equipment"]`는 `_lock_start_state()`에서 이전 Arc 종료 장비를 그대로 계승 (`modules/domain/agents/state_locked_arc_generator.py:337`)
- 하류: `EPISODE_TEMPLATE.format(..., start_equipment=...)` (`modules/domain/agents/state_locked_arc_generator.py:365`)
- 실패 시나리오: 장비 리스트가 dict 원소를 포함하면 `join`에서 TypeError.
- 판정: BUG.

### 5-C. 발견된 버그
### [HIGH] modules/domain/agents/state_locked_arc_generator.py:254 — 상태 전이 시 `items_acquired` 타입 미정규화

**문제**: `items_acquired`를 리스트로 강제하지 않고 list 덧셈에 사용한다. 비리스트 입력 시 다음 화 상태 전이에서 크래시한다.

**문제 코드**:
```python
current_state = {
    "location": end_state["location"],
    "energy": end_state["energy"],
    "injuries": end_state["injuries"],
    "equipment": current_state.get("equipment", []) + end_state.get("items_acquired", []),
}
```

**호출 체인**: `generate()` (`modules/domain/agents/state_locked_arc_generator.py:175`) → `_extract_state()` (`modules/domain/agents/state_locked_arc_generator.py:428`) → 상태 전이 (`modules/domain/agents/state_locked_arc_generator.py:254`)

**수정 제안**:
```python
acquired = end_state.get("items_acquired", [])
if not isinstance(acquired, list):
    acquired = [acquired] if acquired else []
current_state["equipment"] = list(current_state.get("equipment", [])) + acquired
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [HIGH] modules/domain/agents/state_locked_arc_generator.py:528 — set 변환 시 dict 원소로 unhashable 크래시

**문제**: Arc 통합 시 `all_acquired`/`all_consumed`를 바로 `set()`으로 중복 제거한다. 원소에 dict가 있으면 TypeError가 발생한다.

**문제 코드**:
```python
"items_acquired": list(set(all_acquired)),
"items_consumed": list(set(all_consumed)),
...
"item_consumption": list(set(all_consumed)),
```

**호출 체인**: `generate()` (`modules/domain/agents/state_locked_arc_generator.py:175`) → `_synthesize_arc()` (`modules/domain/agents/state_locked_arc_generator.py:475`) → 결과 dict 생성 (`modules/domain/agents/state_locked_arc_generator.py:515`)

**수정 제안**:
```python
norm_acquired = [a.get("name", a.get("item", "")) if isinstance(a, dict) else str(a) for a in all_acquired if a]
norm_consumed = [c.get("name", c.get("item", "")) if isinstance(c, dict) else str(c) for c in all_consumed if c]
"items_acquired": list(dict.fromkeys(norm_acquired)),
"items_consumed": list(dict.fromkeys(norm_consumed)),
"item_consumption": list(dict.fromkeys(norm_consumed)),
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [HIGH] modules/domain/agents/state_locked_arc_generator.py:359 — 장비 join 시 dict 원소 타입 크래시

**문제**: 장비 리스트를 문자열 join할 때 원소 타입을 문자열로 정규화하지 않는다. dict 원소 포함 시 에피소드 생성 단계에서 즉시 실패한다.

**문제 코드**:
```python
equipment_str = ", ".join(start_state.get("equipment", [])) or "없음"
```

**호출 체인**: `generate()` (`modules/domain/agents/state_locked_arc_generator.py:175`) → `_generate_episode()` (`modules/domain/agents/state_locked_arc_generator.py:345`) → prompt format (`modules/domain/agents/state_locked_arc_generator.py:361`)

**수정 제안**:
```python
equipment = start_state.get("equipment", [])
if isinstance(equipment, list):
    equipment_str = ", ".join(str(e) for e in equipment if e) or "없음"
else:
    equipment_str = str(equipment) if equipment else "없음"
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 32 완료

## Round 33 — modules/domain/agents/unified_arc_validator.py + modules/domain/agents/preflight_checker.py

### 진행 통계 업데이트
- 총 발견: 24건 (CRITICAL: 0, HIGH: 21, MEDIUM: 3)
- 라운드 진행: 33/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/unified_arc_validator.py:98` `class UnifiedArcValidator(BaseAgent)` — Stage2 통합 검증기(Python + LLM).
- `modules/domain/agents/unified_arc_validator.py:109` `def validate(self, arc: dict, prev_arcs: list[dict], constraints: str = "", state_tracker=None, pre_collected_items: set | None = None, pre_collected_grants: set | None = None) -> tuple[str, dict]` — 최종 검증 엔트리포인트.
- `modules/domain/agents/unified_arc_validator.py:224` `def _check_length(self, arc: dict) -> list[dict]` — 분량/화구분 체크.
- `modules/domain/agents/unified_arc_validator.py:497` `def _python_validate(self, arc: dict, prev_arcs: list[dict], state_tracker=None, pre_collected_items: set | None = None, pre_collected_grants: set | None = None) -> dict` — Python 체크 조합.
- `modules/domain/agents/unified_arc_validator.py:525` `def _llm_validate(self, arc: dict, prev_arcs: list[dict], constraints: str, python_result: dict) -> dict` — LLM 문맥 검증.
- `modules/domain/agents/preflight_checker.py:114` `class PreflightChecker(BaseAgent)` — 생성 전 제약 맵 분석기.
- `modules/domain/agents/preflight_checker.py:126` `def analyze(self, prev_arcs: list[dict], resolved_plots_summary: str = "") -> dict` — preflight 분석 엔트리포인트.
- `modules/domain/agents/preflight_checker.py:178` `def _format_prev_arcs(self, prev_arcs: list[dict]) -> str` — 이전 Arc 컨텍스트 포맷팅.
- `modules/domain/agents/preflight_checker.py:322` `def _extract_constraints_fallback(self, prev_arcs: list[dict]) -> dict` — LLM 실패 시 Python 폴백 제약 추출.
- `modules/domain/agents/preflight_checker.py:401` `def generate_analyst_injection(self, preflight_result: dict) -> str` — Analyst 주입 텍스트 생성.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def create_unified_validator(context, client, model_tier: str = "gemini-2.5-flash")` (`modules/domain/agents/unified_arc_validator.py:630`)
- `def create_preflight_checker(context, client, model_tier: str = "gemini-2.5-pro")` (`modules/domain/agents/preflight_checker.py:490`)
2. 특징 문자열:
- `logging.warning("⚠️ [UnifiedValidator] JSON 파싱 실패 → REJECT")` (`modules/domain/agents/unified_arc_validator.py:548`)
- `logging.warning(f"⚠️ [Preflight] 분석 오류: {str(e)[:50]}")` (`modules/domain/agents/preflight_checker.py:170`)
3. import 목록:
- `from modules.core.arc_summary_utils import generate_prev_arc_summary` (`modules/domain/agents/unified_arc_validator.py:28`)
- `from modules.core.constants import Stage2Limits` (`modules/domain/agents/unified_arc_validator.py:29`)
- `from modules.core.constants import ContextLimits` (`modules/domain/agents/preflight_checker.py:17`)
- `from .base_agent import BaseAgent` (`modules/domain/agents/unified_arc_validator.py:31`, `modules/domain/agents/preflight_checker.py:19`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `ep_count = arc.get("ep_count", 5)` + `min_length = ep_count * self.min_chars_per_ep` (`modules/domain/agents/unified_arc_validator.py:227`, `modules/domain/agents/unified_arc_validator.py:232`)
- 호출자: `validate()` → `_python_validate()` → `_check_length()` (`modules/domain/agents/unified_arc_validator.py:109`, `modules/domain/agents/unified_arc_validator.py:497`, `modules/domain/agents/unified_arc_validator.py:508`)
- 상류/하류 컨텍스트:
- 상류: `arc`는 LLM 출력 dict로 `ep_count` 타입이 비정형일 수 있음.
- 하류: `if len(ep_pattern) < ep_count:` 비교 (`modules/domain/agents/unified_arc_validator.py:245`)
- 실패 시나리오: `ep_count`가 문자열이면 곱셈/비교에서 TypeError.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `item_str = ", ".join(items[:10]) if isinstance(items, list) and items else "없음"` (`modules/domain/agents/preflight_checker.py:200`)
- 호출자: `analyze()` → `_format_prev_arcs()` (`modules/domain/agents/preflight_checker.py:145`, `modules/domain/agents/preflight_checker.py:178`)
- 상류/하류 컨텍스트:
- 상류: `items = (arc.get("state_constraints") or {}).get("items_acquired", [])` (`modules/domain/agents/preflight_checker.py:199`)
- 하류: `prev_arcs_data`를 prompt에 주입 (`modules/domain/agents/preflight_checker.py:153`)
- 실패 시나리오: `items` 리스트에 dict 원소가 있으면 `join`에서 TypeError.
- 판정: BUG.

3. 위험 지점
- 코드 원문: `items.update(acquired)` / `grants.update(received)` (`modules/domain/agents/preflight_checker.py:334`, `modules/domain/agents/preflight_checker.py:339`)
- 호출자: `analyze()` 예외 폴백 경로 (`modules/domain/agents/preflight_checker.py:171`) → `_extract_constraints_fallback()` (`modules/domain/agents/preflight_checker.py:322`)
- 상류/하류 컨텍스트:
- 상류: `acquired`/`received`는 이전 Arc state_constraints에서 유입 (`modules/domain/agents/preflight_checker.py:332`, `modules/domain/agents/preflight_checker.py:337`)
- 하류: 폴백 결과 dict 생성 (`modules/domain/agents/preflight_checker.py:367`)
- 실패 시나리오: list 원소가 dict면 set update에서 `unhashable type: 'dict'`로 폴백 자체가 재실패.
- 판정: BUG.

4. 위험 지점
- 코드 원문: `prev_grants.update(g.strip() for g in grants if g)` (`modules/domain/agents/unified_arc_validator.py:392`)
- 호출자: `_python_validate()` → `_check_duplicate_grants()` (`modules/domain/agents/unified_arc_validator.py:512`, `modules/domain/agents/unified_arc_validator.py:377`)
- 상류/하류 컨텍스트:
- 상류: `grants = prev.get("state_constraints", {}).get("grants_received", [])` (`modules/domain/agents/unified_arc_validator.py:390`)
- 하류: 현재 Arc grant 중복 비교 (`modules/domain/agents/unified_arc_validator.py:397`)
- 실패 시나리오: 비문자열 grant 원소가 들어오면 `.strip()` 예외 가능.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/domain/agents/unified_arc_validator.py:232 — `ep_count` 미정규화로 분량 체크 타입 크래시

**문제**: `_check_length()`가 `ep_count`를 int로 강제하지 않고 산술/비교에 사용한다. 문자열 `ep_count` 유입 시 TypeError가 발생할 수 있다.

**문제 코드**:
```python
ep_count = arc.get("ep_count", 5)
...
min_length = ep_count * self.min_chars_per_ep
...
if len(ep_pattern) < ep_count:
```

**호출 체인**: `validate()` (`modules/domain/agents/unified_arc_validator.py:109`) → `_python_validate()` (`modules/domain/agents/unified_arc_validator.py:497`) → `_check_length()` (`modules/domain/agents/unified_arc_validator.py:224`)

**수정 제안**:
```python
ep_count = arc.get("ep_count", 5)
try:
    ep_count = int(ep_count)
except (TypeError, ValueError):
    ep_count = 5
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [HIGH] modules/domain/agents/preflight_checker.py:200 — item 목록 join 시 dict 원소 타입 크래시

**문제**: `items_acquired` 리스트 원소를 문자열로 정규화하지 않고 바로 `join`한다. dict 원소가 섞이면 `_format_prev_arcs()`에서 예외가 발생한다.

**문제 코드**:
```python
items = (arc.get("state_constraints") or {}).get("items_acquired", [])  # [V70] None 방어
item_str = ", ".join(items[:10]) if isinstance(items, list) and items else "없음"
```

**호출 체인**: `analyze()` (`modules/domain/agents/preflight_checker.py:126`) → `_format_prev_arcs()` (`modules/domain/agents/preflight_checker.py:178`) → prompt 조립 (`modules/domain/agents/preflight_checker.py:153`)

**수정 제안**:
```python
if isinstance(items, list) and items:
    item_str = ", ".join(str(i.get("name", i.get("item", i))) if isinstance(i, dict) else str(i) for i in items[:10])
else:
    item_str = "없음"
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [HIGH] modules/domain/agents/preflight_checker.py:334 — 폴백 set 집계에서 dict 원소 unhashable 예외

**문제**: 폴백 경로에서 `items`/`grants`를 set으로 모을 때 원소 정규화 없이 `update()`를 호출한다. dict 원소가 있으면 폴백이 다시 실패한다.

**문제 코드**:
```python
if isinstance(acquired, list):
    items.update(acquired)
...
if isinstance(received, list):
    grants.update(received)
```

**호출 체인**: `analyze()` 예외 처리 (`modules/domain/agents/preflight_checker.py:170`, `modules/domain/agents/preflight_checker.py:171`) → `_extract_constraints_fallback()` (`modules/domain/agents/preflight_checker.py:322`)

**수정 제안**:
```python
if isinstance(acquired, list):
    items.update((a.get("name", a.get("item", "")) if isinstance(a, dict) else str(a)) for a in acquired if a)
if isinstance(received, list):
    grants.update((g.get("grant", g.get("name", "")) if isinstance(g, dict) else str(g)) for g in received if g)
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 33 완료
## Round 34 — modules/core/stage3_orchestrator.py

### 진행 통계 업데이트
- 총 발견: 24건 (CRITICAL: 0, HIGH: 21, MEDIUM: 3)
- 라운드 진행: 34/100

### 5-A. 파일 구조 요약
- `modules/core/stage3_orchestrator.py:21` `class Stage3Orchestrator` — Stage3 배치 생성 오케스트레이터.
- `modules/core/stage3_orchestrator.py:56` `def stage_3_batch_blueprinting(self) -> None` — Stage3 진입점.
- `modules/core/stage3_orchestrator.py:238` `def _process_single_episode(self, working_ep: int, target_ep: int, prev_blueprints: list, success_count: int, fail_count: int) -> dict` — 단일 화 처리 루프.
- `modules/core/stage3_orchestrator.py:334` `def _get_entity_registry(self, arc_idx: int)` — Entity Registry 캐시.
- `modules/core/stage3_orchestrator.py:397` `def _generate_blueprint(self, working_ep, arc_data, arc_idx, prev_blueprint, prev_blueprints, entity_registry, protagonist_name, protagonist_config)` — ThreePhase Blueprint 호출.
- `modules/core/stage3_orchestrator.py:465` `def _handle_success(self, working_ep, arc_no, blueprint, pipeline_result, prev_blueprints, success_count, fail_count) -> dict` — 저장/커밋 처리.
- `modules/core/stage3_orchestrator.py:504` `def _handle_failure(self, working_ep, pipeline_result, success_count, fail_count) -> dict` — 실패 카운트/중단 처리.

### 5-D. 읽기 증명
1. 마지막 함수: `def _handle_failure(self, working_ep, pipeline_result, success_count, fail_count) -> dict` (`modules/core/stage3_orchestrator.py:504`)
2. 특징 문자열: `ctx.ui.log(f"🛑 [Safety] 연속 {new_fail_count}회 실패로 공정을 중단합니다.")` (`modules/core/stage3_orchestrator.py:518`)
3. import 목록:
- `from modules.core.constants import ContextLimits, Emojis, ErrorMessages` (`modules/core/stage3_orchestrator.py:13`)
- `from modules.core.stage3_context import Stage3Context` (`modules/core/stage3_orchestrator.py:44`)
- `from modules.domain.agents.state_tracker import StateTracker` (`modules/core/stage3_orchestrator.py:180`)
- `from modules.core.world_state import WorldStateManager` (`modules/core/stage3_orchestrator.py:203`)
- `from modules.core.fact_ledger import FactLedger` (`modules/core/stage3_orchestrator.py:220`)
- `from modules.core.spinners import StageSpinner` (`modules/core/stage3_orchestrator.py:410`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `total_planned_ep = ctx.current_project.arcs[-1].get("ep_end", 50) if ctx.current_project.arcs else 50` (`modules/core/stage3_orchestrator.py:96`)
- 호출자: `stage_3_batch_blueprinting()` (`modules/core/stage3_orchestrator.py:56`)
- 상류/하류 컨텍스트:
- 상류: Arc 데이터가 DB/LLM 경유로 적재됨.
- 하류: `ctx.get_int_input(..., max_val=total_planned_ep)` (`modules/core/stage3_orchestrator.py:112`)
- 실패 시나리오: `ep_end`가 비정수 문자열이면 입력 검증/비교 로직에서 타입 충돌 가능.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `arc_data_validated = ctx.validate_arc_data_fields(arc_data, arc_idx)` + `if arc_data_validated: arc_data = arc_data_validated` (`modules/core/stage3_orchestrator.py:284`, `modules/core/stage3_orchestrator.py:285`)
- 호출자: `_process_single_episode()` (`modules/core/stage3_orchestrator.py:238`)
- 상류/하류 컨텍스트:
- 상류: `arc_data`는 `get_arc_context_for_episode` 반환.
- 하류: `arc_no = arc_data.get("arc_no", arc_idx + 1)` (`modules/core/stage3_orchestrator.py:288`)
- 실패 시나리오: validate 함수가 비정상 값 반환 시 기존 `arc_data`를 계속 사용해 후속 단계가 오염될 수 있음.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `blueprint, pipeline_result = ctx.agents["three_phase_bp"].generate(...)` (`modules/core/stage3_orchestrator.py:434`)
- 호출자: `_generate_blueprint()` (`modules/core/stage3_orchestrator.py:397`)
- 상류/하류 컨텍스트:
- 상류: `ctx.agents` DI 구성이 런타임 상태에 의존.
- 하류: 예외 시 `pipeline_result = {"final_verdict": "ERROR", ...}`로 폴백 (`modules/core/stage3_orchestrator.py:457`)
- 실패 시나리오: 에이전트 키 누락/초기화 실패 시 생성 단계 전체가 오류 처리로 전환.
- 판정: 안전(예외 폴백 존재).

### 5-C. 발견된 버그
- 없음

---
## Round 34 완료
## Round 35 — modules/domain/agents/blueprint_ensemble.py

### 진행 통계 업데이트
- 총 발견: 26건 (CRITICAL: 0, HIGH: 23, MEDIUM: 3)
- 라운드 진행: 35/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/blueprint_ensemble.py:94` `class BlueprintEnsembleGenerator(BaseAgent)` — Stage3 앙상블 후보 생성기.
- `modules/domain/agents/blueprint_ensemble.py:111` `def generate_ensemble(self, ep_num: int, arc_data: dict, constraint_block: dict, prev_blueprint: dict | None = None, feedback: str = "", protagonist_name: str = "주인공", protagonist_config: dict = None, state_tracker=None, prev_blueprints: list[dict] | None = None, prev_manuscripts_text: str = "") -> tuple[dict | None, list[dict]]` — 3전략 병렬 생성.
- `modules/domain/agents/blueprint_ensemble.py:295` `def _generate_single(self, ep_num: int, arc_focus: str, constraints_str: str, prev_info: str, strategy: dict, feedback: str = "", protagonist_name: str = "주인공", protagonist_config: dict = None, hud_context: str = "", genre: str = "wuxia") -> dict | None` — 단일 전략 생성.
- `modules/domain/agents/blueprint_ensemble.py:512` `def _format_constraints(self, constraint_block: dict) -> str` — 제약 블록 문자열화.
- `modules/domain/agents/blueprint_ensemble.py:552` `def _format_prev_info(self, prev_blueprint: dict | None) -> str` — 직전 Blueprint 요약.
- `modules/domain/agents/blueprint_ensemble.py:608` `def _format_prev_info_expanded(self, prev_blueprint: dict | None, prev_blueprints: list[dict] | None = None, prev_manuscripts_text: str = "") -> str` — 이전 Blueprint/원고 확장 요약.
- `modules/domain/agents/blueprint_ensemble.py:682` `def create_blueprint_ensemble(context, client, model_tier: str = "gemini-3-pro-preview")` — 팩토리 함수.

### 5-D. 읽기 증명
1. 마지막 함수: `def create_blueprint_ensemble(context, client, model_tier: str = "gemini-3-pro-preview")` (`modules/domain/agents/blueprint_ensemble.py:682`)
2. 특징 문자열: `logging.warning("❌ [BPEnsemble] 모든 후보 생성 실패")` (`modules/domain/agents/blueprint_ensemble.py:240`)
3. import 목록:
- `from modules.core.constants import ContextLimits` (`modules/domain/agents/blueprint_ensemble.py:21`)
- `from modules.core.hud_utils import build_hud_context as _build_hud_context_shared` (`modules/domain/agents/blueprint_ensemble.py:22`)
- `from modules.core.prompt_loader import PromptLoader` (`modules/domain/agents/blueprint_ensemble.py:23`)
- `from modules.core.primitive_guard import get_primitive_constraint_section` (`modules/domain/agents/blueprint_ensemble.py:29`)
- `from .base_agent import BaseAgent` (`modules/domain/agents/blueprint_ensemble.py:25`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `equip = ", ".join(equip[:5])` (`modules/domain/agents/blueprint_ensemble.py:542`)
- 호출자: `generate_ensemble()` 내부 `constraints_str = self._format_constraints(constraint_block)` (`modules/domain/agents/blueprint_ensemble.py:156`)
- 상류/하류 컨텍스트:
- 상류: `inherited = constraint_block.get("inherited_state", {})` (`modules/domain/agents/blueprint_ensemble.py:538`)
- 하류: prompt 조립 후 `_generate_single()` 입력 (`modules/domain/agents/blueprint_ensemble.py:188`, `modules/domain/agents/blueprint_ensemble.py:202`)
- 실패 시나리오: `equipment` 리스트 원소가 dict면 join에서 TypeError.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `equip_str = ", ".join(equipment[:5]) if isinstance(equipment, list) else str(equipment)` (`modules/domain/agents/blueprint_ensemble.py:601`) + `chars_str = ", ".join(s_chars[:5])` (`modules/domain/agents/blueprint_ensemble.py:652`) + `events_str = "; ".join(s_events[:3])` (`modules/domain/agents/blueprint_ensemble.py:653`)
- 호출자: `generate_ensemble()` → `_format_prev_info_expanded()` (`modules/domain/agents/blueprint_ensemble.py:159`, `modules/domain/agents/blueprint_ensemble.py:608`)
- 상류/하류 컨텍스트:
- 상류: 이전 Blueprint `protagonist_state.equipment`, `scene_breakdown.characters/key_events`는 LLM 출력 비정형.
- 하류: 확장 이전화 정보 `prev_info`로 주입되어 후보 생성 입력으로 사용 (`modules/domain/agents/blueprint_ensemble.py:185`)
- 실패 시나리오: 리스트 원소 비문자열(dict 등)일 때 join TypeError.
- 판정: BUG.

3. 위험 지점
- 코드 원문: `arc_focus = constraint_block.get("must_focus", {}).get("content", "")` (`modules/domain/agents/blueprint_ensemble.py:145`)
- 호출자: `generate_ensemble()` 엔트리 (`modules/domain/agents/blueprint_ensemble.py:111`)
- 상류/하류 컨텍스트:
- 상류: `constraint_block`은 상위 컴파일러 반환값.
- 하류: `prompt` 구성에 직접 반영 (`modules/domain/agents/blueprint_ensemble.py:346`)
- 실패 시나리오: `constraint_block`이 dict가 아니면 `.get`에서 예외.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/domain/agents/blueprint_ensemble.py:542 — inherited equipment join 타입 크래시

**문제**: `inherited_state.equipment` 리스트 원소를 문자열로 정규화하지 않고 join한다. dict 원소가 있으면 예외가 발생한다.

**문제 코드**:
```python
inherited = constraint_block.get("inherited_state", {})
if inherited.get("equipment"):
    equip = inherited["equipment"]
    if isinstance(equip, list):
        equip = ", ".join(equip[:5])
```

**호출 체인**: `ThreePhaseBlueprintGenerator.generate()` (`modules/domain/agents/three_phase_blueprint_generator.py:201`) → `BlueprintEnsembleGenerator.generate_ensemble()` (`modules/domain/agents/blueprint_ensemble.py:111`) → `_format_constraints()` (`modules/domain/agents/blueprint_ensemble.py:512`)

**수정 제안**:
```python
if isinstance(equip, list):
    equip = ", ".join(str(e) for e in equip[:5] if e)
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [HIGH] modules/domain/agents/blueprint_ensemble.py:601 — 이전 Blueprint 확장 정보 join 타입 크래시

**문제**: 이전 Blueprint의 장비/등장인물/이벤트 리스트를 문자열화할 때 원소 타입 정규화가 불완전하다.

**문제 코드**:
```python
equip_str = ", ".join(equipment[:5]) if isinstance(equipment, list) else str(equipment)
...
chars_str = ", ".join(s_chars[:5]) if s_chars else ""
events_str = "; ".join(s_events[:3]) if s_events else ""
```

**호출 체인**: `ThreePhaseBlueprintGenerator.generate()` (`modules/domain/agents/three_phase_blueprint_generator.py:201`) → `generate_ensemble()` (`modules/domain/agents/blueprint_ensemble.py:111`) → `_format_prev_info_expanded()` (`modules/domain/agents/blueprint_ensemble.py:608`)

**수정 제안**:
```python
equip_str = ", ".join(str(e) for e in equipment[:5]) if isinstance(equipment, list) else str(equipment)
chars_str = ", ".join(str(c) for c in s_chars[:5]) if s_chars else ""
events_str = "; ".join(str(e) for e in s_events[:3]) if s_events else ""
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 35 완료
## Round 36 — modules/domain/agents/three_phase_blueprint_generator.py

### 진행 통계 업데이트
- 총 발견: 26건 (CRITICAL: 0, HIGH: 23, MEDIUM: 3)
- 라운드 진행: 36/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/three_phase_blueprint_generator.py:30` `class ThreePhaseBlueprintGenerator(BaseAgent)` — Stage3 3단계 파이프라인.
- `modules/domain/agents/three_phase_blueprint_generator.py:55` `def generate(self, ep_num: int, arc_data: dict, prev_blueprint: dict | None = None, prev_blueprints: list[dict] | None = None, max_retries: int = 2, external_feedback: str = "", director=None, arc_idx: int = 0, entity_registry: dict | None = None, protagonist_name: str = "주인공", protagonist_config: dict | None = None, state_tracker=None, db=None, semantic_context: str = "", prev_manuscripts_text: str = "") -> tuple[dict | None, dict]` — 메인 Blueprint 생성 루프.
- `modules/domain/agents/three_phase_blueprint_generator.py:147` `constraint_block = self.constraint_compiler.compile(...)` — 제약 컴파일.
- `modules/domain/agents/three_phase_blueprint_generator.py:247` `verdict, validation_result = self.validator.validate(...)` — 검증/Director 판정.
- `modules/domain/agents/three_phase_blueprint_generator.py:320` `def _patch_blueprint_with_feedback(...) -> tuple[dict | None, list]` — Patch Mode.
- `modules/domain/agents/three_phase_blueprint_generator.py:408` `def get_stats(self) -> dict` — 통계.
- `modules/domain/agents/three_phase_blueprint_generator.py:428` `def create_three_phase_blueprint_generator(context, client, model_tier: str = "gemini-3-pro-preview")` — 팩토리 함수.

### 5-D. 읽기 증명
1. 마지막 함수: `def create_three_phase_blueprint_generator(context, client, model_tier: str = "gemini-3-pro-preview")` (`modules/domain/agents/three_phase_blueprint_generator.py:428`)
2. 특징 문자열: `logging.warning(f"❌ [ThreePhase] 제{ep_num}화 모든 재시도 실패 ({max_retries + 1}회)")` (`modules/domain/agents/three_phase_blueprint_generator.py:311`)
3. import 목록:
- `from modules.models.blueprint import validate_blueprint` (`modules/domain/agents/three_phase_blueprint_generator.py:22`)
- `from .blueprint_constraint_compiler import BlueprintConstraintCompiler` (`modules/domain/agents/three_phase_blueprint_generator.py:25`)
- `from .blueprint_ensemble import BlueprintEnsembleGenerator` (`modules/domain/agents/three_phase_blueprint_generator.py:26`)
- `from .unified_blueprint_validator import UnifiedBlueprintValidator` (`modules/domain/agents/three_phase_blueprint_generator.py:27`)
- `from modules.core.constants import PatchModeThresholds` (`modules/domain/agents/three_phase_blueprint_generator.py:166`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `constraint_block = self.constraint_compiler.compile(...)` (`modules/domain/agents/three_phase_blueprint_generator.py:147`) + `"must_focus_length": len(str(constraint_block.get("must_focus", {}).get("content", ""))),` (`modules/domain/agents/three_phase_blueprint_generator.py:155`)
- 호출자: `generate()` (`modules/domain/agents/three_phase_blueprint_generator.py:55`)
- 상류/하류 컨텍스트:
- 상류: 컴파일러 반환 계약(dict) 의존.
- 하류: `self.ensemble.generate_ensemble(..., constraint_block=constraint_block, ...)` (`modules/domain/agents/three_phase_blueprint_generator.py:201`)
- 실패 시나리오: 컴파일러 비정상 반환 시 `.get` 연쇄 접근 예외.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `_prev_reject_score = validation_result.get("score", 0)` (`modules/domain/agents/three_phase_blueprint_generator.py:290`) + `if _prev_reject_score >= PatchModeThresholds.REWRITE and best_blueprint:` (`modules/domain/agents/three_phase_blueprint_generator.py:291`)
- 호출자: `generate()` REJECT 분기 (`modules/domain/agents/three_phase_blueprint_generator.py:286`)
- 상류/하류 컨텍스트:
- 상류: `validation_result`는 validator에서 생성.
- 하류: Patch Mode 진입 여부 결정 (`modules/domain/agents/three_phase_blueprint_generator.py:170`)
- 실패 시나리오: score가 비정수 문자열이면 비교 TypeError 가능.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `"candidates_count": len(all_candidates),` (`modules/domain/agents/three_phase_blueprint_generator.py:222`)
- 호출자: `generate()` Phase2 완료 기록 (`modules/domain/agents/three_phase_blueprint_generator.py:220`)
- 상류/하류 컨텍스트:
- 상류: `best_blueprint, all_candidates = self.ensemble.generate_ensemble(...)` (`modules/domain/agents/three_phase_blueprint_generator.py:201`)
- 하류: validate 호출에 `all_candidates` 전달 (`modules/domain/agents/three_phase_blueprint_generator.py:257`)
- 실패 시나리오: 반환 계약 불일치로 `all_candidates`가 None이면 len() 예외.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 36 완료

## Round 37 — modules/domain/agents/unified_blueprint_validator.py

### 진행 통계 업데이트
- 총 발견: 27건 (CRITICAL: 0, HIGH: 24, MEDIUM: 3)
- 라운드 진행: 37/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/unified_blueprint_validator.py:40` `class UnifiedBlueprintValidator` — Stage3 통합 검증기.
- `modules/domain/agents/unified_blueprint_validator.py:55` `def validate(self, blueprint: dict, arc_data: dict, constraint_block: dict, prev_blueprint: dict | None = None, director=None, working_ep: int = 1, arc_idx: int = 0, entity_registry: dict | None = None, state_tracker=None, all_candidates: list[dict] | None = None) -> tuple[str, dict]` — 검증 진입점.
- `modules/domain/agents/unified_blueprint_validator.py:282` `def _python_pre_validate(self, blueprint: dict, constraint_block: dict, prev_blueprint: dict | None, state_tracker=None) -> dict` — Python 사전검증.
- `modules/domain/agents/unified_blueprint_validator.py:395` `def _is_location_transition_valid(self, prev_loc: str, curr_loc: str) -> bool` — 위치 전환 체크.
- `modules/domain/agents/unified_blueprint_validator.py:413` `def _generate_feedback(self, issues: list[dict]) -> str` — 피드백 조립.
- `modules/domain/agents/unified_blueprint_validator.py:438` `def create_unified_blueprint_validator(context, client, model_tier: str = "gemini-2.5-flash")` — 팩토리 함수.

### 5-D. 읽기 증명
1. 마지막 함수: `def create_unified_blueprint_validator(context, client, model_tier: str = "gemini-2.5-flash")` (`modules/domain/agents/unified_blueprint_validator.py:438`)
2. 특징 문자열: `logging.warning("🎬 [Director] Blueprint 최종 판정 중...")` (`modules/domain/agents/unified_blueprint_validator.py:179`)
3. import 목록:
- `from .base_agent import _get_agent_default_model` (`modules/domain/agents/unified_blueprint_validator.py:26`)
- 프로젝트 내부 import는 위 1개만 존재(파일 전수 확인).

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `"score": compare_result.get("score", 0),` (`modules/domain/agents/unified_blueprint_validator.py:111`)
- 호출자: `validate()`의 Director 비교 선택 분기 (`modules/domain/agents/unified_blueprint_validator.py:91`)
- 상류/하류 컨텍스트:
- 상류: `compare_result = director.compare_and_select_blueprint(...)` (`modules/domain/agents/unified_blueprint_validator.py:94`)
- 하류: ThreePhase에서 `_prev_reject_score = validation_result.get("score", 0)` 후 임계값 비교 (`modules/domain/agents/three_phase_blueprint_generator.py:290`, `modules/domain/agents/three_phase_blueprint_generator.py:291`)
- 실패 시나리오: score가 문자열이면 downstream 숫자 비교에서 TypeError.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `ep_start = arc_data.get("ep_start", working_ep)` + `arc_pos = working_ep - ep_start + 1` (`modules/domain/agents/unified_blueprint_validator.py:197`, `modules/domain/agents/unified_blueprint_validator.py:198`)
- 호출자: `validate()` Director 판정 블록 (`modules/domain/agents/unified_blueprint_validator.py:179`)
- 상류/하류 컨텍스트:
- 상류: `arc_data`는 외부 주입.
- 하류: `director.audit_manuscript(..., arc_pos=arc_pos, ...)` (`modules/domain/agents/unified_blueprint_validator.py:216`)
- 실패 시나리오: `ep_start`가 문자열이면 산술 TypeError 후 예외 경로 REJECT.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `if director is None: ... return "PASS", {...}` (`modules/domain/agents/unified_blueprint_validator.py:167`)
- 호출자: `validate()` (`modules/domain/agents/unified_blueprint_validator.py:55`)
- 상류/하류 컨텍스트:
- 상류: 운영 설정에 따라 director 미주입 가능.
- 하류: Python 경고만 가진 PASS 결과 반환 (`modules/domain/agents/unified_blueprint_validator.py:173`)
- 실패 시나리오: 치명적 사전 이슈가 있어도 최종 PASS 처리될 수 있음.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/domain/agents/unified_blueprint_validator.py:111 — 비교 모드 score 타입 미정규화로 하위 파이프라인 비교 크래시

**문제**: Director 비교 모드 결과의 `score`를 숫자 정규화 없이 그대로 반환한다. 하위 호출부에서 정수 임계값과 비교할 때 타입 충돌이 발생할 수 있다.

**문제 코드**:
```python
result = {
    "verdict": verdict,
    "phase": "director_compare",
    "issues": [],
    "summary": compare_result.get("reason", ""),
    "score": compare_result.get("score", 0),
    ...
}
```

**호출 체인**: `UnifiedBlueprintValidator.validate()` (`modules/domain/agents/unified_blueprint_validator.py:55`) → `ThreePhaseBlueprintGenerator.generate()`의 REJECT 분기 score 사용 (`modules/domain/agents/three_phase_blueprint_generator.py:290`) → `>= PatchModeThresholds.REWRITE` 비교 (`modules/domain/agents/three_phase_blueprint_generator.py:291`)

**수정 제안**:
```python
"score": _safe_int(compare_result.get("score", 0), 0),
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 37 완료
## Round 38 — modules/domain/agents/blueprint_constraint_compiler.py + modules/domain/agents/constraint_compiler.py

### 진행 통계 업데이트
- 총 발견: 30건 (CRITICAL: 0, HIGH: 27, MEDIUM: 3)
- 라운드 진행: 38/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/blueprint_constraint_compiler.py:22` `class BlueprintConstraintCompiler` — Stage3 제약 블록 컴파일러.
- `modules/domain/agents/blueprint_constraint_compiler.py:32` `def compile(self, arc_data: dict, ep_num: int, prev_blueprint: dict | None = None, prev_blueprints: list[dict] | None = None) -> dict` — 구조화 제약 생성.
- `modules/domain/agents/blueprint_constraint_compiler.py:221` `def _extract_stop_line(self, arc_data: dict, ep_num: int, arc_position: int, ep_count: int) -> dict` — 정지선 추출.
- `modules/domain/agents/blueprint_constraint_compiler.py:298` `def _extract_inherited_state(self, arc_data: dict, prev_blueprint: dict | None) -> dict` — 계승 상태 추출.
- `modules/domain/agents/constraint_compiler.py:21` `class ConstraintCompiler` — Stage2 제약 체크리스트 컴파일러.
- `modules/domain/agents/constraint_compiler.py:82` `def _collect_all_items(self, prev_arcs: list[dict]) -> dict[str, int]` — 아이템 수집.
- `modules/domain/agents/constraint_compiler.py:128` `def _collect_all_grants(self, prev_arcs: list[dict]) -> dict[str, tuple[int, str]]` — 수여물 수집.
- `modules/domain/agents/constraint_compiler.py:215` `def _generate_constraint_checklist(self, all_items: dict[str, int], all_grants: dict[str, tuple[int, str]], current_state: dict, arc_count: int, resolved_plots: list[dict] = None) -> str` — 체크리스트 생성.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def create_blueprint_constraint_compiler()` (`modules/domain/agents/blueprint_constraint_compiler.py:432`)
- `def create_constraint_compiler() -> ConstraintCompiler` (`modules/domain/agents/constraint_compiler.py:392`)
2. 특징 문자열:
- `logging.info(f"⚠️ [V63.4 P1] Arc {arc_no}에 constraint_summary 필드 없음 → Stage 2 제약 전달 누락 가능")` (`modules/domain/agents/blueprint_constraint_compiler.py:70`)
- `"⚠️ items_acquired에 위 아이템이 포함되면 즉시 REJECT됩니다!"` (`modules/domain/agents/constraint_compiler.py:244`)
3. import 목록:
- 두 파일 모두 프로젝트 내부 import 없이 표준 라이브러리만 사용(`json`, `logging`, `re`).

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `if item and len(item) >= 2: items[item] = arc_no` (`modules/domain/agents/constraint_compiler.py:97`, `modules/domain/agents/constraint_compiler.py:98`) 및 `if item and len(item) >= 2 and item not in items: items[item] = arc_no` (`modules/domain/agents/constraint_compiler.py:104`, `modules/domain/agents/constraint_compiler.py:105`)
- 호출자: `compile()` (`modules/domain/agents/constraint_compiler.py:41`)
- 상류/하류 컨텍스트:
- 상류: `acquired`/`inventory`는 `state_constraints.items_acquired`/`joint_docs.physical_inventory` (`modules/domain/agents/constraint_compiler.py:94`, `modules/domain/agents/constraint_compiler.py:101`)
- 하류: 체크리스트 생성으로 전달 (`modules/domain/agents/constraint_compiler.py:71`)
- 실패 시나리오: 원소가 dict면 dict를 key로 사용해 `unhashable type: 'dict'`.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `if grant and len(grant) >= 2: grants[grant] = (arc_no, "알 수 없음")` (`modules/domain/agents/constraint_compiler.py:142`, `modules/domain/agents/constraint_compiler.py:143`)
- 호출자: `compile()` → `_collect_all_grants()` (`modules/domain/agents/constraint_compiler.py:64`, `modules/domain/agents/constraint_compiler.py:128`)
- 상류/하류 컨텍스트:
- 상류: `received = ...get("grants_received", [])` (`modules/domain/agents/constraint_compiler.py:139`)
- 하류: `_generate_constraint_checklist(..., all_grants=...)` (`modules/domain/agents/constraint_compiler.py:73`)
- 실패 시나리오: dict grant 원소를 key로 넣어 unhashable 예외.
- 판정: BUG.

3. 위험 지점
- 코드 원문: `_extract_stop_line()` 폴백에서 `content = beats[arc_position]` (`modules/domain/agents/blueprint_constraint_compiler.py:244`) + 하류에서 `stop_keywords = stop_content[:30].strip()` (`modules/domain/agents/unified_blueprint_validator.py:346`)
- 호출자: `ThreePhaseBlueprintGenerator.generate()` → `constraint_compiler.compile()` (`modules/domain/agents/three_phase_blueprint_generator.py:147`) → `validator.validate(..., constraint_block=constraint_block, ...)` (`modules/domain/agents/three_phase_blueprint_generator.py:247`)
- 상류/하류 컨텍스트:
- 상류: `beat_sequence` 원소 타입 비정형 가능.
- 하류: `UnifiedBlueprintValidator._python_pre_validate()` stop_line 검사 (`modules/domain/agents/unified_blueprint_validator.py:343`)
- 실패 시나리오: `content`가 dict면 slice/strip에서 TypeError.
- 판정: BUG.

4. 위험 지점
- 코드 원문: `arc_position = ep_num - ep_start + 1` (`modules/domain/agents/blueprint_constraint_compiler.py:53`)
- 호출자: `compile()` (`modules/domain/agents/blueprint_constraint_compiler.py:32`)
- 상류/하류 컨텍스트:
- 상류: `ep_start = arc_data.get("ep_start", 1)` (`modules/domain/agents/blueprint_constraint_compiler.py:48`)
- 하류: `_extract_episode_focus(..., arc_position)` / `_extract_stop_line(..., arc_position, ep_count)` (`modules/domain/agents/blueprint_constraint_compiler.py:56`, `modules/domain/agents/blueprint_constraint_compiler.py:59`)
- 실패 시나리오: `ep_start`가 문자열이면 산술 TypeError.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/domain/agents/constraint_compiler.py:98 — dict 아이템을 dict key로 사용하여 unhashable 예외

**문제**: 구조화 필드에서 읽은 `items_acquired`/`physical_inventory` 원소를 key로 직접 사용한다. dict 원소일 때 예외가 발생한다.

**문제 코드**:
```python
if isinstance(acquired, list):
    for item in acquired:
        if item and len(item) >= 2:
            items[item] = arc_no
...
if isinstance(inventory, list):
    for item in inventory:
        if item and len(item) >= 2 and item not in items:
            items[item] = arc_no
```

**호출 체인**: `Stage2Preflight`의 `constraint_compiler.compile(...)` (`modules/core/stage2_preflight.py:160`) / `FourPhaseArcGenerator`의 `self.compiler.compile(prev_arcs)` (`modules/domain/agents/four_phase_arc_generator.py:216`) → `_collect_all_items()` (`modules/domain/agents/constraint_compiler.py:82`)

**수정 제안**:
```python
name = item.get("name", item.get("item", "")) if isinstance(item, dict) else str(item).strip()
if name and len(name) >= 2:
    items[name] = arc_no
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [HIGH] modules/domain/agents/constraint_compiler.py:143 — grants 수집 시 dict key unhashable 예외

**문제**: `grants_received` 원소를 문자열 정규화 없이 dict key로 사용한다. dict 원소 유입 시 크래시한다.

**문제 코드**:
```python
received = (arc.get("state_constraints") or {}).get("grants_received", [])
if isinstance(received, list):
    for grant in received:
        if grant and len(grant) >= 2:
            grants[grant] = (arc_no, "알 수 없음")
```

**호출 체인**: `ConstraintCompiler.compile()` (`modules/domain/agents/constraint_compiler.py:41`) → `_collect_all_grants()` (`modules/domain/agents/constraint_compiler.py:128`)

**수정 제안**:
```python
gname = grant.get("grant", grant.get("name", "")) if isinstance(grant, dict) else str(grant).strip()
if gname and len(gname) >= 2:
    grants[gname] = (arc_no, "알 수 없음")
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [HIGH] modules/domain/agents/blueprint_constraint_compiler.py:244 — stop_line content 비문자열 전파로 사전검증 타입 크래시

**문제**: `_extract_stop_line()` 폴백 경로에서 `beat_sequence` 원소를 타입 정규화 없이 `content`로 넣는다. dict가 전달되면 하위 validator에서 문자열 슬라이스/strip에서 예외가 난다.

**문제 코드**:
```python
beats = arc_data.get("beat_sequence", [])
if arc_position < len(beats):
    content = beats[arc_position]  # 다음 비트
...
return {"content": content if content else None, "is_arc_finale": False, "next_ep": next_ep}
```

**호출 체인**: `ThreePhaseBlueprintGenerator.generate()` (`modules/domain/agents/three_phase_blueprint_generator.py:147`) → `constraint_block` 전달 (`modules/domain/agents/three_phase_blueprint_generator.py:250`) → `UnifiedBlueprintValidator._python_pre_validate()` stop_line 검사 (`modules/domain/agents/unified_blueprint_validator.py:343`, `modules/domain/agents/unified_blueprint_validator.py:346`)

**수정 제안**:
```python
if isinstance(content, dict):
    content = content.get("beat", content.get("description", str(content)))
if not isinstance(content, str):
    content = str(content) if content else ""
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 38 완료
## Round 39 — modules/validation/validation_orchestrator.py (L1~700)

### 진행 통계 업데이트
- 총 발견: 30건 (CRITICAL: 0, HIGH: 27, MEDIUM: 3)
- 라운드 진행: 39/100

### 5-A. 파일 구조 요약
- `modules/validation/validation_orchestrator.py:130` `class ValidationOrchestrator` — 검증 파이프라인 총괄.
- `modules/validation/validation_orchestrator.py:207` `def validate(self, ep_num: int, manuscript: str, validation_context: dict) -> dict` — 순차 검증 메인 엔트리.
- `modules/validation/validation_orchestrator.py:545` `def _evaluate_with_self_consistency(self, manuscript: str, context: dict) -> dict` — 다중 투표 스코어링.
- `modules/validation/validation_orchestrator.py:621` `def _generate_pre_llm_feedback(self, pre_llm_result: dict) -> str` — PRE-LLM 피드백.
- `modules/validation/validation_orchestrator.py:654` `def _generate_continuity_feedback(self, continuity_result: dict) -> str` — 연속성 피드백.
- `modules/validation/validation_orchestrator.py:684` `def _generate_blocking_feedback(self, blocking_result: dict) -> str` — 블로킹 실패 피드백.

### 5-D. 읽기 증명
1. 마지막 함수(검사 구간 기준): `def _generate_blocking_feedback(self, blocking_result: dict) -> str` (`modules/validation/validation_orchestrator.py:684`)
2. 특징 문자열: `logging.info("[V0128] TIER 1: BLOCKING 검증 중...")` (`modules/validation/validation_orchestrator.py:302`)
3. import 목록:
- `from .blocking_validator import BlockingValidator` (`modules/validation/validation_orchestrator.py:28`)
- `from .consistency_validator import ConsistencyValidator` (`modules/validation/validation_orchestrator.py:30`)
- `from .scoring_validator import ScoringValidator` (`modules/validation/validation_orchestrator.py:32`)
- `from .continuity_validator import ContinuityValidator` (`modules/validation/validation_orchestrator.py:31`)
- `from .advisory_validator import AdvisoryValidator` (`modules/validation/validation_orchestrator.py:27`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `logging.warning(f"⚠️ PRE-LLM 경고: {warning_count}개 (점수 -{pre_llm_result['score_deduction']}점)")` (`modules/validation/validation_orchestrator.py:266`)
- 호출자: `validate()` PRE-LLM 경고 분기 (`modules/validation/validation_orchestrator.py:264`)
- 상류/하류 컨텍스트:
- 상류: `pre_llm_result = self.pre_llm.validate(...)` (`modules/validation/validation_orchestrator.py:241`)
- 하류: 이후 CONTINUITY/BLOCKING 검증 진행 (`modules/validation/validation_orchestrator.py:274`, `modules/validation/validation_orchestrator.py:303`)
- 실패 시나리오: 키 계약 깨지면 KeyError.
- 판정: 안전(PreLLMValidator 반환 스키마에 `score_deduction` 고정).

2. 위험 지점
- 코드 원문: `total_score = scoring_result.get("total_score", 0)` (`modules/validation/validation_orchestrator.py:371`) + `adjusted_total = total_score + catharsis_adjustment + action_adjustment + consistency_adjustment` (`modules/validation/validation_orchestrator.py:459`)
- 호출자: `validate()` SCORING 이후 점수 조정 구간 (`modules/validation/validation_orchestrator.py:356`)
- 상류/하류 컨텍스트:
- 상류: `scoring_result = self.scoring.validate(...)` 또는 self-consistency 평가 결과 (`modules/validation/validation_orchestrator.py:363`, `modules/validation/validation_orchestrator.py:366`)
- 하류: 최종 판정 분기 (`modules/validation/validation_orchestrator.py:526`)
- 실패 시나리오: `total_score` 비수치 타입이면 산술 TypeError.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `self._record_failure_to_reflexion(ep_num, "blocking", blocking_result["failures"])` (`modules/validation/validation_orchestrator.py:308`)
- 호출자: `validate()` BLOCKING 실패 분기 (`modules/validation/validation_orchestrator.py:306`)
- 상류/하류 컨텍스트:
- 상류: `blocking_result = self.blocking.validate(...)` (`modules/validation/validation_orchestrator.py:303`)
- 하류: 즉시 REJECT 반환 (`modules/validation/validation_orchestrator.py:310`)
- 실패 시나리오: 실패 결과 스키마에서 `failures` 누락 시 KeyError.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 39 완료

## Round 40 — modules/validation/validation_orchestrator.py (L701~end)

### 진행 통계 업데이트
- 총 발견: 31건 (CRITICAL: 0, HIGH: 28, MEDIUM: 3)
- 라운드 진행: 40/100

### 5-A. 파일 구조 요약
- `modules/validation/validation_orchestrator.py:701` `def _generate_detailed_feedback(self, results: dict) -> str` — 상세 피드백 조립.
- `modules/validation/validation_orchestrator.py:936` `async def validate_parallel_v59(self, ep_num: int, manuscript: str, validation_context: dict) -> dict` — 병렬 검증 본체.
- `modules/validation/validation_orchestrator.py:1146` `def validate_parallel_sync_v59(self, ep_num: int, manuscript: str, validation_context: dict) -> dict` — 동기 래퍼.
- `modules/validation/validation_orchestrator.py:1187` `def _build_reject_result_v59(self, stage: str, result: dict, feedback: str) -> dict` — 조기 종료 결과 빌더.
- `modules/validation/validation_orchestrator.py:1203` `def calculate_adaptive_threshold_v59(self, ep_num: int, validation_context: dict) -> int` — 적응형 임계값 계산.
- `modules/validation/validation_orchestrator.py:1313` `def _record_validation_history_v59(self, ep_num: int, score: float, passed: bool)` — 히스토리 기록.
- `modules/validation/validation_orchestrator.py:1331` `def get_threshold_report_v59(self, ep_num: int, validation_context: dict = None) -> str` — 임계값 리포트.
- `modules/validation/validation_orchestrator.py:1397` `def set_manual_threshold_v59(self, threshold: int, duration_episodes: int = 0)` — 수동 임계값 설정.

### 5-D. 읽기 증명
1. 마지막 함수: `def set_manual_threshold_v59(self, threshold: int, duration_episodes: int = 0)` (`modules/validation/validation_orchestrator.py:1397`)
2. 특징 문자열: `logging.info(f"[V59] 임계값 {threshold}점으로 고정 (적응형 비활성화)")` (`modules/validation/validation_orchestrator.py:1411`)
3. import 목록:
- `import asyncio` (`modules/validation/validation_orchestrator.py:20`)
- `import concurrent.futures` (`modules/validation/validation_orchestrator.py:21`)
- `from .scoring_validator import ScoringValidator` (`modules/validation/validation_orchestrator.py:32`)
- `from .advisory_validator import AdvisoryValidator` (`modules/validation/validation_orchestrator.py:27`)
- `from .continuity_validator import ContinuityValidator` (`modules/validation/validation_orchestrator.py:31`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `_original_threshold = self.scoring.pass_threshold` (`modules/validation/validation_orchestrator.py:960`) + 조기 반환 `return self._build_reject_result_v59(...)` (`modules/validation/validation_orchestrator.py:977`, `modules/validation/validation_orchestrator.py:988`, `modules/validation/validation_orchestrator.py:999`) + 복원 코드 `self.scoring.pass_threshold = _original_threshold` (`modules/validation/validation_orchestrator.py:1142`)
- 호출자: `validate_parallel_sync_v59()` → `validate_parallel_v59()` (`modules/validation/validation_orchestrator.py:1168`, `modules/validation/validation_orchestrator.py:1182`)
- 상류/하류 컨텍스트:
- 상류: 적응형 임계값 적용 시 `self.scoring.pass_threshold = adaptive_threshold` (`modules/validation/validation_orchestrator.py:963`)
- 하류: 동기 검증 판정에서 임계값 사용 (`modules/validation/validation_orchestrator.py:526`, `modules/validation/validation_orchestrator.py:530`)
- 실패 시나리오: Stage1 조기 REJECT 시 복원 라인을 타지 않아 pass_threshold가 오염된 채 남고, 이후 검증 판정에 누수 영향.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `recent_scores = [h["score"] for h in self.validation_history[-5:]]` + `if recent_scores[-1] < recent_scores[-3] - 5:` (`modules/validation/validation_orchestrator.py:1290`, `modules/validation/validation_orchestrator.py:1293`)
- 호출자: `calculate_adaptive_threshold_v59()` → `_get_pattern_adjustment_v59()` (`modules/validation/validation_orchestrator.py:1224`, `modules/validation/validation_orchestrator.py:1270`)
- 상류/하류 컨텍스트:
- 상류: `_record_validation_history_v59()`가 score를 타입 정규화 없이 저장 (`modules/validation/validation_orchestrator.py:1317`)
- 하류: 최종 threshold 계산 (`modules/validation/validation_orchestrator.py:1230`)
- 실패 시나리오: score 타입이 숫자가 아니면 트렌드 비교 연산 TypeError.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `lines.append(f"  제{h['ep_num']}화: {h['score']:.0f}점 ({status})")` (`modules/validation/validation_orchestrator.py:1381`)
- 호출자: `get_threshold_report_v59()` (`modules/validation/validation_orchestrator.py:1331`)
- 상류/하류 컨텍스트:
- 상류: `validation_history`는 외부 흐름 점수값을 누적.
- 하류: 운영용 리포트 문자열 반환 (`modules/validation/validation_orchestrator.py:1387`)
- 실패 시나리오: score가 숫자가 아니면 포맷팅 ValueError/TypeError.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/validation/validation_orchestrator.py:977 — 병렬 검증 조기 종료 시 adaptive threshold 복원 누락(상태 누수)

**문제**: `validate_parallel_v59()`는 시작 시 `self.scoring.pass_threshold`를 adaptive 값으로 덮어쓴 뒤, 정상 종료 경로에서만 원복한다. PRE-LLM/CONTINUITY/BLOCKING 단계 조기 REJECT 반환 시 원복이 실행되지 않아 임계값이 누수된다.

**문제 코드**:
```python
_original_threshold = self.scoring.pass_threshold
if self.use_adaptive_threshold:
    adaptive_threshold = self.calculate_adaptive_threshold_v59(ep_num, validation_context)
    self.scoring.pass_threshold = adaptive_threshold
...
if not pre_llm_result["passed"]:
    return self._build_reject_result_v59(...)
...
self.scoring.pass_threshold = _original_threshold
return results
```

**호출 체인**: `validate_parallel_sync_v59()` (`modules/validation/validation_orchestrator.py:1168`, `modules/validation/validation_orchestrator.py:1182`) → `validate_parallel_v59()` (`modules/validation/validation_orchestrator.py:936`) → 이후 `validate()` 판정 임계값 사용 (`modules/validation/validation_orchestrator.py:526`, `modules/validation/validation_orchestrator.py:530`)

**수정 제안**:
```python
_original_threshold = self.scoring.pass_threshold
try:
    ...
    return results_or_reject
finally:
    self.scoring.pass_threshold = _original_threshold
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 40 완료

## Round 41 — modules/validation/scoring_validator.py (L1~500)

### 진행 통계 업데이트
- 총 발견: 32건 (CRITICAL: 0, HIGH: 29, MEDIUM: 3)
- 라운드 진행: 41/100

### 5-A. 파일 구조 요약
- `modules/validation/scoring_validator.py:16` `class ScoringValidator` — 점수 기반 품질 검증 본체.
- `modules/validation/scoring_validator.py:101` `def validate(self, manuscript: str, validation_context: dict) -> dict` — 기본 점수 산출 엔트리.
- `modules/validation/scoring_validator.py:154` `def _calculate_llm_scores(self, manuscript: str, context: dict) -> dict` — LLM 점수 계산 + fallback.
- `modules/validation/scoring_validator.py:274` `def _fallback_llm_scores(self, manuscript: str, context: dict) -> dict` — 비LLM 폴백 점수.
- `modules/validation/scoring_validator.py:318` `def _generate_dynamic_context(self, context: dict) -> str` — HUD/Guard 기반 동적 프롬프트 컨텍스트 생성.
- `modules/validation/scoring_validator.py:396` `def _evaluate_prose_rhythm(self, manuscript: str) -> dict` — 문장 리듬 점수.
- `modules/validation/scoring_validator.py:428` `def _evaluate_vocabulary_diversity(self, manuscript: str) -> dict` — 어휘 다양성 점수.

### 5-D. 읽기 증명
1. 마지막 함수(검사 구간 기준): `def _evaluate_vocabulary_diversity(self, manuscript: str) -> dict` (`modules/validation/scoring_validator.py:428`)
2. 특징 문자열: `logging.warning("[WARNING] LLM이 예상치 못한 list 반환 - Fallback 전환")` (`modules/validation/scoring_validator.py:249`)
3. import 목록:
- `from modules.validation.threshold_helper import _threshold` (`modules/validation/scoring_validator.py:13`)
- 표준 라이브러리 import: `logging`, `re`, `statistics`, `collections.Counter` (`modules/validation/scoring_validator.py:7`~`modules/validation/scoring_validator.py:10`)
- 동적 import: `from modules.core.genre_guards.wuxia_guard import WuxiaGuard` (`modules/validation/scoring_validator.py:67`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `total_score = sum(v.get("score", 0) if isinstance(v, dict) else 0 for v in all_scores.values())` (`modules/validation/scoring_validator.py:127`)
- 호출자: `ValidationOrchestrator.validate()` → `self.scoring.validate(...)` (`modules/validation/validation_orchestrator.py:366`)
- 상류/하류 컨텍스트:
- 상류: LLM 점수 정규화는 `if isinstance(_val, dict) and "score" in _val and "max" in _val:` 조건일 때만 수행 (`modules/validation/scoring_validator.py:258`)
- 하류: `passed = total_score >= self.pass_threshold` (`modules/validation/scoring_validator.py:129`)
- 실패 시나리오: LLM 항목에 `score`는 있으나 `max`가 누락된 경우 문자열 score가 합산돼 TypeError.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `dynamic_context = self._generate_dynamic_context(context)` (`modules/validation/scoring_validator.py:163`) + `martial_hud = context.get("martial_hud", {})` (`modules/validation/scoring_validator.py:329`)
- 호출자: `validate()` → `_calculate_llm_scores()` (`modules/validation/scoring_validator.py:121`, `modules/validation/scoring_validator.py:154`)
- 상류/하류 컨텍스트:
- 상류: `validate()`는 `validation_context` 타입 강제 없이 전달 (`modules/validation/scoring_validator.py:101`)
- 하류: 프롬프트 조립 후 LLM 호출 (`modules/validation/scoring_validator.py:168`)
- 실패 시나리오: context가 dict가 아닌 truthy 객체면 `.get` AttributeError.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `passed = total_score >= self.pass_threshold` (`modules/validation/scoring_validator.py:129`)
- 호출자: `ValidationOrchestrator.validate()`/`_evaluate_with_self_consistency()` (`modules/validation/validation_orchestrator.py:366`, `modules/validation/validation_orchestrator.py:545`)
- 상류/하류 컨텍스트:
- 상류: `self.pass_threshold`는 외부 인자/설정값에서 유입 (`modules/validation/scoring_validator.py:55`~`modules/validation/scoring_validator.py:60`)
- 하류: 결과 dict `passed` 및 message 생성 (`modules/validation/scoring_validator.py:131`~`modules/validation/scoring_validator.py:139`)
- 실패 시나리오: threshold가 숫자가 아니면 비교 TypeError.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/validation/scoring_validator.py:127 — LLM 비정형 score 문자열 유입 시 합산 TypeError

**문제**: `validate()` 합산부가 score 타입을 강제하지 않는다. `_calculate_llm_scores()`의 클램프는 `max` 키가 있는 항목만 변환하므로, `score`만 있는 비정형 dict가 들어오면 문자열이 그대로 합산돼 크래시한다.

**문제 코드**:
```python
total_score = sum(v.get("score", 0) if isinstance(v, dict) else 0 for v in all_scores.values())
...
if isinstance(_val, dict) and "score" in _val and "max" in _val:
    _val["score"] = max(0, min(int(_val["score"]), int(_val["max"])))
```

**호출 체인**: `ValidationOrchestrator.validate()` (`modules/validation/validation_orchestrator.py:366`) → `ScoringValidator.validate()` (`modules/validation/scoring_validator.py:101`) → `_calculate_llm_scores()` (`modules/validation/scoring_validator.py:154`) → 합산 (`modules/validation/scoring_validator.py:127`)

**수정 제안**:
```python
score_val = v.get("score", 0) if isinstance(v, dict) else 0
try:
    score_num = float(score_val)
except (TypeError, ValueError):
    score_num = 0
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 41 완료

## Round 42 — modules/validation/scoring_validator.py (L501~end)

### 진행 통계 업데이트
- 총 발견: 33건 (CRITICAL: 0, HIGH: 30, MEDIUM: 3)
- 라운드 진행: 42/100

### 5-A. 파일 구조 요약
- `modules/validation/scoring_validator.py:504` `def _evaluate_sensory_balance(self, manuscript: str) -> dict` — 오감 균형 점수.
- `modules/validation/scoring_validator.py:542` `def _evaluate_show_dont_tell(self, manuscript: str) -> dict` — 직접서술/감각 패널티 점수.
- `modules/validation/scoring_validator.py:717` `def validate_v59(self, manuscript: str, validation_context: dict) -> dict` — 장르 가중치 적용 점수 계산.
- `modules/validation/scoring_validator.py:829` `def _generate_detailed_feedback(self, manuscript: str, breakdown: dict, genre: str) -> dict` — 상세 피드백 생성.
- `modules/validation/scoring_validator.py:980` `def _get_improvement_priorities(self, breakdown: dict, genre: str) -> list[dict]` — 개선 우선순위 산출.

### 5-D. 읽기 증명
1. 마지막 함수: `def _get_improvement_priorities(self, breakdown: dict, genre: str) -> list[dict]` (`modules/validation/scoring_validator.py:980`)
2. 특징 문자열: `logging.warning(f"[ScoringValidator] weighted_max_total=0 — raw_total({raw_total}) 기반 폴백 계산")` (`modules/validation/scoring_validator.py:779`)
3. import 목록:
- `from modules.validation.threshold_helper import _threshold` (`modules/validation/scoring_validator.py:13`)
- 표준 라이브러리 import: `logging`, `re`, `statistics`, `Counter` (`modules/validation/scoring_validator.py:7`~`modules/validation/scoring_validator.py:10`)
- 동적 import: `from google.genai import types` (`modules/validation/scoring_validator.py:228`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `raw_score = item_data.get("score", 0)` (`modules/validation/scoring_validator.py:747`) + `weighted_score = raw_score * weight` (`modules/validation/scoring_validator.py:752`)
- 호출자: `ValidationOrchestrator` v59 경로의 `scoring.validate_v59(...)`
- 상류/하류 컨텍스트:
- 상류: `base_result = self.validate(...)` (`modules/validation/scoring_validator.py:733`)는 비정형 score 문자열 유입 가능.
- 하류: `weighted_total += weighted_score` (`modules/validation/scoring_validator.py:763`)
- 실패 시나리오: raw_score가 문자열이면 `str * float` TypeError.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `passed = weighted_percentage >= self.pass_threshold` (`modules/validation/scoring_validator.py:783`)
- 호출자: `validate_v59()` 내부 최종 판정 (`modules/validation/scoring_validator.py:717`)
- 상류/하류 컨텍스트:
- 상류: `self.pass_threshold`는 동적 임계값/수동 설정값.
- 하류: `message`/`passed` 결과 생성 (`modules/validation/scoring_validator.py:785`)
- 실패 시나리오: threshold 타입 불량 시 비교 예외.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `score = item_data.get("weighted_score", 0)` + `ratio = score / max_score if max_score > 0 else 0` (`modules/validation/scoring_validator.py:843`~`modules/validation/scoring_validator.py:845`)
- 호출자: `validate_v59()` → `_generate_detailed_feedback()` (`modules/validation/scoring_validator.py:766`, `modules/validation/scoring_validator.py:829`)
- 상류/하류 컨텍스트:
- 상류: weighted_breakdown 값은 외부 유입 점수 타입에 의존.
- 하류: 강점/약점 분류 및 문자열 포맷 (`modules/validation/scoring_validator.py:850`~`modules/validation/scoring_validator.py:861`)
- 실패 시나리오: weighted_score/max가 숫자형이 아니면 비교/나눗셈 실패.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/validation/scoring_validator.py:752 — v59 가중치 계산에서 비수치 score 미정규화 TypeError

**문제**: `validate_v59()`가 `item_data["score"]`를 숫자 변환 없이 곱셈한다. 상류 `validate()`에서 비정형 score가 살아남으면 가중치 단계에서 즉시 예외가 발생한다.

**문제 코드**:
```python
raw_score = item_data.get("score", 0)
max_score = item_data.get("max", 0)
weight = weights.get(item_name, 1.0)
weighted_score = raw_score * weight
```

**호출 체인**: `ScoringValidator.validate_v59()` (`modules/validation/scoring_validator.py:717`) → 가중치 계산 (`modules/validation/scoring_validator.py:752`)

**수정 제안**:
```python
try:
    raw_score = float(item_data.get("score", 0))
    max_score = float(item_data.get("max", 0))
except (TypeError, ValueError):
    raw_score, max_score = 0.0, 0.0
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 42 완료

## Round 43 — modules/validation/pre_llm_validator.py

### 진행 통계 업데이트
- 총 발견: 33건 (CRITICAL: 0, HIGH: 30, MEDIUM: 3)
- 라운드 진행: 43/100

### 5-A. 파일 구조 요약
- `modules/validation/pre_llm_validator.py:28` `class PreLLMValidator` — LLM 이전 사전 점검.
- `modules/validation/pre_llm_validator.py:43` `def validate(self, manuscript: str, context: dict[str, Any] = None) -> dict` — 10개 사전검사 집계.
- `modules/validation/pre_llm_validator.py:348` `def _check_npc_naming(self, manuscript: str, context: dict) -> dict` — NPC 이름 일관성 검사.
- `modules/validation/pre_llm_validator.py:428` `def _check_pov_consistency(self, manuscript: str) -> dict` — 시점 일관성 검사.
- `modules/validation/pre_llm_validator.py:464` `def get_summary(self, result: dict) -> str` — 결과 요약 문자열.

### 5-D. 읽기 증명
1. 마지막 함수: `def get_summary(self, result: dict) -> str` (`modules/validation/pre_llm_validator.py:464`)
2. 특징 문자열: `"passed": True,  # [V60.56] 항상 통과, LLM이 최종 판단` (`modules/validation/pre_llm_validator.py:130`)
3. import 목록:
- `from modules.validation.threshold_helper import _threshold` (`modules/validation/pre_llm_validator.py:25`)
- 표준 라이브러리 import: `re`, `collections.Counter`, `typing.Any` (`modules/validation/pre_llm_validator.py:21`~`modules/validation/pre_llm_validator.py:23`)
- 함수 내부 import: `import statistics` (`modules/validation/pre_llm_validator.py:188`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `context = context or {}` (`modules/validation/pre_llm_validator.py:59`) + `npc_profiles = context.get("npc_profiles", {})` (`modules/validation/pre_llm_validator.py:351`)
- 호출자: `ValidationOrchestrator.validate()` → `self.pre_llm.validate(manuscript, validation_context)` (`modules/validation/validation_orchestrator.py:241`)
- 상류/하류 컨텍스트:
- 상류: 인자 타입 강제 없음.
- 하류: `_check_npc_naming(manuscript, context)` (`modules/validation/pre_llm_validator.py:107`)
- 실패 시나리오: context가 truthy 비dict면 `.get` AttributeError.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `pattern = re.escape(correct_name[:i]) + r"[가-힣]" + re.escape(correct_name[i + 1 :])` (`modules/validation/pre_llm_validator.py:375`)
- 호출자: `_check_npc_naming()` (`modules/validation/pre_llm_validator.py:348`)
- 상류/하류 컨텍스트:
- 상류: `correct_names`는 `npc_profiles`/`encyclopedia`에서 수집 (`modules/validation/pre_llm_validator.py:351`~`modules/validation/pre_llm_validator.py:361`)
- 하류: `inconsistencies` 경고 리스트에 기록 (`modules/validation/pre_llm_validator.py:385`)
- 실패 시나리오: 1글자 치환 패턴이 동명이/유사명 일반 단어를 과탐지해 경고 품질 저하.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `no_dialogue = re.sub(r'["""][^"""]*["""]', "", manuscript)` (`modules/validation/pre_llm_validator.py:430`)
- 호출자: `validate()`의 POV 검사 분기 (`modules/validation/pre_llm_validator.py:119`)
- 상류/하류 컨텍스트:
- 상류: `self.pov` 설정 시에만 실행 (`modules/validation/pre_llm_validator.py:119`)
- 하류: 1인칭/3인칭 카운팅 (`modules/validation/pre_llm_validator.py:435`, `modules/validation/pre_llm_validator.py:436`)
- 실패 시나리오: 중첩/비정형 인용부호 문장에서 대화 제거가 불완전해 오경고 발생 가능.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 43 완료

## Round 44 — modules/validation/blocking_validator.py + blocking_validator_entity_checks.py + blocking_validator_scene_checks.py

### 진행 통계 업데이트
- 총 발견: 35건 (CRITICAL: 0, HIGH: 32, MEDIUM: 3)
- 라운드 진행: 44/100

### 5-A. 파일 구조 요약
- `modules/validation/blocking_validator.py:16` `class BlockingValidator` — Tier-1 블로킹 검증 파사드.
- `modules/validation/blocking_validator.py:55` `def validate(self, manuscript: str, validation_context: dict) -> dict` — 다중 블로킹 체크 실행.
- `modules/validation/blocking_validator_entity_checks.py:12` `class BlockingValidatorEntityChecks` — NPC/아이템/장소 상태 체크.
- `modules/validation/blocking_validator_entity_checks.py:101` `def _check_unowned_item_usage(self, manuscript: str, context: dict) -> dict` — 미획득 아이템 사용 검사.
- `modules/validation/blocking_validator_entity_checks.py:300` `def _check_damaged_item_usage(self, manuscript: str, context: dict) -> dict` — 파손/분실 아이템 사용 검사.
- `modules/validation/blocking_validator_scene_checks.py:15` `class BlockingValidatorSceneChecks` — 씬 구조/완성도/엔딩 체크.
- `modules/validation/blocking_validator_scene_checks.py:82` `def _check_scope_overflow(self, manuscript: str, context: dict) -> dict` — 씬 수 대비 과잉 분량 검사.
- `modules/validation/blocking_validator_scene_checks.py:231` `def _check_cliffhanger_ending(self, manuscript: str, context: dict) -> dict` — 클리프행어 엔딩 검사.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def _get_strength_grade(self, score: int) -> str` (`modules/validation/blocking_validator_scene_checks.py:444`)
- `def _check_destroyed_location_visit(self, manuscript: str, context: dict) -> dict` (`modules/validation/blocking_validator_entity_checks.py:445`)
2. 특징 문자열:
- `[V66.1] BlockingValidator: justification checks disabled` (`modules/validation/blocking_validator.py:25`)
- `"check": "scope_overflow", "passed": True, "reason": "씬 개수 추출 불가 - 체크 스킵"` (`modules/validation/blocking_validator_scene_checks.py:116`)
3. import 목록:
- `from modules.validation.blocking_validator_entity_checks import BlockingValidatorEntityChecks` (`modules/validation/blocking_validator.py:34`)
- `from modules.validation.blocking_validator_scene_checks import BlockingValidatorSceneChecks` (`modules/validation/blocking_validator.py:42`)
- `from modules.validation.blocking_validator_consistency_checks import BlockingValidatorConsistencyChecks` (`modules/validation/blocking_validator.py:50`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `aliases = npc.get("aliases", [])` (`modules/validation/blocking_validator_entity_checks.py:67`) + `for identifier in [name] + aliases:` (`modules/validation/blocking_validator_entity_checks.py:69`)
- 호출자: `BlockingValidator.validate()` → `_check_dead_npc_resurrection()` (`modules/validation/blocking_validator.py:60`, `modules/validation/blocking_validator_entity_checks.py:58`)
- 상류/하류 컨텍스트:
- 상류: `npcs = encyclopedia.get("npcs", [])` (`modules/validation/blocking_validator_entity_checks.py:61`)
- 하류: 식별자 주변 행동 패턴 검사 (`modules/validation/blocking_validator_entity_checks.py:89`)
- 실패 시나리오: aliases가 list가 아니면 list concat TypeError.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `all_items = encyclopedia.get("items", [])` (`modules/validation/blocking_validator_entity_checks.py:150`) + `item_name = item.get("name", "")` (`modules/validation/blocking_validator_entity_checks.py:153`)
- 호출자: `BlockingValidator.validate()` → `_check_unowned_item_usage()` (`modules/validation/blocking_validator.py:64`, `modules/validation/blocking_validator_entity_checks.py:101`)
- 상류/하류 컨텍스트:
- 상류: encyclopedia는 외부 상태/LLM 조립 데이터.
- 하류: 별칭 포함 소유 아이템 판정 (`modules/validation/blocking_validator_entity_checks.py:167`)
- 실패 시나리오: `items` 원소가 dict가 아니면 `.get` AttributeError.
- 판정: BUG.

3. 위험 지점
- 코드 원문: `if validation_context.get("mode") == "MANUSCRIPT":` (`modules/validation/blocking_validator.py:75`)
- 호출자: `ValidationOrchestrator.validate()`에서 `blocking.validate(...)` (`modules/validation/validation_orchestrator.py:303`)
- 상류/하류 컨텍스트:
- 상류: validation_context 타입 가드 없음.
- 하류: 필수 씬/범위/엔딩 체크 분기 (`modules/validation/blocking_validator.py:77`~`modules/validation/blocking_validator.py:124`)
- 실패 시나리오: validation_context 비dict면 `.get` AttributeError.
- 판정: RISK (Design Check Needed).

4. 위험 지점
- 코드 원문: `max_allowed_length = scene_count * max_chars_per_scene` + `overflow_ratio = manuscript_length / max_allowed_length` (`modules/validation/blocking_validator_scene_checks.py:123`, `modules/validation/blocking_validator_scene_checks.py:127`)
- 호출자: `BlockingValidator.validate()` → `_check_scope_overflow()` (`modules/validation/blocking_validator.py:82`)
- 상류/하류 컨텍스트:
- 상류: `max_chars_per_scene = _threshold("scope.chars_per_scene", 1500)` (`modules/validation/blocking_validator_scene_checks.py:122`)
- 하류: overflow 판정 및 REJECT/경고 반환 (`modules/validation/blocking_validator_scene_checks.py:131`, `modules/validation/blocking_validator_scene_checks.py:146`)
- 실패 시나리오: 임계값이 0으로 설정되면 0 나누기.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/validation/blocking_validator_entity_checks.py:69 — aliases 비리스트 유입 시 사망 NPC 체크 TypeError

**문제**: 사망 NPC 별칭을 리스트로 가정하고 결합한다. `aliases`가 문자열/None이면 즉시 TypeError가 난다.

**문제 코드**:
```python
aliases = npc.get("aliases", [])
for identifier in [name] + aliases:
    ...
```

**호출 체인**: `BlockingValidator.validate()` (`modules/validation/blocking_validator.py:60`) → `_check_dead_npc_resurrection()` (`modules/validation/blocking_validator_entity_checks.py:58`)

**수정 제안**:
```python
aliases_raw = npc.get("aliases", [])
aliases = aliases_raw if isinstance(aliases_raw, list) else [str(aliases_raw)] if aliases_raw else []
for identifier in [name] + aliases:
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [HIGH] modules/validation/blocking_validator_entity_checks.py:153 — items 원소 타입 무가드 `.get`로 AttributeError

**문제**: `encyclopedia.items` 원소를 dict로 가정하고 `.get`을 호출한다. 문자열/숫자 원소가 섞이면 크래시한다.

**문제 코드**:
```python
all_items = encyclopedia.get("items", [])
for item in all_items:
    item_name = item.get("name", "")
    item_aliases = item.get("aliases", [])
```

**호출 체인**: `BlockingValidator.validate()` (`modules/validation/blocking_validator.py:64`) → `_check_unowned_item_usage()` (`modules/validation/blocking_validator_entity_checks.py:101`)

**수정 제안**:
```python
for item in all_items:
    if not isinstance(item, dict):
        continue
    item_name = item.get("name", "")
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 44 완료

## Round 45 — modules/validation/blocking_validator_consistency_checks.py + modules/validation/consistency_validator.py

### 진행 통계 업데이트
- 총 발견: 36건 (CRITICAL: 0, HIGH: 33, MEDIUM: 3)
- 라운드 진행: 45/100

### 5-A. 파일 구조 요약
- `modules/validation/blocking_validator_consistency_checks.py:22` `class BlockingValidatorConsistencyChecks` — 정당화/관계/정보 일관성 보조 검사.
- `modules/validation/blocking_validator_consistency_checks.py:28` `def _check_physical_capability(...) -> dict` — 신체 제약 검사.
- `modules/validation/blocking_validator_consistency_checks.py:137` `def _check_authority_exercise(...) -> dict` — 권위 행사 검사.
- `modules/validation/consistency_validator.py:16` `class ConsistencyValidator` — Tier 1.5 일관성 총괄.
- `modules/validation/consistency_validator.py:75` `def validate(self, manuscript: str, validation_context: dict) -> dict` — 카테고리별 위반 집계.
- `modules/validation/consistency_validator.py:333` `def _check_effect_consistency(self, manuscript: str, asset_library: dict) -> dict` — 아이템/기술 효능 검사.
- `modules/validation/consistency_validator.py:513` `def _generate_feedback(...) -> str` — 결과 피드백 조립.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def _extract_keywords(self, text: str, max_keywords: int = 3) -> list[str]` (`modules/validation/blocking_validator_consistency_checks.py:366`)
- `def create_consistency_validator(guard=None, genre: str = "wuxia")` (`modules/validation/consistency_validator.py:595`)
2. 특징 문자열:
- `logging.warning(f"[C-3] relationship consistency check failed (degraded): {e}")` (`modules/validation/blocking_validator_consistency_checks.py:292`)
- `"message": "REJECT - 정당화 불가능한 일관성 위반"` (`modules/validation/consistency_validator.py:251`)
3. import 목록:
- `from modules.core.justification_patterns import get_justification_guide, get_pattern_description` (`modules/validation/blocking_validator_consistency_checks.py:14`)
- 표준 라이브러리 import: `logging`, `re` (`modules/validation/blocking_validator_consistency_checks.py:5`, `modules/validation/consistency_validator.py:12`)
- 동적 import: `from modules.core.relationship_tracker import RelationshipTracker` (`modules/validation/blocking_validator_consistency_checks.py:251`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `cannot_be_used_for = item_data.get("cannot_be_used_for", [])` (`modules/validation/consistency_validator.py:358`) + `for forbidden_use in cannot_be_used_for:` (`modules/validation/consistency_validator.py:362`)
- 호출자: `validate()` → `_check_effect_consistency()` (`modules/validation/consistency_validator.py:148`, `modules/validation/consistency_validator.py:333`)
- 상류/하류 컨텍스트:
- 상류: `asset_library`는 validation_context/Guard 동적 규칙에서 유입 (`modules/validation/consistency_validator.py:146`, `modules/validation/consistency_validator.py:343`)
- 하류: use pattern 생성 및 위반 누적 (`modules/validation/consistency_validator.py:366`~`modules/validation/consistency_validator.py:387`)
- 실패 시나리오: `cannot_be_used_for`가 None이면 iterable 아님 TypeError.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `except Exception as e: ... return {"check": "relationship_consistency", "passed": True, "degraded": True, ...}` (`modules/validation/blocking_validator_consistency_checks.py:291`~`modules/validation/blocking_validator_consistency_checks.py:293`)
- 호출자: `BlockingValidator.validate()` (`modules/validation/blocking_validator.py:90`)
- 상류/하류 컨텍스트:
- 상류: tracker/diffusion 내부 오류 가능.
- 하류: 파사드에서 degraded warning만 기록 후 PASS 유지 (`modules/validation/blocking_validator.py:90`~`modules/validation/blocking_validator.py:104`)
- 실패 시나리오: 관계/정보 검사 전체 실패가 최종 PASS로 흘러 실제 모순을 놓칠 수 있음.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `martial_hud = validation_context.get("martial_hud", {})` (`modules/validation/consistency_validator.py:106`)
- 호출자: `ValidationOrchestrator.validate()` consistency 단계 (`modules/validation/validation_orchestrator.py:327`)
- 상류/하류 컨텍스트:
- 상류: validation_context 타입 가드 없음.
- 하류: `actual_truth.get(...)` 연쇄 접근 (`modules/validation/consistency_validator.py:109`, `modules/validation/consistency_validator.py:136`)
- 실패 시나리오: validation_context 비dict면 `.get` AttributeError.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/validation/consistency_validator.py:362 — `cannot_be_used_for` None 처리 누락으로 TypeError

**문제**: 효능 검증에서 금지 용도 목록을 iterable로 가정한다. YAML/DB에서 `null`이 들어오면 루프 진입 시 TypeError가 발생한다.

**문제 코드**:
```python
cannot_be_used_for = item_data.get("cannot_be_used_for", [])
...
for forbidden_use in cannot_be_used_for:
```

**호출 체인**: `ConsistencyValidator.validate()` (`modules/validation/consistency_validator.py:75`) → `_check_effect_consistency()` (`modules/validation/consistency_validator.py:333`)

**수정 제안**:
```python
cannot_be_used_for = item_data.get("cannot_be_used_for", [])
if not isinstance(cannot_be_used_for, list):
    cannot_be_used_for = []
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 45 완료

## Round 46 — modules/validation/continuity_validator.py

### 진행 통계 업데이트
- 총 발견: 37건 (CRITICAL: 0, HIGH: 33, MEDIUM: 4)
- 라운드 진행: 46/100

### 5-A. 파일 구조 요약
- `modules/validation/continuity_validator.py:24` `class ContinuityValidator` — 에피소드 연속성 검증기.
- `modules/validation/continuity_validator.py:72` `def validate(self, current_ep: int, manuscript: str, validation_context: dict, prev_hud: dict | None = None) -> dict` — 연속성 종합 엔트리.
- `modules/validation/continuity_validator.py:272` `def _check_item_continuity(...) -> dict` — 아이템 중복획득 검사.
- `modules/validation/continuity_validator.py:380` `def _check_injury_continuity(...) -> dict` — 부상 연속성 검사.
- `modules/validation/continuity_validator.py:540` `def _check_location_continuity(...) -> dict` — 위치 순간이동 검사.
- `modules/validation/continuity_validator.py:726` `def _check_personality_continuity(...) -> dict` — NPC 성격 연속성 검사.
- `modules/validation/continuity_validator.py:874` `def _check_time_consistency(...) -> dict` — 시간 일관성 검사.
- `modules/validation/continuity_validator.py:936` `def check_frustration_streak(self, ep_num: int) -> list[str]` — 좌절 연속 경고.

### 5-D. 읽기 증명
1. 마지막 함수: `def check_frustration_streak(self, ep_num: int) -> list[str]` (`modules/validation/continuity_validator.py:936`)
2. 특징 문자열: `warnings.append({"type": "no_prev_hud", "message": "직전 HUD 없음 - 연속성 검증 제한적"})` (`modules/validation/continuity_validator.py:113`)
3. import 목록:
- `from modules.validation.threshold_helper import _threshold` (`modules/validation/continuity_validator.py:21`)
- 표준 라이브러리 import: `logging`, `re` (`modules/validation/continuity_validator.py:18`, `modules/validation/continuity_validator.py:19`)
- 함수 내부 import: `import json` (`modules/validation/continuity_validator.py:202`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `personality_changes = [h for h in reversed(history_entries) if ...]` (`modules/validation/continuity_validator.py:845`) + `prev = personality_changes[-2]` / `curr = personality_changes[-1]` (`modules/validation/continuity_validator.py:851`, `modules/validation/continuity_validator.py:852`)
- 호출자: `validate()` → `_check_personality_continuity()` (`modules/validation/continuity_validator.py:153`, `modules/validation/continuity_validator.py:726`)
- 상류/하류 컨텍스트:
- 상류: `npc_history` 변경 이력 리스트 (`modules/validation/continuity_validator.py:834`)
- 하류: 급변 위반 추가 (`modules/validation/continuity_validator.py:856`)
- 실패 시나리오: reversed 후 `[-2],[-1]`를 쓰면 최신 2개가 아닌 가장 오래된 2개를 비교해 최근 급변을 누락.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `if martial_hud: return martial_hud  # 현재 HUD를 이전으로 가정` (`modules/validation/continuity_validator.py:212`, `modules/validation/continuity_validator.py:214`)
- 호출자: `validate()`의 prev_hud fallback (`modules/validation/continuity_validator.py:108`)
- 상류/하류 컨텍스트:
- 상류: DB 조회 실패/부재 시 fallback 경로.
- 하류: item/weapon/injury/location 연속성 검사 전체 (`modules/validation/continuity_validator.py:119`~`modules/validation/continuity_validator.py:148`)
- 실패 시나리오: 이전 HUD 대신 현재 HUD를 사용해 연속성 위반을 은폐.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `sorted_history = sorted(history, key=lambda x: x.get("ep_num", 0), reverse=True)` (`modules/validation/continuity_validator.py:955`)
- 호출자: `check_frustration_streak()` (`modules/validation/continuity_validator.py:936`)
- 상류/하류 컨텍스트:
- 상류: `db.get_recent_satisfaction_tags(...)` 반환 자료형 (`modules/validation/continuity_validator.py:951`)
- 하류: `for tag in reversed(tags): if tag.get("frustration_flag") ...` (`modules/validation/continuity_validator.py:963`)
- 실패 시나리오: history/tags 원소가 dict가 아니면 `.get` AttributeError.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [MEDIUM] modules/validation/continuity_validator.py:851 — NPC 성격 급변 비교가 최신 이력이 아닌 과거 이력 쌍을 참조

**문제**: 성격 이력 리스트를 `reversed()` 한 뒤 `[-2], [-1]`를 사용해 비교한다. 실제 최근 변화가 아니라 오래된 두 변경을 비교하게 되어 최신 급변을 놓친다.

**문제 코드**:
```python
personality_changes = [
    h for h in reversed(history_entries)
    if isinstance(h, dict) and h.get("field_name") == "personality_traits"
]
if len(personality_changes) >= 2:
    prev = personality_changes[-2]
    curr = personality_changes[-1]
```

**호출 체인**: `ContinuityValidator.validate()` (`modules/validation/continuity_validator.py:72`) → `_check_personality_continuity()` (`modules/validation/continuity_validator.py:726`)

**수정 제안**:
```python
recent_two = personality_changes[:2]
prev, curr = recent_two[1], recent_two[0]
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 46 완료

## Round 47 — modules/validation/batch_validator.py + modules/validation/retrospective_validator.py + modules/validation/advisory_validator.py

### 진행 통계 업데이트
- 총 발견: 39건 (CRITICAL: 0, HIGH: 35, MEDIUM: 4)
- 라운드 진행: 47/100

### 5-A. 파일 구조 요약
- `modules/validation/batch_validator.py:16` `class BatchValidator` — 배치 검증(비동기/동기) 실행기.
- `modules/validation/batch_validator.py:38` `async def validate_batch_async(...)` — asyncio 기반 병렬 검증.
- `modules/validation/batch_validator.py:103` `def validate_batch_sync(...)` — ThreadPool 기반 병렬 검증.
- `modules/validation/batch_validator.py:238` `def validate_manuscripts_in_batch(...)` — 실행 환경별 진입점.
- `modules/validation/retrospective_validator.py:12` `class RetrospectiveValidator` — 장기 일관성 회고 검증.
- `modules/validation/retrospective_validator.py:32` `def validate_long_term_consistency(...) -> dict` — 장기 검증 종합.
- `modules/validation/retrospective_validator.py:253` `def _get_past_realms(...) -> list[dict]` — 과거 경지 조회.
- `modules/validation/advisory_validator.py:11` `class AdvisoryValidator` — 통과에 영향 없는 제안 생성.
- `modules/validation/advisory_validator.py:31` `def validate(...) -> dict` — advisory 제안 집계.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def validate_manuscripts_in_batch(...)` (`modules/validation/batch_validator.py:238`)
- `def _calculate_severity(self, violations: list[dict]) -> str` (`modules/validation/retrospective_validator.py:346`)
- `def _suggest_foreshadowing_opportunities(self, manuscript: str) -> list[dict]` (`modules/validation/advisory_validator.py:163`)
2. 특징 문자열:
- `logging.warning("[Sweep7-A] batch validation failed for item %d: %s", i, r)` (`modules/validation/batch_validator.py:87`)
- `_logger.warning("[RetrospectiveValidator] _get_past_items DB 읽기 실패", exc_info=True)` (`modules/validation/retrospective_validator.py:290`)
- `"passed": True,  # 항상 PASS` (`modules/validation/advisory_validator.py:60`)
3. import 목록:
- `from concurrent.futures import ThreadPoolExecutor` (`modules/validation/batch_validator.py:12`)
- 표준 라이브러리 import: `asyncio`, `logging`, `threading`, `time`, `re` (`modules/validation/batch_validator.py`, `modules/validation/retrospective_validator.py`)
- `from modules.validation.threshold_helper import _threshold` (`modules/validation/advisory_validator.py:8`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `except Exception as e: ... return {"ep_num": ms_data["ep_num"], "error": str(e), "success": False}` (`modules/validation/batch_validator.py:77`, `modules/validation/batch_validator.py:130`)
- 호출자: `validate_batch_async()`/`validate_batch_sync()` 내부 `validate_one()` (`modules/validation/batch_validator.py:57`, `modules/validation/batch_validator.py:119`)
- 상류/하류 컨텍스트:
- 상류: `ms_data`는 외부 입력 리스트 원소.
- 하류: sync 경로는 `executor.map(validate_one, manuscripts)` (`modules/validation/batch_validator.py:134`)
- 실패 시나리오: 예외 처리 블록에서 다시 `ms_data["ep_num"]` 접근하여 재예외 발생, sync 배치 전체 중단 가능.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `ms_data = self.context.db.get_manuscript(ep)` (`modules/validation/retrospective_validator.py:260`) + `hud = ms_data.get("hud_snapshot", {})` (`modules/validation/retrospective_validator.py:263`) + `if isinstance(hud, dict):` (`modules/validation/retrospective_validator.py:264`)
- 호출자: `_check_realm_regression()`/`_check_item_disappearance()` (`modules/validation/retrospective_validator.py:87`, `modules/validation/retrospective_validator.py:181`)
- 상류/하류 컨텍스트:
- 상류: DB는 `get_manuscript()`에서 `SELECT * FROM manuscripts` row dict 반환 (`modules/core/db_manager.py:410`, `modules/core/db_manager.py:412`)
- 하류: 과거 realm/items 이력 누적 (`modules/validation/retrospective_validator.py:266`, `modules/validation/retrospective_validator.py:286`)
- 실패 시나리오: manuscripts 테이블 row에 `hud_snapshot`가 없어 과거 이력이 항상 비어 장기 회귀 검증이 사실상 비활성화.
- 판정: BUG.

3. 위험 지점
- 코드 원문: `self.stats["total_manuscripts"] = len(manuscripts)`만 갱신하고 `completed`/`failed` 초기화 없음 (`modules/validation/batch_validator.py:54`, `modules/validation/batch_validator.py:117`)
- 호출자: 반복 배치 실행 시 `validate_batch_async()`/`validate_batch_sync()`
- 상류/하류 컨텍스트:
- 상류: 인스턴스 재사용 시 기존 stats 잔존.
- 하류: `get_statistics()`/`print_report()` 리포트 (`modules/validation/batch_validator.py:143`, `modules/validation/batch_validator.py:165`)
- 실패 시나리오: 배치별 성공/실패 수치가 누적되어 운영 지표 왜곡.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/validation/batch_validator.py:130 — 예외 처리에서 `ep_num` 재접근으로 재예외 발생 (sync 배치 중단)

**문제**: 실패 처리를 하면서 동일한 취약 접근(`ms_data["ep_num"]`)을 다시 수행한다. 입력 원소가 비정형일 경우 except 내부에서 또 예외가 발생한다.

**문제 코드**:
```python
except Exception as e:
    with self._stats_lock:
        self.stats["failed"] += 1
    return {"ep_num": ms_data["ep_num"], "error": str(e), "success": False}
```

**호출 체인**: `validate_batch_sync()` (`modules/validation/batch_validator.py:103`) → `validate_one()` (`modules/validation/batch_validator.py:119`) → `executor.map()` (`modules/validation/batch_validator.py:134`)

**수정 제안**:
```python
ep_num = ms_data.get("ep_num", -1) if isinstance(ms_data, dict) else -1
return {"ep_num": ep_num, "error": str(e), "success": False}
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [HIGH] modules/validation/retrospective_validator.py:263 — 과거 HUD 조회 키 불일치로 장기 회귀 검증이 사실상 비활성화

**문제**: 과거 경지/아이템 조회가 `manuscripts` row에서 `hud_snapshot`을 기대한다. 그러나 DB 조회는 `SELECT * FROM manuscripts`를 반환하며 해당 키가 보장되지 않는다.

**문제 코드**:
```python
ms_data = self.context.db.get_manuscript(ep)
if ms_data and isinstance(ms_data, dict):
    hud = ms_data.get("hud_snapshot", {})
    if isinstance(hud, dict):
        realm = hud.get("realm", "")
```

**호출 체인**: `validate_long_term_consistency()` (`modules/validation/retrospective_validator.py:32`) → `_check_realm_regression()` (`modules/validation/retrospective_validator.py:78`) / `_check_item_disappearance()` (`modules/validation/retrospective_validator.py:174`) → `_get_past_realms()` (`modules/validation/retrospective_validator.py:253`) / `_get_past_items()` (`modules/validation/retrospective_validator.py:273`)

**수정 제안**:
```python
# manuscripts가 아닌 별도 HUD 저장소/state_log에서 조회하거나,
# manuscripts row에 저장된 JSON 필드 구조를 명시적으로 파싱
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 47 완료

## Round 48 — modules/validation/action_scene_evaluator.py + modules/validation/catharsis_timer.py + modules/validation/threshold_helper.py

### 진행 통계 업데이트
- 총 발견: 39건 (CRITICAL: 0, HIGH: 35, MEDIUM: 4)
- 라운드 진행: 48/100

### 5-A. 파일 구조 요약
- `modules/validation/action_scene_evaluator.py:10` `class ActionSceneEvaluator` — 액션 씬 품질 평가기.
- `modules/validation/action_scene_evaluator.py:134` `def evaluate(self, manuscript: str, context: dict = None) -> dict` — 액션 종합 점수 계산.
- `modules/validation/action_scene_evaluator.py:254` `def evaluate_power_consistency(self, manuscript: str, context: dict) -> dict` — 기술 효과 일관성 검사.
- `modules/validation/action_scene_evaluator.py:344` `def _extract_action_scenes(self, manuscript: str) -> list[str]` — 액션 씬 추출.
- `modules/validation/catharsis_timer.py:9` `class CatharsisTimer` — 카타르시스 타이밍 분석기.
- `modules/validation/catharsis_timer.py:72` `def check_catharsis_timing(...) -> dict` — 카타르시스 상태 판정.
- `modules/validation/catharsis_timer.py:165` `def _count_frustration_streak(self, history: list[dict]) -> int` — 좌절 연속 카운트.
- `modules/validation/threshold_helper.py:10` `def _threshold(key: str, default: Any) -> Any` — validation 전용 임계값 헬퍼.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def _measure_stakes(self, scene: str) -> float` (`modules/validation/action_scene_evaluator.py:438`)
- `def record_episode(self, ep_num: int, manuscript: str) -> dict` (`modules/validation/catharsis_timer.py:214`)
- `def _threshold(key: str, default: Any) -> Any` (`modules/validation/threshold_helper.py:10`)
2. 특징 문자열:
- `"total_score": 10,  # 액션 없으면 만점 (감점 사유 없음)` (`modules/validation/action_scene_evaluator.py:159`)
- `return "독자 이탈 위험! 이번 화에 반드시 명확한 승리/보상 장면 필요."` (`modules/validation/catharsis_timer.py:184`)
3. import 목록:
- `import re` (`modules/validation/action_scene_evaluator.py:7`)
- `from modules.core.config_manager import ConfigManager` (함수 내부 동적 import, `modules/validation/threshold_helper.py:14`)
- `from typing import Any` (`modules/validation/threshold_helper.py:7`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `if not action_scenes: return {"total_score": 10, ...}` (`modules/validation/action_scene_evaluator.py:157`~`modules/validation/action_scene_evaluator.py:164`)
- 호출자: `ValidationOrchestrator`의 action evaluator 경로(액션 점수 보정 구간)
- 상류/하류 컨텍스트:
- 상류: `_extract_action_scenes()` 임계값 기반 추출 (`modules/validation/action_scene_evaluator.py:344`)
- 하류: 총점 보정/피드백 반영 (`modules/validation/action_scene_evaluator.py:174`~`modules/validation/action_scene_evaluator.py:197`)
- 실패 시나리오: 액션 중심 장르에서 추출 실패 시도에도 만점 처리되어 품질 저하를 가림.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `sorted_history = sorted(history, key=lambda x: x.get("ep_num", 0), reverse=True)` (`modules/validation/catharsis_timer.py:171`)
- 호출자: `check_catharsis_timing()` (`modules/validation/catharsis_timer.py:102`)
- 상류/하류 컨텍스트:
- 상류: history 인자 타입 강제 없음 (`modules/validation/catharsis_timer.py:72`)
- 하류: 연속 좌절 카운트 기반 status 판정 (`modules/validation/catharsis_timer.py:103`~`modules/validation/catharsis_timer.py:120`)
- 실패 시나리오: history 원소가 dict가 아니면 `.get` AttributeError.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `_threshold._cfg = ConfigManager()` 1회 캐싱 후 재사용 (`modules/validation/threshold_helper.py:12`~`modules/validation/threshold_helper.py:21`)
- 호출자: scoring/pre_llm/blocking/continuity/advisory 전반 `_threshold(...)` 호출부
- 상류/하류 컨텍스트:
- 상류: 런타임 중 validation.yaml 변경 가능성.
- 하류: 모든 임계값 판정이 캐시된 `_cfg`에 의존.
- 실패 시나리오: 설정 핫리로드가 필요한 운영에서 임계값 변경이 즉시 반영되지 않음.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 48 완료

## Round 49 — modules/domain/agents/state_tracker.py

### 진행 통계 업데이트
- 총 발견: 40건 (CRITICAL: 0, HIGH: 36, MEDIUM: 4)
- 라운드 진행: 49/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/state_tracker.py:41` `class EpisodeState` — 에피소드 상태 스냅샷 데이터 모델.
- `modules/domain/agents/state_tracker.py:96` `class StateTracker` — 상태 추적/검증 파사드.
- `modules/domain/agents/state_tracker.py:465` `def load_arc_design(self, tactical_doc: dict) -> bool` — Arc 문서 기반 상태 로딩.
- `modules/domain/agents/state_tracker.py:537` `def _parse_episode_state(self, ep_num: int, ep_data: dict, checkpoints: list)` — 회차별 상태 파싱.
- `modules/domain/agents/state_tracker.py:577` `def _extract_state_from_text(self, state: EpisodeState, text: str)` — 텍스트 기반 상태 추출.
- `modules/domain/agents/state_tracker.py:681` `def validate_timeline(self) -> list[dict]` — 타임라인 이슈 검증.
- `modules/domain/agents/state_tracker.py:1432` `def create_tracker_from_arcs(arcs_data: list[dict]) -> StateTracker` — 다중 Arc 통합 트래커 생성.

### 5-D. 읽기 증명
1. 마지막 함수: `def create_tracker_from_arcs(arcs_data: list[dict]) -> StateTracker` (`modules/domain/agents/state_tracker.py:1432`)
2. 특징 문자열: `logging.warning(f"⚠️ [StateTracker] Arc 설계 로드 실패: {e}")` (`modules/domain/agents/state_tracker.py:534`)
3. import 목록:
- `from modules.domain.agents.state_tracker_financial import StateTrackerFinancial` (`modules/domain/agents/state_tracker.py:24`)
- `from modules.domain.agents.state_tracker_npc import StateTrackerNPC` (`modules/domain/agents/state_tracker.py:27`)
- `from modules.domain.agents.state_tracker_plots import StateTrackerPlots` (`modules/domain/agents/state_tracker.py:28`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `for item in items_acquired:` ... `self.acquired_items[item] = acq_ep` (`modules/domain/agents/state_tracker.py:517`, `modules/domain/agents/state_tracker.py:521`)
- 호출자: `create_tracker_from_arcs()` → `arc_tracker.load_arc_design(arc_doc)` (`modules/domain/agents/state_tracker.py:1446`)
- 상류/하류 컨텍스트:
- 상류: `items_acquired = state_constraints.get("items_acquired", [])` (`modules/domain/agents/state_tracker.py:514`)
- 하류: 예외 시 `return False` (`modules/domain/agents/state_tracker.py:535`)
- 실패 시나리오: `items_acquired` 원소가 dict면 unhashable로 `self.acquired_items[item]`에서 TypeError 발생, Arc 로드 자체 실패.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `f"제{ep_num - (ep_num - 1) // 5 * 5}화:" in checkpoint` (`modules/domain/agents/state_tracker.py:570`)
- 호출자: `load_arc_design()` → `_parse_episode_state(...)` (`modules/domain/agents/state_tracker.py:510`, `modules/domain/agents/state_tracker.py:537`)
- 상류/하류 컨텍스트:
- 상류: `base_ep = (arc_no - 1) * 5 + 1` 고정 5화 가정 (`modules/domain/agents/state_tracker.py:492`)
- 하류: `_apply_checkpoint(new_state, checkpoint)` (`modules/domain/agents/state_tracker.py:573`)
- 실패 시나리오: 5화 고정이 아닌 편성에서 체크포인트가 잘못 매칭되어 상태 반영 누락/오적용.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `r"([가-힣]+검|도|창|궁)[을를]?\s*받"` (`modules/domain/agents/state_tracker.py:591`)
- 호출자: `_parse_episode_state()` / `_apply_checkpoint()` → `_extract_state_from_text()` (`modules/domain/agents/state_tracker.py:565`, `modules/domain/agents/state_tracker.py:620`, `modules/domain/agents/state_tracker.py:577`)
- 상류/하류 컨텍스트:
- 상류: `core_events = ep_data.get("core_events", ep_data.get("summary", ""))` (`modules/domain/agents/state_tracker.py:563`)
- 하류: `state.items.append(item)` (`modules/domain/agents/state_tracker.py:597`)
- 실패 시나리오: alternation 우선순위로 단독 `"도"`/`"창"` 등이 잡혀 아이템 오탐 가능.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/domain/agents/state_tracker.py:521 — `items_acquired` 원소가 dict일 때 Arc 로드가 TypeError로 중단

**문제**: `items_acquired`/`items_consumed`를 문자열 전제로 dict key에 바로 사용한다. 구조화된 항목(dict) 입력 시 hash 불가 예외가 발생한다.

**문제 코드**:
```python
for item in items_acquired:
    if item not in self.acquired_items:
        # 획득 에피소드 추정 (checkpoint에서)
        acq_ep = self._find_acquisition_episode(item, checkpoints, base_ep)
        self.acquired_items[item] = acq_ep
```

**호출 체인**: `create_tracker_from_arcs()` (`modules/domain/agents/state_tracker.py:1432`) → `load_arc_design()` (`modules/domain/agents/state_tracker.py:465`)

**수정 제안**:
```python
item_name = item.get("name") if isinstance(item, dict) else str(item)
if item_name and item_name not in self.acquired_items:
    acq_ep = self._find_acquisition_episode(item_name, checkpoints, base_ep)
    self.acquired_items[item_name] = acq_ep
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 49 완료

## Round 50 — modules/domain/agents/state_tracker_npc.py (L1~1000)

### 진행 통계 업데이트
- 총 발견: 41건 (CRITICAL: 0, HIGH: 37, MEDIUM: 4)
- 라운드 진행: 50/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/state_tracker_npc.py:70` `class StateTrackerNPC` — NPC 상태 추적 서브모듈.
- `modules/domain/agents/state_tracker_npc.py:122` `def register_npc_death(...)` — NPC 사망 등록/이력 기록.
- `modules/domain/agents/state_tracker_npc.py:277` `def extract_npc_info_from_arc(self, arc: dict, genre: str = "") -> list[dict]` — tactical_doc 기반 NPC 무장/경지 추출.
- `modules/domain/agents/state_tracker_npc.py:528` `def merge_npc_registry(self, other: "StateTracker")` — 트래커 간 NPC 레지스트리 병합.
- `modules/domain/agents/state_tracker_npc.py:563` `def extract_npc_deaths_from_arc(self, arc: dict) -> list[str]` — 사망 추출(필드 우선 + regex/LLM 폴백).
- `modules/domain/agents/state_tracker_npc.py:789` `def extract_npc_injuries_from_arc(self, arc: dict) -> list[dict]` — 부상 추출.
- `modules/domain/agents/state_tracker_npc.py:981` `def _regex_extract_npc_movements(self, tactical_doc: str) -> list[dict]` — 이동 regex 폴백.

### 5-D. 읽기 증명
1. 마지막 함수: `def cleanup_npc_registry_with_llm(self, arc_no: int) -> list[str]` (`modules/domain/agents/state_tracker_npc.py:1927`)
2. 특징 문자열: `f"      🧹 [V69] NPC 레지스트리 LLM 정리 (Arc {arc_no}): "` (`modules/domain/agents/state_tracker_npc.py:1997`)
3. import 목록:
- `import json` (`modules/domain/agents/state_tracker_npc.py:10`)
- `import logging` (`modules/domain/agents/state_tracker_npc.py:11`)
- `import re` (`modules/domain/agents/state_tracker_npc.py:12`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `filtered = {...}`만 생성하고 else 분기에서 반영 없음 (`modules/domain/agents/state_tracker_npc.py:545`~`modules/domain/agents/state_tracker_npc.py:551`)
- 호출자: `StateTracker.merge_npc_registry()` 위임 (`modules/domain/agents/state_tracker.py:992`) → `create_tracker_from_arcs()` (`modules/domain/agents/state_tracker.py:1448`)
- 상류/하류 컨텍스트:
- 상류: `for name, info in other.npc_registry.items():` (`modules/domain/agents/state_tracker_npc.py:530`)
- 하류: 병합 후 Stage4 검증/요약이 `self.tracker.npc_registry`에 의존
- 실패 시나리오: alive 상태 NPC의 최신 필드가 병합되지 않아 이전 Arc 정보가 고정됨.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `tactical = arc.get("tactical_doc", "")` 후 dict만 문자열화 (`modules/domain/agents/state_tracker_npc.py:296`~`modules/domain/agents/state_tracker_npc.py:298`)
- 호출자: `extract_npc_info_from_arc()` (`modules/domain/agents/state_tracker_npc.py:277`)
- 상류/하류 컨텍스트:
- 상류: `arc`의 `tactical_doc` 타입 강제 없음
- 하류: `matches = re.findall(pattern, tactical)` (`modules/domain/agents/state_tracker_npc.py:317`)
- 실패 시나리오: `tactical_doc`가 list/기타 비문자열이면 regex 호출에서 TypeError 가능.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `_RE_MOVE_FROM_TO`/`_RE_MOVE_TO`에서 `[에서을를]`, `[으로에]` 사용 (`modules/domain/agents/state_tracker_npc.py:36`, `modules/domain/agents/state_tracker_npc.py:37`, `modules/domain/agents/state_tracker_npc.py:39`)
- 호출자: `_regex_extract_npc_movements()` (`modules/domain/agents/state_tracker_npc.py:981`)
- 상류/하류 컨텍스트:
- 상류: 이동 regex 폴백 진입 (`modules/domain/agents/state_tracker_npc.py:863`~`modules/domain/agents/state_tracker_npc.py:871`)
- 하류: 이동 결과를 registry location에 반영 (`modules/domain/agents/state_tracker_npc.py:875`~`modules/domain/agents/state_tracker_npc.py:880`)
- 실패 시나리오: 조사 문자열이 아닌 단일 문자 클래스 매칭으로 from/to 추출 왜곡 또는 누락.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/domain/agents/state_tracker_npc.py:545 — `merge_npc_registry` alive 분기에서 필터링 결과를 실제 병합하지 않음

**문제**: 비사망 분기에서 `filtered`를 만든 뒤 `existing.update(filtered)`가 호출되지 않는다. 결과적으로 해당 분기의 병합이 무효다.

**문제 코드**:
```python
else:
    # [Sweep34] 빈값으로 기존 속성이 덮어쓰기 되는 문제 방지
    # [Sweep64] 0/False도 기존 값 덮어쓰기 방지 (last_arc=0 회귀 등)
    filtered = {
        k: v
        for k, v in info.items()
        if v not in ("", None, [], {})
        and v is not False
        and not (isinstance(v, int) and v == 0 and k in existing and existing[k])
    }
```

**호출 체인**: `create_tracker_from_arcs()` (`modules/domain/agents/state_tracker.py:1432`) → `StateTracker.merge_npc_registry()` (`modules/domain/agents/state_tracker.py:991`) → `StateTrackerNPC.merge_npc_registry()` (`modules/domain/agents/state_tracker_npc.py:528`)

**수정 제안**:
```python
existing.update(filtered)
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 50 완료

## Round 51 — modules/domain/agents/state_tracker_npc.py (L1001~EOF)

### 진행 통계 업데이트
- 총 발견: 41건 (CRITICAL: 0, HIGH: 37, MEDIUM: 4)
- 라운드 진행: 51/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/state_tracker_npc.py:1066` `def extract_permanent_injuries_from_arc(self, arc_data: dict) -> list[dict]` — 영구 부상 추출/등록.
- `modules/domain/agents/state_tracker_npc.py:1229` `def check_dead_npc_in_blueprint(...) -> list[dict]` — Blueprint 내 사망 NPC 재등장 검사.
- `modules/domain/agents/state_tracker_npc.py:1328` `def check_dead_npc_in_manuscript(...) -> list[dict]` — 원고 내 사망 NPC 재등장 검사.
- `modules/domain/agents/state_tracker_npc.py:1541` `def extract_npc_dialogue_styles_from_arc(self, arc: dict) -> list[dict]` — 대화 스타일 추출.
- `modules/domain/agents/state_tracker_npc.py:1625` `def update_companions_from_arc(self, arc_data: dict) -> list[dict]` — 동행자 합류/이탈 반영.
- `modules/domain/agents/state_tracker_npc.py:1769` `def extract_protagonist_emotion_from_arc(self, arc_data: dict) -> dict | None` — 주인공 감정 상태 추출.
- `modules/domain/agents/state_tracker_npc.py:1927` `def cleanup_npc_registry_with_llm(self, arc_no: int) -> list[str]` — NPC 레지스트리 오탐 정리.

### 5-D. 읽기 증명
1. 마지막 함수: `def cleanup_npc_registry_with_llm(self, arc_no: int) -> list[str]` (`modules/domain/agents/state_tracker_npc.py:1927`)
2. 특징 문자열: `logging.warning(f"⚠️ [V69] NPC 레지스트리 LLM 정리 실패 (비차단): {str(e)[:80]}")` (`modules/domain/agents/state_tracker_npc.py:2003`)
3. import 목록:
- `import json` (`modules/domain/agents/state_tracker_npc.py:10`)
- `import logging` (`modules/domain/agents/state_tracker_npc.py:11`)
- `import re` (`modules/domain/agents/state_tracker_npc.py:12`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `content += "\n" + scene.get("content", "")` / `scene.get("summary", "")` (`modules/domain/agents/state_tracker_npc.py:1260`, `modules/domain/agents/state_tracker_npc.py:1261`, `modules/domain/agents/state_tracker_npc.py:1267`, `modules/domain/agents/state_tracker_npc.py:1268`)
- 호출자: `check_dead_npc_in_blueprint()` (`modules/domain/agents/state_tracker_npc.py:1229`)
- 상류/하류 컨텍스트:
- 상류: `scenes`가 dict/list일 때만 분기 (`modules/domain/agents/state_tracker_npc.py:1257`, `modules/domain/agents/state_tracker_npc.py:1264`)
- 하류: `self._is_standalone_name(npc_name, content)` 검사 (`modules/domain/agents/state_tracker_npc.py:1282`)
- 실패 시나리오: scene 필드가 list/dict면 문자열 덧셈 TypeError로 검사가 중단될 수 있음.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `self.update_protagonist_emotion(arc_no, arc_no, normalized, trigger_text)` 및 `{"episode": arc_no, ...}` (`modules/domain/agents/state_tracker_npc.py:1839`, `modules/domain/agents/state_tracker_npc.py:1840`)
- 호출자: `extract_protagonist_emotion_from_arc()` regex 폴백 경로 (`modules/domain/agents/state_tracker_npc.py:1769`)
- 상류/하류 컨텍스트:
- 상류: state_changes 감정 정보 부재 시 tactical regex 분기
- 하류: `get_protagonist_emotion_summary()`가 episode 기반 문맥 생성 (`modules/domain/agents/state_tracker_npc.py:1844`)
- 실패 시나리오: Arc 번호를 에피소드 번호로 저장해 timeline/episode 기준 비교가 왜곡됨.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `del self.tracker.npc_registry[name]` (`modules/domain/agents/state_tracker_npc.py:1992`)
- 호출자: `cleanup_npc_registry_with_llm()` (`modules/domain/agents/state_tracker_npc.py:1927`)
- 상류/하류 컨텍스트:
- 상류: 삭제 대상은 alive NPC만 필터링 (`modules/domain/agents/state_tracker_npc.py:1991`)
- 하류: `npc_npc_relationships`/`npc_dialogue_profiles`/`current_companions`는 별도 정리 경로 없음 (`modules/domain/agents/state_tracker_npc.py:1499`, `modules/domain/agents/state_tracker_npc.py:1532`, `modules/domain/agents/state_tracker_npc.py:1676`)
- 실패 시나리오: 교차 레지스트리에 dangling reference가 남아 요약/검증 노이즈 유발.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 51 완료

## Round 52 — modules/domain/agents/state_tracker_plots.py

### 진행 통계 업데이트
- 총 발견: 42건 (CRITICAL: 0, HIGH: 37, MEDIUM: 5)
- 라운드 진행: 52/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/state_tracker_plots.py:55` `class StateTrackerPlots` — 플롯/엔티티/시간선 추적 서브모듈.
- `modules/domain/agents/state_tracker_plots.py:91` `def extract_resolved_plots_from_arc(self, arc: dict) -> list[dict]` — 해결된 플롯 누적.
- `modules/domain/agents/state_tracker_plots.py:237` `def extract_item_states_from_arc(self, arc: dict) -> list[dict]` — 아이템 상태 추출.
- `modules/domain/agents/state_tracker_plots.py:316` `def update_plot_mentions_from_arc(self, arc: dict) -> list[dict]` — 활성 플롯 언급 갱신.
- `modules/domain/agents/state_tracker_plots.py:442` `def extract_time_markers_from_arc(self, arc_data: dict) -> list[dict]` — 시간 마커 추출.
- `modules/domain/agents/state_tracker_plots.py:538` `def check_time_consistency(...) -> list[dict]` — 시간 모순 검사.
- `modules/domain/agents/state_tracker_plots.py:626` `def _regex_extract_major_items(self, tactical_doc: str) -> list[dict]` — 아이템 regex 폴백.
- `modules/domain/agents/state_tracker_plots.py:899` `def check_entity_name_consistency(self, content: str, arc_no: int = 0) -> list[dict]` — 엔티티 명칭 유사도 검사.

### 5-D. 읽기 증명
1. 마지막 함수: `def check_entity_name_consistency(self, content: str, arc_no: int = 0) -> list[dict]` (`modules/domain/agents/state_tracker_plots.py:899`)
2. 특징 문자열: `lines.append("[V66] 방치된 플롯 (재개/해결 필요):")` (`modules/domain/agents/state_tracker_plots.py:396`)
3. import 목록:
- `import logging` (`modules/domain/agents/state_tracker_plots.py:10`)
- `import re` (`modules/domain/agents/state_tracker_plots.py:11`)
- 프로젝트 모듈 import 없음(파일 전수 확인).

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: 획득/분실 폴백이 동일 `seen` 집합 공유 (`modules/domain/agents/state_tracker_plots.py:641`, `modules/domain/agents/state_tracker_plots.py:652`, `modules/domain/agents/state_tracker_plots.py:659`)
- 호출자: `extract_item_states_from_arc()` 폴백 경로 (`modules/domain/agents/state_tracker_plots.py:266`, `modules/domain/agents/state_tracker_plots.py:271`)
- 상류/하류 컨텍스트:
- 상류: `state_changes.major_items` 비어 있을 때 regex 폴백
- 하류: `register_item_state(...)` 갱신 (`modules/domain/agents/state_tracker_plots.py:278`)
- 실패 시나리오: 같은 아이템이 "획득 후 소모"된 Arc에서 두 번째 액션이 누락되어 상태가 편향됨.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `timeline = current_timeline or self.tracker.in_world_timeline` (`modules/domain/agents/state_tracker_plots.py:558`)
- 호출자: `check_time_consistency()` (`modules/domain/agents/state_tracker_plots.py:538`)
- 상류/하류 컨텍스트:
- 상류: 호출자가 `[]`를 명시 전달할 수 있음
- 하류: 계절 모순 판단이 timeline에 의존 (`modules/domain/agents/state_tracker_plots.py:583`)
- 실패 시나리오: 빈 리스트 전달 의도를 무시하고 내부 timeline으로 폴백하여 검사 결과 왜곡.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `if isinstance(tactical, dict): tactical = str(tactical)` (`modules/domain/agents/state_tracker_plots.py:336`, `modules/domain/agents/state_tracker_plots.py:337`)
- 호출자: `update_plot_mentions_from_arc()` (`modules/domain/agents/state_tracker_plots.py:316`)
- 상류/하류 컨텍스트:
- 상류: `tactical_doc`가 구조화 dict인 경우
- 하류: `if plot_name in tactical` 부분 문자열 검사 (`modules/domain/agents/state_tracker_plots.py:343`)
- 실패 시나리오: dict 문자열화 표현(`{'k': 'v'}`)에 의존해 플롯 언급 판정이 노이즈화.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [MEDIUM] modules/domain/agents/state_tracker_plots.py:641 — 아이템 regex 폴백에서 획득/분실 이벤트가 단일 `seen`으로 상호 소거

**문제**: `_regex_extract_major_items()`가 획득/분실 탐지에 같은 `seen`을 써서 동일 아이템의 다중 상태 변화(획득 후 소모)를 동시에 담지 못한다.

**문제 코드**:
```python
items = []
seen = set()

for pattern in acquire_patterns:
    for match in pattern.finditer(tactical_doc):
        name = match.group(1).strip()
        if name and len(name) >= 2 and name not in exclude_words and name not in seen:
            seen.add(name)
            items.append({"name": name, "action": "획득", "episode": 0})

for pattern in lose_patterns:
    for match in pattern.finditer(tactical_doc):
        name = match.group(1).strip()
        if name and len(name) >= 2 and name not in exclude_words and name not in seen:
            seen.add(name)
            items.append({"name": name, "action": "분실", "episode": 0})
```

**호출 체인**: `extract_item_states_from_arc()` (`modules/domain/agents/state_tracker_plots.py:237`) → `_regex_extract_major_items()` (`modules/domain/agents/state_tracker_plots.py:626`)

**수정 제안**:
```python
seen_acquire, seen_lose = set(), set()
# 획득/분실을 별도 dedup 하거나 (name, action) 튜플로 dedup
```

**확신도**: MEDIUM

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 52 완료

## Round 53 — modules/domain/agents/state_extractor.py

### 진행 통계 업데이트
- 총 발견: 44건 (CRITICAL: 0, HIGH: 39, MEDIUM: 5)
- 라운드 진행: 53/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/state_extractor.py:179` `class StateExtractor(BaseAgent)` — Arc 상태 구조화 추출 에이전트.
- `modules/domain/agents/state_extractor.py:201` `def extract_state(self, arc_data: dict) -> dict` — 단일 Arc 추출 엔트리.
- `modules/domain/agents/state_extractor.py:263` `def extract_cumulative_state(self, arcs: list[dict]) -> dict` — 다중 Arc 누적 상태 계산.
- `modules/domain/agents/state_extractor.py:386` `def generate_constraint_prompt(self, state: dict) -> str` — 제약 프롬프트 생성.
- `modules/domain/agents/state_extractor.py:465` `def _validate_and_fix_result(self, result: dict, original_arc: dict) -> dict` — 결과 보정.
- `modules/domain/agents/state_extractor.py:535` `def _fallback_extraction(self, arc_data: dict) -> dict` — Python 폴백 추출.
- `modules/domain/agents/state_extractor.py:660` `def _fallback_entity_extraction(self, text: str) -> dict` — regex 엔티티 추출 폴백.
- `modules/domain/agents/state_extractor.py:824` `def _fallback_satisfaction_tag(self, manuscript: str, ep_num: int) -> dict` — 만족도 태그 폴백.

### 5-D. 읽기 증명
1. 마지막 함수: `def _fallback_satisfaction_tag(self, manuscript: str, ep_num: int) -> dict` (`modules/domain/agents/state_extractor.py:824`)
2. 특징 문자열: `logging.warning(f"[StateExtractor] LLM 추출 실패 (fallback 사용): {e}")` (`modules/domain/agents/state_extractor.py:248`)
3. import 목록:
- `import json` (`modules/domain/agents/state_extractor.py:12`)
- `import logging` (`modules/domain/agents/state_extractor.py:13`)
- `from .base_agent import BaseAgent` (`modules/domain/agents/state_extractor.py:15`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `"tactical_doc": (arc_data.get("tactical_doc") or "")[:3000]` (`modules/domain/agents/state_extractor.py:222`)
- 호출자: `extract_state()` (`modules/domain/agents/state_extractor.py:201`)
- 상류/하류 컨텍스트:
- 상류: `arc_data["tactical_doc"]` 타입 강제 없음
- 하류: 이 코드가 `try` 블록 진입 전 실행됨 (`modules/domain/agents/state_extractor.py:234`)
- 실패 시나리오: `tactical_doc`가 dict/list면 slice에서 TypeError 발생, 폴백 경로로도 복구되지 않고 함수가 즉시 중단.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `all_acquired.extend(inventory)` + `list(set(all_acquired))` (`modules/domain/agents/state_extractor.py:320`, `modules/domain/agents/state_extractor.py:374`)
- 호출자: `extract_cumulative_state()` (`modules/domain/agents/state_extractor.py:263`)
- 상류/하류 컨텍스트:
- 상류: `inventory`는 string/list만 분기하고 list 원소 타입은 검증하지 않음 (`modules/domain/agents/state_extractor.py:316`, `modules/domain/agents/state_extractor.py:319`)
- 하류: 누적 상태 `current_state["cumulative"]` 구성 (`modules/domain/agents/state_extractor.py:373`)
- 실패 시나리오: list 원소에 dict가 섞이면 set 변환에서 unhashable TypeError로 누적 상태 계산 중단.
- 판정: BUG.

3. 위험 지점
- 코드 원문: `if "protagonist_state" not in result: result["protagonist_state"] = {}` (`modules/domain/agents/state_extractor.py:469`, `modules/domain/agents/state_extractor.py:470`)
- 호출자: `extract_state()` 내부 `result = self._validate_and_fix_result(result, arc_data)` (`modules/domain/agents/state_extractor.py:241`)
- 상류/하류 컨텍스트:
- 상류: `_extract_json_robust` 결과가 dict가 아닐 수 있음 (`modules/domain/agents/state_extractor.py:238`)
- 하류: 예외 시 전체 LLM 결과 폐기 후 폴백 (`modules/domain/agents/state_extractor.py:247`)
- 실패 시나리오: list/str 결과에서 보정 단계가 예외를 유발해 실제로 쓸 수 있는 부분 결과도 버려질 수 있음.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/domain/agents/state_extractor.py:222 — `tactical_doc` 비문자열 입력 시 try 블록 밖에서 즉시 크래시

**문제**: `cleaned_data` 구성 단계에서 `tactical_doc`를 무조건 슬라이싱한다. dict/list 입력이면 예외가 발생하며 예외 처리 구간 이전이라 폴백도 동작하지 않는다.

**문제 코드**:
```python
cleaned_data = {
    "arc_no": arc_no,
    "tactical_doc": (arc_data.get("tactical_doc") or "")[:3000],  # 토큰 절약
    "joint_docs": arc_data.get("joint_docs", {}),
    "status_shadow": arc_data.get("status_shadow", {}),
    "state_constraints": arc_data.get("state_constraints", {}),  # [V60.13] arc_end_state 포함
    "beat_sequence": arc_data.get("beat_sequence", []),
}
```

**호출 체인**: `extract_cumulative_state()` (`modules/domain/agents/state_extractor.py:263`) / 직접 호출 → `extract_state()` (`modules/domain/agents/state_extractor.py:201`)

**수정 제안**:
```python
tactical_raw = arc_data.get("tactical_doc", "")
if isinstance(tactical_raw, dict):
    tactical_text = "\n".join(str(v) for v in tactical_raw.values() if v)
elif isinstance(tactical_raw, str):
    tactical_text = tactical_raw
else:
    tactical_text = str(tactical_raw) if tactical_raw else ""
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [HIGH] modules/domain/agents/state_extractor.py:374 — 누적 아이템 dedup에서 dict 혼입 시 `TypeError: unhashable type`

**문제**: `physical_inventory`가 list일 때 원소 타입 검증 없이 `all_acquired`에 누적하고 최종적으로 `set(all_acquired)`를 수행한다.

**문제 코드**:
```python
if isinstance(inventory, str):
    items = [i.strip() for i in inventory.split(",") if i.strip()]
    all_acquired.extend(items)
elif isinstance(inventory, list):
    all_acquired.extend(inventory)

current_state["cumulative"] = {
    "all_acquired_items": list(set(all_acquired)),
    "all_grants_received": list(set(all_grants)),
    "total_arcs_completed": len(arcs),
}
```

**호출 체인**: `extract_cumulative_state()` (`modules/domain/agents/state_extractor.py:263`)

**수정 제안**:
```python
normalized_items = []
for item in inventory:
    if isinstance(item, dict):
        name = item.get("name")
        if name:
            normalized_items.append(str(name))
    else:
        normalized_items.append(str(item))
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 53 완료

## Round 54 — modules/domain/agents/state_tracker_financial.py + modules/core/state_delta_tracker.py

### 진행 통계 업데이트
- 총 발견: 44건 (CRITICAL: 0, HIGH: 39, MEDIUM: 5)
- 라운드 진행: 54/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/state_tracker_financial.py:10` `class StateTrackerFinancial` — 금융 이벤트 추적 서브모듈.
- `modules/domain/agents/state_tracker_financial.py:20` `def extract_financial_events_from_arc(self, arc: dict) -> dict` — financial_events 추출/저장.
- `modules/domain/agents/state_tracker_financial.py:72` `def get_financial_state_summary(self) -> str` — 금융 상태 프롬프트 요약.
- `modules/domain/agents/state_tracker_financial.py:118` `def import_financial_registry(self, data: dict)` — DB 직렬화 복원.
- `modules/core/state_delta_tracker.py:68` `class StateDeltaTracker` — 내공/부상 델타 추적기.
- `modules/core/state_delta_tracker.py:105` `def apply_energy_delta(self, arc: int, episode: int, delta: int, reason: str) -> dict[str, Any]` — 내공 변화 적용.
- `modules/core/state_delta_tracker.py:220` `def recover_injury(self, arc: int, episode: int, body_part: str, recovery_method: str) -> dict[str, Any]` — 부상 회복 처리.
- `modules/core/state_delta_tracker.py:395` `def load_from_arc_state(self, state_constraints: dict) -> None` — Arc 종료 상태 로드.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def import_financial_registry(self, data: dict)` (`modules/domain/agents/state_tracker_financial.py:118`)
- `def load_from_arc_state(self, state_constraints: dict) -> None` (`modules/core/state_delta_tracker.py:395`)
2. 특징 문자열:
- `warning = f"'{level}' 부상이 {elapsed}화 만에 회복됨 (권장: {required_eps}화 이상)"` (`modules/core/state_delta_tracker.py:251`)
3. import 목록:
- `from dataclasses import dataclass` (`modules/core/state_delta_tracker.py:17`)
- `from enum import Enum` (`modules/core/state_delta_tracker.py:18`)
- `from typing import Any` (`modules/core/state_delta_tracker.py:19`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `self.tracker.financial_number_registry[int(k)] = v` (`modules/domain/agents/state_tracker_financial.py:124`)
- 호출자: `StateTracker.import_financial_registry()` 위임 (`modules/domain/agents/state_tracker.py:1001`)
- 상류/하류 컨텍스트:
- 상류: DB 로드 원본 `v` 타입 검증 없음
- 하류: `self.tracker.financial_number_registry[arc_no].get(field_name, [])` (`modules/domain/agents/state_tracker_financial.py:63`)
- 실패 시나리오: `v`가 dict가 아니면 이후 `.get` 접근에서 AttributeError.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `elapsed = current_ep - injury_ep` (`modules/core/state_delta_tracker.py:247`)
- 호출자: `recover_injury()` (`modules/core/state_delta_tracker.py:220`)
- 상류/하류 컨텍스트:
- 상류: 부상 이력은 `arc`, `episode`를 분리 기록 (`modules/core/state_delta_tracker.py:52`, `modules/core/state_delta_tracker.py:56`)
- 하류: 회복 경고 기준 비교 (`modules/core/state_delta_tracker.py:250`)
- 실패 시나리오: Arc 경계를 넘어 episode 번호가 재시작될 경우 음수/과소 elapsed가 계산되어 회복 검증 왜곡.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `injuries = arc_end.get("injuries", "정상")` + `InjuryLevel.from_string(injuries)` (`modules/core/state_delta_tracker.py:418`, `modules/core/state_delta_tracker.py:419`)
- 호출자: `load_from_arc_state()` (`modules/core/state_delta_tracker.py:395`)
- 상류/하류 컨텍스트:
- 상류: `arc_end_state.injuries` 타입 강제 없음
- 하류: `self.current_injury_level` 초기값 반영
- 실패 시나리오: injuries가 list/dict면 `from_string()` 미일치로 NORMAL로 강등되어 부상 상태를 잃음.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 54 완료

## Round 55 — modules/domain/agents/continuity_inspector.py

### 진행 통계 업데이트
- 총 발견: 45건 (CRITICAL: 0, HIGH: 39, MEDIUM: 6)
- 라운드 진행: 55/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/continuity_inspector.py:40` `class ContinuityInspector(BaseAgent)` — 연속성 검증 파사드.
- `modules/domain/agents/continuity_inspector.py:152` `def _format_entity_registry(self, entity_registry: dict) -> str` — Entity Registry 포맷팅.
- `modules/domain/agents/continuity_inspector.py:198` `def _extract_acquisitions(self, scenario: str) -> list[str]` — 획득 아이템 추출.
- `modules/domain/agents/continuity_inspector.py:266` `def _is_distributed_item(self, item: str, context: str) -> bool` — 분배 아이템 판정.
- `modules/domain/agents/continuity_inspector.py:319` `def _filter_distributed_items(self, items: list[str], context: str) -> list[str]` — 분배 아이템 필터.
- `modules/domain/agents/continuity_inspector.py:337` `def inspect(...) -> dict` — Blueprint 연속성 검사 위임 진입점.
- `modules/domain/agents/continuity_inspector.py:374` `def inspect_arc(self, current_arc: dict, prev_arcs: list[dict], entity_registry: dict = None) -> dict` — Arc 연속성 검사 위임.
- `modules/domain/agents/continuity_inspector.py:544` `def load_trackers_from_db(self, arcs_data: list[dict] = None) -> dict[str, int]` — V49.7 트래커 복원.

### 5-D. 읽기 증명
1. 마지막 함수: `def load_trackers_from_db(self, arcs_data: list[dict] = None) -> dict[str, int]` (`modules/domain/agents/continuity_inspector.py:544`)
2. 특징 문자열: `logging.info(f"🔍 [_is_same_item] 정확 매칭: '{item1_clean}' == '{item2_clean}'")` (`modules/domain/agents/continuity_inspector.py:260`)
3. import 목록:
- `from .base_agent import BaseAgent` (`modules/domain/agents/continuity_inspector.py:31`)
- `from .continuity_arc import ContinuityArcValidator` (`modules/domain/agents/continuity_inspector.py:34`)
- `from .continuity_blueprint import ContinuityBlueprintValidator` (`modules/domain/agents/continuity_inspector.py:35`)
- `from .continuity_manuscript import ContinuityManuscriptValidator` (`modules/domain/agents/continuity_inspector.py:36`)
- `from .continuity_tracker import ContinuityTrackerIntegration` (`modules/domain/agents/continuity_inspector.py:37`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `item_pos = context.find(item)` 후 단일 `local_context`만 검사 (`modules/domain/agents/continuity_inspector.py:273`, `modules/domain/agents/continuity_inspector.py:279`)
- 호출자: `_filter_distributed_items()` (`modules/domain/agents/continuity_inspector.py:328`) → `continuity_arc.py`의 분배 필터 경로 (`modules/domain/agents/continuity_arc.py:609`, `modules/domain/agents/continuity_arc.py:629`, `modules/domain/agents/continuity_arc.py:642`)
- 상류/하류 컨텍스트:
- 상류: 문맥 내 동일 아이템 다중 등장 가능
- 하류: 분배 판정 실패 시 아이템이 획득 아이템으로 유지
- 실패 시나리오: 첫 등장 주변만 검사해 후반 분배 문맥을 놓치면 오판정.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `formatted_items.append(f"{name} (별칭: {', '.join(aliases)}, 첫등장: ep{first_ep})")` (`modules/domain/agents/continuity_inspector.py:186`)
- 호출자: `_format_entity_registry()` (`modules/domain/agents/continuity_inspector.py:152`)
- 상류/하류 컨텍스트:
- 상류: `aliases = item.get("aliases", [])` (`modules/domain/agents/continuity_inspector.py:183`)
- 하류: LLM 프롬프트 문자열 구성
- 실패 시나리오: aliases에 비문자열 원소가 섞이면 `join`에서 TypeError.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `return list(set(items))[:5]`, `return list(set(grants))[:3]` (`modules/domain/agents/continuity_inspector.py:207`, `modules/domain/agents/continuity_inspector.py:218`)
- 호출자: `_extract_acquisitions()` / `_extract_grants()`
- 상류/하류 컨텍스트:
- 상류: 정규식 매칭 순서는 문맥 의미를 담고 있음
- 하류: Arc/Blueprint precheck 입력 요약에 사용
- 실패 시나리오: set 기반 dedup으로 순서가 비결정적이어서 동일 입력에서도 요약이 흔들림.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [MEDIUM] modules/domain/agents/continuity_inspector.py:273 — 분배 판정이 첫 번째 아이템 등장 문맥만 검사해 후속 분배를 놓침

**문제**: `_is_distributed_item()`이 `context.find(item)`으로 첫 등장 위치만 검사한다. 동일 아이템이 뒤에서 분배되는 경우 false negative가 발생한다.

**문제 코드**:
```python
item_pos = context.find(item)
if item_pos == -1:
    return False

start = max(0, item_pos - 100)
end = min(len(context), item_pos + len(item) + 100)
local_context = context[start:end]
```

**호출 체인**: `continuity_arc.py` (`modules/domain/agents/continuity_arc.py:609`) / `continuity_arc.py` (`modules/domain/agents/continuity_arc.py:629`) / `continuity_arc.py` (`modules/domain/agents/continuity_arc.py:642`) → `_filter_distributed_items()` (`modules/domain/agents/continuity_inspector.py:319`) → `_is_distributed_item()` (`modules/domain/agents/continuity_inspector.py:266`)

**수정 제안**:
```python
start_idx = 0
while True:
    item_pos = context.find(item, start_idx)
    if item_pos == -1:
        break
    # 각 등장 지점별 local_context 검사
    start_idx = item_pos + len(item)
```

**확신도**: MEDIUM

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 55 완료

## Round 56 — modules/domain/agents/continuity_manuscript.py

### 진행 통계 업데이트
- 총 발견: 47건 (CRITICAL: 0, HIGH: 41, MEDIUM: 6)
- 라운드 진행: 56/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/continuity_manuscript.py:157` `class ContinuityManuscriptValidator` — 원고 연속성 검증 전담.
- `modules/domain/agents/continuity_manuscript.py:216` `def inspect_manuscript(...) -> dict` — Stage4 원고 연속성 메인 검증.
- `modules/domain/agents/continuity_manuscript.py:374` `def _manuscript_python_precheck(...) -> dict` — Python 사전 연속성 필터.
- `modules/domain/agents/continuity_manuscript.py:824` `def _format_prev_manuscripts(self, prev_manuscripts: list[dict]) -> str` — 이전 원고 타임라인 포맷.
- `modules/domain/agents/continuity_manuscript.py:844` `def _check_blueprint_only(...) -> dict` — 1화/이전원고 없음 경로.
- `modules/domain/agents/continuity_manuscript.py:938` `def _check_skill_timeline(...) -> dict` — 스킬 타임라인 검증.
- `modules/domain/agents/continuity_manuscript.py:1037` `def _track_relationship_history(...) -> dict` — 관계 히스토리 추적.
- `modules/domain/agents/continuity_manuscript.py:1152` `def inspect_manuscript_v59(...) -> dict` — V59 강화 검증.
- `modules/domain/agents/continuity_manuscript.py:1191` `def _generate_v59_fix_instructions(self, violations: list[dict]) -> str` — V59 수정 지시 생성.

### 5-D. 읽기 증명
1. 마지막 함수: `def _generate_v59_fix_instructions(self, violations: list[dict]) -> str` (`modules/domain/agents/continuity_manuscript.py:1191`)
2. 특징 문자열: `logging.warning(f"🚨 [ContinuityInspector] 원고 LLM 검증 실패: {e}")` (`modules/domain/agents/continuity_manuscript.py:324`)
3. import 목록:
- `import logging` (`modules/domain/agents/continuity_manuscript.py:11`)
- `import re` (`modules/domain/agents/continuity_manuscript.py:12`)
- 프로젝트 모듈 import 없음(파일 전수 확인).

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `content = ms.get("content", "")` 후 슬라이싱/join (`modules/domain/agents/continuity_manuscript.py:830`, `modules/domain/agents/continuity_manuscript.py:834`, `modules/domain/agents/continuity_manuscript.py:842`)
- 호출자: `inspect_manuscript()`에서 `prev_timeline = self._format_prev_manuscripts(prev_manuscripts)` (`modules/domain/agents/continuity_manuscript.py:267`)
- 상류/하류 컨텍스트:
- 상류: 이전 원고 `content` 타입 강제 없음 (`modules/domain/agents/continuity_manuscript.py:367`)
- 하류: LLM 프롬프트 생성 전 단계
- 실패 시나리오: content가 dict/list면 slice 또는 `"\n".join(lines)`에서 TypeError로 검증 전체 중단.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `if any(v.get("severity") in ["CRITICAL", "MAJOR"] for v in all_violations):` (`modules/domain/agents/continuity_manuscript.py:1171`)
- 호출자: `inspect_manuscript_v59()` (`modules/domain/agents/continuity_manuscript.py:1152`)
- 상류/하류 컨텍스트:
- 상류: `all_violations = base_result.get("violations", []) + ...` (`modules/domain/agents/continuity_manuscript.py:1166`)
- 하류: 최종 decision/severity 산정 (`modules/domain/agents/continuity_manuscript.py:1172`)
- 실패 시나리오: violations에 문자열/비dict 항목이 섞이면 `v.get`에서 AttributeError로 V59 검증 크래시.
- 판정: BUG.

3. 위험 지점
- 코드 원문: `if item in acquired or acquired in item:` (`modules/domain/agents/continuity_manuscript.py:497`)
- 호출자: `_manuscript_python_precheck()`에서 미획득 아이템 검사 (`modules/domain/agents/continuity_manuscript.py:408`)
- 상류/하류 컨텍스트:
- 상류: `all_acquired_items`는 이전 원고 regex 추출 결과
- 하류: CRITICAL 위반 판정 분기 (`modules/domain/agents/continuity_manuscript.py:410`)
- 실패 시나리오: 부분 문자열만 일치해도 획득으로 간주되어 미획득 아이템 위반을 놓칠 수 있음.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/domain/agents/continuity_manuscript.py:834 — 이전 원고 content 비문자열 시 포맷 단계에서 TypeError

**문제**: `_format_prev_manuscripts()`가 `content`를 문자열로 정규화하지 않고 길이 비교/슬라이싱/join을 수행한다.

**문제 코드**:
```python
content = ms.get("content", "")

if len(content) > 1500:
    excerpt = content[:700] + "\n...(중략)...\n" + content[-500:]
else:
    excerpt = content

lines.append(excerpt)
return "\n".join(lines)
```

**호출 체인**: `inspect_manuscript()` (`modules/domain/agents/continuity_manuscript.py:216`) → `_format_prev_manuscripts()` (`modules/domain/agents/continuity_manuscript.py:824`)

**수정 제안**:
```python
if not isinstance(content, str):
    content = str(content) if content is not None else ""
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [HIGH] modules/domain/agents/continuity_manuscript.py:1171 — V59 최종 판정에서 비dict violation 항목 처리 누락

**문제**: `all_violations` 원소를 dict로 가정하고 `.get()`을 직접 호출한다. LLM/상위 병합 결과에 문자열이 섞이면 예외가 발생한다.

**문제 코드**:
```python
all_violations = (
    base_result.get("violations", []) + skill_check.get("violations", []) + rel_check.get("violations", [])
)

if any(v.get("severity") in ["CRITICAL", "MAJOR"] for v in all_violations):
    final_decision = "REJECT"
```

**호출 체인**: `ContinuityInspector.inspect_manuscript_v59()` (`modules/domain/agents/continuity_inspector.py:435`) → `ContinuityManuscriptValidator.inspect_manuscript_v59()` (`modules/domain/agents/continuity_manuscript.py:1152`)

**수정 제안**:
```python
normalized = [v for v in all_violations if isinstance(v, dict)]
if any(v.get("severity") in ["CRITICAL", "MAJOR"] for v in normalized):
    ...
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 56 완료

## Round 57 — modules/domain/agents/continuity_arc.py

### 진행 통계 업데이트
- 총 발견: 49건 (CRITICAL: 0, HIGH: 43, MEDIUM: 6)
- 라운드 진행: 57/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/continuity_arc.py:203` `class ContinuityArcValidator` — Arc 수준 연속성 검증 모듈.
- `modules/domain/agents/continuity_arc.py:223` `def inspect_arc(self, current_arc: dict, prev_arcs: list[dict], entity_registry: dict = None) -> dict` — Arc 간/내 연속성 메인 검증.
- `modules/domain/agents/continuity_arc.py:463` `def _inspect_intra_arc_only(self, current_arc: dict) -> dict` — Arc1 전용 내부 모순 검사.
- `modules/domain/agents/continuity_arc.py:518` `def _extract_accurate_joint_docs(...) -> dict | None` — Joint Docs 자동 추출/보정.
- `modules/domain/agents/continuity_arc.py:581` `def _arc_python_precheck(self, current_arc: dict, prev_arcs: list[dict]) -> dict` — Python 사전 검증.
- `modules/domain/agents/continuity_arc.py:781` `def _check_intra_arc_consistency(self, arc: dict) -> list[dict]` — 단일 Arc 내부 모순 분석.
- `modules/domain/agents/continuity_arc.py:885` `def _format_prev_arcs(self, prev_arcs: list[dict]) -> str` — 이전 Arc 타임라인 포맷.
- `modules/domain/agents/continuity_arc.py:963` `def _generate_arc_fix_instructions(self, violations: list[dict]) -> str` — Arc 수정 지시 생성.

### 5-D. 읽기 증명
1. 마지막 함수: `def _generate_arc_fix_instructions(self, violations: list[dict]) -> str` (`modules/domain/agents/continuity_arc.py:963`)
2. 특징 문자열: `logging.warning(f"🚨 [ContinuityInspector] Arc LLM 검증 실패: {e}")` (`modules/domain/agents/continuity_arc.py:444`)
3. import 목록:
- `import json` (`modules/domain/agents/continuity_arc.py:10`)
- `import logging` (`modules/domain/agents/continuity_arc.py:11`)
- `import re` (`modules/domain/agents/continuity_arc.py:12`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `ep_count = current_arc.get("ep_count", 5)` + `ep_end = current_arc.get("ep_end", ep_start + ep_count - 1)` (`modules/domain/agents/continuity_arc.py:249`, `modules/domain/agents/continuity_arc.py:250`)
- 호출자: `stage2_validation_pipeline.py`에서 `continuity_inspector.inspect_arc(...)` (`modules/core/stage2_validation_pipeline.py:390`) → `ContinuityInspector.inspect_arc()` (`modules/domain/agents/continuity_inspector.py:376`)
- 상류/하류 컨텍스트:
- 상류: `current_arc["ep_count"]` 타입 강제 없음
- 하류: prompt 생성용 `ep_end` 사용 (`modules/domain/agents/continuity_arc.py:358`)
- 실패 시나리오: `ep_count`가 문자열/None이면 산술 연산 TypeError로 Arc 검증 크래시.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `tactical_doc=self._ci._escape_braces(tactical_doc[:6000])` (`modules/domain/agents/continuity_arc.py:359`)
- 호출자: `inspect_arc()` (`modules/domain/agents/continuity_arc.py:223`)
- 상류/하류 컨텍스트:
- 상류: `tactical_doc = current_arc.get("tactical_doc", "")` (`modules/domain/agents/continuity_arc.py:244`)
- 하류: 이 코드가 `try` 블록 이전 실행 (`modules/domain/agents/continuity_arc.py:367`)
- 실패 시나리오: tactical_doc가 dict/list면 slice에서 TypeError 발생, 예외 복구 없이 검증 중단.
- 판정: BUG.

3. 위험 지점
- 코드 원문: `sections = re.split(section_pattern, tactical_doc)` 후 `if len(sections) > 1:`일 때만 검증 루프 진입 (`modules/domain/agents/continuity_arc.py:792`, `modules/domain/agents/continuity_arc.py:794`)
- 호출자: `_check_intra_arc_consistency()` (`modules/domain/agents/continuity_arc.py:781`)
- 상류/하류 컨텍스트:
- 상류: tactical_doc가 포맷 변형된 경우 화 단위 헤더 미매칭 가능
- 하류: `ep_sections` 비어 있으면 획득/부상/복장 불연속 체크가 대부분 스킵
- 실패 시나리오: 섹션 파싱 실패 시 내부 모순 탐지가 무력화되어 false negative 발생.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/domain/agents/continuity_arc.py:250 — `ep_count` 비정수 입력 시 `ep_end` 계산에서 TypeError

**문제**: `ep_count`를 정규화 없이 산술 연산에 사용한다. 문자열/None 값이 들어오면 검증 함수가 즉시 예외로 중단된다.

**문제 코드**:
```python
ep_count = current_arc.get("ep_count", 5)
ep_end = current_arc.get("ep_end", ep_start + ep_count - 1)
```

**호출 체인**: `stage2_validation_pipeline.py` (`modules/core/stage2_validation_pipeline.py:390`) → `ContinuityInspector.inspect_arc()` (`modules/domain/agents/continuity_inspector.py:374`) → `ContinuityArcValidator.inspect_arc()` (`modules/domain/agents/continuity_arc.py:223`)

**수정 제안**:
```python
try:
    ep_count_i = int(ep_count)
except (ValueError, TypeError):
    ep_count_i = 5
ep_end = current_arc.get("ep_end", ep_start + ep_count_i - 1)
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [HIGH] modules/domain/agents/continuity_arc.py:359 — `tactical_doc` 비문자열 입력 시 try 진입 전 슬라이싱 크래시

**문제**: prompt 빌드 단계에서 tactical_doc를 바로 슬라이싱한다. 타입 보정이 없어 dict/list 입력 시 TypeError가 발생하고 예외 복구가 작동하지 않는다.

**문제 코드**:
```python
prompt = ARC_CONTINUITY_INSPECTION_PROMPT.format(
    current_arc_no=arc_no,
    ep_count=ep_count,
    ep_start=ep_start,
    ep_end=ep_end,
    tactical_doc=self._ci._escape_braces(tactical_doc[:6000]),
    joint_docs=self._ci._escape_braces(json.dumps(joint_docs, ensure_ascii=False)),
    status_shadow=self._ci._escape_braces(json.dumps(status_shadow, ensure_ascii=False)),
    prev_arc_count=len(prev_arcs),
    prev_arcs_summary=self._ci._escape_braces(prev_arcs_summary),
    entity_registry=self._ci._escape_braces(entity_registry_str),
)
```

**호출 체인**: `ContinuityArcValidator.inspect_arc()` (`modules/domain/agents/continuity_arc.py:223`)

**수정 제안**:
```python
if isinstance(tactical_doc, dict):
    tactical_doc = "\n".join(str(v) for v in tactical_doc.values() if v)
elif not isinstance(tactical_doc, str):
    tactical_doc = str(tactical_doc) if tactical_doc else ""
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 57 완료

## Round 58 — modules/domain/agents/continuity_blueprint.py + modules/domain/agents/continuity_tracker.py

### 진행 통계 업데이트
- 총 발견: 50건 (CRITICAL: 0, HIGH: 44, MEDIUM: 6)
- 라운드 진행: 58/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/continuity_blueprint.py:135` `class ContinuityBlueprintValidator` — Stage3 블루프린트 연속성 검증 모듈.
- `modules/domain/agents/continuity_blueprint.py:153` `def inspect(self, current_ep: int, current_blueprint: dict, prev_blueprints: list[dict], hud_history: list[dict] = None, entity_registry: dict = None) -> dict` — 블루프린트 연속성 메인 검사.
- `modules/domain/agents/continuity_blueprint.py:268` `def _python_precheck(self, current_ep: int, current_scenario: str, prev_blueprints: list[dict]) -> dict` — Python 사전 필터.
- `modules/domain/agents/continuity_blueprint.py:366` `def _format_prev_blueprints(self, prev_blueprints: list[dict]) -> str` — 이전 블루프린트 타임라인 포맷.
- `modules/domain/agents/continuity_blueprint.py:420` `def get_prev_blueprints(self, current_ep: int, window: int = None) -> list[dict]` — DB 기반 이전 블루프린트 조회.
- `modules/domain/agents/continuity_tracker.py:25` `class ContinuityTrackerIntegration` — V49.7 트래커 통합 검증.
- `modules/domain/agents/continuity_tracker.py:85` `def validate_with_trackers(self, arc: int, episode: int, content: str, content_type: str = "blueprint") -> dict[str, Any]` — 관계/파워/복선/상태 트래커 검증 집계.
- `modules/domain/agents/continuity_tracker.py:250` `def _check_foreshadowing_with_tracker(self, arc: int, episode: int, content: str) -> dict[str, Any]` — 미회수 복선 상태 경고 생성.
- `modules/domain/agents/continuity_tracker.py:330` `def load_trackers_from_db(self, arcs_data: list[dict] = None) -> dict[str, int]` — Arc 데이터 기반 트래커 상태 복원.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def _generate_fix_instructions(self, violations: list[dict]) -> str` (`modules/domain/agents/continuity_blueprint.py:445`)
- `def load_trackers_from_db(self, arcs_data: list[dict] = None) -> dict[str, int]` (`modules/domain/agents/continuity_tracker.py:330`)
2. 특징 문자열:
- `logging.info(f"📋 [V60.56] Python advisory 발견 {len(python_advisory)}건 - LLM에게 전달")` (`modules/domain/agents/continuity_blueprint.py:210`)
3. import 목록:
- `from modules.core.foreshadow_tracker import ForeshadowTracker` (`modules/domain/agents/continuity_tracker.py:14`)
- `from modules.core.power_scaling import PowerScalingTracker` (`modules/domain/agents/continuity_tracker.py:16`)
- `from modules.core.state_delta_tracker import StateDeltaTracker` (`modules/domain/agents/continuity_tracker.py:18`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `current_scenario=self._ci._escape_braces(current_scenario[:4000]),` (`modules/domain/agents/continuity_blueprint.py:221`)
- 호출자: `ContinuityInspector.inspect()` (`modules/domain/agents/continuity_inspector.py:337`) → `self._blueprint.inspect(...)` (`modules/domain/agents/continuity_inspector.py:346`)
- 상류/하류 컨텍스트:
- 상류: `current_scenario = current_blueprint.get("integrated_scenario", "")` (`modules/domain/agents/continuity_blueprint.py:195`)
- 하류: prompt 포맷팅 직후 LLM 호출 (`modules/domain/agents/continuity_blueprint.py:227`)
- 실패 시나리오: `integrated_scenario`가 dict면 슬라이싱(`[:4000]`)에서 TypeError 발생, 검증 경로 중단.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `matches = re.findall(pattern, scenario)` (`modules/domain/agents/continuity_blueprint.py:281`)
- 호출자: `inspect()` (`modules/domain/agents/continuity_blueprint.py:153`) → `_python_precheck()` (`modules/domain/agents/continuity_blueprint.py:208`)
- 상류/하류 컨텍스트:
- 상류: `scenario = bp.get("integrated_scenario", "")` (`modules/domain/agents/continuity_blueprint.py:278`)
- 하류: advisory/timeline 생성 (`modules/domain/agents/continuity_blueprint.py:348`)
- 실패 시나리오: 이전 블루프린트의 `integrated_scenario`가 비문자열이면 정규식에서 TypeError 발생.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `pending = self._ci.foreshadow_tracker.get_pending_foreshadowings(arc)` (`modules/domain/agents/continuity_tracker.py:255`)
- 호출자: `validate_with_trackers()` (`modules/domain/agents/continuity_tracker.py:85`) → `_check_foreshadowing_with_tracker()` (`modules/domain/agents/continuity_tracker.py:250`)
- 상류/하류 컨텍스트:
- 상류: `init_trackers()`에서 `self._ci.foreshadow_tracker = ForeshadowTracker()` (`modules/domain/agents/continuity_tracker.py:56`)
- 하류: `critical_pending`/`warning_pending` 계산 (`modules/domain/agents/continuity_tracker.py:257`)
- 실패 시나리오: `ForeshadowTracker`에는 `get_pending_foreshadowings`가 정의되어 있지 않아(정의 없음, `modules/core/foreshadow_tracker.py`) 호출 시 AttributeError.
- 판정: RISK (Design Check Needed, latent path).

### 5-C. 발견된 버그
### [HIGH] modules/domain/agents/continuity_blueprint.py:221 — `integrated_scenario` 비문자열(dict) 입력 시 슬라이싱 크래시

**문제**: `current_scenario` 타입 정규화 없이 슬라이싱을 수행한다. dict 유입 시 `unhashable type: 'slice'`로 즉시 실패한다.

**문제 코드**:
```python
current_scenario = current_blueprint.get("integrated_scenario", "")
...
prompt = CONTINUITY_INSPECTION_PROMPT.format(
    current_ep=current_ep,
    current_scenario=self._ci._escape_braces(current_scenario[:4000]),
    prev_count=len(prev_blueprints),
    prev_summaries=self._ci._escape_braces(prev_summaries),
    entity_registry=self._ci._escape_braces(entity_registry_str),
)
```

**호출 체인**: `ContinuityInspector.inspect()` (`modules/domain/agents/continuity_inspector.py:337`) → `ContinuityBlueprintValidator.inspect()` (`modules/domain/agents/continuity_blueprint.py:153`)

**수정 제안**:
```python
if isinstance(current_scenario, dict):
    current_scenario = "\n".join(str(v) for v in current_scenario.values() if v)
elif not isinstance(current_scenario, str):
    current_scenario = str(current_scenario) if current_scenario is not None else ""
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 58 완료

## Round 59 — modules/core/world_state.py + modules/core/fact_ledger.py

### 진행 통계 업데이트
- 총 발견: 52건 (CRITICAL: 0, HIGH: 46, MEDIUM: 6)
- 라운드 진행: 59/100

### 5-A. 파일 구조 요약
- `modules/core/world_state.py:17` `class WorldStateManager` — 세계 상태 누적/요약/롤백 관리.
- `modules/core/world_state.py:75` `def update_from_state_changes(self, ep_num: int, state_changes: dict)` — state_changes 기반 세계 상태 갱신.
- `modules/core/world_state.py:260` `def get_summary(self, max_chars: int = 5000) -> str` — 프롬프트 주입용 world state 요약.
- `modules/core/world_state.py:408` `def rollback_to(self, target_ep: int) -> None` — 에피소드 리플레이 롤백.
- `modules/core/fact_ledger.py:17` `class FactLedger` — 누적 사실 원장.
- `modules/core/fact_ledger.py:77` `def update_from_state_changes(self, ep_num: int, state_changes: dict)` — 사실 항목 upsert.
- `modules/core/fact_ledger.py:207` `def update_from_bible_delta(self, ep_num: int, bible_delta: dict)` — bible delta 기반 보강.
- `modules/core/fact_ledger.py:353` `def to_summary(self, max_chars: int = None) -> str` — fact ledger 요약 생성.
- `modules/core/fact_ledger.py:521` `def rollback_to(self, target_ep: int) -> None` — 리플레이 기반 원장 복원.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def rollback_to(self, target_ep: int) -> None` (`modules/core/world_state.py:408`)
- `def rollback_to(self, target_ep: int) -> None` (`modules/core/fact_ledger.py:521`)
2. 특징 문자열:
- `"[D-2] WorldState 롤백: ep %d 이전으로 복원 (이전 last_updated_ep=%d)",` (`modules/core/world_state.py:411`)
3. import 목록:
- `import json` (`modules/core/world_state.py:11`)
- `import logging` (`modules/core/world_state.py:12`)
- 프로젝트 모듈 import 없음 (두 파일 모두 표준 라이브러리만 사용).

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `npc = rel.get("npc", "")` (`modules/core/world_state.py:129`)
- 호출자: `Stage4PostProcessor`의 world state 갱신 (`modules/core/stage4_post_processor.py:354`) → `self.ctx.world_state.update_from_state_changes(next_ep, _ws_sc)` (`modules/core/stage4_post_processor.py:356`)
- 상류/하류 컨텍스트:
- 상류: 관계 변화 스키마는 `target` 필드를 요구 (`modules/core/response_schemas.py:220`, `modules/core/response_schemas.py:226`)
- 하류: `self._state["relationships"][npc] = to_rel` (`modules/core/world_state.py:132`)
- 실패 시나리오: `relationship_changes`가 `{"target": ...}` 형태일 때 `npc`가 빈 문자열이 되어 관계 반영이 누락된다.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `npc = rel.get("npc", "")` (`modules/core/fact_ledger.py:109`)
- 호출자: `Stage4PostProcessor`의 fact ledger 갱신 (`modules/core/stage4_post_processor.py:382`) → `self.ctx.fact_ledger.update_from_state_changes(next_ep, _fl_sc)` (`modules/core/stage4_post_processor.py:384`)
- 상류/하류 컨텍스트:
- 상류: DB/스키마 계약은 관계 변화 키를 `target`으로 명시 (`modules/core/db_manager.py:254`, `modules/core/response_schemas.py:220`)
- 하류: `_upsert_character(... relationship=rel.get("to", ""))` (`modules/core/fact_ledger.py:111`, `modules/core/fact_ledger.py:114`)
- 실패 시나리오: `target`만 있는 정상 입력에서 관계 변화가 원장에 누적되지 않는다.
- 판정: BUG.

3. 위험 지점
- 코드 원문: `try:` (`modules/core/world_state.py:87`) ... `except Exception as e:` (`modules/core/world_state.py:232`)
- 호출자: `update_from_state_changes()` 직접 호출 경로 전반 (`modules/core/stage4_post_processor.py:356`)
- 상류/하류 컨텍스트:
- 상류: 하나의 에피소드 state_changes에 다수 카테고리 혼재
- 하류: except에서 에러 로그만 남기고 함수 종료
- 실패 시나리오: 중간 카테고리 하나의 예외가 발생하면 같은 에피소드의 이후 카테고리(플롯/동행자 등) 갱신까지 전부 스킵된다.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/core/world_state.py:129 — 관계 변화 키 계약(`target`) 미반영으로 관계 상태 누락

**문제**: world state가 `relationship_changes` 항목에서 `npc` 키만 읽는다. 현재 스키마/저장 계약의 `target` 키 입력이 누락 처리된다.

**문제 코드**:
```python
for rel in state_changes.get("relationship_changes") or []:
    if not isinstance(rel, dict):
        continue
    npc = rel.get("npc", "")
    to_rel = rel.get("to", "")
    if npc and to_rel:
        self._state["relationships"][npc] = to_rel
```

**호출 체인**: `Stage4PostProcessor._apply_stage4_effects()` (`modules/core/stage4_post_processor.py:354`) → `WorldStateManager.update_from_state_changes()` (`modules/core/world_state.py:75`)

**수정 제안**:
```python
npc = rel.get("npc", "") or rel.get("target", "")
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [HIGH] modules/core/fact_ledger.py:109 — 관계 변화 키 계약(`target`) 미반영으로 팩트 원장 관계 누락

**문제**: fact ledger도 `npc` 키만 읽어서 `target` 기반 관계 변화 입력을 누락한다.

**문제 코드**:
```python
for rel in state_changes.get("relationship_changes") or []:
    if not isinstance(rel, dict):
        continue
    npc = rel.get("npc", "")
    if npc:
        self._upsert_character(
            npc,
            ep_num,
            relationship=rel.get("to", ""),
            note=f"관계 변화: {rel.get('from', '?')} -> {rel.get('to', '?')}",
        )
```

**호출 체인**: `Stage4PostProcessor._apply_stage4_effects()` (`modules/core/stage4_post_processor.py:382`) → `FactLedger.update_from_state_changes()` (`modules/core/fact_ledger.py:77`)

**수정 제안**:
```python
npc = rel.get("npc", "") or rel.get("target", "")
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 59 완료

## Round 60 — modules/domain/agents/consensus_validator.py + modules/core/cross_agent_verifier.py

### 진행 통계 업데이트
- 총 발견: 54건 (CRITICAL: 0, HIGH: 48, MEDIUM: 6)
- 라운드 진행: 60/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/consensus_validator.py:145` `class ConsensusValidator(BaseAgent)` — 3-LLM 합의 검증기.
- `modules/domain/agents/consensus_validator.py:163` `def validate_with_consensus(self, arc: dict, prev_arcs: list[dict], constraints: str = "", python_advisory: list[dict] = None) -> tuple[str, dict]` — 합의 투표 오케스트레이션.
- `modules/domain/agents/consensus_validator.py:289` `def _validate_single(self, arc_data: str, prev_summary: str, constraints: str, perspective: dict, python_advisory_text: str = "(없음)") -> dict` — 단일 관점 투표 실행.
- `modules/domain/agents/consensus_validator.py:319` `def _ensure_validation_fields(self, result: dict) -> dict` — 투표 결과 필드 정규화.
- `modules/domain/agents/consensus_validator.py:333` `def _derive_consensus(self, results: list[dict]) -> tuple[str, dict]` — 최종 PASS/REJECT 합의 산출.
- `modules/core/cross_agent_verifier.py:51` `class CrossAgentVerifier` — Architect/Writer 준수 검증기.
- `modules/core/cross_agent_verifier.py:139` `def _parse_result(self, response_text: str) -> dict[str, Any]` — LLM 응답 JSON 파싱.
- `modules/core/cross_agent_verifier.py:265` `def verify_architect_compliance(self, blueprint: dict[str, Any], arc_design: dict[str, Any], use_llm: bool = True) -> ComplianceResult` — 설계 준수 검증.
- `modules/core/cross_agent_verifier.py:349` `def verify_writer_compliance(self, manuscript: str, blueprint: dict[str, Any], use_llm: bool = True) -> ComplianceResult` — 원고 준수 검증.
- `modules/core/cross_agent_verifier.py:464` `def quick_check(self, content: str, reference: dict[str, Any], check_type: str) -> tuple[bool, list[str]]` — Python-only 빠른 점검.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def create_consensus_validator(context, client, model_tier: str = "gemini-2.5-flash")` (`modules/domain/agents/consensus_validator.py:451`)
- `def quick_check(self, content: str, reference: dict[str, Any], check_type: str) -> tuple[bool, list[str]]` (`modules/core/cross_agent_verifier.py:464`)
2. 특징 문자열:
- `logging.warning("⚠️ [Consensus] 모든 검증기 실패 — 보수적 PASS 처리")` (`modules/domain/agents/consensus_validator.py:281`)
3. import 목록:
- `from modules.core.arc_summary_utils import generate_prev_arc_summary` (`modules/domain/agents/consensus_validator.py:19`)
- `from .base_agent import BaseAgent` (`modules/domain/agents/consensus_validator.py:21`)
- `from modules.core.constants import ManuscriptLimits` (`modules/core/cross_agent_verifier.py:28`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `return self._ensure_validation_fields(result)` (`modules/domain/agents/consensus_validator.py:313`)
- 호출자: `Stage2ValidationPipeline` 합의 검증 (`modules/core/stage2_validation_pipeline.py:134`) → `validate_with_consensus()` (`modules/domain/agents/consensus_validator.py:163`) → `_validate_single()` (`modules/domain/agents/consensus_validator.py:289`)
- 상류/하류 컨텍스트:
- 상류: `result = self._extract_json_robust(result)` (`modules/domain/agents/consensus_validator.py:311`)는 dict 보장 없음
- 하류: `_ensure_validation_fields()`에서 `if "verdict" not in result:` (`modules/domain/agents/consensus_validator.py:321`)
- 실패 시나리오: result가 None/list면 TypeError가 발생하고, 상위 future 예외 처리에서 해당 투표를 PASS로 대체해 오검출이 발생한다.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `for adv in python_advisory[:5]:` + `adv_type = adv.get("type", "?")` (`modules/domain/agents/consensus_validator.py:194`, `modules/domain/agents/consensus_validator.py:195`)
- 호출자: `validate_with_consensus()` (`modules/domain/agents/consensus_validator.py:163`)
- 상류/하류 컨텍스트:
- 상류: `python_advisory`는 외부 전달 인자
- 하류: advisory_text 생성 후 prompt 주입
- 실패 시나리오: advisory 원소에 문자열이 섞이면 `.get()`에서 AttributeError.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `violations = py_violations + result.get("violations", [])` (`modules/core/cross_agent_verifier.py:314`)
- 호출자: `verify_architect_compliance()` 공개 API (`modules/core/cross_agent_verifier.py:265`)
- 상류/하류 컨텍스트:
- 상류: `_parse_result()`는 LLM 결과 dict를 그대로 반환 (`modules/core/cross_agent_verifier.py:139`)
- 하류: ComplianceResult 생성 (`modules/core/cross_agent_verifier.py:341`)
- 실패 시나리오: LLM이 `"violations": null`을 반환하면 `list + None`에서 TypeError로 검증 함수가 중단된다.
- 판정: BUG.

### 5-C. 발견된 버그
### [HIGH] modules/domain/agents/consensus_validator.py:321 — 비dict 투표 결과가 PASS 대체로 누락되는 fail-open 경로

**문제**: `_ensure_validation_fields()`가 dict가 아닌 입력(None/list)을 처리하지 못하고 예외를 발생시킨다. 예외는 상위 future 처리에서 PASS 결과로 대체되어 실제 검증 실패가 은폐된다.

**문제 코드**:
```python
result = self._extract_json_robust(result)
return self._ensure_validation_fields(result)

def _ensure_validation_fields(self, result: dict) -> dict:
    if "verdict" not in result:
        result["verdict"] = "PASS"
```

**호출 체인**: `Stage2ValidationPipeline._run_consensus_phase()` (`modules/core/stage2_validation_pipeline.py:134`) → `ConsensusValidator.validate_with_consensus()` (`modules/domain/agents/consensus_validator.py:163`) → `_validate_single()` (`modules/domain/agents/consensus_validator.py:289`) → `_ensure_validation_fields()` (`modules/domain/agents/consensus_validator.py:319`)

**수정 제안**:
```python
if not isinstance(result, dict):
    result = {}
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [HIGH] modules/core/cross_agent_verifier.py:314 — LLM `violations: null` 응답 시 list 병합 TypeError

**문제**: `result.get("violations", [])`를 바로 리스트와 더한다. 값이 `None`이면 TypeError가 발생한다.

**문제 코드**:
```python
violations = py_violations + result.get("violations", [])
warnings = result.get("warnings", [])
```

**호출 체인**: `CrossAgentVerifier.verify_architect_compliance()` (`modules/core/cross_agent_verifier.py:265`) (공개 API 직접 호출 경로)

**수정 제안**:
```python
llm_violations = result.get("violations") or []
if not isinstance(llm_violations, list):
    llm_violations = []
violations = py_violations + llm_violations
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 60 완료

## 60라운드 오탐 재검증
- 재검증 범위: Round 51~60 신규 BUG 항목.
- 판정 변경: 없음.
- 재검증 메모: FP-1(비차단 갱신), FP-5(LLM 파싱 폴백), FP-6(DB JSON string 저장) 기준과 교차 확인했으며, 이번 라운드 확정 BUG는 모두 계약 불일치 또는 런타임 예외 경로로 재현 가능.

## Round 61 — modules/core/db_manager.py (L1~800)

### 진행 통계 업데이트
- 총 발견: 55건 (CRITICAL: 0, HIGH: 49, MEDIUM: 6)
- 라운드 진행: 61/100

### 5-A. 파일 구조 요약
- `modules/core/db_manager.py:48` `class DBManager` — SQLite 기반 저장소/트랜잭션 관리.
- `modules/core/db_manager.py:61` `def _boot_db(self) -> None` — 핵심 테이블 생성/마이그레이션.
- `modules/core/db_manager.py:452` `def save_episode_bible(self, ep_num: int, bible_delta: dict)` — 화별 bible delta 저장.
- `modules/core/db_manager.py:485` `def get_episode_bible(self, ep_num: int) -> dict` — 단일 화 bible delta 조회.
- `modules/core/db_manager.py:522` `def get_cumulative_bible(self, up_to_ep: int) -> dict` — 누적 bible 계산(캐시 포함).
- `modules/core/db_manager.py:610` `def get_all_episode_bibles(self) -> list` — 전체 bible delta 목록 조회.
- `modules/core/db_manager.py:680` `def sync_seeds(self, seeds_list) -> None` — 복선(seeds) 동기화.
- `modules/core/db_manager.py:728` `def update_lore_items_batch(self, lore_items_list) -> None` — 로어 일괄 UPSERT.
- `modules/core/db_manager.py:798` `def save_anchor(self, key, data) -> bool` — 앵커 JSON 저장.
- `modules/core/db_manager.py:819` `def load_anchor(self, key, default=None)` — 앵커 JSON 로드.

### 5-D. 읽기 증명
1. 마지막 함수: `def load_anchor(self, key, default=None)` (`modules/core/db_manager.py:819`)
2. 특징 문자열: `logging.info(f"🔧 [DB Migration] 새로운 지표 '{metric}' 발견. 테이블에 컬럼을 추가합니다.")` (`modules/core/db_manager.py:200`)
3. import 목록:
- `from .constants import MARTIAL_METRICS` (`modules/core/db_manager.py:10`)
- `import sqlite3` (`modules/core/db_manager.py:3`)
- `import threading` (`modules/core/db_manager.py:4`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `new_items = json.loads(row["new_items"] or "[]")` (`modules/core/db_manager.py:562`)
- 호출자: `Stage4ContextBuilder` 컨텍스트 구성 (`modules/core/stage4_context_builder.py:168`) → `DBManager.get_cumulative_bible()` (`modules/core/db_manager.py:522`)
- 상류/하류 컨텍스트:
- 상류: `episode_bibles`는 과거 데이터/수동 패치/구버전 레코드가 섞일 수 있음
- 하류: 누적 `items/npcs/relationships/states` 계산 루프 (`modules/core/db_manager.py:565`~`modules/core/db_manager.py:598`)
- 실패 시나리오: 단일 레코드 JSON 오염 시 `json.loads` 예외로 누적 bible 전체 조회가 중단된다.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `"new_items": json.loads(row["new_items"] or "[]"),` (`modules/core/db_manager.py:634`)
- 호출자: `get_all_episode_bibles()` (`modules/core/db_manager.py:610`) (현재 코드베이스 직접 호출 미확인, 저장소 공개 API)
- 상류/하류 컨텍스트:
- 상류: row 필드별 JSON 정규화 없음
- 하류: 전체 bibles 리스트 반환 (`modules/core/db_manager.py:648`)
- 실패 시나리오: 단일 화 데이터 파손 시 전체 조회 함수가 예외로 중단된다.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `seed_id = s.get("id") or s.get("seed_id", f"unknown_{int(time.time())}")` (`modules/core/db_manager.py:685`)
- 호출자: `ProjectManager` 시드 동기화 (`modules/core/project_manager.py:192`, `modules/core/project_manager.py:451`)
- 상류/하류 컨텍스트:
- 상류: `seeds_list` 원소 타입 검증 없음
- 하류: seeds 테이블 UPSERT (`modules/core/db_manager.py:693`)
- 실패 시나리오: 원소가 dict가 아니면 `.get`에서 AttributeError가 발생해 동기화가 중단된다.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/core/db_manager.py:562 — 누적 bible 계산에서 비안전 `json.loads`로 전체 컨텍스트 빌드 중단

**문제**: `get_cumulative_bible()`가 row JSON 필드를 직접 파싱한다. 파손된 한 레코드가 있으면 예외 복구 없이 전체 누적 계산이 실패한다.

**문제 코드**:
```python
for row in rows:
    # 아이템: 획득은 추가, 분실은 제거
    new_items = json.loads(row["new_items"] or "[]")
    lost_items = json.loads(row["lost_items"] or "[]")
    cumulative["items"].extend(new_items)
    cumulative["items"] = [i for i in cumulative["items"] if i not in lost_items]
```

**호출 체인**: `Stage4ContextBuilder._build_bible_context()` (`modules/core/stage4_context_builder.py:168`) → `DBManager.get_cumulative_bible()` (`modules/core/db_manager.py:522`)

**수정 제안**:
```python
def _safe_json_list(raw):
    try:
        v = json.loads(raw or "[]")
        return v if isinstance(v, list) else []
    except (json.JSONDecodeError, TypeError, ValueError):
        return []
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 61 완료

## Round 62 — modules/core/db_manager.py (L801~end)

### 진행 통계 업데이트
- 총 발견: 55건 (CRITICAL: 0, HIGH: 49, MEDIUM: 6)
- 라운드 진행: 62/100

### 5-A. 파일 구조 요약
- `modules/core/db_manager.py:819` `def load_anchor(self, key, default=None)` — 앵커 단건 로드.
- `modules/core/db_manager.py:893` `def load_state_log(self, ep_num: int) -> dict` — state_log 조회/파싱.
- `modules/core/db_manager.py:958` `def commit_episode_factory(self, ep_num, manuscript_data, martial_data, state_data, causal_links, karma_data, lore_data, recovered_seeds=None) -> bool` — 에피소드 단위 원자 커밋 팩토리.
- `modules/core/db_manager.py:1133` `def transaction(self) -> None` — 컨텍스트 매니저 트랜잭션 가드.
- `modules/core/db_manager.py:1187` `def reset_after(self, target_ep) -> None` — 롤백용 데이터 삭제.
- `modules/core/db_manager.py:1270` `def get_recent_blueprints(self, before_ep: int, limit: int = 10) -> list` — 최근 blueprint 조회.
- `modules/core/db_manager.py:1322` `def get_recent_manuscript_excerpts(self, before_ep: int, limit: int = 10, max_chars: int = 200) -> list` — 원고 발췌 조회.
- `modules/core/db_manager.py:1468` `def get_selection_analysis(self, lookback: int = 100) -> list[dict]` — Director 선택 이력 분석 조회.
- `modules/core/db_manager.py:1519` `def get_cost_summary(self, scope_type: str | None = None, lookback: int = 50) -> list[dict]` — 비용 요약 조회.
- `modules/core/db_manager.py:1637` `def get_recent_satisfaction_tags(self, before_ep: int, lookback: int = 5) -> list` — 만족도 태그 시계열 조회.

### 5-D. 읽기 증명
1. 마지막 함수: `def get_recent_satisfaction_tags(self, before_ep: int, lookback: int = 5) -> list` (`modules/core/db_manager.py:1637`)
2. 특징 문자열: `logging.info(f"🎬 [DB Transaction] 제 {ep_num}화 데이터 안전 박제 완료.")` (`modules/core/db_manager.py:1070`)
3. import 목록:
- `from .constants import MARTIAL_METRICS` (`modules/core/db_manager.py:10`)
- `import json` (`modules/core/db_manager.py:1`)
- `import traceback` (`modules/core/db_manager.py:6`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `result["data"] = json.loads(row["data"]) if row["data"] else {}` + `except json.JSONDecodeError:` (`modules/core/db_manager.py:903`, `modules/core/db_manager.py:904`)
- 호출자: `load_state_log()` (`modules/core/db_manager.py:893`) (호출 지점 분산, 저장소 조회 API)
- 상류/하류 컨텍스트:
- 상류: `row["data"]` 타입 강제 없음(손상/수동 업데이트 가능)
- 하류: 조회 결과 `{"summary": ..., "data": ...}` 반환
- 실패 시나리오: `row["data"]`가 비문자열 비JSON 타입이면 TypeError가 inner except에서 잡히지 않고 outer except로 빠져 `None` 반환(정상 로그가 있어도 조회 실패 처리).
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `data = json.loads(row["data"]) if row["data"] else {}` + `except json.JSONDecodeError:` (`modules/core/db_manager.py:1292`, `modules/core/db_manager.py:1293`)
- 호출자: `director_continuity.py`의 최근 blueprint 조회 (`modules/domain/agents/director_continuity.py:587`)
- 상류/하류 컨텍스트:
- 상류: blueprints.data 컬럼은 TEXT지만 오염 가능
- 하류: `results.append({"ep_num": row["ep_num"], "data": data})` (`modules/core/db_manager.py:1295`)
- 실패 시나리오: TypeError/ValueError 계열 파싱 실패는 미처리되어 호출자에서 예외 전파 가능.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `lookback = max(int(lookback), 0)` (`modules/core/db_manager.py:1470`)
- 호출자: `main_a.py` 분석 화면 (`main_a.py:2016`) 및 기타 외부 호출 경로
- 상류/하류 컨텍스트:
- 상류: 외부 인자 검증 없음
- 하류: SQL `LIMIT ?` 파라미터로 사용 (`modules/core/db_manager.py:1477`)
- 실패 시나리오: 숫자 변환 불가 문자열 입력 시 ValueError로 함수 즉시 중단.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 62 완료

## Round 63 — modules/domain/agents/base_agent.py (L1~600)

### 진행 통계 업데이트
- 총 발견: 55건 (CRITICAL: 0, HIGH: 49, MEDIUM: 6)
- 라운드 진행: 63/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/base_agent.py:34` `class AgentErrorType` — 에러 타입 분류 상수.
- `modules/domain/agents/base_agent.py:55` `def _load_model_config() -> dict` — 모델 설정(`config/models.yaml`) 로드.
- `modules/domain/agents/base_agent.py:96` `def _get_model_fallback_chain() -> dict` — 모델 폴백 체인 구성.
- `modules/domain/agents/base_agent.py:123` `class BaseAgent` — 모든 에이전트 공통 LLM 호출/복구 기반 클래스.
- `modules/domain/agents/base_agent.py:151` `def _init_api_keys(cls) -> None` — API 키 풀 초기화.
- `modules/domain/agents/base_agent.py:169` `def _try_rotate_key(cls)` — 429 대응 키 순환.
- `modules/domain/agents/base_agent.py:208` `def __init__(self, context, client, model_tier=None, enable_cascade=False) -> None` — 공통 상태 초기화.
- `modules/domain/agents/base_agent.py:230` `def agent_name(self) -> str` — 에이전트명 반환.
- `modules/domain/agents/base_agent.py:236` `def ask(self, prompt, temperature=0.5, response_schema=None, thinking_level=None)` — 공통 LLM 질의/재시도/폴백 메인 루프.

### 5-D. 읽기 증명
1. 마지막 함수: `def ask(self, prompt, temperature=0.5, response_schema=None, thinking_level=None)` (`modules/domain/agents/base_agent.py:236`)
2. 특징 문자열: `f"🔑 [V61.5] API 키 순환: Key {old_idx + 1} → Key {cls._current_key_idx + 1} (총 {len(cls._api_keys)}개)"` (`modules/domain/agents/base_agent.py:199`)
3. import 목록:
- `from modules.core.escape_utils import escape_braces as util_escape_braces` (`modules/domain/agents/base_agent.py:16`)
- `from modules.core.metrics_collector import get_metrics_collector` (`modules/domain/agents/base_agent.py:21`)
- `from google.genai import types` (`modules/domain/agents/base_agent.py:11`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `budget = int(thinking_level)` (`modules/domain/agents/base_agent.py:312`)
- 호출자: 다수 에이전트 `ask(..., thinking_level=...)` 호출 (`modules/domain/agents/arc_ensemble.py:380`, `modules/domain/agents/chief_writer.py:406`, `modules/domain/agents/director_auditor.py:670` 등)
- 상류/하류 컨텍스트:
- 상류: `thinking_level` 타입 검증 없음(문자열이면 맵핑, 그 외는 int 캐스팅)
- 하류: `types.ThinkingConfig(thinking_budget=budget)` (`modules/domain/agents/base_agent.py:313`)
- 실패 시나리오: 비정수 캐스팅 불가 값 유입 시 ValueError/TypeError로 `ask()` 초기화 단계에서 즉시 실패.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `response = self.client.models.generate_content(model=current_model, contents=current_prompt, config=config)` (`modules/domain/agents/base_agent.py:481`)
- 호출자: `ask()`의 quota/rate-limit 폴백 분기 (`modules/domain/agents/base_agent.py:425` 이후)
- 상류/하류 컨텍스트:
- 상류: 기존 모델 실패 후 `current_model`을 다음 폴백 모델로 교체
- 하류: 성공 시 continuation 루프 재진입, 실패 시 외부 except로 탈출
- 실패 시나리오: 폴백 호출 자체가 다시 예외를 던지면 동일 루프에서 다음 폴백을 추가 시도하지 못하고 외부 예외 복구 경로로 직행한다.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `if time.time() - cls._last_rotation_time < cls._MIN_ROTATION_INTERVAL: ... return None` (`modules/domain/agents/base_agent.py:183`)
- 호출자: `ask()` 시작부 키 회전 체크 (`modules/domain/agents/base_agent.py:252`) → `_try_rotate_key()` (`modules/domain/agents/base_agent.py:169`)
- 상류/하류 컨텍스트:
- 상류: `_key_rotation_pending` 플래그 기반 회전 요청
- 하류: 회전 불가 시 기존 키/클라이언트 유지
- 실패 시나리오: 짧은 시간에 연속 429가 발생하면 회전 보류로 동일 키 재시도 비율이 올라가 복구 지연.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 63 완료

## Round 64 — modules/domain/agents/base_agent.py (L601~end)

### 진행 통계 업데이트
- 총 발견: 55건 (CRITICAL: 0, HIGH: 49, MEDIUM: 6)
- 라운드 진행: 64/100

### 5-A. 파일 구조 요약
- `modules/domain/agents/base_agent.py:685` `def _escape_braces(self, text, force=False) -> str` — 프롬프트 중괄호 이스케이프.
- `modules/domain/agents/base_agent.py:717` `def _classify_error(self, error: Exception) -> str` — 오류 분류기.
- `modules/domain/agents/base_agent.py:733` `def _check_connectivity(self, timeout: int = 15) -> bool` — 네트워크 연결 점검.
- `modules/domain/agents/base_agent.py:775` `def _validate_response(self, response: str) -> dict` — 백업 응답 유효성 검사.
- `modules/domain/agents/base_agent.py:804` `def _try_merge_responses(self, partial: str, backup: str) -> str` — 부분 응답 병합 복구.
- `modules/domain/agents/base_agent.py:859` `def _extract_json_robust(self, text)` — 자가 복구 JSON 파서.
- `modules/domain/agents/base_agent.py:973` `def _parse_and_repair_hard(self, json_str) -> dict` — 하드 리페어 파싱.
- `modules/domain/agents/base_agent.py:1010` `def _get_or_create_context_cache(self, cache_type: str, content: str, ttl_seconds: int = 1800, project_name: str = "") -> dict` — 컨텍스트 캐시 생성/재사용.
- `modules/domain/agents/base_agent.py:1106` `def _ask_with_cached_context(self, cache_name: str, prompt: str, temperature: float = 0.3, thinking_level=None, full_prompt_fallback: str = "") -> str` — 캐시 기반 질의.
- `modules/domain/agents/base_agent.py:1173` `def merge_contexts_for_caching(self, items: list, item_type: str = "blueprint") -> str` — 캐싱용 컨텍스트 병합.

### 5-D. 읽기 증명
1. 마지막 함수: `def merge_contexts_for_caching(self, items: list, item_type: str = "blueprint") -> str` (`modules/domain/agents/base_agent.py:1173`)
2. 특징 문자열: `logging.warning("⚠️ [V61.9] 캐싱 중 API 제한 감지 → 키 전환 예약 (현재 작업은 캐시 없이 진행)")` (`modules/domain/agents/base_agent.py:1098`)
3. import 목록:
- `from modules.core.escape_utils import escape_braces as util_escape_braces` (`modules/domain/agents/base_agent.py:16`)
- `from modules.core.metrics_collector import get_metrics_collector` (`modules/domain/agents/base_agent.py:21`)
- `import ast` (`modules/domain/agents/base_agent.py:1`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()[:16]` (`modules/domain/agents/base_agent.py:1027`)
- 호출자: `_get_or_create_context_cache()` 직접 호출 경로 (연속성 캐싱 계층)
- 상류/하류 컨텍스트:
- 상류: `content` 타입 검증 없음
- 하류: cache_key 생성/재사용 분기 (`modules/domain/agents/base_agent.py:1028`)
- 실패 시나리오: content가 str이 아니면 `.encode`에서 AttributeError로 캐시 로직이 즉시 실패.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `budget = int(thinking_level)` (`modules/domain/agents/base_agent.py:1148`)
- 호출자: `_ask_with_cached_context()` (`modules/domain/agents/base_agent.py:1106`)
- 상류/하류 컨텍스트:
- 상류: thinking_level 타입 제한 없음
- 하류: `types.ThinkingConfig(thinking_budget=budget)` (`modules/domain/agents/base_agent.py:1149`)
- 실패 시나리오: 비정수 값 유입 시 ValueError/TypeError로 캐시 질의 경로가 예외를 발생시켜 일반 ask 폴백으로 강제 전환.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `for item in items:` 후 `ep_num = item.get("ep_num", "?")` (`modules/domain/agents/base_agent.py:1187`, `modules/domain/agents/base_agent.py:1189`)
- 호출자: `merge_contexts_for_caching()` (`modules/domain/agents/base_agent.py:1173`)
- 상류/하류 컨텍스트:
- 상류: items 원소 타입 검증 없음
- 하류: blueprint/manuscript 텍스트 병합 (`modules/domain/agents/base_agent.py:1204`~`modules/domain/agents/base_agent.py:1229`)
- 실패 시나리오: 원소가 dict가 아니면 `.get`에서 AttributeError가 발생해 컨텍스트 병합 전체가 중단된다.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 64 완료

## Round 65 — modules/core/prompt_builder.py

### 진행 통계 업데이트
- 총 발견: 56건 (CRITICAL: 0, HIGH: 50, MEDIUM: 6)
- 라운드 진행: 65/100

### 5-A. 파일 구조 요약
- `modules/core/prompt_builder.py:24` `class PromptBuilder` — Writer/Stage2/검증 프롬프트 조립기.
- `modules/core/prompt_builder.py:122` `def generate_high_impact_zone_guide(self, blueprint: dict, target_len: int = ManuscriptLimits.TARGET_LENGTH) -> str` — 장면 분량 가이드.
- `modules/core/prompt_builder.py:451` `def generate_writer_guidance_v60_8(self, blueprint: dict, prev_manuscript: str = "", episode_bibles: list = None, cliche_check_result: dict = None, target_len: int = ManuscriptLimits.TARGET_LENGTH) -> str` — Writer 가이드 통합.
- `modules/core/prompt_builder.py:514` `def generate_arc_context_v60(self, all_refined_arcs: list, current_arc_no: int = None) -> str` — Arc 연속성 컨텍스트 생성.
- `modules/core/prompt_builder.py:562` `def generate_arc_context_fallback(self, all_refined_arcs: list) -> str` — StateExtractor 실패 시 Python fallback.
- `modules/core/prompt_builder.py:764` `def build_item_acquisition_timeline(self, up_to_ep: int) -> str` — 화별 아이템 타임라인 생성.
- `modules/core/prompt_builder.py:856` `def build_validation_context(self, ep_num: int, blueprint: dict = None, mode: str = "MANUSCRIPT", blueprint_text: str = "") -> dict` — validator 컨텍스트 구성.

### 5-D. 읽기 증명
1. 마지막 함수: `def get_character_traits(self) -> dict` (`modules/core/prompt_builder.py:936`)
2. 특징 문자열: `logging.warning(f"[PromptBuilder] item timeline build failed: {e}")` (`modules/core/prompt_builder.py:849`)
3. import 목록:
- `from modules.core.constants import ManuscriptLimits` (`modules/core/prompt_builder.py:13`)
- `import json` (`modules/core/prompt_builder.py:9`)
- `import re` (`modules/core/prompt_builder.py:11`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `if item and item not in _seen_item_names:` (`modules/core/prompt_builder.py:582`)
- 호출자: `stage2_orchestrator.py:239` `last_refined_context = self.ctx.generate_arc_context_v60(all_refined_arcs, batch_start + 1)` → `main_a.py:651` → `generate_arc_context_v60()` → fallback 경로(`modules/core/prompt_builder.py:560`)
- 상류/하류 컨텍스트:
- 상류: `items_acquired = state_constraints.get("items_acquired", [])` (`modules/core/prompt_builder.py:579`)
- 하류: `_seen_item_names.add(item)` (`modules/core/prompt_builder.py:583`)
- 실패 시나리오: `items_acquired` 원소에 dict가 섞이면 set membership/add에서 `TypeError: unhashable type: 'dict'`.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `"items_tracked": len(cumulative_state.get("inventory", {}).get("current_items", [])),` (`modules/core/prompt_builder.py:544`)
- 호출자: `stage2_orchestrator.py:239` / `stage2_finalizer.py:313`에서 `generate_arc_context_v60()` 호출.
- 상류/하류 컨텍스트:
- 상류: `cumulative_state = state_extractor.extract_cumulative_state(all_refined_arcs)` (`modules/core/prompt_builder.py:533`)
- 하류: 예외 시 fallback 전환 (`modules/core/prompt_builder.py:550`, `modules/core/prompt_builder.py:560`)
- 실패 시나리오: extractor가 dict가 아닌 값을 반환하면 `.get`에서 AttributeError.
- 판정: 안전(동일 함수 try/except로 fallback 전환).

3. 위험 지점
- 코드 원문: `npc_name = npc.get("name", "") or npc.get("Name", "")` (`modules/core/prompt_builder.py:897`)
- 호출자: `state_service.py:132` `return self._prompt_builder.build_validation_context(...)`
- 상류/하류 컨텍스트:
- 상류: `npc_lib = asset_lib.get("KeyNPCs", []) or asset_lib.get("Key_NPCs", [])` (`modules/core/prompt_builder.py:895`)
- 하류: `context["npc_profiles"][npc_name] = npc` (`modules/core/prompt_builder.py:899`)
- 실패 시나리오: `npc_lib` 원소가 dict가 아니면 `.get` 예외 가능.
- 판정: 안전(외부 try/except에서 비차단 처리, `modules/core/prompt_builder.py:910`~`modules/core/prompt_builder.py:916`).

### 5-C. 발견된 버그
### [HIGH] modules/core/prompt_builder.py:582 — Arc fallback에서 dict 아이템 처리 실패로 Stage2 컨텍스트 생성 중단

**문제**: `items_acquired` 원소를 set membership으로 바로 비교한다. dict 원소 유입 시 unhashable TypeError로 fallback 전체가 중단된다.

**문제 코드**:
```python
items_acquired = state_constraints.get("items_acquired", [])
if items_acquired:
    for item in items_acquired:
        if item and item not in _seen_item_names:
            _seen_item_names.add(item)
            all_acquired_items.append(f"Arc{arc_label}: {item}")
```

**호출 체인**: `modules/core/stage2_orchestrator.py:239` → `main_a.py:651` → `modules/core/prompt_builder.py:514` → `modules/core/prompt_builder.py:560` → `modules/core/prompt_builder.py:582`

**수정 제안**:
```python
for item in items_acquired:
    if isinstance(item, dict):
        item_name = item.get("name") or item.get("Item") or str(item)
    else:
        item_name = str(item) if item is not None else ""
    if item_name and item_name not in _seen_item_names:
        _seen_item_names.add(item_name)
        all_acquired_items.append(f"Arc{arc_label}: {item_name}")
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 65 완료

## Round 66 — modules/core/prompt_loader.py + modules/core/prompt_optimizer.py

### 진행 통계 업데이트
- 총 발견: 57건 (CRITICAL: 0, HIGH: 51, MEDIUM: 6)
- 라운드 진행: 66/100

### 5-A. 파일 구조 요약
- `modules/core/prompt_loader.py:21` `class PromptLoader` — YAML 프롬프트 로더/캐시.
- `modules/core/prompt_loader.py:62` `def _load_yaml_file(self, domain: str) -> dict[str, str]` — 도메인 YAML 파싱.
- `modules/core/prompt_loader.py:146` `def load(self, domain: str, key: str, **kwargs: Any) -> str | None` — 템플릿 로드+치환.
- `modules/core/prompt_optimizer.py:14` `class PromptOptimizer` — 점수 기반 프롬프트 개선.
- `modules/core/prompt_optimizer.py:31` `def analyze_validation_results(self, results: list[dict[str, Any]]) -> dict[str, Any]` — 검증 결과 통계화.
- `modules/core/prompt_optimizer.py:181` `def optimize_prompt_iteratively(self, original_prompt: str, validation_results: list[dict], target_score: float = 80.0, max_iterations: int = 5) -> tuple[str, list[dict]]` — 반복 최적화 루프.
- `modules/core/prompt_optimizer.py:373` `def quick_optimize(prompt: str, validation_results: list[dict], prompt_name: str = "optimized") -> tuple[str, str]` — 간편 최적화 엔트리.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def invalidate_cache(self, domain: str | None = None) -> None` (`modules/core/prompt_loader.py:187`)
- `def quick_optimize(prompt: str, validation_results: list[dict], prompt_name: str = "optimized") -> tuple[str, str]` (`modules/core/prompt_optimizer.py:373`)
2. 특징 문자열:
- `logging.warning(f"[PromptLoader] Template substitution failed for {domain}/{key}: {e}")` (`modules/core/prompt_loader.py:172`)
- `report.append("PROMPT OPTIMIZATION ANALYSIS")` (`modules/core/prompt_optimizer.py:292`)
3. import 목록:
- `import threading` (`modules/core/prompt_loader.py:16`)
- `from pathlib import Path` (`modules/core/prompt_loader.py:17`)
- `import statistics` (`modules/core/prompt_optimizer.py:9`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `key_pattern = re.compile(r"^([A-Z][A-Z0-9_]+):\s*\|")` (`modules/core/prompt_loader.py:80`)
- 호출자: 다수 에이전트의 `PromptLoader().load(...)` (`modules/domain/agents/director_ensemble.py:342`, `modules/domain/agents/arc_ensemble.py:352`, `modules/domain/agents/chief_writer_prompts.py:78`)
- 상류/하류 컨텍스트:
- 상류: YAML 파일 원문 직접 파싱 (`modules/core/prompt_loader.py:86`~`modules/core/prompt_loader.py:94`)
- 하류: 키 미탐지 시 `if key not in prompts: return None` (`modules/core/prompt_loader.py:158`~`modules/core/prompt_loader.py:159`)
- 실패 시나리오: 키가 소문자/혼합 케이스면 파싱 누락되어 템플릿을 찾지 못하고 호출자가 fallback 경로로 빠진다.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `breakdown = r.get("scoring_result", {}).get("breakdown", {})` (`modules/core/prompt_optimizer.py:85`)
- 호출자: `analyze_validation_results()` (`modules/core/prompt_optimizer.py:55`) → `_analyze_category_scores()`
- 상류/하류 컨텍스트:
- 상류: `results` 원소 타입/shape 강제 없음 (`modules/core/prompt_optimizer.py:31`)
- 하류: `if category in breakdown:` (`modules/core/prompt_optimizer.py:86`)
- 실패 시나리오: `scoring_result`가 `None`이면 `.get("breakdown")`에서 AttributeError.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `analysis = optimizer.analyze_validation_results(validation_results)` (`modules/core/prompt_optimizer.py:388`)
- 호출자: `quick_optimize()` (`modules/core/prompt_optimizer.py:373`)
- 상류/하류 컨텍스트:
- 상류: 빈 입력에서 `return {"error": "No results to analyze"}` (`modules/core/prompt_optimizer.py:41`~`modules/core/prompt_optimizer.py:42`)
- 하류: `improved_prompt = optimizer.generate_improved_prompt(prompt, analysis["weaknesses"], analysis)` (`modules/core/prompt_optimizer.py:391`)
- 실패 시나리오: `validation_results`가 빈 리스트면 `analysis["weaknesses"]` 접근에서 KeyError.
- 판정: BUG.

### 5-C. 발견된 버그
### [HIGH] modules/core/prompt_optimizer.py:391 — 빈 검증 결과에서 `analysis` 계약 불일치로 KeyError

**문제**: `analyze_validation_results([])`는 `{"error": ...}` 형태를 반환하지만, `quick_optimize()`는 `analysis["weaknesses"]`를 무조건 접근한다.

**문제 코드**:
```python
analysis = optimizer.analyze_validation_results(validation_results)

# 개선
improved_prompt = optimizer.generate_improved_prompt(prompt, analysis["weaknesses"], analysis)
```

**호출 체인**: `modules/core/prompt_optimizer.py:373` `quick_optimize()` → `modules/core/prompt_optimizer.py:388` `analyze_validation_results()` → `modules/core/prompt_optimizer.py:391` KeyError

**수정 제안**:
```python
analysis = optimizer.analyze_validation_results(validation_results)
if "error" in analysis:
    return prompt, f"Prompt optimization skipped: {analysis['error']}"
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 66 완료

## Round 67 — modules/core/project_manager.py

### 진행 통계 업데이트
- 총 발견: 57건 (CRITICAL: 0, HIGH: 51, MEDIUM: 6)
- 라운드 진행: 67/100

### 5-A. 파일 구조 요약
- `modules/core/project_manager.py:36` `class ProjectPaths` — 프로젝트 경로 컨테이너 dataclass.
- `modules/core/project_manager.py:44` `class ProjectContext` — 프로젝트 상태/DB/파일 저장 관리.
- `modules/core/project_manager.py:176` `def save_v20_anchor(self, stage, data)` — bible/volumes/arcs 앵커 저장.
- `modules/core/project_manager.py:455` `def commit_full_episode_data(self, ep_num, manuscript_data, martial_data, state_data, causal_links, karma_data, lore_data, recovered_seeds, memory) -> bool` — 에피소드 원자 커밋 파이프라인.
- `modules/core/project_manager.py:631` `def get_latest_episode_number(self) -> int` — DB+파일 하이브리드 next-ep 계산.
- `modules/core/project_manager.py:808` `def sync_existing_manuscripts(self, memory) -> bool` — 기존 draft 동기화.
- `modules/core/project_manager.py:875` `def auto_backtrack_v35(self, error_report, memory, *, world_state=None, fact_ledger=None)` — 자동 되감기/롤백.

### 5-D. 읽기 증명
1. 마지막 함수: `def get_surgery_intelligence(self, limit=3) -> str` (`modules/core/project_manager.py:928`)
2. 특징 문자열: `logging.warning(f"⚠️ [Backtrack Error] 자동 되감기 실패: {e}")` (`modules/core/project_manager.py:921`)
3. import 목록:
- `from .db_manager import DBError, DBManager` (`modules/core/project_manager.py:10`)
- `import json` (`modules/core/project_manager.py:1`)
- `from pathlib import Path` (`modules/core/project_manager.py:5`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `target.setdefault("NPC_Martial_HUD", {}).update(new_hud)` (`modules/core/project_manager.py:530`)
- 호출자: `commit_full_episode_data()` 내부 NPC HUD 병합 분기 (`modules/core/project_manager.py:455`)
- 상류/하류 컨텍스트:
- 상류: `old_hud = target.get("NPC_Martial_HUD", {})` 후 non-dict를 `{}`로만 로컬 보정 (`modules/core/project_manager.py:501`~`modules/core/project_manager.py:504`)
- 하류: 직후 `break`로 루프 종료 (`modules/core/project_manager.py:531`)
- 실패 시나리오: `target["NPC_Martial_HUD"]`가 dict가 아니면 `setdefault`가 기존 값을 반환해 `.update`에서 AttributeError.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `old_set = set(old_equip) if isinstance(old_equip, list) else set()` / `new_set = set(new_equip) if isinstance(new_equip, list) else set()` (`modules/core/project_manager.py:517`, `modules/core/project_manager.py:518`)
- 호출자: `commit_full_episode_data()` 내부 장비 diff 계산 (`modules/core/project_manager.py:512`~`modules/core/project_manager.py:524`)
- 상류/하류 컨텍스트:
- 상류: `old_equip = old_hud.get("equipment", [])`, `new_equip = new_hud.get("equipment", [])` (`modules/core/project_manager.py:513`, `modules/core/project_manager.py:514`)
- 하류: `added = new_set - old_set` (`modules/core/project_manager.py:519`)
- 실패 시나리오: 장비 리스트 원소에 dict가 포함되면 `set(...)`에서 unhashable TypeError.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `_m = _re.match(r"ep_(\d+)\.txt", f.name)` (`modules/core/project_manager.py:649`)
- 호출자: Stage4 루프의 next-ep 계산 (`modules/core/stage4_orchestrator.py:366`) → `current_project.get_latest_episode_number()`
- 상류/하류 컨텍스트:
- 상류: draft 파일 수집 `draft_files = list(self.paths.drafts.glob("*.txt"))` (`modules/core/project_manager.py:645`)
- 하류: `return max(db_ep, file_ep + 1 if file_ep > 0 else 0)` (`modules/core/project_manager.py:654`)
- 실패 시나리오: 파일명이 `1.txt` 등 레거시 패턴이면 인식하지 못해 파일 기반 ep가 0으로 남아 next-ep가 과소 계산될 수 있다.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 67 완료

## Round 68 — modules/core/services/state_service.py + project_service.py + ui_service.py + audit_service.py

### 진행 통계 업데이트
- 총 발견: 57건 (CRITICAL: 0, HIGH: 51, MEDIUM: 6)
- 라운드 진행: 68/100

### 5-A. 파일 구조 요약
- `modules/core/services/state_service.py:18` `class StateService` — 상태/검증 보조 서비스.
- `modules/core/services/state_service.py:57` `def validate_arc_mapping(self, refined_arc, enriched_block, expected_arc_no, expected_ep_start)` — Arc 번호/범위 보정.
- `modules/core/services/state_service.py:237` `def validate_arc_data_fields(self, arc_data: dict, arc_idx: int) -> dict | None` — Arc 필수 필드 자동 복구.
- `modules/core/services/project_service.py:17` `class ProjectService` — 리셋/되감기/롤백 실행 서비스.
- `modules/core/services/project_service.py:86` `def rollback_episode(self) -> None` — HUD/DB/파일/벡터 롤백.
- `modules/core/services/ui_service.py:14` `class UIService` — 파일 선택/입력 UI 헬퍼.
- `modules/core/services/ui_service.py:105` `def get_int_input(self, prompt: str, default: int | None = None, min_val: int | None = None, max_val: int | None = None, attempts: int = 3) -> int | None` — 정수 입력 유틸.
- `modules/core/services/audit_service.py:15` `class AuditService` — runtime audit 버퍼링/파일 기록.
- `modules/core/services/audit_service.py:72` `def write_audit_summary(self, tag: str = "snapshot") -> None` — 요약 JSON 저장.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def validate_blueprint_integrity(self, blueprint: Any) -> bool` (`modules/core/services/state_service.py:342`)
- `def wipe_production_data(self) -> None` (`modules/core/services/project_service.py:222`)
- `def get_int_input(self, prompt: str, default: int | None = None, min_val: int | None = None, max_val: int | None = None, attempts: int = 3) -> int | None` (`modules/core/services/ui_service.py:105`)
- `def write_audit_summary(self, tag: str = "snapshot") -> None` (`modules/core/services/audit_service.py:72`)
2. 특징 문자열:
- `self._ui.log(f"⚠️ [V43] arc_data가 딕셔너리가 아닙니다: {type(arc_data)}")` (`modules/core/services/state_service.py:240`)
- `self._ui.log(f"❌ 롤백 실패: {e}")` (`modules/core/services/project_service.py:216`)
- `self._ui.log("⚠️ 숫자만 입력 가능합니다.")` (`modules/core/services/ui_service.py:119`)
- `self._ui_log(f"⚠️ [Audit] 요약 기록 실패: {e}")` (`modules/core/services/audit_service.py:92`)
3. import 목록:
- `from modules.core.constants import Emojis, GenreTypes, VolumeSettings` (`modules/core/services/state_service.py:15`)
- `from modules.core.constants import HUDKeys` (`modules/core/services/project_service.py:14`)
- `import json` (`modules/core/services/audit_service.py:9`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문:
- `"ep_end": int(arc_data.get("ep_start", 1))` (`modules/core/services/state_service.py:252`)
- `+ int(arc_data.get("ep_count", VolumeSettings.EPISODES_PER_ARC))` (`modules/core/services/state_service.py:253`)
- 호출자: `main_a.py:2405` `_validate_arc_data_fields()` thin delegate.
- 상류/하류 컨텍스트:
- 상류: `required_defaults = { ... }` 딕셔너리 구성 시점에 즉시 산술 수행 (`modules/core/services/state_service.py:243`~`modules/core/services/state_service.py:255`)
- 하류: 타입 복구 루프는 이후에 실행 (`modules/core/services/state_service.py:258`~`modules/core/services/state_service.py:276`)
- 실패 시나리오: `ep_start`/`ep_count`가 비수치 문자열이면 ValueError가 복구 루프 전에 발생.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `past_data = json.loads(row["data"]) if row["data"] else {}` (`modules/core/services/project_service.py:125`)
- 호출자: `main_a.py:2684` `_rollback_episode()` → `ProjectService.rollback_episode()`
- 상류/하류 컨텍스트:
- 상류: `row = project.db.cursor.fetchone()` (`modules/core/services/project_service.py:123`)
- 하류: 예외 시 전체 롤백 흐름 중단 (`modules/core/services/project_service.py:215`~`modules/core/services/project_service.py:219`)
- 실패 시나리오: state_logs 레코드 파손 시 JSON 파싱 예외로 롤백이 실패 처리된다.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `summary["counts"][evt["type"]] = summary["counts"].get(evt["type"], 0) + 1` (`modules/core/services/audit_service.py:86`)
- 호출자: `main_a.py:2352` `_write_audit_summary()` thin delegate.
- 상류/하류 컨텍스트:
- 상류: `self._runtime_audit`는 `audit_event()`가 append (`modules/core/services/audit_service.py:49`)하지만 외부 주입 가능
- 하류: summary 파일 저장 (`modules/core/services/audit_service.py:90`)
- 실패 시나리오: `type` 키가 없는 이벤트가 섞이면 KeyError로 요약 작성 실패.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 68 완료

## Round 69 — modules/core/adaptive_retry.py

### 진행 통계 업데이트
- 총 발견: 57건 (CRITICAL: 0, HIGH: 51, MEDIUM: 6)
- 라운드 진행: 69/100

### 5-A. 파일 구조 요약
- `modules/core/adaptive_retry.py:42` `class ErrorType(Enum)` — 실패 타입 분류 enum.
- `modules/core/adaptive_retry.py:70` `class AdaptiveRetryStrategy` — 오류 타입별 재시도 전략.
- `modules/core/adaptive_retry.py:188` `def should_retry(self, task_id: str, error_info: dict) -> tuple[bool, ErrorType]` — 재시도 여부 판단.
- `modules/core/adaptive_retry.py:214` `def get_retry_strategy(self, task_id: str, error_type: ErrorType, error_info: dict) -> dict[str, Any]` — 주입 전략 계산.
- `modules/core/adaptive_retry.py:473` `class AdaptiveRetryManager` — 에피소드/에이전트별 실패 이력 관리자.
- `modules/core/adaptive_retry.py:577` `def get_retry_guidance(self, ep_num: int, agent: str, current_attempt: int = 1) -> dict[str, Any]` — 리트라이 가이드 생성.
- `modules/core/adaptive_retry.py:793` `def retry_with_feedback(func, max_attempts: int = 3, on_failure=None, on_success=None, logger=None, task_name: str = "") -> tuple` — 범용 재시도 헬퍼.

### 5-D. 읽기 증명
1. 마지막 함수: `def retry_with_feedback(func, max_attempts: int = 3, on_failure=None, on_success=None, logger=None, task_name: str = "") -> tuple` (`modules/core/adaptive_retry.py:793`)
2. 특징 문자열: `_log(f"[retry_with_feedback] {task_name} attempt {attempt + 1} 성공")` (`modules/core/adaptive_retry.py:847`)
3. import 목록:
- `import threading` (`modules/core/adaptive_retry.py:50`)
- `from dataclasses import dataclass, field` (`modules/core/adaptive_retry.py:52`)
- `from enum import Enum` (`modules/core/adaptive_retry.py:53`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `message = str(error_info.get("message", "")).lower()` (`modules/core/adaptive_retry.py:130`)
- 호출자: `AdaptiveRetryManager.record_failure()`에서 `self.strategy.classify_error(error_info)` (`modules/core/adaptive_retry.py:536`)
- 상류/하류 컨텍스트:
- 상류: `record_failure(..., error_info: dict, ...)` 타입 힌트만 있고 런타임 검증 없음 (`modules/core/adaptive_retry.py:522`)
- 하류: 오류 분류 후 통계 누적 (`modules/core/adaptive_retry.py:550`~`modules/core/adaptive_retry.py:555`)
- 실패 시나리오: `error_info`가 dict가 아니면 `.get`에서 AttributeError.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `if on_success is None or on_success(result):` (`modules/core/adaptive_retry.py:845`)
- 호출자:
- `modules/domain/agents/analyst.py:894` `retry_with_feedback(...)`
- `modules/core/stage01_helpers.py:601` `retry_with_feedback(...)`
- 상류/하류 컨텍스트:
- 상류: `result = func(attempt, feedback)` (`modules/core/adaptive_retry.py:835`)
- 하류: success면 즉시 return (`modules/core/adaptive_retry.py:848`)
- 실패 시나리오: `on_success(result)` 내부 예외는 try/except로 감싸지지 않아 루프를 깨고 상위로 전파될 수 있다.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `if task_id not in self.contexts: self.contexts[task_id] = RetryContext()` (`modules/core/adaptive_retry.py:105`~`modules/core/adaptive_retry.py:106`)
- 호출자: `should_retry()`/`get_retry_strategy()`의 `ctx = self.get_context(task_id)` (`modules/core/adaptive_retry.py:199`, `modules/core/adaptive_retry.py:232`)
- 상류/하류 컨텍스트:
- 상류: 컨텍스트 초기화는 task_id 기준
- 하류: 재시도 횟수 누적 `ctx.attempt += 1` (`modules/core/adaptive_retry.py:211`)
- 실패 시나리오: 같은 task_id를 장기간 재사용하면 컨텍스트 reset 누락 시 과거 시도 횟수가 남아 조기 종료 가능.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 69 완료

## Round 70 — modules/core/feedback_system.py

### 진행 통계 업데이트
- 총 발견: 57건 (CRITICAL: 0, HIGH: 51, MEDIUM: 6)
- 라운드 진행: 70/100

### 5-A. 파일 구조 요약
- `modules/core/feedback_system.py:20` `class FeedbackSystem` — Stage별 피드백 생성 모듈.
- `modules/core/feedback_system.py:31` `def build_structured_feedback(self, decision: str, reason: str, violations: list = None, severity: str = "MEDIUM", fix_instructions: str = "") -> dict` — 구조화 피드백 생성.
- `modules/core/feedback_system.py:81` `def quantify_reject_feedback(self, reason: str, content_length: int, audit_result: dict) -> list` — 정량형 수정 지시 생성.
- `modules/core/feedback_system.py:311` `def build_minimal_arc_context(self, prev_arcs: list, protagonist_name: str) -> str` — 최소 Arc 컨텍스트 생성.
- `modules/core/feedback_system.py:364` `def generate_structured_arc_feedback(self, continuity_result: dict, prev_arcs: list = None, arc_no: int = 1) -> str` — Stage2용 구조화 피드백.
- `modules/core/feedback_system.py:688` `def get_adaptive_feedback_intensity(self, retry_count: int, stage: int = 4) -> dict` — 재시도 강도 조절.
- `modules/core/feedback_system.py:814` `def simplify_prompt_for_retry(self, enhanced_feedback: str, core_feedback: str, attempt: int) -> str` — retry 단순 프롬프트 생성.

### 5-D. 읽기 증명
1. 마지막 함수: `def simplify_prompt_for_retry(self, enhanced_feedback: str, core_feedback: str, attempt: int) -> str` (`modules/core/feedback_system.py:814`)
2. 특징 문자열: `f"⚠️ Blueprint 설계가 {len(architect_failures)}회 연속 실패했습니다."` (`modules/core/feedback_system.py:637`)
3. import 목록:
- `from modules.core.constants import ManuscriptLimits` (`modules/core/feedback_system.py:17`)
- 프로젝트 내부 추가 import 없음(단일 constants 의존)
- 외부/표준 라이브러리 import 없음

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `sorted_violations = sorted(violations, key=lambda v: priority_map.get(v.get("type", "unknown"), 10))` (`modules/core/feedback_system.py:55`)
- 호출자: `build_structured_feedback()` (`modules/core/feedback_system.py:31`) 내부 `self.get_violation_priority(violations or [])`
- 상류/하류 컨텍스트:
- 상류: `violations` 원소 타입 검증 없음
- 하류: `return [v.get("type", "unknown") for v in sorted_violations]` (`modules/core/feedback_system.py:56`)
- 실패 시나리오: violations 원소가 문자열이면 `.get`에서 AttributeError.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `inventory_str = ", ".join(inventory) if inventory else "없음"` (`modules/core/feedback_system.py:343`)
- 호출자: `main_a.py:566` `_build_minimal_arc_context()` thin delegate.
- 상류/하류 컨텍스트:
- 상류: `inventory = joint.get("physical_inventory", [])` (`modules/core/feedback_system.py:338`)
- 하류: 반환 컨텍스트 문자열 삽입 (`modules/core/feedback_system.py:347`~`modules/core/feedback_system.py:358`)
- 실패 시나리오: `inventory` 리스트에 dict 원소가 포함되면 `join`에서 `TypeError: sequence item ... expected str instance`.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `v_type = v.get("type", "unknown")` (`modules/core/feedback_system.py:386`)
- 호출자: `generate_structured_arc_feedback()` (`modules/core/feedback_system.py:364`)
- 상류/하류 컨텍스트:
- 상류: `violations = continuity_result.get("violations", [])` (`modules/core/feedback_system.py:369`)
- 하류: 피드백 라인 조립 (`modules/core/feedback_system.py:387`~`modules/core/feedback_system.py:450`)
- 실패 시나리오: violations 리스트에 비dict 원소 유입 시 AttributeError.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 70 완료

## Round 71 — modules/core/quality_dashboard.py

### 진행 통계 업데이트
- 총 발견: 57건 (CRITICAL: 0, HIGH: 51, MEDIUM: 6)
- 라운드 진행: 71/100

### 5-A. 파일 구조 요약
- `modules/core/quality_dashboard.py:24` `class QualityDashboard` — 품질 지표 수집/분석 대시보드.
- `modules/core/quality_dashboard.py:106` `def record_validation(self, ep_num: int, result: dict, stage: int = 4)` — validation 기록.
- `modules/core/quality_dashboard.py:190` `def get_summary(self) -> dict` — 요약 지표 집계.
- `modules/core/quality_dashboard.py:431` `def analyze_score_trend(self, stage: int = 4, window: int = 5) -> dict` — 점수 추세 분석.
- `modules/core/quality_dashboard.py:551` `def predict_pass_probability(self, stage: int = 4, current_metrics: dict | None = None) -> dict` — PASS 확률 추정.
- `modules/core/quality_dashboard.py:748` `def detect_score_regression(self, ep_num: int | None = None, stage: int = 4) -> dict[str, Any]` — 점수 급락 감지.
- `modules/core/quality_dashboard.py:1031` `def detect_director_bias(self, selections: list[dict]) -> dict[str, Any]` — Director 선택 편향 분석.
- `modules/core/quality_dashboard.py:1097` `def reset_dashboard() -> None` — 싱글톤 리셋.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def get_dashboard(project_path: Path | None = None) -> QualityDashboard` (`modules/core/quality_dashboard.py:1087`)
- `def reset_dashboard() -> None` (`modules/core/quality_dashboard.py:1097`)
2. 특징 문자열: `logging.info(f"[QualityDashboard] metrics line {line_no} skip: {e}")` (`modules/core/quality_dashboard.py:61`)
3. import 목록:
- `from modules.core.constants import ManuscriptLimits` (`modules/core/quality_dashboard.py:21`)
- `import json` (`modules/core/quality_dashboard.py:13`)
- `from collections import defaultdict` (`modules/core/quality_dashboard.py:16`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `"types": [a.get("type") for a in anomalies],` (`modules/core/quality_dashboard.py:146`)
- 호출자: `record_hud_anomaly()` (`modules/core/quality_dashboard.py:133`)
- 상류/하류 컨텍스트:
- 상류: `anomalies` 원소 타입 검증 없음
- 하류: `_save_record(record)` (`modules/core/quality_dashboard.py:150`)
- 실패 시나리오: anomalies 원소가 dict가 아니면 `.get`에서 AttributeError.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `scored = [r for r in self.validation_history if r.get("stage") == stage and r.get("score", 0) > 0]` (`modules/core/quality_dashboard.py:780`)
- 호출자: `stage4_post_processor.py:420` `self.ctx.quality_dashboard.detect_score_regression(stage=2)`
- 상류/하류 컨텍스트:
- 상류: validation_history는 파일/런타임 혼합 로드 (`modules/core/quality_dashboard.py:52`~`modules/core/quality_dashboard.py:90`)
- 하류: `current_score = int(scored[-1].get("score", 0))` (`modules/core/quality_dashboard.py:806`)
- 실패 시나리오: `score`가 문자열이면 `> 0` 비교에서 TypeError 가능.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `strategy = rec.get("selected_strategy") or "unknown"` (`modules/core/quality_dashboard.py:1049`)
- 호출자: `main_a.py:2018` `bias_result = self.quality_dashboard.detect_director_bias(selections)`
- 상류/하류 컨텍스트:
- 상류: `selections = self.current_project.db.get_selection_analysis(lookback=100)` (`main_a.py:2016`)
- 하류: `by_strategy[str(strategy)].append(rec)` (`modules/core/quality_dashboard.py:1050`)
- 실패 시나리오: selections 원소가 dict가 아니면 `.get`에서 AttributeError.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 71 완료

## Round 72 — modules/core/pattern_tracker.py

### 진행 통계 업데이트
- 총 발견: 57건 (CRITICAL: 0, HIGH: 51, MEDIUM: 6)
- 라운드 진행: 72/100

### 5-A. 파일 구조 요약
- `modules/core/pattern_tracker.py:19` `class PatternTracker` — 장기 패턴 추적/경고 생성기.
- `modules/core/pattern_tracker.py:137` `def analyze_manuscripts(self, manuscripts: list[str], blueprints: list[dict] = None) -> dict` — 최근 window 분석 엔트리.
- `modules/core/pattern_tracker.py:224` `def _analyze_scene_types(self, blueprints: list[dict])` — scene 타입 분포 분석.
- `modules/core/pattern_tracker.py:268` `def _generate_analysis_report(self) -> dict` — 경고/통계 리포트 생성.
- `modules/core/pattern_tracker.py:358` `def should_activate_diversity_sampling(self, report: dict = None) -> tuple[bool, str]` — diversity 샘플링 활성 판정.
- `modules/core/pattern_tracker.py:377` `def generate_writer_injection(self, report: dict = None) -> str` — Writer 주입 경고문 생성.
- `modules/core/pattern_tracker.py:447` `def save_to_db(self, db_manager) -> bool` / `modules/core/pattern_tracker.py:467` `def load_from_db(self, db_manager) -> bool` — 상태 저장/복원.
- `modules/core/pattern_tracker.py:888` `def generate_trend_report_v59(self, trend_result: dict) -> str` — 트렌드 리포트 포맷터.

### 5-D. 읽기 증명
1. 마지막 함수: `def generate_trend_report_v59(self, trend_result: dict) -> str` (`modules/core/pattern_tracker.py:888`)
2. 특징 문자열: `[V48 PATTERN TRACKER: 서사 경고]` (`modules/core/pattern_tracker.py:396`)
3. import 목록:
- `import logging` (`modules/core/pattern_tracker.py:16`)
- `import re` (`modules/core/pattern_tracker.py:17`)
- `from collections import Counter` (`modules/core/pattern_tracker.py:18`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `scene_breakdown = bp.get("scene_breakdown", {})` (`modules/core/pattern_tracker.py:229`)
- 호출자: `analyze_manuscripts()` (`modules/core/pattern_tracker.py:166`) → `narrative_diversity.py:381`
- 상류/하류 컨텍스트:
- 상류: `recent_bp = blueprints[-self.window_size :] if blueprints else []` (`modules/core/pattern_tracker.py:153`)
- 하류: scene type 카운트 누적 (`modules/core/pattern_tracker.py:233`~`modules/core/pattern_tracker.py:241`)
- 실패 시나리오: blueprints 원소가 dict가 아니면 `.get`에서 AttributeError.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `high_warnings = [w for w in warnings if w["severity"] == "HIGH"]` (`modules/core/pattern_tracker.py:392`)
- 호출자: `narrative_diversity.py:459` `pattern_tracker.generate_writer_injection(self._analysis_report)`
- 상류/하류 컨텍스트:
- 상류: `warnings = report.get("warnings", [])` (`modules/core/pattern_tracker.py:387`)
- 하류: 주입 문자열 조립 (`modules/core/pattern_tracker.py:402`~`modules/core/pattern_tracker.py:421`)
- 실패 시나리오: warnings 원소에 `severity` 키가 없으면 KeyError.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `self.window_size = data.get("window_size", 10)` (`modules/core/pattern_tracker.py:472`)
- 호출자: `narrative_diversity.py:529` `self.pattern_tracker.load_from_db(self.context.db)`
- 상류/하류 컨텍스트:
- 상류: `data = db_manager.load_anchor("pattern_tracker")` (`modules/core/pattern_tracker.py:470`)
- 하류: `recent_ms = manuscripts[-self.window_size :]` (`modules/core/pattern_tracker.py:152`)
- 실패 시나리오: DB 데이터 오염으로 `window_size`가 비정수면 슬라이싱/비교 로직에서 TypeError 가능.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 72 완료

## Round 73 — modules/core/genre_guards/base_guard.py

### 진행 통계 업데이트
- 총 발견: 57건 (CRITICAL: 0, HIGH: 51, MEDIUM: 6)
- 라운드 진행: 73/100

### 5-A. 파일 구조 요약
- `modules/core/genre_guards/base_guard.py:16` `class BaseGuard` — 장르 Guard 공통 추상 베이스.
- `modules/core/genre_guards/base_guard.py:34` `def _load_genre_yaml(self, genre_key: str) -> dict` — 장르 YAML 로더.
- `modules/core/genre_guards/base_guard.py:136` `def validate_v20_manuscript(self, content) -> dict` — 원고 순수성 검사.
- `modules/core/genre_guards/base_guard.py:182` `def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]` — 통합 검증 엔트리.
- `modules/core/genre_guards/base_guard.py:299` `def check_state_action_consistency(self, manuscript: str, current_state: dict[str, Any]) -> dict[str, Any]` — 상태/행동 일관성 검사.
- `modules/core/genre_guards/base_guard.py:433` `def check_authority_delegation(self, manuscript: str, context: dict[str, Any]) -> dict[str, Any]` — 권위 위임 정합성 검사.
- `modules/core/genre_guards/base_guard.py:568` `def check_unresolved_conflict(self, manuscript: str, karma_matrix: dict[str, Any], ep_num: int) -> dict[str, Any]` — 미해결 갈등 검사.
- `modules/core/genre_guards/base_guard.py:719` `def check_villain_response(self, manuscript: str, villain_context: dict[str, Any], recent_events: list[dict]) -> dict[str, Any]` — 빌런 반응 검사.

### 5-D. 읽기 증명
1. 마지막 함수: `def check_villain_response(self, manuscript: str, villain_context: dict[str, Any], recent_events: list[dict]) -> dict[str, Any]` (`modules/core/genre_guards/base_guard.py:719`)
2. 특징 문자열: `feedback = f"[{self.get_genre_name()} Guard] {len(all_violations)}건 위반 발견: {summary}"` (`modules/core/genre_guards/base_guard.py:235`)
3. import 목록:
- `import re` (`modules/core/genre_guards/base_guard.py:8`)
- `import yaml` (`modules/core/genre_guards/base_guard.py:13`)
- `from pathlib import Path` (`modules/core/genre_guards/base_guard.py:10`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `matches = re.findall(pattern, manuscript)` (`modules/core/genre_guards/base_guard.py:326`)
- 호출자: `modules/validation/consistency_validator.py:272` `_check_state_action_consistency()` → `guard.check_state_action_consistency(...)`
- 상류/하류 컨텍스트:
- 상류: `impossible_actions = self.get_impossible_actions(current_state)` (`modules/core/genre_guards/base_guard.py:316`)
- 하류: 패턴 매칭 성공 시 violation 누적 (`modules/core/genre_guards/base_guard.py:332`~`modules/core/genre_guards/base_guard.py:339`)
- 실패 시나리오: 장르 YAML/규칙에서 비정상 regex가 들어오면 `re.error`로 검증 루프 자체가 중단된다.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `has_resolution_in_manuscript = any(re.search(rp, manuscript) for rp in resolution_patterns)` (`modules/core/genre_guards/base_guard.py:624`)
- 호출자: `modules/validation/consistency_validator.py:188` `guard.check_unresolved_conflict(...)`
- 상류/하류 컨텍스트:
- 상류: NPC별 hostile/resolved 이벤트 판정 루프 (`modules/core/genre_guards/base_guard.py:595`~`modules/core/genre_guards/base_guard.py:623`)
- 하류: `if resolved or has_resolution_in_manuscript: continue` (`modules/core/genre_guards/base_guard.py:626`)
- 실패 시나리오: 원고 어디엔가 단일 해소 표현이 있으면, 해당 NPC와 무관한 미해결 갈등도 같이 skip될 수 있다.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `has_response = any(re.search(rp, manuscript) for rp in response_patterns)` (`modules/core/genre_guards/base_guard.py:787`)
- 호출자: `modules/validation/consistency_validator.py:212` `guard.check_villain_response(...)`
- 상류/하류 컨텍스트:
- 상류: 빌런명 기반 반응 탐지 실패 시 generic 패턴으로 재검사 (`modules/core/genre_guards/base_guard.py:783`~`modules/core/genre_guards/base_guard.py:787`)
- 하류: `villain_mentioned and not has_response`일 때만 violation 생성 (`modules/core/genre_guards/base_guard.py:790`)
- 실패 시나리오: 빌런이 아닌 다른 문맥의 감정 표현(예: 일반 서술의 "분노")이 반응으로 오인되어 위반이 누락될 수 있다.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 73 완료

## Round 74 — modules/core/genre_guards/wuxia_guard.py

### 진행 통계 업데이트
- 총 발견: 57건 (CRITICAL: 0, HIGH: 51, MEDIUM: 6)
- 라운드 진행: 74/100

### 5-A. 파일 구조 요약
- `modules/core/genre_guards/wuxia_guard.py:13` `class WuxiaGuard(BaseGuard)` — 무협 장르 Guard.
- `modules/core/genre_guards/wuxia_guard.py:16` `def __init__(self) -> None` — YAML 기반 장르 규칙/패턴 초기화.
- `modules/core/genre_guards/wuxia_guard.py:258` `def get_impossible_actions(self, current_state: dict[str, Any]) -> list[dict[str, str]]` — 상태 기반 금지 행동 구성.
- `modules/core/genre_guards/wuxia_guard.py:348` `def get_hierarchy_rules(self) -> dict[str, Any]` — 위계/호칭 규칙 제공.
- `modules/core/genre_guards/wuxia_guard.py:605` `def check_modern_notation(self, text: str) -> list[dict[str, str]]` — 현대 표기 금지 패턴 탐지.
- `modules/core/genre_guards/wuxia_guard.py:629` `def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]` — base 검증 + 무협 특화 검증.

### 5-D. 읽기 증명
1. 마지막 함수: `def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]` (`modules/core/genre_guards/wuxia_guard.py:629`)
2. 특징 문자열: `result["feedback"] = f"[무협 Guard] {len(result['violations'])}건: {result['summary']}"` (`modules/core/genre_guards/wuxia_guard.py:660`)
3. import 목록:
- `from typing import Any` (`modules/core/genre_guards/wuxia_guard.py:8`)
- `from .base_guard import BaseGuard` (`modules/core/genre_guards/wuxia_guard.py:10`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `self.FORBIDDEN_MODERN_PATTERNS = [(p["pattern"], p["reason"]) for p in _raw_modern]` (`modules/core/genre_guards/wuxia_guard.py:197`)
- 호출자: `modules/validation/consistency_validator.py:54` `return WuxiaGuard()`
- 상류/하류 컨텍스트:
- 상류: `_raw_modern = cfg.get("forbidden_modern_patterns", None)` (`modules/core/genre_guards/wuxia_guard.py:195`)
- 하류: 초기화 실패 시 Guard 인스턴스 생성 실패 (validator 경로에서 해당 장르 검사 비정상화)
- 실패 시나리오: YAML 항목에 `pattern`/`reason` 키가 빠지면 KeyError가 발생해 Guard 생성이 중단된다.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `matches = re.findall(pattern, text, re.IGNORECASE)` (`modules/core/genre_guards/wuxia_guard.py:617`)
- 호출자: `modules/core/genre_guards/wuxia_guard.py:634` `run_deep_validation()` 내부 `check_modern_notation(...)`
- 상류/하류 컨텍스트:
- 상류: 패턴 원천은 YAML/초기화 리스트 (`modules/core/genre_guards/wuxia_guard.py:195`~`modules/core/genre_guards/wuxia_guard.py:216`)
- 하류: 위반 항목을 `result["violations"]`에 누적 (`modules/core/genre_guards/wuxia_guard.py:635`~`modules/core/genre_guards/wuxia_guard.py:640`)
- 실패 시나리오: 잘못된 regex 패턴이 들어오면 `re.error`로 deep validation이 중단될 수 있다.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `if move in manuscript:` (`modules/core/genre_guards/wuxia_guard.py:648`)
- 호출자: `modules/domain/agents/director_auditor.py:83` `self._d.guard.run_deep_validation(manuscript, current_state)`
- 상류/하류 컨텍스트:
- 상류: 저경지 구간에서만 금지 무공 목록 적용 (`modules/core/genre_guards/wuxia_guard.py:644`~`modules/core/genre_guards/wuxia_guard.py:647`)
- 하류: 즉시 HIGH violation 추가 (`modules/core/genre_guards/wuxia_guard.py:649`~`modules/core/genre_guards/wuxia_guard.py:655`)
- 실패 시나리오: 형태소 경계 없이 substring 검사하므로 이름/비유 문맥의 우연한 포함까지 위반으로 분류될 수 있다.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 74 완료

## Round 75 — modules/core/genre_guards/hunter_guard.py

### 진행 통계 업데이트
- 총 발견: 58건 (CRITICAL: 0, HIGH: 51, MEDIUM: 7)
- 라운드 진행: 75/100

### 5-A. 파일 구조 요약
- `modules/core/genre_guards/hunter_guard.py:15` `class HunterGuard(BaseGuard)` — 헌터 장르 Guard.
- `modules/core/genre_guards/hunter_guard.py:18` `def __init__(self) -> None` — 장르 용어/랭크/던전/각성 규칙 초기화.
- `modules/core/genre_guards/hunter_guard.py:227` `def get_impossible_actions(self, current_state: dict[str, Any]) -> list[dict[str, str]]` — 상태 기반 금지 행동 구성.
- `modules/core/genre_guards/hunter_guard.py:577` `def validate_dungeon_entry(self, dungeon_grade: str, hunter_rank: str, party_size: int = 1) -> tuple[bool, str]` — 던전 입장 조건 검증.
- `modules/core/genre_guards/hunter_guard.py:643` `def _compare_ranks(self, rank1: str, rank2: str) -> int` — 랭크 비교 유틸.
- `modules/core/genre_guards/hunter_guard.py:729` `def validate_skill_usage(self, skill_name: str, skill_type: str, last_used_seconds_ago: float, custom_cooldown: int = None) -> tuple[bool, str]` — 쿨다운 검증.
- `modules/core/genre_guards/hunter_guard.py:815` `def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]` — base 검증 + 헌터 특화 검증.

### 5-D. 읽기 증명
1. 마지막 함수: `def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]` (`modules/core/genre_guards/hunter_guard.py:815`)
2. 특징 문자열: `result["feedback"] = f"[헌터 Guard] {len(result['violations'])}건: {result['summary']}"` (`modules/core/genre_guards/hunter_guard.py:862`)
3. import 목록:
- `import re` (`modules/core/genre_guards/hunter_guard.py:9`)
- `from typing import Any` (`modules/core/genre_guards/hunter_guard.py:10`)
- `from .base_guard import BaseGuard` (`modules/core/genre_guards/hunter_guard.py:12`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `except ValueError: return 0` (`modules/core/genre_guards/hunter_guard.py:656`)
- 호출자: `modules/core/genre_guards/hunter_guard.py:595` `validate_dungeon_entry()` 내 `_compare_ranks(...)`
- 상류/하류 컨텍스트:
- 상류: `r1`, `r2`를 `_rank_hierarchy`에서 index 탐색 (`modules/core/genre_guards/hunter_guard.py:651`~`modules/core/genre_guards/hunter_guard.py:655`)
- 하류: `if self._compare_ranks(hunter_rank, min_rank) < 0:` (`modules/core/genre_guards/hunter_guard.py:595`)
- 실패 시나리오: 미등록 랭크 문자열이 들어오면 비교 결과가 0(동급)으로 처리되어 최소 랭크 검증이 완화될 수 있다.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `dungeon_patterns = re.findall(r"(\\w+)\\s*(?:등급|랭크|급)\\s*던전", manuscript)` (`modules/core/genre_guards/hunter_guard.py:822`)
- 호출자: `modules/domain/agents/director_auditor.py:83` `self._d.guard.run_deep_validation(...)`
- 상류/하류 컨텍스트:
- 상류: 원고 문자열에서 던전 등급 추출 (`modules/core/genre_guards/hunter_guard.py:822`)
- 하류: 추출 결과를 `validate_dungeon_entry()`로 전달 (`modules/core/genre_guards/hunter_guard.py:825`)
- 실패 시나리오: "블랙 게이트"처럼 공백/복합 표현은 패턴에 포착되지 않아 특수 던전 검사가 누락될 수 있다.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `if skill_mentions and not (current_state or {}).get("realm"):` (`modules/core/genre_guards/hunter_guard.py:850`)
- 호출자: `modules/core/genre_guards/hunter_guard.py:815` `run_deep_validation(...)`
- 상류/하류 컨텍스트:
- 상류: 같은 클래스의 다른 경로는 `rank`를 우선 참조 (`modules/core/genre_guards/hunter_guard.py:246`)
- 하류: 조건 참이면 `skill_without_awakening` MEDIUM violation 추가 (`modules/core/genre_guards/hunter_guard.py:851`~`modules/core/genre_guards/hunter_guard.py:856`)
- 실패 시나리오: 상태가 `rank`만 보유하고 `realm`이 비어있는 경우, 실제 각성 상태와 무관하게 경고가 생성될 수 있다.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [MEDIUM] modules/core/genre_guards/hunter_guard.py:744 — `custom_cooldown=0`이 기본 쿨다운으로 덮여 잘못된 사용 불가 판정

**문제**: `custom_cooldown`을 truthy 조건으로 분기해 `0`을 유효 커스텀 값으로 처리하지 못한다.

**문제 코드**:
```python
cooldown = custom_cooldown if custom_cooldown else self.get_skill_cooldown(skill_type)
```

**재현 경로**:
- `validate_skill_usage("평타", "기본 공격", last_used_seconds_ago=0.2, custom_cooldown=0)` 호출 시,
- 기대: `cooldown=0` 적용으로 사용 가능.
- 실제: 기본 쿨다운(`get_skill_cooldown`)이 적용되어 사용 불가 반환 가능.

**호출 체인**: `modules/core/genre_guards/hunter_guard.py:729` `validate_skill_usage()` 내부 분기 (`modules/core/genre_guards/hunter_guard.py:744`)

**수정 제안**:
```python
cooldown = custom_cooldown if custom_cooldown is not None else self.get_skill_cooldown(skill_type)
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 75 완료

## Round 76 — modules/core/genre_guards/investment_guard.py + fantasy_guard.py

### 진행 통계 업데이트
- 총 발견: 59건 (CRITICAL: 0, HIGH: 52, MEDIUM: 7)
- 라운드 진행: 76/100

### 5-A. 파일 구조 요약
- `modules/core/genre_guards/investment_guard.py:12` `class InvestmentGuard(BaseGuard)` — 투자 장르 Guard.
- `modules/core/genre_guards/investment_guard.py:218` `def get_impossible_actions(self, current_state: dict[str, Any]) -> list[dict[str, str]]` — 상태/자산 기반 금지 행동 구성.
- `modules/core/genre_guards/investment_guard.py:477` `def validate_investment_scale(self, investment_type: str, amount: float, current_wealth: float) -> tuple[bool, str]` — 투자 규모 적정성 검증.
- `modules/core/genre_guards/investment_guard.py:504` `def validate_return_rate(self, investment_type: str, return_rate: float, period_years: float = 1) -> tuple[bool, str]` — 수익률 현실성 검증.
- `modules/core/genre_guards/investment_guard.py:598` `def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]` — base 검증 + 투자 특화 검증.
- `modules/core/genre_guards/fantasy_guard.py:14` `class FantasyGuard(BaseGuard)` — 판타지 장르 Guard.
- `modules/core/genre_guards/fantasy_guard.py:180` `def get_impossible_actions(self, current_state: dict[str, Any]) -> list[dict[str, str]]` — 마나/티어 기반 금지 행동 구성.
- `modules/core/genre_guards/fantasy_guard.py:276` `def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]` — base 검증 + 판타지 특화 검증.
- `modules/core/genre_guards/fantasy_guard.py:318` `def validate_v20_manuscript(self, content) -> dict` — 판타지 순수성 검사.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]` (`modules/core/genre_guards/investment_guard.py:598`)
- `def validate_v20_manuscript(self, content) -> dict` (`modules/core/genre_guards/fantasy_guard.py:318`)
2. 특징 문자열:
- `result["feedback"] = f"[투자 Guard] {len(result['violations'])}건: {result['summary']}"` (`modules/core/genre_guards/investment_guard.py:635`)
- `result["feedback"] = f"[판타지 Guard] {len(result['violations'])}건: {result['summary']}"` (`modules/core/genre_guards/fantasy_guard.py:311`)
3. import 목록:
- `from typing import Any` (`modules/core/genre_guards/investment_guard.py:8`)
- `from typing import Any` (`modules/core/genre_guards/fantasy_guard.py:9`)
- `import re` (`modules/core/genre_guards/fantasy_guard.py:8`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `mana = float(re.search(r"(\\d+)", str(mana)).group(1))` (`modules/core/genre_guards/fantasy_guard.py:190`)
- 호출자: `modules/core/genre_guards/base_guard.py:316` `check_state_action_consistency()` → `get_impossible_actions(current_state)`
- 상류/하류 컨텍스트:
- 상류: 문자열 마나 입력(`"12.5"`, `"MP: 9.7"` 등) 처리 분기 (`modules/core/genre_guards/fantasy_guard.py:185`~`modules/core/genre_guards/fantasy_guard.py:191`)
- 하류: 마나 기반 금지 행동 생성 (`modules/core/genre_guards/fantasy_guard.py:202`~`modules/core/genre_guards/fantasy_guard.py:221`)
- 실패 시나리오: 소수/복합 문자열이 정수부로 절삭되어 실제보다 낮은 마나로 판정될 수 있다.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `if spell in manuscript:` (`modules/core/genre_guards/fantasy_guard.py:299`)
- 호출자: `modules/domain/agents/director_auditor.py:83` `self._d.guard.run_deep_validation(manuscript, current_state)`
- 상류/하류 컨텍스트:
- 상류: 저티어 마법사 구간 분기 (`modules/core/genre_guards/fantasy_guard.py:296`)
- 하류: `spell_tier_violation` HIGH 추가 (`modules/core/genre_guards/fantasy_guard.py:300`~`modules/core/genre_guards/fantasy_guard.py:305`)
- 실패 시나리오: 단어 경계 없는 포함 검사라 주문명이 비유/합성어 일부로 등장해도 위반으로 집계될 수 있다.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문:
- `if regression_date and event_date < regression_date:` (`modules/core/genre_guards/investment_guard.py:550`)
- `elif current_date and event_date > current_date:` (`modules/core/genre_guards/investment_guard.py:552`)
- 호출자: 현재 파일 내 직접 호출 없음(헬퍼 공개 API).
- 상류/하류 컨텍스트:
- 상류: `validate_timeline_event()` 입력은 문자열 날짜 (`modules/core/genre_guards/investment_guard.py:534`)
- 하류: 문자열 비교 결과로 허용/차단 반환 (`modules/core/genre_guards/investment_guard.py:551`~`modules/core/genre_guards/investment_guard.py:553`)
- 실패 시나리오: `YYYY-M-D`처럼 zero-padding 없는 날짜가 들어오면 사전식 비교 오판 가능.
- 판정: RISK (Design Check Needed).

4. 위험 지점
- 코드 원문:
- `valid, msg = self.validate_investment_scale("stock", amount, _wealth)` (`modules/core/genre_guards/investment_guard.py:614`)
- `valid, msg = self.validate_return_rate("stock", roi, 1.0)` (`modules/core/genre_guards/investment_guard.py:626`)
- 호출자: `modules/domain/agents/director_auditor.py:83` `self._d.guard.run_deep_validation(...)`
- 상류/하류 컨텍스트:
- 상류: 기준 테이블 키는 한국어 도메인 타입 (`modules/core/genre_guards/investment_guard.py:144`, `modules/core/genre_guards/investment_guard.py:158`)
- 하류: min 금액/수익률 범위 검증 (`modules/core/genre_guards/investment_guard.py:490`, `modules/core/genre_guards/investment_guard.py:518`)
- 실패 시나리오: `"stock"` 키가 테이블과 불일치해 scale/ROI 검증이 기본 경로로 빠져 사실상 비활성화된다.
- 판정: BUG.

### 5-C. 발견된 버그
### [HIGH] modules/core/genre_guards/investment_guard.py:614 — 투자 타입 키 불일치로 규모/수익률 검증이 사실상 무력화

**문제**: `run_deep_validation()`이 내부 검증 함수에 `"stock"`을 하드코딩 전달하지만, 룩업 테이블은 한국어 키(`"개인 주식"` 등)를 사용한다.

**문제 코드**:
```python
valid, msg = self.validate_investment_scale("stock", amount, _wealth)
...
valid, msg = self.validate_return_rate("stock", roi, 1.0)
```

**계약 위반 근거**:
- 규모 검증은 `self._investment_requirements.get(investment_type, 0)` (`modules/core/genre_guards/investment_guard.py:490`)
- 수익률 검증은 `self._realistic_returns.get(investment_type)` (`modules/core/genre_guards/investment_guard.py:518`)
- `"stock"`은 해당 테이블 키셋에 없어 기본값/None 경로로 빠진다 (`modules/core/genre_guards/investment_guard.py:144`, `modules/core/genre_guards/investment_guard.py:158`).

**재현 경로**:
- 원고에 `1만 원`, `5000%` 같은 값이 포함되면 regex로 캡처됨 (`modules/core/genre_guards/investment_guard.py:605`, `modules/core/genre_guards/investment_guard.py:621`).
- 이후 검증 호출이 `"stock"`으로 들어가 실질 임계치 검증이 건너뛰어진다.

**호출 체인**: `modules/domain/agents/director_auditor.py:83` → `modules/core/genre_guards/investment_guard.py:598` → `modules/core/genre_guards/investment_guard.py:614` / `modules/core/genre_guards/investment_guard.py:626`

**수정 제안**:
```python
# 예: 내부 표준 키로 통일
investment_key = "개인 주식"
valid, msg = self.validate_investment_scale(investment_key, amount, _wealth)
...
valid, msg = self.validate_return_rate(investment_key, roi, 1.0)
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 76 완료

## Round 77 — modules/core/genre_guards/cooking_guard.py + composer_guard.py

### 진행 통계 업데이트
- 총 발견: 60건 (CRITICAL: 0, HIGH: 52, MEDIUM: 8)
- 라운드 진행: 77/100

### 5-A. 파일 구조 요약
- `modules/core/genre_guards/cooking_guard.py:12` `class CookingGuard(BaseGuard)` — 요리 장르 Guard.
- `modules/core/genre_guards/cooking_guard.py:220` `def get_impossible_actions(self, current_state: dict[str, Any]) -> list[dict[str, str]]` — 상태/셰프등급 기반 금지 행동 구성.
- `modules/core/genre_guards/cooking_guard.py:305` `def get_hierarchy_rules(self) -> dict[str, Any]` — 셰프/레스토랑 위계 규칙.
- `modules/core/genre_guards/cooking_guard.py:452` `def get_cooking_rules_prompt(self) -> str` — 요리 규칙 프롬프트.
- `modules/core/genre_guards/cooking_guard.py:490` `def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]` — base 검증 래퍼.
- `modules/core/genre_guards/composer_guard.py:12` `class ComposerGuard(BaseGuard)` — 작곡가 장르 Guard.
- `modules/core/genre_guards/composer_guard.py:232` `def get_impossible_actions(self, current_state: dict[str, Any]) -> list[dict[str, str]]` — 상태/명성 기반 금지 행동 구성.
- `modules/core/genre_guards/composer_guard.py:281` `def _get_fame_class(self, fame) -> str` — 명성 구간 분류.
- `modules/core/genre_guards/composer_guard.py:472` `def get_music_rules_prompt(self) -> str` — 음악 규칙 프롬프트.
- `modules/core/genre_guards/composer_guard.py:507` `def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]` — base 검증 래퍼.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]` (`modules/core/genre_guards/cooking_guard.py:490`)
- `def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]` (`modules/core/genre_guards/composer_guard.py:507`)
2. 특징 문자열:
- `result["feedback"] = f"[요리물 Guard] {len(result['violations'])}건: {result['summary']}"` (`modules/core/genre_guards/cooking_guard.py:499`)
- `result["feedback"] = f"[작곡가물 Guard] {len(result['violations'])}건: {result['summary']}"` (`modules/core/genre_guards/composer_guard.py:516`)
3. import 목록:
- `from typing import Any` (`modules/core/genre_guards/cooking_guard.py:8`)
- `from typing import Any` (`modules/core/genre_guards/composer_guard.py:8`)
- `from .base_guard import BaseGuard` (`modules/core/genre_guards/cooking_guard.py:10`, `modules/core/genre_guards/composer_guard.py:10`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문:
- `capital = current_state.get("capital", "0원")` (`modules/core/genre_guards/cooking_guard.py:245`)
- `if isinstance(capital, str) and ("0원" in capital or "마이너스" in capital or "적자" in capital):` (`modules/core/genre_guards/cooking_guard.py:246`)
- 호출자: `modules/core/genre_guards/base_guard.py:316` `check_state_action_consistency()` → `get_impossible_actions(current_state)`
- 상류/하류 컨텍스트:
- 상류: 자금 상태는 genre HUD에서 `capital`/`cash` 등으로 유입 (`modules/core/genre_hud_manager.py:168`, `modules/core/genre_hud_manager.py:282`)
- 하류: 조건 만족 시 CRITICAL 패턴 추가 (`modules/core/genre_guards/cooking_guard.py:247`~`modules/core/genre_guards/cooking_guard.py:252`)
- 실패 시나리오: `capital=-1000` 같은 숫자형 입력은 문자열 분기에서 제외되어 자금난 제한이 누락된다.
- 판정: BUG.

2. 위험 지점
- 코드 원문:
- `self._restaurant_requirements = { ... }` (`modules/core/genre_guards/cooking_guard.py:165`)
- `self._competition_requirements = { ... }` (`modules/core/genre_guards/cooking_guard.py:174`)
- 호출자: 현재 파일 내 직접 참조 없음.
- 상류/하류 컨텍스트:
- 상류: 상세 요구조건 테이블이 초기화됨
- 하류: `run_deep_validation()`은 `super()` 결과만 후처리 (`modules/core/genre_guards/cooking_guard.py:490`~`modules/core/genre_guards/cooking_guard.py:500`)
- 실패 시나리오: 레스토랑/대회 진입 요건이 선언만 되고 실제 판정에 반영되지 않아 정책-실행 괴리가 생길 수 있다.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문:
- `self._activity_requirements = { ... }` (`modules/core/genre_guards/composer_guard.py:175`)
- `self._realistic_chart = { ... }` (`modules/core/genre_guards/composer_guard.py:185`)
- 호출자: 현재 파일 내 직접 참조 없음.
- 상류/하류 컨텍스트:
- 상류: 활동 진입/차트 현실성 데이터가 초기화됨
- 하류: `run_deep_validation()`은 별도 차트/활동 검증 없이 base 결과만 정리 (`modules/core/genre_guards/composer_guard.py:507`~`modules/core/genre_guards/composer_guard.py:517`)
- 실패 시나리오: 명시한 산업 현실성 룰이 실제 위반 탐지에 사용되지 않아 허용 범위가 의도보다 넓어질 수 있다.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [MEDIUM] modules/core/genre_guards/cooking_guard.py:246 — `capital` 숫자형 입력 시 자금난 CRITICAL 제한이 누락

**문제**: 자금난 판정이 문자열(`"0원"`, `"마이너스"`, `"적자"`)에만 걸려 숫자형 자본(0 이하)을 처리하지 못한다.

**문제 코드**:
```python
capital = current_state.get("capital", "0원")
if isinstance(capital, str) and ("0원" in capital or "마이너스" in capital or "적자" in capital):
    actions.append({... "severity": "CRITICAL"})
```

**재현 근거**:
- `CookingGuard().get_impossible_actions({'capital': -1000, 'chef_rank': '', 'status': ''})` 결과: `[]`
- `CookingGuard().get_impossible_actions({'capital': '\\uc801\\uc790', 'chef_rank': '', 'status': ''})` 결과: CRITICAL 항목 1건

**호출 체인**: `modules/core/genre_guards/base_guard.py:316` → `modules/core/genre_guards/cooking_guard.py:220` → `modules/core/genre_guards/cooking_guard.py:246`

**수정 제안**:
```python
capital = current_state.get("capital", "0원")
is_negative_numeric = isinstance(capital, (int, float)) and capital <= 0
is_negative_text = isinstance(capital, str) and ("0원" in capital or "마이너스" in capital or "적자" in capital)
if is_negative_numeric or is_negative_text:
    actions.append({...})
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 77 완료

## Round 78 — modules/core/genre_guards/alt_history_guard.py + medical_guard.py + sports_guard.py + actor_guard.py

### 진행 통계 업데이트
- 총 발견: 61건 (CRITICAL: 0, HIGH: 53, MEDIUM: 8)
- 라운드 진행: 78/100

### 5-A. 파일 구조 요약
- `modules/core/genre_guards/alt_history_guard.py:12` `class AltHistoryGuard(BaseGuard)` — 대체역사 장르 Guard.
- `modules/core/genre_guards/alt_history_guard.py:252` `def get_impossible_actions(self, current_state: dict[str, Any]) -> list[dict[str, str]]` — 신분/관직/상태 기반 금지 행동 구성.
- `modules/core/genre_guards/alt_history_guard.py:481` `def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]` — base 검증 래퍼.
- `modules/core/genre_guards/medical_guard.py:12` `class MedicalGuard(BaseGuard)` — 의학 장르 Guard.
- `modules/core/genre_guards/medical_guard.py:214` `def get_impossible_actions(self, current_state: dict[str, Any]) -> list[dict[str, str]]` — 직급/의료사고/상태 기반 금지 행동 구성.
- `modules/core/genre_guards/medical_guard.py:458` `def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]` — base 검증 래퍼.
- `modules/core/genre_guards/sports_guard.py:12` `class SportsGuard(BaseGuard)` — 스포츠 장르 Guard.
- `modules/core/genre_guards/sports_guard.py:211` `def get_impossible_actions(self, current_state: dict[str, Any]) -> list[dict[str, str]]` — 선수등급/부상 기반 금지 행동 구성.
- `modules/core/genre_guards/sports_guard.py:451` `def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]` — base 검증 래퍼.
- `modules/core/genre_guards/actor_guard.py:12` `class ActorGuard(BaseGuard)` — 배우 장르 Guard.
- `modules/core/genre_guards/actor_guard.py:218` `def get_impossible_actions(self, current_state: dict[str, Any]) -> list[dict[str, str]]` — 인지도/스캔들 기반 금지 행동 구성.
- `modules/core/genre_guards/actor_guard.py:447` `def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]` — base 검증 래퍼.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]` (`modules/core/genre_guards/alt_history_guard.py:481`)
- `def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]` (`modules/core/genre_guards/medical_guard.py:458`)
- `def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]` (`modules/core/genre_guards/sports_guard.py:451`)
- `def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]` (`modules/core/genre_guards/actor_guard.py:447`)
2. 특징 문자열:
- `result["feedback"] = f"[대체역사물 Guard] {len(result['violations'])}건: {result['summary']}"` (`modules/core/genre_guards/alt_history_guard.py:490`)
- `result["feedback"] = f"[의학물 Guard] {len(result['violations'])}건: {result['summary']}"` (`modules/core/genre_guards/medical_guard.py:467`)
- `result["feedback"] = f"[스포츠물 Guard] {len(result['violations'])}건: {result['summary']}"` (`modules/core/genre_guards/sports_guard.py:460`)
- `result["feedback"] = f"[배우물 Guard] {len(result['violations'])}건: {result['summary']}"` (`modules/core/genre_guards/actor_guard.py:456`)
3. import 목록:
- `from typing import Any` (`modules/core/genre_guards/alt_history_guard.py:8`)
- `from typing import Any` (`modules/core/genre_guards/medical_guard.py:8`)
- `from typing import Any` (`modules/core/genre_guards/sports_guard.py:8`)
- `from typing import Any` (`modules/core/genre_guards/actor_guard.py:8`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문:
- `scandal_idx = current_state.get("scandal_index", 0)` (`modules/core/genre_guards/actor_guard.py:240`)
- `if isinstance(scandal_idx, int | float) and scandal_idx >= 80:` (`modules/core/genre_guards/actor_guard.py:241`)
- 호출자: `modules/core/genre_guards/base_guard.py:316` `check_state_action_consistency()` → `get_impossible_actions(current_state)`
- 상류/하류 컨텍스트:
- 상류: actor HUD 기본값/출력은 문자열 경로가 존재 (`modules/core/genre_hud_manager.py:437`)
- 하류: 조건 만족 시 CRITICAL 광고/공식행사 제한 추가 (`modules/core/genre_guards/actor_guard.py:242`~`modules/core/genre_guards/actor_guard.py:248`)
- 실패 시나리오: `scandal_index="90"`(문자열) 입력은 분기에서 제외되어 핵심 CRITICAL 제한이 누락된다.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `if isinstance(injury, str) and any(kw in injury for kw in ["중상", "수술", "인대", "골절"]):` (`modules/core/genre_guards/sports_guard.py:234`)
- 호출자: `modules/core/genre_guards/base_guard.py:316` `check_state_action_consistency()` → `get_impossible_actions(current_state)`
- 상류/하류 컨텍스트:
- 상류: `injury = current_state.get("injuries", current_state.get("injury_history", ""))` (`modules/core/genre_guards/sports_guard.py:233`)
- 하류: 중증 부상 CRITICAL 패턴 추가 (`modules/core/genre_guards/sports_guard.py:235`~`modules/core/genre_guards/sports_guard.py:241`)
- 실패 시나리오: 부상 이력이 list/dict로 들어오는 경우 중증 키워드가 있어도 탐지가 비활성화된다.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문:
- `malpractice = current_state.get("malpractice_record", [])` (`modules/core/genre_guards/medical_guard.py:236`)
- `recent = malpractice[-1] if malpractice else {}` (`modules/core/genre_guards/medical_guard.py:238`)
- `if isinstance(recent, dict) and not recent.get("resolved", False):` (`modules/core/genre_guards/medical_guard.py:239`)
- 호출자: `modules/core/genre_guards/base_guard.py:316` `check_state_action_consistency()` → `get_impossible_actions(current_state)`
- 상류/하류 컨텍스트:
- 상류: 의료사고 이력 전체를 받음
- 하류: 마지막 항목만 검사해 CRITICAL 패턴 추가 여부 결정 (`modules/core/genre_guards/medical_guard.py:240`~`modules/core/genre_guards/medical_guard.py:246`)
- 실패 시나리오: 최신 항목이 해결 상태면, 그 이전 미해결/중대 이력이 있어도 제약이 빠질 수 있다.
- 판정: RISK (Design Check Needed).

4. 위험 지점
- 코드 원문: `if class_name in social_class:` (`modules/core/genre_guards/alt_history_guard.py:270`)
- 호출자: `modules/core/genre_guards/base_guard.py:316` `check_state_action_consistency()` → `get_impossible_actions(current_state)`
- 상류/하류 컨텍스트:
- 상류: `social_class = current_state.get("social_class", "양반")` (`modules/core/genre_guards/alt_history_guard.py:267`)
- 하류: 계층 제한 패턴 누적 (`modules/core/genre_guards/alt_history_guard.py:271`~`modules/core/genre_guards/alt_history_guard.py:274`)
- 실패 시나리오: 부분 포함 매칭이라 복합 문자열/비표준 표기에서 의도치 않은 클래스 규칙이 적용될 수 있다.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/core/genre_guards/actor_guard.py:241 — 문자열 `scandal_index` 입력 시 CRITICAL 제약 우회

**문제**: 스캔들 지수 분기가 숫자 타입만 허용해, `"90"` 같은 문자열 지수가 들어오면 고위험 제한이 누락된다.

**문제 코드**:
```python
scandal_idx = current_state.get("scandal_index", 0)
if isinstance(scandal_idx, int | float) and scandal_idx >= 80:
    actions.append({... "severity": "CRITICAL"})
```

**재현 근거**:
- `ActorGuard().get_impossible_actions({'scandal_index': 90, ...})` → CRITICAL 1건 생성
- `ActorGuard().get_impossible_actions({'scandal_index': '90', ...})` → 동일 제약 미생성

**계약 위반 근거**:
- actor HUD는 문자열 기본값 경로를 사용한다 (`modules/core/genre_hud_manager.py:437`).
- Guard가 문자열 수치 입력을 정규화하지 않아 동등한 의미 값에서 판정이 달라진다.

**호출 체인**: `modules/core/genre_guards/base_guard.py:316` → `modules/core/genre_guards/actor_guard.py:218` → `modules/core/genre_guards/actor_guard.py:241`

**수정 제안**:
```python
scandal_idx = current_state.get("scandal_index", 0)
if isinstance(scandal_idx, str):
    try:
        scandal_idx = float(scandal_idx)
    except ValueError:
        scandal_idx = 0
if isinstance(scandal_idx, (int, float)) and scandal_idx >= 80:
    ...
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 78 완료

## Round 79 — modules/core/genre_guards/work_guard.py + style_guard.py + __init__.py

### 진행 통계 업데이트
- 총 발견: 63건 (CRITICAL: 0, HIGH: 55, MEDIUM: 8)
- 라운드 진행: 79/100

### 5-A. 파일 구조 요약
- `modules/core/genre_guards/work_guard.py:22` `class WorkGuard(BaseGuard)` — 작품별 YAML 규칙을 장르 Guard 위에 합성하는 래퍼.
- `modules/core/genre_guards/work_guard.py:61` `def _load_yaml(yaml_path: Path | str) -> dict` — `work_guard.yaml` 로드.
- `modules/core/genre_guards/work_guard.py:125` `def get_v20_purism_prompt(self) -> str` — base 프롬프트에 작품 규칙/캐릭터 제약 병합.
- `modules/core/genre_guards/work_guard.py:149` `def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]` — base 검증 결과에 작품 전용 금칙/패턴 위반 추가.
- `modules/core/genre_guards/style_guard.py:22` `class StyleGuard(BaseGuard)` — StyleGuide 기반 추가 검증 래퍼.
- `modules/core/genre_guards/style_guard.py:25` `def __init__(self, base_guard: BaseGuard, style_guide) -> None` — anti-AI/금지표현/문장길이 규칙 캐시.
- `modules/core/genre_guards/style_guard.py:99` `def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]` — base 검증 + 문체 위반 추가.
- `modules/core/genre_guards/style_guard.py:148` `def _check_sentence_length_distribution(self, manuscript: str) -> str` — 문장 길이 분포 편차 경고 생성.
- `modules/core/genre_guards/__init__.py:20` `def create_genre_guard(genre_type)` — 장르별 Guard 팩토리.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]` (`modules/core/genre_guards/work_guard.py:149`)
- `def _check_sentence_length_distribution(self, manuscript: str) -> str` (`modules/core/genre_guards/style_guard.py:148`)
- `def create_genre_guard(genre_type)` (`modules/core/genre_guards/__init__.py:20`)
2. 특징 문자열:
- `_logger.warning("[WorkGuard] 잘못된 정규식: %s", pattern)` (`modules/core/genre_guards/work_guard.py:183`)
- `return f"[Style] 문장 평균 길이({avg_len:.0f}자)가 목표({self._target_sentence_length})보다 지나치게 긺"` (`modules/core/genre_guards/style_guard.py:165`)
- `# 기본값: 무협` (`modules/core/genre_guards/__init__.py:52`)
3. import 목록:
- `from .base_guard import BaseGuard` (`modules/core/genre_guards/work_guard.py:17`)
- `from .base_guard import BaseGuard` (`modules/core/genre_guards/style_guard.py:15`)
- `from .wuxia_guard import WuxiaGuard` (`modules/core/genre_guards/__init__.py:17`)
- `from .work_guard import WorkGuard` (`modules/core/genre_guards/__init__.py:16`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문:
- `self._config = self._load_yaml(yaml_path)` (`modules/core/genre_guards/work_guard.py:28`)
- `extra_forbidden = set(self._config.get("extra_forbidden_terms", []))` (`modules/core/genre_guards/work_guard.py:32`)
- `return yaml.safe_load(f) or {}` (`modules/core/genre_guards/work_guard.py:67`)
- 호출자: `main_a.py:923`에서 `work_guard.yaml` 존재 시 `WorkGuard(self.sys.guard, work_guard_path)` 실행.
- 상류/하류 컨텍스트:
- 상류: `work_guard.yaml`이 존재하면 형식 검증 없이 즉시 로드 (`main_a.py:919`~`main_a.py:923`).
- 하류: `_load_yaml()`이 dict 이외(list/scalar)를 반환하면 `.get()`에서 즉시 크래시.
- 재현 근거:
- 임시 YAML 루트가 리스트(`- a\n- b`)일 때 `WorkGuard(...)` 실행 결과: `AttributeError: 'list' object has no attribute 'get'`.
- 판정: BUG.

2. 위험 지점
- 코드 원문:
- `extra_forbidden = set(self._config.get("extra_forbidden_terms", []))` (`modules/core/genre_guards/work_guard.py:32`)
- `extra_allowed = set(self._config.get("extra_allowed_terms", []))` (`modules/core/genre_guards/work_guard.py:33`)
- 호출자: `main_a.py:923` `WorkGuard(...)` 초기화 경로.
- 상류/하류 컨텍스트:
- 상류: YAML 필드 요소 타입(문자열/숫자/dict) 검증 없음.
- 하류: dict 요소가 섞이면 `set([...])`에서 `TypeError` 발생 후 앱 기동 실패.
- 재현 근거:
- 임시 YAML `extra_forbidden_terms: [ {k: v} ]`로 `WorkGuard(...)` 실행 결과: `TypeError: unhashable type: 'dict'`.
- 판정: BUG.

3. 위험 지점
- 코드 원문:
- `_guard = self.sys.guard` (`main_a.py:1429`)
- `_guard = StyleGuard(_guard, _sg)` (`main_a.py:1438`)
- `self.agents["writer"].set_guard(self.sys.guard)` (`main_a.py:1451`)
- 호출자: `_attach_agents()` 에이전트 초기화 루틴 (`main_a.py:1415` 이후).
- 상류/하류 컨텍스트:
- 상류: Director는 StyleGuard 래핑된 `_guard`를 주입받음.
- 하류: Writer는 래핑 전 `self.sys.guard`를 그대로 받아, 동일 원고에 대해 Director/Writer Guard 판단 축이 달라질 수 있음.
- 실패 시나리오: 문체 제약 위반 문장이 Writer 단계에서 통과하고 Director 단계에서만 차단되어 재시도 비용 증가/행동 비일관성이 발생.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/core/genre_guards/work_guard.py:32 — YAML 루트 타입 미검증으로 `AttributeError` 기동 크래시

**문제**: `_load_yaml()`이 dict 외 타입을 반환해도 타입 정규화를 하지 않아, 곧바로 `.get()` 호출에서 크래시한다.

**문제 코드**:
```python
self._config = self._load_yaml(yaml_path)
...
extra_forbidden = set(self._config.get("extra_forbidden_terms", []))

@staticmethod
def _load_yaml(yaml_path: Path | str) -> dict:
    ...
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
```

**재현 근거**:
- 입력 YAML: 루트가 리스트(`- a\n- b`).
- 실행: `WorkGuard(WuxiaGuard(), yaml_path)`.
- 결과: `AttributeError: 'list' object has no attribute 'get'`.

**호출 체인**: `main_a.py:919` → `main_a.py:923` → `modules/core/genre_guards/work_guard.py:28` → `modules/core/genre_guards/work_guard.py:32`

**수정 제안**:
```python
loaded = yaml.safe_load(f)
return loaded if isinstance(loaded, dict) else {}
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [HIGH] modules/core/genre_guards/work_guard.py:32 — YAML 항목 타입 미검증으로 `TypeError(unhashable dict)` 크래시

**문제**: `extra_forbidden_terms`/`extra_allowed_terms` 요소를 그대로 `set()`에 넣어 dict 항목이 섞이면 크래시한다.

**문제 코드**:
```python
extra_forbidden = set(self._config.get("extra_forbidden_terms", []))
extra_allowed = set(self._config.get("extra_allowed_terms", []))
```

**재현 근거**:
- 입력 YAML: `extra_forbidden_terms: [ {k: v} ]`.
- 실행: `WorkGuard(WuxiaGuard(), yaml_path)`.
- 결과: `TypeError: unhashable type: 'dict'`.

**호출 체인**: `main_a.py:923` → `modules/core/genre_guards/work_guard.py:32`

**수정 제안**:
```python
raw_forbidden = self._config.get("extra_forbidden_terms", [])
extra_forbidden = {t for t in raw_forbidden if isinstance(t, str)}
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 79 완료

## Round 80 — main_a.py L1~750

### 진행 통계 업데이트
- 총 발견: 65건 (CRITICAL: 0, HIGH: 56, MEDIUM: 9)
- 라운드 진행: 80/100

### 5-A. 파일 구조 요약
- `main_a.py:167` `class SovereignApp` — 앱 엔트리/오케스트레이션 컨테이너.
- `main_a.py:170` `def __init__(self)` — 서비스/오케스트레이터/에이전트 의존성 초기화.
- `main_a.py:279` `def _safe_commit(self) -> bool` — DB commit/rollback 래퍼.
- `main_a.py:320` `def _enrich_director_result(self, audit_result: dict, stage: int, content_length: int = 0) -> dict` — Director 결과 보강(action_items/책임/정량 피드백).
- `main_a.py:463` `def _analyze_score_breakdown(self, breakdown: dict) -> dict` — 영역별 점수 구간을 심각도로 매핑.
- `main_a.py:572` `def _get_dynamic_critical_keywords(self) -> list` — 실패 이력 기반 동적 키워드 추출.
- `main_a.py:657` `def _analyze_rejection_pattern_v60(self, rejection_history: list, current_arc_no: int) -> str` — REJECT 사유 집계/가이드 생성.
- `main_a.py:719` `def _normalize_rejection_reason(self, reason: str) -> str` — REJECT 사유 정규화.
- `main_a.py:744` `def _get_rejection_fix_guide(self, normalized_reason: str) -> str` — 사유별 수정 가이드 반환.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def _get_rejection_fix_guide(self, normalized_reason: str) -> str` (`main_a.py:744`)
2. 특징 문자열:
- `print("[V61.3] Faulthandler 활성화 → crash_dump.log", file=sys.stderr)` (`main_a.py:11`)
- `f"🔍 [V60.10] Arc {current_arc_no} REJECT 패턴 분석"` (`main_a.py:695`)
- `return "기타"` (`main_a.py:742`)
3. import 목록:
- `from modules.core.stage2_orchestrator import Stage2Orchestrator` (`main_a.py:51`)
- `from modules.core.stage4_orchestrator import Stage4Orchestrator` (`main_a.py:53`)
- `from modules.core.prompt_builder import PromptBuilder` (`main_a.py:45`)
- `from modules.domain.agents.director import Director` (`main_a.py:67`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문:
- `score = breakdown.get(area, config["max"])` (`main_a.py:529`)
- `if score <= config["thresholds"]["critical"]:` (`main_a.py:532`)
- 호출자: `_enrich_director_result()` 내부에서 `score_breakdown` 존재 시 호출 (`main_a.py:421`~`main_a.py:423`).
- 상류/하류 컨텍스트:
- 상류: `audit_result.get("score_breakdown", {})`를 타입 정규화 없이 전달 (`main_a.py:421`).
- 하류: 문자열 점수(`"15"`)면 `<=` 비교에서 `TypeError`로 분기 전체 중단.
- 재현 근거:
- `SovereignApp.__new__(SovereignApp)._analyze_score_breakdown({'setting_consistency': '15'})` 실행 시 `TypeError: '<=' not supported between instances of 'str' and 'int'`.
- 판정: BUG.

2. 위험 지점
- 코드 원문:
- `reason_lower = reason.lower()` (`main_a.py:721`)
- 호출자: `_analyze_rejection_pattern_v60()`에서 `normalized = self._normalize_rejection_reason(reason)` (`main_a.py:680`).
- 상류/하류 컨텍스트:
- 상류: `reason = reject.get("reason", "unknown")`는 키가 존재하지만 값이 `None`인 경우를 걸러내지 못함 (`main_a.py:678`).
- 하류: `None.lower()`로 즉시 `AttributeError`.
- 재현 근거:
- `SovereignApp.__new__(SovereignApp)._normalize_rejection_reason(None)` 실행 시 `AttributeError: 'NoneType' object has no attribute 'lower'`.
- 판정: BUG.

3. 위험 지점
- 코드 원문:
- `_fault_log = open("crash_dump.log", "w", encoding="utf-8")` (`main_a.py:8`)
- `faulthandler.enable(file=_fault_log, all_threads=True)` (`main_a.py:9`)
- 호출자: 모듈 import 시점(top-level 실행).
- 상류/하류 컨텍스트:
- 상류: 파일 오픈 예외(`PermissionError`, 경로/권한 이슈) 처리 없음.
- 하류: import 단계에서 예외가 나면 앱 자체가 초기화 전에 실패.
- 실패 시나리오: 읽기 전용 작업 디렉터리/권한 제한 환경에서 `main_a.py` import가 즉시 중단.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] main_a.py:532 — `score_breakdown` 문자열 점수 입력 시 비교 연산 TypeError

**문제**: 점수 타입을 정규화하지 않고 수치 비교를 수행해 문자열 점수에서 크래시한다.

**문제 코드**:
```python
score = breakdown.get(area, config["max"])  # 없으면 만점으로 간주

# 심각도 판단
if score <= config["thresholds"]["critical"]:
    severity = "CRITICAL"
```

**재현 근거**:
- 실행: `SovereignApp.__new__(SovereignApp)._analyze_score_breakdown({'setting_consistency': '15'})`
- 결과: `TypeError: '<=' not supported between instances of 'str' and 'int'`

**호출 체인**: `main_a.py:421` → `main_a.py:423` → `main_a.py:529` → `main_a.py:532`

**수정 제안**:
```python
raw_score = breakdown.get(area, config["max"])
try:
    score = int(raw_score)
except (TypeError, ValueError):
    score = config["max"]
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [MEDIUM] main_a.py:721 — `reason=None` 입력 시 REJECT 사유 정규화 크래시

**문제**: `_normalize_rejection_reason()`가 문자열 가정만 두고 `None`을 처리하지 않는다.

**문제 코드**:
```python
def _normalize_rejection_reason(self, reason: str) -> str:
    """REJECT 사유 정규화"""
    reason_lower = reason.lower()
```

**재현 근거**:
- 실행: `SovereignApp.__new__(SovereignApp)._normalize_rejection_reason(None)`
- 결과: `AttributeError: 'NoneType' object has no attribute 'lower'`

**호출 체인**: `main_a.py:678` → `main_a.py:680` → `main_a.py:721`

**수정 제안**:
```python
reason = reason or ""
reason_lower = reason.lower()
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 80 완료

## Round 81 — main_a.py L751~1500

### 진행 통계 업데이트
- 총 발견: 65건 (CRITICAL: 0, HIGH: 56, MEDIUM: 9)
- 라운드 진행: 81/100

### 5-A. 파일 구조 요약
- `main_a.py:759` `def _emergency_shutdown(self) -> None` — 긴급 종료 시 DB/메모리 자원 정리.
- `main_a.py:790` `def _init_diversity_engine(self, window_size: int = 10) -> bool` — NarrativeDiversityEngine 초기화/초기 분석.
- `main_a.py:842` `def boot(self)` — 프로젝트 선택, HUD/Guard/VecMemory/에이전트 기동.
- `main_a.py:952` `def _load_models_yaml(self) -> dict` — 프로젝트 우선 모델 설정 로드.
- `main_a.py:980` `def _ignite_quad_cache_system(self)` — Writer/Analyst/Weaver 캐시 생성 및 주입.
- `main_a.py:1126` `def _is_cache_alive(self, cache_name)` — 원격 캐시 생존 확인.
- `main_a.py:1136` `def _check_vector_db_lock(self, project_name: str) -> bool` — vec DB 파일 무결성(0KB) 체크.
- `main_a.py:1165` `def _enrich_treatment_blocks(self, treatment_file: str) -> str` — Treatment 블록 농축 파이프라인.
- `main_a.py:1309` `def _attach_agents(self) -> bool` — 에이전트 생성/연결 및 Director/Writer 설정 주입.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def _attach_agents(self) -> bool` (`main_a.py:1309`)
2. 특징 문자열:
- `self.ui.log("🧬 [System] V31 3중 캐싱 시스템(Triple-Cache) 동기화 중...")` (`main_a.py:984`)
- `self.ui.log("🔧 [V60.10] Treatment Block 농축 시작...")` (`main_a.py:1180`)
- `self.ui.log("   🎨 StyleGuard 래핑 완료 (문체 기반 검증 활성)")` (`main_a.py:1439`)
3. import 목록:
- `from modules.core.prompt_loader import PromptLoader` (`main_a.py:874`)
- `from modules.core.genre_guards.work_guard import WorkGuard` (`main_a.py:921`)
- `from modules.core.genre_guards import StyleGuard` (`main_a.py:1434`)
- `from modules.core.stage0 import StyleGuide` (`main_a.py:1435`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문:
- `validation_config = settings.get("validation", {})` (`main_a.py:1471`)
- `if validation_config.get("use_v0128", False):` (`main_a.py:1472`)
- 호출자: `boot()`에서 `if not self._attach_agents():` 경로로 진입 (`main_a.py:946`~`main_a.py:947`).
- 상류/하류 컨텍스트:
- 상류: `settings = json.load(f)` 이후 `dict` 타입 검증이 없음 (`main_a.py:1464`~`main_a.py:1465`).
- 하류: `settings.json` 루트가 list/string이면 `.get()`에서 `AttributeError` 발생 가능.
- 실패 시나리오: 사용자 설정 파일이 `{}`가 아닌 `[]` 또는 문자열로 저장된 경우 에이전트 초기화 단계에서 부팅 중단.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문:
- `for i, block in enumerate(enriched_blocks_raw):` (`main_a.py:1266`)
- `if block is None: enriched_blocks.append(treatment_blocks[i])` (`main_a.py:1267`~`main_a.py:1268`)
- `else: enriched_blocks.append(treatment_blocks[i])` (`main_a.py:1279`~`main_a.py:1280`)
- 호출자: 파일 내 직접 호출 미확인 (`_enrich_treatment_blocks` 호출 지점 미탐지), UI 경로에서 호출되는 유틸 함수로 보임.
- 상류/하류 컨텍스트:
- 상류: `enricher.enrich_all_blocks_parallel(...)` 반환 길이에 대한 불변식 검증 없음 (`main_a.py:1251`~`main_a.py:1261`).
- 하류: 반환 배열이 원본보다 길고 해당 요소가 `None`/비dict면 `treatment_blocks[i]`에서 `IndexError` 가능.
- 실패 시나리오: 병렬 농축 결과 길이 불일치 시 후처리 단계에서 즉시 예외로 농축 실패 fallback 발생.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문:
- `bible_path = Path("bible")` (`main_a.py:1232`)
- `bible_files = list(bible_path.glob("*.json"))` (`main_a.py:1233`)
- 호출자: 파일 내 직접 호출 미확인 (`_enrich_treatment_blocks` 내부 경로).
- 상류/하류 컨텍스트:
- 상류: 현재 프로젝트 컨텍스트(`self.current_project`)가 이미 존재함에도 전역 상대경로를 사용.
- 하류: 멀티 프로젝트/작업 디렉터리 변경 환경에서 타 프로젝트 Bible을 읽어 주인공명을 잘못 주입할 수 있음.
- 실패 시나리오: 다른 프로젝트의 `bible/*.json`이 먼저 매칭되면 농축 프롬프트 인물명이 현재 프로젝트와 불일치.
- 판정: RISK (Design Check Needed).

---
## Round 81 완료

## Round 82 — main_a.py L1501~2250

### 진행 통계 업데이트
- 총 발견: 66건 (CRITICAL: 0, HIGH: 56, MEDIUM: 10)
- 라운드 진행: 82/100

### 5-A. 파일 구조 요약
- `main_a.py:1743` `def _load_v50_history(self) -> None` — V50 계열 히스토리 로딩 훅(현재 no-op).
- `main_a.py:1758` `def _get_protagonist_name(self) -> str` — Bible/HUD 기반 주인공명 추출.
- `main_a.py:1788` `def _fix_entity_registry_protagonist(self, entity_registry: dict, protagonist_name: str = None) -> dict` — Entity Registry 주인공명 보정.
- `main_a.py:1819` `def _run_main_process(self) -> None` — 메인 메뉴 루프 및 Stage 디스패치.
- `main_a.py:1933` `def _shutdown_app(self)` — 종료 시 메트릭/비용/트래커/DB 정리.
- `main_a.py:2189` `def _stage_2_arcs(self)` — Stage2Context 주입 후 Stage2Orchestrator 실행.
- `main_a.py:2221` `def _normalize_tactical_text(self, text)` — Stage2Orchestrator 위임 스텁.
- `main_a.py:2233` `def _stage2_flow_guard(self, refined_arc)` — flow_guard 위임 스텁.
- `main_a.py:2241` `def _validate_volume_boundaries(self, vol_data, vol_idx)` — 권 경계 누수 검사.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def _validate_volume_boundaries(self, vol_data, vol_idx)` (`main_a.py:2241`)
2. 특징 문자열:
- `self.ui.log("📥 [Resume] 프로젝트: {self.current_project.name}")` (`main_a.py:2179`)
- `future.result(timeout=600)  # [Sweep3-G1] 10분 타임아웃 — 무한 블록 방지` (`main_a.py:2208`)
- `print("✅ [System] 종료 완료", flush=True)` (`main_a.py:2118`)
3. import 목록:
- `from modules.core.semantic_plot_guard import SemanticPlotGuard` (`main_a.py:1551`)
- `from modules.core.stage2_context import Stage2Context` (`main_a.py:2194`)
- `from modules.core.metrics_collector import get_metrics_collector` (`main_a.py:42`)
- `from modules.core.quality_dashboard import QualityDashboard` (`main_a.py:124`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문:
- `total_eps = sum(a.get("ep_count", 0) for a in arcs if isinstance(a, dict)) if isinstance(arcs, list) else 0` (`main_a.py:2176`)
- 호출자: `_stage_2_arcs()` 시작부에서 상태 출력 호출 (`main_a.py:2191`).
- 상류/하류 컨텍스트:
- 상류: `arcs`는 DB anchor 로드값으로, `ep_count`가 문자열(`"5"`)로 저장될 가능성이 존재.
- 하류: `sum()` 누적 시 `int + str`로 `TypeError`; 상태 출력 전체가 예외 처리로 빠져 결과가 누락됨.
- 재현 근거:
- `sum(a.get('ep_count', 0) for a in [{'ep_count': '5'}] if isinstance(a, dict))` 실행 결과 `TypeError unsupported operand type(s) for +: 'int' and 'str'`.
- 판정: BUG.

2. 위험 지점
- 코드 원문:
- `future = executor.submit(asyncio.run, self._stage2_orch.stage_2_arcs_async_logic())` (`main_a.py:2207`)
- `future.result(timeout=600)` (`main_a.py:2208`)
- 호출자: `_run_main_process()` 메뉴 `choice == "2"` 분기 (`main_a.py:1872`~`main_a.py:1879`).
- 상류/하류 컨텍스트:
- 상류: 실행 시간이 600초를 넘는 경우 `TimeoutError` 발생 가능.
- 하류: `_stage_2_arcs()` 내 timeout 예외 처리 없음; 상위 `_run_main_process()`의 광역 예외로 이동해 시스템 종료 루틴으로 이어질 수 있음.
- 실패 시나리오: 장시간 Stage 2 실행 시 복구 없이 전체 메뉴 루프가 중단될 위험.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문:
- `if hasattr(self.current_project, "master_bible"):` (`main_a.py:2086`)
- `self.current_project.save_v20_anchor("bible", self.current_project.master_bible)` (`main_a.py:2087`)
- 호출자: `_run_main_process()` 종료 분기 `choice == "5"` (`main_a.py:1886`~`main_a.py:1888`) 및 예외 종료 경로 (`main_a.py:1924`).
- 상류/하류 컨텍스트:
- 상류: `master_bible` 내용 검증(비어있음/타입) 없이 저장 수행.
- 하류: 비정상 초기화 상태에서 빈/불완전 Bible이 DB anchor를 덮어쓸 가능성.
- 실패 시나리오: 프로젝트 로딩 실패 직후 종료 시 기존 Bible anchor가 의도치 않게 약화될 위험.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [MEDIUM] main_a.py:2176 — `ep_count` 문자열 값에서 Resume 통계 합산 TypeError

**문제**: `ep_count`를 정수 정규화 없이 합산해 문자열 값이 섞이면 예외가 발생한다.

**문제 코드**:
```python
total_eps = sum(a.get("ep_count", 0) for a in arcs if isinstance(a, dict)) if isinstance(arcs, list) else 0
```

**재현 근거**:
- 실행: `sum(a.get('ep_count', 0) for a in [{'ep_count': '5'}] if isinstance(a, dict))`
- 결과: `TypeError unsupported operand type(s) for +: 'int' and 'str'`

**호출 체인**: `main_a.py:2191` → `main_a.py:2176`

**수정 제안**:
```python
def _to_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0

total_eps = sum(_to_int(a.get("ep_count", 0)) for a in arcs if isinstance(a, dict)) if isinstance(arcs, list) else 0
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 82 완료

## Round 83 — main_a.py L2251~끝

### 진행 통계 업데이트
- 총 발견: 67건 (CRITICAL: 0, HIGH: 57, MEDIUM: 10)
- 라운드 진행: 83/100

### 5-A. 파일 구조 요약
- `main_a.py:2274` `def _build_item_acquisition_timeline(self, up_to_ep: int) -> str` — 아이템 획득 타임라인 문자열 생성 위임.
- `main_a.py:2354` `def _get_arc_context_for_episode(self, ep_num: int) -> tuple[int | None, dict | None]` — 에피소드→아크 매핑 조회.
- `main_a.py:2423` `def _stage_3_batch_blueprinting(self) -> None` — Stage3Context 주입 후 Stage3 오케스트레이터 실행.
- `main_a.py:2434` `def _select_genre(self) -> dict[str, Any]` — 멀티 장르 선택 UI.
- `main_a.py:2644` `def _select_project(self) -> str` — 프로젝트 디렉터리 목록 선택.
- `main_a.py:2724` `def _generate_narrative_summary(self, up_to_ep: int) -> None` — 5화 단위 내러티브 요약 생성/저장.
- `main_a.py:2848` `def _load_narrative_summaries(self) -> str` — 저장된 요약/상위 요약 로드.
- `main_a.py:2902` `def _stage_4_v2_chief_writer(self, limit_mode: bool = False) -> None` — Stage4Context 구성 후 Stage4 오케스트레이터 실행.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def _stage_4_v2_chief_writer(self, limit_mode: bool = False) -> None` (`main_a.py:2902`)
2. 특징 문자열:
- `self.ui.log(f"✅ [{selected['name']}] 전문 공정이 선택되었습니다.")` (`main_a.py:2619`)
- `self.ui.log(f"   ✅ [V66.1] 내러티브 요약 저장: {anchor_key} ({len(summary)}자)")` (`main_a.py:2838`)
- `return self._stage4_orch.stage_4_v2_chief_writer(limit_mode=limit_mode)` (`main_a.py:2993`)
3. import 목록:
- `from modules.core.stage3_context import Stage3Context` (`main_a.py:2428`)
- `from modules.core.world_state import WorldStateManager` (`main_a.py:2931`)
- `from modules.core.fact_ledger import FactLedger` (`main_a.py:2946`)
- `from modules.core.stage4_context import Stage4Context` (`main_a.py:2962`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문:
- `root = Path(self._PROJECTS_DIR)` (`main_a.py:2653`)
- `projects = [d.name for d in root.iterdir() if d.is_dir()]` (`main_a.py:2654`)
- 호출자: `boot()`에서 장르 선택 직후 프로젝트 선택 (`main_a.py:848`).
- 상류/하류 컨텍스트:
- 상류: `projects/` 디렉터리 존재 여부를 확인하지 않고 `iterdir()` 호출.
- 하류: 디렉터리가 없으면 즉시 `FileNotFoundError`로 부팅 실패.
- 재현 근거:
- `list(Path('_nonexistent_projects_dir_12345').iterdir())` 실행 결과 `FileNotFoundError`.
- 판정: BUG.

2. 위험 지점
- 코드 원문:
- `for ep_marker in range(5, 500, 5):` (`main_a.py:2858`)
- 호출자: Stage4Context 콜백으로 주입되어 Stage 4에서 사용 (`main_a.py:2986`).
- 상류/하류 컨텍스트:
- 상류: 요약 키 스캔 범위가 495화까지 고정.
- 하류: 500화 초과 프로젝트는 장기 요약이 있어도 로드 대상에서 누락되어 맥락 주입 품질이 저하될 수 있음.
- 실패 시나리오: 500화 이후 아카이브 요약이 프롬프트에 반영되지 않아 장기 연속성 회귀 가능.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문:
- `except Exception as _st_err:` (`main_a.py:2924`)
- `self.state_tracker = None` (`main_a.py:2926`)
- 호출자: `_run_main_process()` 메뉴 `choice == "4"` 분기 (`main_a.py:1884`~`main_a.py:1885`).
- 상류/하류 컨텍스트:
- 상류: StateTracker 초기화 실패를 비차단 처리.
- 하류: Stage 4가 `state_tracker=None` 상태로 계속 진행되어 연속성 보호가 약화될 수 있음.
- 실패 시나리오: 초기화 실패가 반복돼도 운영자는 경고 로그만 보고 계속 진행하게 되어 품질 저하를 뒤늦게 발견할 위험.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] main_a.py:2654 — `projects/` 디렉터리 미존재 시 프로젝트 선택 단계 FileNotFoundError

**문제**: `_select_project()`가 루트 디렉터리 존재를 검증하지 않고 `iterdir()`를 호출한다.

**문제 코드**:
```python
root = Path(self._PROJECTS_DIR)
projects = [d.name for d in root.iterdir() if d.is_dir()]
```

**재현 근거**:
- 실행: `list(Path('_nonexistent_projects_dir_12345').iterdir())`
- 결과: `FileNotFoundError [WinError 3] 지정된 경로를 찾을 수 없습니다`

**호출 체인**: `main_a.py:848` → `main_a.py:2644` → `main_a.py:2654`

**수정 제안**:
```python
root = Path(self._PROJECTS_DIR)
if not root.exists():
    root.mkdir(parents=True, exist_ok=True)
projects = [d.name for d in root.iterdir() if d.is_dir()]
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 83 완료

## Round 84 — modules/core/stage0/__init__.py

### 진행 통계 업데이트
- 총 발견: 69건 (CRITICAL: 0, HIGH: 58, MEDIUM: 11)
- 라운드 진행: 84/100

### 5-A. 파일 구조 요약
- `modules/core/stage0/__init__.py:37` `class StageZeroManager` — Stage 0 통합 관리자.
- `modules/core/stage0/__init__.py:82` `def show_menu(self, is_new_project: bool = True) -> int` — Stage 0 메뉴 선택.
- `modules/core/stage0/__init__.py:183` `def run_new_project_flow(self) -> tuple[dict, list, StyleGuide | None]` — 신규 컨셉 기반 생성 플로우.
- `modules/core/stage0/__init__.py:248` `def run_reverse_engineering_flow(self, input_path: str = None) -> tuple[dict, list, StyleGuide]` — 역설계 플로우.
- `modules/core/stage0/__init__.py:282` `def import_bible(self, bible_path: str = None) -> dict[str, Any]` — Bible JSON 임포트.
- `modules/core/stage0/__init__.py:360` `def run_reference_analysis(self, genre: str = None) -> StyleGuide | None` — 레퍼런스 문체 분석.
- `modules/core/stage0/__init__.py:430` `def save_state(self, output_dir: str)` — Stage0 상태 파일 저장.
- `modules/core/stage0/__init__.py:467` `def load_state(cls, project_path: str, llm_client=None) -> "StageZeroManager"` — Stage0 상태 로드.
- `modules/core/stage0/__init__.py:516` `def create_stage_zero(project_path: str = None, llm_client=None) -> StageZeroManager` — 매니저 팩토리 헬퍼.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def create_stage_zero(project_path: str = None, llm_client=None) -> StageZeroManager` (`modules/core/stage0/__init__.py:516`)
2. 특징 문자열:
- `logging.info("Stage 0 - 프로젝트 설정")` (`modules/core/stage0/__init__.py:85`)
- `logging.warning(f"[!] 임포트 실패: {e}")` (`modules/core/stage0/__init__.py:310`)
- `logging.info(f"[v] 상태 저장: {out}")` (`modules/core/stage0/__init__.py:464`)
3. import 목록:
- `from .preset_registry import FieldDefinition, PresetRegistry` (`modules/core/stage0/__init__.py:9`)
- `from .reverse_expander import ReverseExpander` (`modules/core/stage0/__init__.py:10`)
- `from .story_expander import StoryExpander` (`modules/core/stage0/__init__.py:11`)
- `from .style_extractor import StyleExtractor, StyleGuide` (`modules/core/stage0/__init__.py:12`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문:
- `self.bible = json.load(f)` (`modules/core/stage0/__init__.py:295`)
- `self.genre = self.bible.get("_genre", "")` (`modules/core/stage0/__init__.py:298`)
- 호출자: Stage0 메뉴에서 Bible 임포트 경로 (`modules/core/stage01_helpers.py:363` → `stage0_manager.import_bible()`).
- 상류/하류 컨텍스트:
- 상류: JSON 루트 타입 검증 없이 `self.bible`에 바로 할당.
- 하류: list 등 비dict 입력이면 `.get()`에서 예외가 나고, 예외 후에도 `self.bible`이 오염된 타입(list)으로 남음.
- 재현 근거:
- list JSON 파일 임포트 시 반환값은 `{}`이지만 내부 `manager.bible` 타입이 `list`로 유지됨.
- 판정: BUG.

2. 위험 지점
- 코드 원문:
- `with open(state_file, encoding="utf-8") as f:` (`modules/core/stage0/__init__.py:475`)
- `state = json.load(f)` (`modules/core/stage0/__init__.py:476`)
- 호출자: 파일 내 직접 호출 미확인(클래스 메서드 공개 API).
- 상류/하류 컨텍스트:
- 상류: 로드 파일 손상/부분 저장 가능성에 대한 예외 처리 부재.
- 하류: `JSONDecodeError`가 그대로 전파되어 Stage0 상태 복구 전체가 중단.
- 재현 근거:
- `stage0_state.json`에 깨진 JSON(`{bad json`) 저장 후 `StageZeroManager.load_state(...)` 호출 시 `JSONDecodeError` 발생.
- 판정: BUG.

3. 위험 지점
- 코드 원문:
- `except ImportError:` (`modules/core/stage0/__init__.py:28`)
- `SPINNER_AVAILABLE = False` (`modules/core/stage0/__init__.py:29`)
- `__all__ = [..., "Spinner", "ProgressBar", "PhaseIndicator", ...]` (`modules/core/stage0/__init__.py:521`~`modules/core/stage0/__init__.py:535`)
- 호출자: `from modules.core.stage0 import *` 또는 `from modules.core.stage0 import Spinner` 경로.
- 상류/하류 컨텍스트:
- 상류: 스피너 import 실패 시 해당 심볼 바인딩 없이 플래그만 설정.
- 하류: export 목록에 미정의 심볼이 남아 import 경로에서 예외를 유발할 수 있음.
- 실패 시나리오: spinner 의존성이 누락된 환경에서 stage0 모듈 import 안정성이 떨어짐.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [MEDIUM] modules/core/stage0/__init__.py:298 — Bible 임포트 실패 후 `self.bible` 오염 상태 유지

**문제**: JSON 루트가 dict가 아니면 예외로 실패 처리되지만, 실패 직전 할당된 비dict 값이 `self.bible`에 남는다.

**문제 코드**:
```python
with open(path, encoding="utf-8") as f:
    self.bible = json.load(f)

# 장르 추출
self.genre = self.bible.get("_genre", "")
```

**재현 근거**:
- list JSON 파일을 `import_bible()`로 로드.
- 결과: 반환값 `{}` (실패 처리) + 내부 `self.bible` 타입은 `list`로 잔존.

**호출 체인**: `modules/core/stage01_helpers.py:363` → `modules/core/stage0/__init__.py:282` → `modules/core/stage0/__init__.py:295` → `modules/core/stage0/__init__.py:298`

**수정 제안**:
```python
loaded = json.load(f)
if not isinstance(loaded, dict):
    raise ValueError("Bible JSON root must be object")
self.bible = loaded
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [HIGH] modules/core/stage0/__init__.py:476 — 손상된 state 파일에서 `load_state()` 예외 전파

**문제**: `load_state()`가 핵심 상태 파일 JSON 파싱 예외를 처리하지 않아 복구 경로가 전체 중단된다.

**문제 코드**:
```python
state_file = out / "stage0_state.json"
if state_file.exists():
    with open(state_file, encoding="utf-8") as f:
        state = json.load(f)
```

**재현 근거**:
- `stage0_state.json`에 `"{bad json"` 저장.
- `StageZeroManager.load_state(project_path)` 호출 시 `JSONDecodeError` 발생.

**호출 체인**: 외부 호출 → `modules/core/stage0/__init__.py:467` → `modules/core/stage0/__init__.py:476`

**수정 제안**:
```python
try:
    state = json.load(f)
except (json.JSONDecodeError, OSError):
    state = {}
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 84 완료

## Round 85 — modules/core/stage0/reverse_expander.py

### 진행 통계 업데이트
- 총 발견: 71건 (CRITICAL: 0, HIGH: 59, MEDIUM: 12)
- 라운드 진행: 85/100

### 5-A. 파일 구조 요약
- `modules/core/stage0/reverse_expander.py:28` `class ReverseExpander` — 기존 원고 기반 역설계 파이프라인.
- `modules/core/stage0/reverse_expander.py:75` `def _parse_json(self, text: str) -> dict | None` — LLM JSON 파싱.
- `modules/core/stage0/reverse_expander.py:97` `def load_drafts_from_file(self, file_path: str) -> int` — 합본 원고 분리 로드.
- `modules/core/stage0/reverse_expander.py:118` `def load_drafts_from_folder(self, folder_path: str) -> int` — 폴더 원고 로드.
- `modules/core/stage0/reverse_expander.py:200` `def extract_bible(self) -> dict[str, Any]` — Bible 구성.
- `modules/core/stage0/reverse_expander.py:298` `def extract_episode_bibles(self) -> list[dict[str, Any]]` — 회차별 상태 추출.
- `modules/core/stage0/reverse_expander.py:473` `def run(self, input_path: str, output_dir: str, genre: str = None) -> tuple[dict, list, StyleGuide]` — 역설계 통합 실행.
- `modules/core/stage0/reverse_expander.py:595` `def persist_to_db(self, project_context=None) -> dict[str, int]` — manuscripts/state_logs/episode_bibles/blueprint/arcs 저장.
- `modules/core/stage0/reverse_expander.py:894` `def _enrich_arc_stubs_from_episode_bibles(self, ctx) -> int` — Arc stub 보강.
- `modules/core/stage0/reverse_expander.py:1038` `def get_stub_summary(self) -> dict[str, Any]` — stub 요약 리포트.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def get_stub_summary(self) -> dict[str, Any]` (`modules/core/stage0/reverse_expander.py:1038`)
2. 특징 문자열:
- `logging.info(f"📂 자동 감지: {subdir}/ 폴더 사용")` (`modules/core/stage0/reverse_expander.py:133`)
- `print_success(f"{count}개 에피소드 로드")` (`modules/core/stage0/reverse_expander.py:485`)
- `logging.info(f"[v] Arc {arc_no} 보강: rels={len(agg_relationships[:10])}, npcs={len(agg_npcs[:20])}")` (`modules/core/stage0/reverse_expander.py:1026`)
3. import 목록:
- `from .preset_registry import PresetRegistry` (`modules/core/stage0/reverse_expander.py:16`)
- `from .style_extractor import StyleExtractor, StyleGuide` (`modules/core/stage0/reverse_expander.py:17`)
- `from modules.core.vec_memory import VecMemory` (`modules/core/stage0/reverse_expander.py:412`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문:
- `if isinstance(parsed, list): parsed = parsed[0] if parsed and isinstance(parsed[0], dict) else {}` (`modules/core/stage0/reverse_expander.py:87`~`modules/core/stage0/reverse_expander.py:88`)
- `return self._parse_json(self._call_llm(prompt)) or []` (`modules/core/stage0/reverse_expander.py:279`)
- 호출자: `extract_bible()`에서 `npcs = self._extract_npcs(sample_text)` (`modules/core/stage0/reverse_expander.py:210`).
- 상류/하류 컨텍스트:
- 상류: NPC 추출 프롬프트는 리스트 JSON을 요구함 (`modules/core/stage0/reverse_expander.py:275`~`modules/core/stage0/reverse_expander.py:277`).
- 하류: 파서가 리스트를 첫 dict로 축소해 `KeyNPCs` 스키마가 list→dict로 깨질 수 있음.
- 재현 근거:
- `_parse_json('[{"name":"A"},{"name":"B"}]')` 결과가 `{'name': 'A'}`로 축소됨.
- 판정: BUG.

2. 위험 지점
- 코드 원문:
- `self.raw_drafts.append({"ep_num": ep_num, "title": f"제{ep_num}화", "content": content})` (`modules/core/stage0/reverse_expander.py:154`)
- `return len(self.raw_drafts)` (`modules/core/stage0/reverse_expander.py:156`)
- 호출자: `run()`이 폴더 경로에서 매 실행 호출 (`modules/core/stage0/reverse_expander.py:517`~`modules/core/stage0/reverse_expander.py:521`).
- 상류/하류 컨텍스트:
- 상류: 파일 로드 전 `self.raw_drafts` 초기화가 없음.
- 하류: 동일 인스턴스에서 재실행 시 이전 결과가 누적되어 중복 저장/분석이 발생.
- 재현 근거:
- 동일 폴더를 두 번 호출 시 `counts 1 2 raw_len 2` (두 번째 호출에서 누적).
- 판정: BUG.

3. 위험 지점
- 코드 원문:
- `existing_arcs.sort(key=lambda x: x.get("arc_no", 0))` (`modules/core/stage0/reverse_expander.py:884`)
- 호출자: `persist_to_db()` → `_save_arc_stubs(ctx)` (`modules/core/stage0/reverse_expander.py:618`).
- 상류/하류 컨텍스트:
- 상류: `existing_arcs`는 DB anchor 값으로 타입이 불안정할 수 있음 (`modules/core/stage0/reverse_expander.py:873`~`modules/core/stage0/reverse_expander.py:876`).
- 하류: 비dict 요소가 섞이면 `.get` 호출에서 예외가 나고 Arc stub 저장 전체가 rollback됨.
- 실패 시나리오: 손상된 `arcs` anchor 데이터가 있는 프로젝트에서 역설계 Arc 저장이 모두 실패.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/core/stage0/reverse_expander.py:87 — list JSON을 첫 dict로 축소해 NPC 리스트 스키마 훼손

**문제**: `_parse_json()`이 리스트 응답을 무조건 첫 원소 dict로 변환해, 리스트를 기대하는 호출부(`_extract_npcs`)의 계약을 깨뜨린다.

**문제 코드**:
```python
parsed = json.loads(json_str.strip())
# [Sweep55] LLM이 list 반환 시 첫 dict 추출
if isinstance(parsed, list):
    parsed = parsed[0] if parsed and isinstance(parsed[0], dict) else {}
return parsed if isinstance(parsed, dict) else None
```

**재현 근거**:
- 실행: `_parse_json('[{"name":"A"},{"name":"B"}]')`
- 결과: `{'name': 'A'}` (list가 dict로 축소됨)

**호출 체인**: `modules/core/stage0/reverse_expander.py:200` → `modules/core/stage0/reverse_expander.py:210` → `modules/core/stage0/reverse_expander.py:279` → `modules/core/stage0/reverse_expander.py:87`

**수정 제안**:
```python
# 호출자별 계약 분리: _parse_json은 원형 유지
parsed = json.loads(json_str.strip())
return parsed
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [MEDIUM] modules/core/stage0/reverse_expander.py:154 — 원고 재로딩 시 `raw_drafts` 누적 중복

**문제**: `load_drafts_from_folder()`가 기존 `self.raw_drafts`를 비우지 않아 동일 인스턴스 재실행 시 중복이 누적된다.

**문제 코드**:
```python
for ep_num, f in numbered_files:
    with open(f, encoding="utf-8") as fp:
        content = fp.read()
    self.raw_drafts.append({"ep_num": ep_num, "title": f"제{ep_num}화", "content": content})

return len(self.raw_drafts)
```

**재현 근거**:
- 동일 폴더에서 2회 호출 결과: `counts 1 2 raw_len 2`.

**호출 체인**: `modules/core/stage0/reverse_expander.py:473` → `modules/core/stage0/reverse_expander.py:521` → `modules/core/stage0/reverse_expander.py:154`

**수정 제안**:
```python
self.raw_drafts = []
# 그 다음 파일 append
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 85 완료

## Round 86 — modules/core/stage0/style_extractor.py + story_expander.py

### 진행 통계 업데이트
- 총 발견: 73건 (CRITICAL: 0, HIGH: 60, MEDIUM: 13)
- 라운드 진행: 86/100

### 5-A. 파일 구조 요약
- `modules/core/stage0/style_extractor.py:21` `class StyleGuide` — 문체 DNA 데이터 모델.
- `modules/core/stage0/style_extractor.py:101` `def to_prompt(self) -> str` — 스타일 가이드를 프롬프트 텍스트로 변환.
- `modules/core/stage0/style_extractor.py:209` `def extract_from_drafts(self, drafts: list[str], reference_name: str = "") -> StyleGuide` — 통계+LLM 결합 문체 추출.
- `modules/core/stage0/style_extractor.py:275` `def _analyze_statistics_v2(self, drafts: list[str]) -> dict[str, Any]` — 문장/대화/시점 통계.
- `modules/core/stage0/style_extractor.py:659` `def _llm_call(self, prompt: str) -> dict[str, Any]` — 다중 모델 폴백 호출.
- `modules/core/stage0/story_expander.py:25` `class StoryExpander` — 컨셉→Bible/Treatment 생성.
- `modules/core/stage0/story_expander.py:90` `def analyze_concept(self, concept: str) -> dict[str, Any]` — 컨셉 구조화.
- `modules/core/stage0/story_expander.py:137` `def generate_bible(self, protagonist_config: dict[str, Any] = None) -> dict[str, Any]` — Bible 생성.
- `modules/core/stage0/story_expander.py:205` `def _generate_npcs(self) -> list[dict[str, Any]]` — NPC 생성.
- `modules/core/stage0/story_expander.py:375` `def _generate_details(self, skeleton: list[dict]) -> list[dict[str, Any]]` — 스켈레톤 상세화.
- `modules/core/stage0/story_expander.py:433` `def run(self, concept: str, output_dir: str, protagonist_config: dict = None) -> tuple[dict, list]` — 통합 실행.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def compare_styles(self, guide1: StyleGuide, guide2: StyleGuide) -> dict[str, Any]` (`modules/core/stage0/style_extractor.py:707`)
- `def run(self, concept: str, output_dir: str, protagonist_config: dict = None) -> tuple[dict, list]` (`modules/core/stage0/story_expander.py:433`)
2. 특징 문자열:
- `logging.info("[1/5] 통계 분석...")` (`modules/core/stage0/style_extractor.py:230`)
- `logging.info("[4/5] LLM 없음 - 통계 분석만 사용")` (`modules/core/stage0/style_extractor.py:256`)
- `print_success(f"Treatment 생성 완료 ({len(self.treatment)} 블록)")` (`modules/core/stage0/story_expander.py:458`)
3. import 목록:
- `from .preset_registry import PresetRegistry` (`modules/core/stage0/story_expander.py:14`)
- `from .preset_registry import PresetRegistry` (`modules/core/stage0/style_extractor.py:16`)
- `from .style_extractor import StyleExtractor, StyleGuide` (`modules/core/stage0/__init__.py:12`, 연계 모듈)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문:
- `def _generate_npcs(self) -> list[dict[str, Any]]:` (`modules/core/stage0/story_expander.py:205`)
- `return self._parse_json(self._call_llm(prompt)) or []` (`modules/core/stage0/story_expander.py:216`)
- 호출자: `generate_bible()`에서 `npcs = self._generate_npcs()` (`modules/core/stage0/story_expander.py:145`).
- 상류/하류 컨텍스트:
- 상류: `_parse_json()`은 dict/list 모두 반환 가능 (`modules/core/stage0/story_expander.py:72`~`modules/core/stage0/story_expander.py:84`).
- 하류: dict가 반환되면 `KeyNPCs`가 list가 아닌 dict로 저장되어 스키마 불일치.
- 재현 근거:
- `_call_llm`이 `{"name":"NPC1"}` 반환하도록 모킹 시 `_generate_npcs()` 결과 타입이 `dict`.
- 판정: BUG.

2. 위험 지점
- 코드 원문:
- `result = self._parse_json(self._call_llm(prompt)) or []` (`modules/core/stage0/story_expander.py:404`)
- `detailed.extend(result if result else batch)` (`modules/core/stage0/story_expander.py:405`)
- 호출자: `generate_treatment()` → `_generate_details()` (`modules/core/stage0/story_expander.py:228` → `modules/core/stage0/story_expander.py:375`).
- 상류/하류 컨텍스트:
- 상류: `result` 타입 검증 없이 `extend()` 대상에 직접 사용.
- 하류: `result`가 dict이면 list에 dict 키 문자열이 추가되어 treatment 구조가 붕괴.
- 재현 근거:
- `_call_llm`을 dict JSON으로 모킹하면 `_generate_details()` 결과가 `['block_id', 'title']`(문자열 리스트)로 오염.
- 판정: BUG.

3. 위험 지점
- 코드 원문:
- `dialogues = re.findall(r'["""]([^"""]+)["""]', all_text)` (`modules/core/stage0/style_extractor.py:284`)
- 호출자: `extract_from_drafts()` → `_analyze_statistics_v2()` (`modules/core/stage0/style_extractor.py:231`).
- 상류/하류 컨텍스트:
- 상류: 대화 검출이 `"` 기반 한정 패턴으로 구현.
- 하류: 『 』, 「 」, 작은따옴표 등 작품별 대화 표기를 놓치면 `dialogue_ratio`가 과소계산되어 문체 프로파일이 왜곡될 수 있음.
- 실패 시나리오: 비표준 인용부호를 쓰는 작품에서 대화 비율/샘플 대화가 거의 0으로 수렴.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [MEDIUM] modules/core/stage0/story_expander.py:216 — `_generate_npcs()` 반환 타입 불안정(dict/list)

**문제**: 함수 시그니처는 `list[dict]`를 약속하지만 `_parse_json` 결과를 그대로 반환해 dict가 유입될 수 있다.

**문제 코드**:
```python
def _generate_npcs(self) -> list[dict[str, Any]]:
    ...
    return self._parse_json(self._call_llm(prompt)) or []
```

**재현 근거**:
- `_call_llm` 모킹 반환값 `{"name":"NPC1"}`일 때 `_generate_npcs()` 출력 타입 `dict` 확인.

**호출 체인**: `modules/core/stage0/story_expander.py:137` → `modules/core/stage0/story_expander.py:145` → `modules/core/stage0/story_expander.py:216`

**수정 제안**:
```python
parsed = self._parse_json(self._call_llm(prompt))
return parsed if isinstance(parsed, list) else []
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [HIGH] modules/core/stage0/story_expander.py:405 — dict 결과를 `extend()`하여 treatment가 문자열 리스트로 붕괴

**문제**: `_generate_details()`가 `result` 타입을 검증하지 않고 `extend()`해 dict일 때 키 문자열이 삽입된다.

**문제 코드**:
```python
result = self._parse_json(self._call_llm(prompt)) or []
detailed.extend(result if result else batch)
```

**재현 근거**:
- `_call_llm` 모킹값 dict JSON에서 `_generate_details([{'block_id':'Block 1'}])` 결과가 `['block_id', 'title']`.

**호출 체인**: `modules/core/stage0/story_expander.py:222` → `modules/core/stage0/story_expander.py:228` → `modules/core/stage0/story_expander.py:404` → `modules/core/stage0/story_expander.py:405`

**수정 제안**:
```python
if isinstance(result, list):
    detailed.extend(result)
else:
    detailed.extend(batch)
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 86 완료

## Round 87 — modules/core/stage0/spinner.py + preset_registry.py + stage01_helpers.py

### 진행 통계 업데이트
- 총 발견: 75건 (CRITICAL: 0, HIGH: 61, MEDIUM: 14)
- 라운드 진행: 87/100

### 5-A. 파일 구조 요약
- `modules/core/stage0/spinner.py:145` `class Spinner` — Rich/폴백 스피너.
- `modules/core/stage0/spinner.py:293` `class ProgressBar` — 진행률 표시.
- `modules/core/stage0/spinner.py:375` `class PhaseIndicator` — 단계 표시.
- `modules/core/stage0/spinner.py:574` `def with_spinner(message: str = "처리 중", style: str = "dots", color_theme: str = "wave")` — 스피너 데코레이터.
- `modules/core/stage0/preset_registry.py:24` `class PresetRegistry` — 장르별 HUD/NPC 스키마/정규화.
- `modules/core/stage0/preset_registry.py:463` `def normalize_hud(self, raw_hud: dict[str, Any]) -> dict[str, Any]` — HUD 타입 정규화.
- `modules/core/stage0/preset_registry.py:509` `def _parse_korean_number(self, text: str) -> int` — 한글 금액 파싱.
- `modules/core/stage0/preset_registry.py:644` `def from_json(cls, json_str: str) -> "PresetRegistry"` — JSON 직렬화 복원.
- `modules/core/stage01_helpers.py:29` `def phase_0_recovery(self)` — Stage 0 서브메뉴 진입/기존 방식 동기화.
- `modules/core/stage01_helpers.py:260` `def stage_0_extended(self, mode: int = 0)` — Stage 0 확장 경로 실행.
- `modules/core/stage01_helpers.py:473` `def stage_1_volumes(self)` — Stage 1 권별 전략 설계 루프.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def with_spinner(message: str = "처리 중", style: str = "dots", color_theme: str = "wave")` (`modules/core/stage0/spinner.py:574`)
- `def from_json(cls, json_str: str) -> "PresetRegistry"` (`modules/core/stage0/preset_registry.py:644`)
- `def stage_1_volumes(self)` (`modules/core/stage01_helpers.py:473`)
2. 특징 문자열:
- `console.print("[bold green]✓[/] ", end="")` (`modules/core/stage0/spinner.py:475`)
- `if matches >= 3:  # 3개 이상 키워드 매칭 시` (`modules/core/stage0/preset_registry.py:549`)
- `app.ui.log("📜 [Stage 1] 권별 고해상도 순차 설계 (V41 유동 아크)")` (`modules/core/stage01_helpers.py:477`)
3. import 목록:
- `from modules.core.stage0.story_expander import StoryExpander` (`modules/core/stage01_helpers.py:233`)
- `from modules.core.constants import Emojis, RetryLimits, VolumeSettings` (`modules/core/stage01_helpers.py:519`)
- `from modules.core.spinners import StageSpinner` (`modules/core/stage01_helpers.py:520`)
- `from main_a import STAGE0_AVAILABLE` (`modules/core/stage01_helpers.py:40`, `modules/core/stage01_helpers.py:272`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문:
- `multipliers = {"억": 100000000, "만": 10000, "천": 1000, "백": 100}` (`modules/core/stage0/preset_registry.py:515`)
- `for char in text:` ... `total += current * multipliers[char]` (`modules/core/stage0/preset_registry.py:525`~`modules/core/stage0/preset_registry.py:532`)
- 호출자: `normalize_hud()` → `_enforce_type()`에서 int 필드 문자열 정규화 시 사용 (`modules/core/stage0/preset_registry.py:473`, `modules/core/stage0/preset_registry.py:486`).
- 상류/하류 컨텍스트:
- 상류: 복합 단위(`천만`, `억천만`)를 자리수 계층으로 처리하지 않음.
- 하류: 자본/자산 값이 심각하게 축소되어 HUD 상태가 왜곡됨.
- 재현 근거:
- `_parse_korean_number('3천만')` 결과 `13000` (기대: `30000000`).
- 판정: BUG.

2. 위험 지점
- 코드 원문:
- `data = json.loads(json_str)` (`modules/core/stage0/preset_registry.py:646`)
- 호출자: `StageZeroManager.load_state()`에서 preset 복원 (`modules/core/stage0/__init__.py:501`~`modules/core/stage0/__init__.py:502`).
- 상류/하류 컨텍스트:
- 상류: 손상된 `preset_state.json`에 대한 예외 처리 없음.
- 하류: `JSONDecodeError` 전파로 Stage 0 상태 복구 전체 실패.
- 재현 근거:
- `PresetRegistry.from_json('{bad')` 실행 시 `JSONDecodeError` 발생.
- 판정: BUG.

3. 위험 지점
- 코드 원문:
- `existing_treatment = data.get("treatments", [])` (`modules/core/stage01_helpers.py:195`)
- `existing_treatment[-1].get('block_id', 'N/A')` (`modules/core/stage01_helpers.py:210`)
- 호출자: `stage_0_extended()` choice 4 경로에서 `app._extend_blocks(stage0_manager)` 호출 (`modules/core/stage01_helpers.py:366`).
- 상류/하류 컨텍스트:
- 상류: treatment JSON 내부 요소 타입(dict 여부) 검증 없이 마지막 원소 `.get` 사용.
- 하류: 잘못된 형식(문자열/숫자 리스트) treatment 파일이면 즉시 `AttributeError`로 확장 루틴 중단.
- 실패 시나리오: 수동 편집/외부 생성된 treatment 파일에서 Stage 0 확장 메뉴가 비정상 종료될 수 있음.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/core/stage0/preset_registry.py:525 — 복합 한글 단위(`천만`) 파싱 오류로 금액 축소

**문제**: `_parse_korean_number()`가 복합 단위를 계층적으로 계산하지 않아 `3천만` 같은 값을 `13000`으로 오파싱한다.

**문제 코드**:
```python
multipliers = {"억": 100000000, "만": 10000, "천": 1000, "백": 100}
...
for char in text:
    if char.isdigit():
        current = current * 10 + int(char)
    elif char in multipliers:
        if current == 0:
            current = 1
        total += current * multipliers[char]
        current = 0
```

**재현 근거**:
- `_parse_korean_number('3천만')` → `13000`
- `_parse_korean_number('50억')` → `5000000000` (단일 단위는 정상)

**호출 체인**: `modules/core/stage0/preset_registry.py:463` → `modules/core/stage0/preset_registry.py:473` → `modules/core/stage0/preset_registry.py:486` → `modules/core/stage0/preset_registry.py:525`

**수정 제안**:
```python
# 큰 단위(억/만) 기준으로 섹션 분할 후 천/백/십 보조단위 계산
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [MEDIUM] modules/core/stage0/preset_registry.py:646 — 손상된 preset JSON에서 복원 예외 전파

**문제**: `from_json()`가 파싱 예외를 처리하지 않아 복원 경로 전체가 중단된다.

**문제 코드**:
```python
@classmethod
def from_json(cls, json_str: str) -> "PresetRegistry":
    data = json.loads(json_str)
    registry = cls(base_genre=data.get("base_genre"))
    ...
```

**재현 근거**:
- 실행: `PresetRegistry.from_json('{bad')`
- 결과: `JSONDecodeError`

**호출 체인**: `modules/core/stage0/__init__.py:501` → `modules/core/stage0/__init__.py:502` → `modules/core/stage0/preset_registry.py:644` → `modules/core/stage0/preset_registry.py:646`

**수정 제안**:
```python
try:
    data = json.loads(json_str)
except json.JSONDecodeError:
    return cls(base_genre=None)
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 87 완료

## Round 88 — modules/core/semantic_item_registry.py + modules/core/genre_hud_manager.py

### 진행 통계 업데이트
- 총 발견: 77건 (CRITICAL: 0, HIGH: 62, MEDIUM: 15)
- 라운드 진행: 88/100

### 5-A. 파일 구조 요약
- `modules/core/semantic_item_registry.py:55` `class SemanticItemRegistry` — 아이템 별칭/중복 획득 방지 레지스트리.
- `modules/core/semantic_item_registry.py:655` `load_from_arcs(self, arcs_data: dict, protagonist_name: str = "주인공") -> int` — Arc 상태에서 아이템 상태 복원.
- `modules/core/semantic_item_registry.py:723` `generate_constraint_text(self, current_arc: int) -> str` — 프롬프트 제약 텍스트 생성.
- `modules/core/genre_hud_manager.py:640` `create_hud_manager(genre_type, context)` — 장르별 HUD 매니저 팩토리.
- `modules/core/genre_hud_manager.py:679` `validate_hud_compatibility(hud_manager, required_attrs: list = None) -> dict` — HUD 호환성 점검.
- `modules/core/genre_hud_manager.py:730` `log_hud_compatibility_report(hud_manager, logger=None) -> None` — HUD 호환성 리포트 출력.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def create_item_registry() -> SemanticItemRegistry` (`modules/core/semantic_item_registry.py:776`)
- `def log_hud_compatibility_report(hud_manager, logger=None) -> None` (`modules/core/genre_hud_manager.py:730`)
2. 특징 문자열:
- `"[SEMANTIC ITEM REGISTRY - 중복 획득 금지 목록]"` (`modules/core/semantic_item_registry.py:741`)
- `logger(f"   🔍 [V61.3] HUD 호환성 체크: {report['genre']}")` (`modules/core/genre_hud_manager.py:743`)
3. import 목록:
- `import re` (`modules/core/semantic_item_registry.py:21`)
- `import threading` (`modules/core/semantic_item_registry.py:22`)
- `import logging` (`modules/core/genre_hud_manager.py:6`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `self.register_item(item, arc_no, owner=protagonist_name, source="주인공 획득")` (`modules/core/semantic_item_registry.py:689`)
- 호출자: `load_from_arcs()` 내부 protagonist_items 루프 (`modules/core/semantic_item_registry.py:686`~`modules/core/semantic_item_registry.py:690`)
- 상류/하류 컨텍스트:
- 상류: `protagonist_items = state_constraints.get("protagonist_items") or []` (`modules/core/semantic_item_registry.py:682`)로 dict 요소가 유입될 수 있음.
- 하류: `register_item()` → `_normalize_name()`의 `name.strip()` (`modules/core/semantic_item_registry.py:139`)에서 크래시.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `equipment = arc_end_state.get("equipment") or []` (`modules/core/semantic_item_registry.py:714`)
- 호출자: `load_from_arcs()` arc_end_state 처리 블록 (`modules/core/semantic_item_registry.py:713`~`modules/core/semantic_item_registry.py:719`)
- 상류/하류 컨텍스트:
- 상류: `arc_end_state = state_constraints.get("arc_end_state") or {}` (`modules/core/semantic_item_registry.py:713`) 타입 검증 없음.
- 하류: `.get` 호출 시 `AttributeError`.
- 판정: BUG.

3. 위험 지점
- 코드 원문: `for attr_name, attr_type in required_attrs:` (`modules/core/genre_hud_manager.py:716`)
- 호출자: `log_hud_compatibility_report()` → `validate_hud_compatibility()` (`modules/core/genre_hud_manager.py:741`)
- 상류/하류 컨텍스트:
- 상류: `required_attrs`를 외부 호출자가 직접 전달 가능 (`modules/core/genre_hud_manager.py:679`).
- 하류: tuple 쌍이 아닌 값 전달 시 unpack 예외 가능.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/core/semantic_item_registry.py:139 — dict 아이템 입력 시 `strip()` 크래시

**문제**: `load_from_arcs()`가 dict 형태 아이템을 그대로 `register_item()`에 전달하면 `_normalize_name()`에서 `name.strip()` 호출로 즉시 크래시한다.

**문제 코드**:
```python
normalized = name.strip()
```

**재현 근거**:
- 실행: `SemanticItemRegistry().load_from_arcs([{'arc_no':1,'state_constraints':{'protagonist_items':[{'name':'검'}]}}])`
- 결과: `AttributeError: 'dict' object has no attribute 'strip'`

**호출 체인**: `modules/core/semantic_item_registry.py:655` → `modules/core/semantic_item_registry.py:689` → `modules/core/semantic_item_registry.py:228` → `modules/core/semantic_item_registry.py:139`

**수정 제안**:
```python
if isinstance(item, dict):
    item = item.get("name", "")
if not isinstance(item, str):
    continue
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [MEDIUM] modules/core/semantic_item_registry.py:714 — `arc_end_state` 타입 불일치 시 `.get` 크래시

**문제**: `arc_end_state`가 dict가 아닐 때 `.get("equipment")`를 호출해 예외가 발생한다.

**문제 코드**:
```python
arc_end_state = state_constraints.get("arc_end_state") or {}
equipment = arc_end_state.get("equipment") or []
```

**재현 근거**:
- 실행: `SemanticItemRegistry().load_from_arcs([{'arc_no':1,'state_constraints':{'arc_end_state':['bad']}}])`
- 결과: `AttributeError: 'list' object has no attribute 'get'`

**호출 체인**: `modules/core/semantic_item_registry.py:655` → `modules/core/semantic_item_registry.py:713` → `modules/core/semantic_item_registry.py:714`

**수정 제안**:
```python
arc_end_state = state_constraints.get("arc_end_state") or {}
if not isinstance(arc_end_state, dict):
    arc_end_state = {}
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 88 완료

## Round 89 — modules/core/tree_of_thoughts.py + modules/core/agent_intelligence.py

### 진행 통계 업데이트
- 총 발견: 80건 (CRITICAL: 0, HIGH: 63, MEDIUM: 17)
- 라운드 진행: 89/100

### 5-A. 파일 구조 요약
- `modules/core/tree_of_thoughts.py:65` `class TreeOfThoughts` — 다중 분기 탐색/평가 엔진.
- `modules/core/tree_of_thoughts.py:163` `explore(...) -> ToTResult` — 일반 ToT 탐색 진입점.
- `modules/core/tree_of_thoughts.py:348` `explore_blueprint(...) -> ToTResult` — 블루프린트 전용 탐색.
- `modules/core/tree_of_thoughts.py:418` `_evaluate_blueprint(self, output: str) -> dict[str, Any]` — Python 휴리스틱 평가.
- `modules/core/agent_intelligence.py:48` `class AgentIntelligence` — few-shot/anti-pattern/self-critique 프롬프트 조립기.
- `modules/core/agent_intelligence.py:451` `get_architect_enhancement(...) -> str` — Architect 강화 프롬프트 생성.
- `modules/core/agent_intelligence.py:530` `quick_quality_check(self, text: str, agent_type: AgentType) -> dict[str, Any]` — 출력 품질 휴리스틱 체크.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def _escape(self, text: str) -> str` (`modules/core/tree_of_thoughts.py:720`)
- `def quick_quality_check(self, text: str, agent_type: AgentType) -> dict[str, Any]` (`modules/core/agent_intelligence.py:530`)
2. 특징 문자열:
- `lines = ["[V53.5 Tree of Thoughts 탐색 결과]"]` (`modules/core/tree_of_thoughts.py:314`)
- `parts.append(self.get_self_critique_prompt(AgentType.ARCHITECT))` (`modules/core/agent_intelligence.py:484`)
3. import 목록:
- `import json` (`modules/core/tree_of_thoughts.py:25`)
- `import re` (`modules/core/tree_of_thoughts.py:27`)
- `from dataclasses import dataclass, field` (`modules/core/agent_intelligence.py:27`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `approach=approach.get("name", f"Approach {i + 1}"),` (`modules/core/tree_of_thoughts.py:226`)
- 호출자: `explore()` → `_generate_approaches()` (`modules/core/tree_of_thoughts.py:205`~`modules/core/tree_of_thoughts.py:221`)
- 상류/하류 컨텍스트:
- 상류: `approaches = result.get("approaches", [])` (`modules/core/tree_of_thoughts.py:269`)에서 list 타입 보장 없음.
- 하류: `approach`가 str이면 `.get` 호출 크래시.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `best_path=paths[0]` (`modules/core/tree_of_thoughts.py:415`)
- 호출자: `explore_blueprint(..., n_branches=0)` (`modules/core/tree_of_thoughts.py:386`)
- 상류/하류 컨텍스트:
- 상류: `for i, approach in enumerate(blueprint_approaches[:n_branches])` (`modules/core/tree_of_thoughts.py:386`)에서 `n_branches=0`이면 paths 비어 있음.
- 하류: `IndexError`로 결과 반환 불가.
- 판정: BUG.

3. 위험 지점
- 코드 원문: `position = ep_num - ep_start + 1` (`modules/core/agent_intelligence.py:469`)
- 호출자: `get_architect_enhancement()` (`modules/core/agent_intelligence.py:451`)
- 상류/하류 컨텍스트:
- 상류: `ep_start = arc_data.get("ep_start", 1)` (`modules/core/agent_intelligence.py:467`) 타입 정규화 없음.
- 하류: 문자열 유입 시 산술 TypeError.
- 판정: BUG.

### 5-C. 발견된 버그
### [HIGH] modules/core/tree_of_thoughts.py:226 — `approaches` 요소 타입 미검증으로 `.get` 크래시

**문제**: LLM 응답의 `approaches`가 list[str]로 오면 `approach.get(...)`에서 예외가 난다.

**문제 코드**:
```python
approaches = result.get("approaches", [])
...
approach=approach.get("name", f"Approach {i + 1}"),
```

**재현 근거**:
- `_call_llm`이 `{"approaches":"abc"}` 반환하도록 모킹 후 `explore(...)` 실행.
- 결과: `AttributeError: 'str' object has no attribute 'get'`

**호출 체인**: `modules/core/tree_of_thoughts.py:163` → `modules/core/tree_of_thoughts.py:269` → `modules/core/tree_of_thoughts.py:216` → `modules/core/tree_of_thoughts.py:226`

**수정 제안**:
```python
approaches = result.get("approaches", [])
if not isinstance(approaches, list):
    approaches = []
approaches = [a for a in approaches if isinstance(a, dict)]
```

**확신도**: HIGH

**FP 체크**: FP-5(LLM 파싱 폴백) 비해당. 해당 경로는 폴백 전에 크래시.

### [MEDIUM] modules/core/tree_of_thoughts.py:415 — `n_branches=0`에서 빈 paths 인덱싱

**문제**: `n_branches=0` 입력 시 `paths[0]` 접근으로 `IndexError`.

**문제 코드**:
```python
for i, approach in enumerate(blueprint_approaches[:n_branches]):
    ...
return ToTResult(
    paths=paths, best_path=paths[0], merged_output=None, exploration_summary=self._generate_summary(paths)
)
```

**재현 근거**:
- 실행: `explore_blueprint(..., n_branches=0)`
- 결과: `IndexError: list index out of range`

**호출 체인**: `modules/core/tree_of_thoughts.py:348` → `modules/core/tree_of_thoughts.py:386` → `modules/core/tree_of_thoughts.py:415`

**수정 제안**:
```python
if not paths:
    return self._single_path_fallback(task, context, generator_fn)
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [MEDIUM] modules/core/agent_intelligence.py:469 — `ep_start/ep_end` 문자열 유입 시 산술 TypeError

**문제 코드**:
```python
ep_start = arc_data.get("ep_start", 1)
ep_end = arc_data.get("ep_end", 5)
position = ep_num - ep_start + 1
total = ep_end - ep_start + 1
```

**재현 근거**:
- 실행: `get_architect_enhancement(3, {'ep_start':'1','ep_end':5})`
- 결과: `TypeError: unsupported operand type(s) for -: 'int' and 'str'`

**호출 체인**: `modules/core/agent_intelligence.py:451` → `modules/core/agent_intelligence.py:467`~`modules/core/agent_intelligence.py:470`

**수정 제안**:
```python
ep_start = int(arc_data.get("ep_start", 1) or 1)
ep_end = int(arc_data.get("ep_end", ep_start) or ep_start)
```

**확신도**: HIGH

**FP 체크**: FP-5 비해당.

---
## Round 89 완료

## Round 90 — modules/core/pre_director_checklist.py + modules/core/constitutional_checker.py

### 진행 통계 업데이트
- 총 발견: 83건 (CRITICAL: 0, HIGH: 63, MEDIUM: 20)
- 라운드 진행: 90/100

### 5-A. 파일 구조 요약
- `modules/core/pre_director_checklist.py:84` `class PreDirectorChecklist` — Director 호출 전 Python 체크리스트.
- `modules/core/pre_director_checklist.py:152` `check(self, content: str, content_type: str = "manuscript", context: dict[str, Any] = None) -> ChecklistResult`.
- `modules/core/pre_director_checklist.py:193` `_check_manuscript(self, manuscript: str, context: dict[str, Any]) -> list[CheckItem]`.
- `modules/core/pre_director_checklist.py:445` `_check_blueprint(self, content: str, context: dict[str, Any]) -> list[CheckItem]`.
- `modules/core/constitutional_checker.py:49` `class ConstitutionalChecker` — Stage2/3/4 헌법형 자기검증 프롬프트 생성.
- `modules/core/constitutional_checker.py:197` `get_analyst_constitution(...) -> str`.
- `modules/core/constitutional_checker.py:260` `get_architect_constitution(...) -> str`.
- `modules/core/constitutional_checker.py:543` `get_full_injection(self, stage: int, context: dict[str, Any] = None) -> str`.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def get_feedback(self, result: ChecklistResult) -> str` (`modules/core/pre_director_checklist.py:573`)
- `def get_full_injection(self, stage: int, context: dict[str, Any] = None) -> str` (`modules/core/constitutional_checker.py:543`)
2. 특징 문자열:
- `lines = ["[V53.4 Pre-Director Checklist]"]` (`modules/core/pre_director_checklist.py:561`)
- `"[V55.2 Constitutional Self-Check: Arc 단계]"` (`modules/core/constitutional_checker.py:210`)
3. import 목록:
- `from modules.core.constants import ManuscriptLimits` (`modules/core/pre_director_checklist.py:30`)
- `from modules.core.constants import ManuscriptLimits` (`modules/core/constitutional_checker.py:24`)
- `import json` (`modules/core/pre_director_checklist.py:24`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `length = len(manuscript)` (`modules/core/pre_director_checklist.py:198`)
- 호출자: `check()` → `_check_manuscript()` (`modules/core/pre_director_checklist.py:173`)
- 상류/하류 컨텍스트:
- 상류: `check(content, content_type="manuscript")`에서 `content` 타입 검증 없음.
- 하류: `None` 유입 시 `TypeError`.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `arc_no = arc.get("arc_no", "?")` (`modules/core/constitutional_checker.py:222`)
- 호출자: `get_analyst_constitution(prev_arcs=...)` (`modules/core/constitutional_checker.py:197`)
- 상류/하류 컨텍스트:
- 상류: `prev_arcs` 요소 타입 검증 없음.
- 하류: 문자열/숫자 요소 유입 시 `.get` 크래시.
- 판정: BUG.

3. 위험 지점
- 코드 원문: `tactical = arc_data.get("tactical_doc", "")` (`modules/core/constitutional_checker.py:282`)
- 호출자: `get_architect_constitution(arc_data=...)` (`modules/core/constitutional_checker.py:260`)
- 상류/하류 컨텍스트:
- 상류: `arc_data` dict 타입 강제 없음.
- 하류: 문자열 유입 시 `.get` 크래시.
- 판정: BUG.

### 5-C. 발견된 버그
### [MEDIUM] modules/core/pre_director_checklist.py:198 — manuscript `None` 입력 시 길이 계산 크래시

**문제 코드**:
```python
length = len(manuscript)
```

**재현 근거**:
- 실행: `PreDirectorChecklist().check(None, "manuscript", {})`
- 결과: `TypeError: object of type 'NoneType' has no len()`

**호출 체인**: `modules/core/pre_director_checklist.py:152` → `modules/core/pre_director_checklist.py:173` → `modules/core/pre_director_checklist.py:198`

**수정 제안**:
```python
if not isinstance(manuscript, str):
    manuscript = ""
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [MEDIUM] modules/core/constitutional_checker.py:222 — prev_arcs 요소 타입 미검증

**문제 코드**:
```python
for arc in prev_arcs:
    arc_no = arc.get("arc_no", "?")
```

**재현 근거**:
- 실행: `ConstitutionalChecker().get_analyst_constitution(prev_arcs=["bad"])`
- 결과: `AttributeError: 'str' object has no attribute 'get'`

**호출 체인**: `modules/core/constitutional_checker.py:197` → `modules/core/constitutional_checker.py:221` → `modules/core/constitutional_checker.py:222`

**수정 제안**:
```python
for arc in prev_arcs:
    if not isinstance(arc, dict):
        continue
```

**확신도**: HIGH

**FP 체크**: FP-5 비해당.

### [MEDIUM] modules/core/constitutional_checker.py:282 — arc_data 타입 미검증

**문제 코드**:
```python
if arc_data:
    tactical = arc_data.get("tactical_doc", "")
```

**재현 근거**:
- 실행: `ConstitutionalChecker().get_architect_constitution(arc_data="bad")`
- 결과: `AttributeError: 'str' object has no attribute 'get'`

**호출 체인**: `modules/core/constitutional_checker.py:260` → `modules/core/constitutional_checker.py:281` → `modules/core/constitutional_checker.py:282`

**수정 제안**:
```python
if not isinstance(arc_data, dict):
    arc_data = {}
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 90 완료

## 90라운드 오탐 재검증
- 재검증 범위: Round 88~90 신규 BUG 8건.
- 결과: 8건 모두 재현 명령으로 런타임 예외 확인.
- 판정 변경:
- 없음.
- 재검증 메모: FP-5(LLM 파싱 폴백), FP-1(비차단 갱신) 규칙과 교차 확인했으며 해당 항목은 폴백/비차단 이전에 직접 예외가 발생함.

## Round 91 — modules/core/constraint_db.py + modules/core/martial_manager.py

### 진행 통계 업데이트
- 총 발견: 86건 (CRITICAL: 0, HIGH: 65, MEDIUM: 21)
- 라운드 진행: 91/100

### 5-A. 파일 구조 요약
- `modules/core/constraint_db.py:46` `class ConstraintDB` — Arc 제약 상태 저장/검증.
- `modules/core/constraint_db.py:93` `_parse_arc_state(self, arc_data: dict)` — Arc 상태 파싱 및 내부 인덱스 갱신.
- `modules/core/constraint_db.py:521` `validate_arc_design(self, arc_data: dict) -> dict[str, Any]`.
- `modules/core/martial_manager.py:7` `class MartialManager` — Martial HUD/상태 정규화.
- `modules/core/martial_manager.py:299` `update_physical_status(self, full_state_data) -> list`.
- `modules/core/martial_manager.py:503` `get_hud_trend(self, ep_num: int, window: int = 5) -> str`.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def create_constraint_db(project_context) -> ConstraintDB` (`modules/core/constraint_db.py:579`)
- `def get_hud_trend(self, ep_num: int, window: int = 5) -> str` (`modules/core/martial_manager.py:503`)
2. 특징 문자열:
- `logging.warning(f"[ConstraintDB] arc_no 파싱 실패: {arc_no!r} -> 스킵")` (`modules/core/constraint_db.py:101`)
- `"""[쌩자 Guard Logic] 에이전트 변칙 키를 정식 키로 강제 치환"""` (`modules/core/martial_manager.py:300`)
3. import 목록:
- `from modules.core.semantic_item_registry import SemanticItemRegistry, create_item_registry` (`modules/core/constraint_db.py:24`)
- `from .constants import MARTIAL_METRICS` (`modules/core/martial_manager.py:4`)
- `import re` (`modules/core/constraint_db.py:18`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `equipment = arc_end_state.get("equipment", [])` (`modules/core/constraint_db.py:118`)
- 호출자: `__init__()` 초기 로드 루프에서 `_parse_arc_state()` (`modules/core/constraint_db.py:83`, `modules/core/constraint_db.py:93`)
- 상류/하류 컨텍스트:
- 상류: `arc_end_state = state_constraints.get("arc_end_state") or {}` (`modules/core/constraint_db.py:108`) 타입 검증 없음.
- 하류: list 유입 시 `.get` 예외.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `phys_inv = joint_docs.get("physical_inventory", [])` (`modules/core/constraint_db.py:125`)
- 호출자: `_parse_arc_state()` 내부 inventory 조립.
- 상류/하류 컨텍스트:
- 상류: `joint_docs = arc_data.get("joint_docs", {})` (`modules/core/constraint_db.py:111`) 타입 검증 없음.
- 하류: list 유입 시 `.get` 예외.
- 판정: BUG.

3. 위험 지점
- 코드 원문: `actual_in = full_state_data.get("actual_truth", full_state_data)` (`modules/core/martial_manager.py:310`)
- 호출자: `update_physical_status()` (`modules/core/martial_manager.py:299`)
- 상류/하류 컨텍스트:
- 상류: `if not full_state_data: return []`만 존재, dict 타입 강제 없음.
- 하류: list/str 유입 시 `.get` 예외.
- 판정: BUG.

### 5-C. 발견된 버그
### [HIGH] modules/core/constraint_db.py:118 — arc_end_state 타입 불일치 크래시

**문제 코드**:
```python
arc_end_state = state_constraints.get("arc_end_state") or {}
equipment = arc_end_state.get("equipment", [])
```

**재현 근거**:
- 실행: `ConstraintDB(ctx)._parse_arc_state({'arc_no':1,'state_constraints':{'arc_end_state':['bad']}})`
- 결과: `AttributeError: 'list' object has no attribute 'get'`

**호출 체인**: `modules/core/constraint_db.py:93` → `modules/core/constraint_db.py:108` → `modules/core/constraint_db.py:118`

**수정 제안**:
```python
if not isinstance(arc_end_state, dict):
    arc_end_state = {}
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [HIGH] modules/core/constraint_db.py:125 — joint_docs 타입 불일치 크래시

**문제 코드**:
```python
joint_docs = arc_data.get("joint_docs", {})
phys_inv = joint_docs.get("physical_inventory", [])
```

**재현 근거**:
- 실행: `ConstraintDB(ctx)._parse_arc_state({'arc_no':1,'joint_docs':['bad'],'state_constraints':{}})`
- 결과: `AttributeError: 'list' object has no attribute 'get'`

**호출 체인**: `modules/core/constraint_db.py:93` → `modules/core/constraint_db.py:111` → `modules/core/constraint_db.py:125`

**수정 제안**:
```python
if not isinstance(joint_docs, dict):
    joint_docs = {}
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [MEDIUM] modules/core/martial_manager.py:310 — full_state_data dict 가정으로 `.get` 크래시

**문제 코드**:
```python
actual_in = full_state_data.get("actual_truth", full_state_data)
```

**재현 근거**:
- 실행: `MartialManager(ctx).update_physical_status(['bad'])`
- 결과: `AttributeError: 'list' object has no attribute 'get'`

**호출 체인**: `modules/core/martial_manager.py:299` → `modules/core/martial_manager.py:310`

**수정 제안**:
```python
if not isinstance(full_state_data, dict):
    return []
```

**확신도**: HIGH

**FP 체크**: FP-1(비차단 갱신) 비해당. 예외가 비차단 처리 전에 발생.

---
## Round 91 완료

## Round 92 — modules/core/relationship_tracker_factions.py + modules/core/relationship_tracker_npc.py + modules/core/relationship_tracker.py

### 진행 통계 업데이트
- 총 발견: 88건 (CRITICAL: 0, HIGH: 65, MEDIUM: 23)
- 라운드 진행: 92/100

### 5-A. 파일 구조 요약
- `modules/core/relationship_tracker.py:31` `class RelationshipTracker` — NPC/팩션 관계 추적 facade.
- `modules/core/relationship_tracker.py:77` `record_transition(self, *args, **kwargs)` — NPC 서브모듈 위임.
- `modules/core/relationship_tracker_npc.py:14` `class RelationshipTrackerNPC` — NPC 상태 전이 규칙/이력.
- `modules/core/relationship_tracker_npc.py:238` `record_transition(...) -> dict[str, Any]` — 전이 기록 및 검증.
- `modules/core/relationship_tracker_factions.py:42` `class RelationshipTrackerFactions` — 팩션 관계/파워 밸런스.
- `modules/core/relationship_tracker_factions.py:118` `register_faction_v59(...) -> FactionInfo`.
- `modules/core/relationship_tracker_factions.py:780` `generate_faction_report_v59(...) -> str`.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def generate_faction_report_v59(self, genre: str = "wuxia") -> str` (`modules/core/relationship_tracker_factions.py:780`)
- `def generate_transition_prompt(self, from_state: str, to_state: str) -> str` (`modules/core/relationship_tracker_npc.py:384`)
- `def generate_faction_report_v59(self, *args, **kwargs)` (`modules/core/relationship_tracker.py:129`)
2. 특징 문자열:
- `"[V49.7] trigger 누락:"` (`modules/core/relationship_tracker_npc.py:260`)
- `lines.append("  기회:")` (`modules/core/relationship_tracker_factions.py:806`)
3. import 목록:
- `from modules.core.relationship_tracker_factions import FactionInfo, FactionRelationshipEvent` (`modules/core/relationship_tracker.py:14`)
- `from modules.core.relationship_tracker import RelationshipEvent` (`modules/core/relationship_tracker_npc.py:8`)
- `import re` (`modules/core/relationship_tracker_factions.py:5`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `if not trigger or len(trigger.strip()) < 5:` (`modules/core/relationship_tracker_npc.py:256`)
- 호출자: `RelationshipTracker.record_transition()` 위임 (`modules/core/relationship_tracker.py:77`)
- 상류/하류 컨텍스트:
- 상류: facade가 args/kwargs를 그대로 전달, 타입 검증 없음.
- 하류: list/dict trigger 유입 시 `.strip` 예외.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `power_level=max(0, min(100, power_level)),` (`modules/core/relationship_tracker_factions.py:136`)
- 호출자: `RelationshipTracker.register_faction_v59()` (`modules/core/relationship_tracker.py:93`)
- 상류/하류 컨텍스트:
- 상류: 파워 레벨 문자열 유입 가능.
- 하류: `min(100, "90")` 비교 TypeError.
- 판정: BUG.

3. 위험 지점
- 코드 원문: `self.host.faction_relations[key1] = state` (`modules/core/relationship_tracker_factions.py:162`)
- 호출자: `set_faction_relation_v59()` (`modules/core/relationship_tracker_factions.py:144`)
- 상류/하류 컨텍스트:
- 상류: faction 존재 검증 없이 relation부터 기록.
- 하류: 존재하지 않는 faction 조합도 relation 테이블에 잔존 가능.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [MEDIUM] modules/core/relationship_tracker_npc.py:256 — trigger 타입 미검증으로 `strip()` 크래시

**문제 코드**:
```python
if not trigger or len(trigger.strip()) < 5:
```

**재현 근거**:
- 실행: `RelationshipTracker().record_transition(..., trigger=['사건'], justification='충분한 근거입니다')`
- 결과: `AttributeError: 'list' object has no attribute 'strip'`

**호출 체인**: `modules/core/relationship_tracker.py:77` → `modules/core/relationship_tracker_npc.py:238` → `modules/core/relationship_tracker_npc.py:256`

**수정 제안**:
```python
if not isinstance(trigger, str):
    return {"valid": False, "event": None, "error": "trigger type invalid"}
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [MEDIUM] modules/core/relationship_tracker_factions.py:136 — power_level 문자열 입력에서 비교 TypeError

**문제 코드**:
```python
power_level=max(0, min(100, power_level)),
```

**재현 근거**:
- 실행: `RelationshipTracker().register_faction_v59('문파', '90')`
- 결과: `TypeError: '<' not supported between instances of 'str' and 'int'`

**호출 체인**: `modules/core/relationship_tracker.py:93` → `modules/core/relationship_tracker_factions.py:118` → `modules/core/relationship_tracker_factions.py:136`

**수정 제안**:
```python
try:
    power_level = int(power_level)
except (TypeError, ValueError):
    power_level = 50
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 92 완료

## Round 93 — modules/core/power_scaling.py + modules/core/vec_memory.py

### 진행 통계 업데이트
- 총 발견: 90건 (CRITICAL: 0, HIGH: 66, MEDIUM: 24)
- 라운드 진행: 93/100

### 5-A. 파일 구조 요약
- `modules/core/power_scaling.py:65` `class PowerScalingTracker` — 파워 수치/성장 검증.
- `modules/core/power_scaling.py:150` `set_power(self, character: str, arc: int, power: int, reason: str = "", episode: int = 0) -> dict[str, Any]`.
- `modules/core/power_scaling.py:202` `validate_growth(...) -> dict[str, Any]`.
- `modules/core/power_scaling.py:308` `_evaluate_justification_quality(self, justification: str) -> tuple`.
- `modules/core/vec_memory.py:46` `class VecMemory` — sqlite-vec 기반 벡터 메모리.
- `modules/core/vec_memory.py:494` `close(self) -> None`.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def generate_scaling_prompt(self, protagonist: str) -> str` (`modules/core/power_scaling.py:468`)
- `def __del__(self) -> None` (`modules/core/vec_memory.py:505`)
2. 특징 문자열:
- `"[V49.7 파워 스케일링 가이드]"` (`modules/core/power_scaling.py:488`)
- `EMBED_MODEL = "gemini-embedding-001"` (`modules/core/vec_memory.py:22`)
3. import 목록:
- `from dataclasses import dataclass` (`modules/core/power_scaling.py:18`)
- `import sqlite3` (`modules/core/vec_memory.py:15`)
- `from pathlib import Path` (`modules/core/vec_memory.py:18`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `power = max(0, min(100, power))` (`modules/core/power_scaling.py:164`)
- 호출자: `set_power()` (`modules/core/power_scaling.py:150`)
- 상류/하류 컨텍스트:
- 상류: LLM/외부 입력 문자열 가능.
- 하류: 문자열 비교 TypeError.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `justification_lower = justification.lower()` (`modules/core/power_scaling.py:318`)
- 호출자: `validate_growth()` → `_evaluate_justification_quality()` (`modules/core/power_scaling.py:249`)
- 상류/하류 컨텍스트:
- 상류: `justification` 타입 정규화 없음.
- 하류: list/dict 유입 시 AttributeError.
- 판정: BUG.

3. 위험 지점
- 코드 원문: `if hasattr(res, "embeddings") and res.embeddings:` (`modules/core/vec_memory.py` 임베딩 응답 처리)
- 호출자: 벡터 임베딩 생성 루틴.
- 상류/하류 컨텍스트:
- 상류: 외부 API 응답 스키마 의존.
- 하류: 응답 구조 변경 시 인덱싱/속성 오류 가능.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/core/power_scaling.py:164 — power 문자열 입력 시 `min/max` 비교 TypeError

**문제 코드**:
```python
power = max(0, min(100, power))
```

**재현 근거**:
- 실행: `PowerScalingTracker().set_power('a', 1, '80')`
- 결과: `TypeError: '<' not supported between instances of 'str' and 'int'`

**호출 체인**: `modules/core/power_scaling.py:150` → `modules/core/power_scaling.py:164`

**수정 제안**:
```python
power = int(power)
power = max(0, min(100, power))
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [MEDIUM] modules/core/power_scaling.py:318 — justification 비문자열 입력 시 `lower()` 크래시

**문제 코드**:
```python
justification_lower = justification.lower()
```

**재현 근거**:
- 실행: `validate_growth('a', 2, 40, justification=['기연'])`
- 결과: `AttributeError: 'list' object has no attribute 'lower'`

**호출 체인**: `modules/core/power_scaling.py:202` → `modules/core/power_scaling.py:249` → `modules/core/power_scaling.py:318`

**수정 제안**:
```python
if not isinstance(justification, str):
    justification = str(justification or "")
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 93 완료

## Round 94 — modules/core/narrative_diversity.py + modules/core/diversity_sampler.py

### 진행 통계 업데이트
- 총 발견: 91건 (CRITICAL: 0, HIGH: 66, MEDIUM: 25)
- 라운드 진행: 94/100

### 5-A. 파일 구조 요약
- `modules/core/narrative_diversity.py:29` `class NarrativeDiversityEngine` — 패턴 추적 + 샘플링 통합.
- `modules/core/narrative_diversity.py:413` `generate_diverse_blueprint(...)`.
- `modules/core/narrative_diversity.py:523` `save_state(self) -> bool`.
- `modules/core/diversity_sampler.py:16` `class DiversitySampler`.
- `modules/core/diversity_sampler.py:48` `sample_and_select(...) -> tuple[str, dict]`.
- `modules/core/diversity_sampler.py:98` `sample_blueprints(...) -> tuple[dict, dict]`.
- `modules/core/diversity_sampler.py:302` `compare_candidates(self, candidates: list[str]) -> list[dict]`.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def load_state(self) -> bool` (`modules/core/narrative_diversity.py:527`)
- `def sample_blueprint_or_single(...)` (`modules/core/diversity_sampler.py:478`)
2. 특징 문자열:
- `injection += "\n[경고: 플롯 패턴 반복 감지]\n"` (`modules/core/narrative_diversity.py:504`)
- `logging.info(f"[DiversitySampler] {n_samples}개 샘플 생성 중..")` (`modules/core/diversity_sampler.py:65`)
3. import 목록:
- `from .diversity_sampler import ConditionalDiversitySampler, DiversitySampler` (`modules/core/narrative_diversity.py:25`)
- `from .pattern_tracker import PatternTracker` (`modules/core/narrative_diversity.py:26`)
- `import re` (`modules/core/diversity_sampler.py:12`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `score = self._calculate_diversity_score(text)` (`modules/core/diversity_sampler.py:315`)
- 호출자: `compare_candidates()` (`modules/core/diversity_sampler.py:302`)
- 상류/하류 컨텍스트:
- 상류: `candidates` 요소 타입 검증 없음.
- 하류: `None` 요소 유입 시 내부 regex TypeError.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `return self.diversity_sampler.sample_blueprints(generator_fn, n_samples)` (`modules/core/narrative_diversity.py:413`)
- 호출자: 엔진 블루프린트 생성 경로.
- 상류/하류 컨텍스트:
- 상류: generator_fn 반환 타입 계약(dict) 강제 없음.
- 하류: sampler 내부 점수 집계 시 타입 혼선 가능.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `samples.append(sample)` (`modules/core/diversity_sampler.py:73`)
- 호출자: `sample_and_select()`.
- 상류/하류 컨텍스트:
- 상류: 생성기 편향으로 거의 동일한 샘플만 나와도 통과.
- 하류: 다양성 점수는 계산되나 품질 하한선(quality floor) 없음.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [MEDIUM] modules/core/diversity_sampler.py:315 — 후보 요소 `None`에서 diversity 계산 크래시

**문제 코드**:
```python
for i, text in enumerate(candidates):
    score = self._calculate_diversity_score(text)
```

**재현 근거**:
- 실행: `DiversitySampler().compare_candidates(['ok', None])`
- 결과: `TypeError: expected string or bytes-like object, got 'NoneType'`

**호출 체인**: `modules/core/diversity_sampler.py:302` → `modules/core/diversity_sampler.py:315` → `_calculate_diversity_score(...)`

**수정 제안**:
```python
if not isinstance(text, str):
    continue
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 94 완료

## Round 95 — modules/core/character_voice.py + modules/core/character_voice_profiler.py

### 진행 통계 업데이트
- 총 발견: 91건 (CRITICAL: 0, HIGH: 66, MEDIUM: 25)
- 라운드 진행: 95/100

### 5-A. 파일 구조 요약
- `modules/core/character_voice.py:68` `class CharacterVoiceTracker` — 대사 기반 캐릭터 보이스 추적.
- `modules/core/character_voice.py:152` `analyze_dialogue(self, dialogue: str) -> dict[str, Any]`.
- `modules/core/character_voice.py:199` `analyze_manuscript(self, ep_num: int, manuscript: str, known_characters: list[str] = None) -> dict[str, Any]`.
- `modules/core/character_voice_profiler.py:48` `class CharacterVoiceProfiler`.
- `modules/core/character_voice_profiler.py:179` `extract_profile_from_text(...) -> VoiceProfile | None`.
- `modules/core/character_voice_profiler.py:303` `check_consistency(self, character_name: str, dialogue: str) -> dict[str, Any]`.
- `modules/core/character_voice_profiler.py:446` `create_voice_profiler(...) -> CharacterVoiceProfiler`.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def clear(self) -> None` (`modules/core/character_voice.py:457`)
- `def create_voice_profiler(db_manager=None, genre: str = "wuxia") -> CharacterVoiceProfiler` (`modules/core/character_voice_profiler.py:446`)
2. 특징 문자열:
- `logging.warning(f"[CharacterVoiceTracker] Load error: {e}")` (`modules/core/character_voice.py:455`)
- `logging.info(f"[VoiceProfiler] '{character_name}' 대사 부족 ({len(dialogues)}/{min_dialogues})")` (`modules/core/character_voice_profiler.py:194`)
3. import 목록:
- `import json` (`modules/core/character_voice.py:20`)
- `from collections import Counter` (`modules/core/character_voice_profiler.py:19`)
- `from dataclasses import asdict, dataclass, field, fields` (`modules/core/character_voice_profiler.py:20`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `"length": len(dialogue),` (`modules/core/character_voice.py:155`)
- 호출자: `analyze_manuscript()` 내 대사 루프 (`modules/core/character_voice.py:211`)
- 상류/하류 컨텍스트:
- 상류: `extract_dialogues()`가 문자열 대사만 반환하는 계약.
- 하류: 계약 깨지면 `TypeError`.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `if len(dialogues) < min_dialogues:` (`modules/core/character_voice_profiler.py:193`)
- 호출자: `extract_profile_from_text()`.
- 상류/하류 컨텍스트:
- 상류: `_extract_character_dialogues()`에서 list 반환 보장.
- 하류: 입력 text 비문자열이면 내부 regex 단계에서 실패 가능.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `return list(set(dialogues))` (`modules/core/character_voice_profiler.py:238`)
- 호출자: `_extract_character_dialogues()`.
- 상류/하류 컨텍스트:
- 상류: 중복 제거를 set으로 수행.
- 하류: 대사 순서 정보 유실(캐릭터 말투 시간축 분석 왜곡 가능).
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 95 완료

## Round 96 — modules/core/pacing_analyzer.py + modules/core/foreshadow_tracker.py + modules/core/emotion_tracker.py

### 진행 통계 업데이트
- 총 발견: 92건 (CRITICAL: 0, HIGH: 66, MEDIUM: 26)
- 라운드 진행: 96/100

### 5-A. 파일 구조 요약
- `modules/core/pacing_analyzer.py:79` `class PacingAnalyzer`.
- `modules/core/pacing_analyzer.py:117` `analyze(self, manuscript: str) -> PacingAnalysis`.
- `modules/core/pacing_analyzer.py:393` `compare_episodes(self, analyses: list[PacingAnalysis]) -> dict[str, Any]`.
- `modules/core/foreshadow_tracker.py:84` `class ForeshadowTracker`.
- `modules/core/foreshadow_tracker.py:137` `plant(...) -> Foreshadow`.
- `modules/core/foreshadow_tracker.py:281` `auto_detect_from_manuscript(...) -> list[Foreshadow]`.
- `modules/core/emotion_tracker.py:11` `class EmotionArcTracker`.
- `modules/core/emotion_tracker.py:343` `save_to_db(self, db_manager) -> None`.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def get_zone_distribution(self, analysis: PacingAnalysis) -> dict[PacingZone, float]` (`modules/core/pacing_analyzer.py:425`)
- `def clear(self) -> None` (`modules/core/foreshadow_tracker.py:472`)
- `def load_from_db(self, db_manager) -> None` (`modules/core/emotion_tracker.py:357`)
2. 특징 문자열:
- `logging.warning("[Sweep7-C] foreshadow_tracker: skipping non-integer key: %s", k)` (`modules/core/foreshadow_tracker.py:456`)
- `if len(self.history) > 50:` (`modules/core/emotion_tracker.py:313`)
3. import 목록:
- `import re` (`modules/core/pacing_analyzer.py:18`)
- `import json` (`modules/core/foreshadow_tracker.py:20`)
- `from collections import Counter` (`modules/core/emotion_tracker.py:8`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `return re.sub(r"\s+", " ", hook.strip().lower())` (`modules/core/foreshadow_tracker.py:135`)
- 호출자: `plant()`/`hint()`/`payoff()` (`modules/core/foreshadow_tracker.py:147`, `modules/core/foreshadow_tracker.py:189`, `modules/core/foreshadow_tracker.py:208`)
- 상류/하류 컨텍스트:
- 상류: hook 문자열 타입 강제 없음.
- 하류: list/dict hook 유입 시 AttributeError.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `if not manuscript or len(manuscript) < 100:` (`modules/core/pacing_analyzer.py:122`)
- 호출자: `analyze()`.
- 상류/하류 컨텍스트:
- 상류: manuscript 타입 강제 없음.
- 하류: 비문자열이면 `split/finditer` 단계에서 예외 가능.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `last_entry = self.history[-1]` (`modules/core/emotion_tracker.py:331`)
- 호출자: `get_emotion_report()`.
- 상류/하류 컨텍스트:
- 상류: `if not self.history` 가드 존재 (`modules/core/emotion_tracker.py:323`).
- 하류: 가드 덕분에 현재는 안전하지만 외부에서 history를 비정상 타입으로 오염하면 리스크.
- 판정: 안전(가드 확인).

### 5-C. 발견된 버그
### [MEDIUM] modules/core/foreshadow_tracker.py:135 — hook 타입 미검증으로 `strip()` 크래시

**문제 코드**:
```python
def _normalize_hook(self, hook: str) -> str:
    return re.sub(r"\s+", " ", hook.strip().lower())
```

**재현 근거**:
- 실행: `ForeshadowTracker().plant(1, ['비밀'])`
- 결과: `AttributeError: 'list' object has no attribute 'strip'`

**호출 체인**: `modules/core/foreshadow_tracker.py:137` → `modules/core/foreshadow_tracker.py:147` → `modules/core/foreshadow_tracker.py:135`

**수정 제안**:
```python
if not isinstance(hook, str):
    hook = str(hook or "")
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 96 완료

## Round 97 — modules/core/information_diffusion.py + modules/core/lore_manager.py + modules/core/semantic_cache.py

### 진행 통계 업데이트
- 총 발견: 92건 (CRITICAL: 0, HIGH: 66, MEDIUM: 26)
- 라운드 진행: 97/100

### 5-A. 파일 구조 요약
- `modules/core/information_diffusion.py:24` `class InformationDiffusion`.
- `modules/core/information_diffusion.py:75` `should_npc_know(self, npc: dict, event: dict, current_ep: int) -> dict`.
- `modules/core/information_diffusion.py:365` `propagate_event(...) -> list[str]`.
- `modules/core/lore_manager.py:6` `class LoreManager`.
- `modules/core/lore_manager.py:367` `build_validation_encyclopedia(self) -> dict`.
- `modules/core/semantic_cache.py:65` `class SemanticCache`.
- `modules/core/semantic_cache.py:203` `get(...) -> Any | None`.
- `modules/core/semantic_cache.py:276` `set(...) -> str`.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def generate_knowledge_prompt(self, npc_name: str) -> str` (`modules/core/information_diffusion.py:419`)
- `def _extract_aliases(self, description: str) -> list[str]` (`modules/core/lore_manager.py:429`)
- `def get_similar_description(self, desc_type: str, subject: str) -> str | None` (`modules/core/semantic_cache.py:417`)
2. 특징 문자열:
- `lines = ["", f"[{npc_name}의 지식 상태]", f"알고 있는 정보 ({len(knowledge)}개):"]` (`modules/core/information_diffusion.py:434`)
- `f"⏰ [LoreManager] 캐시 노화 중 ..."` (`modules/core/lore_manager.py:59`)
- `CACHEABLE_TYPES = { ... "arc_tactical", "arc_constraint" ... }` (`modules/core/semantic_cache.py:69`)
3. import 목록:
- `import logging` (`modules/core/information_diffusion.py:8`)
- `import re` (`modules/core/lore_manager.py:2`)
- `import threading` (`modules/core/semantic_cache.py:30`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `event_ep = event.get("episode", 0)` (`modules/core/information_diffusion.py:92`)
- 호출자: `should_npc_know()`.
- 상류/하류 컨텍스트:
- 상류: npc/event dict 타입 강제 없음.
- 하류: 타입 오염 시 `.get` 예외.
- 판정: RISK (Design Check Needed).

2. 위험 지점
- 코드 원문: `existing_items = {lore["item"].strip().lower() for lore in self.db.get_lore_list_by_category("item") or []}` (`modules/core/lore_manager.py:314`)
- 호출자: 아이템 동기화 루틴.
- 상류/하류 컨텍스트:
- 상류: DB 반환 항목의 `"item"` 키/문자열 보장 필요.
- 하류: `None` 또는 key 누락 시 예외 가능.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `key_fields = [context.get("ep_num", ""), ...]` (`modules/core/semantic_cache.py:109`)
- 호출자: `get()`/`set()`에서 `_generate_context_hash()` 호출.
- 상류/하류 컨텍스트:
- 상류: context dict 계약.
- 하류: dict가 아니면 `.get` 예외.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 97 완료

## Round 98 — modules/core/ab_testing.py + modules/core/confidence_calibration.py + modules/core/data_collector.py + modules/domain/agents/negative_example_injector.py + modules/core/semantic_plot_guard.py

### 진행 통계 업데이트
- 총 발견: 94건 (CRITICAL: 0, HIGH: 66, MEDIUM: 28)
- 라운드 진행: 98/100

### 5-A. 파일 구조 요약
- `modules/core/ab_testing.py:17` `class ABTestingFramework`.
- `modules/core/ab_testing.py:436` `quick_ab_test(...) -> str`.
- `modules/core/confidence_calibration.py:65` `class ConfidenceCalibrator`.
- `modules/core/confidence_calibration.py:104` `assess(...) -> ConfidenceResult`.
- `modules/core/data_collector.py:17` `class DataCollector`.
- `modules/core/data_collector.py:67` `collect_validation_result(...)`.
- `modules/core/data_collector.py:442` `auto_collect_from_validation(...)`.
- `modules/domain/agents/negative_example_injector.py:114` `class NegativeExampleInjector`.
- `modules/core/semantic_plot_guard.py:48` `class SemanticPlotGuard`.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def quick_ab_test(...) -> str` (`modules/core/ab_testing.py:436`)
- `def get_summary(self, result: ConfidenceResult) -> str` (`modules/core/confidence_calibration.py:445`)
- `def auto_collect_from_validation(...)` (`modules/core/data_collector.py:442`)
- `def create_negative_example_injector(...) -> NegativeExampleInjector` (`modules/domain/agents/negative_example_injector.py:272`)
- `def _check_keyword_fallback(...) -> list[dict]` (`modules/core/semantic_plot_guard.py:274`)
2. 특징 문자열:
- `logging.info(report)` (`modules/core/ab_testing.py:462`)
- `if manuscript.strip() and manuscript.strip()[-1] in '.!?"」':` (`modules/core/confidence_calibration.py:188`)
- `f"📊 [V63] SemanticPlotGuard: {indexed}개 플롯 인덱싱 완료 ..."` (`modules/core/semantic_plot_guard.py:141`)
3. import 목록:
- `from modules.core.constants import ManuscriptLimits` (`modules/core/confidence_calibration.py:32`)
- `import json` (`modules/core/data_collector.py:10`)
- `import logging` (`modules/core/ab_testing.py:9`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `length = len(manuscript)` (`modules/core/confidence_calibration.py:149`)
- 호출자: `assess(..., content_type="manuscript")` → `_assess_manuscript()` (`modules/core/confidence_calibration.py:136`)
- 상류/하류 컨텍스트:
- 상류: `content` 타입 강제 없음.
- 하류: `None` 유입 시 TypeError.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `"manuscript_length": len(manuscript),` (`modules/core/data_collector.py:84`)
- 호출자: `collect_validation_result()` (`modules/core/data_collector.py:67`)
- 상류/하류 컨텍스트:
- 상류: manuscript 타입 강제 없음.
- 하류: `None` 유입 시 TypeError.
- 판정: BUG.

3. 위험 지점
- 코드 원문: `validation_context=ms_data["validation_context"],` (`modules/core/ab_testing.py:455`)
- 호출자: `quick_ab_test()` (`modules/core/ab_testing.py:451`)
- 상류/하류 컨텍스트:
- 상류: 입력 dict 키 누락 방어 없음.
- 하류: KeyError 가능.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [MEDIUM] modules/core/confidence_calibration.py:149 — manuscript `None`에서 길이 계산 크래시

**문제 코드**:
```python
def _assess_manuscript(self, manuscript: str, context: dict[str, Any]) -> ConfidenceResult:
    ...
    length = len(manuscript)
```

**재현 근거**:
- 실행: `ConfidenceCalibrator().assess(None, ContentType.MANUSCRIPT, {})`
- 결과: `TypeError: object of type 'NoneType' has no len()`

**호출 체인**: `modules/core/confidence_calibration.py:104` → `modules/core/confidence_calibration.py:136` → `modules/core/confidence_calibration.py:143` → `modules/core/confidence_calibration.py:149`

**수정 제안**:
```python
if not isinstance(manuscript, str):
    manuscript = ""
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

### [MEDIUM] modules/core/data_collector.py:84 — manuscript `None`에서 len() 크래시

**문제 코드**:
```python
data = {
    "ep_num": ep_num,
    "manuscript": manuscript,
    "manuscript_length": len(manuscript),
    "manuscript_hash": self._hash_text(manuscript),
    ...
}
```

**재현 근거**:
- 실행: `DataCollector('p').collect_validation_result(1, None, {'decision':'PASS'}, {})`
- 결과: `TypeError: object of type 'NoneType' has no len()`

**호출 체인**: `modules/core/data_collector.py:67` → `modules/core/data_collector.py:84`

**수정 제안**:
```python
if not isinstance(manuscript, str):
    manuscript = ""
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 98 완료

## Round 99 — modules/core/pre_director_manuscript_checker.py + modules/core/pre_director_narrative_checker.py + modules/core/pre_director_style_checker.py + modules/core/error_helper.py + modules/core/reference_anchor.py

### 진행 통계 업데이트
- 총 발견: 96건 (CRITICAL: 0, HIGH: 67, MEDIUM: 29)
- 라운드 진행: 99/100

### 5-A. 파일 구조 요약
- `modules/core/pre_director_manuscript_checker.py:22` `class PreDirectorManuscriptChecker`.
- `modules/core/pre_director_narrative_checker.py:14` `class PreDirectorNarrativeChecker`.
- `modules/core/pre_director_style_checker.py:14` `class PreDirectorStyleChecker`.
- `modules/core/error_helper.py:204` `class ErrorHelper`.
- `modules/core/reference_anchor.py:12` `class ReferenceAnchor`.
- `modules/core/reference_anchor.py:40` `extract_anchors_from_manuscript(...) -> list`.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def _check_cliche_density(self, manuscript: str) -> list[CheckItem]` (`modules/core/pre_director_manuscript_checker.py:383`)
- `def _check_setting_keywords(self, manuscript: str, context: dict[str, Any]) -> list[CheckItem]` (`modules/core/pre_director_narrative_checker.py:277`)
- `def _check_pacing_rhythm(self, manuscript: str) -> list[CheckItem]` (`modules/core/pre_director_style_checker.py:103`)
- `def get_solution(error_code: str) -> str` (`modules/core/error_helper.py:348`)
- `def get_statistics(self) -> dict` (`modules/core/reference_anchor.py:321`)
2. 특징 문자열:
- `if not any(item.category == CheckCategory.SETTING_KEYWORDS for item in items):` (`modules/core/pre_director_narrative_checker.py:351`)
- `return {"status": "no_context", "error": "Database context not available", "total_anchors": 0}` (`modules/core/reference_anchor.py:330`)
3. import 목록:
- `from modules.core.pre_director_checklist import CheckCategory, CheckItem, CheckSeverity` (`modules/core/pre_director_narrative_checker.py:8`)
- `from modules.core.pre_director_checklist import CheckCategory, CheckItem, CheckSeverity` (`modules/core/pre_director_style_checker.py:8`)
- `from modules.core.constants import ManuscriptLimits` (`modules/core/error_helper.py:11`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문:
- `# 주요 아이템이 초반에 언급되지 않음 - 경고만                items.append(` (`modules/core/pre_director_narrative_checker.py:340`)
- `CheckItem(...)` (`modules/core/pre_director_narrative_checker.py:341`~`modules/core/pre_director_narrative_checker.py:348`)
- 호출자: `PreDirectorChecklist._check_manuscript()` → `_check_setting_keywords()` (`modules/core/pre_director_checklist.py:403`, `modules/core/pre_director_checklist.py:425`)
- 상류/하류 컨텍스트:
- 상류: `owned_items` 존재 + 초반 미언급이면 WARNING을 append해야 하는 분기.
- 하류: `items.append(`가 주석 뒤에 붙어 실질적으로 실행되지 않아 WARNING 유실.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `if len(manuscript_content) > 4000:` (`modules/core/reference_anchor.py:52`)
- 호출자: `extract_anchors_from_manuscript()` (`modules/core/reference_anchor.py:40`)
- 상류/하류 컨텍스트:
- 상류: manuscript_content 타입 검증 없음.
- 하류: `None` 유입 시 `TypeError`.
- 판정: BUG.

3. 위험 지점
- 코드 원문: `error_info = ERROR_DEFINITIONS.get(error_code)` (`modules/core/error_helper.py:265`)
- 호출자: `ErrorHelper.print_error()`.
- 상류/하류 컨텍스트:
- 상류: 미등록 코드 입력 가능.
- 하류: fallback 로직은 존재하나 분류 품질 저하 가능.
- 판정: 안전(기본 fallback 존재).

### 5-C. 발견된 버그
### [HIGH] modules/core/pre_director_narrative_checker.py:340 — 경고 append 누락으로 설정 경고가 영구 누락

**문제**: `items.append(` 호출이 주석 뒤에 붙어 실행되지 않아, 조건 충족 시에도 WARNING이 기록되지 않는다.

**문제 코드**:
```python
if main_item and len(main_item) >= 2 and main_item not in first_section:
    # 주요 아이템이 초반에 언급되지 않음 - 경고만                items.append(
        CheckItem(
            category=CheckCategory.SETTING_KEYWORDS,
            name="주요 아이템 미언급기",
            passed=True,
            severity=CheckSeverity.WARNING,
            message=f"주요 아이템 '{main_item}'가 초반에 언급되지 않음",
        )
    )
```

**재현 근거**:
- 실행: `_check_setting_keywords(manuscript, {'owned_items':[{'name':'천검'}], ...})`
- 결과: WARNING 대신 `설정 일관성(PASS)`만 반환.

**호출 체인**: `modules/core/pre_director_checklist.py:403` → `modules/core/pre_director_checklist.py:425` → `modules/core/pre_director_narrative_checker.py:277` → `modules/core/pre_director_narrative_checker.py:340`

**수정 제안**:
```python
if main_item and len(main_item) >= 2 and main_item not in first_section:
    items.append(
        CheckItem(..., severity=CheckSeverity.WARNING, ...)
    )
```

**확신도**: HIGH

**FP 체크**: FP-2(Advisory) 비해당. 의도와 다르게 경고 자체가 생성되지 않음.

### [MEDIUM] modules/core/reference_anchor.py:52 — manuscript_content `None`에서 len() 크래시

**문제 코드**:
```python
if len(manuscript_content) > 4000:
    compressed = manuscript_content[:2000] + "\n\n...(중략)...\n\n" + manuscript_content[-2000:]
```

**재현 근거**:
- 실행: `ReferenceAnchor(ctx).extract_anchors_from_manuscript(1, None)`
- 결과: `TypeError: object of type 'NoneType' has no len()`

**호출 체인**: `modules/core/reference_anchor.py:40` → `modules/core/reference_anchor.py:52`

**수정 제안**:
```python
if not isinstance(manuscript_content, str):
    manuscript_content = ""
```

**확신도**: HIGH

**FP 체크**: FP-1~FP-10 비해당.

---
## Round 99 완료

## Round 100 — modules/core/self_reflection.py + modules/core/reflexion_manager.py + modules/core/repetition_guard.py + modules/core/primitive_guard.py + modules/core/escape_utils.py + modules/core/hud_utils.py + modules/core/arc_summary_utils.py + modules/core/logger.py + modules/core/spinners.py + modules/core/config_manager.py + modules/core/perf_timer.py

### 진행 통계 업데이트
- 총 발견: 97건 (CRITICAL: 0, HIGH: 68, MEDIUM: 29)
- 라운드 진행: 100/100

### 5-A. 파일 구조 요약
- `modules/core/self_reflection.py:51` `class SelfReflector` — self-critique / self-improve 루프.
- `modules/core/self_reflection.py:255` `reflect_and_improve(...) -> ReflectionResult`.
- `modules/core/reflexion_manager.py:12` `class ReflexionManager` — 실패 패턴 메모리 관리.
- `modules/core/repetition_guard.py:14` `class RepetitionGuard` — 반복 문구 탐지.
- `modules/core/primitive_guard.py:20` `class PrimitiveGuard` — 원시인 모드 금칙어/규칙.
- `modules/core/escape_utils.py:11` `class EscapeUtils` — braces/json escape 유틸.
- `modules/core/hud_utils.py:15` `build_hud_context(...) -> str`.
- `modules/core/arc_summary_utils.py:17` `generate_prev_arc_summary(...) -> str`.
- `modules/core/logger.py:32` `class StudioLogger`.
- `modules/core/spinners.py:102` `class StageSpinner`.
- `modules/core/config_manager.py:8` `class ConfigManager`.
- `modules/core/perf_timer.py:27` `class PerfTimer`.

### 5-D. 읽기 증명
1. 마지막 함수:
- `def quick_check(self, output: str, target: ReflectionTarget) -> dict[str, Any]` (`modules/core/self_reflection.py:298`)
- `def get_pattern_summary(self) -> str` (`modules/core/reflexion_manager.py:206`)
- `def update_detail(self, new_detail: str)` (`modules/core/spinners.py:268`)
- `def invalidate_settings_cache(self) -> None` (`modules/core/config_manager.py:163`)
- `def reset(self) -> None` (`modules/core/perf_timer.py:66`)
2. 특징 문자열:
- `logging.warning(f"[SelfReflector] LLM 호출 실패: {e}")` (`modules/core/self_reflection.py:174`)
- `feedback = f"[V60.96 CRITICAL] {genre}+원시인 모드 위반 {len(critical)}건:\n"` (`modules/core/primitive_guard.py:260`)
- `return "HUD 추세 정보 없음"` (`modules/core/hud_utils.py:263`)
3. import 목록:
- `from modules.core.constants import Stage2Limits` (`modules/core/arc_summary_utils.py:14`)
- `from modules.core.constants import ManuscriptLimits` (`modules/core/config_manager.py:5`)
- `import logging` (`modules/core/logger.py:14`)

### 5-B. 위험 지점 분석
1. 위험 지점
- 코드 원문: `changes = [issue.get("type", "unknown") for issue in issues]` (`modules/core/self_reflection.py:283`)
- 호출자: `reflect_and_improve()` (`modules/core/self_reflection.py:255`)
- 상류/하류 컨텍스트:
- 상류: `issues = critique.get("issues", [])` (`modules/core/self_reflection.py:275`)에서 요소 타입 검증 없음.
- 하류: list[str] 유입 시 `AttributeError`.
- 판정: BUG.

2. 위험 지점
- 코드 원문: `return self.settings["models"].get(agent_role, "gemini-2.5-flash")` (`modules/core/config_manager.py:64`)
- 호출자: `get_model_for_agent()`.
- 상류/하류 컨텍스트:
- 상류: `self.settings` 외부 변조 시 `"models"` 키 누락 가능.
- 하류: `KeyError` 가능.
- 판정: RISK (Design Check Needed).

3. 위험 지점
- 코드 원문: `if hasattr(context, "sys") and hasattr(context.sys, "hud"):` (`modules/core/hud_utils.py:258`)
- 호출자: `get_hud_trend_safe()`.
- 상류/하류 컨텍스트:
- 상류: broad `except Exception`로 상세 실패 원인 소실 (`modules/core/hud_utils.py:264`~`modules/core/hud_utils.py:265`).
- 하류: 운영 디버깅 시 원인 추적 어려움.
- 판정: RISK (Design Check Needed).

### 5-C. 발견된 버그
### [HIGH] modules/core/self_reflection.py:283 — `issues` 요소 타입 미검증으로 개선 루프 크래시

**문제 코드**:
```python
issues = critique.get("issues", [])
...
changes = [issue.get("type", "unknown") for issue in issues]
```

**재현 근거**:
- `reflect()`를 `{'severity':'high','issues':['x'],'overall_quality':3}` 반환으로 모킹 후 `reflect_and_improve(...)` 실행.
- 결과: `AttributeError: 'str' object has no attribute 'get'`

**호출 체인**: `modules/core/stage2_validation_pipeline.py:101` → `modules/core/self_reflection.py:255` → `modules/core/self_reflection.py:275` → `modules/core/self_reflection.py:283`

**수정 제안**:
```python
issues = critique.get("issues", [])
if not isinstance(issues, list):
    issues = []
issues = [i for i in issues if isinstance(i, dict)]
```

**확신도**: HIGH

**FP 체크**: FP-5 비해당. 파싱 후 스키마 정규화 누락.

---
## Round 100 완료

## 100라운드 오탐 재검증
- 재검증 범위: Round 91~100 신규 BUG 14건.
- 결과:
- 재현 성공: 14/14
- 오탐 전환: 0건
- 판정 변경:
- 없음.
- 재검증 메모:
- 설계 의도 가능 항목(비차단 로깅, advisory 성격)은 모두 RISK로 분리 유지.
- BUG 항목은 전부 런타임 예외 또는 의도 대비 동작 불일치(경고 누락)까지 확인.

## 자체 검증 결과
- [x] 5-A 빈 라운드: 0개 (Round 88~100 작성 완료)
- [x] 5-D 빈 라운드: 0개
- [x] 5-B 빈 라운드: 0개 (각 라운드 3개 이상 위험 지점 기록)
- [x] FP 체크 누락: 0개 (모든 BUG 항목에 FP 교차검증 기재)
- [x] 라인 번호 누락: 0개 (신규 Round 88~100 항목 기준)
- [x] 호출자 미기재: 0개 (호출 경로 또는 내부/직접 호출 여부 명시)
- [x] 총 위험 지점: 300개 이상 충족 (기존 누적 + Round 88~100 추가 반영)
