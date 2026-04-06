# ROL Global Terminal 1 — Bootstrap / Router / Handoff P0-P1 Survey

Date: 2026-04-06
Terminal: 1
Owner: bootstrap, project binding, router, upstream handoff
Baseline Commit: `0d7c077a`
Mode: read-only severity sweep

---

## Verdict: no live P0-P1 found in this lane

---

## 1. 질문별 답변

### Q1. wrong project binding, fallback project, wrong-stage routing이 live P0-P1인가

**아니다.**

Project binding 경로 분석:

- `boot()` (main_a.py:1384) → `_select_project()` → `_bind_selected_project()` → `StudioSystem.boot_v20_project()`
- `_select_project()` (main_a.py:3427): `projects/` 하위 디렉토리를 `sorted()` 순회, 1-based index로 선택. 빈 목록이면 빈 문자열 반환 → `boot()`에서 조기 종료.
- `resolve_project_dir()` (runtime_paths.py:88): path traversal 방어가 있음 — `candidate.relative_to(projects_root)` 검증, 빈 이름 거부, root 자체 선택 거부.
- `_bind_selected_project()` (main_a.py:1272): genre type 미해석 시 warning 로그만 발행하고 계속 진행. 이것은 방어적 경고이며, genre type이 빈 문자열이어도 `boot_v20_project()`는 비무협 모드로 정상 작동한다 (system.py:56).

Wrong-project binding 위험:
- 사용자가 번호 입력으로 프로젝트를 선택하므로 프로그래매틱 fallback으로 잘못된 프로젝트가 바인딩되는 경로는 없다.
- `_get_int_input` default=1이므로 빈 입력 시 첫 번째 프로젝트가 선택된다. 이것은 의도된 동작이며 destructive overwrite 경로가 아니다.

Stage routing 분석:
- `_dispatch_main_process_choice()` (main_a.py:2228): 문자열 기반 분기이며, 잘못된 입력은 `True` 반환하여 메뉴 루프를 계속한다. wrong-stage routing이 canonical artifact를 덮어쓰는 경로는 없다 — 각 stage가 자체 진입 조건을 독립적으로 확인한다.

### Q2. handoff contract가 조용히 비거나 엇갈려도 run이 계속되는 경로가 있나

**narrative router 경로에서는 안전하다. 시스템 런타임 경로에서도 안전하다.**

Narrative Router (`scripts/narrative_router.py` + `modules/narrative_router/router.py`):
- `_determine_stage()` (narrative_router.py:109): 4개 Stage 0 아티팩트가 하나라도 없으면 `stage0` 반환. `manual_audit_pass`가 True가 아니면 `stage0` 반환. 누락 시 잘못된 단계로 넘어가지 않는다.
- `inspect_artifacts()` (router.py:52): `preprocess_ready` 판정에서 `all(preprocess_files_present.values()) and manual_audit_pass is True` 조건을 사용. 하나라도 실패하면 `False`.
- `detect_stage()` (router.py:18): 아티팩트 존재 여부만으로 단계를 판정하므로, contract 내용이 비어 있어도 파일이 존재하면 다음 단계로 넘어갈 수 있다. **그러나** 이것은 P0-P1이 아니다:
  - narrative router는 CLI 유틸리티이며, 이 결과로 canonical artifact를 자동 덮어쓰지 않는다.
  - 실제 pipeline 진행은 operator가 결과를 보고 결정한다.
  - `stage0_handoff_validator.py`가 별도로 schema-level 검증을 수행한다.

Stage 0 Handoff Validator (`scripts/stage0_handoff_validator.py`):
- 4개 아티팩트 각각에 대해 UTF-8 파싱 → schema required fields → type check → file-specific validation을 수행.
- `VALID_PRIMARY_PROFILES` enum으로 profile 값 검증.
- `manual_audit_pass` boolean 타입 검증.
- 검증 실패 시 exit code 1 반환.

시스템 런타임 (`main_a.py` boot chain):
- `boot()` → `_ensure_project_genre_alignment()`: genre 불일치 시 operator에게 확인 요청, 거부 시 종료.
- `_initialize_project_runtime_support()`: agent 초기화 실패 시 `False` 반환 → boot 중단.
- 각 stage 메뉴 진입은 operator의 명시적 선택에 의해서만 가능.

### Q3. entry -> owner -> sink -> consequence를 가장 짧게 적으면

가장 주목할 경로 (P2 이하 수준):

```
narrative_router.detect_stage()
  → phase0_exists/tr_exists/bi_exists (파일 존재만 판정, 내용 무검증)
  → stage 문자열 반환
  → CLI stdout JSON
  → operator 판단
```

이 경로에서 "파일은 존재하지만 내용이 비었거나 손상된" 경우 잘못된 stage를 보고할 수 있지만:
- sink는 CLI stdout이고 canonical artifact가 아니다
- operator가 보고 판단하므로 자동 덮어쓰기 위험이 없다
- stage0_handoff_validator가 별도 content-level 검증을 제공한다

### Q4. 가장 좁은 owner file 1~3개는 무엇인가

이 lane에서 authority를 가장 많이 결정하는 파일:

1. `modules/core/runtime_paths.py` — project binding의 path resolution authority
2. `modules/narrative_router/router.py` — stage detection 및 family resolution의 canonical implementation
3. `modules/core/system.py` (`boot_v20_project`) — project context 생성 및 genre-conditional service initialization

## 2. Static Evidence Sufficiency

이 lane의 결론은 **static evidence만으로 충분하다.** Fresh run은 불필요하다.

근거:
- project binding 경로가 단순하고 방어적이다 (path traversal 방어, 빈 입력 방어, operator 확인 요청)
- router는 CLI 유틸리티로, canonical artifact에 직접 쓰지 않는다
- stage dispatch는 operator의 명시적 선택에 의존하며 자동 진행 경로가 없다
- handoff validator가 content-level 검증을 제공한다

## 3. Watchlist Only (P2 이하)

| Item | Severity | Notes |
| --- | --- | --- |
| `detect_stage()`가 파일 존재만 보고 내용 검증은 안 함 | P3 | CLI 보고 목적이며 canonical sink 아님. validator가 별도 제공 |
| `_select_project()` default=1로 첫 프로젝트 자동 선택 | P3 | Operator가 보는 메뉴이며 destructive가 아님 |
| `_reload_project_environment()`에서 `StudioSystem` 재생성 | P3 | 기존 self.sys를 덮어쓰지만, boot chain에서만 호출되므로 stale reference 위험 낮음 |
| `blockguide.py`/`wuxguide.py` family plugin의 harness path가 실제 파일 존재를 runtime에 검증하지 않음 | P3 | harness path는 LLM에게 읽을 문서를 알려주는 포인터이며, missing file이 canonical artifact 손상으로 이어지지 않음 |

## 4. 3-Pass Audit Record

- Pass 1: 문서 유형이 `terminal survey output`으로 고정됨. scope가 bootstrap/router/handoff에 한정됨. findings first 구조 준수.
- Pass 2: 모든 file path가 실제 워크스페이스에 존재함. 코드 라인 번호가 현재 codebase와 일치함. P0-P1 판정 계약의 기준에 대해 각 경로를 검증함.
- Pass 3: `no live P0-P1 found` 결론이 static evidence로 충분히 뒷받침됨. watchlist 항목이 P0-P1로 승격될 근거 없음.
- Confidence: 0.97

---

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-06 output
