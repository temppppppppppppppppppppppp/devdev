# OPUS 5문서 통합 감리 — SSOT 실현 오더

> 작성일: 2026-03-13
> 범위:
> - `docs/2026-03-13/TF-S4DD-consolidated-3pass-audit.md`
> - `docs/2026-03-13/stage0-full-survey-consolidated-findings-3pass-reaudit.md`
> - `docs/2026-03-13/stage2-detail-deep-dive-consolidated-findings.md`
> - `docs/2026-03-13/S3D-full-survey-3pass-audit.md`
> - `docs/2026-03-13/XC-6track-merged-remediation-execution-ssot.md`
> 상태: final locked SSOT, 3-pass 재감리 완료, 코드 수정 금지
> 신뢰도: 95% 이상
> 실행 closure: `docs/2026-03-13/opus-5doc-integrated-ssot-execution-closure.md`

---

## 0. 운영 원칙

1. 위 5개 문서는 **참고자료**로만 취급한다. 실행 기준은 리포지토리 실제 코드다.
2. 통합 카운트는 원문 숫자를 그대로 믿지 않는다. 중복, 산술 오류, 부분집합 카운트를 제거한 뒤 SSOT에 반영한다.
3. 이 문서는 **즉시 코드 수정 오더가 아니라 실행 큐 SSOT**다.
4. SSOT에 올리는 항목은 아래 둘 중 하나를 만족해야 한다.
   - 코드 스니펫과 줄 근거로 직접 확인됨
   - 검색 결과 0건 또는 테스트 미커버가 재현됨
5. 미재검증 수치나 저신뢰 P3는 본문에서 제외하고 보류 목록으로 격리한다.

---

## 1. 3-Pass 통합 재감리 결과

### Pass 1. 문서 자체 정합성 점검

#### 확정 문서 오류

| 문서 | 문제 | 근거 |
|------|------|------|
| `stage0-full-survey-consolidated-findings-3pass-reaudit.md` | P3 건수를 `11`로 적었지만 실제 ID는 12개 나열 | P3 요약행과 상세 표 불일치 |
| `stage0-full-survey-consolidated-findings-3pass-reaudit.md` | `오탐 17건` 표기는 산술상 모순 | 같은 문서가 확정 finding 합계를 17건으로 표기 |

#### 실행 집계 주의

| 문서 | 주의점 | 처리 원칙 |
|------|--------|----------|
| `TF-S4DD-consolidated-3pass-audit.md` | M-2가 M-1의 부분집합으로 명시됨 | 실행 큐에서는 M-1/M-2를 하나의 remediation unit으로 묶는다 |
| `XC-6track-merged-remediation-execution-ssot.md` | 본문이 스스로 cross-track 중복을 인정함 | SSOT 실행 순서는 raw count 84건이 아니라 deduped action unit 기준으로 잡는다 |

### Pass 2. 코드 근거 교차 검증

아래 항목만 SSOT 실행 큐로 승격했다.

증거 형식:
- `file:line` = 코드 직접 근거
- `검색 0건` = 부재/미전달/미커버를 재현한 간접 근거
- 문서 내부 산술 오류 = 원문 표/서술 상호 대조 근거

| 우선순위 | 항목 | 코드 근거 | 판정 |
|----------|------|----------|------|
| P1 | Advisory timeout 후 hang 가능성 | `modules/core/stage4_interview_round.py:3810-3829` | 확정 |
| P1 | `_safe_commit()` 실패 시 rollback 미호출 | `modules/core/services/project_service.py:190-192`, `253-255`, `344-346`, `409-411` | 확정 |
| P1 | Stage 2 validation detail이 Stage 4 context로 전달되지 않음 | `modules/core/stage4_context_builder.py`에서 `stage_attempts` 검색 0건 | 확정 |
| P2 | Stage2Context에 `world_state` 슬롯 없음, 오케스트레이터는 바인딩 시도 | `modules/core/stage2_context.py:136-191`, `modules/core/stage2_orchestrator.py:290-294` | 확정 |
| P2 | `npc_deaths` 스키마가 string 배열, 소비자는 dict도 기대 | `modules/core/response_schemas.py:414-417`, `modules/domain/agents/unified_arc_validator.py:333-346` | 확정 |
| P2 | `skill_acquisitions`가 response schema에서 누락 | `modules/core/response_schemas.py` 검색 0건, `modules/domain/agents/unified_arc_validator.py:346-354` | 확정 |
| P2 | `timeline.start/end`는 schema상 string인데 소비자는 dict 기대 | `modules/core/response_schemas.py:382-386`, `modules/domain/agents/unified_arc_validator.py:306-329`, `modules/core/stage3_orchestrator.py:925-939` | 확정 |
| P2 | Stage2 finalizer가 `physical_inventory`와 `arc_start_state.equipment`를 Python에서 강제 계승/동기화 | `modules/core/stage2_finalizer.py:940-996`, `1047-1072` | 확정 |
| P2 | Stage0 `generate_bible()` 실패 시 `self.bible` 기본값 `{}`와 반환값 `None`이 분리 | `modules/core/stage0/story_expander.py:40-43`, `205-210` | 확정 |
| P2 | Stage0 `_enforce_type()` list/dict 경로가 shallow copy | `modules/core/stage0/preset_registry.py:537-541` | 확정 |
| P2 | Stage0 저장 경로에서 Bible 저장 실패와 Treatment 저장이 비대칭 | `modules/core/stage01_helpers.py:654-685` | 확정 |
| P3 | Stage0 CLI UI 한글 mojibake | `modules/core/stage0/__init__.py:317-325` | 확정 |
| P2 | Stage3/4가 Entity Registry를 각각 독립 추출 | `modules/core/stage3_orchestrator.py:811-819`, `modules/core/stage4_orchestrator.py:1352-1358` | 조건부 확정 |
| P2 | Stage3에서 Treatment Block/`gen_err` 경로 테스트 근거 부족 | `tests/test_stage3_orchestrator.py`, `tests/e2e/test_l3_stage3_smoke.py`에서 `TF9|blueprint_gen_error|gen_err` 검색 0건 | 조건부 확정 |
| P2 | Stage4 `_threshold()` 기본값이 YAML과 불일치 | `modules/core/stage4_context_builder.py`, `modules/core/stage4_interview_round.py`, `config/settings/validation.yaml` 비교 | 확정 |
| P3 | Stage4 EMPTY 케이스가 DB에 `ERROR`로 기록 | `modules/core/stage4_interview_round.py:1442-1452` | 확정 |
| P3 | Stage4 UI가 `round_num >= 4` 하드코딩 | `modules/core/stage4_interview_round.py:1426-1431` | 확정 |
| P2 | Advisory 병렬 경로가 공유 `validation_results` dict를 직접 mutate | `modules/core/stage4_interview_round.py:3861-3862`, `3902-3903` | 확정 |
| P2 | 컨텍스트 캐시 clear는 API 키 변경 시에만 수행됨 | `modules/domain/agents/base_agent.py:242`, `1765-1803` | 조건부 확정 |
| P2 | LLM router helper는 raw provider response를 그대로 반환 | `modules/core/llm_generate.py:9-20`, `modules/domain/agents/base_agent.py:334-342` | 조건부 확정 |

### Pass 3. 오탐 제거 후 최종 승격 규칙

- SSOT 본문에는 `확정`과 `조건부 확정`만 남긴다.
- `조건부 확정`은 **즉시 코드 수정 대상이 아니라 설계/테스트 큐**로만 승격한다.
- 원문 수치만 있고 코드 재현이 없는 항목은 본문에서 제외한다.

---

## 2. 최종 SSOT 실현 오더

### Unit 0. 문서 기준선 정정

목표: 이후 실행이 잘못된 카운트 위에서 시작되지 않게 한다.

1. Stage 0 통합본의 P3 건수와 `오탐 17건` 문구를 정정한다.
2. Stage 4 통합본의 M-1/M-2를 실행 기준에서는 단일 unit으로 표시한다.
3. XC 통합본의 `84건`은 raw track count일 뿐 실행 단위가 아니라는 잠금 규칙을 본 문서 기준으로 확정한다.

정지 조건:
- 원문 산술 오류가 남아 있으면 후속 우선순위 문서화 금지.

### Unit 1. 운영 중단/무성 실패 방지 큐

목표: hang, 트랜잭션 잔류, 실패 맥락 손실처럼 운영 안정성에 직접 닿는 항목만 먼저 묶는다.

1. `XC-ADV-006`: Advisory executor timeout 종료 경로 재설계
2. `XC-ERR-016`: `_safe_commit()` false 경로 rollback 보강
3. `XC-ERR-012`: Stage 2 validation error detail을 Stage 4 context로 전달

승격 근거:
- 모두 코드에서 직접 재현되거나 검색 0건으로 확인됨
- raw 문서 기준이 아니라 운영 안전성 기준으로도 최상위

### Unit 2. Stage 2 계약/스키마 정합 큐

목표: Stage 2가 Stage 3/4에 넘기는 구조 계약을 먼저 맞춘다.

1. `world_state` 슬롯 누락과 바인딩 시도 불일치 정리
2. `npc_deaths` 스키마 타입 정합
3. `skill_acquisitions` schema 누락 해소
4. `timeline.start/end` schema vs consumer 계약 정합
5. `physical_inventory` / `arc_start_state.equipment` 자동 계승 범위 문서화

설명:
- 이 묶음은 서로 강하게 연결돼 있다.
- Stage 2 schema를 건드리지 않고 Stage 3/4 test만 늘리면 노이즈만 고정될 가능성이 높다.

### Unit 3. Stage 0 상태 위생 큐

목표: Stage 0 산출물이 빈 상태/오염 상태로 다음 스테이지에 전파되지 않게 한다.

1. `generate_bible()` 실패 시 in-memory 상태 정합 규칙 명문화
2. `_enforce_type()` shallow copy 제거 또는 금지 범위 명시
3. Bible/Treatment 저장 비대칭 경로 정리
4. Stage 0 CLI mojibake 문자열 복구

설명:
- Stage 0는 뒤 스테이지의 seed다.
- 여기서 빈 Bible, 얕은 복사, 인코딩 오염이 남으면 이후 stage 문서가 전부 과장된 증상으로 보일 수 있다.

### Unit 4. Stage 3/4 검증 큐

목표: Stage 3/4에서 이미 존재하는 보호장치가 실제로 테스트되도록 만든다.

1. Stage 3 Treatment Block 주입 경로 테스트
2. Stage 3 `gen_err` 크래시 경로 테스트
3. Stage 3/4 Entity Registry 중복 추출 정책 결정
4. Stage 4 `_threshold()` 기본값과 YAML 동기화
5. Stage 4 EMPTY verdict 라벨 정규화
6. Stage 4 advisory 공유 상태 mutation 보호

설명:
- 이 묶음은 “즉시 고장”보다 “보호장치가 문서만 있고 검증이 빈약한 상태”에 가깝다.
- Unit 1, 2, 3 이후에 묶어서 처리하는 것이 순서상 안전하다.

### Unit 5. 보류된 크로스컷 큐

본 문서에서는 실행 우선순위만 잠그고, 아래는 보류로 둔다.

1. BaseAgent context cache invalidation 전면 정책
2. raw provider response 추상화 계층
3. Stage 4 low-risk cosmetic 정리
4. 원문 P3 전량 정리

보류 사유:
- 영향 범위가 넓거나 멀티프로바이더 전환 같은 전제조건이 붙는다.
- 현재는 “바로 손대면 이득”보다 “순서 없이 손대면 확산 위험”이 크다.

---

## 3. 이번 통합 감리에서 SSOT로 승격하지 않은 항목

아래는 원문에 있었지만 이번 SSOT 본문에서는 제외했다.

1. MagicMock `161:1` 같은 정량 수치
2. Stage 4 `28% 미커버` 같은 총량 지표
3. raw finding 총합 84건, 39건, 17건 같은 문서 집계 숫자 자체
4. 개별 P3 중 코드 영향이 낮고 재현 없이 문장 설명만 있는 항목

제외 이유:
- 이번 턴의 목표는 **실행 오더 SSOT 고정**이지, 전체 원문 수치의 재집계가 아니다.
- 수치 재집계는 별도 트랙으로 떼어야 오히려 오탐을 줄일 수 있다.

---

## 4. 신뢰도 판정

신뢰도 95% 이상으로 판정한 이유:

1. SSOT 본문에 남긴 항목은 전부 코드 스니펫 또는 검색 결과로 재검증했다.
2. 내부 산술 오류가 확인된 문서는 원문 숫자를 실행 기준에서 배제했다.
3. 중복이 명시된 항목은 raw count가 아니라 deduped unit으로 재편성했다.
4. 미재검증 정량 수치는 전부 보류 목록으로 밀어냈다.
5. 문서 내 주요 파일/줄 참조는 존재 여부와 line range를 다시 점검했다.
6. UTF-8 오염(삼중 물음표, replacement character)은 재검사에서 발견되지 않았다.

따라서 본 문서의 95%는
`원문 5개 문서 전체가 95% 정확하다`는 뜻이 아니라,
`실행 큐로 승격한 항목은 95% 이상 신뢰할 수 있다`는 뜻이다.

---

## 5. 이 SSOT 문서 자체의 3-Pass 재감리

### Self Pass 1. 구조

- 코드 수정 지시를 하지 않았다.
- 실행 순서를 Unit 기준으로 단일화했다.
- raw count와 execution unit을 분리했다.

### Self Pass 2. 근거

- 각 Unit은 최소 1개 이상의 코드 근거를 가진다.
- 검색 0건을 근거로 쓴 항목은 문서에 명시했다.
- Stage 0 산술 오류처럼 문서 내부 오류는 원문 줄 근거로 확인했다.
- 주요 `file:line` 참조는 실제 파일 존재와 line range 유효성을 재확인했다.

### Self Pass 3. 오탐 제거

- 재검증하지 못한 정량 수치는 본문에서 제거했다.
- 조건부 확정은 설계/테스트 큐로만 남기고 즉시 수정 큐에서 제외했다.
- 결과적으로 “지금 바로 믿어도 되는 실행 순서”만 남겼다.
- 잠정 표현 `준비만 해 둔다` 같은 문구를 제거해 최종 잠금 문서로 정리했다.

---

## 6. 최종 판정

최종 판정: **PASS (FINAL LOCK)**

단, PASS의 의미는 아래로 한정한다.

- 이 문서는 위 5개 문서를 대체하는 **실행 기준 SSOT**로 사용할 수 있다.
- 원문 문서의 raw count나 severity 총합은 그대로 재사용하면 안 된다.
- 다음 행동은 코드 수정이 아니라 **이 SSOT 순서대로 작업 큐를 재편성하는 것**이다.
- 재감리 기준 현재 문서 수준의 확신도는 95% 이상으로 본다.
