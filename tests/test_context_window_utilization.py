import json
from types import SimpleNamespace

from modules.core.info_paradox_checker import InfoParadoxChecker
from modules.core.long_term_repetition_advisor import LongTermRepetitionAdvisor
from modules.core.npc_drift_advisor import NpcDriftAdvisor
from modules.core.relationship_drift_advisor import RelationshipDriftAdvisor
from modules.core.agent_intelligence import AgentIntelligence, AgentType
from modules.core.stage0.reverse_expander import ReverseExpander
from modules.core.stage0.story_expander import StoryExpander
from modules.core.tree_of_thoughts import TreeOfThoughts
from modules.core.truth_gate import TruthGate
from modules.domain.agents.arc_corrector import ArcCorrector
from modules.domain.agents.critic import Critic
from modules.domain.agents.director_ensemble import DirectorEnsembleSelector


class _DirectorStub:
    def __init__(self):
        self.prompt = ""

    def ask(self, prompt, **_kwargs):
        self.prompt = prompt
        return "{}"

    @staticmethod
    def _extract_json_robust(_response):
        return {
            "selected_index": 0,
            "decision": "PASS",
            "score": 90,
            "contradictions": [],
            "reason": "ok",
            "comparison_notes": "",
            "feedback": "",
            "fix_scope": "inplace",
        }

    @staticmethod
    def _escape_braces(text):
        return text


class _WorldStateStub:
    @staticmethod
    def get_world_laws():
        return ["힘의 대가는 반드시 지불된다"]


def test_director_arc_prompt_preserves_tail_markers():
    director = _DirectorStub()
    selector = DirectorEnsembleSelector(director)
    prev_arc_context = ("앞부분 " * 4000) + "PREV_TAIL_MARKER"
    constraint_block = ("제약 " * 2500) + "CONSTRAINT_TAIL_MARKER"
    advisory = ("경고 " * 2500) + "ADVISORY_TAIL_MARKER"
    arcs = [
        {
            "_strategy": "balanced",
            "ep_count": 5,
            "tactical_doc": "전개" * 800,
            "state_constraints": {"payload": "S" * 6000, "tail": "SC_TAIL_MARKER"},
            "joint_docs": {"payload": "J" * 6000, "tail": "JOINT_TAIL_MARKER"},
        }
    ]

    selector.compare_and_select_arc(
        candidates=arcs,
        arc_no=3,
        curr_block={"payload": "B" * 14000, "tail": "BLOCK_TAIL_MARKER"},
        prev_arc_context=prev_arc_context,
        constraint_block=constraint_block,
        advisory=advisory,
    )

    assert "PREV_TAIL_MARKER" in director.prompt
    assert "CONSTRAINT_TAIL_MARKER" in director.prompt
    assert "ADVISORY_TAIL_MARKER" in director.prompt
    assert "BLOCK_TAIL_MARKER" in director.prompt
    assert "SC_TAIL_MARKER" in director.prompt
    assert "JOINT_TAIL_MARKER" in director.prompt


def test_story_expander_detail_prompt_uses_story_brief():
    captured = {}
    expander = StoryExpander(genre="investment")
    expander.concept = ("초반 설정 " * 500) + "CONCEPT_TAIL_MARKER"
    expander.extracted = {
        "themes": ["심리전", "시장 지배"],
        "tone": "건조한 긴장감",
        "world_laws": ["법칙A", "법칙B"],
    }

    def _fake_call(prompt, **_kwargs):
        captured["prompt"] = prompt
        return "[]"

    expander._call_llm = _fake_call
    expander._generate_details([{"block_id": "Block 1", "title": "시작"}])

    assert "CONCEPT_TAIL_MARKER" in captured["prompt"]
    assert "심리전" in captured["prompt"]
    assert "건조한 긴장감" in captured["prompt"]
    assert "법칙A" in captured["prompt"]


def test_story_expander_default_concept_budget_is_more_generous_than_legacy_cap():
    expander = StoryExpander(genre="investment")
    expander.concept = "HEAD-CONCEPT\n" + ("A" * 6000) + "\nMID-CONCEPT\n" + ("B" * 6000) + "\nTAIL-CONCEPT"

    text = expander._get_concept_prompt_text()

    assert len(text) <= expander._CONCEPT_PROMPT_MAX
    assert len(text) > 4000
    assert "TAIL-CONCEPT" in text


def test_reverse_expander_detect_genre_uses_tail_and_more_drafts():
    captured = {}
    expander = ReverseExpander()
    expander.raw_drafts = [
        {"ep_num": idx, "title": f"ep{idx}", "content": ("앞부분 " * 800) + (f"TAIL_{idx}" if idx == 5 else "")}
        for idx in range(1, 6)
    ]

    def _fake_call(prompt, **_kwargs):
        captured["prompt"] = prompt
        return json.dumps({"genre": "investment"})

    expander._call_llm = _fake_call

    result = expander.detect_genre()

    assert result == "investment"
    assert "TAIL_5" in captured["prompt"]


def test_truth_gate_prompt_includes_tail_snippet():
    captured = {}
    manuscript = ("서두 " * 1200) + "TRUTH_TAIL_MARKER"

    def _ask(prompt):
        captured["prompt"] = prompt
        return '{"violation": false, "reason": ""}'

    gate = TruthGate(world_state=_WorldStateStub(), llm_ask=_ask)

    gate._check_world_law_violation(manuscript, [], [])

    assert "TRUTH_TAIL_MARKER" in captured["prompt"]


def test_npc_drift_prompt_includes_tail_snippet():
    captured = {}
    manuscript = ("홍길동이 등장했다. " * 500) + "NPC_TAIL_MARKER"

    def _ask(prompt):
        captured["prompt"] = prompt
        return "[]"

    advisor = NpcDriftAdvisor(llm_ask=_ask)

    advisor.check(
        manuscript,
        {"홍길동": {"role_at_intro": "상인", "first_seen_ep": 1, "known_attrs": {"job": {"value": "상인"}}}},
        ep_num=10,
    )

    assert "NPC_TAIL_MARKER" in captured["prompt"]


def test_info_paradox_prompt_includes_tail_snippet():
    captured = {}
    manuscript = ("진우는 생각했다. " * 500) + "INFO_TAIL_MARKER"

    def _ask(prompt):
        captured["prompt"] = prompt
        return "[]"

    checker = InfoParadoxChecker(llm_ask=_ask)

    checker.check(manuscript, ep_num=5, pov_character="진우", knowledge_summary="알고 있는 정보")

    assert "INFO_TAIL_MARKER" in captured["prompt"]


def test_relationship_drift_prompt_includes_tail_snippet():
    captured = {}
    manuscript = ("알파와 베타가 대화했다. " * 500) + "REL_TAIL_MARKER"

    def _ask(prompt):
        captured["prompt"] = prompt
        return "[]"

    advisor = RelationshipDriftAdvisor(llm_ask=_ask)

    advisor.check(manuscript, ep_num=9, relationship_timeline="[알파 ↔ 베타]\n1화: 동맹")

    assert "REL_TAIL_MARKER" in captured["prompt"]


def test_long_term_repetition_prompt_includes_tail_snippet():
    captured = {}
    manuscript = ("전투가 벌어졌다. " * 400) + "LONG_TAIL_MARKER"

    def _ask(prompt):
        captured["prompt"] = prompt
        return "[]"

    advisor = LongTermRepetitionAdvisor(llm_ask=_ask)

    advisor.check(manuscript, ep_num=25, pattern_summary="[P1-5] 반복 패턴")

    assert "LONG_TAIL_MARKER" in captured["prompt"]


def test_agent_intelligence_self_critique_prompt_preserves_tail_snippet():
    intel = AgentIntelligence(genre="wuxia")

    prompt = intel.generate_critique_request(
        "HEAD-INTEL\n" + ("I" * 5000) + "\nTAIL-INTEL-MARKER",
        AgentType.WRITER,
    )

    assert "TAIL-INTEL-MARKER" in prompt
    assert "...(중간 생략)..." in prompt


def test_critic_llm_prompt_preserves_tail_snippet():
    critic = Critic.__new__(Critic)
    captured = {}

    def _fake_ask(prompt, temperature=0.3):
        captured["prompt"] = prompt
        return "{}"

    critic.ask = _fake_ask
    critic._extract_json_robust = lambda _response: {}

    critic.get_llm_critique(
        manuscript="HEAD-CRITIC\n" + ("M" * 90000) + "\nTAIL-CRITIC-MARKER",
        hud_report="정상",
        genre="무협",
    )

    assert "TAIL-CRITIC-MARKER" in captured["prompt"]
    assert "...(중간 생략)..." in captured["prompt"]


def test_critic_deep_review_prompt_preserves_tail_snippets():
    critic = Critic.__new__(Critic)
    critic._escape_braces = lambda text: str(text).replace("{", "{{").replace("}", "}}")
    captured = {}

    def _fake_ask(prompt, temperature=0.2):
        captured["prompt"] = prompt
        return '{"overall_score": 8, "scores": {}, "strengths": [], "weaknesses": [], "revision_priority": [], "specific_feedback": ""}'

    critic.ask = _fake_ask
    critic._extract_json_robust = json.loads

    result = critic.deep_review(
        manuscript="HEAD-REVIEW\n" + ("R" * 120000) + "\nTAIL-REVIEW-MS",
        blueprint={"payload": "B" * 120000, "tail": "TAIL-REVIEW-BP"},
        ep_num=3,
        genre="무협",
        prev_ending="HEAD-END\n" + ("E" * 2000) + "\nTAIL-REVIEW-END",
    )

    assert result["recommendation"] == "PASS"
    assert "TAIL-REVIEW-MS" in captured["prompt"]
    assert "TAIL-REVIEW-BP" in captured["prompt"]
    assert "TAIL-REVIEW-END" in captured["prompt"]
    assert "...(중간 생략)..." in captured["prompt"]


def test_arc_corrector_length_prompt_preserves_tail_context():
    corrector = ArcCorrector.__new__(ArcCorrector)
    corrector._escape_braces = lambda text: str(text).replace("{", "{{").replace("}", "}}")
    captured = {}

    def _fake_ask(prompt, temperature=0.3):
        captured["prompt"] = prompt
        return '{"corrected_content": "보강된 제1화", "change_summary": "ok"}'

    corrector.ask = _fake_ask
    corrector._extract_json_robust = json.loads
    corrector._replace_episode_section = lambda tactical, ep_num, new_content: tactical + "\n" + new_content

    arc, result = corrector._correct_length_issue(
        arc={
            "tactical_doc": "[제 1화]\n" + ("전술 " * 2000) + "TAIL-ARC-CORRECTOR",
            "episode_details": [{"ep_num": 1}],
        },
        issue={"message": "제 1화 분량 부족"},
        prev_arcs=[{"joint_docs": {"final_location": "시장", "physical_inventory": ["검"]}}],
    )

    assert result["success"] is True
    assert "TAIL-ARC-CORRECTOR" in captured["prompt"]
    assert "...(중간 생략)..." in captured["prompt"]
    assert arc["episode_details"] == []


def test_arc_corrector_missing_episode_prompt_preserves_tail_context():
    corrector = ArcCorrector.__new__(ArcCorrector)
    corrector._escape_braces = lambda text: str(text).replace("{", "{{").replace("}", "}}")
    captured = {}

    def _fake_ask(prompt, temperature=0.4):
        captured["prompt"] = prompt
        return '{"corrected_content": "새 제2화", "change_summary": "ok"}'

    corrector.ask = _fake_ask
    corrector._extract_json_robust = json.loads
    corrector._insert_episode_section = lambda tactical, ep_num, new_content: tactical + "\n" + new_content

    arc, result = corrector._correct_missing_episode(
        arc={
            "tactical_doc": "[제 1화]\n시작\n" + ("A" * 5000) + "\nTAIL-MISSING-ARC",
            "episode_details": [{"ep_num": 1}, {"ep_num": 2}],
        },
        issue={"message": "[2] 화 누락"},
        prev_arcs=[{"joint_docs": {"final_location": "산문", "physical_inventory": ["패"]}}],
    )

    assert result["success"] is True
    assert "TAIL-MISSING-ARC" in captured["prompt"]
    assert "...(중간 생략)..." in captured["prompt"]
    assert arc["episode_details"] == [{"ep_num": 1}]


def test_tree_of_thoughts_generate_approaches_preserves_tail_context(monkeypatch):
    tot = TreeOfThoughts(api_client=object())
    captured = {}

    def _fake_call(prompt, temperature=0.8):
        captured["prompt"] = prompt
        return '{"approaches": [{"id": 1, "name": "보수적 접근", "description": "안전", "focus": "안정성"}]}'

    monkeypatch.setattr(tot, "_call_llm", _fake_call)

    approaches = tot._generate_approaches(
        task="이번 화 설계",
        context={"payload": "C" * 5000, "tail": "TOT_CTX_TAIL"},
        n_branches=1,
    )

    assert len(approaches) == 1
    assert "TOT_CTX_TAIL" in captured["prompt"]
    assert "...(중간 생략)..." in captured["prompt"]


def test_tree_of_thoughts_evaluate_path_preserves_tail_output(monkeypatch):
    tot = TreeOfThoughts(api_client=object())
    captured = {}

    def _fake_call(prompt, temperature=0.2):
        captured["prompt"] = prompt
        return '{"total": 88, "strengths": [], "weaknesses": []}'

    monkeypatch.setattr(tot, "_call_llm", _fake_call)

    result = tot._evaluate_path("블루프린트 평가", "HEAD-TOT\n" + ("O" * 6000) + "\nTOT_OUTPUT_TAIL")

    assert result["total"] == 88
    assert "TOT_OUTPUT_TAIL" in captured["prompt"]
    assert "...(중간 생략)..." in captured["prompt"]


def test_tree_of_thoughts_arc_prompt_preserves_tail_context(monkeypatch):
    captured = {}

    def _fake_router(**kwargs):
        captured["prompt"] = kwargs["contents"]
        return SimpleNamespace(
            text=json.dumps(
                {
                    "arc_no": 4,
                    "tactical_doc": "전술",
                    "joint_docs": {"final_location": "산문", "physical_inventory": [], "world_joint": "변화"},
                    "state_constraints": {"items_acquired": [], "items_consumed": [], "grants_received": []},
                    "hybrid_composition": {"primary": "A", "secondary": "B"},
                },
                ensure_ascii=False,
            )
        )

    monkeypatch.setattr("modules.core.tree_of_thoughts.generate_content_via_router", _fake_router)

    tot = TreeOfThoughts(api_client=object())
    arc = tot._generate_arc_with_approach(
        arc_no=4,
        vol_strategy="HEAD-VOL\n" + ("V" * 5000) + "\nTOT_VOL_TAIL",
        curr_block={"dna": "BLOCK"},
        prev_arc_context="HEAD-PREV\n" + ("P" * 7000) + "\nTOT_PREV_TAIL",
        assets={},
        feedback="HEAD-FEEDBACK\n" + ("F" * 3000) + "\nTOT_FEEDBACK_TAIL",
        approach={"name": "긴장감 중심", "description": "긴장", "focus": "몰입도", "prompt_hint": "곡선 유지"},
        protagonist_name="주인공",
    )

    assert arc["arc_no"] == 4
    assert "TOT_VOL_TAIL" in captured["prompt"]
    assert "TOT_PREV_TAIL" in captured["prompt"]
    assert "TOT_FEEDBACK_TAIL" in captured["prompt"]
    assert "...(중간 생략)..." in captured["prompt"]
