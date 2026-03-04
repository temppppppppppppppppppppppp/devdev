# TF-55b 구현 결과

> 구현일: 2026-03-04

## 수정 내역

| 수정 | 파일 | 위치 | 완료 여부 |
|------|------|------|---------|
| 수정 1: STATIC/DB_NPC_RELATIONSHIP 상수 추가 | context_advisor.py | `RetrievalSources` (line 98~105) | 완료 |
| 수정 2-A: arc_tactical source=STATIC | context_advisor.py | `_build_stage4_slots()` (line 486~495) | 완료 |
| 수정 2-B: scene_context source=STATIC | context_advisor.py | `_build_stage4_slots()` (line 497~499) | 완료 |
| 수정 2-C: relationship_history source=DB_NPC_RELATIONSHIP | context_advisor.py | `_build_stage4_slots()` (line 511~520) | 완료 |
| 수정 2-D: genre_context source=STATIC | context_advisor.py | `_build_stage4_slots()` (line 523~529) | 완료 |
| 수정 3: STATIC/DB_NPC_RELATIONSHIP 핸들러 추가 | stage4_context_builder.py | `_execute_retrieval_plan()` (line 161~206) | 완료 |

## 실제 수정된 코드 (각 수정별 before/after 인용)

### 수정 1: RetrievalSources 상수 추가

```python
# before
class RetrievalSources:
    """Canonical source identifiers for retrieval slots."""

    VEC_MEMORY = "vec_memory"
    DB_NPC_HISTORY = "db_npc_history"
    MANUSCRIPT_DB = "manuscript_db"  # [Phase2-L2]
```

```python
# after
class RetrievalSources:
    """Canonical source identifiers for retrieval slots."""

    VEC_MEMORY = "vec_memory"
    DB_NPC_HISTORY = "db_npc_history"
    MANUSCRIPT_DB = "manuscript_db"  # [Phase2-L2]
    STATIC = "static"  # [TF-55b] query 문자열 자체를 결과로 반환
    DB_NPC_RELATIONSHIP = "db_npc_relationship"  # [TF-55b] npc_relationship_history 테이블 직접 조회
```

### 수정 2-A: arc_tactical source 변경

```python
# before
slots.append(RetrievalSlot("arc_tactical", f"아크 전술 연속성: {tactical[:320]}", priority=2))
```

```python
# after
slots.append(
    RetrievalSlot(
        "arc_tactical",
        f"아크 전술 연속성: {tactical[:320]}",
        source=RetrievalSources.STATIC,
        priority=2,
    )
)
```

### 수정 2-B: scene_context source 변경

```python
# before
slots.append(RetrievalSlot("scene_context", scene_query, priority=2))
```

```python
# after
slots.append(RetrievalSlot("scene_context", scene_query, source=RetrievalSources.STATIC, priority=2))
```

### 수정 2-C: relationship_history source 변경

```python
# before
slots.append(RetrievalSlot("relationship_history", rel_query, priority=2))
```

```python
# after
slots.append(
    RetrievalSlot(
        "relationship_history",
        rel_query,
        source=RetrievalSources.DB_NPC_RELATIONSHIP,
        priority=2,
    )
)
```

### 수정 2-D: genre_context source 변경

```python
# before
slots.append(RetrievalSlot(f"genre_context_{idx}", f"장르 맥락 키워드: {phrase}", priority=3))
```

```python
# after
slots.append(
    RetrievalSlot(
        f"genre_context_{idx}",
        f"장르 맥락 키워드: {phrase}",
        source=RetrievalSources.STATIC,
        priority=3,
    )
)
```

### 수정 3: _execute_retrieval_plan() source 분기 추가

```python
# before (요약)
if source == RetrievalSources.DB_NPC_HISTORY:
    ...
elif source == "manuscript_db":
    ...
else:
    # 벡터 검색
    ...
```

```python
# after (요약)
if source == RetrievalSources.STATIC:
    result = query_text
elif source == RetrievalSources.DB_NPC_RELATIONSHIP:
    db = getattr(self.ctx, "db", None)
    ...
    _rows = db.get_relationship_history(_names[_i], _names[_j], limit=5)
    ...
elif source == RetrievalSources.DB_NPC_HISTORY:
    ...
elif source == "manuscript_db":
    ...
else:
    # 벡터 검색(기존 코드 유지)
    ...
```

## 검증 결과

- 문법 오류: 없음
  - 실행 명령: `python -m py_compile modules/core/context_advisor.py modules/core/stage4_context_builder.py`
- 상수 참조 일치: 예
  - `RetrievalSources.STATIC` / `RetrievalSources.DB_NPC_RELATIONSHIP` 정의 및 사용 확인
- 기존 분기 유지: 예
  - `DB_NPC_HISTORY`, `manuscript_db`, `else(벡터)` 분기 그대로 유지
- 들여쓰기: 정상
  - `_execute_retrieval_plan()`의 기존 `try` 블록 내부 동일 레벨에 신규 분기 삽입 확인

## 체크리스트

- [x] context_advisor.py만 수정 (본 작업 기준, 다른 코드 파일 미수정)
- [x] stage4_context_builder.py만 추가 수정 (본 작업 기준, 다른 코드 파일 미수정)
- [x] 신규 메서드/클래스 추가 없음
- [x] 기존 VEC_MEMORY/DB_NPC_HISTORY/manuscript_db 분기 유지
