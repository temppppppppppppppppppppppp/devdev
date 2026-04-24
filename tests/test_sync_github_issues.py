from __future__ import annotations

import json

from scripts.sync_github_issues import (
    ExistingIssue,
    QueueItem,
    build_sync_actions,
    issue_matches_topic,
    load_queue_items,
    parse_issue_number_from_url,
    render_issue_body,
    render_issue_title,
    write_github_issue_to_execution_doc,
)


def _execution_doc(topic: str, github_issue: int | None = None) -> str:
    issue_line = f"  github_issue: {github_issue}\n" if github_issue is not None else ""
    return (
        "# Sample Execution SSOT\n"
        "\n"
        "## 0. Execution Metadata Block\n"
        "\n"
        "```yaml\n"
        "execution_meta:\n"
        "  schema_version: execution-meta-block-v1\n"
        f"  topic: {topic}\n"
        f"{issue_line}"
        "  depends_on: []\n"
        "  tranches:\n"
        "    - id: first\n"
        "      title: First tranche\n"
        "```\n"
    )


def _item(topic: str = "repo-trashbox-cleanup", issue: int | None = None, *, root):
    canonical = root / "docs" / "2026-04-24" / f"{topic}-execution-ssot.md"
    temp = root / "docs" / "temp" / f"{topic}-execution-ssot.md"
    canonical.parent.mkdir(parents=True, exist_ok=True)
    temp.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text(_execution_doc(topic, issue), encoding="utf-8")
    temp.write_text(_execution_doc(topic, issue), encoding="utf-8")
    return QueueItem(
        topic=topic,
        temp_path=temp.relative_to(root).as_posix(),
        canonical_path=canonical.relative_to(root).as_posix(),
        status="pending",
        queue_role="parked_future_wave",
        roadmap_rank=5,
        depends_on=[],
    )


def test_parse_issue_number_from_url():
    assert parse_issue_number_from_url("https://github.com/o/r/issues/42") == 42


def test_load_queue_items(tmp_path):
    queue = tmp_path / "docs" / "temp" / "queue-state.json"
    queue.parent.mkdir(parents=True)
    queue.write_text(
        json.dumps(
            {
                "version": "temp-queue-state-v1",
                "items": [
                    {
                        "topic": "alpha",
                        "temp_path": "docs/temp/alpha-execution-ssot.md",
                        "canonical_path": "docs/2026-04-24/alpha-execution-ssot.md",
                        "status": "pending",
                        "queue_role": "parked_future_wave",
                        "roadmap_rank": 1,
                        "depends_on": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    items = load_queue_items(queue)

    assert [item.topic for item in items] == ["alpha"]
    assert items[0].roadmap_rank == 1


def test_render_issue_title_and_body():
    item = QueueItem(
        topic="repo-trashbox-cleanup",
        temp_path="docs/temp/repo-trashbox-cleanup-execution-ssot.md",
        canonical_path="docs/2026-04-24/repo-trashbox-cleanup-execution-ssot.md",
        status="pending",
        queue_role="parked_future_wave",
        roadmap_rank=5,
        depends_on=["canary-root-isolation"],
    )

    assert render_issue_title(item) == "[Parked] Repo Trashbox Cleanup"
    body = render_issue_body(item)
    assert "geuldobi-github-issue-sync" in body
    assert "topic=repo-trashbox-cleanup" in body
    assert "`canary-root-isolation`" in body


def test_render_issue_title_preserves_bi_tr_acronym():
    item = QueueItem(
        topic="stage0-bi-tr-production-harness-normalization-remediation",
        temp_path="docs/temp/stage0-bi-tr-production-harness-normalization-remediation-execution-ssot.md",
        canonical_path="docs/2026-04-02/stage0-bi-tr-production-harness-normalization-remediation-execution-ssot.md",
        status="pending",
        queue_role="parked_future_wave",
        roadmap_rank=3,
        depends_on=[],
    )

    assert render_issue_title(item) == "[Parked] Stage0 BI/TR Production Harness Normalization Remediation"


def test_issue_matches_topic_checks_marker_and_code_topic():
    assert issue_matches_topic(
        ExistingIssue(number=1, title="Human Title", body="topic=repo-trashbox-cleanup"),
        "repo-trashbox-cleanup",
    )
    assert issue_matches_topic(
        ExistingIssue(number=2, title="Human Title", body="- topic: `repo-trashbox-cleanup`"),
        "repo-trashbox-cleanup",
    )
    assert not issue_matches_topic(
        ExistingIssue(number=3, title="Human Title", body="unrelated"),
        "repo-trashbox-cleanup",
    )


def test_write_github_issue_to_execution_doc_inserts_after_topic(tmp_path):
    doc = tmp_path / "sample-execution-ssot.md"
    doc.write_text(_execution_doc("sample"), encoding="utf-8")

    changed = write_github_issue_to_execution_doc(doc, 17)

    assert changed is True
    text = doc.read_text(encoding="utf-8")
    assert "  topic: sample\n  github_issue: 17\n  depends_on: []" in text


def test_build_sync_actions_creates_when_no_issue_exists(tmp_path):
    item = _item(root=tmp_path)

    actions = build_sync_actions([item], root=tmp_path, find_existing_issue=lambda _: None)

    assert len(actions) == 1
    assert actions[0].kind == "create"
    assert actions[0].title == "[Parked] Repo Trashbox Cleanup"


def test_build_sync_actions_links_existing_issue(tmp_path):
    item = _item(root=tmp_path)

    actions = build_sync_actions(
        [item],
        root=tmp_path,
        find_existing_issue=lambda _: ExistingIssue(number=9, title="[Parked] Repo Trashbox Cleanup"),
    )

    assert len(actions) == 1
    assert actions[0].kind == "link"
    assert actions[0].issue_number == 9


def test_build_sync_actions_keeps_linked_issue_without_update(tmp_path):
    item = _item(issue=9, root=tmp_path)

    actions = build_sync_actions([item], root=tmp_path, find_existing_issue=lambda _: None)

    assert len(actions) == 1
    assert actions[0].kind == "linked"
    assert actions[0].issue_number == 9
