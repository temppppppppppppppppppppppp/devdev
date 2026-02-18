# Codex Order: 운영 품질 6대 개선 — 패치 추적 + Resume + 장기 품질 + 편향 감지 + 역방향 피드백 + 비용 추적

> **목표**: 패치 모드 효과 측정, 크래시 복구 보고, 장기 품질 추적, Director 편향 자가진단, Stage 4→2 역방향 피드백, LLM 비용 DB 기록
> **범위**: 12 파일 수정, ~400줄 추가, 테스트 ~15-20건 신규
> **위험도**: 낮음 (기존 로직 불변, 측정/보고/어드바이저리만 추가)
> **우선순위**: Phase 2(Resume) → Phase 3~6 순서

---

## 배경

패치 모드 확장(`dd825a8`) 완료 후, 시스템 운영 관점 빈틈 6개:

1. **패치 모드 결정은 하지만 결과를 추적 안 함** — 패치 vs 전면 재생성 중 어느 쪽이 나은지 데이터 없음
2. **장기 품질 추세 파악 불가** — QualityDashboard가 세션 내 추세만 봄 (100화+ 시리즈 대응 불가)
3. **Director 편향 자가진단 없음** — 특정 전략에 편향된 점수 배분 감지 불가
4. **Stage 4→2 역방향 피드백 없음** — Stage 3→2는 있으나, 원고 난이도 신호가 Arc 설계에 미전달
5. **크래시 후 재개 상태 보고 없음** — DB 기반 implicit resume는 이미 동작하지만, 사용자에게 현황 알림 없음
6. **LLM API 비용이 DB에 안 남음** — MetricsCollector가 세션 내 집계는 하지만 DB 미저장

---

## 진행 현황 (2026-02-17)

- [DONE] Phase 1(패치 추적) 코드 반영 완료
- [DONE] Stage 2/Stage 4/FourPhase/PassRateMonitor 연동 완료
- [DONE] 회귀 테스트 통과: `121 passed`
  - 실행: `pytest -q tests/test_stage2_finalizer.py tests/test_stage2_preflight.py tests/test_stage2_preflight_helpers.py tests/test_stage4_interview_round.py tests/test_arc_patch_mode.py tests/test_stage2_patch_integration.py tests/test_v55_modules.py`
- [DONE] Phase 2(Resume/Checkpoint) 반영 완료
  - `main_a.py`: `_show_resume_status()` 추가, Stage 2/3/4 진입 시 호출, shutdown 시 `pass_rate_monitor.save()` flush
  - `tests/test_resume_status.py` 신규 추가 (resume 로그/예외 비차단/shutdown 저장 비차단)
- [DONE] Phase 2 포함 회귀 테스트 통과: `125 passed`
  - 실행: `pytest -q tests/test_stage2_finalizer.py tests/test_stage2_preflight.py tests/test_stage2_preflight_helpers.py tests/test_stage4_interview_round.py tests/test_arc_patch_mode.py tests/test_stage2_patch_integration.py tests/test_v55_modules.py tests/test_resume_status.py`
- [DONE] Phase 3(장기 품질 추세) 반영 완료
  - `modules/core/quality_dashboard.py`: `get_windowed_quality_trend()`, `detect_quality_drift()` 추가
  - `tests/test_quality_trend.py` 신규 추가 (윈도우 집계/필터링/드리프트/데이터 부족)
- [DONE] Phase 3 포함 회귀 테스트 통과: `144 passed`
  - 실행: `pytest -q tests/test_stage2_finalizer.py tests/test_stage2_preflight.py tests/test_stage2_preflight_helpers.py tests/test_stage4_interview_round.py tests/test_arc_patch_mode.py tests/test_stage2_patch_integration.py tests/test_v55_modules.py tests/test_resume_status.py tests/test_quality_regression.py tests/test_quality_trend.py`
- [DONE] Phase 4(Director 편향 감지) 반영 완료
  - `modules/core/db_manager.py`: `get_selection_analysis()` 추가
  - `modules/core/quality_dashboard.py`: `detect_director_bias()` 추가
  - `main_a.py`: `_shutdown_app`에 Director 편향 advisory 출력 연결
  - `tests/test_director_bias.py` 신규 추가, `tests/test_selection_tracker.py` 보강
- [DONE] Phase 4 포함 회귀 테스트 통과: `158 passed`
  - 실행: `pytest -q tests/test_stage2_finalizer.py tests/test_stage2_preflight.py tests/test_stage2_preflight_helpers.py tests/test_stage4_interview_round.py tests/test_arc_patch_mode.py tests/test_stage2_patch_integration.py tests/test_v55_modules.py tests/test_resume_status.py tests/test_quality_regression.py tests/test_quality_trend.py tests/test_director_bias.py tests/test_selection_tracker.py`
- [DONE] Phase 5(Stage 4→2 역방향 피드백) 반영 완료
  - `modules/core/pass_rate_monitor.py`: `get_arc_difficulty()` 추가
  - `modules/core/feedback_system.py`: `generate_reverse_feedback_stage4_to_2()` 추가
  - `modules/core/stage2_context.py`: `generate_reverse_feedback_stage4_to_2` 콜백 슬롯/바인딩 추가
  - `main_a.py`: `_generate_reverse_feedback_stage4_to_2()` facade 추가
  - `modules/core/stage2_preflight.py`: `_preflight_arc_analysis()`에 Stage 4→2 피드백 주입 + `s4_to_s2_feedback` audit 이벤트 추가
  - `tests/test_arc_difficulty.py` 신규 추가, `tests/test_feedback_system.py`/`tests/test_stage2_context.py`/`tests/test_stage2_preflight_helpers.py` 보강
- [DONE] Phase 5 포함 회귀 테스트 통과: `235 passed`
  - 실행: `pytest -q tests/test_stage2_finalizer.py tests/test_stage2_preflight.py tests/test_stage2_preflight_helpers.py tests/test_stage4_interview_round.py tests/test_arc_patch_mode.py tests/test_stage2_patch_integration.py tests/test_v55_modules.py tests/test_resume_status.py tests/test_quality_regression.py tests/test_quality_trend.py tests/test_director_bias.py tests/test_selection_tracker.py tests/test_feedback_system.py tests/test_stage2_context.py tests/test_arc_difficulty.py`
- [DONE] Phase 6(비용 추적 DB) 반영 완료
  - `modules/core/db_manager.py`: `cost_log` 테이블 + `save_cost_record()` + `get_cost_summary()` 추가
  - `modules/core/metrics_collector.py`: 스코프 누적 + `snapshot_and_reset_scope()` 추가
  - `modules/core/stage2_finalizer.py`: Arc PASS 후 비용 스냅샷 DB 저장
  - `modules/core/stage4_post_processor.py`: Episode PASS 후 비용 스냅샷 DB 저장
  - `main_a.py`: `_shutdown_app`에서 session 잔여 비용 스냅샷 DB 저장
  - `tests/test_cost_tracking.py` 신규 추가, `tests/test_stage2_finalizer.py`/`tests/test_stage4_post_processor.py`/`tests/test_resume_status.py` 보강
- [DONE] Phase 6 포함 회귀 테스트 통과: `254 passed`
  - 실행: `pytest -q tests/test_stage2_finalizer.py tests/test_stage2_preflight.py tests/test_stage2_preflight_helpers.py tests/test_stage4_interview_round.py tests/test_arc_patch_mode.py tests/test_stage2_patch_integration.py tests/test_v55_modules.py tests/test_resume_status.py tests/test_quality_regression.py tests/test_quality_trend.py tests/test_director_bias.py tests/test_selection_tracker.py tests/test_feedback_system.py tests/test_stage2_context.py tests/test_arc_difficulty.py tests/test_cost_tracking.py tests/test_stage4_post_processor.py`
- [NEXT] 운영 검증(실프로젝트 1회) 후 비용 대시보드 연동

### Phase 1 실제 반영 포인트

- `modules/core/pass_rate_monitor.py`
  - `AttemptRecord`에 `is_patch`, `prev_score`, `patch_fallback` 추가
  - `record_attempt()` 확장 및 `get_patch_effectiveness()` 추가
- `modules/core/stage2_preflight.py`
  - `_preflight_enrichment()` 반환값에 `was_patch`, `patch_fallback`, `prev_score` 추가
  - `stage2_patch_mode` audit 이벤트 추가
- `modules/core/stage2_orchestrator.py`
  - preflight patch 메타 수신 후 finalizer로 전달
- `modules/core/stage2_finalizer.py`
  - `run_finalize()` 및 Stage2 pass/reject metrics에 patch 메타 전달
- `modules/core/stage4_interview_round.py`
  - `selection_reason`에 `[patch|score=...]` / `[patch-fallback|score=...]` 태그 기록
- `modules/domain/agents/four_phase_arc_generator.py`
  - `pipeline_result`에 `patch_used`, `patch_fallback` 표준 필드 추가
- `tests/test_stage2_preflight_helpers.py`
  - `_preflight_enrichment` 기대 키셋 업데이트

### 바로 다음 작업 (Phase 2)

- `main_a.py`
  - `_show_resume_status()` 추가
  - `_shutdown_app`에서 `pass_rate_monitor.save()` flush 추가
  - Stage 2/3/4 진입 시 resume 상태 출력 연결
- 테스트
  - `tests/test_resume_status.py` 신규 추가
  - Stage 진입 로그/저장 실패 비차단 동작 검증

---

## 대원칙

- **기존 로직 불변**: 생성·검증·심사 흐름 변경 0건
- **비차단**: 모든 추적/보고가 실패해도 메인 파이프라인 영향 없음 (`try/except` 감싸기)
- **역호환**: 기존 JSON 파일 (pass_rate_monitor.json 등) 로드 시 새 필드 default값으로 동작

---

## Phase 1: 패치 모드 효과 추적 (완료: 2026-02-17)

### 1-A: AttemptRecord 확장

**파일**: `modules/core/pass_rate_monitor.py` (`AttemptRecord` 정의 블록)

**현재:**
```python
@dataclass
class AttemptRecord:
    timestamp: str
    stage: int
    episode: int
    arc: int
    attempt_num: int
    success: bool
    reject_reason: str = ""
    generation_method: str = "default"
    model_tier: int = 1
    duration_ms: int = 0
    token_cost: float = 0.0
```

**변경 (3 필드 추가):**
```python
@dataclass
class AttemptRecord:
    timestamp: str
    stage: int
    episode: int
    arc: int
    attempt_num: int
    success: bool
    reject_reason: str = ""
    generation_method: str = "default"
    model_tier: int = 1
    duration_ms: int = 0
    token_cost: float = 0.0
    is_patch: bool = False          # 패치 시도 여부
    prev_score: int = 0             # 패치 대상의 이전 점수 (0이면 비패치)
    patch_fallback: bool = False    # 패치 실패 → 전면 재생성 폴백
```

모두 default값 → 기존 JSON 역호환.

---

### 1-B: Stage 4 패치 태깅

**파일**: `modules/core/stage4_interview_round.py`

#### 1-B-1: 패치 결정 시점 태깅 (패치 분기 `else:` 블록)

**현재 (`_use_patch` 계산 구간):**
```python
_prev_score = previous_attempt.get("score", 0) if previous_attempt else 0
_prev_manuscript = previous_attempt.get("best_manuscript", "") if previous_attempt else ""
_use_patch = _prev_score >= _PATCH_REWRITE_THRESHOLD and _prev_manuscript
```

**직후에 추가:**
```python
_is_patch = _use_patch
_is_patch_fallback = False
```

#### 1-B-2: 패치 실패 폴백 태깅 (패치 실패 폴백 분기)

**현재 (패치 실패 시 분기):**
```python
if not candidates:
    logging.info("[Phase 3-5B] 패치 실패, full rewrite 폴백")
    self.ctx.ui.log("   ⚠️ [Phase 3-5B] 패치 실패 → 전면 재작성 폴백")
```

**직후에 추가:**
```python
    _is_patch_fallback = True
```

#### 1-B-3: director_selection 저장 시 태그 (director_selection 저장 블록)

**현재 (`save_director_selection` 호출부):**
```python
selection_reason=reason,
```

**변경 (`save_director_selection` 호출 블록 전체):**
```python
try:
    _sel_candidate = director_result.get("selected_candidate", {})
    if not isinstance(_sel_candidate, dict):
        _sel_candidate = {}
    _sel_strategy = _sel_candidate.get("strategy_name", "") or _sel_candidate.get("strategy", "")
    # [Item1] 패치 모드 태그 추가
    _patch_tag = ""
    if round_num > 0:
        if _is_patch:
            _patch_tag = f" [PATCH:prev={_prev_score}]"
            if _is_patch_fallback:
                _patch_tag = f" [PATCH_FALLBACK:prev={_prev_score}]"
        else:
            _patch_tag = f" [REGEN:prev={_prev_score}]"
    self.ctx.current_project.db.save_director_selection(
        ep_num=next_ep,
        round_num=round_num,
        selected_label=selected,
        selected_strategy=_sel_strategy,
        verdict=verdict,
        score=score,
        selection_reason=reason + _patch_tag,
        candidate_count=len(candidates) if candidates else 0,
    )
except Exception as e:
    logging.warning(f"[D-4] Director 선택 기록 실패 (비차단): {e!s:.100}")
```

**주의**: `_is_patch`, `_is_patch_fallback`, `_prev_score` 변수는 round_num==0일 때 정의 안 됨.
→ round_num==0 분기(초기 분기 블록)에서 `_is_patch = False`, `_is_patch_fallback = False`, `_prev_score = 0` 초기화 필요.
→ 메서드 시작부에 기본값 선언:
```python
_is_patch = False
_is_patch_fallback = False
_prev_score = 0
```

---

### 1-C: Stage 2 패치 태깅

#### 1-C-1: preflight_enrichment 반환 dict 확장

**파일**: `modules/core/stage2_preflight.py`

`_preflight_enrichment()` 반환 dict에 2 키 추가:

```python
return {
    "four_phase_passed": ...,
    "refined_arc": ...,
    "generation_method": ...,
    "draft_validator_passed": ...,
    "consensus_passed": ...,
    "st_snapshot": ...,
    "director_feedback_for_fourphase": ...,
    "was_patch": bool(_use_patch),              # 추가
    "patch_fallback": _use_patch and not refined_arc,  # 추가 (패치 시도했으나 실패)
}
```

**주의**: `_use_patch` 변수는 해당 함수 내 패치 모드 분기에서 설정됨. `refined_arc`가 None이면 패치 실패.
패치 미사용 시 `_use_patch = False` 이므로 `was_patch=False`, `patch_fallback=False`.

#### 1-C-2: orchestrator에서 언패킹

**파일**: `modules/core/stage2_orchestrator.py`

**현재:**
```python
four_phase_passed = _enrichment["four_phase_passed"]
refined_arc = _enrichment["refined_arc"]
generation_method = _enrichment["generation_method"]
draft_validator_passed = _enrichment["draft_validator_passed"]
consensus_passed = _enrichment["consensus_passed"]
_st_snapshot = _enrichment["st_snapshot"]
director_feedback_for_fourphase = _enrichment["director_feedback_for_fourphase"]
```

**추가 (언패킹 직후):**
```python
_was_patch = _enrichment.get("was_patch", False)
_patch_fallback = _enrichment.get("patch_fallback", False)
```

#### 1-C-3: finalizer에 패치 정보 전달

**파일**: `modules/core/stage2_orchestrator.py` (`run_finalize()` 호출부)

`run_finalize()` 호출에 3 키워드 추가:
```python
_fin = await self.finalizer.run_finalize(
    ...,
    is_patch=_was_patch,
    prev_score=_previous_attempt.get("score", 0) if _previous_attempt else 0,
    patch_fallback=_patch_fallback,
)
```

#### 1-C-4: finalizer metrics 시그니처 확장

**파일**: `modules/core/stage2_finalizer.py`

`run_finalize()` 시그니처에 3 파라미터 추가:
```python
async def run_finalize(
    self,
    ...,
    is_patch: bool = False,
    prev_score: int = 0,
    patch_fallback: bool = False,
) -> dict:
```

`_record_s2_pass_metrics()` / `_record_s2_reject_metrics()` 시그니처에도 동일 3 파라미터 추가.

`record_attempt()` 호출부(Stage 2 PASS/REJECT metrics 기록 지점)에 전달:
```python
self.ctx.pass_rate_monitor.record_attempt(
    ...,
    is_patch=is_patch,
    prev_score=prev_score,
    patch_fallback=patch_fallback,
)
```

---

### 1-D: FourPhase 내부 패치 플래그

**파일**: `modules/domain/agents/four_phase_arc_generator.py`

패치 성공 시 (`patch_arc_with_feedback` 성공 후):
```python
pipeline_result["patch_used"] = True
```

패치 미사용 / 실패 시:
```python
pipeline_result.setdefault("patch_used", False)
```

호출자(stage2_preflight.py)에서 `audit_event`로 기록:
```python
if _enrichment_result.get("patch_used"):
    self.ctx.audit_event("fourphase_internal_patch", "FourPhase 내부 패치 성공", {"arc_no": global_arc_no})
```

---

### 1-E: 효과 분석 메서드

**파일**: `modules/core/pass_rate_monitor.py` — 신규 메서드

```python
def get_patch_effectiveness(self, stage: int | None = None, recent_n: int = 200) -> dict:
    """패치 vs 전면 재생성 효과 비교.

    Returns:
        {
            "patch_attempts": int,
            "patch_success_rate": float,  # 패치 시도 중 PASS 비율
            "regen_attempts": int,        # 재시도 중 전면 재생성 횟수
            "regen_success_rate": float,
            "patch_fallback_rate": float, # 패치 시도 중 폴백 비율
        }
    """
    records = self.records[-recent_n:] if recent_n else self.records
    if stage is not None:
        records = [r for r in records if r.stage == stage]

    patch_recs = [r for r in records if r.is_patch]
    regen_recs = [r for r in records if not r.is_patch and r.attempt_num > 1]

    patch_success = sum(1 for r in patch_recs if r.success)
    regen_success = sum(1 for r in regen_recs if r.success)
    fallback_count = sum(1 for r in patch_recs if r.patch_fallback)

    return {
        "patch_attempts": len(patch_recs),
        "patch_success_rate": round(patch_success / max(len(patch_recs), 1), 3),
        "regen_attempts": len(regen_recs),
        "regen_success_rate": round(regen_success / max(len(regen_recs), 1), 3),
        "patch_fallback_rate": round(fallback_count / max(len(patch_recs), 1), 3),
    }
```

---

## Phase 2: Resume/Checkpoint (TOP PRIORITY)

### 핵심 발견

- Stage 2/3/4 모두 **이미 per-item DB 저장** → implicit resume 동작
- 실제 갭: ① 사용자에게 현황 미보고 ② shutdown 시 PassRateMonitor 미저장

### 2-A: PassRateMonitor shutdown 저장

**파일**: `main_a.py` (`_shutdown_app` 내 `failure_learner` 저장 직전)

```python
# [Item5] PassRateMonitor 저장
if V50_MODULES_AVAILABLE and hasattr(self, 'pass_rate_monitor') and self.pass_rate_monitor:
    try:
        self.pass_rate_monitor.save()
        print(f"📈 [PassRate] 통과율 기록 저장: {len(self.pass_rate_monitor.records)}건", flush=True)
    except Exception as pr_err:
        print(f"⚠️ [PassRate] 저장 실패: {pr_err}", flush=True)
```

### 2-B: Resume 상태 보고 메서드

**파일**: `main_a.py` — `SovereignApp` 클래스 내 신규 메서드

```python
def _show_resume_status(self):
    """프로젝트 진행 현황 출력 (크래시 후 재시작 대응)."""
    if not self.current_project or not hasattr(self.current_project, "db"):
        return
    try:
        arcs = self.current_project.db.load_anchor("arcs") or []
        bp_max = self.current_project.db.get_latest_blueprint_number()
        ms_max = self.current_project.get_latest_episode_number() - 1
        total_eps = sum(a.get("ep_count", 0) for a in arcs) if arcs else 0

        self.ui.log("─" * 50)
        self.ui.log(f"📋 [Resume] 프로젝트: {self.current_project.name}")
        self.ui.log(f"   Arc 설계: {len(arcs)}개 완료")
        self.ui.log(f"   Blueprint: ep {bp_max}까지 완료")
        self.ui.log(f"   원고: ep {ms_max}까지 완료")
        if total_eps > 0:
            self.ui.log(f"   예상 총 에피소드: {total_eps}")
        self.ui.log("─" * 50)
    except Exception as e:
        logging.warning(f"[Resume] 상태 보고 실패: {e}")
```

### 2-C: Stage 진입 시 호출

각 Stage 진입 메서드 상단에 `self._show_resume_status()` 1줄 추가:

- `_stage_2_arcs()` 상단
- `_stage_3_batch_blueprinting()` 상단
- `_stage_4_v2_chief_writer()` 상단

---

## Phase 3: 장기 품질 추세 (Item 2)

**파일**: `modules/core/quality_dashboard.py` — 신규 메서드 2개

### 3-A: 윈도우 품질 추세

```python
def get_windowed_quality_trend(self, window_size: int = 10, stage: int = 4) -> list[dict]:
    """N 에피소드 윈도우별 평균 점수·통과율.

    Returns:
        [{"window": "ep1-10", "avg_score": 75.2, "pass_rate": 0.8, "count": 10}, ...]
    """
    scored = [r for r in self.validation_history
              if r.get("stage") == stage and isinstance(r.get("score"), (int, float)) and r["score"] > 0]
    if not scored:
        return []

    windows = []
    for i in range(0, len(scored), window_size):
        chunk = scored[i:i + window_size]
        scores = [r["score"] for r in chunk]
        passes = sum(1 for r in chunk if r.get("decision") == "PASS")
        ep_start = chunk[0].get("ep_num", "?")
        ep_end = chunk[-1].get("ep_num", "?")
        windows.append({
            "window": f"ep{ep_start}-{ep_end}",
            "avg_score": round(sum(scores) / len(scores), 1),
            "pass_rate": round(passes / len(chunk), 2),
            "count": len(chunk),
        })
    return windows
```

### 3-B: 품질 드리프트 감지

```python
def detect_quality_drift(self, stage: int = 4, min_windows: int = 3) -> dict:
    """연속 윈도우 점수 하락(드리프트) 감지.

    Returns:
        {"drift": "declining"|"stable"|"improving"|"insufficient_data",
         "recent_avg": float, "overall_avg": float, "windows": int}
    """
    windows = self.get_windowed_quality_trend(stage=stage)
    if len(windows) < min_windows:
        return {"drift": "insufficient_data", "windows": len(windows)}

    recent = [w["avg_score"] for w in windows[-min_windows:]]
    overall_avg = sum(w["avg_score"] for w in windows) / len(windows)
    is_declining = all(recent[i] > recent[i + 1] for i in range(len(recent) - 1))
    is_improving = all(recent[i] < recent[i + 1] for i in range(len(recent) - 1))

    drift = "declining" if is_declining else ("improving" if is_improving else "stable")
    return {
        "drift": drift,
        "recent_avg": round(recent[-1], 1),
        "overall_avg": round(overall_avg, 1),
        "windows": len(windows),
    }
```

### 3-C: 통합

- `_shutdown_app`에서 드리프트 결과 출력 (~5줄, advisory)

---

## Phase 4: Director 편향 감지 (Item 3)

### 4-A: DB 쿼리

**파일**: `modules/core/db_manager.py` — 신규 메서드

```python
def get_selection_analysis(self, lookback: int = 100) -> list[dict]:
    """최근 Director 선택 기록 조회 (편향 분석용)."""
    with self._lock:
        cur = self.cursor.execute(
            "SELECT selected_strategy, verdict, score, selection_reason "
            "FROM director_selections ORDER BY id DESC LIMIT ?",
            (lookback,),
        )
        return [dict(row) for row in cur.fetchall()]
```

### 4-B: 편향 분석

**파일**: `modules/core/quality_dashboard.py` — 신규 메서드

```python
def detect_director_bias(self, selections: list[dict]) -> dict:
    """전략별 점수 분포 분석 + 편향 경고 생성.

    Returns:
        {
            "strategy_stats": {"balanced": {"avg_score": 75, "pass_rate": 0.85, "count": 20}, ...},
            "bias_warnings": ["전략 X가 항상 80+ (편향 가능성)", ...],
        }
    """
    from collections import defaultdict

    by_strategy = defaultdict(list)
    for s in selections:
        strategy = s.get("selected_strategy") or "unknown"
        by_strategy[strategy].append(s)

    stats = {}
    warnings = []
    for strategy, recs in by_strategy.items():
        scores = [r["score"] for r in recs if isinstance(r.get("score"), (int, float))]
        passes = sum(1 for r in recs if r.get("verdict") == "PASS")
        avg = sum(scores) / max(len(scores), 1)
        stats[strategy] = {
            "avg_score": round(avg, 1),
            "pass_rate": round(passes / max(len(recs), 1), 2),
            "count": len(recs),
        }
        if len(scores) >= 10 and avg > 80:
            warnings.append(f"전략 '{strategy}' 평균 {avg:.0f}점 — 편향 가능성")
        if len(scores) >= 10 and avg < 40:
            warnings.append(f"전략 '{strategy}' 평균 {avg:.0f}점 — 과소평가 가능성")

    return {"strategy_stats": dict(stats), "bias_warnings": warnings}
```

### 4-C: 통합

- `_shutdown_app`에서 편향 경고 출력 (~10줄, advisory)

---

## Phase 5: Stage 4→2 역방향 피드백 (Item 4)

### 5-A: Arc 난이도 측정

**파일**: `modules/core/pass_rate_monitor.py` — 신규 메서드

```python
def get_arc_difficulty(self, arc_no: int) -> dict:
    """Arc별 난이도: 해당 Arc 에피소드들의 평균 시도 횟수.

    Returns:
        {"arc_no": int, "difficulty": "easy"|"normal"|"hard"|"unknown",
         "avg_attempts": float, "hard_episodes": list[int]}
    """
    arc_records = [r for r in self.records if r.arc == arc_no and r.stage == 4]
    episodes: dict[int, list[AttemptRecord]] = {}
    for r in arc_records:
        episodes.setdefault(r.episode, []).append(r)

    if not episodes:
        return {"arc_no": arc_no, "difficulty": "unknown", "avg_attempts": 0, "hard_episodes": []}

    attempts_per_ep = []
    hard_eps = []
    for ep, recs in sorted(episodes.items()):
        n = len(recs)
        attempts_per_ep.append(n)
        if n >= 3:
            hard_eps.append(ep)

    avg = sum(attempts_per_ep) / len(attempts_per_ep)
    difficulty = "easy" if avg <= 1.5 else ("normal" if avg <= 3 else "hard")

    return {
        "arc_no": arc_no,
        "difficulty": difficulty,
        "avg_attempts": round(avg, 1),
        "hard_episodes": hard_eps,
    }
```

### 5-B: 역방향 피드백 생성

**파일**: `modules/core/feedback_system.py` — 기존 `generate_reverse_feedback_stage3_to_2()` 아래에 추가

```python
def generate_reverse_feedback_stage4_to_2(self, arc_difficulty: dict) -> str:
    """[Item4] Arc 난이도가 'hard'이면 다음 Arc 설계 시 난이도 경고 주입."""
    if arc_difficulty.get("difficulty") != "hard":
        return ""

    avg = arc_difficulty.get("avg_attempts", 0)
    hard_eps = arc_difficulty.get("hard_episodes", [])
    lines = [
        f"[Stage 4→2 역방향 피드백] 이전 Arc(#{arc_difficulty['arc_no']}) 집필 난이도 높음",
        f"  평균 {avg}회 시도 필요 (hard_episodes: {hard_eps})",
        "  → 다음 Arc 설계 시 씬 구조를 단순화하고 집필 난이도를 낮추세요.",
        "  → 복잡한 다중 NPC 동시 등장, 비선형 시간 전개를 최소화하세요.",
    ]
    return "\n".join(lines)
```

### 5-C: 주입 통합

**파일**: `modules/core/stage2_preflight.py` (기존 stage3→2 역방향 피드백 블록 아래)

```python
# [Item4] Stage 4→2 역방향 피드백 주입
if global_arc_no > 1 and self.ctx.pass_rate_monitor:
    try:
        _prev_difficulty = self.ctx.pass_rate_monitor.get_arc_difficulty(global_arc_no - 1)
        _s4_feedback = self.ctx.generate_reverse_feedback_stage4_to_2(_prev_difficulty)
        if _s4_feedback:
            constraint_block += f"\n\n{_s4_feedback}"
            self.ctx.audit_event("s4_to_s2_feedback", "Arc difficulty feedback injected",
                                 {"arc_no": global_arc_no, "prev_difficulty": _prev_difficulty})
    except Exception as e:
        logging.warning(f"[Item4] Stage 4→2 피드백 실패: {e}")
```

**참고**: `generate_reverse_feedback_stage4_to_2`를 Stage2Context에 콜백으로 등록해야 함.
→ `modules/core/stage2_context.py`에 `generate_reverse_feedback_stage4_to_2` 슬롯 추가
→ `main_a.py`의 `Stage2Context.from_app()`에서 콜백 바인딩

---

## Phase 6: 비용 추적 DB (Item 6)

### 6-A: cost_log 테이블

**파일**: `modules/core/db_manager.py` `_boot_db` 내 (마지막 CREATE TABLE 이후)

```sql
CREATE TABLE IF NOT EXISTS cost_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    scope_type TEXT NOT NULL CHECK(scope_type IN ('arc', 'episode', 'session')),
    scope_id INTEGER DEFAULT 0,
    total_calls INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost_usd REAL DEFAULT 0.0,
    model_breakdown TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### 6-B: CRUD 메서드

**파일**: `modules/core/db_manager.py` — 신규

```python
def save_cost_record(self, *, session_id: str, scope_type: str, scope_id: int = 0,
                     total_calls: int = 0, total_tokens: int = 0, total_cost_usd: float = 0.0,
                     model_breakdown: str = "{}") -> None:
    """비용 기록 저장."""
    with self._lock:
        self.cursor.execute(
            "INSERT INTO cost_log (session_id, scope_type, scope_id, total_calls, "
            "total_tokens, total_cost_usd, model_breakdown) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (session_id, scope_type, scope_id, total_calls, total_tokens, total_cost_usd, model_breakdown),
        )
        self.conn.commit()

def get_cost_summary(self, scope_type: str | None = None, lookback: int = 50) -> list[dict]:
    """비용 요약 조회."""
    with self._lock:
        if scope_type:
            cur = self.cursor.execute(
                "SELECT * FROM cost_log WHERE scope_type = ? ORDER BY id DESC LIMIT ?",
                (scope_type, lookback),
            )
        else:
            cur = self.cursor.execute(
                "SELECT * FROM cost_log ORDER BY id DESC LIMIT ?", (lookback,),
            )
        return [dict(row) for row in cur.fetchall()]
```

### 6-C: MetricsCollector 스코프 스냅샷

**파일**: `modules/core/metrics_collector.py` — 신규 메서드

```python
def snapshot_and_reset_scope(self) -> dict:
    """현재 스코프 집계 반환 후 스코프 카운터 리셋."""
    summary = {
        "calls": self._scope_calls,
        "tokens": self._scope_tokens,
        "cost_usd": round(self._scope_cost, 4),
        "model_breakdown": dict(self._scope_model_breakdown),
    }
    self._scope_calls = 0
    self._scope_tokens = 0
    self._scope_cost = 0.0
    self._scope_model_breakdown = defaultdict(lambda: {"tokens": 0, "cost": 0.0})
    return summary
```

**주의**: `_scope_*` 필드는 `__init__`에서 초기화 필요:
```python
self._scope_calls = 0
self._scope_tokens = 0
self._scope_cost = 0.0
self._scope_model_breakdown = defaultdict(lambda: {"tokens": 0, "cost": 0.0})
```

기존 `end_call()` 메서드에서 session 집계와 별도로 scope 집계도 누적:
```python
self._scope_calls += 1
self._scope_tokens += input_tokens + output_tokens
self._scope_cost += cost
self._scope_model_breakdown[model]["tokens"] += input_tokens + output_tokens
self._scope_model_breakdown[model]["cost"] += cost
```

### 6-D: 통합

- Stage 2 finalizer (`stage2_finalizer.py`): Arc PASS 후
  ```python
  collector = get_metrics_collector()
  if collector and self.ctx.current_project:
      scope = collector.snapshot_and_reset_scope()
      self.ctx.current_project.db.save_cost_record(
          session_id=collector.session_id, scope_type="arc",
          scope_id=global_arc_no, **scope,
      )
  ```
- Stage 4 post_processor (`stage4_post_processor.py`): Episode PASS 후 — 동일 패턴
- `_shutdown_app` (`main_a.py`): Session 종료 시 — 동일 패턴 (scope_type="session")

---

## 수정 파일 총괄

| Phase | 파일 | 변경 | 규모 |
|-------|------|------|------|
| 1 | `pass_rate_monitor.py` | AttemptRecord 3필드 + `get_patch_effectiveness()` | +50줄 |
| 1 | `stage4_interview_round.py` | 패치 태깅 + selection_reason 태그 | +15줄 |
| 1 | `stage2_finalizer.py` | metrics 시그니처 확장 + 전달 | +15줄 |
| 1 | `stage2_preflight.py` | 반환 dict was_patch/patch_fallback | +8줄 |
| 1 | `stage2_orchestrator.py` | 언패킹 + finalizer 전달 | +8줄 |
| 1 | `four_phase_arc_generator.py` | pipeline_result patch_used 플래그 | +5줄 |
| 2 | `main_a.py` | shutdown 저장 + resume 상태 + Stage 호출 | +30줄 |
| 3 | `quality_dashboard.py` | 윈도우 추세 + 드리프트 감지 | +60줄 |
| 4 | `db_manager.py` | selection_analysis 쿼리 | +15줄 |
| 4 | `quality_dashboard.py` | 편향 분석 | +50줄 |
| 5 | `pass_rate_monitor.py` | arc_difficulty 메서드 | +30줄 |
| 5 | `feedback_system.py` | stage4→2 역방향 피드백 | +30줄 |
| 5 | `stage2_preflight.py` | 역방향 피드백 주입 | +10줄 |
| 5 | `stage2_context.py` | 콜백 슬롯 추가 | +3줄 |
| 6 | `db_manager.py` | cost_log 테이블 + CRUD | +40줄 |
| 6 | `metrics_collector.py` | 스코프 스냅샷 + 누적 | +30줄 |
| 6 | `stage2_finalizer.py` | arc 비용 기록 | +5줄 |
| 6 | `stage4_post_processor.py` | episode 비용 기록 | +5줄 |
| | **합계** | **12 파일** | **~400줄** |

---

## 테스트

### 신규 테스트 파일

| 파일 | 테스트 수 | 내용 |
|------|-----------|------|
| `tests/test_patch_tracking.py` | 5건 | AttemptRecord 직렬화/역호환, get_patch_effectiveness() |
| `tests/test_resume_status.py` | 3건 | _show_resume_status() mock DB, shutdown 저장 |
| `tests/test_quality_trend.py` | 4건 | get_windowed_quality_trend(), detect_quality_drift() |
| `tests/test_director_bias.py` | 3건 | detect_director_bias() |
| `tests/test_cost_tracking.py` | 3건 | save_cost_record(), get_cost_summary(), snapshot_and_reset_scope() |
| **합계** | **~18건** | |

### 검증 순서

1. (PowerShell) `$env:PYTHONIOENCODING='utf-8'; python -m pytest tests/ -q` — 전체 테스트 통과
2. (bash/zsh) `PYTHONIOENCODING=utf-8 python -m pytest tests/ -q` — 동일 검증
3. 기존 `pass_rate_monitor.json` 역호환 확인 (새 필드 default값)
4. `python -m ruff check modules/ tests/ --quiet` — 0 violations
5. 각 Phase 완료 후 중간 테스트 실행
