# TF-59: Stage 2 Pipeline Audit — 실전 데이터 기반 5건 진단

> 2026-03-06 투자물 장르 Stage 2 실행(46분, Arc 5개) 콘솔 로그 + DB 분석 기반

---

## 이슈 요약

| # | 이슈 | 심각도 | 수정 필요 |
|---|------|--------|-----------|
| 1 | Enrich 원본 변형 의혹 | 해소 | NO — 원본 보존 확인됨 |
| 2 | 금지 아이템 투자물 오탐 | P1 | YES |
| 3 | Arc 간 재무 상태 연속성 누락 | P1 | YES |
| 4 | llm_calls DB 0건 | P1 | YES |
| 5 | 분량 미달 임계값 과도 | P2 | YES |

---

## 이슈 1: Enrich — 원본 보존 확인 (수정 불필요)

실전 enrich 로그 6건 (`logs/enrich/enrich_Block*_20260306_*.json`) 전수 비교 결과:
- `content.context/event_villain/solution/reward` 전량 동일
- `genre_ext`(14키), `regression_ext`(7키) 전량 동일
- 신규 추가: `joint_docs`(Arc 경계 메타), `status_shadow`(상태 추적) 2개만

코드 경로: `analyst.py` L1197-1287 → `get_enrich_block_prompt_v30()` → 결과를 원본 dict에 merge

**결론**: Enrich = "원본 보존 + 메타 추가". 변형 없음. 종료.

---

## 이슈 2: 금지 아이템 투자물 오탐 (P1)

**증상**: Arc 2~5 후보 전량 "금지 아이템 획득 시도" → -15점×N → 55~70점

**근본 원인**:
- `constraint_compiler.py:82` `_collect_all_items()`: 모든 이전 Arc의 `items_acquired` 누적
- 투자물에서 "주식", "현금", "계약서" 등이 금지 목록에 올라감
- `items_consumed` (L244 response_schemas.py) 필드가 존재하지만 금지 목록 생성 시 참조하지 않음
- 소비된 아이템도 금지 → 재획득 불가능

**수정**: `_collect_all_items()`에서 `items_consumed` 제외 로직 추가

---

## 이슈 3: Arc 간 재무 상태 연속성 누락 (P1)

**증상**: Arc 2 "전량 매도" → Arc 3 "보유 중" 시작

**근본 원인**:
- `ARC_STATE_SCHEMA` (`response_schemas.py:217-226`): location/equipment/injuries/internal_energy만
- `_generate_prev_context()` (`four_phase_arc_generator.py:1143-1152`): 소지품+부상+위치만
- `_extract_current_state()` (`constraint_compiler.py:168-214`): 재무 필드 없음
- TF-48 실행 상태(L1155-1184)에서 자산/자본금은 주입하지만, **ARC_STATE_SCHEMA 자체**에 필드가 없어 LLM이 구조화 출력 불가

**수정**: ARC_STATE_SCHEMA에 optional 재무 3필드 + prev_context/current_state 주입

---

## 이슈 4: llm_calls DB 0건 (P1)

**증상**: 46분 실행, stage_attempts 6건 기록, llm_calls 0건

**근본 원인**:
- `base_agent.py:302-304` `_resolve_logging_db()`:
  ```python
  return getattr(getattr(self.context, "current_project", None), "db", None)
  ```
- main_a.py에서 Agent에 `ProjectContext` 직접 전달 → `context.current_project` 없음 → None
- 실제 DB는 `context.db`에 있음
- `except Exception: pass` (L403-404) 로 실패 완전 침묵

**수정**: 듀얼 패턴 탐색 + debug 로깅

---

## 이슈 5: 분량 미달 임계값 과도 (P2)

**증상**: Arc 2에서 creative 3,340자, balanced 3,464자 < 3,500자 → 2/3 후보 제거

**근본 원인**: `constants.py:207` `MIN_CHARS_PER_EPISODE = 500` × 7화 = 3,500자 하한

**수정**: 500 → 450 (7화 기준 3,500 → 3,150). 품질 압력은 scoring의 -40 CRITICAL에서 유지.

---

## 코덱스 오더

### 터미널 1: 이슈 #4 — llm_calls DB 0건 (base_agent.py)

**파일**: `modules/domain/agents/base_agent.py`

**변경 1** — L302-304 `_resolve_logging_db()` 듀얼 패턴:

```python
# AS-IS (L302-304)
def _resolve_logging_db(self):
    """Return project DB if available."""
    return getattr(getattr(self.context, "current_project", None), "db", None)

# TO-BE
def _resolve_logging_db(self):
    """Return project DB if available."""
    # Pattern 1: DI context (Stage*Context.current_project.db)
    cp = getattr(self.context, "current_project", None)
    if cp is not None:
        db = getattr(cp, "db", None)
        if db is not None:
            return db
    # Pattern 2: Direct ProjectContext (main_a.py agent init)
    return getattr(self.context, "db", None)
```

**변경 2** — L403-404 silent except → debug 로깅:

```python
# AS-IS (L403-404)
        except Exception:
            pass

# TO-BE
        except Exception as _e:
            logging.debug("[llm_call_log] save failed: %s", _e)
```

**테스트**: `_resolve_logging_db()`가 (1) DI context, (2) ProjectContext 직접 전달, (3) context=None 3경우 정상 반환 확인하는 단위 테스트 1개 추가.

**감리 체크리스트**:
- [ ] ProjectContext 직접 전달 시 DB 반환
- [ ] Stage*Context 전달 시 DB 반환 (기존 경로)
- [ ] bare except pass 제거 → logging.debug 교체
- [ ] 기존 테스트 전량 통과

---

### 터미널 2: 이슈 #2 — 금지 아이템 투자물 오탐 (constraint_compiler.py)

**파일**: `modules/domain/agents/constraint_compiler.py`

**변경** — L82-128 `_collect_all_items()` 끝에서 consumed 아이템 제외:

```python
# AS-IS: return items (L128)

# TO-BE: items_consumed 수집 후 제외
# _collect_all_items 메서드 끝(L128 직전)에 추가:

        # [TF-59] 소비된 아이템은 금지 목록에서 제외 (재획득 허용)
        consumed = set()
        for arc in prev_arcs:
            sc = arc.get("state_constraints") or {}
            for item in (sc.get("items_consumed") or []):
                item_str = str(item) if isinstance(item, dict) else item
                if item_str:
                    consumed.add(item_str)
        # consumed에 있는 아이템 제거
        for c in consumed:
            items.pop(c, None)

        return items
```

**테스트**: prev_arcs에 Arc1(acquired=["주식A"], consumed=["주식A"]) + Arc2 → `_collect_all_items()` 결과에 "주식A" 없음 확인. 무협 케이스(acquired=["천잠비급"], consumed=[]) → 금지 유지 확인. 테스트 2개 추가.

**감리 체크리스트**:
- [ ] consumed 아이템이 금지 목록에서 제외됨
- [ ] 무협 장르 기존 금지 로직 정상 (검/비급은 consumed 안 됨)
- [ ] items_consumed가 None/빈리스트일 때 안전
- [ ] 기존 테스트 전량 통과

---

### 터미널 3: 이슈 #3 — Arc 간 재무 상태 연속성 (3파일)

**파일 1**: `modules/core/response_schemas.py` L217-226

**변경** — `ARC_STATE_SCHEMA`에 optional 재무 3필드 추가:

```python
# AS-IS (L217-226)
ARC_STATE_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "location": types.Schema(type=types.Type.STRING),
        "equipment": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
        "injuries": types.Schema(type=types.Type.STRING, enum=["없음", "정상", "경상", "중상", "위독"]),
        "internal_energy": types.Schema(type=types.Type.INTEGER, minimum=0, maximum=100),
    },
    required=["location", "equipment", "injuries", "internal_energy"],
)

# TO-BE
ARC_STATE_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "location": types.Schema(type=types.Type.STRING),
        "equipment": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
        "injuries": types.Schema(type=types.Type.STRING, enum=["없음", "정상", "경상", "중상", "위독"]),
        "internal_energy": types.Schema(type=types.Type.INTEGER, minimum=0, maximum=100),
        # [TF-59] 재무 상태 연속성 (투자물 등 비무협 장르용, optional)
        "capital": types.Schema(type=types.Type.STRING, description="보유 자본금 (예: '5억원', '$1M')"),
        "total_assets": types.Schema(type=types.Type.STRING, description="총 자산 (자본금+투자자산)"),
        "portfolio_position": types.Schema(type=types.Type.STRING, description="현재 포지션 요약 (예: '삼성전자 1000주 보유')"),
    },
    required=["location", "equipment", "injuries", "internal_energy"],
    # capital/total_assets/portfolio_position은 optional — 무협 등은 생략
)
```

주의: `required`는 기존 4개 유지. 신규 3필드는 optional → 무협 하위호환 보장.

**파일 2**: `modules/domain/agents/four_phase_arc_generator.py` L1143-1152

**변경** — 필수 계승 블록에 재무 필드 추가:

```python
# AS-IS (L1143-1152): 내공/부상/위치/소지품만 출력

# TO-BE: L1151 (소지품) 직후, L1152 (구분선) 직전에 삽입:
        # [TF-59] 재무 상태 계승
        _capital = arc_end.get("capital")
        _total_assets = arc_end.get("total_assets")
        _portfolio = arc_end.get("portfolio_position")
        if _capital or _total_assets or _portfolio:
            lines.append(f"✅ 자본금: {_capital or '미기재'}")
            lines.append(f"✅ 총자산: {_total_assets or '미기재'}")
            lines.append(f"✅ 포지션: {_portfolio or '미기재'}")
```

**파일 3**: `modules/domain/agents/constraint_compiler.py` L168-214

**변경** — `_extract_current_state()` 반환 dict에 재무 필드 포함:

```python
# state_extractor_result 경로 (L180-194): return dict에 추가
                "capital": protagonist.get("capital"),
                "total_assets": protagonist.get("total_assets"),
                "portfolio_position": protagonist.get("portfolio_position"),

# 폴백 경로 (L208-214): return dict에 추가
                "capital": state_constraints.get("arc_end_state", {}).get("capital"),
                "total_assets": state_constraints.get("arc_end_state", {}).get("total_assets"),
                "portfolio_position": state_constraints.get("arc_end_state", {}).get("portfolio_position"),
```

**테스트**: (1) ARC_STATE_SCHEMA에 capital 없이도 검증 통과(하위호환), (2) capital 있으면 prev_context에 출력, (3) _extract_current_state()에 재무 키 포함. 테스트 3개 추가.

**감리 체크리스트**:
- [ ] ARC_STATE_SCHEMA에 capital/total_assets/portfolio_position optional 추가
- [ ] required는 기존 4개만 (하위호환)
- [ ] `_generate_prev_context()` 재무 필드 출력
- [ ] `_extract_current_state()` 재무 키 포함
- [ ] 무협 Arc가 스키마 검증 통과
- [ ] 기존 테스트 전량 통과

---

### 터미널 4: 이슈 #5 — 분량 임계값 하향 (constants.py)

**파일**: `modules/core/constants.py` L207

**변경**:

```python
# AS-IS (L207)
    MIN_CHARS_PER_EPISODE = 500  # 화당 최소 문자 수

# TO-BE
    MIN_CHARS_PER_EPISODE = 450  # 화당 최소 문자 수 [TF-59] 500→450 하향
```

**테스트**: 기존 테스트에서 `MIN_CHARS_PER_EPISODE` 참조하는 곳 확인, 값 변경에 따른 regression 없음 확인.

**감리 체크리스트**:
- [ ] MIN_CHARS_PER_EPISODE == 450
- [ ] 3,464자 tactical doc가 7화 기준 통과 (3,464 > 3,150)
- [ ] 기존 테스트 전량 통과

---

## 감리 종합 체크리스트 (전체 패치 후)

**Pre-flight**:
- [ ] `pytest tests/ -q` — 3,415+ passed
- [ ] `ruff check` — 0 violations

**대원칙 검증**:
- [ ] Python은 수집만, 판단은 LLM (대원칙 1) — 전 패치 준수
- [ ] 팩트시트 수정 권한은 LLM만 (대원칙 2) — 전 패치 준수
- [ ] Director 주권주의 위반 없음 (대원칙 3) — 전 패치 준수

**실 파이프라인 검증 (재실행 후)**:
- [ ] llm_calls 테이블에 레코드 존재
- [ ] Arc 2+ 후보 점수 70+ (금지 아이템 오탐 해소)
- [ ] Arc 간 전환 시 재무 상태 prev_context 표시
