# 5-Arc Parallel Vertex Pool Guard Bounded Survey Order

Date: 2026-04-06
Status: operator-ready after 3-pass self-audit
Mode: system-track, read-only bounded survey
Scope: 5-arc parallel run topology, project-local env isolation, shared Vertex pool risk only
Baseline Commit: `0d7c077a9e6f14575aba7fc509b836d218db610d`
Baseline Dirty Summary: active Stage2/Stage4 execution edits, queue docs, material/work-guard docs, and unrelated narrative artifacts are already present; this survey must not mutate code, `docs/temp/`, or existing dirty files

## 1. Objective

이번 오더의 목적은 하나다.

- `fresh run` 직전, `5아크 병렬 운영`을 어떤 topology로 가져가야 가장 안전한지 bounded하게 판정한다.

이번 조사에서 꼭 답해야 하는 질문은 아래다.

1. `shared Vertex pool`의 실제 의미가 무엇인가
2. `project-local .env`가 현재 런타임에서 실제로 안전한 분리 수단인가
3. `한 프로세스 안에서 여러 작품`을 동시에 돌려도 되는가
4. `작품 섞임` 위험과 `hang/latency contention` 위험 중 무엇이 실제 핵심인가
5. `5아크 병렬`의 최소 안전 운영안이 무엇인가

이번 오더는 아래를 하지 않는다.

- Stage2/Stage3/Stage4 의미론 버그 재조사
- execution queue 변경
- 코드 수정
- fresh run 실행
- closure 선언

즉, 이건 `parallel-run operating guard survey`다.
결론은 `안전 topology recommendation`으로 수렴해야 한다.

## 2. Fixed Rules

- 이 오더는 시스템 오더다.
- `AGENTS.md`와 `docs/implementation/system-order-init-harness.md`를 먼저 따른다.
- live code가 1차 authority다.
- dated docs는 contradiction check 또는 prior evidence로만 쓴다.
- `docs/temp/` 수정 금지.
- 코드/설정/DB/산출물 수정 금지.
- 기존 dirty file 수정 금지.
- 조사 산출물은 `docs/2026-04-06/` 아래 assigned output 문서만 허용한다.
- 불확실하면 억지 결론 대신 `fresh probe required`로 남긴다.

## 3. Severity Contract

### `P0`

아래 중 하나면 `P0`다.

- wrong-project write, wrong-project DB/log sink, cross-project artifact overwrite가 live path에 열려 있다
- project-local env reload 때문에 다른 작품이 잘못된 credential/runtime state를 쓰게 되는 live path가 있다
- context cache 또는 sink namespace가 잘못돼 작품 A의 truth가 작품 B run에 섞일 수 있다

### `P1`

아래 중 하나면 `P1`이다.

- 작품 truth가 섞이진 않지만, current topology에서는 hang/latency contention 때문에 5아크 병렬이 실질적으로 운영 불가능하다
- project-local env, key rotation, provider reload가 current topology에서 partial만 먹어서 operator가 잘못된 isolation을 기대하게 만든다
- 같은 Vertex project/location을 공유하는 구조가 fresh run 전 명시적 guard 없이 과도한 blocking risk를 만든다

### `Not P0-P1`

아래면 올리지 마라.

- 단순 개선 아이디어
- nice-to-have throughput tuning
- 장기적으로는 좋지만 현재 5아크 병렬 안전성과 직접 연결되지 않는 구조 청소

## 4. Required Output Shape

각 terminal output 문서는 반드시 아래 6개 섹션을 가진다.

1. `Verdict`
2. `Evidence`
3. `Live Risk`
4. `Owner Files`
5. `What This Means For 5-Arc Parallel`
6. `Need Fresh Probe?`

결론 문장은 아래 둘 중 하나를 반드시 포함한다.

- `no live P0-P1 found in this lane`
- `live P0/P1 found in this lane`

## 5. Common Read List

모든 terminal 공통 read order:

1. `AGENTS.md`
2. `docs/implementation/system-order-init-harness.md`
3. `docs/2026-04-06/stage4-stage2-fresh-run-preflight-watchlist.md`
4. `docs/2026-04-03/0_0-stage34-ep2-focused-bounded-canary-r4-audit.md`
5. `docs/2026-04-03/0_0-stage34-ep2-focused-bounded-canary-r5-audit.md`
6. `docs/poc/executive_summary.md`
7. `config/models.yaml`

주의:

- 이번 조사의 중심은 `5아크 병렬 운영 safety`다.
- Stage 의미론 문제를 새로 발굴하는 wave로 확대하지 마라.
- 기존 Stage queue 문서들은 context only다. queue를 건드리지 마라.

## 6. Terminal Ownership

### Terminal 1

Owner:

- provider env
- Vertex credential loading
- key rotation
- runtime provider reload

Focus files:

- `main_a.py`
- `modules/core/google_client_factory.py`
- `modules/core/providers/vertex_provider.py`
- `modules/core/llm_router.py`
- `config/models.yaml`

Required questions:

1. `projects/<project_name>/.env`는 실제로 언제, 어떻게 로드되는가
2. `project-local .env`가 같은 프로세스 안의 다른 run에 영향을 줄 여지가 있는가
3. `VERTEX_API_KEY_2..9` 회전은 현재 구조에서 실제 isolation인지, 아니면 단순 key fallback인지
4. `VERTEX_PROJECT_ID / VERTEX_LOCATION`까지 분리해야 shared pool이 줄어드는지 static evidence로 어디까지 말할 수 있는가

Output:

- `docs/2026-04-06/5arc-terminal1-provider-env-guard-survey.md`

### Terminal 2

Owner:

- control plane
- process runner
- run concurrency
- process topology

Focus files:

- `modules/api/bridge_server.py`
- `modules/api/process_runner.py`
- `modules/core/runtime_paths.py`
- `modules/core/system.py`
- `modules/core/project_manager.py`

Required questions:

1. current control plane이 본질적으로 `single active run per runner`인지
2. `5아크 병렬`을 하려면 `5프로세스`가 사실상 필수인지
3. process boundary 기준으로 env와 project root가 어떻게 분리되는지
4. 같은 프로세스 안 다중 project bind가 운영상 안전한지, 아니면 금지해야 하는지

Output:

- `docs/2026-04-06/5arc-terminal2-control-plane-topology-survey.md`

### Terminal 3

Owner:

- context caching
- project namespace
- DB/log/artifact sink separation

Focus files:

- `modules/domain/agents/base_agent.py`
- `modules/core/project_manager.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/stage4_outcome_runtime.py`
- `modules/api/prompt_broker.py`

Required questions:

1. context cache key가 `work_id/project_name` 기준으로 충분히 분리되는가
2. DB/log/artifact path가 project root별로 안전하게 갈리는가
3. `작품 섞임`이 실제로 provider 문제가 아니라 app-level namespace 문제인지 분리 가능한가
4. current cache/sink model에서 live `wrong-project bleed` 가능성이 있는가

Output:

- `docs/2026-04-06/5arc-terminal3-cache-sink-isolation-survey.md`

### Terminal 4

Owner:

- prior evidence synthesis
- hang/latency interpretation
- operator recommendation

Focus files:

- `docs/2026-04-03/0_0-stage34-ep2-focused-bounded-canary-r4-audit.md`
- `docs/2026-04-03/0_0-stage34-ep2-focused-bounded-canary-r5-audit.md`
- `docs/poc/executive_summary.md`
- `docs/2026-04-06/stage4-stage2-fresh-run-preflight-watchlist.md`
- `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage4-repair-contract-normalization-remediation-execution-ssot.md`

Required questions:

1. current evidence가 말하는 핵심 리스크는 `content bleed`인가, `shared pool hang/latency contention`인가
2. static evidence만으로 `same root is acceptable but same pool is risky`라는 결론이 충분한가
3. fresh run 전에 꼭 필요한 operator guard는 무엇인가
4. 5아크 병렬에 대한 최종 추천안을 `금지 / 허용 / 조건부 허용` 중 어디로 두는가

Output:

- `docs/2026-04-06/5arc-terminal4-evidence-ops-synthesis-survey.md`

## 7. Final Decision Contract

모든 terminal이 문서를 제출하면, operator는 아래 4개 중 하나로만 최종 정리한다.

1. `same-process 5-arc parallel forbidden; multi-process per project required`
2. `multi-process allowed; project-local .env sufficient for content isolation, but shared Vertex pool remains throughput risk`
3. `multi-process allowed only with per-project Vertex project/location split`
4. `fresh probe required before any 5-arc launch`

이번 wave에서 목표는 새 queue를 만드는 게 아니라, 위 4개 중 하나를 고르는 데 필요한 static evidence를 모으는 것이다.

## 8. Hard Exclusions

이번 조사에서 아래를 새 finding으로 크게 키우지 마라.

- Stage2 persistence truth
- Stage4 numeric carryover
- Stage4 repair readback
- Stage3 future-wave debt
- material-side work-guard semantics

이 항목들은 이미 각자 active lane 또는 별도 track에 있다.
이번 문서는 오직 `5아크 병렬 운영 가드`만 다룬다.

## 9. Operator Notes

- 현재 코드 기준으로 `project-local .env` 지원 흔적은 있다.
- 현재 코드 기준으로 `context cache`는 project namespace를 탄다.
- 현재 코드 기준으로 control plane은 `RUN_ALREADY_ACTIVE` 흔적이 있다.
- 따라서 이번 bounded survey의 초점은 `단일 프로세스로 5아크를 안전하게 운영할 수 있는가`와 `분리된 env가 실제 격리를 충분히 보장하는가` 두 축이어야 한다.

이 문장은 힌트일 뿐이며, terminal은 반드시 live code로 다시 확인해야 한다.

## 10. 3-Pass Audit Record

Pass 1. Structure and scope:

- 전역 재조사로 퍼지지 않도록 `5아크 병렬 운영 가드`로만 범위를 고정했다
- Stage 의미론 lane과 운영 topology lane을 명시적으로 분리했다

Pass 2. Evidence and consistency:

- 현재 대화에서 확인된 live anchors인 `project-local .env`, `context cache namespace`, `RUN_ALREADY_ACTIVE`, `shared Vertex delay evidence`를 공통 읽기와 질문에 반영했다
- 기존 active Stage queue를 다시 흔들지 않도록 exclusion을 명시했다

Pass 3. Execution and readability:

- terminal별 owner를 `provider/env`, `control plane`, `cache/sinks`, `evidence/ops synthesis`로 나눠 병렬성이 생기게 했다
- 최종 산출물이 recommendation 문장 하나로 수렴되도록 decision contract를 단일화했다

Confidence: `97%`
