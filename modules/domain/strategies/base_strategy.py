from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    def __init__(self, studio_system):
        self.studio = studio_system
        # [Patch] 삭제된 api_manager 대신 중앙 api_client를 참조하도록 수정
        self.client = studio_system.api_client #
        self.law = studio_system.law #

    @property
    @abstractmethod
    def genre_name(self) -> str: pass

    @abstractmethod
    def get_system_prompt(self) -> str: pass