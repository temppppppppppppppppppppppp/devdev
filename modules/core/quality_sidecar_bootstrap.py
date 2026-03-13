from __future__ import annotations

import ast
import json
import logging
from pathlib import Path
from typing import Any

from modules.core.db_manager import DBManager
from modules.core.project_support import inspect_project_support_assets, load_work_guard_summary
from modules.core.quality_signal_metrics import compute_quality_signal_bundle

logger = logging.getLogger(__name__)


def _load_metrics_records(metrics_path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not metrics_path.exists():
        return records

    try:
        with metrics_path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    parsed = json.loads(line)
                except (TypeError, ValueError, json.JSONDecodeError):
                    continue
                if isinstance(parsed, dict):
                    records.append(parsed)
    except Exception as exc:
        logger.debug("quality metrics load failed for %s: %s", metrics_path, exc)
    return records


def _latest_stage4_validations(records: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    latest: dict[int, dict[str, Any]] = {}
    for row in records:
        if row.get("type") != "validation":
            continue
        try:
            ep_num = int(row.get("ep_num") or 0)
            stage = int(row.get("stage") or 0)
        except (TypeError, ValueError):
            continue
        if ep_num <= 0 or stage != 4:
            continue
        latest[ep_num] = row
    return latest


def _extract_manuscript_text(raw: Any) -> str:
    text = str(raw or "").strip()
    if not text:
        return ""

    for _ in range(2):
        stripped = text.strip()
        parsed: dict[str, Any] | None = None
        if stripped.startswith("{") and stripped.endswith("}"):
            try:
                parsed = json.loads(stripped)
            except (TypeError, ValueError, json.JSONDecodeError):
                try:
                    maybe = ast.literal_eval(stripped)
                except (SyntaxError, ValueError):
                    maybe = None
                parsed = maybe if isinstance(maybe, dict) else None
        if not isinstance(parsed, dict):
            break
        next_text = ""
        for key in ("corrected_manuscript", "content", "manuscript", "text"):
            value = parsed.get(key)
            if isinstance(value, str) and value.strip():
                next_text = value.strip()
                break
        if not next_text:
            break
        text = next_text

    if text.startswith("# "):
        parts = text.splitlines()
        if len(parts) >= 3 and not parts[1].strip():
            text = "\n".join(parts[2:]).strip()
    return text.strip()


def _load_manuscript_text(project_dir: Path, db: DBManager, ep_num: int) -> str:
    try:
        row = db.get_manuscript(ep_num)
    except Exception as exc:
        logger.debug("db manuscript load failed for ep=%s: %s", ep_num, exc)
        row = None

    candidates: list[str] = []
    if isinstance(row, dict):
        candidates.append(_extract_manuscript_text(row.get("content")))

    draft_path = project_dir / "drafts" / f"ep_{ep_num:04d}.txt"
    if draft_path.exists():
        try:
            candidates.append(_extract_manuscript_text(draft_path.read_text(encoding="utf-8")))
        except Exception as exc:
            logger.debug("draft load failed for %s: %s", draft_path, exc)

    return next((candidate for candidate in candidates if candidate), "")


def _get_latest_stage4_selection(db: DBManager, ep_num: int) -> dict[str, Any] | None:
    predicate = DBManager._director_stage_predicate(4)
    with db._lock:
        cur = db.conn.cursor()
        try:
            cur.execute(
                "SELECT verdict, score, selection_reason, advisory_warnings "
                "FROM director_selections "
                "WHERE ep_num = ? AND " + predicate + " ORDER BY id DESC LIMIT 1",
                (ep_num,),
            )
            row = cur.fetchone()
        finally:
            cur.close()
    return dict(row) if row else None


def inspect_quality_sidecar_health(project_dir: Path, db: DBManager) -> dict[str, Any]:
    metrics_path = project_dir / "logs" / "quality_metrics.jsonl"
    records = _load_metrics_records(metrics_path)
    stage4_validations = _latest_stage4_validations(records)
    retrieval_observations = sum(1 for row in records if row.get("type") == "retrieval_observation")
    with db._lock:
        cur = db.conn.cursor()
        try:
            label_count = int(cur.execute("SELECT COUNT(*) FROM episode_quality_labels").fetchone()[0])
            signal_count = int(cur.execute("SELECT COUNT(*) FROM episode_quality_signals").fetchone()[0])
            review_count = int(cur.execute("SELECT COUNT(*) FROM episode_quality_observations").fetchone()[0])
        finally:
            cur.close()

    payload = {
        "metrics_rows": len(records),
        "stage4_validation_eps": len(stage4_validations),
        "retrieval_observation_rows": retrieval_observations,
        "quality_label_rows": label_count,
        "quality_signal_rows": signal_count,
        "manual_review_rows": review_count,
        "missing_label_eps": max(0, len(stage4_validations) - label_count),
        "missing_signal_eps": max(0, len(stage4_validations) - signal_count),
    }
    support_assets = inspect_project_support_assets(project_dir)
    payload.update(load_work_guard_summary(project_dir))
    payload["author_directives_exists"] = bool(support_assets["author_directives"]["exists"])
    payload["style_guide_exists"] = bool(support_assets["style_guide"]["exists"])
    payload["style_tone"] = str(support_assets["style_guide"]["tone"] or "")
    payload["style_pov"] = str(support_assets["style_guide"]["pov"] or "")
    return payload


def bootstrap_quality_sidecars(project_dir: Path, db: DBManager) -> dict[str, Any]:
    metrics_path = project_dir / "logs" / "quality_metrics.jsonl"
    records = _load_metrics_records(metrics_path)
    latest_validations = _latest_stage4_validations(records)
    report = {
        "metrics_rows": len(records),
        "stage4_validation_eps": len(latest_validations),
        "retrieval_observation_rows": sum(1 for row in records if row.get("type") == "retrieval_observation"),
        "backfilled_labels": 0,
        "backfilled_signals": 0,
        "missing_manuscript_eps": [],
    }
    support_assets = inspect_project_support_assets(project_dir)
    report.update(load_work_guard_summary(project_dir))
    report["author_directives_exists"] = bool(support_assets["author_directives"]["exists"])
    report["style_guide_exists"] = bool(support_assets["style_guide"]["exists"])

    if not latest_validations:
        return report

    for ep_num, validation_row in sorted(latest_validations.items()):
        label_row = db.get_episode_quality_label(ep_num)
        if label_row is None:
            selection = _get_latest_stage4_selection(db, ep_num) or {}
            decision = str(selection.get("verdict") or validation_row.get("decision") or "").strip().upper()
            if not decision:
                decision = "UNKNOWN"
            score_value = selection.get("score", validation_row.get("score", 0))
            try:
                score = int(score_value or 0)
            except (TypeError, ValueError):
                score = 0
            db.save_episode_quality_label(
                ep_num,
                {
                    "score": score,
                    "verdict": decision,
                    "selection_reason": str(selection.get("selection_reason") or "").strip(),
                    "open_review": "",
                    "score_breakdown": {},
                    "consistency_checklist": {},
                },
            )
            report["backfilled_labels"] += 1
            label_row = db.get_episode_quality_label(ep_num)

        if db.get_episode_quality_signal(ep_num) is not None:
            continue

        manuscript_text = _load_manuscript_text(project_dir, db, ep_num)
        signals = validation_row.get("quality_signals") if isinstance(validation_row.get("quality_signals"), dict) else {}
        if not signals:
            if not manuscript_text:
                report["missing_manuscript_eps"].append(ep_num)
                continue
            signals = compute_quality_signal_bundle(
                manuscript_text,
                consistency_checklist=(label_row or {}).get("consistency_checklist", {}),
                warning_count=int(validation_row.get("warnings", 0) or 0),
            )
        db.save_episode_quality_signal(ep_num, signals)
        report["backfilled_signals"] += 1

    return report
