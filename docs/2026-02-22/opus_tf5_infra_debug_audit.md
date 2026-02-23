# Opus TF-5: Infra Debug Audit (TF-D)

> 감사일: 2026-02-22
> 범위: `modules/core/db_manager.py`, `modules/core/vec_memory.py`, `modules/core/prompt_loader.py`, `modules/core/context_advisor.py`, 호출 계약 추적 파일 `modules/domain/agents/base_agent.py`, `modules/domain/agents/arc_ensemble.py`, `modules/domain/agents/blueprint_ensemble.py`
> 방법: 수동 라인 단위 검토 (Read/cat), 호출자→피호출자 추적

## Executive Summary

| 위험도 | 건수 |
|--------|------|
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 1 |
| LOW | 0 |

### [D-1] ArcEnsemble 캐시가 토큰 절감 없이 중복 컨텍스트를 재전송함 — HIGH
- **위치**: `modules/domain/agents/arc_ensemble.py:128`, `modules/domain/agents/arc_ensemble.py:373`, `modules/domain/agents/arc_ensemble.py:382`, `modules/domain/agents/arc_ensemble.py:401`, `modules/domain/agents/base_agent.py:1263`, `modules/domain/agents/base_agent.py:1274`
- **코드 인용**:
```python
shared_context = f"{prev_arc_context or ''}\n\n{constraint_block or ''}"
cache_info = self._get_or_create_context_cache(..., content=shared_context, ...)
...
prompt = self._prompt_loader.load(
    ...,
    constraint_block=self._escape_braces(constraint_block or "(없음)"),
    prev_arc_context=self._escape_braces(prev_arc_context or "시작점"),
)
...
result = self._ask_with_cached_context(cache_name=cache_name, prompt=prompt, ...)
```
```python
wrapped_prompt = (
    f"### [AUTHOR'S ABSOLUTE DIRECTIVES]\n{directives}\n\n"
    f"### [TASK]\n{prompt}\n\n"
)
...
"cached_content": cache_name,
```
- **현상**: 캐시로 올린 `shared_context`를 전략 프롬프트(`prompt`)에서 다시 그대로 포함해 전송한다. `cached_content` + 중복 본문 동시 전송 구조라 비용 절감이 사실상 무효화된다.
- **재현 시나리오**: ArcEnsemble 생성 시 `prev_arc_context`/`constraint_block`이 큰 에피소드(중후반)에서 캐시가 생성되어도 요청 payload에 동일 내용이 다시 포함된다.
- **영향**: Tier4-11 목표(앙상블 입력 토큰 절감)가 달성되지 않고, 경우에 따라 캐시 API 호출 비용/복잡도만 증가한다.
- **수정 제안**:
```python
# cache_name 경로에서는 shared context를 프롬프트에서 제외
strategy_prompt = self._prompt_loader.load(..., constraint_block="", prev_arc_context="", ...)
# 또는 전략 전용 템플릿 분리
```

### [D-2] BlueprintEnsemble도 동일하게 캐시 본문을 중복 전송함 — HIGH
- **위치**: `modules/domain/agents/blueprint_ensemble.py:171`, `modules/domain/agents/blueprint_ensemble.py:361`, `modules/domain/agents/blueprint_ensemble.py:367`, `modules/domain/agents/blueprint_ensemble.py:381`, `modules/domain/agents/base_agent.py:1263`, `modules/domain/agents/base_agent.py:1274`
- **코드 인용**:
```python
shared_context = f"{arc_focus or ''}\n\n{constraints_str or ''}\n\n{prev_info or ''}\n\n{hud_context or ''}"
cache_info = self._get_or_create_context_cache(..., content=shared_context, ...)
```
```python
prompt = self._prompt_loader.load(
    ...,
    arc_focus=self._escape_braces(arc_focus),
    constraints=self._escape_braces(constraints_str),
    prev_info=self._escape_braces(prev_info),
    hud_context=self._escape_braces(hud_context),
)
...
response = self._ask_with_cached_context(cache_name=cache_name, prompt=prompt, ...)
```
- **현상**: Blueprint 앙상블도 캐시에 넣은 대형 공통 컨텍스트를 전략 프롬프트에 중복 주입한다.
- **재현 시나리오**: Stage3 BlueprintEnsemble 호출 시 `arc_focus/prev_info/hud_context`가 큰 경우에도 동일 본문이 캐시 + 프롬프트 양쪽으로 전송된다.
- **영향**: Tier4-11의 Blueprint 토큰 절감 목표가 깨지고, 캐시가 성능/비용 최적화가 아니라 부하 증가 요소가 된다.
- **수정 제안**:
```python
# chief_writer 패턴과 동일하게 cache 경로는 전략 지시문만 전송
strategy_prompt = f"{strategy_directive}\n{output_format}"
full_prompt_fallback = 기존 전체 프롬프트
```

### [D-3] ContextAdvisor 스테이지 플래그가 fail-open(키 누락 시 활성) — MEDIUM
- **위치**: `modules/core/context_advisor.py:277`, `modules/core/context_advisor.py:660`
- **코드 인용**:
```python
if not self.enabled or not self._is_stage_enabled(stage):
    return RetrievalPlan(...)
...
def _is_stage_enabled(self, stage: str) -> bool:
    key = self._STAGE_ENABLED_KEYS.get(stage)
    return bool(_threshold(key, True)) if key else True
```
- **현상**: 스테이지 키가 누락/오타인 배포 설정에서 `_threshold(..., True)` 기본값 때문에 해당 stage가 자동 활성화된다.
- **재현 시나리오**: 운영 YAML에서 `smart_retrieval.stage3_enabled` 같은 키가 빠진 상태에서 `smart_retrieval.enabled=true`만 켜면 stage별 차단 의도와 다르게 실행된다.
- **영향**: 피처 플래그 안전성(의도치 않은 활성화 방지) 저하, 토큰 비용 및 동작 변동 리스크 증가.
- **수정 제안**:
```python
return bool(_threshold(key, False)) if key else False
```

## 비고
- `db_manager.get_manuscripts_range()`와 `vec_memory.retrieve_npc_context()`는 lock 경로/escape 경로가 구현되어 있어 본 TF 범위에서 thread-safety 크래시 이슈는 미발견.
- `PromptLoader.load()`의 `format_map(SafeDict(...))` 경로와 key-miss `None` 반환 자체는 설계 의도(호출측 fallback)와 일치함.
