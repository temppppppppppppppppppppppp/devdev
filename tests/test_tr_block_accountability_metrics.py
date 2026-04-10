from __future__ import annotations

import json
import sys
from pathlib import Path

import scripts.audit_bi_5pass as audit_script
from scripts.tr_batch_harness import compute_treatment_metrics, validate_candidate


def _build_block(
    block_no: int,
    *,
    solution: str,
    stakes: str,
    recognition_from: str = "",
    suspicion_from: str = "",
    callback: list[str] | None = None,
    foreshadow: list[str] | None = None,
    opponent_name: str | None = None,
    section_rotation: str | None = None,
    weakness: str | None = None,
    capital_after: str | None = None,
    capital_before: str | None = None,
    macro_battlefield: str | None = None,
    public_signboard_event: str = "없음",
    representative_reevaluation: str = "없음",
    next_battlefield_ticket: str = "없음",
) -> dict:
    before = capital_before or f"{99 + block_no}억"
    after = capital_after or f"{100 + block_no}억"
    return {
        "block_id": f"Block {block_no}",
        "title": f"테스트 장면 {block_no}",
        "content": {
            "context": (
                "자산이 권력으로 바뀌는 과정과 직전 비용의 잔향이 어떻게 남는지, "
                "실무자와 계약선이 어떤 식으로 움직였는지를 구체적으로 묘사한다. "
                "이 설명은 treatment 책임을 테스트하기 위한 충분한 분량을 가진다."
            ),
            "event_villain": (
                "적대자는 서류, 사람, 시간 압박 중 하나를 흔들며 주인공이 같은 방법을 "
                "반복하지 못하도록 압박한다. 이 사건은 다음 callback이 붙을 수 있게 설계한다."
            ),
            "solution": solution,
            "reward": (
                "이번 결과로 단순 수익이 아니라 승인권, 신용, 정보 우위 중 최소 하나가 "
                "새로 이동했다는 사실을 명시한다. 그래서 reward가 context 재진술로 끝나지 않는다."
            ),
        },
        "stakes": stakes,
        "power_shift": {
            "protagonist": "주인공이 승인선과 발언권을 조금 더 먼저 잡는다",
            "antagonist": "적대자는 의사결정 주도권 일부를 잃는다",
        },
        "relationship_delta": [
            {
                "target": f"실무자 {block_no}",
                "before": "주인공을 관찰만 한다",
                "after": "주인공에게 정보를 넘길지 계산한다",
            },
            {
                "target": f"파트너 {block_no}",
                "before": "주인공을 시험한다",
                "after": "다음 계약을 주인공 쪽으로 기울인다",
            },
        ],
        "foreshadow": foreshadow or [],
        "callback": callback or [],
        "emotional_beat": {"type": "resolve" if block_no % 2 else "pressure", "intensity": 6},
        "location": {
            "place": f"테스트 장소 {block_no}",
            "type": "사업 거점",
            "macro_battlefield": macro_battlefield or f"오프닝 전장 {((block_no - 1) // 3) + 1}",
        },
        "genre_ext": {
            "capital_before": before,
            "capital_after": after,
            "capital_delta": "+1억",
            "deal_type": f"딜 타입 {block_no}",
            "method": f"방법 {block_no}",
            "business_sector": f"섹터 {block_no}",
            "section_rotation": section_rotation or f"책임 구간 {block_no}",
            "opponent": {
                "name": opponent_name or f"상대 {block_no}",
                "type": "경쟁 세력",
                "weakness_exploited": weakness or f"약점 {block_no}",
            },
            "opening_progression": {
                "public_signboard_event": public_signboard_event,
                "representative_reevaluation": representative_reevaluation,
                "next_battlefield_ticket": next_battlefield_ticket,
            },
            "block_cider": {
                "has_cider": True,
                "receipt_type": "재평가 + 권한 이동",
                "receipt_line": "이번 장면 안에서 승인권과 질문권 일부가 주인공 쪽으로 기울며 same-block 사이다가 지급된다.",
                "pain_only_exit": False,
            },
        },
        "regression_ext": {
            "is_regressor": True,
            "regression_type": "회귀",
            "regression_hint": {
                "slip_up": "지나치게 정확한 타이밍 언급",
                "recognition_from": recognition_from,
                "suspicion_from": suspicion_from,
            },
            "death_flag": {
                "avoided": "파산 직전 유동성 경색",
                "method": "현금 흐름 우선순위 재배치",
            },
        },
    }


def _make_positive_blocks() -> list[dict]:
    solutions = [
        "감사 로그를 먼저 묶어 매수 근거를 숨긴 뒤, PB가 남긴 손절 표식을 역으로 따라가며 매입 시점을 끊었다.",
        "그는 대기 자금을 둘로 쪼갰다. 하나는 장전 호가에, 다른 하나는 마감 직전 협상 카드에 걸어 상대의 예측을 비틀었다.",
        "현금흐름 표를 뒤집어 보여 주면서도 서명을 늦췄다; 상대가 먼저 공백을 메우는 순간 그 문장을 증거로 고정했다.",
        "주인공은 운영팀을 먼저 움직이지 않았다. 대신 조용히 승인선을 바꿔 두고, 마지막 결재자만 보이는 리스크를 노출했다.",
        "거래 자체보다 회수 순서를 바꿨다: 손실처럼 보이는 비용을 먼저 떠안고, 그 대가로 정산권과 질문권을 같이 가져왔다.",
        "상대가 숫자만 본다는 점을 이용해 사람을 움직였다. 현장 기록, 배송 지연, 계약 단서 세 개를 겹쳐 반격 타이밍을 만들었다.",
        "그는 매수 대신 보증을 요구했다. 그러자 상대는 안전하다고 믿었고, 그 빈틈에서 주인공이 주도권을 가져가는 구조가 완성됐다.",
        "이번 블록에서는 익절보다 정보 차단이 중요했다. 주인공은 이익 일부를 포기하고, 추적 가능한 흔적부터 먼저 지웠다.",
        "주인공은 합의서를 바로 닫지 않고 질문 하나를 남겼다. 그 질문이 상대 진영 내부 갈등을 바깥으로 끌어내는 스위치가 됐다.",
        "마지막에는 승리 선언 대신 책임 배분을 고정했다. 그래서 이후 후폭풍이 와도 누가 빚을 지고 누가 열쇠를 쥐는지가 남는다.",
    ]
    stakes_list = [
        "이번 블록을 놓치면 PB가 주인공의 비정상적으로 정확한 매매를 내부 리스크팀에 넘기고, 다음 진입선이 통째로 닫힌다.",
        "자금을 나눠 넣는 순간 하나라도 엇나가면 현금이 묶이고, 상대는 주인공이 시간을 잃는 동안 가격표를 먼저 다시 쓴다.",
        "서명을 늦춘 판단이 실패하면 공백은 주인공 책임이 되고, 다음 블록에서 확보할 질문권과 신뢰 잔고가 동시에 증발한다.",
        "승인선을 미리 바꿔 둔 사실이 들키면 주인공은 정보 우위 대신 월권 프레임을 뒤집어쓰고, 협상장은 적의 무대가 된다.",
        "가짜 손실처럼 보이는 선투입이 통하지 않으면 정산권도 못 얻고, 투자금을 잃은 채 왜 손해를 봤는지 설명해야 한다.",
        "사람을 먼저 움직인 전략이 실패하면 현장 실무자와의 신용이 끊기고, 다음 block의 회수 장치가 시작도 못 하고 무너진다.",
        "보증 요구가 안전한 척 보이지 않으면 상대는 즉시 가격을 올리고, 주인공은 주도권 없이 자금만 묶인 채 퇴로를 잃는다.",
        "이익 일부를 포기한 선택이 늦으면 흔적은 그대로 남고, 후속 조사에서 주인공의 정체성과 전략이 동시에 드러날 수 있다.",
        "질문 하나를 남긴 선택이 비어 보이면 상대는 시간을 벌고, 내부 갈등 대신 주인공의 우유부단함만 기록으로 남는다.",
        "책임 배분을 고정하지 못하면 승리 뒤 거버넌스가 다시 흐려지고, 행복하게 끝난 척한 엔딩이 곧바로 권력 공백으로 뒤집힌다.",
    ]

    blocks = []
    for idx in range(1, 11):
        foreshadow = []
        callback = []
        if idx < 10:
            foreshadow = ["정산 질문 하나가 다음 승인선 공백을 찌른다"]
        if idx > 1:
            callback = ["앞서 던진 정산 질문이 승인선 공백을 찔렀다"]
        recognition_from = f"PB {idx}가 주인공의 판단력을 인정하고 다음 거래를 먼저 제안한다" if 3 <= idx <= 8 else ""
        macro_battlefield = "자금 포지션 축" if idx <= 3 else "승인선 전환 축" if idx <= 6 else "회수 고정 축"
        blocks.append(
            _build_block(
                idx,
                solution=solutions[idx - 1],
                stakes=stakes_list[idx - 1],
                recognition_from=recognition_from,
                foreshadow=foreshadow,
                callback=callback,
                macro_battlefield=macro_battlefield,
                public_signboard_event="증권가 메인 라인에 주인공 이름이 처음 오르내른다" if idx == 3 else "없음",
                representative_reevaluation="PB 본부장이 주인공 판단을 공식적으로 인정한다" if idx == 4 else "없음",
                next_battlefield_ticket="구조조정 실무 회의 입장권이 열린다" if idx == 5 else "없음",
            )
        )
    return blocks


def _make_repetitive_blocks() -> list[dict]:
    blocks = []
    for idx in range(1, 11):
        foreshadow = []
        callback = []
        if idx < 10:
            foreshadow = ["세무 질문 하나가 위임 계약의 빈틈을 찌른다"]
        if idx > 1:
            callback = ["앞서 던진 세무 질문이 위임 계약의 빈틈을 찔렀다"]
        blocks.append(
            _build_block(
                idx,
                solution=(
                    f"주인공은 상대 {idx}의 보고서를 다시 묶어 {100 + idx}억 손실처럼 보이게 만들고, "
                    f"실제론 위임 계약과 정산권을 동시에 챙겼다."
                ),
                stakes=(
                    f"이번 블록을 놓치면 상대 {idx}가 {100 + idx}억 손실 프레임을 뒤집어씌우고, "
                    f"위임 계약과 정산권을 한 번에 빼앗는다."
                ),
                recognition_from="",
                foreshadow=foreshadow,
                callback=callback,
                opponent_name=f"상대 {idx}",
                section_rotation=f"반복 감시 {idx}",
                weakness=f"서류 집착 {idx}",
                macro_battlefield="반복 감시 축",
                public_signboard_event="언론이 주인공의 이름을 메인 사례로 올린다" if idx == 9 else "없음",
                representative_reevaluation="대표가 뒤늦게 주인공 판단을 공식적으로 인정한다" if idx == 9 else "없음",
                next_battlefield_ticket="다음 협상장 직행권이 열린다" if idx == 10 else "없음",
            )
        )
    return blocks


def _write_json(path: Path, payload: dict | list) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _build_phase0_payload() -> dict:
    return {
        "project": {"title_ko": "테스트 프로젝트"},
        "protagonist": {"name": "주인공"},
        "setting": {"starter_company": {"name": "테스트컴퍼니"}},
        "phase0_design": {"npc_timeline": [{"name": "조력자A"}, {"name": "조력자B"}]},
    }


def _build_draft_payload() -> list[dict]:
    payload = []
    for idx in range(1, 71):
        payload.append(
            {
                "title": f"에피소드 {idx}",
                "genre_ext": {"capital_after": f"{idx}억"},
            }
        )
    return payload


def _build_bi_payload() -> dict:
    roadmap = [{"title": f"에피소드 {idx}"} for idx in range(1, 71)]
    portfolio_history = [{"block": idx, "total_assets": f"{idx}억"} for idx in range(1, 71)]
    return {
        "MasterBible": {
            "ProjectData": {
                "MetaInfo": {
                    "title": "테스트 프로젝트",
                    "grand_objective": "최종 지배력 확보",
                    "genre_archetype": "investment",
                    "logline": "테스트용 로그라인",
                },
                "CoreIdentity": {
                    "protagonist": "주인공",
                    "protagonist_faction": "주인공 진영",
                    "edge": "현금 흐름을 읽는 힘",
                    "desire": "지배력 확보",
                    "crisis": "승계 실패",
                },
            },
            "FinanceHUD": {
                "Protagonist": {
                    "actual_truth": {
                        "name": "주인공",
                        "rank": "대표",
                        "current_objective": "현금 흐름 유지",
                        "final_goal": "최종 지배력 확보",
                        "financial_status": {"company": "테스트컴퍼니"},
                        "portfolio_history": portfolio_history,
                    }
                }
            },
            "WorldState": {
                "CurrentEra": "현대",
                "CurrentLocation": "서울",
            },
            "AssetLibrary": {
                "KeyNPCs": [
                    {"name": "주인공"},
                    {"name": "조력자A"},
                    {"name": "조력자B"},
                ]
            },
            "plot_roadmap": roadmap,
        }
    }


def _make_audit_metrics() -> dict:
    return {
        "production_density_gate": False,
        "avg_bundle_chars": 640.0,
        "avg_solution_chars": 170.0,
        "foreshadow_total": 20,
        "callback_total": 8,
        "callback_ratio": 0.4,
        "unresolved_foreshadow_count": 9,
        "opponent_unique": 12,
        "top_opponent_repetition": 2,
        "top_opponent_share": 2.9,
        "top_weakness_repetition": 1,
        "deal_top_repetition": 2,
        "method_top_repetition": 2,
        "solution_tail20_top_repetition": 1,
        "one_sentence_like_solution_blocks": 0,
        "business_sector_missing": 0,
        "section_rotation_missing": 4,
        "critical_thin_blocks": [],
        "thin_blocks": [63],
        "short_stakes_blocks": [66, 67, 68],
        "recognition_signal_blocks": 1,
        "max_recognition_gap_streak": 22,
        "late_blank_opponent_blocks": [65, 66],
        "endgame_low_stakes_blocks": [66, 67, 68],
        "normalized_solution_stakes_repeat_max": 4,
        "is_regressor_treatment": True,
        "hard_gate_checks": {
            "critical_thin_blocks_zero": True,
            "thin_blocks_ratio_ok": True,
            "late_thin_blocks_zero": False,
            "short_stakes_blocks_total_ok": False,
            "endgame_low_stakes_zero": False,
            "callback_ratio_ok": False,
            "unresolved_foreshadow_count_ok": False,
            "section_rotation_present": False,
            "late_blank_opponent_ok": False,
            "normalized_solution_stakes_repeat_ok": False,
            "regressor_recognition_count_ok": False,
            "regressor_recognition_gap_ok": False,
        },
        "hard_gate_failures": [
            "late_thin_blocks_zero",
            "callback_ratio_ok",
            "section_rotation_present",
            "regressor_recognition_count_ok",
        ],
        "window_10_opponent_unique_counts": [5, 4, 3, 2, 2, 2, 1],
        "pattern_feedback_snapshot": {
            "top_opponents": [("상대A", 2)],
            "top_weaknesses": [("질문 회피", 1)],
            "solution_pattern_warnings": [],
            "forbidden_pattern_reuse": [],
            "structural_gate_failures": [
                "callback_ratio_ok",
                "section_rotation_present",
            ],
        },
    }


def test_compute_treatment_metrics_flags_golden_canary_structural_gaps():
    sample_path = next(Path("treatments").glob("*골든*카나리아*.json"))
    payload = json.loads(sample_path.read_text(encoding="utf-8"))

    metrics = compute_treatment_metrics(payload)

    assert metrics["avg_bundle_chars"] > 350
    assert metrics["production_density_gate"] is False
    assert metrics["callback_ratio"] < 0.7
    assert metrics["recognition_signal_blocks"] > 0
    assert metrics["unresolved_foreshadow_count"] > 0
    assert metrics["diegetic_meta_ref_count"] > 0
    assert "unresolved_foreshadow_count_ok" in metrics["hard_gate_failures"]
    assert "diegetic_meta_ref_zero" in metrics["hard_gate_failures"]


def test_compute_treatment_metrics_passes_positive_structural_fixture():
    metrics = compute_treatment_metrics(_make_positive_blocks())

    assert metrics["production_density_gate"] is True
    assert metrics["callback_ratio"] >= 0.65
    assert metrics["unresolved_foreshadow_count"] == 0
    assert metrics["recognition_signal_blocks"] >= 6
    assert metrics["section_rotation_missing"] == 0
    assert metrics["endgame_low_stakes_blocks"] == []
    assert metrics["normalized_solution_stakes_repeat_max"] <= 3
    assert metrics["hard_gate_failures"] == []


def test_compute_treatment_metrics_rejects_dense_but_repetitive_solution_stakes():
    metrics = compute_treatment_metrics(_make_repetitive_blocks())

    assert metrics["avg_bundle_chars"] > 350
    assert metrics["normalized_solution_stakes_repeat_max"] > 3
    assert metrics["production_density_gate"] is False
    assert "normalized_solution_stakes_repeat_ok" in metrics["hard_gate_failures"]


def test_compute_treatment_metrics_rejects_opening_macro_battlefield_overstay():
    metrics = compute_treatment_metrics(_make_repetitive_blocks())

    assert "opening_reader_earning_signal_by6" in metrics["hard_gate_failures"]
    assert "opening_macro_progression_ok" in metrics["hard_gate_failures"]
    assert metrics["opening_main_macro_battlefield_overstay"] is True
    assert metrics["first_reader_earning_signal_block"] == 9


def test_validate_candidate_requires_opening_contract_fields():
    block = _build_block(
        1,
        solution="주인공은 승인선의 빈칸을 먼저 읽고 질문 순서를 바꿔 상대의 계산을 흔든다.",
        stakes="이번 장면을 놓치면 승인권과 질문권을 동시에 잃고 다음 전장 입구가 닫힌다.",
    )
    block["location"].pop("macro_battlefield", None)
    block["genre_ext"].pop("opening_progression", None)

    findings, _ = validate_candidate(
        candidate_blocks=[block],
        history_blocks=[],
        start=1,
        batch_size=1,
        roadmap_blocks=None,
        autofix=False,
    )

    rules = {item.rule for item in findings}
    assert "PACE-001" in rules
    assert "PACE-002" in rules


def test_audit_bi_5pass_blocks_bi_handoff_when_source_tr_gate_fails(monkeypatch, temp_dir):
    phase0_path = temp_dir / "phase0.json"
    draft_path = temp_dir / "draft.json"
    bi_path = temp_dir / "bi.json"
    report_path = temp_dir / "report.md"
    _write_json(phase0_path, _build_phase0_payload())
    _write_json(draft_path, _build_draft_payload())
    _write_json(bi_path, _build_bi_payload())

    monkeypatch.setattr(audit_script, "compute_treatment_metrics", lambda _: _make_audit_metrics())
    monkeypatch.setattr(audit_script, "validate_treatment_structure", lambda _: (True, [], []))
    monkeypatch.setattr(audit_script, "validate_bible_structure", lambda _: (True, [], []))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "audit_bi_5pass.py",
            "--phase0",
            str(phase0_path),
            "--draft",
            str(draft_path),
            "--bi",
            str(bi_path),
            "--report",
            str(report_path),
        ],
    )

    exit_code = audit_script.main()
    report_text = report_path.read_text(encoding="utf-8")

    assert exit_code == 1
    assert "- raw_pair_canonical_contract: FAIL" in report_text
    assert "- normalized_pair_canonical_view: FAIL" in report_text
    assert "- source_tr_density_gate: FAIL" in report_text
    assert "- source_tr_callback_gate: FAIL" in report_text
    assert "- source_tr_section_rotation_gate: FAIL" in report_text
    assert "- source_tr_regressor_recognition_count_gate: FAIL" in report_text
    assert "- hard_gate_failures: ['late_thin_blocks_zero', 'callback_ratio_ok', 'section_rotation_present', 'regressor_recognition_count_ok']" in report_text
