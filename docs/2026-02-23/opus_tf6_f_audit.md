# TF-6-F: 크로스-모듈 계약 검증 (Cross-Module Contracts)

## 감사 범위
- 파일: `modules/core/stage2_finalizer.py`, `modules/core/stage3_orchestrator.py`, `modules/core/stage4_context.py`, `modules/core/stage2_context.py`, `modules/domain/agents/block_enricher.py`, `modules/validation/blocking_validator.py`, `modules/validation/blocking_validator_scene_checks.py`
- 코드 줄 수: 약 900줄 수동 확인

## 발견 사항

### [TF-F-1] BlockingValidator 하위 체크가 `manuscript: str` 계약 위반 시 예외를 직접 유발 (MEDIUM)
- **파일**: `modules/validation/blocking_validator.py:56`, `modules/validation/blocking_validator_scene_checks.py:30`, `modules/validation/blocking_validator_scene_checks.py:67`, `modules/validation/blocking_validator_scene_checks.py:119`
- **현재 코드**:
```python
# blocking_validator.py
def validate(self, manuscript: str, validation_context: dict) -> dict:
    ...

# blocking_validator_scene_checks.py
length = len(manuscript)
if any(kw in manuscript for kw in keywords if kw):
manuscript_length = len(manuscript)
```
- **문제**: 상위 계약은 `str`을 가정하지만 하위에서 강제 정규화가 없어 `None`/비문자 입력 시 TypeError가 즉시 발생한다.
- **영향**: 예외 경로에서 validator 자체가 실패하면, 원래 의도한 `REJECT 결과 dict` 대신 파이프라인 중단이 발생할 수 있다.
- **수정안**: `validate()` 진입에서 타입 정규화(`manuscript = manuscript if isinstance(manuscript, str) else str(manuscript or "")`)를 공통 적용.
- **테스트**: `validate(None, {...})`, `validate({"x":1}, {...})`가 예외 없이 결과 dict를 반환하는지 검증.

## 요약
| 심각도 | 건수 |
|--------|------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 1 |
