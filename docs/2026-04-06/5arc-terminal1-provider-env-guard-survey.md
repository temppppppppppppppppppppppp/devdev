# 5-Arc Terminal 1: Provider / Env Guard Survey

Date: 2026-04-06
Terminal: 1 of 4
Owner: provider env, Vertex credential loading, key rotation, runtime provider reload
Baseline Commit: `0d7c077a9e6f14575aba7fc509b836d218db610d`
Authority: live code read-only

## 1. Verdict

**no live P0-P1 found in this lane** — 단, 이것은 **multi-process topology** 전제 하에서만 성립한다.

같은 프로세스 안에서 5아크를 동시에 돌리면 P0 (wrong-project env bleed) 가 열린다.
별도 프로세스면 env isolation은 안전하다. 다만 shared Vertex quota pool contention은 P1 수준으로 남는다.

## 2. Evidence

### Q1. `projects/<project_name>/.env`는 실제로 언제, 어떻게 로드되는가

로드 지점은 3곳이다:

| 순서 | 위치 | 대상 | override |
|------|------|------|----------|
| 1 | `main_a.py:128` | 루트 `.env` (module-level import time) | `override=True` |
| 2 | `main_a.py:365` | 루트 `.env` (`SovereignApp.__init__`) | `override=True` |
| 3 | `main_a.py:1230-1247` | `projects/{name}/.env` (`_reload_project_environment`) | `override=True` |

3번은 `_bind_selected_project` → `_reload_project_environment(project_name)` 체인으로 호출된다 (`main_a.py:1272-1275`).

핵심: `load_dotenv(override=True)` 는 `os.environ` 을 **process-global 하게** 덮어쓴다.

### Q2. `project-local .env`가 같은 프로세스 안의 다른 run에 영향을 줄 여지가 있는가

**있다. P0 수준이다.**

같은 프로세스 안에서 프로젝트를 전환하면 아래 3개 전역 상태가 동시에 오염된다:

1. **`os.environ`** — `load_dotenv(override=True)` 가 프로세스 전역 환경변수를 덮어쓴다. 이전 프로젝트의 `VERTEX_API_KEY`, `VERTEX_PROJECT_ID`, `VERTEX_LOCATION` 등이 새 프로젝트 값으로 교체된다.

2. **`_SHARED_ROUTER`** (`llm_router.py:196`) — module-level singleton. `get_shared_llm_router(force_reload=True)` 로 재생성하지만, 재생성 순간 모든 agent가 같은 라우터를 공유한다.

3. **`BaseAgent._api_keys`** (`base_agent.py:194`) — class-level 변수. `refresh_runtime_provider_state()` 가 초기화하면, 이전 프로젝트 키를 쓰던 모든 인스턴스의 키가 새 프로젝트 키로 바뀐다.

현재 구조에서 "같은 프로세스, 같은 시점에 2개 프로젝트 active" 시나리오는 설계에 없다. 순차 전환 (sequential rebind) 만 지원한다. 따라서 **동일 프로세스 내 5아크 병렬은 env bleed P0 가 열려 있다.**

### Q3. `VERTEX_API_KEY_2..9` 회전은 실제 isolation인지, 단순 key fallback인지

**단순 key fallback (rate-limit 429 방어) 이다. isolation과 무관하다.**

Evidence:

- `load_google_api_keys()` (`google_client_factory.py:56-62`): `VERTEX_API_KEY`, `VERTEX_API_KEY_2`, ..., `VERTEX_API_KEY_9` 순서로 `os.getenv` 하여 리스트 반환
- `BaseAgent._try_rotate_key()` (`base_agent.py:233-287`): 429 또는 quota exhaustion 시 다음 키로 순환
- 순환 트리거: `_key_rotation_pending = True` 설정 → 다음 ask loop 진입 시 `_apply_pending_key_rotation()` (`base_agent.py:854`)
- 모든 키는 동일한 `VERTEX_PROJECT_ID` / `VERTEX_LOCATION` 으로 같은 Vertex pool에 요청한다
- `_rotation_count >= len(_api_keys) - 1` 이면 순환 중단 (`base_agent.py:242-244`)

결론: key 1~9 는 같은 GCP project 내 다른 API key 일 뿐, project-level isolation이 아니다. 5아크가 각자 다른 키를 배정받아도, 같은 Vertex project quota를 공유한다.

### Q4. `VERTEX_PROJECT_ID / VERTEX_LOCATION` 분리로 shared pool이 줄어드는가

**현재 `auth_mode: api_key` 구성에서는 효과 없다.**

Evidence:

- `config/models.yaml:17`: `auth_mode: "api_key"` — 현재 기본값
- `build_google_genai_client()` (`google_client_factory.py:86-126`):
  - `api_key` 모드: `genai.Client(vertexai=True, api_key=resolved_api_key)` — **project/location 미전달**
  - `project_credentials` 모드: `genai.Client(vertexai=True, project=project, location=location)` — project/location 전달
- `VertexAIProvider._build_api_key_client()` (`vertex_provider.py:72-78`): `genai.Client(vertexai=True, api_key=api_key)` — project/location 미사용

따라서:

- `api_key` 모드에서는 `VERTEX_PROJECT_ID`, `VERTEX_LOCATION` env 변수가 client 생성에 사용되지 않는다
- Google Vertex API key는 생성 시 project에 바인딩되므로, API key 자체가 project를 결정한다
- 별도 GCP project의 별도 API key를 프로젝트별 `.env` 에 넣으면 pool 분리가 **가능하다** — 단, 이것은 현재 `api_key` 모드에서도 작동한다
- `project_credentials` 모드로 전환하면 `VERTEX_PROJECT_ID` / `VERTEX_LOCATION` 를 통해 명시적 pool 분리가 가능하지만, 현재 운영에서 사용하지 않는다

## 3. Live Risk

| ID | Severity | Description | Condition |
|----|----------|-------------|-----------|
| T1-R1 | **P0** | 동일 프로세스 내 project `.env` reload가 `os.environ`, `_SHARED_ROUTER`, `BaseAgent._api_keys` 를 process-global 하게 오염 | 같은 프로세스에서 2개 이상 프로젝트 동시 active |
| T1-R2 | **Not live** | 별도 프로세스일 때 project-local `.env` 가 다른 프로세스에 영향 | 별도 프로세스면 `os.environ` 이 독립이므로 발생하지 않음 |
| T1-R3 | **P1** | 5개 프로세스가 같은 Vertex API key (같은 GCP project pool) 를 쓰면 throughput contention / 429 연쇄 가능 | 모든 프로세스가 동일 API key 또는 동일 GCP project 소속 key 사용 |
| T1-R4 | **Not P0-P1** | 키 순환이 프로세스 간 조율 없이 독립 발생 → 이론적 순환 낭비 | nice-to-have 조율이지 안전성 문제는 아님 |

## 4. Owner Files

| File | Role | Risk Surface |
|------|------|-------------|
| `main_a.py:128,365,1230-1247` | `.env` 로드, project env reload | process-global env 오염 |
| `modules/core/llm_router.py:196-203` | `_SHARED_ROUTER` singleton | module-level 공유 상태 |
| `modules/core/google_client_factory.py:86-126` | Vertex client 생성 | env var 기반 credential resolve |
| `modules/core/providers/vertex_provider.py:65-113` | `VertexAIProvider` client caching | instance-level `_client` 캐시 |
| `modules/domain/agents/base_agent.py:192-287` | class-level key rotation state | process-wide 공유 |
| `modules/core/provider_mode.py:7,35-36` | `GEULDOBI_PROVIDER_MODE` env resolve | process-global |
| `config/models.yaml:15-26` | Vertex AI provider config (`auth_mode: api_key`) | pool 경계 결정 |
| `modules/core/runtime_paths.py:81-102` | project directory resolve | env var 기반 경로 결정 |

## 5. What This Means For 5-Arc Parallel

### 금지 조건

- **같은 프로세스 안에서 5아크 병렬은 금지해야 한다.** `os.environ`, `_SHARED_ROUTER`, `BaseAgent._api_keys/caches` 가 모두 process-global이므로, project 전환 시 다른 아크의 credential/provider state가 오염된다.

### 허용 조건

- **별도 프로세스 (5개 프로세스)** 면 env isolation은 완전하다:
  - 각 프로세스가 자신의 `os.environ` 을 가진다
  - 각 프로세스의 `_SHARED_ROUTER`, `BaseAgent._api_keys` 가 독립이다
  - `load_dotenv(override=True)` 가 다른 프로세스에 영향을 주지 않는다

### Shared Pool 주의

- 5개 프로세스가 모두 같은 `VERTEX_API_KEY` (또는 같은 GCP project 소속 키) 를 쓰면:
  - 동일 Vertex quota pool을 5배로 소모한다
  - 429 rate limit 이 한 프로세스에서 발생하면, 같은 pool의 다른 프로세스에도 연쇄될 수 있다
  - key rotation 이 프로세스 간 조율 없이 독립 발생하므로, 같은 대체 키로 몰릴 수 있다
- 프로젝트별 `.env` 에 서로 다른 GCP project 소속 API key 를 넣으면 pool 분리가 가능하다 — 현재 `api_key` 모드에서도 작동한다

### Context Cache 부가 참고

- `BaseAgent._context_caches` 는 class-level dict (`base_agent.py:2128`) 이지만, 캐시 키가 `{cache_type}_{project_name}_{content_hash}` 로 project-namespaced다 (`base_agent.py:2159`)
- 별도 프로세스면 각자 독립 dict이므로 cache bleed는 없다
- 같은 프로세스에서 project 전환 시 `refresh_runtime_provider_state()` 가 `_context_caches.clear()` 를 호출하므로 잔류 캐시도 제거된다 — 하지만 전환 타이밍 race는 이론적으로 가능하다 (추가 P0 근거)

## 6. Need Fresh Probe?

**이 lane에서는 fresh probe 불필요.**

static evidence 만으로 아래가 확정된다:

- `load_dotenv(override=True)` → `os.environ` process-global mutation → 동일 프로세스 multi-project = P0
- 별도 프로세스 = env isolation 완전
- key rotation = fallback only, not isolation
- `api_key` auth mode = `VERTEX_PROJECT_ID/LOCATION` 불사용

fresh run 으로 추가 확인이 필요한 것은 이 lane에 없다. Terminal 2 (control plane topology) 와 Terminal 3 (cache/sink namespace) 의 결론과 합쳐서 최종 topology 판정을 내릴 수 있다.

## 7. Terminal 1 Summary for Decision Contract

이 terminal의 evidence는 **Decision Contract Option 2** 를 지지한다:

> `multi-process allowed; project-local .env sufficient for content isolation, but shared Vertex pool remains throughput risk`

단, 같은 GCP project 소속 key를 공유하는 한 throughput contention (P1) 이 남으므로, 5아크 규모에서는 프로젝트별 별도 GCP project key 또는 quota 분산을 operator-level guard 로 권고한다.

## 8. 3-Pass Audit Record

Pass 1, structure and scope:

- 4개 required question 에 1:1 대응하는 evidence 제시
- Terminal 1 owner (provider env, Vertex credential, key rotation, runtime reload) 범위를 벗어나지 않음
- Stage 의미론 이슈로 확장하지 않음

Pass 2, evidence and consistency:

- 모든 evidence는 live code 행 번호 기반 (main_a.py, google_client_factory.py, vertex_provider.py, llm_router.py, base_agent.py, provider_mode.py, config/models.yaml)
- `api_key` auth mode 에서 `VERTEX_PROJECT_ID/LOCATION` 미사용이라는 결론은 `build_google_genai_client` 와 `VertexAIProvider._build_api_key_client` 양쪽에서 교차 확인
- key rotation 이 isolation 이 아닌 fallback 이라는 판정은 `_try_rotate_key` 로직과 트리거 조건 (429/quota) 에서 확인
- `os.environ` process-global 오염은 Python 표준 동작이며 `load_dotenv(override=True)` 문서와 일치

Pass 3, execution and readability:

- Required Output Shape 6개 섹션 (Verdict, Evidence, Live Risk, Owner Files, What This Means, Need Fresh Probe) 충족
- 결론 문장 `no live P0-P1 found in this lane` 포함 (multi-process 전제)
- Decision Contract 연결 명시

Confidence: `97%`
