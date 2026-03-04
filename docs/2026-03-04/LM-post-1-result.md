# LM-post-1 구현 결과

> 구현일: 2026-03-04

## 수정 내역

| Phase | 파일 | 작업 | 완료 여부 |
|-------|------|------|---------|
| 1 | `config/settings/validation.yaml` + `modules/validation/validation_orchestrator.py` | retrospective lookback 5→10 + YAML 연동 | 완료 |
| 2 | `modules/core/db_manager.py` | `get_recent_causal_links()` 추가 | 완료 |
| 3 | `modules/core/stage4_post_processor.py` | causal_graph Read + Director MC 보조 컨텍스트 주입(비치명) | 완료 |
| 4 | `tests/test_lm_post1.py` | 신규 테스트 7개 추가 | 완료 |

## Phase별 상세

### Phase 1

- `validation.yaml`에 `retrospective.lookback_episodes: 10` 추가
- `ValidationOrchestrator`의 Retrospective 초기화 하드코딩 제거
  - before: `RetrospectiveValidator(..., lookback_episodes=5)`
  - after: `_threshold("retrospective.lookback_episodes", 10)` 로드 + `int` 안전 변환 후 주입

### Phase 2

- `DBManager.get_recent_causal_links(current_ep, lookback=10)` 추가
  - 범위: `[current_ep-lookback, current_ep)`
  - 정렬: `ORDER BY ep_num`
  - malformed JSON row는 skip
  - 실패 시 비치명 `[]` 반환 + debug 로그

### Phase 3

- `stage4_post_processor.py`의 causal dual-write 직후에 causal read 보강
  - `get_recent_causal_links(next_ep, lookback=10)` 호출
  - cause/effect 조합으로 최대 8건 요약 문자열 생성
  - `_director_mc_parts`가 list로 존재할 때만 append (안전 가드)
  - read/주입 실패 시 비치명 debug 로그

### Phase 4

- `tests/test_lm_post1.py` 신규 7개 테스트 추가:
  1. YAML lookback 값(>=10) 확인
  2. ValidationOrchestrator의 retrospective threshold key 사용 확인
  3. RetrospectiveValidator lookback 인자 반영 확인
  4. `get_recent_causal_links()` 빈 DB 반환 확인
  5. 정상 저장/조회 확인
  6. lookback 범위 필터 확인
  7. malformed JSON row skip 확인

## 검증 결과

- py_compile
  - `python -m py_compile modules/validation/validation_orchestrator.py` 통과
  - `python -m py_compile modules/core/db_manager.py` 통과
  - `python -m py_compile modules/core/stage4_post_processor.py` 통과
- 설정 확인
  - `retrospective.lookback_episodes: 10`
- 신규 테스트
  - `pytest tests/test_lm_post1.py -v` → **7 passed, 0 failed**
- ruff
  - `ruff check modules/validation/validation_orchestrator.py modules/core/db_manager.py modules/core/stage4_post_processor.py tests/test_lm_post1.py` → **All checks passed**
- 전체 테스트
  - `pytest tests/ -q` → **3227 passed, 16 skipped, 0 failed**

## 비고

- 오더의 강제 기준(`3220 passed, 16 skipped, 0 failed`) 대비, 신규 테스트 7개 추가로 총 pass 수가 3227로 증가함.
