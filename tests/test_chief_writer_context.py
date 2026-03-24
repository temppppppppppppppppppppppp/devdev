"""[B-1-4] ChiefWriterContextBuilder unit tests."""

from unittest.mock import MagicMock, patch

from modules.domain.agents.chief_writer_context import ChiefWriterContextBuilder
from modules.domain.agents.chief_writer_context_packets import ChiefWriterContextPackets
from modules.domain.agents.chief_writer_prompts import build_chief_writer_main_prompt


def _make_host():
    host = MagicMock()
    host._escape_braces = lambda x: str(x).replace("{", "{{").replace("}", "}}")
    host.context = MagicMock()
    host.context.db = MagicMock()
    host.context.db.get_manuscript.return_value = None
    host.context.db.load_state_log.return_value = None
    host.context.db.load_anchor.return_value = {"_genre": "wuxia"}
    host.context.master_bible = {
        "MasterBible": {
            "ProjectData": {"CoreIdentity": {"desire": "천하제일"}},
            "AssetLibrary": {
                "KeyNPCs": [
                    {
                        "name": "연홍",
                        "relationship_state": "경외",
                        "last_appearance_ep": 3,
                        "NPC_Martial_HUD": {"equipment": ["비연검"]},
                    }
                ],
                "Key_Items": [],
            },
            "protagonist_config": {"world_origin": "현대인", "incarnation_type": "회귀자"},
            "_genre": "wuxia",
        }
    }
    host._get_cached_manuscript = lambda _ep: {"content": "", "hud_snapshot": {}}
    return host


class TestInitAndContext:
    def test_context_builder_init(self):
        host = _make_host()
        builder = ChiefWriterContextBuilder(host)
        assert builder.host is host
        assert isinstance(builder.context_packets, ChiefWriterContextPackets)

    def test_context_property(self):
        host = _make_host()
        builder = ChiefWriterContextBuilder(host)
        assert builder.context is host.context


class TestBuildCommonContext:
    def test_build_common_context_returns_string(self):
        host = _make_host()
        builder = ChiefWriterContextBuilder(host)
        blueprint = {"scene_breakdown": {"scene_1": {"summary": "테스트"}}, "integrated_scenario": "통합"}

        result = builder.build_common_context(
            ep_num=5,
            blueprint=blueprint,
            prev_manuscript="",
            hud_report="내공: 50",
            arc_doc="아크",
            master_bible=host.context.master_bible,
            style_guide="카카오 스타일",
            director_feedback="",
            failure_constraints="",
        )

        assert isinstance(result, str)
        assert len(result) > 100

    def test_build_common_context_with_feedback(self):
        host = _make_host()
        builder = ChiefWriterContextBuilder(host)
        blueprint = {"scene_breakdown": {}, "integrated_scenario": ""}
        result = builder.build_common_context(
            ep_num=5,
            blueprint=blueprint,
            prev_manuscript="",
            hud_report="",
            arc_doc="",
            master_bible=host.context.master_bible,
            style_guide="",
            director_feedback="대화 비율 보강",
            failure_constraints="",
        )
        assert "Director 피드백" in result


    def test_build_common_context_delegates_packet_bundle(self):
        host = _make_host()
        builder = ChiefWriterContextBuilder(host)
        builder.context_packets.build_common_context_packets = MagicMock(
            return_value={
                "prev_ending": "tail",
                "prev_digest": "digest",
                "future_guard_section": "future",
                "past_guard_section": "past",
                "npc_equipment_section": "equip",
                "npc_frequency_section": "freq",
                "hud_trend_section": "trend",
                "hud_anomaly_section": "warn",
                "dna_instruction": "dna",
                "high_density_hud_section": "hd",
                "prev_manuscripts_section": "prev-full",
            }
        )

        with patch("modules.domain.agents.chief_writer_context.build_chief_writer_main_prompt", return_value="prompt"):
            result = builder.build_common_context(
                ep_num=5,
                blueprint={"scene_breakdown": {}, "integrated_scenario": ""},
                prev_manuscript="",
                hud_report="HUD",
                arc_doc="arc",
                master_bible=host.context.master_bible,
                style_guide="",
                director_feedback="",
                failure_constraints="",
            )

        assert result == "prompt"
        builder.context_packets.build_common_context_packets.assert_called_once()

    def test_extract_blueprint_sections_includes_integrated_scenario_and_hook(self):
        builder = ChiefWriterContextBuilder(_make_host())

        scene_breakdown, integrated_advisory, ending_hook, opening_anchor = builder._extract_blueprint_sections(
            {
                "scene_breakdown": {"scene_1": {"summary": "대치"}},
                "integrated_scenario": "통합 흐름",
                "ending_hook": "문이 열린다",
            }
        )

        assert "통합 흐름" not in scene_breakdown
        assert "낮은 우선순위" in integrated_advisory
        assert "통합 흐름" in integrated_advisory
        assert "문이 열린다" in ending_hook

    def test_build_character_voice_section_uses_stage4_fallback(self):
        host = _make_host()
        host.context.character_voice = None
        stage4_voice = MagicMock()
        stage4_voice.get_writing_guide.return_value = "연홍은 격식을 유지한다."
        host._stage4_ctx = MagicMock(character_voice=stage4_voice)
        builder = ChiefWriterContextBuilder(host)

        section = builder._build_character_voice_section(
            {"scene_breakdown": {"scene_1": {"npcs": ["연홍", "백운"]}}}
        )

        assert "연홍은 격식을 유지한다." in section
        stage4_voice.get_writing_guide.assert_called_once_with(["연홍", "백운"])

    def test_build_common_context_shell_uses_helper_sections_and_host_directive(self):
        host = _make_host()
        directive = MagicMock()
        directive.is_empty.return_value = False
        directive.ending_style = "절단"
        directive.ending_avoid_phrases = ["모든 것이 끝났다"]
        directive.expression_ban = ["빙긋"]
        directive.metaphor_avoid = ["불꽃처럼"]
        directive.metaphor_suggest = ["먹구름처럼"]
        directive.emotion_required = "후회"
        directive.npc_directives = {"연홍": "격식 유지"}
        directive.intensity_note = "후반으로 갈수록 압박"
        host._tf54_writing_directive = directive
        builder = ChiefWriterContextBuilder(host)
        builder.context_packets.build_common_context_packets = MagicMock(
            return_value={
                "prev_ending": "tail",
                "prev_digest": "digest",
                "future_guard_section": "future",
                "past_guard_section": "past",
                "npc_equipment_section": "equip",
                "npc_frequency_section": "freq",
                "hud_trend_section": "trend",
                "hud_anomaly_section": "warn",
                "dna_instruction": "dna",
                "high_density_hud_section": "hd",
                "prev_manuscripts_section": "prev-full",
            }
        )

        with patch("modules.domain.agents.chief_writer_context.build_chief_writer_main_prompt", return_value="prompt") as mock_prompt:
            result = builder.build_common_context(
                ep_num=5,
                blueprint={
                    "scene_breakdown": {"scene_1": {"npcs": ["연홍"]}},
                    "integrated_scenario": "통합 흐름",
                    "ending_hook": "누군가 문을 두드린다",
                },
                prev_manuscript="",
                hud_report="HUD",
                arc_doc="arc",
                master_bible=host.context.master_bible,
                style_guide="",
                director_feedback="대화 비율 보강",
                failure_constraints="독백 과다 금지",
                world_state_summary="문파 긴장 고조",
                reference_excerpt="참고 문장",
            )

        assert result == "prompt"
        kwargs = mock_prompt.call_args.kwargs
        assert "대화 비율 보강" in kwargs["feedback_section"]
        assert "독백 과다 금지" in kwargs["constraint_section"]
        assert "문파 긴장 고조" in kwargs["writer_core_section"]
        assert "절단" in kwargs["writer_core_section"]
        assert "참고 문장" in kwargs["reference_excerpt_section"]
        assert "누군가 문을 두드린다" in kwargs["ending_hook_section"]
        assert "회귀자" in kwargs["incarnation_context_section"]
        assert "통합 시나리오 초안" in kwargs["integrated_scenario_advisory_section"]

    def test_main_prompt_places_opening_anchor_before_prev_digest(self):
        prompt = build_chief_writer_main_prompt(
            ep_num=5,
            dna_instruction="dna",
            purism_section="purism",
            world_origin_constraint_section="origin",
            feedback_section="feedback",
            constraint_section="constraint",
            future_guard_section="future",
            past_guard_section="past",
            writer_core_section="writer-core",
            hud_anomaly_section="hud-anomaly",
            scene_breakdown="scene-breakdown",
            prev_digest="PREV-DIGEST",
            prev_ending="PREV-ENDING",
            hud_report="HUD",
            high_density_hud_section="hd-hud",
            hud_trend_section="hud-trend",
            npc_equipment_section="npc-equip",
            npc_frequency_section="npc-freq",
            arc_doc="arc",
            core_identity_desire="desire",
            style_guide="style",
            common_rules="common-rules",
            writing_guidelines="guidelines",
            opening_anchor_section="OPENING-ANCHOR",
        )

        assert prompt.index("OPENING-ANCHOR") < prompt.index("PREV-DIGEST")
        assert "Blueprint의 시작 장소/시간이 직전 화 종료 상태보다 우선한다." in prompt

    def test_main_prompt_marks_integrated_scenario_as_advisory_and_applies_precedence(self):
        prompt = build_chief_writer_main_prompt(
            ep_num=5,
            dna_instruction="dna",
            purism_section="purism",
            world_origin_constraint_section="origin",
            feedback_section="feedback",
            constraint_section="constraint",
            future_guard_section="future",
            past_guard_section="past",
            writer_core_section="writer-core",
            hud_anomaly_section="hud-anomaly",
            scene_breakdown="scene-breakdown",
            prev_digest="PREV-DIGEST",
            prev_ending="PREV-ENDING",
            hud_report="HUD",
            high_density_hud_section="hd-hud",
            hud_trend_section="hud-trend",
            npc_equipment_section="npc-equip",
            npc_frequency_section="npc-freq",
            arc_doc="arc",
            core_identity_desire="desire",
            style_guide="style",
            common_rules="common-rules",
            writing_guidelines="guidelines",
            integrated_scenario_advisory_section="ADVISORY-INTEGRATED",
            carryover_ceiling_section="CARRYOVER-CEILING",
        )

        assert "권위 우선순위" in prompt
        assert "Structured scene breakdown" in prompt
        assert "Advisory integrated scenario prose" in prompt
        assert prompt.index("scene-breakdown") < prompt.index("ADVISORY-INTEGRATED")
        assert "CARRYOVER-CEILING" in prompt


class TestDigestAndGuards:
    def test_generate_episode_digest_authority_moved_to_context_packets(self):
        builder = ChiefWriterContextBuilder(_make_host())
        assert not hasattr(builder, "_generate_episode_digest")
        assert hasattr(builder.context_packets, "_generate_episode_digest")

    def test_fit_compact_text_preserves_tail_context(self):
        builder = ChiefWriterContextBuilder(_make_host())

        text = "HEAD-DIGEST\n" + ("A" * 80) + "\nTAIL-DIGEST"
        result = builder._fit_compact_text(text, 30)

        assert "TAIL-DIGEST" in result
        assert "..." in result

    def test_generate_episode_digest_empty(self):
        builder = ChiefWriterContextBuilder(_make_host())
        assert builder.context_packets._generate_episode_digest("", ep_num=5) == ""

    def test_generate_episode_digest_extracts_death(self):
        builder = ChiefWriterContextBuilder(_make_host())
        manuscript = "가" * 220 + "철무련주가 숨을 거두었다. 시신이 식어갔다."
        digest = builder.context_packets._generate_episode_digest(manuscript, ep_num=5)
        assert "사망 NPC" in digest

    def test_generate_episode_digest_preserves_cliffhanger_tail_context(self):
        builder = ChiefWriterContextBuilder(_make_host())
        manuscript = "媛" * 220 + ("A" * 120) + " TAIL-CLIFF"

        with patch("modules.domain.agents.chief_writer_context_packets.re.search", return_value=True):
            digest = builder.context_packets._generate_episode_digest(manuscript, ep_num=5)

        assert "TAIL-CLIFF" in digest
        assert "..." in digest

    def test_detect_deaths_from_manuscript(self):
        builder = ChiefWriterContextBuilder(_make_host())
        text = "철무련주가 최후를 맞았다. 흑도를 죽였다."
        deaths = builder.context_packets._detect_deaths_from_manuscript(text)
        assert isinstance(deaths, list)
        assert len(deaths) >= 1

    def test_detect_past_events_from_manuscript(self):
        builder = ChiefWriterContextBuilder(_make_host())
        text = "중상을 입었다. 용린검을 획득했다. 회춘단을 잃었다."
        result = builder.context_packets._detect_past_events_from_manuscript(text)
        assert set(result.keys()) == {"injuries", "items_gained", "items_lost", "relationship_changes"}

    def test_build_past_guard_section(self):
        builder = ChiefWriterContextBuilder(_make_host())
        text = "철무련주가 숨을 거두었다. 왼팔이 부러졌다."
        section = builder.context_packets._build_past_guard_section(text, existing_dead_npcs=["흑도"])
        assert "PAST CONSTRAINT" in section

    def test_build_future_guard_section(self):
        builder = ChiefWriterContextBuilder(_make_host())
        section = builder.context_packets._build_future_guard_section(
            current_inventory=["용린검"],
            current_martial_arts=["태극검법"],
            dead_npcs=["철무련주"],
            item_acquisition_timeline="제3화: 용린검 획득",
        )
        assert "HARD CONSTRAINT" in section
        assert "용린검" in section

    def test_build_future_guard_section_empty(self):
        builder = ChiefWriterContextBuilder(_make_host())
        section = builder.context_packets._build_future_guard_section([], [], [], "")
        assert "HARD CONSTRAINT" in section


class TestHudMethods:
    def test_extract_numeric_value_int(self):
        builder = ChiefWriterContextBuilder(_make_host())
        assert builder._extract_numeric_value(42) == 42

    def test_extract_numeric_value_string(self):
        builder = ChiefWriterContextBuilder(_make_host())
        assert builder._extract_numeric_value("내공 +300") == 300

    def test_extract_numeric_value_none(self):
        builder = ChiefWriterContextBuilder(_make_host())
        assert builder._extract_numeric_value(None) == 0

    def test_check_hud_anomalies_no_data(self):
        builder = ChiefWriterContextBuilder(_make_host())
        result = builder.context_packets._check_hud_anomalies(10)
        assert result["has_anomalies"] is False

    def test_check_hud_anomalies_energy_spike(self):
        host = _make_host()

        def _cached(ep):
            if ep == 8:
                return {"content": "x", "hud_snapshot": {"internal_energy": "100", "realm": "이류"}}
            if ep == 9:
                return {"content": "x", "hud_snapshot": {"internal_energy": "900", "realm": "일류"}}
            return {"content": "", "hud_snapshot": {}}

        host._get_cached_manuscript = _cached
        builder = ChiefWriterContextBuilder(host)
        result = builder.context_packets._check_hud_anomalies(10)
        assert result["has_anomalies"] is True


class TestNpcAndDna:
    def test_get_npc_equipment_summary(self):
        builder = ChiefWriterContextBuilder(_make_host())
        result = builder.context_packets._get_npc_equipment_summary(builder.context.master_bible)
        assert "연홍" in result
        assert "비연검" in result

    def test_get_npc_frequency(self):
        host = _make_host()
        host.context.master_bible["MasterBible"]["AssetLibrary"]["KeyNPCs"] = [{"name": "연홍"}]

        def _cached(ep):
            return {"content": "연홍이 등장했다." if ep in (2, 3) else "", "hud_snapshot": {}}

        host._get_cached_manuscript = _cached
        builder = ChiefWriterContextBuilder(host)
        freq = builder.context_packets._get_npc_frequency(5, window=5)
        assert freq["연홍"] >= 2

    def test_get_npc_frequency_warning(self):
        host = _make_host()
        host.context.master_bible["MasterBible"]["AssetLibrary"]["KeyNPCs"] = [{"name": "연홍"}]
        host._get_cached_manuscript = lambda _ep: {"content": "", "hud_snapshot": {}}
        builder = ChiefWriterContextBuilder(host)
        warning = builder.context_packets._get_npc_frequency_warning(5)
        assert "연홍" in warning

    def test_get_dna_instruction_ep1(self):
        builder = ChiefWriterContextBuilder(_make_host())
        result = builder.context_packets._get_dna_instruction(ep_num=1, intro_dna="CYNICAL")
        assert "제1화" in result
        assert "CYNICAL" in result

    def test_get_dna_instruction_ep5(self):
        builder = ChiefWriterContextBuilder(_make_host())
        result = builder.context_packets._get_dna_instruction(ep_num=5, intro_dna="CYNICAL")
        assert "연속 집필 모드" in result


class TestMandatoryAndHelpers:
    def test_build_anti_trope_instructions(self):
        builder = ChiefWriterContextBuilder(_make_host())
        result = builder._build_anti_trope_instructions("무협")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_build_mandatory_context(self):
        builder = ChiefWriterContextBuilder(_make_host())
        result = builder.context_packets._build_mandatory_context(current_ep=1)
        assert "MANDATORY CONTEXT" in result

    def test_extract_recent_events(self):
        host = _make_host()
        host.context.db.load_state_log.side_effect = [
            {"summary": "요약 A", "data": {"major_changes": [{"event": "사건 A", "consequence": "결과 A"}]}},
            {"summary": "요약 B", "data": {"major_changes": []}},
            None,
        ]
        builder = ChiefWriterContextBuilder(host)
        result = builder.context_packets._extract_recent_events(current_ep=4, n_episodes=3)
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_extract_recent_events_preserves_summary_tail_context(self):
        host = _make_host()
        host.context.db.load_state_log.side_effect = [
            {
                "summary": "HEAD-SUMMARY\n" + ("S" * 260) + "\nTAIL-RECENT-EVENT",
                "data": {"major_changes": []},
            },
            None,
            None,
        ]
        builder = ChiefWriterContextBuilder(host)
        result = builder.context_packets._extract_recent_events(current_ep=4, n_episodes=3)
        assert any("TAIL-RECENT-EVENT" in item["description"] for item in result)
        assert any("..." in item["description"] for item in result)

    def test_extract_recent_events_preserves_major_change_tail_context(self):
        host = _make_host()
        host.context.db.load_state_log.side_effect = [
            {
                "summary": "",
                "data": {
                    "major_changes": [
                        {
                            "event": "HEAD-EVENT\n" + ("E" * 180) + "\nTAIL-MAJOR-EVENT",
                            "consequence": "HEAD-CONSEQ\n" + ("C" * 180) + "\nTAIL-MAJOR-CONSEQ",
                        }
                    ]
                },
            },
            None,
            None,
        ]
        builder = ChiefWriterContextBuilder(host)
        result = builder.context_packets._extract_recent_events(current_ep=4, n_episodes=3)
        assert any("TAIL-MAJOR-EVENT" in item["description"] for item in result)
        assert any("TAIL-MAJOR-CONSEQ" in item["consequence"] for item in result)
        assert any("..." in item["description"] for item in result)

    def test_extract_npc_last_states(self):
        builder = ChiefWriterContextBuilder(_make_host())
        states = builder.context_packets._extract_npc_last_states(current_ep=10)
        assert "연홍" in states
        assert "relationship" in states["연홍"]

    def test_build_justification_guidance_physical(self):
        builder = ChiefWriterContextBuilder(_make_host())
        result = builder.context_packets._build_justification_guidance("중상 상태, 기력고갈", "무협")
        assert "신체 제약 감지" in result

    def test_build_justification_guidance_none(self):
        builder = ChiefWriterContextBuilder(_make_host())
        result = builder.context_packets._build_justification_guidance("현재 상태: 정상", "무협")
        assert result == ""


class TestFinancialDigest:
    """[V73] 금융 상태 다이제스트 추출 테스트"""

    def test_digest_extracts_arabic_capital(self):
        builder = ChiefWriterContextBuilder(_make_host())
        manuscript = "가" * 220 + "잔고 131억 원의 잔고 증명서를 꺼내 보였다."
        digest = builder.context_packets._generate_episode_digest(manuscript, ep_num=10)
        assert "확정 자본" in digest
        assert "131억" in digest

    def test_digest_extracts_multiple_capitals(self):
        builder = ChiefWriterContextBuilder(_make_host())
        manuscript = "가" * 220 + "자본금 80억에서 현금 57억으로 줄어들었다."
        digest = builder.context_packets._generate_episode_digest(manuscript, ep_num=11)
        assert "확정 자본" in digest

    def test_digest_no_capital_for_non_financial(self):
        builder = ChiefWriterContextBuilder(_make_host())
        manuscript = "가" * 220 + "검을 뽑아들었다. 내공이 폭발했다."
        digest = builder.context_packets._generate_episode_digest(manuscript, ep_num=5)
        assert "확정 자본" not in digest

    def test_digest_capital_with_comma_number(self):
        builder = ChiefWriterContextBuilder(_make_host())
        manuscript = "가" * 220 + "예수금 1,500만 원이 남았다."
        digest = builder.context_packets._generate_episode_digest(manuscript, ep_num=3)
        assert "확정 자본" in digest
        assert "1,500만" in digest

    def test_digest_reverse_pattern(self):
        """'80억의 자본' 같은 역순 패턴 테스트"""
        builder = ChiefWriterContextBuilder(_make_host())
        manuscript = "가" * 220 + "80억의 자본을 투입했다."
        digest = builder.context_packets._generate_episode_digest(manuscript, ep_num=7)
        assert "확정 자본" in digest


class TestIFCPacketInputWiring:
    """[IFC] Verify that _build_immutable_fact_section receives all supported inputs."""

    def test_prev_digest_flows_into_ifc_packet(self):
        """prev_digest from packet_sections must reach build_packet for completed-event extraction."""
        builder = ChiefWriterContextBuilder(_make_host())
        # prev_manuscript with a death event generates a digest containing "사망"
        prev_ms = "가" * 220 + "적장군이 사망했다. 전투는 완료됐다."
        section = builder._build_immutable_fact_section(
            blueprint={"start_location": "호텔", "scene_breakdown": {}},
            prev_manuscript=prev_ms,
            world_state_summary="- 적장군: 사망(deceased)",
            chain_link_section="",
            prev_digest="- 적장군 처단 완료\n- 전투 종결",
        )
        # completed-event facts should contain the event from prev_digest
        assert "처단" in section or "종결" in section

    def test_world_state_summary_feeds_committed_state_facts(self):
        """world_state_summary with financial facts must populate committed_state_facts."""
        builder = ChiefWriterContextBuilder(_make_host())
        section = builder._build_immutable_fact_section(
            blueprint={"start_location": "사무실"},
            prev_manuscript="",
            world_state_summary="- 자본금: 38억\n- 직원 수: 5명",
            chain_link_section="",
            prev_digest="",
        )
        assert "38억" in section

    def test_ifc_section_empty_when_no_inputs(self):
        """Empty inputs should produce empty section."""
        builder = ChiefWriterContextBuilder(_make_host())
        section = builder._build_immutable_fact_section(
            blueprint={},
            prev_manuscript="",
            world_state_summary="",
            chain_link_section="",
            prev_digest="",
        )
        assert section == ""

    def test_stage4_carryover_ceiling_blocks_unestablished_infrastructure_and_replay(self):
        builder = ChiefWriterContextBuilder(_make_host())
        prev_ms = (
            "창가에 선 채 가죽 양장 노트의 절반을 숫자로 채웠다. "
            "WTI 진입 시점과 청산 가격 계산도 이미 끝냈다."
        )
        section = builder.context_packets._build_stage4_carryover_ceiling_section(
            blueprint={"scene_breakdown": {"scene_1": {"goal": "다음 행동 결정"}}},
            prev_manuscript=prev_ms,
            prev_digest="- 확정 자본: 20억\n- 소도구/장비 상태: 가죽 양장 노트",
        )

        assert "Stage4 Carryover Ceiling" in section
        assert "창가" in section
        assert "노트" in section
        assert "다시 쓰지 마라" in section
        assert "대포폰" in section
