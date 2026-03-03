# TF-31: 스타일 파이프라인 전수조사 + P0/P1 패치

## 1. 파이프라인 구조

### 데이터 흐름

```
입력 소스 3가지:
  ① config/style_references/{genre}/*.txt   (참조 원고, 수동)
  ② ReverseExpander 역설계 원고              (메뉴 2번)
  ③ config/cash/style_seeds_final.txt        (레거시, DEAD)

     ①/② → StyleExtractor (5단계 분석) → StyleGuide 객체
                                              │
            ┌─────────────────────────────────┤
            ▼                                 ▼
     JSON 파일 저장                     DB anchor 저장
  stage0_output/style_guide.json    save_v20_anchor("style_guide")
  (stage0/__init__.py L435)         (stage01_helpers.py L342/441/472)
                                          │
                                          ▼
                                  Stage4 로딩 3단 폴백:
                              ┌─ 1. load_v20_anchor("style_guide")
                              │     → StyleGuide.from_dict() → .to_prompt()
                              ├─ 2. Bible POV → 최소 StyleGuide
                              └─ 3. 수동 선택 (카카오/네이버)
                                          │
                                          ▼
                               ChiefWriter 프롬프트 주입
                                 {style_guide} 플레이스홀더
                               (chief_writer_context.py L361)
```

### StyleExtractor 5단계

| 단계 | 유형 | 내용 | LLM? |
|------|------|------|------|
| Phase 1 | 통계 분석 | 문장길이, 대화비율, POV, 단락 스타일 | ✗ |
| Phase 2 | 샘플 큐레이션 | 대표 문장 25개, 대사 15개, 모범 문단 8개, 장면전환 8개 | ✗ |
| Phase 3 | 리듬 분석 | S/M/L 트리그램 패턴 5개, 액션/일상 밀도 | ✗ |
| Phase 4 | LLM 심층 분석 | tone, description_style, vocabulary 등 8개 필드 | ✓ |
| Phase 5 | Anti-AI 패턴 | 모범 문단 + LLM → AI 금지 패턴 10개 | ✓ |

### StyleGuide.to_prompt() 9개 섹션

1. 핵심 DNA (tone/pov/dialogue_ratio 등)
2. POV 상세 규칙 (시점별 절대 준수)
3. 문장 리듬 패턴 (AI티 방지)
4. 감정 표현 규칙
5. AI 패턴 금지 목록 (위반 시 REJECT)
6. 모범 문단 (show, don't tell)
7. 대화-서술 연결 패턴
8. 장면 전환 스타일
9. 묘사 밀도 + 활용/금지 표현

출력 크기: 완전본 ~2-5KB / 최소본(POV only) ~500자

### DB 저장 경로 (stage01_helpers.py)

| 트리거 | 메서드 | 라인 |
|--------|--------|------|
| 메뉴 2 (역설계) | `_s0_handle_reverse_engineering` | L342 |
| 메뉴 5 (스타일 분석) | `_s0_handle_style_analysis` | L441 |
| 공통 후처리 (컨셉/임포트) | `_s0_save_results` | L472 |

---

## 2. 발견된 문제점

### TF-31-1: StyleExtractor `_ensure_client` bare except [P0]

**파일**: `modules/core/stage0/style_extractor.py` L705-716

**문제**: `except Exception: pass` — LLM 클라이언트 초기화 실패를 무시. TF-30-5에서 ReverseExpander의 동일 패턴을 `(ImportError, ValueError, RuntimeError)` + 로깅으로 수정했으나, StyleExtractor를 놓침.

**영향**: `genai.Client()` 가 `TypeError` 등 예상 외 에러로 실패해도 무시 → 후속 `_llm_call()` 에서 `self.client`가 None → Phase 4/5 전체 스킵 → anti_ai_patterns 미생성.

**수정**:
```python
except (ImportError, ValueError, RuntimeError) as e:  # [TF-31-1]
    logging.debug("[StyleExtractor] LLM init fail: %s", e)
```

---

### TF-31-2: Bible POV 오버라이드 시 불일치 무경고 [P1]

**파일**: `modules/core/stage4_orchestrator.py` L1039-1045

**문제**: 참조 원고에서 추출한 StyleGuide의 POV를 Bible의 `protagonist_config.pov`로 **무조건 덮어씀**. 참조 원고가 3인칭 기반인데 Bible이 1인칭이면:
- sample_sentences, exemplary_passages = 3인칭 문체
- POV 규칙 = 1인칭 절대 준수
- ChiefWriter가 모순된 지시를 받음

**수정**: POV 불일치 시 경고 로깅 추가.
```python
if _bible_pov and loaded_sg.pov and _bible_pov != loaded_sg.pov:
    logging.warning(
        "[TF-31-2] StyleGuide POV(%s) ≠ Bible POV(%s) — Bible 우선 적용",
        loaded_sg.pov, _bible_pov,
    )
loaded_sg.pov = _bible_pov
```

---

### TF-31-3: "혼합" POV 규칙 미정의 [P1]

**파일**: `modules/core/stage0/style_extractor.py` L98-99

**문제**: `_get_pov_rules()`가 "혼합"/"미지정" POV에 대해 빈 문자열 반환 → `to_prompt()` 섹션 2(POV 규칙)가 완전 누락. 시점 혼합 작품에서 ChiefWriter가 시점 전환 규칙 없이 집필.

**수정**: 혼합 POV 규칙 추가.
```python
elif self.pov == "혼합":
    return """## 🎯 시점 규칙: 혼합 시점
- 씬 단위로 시점 전환 허용 (동일 씬 내 시점 혼합 금지)
- 전환 시 명시적 장면 구분자 사용 (빈 줄 + 시간/장소 전환)
- 주인공 씬: 1인칭 내면 서술 허용
- 타 캐릭터 씬: 3인칭 제한적 시점 (해당 인물의 관찰·감정만)
- 전지적 개입은 장(章) 도입부에서만 허용"""
```

---

### TF-31-4: style_seeds_final.txt 레거시 제거 [P1]

**파일**: `modules/core/project_manager.py` L95-118, `modules/domain/agents/writer.py` L248, `main_a.py` L1120

**문제**:
- `project_manager.py`: 프로젝트 생성 시 `style_seeds_final.txt` 생성 (3회 재시도 포함)
- `_style_seed_available` 플래그: **어디서도 참조 안 됨**
- `writer.py` L248: 레거시 `write_v20_manuscript`에서만 읽음 (파이프라인 미사용)
- `main_a.py` L1120: `_ignite_quad_cache_system` 내부에서 읽음 (**메서드 자체가 dead code** — 호출부 0건)
- `chief_writer`: `style_guide` 파라미터로 직접 받음 (파일 미참조)

**영향**: 프로젝트 생성마다 불필요 파일 I/O (3회 재시도까지) + 사용자 혼란 유발

**수정**:
1. `project_manager.py` L95-118: `style_seeds_final.txt` 생성 코드 + `_style_seed_available` 플래그 제거
2. `writer.py` L248-250: `style_seeds_final.txt` 로딩 코드 제거
3. `main_a.py` L1120, L1128-1129: `style_seeds_final.txt` 참조 제거 (dead code 내)

---

## 3. 다운그레이드 (패치 불필요)

| # | 원래 심각도 | 내용 | 다운그레이드 사유 |
|---|---|---|---|
| P2-5 | P2 | 스타일 분석 수동 메뉴만 | 역설계(메뉴2)는 자동 추출. 참조 원고는 사용자 준비 필요 → 수동이 맞음 |
| P2-6 | P2 | POV-only 최소 StyleGuide | V70 의도적 설계. 참조 원고 없는 프로젝트의 최소 보장 |
| INFO-7 | INFO | mtime 기반 캐시 | 실용적 문제 없음. 캐시 miss해도 재분석만 발생 |

---

## 4. 수정 파일 요약

| TF | 파일 | 변경량 |
|----|------|--------|
| 31-1 | `stage0/style_extractor.py` | 1줄 변경 |
| 31-2 | `stage4_orchestrator.py` | +4줄 |
| 31-3 | `stage0/style_extractor.py` | +6줄 |
| 31-4 | `project_manager.py` | -24줄 |
| 31-4 | `domain/agents/writer.py` | -3줄 |
| 31-4 | `main_a.py` | -3줄 |

총 ~10줄 추가, ~30줄 삭제. 6개 파일 수정.

---

## 5. 실행 순서

모두 독립 — 병렬 가능.

1. TF-31-1 (1줄, 가장 안전)
2. TF-31-3 (POV 규칙 추가)
3. TF-31-2 (경고 로깅)
4. TF-31-4 (레거시 제거)

---

## 6. 검증

1. 각 파일 `python -m py_compile` 통과
2. `python -m ruff check` 0 violations
3. `pytest tests/ -q` 전체 통과
