"""Stage 0 개선 테스트 (12건)"""

import inspect
import json
import re

import pytest

from modules.core.constants import GenreTypes
from modules.core.stage0 import StageZeroManager
from modules.core.stage0.reverse_expander import ReverseExpander
from modules.core.stage0.story_expander import StoryExpander


# ──────────────────────────────────────────────
# A-1: SUPPORTED_GENRES == GenreTypes.all()
# ──────────────────────────────────────────────
class TestPhaseA:
    def test_supported_genres_matches_genre_types(self):
        """SUPPORTED_GENRES 키가 GenreTypes.all()과 정확히 일치"""
        assert set(StageZeroManager.SUPPORTED_GENRES.keys()) == set(GenreTypes.all())

    def test_story_expander_genre_prompt_dynamic(self):
        """analyze_concept 프롬프트가 GenreTypes.all() 전부 포함"""
        src = inspect.getsource(StoryExpander.analyze_concept)
        for genre in GenreTypes.all():
            assert genre in src or "GenreTypes.all()" in src, (
                f"analyze_concept에 {genre} 또는 GenreTypes.all() 참조 누락"
            )

    def test_reverse_expander_genre_prompt_no_unsupported(self):
        """detect_genre 프롬프트에 romance/politics/military 미포함"""
        src = inspect.getsource(ReverseExpander.detect_genre)
        for removed in ("romance", "politics", "military"):
            assert removed not in src, f"detect_genre에 제거된 장르 '{removed}' 잔존"

    def test_story_expander_uses_model_constant(self):
        """_call_llm이 AIModels 상수를 참조"""
        src = inspect.getsource(StoryExpander._call_llm)
        assert "gemini-2.5-flash" not in src, "_call_llm에 하드코딩된 모델명 잔존"
        assert "_FALLBACK_MODELS" in src or "AIModels" in src

    def test_reverse_expander_uses_model_constant(self):
        """_call_llm이 AIModels 상수를 참조"""
        src = inspect.getsource(ReverseExpander._call_llm)
        assert "gemini-2.5-flash" not in src, "_call_llm에 하드코딩된 모델명 잔존"
        assert "_FALLBACK_MODELS" in src or "AIModels" in src

    def test_import_bible_fallback_uses_constant(self):
        """import_bible 소스에 GenreTypes.INVESTMENT 참조"""
        src = inspect.getsource(StageZeroManager.import_bible)
        assert "GenreTypes.INVESTMENT" in src or '"investment"' not in src

    def test_import_bible_missing_genre_does_not_force_investment(self, tmp_path):
        manager = StageZeroManager()
        bible_path = tmp_path / "bible_missing_genre.json"
        bible_path.write_text(json.dumps({"MasterBible": {}}, ensure_ascii=False), encoding="utf-8")

        manager.import_bible(str(bible_path))

        assert manager.genre == ""


# ──────────────────────────────────────────────
# Phase B: 안정성 + 매직넘버
# ──────────────────────────────────────────────
class TestPhaseB:
    def test_reverse_expander_no_magic_five(self):
        """reverse_expander 소스에 하드코딩 // 5, * 5 패턴 미존재"""
        # _save_arc_stubs, _save_blueprint_stubs, get_stub_summary 검사
        for method_name in ("_save_arc_stubs", "_save_blueprint_stubs", "get_stub_summary"):
            method = getattr(ReverseExpander, method_name, None)
            if method is None:
                continue
            src = inspect.getsource(method)
            assert re.search(r"//\s*5\b", src) is None, f"{method_name}에 하드코딩 '// 5' 잔존"
            assert re.search(r"\*\s*5\b", src) is None, f"{method_name}에 하드코딩 '* 5' 잔존"

    def test_skeleton_uses_batch(self):
        """_generate_skeleton이 배치 루프 구조 사용"""
        src = inspect.getsource(StoryExpander._generate_skeleton)
        assert "batch_size" in src, "_generate_skeleton에 배치 루프 미구현"
        # 20000 토큰 단일 호출이 아닌 8192 배치 확인
        assert "20000" not in src, "_generate_skeleton이 여전히 단일 20000 토큰 호출"

    def test_episode_bible_truncation_increased(self):
        """에피소드 상태 추출 시 content 절삭이 6000자"""
        src = inspect.getsource(ReverseExpander._extract_single_episode_bible)
        assert "[:6000]" in src, "content 절삭이 6000자로 완화되지 않음"
        assert "[:3000]" not in src, "content 절삭이 여전히 3000자"

    def test_input_eof_handling(self):
        """주요 input 경로에 EOFError 처리 존재"""
        for method_name in (
            "run_reverse_engineering_flow",
            "import_bible",
            "run_reference_analysis",
            "run_new_project_flow",
        ):
            src = inspect.getsource(getattr(StageZeroManager, method_name))
            assert "EOFError" in src, f"{method_name}에 EOFError 처리 누락"

    def test_extract_single_episode_bible_method_exists(self):
        """공통 메서드 _extract_single_episode_bible 존재"""
        assert hasattr(ReverseExpander, "_extract_single_episode_bible")
        assert callable(getattr(ReverseExpander, "_extract_single_episode_bible"))


# ──────────────────────────────────────────────
# Phase C: 코드 위생
# ──────────────────────────────────────────────
class TestPhaseC:
    def test_no_logging_info_for_ui_in_init(self):
        """__init__.py 메뉴/UI 텍스트에 logging.info 미사용 (print 사용)

        [S0-P1-6] 사용자에게 보여야 할 메뉴 텍스트는 print()를 사용.
        logging.info()는 WARNING 레벨에서 보이지 않으므로 UI용으로 부적합.
        """
        src = inspect.getsource(StageZeroManager)
        lines = src.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            # 메뉴 표시용 logging.info 금지 (logging.warning/error는 허용)
            if stripped.startswith("logging.info(") and any(
                kw in stripped for kw in ["[1]", "[2]", "[3]", "[4]", "[5]", "[0]", "메뉴", "선택", "====", "----"]
            ):
                pytest.fail(f"StageZeroManager L{i}: UI용 logging.info() 발견: {stripped[:80]}")
