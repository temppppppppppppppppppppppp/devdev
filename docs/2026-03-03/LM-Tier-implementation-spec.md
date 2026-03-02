# LM-Tier: 장기 기억 + 품질 강화 전면 패치

> **상태**: 미착수 (계획 승인 완료, 구현 대기)
> **기준선**: 3,112 passed, ruff 0 violations, checkpoint `fc7baf3`
> **선행 완료**: B-1-9 거대 함수 2차 분할

---

## 이미 완료 확인된 항목 (작업 불필요)

- TF-31-2/3/4, P0-1(MAX_REVEALS=500), P0-2(established_value), P1-2(MAX_PAIRS=20), P1-3(destroyed=100), P1-4(world_laws=50)

---

## Wave 1 — 독립 작업 3건 (병렬 가능)

### TF-A: `style_extractor.py` bare except 축소

- **파일**: `modules/core/stage0/style_extractor.py` L722
- **현재**: `except Exception as e:`
- **변경**: `except (ImportError, ValueError, RuntimeError) as e:`
- **근거**: MemoryError/SystemExit 등 치명 예외가 묻히는 것 방지
- **줄수**: 1줄 변경
- **테스트**: py_compile + 기존 테스트 통과

### TF-B: 수치 지수 성장 Python 사전 감지 (P1-1)

- **파일**: `modules/core/numeric_drift_advisor.py`
- **변경**: `_detect_exponential_growth()` + `_try_parse_float()` 정적 메서드 추가, `check()` 선두에 호출
- **로직**:
  1. established_value 대비 100배+ → WARNING
  2. history 5연속 50%+ 성장 → WARNING
- **원칙**: Python은 패턴 감지만, 판단은 LLM advisory가 병행 (기존 LLM 경로 유지)
- **줄수**: +60줄
- **테스트 4개** (신규 파일 `tests/test_numeric_drift_exponential.py`):
  - `test_100x_flagged`: established_value 대비 100배 초과 감지
  - `test_no_established_no_flag`: established_value 없으면 스킵
  - `test_5_consecutive_growth`: 5연속 50%+ 성장 감지
  - `test_pre_results_combined`: 두 경고 모두 LLM 프롬프트에 prepend 확인

**구현 상세**:
```python
# check() 메서드 선두에 추가 (L29~51 사이, LLM 호출 전)
pre_warnings = self._detect_exponential_growth(numbers)
# pre_warnings가 있으면 history_text 앞에 prepend

@staticmethod
def _try_parse_float(val) -> float | None:
    """문자열에서 숫자 추출 시도. '100냥' → 100.0"""
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        m = re.search(r"[-+]?\d[\d,]*\.?\d*", val.replace(",", ""))
        if m:
            return float(m.group())
    return None

def _detect_exponential_growth(self, numbers) -> list[str]:
    """Python 사전 감지: 100배+ 급등 or 5연속 50%+ 성장."""
    warnings = []
    for key, entry in (numbers or {}).items():
        if not isinstance(entry, dict):
            continue
        # (1) established_value 대비 100배+
        est = entry.get("established_value")
        cur = entry.get("value")
        est_f = self._try_parse_float(est)
        cur_f = self._try_parse_float(cur)
        if est_f and cur_f and est_f > 0 and cur_f / est_f >= 100:
            warnings.append(f"[Python 사전감지] {key}: 초기값({est}) 대비 현재({cur}) = {cur_f/est_f:.0f}배 급등")
        # (2) 5연속 50%+ 성장
        history = entry.get("history", [])
        if len(history) >= 6:  # 최소 6개 (5개 구간)
            streak = 0
            for i in range(len(history) - 1):
                a = self._try_parse_float(history[i])
                b = self._try_parse_float(history[i + 1])
                if a and b and a > 0 and (b - a) / a >= 0.5:
                    streak += 1
                    if streak >= 5:
                        warnings.append(f"[Python 사전감지] {key}: {streak}연속 50%+ 성장 감지 (지수적 증가 의심)")
                        break
                else:
                    streak = 0
    return warnings
```

### TF-C: fix_scope 전략별 합격률 Director 주입 (A-3 Phase 2)

- **파일**: `modules/core/stage4_interview_round.py` L579 (기존 `[TF7-P1-04]` 블록 직후)
- **변경**: `get_fix_scope_stats()` 호출 → 집계 → `_director_mc_parts`에 주입
- **패턴**: 기존 L567-579 win_rates 주입과 동일 패턴 (try/except, db guard, format, append)
- **줄수**: +25줄
- **테스트 2개** (`tests/test_a3_fix_scope_tracking.py`에 추가):
  - 집계 포맷 검증
  - 빈 데이터 안전성

**구현 상세** (L579 `_director_mandatory_context` 라인 직전에 삽입):
```python
# [A-3 Phase 2] fix_scope 전략별 합격률을 Director에 주입
try:
    if _db is not None and hasattr(_db, "get_fix_scope_stats"):
        _fs_stats = _db.get_fix_scope_stats()
        if _fs_stats and any(v.get("total", 0) > 0 for v in _fs_stats.values()):
            _fs_lines = ["[A-3] fix_scope 전략별 합격률"]
            for _scope, _stat in _fs_stats.items():
                _total = _stat.get("total", 0)
                _pass = _stat.get("pass", 0)
                if _total > 0:
                    _fs_lines.append(f"  - {_scope}: {_pass}/{_total} ({int(_pass/_total*100)}%)")
            _director_mc_parts.append("\n".join(_fs_lines))
except Exception as _fs_err:
    logging.debug(f"[A-3] fix_scope stats fetch 실패 (비치명): {_fs_err}")
```

**db_manager.py `get_fix_scope_stats()` 확인 필요**: 이미 A-3에서 `director_selections` 테이블에 `fix_scope` 컬럼이 추가됨. 집계 메서드가 없으면 추가 필요.

---

## Wave 2 — DB 마이그레이션 2건 (순차)

### TF-D: npc_history reason 컬럼 (P2-2)

- **파일 1**: `modules/core/db_manager.py`
  - L402 뒤: ALTER TABLE 마이그레이션 (`reason TEXT DEFAULT ''`)
  - `insert_npc_change()` (L2246 부근): 시그니처에 `reason=""` 추가 + INSERT 확장
  - `get_npc_history()` (L2270 부근): SELECT에 reason 포함
- **파일 2**: `modules/domain/agents/state_tracker_npc.py` L178 — 호출 시 `reason=""` 전달 (하위호환)
- **줄수**: +15줄
- **테스트 2개** (`tests/test_npc_history.py` 또는 신규):
  - reason round-trip 저장/조회
  - 기본값 빈문자열

**마이그레이션 패턴** (기존 ALTER TABLE 패턴 참고):
```python
# L402 뒤에 추가
try:
    self.cursor.execute("ALTER TABLE npc_history ADD COLUMN reason TEXT DEFAULT ''")
except Exception:
    pass  # 이미 존재
```

### TF-E: HUD Anomaly 활성화

- **파일 1**: `modules/core/db_manager.py`
  - manuscripts 테이블 ALTER TABLE: `hud_snapshot TEXT DEFAULT ''`
  - `save_manuscript()` (L838 부근): `hud_snapshot=None` 파라미터 + JSON 직렬화
  - `get_manuscript()` (L852 부근): hud_snapshot JSON 역직렬화
- **파일 2**: `modules/protocols/db_repository.py` L39 — `save_manuscript` Protocol 시그니처 업데이트
- **파일 3**: `modules/core/stage4_post_processor.py` — `process_pass_result()` 내 `save_manuscript` 호출 시 HUD 스냅샷 전달
  - HUD 소스: `self.ctx.sys.hud.snapshot()` (또는 유사 경로)
- **파일 4**: `modules/domain/agents/chief_writer.py` L1047 — NOTE 주석 갱신
- **줄수**: +35줄
- **핵심**: `_check_hud_anomalies()`는 이미 완전한 로직 보유 (`chief_writer_context.py` L761-790). 데이터 파이프라인만 연결하면 즉시 활성화.
- **테스트 3개**:
  - save/load round-trip
  - JSON 역직렬화
  - 기존 anomaly 테스트 통과

**확인 필요 사항**:
- `save_manuscript()` 현재 시그니처와 INSERT 쿼리 확인
- `get_manuscript()` 현재 반환 형태 확인
- `stage4_post_processor.py`의 `save_manuscript` 호출 지점 확인
- `chief_writer_context.py` L761-790 `_check_hud_anomalies()` 실제 입력 형태 확인
- HUD snapshot 접근 경로 확인 (`self.ctx` 구조)

---

## Wave 3 — 시간 경과 추적 (Wave 2 안정 후)

### TF-F: 누적 경과 시간 추적기 (P2-1)

- **파일 1**: `modules/core/world_state.py`
  - `_INIT_STATE`에 `cumulative_elapsed` 필드 추가 (`{"total_days": 0, "history": []}`)
  - `§12 시간 마커 처리` (L351-376 부근): 누적 로직 추가
  - `_parse_elapsed_days()` 정적 메서드: 한국어 시간 표현 파서
  - `get_cumulative_elapsed()` 공개 메서드
- **파일 2**: `modules/core/narrative_context_formatter.py` — `format()` 내 누적 시간 요약 텍스트 주입
- **줄수**: +80줄 (world_state) + +10줄 (narrative_context_formatter)

**한국어 파서 `_parse_elapsed_days()`**:
```python
@staticmethod
def _parse_elapsed_days(text: str) -> int | None:
    """한국어 시간 표현 → 일수 변환. 실패 시 None."""
    if not text:
        return None
    text = text.strip()
    # 숫자+단위: "3일", "2주", "3개월"
    m = re.search(r"(\d+)\s*(일|주|개월|달|년)", text)
    if m:
        n, unit = int(m.group(1)), m.group(2)
        return {"일": 1, "주": 7, "개월": 30, "달": 30, "년": 365}.get(unit, 1) * n
    # 한국어 수사: "이틀"→2, "사흘"→3, "나흘"→4, "닷새"→5, "엿새"→6, "이레"→7
    korean_nums = {"하루": 1, "이틀": 2, "사흘": 3, "나흘": 4, "닷새": 5, "엿새": 6, "이레": 7}
    for k, v in korean_nums.items():
        if k in text:
            return v
    # 복합: "일주일"→7, "보름"→15, "한 달"→30, "반년"→180
    compounds = {"일주일": 7, "보름": 15, "한 달": 30, "한달": 30, "반년": 180}
    for k, v in compounds.items():
        if k in text:
            return v
    return None
```

**테스트 4개** (신규 `tests/test_cumulative_elapsed.py`):
- `test_parse_numeric`: "3일 후"→3, "2주"→14
- `test_parse_korean_numerals`: "이틀"→2, "사흘"→3
- `test_cumulative_sum`: 다회 업데이트 후 합산 검증
- `test_history_cap_20`: history 리스트 최대 20개 유지

---

## 수정 파일 총괄

| 파일 | TF | 변경 |
|------|-----|------|
| `modules/core/stage0/style_extractor.py` | A | except 축소 (1줄) |
| `modules/core/numeric_drift_advisor.py` | B | 지수 성장 감지 (+60줄) |
| `modules/core/stage4_interview_round.py` | C | fix_scope 주입 (+25줄) |
| `modules/core/db_manager.py` | D+E | ALTER TABLE 2건 + save/get_manuscript 확장 |
| `modules/domain/agents/state_tracker_npc.py` | D | reason 파라미터 전달 |
| `modules/protocols/db_repository.py` | E | Protocol 시그니처 업데이트 |
| `modules/core/stage4_post_processor.py` | E | HUD 스냅샷 전달 |
| `modules/domain/agents/chief_writer.py` | E | NOTE 주석 갱신 |
| `modules/core/world_state.py` | F | 누적 시간 추적 (+80줄) |
| `modules/core/narrative_context_formatter.py` | F | 시간 요약 주입 (+10줄) |
| `tests/` | B,C,D,E,F | ~15개 신규 테스트 |

총 **10파일** + 테스트. **동작 변경**: 기존 기능 0 변경, 순수 기능 추가만.

---

## 검증 절차

각 Wave 완료 후:
```
python -m py_compile <변경 파일>
pytest tests/ -q          # 3,112+ passed
ruff check modules/       # 0 violations
```

최종: pytest 전체 + ruff + CLAUDE.md 업데이트 + 커밋

---

## Deferred (별도 TF로 분리)

| 항목 | 사유 |
|------|------|
| Blueprint 인터리브 자동 모드 | Stage4Context 슬롯 추가 필요, 별도 TF |
| P1-5 장기 반복 감지 | 새 advisory 150줄+, 별도 TF |
| P2-3 VecMemory re-indexing | 200화 실측 데이터 필요 |
