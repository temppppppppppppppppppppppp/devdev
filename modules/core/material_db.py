class MaterialDB:
    """[Wuxia Master Database] 강호의 기연, 영약, 신병이기 및 무림의 암투 소재."""
    MATERIALS = {
        "HERBS": ["천년설삼 (60년 공력)", "만년화리 (양기의 정수)", "빙백신주 (한기 제어)", "소림 대환단", "구전환혼단", "공청석유"],
        "WEAPONS": ["만년한철검 (불괴)", "현철중검 (패도)", "천잠사 (포박)", "벽력탄 (당가 암기)", "무영독침", "청강검"],
        "MANUALS": ["자하신공 원본", "천마신공 (패도)", "유운보법 (회피)", "금강불괴신공 (방어)", "흡성대법 (금기)"],
        "LOCATIONS": ["절벽 아래 동굴", "지하 장경각", "사막 혈교 본거지", "동정호 수정궁", "만년설산 수정 동굴"]
    }
    OBJECTIVES = [
        "멸문지화의 원수를 찾아 구족을 멸한다", 
        "실전된 가문의 비급을 되찾아 가문을 중흥시킨다",
        "마교의 중원 침공을 막기 위해 흩어진 구파일방을 규합한다",
        "천하제일인의 자리에 올라 무림의 질서를 재편한다"
    ]
    @staticmethod
    def get_random_material(category="HERBS"):
        import random
        return random.choice(MaterialDB.MATERIALS.get(category, MaterialDB.MATERIALS["HERBS"]))
