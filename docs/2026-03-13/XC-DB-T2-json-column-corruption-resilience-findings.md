# XC-DB-T2: JSON 컬럼 corruption 복원력

> Track: XC-DB | 타깃: T2 | 생성일: 2026-03-13

---

## 1. 배경

DB에 JSON 텍스트로 저장되는 컬럼이 15개+ 테이블에 존재. `_safe_json_loads()` (L79-84)가 방어 헬퍼로 존재하나, 모든 읽기 경로에 적용되지는 않음.

```python
@staticmethod
def _safe_json_loads(raw, fallback: str):
    try:
        return json.loads(raw or fallback)
    except (json.JSONDecodeError, TypeError, ValueError):
        return json.loads(fallback)
```

---

## 2. Findings

### [XC-DB-005] P2 | JSON 읽기 경로의 비일관적 방어 — _safe_json_loads 미적용 11곳

| 필드 | 내용 |
|------|------|
| ID | XC-DB-005 |
| Severity | P2 (품질 저하) |
| 현상 요약 | JSON 컬럼 읽기 시 `_safe_json_loads()` 대신 `json.loads()` 직접 호출이 11곳 이상이며, 손상 JSON 시 예외 발생 후 동작이 불일치한다 |
| 코드 근거 | 아래 상세 목록 참조 |
| 영향 경계 | anchors, blueprints, state_logs, causal_graph 등 핵심 테이블 |
| 테스트 근거 | `test_db_integrity_recovery.py` 존재하나 JSON 손상 시나리오 미검증 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 읽기 메서드를 `_safe_json_loads()` 통일. 공수: 1시간 |

**`_safe_json_loads()` 적용된 경로** (정상):
- `get_cumulative_bible()` L1274-1310 — `_safe_json_loads(row["new_items"], "[]")` 등
- `get_all_episode_bibles()` L1354-1365
- `get_episode_bibles_before()` L1390-1395
- `get_episode_bible()` L1215-1227 (내부 `_safe_json` 헬퍼 사용)

**`json.loads()` 직접 호출 경로** (손상 시 예외):

| # | 메서드 | 라인 | 동작 |
|---|--------|------|------|
| 1 | `load_anchor()` | L1572 | `json.loads(row["data"])` + except → 빈 dict 반환. **부분 방어** |
| 2 | `load_all_anchors()` | L1583 | `json.loads(row["data"])` + except → 해당 키만 빈 dict. **부분 방어** |
| 3 | `get_blueprint()` | L1105 | `json.loads(row["data"])` + except → None. **부분 방어** |
| 4 | `get_previous_blueprint()` | L1859 | `json.loads(row["data"])` + except → None. **부분 방어** |
| 5 | `get_latest_state()` | L1887 | `json.loads(row["data"])` + except → 빈 dict. **부분 방어** |
| 6 | `load_state_log()` | L1901-1903 | `json.loads(row["data"])` + except → 빈 dict. **부분 방어** |
| 7 | `get_recent_causal_links()` | L1932 | `json.loads(raw)` + except continue. **부분 방어** |
| 8 | `get_causal_links_by_entities()` | L1960 | `json.loads(raw)` + except continue. **부분 방어** |
| 9 | `get_recent_blueprints()` | L2489 | `json.loads(row["data"])` + except → 빈 dict. **부분 방어** |
| 10 | `get_canonical_facts()` | L1630 | `json.loads(d["value_json"])` + except → raw 문자열. **부분 방어** |
| 11 | `get_causal_summary_chain()` | L1913-1917 | **방어 없음** — `r['summary']` 직접 사용 (JSON이 아닌 텍스트 필드) |

**분석**: 대부분의 읽기 경로에 개별 `try/except` 방어가 존재하지만, 방어 방식이 비일관적:
- `load_anchor()`: 손상 → `default` 반환
- `get_blueprint()`: 손상 → `None` 반환
- `get_recent_causal_links()`: 손상 행 → skip (continue)
- `_safe_json_loads()`: 손상 → fallback 문자열 파싱

실제 데이터 손실은 없으나, **일관된 에러 핸들링 패턴 부재**는 유지보수 부담.

---

### [XC-DB-006] P3 | JSON 쓰기 경로 — json.dumps() 실패 미방어 (비현실적)

| 필드 | 내용 |
|------|------|
| ID | XC-DB-006 |
| Severity | P3 (코드 스멜) |
| 현상 요약 | `json.dumps()` 호출 시 직렬화 불가 객체(예: datetime, bytes)가 전달되면 TypeError 발생하나, 대부분의 쓰기 경로에서 미방어 |
| 코드 근거 | `db_manager.py:1547` `save_anchor()` — `json_data = json.dumps(data, ensure_ascii=False)`. `data`에 직렬화 불가 객체 포함 시 전체 anchor 저장 실패. |
| 영향 경계 | LLM 응답 파싱 결과가 예상치 못한 타입을 포함할 가능성. 그러나 현재 시스템에서 모든 LLM 응답은 JSON 파싱 후 dict/list/str/int/float만 포함하므로 **발생 가능성 극히 낮음**. |
| 테스트 근거 | N/A |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | `default=str` 옵션 추가 고려. 낮은 우선순위. |

**쓰기 경로 전수**:
- `save_anchor()` L1547: `json.dumps(data, ensure_ascii=False)` — except 존재, return False
- `save_episode_bible()` L1166-1176: `json.dumps(...)` 10회 — 상위 except 존재
- `save_state_log_with_summary()` L1872: `json.dumps(data_dict, ...)`
- `save_blueprint()` L1846: `json.dumps(data_dict, ...)`
- `save_causal_links()` L2020: `json.dumps(normalized_link, ...)`
- `commit_episode_factory()` L2056-2063: `json.loads` (읽기)

대부분 상위 try/except에서 catch되어 **무성 실패 또는 사용자 경고**로 처리됨.

---

### [XC-DB-007] P3 | _safe_json_loads fallback 파싱 — 2단계 파싱의 불필요한 오버헤드

| 필드 | 내용 |
|------|------|
| ID | XC-DB-007 |
| Severity | P3 (코드 스멜) |
| 현상 요약 | `_safe_json_loads()`가 손상 시 `json.loads(fallback)` 재파싱하는데, fallback은 항상 `"[]"` 또는 `"{}"`이므로 상수를 직접 반환하는 것이 더 효율적 |
| 코드 근거 | `db_manager.py:79-84` |
| 영향 경계 | 성능 미미. 코드 명확성 이슈. |
| 테스트 근거 | N/A |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | `return [] if fallback == "[]" else {}` 등으로 최적화 가능. 최저 우선순위. |

---

### [XC-DB-008] P2 | episode_bibles 새 컬럼 읽기 시 safe_get() 함수 중첩 정의

| 필드 | 내용 |
|------|------|
| ID | XC-DB-008 |
| Severity | P2 (품질 저하) |
| 현상 요약 | `get_episode_bible()` L1201과 `get_all_episode_bibles()` L1345에서 동일한 `safe_get()` 내부 함수를 각각 정의하며, row 클로저에 의존하여 예기치 않은 동작 가능성 |
| 코드 근거 | `db_manager.py:1201-1205` (L1201 safe_get은 L1194의 `row` 클로저 참조) 및 L1345-1349 (for 루프 내 `row` 클로저 — Python late binding에 의해 마지막 row 참조 위험). |
| 영향 경계 | `get_all_episode_bibles()` L1345의 `safe_get()`은 for 루프 내에서 정의되므로 각 반복마다 새 함수 객체 생성. Python 클로저 특성상 **정상 동작** (def가 루프 본문 내부이므로 각 iteration의 row를 올바르게 캡처). |
| 테스트 근거 | `test_db_manager.py` 에서 episode_bible 테스트 존재 여부 미확인 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 공통 유틸로 추출. 공수: 15분 |

**PASS 2 재검증**: Python에서 `for row in rows:` 루프 내부에서 `def safe_get(key, default):` 정의 시, 각 iteration마다 새 함수 객체가 생성되고, 클로저가 **현재 시점의 `row`를 캡처**함. 따라서 **실제 버그 아님**. Severity P2 → P3 하향 고려.

---

## 3. 요약

| ID | Severity | 현상 | 실제 위험 |
|----|----------|------|-----------|
| XC-DB-005 | P2 | JSON 읽기 방어 비일관 | LOW (개별 방어 존재) |
| XC-DB-006 | P3 | JSON 쓰기 미방어 | 극히 낮음 |
| XC-DB-007 | P3 | fallback 이중 파싱 | 성능 미미 |
| XC-DB-008 | P2→P3 | safe_get 중첩 정의 | 코드 스멜 (버그 아님) |
