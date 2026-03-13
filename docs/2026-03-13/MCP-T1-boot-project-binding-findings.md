# [MCP-T1] Boot / Project Binding Findings

> 작성일: 2026-03-13
> 상태: `PASS3 completed`
> 조사 모드: `static / read-only / code-and-test verification`
> 기준 오더: `main_a-control-plane-detail-full-survey-audit-order.md`
> 실행 요약: `PASS1 후보 4건 -> PASS2 제거 2건 -> 최종 2건`

---

## 조사 범위

- `main_a.py`: `boot()`, `_select_genre()`, `_select_project()`, `_load_models_yaml()`, `_get_agent_model_map()`, `_check_vector_db_lock()`
- `modules/core/system.py`
- `modules/core/project_manager.py`
- `modules/core/project_support.py`
- `modules/core/genre_guards/work_guard.py`
- `modules/core/prompt_loader.py`

## 필수 근거

- 읽은 테스트:
  - `tests/test_runtime_paths.py`
  - `tests/test_project_support.py`
  - `tests/test_project_manager_hud_helpers.py`
  - `tests/test_process_runner.py` 중 boot/project root 계약 관련 구간
- 읽은 참조 문서:
  - `docs/2026-03-12/frontend-desktop-bridge-full-survey-3pass-final-audit.md`
  - `docs/2026-03-12/ui-desktop-rerudit-3pass-final.md`
- 실행 검증:
  - `pytest -q tests/test_runtime_paths.py tests/test_project_support.py tests/test_project_manager_hud_helpers.py tests/test_process_runner.py`
  - 결과: `42 passed`
- ad-hoc 재현:
  - 임시 tempdir에서 `project .env -> ProjectContext() -> root .env 재오염` 여부 확인
  - 임시 tempdir에서 `GEULDOBI_PROJECTS_ROOT`와 `ProjectContext.base_path` 정합성 확인

## PASS 기록

- PASS 1:
  - 후보 1: 프로젝트별 `.env`가 boot 중 유지되는가
  - 후보 2: `GEULDOBI_PROJECTS_ROOT` SSOT가 `main_a.py`/`ProjectContext`까지 이어지는가
  - 후보 3: `models.yaml` root fallback이 workspace CWD에서도 직접 성립하는가
  - 후보 4: `_check_vector_db_lock()`가 실제 vector-memory gate와 의미상 일치하는가
- PASS 2:
  - 후보 3 제거: `main_a.py::_load_models_yaml()`의 직접 root fallback은 CWD 의존이지만, 현재 실제 agent model map은 `ConfigManager._load_agents_from_yaml()`의 파일 기준 fallback으로 복구된다.
  - 후보 4 제거: `_check_vector_db_lock()` 명칭은 거칠지만 현재 `VecMemory`가 `project_data.db` shared mode를 쓰므로 즉시 기능 결함으로 올릴 근거는 부족했다.
- PASS 3:
  - 확정 2건만 `MCP-T1-*`로 채택

## Finding Ledger

| ID | Severity | 상태 | 파일/함수 | 요약 |
|----|----------|------|-----------|------|
| MCP-T1-001 | P1 | confirmed | `main_a.py::boot`, `modules/core/project_manager.py::ProjectContext.__init__` | 프로젝트별 `.env`가 boot 중 root `.env`로 다시 덮여 runtime API identity가 분기된다 |
| MCP-T1-002 | P1 | confirmed | `main_a.py::_select_project`, `modules/core/system.py::boot_v20_project`, `modules/core/project_manager.py::ProjectContext.__init__` | control plane이 `GEULDOBI_PROJECTS_ROOT` SSOT를 무시하고 상대 `projects/`를 직접 사용한다 |

## Final Findings

### [MCP-T1-001] P1 - 프로젝트별 `.env`가 `ProjectContext` 초기화 중 root `.env`로 재오염된다

1. ID
   - `MCP-T1-001`
2. Severity
   - `P1`
3. 현상 요약
   - `boot()`는 프로젝트별 `.env`를 먼저 로드해 `StudioSystem`과 `BaseAgent` 멀티키를 재초기화한다.
   - 하지만 직후 `boot_v20_project()`가 `ProjectContext(project_name)`를 만들고, `ProjectContext.__init__`가 경로 없는 `load_dotenv(override=True)`를 다시 호출한다.
   - 그 결과 boot 중간부터 환경변수가 root `.env` 값으로 되돌아가고, 이후 생성되는 `VecMemory` 같은 env-read 의존 객체는 프로젝트 키가 아니라 root 키를 잡는다.
4. 코드 근거
   - `main_a.py:960` `load_dotenv(project_env_path, override=True)`
   - `main_a.py:965` `self.sys = StudioSystem(api_client=genai.Client(api_key=new_api_key))`
   - `main_a.py:975` `self.sys.boot_v20_project(project_name, genre=_genre_type)`
   - `modules/core/project_manager.py:50` `load_dotenv(override=True)`
   - `main_a.py:1067` `self.memory = VecMemory(api_key=os.getenv("GOOGLE_API_KEY", ""), ...)`
   - ad-hoc tempdir 재현에서 `project-key`를 로드한 뒤 `ProjectContext("demo")`를 호출하자 `GOOGLE_API_KEY`가 root `.env` 값으로 바뀌는 것을 확인했다.
5. downstream 영향 경계
   - boot 초반 `StudioSystem.api_client`와 `BaseAgent._init_api_keys()`는 프로젝트 키를 볼 수 있다.
   - boot 후반 `VecMemory` 및 이후 env를 직접 읽는 helper/service는 root 키를 보게 된다.
   - 즉, 한 세션 내부에서 provider identity와 credential boundary가 둘로 갈라질 수 있다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_runtime_paths.py`, `tests/test_project_support.py`, `tests/test_project_manager_hud_helpers.py`, `tests/test_process_runner.py`를 실행했고 모두 통과했다.
   - 그러나 프로젝트 `.env`가 `ProjectContext` 생성 이후에도 유지되는지 검증하는 테스트는 현재 없다.
7. 기존 문서와의 중복 여부
   - duplicate status: `none`
   - 기존 desktop/backend 문서는 env-driven root resolution 존재 여부를 다뤘지만, project-local secret reload가 boot 중 다시 root `.env`에 덮이는 문제는 다루지 않았다.
8. 권장 후속 조치
   - `ProjectContext.__init__`의 무경로 `load_dotenv(override=True)`를 제거하거나, 최소한 project-local env를 덮지 않도록 분리한다.
   - boot 시점에 확정된 credential map을 명시적으로 주입하고, 이후 runtime object는 `os.getenv()`를 다시 읽지 않게 묶는다.
   - 회귀 테스트를 추가한다: `project .env -> boot_v20_project -> VecMemory/api_client key` 일관성 검증.

### [MCP-T1-002] P1 - `main_a.py` control plane이 `GEULDOBI_PROJECTS_ROOT` SSOT를 우회해 잘못된 프로젝트 트리를 열 수 있다

1. ID
   - `MCP-T1-002`
2. Severity
   - `P1`
3. 현상 요약
   - runtime path SSOT는 `resolve_projects_root()`가 `GEULDOBI_PROJECTS_ROOT`를 우선하고 없을 때만 workspace fallback을 쓰도록 잠겨 있다.
   - 그런데 boot control plane은 이 SSOT를 거치지 않고 상대 `projects/`를 직접 사용한다.
   - `_select_project()`는 `Path(self._PROJECTS_DIR)`를 그대로 열고, `StudioSystem.boot_v20_project()`는 `ProjectContext(project_name)`를 기본 인자 그대로 생성해 `projects/{name}`를 붙인다.
   - 따라서 `bridge_server`/`process_runner`가 env 기반 root를 쓰는 환경에서, `main_a.py`만 다른 프로젝트 트리를 선택할 수 있다.
4. 코드 근거
   - `main_a.py:235` `_PROJECTS_DIR = "projects"`
   - `main_a.py:3022` `def _select_project(self) -> str:`
   - `main_a.py:3034` `projects = sorted(d.name for d in root.iterdir() if d.is_dir())`
   - `modules/core/system.py:37` `self.project = ProjectContext(project_name)`
   - `modules/core/project_manager.py:53` `self.base_path = Path(root_dir) / self.name`
   - `modules/core/runtime_paths.py:23-27`은 `GEULDOBI_PROJECTS_ROOT` 우선 규약을 제공한다.
   - `modules/api/process_runner.py:78`, `tests/test_runtime_paths.py:4`, `tests/test_runtime_paths.py:12`는 그 env-root 계약이 실제 SSOT임을 뒷받침한다.
   - ad-hoc tempdir 재현에서 `GEULDOBI_PROJECTS_ROOT=external-projects`를 줬을 때 `resolve_projects_root()`는 `external-projects`를 반환했지만, `ProjectContext("demo")`는 여전히 `projects/demo`를 사용했다.
5. downstream 영향 경계
   - 잘못된 프로젝트 목록 표시
   - 잘못된 `.env`, `author_directives`, `work_guard.yaml`, `project_data.db` 바인딩
   - bridge/process runner가 계산한 project root와 `main_a.py`가 실제로 연 프로젝트가 달라지는 control-plane drift
   - 현재 packaged desktop happy path가 안전한 이유는 launcher가 `cwd`와 env를 우연히 같은 workspace로 맞춰 주기 때문이지, `main_a.py` 자체가 SSOT를 지키기 때문이 아니다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_runtime_paths.py`는 env-root 해석 자체를 검증한다.
   - 하지만 `main_a.py::_select_project()`와 `ProjectContext`가 같은 helper를 사용하도록 묶는 테스트는 없다.
7. 기존 문서와의 중복 여부
   - duplicate status: `related-but-new-control-plane-surface`
   - `docs/2026-03-12/ui-desktop-rerudit-3pass-final.md`는 packaged backend가 `GEULDOBI_WORKSPACE / GEULDOBI_PROJECTS_ROOT` 기준 root를 정상 해석한다고 닫았다.
   - 이번 항목은 packaged backend read path가 아니라, `main_a.py` boot control plane이 같은 SSOT를 아예 호출하지 않는다는 신규 표면이다.
8. 권장 후속 조치
   - `main_a.py`의 `_PROJECTS_DIR` 상수를 제거하고 `runtime_paths.resolve_projects_root()` 결과를 단일 SSOT로 주입한다.
   - `StudioSystem.boot_v20_project()`와 `ProjectContext`에 `project_root`를 명시 인자로 넘긴다.
   - 회귀 테스트를 추가한다: non-workspace CWD + explicit `GEULDOBI_PROJECTS_ROOT`에서 `_select_project()`와 `ProjectContext.paths.root`가 동일 root를 쓰는지 검증.

## Rejected Candidates

| 후보 | PASS2 판정 | 근거 |
|------|------------|------|
| `_load_models_yaml()`의 root fallback이 `Path("config/models.yaml")`라 workspace CWD에서 빈 dict가 된다 | removed | 직접 fallback은 약하지만, 실제 agent model map은 `modules/core/config_manager.py:88-91`의 파일 기준 로더가 복구한다. 현재 코드 기준 즉시 오동작 증거는 부족했다. |
| `_check_vector_db_lock()`가 vector lock을 실제로 보지 않는다 | removed | `modules/core/vec_memory.py:79-85` 기준 현재 production boot는 `project_data.db` shared mode를 사용한다. 이름은 거칠지만, 이 함수만으로 boot invariant 파손을 확정할 근거는 부족했다. |

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| 프로젝트별 `.env` boot 유지성 | 테스트 공백 | `SovereignApp.boot()`를 temp project `.env`와 root `.env`로 기동해 `StudioSystem`, `VecMemory`, BaseAgent key map이 같은 credential을 쓰는지 검증 |
| env-root와 boot control plane 정합성 | 테스트 공백 | explicit `GEULDOBI_PROJECTS_ROOT` + non-workspace CWD + sample project tree에서 `_select_project()`와 `ProjectContext.paths.root`를 함께 검증 |
| packaged desktop happy path 의존성 | 간접 근거만 존재 | launcher가 `cwd == workspace`를 깨도 `main_a.py`가 동일하게 동작하는지 별도 smoke 필요 |

## 마감 체크

- 코드 근거 포함
- downstream 영향 경계 포함
- 현재 테스트 근거 또는 테스트 부재 포함
- 기존 문서와의 중복 여부 포함
- `PASS1 -> PASS2 -> PASS3` 요약 포함
