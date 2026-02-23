# TF-7-G 감사 보고서 — Narrative Diversity / Repetition / Pattern

## 감사 파일 목록
- `modules/core/narrative_diversity.py`
- `modules/core/information_diffusion.py`
- `modules/core/pattern_tracker.py`
- `modules/core/repetition_guard.py`
- `modules/validation/validation_orchestrator.py`
- `modules/core/stage4_interview_round.py` (호출부 추적)

## 발견 이슈 (총 2건)

### [TF-7-G-1] PatternTracker 상태가 분석 호출 간 누적되어 오탐을 유발함 (HIGH)
**파일**: `modules/core/pattern_tracker.py`  
**줄**: `121`, `137`, `151`, `155`, `173`, `181`, `186`, `197`, `268`

**현재 코드**:
```python
self.pattern_history = {
    "cliche_counts": Counter(),
    "starter_counts": Counter(),
    ...
}
...
def analyze_manuscripts(...):
    recent_ms = manuscripts[-self.window_size:]
    self._analyze_cliches(recent_ms)
    self._analyze_sentence_starters(recent_ms)
...
def _analyze_cliches(...):
    for keyword in self.cliche_keywords:
        count = combined.count(keyword)
        if count > 0:
            self.pattern_history["cliche_counts"][keyword] = count
```

**문제**: `analyze_manuscripts()` 시작 시 `Counter`/히스토리를 리셋하지 않아서, 이전 분석에서 잡힌 키가 다음 분석 데이터에 없어도 남는다.

**영향**: 반복/클리셰 경고가 실제보다 높게 유지되어 `HIGH` 경고, Diversity Sampling 권장/강제 판단이 왜곡될 수 있다(침묵형 품질 저하).

**Caller→Callee 근거**:
- `modules/core/narrative_diversity.py:443`에서 `PatternTracker.analyze_manuscripts()`를 매 분석 주기 호출.
- 이후 `modules/core/pattern_tracker.py:268`의 리포트 생성이 누적된 `pattern_history`를 사용.

**권장 수정 방향**: 분석 시작 시 `pattern_history`를 윈도우 기준으로 재초기화하고, 미검출 키도 0으로 갱신되도록 일관화.

### [TF-7-G-2] 플롯 시퀀스 탐지가 `str.find` 첫 매치만 사용해 유효 패턴을 놓침 (MEDIUM)
**파일**: `modules/core/pattern_tracker.py`  
**줄**: `202`, `210`, `217`, `635`, `639`, `644`

**현재 코드**:
```python
for keyword in pattern:
    pos = ms.find(keyword)
    if pos == -1:
        break
    positions.append(pos)
if len(positions) == len(pattern) and positions == sorted(positions):
    ...
```

**문제**: 각 키워드의 "첫 등장 위치"만 비교한다. 앞부분에 다른 맥락의 키워드가 먼저 나오면, 뒤에 올바른 순서로 다시 등장해도 탐지 실패(거짓 음성).

**영향**: 반복 플롯 경향을 과소탐지하여 경고 누락, 다양성 제어 약화.

**Caller→Callee 근거**:
- `analyze_manuscripts()` → `_analyze_plot_patterns()` (`modules/core/pattern_tracker.py:162`, `202`)
- 장르 확장 경로 `analyze_genre_patterns_v59()` → `_check_pattern_sequence()` (`modules/core/pattern_tracker.py:592`, `635`)

**권장 수정 방향**: 이전 매치 이후 위치에서 다음 키워드를 탐색하는 순차 매칭(포인터 기반)으로 전환.

## Risk (총 1건)

### [TF-7-G-R1] InformationDiffusion 전파 경로에 deceased 필터가 없어 호출자 의존성이 큼 (MEDIUM, Risk)
**파일**: `modules/core/information_diffusion.py`  
**줄**: `365`, `392`, `397`, `406`

**현재 코드**:
```python
for npc_name, npc_location in npc_locations.items():
    if self.npc_knows(npc_name, event_id):
        continue
    ...
    if time_passed >= required_time:
        self.grant_knowledge(...)
```

**위험**: `npc_locations`에 사망 NPC가 포함되어도 모듈 내부에서 제외하지 않는다. 지식 전파가 "호출자 전처리"에 전적으로 의존한다.

**Bug-vs-intent 근거**: 함수 시그니처가 위치 맵만 받도록 설계되어 상태(생존/사망) 정보가 없는 구조다. 즉시 버그 단정보다는 계약 리스크로 분류.

**Open Question**: 실제 호출부가 항상 alive NPC만 전달하는지 계약 문서/테스트 확인 필요.

## [FP] 오탐 목록

### [FP-1] ValidationOrchestrator가 `pattern_tracker`와 `repetition_guard`를 동시에 직접 호출해 중복 경고를 만든다
- **판정**: 오탐
- **수동 근거**:
  - `modules/validation/validation_orchestrator.py:26-32` import 목록에 두 모듈 없음.
  - `modules/validation/validation_orchestrator.py:1382-1393`은 `validation_context['pattern_analysis']`만 소비.
- **의도 확인**: 오케스트레이터는 패턴 분석 "소비자"이며 직접 실행기가 아님.

### [FP-2] `repetition_guard` 폴백 체인이 실패 시 REJECT를 유발한다
- **판정**: 오탐
- **수동 근거**:
  - `modules/core/repetition_guard.py:86-87`, `modules/core/repetition_guard.py:92-93` → 데이터 부족 시 `([], 1.0)` 반환.
  - `modules/core/repetition_guard.py:138-139` → 위반 없으면 빈 프롬프트.
- **의도 확인**: 기본 동작은 비차단(advisory)이며 실패 시 안전 통과.

### [FP-3] 초기 에피소드 샘플 부족 시 다양성 점수가 0으로 고정된다
- **판정**: 오탐
- **수동 근거**:
  - `modules/core/pattern_tracker.py:787-788` → 문장 5개 미만이면 `50` 반환(중립 기본값).
- **의도 확인**: 초기 구간 과벌점 방지를 위한 완충 설계.

## 중복 탐지 범위 비교 테이블

| 모듈 | 주 감지 대상 | 핵심 방식 | 결과 성격 | 비고 |
|---|---|---|---|---|
| `pattern_tracker.py` | 플롯/클리셰/문장시작/반응 패턴 | 키워드+카운터 기반 | 경고/샘플링 권장 | 다양성 제어의 상위 입력 |
| `repetition_guard.py` | 문구 3-gram 반복 + 문장 해시 | n-gram/sha256 | 비차단 경고 | 데이터 부족 시 PASS 폴백 |
| `manuscript_validator.py` | 크로스 에피소드 씬 중복 (`_check_cross_episode_duplication`) | 5-gram 교집합 | 경고 | Stage4 후보 사전 점검용 |
| `validation_orchestrator.py` | 패턴 결과 소비(`pattern_analysis`) | 컨텍스트 기반 임계값 조정 | 점수 임계값 조정 | 직접 감지 실행은 하지 않음 |

## 요약 테이블

| 심각도 | 건수 | 항목 |
|---|---:|---|
| HIGH | 1 | `TF-7-G-1` |
| MEDIUM | 1 | `TF-7-G-2` |
| Risk | 1 | `TF-7-G-R1` |
| FP | 3 | `FP-1~3` |

| 체크포인트 | 결과 |
|---|---|
| G-1 중복 탐지 경합 | 직접 중복 호출 경합은 미확인(소비 분리) |
| G-2 초기 샘플 부족 처리 | 중립 점수(50)로 완충 |
| G-3 NPC 소스 정합성 | 내부 소스 없음, 호출자 주입 계약 의존 |
| G-4 패턴 저장소 상한 | 윈도우 기반이지만 상태 리셋 누락으로 오염 발생 |
| G-5 RepetitionGuard 최종 폴백 | PASS(비차단) |
| G-6 장르별 다양성 기준 | 장르 프로파일/패턴 분기 존재 (`pattern_tracker` V59) |
| G-7 오케스트레이터 호출 순서 | 패턴 모듈 직접 호출 없음, `pattern_analysis` 입력 의존 |
