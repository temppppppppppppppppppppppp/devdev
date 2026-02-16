import json


class Bible:
    def __init__(
        self,
        project_name: str,
        genre: str = "WUXIA",
        world: dict = None,
        characters: dict = None,
        inventory: list = None,
        plot_threads: list = None,
        episode_history: list = None,
        **kwargs,
    ) -> None:
        self.project_name = project_name
        self.genre = genre
        self.world = world if world is not None else {"current_location": "미정", "sect_relations": {}}
        self.characters = characters if characters is not None else {}
        self.inventory = inventory if inventory is not None else []
        self.plot_threads = plot_threads if plot_threads is not None else []
        self.episode_history = episode_history if episode_history is not None else []

        # [Wuxia Density Upgrade] 무협 전용 핵심 수치 강제화 (SAMPLE.txt 기반)
        mc = self.characters.get("main", {})
        self.realm = mc.get("realm", "하수")  # 현재 경지
        self.internal_energy = mc.get("internal_energy", 0)  # 내공(갑자)
        self.simbeop = mc.get("simbeop", "기초심법")  # 익힌 심법
        self.edge = mc.get("edge", "알 수 없는 기개")  # 주인공의 차별점(Edge)

        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def summary(self) -> dict:
        """설계자(Architect)와 작가(Writer)를 위한 고밀도 강호 브리핑"""
        mc = self.characters.get("main", {})

        # 은원 관계 중 가장 영향력 있는 데이터 추출 (KarmaService 연동용)
        relations = self.world.get("sect_relations", {})
        top_karma = sorted(relations.items(), key=lambda x: abs(x[1]), reverse=True)[:2]

        return {
            "강호의 인물": f"{mc.get('name')} (경지: {self.realm} / 내공: {self.internal_energy}년)",
            "연마중인 절학": f"{self.simbeop}, {mc.get('main_weapon_art', '기초무공')}",
            "현재 발을 디딘 곳": self.world.get("current_location", "강호 어딘가"),
            "주요 은원(Karma)": dict(top_karma),
            "미회수 복선": [t.get("name") for t in self.plot_threads if t.get("status") == "planted"][:3],
            "주인공의 엣지(Edge)": self.edge,
        }

    def update_martial_status(self, realm: str = None, energy_gain: int = 0) -> None:
        """주인공의 무학적 성장을 데이터에 영구 기록"""
        if realm:
            self.realm = realm
        self.internal_energy += energy_gain
        if "main" in self.characters:
            self.characters["main"]["realm"] = self.realm
            self.characters["main"]["internal_energy"] = self.internal_energy

    def model_dump_json(self, indent: int = 2) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False, indent=indent)
