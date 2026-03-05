# Codex Order: NS-3 — Treatment Block 수치 목표 Self-Critic/Phase 2.5 주입

**작업 ID**: NS-3-A (fallback self-critic) + NS-3-B (main FourPhase 경로)
**우선순위**: P1
**대상 파일**:
- `modules/domain/agents/analyst.py` (NS-3-A, fallback)
- `modules/domain/agents/four_phase_arc_generator.py` (NS-3-B, main 경로)
- `config/prompts/analyst.yaml` — 변경 없음 (프롬프트는 NS-1-S2에서 이미 강화)
- `tests/` 내 적합한 파일 또는 `tests/test_ns3_block_targets.py` 신규

**테스트 기준선**: 3,364 passed (실패 없이 유지)

---

## 배경

NS-1-S2는 `ANALYST_SELF_CRITIC_PROMPT`에 수치 자기검증 항목 7을 추가했으나,
이 self-critic은 **fallback 경로** (`plan_single_arc_v20`)에만 존재.

실제 메인 경로는:
```
FourPhaseArcGenerator.generate()
  └─ Phase 1-2: Ensemble 생성 (curr_block 전달됨, genre_ext는 컨텍스트로만)
  └─ Phase 2.6: Director.compare_and_select_arc(curr_block=curr_block)
  └─ Phase 3: validator.validate() (curr_block 미전달)
  └─ → Director 최종 심사 (stage2_finalizer)
```

**두 경로 모두 treatment block의 `genre_ext` 수치 목표
(capital_before / capital_after / profit_loss 등)가
생성된 arc의 arc_end_state 수치와 일치하는지 LLM이 명시적으로 교차검증하지 않음.**

Arc 2 실패 사례:
- treatment `genre_ext.capital_after`: "23억 (미실현 수익 포함)"
- Arc 생성 tactical_doc: "451억 수익 실현" (계산 오류 + 목표 괴리 동시 발생)
- Director가 REJECT했으나 2회 재시도 소모

---

## 구현 명세 — [NS-3-A] Fallback self-critic에 curr_block 수치 주입

### 대상: `modules/domain/agents/analyst.py`

**위치**: L857-861 (`# 자기 비판 감사 (Self-Critic) 호출` 블록)

**변경 전**:
```python
# 자기 비판 감사 (Self-Critic) 호출
critic_input = (
    f"{get_analyst_self_critic_prompt()}\n[Draft to Review]: {json.dumps(draft_result, ensure_ascii=False)}"
)
audit_result = self._extract_json_robust(self.ask(critic_input, temperature=0.2, thinking_level="low"))
```

**변경 후**:
```python
# 자기 비판 감사 (Self-Critic) 호출
_critic_block_ctx = _format_block_numeric_targets(curr_block)
critic_input = (
    f"{get_analyst_self_critic_prompt()}"
    + (_critic_block_ctx and f"\n\n{_critic_block_ctx}" or "")
    + f"\n[Draft to Review]: {json.dumps(draft_result, ensure_ascii=False)}"
)
audit_result = self._extract_json_robust(self.ask(critic_input, temperature=0.2, thinking_level="low"))
```

**`_format_block_numeric_targets` 헬퍼 함수** — `analyst.py` 모듈 상단 (import 블록 뒤)에 추가:

```python
def _format_block_numeric_targets(curr_block: dict | None) -> str:
    """
    [NS-3-A] curr_block.genre_ext의 수치 목표를 self-critic 컨텍스트 문자열로 변환.
    genre_ext가 없거나 수치 필드가 없으면 빈 문자열 반환.
    """
    if not isinstance(curr_block, dict):
        return ""
    genre_ext = curr_block.get("genre_ext")
    if not isinstance(genre_ext, dict) or not genre_ext:
        return ""

    # 수치 관련 키 우선 추출 (전장르 공통 + 투자물 특화)
    numeric_keys = {
        "capital_before", "capital_after", "capital_delta",
        "profit_loss", "leverage", "position_size",
        "level_before", "level_after", "rank_before", "rank_after",
        "stat_change", "energy_before", "energy_after",
    }
    lines = []
    for k, v in genre_ext.items():
        if k in numeric_keys or any(kw in k for kw in ("capital", "profit", "loss", "delta", "level", "rank", "energy", "stat", "asset", "revenue")):
            lines.append(f"  {k}: {v}")

    if not lines:
        return ""

    return (
        "[NS-3 Treatment 수치 목표 — Arc 종료 상태가 아래 목표에 근접해야 합니다]\n"
        + "\n".join(lines)
        + "\n위 수치와 tactical_doc/arc_end_state 수치가 크게 괴리되면 FAIL 처리하세요. "
        "30% 이내 오차는 서사 변동으로 허용합니다."
    )
```

**소비자 코드 확인**: `plan_single_arc_v20`의 `curr_block` 파라미터(L542)는 이미 클로저 `_arc_attempt_func` 스코프에서 접근 가능 (Python 클로저 규칙). 별도 파라미터 전달 불필요.

---

## 구현 명세 — [NS-3-B] FourPhase 메인 경로 Phase 2.5 Python 교차검증

### 배경

메인 FourPhase 경로에서는 self-critic이 없음. Phase 2.6 Director 선택 전에
**Python-only** 사전 교차검증 단계를 삽입 → Director가 REJECT 전에 경고 인지 → feedback에 포함.

### 대상: `modules/domain/agents/four_phase_arc_generator.py`

**위치**: Phase 2.5 Auto-sanitize (L826-827) 직후, Phase 2.6 Director selection (L440-501) 이전

**추가 코드**:
```python
# [NS-3-B] Phase 2.55: Treatment block 수치 목표 교차검증 (Python-only, advisory)
_ns3b_warning = _check_arc_vs_block_targets(best_arc, curr_block, arc_no)
if _ns3b_warning:
    logging.warning("[NS-3-B] %s", _ns3b_warning)
    # Director 선택 feedback에 prepend → Director가 REJECT 시 피드백에 포함
    feedback = f"[NS-3-B 수치 목표 괴리 경고]\n{_ns3b_warning}\n\n{feedback}" if feedback else f"[NS-3-B 수치 목표 괴리 경고]\n{_ns3b_warning}"
```

**`_check_arc_vs_block_targets` 모듈 레벨 함수** (파일 상단에 추가):

```python
def _check_arc_vs_block_targets(
    arc: dict,
    curr_block: dict | None,
    arc_no: int,
    threshold: float = 0.30,
) -> str:
    """
    [NS-3-B] arc_end_state 수치 vs curr_block.genre_ext 목표 비교.
    Python-only, LLM 0회. 30% 초과 괴리 시 경고 문자열 반환.
    """
    if not isinstance(curr_block, dict) or not isinstance(arc, dict):
        return ""
    genre_ext = curr_block.get("genre_ext")
    if not isinstance(genre_ext, dict):
        return ""

    arc_end = arc.get("state_constraints", {}).get("arc_end_state", {})
    if not isinstance(arc_end, dict):
        return ""

    import re

    def parse_num(s) -> float | None:
        if isinstance(s, (int, float)):
            return float(s)
        if not isinstance(s, str):
            return None
        s = re.sub(r"\([^)]*\)", "", s).strip().lstrip("+-")
        for unit, mult in [("조", 1e12), ("억", 1e8), ("만", 1e4)]:
            m = re.search(r"([\d,]+(?:\.\d+)?)" + unit, s.replace(",", ""))
            if m:
                try:
                    return float(m.group(1)) * mult
                except ValueError:
                    return None
        return None

    target = parse_num(genre_ext.get("capital_after", ""))
    if not target:
        return ""

    actual = None
    actual_key = None
    for key in ("total_assets", "assets", "capital", "total_capital"):
        v = parse_num(str(arc_end.get(key, "")))
        if v is not None:
            actual = v
            actual_key = key
            break

    if actual is None:
        return ""

    div = abs(target - actual) / abs(target) if target else 0
    if div > threshold:
        return (
            f"Arc {arc_no} arc_end_state.{actual_key}={actual/1e8:.1f}억 vs "
            f"treatment 목표 capital_after={genre_ext['capital_after']} "
            f"(괴리 {div*100:.0f}%). tactical_doc 수치를 목표에 맞게 조정하세요."
        )
    return ""
```

---

## 테스트 명세

### [NS-3-A] Fallback self-critic 주입 (3개)

```python
# TC-NS3A-1: curr_block에 genre_ext 있으면 critic_input에 [NS-3 Treatment 수치 목표] 블록 포함
def test_ns3a_block_targets_injected_into_critic_input():
    from modules.domain.agents.analyst import _format_block_numeric_targets
    block = {"genre_ext": {"capital_before": "20억", "capital_after": "23억", "profit_loss": "+3억"}}
    result = _format_block_numeric_targets(block)
    assert "[NS-3 Treatment 수치 목표" in result
    assert "capital_after" in result

# TC-NS3A-2: genre_ext 없는 블록 (무협 내공 등 수치 미기재) → 빈 문자열
def test_ns3a_no_genre_ext_returns_empty():
    from modules.domain.agents.analyst import _format_block_numeric_targets
    block = {"title": "무협 블록", "emotional_beat": "돌파"}
    assert _format_block_numeric_targets(block) == ""

# TC-NS3A-3: curr_block=None → 빈 문자열 (안전 처리)
def test_ns3a_none_block_returns_empty():
    from modules.domain.agents.analyst import _format_block_numeric_targets
    assert _format_block_numeric_targets(None) == ""
```

### [NS-3-B] FourPhase Phase 2.55 교차검증 (3개)

```python
# TC-NS3B-1: arc_end_state 470억 vs genre_ext capital_after 23억 → 경고 문자열 반환
def test_ns3b_large_divergence_returns_warning():
    from modules.domain.agents.four_phase_arc_generator import _check_arc_vs_block_targets
    arc = {"state_constraints": {"arc_end_state": {"total_assets": "470억"}}}
    block = {"genre_ext": {"capital_after": "23억"}}
    result = _check_arc_vs_block_targets(arc, block, arc_no=2)
    assert result != ""
    assert "NS-3-B" in result or "괴리" in result

# TC-NS3B-2: 허용 범위 내 (25억 vs 23억, ~8.7%) → 빈 문자열
def test_ns3b_small_divergence_returns_empty():
    from modules.domain.agents.four_phase_arc_generator import _check_arc_vs_block_targets
    arc = {"state_constraints": {"arc_end_state": {"total_assets": "25억"}}}
    block = {"genre_ext": {"capital_after": "23억"}}
    assert _check_arc_vs_block_targets(arc, block, arc_no=2) == ""

# TC-NS3B-3: genre_ext 없음 → 빈 문자열
def test_ns3b_no_genre_ext_returns_empty():
    from modules.domain.agents.four_phase_arc_generator import _check_arc_vs_block_targets
    arc = {"state_constraints": {"arc_end_state": {"total_assets": "25억"}}}
    block = {"title": "no genre ext"}
    assert _check_arc_vs_block_targets(arc, block, arc_no=1) == ""
```

---

## 감리 포인트

1. `_format_block_numeric_targets` 함수 `analyst.py` 모듈 상단(import 블록 뒤)에 추가 확인
2. `plan_single_arc_v20` L857-861 critic_input 빌드 부분에 `_critic_block_ctx` 주입 확인
3. `_check_arc_vs_block_targets` 함수 `four_phase_arc_generator.py` 모듈 상단에 추가 확인
4. Phase 2.5 (`_check_arc_end_state`) 직후, Phase 2.6 (`if director and len(all_candidates) >= 2:`) 이전에 NS-3-B 블록 삽입 확인
5. `pytest tests/ -q` → 3,364 → 3,370 passed (+6)
6. `ruff check` → 0 violations
7. 기존 analyst / four_phase 관련 테스트 회귀 없음

---

## 스코프 외

- NS-1-S2 YAML 프롬프트 수정 — 이미 완료 (`ANALYST_SELF_CRITIC_PROMPT` 항목 7)
- Phase 3 `UnifiedArcValidator`에 `curr_block` 추가 — ROI 낮음 (Phase 2.6 Director가 이미 curr_block 보며 심사)
- `genre_ext` 필드 정규화 (무협 energy, 헌터 rank 등) — 투자물 우선, 확장은 별도
- NS-3-B의 `feedback` 변수가 해당 scope에서 mutable인지 확인 필요 (retry loop 내부 변수) — Codex가 코드 읽고 판단
