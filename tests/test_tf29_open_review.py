"""[TF-29] open_review 전파 테스트 — Director 자유 리뷰가 CW에 전달되는 경로 검증."""

from modules.core.constants import GenreTypes
from modules.domain.agents.blueprint_ensemble import build_genre_strategy_contract
from modules.domain.agents.director_ensemble import DirectorEnsembleSelector

# ===========================================================================
# Helpers
# ===========================================================================


class _FakeDirector:
    """DirectorEnsembleSelector가 참조하는 최소 Director stub."""

    _last_thinking = ""
    MAX_CONTEXT_CHARS = 700_000

    def ask(self, prompt, temperature=0.1, thinking_level=None):
        self.last_prompt = prompt
        return self._response

    def _extract_json_robust(self, response):
        import json

        try:
            return json.loads(response)
        except Exception:
            return None

    def _escape_braces(self, text):
        return str(text) if text else ""

    def apply_adaptive_decision(self, score, original_decision, arc_pos, total_eps, retry_count, **_kwargs):
        return {"decision": original_decision, "threshold_used": 65, "reason": ""}

    def _operator_log(self, *_args, **_kwargs):
        return None


def _make_ensemble_response(
    selected="A",
    verdict="PASS",
    score=85,
    open_review="분위기 전환이 다소 급격함",
    feedback=None,
):
    """select_and_judge_ensemble이 파싱할 JSON 응답 생성."""
    import json

    return json.dumps(
        {
            "selected": selected,
            "verdict": verdict,
            "score": score,
            "score_breakdown": {},
            "selection_reason": "테스트",
            "feedback": feedback or {"issues": [], "action_items": []},
            "state_updates": {},
            "open_review": open_review,
            "contradiction_check": {"found_contradictions": []},
        },
        ensure_ascii=False,
    )


def _make_candidates(n=3):
    """분량 충족 더미 후보 3개."""
    return [
        {
            "strategy": f"strat_{i}",
            "strategy_name": f"전략{i + 1}",
            "manuscript": "가" * 6000,
            "title": f"제목{i + 1}",
            "state_updates": {},
        }
        for i in range(n)
    ]


# ===========================================================================
# Tests
# ===========================================================================


class TestOpenReviewPropagation:
    """open_review 전파 경로 검증."""

    def test_director_ensemble_returns_open_review(self):
        """select_and_judge_ensemble 반환 dict에 open_review top-level key 포함."""
        director = _FakeDirector()
        director._response = _make_ensemble_response(open_review="톤 급변 의심")
        selector = DirectorEnsembleSelector(director)

        result = selector.select_and_judge_ensemble(
            ep_num=10,
            candidates=_make_candidates(),
            validation_results=[{"warnings": []}] * 3,
            blueprint={"integrated_scenario": "시나리오"},
            previous_ending="이전 엔딩",
        )

        assert "open_review" in result
        assert result["open_review"] == "톤 급변 의심"

    def test_open_review_in_feedback_issues_via_tag(self):
        """open_review가 [자유 리뷰] 태그로 feedback.issues에 병합."""
        director = _FakeDirector()
        director._response = _make_ensemble_response(open_review="감정선 비약")
        selector = DirectorEnsembleSelector(director)

        result = selector.select_and_judge_ensemble(
            ep_num=10,
            candidates=_make_candidates(),
            validation_results=[{"warnings": []}] * 3,
            blueprint={"integrated_scenario": "시나리오"},
            previous_ending="이전 엔딩",
        )

        issues = result.get("feedback", {}).get("issues", [])
        tagged = [i for i in issues if "[자유 리뷰]" in str(i)]
        assert len(tagged) == 1
        assert "감정선 비약" in tagged[0]

    def test_trivial_open_review_not_in_issues(self):
        """'특이사항 없음'은 issues에 추가 안 됨."""
        director = _FakeDirector()
        director._response = _make_ensemble_response(open_review="특이사항 없음")
        selector = DirectorEnsembleSelector(director)

        result = selector.select_and_judge_ensemble(
            ep_num=10,
            candidates=_make_candidates(),
            validation_results=[{"warnings": []}] * 3,
            blueprint={"integrated_scenario": "시나리오"},
            previous_ending="이전 엔딩",
        )

        issues = result.get("feedback", {}).get("issues", [])
        tagged = [i for i in issues if "[자유 리뷰]" in str(i)]
        assert len(tagged) == 0

    def test_empty_open_review_returns_empty_string(self):
        """open_review 없으면 빈 문자열."""
        director = _FakeDirector()
        director._response = _make_ensemble_response(open_review="")
        selector = DirectorEnsembleSelector(director)

        result = selector.select_and_judge_ensemble(
            ep_num=10,
            candidates=_make_candidates(),
            validation_results=[{"warnings": []}] * 3,
            blueprint={"integrated_scenario": "시나리오"},
            previous_ending="이전 엔딩",
        )

        assert result.get("open_review") == ""

    def test_v60_97_swap_prefixes_open_review(self):
        """V60.97 swap 발생 시 open_review에 교체 사실 접두."""
        director = _FakeDirector()
        # LLM이 A를 선택하지만 A는 분량 미달 → B로 swap
        director._response = _make_ensemble_response(
            selected="A", verdict="PASS", score=70, open_review="감정선 전환 급격"
        )
        selector = DirectorEnsembleSelector(director)

        # 후보 A: 분량 미달 (100자), B/C: 분량 충족 (6000자)
        candidates = [
            {
                "strategy": "s0",
                "strategy_name": "전략1",
                "manuscript": "가" * 100,
                "title": "짧은",
                "state_updates": {},
            },
            {
                "strategy": "s1",
                "strategy_name": "전략2",
                "manuscript": "가" * 6000,
                "title": "긴B",
                "state_updates": {},
            },
            {
                "strategy": "s2",
                "strategy_name": "전략3",
                "manuscript": "가" * 6000,
                "title": "긴C",
                "state_updates": {},
            },
        ]

        result = selector.select_and_judge_ensemble(
            ep_num=10,
            candidates=candidates,
            validation_results=[{"warnings": []}] * 3,
            blueprint={"integrated_scenario": "시나리오"},
            previous_ending="이전 엔딩",
        )

        review = result.get("open_review", "")
        assert review.startswith("[V60.97 교체 전 후보 리뷰]"), f"expected swap prefix, got: {review}"
        assert "감정선 전환 급격" in review

    def test_director_prompt_receives_genre_strategy_contract_as_advisory(self):
        director = _FakeDirector()
        director._response = _make_ensemble_response(open_review="투자 장르 계약 반영")
        selector = DirectorEnsembleSelector(director)
        contract = build_genre_strategy_contract(GenreTypes.INVESTMENT, "action_focused")

        result = selector.select_and_judge_ensemble(
            ep_num=10,
            candidates=_make_candidates(),
            validation_results=[{"warnings": []}] * 3,
            blueprint={
                "integrated_scenario": "시나리오",
                "_ensemble_meta": {"genre_strategy_contract": contract},
            },
            previous_ending="이전 엔딩",
            story_context="기존 작품 맥락",
        )

        assert result["open_review"] == "투자 장르 계약 반영"
        assert "Genre Strategy Contract - Director-visible advisory" in director.last_prompt
        assert "selection context, not Python verdict authority" in director.last_prompt
        assert "capital exposure" in director.last_prompt
        assert "vehicle attack" in director.last_prompt
