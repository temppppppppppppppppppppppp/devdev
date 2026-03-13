# XC-ERR Track: 에러 전파 & 실패 모드 충실도 — 전수 조사 감사 오더

> 생성일: 2026-03-13
> 트랙: XC-ERR (Error Propagation & Failure Mode Fidelity)
> 방법론: 3-Pass (수집 → 교차검증 → 위양성 제거)

---

## 1. 감사 범위

### 1차 스코프 (직접 분석 대상)
| 파일 | 역할 | except Exception 카운트 |
|------|------|------------------------|
| `modules/core/failure_analyzer.py` | 실패 패턴 분석 유틸리티 | 28 |
| `modules/core/soft_failure.py` | 구조화된 소프트 실패 리포팅 | 2 |
| `modules/core/stage2_orchestrator.py` | Stage 2 Arc 오케스트레이터 | 12 |
| `modules/core/stage3_orchestrator.py` | Stage 3 Blueprint 오케스트레이터 | 40 |
| `modules/core/stage4_orchestrator.py` | Stage 4 원고 오케스트레이터 | 31 |
| `modules/core/stage4_context_builder.py` | Stage 4 컨텍스트 빌더 | 54 |
| `modules/core/stage4_post_processor.py` | Stage 4 PASS 후처리 | 47 |
| `modules/core/services/project_service.py` | 프로젝트 롤백/리셋 서비스 | 13 |

### 2차 스코프 (전체 modules/ 패턴 스캔)
- **총 `except Exception` 카운트**: 957건 (137개 파일)
- **except Exception + logging.debug/warning만 하는 패턴**: 96건 (96개 파일)
- **bare `except:`**: 0건 (전량 제거 완료)

---

## 2. 서브태스크 구성

| ID | 제목 | 초점 파일 | 산출물 |
|----|------|----------|--------|
| XC-ERR-T1 | Silent Exception 삼킴 전수 조사 | 전체 modules/ | `XC-ERR-T1-silent-exception-swallow-findings.md` |
| XC-ERR-T2 | 에러 카테고리 스테이지간 압축 | stage2_validation_pipeline → DB → stage4_context_builder | `XC-ERR-T2-error-category-cross-stage-compression-findings.md` |
| XC-ERR-T3 | 롤백 핸들러 보상 갭 | project_service.py, db_manager.py | `XC-ERR-T3-rollback-handler-compensation-gap-findings.md` |

---

## 3. 3-Pass 방법론

### PASS 1: 수집
- 정규식 기반 전수 스캔 (`except Exception`, `except:`, `pass`, `continue`, `return None/""/{}/[]`)
- 파일별 카운트 및 패턴 분류
- 모든 후보 finding에 HIGH/MED/LOW 신뢰도 태깅

### PASS 2: 교차검증
- 코드 근거 확인 (실제 라인 번호 + 스니펫)
- 런타임 도달 가능성 검증 (테스트 커버리지 확인)
- 중복 finding 통합

### PASS 3: 위양성 제거
- 의도적 비차단(non-blocking) 패턴 vs 진짜 삼킴 구분
- soft_failure 리포팅이 있는 경우 삼킴으로 분류하지 않음
- 최종 P0-P3 심각도 배정

---

## 4. 핵심 발견 요약

### 전체 통계
- **총 except Exception 패턴**: 957건 / 137 파일
- **silent swallow (pass/continue만)**: ~40건 추정 (상세는 T1)
- **logging.debug만 + return 기본값**: ~96건 (대부분 의도적 비차단)
- **bare except**: 0건
- **soft_failure 리포팅 포함**: 대부분의 주요 오케스트레이터/후처리기

### 심각도 분포 (최종)
| 심각도 | 건수 | 비고 |
|--------|------|------|
| P0 (Critical) | 0 | |
| P1 (High) | 2 | 롤백 보상 갭, 에러 컨텍스트 압축 |
| P2 (Medium) | 5 | Silent swallow 고위험 경로 |
| P3 (Low) | 8 | 비차단 경로 삼킴, 테스트 갭 |

---

## 5. 기존 감사 교차 참조

- **MRL-T4** (commit-rollback-recovery-contract): 롤백 계약 관련 — XC-ERR-T3와 부분 중첩
- **MCP-T4** (destructive-ops-recovery): 파괴적 작업 복구 — XC-ERR-T3와 부분 중첩
- **ROP-T2** (soft-failure-audit): soft_failure 감사 — XC-ERR-T1과 보완 관계
- **상기 트랙들과 중복되는 finding은 교차 참조 표시 후 제외**
