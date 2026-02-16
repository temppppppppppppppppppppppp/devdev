# Codex Order: 문서 3종 현행화 (Doc Sync)

> **목표**: 프로젝트 문서 3종을 코드 실제 상태에 맞게 갱신
> **범위**: 문서 수정만. 코드 변경 없음.
> **위험도**: 제로 (문서만 수정)

---

## 배경

`작업_2026-02-16.md` 백로그 전량 소진 + R5-1a 파일럿 추출까지 완료.
하지만 아래 문서 3종이 현재 상태를 반영하지 못함:

- `내일작업.md` — 테스트 기준선 낡음, R5-1a 미반영
- `docs/프로젝트_현황_로드맵_2026-02-14.md` — checkpoint/테스트 수 낡음, R5-1a/E-1/D-1~4/B-2 미반영
- `참고자료.md` — 완료된 Phase를 "미완료"로 표기 중

---

## 현재 진실 (ground truth)

```
최신 커밋: 1818357 (L3 golden route smoke + readiness truthiness fix)
테스트 기준선: 1,593+ passed, 68 xfailed (ALL GREEN)
E2E: 24 passed (L1 Smoke 8 + L2 NPC 7 + L2 Recovery 7 + L3 골든루트 2 클래스)
Ruff: 0 violations
```

### 최근 완료 항목 (문서 미반영분)

| 항목 | 커밋 | 요약 |
|------|------|------|
| E-1 Silent Pass 로깅 | `380c911` | 16건 YELLOW→logging.warning, 8파일 |
| D-1 POV 시스템 활성화 | `f0390e8` | Stage 0 POV 메뉴, 테스트 4개 |
| D-2 에피소드 롤백 | `9ba06cd` | reset_after() 3종, rollback_to() 2개, 테스트 11개 |
| D-3 StyleGuard | `79afbfd` | StyleGuard 래퍼, anti_ai/forbidden/length, 테스트 12개 |
| D-4 Director 선택 추적 | `a2c1fb2` | director_selections DB, 전략 승률, 테스트 9개 |
| B-2 Protocol 어댑터 | `d45d53c` | DraftValidator/ConstraintCompiler/StateAggregator, 테스트 9개 |
| R5-1a 파일럿 추출 | `4c9278f` | pre_director_checklist 1,579→1,109줄(-30%), 테스트 20개 |
| ✅ 상태 버그 수정 | `1818357` | system.py `is not None`→`bool()` 3곳, 테스트 4개 |
| L3 골든루트 스모크 | `1818357` | 실물 데이터+mock LLM Stage2 파이프라인, 테스트 6개 |

---

## 수정 파일별 지시

### 1. `내일작업.md`

#### 1-A. 섹션 1 "완료된 핵심 단계" 끝에 추가:
```
| R5-1a (pre_director_checklist 파일럿 추출) | 완료 | `4c9278f` — PreDirectorManuscriptChecker 450줄 분리, 1,579→1,109줄(-30%), 테스트 20개 |
| L3 스모크 + ✅ 버그 수정 | 완료 | `1818357` — system.py bool() 수정 + 골든루트 Stage2 스모크 6건 + 상태체크 4건 |
```

#### 1-B. 섹션 2 "현재 테스트 기준선" 갱신:
```bash
pytest tests/ -q  →  1,593+ passed, 68 xfailed  (ALL GREEN)
```
> checkpoint: `1818357`
> E2E: 24 passed, Ruff: 0 violations

#### 1-C. 섹션 3 "지금 남은 작업" — 기존 ✅ 항목은 유지, 아래 내용으로 교체/추가:

```markdown
### 현재 상태: 백로그 전량 소진

모든 계획된 작업이 완료됨. 아래는 선택 가능한 다음 작업:

| 우선순위 | 작업 | 규모 | 성격 |
|---------|------|------|------|
| 선택 1 | R5 계속: blocking_validator(1,394줄), relationship_tracker(1,275줄) 분할 | 중 | 구조개선 |
| 선택 2 | 작품별 Guard YAML 시스템 (config/guards/works/) | 중 | 기능 |
| 선택 3 | L3 확장: Stage 3→4 스모크, 장르 다양화 | 중 | 테스트 |
| 보류 | Phase 4-R4 async 통일 | - | NO-GO 확정 |
| 보류 | ABC 전면 표준화, JSON-in-SQLite | - | 장기 |
```

#### 1-D. 섹션 4 "현재 기술 부채" — 항목 4번 뒤에 추가:
```
5. ~~모놀리스 오케스트레이터 3대장 분할~~ → ✅ B-1 완료
   - 2차 분할(R5): pre_director_checklist R5-1a 완료(1,109줄), blocking_validator(1,394줄)/relationship_tracker(1,275줄) 미착수
6. ~~Stage 상태 표시 버그~~ → ✅ 수정 완료 (`1818357`) — `is not None` → `bool()`
```

---

### 2. `docs/프로젝트_현황_로드맵_2026-02-14.md`

#### 2-A. 파일명 변경:
`프로젝트_현황_로드맵_2026-02-14.md` → `프로젝트_현황_로드맵_2026-02-16.md`

#### 2-B. 헤더 갱신:
```markdown
# 글도비 진행 요약 (2026-02-16)

> 최종 갱신: 2026-02-16, checkpoint `1818357`
```

#### 2-C. 섹션 1 "최근 완료" 끝에 추가:
```markdown
- **E-1 완료: Silent Pass 로깅 보강**
  - `380c911` — 16건 YELLOW 패턴에 logging.warning 추가, 8파일
- **D-1 완료: POV 시스템 활성화**
  - `f0390e8` — Stage 0 POV 선택 메뉴 추가, 테스트 4개
- **D-2 완료: 에피소드 롤백 NPC 되감기**
  - `9ba06cd` — reset_after() 3종 + WorldState/FactLedger rollback_to() + 테스트 11개
- **D-3 완료: 문체 분석 → Guard 자동생성**
  - `79afbfd` — StyleGuard 래퍼 + anti_ai/forbidden/length 검증, 테스트 12개
- **D-4 완료: Director 선택 추적**
  - `a2c1fb2` — director_selections 테이블 + 전략 승률 + 롤백 호환, 테스트 9개
- **B-2 완료: Protocol 미적합 5개 어댑터**
  - `d45d53c` — DraftValidator/ConstraintCompilerProtocol/StateAggregator 3종, 테스트 9개
- **R5-1a 완료: pre_director_checklist 파일럿 추출**
  - `4c9278f` — PreDirectorManuscriptChecker 450줄 분리, 1,579→1,109줄(-30%), 테스트 20개
- **L3 스모크 + ✅ 상태 버그 수정**
  - `1818357` — system.py bool() 수정 3곳 + 골든루트 실물 데이터 Stage2 스모크 6건 + 상태체크 4건
```

#### 2-D. 섹션 2 "현재 테스트 기준선" 갱신:
```markdown
## 2) 현재 테스트 기준선

```bash
pytest tests/ -q  →  1,593+ passed, 68 xfailed  (ALL GREEN)
pytest tests/e2e/ -q  →  24 passed
```

> checkpoint: `1818357`
```

#### 2-E. 섹션 3 "다음 우선순위" 전체 교체:
```markdown
## 3) 다음 우선순위

**백로그 전량 소진. 아래는 선택 가능한 다음 작업:**

| 우선순위 | 작업 | 규모 | 비고 |
|---------|------|------|------|
| 선택 1 | R5 계속: blocking_validator(1,394줄), relationship_tracker(1,275줄) 분할 | 중 | R5-1a 파일럿 완료 |
| 선택 2 | 작품별 Guard YAML 시스템 | 중 | 신규 기능 |
| 선택 3 | L3 확장: Stage 3→4 스모크, 장르 다양화 | 중 | L3 Stage2 완료 (24 E2E) |
| 보류 | Phase 4-R4 async 통일 | - | NO-GO 확정 |
```

#### 2-F. 섹션 4 "전체 로드맵" 표 끝에 추가:
```markdown
| E-1 (Silent Pass 로깅) | ✅ 완료 (`380c911`) |
| D-1 (POV 시스템 활성화) | ✅ 완료 (`f0390e8`) |
| D-2 (에피소드 롤백 NPC 되감기) | ✅ 완료 (`9ba06cd`) |
| D-3 (문체 분석 → Guard 자동생성) | ✅ 완료 (`79afbfd`) |
| D-4 (Director 선택 추적) | ✅ 완료 (`a2c1fb2`) |
| **D. 미활용 기능 활성화** | **✅ 전체 완료** (D-1~D-4) |
| R5-1a (pre_director_checklist 파일럿) | ✅ 완료 (`4c9278f`) |
| L3 스모크 + ✅ 상태 버그 수정 | ✅ 완료 (`1818357`) |
```

---

### 3. `참고자료.md`

이 파일은 2,000줄+ 대형 참고서. **전면 재작성 금지.** 아래 최소 패치만 적용:

#### 3-A. "미완료" 표기 수정 (검색 후 교체)

아래 패턴을 찾아서 상태를 갱신:

| 검색 대상 | 현재 표기 | 수정 후 |
|-----------|----------|---------|
| Phase 6-B (E2E) | "미완료" 또는 "다음" | ✅ 완료 (`1678550`+`1818357`, E2E 24 tests) |
| D-1 POV | "미활용" / "YAML 연동만 필요" | ✅ D-1 활성화 완료 (`f0390e8`), YAML 불필요 (규칙 기반) |
| D-2 에피소드 롤백 | "NPC 되감기 추가 필요" | ✅ D-2 완료 (`9ba06cd`) |
| D-3 문체 분석 | "가드 자동생성 연동 필요" | ✅ D-3 완료 (`79afbfd`) |
| D-4 A/B 테스트 | "확장 필요" | ✅ D-4 완료 (`a2c1fb2`) Director 선택 추적 |
| E-1 Silent Pass | "미완료" 또는 "16건" | ✅ E-1 완료 (`380c911`) 16건 로깅 |
| B-2 Protocol | "미적합 5개" | ✅ B-2 완료 (`d45d53c`) 3종 Protocol 추가 |

#### 3-B. 테스트 기준선 갱신
파일 내 `1,446 passed` 또는 `1,563 passed` → `1,593+ passed, 68 xfailed`

#### 3-C. "기존에 있지만 제대로 안 쓰이는 것들" 표 갱신
해당 표에서 D-1~D-4 항목의 상태 컬럼을 ✅로 변경.

---

## 검증

```bash
# 문서만 변경이므로 코드 검증 불필요
# 단, 마크다운 렌더링 확인
python -c "print('doc sync done')"

# pre-commit (md 파일은 ruff 대상 아님, skip OK)
```

---

## 커밋

```
docs(sync): update 3 tracking docs to reflect R5-1a, L3 smoke, and full backlog completion
```

push 포함.

---

## 체크리스트

- [ ] `내일작업.md` 1-A~1-D 4개소 갱신
- [ ] `프로젝트_현황_로드맵` 파일명 변경 + 2-A~2-F 6개소 갱신
- [ ] `참고자료.md` 3-A~3-C "미완료"→"완료" 최소 패치
- [ ] 커밋 + push
