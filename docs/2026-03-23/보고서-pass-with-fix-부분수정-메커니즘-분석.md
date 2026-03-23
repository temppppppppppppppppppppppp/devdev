# 보고서: PASS_WITH_FIX 및 부분 수정 메커니즘 전수 분석

> **작성일**: 2026-03-23
> **대상 시스템**: 글도비 (Wuxia Studio) 전체 파이프라인
> **핵심 질의**: PASS_WITH_FIX가 프로그래밍적 inplace 치환인가, LLM 재생성인가?

---

## 1. 결론 요약

| 질문 | 답변 |
|------|------|
| PASS_WITH_FIX는 `str.replace("주혁","강혁")` 같은 문자열 치환인가? | **아니다.** LLM 기반 부분 재생성이다. |
| 그러면 전면 재생성인가? | **아니다.** 원본을 보존하고 지적 부분만 수정하도록 LLM에 지시한다. |
| 정확한 성격은? | **"LLM 기반 제한적 부분 재생성(Constrained Partial Regeneration)"** |
| 프로그래밍적 문자열 치환은 시스템 어디에도 없나? | **없다.** 모든 수정은 LLM 호출을 통해 이루어진다. |

### Opus 4.6 / Codex 5.4가 하는 것과의 비교

```
┌─────────────────────────────────────────────────────────────────┐
│ Opus/Codex의 "주혁→강혁" 수정                                    │
│ ─────────────────────────────                                   │
│ 방식: 프로그래밍적 문자열 치환 (deterministic, 100% 정확)          │
│ 비용: 0 토큰                                                     │
│ 원본 보존율: 해당 단어 외 100%                                    │
│ 실패 가능성: 0%                                                   │
│ 대상: 정확히 지정된 단어/문구                                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 글도비 PASS_WITH_FIX의 "주혁→강혁" 수정                          │
│ ─────────────────────────────────                               │
│ 방식: LLM에게 원본 + "주혁을 강혁으로 바꿔라" 지시 전송            │
│ 비용: 수천~수만 토큰 (원본 전체를 LLM이 읽어야 함)                 │
│ 원본 보존율: 목표 70%~100%, 실제로는 LLM이 의도치 않게 변경 가능   │
│ 실패 가능성: 있음 (LLM이 다른 부분도 건드릴 수 있음)               │
│ 대상: Director가 판단한 문제 영역                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 시스템 내 부분 수정 메커니즘 전체 목록 (3종)

글도비 파이프라인에는 **3단계의 수정 메커니즘**이 존재한다. 모두 LLM 호출 기반이며, 프로그래밍적 문자열 치환은 없다.

### 2.1. inplace_patch — 최소 변경 LLM 패치

| 항목 | 상세 |
|------|------|
| **트리거 조건** | 이전 시도 점수 ≥ 60, fix_scope = "inplace" |
| **핵심 파일** | `chief_writer.py` L1792-1837 (원고), `four_phase_arc_generator.py` L619-684 (Arc) |
| **LLM 호출** | 1회, temperature=0.3, thinking_level="medium" |
| **입력** | 원본 전문 + Director 피드백 + fix_pack (수정 대상 명세) |
| **출력** | 패치된 전문 |
| **변경량 제한** | 최대 30% 변경, 최소 70% 원본 보존, 글자 수 ±10% 이내 |
| **실패 시** | patch_with_feedback로 에스컬레이션 |
| **프롬프트 핵심 지시** | "전면 재작성하지 마세요. 지적된 부분만 고치세요." |

**Structural Variant**: 장면(scene) 단위로 타겟팅하는 구조적 inplace patch도 존재
- `chief_writer.py` L1424-1562: `_attempt_structural_inplace_patch()`
- 특정 scene block만 LLM에 전송, 나머지는 프로그래밍적으로 원본 유지
- 이것이 가장 "inplace"에 가까운 메커니즘 (scene 단위 교체)

### 2.2. patch_with_feedback — 앙상블 기반 제한적 재생성

| 항목 | 상세 |
|------|------|
| **트리거 조건** | 이전 시도 점수 50~59, 또는 inplace 실패 후 폴백 |
| **핵심 파일** | `chief_writer.py` L1955-2067 (원고), `four_phase_arc_generator.py` L690-783 (Arc) |
| **LLM 호출** | 1회 (이전 성공 전략 단독 사용, 3-전략 앙상블 아님) |
| **입력** | 원본 + Director 피드백 + 이전 시도의 전략/제약 조건 |
| **출력** | 패치된 전문 (원본 구조 보존 목표) |
| **변경량 제한** | 명시적 비율 제한 없으나, 프롬프트로 보존 지시 |
| **실패 시** | 전면 재생성으로 에스컬레이션 |

### 2.3. 전면 재생성 (Full Regeneration)

| 항목 | 상세 |
|------|------|
| **트리거 조건** | 점수 < 50, 또는 모든 패치 시도 실패 |
| **LLM 호출** | 3회 (3-전략 앙상블) |
| **입력** | 블루프린트 + Director 피드백 (원본 파기) |
| **출력** | 완전히 새로운 원고 3종 → Director가 최종 선택 |
| **에스컬레이션 전략** | ToT (Tree-of-Thoughts), MAD (Multi-Agent Debate) |

---

## 3. 점수 기반 라우팅 결정 트리

```
Director 평가 점수
    │
    ├── score ≥ 60 ──→ inplace_patch (LLM 1회, 최소 변경)
    │                    │
    │                    ├── 성공 → PASS
    │                    └── 실패 → patch_with_feedback로 폴백
    │
    ├── 50 ≤ score < 60 ──→ patch_with_feedback (LLM 1회, 전략 단독)
    │                         │
    │                         ├── 성공 → PASS
    │                         └── 실패 → 전면 재생성
    │
    └── score < 50 ──→ 전면 재생성 (LLM 3회, 앙상블)
```

**설정값** (config/settings/validation.yaml):
```yaml
patch_mode:
  rewrite_below: 50           # < 50: previous_best 파기 → 전면 재생성
  inplace_below: 60           # ≥ 60: in-place 단일 LLM 수정 허용
  min_patched_length: 2000    # InPlace 패치 최소 글자 수
  inplace_max_change_ratio: 0.30   # 30% 이상 변경 시 패치 폐기
  inplace_min_preserve_ratio: 0.70  # 원본 대비 70% 미만 축소 시 패치 폐기
```

**임계값 클래스** (constants.py L633-645):
```python
class PatchModeThresholds:
    REWRITE = 50   # 미만: 전면 재작성
    INPLACE = 60   # 이상: in-place 단일 수정
```

---

## 4. PASS_WITH_FIX 상세 플로우

### 4.1. Director → PASS_WITH_FIX 판정 발행

Director Ensemble이 원고를 평가한 결과:
- 전반적으로 합격이나 **국소적 문제**가 있을 때 발행
- 반드시 `fix_pack`을 동반해야 유효

```python
fix_pack = {
    "patch_targets": ["scene 2-1 대화문", "3번째 문단 묘사"],  # 수정 대상
    "must_fix": ["주혁→강혁 이름 수정", "시간대 3일 경과 반영"],  # 필수 수정
    "do_not_regress": ["주인공의 입문 결정", "NPC 감정선"],        # 건드리면 안 되는 것
    "success_condition": "이름 불일치 해소, 타임라인 정합",        # 성공 기준
    "target_kind": "entity_ref",   # 수정 범위 유형
}
```

**target_kind 유형들**:
- `entity_ref`: 고유명사, 이름, 직급 (가장 국소적)
- `local_phrase`: 특정 문구/표현
- `local_sentence`: 특정 문장
- `scene_model`: 장면 단위 (가장 넓은 범위)

### 4.2. 패치 실행 루프 (최대 3회)

```
PASS_WITH_FIX 판정
    │
    ▼
┌── fix_i = 0, 1, 2 (최대 3회 반복) ──┐
│                                       │
│  1. 계약 검증 (fix_pack 유효성)       │
│     └── 무효 → REJECT으로 다운그레이드 │
│                                       │
│  2. inplace_patch() 실행              │
│     └── LLM에 원본+fix_pack 전송      │
│                                       │
│  3. 변경량 검증                        │
│     ├── 변경 > 30% → 패치 폐기        │
│     ├── 보존 < 70% → 패치 폐기        │
│     └── 글자 수 < 2000 → 패치 폐기    │
│                                       │
│  4. Director 재감사 (reaudit)         │
│     ├── PASS → 최종 합격, 루프 종료    │
│     ├── PASS_WITH_FIX → 다음 반복      │
│     └── REJECT → REJECT으로 전환       │
│                                       │
└───────────────────────────────────────┘
```

**핵심 파일**: `stage4_retry_runtime.py` L90-236 `execute_pass_with_fix_loop()`

### 4.3. 변경량 추적

```python
# constants.py L168-179
def calc_patch_change_ratio(original: str, patched: str) -> float:
    """0.0 = 동일, 1.0 = 완전히 다름. SequenceMatcher 사용 (Korean text용 autojunk=False)"""

def log_patch_diff(stage: str, original: str, patched: str):
    """unified diff 생성, 글자 수 변화 로깅. ex: '제4-Manuscript 2500→2480 (−0.8%)'"""
```

---

## 5. 각 Stage별 적용 현황

| Stage | 대상 산출물 | inplace_patch | patch_with_feedback | 전면 재생성 |
|-------|-----------|:---:|:---:|:---:|
| Stage 2 | Arc 설계 | `_inplace_patch_arc()` | `patch_arc_with_feedback()` | 3-전략 앙상블 |
| Stage 3 | Blueprint | `_inplace_patch_blueprint()` | (앙상블 폴백) | 3-phase 앙상블 |
| Stage 4 | 원고 (Manuscript) | `inplace_patch()` + Structural variant | `patch_with_feedback()` | `regenerate_with_feedback()` |

---

## 6. LLM 프롬프트 — 실제로 어떤 지시를 내리는가

### 6.1. 원고 패치 프롬프트 (chief_writer.yaml)

```
[패치 모드: 원본 보존 + 지적사항만 수정]

당신은 웹소설 교정 전문가입니다.
아래 원본 원고를 기반으로, Director의 피드백에서 지적된 부분만 최소한으로 수정하세요.

## 패치 규칙
1. 원고의 전체 구조, 문체, 장점을 보존
2. Director가 지적한 모순·연속성·설정 오류만 정확히 수정
3. 수정하지 않는 부분은 원문 그대로 유지 — 원문의 문장을 생략하거나 요약하지 마세요
4. 글자 수는 원본 대비 ±10% 이내로 유지
5. 캐릭터 성격, 관계, 세계관 설정은 변경하지 마세요
6. 요약성 대폭 축소 금지: 수정 대상이 아닌 부분을 요약하거나 통째로 압축하지 마세요

## 원본 원고
{original_manuscript}

전면 재작성하지 마세요. 지적된 부분만 고치세요.
```

### 6.2. 구조적 패치 프롬프트 (scene 단위)

```
[Structural InPlace Patch: target scene blocks only]

당신은 원고 전체를 다시 쓰는 것이 아니라,
지정된 scene block만 수정하는 편집자입니다.
target scene 이외의 블록은 시스템이 그대로 유지하므로 절대 다시 작성하지 마세요.

## 출력 형식
{
  "patched_blocks": { "scene_id": "패치된 장면 텍스트" },
  "patch_state_updates": {}
}
```

### 6.3. Arc 패치 프롬프트

```
[패치 모드: Arc 원본 보존 + 지적사항만 수정]

## 패치 규칙
1. Arc의 전체 구조(에피소드 배분, 서사 흐름, 갈등 구조)를 보존
2. Director가 지적한 문제점만 정확히 수정
3. 수정하지 않는 부분은 원본 그대로 유지
4. NPC 설정, 세계관, 관계도는 절대 변경 금지

전면 재설계하지 마세요. 지적된 부분만 고치세요.
```

---

## 7. 상위 모델(Opus/Codex)의 부분 수정 vs 글도비의 부분 수정

### 7.1. 상위 모델이 사용하는 부분 수정 로직의 이름

| 모델/도구 | 기능명 | 메커니즘 |
|----------|--------|---------|
| **Claude Code (Opus 4.6)** | **Edit tool** | 프로그래밍적 정확 문자열 치환 (`old_string → new_string`) |
| **Claude Code (Opus 4.6)** | **replace_all** | Edit tool의 전체 치환 모드 (파일 내 모든 매치 교체) |
| **Codex 5.4 (OpenAI)** | **Apply** / **Patch** | diff 기반 프로그래밍적 치환 |
| **Cursor** | **Apply** | diff 생성 후 프로그래밍적 적용 |
| **GitHub Copilot** | **Inline Edit** | 선택 영역에 대해 LLM 재생성 (하이브리드) |

이들의 공통점: **수정 대상 문자열을 정확히 식별한 후, 프로그래밍적으로 치환**한다.
LLM은 "어디를 어떻게 바꿀지 결정"하는 데만 사용되고, 실제 교체는 deterministic하다.

### 7.2. 글도비와의 차이

```
┌────────────────────────────────────────────────────────────┐
│            상위 모델의 Edit/Apply 패턴                       │
│                                                            │
│  사용자: "주혁을 강혁으로 바꿔"                               │
│    │                                                       │
│    ▼                                                       │
│  LLM: old_string="주혁이 열을 내며"                          │
│       new_string="강혁이 열을 내며"  (결정만 함)              │
│    │                                                       │
│    ▼                                                       │
│  시스템: 파일에서 old_string 찾아서 new_string으로 교체       │
│         (프로그래밍적, 나머지 텍스트 1byte도 안 건드림)        │
│                                                            │
│  결과: 100% 정확, 0% 부작용, 원본 완전 보존                  │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│            글도비의 inplace_patch 패턴                       │
│                                                            │
│  Director: "주혁→강혁 이름 수정 필요" (fix_pack 발행)        │
│    │                                                       │
│    ▼                                                       │
│  시스템: LLM에게 원본 5000자 전체 + fix_pack 전송            │
│    │                                                       │
│    ▼                                                       │
│  LLM: 원본을 읽고, 지적 부분을 수정하여                       │
│       전문을 다시 출력 (재생성)                               │
│    │                                                       │
│    ▼                                                       │
│  시스템: 변경량 검증 (≤30%, ≥70% 보존)                       │
│         → 통과 시 패치된 원고 채택                            │
│                                                            │
│  결과: 높은 확률로 정확하나, LLM이 의도치 않은 변경 가능       │
│        (문체 미묘한 변화, 불필요한 추가/삭제 등)               │
└────────────────────────────────────────────────────────────┘
```

---

## 8. 왜 프로그래밍적 치환을 안 쓰는가?

글도비의 수정 대상은 **코드가 아니라 소설 원고**이다.

| 차원 | 코드 (Opus/Codex 대상) | 소설 원고 (글도비 대상) |
|------|----------------------|---------------------|
| 수정 단위 | 정확한 문자열 (함수명, 변수명) | 서사적 맥락 (대화 흐름, 묘사 톤) |
| 수정 영향 범위 | 해당 토큰만 | 전후 문맥에 영향 (조사 변경, 호칭 변경 등) |
| "장소가 틀렸다" 수정 | `location = "A"` → `location = "B"` | 장소 묘사 문단 전체 재작성 필요 |
| "시간이 틀렸다" 수정 | timestamp 값 교체 | 시간대 관련 묘사/대화/심리 다수 수정 |
| 변경 후 정합성 | 컴파일러/타입체커로 검증 | LLM Director가 재감사 필요 |

**이름 하나 바꾸는 것**은 `str.replace`로 가능하지만,
**"장소가 틀렸다"**는 장소 묘사, 이동 경로, 주변 환경 언급 등을 모두 바꿔야 하므로
LLM이 문맥을 이해하고 재작성해야 한다.

글도비는 두 경우를 구분하지 않고 **모두 LLM 기반 패치로 통일**한 설계이다.

---

## 9. Structural InPlace Patch — 가장 "진짜 inplace"에 가까운 메커니즘

`chief_writer.py` L1424-1562의 `_attempt_structural_inplace_patch()`는 유일하게 **하이브리드 방식**을 사용한다:

```
원고 전체
├── Scene 1 (건드리지 않음) ──→ 프로그래밍적으로 원본 유지
├── Scene 2 (타겟) ──────────→ LLM이 이 장면만 재생성
├── Scene 3 (건드리지 않음) ──→ 프로그래밍적으로 원본 유지
└── Scene 4 (타겟) ──────────→ LLM이 이 장면만 재생성
```

- LLM에게는 **타겟 장면 + 인접 boundary context만** 전송
- 비타겟 장면은 **시스템이 프로그래밍적으로 원본 유지**
- 이것이 "주혁→강혁" 수준의 수정에 가장 적합한 메커니즘
- 단, 타겟 장면 내부는 여전히 LLM이 재생성

---

## 10. 정리: 메커니즘 이름 총정리

| 이름 | 파일 | 성격 | LLM 호출 | 원본 보존 방식 |
|------|------|------|---------|-------------|
| **inplace_patch** | chief_writer.py L1792 | LLM 기반 최소 변경 | 1회 | LLM에게 "보존하라" 지시 (보장 아님) |
| **structural_inplace_patch** | chief_writer.py L1424 | 하이브리드 (장면 단위) | 1회 | 비타겟 장면은 프로그래밍적 보존 |
| **patch_with_feedback** | chief_writer.py L1955 | LLM 기반 제한적 재생성 | 1회 | 이전 전략 재사용 + 보존 지시 |
| **patch_arc_with_feedback** | four_phase_arc_generator.py L690 | LLM 기반 Arc 패치 | 1회 | Arc JSON 필드 단위 병합 |
| **_inplace_patch_arc** | four_phase_arc_generator.py L619 | LLM 기반 Arc 최소 변경 | 1회 | 누락 필드 원본에서 병합 |
| **_inplace_patch_blueprint** | three_phase_blueprint_generator.py | LLM 기반 BP 최소 변경 | 1회 | 누락 필드 원본에서 병합 |
| **전면 재생성** | chief_writer.py generate_ensemble | 3-전략 앙상블 | 3회 | 없음 (완전 새로 생성) |

---

## 11. 개선 가능성 제언

현재 시스템에 **프로그래밍적 문자열 치환 레이어**가 없다. 다음과 같은 경우에는 LLM을 거치지 않는 deterministic 패치가 더 효율적일 수 있다:

| 수정 유형 | 현재 방식 | 가능한 개선 |
|----------|---------|-----------|
| 이름 치환 (주혁→강혁) | LLM 전체 재생성 | `str.replace()` + 조사 보정 |
| 고유명사 수정 (천마신교→천마혈교) | LLM 전체 재생성 | 정규식 치환 |
| 숫자 수정 (3일→5일) | LLM 전체 재생성 | 정규식 치환 |
| 금지어 제거 | LLM 전체 재생성 | 정규식 삭제 + 조사 보정 |

단, **한국어 조사 변환** (이/가, 은/는, 을/를)이 필요하므로 완전한 deterministic 치환은 조사 처리 로직이 추가로 필요하다.

---

## 부록 A: Verdict 4종 정리

| Verdict | 의미 | 후속 액션 |
|---------|------|---------|
| **PASS** | 무조건 합격 | 다음 에피소드로 진행 |
| **PASS_WITH_FIX** | 조건부 합격 (국소 수정 필요) | inplace_patch 루프 (최대 3회) |
| **REJECT** | 불합격 | 점수 기반 라우팅 → inplace/patch/전면 재생성 |
| **CONDITIONAL_PASS** | 적응형 판정 | 에피소드 위치·유형·재시도 횟수에 따라 PASS 또는 REJECT으로 전환 |

## 부록 B: Firewall에 의한 자동 PASS_WITH_FIX 전환

Director에는 **fixable contradiction firewall**이 있어, 특정 유형의 모순이 1~3건 발견되면 자동으로 PASS_WITH_FIX를 발행한다:

```python
_FIXABLE_FIREWALL_TYPE_TOKENS = {
    "고유명사", "이름", "이름불일치",  # 이름 관련
    "직급", "직함",                  # 직급 관련
    "위치명", "지명",                # 장소 관련
    "금지표현",                      # 금기어 관련
}
```

즉 "이름이 틀렸다" 수준의 문제는 시스템이 자동으로 "REJECT하지 말고 PASS_WITH_FIX로 패치하라"고 판단한다.

---

# Part 2: 놓친 근본 질문들 — Deterministic Applicator 부재의 파급

> **핵심 발견**: DEA(Deterministic Edit Applicator) 레이어의 부재는 빙산의 일각이다.
> 20만 줄 코드베이스 전체에 걸쳐 **"이걸 왜 LLM이 하고 있지?"**라는 질문이 한 번도 제기되지 않은 지점이 다수 존재한다.

---

## 12. 놓친 근본 질문 목록

### Q-0. "수정 실행을 왜 LLM이 하고 있지?" (DEA 부재)

이미 Part 1에서 다룸. Director가 fix_pack으로 **"뭘 바꿀지"를 이미 알고 있는데**, 그걸 받아서 프로그래밍적으로 적용하는 레이어가 없다.

- **현재**: Director(결정) → ChiefWriter(LLM으로 전문 재생성)
- **있어야 할 것**: Director(결정) → DEA(프로그래밍 적용) → 실패 시에만 LLM 폴백
- **영향**: 모든 PASS_WITH_FIX 에피소드에서 불필요한 전문 재생성 + 미세 오염 리스크

---

### Q-1. "피드백이 왜 자연어로 전달되지? 기계가 실행할 수 있는 형태여야 하지 않나?"

**현재 상태**: Director가 REJECT/PASS_WITH_FIX를 발행할 때, 피드백의 상당 부분이 자연어 문자열이다.

```python
# stage4_interview_round.py L5102-5165
fix_feedback = ""
fix_feedback += "[Fix Pack]\n"           # 구조화됨 ✓
fix_feedback += "[핵심 수정 지시]\n"       # action_items: 자연어 문자열 리스트 ✗
fix_feedback += "[Director 자유 리뷰]\n"   # open_review: 완전 비구조 ✗
fix_feedback += "[보조 이슈]\n"            # 자연어 ✗
```

- `fix_pack`의 `patch_targets`: `["Scene 3", "Scene 5"]` — 위치 정보 없음 (몇 번째 줄? 어떤 문장?)
- `must_fix`: `["Increase tension in final conflict"]` — 명령문 (실행 불가)
- `success_condition`: `"NPC motivations clear and consistent"` — 텍스트일 뿐, 검증 코드 아님

**놓친 질문**: *"Director가 문제를 발견했으면, 그 위치와 수정 방법을 기계가 실행할 수 있는 형태로 출력해야 하지 않나?"*

**있어야 할 것**:
```python
# 기계 실행 가능한 fix_pack
{
    "edits": [
        {"type": "replace", "location": {"paragraph": 3, "offset": 12, "length": 2},
         "old": "주혁", "new": "강혁"},
        {"type": "rewrite", "location": {"scene": 2, "paragraph": 5},
         "instruction": "시간대를 3일 후로 변경", "context_needed": true}
    ],
    "success_checks": [
        {"type": "string_absent", "target": "주혁"},
        {"type": "string_present", "target": "강혁", "min_count": 3}
    ]
}
```

`type: replace`는 DEA가 처리. `type: rewrite`만 LLM 폴백. `success_checks`는 Python이 검증.

---

### Q-2. "Python이 이미 찾은 문제를 왜 LLM이 다시 찾고 있지?"

**현재 상태**: 검증 파이프라인에 이중 처리가 존재한다.

```
Python ArcDraftValidator.validate()
  → 10+ 규칙 검사 (중복, 위치 연속성, 부상 상태, 타임라인)
  → 구조화된 warnings 출력
       │
       ▼
ConsensusValidator (LLM 3회 호출)
  → 동일한 Arc + Python warnings를 받아서
  → LLM이 같은 내용을 다시 읽고 판단
```

Python이 "에피소드 3과 5에서 위치가 불연속"이라고 이미 발견했는데, LLM 3개가 같은 Arc를 다시 읽으며 같은 문제를 재발견하고 있다.

**놓친 질문**: *"Python이 구조적으로 발견한 문제를 LLM이 재검증할 필요가 있나? Python 결과를 신뢰하고, LLM은 Python이 못 찾는 서사적 판단만 하면 안 되나?"*

**토큰 낭비**: Arc당 ~4,500-6,000 토큰 (LLM 3회 × 1,500-2,000)

---

### Q-3. "LLM이 자기가 만든 구조화된 출력을 왜 다시 LLM으로 파싱하지?"

**현재 상태** (`state_locked_arc_generator.py` L438-485):

```
1단계: LLM이 에피소드 생성 → 출력에 "【화 종료 상태】" 마커 포함
   - 위치: 천마혈교 본당
   - 내공: 상승
   - 부상: 없음

2단계: 다른 LLM 호출로 위 텍스트에서 JSON 추출
   → {"end_location": "천마혈교 본당", "end_energy": "상승", ...}
```

LLM이 자기가 쓴 구조화된 섹션을 다시 LLM으로 파싱하고 있다. 정규식 한 줄이면 끝난다:

```python
import re
pattern = r"- 위치:\s*(.+)"
match = re.search(pattern, episode_text)
end_location = match.group(1).strip()  # "천마혈교 본당"
```

**놓친 질문**: *"LLM 출력에 이미 마커가 있으면, 파싱을 왜 LLM으로 하지?"*

---

### Q-4. "고유명사 검증을 왜 LLM이 하지? Trie 매칭이면 되지 않나?"

**현재 상태** (`director_continuity.py` L46-198):

```
Entity Registry (JSON)
  → 이름, 별칭, 카테고리 직렬화
  → LLM에게 15,000자 원고 + Registry 전달
  → "불일치 찾아줘"
  → LLM이 자연어로 불일치 목록 반환
  → Python이 후처리 (약어 필터, 별칭 매칭)
```

이미 Python 후처리에서 약어/별칭 필터를 하고 있다(L138-147). LLM이 하는 일의 상당 부분이 "Registry에 있는 이름이 원고에 있는지 확인"인데, 이건 문자열 매칭이다.

**놓친 질문**: *"Registry 기반 고유명사 매칭은 Trie/정규식으로 100% 정확하게 할 수 있지 않나? LLM은 '맥락상 이 이름이 다른 인물을 가리키는지' 같은 판단만 하면 되지 않나?"*

**토큰 낭비**: 에피소드당 ~2,000-3,000 토큰

---

### Q-5. "Advisory 8개가 왜 각각 원고를 따로 받지? 공유할 수 있지 않나?"

**현재 상태** (`stage4_interview_round.py` L4519):

```
ThreadPoolExecutor(max_workers=9)
  ├── TruthGate      → 원고 5K + 컨텍스트 20K = 25K
  ├── NpcDrift        → 원고 5K + 컨텍스트 20K = 25K
  ├── Flashback       → 원고 5K + 컨텍스트 20K = 25K
  ├── InfoParadox     → 원고 5K + 컨텍스트 20K = 25K
  ├── RelDrift        → 원고 5K + 컨텍스트 20K = 25K
  ├── LongTermRep     → 원고 5K + 컨텍스트 20K = 25K
  ├── StyleSignal     → 원고 5K + 컨텍스트 20K = 25K
  ├── NumericDrift    → (Python only)
  └── NumericConsist  → (Python only)

7개 LLM Advisory × 3후보 = 21회 독립 전송
합계: 21 × 25K = 525K chars (~131,000 토큰)
```

7개 Advisory가 공유하는 컨텍스트(세계 상태, NPC 레지스트리, 이전 에피소드)는 거의 동일한데, 각각 독립 전송한다. Gemini Context Caching의 50,000자 최소 요건을 Advisory 개별로는 못 채워서(20K < 50K) 캐싱도 안 된다.

**놓친 질문**: *"Advisory 공통 컨텍스트를 하나의 캐시로 묶을 수 없나? 또는 Advisory를 단일 LLM 호출로 합칠 수 없나?"*

**가능한 대안**:
- Advisory 7개의 질문을 하나의 프롬프트에 모아서 LLM 1회 호출 (배치)
- 또는 공통 컨텍스트만 별도 캐시 → 7개 Advisory가 공유 참조

---

### Q-6. "success_condition이 왜 텍스트지? 실행 가능한 검증 코드여야 하지 않나?"

**현재 상태**:

```python
fix_pack["success_condition"] = "NPC motivations clear and internally consistent"
```

이 문자열은 어디에서도 실행되지 않는다. Director 재감사 때 LLM이 "이 조건이 충족됐나?"를 다시 판단한다.

**놓친 질문**: *"패치 성공 여부를 LLM 재감사에만 의존하면, 같은 LLM이 같은 실수를 반복할 수 있지 않나?"*

**있어야 할 것**:
```python
success_checks = [
    {"type": "entity_match", "registry": "npc_registry", "target_ms": patched},
    {"type": "string_absent", "pattern": "주혁"},
    {"type": "change_ratio", "max": 0.05},  # entity_ref 수정이면 5% 이내
]
# Python이 즉시 검증 → 통과 시에만 Director 재감사
```

---

### Q-7. "점수가 같을 때 왜 '첫 번째 후보'를 고르지? 명시적 기준이 없다"

**현재 상태** (`director_ensemble.py`):

```python
# LLM 파싱 실패 시 폴백
logging.warning("[TF-47] 폴백 — 첫 번째 후보 선택 (Python)")
return candidates[0]  # 항상 첫 번째
```

첫 번째 후보는 성공 편향이 가장 높은 전략의 산출물이므로, 폴백이 특정 전략에 무의식적으로 편향된다.

**놓친 질문**: *"앙상블 선택 실패 시 폴백 기준이 '순서'인 게 맞나? Python warning 수, 길이 적합도, 변경량 등 결정론적 기준으로 해야 하지 않나?"*

---

## 13. 근본 원인 분석: 왜 이 질문들이 안 나왔나

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│    시스템 설계의 암묵적 전제:                                    │
│                                                              │
│    "소설은 코드가 아니다.                                       │
│     따라서 모든 처리는 LLM이 해야 한다."                         │
│                                                              │
│    이 전제가 한 번도 도전받지 않았다.                              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

이 전제 때문에:
- **이름 치환**도 LLM이 함 (Q-0: DEA 부재)
- **구조화된 출력 파싱**도 LLM이 함 (Q-3)
- **패턴 매칭**도 LLM이 함 (Q-4)
- **검증 결과 전달**도 자연어로 함 (Q-1)
- **성공 판정**도 LLM이 함 (Q-6)

실제로는 소설 생성 파이프라인에도 **결정론적으로 처리 가능한 작업**이 다수 존재한다:

| 작업 | LLM이 필요한가? | 결정론적 대안 |
|------|:---:|-----------|
| 이름/고유명사 치환 | **아니오** | str.replace + 조사 보정 |
| 고유명사 불일치 탐지 | **아니오** | Trie/정규식 매칭 |
| 구조화된 출력 파싱 | **아니오** | 정규식/JSON 파서 |
| 검증 결과의 재검증 | **아니오** | Python 결과 신뢰 |
| 패치 성공 여부 확인 (이름류) | **아니오** | 문자열 존재/부재 검사 |
| 점수 기반 후보 선택 | **아니오** | 가중 점수 비교 |
| 장소 묘사 변경 | **예** | 문맥 이해 필요 |
| 캐릭터 동기 수정 | **예** | 서사적 판단 필요 |
| 새로운 장면 생성 | **예** | 창작 영역 |
| 문체 일관성 판단 | **예** | 주관적 판단 필요 |

**약 40-50%의 패치/검증 작업이 LLM 없이 처리 가능하다.**

---

## 14. 토큰 영향 추정

### 에피소드 1회 처리 시 원고 텍스트 LLM 전송 횟수

```
정상 통과 (1 Pass):
  ChiefWriter 생성: 3회 (3전략 앙상블)
  Director 선택:   1회
  Advisory 체인:   21회 (7 LLM × 3후보)
  ─────────────
  합계: 25회 × 5,000자 = 125,000자 (~31,000 토큰)

PASS_WITH_FIX (1회 패치):
  위 25회 + 패치 생성 1회 + 재감사 Advisory 21회 + Director 재감사 1회
  ─────────────
  합계: 48회 × 5,000자 = 240,000자 (~60,000 토큰)

3회 리트라이:
  합계: ~100회 × 5,000자 = 500,000자 (~125,000 토큰)
```

### DEA + 결정론적 레이어 도입 시 절감 추정

| 개선 항목 | 현재 토큰 | 절감 후 | 절감률 |
|----------|---------|--------|-------|
| Q-0: DEA (entity_ref 패치) | ~5,000/회 | 0 | **100%** |
| Q-2: Python 결과 재검증 제거 | ~6,000/Arc | ~2,000 | **67%** |
| Q-3: 구조화 출력 정규식 파싱 | ~500/에피 | 0 | **100%** |
| Q-4: 고유명사 Trie 매칭 | ~3,000/에피 | 0 | **100%** |
| Q-5: Advisory 컨텍스트 공유 | ~131,000/에피 | ~40,000 | **69%** |
| Q-6: 성공 검증 Python화 | ~5,000/패치 | ~1,000 | **80%** |

**보수적 추정: 에피소드당 30-40% 토큰 절감 가능**

---

## 15. 우선순위 제안

```
즉시 도입 가능 (코드 변경 최소):
──────────────────────────────
 1. Q-0: DEA 레이어 — entity_ref 타입 fix_pack → 문자열 치환
 2. Q-3: 구조화 출력 정규식 파싱 — 【화 종료 상태】 마커 → regex
 3. Q-6: success_checks Python 검증 — string_absent/present 체크

중기 도입 (설계 변경 필요):
──────────────────────────────
 4. Q-4: 고유명사 Trie 매칭 모듈 — Entity Registry → Trie 빌드
 5. Q-1: fix_pack 구조화 강화 — edit spec 형태로 전환
 6. Q-2: Python 검증 결과 Director 직접 주입 — LLM 재검증 skip

장기 도입 (아키텍처 변경):
──────────────────────────────
 7. Q-5: Advisory 배치 호출 / 컨텍스트 캐시 공유
 8. 전체 파이프라인 "LLM 필요성 감사" — 각 ask() 호출에 대해
    "이 호출이 정말 LLM이 필요한가?" 태그 부착

```

---

# Part 3: 레이어와 무기 — 파이프라인 구조 개편 + LLM 보강 도구 전수조사

> **핵심 구분**:
> - **레이어** = LLM을 거치지 않는 파이프라인 구간. LLM **대신** 처리한다.
> - **무기** = LLM이 호출될 때 같이 쥐여주는 도구. LLM이 **더 잘** 처리하게 돕는다.
>
> 비유: 레이어는 "사자가 오기 전에 함정으로 잡는 것", 무기는 "원시인한테 창을 쥐여주는 것".

---

## 16. 전체 분류 체계

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  📐 레이어 (Layer) — LLM을 안 부르거나, 최소한만 부른다          │
│  ├── L-1.  DEA (Deterministic Edit Applicator) — 수정 레이어  │
│  ├── L-1A. SurgicalRewriteLayer — 수술적 재작성 (하이브리드)   │
│  │         (비타겟 문단: 코드 보존 / 타겟 문단만: LLM 재작성)   │
│  ├── L-2.  RegexParser — 구조화 출력 파싱 레이어               │
│  ├── L-3.  EntityMatcher — 고유명사 매칭 레이어                │
│  ├── L-4.  KoreanParticleEngine — 조사 보정 레이어 (L-1 동반) │
│  ├── L-5.  EarlyReturnGate — Advisory 조기반환 레이어          │
│  └── L-6.  DeterministicScorer — 폴백 선택 레이어             │
│                                                              │
│  ⚔️ 무기 (Weapon) — LLM에게 쥐여준다                          │
│  ├── W-1. FactDatabase — "이거 사실이야?" 즉시 답변 (사실의 창) │
│  ├── W-2. TemporalValidator — "순서 맞아?" 즉시 답변 (시간의 방패)│
│  ├── W-3. SceneContextFilter — 필요한 것만 전달 (시야 확보)    │
│  ├── W-4. ContradictionIndex — 30화→3KB 팩트표 (지도)         │
│  ├── W-5. PatchVerifier — "잘 고쳤나?" 즉시 확인 (거울)        │
│  ├── W-6. AdvisoryBatcher — 컨텍스트 공유 (병참)              │
│  └── W-7. StructuredFeedbackCompiler — 피드백 구조화 (통신기)  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**레이어 vs 무기 판별 기준**:

| | 레이어 | 무기 |
|--|--------|------|
| LLM 호출 | **안 함** | LLM이 **사용함** |
| 역할 | LLM을 대체 | LLM을 보강 |
| 실패 시 | LLM 폴백 | LLM 판단력 저하 |
| 예시 | "주혁→강혁" 치환 (LLM 불필요) | "이 NPC는 23화에 사망" 사실 제공 (LLM이 참조) |

---

# Part 3-A: 레이어 — LLM을 거치지 않는 파이프라인 구간

---

## 17. L-1. DEA (Deterministic Edit Applicator) — 수정 레이어

**대체 대상**: `chief_writer.inplace_patch()` 중 entity_ref 타입 수정 전체

**현재**: Director가 `fix_pack = {"must_fix": ["주혁→강혁"]}` 발행 → ChiefWriter가 5,000자 전체 재생성
**레이어 장착 후**: fix_pack 파싱 → `str.replace("주혁", "강혁")` → 조사 보정(L-4) → 완료. **LLM을 안 부른다.**

```python
class DeterministicEditApplicator:
    """entity_ref / local_phrase 타입 fix를 LLM 없이 적용"""

    def apply(self, manuscript: str, fix_pack: dict) -> str | None:
        """성공 시 패치된 원고, 실패(복잡한 수정) 시 None → LLM 폴백"""
        edits = self._parse_fix_pack(fix_pack)
        result = manuscript
        for edit in edits:
            if edit["type"] == "replace":
                result = result.replace(edit["old"], edit["new"])
                result = self._fix_particles(result, edit)  # L-4 조사 보정
            elif edit["type"] == "delete":
                result = result.replace(edit["target"], "")
            else:
                return None  # 복잡한 수정 → LLM 폴백
        return result
```

**파이프라인 삽입 위치**:
```
기존:  Director(fix_pack) → ChiefWriter.inplace_patch(LLM) → 재감사(LLM)
변경:  Director(fix_pack) → L-1 DEA(Python) → 성공? → 완료
                                             → 실패? → ChiefWriter.inplace_patch(LLM)
```

| 항목 | 수치 |
|------|------|
| 적용 가능 fix 유형 | entity_ref(이름/지명/직급), 금지어 삭제, 숫자 수정 |
| 토큰 절감 | 5,000/회 → 0 (100%) |
| 오염 리스크 | 0% (비수정 영역 물리적 불변) |
| 구현 난이도 | 낮음 (50줄 이내) |

---

## 17-A. L-1A. SurgicalRewriteLayer — 수술적 재작성 레이어

**성격**: L-1(DEA)과 현재 inplace_patch(전문 LLM 재생성) 사이의 **하이브리드 레이어**.
코드가 원고를 문단으로 분리 → 타겟 문단만 LLM에 전송 → 결과를 코드가 다시 꿰맴.
**비타겟 문단은 LLM을 물리적으로 통과하지 않으므로 오염 0%.**

### 왜 필요한가

```
L-1 DEA가 처리 가능한 것:
  "주혁" → "강혁"  (문자열 치환, LLM 불필요)

L-1 DEA가 처리 불가능한 것:
  "주혁이 열을 내며 서재에서 대화를 이어가는 때."
  → 장소가 '서재'가 아니라 '객잔'이어야 함
  → 문장 자체를 재작성해야 함 (LLM 필요)
  → 하지만 이 문장 전후의 4,900자는 건드릴 필요 없음

현재 inplace_patch가 하는 것:
  5,000자 전체를 LLM에 넘김 → 전체 재생성 → 비타겟 영역 오염 가능
```

### 스펙트럼 상의 위치

```
          오염 0%                                오염 가능
          LLM 0회                                LLM이 전문 재생성
    ┌─────────┬─────────────────┬───────────────────┐
    │ L-1 DEA │ L-1A Surgical   │ 현재 inplace_patch │
    │ 문자열   │ Rewrite Layer   │ (전문 LLM 통과)    │
    │ 치환    │                 │                    │
    │         │ 비타겟: 코드 보존 │ 비타겟: LLM 통과   │
    │         │ 타겟: LLM 재작성 │ 타겟: LLM 재작성   │
    └─────────┴─────────────────┴───────────────────┘
```

### 구현

```python
class SurgicalRewriteLayer:
    """문단 단위 수술적 재작성 — 타겟 문단만 LLM, 나머지 코드 보존"""

    def apply(self, manuscript: str, fix_pack: dict,
              llm_ask: Callable) -> str | None:
        """
        1. 원고를 문단으로 분리
        2. fix_pack에서 타겟 문단 식별
        3. 타겟 문단만 LLM에 전송 (전후 boundary context 포함)
        4. LLM 결과를 원본에 splice
        5. 비타겟 문단은 1바이트도 변경 없음
        """
        paragraphs = self._split_paragraphs(manuscript)
        targets = self._identify_targets(paragraphs, fix_pack)

        if not targets:
            return None  # 타겟 식별 실패 → 기존 inplace_patch 폴백

        result_paragraphs = list(paragraphs)  # 원본 복사

        for idx in targets:
            # boundary context: 앞뒤 1-2문단 (LLM이 연결감 유지하도록)
            before = paragraphs[max(0, idx-1):idx]
            after = paragraphs[idx+1:min(len(paragraphs), idx+2)]
            target = paragraphs[idx]

            prompt = self._build_rewrite_prompt(
                target_paragraph=target,
                before_context=before,
                after_context=after,
                fix_instruction=fix_pack["must_fix"],
            )

            # LLM에게는 타겟 1문단 + boundary 2문단만 전송
            # = ~200-500자 (vs 전체 5,000자)
            rewritten = llm_ask(prompt, temperature=0.3)

            if rewritten and len(rewritten) > 20:
                result_paragraphs[idx] = rewritten

        return "\n\n".join(result_paragraphs)

    def _split_paragraphs(self, text: str) -> list[str]:
        """빈 줄 기준 문단 분리"""
        return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    def _identify_targets(self, paragraphs: list[str],
                           fix_pack: dict) -> list[int]:
        """fix_pack의 patch_targets/must_fix에서 타겟 문단 인덱스 식별"""
        targets = []
        for i, para in enumerate(paragraphs):
            for target_hint in fix_pack.get("patch_targets", []):
                # 힌트가 문단 내용에 포함되면 타겟
                if target_hint in para:
                    targets.append(i)
                    break
        return targets

    def _build_rewrite_prompt(self, *, target_paragraph, before_context,
                               after_context, fix_instruction) -> str:
        before_text = "\n".join(before_context) if before_context else "(없음)"
        after_text = "\n".join(after_context) if after_context else "(없음)"
        return (
            f"[문단 수술 모드]\n\n"
            f"아래 '대상 문단'만 수정하세요. 전후 문맥은 참고용입니다.\n\n"
            f"## 수정 지시\n{fix_instruction}\n\n"
            f"## 앞 문단 (참고, 수정 불가)\n{before_text}\n\n"
            f"## 대상 문단 (이것만 수정)\n{target_paragraph}\n\n"
            f"## 뒤 문단 (참고, 수정 불가)\n{after_text}\n\n"
            f"수정된 문단만 출력하세요. 앞뒤 문단을 포함하지 마세요."
        )
```

### L-1 vs L-1A vs 현재 inplace_patch 비교

| | L-1 DEA | **L-1A Surgical** | 현재 inplace_patch |
|--|---------|:-----------------:|-------------------|
| LLM 호출 | 0회 | **타겟 문단 수만큼** (보통 1-2회) | 1회 (전문) |
| LLM 입력 크기 | 0 | **200-500자/문단** | 5,000자 전체 |
| 비타겟 오염 | 0% | **0%** (코드가 보존) | 가능 (LLM 통과) |
| 처리 가능 수정 | 문자열 치환만 | **문장/문단 재작성** | 모든 수정 |
| 예시 | 이름 교체 | **장소 묘사 변경, 대사 톤 변경** | 구조적 재편 |

### 적용 가능한 fix_pack target_kind

| target_kind | L-1 DEA | L-1A Surgical | 현재 inplace_patch |
|-------------|:-------:|:-------------:|:-----------------:|
| entity_ref (이름/지명) | **최적** | 가능 | 과잉 |
| local_phrase (특정 표현) | 가능 | **최적** | 과잉 |
| local_sentence (문장 교체) | 불가 | **최적** | 가능 |
| scene_model (장면 재구성) | 불가 | 제한적 | **최적** |

### 라우팅 결정 트리 (L-1A 포함)

```
Director fix_pack 수신
    │
    ├── target_kind == entity_ref AND "→" 패턴?
    │     → L-1 DEA (문자열 치환, LLM 0회)
    │
    ├── target_kind in {local_phrase, local_sentence}?
    │     → L-1A Surgical Rewrite (타겟 문단만 LLM)
    │       │
    │       ├── 타겟 문단 식별 성공 → 문단 단위 LLM 재작성
    │       └── 타겟 문단 식별 실패 → 폴백 ↓
    │
    ├── target_kind == scene_model?
    │     → 기존 structural_inplace_patch (장면 단위 LLM)
    │
    └── 그 외 / 복잡한 수정
          → 기존 inplace_patch (전문 LLM 재생성)
```

### 토큰 절감

```
현재 (local_sentence 수정 시):
  LLM 입력: 5,000자 전체 + fix_pack + 스타일 가이드 = ~8,000자
  LLM 출력: 5,000자 전체 재생성
  합계: ~13,000자 (~3,250 토큰)

L-1A Surgical (같은 수정):
  LLM 입력: 타겟 200자 + boundary 400자 + 지시 200자 = ~800자
  LLM 출력: 타겟 200자 재작성
  합계: ~1,000자 (~250 토큰)

절감: 3,250 → 250 = 92% 절감
```

| 항목 | 수치 |
|------|------|
| 적용 범위 | local_phrase, local_sentence 타입 fix (PASS_WITH_FIX의 ~40%) |
| 토큰 절감 | 패치당 ~3,000 토큰 → ~250 토큰 (**92%**) |
| 비타겟 오염 | **0%** (코드가 물리적으로 보존) |
| LLM 품질 | 향상 (200자 집중 > 5,000자 속 수정 지시) |
| 구현 난이도 | 중간 (문단 분리 + 타겟 식별 + splice 로직) |

### 현재 structural_inplace_patch와의 관계

```
structural_inplace_patch (기존):
  단위: 장면(scene) — 보통 1,000-2,000자
  장면 내부: LLM이 전체 재생성

L-1A Surgical Rewrite (신규):
  단위: 문단(paragraph) — 보통 100-300자
  문단 내부: LLM이 전체 재생성

관계: L-1A는 structural_inplace_patch의 세분화 버전.
     scene → paragraph로 격리 단위를 축소.
```

---

## 18. L-2. RegexParser — 구조화 출력 파싱 레이어

**대체 대상**: `state_locked_arc_generator.py` L455 — LLM이 자기 출력을 다시 LLM으로 파싱

**현재**: LLM 생성 `【화 종료 상태】` → 또 다른 LLM 호출로 JSON 추출
**레이어 장착 후**: 정규식으로 즉시 파싱. **LLM을 안 부른다.**

```python
class StructuredOutputParser:
    """LLM이 생성한 마커 기반 섹션을 정규식으로 즉시 파싱"""

    PATTERNS = {
        "end_location": r"-\s*위치:\s*(.+)",
        "end_energy":   r"-\s*내공:\s*(.+)",
        "end_injury":   r"-\s*부상:\s*(.+)",
        "items_acquired": r"-\s*획득:\s*(.+)",
        "items_consumed": r"-\s*소모:\s*(.+)",
    }

    def parse_episode_state(self, text: str) -> dict | None:
        marker = "【화 종료 상태】"
        idx = text.find(marker)
        if idx == -1:
            return None  # 마커 없음 → LLM 폴백
        section = text[idx:]
        result = {}
        for key, pattern in self.PATTERNS.items():
            m = re.search(pattern, section)
            if m:
                result[key] = m.group(1).strip()
        return result if result else None
```

| 항목 | 수치 |
|------|------|
| 적용 대상 | state_locked_arc_generator L455, state_extractor L253/L807 |
| 토큰 절감 | ~500-1,500/에피소드 (100%) |
| 정확도 | 마커 존재 시 100%, 미존재 시 LLM 폴백 |
| 구현 난이도 | 매우 낮음 (20줄) |

---

## 19. L-3. EntityMatcher — 고유명사 매칭 레이어

**대체 대상**: `director_continuity.py` L122 — LLM이 15,000자 원고에서 이름 불일치 탐색

**현재**: Entity Registry + 원고 전체를 LLM에 전달 → "불일치 찾아줘"
**레이어 장착 후**: Registry → Trie 빌드 → 원고 스캔 → 불일치 즉시 탐지.
이름/직급/지명 매칭은 **LLM을 안 부른다.** 맥락적 판단(동명이인 구별)만 LLM 폴백.

```python
class EntityMatcher:
    """NPC Registry 기반 고유명사 정합성 검증"""

    def __init__(self, registry: dict):
        self._names = {}  # name → canonical_name
        self._aliases = {}  # alias → canonical_name
        for npc in registry.values():
            canon = npc["name"]
            self._names[canon] = canon
            for alias in npc.get("aliases", []):
                self._aliases[alias] = canon

    def find_mismatches(self, manuscript: str) -> list[dict]:
        """원고에서 Registry에 없는 인명 탐지"""
        issues = []
        for name, canon in self._names.items():
            pattern = rf"(?<![가-힣]){re.escape(name)}[이가은는을를의와과]"
            if re.search(pattern, manuscript):
                # 등장 확인 → 상태 검증
                ...
        return issues
```

| 항목 | 수치 |
|------|------|
| 대체 범위 | director_continuity L122의 ~70% (이름/직급/지명 매칭) |
| 잔여 LLM 필요 | ~30% (맥락적 판단: "이 '철수'가 NPC 김철수인지 다른 인물인지") |
| 토큰 절감 | ~2,000-3,000/에피소드 |
| 구현 난이도 | 중간 (truth_gate.py 패턴 재사용 가능) |

---

## 20. L-4. KoreanParticleEngine — 조사 보정 레이어

**역할**: L-1(DEA) 적용 후 조사 부정합 자동 수정. DEA의 필수 동반 레이어.

**필요한 이유**: "주혁이" → "강혁이" (○), "주혁을" → "강혁을" (○) 이지만 "주혁이" → "강혁가" (✗) 방지

```python
class KoreanParticleEngine:
    """받침 유무에 따른 한국어 조사 자동 보정"""

    PARTICLE_PAIRS = {
        "이": "가", "가": "이",   # 주격
        "을": "를", "를": "을",   # 목적격
        "은": "는", "는": "은",   # 보조사
        "과": "와", "와": "과",   # 접속
        "으로": "로", "로": "으로",  # 방향
        "아": "야", "야": "아",   # 호격
    }

    @staticmethod
    def has_jongseong(char: str) -> bool:
        """한글 문자의 받침 유무 판단"""
        code = ord(char) - 0xAC00
        return code >= 0 and (code % 28) > 0

    def fix_particle(self, old_name: str, new_name: str, text: str) -> str:
        """이름 교체 후 뒤따르는 조사를 자동 보정"""
        old_has = self.has_jongseong(old_name[-1])
        new_has = self.has_jongseong(new_name[-1])
        if old_has == new_has:
            return text  # 받침 동일 → 조사 변경 불필요
        # 받침 상태가 다름 → 조사 교체 필요
        for p1, p2 in self.PARTICLE_PAIRS.items():
            old_with_particle = new_name + p1  # 이미 교체된 이름 + 옛 조사
            new_with_particle = new_name + p2  # 교체된 이름 + 새 조사
            text = text.replace(old_with_particle, new_with_particle)
        return text
```

| 항목 | 수치 |
|------|------|
| 용도 | L-1(DEA) 후처리 필수 동반 레이어 |
| 정확도 | 일반 조사 99%+, 복합 조사(에게서, 으로부터) 별도 규칙 필요 |
| 구현 난이도 | 낮음 (30줄, 받침 판단 공식은 Unicode 표준) |

---

## 21. L-5. EarlyReturnGate — Advisory 조기반환 레이어

**대체 대상**: Advisory 체인의 7개 LLM 호출 중 Python으로 결론낼 수 있는 것

**핵심 발견**: Advisory 9개 중 이미 Python 비율이 높다:

| Advisory | Python 비율 | Early Return 조건 (이 조건 시 LLM skip) |
|----------|:-----------:|--------------------------------------|
| TruthGate | 70% (6/7 검사) | 6개 Python 검사 모두 통과 시 |
| NpcDrift | 30% | 등장 NPC가 0명이면 |
| NumericDrift | 40% | Python 사전경고 0건이면 |
| Flashback | 60% | 회상 마커(`회상`, `기억했다`, `떠올렸다`) 0개면 |
| InfoParadox | 50% | 미래 지식 참조 0건이면 |
| RelDrift | 50% | 관계 변화 0건이면 |
| LongTermRep | 40% | 반복 패턴 < 임계값이면 |
| StyleSignal | 0% | skip 불가 (주관적 판단) |
| NumericConsist | **100%** | 이미 Python only |

```python
class EarlyReturnGate:
    """Advisory LLM 호출 전, Python으로 결론 가능하면 LLM을 안 부른다."""

    def should_call_llm(self, advisory_name: str, python_result: dict) -> bool:
        if advisory_name == "TruthGate":
            return python_result.get("world_law_check_needed", False)
        elif advisory_name == "Flashback":
            return len(python_result.get("flashback_markers", [])) > 0
        elif advisory_name == "InfoParadox":
            return len(python_result.get("temporal_anomalies", [])) > 0
        elif advisory_name == "NpcDrift":
            return len(python_result.get("appearing_npcs", [])) > 0
        elif advisory_name == "NumericDrift":
            return len(python_result.get("pre_warnings", [])) > 0
        return True  # 기본: LLM 호출
```

| 항목 | 수치 |
|------|------|
| 예상 LLM skip 비율 | 에피소드당 7개 Advisory 중 **2-4개** skip |
| 토큰 절감 | 에피소드당 ~40,000-80,000 토큰 |
| 구현 난이도 | 낮음 (각 Advisory에 gate 조건 1개씩 추가) |

---

## 22. L-6. DeterministicScorer — 폴백 선택 레이어

**대체 대상**: 앙상블 폴백 시 `candidates[0]` 선택 (director_ensemble.py)

**현재**: LLM 파싱 실패 → 무조건 첫 번째 후보 선택 (무의식적 편향)
**레이어 장착 후**: Python warning 수, 길이 적합도 등으로 결정론적 순위. **LLM을 안 부른다.**

```python
class DeterministicScorer:
    """LLM 없이 후보 간 결정론적 순위 결정"""

    def rank_candidates(self, candidates: list[dict]) -> list[dict]:
        for c in candidates:
            c["_det_score"] = (
                -c.get("python_warning_count", 0) * 10  # 경고 적을수록 유리
                + min(c.get("char_count", 0), 5500) / 55  # 적정 길이 보너스
                - abs(c.get("char_count", 5000) - 5000) / 100  # 5000자 편차 페널티
                + (1 if c.get("has_cliffhanger") else 0) * 5  # 클리프행어 보너스
            )
        return sorted(candidates, key=lambda c: c["_det_score"], reverse=True)
```

| 항목 | 수치 |
|------|------|
| 적용 시점 | LLM 파싱 실패 폴백, 동점 타이브레이커 |
| 편향 제거 | 전략 순서 → 객관적 품질 메트릭 기반 |
| 구현 난이도 | 낮음 (이미 `_canonical_score_breakdown` 존재) |

---

# Part 3-B: 무기 — LLM에게 쥐여주는 도구

> 레이어(L-1~L-6)는 LLM을 **안 부르는** 것이었다.
> 무기(W-1~W-7)는 LLM을 **부르되**, 더 정확하고 빠르게 일하도록 돕는 도구다.
> LLM 프롬프트에 포함되거나, LLM 출력을 즉시 검증하거나, LLM 입력을 최적화한다.

---

## 23. W-1. FactDatabase — 사실의 창

**대체 대상**: InfoParadox, TruthGate, RelDrift의 LLM 기반 사실 확인

**현재**: LLM이 "주인공이 30화에서 이 정보를 알았나?" 판단
**무기 장착 후**: 사실 DB에서 즉시 조회

```python
class FactDatabase:
    """에피소드별 사실/지식 인덱스 — LLM 없이 사실 확인"""

    def __init__(self, db):
        self._reveals = {}      # {fact_id: reveal_episode}
        self._npc_first_seen = {}  # {npc_name: first_episode}
        self._deaths = {}       # {npc_name: death_episode}
        self._locations = {}    # {location: status}
        self._load_from_db(db)

    def protagonist_knows(self, fact: str, at_episode: int) -> bool:
        """주인공이 특정 에피소드에서 이 사실을 알고 있는가?"""
        reveal_ep = self._reveals.get(fact)
        return reveal_ep is not None and reveal_ep <= at_episode

    def is_alive(self, npc_name: str, at_episode: int) -> bool:
        death_ep = self._deaths.get(npc_name)
        return death_ep is None or death_ep > at_episode

    def npc_introduced(self, npc_name: str, at_episode: int) -> bool:
        first_ep = self._npc_first_seen.get(npc_name)
        return first_ep is not None and first_ep <= at_episode
```

**이미 부분 구현됨**: `fact_ledger.py`, `truth_gate.py`의 deceased 체크, `world_state.py`
**필요한 것**: 이들을 **통합 조회 인터페이스**로 묶는 것

| 항목 | 수치 |
|------|------|
| 조회 시간 | O(1) (dict lookup) vs LLM ~3-5초 |
| 적용 Advisory | TruthGate, InfoParadox, RelDrift |
| 구현 난이도 | 중간 (기존 모듈 통합 래퍼) |

---

## 24. W-2. TemporalValidator — 시간의 방패

**역할**: LLM이 모순 판단할 때, "이 순서 맞아?"를 **즉시 답변**해주는 도구.
LLM 프롬프트에 시간순서 위반 사전탐지 결과를 삽입하여 LLM이 놓치지 않게 한다.

**대체 대상**: InfoParadox, ContinuityValidator의 시간순서 검증 부분

```python
class TemporalValidator:
    """인과관계/시간순서 위반을 결정론적으로 탐지"""

    def check_knowledge_leak(self, manuscript: str, ep_num: int,
                              knowledge_map: dict) -> list[dict]:
        """주인공이 아직 모르는 정보를 언급하는지"""
        violations = []
        for fact, reveal_ep in knowledge_map.items():
            if reveal_ep > ep_num and fact in manuscript:
                violations.append({
                    "type": "knowledge_leak",
                    "fact": fact,
                    "revealed_at": reveal_ep,
                    "current_ep": ep_num
                })
        return violations

    def check_npc_before_introduction(self, manuscript: str, ep_num: int,
                                       first_seen: dict) -> list[dict]:
        """소개 전 NPC가 등장하는지"""
        violations = []
        for npc, intro_ep in first_seen.items():
            if intro_ep > ep_num:
                pattern = rf"(?<![가-힣]){re.escape(npc)}[이가은는을를의]"
                if re.search(pattern, manuscript):
                    violations.append({
                        "type": "premature_npc",
                        "npc": npc,
                        "introduced_at": intro_ep
                    })
        return violations
```

| 항목 | 수치 |
|------|------|
| 정확도 | 정확한 문자열 매칭 시 100% (의미적 우회 탐지 불가 → LLM 보완) |
| 토큰 절감 | InfoParadox LLM 호출의 ~50% skip 가능 |

---

## 25. W-3. SceneContextFilter — 시야 확보

**대체 대상**: NPC 장비, 세계 상태 등 전체 데이터를 무차별 전송하는 패턴

**현재**: NPC 20-40명 전원의 장비 데이터를 매 에피소드 전송 (2-8 KB)
**무기 장착 후**: 현재 scene_breakdown에 등장하는 NPC만 필터

```python
class SceneContextFilter:
    """Blueprint scene_breakdown 기반으로 관련 컨텍스트만 추출"""

    def filter_npcs(self, blueprint: dict, all_npcs: list) -> list:
        scene_npcs = set()
        for scene in blueprint.get("scene_breakdown", {}).values():
            if isinstance(scene, dict):
                scene_npcs.update(scene.get("npcs", []))
        return [npc for npc in all_npcs if npc.get("name") in scene_npcs]

    def filter_world_state(self, blueprint: dict, world_state: dict) -> dict:
        """현재 장면에 관련된 세계 상태만 추출"""
        relevant_locations = set()
        for scene in blueprint.get("scene_breakdown", {}).values():
            if isinstance(scene, dict) and scene.get("location"):
                relevant_locations.add(scene["location"])
        # 관련 지역 + 정치/경제 상황만 포함
        return {k: v for k, v in world_state.items()
                if k in ("politics", "economy") or k in relevant_locations}
```

| 항목 | 수치 |
|------|------|
| NPC 컨텍스트 절감 | 2-8 KB → 200-800 chars (75-90%) |
| 세계 상태 절감 | 1-2 KB → 300-600 chars (40-70%) |
| 적용 위치 | chief_writer_context_packets.py L683-710 |
| 구현 난이도 | 매우 낮음 (필터 조건 추가) |

---

## 26. W-4. ContradictionIndex — 지도

**대체 대상**: Director에게 전송되는 이전 30화 원고 전문 (80-150 KB)

**현재**: Director가 모순 탐지를 위해 이전 30화 원고 전문을 읽음
**무기 장착 후**: 에피소드별 핵심 사실만 인덱싱 → 30KB 이하로 압축

```python
class ContradictionIndex:
    """에피소드별 핵심 사실 인덱스 — Director 컨텍스트 80% 절감"""

    def build_index(self, episodes: list[dict]) -> str:
        """30화 분량의 모순 탐지 인덱스 생성"""
        lines = []
        for ep in episodes:
            lines.append(f"[{ep['ep_num']}화]")
            lines.append(f"  자산: {ep.get('asset', '?')}")
            lines.append(f"  위치: {ep.get('location', '?')}")
            lines.append(f"  관계변화: {ep.get('rel_changes', '없음')}")
            lines.append(f"  사망/파괴: {ep.get('deaths', '없음')}")
            lines.append(f"  핵심사건: {ep.get('key_event', '?')}")
        return "\n".join(lines)
    # 예시 출력:
    # [1화] 자산: 100억 / 위치: 서울 / 관계변화: CEO 첫만남 / 핵심사건: 투자 시작
    # [2화] 자산: 102억 / 위치: 서울 / 관계변화: 없음 / 핵심사건: 시장 조사
    # ...
    # 30화 × 5줄 = ~150줄, ~3-5 KB (vs 현재 80-150 KB)
```

| 항목 | 수치 |
|------|------|
| Director 컨텍스트 절감 | 80-150 KB → 3-5 KB (**95% 절감**) |
| 모순 탐지 정확도 | 수치/이름/위치/사망 = 100%, 서사적 모순 = 별도 LLM 보완 |
| 구현 난이도 | 중간 (episode_bible에서 추출) |

---

## 27. W-5. PatchVerifier — 거울

**역할**: LLM이 패치한 결과를 **즉시 검증**. "잘 고쳤나?" Python으로 확인.
통과 시 Director 재감사 LLM 호출 자체를 skip할 수 있다.

```python
class PatchVerifier:
    """fix_pack 기반 패치 성공 자동 검증 — LLM 재감사 전 Python 선검증"""

    def verify(self, original: str, patched: str, fix_pack: dict) -> bool:
        checks = []
        for target in fix_pack.get("patch_targets", []):
            if "→" in target:
                old, new = target.split("→", 1)
                checks.append(("absent", old.strip()))
                checks.append(("present", new.strip()))
        for check_type, value in checks:
            if check_type == "absent" and value in patched:
                return False
            if check_type == "present" and value not in patched:
                return False
        ratio = calc_patch_change_ratio(original, patched)
        if ratio > 0.30:
            return False
        return True
```

| 항목 | 수치 |
|------|------|
| Director 재감사 skip | entity_ref 타입 패치의 ~80% |
| 토큰 절감 | 재감사당 ~20,000-30,000 토큰 |
| 구현 난이도 | 낮음 |

---

## 28. W-6. AdvisoryBatcher — 병참

**대체 대상**: 7개 LLM Advisory × 3후보 = 21회 독립 LLM 호출

**현재**: 각 Advisory가 독립적으로 LLM 호출 (컨텍스트 공유 없음)
**무기 장착 후**: 공통 컨텍스트 1회 캐시 + Advisory별 질문만 변경

**옵션 A — 컨텍스트 풀링** (현행 아키텍처 유지):
```
공통 컨텍스트 (세계상태 + NPC + 이전에피소드) = 20K
  → 1회 캐시 생성
  → 7개 Advisory가 각각 캐시 참조 + 자기 질문 2K만 추가
  = 20K × 1 + 2K × 7 = 34K (vs 현재 175K, 80% 절감)
```

**옵션 B — 단일 호출 배치** (아키텍처 변경):
```
1회 LLM 호출에 7개 질문 포함:
  "다음 7가지 관점에서 원고를 평가하라:
   1. TruthGate: 세계법칙 위반?
   2. NpcDrift: NPC 속성 변이?
   3. Flashback: 회상 정합성?
   ..."
  → LLM 1회 호출 (vs 현재 7회)
  → 토큰: 25K × 1 (vs 175K)
```

| 항목 | 옵션 A | 옵션 B |
|------|--------|--------|
| 토큰 절감 | ~80% | ~86% |
| 구현 난이도 | 낮음 (캐시 공유) | 높음 (프롬프트 재설계) |
| 병렬성 유지 | 유지 | 상실 (단일 호출) |
| 품질 리스크 | 없음 | LLM 주의분산 가능성 |

---

## 20. 정비 무기 — LLM 출력을 후처리

### W-12. PatchVerifier (패치 성공 자동 검증)

**대체 대상**: PASS_WITH_FIX 재감사의 LLM 의존

**현재**: 패치 후 Director가 다시 전문을 읽고 "성공했나?" 판단
**무기 장착 후**: fix_pack 기반 Python 자동 검증 → 통과 시 Director skip

```python
class PatchVerifier:
    """fix_pack의 success_condition을 실행 가능한 검증으로 변환"""

    def verify(self, original: str, patched: str, fix_pack: dict) -> bool:
        checks = []
        for target in fix_pack.get("patch_targets", []):
            if "→" in target:  # "주혁→강혁" 형태
                old, new = target.split("→", 1)
                checks.append(("absent", old.strip()))
                checks.append(("present", new.strip()))

        for check_type, value in checks:
            if check_type == "absent" and value in patched:
                return False  # 아직 남아있음
            if check_type == "present" and value not in patched:
                return False  # 교체 안 됨

        # 변경량 검증
        ratio = calc_patch_change_ratio(original, patched)
        if ratio > 0.30:
            return False  # 과도한 변경

        return True  # Python 검증 통과 → Director 재감사 skip 가능
```

| 항목 | 수치 |
|------|------|
| Director 재감사 skip | entity_ref 타입 패치의 ~80% |
| 토큰 절감 | 재감사당 ~20,000-30,000 토큰 |
| 구현 난이도 | 낮음 |

---

## 29. W-7. StructuredFeedbackCompiler — 통신기

**역할**: Director → ChiefWriter 피드백 전달 시 **자연어 손실을 방지**.
Director 출력을 LLM이 해석하기 쉬운 구조화 형태 + 레이어가 처리 가능한 edit spec으로 분리.

**현재**: Director가 자연어로 피드백 → ChiefWriter가 자연어를 재해석 (손실 발생)
**무기 장착 후**: `must_fix` → 레이어용(DEA) / LLM용으로 자동 분류

```python
class StructuredFeedbackCompiler:
    """Director 피드백을 기계 실행 가능한 edit spec으로 변환"""

    def compile(self, fix_pack: dict, manuscript: str) -> list[dict]:
        edits = []
        for item in fix_pack.get("must_fix", []):
            # "주혁→강혁" 패턴 → DEA용 replace edit
            if "→" in item:
                old, new = item.split("→", 1)
                edits.append({"type": "replace", "old": old.strip(),
                              "new": new.strip(), "handler": "DEA"})
            # "~를 삭제" 패턴 → DEA용 delete edit
            elif item.endswith("삭제") or item.endswith("제거"):
                target = item.rsplit(" ", 1)[0]
                edits.append({"type": "delete", "target": target,
                              "handler": "DEA"})
            else:
                # 복잡한 수정 → LLM 필요
                edits.append({"type": "rewrite", "instruction": item,
                              "handler": "LLM"})
        return edits
```

---

---

# Part 3-C: 전후 비교 및 우선순위

---

## 30. 레이어+무기 장착 전후 비교: 에피소드 1회 처리

```
현재 (맨손):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ChiefWriter 생성:     3 LLM 호출   (필수 — 창작)
  Director 선택/평가:   1 LLM 호출   (필수 — 판단)
  Advisory 체인:       21 LLM 호출   (7 Advisory × 3후보)
  상태 추출:            3 LLM 호출   (에피소드 종료 상태)
  고유명사 검증:         1 LLM 호출
  ────────────────────────────────────
  합계: 29 LLM 호출

  PASS_WITH_FIX 시 추가:
  패치 생성:            1 LLM 호출   (전문 재생성)
  Director 재감사:      1 LLM 호출
  Advisory 재검증:     21 LLM 호출
  ────────────────────────────────────
  추가: 23 LLM 호출 → 총 52 LLM 호출


무기 장착 후:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ChiefWriter 생성:     3 LLM 호출   (필수 — 변경 없음)
  Director 선택/평가:   1 LLM 호출   (필수 — 변경 없음)
  Advisory 체인:
    W-6 EarlyReturn → 2-4개 skip
    W-11 Batcher → 컨텍스트 공유
    실제 호출:          9-15 LLM 호출 (vs 21)
  상태 추출:
    W-2 RegexParser → 마커 있으면 0 호출
    실제 호출:          0-1 LLM 호출  (vs 3)
  고유명사 검증:
    W-3 EntityMatcher → Python 선행
    실제 호출:          0-1 LLM 호출  (vs 1)
  ────────────────────────────────────
  합계: 13-20 LLM 호출 (vs 29, 31-55% 절감)

  PASS_WITH_FIX 시 추가:
  W-7 통신기 → fix_pack 구조화 → 레이어/LLM 분류
  L-1 DEA → entity_ref면 LLM 0회
  L-4 조사 보정 → 자동
  W-5 거울 → Python 검증 통과 시 재감사 skip
  실제 호출:            0-2 LLM 호출  (vs 23)
  ────────────────────────────────────
  총: 13-22 LLM 호출 (vs 52, 58-75% 절감)
```

---

## 31. 토큰 비용 총 절감 추정

| 분류 | 이름 | 에피소드당 절감 | 10화 Arc 절감 | 비고 |
|:----:|------|:-------------:|:------------:|------|
| L-1 | DEA (수정 레이어) | 5,000 tok | 50,000 | entity_ref 패치 시 |
| L-1A | SurgicalRewrite (수술적 재작성) | **3,000** | **30,000** | local_phrase/sentence 패치 시 (92% 절감) |
| L-2 | RegexParser | 1,500 | 15,000 | 마커 존재 시 100% skip |
| L-3 | EntityMatcher | 2,500 | 25,000 | LLM 70% 대체 |
| L-4 | ParticleEngine | (L-1 동반) | — | DEA 필수 동반 |
| L-5 | EarlyReturnGate | **40,000-80,000** | **400K-800K** | Advisory 2-4개 skip |
| L-6 | DeterministicScorer | 500 | 5,000 | 폴백 시만 |
| W-1 | FactDatabase | 5,000 | 50,000 | 3개 Advisory 보강 |
| W-2 | TemporalValidator | 3,000 | 30,000 | InfoParadox 50% 보강 |
| W-3 | SceneContextFilter | 3,000 | 30,000 | 프롬프트 크기 절감 |
| W-4 | ContradictionIndex | **25,000-35,000** | **250K-350K** | Director 95% 절감 |
| W-5 | PatchVerifier | 20,000-30,000 | 200K-300K | 재감사 skip |
| W-6 | AdvisoryBatcher | **20,000-40,000** | **200K-400K** | 컨텍스트 공유 |
| W-7 | FeedbackCompiler | 2,000 | 20,000 | 피드백 손실 방지 |
| | | | | |
| | **합계** | **~130K-200K/에피** | **~1.3M-2.0M/Arc** | |

**현재 에피소드당 추정 비용**: ~300K-450K 토큰 (캐싱 전)
**레이어+무기 장착 후**: ~100K-250K 토큰
**절감률**: **40-65%**

---

## 32. 구현 우선순위 (ROI × 난이도 매트릭스)

```
                    구현 난이도
              낮음          중간          높음
         ┌──────────┬──────────┬──────────┐
   높    │ ★ L-5   │ W-4      │ W-6B     │
   음    │   Early  │   Contra │   Batch  │
         │   Return │   Index  │   (단일)  │
   R  ├──┤──────────┼──────────┼──────────┤
   O     │ L-1+L-4  │ L-3      │          │
   I  중 │   DEA+   │   Entity │          │
      간 │   조사    │   Match  │          │
         ├──────────┼──────────┼──────────┤
         │ L-2 L-6  │ W-1 W-2  │ W-6A     │
   낮    │ W-5      │ W-3      │ W-7      │
   음    │ Regex    │ Scene    │ Feedback │
         │ Score    │ Filter   │ Compiler │
         │ Verify   │          │          │
         └──────────┴──────────┴──────────┘

즉시 착수 (1주 내):
  1. L-5   EarlyReturnGate     — Advisory skip (가장 큰 절감, 레이어)
  2. L-1   DEA + L-4 조사엔진  — entity_ref 무오염 패치 (레이어)
  3. L-1A  SurgicalRewrite     — 문단 단위 수술적 재작성 (하이브리드 레이어)
  4. L-2   RegexParser          — 자기 출력 자기 파싱 제거 (레이어)
  5. W-5   PatchVerifier        — 재감사 LLM 호출 skip (무기→거울)

2주차:
  5. W-4  ContradictionIndex  — Director 컨텍스트 95% 절감 (무기→지도)
  6. L-3  EntityMatcher       — 고유명사 결정론적 매칭 (레이어)
  7. L-6  DeterministicScorer — 폴백 편향 제거 (레이어)

3주차:
  8. W-3  SceneContextFilter  — NPC/세계상태 필터링 (무기→시야)
  9. W-1  FactDatabase        — 통합 사실 조회 (무기→창)
  10. W-2 TemporalValidator   — 시간순서 자동 검증 (무기→방패)

4주차:
  11. W-6 AdvisoryBatcher    — Advisory 컨텍스트 공유 (무기→병참)
  12. W-7 FeedbackCompiler   — 피드백 구조화 (무기→통신기)
```

---

## 33. 한 줄 요약

> **레이어는 LLM을 안 부르는 것, 무기는 LLM에게 쥐여주는 것.**
> 레이어 7종(L-1~L-6 + L-1A)으로 59개 LLM 호출 중 **~20개(34%)**를 대체하고,
> 무기 7종(W-1~W-7)으로 나머지 ~39개의 **정확도와 효율을 2-3배** 향상시킨다.
>
> **L-1A(수술적 재작성)**는 핵심 혁신이다:
> "장소가 틀렸다 → 해당 문단만 LLM에 보내고 나머지 4,900자는 코드가 보존"
> 이것이 Opus의 Edit tool이 하는 것과 동등한 정밀도를 소설 수정에 가져온다.

---

*끝.*
