"""[V64.P4] ChiefWriter 프롬프트 템플릿 외부화.

[S-01] YAML이 SSOT — Python 인라인 상수 제거, PromptLoader에서만 로드.
폴백 문자열은 최소한만 유지 (YAML 로드 실패 시에만 사용).
"""

from modules.core.prompt_loader import PromptLoader

_PROMPT_LOADER = PromptLoader()

# [S-01] 인라인 상수 제거 — YAML이 SSOT (config/prompts/chief_writer.yaml)
_FALLBACK_EMPTY = ""


def _load_prompt(key: str, fallback: str) -> str:
    loaded = _PROMPT_LOADER.load("chief_writer", key)
    return loaded if loaded is not None else fallback


def get_prompt_template_output() -> str:
    return _load_prompt("PROMPT_TEMPLATE_OUTPUT", _FALLBACK_EMPTY)


def get_common_rules_section() -> str:
    return _load_prompt("COMMON_RULES_SECTION", _FALLBACK_EMPTY)


def get_writing_guidelines_section() -> str:
    return _load_prompt("WRITING_GUIDELINES_SECTION", _FALLBACK_EMPTY)


def get_writing_guidelines_investment_only() -> str:
    """[투자물 전용] 수치 집필 규칙 — investment 장르에서만 주입."""
    return _load_prompt("WRITING_GUIDELINES_INVESTMENT_ONLY", _FALLBACK_EMPTY)


def get_primitive_constraint_fallback() -> str:
    return _load_prompt("PRIMITIVE_CONSTRAINT_FALLBACK", _FALLBACK_EMPTY)


def get_modern_origin_section() -> str:
    return _load_prompt("MODERN_ORIGIN_SECTION", _FALLBACK_EMPTY)


def get_satisfaction_guide_section() -> str:
    """[D-Step2] 독자 대리만족 필수 요소 가이드 — CW 초안 단계 사전 주입."""
    return _load_prompt("SATISFACTION_GUIDE_SECTION", _FALLBACK_EMPTY)


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
    reference_excerpt_section: str = "",
    prev_manuscripts_section: str = "",  # [V67] 이전 원고 전문
    incarnation_context_section: str = "",  # [V67.1] 환생 유형별 집필 맥락
    chain_link_section: str = "",  # [V68] 직전 화 연결고리
    ending_hook_section: str = "",  # [ending_hook] 현재 화 마무리 훅
    emotional_beat_section: str = "",  # [emotional_beat] 감정 정점
    satisfaction_guide_section: str = "",  # [D-Step2] 독자 대리만족 사전 주입
    opening_anchor_section: str = "",  # [TF-2] 시작 장소/시간 불변 계약
    immutable_fact_section: str = "",  # [IFC] 불변 사실 계약 패킷
    integrated_scenario_advisory_section: str = "",  # [S4] advisory-only long-form blueprint prose
    carryover_ceiling_section: str = "",  # [S4] prior/current authority ceiling
    writer_hard_canon_section: str = "",
    writer_soft_guidance_section: str = "",
) -> str:
    """[V65] _build_common_context() 메인 프롬프트 템플릿.

    호출부에서 self._escape_braces() 처리 완료된 값을 전달받는다.
    [V67] prev_manuscripts_section: 이전 30화 원고 전문 (모순 방지용 컨텍스트)
    [V68] chain_link_section: 직전 화 연결고리 (다음 화에서 반드시 이어받아야 할 것)
    """
    _split_writer_sections = bool(writer_hard_canon_section or writer_soft_guidance_section)
    _legacy_writer_core_section = "" if _split_writer_sections else writer_core_section
    return f"""
[Role] 웹소설 1타 작가 (Chief Writer)
[Task] 제{ep_num}화 원고를 Blueprint 기반으로 집필하라.

### Writer Identity Contract
- 너는 분석가, 요약가, 브리핑 엔진, 상태 보고자, 회차 리캡 작성자가 아니다.
- 보고서, 대시보드, 시스템 로그처럼 설명하지 말고 장면 내부의 행동과 감각으로 보여줘라.
- HUD/상태창/시스템 메시지/메타 해설은 canon에 이미 존재할 때만 작중 요소로 제한적으로 사용하라.
- 독자에게 사건을 설명하지 말고, 등장인물의 시점 안에서 서사로 전개하라.

### 핵심 철학
"Blueprint를 토대로 양질의 원고를 연속성 있게 생산한다"

### [V67] 모순 절대 금지
이전 원고에서 확립된 사실(고유명사, 수치, 상태)을 반드시 준수하세요.
변경이 필요한 경우 작중에서 명확한 이유를 설명해야 합니다.

{immutable_fact_section}

### [STEP 0: Read This Authority First]
1. Opening Anchor + Immutable Facts + world-state / mandatory truth + chain_link + prior manuscript full-text + prev digest + carryover ceiling
2. Structured scene breakdown
3. Advisory integrated scenario prose
4. Feedback, constraints, HUD-heavy cues, and style guidance must not override already-established truth

### [STEP 0.5: 권위 우선순위]
아래 우선순위를 반드시 지켜라. 하위 블록이 상위 권위와 충돌하면 하위를 버린다.
1. Opening Anchor
2. Immutable Facts / world-state / mandatory truth / chain_link / prior manuscript full-text / prev digest / carryover ceiling
3. Structured scene breakdown
4. Advisory integrated scenario prose
5. Feedback / constraints / HUD-heavy cues / style guidance

{opening_anchor_section}

{writer_hard_canon_section}

{incarnation_context_section}

{chain_link_section}

{world_origin_constraint_section}

{future_guard_section}

{past_guard_section}

{prev_digest}

{carryover_ceiling_section}

{prev_manuscripts_section}

### [STEP 0.75: Writer Guidance]
{ending_hook_section}

{dna_instruction}

{purism_section}

{feedback_section}
{constraint_section}

{writer_soft_guidance_section}

{_legacy_writer_core_section}

{hud_anomaly_section}

### [STEP 1: Blueprint 분석]
아래 Blueprint의 structured scene contract를 먼저 파악하고, 각 scene anchor의 핵심 의무를 실제 장면으로 구현하라.

⚠️ 필수: scene anchor는 내부 기획 좌표다. 독자-facing 원고 본문에는 scene id, 제목, Markdown 헤더, 구조 라벨을 쓰지 마라.
   anchor별 분량은 균등 분배하지 말고 장면 밀도와 긴장에 맞춰 가변 배분하라.
   장면 전환이 필요하면 산문 전환문이나 `* * *` 같은 중립 전환 마커만 사용하라.
   후반부 anchor도 요약하지 말고, Blueprint의 핵심 의무가 독자 눈앞에서 보이게 써라.

{scene_breakdown}

{integrated_scenario_advisory_section}

{emotional_beat_section}

### [STEP 2: 연속성 확인]

직전 화 엔딩에서 자연스럽게 이어져야 한다. 위 다이제스트의 상태를 반드시 준수하라.
단, 위 Opening Anchor가 있으면 Blueprint의 시작 장소/시간이 직전 화 종료 상태보다 우선한다.

⛔ [V69.1] 중복 서술 금지: 직전 화의 마지막 장면을 다시 서술하지 마라.
   직전 화가 끝난 바로 그 다음 순간부터 시작하라.
   직전 화에서 이미 끝난 대화·행동·이동을 반복하지 마라.
   새 장소·새 행동·시간 점프가 필요하면 전환 문장 또는 장면 전환 마커 `* * *`를 먼저 써라.
   단, `* * *`만 두고 끝내지 말고 직후 1~2문장 안에 무엇이 바뀌었는지 명시하라.
   전환 신호 없이 새 방, 차량 내부, 외부 이동 경로, 더 늦은 시간대로 바로 점프하지 마라.

[직전 화 마지막 장면 — 이 장면 이후부터 시작할 것]
...{prev_ending}

### [STEP 3: 현재 상태 반영]
{hud_report}

{high_density_hud_section}

{hud_trend_section}

필수 준수:
- 현재 경지/내공 범위 내에서만 무공 사용
- 부상 상태는 전투/행동에 반영
- 소지품/자금 상태 일관성 유지

{npc_equipment_section}

{npc_frequency_section}

### [STEP 4: Arc 전술 참조]
{arc_doc}

### [STEP 5: 세계관 설정]
- 주인공 동기: {core_identity_desire}

### [STEP 6: 문체 DNA 가이드 - 위반 시 AI티 판정]
{style_guide}

{reference_excerpt_section}

{satisfaction_guide_section}

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
수정된 JSON 원고만 출력하라. 설명 없이 단일 JSON 객체({{ }}) 하나만. 배열([...])로 감싸지 마라.
"""


def get_expand_length_prompt(
    *,
    current_length: int,
    target_length: int,
    manuscript_escaped: str,
    hud_report_escaped: str,
) -> str:
    """[TF-H] 분량 확장 전용 프롬프트."""
    _deficit = target_length - current_length
    return f"""
[Role] 웹소설 원고 확장 전문가
[Task] 아래 원고를 {target_length}자 이상으로 확장하라. 현재 {current_length}자 (부족분: {_deficit}자).

### 확장 규칙
1. 기존 내용을 절대 삭제하지 마라.
2. 각 씬에 대화를 최소 2개 추가하라 (인물 성격이 드러나는 대화).
3. 주인공의 내면 심리 묘사를 각 씬당 200자 이상 추가하라.
4. 배경/공간 묘사를 구체화하라 (오감: 시각, 청각, 촉각, 후각).
5. 액션이나 긴장 장면이 있다면 슬로우모션 기법으로 늘려라.
6. 반드시 {target_length}자 이상 출력하라. 부족하면 장면 전환 추가.

### 현재 HUD 상태 (참고)
{hud_report_escaped}

### 확장 대상 원고
{manuscript_escaped}

### 출력 형식
확장된 JSON 원고만 출력하라. 설명 없이 단일 JSON 객체({{ }}) 하나만. 배열([...])로 감싸지 마라.
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

6. "AI 티 문장" 금지
   - X "어느새", "말 그대로", "그야말로", "숨을 삼켰다", "시선을 돌렸다" 같은 상투구를 짧은 간격으로 반복
   - X 장면 말미를 설명문으로 기계적으로 요약하거나 같은 리듬으로 닫기
   - O 감정은 행동/대사/구체 감각으로 드러내고, 문장 스타터와 장면 시작·종결 리듬을 계속 바꿔라

[당신이 쓰려는 문장이 위 클리셰에 해당하는가? YES -> 다시 쓰십시오]
"""
