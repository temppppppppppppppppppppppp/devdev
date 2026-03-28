from __future__ import annotations

import json
from pathlib import Path

from scripts.gold_manuscript_benchmark_support import (
    build_case_prompt,
    build_gold_package,
    resolve_title_corpus,
    run_gold_benchmark,
)


def _write_episode(path: Path, episode: int, body: str) -> None:
    text = f"{episode}화. 테스트.\n\n{body}\n"
    path.write_text(text, encoding="utf-8")


def _build_direct_title_dir(tmp_path: Path) -> Path:
    title_dir = tmp_path / "재벌물_독식하는 재벌 3세"
    title_dir.mkdir(parents=True)
    for episode in range(1, 9):
        body = (
            f"주인공은 {episode}화에서도 태성그룹과 투자 계약을 정리했다. "
            f"박성호는 {episode}화 오프닝부터 긴장을 숨기지 못했다. "
            "계약, 투자, 후계, 시장, 압박이 다시 이어졌다. " * 20
        )
        _write_episode(title_dir / f"ep{episode:03d}.txt", episode, body)
    return title_dir


def test_resolve_title_corpus_accepts_direct_title_dir(tmp_path: Path) -> None:
    title_dir = _build_direct_title_dir(tmp_path)

    resolved = resolve_title_corpus(title_dir, title="독식하는 재벌 3세")

    assert resolved["title"] == "독식하는 재벌 3세"
    assert resolved["source_mode"] == "direct"
    assert len(resolved["episode_files"]) == 8


def test_resolve_title_corpus_accepts_manifest_root(tmp_path: Path) -> None:
    corpus_root = tmp_path / "corpus"
    title_dir = corpus_root / "titles" / "독식하는_재벌_3세"
    title_dir.mkdir(parents=True)
    _write_episode(title_dir / "0001.txt", 1, "회귀와 계약이 시작됐다. " * 30)
    _write_episode(title_dir / "0002.txt", 2, "후계 구도와 시장 압박이 이어졌다. " * 30)
    manifest = {
        "titles": [
            {
                "title": "독식하는 재벌 3세",
                "output_dir": str(title_dir),
                "written_episode_count": 2,
            }
        ]
    }
    (corpus_root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    resolved = resolve_title_corpus(corpus_root, title="독식하는 재벌 3세")

    assert resolved["title_dir"] == title_dir
    assert resolved["source_mode"] == "manifest"


def test_build_gold_package_emits_evenly_spaced_cases(tmp_path: Path) -> None:
    title_dir = _build_direct_title_dir(tmp_path)

    gold_package = build_gold_package(title_dir, title="독식하는 재벌 3세", checkpoint_size=2, max_cases=3)

    assert gold_package["mvp_type"] == "manuscript-only"
    assert gold_package["case_count"] == 3
    assert gold_package["cases"][0]["case_id"] == "ep001_002__to__ep003"
    assert gold_package["cases"][-1]["gold_continuation"]["ep_num"] == 8
    assert gold_package["cases"][0]["checkpoint"]["excerpt_strategy"] == "head_middle_tail_v1"


def test_run_gold_benchmark_self_check_scores_cases(tmp_path: Path) -> None:
    title_dir = _build_direct_title_dir(tmp_path)
    gold_package = build_gold_package(title_dir, title="독식하는 재벌 3세", checkpoint_size=2, max_cases=3)

    result = run_gold_benchmark(gold_package, use_gold_candidate=True, genre="investment")

    assert result["scored_case_count"] == 3
    assert result["missing_cases"] == []
    assert result["average_continuity_score"] > 0
    assert result["average_continuity_index"] == 100.0
    assert result["average_gold_fidelity_score"] >= 90
    assert result["average_writing_quality_score"] >= 45
    assert result["primary_score_axis"] == "continuity_index"
    assert result["consistency_primary_axis"] == "consistency_score"
    assert result["consistency_score_mode"] == "auto-only"
    assert result["score_profile"] == "continuity-gold-relative-v2"
    first = result["results"][0]
    assert first["continuity_index"] == 100.0
    assert first["gold_fidelity_axes"]["fulltext_similarity"] == 1.0
    assert first["gold_fidelity_axes"]["gold_opening_overlap"] == 1.0
    assert "continuity_score" in first
    assert "writing_quality_score" in first
    assert "consistency_score" in first
    assert "consistency_auto_score" in first
    assert "consistency_judge_score" in first
    assert "major_contradiction_count" in first
    assert "consistency_findings" in first


def test_build_case_prompt_mentions_title_and_next_episode(tmp_path: Path) -> None:
    title_dir = _build_direct_title_dir(tmp_path)
    gold_package = build_gold_package(title_dir, title="독식하는 재벌 3세", checkpoint_size=2, max_cases=1)
    case = gold_package["cases"][0]

    prompt = build_case_prompt(gold_package["title"], case)

    assert "독식하는 재벌 3세" in prompt
    assert f"제{case['gold_continuation']['ep_num']}화" in prompt
    assert "checkpoint excerpt start" in prompt
