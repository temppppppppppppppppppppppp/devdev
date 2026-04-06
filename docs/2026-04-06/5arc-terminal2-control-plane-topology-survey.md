# 5-Arc Terminal 2 — Control Plane Topology Survey

Date: 2026-04-06
Status: 3-pass audited
Terminal: 2 — control plane, process runner, run concurrency, process topology
Baseline Commit: `0d7c077a9e6f14575aba7fc509b836d218db610d`
Authority: live code read, static evidence only

---

## Verdict

**no live P0-P1 found in this lane**

Current control plane은 구조적으로 **single active run per bridge_server process**다. 5아크 병렬은 반드시 **5개 독립 프로세스**(bridge_server 5개 또는 main_a.py 직접 5개)를 요구한다. 같은 프로세스 안에서 다중 project bind는 아키텍처상 불가능하며, 시도할 수 있는 코드 경로 자체가 없다.

---

## Q1. Current control plane이 본질적으로 `single active run per runner`인가

**Yes — 하드 제약이다.**

Evidence chain:

1. `bridge_server.py:2293` — lifespan에서 `runner = ProcessRunner()` 인스턴스를 **정확히 1개** 생성하고 `app.state.runner`에 바인딩
2. `ProcessRunner.start()` (`process_runner.py:333-334`) — `if self._state != "idle": raise RuntimeError(f"Cannot start: state={self._state}")` — idle이 아니면 기동 자체를 거부
3. `run_validator.py:91-93` — `runner_state in ACTIVE_RUN_STATES` 이면 HTTP 409 `RUN_ALREADY_ACTIVE` 반환
4. `ACTIVE_RUN_STATES = frozenset({"starting", "running", "stopping"})` — 세 상태 모두 차단

결론: 한 bridge_server 프로세스 안에서 두 번째 run을 기동할 수 있는 코드 경로가 없다. 이것은 버그가 아니라 의도된 설계다.

---

## Q2. `5아크 병렬`을 하려면 `5프로세스`가 사실상 필수인가

**Yes — 필수다.**

구조적 근거:

- bridge_server 경로: 1 bridge_server = 1 ProcessRunner = 1 main_a.py subprocess → 5아크 = 5 bridge_server 프로세스 (각각 다른 포트)
- 직접 실행 경로: main_a.py를 직접 5번 실행 → 5개 독립 Python 프로세스

어느 경로든 **프로세스 경계가 곧 run 경계**다. 현재 코드에는 runner pool, run queue, worker thread 등 단일 프로세스 안에서 복수 run을 관리하는 구조가 전혀 없다.

---

## Q3. Process boundary 기준으로 env와 project root가 어떻게 분리되는가

### 3-1. bridge_server → main_a.py subprocess 경로

`ProcessRunner._build_env()` (`process_runner.py:811-867`):

1. `os.environ.copy()` — 부모 프로세스 env를 **복사**
2. `PYTHONIOENCODING=utf-8`, `PYTHONUNBUFFERED=1` 고정
3. `GEULDOBI_RUN_ID` 주입
4. `GEULDOBI_PROVIDER_MODE` 설정 (ambient/vertex/gemini-direct 중 하나)
5. provider_mode에 따라 불필요한 키 제거 또는 passthrough

이 env dict는 `asyncio.create_subprocess_exec(..., env=env)` (`process_runner.py:362-369`)에 전달되어 **자식 프로세스의 독립 환경**이 된다.

→ 5개 subprocess가 각각 다른 env dict를 받으므로 **프로세스 간 env 오염 없음**.

### 3-2. main_a.py 내부 project root 분리

`_bind_selected_project()` (`main_a.py:1272-1284`):

1. `_reload_project_environment(project_name)` → `projects/<name>/.env`를 `load_dotenv(override=True)`
2. `sys.boot_v20_project(project_name, ...)` → `ProjectContext(project_name)` 생성
3. `ProjectContext.__init__()` (`project_manager.py:48-85`) → `resolve_project_dir(project_name)` → `projects/<name>/` 경로에 DB/logs/config/drafts 바인딩

`load_dotenv(override=True)`는 **현재 프로세스의 `os.environ`을 직접 변경**한다. 그러나:

- 각 main_a.py는 독립 프로세스이므로 다른 main_a.py에 영향 없음
- 같은 main_a.py 프로세스 안에서 project를 **교체하면** 이전 project의 env가 잔존할 수 있지만, boot flow가 `_select_genre → _select_project → _bind → run → exit` 단선이므로 실제로 runtime 중 project 교체가 일어나지 않음

→ **프로세스 1개 = 프로젝트 1개** 불변식이 현재 boot flow에서 유지됨.

### 3-3. workspace root 분리

`resolve_workspace_root()` (`runtime_paths.py:74-78`):

- `GEULDOBI_WORKSPACE` 환경 변수 → 명시 지정 시 해당 경로
- 미지정 시 `GEULDOBI_ENGINE_ROOT` 또는 코드 위치 기반 기본값

`resolve_projects_root()` (`runtime_paths.py:81-85`):

- `GEULDOBI_PROJECTS_ROOT` 환경 변수 → 명시 지정 시 해당 경로
- 미지정 시 `workspace/projects/`

→ 5개 프로세스가 같은 workspace를 가리키더라도, 각 프로세스가 서로 다른 project_name을 선택하면 DB/log/artifact 경로가 `projects/<name>/` 단위로 갈린다.

---

## Q4. 같은 프로세스 안 다중 project bind가 운영상 안전한가, 아니면 금지해야 하는가

**해당 코드 경로가 존재하지 않으므로 금지/허용 판정 대상이 아니다.**

현재 아키텍처에서 "같은 프로세스 안에서 두 번째 project를 bind"하려면:

1. bridge_server 경로: 두 번째 `/run`을 호출 → `RUN_ALREADY_ACTIVE` 409 → **차단됨**
2. main_a.py 직접 경로: `boot()` → `_select_project()` → `_bind_selected_project()` → `_run_main_process()` → 종료. 루프 구조가 아니므로 **재bind 경로 없음**

만약 미래에 multi-project 지원을 넣는다면 `load_dotenv(override=True)`의 프로세스-전역 env 변경이 P0 위험이 되지만, 현재는 해당 경로가 닫혀 있다.

---

## Live Risk

| # | Risk | Severity | Status |
|---|------|----------|--------|
| 1 | 같은 프로세스에서 두 번째 run 기동 | — | **아키텍처상 차단됨** (RunValidator + ProcessRunner state guard) |
| 2 | 5개 독립 프로세스가 같은 Vertex pool을 공유 | throughput contention (Terminal 1/4 소관) | **이 terminal 소관 아님** |
| 3 | load_dotenv(override=True)가 프로세스 전역 env를 변경 | 단일 프로세스/단일 프로젝트 불변식이 유지되는 한 safe | **현재 safe** |
| 4 | 5개 프로세스가 같은 workspace의 다른 project를 동시에 쓸 때 file-level 충돌 | DB는 project별 SQLite이므로 격리됨; 공유 config(models.yaml 등)는 read-only | **현재 safe** |

---

## Evidence

| File | Line | What |
|------|------|------|
| `modules/api/bridge_server.py` | 2293 | `runner = ProcessRunner()` — 단일 인스턴스 |
| `modules/api/process_runner.py` | 333-334 | `if self._state != "idle": raise RuntimeError` — 재진입 차단 |
| `modules/api/run_validator.py` | 91-93 | `RUN_ALREADY_ACTIVE` HTTP 409 반환 |
| `modules/api/process_runner.py` | 811-867 | `_build_env()` — os.environ.copy() 기반 독립 env 생성 |
| `modules/api/process_runner.py` | 362-369 | `create_subprocess_exec(..., env=env)` — subprocess에 독립 env 전달 |
| `main_a.py` | 1230-1247 | `_reload_project_environment()` — load_dotenv(override=True) |
| `main_a.py` | 1272-1284 | `_bind_selected_project()` — 단일 project bind |
| `main_a.py` | 1384-1405 | `boot()` — 단선 실행 flow (genre → project → bind → run → end) |
| `modules/core/project_manager.py` | 48-57 | `ProjectContext.__init__()` — project별 경로/DB 격리 |
| `modules/core/runtime_paths.py` | 67-103 | 환경 변수 기반 경로 해석 |

---

## Owner Files

- `modules/api/bridge_server.py`
- `modules/api/process_runner.py`
- `modules/api/run_validator.py`
- `modules/core/runtime_paths.py`
- `modules/core/system.py`
- `modules/core/project_manager.py`
- `main_a.py`

---

## What This Means For 5-Arc Parallel

1. **5아크 병렬 = 5 독립 프로세스**: 현재 아키텍처는 single-run-per-process가 하드 제약이므로, 5아크를 동시에 돌리려면 반드시 5개 프로세스를 띄워야 한다.

2. **프로세스 간 content isolation은 안전하다**: 각 프로세스가 자체 env dict, 자체 ProjectContext, 자체 SQLite DB를 가진다. `projects/<name>/` 경로가 project_name으로 갈리므로 cross-project write 경로가 없다.

3. **공유 지점은 두 가지**:
   - **Vertex API pool**: 5 프로세스가 같은 Vertex project/location + 같은 API key를 쓸 경우 RPM/TPM quota 경합 → Terminal 1/4 소관
   - **workspace-level read-only config**: `config/models.yaml`, `config/prompts/` 등은 공유하지만 read-only이므로 충돌 없음

4. **운영 topology 추천**: bridge_server 5개(각각 다른 포트) 또는 main_a.py 직접 5개. 둘 다 프로세스 격리 기준으로 동일하게 안전하다.

---

## Need Fresh Probe?

**No** — 이 lane의 판정은 live code 구조에서 확정적이다.

- single-run-per-process는 코드에 하드코딩된 제약이므로 fresh run으로 바뀌지 않는다
- env/project root 분리도 boot flow 구조에서 결정되므로 runtime evidence가 추가로 필요하지 않다
- Vertex pool 경합은 이 terminal 소관이 아니며 Terminal 1/4에서 다룬다

---

## 3-Pass Audit Record

Pass 1 — structure and scope:

- 4개 필수 질문 모두에 대해 live code evidence를 직접 인용하여 답변했다
- Terminal 2 소관(control plane/process topology)으로 범위를 한정하고, provider/env(T1)과 cache/sink(T3)은 참조만 했다

Pass 2 — evidence and consistency:

- ProcessRunner의 state guard, RunValidator의 409 반환, bridge_server의 단일 runner 인스턴스 — 3중 방벽이 일관되게 single-run을 강제함을 확인
- load_dotenv(override=True)의 프로세스 전역 side effect가 multi-project 시나리오에서 위험하지만, 현재 boot flow에서 해당 경로가 닫혀 있음을 확인
- runtime_paths.py의 환경 변수 기반 경로 해석이 subprocess env 전달과 정합하는지 확인

Pass 3 — execution and readability:

- 결론이 "5프로세스 필수, 프로세스 간 content isolation은 safe" 한 문장으로 수렴하는지 확인
- Live Risk 테이블에서 모든 항목이 현재 safe이거나 다른 terminal 소관임을 명시

Confidence: `98%`
