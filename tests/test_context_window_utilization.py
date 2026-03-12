import json

from modules.core.info_paradox_checker import InfoParadoxChecker
from modules.core.long_term_repetition_advisor import LongTermRepetitionAdvisor
from modules.core.npc_drift_advisor import NpcDriftAdvisor
from modules.core.relationship_drift_advisor import RelationshipDriftAdvisor
from modules.core.stage0.reverse_expander import ReverseExpander
from modules.core.stage0.story_expander import StoryExpander
from modules.core.truth_gate import TruthGate
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
