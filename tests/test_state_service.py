"""[Phase 4B-3] StateService 단위 테스트

추출 대상: 14개 검증/패턴/아키타입 헬퍼 메서드
"""

from unittest.mock import MagicMock, patch

import pytest

from modules.core.services.state_service import StateService


@pytest.fixture
def ui_mock():
    ui = MagicMock()
    ui.log = MagicMock()
    return ui


@pytest.fixture
def audit_fn():
    return MagicMock()


@pytest.fixture
def genre_fn():
    return lambda: {"type": "wuxia"}


@pytest.fixture
def prompt_builder_mock():
    pb = MagicMock()
    pb.build_validation_context.return_value = {"mode": "MANUSCRIPT"}
    pb.extract_npc_profiles.return_value = {"NPC1": {"role": "히로인"}}
    pb.get_character_traits.return_value = {"trait": "brave"}
    return pb


@pytest.fixture
def feedback_system_mock():
    fs = MagicMock()
    fs.classify_rejection_feedback.return_value = "structural"
    return fs


@pytest.fixture
def svc(ui_mock, audit_fn, genre_fn, prompt_builder_mock, feedback_system_mock):
    return StateService(
        ui=ui_mock,
        audit_event_fn=audit_fn,
        genre_fn=genre_fn,
        prompt_builder=prompt_builder_mock,
        feedback_system=feedback_system_mock,
    )


# ── extract_block_index ──────────────────────────────────────


class TestExtractBlockIndex:
    def test_valid_block_id(self, svc):
        assert svc.extract_block_index("Block 3") == 3

    def test_none_input(self, svc):
        assert svc.extract_block_index(None) is None

    def test_int_input(self, svc):
        assert svc.extract_block_index(42) is None

    def test_no_match(self, svc):
        assert svc.extract_block_index("Section 5") is None

    def test_block_with_extra_text(self, svc):
        assert svc.extract_block_index("Block 12 (expanded)") == 12


# ── validate_arc_mapping ─────────────────────────────────────


class TestValidateArcMapping:
    def test_none_arc_returns_as_is(self, svc):
        assert svc.validate_arc_mapping(None, {}, 1, 1) is None

    def test_non_dict_returns_as_is(self, svc):
        assert svc.validate_arc_mapping("invalid", {}, 1, 1) == "invalid"

    def test_corrects_arc_no(self, svc, ui_mock, audit_fn):
        arc = {"arc_no": 99, "ep_count": 5, "ep_start": 1}
        result = svc.validate_arc_mapping(arc, {}, 1, 1)
        assert result["arc_no"] == 1
        audit_fn.assert_called()

    def test_corrects_ep_start(self, svc, ui_mock):
        arc = {"arc_no": 1, "ep_count": 5, "ep_start": 99}
        result = svc.validate_arc_mapping(arc, {}, 1, 10)
        assert result["ep_start"] == 10
        assert result["ep_end"] == 14  # 10 + 5 - 1

    def test_block_id_mismatch_warning(self, svc, audit_fn):
        arc = {"arc_no": 2, "ep_count": 5, "ep_start": 6}
        block = {"block_id": "Block 5"}
        result = svc.validate_arc_mapping(arc, block, 2, 6)
        assert "mapping_warning" in result


# ── extract_pattern_keywords ─────────────────────────────────


class TestExtractPatternKeywords:
    def test_non_dict_returns_empty(self, svc):
        assert svc.extract_pattern_keywords("not a dict") == []

    def test_basic_extraction(self, svc):
        profile = {"primary": "성장 서사", "secondary": ["복수극", "영웅담"]}
        keywords = svc.extract_pattern_keywords(profile)
        assert "성장" in keywords
        assert "서사" in keywords

    def test_parentheses_removed(self, svc):
        profile = {"primary": "성장(Growth) 서사", "secondary": []}
        keywords = svc.extract_pattern_keywords(profile)
        assert all("Growth" not in k for k in keywords)

    def test_deduplication(self, svc):
        profile = {"primary": "성장 서사", "secondary": ["성장 소설"]}
        keywords = svc.extract_pattern_keywords(profile)
        assert keywords.count("성장") == 1


# ── pattern_presence_check ───────────────────────────────────


class TestPatternPresenceCheck:
    def test_empty_text_returns_false(self, svc):
        assert svc.pattern_presence_check("", {"primary": "test"}) is False

    def test_no_keywords_returns_true(self, svc):
        assert svc.pattern_presence_check("any text", {}) is True

    def test_keyword_found(self, svc):
        profile = {"primary": "성장 서사", "secondary": []}
        assert svc.pattern_presence_check("주인공의 성장 이야기", profile) is True

    def test_keyword_not_found(self, svc):
        profile = {"primary": "성장 서사", "secondary": []}
        assert svc.pattern_presence_check("완전히 다른 내용", profile) is False


# ── build_validation_context (thin → PromptBuilder) ──────────


class TestBuildValidationContext:
    def test_delegates_to_prompt_builder(self, svc, prompt_builder_mock):
        result = svc.build_validation_context(1, {"bp": True}, "MANUSCRIPT", "text")
        prompt_builder_mock.build_validation_context.assert_called_once_with(1, {"bp": True}, "MANUSCRIPT", "text")
        assert result == {"mode": "MANUSCRIPT"}


# ── extract_npc_profiles (thin → PromptBuilder) ──────────────


class TestExtractNpcProfiles:
    def test_delegates_to_prompt_builder(self, svc, prompt_builder_mock):
        result = svc.extract_npc_profiles({"arc": 1})
        prompt_builder_mock.extract_npc_profiles.assert_called_once_with({"arc": 1})
        assert "NPC1" in result


# ── get_character_traits (thin → PromptBuilder) ──────────────


class TestGetCharacterTraits:
    def test_delegates_to_prompt_builder(self, svc, prompt_builder_mock):
        result = svc.get_character_traits()
        prompt_builder_mock.get_character_traits.assert_called_once()
        assert result == {"trait": "brave"}


# ── load_character_archetypes ────────────────────────────────


class TestLoadCharacterArchetypes:
    def test_no_file_returns_empty(self, svc):
        with patch("modules.core.services.state_service.Path") as mock_path:
            mock_file = MagicMock()
            mock_file.exists.return_value = False
            mock_path.return_value.__truediv__ = MagicMock(return_value=mock_file)
            result = svc.load_character_archetypes("wuxia")
        assert result == {}

    def test_file_exists_loads_json(self, svc, tmp_path):
        arch_file = tmp_path / "wuxia.json"
        arch_file.write_text('{"supporter": {}}', encoding="utf-8")
        with patch("modules.core.services.state_service.Path") as mock_path:
            mock_path.return_value.__truediv__ = MagicMock(return_value=arch_file)
            result = svc.load_character_archetypes("wuxia")
        assert result == {"supporter": {}}


# ── get_archetype_reference_for_npcs ─────────────────────────


class TestGetArchetypeReferenceForNpcs:
    def test_empty_profiles_returns_empty(self, svc):
        assert svc.get_archetype_reference_for_npcs({}) == ""

    def test_no_archetypes_returns_empty(self, svc):
        with patch.object(svc, "load_character_archetypes", return_value={}):
            result = svc.get_archetype_reference_for_npcs({"NPC1": {"role": "히로인"}})
        assert result == ""

    def test_heroine_role_matches(self, svc):
        archetypes = {
            "supporter": {
                "heroine": {
                    "classic": {
                        "core_traits": ["강인", "자비"],
                        "speech": "~이에요 말투",
                        "forbidden": ["욕설"],
                    }
                }
            }
        }
        with patch.object(svc, "load_character_archetypes", return_value=archetypes):
            result = svc.get_archetype_reference_for_npcs({"김소연": {"role": "히로인"}})
        assert "김소연" in result
        assert "강인" in result


# ── classify_rejection_feedback (thin → FeedbackSystem) ──────


class TestClassifyRejectionFeedback:
    def test_delegates_to_feedback_system(self, svc, feedback_system_mock):
        result = svc.classify_rejection_feedback("reason", "feedback", {"bp": True})
        feedback_system_mock.classify_rejection_feedback.assert_called_once_with("reason", "feedback", {"bp": True})
        assert result == "structural"


# ── validate_arc_data_fields ─────────────────────────────────


class TestValidateArcDataFields:
    def test_non_dict_returns_none(self, svc, ui_mock):
        assert svc.validate_arc_data_fields("invalid", 0) is None

    def test_missing_fields_repaired(self, svc, ui_mock, audit_fn):
        arc = {"ep_start": 1, "ep_count": 5}
        result = svc.validate_arc_data_fields(arc, 0)
        assert result is not None
        assert "tactical_doc" in result
        assert "beat_sequence" in result
        assert isinstance(result["joint_docs"], dict)

    def test_type_mismatch_repaired(self, svc, ui_mock):
        arc = {
            "ep_start": 1,
            "ep_count": 5,
            "tactical_doc": 123,  # should be str
            "beat_sequence": "not a list",  # should be list
            "joint_docs": "wrong",  # should be dict
            "status_shadow": [],  # should be dict
            "arc_drive": "wrong",  # should be dict
            "hybrid_composition": "wrong",  # should be dict
        }
        result = svc.validate_arc_data_fields(arc, 0)
        assert isinstance(result["tactical_doc"], str)
        assert isinstance(result["beat_sequence"], list)
        assert isinstance(result["joint_docs"], dict)

    def test_valid_data_passes_through(self, svc, ui_mock):
        arc = {
            "ep_start": 1,
            "ep_count": 5,
            "ep_end": 5,
            "tactical_doc": "doc",
            "beat_sequence": [1, 2],
            "joint_docs": {},
            "status_shadow": {},
            "arc_drive": {},
            "hybrid_composition": {"primary": "standard", "secondary": [], "mixing_logic": "기본"},
        }
        result = svc.validate_arc_data_fields(arc, 0)
        assert result == arc


# ── load_genre_references ────────────────────────────────────


class TestLoadGenreReferences:
    def test_missing_files_returns_empty(self, svc, ui_mock):
        with patch("modules.core.services.state_service.Path") as mock_path:
            mock_file = MagicMock()
            mock_file.exists.return_value = False
            mock_path.return_value.__truediv__ = MagicMock(return_value=mock_file)
            cliche, location = svc.load_genre_references()
        assert cliche == []
        assert location == []


# ── validate_arc_integrity ───────────────────────────────────


class TestValidateArcIntegrity:
    def test_missing_keys_fails(self, svc, ui_mock, audit_fn):
        assert svc.validate_arc_integrity({"arc_no": 1}) is False

    def test_invalid_beat_sequence_fails(self, svc, ui_mock):
        arc = {
            "arc_no": 1, "ep_start": 1, "ep_end": 5, "ep_count": 5,
            "tactical_doc": "x" * 600, "beat_sequence": "not_a_list",
        }
        assert svc.validate_arc_integrity(arc) is False

    def test_short_tactical_doc_fails(self, svc, ui_mock):
        arc = {
            "arc_no": 1, "ep_start": 1, "ep_end": 5, "ep_count": 5,
            "tactical_doc": "too short", "beat_sequence": [1],
        }
        assert svc.validate_arc_integrity(arc) is False

    def test_valid_arc_passes(self, svc):
        arc = {
            "arc_no": 1, "ep_start": 1, "ep_end": 5, "ep_count": 5,
            "tactical_doc": "x" * 600, "beat_sequence": [1, 2, 3],
        }
        assert svc.validate_arc_integrity(arc) is True


# ── validate_blueprint_integrity ─────────────────────────────


class TestValidateBlueprintIntegrity:
    def test_non_dict_fails(self, svc, ui_mock, audit_fn):
        assert svc.validate_blueprint_integrity("invalid") is False

    def test_missing_scenario_fails(self, svc, ui_mock):
        assert svc.validate_blueprint_integrity({"scene_breakdown": {}}) is False

    def test_missing_breakdown_fails(self, svc, ui_mock):
        assert svc.validate_blueprint_integrity({"integrated_scenario": "text"}) is False

    def test_valid_blueprint_passes(self, svc):
        bp = {"integrated_scenario": "text", "scene_breakdown": {"s1": "scene"}}
        assert svc.validate_blueprint_integrity(bp) is True


# ── constructor ──────────────────────────────────────────────


class TestConstructor:
    def test_all_deps_stored(self, ui_mock, audit_fn, genre_fn, prompt_builder_mock, feedback_system_mock):
        svc = StateService(
            ui=ui_mock,
            audit_event_fn=audit_fn,
            genre_fn=genre_fn,
            prompt_builder=prompt_builder_mock,
            feedback_system=feedback_system_mock,
        )
        assert svc._ui is ui_mock
        assert svc._audit_event is audit_fn
        assert svc._prompt_builder is prompt_builder_mock
        assert svc._feedback_system is feedback_system_mock
