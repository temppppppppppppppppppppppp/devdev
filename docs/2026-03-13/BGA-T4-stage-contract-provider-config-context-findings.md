# [BGA-T4] Stage Contract / Provider / Config / Context Findings

> 작성일: 2026-03-13
> 상태: `PASS3 completed`
> 조사 모드: `static / read-only / code-and-test verification / source-report cross-check / artifact-proof cross-check / UTF-8 only`
> 기준 오더: `backend-global-full-survey-master-audit-order.md`
> 실행 요약: `PASS1 후보 5건 -> PASS2 제거 2건 -> PASS3 확정 3건`

---

## 조사 범위

- `main_a.py`
  - `_load_models_yaml()`
  - `_get_agent_model_map()`
  - Stage 4 style guide / reference excerpt entry
- `modules/core/constants.py`
- `modules/core/llm_generate.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage0/style_extractor.py`
- `modules/domain/agents/base_agent.py`
- `modules/domain/agents/chief_writer_context.py`
- `config/models.yaml`
- `config/system.yaml`

## 필수 근거

- 읽은 테스트:
  - `tests/test_llm_router.py`
  - `tests/test_config_manager.py`
  - `tests/test_stage0_fixes.py`
  - `tests/test_stage01_fixes.py`
  - `tests/test_work_guard.py`
  - `tests/test_style_guard.py`
  - `tests/test_stage4_orchestrator.py`
  - `tests/test_stage4_interview_round.py`
- 읽은 참조 문서:
  - `docs/2026-03-13/stage0-full-survey-consolidated-findings.md`
  - `docs/2026-03-13/stage2-detail-deep-dive-consolidated-findings.md`
  - `docs/2026-03-13/XC-LLM-consolidated-findings.md`
  - `docs/2026-03-12/backend-health-full-survey-3pass-audit.md`
- 실행 검증:
  - `pytest -q tests/test_llm_router.py tests/test_config_manager.py`
  - 결과: `35 passed in 2.14s`
  - `pytest -q tests/test_stage0_fixes.py tests/test_stage01_fixes.py tests/test_work_guard.py tests/test_style_guard.py`
  - 결과: `78 passed in 2.33s`
- 정적 교차 검증:
  - `main_a._load_models_yaml()`와 `AIModels`, `base_agent._load_model_config()`의 models.yaml 경로 / lifetime 비교
  - `generate_content_via_router()`와 `BaseAgent._generate_content()` 반환 타입 및 downstream `.text` 접근 비교
  - Stage 0 `reference_excerpt` 생성 상한과 Stage 4 chief writer prompt 주입 경로 비교

## PASS 기록

- PASS 1:
  - 후보 1: 모델 설정 SSOT가 project-local / root / import-time loader 사이에서 갈라져 있는가
  - 후보 2: provider abstraction이 여전히 Gemini raw response 모양에 종속돼 있는가
  - 후보 3: Stage 0 `reference_excerpt`가 Stage 4 prompt budget 밖에서 무가드 주입되는가
  - 후보 4: Stage 0 `_call_llm()`이 여전히 모델명을 하드코딩하는가
  - 후보 5: WorkGuard / StyleGuard chain이 stage contract에 실제로 연결되지 않는가
- PASS 2:
  - 후보 4 제거: Stage 0 `_call_llm()` 경로는 현재 `AIModels` / fallback constants를 참조하고, 하드코딩 모델명 잔존 근거는 현재 코드에서 확보되지 않았다.
  - 후보 5 제거: `main_a.py` boot 경로는 `work_guard.yaml`이 있으면 `WorkGuard`를 실제로 감싼다. `tests/test_work_guard.py`, `tests/test_style_guard.py`도 wrapper chain을 green으로 잠근다.
- PASS 3:
  - 확정 3건만 `BGA-T4-*`로 채택

## Finding Ledger

| ID | Severity | 상태 | 파일/함수 | 요약 |
|----|----------|------|-----------|------|
| `BGA-T4-001` | `P2` | confirmed | `main_a.py`, `modules/core/constants.py`, `modules/domain/agents/base_agent.py`, `config/models.yaml` | 모델 설정 SSOT가 project-local loader / root loader / import-time constant로 3갈래다 |
| `BGA-T4-002` | `P2` | confirmed | `modules/core/llm_generate.py`, `modules/domain/agents/base_agent.py` | provider abstraction이 여전히 `response.raw`를 반환해 caller를 Gemini shape에 묶는다 |
| `BGA-T4-003` | `P2` | confirmed | `style_extractor.py`, `stage4_orchestrator.py`, `chief_writer_context.py` | Stage 0 `reference_excerpt`가 Stage 4 chief writer prompt에 무예산으로 직접 주입된다 |

## Final Findings

### [BGA-T4-001] P2 - 모델 설정 SSOT가 project-local loader / root loader / import-time constant로 3갈래다

1. ID
   - `BGA-T4-001`
2. Severity
   - `P2`
3. 현상 요약
   - `main_a.py`는 현재 프로젝트의 `config/models.yaml`을 우선 읽고, 없으면 repo root `config/models.yaml`로 폴백한다.
   - 반면 `AIModels` 상수는 module import 시점에 root `config/models.yaml`을 읽어 고정되고, `BaseAgent._load_model_config()`도 root 파일만 본다.
   - 따라서 같은 실행 안에서도 어떤 경로는 project-local config를 따르고, 어떤 경로는 root config 또는 import-time snapshot을 따른다.
   - 이 구조는 stage/provider/config continuity를 "단일 models SSOT"로 보지 못하게 만들고, 프로젝트별 모델 override가 일부 surface에만 적용되는 drift를 만든다.
4. 코드 근거
   - `main_a.py:1172-1198`의 `_load_models_yaml()` / `_get_agent_model_map()`는 `current_project.paths.config / "models.yaml"`을 root보다 우선한다.
   - `modules/core/constants.py:266-299`의 `AIModels`는 root `config/models.yaml`에서 import-time에 값을 읽어 상수로 고정한다.
   - `modules/domain/agents/base_agent.py:80-97`의 `_resolve_models_config_path()` / `_load_model_config()`는 root `config/models.yaml`만 읽는다.
   - 같은 파일에서도 `main_a.py:1251`, `main_a.py:1276`은 project-local loader 결과를 쓰지만, `main_a.py:1564-1569`, `main_a.py:1590-1626`은 `AIModels.*` 상수를 직접 사용한다.
5. downstream 영향 경계
   - stage2/stage3/stage4 agent model selection
   - project별 provider / model override
   - cost / quality / provider rollout 시 operator 기대치
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_config_manager.py:1-16`은 validation settings loader 검증에 집중하고 `models.yaml` convergence는 다루지 않는다.
   - `tests/test_stage0_fixes.py:38-48`은 Stage 0 `_call_llm()`이 `AIModels`를 참조하는지만 본다.
   - `tests/test_bootstrap_status.py:25`는 `_get_agent_model_map`을 stub으로 대체한다.
   - 현재 회귀망에는 `project-local models.yaml`과 `AIModels` / `BaseAgent` / `main_a`가 동일 값을 보는지 검증하는 테스트가 없다.
7. 기존 문서와의 중복 여부
   - `cross-track-confirmed`
   - `XC-LLM-010`, `XC-LLM-011`, `XC-LLM-012`의 설정 scope/lifetime drift를 T4 contract 관점에서 한 finding으로 재구성했다.
8. 권장 후속 조치
   - model config loader를 단일 API로 통합하고, project-local override 허용 여부를 명시해야 한다.
   - `AIModels` import-time snapshot과 runtime loader를 분리 유지할지 폐기할지 결정해야 한다.
   - 회귀 테스트를 추가해야 한다: `project-local models.yaml` 존재 시 `main_a`, `AIModels`, `BaseAgent`가 같은 결과를 보는지 검증.

### [BGA-T4-002] P2 - provider abstraction이 여전히 `response.raw`를 반환해 caller를 Gemini shape에 묶는다

1. ID
   - `BGA-T4-002`
2. Severity
   - `P2`
3. 현상 요약
   - provider/router 계층은 `LLMResponse`를 만들지만, 두 핵심 helper `generate_content_via_router()`와 `BaseAgent._generate_content()`는 다시 `response.raw`만 반환한다.
   - 그 결과 stage/helper/callback 호출자는 provider-정규화된 `LLMResponse.text`가 아니라 native raw object의 `.text` shape에 의존하게 된다.
   - 현재 기본 provider가 Gemini라 문제를 감추지만, Anthropic/OpenAI/Vertex opt-in이 켜지면 helper contract와 caller parsing contract가 즉시 갈라질 수 있다.
4. 코드 근거
   - `modules/core/llm_generate.py:9-21`은 provider.generate() 결과에서 `return response.raw`를 한다.
   - `modules/domain/agents/base_agent.py:334-345`도 동일하게 `response.raw`를 반환한다.
   - downstream caller는 `main_a.py:1564-1569`, `main_a.py:2593-2598`, `modules/validation/advisory_validator.py:145`, `modules/core/adversarial_self_play.py:159` 등에서 `.text`를 기대한다.
5. downstream 영향 경계
   - Stage 0 summary/style extraction helper
   - Stage 2/3/4 advisory / analysis helper
   - provider rollout과 멀티-provider 준비도
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_llm_router.py:57-72`는 provider layer에서 `response.raw is raw`를 검증한다.
   - 그러나 `generate_content_via_router()` 또는 `BaseAgent._generate_content()`가 non-Gemini provider에서도 caller에게 같은 contract를 보장하는지 검증하는 테스트는 없다.
   - 현재 회귀망은 provider object 자체는 검증하지만 helper-level 반환 타입 SSOT는 잠그지 않는다.
7. 기존 문서와의 중복 여부
   - `cross-track-confirmed`
   - `XC-LLM-005`, `XC-LLM-008`의 raw-return pattern을 T4 provider contract risk로 재확인했다.
8. 권장 후속 조치
   - helper 반환값을 `response.raw`가 아니라 `LLMResponse`로 통일해야 한다.
   - caller는 `.text`, `.finish_reason`, `.usage` 같은 normalized field만 사용하도록 정리해야 한다.
   - 회귀 테스트를 추가해야 한다: helper 반환값이 provider 종류와 무관하게 `.text`를 보장하는지 검증.

### [BGA-T4-003] P2 - Stage 0 `reference_excerpt`가 Stage 4 chief writer prompt에 무예산으로 직접 주입된다

1. ID
   - `BGA-T4-003`
2. Severity
   - `P2`
3. 현상 요약
   - Stage 0 `StyleExtractor`는 chief writer 직접 주입용 `reference_excerpt`를 최대 50,000자까지 만든다.
   - Stage 4 session 준비는 이 excerpt를 그대로 `reference_excerpt`로 싣고, `ChiefWriterContext`는 이를 prompt 본문에 그대로 붙인다.
   - 이 경로에는 Stage 4 context budget이나 prompt budget에 맞춘 별도 downstream truncation이 없다.
   - 따라서 style excerpt가 길어질수록 work-focus / mandatory context / prior manuscript 영역과 경쟁하며 prompt composition budget을 조용히 잠식한다.
4. 코드 근거
   - `modules/core/stage0/style_extractor.py:576-626`은 `reference_excerpt`를 최대 `50_000`자로 구성한다.
   - `modules/core/stage4_orchestrator.py:1492-1513`은 저장된 style guide에서 `reference_excerpt`를 읽어 오고, `modules/core/stage4_orchestrator.py:1556-1565`에서 이를 `_SessionConfig.reference_excerpt`로 넘긴다.
   - `modules/domain/agents/chief_writer_context.py:472-501`은 `reference_excerpt`를 chief writer main prompt에 그대로 삽입한다.
5. downstream 영향 경계
   - Stage 4 chief writer prompt budget
   - Stage 0 style guide -> Stage 4 writing continuity
   - work-focus / mandatory_context / prior manuscript 간 상대 우선순위
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_stage0_fixes.py:128-145`은 Stage 0 concept flow에서 `style_guide is None`인 경우만 본다.
   - `tests/test_stage4_orchestrator.py:473-493`, `tests/test_stage4_orchestrator.py:641-645`는 empty 또는 짧은 `style_guide`를 사용하는 경로만 다룬다.
   - 현재 회귀망에는 큰 `reference_excerpt`가 Stage 4 prompt budget을 어떻게 잠식하는지 검증하는 테스트가 없다.
7. 기존 문서와의 중복 여부
   - `cross-track-confirmed`
   - `SZ0-T4-001`의 excerpt budget 우려를 T4 cross-stage context contract로 재확인했다.
8. 권장 후속 조치
   - Stage 4 진입 전에 `reference_excerpt` 전용 truncation / budget policy를 명시해야 한다.
   - style guide, reference excerpt, work-focus, mandatory context 간 우선순위를 같은 budget SSOT로 잠가야 한다.
   - 회귀 테스트를 추가해야 한다: large `reference_excerpt`에서도 chief writer prompt 필수 섹션이 유지되는지 검증.

## Rejected Candidates

| 후보 | PASS2 판정 | 근거 |
|------|------------|------|
| Stage 0 `_call_llm()`가 여전히 모델명을 하드코딩한다 | removed | `tests/test_stage0_fixes.py:38-48`이 `AIModels` / fallback constant 참조를 고정하고, 이번 정적 재검토에서도 하드코딩 문자열 잔존을 재확인하지 못했다. |
| WorkGuard / StyleGuard chain이 stage contract에 실제 연결되지 않는다 | removed | `main_a.py:1138-1145`는 `work_guard.yaml` 존재 시 `WorkGuard`를 실제로 적용한다. `tests/test_work_guard.py`와 `tests/test_style_guard.py`도 wrapper chain을 green으로 잠근다. |

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| project-local `models.yaml` convergence | 테스트 공백 | `main_a`, `AIModels`, `BaseAgent`가 동일 config source를 보는지 검증 |
| helper-level provider compatibility | 테스트 공백 | `generate_content_via_router()` / `BaseAgent._generate_content()`의 non-Gemini helper contract 테스트 |
| large `reference_excerpt` downstream budget | 테스트 공백 | style excerpt 대형 입력 시 chief writer prompt budget 분배 검증 |

## 마감 체크

- 코드 근거 포함
- downstream 영향 경계 포함
- 현재 테스트 근거 또는 테스트 부재 포함
- 기존 문서와의 중복 여부 포함
- `PASS1 -> PASS2 -> PASS3` 요약 포함
