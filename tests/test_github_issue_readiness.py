from __future__ import annotations

from pathlib import Path

from scripts.github_issue_readiness import (
    evaluate_github_issue_readiness,
    parse_github_repo_from_remote,
)


def test_parse_github_repo_from_https_remote():
    assert (
        parse_github_repo_from_remote("https://github.com/example/project.git")
        == "example/project"
    )


def test_parse_github_repo_from_ssh_remote():
    assert parse_github_repo_from_remote("git@github.com:example/project.git") == "example/project"


def test_readiness_fails_when_active_doc_lacks_github_issue(tmp_path, monkeypatch):
    root = tmp_path
    temp = root / "docs" / "temp"
    temp.mkdir(parents=True)
    path = temp / "sample-execution-ssot.md"
    path.write_text(
        "\n".join(
            [
                "# Sample Execution SSOT",
                "",
                "## 0. Execution Metadata Block",
                "",
                "```yaml",
                "execution_meta:",
                "  schema_version: execution-meta-block-v1",
                "  topic: sample",
                "  depends_on: []",
                "  tranches:",
                "    - id: first",
                "      title: First tranche",
                "```",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "scripts.github_issue_readiness.get_origin_remote_url",
        lambda _: "https://github.com/example/project.git",
    )
    monkeypatch.setattr("scripts.github_issue_readiness.ROOT", root)
    monkeypatch.setattr("scripts.github_issue_readiness.TEMP", temp)
    monkeypatch.setattr("scripts.sync_temp_queue_state.ROOT", root)
    monkeypatch.setattr("scripts.sync_temp_queue_state.TEMP", temp)

    result = evaluate_github_issue_readiness(root=root, temp=temp)

    assert any("github_issue is missing" in message for message in result.errors)


def test_readiness_passes_when_all_active_docs_are_issue_linked(tmp_path, monkeypatch):
    root = tmp_path
    temp = root / "docs" / "temp"
    temp.mkdir(parents=True)

    alpha = temp / "alpha-execution-ssot.md"
    alpha.write_text(
        "\n".join(
            [
                "# Alpha Execution SSOT",
                "",
                "## 0. Execution Metadata Block",
                "",
                "```yaml",
                "execution_meta:",
                "  schema_version: execution-meta-block-v1",
                "  topic: alpha",
                "  github_issue: 3",
                "  depends_on: []",
                "  tranches:",
                "    - id: first",
                "      title: First tranche",
                "```",
            ]
        ),
        encoding="utf-8",
    )
    beta = temp / "beta-execution-ssot.md"
    beta.write_text(
        "\n".join(
            [
                "# Beta Execution SSOT",
                "",
                "## 0. Execution Metadata Block",
                "",
                "```yaml",
                "execution_meta:",
                "  schema_version: execution-meta-block-v1",
                "  topic: beta",
                "  github_issue: 5",
                "  depends_on:",
                "    - alpha",
                "  tranches:",
                "    - id: first",
                "      title: First tranche",
                "```",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "scripts.github_issue_readiness.get_origin_remote_url",
        lambda _: "https://github.com/example/project.git",
    )
    monkeypatch.setattr("scripts.github_issue_readiness.ROOT", root)
    monkeypatch.setattr("scripts.github_issue_readiness.TEMP", temp)
    monkeypatch.setattr("scripts.sync_temp_queue_state.ROOT", root)
    monkeypatch.setattr("scripts.sync_temp_queue_state.TEMP", temp)

    result = evaluate_github_issue_readiness(root=root, temp=temp)

    assert result.errors == []
    assert any("linked to GitHub issue #3" in message for message in result.infos)
    assert any("linked to GitHub issue #5" in message for message in result.infos)
