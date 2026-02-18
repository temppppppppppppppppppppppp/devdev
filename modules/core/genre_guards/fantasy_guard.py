"""
[V66] 판타지 전용 Guard — WuxiaGuard 독립 분리

마법 계층 (견습~전설급), 주문 티어 제한, 마나 상태별 행동 제한.
무협 용어 금지 (내공/진기/단전...), 게임 용어 허용 (마나/스킬/레벨).
"""

import re
from typing import Any

from .base_guard import BaseGuard


class FantasyGuard(BaseGuard):
    """[V66] 판타지(이세계) 장르 Guard"""

    # ═══════════════════════════════════════════════════════════════
    # 마법 계층 시스템
    # ═══════════════════════════════════════════════════════════════

    MAGIC_TIERS = ["견습", "초급", "중급", "상급", "고급", "대마법사", "아크메이지", "전설급"]

    # 티어별 허용 주문 수
    TIER_SPELL_LIMITS = {
        "견습": 2,
        "초급": 4,
        "중급": 6,
        "상급": 8,
        "고급": 12,
        "대마법사": 16,
        "아크메이지": 24,
        "전설급": 99,
    }

    # 상위 티어 전용 주문 키워드
    HIGH_TIER_SPELLS = [
        "시간 역행",
        "차원 절단",
        "공간 파쇄",
        "세계수",
        "신의 권능",
        "금지 마법",
        "금제 마법",
        "영혼 소멸",
        "대멸",
        "천지개벽",
    ]

    def __init__(self) -> None:
        super().__init__()
        cfg = self._load_genre_yaml("fantasy")

        self.ALLOWED_TERMS = cfg.get(
            "allowed_terms",
            [
                "마나",
                "스킬",
                "레벨",
                "퀘스트",
                "던전",
                "스킬트리",
                "버프",
                "디버프",
                "마법진",
                "포션",
                "엘릭서",
                "아티팩트",
                "마정석",
                "소환수",
                "정령",
                "마탑",
                "길드",
                "파티",
                "몬스터",
                "보스",
                "드래곤",
                "엘프",
                "드워프",
                "오크",
                "고블린",
                "슬라임",
                "스켈레톤",
                "리치",
                "네크로맨서",
                "카페",
                "커피",
                "빵",
            ],
        )

        self.FORBIDDEN_TERMS = cfg.get(
            "forbidden_terms",
            [
                "내공",
                "진기",
                "단전",
                "기해",
                "기경팔맥",
                "임독이맥",
                "검강",
                "검기",
                "도기",
                "장강",
                "무림",
                "강호",
                "화경",
                "현경",
                "천인합일",
                "무극",
                "반선",
                "비급",
                "진전",
                "절학",
                "신공",
                "마공",
                "사파",
                "정파",
                "마교",
                "무당",
                "소림",
                "경공",
                "보법",
                "초식",
                "권법",
                "장법",
            ],
        )

        self.MANDATORY_CONCEPTS = cfg.get(
            "mandatory_concepts",
            [
                "마법",
                "마나",
                "주문",
                "마력",
            ],
        )

    def get_genre_name(self) -> str:
        return "판타지"

    def _should_check_english(self) -> bool:
        """판타지는 영어 일부 허용 (게임 용어)."""
        return False

    def _should_check_numbers(self) -> bool:
        """판타지는 숫자 허용 (레벨, 스탯 등)."""
        return False

    def get_v20_purism_prompt(self) -> str:
        """판타지 장르 순혈주의 프롬프트."""
        return """[판타지 장르 순혈주의 가이드라인]

## 절대 금지 용어 (무협 전용)
내공, 진기, 단전, 기해, 기경팔맥, 임독이맥, 검강, 검기, 도기, 장강,
무림, 강호, 화경, 현경, 비급, 진전, 절학, 신공, 마공,
사파, 정파, 마교, 경공, 보법, 초식

## 사용 권장 용어
마나, 마력, 마법진, 주문, 스킬, 레벨, 퀘스트, 던전, 포션,
마정석, 소환수, 정령, 마탑, 길드, 파티, 아티팩트

## 마법 계층 (반드시 순서 준수)
견습 → 초급 → 중급 → 상급 → 고급 → 대마법사 → 아크메이지 → 전설급

## 마나 상태별 행동 제약
- 마나 고갈: 기본 이동만 가능, 마법 사용 불가
- 마나 부족 (<20%): 하위 주문만 가능, 상위 주문 불가
- 마나 충분 (>50%): 자유로운 마법 사용

## 주문 티어 제한
- 견습: 2개, 초급: 4개, 중급: 6개, 상급: 8개
- 고급: 12개, 대마법사: 16개, 아크메이지: 24개
- 금지 마법 (시간 역행, 차원 절단 등): 아크메이지+ 전용"""

    # ═══════════════════════════════════════════════════════════════
    # [V46] 일관성 검증 구현
    # ═══════════════════════════════════════════════════════════════

    def get_impossible_actions(self, current_state: dict[str, Any]) -> list[dict[str, str]]:
        """마나/마법 상태 기반 불가능 행동."""
        actions = []

        mana = current_state.get("mana", current_state.get("magic_power", 100))
        if isinstance(mana, str):
            if mana.strip() in ("고갈", "없음", "소멸", "전무", "0"):  # [V70] 고갈 상태 → 0
                mana = 0
            else:
                try:
                    mana = float(re.search(r"(\d+)", str(mana)).group(1))
                except (AttributeError, ValueError):
                    mana = 100
        if mana is None:
            mana = 100

        tier = str(current_state.get("magic_tier", current_state.get("realm", ""))).strip()

        # 마나 고갈 시 마법 사용 불가
        if mana <= 0:
            actions.append(
                {
                    "pattern": r"마법.*(?:시전|발동|사용|날리|쏘|발사)",
                    "reason": "마나 고갈 상태에서 마법 사용 불가",
                    "severity": "HIGH",
                }
            )
            actions.append(
                {
                    "pattern": r"주문.*(?:외우|시전|발동|사용)",
                    "reason": "마나 고갈 상태에서 주문 시전 불가",
                    "severity": "HIGH",
                }
            )

        # 마나 부족 (<20%) 시 상위 주문 불가
        if 0 < mana < 20:
            for spell in self.HIGH_TIER_SPELLS:
                actions.append(
                    {
                        "pattern": re.escape(spell),
                        "reason": f'마나 부족({mana}%)에서 상위 주문 "{spell}" 사용 불가',
                        "severity": "HIGH",
                    }
                )

        # 견습/초급은 금지 마법 불가
        if tier in ("견습", "초급", "중급"):
            for spell in self.HIGH_TIER_SPELLS:
                actions.append(
                    {
                        "pattern": re.escape(spell),
                        "reason": f'마법 티어 "{tier}"에서 상위 주문 "{spell}" 사용 불가',
                        "severity": "HIGH",
                    }
                )

        return actions

    def get_justification_patterns(self) -> list[str]:
        """마법 세계 정당화 패턴."""
        return [
            r"아티팩트.*힘.*빌려",
            r"금지.*마법.*대가",
            r"생명력.*소모",
            r"마정석.*흡수",
            r"정령.*도움",
            r"축복.*받",
            r"고대.*유물",
            r"죽기.*살기",
        ]

    def get_hierarchy_rules(self) -> dict[str, Any]:
        """마법사 위계."""
        return {
            "ranks": self.MAGIC_TIERS,
            "titles": {
                "전설급": ["대현자", "마신", "마제"],
                "아크메이지": ["마탑주", "현자"],
                "대마법사": ["마도사", "원로"],
                "고급": ["마법사"],
                "상급": ["마법사"],
                "중급": ["마법사"],
                "초급": ["마법학도"],
                "견습": ["견습생"],
            },
            "address_rules": {
                "상위→하위": "반말/하대",
                "하위→상위": "존칭/경어",
            },
        }

    # ═══════════════════════════════════════════════════════════════
    # [V66] run_deep_validation override
    # ═══════════════════════════════════════════════════════════════

    def run_deep_validation(self, manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]:
        """[V66] Fantasy 심층 검증: base + 무협 용어 차단 + 마법 티어 제한."""
        result = super().run_deep_validation(manuscript, current_state or {})

        # 무협 용어 → HIGH 승격 (base class FORBIDDEN_TERMS는 MEDIUM, 판타지에서는 HIGH)
        for v in result["violations"]:
            if v.get("type") == "forbidden_term" and v.get("term", "") in (
                "내공",
                "진기",
                "단전",
                "기해",
                "검강",
                "무림",
                "강호",
                "화경",
            ):
                v["severity"] = "HIGH"

        # 마법 티어 검증 (현재 상태 기반)
        if current_state:
            tier = str(current_state.get("magic_tier", current_state.get("realm", ""))).strip()
            if tier and tier in ("견습", "초급", "중급"):
                for spell in self.HIGH_TIER_SPELLS:
                    if spell in manuscript:
                        result["violations"].append(
                            {
                                "type": "spell_tier_violation",
                                "severity": "HIGH",
                                "message": f"마법 티어 '{tier}'에서 상위 주문 '{spell}' 사용",
                            }
                        )

        result["has_critical"] = any(v.get("severity") in ("HIGH", "CRITICAL") for v in result["violations"])
        if result["violations"]:
            result["summary"] = "; ".join(v.get("message", "") for v in result["violations"][:5])
            result["feedback"] = f"[판타지 Guard] {len(result['violations'])}건: {result['summary']}"
        return result

    # ═══════════════════════════════════════════════════════════════
    # 원고 검증 커스터마이징
    # ═══════════════════════════════════════════════════════════════

    def validate_v20_manuscript(self, content) -> dict:
        """판타지 원고 검증 — 숫자/영어 허용, 무협 용어만 금지."""
        issues = []

        # 금기어 검사 (무협 용어)
        for term in self.FORBIDDEN_TERMS:
            if term in content:
                issues.append(f"무협 전용 용어 발견: '{term}' → 마법/판타지 용어로 대체 필요")

        # 괄호 검출 (한자 예외)
        parentheses_matches = re.findall(r"\((.*?)\)", content)
        for inside in parentheses_matches:
            if re.search(r"[^\u4e00-\u9fff]", inside):
                issues.append(f"괄호 설명 발견: ({inside})")

        return {"is_pure": len(issues) == 0, "issues": issues}
