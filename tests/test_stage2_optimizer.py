"""Stage2Optimizer regression tests."""

from modules.core.stage2_optimizer import ArcAutoCorrector


def test_remove_duplicate_items_normalizes_item_key():
    corrector = ArcAutoCorrector()
    arc = {
        "state_constraints": {
            "items_acquired": [
                {"item": "철검"},
                {"name": "벽력단"},
            ]
        }
    }
    prev_arcs = [
        {
            "state_constraints": {"items_acquired": ["철검"]},
            "joint_docs": {"physical_inventory": []},
        }
    ]

    corrected = corrector._remove_duplicate_items(arc, prev_arcs)

    assert corrected["state_constraints"]["items_acquired"] == ["벽력단"]


def test_fix_start_location_prefers_arc_end_state_over_joint_docs():
    corrector = ArcAutoCorrector()
    arc = {"state_constraints": {"arc_start_state": {"location": "강남 테헤란로"}}}
    prev_arcs = [
        {
            "state_constraints": {"arc_end_state": {"location": "여의도 IFC"}},
            "joint_docs": {"final_location": "삼성동 무역센터"},
        }
    ]

    corrected = corrector._fix_start_location(arc, prev_arcs)

    assert corrected["state_constraints"]["arc_start_state"]["location"] == "여의도 IFC"


def test_sync_final_location_strips_time_info():
    corrector = ArcAutoCorrector()
    arc = {
        "joint_docs": {
            "final_location": "서울 강남구 테헤란로, SW인베스트먼트 오피스. 시계는 2006년 8월 18일 금요일, 오후 4시 30분, 장 마감 직후를 가리킨다."
        },
        "state_constraints": {"arc_end_state": {"location": ""}},
    }

    corrected = corrector._sync_final_location(arc)

    assert corrected["state_constraints"]["arc_end_state"]["location"] == "서울 강남구 테헤란로, SW인베스트먼트 오피스"


def test_sync_final_location_preserves_pure_location():
    corrector = ArcAutoCorrector()
    arc = {
        "joint_docs": {"final_location": "여의도 IFC 오피스"},
        "state_constraints": {"arc_end_state": {"location": "강남"}},
    }

    corrected = corrector._sync_final_location(arc)

    assert corrected["state_constraints"]["arc_end_state"]["location"] == "여의도 IFC 오피스"


def test_sync_final_location_collapses_scene_prose_to_canonical_label():
    corrector = ArcAutoCorrector()
    arc = {
        "joint_docs": {
            "final_location": "서울 강남, SW인베스트먼트 오피스, 아직 페인트 냄새가 남은 텅 빈 회의실과 모니터가 켜진 임시 작업 공간"
        },
        "state_constraints": {"arc_end_state": {"location": ""}},
    }

    corrected = corrector._sync_final_location(arc)

    assert corrected["state_constraints"]["arc_end_state"]["location"] == "서울 강남, SW인베스트먼트 오피스"


def test_strip_wuxia_fields_investment():
    corrector = ArcAutoCorrector()
    arc = {
        "state_constraints": {
            "arc_start_state": {"location": "여의도", "internal_energy": 100, "realm": "후천"},
            "arc_end_state": {"location": "강남", "internal_energy": 90, "martial_arts": "태극권"},
            "items_consumed": [],
        }
    }

    corrected, _ = corrector.auto_correct(arc, prev_arcs=[], genre="investment")

    assert "internal_energy" not in corrected["state_constraints"]["arc_start_state"]
    assert "realm" not in corrected["state_constraints"]["arc_start_state"]
    assert "internal_energy" not in corrected["state_constraints"]["arc_end_state"]
    assert "martial_arts" not in corrected["state_constraints"]["arc_end_state"]


def test_strip_wuxia_fields_wuxia_preserved():
    corrector = ArcAutoCorrector()
    arc = {
        "state_constraints": {
            "arc_start_state": {"location": "무림", "internal_energy": 50},
            "arc_end_state": {"location": "무림", "internal_energy": 55},
            "items_consumed": [],
        }
    }

    corrected, _ = corrector.auto_correct(arc, prev_arcs=[], genre="wuxia")

    assert corrected["state_constraints"]["arc_start_state"]["internal_energy"] == 50
    assert corrected["state_constraints"]["arc_end_state"]["internal_energy"] == 55


def test_filter_abstract_items_consumed():
    corrector = ArcAutoCorrector()
    arc = {
        "state_constraints": {
            "arc_start_state": {},
            "arc_end_state": {},
            "items_consumed": [
                "커피",
                "가족의 무관심이라는 방패막",
                "첫 거래의 기회비용",
                "길이가아주아주긴소모항목이름테스트용",
            ],
        }
    }

    corrected, _ = corrector.auto_correct(arc, prev_arcs=[], genre="investment")

    assert corrected["state_constraints"]["items_consumed"] == ["커피"]


def test_patch_b_reads_protagonist_items_over_items_acquired():
    """[BUG-F] protagonist_items 우선 폴백 — items_acquired만 읽던 오탐 수정."""
    corrector = ArcAutoCorrector()
    prev_arcs = [{
        "state_constraints": {
            "arc_end_state": {"location": "강남", "equipment": ["법인 서류"]},
        },
        "joint_docs": {},
    }]
    arc = {
        "state_constraints": {
            "arc_start_state": {"location": "강남", "equipment": ["법인 서류"]},
            "arc_end_state": {"location": "여의도", "equipment": ["법인 서류", "WTI 확인서"]},
            # API 스키마가 protagonist_items를 강제 → items_acquired 없음
            "protagonist_items": ["WTI 확인서"],
            "items_consumed": [],
        }
    }

    _, corrections = corrector.auto_correct(arc, prev_arcs=prev_arcs, genre="investment")

    # protagonist_items가 정상 인식되면 "출처 불명" 오탐이 없어야 함
    assert not any("출처 불명" in msg for msg in corrections), (
        f"protagonist_items를 인식하지 못해 오탐 발생: {corrections}"
    )


def test_patch_b_falls_back_to_items_acquired():
    """[BUG-F] protagonist_items 없으면 items_acquired 폴백."""
    corrector = ArcAutoCorrector()
    prev_arcs = [{
        "state_constraints": {
            "arc_end_state": {"location": "강남", "equipment": ["법인 서류"]},
        },
        "joint_docs": {},
    }]
    arc = {
        "state_constraints": {
            "arc_start_state": {"location": "강남", "equipment": ["법인 서류"]},
            "arc_end_state": {"location": "여의도", "equipment": ["법인 서류", "WTI 확인서"]},
            "items_acquired": ["WTI 확인서"],
            "items_consumed": [],
        }
    }

    _, corrections = corrector.auto_correct(arc, prev_arcs=prev_arcs, genre="investment")

    assert not any("출처 불명" in msg for msg in corrections), (
        f"items_acquired 폴백 실패: {corrections}"
    )


def test_patch_b_detects_truly_unexplained_items():
    """[BUG-F] 진짜 출처 불명 아이템은 정상 감지."""
    corrector = ArcAutoCorrector()
    prev_arcs = [{
        "state_constraints": {
            "arc_end_state": {"location": "강남", "equipment": ["법인 서류"]},
        },
        "joint_docs": {},
    }]
    arc = {
        "state_constraints": {
            "arc_start_state": {"location": "강남", "equipment": ["법인 서류"]},
            "arc_end_state": {"location": "여의도", "equipment": ["법인 서류", "WTI 확인서", "미스터리 아이템"]},
            "protagonist_items": ["WTI 확인서"],
            "items_consumed": [],
        }
    }

    _, corrections = corrector.auto_correct(arc, prev_arcs=prev_arcs, genre="investment")

    assert any("출처 불명" in msg and "미스터리 아이템" in msg for msg in corrections)


def test_asset_growth_rate_over_200pct():
    corrector = ArcAutoCorrector()
    prev_arcs = [{"state_constraints": {"arc_end_state": {"location": "여의도"}}, "joint_docs": {}}]
    arc = {
        "state_constraints": {
            "arc_start_state": {"location": "여의도", "total_assets": "20억", "equipment": []},
            "arc_end_state": {"location": "여의도", "total_assets": "80억", "equipment": []},
            "items_acquired": [],
            "items_consumed": [],
        }
    }

    _, corrections = corrector.auto_correct(arc, prev_arcs=prev_arcs, genre="investment")

    assert any("[PATCH-A]" in msg for msg in corrections)


def test_asset_growth_rate_under_200pct():
    corrector = ArcAutoCorrector()
    prev_arcs = [{"state_constraints": {"arc_end_state": {"location": "여의도"}}, "joint_docs": {}}]
    arc = {
        "state_constraints": {
            "arc_start_state": {"location": "여의도", "total_assets": "20억", "equipment": []},
            "arc_end_state": {"location": "여의도", "total_assets": "50억", "equipment": []},
            "items_acquired": [],
            "items_consumed": [],
        }
    }

    _, corrections = corrector.auto_correct(arc, prev_arcs=prev_arcs, genre="investment")

    assert not any("[PATCH-A]" in msg for msg in corrections)


def test_equipment_unexplained_appearance():
    corrector = ArcAutoCorrector()
    prev_arcs = [
        {
            "state_constraints": {"arc_end_state": {"location": "여의도", "equipment": ["ThinkPad T60"]}},
            "joint_docs": {"physical_inventory": ["ThinkPad T60"]},
        }
    ]
    arc = {
        "state_constraints": {
            "arc_start_state": {"location": "여의도", "equipment": ["ThinkPad T60"]},
            "arc_end_state": {"location": "여의도", "equipment": ["ThinkPad T60", "Dell XPS"]},
            "items_acquired": [],
            "items_consumed": [],
        }
    }

    _, corrections = corrector.auto_correct(arc, prev_arcs=prev_arcs, genre="investment")

    assert any("출처 불명 소지품" in msg for msg in corrections)


def test_equipment_disappearance():
    corrector = ArcAutoCorrector()
    prev_arcs = [
        {
            "state_constraints": {"arc_end_state": {"location": "여의도", "equipment": ["ThinkPad T60"]}},
            "joint_docs": {"physical_inventory": ["ThinkPad T60"]},
        }
    ]
    arc = {
        "state_constraints": {
            "arc_start_state": {"location": "여의도", "equipment": []},
            "arc_end_state": {"location": "여의도", "equipment": []},
            "items_acquired": [],
            "items_consumed": [],
        }
    }

    _, corrections = corrector.auto_correct(arc, prev_arcs=prev_arcs, genre="investment")

    assert any("이전 Arc 소지품 소멸" in msg for msg in corrections)


def test_equipment_normal_flow():
    corrector = ArcAutoCorrector()
    prev_arcs = [
        {
            "state_constraints": {"arc_end_state": {"location": "여의도", "equipment": ["ThinkPad T60"]}},
            "joint_docs": {"physical_inventory": ["ThinkPad T60"]},
        }
    ]
    arc = {
        "state_constraints": {
            "arc_start_state": {"location": "여의도", "equipment": ["ThinkPad T60"]},
            "arc_end_state": {"location": "여의도", "equipment": ["ThinkPad T60", "USB"]},
            "items_acquired": ["USB"],
            "items_consumed": [],
        }
    }

    _, corrections = corrector.auto_correct(arc, prev_arcs=prev_arcs, genre="investment")

    assert not any("[PATCH-B]" in msg for msg in corrections)


def test_asset_diff_between_arcs_advisory():
    corrector = ArcAutoCorrector()
    prev_arcs = [
        {
            "state_constraints": {"arc_end_state": {"location": "여의도", "total_assets": "100억", "equipment": []}},
            "joint_docs": {"physical_inventory": []},
        }
    ]
    arc = {
        "state_constraints": {
            "arc_start_state": {"location": "여의도", "total_assets": "90억", "equipment": []},
            "arc_end_state": {"location": "여의도", "total_assets": "95억", "equipment": []},
            "items_acquired": [],
            "items_consumed": [],
        }
    }

    _, corrections = corrector.auto_correct(arc, prev_arcs=prev_arcs, genre="investment")

    assert any("[PATCH-D]" in msg for msg in corrections)


def test_tactical_location_mismatch():
    corrector = ArcAutoCorrector()
    arc = {
        "tactical_doc": (
            "제 1화: 여의도 본사에서 시작해 시장 분석을 진행한다.\n"
            "제 2화: 여의도 본사 회의실에서 계약 검토를 마무리한다. "
            "주요 리스크 점검과 회의록 정리를 끝내고 다음 단계를 준비한다."
        ),
        "joint_docs": {"final_location": "서울 강남구 테헤란로 오피스"},
        "state_constraints": {
            "arc_start_state": {"location": "여의도"},
            "arc_end_state": {"location": "서울 강남구 테헤란로 오피스"},
            "items_consumed": [],
        },
    }

    _, corrections = corrector.auto_correct(arc, prev_arcs=[], genre="investment")

    assert any("[PATCH-C]" in msg for msg in corrections)


def test_tactical_location_match():
    corrector = ArcAutoCorrector()
    arc = {
        "tactical_doc": (
            "제 1화: 여의도에서 투자안을 정리한다.\n"
            "제 2화: 서울 강남구 테헤란로 오피스로 이동해 결산을 마치고 아크를 종료한다. "
            "장부 정리와 팀 브리핑까지 완료한 뒤 종료 위치를 확정한다."
        ),
        "joint_docs": {"final_location": "서울 강남구 테헤란로 오피스"},
        "state_constraints": {
            "arc_start_state": {"location": "여의도"},
            "arc_end_state": {"location": "서울 강남구 테헤란로 오피스"},
            "items_consumed": [],
        },
    }

    _, corrections = corrector.auto_correct(arc, prev_arcs=[], genre="investment")

    assert not any("[PATCH-C]" in msg for msg in corrections)


def test_sanitize_tactical_meta_terms_arc():
    corrector = ArcAutoCorrector()
    arc = {
        "tactical_doc": "이전 Arc 종료 후 약 2주가 흘렀고, Arc 4 구간의 여파가 남았다.",
        "state_constraints": {"arc_start_state": {}, "arc_end_state": {}, "items_consumed": []},
        "joint_docs": {},
    }

    corrected, corrections = corrector.auto_correct(arc, prev_arcs=[], genre="investment")

    assert "Arc" not in corrected["tactical_doc"]
    assert "이전 시기 종료" in corrected["tactical_doc"]
    assert any("[C-1]" in msg for msg in corrections)


def test_sanitize_tactical_meta_terms_arc_number_korean_suffix():
    corrector = ArcAutoCorrector()
    arc = {
        "tactical_doc": "Arc 2에서 시작한 거래 전략이 Arc 3으로 이어진다.",
        "state_constraints": {"arc_start_state": {}, "arc_end_state": {}, "items_consumed": []},
        "joint_docs": {},
    }

    corrected, _ = corrector.auto_correct(arc, prev_arcs=[], genre="investment")

    assert "해당 시기에서" in corrected["tactical_doc"]
    assert "시기 2에서" not in corrected["tactical_doc"]
