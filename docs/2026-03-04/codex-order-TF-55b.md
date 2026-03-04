# Codex Order: TF-55b 구현

> **목적**: VecMemory hits=0 쿼리 4종(8건)을 벡터 검색에서 직접 주입/DB 조회로 전환.
> **수정 파일**: `context_advisor.py`, `stage4_context_builder.py`
> **금지**: 파일 생성/삭제, 위 2개 파일 외 수정, 의미 있는 로직 리팩토링.

---

## 0) 강제 제약

- 위에 명시된 2개 파일만 수정. 다른 파일 수정 금지.
- 각 수정은 지정된 위치에만 적용. 인접 코드 변경 금지.
- 신규 메서드/클래스 추가 금지. 기존 구조 안에서만 수정.
- 테스트 파일 수정 금지.

---

## 배경

`_execute_retrieval_plan()`은 `slot.source`에 따라 분기한다:
- `DB_NPC_HISTORY` → `memory.retrieve_npc_context()` (DB 직접)
- `"manuscript_db"` → `_fetch_manuscript_excerpt()` (DB 직접)
- 그 외 → 벡터 검색 (VEC_MEMORY 기본값)

현재 4종 슬롯이 전부 기본값(VEC_MEMORY)으로 벡터 검색에 빠지는데, 이 데이터는 VecMemory에 없다:

| 슬롯 | 데이터 실제 위치 | 현재 source | 목표 source |
|------|--------------|------------|------------|
| `arc_tactical` | `arc_data["tactical_doc"]` — 이미 context_data에 있음 | VEC_MEMORY | STATIC |
| `scene_context` | `blueprint["scene_breakdown"]` — 이미 context_data에 있음 | VEC_MEMORY | STATIC |
| `relationship_history` | `npc_relationship_history` SQLite 테이블 | VEC_MEMORY | DB_NPC_RELATIONSHIP |
| `genre_context_1/2` | `_GENRE_HINTS[genre]` Python dict — 런타임 상수 | VEC_MEMORY | STATIC |

`STATIC` source = query 문자열 자체가 이미 내용이므로 그대로 반환.
`DB_NPC_RELATIONSHIP` source = `db_manager.get_relationship_history()` 직접 호출.

---

## 수정 1: `context_advisor.py` — RetrievalSources 상수 추가

**위치**: `RetrievalSources` 클래스 (L98~103)

```python
# 현재
class RetrievalSources:
    """Canonical source identifiers for retrieval slots."""

    VEC_MEMORY = "vec_memory"
    DB_NPC_HISTORY = "db_npc_history"
    MANUSCRIPT_DB = "manuscript_db"  # [Phase2-L2]
```

```python
# 수정 후
class RetrievalSources:
    """Canonical source identifiers for retrieval slots."""

    VEC_MEMORY = "vec_memory"
    DB_NPC_HISTORY = "db_npc_history"
    MANUSCRIPT_DB = "manuscript_db"  # [Phase2-L2]
    STATIC = "static"  # [TF-55b] query 문자열 자체를 결과로 반환
    DB_NPC_RELATIONSHIP = "db_npc_relationship"  # [TF-55b] npc_relationship_history 테이블 직접 조회
```

---

## 수정 2: `context_advisor.py` — `_build_stage4_slots()` 슬롯 source 변경

**위치**: `_build_stage4_slots()` 내 4곳. 각각 독립적으로 수정.

### 2-A: arc_tactical 슬롯 (현재 L486)

```python
# 현재
slots.append(RetrievalSlot("arc_tactical", f"아크 전술 연속성: {tactical[:320]}", priority=2))
```

```python
# 수정 후
slots.append(RetrievalSlot("arc_tactical", f"아크 전술 연속성: {tactical[:320]}", source=RetrievalSources.STATIC, priority=2))
```

### 2-B: scene_context 슬롯 (현재 L490)

```python
# 현재
slots.append(RetrievalSlot("scene_context", scene_query, priority=2))
```

```python
# 수정 후
slots.append(RetrievalSlot("scene_context", scene_query, source=RetrievalSources.STATIC, priority=2))
```

### 2-C: relationship_history 슬롯 (현재 L504)

```python
# 현재
slots.append(RetrievalSlot("relationship_history", rel_query, priority=2))
```

```python
# 수정 후
slots.append(RetrievalSlot("relationship_history", rel_query, source=RetrievalSources.DB_NPC_RELATIONSHIP, priority=2))
```

### 2-D: genre_context 슬롯 (현재 L508)

```python
# 현재
slots.append(RetrievalSlot(f"genre_context_{idx}", f"장르 맥락 키워드: {phrase}", priority=3))
```

```python
# 수정 후
slots.append(RetrievalSlot(f"genre_context_{idx}", f"장르 맥락 키워드: {phrase}", source=RetrievalSources.STATIC, priority=3))
```

---

## 수정 3: `stage4_context_builder.py` — `_execute_retrieval_plan()` 핸들러 추가

**위치**: `_execute_retrieval_plan()` 내 source 분기 블록 (현재 L161~206).
기존 `if source == RetrievalSources.DB_NPC_HISTORY:` 블록 **앞에** 2개 분기를 추가한다.

```python
# 현재 구조 (요약)
if source == RetrievalSources.DB_NPC_HISTORY:
    ...
elif source == "manuscript_db":
    ...
else:
    # 벡터 검색
    ...
```

```python
# 수정 후 구조
if source == RetrievalSources.STATIC:
    # [TF-55b] query 문자열 자체가 이미 내용 — 벡터 검색 불필요
    result = query_text
elif source == RetrievalSources.DB_NPC_RELATIONSHIP:
    # [TF-55b] npc_relationship_history 테이블 직접 조회
    db = getattr(self.ctx, "db", None)
    result = ""
    if db:
        # "관계 변화 이력: 한정호:변화, 박성호" 형식에서 이름 추출
        _body = query_text.replace("관계 변화 이력:", "").strip()
        _raw_names = [p.split(":")[0].strip() for p in _body.split(",") if p.strip()]
        _names = [n for n in _raw_names if n]
        _lines: list[str] = []
        for _i in range(len(_names)):
            for _j in range(_i + 1, len(_names)):
                _rows = db.get_relationship_history(_names[_i], _names[_j], limit=5)
                for _row in _rows:
                    _lines.append(
                        f"EP{_row.get('change_ep', '?')} {_row.get('npc1', '')}↔{_row.get('npc2', '')}: "
                        f"{_row.get('old_relation', '')}→{_row.get('new_relation', '')}"
                    )
        result = "\n".join(_lines) if _lines else ""
elif source == RetrievalSources.DB_NPC_HISTORY:
    ...
elif source == "manuscript_db":
    ...
else:
    # 벡터 검색 (기존 코드 그대로)
    ...
```

**주의**: `DB_NPC_RELATIONSHIP` 블록의 `db.get_relationship_history(npc1, npc2, limit=5)` 반환값은 `list[dict]`. 각 dict의 키: `change_ep`, `npc1`, `npc2`, `old_relation`, `new_relation`. `db_manager.py:L1537` 참조.

---

## 검증 기준

수정 완료 후 아래를 직접 확인하고 결과를 보고한다.

1. **문법 오류 없음**: 수정된 2개 파일을 파이썬 문법 기준으로 검토.
2. **상수 참조 정확**: `RetrievalSources.STATIC`, `RetrievalSources.DB_NPC_RELATIONSHIP`이 수정 1에서 추가한 것과 동일한지 확인.
3. **기존 분기 유지**: `DB_NPC_HISTORY`, `manuscript_db`, `else(벡터)` 분기가 수정 전과 동일한지 확인.
4. **들여쓰기**: `_execute_retrieval_plan()` 내부 try 블록과 동일한 들여쓰기 레벨인지 확인.

---

## 보고서 형식 (고정)

출력 파일: `C:/Users/wjjo/Desktop/글도비/docs/2026-03-04/TF-55b-implementation-result.md`

```markdown
# TF-55b 구현 결과

> 구현일: 2026-03-04

## 수정 내역

| 수정 | 파일 | 위치 | 완료 여부 |
|------|------|------|---------|
| 수정 1: STATIC/DB_NPC_RELATIONSHIP 상수 추가 | context_advisor.py | RetrievalSources 클래스 | ✅/❌ |
| 수정 2-A: arc_tactical source=STATIC | context_advisor.py | _build_stage4_slots() | ✅/❌ |
| 수정 2-B: scene_context source=STATIC | context_advisor.py | _build_stage4_slots() | ✅/❌ |
| 수정 2-C: relationship_history source=DB_NPC_RELATIONSHIP | context_advisor.py | _build_stage4_slots() | ✅/❌ |
| 수정 2-D: genre_context source=STATIC | context_advisor.py | _build_stage4_slots() | ✅/❌ |
| 수정 3: STATIC/DB_NPC_RELATIONSHIP 핸들러 추가 | stage4_context_builder.py | _execute_retrieval_plan() | ✅/❌ |

## 실제 수정된 코드 (각 수정별 before/after 인용)

(각 수정의 전후 코드를 정확히 인용)

## 검증 결과

- 문법 오류: 없음/있음 (있으면 상세)
- 상수 참조 일치: 예/아니오
- 기존 분기 유지: 예/아니오
- 들여쓰기: 정상/불일치

## 체크리스트

- [ ] context_advisor.py만 수정 (다른 파일 미수정)
- [ ] stage4_context_builder.py만 추가 수정 (다른 파일 미수정)
- [ ] 신규 메서드/클래스 추가 없음
- [ ] 기존 VEC_MEMORY/DB_NPC_HISTORY/manuscript_db 분기 유지
```
