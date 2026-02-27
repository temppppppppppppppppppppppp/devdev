"""[LM-G] NarrativeContextFormatter + WorldState motivations/promises 테스트."""

from modules.core.narrative_context_formatter import NarrativeContextFormatter

# ═══════════════════════════════════════════════════════════════
# FormatMotivations
# ═══════════════════════════════════════════════════════════════


class TestFormatMotivations:
    """format_motivations 테스트."""

    def test_basic_format(self):
        """활성 플롯 + NPC 동기 포맷."""
        plots = {
            "복수극": {"status": "active", "first_arc": 1, "last_mention_arc": 3},
        }
        npcs = {"장무기": "강호 제패"}
        result = NarrativeContextFormatter.format_motivations(plots, npcs, current_arc_no=4)
        assert "[진행 중 동기/플롯]" in result
        assert "복수극" in result
        assert "[주요 NPC 동기]" in result
        assert "장무기" in result
        assert "강호 제패" in result

    def test_suspended_plot_warning(self):
        """방치 플롯에 경고 표시."""
        plots = {
            "오래된 플롯": {"status": "suspended", "first_arc": 1, "last_mention_arc": 2},
        }
        result = NarrativeContextFormatter.format_motivations(plots, {}, current_arc_no=6)
        assert "⚠" in result
        assert "방치" in result

    def test_empty_data(self):
        """빈 입력 → 빈 문자열."""
        assert NarrativeContextFormatter.format_motivations(None, None, 1) == ""
        assert NarrativeContextFormatter.format_motivations({}, {}, 1) == ""

    def test_resolved_plots_excluded(self):
        """resolved 상태 플롯은 제외."""
        plots = {
            "완결된 플롯": {"status": "resolved", "first_arc": 1, "last_mention_arc": 3},
            "활성 플롯": {"status": "active", "first_arc": 2, "last_mention_arc": 4},
        }
        result = NarrativeContextFormatter.format_motivations(plots, {}, current_arc_no=5)
        assert "완결된 플롯" not in result
        assert "활성 플롯" in result

    def test_gap_warning_threshold(self):
        """3+ Arc 방치 시 경고, 2 Arc 이하는 경고 없음."""
        plots = {
            "갭2": {"status": "active", "first_arc": 1, "last_mention_arc": 3},
            "갭3": {"status": "active", "first_arc": 1, "last_mention_arc": 2},
        }
        result = NarrativeContextFormatter.format_motivations(plots, {}, current_arc_no=5)
        # 갭2: 5-3=2 → 경고 없음, 갭3: 5-2=3 → 경고
        lines = result.split("\n")
        gap2_line = [x for x in lines if "갭2" in x][0]
        gap3_line = [x for x in lines if "갭3" in x][0]
        assert "⚠" not in gap2_line
        assert "⚠" in gap3_line


# ═══════════════════════════════════════════════════════════════
# FormatPromises
# ═══════════════════════════════════════════════════════════════


class TestFormatPromises:
    """format_promises 테스트."""

    def test_basic_format(self):
        """미이행 약속 포맷."""
        commits = [
            {"arc_no": 2, "parties": "장무기, 조민", "description": "무림맹주 자리 양보", "status": "pending"},
        ]
        result = NarrativeContextFormatter.format_promises(commits, current_arc_no=4)
        assert "[미이행 약속/서약]" in result
        assert "무림맹주 자리 양보" in result
        assert "장무기, 조민" in result

    def test_fulfilled_excluded(self):
        """fulfilled 상태 약속은 제외."""
        commits = [
            {"arc_no": 1, "description": "이행된 약속", "status": "fulfilled"},
            {"arc_no": 2, "description": "미이행 약속", "status": "pending"},
        ]
        result = NarrativeContextFormatter.format_promises(commits, current_arc_no=4)
        assert "이행된 약속" not in result
        assert "미이행 약속" in result

    def test_long_elapsed_warning(self):
        """3+ Arc 장기 미이행 경고."""
        commits = [
            {"arc_no": 1, "description": "오래된 약속", "status": "pending"},
        ]
        result = NarrativeContextFormatter.format_promises(commits, current_arc_no=5)
        assert "⚠" in result
        assert "장기 미이행" in result

    def test_empty_list(self):
        """빈 리스트 → 빈 문자열."""
        assert NarrativeContextFormatter.format_promises([], current_arc_no=1) == ""
        assert NarrativeContextFormatter.format_promises(None, current_arc_no=1) == ""

    def test_all_fulfilled(self):
        """전부 이행 → 빈 문자열."""
        commits = [
            {"arc_no": 1, "description": "약속1", "status": "fulfilled"},
            {"arc_no": 2, "description": "약속2", "status": "이행"},
        ]
        result = NarrativeContextFormatter.format_promises(commits, current_arc_no=5)
        assert result == ""


# ═══════════════════════════════════════════════════════════════
# FormatArcScales
# ═══════════════════════════════════════════════════════════════


class TestFormatArcScales:
    """format_arc_scales 테스트."""

    def test_basic_format(self):
        """Arc 3개 포맷."""
        arcs = [
            {"tactical_doc": "입문편: 주인공 각성\n세부 내용..."},
            {"tactical_doc": "성장편: 동료 합류\n세부 내용..."},
            {"tactical_doc": "결전편: 최종 보스\n세부 내용..."},
        ]
        result = NarrativeContextFormatter.format_arc_scales(arcs)
        assert "[Arc 스케일 진행]" in result
        assert "Arc 1" in result
        assert "입문편: 주인공 각성" in result
        assert "세부 내용" not in result  # 첫 줄만

    def test_single_arc_returns_empty(self):
        """Arc 1개 → 빈 문자열."""
        arcs = [{"tactical_doc": "유일한 Arc"}]
        assert NarrativeContextFormatter.format_arc_scales(arcs) == ""

    def test_empty_arcs(self):
        """빈 리스트 → 빈 문자열."""
        assert NarrativeContextFormatter.format_arc_scales([]) == ""
        assert NarrativeContextFormatter.format_arc_scales(None) == ""

    def test_dict_tactical_doc(self):
        """tactical_doc가 dict인 경우."""
        arcs = [
            {"tactical_doc": {"theme": "복수", "intensity": "HIGH"}},
            {"tactical_doc": {"theme": "성장", "intensity": "MEDIUM"}},
        ]
        result = NarrativeContextFormatter.format_arc_scales(arcs)
        assert "복수" in result
        assert "HIGH" in result
        assert "성장" in result


# ═══════════════════════════════════════════════════════════════
# FormatAll
# ═══════════════════════════════════════════════════════════════


class TestFormatAll:
    """format_all 통합 테스트."""

    def test_all_sections_combined(self):
        """3개 섹션 통합 + 헤더."""
        result = NarrativeContextFormatter.format_all(
            active_plots={"플롯A": {"status": "active", "first_arc": 1, "last_mention_arc": 2}},
            npc_motivations={"NPC1": "복수"},
            pending_commitments=[{"arc_no": 1, "description": "약속1", "status": "pending"}],
            all_refined_arcs=[
                {"tactical_doc": "Arc1 내용"},
                {"tactical_doc": "Arc2 내용"},
            ],
            current_arc_no=3,
        )
        assert "[LM-G 서사 구조 참고 — advisory]" in result
        assert "[진행 중 동기/플롯]" in result
        assert "[미이행 약속/서약]" in result
        assert "[Arc 스케일 진행]" in result

    def test_empty_all(self):
        """모든 데이터 없음 → 빈 문자열."""
        result = NarrativeContextFormatter.format_all(
            active_plots=None,
            npc_motivations=None,
            pending_commitments=None,
            all_refined_arcs=None,
            current_arc_no=1,
        )
        assert result == ""

    def test_max_chars_truncation(self):
        """max_chars 절삭."""
        plots = {f"플롯_{i}": {"status": "active", "first_arc": 1, "last_mention_arc": 1} for i in range(50)}
        result = NarrativeContextFormatter.format_all(
            active_plots=plots,
            npc_motivations=None,
            pending_commitments=None,
            all_refined_arcs=None,
            current_arc_no=5,
            max_chars=200,
        )
        assert len(result) <= 200
        assert "절삭" in result


# ═══════════════════════════════════════════════════════════════
# EdgeCases
# ═══════════════════════════════════════════════════════════════


class TestEdgeCases:
    """엣지케이스 방어 테스트."""

    def test_non_dict_plot_entries(self):
        """비정상 타입 플롯 엔트리 → 무시."""
        plots = {
            "정상": {"status": "active", "first_arc": 1, "last_mention_arc": 2},
            "비정상": "이건 dict가 아님",
            "비정상2": 42,
        }
        result = NarrativeContextFormatter.format_motivations(plots, {}, current_arc_no=5)
        assert "정상" in result
        assert "비정상" not in result or "비정상2" not in result.split("[진행 중 동기/플롯]")[1].split("\n")[1:]

    def test_non_dict_commitment_entries(self):
        """비정상 타입 약속 엔트리 → 무시."""
        commits = [
            {"description": "정상 약속", "status": "pending", "arc_no": 1},
            "비정상 문자열",
            42,
        ]
        result = NarrativeContextFormatter.format_promises(commits, current_arc_no=5)
        assert "정상 약속" in result
        # 비정상 엔트리는 무시됨 (에러 없음)

    def test_parties_as_string(self):
        """parties가 문자열인 경우 처리."""
        commits = [
            {"description": "약속", "status": "pending", "arc_no": 1, "parties": "장무기"},
        ]
        result = NarrativeContextFormatter.format_promises(commits, current_arc_no=2)
        assert "장무기" in result

    def test_parties_as_list(self):
        """parties가 리스트인 경우 처리."""
        commits = [
            {"description": "약속", "status": "pending", "arc_no": 1, "parties": ["장무기", "조민"]},
        ]
        result = NarrativeContextFormatter.format_promises(commits, current_arc_no=2)
        assert "장무기" in result
        assert "조민" in result


# ═══════════════════════════════════════════════════════════════
# WorldState motivations/promises
# ═══════════════════════════════════════════════════════════════


class _FakeDB:
    """WorldState 테스트용 가짜 DB."""

    def load_anchor(self, key):
        return None

    def save_anchor(self, key, value):
        pass


class TestWorldStateMotivations:
    """WorldState motivations/promises 필드 테스트."""

    def _make_ws(self):
        from modules.core.world_state import WorldStateManager

        return WorldStateManager(_FakeDB())

    def test_motivations_field_init(self):
        """motivations/promises 필드 존재 확인."""
        ws = self._make_ws()
        state = ws.get_state_dict()
        assert "motivations" in state
        assert isinstance(state["motivations"], list)
        assert "promises" in state
        assert isinstance(state["promises"], list)

    def test_update_protagonist_motivations(self):
        """동기 추가 + 상태 업데이트."""
        ws = self._make_ws()
        ws.update_from_state_changes(
            1,
            {
                "protagonist_motivations": [
                    {"text": "복수", "status": "active"},
                    {"text": "사랑", "status": "active"},
                ],
            },
        )
        state = ws.get_state_dict()
        assert len(state["motivations"]) == 2
        assert state["motivations"][0]["text"] == "복수"

        # 상태 업데이트 (중복 방지)
        ws.update_from_state_changes(
            5,
            {
                "protagonist_motivations": [
                    {"text": "복수", "status": "resolved"},
                ],
            },
        )
        state = ws.get_state_dict()
        assert len(state["motivations"]) == 2  # 중복 추가 안 됨
        resolved = [m for m in state["motivations"] if m["text"] == "복수"][0]
        assert resolved["status"] == "resolved"
        assert resolved["resolved_ep"] == 5

    def test_update_promises(self):
        """약속 추가 + 중복 방지."""
        ws = self._make_ws()
        ws.update_from_state_changes(
            1,
            {
                "commitments": [
                    {"text": "무림맹주 양보", "promiser": "장무기", "status": "pending"},
                ],
            },
        )
        state = ws.get_state_dict()
        assert len(state["promises"]) == 1
        assert state["promises"][0]["text"] == "무림맹주 양보"
        assert state["promises"][0]["promiser"] == "장무기"

        # 중복 추가 시도 → 무시
        ws.update_from_state_changes(
            2,
            {
                "commitments": [
                    {"text": "무림맹주 양보", "status": "fulfilled"},
                ],
            },
        )
        state = ws.get_state_dict()
        assert len(state["promises"]) == 1  # 중복 없음
        assert state["promises"][0]["status"] == "fulfilled"

    def test_motivations_fifo(self):
        """FIFO 20개 상한."""
        ws = self._make_ws()
        mots = [{"text": f"동기_{i}", "status": "active"} for i in range(25)]
        ws.update_from_state_changes(1, {"protagonist_motivations": mots})
        state = ws.get_state_dict()
        assert len(state["motivations"]) == 20
        # 최근 20개만 유지
        assert state["motivations"][-1]["text"] == "동기_24"
