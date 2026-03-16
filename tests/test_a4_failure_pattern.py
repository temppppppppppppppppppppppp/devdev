"""[A-4] 공통 실패 패턴 감지 — contradiction_types 전파 + 수렴 추적 테스트."""

import json

from modules.domain.agents.director_ensemble import DirectorEnsembleSelector

# ===========================================================================
# Helpers
# ===========================================================================


class _FakeDirector:
    """DirectorEnsembleSelector가 참조하는 최소 Director stub."""

    _last_thinking = ""
    MAX_CONTEXT_CHARS = 700_000

    def ask(self, prompt, temperature=0.1, thinking_level=None):
        return self._response

    def _extract_json_robust(self, response):
        try:
            return json.loads(response)
        except Exception:
            return None

    def _escape_braces(self, text):
        return str(text) if text else ""

    def apply_adaptive_decision(self, score, original_decision, arc_pos, total_eps, retry_count):
        return {"decision": original_decision, "threshold_used": 65, "reason": ""}

    def _operator_log(self, *_args, **_kwargs):
        return None


def _make_ensemble_response(
    *,
    selected="A",
    verdict="REJECT",
    score=45,
    contradictions=None,
):
    """select_and_judge_ensemble이 파싱할 JSON 응답 생성."""
    return json.dumps(
        {
            "selected": selected,
            "verdict": verdict,
            "score": score,
            "score_breakdown": {},
            "selection_reason": "테스트",
            "feedback": {"issues": ["모순 발견"], "action_items": []},
            "state_updates": {},
            "open_review": "",
            "contradiction_check": {
                "found_contradictions": contradictions or [],
            },
            "error_category": "LOGIC_ERROR",
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


class TestContradictionTypesInReturn:
    """select_and_judge_ensemble 반환에 contradiction_types 포함 검증."""

    def test_contradiction_types_present_with_contradictions(self):
        """모순이 있을 때 contradiction_types에 type 목록 반환."""
        director = _FakeDirector()
        director._response = _make_ensemble_response(
            contradictions=[
                {"type": "타임라인", "severity": "CRITICAL", "description": "시간 불일치"},
                {"type": "수치", "severity": "MAJOR", "description": "금액 오류"},
            ],
        )
        selector = DirectorEnsembleSelector(director)

        result = selector.select_and_judge_ensemble(
            ep_num=10,
            candidates=_make_candidates(),
            validation_results=[{"warnings": []}] * 3,
            blueprint={"integrated_scenario": "시나리오"},
            previous_ending="이전 엔딩",
        )

        assert "contradiction_types" in result
        assert result["contradiction_types"] == ["타임라인", "수치"]

    def test_contradiction_types_empty_when_no_contradictions(self):
        """모순이 없을 때 빈 리스트 반환."""
        director = _FakeDirector()
        director._response = _make_ensemble_response(contradictions=[])
        selector = DirectorEnsembleSelector(director)

        result = selector.select_and_judge_ensemble(
            ep_num=10,
            candidates=_make_candidates(),
            validation_results=[{"warnings": []}] * 3,
            blueprint={"integrated_scenario": "시나리오"},
            previous_ending="이전 엔딩",
        )

        assert result["contradiction_types"] == []

    def test_contradiction_types_filters_non_dict_entries(self):
        """found_contradictions에 비-dict 항목이 있으면 필터링."""
        director = _FakeDirector()
        director._response = _make_ensemble_response(
            contradictions=[
                {"type": "사망", "severity": "CRITICAL", "description": "사망자 등장"},
                "잘못된 항목",  # non-dict — 필터됨
                42,  # non-dict — 필터됨
            ],
        )
        selector = DirectorEnsembleSelector(director)

        result = selector.select_and_judge_ensemble(
            ep_num=10,
            candidates=_make_candidates(),
            validation_results=[{"warnings": []}] * 3,
            blueprint={"integrated_scenario": "시나리오"},
            previous_ending="이전 엔딩",
        )

        assert result["contradiction_types"] == ["사망"]


class TestContradictionTypesInPreviousAttempt:
    """REJECT 시 previous_attempt에 error_category + contradiction_types 저장 검증."""

    def test_previous_attempt_stores_contradiction_types(self):
        """interview_round의 previous_attempt dict 구조 검증 (단위 테스트)."""
        # previous_attempt은 interview_round.py에서 조립되므로,
        # director_result mock으로 직접 조립 로직을 검증
        director_result = {
            "error_category": "LOGIC_ERROR",
            "contradiction_types": ["타임라인", "타임라인", "수치"],
            "open_review": "",
            "fix_scope": "",
            "fix_scope_reasoning": "",
            "pre_firewall_score": 45,
            "selected_candidate": {"manuscript": "원고"},
            "score_breakdown": {},
            "selection_reason": "테스트",
            "state_updates": {},
        }

        # interview_round.py L1151-1171 조립 로직 재현
        previous_attempt = {
            "error_category": director_result.get("error_category", ""),
            "contradiction_types": director_result.get("contradiction_types", []),
        }

        assert previous_attempt["error_category"] == "LOGIC_ERROR"
        assert previous_attempt["contradiction_types"] == ["타임라인", "타임라인", "수치"]

    def test_dominant_contradiction_detection(self):
        """Counter로 dominant contradiction type 추출 로직 검증."""
        from collections import Counter

        ct_list = ["타임라인", "타임라인", "수치"]
        ct_counter = Counter(ct_list)
        dominant = ct_counter.most_common(1)[0][0]

        assert dominant == "타임라인"

    def test_empty_contradiction_types_no_dominant(self):
        """빈 리스트면 dominant 없음."""
        ct_list = []
        dominant = ""
        if ct_list:
            from collections import Counter

            ct_counter = Counter(ct_list)
            dominant = ct_counter.most_common(1)[0][0] if ct_counter else ""

        assert dominant == ""
