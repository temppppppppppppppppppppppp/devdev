# TF-60: Post-Audit Cleanup — 런타임 잔여 + Arc 검수 + 로깅 보완 + NC-1 S2 확장

> TF-59 감리 후 잔여 전량 처리. 6개 터미널 병렬.

---

## 이슈 요약

| # | 이슈 | 심각도 | 터미널 |
|---|------|--------|--------|
| 1 | Ruff violations 9건 | P2 | T1 |
| 2 | vec_memory 테스트 3건 실패 | P1 | T2 |
| 3 | four_phase_error: dict in str list | P2 | T3 |
| 4 | duration_ms 0건 | 자연해결 | — |
| 5 | Arc 위치 디테일 과잉 복사 | P2 | T4 |
| 6 | Arc 3 WTI 시세 시간 정지 | P2 | #5 해결 시 자연 해결 |
| 7 | 정신력(%) 무협 잔재 | P2 | T4 |
| 8 | llm_calls thinking_snippet 컬럼 누락 | P1 | T5 |
| 9 | director_selections Stage 2 미기록 | P1 | T5 |
| 10 | stage_attempts generation_method NULL | P2 | T5 |
| 11 | pass_rate_monitor duration_ms/token_cost 0 | P2 | T5 |
| 12 | Arc 4 금 수익 산술 오류 (NC-1 S2 확장) | P1 | T6 |

---

## 터미널 1 오더: Ruff 9건

**목표**: `ruff check modules/ config/ tests/ main_a.py --exclude modules/api --exclude tests/test_api*` → 0 errors

**작업**:

```bash
cd "C:/Users/wjjo/Desktop/글도비"
ruff check modules/ config/ tests/ main_a.py --fix --exclude modules/api --exclude "tests/test_api*" --exclude "tests/test_risk*" --exclude "tests/test_run_*"
```

이후 수동 1건:
- `modules/domain/agents/block_enricher.py:22` — E402 (import not at top)
- 해결: `from .base_agent import BaseAgent` import를 `_threshold` import 위로 이동하거나, `_BLOCK_AUDIT_PASS_SCORE = _threshold(...)` 정의를 BaseAgent import 아래로 이동

**테스트**: `pytest tests/ -q --ignore=tests/test_vec_memory.py` 전량 통과 확인

**감리 체크리스트**:
- [ ] `ruff check modules/ config/ tests/ main_a.py --exclude modules/api --exclude tests/test_api*` → 0 errors
- [ ] block_enricher.py E402 해결
- [ ] 기존 테스트 전량 통과

---

## 터미널 2 오더: vec_memory 테스트 3건

**목표**: `pytest tests/test_vec_memory.py -q` → 0 failed

**파일**: `modules/core/vec_memory.py`, `tests/test_vec_memory.py`

**실패 상세**:

1. **TestKNNSearch::test_retrieve_high_res_context** — sqlite-vec KNN 쿼리에서 `k=?` 제약 누락. 에러: `A LIMIT or 'k = ?' constraint is required on vec0 knn queries`
2. **TestEmbeddingKeywordFallback::test_embedding_failure_uses_keyword_fallback** — `assert '무공' in result` 실패. sparse 경로만 결과 반환, keyword fallback 내용 누락
3. **TestHybridRetrieval::test_d2_dense_log_format** — `path=dense` 로그 기대하나 실제 `path=hybrid` + `path=fallback_entry`만 출력

**작업**:
1. `vec_memory.py`에서 KNN 쿼리 빌드하는 모든 경로를 확인 — `vec0` 테이블 SELECT에서 `k=?` 파라미터가 항상 포함되는지 점검
2. KNN 실패 시 fallback 분기에서 keyword 검색이 실제로 결과를 반환하는지 확인
3. `path=dense` vs `path=hybrid` 로깅 분기 조건 확인 — 테스트 기대값과 실제 동작 동기화
4. 테스트 수정이 필요하면 테스트 기대값을 현재 코드 동작에 맞춤 (코드가 올바른 경우)
5. 코드가 잘못된 경우 코드 수정

**감리 체크리스트**:
- [ ] `pytest tests/test_vec_memory.py -q` → 0 failed
- [ ] KNN 쿼리에 k 파라미터 항상 포함
- [ ] hybrid/dense/fallback 경로 구분 정상

---

## 터미널 3 오더: dict in str list 방어

**목표**: LLM 응답 유래 리스트의 join 경로에서 dict 항목으로 인한 TypeError 방지

**증상**: Arc 3 첫 시도에서 `sequence item 0: expected str instance, dict found` 에러 (runtime_audit.jsonl L7)

**파일**: 아래 4파일에서 `".join(` 패턴 전수 조사

1. `modules/domain/agents/four_phase_arc_generator.py` — 15개 join 경로
2. `modules/domain/agents/arc_ensemble.py` — items_acquired 처리 경로
3. `modules/domain/agents/constraint_compiler.py` — 아이템/수여물 수집
4. `modules/domain/agents/arc_draft_validator.py` — 검증 경로

**작업**:
1. 각 파일에서 `grep -n '\.join(' FILE` 실행
2. join의 입력 리스트가 LLM 응답(arc, state_constraints, equipment, items 등)에서 온 경우 `[str(x) for x in items]` 방어 추가
3. 이미 `str()` 방어가 있는 곳(예: arc_ensemble.py L625 `_acq_strs`)은 스킵
4. 테스트 1개 추가: dict 항목이 포함된 리스트 join 시 에러 없음 확인

**감리 체크리스트**:
- [ ] LLM 응답 유래 리스트의 join에 str() 방어 추가 (변경 지점 목록 제출)
- [ ] dict 항목 포함 리스트 join 시 에러 없음 (테스트 1개)
- [ ] 기존 테스트 전량 통과

---

## 터미널 4 오더: Arc 품질 — 위치 트림 + 정신력 금지

### 이슈 5: 위치 디테일 과잉 복사

**증상**: Arc 3 전 4화에서 시작 위치가 동일한 초장문(142자) 반복:
```
서울 강남구 테헤란로, SW인베스트먼트 개인 오피스. 책상 위 3개의 모니터 중
중앙 모니터에 WTI 실시간 시세창이 켜져 있고, 가격은 65.12달러에서 등락을 반복하고 있다.
```

**근본 원인**: `v60_25_auto_correct`가 `joint_docs.final_location`의 장문 묘사를 `arc_start_state.location`에 그대로 복사.

**파일**: `modules/domain/agents/four_phase_arc_generator.py`

**작업**: `_generate_prev_context()`에서 `final_location` 값을 사용할 때, 80자 초과 시 첫 문장(`.` 또는 `,` 기준) 또는 첫 80자로 트림하는 유틸 함수 추가.

```python
def _trim_location(loc: str, max_len: int = 80) -> str:
    """위치 문자열이 과도하게 긴 경우 핵심어만 추출."""
    if not loc or len(loc) <= max_len:
        return loc
    # 첫 문장(마침표 기준) 추출 시도
    dot_pos = loc.find('.')
    if 10 < dot_pos <= max_len:
        return loc[:dot_pos].strip()
    # 마침표 없으면 첫 max_len자
    return loc[:max_len].rstrip() + "…"
```

적용 위치:
- L1136 `final_location = arc_end.get("location") or joint.get("final_location", "알 수 없음")` 직후에 `final_location = _trim_location(final_location)` 추가
- 이 함수는 모듈 상단(또는 클래스 내 staticmethod)에 정의

### 이슈 7: 정신력(%) 무협 잔재

**증상**: 투자물 tactical_doc에 "정신력: 95%" 등 RPG식 수치 표현. `internal_energy`의 비무협 변환체.

**파일**: `config/prompts/analyst.yaml`

**작업**: `ANALYST_SELF_CRITIC_PROMPT` 또는 Phase 2 프롬프트에 비무협 장르용 지시 추가:

현재 `_generate_prev_context()` L1127-1132에서 비무협 시 `final_energy = None` → `✅ 내공:` 라인 출력 스킵. 이건 정상 작동 중.

문제는 LLM이 tactical_doc의 `[시작 상태]`/`[종료 상태]`에 자체적으로 "정신력: N%"를 넣는 것. 이를 억제하려면:

`four_phase_arc_generator.py`의 Phase 2 프롬프트 조립 시 비무협 장르인 경우 다음 지시를 constraint_block에 prepend:
```
⚠️ 이 작품은 {genre} 장르입니다. tactical_doc의 [시작 상태]/[종료 상태]에
"내공", "정신력", "마나" 등의 수치화된 능력치를 사용하지 마세요.
심리 상태는 서술형으로 표현하세요. (예: "극도의 긴장 상태", "자신감 회복")
```

**테스트**:
- 위치 트림: 100자 입력 → 80자 이내 출력 + 핵심 지명 보존 확인 (테스트 1개)
- 비무협 프롬프트: 프롬프트에 수치형 능력치 금지 지시 존재 확인 (테스트 1개)

**감리 체크리스트**:
- [ ] 80자+ 위치가 트림되는 단위 테스트 PASS
- [ ] 핵심 위치 정보(건물명, 지역) 보존
- [ ] 비무협 프롬프트에 정신력 수치 금지 지시 존재
- [ ] 기존 테스트 전량 통과

---

## 터미널 5 오더: 로깅 체계 4건 보완

### 이슈 8: llm_calls thinking_snippet 컬럼 누락 (P1)

**현재 스키마** (`db_manager.py`):
```sql
CREATE TABLE llm_calls (
    ...
    prompt_snippet TEXT,
    response_snippet TEXT
    -- thinking_snippet 누락!
);
```

**파일**: `modules/core/db_manager.py`

**작업**:
1. `llm_calls` 테이블 CREATE 문에 `thinking_snippet TEXT` 컬럼 추가
2. 마이그레이션: `_ensure_columns()` 또는 `ALTER TABLE llm_calls ADD COLUMN thinking_snippet TEXT` 경로에 추가
3. `save_llm_call()` 메서드에 `thinking_snippet` 파라미터 수신 + INSERT 반영

`base_agent.py` L384에서 이미 `_thinking_snippet`을 계산하고 L401에서 `thinking_snippet=_thinking_snippet`으로 전달 중이므로, `save_llm_call()`만 수정하면 됨.

### 이슈 9: director_selections Stage 2 미기록 (P1)

**증상**: decisions.jsonl에 14건 기록. director_selections DB 테이블 0건.

**파일**: `modules/core/stage2_finalizer.py` 또는 `modules/core/stage2_validation_pipeline.py`

**작업**:
1. Stage 2 Director 판정 경로에서 `db.save_director_selection()` 호출 존재 여부 확인
2. 없으면 Director verdict 반환 직후에 저장 로직 추가:
   ```python
   if _db and hasattr(_db, "save_director_selection"):
       _db.save_director_selection(
           ep_num=0,  # Stage 2는 ep_num 대신 arc_num 사용
           round_num=round_num,
           selected_label=selected_label or "",
           selected_strategy=generation_method or "",
           verdict=verdict,
           score=score,
           selection_reason=reason[:200] if reason else "",
           fix_scope=fix_scope or "",
       )
   ```
3. TF-59 #4(DB resolve) 패치 적용 후에도 0건인지 확인 — 호출 자체가 없을 가능성 높음

### 이슈 10: stage_attempts generation_method NULL (P2)

**증상**: 6건 전부 `generation_method=None`

**파일**: `modules/core/stage2_orchestrator.py` 또는 `stage2_finalizer.py`

**작업**:
1. `save_stage_attempt()` 호출 경로를 grep으로 찾기
2. `generation_method` 파라미터가 전달되는지 확인
3. 미전달이면 `four_phase`/`four_phase_asp` 값을 인자로 추가

### 이슈 11: pass_rate_monitor duration_ms/token_cost 0 (P2)

**증상**: 6건 전부 `duration_ms=0`, `token_cost=0.0`

**파일**: `modules/core/stage2_orchestrator.py` (pass_rate_monitor 기록 경로)

**작업**:
1. pass_rate_monitor 기록 시점에서 duration/cost 값 전달 경로 확인
2. `stage_attempts`에는 `duration_ms` 있으므로 동일 시점에 pass_rate에도 전파

**테스트**: DB 스키마 검증 테스트 — `thinking_snippet` 컬럼 존재, `save_llm_call(thinking_snippet=...)` 정상 저장 (테스트 1개)

**감리 체크리스트**:
- [ ] llm_calls 스키마에 thinking_snippet 컬럼 존재
- [ ] save_llm_call()에 thinking_snippet 파라미터 반영
- [ ] Stage 2 Director 판정 → director_selections 저장 경로 존재
- [ ] stage_attempts.generation_method에 값 전달
- [ ] pass_rate_monitor에 duration_ms 전파
- [ ] 기존 테스트 전량 통과

---

## 터미널 6 오더: NC-1 Stage 2 확장 — tactical_doc 산술 검증

### 배경 분석

Arc 4 금 투자 수익에서 산술 오류 발견:
- 15억 × 2배 레버리지 → 30억 포지션
- 금 620→680달러 = 약 9.7% 상승
- 2배 레버리지 수익 = 약 19.4% → 15억 × 19.4% = **2.9억** 수익
- 그러나 원문: "1/3 익절 → 원금5+수익5=10억" → **수익률 100%** (비현실적)

**현재 Stage 2 산술 검증 체계**:

| 계층 | 검증 | 한계 |
|------|------|------|
| LLM `ANALYST_SELF_CRITIC` 항목 7 | LLM이 수식 재계산 | 서술형 산술("1/3 익절→원금5+수익5")을 포착 못함 |
| Python `_check_tactical_arithmetic()` | regex 곱셈/합산 패턴 | InPlace 패치 후에만 실행. 첫 생성 시 미실행 |
| NC-1 `NumericConsistencyChecker` | 9개 Python 검사 | **Stage 4 원고 전용** — Stage 2 미적용 |

**NC-1의 9개 검사 중 Stage 2 tactical_doc에 적용 가능한 것**:

| 검사 | 적용 가능 | 효과 |
|------|----------|------|
| ①FactLedger 교차 | O | tactical_doc 수치 vs FactLedger |
| ②산술 일관성(A+B=C, 레버리지) | **O — 핵심** | Arc 4 오류 직접 포착 |
| ⑥퍼센트 구성 | O | 레버리지/수익률 검증 |
| ⑨레버리지 수익률% | **O — 핵심** | "X달러→Y달러 × N배 → Z%" 검증 |
| ③직함/④"처음" 이벤트/⑦동명이인 | 가능하나 ROI 낮음 | Stage 2에서 빈도 낮음 |
| ⑧도입부 유사도 | N/A | 원고 전용 |

**수정 계획**: NC-1을 Stage 2에서 재사용. 새 메서드 `check_tactical_doc()` 추가.

**파일 1**: `modules/core/numeric_consistency_checker.py`

**작업**: `check_tactical_doc(tactical_doc, ep_num, *, fact_ledger_snapshot=None)` 메서드 추가.

```python
def check_tactical_doc(
    self,
    tactical_doc: str,
    arc_num: int,
    *,
    fact_ledger_snapshot: dict | None = None,
) -> list[dict]:
    """[TF-60] Stage 2 tactical_doc 산술 검증. check()의 서브셋."""
    if not tactical_doc or not tactical_doc.strip():
        return []

    warnings: list[dict] = []
    extracted = self._extract_all_numbers(tactical_doc)

    # 1. FactLedger 교차 (사용 가능한 경우)
    if self._fact_ledger:
        try:
            warnings.extend(self._check_against_ledger(extracted, arc_num))
        except Exception as e:
            logging.debug("[NC-1-S2] FactLedger 교차 실패: %s", e)

    # 2. 산술 일관성 (A+B=C, 레버리지)
    try:
        warnings.extend(self._check_arithmetic(extracted, tactical_doc))
    except Exception as e:
        logging.debug("[NC-1-S2] 산술 검사 실패: %s", e)

    # 3. 퍼센트 구성 검증
    try:
        warnings.extend(self._check_percent_composition(tactical_doc))
    except Exception as e:
        logging.debug("[NC-1-S2] 퍼센트 구성 실패: %s", e)

    return warnings
```

**파일 2**: `modules/core/stage2_finalizer.py` (또는 `stage2_validation_pipeline.py`)

**작업**: Director 심사 직전에 NC-1 S2 검사 실행, 결과를 Director story_context에 advisory로 주입.

```python
# Director 심사 직전
from modules.core.numeric_consistency_checker import NumericConsistencyChecker
_nc1_checker = NumericConsistencyChecker(fact_ledger=_fl, db=_db)
_nc1_warns = _nc1_checker.check_tactical_doc(
    tactical_doc=arc.get("tactical_doc", ""),
    arc_num=arc.get("arc_no", 0),
)
if _nc1_warns:
    _nc1_text = "\n".join(f"  - [{w['severity']}] {w['text']}" for w in _nc1_warns)
    # Director story_context에 advisory 주입
    story_context += f"\n\n[NC-1-S2 산술 검증 경고]\n{_nc1_text}\n위 경고를 참고하여 수치 정합성을 검증하세요."
```

**파일 3**: 기존 `_check_tactical_arithmetic()` (stage2_finalizer.py L76)

**작업**: InPlace 패치 경로뿐 아니라 **첫 생성 경로에서도 실행**하도록 호출 위치 확장. 현재 L540에서만 호출 → Director 심사 전 공통 경로에도 추가.

**테스트**:
1. `check_tactical_doc("15억 × 2배 = 60억", 1)` → 산술 불일치 경고 (15×2=30, 60 아님)
2. `check_tactical_doc("원금5억 + 수익5억 = 10억", 1)` → 일치 (경고 없음)
3. `check_tactical_doc("620달러에서 680달러로 상승, 2배 레버리지, 수익률 100%", 1)` → 경고 (실제 ~19.4%)
4. Stage 2 Director context에 NC-1-S2 경고 주입 확인 (통합 테스트 1개)

**감리 체크리스트**:
- [ ] `check_tactical_doc()` 메서드 존재 (NC-1 서브셋: 산술+FactLedger+퍼센트)
- [ ] Stage 2 Director 심사 전 NC-1-S2 호출
- [ ] advisory-only (REJECT 강제 아님, 대원칙 3 준수)
- [ ] 산술 불일치 테스트 3개 PASS
- [ ] 통합 테스트 1개 PASS
- [ ] 기존 테스트 전량 통과

---

## 감리 종합 (전체 패치 후)

**Pre-flight**:
- [ ] `ruff check modules/ config/ tests/ main_a.py --exclude modules/api --exclude tests/test_api*` → 0 errors
- [ ] `pytest tests/ -q` → 3,531+ passed, **0 failed**

**Arc 품질**:
- [ ] 80자+ 위치가 트림됨
- [ ] 비무협 프롬프트에 정신력 수치 금지 지시

**로깅**:
- [ ] llm_calls.thinking_snippet 컬럼 존재
- [ ] director_selections Stage 2 저장 경로 존재
- [ ] stage_attempts.generation_method 값 전달
- [ ] pass_rate_monitor duration_ms 전파

**NC-1 S2**:
- [ ] check_tactical_doc() 메서드 존재
- [ ] Director advisory 주입 (REJECT 강제 아님)
- [ ] 산술 테스트 3+1개 PASS

**대원칙 검증**:
- [ ] 대원칙 1: Python은 수집만, 판단은 LLM (NC-1 S2는 advisory-only) ✅
- [ ] 대원칙 2: 팩트시트 수정 권한은 LLM만 ✅
- [ ] 대원칙 3: Director 주권주의 (NC-1 S2는 정보 제공만, 감점/REJECT 없음) ✅
