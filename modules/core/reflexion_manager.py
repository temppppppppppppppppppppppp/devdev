"""
[Phase 5.2.2] Reflexion System
과거 실패 패턴을 학습하여 반복 방지

Reflexion: 실패 → 분석 → 기억 → 회피
"""
import json
import logging
from typing import Dict, List, Any
from datetime import datetime


class ReflexionManager:
    """
    과거 실패 패턴 학습 및 관리

    기능:
    1. 실패 패턴 저장
    2. 빈도 추적
    3. 프롬프트 생성 (Writer/Architect에 주입)
    """

    def __init__(self, context) -> None:
        """
        Args:
            context: ProjectContext 객체
        """
        self.context = context
        self.memory = []  # 메모리 캐시
        self.loaded = False

    def load_memory(self) -> None:
        """DB에서 실패 메모리 로드"""
        if self.loaded:
            return

        try:
            # reflexion_memory 테이블에서 로드
            rows = self.context.db.execute_query(
                "SELECT pattern_type, description, frequency, solution, first_seen, last_seen FROM reflexion_memory ORDER BY frequency DESC"
            )

            self.memory = []
            for row in rows:
                self.memory.append({
                    'pattern_type': row[0],
                    'description': row[1],
                    'frequency': row[2],
                    'solution': row[3],
                    'first_seen': row[4],
                    'last_seen': row[5]
                })

            self.loaded = True
            logging.warning(f"📚 [Reflexion] 과거 실패 패턴 {len(self.memory)}개 로드됨")

        except Exception as e:
            # 테이블이 없거나 오류 시 빈 메모리
            logging.warning(f"⚠️ [Reflexion] 메모리 로드 실패 (첫 실행일 수 있음): {e}")
            self.memory = []
            self.loaded = True

    def record_failure(self, ep_num: int, failure_type: str, description: str, solution: str = ""):
        """
        실패 패턴 기록

        Args:
            ep_num: 에피소드 번호
            failure_type: 실패 유형 ('blocking', 'scoring', 'consistency', etc.)
            description: 실패 내용
            solution: 해결 방법 (옵션)
        """
        self.load_memory()

        # 패턴 식별 (간단한 키워드 기반)
        pattern_key = self._identify_pattern(description)

        # 기존 패턴 찾기
        existing = None
        for item in self.memory:
            if item['pattern_type'] == pattern_key:
                existing = item
                break

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if existing:
            # 빈도 증가
            new_frequency = existing['frequency'] + 1

            self.context.db.execute_update(
                """UPDATE reflexion_memory
                   SET frequency = ?, last_seen = ?, last_ep = ?
                   WHERE pattern_type = ?""",
                (new_frequency, timestamp, ep_num, pattern_key)
            )
            # Commit to persist frequency update
            self.context.db.conn.commit()

            existing['frequency'] = new_frequency
            existing['last_seen'] = timestamp

            logging.info(f"📝 [Reflexion] 패턴 '{pattern_key}' 빈도 증가: {new_frequency}회")

        else:
            # 새 패턴 추가
            self.context.db.execute_update(
                """INSERT INTO reflexion_memory
                   (pattern_type, description, frequency, solution, first_seen, last_seen, first_ep, last_ep)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (pattern_key, description, 1, solution, timestamp, timestamp, ep_num, ep_num)
            )
            # Commit to persist new pattern
            self.context.db.conn.commit()

            new_pattern = {
                'pattern_type': pattern_key,
                'description': description,
                'frequency': 1,
                'solution': solution,
                'first_seen': timestamp,
                'last_seen': timestamp
            }
            self.memory.append(new_pattern)

            logging.info(f"✨ [Reflexion] 새 패턴 기록: '{pattern_key}'")

    def _identify_pattern(self, description: str) -> str:
        """
        실패 내용에서 패턴 키 추출 (간단한 키워드 기반)

        Args:
            description: 실패 설명

        Returns:
            str: 패턴 키
        """
        # 키워드 매핑
        patterns = {
            '사망': 'dead_npc_resurrection',
            '재등장': 'dead_npc_resurrection',
            '경외': 'relationship_regression',
            '무시': 'relationship_regression',
            '관계 역행': 'relationship_regression',
            '장비': 'equipment_inconsistency',
            'NPC 장비': 'equipment_inconsistency',
            '미획득': 'unowned_item_usage',
            '아이템': 'unowned_item_usage',
            '미래': 'future_leak',
            '누수': 'future_leak',
            'HUD': 'hud_contradiction',
            '모순': 'hud_contradiction',
            '정당화': 'justification_missing',
            '클리셰': 'cliche_overuse',
        }

        for keyword, pattern_key in patterns.items():
            if keyword in description:
                return pattern_key

        # 매칭 안되면 일반 실패로
        return 'generic_failure'

    def get_prompt_injection(self, min_frequency: int = 2) -> str:
        """
        Writer/Architect 프롬프트에 주입할 과거 실패 패턴 생성

        Args:
            min_frequency: 최소 빈도 (이 이상만 주입)

        Returns:
            str: 프롬프트 문자열
        """
        self.load_memory()

        # 빈도 높은 패턴 필터링
        frequent_patterns = [
            p for p in self.memory
            if p['frequency'] >= min_frequency
        ]

        if not frequent_patterns:
            return ""

        # 상위 5개만
        top_patterns = sorted(frequent_patterns, key=lambda x: x['frequency'], reverse=True)[:5]

        prompt_parts = [
            "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "\n🧠 [REFLEXION: 과거 실패 패턴 - 반드시 회피]",
            "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
            "\n이 프로젝트에서 과거에 반복된 실패 패턴입니다.",
            "동일한 실수를 절대 반복하지 마십시오.\n"
        ]

        for i, pattern in enumerate(top_patterns, 1):
            prompt_parts.append(f"\n[실패 패턴 {i}] {pattern['description']}")
            prompt_parts.append(f"  빈도: {pattern['frequency']}회")
            if pattern.get('solution'):
                prompt_parts.append(f"  해결책: {pattern['solution']}")
            prompt_parts.append("")

        prompt_parts.append("\n⚠️ 위 패턴을 피하기 위해 작성 전 한 번 더 확인하십시오.")
        prompt_parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

        return "\n".join(prompt_parts)

    def get_pattern_summary(self) -> str:
        """
        패턴 요약 (디버깅/모니터링용)

        Returns:
            str: 패턴 요약 문자열
        """
        self.load_memory()

        if not self.memory:
            return "과거 실패 패턴 없음 (첫 실행 또는 완벽한 프로젝트)"

        summary_parts = [f"총 {len(self.memory)}개 패턴 기록됨:\n"]

        for pattern in sorted(self.memory, key=lambda x: x['frequency'], reverse=True)[:10]:
            summary_parts.append(
                f"- {pattern['pattern_type']}: {pattern['frequency']}회 ({pattern['description'][:50]}...)"
            )

        return "\n".join(summary_parts)
