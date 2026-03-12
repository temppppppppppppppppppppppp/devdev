# Phase 4 코덱스 오더 — QI-1-B (투자물 클로닝 강화)

> ⚠️ **반드시 UTF-8 인코딩으로 읽을 것**
> 작성일: 2026-03-09
> 상태: 구현 대기

---

## TF 구성 (4건, B1 사용자 의존 스킵)

### TF-B2: _score_sentence() 장르별 가중치 분기 (LOW)
- 파일: `modules/core/stage0/style_extractor.py`
- `StyleExtractor.__init__`에 `genre: str = ""` 파라미터 추가 → `self.genre` 저장
- `_score_sentence()` 내부에서 `self.genre` 분기:
  - 투자물: 금융 서술어 +3, 수치 표현 +2, 협상 동사 +2
  - 기존 무협 감각어/액션동사: 장르 공통 +1로 하향 (투자물 시)
- 호출자 `run_reference_analysis()`, `ReverseExpander.extract_style_guide()` genre 전달 확인

### TF-B3: Anti-AI 패턴 장르 힌트 (LOW)
- 파일: `modules/core/stage0/style_extractor.py` `_generate_anti_patterns()`
- LLM 프롬프트에 `self.genre` 힌트 추가
- 투자물 시 장르 특화 Anti-AI 지시 삽입

### TF-B4: to_prompt() 투자물 전용 섹션 (LOW)
- 파일: `modules/core/stage0/style_extractor.py`
- `StyleGuide` dataclass에 `genre: str = ""` 필드 추가
- `to_prompt()` 말미에 genre=="investment" 시 투자물 문체 규칙 섹션

### TF-B5: POV 장르 인식 (LOW)
- 파일: `modules/core/stage0/style_extractor.py` `_get_pov_rules()`
- 1인칭 + 투자물 시 추가 규칙 (시장 조망 금지, 타인 의도 간접 전달)

---

## 실행 순서

```
Step 1: TF-B2 (StyleExtractor genre 파라미터 + _score_sentence 분기)
Step 2: TF-B3 (_generate_anti_patterns genre 힌트)
Step 3: TF-B4 (StyleGuide.genre + to_prompt 투자물 섹션)
Step 4: TF-B5 (_get_pov_rules 투자물 1인칭)
Step 5: 테스트 실행
```

---

## 체크리스트

- [ ] TF-B2: __init__ genre 파라미터 + self.genre 저장
- [ ] TF-B2: _score_sentence() 투자물 가중치 분기
- [ ] TF-B2: 투자물 금융어/수치/협상 키워드 사전
- [ ] TF-B3: _generate_anti_patterns() 프롬프트 genre 힌트
- [ ] TF-B4: StyleGuide dataclass genre 필드
- [ ] TF-B4: to_prompt() 투자물 전용 섹션
- [ ] TF-B5: _get_pov_rules() 투자물 1인칭 추가 규칙
- [ ] 테스트: 3,696 passed 유지
