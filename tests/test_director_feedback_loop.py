"""[Phase3-ROI] Director REJECT 시 근거 요약 블록 피드백 테스트."""


def _build_evidence_block(selected: str, validation_results: list[dict]) -> str:
    """stage4_interview_round.py Phase3-ROI 로직을 추출한 순수 함수."""
    _selected_ci = (
        max(0, ord(selected) - ord("A"))
        if isinstance(selected, str) and selected.isalpha()
        else 0
    )
    _selected_vr = (
        validation_results[_selected_ci]
        if _selected_ci < len(validation_results)
        else {}
    )
    _evidence_lines: list[str] = []
    for _tw in (_selected_vr.get("truth_gate_warnings") or [])[:3]:
        if isinstance(_tw, dict):
            _evidence_lines.append(f"  [{_tw.get('severity', '?')}] {_tw.get('text', '')}")
    for _sv in (_selected_vr.get("structured_violations") or [])[:3]:
        if isinstance(_sv, dict):
            _evidence_lines.append(f"  [VIOLATION] {_sv.get('reason', '')}")
    return (
        "[근거 요약 — 수정 시 반드시 반영]\n" + "\n".join(_evidence_lines) + "\n"
        if _evidence_lines
        else ""
    )


def _apply_evidence_to_feedback(evidence_block: str, director_feedback: str) -> str:
    if evidence_block:
        return evidence_block + director_feedback
    return director_feedback


# ─── 테스트 ──────────────────────────────────────────────────────────────────

def test_evidence_block_prepended_on_reject():
    """근거 블록이 director_feedback 앞에 위치해야 한다."""
    vr = [
        {
            "truth_gate_warnings": [{"severity": "CRITICAL", "text": "사망 NPC 등장"}],
            "structured_violations": [],
        }
    ]
    evidence = _build_evidence_block("A", vr)
    assert evidence.startswith("[근거 요약 — 수정 시 반드시 반영]")

    original_feedback = "캐릭터 동기 보완 필요"
    result = _apply_evidence_to_feedback(evidence, original_feedback)
    assert result.startswith("[근거 요약")
    assert original_feedback in result
    assert result.index("[근거 요약") < result.index(original_feedback)


def test_evidence_block_empty_when_no_warnings():
    """경고가 없으면 evidence_block이 빈 문자열 → director_feedback 변화 없음."""
    vr = [{"truth_gate_warnings": [], "structured_violations": []}]
    evidence = _build_evidence_block("A", vr)
    assert evidence == ""

    original_feedback = "원고 품질 개선 필요"
    result = _apply_evidence_to_feedback(evidence, original_feedback)
    assert result == original_feedback


def test_truth_gate_evidence_in_director_feedback():
    """TruthGate CRITICAL 경고가 director_feedback에 반영된다."""
    vr = [
        {
            "truth_gate_warnings": [
                {"severity": "CRITICAL", "text": "deceased NPC 홍길동 행동 감지"},
                {"severity": "WARNING", "text": "아이템 미등록"},
            ],
            "structured_violations": [],
        }
    ]
    evidence = _build_evidence_block("A", vr)
    assert "[CRITICAL]" in evidence
    assert "홍길동" in evidence
    assert "[WARNING]" in evidence


def test_structured_violation_in_director_feedback():
    """structured_violations reason이 [VIOLATION] 태그로 반영된다."""
    vr = [
        {
            "truth_gate_warnings": [],
            "structured_violations": [
                {"reason": "연속성 위반: 장소 불일치"},
                {"reason": "NPC 관계 모순"},
            ],
        }
    ]
    evidence = _build_evidence_block("A", vr)
    assert "[VIOLATION]" in evidence
    assert "연속성 위반" in evidence
    assert "NPC 관계 모순" in evidence
