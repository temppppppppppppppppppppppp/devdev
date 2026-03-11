# TF-IPG: InPlace Patch Guard 강화 + 프롬프트 개선

> 작성일: 2026-03-11
> 트리거: 00_test_03 ep_0003 PASS_WITH_FIX → 분량 축소 → 연쇄 REJECT 패턴
> 테스트 기준선: 3,903 passed, 16 skipped (이전: 3,847 collected)

---

## 1. 배경

00_test_03 (treatment-3.1-flash-lite) ep_0003에서:
- Round 1: PASS_WITH_FIX → InPlace patch 진입
- Patch 결과: 5,000자+ → 2,769자 (45% 축소)
- `min_patched_length=2,000` 통과 (절대 하한만 체크)
- Director 재심사: score 50, REJECT
- 이후 4회 추가 시도 모두 실패 → Arc 1 미완주

**근본 원인**: InPlace patch에 원본 대비 축소 guard가 없었음.

---

## 2. 수정 내역

### Phase 1: Guard 패치 (GAP-1~6)

| GAP | 파일 | 수정 내용 |
|-----|------|----------|
| GAP-1 | `chief_writer.py` L1059-1065 | 추출된 manuscript 자체의 길이 체크 (raw 응답이 아닌 추출본 기준 2,000자 미만 → `return []`) |
| GAP-2 | `stage4_interview_round.py` L2870-2887 | REJECT retry 경로에 `min_patched_length` + 축소 guard 추가 (기존: `.strip()` 만 체크) |
| GAP-3 | `stage4_interview_round.py` L2249-2257 | PASS_WITH_FIX 경로에 원본 대비 70% 미만 축소 시 patch 폐기 guard |
| GAP-4 | `stage4_orchestrator.py` L1122-1134 | V75-D blueprint inplace 경로에 `log_patch_diff()` + `calc_patch_change_ratio()` 추가 |
| GAP-5 | `stage2_preflight.py` L1255-1268 | preflight retry 경로에 diff 로깅 + change ratio 체크 추가 |
| GAP-6 | `constants.py` L207-213 | `log_patch_diff()`에 글자수 delta 1줄 로깅 추가 (`X자 → Y자 (+Z.Z%)`) |

### Phase 2: 프롬프트 개선

| 파일 | 수정 내용 |
|------|----------|
| `chief_writer.yaml` PATCH_MODE_PROMPT | 규칙 3: "원문의 문장을 생략하거나 요약하지 마세요" 추가 |
| `chief_writer.yaml` PATCH_MODE_PROMPT | 규칙 4: `{original_char_count}자`, `{min_char_target}자 이상` 구체적 숫자 주입 |
| `chief_writer.yaml` PATCH_MODE_PROMPT | 규칙 6 신규: "절대 축소 금지" 명시 |
| `chief_writer.yaml` PATCH_MODE_PROMPT | `[원고_끝]` 마커 의무화 — 출력 잘림 감지 |
| `chief_writer.py` L982-985 | `format()`에 `original_char_count`, `min_char_target` 인자 추가 |
| `chief_writer.py` L1059-1063 | `[원고_끝]` 마커 검증: 있으면 마커 제거, 없으면 잘림 경고 |

### Phase 3: 설정

| 파일 | 수정 내용 |
|------|----------|
| `validation.yaml` L108 | `inplace_min_preserve_ratio: 0.70` 신규 (YAML SSOT) |

### Phase 4: 테스트 보정 (이전 세션 미커밋 변경 관련)

| 파일 | 수정 내용 |
|------|----------|
| `test_chief_writer_quality.py` L70 | rubric skip 테스트 manuscript를 4,000자+ 길이로 변경 (이전 세션 `_extract_content_text` + MIN_LENGTH 조건 추가에 대응) |
| `test_chief_writer_quality.py` L424 | `thinking_level` "medium" → "low" 기대값 보정 (이전 세션 변경 반영) |
| `test_stage234_fixes.py` L89-90 | `_common_writer_kwargs` unpack 기대값 3→2회 보정 (이전 세션 변경 반영) |

---

## 3. 변경 근거

### 프롬프트 개선의 이유

조사 결과, 현재 InPlace patch가 축소되는 근본 원인 3가지:

1. **`response_mime_type="application/json"` 강제** (`base_agent.py` L793)
   - 프롬프트는 "순수 텍스트" 출력 지시하지만 API가 JSON 강제
   - LLM이 JSON 안에 원고를 축소해서 넣는 경향
   - 기존 TF-47 코드가 JSON 추출 처리하지만, 축소 자체는 방지 못함

2. **원본 글자수를 LLM에게 안 알려줌**
   - "±10% 유지"라 하면서 원본이 몇 자인지 미제공
   - LLM은 자기 출력 토큰 수를 셀 수 없으므로 구체적 목표 필수
   - → `{original_char_count}`, `{min_char_target}` 플레이스홀더 추가

3. **LLM의 요약 편향 (summarization bias)**
   - "고치세요"라 하면 LLM은 수정 안 하는 부분을 압축하는 경향
   - 특히 Gemini 2.5 Pro / flash-lite에서 심함
   - → 규칙 6 "절대 축소 금지" 명시 + `[원고_끝]` 마커로 잘림 감지

### Guard의 이유

| Guard | 비용 | 효과 |
|-------|------|------|
| GAP-3 (70% 축소 방지) | if 1줄 | retry 예산 1회 절약 (Director 재심사까지 안 감) |
| GAP-1 (추출본 길이 체크) | if 1줄 | JSON wrapper에 의한 가짜 통과 방지 |
| GAP-2 (REJECT 경로 통합) | if 4줄 | PASS_WITH_FIX 경로와 동일 보호 수준 달성 |
| GAP-4/5 (diff 로깅) | try/except | 진단 가능성 확보 (런타임 비용 0) |
| GAP-6 (글자수 delta) | 1줄 | 즉시 축소 여부 판별 가능 |

---

## 4. 3-Pass 감리

### Pass 1. 코드 정합성 감리

- [x] GAP-1: `chief_writer.py` — `_manuscript` 길이 체크 위치가 JSON 추출 후, return 전. 정상.
- [x] GAP-2: `stage4_interview_round.py` — 기존 `.strip()` 체크 직후 elif 분기. 정상.
- [x] GAP-3: `stage4_interview_round.py` — `_min_patch_len` 체크 직후 축소 체크. 순서 정상 (절대 하한 먼저, 상대 하한 다음).
- [x] GAP-4: `stage4_orchestrator.py` — `_patched_bp` 존재 확인 후, `round_ctx` 교체 전. 정상.
- [x] GAP-5: `stage2_preflight.py` — InPlace 성공 후, `final_verdict` 설정 전. 정상.
- [x] GAP-6: `constants.py` — `log_patch_diff()` 본문 맨 앞. 정상.
- [x] 프롬프트: `{original_char_count}`, `{min_char_target}` → `inplace_patch()` format 인자에 추가됨.
- [x] `[원고_끝]` 마커: 프롬프트에 지시 + `chief_writer.py`에서 `rfind("[원고_끝]")` 검증/제거.
- [x] `validation.yaml`: `inplace_min_preserve_ratio: 0.70` 추가. `_threshold()` 경로로 접근됨.
- [x] 테스트: 3,903 passed, 16 skipped, 0 failed.

### Pass 2. 대원칙 정합성 감리

- [x] **대원칙 1 (Python 수집, LLM 판단)**: Guard는 Python이 축소를 감지하여 patch를 폐기할 뿐, REJECT/합격을 판정하지 않음. Director가 재심사로 최종 판정. 준수.
- [x] **대원칙 3 (Director 주권주의)**: 축소 patch 폐기는 "Director에게 보여주지 않는 것"이지, "Director를 대신해 REJECT하는 것"이 아님. 폐기 후 기존 retry 경로로 위임. 준수.
- [x] **YAML SSOT**: `inplace_min_preserve_ratio`는 `validation.yaml`에 정의, `_threshold()`로 접근. 하드코딩 없음. 준수.
- [x] **프롬프트 외부화**: `chief_writer.yaml` PATCH_MODE_PROMPT에 모든 지시. Python에 프롬프트 문자열 하드코딩 없음. 준수.

### Pass 3. 부작용 / 위험 감리

- [x] 70% 임계값이 너무 공격적이진 않은가? → 원본 5,000자 기준 3,500자 하한. 정상적인 InPlace는 ±10% (4,500~5,500) 범위. 30% 축소를 허용해도 3,500자이므로 MIN_LENGTH(4,000자)와는 별개 안전장치. 적절.
- [x] `[원고_끝]` 마커가 LLM이 원고 내부에 넣을 위험? → `rfind()`로 마지막 마커만 탐지. 원고 본문에 `[원고_끝]`이 나올 확률 극히 낮음 (웹소설 문체에 없는 패턴). 적절.
- [x] 프롬프트 `{original_char_count}` / `{min_char_target}` 포맷 오류 위험? → `_orig_len`은 항상 int, `_min_char_target`은 `int(_orig_len * 0.9)`. 포맷 에러 불가. 안전.
- [x] fallback 경로가 문제를 유발하는가? → 폴백 템플릿에는 `{original_char_count}` 미포함 (L990-993). 기존과 동일 동작. 안전.
- [x] GAP-4/5 diff 로깅이 성능에 영향? → `log_patch_diff` 내부 difflib 호출은 O(n) 미만. JSON stringify 비용도 30KB 미만. 무시 가능.

---

## 5. 미해소 항목 (향후 검토)

| ID | 내용 | 우선순위 |
|----|------|---------|
| IPG-P2-1 | `response_mime_type="application/json"` 강제가 InPlace에서는 불필요 — `base_agent.ask()`에 `disable_json_mode=True` 옵션 검토 | P2 |
| IPG-P2-2 | Search/Replace 포맷 (aider 패턴) 전환 — LLM이 변경 부분만 반환, Python이 적용 | P2 |
| IPG-P2-3 | Windowed editing (씬 단위 분할) — 5,000자+ 원고를 씬별로 분리, 문제 씬만 패치 | P2 |
| IPG-P2-4 | S2/S3 InPlace에도 축소 guard 추가 (현재 JSON 구조 검증 + deep merge로 부분 보호됨) | P3 |

---

## 6. 조사 결과 요약: LLM InPlace 편집 모범 사례

### 왜 LLM이 "고치세요" 하면 축소하는가?

1. **요약 편향 (Summarization Bias)**: LLM은 요약 태스크로 대량 학습됨. "고치세요" = "압축하고 재생성" 모드로 빠짐.
2. **Lazy Output**: Gemini 2.5 Pro의 기본 `maxOutputTokens`는 8,192 (최대 65,536이 아님). thinking_level이 높으면 추론 토큰에 예산 소모.
3. **Attention Decay**: 긴 텍스트의 후반부일수록 압축/생략 경향 심화.
4. **JSON Mode Friction**: `response_mime_type="application/json"` 사용 시 JSON 구문에 토큰 소비 → 내부 텍스트 축소.

### 업계 모범 사례 (조사 출처: aider, chopdiff, Cursor 등)

| 기법 | 설명 | 효과 |
|------|------|------|
| Search/Replace Block | 변경할 원문 + 수정본만 반환. Python이 `str.replace()` 적용 | 축소 원천 차단 |
| Unified Diff | LLM이 unified diff 반환, Python이 적용 | GPT-4 Turbo 기준 3x laziness 감소 |
| Windowed Transform | 문서를 씬/문단 단위로 분할, 문제 부분만 LLM 처리 | Attention decay 해소 |
| Marker-Based | `[KEEP-AS-IS]` / `[EDIT-THIS]` 태그로 구분 | 보존/수정 영역 명시적 분리 |
| Character Count Enforcement | 원본 글자수 명시 + END 마커 | 잘림 감지 가능 (현재 채택) |

현재 채택: **Character Count Enforcement** (가장 낮은 구현 비용 + 기존 아키텍처 호환).
향후 검토: **Search/Replace Block** (축소 원천 차단이지만 프롬프트 구조 전면 변경 필요).
