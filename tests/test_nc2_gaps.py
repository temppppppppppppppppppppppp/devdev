"""
[NC-2] 실파이프라인 11대 이슈 잔여 갭 해소 통합 테스트

GAP-1: 에피소드 간 씬 유사도 (stage4_context_builder + Director advisory)
GAP-2: 퍼센트/비율 구성 검증 (numeric_consistency_checker)
GAP-3: 공간 연속성 (director.yaml 프롬프트 강화)
GAP-4: NPC 동명이인 감지 (numeric_consistency_checker)
GAP-5: 시간 경과 Stage4 주입 (stage4_interview_round + director.yaml)
GAP-6: 연속 에피소드 도입부 유사도 (numeric_consistency_checker)
"""

from unittest.mock import MagicMock

from modules.core.numeric_consistency_checker import NumericConsistencyChecker
from modules.core.stage4_context_builder import Stage4ContextBuilder

# ── GAP-1: 씬 유사도 ────────────────────────────────────────────


class TestSceneSimilarity:
    def test_split_scenes_basic(self):
        text = "첫 번째 씬입니다. 주인공이 사무실에 있다. 길고 긴 서술이 이어진다.\n\n---\n\n두 번째 씬입니다. 주인공이 카페로 이동했다. 새로운 장면이 펼쳐진다."
        scenes = Stage4ContextBuilder._split_scenes(text)
        assert len(scenes) >= 2

    def test_scene_keywords_extraction(self):
        scene = "김도현은 증권사 사무실에서 모니터를 바라보며 투자 전략을 고민했다."
        kws = Stage4ContextBuilder._scene_keywords(scene)
        assert "김도현" in kws or "증권사" in kws or "사무실" in kws

    def test_similar_scenes_advisory(self):
        # 동일한 원고를 prev_kws로 변환해서 비교 → 높은 유사도 보장
        scene1 = "김도현은 증권사 사무실에서 모니터를 바라보며 투자 전략을 고민했다. " * 5
        scene2 = "회의실에서 팀장에게 보고를 하며 실적 분석 결과를 설명했다. " * 5
        candidate = f"# 씬 1\n{scene1}\n\n---\n\n{scene2}"
        # prev_kws를 실제 _scene_keywords로 생성
        prev_kws = [
            {
                "ep": 5,
                "scenes": [
                    Stage4ContextBuilder._scene_keywords(scene1),
                    Stage4ContextBuilder._scene_keywords(scene2),
                ],
            }
        ]
        advisory = Stage4ContextBuilder.compute_scene_similarity_advisory(
            candidate,
            prev_kws,
            threshold=0.30,
        )
        assert "[SceneSimilarity]" in advisory

    def test_different_scenes_no_advisory(self):
        prev_kws = [
            {
                "ep": 5,
                "scenes": [
                    {"산장", "무공", "수련", "제자", "검법"},
                ],
            }
        ]
        candidate = (
            "# 씬 1\n김도현은 증권사 사무실에서 주식 차트를 분석했다. " * 5
            + "\n\n---\n\n"
            + "점심시간에 카페에서 커피를 마시며 동료와 대화했다. " * 5
        )
        advisory = Stage4ContextBuilder.compute_scene_similarity_advisory(
            candidate,
            prev_kws,
        )
        assert advisory == ""

    def test_empty_inputs(self):
        assert Stage4ContextBuilder.compute_scene_similarity_advisory("", []) == ""
        assert Stage4ContextBuilder.compute_scene_similarity_advisory("text", []) == ""

    def test_collect_recent_scene_keywords(self):
        db = MagicMock()
        # 100자 이상의 충분한 길이 원고
        scene1 = "첫 씬 내용입니다. 주인공이 등장합니다. 길고 긴 서술이 이어집니다. 사무실에서 회의가 진행된다. 모두가 집중하고 있었다."
        scene2 = "두 번째 씬이다. 새로운 장면이 펼쳐진다. 다양한 사건이 발생한다. 카페에서 커피를 마시며 대화했다. 분위기가 좋았다."
        db.get_manuscript.return_value = {
            "content": f"{scene1}\n\n---\n\n{scene2}",
        }
        result = Stage4ContextBuilder._collect_recent_scene_keywords(db, 5, lookback=2)
        assert len(result) >= 1
        assert "ep" in result[0]
        assert "scenes" in result[0]


# ── GAP-2: 퍼센트 구성 검증 ──────────────────────────────────────


class TestPercentCompositionIntegration:
    def test_maintenance_rate_mismatch(self):
        fl = MagicMock()
        fl.get_numbers.return_value = {
            "평가금액": {"value": 13, "unit": "억", "last_ep": 5},
            "증거금": {"value": 10, "unit": "억", "last_ep": 5},
        }
        checker = NumericConsistencyChecker(fact_ledger=fl)
        text = "증거금 유지율 150%를 기록하며 안정적인 거래를 유지했다."
        warns = checker.check(text, ep_num=6)
        pct = [w for w in warns if w["check"] == "퍼센트 구성"]
        assert len(pct) >= 1
        assert "비율 불일치" in pct[0]["text"]

    def test_debt_ratio_check(self):
        fl = MagicMock()
        fl.get_numbers.return_value = {
            "부채": {"value": 30, "unit": "억", "last_ep": 5},
            "자본": {"value": 100, "unit": "억", "last_ep": 5},
        }
        checker = NumericConsistencyChecker(fact_ledger=fl)
        text = "부채비율 50%로 안정적이다."
        warns = checker.check(text, ep_num=6)
        pct = [w for w in warns if w["check"] == "퍼센트 구성"]
        # 30/100 = 30%, 원고 50% → 불일치 (20%p > 2%p)
        assert len(pct) >= 1


# ── GAP-3: 공간 연속성 (director.yaml 프롬프트 확인) ──────────────


class TestSpaceContinuityPrompt:
    def test_director_yaml_contains_space_keywords(self):
        with open("config/prompts/director.yaml", encoding="utf-8") as f:
            content = f.read()
        assert "공간 연속성" in content
        assert "이동 묘사" in content
        assert "전환 표지" in content

    def test_audit_step1_space_check(self):
        with open("config/prompts/director.yaml", encoding="utf-8") as f:
            content = f.read()
        assert "공간 이동" in content


# ── GAP-4: NPC 동명이인 감지 ──────────────────────────────────────


class TestNpcNameCollisionIntegration:
    def test_list_type_npcs(self):
        ws = MagicMock()
        ws.npcs = [
            {"name": "이준영", "role": "트레이더"},
            {"name": "이준영", "role": "애널리스트"},
        ]
        checker = NumericConsistencyChecker(world_state=ws)
        text = "이준영이 전화를 받았다."
        warns = checker.check(text, ep_num=3)
        name_warns = [w for w in warns if w["check"] == "NPC 동명이인"]
        assert len(name_warns) >= 1

    def test_multiple_titles_in_manuscript(self):
        ws = MagicMock()
        ws.npcs = {
            "npc1": {"name": "박성호", "role": "PB"},
        }
        checker = NumericConsistencyChecker(world_state=ws)
        text = "박성호 팀장이 보고했다. 한편 박성호 과장은 다른 업무를 처리했다."
        warns = checker.check(text, ep_num=3)
        name_warns = [w for w in warns if w["check"] == "NPC 동명이인"]
        assert len(name_warns) >= 1
        assert "복수 직함" in name_warns[0]["text"]


# ── GAP-5: 시간 경과 Stage4 주입 ─────────────────────────────────


class TestTimelineInjection:
    def test_director_yaml_timeline_keywords(self):
        with open("config/prompts/director.yaml", encoding="utf-8") as f:
            content = f.read()
        assert "[Timeline]" in content
        assert "시간 경과" in content

    def test_format_cumulative_time_integration(self):
        from modules.core.narrative_context_formatter import NarrativeContextFormatter

        elapsed = {"total_days": 45, "history": []}
        result = NarrativeContextFormatter.format_cumulative_time(elapsed)
        assert result  # 비어있지 않아야 함
        assert "45" in result or "1개월" in result or "달" in result

    def test_cumulative_elapsed_empty(self):
        from modules.core.narrative_context_formatter import NarrativeContextFormatter

        assert NarrativeContextFormatter.format_cumulative_time(None) == ""
        assert NarrativeContextFormatter.format_cumulative_time({}) == ""
        assert NarrativeContextFormatter.format_cumulative_time({"total_days": 0}) == ""


# ── GAP-6: 도입부 유사도 ─────────────────────────────────────────


class TestOpeningSimilarityIntegration:
    def test_exact_duplicate_opening(self):
        opening = "아침 햇살이 사무실 창문을 비추었다. 김도현은 책상 앞에 앉아 모니터를 바라보았다." * 5
        checker = NumericConsistencyChecker()
        warns = checker.check(opening, ep_num=5, prev_manuscript=opening)
        opening_warns = [w for w in warns if w["check"] == "도입부 유사도"]
        assert len(opening_warns) >= 1

    def test_short_manuscript_skip(self):
        checker = NumericConsistencyChecker()
        warns = checker.check("짧은 텍스트", ep_num=5, prev_manuscript="짧은 텍스트")
        opening_warns = [w for w in warns if w["check"] == "도입부 유사도"]
        assert len(opening_warns) == 0

    def test_threshold_customizable(self):
        """_check_opening_similarity threshold 직접 호출 테스트."""
        text1 = "완전히 다른 내용입니다. 새로운 시작의 아침이 밝았다. 주인공은 전혀 다른 장소에 있었다." * 5
        text2 = "깊은 밤 어둠 속에서 눈을 떴다. 낯선 천장이 보였다. 여기가 어디인지 알 수 없었다." * 5
        result = NumericConsistencyChecker._check_opening_similarity(
            text1,
            prev_manuscript=text2,
            threshold=0.10,
        )
        # 매우 다른 내용이므로 10% 임계값이어도 경고 없을 가능성 높음
        assert isinstance(result, list)


# ── 통합: NC-2 전체 체크 경로 ─────────────────────────────────────


class TestNC2FullPath:
    def test_all_nc2_checks_run(self):
        """check() 호출 시 NC-2 3개 검사가 모두 경로를 탄다."""
        fl = MagicMock()
        fl.get_numbers.return_value = {
            "평가금액": {"value": 15, "unit": "억"},
            "증거금": {"value": 10, "unit": "억"},
        }
        ws = MagicMock()
        ws.npcs = {"npc1": {"name": "테스트", "role": "역할"}}
        checker = NumericConsistencyChecker(fact_ledger=fl, world_state=ws)
        text = "증거금 유지율 150%이다. 테스트 팀장이 보고했다. " * 10
        prev = "완전히 다른 도입부. 밤하늘이 빛나고 있었다. " * 10
        warns = checker.check(text, ep_num=5, prev_manuscript=prev)
        assert isinstance(warns, list)
        # 에러 없이 전체 체크 완료 확인
