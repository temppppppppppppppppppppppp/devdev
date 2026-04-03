"""
Stage 4 Immutable Fact Contract — shared packet substrate.

Builds one normalized immutable-fact packet per attempt family and exposes
compact helpers for violation classification and rewrite escalation.

Design constraints (from execution SSOT):
- packet is derived-only — never becomes a new authority owner
- Director remains final judge
- no new DB schema in this wave
- no global caches for packet state
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

_logger = logging.getLogger(__name__)

# ── Violation family vocabulary ──────────────────────────────────

VIOLATION_OPENING_ANCHOR_DRIFT = "opening_anchor_drift"
VIOLATION_COMMITTED_STATE_REGRESSION = "committed_state_regression"
VIOLATION_COMPLETED_EVENT_REPLAY = "completed_event_replay"
VIOLATION_SCENE_OBLIGATION_MISSING = "scene_obligation_missing"
VIOLATION_SCENE_ORDER_DRIFT = "scene_order_drift"
VIOLATION_METADATA_REFERENCE_SHAPE = "metadata_reference_shape_violation"

_HARD_FACT_FAMILIES = frozenset(
    {
        VIOLATION_OPENING_ANCHOR_DRIFT,
        VIOLATION_COMMITTED_STATE_REGRESSION,
        VIOLATION_COMPLETED_EVENT_REPLAY,
    }
)

_REWRITE_BIASED_FAMILIES = frozenset(
    {
        VIOLATION_OPENING_ANCHOR_DRIFT,
        VIOLATION_COMMITTED_STATE_REGRESSION,
        VIOLATION_COMPLETED_EVENT_REPLAY,
        VIOLATION_SCENE_ORDER_DRIFT,
    }
)


# ── Data structures ──────────────────────────────────────────────


@dataclass(frozen=True)
class SceneObligation:
    """One row of scene-level must/must-not obligations."""

    scene_key: str
    title: str = ""
    goal: str = ""
    location: str = ""
    must_materialize: str = ""
    must_not_erase: str = ""


@dataclass
class ImmutableFactPacket:
    """Normalized immutable-fact contract built once per attempt family."""

    # 1. opening anchor
    start_location: str = ""
    start_time_flow: str = ""
    scene_1_title: str = ""
    scene_1_location: str = ""
    prev_ending_bridge: str = ""
    carryover_cliffhanger: str = ""
    carryover_pending_actions: str = ""
    carryover_location: str = ""
    carryover_time_marker: str = ""

    # 2. committed state facts
    committed_state_facts: list[str] = field(default_factory=list)

    # 3. completed event facts
    completed_event_facts: list[str] = field(default_factory=list)

    # 4. scene obligations
    scene_obligations: list[SceneObligation] = field(default_factory=list)

    # 5. repair policy hints
    patch_friendly_families: list[str] = field(default_factory=list)
    rewrite_biased_families: list[str] = field(default_factory=list)

    # 6. upstream contract flags
    prior_arc_recovery_open: bool = False
    blueprint_metadata_complete: bool = True

    # 7. sink normalization rules (static)
    scalar_only_sink_fields: tuple[str, ...] = ("npc", "target", "to", "from")

    def is_empty(self) -> bool:
        return not (
            self.start_location
            or self.start_time_flow
            or self.scene_1_location
            or self.prev_ending_bridge
            or self.carryover_cliffhanger
            or self.carryover_pending_actions
            or self.carryover_location
            or self.carryover_time_marker
            or self.committed_state_facts
            or self.completed_event_facts
            or self.scene_obligations
        )


# ── Packet building ──────────────────────────────────────────────


def build_packet(
    *,
    blueprint: dict | None = None,
    prev_manuscript_ending: str = "",
    world_state_summary: str = "",
    fact_ledger_summary: str = "",
    chain_link_section: str = "",
    prev_digest: str = "",
) -> ImmutableFactPacket:
    """Build one immutable fact packet from already-available Stage 4 inputs.

    The packet is derived data — it compiles facts that already exist in
    blueprint, prior manuscript, world state, and fact ledger into one
    normalized object.
    """
    bp = blueprint if isinstance(blueprint, dict) else {}
    packet = ImmutableFactPacket()

    # ── 1. Opening anchor ────────────────────────────────────────
    packet.start_location = str(bp.get("start_location", "") or "").strip()
    packet.start_time_flow = str(bp.get("time_flow", "") or "").strip()

    scenes = bp.get("scene_breakdown", {})
    if isinstance(scenes, dict) and scenes:
        scene_1 = scenes.get("scene_1") or next(iter(scenes.values()), {})
        if isinstance(scene_1, dict):
            packet.scene_1_title = str(scene_1.get("title", "") or "").strip()
            packet.scene_1_location = str(scene_1.get("location", "") or "").strip()

    if prev_manuscript_ending:
        packet.prev_ending_bridge = prev_manuscript_ending[-500:]
    _extract_chain_link_carryover(packet, chain_link_section)

    # ── 2. Committed state facts ─────────────────────────────────
    _extract_committed_state_facts(packet, world_state_summary, fact_ledger_summary)

    # ── 3. Completed event facts ─────────────────────────────────
    _extract_completed_event_facts(packet, prev_digest, chain_link_section)

    # ── 4. Scene obligations ─────────────────────────────────────
    _extract_scene_obligations(packet, bp)

    # ── 5. Repair policy hints ───────────────────────────────────
    packet.patch_friendly_families = [
        VIOLATION_SCENE_OBLIGATION_MISSING,
    ]
    packet.rewrite_biased_families = list(_REWRITE_BIASED_FAMILIES)

    # ── 6. Upstream contract flags ───────────────────────────────
    _check_upstream_flags(packet, bp)

    return packet


def _extract_chain_link_carryover(packet: ImmutableFactPacket, chain_link_section: str) -> None:
    if not chain_link_section:
        return
    for raw_line in str(chain_link_section).splitlines():
        line = raw_line.strip()
        if not line.startswith("- carryover_"):
            continue
        key, _, value = line[2:].partition(":")
        normalized_value = " ".join(str(value).split()).strip()
        if not normalized_value:
            continue
        if key == "carryover_cliffhanger":
            packet.carryover_cliffhanger = normalized_value
        elif key == "carryover_pending_actions":
            packet.carryover_pending_actions = normalized_value
        elif key == "carryover_location":
            packet.carryover_location = normalized_value
        elif key == "carryover_time_marker":
            packet.carryover_time_marker = normalized_value


def _extract_committed_state_facts(
    packet: ImmutableFactPacket,
    world_state_summary: str,
    fact_ledger_summary: str,
) -> None:
    """Extract committed state facts from world state and fact ledger summaries."""
    facts: list[str] = []

    if fact_ledger_summary:
        for line in fact_ledger_summary.split("\n"):
            line = line.strip()
            if line.startswith("-") and any(
                kw in line
                for kw in (
                    "억", "만원", "원", "달러", "$", "계좌", "자본", "잔고", "자산",
                    "capital", "won", "balance", "account", "fund",
                    "소유", "법인", "개인", "명의", "보유", "활동중",
                )
            ):
                facts.append(line.lstrip("- ").strip())

    if world_state_summary:
        for line in world_state_summary.split("\n"):
            line = line.strip()
            if line.startswith("-") and any(
                kw in line for kw in ("사망", "deceased", "부상", "관계:", "소지품", "보유")
            ):
                facts.append(line.lstrip("- ").strip())

    packet.committed_state_facts = facts[:20]


def _extract_completed_event_facts(
    packet: ImmutableFactPacket,
    prev_digest: str,
    chain_link_section: str,
) -> None:
    """Extract completed-event facts from digest and chain link."""
    events: list[str] = []

    for source in (prev_digest, chain_link_section):
        if not source:
            continue
        for line in source.split("\n"):
            line = line.strip()
            if line.startswith("-") and any(
                kw in line
                for kw in (
                    "완료",
                    "달성",
                    "처단",
                    "사망",
                    "획득",
                    "습득",
                    "돌파",
                    "성공",
                    "해결",
                    "종결",
                    "개설",
                    "구축",
                    "이체",
                    "계약",
                    "세팅",
                    "수령",
                    "발급",
                    "설립",
                    "입주",
                    "확인",
                )
            ):
                events.append(line.lstrip("- ").strip())

    packet.completed_event_facts = events[:15]


def _extract_scene_obligations(packet: ImmutableFactPacket, bp: dict) -> None:
    """Extract per-scene obligations from blueprint scene_breakdown."""
    scenes = bp.get("scene_breakdown", {})
    if not isinstance(scenes, dict):
        return

    obligations: list[SceneObligation] = []
    for key, scene in scenes.items():
        if not isinstance(scene, dict):
            continue
        obligations.append(
            SceneObligation(
                scene_key=str(key),
                title=str(scene.get("title", "") or "").strip(),
                goal=str(scene.get("goal", "") or scene.get("summary", "") or "").strip(),
                location=str(scene.get("location", "") or "").strip(),
                must_materialize=str(scene.get("must_materialize", "") or scene.get("goal", "") or "").strip(),
                must_not_erase=str(scene.get("must_not_erase", "") or "").strip(),
            )
        )

    packet.scene_obligations = obligations


def _check_upstream_flags(packet: ImmutableFactPacket, bp: dict) -> None:
    """Check upstream contract completeness flags."""
    scenes = bp.get("scene_breakdown", {})
    if isinstance(scenes, dict):
        missing_metadata = 0
        for scene in scenes.values():
            if isinstance(scene, dict):
                if not (scene.get("goal") or scene.get("summary")):
                    missing_metadata += 1
        if missing_metadata > 0:
            packet.blueprint_metadata_complete = False


# ── Violation classification ─────────────────────────────────────


def classify_violation_family(
    *,
    rejection_reason: str = "",
    fix_pack: dict | None = None,
    patch_targets_empty: bool = False,
) -> list[str]:
    """Classify rejection into explicit violation families.

    Returns a list of violation family strings from the shared vocabulary.
    """
    families: list[str] = []
    reason_lower = (rejection_reason or "").lower()

    # opening anchor drift
    if any(
        kw in reason_lower
        for kw in (
            "시작 장소",
            "시작 위치",
            "opening",
            "start_location",
            "첫 씬 장소",
            "오프닝",
            "시간대 불일치",
            "time_flow",
        )
    ):
        families.append(VIOLATION_OPENING_ANCHOR_DRIFT)

    # committed state regression
    if any(
        kw in reason_lower
        for kw in (
            "수치 모순",
            "금액",
            "자본",
            "잔고",
            "state drift",
            "state regression",
            "상태 모순",
            "numeric",
            "balance",
            "capital",
        )
    ):
        families.append(VIOLATION_COMMITTED_STATE_REGRESSION)

    # completed event replay
    if any(
        kw in reason_lower
        for kw in (
            "이미 완료",
            "already completed",
            "중복 서술",
            "replay",
            "반복",
            "이미 끝난",
            "이미 해결",
        )
    ):
        families.append(VIOLATION_COMPLETED_EVENT_REPLAY)

    # scene obligation missing
    if any(
        kw in reason_lower
        for kw in (
            "씬 완성도",
            "씬 누락",
            "scene missing",
            "scene completeness",
            "0/",
            "씬만 완성",
        )
    ):
        families.append(VIOLATION_SCENE_OBLIGATION_MISSING)

    # scene order drift
    if any(
        kw in reason_lower
        for kw in (
            "씬 순서",
            "scene order",
            "scene sequence",
            "장면 순서",
        )
    ):
        families.append(VIOLATION_SCENE_ORDER_DRIFT)

    # metadata reference shape violation
    if any(
        kw in reason_lower
        for kw in (
            "unhashable",
            "dict witness",
            "metadata shape",
            "reference shape",
        )
    ):
        families.append(VIOLATION_METADATA_REFERENCE_SHAPE)

    # fix_pack heuristic
    if isinstance(fix_pack, dict):
        fp_text = " ".join(str(v) for v in fix_pack.values() if v).lower()
        if "opening" in fp_text or "시작 장소" in fp_text:
            if VIOLATION_OPENING_ANCHOR_DRIFT not in families:
                families.append(VIOLATION_OPENING_ANCHOR_DRIFT)
        if any(kw in fp_text for kw in ("자본", "금액", "수치")):
            if VIOLATION_COMMITTED_STATE_REGRESSION not in families:
                families.append(VIOLATION_COMMITTED_STATE_REGRESSION)

    # empty patch targets alone is not enough to infer a violation family —
    # only promote if there is at least SOME textual evidence of hard-fact drift
    # (removed overly aggressive fallback that assumed state regression from empty patches alone)

    return families


# ── Rewrite escalation ───────────────────────────────────────────


def should_escalate_to_rewrite(
    *,
    violation_families: list[str],
    patch_targets_empty: bool = False,
    consecutive_empty_patches: int = 0,
) -> bool:
    """Determine if the retry path should escalate to rewrite-biased regeneration.

    Rules (from design doc):
    1. If violation family is hard fact drift AND patch targets are weak/empty → escalate
    2. If consecutive empty patch rounds >= 2 → escalate
    3. If scene-model obligation is broken broadly → escalate
    """
    has_hard_fact_family = any(family in _HARD_FACT_FAMILIES for family in violation_families)
    has_rewrite_biased = any(family in _REWRITE_BIASED_FAMILIES for family in violation_families)

    # Rule 1: hard fact + empty patches
    if has_hard_fact_family and patch_targets_empty:
        return True

    # Rule 2: consecutive empty patches (plateau)
    if consecutive_empty_patches >= 2:
        return True

    # Rule 3: broad scene obligation failure
    if VIOLATION_SCENE_OBLIGATION_MISSING in violation_families and VIOLATION_SCENE_ORDER_DRIFT in violation_families:
        return True

    # Rule 4: rewrite-biased + two or more consecutive empties
    if has_rewrite_biased and consecutive_empty_patches >= 1:
        return True

    return False


# ── Actor reference normalization (Tranche 8 substrate) ──────────


def normalize_actor_reference(value: Any) -> str:
    """Normalize an actor reference to a stable scalar string.

    Rich dict witnesses must be scalarized before reaching WorldState or
    FactLedger persistence sinks. This normalizer extracts the best scalar
    name from whatever shape the producer emitted.
    """
    if isinstance(value, str):
        return value.strip()

    if isinstance(value, dict):
        # Try common name keys in priority order
        for key in ("name", "npc", "target", "actor", "character"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        # Last resort: first string value
        for v in value.values():
            if isinstance(v, str) and v.strip():
                return v.strip()
        _logger.warning("[IFC] dict actor ref could not be scalarized: %s", value)
        return str(value)

    if isinstance(value, (list, tuple)) and value:
        first = value[0]
        if isinstance(first, str):
            return first.strip()
        return normalize_actor_reference(first)

    return str(value).strip() if value else ""


def normalize_relationship_changes(changes: list) -> list[dict]:
    """Normalize relationship_changes list so all actor refs are scalar strings.

    This is the producer-side normalization gate before metadata persistence.
    """
    if not isinstance(changes, list):
        return []

    normalized: list[dict] = []
    for rel in changes:
        if not isinstance(rel, dict):
            continue
        npc_raw = rel.get("npc") or rel.get("target") or ""
        npc = normalize_actor_reference(npc_raw)
        if not npc:
            continue

        to_raw = rel.get("to", "")
        to_val = normalize_actor_reference(to_raw) if isinstance(to_raw, dict) else str(to_raw or "").strip()
        from_raw = rel.get("from", "")
        from_val = normalize_actor_reference(from_raw) if isinstance(from_raw, dict) else str(from_raw or "").strip()

        normalized.append({"npc": npc, "to": to_val, "from": from_val})

    return normalized


# ── Prompt rendering ─────────────────────────────────────────────


def render_packet_for_cw(packet: ImmutableFactPacket) -> str:
    """Render the immutable fact packet as a CW prompt section.

    This section is injected ahead of softer context and states clearly
    that packet facts override local plausibility improvisation.
    """
    if packet.is_empty():
        return ""

    lines: list[str] = [
        "### [IFC] 불변 사실 계약 (Immutable Fact Contract)",
        "아래 사실은 이 화의 절대 불변 조건입니다. 창작적 판단으로 변경할 수 없습니다.",
        "불변 사실과 로컬 개연성이 충돌하면, 불변 사실이 우선합니다.",
        "자체적으로 모순을 수정하지 말고, 모순이 보이면 그대로 표면화하세요.",
        "",
    ]

    # Opening anchor
    if packet.start_location or packet.start_time_flow:
        lines.append("#### 1. 시작 계약 (Opening Anchor)")
        if packet.start_location:
            lines.append(f"- 시작 장소: {packet.start_location}")
        if packet.scene_1_location and packet.scene_1_location != packet.start_location:
            lines.append(f"- 첫 씬 세부 장소: {packet.scene_1_location}")
        if packet.start_time_flow:
            lines.append(f"- 시간대: {packet.start_time_flow}")
        if packet.scene_1_title:
            lines.append(f"- 첫 씬 제목: {packet.scene_1_title}")
        if packet.prev_ending_bridge:
            bridge_excerpt = " ".join(str(packet.prev_ending_bridge).split())
            if len(bridge_excerpt) > 260:
                bridge_excerpt = bridge_excerpt[:257] + "..."
            lines.append(f"- 직전 화 종료 브리지: {bridge_excerpt}")
        if packet.carryover_cliffhanger:
            lines.append(f"- carryover cliffhanger to resolve or explicitly transition from: {packet.carryover_cliffhanger}")
        if packet.carryover_location:
            lines.append(f"- carryover location to honor or explicitly transition from: {packet.carryover_location}")
        if packet.carryover_time_marker:
            lines.append(f"- carryover time_marker to honor or explicitly advance from: {packet.carryover_time_marker}")
        if packet.carryover_pending_actions:
            lines.append(
                "- carryover pending_actions to resolve before new thread or explicitly transition away: "
                f"{packet.carryover_pending_actions}"
            )
        lines.append(
            "- 다른 장소/시간 또는 다른 시점 opening이 필요하면 전환 문장이나 `* * *` 후 1~2문장 안에 바뀐 장소/시간/행동 상태를 명시하세요."
        )
        lines.append("⛔ 위 anchor를 무전환으로 덮어쓰거나, 직전 화에서 이미 끝난 행동을 opening에서 다시 재연하면 즉시 불합격.")
        lines.append("")

    # Committed state facts
    if packet.committed_state_facts:
        lines.append("#### 2. 확정 상태 사실 (Committed State)")
        for fact in packet.committed_state_facts[:15]:
            lines.append(f"- {fact}")
        lines.append("⛔ 위 수치/상태를 임의로 변경하면 즉시 불합격.")
        lines.append("")

    # Completed event facts
    if packet.completed_event_facts:
        lines.append("#### 3. 완료된 사건 (Completed Events)")
        for event in packet.completed_event_facts[:10]:
            lines.append(f"- {event}")
        lines.append("⛔ 이미 끝난 사건을 미해결인 것처럼 다시 서술하면 불합격.")
        lines.append("")

    # Scene obligations
    if packet.scene_obligations:
        lines.append("#### 4. 씬별 의무 (Scene Obligations)")
        for ob in packet.scene_obligations:
            parts = [f"**{ob.scene_key}**"]
            if ob.title:
                parts.append(f"제목={ob.title}")
            if ob.goal:
                parts.append(f"목표={ob.goal}")
            if ob.location:
                parts.append(f"장소={ob.location}")
            lines.append(f"- {' | '.join(parts)}")
        lines.append("⛔ 위 씬을 누락하거나 순서를 바꾸면 불합격.")
        lines.append("")

    # Upstream flags
    if not packet.blueprint_metadata_complete:
        lines.append("⚠️ Blueprint 일부 씬에 goal/summary 메타데이터가 불완전합니다.")
        lines.append("   가능한 한 씬 제목과 맥락에서 의도를 추론하되, 확신 없으면 표면화하세요.")
        lines.append("")

    return "\n".join(lines)


def render_violation_summary(violation_families: list[str]) -> str:
    """Render violation families as a compact operator-facing string."""
    if not violation_families:
        return ""
    _labels = {
        VIOLATION_OPENING_ANCHOR_DRIFT: "시작계약위반",
        VIOLATION_COMMITTED_STATE_REGRESSION: "확정상태회귀",
        VIOLATION_COMPLETED_EVENT_REPLAY: "완료사건반복",
        VIOLATION_SCENE_OBLIGATION_MISSING: "씬의무누락",
        VIOLATION_SCENE_ORDER_DRIFT: "씬순서이탈",
        VIOLATION_METADATA_REFERENCE_SHAPE: "메타데이터형식위반",
    }
    return " / ".join(_labels.get(f, f) for f in violation_families)
