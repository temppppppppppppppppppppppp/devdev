from types import SimpleNamespace
from unittest.mock import MagicMock

import main_a


def test_collect_treatment_enrichment_candidates_returns_only_needy_blocks():
    app = SimpleNamespace()
    treatment_blocks = [
        {"block_id": "B1", "content": {"summary": "dense"}},
        {"block_id": "B2", "content": {"summary": "thin"}},
        {"block_id": "B3", "content": {"summary": "thin-2"}},
    ]
    analyses = iter(
        [
            {"needs_enrichment": False, "density_score": 0.9, "missing_elements": []},
            {"needs_enrichment": True, "density_score": 0.4, "missing_elements": ["scene"]},
            {"needs_enrichment": True, "density_score": 0.2, "missing_elements": ["stakes"]},
        ]
    )
    enricher = SimpleNamespace(analyze_block_density=lambda _block: next(analyses))

    result = main_a.SovereignApp._collect_treatment_enrichment_candidates(
        app,
        treatment_blocks=treatment_blocks,
        enricher=enricher,
    )

    assert result == [
        {"index": 1, "block_id": "B2", "density_score": 0.4, "missing": ["scene"]},
        {"index": 2, "block_id": "B3", "density_score": 0.2, "missing": ["stakes"]},
    ]


def test_resolve_treatment_enrichment_context_reads_bible(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    bible_dir = tmp_path / "bible"
    bible_dir.mkdir()
    (bible_dir / "demo.json").write_text('{"MasterBible": {"characters": [{"name": "Hero"}]}}', encoding="utf-8")
    monkeypatch.setattr(main_a.HUDKeys, "get_protagonist_name", lambda _root, genre: f"{genre}-hero")

    app = SimpleNamespace(
        selected_genre={"type": "fantasy"},
        ui=SimpleNamespace(log=MagicMock()),
    )

    genre, protagonist_name = main_a.SovereignApp._resolve_treatment_enrichment_context(app)

    assert genre == "fantasy"
    assert protagonist_name == "fantasy-hero"


def test_merge_enriched_treatment_blocks_preserves_original_metadata():
    app = SimpleNamespace()
    treatment_blocks = [
        {"block_id": "B1", "title": "old", "content": {"a": 1}, "genre_ext": {"tone": "bright"}},
        {"block_id": "B2", "title": "old2", "content": {"b": 2}, "status_shadow": {"old": True}},
    ]

    merged = main_a.SovereignApp._merge_enriched_treatment_blocks(
        app,
        treatment_blocks=treatment_blocks,
        enriched_blocks_raw=[
            {"block_id": "B1-new", "title": "new", "content": {"a": 9}, "joint_docs": {"notes": 1}},
            None,
        ],
    )

    assert merged[0]["block_id"] == "B1-new"
    assert merged[0]["title"] == "new"
    assert merged[0]["content"] == {"a": 9}
    assert merged[0]["joint_docs"] == {"notes": 1}
    assert merged[0]["genre_ext"] == {"tone": "bright"}
    assert merged[1] == treatment_blocks[1]


def test_confirm_treatment_enrichment_plan_logs_summary_and_honors_decline():
    app = SimpleNamespace(
        ui=SimpleNamespace(log=MagicMock()),
        _confirm=MagicMock(return_value=False),
    )

    proceed = main_a.SovereignApp._confirm_treatment_enrichment_plan(
        app,
        treatment_blocks=[{"block_id": "B1"}, {"block_id": "B2"}],
        needs_enrichment=[{"block_id": "B2", "density_score": 0.4, "missing": ["scene"]}],
    )

    assert proceed is False
    app._confirm.assert_called_once()
    confirm_prompt = app._confirm.call_args.args[0]
    assert "비정규 semantic rewrite utility" in confirm_prompt
    logs = [call.args[0] for call in app.ui.log.call_args_list if call.args]
    assert any("농축 필요 Block" in msg for msg in logs)
    assert any("canonical Stage0 pair pass 경로가 아닌" in msg for msg in logs)
    assert any("title/content/joint_docs/status_shadow" in msg for msg in logs)
    assert any("농축을 건너뜁니다." in msg for msg in logs)


def test_run_treatment_block_parallel_enrichment_merges_and_logs_stats():
    app = SimpleNamespace(ui=SimpleNamespace(log=MagicMock()))
    treatment_blocks = [
        {"block_id": "B1", "title": "old", "content": {"x": 1}},
        {"block_id": "B2", "title": "old2", "content": {"y": 2}},
    ]
    enricher = SimpleNamespace(
        enrich_all_blocks_parallel=MagicMock(
            return_value={
                "enriched_blocks": [
                    {"block_id": "B1-new", "title": "new", "content": {"x": 9}},
                    None,
                ],
                "statistics": {"enriched_count": 1, "skipped_count": 1, "failed_count": 0},
                "causal_issues_found": 2,
            }
        )
    )

    result = main_a.SovereignApp._run_treatment_block_parallel_enrichment(
        app,
        treatment_blocks=treatment_blocks,
        enricher=enricher,
        protagonist_name="Hero",
        genre="wuxia",
    )

    assert result[0]["block_id"] == "B1-new"
    assert result[1] == treatment_blocks[1]
    logs = [call.args[0] for call in app.ui.log.call_args_list if call.args]
    assert any("비정규 utility" in msg for msg in logs)
    assert any("농축 완료" in msg for msg in logs)
    assert any("인과 수정" in msg for msg in logs)


def test_save_enriched_treatment_blocks_writes_new_file(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    treatments_dir = tmp_path / "treatments"
    treatments_dir.mkdir()
    app = SimpleNamespace(ui=SimpleNamespace(log=MagicMock()))

    filename = main_a.SovereignApp._save_enriched_treatment_blocks(
        app,
        treatment_file="demo.json",
        enriched_blocks=[{"block_id": "B1", "title": "x", "content": {}}],
    )

    assert filename == "demo_enriched.json"
    saved_path = treatments_dir / filename
    assert saved_path.exists()
    assert '"block_id": "B1"' in saved_path.read_text(encoding="utf-8")
    logs = [call.args[0] for call in app.ui.log.call_args_list if call.args]
    assert any("canonical source 유지" in msg for msg in logs)
    assert any("비정규 utility output" in msg for msg in logs)
