"""[B-1-4] ChiefWriterContextBuilder unit tests."""

from unittest.mock import MagicMock

from modules.domain.agents.chief_writer_context import ChiefWriterContextBuilder


def _make_host():
    host = MagicMock()
    host._escape_braces = lambda x: str(x).replace("{", "{{").replace("}", "}}")
    host.context = MagicMock()
    host.context.db = MagicMock()
    host.context.db.get_manuscript.return_value = None
    host.context.db.load_state_log.return_value = None
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


class TestDigestAndGuards:
    def test_generate_episode_digest_empty(self):
        builder = ChiefWriterContextBuilder(_make_host())
        assert builder._generate_episode_digest("", ep_num=5) == ""

    def test_generate_episode_digest_extracts_death(self):
        builder = ChiefWriterContextBuilder(_make_host())
        manuscript = "가" * 220 + "철무련주가 숨을 거두었다. 시신이 식어갔다."
        digest = builder._generate_episode_digest(manuscript, ep_num=5)
        assert "사망 NPC" in digest

    def test_detect_deaths_from_manuscript(self):
        builder = ChiefWriterContextBuilder(_make_host())
        text = "철무련주가 최후를 맞았다. 흑도를 죽였다."
        deaths = builder._detect_deaths_from_manuscript(text)
        assert isinstance(deaths, list)
        assert len(deaths) >= 1

    def test_detect_past_events_from_manuscript(self):
        builder = ChiefWriterContextBuilder(_make_host())
        text = "중상을 입었다. 용린검을 획득했다. 회춘단을 잃었다."
        result = builder._detect_past_events_from_manuscript(text)
        assert set(result.keys()) == {"injuries", "items_gained", "items_lost", "relationship_changes"}

    def test_build_past_guard_section(self):
        builder = ChiefWriterContextBuilder(_make_host())
        text = "철무련주가 숨을 거두었다. 왼팔이 부러졌다."
        section = builder._build_past_guard_section(text, existing_dead_npcs=["흑도"])
        assert "PAST CONSTRAINT" in section

    def test_build_future_guard_section(self):
        builder = ChiefWriterContextBuilder(_make_host())
        section = builder._build_future_guard_section(
            current_inventory=["용린검"],
            current_martial_arts=["태극검법"],
            dead_npcs=["철무련주"],
            item_acquisition_timeline="제3화: 용린검 획득",
        )
        assert "HARD CONSTRAINT" in section
        assert "용린검" in section

    def test_build_future_guard_section_empty(self):
        builder = ChiefWriterContextBuilder(_make_host())
        section = builder._build_future_guard_section([], [], [], "")
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
        result = builder._check_hud_anomalies(10)
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
        result = builder._check_hud_anomalies(10)
        assert result["has_anomalies"] is True


class TestNpcAndDna:
    def test_get_npc_equipment_summary(self):
        builder = ChiefWriterContextBuilder(_make_host())
        result = builder._get_npc_equipment_summary(builder.context.master_bible)
        assert "연홍" in result
        assert "비연검" in result

    def test_get_npc_frequency(self):
        host = _make_host()
        host.context.master_bible["MasterBible"]["AssetLibrary"]["KeyNPCs"] = [{"name": "연홍"}]

        def _cached(ep):
            return {"content": "연홍이 등장했다." if ep in (2, 3) else "", "hud_snapshot": {}}

        host._get_cached_manuscript = _cached
        builder = ChiefWriterContextBuilder(host)
        freq = builder._get_npc_frequency(5, window=5)
        assert freq["연홍"] >= 2

    def test_get_npc_frequency_warning(self):
        host = _make_host()
        host.context.master_bible["MasterBible"]["AssetLibrary"]["KeyNPCs"] = [{"name": "연홍"}]
        host._get_cached_manuscript = lambda _ep: {"content": "", "hud_snapshot": {}}
        builder = ChiefWriterContextBuilder(host)
        warning = builder._get_npc_frequency_warning(5)
        assert "연홍" in warning

    def test_get_dna_instruction_ep1(self):
        builder = ChiefWriterContextBuilder(_make_host())
        result = builder._get_dna_instruction(ep_num=1, intro_dna="CYNICAL")
        assert "제1화" in result
        assert "CYNICAL" in result

    def test_get_dna_instruction_ep5(self):
        builder = ChiefWriterContextBuilder(_make_host())
        result = builder._get_dna_instruction(ep_num=5, intro_dna="CYNICAL")
        assert "연속 집필 모드" in result


class TestMandatoryAndHelpers:
    def test_build_anti_trope_instructions(self):
        builder = ChiefWriterContextBuilder(_make_host())
        result = builder._build_anti_trope_instructions("무협")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_build_mandatory_context(self):
        builder = ChiefWriterContextBuilder(_make_host())
        result = builder._build_mandatory_context(current_ep=1)
        assert "MANDATORY CONTEXT" in result

    def test_extract_recent_events(self):
        host = _make_host()
        host.context.db.load_state_log.side_effect = [
            {"summary": "요약 A", "data": {"major_changes": [{"event": "사건 A", "consequence": "결과 A"}]}},
            {"summary": "요약 B", "data": {"major_changes": []}},
            None,
        ]
        builder = ChiefWriterContextBuilder(host)
        result = builder._extract_recent_events(current_ep=4, n_episodes=3)
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_extract_npc_last_states(self):
        builder = ChiefWriterContextBuilder(_make_host())
        states = builder._extract_npc_last_states(current_ep=10)
        assert "연홍" in states
        assert "relationship" in states["연홍"]

    def test_build_justification_guidance_physical(self):
        builder = ChiefWriterContextBuilder(_make_host())
        result = builder._build_justification_guidance("중상 상태, 기력고갈", "무협")
        assert "신체 제약 감지" in result

    def test_build_justification_guidance_none(self):
        builder = ChiefWriterContextBuilder(_make_host())
        result = builder._build_justification_guidance("현재 상태: 정상", "무협")
        assert result == ""
