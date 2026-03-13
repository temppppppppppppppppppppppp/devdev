# Stage 0 전량 전수조사 — 최종 3pass 재감리

> 작성일: 2026-03-13
> TF Prefix: `SZ0`
> 상태: `final`
> 입력: 5개 트랙 findings + 통합본 (18건 고유 finding)

---

## 재감리 목적

통합본의 18건(P2×8, P3×10)에 대해:
1. 트랙 간 중복/모순 없는지 확인
2. Severity 일관성 검증
3. 누락된 교차 영향 식별
4. 최종 확정 판정

---

## REAUDIT PASS 1 — 중복/모순 검토

### 중복 확인

| Finding A | Finding B | 판정 |
|-----------|-----------|------|
| SZ0-T3-003 (인코딩 깨짐) | SZ0-T5-001 (인코딩 깨짐) | **동일 이슈**. T3-003을 SSOT로, T5-001은 T3-003 참조로 통합 |
| SZ0-T5-003 (POV UI 중복) | SZ0-T3-003 (인코딩 깨짐) | **관련이지만 별건**. T5-003은 중복 구현 drift 위험, T3-003은 인코딩 문제. 양쪽 유지 |
| SZ0-T1-F04 (relationship 15캡) | SZ0-T3-002 (_INCOMPATIBLE 불완전) | **별건**. T1-F04는 데이터 절삭, T3-002는 장르 감지 가드 부족. 영역 다름 |

### 모순 확인

- T2 "대원칙 위반 0건" vs T4-002/T4-003 "원칙 위반 아님 (P3 정보성)": **모순 없음**. T2는 위반 여부를, T4는 위반이 아닌 근거를 각각 기록.
- T1 "P1-2/P1-3 오탐" vs T2 "C-6/C-7 허용": **일치**. 양 트랙 동일 판정.

→ 중복 1건 통합, 모순 0건

---

## REAUDIT PASS 2 — Severity 일관성 검증

### P2 일관성 (8건)

| ID | 기준 | 판정 |
|----|------|------|
| T1-F01 (self.bible 불일치) | 기능적 위험 + 테스트 부재 | P2 적정 |
| T1-F02 (arcs 이중 저장) | 트랜잭션 내 기능 정상, 설계 비효율 | **P3으로 하향 검토** — 기능 안전하므로 P3이 적정. 그러나 persist_to_db() 전체 테스트 부재(T1-F03)와 연동되므로 P2 유지 |
| T1-F03 (persist_to_db 테스트 부재) | 5개 서브메서드 + 롤백 경로 미검증 | P2 적정 |
| T1-F04 (15개 캡) | 장편에서 관계 누락 가능, 실질 영향 제한적 | **P3으로 하향** — Arc stub 자체가 참고용이므로 실질 영향 낮음 |
| T3-001 (shallow copy) | nested 구조 공유 → 잠재적 데이터 오염 | P2 적정 |
| T3-002 (_INCOMPATIBLE 불완전) | 10/13 장르 가드 없음. 단 matches≥3 임계값 + 단일 장르 운영이 완화 | P2 적정 |
| T4-001 (reference_excerpt truncation) | 현 1M 모델에서 즉시 문제 아님. fallback 모델 시 위험 | P2 적정 |
| T5-003 (POV UI 중복) | drift 위험은 있으나 즉시 장애는 아님 | **P3으로 하향** — 리팩토링 권장이지 결함이 아님 |

### Severity 조정 결과

| ID | 원래 | 최종 | 사유 |
|----|------|------|------|
| T1-F04 | P2 | **P3** | Arc stub 참고용, 실질 영향 낮음 |
| T5-003 | P2 | **P3** | 중복 구현은 리팩토링 권장, 즉시 결함 아님 |
| 나머지 | — | 유지 | — |

---

## REAUDIT PASS 3 — 최종 확정

### 최종 수치

| Severity | 건수 | Finding ID |
|----------|------|------------|
| P0 | 0 | — |
| P1 | 0 | — |
| P2 | **6** | T1-F01, T1-F02, T1-F03, T3-001, T3-002, T4-001 |
| P3 | **12** | T1-F04, T1-F05, T1-F06, T1-F07, T1-F08, T3-003, T3-004, T3-005, T4-002, T4-003, T5-002, T5-003 |
| 합계 | **18건** (중복 T5-001→T3-003 통합 반영 후 최종 고유 finding 수) |
| 오탐 | 별도 집계 제외 (원문 `17건` 표기는 산술 오류) |
| 대원칙 위반 | 0건 |

### 최종 확정 Findings 전량

#### P2 (6건)

| # | ID | 파일 | 핵심 |
|---|-----|------|------|
| 1 | SZ0-T1-F01 | story_expander.py L208 | generate_bible() None 반환 시 self.bible={} 상태 불일치 |
| 2 | SZ0-T1-F02 | reverse_expander.py L1039,L1181 | save_anchor("arcs") 이중 호출 (기능 정상, 불필요 I/O) |
| 3 | SZ0-T1-F03 | reverse_expander.py L783-833 | persist_to_db() 5개 서브메서드 + 롤백 통합 테스트 부재 |
| 4 | SZ0-T3-001 | preset_registry.py L537,L541 | _enforce_type() list/dict shallow copy → nested 공유 참조 |
| 5 | SZ0-T3-002 | preset_registry.py L613-617 | _INCOMPATIBLE 3/13 장르만 커버 → false positive 미차단 |
| 6 | SZ0-T4-001 | style_extractor.py L577 / chief_writer_context.py L472 | reference_excerpt 50KB truncation guard 부재 |

#### P3 (12건)

| # | ID | 파일 | 핵심 |
|---|-----|------|------|
| 1 | SZ0-T1-F04 | reverse_expander.py L1131 | relationship_changes 15개 캡 (Arc stub 참고용) |
| 2 | SZ0-T1-F05 | story_expander + reverse_expander (4곳) | list→dict[0] 추출 패턴 |
| 3 | SZ0-T1-F06 | reverse_expander.py L311 | _extract_title 단순 휴리스틱 |
| 4 | SZ0-T1-F07 | story_expander.py L467 | _generate_skeleton 배치 실패 시 silent continuation |
| 5 | SZ0-T1-F08 | reverse_expander.py L435 | episode_bible 빈 stub 전파 → HUD 체인 1회 단절 |
| 6 | SZ0-T3-003 | __init__.py L317,L325 | 한글 인코딩 깨짐 (mojibake) |
| 7 | SZ0-T3-004 | preset_registry.py L38,L119,L393 | reputation 필드 COMMON/composer/medical 타입 충돌 |
| 8 | SZ0-T3-005 | preset_registry.py L558-574 | _parse_korean_number() 음수/소수점 미처리 |
| 9 | SZ0-T4-002 | style_extractor.py L628-670, L554-570 | 자동 점수 계산 — 통계적 필터링 확인 (원칙 위반 아님) |
| 10 | SZ0-T4-003 | stage4_orchestrator.py L1492 | StyleGuide→CW Director 미경유 — 집필 지시 영역 확인 (위반 아님) |
| 11 | SZ0-T5-002 | stage01_helpers.py L654-699 | bible/treatment 비대칭 저장 |
| 12 | SZ0-T5-003 | __init__.py + stage01_helpers.py | POV 설정 UI 중복 구현 drift 위험 |

---

## 교차 영향 분석

### T1-F01 ↔ T5-002 연관

- T1-F01: generate_bible() None 반환 시 self.bible 미갱신
- T5-002: _s0_save_results()에서 bible 저장 실패 시 treatment만 저장

이 두 건이 동시 발생하면: Bible 생성 실패 → None 반환 → caller가 `self.bible={}`를 저장 시도 → 빈 bible 저장 성공 → treatment도 저장 → 빈 bible + 유효 treatment 조합이 DB에 영속. Stage 2 진입 시 plot_roadmap 없이 treatment만 참조하게 됨.

**영향**: 발생 확률 극히 낮음 (LLM protagonist 생성 실패 + 빈 dict 저장 경로). run() 내에서 `if not self.bible:` 가드가 treatment 생성 자체를 차단하므로 정상 flow에서는 도달 불가.

### T3-001 ↔ T1-F08 연관

- T3-001: normalize_hud()의 shallow copy
- T1-F08: 빈 stub 전파 시 hud_snapshot={}

빈 stub의 hud_snapshot이 `{}`이면 normalize_hud()가 빈 dict를 처리. shallow copy 문제는 빈 dict에서는 발동하지 않음 (nested 구조 없음). **교차 영향 없음**.

### T3-002 ↔ T4-001 간접 연관

- T3-002: false positive로 불필요한 장르 프리셋 활성화 → HUD 필드 증가
- T4-001: reference_excerpt + to_prompt()의 토큰 예산

프리셋 증가 → HUD report 크기 증가 → CW 프롬프트에 추가 토큰 부담. T4-001의 truncation guard 부재와 합산 시 프롬프트 크기 더 커질 수 있으나, HUD report 자체는 소형(~2KB)이므로 **실질 교차 영향 미미**.

---

## 후속 조치 우선순위 권장

### 즉시 수정 가능 (Quick Win)

1. **SZ0-T3-003**: L317, L325 한글 문자열 복원 (1분)
2. **SZ0-T1-F01**: `return None` 전에 `self.bible = None` 추가 (1줄)
3. **SZ0-T3-001**: `_enforce_type()`의 list/dict 경로를 `copy.deepcopy(value)`로 변경 (2줄)

### 테스트 추가 권장

4. **SZ0-T1-F03**: persist_to_db() 정상/롤백 통합 테스트
5. **SZ0-T3-005**: _parse_korean_number() 음수/소수점/빈문자열 boundary 테스트
6. **SZ0-T3-002**: _INCOMPATIBLE 장르 쌍 추가 또는 임계값 상향

### 모니터링 추가 권장

7. **SZ0-T4-001**: reference_excerpt 주입 시 smart_truncate() 또는 별도 상한 적용

### 장기 리팩토링

8. **SZ0-T5-003**: POV 설정 UI SSOT 통합
9. **SZ0-T1-F02**: save_anchor("arcs") 이중 호출 → 단일 저장으로 통합

---

## 결론

Stage 0 모듈은 **P0/P1 결함 0건, 대원칙 위반 0건**으로 안정적이다. P2 6건은 모두 "즉시 장애"가 아닌 "방어적 개선" 범주이며, 가장 영향이 큰 T3-001(shallow copy)과 T4-001(truncation guard)은 각각 2줄, 1줄 수정으로 해결 가능하다. 최종 고유 finding은 18건이며, 원문 표의 `오탐 17건` 표기는 산술 오류로 본문에서 제거했다.

전체 코드 품질: **양호** (6,300줄 대비 P2 6건 = 1,050줄당 1건)
