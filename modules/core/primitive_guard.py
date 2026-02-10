"""
[V60.96] 원시인 모드 금지어 Guard (장르별)
=========================================
world_origin == '원시인' + 장르별 적용
- 무협: 전체 금지
- 판타지: 지구 현대 기술/브랜드만 금지
- 헌터: 게임 용어만 주의
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class PrimitiveGuard:
    """원시인 모드 현대 용어 검증기 (장르별)"""

    _instance = None
    _data = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if PrimitiveGuard._data is None:
            self._load_data()

    def _load_data(self):
        """JSON 파일에서 금지어 데이터 로드"""
        json_path = Path(__file__).parent / "laws" / "primitive_forbidden.json"
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                PrimitiveGuard._data = json.load(f)
        except Exception as e:
            print(f"[PrimitiveGuard] JSON 로드 실패: {e}")
            PrimitiveGuard._data = {
                "genre_rules": {},
                "categories": {},
                "regex_patterns_by_genre": {},
                "prompt_injection_by_genre": {}
            }

    @property
    def data(self) -> Dict:
        return PrimitiveGuard._data or {}

    def get_genre_rule(self, genre: str) -> Dict:
        """장르별 규칙 반환"""
        return self.data.get("genre_rules", {}).get(genre, {
            "apply_level": "none",
            "blocked_categories": []
        })

    def get_blocked_categories(self, genre: str) -> List[str]:
        """장르별 차단 카테고리 목록"""
        rule = self.get_genre_rule(genre)
        blocked = rule.get("blocked_categories", [])
        if "ALL" in blocked:
            return list(self.data.get("categories", {}).keys())
        return blocked

    def get_forbidden_words_for_genre(self, genre: str) -> List[str]:
        """장르별 금지어 목록"""
        words = []
        blocked_cats = self.get_blocked_categories(genre)

        for cat_key, cat_data in self.data.get("categories", {}).items():
            # 카테고리가 차단 목록에 있거나, 카테고리의 genres에 해당 장르가 포함된 경우
            cat_genres = cat_data.get("genres", [])
            if cat_key in blocked_cats or genre in cat_genres:
                words.extend(cat_data.get("forbidden", []))

        return words

    def get_regex_patterns_for_genre(self, genre: str) -> List[Tuple[str, str]]:
        """장르별 regex 패턴 목록"""
        patterns = []
        genre_patterns = self.data.get("regex_patterns_by_genre", {}).get(genre, [])
        for item in genre_patterns:
            patterns.append((item["pattern"], item["category"]))
        return patterns

    def get_prompt_injection(self, genre: str, length: str = "medium") -> str:
        """장르별 프롬프트 주입 텍스트"""
        genre_prompts = self.data.get("prompt_injection_by_genre", {}).get(genre, {})
        return genre_prompts.get(length, "")

    def get_alternatives_for_genre(self, genre: str) -> Dict[str, str]:
        """장르별 대체 표현 사전"""
        alternatives = {}
        blocked_cats = self.get_blocked_categories(genre)

        for cat_key, cat_data in self.data.get("categories", {}).items():
            cat_genres = cat_data.get("genres", [])
            if cat_key in blocked_cats or genre in cat_genres:
                alternatives.update(cat_data.get("alternatives", {}))

        return alternatives

    def validate(self, text: str, genre: str = "wuxia") -> Tuple[str, List[Dict]]:
        """
        텍스트에서 현대 용어 검출 (장르별)

        Args:
            text: 검증할 텍스트
            genre: 장르 (wuxia, fantasy, hunter, investment)

        Returns:
            (verdict, violations)
        """
        # 적용 레벨 확인
        rule = self.get_genre_rule(genre)
        apply_level = rule.get("apply_level", "none")

        if apply_level == "none":
            return "PASS", []

        violations = []
        decision = "PASS"

        # 장르별 패턴 검사
        for pattern, category in self.get_regex_patterns_for_genre(genre):
            try:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    severity = "CRITICAL" if apply_level == "full" else "WARNING"

                    violations.append({
                        "type": "MODERN_TERM",
                        "severity": severity,
                        "category": category,
                        "found": list(set(str(m) if isinstance(m, str) else str(m[0]) for m in matches))[:5],
                        "message": f"[{genre}+원시인] {category} 사용 금지: {matches[:3]}"
                    })

                    if severity == "CRITICAL":
                        decision = "REJECT"
                    elif decision == "PASS":
                        decision = "WARNING"
            except Exception:
                continue

        return decision, violations

    def build_constraint_section(self, genre: str = "wuxia", include_alternatives: bool = True) -> str:
        """
        장르별 제약 섹션 생성

        Args:
            genre: 장르
            include_alternatives: 대체 표현 포함 여부
        """
        rule = self.get_genre_rule(genre)
        apply_level = rule.get("apply_level", "none")

        if apply_level == "none":
            return ""

        # full 프롬프트 사용
        full_prompt = self.get_prompt_injection(genre, "full")
        if full_prompt:
            return full_prompt

        # 폴백: 동적 생성
        lines = [f"### ⚠️ [{genre}+원시인 모드]"]
        lines.append(rule.get("description", ""))

        return "\n".join(lines)


# 싱글톤 인스턴스
_guard_instance = None


def get_primitive_guard() -> PrimitiveGuard:
    """PrimitiveGuard 싱글톤 인스턴스 반환"""
    global _guard_instance
    if _guard_instance is None:
        _guard_instance = PrimitiveGuard()
    return _guard_instance


def is_primitive_mode(protagonist_config: Dict) -> bool:
    """protagonist_config에서 원시인 모드 여부 확인"""
    if not protagonist_config:
        return False
    return protagonist_config.get("world_origin", "") == "원시인"


def get_primitive_constraint_section(
    protagonist_config: Dict,
    genre: str = "wuxia",
    length: str = "full"
) -> str:
    """
    장르+protagonist_config 기반 원시인 제약 섹션 반환

    Args:
        protagonist_config: {world_origin, incarnation_type}
        genre: 장르 (wuxia, fantasy, hunter, investment)
        length: "short", "medium", "full", "build"

    Returns:
        제약 섹션 텍스트 (원시인 아니면 빈 문자열)
    """
    if not is_primitive_mode(protagonist_config):
        return ""

    guard = get_primitive_guard()

    # 적용 레벨 확인
    rule = guard.get_genre_rule(genre)
    if rule.get("apply_level", "none") == "none":
        return ""

    if length == "build":
        return guard.build_constraint_section(genre)
    else:
        return guard.get_prompt_injection(genre, length)


def validate_primitive_compliance(
    text: str,
    protagonist_config: Dict,
    genre: str = "wuxia"
) -> Tuple[str, List[Dict], str]:
    """
    텍스트의 원시인 모드 준수 검증 (장르별)

    Args:
        text: 검증할 텍스트
        protagonist_config: {world_origin, incarnation_type}
        genre: 장르

    Returns:
        (verdict, violations, feedback)
    """
    if not is_primitive_mode(protagonist_config):
        return "PASS", [], ""

    guard = get_primitive_guard()

    # 적용 레벨 확인
    rule = guard.get_genre_rule(genre)
    if rule.get("apply_level", "none") == "none":
        return "PASS", [], ""

    verdict, violations = guard.validate(text, genre)

    feedback = ""
    if violations:
        critical = [v for v in violations if v.get("severity") == "CRITICAL"]
        warning = [v for v in violations if v.get("severity") == "WARNING"]

        if critical:
            feedback = f"[V60.96 CRITICAL] {genre}+원시인 모드 위반 {len(critical)}건:\n"
            for v in critical[:3]:
                feedback += f"  - {v.get('message', '')}\n"

        if warning:
            feedback += f"[V60.96 WARNING] 확인 필요 {len(warning)}건:\n"
            for v in warning[:2]:
                feedback += f"  - {v.get('message', '')}\n"

    return verdict, violations, feedback


def get_genre_from_context(context) -> str:
    """context에서 장르 추출"""
    try:
        if hasattr(context, 'db'):
            bible = context.db.load_anchor('bible')
            if bible:
                return bible.get('_genre', 'wuxia')
        if hasattr(context, 'load_v20_anchor'):
            bible = context.load_v20_anchor('bible')
            if bible:
                return bible.get('_genre', 'wuxia')
    except (AttributeError, KeyError, TypeError):  # [V64.P4] genre extraction with safe default
        pass
    return 'wuxia'  # 기본값
