# TF-7-J: Emotion / Foreshadow / Karma / Catharsis 시스템 — 감사 실행 오더

> **Opus TF-7-J** | 2026-02-23
> **담당**: Opus 에이전트 J
> **출력**: `docs/2026-02-23/opus_tf7_j_audit.md`
> **수칙**: 수정 금지 / 수동 코드 조사만 / 근거 필수

---

## 배경
독자 대리만족 프레임워크(D 완료, Step 1~5)에서 구현된 4개 모듈. TF에서 감사 미실시. `karma_service.py`가 24줄로 매우 짧아 스텁(미구현) 가능성 있음. 파이프라인 배선(실제 호출 경로) 확인 필요.

---

## 실행 순서

### Step 1: KarmaService 구현 확인
**파일**: `modules/core/karma_service.py` (24줄)
- Read 도구로 전체 파일 읽기 (짧으므로 한 번에)
- 실제 구현 여부: 메서드 내용이 `pass`, `raise NotImplementedError`, 또는 실제 로직인지
- 스텁으로 판단 시: HIGH 이슈 등록 (카르마 시스템 미작동)
- 실제 구현이면: DB 저장 경로, NPC별 카르마 추적 방식 확인

### Step 2: EmotionTracker 스냅샷 저장
**파일**: `modules/core/emotion_tracker.py` (397줄)
- Read 도구로 전체 파일 읽기
- 감정 상태 저장 방식: 에피소드별 스냅샷 DB 테이블인지, 단일 인메모리 상태인지
- 롤백 시 감정 상태 복구: `rollback_to(ep_num)` 또는 유사 메서드 존재 여부
- 감정 상태 직렬화 시 `ensure_ascii=False` 여부 (한글 감정 레이블)
- `stage4_post_processor.py` 또는 `director.py`에서 호출 여부 확인

### Step 3: ForeshadowTracker 회수 에피소드 기록
**파일**: `modules/core/foreshadow_tracker.py` (544줄)
- Read 도구로 전체 파일 읽기
- 복선 항목 스키마: `{"id", "ep_planted", "ep_resolved", "content", "resolved": bool}`
- 복선 회수 시 `ep_resolved` 기록 여부
- 롤백 후 `ep_resolved > target_ep` 인 항목을 미회수로 되돌리는 로직
- 미회수 복선 목록 조회 메서드 확인

### Step 4: CatharsisTimer ZeroDivision 방어
**파일**: `modules/validation/catharsis_timer.py`
- 파일 크기 확인 후 Read
- 카타르시스 타이밍 계산 공식
- `ep_count` 또는 총 에피소드 수가 0인 경우 분모 방어 (`if ep_count == 0` 또는 `max(1, ep_count)`)
- 타이밍 결과를 Director 또는 Stage4에 전달하는 경로

### Step 5: 파이프라인 배선 확인
- `stage4_orchestrator.py`에서 4개 모듈 호출 경로 확인
- `stage4_post_processor.py`에서 감정/복선/카르마/카타르시스 데이터 활용 경로
- `director.py`에서 카타르시스 타이밍 기반 원고 평가 경로
- 배선되지 않은 모듈은 "Dead Feature" 이슈로 등록

---

## 이슈 분류 기준
| 항목 | 등급 |
|------|------|
| karma_service.py 스텁 | HIGH |
| 롤백 시 감정/복선 상태 복구 불가 | HIGH |
| 파이프라인 미배선 (Dead Feature) | MEDIUM |
| ep_count=0 분모 오류 | MEDIUM |

## 출력 파일 구조
```
# TF-7-J 감사 보고서 — Emotion / Foreshadow / Karma / Catharsis

## 감사 파일 목록
## 발견 이슈 (총 N건)
### [TF-7-J-1] karma_service.py 스텁 여부
...
## 파이프라인 배선 현황 테이블 (4개 모듈 × 호출 경로)
## [FP] 오탐 목록
## 요약 테이블
```
