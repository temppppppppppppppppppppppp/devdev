# Phase 3 코덱스 오더 — PC-1-B + QI-1-C (전량)

> ⚠️ **반드시 UTF-8 인코딩으로 읽을 것**
> 작성일: 2026-03-09
> 상태: 구현 대기

---

## TF 구성 (5건)

### TF-PC1B: 휴리스틱 보정 (MED-HIGH)
- 파일: `modules/domain/agents/four_phase_arc_generator.py`
- L370-378: sentence_count 분기 ep_count 값 하향
  - ≤8문장: 4→**3**화
  - ≥15문장: 6→**5**화
  - 중간(else): 불변 (Stage2Limits.DEFAULT_EP_COUNT = 4)
- reasoning 문자열 + 주석 동기화

### TF-C1: PERSONALITY_PATTERNS 참고용 전환 (LOW)
- 파일: `modules/core/character_voice_profiler.py` L75-102
- 키워드 풀 확장 (aggressive/cold/warm에 다양한 표현 추가)
- docstring/주석에 "참고용 예시, LLM이 상황에 따라 자유 변형" 명시

### TF-C2: EXCLAMATION_PATTERNS 동적화 (LOW)
- 파일: `modules/core/character_voice.py` L89-95
- CRUDE 키워드 풀 확장 + "상황에 따라 강도 조절" 주석

### TF-C3: intro_dna CYNICAL 기본값 제거 (MED)
- 4파일 7곳: `"CYNICAL"` → `""`
  - `chief_writer.py` L170, L645, L943
  - `chief_writer_context.py` L68, L1066
  - `stage4_orchestrator.py` L686 → protagonist_config에서 동적 로드
  - `writer.py` L66
- `_get_dna_instruction()`: 빈 intro_dna → DNA 블록 생략

### TF-C4: LoreManager 기본 톤 제거 (LOW)
- 파일: `modules/core/lore_manager.py` L128
- `"격조 있는 무인"` → `""` + 빈 톤 시 톤 라인 생략

---

## 실행 순서

```
Step 1: TF-PC1B (독립)
Step 2: TF-C1 (독립)
Step 3: TF-C2 (독립)
Step 4: TF-C4 (독립)
Step 5: TF-C3 (의존: _get_dna_instruction 수정 포함)
Step 6: 테스트 실행 — 전량 PASS 확인
```

---

## 체크리스트

- [ ] TF-PC1B: L370 `ep_count = 4` → `3`, L374 `ep_count = 6` → `5`
- [ ] TF-PC1B: L372 reasoning "4화" → "3화", L375 reasoning "6화" → "5화"
- [ ] TF-C1: PERSONALITY_PATTERNS 키워드 풀 확장 + 참고용 주석
- [ ] TF-C2: EXCLAMATION_PATTERNS CRUDE 확장 + 강도 조절 주석
- [ ] TF-C3: chief_writer.py 3곳 `"CYNICAL"` → `""`
- [ ] TF-C3: chief_writer_context.py 2곳 `"CYNICAL"` → `""`
- [ ] TF-C3: writer.py 1곳 `"CYNICAL"` → `""`
- [ ] TF-C3: stage4_orchestrator.py L686 → protagonist_config 동적 로드
- [ ] TF-C3: _get_dna_instruction() 빈 intro_dna 분기 추가
- [ ] TF-C4: lore_manager.py `"격조 있는 무인"` → `""` + 빈 톤 분기
- [ ] 테스트: 3,696 passed 유지 (기존 실패 2건 제외)
