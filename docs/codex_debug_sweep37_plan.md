# Debug Sweep 37 — 한글 깨짐(Mojibake) + BOM 오염 수정

## Context

Sweep 36 완료 (2,087 passed, 68 xfailed). 5개 탐색 에이전트로 전체 코드베이스 인코딩 상태 검사:
- `main_a.py`: 깨끗
- `modules/core/*.py`: **`db_manager.py` 260줄 mojibake** (working tree 전용, HEAD는 깨끗)
- `modules/domain/agents/*.py`: 깨끗 (`block_enricher.py` UTF-8 BOM만)
- `config/prompts/*.yaml` + `config/settings/*.yaml`: 깨끗
- `modules/validation/*.py`, `modules/models/*.py`, `modules/core/services/*.py`, `modules/core/genre_guards/*.py`, `modules/core/stage0/*.py`: 깨끗

---

## A-1 (CRITICAL): `db_manager.py` — 260줄 한글 주석/독스트링 전면 깨짐

**파일**: `modules/core/db_manager.py`

**문제**: working tree의 파일이 인코딩 오염됨. EUC-KR/CP949 바이트가 Latin-1로 해석 후 UTF-8로 재저장 → 한자(踰, 濡, 怨, 媛, 諛) + `\x80` 제어문자 혼합:

```python
# HEAD (정상):
# [V44] DB 에러 심각도 분류
"""DB 작업 중 발생하는 기본 예외"""
# 데이터 손실 위험
# 작업 실패, 복구 가능

# Working tree (깨짐):
# [V44] DB ?먮윭 ?ш컖??遺꾨쪟
"""DB ?묒뾽 以?諛쒖깮?섎뒗 湲곕낯 ?덉쇅"""
# ?곗씠???먯떎 ?꾪뿕
# ?묒뾽 ?ㅽ뙣, 蹂듦뎄 媛??
```

- 260줄 영향 (주석, 독스트링, 로깅 문자열, SQL 코멘트 전부)
- UTF-8 BOM(`\xef\xbb\xbf`)도 첫 줄에 추가됨
- **기능 코드 변경 없음** — 모든 diff가 한글 텍스트 깨짐뿐
- HEAD 커밋 버전은 깨끗

**수정**: HEAD에서 복원:
```bash
git checkout HEAD -- modules/core/db_manager.py
```

---

## A-2 (LOW): `block_enricher.py` — UTF-8 BOM 오염

**파일**: `modules/domain/agents/block_enricher.py`

**문제**: 파일 첫 바이트에 UTF-8 BOM(`\xef\xbb\xbf`)이 추가됨:
```
# HEAD: 22 22 22 0a  ("""  정상)
# Working: ef bb bf 22 22 22  (﻿"""  BOM 추가)
```

- Python 3는 BOM을 무시하지만, 일부 도구(diff, lint)에서 문제 발생 가능
- 이 파일에는 Sweep 34/36의 기능 변경(total_score 타입 안전성, 로깅 추가)이 포함되어 있어 `git checkout`은 불가

**수정**: 첫 줄에서 BOM만 제거:
```python
import pathlib

p = pathlib.Path("modules/domain/agents/block_enricher.py")
content = p.read_bytes()
if content[:3] == b'\xef\xbb\xbf':
    p.write_bytes(content[3:])
    print("BOM removed")
```

---

## 수정 파일 총괄

| # | 파일 | 변경 |
|---|------|------|
| A-1 | `modules/core/db_manager.py` | `git checkout HEAD --` 복원 (260줄 mojibake 전면 해소) |
| A-2 | `modules/domain/agents/block_enricher.py` | BOM 3바이트 제거 |

**총 2파일**

---

## 검증

```bash
# A-1: db_manager.py 복원
git checkout HEAD -- modules/core/db_manager.py

# A-2: block_enricher.py BOM 제거
python -c "
import pathlib
p = pathlib.Path('modules/domain/agents/block_enricher.py')
content = p.read_bytes()
if content[:3] == b'\xef\xbb\xbf':
    p.write_bytes(content[3:])
    print('BOM removed from block_enricher.py')
else:
    print('No BOM found')
"

# 복원 후 mojibake 잔여 확인
python -c "
import pathlib
content = pathlib.Path('modules/core/db_manager.py').read_text(encoding='utf-8')
# 한자 문자가 주석에 있으면 mojibake 잔존
import re
hanja = re.findall(r'[踰濡怨媛諛吏湲而씤뿰쓣]', content)
if hanja:
    print(f'WARNING: {len(hanja)} mojibake characters remaining')
else:
    print('CLEAN: No mojibake detected')
"

# BOM 잔여 확인
python -c "
for f in ['modules/core/db_manager.py', 'modules/domain/agents/block_enricher.py']:
    data = open(f, 'rb').read(3)
    if data == b'\xef\xbb\xbf':
        print(f'BOM FOUND: {f}')
    else:
        print(f'CLEAN: {f}')
"

# 전체 테스트
set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -q -x -p no:capture
```

---

## 원인 분석

`db_manager.py`의 오염 원인:
- Codex 또는 외부 에디터가 파일을 CP949/EUC-KR로 읽은 후 UTF-8로 재저장
- 한글 멀티바이트 시퀀스가 Latin-1 코드포인트로 해석되어 한자+제어문자로 변환
- BOM은 Windows 에디터(메모장 등)가 UTF-8 저장 시 자동 추가하는 패턴

**재발 방지**: `.editorconfig` 또는 에디터 설정에서 `charset = utf-8` (BOM 없음) 강제 권장
