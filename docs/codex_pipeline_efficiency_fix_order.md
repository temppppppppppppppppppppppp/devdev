# Codex 오더: 파이프라인 효율성 수정

> Dead Config 6건 + Information Bottleneck 6건 + Broken Wiring 모듈 연결 + 미사용 정리
> Phase 1 → 2 → 3 → 4 → 5 순차 실행. 각 Phase 후 테스트.
> **코드를 수정합니다.**

---

## 배경

`docs/파이프라인_효율성_감사_결과.md` 감사 결과 22건 확인:
- Dead Config 4건 + 추가 2건: 설정은 있는데 안 읽힘
- Information Bottleneck 6건: 데이터가 경로 중간에 축소
- Broken Wiring 12건: 구현됐는데 호출 안 됨

감사 결과를 기반으로 수정 + 미연결 모듈 8개 파이프라인 연결.

---

## 대원칙

1. **Director 주권 유지**: 모듈이 REJECT할 수 있으나 ACCEPT는 Director만
2. **Python 감지 → LLM 판단**: 새 모듈은 Python 사전검사 → LLM은 기존 Director가 담당
3. **비차단 갱신**: 새 모듈 실패 시 기존 경로 fallback (파이프라인 중단 금지)
4. **기존 테스트 불변**: 2100 passed + 68 xfailed 유지
5. **기존 반환 계약 유지**: `process_pass_result()` → `bool`, Director ensemble → variable candidate count OK
6. **Enum 비교 사용**: ComplianceLevel, ConfidenceLevel 등은 Enum — `.name ==` 대신 `== Enum.VALUE` 비교

---

## 패치 모드 상호작용 규칙

### 현재 패치 모드 동작
```
Director REJECT → score/best_manuscript 저장 → 다음 라운드
→ score ≥ 50 + best_manuscript 존재 → 패치 모드 진입
→ score < 50 → 전면 재작성
```
핵심 변수: `score` (Director 부여), `verdict`, `best_manuscript`

### 새 모듈과 패치 모드의 관계

| 모듈 | 패치 분기 영향 | 이유 |
|------|--------------|------|
| PreDirectorChecklist | **없음** | warnings 추가만, score/verdict 불변 |
| ConfidenceCalibrator | **없음** | warnings 추가만, Director가 score 부여 |
| CrossAgentVerifier | **없음** | warnings 추가만, Director가 score 부여 |
| DynamicPromptWeighter | **간접** | 원고 품질 향상 → Director score 상승 가능 |
| ChainOfVerification | **없음** | Score ≥ 90 PASS 후 실행 → REJECT 루프 외부 |
| ASP (교정) | **간접** | 수정안 → Director 재심사 → score로 패치 판단 |

### 필수 규칙

1. **모듈은 score를 변경하지 않는다**: score는 반드시 Director가 부여.
2. **Score 90 Gate**: Director PASS + score < 90 → REJECT 전환 → 패치 모드 (score ≥ 50).
3. **ASP 수정안은 후보 추가**: candidates에 추가 → Director가 재심사. REJECT 시 score ≥ 50이면 패치.
4. **CoVe**: Score ≥ 90 통과 후에만 실행. CoVe 실패 시 재작성 루프 재진입 → 이전 score로 패치 판단.
5. **5회 소진**: 자동 진행 안 함. 사용자 대기.
6. **패치 모드 비활성화 시**: `enable_patch_mode=false` → 항상 전면 재작성.

---

## Phase 1: Dead Config 정리 (6건)

### 1-1. `manuscript.*` YAML 키 → `_threshold()` 연결

**파일**: `modules/core/constants.py`

현재 `ManuscriptLimits` 클래스가 하드코딩 상수:
```python
class ManuscriptLimits:
    MIN_LENGTH = 4000
    WARNING_LENGTH = 4500
    TARGET_LENGTH = 5000
    MAX_LENGTH = 15000
```

수정: `_threshold()` 소비로 전환하여 `validation.yaml` manuscript 섹션과 연결.

```python
from modules.validation.threshold_helper import _threshold

class ManuscriptLimits:
    MIN_LENGTH = _threshold("manuscript.min_length", 4000)
    WARNING_LENGTH = _threshold("manuscript.warning_length", 4500)
    TARGET_LENGTH = _threshold("manuscript.target_length", 5000)
    MAX_LENGTH = _threshold("manuscript.max_length", 15000)
```

**주의**: `_threshold()`는 모듈 로드 시 1회만 평가됨. 클래스 속성이므로 기존 `ManuscriptLimits.MIN_LENGTH` 참조 31곳은 변경 불필요.

**circular import 검증 완료**: `constants.py` → `threshold_helper.py` → `config_manager.py` → `constants.py` 경로가 의심되나, 실제로 `constants.py`는 stdlib(`logging`)만 import하고 커스텀 모듈 import 없음. 순환 의존 위험 0. 직접 대입 방식 사용.

### 1-2. `use_parallel_validation` 삭제

**파일**: `modules/validation/validation_orchestrator.py`

```python
# 삭제할 줄 (L194 부근):
self.use_parallel_validation = config.get("use_parallel_validation", True)
```

한 줄 삭제. 다른 곳에서 참조 없음 (확인 완료).

### 1-3. `enable_cascade`, `self.cascade` 삭제

**파일**: `modules/domain/agents/base_agent.py`

```python
# L210 __init__ 시그니처에서 enable_cascade=False 파라미터 제거
# L222-223 삭제:
self.enable_cascade = enable_cascade
self.cascade = None
```

**사전 확인**: `enable_cascade`를 전달하는 호출 측이 있는지 grep 확인. 없으면 안전 삭제.

### 1-4. 미사용 프롬프트 YAML 5개 삭제

```
config/prompts/chain_of_verification.yaml
config/prompts/tree_of_thoughts.yaml
config/prompts/multi_agent_deliberation.yaml
config/prompts/adversarial_self_play.yaml
config/prompts/cross_agent_verifier.yaml
```

해당 5개 .yaml 파일 삭제. 대응 Python 모듈은 클래스 레벨 하드코딩 프롬프트 사용 중 (YAML 미참조 확인됨).

**주의**: `config/prompts/director_auditor.yaml`은 삭제 금지 — `director_auditor.py` L640, L761에서 `PromptLoader`로 능동 로딩 중.

### 1-5. `patch_mode.*` YAML 키 → `_threshold()` 연결

**파일 1**: `modules/core/constants.py` (L532-536 부근)

현재 `PatchModeThresholds` 하드코딩:
```python
class PatchModeThresholds:
    REWRITE = 50   # 미만: 전면 재작성
    PATCH = 80     # 50~80: 부분 수정
```

`validation.yaml`에 이미 존재하는 키:
```yaml
patch_mode:
  rewrite_below: 50
  patch_below: 80
```

수정: `_threshold()` 소비로 전환.
```python
class PatchModeThresholds:
    REWRITE = _threshold("patch_mode.rewrite_below", 50)
    PATCH = _threshold("patch_mode.patch_below", 80)
```

**참고**: 1-1과 동일 경로이나 circular import 위험 0 확인됨. 직접 대입 사용.

### 1-6. `feature_flags.enable_patch_mode` 플래그 연결

**파일**: `modules/core/stage4_interview_round.py` (L108 부근)

`validation.yaml:155`에 `enable_patch_mode: true` 정의됨.
현재 Stage4에서 패치 모드 진입 시 이 플래그를 체크하지 않음.

수정: `_threshold()` 패턴으로 플래그 체크 추가 (ConfigManager는 인스턴스 메서드라 정적 호출 불가).
```python
_patch_enabled = bool(_threshold("feature_flags.enable_patch_mode", 1))
_use_patch = _patch_enabled and _prev_score >= _PATCH_REWRITE_THRESHOLD and _prev_manuscript
```

**참고**: `validation.yaml` L153-161에 `feature_flags.enable_patch_mode: true` 이미 존재. YAML 수정 불필요.

### Phase 1 테스트

```bash
python -m ruff check modules/ main_a.py --no-fix
set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -q --tb=short --capture=no
```

---

## Phase 2: Information Bottleneck 해소 (6건)

### 2-1. 벡터 메타 상한 확대

**파일**: `modules/core/vec_memory.py` (L210-217 부근)

현재:
```python
causal_str = json.dumps(causal_links, ensure_ascii=False)[:500]
evt_str = ",".join(str(e) for e in event_types)[:200]
ent_str = ",".join(str(n) for n in entity_names)[:300]
# ...
(ep_num, summary[:500], causal_str, arc_no, evt_str, ent_str)
```

수정:
```python
causal_str = json.dumps(causal_links, ensure_ascii=False)[:2000]
evt_str = ",".join(str(e) for e in event_types)[:500]
ent_str = ",".join(str(n) for n in entity_names)[:1000]
# ...
(ep_num, summary[:1000], causal_str, arc_no, evt_str, ent_str)
```

### 2-2. 패치 모드 smart_truncate

**파일**: `modules/domain/agents/chief_writer.py` (L696, L703 부근)

현재:
```python
original_manuscript[:30000]  # 2곳
```

수정:
```python
from modules.core.constants import smart_truncate
# ...
smart_truncate(original_manuscript, max_chars=30000, head_chars=5000)
```

`smart_truncate`는 이미 `constants.py`에 정의됨 (이전 컨텍스트 최대화 Phase에서 추가).

### 2-3. Director 경고 상한 확대

**파일**: `modules/core/stage4_interview_round.py` (L509 부근)

현재:
```python
_vr_warns[:10]
```

수정:
```python
_vr_warns[:30]
```

### 2-4. 초기 동기화 보강

**파일**: `modules/core/project_manager.py`

3곳 수정:
```python
# L838 부근: summary 범위 확대
summary = content[:300]...  →  summary = content[:1000]...

# L853 부근: entity 검색 범위 확대
content[:3000]  →  content[:8000]

# L861 부근: entity 상한 확대
list(_bulk_entities)[:10]  →  list(_bulk_entities)[:30]
```

### 2-5. 검증 결과 구조 보존

**파일**: `modules/core/stage4_interview_round.py` (L340-390 부근)

현재: `reason = v.get("reason", str(v))` 로 문자열만 추출.

수정 방향:
1. 기존 `reason` 문자열 추출은 **유지** (하위 호환)
2. `validation_results[ci]`에 새 키 추가:

```python
# 기존 코드 직후에 추가
if "structured_violations" not in validation_results[ci]:
    validation_results[ci]["structured_violations"] = []
validation_results[ci]["structured_violations"].append(v)  # raw dict 보존
```

3. Director 프롬프트 조립 시 (`_vr_warnings_for_director` 부근) severity 정보도 포함:

```python
# 기존 문자열 경고에 severity 태그 추가
# cv_violations: consistency_validator 반환 dict의 "violations" 리스트 (stage4_interview_round.py L340-390 부근에서 추출)
for v in cv_violations:
    severity = v.get("severity", "")
    reason = v.get("reason", str(v))
    tagged = f"[{severity}] {reason}" if severity else reason
    validation_results[ci]["warnings"].append(tagged)
```

### 2-6. REJECT 피드백 보강

**파일 1**: `modules/core/stage4_interview_round.py` (L620-627 부근)

현재 `previous_attempt` dict에 추가:
```python
previous_attempt = {
    "strategy": selected,
    "rejection_reason": director_feedback,
    "action_items": action_items,
    "score": score,
    "best_manuscript": ...,
    # ── 신규 추가 ──
    "score_breakdown": director_result.get("score_breakdown", {}),
    "selection_reason": director_result.get("selection_reason", ""),
    "validation_warnings": [w for vr in validation_results for w in vr.get("warnings", [])][:20],
}
```

**파일 2**: `modules/domain/agents/chief_writer.py` (L580-597 부근)

`enhanced_feedback` 조립 시 추가 정보 활용:
```python
# score_breakdown이 있으면 세부 채점 포함
_sb = previous_attempt.get("score_breakdown", {})
if _sb:
    _sb_lines = [f"  - {k}: {v}" for k, v in _sb.items() if isinstance(v, (int, float))]
    if _sb_lines:
        enhanced_feedback += "\n[세부 채점]\n" + "\n".join(_sb_lines)

# validation_warnings가 있으면 포함
_vw = previous_attempt.get("validation_warnings", [])
if _vw:
    enhanced_feedback += "\n[Python 검증 경고]\n" + "\n".join(f"- {w}" for w in _vw[:10])
```

### Phase 2 테스트

```bash
python -m ruff check modules/ main_a.py --no-fix
set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -q --tb=short --capture=no
```

---

## Phase 2.5: Score 90 Quality Gate (Stage 2/3/4 공통)

### 개요

현재: Director PASS → 즉시 통과.
변경: Director PASS + score ≥ 90 → 통과. PASS + score < 90 → REJECT 전환 → 패치 모드.
5회 기회 소진 시 → 사용자 대기 (자동 진행 안 함).

### 2.5-1. Stage4 PASS 분기 — score ≥ 90 강제

**파일**: `modules/core/stage4_interview_round.py` (L574 부근, PASS 분기)

현재:
```python
if verdict == "PASS":
    # 최종 통과 처리
```

수정:
```python
_QUALITY_GATE_SCORE = _threshold("scoring.quality_gate_score", 90)

if verdict == "PASS":
    if score < _QUALITY_GATE_SCORE:
        # PASS이지만 score 미달 → REJECT으로 전환
        self.ctx.ui.log(f"   ⚠️ [QualityGate] PASS 판정이나 score={score} < {_QUALITY_GATE_SCORE} → 패치 모드")
        verdict = "REJECT"
        director_feedback += f"\n[Quality Gate] Director PASS 판정이나 점수 {score}점으로 {_QUALITY_GATE_SCORE}점 미달. 품질 개선 후 재제출."
        # 아래 REJECT 경로로 자연 진행 → score ≥ 50이면 패치 모드
    else:
        # score ≥ 90: 정상 통과
        ...
```

### 2.5-2. Stage2 PASS 분기 — score ≥ 90 강제

**파일**: `modules/core/stage2_finalizer.py` (L176 부근, PASS 분기)

현재:
```python
if audit.get("decision") == "PASS" and _td_len >= 1500:
    # 최종 통과 처리
```

수정:
```python
_QUALITY_GATE_SCORE = _threshold("scoring.quality_gate_score", 90)
_score = audit.get("score", 0)

if audit.get("decision") == "PASS" and _td_len >= 1500:
    if _score < _QUALITY_GATE_SCORE:
        self.ctx.ui.log(f"      ⚠️ [QualityGate] PASS 판정이나 score={_score} < {_QUALITY_GATE_SCORE} → REJECT 전환")
        audit["decision"] = "REJECT"
        audit["reason"] = (audit.get("reason") or "") + f"\n[Quality Gate] score {_score}점으로 {_QUALITY_GATE_SCORE}점 미달."
        audit["re_slice_instruction"] = audit.get("re_slice_instruction") or "품질 개선 후 재제출"
        # 아래 else(REJECT) 경로로 자연 진행
    else:
        # score ≥ 90: 정상 통과
        ...
```

**주의**: `stage2_finalizer.py:153` quota fallback PASS (50점) 로직은 사실상 무력화됨.
- quota fallback PASS는 score=50으로 PASS → Quality Gate에서 score < 90 → REJECT
- 의도적: 품질 미달 Arc가 그대로 넘어가는 것을 방지
- 5회 소진 시 사용자 대기

### 2.5-3. Stage3 PASS 분기 — score ≥ 90 강제

**파일**: `modules/domain/agents/three_phase_blueprint_generator.py` (L277 부근, PASS 분기)

현재:
```python
if verdict == "PASS":
    self.stats["phase3_pass"] += 1
    pipeline_result["final_verdict"] = "PASS"
    ...
    return best_blueprint, pipeline_result
```

수정:
```python
_QUALITY_GATE_SCORE = _threshold("scoring.quality_gate_score", 90)
_score = validation_result.get("score", 0)

if verdict == "PASS":
    if _score < _QUALITY_GATE_SCORE:
        logging.warning(f"[QualityGate] Stage3 PASS이나 score={_score} < {_QUALITY_GATE_SCORE} → REJECT 전환")
        verdict = "REJECT"
        feedback = (feedback or "") + f"\n[Quality Gate] score {_score}점으로 {_QUALITY_GATE_SCORE}점 미달."
        # 아래 REJECT 경로로 자연 진행
    else:
        self.stats["phase3_pass"] += 1
        pipeline_result["final_verdict"] = "PASS"
        ...
        return best_blueprint, pipeline_result
```

**변수 참고**: Stage3는 `verdict`, `feedback`, `validation_result` 사용. `validation_result`에서 score 추출.

### 2.5-4. validation.yaml에 quality_gate_score 추가

**파일**: `config/settings/validation.yaml`

`scoring` 섹션에 추가:
```yaml
scoring:
  quality_gate_score: 90        # PASS 판정 필요 최소 점수 (미만 시 REJECT 전환)
  default_pass_threshold: 70
  ...
```

### 2.5-5. 5회 소진 시 사용자 대기

**파일**: `modules/core/stage4_orchestrator.py` (L584, L602 부근)

현재 동작: 5회 소진 시 자동 중단 + 로그 출력 (L602):
```python
self.ctx.ui.log(f"\n⛔ [EP {next_ep}] 5회 면담 모두 실패. 인간 검토 필요.")
return _RoundOutcome(should_return=True)
```

수정: 기존 자동 중단 흐름을 유지하되, 최선 결과물이 있으면 사용자에게 선택지 제공.
UIService의 기존 `get_int_input()` 패턴 사용:
```python
_last_best = previous_attempt.get("best_manuscript", "") if previous_attempt else ""
_last_score = previous_attempt.get("score", 0) if previous_attempt else 0
if not final_manuscript and _last_best:
    self.ctx.ui.log(f"\n⚠️ [EP {next_ep}] 5회 소진. 마지막 최선 결과물(score={_last_score}) 존재.")
    _choice = self.ctx.get_int_input(
        "  1=최선 결과물로 진행  2=건너뛰기: ", default=2, min_val=1, max_val=2
    )
    if _choice == 1:
        final_manuscript = _last_best
    else:
        return _RoundOutcome(should_return=True)
elif not final_manuscript:
    self.ctx.ui.log(f"\n⛔ [EP {next_ep}] 5회 면담 모두 실패. 인간 검토 필요.")
    return _RoundOutcome(should_return=True)
```

**Stage2**: `modules/core/stage2_orchestrator.py`, `stage_2_arcs_async_logic()` 메서드 L584 부근.
현재 `if not passed:` 이후 `# [V60.45] 다시 하기 옵션` (L672) 앞에 삽입.
변수: `_last_best` = 직전 REJECT의 `refined_arc` (존재 시), `_last_score` = `audit.get("score", 0)`.
기존 while-True 사용자 메뉴(옵션 1~4)는 그대로 두되, 그 전에 최선 결과물이 있으면 선택지 추가.
```python
# stage2_orchestrator.py L584 부근, `if not passed:` 블록 내, `# [V60.45]` 전
if _last_refined_arc:
    _last_score = _last_refined_arc.get("_director_score", 0)
    self.ctx.ui.log(f"\n⚠️ Arc {global_arc_no}: 5회 소진. 마지막 최선 결과물(score={_last_score}) 존재.")
    _choice = self.ctx.get_int_input(
        "  1=최선 결과물로 진행  2=기존 메뉴로: ", default=2, min_val=1, max_val=2
    )
    if _choice == 1:
        refined_arc = _last_refined_arc
        passed = True
        break  # while attempt 루프 탈출 아닌, 기존 흐름에 맞게 조정
```

**Stage3**: `modules/domain/agents/three_phase_blueprint_generator.py`, `generate()` 메서드 L309 부근.
현재 `# 모든 재시도 실패` 후 `return None, pipeline_result` 전에 삽입.
```python
# three_phase_blueprint_generator.py L309 부근, return None 전
if best_blueprint:
    logging.warning(f"[ThreePhase] 모든 재시도 실패이나 마지막 최선 blueprint 존재 (score={_last_score})")
    # Stage3는 LLM 에이전트 내부 — UI 직접 호출 가능 여부 확인 후 get_int_input 사용
    # UI 미접근 시: best_blueprint 그대로 반환 (quality gate가 걸러줌)
    pipeline_result["final_verdict"] = "PASS_WITH_WARNING"
    return best_blueprint, pipeline_result
```

### 패치 모드 상호작용 (변경 사항)

| 시나리오 | 동작 |
|---------|------|
| Director PASS + score ≥ 90 | 통과 → ChainOfVerification 사후검증 |
| Director PASS + score 50~89 | REJECT 전환 → 패치 모드 (score ≥ 50) |
| Director PASS + score < 50 | REJECT 전환 → 전면 재작성 |
| Director REJECT + score ≥ 50 | 패치 모드 (기존 동작) |
| Director REJECT + score < 50 | 전면 재작성 (기존 동작) |
| 5회 소진 | 사용자 대기 |

---

## Phase 3: Always-On 모듈 5개 연결

### 공통 작업: Stage4Context 슬롯 확장

**파일**: `modules/core/stage4_context.py`

`__slots__`에 5개 추가:
```python
__slots__ = (
    ...,
    "pre_director_checklist",
    "confidence_calibrator",
    "prompt_weighter",
    "cross_verifier",
    "chain_of_verification",
)
```

`from_app()` 클래스메서드에서 주입:
```python
@classmethod
def from_app(cls, app):
    ctx = cls(...)
    ...
    ctx.pre_director_checklist = getattr(app, "pre_director_checklist", None)
    ctx.confidence_calibrator = getattr(app, "confidence_calibrator", None)
    ctx.prompt_weighter = getattr(app, "prompt_weighter", None)
    ctx.cross_verifier = getattr(app, "cross_verifier", None)
    ctx.chain_of_verification = getattr(app, "chain_of_verification", None)
    return ctx
```

### 3-1. PreDirectorChecklist 연결 (Python, $0)

**삽입 파일**: `modules/core/stage4_interview_round.py`

**삽입 지점**: Director 평가 직전 (Director `select_and_judge_ensemble` 호출 전).
원고 생성 후, validation 결과 수집 후, Director 호출 직전에 삽입.

```python
# Director 호출 직전에 삽입
if self.ctx.pre_director_checklist:
    try:
        _checklist_ctx = {}
        if blueprint:
            _checklist_ctx["blueprint"] = blueprint
        if _prev_manuscript:
            _checklist_ctx["prev_manuscript"] = _prev_manuscript

        for ci, cand in enumerate(candidates):
            _ms = cand.get("manuscript", "")
            if not _ms or ci >= len(validation_results):
                continue
            _cl_result = self.ctx.pre_director_checklist.check(_ms, "manuscript", context=_checklist_ctx)
            if not _cl_result.passed:
                for _br in _cl_result.blocking_reasons:
                    validation_results[ci]["warnings"].append(f"[PreCheck] {_br}")
                validation_results[ci]["warning_count"] = len(validation_results[ci]["warnings"])
                self.ctx.ui.log(f"   ⚠️ [PreCheck] 후보{ci+1}: {_cl_result.summary[:60]}...")
    except Exception as e:
        logging.warning(f"[SilentPass:PreDirectorChecklist] {e!s:.100}")
```

**주의**: PreDirectorChecklist가 불합격 시키더라도 Director 호출은 그대로 진행. warnings에 추가만 함.

### 3-2. ConfidenceCalibrator 연결 (Python, $0)

**삽입 파일**: `modules/core/stage4_interview_round.py`

**삽입 지점**: PreDirectorChecklist 직후, Director 호출 직전.

```python
if self.ctx.confidence_calibrator:
    try:
        for ci, cand in enumerate(candidates):
            _ms = cand.get("manuscript", "")
            if not _ms or ci >= len(validation_results):
                continue
            _conf = self.ctx.confidence_calibrator.assess(
                _ms, "manuscript",
                context={"blueprint": blueprint, "prev_manuscript": _prev_manuscript}
            )
            if _conf.concerns:
                for _c in _conf.concerns[:3]:
                    # ConfidenceLevel도 Enum — .value 사용
                    validation_results[ci]["warnings"].append(f"[Confidence:{_conf.level.value}] {_c}")
                validation_results[ci]["warning_count"] = len(validation_results[ci]["warnings"])
    except Exception as e:
        logging.warning(f"[SilentPass:ConfidenceCalibrator] {e!s:.100}")
```

**주의**: `recommendation == "regenerate"` 경우에도 Director에게 위임 (concerns를 warnings으로 전달). Director가 최종 판정.

### 3-3. DynamicPromptWeighter 연결 (Python, $0)

**삽입 파일**: `modules/core/stage4_interview_round.py`

**삽입 지점**: Chief Writer 호출 전, 프롬프트 조립 단계.

```python
# Chief Writer 프롬프트에 가중치 지침 주입
_weighted_injection = ""
if self.ctx.prompt_weighter:
    try:
        _weighted_injection = self.ctx.prompt_weighter.get_weighted_prompt("writer", 4, top_n=3)
    except Exception as e:
        logging.warning(f"[SilentPass:PromptWeighter] {e!s:.100}")

# _weighted_injection을 mandatory_context 또는 director_feedback에 append
if _weighted_injection:
    director_feedback = (_weighted_injection + "\n\n" + director_feedback) if director_feedback else _weighted_injection
```

**삽입 위치 정확 확인**: `stage4_interview_round.py`에서 `chief_writer.generate_ensemble()` 호출 전에 `director_feedback` 변수에 prepend. (참조: stage4_interview_round.py L75, chief_writer.py L114)

**주의**: `director_feedback` 변수는 이름과 달리 **Chief Writer 전용**. Director Agent에는 전달되지 않음 (`director_ensemble.select_and_judge_ensemble()`의 파라미터에 director_feedback 없음). 따라서 Writer 전용 지침 주입이 안전.

### 3-4. CrossAgentVerifier 연결 (Python precheck → LLM 에스컬레이션)

**삽입 파일**: `modules/core/stage4_interview_round.py`

**삽입 지점**: PreDirectorChecklist 직후, Director 호출 직전.

```python
if self.ctx.cross_verifier and blueprint:
    try:
        for ci, cand in enumerate(candidates):
            _ms = cand.get("manuscript", "")
            if not _ms or ci >= len(validation_results):
                continue
            _compliance = self.ctx.cross_verifier.verify_writer_compliance(
                manuscript=_ms, blueprint=blueprint, use_llm=False  # Python only
            )
            # ⚠️ ComplianceLevel은 Enum — .name이 아니라 Enum 비교 사용
            from modules.core.cross_agent_verifier import ComplianceLevel
            if _compliance.level == ComplianceLevel.VIOLATION:
                for _v in _compliance.violations[:5]:
                    _v_msg = _v.get("reason", str(_v)) if isinstance(_v, dict) else str(_v)
                    validation_results[ci]["warnings"].append(f"[CrossVerify:VIOLATION] {_v_msg}")
                validation_results[ci]["warning_count"] = len(validation_results[ci]["warnings"])
            elif _compliance.warnings:
                for _w in _compliance.warnings[:3]:
                    _w_msg = _w.get("reason", str(_w)) if isinstance(_w, dict) else str(_w)
                    validation_results[ci]["warnings"].append(f"[CrossVerify:WARNING] {_w_msg}")
                validation_results[ci]["warning_count"] = len(validation_results[ci]["warnings"])
    except Exception as e:
        logging.warning(f"[SilentPass:CrossAgentVerifier] {e!s:.100}")
```

### 3-5. ChainOfVerification 연결 (Director ACCEPT 후 사후검증)

**삽입 파일**: `modules/core/stage4_orchestrator.py`

**삽입 메서드**: `_handle_round_outcome()` (L568) — 5회 면담 루프가 있는 메서드.

**삽입 지점**: PASS 분기(L592) 내부, `final_manuscript` 할당(L593-595) 직후 / `break`(L596) 직전.

**⚠️ 루프 구조 주의**:
```
_run_interview_loop()          ← 에피소드 루프 (process_pass_result 호출)
  └─ _handle_round_outcome()   ← 면담 루프 (for interview_round in range(5))
       └─ interview_round.run()
```
CoVe는 `_handle_round_outcome()`의 면담 루프 안에 넣어야 `continue`가 다음 면담 라운드로 이동.
`_run_interview_loop()` 쪽에 넣으면 면담 루프 이미 종료 후라 재시도 불가.

```python
# _handle_round_outcome() L592-596 PASS 분기 수정:
if _round_result.verdict == "PASS":
    final_manuscript = _round_result.final_manuscript
    final_title = _round_result.final_title
    final_state_updates = _round_result.final_state_updates

    # ── CoVe 사후검증 (PASS 확정 후, break 전) ──
    if self.ctx.chain_of_verification and final_manuscript:
        try:
            _cove_context = {}
            _prev_ms = round_ctx.prev_manuscripts_text or ""
            _bp = round_ctx.blueprint
            if _prev_ms:
                _cove_context["prev_manuscript"] = _prev_ms[-1500:]
            if _bp:
                _cove_context["blueprint"] = _bp

            # 1단계: Python 빠른 검증 ($0)
            _quick_ok, _quick_msg = self.ctx.chain_of_verification.quick_verify(
                final_manuscript, _cove_context
            )
            if not _quick_ok:
                self.ctx.ui.log(f"   ⚠️ [CoVe] 사후검증 경고: {_quick_msg[:60]}...")
                # 2단계: LLM 정밀 검증 ($0.01) — quick 실패 시만
                try:
                    _cove_result = self.ctx.chain_of_verification.verify(
                        final_manuscript, _cove_context, content_type="manuscript"
                    )
                    if _cove_result.should_regenerate:
                        self.ctx.ui.log(f"   🚨 [CoVe] 치명적 모순 감지 → REJECT 전환")
                        final_manuscript = None  # PASS 취소
                        _cove_feedback = _cove_result.correction_hints or _cove_result.summary
                        director_feedback = f"[CoVe 사후검증 실패]\n{_cove_feedback}"
                        continue  # ← for interview_round in range(5)의 다음 반복으로
                except Exception as e:
                    logging.warning(f"[SilentPass:CoVe:LLM] {e!s:.100}")
        except Exception as e:
            logging.warning(f"[SilentPass:CoVe:Quick] {e!s:.100}")

    break  # CoVe 통과 → 면담 루프 탈출
```

**핵심 변경**:
- `break`를 CoVe 검증 **이후**로 이동 (기존 L596 → CoVe 블록 아래)
- CoVe 실패 시 `final_manuscript = None` + `continue` → 면담 루프 다음 라운드
- CoVe 성공 시 `break` → `_run_interview_loop()`로 돌아가서 `process_pass_result()` 호출
- `process_pass_result()` 반환 계약 변경 없음 (bool, False=DB실패=break)
- CoVe는 `stage4_post_processor.py`에 넣지 않음
- 비차단: CoVe 예외 시 기존 `break` 경로 그대로 진행

### Phase 3 테스트

```bash
python -m ruff check modules/ main_a.py --no-fix
set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -q --tb=short --capture=no
```

---

## Phase 4: ASP 교정 모듈 연결 (재시도 2회차+)

### 역할 분리 원칙

```
Director = 최종 판정자 (PASS/REJECT 권한)
ASP (AdversarialSelfPlay) = 재작성용 레드팀 (교정만, 판정 없음)
```

- 기본: Director만 동작
- REJECT 2회 이상: ASP 1회 실행 → "수정안"만 생성
- ASP 수정안도 반드시 Director가 재심사 (최종 PASS/REJECT는 Director)
- ToT/MAD는 이번에 연결하지 않음 (초기화 코드 유지, 파이프라인 미연결)

### 4-1. Stage4Context 슬롯 추가

**파일**: `modules/core/stage4_context.py`

```python
__slots__ = (
    ...,
    "adversarial_self_play",
)
```

`from_app()`에서 주입:
```python
ctx.adversarial_self_play = getattr(app, "adversarial_self_play", None)
```

### 4-2. ASP 교정 코드 구현

**파일**: `modules/core/stage4_interview_round.py`

**삽입 지점**: `run()` 메서드 (L15) 내부, `else:` 분기 (L101, `round_num >= 1` 경로) 앞. `generate_ensemble()` 호출 전에 ASP 교정 코드를 삽입.

```python
# REJECT 2회 이상 → ASP 교정 1회
_asp_manuscript = None
if round_num >= 2 and self.ctx.adversarial_self_play and previous_attempt:
    try:
        _prev_ms = previous_attempt.get("best_manuscript", "")
        if _prev_ms:
            self.ctx.ui.log(f"   🔥 [ASP] 레드팀 교정 발동 (재시도 {round_num + 1}회차)")
            _asp_ctx = {}
            if blueprint:
                _asp_ctx["blueprint"] = blueprint
            if director_feedback:
                _asp_ctx["director_feedback"] = director_feedback

            _asp_result = self.ctx.adversarial_self_play.generate_with_adversary(
                initial_content=_prev_ms,
                content_type="manuscript",
                context=_asp_ctx,
            )
            if _asp_result and hasattr(_asp_result, "final_output") and _asp_result.final_output:
                _asp_manuscript = _asp_result.final_output
                self.ctx.ui.log(f"   ✅ [ASP] 교정 완료 (delta: +{getattr(_asp_result, 'improvement_delta', '?')})")
    except Exception as e:
        logging.warning(f"[SilentPass:ASP] {e!s:.200}")

# ASP 교정안을 후보에 추가 → Director가 기존 후보와 함께 재심사
if _asp_manuscript:
    candidates.append({"manuscript": _asp_manuscript, "strategy": "asp_correction"})
```

**핵심**:
- ASP는 "수정안"만 만듦. PASS/REJECT 판정은 Director가 함.
- ASP 결과물은 candidates에 추가 (기존 후보 대체가 아님).
- Director가 기존 후보보다 ASP 수정안이 낫다고 판단하면 선택.

### Phase 4 테스트

```bash
python -m ruff check modules/ main_a.py --no-fix
set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -q --tb=short --capture=no
```

---

## Phase 5: 미사용 모듈 정리

### 5-1. main_a.py에서 3개 초기화 제거

**파일**: `main_a.py`

삭제 대상 3종류:

**A. `__init__` 상단 None 선언 (L262-267 부근)**:
```python
self.semantic_cache = None  # L262 삭제
self.context_compressor = None  # L263 삭제
self.manuscript_enhancer = None  # L267 삭제
```

**B. 초기화 블록 (L1688~1709 부근)**:
```python
# L1688-1689: SemanticCache 초기화 + 로그 전체 삭제
self.semantic_cache = SemanticCache(max_size=500)
self.ui.log("   💾 [V54.1] Semantic Cache 활성화")

# L1692-1693: ContextCompressor 초기화 + 로그 전체 삭제
self.context_compressor = ContextCompressor(target_ratio=0.6, max_field_length=2000)
self.ui.log("   📦 [V54.2] Context Compressor 활성화")

# L1709-1710: ManuscriptEnhancer 초기화 + 로그 전체 삭제
self.manuscript_enhancer = ManuscriptEnhancer(genre=genre_type)
self.ui.log("   ✨ [V55] Manuscript Enhancer 활성화 (7개 서브모듈)")
```

**C. import 문**:
```python
from modules.core.context_compression import ContextCompressor  # L110 삭제
from modules.core.manuscript_enhancer import ManuscriptEnhancer  # L117 삭제
from modules.core.semantic_cache import SemanticCache  # L128 삭제
```

**유지 대상** (삭제하지 않음):
- `TreeOfThoughts` 초기화 — 추후 연결 가능
- `MultiAgentDeliberation` 초기화 — 추후 연결 가능
- `AdversarialSelfPlay` 초기화 — Phase 4에서 파이프라인 연결됨

**모듈 .py 파일은 전부 보존** (삭제하지 않음).

### Phase 5 테스트

```bash
python -m ruff check modules/ main_a.py --no-fix
set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -q --tb=short --capture=no
```

---

## Director 피드백 현황 분석

각 Phase가 해소하는 피드백 누수를 정리.

### Stage 4 (원고) — 현재 누수 3건

| 누수 | 현상 | 해소 Phase |
|------|------|-----------|
| `score_breakdown` 미전달 | Director가 세부 채점(character_consistency, dialogue_quality 등) 반환하나 Chief Writer에 도달 안 함 | **Phase 2-6** |
| `validation_warnings` 미전달 | Python 검증 경고가 Chief Writer 재작성 프롬프트에 없음 | **Phase 2-6** |
| 경고 상한 `[:10]` | Director에게 전달되는 검증 경고가 10개로 절삭 | **Phase 2-3** |

**현재 작동하는 것**: `action_items` → `director_feedback` 문자열 → `enhanced_feedback` 템플릿 → `🚨 [Director 피드백 - 반드시 반영]` 마커로 LLM 프롬프트 주입. 패치/전면 재작성 양 경로 모두 무절삭 전달.

### Stage 2 (Arc) — 누수 거의 없음

Director가 `reason` + `re_slice_instruction` + 적응형 재시도 가이드를 조립하여 `director_feedback_for_fourphase` 블록으로 FourPhase에 직접 주입. Self-consistency 투표로 오판 감소. **이번 Phase에서 추가 수정 없음.**

### Stage 3 (Blueprint) — 경미한 약점

Director 피드백이 단일 `feedback` string. Stage 2의 reason + re_slice_instruction 이중 구조보다 구조화 부족. `comparison_notes`(후보별 비교 분석) 활용도 불명확. **Phase 2.5-3 Quality Gate가 최소 품질 보장 역할.**

### Phase별 피드백 개선 매핑

```
Phase 2-3  → Director에게 가는 경고 10→30개 확대
Phase 2-5  → severity 태그 + structured_violations 보존
Phase 2-6  → score_breakdown + validation_warnings를 Chief Writer에 전달
Phase 3-1  → PreDirectorChecklist: 구조/연속성 경고를 Director 입력에 추가
Phase 3-2  → ConfidenceCalibrator: 신뢰도 기반 경고 추가
Phase 3-4  → CrossAgentVerifier: blueprint 준수 위반 경고 추가
Phase 3-5  → CoVe: PASS 후 모순 감지 시 피드백 포함 재시도
Phase 4-2  → ASP: 2회 REJECT 후 레드팀 교정안을 후보에 추가
```

---

## 주의사항

- Phase 순서 엄수 (1 → 2 → 2.5 → 3 → 4 → 5)
- 각 Phase 완료 후 ruff + pytest 실행
- Phase 3에서 Stage4Context 슬롯 추가 시 기존 `from_app()` 패턴 준수 (`getattr(app, ..., None)`)
- Phase 4 필살기 결과는 반드시 Director 심사를 거침 (candidates에 추가)
- **Director 주권 절대 불가침**: 모듈이 ACCEPT 판정을 내려선 안 됨
- `[SilentPass:모듈명]` 형식으로 모든 예외 로깅 (기존 패턴 준수)
- `adaptive_retry_manager`의 `record_failure()`, `should_trigger_ultimate()` 실제 시그니처를 코드에서 확인 후 사용
- CoVe는 `_handle_round_outcome()` 면담 루프(L584) 안에 삽입 — `_run_interview_loop()` 쪽 아님
