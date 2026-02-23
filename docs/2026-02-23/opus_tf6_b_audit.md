# TF-6-B: 상태 누적 / 메모리 성장 (State Accumulation)

## 감사 범위
- 파일: `modules/domain/agents/state_tracker.py`, `modules/domain/agents/state_tracker_plots.py`, `modules/core/db_manager.py`, `modules/domain/agents/state_tracker_npc.py`, `modules/core/data_collector.py`
- 코드 줄 수: 약 900줄 수동 확인

## 발견 사항

### [TF-B-1] `resolved_plots` 저장소는 무제한 누적, 출력만 제한됨 (MEDIUM)
- **파일**: `modules/domain/agents/state_tracker.py:132`, `modules/domain/agents/state_tracker_plots.py:117`, `modules/domain/agents/state_tracker_plots.py:128`
- **현재 코드**:
```python
# state_tracker.py
self.resolved_plots: list[dict] = []

# state_tracker_plots.py
self.tracker.resolved_plots.append(entry)
recent_items = self.tracker.resolved_plots[-safe_max_items:]
```
- **문제**: 프롬프트 주입은 `max_items`로 제한하지만 실제 저장 리스트는 상한이 없다.
- **영향**: 장기 연재(수백 화)에서 메모리 증가 및 직렬화 비용 증가.
- **수정안**: 저장 시점에 상한 도입(예: `resolved_plots_max`) 후 오래된 항목 제거.
- **테스트**: 1,000개 삽입 후 `len(resolved_plots) <= cap` 보장 확인.

### [TF-B-2] cumulative bible의 `all_reveals`가 무한 확장됨 (MEDIUM)
- **파일**: `modules/core/db_manager.py:849`, `modules/core/db_manager.py:901`
- **현재 코드**:
```python
cumulative = { ..., "all_reveals": [] }
...
cumulative["all_reveals"].extend(reveals)
```
- **문제**: `items/npcs`와 달리 `all_reveals`는 중복 제거/상한 없이 누적된다.
- **영향**: 대형 프로젝트에서 상태 집계 비용과 메모리 사용량 증가.
- **수정안**: `all_reveals`도 상한/중복 제거 정책 적용(예: 최근 N개 + 해시 기반 dedupe).
- **테스트**: reveal 중복/대량 입력 시 결과 길이와 성능 지표 검증.

### [TF-B-3] RLHFCollector의 `feedback_log` 인메모리 누적 상한 부재 (MEDIUM)
- **파일**: `modules/core/data_collector.py:350`, `modules/core/data_collector.py:383`, `modules/core/data_collector.py:406`
- **현재 코드**:
```python
self.feedback_log = []
...
self.feedback_log.append(feedback)
...
for feedback in self.feedback_log:
    out.write(...)
```
- **문제**: 파일 저장은 즉시 수행하지만 메모리 로그는 무제한 유지된다.
- **영향**: 장시간 실행 시 프로세스 메모리 점유가 지속 증가.
- **수정안**: `deque(maxlen=N)` 또는 append 후 즉시 flush-only 모드 제공.
- **테스트**: 10k 건 수집 시 메모리 증가율 상한 확인.

## 요약
| 심각도 | 건수 |
|--------|------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 3 |
