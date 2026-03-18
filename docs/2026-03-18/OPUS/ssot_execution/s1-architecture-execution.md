# S1 아키텍처 개관 — 실행문서

> 소스: S1 SSOT (2026-03-18)
> 감리: 기본 3pass + 적대적 5pass
> 작성: 2026-03-18

---

## 실행 항목

| ID | 항목 | 우선순위 | 상세 내용 | 완료 기준 | 추정 공수 | 의존성 | S1 근거 |
|----|------|----------|-----------|-----------|-----------|--------|---------|
| S1-EX-001 | `.gitattributes` 파일 생성 및 CRLF 정책 확립 | P0 (즉시) | `.gitattributes` 파일이 부재하여 Windows 환경에서 LF/CRLF 혼재 발생. `git diff` 시 CRLF 경고 8건 확인. `*.py text eol=lf`, `*.js text eol=lf`, `*.html text eol=lf`, `*.yaml text eol=lf`, `*.json text eol=lf` 등 주요 확장자별 정책을 명시하고, `.editorconfig`에 `end_of_line = lf` 추가 (현재 `.editorconfig` `[*]` 블록 line 3-5에 `charset`/`insert_final_newline`만 존재 → line 5 `insert_final_newline = true` 다음에 `end_of_line = lf` 삽입). | (1) `.gitattributes` 파일 존재 (2) `git diff` 실행 시 CRLF 경고 0건 (3) `.editorconfig`에 `end_of_line = lf` 명시 (4) CI 또는 pre-commit hook에서 line-ending 검사 통과 | 0.5h | 없음 | S1 §10.1: ".gitattributes 부재 → CRLF 경고 8건"; S1 §8: ".editorconfig에 end_of_line 미지정" |
| S1-EX-002 | CRLF 혼재 파일 일괄 정규화 | P0 (즉시) | `.gitattributes` 적용 후 기존 파일의 line ending을 일괄 정규화. `git add --renormalize .` 실행 후 커밋. 경고 발생 파일 8건을 특정하여 변환 확인. CRLF 파일 열거 명령: `git diff --check HEAD~1 2>/dev/null | grep "trailing whitespace\|CRLF" | head -20` | (1) `git grep -I -l $'\r'` 결과 0건 (2) 정규화 커밋 완료 (3) 이후 `git diff` 시 CRLF 관련 경고 0건 | 0.5h | S1-EX-001 | S1 §10.1: "CRLF 경고 8건"; S1 §8: "Windows LF/CRLF 혼재 가능" |
| S1-EX-003 | Stage 3 패칭 안정성 회귀 검증 | P1 (이번 주) | 서베이 시점 Stage 3가 PATCHING 상태. Gemini API `additionalProperties` 미지원으로 인한 `schema_incompatible` 에러에 대해 4계층 수정(스키마 +71/-71 LOC, 에러 분류 +4 LOC, 빠른 실패 +21/-1 LOC, 상태 리셋 +1 LOC)이 적용됨. 4계층 수정 대상 파일: `modules/core/response_schemas.py`, `modules/domain/agents/base_agent.py`, `modules/domain/agents/blueprint_ensemble.py`, `modules/domain/agents/three_phase_blueprint_generator.py`. 패치 후 94 테스트 통과 확인되었으나, 패치가 다른 스테이지에 미치는 부작용 여부를 회귀 테스트로 검증 필요. 테스트 실행 명령: `cd C:\Users\wjjo\Desktop\글도비 && python -m pytest tests/test_blueprint_patch_mode.py tests/test_base_agent.py tests/test_legacy_reentry_reaudit.py -v` | (1) Stage 3 전용 테스트 94건 재실행 → 전수 통과 (2) Stage 2→3 연결 통합 테스트 통과 (3) Stage 3→4 연결 통합 테스트 통과 (4) `schema_incompatible` 에러 재현 테스트 작성 및 통과 (5) Stage 3 상태를 HEALTHY로 갱신 | 2h | 없음 | S1 §8: "Stage 3: PATCHING — 서베이 시점 패칭 진행 중"; S1 §10.1: "Stage 3 서베이 시점 패칭 (Gemini additionalProperties, 4계층 수정)" |
| S1-EX-004 | 테스트 파일 수 불일치 해소 (290 vs 323) | P1 (이번 주) | evidence-manifest(`docs/2026-03-18/OPUS/geuldobi-v2-static-improvement-discovery-evidence-manifest.md`) 기준 290개 vs 실측 323개. 카운팅 기준 차이 원인을 규명하고 정확한 수치를 확정. conftest.py, __init__.py, 헬퍼 파일 등 비테스트 파일 포함 여부, 또는 glob 패턴 차이 가능. 조사 명령: `find tests/ -name "*.py" -type f | wc -l` | (1) 카운팅 기준 차이 원인 문서화 (2) "테스트 파일"의 공식 정의 확립 (예: `test_*.py` 패턴만 vs 전체 tests/ 디렉토리) (3) S1 SSOT 수치를 확정 값으로 갱신 (4) evidence-manifest와 S1 수치 일치 | 1h | 없음 | S1 §10.1: "테스트 파일 수 불일치 (evidence-manifest vs 실측: 290 vs 323 — 카운팅 기준 차이)" |
| S1-EX-005 | 디렉토리 구조 §2 중복 제목 수정 | P2 (다음 주) | S1 SSOT 본문에서 "## 2. 프로젝트 규모"와 "## 2. 디렉토리 구조"가 동일 번호(§2)를 사용. 디렉토리 구조를 §2-bis 또는 §2.5로 재번호 부여 필요. | (1) S1 SSOT 내 섹션 번호 중복 0건 (2) 모든 상호 참조가 올바른 섹션을 가리킴 | 0.25h | 없음 | S1 본문: 15행 "## 2. 프로젝트 규모" vs 29행 "## 2. 디렉토리 구조" 중복 |
| S1-EX-006 | tests/ 파일 수 내부 불일치 해소 (§2 표 vs 디렉토리 구조) | P2 (다음 주) | §2 프로젝트 규모 표에서 tests/ = ~323개로 기재, 디렉토리 구조 섹션에서는 ~316개로 기재. 동일 문서 내 7개 차이. S1-EX-004 결과를 반영하여 단일 확정 수치로 통일. | (1) S1 SSOT 내 tests/ 파일 수 단일 수치로 통일 (2) 해당 수치의 산출 근거(카운팅 기준) 명시 | 0.25h | S1-EX-004 | S1 §2 표: "~323" vs S1 디렉토리 구조: "~316" |

---

## 감리 이력

### 기본 3pass

#### Pass 1: 사실 검증 (Fact Verification)

각 실행 항목의 S1 근거 추적 결과:

| ID | 근거 추적 | 판정 |
|----|-----------|------|
| S1-EX-001 | S1 §10.1 ".gitattributes 부재 → CRLF 경고 8건" + §8 ".editorconfig에 end_of_line 미지정" → 정확히 일치 | PASS |
| S1-EX-002 | S1 §10.1 "CRLF 경고 8건" + §8 "Windows LF/CRLF 혼재 가능" → 정확히 일치 | PASS |
| S1-EX-003 | S1 §8 "Stage 3: PATCHING" + §10.1 "4계층 수정" + "94 passed, 0 failed" → 정확히 일치 | PASS |
| S1-EX-004 | S1 §10.1 "290 vs 323 — 카운팅 기준 차이" → 정확히 일치 | PASS |
| S1-EX-005 | S1 본문 15행/29행 직접 확인 → 정확히 일치 | PASS |
| S1-EX-006 | S1 §2 표 "~323" vs 디렉토리 구조 "~316" → 정확히 일치 (7개 차이 확인) | PASS |

**Pass 1 결론**: 모든 항목이 S1 원문에 직접 추적 가능. 허위 근거 0건.

#### Pass 2: 교차 일관성 (Cross-consistency)

| 검사 항목 | 결과 |
|-----------|------|
| 우선순위 간 모순 | 없음. P0 2건(긴급), P1 2건(이번 주), P2 2건(다음 주) — 순차적 긴급도 |
| 의존성 순환 | 없음. S1-EX-002 → S1-EX-001 (선형), S1-EX-006 → S1-EX-004 (선형) |
| 완료 기준 간 충돌 | 없음. S1-EX-004와 S1-EX-006의 "수치 확정"이 동일 방향 |
| 공수 합산 타당성 | 총 4.5h — S1 범위(아키텍처 개관) 대비 적절 |

**Pass 2 결론**: 내부 모순 0건.

#### Pass 3: 완전성 (Completeness)

S1 §10.1 발견사항 대비 실행 항목 매핑:

| S1 발견사항 | 매핑된 실행 항목 | 상태 |
|-------------|-----------------|------|
| .gitattributes 부재 → CRLF 경고 8건 | S1-EX-001, S1-EX-002 | 커버됨 |
| Stage 3 서베이 시점 패칭 | S1-EX-003 | 커버됨 |
| 테스트 파일 수 불일치 (290 vs 323) | S1-EX-004 | 커버됨 |

S1 본문 내 추가 발견(감리자 자체 발견):

| 추가 발견 | 매핑된 실행 항목 | 상태 |
|-----------|-----------------|------|
| §2 섹션 번호 중복 | S1-EX-005 | 커버됨 |
| tests/ 파일 수 내부 불일치 (323 vs 316) | S1-EX-006 | 커버됨 |

**Pass 3 결론**: S1의 명시적 발견사항 3건 + 감리자 발견 2건, 총 5건 모두 실행 항목에 매핑됨. 누락 0건.

---

### 적대적 5pass

#### Pass 1: 우선순위 도전 (Challenge Priority Assignments)

| ID | 현재 | 도전 | 판정 |
|----|------|------|------|
| S1-EX-001 | P0 | ".gitattributes 부재가 빌드/배포를 차단하는가?" — 직접 차단하지 않으나, CRLF 혼재는 `git diff` 노이즈를 유발하여 모든 후속 코드 변경의 리뷰 품질을 저하시킴. 또한 cross-platform 협업 시 merge conflict 원인. | **P0 유지**. 후속 모든 커밋의 diff 신뢰성에 영향하므로 최우선 해결 타당. |
| S1-EX-002 | P0 | "정규화를 굳이 별도 P0로 분리할 필요 있는가? S1-EX-001에 포함 가능." — 별도 커밋으로 분리하면 정규화 변경만 격리되어 blame 오염 최소화 가능. 그러나 실행 순서상 S1-EX-001 직후이므로 동일 PR에서 처리 가능. | **P0 유지, 단 S1-EX-001과 동일 PR 허용 명시**. 우선순위는 동일하되 실행 단위를 유연화. |
| S1-EX-003 | P1 | "이미 94 테스트 통과했는데 회귀 검증이 P1인가? P2면 안 되는가?" — Stage 3 PATCHING 상태가 서베이 시점 기록이며, 현재 상태가 불확실. HEALTHY 전환을 확인하지 않으면 S6 실행 항목과 충돌 가능. | **P1 유지**. S6 실행문서의 선행 조건이 될 수 있으므로 이번 주 내 확인 필요. |
| S1-EX-004 | P1 | "카운팅 기준 차이일 뿐 실제 버그가 아닌데 P1인가?" — 수치 불일치는 향후 감리 문서 전반의 신뢰도를 저하시킴. 특히 evidence-manifest가 다른 SSOT의 근거로 사용되므로 조기 확정 필요. | **P1 유지**. 감리 체계의 정합성 기반이므로 타당. |
| S1-EX-005 | P2 | "문서 내 섹션 번호 중복이 P2인가? P3(백로그)면 안 되는가?" — 당장 기능에 영향 없으나, 다른 SSOT에서 S1 §2를 참조할 때 혼란 유발. P2(다음 주)가 적절. | **P2 유지**. |
| S1-EX-006 | P2 | "S1-EX-004에 흡수 가능한데 별도 항목인가?" — S1-EX-004는 원인 규명, S1-EX-006은 문서 반영. 논리적으로 분리 타당하나 동시 처리 허용. | **P2 유지, S1-EX-004와 동시 처리 허용 명시**. |

**Pass 1 수정사항**: S1-EX-002에 "S1-EX-001과 동일 PR 허용" 주석 추가. S1-EX-006에 "S1-EX-004와 동시 처리 허용" 주석 추가. 우선순위 변경 0건.

#### Pass 2: 모호/측정 불가 완료 기준 검사 (Vague/Unmeasurable Success Criteria)

| ID | 완료 기준 검사 | 판정 |
|----|----------------|------|
| S1-EX-001 | "CRLF 경고 0건" — 측정 가능 (git diff 실행). "CI hook 통과" — CI가 존재하지 않을 수 있음. | **수정**: "CI 또는 pre-commit hook" → "로컬 `git diff` 실행 시 CRLF 경고 0건 확인 (CI 존재 시 hook 추가)" |
| S1-EX-002 | "`git grep -I -l $'\r'` 결과 0건" — 바이너리 파일 제외 조건 명확. 측정 가능. | PASS |
| S1-EX-003 | "Stage 3 상태를 HEALTHY로 갱신" — 누가, 어디에 갱신하는지 불명확. | **수정**: "S1 SSOT §8 표의 Stage 3 상태를 PATCHING → HEALTHY로 갱신하고 커밋" |
| S1-EX-004 | "공식 정의 확립" — 어디에 기록하는지 불명확. | **수정**: "tests/ 카운팅 기준을 S1 SSOT §2에 각주로 명시" |
| S1-EX-005 | "섹션 번호 중복 0건" — 측정 가능. | PASS |
| S1-EX-006 | "단일 수치로 통일" — 측정 가능. | PASS |

**Pass 2 수정사항**: S1-EX-001, S1-EX-003, S1-EX-004의 완료 기준을 구체화.

#### Pass 3: 누락 의존성 탐색 (Missing Dependencies)

| 관계 | 검사 | 판정 |
|------|------|------|
| S1-EX-003 → S6 실행문서 | Stage 3 HEALTHY 전환은 S6 실행문서의 전제 조건이 될 수 있음. S1-EX-003 완료 후 S6 실행 시작이 안전. | **추가**: S1-EX-003 비고에 "S6 실행문서의 선행 조건" 명시 |
| S1-EX-001 → 전체 후속 커밋 | CRLF 정규화 전에 다른 코드 변경을 커밋하면 diff 오염. | **이미 P0으로 반영됨** — 추가 조치 불필요 |
| S1-EX-004 → S1-EX-006 | 이미 명시됨. | PASS |
| S1-EX-005 → 타 SSOT 참조 | S2-S7에서 "S1 §2" 참조 시 혼란. 섹션 번호 변경 후 타 SSOT 갱신 필요 가능. | **추가**: S1-EX-005 비고에 "S2-S7의 S1 §2 참조 존재 여부 확인 후 갱신" 조건 추가 |

**Pass 3 수정사항**: S1-EX-003에 S6 의존 주석 추가. S1-EX-005에 타 SSOT 참조 확인 조건 추가.

#### Pass 4: 공수 추정 도전 (Challenge Effort Estimates)

| ID | 현재 추정 | 도전 | 판정 |
|----|-----------|------|------|
| S1-EX-001 | 0.5h | ".gitattributes 작성 + .editorconfig 수정 + 테스트" — 파일 확장자 종류가 다양(py, js, html, yaml, json, md, sql, jsonl 등). 전수 확인 시 0.5h 타당. | **0.5h 유지** |
| S1-EX-002 | 0.5h | "`git add --renormalize .`은 1분이면 끝나는데 0.5h?" — 정규화 후 diff 확인, 바이너리 파일 오정규화 여부 검사, 커밋 메시지 작성 포함. 573+ 파일 대상. | **0.5h 유지** — 검증 시간 포함 시 타당 |
| S1-EX-003 | 2h | "94 테스트 재실행은 자동화되어 있을 텐데 2h?" — 단순 재실행 외에 Stage 2→3, 3→4 통합 테스트 확인 + schema_incompatible 재현 테스트 작성이 포함. 재현 테스트 작성이 주 공수. | **2h 유지** — 재현 테스트 신규 작성 포함 시 타당. 단, 재현 테스트가 이미 존재하면 1h로 단축 가능. |
| S1-EX-004 | 1h | "파일 카운팅에 1h?" — glob 패턴 차이 분석, conftest/init 파일 분류 기준 정의, 문서 갱신 포함. | **1h 유지** |
| S1-EX-005 | 0.25h | 단순 번호 변경. | **0.25h 유지** |
| S1-EX-006 | 0.25h | S1-EX-004 결과를 붙여넣기 수준. | **0.25h 유지** |

**Pass 4 수정사항**: S1-EX-003에 "재현 테스트 기존재 시 1h로 단축 가능" 주석 추가. 총 공수 4.5h 유지.

#### Pass 5: 최종 판정 및 수정 반영 (Final Verdict)

**적대적 5pass 종합 결과**:

| 패스 | 수정 건수 | 요약 |
|------|-----------|------|
| Pass 1 (우선순위) | 0건 변경, 2건 주석 추가 | S1-EX-002/006에 동시 처리 허용 주석 |
| Pass 2 (완료 기준) | 3건 구체화 | S1-EX-001/003/004의 기준을 측정 가능하게 수정 |
| Pass 3 (의존성) | 2건 추가 | S1-EX-003 → S6 의존, S1-EX-005 → 타 SSOT 참조 확인 |
| Pass 4 (공수) | 1건 주석 추가 | S1-EX-003 조건부 단축 가능성 명시 |
| Pass 5 (최종) | 아래 최종 실행 항목 표에 반영 | — |

---

## 최종 실행 항목 (감리 수정 반영)

| ID | 항목 | 우선순위 | 상세 내용 | 완료 기준 | 추정 공수 | 의존성 | S1 근거 | 감리 수정 |
|----|------|----------|-----------|-----------|-----------|--------|---------|-----------|
| S1-EX-001 | `.gitattributes` 생성 + `.editorconfig` 수정 | P0 | `.gitattributes` 부재로 CRLF 경고 8건. 주요 확장자(py, js, html, yaml, json, md, sql, jsonl 등)별 `text eol=lf` 정책 명시. `.editorconfig`에 `end_of_line = lf` 추가 (현재 `[*]` 블록 line 5 `insert_final_newline = true` 다음에 삽입). | (1) `.gitattributes` 존재 (2) 로컬 `git diff` 실행 시 CRLF 경고 0건 (3) `.editorconfig`에 `end_of_line = lf` 명시 (4) CI 존재 시 line-ending 검사 hook 추가 | 0.5h | 없음 | §10.1, §8 | Pass 2: 완료 기준 구체화 (CI 조건부) |
| S1-EX-002 | CRLF 혼재 파일 일괄 정규화 | P0 | `git add --renormalize .` + 검증. CRLF 파일 열거: `git diff --check HEAD~1 2>/dev/null | grep "trailing whitespace\|CRLF" | head -20`. S1-EX-001과 동일 PR 허용. | (1) `git grep -I -l $'\r'` 결과 0건 (2) 정규화 커밋 완료 (3) `git diff` CRLF 경고 0건 | 0.5h | S1-EX-001 | §10.1, §8 | Pass 1: 동일 PR 허용 주석 |
| S1-EX-003 | Stage 3 패칭 안정성 회귀 검증 | P1 | 4계층 수정(스키마/에러분류/빠른실패/상태리셋: `modules/core/response_schemas.py`, `modules/domain/agents/base_agent.py`, `modules/domain/agents/blueprint_ensemble.py`, `modules/domain/agents/three_phase_blueprint_generator.py`) 후 회귀 검증. 테스트 실행: `cd C:\Users\wjjo\Desktop\글도비 && python -m pytest tests/test_blueprint_patch_mode.py tests/test_base_agent.py tests/test_legacy_reentry_reaudit.py -v`. `schema_incompatible` 재현 테스트 작성. S6 실행문서의 선행 조건. | (1) Stage 3 전용 테스트 94건 전수 통과 (2) Stage 2→3, 3→4 통합 테스트 통과 (3) `schema_incompatible` 재현 테스트 작성 및 통과 (4) S1 SSOT §8 표 Stage 3 = HEALTHY로 갱신 커밋 | 2h (재현 테스트 기존재 시 1h) | 없음. S6 실행문서의 선행 조건 | §8, §10.1 | Pass 2: 갱신 위치 명시. Pass 3: S6 의존 추가. Pass 4: 조건부 단축 |
| S1-EX-004 | 테스트 파일 수 불일치 원인 규명 | P1 | evidence-manifest(`docs/2026-03-18/OPUS/geuldobi-v2-static-improvement-discovery-evidence-manifest.md`) 290 vs 실측 323. 조사: `find tests/ -name "*.py" -type f | wc -l`. glob 패턴/포함 기준 차이 분석. | (1) 차이 원인 문서화 (2) "테스트 파일" 공식 정의를 S1 SSOT §2에 각주로 명시 (3) 확정 수치로 S1 갱신 (4) evidence-manifest 수치 일치 | 1h | 없음 | §10.1 | Pass 2: 기록 위치 구체화 |
| S1-EX-005 | S1 SSOT §2 중복 섹션 번호 수정 | P2 | "## 2. 프로젝트 규모"와 "## 2. 디렉토리 구조" 중복. 후자를 §3으로 재번호하고 후속 섹션 번호 순차 조정. S2-S7에서 S1 §번호 참조 존재 시 함께 갱신. | (1) S1 SSOT 섹션 번호 중복 0건 (2) S2-S7의 S1 참조 정합성 확인 | 0.25h | 없음. 완료 후 S2-S7 참조 확인 필요 | S1 본문 15행/29행 | Pass 3: 타 SSOT 참조 확인 조건 추가 |
| S1-EX-006 | tests/ 파일 수 내부 불일치 통일 (323 vs 316) | P2 | §2 표(~323) vs 디렉토리 구조(~316) 7개 차이. S1-EX-004 결과를 반영하여 단일 수치로 통일. S1-EX-004와 동시 처리 허용. | (1) S1 SSOT 내 tests/ 수치 단일화 (2) 산출 근거 명시 | 0.25h | S1-EX-004 | §2 표 vs 디렉토리 구조 | Pass 1: 동시 처리 허용 주석 |

**총 추정 공수**: 4.5h (최소 3.5h — S1-EX-003 조건부 단축 시)

---

## 실행 순서 권고

```
Phase 1 (P0, 즉시):
  S1-EX-001 → S1-EX-002 (동일 PR 가능)

Phase 2 (P1, 이번 주):
  S1-EX-003 (독립 실행, S6 실행 전 완료)
  S1-EX-004 (독립 실행)

Phase 3 (P2, 다음 주):
  S1-EX-004 완료 후 → S1-EX-006 (동시 처리 가능)
  S1-EX-005 (독립 실행, 완료 후 타 SSOT 참조 확인)
```

---

*끝 — S1 아키텍처 개관 실행문서*
