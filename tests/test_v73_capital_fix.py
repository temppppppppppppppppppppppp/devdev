"""[V73] 자본금 역동기화 2중 방어 테스트."""

from unittest.mock import MagicMock, patch

from modules.core.genre_hud_manager import FinanceHUDManager
from modules.core.stage4_post_processor import Stage4PostProcessor

# ── 방어1: Director state_updates 우선 ──────────────────────────────────


def test_v73_skip_when_director_set_capital():
    """Director가 'capital' 키를 state_updates에 포함하면 _reconcile_capital 조기 리턴."""
    proc = Stage4PostProcessor.__new__(Stage4PostProcessor)
    proc.ctx = MagicMock()
    # FinanceHUDManager 체크 통과용
    mock_hud = MagicMock(spec=FinanceHUDManager)
    proc.ctx.sys.hud = mock_hud

    with patch.object(proc, "_extract_capital_from_manuscript") as mock_extract:
        proc._reconcile_capital(
            final_manuscript="자본금 200억이다.",
            ep_num=5,
            final_state_updates={"capital": "200억"},
        )
        # Director가 capital 설정 → extract 호출 안 됨
        mock_extract.assert_not_called()


def test_v73_skip_when_director_set_jabon():
    """'자본금' 키도 대소문자 무관하게 감지."""
    proc = Stage4PostProcessor.__new__(Stage4PostProcessor)
    proc.ctx = MagicMock()
    proc.ctx.sys.hud = MagicMock(spec=FinanceHUDManager)

    with patch.object(proc, "_extract_capital_from_manuscript") as mock_extract:
        proc._reconcile_capital(
            final_manuscript="자본금 200억",
            ep_num=3,
            final_state_updates={"자본금": "200억"},
        )
        mock_extract.assert_not_called()


def test_v73_runs_when_director_no_capital():
    """Director state_updates에 capital 없으면 정상 실행."""
    proc = Stage4PostProcessor.__new__(Stage4PostProcessor)
    proc.ctx = MagicMock()
    mock_hud = MagicMock(spec=FinanceHUDManager)
    mock_hud.pro_data = {"capital": "100억"}
    proc.ctx.sys.hud = mock_hud

    # capital 없는 state_updates → 실행 진행 (크래시 없음만 확인)
    try:
        proc._reconcile_capital(
            final_manuscript="잔고 200억이 남아있었다.",
            ep_num=7,
            final_state_updates={"exp": 500},
        )
    except Exception as e:  # pragma: no cover - 명시적 방어 테스트
        assert False, f"예외 발생: {e}"


# ── 방어2: 대사 제거 후 regex ────────────────────────────────────────────


def test_v73_dialogue_capital_excluded():
    """대사 속 타인 자산은 추출되지 않아야 한다."""
    manuscript = (
        "나레이션: 잔고 50억이 남아있다.\n"
        '"김사장 자산이 300억이나 된다고?" 그가 말했다.'
    )
    result = Stage4PostProcessor._extract_capital_from_manuscript(manuscript)
    # 대사(300억) 제거 → 나레이션(50억)만 남아야 함
    assert result == 50.0, f"expected 50.0, got {result}"


def test_v73_narration_capital_extracted():
    """나레이션 자본금은 정상 추출."""
    manuscript = "그의 잔고는 150억이었다. 충분한 실탄이었다."
    result = Stage4PostProcessor._extract_capital_from_manuscript(manuscript)
    assert result == 150.0, f"expected 150.0, got {result}"


def test_v73_dialogue_only_returns_none():
    """자본금 언급이 대사 내부에만 있으면 None 반환."""
    manuscript = '"잔고가 80억이래." 비서가 보고했다.'
    result = Stage4PostProcessor._extract_capital_from_manuscript(manuscript)
    assert result is None, f"expected None, got {result}"


def test_v73_no_capital_mention_returns_none():
    """자본금 언급 없으면 None."""
    assert Stage4PostProcessor._extract_capital_from_manuscript("오늘도 하루가 지났다.") is None
