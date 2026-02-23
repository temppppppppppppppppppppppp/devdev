"""
Preset Registry - 프리셋 기반 동적 스키마 체계
===============================================
공통 + 장르별 프리셋 조합, 런타임 확장 지원
"""

import copy
import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class FieldDefinition:
    """필드 정의"""

    name: str
    type: str  # int, str, float, enum, list, dict
    default: Any = None
    enum_values: list[str] = field(default_factory=list)
    description: str = ""


class PresetRegistry:
    """프리셋 레지스트리 - 장르별 스키마 관리"""

    # 공통 필드 (모든 장르에 적용)
    COMMON_PRESET = {
        "name": FieldDefinition("name", "str", "", description="주인공 이름"),
        "age": FieldDefinition("age", "int", 25, description="나이"),
        "goal": FieldDefinition("goal", "str", "", description="최종 목표"),
        "current_objective": FieldDefinition("current_objective", "str", "", description="현재 목표"),
        "relationships": FieldDefinition("relationships", "dict", {}, description="인간관계"),
        "location": FieldDefinition("location", "str", "", description="현재 위치"),
        "reputation": FieldDefinition("reputation", "dict", {}, description="평판"),
        "secrets": FieldDefinition("secrets", "list", [], description="비밀"),
        "injuries": FieldDefinition("injuries", "str", "정상", description="부상 상태 (정상/경상/중상/위독)"),
    }

    # 장르별 프리셋
    GENRE_PRESETS = {
        "investment": {
            "capital": FieldDefinition("capital", "str", "0원", description="총 자본"),
            "liquid_cash": FieldDefinition("liquid_cash", "str", "0원", description="현금"),
            "portfolio": FieldDefinition("portfolio", "list", [], description="포트폴리오"),
            "stocks": FieldDefinition("stocks", "list", [], description="주식"),
            "real_estate": FieldDefinition("real_estate", "list", [], description="부동산"),
            "debt": FieldDefinition("debt", "str", "0원", description="부채"),
            "network_level": FieldDefinition(
                "network_level", "dict", {"financial": 0, "political": 0, "business": 0}, description="인맥 레벨"
            ),
            "investment_style": FieldDefinition("investment_style", "str", "", description="투자 스타일"),
            "risk_tolerance": FieldDefinition(
                "risk_tolerance",
                "enum",
                "중립",
                enum_values=["보수", "중립", "공격", "극공격"],
                description="위험 선호도",
            ),
        },
        "wuxia": {
            "internal_energy": FieldDefinition("internal_energy", "int", 0, description="내공"),
            "rank": FieldDefinition(
                "rank",
                "enum",
                "말류",
                enum_values=["말류", "삼류", "이류", "일류", "절정", "화경", "현경", "신경"],
                description="무공 경지",
            ),
            "martial_arts": FieldDefinition("martial_arts", "list", [], description="습득 무공"),
            "faction": FieldDefinition("faction", "str", "무소속", description="소속 문파"),
            "faction_standing": FieldDefinition("faction_standing", "dict", {}, description="문파별 호감도"),
            "karma": FieldDefinition("karma", "dict", {"righteous": 0, "evil": 0}, description="정사 성향"),
            "secret_techniques": FieldDefinition("secret_techniques", "list", [], description="비전"),
            "qi_nature": FieldDefinition("qi_nature", "str", "", description="기의 속성"),
        },
        "hunter": {
            "level": FieldDefinition("level", "int", 1, description="레벨"),
            "rank": FieldDefinition(
                "rank",
                "enum",
                "E",
                enum_values=["F", "E", "D", "C", "B", "A", "S", "SS", "SSS"],
                description="헌터 등급",
            ),
            "class": FieldDefinition("class", "str", "", description="직업"),
            "mana": FieldDefinition("mana", "int", 0, description="마나"),
            "stats": FieldDefinition(
                "stats",
                "dict",
                {"strength": 10, "agility": 10, "intelligence": 10, "vitality": 10, "luck": 10},
                description="스탯",
            ),
            "skills": FieldDefinition("skills", "list", [], description="스킬"),
            "equipment": FieldDefinition("equipment", "list", [], description="장비"),
            "guild": FieldDefinition("guild", "str", "무소속", description="소속 길드"),
            "achievements": FieldDefinition("achievements", "list", [], description="업적"),
            "unique_ability": FieldDefinition("unique_ability", "str", "", description="고유 능력"),
        },
        "fantasy": {
            "magic_power": FieldDefinition("magic_power", "int", 0, description="마력"),
            "magic_affinity": FieldDefinition("magic_affinity", "list", [], description="마법 친화 속성"),
            "spells": FieldDefinition("spells", "list", [], description="마법"),
            "race": FieldDefinition("race", "str", "인간", description="종족"),
            "blessings": FieldDefinition("blessings", "list", [], description="축복"),
            "curses": FieldDefinition("curses", "list", [], description="저주"),
            "divine_favor": FieldDefinition("divine_favor", "dict", {}, description="신의 총애"),
        },
        "composer": {
            "music_skill": FieldDefinition(
                "music_skill",
                "dict",
                {"composition": 0, "arrangement": 0, "production": 0, "instrument": [], "vocal_range": ""},
                description="음악 능력치",
            ),
            "reputation": FieldDefinition(
                "reputation", "dict", {"public": 0, "industry": 0, "critic": 0}, description="명성 (대중/업계/평론)"
            ),
            "discography": FieldDefinition("discography", "list", [], description="발표 작품"),
            "awards": FieldDefinition("awards", "list", [], description="수상 이력"),
            "contracts": FieldDefinition("contracts", "dict", {}, description="계약 관계"),
            "wealth": FieldDefinition("wealth", "str", "0원", description="재산"),
            "network": FieldDefinition(
                "network", "dict", {"artists": [], "producers": [], "executives": []}, description="인맥"
            ),
            "mental_state": FieldDefinition("mental_state", "str", "정상", description="정신 상태"),
            "creative_block": FieldDefinition("creative_block", "str", "없음", description="슬럼프 상태"),
            "genre_mastery": FieldDefinition("genre_mastery", "list", [], description="장악한 음악 장르"),
        },
        "cooking": {
            "chef_rank": FieldDefinition(
                "chef_rank",
                "enum",
                "수습생",
                enum_values=["수습생", "준요리사", "요리사", "수석요리사", "셰프", "명셰프", "거장", "전설의요리인"],
                description="요리사 등급",
            ),
            "signature_dish": FieldDefinition("signature_dish", "str", "", description="대표 요리"),
            "culinary_techniques": FieldDefinition("culinary_techniques", "list", [], description="습득 조리 기법"),
            "recipe_vault": FieldDefinition("recipe_vault", "list", [], description="레시피 보관함"),
            "food_philosophy": FieldDefinition("food_philosophy", "str", "", description="요리 철학"),
            "restaurant_name": FieldDefinition("restaurant_name", "str", "", description="식당 이름"),
            "restaurant_tier": FieldDefinition(
                "restaurant_tier",
                "enum",
                "포장마차",
                enum_values=["포장마차", "동네식당", "맛집", "파인다이닝", "미슐랭1스타", "미슐랭2스타", "미슐랭3스타"],
                description="식당 등급",
            ),
            "reputation_score": FieldDefinition("reputation_score", "int", 0, description="평판 점수 (0-100)"),
            "monthly_revenue": FieldDefinition("monthly_revenue", "str", "0원", description="월 매출"),
            "capital": FieldDefinition("capital", "str", "0원", description="운영 자금"),
            "customer_loyalty": FieldDefinition("customer_loyalty", "int", 0, description="단골 고객 수"),
        },
        "alt_history": {
            "social_class": FieldDefinition(
                "social_class", "enum", "양반", enum_values=["왕족", "양반", "중인", "상민", "천민"], description="신분"
            ),
            "court_rank": FieldDefinition("court_rank", "str", "무품", description="품계 (정1품~종9품)"),
            "position": FieldDefinition("position", "str", "없음", description="관직명"),
            "faction": FieldDefinition("faction", "str", "무소속", description="당파 (노론/소론/남인/북인 등)"),
            "political_influence": FieldDefinition("political_influence", "int", 0, description="정치적 영향력"),
            "wealth": FieldDefinition("wealth", "str", "빈한", description="재산 수준"),
            "knowledge": FieldDefinition("knowledge", "list", [], description="보유 지식/기술 (현대 지식 포함)"),
            "connections": FieldDefinition(
                "connections",
                "dict",
                {"royal": 0, "nobility": 0, "commoner": 0, "foreign": 0},
                description="인맥 (왕실/양반/민간/외교)",
            ),
            "public_trust": FieldDefinition("public_trust", "int", 50, description="민심 (0~100)"),
            "karma": FieldDefinition("karma", "int", 0, description="인과율"),
        },
        "actor": {
            "fame": FieldDefinition(
                "fame",
                "enum",
                "무명",
                enum_values=["무명", "엑스트라", "단역", "조연", "주연", "톱스타", "한류스타", "레전드"],
                description="인지도 등급",
            ),
            "acting_skill": FieldDefinition("acting_skill", "str", "초보", description="연기력 수준"),
            "agency": FieldDefinition("agency", "str", "무소속", description="소속사"),
            "filmography": FieldDefinition("filmography", "list", [], description="출연작 목록"),
            "fandom": FieldDefinition("fandom", "int", 0, description="팬덤 규모"),
            "scandal_index": FieldDefinition("scandal_index", "int", 0, description="스캔들 지수 (0~100)"),
            "box_office": FieldDefinition("box_office", "str", "없음", description="흥행 성적"),
            "wealth": FieldDefinition("wealth", "str", "0원", description="재산"),
            "network": FieldDefinition(
                "network",
                "dict",
                {"directors": [], "actors": [], "producers": [], "agencies": []},
                description="업계 인맥",
            ),
            "awards": FieldDefinition("awards", "list", [], description="수상 이력"),
            "mental_state": FieldDefinition("mental_state", "str", "정상", description="정신 상태"),
        },
        "sports": {
            "athlete_tier": FieldDefinition(
                "athlete_tier",
                "enum",
                "아마추어",
                enum_values=["동호회", "아마추어", "세미프로", "프로신인", "프로정규", "올스타", "국가대표", "전설"],
                description="선수 등급",
            ),
            "sport_type": FieldDefinition("sport_type", "str", "", description="종목"),
            "position": FieldDefinition("position", "str", "", description="포지션"),
            "physical_stats": FieldDefinition(
                "physical_stats",
                "dict",
                {"strength": 50, "speed": 50, "stamina": 50, "technique": 50, "mental": 50},
                description="신체 능력치 (0-100)",
            ),
            "record": FieldDefinition("record", "dict", {"wins": 0, "losses": 0, "draws": 0}, description="전적"),
            "skills": FieldDefinition("skills", "list", [], description="습득 기술"),
            "team": FieldDefinition("team", "str", "무소속", description="소속팀"),
            "ranking": FieldDefinition("ranking", "str", "무랭킹", description="순위"),
            "sponsorship": FieldDefinition("sponsorship", "list", [], description="스폰서"),
            "wealth": FieldDefinition("wealth", "str", "0원", description="연봉/자산"),
            "injury_history": FieldDefinition("injury_history", "list", [], description="부상 이력"),
            "mental_state": FieldDefinition("mental_state", "str", "정상", description="멘탈 상태"),
            "coach": FieldDefinition("coach", "str", "", description="코치/트레이너"),
        },
        "medical": {
            "doctor_rank": FieldDefinition(
                "doctor_rank",
                "enum",
                "의대생",
                enum_values=["의대생", "인턴", "레지던트", "전문의", "펠로우", "부교수", "교수", "석좌교수"],
                description="의사 직급",
            ),
            "specialty": FieldDefinition("specialty", "str", "", description="전공과"),
            "hospital": FieldDefinition("hospital", "str", "", description="소속 병원"),
            "surgery_count": FieldDefinition("surgery_count", "int", 0, description="수술 횟수"),
            "success_rate": FieldDefinition("success_rate", "float", 0.0, description="성공률 (%)"),
            "patients": FieldDefinition("patients", "list", [], description="주요 환자 케이스"),
            "research": FieldDefinition("research", "list", [], description="연구/논문"),
            "medical_skills": FieldDefinition("medical_skills", "list", [], description="습득 의술"),
            "wealth": FieldDefinition("wealth", "str", "0원", description="재산"),
            "mental_state": FieldDefinition("mental_state", "str", "정상", description="정신 상태"),
            "malpractice_record": FieldDefinition("malpractice_record", "list", [], description="의료사고 이력"),
            "network": FieldDefinition(
                "network", "dict", {"hospital": [], "academic": [], "pharmaceutical": []}, description="인맥"
            ),
        },
        "romance": {
            "affection": FieldDefinition("affection", "dict", {}, description="NPC별 호감도"),
            "relationship_status": FieldDefinition("relationship_status", "dict", {}, description="관계 상태"),
            "charm": FieldDefinition("charm", "int", 50, description="매력 수치"),
            "love_rivals": FieldDefinition("love_rivals", "list", [], description="연적"),
            "flags": FieldDefinition("flags", "dict", {}, description="이벤트 플래그"),
        },
        "politics": {
            "influence": FieldDefinition("influence", "int", 0, description="영향력"),
            "faction_power": FieldDefinition("faction_power", "dict", {}, description="파벌 권력"),
            "supporters": FieldDefinition("supporters", "list", [], description="지지자"),
            "enemies": FieldDefinition("enemies", "list", [], description="정적"),
            "public_approval": FieldDefinition("public_approval", "int", 50, description="민심"),
            "political_capital": FieldDefinition("political_capital", "int", 0, description="정치 자본"),
        },
        "military": {
            "rank": FieldDefinition("rank", "str", "병사", description="군 계급"),
            "command_ability": FieldDefinition("command_ability", "int", 0, description="지휘력"),
            "troops": FieldDefinition("troops", "dict", {}, description="휘하 병력"),
            "battle_record": FieldDefinition("battle_record", "dict", {"wins": 0, "losses": 0}, description="전적"),
            "tactics": FieldDefinition("tactics", "list", [], description="전술"),
            "equipment": FieldDefinition("equipment", "list", [], description="군장비"),
        },
    }

    # ========================================
    # NPC 프리셋 (장르별 NPC 상태 추적 필드)
    # ========================================
    NPC_COMMON_PRESET = {
        "name": FieldDefinition("name", "str", "", description="NPC 이름"),
        "status": FieldDefinition(
            "status",
            "enum",
            "alive",
            enum_values=["alive", "dead", "injured", "missing", "unknown"],
            description="생존 상태",
        ),
        "role": FieldDefinition("role", "str", "", description="역할 (조력자/적대자/중립)"),
        "relationship": FieldDefinition("relationship", "str", "neutral", description="주인공과의 관계"),
        "first_appearance": FieldDefinition("first_appearance", "int", 0, description="첫 등장 Arc"),
        "last_seen_arc": FieldDefinition("last_seen_arc", "int", 0, description="마지막 등장 Arc"),
        "description": FieldDefinition("description", "str", "", description="인물 설명"),
    }

    NPC_GENRE_PRESETS = {
        "wuxia": {
            "faction": FieldDefinition("faction", "str", "무소속", description="소속 문파"),
            "rank": FieldDefinition(
                "rank",
                "enum",
                "말류",
                enum_values=["말류", "삼류", "이류", "일류", "절정", "화경", "현경", "신경"],
                description="무공 경지",
            ),
            "martial_arts": FieldDefinition("martial_arts", "list", [], description="무공"),
            "weapon": FieldDefinition("weapon", "str", "", description="주 무기"),
            "karma": FieldDefinition("karma", "str", "중립", description="정사 성향"),
            "title": FieldDefinition("title", "str", "", description="별호"),
        },
        "hunter": {
            "guild": FieldDefinition("guild", "str", "무소속", description="소속 길드"),
            "awakening_rank": FieldDefinition(
                "awakening_rank",
                "enum",
                "E",
                enum_values=["F", "E", "D", "C", "B", "A", "S", "SS", "SSS"],
                description="각성 등급",
            ),
            "class": FieldDefinition("class", "str", "", description="직업"),
            "skills": FieldDefinition("skills", "list", [], description="스킬"),
            "level": FieldDefinition("level", "int", 1, description="레벨"),
        },
        "investment": {
            "company": FieldDefinition("company", "str", "", description="소속 회사"),
            "position": FieldDefinition("position", "str", "", description="직급"),
            "net_worth": FieldDefinition("net_worth", "str", "0원", description="자산"),
            "influence": FieldDefinition("influence", "str", "", description="영향력 분야"),
            "network": FieldDefinition("network", "list", [], description="인맥"),
        },
        "fantasy": {
            "race": FieldDefinition("race", "str", "인간", description="종족"),
            "magic_affinity": FieldDefinition("magic_affinity", "list", [], description="마법 속성"),
            "rank": FieldDefinition("rank", "str", "", description="계급/지위"),
            "blessings": FieldDefinition("blessings", "list", [], description="축복"),
        },
        "composer": {
            "role_in_industry": FieldDefinition("role_in_industry", "str", "", description="업계 역할"),
            "musical_style": FieldDefinition("musical_style", "str", "", description="음악 스타일"),
            "company": FieldDefinition("company", "str", "", description="소속사"),
            "influence": FieldDefinition("influence", "int", 0, description="영향력"),
            "relationship_type": FieldDefinition(
                "relationship_type", "str", "", description="관계 유형 (멘토/라이벌/팬 등)"
            ),
        },
        "cooking": {
            "role_in_kitchen": FieldDefinition("role_in_kitchen", "str", "", description="주방 역할"),
            "culinary_style": FieldDefinition("culinary_style", "str", "", description="요리 스타일"),
            "restaurant": FieldDefinition("restaurant", "str", "", description="소속 식당"),
            "chef_rank": FieldDefinition("chef_rank", "str", "", description="요리사 등급"),
            "relationship_type": FieldDefinition(
                "relationship_type", "str", "", description="관계 유형 (멘토/라이벌/고객 등)"
            ),
        },
        "alt_history": {
            "social_class": FieldDefinition(
                "social_class", "enum", "양반", enum_values=["왕족", "양반", "중인", "상민", "천민"], description="신분"
            ),
            "position": FieldDefinition("position", "str", "", description="관직"),
            "faction": FieldDefinition("faction", "str", "", description="당파"),
            "loyalty": FieldDefinition("loyalty", "str", "neutral", description="충성 대상"),
            "influence": FieldDefinition("influence", "int", 0, description="정치적 영향력"),
        },
        "actor": {
            "role_in_industry": FieldDefinition("role_in_industry", "str", "", description="업계 역할"),
            "fame_level": FieldDefinition("fame_level", "str", "", description="인지도"),
            "agency": FieldDefinition("agency", "str", "", description="소속사"),
            "filmography": FieldDefinition("filmography", "list", [], description="출연작"),
            "relationship_type": FieldDefinition(
                "relationship_type", "str", "", description="관계 유형 (멘토/라이벌/팬 등)"
            ),
        },
        "sports": {
            "team": FieldDefinition("team", "str", "", description="소속팀"),
            "athlete_tier": FieldDefinition(
                "athlete_tier",
                "enum",
                "아마추어",
                enum_values=["동호회", "아마추어", "세미프로", "프로신인", "프로정규", "올스타", "국가대표", "전설"],
                description="선수 등급",
            ),
            "position": FieldDefinition("position", "str", "", description="포지션"),
            "record": FieldDefinition("record", "dict", {"wins": 0, "losses": 0}, description="전적"),
            "skills": FieldDefinition("skills", "list", [], description="기술"),
        },
        "medical": {
            "hospital": FieldDefinition("hospital", "str", "", description="소속 병원"),
            "doctor_rank": FieldDefinition(
                "doctor_rank",
                "enum",
                "레지던트",
                enum_values=["의대생", "인턴", "레지던트", "전문의", "펠로우", "부교수", "교수", "석좌교수"],
                description="의사 직급",
            ),
            "specialty": FieldDefinition("specialty", "str", "", description="전공과"),
            "reputation": FieldDefinition("reputation", "str", "", description="평판"),
            "skills": FieldDefinition("skills", "list", [], description="의술"),
        },
        "romance": {
            "affection": FieldDefinition("affection", "int", 0, description="호감도"),
            "relationship_stage": FieldDefinition("relationship_stage", "str", "stranger", description="관계 단계"),
            "personality": FieldDefinition("personality", "str", "", description="성격"),
        },
        "politics": {
            "faction": FieldDefinition("faction", "str", "", description="파벌"),
            "rank": FieldDefinition("rank", "str", "", description="관직/지위"),
            "loyalty": FieldDefinition("loyalty", "str", "neutral", description="충성 대상"),
            "influence": FieldDefinition("influence", "int", 0, description="영향력"),
        },
        "military": {
            "rank": FieldDefinition("rank", "str", "", description="군 계급"),
            "unit": FieldDefinition("unit", "str", "", description="소속 부대"),
            "combat_record": FieldDefinition("combat_record", "str", "", description="전투 기록"),
        },
    }

    # 필드명 별칭 (정규화용)
    FIELD_ALIASES = {
        "internal_energy": ["내공", "inner_power", "qi", "기"],
        "rank": ["경지", "realm", "등급", "grade"],
        "capital": ["자본", "자산", "money", "wealth", "총자산"],
        "level": ["레벨", "lv"],
        "mana": ["마나", "mp", "마력"],
        "skills": ["스킬", "기술", "abilities"],
        "martial_arts": ["무공", "무술", "techniques"],
        # composer
        "music_skill": ["음악능력", "음악_능력치"],
        "genre_mastery": ["장르숙련", "장르_마스터리"],
        "creative_block": ["슬럼프", "창작막힘"],
        # cooking
        "chef_rank": ["셰프등급", "요리사등급", "chef_level"],
        "signature_dish": ["대표요리", "시그니처"],
        "culinary_techniques": ["조리기법", "요리기술"],
        "restaurant_tier": ["식당등급", "레스토랑등급"],
        "reputation_score": ["평판점수", "reputation_point"],
        # alt_history
        "social_class": ["신분", "계급", "신분등급"],
        "court_rank": ["품계", "관품"],
        "political_influence": ["정치영향력", "정치력"],
        "public_trust": ["민심", "신뢰도"],
        # actor
        "acting_skill": ["연기력", "연기실력", "acting_level"],
        "fame": ["인지도", "fame_level", "명성"],
        "filmography": ["출연작", "필모그래피"],
        "scandal_index": ["스캔들지수", "스캔들"],
        "fandom": ["팬덤", "팬규모"],
        # sports
        "athlete_tier": ["선수등급", "선수_티어", "athlete_rank"],
        "sport_type": ["종목", "스포츠종목"],
        "physical_stats": ["신체능력", "체력스탯"],
        "ranking": ["순위", "랭킹"],
        # medical
        "doctor_rank": ["의사직급", "의사등급", "doctor_level"],
        "specialty": ["전공과", "전문분야"],
        "surgery_count": ["수술횟수", "수술_건수"],
        "success_rate": ["성공률", "수술성공률"],
        "malpractice_record": ["의료사고", "의료사고이력"],
    }

    def __init__(self, base_genre: str = None):
        self.base_genre = base_genre
        # [TF7-P2-02] set → list로 변경하여 순서 보장 (common 항상 첫 번째)
        self.active_presets: list[str] = ["common"]
        if base_genre and base_genre in self.GENRE_PRESETS:
            self.active_presets.append(base_genre)
        self.discovered_fields: dict[str, FieldDefinition] = {}

    def activate_preset(self, preset_name: str) -> bool:
        """프리셋 활성화"""
        if preset_name in self.GENRE_PRESETS or preset_name == "common":
            # [TF7-P2-02] 중복 추가 방지
            if preset_name not in self.active_presets:
                self.active_presets.append(preset_name)
            return True
        return False

    def deactivate_preset(self, preset_name: str) -> bool:
        """프리셋 비활성화"""
        if preset_name in self.active_presets and preset_name != "common":
            self.active_presets.remove(preset_name)
            return True
        return False

    def get_active_fields(self) -> dict[str, FieldDefinition]:
        """현재 활성화된 모든 필드 반환
        [TF7-P2-02] 우선순위: common → base_genre → 추가 preset 순으로 적용
        """
        fields = dict(self.COMMON_PRESET)
        # list 순회로 순서 보장 (common은 __init__에서 항상 첫 번째)
        for preset_name in self.active_presets:
            if preset_name in self.GENRE_PRESETS:
                fields.update(self.GENRE_PRESETS[preset_name])
        fields.update(self.discovered_fields)
        return fields

    def get_field_names(self) -> list[str]:
        """활성 필드명 목록"""
        return list(self.get_active_fields().keys())

    def normalize_field_name(self, field_name: str) -> str:
        """별칭 → 정규 필드명 변환"""
        for canonical, aliases in self.FIELD_ALIASES.items():
            if field_name == canonical or field_name in aliases:
                return canonical
        return field_name

    def normalize_hud(self, raw_hud: dict[str, Any]) -> dict[str, Any]:
        """LLM 출력 HUD 정규화"""
        normalized = {}
        active_fields = self.get_active_fields()

        for key, value in raw_hud.items():
            canonical = self.normalize_field_name(key)

            if canonical in active_fields:
                field_def = active_fields[canonical]
                normalized[canonical] = self._enforce_type(value, field_def)
            else:
                # 알 수 없는 필드는 그대로 저장 (discovered로 기록 가능)
                normalized[canonical] = value

        return normalized

    def _enforce_type(self, value: Any, field_def: FieldDefinition) -> Any:
        """타입 강제"""
        try:
            if field_def.type == "int":
                if isinstance(value, str):
                    # "100만원" → 1000000 변환 시도
                    return self._parse_korean_number(value)
                return int(value)
            elif field_def.type == "float":
                return float(value)
            elif field_def.type == "str":
                return str(value)
            elif field_def.type == "list":
                if isinstance(value, list):
                    return list(value)  # [P0] 얕은 복사 — 공유 참조 방지
                return [value] if value else []
            elif field_def.type == "dict":
                if isinstance(value, dict):
                    return dict(value)  # [P0] 얕은 복사 — 공유 참조 방지
                return {}
            elif field_def.type == "enum":
                if value in field_def.enum_values:
                    return value
                # 가장 가까운 값 찾기
                return copy.deepcopy(field_def.default)
        except (ValueError, TypeError, KeyError, AttributeError):  # [V64.P4] field validation failure
            return copy.deepcopy(field_def.default)
        return value

    def _parse_korean_number(self, text: str) -> int:
        """한글 숫자 파싱 (50억, 1000만원, 1억5천만 등)

        [G15] 복합 단위 지원: "1억5천만" = 150,000,000
        억/만은 대단위, 천/백은 소단위로 분리하여 파싱.
        """
        text = text.replace(",", "").replace(" ", "")

        multipliers = {"억": 100000000, "만": 10000, "천": 1000, "백": 100}

        # 순수 숫자면 바로 반환
        clean = re.sub(r"[^\d]", "", text)
        if clean and not any(m in text for m in multipliers.keys()):
            return int(clean)

        # [G15] 대단위(억, 만) 기준으로 분리하여 복합 파싱
        # "1억5천만" → 억 파트: "1억" = 1*억, 만 파트: "5천만" = 5천*만
        total = 0
        current = 0  # 현재 누적 숫자
        sub_total = 0  # 소단위(천/백) 누적

        for char in text:
            if char.isdigit():
                current = current * 10 + int(char)
            elif char in multipliers:
                if current == 0:
                    current = 1
                mult_val = multipliers[char]
                if mult_val >= 10000:
                    # 대단위(억, 만): sub_total + current를 계수로 사용
                    total += (sub_total + current) * mult_val
                    current = 0
                    sub_total = 0
                else:
                    # 소단위(천, 백): sub_total에 누적
                    sub_total += current * mult_val
                    current = 0

        # 나머지 (단위 없는 끝자리 숫자)
        return total + sub_total + current

    def detect_new_genre(self, content: str) -> str | None:
        """콘텐츠에서 새 장르 요소 감지"""
        # 장르별 키워드
        genre_keywords = {
            "wuxia": ["내공", "무공", "경지", "강호", "문파", "무림", "검법", "장풍"],
            "hunter": ["던전", "각성", "헌터", "길드", "마나", "레이드", "게이트", "몬스터"],
            "investment": ["주식", "투자", "자본", "부동산", "펀드", "배당", "시세", "상장"],
            "fantasy": ["마법", "마력", "주문", "용", "엘프", "드래곤", "이계", "차원"],
            "composer": ["작곡", "편곡", "프로듀싱", "음원", "앨범", "차트", "보컬", "멜로디"],
            "cooking": ["요리", "셰프", "레시피", "식재료", "조리", "미슐랭", "식당", "주방"],
            "alt_history": ["조선", "관직", "양반", "궁궐", "임금", "당파", "과거시험", "내시"],
            "actor": ["오디션", "촬영", "배우", "대본", "감독", "캐스팅", "시청률", "영화제"],
            "sports": ["선수", "경기", "코치", "훈련", "리그", "챔피언", "체력", "시합"],
            "medical": ["수술", "환자", "진료", "병원", "의사", "레지던트", "진단", "처방"],
            "romance": ["사랑", "연애", "고백", "키스", "호감", "설렘", "짝사랑"],
            "politics": ["왕위", "왕좌", "대권", "정치", "파벌", "암투", "권력"],
            "military": ["전쟁", "군대", "병사", "장군", "전투", "진영", "병력"],
        }

        content_lower = content.lower()
        for genre, keywords in genre_keywords.items():
            if genre not in self.active_presets:
                matches = sum(1 for kw in keywords if kw in content_lower)
                if matches >= 3:  # 3개 이상 키워드 매칭 시
                    return genre
        return None

    def build_initial_hud(self, protagonist_info: dict[str, Any]) -> dict[str, Any]:
        """초기 HUD 생성"""
        hud = {}
        active_fields = self.get_active_fields()

        for field_name, field_def in active_fields.items():
            if field_name in protagonist_info:
                hud[field_name] = protagonist_info[field_name]
            else:
                # [V61.5] mutable default 복사 ([], {} 공유 객체 오염 방지)
                hud[field_name] = copy.deepcopy(field_def.default)

        return hud

    # ========================================
    # NPC 필드 관리
    # ========================================

    def get_npc_fields(self) -> dict[str, FieldDefinition]:
        """현재 활성화된 NPC 필드 반환"""
        fields = dict(self.NPC_COMMON_PRESET)
        for preset_name in self.active_presets:
            if preset_name in self.NPC_GENRE_PRESETS:
                fields.update(self.NPC_GENRE_PRESETS[preset_name])
        return fields

    def build_npc_template(self, npc_info: dict[str, Any] = None) -> dict[str, Any]:
        """NPC 템플릿 생성"""
        template = {}
        npc_fields = self.get_npc_fields()

        for field_name, field_def in npc_fields.items():
            if npc_info and field_name in npc_info:
                template[field_name] = npc_info[field_name]
            else:
                template[field_name] = copy.deepcopy(field_def.default)  # [V70] mutable default 공유 방지

        return template

    def normalize_npc(self, raw_npc: dict[str, Any]) -> dict[str, Any]:
        """NPC 데이터 정규화"""
        normalized = {}
        npc_fields = self.get_npc_fields()

        for key, value in raw_npc.items():
            canonical = self.normalize_field_name(key)
            if canonical in npc_fields:
                field_def = npc_fields[canonical]
                normalized[canonical] = self._enforce_type(value, field_def)
            else:
                normalized[canonical] = value

        return normalized

    def get_npc_schema_for_prompt(self) -> str:
        """NPC용 프롬프트 스키마"""
        fields = self.get_npc_fields()
        lines = ["## NPC 추적 필드"]

        for name, field_def in fields.items():
            if field_def.type == "enum":
                lines.append(f"- {name}: {field_def.enum_values} 중 하나")
            else:
                lines.append(f"- {name}: {field_def.type} ({field_def.description})")

        return "\n".join(lines)

    def get_schema_for_prompt(self) -> str:
        """프롬프트용 스키마 문자열 생성"""
        fields = self.get_active_fields()
        lines = ["## 추적 필드 (정확히 이 필드명 사용)"]

        for name, field_def in fields.items():
            if field_def.type == "enum":
                lines.append(f"- {name}: {field_def.enum_values} 중 하나")
            else:
                lines.append(f"- {name}: {field_def.type} ({field_def.description})")

        return "\n".join(lines)

    def to_json(self) -> str:
        """현재 상태 JSON 직렬화"""
        data: dict[str, Any] = {
            "base_genre": self.base_genre,
            "active_presets": list(self.active_presets),
        }
        if self.discovered_fields:
            data["discovered_fields"] = {k: asdict(v) for k, v in self.discovered_fields.items()}
        return json.dumps(data, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "PresetRegistry":
        """JSON에서 복원"""
        try:
            data = json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return cls()
        if not isinstance(data, dict):
            return cls()
        registry = cls(base_genre=data.get("base_genre"))
        active_presets = data.get("active_presets", [])
        if not isinstance(active_presets, list):  # [P1-A3-4] 타입 검증
            active_presets = []
        for preset in active_presets:
            registry.activate_preset(preset)
        for name, fd in data.get("discovered_fields", {}).items():
            if isinstance(fd, dict):
                registry.discovered_fields[name] = FieldDefinition(**fd)
        return registry
