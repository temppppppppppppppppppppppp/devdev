from __future__ import annotations

# utf8-hygiene: allow-file -- legacy EPUB metadata regex patterns use literal ? quantifiers.

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone

UTC = timezone.utc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.investment_corpus_support import (  # noqa: E402
    extract_epub_text,
    parse_episode_number,
    select_ssot_dir,
)

DEFAULT_TITLE_DIR = Path(r"\\172.16.10.120\소설사업부\판무팀_ssot\02_연재\매지컬 써전(강산)")
DEFAULT_OUTPUT_ROOT = (
    ROOT
    / "material_ssot"
    / "10_research"
    / "50_corpus_curated"
    / "reference_samples"
    / "medical_magical_surgeon_sample_corpus"
)


@dataclass(slots=True)
class PlannedSample:
    episode: int
    epub_path: Path
    reason: str


@dataclass(slots=True)
class EpisodeSourceSelection:
    source_dir: Path
    rule: str
    epub_count: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a small representative sample corpus from a NAS EPUB title directory."
    )
    parser.add_argument(
        "--title-dir",
        default=str(DEFAULT_TITLE_DIR),
        help="Direct NAS title directory path such as \\\\server\\share\\title",
    )
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="Output directory for samples, manifest.json, and README.md",
    )
    parser.add_argument(
        "--sample-count",
        type=int,
        default=10,
        help="How many representative episodes to export",
    )
    parser.add_argument(
        "--min-later-episode",
        type=int,
        default=10,
        help="Lower bound for spread samples after opening anchors",
    )
    return parser.parse_args()


def decode_text_file(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp949", "euc-kr"):
        try:
            return raw.decode(encoding).replace("\r\n", "\n").replace("\r", "\n")
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore").replace("\r\n", "\n").replace("\r", "\n")


def find_bibliography_text(title_dir: Path) -> Path | None:
    manuscript_dir = title_dir / "1_원고"
    if not manuscript_dir.exists():
        return None
    candidates = sorted(manuscript_dir.rglob("*서지정보*.txt"))
    if candidates:
        return candidates[0]
    txt_candidates = sorted(manuscript_dir.rglob("*.txt"))
    return txt_candidates[0] if txt_candidates else None


def parse_bibliography(text: str) -> dict[str, object]:
    normalized = text.replace("\u2026", "...")
    lines = [line.strip() for line in normalized.splitlines()]
    compact_lines = [line for line in lines if line]

    def _search(pattern: str) -> str | None:
        match = re.search(pattern, normalized, re.IGNORECASE)
        return match.group(1).strip() if match else None

    title = _search(
        r"(?:제목|작품명)\s*[:：]\s*(.+)"
    )  # utf8-hygiene: allow-line rationale: regex uses literal ? quantifier.
    author = _search(
        r"(?:작가명|작가)\s*[:：]\s*(.+)"
    )  # utf8-hygiene: allow-line rationale: regex uses literal ? quantifier.
    isbn = _search(
        r"isbn\s*[:：]?\s*([0-9\-\/]+)"
    )  # utf8-hygiene: allow-line rationale: regex uses literal ? quantifier.
    total_episodes = _search(r"총\s*(\d+)\s*화")
    free_episodes = _search(r"무료\s*([0-9\-~()권화 ]+)")

    description_markers = ("작품 소개", "책소개", "소개글", "도서소개")
    description_lines: list[str] = []
    for index, line in enumerate(compact_lines):
        if any(marker in line for marker in description_markers):
            for candidate in compact_lines[index + 1 :]:
                if re.search(
                    r"(?:작가명|작가|isbn|무료|총\s*\d+\s*화|가격|출간일|상품번호)\s*[:：]?", candidate, re.IGNORECASE
                ):  # utf8-hygiene: allow-line rationale: regex uses literal ? quantifier.
                    break
                description_lines.append(candidate)
            break

    return {
        "title": title,
        "author": author,
        "isbn": isbn,
        "total_episodes": int(total_episodes) if total_episodes else None,
        "free_episodes": free_episodes,
        "description": " ".join(description_lines).strip() or None,
        "raw_excerpt": "\n".join(compact_lines[:12]),
    }


def count_epubs(path: Path) -> int:
    return sum(1 for item in path.rglob("*.epub") if item.is_file())


def resolve_episode_source_dir(selection_root: Path) -> EpisodeSourceSelection:
    direct_epubs = sorted(path for path in selection_root.glob("*.epub") if path.is_file())
    child_counts: list[tuple[Path, int]] = []
    for child in sorted(selection_root.iterdir()):
        if child.is_dir():
            count = count_epubs(child)
            if count > 0:
                child_counts.append((child, count))

    explicit_epub_candidates = [(child, count) for child, count in child_counts if child.name.lower() == "epub"]
    if explicit_epub_candidates:
        child, count = max(explicit_epub_candidates, key=lambda item: (item[1], -len(item[0].name)))
        return EpisodeSourceSelection(source_dir=child, rule="prefer-explicit-epub-subdir", epub_count=count)

    if direct_epubs:
        return EpisodeSourceSelection(
            source_dir=selection_root, rule="prefer-direct-epub-root", epub_count=len(direct_epubs)
        )

    if child_counts:
        child, count = max(child_counts, key=lambda item: (item[1], -len(item[0].name)))
        return EpisodeSourceSelection(
            source_dir=child, rule="prefer-largest-epub-subdir-within-selection", epub_count=count
        )

    raise ValueError(f"no epub-bearing source dir found under: {selection_root}")


def list_canonical_epubs(source_dir: Path) -> list[Path]:
    by_episode: dict[int, Path] = {}
    all_epubs = [path for path in source_dir.rglob("*.epub") if path.is_file()]
    ranked_epubs = sorted(
        all_epubs,
        key=lambda path: (
            parse_episode_number(path.name),
            len(path.relative_to(source_dir).parts),
            len(path.name),
            path.name,
        ),
    )
    for path in ranked_epubs:
        episode = parse_episode_number(path.name)
        by_episode.setdefault(episode, path)
    return [by_episode[episode] for episode in sorted(by_episode)]


def evenly_spaced_indices(pool_size: int, needed: int) -> list[int]:
    if needed <= 0 or pool_size <= 0:
        return []
    if needed >= pool_size:
        return list(range(pool_size))
    if needed == 1:
        return [pool_size - 1]

    raw = [round(index * (pool_size - 1) / (needed - 1)) for index in range(needed)]
    deduped: list[int] = []
    seen: set[int] = set()
    for index in raw:
        if index not in seen:
            deduped.append(index)
            seen.add(index)

    cursor = 0
    while len(deduped) < needed and cursor < pool_size:
        if cursor not in seen:
            deduped.append(cursor)
            seen.add(cursor)
        cursor += 1
    return sorted(deduped)[:needed]


def plan_samples(epubs: list[Path], sample_count: int, min_later_episode: int) -> list[PlannedSample]:
    episode_pairs = [(parse_episode_number(path.name), path) for path in epubs]
    if sample_count >= len(episode_pairs):
        return [PlannedSample(episode=episode, epub_path=path, reason="full-export") for episode, path in episode_pairs]

    episode_map = {episode: path for episode, path in episode_pairs}
    selected: list[PlannedSample] = []
    used: set[int] = set()

    for anchor in (1, 2, 3):
        path = episode_map.get(anchor)
        if path is None or anchor in used or len(selected) >= sample_count:
            continue
        selected.append(PlannedSample(episode=anchor, epub_path=path, reason="opening-anchor"))
        used.add(anchor)

    needed = sample_count - len(selected)
    later_pool = [
        (episode, path) for episode, path in episode_pairs if episode >= min_later_episode and episode not in used
    ]
    fallback_pool = [(episode, path) for episode, path in episode_pairs if episode not in used]
    pool = later_pool if len(later_pool) >= needed else fallback_pool

    for index in evenly_spaced_indices(len(pool), needed):
        episode, path = pool[index]
        if episode in used:
            continue
        selected.append(PlannedSample(episode=episode, epub_path=path, reason="spread-sample"))
        used.add(episode)

    if len(selected) < sample_count:
        for episode, path in fallback_pool:
            if episode in used:
                continue
            selected.append(PlannedSample(episode=episode, epub_path=path, reason="fill-gap"))
            used.add(episode)
            if len(selected) >= sample_count:
                break

    return sorted(selected, key=lambda item: item.episode)


def write_readme(output_root: Path, manifest: dict[str, object]) -> None:
    title = manifest["title"]
    lines = [
        f"# {title} Sample Corpus",
        "",
        f"- built_at: {manifest['generated_at']}",
        f"- source_title_dir: `{manifest['source_title_dir']}`",
        f"- ssot_dir: `{manifest['ssot_dir']}`",
        f"- ssot_rule: `{manifest['ssot_rule']}`",
        f"- total_ssot_epubs: {manifest['total_ssot_epubs']}",
        f"- current_episode_span: {manifest['current_episode_min']}..{manifest['current_episode_max']}",
        f"- sample_count: {manifest['sample_count']}",
        f"- sample_strategy: `{manifest['sample_strategy']}`",
        "",
        "## Bibliography",
        "",
        f"- author: {manifest['bibliography'].get('author') or 'unknown'}",
        f"- isbn: {manifest['bibliography'].get('isbn') or 'unknown'}",
        f"- total_episodes: {manifest['bibliography'].get('total_episodes') or 'unknown'}",
        f"- free_episodes: {manifest['bibliography'].get('free_episodes') or 'unknown'}",
        f"- description: {manifest['bibliography'].get('description') or 'n/a'}",
        "",
        "## Sample Episodes",
        "",
    ]
    if manifest.get("episode_count_mismatch_note"):
        lines.insert(
            len(lines) - 3,
            f"- note: {manifest['episode_count_mismatch_note']}",
        )
    for sample in manifest["samples"]:
        lines.append(
            f"- ep{sample['episode']:04d}: `{sample['output_file']}` ({sample['reason']}, {sample['char_count']} chars)"
        )
    lines.append("")
    lines.append(
        "This corpus is a first-pass medical reference pack built from the direct NAS medical title found in the 02_연재 slice."
    )
    (output_root / "README.md").write_text("\n".join(lines), encoding="utf-8")


def clear_stale_sample_exports(samples_dir: Path, planned_samples: list[PlannedSample]) -> None:
    expected = {f"ep{sample.episode:04d}.txt" for sample in planned_samples}
    for stale_file in samples_dir.glob("ep*.txt"):
        if stale_file.name not in expected:
            stale_file.unlink()


def main() -> int:
    args = parse_args()
    title_dir = Path(args.title_dir)
    output_root = Path(args.output_root)
    sample_count = max(args.sample_count, 1)

    if not title_dir.exists():
        raise SystemExit(f"missing title_dir: {title_dir}")

    selection = select_ssot_dir(title_dir.name, title_dir)
    episode_source = resolve_episode_source_dir(selection.source_path)
    epubs = list_canonical_epubs(episode_source.source_dir)
    if not epubs:
        raise SystemExit(f"no epubs found under selected SSOT dir: {episode_source.source_dir}")

    planned_samples = plan_samples(epubs, sample_count=sample_count, min_later_episode=max(args.min_later_episode, 1))
    episode_numbers = [parse_episode_number(path.name) for path in epubs]

    output_root.mkdir(parents=True, exist_ok=True)
    samples_dir = output_root / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)
    clear_stale_sample_exports(samples_dir, planned_samples)

    bibliography_path = find_bibliography_text(title_dir)
    bibliography_text = decode_text_file(bibliography_path) if bibliography_path else ""
    bibliography = parse_bibliography(bibliography_text) if bibliography_text else {}
    bibliography_total = bibliography.get("total_episodes")
    mismatch_note = None
    if isinstance(bibliography_total, int) and bibliography_total != episode_numbers[-1]:
        mismatch_note = f"bibliography says total {bibliography_total} episodes, but current canonical EPUB set runs to {episode_numbers[-1]} episodes"

    sample_entries: list[dict[str, object]] = []
    for planned in planned_samples:
        episode = extract_epub_text(planned.epub_path)
        output_file = samples_dir / f"ep{planned.episode:04d}.txt"
        output_file.write_text(episode.text, encoding="utf-8")
        sample_entries.append(
            {
                "episode": planned.episode,
                "reason": planned.reason,
                "source_epub": str(planned.epub_path),
                "source_epub_name": planned.epub_path.name,
                "output_file": str(output_file.relative_to(output_root)).replace("\\", "/"),
                "char_count": len(episode.text),
                "line_count": episode.text.count("\n") + 1,
                "text_hash": episode.text_hash,
                "content_entries": episode.content_entries,
                "skipped_entries": episode.skipped_entries,
            }
        )

    manifest = {
        "generated_at": datetime.now(UTC).isoformat(),
        "title": bibliography.get("title") or title_dir.name,
        "title_dir_name": title_dir.name,
        "source_title_dir": str(title_dir),
        "ssot_dir": str(selection.source_path),
        "ssot_rule": selection.rule,
        "episode_source_dir": str(episode_source.source_dir),
        "episode_source_rule": episode_source.rule,
        "total_ssot_epubs": len(epubs),
        "current_episode_min": episode_numbers[0],
        "current_episode_max": episode_numbers[-1],
        "episode_count_mismatch_note": mismatch_note,
        "sample_count": len(sample_entries),
        "sample_strategy": f"opening-anchor(1,2,3)+spread(min_later_episode={max(args.min_later_episode, 1)})",
        "bibliography_source": str(bibliography_path) if bibliography_path else None,
        "bibliography": bibliography,
        "samples": sample_entries,
    }

    (output_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_readme(output_root, manifest)
    print(json.dumps({"output_root": str(output_root), "sample_count": len(sample_entries)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
