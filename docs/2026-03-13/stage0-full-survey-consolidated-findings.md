# Stage 0 전량 전수조사 — 통합 Findings

> 작성일: 2026-03-13
> TF Prefix: `SZ0`
> 상태: `consolidated`
> 대상: Stage 0 모듈 7파일 + main_a.py Stage 0 관련 (~6,300줄)

---

## Executive Summary

5개 트랙(T1~T5) 3pass 감리 결과를 통합한다.

| 구분 | 건수 |
|------|------|
| **P0** | 0 |
| **P1** | 0 |
| **P2** | 8 |
| **P3** | 11 |
| **오탐 제거** | 17 |
| **대원칙 위반** | 0 |
| **INFO** | 4 (T2) |

사전 배정 11건 최종 판정:

| 사전 배정 | 최종 | 사유 |
|-----------|------|------|
| P1-1 (list→dict 첫 항목) | P3 (T1-F05) | 방어 코드 존재, 프롬프트 단일 객체 표준 |
| P1-2 (hud→state_changes) | 오탐 | 포맷 변환, 원칙 위반 아님 |
| P1-3 (Arc stub 보강) | 오탐 | LLM 출력 집계/재배치 |
| P2-4 (normalize_hud 타입 강제) | 오탐 (원칙), P2 (shallow copy) | 원칙 위반 아님. 단 shallow copy 문제 별도 확정 |
| P2-5 (_INCOMPATIBLE 불완전) | P2 (T3-002) | 3/13 장르만 커버 |
| P2-6 (자동 점수 계산) | P3 (T4-002) | 통계적 필터링, 원칙 위반 아님 |
| P2-7 (reference_excerpt 50KB) | P2 (T4-001) | truncation guard 부재 |
| P2-8 (StyleGuide→CW Director bypass) | P3 (T4-003) | 집필 지시 영역, Director 주권 위반 아님 |
| P3-9 (인코딩 깨짐) | P3 (T3-003, T5-001) | 확인, 2곳 mojibake |
| P3-10 (generate_bible 조기반환) | P2 (T1-F01) | self.bible 상태 불일치 위험으로 상향 |
| P3-11 (프리셋 하드코딩) | 오탐 | 동적 장르 확장 폐기 확정, 의도된 설계 |

---

## 트랙별 확정 Findings 전량 목록

### T1 — Expander Pipeline Data Integrity

| ID | Sev | 파일 | 요약 |
|----|-----|------|------|
| SZ0-T1-F01 | P2 | story_expander.py L208 | generate_bible() None 반환 시 self.bible 상태 불일치 |
| SZ0-T1-F02 | P2 | reverse_expander.py L1039,L1181 | persist_to_db() 내 save_anchor("arcs") 이중 호출 |
| SZ0-T1-F03 | P2 | reverse_expander.py L783-833 | persist_to_db() 통합 테스트 부재 |
| SZ0-T1-F04 | P2 | reverse_expander.py L1131 | _enrich_arc_stubs relationship_changes 15개 캡 |
| SZ0-T1-F05 | P3 | story_expander L181,L278 / reverse_expander L336,L371 | list→dict 첫 항목 추출 패턴 (4곳) |
| SZ0-T1-F06 | P3 | reverse_expander.py L311 | _extract_title 단순 휴리스틱 |
| SZ0-T1-F07 | P3 | story_expander.py L467 | _generate_skeleton 배치 실패 시 silent continuation |
| SZ0-T1-F08 | P3 | reverse_expander.py L435 | episode_bible 빈 stub 전파로 HUD 체인 단절 |

### T2 — Principle Compliance Audit

| 결과 | 내용 |
|------|------|
| 확정 위반 | **0건** |
| 경계→허용 | 6건 (통계 분류, 포맷 변환, 구조 검증 등) |
| INFO | 4건 (I-1~I-4: 하드코딩 태그, 장르별 hud 필드, enum fallback, POV 임계값) |

### T3 — Preset Schema & HUD Contract

| ID | Sev | 파일 | 요약 |
|----|-----|------|------|
| SZ0-T3-001 | P2 | preset_registry.py L537,L541 | _enforce_type() 정상 경로 shallow copy — nested 구조 공유 참조 |
| SZ0-T3-002 | P2 | preset_registry.py L613-617 | _INCOMPATIBLE 맵이 3/13 장르만 커버 |
| SZ0-T3-003 | P3 | __init__.py L317,L325 | 한글 인코딩 깨짐 (mojibake) |
| SZ0-T3-004 | P3 | preset_registry.py L38,L119,L393 | reputation 필드 충돌 (COMMON/composer/NPC medical 타입 불일치) |
| SZ0-T3-005 | P3 | preset_registry.py L558-574 | _parse_korean_number() 음수/소수점 미처리 |

### T4 — Style Extraction & Downstream Injection

| ID | Sev | 파일 | 요약 |
|----|-----|------|------|
| SZ0-T4-001 | P2 | style_extractor.py L577 / chief_writer_context.py L472 | reference_excerpt 50KB truncation guard 부재 |
| SZ0-T4-002 | P3 | style_extractor.py L628-670, L554-570 | _score_sentence/_score_passage 점수 계산은 통계적 필터링 (원칙 위반 아님) |
| SZ0-T4-003 | P3 | stage4_orchestrator.py L1492 | StyleGuide→CW Director 심사 미경유 (집필 지시 영역, 위반 아님) |

### T5 — Integration Wiring & Regression

| ID | Sev | 파일 | 요약 |
|----|-----|------|------|
| SZ0-T5-001 | P3 | __init__.py L317,L325 | show_protagonist_config_menu() 인코딩 깨짐 (T3-003과 동일) |
| SZ0-T5-002 | P3 | stage01_helpers.py L654-699 | _s0_save_results() bible/treatment 비대칭 저장 |
| SZ0-T5-003 | P2 | __init__.py + stage01_helpers.py | POV 설정 UI 중복 구현 — drift 위험 |

---

## 중복 제거 후 고유 Finding 수

T3-003과 T5-001은 동일 이슈 (인코딩 깨짐). 통합 후 고유 건수:

| Severity | 고유 건수 | Finding ID |
|----------|----------|------------|
| P0 | 0 | — |
| P1 | 0 | — |
| P2 | 8 | T1-F01, T1-F02, T1-F03, T1-F04, T3-001, T3-002, T4-001, T5-003 |
| P3 | 10 | T1-F05, T1-F06, T1-F07, T1-F08, T3-003/T5-001(1건), T3-004, T3-005, T4-002, T4-003, T5-002 |
| 합계 | **18건** | |

---

## 오탐 제거 총괄 (17건)

| 트랙 | 건수 | 주요 사유 |
|------|------|-----------|
| T1 | 8 | 의도된 graceful degradation, 포맷 변환, 데이터 집계 |
| T2 | 10 | 전량 허용 판정 (통계 분류, 구조 검증, 사용자 선택 반영 등) |
| T3 | 4 | 설계 의도(하드코딩), deepcopy 보호, round-trip 정상, 포맷 정규화 |
| T4 | 2 | router 추상화 준수, 기존 감사 검증 완료 |
| T5 | 3 | 의도된 UX, MRL-T3-001 중복, 의도된 설계 |

---

## Coverage Gap 통합

| Gap | 트랙 | 영역 | 우선순위 |
|-----|------|------|----------|
| persist_to_db() 정상/롤백 테스트 | T1 | reverse_expander | HIGH |
| _enforce_type() nested shallow copy 테스트 | T3 | preset_registry | HIGH |
| reference_excerpt + CW 프롬프트 크기 모니터링 | T4 | style_extractor → CW | MED |
| _parse_korean_number() boundary 테스트 | T3 | preset_registry | MED |
| generate_bible() None 반환 케이스 테스트 | T1 | story_expander | MED |
| _INCOMPATIBLE 장르 쌍 false positive 테스트 | T3 | preset_registry | MED |
| show_protagonist_config_menu() 출력 검증 | T5 | __init__.py | LOW |
| _s0_save_results() 부분 실패 시나리오 테스트 | T5 | stage01_helpers | LOW |
| save_state()/load_state() 라운드트립 테스트 | T5 | __init__.py | LOW |
| _enrich_arc_stubs 캡 초과 테스트 | T1 | reverse_expander | LOW |

---

## 기존 감리 교차 참조

| 기존 문서 | 관련 트랙 | 중복/재오픈 |
|-----------|----------|------------|
| ROP-T4-stage0-pov-styleguide-provenance | T4, T5 | 중복 없음. ROP-T4-001(P1 POV provenance), ROP-T4-002(P2 raw POV 노출) 모두 본 감사 범위 밖 |
| MRL-T3-project-switch-preset-registry | T3, T5 | MRL-T3-001(P1) 하위 증상이 T5 후보 F로 나왔으나 오탐 처리. MRL-T3-002(P2) 범위 밖 |
| OPUS-TF-T2 | T1 | T2-003 (list→dict) P2→P3 동일 판정. T2-004 (generate_bible) P1→P2 동일 판정 |
