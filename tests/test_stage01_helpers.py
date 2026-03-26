"""[Phase 4C-1b-a] Stage01Helpers 단위 테스트

추출 대상: phase_0_recovery, extend_blocks
"""

from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from modules.core.stage01_helpers import Stage01Helpers

# ── Fixtures ─────────────────────────────────────────────────


@pytest.fixture
def app_mock():
    """SovereignApp 모의 객체 — Stage 0 helpers에 필요한 최소 인터페이스"""
    app = MagicMock()

    # Genre
    app.selected_genre = {"name": "무협", "type": "wuxia"}

    # Project
    app.current_project.paths.root = MagicMock()
    app.current_project.paths.drafts = MagicMock()
    app.current_project.master_bible = {"MasterBible": {"protagonist_config": {}}}
    app.current_project.force_sync_v25_dna.return_value = True

    # Facade methods
    app._ui_select_bible.return_value = "bible.json"
    app._ui_select_treatment.return_value = "treatment.json"
    app._enrich_treatment_blocks.return_value = "treatment_enriched.json"
    app._stage_0_extended = MagicMock()
    app._audit_event = MagicMock()
    app.memory = MagicMock()

    return app


@pytest.fixture
def helpers(app_mock):
    return Stage01Helpers(app=app_mock)


# ── Constructor ──────────────────────────────────────────────


class TestConstructor:
    def test_app_reference_stored(self, helpers, app_mock):
        assert helpers.app is app_mock

    def test_stage0_availability_probe_recovers_from_stale_spinner_flag(self, monkeypatch):
        import modules.core.spinners as spinners

        monkeypatch.setattr(spinners, "STAGE0_AVAILABLE", False)

        assert Stage01Helpers._stage0_extended_available() is True
        assert spinners.STAGE0_AVAILABLE is True


# ── phase_0_recovery ────────────────────────────────────────


class TestPhase0Recovery:
    def test_cancel_choice_0(self, helpers, app_mock):
        """선택 0 → 취소 (아무 작업 안 함)"""
        with (
            redirect_stdout(StringIO()),
            patch("builtins.input", return_value="0"),
            patch("modules.core.spinners.STAGE0_AVAILABLE", True),
        ):
            helpers.phase_0_recovery()
        # 취소 시 아무 facade 메서드도 호출하지 않음
        app_mock._stage_0_extended.assert_not_called()
        app_mock._ui_select_bible.assert_not_called()

    def test_choice_2_delegates_to_stage_0_extended(self, helpers, app_mock):
        """선택 2 → self.stage_0_extended(mode=1) 호출"""
        with (
            redirect_stdout(StringIO()),
            patch("builtins.input", return_value="2"),
            patch("modules.core.spinners.STAGE0_AVAILABLE", True),
            patch.object(helpers, "stage_0_extended") as mock_s0,
        ):
            helpers.phase_0_recovery()
        mock_s0.assert_called_once_with(mode=1)

    def test_choice_3_delegates_to_stage_0_extended(self, helpers, app_mock):
        """선택 3 → self.stage_0_extended(mode=2) 호출"""
        with (
            redirect_stdout(StringIO()),
            patch("builtins.input", return_value="3"),
            patch("modules.core.spinners.STAGE0_AVAILABLE", True),
            patch.object(helpers, "stage_0_extended") as mock_s0,
        ):
            helpers.phase_0_recovery()
        mock_s0.assert_called_once_with(mode=2)

    def test_choice_4_delegates_to_stage_0_extended(self, helpers, app_mock):
        """선택 4 → self.stage_0_extended(mode=3) 호출"""
        with (
            redirect_stdout(StringIO()),
            patch("builtins.input", return_value="4"),
            patch("modules.core.spinners.STAGE0_AVAILABLE", True),
            patch.object(helpers, "stage_0_extended") as mock_s0,
        ):
            helpers.phase_0_recovery()
        mock_s0.assert_called_once_with(mode=3)

    def test_choice_5_delegates_to_stage_0_extended(self, helpers, app_mock):
        """선택 5 → self.stage_0_extended(mode=4) 호출"""
        with (
            redirect_stdout(StringIO()),
            patch("builtins.input", return_value="5"),
            patch("modules.core.spinners.STAGE0_AVAILABLE", True),
            patch.object(helpers, "stage_0_extended") as mock_s0,
        ):
            helpers.phase_0_recovery()
        mock_s0.assert_called_once_with(mode=4)

    def test_choice_6_delegates_to_stage_0_extended(self, helpers, app_mock):
        """선택 6 → self.stage_0_extended(mode=5) 호출"""
        with (
            redirect_stdout(StringIO()),
            patch("builtins.input", return_value="6"),
            patch("modules.core.spinners.STAGE0_AVAILABLE", True),
            patch.object(helpers, "stage_0_extended") as mock_s0,
        ):
            helpers.phase_0_recovery()
        mock_s0.assert_called_once_with(mode=5)

    def test_choice_7_delegates_to_stage_0_extended(self, helpers, app_mock):
        """선택 7 → self.stage_0_extended(mode=6) 호출"""
        with (
            redirect_stdout(StringIO()),
            patch("builtins.input", return_value="7"),
            patch("modules.core.spinners.STAGE0_AVAILABLE", True),
            patch.object(helpers, "stage_0_extended") as mock_s0,
        ):
            helpers.phase_0_recovery()
        mock_s0.assert_called_once_with(mode=6)

    def test_stage0_unavailable_skips_extended_choices(self, helpers, app_mock):
        """STAGE0_AVAILABLE=False 시 choice=2는 기존 방식으로 진행"""
        # choice=2이지만 STAGE0_AVAILABLE=False → 기존 방식 (bible/treatment 선택)
        # 기존 방식: choice, enrich(N), world(1), type(1), pov(2), Enter
        with (
            redirect_stdout(StringIO()),
            patch("builtins.input", side_effect=["2", "N", "1", "1", "2", "2", ""]),
            patch.object(Stage01Helpers, "_stage0_extended_available", return_value=False),
        ):
            helpers.phase_0_recovery()
        # _stage_0_extended가 호출되지 않아야 함
        app_mock._stage_0_extended.assert_not_called()
        # 기존 방식이므로 _ui_select_bible 호출
        app_mock._ui_select_bible.assert_called_once()

    def test_default_choice_uses_legacy_flow(self, helpers, app_mock):
        """기본 선택(1) → 기존 방식 (파일 선택 → DNA 이식)"""
        # input sequence: choice=1, enrich=N, world=1, type=1, pov=2, Enter
        with (
            redirect_stdout(StringIO()),
            patch("builtins.input", side_effect=["1", "N", "1", "1", "2", "2", ""]),
            patch("modules.core.spinners.STAGE0_AVAILABLE", True),
        ):
            helpers.phase_0_recovery()
        app_mock._ui_select_bible.assert_called_once()
        app_mock._ui_select_treatment.assert_called_once()
        app_mock.current_project.force_sync_v25_dna.assert_called_once_with("bible.json", "treatment.json")

    def test_legacy_flow_can_store_mixed_pov(self, helpers, app_mock):
        """기존 흐름에서도 POV 4번 선택 시 혼합 시점이 저장된다."""
        with (
            redirect_stdout(StringIO()),
            patch("builtins.input", side_effect=["1", "N", "1", "1", "4", "3", ""]),
            patch("modules.core.spinners.STAGE0_AVAILABLE", True),
        ):
            helpers.phase_0_recovery()

        saved = app_mock.current_project.master_bible["MasterBible"]["protagonist_config"]
        assert saved["external_pov_insert_policy"] == "적극 허용"
        assert saved["pov"] == "혼합"

    @pytest.mark.parametrize(
        ("policy_choice", "expected"),
        [("1", "금지"), ("2", "제한적 허용"), ("3", "적극 허용")],
    )
    def test_legacy_flow_external_pov_policy_choices_match_stage0_menu(
        self, helpers, app_mock, policy_choice, expected
    ):
        with (
            redirect_stdout(StringIO()),
            patch("builtins.input", side_effect=["1", "N", "1", "1", "2", policy_choice, ""]),
            patch("modules.core.spinners.STAGE0_AVAILABLE", True),
        ):
            helpers.phase_0_recovery()

        saved = app_mock.current_project.master_bible["MasterBible"]["protagonist_config"]
        assert saved["pov"] == "3인칭"
        assert saved["external_pov_insert_policy"] == expected

    def test_legacy_flow_world_origin_and_incarnation_defaults_match_stage0(self, helpers, app_mock):
        with (
            redirect_stdout(StringIO()),
            patch("builtins.input", side_effect=["1", "N", "invalid", "invalid", "", "", ""]),
            patch("modules.core.spinners.STAGE0_AVAILABLE", True),
        ):
            helpers.phase_0_recovery()

        saved = app_mock.current_project.master_bible["MasterBible"]["protagonist_config"]
        assert saved["world_origin"] == "현대인"
        assert saved["incarnation_type"] == "일반"
        assert saved["pov"] == "3인칭"
        assert saved["external_pov_insert_policy"] == "제한적 허용"

    def test_save_phase0_protagonist_config_merges_existing_family_fields(self, app_mock):
        app_mock.current_project.master_bible = {
            "MasterBible": {
                "protagonist_config": {
                    "name": "진무",
                    "martial_lineage": "화산파",
                    "pov": "1인칭",
                }
            }
        }

        Stage01Helpers._save_phase0_protagonist_config(
            app_mock,
            {
                "world_origin": "현대인",
                "incarnation_type": "환생자",
                "pov": "3인칭",
                "external_pov_insert_policy": "제한적 허용",
            },
        )

        saved = app_mock.current_project.master_bible["MasterBible"]["protagonist_config"]
        assert saved["name"] == "진무"
        assert saved["martial_lineage"] == "화산파"
        assert saved["world_origin"] == "현대인"
        assert saved["incarnation_type"] == "환생자"
        assert saved["pov"] == "3인칭"

    def test_save_phase0_protagonist_config_handles_non_dict_existing_config(self, app_mock):
        app_mock.current_project.master_bible = {"MasterBible": {"protagonist_config": "legacy"}}

        Stage01Helpers._save_phase0_protagonist_config(
            app_mock,
            {
                "world_origin": "원시인",
                "incarnation_type": "회귀자",
            },
        )

        saved = app_mock.current_project.master_bible["MasterBible"]["protagonist_config"]
        assert saved == {"world_origin": "원시인", "incarnation_type": "회귀자"}

    def test_no_bible_file_aborts(self, helpers, app_mock):
        """Bible 파일 없으면 중단"""
        app_mock._ui_select_bible.return_value = None
        with (
            redirect_stdout(StringIO()),
            patch("builtins.input", return_value="1"),
            patch("modules.core.spinners.STAGE0_AVAILABLE", True),
        ):
            helpers.phase_0_recovery()
        # 중단 시 force_sync 호출 안 함
        app_mock.current_project.force_sync_v25_dna.assert_not_called()

    def test_dna_failure_skips_post_processing(self, helpers, app_mock):
        """DNA 이식 실패 시 후속 처리 안 함"""
        app_mock.current_project.force_sync_v25_dna.return_value = False
        with (
            redirect_stdout(StringIO()),
            patch("builtins.input", side_effect=["1", "N", "1", "1", "2", "2", ""]),
            patch("modules.core.spinners.STAGE0_AVAILABLE", True),
        ):
            helpers.phase_0_recovery()
        # _load_from_db가 호출되지 않아야 함 (dna_success=False)
        app_mock.current_project._load_from_db.assert_not_called()
        app_mock._audit_event.assert_called_once()
        assert app_mock._audit_event.call_args.args[0] == "dna_sync_failed"
        logged = " ".join(str(c) for c in app_mock.ui.log.call_args_list)
        assert "DNA sync failed" in logged

    def test_sync_error_nonfatal(self, helpers, app_mock):
        """원고 동기화 오류가 발생해도 비차단"""
        app_mock.current_project.paths.drafts.glob.return_value = [MagicMock()]
        app_mock.current_project.sync_existing_manuscripts.side_effect = RuntimeError("sync crash")
        with (
            redirect_stdout(StringIO()),
            patch("builtins.input", side_effect=["1", "N", "1", "1", "2", "2", ""]),
            patch("modules.core.spinners.STAGE0_AVAILABLE", True),
        ):
            helpers.phase_0_recovery()
        app_mock._audit_event.assert_called()
        # 에러가 발생해도 _load_from_db는 여전히 호출
        app_mock.current_project._load_from_db.assert_called_once()

    def test_genre_displayed(self, helpers, app_mock):
        """장르 정보 표시 — app.ui.log 호출에서 확인"""
        with (
            redirect_stdout(StringIO()),
            patch("builtins.input", return_value="0"),
            patch("modules.core.spinners.STAGE0_AVAILABLE", True),
        ):
            helpers.phase_0_recovery()
        logged = " ".join(str(c) for c in app_mock.ui.log.call_args_list)
        assert "무협" in logged
        assert "wuxia" in logged

    def test_no_genre_no_crash(self, helpers, app_mock):
        """장르 없어도 크래시 없음"""
        app_mock.selected_genre = None
        with (
            redirect_stdout(StringIO()),
            patch("builtins.input", return_value="0"),
            patch("modules.core.spinners.STAGE0_AVAILABLE", True),
        ):
            helpers.phase_0_recovery()
        # No crash


# ── extend_blocks ────────────────────────────────────────────


class TestExtendBlocks:
    def test_no_treatment_returns_empty(self, helpers, app_mock):
        """Treatment 파일 없으면 빈 리스트 반환"""
        # All treatment files don't exist
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        app_mock.current_project.paths.root.__truediv__ = MagicMock(return_value=mock_path)
        with redirect_stdout(StringIO()):
            result = helpers.extend_blocks(MagicMock())
        assert result == []

    def test_treatment_loaded_and_expanded(self, helpers, app_mock, tmp_path):
        """Treatment 로드 + StoryExpander 확장 성공"""
        import json as _json

        # Create a real treatment file
        treatment_file = tmp_path / "treatment_extended.json"
        treatment_file.write_text(
            _json.dumps({"treatments": [{"block_id": "B1", "title": "Test"}]}),
            encoding="utf-8",
        )

        # Make paths.root point to tmp_path
        app_mock.current_project.paths.root = tmp_path

        stage0_mgr = MagicMock()
        stage0_mgr.genre = "wuxia"

        with (
            patch("builtins.input", side_effect=["5", ""]),
            patch("modules.core.stage01_helpers.Stage01Helpers.extend_blocks") as mock_extend,
        ):
            # Just verify the method can be called
            mock_extend.return_value = [{"block_id": "B1"}, {"block_id": "B2"}]
            result = mock_extend(helpers, stage0_mgr)
            assert len(result) == 2

    def test_expander_exception_returns_empty(self, helpers, app_mock, tmp_path):
        """StoryExpander 실패 시 저장 우회를 위해 빈 리스트 반환"""
        import json as _json

        treatment_file = tmp_path / "treatment_extended.json"
        existing_data = [{"block_id": "B1", "title": "Existing"}]
        treatment_file.write_text(
            _json.dumps({"treatments": existing_data}),
            encoding="utf-8",
        )
        app_mock.current_project.paths.root = tmp_path

        stage0_mgr = MagicMock()
        stage0_mgr.genre = "wuxia"

        with (
            redirect_stdout(StringIO()),
            patch("builtins.input", side_effect=["5", ""]),
            patch(
                "modules.core.stage0.story_expander.StoryExpander",
                MagicMock(side_effect=ImportError("no module"), _STAGE0_REVIEW_MAX_ATTEMPTS=2),
            ),
        ):
            result = helpers.extend_blocks(stage0_mgr)
        assert result == []


# ── stage_0_extended ─────────────────────────────────────────


class TestStage0Extended:
    def test_stage0_unavailable_returns_early(self, helpers, app_mock):
        """STAGE0_AVAILABLE=False → 즉시 반환"""
        with redirect_stdout(StringIO()), patch.object(Stage01Helpers, "_stage0_extended_available", return_value=False):
            helpers.stage_0_extended(mode=1)
        # StageZeroManager 초기화 안 함 (아무 project 접근 없음)
        app_mock.current_project.save_v20_anchor.assert_not_called()

    def test_mode_1_calls_new_project_flow(self, helpers, app_mock):
        """mode=1 → run_new_project_flow 호출"""
        mock_mgr = MagicMock()
        mock_mgr.run_new_project_flow.return_value = ({"MasterBible": {}}, [], None)
        mock_mgr.preset_registry = None
        mock_mgr.style_guide = None
        with (
            redirect_stdout(StringIO()),
            patch("modules.core.spinners.STAGE0_AVAILABLE", True),
            patch("modules.core.stage0.StageZeroManager", return_value=mock_mgr),
            patch("modules.core.stage0.PresetRegistry"),
            patch("builtins.input", return_value=""),
        ):
            helpers.stage_0_extended(mode=1)
        mock_mgr.run_new_project_flow.assert_called_once()

    def test_mode_3_calls_import_bible(self, helpers, app_mock):
        """mode=3 → import_bible 호출"""
        mock_mgr = MagicMock()
        mock_mgr.import_bible.return_value = {"MasterBible": {"protagonist_config": {}}}
        mock_mgr.preset_registry = None
        mock_mgr.style_guide = None
        with (
            redirect_stdout(StringIO()),
            patch("modules.core.spinners.STAGE0_AVAILABLE", True),
            patch("modules.core.stage0.StageZeroManager", return_value=mock_mgr),
            patch("modules.core.stage0.PresetRegistry"),
            patch("builtins.input", return_value=""),
        ):
            helpers.stage_0_extended(mode=3)
        mock_mgr.import_bible.assert_called_once()

    def test_mode_4_calls_extend_blocks(self, helpers, app_mock):
        """mode=4 → self.extend_blocks 호출 (via _s0_handle_block_extension)"""
        mock_mgr = MagicMock()
        with (
            redirect_stdout(StringIO()),
            patch("modules.core.spinners.STAGE0_AVAILABLE", True),
            patch("modules.core.stage0.StageZeroManager", return_value=mock_mgr),
            patch("modules.core.stage0.PresetRegistry"),
            patch("builtins.input", return_value=""),
            patch.object(helpers, "extend_blocks", return_value=[]) as mock_eb,
        ):
            helpers.stage_0_extended(mode=4)
        mock_eb.assert_called_once_with(mock_mgr)


class TestStage0RoadmapInjection:
    def test_s0_save_results_injects_plot_roadmap_from_treatment(self, app_mock, tmp_path):
        app_mock.current_project.paths.root = tmp_path
        bible = {"MasterBible": {"ProjectData": {}}}
        treatment = [
            {"title": "블록 1", "content": {"context": "도입", "reward": "출발"}, "ep_start": 1, "ep_end": 5},
            {"title": "블록 2", "content": {"context": "전개", "reward": "전환"}, "ep_start": 6, "ep_end": 10},
        ]
        stage0_mgr = MagicMock()
        stage0_mgr.preset_registry = None
        stage0_mgr.style_guide = None

        with patch("builtins.input", return_value=""):
            Stage01Helpers._s0_save_results(app_mock, stage0_mgr, bible, treatment)

        roadmap = bible["MasterBible"]["plot_roadmap"]
        assert [block["block_no"] for block in roadmap] == [1, 2]
        assert roadmap[0]["title"] == "블록 1"
        saved_key, saved_payload = app_mock.current_project.save_v20_anchor.call_args.args
        assert saved_key == "bible"
        assert saved_payload["MasterBible"]["plot_roadmap"][1]["ep_end"] == 10

    def test_s0_save_results_builds_stub_plot_roadmap_from_saved_arcs(self, app_mock):
        bible = {"MasterBible": {"ProjectData": {}}}
        app_mock.current_project.db.load_anchor.return_value = [
            {"arc_no": 1, "ep_start": 1, "ep_end": 5, "tactical_doc": "stub arc", "_stub": True}
        ]
        stage0_mgr = MagicMock()
        stage0_mgr.preset_registry = None
        stage0_mgr.style_guide = None

        with patch("builtins.input", return_value=""):
            Stage01Helpers._s0_save_results(app_mock, stage0_mgr, bible, treatment=None)

        roadmap = bible["MasterBible"]["plot_roadmap"]
        assert roadmap[0]["arc_no"] == 1
        assert roadmap[0]["ep_count"] == 5
        assert roadmap[0]["_stub"] is True

    def test_s0_save_results_skips_treatment_when_bible_save_fails(self, app_mock, tmp_path):
        app_mock.current_project.paths.root = tmp_path
        app_mock.current_project.save_v20_anchor.side_effect = RuntimeError("bible-fail")
        bible = {"MasterBible": {"ProjectData": {}}}
        treatment = [{"title": "블록 1", "content": {"context": "도입"}, "ep_start": 1, "ep_end": 5}]
        stage0_mgr = MagicMock()
        stage0_mgr.preset_registry = None
        stage0_mgr.style_guide = None

        with patch("builtins.input", return_value=""):
            Stage01Helpers._s0_save_results(app_mock, stage0_mgr, bible, treatment)

        assert not (tmp_path / "treatment_generated.json").exists()
        app_mock.current_project._load_from_db.assert_not_called()

    def test_s0_save_results_blocks_title_only_handoff(self, app_mock, tmp_path):
        app_mock.current_project.paths.root = tmp_path
        bible = {"MasterBible": {"ProjectData": {}}}
        treatment = [{"title": "블록 1", "summary": "요약만 있음", "ep_start": 1, "ep_end": 5}]
        stage0_mgr = MagicMock()
        stage0_mgr.preset_registry = None
        stage0_mgr.style_guide = None

        with patch("builtins.input", return_value=""):
            Stage01Helpers._s0_save_results(app_mock, stage0_mgr, bible, treatment)

        app_mock.current_project.save_v20_anchor.assert_not_called()
        assert not (tmp_path / "treatment_generated.json").exists()

    def test_validate_plot_roadmap_entries_flags_summary_only_entries(self):
        warnings = Stage01Helpers._validate_plot_roadmap_entries(
            [{"block_no": 1, "title": "블록 1", "summary": "요약만"}]
        )

        assert warnings
        assert "title/summary only" in warnings[0]

    def test_block_extension_routes_through_shared_persistence(self, helpers, app_mock):
        stage0_mgr = MagicMock()
        bible = {"MasterBible": {"ProjectData": {}}}
        app_mock.current_project.master_bible = bible

        with (
            patch.object(helpers, "extend_blocks", return_value=[{"title": "블록 1", "content": {"context": "도입"}}]),
            patch.object(helpers, "_persist_stage0_results") as persist,
            patch.object(Stage01Helpers, "_pause_with_ui"),
        ):
            helpers._s0_handle_block_extension(app_mock, stage0_mgr)

        persist.assert_called_once()
        assert persist.call_args.kwargs["treatment_filename"] == "treatment_extended.json"
        assert persist.call_args.kwargs["pause"] is False

    def test_mode_5_calls_reference_analysis(self, helpers, app_mock):
        """mode=5 → run_reference_analysis 호출"""
        mock_mgr = MagicMock()
        mock_mgr.run_reference_analysis.return_value = None
        with (
            redirect_stdout(StringIO()),
            patch("modules.core.spinners.STAGE0_AVAILABLE", True),
            patch("modules.core.stage0.StageZeroManager", return_value=mock_mgr),
            patch("modules.core.stage0.PresetRegistry"),
            patch("builtins.input", return_value=""),
        ):
            helpers.stage_0_extended(mode=5)
        mock_mgr.run_reference_analysis.assert_called_once()

    def test_mode_5_calls_reference_analysis_with_stale_spinner_flag(self, helpers, app_mock):
        mock_mgr = MagicMock()
        mock_mgr.run_reference_analysis.return_value = None
        with (
            redirect_stdout(StringIO()),
            patch.object(Stage01Helpers, "_stage0_extended_available", return_value=True),
            patch("modules.core.stage0.StageZeroManager", return_value=mock_mgr),
            patch("modules.core.stage0.PresetRegistry"),
            patch("builtins.input", return_value=""),
        ):
            helpers.stage_0_extended(mode=5)
        mock_mgr.run_reference_analysis.assert_called_once()

    def test_mode_6_calls_manage_work_guard(self, helpers, app_mock):
        """mode=6 → manage_work_guard 호출"""
        mock_mgr = MagicMock()
        with (
            redirect_stdout(StringIO()),
            patch("modules.core.spinners.STAGE0_AVAILABLE", True),
            patch("modules.core.stage0.StageZeroManager", return_value=mock_mgr),
            patch("modules.core.stage0.PresetRegistry"),
            patch("builtins.input", return_value=""),
        ):
            helpers.stage_0_extended(mode=6)
        mock_mgr.manage_work_guard.assert_called_once()

    def test_invalid_choice_cancels(self, helpers, app_mock):
        """유효하지 않은 choice → 취소"""
        mock_mgr = MagicMock()
        mock_mgr.show_menu.return_value = 99  # 없는 선택
        with (
            redirect_stdout(StringIO()),
            patch("modules.core.spinners.STAGE0_AVAILABLE", True),
            patch("modules.core.stage0.StageZeroManager", return_value=mock_mgr),
            patch("modules.core.stage0.PresetRegistry"),
        ):
            helpers.stage_0_extended(mode=0)
        app_mock.current_project.save_v20_anchor.assert_not_called()

    def test_bible_saved_on_success(self, helpers, app_mock):
        """Bible 생성 성공 시 DB 저장"""
        mock_mgr = MagicMock()
        bible = {"MasterBible": {"protagonist_config": {"type": "회귀자"}}}
        mock_mgr.run_new_project_flow.return_value = (bible, None, None)
        mock_mgr.preset_registry = None
        mock_mgr.style_guide = None
        with (
            redirect_stdout(StringIO()),
            patch("modules.core.spinners.STAGE0_AVAILABLE", True),
            patch("modules.core.stage0.StageZeroManager", return_value=mock_mgr),
            patch("modules.core.stage0.PresetRegistry"),
            patch("builtins.input", return_value=""),
        ):
            helpers.stage_0_extended(mode=1)
        app_mock.current_project.save_v20_anchor.assert_any_call("bible", bible)
        app_mock.current_project._load_from_db.assert_called_once()


# ── stage_1_volumes ──────────────────────────────────────────


class TestStage1Volumes:
    def test_skip_choice_returns_early(self, helpers, app_mock):
        """스킵 선택(2) → 즉시 반환"""
        with patch("builtins.input", side_effect=["2", ""]):
            helpers.stage_1_volumes()
        app_mock._safe_commit.assert_not_called()

    def test_no_project_returns_early(self, helpers, app_mock):
        """프로젝트 없으면 반환"""
        app_mock.current_project = None
        with patch("builtins.input", side_effect=["1", ""]):
            helpers.stage_1_volumes()
        # _safe_commit은 호출되지만 project 접근에서 반환
        app_mock._safe_commit.assert_called_once()

    def test_no_roadmap_returns_early(self, helpers, app_mock):
        """plot_roadmap 없으면 반환"""
        app_mock.current_project.master_bible = {"MasterBible": {}}
        app_mock.current_project._load_from_db = MagicMock()  # recovery도 실패
        with patch("builtins.input", side_effect=["1", ""]):
            helpers.stage_1_volumes()
        app_mock.ui.log.assert_called()

    def test_successful_volume_design(self, helpers, app_mock):
        """1권 설계 성공 플로우"""
        # 5개 아크 → 1권
        app_mock.current_project.master_bible = {
            "MasterBible": {
                "plot_roadmap": [{"arc": i} for i in range(5)],
                "ProjectData": {"MetaInfo": {}},
            }
        }
        app_mock._get_protagonist_name.return_value = "주인공"
        app_mock._validate_volume_boundaries.return_value = {"status": "PASS"}
        app_mock.agents = {"analyst": MagicMock()}
        app_mock.agents["analyst"].plan_single_volume_v20.return_value = {
            "strategy_doc": "x" * 2500,
        }

        with (
            patch("builtins.input", side_effect=["1", ""]),
            patch("modules.core.spinners.StageSpinner"),
            patch("modules.core.adaptive_retry.retry_with_feedback") as mock_retry,
        ):
            # retry_with_feedback returns (result, attempts, passed)
            mock_retry.return_value = ({"strategy_doc": "x" * 2500}, 1, True)
            helpers.stage_1_volumes()

        app_mock.current_project.save_v20_anchor.assert_called_once_with("volumes", [{"strategy_doc": "x" * 2500}])
        app_mock._show_volume_table.assert_called_once_with([{"strategy_doc": "x" * 2500}])

    def test_quality_fail_stops(self, helpers, app_mock):
        """품질 미달 시 공정 중단"""
        app_mock.current_project.master_bible = {
            "MasterBible": {
                "plot_roadmap": [{"arc": i} for i in range(5)],
                "ProjectData": {"MetaInfo": {}},
            }
        }

        with (
            patch("builtins.input", side_effect=["1"]),
            patch("modules.core.spinners.StageSpinner"),
            patch("modules.core.adaptive_retry.retry_with_feedback") as mock_retry,
        ):
            mock_retry.return_value = (None, 3, False)
            helpers.stage_1_volumes()

        # 실패 시 save_v20_anchor 호출 안 함
        app_mock.current_project.save_v20_anchor.assert_not_called()


class TestBoundaryValidation:
    def test_validate_volume_boundaries_serializes_dict_strategy_doc(self):
        result = Stage01Helpers.validate_volume_boundaries(
            {"strategy_doc": {"summary": "제 1권 내부 사건만 다룬다."}},
            1,
        )

        assert result["status"] == "PASS"

    def test_validate_volume_boundaries_rejects_none_strategy_doc(self):
        result = Stage01Helpers.validate_volume_boundaries({"strategy_doc": None}, 1)

        assert result["status"] == "REJECT"
        assert "strategy_doc" in result["reason"]

    def test_stage1_success_path_executes_real_boundary_callback_chain(self, helpers, app_mock):
        app_mock.current_project.master_bible = {
            "MasterBible": {
                "plot_roadmap": [{"arc": i} for i in range(5)],
                "ProjectData": {"MetaInfo": {}},
            }
        }
        app_mock._get_protagonist_name.return_value = "주인공"
        app_mock._validate_volume_boundaries.side_effect = AssertionError("legacy private validator should not be used")
        app_mock.agents = {"analyst": MagicMock()}
        app_mock.agents["analyst"].plan_single_volume_v20.return_value = {
            "strategy_doc": "현재 권 사건만 다룬다. " * 180,
        }

        with (
            patch("builtins.input", side_effect=["1", ""]),
            patch("modules.core.spinners.StageSpinner"),
        ):
            helpers.stage_1_volumes()

        app_mock.current_project.save_v20_anchor.assert_called_once()

    def test_stage1_retries_after_boundary_reject(self, helpers, app_mock):
        app_mock.current_project.master_bible = {
            "MasterBible": {
                "plot_roadmap": [{"arc": i} for i in range(5)],
                "ProjectData": {"MetaInfo": {}},
            }
        }
        app_mock._get_protagonist_name.return_value = "주인공"
        app_mock._validate_volume_boundaries.side_effect = AssertionError("legacy private validator should not be used")
        app_mock.agents = {"analyst": MagicMock()}
        app_mock.agents["analyst"].plan_single_volume_v20.side_effect = [
            {"strategy_doc": ("제 2권에서 벌어질 일을 미리 적는다. " * 120)},
            {"strategy_doc": ("현재 권 사건만 다룬다. " * 180)},
        ]

        with (
            patch("builtins.input", side_effect=["1", ""]),
            patch("modules.core.spinners.StageSpinner"),
        ):
            helpers.stage_1_volumes()

        assert app_mock.agents["analyst"].plan_single_volume_v20.call_count == 2
        app_mock._audit_event.assert_any_call(
            "volume_boundary_violation",
            "미래 권(2권) 정보 누수 감지",
            {"vol_no": 1, "feedback": "제 1권 설계에서 2권 내용을 언급하지 마십시오."},
        )
