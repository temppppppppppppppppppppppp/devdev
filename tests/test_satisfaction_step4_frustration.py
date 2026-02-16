"""
[Phase 3-D4] 좌절-보상 타이머 (advisory) 테스트

ContinuityValidator.check_frustration_streak() + Stage4 advisory hook 검증.
"""

import inspect
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.core.db_manager import DBManager
from modules.validation.threshold_helper import _threshold


@pytest.fixture
def db(tmp_path):
    """In-memory DBManager."""
    d = DBManager(tmp_path / "test_frustration.db")
    yield d
    d.close()


@pytest.fixture
def validator_with_db(db):
    """ContinuityValidator with DB context."""
    from modules.validation.continuity_validator import ContinuityValidator

    ctx = MagicMock()
    ctx.db = db
    return ContinuityValidator(context=ctx)


class TestFrustrationStreak:
    """좌절 연속 화수 계산 검증."""

    def test_no_tags_returns_empty(self, validator_with_db):
        """태그가 없으면 빈 리스트."""
        warnings = validator_with_db.check_frustration_streak(ep_num=5)
        assert warnings == []

    def test_no_frustration_returns_empty(self, validator_with_db, db):
        """좌절 플래그가 없으면 경고 없음."""
        for ep in range(1, 5):
            db.save_satisfaction_tag(ep, {"primary_tag": "일상", "frustration_flag": False})
        warnings = validator_with_db.check_frustration_streak(ep_num=5)
        assert warnings == []

    def test_streak_below_threshold_empty(self, validator_with_db, db):
        """좌절 2화 연속은 warning 임계값(3) 미만."""
        db.save_satisfaction_tag(1, {"primary_tag": "좌절", "frustration_flag": True})
        db.save_satisfaction_tag(2, {"primary_tag": "좌절", "frustration_flag": True})
        warnings = validator_with_db.check_frustration_streak(ep_num=3)
        assert warnings == []

    def test_streak_3_warning(self, validator_with_db, db):
        """좌절 3화 연속이면 권장 경고."""
        for ep in range(1, 4):
            db.save_satisfaction_tag(ep, {"primary_tag": "좌절", "frustration_flag": True})
        warnings = validator_with_db.check_frustration_streak(ep_num=4)
        assert len(warnings) == 1
        assert "3화 연속" in warnings[0]
        assert "권장" in warnings[0]

    def test_streak_5_critical(self, validator_with_db, db):
        """좌절 5화 연속이면 심각 경고."""
        for ep in range(1, 6):
            db.save_satisfaction_tag(ep, {"primary_tag": "좌절", "frustration_flag": True})
        warnings = validator_with_db.check_frustration_streak(ep_num=6)
        assert len(warnings) == 1
        assert "5화 연속" in warnings[0]
        assert "심각" in warnings[0]

    def test_streak_reset_after_reward(self, validator_with_db, db):
        """중간 보상(비좌절) 등장 시 streak 리셋."""
        db.save_satisfaction_tag(1, {"primary_tag": "좌절", "frustration_flag": True})
        db.save_satisfaction_tag(2, {"primary_tag": "좌절", "frustration_flag": True})
        db.save_satisfaction_tag(3, {"primary_tag": "성취", "frustration_flag": False})
        db.save_satisfaction_tag(4, {"primary_tag": "좌절", "frustration_flag": True})
        warnings = validator_with_db.check_frustration_streak(ep_num=5)
        assert warnings == []

    def test_streak_counts_from_latest(self, validator_with_db, db):
        """과거 좌절이 많아도 최신이 비좌절이면 streak=0."""
        for ep in range(1, 6):
            db.save_satisfaction_tag(ep, {"primary_tag": "좌절", "frustration_flag": True})
        db.save_satisfaction_tag(6, {"primary_tag": "일상", "frustration_flag": False})
        warnings = validator_with_db.check_frustration_streak(ep_num=7)
        assert warnings == []


class TestFrustrationThresholds:
    """YAML/threshold_helper 설정값 검증."""

    def test_yaml_satisfaction_section_exists(self):
        """validation.yaml에 satisfaction 섹션 존재."""
        validation_yaml = Path(__file__).parent.parent / "config" / "settings" / "validation.yaml"
        text = validation_yaml.read_text(encoding="utf-8")
        assert "satisfaction:" in text
        assert "frustration_warning_streak" in text
        assert "frustration_critical_streak" in text

    def test_threshold_warning_default(self):
        """warning 임계값 기본 3."""
        assert _threshold("satisfaction.frustration_warning_streak", 3) == 3

    def test_threshold_critical_default(self):
        """critical 임계값 기본 5."""
        assert _threshold("satisfaction.frustration_critical_streak", 5) == 5


class TestStage4FrustrationHook:
    """Stage4 advisory hook 코드 존재/패턴 검증."""

    def test_hook_code_exists(self):
        """stage4_orchestrator 소스에 check_frustration_streak 호출 존재."""
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        source = inspect.getsource(Stage4Orchestrator)
        assert "check_frustration_streak" in source
        assert "[D Step 4]" in source

    def test_hook_non_blocking(self):
        """좌절 타이머 예외가 비차단 패턴인지 확인."""
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        source = inspect.getsource(Stage4Orchestrator)
        assert "좌절-보상 타이머 실패 (비차단)" in source

    def test_hook_injects_to_validation_results(self):
        """경고가 validation_results warnings로 주입되는지 확인."""
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        source = inspect.getsource(Stage4Orchestrator)
        assert 'validation_results[ci]["warnings"]' in source
        assert "[D Step 4] {_fw}" in source
        assert "warning_count" in source


class TestWarningFormat:
    """경고 메시지 형식 검증."""

    def test_warning_message_contains_streak_count(self, validator_with_db, db):
        """경고 문구에 연속 화수 포함."""
        for ep in range(1, 4):
            db.save_satisfaction_tag(ep, {"primary_tag": "좌절", "frustration_flag": True})
        warnings = validator_with_db.check_frustration_streak(ep_num=4)
        assert warnings
        assert "3화 연속" in warnings[0]

    def test_critical_message_contains_severe(self, validator_with_db, db):
        """심각 경고 문구에 '심각' 포함."""
        for ep in range(1, 6):
            db.save_satisfaction_tag(ep, {"primary_tag": "좌절", "frustration_flag": True})
        warnings = validator_with_db.check_frustration_streak(ep_num=6)
        assert warnings
        assert "심각" in warnings[0]
