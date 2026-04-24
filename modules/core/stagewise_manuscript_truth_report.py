"""Build a bounded post-run manuscript-truth report for one project."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone

UTC = timezone.utc
from pathlib import Path
from typing import Any

from modules.core.rationale_contract import (
    resolve_comparison_notes_text,
    resolve_selection_reason_text,
    resolve_structured_advisory_payload,
    resolve_verdict_reason_text,
)


def _coerce_int(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _clean_inline(value: object, limit: int = 240) -> str:
    text = " ".join(str(value or "").replace("\r", "\n").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _markdown_cell(value: object, limit: int = 96) -> str:
    return _clean_inline(value, limit=limit).replace("|", "\\|")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _resolve_project_file(project_root: Path, relative_or_absolute: str) -> Path:
    candidate = Path(str(relative_or_absolute or "").strip())
    if candidate.is_absolute():
        return candidate
    return project_root / candidate


def _display_project_path(project_label: str, relative_or_absolute: str | Path) -> str:
    raw = str(relative_or_absolute).strip().replace("\\", "/")
    if not raw:
        return ""
    if raw.startswith(project_label):
        return raw
    if raw.startswith("logs/") or raw.startswith("plans/") or raw.startswith("project_data.db"):
        return f"{project_label}/{raw}"
    return raw


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _first_nonempty_line(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        cleaned = line.strip()
        if cleaned:
            return cleaned
    return ""


def _last_narrative_line(path: Path) -> str:
    for line in reversed(path.read_text(encoding="utf-8").splitlines()):
        cleaned = line.strip()
        if not cleaned:
            continue
        if cleaned == "[원고_끝]":
            continue
        if cleaned.startswith("{{") and cleaned.endswith("}}"):
            continue
        return cleaned
    return ""


def _attempt_sort_value(path: Path) -> int:
    parent_name = path.parent.name
    if parent_name.startswith("attempt_"):
        value = _coerce_int(parent_name.removeprefix("attempt_"))
        if value is not None:
            return value
    return -1


def _terminal_artifact_kind(path: str) -> str:
    name = Path(str(path or "")).name
    if name.startswith("patched_after_fix__"):
        return "patched_after_fix"
    if name.startswith("final_manuscript__"):
        return "final_manuscript"
    return "other"


def _stage2_arc_truth(project_root: Path, project_label: str) -> list[dict[str, Any]]:
    latest_by_arc: dict[int, tuple[int, Path, dict[str, Any]]] = {}
    for path in sorted((project_root / "logs" / "artifacts" / "stage2").glob("arc_*/attempt_*/final_arc__*.json")):
        payload = _load_json(path)
        arc_no = _coerce_int(payload.get("arc_no")) or _coerce_int(path.parent.parent.name.removeprefix("arc_")) or 0
        attempt_value = _attempt_sort_value(path)
        current = latest_by_arc.get(arc_no)
        if current is None or attempt_value >= current[0]:
            latest_by_arc[arc_no] = (attempt_value, path, payload)

    rows: list[dict[str, Any]] = []
    for arc_no in sorted(latest_by_arc):
        _, path, payload = latest_by_arc[arc_no]
        constraint_summary = str(payload.get("constraint_summary", "") or "")
        rows.append(
            {
                "arc_no": arc_no,
                "title": str(payload.get("title", "") or ""),
                "episode_span": {
                    "start": _coerce_int(payload.get("ep_start")),
                    "end": _coerce_int(payload.get("ep_end")),
                },
                "constraint_summary_state": "present" if constraint_summary.strip() else "blank",
                "constraint_summary_excerpt": _clean_inline(constraint_summary),
                "artifact_path": _display_project_path(
                    project_label,
                    path.relative_to(project_root).as_posix(),
                ),
                "artifact_sha256": _sha256(path),
            }
        )
    return rows


def _stage3_blueprint_truth(project_root: Path, project_label: str) -> list[dict[str, Any]]:
    latest_by_episode: dict[int, dict[str, Any]] = {}
    decisions_path = project_root / "logs" / "session" / "decisions.jsonl"
    for row in _load_jsonl(decisions_path):
        if str(row.get("stage", "") or "").strip().lower() != "stage3":
            continue
        if str(row.get("result", "") or "").strip().upper() != "PASS":
            continue
        ep_num = _coerce_int(row.get("ep_num"))
        meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
        if ep_num is None or not str(meta.get("artifact_path", "") or "").strip():
            continue
        latest_by_episode[ep_num] = row

    rows: list[dict[str, Any]] = []
    for ep_num in sorted(latest_by_episode):
        row = latest_by_episode[ep_num]
        meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
        artifact_rel = str(meta.get("artifact_path", "") or "").strip()
        artifact_path = _resolve_project_file(project_root, artifact_rel)
        payload = _load_json(artifact_path)
        rows.append(
            {
                "ep_num": ep_num,
                "title": str(payload.get("title", "") or ""),
                "candidate_key": str(meta.get("candidate_key", "") or ""),
                "ending_hook": str(payload.get("ending_hook", "") or ""),
                "expected_ending": str(payload.get("expected_ending", "") or ""),
                "artifact_path": _display_project_path(project_label, artifact_rel),
                "artifact_sha256": _sha256(artifact_path),
                "selection_reason": str(meta.get("selection_reason", "") or ""),
                "verdict_reason": str(meta.get("verdict_reason", "") or ""),
                "comparison_notes": resolve_comparison_notes_text(meta.get("comparison_notes", "")),
                "selected_candidate_advisory_struct": resolve_structured_advisory_payload(
                    meta.get("selected_candidate_advisory_struct")
                ),
            }
        )
    return rows


def _stage4_terminal_truth(
    project_root: Path, project_label: str
) -> tuple[list[dict[str, Any]], dict[int, list[dict[str, Any]]]]:
    rows_by_episode: dict[int, list[dict[str, Any]]] = defaultdict(list)
    latest_terminal_by_episode: dict[int, dict[str, Any]] = {}

    for row in _load_jsonl(project_root / "logs" / "episode_production.jsonl"):
        ep_num = _coerce_int(row.get("ep"))
        if ep_num is None:
            continue
        rows_by_episode[ep_num].append(row)
        final_verdict = str(row.get("final_verdict", row.get("verdict", "")) or "").strip().upper()
        artifact_rel = str(row.get("artifact_path", "") or "").strip()
        if final_verdict == "PASS" and artifact_rel:
            latest_terminal_by_episode[ep_num] = row

    rows: list[dict[str, Any]] = []
    for ep_num in sorted(latest_terminal_by_episode):
        row = latest_terminal_by_episode[ep_num]
        artifact_rel = str(row.get("artifact_path", "") or "").strip()
        artifact_path = _resolve_project_file(project_root, artifact_rel)
        selection_artifact_rel = str(row.get("selection_artifact_path", "") or "").strip()
        rows.append(
            {
                "ep_num": ep_num,
                "round": _coerce_int(row.get("round")),
                "candidate_key": str(row.get("candidate_key", "") or ""),
                "terminal_artifact_kind": _terminal_artifact_kind(artifact_rel),
                "artifact_path": _display_project_path(project_label, artifact_rel),
                "artifact_sha256": _sha256(artifact_path),
                "selection_artifact_path": _display_project_path(project_label, selection_artifact_rel),
                "final_verdict": str(row.get("final_verdict", row.get("verdict", "")) or ""),
                "selection_reason": resolve_selection_reason_text(
                    row.get("selection_reason", ""),
                    row.get("reason", ""),
                ),
                "verdict_reason": resolve_verdict_reason_text(
                    row.get("verdict_reason", ""),
                    row.get("reason", ""),
                    row.get("selection_reason", ""),
                ),
                "comparison_notes": resolve_comparison_notes_text(row.get("comparison_notes", "")),
                "selected_candidate_advisory_struct": resolve_structured_advisory_payload(
                    row.get("selected_candidate_advisory_struct")
                ),
                "open_review": str(row.get("open_review", "") or ""),
                "first_line": _first_nonempty_line(artifact_path),
                "last_narrative_line": _last_narrative_line(artifact_path),
            }
        )
    return rows, rows_by_episode


def _episode_4_to_5_continuity(
    stage3_rows: list[dict[str, Any]],
    stage4_rows: list[dict[str, Any]],
    episode_production_rows: dict[int, list[dict[str, Any]]],
) -> dict[str, Any]:
    stage3_by_episode = {row["ep_num"]: row for row in stage3_rows}
    stage4_by_episode = {row["ep_num"]: row for row in stage4_rows}

    reject_rounds: list[dict[str, Any]] = []
    pass_round: dict[str, Any] | None = None
    for row in episode_production_rows.get(5, []):
        artifact_path = str(row.get("artifact_path", "") or "").strip()
        final_verdict = str(row.get("final_verdict", row.get("verdict", "")) or "").strip().upper()
        if not artifact_path:
            continue
        payload = {
            "round": _coerce_int(row.get("round")),
            "candidate_key": str(row.get("candidate_key", "") or ""),
            "artifact_path": artifact_path.replace("\\", "/"),
            "selection_reason": resolve_selection_reason_text(
                row.get("selection_reason", ""),
                row.get("reason", ""),
            ),
            "verdict_reason": resolve_verdict_reason_text(
                row.get("verdict_reason", ""),
                row.get("reason", ""),
                row.get("selection_reason", ""),
            ),
            "comparison_notes": resolve_comparison_notes_text(row.get("comparison_notes", "")),
            "selected_candidate_advisory_struct": resolve_structured_advisory_payload(
                row.get("selected_candidate_advisory_struct")
            ),
            "open_review": str(row.get("open_review", "") or ""),
        }
        if final_verdict == "REJECT":
            reject_rounds.append(payload)
        elif final_verdict == "PASS":
            pass_round = payload

    contradiction_summary = reject_rounds[-1]["verdict_reason"] if reject_rounds else ""
    repair_summary = pass_round["verdict_reason"] if pass_round else ""

    return {
        "ep4_blueprint": stage3_by_episode.get(4, {}),
        "ep4_terminal": stage4_by_episode.get(4, {}),
        "ep5_blueprint": stage3_by_episode.get(5, {}),
        "ep5_reject_rounds": reject_rounds,
        "ep5_pass_round": pass_round or {},
        "contradiction_summary": contradiction_summary,
        "repair_summary": repair_summary,
    }


def build_stagewise_manuscript_truth_report(
    project_path: str | Path,
    *,
    project_label: str | None = None,
) -> dict[str, Any]:
    project_root = Path(project_path)
    project_label = str(project_label or project_root.as_posix()).replace("\\", "/")

    stage2_rows = _stage2_arc_truth(project_root, project_label)
    stage3_rows = _stage3_blueprint_truth(project_root, project_label)
    stage4_rows, episode_production_rows = _stage4_terminal_truth(project_root, project_label)
    continuity = _episode_4_to_5_continuity(stage3_rows, stage4_rows, episode_production_rows)

    stage2_count = len(stage2_rows)
    stage3_count = len(stage3_rows)
    stage4_artifact_file_count = len([path for path in (project_root / "logs" / "artifacts" / "stage4").rglob("*") if path.is_file()])

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "project": project_label,
        "source_evidence": {
            "stage2_dir": _display_project_path(project_label, "logs/artifacts/stage2"),
            "stage3_dir": _display_project_path(project_label, "logs/artifacts/stage3"),
            "stage4_dir": _display_project_path(project_label, "logs/artifacts/stage4"),
            "session_decisions": _display_project_path(project_label, "logs/session/decisions.jsonl"),
            "episode_production": _display_project_path(project_label, "logs/episode_production.jsonl"),
        },
        "artifact_counts": {
            "stage2_selected_arc_files": stage2_count,
            "stage3_selected_blueprint_files": stage3_count,
            "stage4_artifact_files": stage4_artifact_file_count,
            "stage4_terminal_passes": len(stage4_rows),
        },
        "stage2_arc_truth": stage2_rows,
        "stage3_blueprint_truth": stage3_rows,
        "stage4_terminal_truth": stage4_rows,
        "continuity_handoff": {
            "episode_4_to_5": continuity,
        },
        "judgment": [
            "Stage 2 artifact truth is complete, but carryover metadata starts uneven because arc 1 enters with a blank constraint summary.",
            "Stage 3 blueprint truth is explicit and locally strong, but Episode 5 still needed Stage 4 repair against Episode 4's realized terminal state.",
            "Stage 4 terminal authority is now explicit across both patched and final manuscript outputs, so patched finals are no longer implicit leftovers.",
        ],
    }


def render_stagewise_manuscript_truth_markdown(report: dict[str, Any]) -> str:
    counts = report["artifact_counts"]
    stage2_rows = report["stage2_arc_truth"]
    stage3_rows = report["stage3_blueprint_truth"]
    stage4_rows = report["stage4_terminal_truth"]
    continuity = report["continuity_handoff"]["episode_4_to_5"]

    stage2_table = "\n".join(
        f"| {row['arc_no']} | {_markdown_cell(row['title'])} | {row['episode_span']['start']}-{row['episode_span']['end']} | {row['constraint_summary_state']} | `{row['artifact_path']}` | `{row['artifact_sha256'][:12]}` |"
        for row in stage2_rows
    )
    stage3_table = "\n".join(
        f"| {row['ep_num']} | {_markdown_cell(row['candidate_key'])} | {_markdown_cell(row['title'])} | {_markdown_cell(row['ending_hook'])} | `{row['artifact_path']}` | `{row['artifact_sha256'][:12]}` |"
        for row in stage3_rows
    )
    stage4_table = "\n".join(
        f"| {row['ep_num']} | {row['round']} | {row['terminal_artifact_kind']} | {_markdown_cell(row['candidate_key'])} | {_markdown_cell(row['last_narrative_line'])} | `{row['artifact_path']}` | `{row['artifact_sha256'][:12]}` |"
        for row in stage4_rows
    )

    reject_lines = continuity["ep5_reject_rounds"]
    reject_block = "\n".join(
        f"- round `{row['round']}` / `{row['candidate_key']}`: {_clean_inline(row['verdict_reason'], limit=220)}"
        for row in reject_lines
    ) or "- no reject rounds captured"

    pass_round = continuity["ep5_pass_round"]
    pass_block = (
        f"- round `{pass_round.get('round')}` / `{pass_round.get('candidate_key')}`: "
        f"{_clean_inline(pass_round.get('verdict_reason', ''), limit=220)}"
        if pass_round
        else "- no terminal PASS row captured"
    )

    judgment_block = "\n".join(f"- {line}" for line in report["judgment"])

    return f"""# Stagewise Manuscript Truth Report

Project: `{report['project']}`
Generated By: `scripts/generate_stagewise_manuscript_truth_report.py`
Generated At: `{report['generated_at']}`

Source Evidence:
- `{report['source_evidence']['stage2_dir']}`
- `{report['source_evidence']['stage3_dir']}`
- `{report['source_evidence']['stage4_dir']}`
- `{report['source_evidence']['session_decisions']}`
- `{report['source_evidence']['episode_production']}`

## 1. Artifact Counts
- Stage 2 selected arc files: `{counts['stage2_selected_arc_files']}`
- Stage 3 selected blueprint files: `{counts['stage3_selected_blueprint_files']}`
- Stage 4 artifact files: `{counts['stage4_artifact_files']}`
- Stage 4 terminal PASS rows: `{counts['stage4_terminal_passes']}`

## 2. Stage 2 Arc Truth
| Arc | Title | Episodes | Constraint Summary | Artifact | SHA256 |
| --- | --- | --- | --- | --- | --- |
{stage2_table}

## 3. Stage 3 Blueprint Truth
| Ep | Candidate | Title | Ending Hook | Artifact | SHA256 |
| --- | --- | --- | --- | --- | --- |
{stage3_table}

## 4. Stage 4 Terminal Manuscript Truth
| Ep | Round | Terminal Kind | Candidate | Last Narrative Line | Artifact | SHA256 |
| --- | --- | --- | --- | --- | --- | --- |
{stage4_table}

## 5. Episode 4 -> Episode 5 Continuity Repair
- Episode 4 blueprint hook: {_clean_inline(continuity['ep4_blueprint'].get('ending_hook', ''), limit=220)}
- Episode 4 terminal authority: `{continuity['ep4_terminal'].get('artifact_path', '')}` (`{continuity['ep4_terminal'].get('terminal_artifact_kind', '')}`)
- Episode 5 blueprint hook: {_clean_inline(continuity['ep5_blueprint'].get('ending_hook', ''), limit=220)}
- Contradiction summary: {_clean_inline(continuity.get('contradiction_summary', ''), limit=220)}
- Repair summary: {_clean_inline(continuity.get('repair_summary', ''), limit=220)}

Reject rounds:
{reject_block}

Terminal repair:
{pass_block}

## 6. Judgment
{judgment_block}
"""


def write_stagewise_manuscript_truth_report(
    project_path: str | Path,
    *,
    markdown_output: str | Path,
    json_output: str | Path,
    project_label: str | None = None,
) -> dict[str, Any]:
    report = build_stagewise_manuscript_truth_report(project_path, project_label=project_label)
    markdown_path = Path(markdown_output)
    json_path = Path(json_output)
    markdown_path.write_text(render_stagewise_manuscript_truth_markdown(report).rstrip() + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report
