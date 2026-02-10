"""[V64.P4] ChiefWriter 프롬프트 템플릿 외부화.

ChiefWriter의 대형 프롬프트 문자열을 코드 로직에서 분리.
[V65] C-4 Part 2: 잔존 프롬프트 4개 추가 외부화.
"""

# -- ChiefWriter Output Format Template --  [V64.P4]

# [V60.82] 프롬프트 템플릿 상수 (프리컴파일)
PROMPT_TEMPLATE_OUTPUT = """
### 📌 출력 형식 (Strict JSON)
{{
    "title": "에피소드 제목 (한글만)",
    "content": "5,000자 이상의 소설 본문 (줄바꿈은 \\n)",
    "state_updates": {{
        "internal_energy": "현재 내공 % (0-100)",
        "realm": "경지명 또는 현상 유지",
        "causal_injuries": "부상 상태",
        "wealth": "현재 총 자산",
        "misunderstanding": 0-100,
        "obsession": 0-100,
        "equipment": ["소지품 목록"],
        "martial_arts": ["무공 목록"]
    }},
    "writing_strategy": "{strategy}",
    "key_scenes_covered": ["반영한 씬 목록"]
}}
"""


# -- ChiefWriter Common Context Template --  [V64.P4]
# 이 템플릿은 _build_common_context()에서 사용. 많은 동적 섹션을 조립하므로
# 최종 f-string은 소스 파일에 유지하되, 정적 부분인 Common Rules와 집필 지침을 여기에 외부화.

COMMON_RULES_SECTION = """
### 🔥 변환 원칙 (Common Rules) - 위반 시 AI티 판정
1. 감정어 삭제 → 행동 변환: '화가 났다', '슬펐다', '당황했다' 같은 추상적 감정 단어를 금지한다. 대신 미세한 표정 변화, 손짓, 호흡, 시선 처리, 주변 사물과의 상호작용으로 감정을 유추하게 만들어라. (예: "그는 초조해했다" → "그는 마른입술을 혀로 훑으며 펜을 톡, 톡, 책상에 두드렸다.")
2. 감각적 묘사 강화 (오감 활용): 상황을 설명하지 말고, 독자가 그 현장에 있는 것처럼 느끼게 해라. 소리(청각), 냄새(후각), 질감(촉각)을 문장에 녹여내라.
3. 요약된 대화의 장면화: "그들은 협상에 대해 길게 논쟁했다"처럼 요약된 서술을 금지한다. 날 선 티키타카(대화)가 오가는 실제 장면으로 풀어 써라.
4. 문장 밀도 조절: 무의미한 미사여구로 문장 길이를 늘리지 마라. 불필요한 접속사와 수식어는 쳐내고, '동사(Action)' 위주로 문장을 짧고 힘 있게 끊어쳐라.
5. [V63] 예측 가능한 전개 금지 → 반전 삽입: 독자가 예상하는 결과를 한 번 비틀어라. (예: "적이 도발했다 → 주인공이 화를 내며 싸웠다" ❌ → "적이 도발했다 → 주인공이 무시하고 지나가자 적이 당황해 실수했다" ✅)
6. [V63] 긴장 유지 원칙: 매 씬의 마지막 문장은 불확실성/궁금증을 남겨라. (예: "그렇게 싸움은 끝났다." ❌ → "싸움은 끝났다. 하지만 구석에서 지켜보던 그림자가 먼저 움직이기 시작했다." ✅)
7. [V63] 캐릭터 고유 반응: 같은 상황에서도 캐릭터마다 다르게 반응시켜라. (예: 모두 "놀라며 경악했다" ❌ → 장로는 찻잔을 내려놓고, 소녀는 주먹을 움켜쥐고, 하인은 몸을 낮추는 ✅)
"""

WRITING_GUIDELINES_SECTION = """
### 📌 집필 지침 (위반 시 즉시 REJECT)
1. ⚠️ 분량: 반드시 5,000자 이상. 4,999자 이하는 무조건 REJECT. 부족하면 장면 묘사, 인물 심리, 대화를 확장하라
2. 모든 씬을 균등한 비중으로 전개 - 각 씬 최소 1,000자 이상
3. 후반부 급전개/요약 절대 금지 - 마지막 씬도 앞 씬과 동일한 밀도로 작성
4. [V63] 클리프행어 엔딩: 단순 "...했다"가 아닌, 독자가 다음 화를 즉시 누를 수밖에 없는 미해결 질문/위기/반전으로 끝내라. (예: "그는 집으로 돌아갔다." ❌ → "문을 열자, 이미 죽었어야 할 남자가 탁자 앞에 앉아 있었다." ✅)
5. 죽은 NPC 부활, 미습득 무공 사용 절대 금지
6. 영문 병기 금지 - "윈도우(Windows)", "검(Sword)" 같은 한글(English) 표기 금지. 한글만 사용
"""


# ============================================================================
# [V65] C-4 Part 2: 잔존 인라인 프롬프트 외부화
# ============================================================================

# -- 원시인 모드 제약 섹션 (폴백용 상수) --  [V65]
PRIMITIVE_CONSTRAINT_FALLBACK = """
### 🚨 [원시인 모드] 현대 용어 절대 금지!
❌ 금지: 헬스장, 바벨, 병원, 학교, 시스템, 스트레스, 축구, 자동차
✅ 대체: 무관, 석추, 의원, 서당, 체계, 심기, 격구, 마차
⚠️ 회귀자라도 현대 용어 사용 불가!
"""

MODERN_ORIGIN_SECTION = """
### ✅ [현대인 모드] 현대 지식 활용 가능
주인공은 현대 세계 출신으로 현대 지식을 내적 독백에서 활용 가능합니다.
단, 대화에서 현대 용어 남발은 자제하고 세계관에 맞게 표현하세요.
"""


def build_chief_writer_main_prompt(
    *,
    ep_num: int,
    dna_instruction: str,
    purism_section: str,
    world_origin_constraint_section: str,
    feedback_section: str,
    constraint_section: str,
    future_guard_section: str,
    past_guard_section: str,
    writer_core_section: str,
    hud_anomaly_section: str,
    scene_breakdown: str,
    prev_digest: str,
    prev_ending: str,
    hud_report: str,
    high_density_hud_section: str,
    hud_trend_section: str,
    npc_equipment_section: str,
    npc_frequency_section: str,
    arc_doc: str,
    core_identity_desire: str,
    style_guide: str,
    common_rules: str,
    writing_guidelines: str,
) -> str:
    """[V65] _build_common_context() 메인 프롬프트 템플릿.

    호출부에서 self._escape_braces() 처리 완료된 값을 전달받는다.
    """
    return f"""
[Role] 웹소설 1타 작가 (Chief Writer)
[Task] 제{ep_num}화 원고를 Blueprint 기반으로 집필하라.

### 핵심 철학
"Blueprint를 토대로 양질의 원고를 연속성 있게 생산한다"

{dna_instruction}

{purism_section}

{world_origin_constraint_section}

{feedback_section}
{constraint_section}

{future_guard_section}

{past_guard_section}

{writer_core_section}

{hud_anomaly_section}

### 📋 [STEP 1: Blueprint 분석]
아래 Blueprint의 모든 씬을 파악하고, 누락 없이 반영하라.

{scene_breakdown}

### 📋 [STEP 2: 연속성 확인]
{prev_digest}

직전 화 엔딩에서 자연스럽게 이어져야 한다. 위 다이제스트의 상태를 반드시 준수하라.

[직전 화 마지막 장면]
...{prev_ending}

### 📋 [STEP 3: 현재 상태 반영]
{hud_report}

{high_density_hud_section}

{hud_trend_section}

⚠️ 필수 준수:
- 현재 경지/내공 범위 내에서만 무공 사용
- 부상 상태는 전투/행동에 반영
- 소지품/자금 상태 일관성 유지

{npc_equipment_section}

{npc_frequency_section}

### 📋 [STEP 4: Arc 전술 참조]
{arc_doc}

### 📋 [STEP 5: 세계관 설정]
- 주인공 동기: {core_identity_desire}

### 📋 [STEP 6: 문체 DNA 가이드 - 위반 시 AI티 판정]
{style_guide}

{common_rules}
{writing_guidelines}
"""


def get_fix_issues_prompt(
    *,
    fix_instructions_text: str,
    hud_report_escaped: str,
    manuscript_escaped: str,
) -> str:
    """[V65] _fix_issues() 교정 프롬프트 템플릿.

    호출부에서 self._escape_braces() 처리 완료된 값을 전달받는다.
    """
    return f"""
[Role] 원고 교정 전문가
[Task] 아래 원고에서 발견된 문제를 수정하라.

### 발견된 문제
{fix_instructions_text}

### 현재 HUD 상태 (참고)
{hud_report_escaped}

### 수정 대상 원고
{manuscript_escaped}

### 출력 형식
수정된 JSON 원고만 출력하라. 설명 없이 JSON만.
"""


def get_anti_trope_instructions(*, genre_name: str) -> str:
    """[V65] 반클리셰 명령 프롬프트 템플릿."""
    return f"""
[ANTI-TROPE PROTOCOL - 장르 관습 재정의]

이 작품은 일반적인 {genre_name}물과 다릅니다. 다음 클리셰는 절대 사용하지 마십시오:

1. "약해 보이는 주인공" 클리셰 금지
   - X "허름한 행색", "평범해 보이는", "별 볼일 없어 보이는"
   - O 주인공의 실제 HUD 상태를 직접 반영
   - O "증표를 본 순간 안색이 창백해졌다" (데이터 기반 묘사)

2. "무시-사이다" 공식 과다 사용 금지
   - X 매 에피소드마다 무시당하고 압도하는 반복
   - O 주인공의 명성/권위가 증가하면 무시는 감소해야 함
   - O 무시가 필요하면 반드시 알리바이 (정보 차단, 변장 등)

3. "조연의 영구 생존" 클리셰 금지
   - X 모욕한 하인이 아무 처벌 없이 계속 등장
   - O 모욕/배신한 조연은 반드시 청산 (처단/퇴장/굴복)

4. "순간 회복" 클리셰 금지
   - X 전투 중 부상 -> 다음 장면에서 멀쩡함 (설명 없이)
   - O 부상은 지속적으로 영향 주거나, 치료 과정 명시

5. "NPC의 기억상실" 클리셰 금지
   - X 이전 화에서 경외했던 NPC가 이번 화에서 다시 무시
   - O 관계는 단방향 발전 (무시->경외는 가능, 경외->무시는 정당화 필요)

[당신이 쓰려는 문장이 위 클리셰에 해당하는가? YES -> 다시 쓰십시오]
"""
