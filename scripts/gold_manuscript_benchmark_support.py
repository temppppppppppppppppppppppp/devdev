from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from modules.validation.scoring_validator import ScoringValidator
from scripts.investment_corpus_support import (
    COMMON_GIVEN_NAMES,
    ORG_CANDIDATE_RE,
    ORG_STOPWORDS,
    PERSON_CANDIDATE_RE,
    PERSON_STOPWORDS,
    dump_json,
    slugify_title,
)

ROOT = Path(__file__).resolve().parents[1]
TXT_EPISODE_PATTERNS = (
    re.compile(r"^(?:ep)?(?P<episode>\d+)\.txt$", re.IGNORECASE),
    re.compile(r".*?(?P<episode>\d+)\uD654\.txt$", re.IGNORECASE),
    re.compile(r".*?[_ ](?P<episode>\d+)\.txt$", re.IGNORECASE),
)
TOKEN_RE = re.compile(r"[A-Za-z0-9가-힣]+")
NUMBER_ANCHOR_RE = re.compile(
    r"\d[\d,]*(?:\.\d+)?(?:\uC5B5|\uB9CC|\uCC9C|\uBC31|\uD37C\uC13C\uD2B8|%|\uB144|\uC6D4|\uC77C|\uB2EC\uB7EC|\uC6D0)?"
)
TOKEN_STOPWORDS = {
    "그리고",
    "그러나",
    "하지만",
    "그때",
    "지금",
    "이번",
    "다음",
    "이후",
    "정도",
    "하나",
    "그녀",
    "그는",
    "나는",
    "있다",
    "했다",
    "하게",
    "처럼",
    "에게",
    "에서",
    "으로",
    "했다",
    "이었다",
}


@dataclass(frozen=True)
class EpisodeText:
    ep_num: int
    path: Path
    text: str
    sha256: str


def now_iso() -> str:
    return datetime.now(UTC).astimezone().isoformat(timespec="seconds")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _parse_txt_episode_number(path: Path) -> int:
    for pattern in TXT_EPISODE_PATTERNS:
        match = pattern.match(path.name)
        if match:
            return int(match.group("episode"))
    msg = f"unsupported episode txt filename pattern: {path.name}"
    raise ValueError(msg)


def _list_episode_files(title_dir: Path) -> list[Path]:
    candidates: list[tuple[int, Path]] = []
    for path in title_dir.iterdir():
        if not path.is_file() or path.suffix.lower() != ".txt":
            continue
        try:
            ep_num = _parse_txt_episode_number(path)
        except ValueError:
            continue
        candidates.append((ep_num, path))
    return [path for _, path in sorted(candidates)]


def _load_manifest_title_dir(input_root: Path, title: str) -> Path | None:
    manifest_path = input_root / "manifest.json"
    if not manifest_path.exists():
        return None
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in payload.get("titles", []):
        if not isinstance(entry, dict):
            continue
        if entry.get("title") != title:
            continue
        output_dir = entry.get("output_dir")
        if output_dir:
            return Path(output_dir)
    return None


def _resolve_direct_title_dir(input_root: Path, title: str | None) -> Path:
    if _list_episode_files(input_root):
        return input_root

    if title:
        title_slug = slugify_title(title)
        for child in input_root.iterdir():
            if not child.is_dir():
                continue
            child_slug = slugify_title(child.name)
            if child.name == title or child.name.endswith(title) or child_slug == title_slug:
                if _list_episode_files(child):
                    return child

    txt_children = [child for child in input_root.iterdir() if child.is_dir() and _list_episode_files(child)]
    if len(txt_children) == 1:
        return txt_children[0]

    msg = f"unable to resolve title dir from input_root={input_root}"
    raise ValueError(msg)


def resolve_title_corpus(input_root: Path, *, title: str | None = None) -> dict[str, Any]:
    input_root = Path(input_root)
    manifest_title_dir = _load_manifest_title_dir(input_root, title) if title else None
    title_dir = manifest_title_dir or _resolve_direct_title_dir(input_root, title)
    effective_title = title
    if not effective_title:
        name = title_dir.name
        effective_title = name.split("_", 1)[1] if "_" in name else name
    episode_files = _list_episode_files(title_dir)
    if len(episode_files) < 2:
        msg = f"not enough episode txt files in {title_dir}"
        raise ValueError(msg)
    return {
        "title": effective_title,
        "title_dir": title_dir,
        "input_root": input_root,
        "source_mode": "manifest" if manifest_title_dir else "direct",
        "episode_files": episode_files,
    }


def _load_episodes(episode_files: list[Path]) -> list[EpisodeText]:
    episodes: list[EpisodeText] = []
    for path in episode_files:
        raw = path.read_bytes()
        text = raw.decode("utf-8").strip()
        episodes.append(
            EpisodeText(
                ep_num=_parse_txt_episode_number(path),
                path=path,
                text=text,
                sha256=_sha256_bytes(raw),
            )
        )
    return episodes


def _excerpt_head_middle_tail(text: str) -> str:
    if len(text) <= 1800:
        return text
    head = text[:800]
    tail = text[-500:]
    mid_start = 800
    mid_end = max(mid_start, len(text) - 500)
    mid_content = text[mid_start:mid_end]
    mid_point = len(mid_content) // 2
    anchor = mid_content[max(0, mid_point - 250) : mid_point + 250]
    return head + "\n...(중략)...\n" + anchor + "\n...(중략)...\n" + tail


def _relative_to_root(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _episode_ref(ep: EpisodeText) -> dict[str, Any]:
    return {
        "ep_num": ep.ep_num,
        "path": _relative_to_root(ep.path),
        "sha256": ep.sha256,
        "char_count": len(ep.text),
    }


def _pick_case_offsets(total_cases: int, max_cases: int) -> list[int]:
    if total_cases <= max_cases:
        return list(range(total_cases))
    if max_cases <= 1:
        return [total_cases - 1]
    offsets: list[int] = []
    last = total_cases - 1
    for slot in range(max_cases):
        offset = round(slot * last / (max_cases - 1))
        if offsets and offset <= offsets[-1]:
            offset = offsets[-1] + 1
        offsets.append(min(offset, last))
    return offsets


def build_gold_package(
    input_root: Path,
    *,
    title: str | None = None,
    checkpoint_size: int = 3,
    max_cases: int = 5,
) -> dict[str, Any]:
    resolved = resolve_title_corpus(input_root, title=title)
    episodes = _load_episodes(resolved["episode_files"])
    if checkpoint_size < 1:
        raise ValueError("checkpoint_size must be >= 1")
    if len(episodes) <= checkpoint_size:
        raise ValueError("episode count must exceed checkpoint_size")

    total_cases = len(episodes) - checkpoint_size
    offsets = _pick_case_offsets(total_cases, max_cases)
    cases: list[dict[str, Any]] = []
    for offset in offsets:
        gold_index = checkpoint_size + offset
        checkpoint_eps = episodes[gold_index - checkpoint_size : gold_index]
        gold_ep = episodes[gold_index]
        combined_excerpt = "\n\n---\n\n".join(
            f"[제{episode.ep_num}화]\n{_excerpt_head_middle_tail(episode.text)}" for episode in checkpoint_eps
        )
        tail_anchor = checkpoint_eps[-1].text[-700:]
        case_id = (
            f"ep{checkpoint_eps[0].ep_num:03d}_{checkpoint_eps[-1].ep_num:03d}"
            f"__to__ep{gold_ep.ep_num:03d}"
        )
        cases.append(
            {
                "case_id": case_id,
                "checkpoint": {
                    "episode_span": [checkpoint_eps[0].ep_num, checkpoint_eps[-1].ep_num],
                    "episode_numbers": [episode.ep_num for episode in checkpoint_eps],
                    "episode_refs": [_episode_ref(episode) for episode in checkpoint_eps],
                    "excerpt_strategy": "head_middle_tail_v1",
                    "combined_excerpt": combined_excerpt,
                    "tail_anchor_excerpt": tail_anchor,
                },
                "gold_continuation": {
                    "ep_num": gold_ep.ep_num,
                    "episode_ref": _episode_ref(gold_ep),
                    "opening_excerpt": gold_ep.text[:1200],
                },
                "gold_ledger": None,
            }
        )

    return {
        "generated_at": now_iso(),
        "mvp_type": "manuscript-only",
        "title": resolved["title"],
        "title_slug": slugify_title(resolved["title"]),
        "source_mode": resolved["source_mode"],
        "input_root": _relative_to_root(resolved["input_root"]),
        "title_dir": _relative_to_root(resolved["title_dir"]),
        "episode_count": len(episodes),
        "checkpoint_size": checkpoint_size,
        "case_count": len(cases),
        "cases": cases,
    }


def build_case_prompt(title: str, case: dict[str, Any]) -> str:
    checkpoint = case["checkpoint"]
    gold = case["gold_continuation"]
    start_ep, end_ep = checkpoint["episode_span"]
    next_ep = gold["ep_num"]
    return f"""너는 한국형 웹소설 장편 연속성 벤치용 writer다.

작품명: {title}
과제: 아래 checkpoint만 보고 바로 다음 화인 제{next_ep}화를 한국어 원고로 작성하라.

규칙:
- 이전 화들의 인물/관계/압박/진행 중인 문제를 opening에서 자연스럽게 이어라.
- 요약문, 해설문, 메타 설명, bullet, JSON 출력은 금지한다.
- 완결 요약이 아니라 실제 연재 원고처럼 서술한다.
- 지나친 설정 추가보다 checkpoint에 드러난 제약을 우선한다.
- 분량은 충분히 길게 작성하되, 장면 전개가 자연스럽게 이어지게 한다.

checkpoint 범위: 제{start_ep}화~제{end_ep}화
case_id: {case["case_id"]}

===== checkpoint excerpt start =====
{checkpoint["combined_excerpt"]}
===== checkpoint excerpt end =====

이제 제{next_ep}화 원고만 출력하라."""


def _normalize_tokens(text: str) -> list[str]:
    tokens = [match.group(0).lower() for match in TOKEN_RE.finditer(text)]
    return [token for token in tokens if len(token) > 1 and token not in TOKEN_STOPWORDS]


def _jaccard_similarity(left: str, right: str) -> float:
    left_tokens = set(_normalize_tokens(left))
    right_tokens = set(_normalize_tokens(right))
    if not left_tokens and not right_tokens:
        return 1.0
    if not left_tokens or not right_tokens:
        return 0.0
    union = left_tokens | right_tokens
    if not union:
        return 0.0
    return len(left_tokens & right_tokens) / len(union)


def _tail_anchor_recall(tail_anchor: str, candidate_opening: str, *, max_terms: int = 12) -> dict[str, Any]:
    tail_tokens = _normalize_tokens(tail_anchor)
    counts = Counter(tail_tokens)
    salient_terms = [token for token, _ in counts.most_common(max_terms)]
    if not salient_terms:
        return {"score": None, "terms": [], "matched_terms": [], "applicable": False}
    opening_tokens = set(_normalize_tokens(candidate_opening))
    matched_terms = [token for token in salient_terms if token in opening_tokens]
    return {
        "score": len(matched_terms) / len(salient_terms),
        "terms": salient_terms,
        "matched_terms": matched_terms,
        "applicable": True,
    }


def _intrinsic_quality(candidate_text: str, *, genre: str) -> dict[str, Any]:
    validator = ScoringValidator(client=None, genre=genre)
    context = {
        "mode": "MANUSCRIPT",
        "encyclopedia": {},
        "martial_hud": {},
        "blueprint": {},
        "history": [],
        "npc_profiles": {},
    }
    return validator.validate(candidate_text, context)


def _salient_term_recall(source_text: str, target_text: str, *, max_terms: int = 18) -> dict[str, Any]:
    counts = Counter(_normalize_tokens(source_text))
    salient_terms = [token for token, _ in counts.most_common(max_terms)]
    if not salient_terms:
        return {"score": None, "terms": [], "matched_terms": [], "applicable": False}
    target_tokens = set(_normalize_tokens(target_text))
    matched_terms = [token for token in salient_terms if token in target_tokens]
    return {
        "score": len(matched_terms) / len(salient_terms),
        "terms": salient_terms,
        "matched_terms": matched_terms,
        "applicable": True,
    }


def _extract_entities(text: str) -> dict[str, list[str]]:
    persons: list[str] = []
    organizations: list[str] = []

    for match in PERSON_CANDIDATE_RE.finditer(text):
        candidate = match.group("name").strip()
        if len(candidate) != 3:
            continue
        if candidate in PERSON_STOPWORDS:
            continue
        if candidate[1:] not in COMMON_GIVEN_NAMES:
            continue
        if candidate not in persons:
            persons.append(candidate)

    for match in ORG_CANDIDATE_RE.finditer(text):
        candidate = match.group("name").strip()
        if candidate in ORG_STOPWORDS:
            continue
        if candidate not in organizations:
            organizations.append(candidate)

    return {"persons": persons, "organizations": organizations}


def _entity_carryover_recall(source_text: str, target_text: str) -> dict[str, Any]:
    extracted = _extract_entities(source_text)
    expected = extracted["persons"] + extracted["organizations"]
    if not expected:
        return {"score": None, "expected": [], "matched": [], "applicable": False}
    matched = [entity for entity in expected if entity in target_text]
    return {
        "score": len(matched) / len(expected),
        "expected": expected,
        "matched": matched,
        "applicable": True,
    }


def _numeric_anchor_recall(source_text: str, target_text: str, *, max_values: int = 10) -> dict[str, Any]:
    expected = []
    for match in NUMBER_ANCHOR_RE.finditer(source_text):
        value = match.group(0).strip()
        if not value or value in expected:
            continue
        expected.append(value)
        if len(expected) >= max_values:
            break
    if not expected:
        return {"score": None, "expected": [], "matched": [], "applicable": False}
    matched = [value for value in expected if value in target_text]
    return {
        "score": len(matched) / len(expected),
        "expected": expected,
        "matched": matched,
        "applicable": True,
    }


def _weighted_average(weighted_scores: list[tuple[float, float | None]]) -> float:
    applicable = [(weight, score) for weight, score in weighted_scores if score is not None]
    total_weight = sum(weight for weight, _ in applicable)
    if total_weight <= 0:
        return 0.0
    return sum(weight * score for weight, score in applicable) / total_weight


def _average_metric(results: list[dict[str, Any]], key: str) -> float:
    values = [float(item[key]) for item in results if item.get(key) is not None]
    return round(sum(values) / len(values), 2) if values else 0.0


def _continuity_probe(case: dict[str, Any], target_text: str) -> dict[str, Any]:
    opening = target_text[:1200]
    prefix = target_text[:2200]
    tail_result = _tail_anchor_recall(case["checkpoint"]["tail_anchor_excerpt"], opening)
    checkpoint_term_result = _salient_term_recall(case["checkpoint"]["combined_excerpt"], prefix)
    entity_result = _entity_carryover_recall(case["checkpoint"]["tail_anchor_excerpt"], prefix)
    numeric_result = _numeric_anchor_recall(case["checkpoint"]["tail_anchor_excerpt"], prefix)
    continuity_score = 100.0 * _weighted_average(
        [
            (0.35, tail_result["score"]),
            (0.30, checkpoint_term_result["score"]),
            (0.20, entity_result["score"]),
            (0.15, numeric_result["score"]),
        ]
    )
    return {
        "opening": opening,
        "prefix": prefix,
        "score": continuity_score,
        "axes": {
            "tail_anchor_recall": round(tail_result["score"], 4) if tail_result["score"] is not None else None,
            "checkpoint_term_recall": (
                round(checkpoint_term_result["score"], 4) if checkpoint_term_result["score"] is not None else None
            ),
            "entity_carryover_recall": round(entity_result["score"], 4) if entity_result["score"] is not None else None,
            "numeric_anchor_recall": round(numeric_result["score"], 4) if numeric_result["score"] is not None else None,
        },
        "tail_result": tail_result,
        "checkpoint_term_result": checkpoint_term_result,
        "entity_result": entity_result,
        "numeric_result": numeric_result,
    }


def _gold_relative_index(candidate_score: float, gold_score: float) -> float | None:
    if gold_score > 0:
        return 100.0 * candidate_score / gold_score
    if candidate_score == 0:
        return 100.0
    return None


def score_case(case: dict[str, Any], candidate_text: str, *, genre: str = "investment") -> dict[str, Any]:
    gold_path = ROOT / case["gold_continuation"]["episode_ref"]["path"]
    gold_text = gold_path.read_text(encoding="utf-8").strip()
    candidate_probe = _continuity_probe(case, candidate_text)
    gold_probe = _continuity_probe(case, gold_text)
    candidate_opening = candidate_probe["opening"]
    gold_opening = gold_text[:1200]
    intrinsic = _intrinsic_quality(candidate_text, genre=genre)
    length_alignment = min(len(candidate_text), len(gold_text)) / max(len(candidate_text), len(gold_text))
    fulltext_similarity = SequenceMatcher(None, candidate_text[:4000], gold_text[:4000]).ratio()
    gold_opening_overlap = _jaccard_similarity(candidate_opening, gold_opening)
    intrinsic_percent = float(intrinsic.get("percentage", 0.0)) / 100.0
    continuity_score = candidate_probe["score"]
    gold_continuity_score = gold_probe["score"]
    continuity_index = _gold_relative_index(continuity_score, gold_continuity_score)
    gold_fidelity_score = 100.0 * _weighted_average(
        [
            (0.60, fulltext_similarity),
            (0.25, gold_opening_overlap),
            (0.15, length_alignment),
        ]
    )
    legacy_blended_auto_score = 100.0 * (
        (0.3 * fulltext_similarity)
        + (0.2 * gold_opening_overlap)
        + (0.2 * (candidate_probe["tail_result"]["score"] or 0.0))
        + (0.1 * length_alignment)
        + (0.2 * intrinsic_percent)
    )
    return {
        "case_id": case["case_id"],
        "gold_ep_num": case["gold_continuation"]["ep_num"],
        "candidate_char_count": len(candidate_text),
        "gold_char_count": len(gold_text),
        "continuity_score": round(continuity_score, 2),
        "gold_continuity_score": round(gold_continuity_score, 2),
        "continuity_index": round(continuity_index, 2) if continuity_index is not None else None,
        "continuity_delta_vs_gold": round(continuity_score - gold_continuity_score, 2),
        "gold_fidelity_score": round(gold_fidelity_score, 2),
        "writing_quality_score": round(intrinsic_percent * 100.0, 2),
        "legacy_blended_auto_score": round(legacy_blended_auto_score, 2),
        "auto_score": round(continuity_index, 2) if continuity_index is not None else None,
        "continuity_axes": candidate_probe["axes"],
        "gold_continuity_axes": gold_probe["axes"],
        "gold_fidelity_axes": {
            "fulltext_similarity": round(fulltext_similarity, 4),
            "gold_opening_overlap": round(gold_opening_overlap, 4),
            "length_alignment": round(length_alignment, 4),
        },
        "writing_quality_axes": {
            "intrinsic_quality_percent": round(intrinsic_percent, 4),
        },
        "tail_anchor_terms": candidate_probe["tail_result"]["terms"],
        "tail_anchor_matched_terms": candidate_probe["tail_result"]["matched_terms"],
        "checkpoint_terms": candidate_probe["checkpoint_term_result"]["terms"],
        "checkpoint_terms_matched": candidate_probe["checkpoint_term_result"]["matched_terms"],
        "tail_entities": candidate_probe["entity_result"]["expected"],
        "tail_entities_matched": candidate_probe["entity_result"]["matched"],
        "tail_numeric_anchors": candidate_probe["numeric_result"]["expected"],
        "tail_numeric_anchors_matched": candidate_probe["numeric_result"]["matched"],
        "intrinsic_quality": intrinsic,
    }


def run_gold_benchmark(
    gold_package: dict[str, Any],
    *,
    candidate_dir: Path | None = None,
    use_gold_candidate: bool = False,
    genre: str = "investment",
) -> dict[str, Any]:
    cases = gold_package.get("cases", [])
    results: list[dict[str, Any]] = []
    missing_cases: list[str] = []

    for case in cases:
        case_id = case["case_id"]
        if use_gold_candidate:
            candidate_path = ROOT / case["gold_continuation"]["episode_ref"]["path"]
        else:
            if candidate_dir is None:
                raise ValueError("candidate_dir is required unless use_gold_candidate=True")
            candidate_path = Path(candidate_dir) / f"{case_id}.txt"
            if not candidate_path.exists():
                missing_cases.append(case_id)
                continue
        candidate_text = candidate_path.read_text(encoding="utf-8").strip()
        result = score_case(case, candidate_text, genre=genre)
        result["candidate_path"] = _relative_to_root(candidate_path)
        result["candidate_sha256"] = _sha256_bytes(candidate_text.encode("utf-8"))
        results.append(result)

    average_continuity_score = _average_metric(results, "continuity_score")
    average_gold_continuity_score = _average_metric(results, "gold_continuity_score")
    average_continuity_index = _average_metric(results, "continuity_index")
    average_gold_fidelity_score = _average_metric(results, "gold_fidelity_score")
    average_writing_quality_score = _average_metric(results, "writing_quality_score")
    average_legacy_blended_auto_score = _average_metric(results, "legacy_blended_auto_score")
    return {
        "generated_at": now_iso(),
        "title": gold_package.get("title", ""),
        "title_slug": gold_package.get("title_slug", ""),
        "mvp_type": gold_package.get("mvp_type", "manuscript-only"),
        "score_profile": "continuity-gold-relative-v2",
        "primary_score_axis": "continuity_index",
        "score_axes": {
            "primary": "continuity_index",
            "secondary": [
                "continuity_score",
                "gold_continuity_score",
                "gold_fidelity_score",
                "writing_quality_score",
                "legacy_blended_auto_score",
            ],
        },
        "case_count": len(cases),
        "scored_case_count": len(results),
        "missing_cases": missing_cases,
        "use_gold_candidate": use_gold_candidate,
        "genre": genre,
        "average_continuity_index": average_continuity_index,
        "average_continuity_score": average_continuity_score,
        "average_gold_continuity_score": average_gold_continuity_score,
        "average_gold_fidelity_score": average_gold_fidelity_score,
        "average_writing_quality_score": average_writing_quality_score,
        "average_legacy_blended_auto_score": average_legacy_blended_auto_score,
        "average_auto_score": average_continuity_index,
        "results": results,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_json(payload) + "\n", encoding="utf-8")
