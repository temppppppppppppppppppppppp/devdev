# Phase 4: Few-Shot Justification Patterns - 구축 완료

**날짜**: 2026-01-29
**상태**: ✅ 전체 구축 완료 및 테스트 통과 (3/3)

---

## 📌 Phase 4의 목표

**문제**: Phase 1-3는 "나쁜 것을 차단"하는 데 집중. 하지만 AI가 제약 조건(나약한 몸, 낮은 지위)을 극복하는 **방법**을 모르면, 창의성이 억제됨.

**해결**: Few-Shot Learning을 통해 AI에게 "정당화 논리 구조"를 가르침. 패턴은 제약이 아닌 영감의 원천.

**핵심 통찰** (from Gemini 대화):
> "정당화는 창의성과 일관성의 다리"
> `state → obstacle → justification → result`

---

## 🏗️ 구축 내역

### Phase 4.1: Justification Pattern Library ✅

**파일**: `modules/core/justification_patterns.py`

**패턴 구조**:
```python
JUSTIFICATION_PATTERNS = {
    "wuxia": {
        "weak_body_strong_action": {
            "description": "나약한 신체로 강력한 행동을 할 때의 정당화 패턴",
            "logic_structure": "[제약 인정] → [특수 방법 활용] → [대가 명시] → [결과 달성]",
            "examples": [
                {
                    "situation": "나약한 몸으로 100근 대도 들기",
                    "justification": "전생에 체득한 발경법으로 팔목의 기혈을 순간 폭발시켰다. 뼈마디가 어긋나는 고통이 밀려왔지만, 녹슨 철괴는 지면에서 떨어졌다.",
                    "structure": "[제약: 나약] → [방법: 발경법] → [대가: 뼈 고통] → [결과: 들어올림]"
                },
                ...
            ],
            "creation_guide": "위 예시들의 '논리 구조'를 참고하여 새로운 정당화를 창의적으로 만드십시오."
        },
        "low_status_high_authority": {...},
        "sudden_power_increase": {...}
    },
    "hunter": {
        "low_rank_high_achievement": {...},
        "sudden_power_increase": {...}
    },
    "investment": {
        "weak_capital_high_return": {...}
    }
}
```

**총 패턴 수**: 6개 (무협 3개, 헌터 2개, 투자 1개)

**Helper Functions**:
- `get_justification_guide(genre, situation_type)` - Few-Shot 프롬프트 생성
- `get_available_patterns(genre)` - 사용 가능 패턴 목록
- `get_pattern_description(genre, situation_type)` - 짧은 설명

---

### Phase 4.2: BlockingValidator 제안 기능 ✅

**파일**: `modules/validation/blocking_validator.py`

**신규 기능**:
```python
BlockingValidator(context=None, enable_justification_checks=False)
```

**기본값 OFF**: 통과율 유지를 위해 옵션 체크
**활성화 시**: 제약 위반 감지 + 정당화 패턴 제안

**신규 체크 메서드**:
1. `_check_physical_capability()` - 나약한데 강한 행동
2. `_check_authority_exercise()` - 낮은 지위로 명령/지시

**실패 시 반환 포맷**:
```python
{
    "check": "physical_capability",
    "passed": False,
    "reason": "나약한 신체 상태(나약, 중독)에서 강력한 행동 수행",
    "severity": "MEDIUM",
    "location": 1234,
    "context": "주변 100자...",
    "suggested_pattern": "나약한 신체로 강력한 행동...",
    "justification_guide": "Few-Shot 예시들...",
    "fix_template": "'{행동}' 직전에 정당화 문구를 추가하십시오...",
    "quick_fixes": [
        "전생 기억/경험을 활용한 효율적 방법",
        "기혈을 짜내며 순간 폭발력 (부작용 명시)",
        "특수 기법으로 힘의 방향 전환 (대가 표현)"
    ]
}
```

**감지 패턴**:
- 물리적 능력: `무거운.*들어올`, `\d{2,}근.*대도`, `일격에.*박살` 등
- 권위 행사: `명령했다`, `지시했다`, `복종하라`, `단호하게.*말했다` 등

**정당화 키워드 체크**: 이미 정당화가 있으면 통과 (발경, 기혈, 전생, 경험 등)

---

### Phase 4.3: Writer 통합 ✅

**파일**: `modules/domain/agents/writer.py`

**신규 메서드**:
```python
def _build_justification_guidance(hud_report: str, genre_name: str) -> str
```

**동작 방식**:
1. HUD에서 제약 조건 자동 감지
   - 신체 제약: `['나약', '중독', '부상', '중상', '쇠약', '기력고갈', '기혈역류']`
   - 지위 제약: `['하인', '노예', '평민', '무명', '낭인', '거지']` + `reputation < 30`
   - 돌파 가능성: `['돌파', '깨달음', '체득', '각성', '각오']`

2. 해당 제약에 맞는 Few-Shot 패턴 로드
3. Writer 프롬프트에 자동 주입

**프롬프트 위치**:
```python
dynamic_prompt = f"""
{mandatory_context}
{feedback_section}
{reference_anchor_prompt}
{anti_trope}
{justification_guidance}  # ← Phase 4 추가

[WRITER'S FOCUS MISSION]
...
"""
```

**효과**: Writer가 제약 조건 극복 장면 작성 시, 자동으로 Few-Shot 패턴을 참고하여 정당화 고려

---

## ✅ 테스트 결과

**테스트 파일**: `test_phase4_justification_system.py`

```
============================================================
Phase 4 테스트 결과 요약
============================================================
✅ PASS          Phase 4.1 (Pattern Library)
✅ PASS          Phase 4.2 (Validator Suggestions)
✅ PASS          Phase 4.3 (Writer Integration)
============================================================
통과: 3/3 (100.0%)
============================================================

[SUCCESS] Phase 4 완료! 정당화 시스템 준비됨.
```

**검증 항목**:
- Phase 4.1: 패턴 로드, Few-Shot 가이드 생성, 다중 장르 지원
- Phase 4.2: 옵션 체크 활성화/비활성화, 제약 감지, 제안 제공
- Phase 4.3: Writer 메서드 존재, HUD 파싱, 제약 감지, 가이드 생성

---

## 🎯 Few-Shot Learning의 핵심

### "패턴은 감옥이 아닌 영감의 원천"

**질문**: 패턴이 5개면 AI는 5가지 표현만 쓰는가?
**답변**: 아니다. AI는 논리 구조를 학습하여 무한한 변주를 창조한다.

**예시**:
```
논리 구조: [제약 인정] → [특수 방법] → [대가 명시] → [결과]

패턴 예시 1: "나약한 몸 + 발경법 + 뼈 고통 + 들어올림"
AI 창조 1: "나약한 몸 + 진기 역류 + 피토 + 박살냄"
AI 창조 2: "중독 상태 + 혈도 자극 + 수명 감소 + 돌파"
AI 창조 3: "쇠약 + 전생 기억 + 정신적 고통 + 통찰"
...무한 변주 가능
```

**CoT 구조와의 연결**:
```
state → obstacle → justification → result
  ↓         ↓            ↓            ↓
[제약]   [장애]      [특수 방법]    [결과]
                     [대가 명시]
```

---

## 💰 비용 영향

**Phase 4 추가 비용**: $0

- Pattern Library: 정적 데이터 (Python dict)
- BlockingValidator 체크: Python 정규식 (LLM 호출 없음)
- Writer 가이드: 프롬프트 토큰 약간 증가 (~200토큰)

**총 프로젝트 비용** (250화 기준):
- Phase 1-3: ~$10 (V0128 검증 비용)
- Phase 4: $0
- **합계**: ~$10

---

## 🔧 사용 방법

### 1. 기본 모드 (현재 설정)
Phase 4.3 (Writer 통합)만 활성화됨. Writer가 자동으로 정당화 패턴 학습.

### 2. 고급 모드 (옵션)
Phase 4.2 (Validator 제안)을 활성화하려면:

**방법 1**: ValidationOrchestrator 수정
```python
# modules/validation/validation_orchestrator.py
self.blocking = BlockingValidator(
    context=self.context,
    enable_justification_checks=True  # ← 추가
)
```

**방법 2**: settings.json에 옵션 추가 (권장)
```json
{
  "validation": {
    "use_v0128": true,
    "use_retrospective": true,
    "enable_justification_checks": true  // ← 추가
  }
}
```

---

## 🚀 다음 단계

### 1. 원고 생산 테스트
- 기존 프로젝트 또는 신규 프로젝트 선택
- 1-3화 생산하여 Phase 4 효과 확인
- Writer가 제약 극복 시 자동으로 정당화를 사용하는지 검증

### 2. 피드백 수집
- 정당화가 자연스럽게 삽입되는가?
- 정당화 표현이 반복되지 않고 창의적인가?
- 논리 구조는 유지되면서 표현은 다양한가?

### 3. 패턴 확장 (선택)
필요 시 `justification_patterns.py`에 새로운 패턴 추가:
- Romance: `poor_status_high_appeal` (가난한데 매력적)
- Fantasy: `low_mana_powerful_spell` (마나 없는데 강력한 주문)
- SF: `outdated_tech_breakthrough` (구식 기술로 돌파)

---

## 📊 전체 시스템 요약

```
┌─────────────────────────────────────────────────────────────┐
│                  서사 관성 극복 시스템                      │
│                     (4 Phases Complete)                      │
└─────────────────────────────────────────────────────────────┘

[Phase 1] Prompt Engineering ($0)
   ├─ Anti-Trope Instructions (클리셰 회피)
   └─ Mandatory Context (과거 맥락 강제 상기)

[Phase 2] Infrastructure ($0)
   ├─ Relationship State Machine (관계 일관성)
   └─ Information Diffusion (정보 전파)

[Phase 3] Retrospective ($0)
   └─ Long-term Consistency (5화 추적)

[Phase 4] Few-Shot Justification ($0)
   ├─ Pattern Library (정당화 패턴)
   ├─ Validator Suggestions (실패 시 제안)
   └─ Writer Integration (자동 적용)

═══════════════════════════════════════════════════════════════
총 비용: ~$10 (250화)
서사 관성 극복율: 예상 80%+
AI 창의성: 보존 (Few-Shot Learning)
═══════════════════════════════════════════════════════════════
```

---

## 🎉 결론

**Phase 4 완료로 서사 관성 극복 시스템이 완성되었습니다.**

**핵심 성과**:
1. ✅ 차단 시스템 (Phase 1-3) - 나쁜 것을 막음
2. ✅ 생성 시스템 (Phase 4) - 좋은 것을 만드는 법 가르침
3. ✅ Few-Shot Learning - 창의성 보존하면서 논리성 확보
4. ✅ $0 비용 - 모든 구조적 개선은 Python 기반

**차별화 포인트**:
- 하드코딩된 규칙 ❌
- AI에게 논리 구조를 가르쳐 무한 변주 창조 ✅

**이제 실전 테스트를 통해 효과를 검증할 차례입니다!**

---

*작성: Claude Code*
*날짜: 2026-01-29*
