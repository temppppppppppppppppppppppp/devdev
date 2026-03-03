"""Stage4 InterviewRound _cv_context 배선 검증 테스트.

3건의 runtime warning 수정을 검증:
- P1: protagonist_name — HUDKeys.get_protagonist_name() 경로
- P1: prev_hud — self.ctx.sys.hud.pro_root 배선
- P2: ConsistencyValidator 3 checks (karma_matrix, villain_context, authority_context)
"""

from unittest.mock import MagicMock

from modules.core.stage4_interview_round import Stage4InterviewRound
from modules.core.stage4_orchestrator import _RoundContext


def _make_ctx(*, master_bible=None, next_ep=3):
    ctx = MagicMock()
    ctx.ui = MagicMock()
    ctx.perf_timer = MagicMock()
    ctx.current_project = MagicMock()
    ctx.current_project.master_bible = master_bible or {"MasterBible": {}}
    ctx.current_project.db = MagicMock()
    ctx.current_project.db.get_recent_manuscripts.return_value = []
    ctx.current_project.db.get_manuscript.return_value = {"content": "이전 원고"}
    ctx.current_project.db.get_episode_bible.return_value = {}
    ctx.state_tracker = MagicMock()
    ctx.state_tracker.npc_registry = {}
    ctx.state_tracker.item_state_registry = {}
    ctx.state_tracker.get_npc_change_history.return_value = []
    ctx.state_tracker.check_destroyed_entity_in_manuscript.return_value = []
    ctx.state_tracker.in_world_timeline = []
    ctx.state_tracker.check_time_consistency.return_value = []
    ctx.agents = {"director": MagicMock()}
    ctx.context_advisor = None
    ctx.memory = None
    ctx.get_module = MagicMock(return_value=None)
    # sys.hud for prev_hud
    ctx.sys = MagicMock()
    ctx.sys.hud = None
    return ctx


def _make_round_ctx(*, next_ep=3, genre_name="투자"):
    chief_writer = MagicMock()
    chief_writer.generate_ensemble.return_value = [
        {"manuscript": "테스트 원고 " * 300, "strategy_name": "balanced", "title": "테스트"}
    ]

    manuscript_validator = MagicMock()
    manuscript_validator.validate_all_candidates.return_value = [
        {"warnings": [], "warning_count": 0, "focus_points": [], "metrics": {"length": 2000}}
    ]
    consistency_validator = MagicMock()
    consistency_validator.validate.return_value = {"violations": [], "score_penalty": 0}
    blocking_validator = MagicMock()
    blocking_validator.validate.return_value = {"passed": True, "failures": []}
    continuity_validator = MagicMock()
    continuity_validator.validate.return_value = {"violations": [], "warnings": []}
    continuity_validator.check_frustration_streak.return_value = []

    return _RoundContext(
        chief_writer=chief_writer,
        manuscript_validator=manuscript_validator,
        consistency_validator=consistency_validator,
        blocking_validator=blocking_validator,
        continuity_validator=continuity_validator,
        next_ep=next_ep,
        blueprint={"integrated_scenario": "테스트"},
        arc_data={"arc_no": 1},
        arc_pos=1,
        total_ep_in_arc=10,
        arc_tactical="전술",
        prev_text="이전 원고",
        prev_ending="엔딩",
        prev_manuscripts_text="",
        episode_digest="",
        hud_report="HUD",
        current_inventory=[],
        current_martial_arts=[],
        dead_npcs=[],
        item_acquisition_timeline="",
        chain_link_section="",
        world_state_summary="",
        purism_prompt="",
        genre_name=genre_name,
        npc_equipment_summary="",
        effective_anti_trope="",
        intro_dna="CYNICAL",
        story_context="",
        style_guide="",
        reference_anchor_prompt="",
        mandatory_context="",
        justification_prompt="",
        reflexion_prompt="",
        preflight_advisory="",
    )


def _run_and_capture_cv_context(ctx, round_ctx):
    """InterviewRound.run()을 실행하고 ConsistencyValidator.validate에 전달된 _cv_context를 캡처."""
    ir = Stage4InterviewRound(ctx)
    cv = round_ctx.consistency_validator

    # Director가 REJECT 반환 (빠른 종료)
    ctx.agents["director"].select_and_judge_ensemble.return_value = {
        "selected": "A",
        "verdict": "REJECT",
        "score": 50,
        "feedback": {"issues": ["테스트"]},
        "action_items": ["수정 필요"],
        "selected_candidate": {"manuscript": "원고", "strategy": "balanced"},
    }

    ir.run(
        round_num=0,
        stage4_spinner=MagicMock(),
        director_feedback="",
        previous_attempt=None,
        round_ctx=round_ctx,
    )

    # cv.validate 호출에서 _cv_context (두 번째 인수) 캡처
    if cv.validate.called:
        return cv.validate.call_args[0][1]  # positional arg [1] = _cv_context
    return None


# ═══════════════════════════════════════════════════════════════
# Test 1: protagonist_name — HUDKeys.get_protagonist_name() 경로
# ═══════════════════════════════════════════════════════════════


class TestProtagonistName:
    def test_protagonist_name_from_hud_keys(self):
        """HUDKeys.get_protagonist_name()이 반환한 이름이 _cv_context에 주입된다."""
        bible = {
            "MasterBible": {
                "ProjectData": {"CoreIdentity": {"protagonist": "서진우"}},
                "FinanceHUD": {"Protagonist": {"actual_truth": {"name": "서진우"}}},
            }
        }
        ctx = _make_ctx(master_bible=bible)
        round_ctx = _make_round_ctx(genre_name="투자")
        cv_context = _run_and_capture_cv_context(ctx, round_ctx)

        assert cv_context is not None
        assert cv_context.get("protagonist_name") == "서진우"

    def test_protagonist_name_fallback_warning(self):
        """Bible에 주인공 이름이 없으면 protagonist_name 키가 없고 warning 로그 발생."""
        bible = {"MasterBible": {}}
        ctx = _make_ctx(master_bible=bible)
        round_ctx = _make_round_ctx(genre_name="투자")
        cv_context = _run_and_capture_cv_context(ctx, round_ctx)

        assert cv_context is not None
        # "주인공" 기본값은 실제 이름이 아니므로 주입하지 않음
        assert "protagonist_name" not in cv_context

    def test_protagonist_name_rejects_role_name(self):
        """HUDKeys가 역할명('주인공')을 반환하면 주입하지 않는다."""
        bible = {"MasterBible": {"FinanceHUD": {"Protagonist": {"actual_truth": {"name": "투자자"}}}}}
        ctx = _make_ctx(master_bible=bible)
        round_ctx = _make_round_ctx(genre_name="투자")
        cv_context = _run_and_capture_cv_context(ctx, round_ctx)

        assert cv_context is not None
        # "투자자"는 역할명 블랙리스트 → HUDKeys가 "주인공" 반환 → 주입 안 됨
        assert "protagonist_name" not in cv_context


# ═══════════════════════════════════════════════════════════════
# Test 2: prev_hud — sys.hud.pro_root 배선
# ═══════════════════════════════════════════════════════════════


class TestPrevHud:
    def test_prev_hud_injected_when_ep_gt_1(self):
        """next_ep > 1이고 HUD가 있으면 _cv_context['prev_hud']에 주입된다."""
        ctx = _make_ctx()
        hud_mock = MagicMock()
        hud_mock.pro_root = {"name": "서진우", "wealth": "100억", "location": "서울"}
        ctx.sys.hud = hud_mock

        round_ctx = _make_round_ctx(next_ep=3)
        cv_context = _run_and_capture_cv_context(ctx, round_ctx)

        assert cv_context is not None
        assert cv_context["prev_hud"] == {"name": "서진우", "wealth": "100억", "location": "서울"}
        assert cv_context["martial_hud"] == cv_context["prev_hud"]

    def test_prev_hud_empty_on_ep_1(self):
        """next_ep == 1이면 prev_hud는 빈 dict."""
        ctx = _make_ctx()
        hud_mock = MagicMock()
        hud_mock.pro_root = {"name": "서진우"}
        ctx.sys.hud = hud_mock

        round_ctx = _make_round_ctx(next_ep=1)
        cv_context = _run_and_capture_cv_context(ctx, round_ctx)

        assert cv_context is not None
        assert cv_context["prev_hud"] == {}

    def test_prev_hud_empty_when_no_hud(self):
        """HUD 모듈이 없으면 prev_hud는 빈 dict."""
        ctx = _make_ctx()
        ctx.sys.hud = None

        round_ctx = _make_round_ctx(next_ep=3)
        cv_context = _run_and_capture_cv_context(ctx, round_ctx)

        assert cv_context is not None
        assert cv_context["prev_hud"] == {}


# ═══════════════════════════════════════════════════════════════
# Test 3: karma_matrix — DB karma → NPC별 dict 변환
# ═══════════════════════════════════════════════════════════════


class TestKarmaMatrix:
    def test_karma_matrix_assembled_from_db(self):
        """DB episode_bible에 karma 데이터가 있으면 dict 형태로 변환된다."""
        ctx = _make_ctx()
        ctx.current_project.db.get_episode_bible.return_value = {
            "karma_matrix": [
                {"target": "김대표", "relation": "적대", "type": "배신", "description": "자금 횡령"},
                {"target": "김대표", "relation": "적대", "type": "복수", "description": "법적 대응"},
                {"target": "박비서", "relation": "신뢰", "type": "도움", "description": "내부 정보 제공"},
            ]
        }
        round_ctx = _make_round_ctx(next_ep=3)
        cv_context = _run_and_capture_cv_context(ctx, round_ctx)

        assert cv_context is not None
        km = cv_context.get("karma_matrix", {})
        assert "김대표" in km
        assert km["김대표"]["relation_type"] == "적대"
        assert len(km["김대표"]["events"]) == 2
        assert "박비서" in km
        assert len(km["박비서"]["events"]) == 1

    def test_karma_matrix_empty_when_no_data(self):
        """DB에 karma 데이터가 없으면 karma_matrix는 기본 빈 dict 유지."""
        ctx = _make_ctx()
        ctx.current_project.db.get_episode_bible.return_value = {}
        round_ctx = _make_round_ctx(next_ep=3)
        cv_context = _run_and_capture_cv_context(ctx, round_ctx)

        assert cv_context is not None
        assert cv_context.get("karma_matrix") == {}


# ═══════════════════════════════════════════════════════════════
# Test 4: villain_context — KeyNPCs 빌런 키워드 매칭
# ═══════════════════════════════════════════════════════════════


class TestVillainContext:
    def test_villain_context_from_key_npcs(self):
        """KeyNPCs에 빌런 키워드 NPC가 있으면 villain_context가 생성된다."""
        bible = {
            "MasterBible": {
                "AssetLibrary": {
                    "KeyNPCs": [
                        {"name": "서진우", "role": "주인공"},
                        {"name": "장현석", "role": "적대 세력 수장"},
                        {"name": "박비서", "role": "조력자"},
                    ]
                }
            }
        }
        ctx = _make_ctx(master_bible=bible)
        round_ctx = _make_round_ctx(next_ep=3)
        cv_context = _run_and_capture_cv_context(ctx, round_ctx)

        assert cv_context is not None
        vc = cv_context.get("villain_context", {})
        assert vc.get("villain_name") == "장현석"
        assert "적대" in vc.get("villain_role", "")
        assert vc.get("is_aware") is True

    def test_deceased_villain_excluded(self):
        """npc_registry에서 deceased인 빌런은 villain_context에서 제외된다."""
        bible = {
            "MasterBible": {
                "AssetLibrary": {
                    "KeyNPCs": [
                        {"name": "장현석", "role": "적대 세력 수장"},
                    ]
                }
            }
        }
        ctx = _make_ctx(master_bible=bible)
        ctx.state_tracker.npc_registry = {"장현석": {"status": "dead"}}
        round_ctx = _make_round_ctx(next_ep=3)
        cv_context = _run_and_capture_cv_context(ctx, round_ctx)

        assert cv_context is not None
        assert cv_context.get("villain_context", {}) == {}

    def test_deceased_villain_skipped_to_next(self):
        """첫 빌런이 사망하면 다음 빌런 후보로 넘어간다."""
        bible = {
            "MasterBible": {
                "AssetLibrary": {
                    "KeyNPCs": [
                        {"name": "장현석", "role": "적대 세력 1대 수장"},
                        {"name": "장현석Jr", "role": "숙적, 2대 수장"},
                    ]
                }
            }
        }
        ctx = _make_ctx(master_bible=bible)
        ctx.state_tracker.npc_registry = {"장현석": {"status": "dead"}}
        round_ctx = _make_round_ctx(next_ep=10)
        cv_context = _run_and_capture_cv_context(ctx, round_ctx)

        assert cv_context is not None
        vc = cv_context.get("villain_context", {})
        assert vc.get("villain_name") == "장현석Jr"
        assert "숙적" in vc.get("villain_role", "")

    def test_no_villain_no_context(self):
        """빌런 키워드 매칭 NPC가 없으면 villain_context 키 없음."""
        bible = {
            "MasterBible": {
                "AssetLibrary": {
                    "KeyNPCs": [
                        {"name": "서진우", "role": "주인공"},
                        {"name": "박비서", "role": "조력자"},
                    ]
                }
            }
        }
        ctx = _make_ctx(master_bible=bible)
        round_ctx = _make_round_ctx(next_ep=3)
        cv_context = _run_and_capture_cv_context(ctx, round_ctx)

        assert cv_context is not None
        assert "villain_context" not in cv_context


# ═══════════════════════════════════════════════════════════════
# Test 5: authority_context — KeyNPCs 상사 키워드 매칭
# ═══════════════════════════════════════════════════════════════


class TestAuthorityContext:
    def test_authority_context_from_key_npcs(self):
        """KeyNPCs에 상사 키워드 NPC가 있으면 authority_context가 생성된다."""
        bible = {
            "MasterBible": {
                "protagonist_config": {"position": "신입 트레이더"},
                "AssetLibrary": {
                    "KeyNPCs": [
                        {"name": "서진우", "role": "주인공"},
                        {"name": "최회장", "role": "회장, 금융그룹 총수", "position": "대표이사 회장"},
                    ]
                },
            }
        }
        ctx = _make_ctx(master_bible=bible)
        round_ctx = _make_round_ctx(next_ep=3)
        cv_context = _run_and_capture_cv_context(ctx, round_ctx)

        assert cv_context is not None
        ac = cv_context.get("authority_context", {})
        assert ac.get("superior_name") == "최회장"
        assert ac.get("superior_alive") is True
        assert ac.get("protagonist_position") == "신입 트레이더"
        assert ac.get("superior_position") == "대표이사 회장"

    def test_authority_context_deceased_superior_excluded(self):
        """유일한 상사가 사망이면 authority_context 미생성 (검사 스킵)."""
        bible = {
            "MasterBible": {
                "protagonist_config": {"position": "트레이더"},
                "AssetLibrary": {
                    "KeyNPCs": [
                        {"name": "최회장", "role": "회장"},
                    ]
                },
            }
        }
        ctx = _make_ctx(master_bible=bible)
        ctx.state_tracker.npc_registry = {"최회장": {"status": "dead"}}
        round_ctx = _make_round_ctx(next_ep=3)
        cv_context = _run_and_capture_cv_context(ctx, round_ctx)

        assert cv_context is not None
        assert "authority_context" not in cv_context

    def test_authority_context_deceased_skipped_to_next(self):
        """첫 상사가 사망하면 다음 생존 상사로 넘어간다."""
        bible = {
            "MasterBible": {
                "protagonist_config": {"position": "트레이더"},
                "AssetLibrary": {
                    "KeyNPCs": [
                        {"name": "최회장", "role": "회장, 전임 총수"},
                        {"name": "박전무", "role": "상사, 투자본부장", "position": "전무이사"},
                    ]
                },
            }
        }
        ctx = _make_ctx(master_bible=bible)
        ctx.state_tracker.npc_registry = {"최회장": {"status": "dead"}}
        round_ctx = _make_round_ctx(next_ep=10)
        cv_context = _run_and_capture_cv_context(ctx, round_ctx)

        assert cv_context is not None
        ac = cv_context.get("authority_context", {})
        assert ac.get("superior_name") == "박전무"
        assert ac.get("superior_alive") is True
        assert ac.get("superior_position") == "전무이사"

    def test_no_superior_no_context(self):
        """상사 키워드 매칭 NPC가 없으면 authority_context 키 없음."""
        bible = {
            "MasterBible": {
                "AssetLibrary": {
                    "KeyNPCs": [
                        {"name": "서진우", "role": "주인공"},
                        {"name": "이동료", "role": "동료 트레이더"},
                    ]
                }
            }
        }
        ctx = _make_ctx(master_bible=bible)
        round_ctx = _make_round_ctx(next_ep=3)
        cv_context = _run_and_capture_cv_context(ctx, round_ctx)

        assert cv_context is not None
        assert "authority_context" not in cv_context
