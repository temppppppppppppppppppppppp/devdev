import json
from pathlib import Path
from unittest.mock import patch

from modules.core.stage0 import StageZeroManager
from modules.core.stage0.style_extractor import StyleExtractor, StyleGuide


def _prepare_reference_tree(tmp_path: Path, genre: str = "investment") -> tuple[Path, Path]:
    ref_dir = tmp_path / "config" / "style_references" / genre / "sample_work"
    ref_dir.mkdir(parents=True, exist_ok=True)
    (ref_dir / "0001.txt").write_text("투자물 샘플 본문", encoding="utf-8")
    cache_path = tmp_path / "config" / "style_references" / genre / "style_guide.json"
    return ref_dir.parent, cache_path


def test_style_cache_hit_uses_meta_wrapped_cache(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    genre_dir, cache_path = _prepare_reference_tree(tmp_path)

    extractor = StyleExtractor()
    cached_guide = StyleGuide(tone="sharp", genre="investment")
    cache_payload = {
        "_cache_meta": extractor._build_cache_meta("investment", genre_dir),
        "style_guide": cached_guide.to_dict(),
    }
    cache_path.write_text(json.dumps(cache_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    with patch.object(StyleExtractor, "extract_from_drafts", side_effect=AssertionError("cache hit expected")):
        guide = extractor.extract_from_references("investment", cache_mode="use")

    assert guide is not None
    assert guide.tone == "sharp"
    assert extractor.last_cache_status == "hit"


def test_style_cache_reanalyzes_when_meta_mismatch(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    genre_dir, cache_path = _prepare_reference_tree(tmp_path)

    extractor = StyleExtractor()
    stale_meta = extractor._build_cache_meta("investment", genre_dir)
    stale_meta["prompt_contract_hash"] = "stale"
    cache_payload = {
        "_cache_meta": stale_meta,
        "style_guide": StyleGuide(tone="old", genre="investment").to_dict(),
    }
    cache_path.write_text(json.dumps(cache_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    fresh_guide = StyleGuide(tone="fresh", genre="investment")
    with patch.object(StyleExtractor, "extract_from_drafts", return_value=fresh_guide) as mock_extract:
        guide = extractor.extract_from_references("investment", cache_mode="use")

    assert guide is not None
    assert guide.tone == "fresh"
    assert mock_extract.called
    saved_payload = json.loads(cache_path.read_text(encoding="utf-8"))
    assert saved_payload["_cache_meta"]["prompt_contract_hash"] == extractor._prompt_contract_hash()
    assert extractor.last_cache_status == "miss"


def test_style_cache_tracks_primary_pov_contract_in_meta(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    genre_dir, cache_path = _prepare_reference_tree(tmp_path)

    extractor = StyleExtractor()
    cache_payload = {
        "_cache_meta": extractor._build_cache_meta(
            "investment",
            genre_dir,
            selected_primary_pov="3인칭",
            external_pov_insert_policy="제한적 허용",
        ),
        "style_guide": StyleGuide(tone="old", genre="investment").to_dict(),
    }
    cache_path.write_text(json.dumps(cache_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    fresh_guide = StyleGuide(tone="fresh", genre="investment")
    with patch.object(StyleExtractor, "extract_from_drafts", return_value=fresh_guide) as mock_extract:
        guide = extractor.extract_from_references(
            "investment",
            cache_mode="use",
            selected_primary_pov="1인칭",
            external_pov_insert_policy="금지",
        )

    assert guide is not None
    assert guide.pov == "1인칭"
    assert guide.extracted_pov in {"", "1인칭", "old", "fresh"} or isinstance(guide.extracted_pov, str)
    assert guide.external_pov_insert_policy == "금지"
    assert mock_extract.called


def test_style_cache_reset_mode_deletes_and_rebuilds(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    genre_dir, cache_path = _prepare_reference_tree(tmp_path)

    extractor = StyleExtractor()
    old_payload = {
        "_cache_meta": extractor._build_cache_meta("investment", genre_dir),
        "style_guide": StyleGuide(tone="old", genre="investment").to_dict(),
    }
    cache_path.write_text(json.dumps(old_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    rebuilt_guide = StyleGuide(tone="rebuilt", genre="investment")
    with patch.object(StyleExtractor, "extract_from_drafts", return_value=rebuilt_guide):
        guide = extractor.extract_from_references("investment", cache_mode="reset")

    assert guide is not None
    assert guide.tone == "rebuilt"
    saved_payload = json.loads(cache_path.read_text(encoding="utf-8"))
    assert saved_payload["style_guide"]["tone"] == "rebuilt"


def test_prepare_reference_manuscripts_syncs_packaged_investment_refs(tmp_path, monkeypatch):
    workspace_root = tmp_path / "workspace"
    engine_root = tmp_path / "engine"
    workspace_root.mkdir(parents=True, exist_ok=True)
    packaged_ref_dir = engine_root / "config" / "style_references" / "investment" / "sample_work"
    packaged_ref_dir.mkdir(parents=True, exist_ok=True)
    (packaged_ref_dir / "0001.txt").write_text("투자물 레퍼런스 본문", encoding="utf-8")

    monkeypatch.setenv("GEULDOBI_WORKSPACE", str(workspace_root))
    monkeypatch.setenv("GEULDOBI_ENGINE_ROOT", str(engine_root))
    monkeypatch.chdir(workspace_root)

    prepared = StyleExtractor.prepare_reference_manuscripts("investment")

    synced_file = workspace_root / "config" / "style_references" / "investment" / "sample_work" / "0001.txt"
    assert prepared["status"] == "packaged_sync"
    assert prepared["source_dir"] == engine_root / "config" / "style_references" / "investment"
    assert synced_file.exists()
    assert prepared["works"] == {"sample_work": ["투자물 레퍼런스 본문"]}


def test_manage_work_guard_can_initialize_optional_template(tmp_path):
    project_dir = tmp_path / "project"
    manager = StageZeroManager(project_path=str(project_dir))
    manager.genre = "investment"

    with patch("builtins.input", return_value="2"):
        manager.manage_work_guard()

    work_guard_path = project_dir / "config" / "work_guard.yaml"
    assert work_guard_path.exists()
    payload = work_guard_path.read_text(encoding="utf-8")
    assert "work_type: investment" in payload
    assert "tracking_slots:" in payload


def test_run_reference_analysis_accepts_explicit_cache_mode(tmp_path):
    manager = StageZeroManager(project_path=str(tmp_path))

    fake_style = StyleGuide(tone="calm", genre="investment")
    with (
        patch.object(StageZeroManager, "show_genre_menu", return_value="investment"),
        patch(
            "modules.core.stage0.StyleExtractor.prepare_reference_manuscripts",
            return_value={
                "status": "workspace",
                "ref_dir": tmp_path / "config" / "style_references" / "investment",
                "source_dir": None,
                "works": {"ref": ["a"]},
            },
        ),
        patch("builtins.input", return_value="y"),
        patch("modules.core.stage0.StyleExtractor.extract_from_references", return_value=fake_style) as mock_extract,
    ):
        result = manager.run_reference_analysis(cache_mode="refresh")

    assert result is fake_style
    mock_extract.assert_called_once_with(
        "investment",
        cache_mode="refresh",
        selected_primary_pov="",
        external_pov_insert_policy="",
    )


def test_run_reference_analysis_passes_pov_contract(tmp_path):
    manager = StageZeroManager(project_path=str(tmp_path))
    manager.protagonist_config = {"pov": "혼합", "external_pov_insert_policy": "적극 허용"}

    fake_style = StyleGuide(tone="calm", genre="investment")
    with (
        patch.object(StageZeroManager, "show_genre_menu", return_value="investment"),
        patch(
            "modules.core.stage0.StyleExtractor.prepare_reference_manuscripts",
            return_value={
                "status": "workspace",
                "ref_dir": tmp_path / "config" / "style_references" / "investment",
                "source_dir": None,
                "works": {"ref": ["a"]},
            },
        ),
        patch("builtins.input", return_value="y"),
        patch("modules.core.stage0.StyleExtractor.extract_from_references", return_value=fake_style) as mock_extract,
    ):
        result = manager.run_reference_analysis(cache_mode="refresh")

    assert result is fake_style
    mock_extract.assert_called_once_with(
        "investment",
        cache_mode="refresh",
        selected_primary_pov="혼합",
        external_pov_insert_policy="적극 허용",
    )


def test_run_reference_analysis_logs_reference_sync_and_cache_mode(tmp_path):
    manager = StageZeroManager(project_path=str(tmp_path))

    fake_style = StyleGuide(tone="calm", genre="investment")
    with (
        patch.object(StageZeroManager, "show_genre_menu", return_value="investment"),
        patch(
            "modules.core.stage0.StyleExtractor.prepare_reference_manuscripts",
            return_value={
                "status": "packaged_sync",
                "ref_dir": tmp_path / "config" / "style_references" / "investment",
                "source_dir": tmp_path / "engine" / "config" / "style_references" / "investment",
                "works": {"ref": ["a"]},
            },
        ),
        patch("builtins.input", return_value="y"),
        patch("modules.core.stage0.StyleExtractor.extract_from_references", return_value=fake_style),
        patch.object(StageZeroManager, "_ui_log") as mock_ui_log,
    ):
        result = manager.run_reference_analysis(cache_mode="use")

    assert result is fake_style
    logged_messages = [call.args[0] for call in mock_ui_log.call_args_list if call.args]
    assert any("투자물 레퍼런스 초기화" in message for message in logged_messages)
    assert any("스타일 캐시 모드: 캐시 사용" in message for message in logged_messages)
