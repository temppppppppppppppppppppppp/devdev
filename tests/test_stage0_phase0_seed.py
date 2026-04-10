from __future__ import annotations

import json
from pathlib import Path

from modules.core.stage0_phase0_seed import (
    build_phase0_seed_from_stage0,
    sync_phase0_seed_from_stage0,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _card_manifest(entries: list[dict]) -> dict:
    return {"entries": entries}


def test_build_phase0_seed_from_stage0_uses_reference_selection_authority(temp_dir) -> None:
    work_id = "phase0_demo"
    project_root = temp_dir / "narrative_ssot" / "50_projects" / work_id
    cards_root = temp_dir / "narrative_ssot" / "10_reference_bank" / "cards"

    _write_json(
        project_root / "10_reference_selection" / "reference_selection.json",
        {
            "work_id": work_id,
            "selection_date": "2026-04-10",
            "work_identity_override": {
                "title": "골든 루트",
                "commercial_label": "골든 카나리아",
                "slug_aliases": [
                    "카나리아 테스트",
                    "phase0_demo"
                ],
                "reason": "Stage0 authority가 test slug 대신 canonical title을 우선하도록 잠근다.",
            },
            "profile_override": {
                "primary_profile": "business_growth_profile",
                "secondary_profile": "investment_market_profile",
                "reason": "기업 성장 축을 주 profile로 잠근다.",
            },
            "opening_bundle_contract_override": {
                "bundle_window": "TR 2~6",
                "macro_battlefield": "첫 권위 시위와 투자 진입 전장",
                "macro_battlefield_map": [
                    "가문 내부 공개 증명",
                    "실무 라인 재평가",
                    "기관 전장 입장권 확보",
                ],
                "bundle_goal": "TR 2~6 안에 첫 권위 시위와 다음 투자 전장 입장권을 확보한다.",
                "first_signboard_block": 3,
                "representative_reevaluation_block": 4,
                "next_battlefield_ticket_block": 6,
                "timing_reconciliation_note": "opening macro battlefield는 기업 후계자 권위 시위로 잠근다.",
            },
            "selected_cards": [
                {
                    "card_slug": "phase0_card",
                    "track": "A",
                    "handoff_label": "phase0_card_A_ready",
                    "selection_reason": "권위 시위와 투자 성장의 opening seed를 참고한다.",
                    "must_not_copy_applied": True,
                    "contamination_risk_reviewed": True,
                }
            ],
        },
    )
    _write_json(
        project_root / "10_reference_selection" / "contamination_guard.json",
        {
            "must_not_copy_reviewed": False,
            "contamination_risk_reviewed": False,
            "notes": "",
        },
    )
    _write_json(
        temp_dir / "narrative_ssot" / "10_reference_bank" / "reference_card_manifest.json",
        _card_manifest(
            [
                {
                    "slug": "phase0_card",
                    "track": "A",
                    "output_path": "material_ssot/10_research/20_fewshot_bank/cards/phase0_card_A.md",
                }
            ]
        ),
    )
    cards_root.mkdir(parents=True, exist_ok=True)
    (cards_root / "phase0_card_A.md").write_text(
        """## Slim Reference Card v1

**usable_lane**: 현대 현판 기업물
**usable_sector**: 기업물, 투자물
**opening_humiliation**: 과소평가된 막내의 출발
**protagonist_edge**: 빠른 판단과 투자 감각
**block1_spike**: 첫 수익과 공개 재평가
**first_reward**: 첫 계약금과 입장권
**growth_axis**: 첫 인정 → 다음 계약 → 산업 확장
**authority_gain_route**: 실적 공인 → 권위 상승 → 다음 전장 배정
**must_borrow**: 권위 시위와 빠른 재평가
**must_not_copy**: 고유 회사명과 고유 권력 구도
**contamination_risk**: 고유 장면과 고유 권력 구도 직이식 금지
**source_manifest_ready_label**: phase0_card_A_ready

## 현대 현판 적용 분해
""",
        encoding="utf-8",
    )

    result = build_phase0_seed_from_stage0(work_id, root=temp_dir)

    assert result.phase0_design["title"] == "골든 루트"
    assert result.phase0_design["work_identity_surface"]["commercial_label"] == "골든 카나리아"
    assert result.phase0_design["work_identity_surface"]["slug_aliases"] == [
        "카나리아 테스트",
        "phase0_demo",
    ]
    assert result.phase0_design["opening_bundle_contract"]["macro_battlefield"] == "첫 권위 시위와 투자 진입 전장"
    assert result.phase0_design["opening_arc"]["first_signboard_block"] == 3
    assert result.phase0_design["planning_seed_authority"]["work_identity_resolution"].startswith(
        "work_identity_override locked"
    )
    assert result.phase0_design["planning_seed_authority"]["title_resolution"].startswith(
        "work_identity_override locked"
    )
    assert result.phase0_design["planning_seed_authority"]["profile_resolution"].startswith(
        "profile_override locked"
    )
    assert result.phase0_design["planning_seed_authority"]["opening_contract_resolution"].startswith(
        "opening_bundle_contract_override locked"
    )


def test_sync_phase0_seed_from_stage0_preserves_existing_manual_protagonist(temp_dir) -> None:
    work_id = "phase0_sync_demo"
    project_root = temp_dir / "narrative_ssot" / "50_projects" / work_id
    cards_root = temp_dir / "narrative_ssot" / "10_reference_bank" / "cards"

    _write_json(
        project_root / "10_reference_selection" / "reference_selection.json",
        {
            "work_id": work_id,
            "selection_date": "2026-04-10",
            "selected_cards": [
                {
                    "card_slug": "phase0_sync_card",
                    "track": "A",
                    "handoff_label": "phase0_sync_card_A_ready",
                    "selection_reason": "기업 성장 opening을 참고한다.",
                    "must_not_copy_applied": True,
                    "contamination_risk_reviewed": True,
                }
            ],
        },
    )
    _write_json(
        project_root / "10_reference_selection" / "contamination_guard.json",
        {
            "must_not_copy_reviewed": False,
            "contamination_risk_reviewed": False,
            "notes": "",
        },
    )
    _write_json(
        temp_dir / "narrative_ssot" / "10_reference_bank" / "reference_card_manifest.json",
        _card_manifest(
            [
                {
                    "slug": "phase0_sync_card",
                    "track": "A",
                    "output_path": "material_ssot/10_research/20_fewshot_bank/cards/phase0_sync_card_A.md",
                }
            ]
        ),
    )
    cards_root.mkdir(parents=True, exist_ok=True)
    (cards_root / "phase0_sync_card_A.md").write_text(
        """## Slim Reference Card v1

**usable_lane**: 현대 현판 기업물
**usable_sector**: 기업물
**opening_humiliation**: 고립된 막내의 출발
**protagonist_edge**: 계약 감각과 권위 시위
**block1_spike**: 첫 공개 승리
**first_reward**: 첫 계약권 확보
**growth_axis**: 첫 인정 → 사업 확장
**authority_gain_route**: 실적 공인 → 다음 전장 배정
**must_borrow**: 빠른 인정 구조
**must_not_copy**: 고유 인물과 고유 회사명
**contamination_risk**: 직이식 금지
**source_manifest_ready_label**: phase0_sync_card_A_ready

## 현대 현판 적용 분해
""",
        encoding="utf-8",
    )
    _write_json(
        project_root / "30_planning" / "phase0_design.json",
        {
            "work_id": work_id,
            "title": "",
            "protagonist": "한시우",
            "core_fantasy": "",
            "opening_arc": {},
            "opening_bundle_contract": {},
            "representative_spike": {},
            "growth_axis": {},
            "opponent_transition_plan": {},
            "payoff_axis": {},
        },
    )

    result = sync_phase0_seed_from_stage0(work_id, root=temp_dir, write=True)
    phase0_design = json.loads((project_root / "30_planning" / "phase0_design.json").read_text(encoding="utf-8"))

    assert len(result.updated_paths) == 1
    assert phase0_design["protagonist"] == "한시우"
    assert phase0_design["opening_bundle_contract"]["bundle_window"] == "TR 2~6"
    assert phase0_design["planning_seed_authority"]["stage0_source_mode"]
