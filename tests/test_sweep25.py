from types import SimpleNamespace
from unittest.mock import MagicMock

from modules.core.db_manager import DBManager
from modules.core.genre_guards.fantasy_guard import FantasyGuard
from modules.core.genre_guards.hunter_guard import HunterGuard
from modules.core.genre_guards.style_guard import StyleGuard
from modules.core.genre_guards.work_guard import WorkGuard
from modules.core.genre_guards.wuxia_guard import WuxiaGuard
from modules.core.pass_rate_monitor import PassRateMonitor
from modules.core.project_manager import ProjectContext
from modules.core.vec_memory import VecMemory
from modules.domain.agents.writer import Writer


def test_work_guard_wrapper_accepts_three_arg_delegation(tmp_path):
    base = WuxiaGuard()
    guard = WorkGuard(base_guard=base, yaml_path=tmp_path / "missing_work_guard.yaml")

    out1 = guard.check_unresolved_conflict("원고", {}, 1)
    out2 = guard.check_villain_response(
        "원고",
        {"villain_name": "적", "villain_role": "주적", "is_aware": True},
        [],
    )

    assert isinstance(out1, dict)
    assert isinstance(out2, dict)


def test_style_guard_wrapper_accepts_three_arg_delegation():
    base = WuxiaGuard()
    style_guide = SimpleNamespace(
        anti_ai_patterns=[],
        forbidden_expressions=[],
        sentence_length="medium",
    )
    guard = StyleGuard(base_guard=base, style_guide=style_guide)

    out1 = guard.check_unresolved_conflict("원고", {}, 1)
    out2 = guard.check_villain_response(
        "원고",
        {"villain_name": "적", "villain_role": "주적", "is_aware": True},
        [],
    )

    assert isinstance(out1, dict)
    assert isinstance(out2, dict)


def test_db_manager_load_all_anchors_handles_null_data(tmp_path):
    db = DBManager(tmp_path / "sweep25_anchors.db")
    try:
        db.cursor.execute("INSERT OR REPLACE INTO anchors (key, data) VALUES (?, ?)", ("bad_anchor", None))
        db.conn.commit()

        data = db.load_all_anchors()
        assert data["bad_anchor"] == {}
    finally:
        db.close()


def test_db_manager_get_latest_state_handles_null_data(tmp_path):
    db = DBManager(tmp_path / "sweep25_state.db")
    try:
        db.cursor.execute(
            "INSERT OR REPLACE INTO state_logs (ep_num, data, summary) VALUES (?, ?, ?)",
            (1, None, ""),
        )
        db.conn.commit()

        assert db.get_latest_state() == {}
    finally:
        db.close()


def test_fantasy_guard_handles_none_mana_without_type_error():
    guard = FantasyGuard()
    actions = guard.get_impossible_actions({"mana": None})
    assert isinstance(actions, list)


def test_hunter_guard_escapes_regex_meta_skill_name():
    guard = HunterGuard()
    result = guard.check_state_action_consistency(
        "주인공은 Skill( 을 억지로 발동했다.",
        {"skill_cooldowns": {"Skill(": 3}},
    )
    assert isinstance(result, dict)
    assert "violations" in result


def test_writer_npc_frequency_uses_master_bible_root():
    ctx = SimpleNamespace(
        master_bible={"MasterBible": {"AssetLibrary": {"KeyNPCs": [{"name": "NPC_A"}]}}},
        db=MagicMock(),
    )
    ctx.db.get_manuscript.side_effect = [
        {"content": "NPC_A 등장"},
        {"content": "기타 내용"},
    ]

    writer = Writer(context=ctx, client=MagicMock(), model_tier="gemini-2.5-flash")
    freq = writer._get_npc_frequency(ep_num=3, window=10)

    assert freq.get("NPC_A", 0) >= 1


def test_auto_backtrack_defaults_origin_to_latest_minus_one():
    pm = ProjectContext.__new__(ProjectContext)
    pm.db = MagicMock()
    pm.db.get_rollback_impact.return_value = {}
    pm.get_latest_episode_number = MagicMock(return_value=11)
    pm.reset_project = MagicMock()

    result = pm.auto_backtrack_v35("번호 없는 에러 리포트", memory=None)

    assert result == 10
    pm.reset_project.assert_called_once_with(10)


def test_vec_memory_embedding_none_retries_three_times(monkeypatch):
    mem = VecMemory(":memory:", api_key="", ui_log=MagicMock())
    try:
        mocked_models = MagicMock()
        mocked_models.embed_content.return_value = SimpleNamespace(embedding=None)
        mem._genai_client = SimpleNamespace(models=mocked_models)
        monkeypatch.setattr("modules.core.vec_memory.time.sleep", lambda _x: None)

        assert mem._embed_text("text to embed") is None
        assert mocked_models.embed_content.call_count == 3
    finally:
        mem.close()


def test_pass_rate_monitor_ignores_unknown_record_fields(tmp_path):
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "pass_rate_monitor.json"
    log_path.write_text(
        """
{
  "records": [
    {
      "timestamp": "2026-02-17T12:00:00",
      "stage": 4,
      "episode": 7,
      "arc": 2,
      "attempt_num": 1,
      "success": true,
      "unknown_field": "ignore_me"
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    monitor = PassRateMonitor(project_path=str(tmp_path))
    assert len(monitor.records) == 1
    assert monitor.records[0].stage == 4
