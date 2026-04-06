import json

from modules.core.project_support import (
    build_style_guide_summary,
    default_external_pov_insert_policy,
    inspect_project_support_assets,
    load_work_guard_summary,
    normalize_external_pov_insert_policy,
    resolve_project_bible_pov,
    resolve_project_external_pov_insert_policy,
    resolve_project_pov_contract,
    resolve_style_dialogue_ratio_target,
)


class DummyProject:
    def __init__(self, *, style_data=None, bible=None):
        self._style_data = style_data or {}
        self.master_bible = bible or {}

    def load_v20_anchor(self, key):
        if key == "style_guide":
            return self._style_data
        return None


def test_default_external_pov_insert_policy_prefers_investment_limited_mode():
    assert default_external_pov_insert_policy("1인칭", genre="investment") == "제한적 허용"
    assert default_external_pov_insert_policy("1인칭", genre="wuxia") == "금지"


def test_build_style_guide_summary_uses_effective_pov_contract():
    project = DummyProject(
        style_data={
            "tone": "sharp",
            "pov": "3인칭",
            "extracted_pov": "1인칭",
            "selected_primary_pov": "3인칭",
            "effective_primary_pov": "3인칭",
            "external_pov_insert_policy": "제한적 허용",
            "dialogue_ratio": 0.4,
            "sentence_length": "short",
            "description_style": "dense",
            "anti_ai_patterns": ["generic phrasing"],
        },
        bible={"MasterBible": {"protagonist_config": {"pov": "3인칭", "external_pov_insert_policy": "제한적 허용"}}},
    )

    text = build_style_guide_summary(
        project,
        heading="[문체 가이드 요약]",
        max_chars=500,
        include_dialogue_ratio=True,
        secondary_style_key="description_style",
        secondary_style_label="묘사",
    )

    assert "[문체 가이드 요약]" in text
    assert "시점=3인칭" in text
    assert "타자 시점 삽입=제한적 허용" in text
    assert "대화 비율=40%" in text
    assert "generic phrasing" in text


def test_resolve_project_pov_contract_handles_style_provenance():
    project = DummyProject(
        style_data={
            "pov": "1인칭",
            "extracted_pov": "1인칭",
            "selected_primary_pov": "혼합",
            "effective_primary_pov": "혼합",
            "external_pov_insert_policy": "적극 허용",
        },
        bible={"MasterBible": {"protagonist_config": {"pov": "혼합", "external_pov_insert_policy": "적극 허용"}}},
    )

    contract = resolve_project_pov_contract(project)

    assert contract["primary_pov"] == "혼합"
    assert contract["style_guide_extracted_pov"] == "1인칭"
    assert contract["effective_pov"] == "혼합"
    assert contract["external_pov_insert_policy"] == "적극 허용"


def test_resolve_project_bible_pov_returns_empty_for_missing_payload():
    assert resolve_project_bible_pov(DummyProject()) == ""
    assert resolve_project_external_pov_insert_policy(DummyProject()) == ""


def test_resolve_style_dialogue_ratio_target_accepts_percent_strings():
    assert resolve_style_dialogue_ratio_target({"dialogue_ratio": "40%"}) == 0.4
    assert resolve_style_dialogue_ratio_target(project=DummyProject(style_data={"dialogue_ratio": 0.35})) == 0.35
    assert resolve_style_dialogue_ratio_target({"dialogue_ratio": "0%"}) == 0.0
    assert resolve_style_dialogue_ratio_target({"dialogue_ratio": 0.0}) == 0.0


def test_inspect_project_support_assets_reports_ready_flags(tmp_path):
    project_dir = tmp_path / "demo"
    (project_dir / "config").mkdir(parents=True)
    (project_dir / "stage0_output").mkdir(parents=True)
    (project_dir / "config" / "author_directives.txt").write_text("intent", encoding="utf-8")
    (project_dir / "config" / "work_guard.yaml").write_text(
        "work_identity:\n  work_id: demo_work\n  work_type: enterprise\n  tracking_slots:\n    - hero\n",
        encoding="utf-8",
    )
    (project_dir / "stage0_output" / "style_guide.json").write_text(
        json.dumps(
            {
                "tone": "sharp",
                "pov": "1인칭",
                "extracted_pov": "1인칭",
                "effective_primary_pov": "3인칭",
                "external_pov_insert_policy": "제한적 허용",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    payload = inspect_project_support_assets(project_dir)

    assert payload["author_directives"]["ready"] is True
    assert payload["work_guard"]["work_guard_exists"] is True
    assert payload["work_guard"]["work_id"] == "demo_work"
    assert payload["work_guard"]["tracking_slots"] == 1
    assert payload["style_guide"]["ready"] is True
    assert payload["style_guide"]["tone"] == "sharp"
    assert payload["style_guide"]["effective_pov"] == "3인칭"
    assert payload["style_guide"]["external_pov_insert_policy"] == "제한적 허용"


def test_load_work_guard_summary_handles_missing_file(tmp_path):
    payload = load_work_guard_summary(tmp_path)

    assert payload["work_guard_exists"] is False
    assert payload["work_id"] == ""
    assert payload["tracking_slots"] == 0


def test_load_work_guard_summary_marks_invalid_yaml(tmp_path):
    project_dir = tmp_path / "demo"
    (project_dir / "config").mkdir(parents=True)
    (project_dir / "config" / "work_guard.yaml").write_text("work_identity: [broken", encoding="utf-8")

    payload = load_work_guard_summary(project_dir)

    assert payload["work_guard_exists"] is True
    assert payload["work_guard_valid"] is False
    assert "YAML parse failed" in payload["work_guard_error"]
    assert payload["tracking_slots"] == 0


def test_inspect_project_support_assets_marks_invalid_work_guard_not_ready(tmp_path):
    project_dir = tmp_path / "demo"
    (project_dir / "config").mkdir(parents=True)
    (project_dir / "stage0_output").mkdir(parents=True)
    (project_dir / "config" / "work_guard.yaml").write_text("work_identity: [broken", encoding="utf-8")

    payload = inspect_project_support_assets(project_dir)

    assert payload["work_guard"]["exists"] is True
    assert payload["work_guard"]["ready"] is False
    assert payload["work_guard"]["work_guard_valid"] is False


def test_normalize_external_pov_insert_policy_defaults_by_primary_pov():
    assert normalize_external_pov_insert_policy("", primary_pov="3인칭") == "제한적 허용"
    assert normalize_external_pov_insert_policy("허용", primary_pov="1인칭") == "제한적 허용"
