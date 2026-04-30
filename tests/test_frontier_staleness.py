import hashlib

from modules.core.frontier_staleness import (
    detect_stage4_frontier_staleness,
    frontier_status_satisfied_by_stage3_lineage,
    mark_downstream_frontier_requires_revalidation,
)


class _Project:
    def __init__(self):
        self.blueprints = {
            6: {"ep_num": 6, "summary": "future blueprint"},
            7: {"ep_num": 7, "summary": "future blueprint"},
        }
        self.saved = {}

    def get_blueprint(self, ep_num):
        return self.blueprints.get(ep_num)

    def save_episode_blueprint(self, ep_num, data):
        self.saved[ep_num] = data


def test_detect_stage4_frontier_staleness_flags_completed_wti_month_mismatch():
    result = detect_stage4_frontier_staleness(
        ep_num=6,
        blueprint={"summary": "한미증권 VIP룸에서 WTI 6월물 15억 원 매수 지시를 반복한다."},
        arc_data={"tactical_doc": "가승인 서류와 PB 설득을 다시 처리한다."},
        prev_manuscript_text="WTI 원유 선물 3월물 매수 포지션에 전량 진입했다. 딸깍.",
    )

    assert result["stale"] is True
    assert result["severity"] == "hard"
    assert result["evidence"]["prev_wti_months"] == ["3"]
    assert result["evidence"]["frontier_wti_months"] == ["6"]


def test_detect_stage4_frontier_staleness_flags_stage3_meta_hash_mismatch_without_wti_terms():
    stale_hash = hashlib.sha256(b"old accepted contract").hexdigest()

    result = detect_stage4_frontier_staleness(
        ep_num=6,
        blueprint={
            "summary": "다음 법적 압박으로 넘어간다.",
            "_stage3_meta": {"source_prev_manuscript_hash": stale_hash},
        },
        arc_data={"tactical_doc": "제6화: 계약 후속 압박"},
        prev_manuscript_text="새로 확정된 계약 체결 완료. 모두가 서명본을 확인했다.",
    )

    assert result["stale"] is True
    assert result["severity"] == "hard"
    assert result["evidence"]["source"] == "_stage3_meta+accepted_prev_manuscript"
    assert result["evidence"]["recorded_prev_manuscript_hash"] == stale_hash


def test_detect_stage4_frontier_staleness_prefers_db_lineage_sidecar_over_stale_json_meta():
    prev_text = "확정된 WTI 원유 선물 3월물 포지션을 점검한다."
    prev_hash = hashlib.sha256(prev_text.encode("utf-8")).hexdigest()
    stale_hash = hashlib.sha256(b"old blueprint json lineage").hexdigest()

    result = detect_stage4_frontier_staleness(
        ep_num=6,
        blueprint={
            "summary": "확정 포지션을 리스크 관리한다.",
            "_stage3_meta": {
                "source_prev_manuscript_ep": 5,
                "source_prev_manuscript_hash": stale_hash,
            },
        },
        blueprint_lineage={
            "ep_num": 6,
            "source_prev_manuscript_ep": 5,
            "source_prev_manuscript_hash": prev_hash,
            "frontier_basis_version": "stage3-frontier-basis-v1",
            "lineage_complete": True,
        },
        arc_data={},
        prev_manuscript_text=prev_text,
    )

    assert result["stale"] is False


def test_detect_stage4_frontier_staleness_uses_db_lineage_sidecar_when_json_meta_missing():
    prev_text = "새로 확정된 계약 체결 완료. 모두가 서명본을 확인했다."
    stale_hash = hashlib.sha256(b"old accepted contract").hexdigest()

    result = detect_stage4_frontier_staleness(
        ep_num=6,
        blueprint={"summary": "다음 법적 압박으로 넘어간다."},
        blueprint_lineage={
            "ep_num": 6,
            "source_prev_manuscript_ep": 5,
            "source_prev_manuscript_hash": stale_hash,
            "lineage_complete": True,
        },
        arc_data={},
        prev_manuscript_text=prev_text,
    )

    assert result["stale"] is True
    assert result["evidence"]["source"] == "db_blueprint_lineage+accepted_prev_manuscript"


def test_detect_stage4_frontier_staleness_allows_verified_stage3_lineage_to_carry_same_position():
    prev_text = "WTI 원유 선물 3월물 매수 포지션에 15억 원 진입 완료. 딸깍."
    prev_hash = hashlib.sha256(prev_text.encode("utf-8")).hexdigest()

    result = detect_stage4_frontier_staleness(
        ep_num=6,
        blueprint={
            "summary": "남은 현금 5억 원을 확인하고 기존 WTI 3월물 롱 포지션의 리스크를 관리한다.",
            "_stage3_meta": {
                "source_prev_manuscript_ep": 5,
                "source_prev_manuscript_hash": prev_hash,
                "frontier_basis_version": "stage3-frontier-basis-v1",
            },
        },
        arc_data={"tactical_doc": "구버전 Arc에는 WTI 6월물 매수 지시와 가승인 서류가 남아 있다."},
        prev_manuscript_text=prev_text,
    )

    assert result["stale"] is False
    assert result["severity"] == "none"


def test_frontier_status_satisfied_by_db_lineage_sidecar():
    prev_text = "WTI 원유 선물 3월물 매수 포지션에 15억 원 진입 완료. 딸깍."
    prev_hash = hashlib.sha256(prev_text.encode("utf-8")).hexdigest()

    satisfied = frontier_status_satisfied_by_stage3_lineage(
        blueprint={"_stage3_meta": {"source_prev_manuscript_ep": 5, "source_prev_manuscript_hash": "stale"}},
        blueprint_lineage={
            "ep_num": 6,
            "source_prev_manuscript_ep": 5,
            "source_prev_manuscript_hash": prev_hash,
            "lineage_complete": True,
        },
        frontier_status={
            "status": "requires_actual_manuscript_revalidation",
            "evidence": {"accepted_ep": 5, "accepted_manuscript_hash": prev_hash},
        },
        prev_manuscript_text=prev_text,
    )

    assert satisfied is True


def test_detect_stage4_frontier_staleness_still_flags_new_month_with_verified_stage3_lineage():
    prev_text = "WTI 원유 선물 3월물 매수 포지션에 15억 원 진입 완료. 딸깍."
    prev_hash = hashlib.sha256(prev_text.encode("utf-8")).hexdigest()

    result = detect_stage4_frontier_staleness(
        ep_num=6,
        blueprint={
            "summary": "WTI 6월물 15억 원 매수 지시를 다시 실행한다.",
            "_stage3_meta": {
                "source_prev_manuscript_ep": 5,
                "source_prev_manuscript_hash": prev_hash,
                "frontier_basis_version": "stage3-frontier-basis-v1",
            },
        },
        arc_data={"tactical_doc": "구버전 Arc에는 WTI 6월물 매수 지시와 가승인 서류가 남아 있다."},
        prev_manuscript_text=prev_text,
    )

    assert result["stale"] is True
    assert result["severity"] == "hard"
    assert result["evidence"]["frontier_wti_months"] == ["6"]
    assert result["evidence"]["stage3_lineage_matches_prev_manuscript"] is True


def test_detect_stage4_frontier_staleness_ignores_stable_business_registration_item_name():
    prev_text = "WTI 원유 선물 3월물 매수 포지션에 15억 원 진입 완료. 딸깍."
    prev_hash = hashlib.sha256(prev_text.encode("utf-8")).hexdigest()

    result = detect_stage4_frontier_staleness(
        ep_num=6,
        blueprint={
            "summary": "기존 WTI 3월물 롱 포지션을 점검한다.",
            "items": ["SW인베스트먼트 사업자 등록증 가승인 서류"],
            "_stage3_meta": {
                "source_prev_manuscript_ep": 5,
                "source_prev_manuscript_hash": prev_hash,
                "frontier_basis_version": "stage3-frontier-basis-v1",
            },
        },
        arc_data={},
        prev_manuscript_text=prev_text,
    )

    assert result["stale"] is False


def test_mark_downstream_frontier_requires_revalidation_marks_future_metadata_only():
    project = _Project()

    marked = mark_downstream_frontier_requires_revalidation(
        project=project,
        accepted_ep=5,
        arc_data={"ep_end": 7},
        manuscript_hash="abc123",
    )

    assert marked == [6, 7]
    assert project.saved[6]["summary"] == "future blueprint"
    assert project.saved[6]["_frontier_status"]["status"] == "requires_actual_manuscript_revalidation"
    assert project.saved[7]["_frontier_status"]["evidence"]["accepted_manuscript_hash"] == "abc123"


def test_mark_downstream_frontier_requires_revalidation_resolves_ep_count_arc_end():
    project = _Project()

    marked = mark_downstream_frontier_requires_revalidation(
        project=project,
        accepted_ep=5,
        arc_data={"ep_start": 5, "ep_count": 3},
        manuscript_hash="abc123",
    )

    assert marked == [6, 7]
    assert project.saved[7]["_frontier_status"]["detected_before_ep"] == 6
