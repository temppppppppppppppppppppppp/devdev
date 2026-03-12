"""
[NC-1] NumericConsistencyChecker 단위 테스트
"""

from unittest.mock import MagicMock

import pytest

from modules.core.numeric_consistency_checker import NumericConsistencyChecker

# ── Fixture ──────────────────────────────────────────────────────


@pytest.fixture
def checker():
    return NumericConsistencyChecker()


@pytest.fixture
def checker_with_ledger():
    fl = MagicMock()
    fl.get_numbers.return_value = {
        "자본금": {"value": 80, "unit": "억", "last_ep": 5},
        "포지션": {"value": 45, "unit": "억", "last_ep": 5},
        "수익": {"value": 10, "unit": "억", "last_ep": 5},
    }
    return NumericConsistencyChecker(fact_ledger=fl)


@pytest.fixture
def checker_with_db():
    db = MagicMock()
    return NumericConsistencyChecker(db=db)


# ── 1. 숫자 추출 테스트 ────────────────────────────────────────


class TestExtractNumbers:
    def test_extract_eok(self, checker):
        text = "잔고 131억 원이다."
        nums = checker._extract_all_numbers(text)
        assert any(abs(n.value_eok - 131.0) < 0.1 for n in nums)

    def test_extract_man(self, checker):
        text = "수익 5000만 원이다."
        nums = checker._extract_all_numbers(text)
        assert any(abs(n.value_eok - 0.5) < 0.01 for n in nums)

    def test_extract_compound(self, checker):
        text = "자본금 38억 3000만 원"
        nums = checker._extract_all_numbers(text)
        assert any(abs(n.value_eok - 38.3) < 0.1 for n in nums)

    def test_extract_percent(self, checker):
        text = "수익률 15%를 기록했다."
        nums = checker._extract_all_numbers(text)
        assert any(n.context_label == "퍼센트" and abs(n.value_eok - 15) < 0.1 for n in nums)

    def test_extract_leverage(self, checker):
        text = "3배 레버리지를 걸었다."
        nums = checker._extract_all_numbers(text)
        assert any(n.context_label == "레버리지" and abs(n.value_eok - 3) < 0.1 for n in nums)

    def test_dialogue_excluded(self, checker):
        text = '"상대방의 자본금 200억이래요" 라고 말했다. 잔고 80억이다.'
        nums = checker._extract_all_numbers(text)
        # 200억은 대사이므로 제외, 80억만 추출
        eok_values = [n.value_eok for n in nums if n.context_label != "퍼센트"]
        assert 200.0 not in eok_values
        assert any(abs(v - 80.0) < 0.1 for v in eok_values)

    def test_empty_text(self, checker):
        assert checker._extract_all_numbers("") == []
        assert checker._extract_all_numbers("아무 숫자도 없는 문장") == []

    def test_multiple_amounts(self, checker):
        text = "자본금 80억에서 수익 10억을 합치면 총 자산 90억이다."
        nums = checker._extract_all_numbers(text)
        eok_values = sorted([n.value_eok for n in nums if n.context_label != "퍼센트"])
        assert len(eok_values) >= 3


# ── 2. FactLedger 교차 검증 ─────────────────────────────────────


class TestFactLedgerCross:
    def test_match_no_warning(self, checker_with_ledger):
        text = "자본금 80억을 운용 중이다."
        warns = checker_with_ledger.check(text, ep_num=6)
        # 80억 == FactLedger 80억 → 경고 없음
        fl_warns = [w for w in warns if w["check"] == "FactLedger 교차"]
        assert len(fl_warns) == 0

    def test_mismatch_warning(self, checker_with_ledger):
        text = "포지션 60억을 유지하고 있다."
        warns = checker_with_ledger.check(text, ep_num=6)
        fl_warns = [w for w in warns if w["check"] == "FactLedger 교차"]
        # 60억 vs 45억 → MAJOR
        assert len(fl_warns) >= 1
        assert fl_warns[0]["severity"] == "MAJOR"

    def test_within_tolerance(self, checker_with_ledger):
        text = "수익 10억 2000만 원이다."
        warns = checker_with_ledger.check(text, ep_num=6)
        fl_warns = [w for w in warns if w["check"] == "FactLedger 교차"]
        # 10.2억 vs 10억 = 2% 차이 < 5% 허용
        assert len(fl_warns) == 0

    def test_no_ledger(self, checker):
        text = "자본금 80억이다."
        warns = checker.check(text, ep_num=6)
        fl_warns = [w for w in warns if w["check"] == "FactLedger 교차"]
        assert len(fl_warns) == 0

    def test_synonym_matching(self, checker_with_ledger):
        # "잔고" is synonym of "자본금"
        text = "잔고 60억이 남았다."
        warns = checker_with_ledger.check(text, ep_num=6)
        fl_warns = [w for w in warns if w["check"] == "FactLedger 교차"]
        # 60억 vs 자본금 80억 → MAJOR (synonyms match)
        assert len(fl_warns) >= 1


# ── 3. 산술 일관성 ──────────────────────────────────────────────


class TestArithmetic:
    def test_sum_correct(self, checker):
        text = "수익 10억 더하면 원금 80억 합계 총 90억이다."
        warns = checker.check(text, ep_num=3)
        arith_warns = [w for w in warns if w["check"] == "산술 일관성"]
        assert len(arith_warns) == 0

    def test_sum_incorrect(self, checker):
        text = "수익 10억 더하면 원금 80억 합계 총 100억이다."
        warns = checker.check(text, ep_num=3)
        arith_warns = [w for w in warns if w["check"] == "산술 일관성"]
        assert len(arith_warns) >= 1
        assert arith_warns[0]["severity"] == "MAJOR"


# ── 4. 직함 변경 ────────────────────────────────────────────────


class TestTitleConsistency:
    def test_no_change(self):
        db = MagicMock()
        db.get_manuscript.return_value = {"manuscript": "김과장 과장이 말했다."}
        checker = NumericConsistencyChecker(db=db)
        text = "김과장 과장이 다시 나타났다."
        warns = checker.check(text, ep_num=3)
        title_warns = [w for w in warns if w["check"] == "직함 변경"]
        assert len(title_warns) == 0

    def test_unauthorized_change(self):
        db = MagicMock()
        db.get_manuscript.return_value = {"manuscript": "박민수 팀장이 지시했다."}
        checker = NumericConsistencyChecker(db=db)
        text = "박민수 부장이 회의에 참석했다."
        warns = checker.check(text, ep_num=3)
        title_warns = [w for w in warns if w["check"] == "직함 변경"]
        assert len(title_warns) >= 1
        assert "무단 변경" in title_warns[0]["text"]

    def test_promotion_allowed(self):
        db = MagicMock()
        db.get_manuscript.return_value = {"manuscript": "이영수 대리가 보고했다."}
        checker = NumericConsistencyChecker(db=db)
        text = "이영수 과장이 승진 후 업무를 시작했다."
        warns = checker.check(text, ep_num=3)
        title_warns = [w for w in warns if w["check"] == "직함 변경"]
        assert len(title_warns) == 0

    def test_medical_promotion_allowed_within_same_domain(self):
        db = MagicMock()
        db.get_manuscript.return_value = {"manuscript": "김도윤 레지던트가 수술방으로 뛰어갔다."}
        checker = NumericConsistencyChecker(db=db)
        text = "김도윤 전문의가 첫 집도를 맡았다."
        warns = checker.check(text, ep_num=3)
        title_warns = [w for w in warns if w["check"] == "직함 변경"]
        assert len(title_warns) == 0

    def test_cross_domain_title_change_is_not_treated_as_promotion(self):
        db = MagicMock()
        db.get_manuscript.return_value = {"manuscript": "김도윤 레지던트가 수술방으로 뛰어갔다."}
        checker = NumericConsistencyChecker(db=db)
        text = "김도윤 박사가 연구실로 향했다."
        warns = checker.check(text, ep_num=3)
        title_warns = [w for w in warns if w["check"] == "직함 변경"]
        assert len(title_warns) >= 1
        assert "무단 변경" in title_warns[0]["text"]

    def test_no_db(self, checker):
        text = "박민수 부장이 회의에 참석했다."
        warns = checker.check(text, ep_num=3)
        title_warns = [w for w in warns if w["check"] == "직함 변경"]
        assert len(title_warns) == 0


# ── 5. "처음" 이벤트 모순 ───────────────────────────────────────


class TestEventOrdering:
    def test_first_time_contradiction(self):
        db = MagicMock()
        db.get_episode_bible.return_value = {
            "state_changes": "주식 거래 성공",
            "reveals": [],
            "new_items": [],
            "relationship_changes": [],
        }
        db.get_manuscript.return_value = {"manuscript": "주식 거래를 완료했다. 거래 성공이다."}
        checker = NumericConsistencyChecker(db=db)
        text = "처음 해보는 주식 거래에 긴장했다."
        warns = checker.check(text, ep_num=5)
        event_warns = [w for w in warns if w["check"] == "이벤트 순서"]
        assert len(event_warns) >= 1
        assert event_warns[0]["severity"] == "MINOR"

    def test_genuine_first(self):
        db = MagicMock()
        db.get_episode_bible.return_value = {
            "state_changes": "거래 성공",
            "reveals": [],
            "new_items": [],
            "relationship_changes": [],
        }
        db.get_manuscript.return_value = {"manuscript": "거래가 성사되었다."}
        checker = NumericConsistencyChecker(db=db)
        text = "처음 만난 해외 투자자가 인상적이었다."
        warns = checker.check(text, ep_num=5)
        event_warns = [w for w in warns if w["check"] == "이벤트 순서"]
        # "해외 투자자" 키워드가 이전에 없으므로 경고 없음
        assert len(event_warns) == 0

    def test_ep1_skip(self, checker):
        text = "처음 만난 사람이다."
        warns = checker.check(text, ep_num=1)
        event_warns = [w for w in warns if w["check"] == "이벤트 순서"]
        assert len(event_warns) == 0


# ── 6. 통합 테스트 ──────────────────────────────────────────────


class TestIntegration:
    def test_check_returns_list(self, checker):
        result = checker.check("잔고 80억이다.", ep_num=3)
        assert isinstance(result, list)

    def test_empty_manuscript(self, checker):
        assert checker.check("", ep_num=3) == []
        assert checker.check("   ", ep_num=3) == []

    def test_warning_format(self, checker_with_ledger):
        text = "포지션 60억을 유지 중이다."
        warns = checker_with_ledger.check(text, ep_num=6)
        for w in warns:
            assert "check" in w
            assert "severity" in w
            assert "text" in w
            assert w["severity"] in ("MAJOR", "MINOR")

    def test_max_warnings_not_exceeded(self, checker_with_ledger):
        # 많은 숫자가 있어도 체크 자체는 제한 없이 모두 반환
        text = " ".join(f"자본금 {i}억" for i in range(1, 50))
        warns = checker_with_ledger.check(text, ep_num=6)
        assert isinstance(warns, list)


# ── 6-1. [NC-2] NPC 이름 정규화(괄호 접미사) ─────────────────────


class TestNpcNameCollisionNormalization:
    def test_parenthesized_name_is_normalized_for_collision(self):
        world_state = MagicMock()
        world_state.npcs = {
            "npc_1": {"name": "박성호", "role": "PB"},
            "npc_2": {"name": "박성호 (담당 PB)", "role": "PB"},
        }
        checker = NumericConsistencyChecker(world_state=world_state)

        warns = checker.check("박성호가 보고서를 넘겼다.", ep_num=4)
        name_warns = [w for w in warns if w["check"] == "NPC 동명이인"]
        assert len(name_warns) >= 1
        assert "박성호" in name_warns[0]["text"]


# ── 7. [NC-2] 퍼센트 구성 검증 ───────────────────────────────────


class TestPercentComposition:
    def test_percent_mismatch(self):
        fl = MagicMock()
        fl.get_numbers.return_value = {
            "평가금액": {"value": 13, "unit": "억", "last_ep": 5},
            "증거금": {"value": 10, "unit": "억", "last_ep": 5},
        }
        checker = NumericConsistencyChecker(fact_ledger=fl)
        text = "증거금 유지율 150%를 유지하고 있다."
        warns = checker.check(text, ep_num=6)
        pct_warns = [w for w in warns if w["check"] == "퍼센트 구성"]
        # 13/10 = 130%, 원고 150% → 불일치
        assert len(pct_warns) >= 1
        assert pct_warns[0]["severity"] == "MAJOR"

    def test_percent_correct(self):
        fl = MagicMock()
        fl.get_numbers.return_value = {
            "평가금액": {"value": 15, "unit": "억", "last_ep": 5},
            "증거금": {"value": 10, "unit": "억", "last_ep": 5},
        }
        checker = NumericConsistencyChecker(fact_ledger=fl)
        text = "증거금 유지율 150%를 유지하고 있다."
        warns = checker.check(text, ep_num=6)
        pct_warns = [w for w in warns if w["check"] == "퍼센트 구성"]
        assert len(pct_warns) == 0

    def test_percent_skip_no_ledger_data(self):
        fl = MagicMock()
        fl.get_numbers.return_value = {
            "자본금": {"value": 80, "unit": "억", "last_ep": 5},
        }
        checker = NumericConsistencyChecker(fact_ledger=fl)
        text = "증거금 유지율 150%를 유지하고 있다."
        warns = checker.check(text, ep_num=6)
        pct_warns = [w for w in warns if w["check"] == "퍼센트 구성"]
        # 분자/분모 데이터 없으면 SKIP
        assert len(pct_warns) == 0


# ── 8. [NC-2] NPC 동명이인 감지 ──────────────────────────────────


class TestNpcNameCollision:
    def test_duplicate_name_detected(self):
        ws = MagicMock()
        ws.npcs = {
            "npc1": {"name": "박성호", "role": "PB"},
            "npc2": {"name": "박성호", "role": "증권사 직원"},
        }
        checker = NumericConsistencyChecker(world_state=ws)
        text = "박성호가 전화를 걸었다."
        warns = checker.check(text, ep_num=3)
        name_warns = [w for w in warns if w["check"] == "NPC 동명이인"]
        assert len(name_warns) >= 1
        assert "동명이인" in name_warns[0]["text"]

    def test_single_npc_no_warning(self):
        ws = MagicMock()
        ws.npcs = {
            "npc1": {"name": "김철수", "role": "팀장"},
        }
        checker = NumericConsistencyChecker(world_state=ws)
        text = "김철수 팀장이 보고했다."
        warns = checker.check(text, ep_num=3)
        name_warns = [w for w in warns if w["check"] == "NPC 동명이인"]
        assert len(name_warns) == 0

    def test_no_world_state_skip(self, checker):
        text = "박성호가 나타났다."
        warns = checker.check(text, ep_num=3)
        name_warns = [w for w in warns if w["check"] == "NPC 동명이인"]
        assert len(name_warns) == 0


# ── 9. [NC-2] 도입부 유사도 ──────────────────────────────────────


class TestOpeningSimilarity:
    def test_similar_opening_detected(self, checker):
        prev = "아침 햇살이 사무실 창문을 비추었다. 김도현은 책상 앞에 앉아 모니터를 바라보았다. " * 10
        curr = "아침 햇살이 사무실 창문을 비추었다. 김도현은 책상 앞에 앉아 커피를 마셨다. " * 10
        warns = checker.check(curr, ep_num=5, prev_manuscript=prev)
        opening_warns = [w for w in warns if w["check"] == "도입부 유사도"]
        assert len(opening_warns) >= 1
        assert opening_warns[0]["severity"] == "MINOR"

    def test_different_opening_ok(self, checker):
        prev = "밤하늘의 별이 빛나고 있었다. 이준영은 테라스에서 맥주를 마셨다. 전화가 울렸다." * 5
        curr = "아침 햇살이 사무실을 비추었다. 김도현은 모니터를 켰다. 새로운 하루가 시작되었다." * 5
        warns = checker.check(curr, ep_num=5, prev_manuscript=prev)
        opening_warns = [w for w in warns if w["check"] == "도입부 유사도"]
        assert len(opening_warns) == 0

    def test_no_prev_manuscript_skip(self, checker):
        text = "아침 햇살이 사무실 창문을 비추었다."
        warns = checker.check(text, ep_num=5)
        opening_warns = [w for w in warns if w["check"] == "도입부 유사도"]
        assert len(opening_warns) == 0


# ── [TF-21-06] _check_leverage_return_pct 직접 테스트 ────────────────────


class TestLeverageReturnPct:
    def test_correct_leverage_no_warning(self, checker):
        """100달러에서 110달러 × 10배 → 수익률 100% (정확) — 경고 없음.
        마침표 없이 단일 문장으로 구성 (regex [^.。\\n] 제약 회피).
        """
        text = "100달러에서 110달러로 올라 10배 레버리지로 수익률이 100%가 되었다"
        warns = checker._check_leverage_return_pct(text)
        assert len(warns) == 0

    def test_wrong_leverage_triggers_warning(self, checker):
        """100달러에서 110달러 × 10배 → 수익률 500% 주장 (실제 100%) — 경고."""
        text = "100달러에서 110달러로 올라 10배 레버리지로 수익률이 500%가 되었다"
        warns = checker._check_leverage_return_pct(text)
        assert len(warns) >= 1
        assert warns[0]["severity"] == "MAJOR"
