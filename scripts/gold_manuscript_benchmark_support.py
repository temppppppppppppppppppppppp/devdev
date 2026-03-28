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

from modules.core.truth_gate import TruthGate
from modules.validation.continuity_validator import ContinuityValidator
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
MAJOR_CONTRADICTION_SEVERITIES = {"BLOCKING", "CRITICAL", "MAJOR"}
CONSISTENCY_SEVERITY_PENALTIES = {
    "BLOCKING": 28.0,
    "CRITICAL": 24.0,
    "MAJOR": 15.0,
    "MEDIUM": 9.0,
    "WARNING": 6.0,
    "INFO": 3.0,
    "MINOR": 3.0,
}
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


def attach_lightweight_ledgers(
    gold_package: dict[str, Any],
    *,
    ledger_path: Path | None = None,
) -> dict[str, Any]:
    package_cases = gold_package.get("cases", [])
    if not package_cases:
        return gold_package

    if ledger_path is None:
        title_slug = gold_package.get("title_slug")
        if not title_slug:
            return gold_package
        ledger_path = ROOT / "data" / "gold_manuscript_benchmark" / title_slug / "gold_ledger_light.json"

    ledger_path = Path(ledger_path)
    if not ledger_path.exists():
        return gold_package

    ledger_payload = json.loads(ledger_path.read_text(encoding="utf-8"))
    case_ledgers = ledger_payload.get("cases", {})
    if not isinstance(case_ledgers, dict):
        return gold_package

    by_case_id = {str(case_id): ledger for case_id, ledger in case_ledgers.items() if isinstance(ledger, dict)}
    applied = 0
    for case in package_cases:
        case_id = case.get("case_id")
        if case_id not in by_case_id:
            continue
        case["gold_ledger"] = by_case_id[case_id]
        applied += 1

    gold_package["gold_ledger_source"] = _relative_to_root(ledger_path)
    gold_package["gold_ledger_case_count"] = applied
    return gold_package


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


def _read_episode_ref(episode_ref: dict[str, Any]) -> str:
    path = ROOT / episode_ref["path"]
    return path.read_text(encoding="utf-8").strip()


def _ledger_lookup(ledger: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in ledger:
            return ledger[key]
    return None


def _dedupe_strings(values: list[str]) -> list[str]:
    deduped: list[str] = []
    for value in values:
        item = str(value or "").strip()
        if item and item not in deduped:
            deduped.append(item)
    return deduped


def _coerce_named_values(raw: Any, *, name_keys: tuple[str, ...] = ("name", "text", "law", "location", "item")) -> list[str]:
    values: list[str] = []
    if isinstance(raw, str):
        values.append(raw)
    elif isinstance(raw, list):
        for item in raw:
            if isinstance(item, str):
                values.append(item)
                continue
            if isinstance(item, dict):
                for key in name_keys:
                    candidate = item.get(key)
                    if isinstance(candidate, str) and candidate.strip():
                        values.append(candidate)
                        break
    elif isinstance(raw, dict):
        for key, value in raw.items():
            if isinstance(value, dict):
                for candidate_key in name_keys:
                    candidate = value.get(candidate_key)
                    if isinstance(candidate, str) and candidate.strip():
                        values.append(candidate)
                        break
                else:
                    values.append(str(key))
                continue
            if isinstance(value, str) and value.strip():
                values.append(value)
                continue
            values.append(str(key))
    return _dedupe_strings(values)


def _case_gold_ledger(case: dict[str, Any]) -> dict[str, Any]:
    ledger = case.get("gold_ledger")
    return ledger if isinstance(ledger, dict) else {}


def _build_prev_hud(case: dict[str, Any]) -> dict[str, Any]:
    ledger = _case_gold_ledger(case)
    protagonist = ledger.get("protagonist")
    protagonist = protagonist if isinstance(protagonist, dict) else {}

    actual_truth: dict[str, Any] = {}
    location = protagonist.get("location") or _ledger_lookup(ledger, "location", "protagonist_location")
    condition = protagonist.get("condition") or _ledger_lookup(ledger, "condition", "protagonist_condition")
    inventory_counts = protagonist.get("inventory_counts") or _ledger_lookup(ledger, "inventory_counts")
    equipment = protagonist.get("equipment")
    if equipment is None:
        equipment = _ledger_lookup(ledger, "active_items", "items")
    active_pressure_vectors = protagonist.get("active_pressure_vectors")
    if active_pressure_vectors is None:
        active_pressure_vectors = _ledger_lookup(ledger, "active_pressure_vectors", "active_pressure")

    if isinstance(location, str) and location.strip():
        actual_truth["location"] = location.strip()
    if isinstance(condition, str) and condition.strip():
        actual_truth["condition"] = condition.strip()
    if inventory_counts:
        actual_truth["inventory_counts"] = inventory_counts
    equipment_names = _coerce_named_values(equipment)
    if equipment_names:
        actual_truth["equipment"] = equipment_names
    if isinstance(active_pressure_vectors, list) and active_pressure_vectors:
        actual_truth["active_pressure_vectors"] = active_pressure_vectors

    prev_hud = {"actual_truth": actual_truth}
    if not actual_truth:
        prev_hud["benchmark_fallback"] = True
    return prev_hud


def _extract_npc_personalities(ledger: dict[str, Any]) -> dict[str, dict[str, str]]:
    personalities: dict[str, dict[str, str]] = {}
    for source in (_ledger_lookup(ledger, "alive_npcs"), _ledger_lookup(ledger, "npc_registry")):
        if not isinstance(source, dict):
            continue
        for name, info in source.items():
            if not isinstance(info, dict):
                continue
            traits = info.get("traits") or info.get("personality") or info.get("personality_traits")
            if isinstance(traits, str) and traits.strip():
                personalities[str(name)] = {"traits": traits.strip()}
    return personalities


def _build_validation_context(case: dict[str, Any], *, genre: str) -> dict[str, Any]:
    ledger = _case_gold_ledger(case)
    validation_context: dict[str, Any] = {
        "genre": genre,
        "prev_hud": _build_prev_hud(case),
        "prev_full_text": _read_episode_ref(case["checkpoint"]["episode_refs"][-1]),
    }

    npc_personalities = _extract_npc_personalities(ledger)
    if npc_personalities:
        validation_context["npc_personalities"] = npc_personalities

    npc_history = _ledger_lookup(ledger, "npc_history")
    if isinstance(npc_history, dict) and npc_history:
        validation_context["npc_history"] = npc_history

    time_warnings = _ledger_lookup(ledger, "time_warnings")
    if isinstance(time_warnings, list) and time_warnings:
        validation_context["time_warnings"] = time_warnings

    arc_pos = _ledger_lookup(ledger, "arc_pos")
    if isinstance(arc_pos, int):
        validation_context["arc_pos"] = arc_pos

    return validation_context


class _BenchmarkWorldState:
    def __init__(self, ledger: dict[str, Any]) -> None:
        self._deceased_npcs = _coerce_named_values(
            _ledger_lookup(ledger, "dead_npcs", "deceased_npcs", "deceased"),
        )
        self._destroyed_locations = _coerce_named_values(
            _ledger_lookup(ledger, "destroyed_locations", "destroyed"),
        )
        self._owned_items = _coerce_named_values(_ledger_lookup(ledger, "active_items", "items"))
        self._known_skills = _coerce_named_values(_ledger_lookup(ledger, "skills", "known_skills"))
        self._world_laws = _coerce_named_values(_ledger_lookup(ledger, "world_laws"), name_keys=("law", "text", "name"))

        self._npc_role_snapshot: dict[str, dict[str, Any]] = {}
        alive_npcs = _ledger_lookup(ledger, "alive_npcs", "npc_registry")
        if isinstance(alive_npcs, dict):
            for name, info in alive_npcs.items():
                if not isinstance(info, dict):
                    continue
                role_at_intro = str(info.get("role_at_intro") or info.get("role") or "").strip()
                known_attrs: dict[str, dict[str, Any]] = {}
                for field_name in ("relation", "location", "personality", "traits"):
                    value = info.get(field_name)
                    if isinstance(value, str) and value.strip():
                        normalized_field = "personality_traits" if field_name in {"personality", "traits"} else field_name
                        known_attrs[normalized_field] = {"value": value.strip()}
                if role_at_intro or known_attrs:
                    self._npc_role_snapshot[str(name)] = {
                        "role_at_intro": role_at_intro,
                        "first_seen_ep": int(info.get("first_seen_ep", 0) or 0),
                        "known_attrs": known_attrs,
                    }

    def get_deceased_npcs(self) -> list[str]:
        return list(self._deceased_npcs)

    def get_owned_items(self) -> list[str]:
        return list(self._owned_items)

    def get_destroyed_locations(self) -> list[str]:
        return list(self._destroyed_locations)

    def get_known_skills(self) -> list[str]:
        return list(self._known_skills)

    def get_world_laws(self) -> list[str]:
        return list(self._world_laws)

    def get_npc_role_snapshot(self) -> dict[str, dict[str, Any]]:
        return dict(self._npc_role_snapshot)


def _build_npc_registry(ledger: dict[str, Any]) -> dict[str, Any] | None:
    registry: dict[str, Any] = {}
    alive_npcs = _ledger_lookup(ledger, "alive_npcs", "npc_registry")
    if isinstance(alive_npcs, dict):
        for name, info in alive_npcs.items():
            if isinstance(info, dict):
                registry[str(name)] = dict(info)
            else:
                registry[str(name)] = {}
            registry[str(name)].setdefault("status", "alive")

    deceased_names = _coerce_named_values(_ledger_lookup(ledger, "dead_npcs", "deceased_npcs", "deceased"))
    for name in deceased_names:
        entry = registry.setdefault(name, {})
        entry["status"] = "dead"

    return registry or None


def _normalize_issue_entries(
    entries: list[Any],
    *,
    source: str,
    bucket: str,
    default_severity: str = "WARNING",
    skip_types: set[str] | None = None,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    blocked_types = skip_types or set()
    for entry in entries or []:
        payload = dict(entry) if isinstance(entry, dict) else {"reason": str(entry)}
        issue_type = str(payload.get("type", "") or "").strip()
        if issue_type in blocked_types:
            continue
        severity = str(payload.get("severity", default_severity) or default_severity).upper()
        reason = str(payload.get("reason") or payload.get("text") or payload.get("description") or "").strip()
        if not reason:
            reason = str(entry)
        if severity == "WARNING" and "contradiction" in reason.lower():
            severity = "MAJOR"
        normalized.append(
            {
                **payload,
                "source": source,
                "bucket": bucket,
                "type": issue_type,
                "severity": severity,
                "reason": reason,
            }
        )
    return normalized


def _issue_penalty(issue: dict[str, Any]) -> float:
    severity = str(issue.get("severity", "WARNING") or "WARNING").upper()
    penalty = CONSISTENCY_SEVERITY_PENALTIES.get(severity, CONSISTENCY_SEVERITY_PENALTIES["WARNING"])
    if issue.get("bucket") == "warning":
        return max(2.0, round(penalty * 0.5, 2))
    return penalty


def _consistency_coverage_fields(case: dict[str, Any], validation_context: dict[str, Any]) -> list[str]:
    coverage = ["prev_full_text"]
    prev_hud = validation_context.get("prev_hud")
    if isinstance(prev_hud, dict) and prev_hud.get("actual_truth"):
        coverage.append("prev_hud")

    ledger = _case_gold_ledger(case)
    if ledger:
        coverage.append("gold_ledger")
        if _build_npc_registry(ledger):
            coverage.append("npc_registry")
        if _extract_npc_personalities(ledger):
            coverage.append("npc_personalities")
        if _coerce_named_values(_ledger_lookup(ledger, "dead_npcs", "deceased_npcs", "deceased")):
            coverage.append("dead_npcs")
        if _coerce_named_values(_ledger_lookup(ledger, "destroyed_locations", "destroyed")):
            coverage.append("destroyed_locations")

    return coverage


def _constraint_scope_text(target_text: str, scope: str) -> str:
    if scope == "opening":
        return target_text[:1200]
    if scope == "prefix":
        return target_text[:2200]
    return target_text


def _manual_constraint_probe(ledger: dict[str, Any], target_text: str) -> list[dict[str, Any]]:
    constraints = ledger.get("manual_constraints")
    if not isinstance(constraints, list):
        return []

    findings: list[dict[str, Any]] = []
    for raw in constraints:
        if not isinstance(raw, dict):
            continue

        constraint_type = str(raw.get("type", "") or "").strip()
        scope = str(raw.get("scope", "opening") or "opening").strip()
        scope_text = _constraint_scope_text(target_text, scope)
        lowered_scope = scope_text.lower()
        terms = [str(term).strip() for term in raw.get("terms", []) if str(term).strip()]
        allow_terms = [str(term).strip() for term in raw.get("allow_if_any_terms", []) if str(term).strip()]
        severity = str(raw.get("severity", "WARNING") or "WARNING").upper()
        constraint_id = str(raw.get("id", constraint_type) or constraint_type)
        label = str(raw.get("label", constraint_id) or constraint_id)

        if allow_terms and any(term.lower() in lowered_scope for term in allow_terms):
            continue

        if constraint_type == "require_any_terms":
            matched_terms = [term for term in terms if term.lower() in lowered_scope]
            min_matches = int(raw.get("min_matches", 1) or 1)
            if len(matched_terms) >= min_matches:
                continue
            findings.append(
                {
                    "type": "manual_constraint_missing_terms",
                    "severity": severity,
                    "bucket": "warning",
                    "source": "manual_constraint",
                    "constraint_id": constraint_id,
                    "label": label,
                    "matched_terms": matched_terms,
                    "expected_terms": terms,
                    "reason": str(raw.get("reason") or f"expected opening carry-over missing: {label}"),
                    "fix_suggestion": str(
                        raw.get("fix_suggestion")
                        or "opening 초반에 직전 화의 핵심 제약/장면/인물을 다시 연결하세요."
                    ),
                }
            )
            continue

        if constraint_type == "forbid_any_terms":
            matched_terms = [term for term in terms if term.lower() in lowered_scope]
            if not matched_terms:
                continue
            findings.append(
                {
                    "type": "manual_constraint_forbidden_terms",
                    "severity": severity,
                    "bucket": "violation",
                    "source": "manual_constraint",
                    "constraint_id": constraint_id,
                    "label": label,
                    "matched_terms": matched_terms,
                    "reason": str(raw.get("reason") or f"forbidden contradiction trigger: {label}"),
                    "fix_suggestion": str(
                        raw.get("fix_suggestion")
                        or "checkpoint에서 확정되지 않은 상태 변화나 모순되는 표현을 제거하세요."
                    ),
                }
            )

    return findings


def _extract_json_payload(raw_text: str) -> dict[str, Any] | None:
    text = str(raw_text or "").strip()
    if not text:
        return None

    fenced = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()
    else:
        fenced = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
        if fenced:
            text = fenced.group(1).strip()

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end < start:
            return None
        try:
            payload = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None

    return payload if isinstance(payload, dict) else None


def _build_consistency_judge_prompt(case: dict[str, Any], target_text: str, *, genre: str) -> str:
    ledger = _case_gold_ledger(case)
    checkpoint = case["checkpoint"]
    checkpoint_excerpt = checkpoint["combined_excerpt"][:6000]
    tail_anchor = checkpoint["tail_anchor_excerpt"][:1200]
    ledger_excerpt = dump_json(ledger) if ledger else "{}"
    candidate_excerpt = target_text[:7000]
    return f"""너는 장편 서사 benchmark의 contradiction-first continuity judge다.

목표:
- gold continuation과의 유사도는 보지 말 것
- 오직 checkpoint / 직전 상태 / optional ledger 기준으로
  후보 원고가 이전 내용과 모순되거나, 직전 제약을 말도 안 되게 깨는지 판정할 것

장르: {genre}
case_id: {case["case_id"]}
다음 화 번호: {case["gold_continuation"]["ep_num"]}

판정 원칙:
- direct contradiction, impossible state shift, dead/alive reversal, location jump,
  relationship/role reversal, item/state inconsistency는 강하게 감점
- immediate active pressure를 아무 설명 없이 무시해 opening plausibility를 깨면 감점 가능
- 단순히 gold와 다른 전개라는 이유만으로 감점 금지
- checkpoint와 양립 가능한 새로운 전개는 허용
- 애매하면 MAJOR 대신 WARNING을 사용

반드시 JSON만 반환:
{{
  "score": 0-100,
  "major_contradiction_count": 0,
  "findings": [
    {{
      "severity": "CRITICAL|MAJOR|WARNING|INFO",
      "type": "short_snake_case",
      "reason": "why this contradicts prior state",
      "evidence": "short quote or cue from candidate/checkpoint",
      "fix_suggestion": "brief fix"
    }}
  ],
  "summary": "one-line verdict"
}}

===== checkpoint excerpt start =====
{checkpoint_excerpt}
===== checkpoint excerpt end =====

===== tail anchor start =====
{tail_anchor}
===== tail anchor end =====

===== optional gold ledger start =====
{ledger_excerpt}
===== optional gold ledger end =====

===== candidate manuscript start =====
{candidate_excerpt}
===== candidate manuscript end =====
"""


def _llm_consistency_probe(
    case: dict[str, Any],
    target_text: str,
    *,
    genre: str,
    consistency_llm_ask: Any,
) -> dict[str, Any] | None:
    if consistency_llm_ask is None:
        return None

    prompt = _build_consistency_judge_prompt(case, target_text, genre=genre)
    raw_response = consistency_llm_ask(prompt)
    payload = _extract_json_payload(raw_response)
    if not payload:
        return {
            "score": None,
            "major_contradiction_count": 0,
            "findings": [],
            "summary": "llm judge parse failed",
            "raw_response": str(raw_response or "")[:2000],
            "judge_error": "invalid_json",
        }

    findings_raw = payload.get("findings", [])
    findings = _normalize_issue_entries(
        findings_raw if isinstance(findings_raw, list) else [],
        source="llm_consistency_judge",
        bucket="violation",
        default_severity="WARNING",
    )
    try:
        score = float(payload.get("score"))
    except (TypeError, ValueError):
        score = None
    if score is not None:
        score = max(0.0, min(100.0, score))

    try:
        major_contradiction_count = int(payload.get("major_contradiction_count", 0) or 0)
    except (TypeError, ValueError):
        major_contradiction_count = sum(
            1 for finding in findings if str(finding.get("severity", "")).upper() in MAJOR_CONTRADICTION_SEVERITIES
        )

    return {
        "score": score,
        "major_contradiction_count": major_contradiction_count,
        "findings": findings,
        "summary": str(payload.get("summary", "") or "").strip(),
        "raw_response": str(raw_response or "")[:2000],
        "judge_error": None,
    }


def _consistency_probe(case: dict[str, Any], target_text: str, *, genre: str) -> dict[str, Any]:
    validation_context = _build_validation_context(case, genre=genre)
    continuity_result = ContinuityValidator(context=None).validate(
        current_ep=int(case["gold_continuation"]["ep_num"]),
        manuscript=target_text,
        validation_context=validation_context,
        prev_hud=validation_context.get("prev_hud"),
    )

    ledger = _case_gold_ledger(case)
    truth_result = TruthGate(
        world_state=_BenchmarkWorldState(ledger),
        fact_ledger=ledger or None,
        llm_ask=None,
    ).validate(
        target_text,
        state_updates={},
        npc_registry=_build_npc_registry(ledger),
    )

    continuity_violations = _normalize_issue_entries(
        continuity_result.get("violations", []),
        source="continuity_validator",
        bucket="violation",
        default_severity="WARNING",
    )
    continuity_warnings = _normalize_issue_entries(
        continuity_result.get("warnings", []),
        source="continuity_validator",
        bucket="warning",
        default_severity="WARNING",
        skip_types={"threat_carryover_drift"},
    )
    truth_warnings = _normalize_issue_entries(
        truth_result.get("structured_warnings", []),
        source="truth_gate",
        bucket="warning",
        default_severity="WARNING",
    )
    manual_constraint_findings = _normalize_issue_entries(
        _manual_constraint_probe(ledger, target_text),
        source="manual_constraint",
        bucket="warning",
        default_severity="WARNING",
    )

    all_issues = continuity_violations + continuity_warnings + truth_warnings + manual_constraint_findings
    total_penalty = min(100.0, sum(_issue_penalty(issue) for issue in all_issues))
    major_contradiction_count = sum(
        1 for issue in all_issues if str(issue.get("severity", "")).upper() in MAJOR_CONTRADICTION_SEVERITIES
    )

    return {
        "score": max(0.0, 100.0 - total_penalty),
        "penalty": round(total_penalty, 2),
        "continuity_violations": continuity_violations,
        "continuity_warnings": continuity_warnings,
        "truth_warnings": truth_warnings,
        "manual_constraint_findings": manual_constraint_findings,
        "coverage_fields": _consistency_coverage_fields(case, validation_context),
        "source_mode": "lightweight-ledger" if ledger else "checkpoint-only",
        "major_contradiction_count": major_contradiction_count,
        "continuity_violation_count": len(continuity_violations),
        "continuity_warning_count": len(continuity_warnings),
        "truth_warning_count": len(truth_warnings),
        "manual_constraint_count": len(manual_constraint_findings),
    }


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


def score_case(
    case: dict[str, Any],
    candidate_text: str,
    *,
    genre: str = "investment",
    consistency_llm_ask: Any = None,
    consistency_judge_model: str | None = None,
) -> dict[str, Any]:
    gold_text = _read_episode_ref(case["gold_continuation"]["episode_ref"])
    candidate_probe = _continuity_probe(case, candidate_text)
    gold_probe = _continuity_probe(case, gold_text)
    consistency_auto_probe = _consistency_probe(case, candidate_text, genre=genre)
    consistency_llm_probe = _llm_consistency_probe(
        case,
        candidate_text,
        genre=genre,
        consistency_llm_ask=consistency_llm_ask,
    )
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
    auto_consistency_score = round(consistency_auto_probe["score"], 2)
    llm_consistency_score = (
        round(consistency_llm_probe["score"], 2)
        if consistency_llm_probe and consistency_llm_probe.get("score") is not None
        else None
    )
    primary_consistency_score = llm_consistency_score if llm_consistency_score is not None else auto_consistency_score
    primary_consistency_findings = (
        consistency_llm_probe["findings"]
        if consistency_llm_probe and llm_consistency_score is not None
        else (
            consistency_auto_probe["continuity_violations"]
            + consistency_auto_probe["continuity_warnings"]
            + consistency_auto_probe["truth_warnings"]
            + consistency_auto_probe["manual_constraint_findings"]
        )
    )
    primary_major_contradiction_count = (
        consistency_llm_probe["major_contradiction_count"]
        if consistency_llm_probe and llm_consistency_score is not None
        else consistency_auto_probe["major_contradiction_count"]
    )
    consistency_score_mode = "llm-judge" if llm_consistency_score is not None else "auto-only"
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
        "consistency_score": primary_consistency_score,
        "consistency_score_mode": consistency_score_mode,
        "consistency_auto_score": auto_consistency_score,
        "consistency_judge_score": llm_consistency_score,
        "consistency_judge_model": consistency_judge_model,
        "consistency_judge_summary": (
            consistency_llm_probe["summary"]
            if consistency_llm_probe and consistency_llm_probe.get("summary")
            else None
        ),
        "consistency_penalty": consistency_auto_probe["penalty"],
        "consistency_source_mode": consistency_auto_probe["source_mode"],
        "continuity_violation_count": consistency_auto_probe["continuity_violation_count"],
        "continuity_warning_count": consistency_auto_probe["continuity_warning_count"],
        "truth_warning_count": consistency_auto_probe["truth_warning_count"],
        "manual_constraint_count": consistency_auto_probe["manual_constraint_count"],
        "major_contradiction_count": primary_major_contradiction_count,
        "continuity_axes": candidate_probe["axes"],
        "consistency_axes": {
            "mode": consistency_score_mode,
            "penalty": consistency_auto_probe["penalty"],
            "source_mode": consistency_auto_probe["source_mode"],
            "coverage_fields": consistency_auto_probe["coverage_fields"],
            "continuity_violation_count": consistency_auto_probe["continuity_violation_count"],
            "continuity_warning_count": consistency_auto_probe["continuity_warning_count"],
            "truth_warning_count": consistency_auto_probe["truth_warning_count"],
            "manual_constraint_count": consistency_auto_probe["manual_constraint_count"],
            "major_contradiction_count": primary_major_contradiction_count,
            "consistency_auto_score": auto_consistency_score,
            "consistency_judge_score": llm_consistency_score,
            "consistency_judge_model": consistency_judge_model,
        },
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
        "consistency_findings": primary_consistency_findings,
        "consistency_supporting_findings": (
            consistency_auto_probe["continuity_violations"]
            + consistency_auto_probe["continuity_warnings"]
            + consistency_auto_probe["truth_warnings"]
            + consistency_auto_probe["manual_constraint_findings"]
        ),
        "consistency_judge_raw_response": (
            consistency_llm_probe["raw_response"] if consistency_llm_probe else None
        ),
        "consistency_judge_error": consistency_llm_probe["judge_error"] if consistency_llm_probe else None,
    }


def run_gold_benchmark(
    gold_package: dict[str, Any],
    *,
    candidate_dir: Path | None = None,
    use_gold_candidate: bool = False,
    genre: str = "investment",
    consistency_llm_ask: Any = None,
    consistency_judge_model: str | None = None,
) -> dict[str, Any]:
    attach_lightweight_ledgers(gold_package)
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
        result = score_case(
            case,
            candidate_text,
            genre=genre,
            consistency_llm_ask=consistency_llm_ask,
            consistency_judge_model=consistency_judge_model,
        )
        result["candidate_path"] = _relative_to_root(candidate_path)
        result["candidate_sha256"] = _sha256_bytes(candidate_text.encode("utf-8"))
        results.append(result)

    average_continuity_score = _average_metric(results, "continuity_score")
    average_gold_continuity_score = _average_metric(results, "gold_continuity_score")
    average_continuity_index = _average_metric(results, "continuity_index")
    average_gold_fidelity_score = _average_metric(results, "gold_fidelity_score")
    average_writing_quality_score = _average_metric(results, "writing_quality_score")
    average_legacy_blended_auto_score = _average_metric(results, "legacy_blended_auto_score")
    average_consistency_score = _average_metric(results, "consistency_score")
    average_consistency_auto_score = _average_metric(results, "consistency_auto_score")
    average_consistency_judge_score = _average_metric(results, "consistency_judge_score")
    average_continuity_violation_count = _average_metric(results, "continuity_violation_count")
    average_truth_warning_count = _average_metric(results, "truth_warning_count")
    average_manual_constraint_count = _average_metric(results, "manual_constraint_count")
    average_major_contradiction_count = _average_metric(results, "major_contradiction_count")
    return {
        "generated_at": now_iso(),
        "title": gold_package.get("title", ""),
        "title_slug": gold_package.get("title_slug", ""),
        "mvp_type": gold_package.get("mvp_type", "manuscript-only"),
        "score_profile": "continuity-gold-relative-v2",
        "primary_score_axis": "continuity_index",
        "consistency_score_profile": "contradiction-first-v1",
        "consistency_primary_axis": "consistency_score",
        "consistency_score_mode": "llm-judge" if consistency_judge_model else "auto-only",
        "consistency_judge_model": consistency_judge_model,
        "score_axes": {
            "primary": "continuity_index",
            "secondary": [
                "continuity_score",
                "gold_continuity_score",
                "gold_fidelity_score",
                "writing_quality_score",
                "legacy_blended_auto_score",
                "consistency_score",
                "consistency_auto_score",
                "consistency_judge_score",
                "major_contradiction_count",
                "continuity_violation_count",
                "truth_warning_count",
                "manual_constraint_count",
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
        "average_consistency_score": average_consistency_score,
        "average_consistency_auto_score": average_consistency_auto_score,
        "average_consistency_judge_score": average_consistency_judge_score,
        "average_continuity_violation_count": average_continuity_violation_count,
        "average_truth_warning_count": average_truth_warning_count,
        "average_manual_constraint_count": average_manual_constraint_count,
        "average_major_contradiction_count": average_major_contradiction_count,
        "average_auto_score": average_continuity_index,
        "results": results,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_json(payload) + "\n", encoding="utf-8")
