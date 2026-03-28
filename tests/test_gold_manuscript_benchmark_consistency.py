from __future__ import annotations

import json
from pathlib import Path

from scripts.gold_manuscript_benchmark_support import (
    attach_lightweight_ledgers,
    build_gold_package,
    run_gold_benchmark,
)


def _write_episode(path: Path, episode: int, body: str) -> None:
    path.write_text(f"Episode {episode}\n\n{body}\n", encoding="utf-8")


def _build_title_dir(tmp_path: Path) -> Path:
    title_dir = tmp_path / "benchmark_title"
    title_dir.mkdir(parents=True)
    for episode in range(1, 5):
        body = (
            f"주인공은 {episode}화에서도 본사 회의실에서 계약과 보고를 이어갔다. "
            f"마지막 장면에서는 투자팀이 다음 대응을 준비했다. " * 12
        )
        _write_episode(title_dir / f"ep{episode:03d}.txt", episode, body)
    return title_dir


def test_consistency_score_flags_dead_npc_action(tmp_path: Path) -> None:
    title_dir = _build_title_dir(tmp_path)
    gold_package = build_gold_package(title_dir, title="benchmark_title", checkpoint_size=2, max_cases=1)
    case = gold_package["cases"][0]
    case["gold_ledger"] = {
        "dead_npcs": {"박성민": {"ep": 1}},
        "alive_npcs": {"강민우": {"traits": "냉정", "role": "팀장"}},
        "protagonist": {"location": "서울 본사"},
    }

    candidate_dir = tmp_path / "candidates"
    candidate_dir.mkdir()
    (candidate_dir / f"{case['case_id']}.txt").write_text(
        "박성민이 웃으며 문을 열고 회의실 안으로 들어왔다.\n",
        encoding="utf-8",
    )

    result = run_gold_benchmark(gold_package, candidate_dir=candidate_dir, genre="investment")

    assert result["consistency_primary_axis"] == "consistency_score"
    assert result["average_consistency_score"] < 100.0
    first = result["results"][0]
    assert first["consistency_source_mode"] == "lightweight-ledger"
    assert first["truth_warning_count"] >= 1
    assert first["major_contradiction_count"] >= 1
    assert any(finding["source"] == "truth_gate" for finding in first["consistency_findings"])


def test_attach_lightweight_ledgers_and_manual_constraints(tmp_path: Path) -> None:
    title_dir = _build_title_dir(tmp_path)
    gold_package = build_gold_package(title_dir, title="benchmark_title", checkpoint_size=2, max_cases=1)
    case = gold_package["cases"][0]

    ledger_path = tmp_path / "gold_ledger_light.json"
    ledger_path.write_text(
        (
            "{\n"
            '  "cases": {\n'
            f'    "{case["case_id"]}": {{\n'
            '      "protagonist": {"location": "서울 본사"},\n'
            '      "manual_constraints": [\n'
            '        {\n'
            '          "id": "opening_anchor",\n'
            '          "type": "require_any_terms",\n'
            '          "scope": "opening",\n'
            '          "terms": ["회의실", "투자팀"],\n'
            '          "min_matches": 1,\n'
            '          "severity": "WARNING"\n'
            "        }\n"
            "      ]\n"
            "    }\n"
            "  }\n"
            "}\n"
        ),
        encoding="utf-8",
    )

    attach_lightweight_ledgers(gold_package, ledger_path=ledger_path)

    candidate_dir = tmp_path / "candidates"
    candidate_dir.mkdir()
    (candidate_dir / f"{case['case_id']}.txt").write_text(
        "전혀 다른 장면으로 시작한다.\n",
        encoding="utf-8",
    )

    result = run_gold_benchmark(gold_package, candidate_dir=candidate_dir, genre="investment")

    first = result["results"][0]
    assert first["manual_constraint_count"] >= 1
    assert result["average_manual_constraint_count"] >= 1.0
    assert any(finding["source"] == "manual_constraint" for finding in first["consistency_findings"])


def test_llm_consistency_judge_becomes_primary_axis(tmp_path: Path) -> None:
    title_dir = _build_title_dir(tmp_path)
    gold_package = build_gold_package(title_dir, title="benchmark_title", checkpoint_size=2, max_cases=1)
    case = gold_package["cases"][0]
    case["gold_ledger"] = {
        "protagonist": {"location": "서울 본사"},
        "alive_npcs": {"강민우": {"traits": "냉정", "role": "팀장"}},
    }

    candidate_dir = tmp_path / "candidates"
    candidate_dir.mkdir()
    (candidate_dir / f"{case['case_id']}.txt").write_text(
        "강민우를 본부장에서 갑자기 인턴으로 부르며, 정광은 부산 항만에 도착했다고 말했다.\n",
        encoding="utf-8",
    )

    def _fake_llm_ask(prompt: str) -> str:
        assert case["case_id"] in prompt
        return json.dumps(
            {
                "score": 61,
                "major_contradiction_count": 2,
                "findings": [
                    {
                        "severity": "CRITICAL",
                        "type": "location_jump",
                        "reason": "서울 본사 직후 설명 없이 부산 항만으로 이동했다.",
                        "evidence": "부산 항만에 도착",
                        "fix_suggestion": "이동 경위나 시간 경과를 먼저 제시하세요.",
                    },
                    {
                        "severity": "MAJOR",
                        "type": "role_reversal",
                        "reason": "강민우의 팀장 역할이 인턴으로 뒤집혔다.",
                        "evidence": "강민우를 본부장에서 갑자기 인턴으로",
                        "fix_suggestion": "기존 역할을 유지하거나 변경 근거를 제시하세요.",
                    },
                ],
                "summary": "prior-state contradiction detected",
            },
            ensure_ascii=False,
        )

    result = run_gold_benchmark(
        gold_package,
        candidate_dir=candidate_dir,
        genre="investment",
        consistency_llm_ask=_fake_llm_ask,
        consistency_judge_model="fake-judge",
    )

    first = result["results"][0]
    assert result["consistency_score_mode"] == "llm-judge"
    assert result["consistency_judge_model"] == "fake-judge"
    assert result["average_consistency_score"] == 61.0
    assert result["average_consistency_judge_score"] == 61.0
    assert first["consistency_score"] == 61.0
    assert first["consistency_score_mode"] == "llm-judge"
    assert first["consistency_judge_score"] == 61.0
    assert first["major_contradiction_count"] == 2
    assert any(finding["source"] == "llm_consistency_judge" for finding in first["consistency_findings"])
    assert len(first["consistency_supporting_findings"]) >= 0
