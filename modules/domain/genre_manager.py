import logging

from .strategies.composer_strategy import ComposerStrategy
from .strategies.cooking_strategy import CookingStrategy
from .strategies.hunter_strategy import HunterStrategy
from .strategies.investment_strategy import InvestmentStrategy
from .strategies.medical_strategy import MedicalStrategy
from .strategies.sports_strategy import SportsStrategy
from .strategies.wuxia_strategy import WuxiaStrategy


class GenreManager:
    def __init__(self, studio_system) -> None:
        self.studio = studio_system

    def get_strategy(self):
        """[V40 Multi-Genre] 프로젝트의 장르에 따라 동적으로 전략을 반환합니다."""
        # 프로젝트에 저장된 장르 정보 확인
        genre_type = "wuxia"  # 기본값

        if hasattr(self.studio, "project") and self.studio.project:
            if hasattr(self.studio.project, "genre"):
                genre_type = self.studio.project.genre.get("type", "wuxia")
            elif hasattr(self.studio.project, "db"):
                # DB에서 장르 정보 로드 시도
                stored_genre = self.studio.project.db.load_anchor("genre_info")
                if stored_genre:
                    genre_type = stored_genre.get("type", "wuxia")

        # 장르별 전략 반환
        if genre_type == "wuxia":
            return WuxiaStrategy(self.studio)
        elif genre_type == "hunter":
            return HunterStrategy(self.studio)
        elif genre_type == "investment":
            return InvestmentStrategy(self.studio)
        elif genre_type == "composer":
            return ComposerStrategy(self.studio)
        elif genre_type == "cooking":
            return CookingStrategy(self.studio)
        elif genre_type == "sports":
            return SportsStrategy(self.studio)
        elif genre_type == "medical":
            return MedicalStrategy(self.studio)
        else:
            # 알 수 없는 장르는 무협으로 폴백
            logging.warning(f"⚠️ [GenreManager] 알 수 없는 장르: {genre_type}, 무협으로 대체합니다.")
            return WuxiaStrategy(self.studio)
