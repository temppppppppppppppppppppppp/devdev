from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TARGETS = {
    ROOT / "main_a.py": [
        "Faulthandler 활성화",
        "Faulthandler 초기화 실패",
        "Stage 0 모듈 로드 실패",
        "[V50] 일부 모듈 미설치",
        "print(message, flush=True)",
    ],
    ROOT / "modules" / "core" / "stage3_orchestrator.py": [],
    ROOT / "modules" / "core" / "stage4_orchestrator.py": [],
    ROOT / "modules" / "core" / "stage4_interview_round.py": [],
    ROOT / "modules" / "domain" / "agents" / "base_agent.py": [],
    ROOT / "modules" / "domain" / "agents" / "arc_ensemble.py": [],
    ROOT / "modules" / "domain" / "agents" / "blueprint_ensemble.py": [],
    ROOT / "modules" / "domain" / "agents" / "chief_writer.py": [],
    ROOT / "modules" / "domain" / "agents" / "chief_writer_quality.py": [],
    ROOT / "modules" / "domain" / "agents" / "analyst.py": [],
    ROOT / "modules" / "domain" / "agents" / "three_phase_blueprint_generator.py": [],
    ROOT / "modules" / "domain" / "agents" / "unified_arc_validator.py": [],
    ROOT / "modules" / "domain" / "agents" / "director_ensemble.py": [],
    ROOT / "modules" / "domain" / "agents" / "director_auditor.py": [],
    ROOT / "modules" / "core" / "services" / "ui_service.py": [],
    ROOT / "modules" / "core" / "stage0" / "__init__.py": [],
    ROOT / "modules" / "core" / "stage0" / "style_extractor.py": [],
    ROOT / "modules" / "core" / "stage01_helpers.py": [],
}


def _collect_raw_print_segments(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source)
    segments: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "print":
            continue
        segment = ast.get_source_segment(source, node)
        assert segment is not None, f"missing source segment for print() in {path}"
        segments.append(segment)
    return segments


def test_runtime_raw_print_allowlist_is_explicit_and_bounded():
    for path, allow_markers in TARGETS.items():
        segments = _collect_raw_print_segments(path)
        unexpected = [
            segment
            for segment in segments
            if not any(marker in segment for marker in allow_markers)
        ]
        assert not unexpected, f"{path}: unexpected raw print(s): {unexpected}"
