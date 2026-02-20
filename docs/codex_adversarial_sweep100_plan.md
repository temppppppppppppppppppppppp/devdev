# 적대적 복원력 (Adversarial Resilience) 100-Round Sweep Plan

> **관점**: 모든 외부 입력이 **최대한 적대적/고장**인 상태에서 시스템이 안전하게 동작하는지 검증
> **질문**: "LLM이 쓰레기를 뱉고, DB가 깨지고, API가 죽고, 파일이 잠겨도 파이프라인이 살아남는가?"

---

## 기존 스윕과의 차별점

| 기존 | 본 플랜 |
|------|---------|
| 정상 코드에서 버그 탐색 | **적대적 입력을 의도적으로 주입했을 때** 방어력 검증 |
| "버그가 있나?" | **"공격받으면 어떻게 되나?"** |

---

## Phase 1: LLM 적대적 응답 (R01–R10)

LLM이 예상과 완전히 다른 응답을 반환할 때.

| Round | 적대적 입력 | 검증 |
|-------|-----------|------|
| R01 | LLM 응답 = 빈 문자열 `""` | `_extract_json_robust` → 전체 파이프라인 안전성 |
| R02 | LLM 응답 = `"I cannot help with that"` 거부 | 거부 메시지가 JSON 파싱 방어 통과 시 |
| R03 | LLM 응답 = 거대 JSON (100KB+) | 메모리 소비, 프롬프트 삽입 시 크기 초과 |
| R04 | LLM 응답 = 유효 JSON이나 **스키마 불일치** | 키 존재하나 타입 다름 (string 대신 number) |
| R05 | LLM 응답 = 중첩 JSON (10레벨 depth) | 재귀 파싱, 스택 오버플로우 |
| R06 | LLM 응답 = Markdown 코드블록 내 JSON | ` ```json {...}``` ` 래핑 파싱 |
| R07 | LLM 응답 = 여러 JSON 객체 연결 | `{...}{...}` 두 개 연속 |
| R08 | LLM 응답 = 이전 프롬프트 echo (프롬프트 주입) | 프롬프트 텍스트가 원고로 기록 |
| R09 | LLM 응답 = Unicode 특수문자 (이모지, RTL, 제어문자) | 텍스트 처리, 정규식, DB 저장 |
| R10 | LLM 응답 = 불완전 JSON (잘린 응답) | API 토큰 초과 → 중간 절단 |

### Phase 2: LLM 콘텐츠 적대성 (R11–R20)

유효 JSON이나 **내용이 악의적**인 경우.

| Round | 적대적 콘텐츠 | 검증 |
|-------|-------------|------|
| R11 | Arc에 에피소드 수 = 0 또는 음수 | `ep_count <= 0` 방어 |
| R12 | Arc에 에피소드 수 = 10000 (극대) | 리소스 소모 방어 |
| R13 | Blueprint 장면 수 = 0 | 빈 장면 → `scene_breakdown` 빈 dict |
| R14 | 원고 텍스트 = 100만자 (극히 긴 텍스트) | 메모리, DB 저장, 프롬프트 삽입 |
| R15 | NPC 이름 = SQL injection `'; DROP TABLE--` | DB 저장 시 SQL 안전성 |
| R16 | NPC 이름 = 정규식 메타문자 `(.*)+` | ReDoS (정규식 서비스 거부) |
| R17 | 피드백 텍스트에 `{`, `}`, `{key}` 포함 | `.format()` / `.replace()` 오염 |
| R18 | 원고에 프롬프트 placeholder `{current_state_json}` | chained `.replace()` 이중 치환 |
| R19 | 파워 변화 값 = `int(2**31)` (정수 오버플로우) | 산술 연산 안전 |
| R20 | 관계 변화에 LLM 할루시네이션 NPC 대량 삽입 | 레지스트리 무한 팽창 |

### Phase 3: API 장애 (R21–R30)

Gemini API 관련 장애.

| Round | 장애 | 검증 |
|-------|------|------|
| R21 | API 429 Too Many Requests 반복 | 재시도 로직, 백오프, 모델 전환 |
| R22 | API 500 Internal Server Error | 서버 오류 처리, 재시도 횟수 제한 |
| R23 | API 타임아웃 (30초+) | `ask()` 타임아웃 → 재시도 vs 포기 |
| R24 | API 네트워크 연결 끊김 | `ConnectionError` 처리 |
| R25 | API 키 만료/무효 | 401 처리, 사용자 알림 |
| R26 | 전체 모델 할당 소진 (`_quota_exhausted_models` 전부) | 모든 모델 쿼터 소진 시 |
| R27 | API 응답 인코딩 오류 | UTF-8 아닌 응답 |
| R28 | API 응답 부분 수신 (chunked transfer 중단) | 불완전 바디 |
| R29 | 동시 API 호출 3개 중 2개 실패 | `ThreadPoolExecutor` 부분 실패 수집 |
| R30 | API 응답 지연 → `as_completed(timeout)` 만료 | 타임아웃 후 worker 정리 |

### Phase 4: DB 장애 (R31–R40)

SQLite 데이터베이스 장애.

| Round | 장애 | 검증 |
|-------|------|------|
| R31 | DB 파일 잠금 (다른 프로세스) | `OperationalError: database is locked` |
| R32 | DB 파일 손상 (corrupt) | `DatabaseError: database disk image is malformed` |
| R33 | DB 디스크 공간 부족 | 쓰기 실패 시 트랜잭션 처리 |
| R34 | DB 테이블 존재하지 않음 | 마이그레이션 미실행 |
| R35 | DB JSON 컬럼에 잘못된 JSON 저장 | `json.loads` 실패 |
| R36 | DB 동시 쓰기 (RLock 경계) | 다른 Stage에서 동시 접근 |
| R37 | DB 트랜잭션 부분 커밋 + 롤백 누락 | `vec_memory` 부분 DML |
| R38 | DB 마이그레이션 중 중단 | 스키마 부분 변경 |
| R39 | DB row 대량 삽입 (10만건+) | 벌크 연산 성능/메모리 |
| R40 | DB `VACUUM` 중 접근 | 정리 작업 중 읽기/쓰기 |

### Phase 5: 파일시스템 장애 (R41–R50)

| Round | 장애 | 검증 |
|-------|------|------|
| R41 | 프로젝트 디렉토리 없음 | 경로 생성 실패 |
| R42 | 파일 권한 없음 (읽기 전용) | 쓰기 실패 |
| R43 | 파일 인코딩 불일치 (CP949 vs UTF-8) | 한국어 파일 읽기 실패 |
| R44 | YAML 설정 파일 문법 오류 | `yaml.safe_load` 실패 |
| R45 | YAML 설정 파일 빈 파일 | `None` 반환 → 하류 접근 |
| R46 | 프롬프트 YAML 키 삭제 | 특정 키만 빈 상태 |
| R47 | 로그 파일 잠금 (Windows) | `crash_dump.log` 기록 실패 |
| R48 | 심볼릭 링크 / 순환 참조 | 디렉토리 순회 무한 루프 |
| R49 | 매우 긴 파일명 (260자+) | Windows 경로 제한 |
| R50 | 중간 저장 파일 손상 | 이전 세션 데이터 불완전 복원 |

### Phase 6: 사용자 입력 적대성 (R51–R60)

| Round | 적대적 입력 | 검증 |
|-------|-----------|------|
| R51 | `input()` EOF (비대화형 파이프라인) | stdin 없는 환경 |
| R52 | 사용자 숫자 입력에 문자 | `get_int_input` 에러 처리 |
| R53 | 사용자 선택에 범위 밖 숫자 | 메뉴 선택 경계 |
| R54 | 장르 이름에 특수문자 | 장르 → Guard 매핑 |
| R55 | 프로젝트 이름에 경로 구분자 (`/`, `\`) | 디렉토리 생성 |
| R56 | 빈 문자열 입력 (Enter만) | 기본값 처리 |
| R57 | Ctrl+C 중간 인터럽트 | 시그널 핸들링, 상태 저장 |
| R58 | 초기 설정에서 0권 0에피소드 지정 | 최소 제한 |
| R59 | 매우 큰 숫자 입력 (Arc 1000개) | 상한 방어 |
| R60 | 동일 프로젝트 중복 생성 | 기존 데이터 덮어쓰기 |

### Phase 7: 메모리/리소스 고갈 (R61–R70)

| Round | 장애 | 검증 |
|-------|------|------|
| R61 | `_context_caches` dict 무한 성장 | 캐시 크기 제한 |
| R62 | `_failures` 리스트 무한 성장 | `adaptive_retry` 메모리 누수 |
| R63 | `_cumulative_bible_cache` 무한 성장 | `db_manager` 메모리 |
| R64 | `_quota_exhausted_models` 무한 성장 | 모델 목록 |
| R65 | 에피소드 100개+ 연속 실행 | 누적 메모리 |
| R66 | ThreadPoolExecutor worker 스레드 잔존 | 스레드 리소스 누수 |
| R67 | 대형 프롬프트 (50KB+) 반복 생성 | 문자열 메모리 |
| R68 | 대형 NPC 레지스트리 (NPC 500명+) | dict 순회 성능 |
| R69 | DB 연결 미해제 | 커넥션 리소스 |
| R70 | 로그 버퍼 무한 성장 | audit_buffer 메모리 |

### Phase 8: 타이밍/순서 적대 (R71–R80)

| Round | 적대 시나리오 | 검증 |
|-------|-------------|------|
| R71 | Stage 3 진입 전에 Stage 4 호출 | 상태 미초기화 |
| R72 | Blueprint 생성 전에 원고 생성 시도 | 전제 조건 가드 |
| R73 | 두 Arc 동시 처리 시도 | 상태 충돌 |
| R74 | DB 커밋 전 다음 Stage 진입 | 미저장 데이터 |
| R75 | 캐시 무효화 전 캐시 참조 | stale 캐시 |
| R76 | StateTracker 초기화 전 상태 조회 | 미초기화 접근 |
| R77 | Context 생성 전 ctx 속성 접근 | AttributeError |
| R78 | REJECT 처리 중 PASS 판정 도착 | 판정 경쟁 |
| R79 | 재개(resume) 시 Stage 2 완료 + Stage 3 미시작 | 중간 상태 복원 |
| R80 | 에피소드 번호 역행 | 순서 보장 |

### Phase 9: 동시성 적대 (R81–R90)

| Round | 적대 시나리오 | 검증 |
|-------|-------------|------|
| R81 | 3 전략 동시 생성 중 전부 실패 | 빈 후보 리스트 |
| R82 | 병렬 LLM 호출 중 모델 전환 발생 | 공유 모델 상태 |
| R83 | `cancel()` 후 `result()` 호출 | `CancelledError` 처리 |
| R84 | 스레드 A 캐시 갱신 + 스레드 B 캐시 읽기 | 경쟁 조건 |
| R85 | 스레드 A DB 쓰기 + 스레드 B DB 읽기 | 일관성 |
| R86 | `with ThreadPoolExecutor` 내부 예외 | `__exit__` 정리 |
| R87 | Future 결과 수집 중 프로세스 종료 | 정리 안전 |
| R88 | 병렬 검증 중 validator 상태 공유 | 상태 격리 |
| R89 | 재시도 루프 + 병렬 실행 교차 | 카운터 경쟁 |
| R90 | GIL 해제 구간 (I/O) 중 공유 dict 수정 | 읽기/쓰기 충돌 |

### Phase 10: 복합 장애 시나리오 (R91–R100)

| Round | 복합 장애 | 검증 |
|-------|----------|------|
| R91 | LLM 거부 + DB 잠금 동시 | 이중 실패 복구 |
| R92 | API 타임아웃 + 스레드 미취소 + 재시도 | 3중 장애 연쇄 |
| R93 | YAML 손상 + 기본값 fallback + LLM 호출 | 설정 부재 상태 기능 |
| R94 | NPC 대량 삽입 + DB 저장 실패 + 메모리 | 리소스 포화 |
| R95 | 5라운드 전부 REJECT + DB 커밋 실패 | 폴백 경로 + 저장 실패 |
| R96 | 재개 + 이전 상태 손상 + LLM 거부 | 복원 불가 상태 |
| R97 | 전체 모델 쿼터 소진 + 중간 Stage | 진행 불가 상태 핸들링 |
| R98 | 병렬 API 전부 실패 + 타임아웃 + 재시도 소진 | 최악 케이스 |
| R99 | 디스크 공간 부족 + DB + 로그 + 파일 모두 실패 | 전체 I/O 실패 |
| R100 | 전체 Phase 1-9 결과 교차 검증 | 종합 방어력 평가 |

---

## 출력 형식

```markdown
## Round N — [적대 시나리오]

### 공격 정의
- **입력/장애**: [구체적 적대 조건]
- **기대 방어**: 안전한 에러 처리 + 파이프라인 지속

### 방어 경로 추적
**[방어 지점 1: 파일:함수:L100]**
- 코드: `실제 코드`
- 방어 결과: ✅ 안전 / ❌ 크래시 / ⚠️ 부분 방어

### 발견
- **방어력**: 완전 / 부분 / 없음
- **최악 시나리오**: [발생 시 결과]
```

## 결과 파일
- 플랜: `docs/codex_adversarial_sweep100_plan.md`
- 결과: `docs/codex_findings_adversarial_sweep100.md`

---

## 무중단 수동검사 강제 가드 (필수)

본 섹션은 본 플랜 수행 시 최우선 강제 규칙이다. 자동 스캔 흔적이 있으면 라운드를 무효 처리한다.

### 1) 수동 검사 강제 / 검색 금지
- 금지 도구: `rg`, `grep`, `freg`, `greg`, `Select-String`, `findstr`, `git grep`, IDE 전역 검색, 기타 패턴 검색 자동화 전부.
- 허용 방식: 대상 파일을 직접 열람하는 단순 읽기만 허용 (`Get-Content`, 에디터 수동 열람).
- 근거 규칙: 모든 판정은 최소 1개 이상의 `file:line` 근거를 포함해야 하며, 근거는 수동 열람 내용이어야 한다.
- 위반 처리: 검색 기반 근거가 1회라도 확인되면 해당 라운드는 무효이며 동일 라운드를 처음부터 재수행한다.

### 2) 무중단 수행 규칙
- 기본 원칙: Round 1~100을 사용자 재질문 없이 연속 수행한다.
- 중간 정산/요약은 허용하되, 수행 중단 사유로 사용하지 않는다.
- 중단 허용(하드 블로커) 조건:
  - 대상 파일 실존 불가
  - 파일 권한/잠금으로 열람 불가
  - 문서/코드 파손으로 라인 판독 불가
- 하드 블로커 발생 시 1회만 아래 포맷으로 보고한다:
  - `Blocker`: [원인]
  - `Last Completed Round`: [N]
  - `Resume Condition`: [필요 조치]

### 3) 컨텍스트 컴팩트 내성 규칙
- 컨텍스트 컴팩트 발생 시 즉시 플랜 문서와 결과 문서의 마지막 완료 라운드를 기준으로 상태를 복구한다.
- 복구 직후 사용자 문의 없이 `Last Completed Round + 1`부터 재개한다.
- 라운드마다 다음 최소 메타를 남긴다:
  - `Last Completed Round`
  - `Last Read Files`
  - `Next Round`

### 4) 라운드 출력 스키마 (고정)
- 각 라운드는 아래 섹션을 반드시 모두 포함한다:
  - `Read Files`
  - `Manual Inspection Evidence`
  - `Confirmed Bugs`
  - `Risks`
  - `False Positives Excluded`
  - `Test Gaps`
- `Manual Inspection Evidence`는 최소 2개 bullet로 작성하고, 각 bullet에 `file:line`을 포함한다.
- `Confirmed Bugs`가 `none`이 아닌 경우:
  - `[P0]`~`[P3]` severity 태그 필수
  - `file:line` 필수
  - 기존 의도/철학과 충돌 여부(`intent check`) 필수
- 각 라운드에 `Intent Alignment Check`를 추가한다:
  - `Candidate Intent`
  - `Intent Evidence (file:line)`
  - `Conflict Evidence (file:line or none)`
  - `Decision (Aligned / Conflict / Unclear)`

### 5) 오탐 방지 / 설계 의도 보존 게이트
- `BUG` 확정 전 아래 항목을 모두 기록한다:
  - `Intent Source`: 주석/함수명/정책명/상수/가드 로직 근거 (`file:line`)
  - `Caller Contract`: 상위 호출자 기대 동작 근거 (`file:line`)
  - `Fallback Policy`: 비차단/Advisory/Fallback 경로 존재 여부 (`file:line`)
  - `Reachability`: 실제 도달 가능한 호출 경로 (`file:line`)
  - `Blast Radius`: 장애 전파 범위와 발현 조건
- 판정 규칙:
  - 의도 근거와 충돌 근거가 동시에 존재하면 `Confirmed Bugs` 금지, `Risks`로 분류
  - 정책 의도와 합치하고 가드가 존재하면 `False Positives Excluded`로 분류
  - 의도와 명확히 충돌 + 도달 가능 + 보호 부재일 때만 `Confirmed Bugs`로 확정
- 금지 규칙:
  - 단일 라인/단일 파일 근거만으로 버그 확정 금지 (최소 2파일 근거 필수)
  - 일반 베스트 프랙티스 위반만으로 버그 확정 금지
- 기록 의무:
  - 모든 BUG/RISK 항목에 `intent check: pass/fail/unclear` 표기
  - `unclear`는 BUG 금지, RISK로 유지 후 후속 검증 항목에 추가

### 6) 판정 주권 규칙 (Director Sovereignty / 내각제)
- Python/정적 규칙/검증 스크립트는 `WARNING` 또는 `ADVISORY`까지만 가능하며, 단독 `REJECT`/`BLOCK` 판정은 금지한다.
- 자동 검사의 역할은 이상 징후 플래그와 근거 수집 보조에 한정한다.
- 최종 판정 주권:
  - `REJECT`/`PASS` 최종 결정은 Director LLM(단일 또는 ensemble)만 수행한다.
- 충돌 처리:
  - Python 경고 vs Director 승인: `False Positives Excluded`로 기록
  - Python 경고 vs Director 반려: Director 근거와 함께 `Confirmed Bugs` 또는 `Risks`로 기록
- Director 판정 불가(응답 없음/보류) 시:
  - `Pending Director Decision`으로 기록하고 `REJECT` 확정 금지

### 7) 체크포인트/품질 게이트
- 매 10라운드마다 체크포인트를 작성한다.
- 체크포인트 최소 항목:
  - Cumulative Confirmed Bugs (P0~P3 분해)
  - Cumulative Risks
  - Cumulative False Positives Excluded
  - Cumulative Test Gaps
  - Phase False-Positive Ratio
  - Consecutive Empty Rounds
  - Manual Evidence Compliance Rate

### 8) 최종 유효성 판정 (완료 조건)
- 아래 검증을 모두 통과해야 완료로 인정한다.
- `python scripts/validate_manual_sweep.py docs/codex_findings_adversarial_sweep100.md --from-round 1 --to-round 100`
- `python scripts/validate_manual_sweep.py docs/codex_findings_adversarial_sweep100.md --from-round 1 --to-round 100 --max-fp-ratio 0.35 --max-fp-streak 2`
- 위 Python 검증은 문서 형식/근거 충족 여부 확인용이며, 최종 내용 판정(REJECT/PASS) 권한이 아니다.
- 검증 실패 시 실패 라운드를 수정하고 재검증한다.
