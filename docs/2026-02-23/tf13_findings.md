# TF-13 Findings - Prompt Integration Audit

> Baseline: 2,549 passed, 0 violations (commit `91a87ab`)

---

## Current Position

```text
Last Completed Round: Round D
Next Round: -
Status: Completed
```

---

## Progress Table

| Round | Scope | Status | HIGH | MED | LOW | INFO |
|---|---|---|---:|---:|---:|---:|
| A | analyst.yaml (7 prompts) | Completed | 0 | 1 | 1 | 1 |
| B | chief_writer + director (10 prompts) | Completed | 0 | 1 | 1 | 1 |
| C | ensemble + generators (4 prompts) | Completed | 0 | 0 | 0 | 0 |
| D | SafeDict + PromptLoader cross-check | Completed | 0 | 0 | 1 | 1 |

---

## Findings

### Round A
1. [MED] `ANALYST_SELF_CRITIC_PROMPT`의 `{ep_start}`가 실제 주입되지 않은 채 LLM 입력으로 전달됨.
   - Evidence: `config/prompts/analyst.yaml:556`
     - `- ... {ep_start} ...`
   - Evidence: `modules/domain/agents/analyst_prompt_api.py:65`
     - `def get_analyst_self_critic_prompt() -> str:`
     - `    return _load_prompt("ANALYST_SELF_CRITIC_PROMPT", legacy.ANALYST_SELF_CRITIC_PROMPT)`
   - Evidence: `modules/domain/agents/analyst.py:837`
     - `critic_input = (f"{get_analyst_self_critic_prompt()}...")`
   - Why it matters: Self-critic가 시작 화수 기준을 정확히 참조하지 못해 연속성 감지 품질이 떨어질 수 있다.

2. [LOW] `RECOVERY_PROMPT`/`VOLUME_STRATEGY_PROMPT`는 YAML key 누락 시 fallback 본문 없이 빈 문자열을 반환함.
   - Evidence: `modules/domain/agents/analyst_prompt_api.py:71`
     - `prompt = _PROMPT_LOADER.load("analyst", "RECOVERY_PROMPT")`
     - `if prompt is not None: return prompt`
     - `return ""`
   - Evidence: `modules/domain/agents/analyst_prompt_api.py:80`
     - `prompt = _PROMPT_LOADER.load("analyst", "VOLUME_STRATEGY_PROMPT")`
     - `if prompt is not None: return prompt`
     - `return ""`
   - Evidence: `modules/domain/agents/analyst.py:1085`
     - `prompt = template.format(...)`
   - Why it matters: 설정 누락/파싱 실패 시 호출 자체는 계속되지만 실질적으로 비어 있는 프롬프트가 전송된다.

3. [INFO] 5개 프롬프트는 YAML과 `analyst_prompts.py` 양쪽에 중복 유지되고 있음.
   - Evidence: `config/prompts/analyst.yaml:5`
     - `POST_STITCH_REPAIR_PROMPT: |`
   - Evidence: `modules/domain/agents/analyst_prompts.py:7`
     - `POST_STITCH_REPAIR_PROMPT = """`
   - Why it matters: 현재 내용은 strip 기준 동일하지만, 장기적으로 이원 관리에 따른 드리프트 위험이 있다.

### Round B
1. [MED] `MANUSCRIPT_HISTORY_CONFLICT_PROMPT` 로드 실패 시 연속성 검증이 `PASS`로 fail-open 처리됨.
   - Evidence: `modules/domain/agents/director_continuity.py:401`
     - `if not prompt:`
     - `    return {"decision": "PASS", ... "prompt_error": True}`
   - Evidence: `modules/domain/agents/director_continuity.py:736`
     - `if not prompt:`
     - `    return {"decision": "PASS", ... "prompt_error": True}`
   - Why it matters: YAML 키 누락/파싱 실패 상황에서 충돌 검사 자체가 우회되어 모순 원고가 통과할 수 있다.

2. [LOW] Chief Writer 프롬프트 6종은 YAML 누락 시 모두 빈 문자열 fallback이라 품질 저하가 조용히 발생함.
   - Evidence: `modules/domain/agents/chief_writer_prompts.py:12`
     - `_FALLBACK_EMPTY = ""`
   - Evidence: `modules/domain/agents/chief_writer_prompts.py:15`
     - `def _load_prompt(key: str, fallback: str) -> str:`
     - `    loaded = _PROMPT_LOADER.load("chief_writer", key)`
     - `    return loaded if loaded is not None else fallback`
   - Why it matters: 설정 누락 시 즉시 실패하지 않아, 출력 스키마/가이드 섹션이 빈 채로 모델 호출이 진행된다.

3. [INFO] Director 프롬프트는 YAML 실사용 경로와 `director_prompts.py` 하드코딩 템플릿이 공존하는 이원 구조임.
   - Evidence: `modules/domain/agents/director_ensemble.py:342`
     - `prompt = self._prompt_loader.load("director", "ENSEMBLE_SELECTION_PROMPT", ...)`
   - Evidence: `modules/domain/agents/director_prompts.py:10`
     - `ENSEMBLE_SELECTION_PROMPT = """`
   - Why it matters: 현재 로더 경로가 실사용이지만 하드코딩 템플릿이 남아 있어 장기적으로 드리프트 위험이 있다.

### Round C
No findings.

- Verification note: `ensemble.yaml` 2개 프롬프트와 `arc_generator.yaml`/`blueprint_generator.yaml` 패치 프롬프트의 placeholder는 호출부 kwargs와 1:1로 일치함.
- Verification note: `patch_*_with_feedback` 경로에서 `{feedback_text}`/`{original_*}`는 `.format()` 전에 brace escape가 적용됨.

### Round D
1. [LOW] `PromptLoader` 캐시 키가 `domain` 단일 축이라, 런타임에 프롬프트 디렉터리(`PROMPT_DIR`)가 바뀌면 이전 프로젝트 템플릿이 재사용될 수 있다.
   - Evidence: `modules/core/prompt_loader.py:38`
     - `_cache: dict[str, dict[str, str]] = {}`
   - Evidence: `modules/core/prompt_loader.py:58`
     - `env_path = os.getenv("PROMPT_DIR")`
   - Evidence: `modules/core/prompt_loader.py:71`
     - `if domain in self._cache:`
     - `    return self._cache[domain]`
   - Evidence: `modules/core/prompt_loader.py:189`
     - `def invalidate_cache(self, domain: str | None = None) -> None:`
   - Evidence: `modules/core/emotion_tracker.py:41`
     - `self._prompt_loader = PromptLoader() if PromptLoader else None`
   - Evidence: `modules/core/emotion_tracker.py:49`
     - `prompt = self._prompt_loader.load("emotion_tracker", key, n_episodes=n_episodes)`
   - Why it matters: 동일 프로세스에서 프로젝트/프롬프트 경로 전환 시 `invalidate_cache()`가 선행되지 않으면 이전 캐시가 남아 잘못된 템플릿이 주입될 수 있다.

2. [INFO] `SafeDict`는 미주입 변수를 `{name}` 형태로 보존하며, `emotion_tracker.yaml`의 `{n_episodes}`는 호출부에서 정상 주입된다.
   - Evidence: `modules/core/prompt_loader.py:24`
     - `def __missing__(self, k: str) -> str:`
     - `    return "{" + k + "}"`
   - Evidence: `modules/core/prompt_loader.py:170`
     - `return template.format_map(SafeDict(**kwargs))`
   - Evidence: `config/prompts/emotion_tracker.yaml:6`
     - `최근 {n_episodes}화 동안 부정적 감정...`
   - Evidence: `config/prompts/emotion_tracker.yaml:34`
     - `최근 {n_episodes}화 동안 긍정적 감정...`
   - Evidence: `modules/core/emotion_tracker.py:49`
     - `load("emotion_tracker", key, n_episodes=n_episodes)`
   - Why it matters: Round D 범위에서 placeholder 처리 경로는 기능적으로 일치하며, unresolved token이 있어도 그대로 보존되어 런타임 예외로 번지지 않는다.

- Verification note: `modules/core/prompt_builder.py`는 문자열 조립/컨텍스트 생성 유틸 중심이며 `PromptLoader` 직접 import/호출 경로가 없다.

---

## Totals

| Severity | Count |
|---|---:|
| HIGH | 0 |
| MEDIUM | 2 |
| LOW | 3 |
| INFO | 3 |
| **Total** | **8** |
