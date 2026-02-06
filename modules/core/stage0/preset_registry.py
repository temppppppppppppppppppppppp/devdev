"""
Preset Registry - 프리셋 기반 동적 스키마 체계
===============================================
공통 + 장르별 프리셋 조합, 런타임 확장 지원
"""

import json
import copy
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass, field


@dataclass
class FieldDefinition:
    """필드 정의"""
    name: str
    type: str  # int, str, float, enum, list, dict
    default: Any = None
    enum_values: List[str] = field(default_factory=list)
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
            "network_level": FieldDefinition("network_level", "dict", {
                "financial": 0, "political": 0, "business": 0
            }, description="인맥 레벨"),
            "investment_style": FieldDefinition("investment_style", "str", "", description="투자 스타일"),
            "risk_tolerance": FieldDefinition("risk_tolerance", "enum", "중립",
                enum_values=["보수", "중립", "공격", "극공격"], description="위험 선호도"),
        },
        "wuxia": {
            "internal_energy": FieldDefinition("internal_energy", "int", 0, description="내공"),
            "rank": FieldDefinition("rank", "enum", "말류",
                enum_values=["말류", "삼류", "이류", "일류", "절정", "화경", "현경", "신경"],
                description="무공 경지"),
            "martial_arts": FieldDefinition("martial_arts", "list", [], description="습득 무공"),
            "faction": FieldDefinition("faction", "str", "무소속", description="소속 문파"),
            "faction_standing": FieldDefinition("faction_standing", "dict", {}, description="문파별 호감도"),
            "karma": FieldDefinition("karma", "dict", {"righteous": 0, "evil": 0}, description="정사 성향"),
            "secret_techniques": FieldDefinition("secret_techniques", "list", [], description="비전"),
            "qi_nature": FieldDefinition("qi_nature", "str", "", description="기의 속성"),
        },
        "hunter": {
            "level": FieldDefinition("level", "int", 1, description="레벨"),
            "rank": FieldDefinition("rank", "enum", "E",
                enum_values=["F", "E", "D", "C", "B", "A", "S", "SS", "SSS"],
                description="헌터 등급"),
            "class": FieldDefinition("class", "str", "", description="직업"),
            "mana": FieldDefinition("mana", "int", 0, description="마나"),
            "stats": FieldDefinition("stats", "dict", {
                "strength": 10, "agility": 10, "intelligence": 10, "vitality": 10, "luck": 10
            }, description="스탯"),
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
        "status": FieldDefinition("status", "enum", "alive",
            enum_values=["alive", "dead", "injured", "missing", "unknown"], description="생존 상태"),
        "role": FieldDefinition("role", "str", "", description="역할 (조력자/적대자/중립)"),
        "relationship": FieldDefinition("relationship", "str", "neutral", description="주인공과의 관계"),
        "first_appearance": FieldDefinition("first_appearance", "int", 0, description="첫 등장 Arc"),
        "last_seen_arc": FieldDefinition("last_seen_arc", "int", 0, description="마지막 등장 Arc"),
        "description": FieldDefinition("description", "str", "", description="인물 설명"),
    }

    NPC_GENRE_PRESETS = {
        "wuxia": {
            "faction": FieldDefinition("faction", "str", "무소속", description="소속 문파"),
            "rank": FieldDefinition("rank", "enum", "말류",
                enum_values=["말류", "삼류", "이류", "일류", "절정", "화경", "현경", "신경"], description="무공 경지"),
            "martial_arts": FieldDefinition("martial_arts", "list", [], description="무공"),
            "weapon": FieldDefinition("weapon", "str", "", description="주 무기"),
            "karma": FieldDefinition("karma", "str", "중립", description="정사 성향"),
            "title": FieldDefinition("title", "str", "", description="별호"),
        },
        "hunter": {
            "guild": FieldDefinition("guild", "str", "무소속", description="소속 길드"),
            "awakening_rank": FieldDefinition("awakening_rank", "enum", "E",
                enum_values=["F", "E", "D", "C", "B", "A", "S", "SS", "SSS"], description="각성 등급"),
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
    }

    def __init__(self, base_genre: str = None):
        self.base_genre = base_genre
        self.active_presets: Set[str] = {"common"}
        if base_genre and base_genre in self.GENRE_PRESETS:
            self.active_presets.add(base_genre)
        self.discovered_fields: Dict[str, FieldDefinition] = {}

    def activate_preset(self, preset_name: str) -> bool:
        """프리셋 활성화"""
        if preset_name in self.GENRE_PRESETS or preset_name == "common":
            self.active_presets.add(preset_name)
            return True
        return False

    def deactivate_preset(self, preset_name: str) -> bool:
        """프리셋 비활성화"""
        if preset_name in self.active_presets and preset_name != "common":
            self.active_presets.discard(preset_name)
            return True
        return False

    def get_active_fields(self) -> Dict[str, FieldDefinition]:
        """현재 활성화된 모든 필드 반환"""
        fields = dict(self.COMMON_PRESET)
        for preset_name in self.active_presets:
            if preset_name in self.GENRE_PRESETS:
                fields.update(self.GENRE_PRESETS[preset_name])
        fields.update(self.discovered_fields)
        return fields

    def get_field_names(self) -> List[str]:
        """활성 필드명 목록"""
        return list(self.get_active_fields().keys())

    def normalize_field_name(self, field_name: str) -> str:
        """별칭 → 정규 필드명 변환"""
        for canonical, aliases in self.FIELD_ALIASES.items():
            if field_name == canonical or field_name in aliases:
                return canonical
        return field_name

    def normalize_hud(self, raw_hud: Dict[str, Any]) -> Dict[str, Any]:
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
                    return value
                return [value] if value else []
            elif field_def.type == "dict":
                if isinstance(value, dict):
                    return value
                return {}
            elif field_def.type == "enum":
                if value in field_def.enum_values:
                    return value
                # 가장 가까운 값 찾기
                return field_def.default
        except:
            return field_def.default
        return value

    def _parse_korean_number(self, text: str) -> int:
        """한글 숫자 파싱 (50억, 1000만원 등)"""
        import re
        text = text.replace(",", "").replace(" ", "")

        multipliers = {"억": 100000000, "만": 10000, "천": 1000, "백": 100}

        # 순수 숫자면 바로 반환
        clean = re.sub(r'[^\d]', '', text)
        if clean and not any(m in text for m in multipliers.keys()):
            return int(clean)

        total = 0
        current = 0

        for char in text:
            if char.isdigit():
                current = current * 10 + int(char)
            elif char in multipliers:
                if current == 0:
                    current = 1
                total += current * multipliers[char]
                current = 0

        return total + current

    def detect_new_genre(self, content: str) -> Optional[str]:
        """콘텐츠에서 새 장르 요소 감지"""
        # 장르별 키워드
        genre_keywords = {
            "fantasy": ["마법", "마력", "주문", "용", "엘프", "드래곤", "이계", "차원"],
            "romance": ["사랑", "연애", "고백", "키스", "호감", "설렘", "짝사랑"],
            "politics": ["왕위", "왕좌", "대권", "정치", "파벌", "암투", "권력"],
            "military": ["전쟁", "군대", "병사", "장군", "전투", "진영", "병력"],
        }

        for genre, keywords in genre_keywords.items():
            if genre not in self.active_presets:
                matches = sum(1 for kw in keywords if kw in content)
                if matches >= 3:  # 3개 이상 키워드 매칭 시
                    return genre
        return None

    def build_initial_hud(self, protagonist_info: Dict[str, Any]) -> Dict[str, Any]:
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

    def get_npc_fields(self) -> Dict[str, FieldDefinition]:
        """현재 활성화된 NPC 필드 반환"""
        fields = dict(self.NPC_COMMON_PRESET)
        for preset_name in self.active_presets:
            if preset_name in self.NPC_GENRE_PRESETS:
                fields.update(self.NPC_GENRE_PRESETS[preset_name])
        return fields

    def build_npc_template(self, npc_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """NPC 템플릿 생성"""
        template = {}
        npc_fields = self.get_npc_fields()

        for field_name, field_def in npc_fields.items():
            if npc_info and field_name in npc_info:
                template[field_name] = npc_info[field_name]
            else:
                template[field_name] = field_def.default

        return template

    def normalize_npc(self, raw_npc: Dict[str, Any]) -> Dict[str, Any]:
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
        return json.dumps({
            "base_genre": self.base_genre,
            "active_presets": list(self.active_presets),
        }, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "PresetRegistry":
        """JSON에서 복원"""
        data = json.loads(json_str)
        registry = cls(base_genre=data.get("base_genre"))
        for preset in data.get("active_presets", []):
            registry.activate_preset(preset)
        return registry
