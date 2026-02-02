"""
[V50.1] Tension Curve Manager
긴장도 곡선 관리 - Arc/Episode별 긴장도 추적 및 최적화

기능:
1. 에피소드별 긴장도 수치화 (0-100)
2. 긴장도 패턴 분류: REST → LOW → RISING → HIGH → CLIMAX → FALLING
3. Arc 내 긴장도 곡선 검증
4. 연속 고조/이완 방지
5. 클라이맥스 타이밍 최적화

사용:
    manager = TensionCurveManager()
    manager.record_tension(arc=1, episode=1, content="...")
    validation = manager.validate_arc_curve(arc=1)
    suggestion = manager.suggest_next_tension(arc=1, current_ep=3)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import re


class TensionLevel(Enum):
    """긴장도 수준"""
    REST = (0, 20, "휴식")      # 평화로운 일상
    LOW = (21, 35, "저조")      # 가벼운 긴장
    RISING = (36, 55, "상승")   # 긴장 고조 중
    HIGH = (56, 75, "고조")     # 높은 긴장
    CLIMAX = (76, 95, "절정")   # 클라이맥스
    FALLING = (96, 100, "하강") # 긴장 해소 (특수: 절정 직후)

    @property
    def min_score(self) -> int:
        return self.value[0]

    @property
    def max_score(self) -> int:
        return self.value[1]

    @property
    def name_kr(self) -> str:
        return self.value[2]

    @classmethod
    def from_score(cls, score: int) -> "TensionLevel":
        """점수로부터 긴장도 수준 반환"""
        # FALLING은 특수 케이스로 직접 지정해야 함
        if score <= 20:
            return cls.REST
        elif score <= 35:
            return cls.LOW
        elif score <= 55:
            return cls.RISING
        elif score <= 75:
            return cls.HIGH
        else:
            return cls.CLIMAX

    def intensity_index(self) -> int:
        """긴장 강도 인덱스 (0=REST, 4=CLIMAX)"""
        order = [TensionLevel.REST, TensionLevel.LOW, TensionLevel.RISING,
                 TensionLevel.HIGH, TensionLevel.CLIMAX, TensionLevel.FALLING]
        return order.index(self)


@dataclass
class TensionRecord:
    """긴장도 기록"""
    arc: int
    episode: int
    score: int  # 0-100
    level: TensionLevel
    keywords_detected: List[str] = field(default_factory=list)
    scene_types: List[str] = field(default_factory=list)
    notes: str = ""


class TensionCurveManager:
    """
    [V50.1] 긴장도 곡선 관리자

    Arc 내 긴장도 흐름을 추적하고 최적화하여
    독자의 몰입도를 극대화합니다.
    """

    # ═══════════════════════════════════════════════════════════════
    # 긴장도 감지 키워드 (장르 공통)
    # ═══════════════════════════════════════════════════════════════

    TENSION_KEYWORDS = {
        "climax": {
            "keywords": [
                "결전", "최후", "대결", "폭발", "절체절명", "목숨을 걸",
                "죽음", "최종", "마지막", "결말", "종말", "파멸", "멸망",
                "사활", "생사", "운명의", "숙명", "피할 수 없", "각오"
            ],
            "weight": 90
        },
        "high": {
            "keywords": [
                "긴장", "위기", "위험", "충돌", "대치", "추격", "전투",
                "격돌", "습격", "포위", "함정", "배신", "발각", "급습",
                "분노", "살기", "적의", "위협", "공격", "방어"
            ],
            "weight": 70
        },
        "rising": {
            "keywords": [
                "의심", "불안", "조짐", "암시", "접근", "추적", "감시",
                "경계", "수상", "이상", "낌새", "기색", "분위기", "조심",
                "눈치", "탐색", "조사", "단서", "정보", "계획"
            ],
            "weight": 50
        },
        "low": {
            "keywords": [
                "일상", "휴식", "대화", "준비", "이동", "수련", "연습",
                "식사", "숙소", "여정", "산책", "구경", "쇼핑", "정비",
                "회의", "상담", "논의", "설명", "소개", "만남"
            ],
            "weight": 30
        },
        "rest": {
            "keywords": [
                "평화", "안정", "회복", "웃음", "농담", "유머", "화기애애",
                "한가", "여유", "편안", "고요", "잠", "꿈", "추억",
                "감사", "기쁨", "축하", "잔치", "연회", "휴양"
            ],
            "weight": 15
        }
    }

    # 씬 타입별 기본 긴장도
    SCENE_TYPE_TENSION = {
        "전투": 75,
        "비무": 70,
        "추격": 70,
        "대치": 65,
        "협상": 50,
        "탐색": 45,
        "수련": 30,
        "대화": 25,
        "이동": 20,
        "휴식": 15,
        "회상": 35,
        "독백": 40,
    }

    # ═══════════════════════════════════════════════════════════════
    # 곡선 규칙
    # ═══════════════════════════════════════════════════════════════

    # Arc 내 규칙
    MAX_CONSECUTIVE_CLIMAX = 2      # 연속 절정 최대 2화
    MAX_CONSECUTIVE_REST = 3        # 연속 휴식 최대 3화
    MAX_CONSECUTIVE_HIGH = 3        # 연속 고조 최대 3화
    MIN_RISING_BEFORE_CLIMAX = 1    # 절정 전 최소 1화 상승

    # Arc 구조 규칙
    IDEAL_CLIMAX_POSITION = 0.8     # Arc의 80% 지점에서 절정 권장
    CLIMAX_POSITION_TOLERANCE = 0.15 # ±15% 허용

    def __init__(self):
        self.records: Dict[int, List[TensionRecord]] = {}  # {arc: [records]}
        self.arc_metadata: Dict[int, Dict] = {}  # {arc: {ep_count, climax_ep, ...}}

    def record_tension(
        self,
        arc: int,
        episode: int,
        content: str,
        manual_score: int = None,
        scene_types: List[str] = None
    ) -> TensionRecord:
        """
        에피소드 긴장도 기록

        Args:
            arc: Arc 번호
            episode: 에피소드 번호
            content: 에피소드 내용 (블루프린트 또는 원고)
            manual_score: 수동 지정 점수 (None이면 자동 분석)
            scene_types: 씬 타입 목록 (선택적)

        Returns:
            TensionRecord
        """
        if manual_score is not None:
            score = max(0, min(100, manual_score))
            keywords = []
        else:
            score, keywords = self._analyze_tension(content)

        # 씬 타입 기반 보정
        if scene_types:
            scene_avg = sum(
                self.SCENE_TYPE_TENSION.get(st, 40)
                for st in scene_types
            ) / len(scene_types)
            # 키워드 분석과 씬 타입의 가중 평균
            score = int(score * 0.6 + scene_avg * 0.4)

        level = TensionLevel.from_score(score)

        record = TensionRecord(
            arc=arc,
            episode=episode,
            score=score,
            level=level,
            keywords_detected=keywords,
            scene_types=scene_types or []
        )

        if arc not in self.records:
            self.records[arc] = []

        # 같은 에피소드 기록이 있으면 교체
        self.records[arc] = [r for r in self.records[arc] if r.episode != episode]
        self.records[arc].append(record)
        self.records[arc].sort(key=lambda r: r.episode)

        return record

    def _analyze_tension(self, content: str) -> Tuple[int, List[str]]:
        """
        텍스트에서 긴장도 분석

        Returns:
            (score, detected_keywords)
        """
        if not content:
            return (30, [])

        content_lower = content.lower()
        detected = []
        weighted_scores = []

        for level_name, config in self.TENSION_KEYWORDS.items():
            for keyword in config["keywords"]:
                count = content_lower.count(keyword)
                if count > 0:
                    detected.append(keyword)
                    # 키워드당 가중치 (중복 등장 시 감소)
                    for i in range(min(count, 3)):
                        weight_decay = 1.0 / (i + 1)
                        weighted_scores.append(config["weight"] * weight_decay)

        if not weighted_scores:
            return (35, [])  # 기본값: LOW

        # 상위 5개 키워드의 가중 평균
        weighted_scores.sort(reverse=True)
        top_scores = weighted_scores[:5]
        avg_score = sum(top_scores) / len(top_scores)

        # 키워드 다양성 보너스
        diversity_bonus = min(len(detected) * 2, 10)

        final_score = min(100, int(avg_score + diversity_bonus))
        return (final_score, detected[:10])  # 최대 10개 키워드 반환

    def validate_arc_curve(self, arc: int) -> Dict[str, Any]:
        """
        Arc 긴장도 곡선 검증

        Args:
            arc: Arc 번호

        Returns:
            {
                "valid": bool,
                "score": int (0-100),
                "violations": [],
                "warnings": [],
                "curve_shape": str,
                "suggestion": str
            }
        """
        if arc not in self.records or not self.records[arc]:
            return {
                "valid": True,
                "score": 50,
                "violations": [],
                "warnings": ["긴장도 기록 없음"],
                "curve_shape": "unknown",
                "suggestion": ""
            }

        records = sorted(self.records[arc], key=lambda r: r.episode)
        violations = []
        warnings = []

        # ═══════════════════════════════════════════════════════════════
        # 1. 연속 패턴 검증
        # ═══════════════════════════════════════════════════════════════
        consecutive_check = self._check_consecutive_patterns(records)
        violations.extend(consecutive_check["violations"])
        warnings.extend(consecutive_check["warnings"])

        # ═══════════════════════════════════════════════════════════════
        # 2. 클라이맥스 위치 검증
        # ═══════════════════════════════════════════════════════════════
        climax_check = self._check_climax_position(records)
        if climax_check.get("violation"):
            violations.append(climax_check["violation"])
        if climax_check.get("warning"):
            warnings.append(climax_check["warning"])

        # ═══════════════════════════════════════════════════════════════
        # 3. 곡선 형태 분석
        # ═══════════════════════════════════════════════════════════════
        curve_shape = self._analyze_curve_shape(records)

        # ═══════════════════════════════════════════════════════════════
        # 4. 점수 계산
        # ═══════════════════════════════════════════════════════════════
        base_score = 100
        base_score -= len(violations) * 20
        base_score -= len(warnings) * 5

        # 곡선 형태 보너스/감점
        shape_bonus = {
            "rising_climax": 10,
            "double_peak": 5,
            "wave": 0,
            "flat": -15,
            "chaotic": -10,
            "front_loaded": -10,
        }
        base_score += shape_bonus.get(curve_shape, 0)
        final_score = max(0, min(100, base_score))

        # 제안 생성
        suggestion = self._generate_curve_suggestion(records, violations, warnings, curve_shape)

        return {
            "valid": len(violations) == 0,
            "score": final_score,
            "violations": violations,
            "warnings": warnings,
            "curve_shape": curve_shape,
            "suggestion": suggestion,
            "records_count": len(records)
        }

    def _check_consecutive_patterns(self, records: List[TensionRecord]) -> Dict[str, Any]:
        """연속 패턴 검증"""
        violations = []
        warnings = []

        if len(records) < 2:
            return {"violations": [], "warnings": []}

        # 연속 카운트
        consecutive_climax = 0
        consecutive_rest = 0
        consecutive_high = 0

        for i, record in enumerate(records):
            level = record.level

            # CLIMAX 연속
            if level == TensionLevel.CLIMAX:
                consecutive_climax += 1
                consecutive_rest = 0
                consecutive_high = 0
                if consecutive_climax > self.MAX_CONSECUTIVE_CLIMAX:
                    violations.append({
                        "type": "consecutive_climax",
                        "episode": record.episode,
                        "message": f"절정이 {consecutive_climax}화 연속 - 독자 피로 유발"
                    })
            # REST 연속
            elif level == TensionLevel.REST:
                consecutive_rest += 1
                consecutive_climax = 0
                consecutive_high = 0
                if consecutive_rest > self.MAX_CONSECUTIVE_REST:
                    warnings.append({
                        "type": "consecutive_rest",
                        "episode": record.episode,
                        "message": f"휴식이 {consecutive_rest}화 연속 - 지루함 유발 가능"
                    })
            # HIGH 연속
            elif level == TensionLevel.HIGH:
                consecutive_high += 1
                consecutive_climax = 0
                consecutive_rest = 0
                if consecutive_high > self.MAX_CONSECUTIVE_HIGH:
                    warnings.append({
                        "type": "consecutive_high",
                        "episode": record.episode,
                        "message": f"고조가 {consecutive_high}화 연속 - 긴장감 마비 가능"
                    })
            else:
                consecutive_climax = 0
                consecutive_rest = 0
                consecutive_high = 0

        return {"violations": violations, "warnings": warnings}

    def _check_climax_position(self, records: List[TensionRecord]) -> Dict[str, Any]:
        """클라이맥스 위치 검증"""
        result = {}

        climax_episodes = [r.episode for r in records if r.level == TensionLevel.CLIMAX]

        if not climax_episodes:
            result["warning"] = {
                "type": "no_climax",
                "message": "Arc에 절정(CLIMAX) 에피소드가 없음"
            }
            return result

        total_eps = len(records)
        if total_eps < 3:
            return result

        # 마지막 절정의 상대적 위치
        last_climax_idx = max(
            i for i, r in enumerate(records)
            if r.level == TensionLevel.CLIMAX
        )
        relative_position = (last_climax_idx + 1) / total_eps

        ideal_min = self.IDEAL_CLIMAX_POSITION - self.CLIMAX_POSITION_TOLERANCE
        ideal_max = self.IDEAL_CLIMAX_POSITION + self.CLIMAX_POSITION_TOLERANCE

        if relative_position < ideal_min - 0.1:
            result["violation"] = {
                "type": "early_climax",
                "position": relative_position,
                "message": f"절정이 너무 이름 (Arc의 {relative_position:.0%} 지점) - 후반부가 늘어짐"
            }
        elif relative_position < ideal_min:
            result["warning"] = {
                "type": "slightly_early_climax",
                "position": relative_position,
                "message": f"절정이 약간 이름 (Arc의 {relative_position:.0%} 지점)"
            }

        return result

    def _analyze_curve_shape(self, records: List[TensionRecord]) -> str:
        """곡선 형태 분석"""
        if len(records) < 3:
            return "unknown"

        scores = [r.score for r in records]
        n = len(scores)

        # 평균 및 변동성
        avg = sum(scores) / n
        variance = sum((s - avg) ** 2 for s in scores) / n

        # 추세 분석
        first_third = sum(scores[:n//3]) / max(1, n//3)
        last_third = sum(scores[-(n//3):]) / max(1, n//3)

        # 피크 위치
        max_idx = scores.index(max(scores))
        relative_peak = max_idx / (n - 1) if n > 1 else 0.5

        # 형태 판정
        if variance < 100:
            return "flat"  # 변화 거의 없음
        elif relative_peak < 0.3:
            return "front_loaded"  # 앞부분에 피크
        elif relative_peak > 0.6 and last_third > first_third:
            return "rising_climax"  # 이상적: 상승 후 절정
        elif scores.count(max(scores)) > 1 or (max(scores[:n//2]) > 60 and max(scores[n//2:]) > 60):
            return "double_peak"  # 이중 피크
        elif variance > 400:
            return "chaotic"  # 너무 들쭉날쭉
        else:
            return "wave"  # 물결 형태

    def _generate_curve_suggestion(
        self,
        records: List[TensionRecord],
        violations: List[Dict],
        warnings: List[Dict],
        curve_shape: str
    ) -> str:
        """곡선 개선 제안 생성"""
        suggestions = []

        if curve_shape == "flat":
            suggestions.append("긴장도 변화가 부족합니다. 위기/갈등 장면을 추가하세요.")
        elif curve_shape == "front_loaded":
            suggestions.append("클라이맥스가 너무 앞에 있습니다. 후반부에 더 큰 위기를 배치하세요.")
        elif curve_shape == "chaotic":
            suggestions.append("긴장도가 너무 들쭉날쭉합니다. 점진적인 상승/하강을 유지하세요.")

        for v in violations:
            if v.get("type") == "consecutive_climax":
                suggestions.append("연속 절정 사이에 짧은 휴식/정리 장면을 삽입하세요.")
            elif v.get("type") == "early_climax":
                suggestions.append("후반부에 더 큰 결전/반전을 배치하여 긴장감을 유지하세요.")

        for w in warnings:
            if w.get("type") == "consecutive_rest":
                suggestions.append("휴식 장면이 길어지고 있습니다. 작은 갈등/복선을 삽입하세요.")
            elif w.get("type") == "no_climax":
                suggestions.append("Arc 후반부에 결정적인 대결/전환점을 배치하세요.")

        return " ".join(suggestions) if suggestions else "긴장도 곡선이 적절합니다."

    def suggest_next_tension(self, arc: int, current_ep: int, arc_total_eps: int = 5) -> Dict[str, Any]:
        """
        다음 에피소드의 권장 긴장도 제안

        Args:
            arc: Arc 번호
            current_ep: 현재 에피소드 (다음 에피소드 = current_ep + 1)
            arc_total_eps: Arc 총 에피소드 수

        Returns:
            {
                "recommended_level": TensionLevel,
                "recommended_score_range": (min, max),
                "reason": str,
                "keywords_to_include": []
            }
        """
        next_ep = current_ep + 1
        relative_position = next_ep / arc_total_eps

        # 이전 기록 확인
        prev_records = []
        if arc in self.records:
            prev_records = [r for r in self.records[arc] if r.episode <= current_ep]
            prev_records.sort(key=lambda r: r.episode)

        # 직전 에피소드 긴장도
        prev_level = TensionLevel.LOW
        prev_score = 30
        if prev_records:
            prev_level = prev_records[-1].level
            prev_score = prev_records[-1].score

        # 위치 기반 권장 긴장도
        if relative_position >= 0.8:
            # Arc 끝: 절정 또는 하강
            if prev_level == TensionLevel.CLIMAX:
                recommended = TensionLevel.FALLING
                score_range = (20, 40)
                reason = "절정 직후 - 긴장 해소/정리 필요"
            else:
                recommended = TensionLevel.CLIMAX
                score_range = (80, 95)
                reason = "Arc 후반 - 클라이맥스 타이밍"
        elif relative_position >= 0.6:
            # Arc 후반: 고조 또는 절정 준비
            if prev_level in [TensionLevel.HIGH, TensionLevel.CLIMAX]:
                recommended = TensionLevel.CLIMAX
                score_range = (80, 95)
                reason = "긴장 고조 후 - 절정 돌입 적기"
            else:
                recommended = TensionLevel.HIGH
                score_range = (60, 75)
                reason = "Arc 후반 진입 - 긴장 고조 필요"
        elif relative_position >= 0.4:
            # Arc 중반: 상승 또는 고조
            recommended = TensionLevel.RISING
            score_range = (40, 55)
            reason = "Arc 중반 - 갈등 심화/복선 회수"
        else:
            # Arc 초반: 저조 또는 상승
            if prev_level == TensionLevel.REST:
                recommended = TensionLevel.LOW
                score_range = (25, 35)
                reason = "Arc 초반 - 상황 설정/복선 설치"
            else:
                recommended = TensionLevel.RISING
                score_range = (35, 45)
                reason = "Arc 초반 - 점진적 긴장 상승"

        # 연속 패턴 방지 보정
        if prev_records and len(prev_records) >= 2:
            recent_levels = [r.level for r in prev_records[-2:]]
            if all(l == TensionLevel.REST for l in recent_levels):
                recommended = TensionLevel.LOW
                score_range = (30, 40)
                reason = "휴식 연속 - 작은 갈등 삽입 권장"
            elif all(l == TensionLevel.CLIMAX for l in recent_levels):
                recommended = TensionLevel.FALLING
                score_range = (25, 40)
                reason = "절정 연속 - 휴식/정리 필수"

        # 권장 키워드
        keywords = self.TENSION_KEYWORDS.get(recommended.name.lower(), {}).get("keywords", [])[:5]

        return {
            "recommended_level": recommended,
            "recommended_level_kr": recommended.name_kr,
            "recommended_score_range": score_range,
            "reason": reason,
            "keywords_to_include": keywords,
            "next_episode": next_ep,
            "relative_position": relative_position
        }

    def get_arc_curve_data(self, arc: int) -> List[Dict]:
        """Arc 긴장도 곡선 데이터 반환"""
        if arc not in self.records:
            return []

        return [
            {
                "episode": r.episode,
                "score": r.score,
                "level": r.level.name,
                "level_kr": r.level.name_kr,
                "keywords": r.keywords_detected
            }
            for r in sorted(self.records[arc], key=lambda r: r.episode)
        ]

    def generate_tension_prompt(self, arc: int, next_ep: int, arc_total_eps: int = 5) -> str:
        """
        Writer/Architect용 긴장도 가이드 프롬프트 생성
        """
        suggestion = self.suggest_next_tension(arc, next_ep - 1, arc_total_eps)

        lines = [
            "",
            "=" * 50,
            "[V50.1 긴장도 곡선 가이드]",
            "=" * 50,
            f"현재 위치: Arc {arc}, 제 {next_ep}화 (Arc의 {suggestion['relative_position']:.0%} 지점)",
            "",
            f"권장 긴장도: {suggestion['recommended_level_kr']} ({suggestion['recommended_score_range'][0]}~{suggestion['recommended_score_range'][1]}점)",
            f"이유: {suggestion['reason']}",
            "",
            f"활용 권장 키워드: {', '.join(suggestion['keywords_to_include'])}",
            "=" * 50,
        ]

        # 이전 곡선 시각화 (간단한 ASCII)
        if arc in self.records and self.records[arc]:
            lines.append("")
            lines.append("지금까지의 긴장도 흐름:")
            for r in sorted(self.records[arc], key=lambda x: x.episode):
                bar_len = r.score // 5
                bar = "█" * bar_len + "░" * (20 - bar_len)
                lines.append(f"  Ep{r.episode}: {bar} {r.score} ({r.level.name_kr})")
            lines.append("")

        return "\n".join(lines)

    def load_from_blueprints(self, blueprints: List[Dict]) -> int:
        """
        블루프린트 목록에서 긴장도 분석 및 로드

        Args:
            blueprints: 블루프린트 리스트 [{ep_num, arc_no, integrated_scenario, ...}]

        Returns:
            로드된 기록 수
        """
        count = 0
        for bp in blueprints:
            if not isinstance(bp, dict):
                continue

            arc = bp.get("arc_no", 1)
            ep = bp.get("ep_num", 0)
            content = bp.get("integrated_scenario", "")

            if ep > 0 and content:
                self.record_tension(arc=arc, episode=ep, content=content)
                count += 1

        return count
