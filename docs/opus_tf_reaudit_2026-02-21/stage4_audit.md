# Stage 4 Opus TF Audit Report

**Date**: 2026-02-21
**Scope**: `stage4_orchestrator.py`, `stage4_interview_round.py`, `stage4_post_processor.py`, `stage4_context_builder.py`, `stage4_context.py`, `stage4_types.py`, `chief_writer.py`, `chief_writer_context.py`, `chief_writer_quality.py`

## Findings

### S4-01. CoVe REJECT on final round loses state_updates and title
- **TF**: TF-2 (Data flow)
- **Severity**: IMPORTANT
- **File**: `modules/core/stage4_orchestrator.py:568-574`
- **Content**: CoVe 사후검증 REJECT 시 `previous_attempt`에 `state_updates` 미포함. 사용자가 마지막 best를 강제 수락하면 `final_state_updates = {}` → martial tracker/HUD 갱신 누락.
- **Impact**: CoVe REJECT + 강제 수락 시 상태 추적 소실
- **Difficulty**: LOW
- **Previous**: NEW

### S4-02. Post-processor uses arc_data.state_changes instead of final_state_updates for WorldState/FactLedger
- **TF**: TF-2 (Data flow)
- **Severity**: IMPORTANT
- **File**: `modules/core/stage4_post_processor.py:429,450,166`
- **Content**: WorldState(L429), FactLedger(L450), 벡터 메모리(L166)가 Director 추출 `final_state_updates` 대신 Arc 계획 `arc_data.state_changes` 사용. 매 에피소드 동일한 Arc 레벨 변경사항 반복 적용.
- **Impact**: V68 장기 일관성 시스템(WorldState/FactLedger)에 부정확한 상태 누적
- **Difficulty**: MEDIUM
- **Previous**: NEW

### S4-07. Quality regression detection checks Stage 2 instead of Stage 4
- **TF**: TF-3 (Validation)
- **Severity**: IMPORTANT
- **File**: `modules/core/stage4_post_processor.py:509`
- **Content**: `detect_score_regression(stage=2)` — Stage 4 후처리에서 Stage 2 점수 회귀 감지. `stage=4` 여야 함.
- **Impact**: 원고 품질 회귀 경고가 Arc 점수 추세를 보여줌
- **Difficulty**: LOW
- **Previous**: NEW

### S4-03. time_warnings accumulate across rounds within same episode
- **TF**: TF-3 (Validation)
- **Severity**: INSIGHT
- **File**: `modules/core/stage4_interview_round.py:288,653`
- **Content**: CoVe REJECT 후 다음 라운드에 이전 라운드의 스테일 시간 경고 전달
- **Impact**: Advisory용이라 실질 영향 낮음
- **Difficulty**: LOW
- **Previous**: NEW

### S4-04. CoVe rejection overwrites all accumulated director_feedback
- **TF**: TF-1 (LLM interaction)
- **Severity**: INSIGHT
- **File**: `modules/core/stage4_orchestrator.py:567`
- **Content**: CoVe 피드백이 이전 REJECT 피드백 전체를 덮어씀
- **Impact**: Writer가 이전 라운드 문제 반복 가능
- **Difficulty**: LOW
- **Previous**: NEW

### S4-05. Mandatory context truncation removes back sections indiscriminately
- **TF**: TF-1 (LLM interaction)
- **Severity**: INSIGHT (downgraded from IMPORTANT — designed behavior with logging)
- **File**: `modules/core/stage4_orchestrator.py:438-439`
- **Content**: 80K 초과 시 뒤에서부터 섹션 제거. 벡터 메모리, 페이싱 분석 등이 먼저 절삭됨.
- **Impact**: 장기연재(30화+)에서 벡터 메모리 컨텍스트 손실 가능
- **Difficulty**: MEDIUM
- **Previous**: NEW

### S4-06. prev_manuscripts_text loaded twice independently
- **TF**: TF-4 (Resource waste)
- **Severity**: INSIGHT
- **File**: `modules/core/stage4_interview_round.py:442-452` vs `stage4_context_builder.py:130-147`
- **Content**: 동일 범위 원고를 context_builder와 interview_round에서 별도 DB 조회
- **Impact**: 라운드당 최대 30회 중복 DB 호출
- **Difficulty**: LOW
- **Previous**: NEW

### S4-08. Empty manuscript candidates pass through to Director
- **TF**: TF-3 (Validation)
- **Severity**: INSIGHT
- **File**: `modules/domain/agents/chief_writer.py:292-300,366-379`
- **Content**: 타임아웃/크래시 시 빈 원고 후보가 Director에 전달. Director가 빈 후보 선택 가능성 이론적으로 존재.
- **Impact**: 실질적으로 Director가 최장/최고 후보 선택하므로 낮음
- **Difficulty**: LOW
- **Previous**: NEW

### S4-09. cumulative_bible collected but never passed to writer
- **TF**: TF-2 (Data flow)
- **Severity**: INSIGHT
- **File**: `modules/core/stage4_context_builder.py:172,203`
- **Content**: DB에서 로딩하지만 dead_npcs만 추출, 나머지 데이터 미사용
- **Impact**: 누적 바이블 데이터 낭비
- **Difficulty**: LOW
- **Previous**: NEW

### S4-10. save_manuscript commits before update_martial_tracker
- **TF**: TF-4 (Transaction safety)
- **Severity**: INSIGHT
- **File**: `modules/core/stage4_post_processor.py:119,125`
- **Content**: `save_manuscript()`가 내부 커밋 후 `update_martial_tracker()` 실패 시 원고만 저장, 트래커 소실. 롤백 부분적.
- **Impact**: 트래커 실패 시 에피소드 진행 차단 + 원고 중복 가능
- **Difficulty**: MEDIUM
- **Previous**: NEW

### S4-11. Patch mode single_strategy filter may not match strategy key format
- **TF**: TF-1 (LLM interaction)
- **Severity**: INSIGHT
- **File**: `modules/domain/agents/chief_writer.py:785`
- **Content**: `selected_strategy_key`가 "A"/"후보1" 형태면 필터 불일치 → 3개 전략 모두 생성
- **Impact**: 토큰 낭비, 동작 정상
- **Difficulty**: LOW
- **Previous**: NEW

### S4-12. Smart truncation section-split pattern misses non-bracket headers
- **TF**: TF-1 (LLM interaction)
- **Severity**: INSIGHT
- **File**: `modules/core/stage4_orchestrator.py:430-431`
- **Content**: `\n[` 패턴으로만 분할 → `### ` 헤더 섹션 병합
- **Impact**: 절삭 세밀도 저하, 기능적 영향 낮음
- **Difficulty**: LOW
- **Previous**: NEW

### S4-13. ChiefWriter manuscript cache thread safety (read-only, safe)
- **TF**: TF-4 (Thread safety)
- **Severity**: INSIGHT
- **File**: `modules/domain/agents/chief_writer.py:844-856`
- **Content**: 캐시가 병렬 실행 중 읽기 전용 — 현재 안전, 유지보수 주의
- **Impact**: 없음
- **Difficulty**: N/A
- **Previous**: NEW

## Summary: 0 CRITICAL, 3 IMPORTANT, 10 INSIGHT
