"""
[V40 Multi-Genre Factory] 장르별 HUD 시스템 통합 관리자
무협/헌터/투자 3가지 장르의 HUD를 추상화하여 통일된 인터페이스 제공
"""

import logging
from abc import ABC, abstractmethod


class GenreHUDManager(ABC):
    """장르 독립적 HUD 추상 인터페이스"""

    hud_key: str = ""
    hud_key_alt: str = ""
    legacy_hud_keys: tuple = ()

    def __init__(self, context) -> None:
        self.context = context
        self.canonical_map = {}  # 각 장르별로 오버라이드

    def _get_bible(self) -> dict:
        return self.context.master_bible.get("MasterBible", self.context.master_bible)

    def _resolve_default_name(self, bible: dict) -> str:
        try:
            return (
                bible.get("ProjectData", {}).get("CoreIdentity", {}).get("protagonist")
                or bible.get("InitialHUD", {}).get("name")
                or "주인공"
            )
        except Exception:
            return "주인공"

    @property
    def pro_root(self) -> dict:
        bible = self._get_bible()
        search_keys = [self.hud_key]
        if self.hud_key_alt:
            search_keys.append(self.hud_key_alt)
        if self.legacy_hud_keys:
            search_keys.extend(list(self.legacy_hud_keys))

        hud_data = None
        for key in search_keys:
            candidate = bible.get(key, {})
            if isinstance(candidate, dict) and candidate:
                hud_data = candidate
                if key != self.hud_key and self.hud_key:
                    bible[self.hud_key] = candidate
                break

        if not isinstance(hud_data, dict) or not hud_data:
            hud_data = {"Protagonist": {"actual_truth": {"name": self._resolve_default_name(bible)}}}
            if self.hud_key:
                bible[self.hud_key] = hud_data

        return hud_data.get("Protagonist", hud_data)

    @property
    def pro_data(self) -> dict:
        return self.pro_root.get("actual_truth", self.pro_root)

    @abstractmethod
    def get_v20_hud_report(self) -> str:
        """HUD 보고서 생성 (장르별 구현)"""
        pass

    @abstractmethod
    def get_critical_keys(self) -> list:
        """장르별 필수 추적 키 반환"""
        pass

    def update_physical_status(self, full_state_data: dict):
        """[V64.P4-refactor] 공통 상태 업데이트"""
        if not full_state_data:
            return []

        bible = self._get_bible()
        pro = bible.setdefault(self.hud_key, {}).setdefault("Protagonist", {})
        actual = pro.setdefault("actual_truth", {})
        actual_in = full_state_data.get("actual_truth", full_state_data)

        changes = []
        for canonical_key, fallback_keys in self.canonical_map.items():
            val = None
            for incoming_key in fallback_keys:
                if incoming_key in actual_in:
                    val = actual_in[incoming_key]
                    break

            if val is not None:
                old_val = actual.get(canonical_key, "기록 없음")
                if str(old_val) != str(val):
                    actual[canonical_key] = val
                    changes.append(f"{canonical_key}: {old_val} -> {val}")

        if changes:
            self.context.save_v20_anchor("bible", self.context.master_bible)

        return changes

    def _get_normalized_val(self, canonical_key: str, default="기록 없음") -> str:
        """변칙 키 정규화 (공통 로직)"""
        fallbacks = self.canonical_map.get(canonical_key, [canonical_key])
        for key in fallbacks:
            val = self.pro_data.get(key)
            if val is not None:
                return val
        return default


class HunterHUDManager(GenreHUDManager):
    hud_key = "HunterHUD"
    hud_key_alt = "hunter_hud"
    """[헌터물] 각성자/헌터 전용 HUD 시스템"""

    def __init__(self, context) -> None:
        super().__init__(context)
        self.canonical_map = {
            "awakening_rank": ["rank", "hunter_rank", "awakening_rank", "랭크", "등급", "각성등급"],
            "mana": ["mana", "magic_power", "mp", "마나", "마력"],
            "skills": ["skills", "abilities", "skill_list", "스킬", "능력"],
            "wealth": ["wealth", "money", "funds", "자금", "재산", "골드"],
            "injuries": ["injuries", "status", "hp", "부상", "상태", "체력"],
            "current_objective": ["objective", "quest", "current_objective", "목표", "퀘스트"],
            "reputation": ["reputation", "fame", "명성", "평판"],
            "guild": ["guild", "party", "affiliation", "길드", "소속"],
            "equipment": ["equipment", "items", "장비", "아이템"],
            "title": ["title", "alias", "칭호", "별명"],
            "stat_points": ["stat_points", "points", "스탯포인트", "포인트"],
            "level": ["level", "lv", "레벨"],
            "dungeon_clear": ["dungeon_clear", "achievements", "던전클리어", "업적"],
        }

    def get_critical_keys(self) -> list:
        """헌터물 필수 추적 키"""
        return ["awakening_rank", "mana", "skills", "wealth", "reputation", "injuries", "guild", "level"]

    def get_v20_hud_report(self) -> str:
        """헌터 HUD 보고서"""
        return f"""
[🎮 HUNTER STATUS HUD]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Name: {self.pro_data.get("name", "각성자")}
⭐ Rank: {self._get_normalized_val("awakening_rank", "F급")}
🔮 Mana: {self._get_normalized_val("mana", "0")}
📊 Level: {self._get_normalized_val("level", "Lv.1")}

💪 Skills: {self._get_normalized_val("skills", "없음")}
🏢 Guild: {self._get_normalized_val("guild", "무소속")}
💰 Wealth: {self._get_normalized_val("wealth", "0원")}
❤️ Status: {self._get_normalized_val("injuries", "정상")}

🎯 Current Quest: {self._get_normalized_val("current_objective", "생존")}
🏆 Title: {self._get_normalized_val("title", "무명 헌터")}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


class FinanceHUDManager(GenreHUDManager):
    hud_key = "FinanceHUD"
    hud_key_alt = "finance_hud"
    """[투자물] 금융/투자 전용 HUD 시스템"""

    def __init__(self, context) -> None:
        super().__init__(context)
        self.canonical_map = {
            "capital": ["capital", "cash", "liquid_assets", "자본", "현금", "유동자산"],
            "total_assets": ["total_assets", "net_worth", "wealth", "총자산", "순자산"],
            "stocks": ["stocks", "portfolio", "holdings", "주식", "포트폴리오", "보유주식"],
            "real_estate": ["real_estate", "properties", "부동산", "건물"],
            "companies": ["companies", "businesses", "owned_companies", "기업", "회사", "보유기업"],
            "reputation": ["reputation", "credibility", "fame", "평판", "신용도", "명성"],
            "connections": ["connections", "network", "relationships", "인맥", "네트워크", "관계"],
            "current_objective": ["objective", "goal", "current_objective", "목표", "투자목표"],
            "market_insight": ["market_insight", "info_level", "intelligence", "시장통찰력", "정보력"],
            "risk_level": ["risk_level", "risk", "리스크레벨", "위험도"],
            "status": ["status", "condition", "상태", "컨디션"],
            "position": ["position", "title", "직위", "직책"],
            "public_image": ["public_image", "media_presence", "대중이미지", "언론인식"],
        }

    def get_critical_keys(self) -> list:
        """투자물 필수 추적 키"""
        return ["capital", "total_assets", "stocks", "reputation", "connections", "market_insight", "status"]

    def get_v20_hud_report(self) -> str:
        """투자 HUD 보고서"""
        return f"""
[💼 FINANCE STATUS HUD]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Name: {self.pro_data.get("name", "투자자")}
💰 Capital: {self._get_normalized_val("capital", "0원")}
📊 Total Assets: {self._get_normalized_val("total_assets", "0원")}
📈 Stocks: {self._get_normalized_val("stocks", "없음")}

🏢 Companies: {self._get_normalized_val("companies", "없음")}
🏠 Real Estate: {self._get_normalized_val("real_estate", "없음")}
🤝 Connections: {self._get_normalized_val("connections", "평범")}
🧠 Market Insight: {self._get_normalized_val("market_insight", "초보")}

🎯 Investment Goal: {self._get_normalized_val("current_objective", "재산 증식")}
⚡ Status: {self._get_normalized_val("status", "정상")}
🏆 Position: {self._get_normalized_val("position", "개인투자자")}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


class ComposerHUDManager(GenreHUDManager):
    hud_key = "ComposerHUD"
    hud_key_alt = "composer_hud"
    """[작곡가물] 음악 + 산업 전용 HUD 시스템"""

    def __init__(self, context) -> None:
        super().__init__(context)
        self.canonical_map = {
            # 음악 능력
            "composition": ["composition", "composing", "작곡력", "작곡"],
            "arrangement": ["arrangement", "arranging", "편곡력", "편곡"],
            "production": ["production", "producing", "프로듀싱", "제작"],
            "instruments": ["instruments", "instrument", "악기", "연주"],
            # 산업/비즈니스
            "reputation": ["reputation", "fame", "명성", "평판", "인지도"],
            "wealth": ["wealth", "money", "income", "재산", "수입", "자산"],
            "contracts": ["contracts", "deals", "계약", "딜"],
            "company": ["company", "label", "agency", "소속사", "레이블"],
            # 상태
            "awards": ["awards", "prizes", "수상", "상"],
            "discography": ["discography", "works", "albums", "앨범", "작품"],
            "mental_state": ["mental_state", "condition", "정신상태", "컨디션"],
            "current_objective": ["objective", "goal", "current_objective", "목표"],
            "creative_block": ["creative_block", "slump", "슬럼프", "창작고통"],
        }

    def get_critical_keys(self) -> list:
        """작곡가물 필수 추적 키"""
        return ["composition", "arrangement", "production", "reputation", "wealth", "mental_state", "current_objective"]

    def get_v20_hud_report(self) -> str:
        """작곡가 HUD 보고서"""
        return f"""
[🎵 COMPOSER STATUS HUD]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Name: {self.pro_data.get("name", "작곡가")}
🎹 Composition: {self._get_normalized_val("composition", "0")}
🎼 Arrangement: {self._get_normalized_val("arrangement", "0")}
🎧 Production: {self._get_normalized_val("production", "0")}
🎸 Instruments: {self._get_normalized_val("instruments", "없음")}

⭐ Reputation: {self._get_normalized_val("reputation", "무명")}
💰 Wealth: {self._get_normalized_val("wealth", "0원")}
🏢 Company: {self._get_normalized_val("company", "무소속")}
🏆 Awards: {self._get_normalized_val("awards", "없음")}

🎵 Discography: {self._get_normalized_val("discography", "없음")}
🎯 Current Goal: {self._get_normalized_val("current_objective", "데뷔")}
💭 Mental State: {self._get_normalized_val("mental_state", "정상")}
🔥 Creative Block: {self._get_normalized_val("creative_block", "없음")}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


class CookingHUDManager(GenreHUDManager):
    hud_key = "CookingHUD"
    hud_key_alt = "cooking_hud"
    """[요리물] 셰프 등급 + 식당 경영 전용 HUD 시스템"""

    def __init__(self, context) -> None:
        super().__init__(context)
        self.canonical_map = {
            # 셰프 성장축
            "chef_rank": ["chef_rank", "rank", "cooking_level", "요리사등급", "등급", "셰프등급"],
            "signature_dish": ["signature_dish", "best_dish", "specialty", "대표요리", "시그니처"],
            "culinary_techniques": ["culinary_techniques", "techniques", "skills", "조리기법", "기술"],
            "recipe_vault": ["recipe_vault", "recipes", "레시피", "비법"],
            "food_philosophy": ["food_philosophy", "philosophy", "요리철학", "철학"],
            # 식당 경영축
            "restaurant_name": ["restaurant_name", "shop_name", "식당이름", "가게이름"],
            "restaurant_tier": ["restaurant_tier", "tier", "restaurant_rank", "식당등급"],
            "reputation_score": ["reputation_score", "reputation", "fame", "평판", "명성"],
            "monthly_revenue": ["monthly_revenue", "revenue", "월매출", "매출"],
            "capital": ["capital", "funds", "money", "자금", "자본", "운영자금"],
            "customer_loyalty": ["customer_loyalty", "loyalty", "regulars", "단골", "고객충성도"],
            # 공통
            "current_objective": ["objective", "goal", "current_objective", "목표"],
            "status": ["status", "condition", "상태", "컨디션"],
        }

    def get_critical_keys(self) -> list:
        """요리물 필수 추적 키"""
        return [
            "chef_rank",
            "signature_dish",
            "culinary_techniques",
            "restaurant_tier",
            "reputation_score",
            "capital",
            "current_objective",
        ]

    def get_v20_hud_report(self) -> str:
        """요리물 HUD 보고서"""
        return f"""
[🍳 COOKING STATUS HUD]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Name: {self.pro_data.get("name", "요리사")}
👨‍🍳 Chef Rank: {self._get_normalized_val("chef_rank", "수습생")}
🍽️ Signature Dish: {self._get_normalized_val("signature_dish", "없음")}
🔪 Techniques: {self._get_normalized_val("culinary_techniques", "없음")}
📖 Recipes: {self._get_normalized_val("recipe_vault", "없음")}

🏪 Restaurant: {self._get_normalized_val("restaurant_name", "없음")}
⭐ Tier: {self._get_normalized_val("restaurant_tier", "포장마차")}
📊 Reputation: {self._get_normalized_val("reputation_score", "0")}
💰 Capital: {self._get_normalized_val("capital", "0원")}
📈 Revenue: {self._get_normalized_val("monthly_revenue", "0원")}
👥 Regulars: {self._get_normalized_val("customer_loyalty", "0")}

🎯 Current Goal: {self._get_normalized_val("current_objective", "첫 가게 오픈")}
❤️ Status: {self._get_normalized_val("status", "정상")}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


class JoseonHUDManager(GenreHUDManager):
    hud_key = "JoseonHUD"
    hud_key_alt = "joseon_hud"
    """[대체역사물] 조선 시대 관직/당파/신분 전용 HUD 시스템"""

    def __init__(self, context) -> None:
        super().__init__(context)
        self.canonical_map = {
            # 신분/관직
            "social_class": ["social_class", "class", "status", "신분", "계급"],
            "court_rank": ["court_rank", "rank", "grade", "품계", "관품"],
            "position": ["position", "office", "title", "관직", "직위", "벼슬"],
            "faction": ["faction", "party", "political_party", "당파", "붕당"],
            # 영향력/재산
            "political_influence": ["political_influence", "influence", "power", "영향력", "권세"],
            "wealth": ["wealth", "property", "assets", "재산", "전답"],
            "public_trust": ["public_trust", "popularity", "approval", "민심", "민망"],
            # 지식/인맥
            "knowledge": ["knowledge", "skills", "expertise", "지식", "학문", "기술"],
            "connections": ["connections", "network", "allies", "인맥", "교유"],
            # 공통
            "current_objective": ["objective", "goal", "current_objective", "목표"],
            "injuries": ["injuries", "condition", "health", "상태", "건강"],
        }

    def get_critical_keys(self) -> list:
        """대체역사물 필수 추적 키"""
        return [
            "social_class",
            "court_rank",
            "position",
            "faction",
            "political_influence",
            "wealth",
            "public_trust",
            "current_objective",
        ]

    def get_v20_hud_report(self) -> str:
        """대체역사 HUD 보고서"""
        return f"""
[📜 JOSEON STATUS HUD]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Name: {self.pro_data.get("name", "선비")}
🏛️ Social Class: {self._get_normalized_val("social_class", "양반")}
📋 Court Rank: {self._get_normalized_val("court_rank", "무품")}
🎖️ Position: {self._get_normalized_val("position", "없음")}
⚔️ Faction: {self._get_normalized_val("faction", "무소속")}

👑 Influence: {self._get_normalized_val("political_influence", "0")}
💰 Wealth: {self._get_normalized_val("wealth", "빈한")}
👥 Public Trust: {self._get_normalized_val("public_trust", "50")}
📚 Knowledge: {self._get_normalized_val("knowledge", "없음")}
🤝 Connections: {self._get_normalized_val("connections", "없음")}

🎯 Current Goal: {self._get_normalized_val("current_objective", "과거 급제")}
❤️ Status: {self._get_normalized_val("injuries", "정상")}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


class ActorHUDManager(GenreHUDManager):
    hud_key = "ActorHUD"
    hud_key_alt = "actor_hud"
    """[배우물] 연예계 경력 + 인지도 전용 HUD 시스템"""

    def __init__(self, context) -> None:
        super().__init__(context)
        self.canonical_map = {
            # 배우 능력
            "acting_skill": ["acting_skill", "acting", "skill_level", "연기력", "연기"],
            "fame": ["fame", "recognition", "popularity", "인지도", "명성", "인기"],
            "filmography": ["filmography", "works", "credits", "필모그래피", "출연작"],
            # 산업/비즈니스
            "agency": ["agency", "company", "management", "소속사", "매니지먼트"],
            "fandom": ["fandom", "fans", "fan_base", "팬덤", "팬층"],
            "scandal_index": ["scandal_index", "scandal", "controversy", "스캔들지수", "논란도"],
            "box_office": ["box_office", "performance", "record", "흥행성적", "흥행"],
            "wealth": ["wealth", "income", "earnings", "재산", "수입", "출연료"],
            # 인맥/상태
            "network": ["network", "connections", "relationships", "인맥", "업계인맥"],
            "awards": ["awards", "prizes", "trophies", "수상", "수상경력"],
            "reputation": ["reputation", "image", "public_image", "평판", "이미지"],
            "current_objective": ["objective", "goal", "current_objective", "목표"],
            "mental_state": ["mental_state", "condition", "정신상태", "컨디션"],
        }

    def get_critical_keys(self) -> list:
        """배우물 필수 추적 키"""
        return [
            "acting_skill",
            "fame",
            "filmography",
            "agency",
            "fandom",
            "scandal_index",
            "box_office",
            "current_objective",
        ]

    def get_v20_hud_report(self) -> str:
        """배우물 HUD 보고서"""
        return f"""
[🎬 ACTOR STATUS HUD]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Name: {self.pro_data.get("name", "배우")}
🎭 Acting Skill: {self._get_normalized_val("acting_skill", "초보")}
⭐ Fame: {self._get_normalized_val("fame", "무명")}
🎬 Filmography: {self._get_normalized_val("filmography", "없음")}

🏢 Agency: {self._get_normalized_val("agency", "무소속")}
👥 Fandom: {self._get_normalized_val("fandom", "없음")}
📊 Scandal Index: {self._get_normalized_val("scandal_index", "0")}
💰 Wealth: {self._get_normalized_val("wealth", "0원")}
🎯 Box Office: {self._get_normalized_val("box_office", "없음")}

🏆 Awards: {self._get_normalized_val("awards", "없음")}
🤝 Network: {self._get_normalized_val("network", "없음")}
🎯 Current Goal: {self._get_normalized_val("current_objective", "데뷔")}
💭 Mental State: {self._get_normalized_val("mental_state", "정상")}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


class SportsHUDManager(GenreHUDManager):
    hud_key = "SportsHUD"
    hud_key_alt = "sports_hud"
    """[스포츠물] 선수 성장 + 팀 스포츠 전용 HUD 시스템"""

    def __init__(self, context) -> None:
        super().__init__(context)
        self.canonical_map = {
            "athlete_tier": ["athlete_tier", "tier", "rank", "선수등급", "등급"],
            "sport_type": ["sport_type", "sport", "종목"],
            "position": ["position", "role", "포지션"],
            "physical_stats": ["physical_stats", "stats", "능력치", "신체능력"],
            "record": ["record", "match_record", "전적", "승패"],
            "skills": ["skills", "techniques", "기술", "특기"],
            "team": ["team", "club", "소속팀", "팀", "구단"],
            "ranking": ["ranking", "league_rank", "순위", "랭킹"],
            "wealth": ["wealth", "salary", "연봉", "자산"],
            "reputation": ["reputation", "fame", "명성", "인기"],
            "injuries": ["injuries", "injury_status", "condition", "부상", "컨디션"],
            "mental_state": ["mental_state", "mentality", "멘탈"],
            "current_objective": ["objective", "goal", "current_objective", "목표"],
            "sponsorship": ["sponsorship", "sponsors", "스폰서"],
            "coach": ["coach", "trainer", "코치", "트레이너"],
        }

    def get_critical_keys(self) -> list:
        """스포츠물 필수 추적 키"""
        return [
            "athlete_tier",
            "sport_type",
            "physical_stats",
            "record",
            "team",
            "ranking",
            "reputation",
            "current_objective",
        ]

    def get_v20_hud_report(self) -> str:
        """스포츠물 HUD 보고서"""
        return f"""
[🏆 SPORTS STATUS HUD]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Name: {self.pro_data.get("name", "선수")}
⭐ Athlete Tier: {self._get_normalized_val("athlete_tier", "아마추어")}
⚽ Sport: {self._get_normalized_val("sport_type", "미정")}
🎯 Position: {self._get_normalized_val("position", "미정")}

💪 Physical Stats: {self._get_normalized_val("physical_stats", "기본")}
📊 Record: {self._get_normalized_val("record", "없음")}
🔧 Skills: {self._get_normalized_val("skills", "없음")}
🏢 Team: {self._get_normalized_val("team", "무소속")}
🏅 Ranking: {self._get_normalized_val("ranking", "무랭킹")}

💰 Wealth: {self._get_normalized_val("wealth", "0원")}
⭐ Reputation: {self._get_normalized_val("reputation", "무명")}
❤️ Injuries: {self._get_normalized_val("injuries", "정상")}
💭 Mental: {self._get_normalized_val("mental_state", "정상")}
🎯 Current Goal: {self._get_normalized_val("current_objective", "프로 데뷔")}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


class MedicalHUDManager(GenreHUDManager):
    hud_key = "MedicalHUD"
    hud_key_alt = "medical_hud"
    """[의학물] 의사 직급 + 병원 시스템 전용 HUD 시스템"""

    def __init__(self, context) -> None:
        super().__init__(context)
        self.canonical_map = {
            "doctor_rank": ["doctor_rank", "position", "rank", "직급", "직위"],
            "specialty": ["specialty", "department", "전공과", "전공"],
            "hospital": ["hospital", "institution", "병원", "소속"],
            "surgery_count": ["surgery_count", "operations", "수술횟수"],
            "success_rate": ["success_rate", "rate", "성공률"],
            "medical_skills": ["medical_skills", "skills", "procedures", "의술"],
            "research": ["research", "papers", "연구", "논문"],
            "reputation": ["reputation", "fame", "명성", "평판"],
            "wealth": ["wealth", "income", "재산", "수입"],
            "mental_state": ["mental_state", "mentality", "정신상태"],
            "patients": ["patients", "cases", "환자", "케이스"],
            "network": ["network", "connections", "인맥"],
            "current_objective": ["objective", "goal", "current_objective", "목표"],
            "malpractice_record": ["malpractice_record", "malpractice", "의료사고"],
        }

    def get_critical_keys(self) -> list:
        """의학물 필수 추적 키"""
        return [
            "doctor_rank",
            "specialty",
            "hospital",
            "surgery_count",
            "success_rate",
            "reputation",
            "current_objective",
        ]

    def get_v20_hud_report(self) -> str:
        """의학물 HUD 보고서"""
        return f"""
[🏥 MEDICAL STATUS HUD]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Name: {self.pro_data.get("name", "의사")}
🩺 Doctor Rank: {self._get_normalized_val("doctor_rank", "의대생")}
🔬 Specialty: {self._get_normalized_val("specialty", "미정")}
🏥 Hospital: {self._get_normalized_val("hospital", "미정")}

🔪 Surgery Count: {self._get_normalized_val("surgery_count", "0")}
📊 Success Rate: {self._get_normalized_val("success_rate", "0%")}
💊 Medical Skills: {self._get_normalized_val("medical_skills", "없음")}
📖 Research: {self._get_normalized_val("research", "없음")}

⭐ Reputation: {self._get_normalized_val("reputation", "무명")}
💰 Wealth: {self._get_normalized_val("wealth", "0원")}
💭 Mental State: {self._get_normalized_val("mental_state", "정상")}
🤝 Network: {self._get_normalized_val("network", "없음")}
🎯 Current Goal: {self._get_normalized_val("current_objective", "전문의 취득")}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


class FantasyHUDManager(GenreHUDManager):
    hud_key = "FantasyHUD"
    hud_key_alt = "fantasy_hud"
    legacy_hud_keys = ("MartialHUD",)
    """[V66] 판타지(이세계) 전용 HUD 시스템"""

    def __init__(self, context) -> None:
        super().__init__(context)
        self.canonical_map = {
            "magic_tier": ["magic_tier", "realm", "magic_level", "마법등급", "마법티어"],
            "mana": ["mana", "magic_power", "mp", "마나", "마력"],
            "spells": ["spells", "spell_list", "magic_skills", "주문", "마법목록"],
            "race": ["race", "species", "종족"],
            "blessings": ["blessings", "buffs", "축복", "버프"],
            "curses": ["curses", "debuffs", "저주", "디버프"],
            "equipment": ["equipment", "items", "장비", "아이템"],
            "wealth": ["wealth", "gold", "money", "골드", "재산"],
            "injuries": ["injuries", "status", "hp", "부상", "상태"],
            "reputation": ["reputation", "fame", "명성", "평판"],
            "guild": ["guild", "party", "affiliation", "길드", "소속"],
            "current_objective": ["objective", "quest", "목표", "퀘스트"],
            "level": ["level", "lv", "레벨"],
        }

    def get_critical_keys(self) -> list:
        """[V70] 판타지 필수 추적 키"""
        return [
            "magic_tier",
            "mana",
            "spells",
            "race",
            "level",
            "equipment",
            "wealth",
            "injuries",
            "reputation",
            "current_objective",
        ]

    def get_v20_hud_report(self) -> str:
        """[V70] 판타지 HUD 보고서"""
        return f"""
[🧙 FANTASY STATUS HUD]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Name: {self.pro_data.get("name", "모험자")}
⭐ Magic Tier: {self._get_normalized_val("magic_tier", "견습")}
🔮 Mana: {self._get_normalized_val("mana", "100")}
📊 Level: {self._get_normalized_val("level", "1")}
🧬 Race: {self._get_normalized_val("race", "인간")}

📜 Spells: {self._get_normalized_val("spells", "없음")}
✨ Blessings: {self._get_normalized_val("blessings", "없음")}
💀 Curses: {self._get_normalized_val("curses", "없음")}
🛡️ Equipment: {self._get_normalized_val("equipment", "없음")}

🏢 Guild: {self._get_normalized_val("guild", "무소속")}
💰 Wealth: {self._get_normalized_val("wealth", "0골드")}
🏆 Reputation: {self._get_normalized_val("reputation", "무명")}
❤️ Status: {self._get_normalized_val("injuries", "정상")}

🎯 Current Quest: {self._get_normalized_val("current_objective", "생존")}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    def snapshot(self) -> dict:
        return dict(self.pro_data)


def create_hud_manager(genre_type, context):
    """
    [V40 Factory] 장르별 HUD 매니저 생성 팩토리 함수

    Args:
        genre_type: 'wuxia' | 'hunter' | 'investment' | 'composer' | 'cooking' | 'alt_history' | 'actor' | 'sports' | 'medical'
        context: ProjectManager 인스턴스

    Returns:
        GenreHUDManager 구현체
    """
    from .martial_manager import MartialManager

    if genre_type == "wuxia":
        return MartialManager(context)
    elif genre_type == "hunter":
        return HunterHUDManager(context)
    elif genre_type == "investment":
        return FinanceHUDManager(context)
    elif genre_type == "composer":
        return ComposerHUDManager(context)
    elif genre_type == "cooking":
        return CookingHUDManager(context)
    elif genre_type == "alt_history":
        return JoseonHUDManager(context)
    elif genre_type == "actor":
        return ActorHUDManager(context)
    elif genre_type == "sports":
        return SportsHUDManager(context)
    elif genre_type == "medical":
        return MedicalHUDManager(context)
    elif genre_type == "fantasy":
        return FantasyHUDManager(context)  # [V66]
    else:
        # [V70] 미매핑 장르 (romance, politics, military 등) → MartialManager 폴백
        logging.warning(f" [V70] 미매핑 장르 '{genre_type}' → MartialManager 폴백")
        return MartialManager(context)  # [V70] WuxiaHUDManager → MartialManager (NameError 수정)


def validate_hud_compatibility(hud_manager, required_attrs: list = None) -> dict:
    """
    [V61.3] HUD 호환성 검증 - 필수 속성 존재 여부 체크

    Args:
        hud_manager: GenreHUDManager 인스턴스
        required_attrs: 체크할 속성 목록 (기본: Stage 4에서 사용하는 속성들)

    Returns:
        {
            "valid": bool,
            "genre": str,
            "missing": [str],  # 누락된 속성
            "warnings": [str]
        }
    """
    if required_attrs is None:
        # Stage 4에서 사용하는 주요 속성들
        required_attrs = [
            ("pro_root", "property"),
            ("pro_data", "property"),
            ("get_v20_hud_report", "method"),
            ("get_critical_keys", "method"),
            ("update_physical_status", "method"),
        ]

    # 선택적 속성 (무협에만 있음)
    optional_attrs = [
        ("inventory", "property"),
        ("techniques", "property"),
        ("snapshot", "method"),
        ("bulk_update", "method"),
    ]

    result = {"valid": True, "genre": type(hud_manager).__name__, "missing": [], "optional_missing": [], "warnings": []}

    # 필수 속성 체크
    for attr_name, attr_type in required_attrs:
        if not hasattr(hud_manager, attr_name):
            result["missing"].append(f"{attr_name} ({attr_type})")
            result["valid"] = False

    # 선택적 속성 체크 (경고만)
    for attr_name, attr_type in optional_attrs:
        if not hasattr(hud_manager, attr_name):
            result["optional_missing"].append(f"{attr_name} ({attr_type})")
            result["warnings"].append(f"'{attr_name}' 속성 없음 - 무협 전용 기능, 다른 장르에서는 hasattr 체크 필요")

    return result


def log_hud_compatibility_report(hud_manager, logger=None) -> None:
    """
    [V61.3] HUD 호환성 보고서 출력

    Args:
        hud_manager: GenreHUDManager 인스턴스
        logger: 로거 함수 (기본: print)
    """
    if logger is None:
        logger = print

    report = validate_hud_compatibility(hud_manager)

    logger(f"   🔍 [V61.3] HUD 호환성 체크: {report['genre']}")

    if report["valid"]:
        logger("      ✅ 필수 속성 모두 존재")
    else:
        logger(f"      ❌ 누락된 필수 속성: {', '.join(report['missing'])}")

    if report["optional_missing"]:
        logger(f"      ⚠️ 선택적 속성 누락 (정상): {', '.join(report['optional_missing'])}")
