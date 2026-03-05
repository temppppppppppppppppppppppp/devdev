# Codex Order: LOG-EMOJI — 콘솔 로그 이모지 제거

**작업 ID**: LOG-EMOJI
**우선순위**: P2 (기능 영향 없음, 표시 개선)
**대상**: `modules/` 하위 모든 `.py` 파일의 `logging.*()` 호출

---

## 배경

Windows 터미널(CP949)이 `logging.*()` 인자 안의 이모지+한글 조합 일부를
`?~~` 형태로 깨뜨림.

LLM 프롬프트 문자열에 포함된 이모지(advisory 헤더 등)는 API로 직접 전달되므로
터미널 인코딩과 무관 → **유지**.

---

## 처리 방침

| 이모지 | 처리 |
|--------|------|
| `\u2705` (✅) | **유지** — 합격/성공 신호, 가독성 기여 |
| `\u274c` (❌) | **유지** — 실패 신호, 가독성 기여 |
| 그 외 모든 이모지 | **완전 제거** (빈 문자열로 교체, 태그 치환 없음) |

"제거"란 해당 이모지 문자를 공백 없이 삭제하는 것. 앞뒤 공백 정리도 함께.

---

## 스코프

### 수정 대상
- `modules/**/*.py` 내 `logging.info(...)` / `logging.warning(...)` /
  `logging.debug(...)` / `logging.error(...)` / `logging.critical(...)` 호출의
  **문자열 리터럴 내 이모지**

### 수정 제외 (건드리지 말 것)
- `config/prompts/*.yaml` — LLM 프롬프트, 이모지 의미 있음
- LLM에게 전달되는 문자열 변수 (advisory 문자열 등)
- `print()` 호출 — 메뉴 UI는 별도
- `tests/` — 테스트 문자열 변경 금지

---

## 구현

`scripts/strip_log_emojis.py`를 아래와 같이 작성 후 실행, 완료 후 삭제.

### 중요: 인코딩 주의사항

**스크립트 소스 내에서 이모지를 리터럴 문자로 쓰지 말 것.**
유지 대상 2개를 포함해 모든 이모지는 `\uXXXX` / `\UXXXXXXXX` 코드포인트로만 표기.
(Codex가 파일 저장 시 인코딩을 깨뜨리는 것을 방지)

```python
import re
from pathlib import Path

# 유지 대상 코드포인트 (이 문자는 제거하지 않음)
KEEP = {
    0x2705,  # \u2705  (체크마크 - OK)
    0x274C,  # \u274c  (X - FAIL)
}

def is_removable_emoji(ch: str) -> bool:
    cp = ord(ch)
    if cp in KEEP:
        return False
    # 이모지/심볼 유니코드 블록 범위
    return (
        0x2300 <= cp <= 0x27BF   # Misc Technical / Dingbats
        or 0x2B00 <= cp <= 0x2BFF
        or 0x1F000 <= cp <= 0x1FFFF  # Emoji Extended
        or cp in (
            0xFE0F,  # variation selector-16 (이모지 수식자)
        )
    )

def strip_emojis_from_match(s: str) -> str:
    chars = []
    i = 0
    while i < len(s):
        ch = s[i]
        if is_removable_emoji(ch):
            # 앞 공백이 남으면 다음 문자 확인 후 정리
            if chars and chars[-1] == ' ':
                # 뒤에도 공백이나 특수문자면 앞 공백 제거
                pass  # 그냥 skip
            i += 1
            continue
        chars.append(ch)
        i += 1
    # 연속 공백 정리
    result = ''.join(chars)
    result = re.sub(r'  +', ' ', result)
    return result.strip()

# logging.*(...)  호출의 첫 번째 문자열 인자만 처리
LOG_CALL_RE = re.compile(
    r'(logging\s*\.\s*(?:info|warning|debug|error|critical)\s*\()'
    r'(\s*(?:f?"""[\s\S]*?"""|f?\'\'\'[\s\S]*?\'\'\'|f?"[^"]*"|f?\'[^\']*\'))',
    re.MULTILINE,
)

def process_file(path: Path) -> bool:
    src = path.read_text(encoding='utf-8')
    changed = False

    def replacer(m):
        nonlocal changed
        prefix = m.group(1)
        arg = m.group(2)
        new_arg = strip_emojis_from_match(arg)
        if new_arg != arg:
            changed = True
            return prefix + new_arg
        return m.group(0)

    new_src = LOG_CALL_RE.sub(replacer, src)
    if changed:
        path.write_text(new_src, encoding='utf-8')
    return changed

count = 0
for py_file in Path('modules').rglob('*.py'):
    if process_file(py_file):
        count += 1
        print(f'[OK] {py_file}')

print(f'\n[DONE] {count} files updated')
```

---

## 감리 포인트

1. `ruff check modules/` → 0 violations
2. `pytest tests/ -q` → **3,370 passed** (기준선 유지)
3. 아래 명령으로 유지 대상 외 이모지 잔존 여부 확인:
   ```
   python -c "
   import re, sys
   from pathlib import Path
   KEEP = {'\u2705', '\u274c'}
   pat = re.compile(r'logging\.(info|warning|debug|error|critical)')
   issues = []
   for f in Path('modules').rglob('*.py'):
       for i, line in enumerate(f.read_text(encoding='utf-8').splitlines(), 1):
           if pat.search(line):
               non_ascii = [c for c in line if ord(c) > 0x27FF and c not in KEEP]
               if non_ascii:
                   issues.append(f'{f}:{i}  {non_ascii}')
   if issues:
       print('REMAINING EMOJIS:'); [print(x) for x in issues]
   else:
       print('CLEAN')
   "
   ```
4. `\u2705` / `\u274c` 는 logging 라인에 그대로 남아있어야 함
5. `config/prompts/*.yaml` diff 없음 확인
