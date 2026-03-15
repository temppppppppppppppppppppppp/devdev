from pathlib import Path

from scripts.check_utf8_hygiene import _coerce_for_terminal, collect_findings


def test_clean_file_has_no_findings(tmp_path):
    target = tmp_path / "clean.py"
    target.write_text('print("ok")\n', encoding="utf-8")

    assert collect_findings([target]) == []


def test_invalid_utf8_is_reported(tmp_path):
    target = tmp_path / "broken.txt"
    target.write_bytes(b"\xff\xfe\x80")

    findings = collect_findings([target])

    assert len(findings) == 1
    assert findings[0].kind == "invalid_utf8"


def test_replacement_character_is_reported(tmp_path):
    target = tmp_path / "replacement.md"
    target.write_text("broken \ufffd token\n", encoding="utf-8")

    findings = collect_findings([target])

    assert any(finding.kind == "replacement_character" for finding in findings)


def test_suspicious_question_token_is_reported(tmp_path):
    target = tmp_path / "question.txt"
    target.write_text("?\uac00\n", encoding="utf-8")

    findings = collect_findings([target])

    assert any(finding.kind == "suspicious_question_token" for finding in findings)


def test_legitimate_korean_question_prompt_is_allowed(tmp_path):
    target = tmp_path / "prompt.txt"
    target.write_text("\uba87 \uac1c \ucd08\uae30 tranche\ub85c Arc\ub97c \uc9c4\ud589\ud560\uae4c\uc694?\n", encoding="utf-8")

    assert collect_findings([target]) == []


def test_mixed_ascii_hangul_terminal_question_token_is_allowed(tmp_path):
    target = tmp_path / "arc_prompt.txt"
    target.write_text("Arc\ub85c?\n", encoding="utf-8")

    assert collect_findings([target]) == []


def test_hangul_cjk_mixed_token_is_reported(tmp_path):
    target = tmp_path / "mixed.txt"
    target.write_text("\u4e2d\uac00\n", encoding="utf-8")

    findings = collect_findings([target])

    assert any(finding.kind == "hangul_cjk_mixed_token" for finding in findings)


def test_allow_line_marker_skips_literal_example(tmp_path):
    target = tmp_path / "allowed.md"
    target.write_text("literal ??? example  # utf8-hygiene: allow-line\n", encoding="utf-8")

    assert collect_findings([target]) == []


def test_terminal_coercion_escapes_unencodable_emoji_for_cp949():
    rendered = _coerce_for_terminal("broken \U0001f3b9 token", encoding="cp949")

    assert "broken " in rendered
    assert "\\U0001f3b9" in rendered


def test_repo_contract_locks_utf8_guardrails():
    agents = Path("AGENTS.md").read_text(encoding="utf-8")
    pre_commit = Path(".pre-commit-config.yaml").read_text(encoding="utf-8")
    editorconfig = Path(".editorconfig").read_text(encoding="utf-8")
    init_harness = Path("docs/implementation/system-order-init-harness.md").read_text(encoding="utf-8")

    assert "## Encoding Guardrails" in agents
    assert "UTF-8은 시스템 오더와 서사 파이프라인 오더를 모두 포함하는 워크스페이스 전역 불변식이다." in agents
    assert "scripts/check_utf8_hygiene.py" in agents
    assert "triple-question placeholder, `U+FFFD`" in agents
    assert "charset = utf-8" in editorconfig
    assert "check-utf8-hygiene" in pre_commit
    assert "Treat UTF-8 integrity as a workspace-wide invariant" in init_harness
