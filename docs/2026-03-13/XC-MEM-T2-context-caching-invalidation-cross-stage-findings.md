# XC-MEM-T2: Context Caching 무효화 크로스 스테이지 — 상세 분석

> 날짜: 2026-03-13
> Track: XC-MEM / Target: T2
> 대상: `modules/domain/agents/base_agent.py`, `main_a.py`, `modules/domain/agents/director.py`, `modules/domain/agents/chief_writer.py`

---

## 1. 분석 범위

5개 에이전트(chief_writer, arc_ensemble, blueprint_ensemble, director_ensemble, director_continuity)가 사용하는 Gemini Context Caching이 롤백/리셋/와이프 시 올바르게 무효화되는지 검사한다.

---

## 2. 캐시 아키텍처 이해

### 2.1 두 레벨의 캐시

**레벨 1: Gemini API Context Cache (`BaseAgent._context_caches`)**
```python
# base_agent.py:1765-1766
_context_caches = {}  # {cache_key: {"name": str, "created_at": float, "content_hash": str}}
_cache_lock = threading.Lock()
```
- 클래스 변수 — 모든 BaseAgent 인스턴스가 공유
- Gemini API 서버에 캐싱된 컨텍스트의 name을 보관
- TTL 기본 1800초(30분)
- 현재 `.clear()` 호출 위치: **API key rotation 시에만** (`base_agent.py:242`)

**레벨 2: 개별 에이전트 인메모리 캐시**
- `ChiefWriter._manuscript_cache` / `_cache_ep_num` → `invalidate_manuscript_cache()` (L1808)
- `Director._caching.manuscript_cache_name` / `_continuity._cached_manuscript_ep` → `invalidate_caches()` (L105)
- `StateExtractor._state_cache` → `invalidate_cache()` (L263)

### 2.2 롤백 시 캐시 무효화 코드

```python
# main_a.py:3288-3314 (_rollback_episode)
if success:
    self.state_tracker = None
    self._prompt_builder.invalidate_timeline_cache()
    self._cumulative_state_cache = None
    self._cumulative_state_cache_key = None
    self._narrative_summaries_cache = None
    try:
        _writer = self.agents.get("writer")
        if _writer and hasattr(_writer, "invalidate_manuscript_cache"):
            _writer.invalidate_manuscript_cache()          # Level 2 only
    ...
    try:
        _director = self.agents.get("director")
        if _director and hasattr(_director, "invalidate_caches"):
            _director.invalidate_caches()                  # Level 2 only
```

**`BaseAgent._context_caches.clear()`는 호출되지 않는다.**

동일 패턴이 `_reset_stage_2()` (L3226), `_rewind_stage_2()` (L3256), `_wipe_production_data()` (L3328)에서도 반복된다.

### 2.3 `_context_caches.clear()` 호출 위치 전수조사

| 위치 | 트리거 |
|------|--------|
| `base_agent.py:242` | API key rotation 시 (quota 소진 등) |
| `main_a.py:1048` | API 키 강제 리셋 UI 메뉴 실행 시 |

**롤백/리셋/와이프 4개 파괴적 연산에서는 한 곳도 호출하지 않는다.**

---

## 3. 영향 분석

### 3.1 Stale 캐시 생존 시나리오

1. 사용자가 Episode 50까지 생산
2. Episode 50의 Stage 4 실행 중 `chief_writer` 에이전트가 Gemini Context Cache 생성 (TTL 30분)
3. 사용자가 Episode 45로 롤백 (`_rollback_episode()`)
4. `ChiefWriter.invalidate_manuscript_cache()` 호출 → Level 2 인메모리 캐시 클리어
5. **그러나** `BaseAgent._context_caches`에는 Episode 50 기준 캐시 name이 남아 있음
6. 30분 TTL 내에 Episode 46 생산 시작하면, `_get_or_create_context_cache()`에서 content_hash가 다르므로 새 캐시 생성

### 3.2 실질적 위험도 평가

`_context_caches`의 캐시 키는 `{cache_type}_{project_name}_{content_hash}`로 구성된다. 롤백 후 재실행 시:
- 컨텍스트 내용(blueprint, 이전 원고 등)이 변경되므로 `content_hash`가 달라짐
- 따라서 기존 캐시가 HIT되지 않고 새 캐시가 생성됨

**결론: content_hash 기반 캐시 키 설계로 인해, 롤백 후 stale 캐시가 실제로 HIT될 확률은 매우 낮다.** 단, 아래의 edge case가 존재한다:

- 동일 에피소드 재실행 (롤백 직후 같은 에피소드 즉시 재생산): 이전과 동일한 컨텍스트가 전달되면 캐시 HIT 가능. 이 경우 캐시된 컨텍스트는 "이전 에피소드들의 원고"를 포함하는데, 롤백으로 해당 에피소드들이 DB에서 삭제되었으므로 orphaned 캐시가 된다. 그러나 Gemini API 서버에서의 cached_content는 프롬프트 텍스트일 뿐이므로, LLM 응답 품질에만 영향을 미치고 데이터 오염은 아니다.

---

## 4. Finding

### [XC-MEM-T2-001] P2 | 롤백/리셋/와이프 시 BaseAgent._context_caches 미무효화

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T2-001 |
| Severity | P2 |
| 현상 요약 | 4개 파괴적 연산(rollback_episode, reset_stage_2, rewind_stage_2, wipe_production_data) 후 `BaseAgent._context_caches`가 무효화되지 않아, TTL(30분) 내 동일 content_hash 재진입 시 stale Gemini 캐시 HIT 가능 |
| 코드 근거 | `main_a.py:3288-3314` — `_rollback_episode()` 성공 후 Level 2 캐시만 무효화. `BaseAgent._context_caches.clear()` 호출 없음. 동일 패턴: L3226(`_reset_stage_2`), L3256(`_rewind_stage_2`), L3328(`_wipe_production_data`) |
| 영향 경계 | 5개 Context Caching 에이전트(chief_writer, arc_ensemble, blueprint_ensemble, director_ensemble, director_continuity). content_hash 기반 키 설계로 실제 HIT 확률은 낮으나 0은 아님 |
| 테스트 근거 | `tests/test_main_a_rollback.py`는 Level 2 캐시 무효화만 검증. `BaseAgent._context_caches` 상태 검증 없음 |
| 기존 중복 여부 | `MRL-T2-cache-anchor-history-lifecycle-findings.md`에서 "unified cache/history restore entrypoint 미검증" 지적 있으나, Gemini API Context Cache 레벨의 구체적 누락은 미지적 |
| 권장 후속 조치 | 4개 파괴적 연산 성공 후 `BaseAgent._context_caches.clear()` 1줄 추가 (0.5h). 또는 `ProjectService._restore_runtime_state()`에 추가하여 일괄 처리 |

### [XC-MEM-T2-002] P3 | arc_ensemble/blueprint_ensemble에 대한 개별 캐시 무효화 미호출

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T2-002 |
| Severity | P3 |
| 현상 요약 | 롤백 시 `writer.invalidate_manuscript_cache()`와 `director.invalidate_caches()`는 호출하지만, `arc_ensemble`과 `blueprint_ensemble`에 대한 개별 캐시 무효화 호출 없음 |
| 코드 근거 | `main_a.py:3226-3246`(`_reset_stage_2`)에서 `state_extractor`, `writer`, `director` 3개만 무효화. `arc_ensemble`, `blueprint_ensemble`은 언급 없음 |
| 영향 경계 | Stage 2 리셋/리와인드 후 Stage 2 재실행 시 arc/blueprint 에이전트의 인메모리 상태가 stale일 수 있음 |
| 테스트 근거 | arc_ensemble/blueprint_ensemble 캐시 무효화 테스트 없음 |
| 기존 중복 여부 | 기존 finding에 동일 지적 없음 |
| 권장 후속 조치 | `arc_ensemble`과 `blueprint_ensemble`이 BaseAgent의 Level 2 인메모리 캐시를 사용하는지 확인 후, 사용한다면 무효화 추가 (1h) |

### [XC-MEM-T2-003] P3 | _context_caches TTL 만료가 유일한 자동 정리 메커니즘

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T2-003 |
| Severity | P3 |
| 현상 요약 | `_context_caches`의 자동 정리는 (1) TTL 만료 시 다음 접근에서 삭제 (2) 최대 50개 초과 시 LRU 퇴출뿐. 명시적 무효화 API가 없음 |
| 코드 근거 | `base_agent.py:1804-1810` — TTL 만료 시 `.pop()`. L1842-1846 — 50개 초과 시 LRU. 명시적 `invalidate_context_cache()` 메서드 없음 |
| 영향 경계 | Gemini API 서버 캐시 자원 낭비 (비용 영향 미미) |
| 테스트 근거 | Context Cache TTL/LRU 테스트 없음 |
| 기존 중복 여부 | 기존 finding에 동일 지적 없음 |
| 권장 후속 조치 | `BaseAgent.invalidate_all_context_caches()` 클래스 메서드 추가 후 파괴적 연산에서 호출 (1h) |

---

## 5. 종합 판정

T2 영역에서 **가장 주목할 finding은 XC-MEM-T2-001**이다. content_hash 기반 키 설계가 자연적 방어막 역할을 하지만, 동일 에피소드 재실행 시 stale 캐시 HIT 가능성이 이론적으로 존재한다. 수정 공수는 0.5h로 매우 낮으므로 방어적 개선 권장.
