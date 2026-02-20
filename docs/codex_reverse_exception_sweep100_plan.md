# 역방향 예외 소거 100-Round Sweep Plan

> **관점**: 크래시 증상(예외 유형)에서 출발 → 모든 가능한 원인 경로를 **역추적**하여 소거
> **기존 스윕이 "코드를 읽고 → 문제를 찾는" 정방향이라면, 이 플랜은 "크래시에서 출발 → 원인으로 거슬러가는" 역방향**

---

## 기존 스윕과의 차별점

| 관점 | 방향 | 본 플랜 |
|------|------|---------|
| 파일별/시나리오/생애주기 | 정방향 (코드 → 버그) | **역방향 (예외 → 코드 경로 소거)** |
| 질문 | "여기에 문제가 있나?" | **"TypeError를 만드는 모든 경로가 방어되었나?"** |

---

## 10개 카테고리 × 10 라운드

### Phase 1: TypeError 역추적 (R01–R10)

`int()`, `float()`, `str+int`, `NoneType has no attribute` 등 타입 오류.

| Round | 예외 트리거 | 역추적 대상 |
|-------|-----------|-------------|
| R01 | `int(None)` — `.get()` 반환 None에 int() 호출 | `ep_count`, `ep_start`, `arc_no` 전체 `int()` 캐스트 역추적 |
| R02 | `str + int` — 문자열 산술 | `ep_end = ep_start + ep_count - 1` 경로, LLM이 string 반환 시 |
| R03 | `NoneType.get()` — None에 dict 메서드 호출 | `arc_data.get("state_constraints").get("...")` 체인 전체 |
| R04 | `NoneType.split()` — None에 문자열 메서드 호출 | `tactical_doc`, `constraint_summary` 등 str 기대 필드 |
| R05 | `NoneType.append()` — None 리스트에 추가 | `stage_rejection_history`, `_failures` 등 리스트 필드 |
| R06 | `list + dict` — 타입 혼재 산술 | `physical_inventory` str/dict 혼재, `items_acquired` |
| R07 | `bool(dict)` vs `len(dict)` 혼동 | 빈 dict가 truthy → 잘못된 분기 진입 경로 |
| R08 | `iter(string)` — 문자열을 리스트로 착각한 반복 | `state_changes` string 유입 시 char-by-char 반복 |
| R09 | `int(str)` — 숫자가 아닌 문자열 int 캐스트 | LLM 응답에 `"다섯"`, `"5개"` 등 비숫자 유입 |
| R10 | `float("inf")` / `float("nan")` 비교 | 점수 계산 경로에서 inf/nan 전파 |

### Phase 2: KeyError 역추적 (R11–R20)

dict 키 접근 실패.

| Round | 예외 트리거 | 역추적 대상 |
|-------|-----------|-------------|
| R11 | `dict["missing_key"]` — bracket 접근 | `refined_arc["action"]`, `draft_result["warnings"]` 등 전체 |
| R12 | `.get()` 없는 중첩 접근 | `data["a"]["b"]` 패턴 — 중간 키 부재 시 |
| R13 | `issue["severity"]` — LLM 응답 dict | analyst.py 등 LLM 반환 dict의 필수 키 보장 |
| R14 | `f-string {key}` — format 키 부재 | `.format(**dict)` 시 dict에 기대 키 누락 |
| R15 | `pop("key")` — 존재하지 않는 키 pop | 삭제 연산 시 키 존재 사전 확인 |
| R16 | Pydantic `extra="allow"` 키의 bracket 접근 | `model_dump()` 후 extra 키 접근 패턴 |
| R17 | JSON Schema 키 vs 런타임 키 불일치 | `response_schemas.py` 정의 vs 실제 LLM 출력 vs 코드 접근 |
| R18 | 조건부 키 (장르별 존재/부재) | 투자 장르에만 있는 키를 범용 경로에서 접근 |
| R19 | 캐시 키 충돌 | 같은 키에 다른 값 덮어쓰기, 키 해시 충돌 |
| R20 | DB 컬럼 이름 변경 후 잔존 접근 | 마이그레이션 후 옛 이름 접근 잔존 |

### Phase 3: AttributeError 역추적 (R21–R30)

객체 속성 접근 실패.

| Round | 예외 트리거 | 역추적 대상 |
|-------|-----------|-------------|
| R21 | `self.ctx.xxx` — DI 미바인딩 속성 | Context `__slots__` vs `from_app()` 바인딩 격차 |
| R22 | `getattr(None, "method")` — None 객체 메서드 호출 | lazy init 전 접근, `state_tracker=None` |
| R23 | `app.current_project` 부재 | 프로젝트 미선택 상태에서 Stage 진입 |
| R24 | `self.xxx` 초기화 순서 의존 | `__init__` 내 순서-의존적 속성 참조 |
| R25 | Protocol 메서드 미구현 | `StateServiceProtocol` 70개 중 미구현 메서드 호출 |
| R26 | 동적 속성 (`setattr`/`delattr`) 후 접근 | 런타임 동적 속성 추가/삭제 후 잔존 참조 |
| R27 | import 실패 fallback 경로 | `ImportError` catch 후 모듈 None → 메서드 호출 |
| R28 | `selected_candidate.get(...)` — None 후보 | `director_ensemble` 투표 결과 None |
| R29 | Guard 객체 미등록 | 장르 미매칭 시 Guard=None → 메서드 호출 |
| R30 | 삭제된 모듈 잔존 참조 | sweep300에서 삭제된 모듈 import 잔존 |

### Phase 4: IndexError / ValueError 역추적 (R31–R40)

리스트 인덱스, 값 오류.

| Round | 예외 트리거 | 역추적 대상 |
|-------|-----------|-------------|
| R31 | `list[0]` — 빈 리스트 첫 원소 접근 | `candidates[0]`, `arcs[0]` 등 |
| R32 | `str.split()[N]` — 분할 결과 원소 부족 | LLM 응답 파싱 시 split 후 인덱스 |
| R33 | `max([])` / `min([])` — 빈 시퀀스 | 점수 리스트, 후보 리스트 aggregate |
| R34 | `list.index(x)` — 존재하지 않는 원소 | 인덱스 검색 후 사용 |
| R35 | `list[-1]` — 빈 리스트 마지막 원소 | 최근 에피소드 접근 패턴 |
| R36 | `int("abc")` — ValueError | 설정 파싱, 사용자 입력 파싱 |
| R37 | `json.loads("invalid")` — JSONDecodeError | LLM 응답, DB 저장 값 역직렬화 |
| R38 | `re.compile("[invalid")` — 잘못된 정규식 | LLM/사용자 입력이 정규식 패턴에 삽입 |
| R39 | slice 범위 초과 | `manuscript[:3000]` 등 절삭 → 빈 결과 |
| R40 | `enum(value)` — 존재하지 않는 enum 값 | 상태 코드, verdict 값 매핑 |

### Phase 5: ZeroDivisionError 역추적 (R41–R50)

0 나누기 — 동적 분모.

| Round | 예외 트리거 | 역추적 대상 |
|-------|-----------|-------------|
| R41 | `score / total_weight` — 가중치 합 0 | `scoring_validator` 가중치 합산 |
| R42 | `count / len(items)` — 빈 리스트 길이 | 통계 계산 전체 경로 |
| R43 | `ratio = a / b` — 비율 계산 | FP ratio, pass rate, 점수 비율 |
| R44 | `average = sum(scores) / len(scores)` — 빈 점수 | 평균 점수 계산 경로 |
| R45 | `episodes_per_arc` 동적 값 0 | 볼륨 설정에서 유래한 나누기 |
| R46 | `progress = current / total` — total 0 | 진행률 계산 |
| R47 | `normalize = value / max_value` — max 0 | 점수 정규화 |
| R48 | `frequency = count / total_words` — 빈 원고 | 단어 빈도 분석 |
| R49 | `scene_allocation = total / num_scenes` — 장면 0 | 장면 분배 계산 |
| R50 | 복합: 정수 나누기 + 반올림 | `int(a / b)` vs `a // b` 차이 |

### Phase 6: 무한 루프 / 교착 역추적 (R51–R60)

프로그램이 멈추는 경로.

| Round | 증상 | 역추적 대상 |
|-------|------|-------------|
| R51 | `input()` 비대화형 차단 | 모든 `input()` / `get_int_input()` 호출 위치 |
| R52 | `while True` 탈출 조건 누락 | 재시도 루프 max_attempts 강제 |
| R53 | `ThreadPoolExecutor` shutdown 대기 | `with` 블록 내 timeout 후 계속 대기 |
| R54 | `future.result(timeout)` 후 미취소 | cancel 미동작 → worker 계속 실행 |
| R55 | `RLock` 재진입 데드락 | `db_manager` RLock 교차 호출 경로 |
| R56 | 재시도 루프 카운터 리셋 | retry 중 카운터가 불의로 리셋되는 경로 |
| R57 | 무한 재귀 | 간접 재귀 호출 체인 |
| R58 | asyncio 이벤트 루프 차단 | sync 호출이 async 루프 내 실행 |
| R59 | DB 트랜잭션 미종료 | `conn.in_transaction=True` 영구 유지 |
| R60 | 메모리 무한 성장 → OOM | 캐시/리스트 unbounded 성장 전체 |

### Phase 7: 데이터 오염 (Silent Corruption) 역추적 (R61–R70)

크래시 없이 **잘못된 결과**를 내는 경로.

| Round | 증상 | 역추적 대상 |
|-------|------|-------------|
| R61 | dead store — 대입 후 미사용 | 값 계산 → 변수 저장 → 이후 다른 변수 사용 |
| R62 | stale 캐시 사용 | 데이터 갱신 후 캐시 미무효화 → 옛 값 전파 |
| R63 | 조건문 and/or 혼동 | `if a and b` vs `if a or b` — 의도 반전 |
| R64 | 비교 방향 반전 | `>=` vs `<=`, `>` vs `<` 뒤바뀜 |
| R65 | 기본값 타입 불일치 | `.get("key", 0)` → int 기대인데 downstream에서 str 기대 |
| R66 | `.replace()` 연쇄 오염 | 이미 삽입된 텍스트 내 placeholder 이중 치환 |
| R67 | 캐시 변경 후 무효화 누락 | 데이터 수정 → 관련 캐시 None 미설정 |
| R68 | 하드코딩 값으로 기능 비활성화 | `if False:`, `threshold = 999999` 등 |
| R69 | 에피소드 번호 off-by-one | `episode - 1` 인덱싱 0-based vs 1-based 혼재 |
| R70 | 부동소수점 비교 오류 | `0.1 + 0.2 != 0.3` 류 비교 |

### Phase 8: set/unhashable 오류 역추적 (R71–R80)

`set()` 연산 시 unhashable 타입.

| Round | 예외 트리거 | 역추적 대상 |
|-------|-----------|-------------|
| R71 | `set(list_of_dicts)` | `items_acquired` dict 원소 → set 변환 |
| R72 | `set.update(list_of_mixed)` | str + dict 혼재 리스트 → set 연산 |
| R73 | `set.intersection()` 타입 불일치 | 두 set의 원소 타입 차이 |
| R74 | `dict` 키에 unhashable 사용 | list를 dict 키로 사용 시도 |
| R75 | `in` 연산 unhashable | `dict_item in set` 체크 |
| R76 | `frozenset` 변환 실패 | mutable 원소 포함 리스트 → frozenset |
| R77 | 중복 제거 목적 set 변환 | NPC 이름 중복 제거 시 dict 엔트리 혼재 |
| R78 | `collections.Counter` unhashable | 빈도 계산 시 unhashable 원소 |
| R79 | Jaccard 유사도 set 연산 | 문자열/dict 혼재 비교 대상 |
| R80 | sorted() key function 타입 혼재 | str과 int 혼재 정렬 |

### Phase 9: 정규식 오류 역추적 (R81–R90)

`re` 모듈 관련 오류.

| Round | 예외 트리거 | 역추적 대상 |
|-------|-----------|-------------|
| R81 | `re.compile(user_input)` — 미이스케이프 | LLM 생성 NPC 이름에 `(`, `[`, `*` 포함 |
| R82 | `re.search(pattern, None)` | 대상 문자열 None |
| R83 | `re.sub` 교체 문자열 내 `\1` 역참조 오류 | 교체 패턴에 사용자 텍스트 삽입 |
| R84 | 장르 가드 금기어 정규식 | YAML에서 로드한 패턴 유효성 |
| R85 | `re.DOTALL` 누락 | 여러 줄 텍스트 매칭 실패 |
| R86 | greedy vs lazy 매칭 | `.*` vs `.*?` 차이로 과대/과소 매칭 |
| R87 | Unicode 정규식 | 한국어/특수문자 매칭 실패 |
| R88 | `re.compile` 캐싱 | 동일 패턴 반복 컴파일 vs `re.cache` |
| R89 | group 인덱스 초과 | `match.group(N)` — N번 그룹 부재 |
| R90 | 빈 문자열 매치 | `re.search("", text)` — 항상 매치 |

### Phase 10: DB/IO 오류 역추적 (R91–R100)

SQLite, 파일시스템, 네트워크 오류.

| Round | 예외 트리거 | 역추적 대상 |
|-------|-----------|-------------|
| R91 | `sqlite3.OperationalError` — 테이블 부재 | 마이그레이션 미실행 상태 |
| R92 | `sqlite3.IntegrityError` — 제약 위반 | UNIQUE, NOT NULL 제약 |
| R93 | JSON 컬럼 저장 → 읽기 불일치 | `json.dumps` → `json.loads` 라운드트립 |
| R94 | 파일 인코딩 오류 | UTF-8 vs CP949 혼재 |
| R95 | 파일 잠금 (Windows) | 다른 프로세스 파일 접근 중 |
| R96 | API 429 (Rate Limit) 처리 | Gemini API 할당 초과 → 재시도 |
| R97 | API 응답 truncation | 긴 응답 잘림 → 불완전 JSON |
| R98 | 디스크 공간 부족 | DB 저장, 로그 기록 실패 |
| R99 | 네트워크 타임아웃 | API 호출 중 연결 끊김 |
| R100 | 복합 장애 | DB 오류 + API 실패 + 파일 잠금 동시 발생 |

---

## 라운드별 출력 형식

```markdown
## Round N — [예외 유형]: [트리거 패턴]

### 예외 정의
- **예외**: `TypeError` / `KeyError` / etc.
- **트리거**: [구체적 코드 패턴]
- **심각도**: CRITICAL / HIGH / MEDIUM

### 역추적 경로 (발생 가능 위치 소거)
**[위치 1: 파일A:L100]**
- 코드: `실제 코드`
- 방어 여부: ✅ 방어됨 (가드 코드: `if x is not None:`) / ❌ 미방어
- 도달 가능성: [caller에서 None 전달 가능한 경로]

**[위치 2: 파일B:L200]**
- 코드: `실제 코드`
- 방어 여부: ✅ / ❌
- 도달 가능성: [caller 분석]

### 소거 결과
- 총 위치: N개
- 방어됨: M개
- **미방어: K개** → BUG 후보
- FP 체크: FP-1~10 교차 확인

---
## Round N 완료
```

## 결과 파일
- 플랜: `docs/codex_reverse_exception_sweep100_plan.md`
- 결과: `docs/codex_findings_reverse_exception_sweep100.md`

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
- `python scripts/validate_manual_sweep.py docs/codex_findings_reverse_exception_sweep100.md --from-round 1 --to-round 100`
- `python scripts/validate_manual_sweep.py docs/codex_findings_reverse_exception_sweep100.md --from-round 1 --to-round 100 --max-fp-ratio 0.35 --max-fp-streak 2`
- 위 Python 검증은 문서 형식/근거 충족 여부 확인용이며, 최종 내용 판정(REJECT/PASS) 권한이 아니다.
- 검증 실패 시 실패 라운드를 수정하고 재검증한다.
