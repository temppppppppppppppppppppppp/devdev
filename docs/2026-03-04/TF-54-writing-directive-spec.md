# TF-54: WritingDirective 구현 명세

> **상태**: 미구현 (문서화 완료)
> **작성일**: 2026-03-04
> **산출물**: PatternTracker + WritingDirectiveGenerator + CW/Director 정합성 배선
> **예상 변경**: ~500줄 신규, ~120줄 수정, ~25개 테스트

---

## 1. 문제 분석

### 1.1 25화 원고 전수 분석 결과 (투자물 장르, 프로젝트 000000)

| 패턴 | 발견 | 심각도 |
|------|------|--------|
| **표현 반복** | "사무실 공기가 얼어붙었다" 14회/25화, "얼음처럼 차가운 미소" 8회, "동공이 흔들렸다" 7회 | HIGH |
| **엔딩 고착** | 25/25화 전부 "거창한 선언문" 엔딩. 조용한 여운 0건 | HIGH |
| **감정 빈곤** | 주인공 감정 2색만: "차가운 만족" + "차가운 분노". 유머 0건 | HIGH |
| **NPC 반응 고정** | 박성호: "경악→말더듬→복종" 25회 연속 고정 | MEDIUM |
| **은유 편중** | 군사/사냥 은유 50+회. 다른 영역 거의 부재 | MEDIUM |

### 1.2 근본 원인

```
현재: Blueprint(WHAT만) → CW(매화 동일한 8개 정적 규칙) → Director(문체 피드백 금지 TF-35c)
     ↑ 서로 다른 방향을 보고 있음

목표: Blueprint(WHAT+HOW) → CW(에피소드별 동적 지시) → Director(지시 준수 확인)
     ↑ 같은 방향을 보면 통과율 UP + 품질 UP
```

- **Blueprint**: "무엇이 일어나는가"만 설계. "어떻게 쓸 것인가"는 없음
- **CW**: 매화 동일한 8개 정적 COMMON_RULES로 집필
- **Director**: TF-35c로 문체 피드백 금지 → 반복 문체 교정 불가
- **3개 스테이지가 "어떻게 쓸 것인가"를 공유하지 않아 정합성 부재**

---

## 2. 아키텍처 설계

### 2.1 WritingDirective 레이어

```
┌─────────────────────────────────────────────────────┐
│  PatternTracker (Python, LLM 0회)                    │
│  직전 N화 원고에서 패턴 집계:                          │
│  - 표현 빈도 (사무실 공기, 동공 흔들림 등)              │
│  - 엔딩 패턴 (선언문 4연속 등)                         │
│  - NPC 반응 패턴 (박성호: 경악→복종 5연속)              │
│  - 은유 카테고리 (군사 80%, 기타 20%)                   │
│  - 감정 다양성 지수                                    │
└────────────────┬────────────────────────────────────┘
                 │ 패턴 요약 텍스트
                 ▼
┌─────────────────────────────────────────────────────┐
│  WritingDirectiveGenerator (LLM 1회, Stage4 단계)     │
│  패턴 요약 + 현재 Blueprint → 에피소드별 집필 지시 생성  │
│                                                       │
│  출력 예시:                                            │
│  {                                                    │
│    "ending_style": "조용한 여운 (선언문 4연속이므로)",    │
│    "metaphor_avoid": ["전쟁","사냥","총알","참호"],      │
│    "metaphor_suggest": ["요리/조리","건축","바둑"],      │
│    "emotion_required": "주인공 약점 노출 1건",          │
│    "npc_directives": {"박성호": "유능한 모습 1건, 말더듬 금지"},│
│    "intensity_note": "일상 행동은 담담하게",             │
│    "expression_ban": ["사무실 공기","동공이 흔들"]       │
│  }                                                    │
└────────────────┬────────────────────────────────────┘
                 │ writing_directives JSON
                 ▼
        ┌────────┴────────┐
        ▼                 ▼
  ┌──────────┐     ┌──────────┐
  │ CW 컨텍스트│     │ Director │
  │ 주입      │     │ 채점 기준│
  └──────────┘     └──────────┘
```

### 2.2 핵심 원칙

- **단일 LLM 호출**: PatternTracker(Python 집계) → WritingDirectiveGenerator(LLM 1회)로 패턴 분석 + 지시 생성 통합
- **CW-Director 정합성**: 동일한 WritingDirective를 CW 컨텍스트와 Director mandatory_context에 주입. 같은 기준으로 집필/평가
- **TF-35c 부분 해제**: "스타일 개선 요구" 금지 유지, 단 "사전 합의된 계약 위반 지적"은 허용

### 2.3 LLM 통합 방식

PatternTracker + DirectiveGenerator를 **단일 LLM 호출**로 통합:
- Python이 직전 N화 원고를 DB에서 로드 + 기본 포맷팅
- LLM이 원고 텍스트 + Blueprint를 받아 패턴 분석과 지시를 한번에 출력
- Python 사전 집계(regex 기반 표현 빈도, 엔딩 분류)는 유지 — LLM에 요약 텍스트로 전달

**비용**: Gemini Flash 1회/에피소드 (~1K input, ~300 output) ≈ $0.001

---

## 3. TF 구현 명세 (54a~54e)

### 3.1 TF-54a: PatternTracker — Python 패턴 집계기

**신규 파일**: `modules/core/pattern_tracker.py` (~200줄)

**입력**: DB에서 직전 N화 원고 텍스트 로드 (기본 N=5, `validation.yaml` 설정)

**출력**: `PatternReport` dataclass

```python
@dataclass
class PatternReport:
    expression_freq: dict[str, int]     # {"사무실의 공기": 7, "동공이 흔들": 5, ...}
    ending_patterns: list[str]          # ["선언문", "선언문", "선언문", "수사의문문"]
    npc_reaction_patterns: dict[str, list[str]]  # {"박성호": ["경악→복종","경악→복종",...]}
    metaphor_categories: dict[str, int] # {"군사": 15, "자연": 2, "음식": 0}
    emotion_diversity: float            # unique_emotions / total_emotions (0~1)
    protagonist_emotions: list[str]     # ["차가운 만족","차가운 분노","차가운 만족",...]
```

**핵심 메서드**:
- `build_report(db, ep_num, lookback=5) -> PatternReport` — regex + 키워드 매칭
- `to_summary_text() -> str` — LLM 주입용 요약 텍스트 (~500자)

**추적 대상 표현 목록** (장르 무관 + 투자물 특화):

```python
TRACKED_EXPRESSIONS = [
    "사무실의 공기", "동공이 흔들", "입꼬리를 비틀", "폐부 깊숙이",
    "단순한 .{1,15}(아니다|아니었다)", "거의 비명에 가까운",
    "강철 같은", "얼음처럼 차가운", "모든 것은 시나리오대로",
    "눈에 불꽃이 타올", "얼굴이 하얗게 질", "사냥감|맹수|포식자",
    "제국의 (왕|지휘석|기둥|영토)", "나는 알고 있었다",
    "그때였다", "텅 빈 사무실",
]

METAPHOR_CATEGORIES = {
    "군사": ["전쟁", "총알", "참호", "사령관", "전함", "함교", "무기", "탄창"],
    "사냥": ["사냥감", "맹수", "포식자", "먹잇감", "조준경", "미끼"],
    "제국": ["제국", "왕", "왕국", "기사", "신하", "왕좌"],
    "자연": ["바람", "파도", "폭풍", "태양", "달빛", "강물"],
    "음식": ["요리", "맛", "조리", "재료", "양념"],
    "건축": ["기둥", "주춧돌", "벽돌", "설계", "건물"],
    "게임": ["바둑", "장기", "체스", "카드", "판"],
}

ENDING_CLASSIFIERS = {
    "선언문": ["시작이었다", "서막이 올랐다", "전쟁이 시작", "사냥이 시작"],
    "수사의문문": ["것인가?", "것일까?", "될 것인가?"],
    "차가운미소": ["미소가 걸렸다", "미소를 지었다", "입꼬리를"],
    "조용한여운": [],  # fallback when unclassified
}
```

**추가 산출물**:
- `WritingDirective` dataclass → `modules/core/stage4_types.py` (~20줄)
- 설정 → `config/settings/validation.yaml` (~10줄)

**비용**: LLM 0회. 순수 Python. 테스트 용이.

---

### 3.2 TF-54b: WritingDirectiveGenerator — LLM 기반 지시 생성

**신규 파일**: `modules/core/writing_directive_generator.py` (~250줄)

**타이밍**: Blueprint 생성 후, CW 호출 전 (Stage4 Interview Round)

**호출 지점**: `stage4_interview_round.py`의 `run()` 메서드, Blueprint 로드 후

```python
class WritingDirectiveGenerator:
    def generate(
        self,
        pattern_report: PatternReport,
        blueprint: dict,
        genre: str,
        ep_num: int,
        llm_callback: Callable,
    ) -> WritingDirective:
        """패턴 리포트 + 블루프린트로 에피소드별 집필 지시 생성."""
```

**프롬프트** (외부화 YAML: `config/prompts/writing_directive.yaml`):

```yaml
system: |
  당신은 웹소설 집필 감독입니다.

  [직전 {N}화 패턴 분석 결과]
  {pattern_summary}

  [이번 화 블루프린트 요약]
  {integrated_scenario}

  위 패턴을 참고하여, 이번 화의 집필 지시를 생성하세요.
  목표: 직전 화들과 겹치지 않는 신선한 표현·구조·감정을 유도.

  출력 (JSON):
  {
    "ending_style": "이번 화의 마무리 방식 (선언문/수사의문/조용한여운/일상적마무리 중 택1, 사유 포함)",
    "metaphor_avoid": ["이번 화에서 피해야 할 은유 키워드 (최근 과사용)"],
    "metaphor_suggest": ["대안 은유 영역 (최근 미사용)"],
    "emotion_required": "주인공에게 요구하는 감정 (최근 부족한 감정)",
    "npc_directives": {"NPC명": "이번 화에서의 행동 지시"},
    "intensity_note": "이번 화의 전반적 강도 가이드",
    "expression_ban": ["이번 화에서 금지할 표현 (최근 3회+ 사용)"]
  }
```

**비용**: Gemini Flash 1회 (~1K input, ~300 output) ≈ $0.001/에피소드

---

### 3.3 TF-54c: CW 프롬프트 정합성 — 지시 주입 + 규칙 확장

**수정 파일**:
- `modules/domain/agents/chief_writer_context.py` — `build_common_context()`에 `writing_directive` 파라미터 추가
- `config/prompts/chief_writer.yaml` — COMMON_RULES 9~11번 추가
- `modules/core/stage4_interview_round.py` — WritingDirective 생성 + CW 컨텍스트 주입

**CW 컨텍스트 주입 코드**:

```python
# chief_writer_context.py — build_common_context() 내부
if writing_directive:
    directive_section = f"""
### 이번 화 집필 지시 (WritingDirective)
**반드시 준수하세요. Director가 이 지시의 준수 여부를 평가합니다.**

- 마무리 방식: {writing_directive.ending_style}
- 금지 표현: {', '.join(writing_directive.expression_ban)}
- 피할 은유: {', '.join(writing_directive.metaphor_avoid)}
- 추천 은유: {', '.join(writing_directive.metaphor_suggest)}
- 감정 요구: {writing_directive.emotion_required}
- NPC 지시: {writing_directive.npc_directives}
- 강도 가이드: {writing_directive.intensity_note}
"""
```

**신규 COMMON_RULES** (chief_writer.yaml):

```yaml
9. [TF-54] 은유 다양성: 직전 3화에서 사용한 은유 영역을 반복하지 마라.
   WritingDirective의 metaphor_avoid/suggest를 따라라.
10. [TF-54] 강도 조절: 일상 행동(계약, 이동, 식사)은 담담하게 서술하라.
    모든 장면을 극적으로 묘사하면 진짜 클라이맥스의 임팩트가 죽는다.
11. [TF-54] NPC 음성 분화: 각 NPC는 고유한 말투·어휘·문장 길이를 가져야 한다.
    모든 NPC가 "대, 대표님!" 패턴으로 말더듬하면 안 된다.
```

**Blueprint 프롬프트 변경** (ensemble.yaml):

```yaml
# 기존: "마지막 씬은 반드시 긴장 또는 궁금증으로 끝낼 것 (클리프행어)"
# 변경: "마지막 씬의 마무리 방식은 WritingDirective의 ending_style을 따를 것.
#        클리프행어만 반복하면 독자가 피로해진다. 3화 중 1화는 조용한 여운으로."
```

---

### 3.4 TF-54d: Director 정합성 — 지시 평가 + TF-35c 부분 해제

**수정 파일**:
- `config/prompts/director.yaml` — TF-35c 부분 해제 + WritingDirective 평가 가이드
- `modules/domain/agents/director_ensemble.py` — mandatory_context에 directive 추가
- `modules/core/stage4_interview_round.py` — Director에 directive 전달

**TF-35c 변경**:

```yaml
# 기존:
# "절대 포함하지 말 것: 분량 확장, 대화 비율 조정, 문체 개선, 묘사 추가 등 양적/스타일 지시."

# 변경:
# "절대 포함하지 말 것: 분량 확장, 대화 비율 조정, 묘사 추가 등 양적 지시.
#  단, WritingDirective 위반 사항은 feedback에 포함할 것:
#  - 금지 표현 사용 ('사무실 공기' 금지인데 2회 사용)
#  - ending_style 미준수 ('조용한 여운' 지시인데 선언문으로 종결)
#  - 감정 요구 미충족 ('주인공 약점 노출' 요구인데 차가운 만족만)
#  이것은 스타일 '개선' 요구가 아니라 사전 합의된 '계약' 위반 지적이다."
```

**Director 채점**: 기존 `quality_engagement` (20점) 내에서 평가. 신규 채점 항목 불추가 — 채점 구조 변경 최소화. Director 프롬프트에 추가: "quality_engagement 평가 시 WritingDirective 준수 여부를 고려하라."

**mandatory_context 주입**: Director가 CW와 **동일한** WritingDirective 텍스트를 `_director_mc_parts`로 수신. CW-Director 정합성 보장.

---

### 3.5 TF-54e: CW Self-Critique 확장 — 지시 준수 자가 점검

**수정 파일**: `modules/domain/agents/chief_writer_quality.py`

**신규 체크 2건** (기존 5건 → 7건):

```python
# 6번째 체크: WritingDirective 준수
def _check_writing_directive(self, manuscript: str, directive: WritingDirective) -> list:
    """금지 표현 사용, ending_style 미준수 등 감지."""
    issues = []
    for expr in directive.expression_ban:
        if expr in manuscript:
            issues.append(f"금지 표현 '{expr}' 사용됨")
    # ending style 체크 (마지막 3문장 분석)
    # metaphor category 체크 (avoid 목록 매칭)
    return issues

# 7번째 체크: 표현 신선도
def _check_expression_freshness(self, manuscript: str, recent_manuscripts: list[str]) -> list:
    """직전 5화 대비 3회+ 반복 표현 감지."""
    # TRACKED_EXPRESSIONS regex 매칭
    # 직전 N화에서 이미 사용된 표현이면 플래그
    return issues
```

기존 `_self_critique()` 메서드의 체크 리스트에 통합, severity 점수에 반영.

---

## 4. 수정 파일 목록 및 주입 지점

### 4.1 신규 파일

| 파일 | TF | 줄 수 | 역할 |
|------|-----|-------|------|
| `modules/core/pattern_tracker.py` | 54a | ~200 | Python 패턴 집계기 |
| `modules/core/writing_directive_generator.py` | 54b | ~250 | LLM 기반 지시 생성기 |
| `config/prompts/writing_directive.yaml` | 54b | ~50 | 지시 생성 프롬프트 |
| `tests/test_pattern_tracker.py` | 54a | ~15개 | PatternTracker 단위 테스트 |
| `tests/test_writing_directive.py` | 54b,e | ~10개 | 지시 생성 + self-critique 통합 테스트 |

### 4.2 수정 파일

| 파일 | TF | 변경 | 주입 지점 |
|------|-----|------|----------|
| `modules/core/stage4_types.py` | 54a | `WritingDirective` dataclass 추가 (~20줄) | 파일 말미 |
| `config/settings/validation.yaml` | 54a | pattern_tracker 설정 (~10줄) | 파일 말미 |
| `modules/domain/agents/chief_writer_context.py` | 54c | `writing_directive` 파라미터 + 섹션 주입 (~25줄) | `build_common_context()` (L43) |
| `config/prompts/chief_writer.yaml` | 54c | COMMON_RULES 9~11번 추가 (~15줄) | COMMON_RULES 섹션 |
| `config/prompts/ensemble.yaml` | 54c | 클리프행어 필수 규칙 완화 (~5줄) | 마지막 씬 규칙 |
| `modules/core/stage4_interview_round.py` | 54c,d | PatternTracker 호출 + Directive 생성 + CW/Director 주입 (~40줄) | `run()` 메서드, Blueprint 로드 후 |
| `config/prompts/director.yaml` | 54d | TF-35c 부분 해제 + 평가 가이드 (~20줄) | TF-35c 규칙 섹션 |
| `modules/domain/agents/director_ensemble.py` | 54d | mandatory_context에 directive 추가 (~10줄) | `_director_mc_parts` 구성부 |
| `modules/domain/agents/chief_writer_quality.py` | 54e | `_check_writing_directive()` + `_check_expression_freshness()` (~80줄) | `_self_critique()` 메서드 |

### 4.3 상세 주입 지점

| 파일 | 라인 범위 | 함수 | 주입 유형 |
|------|----------|------|----------|
| `chief_writer_context.py` | L43~85 | `build_common_context()` | 파라미터 추가 + 섹션 삽입 |
| `chief_writer_context.py` | L103~115 | Blueprint 추출 | scene_breakdown 조립부 수정 |
| `stage4_context_builder.py` | L465~700 | `prepare_episode_context()` | 반환 dict에 custom_sections 추가 |
| `stage4_context_builder.py` | L703~900+ | `build_mandatory_context()` | `_mc_parts`에 directive prepend |
| `stage4_interview_round.py` | `run()` 내부 | Blueprint 로드 직후 | PatternTracker + Generator 호출 |

---

## 5. 구현 순서 및 의존성

```
TF-54a (PatternTracker)        ← 독립, 의존성 없음
    │
TF-54b (DirectiveGenerator)    ← 54a 필요
    │
    ├── TF-54c (CW 주입 + 규칙)  ← 54b 필요
    │
    ├── TF-54d (Director 정합성)  ← 54c와 병렬 가능
    │
    └── TF-54e (self-critique)   ← 54c 필요

순서: 54a → 54b → 54c+54d 병렬 → 54e
```

---

## 6. 기대 효과

| 지표 | 현재 | TF-54 후 예상 |
|------|------|--------------|
| 표현 반복 | 14회/5화 ("사무실 공기") | 0~1회/5화 (expression_ban) |
| 엔딩 다양성 | 100% 선언문 | ~33% 조용한 여운 (ending_style) |
| 은유 다양성 | 군사/사냥 80%+ | 40% 미만 (metaphor_avoid/suggest) |
| NPC 반응 다양성 | 경악→복종 고정 | 행동 변형 (npc_directives) |
| 1차 통과율 | (미측정) | 15~25% 향상 (CW-Director 정합성) |
| 추가 LLM 비용 | 0 | Flash 1회/에피소드 (~$0.001) |

---

## 7. 검증 계획

### 7.1 단위 테스트

```bash
pytest tests/test_pattern_tracker.py -v    # 표현 감지, 엔딩 분류, 은유 카테고리, NPC 반응 패턴
pytest tests/test_writing_directive.py -v   # 지시 생성, self-critique 통합
```

### 7.2 통합 검증

```bash
python -m py_compile modules/core/pattern_tracker.py
python -m py_compile modules/core/writing_directive_generator.py
ruff check modules/ config/ tests/
pytest tests/ -q   # 전체 회귀 (기존 3,170 + ~25 신규 ≈ 3,195 passed)
```

### 7.3 라이브 파이프라인 검증

1. 기존 프로젝트(000000)에서 Stage4 1화 실행
2. PatternTracker가 직전 5화 패턴을 정확히 집계하는지 확인
3. WritingDirective가 생성되어 CW 컨텍스트에 주입되는지 로그 확인
4. Director가 mandatory_context에서 directive를 수신하는지 로그 확인
5. CW self-critique에서 directive 위반 체크가 동작하는지 확인

---

## 8. 참고: 기존 CW COMMON_RULES (8개)

```
1. 감정어 삭제 → 행동 변환
2. 감각적 묘사 강화 (오감 활용)
3. 요약된 대화의 장면화
4. 문장 밀도 조절
5. [V63] 예측 가능한 전개 금지 → 반전 삽입
6. [V63] 긴장 유지 원칙
7. [V63] 캐릭터 고유 반응
8. [TF-36] 웹소설 줄바꿈 규칙
```

TF-54로 9~11번 추가:
```
9.  [TF-54] 은유 다양성
10. [TF-54] 강도 조절
11. [TF-54] NPC 음성 분화
```

---

## 9. 참고: 기존 build_common_context() 시그니처

```python
def build_common_context(
    self,
    ep_num: int,
    blueprint: dict,
    prev_manuscript: str,
    hud_report: str,
    arc_doc: str,
    master_bible: dict,
    style_guide: str,
    director_feedback: str,
    failure_constraints: str,
    npc_equipment_summary: str,
    intro_dna: str = "CYNICAL",
    purism_prompt: str = "",
    world_state_summary: str = "",
    chain_link_section: str = "",
    emotional_beat_section: str = "",
    motivations: list = None,
    promises: list = None,
    upcoming_arc_items: list[str] = None,
)
```

`writing_directive: WritingDirective | None = None` 파라미터 추가 예정.

---

## 10. 참고: DynamicPromptWeighter 통합 가능성

기존 `modules/core/dynamic_prompt_weighting.py`에 CONTINUITY, ITEM_MANAGEMENT, RELATIONSHIP, PACING 등 카테고리가 있으나, 현재 chief_writer.py 파이프라인에서 **사용되지 않음**. 스타일/표현 카테고리도 없음. 향후 WritingDirective와 DynamicPromptWeighter 통합 검토 가능 (후순위).
