from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.archive_benchmark_record import archive_benchmark_record


def safe_archive_benchmark_record(
    *,
    workspace_root: str | Path,
    project: str,
    lane: str,
    target_ep: int | None = None,
    status: str = "snapshot",
    notes: str = "",
    run_label: str | None = None,
) -> dict[str, Any]:
    try:
        manifest = archive_benchmark_record(
            workspace_root=workspace_root,
            project=project,
            lane=lane,
            target_ep=target_ep,
            status=status,
            notes=notes,
            run_label=run_label,
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "error": str(exc),
            "lane": lane,
            "target_ep": target_ep,
        }
    return {
        "status": "ok",
        "lane": lane,
        "target_ep": target_ep,
        "run_id": manifest.get("run_id", ""),
        "record_root": manifest.get("record_root", ""),
    }
