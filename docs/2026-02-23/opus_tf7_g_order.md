# TF-7-G: Narrative Diversity / Repetition / Pattern Tracker — 감사 실행 오더

> **Opus TF-7-G** | 2026-02-23
> **담당**: Opus 에이전트 G
> **출력**: `docs/2026-02-23/opus_tf7_g_audit.md`
> **수칙**: 수정 금지 / 수동 코드 조사만 / 근거 필수

---

## 배경
반복 탐지 시스템이 3개 모듈로 분산 구현됨. 크로스 에피소드 반복 감지(3-B)와 SemanticPlotGuard 키워드 폴백(C-1) 완료. 3개 모듈이 서로 중복 탐지하는지, `validation_orchestrator`에서 올바르게 오케스트레이션되는지 미검증.

---

## 실행 순서

### Step 1: NarrativeDiversity 점수 계산
**파일**: `modules/core/narrative_diversity.py` (592줄)
- Read 도구로 전체 파일 읽기
- 다양성 점수 계산 알고리즘: 임베딩 기반인지, TF-IDF인지, 키워드 기반인지
- 초기 에피소드(1~3화) 샘플 부족 시 점수 처리: 기본값 vs 0 vs 1.0
- 장르별 다양성 기준 분기 여부 — 무협/헌터 장르에서 전투 반복 허용 로직

### Step 2: InformationDiffusion NPC 목록 소스
**파일**: `modules/core/information_diffusion.py` (441줄)
- Read 도구로 전체 파일 읽기
- NPC 목록 조회 경로: `state_tracker.get_npcs()` vs DB 직접 쿼리 vs DI 주입
- stale NPC 목록 사용 위험: `state_tracker` 캐시 미무효화 시
- `information_diffusion` 계산에 `deceased` NPC 포함 여부

### Step 3: PatternTracker 크기 제한
**파일**: `modules/core/pattern_tracker.py` (936줄)
- 1~470줄 읽기
- 471~936줄 읽기
- 패턴 DB 항목 자료구조: `list`, `dict`, DB 테이블 중 어느 것인가
- 최대 항목 수 제한 여부 (TF-6 TF-B 계열 패턴)
- `pattern_tracker`와 `repetition_guard` 간 중복 탐지 범위 비교

### Step 4: RepetitionGuard 폴백 체인
**파일**: `modules/core/repetition_guard.py`
- Read 도구로 전체 파일 읽기
- C-1 패치 확인: 임베딩 실패 시 키워드 폴백 경로 존재
- 키워드 폴백도 실패 시 최종 폴백: PASS vs REJECT vs 예외
- `validation_orchestrator`에서 `repetition_guard`와 `pattern_tracker` 모두 호출하는지 확인

### Step 5: 중복 탐지 오케스트레이션
**파일**: `modules/validation/validation_orchestrator.py` (관련 섹션만)
- narrative_diversity, information_diffusion, pattern_tracker, repetition_guard 호출 위치 찾기
- 호출 순서: 순차인지 병렬인지
- 결과 집계 방식: 하나만 REJECT이면 전체 REJECT인지, 다수결인지

---

## 출력 파일 구조
```
# TF-7-G 감사 보고서 — Narrative Diversity / Repetition / Pattern

## 감사 파일 목록
## 발견 이슈 (총 N건)
### [TF-7-G-1] ...
## [FP] 오탐 목록
## 중복 탐지 범위 비교 테이블 (3개 모듈별 감지 대상)
## 요약 테이블
```
