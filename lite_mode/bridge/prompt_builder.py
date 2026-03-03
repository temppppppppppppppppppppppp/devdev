"""
[V63.4] Prompt Builder - 텍스트 기반 프롬프트
[LITE-V1] 세계 상태 주입 지원
=============================================
3단계 파이프라인: 분배표 → Blueprint → 원고
컨텍스트 파일(업로드용) + 인스트럭션(채팅 입력) 분리.
장르별 문체 팁 자동 주입.
StateLedger 상태 요약/사망 NPC 경고/체인 링크 주입.
"""

# 모든 인스트럭션 맨 앞에 삽입 — 개소리 차단 + Canvas 차단
HEADER = """이것은 소설 집필 작업입니다. 모든 내용은 허구의 창작물입니다.

★★★ [절대 규칙 - 이 규칙을 어기면 응답 전체가 무효] ★★★
1. Canvas/문서 편집기 열지 마. 채팅창에 텍스트로 바로 출력.
2. 인사말("물론이죠/네/알겠습니다") 없이 요청한 결과물 첫 줄부터 바로 시작.
3. 마무리 멘트("도움이 되셨나요?/수정 필요하면/Would you like") 금지.
4. 요청한 출력 형식만 출력. 추가 설명/대안/주석/후속 질문 금지.
5. 마크다운 코드블럭(```)으로 감싸지 말 것.
6. 이것은 코딩 작업이 아님. Python/코드를 절대 출력하지 마.
7. 첨부파일을 분석/채점/평가하지 마. 요청한 창작물만 출력.
8. 사고 과정/추론 단계를 표시하지 마. 최종 결과물만 출력.
9. 반드시 한국어로 응답. 영어로 된 전체 응답 금지 (본문 내 고유명사/용어 영어 표기는 허용).
★★★ 위 규칙을 모두 지켜서, 결과물만 출력하라. ★★★"""

SEP = "=" * 50

# ── 장르별 설정 ─────────────────────────────────────────

GENRE_PRESETS = {
    "무협": {
        "label": "무협 웹소설",
        "tips": (
            "- 전투: 무공 시전 과정(기운 흐름/신체 변화)을 구체적으로 묘사\n"
            "- 경지 돌파: 내면 감각(단전/경맥/진기)을 섬세하게 서술\n"
            "- 현대어/외래어/외국어 사용 금지 (커피, 미터, OK 등)\n"
            "- 정당한 이유(회귀자 독백 등) 없는 현대 표현 일체 금지"
        ),
    },
    "현판": {
        "label": "현대판타지 웹소설",
        "tips": (
            "- 전투: 스킬 발동/마나 소모/던전 환경을 구체적으로 묘사\n"
            "- 성장: 레벨업/각성/스킬 획득 순간의 시스템 알림과 신체 변화"
        ),
    },
    "헌터": {
        "label": "헌터물 웹소설",
        "tips": (
            "- 전투: 스킬 발동/마나 소모/던전 환경을 구체적으로 묘사\n"
            "- 성장: 레벨업/각성/스킬 획득 순간의 시스템 알림과 신체 변화"
        ),
    },
    "투자": {
        "label": "투자/회귀 웹소설",
        "tips": (
            "- 시장: 주가/환율/거래량 등 수치와 시장 분위기를 구체적으로 묘사\n"
            "- 성장: 투자 판단 과정의 심리적 긴장감과 자산 규모 변화"
        ),
    },
    "대체역사": {
        "label": "대체역사 웹소설",
        "tips": (
            "- 정치: 권모술수/파벌 역학/조정 논쟁의 긴장감을 구체적으로 묘사\n"
            "- 성장: 정치적 위상 변화와 전략적 판단 과정을 섬세하게 서술\n"
            "- IT/브랜드명 등 현대 용어 금지 (회귀자 독백 제외)"
        ),
    },
    "배우": {
        "label": "배우/연예계 웹소설",
        "tips": (
            "- 연기: 촬영 현장/오디션/감정 이입 과정을 구체적으로 묘사\n"
            "- 성장: 연기력 향상/인지도 변화/업계 반응을 섬세하게 서술"
        ),
    },
    "스포츠": {
        "label": "스포츠 웹소설",
        "tips": (
            "- 경기: 기술 시전/신체 역학/경기 흐름을 구체적으로 묘사\n"
            "- 성장: 피지컬 한계 돌파/전술 각성/멘탈 변화를 섬세하게 서술"
        ),
    },
    "의학": {
        "label": "의학 웹소설",
        "tips": (
            "- 진료: 의학 용어/시술 과정/환자 상태를 구체적으로 묘사\n"
            "- 성장: 진단 능력 향상/의료 윤리 갈등/전문성 확대를 섬세하게 서술"
        ),
    },
    "요리": {
        "label": "요리 웹소설",
        "tips": (
            "- 요리: 식재료/조리 과정/맛과 향의 변화를 구체적으로 묘사\n"
            "- 성장: 미각 감각 확장/레시피 창작/요리 철학 변화를 섬세하게 서술"
        ),
    },
}

DEFAULT_GENRE = {
    "label": "웹소설",
    "tips": ("- 장르 핵심 장면을 구체적이고 감각적으로 묘사\n- 성장/변화 순간을 섬세하게 서술"),
}


def _get_genre_preset(genre: str) -> dict:
    """장르명으로 프리셋 조회. 없으면 기본값."""
    return GENRE_PRESETS.get(genre, DEFAULT_GENRE)


class PromptBuilder:
    """프롬프트 조립기 - 컨텍스트 파일 + 인스트럭션 쌍 생성"""

    # ═══════════════════════════════════════════════════════
    # Stage 2: 분배표 (블록 → 화별 분배)
    # ═══════════════════════════════════════════════════════

    @staticmethod
    def build_arc_context(bible: str, block: str, prev_arc: str = "", state_summary: str = "") -> str:
        """업로드할 컨텍스트 파일 [LITE-V1] state_summary 주입"""
        parts = []
        if bible:
            parts.append(f"{SEP}\n[세계관 설정 (Bible)]\n{SEP}\n{bible}")
        if state_summary:
            parts.append(f"{SEP}\n[현재 세계 상태 — 반드시 참고]\n{SEP}\n{state_summary}")
        parts.append(f"{SEP}\n[이번 Arc 줄거리 블록]\n{SEP}\n{block}")
        if prev_arc:
            parts.append(f"{SEP}\n[최근 Arc 분배표 (최대 10개)]\n{SEP}\n{prev_arc}")
        return "\n\n".join(parts)

    @staticmethod
    def build_arc_instruction(arc_no: int, ep_start: int, ep_count: int, dead_npc_warning: str = "") -> str:
        """채팅에 입력할 인스트럭션 [LITE-V1] dead_npc_warning 주입"""
        ep_end = ep_start + ep_count - 1
        base = f"""{HEADER}

첨부 파일은 웹소설의 세계관과 Arc #{arc_no} 줄거리 블록입니다.

[작업] 이 블록을 {ep_count}화로 분배하세요.
- 대상: 제{ep_start}화 ~ 제{ep_end}화
- 블록의 모든 사건/갈등/성장을 {ep_count}화에 균등 배분
- [성장/경지] 섹션이 있으면 → 해당 성장이 일어나는 화를 특정하여 배치
- 각 화가 독립적 사건 + 클리프행어로 끝날 것
- 직전 Arc 분배표(있으면)의 마지막 화에서 이어질 것

[출력 형식 - 반드시 준수]

# Arc #{arc_no} 분배표 (제{ep_start}화~제{ep_end}화)

## 제{ep_start}화: (제목)
- 핵심 사건: (이 화에서 벌어지는 일 2~3줄)
- 등장인물: (이 화의 주요 인물)
- 성장/변화: (이 화에서 성장이 있으면 기재, 없으면 '유지')
- 클리프행어: (이 화 끝의 긴장 포인트)

## 제{ep_start + 1}화: (제목)
...

(제{ep_end}화까지 빠짐없이)

## Arc 종료 상태
- 주인공 능력/레벨
- 주인공 상태/위치
- 주요 변화
- 다음 Arc 연결점"""

        if dead_npc_warning:
            base += f"\n\n{dead_npc_warning}"

        return base

    # ═══════════════════════════════════════════════════════
    # Stage 3: Blueprint (분배표 + 원본 블록 → 씬 설계)
    # ═══════════════════════════════════════════════════════

    @staticmethod
    def build_blueprint_context(
        bible: str,
        arc: str,
        block: str,
        prev_bp: str = "",
        state_summary: str = "",
    ) -> str:
        """bible + 분배표 + 원본 블록 + 직전 Blueprint + 세계 상태 [LITE-V1]"""
        parts = []
        if bible:
            parts.append(f"{SEP}\n[세계관 설정 (Bible)]\n{SEP}\n{bible}")
        if state_summary:
            parts.append(f"{SEP}\n[현재 세계 상태 — 반드시 참고]\n{SEP}\n{state_summary}")
        parts.append(f"{SEP}\n[화별 분배표]\n{SEP}\n{arc}")
        parts.append(f"{SEP}\n[원본 줄거리 블록 (상세 맥락 참고용)]\n{SEP}\n{block}")
        if prev_bp:
            parts.append(f"{SEP}\n[최근 Blueprint (최대 10화)]\n{SEP}\n{prev_bp}")
        return "\n\n".join(parts)

    @staticmethod
    def build_blueprint_instruction(ep_num: int, dead_npc_warning: str = "") -> str:
        """[LITE-V1] dead_npc_warning 주입"""
        base = f"""{HEADER}

첨부 파일에 세계관, 화별 분배표, 원본 줄거리 블록이 있습니다.

[작업] 제{ep_num}화 에피소드 Blueprint 작성
- 분배표에서 제{ep_num}화에 배정된 사건을 중심으로 씬 설계
- 원본 블록의 전투/전략/성장 묘사를 적극 활용하여 씬 디테일 보강
- Bible의 캐릭터명/고유명사를 정확히 사용
- 성장/돌파가 있는 화면 → 해당 과정을 별도 씬으로 설계
- 씬별 상세 설계 (최소 3개 씬)
- 각 씬: 위치, 등장인물, 핵심 사건, 대사 포인트, 분위기

[출력 형식 - 반드시 준수]

# 제{ep_num}화 Blueprint

제목: (에피소드 제목)

## 씬 1: (위치/상황)
- 등장인물:
- 핵심 사건:
(상세 씬 설계 - 300자 이상)

## 씬 2: (위치/상황)
...

## 엔딩 훅
(다음 화로 이어지는 긴장감 있는 마무리)

## 종료 상태
- 주인공 능력/상태
- 주요 변화"""

        if dead_npc_warning:
            base += f"\n\n{dead_npc_warning}"

        return base

    # ═══════════════════════════════════════════════════════
    # Stage 4: Manuscript (원고)
    # ═══════════════════════════════════════════════════════

    @staticmethod
    def build_manuscript_context(
        bible: str,
        blueprint: str,
        prev_ms: str = "",
        style: str = "",
        state_summary: str = "",
        chain_link: str = "",
    ) -> str:
        """[LITE-V1] state_summary + chain_link 주입"""
        parts = []
        if bible:
            parts.append(f"{SEP}\n[세계관 설정 (Bible)]\n{SEP}\n{bible}")
        if state_summary:
            parts.append(f"{SEP}\n[현재 세계 상태 — 반드시 참고]\n{SEP}\n{state_summary}")
        if chain_link:
            parts.append(f"{SEP}\n{chain_link}")
        parts.append(f"{SEP}\n[에피소드 Blueprint]\n{SEP}\n{blueprint}")
        if prev_ms:
            parts.append(f"{SEP}\n[최근 원고 (최대 10화)]\n{SEP}\n{prev_ms}")
        if style:
            parts.append(f"{SEP}\n[문체 가이드]\n{SEP}\n{style}")
        return "\n\n".join(parts)

    @staticmethod
    def build_manuscript_instruction(ep_num: int, genre: str = "", dead_npc_warning: str = "") -> str:
        """[LITE-V1] dead_npc_warning 주입"""
        preset = _get_genre_preset(genre)
        genre_label = preset["label"]
        genre_tips = preset["tips"]

        base = f"""{HEADER}

첨부 파일은 제{ep_num}화의 세계관, Blueprint, 참고 자료입니다.

[작업] 제{ep_num}화 웹소설 원고 집필
- 장르: {genre_label} (문피아 20~30대 독자)
- 분량: 공백 포함 최소 8,000자 이상

[필수 제약]
1. 맨 윗줄에 '제 {ep_num}화' 표기 후 시작
2. 사족(인사말/설명) 없이 소설 본문만 출력
3. 불필요한 HTML 요소나 진한 글자(**) 사용 금지
4. 마지막에 '* * *' 종료 표시
5. 3인칭 시점
6. Blueprint의 모든 씬을 균등 비중으로 전개
7. 후반부 급전개/요약 절대 금지
8. 직전 화 마지막 장면에서 자연스럽게 이어질 것
9. Bible의 캐릭터명/고유명사를 정확히 사용
10. 장면 전환은 반드시 '%%%%'로만 표시 (다른 구분자 금지)
11. '한글(영어)' 병기 표기 절대 금지 (예: 기(Qi), 검(Sword) 등)
12. 한자 병기도 금지 (예: 천하제일(天下第一) 등)

[문체 원칙]
- 감정어 삭제 → 행동/미세표정으로 감정 유추
- 감각적 묘사 (소리/냄새/질감) 활용
- 날 선 대화가 오가는 실제 장면으로 풀어쓰기
- 동사(Action) 위주 짧고 힘 있는 문장
{genre_tips}"""

        if dead_npc_warning:
            base += f"\n\n{dead_npc_warning}"

        return base
