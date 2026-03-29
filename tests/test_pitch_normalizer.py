"""Tests for modules.core.pitch_normalizer — Mode A (Mechanical Normalize)."""
from __future__ import annotations

import pytest

from modules.core.pitch_normalizer import (
    PitchCollisionError,
    _assert_within,
    _eval_completeness,
    _eval_signals,
    _eval_wuxia_overlay,
    _is_wuxia_register_name,
    _yaml_scalar,
    mirror_pitch_to_preprocess,
    normalize_pitch,
    normalize_pitch_to_canon,
    promote_pitch,
    read_pending_pitch,
    read_pitch,
    validate_verdicts,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_RAW = (
    "재벌 3세가 체면만 남고 개인 자금은 끊긴 상태에서 시작한다. "
    "장례식장 급식 공백과 의전 혼선을 해결해 첫 수수료 확보. "
    "형이 심어둔 방해 공작을 역이용. "
    "윤재이는 가문의 밑단 돈줄을 장악해 위기를 역전시킨다."
)

SAMPLE_WUXIA_RAW = (
    "천독문(天毒門)의 막내 제자 백소연(白小燕)은 입문 경지에 불과하지만, "
    "사형 진무혁(陳武赫)이 남긴 비급을 손에 넣는다. "
    "문파 내부의 장로 세력과 가주의 대립 속에서 "
    "검법과 독공을 결합한 절학을 완성하며 강호에 이름을 알린다. "
    "하지만 무림맹의 추격과 세가의 음모가 위기를 몰고 온다."
)


@pytest.fixture()
def pitch_dirs(tmp_path, monkeypatch):
    """Redirect pitch storage to tmp_path for isolation."""
    pending = tmp_path / "pending"
    canon = tmp_path / "canon"
    preprocess = tmp_path / "preprocess"
    pending.mkdir()
    canon.mkdir()
    preprocess.mkdir()

    import modules.core.pitch_normalizer as mod

    monkeypatch.setattr(mod, "_PENDING_BASE", pending)
    monkeypatch.setattr(mod, "_CANON_BASE", canon)
    monkeypatch.setattr(mod, "_PREPROCESS_BASE", preprocess)

    return {"pending": pending, "canon": canon, "preprocess": preprocess}


# ---------------------------------------------------------------------------
# normalize_pitch (pending path)
# ---------------------------------------------------------------------------


class TestNormalizePitch:
    def test_creates_pending_pitch(self, pitch_dirs):
        result = normalize_pitch(SAMPLE_RAW, slug="재벌밑단", title="재벌물 테스트")
        path = result["path"]
        assert path.exists()
        assert "pending" in str(path)
        assert path.name == "pitch.md"
        content = path.read_text(encoding="utf-8")
        assert "work_id: pending" in content
        assert "slug: 재벌밑단" in content
        assert SAMPLE_RAW in content

    def test_collision_raises(self, pitch_dirs):
        normalize_pitch(SAMPLE_RAW, slug="test_slug")
        with pytest.raises(PitchCollisionError):
            normalize_pitch(SAMPLE_RAW, slug="test_slug")

    def test_collision_force_overwrites(self, pitch_dirs):
        normalize_pitch(SAMPLE_RAW, slug="test_slug", title="v1")
        result = normalize_pitch("updated", slug="test_slug", title="v2", force=True)
        content = result["path"].read_text(encoding="utf-8")
        assert "updated" in content

    def test_completeness_all_false_mode_a(self, pitch_dirs):
        """Mode A puts everything in Raw Input; other sections are empty."""
        result = normalize_pitch(SAMPLE_RAW, slug="empty_sections")
        for key, val in result["completeness"].items():
            assert val is False, f"{key} should be False in Mode A"

    def test_signals_extracted_from_raw(self, pitch_dirs):
        result = normalize_pitch(SAMPLE_RAW, slug="sig_test")
        # defeat beats: 위기
        assert result["signals"]["defeat_beats_present"] is True
        # names: 윤재이 at minimum
        assert result["signals"]["npc_pool_present"] is True


# ---------------------------------------------------------------------------
# normalize_pitch_to_canon (direct canon)
# ---------------------------------------------------------------------------


class TestNormalizePitchToCanon:
    def test_creates_canon_pitch(self, pitch_dirs):
        result = normalize_pitch_to_canon(
            SAMPLE_RAW, work_id="chaebol_test", title="재벌 테스트"
        )
        path = result["path"]
        assert path.exists()
        assert "canon" in str(path)
        content = path.read_text(encoding="utf-8")
        assert "work_id: chaebol_test" in content
        assert "slug" not in content.split("---")[1]

    def test_collision_raises(self, pitch_dirs):
        normalize_pitch_to_canon(SAMPLE_RAW, work_id="coll_test")
        with pytest.raises(PitchCollisionError):
            normalize_pitch_to_canon(SAMPLE_RAW, work_id="coll_test")

    def test_collision_force(self, pitch_dirs):
        normalize_pitch_to_canon(SAMPLE_RAW, work_id="coll_test")
        normalize_pitch_to_canon("new", work_id="coll_test", force=True)
        data = read_pitch("coll_test")
        assert data is not None
        assert "new" in data["sections"].get("Raw Input", "")


# ---------------------------------------------------------------------------
# promote_pitch
# ---------------------------------------------------------------------------


class TestPromotePitch:
    def test_promote_moves_to_canon(self, pitch_dirs):
        normalize_pitch(SAMPLE_RAW, slug="promo_slug", title="Promo")
        canon_path = promote_pitch("promo_slug", "promo_work_id")
        assert canon_path.exists()
        # Pending should be gone
        assert not (pitch_dirs["pending"] / "promo_slug").exists()
        # work_id updated in content
        content = canon_path.read_text(encoding="utf-8")
        assert "work_id: promo_work_id" in content
        assert "slug" not in content.split("---")[1]

    def test_promote_collision_raises(self, pitch_dirs):
        normalize_pitch(SAMPLE_RAW, slug="slug_a")
        normalize_pitch_to_canon(SAMPLE_RAW, work_id="existing_wid")
        with pytest.raises(PitchCollisionError):
            promote_pitch("slug_a", "existing_wid")

    def test_promote_collision_force(self, pitch_dirs):
        normalize_pitch(SAMPLE_RAW, slug="slug_b", title="new")
        normalize_pitch_to_canon("old", work_id="target_wid")
        promote_pitch("slug_b", "target_wid", force=True)
        data = read_pitch("target_wid")
        assert SAMPLE_RAW in data["sections"].get("Raw Input", "")

    def test_promote_missing_pending(self, pitch_dirs):
        with pytest.raises(FileNotFoundError):
            promote_pitch("nonexistent", "any_wid")


# ---------------------------------------------------------------------------
# read_pitch / read_pending_pitch
# ---------------------------------------------------------------------------


class TestReadPitch:
    def test_read_canon(self, pitch_dirs):
        normalize_pitch_to_canon(SAMPLE_RAW, work_id="read_test", title="Read")
        data = read_pitch("read_test")
        assert data is not None
        assert data["meta"]["work_id"] == "read_test"
        assert data["meta"]["title"] == "Read"
        assert "Raw Input" in data["sections"]
        assert SAMPLE_RAW in data["sections"]["Raw Input"]

    def test_read_pending(self, pitch_dirs):
        normalize_pitch(SAMPLE_RAW, slug="pend_read")
        data = read_pending_pitch("pend_read")
        assert data is not None
        assert data["meta"]["work_id"] == "pending"

    def test_read_nonexistent(self, pitch_dirs):
        assert read_pitch("nope") is None
        assert read_pending_pitch("nope") is None


# ---------------------------------------------------------------------------
# mirror_pitch_to_preprocess
# ---------------------------------------------------------------------------


class TestMirror:
    def test_mirror_copies(self, pitch_dirs):
        normalize_pitch_to_canon(SAMPLE_RAW, work_id="mirror_wid")
        # Create preprocess base (simulating existing work_id instantiation)
        pp_dir = pitch_dirs["preprocess"] / "mirror_wid"
        pp_dir.mkdir()

        dst = mirror_pitch_to_preprocess("mirror_wid")
        assert dst is not None
        assert dst.exists()
        assert dst.name == "pitch.md"
        assert "00_brief" in str(dst)
        # Content matches canon
        canon_content = (pitch_dirs["canon"] / "mirror_wid" / "pitch.md").read_text(encoding="utf-8")
        assert dst.read_text(encoding="utf-8") == canon_content

    def test_mirror_overwrites(self, pitch_dirs):
        normalize_pitch_to_canon(SAMPLE_RAW, work_id="ow_wid")
        pp_dir = pitch_dirs["preprocess"] / "ow_wid" / "00_brief"
        pp_dir.mkdir(parents=True)
        old = pp_dir / "pitch.md"
        old.write_text("stale content", encoding="utf-8")

        dst = mirror_pitch_to_preprocess("ow_wid")
        assert "stale content" not in dst.read_text(encoding="utf-8")
        assert SAMPLE_RAW in dst.read_text(encoding="utf-8")

    def test_mirror_no_canon(self, pitch_dirs):
        assert mirror_pitch_to_preprocess("ghost") is None

    def test_mirror_no_preprocess(self, pitch_dirs):
        normalize_pitch_to_canon(SAMPLE_RAW, work_id="no_pp")
        assert mirror_pitch_to_preprocess("no_pp") is None


# ---------------------------------------------------------------------------
# Completeness checks (unit)
# ---------------------------------------------------------------------------


class TestCompleteness:
    def test_empty_sections(self):
        sections = {s: "" for s in ("Hook", "Protagonist", "Conflict", "World", "Market Angle")}
        result = _eval_completeness(sections)
        assert all(v is False for v in result.values())

    def test_html_comment_only(self):
        sections = {
            "Hook": "<!-- placeholder -->",
            "Protagonist": "",
            "Conflict": "",
            "World": "",
            "Market Angle": "<!-- LLM or human fills this -->",
        }
        result = _eval_completeness(sections)
        assert result["hook"] is False
        assert result["market_angle"] is False

    def test_substantial_text(self):
        sections = {
            "Hook": "재벌 3세가 용돈 0원인 상태에서 시작하는 역전물",
            "Protagonist": "윤재이 — 재벌 3세 후계 경쟁자, 개인 현금 0원 상태",
            "Conflict": "가문 밑단 운영망 장악 vs 형제 방해",
            "World": "현대 한국 재벌 그룹 내부 — 하부 운영망 급식 호텔 공장 병원 중심",
            "Market Angle": "",
        }
        result = _eval_completeness(sections)
        assert result["hook"] is True
        assert result["protagonist"] is True
        assert result["conflict"] is True
        assert result["world"] is True
        assert result["market_angle"] is False


# ---------------------------------------------------------------------------
# Signals (unit)
# ---------------------------------------------------------------------------


class TestSignals:
    def test_block_engine(self):
        signals = _eval_signals("블록 1에서 블록 10까지 전개하는 엔진", {})
        assert signals["block_engine_sketched"] is True

    def test_no_block_engine(self):
        signals = _eval_signals("재벌 3세 이야기", {})
        assert signals["block_engine_sketched"] is False

    def test_defeat_beats(self):
        signals = _eval_signals("주인공이 위기에 빠지고 좌절한다", {})
        assert signals["defeat_beats_present"] is True

    def test_npc_pool(self):
        signals = _eval_signals("윤재이는 민태수와 하성우를 만난다", {})
        assert signals["npc_pool_present"] is True

    def test_npc_pool_insufficient(self):
        signals = _eval_signals("주인공이 달린다", {})
        assert signals["npc_pool_present"] is False


# ---------------------------------------------------------------------------
# Wuxia overlay signals (unit)
# ---------------------------------------------------------------------------


class TestWuxiaOverlay:
    def test_full_wuxia_signals(self):
        overlay = _eval_wuxia_overlay(SAMPLE_WUXIA_RAW)
        assert overlay["realm_terms_found"] is True
        assert overlay["sect_terms_found"] is True
        assert overlay["martial_showcase_found"] is True

    def test_naming_register_high(self):
        text = "백소연(白小燕)과 진무혁(陳武赫)과 이청풍(李淸風)이 강호를 누빈다"
        overlay = _eval_wuxia_overlay(text)
        assert overlay["naming_register"] == "high"

    def test_naming_register_low(self):
        text = "철수와 영희가 무림에서 싸운다. 내공이 강하다."
        overlay = _eval_wuxia_overlay(text)
        assert overlay["naming_register"] in ("low", "partial")

    def test_no_wuxia_terms(self):
        text = "현대 서울에서 재벌이 투자를 한다"
        overlay = _eval_wuxia_overlay(text)
        assert overlay["realm_terms_found"] is False
        assert overlay["sect_terms_found"] is False
        assert overlay["martial_showcase_found"] is False

    def test_wuxia_overlay_only_for_wuxguide(self, pitch_dirs):
        result = normalize_pitch(
            SAMPLE_WUXIA_RAW,
            slug="wuxia_test",
            family_guess="wuxguide",
        )
        assert "realm_terms_found" in result["overlay_signals"]

    def test_no_overlay_for_blockguide(self, pitch_dirs):
        result = normalize_pitch(
            SAMPLE_WUXIA_RAW,
            slug="block_test",
            family_guess="blockguide",
        )
        assert result["overlay_signals"] == {}


# ---------------------------------------------------------------------------
# Frontmatter round-trip
# ---------------------------------------------------------------------------


class TestFrontmatterRoundTrip:
    def test_round_trip(self, pitch_dirs):
        normalize_pitch_to_canon(
            SAMPLE_RAW,
            work_id="rt_test",
            title="Round Trip",
            family_guess="blockguide",
            genre_hint="investment",
        )
        data = read_pitch("rt_test")
        meta = data["meta"]
        assert meta["work_id"] == "rt_test"
        assert meta["title"] == "Round Trip"
        assert meta["family_guess"] == "blockguide"
        assert meta["genre_hint"] == "investment"
        assert meta["normalized_version"] == 1
        assert isinstance(meta["completeness"], dict)
        assert isinstance(meta["signals"], dict)
        assert meta["verdicts"] == {}


# ---------------------------------------------------------------------------
# Structured verdicts validation
# ---------------------------------------------------------------------------


class TestVerdicts:
    def test_valid_verdicts(self):
        verdicts = {
            "commercial_viability": {
                "status": "PASS",
                "rationale": "Strong differentiation",
                "reviewed_by": "human",
                "reviewed_at": "2026-03-29",
            },
            "old_pattern_check": {
                "status": "FAIL",
                "rationale": "회귀+만렙 패턴 검출",
                "reviewed_by": "llm",
                "reviewed_at": "2026-03-29",
            },
        }
        assert validate_verdicts(verdicts) == []

    def test_missing_keys(self):
        verdicts = {
            "bad_verdict": {
                "status": "PASS",
            },
        }
        errors = validate_verdicts(verdicts)
        assert len(errors) == 1
        assert "missing keys" in errors[0]

    def test_invalid_status(self):
        verdicts = {
            "test": {
                "status": "MAYBE",
                "rationale": "unsure",
                "reviewed_by": "human",
                "reviewed_at": "2026-03-29",
            },
        }
        errors = validate_verdicts(verdicts)
        assert any("MAYBE" in e for e in errors)

    def test_extra_keys(self):
        verdicts = {
            "test": {
                "status": "PASS",
                "rationale": "ok",
                "reviewed_by": "human",
                "reviewed_at": "2026-03-29",
                "extra_field": "bad",
            },
        }
        errors = validate_verdicts(verdicts)
        assert any("unexpected" in e for e in errors)

    def test_empty_verdicts_valid(self):
        assert validate_verdicts({}) == []

    def test_non_dict_verdict(self):
        errors = validate_verdicts({"bad": "string"})
        assert any("must be a dict" in e for e in errors)


# ---------------------------------------------------------------------------
# Path safety (Fix 1)
# ---------------------------------------------------------------------------


class TestPathSafety:
    def test_reject_slash_in_slug(self, pitch_dirs):
        with pytest.raises(ValueError, match="invalid characters"):
            normalize_pitch(SAMPLE_RAW, slug="../../etc")

    def test_reject_backslash_in_slug(self, pitch_dirs):
        with pytest.raises(ValueError, match="invalid characters"):
            normalize_pitch(SAMPLE_RAW, slug="foo\\bar")

    def test_reject_dot_dot_in_work_id(self, pitch_dirs):
        with pytest.raises(ValueError, match="invalid characters"):
            normalize_pitch_to_canon(SAMPLE_RAW, work_id="..")

    def test_reject_slash_in_work_id(self, pitch_dirs):
        with pytest.raises(ValueError, match="invalid characters"):
            normalize_pitch_to_canon(SAMPLE_RAW, work_id="a/b")

    def test_reject_empty_slug(self, pitch_dirs):
        with pytest.raises(ValueError, match="must not be empty"):
            normalize_pitch(SAMPLE_RAW, slug="")

    def test_reject_empty_work_id(self, pitch_dirs):
        with pytest.raises(ValueError, match="must not be empty"):
            normalize_pitch_to_canon(SAMPLE_RAW, work_id="")

    def test_reject_whitespace_only(self, pitch_dirs):
        with pytest.raises(ValueError, match="must not be empty"):
            normalize_pitch(SAMPLE_RAW, slug="   ")

    def test_reject_path_separator_in_promote(self, pitch_dirs):
        with pytest.raises(ValueError, match="invalid characters"):
            promote_pitch("../evil", "target")

    def test_reject_path_separator_in_read(self, pitch_dirs):
        with pytest.raises(ValueError, match="invalid characters"):
            read_pitch("../../etc/passwd")

    def test_reject_path_separator_in_read_pending(self, pitch_dirs):
        with pytest.raises(ValueError, match="invalid characters"):
            read_pending_pitch("foo/bar")

    def test_reject_path_separator_in_mirror(self, pitch_dirs):
        with pytest.raises(ValueError, match="invalid characters"):
            mirror_pitch_to_preprocess("../escape")

    def test_korean_slug_allowed(self, pitch_dirs):
        result = normalize_pitch(SAMPLE_RAW, slug="재벌물테스트")
        assert result["path"].exists()

    def test_hyphen_underscore_allowed(self, pitch_dirs):
        result = normalize_pitch(SAMPLE_RAW, slug="my-pitch_01")
        assert result["path"].exists()


# ---------------------------------------------------------------------------
# YAML escaping (Fix 2)
# ---------------------------------------------------------------------------


class TestYamlEscaping:
    def test_embedded_double_quote(self):
        assert _yaml_scalar('He said "hello"') == '"He said \\"hello\\""'

    def test_embedded_backslash(self):
        assert _yaml_scalar("path\\to\\file") == '"path\\\\to\\\\file"'

    def test_both_quote_and_backslash(self):
        s = 'a\\"b'
        result = _yaml_scalar(s)
        assert result == '"a\\\\\\"b"'

    def test_round_trip_with_quotes(self, pitch_dirs):
        title = '제목에 "큰따옴표"가 있다'
        normalize_pitch_to_canon(SAMPLE_RAW, work_id="yaml_rt", title=title)
        data = read_pitch("yaml_rt")
        assert data["meta"]["title"] == title

    def test_round_trip_with_backslash(self, pitch_dirs):
        title = "경로\\표시\\포함"
        normalize_pitch_to_canon(SAMPLE_RAW, work_id="yaml_bs", title=title)
        data = read_pitch("yaml_bs")
        assert data["meta"]["title"] == title

    def test_plain_string_no_quotes(self):
        assert _yaml_scalar("simple") == "simple"

    def test_colon_triggers_quoting(self):
        result = _yaml_scalar("key: value")
        assert result.startswith('"')
        assert result.endswith('"')


# ---------------------------------------------------------------------------
# Wuxia naming register (Fix 3)
# ---------------------------------------------------------------------------


class TestWuxiaNamingRegister:
    def test_hanja_annotated_names(self):
        """Names with hanja annotation are always wuxia-register."""
        assert _is_wuxia_register_name("백소연", frozenset({"백소연"})) is True

    def test_compound_surname(self):
        """Known wuxia compound surnames are always wuxia-register."""
        assert _is_wuxia_register_name("남궁세가", frozenset()) is True
        assert _is_wuxia_register_name("제갈명", frozenset()) is True
        assert _is_wuxia_register_name("독고진", frozenset()) is True

    def test_wuxia_syllable_3char(self):
        """3-char names with wuxia-register given syllables match."""
        assert _is_wuxia_register_name("진무혁", frozenset()) is True  # 무, 혁
        assert _is_wuxia_register_name("이청풍", frozenset()) is True  # 청, 풍

    def test_modern_name_no_match(self):
        """Modern Korean names without wuxia syllables don't match."""
        assert _is_wuxia_register_name("철수", frozenset()) is False
        assert _is_wuxia_register_name("영희", frozenset()) is False
        assert _is_wuxia_register_name("민수", frozenset()) is False

    def test_register_high_without_hanja(self):
        """Wuxia names without hanja annotation still score high."""
        text = "진무혁과 백소연과 이청풍이 강호를 누빈다"
        overlay = _eval_wuxia_overlay(text)
        assert overlay["naming_register"] == "high"

    def test_register_low_modern_names(self):
        """Pure modern names score low."""
        text = "철수와 영희가 무림에서 싸운다. 내공이 강하다."
        overlay = _eval_wuxia_overlay(text)
        assert overlay["naming_register"] == "low"

    def test_register_partial_mixed(self):
        """Mix of wuxia and modern names scores partial."""
        # 제갈명(compound surname) + 이청풍(wuxia syllables) = 2 wuxia
        # 철수 + 영희 + 민수 = 3 modern → 2/5 = 0.4 → partial
        text = "제갈명과 이청풍이 철수와 영희와 민수를 만난다"
        overlay = _eval_wuxia_overlay(text)
        assert overlay["naming_register"] == "partial"

    def test_2char_wuxia_name(self):
        """2-char names with wuxia syllables match."""
        assert _is_wuxia_register_name("검호", frozenset()) is True
        assert _is_wuxia_register_name("청풍", frozenset()) is True


# ---------------------------------------------------------------------------
# _assert_within: is_relative_to, not string prefix (Blocker 1)
# ---------------------------------------------------------------------------


class TestAssertWithin:
    def test_sibling_dir_rejected(self, tmp_path):
        """pending2/ must not pass as under pending/ (string prefix bug)."""
        root = tmp_path / "pending"
        root.mkdir()
        sibling = tmp_path / "pending2" / "evil"
        sibling.mkdir(parents=True)
        with pytest.raises(ValueError, match="escapes intended root"):
            _assert_within(sibling, root)

    def test_child_accepted(self, tmp_path):
        root = tmp_path / "pending"
        child = root / "good_slug" / "pitch.md"
        root.mkdir()
        (root / "good_slug").mkdir()
        # Should not raise
        _assert_within(child, root)


# ---------------------------------------------------------------------------
# Multiline scalar rejection (Blocker 2)
# ---------------------------------------------------------------------------


class TestMultilineRejection:
    def test_newline_in_scalar_raises(self):
        with pytest.raises(ValueError, match="newlines"):
            _yaml_scalar("line1\nline2")

    def test_carriage_return_raises(self):
        with pytest.raises(ValueError, match="newlines"):
            _yaml_scalar("line1\rline2")

    def test_newline_in_title_raises_at_normalize(self, pitch_dirs):
        with pytest.raises(ValueError, match="newlines"):
            normalize_pitch_to_canon(
                SAMPLE_RAW, work_id="nl_test", title="bad\ntitle"
            )
