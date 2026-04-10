from __future__ import annotations

import json
from pathlib import Path

from modules.core.reference_selection_stage0 import (
    build_stage0_selection_draft,
    sync_stage0_from_reference_selection,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _card_manifest(entries: list[dict]) -> dict:
    return {"entries": entries}


def test_build_stage0_selection_draft_parses_bullet_and_table_cards(temp_dir) -> None:
    work_id = "demo_work"
    project_root = temp_dir / "narrative_ssot" / "50_projects" / work_id
    cards_root = temp_dir / "narrative_ssot" / "10_reference_bank" / "cards"

    _write_json(
        project_root / "10_reference_selection" / "reference_selection.json",
        {
            "work_id": work_id,
            "selection_date": "2026-04-10",
            "selected_cards": [
                {
                    "card_slug": "alpha_invest",
                    "track": "A",
                    "handoff_label": "alpha_invest_A_slim_v1",
                    "selection_reason": "투자형 오프닝과 TR 2~6 속도감을 참고한다.",
                    "must_not_copy_applied": True,
                    "contamination_risk_reviewed": True,
                },
                {
                    "card_slug": "beta_authority",
                    "track": "A",
                    "handoff_label": "beta_authority_A_slim_v1",
                    "selection_reason": "공개 굴욕과 권위 시위를 보강한다.",
                    "must_not_copy_applied": True,
                    "contamination_risk_reviewed": True,
                },
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
                    "slug": "alpha_invest",
                    "track": "A",
                    "output_path": "material_ssot/10_research/20_fewshot_bank/cards/alpha_invest_A.md",
                },
                {
                    "slug": "beta_authority",
                    "track": "A",
                    "output_path": "material_ssot/10_research/20_fewshot_bank/cards/beta_authority_A.md",
                },
            ]
        ),
    )
    cards_root.mkdir(parents=True, exist_ok=True)
    (cards_root / "alpha_invest_A.md").write_text(
        """## 4. Slim Reference Card v1

- **source_label**: 알파 투자물
- **usable_lane**: 현대 현판 투자/기업물
- **usable_sector**: 투자물, 금융물
- **opening_humiliation**: 바닥 계좌와 무시당한 신입 출발
- **protagonist_edge**: 미래 정보와 투자 구조 설계
- **what**: 투자 구조를 선점한다
- **how**: 법인과 펀드를 먼저 세팅한다
- **block1_spike**: 지식 격차 → 거액 베팅
- **first_reward**: 첫 수익과 다음 딜 입장권
- **growth_axis**: 시드머니 → 펀드 → 지분 딜
- **authority_gain_route**: 첫 수익 → 시장 신뢰 → 더 큰 딜
- **sector_expansion_path**: 환율 → 주식 → 지분 딜
- **must_borrow**: 합법 인프라 먼저, 투자 나중
- **must_not_copy**: 고유 펀드명과 고유 이벤트
- **contamination_risk**: 실제 사건과 고유 장치 직이식 금지
- **source_manifest_ready_label**: alpha_invest_A_slim_v1

## 5. 현대 현판 적용 분해
""",
        encoding="utf-8",
    )
    (cards_root / "beta_authority_A.md").write_text(
        """## 4. Slim Reference Card v1

| 필드 | 값 |
| --- | --- |
| source_label | 베타 권위물 |
| usable_lane | 현대 현판 권위물 |
| usable_sector | 기업물, 법조물 |
| opening_humiliation | 상대 안방에 들어가기 전 공개 무시 |
| protagonist_edge | 숫자 증거와 제도적 권위 |
| what | 증거로 반박 불가 상태를 만든다 |
| how | 상대 안방에서 공개 굴욕을 실행한다 |
| block1_spike | 공개 굴욕과 권위 행사형 사이다 |
| first_reward | 첫 공개 승리와 상급자 인정 |
| growth_axis | 작은 승인권 → 큰 승인권 |
| authority_gain_route | 증거 제시 → 인정 획득 → 다음 전장 배정 |
| sector_expansion_path | 내부 승인 → 대외 협상 |
| must_borrow | 공개 굴욕과 증거 시위 |
| must_not_copy | 고유 직업 설정과 고유 조직 |
| contamination_risk | 동일 권한과 장면 구성을 그대로 복제하면 오염 |
| source_manifest_ready_label | beta_authority_A_slim_v1 |

## 5. 현대 현판 적용 분해
""",
        encoding="utf-8",
    )

    result = build_stage0_selection_draft(work_id, root=temp_dir)

    assert result.profile_lock["primary_profile"] == "investment_market_profile"
    assert result.source_manifest["reference_only_sources"][0].endswith("reference_selection.json")
    assert any(path.endswith("alpha_invest_A.md") for path in result.source_manifest["reference_only_sources"])
    assert result.material_bundle_summary["opening_bundle_contract"]["bundle_window"] == "TR 2~6"
    assert result.material_bundle_summary["opening_bundle_contract"]["macro_battlefield"] in {
        "첫 투자 인프라와 대형 베팅 전장",
        "증거 공개와 권위 행사 전장",
    }
    assert result.phase0_ready_snapshot["manual_audit_pass"] is False
    assert result.contamination_guard["must_not_copy_reviewed"] is True


def test_sync_stage0_from_reference_selection_writes_preprocess_files(temp_dir) -> None:
    work_id = "sync_demo"
    project_root = temp_dir / "narrative_ssot" / "50_projects" / work_id
    cards_root = temp_dir / "narrative_ssot" / "10_reference_bank" / "cards"

    _write_json(
        project_root / "10_reference_selection" / "reference_selection.json",
        {
            "work_id": work_id,
            "selection_date": "2026-04-10",
            "selected_cards": [
                {
                    "card_slug": "gamma_office",
                    "track": "A",
                    "handoff_label": "gamma_office_A_slim_v1",
                    "selection_reason": "직장형 승인권과 조직 권력을 쓴다.",
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
                    "slug": "gamma_office",
                    "track": "A",
                    "output_path": "material_ssot/10_research/20_fewshot_bank/cards/gamma_office_A.md",
                }
            ]
        ),
    )
    cards_root.mkdir(parents=True, exist_ok=True)
    (cards_root / "gamma_office_A.md").write_text(
        """## 4. Slim Reference Card v1

- **usable_lane**: 현대 현판 직장물
- **usable_sector**: 직장물, 기업물
- **opening_humiliation**: 결재선에서 밀려난 신입
- **protagonist_edge**: 승인권과 실무 통제력
- **block1_spike**: 결재선 공개 반전
- **first_reward**: 첫 승인권 확보
- **growth_axis**: 승인권 → 조직 권력
- **authority_gain_route**: 실무 성과 → 승인권 → 팀 재편
- **must_borrow**: 결재선과 승인권 중심 오프닝
- **must_not_copy**: 고유 회사와 고유 인물명
- **contamination_risk**: 직장 장면 그대로 복제 금지
- **source_manifest_ready_label**: gamma_office_A_slim_v1

## 5. 현대 현판 적용 분해
""",
        encoding="utf-8",
    )

    result = sync_stage0_from_reference_selection(work_id, root=temp_dir, write=True)

    assert len(result.updated_paths) == 5
    source_manifest = json.loads((project_root / "20_preprocess" / "source_manifest.json").read_text(encoding="utf-8"))
    profile_lock = json.loads((project_root / "20_preprocess" / "profile_lock.json").read_text(encoding="utf-8"))
    material_bundle = json.loads((project_root / "20_preprocess" / "material_bundle_summary.json").read_text(encoding="utf-8"))
    snapshot = json.loads((project_root / "20_preprocess" / "phase0_ready_snapshot.json").read_text(encoding="utf-8"))
    guard = json.loads((project_root / "10_reference_selection" / "contamination_guard.json").read_text(encoding="utf-8"))

    assert source_manifest["work_identity"]["primary_profile"] == "office_power_profile"
    assert profile_lock["hud_interpretation"]["capital"] == "승인권과 인사 자본"
    assert material_bundle["opening_bundle_contract"]["first_signboard_block"] == 3
    assert snapshot["profile_locked"] is True
    assert guard["contamination_risk_reviewed"] is True


def test_build_stage0_selection_draft_accepts_plain_bold_field_cards(temp_dir) -> None:
    work_id = "plain_demo"
    project_root = temp_dir / "narrative_ssot" / "50_projects" / work_id
    cards_root = temp_dir / "narrative_ssot" / "10_reference_bank" / "cards"

    _write_json(
        project_root / "10_reference_selection" / "reference_selection.json",
        {
            "work_id": work_id,
            "selection_date": "2026-04-10",
            "selected_cards": [
                {
                    "card_slug": "plain_card",
                    "track": "A",
                    "handoff_label": "plain_card_A_ready",
                    "selection_reason": "신입 과잉 성능형 오프닝을 잡는다.",
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
                    "slug": "plain_card",
                    "track": "A",
                    "output_path": "material_ssot/10_research/20_fewshot_bank/cards/plain_card_A.md",
                }
            ]
        ),
    )
    cards_root.mkdir(parents=True, exist_ok=True)
    (cards_root / "plain_card_A.md").write_text(
        """## Slim Reference Card v1

**usable_lane**: 현대 현판 기업물
**usable_sector**: 기업물, 직장물
**opening_humiliation**: 혼자 남겨진 신입
**protagonist_edge**: 실무 과잉 성능과 빠른 설계
**block1_spike**: 3화 안에 첫 인정과 첫 계약
**first_reward**: 첫 계약금과 팀 내 재평가
**growth_axis**: 실무 인정 → 계약 → 조직 권력
**authority_gain_route**: 결과물 공개 → 상급자 인정 → 다음 프로젝트 배정
**must_borrow**: 빠른 인정과 조직 권력 전환
**must_not_copy**: 고유 회사명과 인물명
**contamination_risk**: 고유 장면 직이식 금지
**source_manifest_ready_label**: plain_card_A_ready

## 현대 현판 적용 분해
""",
        encoding="utf-8",
    )

    result = build_stage0_selection_draft(work_id, root=temp_dir)

    assert result.profile_lock["primary_profile"] == "office_power_profile"
    assert result.material_bundle_summary["opening_bundle_contract"]["bundle_window"] == "TR 2~6"


def test_build_stage0_selection_draft_respects_profile_override(temp_dir) -> None:
    work_id = "override_demo"
    project_root = temp_dir / "narrative_ssot" / "50_projects" / work_id
    cards_root = temp_dir / "narrative_ssot" / "10_reference_bank" / "cards"

    _write_json(
        project_root / "10_reference_selection" / "reference_selection.json",
        {
            "work_id": work_id,
            "selection_date": "2026-04-10",
            "profile_override": {
                "primary_profile": "business_growth_profile",
                "secondary_profile": "investment_market_profile",
                "reason": "특허/스타트업 신호보다 기업 확장과 투자 축을 우선 lane으로 잠근다.",
            },
            "selected_cards": [
                {
                    "card_slug": "override_card",
                    "track": "A",
                    "handoff_label": "override_card_A_ready",
                    "selection_reason": "특허 기반 성장과 빠른 인정 구조를 참고한다.",
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
                    "slug": "override_card",
                    "track": "A",
                    "output_path": "material_ssot/10_research/20_fewshot_bank/cards/override_card_A.md",
                }
            ]
        ),
    )
    cards_root.mkdir(parents=True, exist_ok=True)
    (cards_root / "override_card_A.md").write_text(
        """## Slim Reference Card v1

**usable_lane**: 현대 현판 기업물 — 신입 과잉 성능형, 특허·기술 자산 축적형
**usable_sector**: 기업/스타트업 성장물, 지식재산 기반 부의 축적
**opening_humiliation**: 혼자 남은 고졸 신입
**protagonist_edge**: 특허 설계와 빠른 실무 우위
**block1_spike**: 빠른 인정과 첫 대형 계약
**first_reward**: 첫 계약금과 조직 재평가
**growth_axis**: 특허 자산 → 계약 → 산업 확장
**authority_gain_route**: 실적 공인 → 더 큰 딜 → 산업 확장
**must_borrow**: 빠른 보상과 기업 확장 구조
**must_not_copy**: 고유 회사명과 고유 실존 인물
**contamination_risk**: 고유 시대 배경과 고유 특허 장치 복제 금지
**source_manifest_ready_label**: override_card_A_ready

## 현대 현판 적용 분해
""",
        encoding="utf-8",
    )

    result = build_stage0_selection_draft(work_id, root=temp_dir)

    assert result.profile_lock["primary_profile"] == "business_growth_profile"
    assert result.profile_lock["secondary_profile"] == "investment_market_profile"
    assert "profile_override locked in reference_selection" in result.source_manifest["manual_audit_note"]
