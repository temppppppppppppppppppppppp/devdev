import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from modules.core.character_voice_profiler import CharacterVoiceProfiler
from modules.core.genre_guards.wuxia_guard import WuxiaGuard
from modules.core.narrative_diversity import NarrativeDiversityEngine
from modules.core.project_manager import ProjectContext
from modules.core.services.project_service import ProjectService
from modules.domain.agents.manuscript_validator import ManuscriptValidator
from modules.validation.consistency_validator import ConsistencyValidator
from modules.validation.pre_llm_validator import PreLLMValidator


def test_base_guard_unresolved_conflict_escapes_npc_name():
    guard = WuxiaGuard()
    result = guard.check_unresolved_conflict(
        "적(왕과 함께 이동했다.",
        {
            "적(왕": {
                "events": [{"type": "공격"}],
                "relation_type": "enemy",
            }
        },
        7,
    )
    assert isinstance(result, dict)
    assert "violations" in result


def test_base_guard_villain_response_escapes_villain_name():
    guard = WuxiaGuard()
    result = guard.check_villain_response(
        "흑막(왕은 분노했다.",
        {"villain_name": "흑막(왕", "villain_role": "주적", "is_aware": True},
        [{"type": "대역전"}],
    )
    assert isinstance(result, dict)
    assert "passed" in result


def test_consistency_validator_effect_pattern_escapes_item_and_use():
    validator = ConsistencyValidator(guard=WuxiaGuard())
    result = validator._check_effect_consistency(
        "천뢰(검으로 치유를 시도했다.",
        {
            "천뢰(검": {
                "cannot_be_used_for": ["치유"],
                "transformation_allowed": False,
            }
        },
    )
    assert isinstance(result, dict)
    assert result["passed"] is False


def test_consistency_validator_relation_pattern_escapes_npc_name():
    validator = ConsistencyValidator(guard=WuxiaGuard())
    result = validator._check_relation_dynamics(
        "적(왕이 충성을 맹세했다.",
        {
            "적(왕": {
                "events": [{"type": "betrayal"}],
                "relation_type": "enemy",
            }
        },
        {"prev_episode_events": []},
    )
    assert isinstance(result, dict)
    assert "violations" in result


def test_manuscript_validator_alive_pattern_escapes_dead_npc_name():
    validator = ManuscriptValidator(context=SimpleNamespace(master_bible={}))
    validator._dead_npcs = {"적(왕"}
    result = validator._check_basic_continuity("적(왕이 말했다.", "이전 내용", "")
    assert isinstance(result, dict)
    assert "warnings" in result


def test_character_voice_profiler_dialogue_pattern_escapes_name():
    profiler = CharacterVoiceProfiler(db_manager=None, genre="wuxia")
    dialogues = profiler._extract_character_dialogues("적(왕", '적(왕이 "살아남아라"라고 말했다.')
    assert isinstance(dialogues, list)


def test_pre_llm_validator_npc_naming_escapes_correct_name():
    validator = PreLLMValidator()
    result = validator._check_npc_naming(
        "천뢰(겸이 등장했다.",
        {"npc_profiles": {"천뢰(검": {}}},
    )
    assert isinstance(result, dict)
    assert "inconsistencies" in result


def test_project_manager_backtrack_uses_latest_episode_minus_one():
    pm = ProjectContext.__new__(ProjectContext)
    pm.db = MagicMock()
    pm.db.get_rollback_impact.return_value = {}
    pm.get_latest_episode_number = MagicMock(return_value=11)
    pm.reset_project = MagicMock()

    fake_match = MagicMock()
    fake_match.group.return_value = "5"
    with patch("modules.core.project_manager.re.search", return_value=fake_match):
        target_ep = pm.auto_backtrack_v35("모순 리포트", memory=None)

    assert target_ep == 7
    pm.reset_project.assert_called_once_with(7)


def test_narrative_diversity_uses_last_n_real_episodes():
    import modules.core.narrative_diversity as narrative_diversity

    narrative_diversity.logging = MagicMock()
    db = MagicMock()
    db.get_latest_episode_number.return_value = 11  # real latest = 10
    db.get_manuscript.side_effect = lambda ep: {"content": f"ep-{ep}"}
    db.get_blueprint.return_value = None
    context = SimpleNamespace(db=db)

    engine = NarrativeDiversityEngine(context=context, genre="wuxia", window_size=5)
    engine.analyze_recent_episodes(5)

    called_eps = [call.args[0] for call in db.get_manuscript.call_args_list]
    assert called_eps == [6, 7, 8, 9, 10]


def test_project_service_rollback_handles_null_json_rows():
    ui = SimpleNamespace(log=MagicMock())
    cursor = MagicMock()
    cursor.fetchone.side_effect = [
        {"data": json.dumps({"state_updates": {"actual_truth": {"hp": 10}}})},
        {"data": None},
    ]
    project = SimpleNamespace(
        get_latest_episode_number=MagicMock(return_value=6),
        paths=SimpleNamespace(drafts=SimpleNamespace(glob=MagicMock(return_value=[]))),
        db=SimpleNamespace(cursor=cursor, delete_episode_bibles_after=MagicMock(return_value=0)),
        _load_from_db=MagicMock(),
        master_bible={},
    )
    svc = ProjectService(
        project_fn=lambda: project,
        ui=ui,
        safe_commit_fn=MagicMock(return_value=True),
        genre_fn=lambda: {"type": "wuxia"},
        memory_fn=lambda: None,
    )

    with patch("builtins.input", side_effect=["3", "y", ""]):
        svc.rollback_episode()

    project._load_from_db.assert_called_once()


def test_stage4_orchestrator_uses_perf_logger_for_target_calls():
    text = Path("modules/core/stage4_orchestrator.py").read_text(encoding="utf-8")
    assert 'logging.info(f"[V66.1] mandatory_context' not in text
    assert 'logging.info(f"📋 [V67.1] story_context 조립 완료' not in text
    assert 'logging.warning(f"⚠️ [V67.1] story_context 조립 실패' not in text
    assert 'logging.warning(f"[SilentPass:Stage4] Bible POV 오버라이드 실패' not in text
    assert 'logging.warning(f"[SilentPass:Stage4] Bible POV 기반 스타일 가이드 생성 실패' not in text


def test_retrospective_validator_uses_module_logger_for_warnings():
    text = Path("modules/validation/retrospective_validator.py").read_text(encoding="utf-8")
    assert 'logging.warning(f"⚠️ [Retrospective] 경지 역행 체크 실패' not in text
    assert 'logging.warning(f"⚠️ [Retrospective] 관계 역행 체크 실패' not in text
    assert 'logging.warning(f"⚠️ [Retrospective] 아이템 소실 체크 실패' not in text
    assert 'logging.warning(f"⚠️ [Retrospective] 갈등 재발 체크 실패' not in text
