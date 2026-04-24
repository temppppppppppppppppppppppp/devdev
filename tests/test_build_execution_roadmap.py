from __future__ import annotations

import json

from scripts import build_execution_roadmap


def test_build_execution_roadmap_rewrite_roadmap_ranks_rewrites_queue_state_and_roadmap(
    tmp_path, monkeypatch
):
    root = tmp_path
    docs = root / "docs"
    temp = docs / "temp"
    dated = docs / "2026-04-23"
    temp.mkdir(parents=True)
    dated.mkdir(parents=True)
    queue_state_path = temp / "queue-state.json"
    roadmap_body = "\n".join(
        [
            "# Active Temp Execution Roadmap",
            "",
            "Date: 2026-04-23",
            "Status: active",
            "Canonical Path: `docs/2026-04-23/active-temp-execution-roadmap.md`",
            "Temp Mirror Path: `docs/temp/execution-roadmap.md`",
            "",
            "## 3. Queue Semantics",
            "",
            "Working order:",
            "1. `beta` (parked future wave; depends on alpha but is currently misranked)",
            "2. `alpha` (parked future wave; upstream dependency)",
            "",
            "## 4. Immediate Next Moves",
            "",
            "1. keep the queue honest",
        ]
    )
    (dated / "active-temp-execution-roadmap.md").write_text(roadmap_body + "\n", encoding="utf-8")
    (temp / "execution-roadmap.md").write_text(roadmap_body + "\n", encoding="utf-8")
    queue_state_path.write_text(
        """{
  "version": "temp-queue-state-v1",
  "generated_at": "2026-04-23T00:00:00+00:00",
  "queue_mode": "aggregate",
  "active_item_count": 2,
  "roadmap": {
    "temp_path": "docs/temp/execution-roadmap.md",
    "canonical_path": "docs/2026-04-23/active-temp-execution-roadmap.md",
    "status": "active"
  },
  "items": [
    {
      "topic": "beta",
      "temp_path": "docs/temp/beta-execution-ssot.md",
      "canonical_path": "docs/2026-04-23/beta-execution-ssot.md",
      "status": "pending",
      "queue_role": "parked_future_wave",
      "roadmap_rank": 1,
      "depends_on": [
        "alpha"
      ],
      "mirror_present": true,
      "canonical_present": true
    },
    {
      "topic": "alpha",
      "temp_path": "docs/temp/alpha-execution-ssot.md",
      "canonical_path": "docs/2026-04-23/alpha-execution-ssot.md",
      "status": "pending",
      "queue_role": "parked_future_wave",
      "roadmap_rank": 2,
      "depends_on": [],
      "mirror_present": true,
      "canonical_present": true
    }
  ]
}
""",
        encoding="utf-8",
    )

    monkeypatch.setattr("scripts.ops_support.ROOT", root)
    monkeypatch.setattr("scripts.ops_support.DOCS", docs)
    monkeypatch.setattr("scripts.ops_support.TEMP", temp)
    monkeypatch.setattr("scripts.ops_support.QUEUE_STATE_PATH", queue_state_path)
    monkeypatch.setattr("scripts.build_execution_roadmap.ROOT", root)
    monkeypatch.setattr("scripts.build_execution_roadmap.DOCS", docs)
    monkeypatch.setattr("scripts.build_execution_roadmap.TEMP", temp)
    monkeypatch.setattr("scripts.build_execution_roadmap.QUEUE_STATE_PATH", queue_state_path)
    monkeypatch.setattr(
        "sys.argv",
        ["build_execution_roadmap.py", "--rewrite-roadmap-ranks"],
    )

    assert build_execution_roadmap.main() == 0

    rewritten_state = json.loads(queue_state_path.read_text(encoding="utf-8"))
    rewritten_topics = [item["topic"] for item in rewritten_state["items"]]
    rewritten_ranks = [item["roadmap_rank"] for item in rewritten_state["items"]]
    assert rewritten_topics == ["alpha", "beta"]
    assert rewritten_ranks == [1, 2]

    roadmap_text = (temp / "execution-roadmap.md").read_text(encoding="utf-8")
    assert "1. `alpha`" in roadmap_text
    assert "2. `beta`" in roadmap_text
    assert "## 4. Immediate Next Moves" in roadmap_text
    assert "keep the queue honest" in roadmap_text
    assert (dated / "active-temp-execution-roadmap.md").exists()
