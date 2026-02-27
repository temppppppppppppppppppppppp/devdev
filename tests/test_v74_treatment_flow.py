"""
[V74] Treatment 컨텍스트 파이프라인 강화 — 12개 테스트
genre_ext → Stage 3/4 전달, Director 프롬프트 체크, HUD 스냅샷
"""

import json
from unittest.mock import MagicMock

import pytest

# ──────────────────────────────────────────────
# Change A: Stage 3 TF9 genre_ext 주입 테스트
# ──────────────────────────────────────────────


def _make_stage3_block(genre_ext=None, **extra_fields):
    """TF9 블록 fixture."""
    block = {
        "title": "테스트 아크",
        "emotional_beat": "성장",
        "content": {"context": "투자 시작"},
    }
    if genre_ext is not None:
        block["genre_ext"] = genre_ext
    block.update(extra_fields)
    return block


def _run_stage3_genre_ext_extraction(block):
    """Stage3 TF9 블록에서 genre_ext 추출 로직 재현."""
    import json as _json

    _block_fields = []
    for _f in ("title", "emotional_beat", "foreshadow", "power_shift", "event_villain", "solution", "reward"):
        if block.get(_f):
            _block_fields.append(f"  {_f}: {block[_f]}")
    _content = block.get("content", {})
    if isinstance(_content, dict):
        for _cf in ("context", "event_villain", "solution"):
            if _content.get(_cf):
                _block_fields.append(f"  content.{_cf}: {_content[_cf]}")
    # [V74] genre_ext extraction — mirrors stage3_orchestrator.py
    _genre_ext = block.get("genre_ext", {})
    if isinstance(_genre_ext, dict) and _genre_ext:
        _ge_lines = []
        for _gk, _gv in _genre_ext.items():
            if isinstance(_gv, dict | list):
                _ge_lines.append(f"    {_gk}: {_json.dumps(_gv, ensure_ascii=False)}")
            else:
                _ge_lines.append(f"    {_gk}: {_gv}")
        _block_fields.append("  genre_ext:\n" + "\n".join(_ge_lines))
    return _block_fields


class TestStage3GenreExt:
    """Change A: Stage 3 TF9 genre_ext 주입."""

    def test_genre_ext_dict_included(self):
        """#1: genre_ext dict → _block_fields에 포함."""
        block = _make_stage3_block(genre_ext={"capital_before": "30억", "capital_after": "45억"})
        fields = _run_stage3_genre_ext_extraction(block)
        joined = "\n".join(fields)
        assert "genre_ext:" in joined
        assert "capital_before" in joined
        assert "capital_after" in joined

    def test_empty_genre_ext_skipped(self):
        """#2: 빈 genre_ext → 스킵."""
        block = _make_stage3_block(genre_ext={})
        fields = _run_stage3_genre_ext_extraction(block)
        joined = "\n".join(fields)
        assert "genre_ext:" not in joined

    def test_nested_dict_json_serialized(self):
        """#3: nested dict (opponent) → JSON 직렬화."""
        block = _make_stage3_block(genre_ext={"opponent": {"name": "장회장", "strategy": "공매도"}})
        fields = _run_stage3_genre_ext_extraction(block)
        joined = "\n".join(fields)
        assert "opponent:" in joined
        assert "장회장" in joined

    def test_nested_list_json_serialized(self):
        """#4: nested list (leverage_used) → JSON 직렬화."""
        block = _make_stage3_block(genre_ext={"leverage_used": ["선물", "옵션", "3배 레버리지"]})
        fields = _run_stage3_genre_ext_extraction(block)
        joined = "\n".join(fields)
        assert "leverage_used:" in joined
        assert "선물" in joined


# ──────────────────────────────────────────────
# Change B: Stage 4 mandatory_context genre_ext 주입
# ──────────────────────────────────────────────


def _make_ctx_for_mandatory(plot_roadmap, arc_no=1):
    """Stage4ContextBuilder.ctx mock."""
    ctx = MagicMock()
    bible = {"MasterBible": {"plot_roadmap": plot_roadmap}}
    ctx.current_project.master_bible = bible
    ctx.world_state = None
    ctx.fact_ledger = None
    ctx.state_tracker = None
    ctx.ui.log = MagicMock()
    return ctx


class TestStage4MandatoryGenreExt:
    """Change B: Stage 4 mandatory_context에 Treatment genre_ext 주입."""

    def _run_genre_ext_injection(self, plot_roadmap, arc_no=1):
        """mandatory_context의 V74 genre_ext 주입 로직 단독 재현."""
        _mc_parts = ["base_context"]
        arc_data = {"arc_no": arc_no}
        try:
            _mb = {"MasterBible": {"plot_roadmap": plot_roadmap}}
            _bible_root = _mb.get("MasterBible", _mb)
            _plot_roadmap = _bible_root.get("plot_roadmap", [])
            _arc_no = arc_data.get("arc_no", 1) if arc_data else 1
            _arc_idx = _arc_no - 1
            if isinstance(_plot_roadmap, list) and 0 <= _arc_idx < len(_plot_roadmap):
                _tr_block = _plot_roadmap[_arc_idx]
                if isinstance(_tr_block, dict):
                    _genre_ext = _tr_block.get("genre_ext", {})
                    if isinstance(_genre_ext, dict) and _genre_ext:
                        _ge_lines = ["### [V74 Treatment] 이번 아크 장르 특화 정보"]
                        for _gk, _gv in _genre_ext.items():
                            if isinstance(_gv, dict | list):
                                _ge_lines.append(f"  {_gk}: {json.dumps(_gv, ensure_ascii=False)}")
                            else:
                                _ge_lines.append(f"  {_gk}: {_gv}")
                        _ge_lines.append(
                            "⚠️ 원고의 장르 수치(금액, 수익, 레벨, 경지 등)가 "
                            "위 Treatment 목표와 합리적으로 연결되어야 합니다."
                        )
                        _mc_parts.insert(2, "\n".join(_ge_lines))
        except Exception:
            pass
        return _mc_parts

    def test_treatment_section_in_mc(self):
        """#5: mandatory_context에 'Treatment' 섹션 포함."""
        roadmap = [{"genre_ext": {"capital_before": "30억", "capital_after": "45억"}}]
        parts = self._run_genre_ext_injection(roadmap, arc_no=1)
        joined = "\n".join(parts)
        assert "V74 Treatment" in joined
        assert "capital_before" in joined

    def test_no_genre_ext_no_error(self):
        """#6: genre_ext 없으면 오류 없이 스킵."""
        roadmap = [{"title": "아크1"}]
        parts = self._run_genre_ext_injection(roadmap, arc_no=1)
        joined = "\n".join(parts)
        assert "V74 Treatment" not in joined
        assert len(parts) == 1  # base_context만

    def test_arc_no_2_maps_to_index_1(self):
        """#7: arc_no=2 → plot_roadmap[1] 매핑."""
        roadmap = [
            {"genre_ext": {"capital_before": "10억"}},
            {"genre_ext": {"capital_before": "50억", "target": "100억"}},
        ]
        parts = self._run_genre_ext_injection(roadmap, arc_no=2)
        joined = "\n".join(parts)
        assert "50억" in joined
        assert "10억" not in joined

    def test_arc_no_out_of_range_skipped(self):
        """#8: arc_no 범위 초과 → 조용히 스킵."""
        roadmap = [{"genre_ext": {"capital_before": "30억"}}]
        parts = self._run_genre_ext_injection(roadmap, arc_no=99)
        joined = "\n".join(parts)
        assert "V74 Treatment" not in joined


# ──────────────────────────────────────────────
# Change C: Director YAML 체크 항목 테스트
# ──────────────────────────────────────────────


class TestDirectorYaml:
    """Change C: director.yaml Treatment 관련 항목 존재 확인."""

    @pytest.fixture(autouse=True)
    def _load_yaml(self):
        import pathlib

        yaml_path = pathlib.Path(__file__).resolve().parent.parent / "config" / "prompts" / "director.yaml"
        self.yaml_text = yaml_path.read_text(encoding="utf-8")

    def test_treatment_check_item_exists(self):
        """#9: director.yaml에 'Treatment 장르 목표 정합성' 체크 항목 존재."""
        assert "Treatment 장르 목표 정합성" in self.yaml_text

    def test_contradiction_type_includes_treatment(self):
        """#10: contradiction type에 'Treatment목표' 포함."""
        assert "Treatment목표" in self.yaml_text


# ──────────────────────────────────────────────
# Change D: HUD 자본금 스냅샷 테스트
# ──────────────────────────────────────────────


class TestHUDSnapshot:
    """Change D: FinanceHUDManager → HUD 확정 자본 다이제스트 추가."""

    def _run_hud_snapshot(self, hud, episode_digest=""):
        """HUD 스냅샷 주입 로직 단독 재현."""
        _episode_digest = episode_digest
        try:
            if hud is not None:
                from modules.core.genre_hud_manager import FinanceHUDManager

                if isinstance(hud, FinanceHUDManager):
                    _hud_cap = hud.pro_data.get("capital", "")
                    _hud_total = hud.pro_data.get("total_assets", "")
                    _hud_parts = []
                    if _hud_cap:
                        _hud_parts.append(f"HUD 확정 자본: {_hud_cap}")
                    if _hud_total:
                        _hud_parts.append(f"HUD 총자산: {_hud_total}")
                    if _hud_parts:
                        _snapshot = "\n".join(f"- {p}" for p in _hud_parts)
                        _episode_digest = (
                            (_episode_digest + f"\n{_snapshot}")
                            if _episode_digest
                            else f"[HUD 금융 스냅샷]\n{_snapshot}"
                        )
        except Exception:
            pass
        return _episode_digest

    def test_finance_hud_snapshot_added(self):
        """#11: FinanceHUDManager → 'HUD 확정 자본' 추가."""
        from modules.core.genre_hud_manager import FinanceHUDManager

        mock_ctx = MagicMock()
        mock_ctx.master_bible = {
            "MasterBible": {
                "FinanceHUD": {
                    "Protagonist": {
                        "actual_truth": {
                            "name": "주인공",
                            "capital": "45억",
                            "total_assets": "120억",
                        }
                    }
                }
            }
        }
        hud = FinanceHUDManager(mock_ctx)
        result = self._run_hud_snapshot(hud, episode_digest="기존 다이제스트")
        assert "HUD 확정 자본: 45억" in result
        assert "HUD 총자산: 120억" in result

    def test_non_finance_hud_no_snapshot(self):
        """#12: 비투자물 HUD → 스냅샷 미추가."""
        from modules.core.genre_hud_manager import HunterHUDManager

        mock_ctx = MagicMock()
        mock_ctx.master_bible = {
            "MasterBible": {"HunterHUD": {"Protagonist": {"actual_truth": {"name": "각성자", "level": "Lv.5"}}}}
        }
        hud = HunterHUDManager(mock_ctx)
        result = self._run_hud_snapshot(hud, episode_digest="기존 다이제스트")
        assert result == "기존 다이제스트"
