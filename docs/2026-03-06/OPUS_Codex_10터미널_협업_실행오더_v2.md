# OPUS TF + Codex 10터미널 협업 실행 오더 v2 (실행판)

> 작성일: 2026-03-06  
> 이전 버전: v1  
> 목적: `터미널 10개` 병렬 운용에서 충돌/대기/재작업을 최소화하고 PoC를 가장 빠르게 구현/검증  
> 기준 문서: `docs/2026-03-05/codex-ui-webgal-light-proposal.md` (`v1.17`)  
> 적용 산출물: `docs/implementation/*`, `scripts/e2e_menu_smoke.ps1`, `tests/*`

---

## 0. 운용 모드 선언 (파일 폴링 기반)

| 모드 | 의미 | 허용 작업 |
|---|---|---|
| `CODE_LOCK` | 코드 수정 금지 | 문서 감리, 테스트 명세, 게이트 점검 |
| `CODE_OPEN` | 코드 수정 허용 | 구현/테스트/스모크/증빙 생성 |

규칙:
1. T0(또는 대리 T9)가 모드/지시를 `docs/2026-03-06/handoff/T0-broadcast.md`에 기록한다.
2. 각 터미널은 작업 착수 전에 `T0-broadcast.md`를 직접 확인하고, 확인 시각을 자기 `handoff`에 기록한다.
3. 실시간 브로드캐스트/메시지 버스는 없다. 조율은 파일 폴링으로만 수행한다.
4. `T0-broadcast.md`의 엔트리는 `seq` 증가 규칙을 따른다(역행 금지).

T0-broadcast.md 초기 템플릿:
```markdown
# T0 Broadcast
## seq: 1
## mode: CODE_LOCK
## phase: A
## message: Phase A 시작. T1~T3 계약 동결 착수.
```

---

## 0.5. 용어 정의

- Mode B: `codex-ui-webgal-light-proposal.md` §3에 정의된 실시간 입력 처리 모드
- key/sub_key: `/run` API의 프롬프트 식별자 (`api-contract-v1.yaml` §2 참조)
- 위험키: `RISK_APPROVAL_REQUIRED` 대상으로 분류된 key 목록

---

## 1. 역할 분리 (OPUS TF vs Codex)

| 축 | 주 역할 | 산출물 |
|---|---|---|
| OPUS TF | 리스크 탐지, 회귀 포인트 정의, 테스트 관점 감리 | 위험 목록, 테스트 요구사항, 감리 코멘트 |
| Codex | 코드/문서 패치, 파일 정합성 유지, 산출물 생성 | 실제 변경 파일, 스크립트, 체크리스트 반영 |

원칙:
1. OPUS TF는 `무엇을 막아야 하는지`를 정의한다.
2. Codex는 `어떻게 고정할지`를 파일로 확정한다.
3. 책임 회피 방지를 위해 최종 소유자는 터미널 기준으로 1명만 둔다.

---

## 2. 10터미널 역할 배치 (고정)

| 터미널 | 책임 | 1차 소유 파일 | 선행 의존 |
|---|---|---|---|
| `T0` | 총괄 오더/병합/우선순위/최종 판정 | 본 문서 + 종합 보고 | 없음 |
| `T1` | Prompt Map 동결 | `docs/implementation/prompt-map-v1.json` | 없음 |
| `T2` | API Contract 동결 | `docs/implementation/api-contract-v1.yaml` | 없음 |
| `T3` | Event Schema 동결 | `docs/implementation/event-schema-v1.json` | 없음 |
| `T4` | `/run` 검증 로직 | 백엔드 run validator 코드 | `T1,T2` |
| `T5` | Mode B 입력/이벤트 | `/run/{run_id}/input` + WS 이벤트 | `T2,T3` |
| `T6` | 위험키 안전정책 | `RISK_APPROVAL_*` 처리 + 감사로그 | `T1,T2` |
| `T7` | 스모크 자동화 | `scripts/e2e_menu_smoke.ps1` → `artifacts/smoke/smoke-summary.json` (스크립트 출력 경로) | `T2` |
| `T8` | 테스트 자동화 | `tests/*` | `T1,T2,T3` |
| `T9` | 릴리즈 게이트/운영 증빙 | `docs/implementation/release-gate-v1.md` | `T7,T8` |

T0 불가 시: T9가 대리 판정권을 갖는다. T9는 `T0-broadcast.md`에 `[DELEGATE_T9 선언]`을 기록하고, 각 터미널은 작업 착수 전 이를 직접 확인한다.

스플래시 스크린 구현 소유: T5 (UI 입력/이벤트 담당)가 `src/splash/*` 구현을 소유한다. T7은 스모크 검증만 담당.

---

## 3. 실행 순서 (최적 오더)

### Phase A (선행 90분): 계약 동결
0. `T0`가 `docs/2026-03-06/handoff/` 디렉터리를 생성하고 `T0-broadcast.md`를 초기화한다. (선행 조건)
1. `T1~T3`이 계약 3종을 동결한다.
2. `T0`가 필드명/오류코드 충돌을 검토한다.
3. `T0`가 `T0-broadcast.md`에 `[PHASE_A_G1_PASS]`를 기록하기 전에는 `T4~T8` 구현 착수 금지.

완료 조건:
- `prompt-map-v1.json`, `api-contract-v1.yaml`, `event-schema-v1.json` 승인 완료.

### Phase B (병렬 3~4시간): 구현/검증 준비
1. `T4`: key/sub_key/중복 실행/승인 누락 검증 구현.
2. `T5`: `prompt_request/resolved/timeout` 왕복 구현.
3. `T6`: `RISK_APPROVAL_REQUIRED/EXPIRED/DUAL_CONTROL_REQUIRED` 구현.
4. `T7`: 스모크 실행 스크립트와 결과 파일 생성 경로 고정.
5. `T8`: 오류코드/분기 pytest 작성.
6. `T9`: 릴리즈 `NO-GO` 자동 규칙 고정.

완료 조건:
- 핵심 기능 PR 생성.
- 스모크/테스트 케이스 정의 완료.
- T0가 `T0-broadcast.md`에 `[PHASE_B_COMPLETE]`를 기록한 후 Phase C 착수.

### Phase C (통합 2시간): 판정
1. `T7` 스모크 실행 결과 수집.
2. `T8` 테스트 결과 수집.
3. `T9` 증빙 파일 존재성 확인.
4. `T0` 최종 Go/No-Go 회의.

완료 조건:
- `artifacts/smoke/smoke-summary.json` 상태 `passed`.
- 필수 증빙 누락 0건.

---

## 4. 상태 보고 프로토콜 (공용)

보고 주기:
1. 작업 착수 전: `T0-broadcast.md` 확인 1회(필수)
2. 진행 중: 30분마다 `T0-broadcast.md` 재확인 + 자기 `handoff` 갱신
3. Phase 전환 구간: 5분 주기로 재확인
4. 블로커 발생 시: 자기 `handoff`에 `BLOCKER` 즉시 기록
5. 단계 완료 시: 자기 `handoff` 즉시 갱신

보고 포맷:
```text
[T번호][상태:READY|RUNNING|BLOCKER|DONE]
작업:
변경 파일:
다음 액션:
리스크:
```

통신 채널:
- 실시간 알림 채널 없음
- 조율/지시 전달은 `T0-broadcast.md` + 각 `Tn-handoff.md` 폴링으로만 수행
- 각 터미널은 `last_seen_seq`를 handoff에 기록해 stale 지시 수신을 방지

블로커 SLA:
1. T0는 `handoff` 폴더를 15분 주기로 폴링하고 1차 응답을 남긴다.
2. 소유권 재할당 판단: 30분 이내
3. 미해결 시: Phase rollback 여부 결정

---

## 5. Handoff 규격 (필수)

경로:
- `docs/2026-03-06/handoff/T{번호}-handoff.md`

필수 항목:
1. 변경 파일 목록
2. 완료 항목
3. 미완료 항목
4. 리스크 1~3개
5. 다음 터미널 액션 1줄

템플릿:
```markdown
# T{번호} Handoff
- 시각:
- 모드: CODE_LOCK / CODE_OPEN
- last_seen_broadcast_seq:
- 변경 파일:
- 완료:
- 미완료:
- 리스크:
- 다음 액션:
```

---

## 6. 충돌 방지 규칙

1. 동일 파일 동시 편집 금지.
2. 파일 소유권 변경은 T0 승인 후만 허용.
3. PR 단위는 기능 축 1개만 허용.
4. 장애 기록은 `누가/입력/기대/실제/로그경로` 5요소를 강제.
5. 계약 3종(`T1~T3`)은 승인 후 임의 필드 추가 금지.

---

## 7. 게이트 판정식 (실행판)

`GO` 조건:
1. `G1`: 계약 3종 동결 완료
2. `G2`: `/run` 검증 및 `RISK_*` 분기 동작 확인
3. `G3`: `smoke-summary.json` = `passed`
4. `G4`: `pytest` 핵심 케이스 통과
5. `G5`: `release-gate-v1.md` 필수 증빙 파일 존재
6. `G6`: 위험 승인 샘플 로그 검증 완료

판정 규칙:
- `G1~G6` 모두 true면 `GO`
- 하나라도 false면 `NO-GO`

판정 시점:
- `G1`: Phase A 완료 직후 (미통과 시 T4~T8 착수 금지)
- `G2/G4`: Phase B 완료 직후
- `G3/G5/G6`: Phase C 완료 직후 (최종 GO/NO-GO)

---

## 8. 코드 수정 금지 모드 운용 (현재 대응)

`CODE_LOCK`일 때 허용:
1. `T1~T3`: 계약 문서 정합성 재감리
2. `T7`: 스모크 케이스/기대코드 문서화
3. `T8`: 테스트 명세서 작성
4. `T9`: 릴리즈 체크리스트/승인 문서 확정

`CODE_OPEN` 전환 트리거:
- T0(또는 대리 T9)가 `T0-broadcast.md`에 `[CODE_OPEN 선언]` 메시지를 기록한 시점

---

## 9. 즉시 중단 조건

1. 계약 파일 3종 필드명 불일치
   ※ T6 구현 완료 전(Phase B 진행 중)에는 T0가 수동으로 승인 로그를 확인한다.
2. 위험키 승인에서 동일 승인자 통과
3. 스모크 상태 `network_error` 또는 `failed`

조치:
1. 신규 배포 즉시 중지
2. 블로커 보고서 작성
3. T0 재오더 발령

---

## 9.5 감리 3회 결과 (2026-03-06)

1회차 감리:
- `G3` 판정 시점 중복 표기를 제거하고 단계별 판정을 명확화함
- `동결 선언`의 기록 위치를 `T0-broadcast.md`로 고정함

2회차 감리:
- 패키지 공지문을 파일 폴링 기준으로 정렬함
- `T0-broadcast.md`를 공용 지시판으로 명시함

3회차 감리:
- T1~T9 개별 발령문의 시작 조건 형식을 통일함
- 전 터미널에 `last_seen_broadcast_seq` 기록 규칙을 반영함

---

## 10. 복붙용 발령문

### 발령문 A (계약 동결)
`T1~T3는 계약 3종 동결 후 handoff 제출. 동결 선언 전 구현 착수 금지.`

### 발령문 B (병렬 구현)
`T4~T9는 동결 선언 이후 병렬 착수. 파일 소유권/PR 단위/보고 포맷 준수.`

### 발령문 C (최종 판정)
`최종 판정은 G1~G6 전부 통과 시 GO. 하나라도 실패하면 NO-GO.`

---

## 11. 당일 종료 체크리스트

1. 모든 터미널 handoff 파일 생성 완료
2. 블로커 open 항목 0건 또는 오너 지정 완료
3. 스모크/테스트/증빙 경로가 보고서에 연결됨
4. 다음날 첫 작업 우선순위 3개가 T0 문서에 확정됨

---

## 부록 A. 스플래시 스크린 자산 명세

> 참고 원본: `docs/2026-03-05/codex-ui-webgal-light-proposal.md` §스플래시 스크린

### 아이콘 라이브러리
- 패키지: `lucide-react` (MIT)
- 사용 아이콘: `PenLine` (1순위) 또는 `BookOpen` (대안)
- 설치: `npm install lucide-react`

### 소유 터미널
- T7 (스모크 자동화)이 스플래시 창 동작을 스모크 케이스에 포함
  - 케이스: exe 실행 → 스플래시 출현 확인 → Python ready 후 자동 닫힘 확인

### 구현 파일 경로
- 프로젝트 루트: Electron 앱 레포 (글도비 백엔드 레포와 별도 관리, 배포 시 PyInstaller 번들로 통합)
```
geuldobi-desktop/        ← Electron 프로젝트 루트
└── src/splash/
    ├── splash.html
    ├── splash.css
    └── splash.js     ← /status 폴링 + 첫 실행 감지 로직
```

### 첫 실행 감지
- 파일: `%LOCALAPPDATA%/Geuldobi/.first_run`
- 없으면 첫 실행 → "첫 실행은 잠시 시간이 걸립니다" 표시 후 파일 생성
- 있으면 → "시작하는 중..." 만 표시

---

## 부록 B. 개별 발령문 패키지

- 착수 전 확인: `docs/2026-03-06/orders_10terminals/` 내 `T1~T9` 파일 전량 존재 여부를 T0가 확인한다.
- 패키지 경로: `docs/2026-03-06/orders_10terminals/`
- 배포 가이드: `docs/2026-03-06/orders_10terminals/00_배포가이드.md`
- 전체 공지 발령문: `docs/2026-03-06/orders_10terminals/00_전체_공지_발령문.md`
- 개별 발령문: `T1`~`T9` 파일
- 종합 체크리스트: `docs/2026-03-06/orders_10terminals/99_종합_체크리스트.md`
