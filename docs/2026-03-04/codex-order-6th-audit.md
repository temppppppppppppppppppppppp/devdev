# Codex Order: 6차 전수조사

> **목적**: 최근 구현 3종(TF-54 WritingDirective / Model SSOT / 합격률 개선)의
> **신규 코드 전수 감사** + 기존 코드에서 아직 미감사된 영역 P0/P1 이슈 발굴·패치.
> **금지**: 모델 값 변경. 기존 테스트 시그니처 변경. 명세에 없는 신기능 추가.
> **출력 보고서**: `docs/2026-03-04/6th-audit-result.md`

---

## 0) 강제 제약

- 각 패치 후 즉시 `python -m py_compile <수정파일>` 통과 필수.
- `pytest tests/ -q` 기준선: **3213 passed, 16 skipped, 0 failed**.
- `ruff check modules/ tests/` 위반 0건 유지.

---

## 1) 감사 대상 파일 (우선순위 순)

### A 그룹 — TF-54 신규 파일 (전수 감사)

| 파일 | 줄 수 | 주목 포인트 |
|------|-------|-----------|
| `modules/core/pattern_tracker.py` | 1125 | build_report() 예외 처리, manuscripts 빈 경우, regex 컴파일 안전성 |
| `modules/core/writing_directive_generator.py` | 196 | LLM 응답 파싱 실패 폴백, prompt_loader 미로드 폴백 |
| `modules/core/stage4_types.py` | TF-54 추가분 | WritingDirective.is_empty() 명세 완결성 |

### B 그룹 — Model SSOT 변경 파급 (타격점 감사)

| 파일 | 타격점 |
|------|-------|
| `modules/core/constants.py` | `_load_model_from_yaml()` import-time 실행 — circular import, FileNotFoundError 처리 |
| `modules/core/config_manager.py` | `_load_agents_from_yaml()` fallback dict 완전성 |

### C 그룹 — 합격률 개선 파급

| 파일 | 타격점 |
|------|-------|
| `modules/domain/agents/chief_writer_quality.py` | `apply_self_critique()` blueprint/directive getattr fallback 경로 |
| `modules/core/stage4_interview_round.py` | blueprint setattr L111 — dict 타입 검사 경계 |

### D 그룹 — 잔존 하드코딩 (SSOT 미완 부분)

아래 파일들은 모델 SSOT 작업에서 **의도적으로 제외**된 것들이나, 정책 일관성 확인이 필요:

```
modules/core/adversarial_self_play.py:136     default="gemini-2.5-flash"
modules/core/chain_of_verification.py:122     default="gemini-2.5-flash"
modules/core/confidence_calibration.py:94     self.model = "gemini-2.5-flash"
modules/core/cross_agent_verifier.py:118      default="gemini-2.5-flash"
modules/core/multi_agent_deliberation.py:181  default="gemini-2.5-flash"
modules/core/reference_anchor.py:110          model_tier="gemini-2.5-flash"
modules/domain/agents/arc_corrector.py:592    default="gemini-2.5-flash"
modules/domain/agents/arc_critic.py:131,368   default="gemini-2.5-flash"
modules/domain/agents/arc_ensemble.py:113,890 default="gemini-2.5-pro"
```

**감사 방침**: 이 파일들은 `AIModels.*`로 교체하면 되나, **호출자가 명시적으로 값을 주입하는 경우**(default만 바꿔도 무방한지) 확인 후 P0/P1 분류. 호출자가 항상 덮어쓰면 → P2(무해), 호출자가 default를 그대로 쓰는 경우 → P1(교체 권장).

---

## 2) 감사 체크리스트

> **수동 검사 필수**: 각 항목마다 해당 파일을 직접 열어 코드를 읽고 로직을 확인한 후
> 런타임 스크립트로 검증한다. 스크립트만으로 통과해도 코드를 읽지 않으면 감사 미완.

---

### A-1: PatternTracker 엣지케이스

**① 코드 수동 검사** — 아래 메서드를 직접 읽어라:

```
파일: modules/core/pattern_tracker.py
읽을 범위:
  - build_report()       전체
  - _load_manuscripts()  전체
  - _count_expressions() 전체
  - _classify_endings()  전체
```

체크포인트:
- `build_report(db=None)` → `_load_manuscripts()` 진입 전에 `db is None` 방어 있는지
- `_load_manuscripts()` 반환 `[]` 일 때 → `_count_expressions([])` 에서 분모 0 없는지
- `_count_expressions()` 내부 — manuscripts 합산 후 `total == 0` 분기 처리 있는지
- `TRACKED_EXPRESSIONS` 각 패턴이 `re.compile()` 가능한지 (raw string `r"..."` 여부)

**P0 기준**: ZeroDivisionError / AttributeError / re.error 미처리 → 런타임 크래시 가능.
**P1 기준**: None 타입 미검사로 silent wrong behavior.

**② 런타임 검증**:

```bash
python -c "
from modules.core.pattern_tracker import PatternTracker, TRACKED_EXPRESSIONS
import re
for p in TRACKED_EXPRESSIONS:
    try:
        re.compile(p)
    except re.error as e:
        print(f'REGEX_ERROR: {p!r} → {e}')

pt = PatternTracker()
result = pt.build_report(db=None, ep_num=1, lookback=5)
print('db=None result:', result)
"
```

---

### A-2: WritingDirectiveGenerator LLM 파싱 폴백

**① 코드 수동 검사** — 아래 메서드를 직접 읽어라:

```
파일: modules/core/writing_directive_generator.py
읽을 범위:
  - _parse_response()  전체
  - generate()         전체 (try/except 구조 확인)
```

체크포인트:
- `_parse_response("")` — 빈 문자열 입력 시 JSONDecodeError 전파 없이 `WritingDirective()` 반환하는지
- `_parse_response('{"expression_ban": "단일문자열"}')` — ban 필드가 str일 때 list로 변환하는지, 아니면 그대로 str 할당인지
- `generate()` 최상위 except — LLM 호출 실패 시 `WritingDirective()` 반환하는지 확인

**② 런타임 검증**:

```bash
python -c "
from modules.core.writing_directive_generator import WritingDirectiveGenerator
gen = WritingDirectiveGenerator()
for raw in ['', '{}', 'not json', '{\"expression_ban\": \"단일문자열\"}']:
    wd = gen._parse_response(raw)
    print(f'{raw!r} → ending_style={wd.ending_style!r}, ban={wd.expression_ban}')
"
```

---

### A-3: WritingDirective.is_empty() 완전성

**① 코드 수동 검사**:

```
파일: modules/core/stage4_types.py
읽을 범위: WritingDirective 클래스 전체 (is_empty() 포함)
```

체크포인트:
- `is_empty()` 구현이 `not any([ending_style, metaphor_avoid, expression_ban])` 인지 확인
- `emotion_required` / `intensity_note` / `npc_directives` 단독 시 `is_empty()=True` → Director MC에 미추가. 이것이 의도된 정책인지 확인.
- 의도된 정책이 아니라면 P1 패치.

---

### B-1: _load_model_from_yaml() 안전성

**① 코드 수동 검사**:

```
파일: modules/core/constants.py
읽을 범위: _load_model_from_yaml() 함수 전체 + AIModels 클래스 attribute 선언부
```

체크포인트:
- `try/except Exception` 블록이 `FileNotFoundError`, `KeyError`, `yaml.YAMLError` 전부 포함하는지
- `import yaml` 이 함수 내부 지연 import인지 확인 (circular import 방지)
- `_val` 이 빈 문자열 `""` 일 때 fallback으로 넘어가는지 (`if _val and isinstance(_val, str)`)

**② 런타임 검증**:

```bash
python -c "
import modules.core.constants as c
print('STAGE4_FIXED_WRITER_MODEL:', c.AIModels.STAGE4_FIXED_WRITER_MODEL)
print('FLASH_ANALYSIS_MODEL:', c.AIModels.FLASH_ANALYSIS_MODEL)
print('EMERGENCY_FALLBACK:', c.AIModels.EMERGENCY_FALLBACK)
"
```

---

### B-2: ConfigManager fallback dict 완전성

**① 코드 수동 검사**:

```
파일: modules/core/config_manager.py
읽을 범위: __init__() + _load_agents_from_yaml() + fallback dict 전체
```

체크포인트:
- fallback dict 키 목록이 `models.yaml`의 `agents` 섹션 키와 일치하는지
- `_load_agents_from_yaml()` 실패 시 fallback dict의 `writer` 값이 `"gemini-2.5-flash"` 인지 (`models.yaml`과 동일해야 함)

**② 런타임 검증**:

```bash
python -c "
from modules.core.config_manager import ConfigManager
cm = ConfigManager()
models = cm.settings.get('models', {})
print('모델 키 목록:', list(models.keys()))
expected = ['analyst', 'writer', 'director', 'validator', 'four_phase_arc_generator',
            'state_locked_arc_generator', 'chief_writer']
for k in expected:
    print(f'  {k}: {models.get(k, \"MISSING\")}')
"
```

---

### C-1: blueprint setattr 타입 안전성

**① 코드 수동 검사**:

```
파일: modules/core/stage4_interview_round.py
읽을 범위: blueprint setattr 처리 블록 (L105~L115 근방)

파일: modules/domain/agents/chief_writer_quality.py
읽을 범위: apply_self_critique() L67~L104 (getattr fallback 블록)
```

체크포인트:
- `setattr(chief_writer, "_current_blueprint", blueprint if isinstance(blueprint, dict) else {})` — `blueprint`가 `None` / `str` / `list`일 때 `{}` 설정되는지
- `apply_self_critique()` 내 `getattr(self.host, "_current_blueprint", None)` → None이면 `_check_ending_hook_presence(content, None)` → `[]` 반환 (안전 경로 확인)

---

### C-2: _self_critique 경로별 blueprint 전달 완전성

**① 코드 수동 검사**:

```
파일: modules/domain/agents/chief_writer_quality.py
읽을 범위: apply_self_critique() 전체 (L67~L175 근방)
```

체크포인트:
- `_self_critique()` 호출이 총 몇 곳인지 — rubric 조기 스킵 체크(L113)와 메인 루프(L139) 외에 더 있는지
- 모든 호출부에 `blueprint=blueprint, directive=directive, expression_freq=expression_freq` 인자가 **전달되는지** 확인
- 누락된 호출부가 있으면 → P1 패치

**② 런타임 검증**:

```bash
grep -n "_self_critique(" modules/domain/agents/chief_writer_quality.py
```

---

### D-1: 잔존 하드코딩 P1 분류

**① 코드 수동 검사** — 9개 파일 각각:

```
modules/core/adversarial_self_play.py       L136 근방
modules/core/chain_of_verification.py       L122 근방
modules/core/confidence_calibration.py      L94 근방
modules/core/cross_agent_verifier.py        L118 근방
modules/core/multi_agent_deliberation.py    L181 근방
modules/core/reference_anchor.py            L110 근방
modules/domain/agents/arc_corrector.py      L592 근방
modules/domain/agents/arc_critic.py         L131, L368 근방
modules/domain/agents/arc_ensemble.py       L113, L890 근방
```

각 파일에서 확인:
1. 해당 클래스/함수를 **호출하는 상위 코드**를 grep으로 찾아 직접 읽어라.
2. 호출자가 model 인자를 명시적으로 넘기는지 확인.
3. **호출자가 default를 사용하는 경우** → P1 (`AIModels.FLASH_ANALYSIS_MODEL` 또는 `AIModels.DEFAULT_ARCHITECT`로 교체).
4. **호출자가 항상 명시 전달** → P2 (현상 유지, `# [SSOT-P2] 호출자 명시 전달` 주석 추가).

---

## 3) 패치 원칙

### P0 패치 즉시 처리
- ZeroDivisionError / AttributeError / 예외 전파로 파이프라인 중단 가능한 경우.
- 수정 후 py_compile + 단위 검증 즉시.

### P1 패치 처리
- Silent wrong behavior, 타입 미검사, SSOT 미완 등.
- 수정 후 전체 테스트 회귀 확인.

### 보존 항목 (절대 변경 금지)
- `base_agent.py:45 DEFAULT_MODEL_TIER` — BaseAgent 폴백 체인 딕셔너리 키, 모델명 자체 아님.
- `metrics_collector.py` 가격표 — 하드코딩 정책 (SSOT 아님, 단가표).
- `arc_ensemble.py:113` gemini-2.5-pro — 호출자(`stage2_orchestrator`)가 명시 전달 여부 확인 후 결정.

---

## 4) 실행 순서

```bash
# 단계 1: 각 감사 항목 python -c 검증 스크립트 실행
# 단계 2: P0 발견 시 즉시 패치 → py_compile 확인
# 단계 3: P1 전체 수집 후 패치 → pytest tests/ -q 확인
# 단계 4: ruff check modules/ tests/
# 단계 5: 최종 전체 테스트

pytest tests/ -q
ruff check modules/ tests/
```

---

## 5) 보고서 형식

출력: `docs/2026-03-04/6th-audit-result.md`

```markdown
# 6차 전수조사 결과

> 감사일: 2026-03-04

## 감사 범위

A. TF-54 신규 파일 3개
B. Model SSOT 파급 2개
C. 합격률 개선 파급 2개
D. 잔존 하드코딩 9개 파일

## 발견 이슈

| ID | 파일 | 내용 | 등급 | 처리 |
|----|------|------|------|------|
| A-001 | pattern_tracker.py | ... | P0/P1/P2 | 패치/현상유지 |

## 패치 내역

(패치한 항목별 before/after 핵심 라인)

## 검증 결과

- py_compile: 통과
- ruff: 위반 0건
- 전체 테스트: N passed, 0 failed (16 skipped)

## P2 목록 (현상 유지 이유 포함)

(패치하지 않은 항목과 이유)
```

---

## 6) 합격 기준

- P0 이슈 **전량 패치**
- P1 이슈 **전량 패치 또는 명시적 현상유지 판정**
- 전체 테스트 **3213+ passed, 0 failed**
- ruff 위반 **0건**
