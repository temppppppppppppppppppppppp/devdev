"""codex-item-regex-overhaul.md 구현 검증 테스트."""

import yaml

from modules.core.constraint_db import ConstraintDB
from modules.core.failure_analyzer import FailureAnalyzer
from modules.core.genre_schema_builder import get_item_suffixes
from modules.core.prompt_builder import GRANT_PATTERNS_COMPILED
from modules.core.semantic_item_registry import SemanticItemRegistry
from modules.domain.agents.arc_ensemble import _extract_forbidden_items


def test_unmatched_items_detects_gap():
    registry = SemanticItemRegistry()
    registry.register_item("맥북프로", arc_no=1)

    unmatched = registry.get_unmatched_items("investment")
    assert "맥북프로" in unmatched


def test_unmatched_items_known_suffix():
    registry = SemanticItemRegistry()
    registry.register_item("법인인감", arc_no=1)

    unmatched = registry.get_unmatched_items("investment")
    assert "법인인감" not in unmatched


def test_gap_report_suggests_suffixes():
    registry = SemanticItemRegistry()
    for item in ("맥북프로", "갤럭시프로", "에어팟프로"):
        registry.register_item(item, arc_no=1)

    report = FailureAnalyzer(db=None).item_suffix_gap_report(registry, genre="investment")
    assert report["unmatched_count"] >= 3
    assert "프로" in report["suggested_suffixes"]


def test_review_suffix_approve_reject():
    candidates = [
        {"suffix": "프로", "examples": ["맥북프로", "갤럭시프로"], "count": 2},
        {"suffix": "인감", "examples": ["법인인감", "개인인감"], "count": 2},
    ]

    def _fake_llm(_prompt: str) -> str:
        return (
            '[{"suffix":"프로","verdict":"REJECT","reason":"브랜드 접미사"},'
            '{"suffix":"인감","verdict":"APPROVE","reason":"문서/도구 접미사"}]'
        )

    reviewed = FailureAnalyzer(db=None).review_suffix_candidates(candidates, llm_ask=_fake_llm)
    by_suffix = {row["suffix"]: row for row in reviewed}

    assert by_suffix["프로"]["verdict"] == "REJECT"
    assert by_suffix["인감"]["verdict"] == "APPROVE"


def test_prompt_builder_grant_patterns_include_ssot_suffix():
    text = "대표가 법인인감을 수여받았다."
    assert any(pattern.search(text) for pattern, _ in GRANT_PATTERNS_COMPILED)


def test_constraint_db_extract_grants_uses_ssot_suffixes():
    db = ConstraintDB(project_context=None, genre="investment")
    grants = db._extract_grants_from_tactical("대표가 법인인감을 수여받았다.")
    assert any(str(grant).strip().endswith("인감") for grant in grants)


def test_arc_ensemble_forbidden_extraction_uses_ssot_suffixes():
    block = (
        "❌ 다음 아이템 획득 금지 (이미 보유 중):\n"
        "   ❌ 법인인감 - Arc 1에서 획득\n"
        "   ❌ 워크스테이션 - Arc 2에서 획득\n"
    )
    items = _extract_forbidden_items(block)

    assert "법인인감" in items
    assert "워크스테이션" in items
    assert not any(item.startswith("다음") for item in items)


def test_get_item_suffixes_loads_from_yaml():
    """YAML 파일에서 접미사를 로드하는지 확인."""
    suffixes = get_item_suffixes("investment")
    assert "통장" in suffixes
    assert "인감" in suffixes


def test_review_and_apply_suffixes_writes_yaml(tmp_path):
    """APPROVE된 접미사가 YAML에 자동 append되는지 확인."""
    # 임시 YAML 생성
    yaml_path = tmp_path / "item_suffixes.yaml"
    yaml_path.write_text(
        yaml.dump({"_common": ["패"], "investment": ["통장"]}, allow_unicode=True),
        encoding="utf-8",
    )

    # 10건 이상 unmatched 생성 — 각각 충분히 다른 아이템명
    registry = SemanticItemRegistry()
    unique_items = [
        "맥북프로", "갤럭시프로", "에어팟프로",
        "블루투스이어폰", "사무실열쇠고리", "전기자전거",
        "보조배터리", "태블릿피씨", "무선마우스",
        "레이저프린터", "커피머신", "스마트워치",
    ]
    for item in unique_items:
        registry.register_item(item, arc_no=1)

    def _fake_llm(_prompt: str) -> str:
        return '[{"suffix":"프로","verdict":"APPROVE","reason":"제품 접미사"}]'

    analyzer = FailureAnalyzer(db=None)

    # _append_to_suffix_yaml의 경로를 임시로 교체
    import modules.core.failure_analyzer as fa_mod
    original_method = fa_mod.FailureAnalyzer._append_to_suffix_yaml

    @staticmethod
    def _mock_append(genre, suffixes):
        import yaml as _yaml

        from modules.core.genre_schema_builder import _normalize_item_genre_key
        data = _yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        genre_key = _normalize_item_genre_key(genre) or "_common"
        existing = data.get(genre_key, [])
        if not isinstance(existing, list):
            existing = []
        for s in suffixes:
            s = str(s).strip()
            if s and s not in existing:
                existing.append(s)
        data[genre_key] = existing
        yaml_path.write_text(
            _yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )

    fa_mod.FailureAnalyzer._append_to_suffix_yaml = _mock_append
    try:
        result = analyzer.review_and_apply_suffixes(registry, genre="investment", llm_ask=_fake_llm)
        assert "프로" in result["approved"]

        # YAML에 실제로 추가되었는지
        updated = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        assert "프로" in updated["investment"]
    finally:
        fa_mod.FailureAnalyzer._append_to_suffix_yaml = original_method


def test_review_and_apply_skips_below_threshold():
    """unmatched 10건 미달 시 스킵."""
    registry = SemanticItemRegistry()
    registry.register_item("맥북프로", arc_no=1)

    result = FailureAnalyzer(db=None).review_and_apply_suffixes(registry, genre="investment")
    assert result["reviewed"] == 0


def test_semantic_registry_respects_runtime_protagonist_name():
    registry = SemanticItemRegistry()
    registry.register_item("법인인감", arc_no=1, owner="윤지후")

    assert registry.is_protagonist_item("법인인감", protagonist_name="윤지후") is True
    assert registry.get_protagonist_items("윤지후")[0]["name"] == "법인인감"

    registry.transfer_item("법인인감", from_owner="윤지후", to_owner="재무팀장", arc=2, protagonist_name="윤지후")
    lifecycle = registry.get_item_lifecycle("법인인감")
    assert lifecycle["current_state"] == "분배됨"
