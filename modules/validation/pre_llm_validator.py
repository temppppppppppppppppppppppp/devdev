"""
[V60.56] Pre-LLM Validator - Advisory Mode
Python 기반 검사 → LLM에게 정보 제공용 (REJECT 권한 없음)

10가지 Python 기반 검사 (모두 advisory):
1. 중복 단어 과다 (vocabulary diversity)
2. 문장 길이 극단화 (prose rhythm)
3. 대사 절대 부족
4. 감각 묘사 메이저 누락
5. 신체 물리학 오류
6. 시간 흐름 비논리
7. 문장 끝 형식 일관성
8. NPC 이름 불일치
9. 반복되는 문장 구조
10. [V70] 시점(POV) 일관성

비용: $0 (Python 기반)
[V60.56] REJECT 권한 제거: Python은 정보 수집만, LLM이 최종 판단
"""

import re
from collections import Counter
from typing import Any

from modules.validation.threshold_helper import _threshold


class PreLLMValidator:
    """
    원고 검증 전 9가지 Python 기반 검사
    LLM 호출 비용 없이 명백한 오류를 사전 차단
    """

    def __init__(self, genre: str = "wuxia", pov: str = "", protagonist_name: str = ""):
        """
        Args:
            genre: 장르 (wuxia, hunter, investment)
            pov: [V70] 서술 시점 (1인칭/3인칭/전지적/혼합)
            protagonist_name: [S-06] 주인공 이름 (동적 POV regex 빌드)
        """
        self.genre = genre
        self.pov = pov
        self.protagonist_name = protagonist_name

    def validate(self, manuscript: str, context: dict[str, Any] = None) -> dict:
        """
        9가지 검증 실행

        Args:
            manuscript: 검증할 원고
            context: 검증 컨텍스트 (encyclopedia, npc_profiles 등)

        Returns:
            {
                "passed": bool,
                "critical_issues": [...],
                "warnings": [...],
                "score_deduction": int (0-10)
            }
        """
        context = context or {}
        issues = []
        warnings = []
        score_deduction = 0

        # 1. 과다 반복 단어 (TTR 악화)
        repeated = self._check_word_repetition(manuscript)
        if repeated.get("has_issue"):
            issues.append(repeated)
            score_deduction += 3

        # 2. 극단적 문장 길이 변화
        rhythm_issue = self._check_extreme_sentence_length(manuscript)
        if rhythm_issue.get("has_issue"):
            warnings.append(rhythm_issue)
            score_deduction += 2

        # 3. 대사 절대 부족
        dialogue = self._check_dialogue_presence(manuscript)
        if dialogue.get("missing"):
            issues.append(dialogue)
            score_deduction += 5

        # 4. 감각 묘사 메이저 누락
        sensory = self._check_sensory_presence(manuscript)
        if sensory.get("missing_count", 0) > 3:
            warnings.append(sensory)
            score_deduction += 2

        # 5. 신체 물리학 오류 (중요!)
        physics = self._check_body_physics(manuscript)
        if physics.get("violations"):
            issues.append(physics)
            score_deduction += 4

        # 6. 시간 흐름 비논리
        time_logic = self._check_time_progression(manuscript)
        if time_logic.get("violations"):
            warnings.append(time_logic)
            score_deduction += 1

        # 7. 문장 끝 형식 일관성
        ending_format = self._check_sentence_endings(manuscript)
        if ending_format.get("inconsistency_level", 0) > 0.5:
            warnings.append(ending_format)
            score_deduction += 1

        # 8. NPC 이름 일관성
        npc_names = self._check_npc_naming(manuscript, context)
        if npc_names.get("inconsistencies"):
            warnings.append(npc_names)
            score_deduction += 2

        # 9. 회차별 반복 구조
        repetitive = self._check_structural_repetition(manuscript)
        if repetitive.get("repetition_score", 0) > _threshold("pre_llm.repetition_score_threshold", 0.6):
            warnings.append(repetitive)
            score_deduction += 1

        # 10. [V70] 시점(POV) 일관성 체크
        if self.pov:
            pov_result = self._check_pov_consistency(manuscript)
            if pov_result.get("has_issue"):
                warnings.append(pov_result)
                score_deduction += 2

        # [V60.56] 최종 판정 - Python은 REJECT 권한 없음, 항상 passed=True
        # issues를 advisory로 변환 (LLM에게 전달할 정보)
        advisory_issues = issues

        return {
            "passed": True,  # [V60.56] 항상 통과, LLM이 최종 판단
            "critical_issues": [],  # [V60.56] 빈 리스트 (REJECT 안 함)
            "advisory_issues": advisory_issues,  # [V60.56] LLM에게 전달할 정보
            "warnings": warnings,
            "score_deduction": min(10, score_deduction),
            "reason": f"Advisory - 참고사항 {len(advisory_issues)}개, 경고 {len(warnings)}개",
            "check_count": 10,
        }

    def _check_word_repetition(self, manuscript: str) -> dict:
        """1. 과다 반복 단어 체크"""
        words = re.findall(r"[가-힣]{2,}", manuscript)
        if not words:
            return {"has_issue": False}

        word_counts = Counter(words)

        # 불용어 제외
        stopwords = {
            "것이다",
            "있다",
            "없다",
            "하다",
            "되다",
            "이다",
            "그",
            "저",
            "이",
            "그것",
            "이것",
            "했다",
            "있었다",
            "그리고",
            "하지만",
            "그러나",
            "그래서",
            "때문에",
        }
        word_counts = Counter(
            {w: c for w, c in word_counts.items() if w not in stopwords}
        )  # [V66.2] F-3: Counter 유지 (.most_common 보존)

        # 같은 단어가 15회 이상 반복 = 위반
        overused = [(w, c) for w, c in word_counts.most_common(10) if c > 15]

        if overused:
            return {
                "has_issue": True,
                "category": "과다_반복_단어",
                "items": overused[:5],
                "severity": "HIGH" if overused[0][1] > 25 else "MEDIUM",
                "description": f"'{overused[0][0]}' {overused[0][1]}회 반복",
            }

        return {"has_issue": False}

    def _check_extreme_sentence_length(self, manuscript: str) -> dict:
        """2. 극단적 문장 길이 변화"""
        import statistics

        sentences = re.split(r"[.!?]\s+", manuscript)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]

        if len(sentences) < 10:
            return {"has_issue": False}

        lengths = [len(s) for s in sentences]
        mean_len = statistics.mean(lengths)

        if mean_len < 0.001:
            return {"has_issue": False}

        std_dev = statistics.stdev(lengths) if len(lengths) > 1 else 0
        cv = std_dev / mean_len

        if cv > 0.8:  # 극단적 변화
            return {
                "has_issue": True,
                "category": "문장_길이_극단화",
                "cv": round(cv, 2),
                "mean": round(mean_len, 1),
                "severity": "WARNING",
                "description": f"문장 길이 변동계수 {cv:.2f} (권장 0.3~0.6)",
            }

        return {"has_issue": False}

    def _check_dialogue_presence(self, manuscript: str) -> dict:
        """3. 대사 절대 부족"""
        # 큰따옴표 또는 유니코드 따옴표
        dialogue_count = manuscript.count('"') + manuscript.count("\u201c") + manuscript.count("\u201d")
        dialogue_pairs = dialogue_count // 2  # 쌍으로 계산

        # 1000자당 최소 1.5회의 대사 필요
        expected_min = max(3, int(len(manuscript) / 700))

        if dialogue_pairs < expected_min:
            return {
                "missing": True,
                "category": "대사_부족",
                "count": dialogue_pairs,
                "expected_min": expected_min,
                "severity": "CRITICAL",
                "description": f"대사 {dialogue_pairs}회 (최소 {expected_min}회 필요)",
            }

        return {"missing": False}

    def _check_sensory_presence(self, manuscript: str) -> dict:
        """4. 감각 묘사 메이저 누락"""
        sensory_keywords = {
            "visual": ["보았다", "보이", "빛", "색", "형태", "눈에", "모습", "바라보"],
            "auditory": ["소리", "들렸다", "들었다", "울렸다", "고요", "시끄"],
            "tactile": ["느껴졌다", "차가", "따뜻", "부드", "거칠", "아팠다", "통증"],
            "olfactory": ["냄새", "향기", "악취", "향이"],
        }

        # 무협 특화 감각
        if self.genre == "wuxia":
            sensory_keywords["martial"] = ["기혈", "내공", "기운", "살기", "검기", "파동", "기감"]

        paragraphs = [p for p in manuscript.split("\n\n") if len(p) > 100]
        missing_senses = 0

        for para in paragraphs:
            sensory_count = sum(para.count(kw) for senses in sensory_keywords.values() for kw in senses)
            if sensory_count == 0:
                missing_senses += 1

        return {
            "missing_count": missing_senses,
            "total_paragraphs": len(paragraphs),
            "category": "감각_메이저_누락",
            "severity": "WARNING" if missing_senses > 3 else "OK",
            "description": f"{missing_senses}/{len(paragraphs)} 문단에 감각 묘사 없음",
        }

    def _check_body_physics(self, manuscript: str) -> dict:
        """5. 신체 물리학 오류"""
        violations = []

        # 패턴: 동시에 3개 이상 행동
        triple_action = re.findall(
            r"(왼손|오른손|양손).{0,20}(왼손|오른손|양손).{0,20}(왼손|오른손|양손)",
            manuscript,
            re.DOTALL,
        )
        if triple_action:
            violations.append("손 사용 모순 (3개 이상 동시 사용)")

        # [I-07] 부상-행동 패턴은 continuity_validator 전담 → 여기서 제거
        # (명백한 물리 위반인 "손 3개" 등만 pre_llm에서 감지)

        return {
            "violations": violations[:3],
            "category": "신체_물리학_오류",
            "severity": "CRITICAL" if violations else "OK",
            "description": violations[0] if violations else "정상",
        }

    def _check_time_progression(self, manuscript: str) -> dict:
        """6. 시간 흐름 비논리"""
        time_markers = re.findall(r"(?:같은 날|그날|다음날|이튿날|며칠 후|다음 주|몇 주 후|한 달|일 년)", manuscript)

        violations = []

        # 시간 표현이 너무 자주 변함 (15회 이상) = 혼란
        if len(time_markers) > 15:
            violations.append(f"시간 표현 과다 ({len(time_markers)}회)")

        # "같은 날" 다음에 바로 "며칠 후" 같은 모순
        time_text = " ".join(time_markers)
        if "같은 날" in time_text and "며칠 후" in time_text:
            # 순서 체크
            same_day_idx = manuscript.find("같은 날")
            days_later_idx = manuscript.find("며칠 후")
            if same_day_idx >= 0 and days_later_idx >= 0 and days_later_idx < same_day_idx:
                violations.append("시간 흐름 역행 (며칠 후 → 같은 날)")

        return {
            "violations": violations,
            "count": len(time_markers),
            "category": "시간_흐름_비논리",
            "severity": "WARNING" if violations else "OK",
        }

    def _check_sentence_endings(self, manuscript: str) -> dict:
        """7. 문장 끝 형식 일관성"""
        # 문장 끝 패턴
        endings = re.findall(r"[가-힣]+다[.!?]", manuscript)

        if len(endings) < 10:
            return {"inconsistency_level": 0}

        # 마침표, 느낌표, 물음표 비율
        period_count = sum(1 for e in endings if e.endswith("."))
        exclaim_count = sum(1 for e in endings if e.endswith("!"))
        question_count = sum(1 for e in endings if e.endswith("?"))

        total = len(endings)

        # 느낌표가 30% 이상이면 과다
        if exclaim_count / total > 0.3:
            return {
                "inconsistency_level": 0.6,
                "category": "느낌표_과다",
                "severity": "WARNING",
                "description": f"느낌표 {exclaim_count / total:.0%} (권장 10% 이하)",
            }

        return {"inconsistency_level": 0}

    def _check_npc_naming(self, manuscript: str, context: dict) -> dict:
        """8. NPC 이름 일관성"""
        # context에서 올바른 NPC 이름 추출
        npc_profiles = context.get("npc_profiles", {})
        encyclopedia = context.get("encyclopedia", {})

        correct_names = set()
        if isinstance(npc_profiles, dict):
            correct_names.update(npc_profiles.keys())
        if isinstance(encyclopedia, dict):
            npcs = encyclopedia.get("npcs", [])
            for npc in npcs:
                if isinstance(npc, dict) and npc.get("name"):
                    correct_names.add(npc["name"])

        if not correct_names:
            return {"inconsistencies": []}

        inconsistencies = []

        # 정의된 NPC 이름과 비슷하지만 다른 이름 찾기
        for correct_name in correct_names:
            if len(correct_name) < 2:
                continue

            # 유사 이름 패턴 (1자 다름)
            for i in range(len(correct_name)):
                # 각 위치에서 다른 문자로 대체된 이름 찾기
                pattern = re.escape(correct_name[:i]) + r"[가-힣]" + re.escape(correct_name[i + 1 :])
                similar_names = re.findall(pattern, manuscript)
                for found in similar_names:
                    if found != correct_name:
                        inconsistencies.append((found, correct_name))

        # 중복 제거
        inconsistencies = list(set(inconsistencies))[:3]

        return {
            "inconsistencies": inconsistencies,
            "category": "NPC_이름_불일치",
            "severity": "WARNING" if inconsistencies else "OK",
            "description": f"{len(inconsistencies)}개 NPC 이름 불일치" if inconsistencies else "정상",
        }

    def _check_structural_repetition(self, manuscript: str) -> dict:
        """9. 회차별 반복되는 문장 구조"""
        sentences = re.split(r"[.!?]\s+", manuscript)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

        if len(sentences) < 15:
            return {"repetition_score": 0}

        # 처음 3단어로 문장 시작 패턴 추출
        sentence_starts = []
        for sent in sentences:
            words = re.findall(r"[가-힣]+", sent)
            if len(words) >= 3:
                start = " ".join(words[:3])
                sentence_starts.append(start)

        if not sentence_starts:
            return {"repetition_score": 0}

        # 가장 자주 반복되는 시작 패턴
        most_common = Counter(sentence_starts).most_common(3)

        # 상위 3개 패턴의 총 비율
        top_3_count = sum(count for _, count in most_common)
        repetition_score = top_3_count / len(sentence_starts)

        return {
            "repetition_score": round(repetition_score, 2),
            "most_common_starts": most_common[:3],
            "category": "구조적_반복",
            "severity": (
                "WARNING" if repetition_score > _threshold("pre_llm.repetition_score_threshold", 0.6) else "OK"
            ),
            "description": f"상위 3개 시작 패턴 비율 {repetition_score:.0%}",
        }

    def _check_pov_consistency(self, manuscript: str) -> dict:
        """10. [V70] 시점(POV) 일관성 체크"""
        # 대화 내용 제거 (대화 속 '나'는 무관)
        no_dialogue = re.sub(r'["""][^"""]*["""]', "", manuscript)
        # ―로 시작하는 대화도 제거
        no_dialogue = re.sub(r"―[^\n]+", "", no_dialogue)

        first_person = len(re.findall(r"(?:나는|내가|나를|나에게|내 )", no_dialogue))
        # [S-06] 동적 주인공명 regex — 하드코딩 "시우" 제거
        _third_base = r"(?:그는|그녀는|그가|그를"
        if self.protagonist_name:
            _name = re.escape(self.protagonist_name)
            _third_base += rf"|{_name}는|{_name}가"
        _third_base += r")"
        third_person = len(re.findall(_third_base, no_dialogue))

        violations = []

        if self.pov == "1인칭":
            # 1인칭인데 3인칭 서술이 많으면 문제
            if third_person > 5 and third_person > first_person * 0.3:
                violations.append(f"1인칭 모드인데 3인칭 서술 {third_person}회 감지 (1인칭 {first_person}회 대비 과다)")
        elif self.pov == "3인칭":
            # 3인칭인데 서술자 '나'가 많으면 문제
            if first_person > 5 and first_person > third_person * 0.3:
                violations.append(
                    f"3인칭 모드인데 서술자 1인칭 {first_person}회 감지 (3인칭 {third_person}회 대비 과다)"
                )
        elif self.pov == "전지적":
            if first_person > 5 and first_person > max(3, third_person * 0.2):
                violations.append(f"전지적 시점인데 서술자 1인칭 {first_person}회 감지")
        elif self.pov == "혼합":
            _has_scene_separator = bool(re.search(r"\n\s*\*{3,}\s*\n", no_dialogue))
            scene_blocks = [block.strip() for block in re.split(r"\n\s*\*{3,}\s*\n", no_dialogue) if block.strip()]
            if not _has_scene_separator and first_person > 5 and third_person > 5:
                violations.append("혼합 시점인데 씬 구분자(***) 없이 1인칭/3인칭 서술이 함께 나타남")
            mixed_blocks = []
            for idx, block in enumerate(scene_blocks, 1):
                block_first = len(re.findall(r"(?:나는|내가|나를|나에게|내 )", block))
                block_third = len(re.findall(_third_base, block))
                if block_first > 2 and block_third > 2:
                    mixed_blocks.append(idx)
            if not violations and mixed_blocks:
                violations.append(
                    "혼합 시점인데 동일 씬 블록에서 1인칭/3인칭 서술이 함께 감지됨 "
                    f"(scene {', '.join(str(i) for i in mixed_blocks[:4])})"
                )

        if violations:
            return {
                "has_issue": True,
                "category": "시점_일관성",
                "severity": "WARNING",
                "description": violations[0],
                "first_person_count": first_person,
                "third_person_count": third_person,
                "expected_pov": self.pov,
            }

        return {"has_issue": False}

    def get_summary(self, result: dict) -> str:
        """검증 결과 요약 문자열 생성"""
        lines = [
            "=" * 50,
            "[V56 Pre-LLM Validator] 사전 검증 결과",
            "=" * 50,
        ]

        if result["passed"]:
            lines.append(f"✅ 통과 (경고 {len(result['warnings'])}개)")
        else:
            lines.append(f"❌ REJECT (이슈 {len(result['critical_issues'])}개)")

        if result["critical_issues"]:
            lines.append("\n🚨 Critical Issues:")
            for issue in result["critical_issues"]:
                desc = issue.get("description", issue.get("category", "Unknown"))
                lines.append(f"   - {desc}")

        if result["warnings"]:
            lines.append("\n⚠️ Warnings:")
            for warning in result["warnings"][:3]:
                desc = warning.get("description", warning.get("category", "Unknown"))
                lines.append(f"   - {desc}")

        lines.append(f"\n점수 감점: -{result['score_deduction']}점")
        lines.append("=" * 50)

        return "\n".join(lines)
