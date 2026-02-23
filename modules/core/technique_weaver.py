class TechniqueWeaver:
    """[V24 Sovereign] 무도십이류(武道十二流)의 물리적 충돌과 인과를 계산하는 범용 엔진"""

    def __init__(self) -> None:
        # 무도십이류의 절대적 물리 속성 정의
        self.streams_physics = {
            "강(强)": {"vector": "직선/폭발", "sound": "파성(破聲)", "impact": "분쇄/파편"},
            "중(重)": {"vector": "하강/압착", "sound": "굉음(轟音)", "impact": "지면함몰/골절"},
            "패(覇)": {"vector": "방사/진동", "sound": "공명(共鳴)", "impact": "기세억눌림/주변파손"},
            "유(柔)": {"vector": "곡선/회전", "sound": "마찰음(摩擦)", "impact": "힘의반사/방향전환"},
            "쾌(快)": {"vector": "점/선", "sound": "예음(銳音)", "impact": "잔상/다중타격"},
            "비(飛)": {"vector": "상승/공간", "sound": "풍음(風音)", "impact": "중력무시/사각공격"},
            "둔(鈍)": {"vector": "정지/반동", "sound": "둔탁음", "impact": "충격흡수/무게중심유지"},
            "환(幻)": {"vector": "불규칙/분산", "sound": "환청", "impact": "시각왜곡/허상"},
            "산(散)": {"vector": "해체/입자", "sound": "소멸음", "impact": "진기분해/흐름차단"},
            "자(刺)": {"vector": "일점집중", "sound": "파공음", "impact": "관통/내부파괴"},
            "암(暗)": {"vector": "소리없음", "sound": "침묵", "impact": "기척소멸/급소기습"},
            "밀(밀)": {"vector": "연결/그물", "sound": "금속음", "impact": "공간봉쇄/지속압박"},
        }

    # [수정 완료] main.py의 호출 규격에 맞춰 함수명 변경 (resolve_collision -> weave_v20_combat)
    def weave_v20_combat(self, mc_tech: str, enemy_style: str) -> dict:  #
        """[V24] 두 무공의 성질이 충돌했을 때의 물리적 상호작용 계산"""

        # 공격자(주인공/조연)와 방어자 성질에 따른 물리 속성 매칭
        # (현재 main.py 로직상 mc_tech은 이름으로, enemy_style은 십이류 성질로 수혈됨)
        self.streams_physics.get("강(强)")  # 기본값 설정
        def_phys = self.streams_physics.get(enemy_style, self.streams_physics["강(强)"])

        # [Collision Blueprint] 모든 인물에게 적용되는 보편적 물리 결과
        return {
            "interaction": {
                "vector_clash": f"공방의 궤적이 {def_phys['vector']}와 충돌",
                "sound_landscape": f"{def_phys['sound']}의 파동이 전장에 공명함",
                "environmental_damage": f"{def_phys['impact']} 현상이 주변 환경을 파괴",
            },
            "rendering_guideline": (
                f"{mc_tech}의 진기와 {enemy_style}의 성질이 부딪히며 발생하는 "
                f"에너지의 인과관계를 물리 법칙에 따라 묘사하라. "
                f"특히 {def_phys['impact']}이 발생하는 지점의 시각적 파괴력을 극대화할 것."
            ),
        }
