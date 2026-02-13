# codex_fix_pytest_io.md
# pytest 전체 수집 I/O 크래시 수정

## 배경

`python -m pytest tests/` 실행 시 `ValueError: I/O operation on closed file.`로 전체 테스트 수집 실패.
원인: `tests/stage3_isolated_test/` 내 3개 파일이 **모듈 레벨**에서 `sys.stdout`/`sys.stderr`를 재래핑하여
pytest의 capture 메커니즘을 파괴함.

## 원인 코드 (3개 파일 동일 패턴)

```python
# L20-22 (모듈 레벨 — import 시 즉시 실행됨)
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
```

pytest가 `tests/` 디렉토리를 수집할 때 이 파일들을 import → `sys.stderr` 교체 → pytest capture 깨짐.

## Task: 모듈 레벨 재래핑을 `if __name__` 가드 아래로 이동

### 대상 파일

1. `tests/stage3_isolated_test/test_stage3_arc3.py`
2. `tests/stage3_isolated_test/test_stage3_arc3_v2.py`
3. `tests/stage3_isolated_test/test_stage3_production.py`

### 수정 방법 (3개 파일 모두 동일)

L20-22의 `sys.stdout`/`sys.stderr` 재래핑 코드를 삭제하고,
`if __name__ == "__main__":` 블록 첫 줄로 이동.

**Before (각 파일 L15~22):**
```python
import os
import sys
import io

# Windows UTF-8 출력 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
```

**After (각 파일 L15~17):**
```python
import os
import sys
import io
```

**그리고 `if __name__ == "__main__":` 블록 시작 부분에 추가:**
```python
if __name__ == "__main__":
    # Windows UTF-8 출력 설정 (pytest 수집 시 capture 파괴 방지)
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    main()
```

### 주의사항

- `io` import는 모듈 레벨에 유지 (삭제 금지)
- `if __name__` 블록 내에서 `main()` 호출 전에 래핑 코드를 넣을 것
- 다른 코드는 변경하지 말 것

## 검증

```bash
# 1. 구문 검사
python -m compileall tests/stage3_isolated_test/ -q

# 2. pytest 전체 수집 검증 (핵심!)
python -m pytest tests/ --collect-only -q 2>&1 | tail -3

# 3. 개별 테스트 수집 검증
python -m pytest tests/stage3_isolated_test/ --collect-only -q 2>&1 | tail -3

# 4. 기존 테스트 통과 확인
python -m pytest tests/test_genre_guard.py -q --tb=short
```

## 예상 결과

- `tests/ --collect-only` 에서 `ValueError: I/O operation on closed file.` 사라짐
- 22개+ 테스트 파일에서 600+ tests 정상 수집
