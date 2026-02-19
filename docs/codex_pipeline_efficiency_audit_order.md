# Codex 오더: 파이프라인 효율성 전수 감사

> Dead Config / Information Bottleneck / Broken Wiring 3대 패턴 전수 조사.
> 코드 수정 없음. 조사만.

---

## 배경

이전 Gemini 컨텍스트 조사에서 3가지 비효율 패턴을 발견:
- `use_summary` 파라미터 구현됐지만 미반영 (Dead Config)
- 벡터 메모리 요약이 제목 100자로 축소 (Information Bottleneck)
- ChainOfVerification 초기화만 되고 미호출 (Broken Wiring)

**이런 패턴이 코드베이스 전체에 더 있는지** 전수 조사.

---

## 조사 대상 파일

```
# 전체 대상
modules/domain/agents/*.py        # 에이전트 20+개
modules/core/*.py                 # 코어 모듈 30+개
modules/validation/*.py           # 검증 모듈 15+개
modules/core/genre_guards/*.py    # 장르 가드 10+개
modules/core/stage0/*.py          # Stage 0 모듈
main_a.py                         # 진입점 (4200줄)
config/settings/validation.yaml   # 설정 파일
config/prompts/*.yaml             # 프롬프트 43개
```

---

## 패턴 A: Dead Config — 설정은 있는데 안 읽힘

### 조사 방법

1. **`__init__`에서 설정되는 모든 self 속성** 중, 같은 클래스 내 다른 메서드에서 **한 번도 참조되지 않는** 것을 찾으세요.

```python
# 이미 발견된 예시:
self.history_check_max_episodes = 10  # director.py:57 — 참조 0건
```

2. **함수 파라미터 중 본문에서 사용되지 않는 것**을 찾으세요.

```python
# 이미 발견된 예시:
def check_manuscript_history_conflicts(self, ..., use_summary: bool = True, ...):
    # use_summary가 분기 로직에 반영 안 됨
```

3. **`validation.yaml`에 정의됐지만 `_threshold()`로 읽히지 않는 키**를 찾으세요.

4. **`config/prompts/*.yaml`에 정의됐지만 `PromptLoader.load()`로 로드되지 않는 프롬프트**를 찾으세요.

### 중점 조사 파일

| 파일 | 이유 |
|------|------|
| `modules/domain/agents/director.py` `__init__` | 설정값 다수 정의 |
| `modules/domain/agents/chief_writer.py` `__init__` | 설정값 다수 정의 |
| `modules/domain/agents/base_agent.py` `__init__` | 공통 설정 |
| `main_a.py` `__init__` (L200~400) | 모듈 초기화 속성 다수 |
| `modules/validation/validation_orchestrator.py` `__init__` | 검증 설정 |
| 모든 genre_guard `__init__` | 장르별 설정값 |

### 기록 형식

```markdown
### [Dead Config] 파일:라인 — 속성/파라미터명
- 정의: `self.xxx = value` 또는 `param: type = default`
- 참조: 0건 (또는 "1건이지만 실제 분기에 미반영")
- 의도된 용도 추정: ...
- 심각도: HIGH(기능 미작동) / MEDIUM(최적화 불가) / LOW(미관)
```

---

## 패턴 B: Information Bottleneck — 데이터가 경로 중간에 축소

### 조사 방법

1. **`[:N]` 슬라이싱으로 데이터가 잘리는 모든 지점**을 찾으세요. 특히:
   - LLM 응답 파싱 후 일부 필드만 추출하고 나머지 버리는 곳
   - 에이전트 A의 출력을 에이전트 B에 전달할 때 축소하는 곳
   - DB 저장 시 데이터를 축소하는 곳

2. **LLM 응답에서 파싱 후 버려지는 필드**를 찾으세요.

```python
# 예시 패턴:
result = self._extract_json_robust(response)
score = result.get("score", 0)        # 사용됨
feedback = result.get("feedback", "") # 사용됨
reasoning = result.get("reasoning")   # ← 버려짐?
details = result.get("details")       # ← 버려짐?
```

3. **Stage 간 데이터 전달에서 손실**을 찾으세요.
   - Stage 2 → Stage 3: Arc 데이터 중 빠지는 필드
   - Stage 3 → Stage 4: Blueprint 데이터 중 빠지는 필드
   - Stage 4 → DB 저장: 원고 메타데이터 중 빠지는 필드

4. **요약/압축 지점**에서 원본 대비 정보 손실률을 추정하세요.

### 중점 조사 경로

| 경로 | 조사 내용 |
|------|-----------|
| Analyst → Arc 데이터 | LLM이 Arc JSON에 넣은 필드 중 downstream에서 안 쓰이는 것 |
| Blueprint → ChiefWriter | Blueprint의 어떤 필드가 Writer 프롬프트에 안 들어가는지 |
| Director 심사 결과 → 피드백 | Director가 반환한 JSON 중 재작성 피드백에 안 들어가는 필드 |
| ChiefWriter 출력 → DB 저장 | 원고와 함께 생성된 메타(state_updates 등)의 저장 완전성 |
| 에피소드 저장 → 벡터 메모리 | 원고 → 임베딩 시 얼마나 축소되는지 |
| NPC 팩트시트 → 프롬프트 | 팩트시트 전체 vs 실제 프롬프트 주입량 |
| WorldState → 프롬프트 | 세계 상태 전체 vs 요약 주입량 |
| FactLedger → 프롬프트 | 팩트 원장 전체 vs 요약 주입량 |

### 기록 형식

```markdown
### [Bottleneck] 파일:라인 — 설명
- 입력 크기: ~N자 / N필드
- 출력 크기: ~M자 / M필드
- 손실률: ~X%
- 잃어버리는 정보: 구체적으로 무엇
- 심각도: HIGH(모순 유발 가능) / MEDIUM(품질 저하) / LOW(미미)
```

---

## 패턴 C: Broken Wiring — 구현됐는데 호출 안 됨

### 조사 방법

1. **`main_a.py`에서 초기화되는 모든 모듈** 중 실제 파이프라인(Stage 0/2/3/4)에서 **호출되지 않는** 것을 찾으세요.

```python
# 이미 발견된 예시:
self.chain_of_verification = ChainOfVerification(...)  # 초기화만, .verify() 미호출
```

2. **클래스에 정의된 public 메서드** 중 **외부에서 호출되지 않는** 것을 찾으세요.
   - `_`로 시작하는 private 메서드는 제외
   - 테스트에서만 호출되는 것은 별도 표기

3. **import 되지만 사용되지 않는 모듈/클래스**를 찾으세요.

4. **조건부로만 활성화되는 경로** 중 그 조건이 **현재 코드에서 절대 True가 안 되는** 것을 찾으세요.

```python
# 예시 패턴:
if self.some_flag:  # ← some_flag가 항상 False면 dead path
    self.do_something()
```

### 중점 조사 대상

| 대상 | 조사 이유 |
|------|-----------|
| `main_a.py` L200~400 초기화 블록 | V50~V65 시대 모듈 중 미연결 가능성 |
| `main_a.py` L1600~1700 V53 모듈 초기화 | 지능 향상 모듈 5개 중 미연결 확인 |
| `base_agent.py` public 메서드 | 범용 메서드 중 미사용 |
| `director.py` + 5개 서브모듈 | Director 기능 중 미호출 |
| `chief_writer.py` + 2개 서브모듈 | Writer 기능 중 미호출 |
| 각 genre_guard의 public 메서드 | 가드 검사 중 미호출 |
| `modules/core/` 유틸 모듈 | 유틸 함수 중 미사용 |

### 기록 형식

```markdown
### [Broken Wiring] 파일:라인 — 클래스.메서드명
- 구현 상태: 완전 구현 / 부분 구현 / 스텁
- 초기화: main_a.py:NNNN 에서 초기화됨 / 안 됨
- 호출: 0건 / N건(테스트만)
- 의도된 용도: ...
- 활성화 방법 추정: ...
- 심각도: HIGH(핵심 기능 미작동) / MEDIUM(보조 기능) / LOW(레거시)
```

---

## 추가 조사: 에이전트 간 피드백 루프 손실

### Director 피드백 → Writer 재작성 경로

Director가 REJECT 판정 시 피드백을 Writer에게 전달하는 경로를 추적하세요:

1. Director가 반환하는 피드백 JSON의 **전체 필드 목록**
2. 그 중 **Writer 재작성 프롬프트에 실제 주입되는 필드**
3. **빠지는 필드**가 있다면 무엇인지

### Validator 경고 → Director 판정 경로

validation_orchestrator가 수집한 경고/위반이 Director 심사 프롬프트에 들어가는 경로:

1. 각 Validator가 반환하는 **경고/위반 필드 전체**
2. Director 프롬프트에 **실제 주입되는 필드**
3. **빠지는 정보**가 있다면 무엇인지

---

## 출력 형식

파일명: `docs/파이프라인_효율성_감사_결과.md`

```markdown
# 파이프라인 효율성 감사 결과

## 요약
- Dead Config: N건
- Information Bottleneck: N건
- Broken Wiring: N건

## 1. Dead Config 목록 (심각도순)
### [HIGH] ...
### [MEDIUM] ...
### [LOW] ...

## 2. Information Bottleneck 목록 (심각도순)
### [HIGH] ...
### [MEDIUM] ...
### [LOW] ...

## 3. Broken Wiring 목록 (심각도순)
### [HIGH] ...
### [MEDIUM] ...
### [LOW] ...

## 4. 피드백 루프 손실 분석
### Director → Writer
### Validator → Director

## 5. 개선 우선순위 Top 10
```

---

## Codex 실행 설정

```
모드: 읽기 전용 (코드 수정 없음)
모델: o3 또는 o4-mini
라운드: 제한 없음
컨텍스트: 이 파일 + 코드베이스 전체
```

## 주의사항

- **코드를 수정하지 마세요.** 조사만 하세요.
- `main_a.py`는 4200줄 — `__init__`(L200~400)과 모듈 초기화(L1500~1700) 구간을 중점 확인
- Dead Config 판정 시, **테스트에서만 참조되는 경우**는 별도 표기 (프로덕션 미사용)
- Broken Wiring 판정 시, **의도적으로 비활성화된 경우** (주석에 "disabled", "TODO" 등) 별도 표기
- Information Bottleneck에서 **`[:N]` 패턴**은 이전 조사(`docs/컨텍스트_활용_조사_결과.md`)에서 이미 찾은 컨텍스트 절삭은 제외 — **새로운 손실 지점만** 보고
- `_threshold()` 패턴 (`modules/validation/threshold_helper.py`)의 작동 방식을 이해한 뒤, YAML에 키가 있는데 `_threshold()`로 안 읽히는 것도 Dead Config으로 분류
