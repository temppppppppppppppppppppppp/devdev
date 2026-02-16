# Codex Order — D Step 4: 좌절-보상 타이머 (advisory)

> 실행 전제: HEAD `470dfee`, 테스트 346 passed
> 청사진 참조: `docs/phase3_satisfaction_blueprint.md` §4-5

---

## 목표

최근 에피소드의 만족도 태그(`episode_satisfaction_tags` 테이블)를 조회하여
**좌절 연속 화수**를 감지하고, 경고를 Director에 advisory로 전달한다.

핵심 원칙: **Python은 좌절 연속 화수를 "감지"만 하고, 경고를 Director에 전달한다.
Python이 REJECT하지 않으며, Director가 최종 판단한다.**

---

## 수정/생성 파일 (4개)

| 파일 | 변경 | 규모 |
|------|------|------|
| `config/settings/validation.yaml` | `satisfaction:` 섹션 추가 | ~5줄 |
| `modules/validation/continuity_validator.py` | `check_frustration_streak()` 메서드 추가 | ~40줄 |
| `modules/core/stage4_orchestrator.py` | 좌절 타이머 호출 훅 추가 | ~15줄 |
| `tests/test_satisfaction_step4_frustration.py` | **신규** 테스트 | ~250줄 |

**프로덕션 코드 변경은 위 3개 파일에만 한정. 다른 파일 절대 수정 금지.**

---

## 1. validation.yaml — `satisfaction:` 섹션 추가

**삽입 위치**: `cross_episode_repetition:` 섹션 뒤, `feature_flags:` 섹션 앞 (L133과 L135 사이)

```yaml
# ── 만족도 좌절-보상 타이머 ────────────────────────────────────
satisfaction:
  frustration_warning_streak: 3    # 좌절 N화 연속 시 WARNING (보상 에피소드 권장)
  frustration_critical_streak: 5   # 좌절 N화 연속 시 강한 WARNING (대리만족 부재 심각)
```

---

## 2. continuity_validator.py — `check_frustration_streak()` 추가

### 삽입 위치

파일 끝 (L932 뒤). 기존 `_check_time_consistency` 메서드 뒤에 새 메서드 추가.

### 코드

```python
    # ── [D Step 4] 좌절-보상 타이머 (advisory) ──────────────────

    def check_frustration_streak(self, ep_num: int) -> list[str]:
        """최근 에피소드의 좌절 연속 화수를 검사한다.

        Rules:
        - 좌절 N화 연속 (default 3): WARNING "보상 에피소드 권장"
        - 좌절 M화 연속 (default 5): WARNING "대리만족 부재 심각"

        Returns:
            경고 메시지 리스트 (빈 리스트 = 정상)
        """
        db = getattr(self.context, "db", None) if self.context else None
        if not db or not hasattr(db, "get_recent_satisfaction_tags"):
            return []

        warn_threshold = _threshold("satisfaction.frustration_warning_streak", 3)
        crit_threshold = _threshold("satisfaction.frustration_critical_streak", 5)

        try:
            tags = db.get_recent_satisfaction_tags(before_ep=ep_num, lookback=crit_threshold)
        except Exception:
            return []

        if not tags:
            return []

        # 최신→과거 순으로 연속 좌절 카운트
        streak = 0
        for tag in reversed(tags):
            if tag.get("frustration_flag"):
                streak += 1
            else:
                break

        warnings = []
        if streak >= crit_threshold:
            warnings.append(
                f"[Satisfaction] 좌절 {streak}화 연속 — 대리만족 부재 심각. "
                f"다음 에피소드에 보상 장면 필수."
            )
        elif streak >= warn_threshold:
            warnings.append(
                f"[Satisfaction] 좌절 {streak}화 연속 — 보상 에피소드 권장."
            )
        return warnings
```

### 주의사항

- `_threshold` 임포트는 이미 L21에 존재: `from modules.validation.threshold_helper import _threshold`
- `self.context`는 `__init__` 에서 받은 context (ProjectContext). `self.context.db`로 DB 접근.
- `get_recent_satisfaction_tags(before_ep, lookback)` — Step 3에서 추가한 DBManager 메서드.
  반환: `[{"ep_num": int, "primary_tag": str, "frustration_flag": bool, ...}, ...]` (오래된 순)
- **이 메서드는 ContinuityValidator.validate() 내부에서 호출하지 않는다.**
  원고 내용과 무관하므로, stage4_orchestrator에서 직접 1회 호출한다.

---

## 3. stage4_orchestrator.py — 좌절 타이머 훅 추가

### 삽입 위치

ContinuityValidator 루프 뒤, 파괴 엔티티 감지 블록 앞.
즉, **L2081 직후 ~ L2083 직전** (현재 빈 줄이 있는 지점).

```
현재:
L2080:                        validation_results[ci]["warning_count"] = len(validation_results[ci]["warnings"])
L2081:        except Exception as _ct_err:
L2082:            self.ctx.ui.log(f"      ⚠️ [V66.1] ContinuityValidator 실행 실패: {str(_ct_err)[:60]}")
L2083:
L2084:        # [V66.2] C-4: 파괴 엔티티 감지 → Director에 경고 전달
```

### 삽입할 코드 (L2083 위치에)

```python
        # [D Step 4] 좌절-보상 타이머 — Director에 advisory 전달
        try:
            _frust_warnings = continuity_validator.check_frustration_streak(next_ep)
            if _frust_warnings:
                for ci in range(len(validation_results)):
                    for _fw in _frust_warnings:
                        validation_results[ci]["warnings"].append(f"[D Step 4] {_fw}")
                    validation_results[ci]["warning_count"] = len(validation_results[ci]["warnings"])
                for _fw in _frust_warnings:
                    self.ctx.ui.log(f"      ⚠️ {_fw}")
        except Exception as _frust_err:
            logging.warning("[D Step 4] 좌절-보상 타이머 실패 (비차단): %s", _frust_err)

```

### 패턴 설명

- `continuity_validator`는 L2287에서 `ContinuityValidator(context=self.ctx.current_project)` 로 이미 생성됨
- 경고를 **모든 후보의 `validation_results[ci]["warnings"]`** 에 추가 → L2156-2174에서 Director mandatory_context에 자동 포함
- 원고 내용 무관하므로 per-candidate가 아니라 **1회만 호출**, 결과를 전 후보에 주입
- try/except + logging.warning = 비차단 패턴 (기존 advisory 훅과 동일)

---

## 4. 테스트 — `tests/test_satisfaction_step4_frustration.py`

### 구조

```
TestFrustrationStreak (7개)
  - test_no_tags_returns_empty           # 태그 0건 → 빈 리스트
  - test_no_frustration_returns_empty    # 좌절 없음 → 빈 리스트
  - test_streak_below_threshold_empty    # 좌절 2화 → 빈 리스트 (3 미만)
  - test_streak_3_warning               # 좌절 3화 연속 → 경고 1건 "권장"
  - test_streak_5_critical              # 좌절 5화 연속 → 경고 1건 "심각"
  - test_streak_reset_after_reward      # 중간에 성취 → streak 초기화
  - test_streak_counts_from_latest      # 과거 좌절 + 최신 성취 → streak 0

TestFrustrationThresholds (3개)
  - test_yaml_satisfaction_section_exists     # validation.yaml에 satisfaction 섹션 존재
  - test_threshold_warning_default           # _threshold("satisfaction.frustration_warning_streak", 3) → 3
  - test_threshold_critical_default          # _threshold("satisfaction.frustration_critical_streak", 5) → 5

TestStage4FrustrationHook (3개)
  - test_hook_code_exists                    # stage4_orchestrator 소스에 "check_frustration_streak" 존재
  - test_hook_non_blocking                   # "비차단" 또는 try/except 패턴 존재
  - test_hook_injects_to_validation_results  # "[D Step 4]" 접두사로 warnings에 주입

TestWarningFormat (2개)
  - test_warning_message_contains_streak_count   # 경고에 화수 포함 (예: "3화 연속")
  - test_critical_message_contains_severe        # 심각 경고에 "심각" 포함
```

### Fixtures

```python
@pytest.fixture
def db(tmp_path):
    """In-memory DBManager."""
    from modules.core.db_manager import DBManager
    d = DBManager(tmp_path / "test_frust.db")
    yield d
    d.close()

@pytest.fixture
def validator_with_db(db):
    """ContinuityValidator with DB context."""
    from modules.validation.continuity_validator import ContinuityValidator
    ctx = MagicMock()
    ctx.db = db
    return ContinuityValidator(context=ctx)
```

### 주요 테스트 패턴

```python
def test_streak_3_warning(self, validator_with_db, db):
    """좌절 3화 연속 → 경고 1건"""
    for i in range(1, 4):
        db.save_satisfaction_tag(i, {"primary_tag": "좌절", "frustration_flag": True})
    warnings = validator_with_db.check_frustration_streak(ep_num=4)
    assert len(warnings) == 1
    assert "3화 연속" in warnings[0]
    assert "권장" in warnings[0]

def test_streak_reset_after_reward(self, validator_with_db, db):
    """중간에 성취 → streak 초기화"""
    db.save_satisfaction_tag(1, {"primary_tag": "좌절", "frustration_flag": True})
    db.save_satisfaction_tag(2, {"primary_tag": "좌절", "frustration_flag": True})
    db.save_satisfaction_tag(3, {"primary_tag": "성취", "frustration_flag": False})  # ← 리셋
    db.save_satisfaction_tag(4, {"primary_tag": "좌절", "frustration_flag": True})
    warnings = validator_with_db.check_frustration_streak(ep_num=5)
    assert warnings == []  # streak 1 < 3
```

---

## 5. 검증 게이트 (순서대로)

```bash
# Gate 1: py_compile (수정 파일)
python -m py_compile modules/validation/continuity_validator.py
python -m py_compile modules/core/stage4_orchestrator.py
python -m py_compile tests/test_satisfaction_step4_frustration.py

# Gate 2: SovereignApp import 불변
python -c "from main_a import SovereignApp; print('OK')"

# Gate 3: 신규 테스트 실행
set PYTHONIOENCODING=utf-8
pytest tests/test_satisfaction_step4_frustration.py -v

# Gate 4: 기존 테스트 회귀 없음
pytest tests/test_satisfaction_step3_tagging.py tests/test_satisfaction_step2_prompts.py tests/test_satisfaction_framework.py -v
pytest tests/test_npc_history.py tests/test_config_manager.py tests/test_stage4_orchestrator.py -v
pytest tests/test_stage2_pipeline.py tests/test_stage2_context.py -v

# Gate 5: pre-commit
pre-commit run --files modules/validation/continuity_validator.py modules/core/stage4_orchestrator.py tests/test_satisfaction_step4_frustration.py config/settings/validation.yaml
```

---

## 6. 커밋 메시지

```
feat(phase3-d4): add frustration-reward advisory timer for Director feedback

- ContinuityValidator.check_frustration_streak(): 좌절 연속 화수 감지
- Stage4 pre-Director hook: advisory warnings → validation_results → Director
- validation.yaml: satisfaction.frustration_warning_streak(3) / critical(5)
- 테스트 15개 (streak scenarios + threshold + hook integration)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

---

## 7. 절대 하지 말 것

1. **REJECT 로직 추가 금지** — 이 기능은 advisory-only. Python은 감지만, 판단은 Director.
2. **ContinuityValidator.validate() 내부에서 호출 금지** — 원고 내용과 무관한 검사이므로 stage4에서 1회 호출.
3. **기존 validate() 반환 구조 변경 금지** — `{"tier": "CONTINUITY", "passed": ..., "violations": ..., "warnings": ...}` 불변.
4. **다른 파일 수정 금지** — 위 3개 프로덕션 파일 + 1개 테스트 파일만 수정/생성.
5. **LLM 호출 추가 금지** — 이 기능은 순수 Python (DB 조회 + 비교). $0 비용.
6. **frustration_flag 재계산 금지** — Step 3에서 이미 저장된 값 그대로 사용.

---

## 8. 참조 코드 위치

| 항목 | 파일:라인 |
|------|----------|
| `ContinuityValidator.__init__` | `continuity_validator.py:32-37` |
| `ContinuityValidator._check_time_consistency` (마지막 메서드) | `continuity_validator.py:874-932` |
| `_threshold` 임포트 | `continuity_validator.py:21` |
| `continuity_validator` 생성 | `stage4_orchestrator.py:2287` |
| ContinuityValidator 루프 (삽입 지점 직전) | `stage4_orchestrator.py:2060-2082` |
| 파괴 엔티티 감지 (삽입 지점 직후) | `stage4_orchestrator.py:2083-2096` |
| Director mandatory_context 조립 | `stage4_orchestrator.py:2156-2174` |
| `get_recent_satisfaction_tags` | `db_manager.py:1382-1407` |
| `save_satisfaction_tag` | `db_manager.py:1346-1380` |
| Step 3 만족도 태깅 훅 | `stage4_orchestrator.py:1168-1181` |
| validation.yaml 현재 끝 | `validation.yaml:143` |
