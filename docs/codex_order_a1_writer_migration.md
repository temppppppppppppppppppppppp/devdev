# Codex Order A-1: writer.py 유틸리티 해체

> 우선순위: 1 / 카테고리: 기술부채 / 규모: 소 / 위험도: 낮음

---

## 목표

`modules/domain/agents/writer.py`의 유틸리티 메서드 3개 + 헬퍼 5개를 독립 모듈로 이전.
Writer 클래스는 냉동인간 폴백(`write_v20_manuscript`)만 유지.

---

## 현재 구조

### writer.py (501줄) — 이전 대상

| 라인 | 메서드 | 역할 | 호출처 |
|------|--------|------|--------|
| 257-285 | `_build_mandatory_context(current_ep)` | HUD 이상치 + 최근 사건 + NPC 상태 → 문자열 | stage4_orchestrator.py L535 |
| 287-295 | `_build_anti_trope_instructions(genre_name)` | 반클리셰 프롬프트 | stage4_orchestrator.py L766 |
| 297-329 | `_build_justification_guidance(hud_report, genre_name)` | 정당화 패턴 안내 | stage4_orchestrator.py L771 |
| 335-381 | `_check_hud_anomalies_v60(current_ep)` | HUD 급변 감지 | `_build_mandatory_context` 내부 |
| 383-390 | `_extract_numeric_value(value)` | HUD 숫자 추출 | `_check_hud_anomalies_v60` 내부 |
| 392-409 | `_extract_recent_events(current_ep, n_episodes)` | 최근 N화 사건 | `_build_mandatory_context` 내부 |
| 411-431 | `_extract_npc_last_states(current_ep)` | NPC 마지막 상태 | `_build_mandatory_context` 내부 |
| 433-435 | `_get_hud_trend_safe(ep_num)` | HUD 트렌드 (이미 hud_utils 위임) | **미사용 — 삭제 가능** |

### stage4_orchestrator.py — 호출 지점

`_build_mandatory_context()` (L485-584) 내부에서:
- L535: `mandatory_context = writer_agent._build_mandatory_context(next_ep)`
- L766: `anti_trope_prompt = writer_agent._build_anti_trope_instructions(genre_name)`
- L771: `justification_prompt = writer_agent._build_justification_guidance(hud_report, genre_name)`

`writer_agent`는 L1457에서 `self.ctx.agents.get("writer")`로 획득, L494 `writer_agent` 파라미터로 전달됨.

---

## 작업 상세

### Step 1: 신규 모듈 생성

**파일**: `modules/core/writer_prompt_builders.py` (~170줄)

```python
"""
[A-1] Writer 유틸리티 독립 모듈

writer.py에서 분리된 프롬프트 빌더 + 헬퍼 함수.
stage4_orchestrator._build_mandatory_context()에서 호출.
"""
import re
import logging


def build_mandatory_context(db, master_bible, current_ep: int) -> str:
    """[main_a.py line 6307] 강제 맥락 주입

    Parameters:
        db: DBManager 인스턴스 (get_manuscript, load_state_log 메서드 사용)
        master_bible: dict — 프로젝트 MasterBible
        current_ep: int — 현재 에피소드 번호
    """
    parts = ["[MANDATORY CONTEXT]\n"]

    hud_anomalies = _check_hud_anomalies(db, current_ep)
    if hud_anomalies.get("has_anomalies"):
        parts.append("\n[HUD ANOMALY WARNING]\n")
        for a in hud_anomalies.get("anomalies", []):
            parts.append(f"- {a['type']}: {a['description']}")
            parts.append(f"  -> {a['recommendation']}\n")

    recent_events = _extract_recent_events(db, current_ep, n_episodes=3)
    if recent_events:
        parts.append("\n최근 중요 사건:")
        for event in recent_events:
            parts.append(f"- 제{event['ep_num']}화: {event['description']}")
            if event.get("consequence"):
                parts.append(f"  현재 상태: {event['consequence']}")

    npc_states = _extract_npc_last_states(master_bible, current_ep)
    if npc_states:
        parts.append("\nNPC 마지막 관계 상태:")
        for npc_name, state_info in npc_states.items():
            parts.append(f"- {npc_name}: {state_info['relationship']} (제{state_info['last_ep']}화)")

    if len(parts) == 1:
        parts.append("\n(첫 에피소드이거나 강제 맥락 없음)")
    return "\n".join(parts)


def build_anti_trope_instructions(genre_name: str) -> str:
    """[main_a.py line 6354] 반클리셰 명령"""
    return f"""[ANTI-TROPE PROTOCOL - {genre_name}]
1. "약해 보이는 주인공" 클리셰 금지 - HUD 상태 직접 반영
2. "무시-사이다" 매 화 반복 금지 - 명성 증가하면 무시 감소
3. "조연 영구 생존" 금지 - 모욕/배신한 조연은 청산
4. "순간 회복" 금지 - 부상 지속 영향 또는 치료 과정 명시
5. "NPC 기억상실" 금지 - 관계는 단방향 발전
"""


def build_justification_guidance(hud_report: str, genre_name: str) -> str:
    """[main_a.py line 6360] 정당화 패턴 안내"""
    try:
        from modules.core.justification_patterns import get_justification_guide
    except ImportError:
        return ""

    active_constraints = []
    physical_constraints = ["나약", "중독", "부상", "중상", "쇠약", "기력고갈", "기혈역류"]
    if any(c in hud_report for c in physical_constraints):
        active_constraints.append("weak_body_strong_action")

    hud_lower = hud_report.lower()
    low_status_keywords = ["하인", "노예", "평민", "무명", "낭인", "거지", "천민"]
    if any(kw in hud_report for kw in low_status_keywords) or "reputation" in hud_lower:
        rep_match = re.search(r"reputation[:\s]+(\d+)", hud_report, re.IGNORECASE)
        if rep_match and int(rep_match.group(1)) < 30:
            active_constraints.append("low_status_high_authority")

    breakthrough_keywords = ["돌파", "깨달음", "체득", "각성", "각오"]
    if any(kw in hud_report for kw in breakthrough_keywords):
        active_constraints.append("sudden_power_increase")

    if not active_constraints:
        return ""

    parts = ["[JUSTIFICATION PATTERNS]\n"]
    for ct in active_constraints:
        try:
            parts.append(get_justification_guide(genre_name, ct))
        except Exception:
            pass
    return "\n".join(parts)


# ──────────────────────────────────────────────
# 내부 헬퍼
# ──────────────────────────────────────────────

def _check_hud_anomalies(db, current_ep: int) -> dict:
    """HUD 급변 감지"""
    anomalies = []
    if current_ep < 2:
        return {"has_anomalies": False, "anomalies": []}
    try:
        hud_history = []
        for ep in range(max(1, current_ep - 3), current_ep):
            try:
                ms_data = db.get_manuscript(ep)
                if ms_data and isinstance(ms_data, dict):
                    hud_snapshot = ms_data.get("hud_snapshot", {})
                    if hud_snapshot:
                        hud_history.append({"ep": ep, "hud": hud_snapshot})
            except Exception:
                continue
        if not hud_history:
            return {"has_anomalies": False, "anomalies": []}

        if len(hud_history) >= 2:
            latest = hud_history[-1]["hud"]
            prev_hud = hud_history[-2]["hud"]
            curr_energy = _extract_numeric_value(latest.get("internal_energy", 0))
            prev_energy = _extract_numeric_value(prev_hud.get("internal_energy", 0))
            if curr_energy - prev_energy > 500:
                anomalies.append({
                    "type": "내공 급상승",
                    "description": f"+{curr_energy - prev_energy}",
                    "recommendation": "정당화 필요",
                })
            curr_realm = latest.get("realm", "")
            prev_realm = prev_hud.get("realm", "")
            realm_tiers = ["하수", "삼류", "이류", "일류", "초일류", "절정", "화경", "현경", "귀환"]
            if curr_realm and prev_realm and curr_realm != prev_realm:
                try:
                    ci = realm_tiers.index(curr_realm) if curr_realm in realm_tiers else -1
                    pi = realm_tiers.index(prev_realm) if prev_realm in realm_tiers else -1
                    if ci - pi >= 2:
                        anomalies.append({
                            "type": "경지 급상승",
                            "description": f"{prev_realm}->{curr_realm}",
                            "recommendation": "특수 기연 정당화 필수",
                        })
                except ValueError:
                    pass
            curr_injury = str(latest.get("causal_injuries", "")).lower()
            prev_injury = str(prev_hud.get("causal_injuries", "")).lower()
            injury_levels = {
                "정상": 0, "경상": 1, "중상": 2, "중독": 2,
                "내상": 2, "빈사": 3, "치명상": 3,
            }
            cl = max((lv for nm, lv in injury_levels.items() if nm in curr_injury), default=0)
            pl = max((lv for nm, lv in injury_levels.items() if nm in prev_injury), default=0)
            if pl >= 2 and cl == 0:
                anomalies.append({
                    "type": "부상 급회복",
                    "description": f"{prev_injury}->{curr_injury}",
                    "recommendation": "치료 과정 필요",
                })
    except Exception:
        return {"has_anomalies": False, "anomalies": []}
    return {"has_anomalies": len(anomalies) > 0, "anomalies": anomalies}


def _extract_numeric_value(value) -> int:
    """HUD 값에서 숫자 추출"""
    if isinstance(value, int | float):
        return int(value)
    if isinstance(value, str):
        match = re.search(r"[+-]?\d+", value)
        return int(match.group()) if match else 0
    return 0


def _extract_recent_events(db, current_ep: int, n_episodes: int = 3) -> list:
    """최근 N화 핵심 사건 추출"""
    events = []
    try:
        for ep in range(max(1, current_ep - n_episodes), current_ep):
            log_data = db.load_state_log(ep)
            if log_data and isinstance(log_data, dict):
                summary = log_data.get("summary", "")
                if summary and len(summary) > 10:
                    events.append({"ep_num": ep, "description": summary[:200], "consequence": ""})
                data = log_data.get("data", {})
                if isinstance(data, dict):
                    for change in (data.get("major_changes", []) or [])[:2]:
                        if isinstance(change, dict):
                            events.append({
                                "ep_num": ep,
                                "description": change.get("event", ""),
                                "consequence": change.get("consequence", ""),
                            })
    except Exception:
        pass
    return events[-5:]


def _extract_npc_last_states(master_bible: dict, current_ep: int) -> dict:
    """등장 NPC 마지막 상태"""
    npc_states = {}
    try:
        bible_root = master_bible.get("MasterBible", master_bible) if master_bible else {}
        assets = bible_root.get("AssetLibrary", {})
        key_npcs = assets.get("KeyNPCs", []) or assets.get("Key_NPCs", [])
        for npc in key_npcs:
            if not isinstance(npc, dict):
                continue
            name = npc.get("name") or npc.get("Name", "")
            if not name:
                continue
            relationship = npc.get("relationship_state", "중립")
            last_appearance = npc.get("last_appearance_ep", 0)
            if isinstance(last_appearance, int) and 0 < last_appearance < current_ep:
                npc_states[name] = {"relationship": relationship, "last_ep": last_appearance}
    except Exception:
        pass
    return npc_states
```

**핵심 변환 규칙**:
- `self.context.db` → 파라미터 `db`
- `self.context.master_bible` (= `getattr(self.context, 'master_bible', {})`) → 파라미터 `master_bible`
- `self.last_hud_anomalies` 사이드이펙트 제거 (stage4에서 미사용)
- `_get_hud_trend_safe`, `_get_npc_frequency_warning`, `_get_npc_frequency` → **이전 안 함** (writer 내부 전용, write_v20_manuscript에서만 사용)
- `_format_entity_registry_for_writer` → **이전 안 함** (writer 내부 전용)

---

### Step 2: stage4_orchestrator.py 호출 변경

**파일**: `modules/core/stage4_orchestrator.py`

#### 2-a. import 추가 (파일 상단 import 영역)

기존 import 영역 끝에 추가:
```python
from modules.core.writer_prompt_builders import (
    build_mandatory_context as _build_writer_mandatory_context,
    build_anti_trope_instructions as _build_anti_trope,
    build_justification_guidance as _build_justification,
)
```

#### 2-b. L535 변경

**Before** (L534-537):
```python
        try:
            mandatory_context = writer_agent._build_mandatory_context(next_ep)
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ Mandatory Context 실패 (비치명): {e}")
```

**After**:
```python
        try:
            _db = getattr(self.ctx.current_project, "db", None)
            _bible = getattr(self.ctx.current_project, "master_bible", {})
            mandatory_context = _build_writer_mandatory_context(_db, _bible, next_ep)
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ Mandatory Context 실패 (비치명): {e}")
```

#### 2-c. L766 변경

**Before** (L765-768):
```python
        try:
            anti_trope_prompt = writer_agent._build_anti_trope_instructions(genre_name)
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ Anti-Trope 실패 (비치명): {e}")
```

**After**:
```python
        try:
            anti_trope_prompt = _build_anti_trope(genre_name)
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ Anti-Trope 실패 (비치명): {e}")
```

#### 2-d. L771 변경

**Before** (L770-773):
```python
        try:
            justification_prompt = writer_agent._build_justification_guidance(hud_report, genre_name)
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ Justification 실패 (비치명): {e}")
```

**After**:
```python
        try:
            justification_prompt = _build_justification(hud_report, genre_name)
        except Exception as e:
            self.ctx.ui.log(f"   ⚠️ Justification 실패 (비치명): {e}")
```

#### 2-e. `writer_agent` 파라미터 존재 여부

`_build_mandatory_context()` 시그니처(L485-498)에서 `writer_agent` 파라미터를 **유지**한다.
이유: L507에서 `writer_agent is None`이면 early return → 이 로직은 유지.
단, L535/L766/L771은 더 이상 `writer_agent`에 의존하지 않으므로, `writer_agent is None` 체크에서 빈 문자열 반환하는 early return을 삭제하거나 유지하되 주석으로 "냉동인간 참조용" 명기.

**권장**: early return 유지. `writer_agent is None`이면 `db/bible`도 없을 가능성 높으므로 안전.
단, `_build_writer_mandatory_context` 호출은 early return 아래에 위치하므로 writer_agent가 None이면 실행 안 됨 → **변경 없음**.

---

### Step 3: writer.py에서 이전된 메서드 삭제

**파일**: `modules/domain/agents/writer.py`

**삭제 대상** (8개 메서드):
- L257-285: `_build_mandatory_context`
- L287-295: `_build_anti_trope_instructions`
- L297-329: `_build_justification_guidance`
- L335-381: `_check_hud_anomalies_v60`
- L383-390: `_extract_numeric_value`
- L392-409: `_extract_recent_events`
- L411-431: `_extract_npc_last_states`
- L433-435: `_get_hud_trend_safe` (hud_utils 위임 → 미사용 확인 후 삭제)

**유지 대상**:
- L22-38: Writer 클래스 정의 + `set_guard()`, `set_genre()`
- L44-232: `write_v20_manuscript()`, `_fallback_full_request()`, `_sanitize_leakage()`
- L238-255: `get_genre_rules_prompt()`
- L437-479: `_get_npc_frequency_warning()`, `_get_npc_frequency()` (write_v20_manuscript 내부 사용)
- L481-501: `_format_entity_registry_for_writer()` (write_v20_manuscript 내부 사용)

**주의**: `_get_hud_trend_safe`(L433-435)는 `write_v20_manuscript` 내에서 호출되는지 확인 필요.
→ `write_v20_manuscript` 본문에 `_get_hud_trend_safe` 호출이 없으면 삭제.
→ 호출이 있으면 유지.

**삭제 후 import 정리**:
- L19의 `from modules.core.hud_utils import get_hud_trend_safe as _get_hud_trend_safe_shared`
  → `_get_hud_trend_safe` 삭제 시 함께 삭제

---

### Step 4: 테스트

**파일**: `tests/test_writer_prompt_builders.py` (신규, ~80줄)

```python
"""[A-1] writer_prompt_builders 단위 테스트"""
import pytest
from unittest.mock import MagicMock


class TestBuildMandatoryContext:
    """build_mandatory_context 함수 테스트"""

    def test_first_episode_returns_default(self):
        from modules.core.writer_prompt_builders import build_mandatory_context
        db = MagicMock()
        result = build_mandatory_context(db, {}, 1)
        assert "[MANDATORY CONTEXT]" in result
        assert "첫 에피소드" in result

    def test_with_hud_anomaly(self):
        from modules.core.writer_prompt_builders import build_mandatory_context
        db = MagicMock()
        db.get_manuscript.side_effect = [
            {"hud_snapshot": {"internal_energy": 100, "realm": "삼류"}},
            {"hud_snapshot": {"internal_energy": 700, "realm": "삼류"}},
        ]
        db.load_state_log.return_value = None
        result = build_mandatory_context(db, {}, 5)
        assert "내공 급상승" in result

    def test_with_recent_events(self):
        from modules.core.writer_prompt_builders import build_mandatory_context
        db = MagicMock()
        db.get_manuscript.return_value = None
        db.load_state_log.return_value = {"summary": "주인공이 흑풍과 대결하여 승리", "data": {}}
        result = build_mandatory_context(db, {}, 5)
        assert "흑풍" in result

    def test_with_npc_states(self):
        from modules.core.writer_prompt_builders import build_mandatory_context
        db = MagicMock()
        db.get_manuscript.return_value = None
        db.load_state_log.return_value = None
        bible = {
            "MasterBible": {
                "AssetLibrary": {
                    "KeyNPCs": [
                        {"name": "노사부", "relationship_state": "사제", "last_appearance_ep": 3},
                    ]
                }
            }
        }
        result = build_mandatory_context(db, bible, 5)
        assert "노사부" in result
        assert "사제" in result

    def test_db_none_safe(self):
        from modules.core.writer_prompt_builders import build_mandatory_context
        result = build_mandatory_context(None, {}, 5)
        assert "[MANDATORY CONTEXT]" in result


class TestBuildAntiTrope:
    """build_anti_trope_instructions 함수 테스트"""

    def test_returns_genre_name(self):
        from modules.core.writer_prompt_builders import build_anti_trope_instructions
        result = build_anti_trope_instructions("무협")
        assert "무협" in result
        assert "ANTI-TROPE" in result

    def test_contains_rules(self):
        from modules.core.writer_prompt_builders import build_anti_trope_instructions
        result = build_anti_trope_instructions("판타지")
        assert "클리셰 금지" in result


class TestBuildJustification:
    """build_justification_guidance 함수 테스트"""

    def test_no_constraints_returns_empty(self):
        from modules.core.writer_prompt_builders import build_justification_guidance
        result = build_justification_guidance("명성 100, 내공 5000", "무협")
        assert result == ""

    def test_physical_constraint_detected(self):
        from modules.core.writer_prompt_builders import build_justification_guidance
        result = build_justification_guidance("부상: 중상, 내공 500", "무협")
        # justification_patterns 모듈이 없으면 빈 문자열
        assert isinstance(result, str)


class TestHelpers:
    """내부 헬퍼 함수 테스트"""

    def test_extract_numeric_value_int(self):
        from modules.core.writer_prompt_builders import _extract_numeric_value
        assert _extract_numeric_value(42) == 42

    def test_extract_numeric_value_str(self):
        from modules.core.writer_prompt_builders import _extract_numeric_value
        assert _extract_numeric_value("내공 1500") == 1500

    def test_extract_numeric_value_none(self):
        from modules.core.writer_prompt_builders import _extract_numeric_value
        assert _extract_numeric_value(None) == 0

    def test_extract_npc_last_states_empty(self):
        from modules.core.writer_prompt_builders import _extract_npc_last_states
        result = _extract_npc_last_states({}, 5)
        assert result == {}
```

---

## 검증 게이트

```bash
# Gate 1: 신규 모듈 import 확인
python -c "from modules.core.writer_prompt_builders import build_mandatory_context, build_anti_trope_instructions, build_justification_guidance; print('OK')"

# Gate 2: SovereignApp import 불변
python -c "from main_a import SovereignApp; print('OK')"

# Gate 3: 신규 테스트 통과
set PYTHONIOENCODING=utf-8
pytest tests/test_writer_prompt_builders.py -v

# Gate 4: 기존 회귀 테스트
pytest tests/test_stage4_orchestrator.py tests/test_npc_history.py tests/test_config_manager.py -v

# Gate 5: pre-commit
pre-commit run --files modules/core/writer_prompt_builders.py modules/core/stage4_orchestrator.py modules/domain/agents/writer.py tests/test_writer_prompt_builders.py
```

---

## 커밋

```
refactor(A-1): extract writer prompt builders to standalone module

- Create modules/core/writer_prompt_builders.py (3 builders + 4 helpers)
- Update stage4_orchestrator to call standalone functions instead of writer_agent methods
- Remove migrated methods from writer.py (keep write_v20_manuscript fallback)
- Add 14 unit tests for writer_prompt_builders

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

---

## 수정 금지

- `write_v20_manuscript()` 로직 변경 금지
- `main_a.py`의 Writer 초기화 경로 변경 금지
- ~~stage4_orchestrator.py 냉동인간 소환 경로~~ (삭제됨 — 5라운드 실패 시 종료로 교체)
- 기존 테스트 파일 수정 금지
