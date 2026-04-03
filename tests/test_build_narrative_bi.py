from __future__ import annotations

import json
import sys
from types import SimpleNamespace

import scripts.build_narrative_bi as script


def _write_json(path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _full_content(label: str) -> dict:
    return {
        "context": f"{label} 배경",
        "event_villain": f"{label} 사건",
        "solution": f"{label} 해결",
        "reward": f"{label} 보상",
    }


def test_build_narrative_bi_reports_canonical_and_normalized_status(monkeypatch, capsys, temp_dir):
    phase0_path = temp_dir / "phase0.json"
    draft_path = temp_dir / "draft.json"
    output_path = temp_dir / "bi.json"

    _write_json(phase0_path, {"project": {"title": "테스트 작품"}})
    _write_json(
        draft_path,
        {
            "blocks": [
                {
                    "block_id": "Block 1",
                    "title": "정본 블록 1",
                    "content": _full_content("정본"),
                }
            ]
        },
    )
    _write_json(
        output_path,
        {
            "MasterBible": {
                "ProjectData": {
                    "MetaInfo": {"title": "정본 작품"},
                    "CoreIdentity": {"protagonist": "주인공"},
                },
                "protagonist_config": {
                    "world_origin": "현대인",
                    "incarnation_type": "회귀자",
                    "pov": "3인칭",
                    "external_pov_insert_policy": "제한적 허용",
                },
                "plot_roadmap": [
                    {
                        "block_no": 1,
                        "title": "정본 블록 1",
                        "content": _full_content("정본"),
                    }
                ],
            }
        },
    )

    family = SimpleNamespace(
        key="blockguide",
        contract=SimpleNamespace(
            bi=SimpleNamespace(
                builder_script="scripts/build_bi_from_phase0_and_tr.py",
                audit_script="scripts/audit_bi_5pass.py",
                hud_root="FinanceHUD",
                required_phase0_sections=(),
                required_phase0_design_fields=(),
                required_master_sections=(),
            )
        ),
    )
    monkeypatch.setattr(script, "resolve_family_plugin", lambda **_kwargs: family)
    monkeypatch.setattr(script, "resolve_route", lambda **_kwargs: SimpleNamespace())
    monkeypatch.setattr(script.subprocess, "run", lambda *_args, **_kwargs: SimpleNamespace(returncode=0))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_narrative_bi.py",
            "--phase0",
            str(phase0_path),
            "--draft",
            str(draft_path),
            "--output",
            str(output_path),
            "--family",
            "blockguide",
        ],
    )

    exit_code = script.main()
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "[CHECK] pair=pass" in out
    assert "canonical=fail (tr=fail, bi=pass)" in out
    assert "normalized=pass (tr=pass, bi=pass)" in out
