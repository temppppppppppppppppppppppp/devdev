# T3 Handoff — Event Schema 동결

- 담당: T3 (Event Schema 동결)
- 완료 시각: 2026-03-06
- last_seen_broadcast_seq: 0 (T0-broadcast 초기 상태)

---

## 산출물

- 파일: `docs/implementation/event-schema-v1.json`
- 상태: **동결 완료 (변경 없음)** — 기준 문서와 완전 일치

---

## 검증 결과

### 1. 공통 필드 (required) ✅

| 필드 | 스키마 타입 | 제약 |
|------|------------|------|
| `event_version` | string | const "v1" |
| `seq` | integer | minimum 1 |
| `run_id` | string | — |
| `type` | string | enum (7개) |
| `ts` | string | format date-time |
| `payload` | object | — |

### 2. type enum ✅

모두 포함 확인:
- `run_started`, `progress`
- `prompt_request`, `prompt_resolved`, `prompt_timeout`
- `run_completed`, `run_failed`

### 3. prompt_* 조건부 payload 필수 필드 ✅

| type | required 필드 |
|------|--------------|
| `prompt_request` | `prompt_id`, `step_id`, `input_type`, `default`, `timeout_sec` |
| `prompt_resolved` | `prompt_id`, `value`, `source` |
| `prompt_timeout` | `prompt_id`, `applied_default` |

### 4. JSON schema 파싱 성공 ✅

유효한 JSON, `$schema: https://json-schema.org/draft/2020-12/schema` 선언 정상.

---

## 완료 기준 충족 여부

| 기준 | 결과 |
|------|------|
| JSON schema 파싱 성공 | PASS |
| `prompt_*` 필수 필드 누락 0건 | PASS |
| T2 API 계약과 이벤트명 충돌 0건 | PASS |

---

## 비고

- 기준 문서 내 "이벤트 스키마 예시"(line 117) 의 `event_version: 1`(정수)은 예시 스니펫의 오기.
  정식 JSON 스키마(기준 문서 line 1429~)는 `"const": "v1"`(문자열)로 명시되어 있으며 현 파일과 일치함. 별도 수정 불필요.
- 기준 문서 line 108의 필드 목록(`key`, `step`, `type`, `required`)은 초기 서술 단계 텍스트이며,
  이후 확정된 JSON 스키마(line 1454+)의 `step_id`, `input_type`, `timeout_sec` 가 우선함.

---

## 후속 의존 터미널 공지

- `event-schema-v1.json` 동결. 이벤트 타입/필드 변경 시 T3 재검토 필요.
- T4(BE 서버 스텁), T5(WS emit) 등 이벤트 발행 구현 터미널은 본 스키마를 참조할 것.
