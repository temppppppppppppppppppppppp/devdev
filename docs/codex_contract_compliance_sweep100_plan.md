# 계약·프로토콜 준수 감사 100-Round Sweep Plan

> **관점**: Protocol 정의 ↔ 구현체 ↔ 호출자 3자간 **계약 일치** 검증
> **질문**: "Protocol에 정의된 메서드가 올바르게 구현되고 호출자가 계약대로 사용하는가?"

---

## 10개 Phase × 10 라운드

### Phase 1: Service Protocol (R01–R10)
`protocols/app_services.py` vs `main_a.py` vs 오케스트레이터.

| Round | 대상 |
|-------|------|
| R01 | `UIServiceProtocol` — `log()`, `title()` |
| R02 | `AuditServiceProtocol` — `audit_event()`, `flush`, `write` |
| R03 | `ProjectRepositoryProtocol` — `name`, `master_bible`, `volumes`, `arcs` |
| R04 | `StateServiceProtocol` — 추출 메서드 그룹 |
| R05 | `StateServiceProtocol` — 조회 메서드 그룹 |
| R06 | `StateServiceProtocol` — 변경 메서드 그룹 |
| R07 | Protocol 미정의 — `app.xxx` 호출 중 Protocol 누락 탐색 |
| R08 | Protocol 정의 — `SovereignApp` 미구현 메서드 탐색 |
| R09 | 반환 타입 계약 정합 |
| R10 | Optional 반환 vs 호출자 None Guard |

### Phase 2: Agent Protocol (R11–R20)
`protocols/agents.py` — 에이전트 인터페이스.

| Round | 대상 |
|-------|------|
| R11 | `BaseAgent` — `ask()`, `_extract_json_robust()` 오버라이드 |
| R12 | `Analyst` 반환 dict 구조 vs 호출자 |
| R13 | `ChiefWriter` `generate_ensemble()` → list[dict] |
| R14 | `Director` 감사/채점/앙상블 반환값 |
| R15 | `BlueprintGenerator` 3단계 반환 구조 |
| R16 | `StateTracker` 70+ 메서드 중 실제 호출 메서드 입출력 |
| R17 | `ContinuityInspector` facade 위임 시그니처 |
| R18 | `ArcEnsemble`/`BlueprintEnsemble` 투표 입출력 |
| R19 | `ConsensusValidator` 결과 병합 |
| R20 | `BlockEnricher` 블록 입출력 구조 |

### Phase 3: Validator Protocol (R21–R30)
`protocols/validators.py` — 검증기 계약.

| Round | 대상 |
|-------|------|
| R21 | `ValidatorProtocol` — `validate()` 시그니처, 반환 dict (`verdict`/`score`/`feedback`) |
| R22 | `BlockingValidator` BLOCK/PASS 구조 |
| R23 | `ScoringValidator` 점수 dict, 카테고리 키 |
| R24 | `PreLLMValidator` 사전 검증 → Orchestrator 소비 |
| R25 | `ConsistencyValidator` 일관성 점수 + 위반 사항 |
| R26 | `ContinuityValidator` 연속성 점수 |
| R27 | `RetrospectiveValidator` 과거 데이터 기반 |
| R28 | `ValidationOrchestrator` 개별 → 최종 verdict 변환 |
| R29 | Validator 간 우선순위/순서 |
| R30 | `_threshold()` YAML 키 → 기본값 fallback |

### Phase 4: DB Repository 계약 (R31–R40)

| Round | 대상 |
|-------|------|
| R31 | CRUD 시그니처 — Protocol vs `db_manager.py` |
| R32 | 트랜잭션 — `safe_commit` 반환, rollback 보장 |
| R33 | JSON 직렬화 라운드트립 |
| R34 | 스레드 안전 — RLock 범위 |
| R35 | 마이그레이션 — 기존 데이터 보존 |
| R36 | 캐시 갱신/무효화 타이밍 |
| R37 | 벌크 조회 — row-level 에러 처리 |
| R38 | `vec_memory` 트랜잭션 계약 |
| R39 | 동시 접근 패턴 |
| R40 | 삭제 cascade 계약 |

### Phase 5: DI Context 계약 (R41–R50)

| Round | 대상 |
|-------|------|
| R41 | `Stage2Context.__slots__` vs `from_app()` 바인딩 전수 |
| R42 | `Stage3Context.__slots__` vs `from_app()` 바인딩 전수 |
| R43 | `Stage4Context.__slots__` vs `from_app()` 바인딩 전수 |
| R44 | 선택적 바인딩 하류 None Guard |
| R45 | 콜백 시그니처 정합 |
| R46 | Stage 전환 시 공유 속성 계승 |
| R47 | `app.xxx` vs `ctx.xxx` 이름 매핑 |
| R48 | `from_app` 예외 → 부분 초기화 |
| R49 | Context 불변 vs 가변 필드 |
| R50 | Context 수명 보장 |

### Phase 6: Response Schema 계약 (R51–R60)

| Round | 대상 |
|-------|------|
| R51 | `ARC_DESIGN_SCHEMA` vs `ArcData` Pydantic |
| R52 | `ARC_STATE_CONSTRAINTS_SCHEMA` vs `StateConstraints` |
| R53 | `BLUEPRINT_SCHEMA` vs `Blueprint` Pydantic |
| R54 | Schema `required` vs Pydantic `default` 불일치 |
| R55 | LLM 실제 출력 vs Schema (미정의 키 생성 패턴) |
| R56 | `_extract_json_robust` 반환 분기 vs 호출자 기대 |
| R57 | 스키마 버전 하위 호환성 |
| R58 | 프롬프트 내 스키마 삽입 경로 |
| R59 | 스키마 키 이름 vs 코드 접근 키 이름 |
| R60 | `model_validator` 전처리기 부작용 |

### Phase 7: Prompt 계약 (R61–R70)

| Round | 대상 |
|-------|------|
| R61 | YAML 프롬프트 키 vs `prompt_loader` |
| R62 | placeholder vs `.replace()` 전체 목록 |
| R63–R66 | `analyst_prompts`, `director_prompts`, `chief_writer_prompts`, `writer_prompt_builders` 파라미터 |
| R67 | 프롬프트 크기 제한 → 절삭 → 정보 손실 |
| R68 | system/user prompt 분리 |
| R69 | 프롬프트 캐싱 키 계약 |
| R70 | `{}` 중괄호, `\n` 이스케이프 |

### Phase 8: 에러 정책 계약 (R71–R80)

| Round | 대상 |
|-------|------|
| R71 | CRITICAL — re-raise 준수 |
| R72 | IMPORTANT — log+safe default |
| R73 | OPTIONAL — pass/warning |
| R74 | `[SilentPass:모듈명]` 표준 준수 |
| R75 | `except Exception` vs specific 적절성 |
| R76 | 하위→상위 예외 전파 |
| R77 | 비차단 원칙 (FP-1) 준수 |
| R78 | Advisory 비개입 (FP-2) 준수 |
| R79 | 에러 메시지 형식 (`[모듈명]` 접두사) |
| R80 | 에러 복구 후 상태 일관성 |

### Phase 9: Guard 체인 계약 (R81–R90)

| Round | 대상 |
|-------|------|
| R81 | Genre→Work→Style 순서 보장 |
| R82 | `base_guard` 추상 메서드 vs 서브클래스 구현 |
| R83 | Guard 반환 PASS/WARN/BLOCK 구조 |
| R84 | 장르→Guard 클래스 매핑 완전성 |
| R85 | Guard YAML 설정 키 정합 |
| R86 | deep validation 반환 구조 |
| R87 | Guard 실패 시 파이프라인 계속 |
| R88 | 금기어 정규식 YAML→`re.compile` 유효성 |
| R89 | Guard 결과→ValidationOrchestrator 통합 |
| R90 | 장르 변경 시 Guard 재로드 |

### Phase 10: Stage 전환 계약 (R91–R100)

| Round | 대상 |
|-------|------|
| R91 | Stage 0 → app 초기화 바인딩 완전성 |
| R92 | Stage 0→2 사전 조건 (bible, volumes, genre) |
| R93 | Stage 2→3 (arcs, DB 커밋) |
| R94 | Stage 3→4 (blueprints, tracker) |
| R95 | Stage 4→종료 (post_episode, DB 최종 커밋) |
| R96 | 중간 실패→재개 상태 복원 |
| R97 | 다중 Arc 간 누적 상태 |
| R98 | 다중 Episode 간 누적 상태 |
| R99 | 전체 파이프라인 불변 조건 |
| R100 | Phase 1-9 교차 검증 |

---

## 출력 형식

```markdown
## Round N — [계약 대상]

### 계약 정의
- **Protocol**: [파일:라인]
- **구현체**: [파일:라인]
- **호출자**: [파일:라인]

### 3자간 검증
Protocol 시그니처 → 구현체 실제 시그니처 → 호출자 사용 패턴

### 발견
- 계약 위반 유형: 시그니처/반환타입/미구현/과잉의존
- 영향: [런타임 영향]
```

## 결과 파일
- 플랜: `docs/codex_contract_compliance_sweep100_plan.md`
- 결과: `docs/codex_findings_contract_compliance_sweep100.md`

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
- `python scripts/validate_manual_sweep.py docs/codex_findings_contract_compliance_sweep100.md --from-round 1 --to-round 100`
- `python scripts/validate_manual_sweep.py docs/codex_findings_contract_compliance_sweep100.md --from-round 1 --to-round 100 --max-fp-ratio 0.35 --max-fp-streak 2`
- 위 Python 검증은 문서 형식/근거 충족 여부 확인용이며, 최종 내용 판정(REJECT/PASS) 권한이 아니다.
- 검증 실패 시 실패 라운드를 수정하고 재검증한다.
