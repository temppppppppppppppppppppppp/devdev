"""[LM-E] FlashbackVerifier 테스트 — 회상/플래시백 오염 감지."""

import json

from modules.core.flashback_verifier import FlashbackVerifier

# ═══════════════════════════════════════════════════════════════
# DetectFlashbacks 테스트
# ═══════════════════════════════════════════════════════════════


class TestDetectFlashbacks:
    def test_single_marker(self):
        verifier = FlashbackVerifier()
        ms = "그는 조용히 눈을 감았다. 회상 속에서 스승의 얼굴이 떠올랐다."
        result = verifier.detect_flashbacks(ms)
        assert len(result) == 1
        assert result[0]["marker"] == "회상"
        assert "스승" in result[0]["text"]

    def test_multiple_markers(self):
        verifier = FlashbackVerifier()
        ms = "A" * 300 + "회상 속에서 그날의 일이 생각났다." + "B" * 300 + "예전에 있었던 일이 생각났다." + "C" * 300
        result = verifier.detect_flashbacks(ms)
        assert len(result) >= 2
        markers = [r["marker"] for r in result]
        assert "회상" in markers
        assert "예전에" in markers

    def test_no_markers(self):
        verifier = FlashbackVerifier()
        ms = "그는 검을 들고 앞으로 나아갔다. 바람이 불었다."
        result = verifier.detect_flashbacks(ms)
        assert result == []

    def test_max_flashbacks_cap(self):
        verifier = FlashbackVerifier()
        # 마커 6개 이상 배치 — 5개 상한
        parts = []
        markers = ["회상", "기억했다", "떠올렸다", "떠올랐다", "예전에", "돌이켜보면"]
        for m in markers:
            parts.append("X" * 300 + m + "Y" * 300)
        ms = "".join(parts)
        result = verifier.detect_flashbacks(ms)
        assert len(result) <= 5

    def test_context_window_200(self):
        verifier = FlashbackVerifier()
        prefix = "가" * 200
        suffix = "나" * 200
        ms = prefix + "회상" + suffix
        result = verifier.detect_flashbacks(ms)
        assert len(result) == 1
        # 전체 200자 윈도우: 마커 앞 100자 + 마커 + 뒤 100자 정도
        text = result[0]["text"]
        assert len(text) <= 210  # 마커 2자 + 앞뒤 각 100자 이내

    def test_duplicate_region_dedup(self):
        verifier = FlashbackVerifier()
        # "회상"과 "기억했다"가 바로 인접 → 윈도우가 겹침, 하나만 추출
        ms = "회상 속에서 기억했다."
        result = verifier.detect_flashbacks(ms)
        assert len(result) == 1  # 첫 마커만 잡히고 두 번째는 겹침으로 제거


# ═══════════════════════════════════════════════════════════════
# LlmCheck 테스트
# ═══════════════════════════════════════════════════════════════


class TestLlmCheck:
    def test_contamination_detected(self):
        contamination_response = json.dumps(
            [
                {
                    "marker": "회상",
                    "issue": "10화에서 스승은 검이 아니라 창을 사용했으나, 회상에서 검을 사용한 것으로 묘사",
                    "referenced_context": "10화: 스승이 창을 들고 제자를 가르쳤다",
                }
            ],
            ensure_ascii=False,
        )
        verifier = FlashbackVerifier(llm_ask=lambda _: contamination_response)
        ms = "A" * 100 + "회상 속에서 스승이 검을 휘두르던 모습이 떠올랐다." + "B" * 100
        result = verifier.check(ms, ep_num=20, reference_context="10화: 스승이 창을 들고 제자를 가르쳤다")
        assert len(result) == 1
        assert result[0]["marker"] == "회상"
        assert result[0]["severity"] == "MAJOR"
        assert result[0]["check"] == "flashback_contamination"
        assert "스승" in result[0]["issue"]

    def test_no_contamination(self):
        verifier = FlashbackVerifier(llm_ask=lambda _: "[]")
        ms = "A" * 100 + "회상 속에서 스승이 창을 들고 있었다." + "B" * 100
        result = verifier.check(ms, ep_num=20, reference_context="10화: 스승이 창을 들고 제자를 가르쳤다")
        assert result == []

    def test_no_llm_returns_empty(self):
        verifier = FlashbackVerifier(llm_ask=None)
        ms = "회상 속에서 스승이 말했다."
        result = verifier.check(ms, ep_num=20, reference_context="과거 맥락")
        assert result == []

    def test_no_reference_returns_empty(self):
        verifier = FlashbackVerifier(llm_ask=lambda _: "[]")
        ms = "회상 속에서 스승이 말했다."
        result = verifier.check(ms, ep_num=20, reference_context="")
        assert result == []

    def test_llm_exception_graceful(self):
        def _raise(_):
            raise RuntimeError("API 오류")

        verifier = FlashbackVerifier(llm_ask=_raise)
        ms = "A" * 100 + "회상 속에서 그때의 일이 떠올랐다." + "B" * 100
        result = verifier.check(ms, ep_num=20, reference_context="과거 맥락")
        assert result == []

    def test_json_in_code_fence(self):
        fenced = '```json\n[{"marker": "회상", "issue": "스승 무기 불일치", "referenced_context": "10화 창"}]\n```'
        verifier = FlashbackVerifier(llm_ask=lambda _: fenced)
        ms = "A" * 100 + "회상 속에서 스승이 검을 들었다." + "B" * 100
        result = verifier.check(ms, ep_num=20, reference_context="10화: 스승이 창을 들었다")
        assert len(result) == 1
        assert result[0]["marker"] == "회상"

    def test_invalid_json_graceful(self):
        verifier = FlashbackVerifier(llm_ask=lambda _: "이것은 JSON이 아닙니다")
        ms = "A" * 100 + "회상 속에서 그가 말했다." + "B" * 100
        result = verifier.check(ms, ep_num=20, reference_context="과거 맥락")
        assert result == []


# ═══════════════════════════════════════════════════════════════
# EdgeCases 테스트
# ═══════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_empty_manuscript(self):
        verifier = FlashbackVerifier(llm_ask=lambda _: "[]")
        result = verifier.check("", ep_num=10, reference_context="과거 맥락")
        assert result == []


# ═══════════════════════════════════════════════════════════════
# Integration 테스트
# ═══════════════════════════════════════════════════════════════


class TestIntegration:
    def test_check_returns_correct_format(self):
        response = json.dumps(
            [
                {
                    "marker": "떠올렸다",
                    "issue": "5화에서 보석은 파란색이었으나 회상에서 빨간색으로 묘사",
                    "referenced_context": "5화: 파란 보석이 빛났다",
                }
            ],
            ensure_ascii=False,
        )
        verifier = FlashbackVerifier(llm_ask=lambda _: response)
        ms = "A" * 100 + "그녀는 떠올렸다. 빨간 보석이 손안에서 빛나던 그 순간을." + "B" * 100
        result = verifier.check(ms, ep_num=15, reference_context="5화: 파란 보석이 빛났다")
        assert len(result) == 1
        item = result[0]
        # 필수 키 검증
        assert "marker" in item
        assert "issue" in item
        assert "referenced_context" in item
        assert item["severity"] == "MAJOR"
        assert item["check"] == "flashback_contamination"


# ═══════════════════════════════════════════════════════════════
# [LM-H] ManuscriptSnippets 테스트
# ═══════════════════════════════════════════════════════════════


class TestManuscriptSnippets:
    def test_manuscript_snippets_included_in_prompt(self):
        """manuscript_snippets가 프롬프트에 포함됨"""
        captured = []

        def _capture(prompt):
            captured.append(prompt)
            return "[]"

        verifier = FlashbackVerifier(llm_ask=_capture)
        ms = "A" * 100 + "회상 속에서 스승이 창을 들었다." + "B" * 100
        verifier.check(
            ms,
            ep_num=20,
            reference_context="10화 요약: 스승이 검을 들었다",
            manuscript_snippets="[제 10화 원문]\n스승이 빛나는 검을 뽑아들었다.",
        )
        assert captured
        prompt = captured[0]
        assert "원문 발췌" in prompt
        assert "스승이 빛나는 검을 뽑아들었다" in prompt

    def test_manuscript_snippets_priority_instruction(self):
        """원문 우선 참조 지시문이 프롬프트에 포함됨"""
        captured = []

        def _capture(prompt):
            captured.append(prompt)
            return "[]"

        verifier = FlashbackVerifier(llm_ask=_capture)
        ms = "A" * 100 + "회상 속에서 기억했다." + "B" * 100
        verifier.check(
            ms,
            ep_num=20,
            reference_context="요약",
            manuscript_snippets="원문 내용",
        )
        assert captured
        assert "원문을 우선 참조" in captured[0]

    def test_no_manuscript_snippets_no_priority_instruction(self):
        """manuscript_snippets 없으면 원문 우선 지시문 없음"""
        captured = []

        def _capture(prompt):
            captured.append(prompt)
            return "[]"

        verifier = FlashbackVerifier(llm_ask=_capture)
        ms = "A" * 100 + "회상 속에서 기억했다." + "B" * 100
        verifier.check(ms, ep_num=20, reference_context="요약")
        assert captured
        assert "원문을 우선 참조" not in captured[0]

    def test_format_includes_both_sections(self):
        """포맷에 요약과 원문 발췌 모두 포함"""
        verifier = FlashbackVerifier()
        flashbacks = [{"marker": "회상", "text": "회상 장면", "position": 0}]
        formatted = verifier._format_for_llm(
            flashbacks,
            "10화 요약: 스승이 검을 들었다",
            "10화 원문: 스승이 빛나는 검을 뽑아들었다.",
        )
        assert "에피소드 요약" in formatted
        assert "원고 원문 발췌" in formatted
        assert "스승이 빛나는 검을 뽑아들었다" in formatted

    def test_contamination_with_manuscript_snippets(self):
        """manuscript_snippets와 함께 오염 감지 성공"""
        response = json.dumps(
            [
                {
                    "marker": "회상",
                    "issue": "원문에서 스승은 창을 사용했으나 회상에서 검으로 묘사",
                    "referenced_context": "10화 원문: 스승이 창을 들고",
                }
            ],
            ensure_ascii=False,
        )
        verifier = FlashbackVerifier(llm_ask=lambda _: response)
        ms = "A" * 100 + "회상 속에서 스승이 검을 들었다." + "B" * 100
        result = verifier.check(
            ms,
            ep_num=20,
            reference_context="10화 요약",
            manuscript_snippets="[제 10화 원문]\n스승이 창을 들고 수련하고 있었다.",
        )
        assert len(result) == 1
        assert result[0]["check"] == "flashback_contamination"
