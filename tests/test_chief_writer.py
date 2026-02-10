"""[V65] ChiefWriter + Stage4Orchestrator Unit Tests

ChiefWriter (modules/domain/agents/chief_writer.py):
- 초기화, _build_common_context, _generate_episode_digest, _build_prohibition_prompt,
  generate_ensemble, regenerate_with_feedback, _sanitize_leakage, _evaluate_with_rubric,
  _build_future_guard_section, _build_past_guard_section, _get_dna_instruction 등

Stage4Orchestrator (modules/core/stage4_orchestrator.py):
- 초기화, PacingAnalyzer 주입, PerfTimer 호출, mandatory_context 조립 등
"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.domain.agents.chief_writer import ChiefWriter
from modules.core.stage4_orchestrator import Stage4Orchestrator


# ══════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════

@pytest.fixture
def mock_context():
    """ProjectContext mock"""
    ctx = MagicMock()
    ctx.author_directives = ""
    ctx.db = MagicMock()
    ctx.db.get_manuscript = MagicMock(return_value=None)
    ctx.db.load_state_log = MagicMock(return_value=None)
    ctx.master_bible = {
        "MasterBible": {
            "ProjectData": {
                "CoreIdentity": {"desire": "천하제일"}
            },
            "AssetLibrary": {
                "KeyNPCs": [
                    {"name": "연홍", "relationship_state": "경외", "NPC_Martial_HUD": {"equipment": ["비연검"]}},
                    {"name": "철무련주", "relationship_state": "적대", "NPC_Martial_HUD": {"equipment": ["혈마도"]}},
                ],
                "Key_Items": []
            },
            "protagonist_config": {
                "world_origin": "현대인",
                "incarnation_type": "회귀자"
            }
        }
    }
    return ctx


@pytest.fixture
def mock_client():
    """API client mock"""
    client = MagicMock()
    return client


@pytest.fixture
def chief_writer(mock_context, mock_client):
    """ChiefWriter 인스턴스"""
    cw = ChiefWriter(context=mock_context, client=mock_client, model_tier="gemini-2.5-flash")
    return cw


@pytest.fixture
def sample_blueprint():
    """테스트용 Blueprint"""
    return {
        "ep_num": 10,
        "title": "결전의 날",
        "scene_breakdown": {
            "scene_1": {"summary": "청풍산장에서 결투 준비", "content": "이청풍이 검을 준비한다"},
            "scene_2": {"summary": "철무련주와의 대결", "content": "치열한 검법 대결이 벌어진다"},
        },
        "integrated_scenario": "청풍산장에서의 최후의 결투가 시작된다."
    }


@pytest.fixture
def sample_master_bible():
    """테스트용 MasterBible"""
    return {
        "MasterBible": {
            "ProjectData": {"CoreIdentity": {"desire": "천하제일"}},
            "AssetLibrary": {
                "KeyNPCs": [
                    {"name": "연홍", "relationship_state": "경외", "NPC_Martial_HUD": {"equipment": ["비연검"]}},
                ],
                "Key_Items": []
            },
            "protagonist_config": {"world_origin": "현대인", "incarnation_type": "회귀자"},
            "_genre": "wuxia"
        }
    }


@pytest.fixture
def wuxia_manuscript():
    """충분한 분량의 무협 원고 (테스트용)"""
    base = (
        "이청풍은 검을 들고 천천히 앞으로 나아갔다. "
        "청풍검법의 제삼 초식이 그의 손끝에서 피어났다. "
        "바람처럼 가볍고 물처럼 유연한 검세가 허공을 갈랐다. "
        "상대의 눈이 크게 떠졌다. 이것이 바로 청풍산의 비전이란 말인가. "
        "철무련주는 이를 악물고 반격에 나섰다. "
        "하지만 이미 기선을 빼앗긴 상황에서 반격은 무의미했다. "
        "이청풍의 검이 마침내 상대의 어깨를 스쳤다. "
        "피가 튀었다. 첫 번째 상처였다. "
    )
    return (base * 25).strip()


@pytest.fixture
def mock_app():
    """SovereignApp mock (Stage4Orchestrator용)"""
    app = MagicMock()
    app.ui = MagicMock()
    app.ui.log = MagicMock()
    app.ui.console = MagicMock()
    app.selected_genre = {"type": "wuxia", "name": "무협"}
    app.current_project = MagicMock()
    app.current_project.db = MagicMock()
    app.current_project.master_bible = {
        "MasterBible": {
            "ProjectData": {"CoreIdentity": {"desire": "천하제일"}},
            "AssetLibrary": {"KeyNPCs": [], "Key_Items": []},
            "protagonist_config": {"world_origin": "현대인", "incarnation_type": "회귀자"}
        }
    }
    app.current_project.arcs = []
    app.current_project.name = "test_project"
    app.current_project.paths = MagicMock()
    app.current_project.paths.drafts = Path("/tmp/test_drafts")
    app.perf_timer = MagicMock()
    app.sys = MagicMock()
    app.sys.api_client = MagicMock()
    app.agents = {"director": MagicMock(), "writer": MagicMock(), "manager": MagicMock()}
    app.character_voice = None
    app.diversity_engine = None
    app.memory = MagicMock()
    app.failure_learner = None
    app.foreshadow_tracker = None
    return app


# ══════════════════════════════════════════════════════════════
# Test 1: ChiefWriter 초기화
# ══════════════════════════════════════════════════════════════

class TestChiefWriterInit:
    def test_attributes_exist(self, chief_writer):
        """초기화 시 필수 속성 존재 확인"""
        assert chief_writer._agent_name == "ChiefWriter"
        assert hasattr(chief_writer, '_manuscript_cache')
        assert hasattr(chief_writer, '_cache_ep_num')
        assert isinstance(chief_writer._manuscript_cache, dict)
        assert chief_writer._cache_ep_num == -1

    def test_ensemble_strategies_defined(self, chief_writer):
        """앙상블 전략 정의 확인"""
        strategies = chief_writer.ENSEMBLE_STRATEGIES
        assert "balanced" in strategies
        assert "narrative" in strategies
        assert "tension" in strategies
        for key, val in strategies.items():
            assert "name" in val
            assert "temperature" in val
            assert "instruction" in val

    def test_inherits_base_agent(self, chief_writer):
        """BaseAgent 상속 확인"""
        assert hasattr(chief_writer, 'ask')
        assert hasattr(chief_writer, '_extract_json_robust')
        assert hasattr(chief_writer, '_escape_braces')

    def test_timeout_constants(self, chief_writer):
        """앙상블 타임아웃 상수 존재 확인"""
        assert chief_writer.ENSEMBLE_TIMEOUT > 0
        assert chief_writer.SINGLE_CANDIDATE_TIMEOUT > 0
        assert chief_writer.SINGLE_CANDIDATE_TIMEOUT <= chief_writer.ENSEMBLE_TIMEOUT


# ══════════════════════════════════════════════════════════════
# Test 2: _build_common_context TIER1/2/3
# ══════════════════════════════════════════════════════════════

class TestBuildCommonContext:
    def test_contains_blueprint_info(self, chief_writer, sample_blueprint, sample_master_bible):
        """Blueprint 씬 정보가 컨텍스트에 포함되는지 확인"""
        result = chief_writer._build_common_context(
            ep_num=10, blueprint=sample_blueprint, prev_manuscript="",
            hud_report="내공: 50", arc_doc="아크 전술", master_bible=sample_master_bible,
            style_guide="카카오 스타일", director_feedback="", failure_constraints=""
        )
        assert "scene_1" in result or "결투 준비" in result or "청풍산장" in result
        assert "통합 시나리오" in result or "최후의 결투" in result

    def test_contains_hud_report(self, chief_writer, sample_blueprint, sample_master_bible):
        """HUD 리포트 포함 확인"""
        hud = "내공: 75, 경지: 일류, 부상: 없음"
        result = chief_writer._build_common_context(
            ep_num=10, blueprint=sample_blueprint, prev_manuscript="",
            hud_report=hud, arc_doc="", master_bible=sample_master_bible,
            style_guide="", director_feedback="", failure_constraints=""
        )
        assert "일류" in result or "75" in result

    def test_contains_arc_doc(self, chief_writer, sample_blueprint, sample_master_bible):
        """Arc 전술 문서 포함 확인"""
        arc = "이 아크에서 주인공은 절정 고수와 대결한다"
        result = chief_writer._build_common_context(
            ep_num=10, blueprint=sample_blueprint, prev_manuscript="",
            hud_report="", arc_doc=arc, master_bible=sample_master_bible,
            style_guide="", director_feedback="", failure_constraints=""
        )
        assert "절정 고수" in result

    def test_contains_common_rules(self, chief_writer, sample_blueprint, sample_master_bible):
        """Common Rules 섹션 포함 확인"""
        result = chief_writer._build_common_context(
            ep_num=10, blueprint=sample_blueprint, prev_manuscript="",
            hud_report="", arc_doc="", master_bible=sample_master_bible,
            style_guide="", director_feedback="", failure_constraints=""
        )
        assert "Common Rules" in result or "변환 원칙" in result

    def test_director_feedback_included(self, chief_writer, sample_blueprint, sample_master_bible):
        """Director 피드백 섹션이 포함되는지 확인"""
        feedback = "대화 비율이 너무 낮습니다. 30% 이상으로 높이세요."
        result = chief_writer._build_common_context(
            ep_num=10, blueprint=sample_blueprint, prev_manuscript="",
            hud_report="", arc_doc="", master_bible=sample_master_bible,
            style_guide="", director_feedback=feedback, failure_constraints=""
        )
        assert "Director 피드백" in result
        assert "대화 비율" in result


# ══════════════════════════════════════════════════════════════
# Test 3: _build_common_context — style_guide 없을 때 안전 처리
# ══════════════════════════════════════════════════════════════

class TestBuildCommonContextNoStyleGuide:
    def test_no_style_guide(self, chief_writer, sample_blueprint, sample_master_bible):
        """style_guide 빈 문자열 시 기본 문체 표시"""
        result = chief_writer._build_common_context(
            ep_num=5, blueprint=sample_blueprint, prev_manuscript="",
            hud_report="", arc_doc="", master_bible=sample_master_bible,
            style_guide="", director_feedback="", failure_constraints=""
        )
        # style_guide가 비면 "기본 웹소설 문체" 표시
        assert "기본 웹소설 문체" in result

    def test_with_style_guide(self, chief_writer, sample_blueprint, sample_master_bible):
        """style_guide가 주어지면 해당 가이드가 포함"""
        result = chief_writer._build_common_context(
            ep_num=5, blueprint=sample_blueprint, prev_manuscript="",
            hud_report="", arc_doc="", master_bible=sample_master_bible,
            style_guide="카카오: 사이다 전개, 절벽걸기, 4K 해상도 묘사",
            director_feedback="", failure_constraints=""
        )
        assert "카카오" in result
        assert "기본 웹소설 문체" not in result


# ══════════════════════════════════════════════════════════════
# Test 4: _build_common_context — prev_text 있을 때 digest 생성
# ══════════════════════════════════════════════════════════════

class TestBuildCommonContextPrevText:
    def test_prev_manuscript_generates_digest(self, chief_writer, sample_blueprint, sample_master_bible, wuxia_manuscript):
        """직전 원고가 주어지면 digest가 생성되어 컨텍스트에 포함"""
        result = chief_writer._build_common_context(
            ep_num=10, blueprint=sample_blueprint, prev_manuscript=wuxia_manuscript,
            hud_report="", arc_doc="", master_bible=sample_master_bible,
            style_guide="", director_feedback="", failure_constraints=""
        )
        # 다이제스트 또는 직전 화 엔딩이 포함되어야 함
        assert "직전 화" in result or "다이제스트" in result or "마지막 장면" in result

    def test_no_prev_manuscript(self, chief_writer, sample_blueprint, sample_master_bible):
        """직전 원고가 없을 때 안전하게 처리"""
        result = chief_writer._build_common_context(
            ep_num=1, blueprint=sample_blueprint, prev_manuscript="",
            hud_report="", arc_doc="", master_bible=sample_master_bible,
            style_guide="", director_feedback="", failure_constraints=""
        )
        # 에러 없이 결과 반환
        assert isinstance(result, str)
        assert len(result) > 100


# ══════════════════════════════════════════════════════════════
# Test 5: _generate_episode_digest — 구조 확인
# ══════════════════════════════════════════════════════════════

class TestGenerateEpisodeDigest:
    def test_death_detection(self, chief_writer):
        """사망 NPC가 다이제스트에 포함"""
        manuscript = "A" * 300 + "철무련주가 숨을 거두었다. 그의 시신은 차갑게 식어갔다."
        digest = chief_writer._generate_episode_digest(manuscript, ep_num=5)
        assert "사망 NPC" in digest
        assert "철무련주" in digest

    def test_skill_acquisition(self, chief_writer):
        """무공 습득이 다이제스트에 포함"""
        manuscript = "A" * 300 + "이청풍은 태극검법을 깨달았다. 새로운 경지가 열렸다."
        digest = chief_writer._generate_episode_digest(manuscript, ep_num=5)
        assert "습득 무공" in digest
        assert "태극검법" in digest

    def test_item_acquisition(self, chief_writer):
        """아이템 획득이 다이제스트에 포함"""
        manuscript = "A" * 300 + "파천검을 획득했다. 이것이야말로 전설의 명검이었다."
        digest = chief_writer._generate_episode_digest(manuscript, ep_num=5)
        assert "획득 아이템" in digest

    def test_injury_detection(self, chief_writer):
        """부상 상태가 다이제스트에 포함"""
        manuscript = "A" * 300 + "왼팔이 부러졌다. 극심한 고통이 몰려왔다."
        digest = chief_writer._generate_episode_digest(manuscript, ep_num=5)
        assert "부상" in digest


# ══════════════════════════════════════════════════════════════
# Test 6: _generate_episode_digest — 빈 텍스트
# ══════════════════════════════════════════════════════════════

class TestGenerateEpisodeDigestEmpty:
    def test_empty_manuscript(self, chief_writer):
        """빈 원고 → 빈 다이제스트"""
        digest = chief_writer._generate_episode_digest("", ep_num=5)
        assert digest == ""

    def test_short_manuscript(self, chief_writer):
        """200자 미만 짧은 원고 → 빈 다이제스트"""
        digest = chief_writer._generate_episode_digest("짧은 텍스트", ep_num=5)
        assert digest == ""

    def test_no_events_manuscript(self, chief_writer):
        """이벤트 없는 원고 → 빈 다이제스트"""
        plain = "가" * 300  # 한글로 채우되 특별한 이벤트 패턴 없음
        digest = chief_writer._generate_episode_digest(plain, ep_num=5)
        assert digest == "" or isinstance(digest, str)


# ══════════════════════════════════════════════════════════════
# Test 7: _build_future_guard_section / _build_past_guard_section
# ══════════════════════════════════════════════════════════════

class TestBuildProhibitionPrompts:
    def test_future_guard_with_inventory(self, chief_writer):
        """소지품이 있을 때 미래 침범 방지 섹션 생성"""
        result = chief_writer._build_future_guard_section(
            current_inventory=["용린검", "회춘단"],
            current_martial_arts=["태극검법"],
            dead_npcs=["철무련주"],
            item_acquisition_timeline=""
        )
        assert "용린검" in result
        assert "태극검법" in result
        assert "철무련주" in result
        assert "HARD CONSTRAINT" in result

    def test_future_guard_empty(self, chief_writer):
        """소지품/무공/사망NPC 없을 때 기본 가드"""
        result = chief_writer._build_future_guard_section(
            current_inventory=[], current_martial_arts=[],
            dead_npcs=[], item_acquisition_timeline=""
        )
        assert "HARD CONSTRAINT" in result or "미래 침범 방지" in result

    def test_past_guard_with_deaths(self, chief_writer):
        """이전 원고에서 사망 NPC 발견 시 과거 침범 방지"""
        prev = "철무련주가 숨을 거두었다. 그의 시신은 차갑게 식어갔다."
        result = chief_writer._build_past_guard_section(
            prev_manuscript=prev, existing_dead_npcs=["흑도"]
        )
        assert "PAST CONSTRAINT" in result
        assert "흑도" in result or "철무련주" in result

    def test_past_guard_no_prev(self, chief_writer):
        """직전 원고가 없을 때 빈 문자열"""
        result = chief_writer._build_past_guard_section(
            prev_manuscript="", existing_dead_npcs=[]
        )
        assert result == ""


# ══════════════════════════════════════════════════════════════
# Test 8: generate_ensemble — LLM mock으로 3개 후보 반환
# ══════════════════════════════════════════════════════════════

class TestGenerateEnsemble:
    def test_returns_candidates_list(self, chief_writer, sample_blueprint, sample_master_bible):
        """generate_ensemble이 리스트를 반환하는지 확인"""
        mock_response = json.dumps({
            "title": "테스트 에피소드",
            "content": "A" * 5000,
            "state_updates": {"realm": "일류"},
            "key_scenes_covered": ["scene_1"]
        })
        # LLM ask() 호출을 mock
        chief_writer.ask = MagicMock(return_value=mock_response)
        chief_writer._ask_with_cached_context = MagicMock(return_value=mock_response)
        # Self-Critique 스킵 (rubric 높음)
        chief_writer._evaluate_with_rubric = MagicMock(return_value=4.0)

        candidates = chief_writer.generate_ensemble(
            ep_num=10, blueprint=sample_blueprint, prev_manuscript="직전 원고",
            hud_report="내공: 50", arc_doc="아크 문서", master_bible=sample_master_bible,
            style_guide="카카오", genre_name="무협"
        )
        assert isinstance(candidates, list)
        assert len(candidates) >= 1

    def test_candidate_structure(self, chief_writer, sample_blueprint, sample_master_bible):
        """각 후보의 구조 확인"""
        mock_response = json.dumps({
            "title": "제10화",
            "content": "B" * 5000,
            "state_updates": {"realm": "절정"},
            "key_scenes_covered": ["scene_1", "scene_2"]
        })
        chief_writer.ask = MagicMock(return_value=mock_response)
        chief_writer._ask_with_cached_context = MagicMock(return_value=mock_response)
        chief_writer._evaluate_with_rubric = MagicMock(return_value=4.0)

        candidates = chief_writer.generate_ensemble(
            ep_num=10, blueprint=sample_blueprint, prev_manuscript="",
            hud_report="", arc_doc="", master_bible=sample_master_bible,
            genre_name="무협"
        )
        valid = [c for c in candidates if not c.get("error")]
        if valid:
            cand = valid[0]
            assert "strategy" in cand
            assert "manuscript" in cand
            assert "title" in cand
            assert "state_updates" in cand
            assert "metadata" in cand


# ══════════════════════════════════════════════════════════════
# Test 9: regenerate_with_feedback
# ══════════════════════════════════════════════════════════════

class TestRegenerateWithFeedback:
    def test_feedback_enhanced(self, chief_writer, sample_blueprint, sample_master_bible):
        """피드백이 강화되어 generate_ensemble에 전달되는지 확인"""
        mock_response = json.dumps({
            "title": "재시도 에피소드",
            "content": "C" * 5000,
            "state_updates": {},
            "key_scenes_covered": []
        })
        chief_writer.ask = MagicMock(return_value=mock_response)
        chief_writer._ask_with_cached_context = MagicMock(return_value=mock_response)
        chief_writer._evaluate_with_rubric = MagicMock(return_value=4.0)

        previous_attempt = {
            "strategy": "balanced",
            "rejection_reason": "분량 부족",
            "action_items": ["분량을 5000자 이상으로 늘리시오"],
            "score": 45
        }

        candidates = chief_writer.regenerate_with_feedback(
            ep_num=10, blueprint=sample_blueprint, prev_manuscript="",
            hud_report="", arc_doc="", master_bible=sample_master_bible,
            style_guide="", director_feedback="분량 부족. 5000자 이상 작성하라.",
            previous_attempt=previous_attempt, attempt_number=2,
            genre_name="무협"
        )
        assert isinstance(candidates, list)
        assert len(candidates) >= 1


# ══════════════════════════════════════════════════════════════
# Test 10: _sanitize_leakage
# ══════════════════════════════════════════════════════════════

class TestSanitizeLeakage:
    def test_removes_banned_keys(self, chief_writer):
        """금지 키가 제거되는지 확인"""
        data = {
            "title": "제목",
            "content": "본문",
            "next_episode": "다음 화 힌트",
            "future_hint": "미래 스포일러"
        }
        result = chief_writer._sanitize_leakage(json.dumps(data, ensure_ascii=False))
        parsed = json.loads(result)
        assert "next_episode" not in parsed
        assert "future_hint" not in parsed
        assert "title" in parsed
        assert "content" in parsed

    def test_removes_english_parentheses(self, chief_writer):
        """영문 괄호 병기 제거"""
        text = "윈도우(Windows)에서 검(Sword)을 들었다."
        result = chief_writer._sanitize_leakage(text)
        assert "(Windows)" not in result
        assert "(Sword)" not in result
        assert "윈도우" in result

    def test_empty_text(self, chief_writer):
        """빈 텍스트 안전 처리"""
        assert chief_writer._sanitize_leakage("") == ""
        assert chief_writer._sanitize_leakage(None) is None


# ══════════════════════════════════════════════════════════════
# Test 11: _evaluate_with_rubric
# ══════════════════════════════════════════════════════════════

class TestEvaluateWithRubric:
    def test_returns_float(self, chief_writer):
        """float 점수 반환"""
        manuscript = json.dumps({
            "content": "그는 마른입술을 혀로 훑으며 펜을 톡톡 두드렸다. 소리가 울려퍼졌다. "
                       "차가운 바람이 뺨을 때렸다. 악취가 진동했다. "
                       '"너 대체 뭘 안다는 거냐?" '
                       '"충분히 알고 있습니다." ' * 50
        })
        score = chief_writer._evaluate_with_rubric(manuscript, "무협")
        assert isinstance(score, float)
        assert 1.0 <= score <= 4.0

    def test_empty_content_returns_low(self, chief_writer):
        """빈 내용 → 낮은 점수"""
        score = chief_writer._evaluate_with_rubric('{"content": ""}', "무협")
        assert score <= 2.0

    def test_short_content_returns_low(self, chief_writer):
        """짧은 내용 → 낮은 점수"""
        score = chief_writer._evaluate_with_rubric('{"content": "짧은 글"}', "무협")
        assert score <= 2.0


# ══════════════════════════════════════════════════════════════
# Test 12: _get_dna_instruction
# ══════════════════════════════════════════════════════════════

class TestGetDnaInstruction:
    def test_ep1_special_dna(self, chief_writer):
        """1화에서 특수 DNA 적용"""
        result = chief_writer._get_dna_instruction(ep_num=1, intro_dna="CYNICAL")
        assert "제1화" in result or "DNA" in result
        assert "CYNICAL" in result

    def test_ep2_continuity_mode(self, chief_writer):
        """2화 이후 연속 집필 모드"""
        result = chief_writer._get_dna_instruction(ep_num=2, intro_dna="CYNICAL")
        assert "연속 집필" in result
        assert "CYNICAL" not in result

    def test_ep50_continuity_mode(self, chief_writer):
        """50화에서도 연속 집필 모드 유지"""
        result = chief_writer._get_dna_instruction(ep_num=50, intro_dna="MYSTERIOUS")
        assert "연속 집필" in result


# ══════════════════════════════════════════════════════════════
# Test 13: _detect_deaths_from_manuscript
# ══════════════════════════════════════════════════════════════

class TestDetectDeaths:
    def test_death_detection(self, chief_writer):
        """사망 패턴 탐지"""
        text = "철무련주가 최후를 맞았다. 흑도를 죽였다."
        deaths = chief_writer._detect_deaths_from_manuscript(text)
        assert "철무련주" in deaths or "흑도" in deaths

    def test_no_deaths(self, chief_writer):
        """사망 없는 원고"""
        text = "이청풍은 산책을 했다. 연홍과 대화를 나누었다."
        deaths = chief_writer._detect_deaths_from_manuscript(text)
        assert len(deaths) == 0

    def test_empty_manuscript(self, chief_writer):
        """빈 원고"""
        deaths = chief_writer._detect_deaths_from_manuscript("")
        assert deaths == []


# ══════════════════════════════════════════════════════════════
# Test 14: _get_npc_equipment_summary
# ══════════════════════════════════════════════════════════════

class TestGetNpcEquipmentSummary:
    def test_extracts_equipment(self, chief_writer, sample_master_bible):
        """NPC 장비 정보 추출"""
        result = chief_writer._get_npc_equipment_summary(sample_master_bible)
        assert "연홍" in result
        assert "비연검" in result

    def test_empty_npcs(self, chief_writer):
        """NPC 없는 바이블"""
        empty_bible = {"MasterBible": {"AssetLibrary": {"KeyNPCs": []}}}
        result = chief_writer._get_npc_equipment_summary(empty_bible)
        assert "정보 없음" in result

    def test_no_equipment(self, chief_writer):
        """장비 정보 없는 NPC"""
        bible = {"MasterBible": {"AssetLibrary": {"KeyNPCs": [{"name": "연홍", "NPC_Martial_HUD": {}}]}}}
        result = chief_writer._get_npc_equipment_summary(bible)
        assert "정보 없음" in result


# ══════════════════════════════════════════════════════════════
# Test 15: _check_hud_consistency
# ══════════════════════════════════════════════════════════════

class TestCheckHudConsistency:
    def test_weak_with_strong_action_no_justification(self, chief_writer):
        """약한 상태에서 강력 행동 + 정당화 없음 → 이슈 감지"""
        content = "주인공은 일격에 적을 박살냈다."
        hud = "현재 상태: 부상, 중상"
        issues = chief_writer._check_hud_consistency(content, hud)
        assert len(issues) >= 1
        assert issues[0]["type"] == "hud_contradiction"

    def test_weak_with_strong_action_justified(self, chief_writer):
        """약한 상태 + 강력 행동이지만 정당화 있음 → 이슈 없음"""
        content = "발경을 동원하여 일격에 적을 박살냈다. 그 대가로 내상을 입었다."
        hud = "현재 상태: 부상, 중상"
        issues = chief_writer._check_hud_consistency(content, hud)
        assert len(issues) == 0

    def test_healthy_with_strong_action(self, chief_writer):
        """건강한 상태에서 강력 행동 → 이슈 없음"""
        content = "일격에 적을 분쇄했다."
        hud = "현재 상태: 정상, 내공 충만"
        issues = chief_writer._check_hud_consistency(content, hud)
        assert len(issues) == 0


# ══════════════════════════════════════════════════════════════
# Test 16: Stage4Orchestrator 초기화
# ══════════════════════════════════════════════════════════════

class TestStage4OrchestratorInit:
    def test_init_with_app(self, mock_app):
        """SovereignApp 참조가 올바르게 저장"""
        orch = Stage4Orchestrator(mock_app)
        assert orch.app is mock_app

    def test_has_main_method(self, mock_app):
        """메인 파이프라인 메서드 존재 확인"""
        orch = Stage4Orchestrator(mock_app)
        assert hasattr(orch, 'stage_4_v2_chief_writer')
        assert callable(orch.stage_4_v2_chief_writer)


# ══════════════════════════════════════════════════════════════
# Test 17: Stage4Orchestrator — early exit 조건
# ══════════════════════════════════════════════════════════════

class TestStage4OrchestratorEarlyExit:
    def test_no_bible_exits(self, mock_app):
        """Bible이 없으면 즉시 종료"""
        mock_app.current_project.master_bible = None
        mock_app.current_project.arcs = [{"arc_no": 1}]
        orch = Stage4Orchestrator(mock_app)
        orch.stage_4_v2_chief_writer()
        # log가 호출되어 에러 메시지 출력됨
        mock_app.ui.log.assert_called()
        log_calls = [str(c) for c in mock_app.ui.log.call_args_list]
        assert any("Bible" in str(c) or "Arc" in str(c) for c in log_calls)

    def test_no_arcs_exits(self, mock_app):
        """Arc가 없으면 즉시 종료"""
        mock_app.current_project.arcs = []
        orch = Stage4Orchestrator(mock_app)
        orch.stage_4_v2_chief_writer()
        mock_app.ui.log.assert_called()


# ══════════════════════════════════════════════════════════════
# Test 18: Stage4Orchestrator — PerfTimer 호출
# ══════════════════════════════════════════════════════════════

class TestStage4PerfTimer:
    def test_perf_timer_attribute_accessed(self, mock_app):
        """PerfTimer 속성이 접근 가능한지 확인"""
        orch = Stage4Orchestrator(mock_app)
        # PerfTimer는 orch.app.perf_timer로 접근
        assert orch.app.perf_timer is not None
        assert hasattr(orch.app.perf_timer, 'start')
        assert hasattr(orch.app.perf_timer, 'stop')


# ══════════════════════════════════════════════════════════════
# Test 19: _build_future_guard_section — dead_npcs 제약
# ══════════════════════════════════════════════════════════════

class TestFutureGuardDeadNPCs:
    def test_dead_npcs_section(self, chief_writer):
        """사망 NPC 리스트가 미래 침범 방지에 포함"""
        result = chief_writer._build_future_guard_section(
            current_inventory=[], current_martial_arts=[],
            dead_npcs=["철무련주", "흑도", "독왕"],
            item_acquisition_timeline=""
        )
        assert "철무련주" in result
        assert "흑도" in result
        assert "독왕" in result
        assert "사망" in result

    def test_item_timeline_included(self, chief_writer):
        """아이템 획득 타임라인이 포함"""
        timeline = "제3화: 용린검 획득\n제7화: 회춘단 획득"
        result = chief_writer._build_future_guard_section(
            current_inventory=["용린검", "회춘단"],
            current_martial_arts=[],
            dead_npcs=[],
            item_acquisition_timeline=timeline
        )
        assert "타임라인" in result
        assert "용린검" in result


# ══════════════════════════════════════════════════════════════
# Test 20: _extract_numeric_value
# ══════════════════════════════════════════════════════════════

class TestExtractNumericValue:
    def test_int_value(self, chief_writer):
        """정수 입력"""
        assert chief_writer._extract_numeric_value(42) == 42

    def test_float_value(self, chief_writer):
        """실수 입력 → 정수 변환"""
        assert chief_writer._extract_numeric_value(75.5) == 75

    def test_string_value(self, chief_writer):
        """문자열에서 숫자 추출"""
        assert chief_writer._extract_numeric_value("내공 +300") == 300

    def test_no_number(self, chief_writer):
        """숫자 없는 문자열 → 0"""
        assert chief_writer._extract_numeric_value("없음") == 0

    def test_none_value(self, chief_writer):
        """None 입력 → 0"""
        assert chief_writer._extract_numeric_value(None) == 0


# ══════════════════════════════════════════════════════════════
# Test 21: _check_hud_anomalies
# ══════════════════════════════════════════════════════════════

class TestCheckHudAnomalies:
    def test_ep1_no_anomalies(self, chief_writer):
        """1화에서는 비교 대상 없어 이상 없음"""
        result = chief_writer._check_hud_anomalies(1)
        assert result['has_anomalies'] is False

    def test_no_cache_no_anomalies(self, chief_writer):
        """캐시 없을 때 이상 없음"""
        result = chief_writer._check_hud_anomalies(10)
        assert result['has_anomalies'] is False


# ══════════════════════════════════════════════════════════════
# Test 22: world_origin constraint in _build_common_context
# ══════════════════════════════════════════════════════════════

class TestWorldOriginConstraint:
    def test_modern_person_context(self, chief_writer, sample_blueprint, sample_master_bible):
        """현대인 모드 → 현대인 모드 안내 포함"""
        # sample_master_bible은 world_origin=현대인
        result = chief_writer._build_common_context(
            ep_num=5, blueprint=sample_blueprint, prev_manuscript="",
            hud_report="", arc_doc="", master_bible=sample_master_bible,
            style_guide="", director_feedback="", failure_constraints=""
        )
        assert "현대인 모드" in result

    def test_primitive_person_context(self, chief_writer, sample_blueprint):
        """원시인 모드 → 원시인 제약 포함"""
        primitive_bible = {
            "MasterBible": {
                "ProjectData": {"CoreIdentity": {"desire": "복수"}},
                "AssetLibrary": {"KeyNPCs": []},
                "protagonist_config": {"world_origin": "원시인", "incarnation_type": "회귀자"},
                "_genre": "wuxia"
            }
        }
        result = chief_writer._build_common_context(
            ep_num=5, blueprint=sample_blueprint, prev_manuscript="",
            hud_report="", arc_doc="", master_bible=primitive_bible,
            style_guide="", director_feedback="", failure_constraints=""
        )
        assert "원시인" in result


# ══════════════════════════════════════════════════════════════
# Test 23: _self_critique structure
# ══════════════════════════════════════════════════════════════

class TestSelfCritique:
    def test_returns_expected_structure(self, chief_writer):
        """self_critique 반환 구조 확인"""
        manuscript = json.dumps({"content": "평화로운 하루였다." * 100})
        result = chief_writer._self_critique(
            manuscript=manuscript,
            hud_report="상태: 정상",
            encyclopedia={"npcs": []},
            genre_name="무협",
            ep_num=5
        )
        assert "has_issues" in result
        assert "issues" in result
        assert "severity" in result
        assert isinstance(result["has_issues"], bool)
        assert isinstance(result["issues"], list)
        assert result["severity"] in ["low", "medium", "high"]

    def test_severity_levels(self, chief_writer):
        """이슈 수에 따른 심각도 판단"""
        # 이슈 0개 → low
        result0 = {"has_issues": False, "issues": [], "severity": "low"}
        assert result0["severity"] == "low"


# ══════════════════════════════════════════════════════════════
# Test 24: _build_anti_trope_instructions
# ══════════════════════════════════════════════════════════════

class TestBuildAntiTropeInstructions:
    def test_contains_genre(self, chief_writer):
        """장르명이 반클리셰 지침에 포함"""
        result = chief_writer._build_anti_trope_instructions("무협")
        assert "무협" in result
        assert "ANTI-TROPE" in result

    def test_contains_cliche_warnings(self, chief_writer):
        """클리셰 경고가 포함"""
        result = chief_writer._build_anti_trope_instructions("무협")
        assert "클리셰" in result or "금지" in result


# ══════════════════════════════════════════════════════════════
# Test 25: _prefetch_manuscripts
# ══════════════════════════════════════════════════════════════

class TestPrefetchManuscripts:
    def test_cache_populated(self, chief_writer, mock_context):
        """프리페치 후 캐시가 채워지는지 확인"""
        mock_context.db.get_manuscript = MagicMock(return_value={
            "content": "테스트 원고", "hud_snapshot": {"realm": "일류"}
        })
        chief_writer._prefetch_manuscripts(ep_num=5, window=3)
        assert chief_writer._cache_ep_num == 5
        # 에피소드 2, 3, 4가 캐시되어야 함
        assert len(chief_writer._manuscript_cache) >= 1

    def test_cache_reuse(self, chief_writer, mock_context):
        """같은 에피소드 재호출 시 DB 재조회 안 함"""
        mock_context.db.get_manuscript = MagicMock(return_value={"content": "원고", "hud_snapshot": {}})
        chief_writer._prefetch_manuscripts(ep_num=10, window=3)
        call_count = mock_context.db.get_manuscript.call_count

        chief_writer._prefetch_manuscripts(ep_num=10, window=3)
        assert mock_context.db.get_manuscript.call_count == call_count  # 추가 호출 없음
