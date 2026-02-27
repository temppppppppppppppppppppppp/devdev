# 1M 컨텍스트 감리 체크리스트

작성일: 2026-02-27  
목적: "Gemini 1M 컨텍스트 최대 활용" 정책이 코드/설정/운영에서 실제로 일치하는지 검증

---

## 1. 단위 검증

- [ ] `1M = 1,000,000 = 1000k`, `100k = 100,000 = 0.1M` 문서화
- [ ] `tokens`와 `chars`를 같은 표에 분리 표기
- [ ] 정책 문서/코드 주석에서 단위 혼용 표현 제거

## 2. 전역 게이트

- [ ] `config/system.yaml`의 `api.max_context_chars` 목표값 확인
- [ ] `modules/domain/agents/base_agent.py` `_apply_prompt_size_gate()` 적용 확인
- [ ] `modules/core/constants.py` `ContextLimits.MAX_CONTEXT_CHARS` 충돌 여부 확인
- [ ] 런타임 로드값(`_threshold`/상수)이 설정값과 동일한지 확인

## 3. Stage/Director 예산

- [ ] `config/settings/validation.yaml` `smart_retrieval.stage4_total_budget` 확인
- [ ] `config/settings/validation.yaml` `smart_retrieval.director_total_budget` 확인
- [ ] `context.mandatory_context_max` / `context.director_mandatory_max` 확인
- [ ] 코드 fallback 하드코드 기본값이 정책과 불일치하지 않는지 확인

## 4. 숨은 절삭 경로

- [ ] `[:50000]`, `[:30000]` 등 하드컷 전수 검색
- [ ] `mandatory_context` 조립 이후 추가 절삭 경로 확인
- [ ] `smart_truncate` 호출 지점별 `max_chars` 검토
- [ ] 캐시 실패 fallback에서 후보 원고/출력 포맷이 잘리지 않는지 확인

## 5. Director 캐싱

- [ ] Stable/Variable 프롬프트 분리 적용 확인
- [ ] 캐시 hit/miss/fallback 경로별 로그 확인
- [ ] 캐시 실패 시 legacy 동작과 기능 동등성 확인
- [ ] TTL/최소 캐시 길이 설정이 운영 패턴과 맞는지 확인

## 6. 성능/품질 검증

- [ ] 관련 테스트 통과 (`director`, `stage4_context_builder`, `critic`)
- [ ] 장문 컨텍스트 E2E 1회 이상 실행
- [ ] 샘플 호출에서 입력 chars/tokens 로깅 확인
- [ ] cache hit vs miss 비용/지연 비교

## 7. 승인 기준

- [ ] "1M 정책표"와 코드/설정 값 100% 일치
- [ ] `100k/200k/700k/1M` 각 값의 의미와 적용 위치 문서화
- [ ] 리그레션 테스트/로그 알람으로 정책 드리프트 감시 가능

---

## 감리 결과 기록

- 감리 일시:
- 감리자:
- 결론: `PASS` / `FAIL`
- 핵심 이슈:
- 후속 액션:

