"""Pitch Normalization Layer — Mode A (Mechanical Normalize).

Converts unstructured narrative pitches into a canonical markdown format
with completeness checks, structural signals, and family-based overlay
signals.  Verdicts (commercial viability, old-pattern checks, etc.) are
**never** written by this module; they are reserved for LLM or human
reviewers.

Storage hierarchy
-----------------
- pending:  전처리_ssot/docs/10_pitches/pending/{slug}/pitch.md
- canon:    전처리_ssot/docs/10_pitches/canon/{work_id}/pitch.md
- mirror:   treatments/preprocess/{work_id}/00_brief/pitch.md  (optional)

Canon is the only writable authority.  Mirror is overwrite-only, no
reverse sync.
"""
from __future__ import annotations

import re
import shutil
from datetime import date
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ROOT = Path(__file__).resolve().parents[2]

_PITCHES_BASE = _ROOT / "전처리_ssot" / "docs" / "10_pitches"
_PENDING_BASE = _PITCHES_BASE / "pending"
_CANON_BASE = _PITCHES_BASE / "canon"
_PREPROCESS_BASE = _ROOT / "treatments" / "preprocess"

_SECTIONS = (
    "Hook",
    "Protagonist",
    "Conflict",
    "World",
    "Market Angle",
    "Notes",
    "Raw Input",
)

_COMPLETENESS_SECTIONS = ("Hook", "Protagonist", "Conflict", "World", "Market Angle")
_MIN_SUBSTANCE_CHARS = 20

NORMALIZED_VERSION = 1

# Signal extraction patterns (common)
_BLOCK_ENGINE_RE = re.compile(
    r"블록|에피소드|아크|block|arc|episode|대단원|권|부",
    re.IGNORECASE,
)
_DEFEAT_BEATS_RE = re.compile(r"패배|위기|추락|실패|위험|몰락|굴욕|좌절|궁지|절체절명")
# Rough Korean proper-name heuristic: 2-4 syllable Hangul tokens preceded
# by a space/SOL and followed by particles or punctuation typical for names.
_NAME_CANDIDATE_RE = re.compile(r"(?:^|(?<=\s))([가-힣]{2,4})(?=[은는이가의를에와과,.\s])")

# Wuxia overlay patterns
_REALM_RE = re.compile(r"경지|무공|내공|진기|수련|화경|현경|절정|초절정|입문|삼류|이류|일류|선천|귀신")
_SECT_RE = re.compile(r"문파|방파|세가|맹주|무림|강호|장문인|가주|장로|제자|사형|사제")
_MARTIAL_RE = re.compile(r"초식|검법|권법|장법|도법|경공|암기|비급|절학|신공")
# Hanja-annotated name: 백소연(白小燕)
_HANJA_PAREN_RE = re.compile(r"[가-힣]{2,4}\([^\)]*[\u4e00-\u9fff]+[^\)]*\)")

# Wuxia compound surnames (2-char, distinctive to martial-arts fiction)
_WUXIA_COMPOUND_SURNAMES = frozenset({
    "남궁", "제갈", "사마", "독고", "황보", "선우", "모용",
    "공손", "단목", "동방", "서문", "탁발", "태사",
})

# Sino-Korean syllables strongly associated with classical/wuxia naming
# register — curated from common wuxia character names across Korean
# web-novel and wuxia fiction corpora.
_WUXIA_GIVEN_SYLLABLES = frozenset({
    "연", "혁", "풍", "린", "운", "천", "검", "무", "영", "화",
    "용", "봉", "설", "월", "매", "란", "경", "청", "현", "명",
    "광", "웅", "강", "덕", "학", "룡", "표", "곤", "옥", "비",
    "초", "담", "휘", "창", "진", "호", "산", "일",
    "염", "해", "야", "홍", "기", "탁", "묵", "섭", "권", "충",
})

# Verdict status enum
VERDICT_STATUSES = frozenset({"PASS", "FAIL", "HOLD", "SKIP"})
VERDICT_KEYS = frozenset({"status", "rationale", "reviewed_by", "reviewed_at"})

# Path-safe identifier pattern: Korean, alphanumeric, underscore, hyphen.
# Must start with a non-separator character.  No path separators, no dot-dot.
_SAFE_ID_RE = re.compile(r"^[가-힣a-zA-Z0-9][가-힣a-zA-Z0-9_-]*$")

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class PitchCollisionError(FileExistsError):
    """Raised when a pitch target path already exists and force is not set."""


# ---------------------------------------------------------------------------
# Path validation
# ---------------------------------------------------------------------------


def _validate_path_id(value: str, label: str) -> None:
    """Reject slug/work_id values that could escape the intended root."""
    if not value or not value.strip():
        raise ValueError(f"{label} must not be empty")
    if not _SAFE_ID_RE.match(value):
        raise ValueError(
            f"{label} contains invalid characters: {value!r}. "
            "Only Korean, alphanumeric, underscore, and hyphen allowed. "
            "Path separators (/ \\ ..) are forbidden."
        )


def _assert_within(path: Path, root: Path) -> None:
    """Raise ValueError if *path* escapes *root* after resolution."""
    resolved = path.resolve()
    root_resolved = root.resolve()
    if not resolved.is_relative_to(root_resolved):
        raise ValueError(
            f"Path escapes intended root: {resolved} is not under {root_resolved}"
        )


# ---------------------------------------------------------------------------
# YAML frontmatter helpers (minimal, no external dependency)
# ---------------------------------------------------------------------------


def _dump_frontmatter(meta: dict[str, Any]) -> str:
    """Serialize metadata dict to YAML frontmatter string.

    Handles the nested dicts (completeness, signals, overlay_signals, verdicts)
    with simple two-level indentation.  No third-party YAML library required.
    """
    lines: list[str] = ["---"]
    for key, value in meta.items():
        if isinstance(value, dict):
            if not value:
                lines.append(f"{key}: {{}}")
            else:
                lines.append(f"{key}:")
                for k2, v2 in value.items():
                    if isinstance(v2, dict):
                        if not v2:
                            lines.append(f"  {k2}: {{}}")
                        else:
                            lines.append(f"  {k2}:")
                            for k3, v3 in v2.items():
                                lines.append(f"    {k3}: {_yaml_scalar(v3)}")
                    else:
                        lines.append(f"  {k2}: {_yaml_scalar(v2)}")
        else:
            lines.append(f"{key}: {_yaml_scalar(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def _yaml_scalar(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if v is None:
        return ""
    s = str(v)
    # Multiline values cannot round-trip through our line-based parser.
    # Reject them at serialization time rather than producing broken output.
    if "\n" in s or "\r" in s:
        raise ValueError(
            f"Frontmatter scalar values must not contain newlines: {s!r:.80}"
        )
    _NEEDS_QUOTE_CHARS = frozenset(':#{},[]&*?|-<>=!%@`"\\')
    if not s or any(c in _NEEDS_QUOTE_CHARS for c in s):
        escaped = s.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return s


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from pitch.md content.

    Returns (meta_dict, body_text).  Handles two levels of nesting.
    """
    if not text.startswith("---"):
        return {}, text

    end = text.find("\n---", 3)
    if end == -1:
        return {}, text

    fm_block = text[4:end].strip()
    body = text[end + 4:].lstrip("\n")

    meta: dict[str, Any] = {}
    current_l1_key: str | None = None
    current_l2_key: str | None = None

    for line in fm_block.split("\n"):
        stripped = line.rstrip()
        if not stripped:
            continue

        indent = len(line) - len(line.lstrip())

        if indent == 0:
            # Top-level key
            current_l1_key = None
            current_l2_key = None
            if ":" not in stripped:
                continue
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()
            if val == "" or val == "{}":
                # Could be dict start or empty dict
                meta[key] = {} if val == "{}" else {}
                current_l1_key = key
            else:
                meta[key] = _parse_scalar(val)
        elif indent >= 4 and current_l1_key and current_l2_key:
            # Level 3 (verdict sub-fields)
            if ":" not in stripped:
                continue
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()
            parent = meta.get(current_l1_key, {})
            if isinstance(parent, dict) and current_l2_key in parent:
                if isinstance(parent[current_l2_key], dict):
                    parent[current_l2_key][key] = _parse_scalar(val)
        elif indent >= 2 and current_l1_key:
            # Level 2
            current_l2_key = None
            if ":" not in stripped:
                continue
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()
            if not isinstance(meta.get(current_l1_key), dict):
                meta[current_l1_key] = {}
            if val == "" or val == "{}":
                meta[current_l1_key][key] = {} if val == "{}" else {}
                current_l2_key = key
            else:
                meta[current_l1_key][key] = _parse_scalar(val)

    return meta, body


def _parse_scalar(s: str) -> Any:
    if s.startswith('"') and s.endswith('"'):
        inner = s[1:-1]
        return inner.replace('\\"', '"').replace("\\\\", "\\")
    if s == "true":
        return True
    if s == "false":
        return False
    if s == "{}":
        return {}
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _parse_sections(body: str) -> dict[str, str]:
    """Split markdown body into section_name -> content dict."""
    result: dict[str, str] = {}
    current_section: str | None = None
    current_lines: list[str] = []

    for line in body.split("\n"):
        m = re.match(r"^##\s+(.+)$", line)
        if m:
            if current_section is not None:
                result[current_section] = "\n".join(current_lines).strip()
            current_section = m.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_section is not None:
        result[current_section] = "\n".join(current_lines).strip()

    return result


# ---------------------------------------------------------------------------
# Completeness + signal extraction
# ---------------------------------------------------------------------------

_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def _has_substance(text: str) -> bool:
    """True if text has >= _MIN_SUBSTANCE_CHARS of real content."""
    cleaned = _HTML_COMMENT_RE.sub("", text).strip()
    return len(cleaned) >= _MIN_SUBSTANCE_CHARS


def _eval_completeness(sections: dict[str, str]) -> dict[str, bool]:
    return {
        _section_key(s): _has_substance(sections.get(s, ""))
        for s in _COMPLETENESS_SECTIONS
    }


def _section_key(name: str) -> str:
    return name.lower().replace(" ", "_")


def _eval_signals(full_text: str, sections: dict[str, str]) -> dict[str, bool]:
    hook_conflict = (sections.get("Hook", "") + " " + sections.get("Conflict", "")).strip()
    search_text = hook_conflict if hook_conflict else full_text
    return {
        "block_engine_sketched": bool(_BLOCK_ENGINE_RE.search(search_text)),
        "npc_pool_present": len(_NAME_CANDIDATE_RE.findall(full_text)) >= 2,
        "defeat_beats_present": bool(_DEFEAT_BEATS_RE.search(full_text)),
    }


def _is_wuxia_register_name(name: str, hanja_annotated_names: frozenset[str]) -> bool:
    """Determine if a Korean name follows wuxia naming conventions.

    Three tiers:
      1. Hanja-annotated in the source text  → definite
      2. Starts with a known wuxia compound surname → definite
      3. Given-name syllables overlap with wuxia register set → likely
    """
    # Tier 1: annotated with hanja elsewhere in the text
    if name in hanja_annotated_names:
        return True
    # Tier 2: compound surname
    if len(name) >= 3 and name[:2] in _WUXIA_COMPOUND_SURNAMES:
        return True
    # Tier 3: syllable check on the given-name portion
    if len(name) == 3:
        given = name[1:]  # surname 1 char + given 2 chars
        if any(s in _WUXIA_GIVEN_SYLLABLES for s in given):
            return True
    if len(name) == 4:
        # Could be compound-surname(2)+given(2) or surname(1)+given(3)
        given_2 = name[2:]
        given_3 = name[1:]
        if any(s in _WUXIA_GIVEN_SYLLABLES for s in given_2):
            return True
        if sum(1 for s in given_3 if s in _WUXIA_GIVEN_SYLLABLES) >= 2:
            return True
    if len(name) == 2:
        # Require BOTH syllables — single overlap is too ambiguous for
        # 2-char names (e.g. 영희: 영 is wuxia but 희 is not).
        if all(s in _WUXIA_GIVEN_SYLLABLES for s in name):
            return True
    return False


def _eval_wuxia_overlay(full_text: str) -> dict[str, Any]:
    names = _NAME_CANDIDATE_RE.findall(full_text)

    # Collect names that have hanja annotations for tier-1 matching
    hanja_annotated = frozenset(
        m[:m.index("(")]
        for m in _HANJA_PAREN_RE.findall(full_text)
        if "(" in m
    )

    total_names = max(len(names), 1)
    wuxia_count = sum(
        1 for n in names if _is_wuxia_register_name(n, hanja_annotated)
    )
    ratio = wuxia_count / total_names

    if ratio >= 0.7:
        naming_register = "high"
    elif ratio >= 0.3:
        naming_register = "partial"
    else:
        naming_register = "low"

    return {
        "realm_terms_found": bool(_REALM_RE.search(full_text)),
        "sect_terms_found": bool(_SECT_RE.search(full_text)),
        "martial_showcase_found": bool(_MARTIAL_RE.search(full_text)),
        "naming_register": naming_register,
    }


# ---------------------------------------------------------------------------
# Verdict validation (read-time only, never written by this module)
# ---------------------------------------------------------------------------


def validate_verdicts(verdicts: dict[str, Any]) -> list[str]:
    """Return list of validation errors for a verdicts dict.  Empty = valid."""
    errors: list[str] = []
    if not isinstance(verdicts, dict):
        return ["verdicts must be a dict"]
    for key, obj in verdicts.items():
        if not isinstance(obj, dict):
            errors.append(f"verdict '{key}' must be a dict, got {type(obj).__name__}")
            continue
        missing = VERDICT_KEYS - set(obj.keys())
        if missing:
            errors.append(f"verdict '{key}' missing keys: {sorted(missing)}")
        extra = set(obj.keys()) - VERDICT_KEYS
        if extra:
            errors.append(f"verdict '{key}' has unexpected keys: {sorted(extra)}")
        status = obj.get("status")
        if status is not None and status not in VERDICT_STATUSES:
            errors.append(f"verdict '{key}' status '{status}' not in {sorted(VERDICT_STATUSES)}")
    return errors


# ---------------------------------------------------------------------------
# Core build helpers
# ---------------------------------------------------------------------------


def _build_body(sections_content: dict[str, str]) -> str:
    parts: list[str] = []
    for section_name in _SECTIONS:
        parts.append(f"## {section_name}")
        parts.append("")
        content = sections_content.get(section_name, "")
        if content:
            parts.append(content)
        parts.append("")
    return "\n".join(parts)


def _build_pitch_md(
    *,
    raw_input: str,
    work_id: str,
    slug: str = "",
    title: str,
    family_guess: str,
    genre_hint: str,
    created: str,
) -> tuple[str, dict[str, Any]]:
    """Build pitch.md content and return (md_text, result_dict)."""
    full_text = raw_input

    sections_content: dict[str, str] = {s: "" for s in _SECTIONS}
    sections_content["Raw Input"] = raw_input

    completeness = _eval_completeness(sections_content)
    signals = _eval_signals(full_text, sections_content)

    overlay_signals: dict[str, Any] = {}
    if family_guess == "wuxguide":
        overlay_signals = _eval_wuxia_overlay(full_text)

    meta: dict[str, Any] = {
        "work_id": work_id,
    }
    if slug:
        meta["slug"] = slug
    meta.update({
        "title": title,
        "family_guess": family_guess,
        "genre_hint": genre_hint,
        "created": created,
        "normalized_version": NORMALIZED_VERSION,
        "completeness": completeness,
        "signals": signals,
        "overlay_signals": overlay_signals,
        "verdicts": {},
    })

    md_text = _dump_frontmatter(meta) + "\n" + _build_body(sections_content)

    return md_text, {
        "completeness": completeness,
        "signals": signals,
        "overlay_signals": overlay_signals,
    }


def _write_pitch(target: Path, content: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def normalize_pitch(
    raw_input: str,
    *,
    slug: str,
    title: str = "",
    family_guess: str = "blockguide",
    genre_hint: str = "",
    force: bool = False,
) -> dict[str, Any]:
    """Normalize raw input into pending/{slug}/pitch.md.

    Raises PitchCollisionError if target exists and force is False.
    """
    _validate_path_id(slug, "slug")
    target = _PENDING_BASE / slug / "pitch.md"
    _assert_within(target, _PENDING_BASE)
    if target.exists() and not force:
        raise PitchCollisionError(f"Pending pitch already exists: {target}")

    md_text, result = _build_pitch_md(
        raw_input=raw_input,
        work_id="pending",
        slug=slug,
        title=title,
        family_guess=family_guess,
        genre_hint=genre_hint,
        created=date.today().isoformat(),
    )
    _write_pitch(target, md_text)
    result["path"] = target
    return result


def normalize_pitch_to_canon(
    raw_input: str,
    *,
    work_id: str,
    title: str = "",
    family_guess: str = "blockguide",
    genre_hint: str = "",
    force: bool = False,
) -> dict[str, Any]:
    """Normalize raw input directly into canon/{work_id}/pitch.md.

    Raises PitchCollisionError if target exists and force is False.
    """
    _validate_path_id(work_id, "work_id")
    target = _CANON_BASE / work_id / "pitch.md"
    _assert_within(target, _CANON_BASE)
    if target.exists() and not force:
        raise PitchCollisionError(f"Canon pitch already exists: {target}")

    md_text, result = _build_pitch_md(
        raw_input=raw_input,
        work_id=work_id,
        title=title,
        family_guess=family_guess,
        genre_hint=genre_hint,
        created=date.today().isoformat(),
    )
    _write_pitch(target, md_text)
    result["path"] = target
    return result


def promote_pitch(slug: str, work_id: str, *, force: bool = False) -> Path:
    """Move pending/{slug}/ to canon/{work_id}/.

    Updates work_id in frontmatter.  Raises PitchCollisionError if canon
    target exists and force is False.  Raises FileNotFoundError if pending
    source does not exist.
    """
    _validate_path_id(slug, "slug")
    _validate_path_id(work_id, "work_id")
    src_dir = _PENDING_BASE / slug
    _assert_within(src_dir, _PENDING_BASE)
    src_file = src_dir / "pitch.md"
    if not src_file.exists():
        raise FileNotFoundError(f"Pending pitch not found: {src_file}")

    dst_dir = _CANON_BASE / work_id
    _assert_within(dst_dir, _CANON_BASE)
    if dst_dir.exists() and not force:
        raise PitchCollisionError(f"Canon path already exists: {dst_dir}")

    # Read, update work_id, remove slug
    content = src_file.read_text(encoding="utf-8")
    meta, body = _parse_frontmatter(content)
    meta["work_id"] = work_id
    meta.pop("slug", None)

    # Write to canon (verify containment before any rmtree)
    new_content = _dump_frontmatter(meta) + "\n" + body
    if dst_dir.exists():
        _assert_within(dst_dir, _CANON_BASE)
        shutil.rmtree(dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst_file = dst_dir / "pitch.md"
    dst_file.write_text(new_content, encoding="utf-8")

    # Remove pending source (verify containment before rmtree)
    _assert_within(src_dir, _PENDING_BASE)
    shutil.rmtree(src_dir)

    return dst_file


def read_pitch(work_id: str) -> dict[str, Any] | None:
    """Read and parse canon/{work_id}/pitch.md.  Returns None if not found."""
    _validate_path_id(work_id, "work_id")
    target = _CANON_BASE / work_id / "pitch.md"
    _assert_within(target, _CANON_BASE)
    if not target.exists():
        return None
    content = target.read_text(encoding="utf-8")
    meta, body = _parse_frontmatter(content)
    sections = _parse_sections(body)
    return {"meta": meta, "sections": sections, "path": target}


def read_pending_pitch(slug: str) -> dict[str, Any] | None:
    """Read and parse pending/{slug}/pitch.md.  Returns None if not found."""
    _validate_path_id(slug, "slug")
    target = _PENDING_BASE / slug / "pitch.md"
    _assert_within(target, _PENDING_BASE)
    if not target.exists():
        return None
    content = target.read_text(encoding="utf-8")
    meta, body = _parse_frontmatter(content)
    sections = _parse_sections(body)
    return {"meta": meta, "sections": sections, "path": target}


def mirror_pitch_to_preprocess(work_id: str) -> Path | None:
    """Copy canon pitch to preprocess/00_brief/pitch.md.

    Always overwrites (canon wins).  Returns None if canon pitch does not
    exist or preprocess base does not exist.
    """
    _validate_path_id(work_id, "work_id")
    canon_file = _CANON_BASE / work_id / "pitch.md"
    _assert_within(canon_file, _CANON_BASE)
    if not canon_file.exists():
        return None

    preprocess_dir = _PREPROCESS_BASE / work_id
    _assert_within(preprocess_dir, _PREPROCESS_BASE)
    if not preprocess_dir.exists():
        return None

    brief_dir = preprocess_dir / "00_brief"
    brief_dir.mkdir(parents=True, exist_ok=True)
    dst = brief_dir / "pitch.md"
    shutil.copy2(canon_file, dst)
    return dst
