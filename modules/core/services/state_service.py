"""[Phase 4B-3] StateService — validation/pattern helper service

원본: main_a.py:2707-3132 (14개 메서드, ~345줄)

NOTE:
- 이 구현체는 PromptBuilder/FeedbackSystem 기반 helper 묶음이다.
- `modules/protocols/app_services.py::StateServiceProtocol`은 `StateTracker` facade surface를
  모델링하며, 본 helper service의 conform target이 아니다.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from modules.core.constants import Emojis, GenreTypes, Stage2Limits, VolumeSettings


class StateService:
    """검증/패턴/아키타입 헬퍼 서비스.

    Args:
        ui: StudioVisualizer 인스턴스
        audit_event_fn: _audit_event 콜백
        genre_fn: () -> selected_genre dict 또는 None
        prompt_builder: PromptBuilder 인스턴스
        feedback_system: FeedbackSystem 인스턴스
    """

    def __init__(
        self,
        ui: Any,
        audit_event_fn: Callable,
        genre_fn: Callable[[], Any],
        prompt_builder: Any,
        feedback_system: Any,
    ) -> None:
        self._ui = ui
        self._audit_event = audit_event_fn
        self._genre_fn = genre_fn
        self._prompt_builder = prompt_builder
        self._feedback_system = feedback_system

    # ── extract_block_index ──────────────────────────────────────
    def extract_block_index(self, block_id: Any) -> int | None:
        """블록 ID 문자열에서 인덱스 번호 추출. 원본: main_a.py:2707"""
        if not isinstance(block_id, str):
            return None
        match = re.search(r"Block\s+(\d+)", block_id)
        if not match:
            return None
        try:
            return int(match.group(1))
        except ValueError:
            return None

    # ── validate_arc_mapping ─────────────────────────────────────
    def validate_arc_mapping(self, refined_arc, enriched_block, expected_arc_no, expected_ep_start):
        """아크 매핑 검증/보정. 원본: main_a.py:2727"""
        if not refined_arc or not isinstance(refined_arc, dict):
            return refined_arc

        if refined_arc.get("arc_no") != expected_arc_no:
            self._ui.log(f"⚠️ [Mapping] arc_no 불일치: {refined_arc.get('arc_no')} -> {expected_arc_no} (보정)")
            self._audit_event(
                "mapping_fix", "arc_no mismatch", {"original": refined_arc.get("arc_no"), "expected": expected_arc_no}
            )
            refined_arc["arc_no"] = expected_arc_no

        # [Sweep11] ep_end를 ep_count 대용으로 쓰면 절대값→카운트 혼동 → 과팽창
        ep_count = refined_arc.get("ep_count")
        if not isinstance(ep_count, int):
            try:
                ep_count = int(ep_count) if ep_count and not isinstance(ep_count, dict | list) else Stage2Limits.DEFAULT_EP_COUNT
            except (ValueError, TypeError):
                ep_count = Stage2Limits.DEFAULT_EP_COUNT
        if refined_arc.get("ep_start") != expected_ep_start:
            self._ui.log(f"⚠️ [Mapping] ep_start 불일치: {refined_arc.get('ep_start')} -> {expected_ep_start} (보정)")
            self._audit_event(
                "mapping_fix",
                "ep_start mismatch",
                {"original": refined_arc.get("ep_start"), "expected": expected_ep_start},
            )
            refined_arc["ep_start"] = expected_ep_start
        refined_arc["ep_end"] = expected_ep_start + int(ep_count) - 1

        block_id = None
        if isinstance(enriched_block, dict):
            block_id = enriched_block.get("block_id") or enriched_block.get("id")
        block_index = self.extract_block_index(block_id)
        if block_index is not None and block_index != expected_arc_no:
            self._ui.log(f"⚠️ [Mapping] 블록 인덱스 불일치: {block_id} (arc {expected_arc_no})")
            refined_arc["mapping_warning"] = f"block_id={block_id} vs arc_no={expected_arc_no}"
            self._audit_event("mapping_warning", "block_id mismatch", {"block_id": block_id, "arc_no": expected_arc_no})

        return refined_arc

    # ── extract_pattern_keywords ─────────────────────────────────
    def extract_pattern_keywords(self, pattern_profile):
        """패턴 프로필에서 키워드 추출. 원본: main_a.py:2769"""
        if not isinstance(pattern_profile, dict):
            return []
        keywords = []
        primary = pattern_profile.get("primary", "")
        secondary = pattern_profile.get("secondary", [])
        raw_items = []
        if isinstance(primary, str) and primary.strip():
            raw_items.append(primary)
        if isinstance(secondary, list):
            raw_items.extend([s for s in secondary if isinstance(s, str)])
        for item in raw_items:
            core = re.sub(r"\([^)]*\)", "", item).strip()
            parts = re.split(r"[\s/]+", core)
            keywords.extend([p for p in parts if len(p) >= 2])
        return list(dict.fromkeys(keywords))

    # ── pattern_presence_check ───────────────────────────────────
    def pattern_presence_check(self, text, pattern_profile, min_hits=1):
        """텍스트에서 패턴 존재 확인. 원본: main_a.py:2788"""
        if not isinstance(text, str) or not text.strip():
            return False
        keywords = self.extract_pattern_keywords(pattern_profile)
        if not keywords:
            return True
        hits = sum(1 for k in keywords if k in text)
        return hits >= min_hits

    # ── build_validation_context (thin → PromptBuilder) ──────────
    def build_validation_context(
        self, ep_num: int, blueprint: dict = None, mode: str = "MANUSCRIPT", blueprint_text: str = ""
    ) -> dict:
        """[V64 P2-2] → PromptBuilder. 원본: main_a.py:2801"""
        return self._prompt_builder.build_validation_context(ep_num, blueprint, mode, blueprint_text)

    # ── extract_npc_profiles (thin → PromptBuilder) ──────────────
    def extract_npc_profiles(self, arc_data: dict) -> dict:
        """[V64 P2-2] → PromptBuilder. 원본: main_a.py:2811"""
        return self._prompt_builder.extract_npc_profiles(arc_data)

    # ── get_character_traits (thin → PromptBuilder) ──────────────
    def get_character_traits(self) -> dict:
        """[V64 P2-2] → PromptBuilder. 원본: main_a.py:2815"""
        return self._prompt_builder.get_character_traits()

    # ── load_character_archetypes ────────────────────────────────
    def load_character_archetypes(self, genre: str = "wuxia") -> dict:
        """장르별 캐릭터 아키타입 JSON 로드. 원본: main_a.py:2819"""
        archetypes = {}
        try:
            archetype_path = Path("modules/core/laws/archetypes") / f"{genre}.json"
            if archetype_path.exists():
                archetypes = json.loads(archetype_path.read_text(encoding="utf-8"))
        except Exception as e:
            logging.warning("[StateService] load_character_archetypes 실패: %s", e)  # [TF-11-12]
        return archetypes

    # ── get_archetype_reference_for_npcs ─────────────────────────
    def get_archetype_reference_for_npcs(self, npc_profiles: dict, genre: str = "wuxia") -> str:
        """NPC 프로필에 맞는 아키타입 참고 자료 생성. 원본: main_a.py:2830"""
        if not npc_profiles:
            return ""

        archetypes = self.load_character_archetypes(genre)
        if not archetypes:
            return ""

        reference_lines = [
            "[📚 캐릭터 아키타입 참고 자료]",
            "등장 NPC들의 유형입니다. 참고하되 변주는 자유롭게 하십시오.",
            "",
        ]

        for npc_name, npc_data in npc_profiles.items():
            npc_role = npc_data.get("role", "") or npc_data.get("Role", "")
            npc_archetype = npc_data.get("archetype", "")

            role_lower = npc_role.lower() if npc_role else ""
            archetype_info = None

            if "히로인" in role_lower or "heroine" in role_lower or "여주" in role_lower:
                category = "supporter"
                subcategory = "heroine"
            elif "스승" in role_lower or "mentor" in role_lower or "사부" in role_lower:
                category = "mentor"
                subcategory = "master"
            elif "적" in role_lower or "악당" in role_lower or "antagonist" in role_lower:
                category = "antagonist"
                subcategory = "rival"
            elif "제자" in role_lower or "수혜" in role_lower:
                category = "beneficiary"
                subcategory = "disciple"
            elif "장로" in role_lower or "검증" in role_lower:
                category = "validator"
                subcategory = "authority"
            else:
                category = None
                subcategory = None

            if category and subcategory:
                cat_data = archetypes.get(category, {})
                subcat_data = cat_data.get(subcategory, {})

                if npc_archetype and npc_archetype in subcat_data:
                    archetype_info = subcat_data[npc_archetype]
                    archetype_name = npc_archetype
                elif subcat_data:
                    for key, val in subcat_data.items():
                        if not key.startswith("_") and isinstance(val, dict):
                            archetype_info = val
                            archetype_name = key
                            break

            if archetype_info:
                traits = archetype_info.get("core_traits", [])
                speech = archetype_info.get("speech", "")
                forbidden = archetype_info.get("forbidden", [])

                reference_lines.append(f"- **{npc_name}**: '{archetype_name}' 유형")
                if traits:
                    reference_lines.append(f"  - 핵심 특성: {', '.join(traits[:4])}")
                if speech:
                    reference_lines.append(f"  - 말투: {speech[:50]}...")
                if forbidden:
                    reference_lines.append(f"  - 금기: {', '.join(forbidden[:3])}")
                reference_lines.append("")

        if len(reference_lines) <= 3:
            return ""

        return "\n".join(reference_lines)

    # ── classify_rejection_feedback (thin → FeedbackSystem) ──────
    def classify_rejection_feedback(self, reason: str, feedback: str, blueprint: dict = None) -> str:
        """[V64 P2-3] → FeedbackSystem. 원본: main_a.py:2909"""
        return self._feedback_system.classify_rejection_feedback(reason, feedback, blueprint)

    # ── validate_arc_data_fields ─────────────────────────────────
    def validate_arc_data_fields(self, arc_data: dict, arc_idx: int) -> dict | None:
        """[V43] arc_data 필수 필드 검증 및 자동 복구. 원본: main_a.py:2974"""
        if not isinstance(arc_data, dict):
            self._ui.log(f"🚨 [V43] arc_data가 딕셔너리가 아닙니다: {type(arc_data)}")
            return None

        required_defaults = {
            "tactical_doc": "",
            "beat_sequence": [],
            "joint_docs": {},
            "status_shadow": {},
            "arc_drive": {},
            "hybrid_composition": {"primary": "standard", "secondary": [], "mixing_logic": "기본"},
            "ep_count": arc_data.get("ep_count", VolumeSettings.EPISODES_PER_ARC),
            # [Codex-fix] LLM이 string 반환 시 TypeError 방지
            "ep_end": int(arc_data.get("ep_start", 1))
            + int(arc_data.get("ep_count", VolumeSettings.EPISODES_PER_ARC))
            - 1,
        }

        repaired = False
        for field, default_val in required_defaults.items():
            current_val = arc_data.get(field)

            if current_val is None:
                arc_data[field] = default_val
                self._ui.log(f"   ⚠️ [V43] Arc {arc_idx}: {field} 누락 → 기본값 주입")
                self._audit_event("field_repair", f"{field} missing", {"arc_idx": arc_idx})
                repaired = True
            elif isinstance(default_val, dict) and not isinstance(current_val, dict):
                arc_data[field] = default_val
                self._ui.log(f"   ⚠️ [V43] Arc {arc_idx}: {field} 타입 오류 → dict로 복구")
                repaired = True
            elif isinstance(default_val, list) and not isinstance(current_val, list):
                arc_data[field] = default_val
                self._ui.log(f"   ⚠️ [V43] Arc {arc_idx}: {field} 타입 오류 → list로 복구")
                repaired = True
            elif isinstance(default_val, str) and not isinstance(current_val, str):
                arc_data[field] = str(current_val) if current_val else default_val
                self._ui.log(f"   ⚠️ [V43] Arc {arc_idx}: {field} 타입 오류 → str로 변환")
                repaired = True

        if repaired:
            self._ui.log(f"   🔧 [V43] Arc {arc_idx} 데이터 복구 완료")

        return arc_data

    # ── load_genre_references ────────────────────────────────────
    def load_genre_references(self) -> tuple[list, list]:
        """장르별 레퍼런스 데이터 로드. 원본: main_a.py:3030"""
        seeds_path = Path("modules/core/laws/seeds")
        selected_genre = self._genre_fn()
        genre_type = selected_genre.get("type", GenreTypes.WUXIA) if selected_genre else GenreTypes.WUXIA

        cliche_data = []
        location_data = []

        try:
            cliche_file = seeds_path / f"cliche_pool_{genre_type}.json"
            if not cliche_file.exists():
                cliche_file = seeds_path / "cliche_pool.json"

            location_file = seeds_path / f"location_pool_{genre_type}.json"
            if not location_file.exists():
                location_file = seeds_path / "location_pool.json"

            if cliche_file.exists():
                cliche_data = json.loads(cliche_file.read_text(encoding="utf-8"))
            if location_file.exists():
                location_data = json.loads(location_file.read_text(encoding="utf-8"))

            self._ui.log(f"{Emojis.CHECK} [{genre_type}] 장르 전용 레퍼런스 데이터 로드 완료")
            self._audit_event(
                "reference_loaded",
                f"genre references loaded for {genre_type}",
                {"cliche_count": len(cliche_data), "location_count": len(location_data)},
            )
        except Exception as e:
            self._ui.log(f"{Emojis.ERROR} 레퍼런스 파일 로드 실패: {e}")
            self._audit_event("reference_load_error", "failed to load genre references", {"error": str(e)})

        return cliche_data, location_data

    # ── validate_arc_integrity ───────────────────────────────────
    def validate_arc_integrity(self, arc_data: dict[str, Any]) -> bool:
        """아크 데이터 무결성 검증. 원본: main_a.py:3078"""
        required_keys = ["arc_no", "ep_start", "ep_end", "ep_count", "tactical_doc", "beat_sequence"]
        missing = [k for k in required_keys if not arc_data.get(k)]
        if missing:
            self._ui.log(f"🚨 [Integrity] Arc 필수 키 누락: {missing}")
            self._audit_event(
                "integrity_fail", "arc missing keys", {"missing": missing, "arc_no": arc_data.get("arc_no")}
            )
            return False
        if not isinstance(arc_data.get("beat_sequence"), list) or len(arc_data.get("beat_sequence")) < 1:
            self._ui.log("🚨 [Integrity] beat_sequence 형식 오류")
            self._audit_event("integrity_fail", "beat_sequence invalid", {"arc_no": arc_data.get("arc_no")})
            return False
        if not isinstance(arc_data.get("tactical_doc"), str) or len(arc_data.get("tactical_doc", "")) < 500:
            self._ui.log("🚨 [Integrity] tactical_doc 분량 부족")
            self._audit_event("integrity_fail", "tactical_doc too short", {"arc_no": arc_data.get("arc_no")})
            return False
        return True

    # ── validate_blueprint_integrity ─────────────────────────────
    def validate_blueprint_integrity(self, blueprint: Any) -> bool:
        """블루프린트 데이터 무결성 검증. 원본: main_a.py:3108"""
        if not isinstance(blueprint, dict):
            self._ui.log(f"{Emojis.ERROR} [Integrity] Blueprint 형식 오류")
            self._audit_event("integrity_fail", "blueprint invalid type")
            return False
        if "integrated_scenario" not in blueprint or not isinstance(blueprint.get("integrated_scenario"), str):
            self._ui.log(f"{Emojis.ERROR} [Integrity] integrated_scenario 누락")
            self._audit_event("integrity_fail", "integrated_scenario missing")
            return False
        _sb = blueprint.get("scene_breakdown")
        if _sb is None:
            self._ui.log(f"{Emojis.ERROR} [Integrity] scene_breakdown 누락")
            self._audit_event("integrity_fail", "scene_breakdown missing")
            return False
        # [S3-N-P1-1] LLM이 list로 반환할 수 있으므로 list→dict 자동 변환
        if isinstance(_sb, list):
            _converted = {}
            for i, item in enumerate(_sb):
                key = f"scene_{i + 1}" if not isinstance(item, dict) or "scene_id" not in item else item["scene_id"]
                _converted[key] = item
            blueprint["scene_breakdown"] = _converted
        elif not isinstance(_sb, dict):
            self._ui.log(f"{Emojis.ERROR} [Integrity] scene_breakdown 형식 오류 (dict/list 아님)")
            self._audit_event("integrity_fail", "scene_breakdown invalid type")
            return False
        return True
