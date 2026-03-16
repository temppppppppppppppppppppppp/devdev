# TF-B: Stage 0 → Downstream Weak Links

> 조사일: 2026-03-16
> 범위: anti_ai_patterns / dialogue_ratio / vocabulary_level 강제 경로 갭
> 방법: Grep 전체 .py 검색 + 코드 직접 읽기

---

## Signal Inventory

| # | Signal | Producer (file:line) | Expected Consumer | Actual Consumer | Status | Impact |
|---|--------|---------------------|-------------------|-----------------|--------|--------|
| B-1 | `anti_ai_patterns` | style_extractor.py:833 (LLM phase 5) | S4 검증기 (문맥 기반 탐지) | style_guard.py:107-115 (substring 매칭) | **ENFORCED** (brittle) | M |
| B-2 | `dialogue_ratio` | style_extractor.py:498 | S4 검증기 (StyleGuide 타겟 대비) | pre_director_manuscript_checker.py:33-119 (하드코딩 0.30) | **ADVISORY** | H |
| B-3 | `vocabulary_level` | style_extractor.py (LLM phase 4) | S4 검증기 (어휘 복잡도 측정) | **NONE** | **DEAD** | M |

---

## Detailed Findings

### [TF-B-1] anti_ai_patterns — ENFORCED (brittle)

- **Producer**: `StyleExtractor._generate_anti_patterns()` → `style_extractor.py:833`
  - LLM 기반 AI 금지 패턴 10개 생성 (예: "깊은 슬픔을 느꼈다" 금지)
- **Prompt Injection**: `StyleGuide.to_prompt()` L155-158
  - "AI 패턴 금지 목록 (위반 시 즉시 REJECT)" 섹션으로 직렬화
- **Enforcement**: `StyleGuard.run_deep_validation()` → `genre_guards/style_guard.py:107-115`
  - 생성 원고에서 각 패턴 **substring 매칭** 수행
  - 발견 시 `{"type": "style_anti_ai", "severity": "MEDIUM"}` violation 생성
  - quality_gate_score 임계값에 영향 → 재시도 트리거 가능
- **Status**: ENFORCED — 다만 **substring 기반이라 취약**
- **Evidence Gap**: "깊은 슬픔을 느꼈다" → 감지됨. "깊은 슬픔이 들렸다" → 미감지
- **Impact**: M — 패턴 변형 시 우회됨
- **Remediation**: WIRE — 의미 기반 매칭으로 업그레이드 권장 (regex 또는 임베딩 유사도)

### [TF-B-2] dialogue_ratio — ADVISORY (하드코딩 타겟 불일치)

- **Producer**: `StyleExtractor._analyze_statistics_v2()` → `style_extractor.py:498`
  - dialogue_chars / total_chars 계산. 프로젝트별 실측값 저장
  - 예: 투자물 0.25, 무협 0.35 등
- **Prompt Injection**: `StyleGuide.to_prompt()` L133
  - "대화 비율: 30%" 형태로 직렬화
- **Measurement**: `PreDirectorManuscriptChecker._check_dialogue_ratio()` → `pre_director_manuscript_checker.py:33-119`
  - 생성 원고의 실제 대화 비율 측정 ✅
  - **BUT**: 비교 기준이 **하드코딩 0.30** (이상치: <0.15 FAIL, <0.22 WARNING, >0.50 WARNING)
  - StyleGuide.dialogue_ratio (프로젝트별 타겟) **무시**
- **Status**: ADVISORY — 측정은 하지만 프로젝트별 타겟 미연동
- **Evidence Gap**: StyleGuide에 dialogue_ratio=0.25 저장 → 체커는 0.30 기준 → 불일치
- **Impact**: H — 장르별 대화 비율 차이가 반영되지 않음 (투자물 vs 무협)
- **Remediation**: WIRE — PreDirectorManuscriptChecker에 StyleGuide.dialogue_ratio 주입하여 동적 임계값 적용

### [TF-B-3] vocabulary_level — DEAD

- **Producer**: `StyleExtractor._deep_llm_analysis()` → LLM phase 4
  - LLM이 "easy/medium/hard" 분류
- **Prompt Injection**: `StyleGuide.to_prompt()` L135
  - "어휘: medium" 형태로 직렬화
- **Measurement**: **없음**
  - `pre_director_manuscript_checker.py`: vocabulary_level 체크 없음
  - `pre_director_style_checker.py`: vocabulary_level 체크 없음
  - `quality_signal_metrics.py`: vocabulary 측정 함수 없음
- **Status**: DEAD — 추출 → 프롬프트 주입만. 생성 원고의 어휘 수준 측정 파이프라인 전무
- **Evidence**: Grep `vocabulary_level` → style_extractor.py + character_voice.py(NPC별 프로필)만 히트. 검증 로직 0건
- **Impact**: M — 어휘 수준 일탈 시 감지 불가 (easy 작품에 hard 어휘 혼입 등)
- **Remediation**: WIRE — 어휘 복잡도 휴리스틱(평균 음절 수, 한자어 비율 등) 추가 권장

---

## Summary

| Status | Count | Signals |
|--------|-------|---------|
| **ENFORCED** (brittle) | 1 | anti_ai_patterns |
| **ADVISORY** | 1 | dialogue_ratio |
| **DEAD** | 1 | vocabulary_level |

### 구조적 패턴

**StyleGuide → to_prompt() → LLM "부탁" 모델**: 3개 신호 모두 프롬프트에 포함되어 LLM에게 "이렇게 써달라" 요청하지만, 실제 결과물 검증은 anti_ai_patterns만 부분적으로 수행. **"측정 → 비교 → 강제" 파이프라인 부재**가 근본 원인.

### Remediation 우선순위

| 우선순위 | Signal | 조치 | 효과 |
|---------|--------|------|------|
| **P1** | dialogue_ratio | PreDirectorManuscriptChecker에 StyleGuide 타겟 연동 | 장르별 대화 비율 강제 |
| **P2** | anti_ai_patterns | substring → regex/semantic 매칭 업그레이드 | 패턴 변형 우회 방지 |
| **P3** | vocabulary_level | 어휘 복잡도 측정기 추가 | 문체 일탈 감지 |
