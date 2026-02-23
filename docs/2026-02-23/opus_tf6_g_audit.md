# TF-6-G: 임계값 / 매직넘버 외부화 (Threshold Externalization)

## 감사 범위
- 파일: `modules/domain/agents/base_agent.py`, `modules/core/stage4_interview_round.py`, `modules/core/stage2_validation_pipeline.py`, `modules/validation/scoring_validator.py`, `config/settings/validation.yaml`
- 코드 줄 수: 약 1,500줄 수동 확인

## 발견 사항

### [TF-G-1] Stage4 Interview Round의 슬롯 절단/엔티티 캡이 하드코딩 유지 (MEDIUM)
- **파일**: `modules/core/stage4_interview_round.py:475`, `modules/core/stage4_interview_round.py:479`, `modules/core/stage4_interview_round.py:488`
- **현재 코드**:
```python
_slot_max = ... or 1500
_slot_npcs = _npc_roster[:5]
if len(_slot_npcs) >= 5:
    break
```
- **문제**: `validation.yaml` 조정 없이 코드 수정이 필요한 고정값이다.
- **영향**: 장르/프로젝트별 retrieval 민감도 튜닝 비용 증가.
- **수정안**: `smart_retrieval.slot_max_chars_default`, `smart_retrieval.max_npcs_per_slot`로 외부화.
- **테스트**: 설정값 변경 시 로그/출력 길이와 NPC 선택 개수가 즉시 반영되는지 확인.

### [TF-G-2] Stage2 Flow Guard 핵심 임계값 다수가 코드 상수 (MEDIUM)
- **파일**: `modules/core/stage2_validation_pipeline.py:626`, `modules/core/stage2_validation_pipeline.py:652`, `modules/core/stage2_validation_pipeline.py:688`, `modules/core/stage2_validation_pipeline.py:720`
- **현재 코드**:
```python
len(beats) < max(3, ep_count)
avg_words < 6 or any(c < 4 ...)
if diversity < 0.6
if stagnation_hits >= 3
```
- **문제**: 이미 threshold 체계가 있는 파일인데 일부 핵심 컷오프가 분리되지 않았다.
- **영향**: 장르별 품질 기준 조정 시 코드 배포가 필요.
- **수정안**: `scope.min_beats_floor`, `scope.min_avg_words`, `scope.min_word_per_beat`, `scope.min_diversity`, `scope.max_stagnation_hits` 외부화.
- **테스트**: YAML만 바꿔 동일 입력의 PASS/REJECT가 의도대로 변하는지 검증.

### [TF-G-3] ScoringValidator의 휴리스틱 밴드가 코드에 고정됨 (MEDIUM)
- **파일**: `modules/validation/scoring_validator.py:107`, `modules/validation/scoring_validator.py:470`, `modules/validation/scoring_validator.py:473`, `modules/validation/scoring_validator.py:1108`, `modules/validation/scoring_validator.py:1121`
- **현재 코드**:
```python
return sanitized[:3000]
if 0.35 <= cv <= 0.55: ...
if martial_count < 3: ...
if system_count < 5: ...
```
- **문제**: 합격선(`pass_threshold`)은 외부화됐지만 세부 채점 규칙은 대부분 하드코딩이다.
- **영향**: 장르별 판정 민감도 실험 시 코드 수정이 필수.
- **수정안**: CV/TTR/장르 키워드 컷오프를 `scoring.*` 하위 키로 외부화.
- **테스트**: 장르별 컷오프 변경 회귀 테스트(동일 원고 점수 변화 예상치 검증).

### [TF-G-4] BaseAgent 안전성/캐시 상수 일부 미외부화 (MEDIUM)
- **파일**: `modules/domain/agents/base_agent.py:959`, `modules/domain/agents/base_agent.py:1034`, `modules/domain/agents/base_agent.py:1035`, `modules/domain/agents/base_agent.py:1138`, `modules/domain/agents/base_agent.py:1184`
- **현재 코드**:
```python
_MAX_JSON_PAYLOAD = 500_000
MAX_DEPTH = 20
_MAX_VISITS = 100
_CONTEXT_CACHE_MAX = 50
if len(content) < 50000:  # cache skip
```
- **문제**: 운영 튜닝 대상 값들이 코드 내부 상수로 남아 있다.
- **영향**: 프로젝트 규모별 API/메모리 튜닝을 런타임 설정으로 제어하기 어렵다.
- **수정안**: `retry.max_json_payload`, `cache.context_max_entries`, `cache.min_content_chars` 등으로 외부화.
- **테스트**: 극단 입력(대형 JSON, 캐시 폭주)에서 YAML 조정만으로 동작 변화 확인.

## 요약
| 심각도 | 건수 |
|--------|------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 4 |
