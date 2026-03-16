# TF-A: Stage 0 Dead Extraction Signals

> 조사일: 2026-03-16
> 범위: style_extractor.py V2 필드 7개 + 보조 2개
> 방법: Grep 전체 .py 검색 + 코드 직접 읽기

---

## Signal Inventory

| # | Signal | Producer (file:line) | Expected Consumer | Actual Consumer | Status | Impact |
|---|--------|---------------------|-------------------|-----------------|--------|--------|
| A-1 | `sentence_rhythm` | style_extractor.py:742 | S4 CW / 검증기 | to_prompt() only (L144-147) | **WEAK** | M |
| A-2 | `emotion_rendering` | style_extractor.py (LLM phase 4) | S4 CW / 검증기 | to_prompt() only (L150-152) | **WEAK** | M |
| A-3 | `scene_transitions` | style_extractor.py:568 | S4 CW / 검증기 | to_prompt() only (L177-179) | **WEAK** | L |
| A-4 | `dialogue_narration_pattern` | style_extractor.py (LLM phase 4) | S4 CW / 검증기 | to_prompt() only (L169-171) | **WEAK** | M |
| A-5 | `action_scene_density` | style_extractor.py:751 | S4 CW / 검증기 | to_prompt() only (L182-185) | **WEAK** | L |
| A-6 | `calm_scene_density` | style_extractor.py:754 | S4 CW / 검증기 | to_prompt() only (L182-185) | **WEAK** | L |
| A-7 | `exemplary_passages` | style_extractor.py:560 | S4 CW / 검증기 | to_prompt() (L161-166) + stage0/__init__.py:731 (UI only) | **WEAK** | M |

### 보조 필드 (LIVE — 참고용)

| # | Signal | Producer | Actual Consumer | Status |
|---|--------|----------|-----------------|--------|
| A-8 | `anti_ai_patterns` | style_extractor.py (LLM phase 5) | genre_guards/style_guard.py:35 (L99-115 enforcement) | **LIVE** |
| A-9 | `reference_excerpt` | style_extractor.py:454 | stage4_orchestrator.py:1600 → CW 주입 | **LIVE** |

---

## Detailed Findings

### [TF-A-1] sentence_rhythm

- **Producer**: `_analyze_rhythm()` → `style_extractor.py:742`
  - 문장 길이 시퀀스 분석 (S/M/L trigram 패턴)
  - 예: "주요 리듬: SMS(42회), MSM(38회), ..."
- **Storage**: StyleGuide.sentence_rhythm (str)
- **Expected Consumer**: Stage 4 writer/validator가 생성 원고의 리듬 패턴을 측정 → 편차 시 reject
- **Actual Consumer**: `to_prompt()` L144-147에서 LLM 프롬프트 텍스트로 직렬화
- **Status**: WEAK — 프롬프트에 포함되나, 생성 원고에 대한 리듬 패턴 **검증 없음**
- **Evidence**: Grep `sentence_rhythm` → style_extractor.py 내부만 히트. 외부 소비자 0건
- **Impact**: M — AI 모델이 프롬프트 지시를 무시할 경우 리듬 편향 감지 불가
- **Remediation**: KEEP-AUDIT (to_prompt 경유 soft guidance로 충분. 강제 시 과도 engineering)

### [TF-A-2] emotion_rendering

- **Producer**: `_deep_llm_analysis()` → LLM phase 4 (후반부 분석)
  - LLM이 작가의 감정 표현 방식을 2-3문장으로 기술
- **Storage**: StyleGuide.emotion_rendering (str)
- **Expected Consumer**: S4 validator가 감정 직접 서술("슬펐다") 비율 측정 → 위반 시 reject
- **Actual Consumer**: `to_prompt()` L150-152에서 프롬프트 텍스트로 직렬화
- **Status**: WEAK — 감정 표현 패턴 **측정/검증 로직 없음**
- **Evidence**: Grep `emotion_rendering` → style_extractor.py 내부만 히트
- **Impact**: M — "Show don't tell" 위반이 프롬프트만으로 방지되지 않는 경우 감지 불가
- **Remediation**: KEEP-AUDIT

### [TF-A-3] scene_transitions

- **Producer**: `_curate_samples()` → `style_extractor.py:568`
  - _TRANSITION_MARKERS 기반 장면 전환 문장 추출 (10-80자, 최대 12개)
- **Storage**: StyleGuide.scene_transitions (list[str])
- **Expected Consumer**: S4 writer가 참고 / validator가 전환 패턴 검증
- **Actual Consumer**: `to_prompt()` L177-179에서 예시 리스트로 직렬화
- **Status**: WEAK
- **Evidence**: Grep `scene_transitions` → style_extractor.py 내부만 히트
- **Impact**: L — 장면 전환 패턴은 참고 수준. 강제 가치 낮음
- **Remediation**: KEEP-AUDIT

### [TF-A-4] dialogue_narration_pattern

- **Producer**: `_deep_llm_analysis()` → LLM phase 4 (후반부 분석)
  - LLM이 대화-서술 연결 패턴을 2-3문장으로 기술
- **Storage**: StyleGuide.dialogue_narration_pattern (str)
- **Expected Consumer**: S4 writer가 대화 후 지문 패턴 준수 / validator 측정
- **Actual Consumer**: `to_prompt()` L169-171에서 프롬프트 텍스트로 직렬화
- **Status**: WEAK
- **Evidence**: Grep `dialogue_narration_pattern` → style_extractor.py 내부만 히트
- **Impact**: M — 대화-서술 연결은 AI티 핵심 요소이나 측정 경로 없음
- **Remediation**: WIRE (dialogue_ratio와 함께 측정 로직 추가 권장)

### [TF-A-5] action_scene_density

- **Producer**: `_analyze_rhythm()` → `style_extractor.py:751`
  - 액션씬 내 평균 문장 길이 계산
  - 예: "평균 23자/문장, 단문 위주 빠른 리듬"
- **Storage**: StyleGuide.action_scene_density (str)
- **Expected Consumer**: S4에서 액션씬 밀도 검증
- **Actual Consumer**: `to_prompt()` L182-185에서 텍스트로 직렬화
- **Status**: WEAK
- **Evidence**: Grep `action_scene_density` → style_extractor.py 내부만 히트
- **Impact**: L — 참고 수준 가이드
- **Remediation**: KEEP-AUDIT

### [TF-A-6] calm_scene_density

- **Producer**: `_analyze_rhythm()` → `style_extractor.py:754`
  - 일상씬 내 평균 문장 길이 계산
- **Storage**: StyleGuide.calm_scene_density (str)
- **Expected Consumer**: S4에서 일상씬 밀도 검증
- **Actual Consumer**: `to_prompt()` L182-185에서 텍스트로 직렬화
- **Status**: WEAK
- **Evidence**: Grep `calm_scene_density` → style_extractor.py 내부만 히트
- **Impact**: L
- **Remediation**: KEEP-AUDIT

### [TF-A-7] exemplary_passages

- **Producer**: `_curate_samples()` → `style_extractor.py:560`
  - 점수 기반 모범 문단 15개 선별 (150-600자)
- **Storage**: StyleGuide.exemplary_passages (list[str])
- **Expected Consumer**: S4 CW에 직접 주입 / 유사도 측정
- **Actual Consumer**:
  1. `to_prompt()` L161-166 (프롬프트 "참고 문체" 섹션)
  2. `_build_reference_excerpt()` L629 (발췌 구성 재료)
  3. `stage0/__init__.py:731` (UI 요약 출력)
- **Status**: WEAK — 3곳 사용이나 모두 **입력 재료/표시 용도**. 생성 원고와의 유사도 검증 없음
- **Evidence**: 외부 파일 stage0/__init__.py에서 UI 출력만 확인
- **Impact**: M — 모범 문단이 실제 생성 결과에 반영되었는지 측정 불가
- **Remediation**: KEEP-AUDIT (reference_excerpt가 CW 주입을 커버)

---

## Summary

| Status | Count | Fields |
|--------|-------|--------|
| **WEAK** | 7 | sentence_rhythm, emotion_rendering, scene_transitions, dialogue_narration_pattern, action_scene_density, calm_scene_density, exemplary_passages |
| **LIVE** | 2 | anti_ai_patterns (StyleGuard 강제), reference_excerpt (CW 직접 주입) |

### 구조적 패턴

**to_prompt()가 유일한 소비 경로**: 7개 WEAK 필드 모두 `StyleGuide.to_prompt()` → LLM 프롬프트 텍스트로만 소비됨. 프로그래밍적 검증/강제 경로 없음.

**근본 원인**: V2 필드 추출 시 "분석→저장→프롬프트 주입" 파이프라인만 구축. "생성→측정→비교→재시도" 피드백 루프 미구축.

### Remediation 권고

| 우선순위 | 필드 | 조치 |
|---------|------|------|
| P1 | dialogue_narration_pattern | WIRE — 대화-서술 패턴 측정기 추가 권장 |
| P2 | sentence_rhythm | WIRE — 생성 원고 리듬 패턴 측정 → 편차 경고 |
| P3 | emotion_rendering | WIRE — 감정 직접 서술 비율 측정 |
| KEEP | scene_transitions, action/calm_density, exemplary_passages | KEEP-AUDIT — to_prompt 경유 soft guidance 충분 |
