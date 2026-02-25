"""
[Step 2] Pydantic v2 모델 테스트

검증 대상:
- ArcData: 최소/전체/extra 키/model_dump dict 호환
- StateConstraints: canonical 키 + 런타임 전용 키 (items_acquired/grants_received)
- Blueprint: 최소/전체/extra
- ManuscriptCandidate: 전략별/에러 폴백
- NPCEntry: 기본/사망/동적 필드
- validate_* 헬퍼: 성공/실패 graceful degradation
"""

import pytest
from pydantic import ValidationError

from modules.models.arc import (
    ArcData,
    ArcState,
    HybridComposition,
    JointDocs,
    StateChanges,
    StateConstraints,
    StatusShadow,
    validate_arc,
    validate_blueprint_arc,
)
from modules.models.blueprint import Blueprint, validate_blueprint
from modules.models.manuscript import (
    ManuscriptCandidate,
    SelfCritiqueResult,
    validate_manuscript_candidate,
)
from modules.models.npc import NPCEntry, validate_npc_entry

# ═══════════════════════════════════════════════════════════════════
# ArcData
# ═══════════════════════════════════════════════════════════════════


class TestArcData:
    """ArcData 모델 검증"""

    def test_minimal(self):
        raw = {"arc_no": 1, "ep_start": 1, "ep_end": 5}
        arc = ArcData.model_validate(raw)
        assert arc.arc_no == 1
        assert arc.ep_start == 1
        assert arc.ep_end == 5
        assert arc.ep_count == 5  # default

    def test_full_fields(self):
        raw = {
            "arc_no": 3,
            "ep_start": 11,
            "ep_end": 15,
            "ep_count": 5,
            "volume_no": 2,
            "title": "패왕의 부름",
            "tactical_doc": "전술 문서 본문",
            "beat_sequence": ["beat1", "beat2"],
            "state_constraints": {
                "arc_start_state": {"location": "산정"},
                "arc_end_state": {"location": "계곡"},
                "protagonist_items": ["천잠사"],
                "items_consumed": ["금전"],
                "power_changes": {"start_power": 30, "end_power": 45},
            },
            "joint_docs": {"final_location": "계곡", "physical_inventory": ["천잠사"]},
            "status_shadow": {"expected_injuries": "경상"},
            "constraint_summary": "금지: 이전 무공 사용",
            "state_changes": {"npc_deaths": []},
            "hybrid_composition": {"primary": "성장물", "mixing_logic": "선형"},
        }
        arc = ArcData.model_validate(raw)
        assert arc.title == "패왕의 부름"
        assert arc.state_constraints["protagonist_items"] == ["천잠사"]

    def test_extra_keys_allowed(self):
        raw = {"arc_no": 1, "ep_start": 1, "ep_end": 5, "_ensemble_meta": {"best_strategy": "A"}}
        arc = ArcData.model_validate(raw)
        d = arc.model_dump()
        assert d["_ensemble_meta"] == {"best_strategy": "A"}

    def test_model_dump_dict_compatible(self):
        raw = {"arc_no": 1, "ep_start": 1, "ep_end": 5, "tactical_doc": "test"}
        arc = ArcData.model_validate(raw)
        d = arc.model_dump()
        assert isinstance(d, dict)
        assert d["arc_no"] == 1
        assert d.get("tactical_doc") == "test"

    def test_global_arc_no_sync(self):
        """global_arc_no만 있으면 arc_no로 동기화"""
        raw = {"global_arc_no": 7, "ep_start": 31, "ep_end": 35}
        arc = ArcData.model_validate(raw)
        assert arc.arc_no == 7
        assert arc.global_arc_no == 7

    def test_arc_no_to_global_sync(self):
        """arc_no만 있으면 global_arc_no로 동기화"""
        raw = {"arc_no": 4, "ep_start": 16, "ep_end": 20}
        arc = ArcData.model_validate(raw)
        assert arc.global_arc_no == 4

    def test_missing_required_raises(self):
        """필수 필드 누락 시 ValidationError"""
        with pytest.raises(ValidationError):
            ArcData.model_validate({"ep_start": 1, "ep_end": 5})

    def test_tactical_doc_as_dict(self):
        """tactical_doc이 dict여도 수용"""
        raw = {"arc_no": 1, "ep_start": 1, "ep_end": 5, "tactical_doc": {"phase": "setup"}}
        arc = ArcData.model_validate(raw)
        assert isinstance(arc.tactical_doc, dict)

    def test_beat_sequence_as_string(self):
        """beat_sequence가 str이어도 수용"""
        raw = {"arc_no": 1, "ep_start": 1, "ep_end": 5, "beat_sequence": "단일 비트"}
        arc = ArcData.model_validate(raw)
        assert arc.beat_sequence == "단일 비트"


# ═══════════════════════════════════════════════════════════════════
# StateConstraints
# ═══════════════════════════════════════════════════════════════════


class TestStateConstraints:
    """StateConstraints 모델 — 3계층 키 불일치 흡수 검증"""

    def test_canonical_keys(self):
        raw = {
            "arc_start_state": {"location": "산정"},
            "arc_end_state": {"location": "계곡"},
            "items_consumed": ["금전"],
            "power_changes": {"start_power": 30, "end_power": 45},
        }
        sc = StateConstraints.model_validate(raw)
        assert sc.items_consumed == ["금전"]
        assert sc.power_changes["start_power"] == 30

    def test_runtime_only_keys(self):
        """constraint_compiler 런타임 전용 키 수용"""
        raw = {
            "items_acquired": ["천잠비급", "독룡검"],
            "grants_received": ["사패"],
        }
        sc = StateConstraints.model_validate(raw)
        assert sc.items_acquired == ["천잠비급", "독룡검"]
        assert sc.grants_received == ["사패"]

    def test_extra_keys(self):
        raw = {"unknown_runtime_key": "some_value"}
        sc = StateConstraints.model_validate(raw)
        assert sc.model_dump()["unknown_runtime_key"] == "some_value"

    def test_empty(self):
        sc = StateConstraints.model_validate({})
        assert sc.protagonist_items == []
        assert sc.items_acquired is None


# ═══════════════════════════════════════════════════════════════════
# ArcState
# ═══════════════════════════════════════════════════════════════════


class TestArcState:
    def test_defaults(self):
        s = ArcState.model_validate({})
        assert s.location == ""
        assert s.injuries == "정상"
        assert s.internal_energy == 100

    def test_full(self):
        raw = {"location": "산정", "equipment": ["검", "갑옷"], "injuries": "중상", "internal_energy": 30}
        s = ArcState.model_validate(raw)
        assert s.equipment == ["검", "갑옷"]
        assert s.injuries == "중상"


# ═══════════════════════════════════════════════════════════════════
# Sub-models
# ═══════════════════════════════════════════════════════════════════


class TestSubModels:
    def test_hybrid_composition(self):
        raw = {"primary": "성장물", "secondary": ["무협", "로맨스"], "mixing_logic": "선형"}
        hc = HybridComposition.model_validate(raw)
        assert hc.primary == "성장물"

    def test_joint_docs(self):
        raw = {"final_location": "계곡", "physical_inventory": ["검"], "world_joint": "중원"}
        jd = JointDocs.model_validate(raw)
        assert jd.physical_inventory == ["검"]

    def test_joint_docs_inventory_as_string(self):
        raw = {"physical_inventory": "검, 갑옷"}
        jd = JointDocs.model_validate(raw)
        assert jd.physical_inventory == "검, 갑옷"

    def test_status_shadow(self):
        raw = {"expected_injuries": "경상", "internal_energy_loss": "30%"}
        ss = StatusShadow.model_validate(raw)
        assert ss.expected_injuries == "경상"

    def test_state_changes(self):
        raw = {
            "npc_deaths": [{"name": "악마왕", "episode": 5, "cause": "전투"}],
            "skill_acquisitions": [{"name": "뇌전공", "episode": 3, "source": "비급"}],
        }
        sc = StateChanges.model_validate(raw)
        assert len(sc.npc_deaths) == 1
        assert sc.npc_deaths[0]["name"] == "악마왕"


# ═══════════════════════════════════════════════════════════════════
# Blueprint
# ═══════════════════════════════════════════════════════════════════


class TestBlueprint:
    def test_minimal(self):
        raw = {"episode_number": 3, "scene_breakdown": {"s1": "장면1"}, "integrated_scenario": "시나리오"}
        bp = Blueprint.model_validate(raw)
        assert bp.episode_number == 3

    def test_extra_keys(self):
        raw = {"_ensemble_meta": {"strategy": "tension"}}
        bp = Blueprint.model_validate(raw)
        assert bp.model_dump()["_ensemble_meta"] == {"strategy": "tension"}

    def test_full_fields(self):
        raw = {
            "episode_number": 5,
            "scene_breakdown": {"s1": "opening"},
            "integrated_scenario": "통합 시나리오",
            "pacing_notes": "빠르게",
            "target_beat": "클라이맥스",
            "relationship_changes": [{"target": "A", "from_state": "적", "to_state": "아군"}],
            "time_flow": "3일 후",
            "protagonist_state": {"hp": 80},
            "start_location": "산정",
            "core_tension": "생존",
            "expected_ending": "클리프행어",
        }
        bp = Blueprint.model_validate(raw)
        assert bp.core_tension == "생존"
        assert bp.relationship_changes[0]["target"] == "A"

    def test_model_dump_dict(self):
        raw = {"episode_number": 1, "scene_breakdown": {}, "integrated_scenario": "test"}
        bp = Blueprint.model_validate(raw)
        d = bp.model_dump()
        assert isinstance(d, dict)
        assert d["integrated_scenario"] == "test"


# ═══════════════════════════════════════════════════════════════════
# ManuscriptCandidate
# ═══════════════════════════════════════════════════════════════════


class TestManuscriptCandidate:
    def test_balanced_strategy(self):
        raw = {
            "strategy": "balanced",
            "strategy_name": "균형형",
            "manuscript": "원고 본문...",
            "title": "제1화",
        }
        mc = ManuscriptCandidate.model_validate(raw)
        assert mc.strategy == "balanced"
        assert mc.manuscript == "원고 본문..."

    def test_error_fallback(self):
        raw = {
            "strategy": "error_fallback",
            "strategy_name": "에러 폴백",
            "manuscript": "",
            "title": "제1화 (생성 실패)",
            "error": True,
            "error_message": "모든 후보 생성 실패",
        }
        mc = ManuscriptCandidate.model_validate(raw)
        assert mc.error is True
        assert mc.error_message == "모든 후보 생성 실패"

    def test_extra_metadata(self):
        raw = {"strategy": "tension", "manuscript": "본문", "custom_score": 85}
        mc = ManuscriptCandidate.model_validate(raw)
        assert mc.model_dump()["custom_score"] == 85


class TestSelfCritiqueResult:
    def test_no_issues(self):
        raw = {"has_issues": False, "issues": [], "severity": ""}
        sc = SelfCritiqueResult.model_validate(raw)
        assert sc.has_issues is False

    def test_with_issues(self):
        raw = {"has_issues": True, "issues": ["NPC 불일치", "시간 역행"], "severity": "MAJOR"}
        sc = SelfCritiqueResult.model_validate(raw)
        assert len(sc.issues) == 2


# ═══════════════════════════════════════════════════════════════════
# NPCEntry
# ═══════════════════════════════════════════════════════════════════


class TestNPCEntry:
    def test_minimal(self):
        raw = {"name": "사독"}
        npc = NPCEntry.model_validate(raw)
        assert npc.name == "사독"
        assert npc.status == "alive"

    def test_dead_npc(self):
        raw = {"name": "독룡", "status": "dead", "death_arc": 3}
        npc = NPCEntry.model_validate(raw)
        assert npc.death_arc == 3

    def test_extra_preset_fields(self):
        """PresetRegistry 동적 필드 수용"""
        raw = {
            "name": "사독",
            "martial_arts": "독룡장",
            "faction": "사파",
            "internal_energy_level": 85,
        }
        npc = NPCEntry.model_validate(raw)
        d = npc.model_dump()
        assert d["martial_arts"] == "독룡장"
        assert d["faction"] == "사파"

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            NPCEntry.model_validate({"status": "alive"})


# ═══════════════════════════════════════════════════════════════════
# validate_* 헬퍼 (graceful degradation)
# ═══════════════════════════════════════════════════════════════════


class TestValidateHelpers:
    def test_validate_arc_success(self):
        raw = {"arc_no": 1, "ep_start": 1, "ep_end": 5, "tactical_doc": "test"}
        result = validate_arc(raw)
        assert isinstance(result, dict)
        assert result["arc_no"] == 1

    def test_validate_arc_failure_returns_original(self):
        """필수 키 누락 → 원본 dict 반환 (크래시 아님)"""
        bad = {"ep_start": 1}  # arc_no 누락
        result = validate_arc(bad)
        assert result is bad  # 원본 그대로

    def test_validate_arc_preserves_extra_keys(self):
        raw = {"arc_no": 1, "ep_start": 1, "ep_end": 5, "custom_key": "value"}
        result = validate_arc(raw)
        assert result["custom_key"] == "value"

    def test_validate_blueprint_success(self):
        raw = {"episode_number": 3, "scene_breakdown": {}, "integrated_scenario": "test"}
        result = validate_blueprint(raw)
        assert isinstance(result, dict)
        assert result["episode_number"] == 3

    def test_validate_blueprint_failure_returns_original(self):
        """Blueprint 검증 실패 시 원본 반환"""
        # Blueprint는 필수 필드 없이도 기본값으로 통과하므로
        # 타입 에러를 유발
        bad = "not_a_dict"
        result = validate_blueprint(bad)
        assert result == "not_a_dict"

    def test_validate_manuscript_candidate_success(self):
        raw = {"strategy": "balanced", "manuscript": "본문"}
        result = validate_manuscript_candidate(raw)
        assert result["strategy"] == "balanced"

    def test_validate_manuscript_candidate_failure(self):
        bad = "not_a_dict"
        result = validate_manuscript_candidate(bad)
        assert result == "not_a_dict"

    def test_validate_npc_entry_success(self):
        raw = {"name": "사독", "weapon": "독룡검"}
        result = validate_npc_entry(raw)
        assert result["name"] == "사독"

    def test_validate_npc_entry_failure(self):
        bad = {"status": "alive"}  # name 누락
        result = validate_npc_entry(bad)
        assert result is bad

    def test_validate_blueprint_arc_success(self):
        raw = {
            "arc_no": 1,
            "state_constraints": {
                "arc_start_state": {"location": "산정"},
                "items_consumed": ["금전"],
            },
        }
        result = validate_blueprint_arc(raw)
        assert result["state_constraints"]["items_consumed"] == ["금전"]

    def test_validate_blueprint_arc_no_constraints(self):
        raw = {"arc_no": 1}
        result = validate_blueprint_arc(raw)
        assert result["arc_no"] == 1


# ═══════════════════════════════════════════════════════════════════
# Dict 호환성 (기존 .get() 패턴 검증)
# ═══════════════════════════════════════════════════════════════════


class TestDictCompatibility:
    """model_dump() 결과가 기존 .get() 패턴과 100% 호환되는지 검증"""

    def test_arc_get_pattern(self):
        raw = {"arc_no": 1, "ep_start": 1, "ep_end": 5, "ep_count": 4}
        d = validate_arc(raw)
        # stage2_orchestrator.py 패턴: a.get("ep_start", 0)
        assert d.get("ep_start", 0) == 1
        assert d.get("ep_end", 0) == 5
        assert d.get("nonexistent", "default") == "default"

    def test_arc_state_constraints_nested_get(self):
        """constraint_compiler.py 패턴: (arc.get("state_constraints") or {}).get("items_acquired")"""
        raw = {
            "arc_no": 1,
            "ep_start": 1,
            "ep_end": 5,
            "state_constraints": {"items_acquired": ["검"], "items_consumed": ["금전"]},
        }
        d = validate_arc(raw)
        acquired = (d.get("state_constraints") or {}).get("items_acquired")
        assert acquired == ["검"]

    def test_blueprint_get_pattern(self):
        raw = {"episode_number": 5, "scene_breakdown": {"s1": "x"}, "integrated_scenario": "y"}
        d = validate_blueprint(raw)
        assert d.get("scene_breakdown", {}) == {"s1": "x"}
        assert d.get("nonexistent_key", None) is None

    def test_manuscript_get_pattern(self):
        """stage4_orchestrator.py 패턴: candidates[i].get("manuscript")"""
        raw = {"strategy": "balanced", "manuscript": "원고 본문"}
        d = validate_manuscript_candidate(raw)
        assert d.get("manuscript") == "원고 본문"
        assert d.get("strategy_name", "") == ""

    def test_json_dumps_compatible(self):
        """DB 저장 패턴: json.dumps(arc_dict)"""
        import json

        raw = {"arc_no": 1, "ep_start": 1, "ep_end": 5, "tactical_doc": "테스트"}
        d = validate_arc(raw)
        serialized = json.dumps(d, ensure_ascii=False)
        assert "arc_no" in serialized
        reloaded = json.loads(serialized)
        assert reloaded["arc_no"] == 1


# ═══════════════════════════════════════════════════════════════════
# TF-12 Layer 1: SSOT 계약 강제 검증
# ═══════════════════════════════════════════════════════════════════


class TestArcDataSSOTContracts:
    """TF-12 Layer 1: SSOT 계약 강제 검증"""

    def test_injuries_none_normalized(self):
        arc = ArcData.model_validate(
            {"arc_no": 1, "ep_start": 1, "ep_end": 5,
             "state_constraints": {"arc_end_state": {"injuries": None}}}
        )
        assert arc.state_constraints["arc_end_state"]["injuries"] == "없음"

    def test_injuries_empty_string_normalized(self):
        arc = ArcData.model_validate(
            {"arc_no": 1, "ep_start": 1, "ep_end": 5,
             "state_constraints": {"arc_end_state": {"injuries": ""}}}
        )
        assert arc.state_constraints["arc_end_state"]["injuries"] == "없음"

    def test_injuries_real_value_preserved(self):
        arc = ArcData.model_validate(
            {"arc_no": 1, "ep_start": 1, "ep_end": 5,
             "state_constraints": {"arc_end_state": {"injuries": "왼팔 골절"}}}
        )
        assert arc.state_constraints["arc_end_state"]["injuries"] == "왼팔 골절"

    def test_location_synced_from_joint_docs(self):
        arc = ArcData.model_validate(
            {"arc_no": 1, "ep_start": 1, "ep_end": 5,
             "state_constraints": {"arc_end_state": {}},
             "joint_docs": {"final_location": "역삼동 사무실"}}
        )
        assert arc.state_constraints["arc_end_state"]["location"] == "역삼동 사무실"

    def test_location_not_overridden_if_set(self):
        arc = ArcData.model_validate(
            {"arc_no": 1, "ep_start": 1, "ep_end": 5,
             "state_constraints": {"arc_end_state": {"location": "강남"}},
             "joint_docs": {"final_location": "역삼동"}}
        )
        assert arc.state_constraints["arc_end_state"]["location"] == "강남"

    def test_no_arc_end_state_key_untouched(self):
        arc = ArcData.model_validate(
            {"arc_no": 1, "ep_start": 1, "ep_end": 5,
             "state_constraints": {}}
        )
        assert arc.state_constraints.get("arc_end_state") is None

    def test_empty_state_constraints_untouched(self):
        arc = ArcData.model_validate(
            {"arc_no": 1, "ep_start": 1, "ep_end": 5}
        )
        assert arc.state_constraints == {}

    def test_shadow_does_not_leak_into_injuries(self):
        """핵심: validate_arc 통과 후 shadow가 injuries에 영향 없음"""
        result = validate_arc({
            "arc_no": 1, "ep_start": 1, "ep_end": 5,
            "state_constraints": {"arc_end_state": {}},
            "status_shadow": {"expected_injuries": "폐암 말기"},
            "joint_docs": {"final_location": "판교"},
        })
        assert result["state_constraints"]["arc_end_state"]["injuries"] == "없음"
        assert result["state_constraints"]["arc_end_state"]["location"] == "판교"
