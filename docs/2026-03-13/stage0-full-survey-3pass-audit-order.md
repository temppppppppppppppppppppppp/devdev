# Stage 0 전량 전수조사 3pass 감리 — 조사 오더

> 작성일: 2026-03-13
> TF Prefix: `SZ0`
> 상태: `executing`

---

## 조사 배경

Stage 0 모듈(5,170줄, 6파일)의 디테일 딥다이브 전수조사.
코드 수정 금지, 근거 기반 조사, 3pass 감리로 오탐 제거 후 문서화.

## 대원칙

1. **Python은 수집만, 판단은 LLM이** — Python은 데이터 수집·포맷팅·전달만
2. **팩트시트 수정 권한은 LLM만** — NPC 속성, 세계관 설정 수정은 LLM뿐
3. **디렉터 주권주의** — Director가 최종 품질 결정권
4. **사망 캐릭터는 회상/언급만 허용**

## 대원칙 위반 판정 기준

- **위반 아님**: 타입 변환, 필드명 정규화, 포맷 변환, 통계적 점수
- **위반**: Python이 품질 판단/팩트 생성/Director 우회
- **경계**: PASS 2에서 정밀 판정

---

## 조사 대상

| 파일 | 줄수 | 역할 |
|------|------|------|
| `modules/core/stage0/__init__.py` | 810 | StageZeroManager 통합 |
| `modules/core/stage0/preset_registry.py` | 739 | 프리셋 스키마 체계 |
| `modules/core/stage0/story_expander.py` | 600 | 컨셉 → Bible + Treatment |
| `modules/core/stage0/reverse_expander.py` | 1,212 | 역설계 (원고 → Bible) |
| `modules/core/stage0/style_extractor.py` | 1,143 | 문체 DNA 추출 |
| `modules/core/stage0/spinner.py` | 666 | UI 스피너 |
| `modules/core/stage01_helpers.py` | 897 | Phase 0/1 위임 |
| `main_a.py` (Stage 0 관련 부분) | ~200 | lazy load, preset restore, 메뉴 |

---

## 5개 트랙

| 트랙 | 대상 | 핵심 관심사 |
|------|------|-------------|
| **SZ0-T1** Expander Pipeline Data Integrity | story_expander, reverse_expander | LLM 응답 파싱, 데이터 소실, DB 트랜잭션 |
| **SZ0-T2** Principle Compliance Audit | 전 6파일 | 대원칙 4개 위반 전수 |
| **SZ0-T3** Preset Schema & HUD Contract | preset_registry, __init__.py | 타입 강제, 장르 호환성, 직렬화 |
| **SZ0-T4** Style Extraction & Downstream | style_extractor, CW 주입 경로 | 자동 점수, excerpt 상한, Director bypass |
| **SZ0-T5** Integration Wiring & Regression | main_a.py, stage01_helpers, 테스트 | lazy load, preset restore, 테스트 커버리지 |

---

## 3pass 프로토콜

- **PASS 1**: 1줄 단위 전수 읽기 → 후보 finding 수집 (ID, 확신도, 분류, 코드 근거)
- **PASS 2**: caller 추적 + 테스트 근거 확인 + 기존 감리 대조 → 확신도 조정, 오탐 분류
- **PASS 3**: 최종 확정 (P0~P3 severity), 오탐 제거 요약, 후속 조치 권장

---

## 1차 조사 이슈 11건 검증 배정

| 이슈 | 트랙 | 내용 |
|------|------|------|
| P1-1 | T1 | story_expander L277: list→dict 첫 항목만 추출 |
| P1-2 | T1,T2 | reverse_expander L897: hud→state_changes 자동변환 |
| P1-3 | T1,T2 | reverse_expander L1046: Arc stub 자동보강 |
| P2-4 | T3,T2 | preset_registry L506: normalize_hud() |
| P2-5 | T3 | _INCOMPATIBLE 투자/무협만 |
| P2-6 | T4,T2 | style_extractor 자동 점수 계산 |
| P2-7 | T4 | reference_excerpt 50KB 상한 |
| P2-8 | T4,T2 | StyleGuide→CW Director bypass |
| P3-9 | T3 | __init__.py 인코딩 깨짐 |
| P3-10 | T1 | generate_bible() 실패 조기반환 |
| P3-11 | T3,T5 | 프리셋 Python 하드코딩 |

---

## 기존 감리 중복 대조 대상

| 기존 문서 | 관련 트랙 | 핵심 finding |
|-----------|----------|-------------|
| ROP-T4-stage0-pov-styleguide-provenance-findings | T4, T5 | ROP-T4-001(P1): live artifact POV provenance 미갱신, ROP-T4-002(P2): operator surface raw POV 노출 |
| MRL-T3-project-switch-preset-registry-findings | T3, T5 | MRL-T3-001(P1): genre/preset truth-source split, MRL-T3-002(P2): destructive recovery partial-success masking |

---

## 산출물 (docs/2026-03-13/)

1. `stage0-full-survey-3pass-audit-order.md` — 본 문서
2. `SZ0-T1-expander-pipeline-data-integrity-findings.md`
3. `SZ0-T2-principle-compliance-audit-findings.md`
4. `SZ0-T3-preset-schema-hud-contract-findings.md`
5. `SZ0-T4-style-extraction-downstream-injection-findings.md`
6. `SZ0-T5-integration-wiring-regression-findings.md`
7. `stage0-full-survey-consolidated-findings.md` — 통합
8. `stage0-full-survey-consolidated-findings-3pass-reaudit.md` — 최종 재감리
