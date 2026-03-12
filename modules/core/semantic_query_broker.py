"""
Semantic query broker for source-backed, read-only relationship lookups.

This first batch focuses on protagonist-centric relationship questions such as
"소꿉친구", "라이벌", "멘토", and other fuzzy relation intents. Python gathers
candidate evidence from WorldState / FactLedger / DB relationship edges, then
the caller can decide how to consume the slice.
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from typing import Any

_logger = logging.getLogger(__name__)


def _normalize_attr_value(raw: Any) -> str:
    if isinstance(raw, dict):
        if "value" in raw:
            return _normalize_attr_value(raw.get("value"))
        if "desc" in raw:
            return _normalize_attr_value(raw.get("desc"))
    if isinstance(raw, list):
        return ", ".join(str(item).strip() for item in raw if str(item).strip())
    return str(raw or "").strip()


class SemanticQueryBroker:
    """Read-only broker that collects source-backed relation candidates."""

    _INTENT_SPECS: dict[str, dict[str, Any]] = {
        "childhood_friend": {
            "label": "소꿉친구",
            "aliases": [
                "소꿉친구",
                "죽마고우",
                "어릴 때부터 친구",
                "어린 시절 친구",
                "동네 친구",
                "학창 시절 친구",
            ],
            "patterns": [
                r"소꿉",
                r"죽마고우",
                r"어릴\s*때부터",
                r"어린\s*시절",
                r"동네\s*친구",
                r"학창\s*시절",
                r"같이\s*자라",
            ],
        },
        "rival": {
            "label": "라이벌",
            "aliases": ["라이벌", "숙적", "맞수", "경쟁자", "경쟁 관계"],
            "patterns": [r"라이벌", r"숙적", r"맞수", r"경쟁자", r"경쟁\s*관계"],
        },
        "mentor": {
            "label": "멘토/사부",
            "aliases": ["멘토", "스승", "사부", "은사", "사제"],
            "patterns": [r"멘토", r"스승", r"사부", r"은사", r"사제"],
        },
        "ally": {
            "label": "핵심 조력자",
            "aliases": ["조력자", "동료", "동맹", "우군", "파트너", "측근", "오른팔"],
            "patterns": [r"조력", r"동료", r"동맹", r"우군", r"파트너", r"측근", r"오른팔", r"신뢰"],
        },
        "benefactor": {
            "label": "은인",
            "aliases": ["은인", "목숨을 구해준", "빚을 진", "신세를 진"],
            "patterns": [r"은인", r"목숨.{0,8}구해", r"빚을\s*졌", r"신세를\s*졌"],
        },
        "family_like": {
            "label": "가족 같은 인물",
            "aliases": ["가족 같은", "형제 같은", "자매 같은", "식구 같은"],
            "patterns": [r"가족\s*같", r"형제\s*같", r"자매\s*같", r"식구\s*같", r"남매\s*같"],
        },
    }
    _GENERIC_WEIGHTS: tuple[tuple[str, int], ...] = (
        ("소꿉", 8),
        ("죽마고우", 8),
        ("가족", 7),
        ("은인", 7),
        ("멘토", 6),
        ("스승", 6),
        ("사부", 6),
        ("사제", 6),
        ("라이벌", 5),
        ("숙적", 5),
        ("맞수", 5),
        ("동맹", 4),
        ("동료", 4),
        ("우군", 4),
        ("신뢰", 4),
        ("측근", 4),
        ("파트너", 4),
        ("원수", 3),
        ("적대", 3),
        ("후배", 2),
        ("제자", 2),
        ("연습생", 2),
        ("배우", 1),
    )
    _GENERIC_RELATION_QUERY_HINTS = (
        "관계",
        "라인",
        "동료",
        "멘토",
        "사부",
        "후배",
        "배우",
        "연습생",
        "조력",
        "라이벌",
        "은인",
        "소꿉",
        "가족",
        "인맥",
        "문파",
    )

    def __init__(
        self,
        *,
        db=None,
        world_state=None,
        fact_ledger=None,
        state_tracker=None,
        protagonist_name: str = "",
    ) -> None:
        self.db = db
        self.world_state = world_state
        self.fact_ledger = fact_ledger
        self.state_tracker = state_tracker
        self.protagonist_name = str(protagonist_name or "").strip()

    @classmethod
    def infer_relation_intents(cls, query_text: str) -> list[str]:
        lowered = str(query_text or "").strip().lower()
        if not lowered:
            return []

        matched: list[str] = []
        for intent, spec in cls._INTENT_SPECS.items():
            aliases = [str(x).lower() for x in spec.get("aliases", [])]
            patterns = [str(x) for x in spec.get("patterns", [])]
            if any(alias and alias in lowered for alias in aliases):
                matched.append(intent)
                continue
            if any(re.search(pattern, lowered) for pattern in patterns):
                matched.append(intent)
        return matched

    @classmethod
    def should_build_relation_slice(cls, focus_text: str) -> bool:
        lowered = str(focus_text or "").strip().lower()
        if not lowered:
            return False
        if cls.infer_relation_intents(lowered):
            return True
        return any(hint in lowered for hint in cls._GENERIC_RELATION_QUERY_HINTS)

    @classmethod
    def _score_generic_text(cls, text: str) -> int:
        lowered = str(text or "").strip().lower()
        if not lowered:
            return 0
        score = 0
        for token, weight in cls._GENERIC_WEIGHTS:
            if token in lowered:
                score += weight
        return score

    @classmethod
    def _score_intent_text(cls, intent: str, text: str) -> int:
        lowered = str(text or "").strip().lower()
        if not lowered:
            return 0
        spec = cls._INTENT_SPECS.get(intent, {})
        score = 0
        for alias in spec.get("aliases", []):
            alias_text = str(alias or "").strip().lower()
            if alias_text and alias_text in lowered:
                score += 8
        for pattern in spec.get("patterns", []):
            if re.search(str(pattern), lowered):
                score += 6
        return score

    @staticmethod
    def _make_evidence(source: str, text: str, *, ep: int | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"source": source, "text": str(text or "").strip()}
        if ep is not None:
            payload["ep"] = ep
        return payload

    def _iter_world_state_evidence(self) -> list[tuple[str, dict[str, Any]]]:
        evidence_rows: list[tuple[str, dict[str, Any]]] = []
        ws = self.world_state
        if not ws:
            return evidence_rows
        try:
            state = ws.get_state_dict() if hasattr(ws, "get_state_dict") else getattr(ws, "_state", {})
        except Exception as exc:
            _logger.debug("[SemanticQueryBroker] world_state 조회 실패 (비치명): %s", exc)
            return evidence_rows
        if not isinstance(state, dict):
            return evidence_rows

        relationships = state.get("relationships", {})
        if isinstance(relationships, dict):
            for npc_name, relation in relationships.items():
                name = str(npc_name or "").strip()
                relation_text = str(relation or "").strip()
                if name and relation_text:
                    evidence_rows.append((name, self._make_evidence("world_state.relationships", relation_text)))

        alive_npcs = state.get("alive_npcs", {})
        if isinstance(alive_npcs, dict):
            for npc_name, info in alive_npcs.items():
                name = str(npc_name or "").strip()
                if not name or not isinstance(info, dict):
                    continue
                relation = str(info.get("relation", "") or "").strip()
                if relation:
                    evidence_rows.append((name, self._make_evidence("world_state.alive_npcs", relation)))
                role = str(info.get("role", "") or "").strip()
                if role:
                    evidence_rows.append((name, self._make_evidence("world_state.role", role)))
                known_attrs = info.get("known_attrs", {})
                if isinstance(known_attrs, dict):
                    relation_attr = _normalize_attr_value(known_attrs.get("relation_to_protag"))
                    if relation_attr:
                        evidence_rows.append((name, self._make_evidence("world_state.known_attrs", relation_attr)))
        return evidence_rows

    def _iter_fact_ledger_evidence(self) -> list[tuple[str, dict[str, Any]]]:
        evidence_rows: list[tuple[str, dict[str, Any]]] = []
        ledger = getattr(self.fact_ledger, "_ledger", None)
        if not isinstance(ledger, dict):
            return evidence_rows
        characters = ledger.get("characters", {})
        if not isinstance(characters, dict):
            return evidence_rows
        for npc_name, info in characters.items():
            name = str(npc_name or "").strip()
            if not name or not isinstance(info, dict):
                continue
            relationship = str(info.get("relationship", "") or "").strip()
            established_ep = info.get("established_ep")
            if relationship:
                evidence_rows.append(
                    (name, self._make_evidence("fact_ledger.relationship", relationship, ep=established_ep))
                )
            for note in info.get("history", [])[-8:]:
                note_text = str(note or "").strip()
                if not note_text:
                    continue
                ep = None
                match = re.match(r"ep(\d+):", note_text)
                if match:
                    ep = int(match.group(1))
                evidence_rows.append((name, self._make_evidence("fact_ledger.history", note_text, ep=ep)))
        return evidence_rows

    def _iter_state_tracker_evidence(self) -> list[tuple[str, dict[str, Any]]]:
        evidence_rows: list[tuple[str, dict[str, Any]]] = []
        tracker = self.state_tracker
        registry = getattr(tracker, "npc_registry", None)
        if not isinstance(registry, dict):
            return evidence_rows
        for npc_name, info in registry.items():
            name = str(npc_name or "").strip()
            if not name or not isinstance(info, dict):
                continue
            relation = str(info.get("relation_to_protag", "") or "").strip()
            if relation:
                evidence_rows.append((name, self._make_evidence("state_tracker.registry", relation)))
            role = str(info.get("role", "") or "").strip()
            if role:
                evidence_rows.append((name, self._make_evidence("state_tracker.role", role)))
        return evidence_rows

    def _iter_db_evidence(self) -> list[tuple[str, dict[str, Any]]]:
        evidence_rows: list[tuple[str, dict[str, Any]]] = []
        if not self.db or not self.protagonist_name or not hasattr(self.db, "get_npc_relationship_edges"):
            return evidence_rows
        try:
            edges = self.db.get_npc_relationship_edges(self.protagonist_name)
        except Exception as exc:
            _logger.debug("[SemanticQueryBroker] relationship edges 조회 실패 (비치명): %s", exc)
            return evidence_rows
        for edge in edges or []:
            if not isinstance(edge, dict):
                continue
            npc1 = str(edge.get("npc1", "") or "").strip()
            npc2 = str(edge.get("npc2", "") or "").strip()
            relation = str(edge.get("relation", "") or "").strip()
            if not relation:
                continue
            if npc1 == self.protagonist_name:
                other = npc2
            elif npc2 == self.protagonist_name:
                other = npc1
            else:
                continue
            if not other:
                continue
            updated_ep = edge.get("updated_ep")
            evidence_rows.append((other, self._make_evidence("db.relationship_edge", relation, ep=updated_ep)))
            if hasattr(self.db, "get_relationship_history"):
                try:
                    history = self.db.get_relationship_history(self.protagonist_name, other, limit=5)
                except Exception as exc:
                    _logger.debug("[SemanticQueryBroker] relationship history 조회 실패 (비치명): %s", exc)
                    history = []
                for row in history or []:
                    if not isinstance(row, dict):
                        continue
                    old_relation = str(row.get("old_relation", "") or "").strip()
                    new_relation = str(row.get("new_relation", "") or "").strip()
                    change_ep = row.get("change_ep")
                    text = f"{old_relation} -> {new_relation}".strip(" ->")
                    if text:
                        evidence_rows.append((other, self._make_evidence("db.relationship_history", text, ep=change_ep)))
        return evidence_rows

    def _collect_candidates(self) -> dict[str, dict[str, Any]]:
        candidates: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"name": "", "generic_score": 0, "evidences": [], "source_counts": defaultdict(int)}
        )

        for npc_name, evidence in (
            self._iter_world_state_evidence()
            + self._iter_fact_ledger_evidence()
            + self._iter_state_tracker_evidence()
            + self._iter_db_evidence()
        ):
            name = str(npc_name or "").strip()
            if not name or name == self.protagonist_name:
                continue
            text = str(evidence.get("text", "") or "").strip()
            if not text:
                continue
            bucket = candidates[name]
            bucket["name"] = name
            bucket["generic_score"] += self._score_generic_text(text)
            bucket["evidences"].append(evidence)
            bucket["source_counts"][str(evidence.get("source", ""))] += 1

        return candidates

    def get_key_relationship_candidates(self, limit: int = 4) -> list[dict[str, Any]]:
        candidates = self._collect_candidates()
        scored: list[dict[str, Any]] = []
        for info in candidates.values():
            evidence_count = len(info["evidences"])
            source_count = len(info["source_counts"])
            score = int(info["generic_score"]) + evidence_count + (source_count * 2)
            if score <= 0:
                continue
            rendered_sources = sorted(info["source_counts"].keys())[:4]
            preview_evidence = info["evidences"][:3]
            scored.append(
                {
                    "name": info["name"],
                    "score": score,
                    "sources": rendered_sources,
                    "evidences": preview_evidence,
                }
            )

        scored.sort(key=lambda row: (-int(row["score"]), row["name"]))
        return scored[:limit]

    def answer_relation_intent(self, intent: str, limit: int = 3) -> dict[str, Any]:
        spec = self._INTENT_SPECS.get(intent)
        if not spec:
            return {}
        candidates = self._collect_candidates()
        scored: list[dict[str, Any]] = []
        for info in candidates.values():
            intent_score = 0
            matched_evidence = []
            for evidence in info["evidences"]:
                text = str(evidence.get("text", "") or "").strip()
                score = self._score_intent_text(intent, text)
                if score > 0:
                    intent_score += score
                    matched_evidence.append(evidence)
            if intent_score <= 0:
                continue
            scored.append(
                {
                    "name": info["name"],
                    "score": intent_score + len(matched_evidence),
                    "sources": sorted({e["source"] for e in matched_evidence})[:4],
                    "evidences": matched_evidence[:3],
                }
            )
        scored.sort(key=lambda row: (-int(row["score"]), row["name"]))
        return {
            "intent": intent,
            "label": str(spec.get("label", intent)),
            "candidates": scored[:limit],
        }

    def build_relation_slice(
        self,
        *,
        focus_text: str,
        max_chars: int = 700,
        header: str = "[관계 의미 질의]",
    ) -> str:
        if not self.protagonist_name:
            return ""
        if not self.should_build_relation_slice(focus_text):
            return ""

        lines = [header]
        key_candidates = self.get_key_relationship_candidates(limit=3)
        if key_candidates:
            rendered = []
            for candidate in key_candidates:
                source_hint = "/".join(candidate.get("sources", [])[:2])
                rendered.append(f"{candidate['name']}({source_hint})")
            lines.append(f"- 핵심 관계 후보: {', '.join(rendered)}")

        for intent in self.infer_relation_intents(focus_text)[:2]:
            answer = self.answer_relation_intent(intent, limit=2)
            candidates = answer.get("candidates", [])
            if not candidates:
                continue
            rendered_candidates = []
            for candidate in candidates:
                evidence_texts = []
                for evidence in candidate.get("evidences", [])[:2]:
                    snippet = str(evidence.get("text", "") or "").strip()
                    snippet = snippet[:36] + "..." if len(snippet) > 39 else snippet
                    evidence_texts.append(f"{evidence.get('source', '?')}={snippet}")
                rendered_candidates.append(
                    f"{candidate['name']} [{'; '.join(evidence_texts)}]"
                )
            lines.append(f"- {answer['label']} 후보: {', '.join(rendered_candidates)}")

        if len(lines) <= 1:
            return ""
        block = "\n".join(lines)
        if len(block) > max_chars:
            block = block[: max_chars - 18] + "\n... (관계 질의 절삭)"
        return block

    def build_stage4_relation_slice(
        self,
        *,
        focus_text: str,
        max_chars: int = 700,
    ) -> str:
        return self.build_relation_slice(
            focus_text=focus_text,
            max_chars=max_chars,
            header="[관계 의미 질의]",
        )
