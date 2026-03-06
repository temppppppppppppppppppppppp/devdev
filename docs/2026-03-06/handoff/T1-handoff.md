# T1 Handoff — Prompt Map 동결

- 작성: 2026-03-06
- 담당: T1 (Prompt Map)
- last_seen_broadcast_seq: [2026-03-06T00:00:00+09:00] CODE_LOCK 선언

---

## 결론

`docs/implementation/prompt-map-v1.json` 검증 및 수정 완료.
key 누락 0건, 필수 필드 누락 0건.

---

## 검증 결과

### 상위 메뉴 key 전수 확인

| key | 존재 | requires_sub_key | requires_double_confirm | approval_policy | 판정 |
|---|---|---|---|---|---|
| `0` | ✅ | true | - | - | PASS |
| `1` | ✅ | false | - | - | PASS |
| `2` | ✅ | false | - | - | PASS |
| `3` | ✅ | false | - | - | PASS |
| `4` | ✅ | false | - | - | PASS |
| `5` | ✅ | false | - | - | PASS (ui_only_action=exit_app) |
| `6` | ✅ | false | - | - | PASS (수정 후) |
| `44` | ✅ | false | true | dual_control | PASS (수정 후) |
| `77` | ✅ | false | true | dual_control | PASS |
| `88` | ✅ | false | true | dual_control | PASS |
| `99` | ✅ | false | true | dual_control | PASS (수정 후) |

### Stage 0 sub_key 확인

allowed_sub_keys: `["0","1","2","3","4","5","6"]` — 제안서 7개(0~6) 전량 일치. ✅

---

## 발견된 갭 및 수정 내역

### GAP-1 (P1) — key="6" `onestop_fail_action` 스텝 누락

- 제안서: One-Stop 후속 입력 3개 (배치 Arc 개수 / **Stage 3 실패 시 [건너뛰기|중단]** / 계속 여부)
- 수정 전: 2개 스텝 (onestop_batch_count, onestop_continue)
- 수정 후: 스텝 추가
  ```json
  {
    "step_id": "onestop_fail_action",
    "type": "enum",
    "options": ["skip", "stop"],
    "default": "stop"
  }
  ```

### GAP-2 (P1) — key="44" `rollback_target_episode` 스텝 누락

- 제안서: "되감기 화수 + 확인(y/n)" — 화수 입력 스텝 필요
- 수정 전: `steps: []`
- 수정 후: 스텝 추가
  ```json
  {
    "step_id": "rollback_target_episode",
    "type": "int",
    "required": true,
    "default": 1,
    "min": 1,
    "max": 999
  }
  ```

### GAP-3 (P1) — key="99" `rewind_target_arc` 스텝 누락

- 제안서: "시작 Arc 번호 + 확인(y/n)" — Arc 번호 입력 스텝 필요
- 수정 전: `steps: []`
- 수정 후: 스텝 추가
  ```json
  {
    "step_id": "rewind_target_arc",
    "type": "int",
    "required": true,
    "default": 1,
    "min": 1,
    "max": 99
  }
  ```

### GAP-4 (P2) — key="2" `stage2_fail_action` 기본값 불일치

- 제안서: 실패 시 분기 기본값 = `2` (중단=stop)
- 수정 전: `"default": "retry"`
- 수정 후: `"default": "stop"`

---

## 수정 없는 항목

- key="77", "88": steps:[] 정상 — 각각 "삭제 확인 y/n"만 필요, 추가 입력 없음. ✅
- key="3" `stage3_skip_allowed=false`: 제안서 "실패 시 즉시 중단" 정책과 일치. ✅
- key="4" `stage4_fallback` options: ["adopt_best","skip"] ← 제안서 [1]최선채택/[2]건너뛰기 대응. ✅

---

## 완료 기준 점검

| 기준 | 결과 |
|---|---|
| key 누락 0건 | ✅ 11개 전량 존재 |
| 필수 필드 누락 0건 | ✅ (4건 수정 후) |
| T2/T3와 필드명 충돌 | 미확인 (T2/T3 handoff 산출물 대기) |

---

## T2/T3 인계 사항

- `onestop_fail_action` (key=6): enum `["skip","stop"]` — T2 API 계약에 반영 요청
- `rollback_target_episode` (key=44): int, min=1 — T2 `/run` body 스키마에 반영 요청
- `rewind_target_arc` (key=99): int, min=1 — T2 `/run` body 스키마에 반영 요청
- T3 이벤트 스키마 영향 없음 (prompt-map은 입력 계약만 정의)
