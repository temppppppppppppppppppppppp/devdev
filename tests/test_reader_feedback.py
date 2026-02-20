"""[TF-I23/I24] Reader feedback pipeline tests — satisfaction + pacing → Blueprint."""

from unittest.mock import MagicMock

from modules.core.db_manager import DBManager


class TestPacingDBRoundTrip:
    """[TF-I24] episode_pacing 테이블 DB 라운드트립"""

    def test_save_and_load_pacing(self, temp_dir):
        """호흡 분석 결과 저장 → 조회 라운드트립"""
        db = DBManager(temp_dir / "test_pacing.db")
        try:
            db.save_pacing_record(
                5,
                {
                    "pacing_score": 72,
                    "dialogue_ratio": 0.35,
                    "scene_break_count": 6,
                    "avg_sentence_length": 28.5,
                    "short_sentence_ratio": 0.12,
                    "long_sentence_ratio": 0.08,
                    "issues": ["장면 전환 과다"],
                },
            )
            db.save_pacing_record(
                6,
                {
                    "pacing_score": 65,
                    "dialogue_ratio": 0.20,
                    "scene_break_count": 3,
                },
            )

            records = db.get_recent_pacing_records(before_ep=7, lookback=5)
            assert len(records) == 2
            assert records[0]["ep_num"] == 5  # 오래된 순
            assert records[0]["pacing_score"] == 72
            assert records[0]["dialogue_ratio"] == 0.35
            assert records[0]["issues"] == ["장면 전환 과다"]
            assert records[1]["ep_num"] == 6
            assert records[1]["pacing_score"] == 65
        finally:
            db.close()

    def test_pacing_empty_before_first_ep(self, temp_dir):
        """에피소드 없을 때 빈 리스트 반환"""
        db = DBManager(temp_dir / "test_pacing_empty.db")
        try:
            records = db.get_recent_pacing_records(before_ep=1, lookback=5)
            assert records == []
        finally:
            db.close()


class TestReaderFeedbackContext:
    """[TF-I23/I24] _build_reader_feedback_context() 테스트"""

    def _make_ensemble(self):
        from modules.domain.agents.blueprint_ensemble import BlueprintEnsembleGenerator

        context = MagicMock()
        context.author_directives = ""
        client = MagicMock()
        gen = BlueprintEnsembleGenerator(context, client, model_tier="gemini-2.5-flash")
        return gen

    def test_feedback_with_satisfaction_data(self):
        """만족도 데이터 있을 때 피드백 문자열 생성"""
        gen = self._make_ensemble()
        gen.context.db = MagicMock()
        gen.context.db.get_recent_satisfaction_tags.return_value = [
            {
                "ep_num": 8,
                "primary_tag": "성취",
                "satisfaction_score": 8,
                "protagonist_agency": "자력",
                "frustration_flag": False,
            },
            {
                "ep_num": 9,
                "primary_tag": "좌절",
                "satisfaction_score": 3,
                "protagonist_agency": "타인의존",
                "frustration_flag": True,
            },
        ]
        gen.context.db.get_recent_pacing_records.return_value = []

        result = gen._build_reader_feedback_context(ep_num=10)
        assert "제8화" in result
        assert "성취" in result
        assert "제9화" in result
        assert "좌절" in result

    def test_feedback_with_pacing_data(self):
        """호흡 데이터 있을 때 피드백 문자열 생성"""
        gen = self._make_ensemble()
        gen.context.db = MagicMock()
        gen.context.db.get_recent_satisfaction_tags.return_value = []
        gen.context.db.get_recent_pacing_records.return_value = [
            {"ep_num": 8, "pacing_score": 72, "dialogue_ratio": 0.35, "scene_break_count": 6},
            {"ep_num": 9, "pacing_score": 65, "dialogue_ratio": 0.20, "scene_break_count": 3},
        ]

        result = gen._build_reader_feedback_context(ep_num=10)
        assert "호흡 분석" in result
        assert "제8화" in result
        assert "72" in result

    def test_feedback_empty_when_no_data(self):
        """데이터 없으면 빈 문자열"""
        gen = self._make_ensemble()
        gen.context.db = MagicMock()
        gen.context.db.get_recent_satisfaction_tags.return_value = []
        gen.context.db.get_recent_pacing_records.return_value = []

        result = gen._build_reader_feedback_context(ep_num=1)
        assert result == ""

    def test_feedback_no_db_safe(self):
        """DB 없어도 안전"""
        gen = self._make_ensemble()
        gen.context.db = None

        result = gen._build_reader_feedback_context(ep_num=10)
        assert result == ""

    def test_consecutive_frustration_warning(self):
        """연속 좌절 경고 생성"""
        gen = self._make_ensemble()
        gen.context.db = MagicMock()
        gen.context.db.get_recent_satisfaction_tags.return_value = [
            {
                "ep_num": 7,
                "primary_tag": "좌절",
                "satisfaction_score": 3,
                "protagonist_agency": "타인의존",
                "frustration_flag": True,
            },
            {
                "ep_num": 8,
                "primary_tag": "좌절",
                "satisfaction_score": 2,
                "protagonist_agency": "타인의존",
                "frustration_flag": True,
            },
        ]
        gen.context.db.get_recent_pacing_records.return_value = []

        result = gen._build_reader_feedback_context(ep_num=9)
        assert "능동적 활약" in result


class TestPacingSaveInPostProcessor:
    """[TF-I24] Stage4 PASS 후 호흡 저장"""

    def test_pacing_save_called(self, tmp_path):
        from modules.core.stage4_post_processor import Stage4PostProcessor

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.sys = MagicMock()
        ctx.sys.hud = MagicMock()
        ctx.sys.hud.snapshot.return_value = {}
        ctx.sys.hud.bulk_update = MagicMock()

        director = MagicMock()
        director.on_approve_workflow.return_value = {}
        manager = MagicMock()
        manager.update_state_and_lore_v20.return_value = {}
        state_extractor = MagicMock()
        state_extractor.extract_satisfaction_tag.return_value = None

        ctx.agents = {"director": director, "manager": manager, "state_extractor": state_extractor}

        db = MagicMock()
        db.conn = MagicMock()
        db.get_episode_bible.return_value = {}
        db.load_anchor.return_value = []
        db.transaction.return_value.__enter__ = MagicMock(return_value=None)
        db.transaction.return_value.__exit__ = MagicMock(return_value=False)

        project = MagicMock()
        project.db = db
        project.name = "test"
        project.latest_state = {}
        project.seed_tracker = None
        project.karma_matrix = {}
        project.master_bible = {
            "MasterBible": {"AssetLibrary": {"KeyNPCs": []}, "protagonist_config": {"name": "주인공"}},
            "npc_registry": {},
        }
        ctx.current_project = project

        # PacingAnalyzer mock
        from dataclasses import dataclass

        @dataclass
        class FakePacingResult:
            pacing_score: int = 72
            dialogue_ratio: float = 0.35
            scene_break_count: int = 6
            avg_sentence_length: float = 28.5
            short_sentence_ratio: float = 0.12
            long_sentence_ratio: float = 0.08
            issues: list = None

            def __post_init__(self):
                if self.issues is None:
                    self.issues = []

        pacing_analyzer = MagicMock()
        pacing_analyzer.analyze.return_value = FakePacingResult()
        ctx.pacing_analyzer = pacing_analyzer

        ctx.memory = None
        ctx.state_tracker = None
        ctx.world_state = None
        ctx.fact_ledger = None
        ctx.character_voice = None
        ctx.foreshadow_tracker = None
        ctx.failure_learner = None
        ctx.quality_dashboard = None
        ctx.perf_timer = MagicMock()
        ctx.flush_audit_buffer = MagicMock()
        ctx.get_protagonist_name = lambda: "주인공"
        ctx.generate_narrative_summary = MagicMock()

        pp = Stage4PostProcessor(ctx)
        pp.ctx.current_project.db.save_manuscript.return_value = True

        pp.process_pass_result(
            next_ep=5,
            final_manuscript="테스트 원고 " * 500,
            final_title="테스트",
            final_state_updates={},
            blueprint={"scene_breakdown": []},
            arc_data={"arc_no": 1},
            output_dir=tmp_path,
            v50_modules_available=False,
            extract_chain_link_fn=lambda *_args, **_kwargs: {},
        )

        # save_pacing_record 호출 확인
        db.save_pacing_record.assert_called_once()
        call_args = db.save_pacing_record.call_args
        assert call_args[0][0] == 5  # ep_num
        assert call_args[0][1]["pacing_score"] == 72
