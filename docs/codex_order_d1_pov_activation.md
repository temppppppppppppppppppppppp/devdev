# Codex Order: D-1 시점(POV) 시스템 활성화

> **목표**: Stage 0에 POV 선택 메뉴 추가 → 기존 POV 시스템 전체 자동 활성화
> **범위**: 1개 파일 수정 (~20줄), 테스트 1개 추가
> **위험도**: 극저 (프로덕션 로직 변경 없음, 입력 경로만 추가)

---

## 배경

POV 시스템은 이미 **95% 구현 완료**되어 있으나, Stage 0에 POV 선택 메뉴가 없어서
`protagonist_config["pov"]`가 항상 빈 문자열 → 전체 POV 체인이 비활성 상태.

**기존 구현 (이미 작동 대기 중):**

| 컴포넌트 | 파일 | 상태 |
|----------|------|------|
| Blueprint POV 제약 | `blueprint_ensemble.py` L325-337 | ✅ 1인칭→villain_scheme 금지 등 |
| SCENE_PRESETS 12종 | `blueprint_ensemble.py` L76-90 | ✅ ensemble.yaml에 테이블 포함 |
| StyleGuide.pov + _get_pov_rules() | `style_extractor.py` L26, L71-99 | ✅ 3종 규칙 (1인칭/3인칭/전지적) |
| StyleGuide.to_prompt() | `style_extractor.py` L101-169 | ✅ STEP 6에 주입 |
| Stage 4 Bible POV 로드 | `stage4_orchestrator.py` L789, L809 | ✅ protagonist_config.pov 읽기 |
| Stage 4 최소 StyleGuide 생성 | `stage4_orchestrator.py` L803-815 | ✅ Bible POV만으로 가이드 생성 |
| Chief Writer 프롬프트 주입 | `chief_writer_prompts.py` L213 | ✅ STEP 6: 문체 DNA 가이드 |

**빠진 것 (이번 작업):**

| 컴포넌트 | 파일 | 상태 |
|----------|------|------|
| Stage 0 POV 선택 메뉴 | `stage0/__init__.py` | ❌ 미구현 |

---

## 수정 내용

### `modules/core/stage0/__init__.py`

#### 1. POV_OPTIONS 상수 추가 (L63 뒤)

**현재 (L62-64):**
```python
WORLD_ORIGIN_OPTIONS = ["현대인", "원시인"]
INCARNATION_TYPES = ["회귀자", "빙의자", "환생자", "일반"]
```

**수정 후:**
```python
WORLD_ORIGIN_OPTIONS = ["현대인", "원시인"]
INCARNATION_TYPES = ["회귀자", "빙의자", "환생자", "일반"]
POV_OPTIONS = ["1인칭", "3인칭", "전지적"]
```

#### 2. POV 선택 UI 추가 (show_protagonist_config_menu 내, L162 뒤)

**현재 (L151-164):**
```python
        # 회귀/빙의 타입
        logging.info("\n  [캐릭터 타입]")
        for i, opt in enumerate(self.INCARNATION_TYPES, 1):
            logging.info(f"[{i}] {opt}")
        try:
            choice = int(input("    선택: ").strip()) - 1
            if 0 <= choice < len(self.INCARNATION_TYPES):
                config["incarnation_type"] = self.INCARNATION_TYPES[choice]
            else:
                config["incarnation_type"] = "일반"
        except (ValueError, IndexError, EOFError):
            config["incarnation_type"] = "일반"

        return config
```

**수정 후:**
```python
        # 회귀/빙의 타입
        logging.info("\n  [캐릭터 타입]")
        for i, opt in enumerate(self.INCARNATION_TYPES, 1):
            logging.info(f"[{i}] {opt}")
        try:
            choice = int(input("    선택: ").strip()) - 1
            if 0 <= choice < len(self.INCARNATION_TYPES):
                config["incarnation_type"] = self.INCARNATION_TYPES[choice]
            else:
                config["incarnation_type"] = "일반"
        except (ValueError, IndexError, EOFError):
            config["incarnation_type"] = "일반"

        # [D-1] 시점(POV) 선택
        logging.info("\n  [시점(POV)]")
        for i, opt in enumerate(self.POV_OPTIONS, 1):
            logging.info(f"[{i}] {opt}")
        try:
            choice = int(input("    선택: ").strip()) - 1
            if 0 <= choice < len(self.POV_OPTIONS):
                config["pov"] = self.POV_OPTIONS[choice]
            else:
                config["pov"] = "3인칭"
        except (ValueError, IndexError, EOFError):
            config["pov"] = "3인칭"

        return config
```

> **기본값**: "3인칭" (가장 범용적, villain_scheme/side_glimpse 사용 가능)

---

## 동작 원리 (변경 후 자동 활성화 체인)

```
Stage 0: protagonist_config["pov"] = "1인칭"
  ↓
Bible 생성: MasterBible.protagonist_config.pov = "1인칭"
  ↓
Stage 2 Blueprint: _pov_constraint() → "villain_scheme 금지, 주인공 필수 등장"
  ↓
Stage 4 부팅: Bible에서 pov 읽기 → 최소 StyleGuide 생성 (또는 저장된 가이드 오버라이드)
  ↓
Chief Writer: STEP 6 문체 DNA 가이드에 POV 규칙 포함
  ↓
LLM: 1인칭 규칙 준수하여 원고 작성
```

---

## 테스트

### `tests/test_stage0_pov.py` (신규, ~40줄)

```python
"""[D-1] Stage 0 POV 선택 메뉴 테스트."""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestPOVSelection:
    """Stage 0 POV 선택 메뉴 검증."""

    def test_pov_options_defined(self):
        """POV_OPTIONS 상수가 3개 시점을 포함."""
        from modules.core.stage0 import StageZeroManager
        assert hasattr(StageZeroManager, "POV_OPTIONS")
        assert "1인칭" in StageZeroManager.POV_OPTIONS
        assert "3인칭" in StageZeroManager.POV_OPTIONS
        assert "전지적" in StageZeroManager.POV_OPTIONS

    @patch("builtins.input", side_effect=["1", "1", "1"])  # world, type, pov
    def test_pov_first_person_selected(self, mock_input):
        """1인칭 선택 시 config에 pov='1인칭' 포함."""
        from modules.core.stage0 import StageZeroManager
        mgr = StageZeroManager.__new__(StageZeroManager)
        mgr.WORLD_ORIGIN_OPTIONS = StageZeroManager.WORLD_ORIGIN_OPTIONS
        mgr.INCARNATION_TYPES = StageZeroManager.INCARNATION_TYPES
        mgr.POV_OPTIONS = StageZeroManager.POV_OPTIONS
        config = mgr.show_protagonist_config_menu()
        assert config["pov"] == "1인칭"

    @patch("builtins.input", side_effect=["1", "1", "2"])  # world, type, pov=3인칭
    def test_pov_third_person_selected(self, mock_input):
        """3인칭 선택 시 config에 pov='3인칭' 포함."""
        from modules.core.stage0 import StageZeroManager
        mgr = StageZeroManager.__new__(StageZeroManager)
        mgr.WORLD_ORIGIN_OPTIONS = StageZeroManager.WORLD_ORIGIN_OPTIONS
        mgr.INCARNATION_TYPES = StageZeroManager.INCARNATION_TYPES
        mgr.POV_OPTIONS = StageZeroManager.POV_OPTIONS
        config = mgr.show_protagonist_config_menu()
        assert config["pov"] == "3인칭"

    @patch("builtins.input", side_effect=["1", "1", "invalid"])  # 잘못된 입력 → 기본값
    def test_pov_default_on_invalid_input(self, mock_input):
        """잘못된 입력 시 기본값 '3인칭'."""
        from modules.core.stage0 import StageZeroManager
        mgr = StageZeroManager.__new__(StageZeroManager)
        mgr.WORLD_ORIGIN_OPTIONS = StageZeroManager.WORLD_ORIGIN_OPTIONS
        mgr.INCARNATION_TYPES = StageZeroManager.INCARNATION_TYPES
        mgr.POV_OPTIONS = StageZeroManager.POV_OPTIONS
        config = mgr.show_protagonist_config_menu()
        assert config["pov"] == "3인칭"

    def test_style_guide_pov_rules_exist(self):
        """StyleGuide가 1인칭/3인칭/전지적 규칙을 생성하는지 확인."""
        from modules.core.stage0 import StyleGuide
        for pov in ["1인칭", "3인칭", "전지적"]:
            sg = StyleGuide(pov=pov)
            prompt = sg.to_prompt()
            assert "시점 규칙" in prompt
            assert pov in prompt
```

---

## 검증 게이트

```bash
# Gate 1: py_compile
python -m py_compile modules/core/stage0/__init__.py

# Gate 2: SovereignApp import
python -c "from main_a import SovereignApp; print('OK')"

# Gate 3: 신규 테스트
set PYTHONIOENCODING=utf-8
pytest tests/test_stage0_pov.py -v

# Gate 4: 기존 테스트 회귀 없음
set PYTHONIOENCODING=utf-8
pytest tests/ -q

# Gate 5: pre-commit
pre-commit run --files modules/core/stage0/__init__.py tests/test_stage0_pov.py
```

---

## 체크리스트

- [ ] POV_OPTIONS 상수 추가 (L63)
- [ ] show_protagonist_config_menu에 POV 선택 UI 추가 (~12줄)
- [ ] 테스트 파일 생성 (4건)
- [ ] Gate 1-5 통과
- [ ] 커밋: `feat(stage0): add POV selection menu to protagonist config (D-1)`

---

## 프로덕션 코드 변경: `stage0/__init__.py` 1곳만 (POV_OPTIONS + 메뉴 UI)
## 테스트 전용 파일: `tests/test_stage0_pov.py` (신규)
