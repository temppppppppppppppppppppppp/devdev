"""[B-4] CW self-critique 주인공 동기/약속 방치 감지 테스트."""

import pytest

from modules.domain.agents.chief_writer_quality import ChiefWriterQualityGate


@pytest.fixture
def quality_gate():
    """최소 QualityGate 인스턴스."""
    gate = ChiefWriterQualityGate.__new__(ChiefWriterQualityGate)
    return gate


class TestMotivationConsistency:
    """B-4: _check_motivation_consistency 단위 테스트."""

    def test_active_motivation_keyword_present(self, quality_gate):
        """활성 동기 키워드가 본문에 있으면 이슈 없음."""
        content = "주인공은 복수를 위해 검을 들었다."
        motivations = [{"text": "복수를 위한 여정", "status": "active"}]
        issues = quality_gate._check_motivation_consistency(content, motivations, [])
        assert len(issues) == 0

    def test_active_motivation_keyword_missing(self, quality_gate):
        """활성 동기 키워드가 본문에 없으면 motivation_abandoned."""
        content = "주인공은 시장에서 만두를 사 먹었다."
        motivations = [{"text": "복수를 위한 여정", "status": "active"}]
        issues = quality_gate._check_motivation_consistency(content, motivations, [])
        assert len(issues) == 1
        assert issues[0]["type"] == "motivation_abandoned"
        assert issues[0]["severity"] == "low"

    def test_resolved_motivation_ignored(self, quality_gate):
        """완료된 동기는 체크하지 않음."""
        content = "주인공은 시장에서 만두를 사 먹었다."
        motivations = [{"text": "복수를 위한 여정", "status": "resolved"}]
        issues = quality_gate._check_motivation_consistency(content, motivations, [])
        assert len(issues) == 0

    def test_promise_party_present_but_promise_unmentioned(self, quality_gate):
        """미이행 약속 당사자가 등장하는데 약속 내용 미언급."""
        content = "강호는 이영희를 만나 차를 마셨다."
        promises = [
            {
                "text": "무공 비급 전수 약속",
                "promiser": "이영희",
                "promisee": "강호",
                "status": "pending",
            }
        ]
        issues = quality_gate._check_motivation_consistency(content, [], promises)
        assert len(issues) == 1
        assert issues[0]["type"] == "promise_unacknowledged"

    def test_promise_party_present_and_promise_mentioned(self, quality_gate):
        """미이행 약속 당사자 등장 + 약속 내용도 언급 → 이슈 없음."""
        content = "강호는 이영희를 만나 무공 비급에 대해 이야기했다."
        promises = [
            {
                "text": "무공 비급 전수 약속",
                "promiser": "이영희",
                "promisee": "강호",
                "status": "pending",
            }
        ]
        issues = quality_gate._check_motivation_consistency(content, [], promises)
        assert len(issues) == 0

    def test_empty_content_returns_empty(self, quality_gate):
        """빈 본문이면 이슈 없음."""
        issues = quality_gate._check_motivation_consistency("", [{"text": "복수", "status": "active"}], [])
        assert len(issues) == 0
