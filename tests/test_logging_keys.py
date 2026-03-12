from unittest.mock import MagicMock

from modules.core.logging_keys import build_attempt_key, resolve_logging_session_id


def test_build_attempt_key_includes_session_id_when_present():
    assert build_attempt_key(stage=4, ep_num=7, arc_num=1, attempt_num=2, session_id="sess") == "s4:ep7:arc1:a2:sess"


def test_resolve_logging_session_id_ignores_magicmock_attributes():
    source = MagicMock()
    source.metrics_session_id = MagicMock()
    source.session_id = MagicMock()

    assert resolve_logging_session_id(source, fallback="fallback_sess") == "fallback_sess"


def test_resolve_logging_session_id_prefers_explicit_strings():
    source = MagicMock()
    source.metrics_session_id = "metrics_sess"
    source.session_id = "legacy_sess"

    assert resolve_logging_session_id(source, fallback="fallback_sess") == "metrics_sess"
