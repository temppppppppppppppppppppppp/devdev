# TF-6-D: LLM 응답 견고성 (LLM Response Robustness)

## 감사 범위
- 파일: `modules/domain/agents/base_agent.py`, `modules/domain/agents/analyst.py`, `modules/domain/agents/arc_critic.py`, `modules/domain/agents/arc_corrector.py`, `modules/domain/agents/chief_writer.py`, `modules/domain/agents/director.py`, `modules/domain/agents/director_continuity.py`, `modules/domain/agents/four_phase_arc_generator.py`
- 코드 줄 수: 약 1,400줄 수동 확인

## 발견 사항

### [TF-D-1] BaseAgent 백업 응답 검증이 에이전트 공통 키셋에 과도 의존 (MEDIUM)
- **파일**: `modules/domain/agents/base_agent.py:741`, `modules/domain/agents/base_agent.py:896`, `modules/domain/agents/base_agent.py:900`
- **현재 코드**:
```python
validation = self._validate_response(backup_text)
...
key_fields = ["content", "tactical_doc", "integrated_scenario", "title", "state_updates"]
has_key_field = any(f'"{field}"' in response for field in key_fields)
if not has_key_field:
    return {"valid": False, "reason": "핵심 필드 없음"}
```
- **문제**: 백업 모델 응답 검증이 일부 에이전트 전용 키만 허용해, `{"decision": "PASS"}` 같은 유효 JSON도 부정 처리할 수 있다.
- **영향**: 불필요한 fallback/오류 응답 증가, 재시도 비용 상승.
- **수정안**: 에이전트별 필수 키를 설정값으로 분리하거나, JSON 구조 유효성 검증과 도메인 키 검증을 분리.
- **테스트**: Director/Validator 계열 최소 응답(`decision`, `conflicts`)이 backup 경로에서 valid 처리되는지 단위 테스트 추가.

## 요약
| 심각도 | 건수 |
|--------|------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 1 |
