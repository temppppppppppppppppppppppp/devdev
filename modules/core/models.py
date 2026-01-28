class Bible:
    def __init__(self, project_name, genre, world=None, characters=None, 
                 inventory=None, plot_threads=None, episode_history=None, **kwargs):
        self.project_name = project_name
        self.genre = genre
        self.world = world if world is not None else {}
        self.characters = characters if characters is not None else {}
        self.inventory = inventory if inventory is not None else []
        self.plot_threads = plot_threads if plot_threads is not None else []
        self.episode_history = episode_history if episode_history is not None else []
        
        # 추가적인 데이터가 들어올 경우를 대비한 유연성 확보
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def summary(self):
        """설계자(Architect)가 이해하기 쉬운 요약본 생성"""
        mc = self.characters.get('main', {})
        return {
            "주인공": mc.get('name', '알 수 없음'),
            "상태": mc.get('description', ''),
            "인벤토리": self.inventory[:5] if self.inventory else [],
            "현재위치": self.world.get('current_location', '미정'),
            "활성복선": self.plot_threads[:3] if self.plot_threads else []
        }

    def model_dump_json(self, indent=2):
        """저장을 위한 딕셔너리 변환 (json.dumps용)"""
        import json
        return json.dumps(self.__dict__, ensure_ascii=False, indent=indent)