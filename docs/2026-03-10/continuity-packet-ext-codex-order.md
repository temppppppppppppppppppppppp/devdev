# Continuity Packet 확장 코덱스 오더 (관계 변천사 + 수치 이력)

> 작성: 2026-03-10
> 상태: 구현 대기
> 전제: `continuity-packet-codex-order.md`의 CP 구현이 먼저 완료되어야 함
> **⚠️ 필수 선행 수정**: `_extract_blueprint_entities()` 반환 dict에 `"_full_text"` 키 추가 (§3-0 참조)
> 목표: CP에 관계 궤적 + 수치 이력 섹션 추가 — CW가 "어떻게 여기까지 왔는지"를 볼 수 있게

---

## 1. 문제

CP 1차 구현은 NPC **현재 상태**와 **개별 이력**(FactLedger character history, npc_history 변경)을 주입한다.
그러나 두 가지가 빠져 있다:

1. **관계 궤적**: `npc_relationship_history` 테이블에 NPC 간 관계 변화 전체 이력이 저장되어 있으나, CW는 현재 관계만 봄. "적→동맹→연인" 같은 **궤적**을 볼 수 없음.
2. **수치 이력**: `FactLedger.numbers`에 수치 팩트별 history[]가 저장되어 있으나, CW는 현재 값만 봄. "자본금 1억→3억→10억" 같은 **변화 흐름**을 볼 수 없음.

둘 다 **DB에 있지만 LLM이 못 보는** 패턴.

## 2. 해법: CP 섹션 확장

기존 `_build_continuity_packet()` 메서드에 **섹션 5, 6**을 추가한다.

**핵심 원칙:**
- CP 1차 구현과 동일 (LLM 호출 0회, 읽기 전용, 비치명)
- 기존 섹션 1~4의 예산 소비 후 잔여 예산 내에서만 추가
- 예산 상한을 5000자 → 6500자로 상향 (30% 증가, 50K 대비 13%)

## 3. 구현 명세

### 3-0. 필수 선행 수정: `_extract_blueprint_entities` 반환 확장

> **이 수정을 먼저 하지 않으면 섹션 6(수치 이력)에서 NameError 발생.**

현재 `_extract_blueprint_entities()`는 4개 키만 반환한다 (`npcs`, `items`, `plots`, `locations`).
섹션 6에서 Blueprint 텍스트와 수치 키를 매칭하려면 `_full_text`가 필요하다.

**수정 위치**: `stage4_context_builder.py` `_extract_blueprint_entities()` 메서드의 `return` 문

**변경 전** (현재 구현):
```python
        return {"npcs": npcs, "items": items, "plots": plots, "locations": locations}
```

**변경 후**:
```python
        return {"npcs": npcs, "items": items, "plots": plots, "locations": locations, "_full_text": full_text}
```

> `full_text`는 이 메서드 내부 L228(`full_text = "\n".join(text_parts)`)에서 이미 생성되어 있다.
> 기존 소비자(build_mandatory_context 내 CP 주입 코드)는 `npcs`/`items`/`plots`/`locations`만 참조하므로 영향 0.

### 3-A. 관계 궤적 섹션 (`섹션 5`)

**위치**: `_build_continuity_packet()` 내부, 기존 섹션 4(현재 위치) 직후

**로직**:
```python
    # 5. 지목 NPC 관계 궤적 (npc_relationship_history)
    # 주의: 변수명은 CP 1차 구현 컨벤션에 맞춤 (db, used, budget — 언더스코어 없음)
    if db and hasattr(db, "get_relationship_history"):
        rel_lines: list[str] = []
        seen_pairs: set[tuple[str, str]] = set()
        for npc_name in (entities.get("npcs") or [])[:10]:
            try:
                # npc_name 관련 모든 관계 엣지 조회
                edges = db.get_npc_relationship_edges(npc_name)
                for edge in (edges or [])[:5]:
                    if not isinstance(edge, dict):
                        continue
                    n1 = edge.get("npc1", "")
                    n2 = edge.get("npc2", "")
                    pair_key = tuple(sorted([n1, n2]))
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)

                    # 상대가 Blueprint에 등장하는 NPC인 경우에만 궤적 표시
                    other = n2 if n1 == npc_name else n1
                    if other not in (entities.get("npcs") or []):
                        continue

                    # 관계 이력 조회 (시간순, 최대 5건)
                    rel_hist = db.get_relationship_history(n1, n2, limit=5)
                    if not rel_hist:
                        # 이력 없으면 현재 관계만
                        cur_rel = edge.get("relation", "?")
                        rel_lines.append(
                            f"  {n1} ↔ {n2}: {cur_rel} (ep{edge.get('since_ep', '?')}~)"
                        )
                        continue

                    # 궤적 조립: "적→동맹→연인 (ep3→ep15→ep42)"
                    stages: list[str] = []
                    eps: list[str] = []
                    for h in rel_hist:
                        if not isinstance(h, dict):
                            continue
                        new_rel = h.get("new_relation", "")
                        change_ep = h.get("change_ep", "?")
                        if new_rel:
                            stages.append(new_rel)
                            eps.append(str(change_ep))
                    if stages:
                        trajectory = "→".join(stages)
                        ep_flow = "→".join(f"ep{e}" for e in eps)
                        rel_lines.append(f"  {n1} ↔ {n2}: {trajectory} ({ep_flow})")
            except Exception as rel_err:
                logging.debug("[CP] 관계 궤적 조회 실패: %s", rel_err)

        if rel_lines:
            rel_section = "• 관계 변천사\n" + "\n".join(rel_lines[:8])
            if used + len(rel_section) <= budget:
                parts.append(rel_section)
                used += len(rel_section)
```

### 3-B. 수치 이력 섹션 (`섹션 6`)

**위치**: 관계 궤적 섹션 직후, `result = "\n".join(parts)` 직전

**로직**:
```python
    # 6. 지목 수치 팩트 이력 (FactLedger numbers)
    # 주의: 변수명은 CP 1차 구현 컨벤션에 맞춤 (fact_ledger, ledger, used, budget — 언더스코어 없음)
    full_text = entities.get("_full_text", "")  # §3-0에서 추가한 Blueprint 합산 텍스트
    if full_text and fact_ledger:
        nums = ledger.get("numbers", {})
        if nums:
            num_lines = []
            for num_key, num_info in nums.items():
                if not isinstance(num_info, dict):
                    continue
                # Blueprint 텍스트에 수치 키가 등장하는 경우만
                if num_key not in full_text:
                    continue

                cur_val = num_info.get("value", "?")
                unit = num_info.get("unit", "")
                est_val = num_info.get("established_value", "")
                est_ep = num_info.get("established_ep", "?")
                last_ep = num_info.get("last_ep", "?")
                unit_str = f" {unit}" if unit else ""

                # 초기값→현재값 궤적
                if est_val and str(est_val) != str(cur_val):
                    num_lines.append(
                        f"  {num_key}: {est_val}{unit_str}(ep{est_ep}) → {cur_val}{unit_str}(ep{last_ep})"
                    )
                else:
                    num_lines.append(
                        f"  {num_key}: {cur_val}{unit_str} (ep{last_ep} 기준)"
                    )

                # 최근 변경 이력 3건
                history = num_info.get("history", [])
                # history 항목은 string ("ep{N}: {note}" 포맷)
                for h_entry in history[-3:]:
                    if isinstance(h_entry, str):
                        num_lines.append(f"    └ {h_entry[:80]}")

            if num_lines:
                num_section = "• 수치 변화 이력\n" + "\n".join(num_lines[:15])
                if used + len(num_section) <= budget:
                    parts.append(num_section)
                    used += len(num_section)
```

### 3-C. 예산 상향

**위치**: `_build_continuity_packet()` 내부, `budget = 5000` 행

**변경**:
```python
    budget = 6500  # 총 예산 (자) — 섹션 5·6 확장분 반영 (50K 대비 13%)
```

### 3-D. (§3-0으로 이동됨)

## 4. 설계 결정 근거

| 결정 | 이유 |
|------|------|
| 6500자 예산 | 기존 5000 + 관계(~500) + 수치(~1000). 50K 대비 13%로 미미 |
| Blueprint NPC 쌍만 관계 조회 | 전체 NPC 관계는 수백 쌍. Blueprint 등장 NPC끼리만 필터 |
| `seen_pairs` 중복 방지 | A↔B, B↔A 이중 출력 방지 |
| 수치 이력 최근 3건 | 전체 이력은 100건까지 가능. 3건이면 추세 파악 충분 |
| `_full_text` 반환 확장 (§3-0) | entities dict에 `_full_text` 추가 — 기존 소비자(CP 주입 코드)는 `_full_text` 무시하므로 영향 0. **필수 선행** |

## 5. 테스트 요구사항 (`tests/test_continuity_packet.py`에 추가)

```
11. test_build_continuity_packet_relationship_trajectory
    - NPC 2명이 Blueprint에 동시 등장 + relationship_history 3건
    → "→" 궤적 포맷 포함 확인

12. test_build_continuity_packet_relationship_no_overlap
    - NPC A는 Blueprint에 있으나 상대 NPC B는 없음
    → 관계 궤적 미출력 확인

13. test_build_continuity_packet_numeric_history
    - FactLedger numbers에 "자본금" 키 + Blueprint 텍스트에 "자본금" 포함
    → 초기값→현재값 궤적 + 최근 이력 3건 포함 확인

14. test_build_continuity_packet_numeric_no_match
    - FactLedger numbers에 키 있으나 Blueprint 텍스트에 미등장
    → 수치 이력 미출력 확인

15. test_build_continuity_packet_extended_budget
    - NPC 10명 + 관계 + 수치 → 6500자 예산 내 truncation 확인
    - ⚠️ 기존 테스트 #5(test_build_continuity_packet_budget)의 `assert len(packet) <= 5000` → `<= 6500`으로 수정 필요

16. test_extract_blueprint_entities_returns_full_text
    - §3-0 선행 수정 검증: _extract_blueprint_entities 반환값에 "_full_text" 키 포함
    - "_full_text" 값이 비어있지 않은 string인지 확인
```

## 6. 파일 변경 목록

| 파일 | 변경 | 신규/수정 |
|------|------|----------|
| `modules/core/stage4_context_builder.py` | `_build_continuity_packet()` 섹션 5·6 추가 | 수정 |
| `modules/core/stage4_context_builder.py` | `_extract_blueprint_entities()` 반환에 `_full_text` 추가 | 수정 |
| `modules/core/stage4_context_builder.py` | `budget` 5000 → 6500 | 수정 |
| `tests/test_continuity_packet.py` | 테스트 6개 추가 (#11~#16) | 수정 |

## 7. 절대 하지 말 것

- CP 1차 구현(섹션 1~4)의 로직을 변경하지 말 것
- `npc_relationship_edges` / `npc_relationship_history` 테이블을 수정하지 말 것
- `FactLedger._upsert_number()` 등 쓰기 메서드를 호출하지 말 것
- LLM 호출을 추가하지 말 것
- 6500자 예산을 초과하지 말 것
- `_extract_blueprint_entities` 기존 반환 키 4개(npcs/items/plots/locations)를 제거·변경하지 말 것

## 8. 검증 기준

- `pytest tests/test_continuity_packet.py -v` 전량 PASS (기존 10개 + 신규 6개)
- `pytest tests/test_stage4_context_builder.py -v` 기존 테스트 전량 PASS (회귀 0)
- `pytest tests/ -q` 전체 테스트 기존 3,614+ 유지
- `ruff check modules/core/stage4_context_builder.py` 0 violations

## 9. 사이드 이펙트 사전 분석

| 항목 | 영향 |
|------|------|
| Context budget 압축 | 1500자 추가 → 기존 CP보다 약간 더 budget 트리거 가능. 설계된 동작 |
| `_extract_blueprint_entities` 반환 dict 변경 | `_full_text` 키 추가. 기존 소비자(§3-C 주입 코드)는 `npcs`/`items`/`plots`/`locations`만 참조 → 영향 0 |
| DB 쿼리 추가 | `get_npc_relationship_edges` × 최대 10회 + `get_relationship_history` × 최대 5쌍. 인덱스 탐, <5ms 총합 |
| FactLedger 읽기 | `_ledger["numbers"]` dict 순회. 읽기 전용, 뮤테이션 없음 |
| 관계 `sorted()` 키 정합 | `get_relationship_history`가 내부에서 `sorted([npc1, npc2])` 처리. CP 코드에서 별도 sorted 불필요 |
