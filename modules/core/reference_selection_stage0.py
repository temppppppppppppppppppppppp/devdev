from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

SLIM_SECTION_RE = re.compile(
    r"##\s*(?:4\.\s*)?Slim Reference Card v1(?P<body>.*?)(?:\n##\s|\Z)",
    re.DOTALL,
)
BULLET_FIELD_RE = re.compile(r"^- \*\*(?P<key>[^*]+)\*\*:\s*(?P<value>.+)$", re.MULTILINE)
PLAIN_FIELD_RE = re.compile(r"^\*\*(?P<key>[^*]+)\*\*:\s*(?P<value>.+)$", re.MULTILINE)
TABLE_FIELD_RE = re.compile(
    r"^\|\s*\*\*(?P<key>[^*]+)\*\*\s*\|\s*(?P<value>.*?)\s*\|$",
    re.MULTILINE,
)
PLAIN_TABLE_FIELD_RE = re.compile(
    r"^\|\s*(?P<key>[^|*][^|]*)\s*\|\s*(?P<value>.*?)\s*\|$",
    re.MULTILINE,
)
INLINE_SPLIT_RE = re.compile(r"\s*(?:/|·|•|;|,)\s*")

PROFILE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "investment_market_profile": ("투자", "금융", "주식", "환율", "펀드", "m&a", "지분", "포트폴리오"),
    "office_power_profile": ("직장", "회사", "신입", "승진", "결재", "사무실", "상사"),
    "medical_professional_profile": ("의사", "병원", "수술", "응급실", "의료", "환자"),
    "entertainment_media_profile": ("엔터", "가수", "배우", "방송", "미디어", "예능"),
    "tech_startup_profile": ("스타트업", "saas", "플랫폼", "앱", "기술", "ai", "개발"),
    "urban_power_profile": ("게이트", "헌터", "길드", "각성", "던전", "이능"),
    "wuxia": ("무협", "강호", "검법", "내공", "문파"),
    "business_growth_profile": ("재벌", "기업", "사업", "경영", "그룹", "회장", "인수", "운영"),
}
VALID_PROFILES = tuple(PROFILE_KEYWORDS.keys())

HUD_DEFAULTS: dict[str, dict[str, str]] = {
    "investment_market_profile": {
        "capital": "운용 자금과 평가이익",
        "deal_type": "매수·매도·지분 딜",
        "resource_power_hud": "포지션·신뢰·접근권",
        "business_lines": "포트폴리오와 투자 테마",
        "company_state": "법인·펀드 상태",
    },
    "office_power_profile": {
        "capital": "승인권과 인사 자본",
        "deal_type": "결재·배치·승진",
        "resource_power_hud": "보고 라인·평판·업무 성과",
        "business_lines": "조직 라인과 핵심 프로젝트",
        "company_state": "조직 내 위상과 결재 체계",
    },
    "medical_professional_profile": {
        "capital": "수술 실적과 병원 신뢰",
        "deal_type": "수술·자문·진료권",
        "resource_power_hud": "환자 결과·의료 네트워크",
        "business_lines": "진료과·연구 라인",
        "company_state": "병원 내 위상과 운영 상태",
    },
    "entertainment_media_profile": {
        "capital": "인지도와 협찬 자본",
        "deal_type": "캐스팅·편성·계약",
        "resource_power_hud": "화제성·팬덤·섭외력",
        "business_lines": "채널·아티스트·콘텐츠 라인",
        "company_state": "프로젝트 흥행과 브랜드 상태",
    },
    "tech_startup_profile": {
        "capital": "런웨이와 제품 지표",
        "deal_type": "투자유치·계약·배포",
        "resource_power_hud": "유저 성장·제품 속도·기술 우위",
        "business_lines": "제품군과 기술 스택",
        "company_state": "회사 런웨이와 운영 지표",
    },
    "urban_power_profile": {
        "capital": "전투 자원과 길드 신뢰",
        "deal_type": "공략·배치·보상 계약",
        "resource_power_hud": "전투력·명성·점유권",
        "business_lines": "헌터팀과 공략 라인",
        "company_state": "길드 상태와 구역 통제",
    },
    "wuxia": {
        "capital": "내공과 문파 자원",
        "deal_type": "비급·거래·맹약",
        "resource_power_hud": "경지·명성·문파 지원",
        "business_lines": "문파·상단·세력 라인",
        "company_state": "강호 위상과 세력도",
    },
    "business_growth_profile": {
        "capital": "현금흐름과 사업권",
        "deal_type": "계약·인수·운영권",
        "resource_power_hud": "매출·점유율·승인권",
        "business_lines": "사업 부문과 계열사",
        "company_state": "회사 체력과 확장 상태",
    },
}


@dataclass(frozen=True)
class CardSignal:
    card_slug: str
    track: str
    handoff_label: str
    selection_reason: str
    mirror_relpath: str
    fields: dict[str, str]
    manifest_entry: dict[str, Any]


@dataclass(frozen=True)
class Stage0SelectionDraftResult:
    source_manifest: dict[str, Any]
    profile_lock: dict[str, Any]
    material_bundle_summary: dict[str, Any]
    phase0_ready_snapshot: dict[str, Any]
    contamination_guard: dict[str, Any]
    selected_cards: tuple[CardSignal, ...]
    updated_paths: tuple[str, ...]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _normalize_key(key: str) -> str:
    normalized = key.strip().lower().replace(" ", "_").replace("-", "_")
    normalized = normalized.replace("(", "").replace(")", "")
    return normalized


def _clean_text(value: str) -> str:
    cleaned = re.sub(r"`+", "", value or "")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip(" |")


def _shorten(text: str, limit: int = 120) -> str:
    compact = _clean_text(text)
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def _first_nonempty(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _unique_texts(values: list[str], limit: int | None = None) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        compact = _clean_text(value)
        if not compact or compact in seen:
            continue
        seen.add(compact)
        unique.append(compact)
        if limit is not None and len(unique) >= limit:
            break
    return unique


def _extract_slim_fields(card_text: str) -> dict[str, str]:
    match = SLIM_SECTION_RE.search(card_text)
    if not match:
        raise ValueError("Slim Reference Card v1 section not found")
    body = match.group("body")
    fields: dict[str, str] = {}

    for pattern in (BULLET_FIELD_RE, PLAIN_FIELD_RE, TABLE_FIELD_RE, PLAIN_TABLE_FIELD_RE):
        for field_match in pattern.finditer(body):
            key = _normalize_key(field_match.group("key"))
            value = _clean_text(field_match.group("value"))
            if key in {"필드", "---", "------"}:
                continue
            if value and key not in fields:
                fields[key] = value

    if not fields:
        raise ValueError("No slim card fields parsed")
    return fields


def _load_card_manifest(root: Path) -> dict[tuple[str, str], dict[str, Any]]:
    manifest_path = root / "narrative_ssot" / "10_reference_bank" / "reference_card_manifest.json"
    manifest = _read_json(manifest_path)
    entries = manifest.get("entries", [])
    if not isinstance(entries, list):
        raise ValueError(f"Invalid reference card manifest: {manifest_path}")
    table: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        slug = str(entry.get("slug", "")).strip()
        track = str(entry.get("track", "")).strip().upper()
        if slug and track:
            table[(slug, track)] = entry
    return table


def _resolve_card_path(root: Path, entry: dict[str, Any]) -> tuple[Path, str]:
    filename = Path(str(entry.get("output_path", ""))).name
    if not filename:
        slug = str(entry.get("slug", "")).strip()
        track = str(entry.get("track", "")).strip().upper()
        filename = f"{slug}_{track}.md"
    card_path = root / "narrative_ssot" / "10_reference_bank" / "cards" / filename
    relpath = str(card_path.relative_to(root)).replace("\\", "/")
    return card_path, relpath


def load_selected_card_signals(
    work_id: str,
    root: Path = ROOT,
) -> tuple[dict[str, Any], dict[str, Any], tuple[CardSignal, ...]]:
    project_root = root / "narrative_ssot" / "50_projects" / work_id
    reference_selection_path = project_root / "10_reference_selection" / "reference_selection.json"
    contamination_guard_path = project_root / "10_reference_selection" / "contamination_guard.json"

    reference_selection = _read_json(reference_selection_path)
    contamination_guard = _read_json(contamination_guard_path)
    manifest_lookup = _load_card_manifest(root)

    selected_cards = reference_selection.get("selected_cards")
    if not isinstance(selected_cards, list) or not selected_cards:
        raise ValueError(f"reference_selection has no selected_cards: {reference_selection_path}")

    signals: list[CardSignal] = []
    for raw_card in selected_cards:
        if not isinstance(raw_card, dict):
            raise ValueError("selected_cards entries must be objects")
        slug = str(raw_card.get("card_slug", "")).strip()
        track = str(raw_card.get("track", "")).strip().upper()
        handoff_label = str(raw_card.get("handoff_label", "")).strip()
        selection_reason = str(raw_card.get("selection_reason", "")).strip()
        if not raw_card.get("must_not_copy_applied"):
            raise ValueError(f"{slug}_{track} missing must_not_copy_applied=true")
        if not raw_card.get("contamination_risk_reviewed"):
            raise ValueError(f"{slug}_{track} missing contamination_risk_reviewed=true")
        manifest_entry = manifest_lookup.get((slug, track))
        if manifest_entry is None:
            raise ValueError(f"Card not found in manifest: {slug}_{track}")
        card_path, relpath = _resolve_card_path(root, manifest_entry)
        if not card_path.is_file():
            raise ValueError(f"Card file missing: {card_path}")
        card_text = card_path.read_text(encoding="utf-8")
        signals.append(
            CardSignal(
                card_slug=slug,
                track=track,
                handoff_label=handoff_label,
                selection_reason=selection_reason,
                mirror_relpath=relpath,
                fields=_extract_slim_fields(card_text),
                manifest_entry=manifest_entry,
            )
        )

    return reference_selection, contamination_guard, tuple(signals)


def infer_profiles(cards: tuple[CardSignal, ...]) -> tuple[str, str]:
    blob = " ".join(
        _first_nonempty(
            card.selection_reason,
            card.fields.get("usable_lane"),
            card.fields.get("usable_sector"),
            card.fields.get("growth_axis"),
            card.fields.get("authority_gain_route"),
            card.fields.get("block1_spike"),
        ).lower()
        for card in cards
    )
    scores: list[tuple[int, str]] = []
    for profile, keywords in PROFILE_KEYWORDS.items():
        score = sum(blob.count(keyword.lower()) for keyword in keywords)
        scores.append((score, profile))
    scores.sort(reverse=True)
    primary = next((profile for score, profile in scores if score > 0), "business_growth_profile")
    secondary = ""
    for score, profile in scores:
        if score > 0 and profile != primary:
            secondary = profile
            break
    return primary, secondary


def _profile_override(reference_selection: dict[str, Any]) -> tuple[str, str, str]:
    override = reference_selection.get("profile_override")
    if override is None:
        return "", "", ""
    if not isinstance(override, dict):
        raise ValueError("reference_selection.profile_override must be an object or null")

    primary = _clean_text(str(override.get("primary_profile", "")))
    secondary = _clean_text(str(override.get("secondary_profile", "")))
    reason = _clean_text(str(override.get("reason", "")))

    if not primary:
        raise ValueError("reference_selection.profile_override.primary_profile must be non-empty")
    if primary not in VALID_PROFILES:
        raise ValueError(
            f"reference_selection.profile_override.primary_profile '{primary}' is not a valid profile"
        )
    if secondary and secondary not in VALID_PROFILES:
        raise ValueError(
            f"reference_selection.profile_override.secondary_profile '{secondary}' is not a valid profile"
        )
    if secondary == primary:
        secondary = ""
    if not reason:
        raise ValueError("reference_selection.profile_override.reason must be non-empty")
    return primary, secondary, reason


def resolve_profiles(
    reference_selection: dict[str, Any],
    cards: tuple[CardSignal, ...],
) -> tuple[str, str, str]:
    override_primary, override_secondary, override_reason = _profile_override(reference_selection)
    if override_primary:
        return (
            override_primary,
            override_secondary,
            f"profile_override locked in reference_selection: {override_reason}",
        )
    inferred_primary, inferred_secondary = infer_profiles(cards)
    return inferred_primary, inferred_secondary, "inferred from selected_cards heuristics"


def _profile_hud(primary_profile: str) -> dict[str, str]:
    return dict(HUD_DEFAULTS.get(primary_profile, HUD_DEFAULTS["business_growth_profile"]))


def _split_inline_items(value: str) -> list[str]:
    compact = _clean_text(value)
    if not compact:
        return []
    if compact.startswith("(") and compact.endswith(")"):
        compact = compact[1:-1].strip()
    if len(compact) < 24:
        return [compact]
    parts = INLINE_SPLIT_RE.split(compact)
    if len(parts) <= 1:
        return [compact]
    return [part for part in parts if part]


def _role_candidates(card: CardSignal) -> list[str]:
    blob = " ".join(card.fields.values())
    label = f"{card.card_slug}_{card.track}"
    roles: list[str] = []
    if "멘토" in blob or "원로" in blob:
        roles.append(f"{label}: 업계 원로 또는 멘토 체인 인물")
    if any(token in blob for token in ("부하", "실장", "참모", "비서")):
        roles.append(f"{label}: 주인공 권위를 비춰줄 실무 참모")
    if any(token in blob for token in ("어머니", "가족", "형", "혈연")):
        roles.append(f"{label}: 보호 대상 가족 또는 결핍 고리")
    if any(token in blob for token in ("유착", "검사", "부패", "적", "비리")):
        roles.append(f"{label}: 시스템 내부의 부패 실무자")
    if not roles:
        roles.append(f"{label}: opening battlefield 이해관계자")
    return roles


def _macro_battlefield(cards: tuple[CardSignal, ...]) -> str:
    blob = " ".join(
        _first_nonempty(
            card.fields.get("block1_spike"),
            card.fields.get("must_borrow"),
            card.fields.get("first_reward"),
            card.fields.get("growth_axis"),
        )
        for card in cards
    )
    if any(token in blob for token in ("과세", "증거", "공개 굴욕", "안방", "권위")):
        return "증거 공개와 권위 행사 전장"
    if any(token in blob for token in ("투자", "레버리지", "펀드", "환율", "M&A", "거액 베팅")):
        return "첫 투자 인프라와 대형 베팅 전장"
    if any(token in blob for token in ("회장", "30조", "비상장", "완성된", "권력")):
        return "완성형 권력 공개 전장"
    if any(token in blob for token in ("직장", "신입", "승진", "결재", "상사")):
        return "조직 내부 승인과 권력 전장"
    return _shorten(blob, limit=36) + " 전장"


def build_opening_bundle_contract(cards: tuple[CardSignal, ...]) -> dict[str, Any]:
    primary = cards[0]
    opening = _first_nonempty(primary.fields.get("opening_humiliation"), primary.selection_reason)
    spike = _first_nonempty(primary.fields.get("block1_spike"), primary.fields.get("must_borrow"))
    reward = _first_nonempty(primary.fields.get("first_reward"), primary.fields.get("growth_axis"))
    authority = _first_nonempty(primary.fields.get("authority_gain_route"), primary.fields.get("growth_axis"))

    map_items = _unique_texts(
        [
            _shorten(opening, 84),
            _shorten(spike, 84),
            _shorten(reward, 84),
        ],
        limit=3,
    )
    if not map_items:
        map_items = ["Selected reference cards require an opening battlefield map."]

    bundle_goal = _shorten(
        f"{reward or spike}를 독자에게 증명하고 {authority or spike}로 다음 전장 입장권을 연다.",
        140,
    )
    timing_note = _shorten(
        f"selected_cards 중심 초안이다. signboard·reevaluation·next-ticket는 TR 2~6 안에 "
        f"압축하고, opening macro battlefield는 {_macro_battlefield(cards)}에서 머물지 않게 설계한다.",
        180,
    )
    return {
        "bundle_window": "TR 2~6",
        "macro_battlefield": _macro_battlefield(cards),
        "macro_battlefield_map": map_items,
        "bundle_goal": bundle_goal,
        "first_signboard_block": 3,
        "representative_reevaluation_block": 4,
        "next_battlefield_ticket_block": 6,
        "timing_reconciliation_note": timing_note,
    }


def build_stage0_selection_draft(
    work_id: str,
    root: Path = ROOT,
) -> Stage0SelectionDraftResult:
    reference_selection, _contamination_guard, cards = load_selected_card_signals(work_id, root=root)
    primary_profile, secondary_profile, profile_resolution = resolve_profiles(reference_selection, cards)

    selection_relpath = f"narrative_ssot/50_projects/{work_id}/10_reference_selection/reference_selection.json"
    opening_bundle_contract = build_opening_bundle_contract(cards)
    project_title = f"TODO: replace title for {work_id}"

    reference_only_sources = _unique_texts(
        [selection_relpath, *[card.mirror_relpath for card in cards]],
        limit=8,
    )

    core_materials = _unique_texts(
        [
            f"{card.card_slug}_{card.track}: {card.fields.get('must_borrow', '')}"
            for card in cards
        ]
        + [
            f"{card.card_slug}_{card.track}: {card.fields.get('block1_spike', '')}"
            for card in cards
        ],
        limit=8,
    )

    npc_pool = _unique_texts(
        [role for card in cards for role in _role_candidates(card)],
        limit=8,
    )

    crisis_pool = _unique_texts(
        [
            f"{card.card_slug}_{card.track}: {card.fields.get('opening_humiliation', '')}"
            for card in cards
        ]
        + [
            f"{card.card_slug}_{card.track}: {card.fields.get('contamination_risk', '')}"
            for card in cards
        ],
        limit=8,
    )

    hard_constraints = _unique_texts(
        [
            f"{card.card_slug}_{card.track}: {card.fields.get('must_not_copy', '')}"
            for card in cards
        ]
        + [
            f"{card.card_slug}_{card.track}: selection_reason={card.selection_reason}"
            for card in cards
        ],
        limit=8,
    )

    do_not_fake = _unique_texts(
        [
            f"{card.card_slug}_{card.track}: {card.fields.get('contamination_risk', '')}"
            for card in cards
        ]
        + [
            "Selected few-shot cards are structure references only; named entities and signature gimmicks remain forbidden."
        ],
        limit=8,
    )

    source_manifest = {
        "work_identity": {
            "work_id": work_id,
            "title": project_title,
            "primary_profile": primary_profile,
            "secondary_profile": secondary_profile,
        },
        "canonical_sources": [f"material_ssot/20_pitch/canon/{work_id}.md"],
        "reference_only_sources": reference_only_sources,
        "core_materials": core_materials,
        "npc_pool": npc_pool,
        "crisis_pool": crisis_pool,
        "hard_constraints": hard_constraints,
        "do_not_fake": do_not_fake,
        "manual_audit_note": _shorten(
            "reference_selection 기반 자동 Stage0 초안이다. selected_cards의 오프닝 구조와 must_not_copy "
            f"제약은 이식했지만, 프로젝트 고유 재료와 canon source 감사는 아직 미완료다. Profile: {profile_resolution}.",
            180,
        ),
    }

    resource_axis = _unique_texts(
        [
            f"{card.card_slug}_{card.track}: {card.fields.get('first_reward', '')}"
            for card in cards
        ]
        + [
            f"{card.card_slug}_{card.track}: {card.fields.get('growth_axis', '')}"
            for card in cards
        ],
        limit=6,
    )

    power_axis = _unique_texts(
        [
            f"{card.card_slug}_{card.track}: {card.fields.get('protagonist_edge', '')}"
            for card in cards
        ]
        + [
            f"{card.card_slug}_{card.track}: {card.fields.get('block1_spike', '')}"
            for card in cards
        ],
        limit=6,
    )

    control_axis = _unique_texts(
        [
            f"{card.card_slug}_{card.track}: {card.fields.get('authority_gain_route', '')}"
            for card in cards
        ]
        + [
            f"{card.card_slug}_{card.track}: {card.fields.get('how', '')}"
            for card in cards
        ],
        limit=6,
    )

    payoff_axis = _unique_texts(
        [
            f"{card.card_slug}_{card.track}: {card.fields.get('first_reward', '')}"
            for card in cards
        ]
        + [
            f"{card.card_slug}_{card.track}: {card.fields.get('sector_expansion_path', '')}"
            for card in cards
        ],
        limit=6,
    )

    failure_axis = _unique_texts(
        [
            f"{card.card_slug}_{card.track}: {card.fields.get('opening_humiliation', '')}"
            for card in cards
        ]
        + [
            f"{card.card_slug}_{card.track}: {card.fields.get('contamination_risk', '')}"
            for card in cards
        ],
        limit=6,
    )

    profile_lock = {
        "primary_profile": primary_profile,
        "secondary_profile": secondary_profile,
        "resource_axis": resource_axis,
        "power_axis": power_axis,
        "control_axis": control_axis,
        "payoff_axis": payoff_axis,
        "failure_axis": failure_axis,
        "hud_interpretation": _profile_hud(primary_profile),
    }

    material_bundle_summary = {
        "events": _unique_texts(
            [
                f"{card.card_slug}_{card.track}: {card.fields.get('opening_humiliation', '')}"
                for card in cards
            ]
            + [
                f"{card.card_slug}_{card.track}: {card.fields.get('block1_spike', '')}"
                for card in cards
            ]
            + [
                f"{card.card_slug}_{card.track}: {card.fields.get('first_reward', '')}"
                for card in cards
            ],
            limit=10,
        ),
        "npc_candidates": npc_pool,
        "crisis_candidates": crisis_pool,
        "terms": _unique_texts(
            [card.handoff_label for card in cards]
            + [card.fields.get("source_manifest_ready_label", "") for card in cards]
            + [primary_profile, secondary_profile],
            limit=10,
        ),
        "scene_details": _unique_texts(
            [
                f"{card.card_slug}_{card.track}: {card.fields.get('block1_spike', '')}"
                for card in cards
            ]
            + [
                f"{card.card_slug}_{card.track}: {card.fields.get('authority_gain_route', '')}"
                for card in cards
            ]
            + [
                f"{card.card_slug}_{card.track}: {card.fields.get('sector_expansion_path', '')}"
                for card in cards
            ],
            limit=10,
        ),
        "notes": _shorten(
            "selected_cards 기반 preprocess 초안이다. card의 Block 1 신호와 must_borrow 축만 요약 반영했으며, "
            f"실물 재료 audit 전까지는 TR 생산 authority로 단독 사용하면 안 된다. Profile: {profile_resolution}.",
            180,
        ),
        "opening_bundle_contract": opening_bundle_contract,
    }

    phase0_ready_snapshot = {
        "identity_locked": False,
        "profile_locked": bool(primary_profile and resource_axis and power_axis),
        "material_sufficient": len(cards) >= 1 and bool(material_bundle_summary["events"]),
        "manual_audit_pass": False,
        "remaining_risks": _unique_texts(
            [
                "Project-specific canon source is still a placeholder and must be replaced by audited materials.",
                "Opening bundle contract is inferred from selected reference cards, not from work-specific Phase0 evidence.",
                "Human audit must confirm contamination controls before planning handoff.",
                f"Current profile resolution: {profile_resolution}.",
            ]
        ),
    }

    contamination_guard_result = {
        "must_not_copy_reviewed": True,
        "contamination_risk_reviewed": True,
        "notes": _shorten(
            "selected_cards의 must_not_copy_applied / contamination_risk_reviewed=true를 확인했다. "
            "Stage0 초안은 구조 차용 전용이며 고유명·시그니처 장치는 금지 상태를 유지한다.",
            180,
        ),
    }

    return Stage0SelectionDraftResult(
        source_manifest=source_manifest,
        profile_lock=profile_lock,
        material_bundle_summary=material_bundle_summary,
        phase0_ready_snapshot=phase0_ready_snapshot,
        contamination_guard=contamination_guard_result,
        selected_cards=cards,
        updated_paths=(),
    )


def sync_stage0_from_reference_selection(
    work_id: str,
    root: Path = ROOT,
    write: bool = True,
) -> Stage0SelectionDraftResult:
    result = build_stage0_selection_draft(work_id, root=root)
    project_root = root / "narrative_ssot" / "50_projects" / work_id
    preprocess_root = project_root / "20_preprocess"
    contamination_guard_path = project_root / "10_reference_selection" / "contamination_guard.json"

    outputs = {
        preprocess_root / "source_manifest.json": result.source_manifest,
        preprocess_root / "profile_lock.json": result.profile_lock,
        preprocess_root / "material_bundle_summary.json": result.material_bundle_summary,
        preprocess_root / "phase0_ready_snapshot.json": result.phase0_ready_snapshot,
        contamination_guard_path: result.contamination_guard,
    }

    updated_paths: list[str] = []
    if write:
        for path, payload in outputs.items():
            _write_json(path, payload)
            updated_paths.append(str(path))

    return Stage0SelectionDraftResult(
        source_manifest=result.source_manifest,
        profile_lock=result.profile_lock,
        material_bundle_summary=result.material_bundle_summary,
        phase0_ready_snapshot=result.phase0_ready_snapshot,
        contamination_guard=result.contamination_guard,
        selected_cards=result.selected_cards,
        updated_paths=tuple(updated_paths),
    )
