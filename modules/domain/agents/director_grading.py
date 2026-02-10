"""
[V64 P2-1] Director GradingSystem — 원고 품질 등급화 전담 모듈

Director God Object 분해의 두 번째 단계.
원고 품질 평가, 등급 부여, 수정 가이드 생성을 담당.
순수 데이터 가공 — LLM 호출 없음, BaseAgent 의존 없음.
"""


class DirectorGradingSystem:
    """
    [V64 P2-1] Director에서 분리된 등급화 모듈

    담당:
    - grade_manuscript_v59(): 원고 품질 등급화 (A/B/C/D)
    - generate_revision_guide_v59(): 등급 기반 수정 가이드 생성
    - format_revision_report_v59(): 사람이 읽기 좋은 리포트 포맷
    """

    # [V59] 등급별 기준 정의
    QUALITY_GRADES = {
        'A': {
            'min_score': 85,
            'label': '출판 수준',
            'description': '수정 없이 바로 게재 가능한 수준',
            'action': 'PUBLISH_READY'
        },
        'B': {
            'min_score': 70,
            'label': '게재 가능',
            'description': '경미한 수정 후 게재 가능',
            'action': 'MINOR_REVISION'
        },
        'C': {
            'min_score': 50,
            'label': '수정 필요',
            'description': '상당한 수정 후 재검토 필요',
            'action': 'MAJOR_REVISION'
        },
        'D': {
            'min_score': 0,
            'label': '재작성 필요',
            'description': '근본적인 재작성 필요',
            'action': 'REWRITE'
        }
    }

    # [V63.2] 품질 항목별 가중치 — 일관성 강화
    QUALITY_WEIGHTS = {
        'structure': 0.15,      # 구조적 완성도
        'prose': 0.15,          # 문장력 (0.20→0.15)
        'consistency': 0.30,    # 설정 일관성 (0.20→0.30)
        'engagement': 0.20,     # 독자 몰입도 (0.25→0.20)
        'commercial': 0.20,     # 상업적 매력
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
        base_score = validation_result.get('total_score', 0)
        breakdown = validation_result.get('breakdown', {})

        # 2. 세부 점수 분석
        item_scores = {}
        for category, weight in self.QUALITY_WEIGHTS.items():
            related_score = self._extract_category_score(breakdown, category)
            item_scores[category] = {
                'score': related_score,
                'weight': weight,
                'weighted_score': related_score * weight
            }

        # 3. 가중 총점 계산
        weighted_total = sum(item['weighted_score'] for item in item_scores.values())

        # 4. 등급 결정
        grade = 'D'
        for g, criteria in self.QUALITY_GRADES.items():
            if weighted_total >= criteria['min_score']:
                grade = g
                break

        grade_info = self.QUALITY_GRADES[grade]

        # 5. 강점/약점 추출
        strengths = []
        weaknesses = []
        for category, data in item_scores.items():
            if data['score'] >= 80:
                strengths.append({
                    'category': category,
                    'score': data['score'],
                    'note': self._get_strength_description(category)
                })
            elif data['score'] < 60:
                weaknesses.append({
                    'category': category,
                    'score': data['score'],
                    'note': self._get_weakness_description(category)
                })

        # 6. 수정 가이드 생성
        revision_guide = self.generate_revision_guide_v59(
            grade=grade,
            item_scores=item_scores,
            weaknesses=weaknesses,
            validation_result=validation_result
        )

        return {
            'grade': grade,
            'score': round(weighted_total, 1),
            'label': grade_info['label'],
            'description': grade_info['description'],
            'action': grade_info['action'],
            'breakdown': item_scores,
            'revision_guide': revision_guide,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'ep_num': ep_num
        }

    def _extract_category_score(self, breakdown: dict, category: str) -> float:
        """validation breakdown에서 카테고리별 점수 추출"""
        category_mapping = {
            'structure': ['scene_completeness', 'scope_overflow', 'required_scenes'],
            'prose': ['prose_rhythm', 'vocabulary_diversity', 'show_dont_tell'],
            'consistency': ['character_consistency', 'relationship_consistency', 'continuity'],
            'engagement': ['emotion_arc', 'commercial_appeal', 'cliffhanger'],
            'commercial': ['commercial_appeal', 'pattern_diversity'],
        }

        related_items = category_mapping.get(category, [])
        scores = []

        for item_name in related_items:
            if item_name in breakdown:
                item_data = breakdown[item_name]
                if isinstance(item_data, dict):
                    score = item_data.get('score', 0)
                    max_score = item_data.get('max', 1)
                    scores.append((score / max_score) * 100 if max_score > 0 else 0)

        return sum(scores) / len(scores) if scores else 50

    def _get_strength_description(self, category: str) -> str:
        """강점 설명 반환"""
        descriptions = {
            'structure': '씬 구성과 전개가 탄탄합니다',
            'prose': '문장력이 유려하고 읽기 좋습니다',
            'consistency': '설정 일관성이 잘 유지됩니다',
            'engagement': '독자 몰입도가 높습니다',
            'commercial': '상업적 매력이 있습니다',
        }
        return descriptions.get(category, '양호한 수준입니다')

    def _get_weakness_description(self, category: str) -> str:
        """약점 설명 반환"""
        descriptions = {
            'structure': '씬 구성이 불균형하거나 누락이 있습니다',
            'prose': '문장이 단조롭거나 묘사가 부족합니다',
            'consistency': '설정 모순이나 불일치가 있습니다',
            'engagement': '독자 몰입을 방해하는 요소가 있습니다',
            'commercial': '상업적 매력 요소가 부족합니다',
        }
        return descriptions.get(category, '개선이 필요합니다')

    def generate_revision_guide_v59(self, grade: str, item_scores: dict,
                                     weaknesses: list, validation_result: dict) -> dict:
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

        if grade == 'D':
            priority = 'CRITICAL'
            tasks.append({
                'type': 'rewrite',
                'description': '원고 전체를 재구성해야 합니다',
                'detail': 'Blueprint를 다시 확인하고 기본 구조부터 재설계하세요'
            })
        elif grade == 'C':
            priority = 'HIGH'
            tasks.append({
                'type': 'major_revision',
                'description': '주요 문제점 수정이 필요합니다',
                'detail': '아래 약점 항목들을 집중 개선하세요'
            })
        elif grade == 'B':
            priority = 'MEDIUM'
            tasks.append({
                'type': 'minor_revision',
                'description': '경미한 수정으로 품질 향상 가능합니다',
                'detail': '아래 제안사항을 참고하여 다듬으세요'
            })
        else:  # A
            priority = 'LOW'
            tasks.append({
                'type': 'polish',
                'description': '최종 교정 수준의 검토만 필요합니다',
                'detail': '오탈자나 미세한 표현 개선 위주로 확인하세요'
            })

        for weakness in weaknesses:
            category = weakness.get('category', '')
            score = weakness.get('score', 0)

            revision_task = self._generate_category_revision(category, score, validation_result)
            if revision_task:
                tasks.append(revision_task)

            example = self._get_revision_example(category)
            if example:
                examples.append(example)

        effort_map = {
            'D': '4시간 이상 소요 예상',
            'C': '2-4시간 소요 예상',
            'B': '30분-1시간 소요 예상',
            'A': '15분 내외 소요 예상'
        }

        return {
            'priority': priority,
            'grade': grade,
            'tasks': tasks[:10],
            'examples': examples[:5],
            'estimated_effort': effort_map.get(grade, '알 수 없음'),
            'focus_areas': [w['category'] for w in weaknesses[:3]]
        }

    def _generate_category_revision(self, category: str, score: float, validation_result: dict) -> dict:
        """카테고리별 수정 지침 생성"""
        revisions = {
            'structure': {
                'type': 'structure_fix',
                'description': '씬 구조 개선',
                'details': [
                    'Blueprint의 6개 씬이 모두 반영되었는지 확인',
                    '각 씬의 분량이 균등하게 배분되었는지 검토',
                    '씬 전환이 자연스러운지 점검'
                ]
            },
            'prose': {
                'type': 'prose_improvement',
                'description': '문장력 향상',
                'details': [
                    '직접 감정 서술("슬펐다") → 묘사로 전환',
                    '문장 시작 패턴 다양화 (연속 3문장 같은 시작 금지)',
                    '감각 묘사 추가 (시각 외 청각, 촉각 등)'
                ]
            },
            'consistency': {
                'type': 'consistency_fix',
                'description': '설정 일관성 수정',
                'details': [
                    '직전 화 엔딩과 현재 화 시작의 연결 확인',
                    'NPC 관계 상태 변화의 정당성 검토',
                    '아이템/무공 사용의 획득 시점 확인'
                ]
            },
            'engagement': {
                'type': 'engagement_boost',
                'description': '몰입도 강화',
                'details': [
                    '감정 전환의 자연스러운 흐름 설계',
                    '긴장감 있는 갈등 요소 추가',
                    'Cliffhanger 엔딩 강화'
                ]
            },
            'commercial': {
                'type': 'commercial_appeal',
                'description': '상업적 매력 강화',
                'details': [
                    '사이다 요소 또는 복선 추가',
                    '다음 화 기대감을 높이는 떡밥 배치',
                    '독자 감정 반응 유발 포인트 삽입'
                ]
            }
        }

        base_revision = revisions.get(category, {})
        if not base_revision:
            return None

        if score < 40:
            base_revision['urgency'] = 'CRITICAL'
            base_revision['note'] = '이 항목의 대폭 개선 없이는 게재 불가'
        elif score < 60:
            base_revision['urgency'] = 'HIGH'
            base_revision['note'] = '상당한 수정 필요'
        else:
            base_revision['urgency'] = 'MEDIUM'
            base_revision['note'] = '다듬기 수준의 개선 권장'

        return base_revision

    def _get_revision_example(self, category: str) -> dict:
        """카테고리별 수정 예시"""
        examples = {
            'structure': {
                'before': '갑자기 장면이 전환되어 다른 장소에 있었다.',
                'after': '한참을 걸은 끝에 객잔의 불빛이 눈에 들어왔다. 주인공은 지친 발걸음을 옮겨 문을 밀었다.',
                'note': '장면 전환에 시간/공간의 흐름을 명시'
            },
            'prose': {
                'before': '그는 슬펐다. 정말 슬펐다. 너무 슬펐다.',
                'after': '어깨가 축 처졌다. 주먹이 부들부들 떨렸고, 눈앞이 흐릿해졌다.',
                'note': '감정을 행동/신체 반응으로 묘사'
            },
            'consistency': {
                'before': '(직전 화 부상) → 멀쩡하게 전력 질주했다.',
                'after': '(직전 화 부상) → 부상당한 다리를 끌며 겨우 뛰었다. 통증이 밀려왔지만 멈출 수 없었다.',
                'note': '상태의 연속성 유지'
            },
            'engagement': {
                'before': '무사히 해결되어 잠들었다.',
                'after': '해결된 줄 알았다. 그때, 창문 너머로 낯선 그림자가 스쳐 지나갔다.',
                'note': 'Cliffhanger로 긴장감 유지'
            },
            'commercial': {
                'before': '다음에 또 보자고 인사했다.',
                'after': '"다음에 보자. 그때...내가 숨긴 비밀을 알려주마." 의미심장한 미소가 번졌다.',
                'note': '떡밥/복선으로 기대감 유발'
            }
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
            f"\n{'='*60}",
            f"📊 [V59] 품질 등급 리포트 - 제{grade_result.get('ep_num', '?')}화",
            f"{'='*60}\n",
        ]

        grade = grade_result.get('grade', '?')
        score = grade_result.get('score', 0)
        label = grade_result.get('label', '')

        grade_emoji = {'A': '🏆', 'B': '✅', 'C': '⚠️', 'D': '❌'}.get(grade, '❓')
        lines.append(f"{grade_emoji} 등급: {grade} ({label})")
        lines.append(f"   점수: {score}/100")
        lines.append(f"   판정: {grade_result.get('description', '')}\n")

        strengths = grade_result.get('strengths', [])
        if strengths:
            lines.append("✨ 강점:")
            for s in strengths[:3]:
                lines.append(f"   - {s['category']}: {s['note']} ({s['score']}점)")
            lines.append("")

        weaknesses = grade_result.get('weaknesses', [])
        if weaknesses:
            lines.append("⚠️ 개선 필요:")
            for w in weaknesses[:3]:
                lines.append(f"   - {w['category']}: {w['note']} ({w['score']}점)")
            lines.append("")

        revision = grade_result.get('revision_guide', {})
        if revision:
            lines.append(f"📝 수정 가이드 (우선순위: {revision.get('priority', '?')})")
            lines.append(f"   예상 소요: {revision.get('estimated_effort', '?')}")
            lines.append("")

            tasks = revision.get('tasks', [])
            for i, task in enumerate(tasks[:5], 1):
                lines.append(f"   {i}. [{task.get('type', '?')}] {task.get('description', '')}")
                if task.get('details'):
                    for detail in task['details'][:3]:
                        lines.append(f"      - {detail}")

            examples = revision.get('examples', [])
            if examples:
                lines.append("\n📚 수정 예시:")
                for ex in examples[:2]:
                    if ex:
                        lines.append(f"   Before: {ex.get('before', '')[:50]}...")
                        lines.append(f"   After:  {ex.get('after', '')[:50]}...")
                        lines.append(f"   💡 {ex.get('note', '')}")
                        lines.append("")

        lines.append(f"{'='*60}\n")

        return "\n".join(lines)
