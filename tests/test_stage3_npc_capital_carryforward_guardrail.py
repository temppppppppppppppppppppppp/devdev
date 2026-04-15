"""
[NPC-CF] Stage 3 NPC + Capital Carry-Forward Wave Guardrail Tests

Tests for:
- Tranche A: NPC/Institution fact-lock anchor extraction
- Tranche B: Capital carry-forward fallback extraction from free-text
- Tranche C: Institution drift detection + phantom capital drift detection
"""

from modules.core.cross_stage_authority_packet import CROSS_STAGE_AUTHORITY_PACKET_VERSION
from modules.domain.agents.blueprint_constraint_compiler import BlueprintConstraintCompiler
from modules.domain.agents.unified_blueprint_validator import UnifiedBlueprintValidator

# ============================================================
# Tranche A: NPC/Institution Fact-Lock Anchor Extraction
# ============================================================


class TestInstitutionFactLockAnchor:
    """Institution/venue names are extracted and locked from prior accepted canon."""

    def test_institution_from_manuscript(self):
        """Manuscript text containing institution names produces 기관 anchors."""
        result = BlueprintConstraintCompiler._build_fact_lock_packet(
            prev_blueprint={"end_location": "사무실"},
            prev_manuscript_ending="김 대표는 HMC투자증권 VVIP PB센터에서 회의를 마쳤다.",
            arc_data={},
            ep_num=4,
        )
        anchors = result.get("anchors", [])
        inst_anchors = [a for a in anchors if a["category"] == "기관"]
        names = [a["fact"] for a in inst_anchors]
        assert any("HMC투자증권" in n for n in names), f"HMC투자증권 not found in {names}"
        assert any("PB센터" in n for n in names), f"PB센터 not found in {names}"

    def test_institution_from_blueprint_scene_locations(self):
        """Scene locations containing institution names produce 기관 anchors."""
        bp = {
            "end_location": "HMC투자증권 VVIP PB센터",
            "scene_breakdown": {
                "scene_1": {"location": "SW인베스트먼트 사무실"},
                "scene_2": {"location": "여의도 공원"},
            },
        }
        result = BlueprintConstraintCompiler._build_fact_lock_packet(
            prev_blueprint=bp,
            prev_manuscript_ending="",
            arc_data={},
            ep_num=4,
        )
        anchors = result.get("anchors", [])
        inst_anchors = [a for a in anchors if a["category"] == "기관"]
        names = " ".join(a["fact"] for a in inst_anchors)
        assert "HMC투자증권" in names
        assert "인베스트먼트" in names

    def test_institution_from_ending_state(self):
        """Ending state text containing institution names produces 기관 anchors."""
        bp = {
            "end_location": "사무실",
            "ending_state": {
                "location_detail": "국민은행 여의도지점 VIP 라운지",
            },
        }
        result = BlueprintConstraintCompiler._build_fact_lock_packet(
            prev_blueprint=bp,
            prev_manuscript_ending="",
            arc_data={},
            ep_num=4,
        )
        anchors = result.get("anchors", [])
        inst_anchors = [a for a in anchors if a["category"] == "기관"]
        names = " ".join(a["fact"] for a in inst_anchors)
        assert "국민은행" in names

    def test_short_names_filtered(self):
        """Institution names shorter than 4 chars are filtered out."""
        result = BlueprintConstraintCompiler._build_fact_lock_packet(
            prev_blueprint={"end_location": "동쪽"},
            prev_manuscript_ending="A은행에서 대출을 받았다.",
            arc_data={},
            ep_num=3,
        )
        anchors = result.get("anchors", [])
        inst_anchors = [a for a in anchors if a["category"] == "기관"]
        # "A은행" is only 3 chars -> should be filtered
        assert len(inst_anchors) == 0

    def test_no_institution_no_anchor(self):
        """No institution mentions produce no 기관 anchors."""
        result = BlueprintConstraintCompiler._build_fact_lock_packet(
            prev_blueprint={"end_location": "산속 오두막"},
            prev_manuscript_ending="그는 조용히 무공을 수련했다.",
            arc_data={},
            ep_num=3,
        )
        anchors = result.get("anchors", [])
        inst_anchors = [a for a in anchors if a["category"] == "기관"]
        assert len(inst_anchors) == 0

    def test_institution_anchors_bounded(self):
        """Institution anchors are bounded to max 4."""
        text = (
            "한국투자증권, 미래에셋증권, 삼성증권, NH투자증권, "
            "KB증권, 대신증권, 키움증권에서 동시에 회의했다."
        )
        result = BlueprintConstraintCompiler._build_fact_lock_packet(
            prev_blueprint={"end_location": "증권가"},
            prev_manuscript_ending=text,
            arc_data={},
            ep_num=4,
        )
        anchors = result.get("anchors", [])
        inst_anchors = [a for a in anchors if a["category"] == "기관"]
        assert len(inst_anchors) <= 4


    def test_manuscript_institution_outranks_conflicting_blueprint_institution(self):
        bp = {
            "end_location": "한미증권 본점",
            "scene_breakdown": {"scene_1": {"location": "한미증권 PB센터"}},
            "ending_state": {"location_detail": "한미증권 VIP 라운지"},
        }
        result = BlueprintConstraintCompiler._build_fact_lock_packet(
            prev_blueprint=bp,
            prev_manuscript_ending="김도진은 HMC투자증권 VVIP PB센터에서 미팅을 마치고 자리에서 일어섰다.",
            arc_data={},
            ep_num=4,
        )

        names = " ".join(a["fact"] for a in result.get("anchors", []) if a["category"] == "기관")
        assert "HMC투자증권" in names
        assert "한미증권" not in names

    def test_compiled_fact_lock_prefers_manuscript_truth_for_validator(self):
        bp = {
            "end_location": "한미증권 본점",
            "scene_breakdown": {"scene_1": {"location": "한미증권 PB센터"}},
            "ending_state": {"location_detail": "한미증권 VIP 라운지"},
        }
        packet = BlueprintConstraintCompiler._build_fact_lock_packet(
            prev_blueprint=bp,
            prev_manuscript_ending="김도진은 HMC투자증권 VVIP PB센터에서 미팅을 마치고 자리에서 일어섰다.",
            arc_data={},
            ep_num=4,
        )

        no_issue = UnifiedBlueprintValidator._collect_fact_lock_drift_issues(
            blueprint={},
            integrated="김도진은 HMC투자증권 VVIP PB센터에서 다시 강민철과 마주 앉았다.",
            constraint_block={"fact_lock_packet": packet},
        )
        assert [i for i in no_issue if i["category"] == "fact_lock_institution"] == []

        yes_issue = UnifiedBlueprintValidator._collect_fact_lock_drift_issues(
            blueprint={},
            integrated="김도진은 한미증권 PB센터에서 박성호를 다시 만났다.",
            constraint_block={"fact_lock_packet": packet},
        )
        inst_issues = [i for i in yes_issue if i["category"] == "fact_lock_institution"]
        assert len(inst_issues) >= 1
        assert "한미증권" in inst_issues[0]["issue"]

    def test_manuscript_institution_survives_anchor_truncation_priority(self):
        bp = {
            "end_location": "Alpha증권",
            "scene_breakdown": {
                "scene_1": {"location": "Bravo은행"},
                "scene_2": {"location": "Charlie병원"},
            },
            "ending_state": {"location_detail": "Delta센터"},
        }
        result = BlueprintConstraintCompiler._build_fact_lock_packet(
            prev_blueprint=bp,
            prev_manuscript_ending="김도진은 Zeta그룹 회의실에서 마지막 결재를 마쳤다.",
            arc_data={},
            ep_num=4,
        )

        names = [a["fact"] for a in result.get("anchors", []) if a["category"] == "기관"]
        assert len(names) <= 4
        assert any("Zeta그룹" in name for name in names), names
        assert not any("Delta센터" in name for name in names), names


# ============================================================
# Tranche B: Capital Carry-Forward Fallback Extraction
# ============================================================


class TestCapitalFallbackExtraction:
    """Capital amounts are extracted from free-text equipment and status fields."""

    def test_capital_from_equipment_deposited(self):
        """Equipment with deposited capital produces a 보유 자본 field."""
        bp = {
            "protagonist_state": {
                "equipment": [
                    "19억 3천만 원이 예치된 계좌 내역",
                    "노트북",
                ],
            },
        }
        result = BlueprintConstraintCompiler._build_capital_continuity_packet(
            prev_blueprint=bp,
            prev_manuscript_ending="",
            arc_data={},
            genre="investment",
        )
        fields = result.get("fields", [])
        assert len(fields) >= 1
        deposited = [f for f in fields if "보유" in f.get("label", "")]
        assert len(deposited) >= 1
        assert "19억" in deposited[0]["value"]

    def test_capital_from_equipment_deployed(self):
        """Equipment with deployed capital produces a 투입 확정 field."""
        bp = {
            "protagonist_state": {
                "equipment": [
                    "198만 달러 WTI 선물 매수 체결 확인서",
                ],
            },
        }
        result = BlueprintConstraintCompiler._build_capital_continuity_packet(
            prev_blueprint=bp,
            prev_manuscript_ending="",
            arc_data={},
            genre="investment",
        )
        fields = result.get("fields", [])
        deployed = [f for f in fields if "투입" in f.get("label", "")]
        assert len(deployed) >= 1
        assert "198만" in deployed[0]["value"]

    def test_capital_from_protagonist_status(self):
        """Protagonist status text with capital amounts produces fields."""
        bp = {
            "protagonist_state": {
                "status": "19억 원을 WTI 선물에 투입 완료",
            },
        }
        result = BlueprintConstraintCompiler._build_capital_continuity_packet(
            prev_blueprint=bp,
            prev_manuscript_ending="",
            arc_data={},
            genre="investment",
        )
        fields = result.get("fields", [])
        assert len(fields) >= 1
        deployed = [f for f in fields if "투입" in f.get("label", "")]
        assert len(deployed) >= 1

    def test_capital_from_manuscript_deployment(self):
        """Manuscript tail with deployment action produces 투입 확정 field."""
        ms_text = "김 대표는 19억 원을 WTI 선물에 전액 투입했다. 이제 남은 현금은 없었다."
        result = BlueprintConstraintCompiler._build_capital_continuity_packet(
            prev_blueprint={},
            prev_manuscript_ending=ms_text,
            arc_data={},
            genre="investment",
        )
        fields = result.get("fields", [])
        deployed = [f for f in fields if "투입" in f.get("label", "")]
        assert len(deployed) >= 1
        assert "19억" in deployed[0]["value"]

    def test_non_investment_genre_still_empty(self):
        """Non-investment genre returns empty even with capital in equipment."""
        bp = {
            "protagonist_state": {
                "equipment": ["10만 냥이 보관된 금고"],
            },
        }
        result = BlueprintConstraintCompiler._build_capital_continuity_packet(
            prev_blueprint=bp,
            prev_manuscript_ending="",
            arc_data={},
            genre="wuxia",
        )
        assert result == {}

    def test_fallback_fields_bounded(self):
        """Fallback extraction respects the 8-field limit."""
        equip = [f"{i}억 원이 예치된 계좌 {i}" for i in range(1, 12)]
        bp = {"protagonist_state": {"equipment": equip}}
        result = BlueprintConstraintCompiler._build_capital_continuity_packet(
            prev_blueprint=bp,
            prev_manuscript_ending="",
            arc_data={},
            genre="investment",
        )
        fields = result.get("fields", [])
        assert len(fields) <= 8

    def test_structured_plus_fallback_coexist(self):
        """Structured ending_state fields coexist with equipment fallback."""
        bp = {
            "ending_state": {"balance": "19억 원"},
            "protagonist_state": {
                "equipment": ["198만 달러 WTI 선물 매수 체결 확인서"],
            },
        }
        result = BlueprintConstraintCompiler._build_capital_continuity_packet(
            prev_blueprint=bp,
            prev_manuscript_ending="",
            arc_data={},
            genre="investment",
        )
        fields = result.get("fields", [])
        labels = [f["label"] for f in fields]
        assert "잔고/자본" in labels  # structured
        assert any("투입" in label for label in labels)  # fallback


# ============================================================
# Tranche C: Institution Drift + Phantom Capital Drift Detection
# ============================================================


class TestInstitutionDriftDetection:
    """Prevalidation detects institution/venue drift against fact-lock anchors."""

    def test_institution_drift_detected(self):
        """Blueprint using different institution name triggers CRITICAL issue."""
        constraint_block = {
            "fact_lock_packet": {
                "anchors": [
                    {"category": "기관", "fact": "확정 기관/장소: HMC투자증권"},
                ],
            },
        }
        integrated = "김 대표는 한미증권 본사 VVIP 프라이빗 룸에서 미팅을 시작했다."
        issues = UnifiedBlueprintValidator._collect_fact_lock_drift_issues(
            blueprint={},
            integrated=integrated,
            constraint_block=constraint_block,
        )
        inst_issues = [i for i in issues if i["category"] == "fact_lock_institution"]
        assert len(inst_issues) >= 1
        assert inst_issues[0]["severity"] == "CRITICAL"
        assert "한미증권" in inst_issues[0]["issue"]

    def test_no_drift_when_institution_matches(self):
        """No issue when blueprint uses the same institution name."""
        constraint_block = {
            "fact_lock_packet": {
                "anchors": [
                    {"category": "기관", "fact": "확정 기관/장소: HMC투자증권"},
                ],
            },
        }
        integrated = "김 대표는 HMC투자증권 VVIP PB센터에서 미팅을 시작했다."
        issues = UnifiedBlueprintValidator._collect_fact_lock_drift_issues(
            blueprint={},
            integrated=integrated,
            constraint_block=constraint_block,
        )
        inst_issues = [i for i in issues if i["category"] == "fact_lock_institution"]
        assert len(inst_issues) == 0

    def test_no_drift_when_no_competing_institution(self):
        """No issue when locked institution is absent but no competing name either."""
        constraint_block = {
            "fact_lock_packet": {
                "anchors": [
                    {"category": "기관", "fact": "확정 기관/장소: HMC투자증권"},
                ],
            },
        }
        integrated = "그는 조용히 사무실에서 차트를 분석했다."
        issues = UnifiedBlueprintValidator._collect_fact_lock_drift_issues(
            blueprint={},
            integrated=integrated,
            constraint_block=constraint_block,
        )
        inst_issues = [i for i in issues if i["category"] == "fact_lock_institution"]
        assert len(inst_issues) == 0

    def test_drift_with_same_suffix_type(self):
        """Drift is detected when a different 증권 company replaces the locked one."""
        constraint_block = {
            "fact_lock_packet": {
                "anchors": [
                    {"category": "기관", "fact": "확정 기관/장소: 삼성증권"},
                ],
            },
        }
        integrated = "미래에셋증권 본사 12층에서 비밀 회동이 이루어졌다."
        issues = UnifiedBlueprintValidator._collect_fact_lock_drift_issues(
            blueprint={},
            integrated=integrated,
            constraint_block=constraint_block,
        )
        inst_issues = [i for i in issues if i["category"] == "fact_lock_institution"]
        assert len(inst_issues) >= 1
        assert "미래에셋증권" in inst_issues[0]["issue"]


class TestPhantomCapitalDriftDetection:
    """Prevalidation detects deployed capital reappearing as available."""

    def test_phantom_capital_detected(self):
        """Deployed amount appearing as deposited in blueprint triggers issue."""
        constraint_block = {
            "capital_continuity_packet": {
                "fields": [
                    {"label": "투입 확정", "value": "19억 원 (투입/체결 완료 — 가용 아님)"},
                ],
            },
        }
        integrated = "19억 원이 예치된 계좌 내역을 확인하며 다음 투자를 계획했다."
        issues = UnifiedBlueprintValidator._collect_capital_state_drift_issues(
            integrated=integrated,
            constraint_block=constraint_block,
        )
        phantom_issues = [i for i in issues if i["category"] == "phantom_capital"]
        assert len(phantom_issues) >= 1
        assert phantom_issues[0]["severity"] == "MAJOR"

    def test_no_phantom_when_capital_not_reappearing(self):
        """No issue when deployed capital does not reappear as available."""
        constraint_block = {
            "capital_continuity_packet": {
                "fields": [
                    {"label": "투입 확정", "value": "19억 원 (투입/체결 완료 — 가용 아님)"},
                ],
            },
        }
        integrated = "WTI 선물 포지션의 수익률을 확인했다. 환율이 유리하게 움직이고 있었다."
        issues = UnifiedBlueprintValidator._collect_capital_state_drift_issues(
            integrated=integrated,
            constraint_block=constraint_block,
        )
        phantom_issues = [i for i in issues if i["category"] == "phantom_capital"]
        assert len(phantom_issues) == 0

    def test_existing_contradiction_patterns_still_work(self):
        """Existing generic contradiction patterns still trigger."""
        constraint_block = {
            "capital_continuity_packet": {
                "fields": [
                    {"label": "잔고/자본", "value": "19억 원"},
                ],
            },
        }
        integrated = "아직 여유 자금이 충분하니 추가 투자를 결정했다."
        issues = UnifiedBlueprintValidator._collect_capital_state_drift_issues(
            integrated=integrated,
            constraint_block=constraint_block,
        )
        generic_issues = [i for i in issues if i["category"] == "capital_state"]
        assert len(generic_issues) >= 1
        assert generic_issues[0]["severity"] == "CRITICAL"

    def test_phantom_capital_with_comma_amount(self):
        """Phantom detection works with comma-formatted amounts."""
        constraint_block = {
            "capital_continuity_packet": {
                "fields": [
                    {"label": "투입 확정", "value": "1,930,000,000원 투입/매수 — 가용 자본 아님"},
                ],
            },
        }
        integrated = "1930000000원이 잔고에 보유되어 있었다."
        issues = UnifiedBlueprintValidator._collect_capital_state_drift_issues(
            integrated=integrated,
            constraint_block=constraint_block,
        )
        phantom_issues = [i for i in issues if i["category"] == "phantom_capital"]
        assert len(phantom_issues) >= 1


# ============================================================
# Integration: End-to-End Compile + Validate
# ============================================================


class TestEndToEndCompileValidate:
    """Full pipeline: compile constraints then validate blueprint against them."""

    def test_ep6_institution_drift_caught_e2e(self):
        """EP6 institution drift (HMC투자증권→한미증권) is caught end-to-end."""
        compiler = BlueprintConstraintCompiler()
        prev_bp = {
            "end_location": "HMC투자증권 VVIP PB센터",
            "scene_breakdown": {"scene_1": {"location": "HMC투자증권 VVIP PB센터"}},
            "ending_hook": "내일의 시장이 기대된다.",
        }
        constraint_block = compiler.compile(
            arc_data={"ep_start": 1, "ep_count": 10, "arc_no": 1},
            ep_num=6,
            prev_blueprint=prev_bp,
            genre="investment",
            prev_manuscript_ending="그는 HMC투자증권 VVIP PB센터를 나서며 미소 지었다.",
        )

        # Verify institution anchor was extracted
        fl = constraint_block.get("fact_lock_packet", {})
        inst_anchors = [a for a in fl.get("anchors", []) if a["category"] == "기관"]
        assert any("HMC투자증권" in a["fact"] for a in inst_anchors)

        # Validate a drifted blueprint
        drifted_bp = {
            "start_location": "한미증권 본사",
            "integrated_scenario": "김 대표는 여의도 한미증권 본사 VVIP 프라이빗 룸에서 미팅을 시작했다. " * 20,
            "scene_breakdown": {"scene_1": {"goal": "미팅", "summary": "한미증권 회의"}},
        }
        issues = UnifiedBlueprintValidator._collect_fact_lock_drift_issues(
            blueprint=drifted_bp,
            integrated=drifted_bp["integrated_scenario"],
            constraint_block=constraint_block,
        )
        inst_issues = [i for i in issues if i["category"] == "fact_lock_institution"]
        assert len(inst_issues) >= 1, f"Institution drift not detected. Issues: {issues}"

    def test_ep5_stale_capital_fallback_extraction(self):
        """EP5 stale capital (19억 3천만 원) is captured via equipment fallback."""
        compiler = BlueprintConstraintCompiler()
        prev_bp = {
            "end_location": "사무실",
            "protagonist_state": {
                "equipment": [
                    "약 198만 달러가 예치된 파생상품 계좌",
                    "노트북",
                ],
            },
        }
        constraint_block = compiler.compile(
            arc_data={"ep_start": 1, "ep_count": 10, "arc_no": 1},
            ep_num=5,
            prev_blueprint=prev_bp,
            genre="investment",
            prev_manuscript_ending="19억 원을 전액 WTI 선물에 투입했다.",
        )

        cap_pkt = constraint_block.get("capital_continuity_packet", {})
        fields = cap_pkt.get("fields", [])
        assert len(fields) >= 1, f"No capital fields extracted. Packet: {cap_pkt}"
        # Should have deployment marker from manuscript
        deployed = [f for f in fields if "투입" in f.get("label", "")]
        assert len(deployed) >= 1, f"No deployment marker found. Fields: {fields}"


class TestEpisodeStatePacket:
    def test_mid_arc_packet_prefers_previous_blueprint_location_and_records_dropped_arc_start_conflict(self):
        compiler = BlueprintConstraintCompiler()
        prev_bp = {
            "ep_num": 8,
            "end_location": "한미증권 청담동 지점 15층 VIP룸",
            "time_flow": "2006년 2월 늦은 밤",
            "protagonist_state": {
                "equipment": ["가죽 서류가방", "CME 계좌 증빙"],
                "injuries": "없음",
                "companions": ["박성호"],
                "mood": "냉정한 압박감",
            },
            "scene_breakdown": {
                "scene_2": {
                    "location": "한미증권 청담동 지점 15층 VIP룸",
                    "characters": ["한시우", "박성호"],
                }
            },
        }
        arc_data = {
            "ep_start": 7,
            "ep_count": 4,
            "arc_no": 2,
            "joint_docs": {"final_location": "본가 개인 서재"},
            "state_constraints": {
                "arc_start_state": {
                    "location": "본가 개인 서재",
                    "equipment": ["가죽 서류가방", "삼성 애니콜 SGH-D600"],
                    "injuries": "오른쪽 손목 결림",
                }
            },
        }

        constraint_block = compiler.compile(
            arc_data=arc_data,
            ep_num=9,
            prev_blueprint=prev_bp,
            prev_blueprints=[prev_bp],
            genre="investment",
            prev_manuscript_ending="그는 VIP룸 문을 나서며 바로 다음 협상 수를 계산했다.",
        )

        packet = constraint_block.get("episode_state_packet", {})
        opening_truth = packet.get("opening_truth", {})
        protagonist_truth = packet.get("protagonist_truth", {})

        assert opening_truth.get("location") == "한미증권 청담동 지점 15층 VIP룸"
        assert opening_truth.get("location_source") == "prev_blueprint.scene_breakdown.last.location"
        assert constraint_block.get("continuity", {}).get("location") == "한미증권 청담동 지점 15층 VIP룸"
        assert protagonist_truth.get("equipment") == ["가죽 서류가방", "CME 계좌 증빙"]
        assert protagonist_truth.get("injuries") == "없음"
        assert "mid_arc_arc_start_location_override_blocked" in packet.get("rewrite_required_reasons", [])
        assert "mid_arc_arc_start_equipment_override_blocked" in packet.get("rewrite_required_reasons", [])
        assert any(
            item.get("field") == "opening.location" for item in packet.get("dropped_conflicts", []) if isinstance(item, dict)
        )

    def test_mid_arc_packet_keeps_previous_blueprint_authority_even_when_cross_stage_packet_is_present(self):
        compiler = BlueprintConstraintCompiler()
        prev_bp = {
            "ep_num": 8,
            "end_location": "Prev Blueprint Room",
            "time_flow": "Night briefing",
            "protagonist_state": {
                "equipment": ["legacy-case", "cme-proof"],
                "injuries": "stable",
            },
            "scene_breakdown": {
                "scene_2": {
                    "location": "Prev Blueprint Room",
                    "characters": ["lead", "ally"],
                }
            },
        }
        arc_data = {
            "ep_start": 7,
            "ep_count": 4,
            "arc_no": 2,
            "joint_docs": {"final_location": "Joint Back Office"},
            "cross_stage_authority_packet": {
                "contract_version": CROSS_STAGE_AUTHORITY_PACKET_VERSION,
                "opening_carryover": {
                    "location": "Packet Back Office",
                    "location_source": "state_constraints.arc_end_state.location",
                },
                "protagonist_carryover": {
                    "equipment": ["packet-briefcase"],
                    "injuries": "packet-wrist",
                },
                "numeric_carryover": {"capital": "packet-capital"},
            },
            "state_constraints": {
                "arc_start_state": {
                    "location": "Arc Start Office",
                    "equipment": ["arc-start-briefcase"],
                    "injuries": "arc-start-wrist",
                }
            },
        }

        constraint_block = compiler.compile(
            arc_data=arc_data,
            ep_num=9,
            prev_blueprint=prev_bp,
            prev_blueprints=[prev_bp],
            genre="investment",
            prev_manuscript_ending="He exits the room and recalculates the next move.",
        )

        packet = constraint_block.get("episode_state_packet", {})
        opening_truth = packet.get("opening_truth", {})
        protagonist_truth = packet.get("protagonist_truth", {})

        assert opening_truth.get("location") == "Prev Blueprint Room"
        assert opening_truth.get("location_source") == "prev_blueprint.scene_breakdown.last.location"
        assert protagonist_truth.get("equipment") == ["legacy-case", "cme-proof"]
        assert protagonist_truth.get("injuries") == "stable"
        assert "cross_stage_authority_packet.opening_carryover.location" in packet.get("source_precedence", {}).get(
            "opening_truth", []
        )
        assert "cross_stage_authority_packet.protagonist_carryover" in packet.get("source_precedence", {}).get(
            "protagonist_truth", []
        )
        assert "mid_arc_arc_start_location_override_blocked" in packet.get("rewrite_required_reasons", [])
        assert "mid_arc_arc_start_equipment_override_blocked" in packet.get("rewrite_required_reasons", [])

    def test_episode_state_packet_prefers_cross_stage_authority_packet_for_stage2_opening_and_protagonist_truth(self):
        compiler = BlueprintConstraintCompiler()
        constraint_block = compiler.compile(
            arc_data={
                "ep_start": 11,
                "ep_count": 3,
                "arc_no": 3,
                "joint_docs": {
                    "final_location": "Stale Joint Office",
                    "physical_inventory": ["stale-pager"],
                },
                "status_shadow": {
                    "expected_injuries": "stale-shoulder",
                    "internal_energy_loss": "40%",
                },
                "cross_stage_authority_packet": {
                    "contract_version": CROSS_STAGE_AUTHORITY_PACKET_VERSION,
                    "opening_carryover": {
                        "location": "Packet Hall",
                        "location_source": "state_constraints.arc_end_state.location",
                    },
                    "protagonist_carryover": {
                        "equipment": ["packet-sword"],
                        "injuries": "packet-clear",
                        "internal_energy": "88%",
                    },
                    "numeric_carryover": {},
                },
                "state_constraints": {
                    "arc_start_state": {
                        "location": "Arc Start Office",
                        "equipment": ["arc-start-briefcase"],
                        "injuries": "arc-start-wrist",
                        "internal_energy": 44,
                    }
                },
            },
            ep_num=11,
            prev_blueprint={},
            genre="wuxia",
        )

        packet = constraint_block.get("episode_state_packet", {})
        protagonist_truth = packet.get("protagonist_truth", {})

        assert constraint_block.get("continuity", {}).get("location") == "Packet Hall"
        assert packet.get("opening_truth", {}).get("location_source") == "state_constraints.arc_end_state.location"
        assert constraint_block.get("inherited_state", {}).get("equipment") == ["packet-sword"]
        assert constraint_block.get("inherited_state", {}).get("injuries") == "packet-clear"
        assert constraint_block.get("inherited_state", {}).get("internal_energy") == "88%"
        assert protagonist_truth.get("sources", {}).get("equipment") == (
            "cross_stage_authority_packet.protagonist_carryover.equipment"
        )
        assert protagonist_truth.get("sources", {}).get("injuries") == (
            "cross_stage_authority_packet.protagonist_carryover.injuries"
        )
        assert protagonist_truth.get("sources", {}).get("internal_energy") == (
            "cross_stage_authority_packet.protagonist_carryover.internal_energy"
        )

    def test_mid_arc_packet_conflicts_are_recorded_when_previous_blueprint_keeps_authority(self):
        compiler = BlueprintConstraintCompiler()
        prev_bp = {
            "ep_num": 8,
            "end_location": "Prev Blueprint Room",
            "protagonist_state": {
                "equipment": ["legacy-case"],
                "injuries": "stable",
            },
            "scene_breakdown": {
                "scene_2": {
                    "location": "Prev Blueprint Room",
                    "characters": ["lead", "ally"],
                }
            },
        }
        constraint_block = compiler.compile(
            arc_data={
                "ep_start": 7,
                "ep_count": 4,
                "arc_no": 2,
                "cross_stage_authority_packet": {
                    "contract_version": CROSS_STAGE_AUTHORITY_PACKET_VERSION,
                    "opening_carryover": {
                        "location": "Packet Back Office",
                        "location_source": "state_constraints.arc_end_state.location",
                    },
                    "protagonist_carryover": {
                        "equipment": ["packet-briefcase"],
                        "injuries": "packet-wrist",
                    },
                    "numeric_carryover": {},
                },
            },
            ep_num=9,
            prev_blueprint=prev_bp,
            prev_blueprints=[prev_bp],
            genre="investment",
            prev_manuscript_ending="He exits the room and recalculates the next move.",
        )

        packet = constraint_block.get("episode_state_packet", {})
        reasons = packet.get("rewrite_required_reasons", [])
        conflicts = [item for item in packet.get("dropped_conflicts", []) if isinstance(item, dict)]

        assert "mid_arc_cross_stage_packet_location_override_blocked" in reasons
        assert "mid_arc_cross_stage_packet_equipment_override_blocked" in reasons
        assert "mid_arc_cross_stage_packet_injury_override_blocked" in reasons
        assert any(item.get("field") == "opening.location" for item in conflicts)
        assert any(item.get("field") == "protagonist.equipment" for item in conflicts)
        assert any(item.get("field") == "protagonist.injuries" for item in conflicts)

    def test_episode_state_packet_falls_back_to_scattered_stage2_fields_when_cross_stage_authority_packet_missing(self):
        compiler = BlueprintConstraintCompiler()
        constraint_block = compiler.compile(
            arc_data={
                "ep_start": 11,
                "ep_count": 3,
                "arc_no": 3,
                "joint_docs": {
                    "final_location": "Fallback Joint Office",
                    "physical_inventory": ["fallback-pager"],
                },
                "status_shadow": {
                    "expected_injuries": "fallback-shoulder",
                    "internal_energy_loss": "40%",
                },
            },
            ep_num=11,
            prev_blueprint={},
            genre="wuxia",
        )

        packet = constraint_block.get("episode_state_packet", {})
        protagonist_truth = packet.get("protagonist_truth", {})

        assert constraint_block.get("continuity", {}).get("location") == "Fallback Joint Office"
        assert packet.get("opening_truth", {}).get("location_source") == "arc_data.joint_docs.final_location"
        assert constraint_block.get("inherited_state", {}).get("equipment") == ["fallback-pager"]
        assert constraint_block.get("inherited_state", {}).get("injuries") == "fallback-shoulder"
        assert constraint_block.get("inherited_state", {}).get("internal_energy") == "60%"
        assert protagonist_truth.get("sources", {}).get("equipment") == "arc_data.joint_docs.physical_inventory"
        assert protagonist_truth.get("sources", {}).get("injuries") == "arc_data.status_shadow.expected_injuries"
        assert protagonist_truth.get("sources", {}).get("internal_energy") == (
            "arc_data.status_shadow.internal_energy_loss"
        )
