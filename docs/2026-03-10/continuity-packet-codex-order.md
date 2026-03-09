# Continuity Packet 구현 코덱스 오더

> 작성: 2026-03-10
> 상태: 구현 대기
> 목표: 250화 장기 연재에서 장기 기억 열화 방지

---

## 1. 문제

WorldState.get_summary()는 **고정 cap 기반 평탄 투영**이다:

```
생존 NPC → sorted[:30]
사망 NPC → [:20]
관계 → [:20]
아이템 → [:20]
플롯 → [-10:]
타임라인 → [-5:]
```

100화 넘으면 초반 핵심 인물이 30명 밖으로 밀려나고, 200화엔 초반 인과 대부분이 프롬프트에서 사라진다. **저장은 되어 있지만 LLM이 못 본다.**

현재 mandatory_context 조립 순서 (`stage4_context_builder.py:959-1115`):
1. Canonical Constraints (NPC 초기속성 + 수치 참조)
2. 타임라인
3. FactLedger 요약
4. WorldState.get_summary() ← **여기가 평탄 투영**
5. 시리즈/볼륨 요약
6. Treatment genre_ext
7. StateTracker 16종 요약
8. Arc 요약
9. SC Retrieval 결과
10. 기타 (ambient NPC, constraint 등)

## 2. 해법: Continuity Packet

현재 화 Blueprint에 등장하는 엔티티를 기준으로 **지목형 기억**을 별도 패킷으로 조립하여 mandatory_context 상단에 주입한다.

**핵심 원칙:**
- WorldState.get_summary()를 **대체하지 않는다** — 보완한다
- Blueprint가 없으면 패킷을 생성하지 않는다 (폴백: 기존 로직 그대로)
- Python은 데이터 수집만, 판단은 LLM이 (대원칙 1)
- Director 판정을 방해하지 않는다 (대원칙 3)
- LLM 호출 0회 — 순수 Python 데이터 조립

## 3. 구현 명세

### 3-A. 엔티티 추출 (`_extract_blueprint_entities`)

**위치**: `stage4_context_builder.py`에 새 private 메서드

**입력**: `blueprint: dict`

**로직**:
```python
def _extract_blueprint_entities(self, blueprint: dict) -> dict:
    """Blueprint에서 이번 화 관련 엔티티명을 추출한다."""
    if not blueprint or not isinstance(blueprint, dict):
        return {"npcs": [], "items": [], "plots": [], "locations": []}

    # Blueprint 텍스트 전체를 합산
    _text_parts = []
    for key in ("integrated_scenario", "scene_breakdown", "core_tension",
                "expected_ending", "pacing_notes", "target_beat",
                "relationship_changes", "time_flow", "protagonist_state",
                # extra="allow" 대비 fallback 키
                "synopsis", "scenes", "ending_hook", "key_events",
                "npc_appearances", "emotional_arc", "required_items"):
        val = blueprint.get(key)
        if isinstance(val, str):
            _text_parts.append(val)
        elif isinstance(val, list):
            for item in val:
                _text_parts.append(str(item) if not isinstance(item, str) else item)
        elif isinstance(val, dict):
            _text_parts.append(json.dumps(val, ensure_ascii=False))

    _full_text = "\n".join(_text_parts)

    # WorldState에서 전체 NPC 목록 가져와서 Blueprint 텍스트에 등장하는지 매칭
    npcs = []
    if self.ctx.world_state:
        _ws = self.ctx.world_state._state
        all_npcs = set()
        for pool in ("alive_npcs", "dead_npcs"):
            for name in (_ws.get(pool) or {}):
                all_npcs.add(str(name))
        npcs = [n for n in all_npcs if n in _full_text]

    # 아이템: WorldState active_items와 매칭
    items = []
    if self.ctx.world_state:
        _items = self.ctx.world_state._state.get("active_items", {})
        items = [n for n in _items if n in _full_text]

    # 플롯: active_plots와 매칭
    plots = []
    if self.ctx.world_state:
        for p in self.ctx.world_state._state.get("active_plots", []):
            _pname = p.get("plot", "") if isinstance(p, dict) else str(p)
            if _pname and _pname in _full_text:
                plots.append(_pname)

    # 장소: protagonist location + blueprint 내 장소 키워드
    locations = []
    if self.ctx.world_state:
        _prot = self.ctx.world_state._state.get("protagonist", {})
        _loc = _prot.get("location", "")
        if _loc:
            locations.append(_loc)

    return {"npcs": npcs, "items": items, "plots": plots, "locations": locations}
```

### 3-B. 패킷 조립 (`_build_continuity_packet`)

**위치**: `stage4_context_builder.py`에 새 private 메서드

**입력**: `entities: dict` (3-A 반환값)

> `next_ep` 파라미터는 의도적으로 제거 — 본문에서 미사용. 필요 시 로깅용으로 추가 가능.

**출력**: `str` (프롬프트 텍스트, 최대 5000자)

**로직**:
```python
def _build_continuity_packet(self, entities: dict) -> str:
    """이번 화 관련 엔티티의 상세 이력을 지목 조회하여 패킷으로 조립."""
    if not any(entities.values()):
        return ""

    parts = ["=== [Continuity Packet] 이번 화 필수 기억 ==="]
    _budget = 5000  # 총 예산 (자)
    _used = 0

    # 1. 지목 NPC 상세 (WorldState + FactLedger + NPC History)
    _db = getattr(self.ctx.current_project, "db", None)
    for npc_name in entities["npcs"][:10]:  # 최대 10명
        _npc_block = []

        # WorldState 상세
        if self.ctx.world_state:
            _ws = self.ctx.world_state._state
            for pool in ("alive_npcs", "dead_npcs"):
                _info = (_ws.get(pool) or {}).get(npc_name)
                if _info and isinstance(_info, dict):
                    _desc = ", ".join(f"{k}={v}" for k, v in _info.items()
                                     if v and k != "name")
                    _npc_block.append(f"  상태: {_desc[:200]}")
                    if pool == "dead_npcs":
                        _npc_block.append("  ⚠️ 사망 — 행동/대사 등장 금지 (회상/언급만 허용)")

        # FactLedger 관련 항목
        if self.ctx.fact_ledger:
            _fl = self.ctx.fact_ledger
            # FactLedger 내부 키: "characters" (NOT "persons")
            _char_facts = _fl._ledger.get("characters", {}).get(npc_name, {})
            if _char_facts:
                _history = _char_facts.get("history", [])
                # 최근 5건 — history 항목은 string ("ep{N}: {note}" 포맷)
                for entry in _history[-5:]:
                    if isinstance(entry, str):
                        _npc_block.append(f"  [이력] {entry[:100]}")

        # NPC 변경 이력 (npc_history 테이블)
        if _db and hasattr(_db, "get_npc_history"):
            try:
                _hist = _db.get_npc_history(npc_name, limit=3)
                for h in (_hist or []):
                    if isinstance(h, dict):
                        # DB 컬럼: episode_no, field_name, old_value, new_value
                        _npc_block.append(
                            f"  [변경 {h.get('episode_no','?')}화] "
                            f"{h.get('field_name','')}: {str(h.get('old_value',''))[:30]} → "
                            f"{str(h.get('new_value',''))[:30]}"
                        )
            except Exception as _nh_err:
                logging.debug("[CP] npc_history 조회 실패: %s", _nh_err)

        if _npc_block:
            _section = f"• {npc_name}\n" + "\n".join(_npc_block)
            if _used + len(_section) > _budget:
                break
            parts.append(_section)
            _used += len(_section)

    # 2. 지목 플롯 상세
    for plot_name in entities["plots"][:5]:
        _plot_line = f"• 진행 중 플롯: {plot_name}"
        if _used + len(_plot_line) > _budget:
            break
        parts.append(_plot_line)
        _used += len(_plot_line)

    # 3. 지목 아이템 상세
    if entities["items"]:
        _item_line = "• 관련 아이템: " + ", ".join(entities["items"][:10])
        if _used + len(_item_line) <= _budget:
            parts.append(_item_line)
            _used += len(_item_line)

    # 4. 현재 위치
    if entities["locations"]:
        _loc_line = "• 현재 위치: " + ", ".join(entities["locations"][:3])
        if _used + len(_loc_line) <= _budget:
            parts.append(_loc_line)

    result = "\n".join(parts)
    return result[:_budget]
```

### 3-C. 주입 지점

**위치**: `stage4_context_builder.py` `build_mandatory_context()` 메서드 내부

**삽입 위치**: L1064 (Treatment genre_ext 주입) 직후, L1066 (StateTracker 16종 요약) 직전

> **주의**: L959 직후에 insert(0)하면 이후 L973(WorldState), L985(Timeline),
> L1017(FactLedger), L1034(Canonical)의 insert(0)에 밀려 position 4~5가 됨.
> L1064 직후에 insert(0)해야 진짜 최상단 배치.

```python
# === [Continuity Packet] Blueprint 기반 지목형 기억 주입 ===
# 위치: Treatment genre_ext(L1064) 직후, StateTracker(L1066) 직전
# 이 시점 이후에는 insert(0) 호출이 없으므로 진짜 최상단 배치됨
if blueprint:
    try:
        _cp_entities = self._extract_blueprint_entities(blueprint)
        _cp_text = self._build_continuity_packet(_cp_entities)
        if _cp_text:
            _mc_parts.insert(0, _cp_text)
            logging.info(
                "[CP] Continuity Packet 주입 (%d자, NPC %d, 플롯 %d, 아이템 %d)",
                len(_cp_text),
                len(_cp_entities["npcs"]),
                len(_cp_entities["plots"]),
                len(_cp_entities["items"]),
            )
    except Exception as _cp_err:
        logging.warning("[CP] Continuity Packet 생성 실패 (비치명): %s", str(_cp_err)[:80])
```

## 4. 설계 결정 근거

| 결정 | 이유 |
|------|------|
| LLM 호출 0회 | 매화 호출하면 비용+지연. Blueprint 텍스트 매칭으로 충분 |
| WorldState 대체 아님 | get_summary()는 전체 조감도, CP는 이번 화 줌인. 역할이 다름 |
| 5000자 예산 | Gemini 1M 대비 미미. 현재 mandatory_context 총량(~50K) 대비 10% |
| NPC 최대 10명 | Blueprint 1화에 등장하는 NPC는 보통 3~7명. 10이면 충분 |
| L1064 이후 insert(0) 최상단 | 모든 insert(0) 완료 후 삽입해야 진짜 position 0. "이번 화에서 반드시 기억해야 할 사실"이므로 최우선 배치 |
| Blueprint 없으면 스킵 | Stage 4 첫 진입 시 blueprint=None 가능. 기존 로직에 영향 0 |

## 5. 테스트 요구사항

### 5-A. 단위 테스트 (`tests/test_continuity_packet.py`)

```
1. test_extract_blueprint_entities_basic
   - Blueprint에 NPC 이름 3개 포함 → 3개 추출 확인

2. test_extract_blueprint_entities_empty
   - Blueprint=None → 빈 dict 반환

3. test_extract_blueprint_entities_dead_npc
   - 사망 NPC 이름이 Blueprint에 있으면 추출됨 (회상 가능)

4. test_build_continuity_packet_basic
   - NPC 2명 + 플롯 1개 → 패킷 문자열 생성 확인

5. test_build_continuity_packet_budget
   - NPC 20명 → 5000자 예산 내에서 truncation 확인

6. test_build_continuity_packet_empty_entities
   - 빈 entities → 빈 문자열 반환

7. test_build_continuity_packet_with_fact_ledger
   - FactLedger에 NPC 이력 있을 때 최근 5건 포함 확인

8. test_build_continuity_packet_with_npc_history
   - npc_history 테이블에 변경 이력 있을 때 최근 3건 포함 확인

9. test_mandatory_context_includes_packet
   - build_mandatory_context() 호출 시 반환 dict의 "mandatory_context"에
     "[Continuity Packet]" 포함 확인
   - ⚠️ 시그니처 필수 인자 12개 mock 필요:
     next_ep, arc_data, arc_tactical, prev_text, prev_ending,
     hud_report, writer_agent, anchor_sys, s4_genre_type,
     v50_modules_available, blueprint=valid_bp
   - writer_agent과 anchor_sys는 MagicMock으로 충분

10. test_mandatory_context_no_blueprint_no_packet
    - 동일 mock + blueprint=None → CP 미포함 확인
```

### 5-B. 기존 테스트 영향

- `tests/test_stage4_context_builder.py` — build_mandatory_context 호출하는 기존 테스트에 blueprint=None 전달 중이면 영향 없음. blueprint 전달 중이면 CP가 추가되므로 assertion 조정 필요할 수 있음.

## 6. 파일 변경 목록

| 파일 | 변경 | 신규/수정 |
|------|------|----------|
| `modules/core/stage4_context_builder.py` | `_extract_blueprint_entities()` 추가 | 수정 |
| `modules/core/stage4_context_builder.py` | `_build_continuity_packet()` 추가 | 수정 |
| `modules/core/stage4_context_builder.py` | `build_mandatory_context()` 내 CP 주입 3줄 | 수정 |
| `tests/test_continuity_packet.py` | 단위 테스트 10개 | 신규 |

## 7. 절대 하지 말 것

- WorldState.get_summary()의 cap(30/20/20 등)을 변경하지 말 것
- FactLedger.to_summary()를 수정하지 말 것
- LLM 호출을 추가하지 말 것
- build_mandatory_context()의 기존 블록 순서를 변경하지 말 것
- 5000자 예산을 초과하지 말 것
- Director/CW 프롬프트를 수정하지 말 것

## 8. 검증 기준

- `pytest tests/test_continuity_packet.py -v` 전량 PASS
- `pytest tests/test_stage4_context_builder.py -v` 기존 테스트 전량 PASS (회귀 0)
- `pytest tests/ -q` 전체 테스트 기존 3,614+ 유지
- `ruff check modules/core/stage4_context_builder.py` 0 violations
