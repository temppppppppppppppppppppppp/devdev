from pathlib import Path


INDEX_HTML = Path("geuldobi-desktop/src/index.html").read_text(encoding="utf-8")


def test_escape_helpers_exist():
    assert "function escapeHtml(value)" in INDEX_HTML
    assert 'function sanitizeToken(value, fallback = "pending")' in INDEX_HTML


def test_high_risk_dynamic_surfaces_use_escape_html():
    expected_fragments = [
        "${actionTitle}",
        "${actionSummary}",
        "${actionImpact}",
        "${actionNote}",
        "${shortLabel}",
        "${titleLabel}",
        "${metaLabel}",
        "${detailLabel}",
        "${pathLabel}",
        "${warningLabel}",
        "${safeSources}",
        "${safeWarningsText}",
        "${signalReason}",
        "${noteLabel}${verdictLabel}",
        "${notesLabel}",
        "${signalLabel} advisory 후보",
        'const safeFileName = escapeHtml(f.name);',
    ]
    for fragment in expected_fragments:
        assert fragment in INDEX_HTML


def test_dynamic_class_tokens_are_sanitized():
    assert 'const status = sanitizeToken(item.status, "pending");' in INDEX_HTML
    assert 'const signalStatus = sanitizeToken(stat.status, "watch");' in INDEX_HTML
