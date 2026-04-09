"""
[V64 P2-1] Director GradingSystem — 원고 품질 등급화 전담 모듈
[V65 C-5] 적응형 기준선 + 상태 업데이트 검증 메서드 추가

Director God Object 분해의 두 번째 단계.
원고 품질 평가, 등급 부여, 수정 가이드 생성을 담당.
적응형 PASS 기준선 계산 및 상태 업데이트 검증도 포함.
순수 데이터 가공 — LLM 호출 없음, BaseAgent 의존 없음.
"""

from modules.core.constants import ManuscriptLimits
from modules.validation.threshold_helper import _threshold

_ADAPTIVE_BASE_MIN = _threshold("adaptive_grading.base_score_min", 45)    # [TF-6-07]
_ADAPTIVE_BASE_MAX = _threshold("adaptive_grading.base_score_max", 85)    # [TF-6-07]
_ADAPTIVE_LEN_MIN = _threshold("adaptive_grading.length_base_min", 3500)  # [TF-6-07]
_ADAPTIVE_LEN_MAX = _threshold("adaptive_grading.length_base_max", 6000)  # [TF-6-07]


class DirectorGradingSystem:
    """
    [V64 P2-1] Director에서 분리된 등급화 모듈

    담당:
    - grade_manuscript_v59(): 원고 품질 등급화 (A/B/C/D)
    - generate_revision_guide_v59(): 등급 기반 수정 가이드 생성
    - format_revision_report_v59(): 사람이 읽기 좋은 리포트 포맷
    - get_adaptive_threshold(): 적응형 PASS 기준선 계산 [V65 C-5]
    - apply_adaptive_decision(): 적응형 PASS/REJECT 재결정 [V65 C-5]
    - on_approve_workflow(): 상태 업데이트 검증 및 승인 [V65 C-5]
    """

    def __init__(self, director=None) -> None:
        """
        Args:
            director: Director 인스턴스 (적응형 기준선 접근용, 선택적)
        """
        self._d = director

    # [V59] 등급별 기준 정의
    QUALITY_GRADES = {
        "A": {
            "min_score": 85,
            "label": "출판 수준",
            "description": "수정 없이 바로 게재 가능한 수준",
            "action": "PUBLISH_READY",
        },
        "B": {
            "min_score": 70,
            "label": "게재 가능",
            "description": "경미한 수정 후 게재 가능",
            "action": "MINOR_REVISION",
        },
        "C": {
            "min_score": 50,
            "label": "수정 필요",
            "description": "상당한 수정 후 재검토 필요",
            "action": "MAJOR_REVISION",
        },
        "D": {"min_score": 0, "label": "재작성 필요", "description": "근본적인 재작성 필요", "action": "REWRITE"},
    }

    # [V63.2] 품질 항목별 가중치 — 일관성 강화
    # [Phase 3-D1] satisfaction 카테고리 신설, consistency/engagement 소폭 축소
    QUALITY_WEIGHTS = {
        "structure": 0.15,  # 구조적 완성도
        "prose": 0.15,  # 문장력
        "consistency": 0.25,  # 설정 일관성 (0.30→0.25)
        "engagement": 0.15,  # 독자 몰입도 (0.20→0.15)
        "commercial": 0.20,  # 상업적 매력
        "satisfaction": 0.10,  # [Phase 3-D1] 독자 대리만족
    }

    def grade_manuscript_v59(self, ep_num: int, manuscript: str, validation_result: dict) -> dict:
        """
        [V59] 원고 품질 등급화

        Args:
            ep_num: 에피소드 번호
            manuscript: 원고 텍스트
            validation_result: ValidationOrchestrator 결과

        Returns:
            {
                'grade': 'A' | 'B' | 'C' | 'D',
                'score': float,
                'label': str,
                'breakdown': {...},
                'revision_guide': {...},
                'strengths': [...],
                'weaknesses': [...]
            }
        """
        # 1. 기본 점수 추출
        breakdown = validation_result.get("breakdown", {})

        # 2. 세부 점수 분석
        item_scores = {}
        for category, weight in self.QUALITY_WEIGHTS.items():
            related_score = self._extract_category_score(breakdown, category)
            item_scores[category] = {"score": related_score, "weight": weight, "weighted_score": related_score * weight}

        # 3. 가중 총점 계산
        weighted_total = sum(item["weighted_score"] for item in item_scores.values())

        # 4. 등급 결정
        grade = "D"
        for g, criteria in self.QUALITY_GRADES.items():
            if weighted_total >= criteria["min_score"]:
                grade = g
                break

        grade_info = self.QUALITY_GRADES[grade]

        # 5. 강점/약점 추출
        strengths = []
        weaknesses = []
        for category, data in item_scores.items():
            if data["score"] >= 80:
                strengths.append(
                    {"category": category, "score": data["score"], "note": self._get_strength_description(category)}
                )
            elif data["score"] < 60:
                weaknesses.append(
                    {"category": category, "score": data["score"], "note": self._get_weakness_description(category)}
                )

        # 6. 수정 가이드 생성
        revision_guide = self.generate_revision_guide_v59(
            grade=grade, item_scores=item_scores, weaknesses=weaknesses, validation_result=validation_result
        )

        return {
            "grade": grade,
            "score": round(weighted_total, 1),
            "label": grade_info["label"],
            "description": grade_info["description"],
            "action": grade_info["action"],
            "breakdown": item_scores,
            "revision_guide": revision_guide,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "ep_num": ep_num,
        }

    def _extract_category_score(self, breakdown: dict, category: str) -> float:
        """validation breakdown에서 카테고리별 점수 추출"""
        category_mapping = {
            "structure": ["scene_completeness", "scope_overflow", "required_scenes"],
            "prose": ["prose_rhythm", "vocabulary_diversity", "show_dont_tell"],
            "consistency": ["character_consistency", "relationship_consistency", "continuity"],
            "engagement": ["emotion_arc", "cliffhanger"],
            "commercial": ["commercial_appeal", "pattern_diversity"],
            "satisfaction": ["reader_satisfaction"],  # [Phase 3-D1]
        }

        related_items = category_mapping.get(category, [])
        scores = []

        for item_name in related_items:
            if item_name in breakdown:
                item_data = breakdown[item_name]
                if isinstance(item_data, dict):
                    score = item_data.get("score", 0)
                    max_score = item_data.get("max", 1)
                    scores.append((score / max_score) * 100 if max_score > 0 else 0)

        return sum(scores) / len(scores) if scores else 50

    def _get_strength_description(self, category: str) -> str:
        """강점 설명 반환"""
        descriptions = {
            "structure": "씬 구성과 전개가 탄탄합니다",
            "prose": "문장력이 유려하고 읽기 좋습니다",
            "consistency": "설정 일관성이 잘 유지됩니다",
            "engagement": "독자 몰입도가 높습니다",
            "commercial": "상업적 매력이 있습니다",
            "satisfaction": "독자 대리만족 요소가 충분합니다",
        }
        return descriptions.get(category, "양호한 수준입니다")

    def _get_weakness_description(self, category: str) -> str:
        """약점 설명 반환"""
        descriptions = {
            "structure": "씬 구성이 불균형하거나 누락이 있습니다",
            "prose": "문장이 단조롭거나 묘사가 부족합니다",
            "consistency": "설정 모순이나 불일치가 있습니다",
            "engagement": "독자 몰입을 방해하는 요소가 있습니다",
            "commercial": "상업적 매력 요소가 부족합니다",
            "satisfaction": "독자 대리만족 요소(성취/승리/성장)가 부족합니다",
        }
        return descriptions.get(category, "개선이 필요합니다")

    def generate_revision_guide_v59(
        self, grade: str, item_scores: dict, weaknesses: list, validation_result: dict
    ) -> dict:
        """
        [V59] 등급 및 약점 기반 구체적 수정 가이드 생성

        Args:
            grade: 품질 등급 (A/B/C/D)
            item_scores: 항목별 점수
            weaknesses: 약점 목록
            validation_result: 전체 검증 결과

        Returns:
            {
                'priority': str,
                'tasks': [...],
                'examples': [...],
                'estimated_effort': str
            }
        """
        tasks = []
        examples = []

        if grade == "D":
            priority = "CRITICAL"
            tasks.append(
                {
                    "type": "rewrite",
                    "description": "원고 전체를 재구성해야 합니다",
                    "detail": "Blueprint를 다시 확인하고 기본 구조부터 재설계하세요",
                }
            )
        elif grade == "C":
            priority = "HIGH"
            tasks.append(
                {
                    "type": "major_revision",
                    "description": "주요 문제점 수정이 필요합니다",
                    "detail": "아래 약점 항목들을 집중 개선하세요",
                }
            )
        elif grade == "B":
            priority = "MEDIUM"
            tasks.append(
                {
                    "type": "minor_revision",
                    "description": "경미한 수정으로 품질 향상 가능합니다",
                    "detail": "아래 제안사항을 참고하여 다듬으세요",
                }
            )
        else:  # A
            priority = "LOW"
            tasks.append(
                {
                    "type": "polish",
                    "description": "최종 교정 수준의 검토만 필요합니다",
                    "detail": "오탈자나 미세한 표현 개선 위주로 확인하세요",
                }
            )

        for weakness in weaknesses:
            category = weakness.get("category", "")
            score = weakness.get("score", 0)

            revision_task = self._generate_category_revision(category, score, validation_result)
            if revision_task:
                tasks.append(revision_task)

            example = self._get_revision_example(category)
            if example:
                examples.append(example)

        effort_map = {
            "D": "4시간 이상 소요 예상",
            "C": "2-4시간 소요 예상",
            "B": "30분-1시간 소요 예상",
            "A": "15분 내외 소요 예상",
        }

        return {
            "priority": priority,
            "grade": grade,
            "tasks": tasks[:10],
            "examples": examples[:5],
            "estimated_effort": effort_map.get(grade, "알 수 없음"),
            "focus_areas": [w["category"] for w in weaknesses[:3]],
        }

    def _generate_category_revision(self, category: str, score: float, validation_result: dict) -> dict:
        """카테고리별 수정 지침 생성"""
        revisions = {
            "structure": {
                "type": "structure_fix",
                "description": "씬 구조 개선",
                "details": [
                    "Blueprint 핵심 씬/의무가 모두 실제 장면으로 구현되었는지 확인",
                    "후반부 씬이 요약되지 않고 체류 시간이 확보되었는지 검토",
                    "씬 전환이 자연스러운지 점검",
                ],
            },
            "prose": {
                "type": "prose_improvement",
                "description": "문장력 향상",
                "details": [
                    '직접 감정 서술("슬펐다") → 묘사로 전환',
                    "문장 시작 패턴 다양화 (연속 3문장 같은 시작 금지)",
                    "감각 묘사 추가 (시각 외 청각, 촉각 등)",
                ],
            },
            "consistency": {
                "type": "consistency_fix",
                "description": "설정 일관성 수정",
                "details": [
                    "직전 화 엔딩과 현재 화 시작의 연결 확인",
                    "NPC 관계 상태 변화의 정당성 검토",
                    "아이템/무공 사용의 획득 시점 확인",
                ],
            },
            "engagement": {
                "type": "engagement_boost",
                "description": "몰입도 강화",
                "details": ["감정 전환의 자연스러운 흐름 설계", "긴장감 있는 갈등 요소 추가", "Cliffhanger 엔딩 강화"],
            },
            "commercial": {
                "type": "commercial_appeal",
                "description": "상업적 매력 강화",
                "details": [
                    "사이다 요소 또는 복선 추가",
                    "다음 화 기대감을 높이는 떡밥 배치",
                    "독자 감정 반응 유발 포인트 삽입",
                ],
            },
            "satisfaction": {
                "type": "satisfaction_boost",
                "description": "독자 대리만족 강화",
                "details": [
                    "주인공이 성취/승리/인정받는 장면 추가",
                    "자력 해결 비율 높이기 (타인 구출 의존 줄이기)",
                    "독자가 공감할 수 있는 내면 묘사 강화",
                ],
            },
        }

        base_revision = dict(revisions.get(category, {}))
        if not base_revision:
            return None

        if score < 40:
            base_revision["urgency"] = "CRITICAL"
            base_revision["note"] = "이 항목의 대폭 개선 없이는 게재 불가"
        elif score < 60:
            base_revision["urgency"] = "HIGH"
            base_revision["note"] = "상당한 수정 필요"
        else:
            base_revision["urgency"] = "MEDIUM"
            base_revision["note"] = "다듬기 수준의 개선 권장"

        return base_revision

    def _get_revision_example(self, category: str) -> dict:
        """카테고리별 수정 예시"""
        examples = {
            "structure": {
                "before": "갑자기 장면이 전환되어 다른 장소에 있었다.",
                "after": "한참을 걸은 끝에 객잔의 불빛이 눈에 들어왔다. 주인공은 지친 발걸음을 옮겨 문을 밀었다.",
                "note": "장면 전환에 시간/공간의 흐름을 명시",
            },
            "prose": {
                "before": "그는 슬펐다. 정말 슬펐다. 너무 슬펐다.",
                "after": "어깨가 축 처졌다. 주먹이 부들부들 떨렸고, 눈앞이 흐릿해졌다.",
                "note": "감정을 행동/신체 반응으로 묘사",
            },
            "consistency": {
                "before": "(직전 화 부상) → 멀쩡하게 전력 질주했다.",
                "after": "(직전 화 부상) → 부상당한 다리를 끌며 겨우 뛰었다. 통증이 밀려왔지만 멈출 수 없었다.",
                "note": "상태의 연속성 유지",
            },
            "engagement": {
                "before": "무사히 해결되어 잠들었다.",
                "after": "해결된 줄 알았다. 그때, 창문 너머로 낯선 그림자가 스쳐 지나갔다.",
                "note": "Cliffhanger로 긴장감 유지",
            },
            "commercial": {
                "before": "다음에 또 보자고 인사했다.",
                "after": '"다음에 보자. 그때...내가 숨긴 비밀을 알려주마." 의미심장한 미소가 번졌다.',
                "note": "떡밥/복선으로 기대감 유발",
            },
        }

        if not examples.get(category):
            # [Phase 3-D1] satisfaction 카테고리 예시
            if category == "satisfaction":
                return {
                    "before": "주인공은 또 패배했다. 무기력하게 돌아왔다.",
                    "after": '주인공의 검이 마침내 적의 방어를 뚫었다. "해냈다...!" 벅찬 감정이 차올랐다.',
                    "note": "주인공의 성취/승리 장면으로 독자 대리만족 제공",
                }
        return examples.get(category)

    def format_revision_report_v59(self, grade_result: dict) -> str:
        """
        [V59] 수정 가이드를 사람이 읽기 좋은 형태로 포맷

        Args:
            grade_result: grade_manuscript_v59() 결과

        Returns:
            str: 포맷팅된 리포트 텍스트
        """
        lines = [
            f"\n{'=' * 60}",
            f"[V59] 품질 등급 리포트 - 제{grade_result.get('ep_num', 'unknown')}화",
            f"{'=' * 60}\n",
        ]

        grade = grade_result.get("grade", "?")
        score = grade_result.get("score", 0)
        label = grade_result.get("label", "")

        grade_emoji = {"A": "🏆", "B": "✅", "C": "⚠️", "D": "❌"}.get(grade, "❓")
        lines.append(f"{grade_emoji} 등급: {grade} ({label})")
        lines.append(f"   점수: {score}/100")
        lines.append(f"   판정: {grade_result.get('description', '')}\n")

        strengths = grade_result.get("strengths", [])
        if strengths:
            lines.append("✨ 강점:")
            for s in strengths[:3]:
                lines.append(f"   - {s['category']}: {s['note']} ({s['score']}점)")
            lines.append("")

        weaknesses = grade_result.get("weaknesses", [])
        if weaknesses:
            lines.append("⚠️ 개선 필요:")
            for w in weaknesses[:3]:
                lines.append(f"   - {w['category']}: {w['note']} ({w['score']}점)")
            lines.append("")

        revision = grade_result.get("revision_guide", {})
        if revision:
            lines.append(f"📝 수정 가이드 (우선순위: {revision.get('priority', '?')})")
            lines.append(f"   예상 소요: {revision.get('estimated_effort', '?')}")
            lines.append("")

            tasks = revision.get("tasks", [])
            for i, task in enumerate(tasks[:5], 1):
                lines.append(f"   {i}. [{task.get('type', '?')}] {task.get('description', '')}")
                if task.get("details"):
                    for detail in task["details"][:3]:
                        lines.append(f"      - {detail}")

            examples = revision.get("examples", [])
            if examples:
                lines.append("\n📚 수정 예시:")
                for ex in examples[:2]:
                    if ex:
                        lines.append(f"   Before: {(ex.get('before') or '')[:50]}...")
                        lines.append(f"   After:  {(ex.get('after') or '')[:50]}...")
                        lines.append(f"   💡 {ex.get('note') or ''}")
                        lines.append("")

        lines.append(f"{'=' * 60}\n")

        return "\n".join(lines)

    # ── [V65 C-5] 적응형 기준선 + 상태 업데이트 검증 ──────────────

    def get_adaptive_threshold(
        self, arc_pos: int = 1, total_eps: int = 5, ep_type: str = "normal", retry_count: int = 0
    ) -> dict:
        """
        [V65 C-5] 적응형 PASS 기준선 계산

        Arc 위치, 장르, 에피소드 타입별로 동적 기준 적용.
        """
        if not self._d or not self._d.adaptive_thresholds_enabled:
            return {
                "pass_threshold": self._d.base_pass_threshold if self._d else 60,
                "length_threshold": ManuscriptLimits.WARNING_LENGTH,
                "strictness_level": "standard",
                "reason": "adaptive thresholds disabled",
            }

        base = self._d.base_pass_threshold
        length_base = ManuscriptLimits.WARNING_LENGTH
        reason_parts = []

        # 1. Arc 위치 기반 조정
        arc_position_ratio = arc_pos / total_eps if total_eps > 0 else 0.5

        if arc_position_ratio <= 0.2:
            base -= 5
            length_base -= 300
            reason_parts.append("도입부(-5점)")
        elif arc_position_ratio >= 0.8:
            base += 10
            length_base += 300
            reason_parts.append("절정부(+10점)")
        elif 0.4 <= arc_position_ratio <= 0.6:
            base += 3
            reason_parts.append("전환점(+3점)")

        # 2. 장르별 조정
        genre = self._d.genre if self._d else "wuxia"
        if genre == "wuxia":
            base += 0
        elif genre == "hunter":
            base += 2
            reason_parts.append("헌터장르(+2점)")
        elif genre == "investment":
            base += 3
            reason_parts.append("투자장르(+3점)")
        elif genre == "actor":
            base += 2
            reason_parts.append("배우장르(+2점)")
        elif genre == "sports":
            base += 2
            reason_parts.append("스포츠장르(+2점)")
        elif genre == "medical":
            base += 2
            reason_parts.append("의학장르(+2점)")

        # 3. 에피소드 타입별 조정
        if ep_type == "climax":
            base += 10
            length_base += 500
            reason_parts.append("클라이맥스(+10점)")
        elif ep_type == "intro":
            base -= 5
            length_base -= 200
            reason_parts.append("도입부(-5점)")
        elif ep_type == "transition":
            base -= 3
            reason_parts.append("전환(-3점)")

        # 4. 재시도 횟수별 완화
        if retry_count >= 3:
            base -= 10
            reason_parts.append("3+회재시도(-10점)")
        elif retry_count >= 2:
            base -= 5
            reason_parts.append("2회재시도(-5점)")

        # 5. 범위 제한 [TF-6-07] validation.yaml adaptive_grading 참조
        base = max(_ADAPTIVE_BASE_MIN, min(_ADAPTIVE_BASE_MAX, base))
        length_base = max(_ADAPTIVE_LEN_MIN, min(_ADAPTIVE_LEN_MAX, length_base))

        if base >= 75:
            strictness = "strict"
        elif base >= 60:
            strictness = "standard"
        else:
            strictness = "lenient"

        return {
            "pass_threshold": base,
            "length_threshold": length_base,
            "strictness_level": strictness,
            "reason": ", ".join(reason_parts) if reason_parts else "standard",
        }

    def apply_adaptive_decision(
        self, score: int, original_decision: str, arc_pos: int = 1, total_eps: int = 5, retry_count: int = 0,
        ep_type: str = "normal",
    ) -> dict:
        """[V65 C-5] 적응형 기준에 따라 PASS/REJECT 재결정"""
        threshold_info = self.get_adaptive_threshold(arc_pos=arc_pos, total_eps=total_eps, ep_type=ep_type, retry_count=retry_count)

        threshold = threshold_info["pass_threshold"]
        adjusted = False
        new_decision = original_decision

        if score >= threshold:
            if original_decision == "REJECT":
                new_decision = "CONDITIONAL_PASS"
                adjusted = True
        else:
            if original_decision in ("PASS", "PASS_WITH_FIX"):  # [TF-32]
                new_decision = "CONDITIONAL_PASS"
                adjusted = True

        return {
            "decision": new_decision,
            "adjusted": adjusted,
            "threshold_used": threshold,
            "strictness": threshold_info["strictness_level"],
            "reason": threshold_info["reason"],
        }

    def on_approve_workflow(self, ep_num, state_updates, current_hud, martial_manager=None) -> dict:
        """
        [V65 C-5] 상태 업데이트 검증 및 적용

        Writer가 제안한 state_updates를 검증하고, 승인된 항목만 반환합니다.
        """
        if not state_updates or not isinstance(state_updates, dict):
            return {
                "approved": True,
                "applied_updates": {},
                "rejected_updates": {},
                "warnings": ["Writer가 state_updates를 제출하지 않음 - 상태 변경 없음"],
            }

        applied = {}
        rejected = {}
        warnings = []

        LIMITS = {
            "misunderstanding": {"max_change": 30},
            "obsession": {"max_change": 30},
            "wealth": {"max_change": 10000},
        }
        # [TF-41] P1-3: 무협 전용 — 비무협 장르는 내공 변동 검증 스킵
        _genre = self._d.genre if self._d else "wuxia"
        if _genre == "wuxia":
            LIMITS["internal_energy"] = {"max_increase": 200, "max_decrease": -500}

        for key, value in state_updates.items():
            if value in ["현상 유지", "유지", "변화 없음", None, ""]:
                continue

            # [TypeSafety] LLM이 숫자를 직접 반환한 경우 LIMITS 검증 적용
            if isinstance(value, int | float) and key in LIMITS:
                change = int(value)
                limits = LIMITS[key]
                if "max_increase" in limits and change > limits["max_increase"]:
                    rejected[key] = {
                        "proposed": value,
                        "reason": f"증가량 초과 (최대 +{limits['max_increase']})",
                    }
                    warnings.append(f"[REJECT] {key}: {value} → 비합리적 증가량")
                    continue
                if "max_decrease" in limits and change < limits["max_decrease"]:
                    rejected[key] = {
                        "proposed": value,
                        "reason": f"감소량 초과 (최대 {limits['max_decrease']})",
                    }
                    warnings.append(f"[REJECT] {key}: {value} → 비합리적 감소량")
                    continue
                if "max_change" in limits and abs(change) > limits["max_change"]:
                    rejected[key] = {
                        "proposed": value,
                        "reason": f"변화량 초과 (최대 ±{limits['max_change']})",
                    }
                    warnings.append(f"[REJECT] {key}: {value} → 변화량 초과")
                    continue

            if isinstance(value, str) and (value.startswith("+") or value.startswith("-")):
                try:
                    import re

                    numeric_match = re.match(r"^([+-]?\d+)", value)
                    if numeric_match:
                        change = int(numeric_match.group(1))

                        if key in LIMITS:
                            limits = LIMITS[key]
                            if "max_increase" in limits and change > limits["max_increase"]:
                                rejected[key] = {
                                    "proposed": value,
                                    "reason": f"증가량 초과 (최대 +{limits['max_increase']})",
                                }
                                warnings.append(f"[REJECT] {key}: {value} → 비합리적 증가량")
                                continue
                            if "max_decrease" in limits and change < limits["max_decrease"]:
                                rejected[key] = {
                                    "proposed": value,
                                    "reason": f"감소량 초과 (최대 {limits['max_decrease']})",
                                }
                                warnings.append(f"[REJECT] {key}: {value} → 비합리적 감소량")
                                continue
                            if "max_change" in limits and abs(change) > limits["max_change"]:
                                rejected[key] = {
                                    "proposed": value,
                                    "reason": f"변화량 초과 (최대 ±{limits['max_change']})",
                                }
                                warnings.append(f"[REJECT] {key}: {value} → 변화량 초과")
                                continue
                except ValueError:
                    pass

            if key == "realm" and current_hud:
                current_realm = current_hud.get("realm", "")
                if value != current_realm:
                    warnings.append(f"[INFO] 경지 변화 감지: {current_realm} → {value}")

            if key == "causal_injuries" and current_hud:
                current_injury = current_hud.get("causal_injuries", "")
                if current_injury and "중상" in str(current_injury) and "정상" in str(value):
                    warnings.append(f"[WARN] 부상 급회복: {current_injury} → {value} (서사적 근거 필요)")

            applied[key] = value

        is_approved = len(rejected) == 0

        return {"approved": is_approved, "applied_updates": applied, "rejected_updates": rejected, "warnings": warnings}
