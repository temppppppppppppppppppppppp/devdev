# S4 LLM 통합 실행문서

> 생성일: 2026-03-18
> 상태: 활성
> 정규 경로: `docs/2026-03-18/OPUS/ssot_execution/s4-llm-integration-execution.md`
> 소스 SSOT: `docs/2026-03-18/OPUS/ssot/s4-llm-integration.md`
> 소스 감리: 6-pass 적대적 감리 (확신도 93%), 모델 선정 보고서 (확신도 86%)
> 감리 문서:
>   - `docs/2026-03-18/OPUS/geuldobi-v2-llm-integration-deepdive-3pass-audit.md`
>   - `docs/2026-03-18/OPUS/geuldobi-v2-llm-deepdive-adversarial-3pass-correction.md`
>   - `docs/2026-03-18/OPUS/geuldobi-v2-llm-deepdive-final-6pass-verdict.md`
>   - `docs/2026-03-18/OPUS/geuldobi-v2-llm-model-selection-report.md`

---

## 1. 목적

S4 SSOT에서 확정된 24건의 실질 이슈(HIGH 2, MEDIUM 11, LOW 11)와 컨텍스트 캐싱/멀티 프로바이더 전환 항목을 실행 가능한 작업 단위로 분해하여, 구체적인 완료 기준과 추정 공수를 부여한다.

---

## 2. 실행 항목 총괄표

### 2.1 HIGH 우선순위 (2건)

| ID | 항목 | 우선순위 | 상세 | 완료 기준 | 추정 공수 | 의존성 | S4 근거 |
|----|------|---------|------|----------|----------|--------|---------|
| EX-H1 | anyOf 스키마 5곳 타입 고정화 | P0 | `response_schemas.py` L518/L528/L534/L572/L585의 `anyOf=[OBJECT, STRING]` 패턴을 단일 타입(OBJECT 또는 ARRAY)으로 고정. 하류 13곳의 isinstance 가드를 정리하고, 약한 가드 1곳(`confidence_calibration.py` L256의 `or []` 패턴)을 isinstance 검사로 교체. 타입 고정 후 Gemini API에서 비결정적 string 반환이 불가능해지므로, 신규 소비자 추가 시 isinstance 누락 리스크를 근본 제거 | (1) `response_schemas.py` 5곳에서 anyOf 제거, 단일 타입 고정 완료 (2) `confidence_calibration.py` L256의 약한 가드를 isinstance 검사로 교체 (3) 기존 13곳 isinstance 가드 중 불필요해진 것 정리 (4) Stage 3 Blueprint 생성 + Stage 4 원고 생산 E2E 통과 (5) `test_blueprint_patch_mode.py` 전건 통과 | 4시간 | 없음 | S4 SSOT 10.1 H1, response_schemas.py L518-596 |
| EX-H2 | API 키 전체 소진 시 경고 로그 추가 | P0 | `base_agent.py` L224-226에서 `return None` 시 `logging.critical()` 경고 추가. 운영자에게 키 소진 사실을 즉시 전달. 선택적으로 `requires_human_intervention = True` 설정 및 MetricsCollector에 키 소진 이벤트 기록. **교정 코드**: `python # base_agent.py L224-226, ADD before return None: logging.critical("[KEY-EXHAUSTED] All %d API keys exhausted", len(cls._api_keys))` | (1) `base_agent.py` L224-226에 `logging.critical("[KEY-EXHAUSTED] All API keys exhausted...")` 추가 (2) 모든 키 소진 시나리오에서 CRITICAL 로그 출력 확인 (3) 기존 키 회전 테스트 통과 | 1시간 | 없음 | S4 SSOT 10.1 H2, base_agent.py L224-226 |

### 2.2 MEDIUM 우선순위 (11건)

| ID | 항목 | 우선순위 | 상세 | 완료 기준 | 추정 공수 | 의존성 | S4 근거 |
|----|------|---------|------|----------|----------|--------|---------|
| EX-M1 | 캐시 키 네임스페이스 work_id 필수화 | P1 | `base_agent.py` L1848-1862의 폴백 체인에서 `work_id`가 None일 때 장르까지 폴백하는 문제. content_hash가 2차 격리를 제공하여 실질 오염은 불가능하나, 설계 명확화를 위해 `work_id` 필수화 또는 `work_id` 부재 시 WARNING 로그 발생 | (1) `work_id` 부재 시 `logging.warning()` 추가 (2) 폴백 체인에서 `genre` 단독 사용 시 경고 메시지 포함 (3) 기존 캐시 동작 유지 확인 | 2시간 | 없음 | S4 SSOT 10.2 M1, base_agent.py L1848-1862 |
| EX-M2 | protagonist_name 포맷팅 이스케이핑 적용 | P1 | `writer.py` L166에서 `protagonist_name`이 `_escape_braces()` 없이 f-string에 직접 삽입됨. 다른 에이전트에서는 이스케이핑이 적용되어 불일치 발생. NPC 이름 목록(L117-123)과 소설 제목도 동일하게 미이스케이핑 | (1) `writer.py`에서 `protagonist_name`, NPC 이름, 소설 제목에 `_escape_braces()` 적용 (2) 기존 원고 생성 테스트 통과 (3) 중괄호 포함 이름으로 테스트 시 정상 동작 확인 | 2시간 | 없음 | S4 SSOT 10.2 M2, writer.py L166 |
| EX-M3 | 프롬프트 절단 시 호출자 플래그 검사 경로 보완 | P1 | `base_agent.py` L306-326에서 `requires_human_intervention = True` 설정하나, 이를 검사하지 않는 호출 경로 존재. 문자 기반 절단이므로 한국어 토큰 수와 불일치. 토큰 기반 절단은 범위 외이나, 플래그 미검사 경로 식별 및 검사 추가 필요. **탐색 명령**: `grep -rn "\.ask(" modules/domain/agents/ | grep -v "requires_human_intervention"` | (1) `requires_human_intervention` 플래그를 검사하지 않는 호출 경로 전수 식별 (2) 주요 경로에 플래그 검사 + WARNING 로그 추가 (3) 프롬프트 절단 발생 시 운영자에게 가시적 경고 전달 확인 | 3시간 | 없음 | S4 SSOT 10.2 M3, base_agent.py L306-326 |
| EX-M4 | 연속 호출 비용 상한 모니터링 추가 | P2 | MAX_CONTINUATIONS=5 + backup 1회 = 최대 6회 API 호출 가능. 원본 보고서의 10회 주장은 6-pass에서 오류로 확정. 현재 6회 상한은 합리적이나, 연속 호출 발생 빈도와 비용을 MetricsCollector에 기록하여 모니터링 | (1) 연속 호출(continuation) 횟수를 MetricsCollector에 기록 (2) 3회 이상 연속 호출 시 WARNING 로그 (3) 기존 재시도 로직 동작 무변경 확인 | 2시간 | 없음 | S4 SSOT 10.2 M4, base_agent.py L640 |
| EX-M5 | PASS_WITH_FIX 실패 시 verdict 정합성 개선 | P1 | `three_phase_blueprint_generator.py` L625-645에서 PASS_WITH_FIX 3회 실패 시 `verdict="REJECT"` 설정 후 외부 루프 계속, L631에서 부분 수정본이 `best_blueprint`에 채택됨. REJECT 판정과 부분 채택의 의미적 불일치 해소 | (1) PASS_WITH_FIX 3회 실패 시 부분 채택 여부를 명시적으로 결정하는 분기 추가 (2) 부분 채택 시 메타데이터에 `"partial_fix": True` 표시 (3) `test_blueprint_patch_mode.py` 관련 테스트 통과 | 3시간 | EX-H1 | S4 SSOT 10.2 M5, three_phase*.py L625-645 |
| EX-M6 | finish_reason 과도한 except 범위 축소 | P2 | `gemini_provider.py` L24-30에서 `except Exception`이 SAFETY/RECITATION finish_reason을 "stop"으로 위장. except 범위를 `(AttributeError, IndexError)`로 축소하고, SAFETY/RECITATION은 별도 처리 경로 분기 | (1) `gemini_provider.py` except 범위를 구체적 예외로 축소 (2) SAFETY finish_reason 시 별도 로그 + 빈 응답 구분 가능 (3) RECITATION 감지 시 WARNING 로그 (4) 기존 정상 응답 처리 무변경 확인 | 2시간 | EX-M7 | S4 SSOT 10.2 M6, gemini_provider.py L24-30 |
| EX-M7 | Safety 필터 빈 응답 구분 처리 | P2 | `gemini_provider.py` L18-22에서 Safety 필터 차단 시 빈 응답 반환, 정상 빈 응답과 구분 불가. Safety 차단 시 응답에 메타데이터 표시 추가 | (1) Safety 필터 차단 시 `{"safety_blocked": True}` 또는 별도 플래그 반환 (2) 호출부에서 Safety 차단과 정상 빈 응답 구분 가능 (3) Safety 차단 시 WARNING 로그 포함 | 2시간 | 없음 | S4 SSOT 10.2 M7, gemini_provider.py L18-22 |
| EX-M8 | OpenAI usage 키 매핑 통일 | P2 | `base_agent.py` L276-281에서 Gemini 키(`prompt_token_count`) 기준 코드이므로 OpenAI 사용 시 토큰 카운트 0으로 추정 폴백. 프로바이더별 usage 키를 표준 키로 정규화하는 어댑터 추가 | (1) `_build_metric_usage_payload()` 또는 프로바이더 레벨에서 usage 키를 표준화 (2) OpenAI 프로바이더 사용 시에도 정확한 토큰 카운트 반환 (3) Anthropic 프로바이더도 동일 매핑 적용 | 3시간 | 없음 | S4 SSOT 10.2 M8, base_agent.py L276-281 |
| EX-M9 | 비용 예산 한도 집행 메커니즘 추가 | P1 | `metrics_collector.py` L256-269에서 비용 계산만 수행하고 max budget 비교 없음. 에피소드/세션 단위 예산 한도 설정 및 초과 시 WARNING/에스컬레이션 | (1) `system.yaml`에 `budget.max_episode_cost` / `budget.max_session_cost` 설정 추가 (2) MetricsCollector에서 비용 누적 시 한도 비교 (3) 한도 초과 시 `logging.warning()` + `requires_human_intervention = True` (4) 선택적: 한도 초과 시 파이프라인 중단 옵션 | 4시간 | 없음 | S4 SSOT 10.2 M9, metrics_collector.py L256-269 |
| EX-M10 | 시스템 설정 런타임 리로드 지원 | P3 | `base_agent.py` L149의 `_SYSTEM_CFG = _load_system_config()`가 모듈 임포트 시 1회 로드. 런타임 설정 변경 반영 불가. 설정 리로드 트리거 또는 주기적 리로드 메커니즘 추가 | (1) `reload_system_config()` 함수 또는 파일 변경 감지 메커니즘 추가 (2) 설정 리로드 시 기존 인스턴스에 전파 (3) 리로드 시점에 로그 기록 (4) 리로드 중 race condition 방지 (Lock 사용) | 6시간 | 없음 | S4 SSOT 10.2 M10, base_agent.py L149 |
| EX-M11 | 실패 응답 DB 기록 길이 제한 | P2 | `base_agent.py` L537-538에서 실패 시 응답 전문 기록 (길이 제한 없음). 민감한 소설 내용 포함 가능. 기록 길이 상한 설정 및 성공 시에도 스니펫 기록 고려 | (1) 실패 시 응답 기록 길이를 5,000자로 제한 (2) 초과 시 `[TRUNCATED]` 표시 추가 (3) 성공 시에도 선택적 스니펫(500자) 기록 옵션 추가 (4) 기존 DB 스키마 호환성 유지 | 2시간 | 없음 | S4 SSOT 10.2 M11, base_agent.py L537-538 |

### 2.3 LOW 우선순위 (11건)

| ID | 항목 | 우선순위 | 상세 | 완료 기준 | 추정 공수 | 의존성 | S4 근거 |
|----|------|---------|------|----------|----------|--------|---------|
| EX-L1 | `_last_thinking` ask() 진입 시 리셋 추가 | P3 | `base_agent.py` L302에서 `_last_thinking`이 ask() 진입 시 리셋 안 됨. 진단/로깅 전용 필드이므로 기능 영향 없으나, 호출 N+1 실패 시 호출 N의 thinking 잔류 가능 | (1) `ask()` 진입부에 `self._last_thinking = ""` 리셋 추가 (2) 기존 테스트 통과 | 0.5시간 | 없음 | S4 SSOT 10.3 L1 |
| EX-L2 | `json.loads(strict=False)` NaN 리스크 문서화 | P3 | `base_agent.py` L1703에서 `strict=False`가 NaN/Infinity 허용. Gemini JSON 모드가 이를 실질 차단하므로 현재 안전하나, 비-Gemini 프로바이더 전환 시 리스크 발현 가능. 멀티 프로바이더 전환 시 `strict=True` 전환 검토 | (1) 멀티 프로바이더 전환 작업(EX-MP1)에 `strict=True` 전환 항목 포함 (2) 현재는 코드 주석으로 리스크 문서화 | 0.5시간 | EX-MP1 | S4 SSOT 10.3 L2 |
| EX-L3 | 폴백 체인 자기참조 문서화 | P4 | `base_agent.py` L51-54에서 `flash→flash` 자기참조. `_build_model_stack()` L938의 중복 제거로 무한루프 방지 확인됨(6-pass 검증). 코드 주석으로 의도 명시 | (1) 폴백 체인 자기참조에 대한 코드 주석 추가 (2) Flash 단독 사용 시 즉시 실패 동작 확인 | 0.5시간 | 없음 | S4 SSOT 10.3 L3 |
| EX-L4 | 제약 캐시 입력 불변 가정 문서화 | P4 | `three_phase_blueprint_generator.py` L196-212에서 제약 캐시 재사용. 재시도 루프 내 입력 불변이므로 stale 미발생 (6-pass 확인). 향후 재시도 루프에서 입력 변경 시 캐시 무효화 필요 | (1) 코드 주석으로 입력 불변 가정 명시 (2) 입력 변경 시 캐시 무효화 TODO 추가 | 0.5시간 | 없음 | S4 SSOT 10.3 L4 |
| EX-L5 | Temperature 기본값 차이 정리 | P4 | `ask()` 기본값 0.5 vs `_ask_with_cached_context()` 기본값 0.3. 모든 호출부가 명시적 temperature 전달하여 미발현(6-pass 확인). 기본값 통일 권고 | (1) 두 메서드의 기본값을 동일하게 통일 (0.5) (2) 기존 테스트 통과 확인 | 0.5시간 | 없음 | S4 SSOT 10.3 L5 |
| EX-L6 | 토큰 추정 자모 범위 확장 | P3 | `metrics_collector.py` L274-290에서 자모(`ㄱ-ㅎ`, `ㅏ-ㅣ`) 미포함. 실패 호출 한정 폴백이므로 영향 제한적이나, 추정 정확도 개선 가능 | (1) 한글 자모 범위(`\u3131-\u3163`) 추가 (2) 추정 오차 ±30% → ±20% 개선 목표 (3) 기존 비용 보고 테스트 통과 | 1시간 | 없음 | S4 SSOT 10.3 L6 |
| EX-L7 | 배치 검증 부분 실패 로깅 강화 | P3 | `batch_validator.py` L80-94에서 `asyncio.gather(return_exceptions=True)` 사용. 읽기전용이나 부분 실패 시 어떤 검증이 실패했는지 상세 로그 부재 | (1) 부분 실패 시 실패한 검증 항목명과 에러 메시지를 WARNING 로그에 포함 (2) 기존 배치 검증 동작 무변경 | 1시간 | 없음 | S4 SSOT 10.3 L7 |
| EX-L8 | top_p 외부 설정 노출 | P4 | `base_agent.py` L972/L1181/L1342/L2006의 4곳에서 top_p=0.95 하드코딩. `system.yaml`로 외부화하여 실험 가능하게 | (1) `system.yaml`에 `api.top_p` 설정 추가 (2) 4곳의 하드코딩을 설정 참조로 변경 (3) 기본값 0.95 유지, 설정 변경 시 반영 확인 | 2시간 | 없음 | S4 SSOT 10.3 L8 |
| EX-L9 | 캐시 MD5 해시 길이 문서화 | P4 | `base_agent.py` L1894에서 MD5 truncated 16자(64비트). 50 엔트리에서 충돌 확률 ~3.4e-17으로 실질 무의미. 코드 주석으로 근거 기록 | (1) MD5 16자 사용 근거와 충돌 확률을 코드 주석에 기록 | 0.25시간 | 없음 | S4 SSOT 10.3 L9 |
| EX-L10 | 오버랩 100자 상한 문서화 | P4 | `base_agent.py` L1255-1265에서 연속 응답 앵커 매칭 100자 cap. 합리적 상한이나, 100자 초과 오버랩 시 중복 가능. 코드 주석으로 설계 의도 기록 | (1) 오버랩 100자 상한의 설계 근거를 코드 주석에 기록 | 0.25시간 | 없음 | S4 SSOT 10.3 L10 |
| EX-L11 | 앙상블 첫 후보 대표 반환 동작 명시 | P4 | `blueprint_ensemble.py` L398-450에서 적격 후보 중 첫 번째 반환. 전체 후보 목록도 함께 반환되며 Director가 최종 선택하므로 의도적 설계. 코드 주석으로 명시 | (1) 앙상블 선택 로직에 "Director 최종 선택 전제" 주석 추가 | 0.25시간 | 없음 | S4 SSOT 10.3 L11 |

### 2.4 컨텍스트 캐싱 및 멀티 프로바이더 항목

| ID | 항목 | 우선순위 | 상세 | 완료 기준 | 추정 공수 | 의존성 | S4 근거 |
|----|------|---------|------|----------|----------|--------|---------|
| EX-CC1 | Gemini implicit caching 적중률 모니터링 | P2 | 현행 캐시 적중률 40-60% 불안정(GitHub googleapis/python-genai#1880). 실제 적중률을 MetricsCollector에서 추적하여 비용 추정 정확도 향상. **삽입 지점**: `base_agent.py L417-448 (`_build_metric_usage_payload()`) — `cached_content_token_count > 0` 체크 추가` | (1) API 응답의 `cached_content_token_count` 유무로 적중률 계산 (2) 에피소드/세션 단위 적중률 로그 (3) 적중률 50% 미만 시 WARNING | 3시간 | 없음 | S4 SSOT 5.4, 모델 선정 보고서 3.3 |
| EX-CC2 | 캐시 TTL 30분 적정성 검증 | P3 | 현행 TTL 1800초(30분). 에피소드 생산 파이프라인 실행 시간 대비 TTL 적정성 검증 필요. 장시간 실행 시 TTL 만료로 캐시 미스 발생 가능 | (1) 실제 에피소드 생산 시간 측정 (2) TTL 대비 파이프라인 실행 시간 비교 (3) 필요 시 TTL 조정 또는 TTL 자동 연장 메커니즘 추가 | 2시간 | EX-CC1 | S4 SSOT 5.1, base_agent.py L1864-1867 |
| EX-MP1 | 멀티 프로바이더 추상화 레이어 설계 | P1 | 현행 Gemini 전용 프로덕션 경로를 Claude/OpenAI 지원 가능하도록 추상화. `llm_router.py`의 모델명 접두사 라우팅은 구현 완료. `base_agent.py`의 Gemini 전용 config 생성, 캐싱, usage 키를 프로바이더 중립으로 전환 | (1) 프로바이더 인터페이스 정의 (config 생성, 응답 래핑, usage 매핑, 캐싱 전략) (2) Gemini 프로바이더가 기존 동작 100% 유지 (3) Claude/OpenAI 프로바이더 스텁이 인터페이스 준수 (4) 설계 문서 작성 | 16시간 | 없음 | S4 SSOT 1.3, 모델 선정 보고서 6.1-6.4 |
| EX-MP2 | Anthropic 프로바이더 프로덕션 강화 | P2 | `anthropic_provider.py`가 미검증 상태. 메시지 포맷 변환, timeout 전파, usage 키 매핑, Tool use 기반 구조화 출력 구현 필요 | (1) Gemini 포맷 → Claude 포맷 자동 변환 (2) timeout 전파 구현 (3) usage 키를 표준 키로 매핑 (4) 구조화 출력(Tool use 패턴 또는 JSON mode) 구현 (5) 단위 테스트 통과 | 12시간 | EX-MP1 | S4 SSOT 1.3, 6.3, 모델 선정 보고서 6.3 |
| EX-MP3 | OpenAI 프로바이더 프로덕션 강화 | P3 | `openai_provider.py`가 미검증 상태. Structured Outputs 적용, usage 키 매핑, timeout 전파 구현 | (1) Structured Outputs 모드 구현 (2) usage 키 표준 매핑 (3) timeout 전파 (4) 단위 테스트 통과 | 8시간 | EX-MP1 | S4 SSOT 1.3, 6.3 |
| EX-MP4 | 크로스 프로바이더 폴백 체인 구현 | P2 | 현행 `pro→flash` 동일 프로바이더 폴백을 `opus→sonnet→pro→flash` 크로스 프로바이더 체인으로 확장. `models.yaml` fallback_chain 섹션 확장 | (1) `_build_model_stack()`에서 크로스 프로바이더 모델 스택 구성 (2) 프로바이더 전환 시 config/client 자동 교체 (3) 크로스 프로바이더 폴백 시나리오 테스트 통과 (4) 폴백 발생 시 로그 기록 | 8시간 | EX-MP1, EX-MP2 | S4 SSOT 2.2, 모델 선정 보고서 5 |
| EX-MP5 | Claude Rate Limit 80K TPM 병목 사전 검증 | P1 | Claude 기본 80K TPM에서 8-9개 병렬 Advisory Chain 실행 가능 여부 검증. Gemini 4M TPM 대비 50배 제한적 | (1) Advisory Chain 8-9개 병렬 실행 시 Claude TPM 소비량 측정 (2) 80K TPM 초과 여부 판정 (3) 초과 시 Enterprise 티어 또는 AWS Bedrock 경유 필요성 문서화 (4) 병렬도 조절 옵션 설계 | 4시간 | EX-MP2 | S4 SSOT 8.5, 모델 선정 보고서 3.4 |
| EX-MP6 | Pilot 30화 블라인드 비교 계획 수립 | P1 | ChiefWriter 1개만 Opus 전환 후 30화 생산, 현행 Gemini 원고와 블라인드 비교. 한국어 창작 품질 정량 검증 목적 | (1) Pilot 비교 프로토콜 문서화 (블라인드 조건, 평가 기준, 평가자) (2) ChiefWriter 단독 Opus 전환 설정 파일 준비 (3) 비교 대상 에피소드 선정 기준 확정 (4) 평가 루브릭 설계 (문체, 캐릭터 보이스, 경어 일관성, 번역체 비율, 의성어/의태어 활용) | 4시간 | EX-MP1 | 모델 선정 보고서 5Pass 조건부 권고 |

---

## 3. 실행 순서 및 의존성 그래프

```
Phase 0 (즉시, 독립):
  EX-H1 ─────┐
  EX-H2       │
  EX-M1       │
  EX-M2       │
  EX-M9       │
  EX-MP1 ─────┤
              │
Phase 1 (H1/MP1 완료 후):
  EX-M3       │
  EX-M5 ◄─────┘ (EX-H1 의존)
  EX-MP2 ◄──── (EX-MP1 의존)
  EX-MP3 ◄──── (EX-MP1 의존)
  EX-MP5 ◄──── (EX-MP2 의존)
  EX-MP6 ◄──── (EX-MP1 의존)

Phase 2 (Phase 1 완료 후):
  EX-M4, EX-M6, EX-M7, EX-M8, EX-M11
  EX-CC1, EX-CC2
  EX-MP4 ◄──── (EX-MP1 + EX-MP2 의존)

Phase 3 (여유 시):
  EX-M10
  EX-L1 ~ EX-L11
```

---

## 4. 총 추정 공수

| 구분 | 항목 수 | 추정 공수 합계 |
|------|--------|---------------|
| HIGH (P0) | 2건 | 5시간 |
| MEDIUM (P1-P3) | 11건 | 31시간 |
| LOW (P3-P4) | 11건 | 7.25시간 |
| 컨텍스트 캐싱 | 2건 | 5시간 |
| 멀티 프로바이더 | 6건 | 52시간 |
| **합계** | **32건** | **100.25시간** |

---

## 5. FALSE 확정 삭제 항목 (4건, 실행 불요)

6-pass 적대적 감리에서 삭제 확정된 항목으로, 실행 대상에서 제외한다.

| ID | 원본 주장 | FALSE 근거 | 6-Pass 일치 |
|----|----------|-----------|------------|
| F1 | f-string 이중 해제 (원본 3-pass 10.2) | Python f-string은 변수 치환값 내 `{{`를 해제하지 않음 | 4/6 |
| F2 | `_sanitize(None)` -> `"none"` (원본 3-pass 7.2) | `None or ""` -> `""` (빈 문자열). `"none"` 아님 | 6/6 |
| F3 | `_rotation_lock` TOCTOU (원본 3-pass 16.1) | capture-then-release 패턴 + `_key_rotation_pending` 단발 플래그 | 5/6 |
| F4 | `hud_context` 방어적 복사 필요 (원본 3-pass 16.2) | `hud_context`는 Python 문자열(immutable). 스레드 간 변경 불가 | 6/6 |

---

## 6. 감리 이력

### 6.1 소스 감리 경과

| 단계 | 문서 | 에이전트 수 | tool uses | 역할 |
|------|------|-----------|-----------|------|
| 1단계 | llm-integration-deepdive-3pass-audit | 3회 독립 조사 | 109+ | 발견 (28건) |
| 2단계 | llm-deepdive-adversarial-3pass-correction | 3회 적대적 감리 | 78+ | 1차 교정 (CRITICAL 5->0, FALSE 4건) |
| 3단계 | devils-advocate-pass3-audit | 상세 근거 | - | Devil's Advocate |
| 4-6단계 | llm-deepdive-final-6pass-verdict | 3회 2차 적대적 검증 | 200+ | 최종 판정 (HIGH 4->2, 추가 교정 2건) |

### 6.2 심각도 변천사

| 심각도 | 원본(1단계) | 1차 교정(2단계) | 최종(4-6단계) |
|--------|-----------|---------------|-------------|
| CRITICAL | 5 | 0 | **0** |
| HIGH | 9 | 4 | **2** |
| MEDIUM | 10 | 12 | **11** |
| LOW | 4 | 10 | **11** |
| FALSE | 0 | 2+2 | **4** |
| 실질 합계 | 28 | 26 | **24** |

### 6.3 실행문서 3-pass 기본 감리

#### Pass 1: 완전성 검사

| 검사 항목 | 결과 | 비고 |
|----------|------|------|
| S4 SSOT HIGH 2건 전부 실행 항목화 | 통과 | EX-H1, EX-H2 |
| S4 SSOT MEDIUM 11건 전부 실행 항목화 | 통과 | EX-M1 ~ EX-M11 |
| S4 SSOT LOW 11건 전부 실행 항목화 | 통과 | EX-L1 ~ EX-L11 |
| FALSE 4건 제외 확인 | 통과 | F1~F4 명시적 제외 |
| 컨텍스트 캐싱 항목 포함 | 통과 | EX-CC1, EX-CC2 |
| 멀티 프로바이더 전환 항목 포함 | 통과 | EX-MP1 ~ EX-MP6 |
| 모델 선정 보고서 조건부 권고 반영 | 통과 | EX-MP5(Rate Limit), EX-MP6(Pilot) |
| 각 항목에 완료 기준/추정 공수/의존성/근거 존재 | 통과 | 전 32건 확인 |

#### Pass 2: 정합성 검사

| 검사 항목 | 결과 | 비고 |
|----------|------|------|
| 의존성 그래프 순환 없음 | 통과 | Phase 0->1->2->3 단방향 |
| 우선순위와 의존성 일관성 | 통과 | P0 항목은 의존성 없음, P1 이하만 의존성 보유 |
| 파일 경로/라인 번호가 S4 SSOT와 일치 | 통과 | 전 항목 대조 완료 |
| 추정 공수 합리성 (항목당 0.25-16시간) | 통과 | 최대 EX-MP1(16시간)은 프로바이더 추상화 규모에 적절 |
| 완료 기준의 검증 가능성 | 통과 | 전 항목이 관찰 가능한 결과 기술 |
| 6-pass에서 교정된 수치 반영 | 통과 | 연속 호출 10회->6회(EX-M4), Temperature 미발현(EX-L5) 등 |

#### Pass 3: 누락 검사

| 검사 항목 | 결과 | 비고 |
|----------|------|------|
| S4 SSOT 부록 A 감리 이력 반영 | 통과 | 6.1, 6.2절 |
| S4 SSOT 부록 B 근거 파일 참조 가능 | 통과 | 각 항목 S4 근거 열에 위치 명시 |
| 모델 선정 보고서 250화 비용 시나리오 반영 | 통과 | EX-MP6 Pilot 비교에 반영 |
| 보안 전수 조사 결과(6-pass) "안전" 판정 항목 | 통과 | 실행 불요 확인 (ast.literal_eval, SQL injection 등) |
| 스키마 라운드트립 손실 문제 | 통과 | EX-MP1 설계에 포함 (프로바이더별 스키마 변환) |

### 6.4 실행문서 5-pass 적대적 감리

#### Adversarial Pass 1: 과잉 실행 항목 검사

| 질문 | 판정 | 근거 |
|------|------|------|
| FALSE 확정 항목이 실행 항목에 혼입되었는가? | 아니오 | F1-F4 명시적 제외, 5절에 별도 기재 |
| 6-pass에서 하향된 심각도가 원본 심각도로 실행되는가? | 아니오 | EX-M4(6회, 10회 아님), EX-L5(미발현 확인) 등 교정 반영 |
| 실행 불요한 "안전" 판정 항목이 포함되었는가? | 아니오 | ast.literal_eval, SQL injection, 파일시스템 조작 등 미포함 |
| 현행 방어 장치가 충분한 항목에 과잉 실행이 배정되었는가? | 일부 | EX-M1: content_hash 2차 격리로 실질 오염 불가. 그러나 WARNING 로그 추가(2시간)는 과잉이 아닌 설계 명확화 수준. 허용 |

#### Adversarial Pass 2: 과소 실행 항목 검사

| 질문 | 판정 | 근거 |
|------|------|------|
| H1 anyOf 5곳 제거 시 하류 13곳의 isinstance 가드 정리가 누락되었는가? | 아니오 | EX-H1 완료 기준 (3)에 명시 |
| 멀티 프로바이더 전환 시 Thinking Budget 프로바이더별 분기가 누락되었는가? | 부분 누락 | EX-MP1 설계에 포함시켜야 함. 현재 Gemini 전용 값(S4 SSOT 2.5). 아래 보정 반영 |
| Claude 캐싱 전환 시 `cache_control` breakpoint 설정 작업이 누락되었는가? | 아니오 | EX-MP2 상세에 암묵적 포함. 그러나 명시성 부족. 아래 보정 반영 |
| 429 모호 분류(S4 M 수준) 개선이 실행 항목에 없는가? | 맞음 | S4 SSOT에서 MEDIUM으로 하향되었으나 별도 실행 항목 누락. 아래 보정 반영 |

#### Adversarial Pass 3: 의존성 무결성 검사

| 질문 | 판정 | 근거 |
|------|------|------|
| EX-M5(PASS_WITH_FIX)의 EX-H1 의존성이 올바른가? | 예 | anyOf 제거 후 타입 고정이 선행되어야 PASS_WITH_FIX 패치 로직 안정 |
| EX-MP4(크로스 폴백)의 EX-MP1+MP2 의존성이 충분한가? | 예 | 추상화 레이어 + Claude 프로바이더가 선행 필수 |
| EX-MP5(Rate Limit 검증)가 EX-MP2 완료 전 실행 가능한가? | 아니오 | Claude 프로바이더 구현 후에만 실측 가능. 의존성 올바름 |
| Phase 0 항목 간 순서 의존성이 숨겨져 있는가? | 아니오 | 전부 독립 실행 가능 확인 |

#### Adversarial Pass 4: 추정 공수 현실성 검사

| 항목 | 판정 | 근거 |
|------|------|------|
| EX-H1 (4시간): 5곳 anyOf 제거 + 14곳 하류 정리 | 과소 가능 | 19곳 코드 변경 + E2E 테스트. 6시간이 현실적. 아래 보정 반영 |
| EX-MP1 (16시간): 프로바이더 추상화 설계 | 적절 | 인터페이스 정의 + 기존 코드 리팩터링 + 설계 문서. 모델 선정 보고서의 "1-2주" 추정과 정합 |
| EX-MP2 (12시간): Anthropic 프로바이더 강화 | 적절 | 메시지 변환 + 캐싱 + 구조화 출력 + 테스트 |
| EX-M10 (6시간): 런타임 리로드 | 과소 가능 | 파일 감시 + 전파 + race condition 방지. 8시간이 현실적. 아래 보정 반영 |

#### Adversarial Pass 5: 최종 보정 적용

Pass 2, 4에서 발견된 문제를 아래와 같이 보정한다.

**보정 1**: EX-MP1 상세에 "Thinking Budget 프로바이더별 분기" 항목 추가.
- Gemini: ThinkingConfig 사용
- Claude: 별도 설계 필요 (extended thinking 미지원 또는 별도 패턴)
- OpenAI: o-시리즈 reasoning 별도 처리

**보정 2**: EX-MP2 완료 기준에 "(6) Claude prompt caching (`cache_control` breakpoint) 5개 에이전트 적용" 명시 추가.

**보정 3**: 429 모호 분류 개선 실행 항목 추가.

| ID | 항목 | 우선순위 | 상세 | 완료 기준 | 추정 공수 | 의존성 | S4 근거 |
|----|------|---------|------|----------|----------|--------|---------|
| EX-M12 | 429 모호 분류 개선 | P2 | `base_agent.py` L1093-1110에서 ambiguous 429를 rate limit으로 처리. 실제 quota 소진인 경우 무의미한 대기 반복. Gemini 429 응답에 거의 항상 키워드 포함(6-pass 확인)이나, API 에러 형식 변경 시 발현 가능 | (1) ambiguous 429 시 1회 rate limit 대기 후 재실패 시 quota로 재분류 (2) 분류 결과를 로그에 명시 (3) 기존 재시도 동작과 하위 호환 | 2시간 | 없음 | S4 SSOT 3.2, base_agent.py L1093-1110 |

**보정 4**: EX-H1 추정 공수 4시간 -> 6시간으로 상향.

**보정 5**: EX-M10 추정 공수 6시간 -> 8시간으로 상향.

### 6.5 보정 후 총 추정 공수 (최종)

| 구분 | 항목 수 | 추정 공수 합계 |
|------|--------|---------------|
| HIGH (P0) | 2건 | 7시간 (H1: 4->6시간) |
| MEDIUM (P1-P3) | 12건 (M12 추가) | 35시간 (M10: 6->8시간, M12: +2시간) |
| LOW (P3-P4) | 11건 | 7.25시간 |
| 컨텍스트 캐싱 | 2건 | 5시간 |
| 멀티 프로바이더 | 6건 | 52시간 |
| **합계** | **33건** | **106.25시간** |

---

## 7. 참조 파일 목록

### 코드 파일

| 파일 | 경로 | 관련 항목 |
|------|------|----------|
| base_agent.py | `modules/domain/agents/base_agent.py` | EX-H2, EX-M1, EX-M3, EX-M4, EX-M8, EX-M10, EX-M11, EX-M12, EX-L1~L5, EX-L8~L10 |
| response_schemas.py | `modules/core/response_schemas.py` | EX-H1 |
| gemini_provider.py | `modules/core/providers/gemini_provider.py` | EX-M6, EX-M7 |
| openai_provider.py | `modules/core/providers/openai_provider.py` | EX-MP3 |
| anthropic_provider.py | `modules/core/providers/anthropic_provider.py` | EX-MP2 |
| metrics_collector.py | `modules/core/metrics_collector.py` | EX-M9, EX-L6, EX-CC1 |
| writer.py | `modules/domain/agents/writer.py` | EX-M2 |
| three_phase_blueprint_generator.py | `modules/domain/agents/three_phase_blueprint_generator.py` | EX-M5, EX-L4 |
| blueprint_ensemble.py | `modules/domain/agents/blueprint_ensemble.py` | EX-L11 |
| batch_validator.py | `modules/validation/batch_validator.py` | EX-L7 |
| llm_router.py | `modules/core/llm_router.py` | EX-MP1 |
| llm_schema.py | `modules/core/llm_schema.py` | EX-MP1 |
| confidence_calibration.py | `modules/core/confidence_calibration.py` | EX-H1 (약한 가드 수정) |

### 설정 파일

| 파일 | 경로 | 관련 항목 |
|------|------|----------|
| system.yaml | `config/system.yaml` | EX-M9, EX-M10, EX-L8, EX-CC2 |
| models.yaml | `config/models.yaml` | EX-MP1, EX-MP4 |
| validation.yaml | `config/validation.yaml` | EX-M3 |

---

*3-pass 기본 감리 + 5-pass 적대적 감리 완료. 33건 실행 항목, 총 추정 106.25시간.*
*문서 생성: 2026-03-18.*
