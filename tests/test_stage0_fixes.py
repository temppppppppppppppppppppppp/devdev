"""Stage 0 개선 테스트 (12건)"""

import inspect
import json
import re
from unittest.mock import MagicMock, patch

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
        """에피소드 상태 추출 시 head+tail 절삭 helper 사용."""
        src = inspect.getsource(ReverseExpander._extract_single_episode_bible)
        assert "_EPISODE_BIBLE_MAX_CHARS" in src
        assert "self._excerpt(" in src
        assert "[:6000]" not in src

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

    def test_reverse_engineering_flow_handles_draft_encoding_error(self, tmp_path, capsys):
        manager = StageZeroManager(project_path=str(tmp_path))
        src = tmp_path / "broken.txt"
        src.write_text("placeholder", encoding="utf-8")

        with (
            patch.object(StageZeroManager, "show_genre_menu", return_value=""),
            patch.object(
                ReverseExpander,
                "run",
                side_effect=ReverseExpander.DraftEncodingError("UTF-8/cp949로 복구할 수 없는 입력 파일입니다"),
            ),
        ):
            bible, episode_bibles, style_guide = manager.run_reverse_engineering_flow(str(src))

        captured = capsys.readouterr()
        assert bible == {}
        assert episode_bibles == []
        assert style_guide is None
        assert "인코딩 오류로 역설계를 중단합니다" in captured.out

    def test_generate_from_concept_returns_plot_roadmap_before_save(self):
        manager = StageZeroManager()
        manager.genre = "wuxia"
        manager.protagonist_config = {"pov": "3인칭"}
        expander = MagicMock()
        expander.genre = "wuxia"
        expander.preset_registry = MagicMock()
        expander._STAGE0_REVIEW_MAX_ATTEMPTS = 2
        expander.review_stage0_candidate.return_value = {
            "decision": "PASS",
            "reason": "ready",
            "operator_message": "ready",
            "issues": [],
        }
        expander.generate_bible.return_value = {"MasterBible": {"ProjectData": {}}}
        expander.generate_treatment.return_value = [
            {"title": "블록 1", "content": {"context": "도입", "reward": "단서 획득"}, "ep_start": 1, "ep_end": 5},
            {"title": "블록 2", "content": {"context": "전개", "reward": "충돌 심화"}, "ep_start": 6, "ep_end": 10},
        ]

        with patch("modules.core.stage0.StoryExpander", return_value=expander):
            bible, treatment, style_guide = manager.generate_from_concept("컨셉")

        assert style_guide is None
        assert treatment == expander.generate_treatment.return_value
        roadmap = bible["MasterBible"]["plot_roadmap"]
        assert [block["block_no"] for block in roadmap] == [1, 2]
        assert roadmap[0]["title"] == "블록 1"

    def test_generate_from_concept_stops_save_after_bounded_review_failure(self):
        manager = StageZeroManager(project_path="dummy")
        manager.genre = "wuxia"
        expander = MagicMock()
        expander.genre = "wuxia"
        expander.preset_registry = MagicMock()
        expander._STAGE0_REVIEW_MAX_ATTEMPTS = 2
        expander.generate_bible.return_value = {"MasterBible": {"ProjectData": {}}}
        expander.generate_treatment.return_value = [
            {"title": "블록 1", "content": {"context": "도입", "reward": "출발"}, "ep_start": 1, "ep_end": 5}
        ]
        expander.review_stage0_candidate.side_effect = [
            {"decision": "RETRY", "reason": "retry", "operator_message": "retry", "issues": ["weak"]},
            {"decision": "REJECT", "reason": "reject", "operator_message": "reject", "issues": ["weak"]},
        ]

        with patch("modules.core.stage0.StoryExpander", return_value=expander):
            bible, treatment, style_guide = manager.generate_from_concept("컨셉")

        assert bible == {}
        assert treatment == []
        assert style_guide is None
        expander.save_all.assert_not_called()

    def test_generate_from_concept_aborts_on_bible_generation_error(self):
        manager = StageZeroManager(project_path="dummy")
        manager.genre = "wuxia"
        expander = MagicMock()
        expander.genre = "wuxia"
        expander.preset_registry = MagicMock()
        expander._STAGE0_REVIEW_MAX_ATTEMPTS = 2
        expander.generate_bible.side_effect = StoryExpander.BibleGenerationError("contract fail")

        with patch("modules.core.stage0.StoryExpander", return_value=expander):
            bible, treatment, style_guide = manager.generate_from_concept("컨셉")

        assert bible == {}
        assert treatment == []
        assert style_guide is None
        expander.generate_treatment.assert_not_called()
        expander.save_all.assert_not_called()


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
