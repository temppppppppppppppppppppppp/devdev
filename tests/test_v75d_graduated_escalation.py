"""[V75-D] 단계적 에스컬레이션 — inplace 패치 → 전면 재생성 테스트."""

from pathlib import Path

_SRC = Path("modules/core/stage4_orchestrator.py").read_text(encoding="utf-8")


# ── 1. _inplace_attempted 초기값 False ──────────────────────────


def test_inplace_attempted_flag_initialized():
    """_inplace_attempted = False 초기화가 존재하는지 확인."""
    assert "_inplace_attempted = False" in _SRC


# ── 2. streak=2 + inplace 미시도 → inplace 경로 진입 ────────────


def test_inplace_path_condition():
    """streak >= 2 이고 inplace 미시도 시 inplace 패치 경로로 진입."""
    assert "not _inplace_attempted" in _SRC
    # inplace 패치 호출 존재 확인
    assert "_inplace_patch_blueprint(" in _SRC


# ── 3. streak=2 + inplace 시도 완료 → full regen 경로 진입 ──────


def test_full_regen_after_inplace_condition():
    """inplace 시도 후 계속 실패하면 full regen 경로로 진입."""
    assert "_inplace_attempted and not _blueprint_regenerated" in _SRC


# ── 4. _inplace_patch_blueprint 호출 파라미터 확인 ──────────────


def test_inplace_patch_params():
    """inplace 패치 호출 시 blueprint, director_feedback, ep_num, arc_data 전달."""
    assert "original_blueprint=round_ctx.blueprint" in _SRC
    assert "director_feedback=director_feedback" in _SRC
    assert "ep_num=next_ep" in _SRC
    assert "arc_data=round_ctx.arc_data" in _SRC


# ── 5. V75-D 태그 존재 확인 ─────────────────────────────────────


def test_v75d_markers():
    """[V75-D] 마커가 소스에 존재."""
    assert "[V75-D]" in _SRC
    assert "V75-D" in _SRC


# ── 6. 단계적 순서 보장 (inplace → full regen) ──────────────────


def test_inplace_before_full_regen():
    """inplace 패치 블록이 full regen 블록보다 먼저 위치."""
    idx_inplace = _SRC.index("[V75-D] Step 1")
    idx_regen = _SRC.index("[V75-B] Step 2")
    assert idx_inplace < idx_regen, "inplace 패치가 full regen보다 먼저 위치해야 함"
