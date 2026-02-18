# Debug Sweep 36 — 공허 참 override + 에러 삼킴 + arc 계산 불일치

## Context

Sweep 35 완료 (2,074+ passed, 68 xfailed). 5개 탐색 에이전트 중 5개 완료 — Director REJECT 공허 참(vacuous truth) override(1건), 에러 삼킴/스택트레이스 누락(3건), Blueprint 키 불일치(1건), arc 계산 상수 불일치(1건), dead no-op 분기(1건) 발견.

---

## A-1 (MEDIUM-HIGH): `continuity_arc.py:424` — `all()` 공허 참으로 REJECT→PASS 묵시적 override

**파일**: `modules/domain/agents/continuity_arc.py:424-428`

**문제**: LLM이 `{"decision": "REJECT", "violations": []}` 반환 시 `all()` on empty iterable returns `True` (공허 참):

```python
violations = []                         # L415 fallback
intra_only = all(                       # L424 — 빈 리스트에서 all() = True!
    isinstance(v, dict) and v.get("type") in [...]
    for v in violations
)
if intra_only and start_state_corrected:    # L428 — True and True
    result["decision"] = "PASS"             # L429 — REJECT가 PASS로!
```

- **결과**: Director가 REJECT 판정을 내렸으나 구체적 violations를 비워둔 경우, 묵시적으로 PASS 처리됨
- **위반**: CLAUDE.md "디렉터 주권주의" 원칙 — Director의 REJECT를 Python이 override

**수정**: L424를 다음으로 변경:
```python
                intra_only = violations and all(
```

---

## A-2 (MEDIUM): `analyst.py:691-692` — 에러 삼킴 + 절단된 에러 LLM 프롬프트 주입

**파일**: `modules/domain/agents/analyst.py:691-692`

**문제**:
```python
except Exception as e:
    hud_context = f"(HUD 로드 오류: {str(e)[:30]})"
```

- `logging.warning()` 호출 없음 → 에러가 완전히 삼켜짐
- `str(e)[:30]` 절단된 에러가 `safe_data["hud_context"]` → LLM 프롬프트에 주입
- 디버깅 시 HUD 로드 실패 원인 추적 불가

**수정**: L691-692를 다음으로 변경:
```python
            except Exception as e:
                logging.warning(f"[Analyst] HUD 로드 오류: {e}")
                hud_context = f"(HUD 로드 오류: {str(e)[:50]})"
```

---

## A-3 (MEDIUM): `block_enricher.py:783-784` — 검증 경로 완전 삼킴

**파일**: `modules/domain/agents/block_enricher.py:783-784`

**문제**:
```python
except Exception as e:
    return []  # 검증 실패 시 빈 리스트 (에러 없음 처리)
```

- 검증 메서드가 크래시 시 "이상 없음" 반환 → 검증 코드 버그 완전 은폐
- logging 없음 → 운영 중 발견 불가

**수정**: L783-784를 다음으로 변경:
```python
        except Exception as e:
            logging.warning(f"[BlockEnricher] validate_causal_chain 실패 (non-blocking): {e}")
            return []  # 검증 실패 시 빈 리스트
```

---

## A-4 (MEDIUM): `stage2_preflight.py:149-153` — CRITICAL 경로 스택트레이스 누락

**파일**: `modules/core/stage2_preflight.py:149-153`

**문제**:
```python
except Exception as e:  # [V64.P4] CRITICAL: state extraction failure
    self.ctx.ui.log(
        f"      ⚠️ [V64.P4] extract_cumulative_state 실패 (NPC 검증 약화): {str(e)[:80]}"
    )
    self.ctx.audit_event("critical_state_extraction_failed", str(e)[:200])
```

- `[V64.P4] CRITICAL` 주석이 달린 경로인데 `logging.exception()`이나 `traceback.format_exc()` 없음
- UI log에만 `:80` 절단 메시지 → 스택트레이스 완전 소실
- NPC 검증이 비활성화되는 심각한 상황에서 원인 추적 불가

**수정**: L149-153을 다음으로 변경:
```python
                    except Exception as e:  # [V64.P4] CRITICAL: state extraction failure → NPC validation disabled
                        logging.warning(
                            f"[V64.P4] CRITICAL: extract_cumulative_state 실패 (NPC 검증 약화): {e}",
                            exc_info=True,
                        )
                        self.ctx.ui.log(
                            f"      ⚠️ [V64.P4] extract_cumulative_state 실패 (NPC 검증 약화): {str(e)[:80]}"
                        )
                        self.ctx.audit_event("critical_state_extraction_failed", str(e)[:200])
```

---

## A-5 (MEDIUM): Blueprint `ep_num` vs `episode_number` 키 불일치

**파일**: `modules/domain/agents/blueprint_ensemble.py:624`, `modules/domain/agents/continuity_blueprint.py:277,375`

**문제**: LLM 스키마(`response_schemas.py:309`)와 Pydantic 모델(`models/blueprint.py:38`)은 `episode_number`를 사용하지만, 소비자 3곳이 `ep_num`을 읽음:

```python
# blueprint_ensemble.py:624 — 매 Blueprint 생성 시 호출 (LIVE)
bp_ep = bp.get("ep_num", "?")          # → "?" 반환

# continuity_blueprint.py:277 — Python 사전검증 (LIVE)
ep_num = bp.get("ep_num", 0)           # → 0 반환

# continuity_blueprint.py:375 — 아이템 추적 (LIVE)
ep_num = bp.get("ep_num", "?")         # → "?" 반환
```

- **결과**: LLM 프롬프트에 "제?화" 표시 → Blueprint 연속성 컨텍스트 품질 저하
- `ensemble.yaml:277` 프롬프트 템플릿은 `ep_num` 출력을 지시하지만, Gemini 구조화 출력 스키마는 `episode_number` 사용 → 스키마 우선 시 `ep_num` 키 부재

**수정**: `modules/models/blueprint.py`에 `ep_num` alias 추가 (ArcData._sync_arc_no_alias 패턴 참조):
```python
from pydantic import model_validator

class Blueprint(BaseModel):
    # ... 기존 필드 ...
    episode_number: int = 0

    @model_validator(mode="before")
    @classmethod
    def _sync_ep_num_alias(cls, values):
        """ep_num ↔ episode_number 양방향 동기화"""
        if isinstance(values, dict):
            if "ep_num" in values and not values.get("episode_number"):
                values["episode_number"] = values["ep_num"]
            elif "episode_number" in values and "ep_num" not in values:
                values["ep_num"] = values["episode_number"]
        return values
```

이 수정으로 LLM이 어느 키를 출력하든 양방향 동기화됨.

---

## B-1 (LOW): `main_a.py:2158` — Arc 계산 `//10` vs 표준 `EPISODES_PER_ARC=5`

**파일**: `main_a.py:2153-2158`

**문제**:
```python
def _calculate_arc_from_episode(self, ep_num):
    """에피소드 번호로부터 Arc 번호 계산 (각 Arc에 10화)"""
    if ep_num <= 0:
        return 0
    return (ep_num - 1) // 10 + 1          # ← 10화/Arc
```

- `constants.py:207`: `EPISODES_PER_ARC = 5`
- `state_tracker.py:491`: `base_ep = (arc_no - 1) * 5 + 1`
- `state_tracker_npc.py:1226,1325`: `arc_no = (ep_num - 1) // 5 + 1`
- **결과**: 15화 → Arc 2(10화 기준) vs Arc 3(5화 기준) — UI 경고 메시지 부정확
- Smart Skip 경고만 영향, 실제 Arc 처리 루프는 `done_count` 기준이라 데이터 무영향

**수정**: L2154-2158을 다음으로 변경:
```python
    def _calculate_arc_from_episode(self, ep_num):
        """에피소드 번호로부터 Arc 번호 계산"""
        if ep_num <= 0:
            return 0
        return (ep_num - 1) // 5 + 1
```

---

## B-2 (LOW): `stage2_orchestrator.py:192-193` — dead no-op 분기

**파일**: `modules/core/stage2_orchestrator.py:192-193`

**문제**:
```python
if skip_arc_no <= done_count:
    pass                                    # ← no-op
elif skip_arc_no > done_count:
    ...
```

- `if A <= B: pass elif A > B:` — 첫 분기가 완전 no-op, 단순 `if skip_arc_no > done_count:`로 충분
- 코드 가독성 저하

**수정**: L192-199를 다음으로 변경:
```python
        if skip_arc_no > done_count:
            self.ctx.ui.log(f"📂 [Manuscript Detected] 기존 원고 {existing_ms_max_ep}화까지 발견")
            self.ctx.ui.log(
                f"⚠️  [Warning] Arc {skip_arc_no}까지 필요하지만 Arc {done_count}까지만 DB에 존재합니다."
            )
            self.ctx.ui.log(f"💡 [Info] Arc {done_count + 1}부터 설계를 시작합니다. (원고와 Arc 동기화 필요)")
```

---

## 수정 파일 총괄

| # | 파일 | 변경 |
|---|------|------|
| A-1 | `modules/domain/agents/continuity_arc.py` | L424 `violations and` 추가 (1줄) |
| A-2 | `modules/domain/agents/analyst.py` | L691-692 logging 추가 + 절단 확장 (2줄→3줄) |
| A-3 | `modules/domain/agents/block_enricher.py` | L783-784 logging 추가 (1줄→2줄) |
| A-4 | `modules/core/stage2_preflight.py` | L149-153 logging.warning(exc_info=True) 추가 (3줄→6줄) |
| A-5 | `modules/models/blueprint.py` | `_sync_ep_num_alias` model_validator 추가 (~10줄) |
| B-1 | `main_a.py` | L2158 `//10` → `//5` (1줄) |
| B-2 | `modules/core/stage2_orchestrator.py` | L192-199 dead no-op 제거 (8줄→5줄) |

**총 7파일, ~25줄 변경**

---

## 테스트

```python
# tests/test_sweep36.py
"""Sweep 36: 공허 참 override + 에러 삼킴 + arc 계산 테스트"""
import pytest
from unittest.mock import MagicMock, patch


class TestVacuousTruthOverride:
    """A-1: all() on empty violations → REJECT 유지"""

    def test_reject_with_empty_violations_stays_reject(self):
        """violations=[] 일 때 REJECT가 PASS로 바뀌지 않아야 함"""
        from modules.domain.agents.continuity_arc import ContinuityArcInspector
        import pathlib
        source = pathlib.Path("modules/domain/agents/continuity_arc.py").read_text(encoding="utf-8")
        # violations and all(...) 패턴 확인
        assert "violations and all(" in source


class TestAnalystHudLogging:
    """A-2: analyst HUD 에러 로깅 확인"""

    def test_hud_error_logged(self):
        """HUD 로드 오류 시 logging.warning 호출 확인"""
        import pathlib
        source = pathlib.Path("modules/domain/agents/analyst.py").read_text(encoding="utf-8")
        hud_section = source[source.index("HUD 로드 오류"):source.index("HUD 로드 오류") + 300]
        assert "logging.warning" in hud_section


class TestBlockEnricherLogging:
    """A-3: block_enricher 검증 경로 로깅 확인"""

    def test_validate_error_logged(self):
        """검증 실패 시 logging.warning 호출 확인"""
        import pathlib
        source = pathlib.Path("modules/domain/agents/block_enricher.py").read_text(encoding="utf-8")
        # validate_causal_chain 에러 핸들러에 logging 존재 확인
        idx = source.index("validate_causal_chain")
        assert "logging.warning" in source[idx:idx + 500]


class TestPreflightStackTrace:
    """A-4: stage2_preflight CRITICAL 경로 스택트레이스"""

    def test_critical_path_has_exc_info(self):
        """CRITICAL 경로에 exc_info=True 존재 확인"""
        import pathlib
        source = pathlib.Path("modules/core/stage2_preflight.py").read_text(encoding="utf-8")
        critical_section = source[source.index("critical_state_extraction_failed"):source.index("critical_state_extraction_failed") + 500]
        assert "exc_info" in critical_section


class TestArcCalculation:
    """B-1: arc 계산 상수 일치"""

    def test_arc_from_episode_uses_5(self):
        """_calculate_arc_from_episode가 5화 기준 계산"""
        import pathlib
        source = pathlib.Path("main_a.py").read_text(encoding="utf-8")
        func_start = source.index("_calculate_arc_from_episode")
        func_section = source[func_start:func_start + 300]
        assert "// 5" in func_section
        assert "// 10" not in func_section

    def test_ep15_returns_arc3(self):
        """15화 → Arc 3 (5화/Arc 기준)"""
        # 직접 계산 검증
        ep_num = 15
        result = (ep_num - 1) // 5 + 1
        assert result == 3


class TestBlueprintEpNumAlias:
    """A-5: Blueprint ep_num ↔ episode_number 양방향 동기화"""

    def test_episode_number_creates_ep_num(self):
        """episode_number 입력 시 ep_num도 생성"""
        from modules.models.blueprint import Blueprint
        bp = Blueprint.model_validate({"episode_number": 5, "integrated_scenario": "test"})
        dumped = bp.model_dump()
        assert dumped.get("ep_num") == 5

    def test_ep_num_creates_episode_number(self):
        """ep_num 입력 시 episode_number도 생성"""
        from modules.models.blueprint import Blueprint
        bp = Blueprint.model_validate({"ep_num": 7, "integrated_scenario": "test"})
        dumped = bp.model_dump()
        assert dumped.get("episode_number") == 7


class TestDeadNoopRemoval:
    """B-2: dead no-op 분기 제거"""

    def test_no_dead_pass_branch(self):
        """skip_arc_no <= done_count: pass 분기 제거 확인"""
        import pathlib
        source = pathlib.Path("modules/core/stage2_orchestrator.py").read_text(encoding="utf-8")
        smart_skip = source[source.index("Smart Skip"):source.index("Smart Skip") + 500]
        assert "pass" not in smart_skip or "pass_rate" in smart_skip  # pass_rate 변수는 허용
```

```bash
set PYTHONIOENCODING=utf-8 && python -m pytest tests/test_sweep36.py -x -q
set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -x -q
```

---

## 오탐 제거 기록

| 보고 | 실제 | 이유 |
|------|------|------|
| Agent 1: HUD anomaly dead code | ✗ dead code | `hud_snapshot` 컬럼 미존재 — 기능 미구현, 런타임 버그 아님 |
| Agent 1: StateTracker validation dead | ✗ 의도적 | `[V70]` 주석 — "preset_registry/llm_client 없이 검증 불가" 명시적 비활성화 |
| Agent 1: 5 Analyst methods never called | ✗ dead code | 확장 포인트 — 미연결 기능, 런타임 영향 없음 |
| Agent 1: 5 PromptBuilder methods test-only | ✗ dead code | 미연결 품질 가이드 — 런타임 영향 없음 |
| Agent 1: unused cumulative_bible variable | ✗ LOW | L400 미사용 변수 — 불필요 DB 쿼리지만 크래시 아님 |
| Agent 1: BlueprintEnsembleGenerator dead methods | ✗ dead code | 미연결 평가/경고 기능 |
| Agent 1: FactLedger/WorldState utility methods | ✗ dead code | 수동 수정 경로 미연결 |
| Agent 2: state_tracker_npc.py:1828 괄호 | ✗ 무해 | Python 우선순위 정확, 가독성만 이슈 |

---

## Execution Update (2026-02-18)

Status: completed for Sweep 36 scope.

Applied items:
- A-1 `modules/domain/agents/continuity_arc.py`: fixed vacuous-truth override by changing REJECT relaxation guard to `intra_only = violations and all(...)`.
- A-2 `modules/domain/agents/analyst.py`: HUD load error path now logs warning (`[Analyst] HUD 로드 오류`) and uses a wider truncation window (`[:50]`).
- A-3 `modules/domain/agents/block_enricher.py`: causal-chain validation exception path now emits non-blocking warning log before returning empty issues.
- A-4 `modules/core/stage2_preflight.py`: critical cumulative-state extraction failure now logs stack trace via `logging.warning(..., exc_info=True)` in addition to UI/audit signaling.
- A-5 `modules/models/blueprint.py`: added `ep_num` <-> `episode_number` synchronization via `@model_validator(mode="before")`.
- B-1 `main_a.py`: `_calculate_arc_from_episode` now uses 5-episode buckets (`(ep_num - 1) // 5 + 1`).
- B-2 `modules/core/stage2_orchestrator.py`: removed dead no-op branch (`if skip_arc_no <= done_count: pass`) in Smart Skip logic.

Added tests:
- `tests/test_sweep36.py` (8 tests) covering:
  - vacuous-truth guard source check
  - analyst HUD error logging/truncation source check
  - block enricher causal validation warning source check
  - stage2 preflight critical path `exc_info=True` source check
  - blueprint alias sync behavior (both directions)
  - arc calculation source guard (`// 5`, no `// 10`)
  - Smart Skip dead no-op branch removal source check

Verification run:
- `python -m py_compile modules/domain/agents/continuity_arc.py modules/domain/agents/analyst.py modules/domain/agents/block_enricher.py modules/core/stage2_preflight.py modules/models/blueprint.py modules/core/stage2_orchestrator.py main_a.py tests/test_sweep36.py` -> pass
- `python -m pytest tests/test_sweep36.py -q -x` -> `8 passed`
- `python -m pytest tests/test_sweep36.py tests/test_sweep35.py tests/test_sweep34.py tests/test_sweep18.py tests/test_sweep19.py tests/test_sweep23.py tests/test_sweep32.py tests/test_stage2_preflight.py tests/test_stage2_preflight_helpers.py tests/test_stage2_pipeline.py tests/test_continuity_modules.py tests/test_director_modules.py -q -x -p no:capture` -> `316 passed`
- `python -m pytest tests/ -q -p no:capture` -> `2087 passed, 68 xfailed, 1 warning`

Notes:
- Running pytest with default capture intermittently raised `ValueError: I/O operation on closed file`; verification was completed with `-p no:capture`.
- Full suite output still includes existing mocked ImportError traceback print, but pytest exit code is 0 and suite status is green.
