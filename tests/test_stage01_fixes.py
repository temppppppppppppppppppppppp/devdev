"""Stage 0/1 이슈 10건 수정 검증 테스트."""

import inspect

import pytest

from modules.core.constants import GenreTypes


# ──────────────────────────────────────────────
# analyst.py 검증 (A-1 ~ A-6)
# ──────────────────────────────────────────────
class TestAnalystFixes:
    """analyst.py 6건 수정 검증."""

    def test_safe_dict_module_level(self):
        """A-1: _SafeDict가 모듈 레벨에 존재."""
        from modules.domain.agents.analyst import _SafeDict

        d = _SafeDict(a=1)
        assert d["a"] == 1
        assert d["missing"] == "{missing}"

    def test_extract_content_parts_exists(self):
        """A-2: _extract_content_parts 메서드 존재."""
        from modules.domain.agents.analyst import Analyst

        assert hasattr(Analyst, "_extract_content_parts")
        assert callable(getattr(Analyst, "_extract_content_parts"))

    def test_extract_content_parts_returns(self):
        """A-2: 헬퍼가 (list, int) 튜플 반환."""
        from modules.domain.agents.analyst import Analyst

        block = {
            "context": "배경 설명",
            "event_villain": "적 등장",
            "title": "테스트",
        }
        parts, length = Analyst._extract_content_parts(block)
        assert isinstance(parts, list)
        assert isinstance(length, int)
        assert len(parts) >= 2  # context + event_villain + title
        assert length > 0

    def test_extract_content_parts_empty(self):
        """A-2: 빈 블록 → 빈 리스트."""
        from modules.domain.agents.analyst import Analyst

        parts, length = Analyst._extract_content_parts({})
        assert parts == []
        assert length == 0

    def test_extract_content_parts_non_dict(self):
        """A-2: dict가 아닌 입력 → 빈 리스트."""
        from modules.domain.agents.analyst import Analyst

        parts, length = Analyst._extract_content_parts("not a dict")
        assert parts == []
        assert length == 0

    def test_load_genre_libraries_exists(self):
        """A-3: _load_genre_libraries 메서드 존재."""
        from modules.domain.agents.analyst import Analyst

        assert hasattr(Analyst, "_load_genre_libraries")
        assert callable(getattr(Analyst, "_load_genre_libraries"))

    def test_get_current_genre_uses_dict(self):
        """A-4: _get_current_genre 소스에 9-branch if-elif 없음."""
        from modules.domain.agents.analyst import Analyst

        src = inspect.getsource(Analyst._get_current_genre)
        # 9-branch if-elif가 사라지고 dict lookup으로 전환됨
        elif_count = src.count("elif")
        assert elif_count == 0, f"_get_current_genre에 elif {elif_count}개 잔존"

    def test_get_current_genre_uses_constant(self):
        """A-4: _get_current_genre가 GenreTypes.WUXIA 상수 사용."""
        from modules.domain.agents.analyst import Analyst

        src = inspect.getsource(Analyst._get_current_genre)
        assert "GenreTypes.WUXIA" in src, "_get_current_genre에 GenreTypes.WUXIA 미참조"

    def test_genre_detect_map_covers_all(self):
        """A-4: _GENRE_DETECT_MAP이 GenreTypes.all() 전부 포함."""
        from modules.domain.agents.analyst import Analyst

        map_values = set(Analyst._GENRE_DETECT_MAP.values())
        for genre in GenreTypes.all():
            assert genre in map_values, f"_GENRE_DETECT_MAP에 {genre} 미포함"

    def test_validate_stub_docstring(self):
        """A-5: _validate_arc_with_state_tracker docstring에 '비활성화' 언급."""
        from modules.domain.agents.analyst import Analyst

        doc = Analyst._validate_arc_with_state_tracker.__doc__ or ""
        assert "비활성화" in doc, "스텁 docstring에 비활성화 언급 누락"

    def test_post_process_arc_exists(self):
        """A-6: _post_process_arc 메서드 존재."""
        from modules.domain.agents.analyst import Analyst

        assert hasattr(Analyst, "_post_process_arc")
        assert callable(getattr(Analyst, "_post_process_arc"))


# ──────────────────────────────────────────────
# stage01_helpers.py 검증 (B-1 ~ B-4)
# ──────────────────────────────────────────────
class TestStage01HelpersFixes:
    """stage01_helpers.py 4건 수정 검증."""

    def test_capsule_bypass_fixed(self):
        """B-1: phase_0_recovery 소스에 self.app._stage_0_extended 미존재."""
        from modules.core.stage01_helpers import Stage01Helpers

        src = inspect.getsource(Stage01Helpers.phase_0_recovery)
        assert "self.app._stage_0_extended" not in src, "캡슐화 우회 잔존"
        # self.stage_0_extended로 변경됨
        assert "self.stage_0_extended" in src

    def test_extend_blocks_bypass_fixed(self):
        """B-1: stage_0_extended에서 self.extend_blocks() 호출."""
        from modules.core.stage01_helpers import Stage01Helpers

        # _s0_handle_block_extension 에서 self.extend_blocks 직접 호출
        src = inspect.getsource(Stage01Helpers._s0_handle_block_extension)
        assert "self.extend_blocks" in src

    def test_stage0_extended_handlers_exist(self):
        """B-2: 5개 핸들러 + 1 save 메서드 존재."""
        from modules.core.stage01_helpers import Stage01Helpers

        for name in [
            "_s0_handle_concept",
            "_s0_handle_reverse_engineering",
            "_s0_handle_bible_import",
            "_s0_handle_block_extension",
            "_s0_handle_style_analysis",
            "_s0_save_results",
        ]:
            assert hasattr(Stage01Helpers, name), f"{name} 메서드 미존재"

    def test_stage0_extended_dispatcher(self):
        """B-2: stage_0_extended에 handlers dict 존재."""
        from modules.core.stage01_helpers import Stage01Helpers

        src = inspect.getsource(Stage01Helpers.stage_0_extended)
        assert "handlers" in src, "dispatcher dict 미존재"
        assert "handlers.get(choice)" in src, "dict lookup 미사용"

    def test_stage0_extended_no_bare_print(self):
        """B-3: stage_0_extended dispatcher에 bare print 없음."""
        from modules.core.stage01_helpers import Stage01Helpers

        src = inspect.getsource(Stage01Helpers.stage_0_extended)
        lines = src.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("print("):
                pytest.fail(f"stage_0_extended L{i}: bare print() 발견: {stripped[:80]}")

    def test_phase_0_recovery_no_bare_print(self):
        """B-3: phase_0_recovery에 bare print 없음."""
        from modules.core.stage01_helpers import Stage01Helpers

        src = inspect.getsource(Stage01Helpers.phase_0_recovery)
        lines = src.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("print("):
                pytest.fail(f"phase_0_recovery L{i}: bare print() 발견: {stripped[:80]}")

    def test_extend_blocks_no_bare_print(self):
        """B-3: extend_blocks에 bare print 없음."""
        from modules.core.stage01_helpers import Stage01Helpers

        src = inspect.getsource(Stage01Helpers.extend_blocks)
        lines = src.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("print("):
                pytest.fail(f"extend_blocks L{i}: bare print() 발견: {stripped[:80]}")

    def test_input_eof_handling(self):
        """B-4: 모든 input() 호출에 EOFError 처리 존재."""
        from modules.core.stage01_helpers import Stage01Helpers

        src = inspect.getsource(Stage01Helpers)
        # 모든 input() 라인이 try 블록 안에 있는지 확인
        lines = src.split("\n")
        unguarded = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if "input(" in stripped and not stripped.startswith("#"):
                # try 블록 안에 있는지 확인 (이전 줄들에서 try 찾기)
                context = "\n".join(lines[max(0, i - 5) : i + 1])
                if "try:" not in context:
                    # except 절의 일부가 아닌지 확인
                    if "except" not in stripped:
                        unguarded.append(f"L{i + 1}: {stripped[:80]}")
        assert len(unguarded) == 0, f"보호되지 않은 input() {len(unguarded)}건: {unguarded}"
