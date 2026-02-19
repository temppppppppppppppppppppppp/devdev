# Codex 오더: Gemini 컨텍스트 최대 활용 수정 (20건)

> 이 문서는 Codex에게 전달하는 **구현 지시서**입니다.
> 코드를 수정하되, 테스트를 깨뜨리지 마세요.

---

## 배경

Gemini 200K 컨텍스트를 20~60%만 활용 중. 핵심 원인:
- 벡터 메모리 요약이 제목 수준 (100자)
- 200K 절삭이 오래된 화 보존 / 최신 화 절삭 방향
- `use_summary`, `history_check_max_episodes` 등 구현된 설정이 미연결
- 12K/25K/50K 하드코딩 상한이 Gemini 능력 대비 과소

---

## 수정 원칙

1. **외부화**: 새 상한은 `_threshold("context.xxx", default)` 패턴 사용 (`modules/validation/threshold_helper.py`)
2. **기존 동작 보존**: default 값은 기존보다 크거나 같게 (regression 방지)
3. **`smart_truncate`는 `constants.py`에 1회 정의**, 4곳에서 import
4. **테스트**: 기존 2100 passed + 68 xfailed 전량 통과 유지
5. **Phase 순서 준수**: Phase 1 → 2 → 3 → 4 (의존성 있음)

---

## Phase 1: 비활성 경로 복구 + 즉시 수정 (6건)

### 1-1. `use_summary` 파라미터 동작 복구

**파일**: `modules/domain/agents/director_continuity.py`
**위치**: `check_manuscript_history_conflicts()` 메서드 내부, ~L371-378

현재 코드 (버그):
```python
# 전문 사용 (Gemini 컨텍스트 윈도우가 크므로 전문 전달)
h_text = h.get("text", "") or h.get("summary", "")
```

수정 (use_summary 분기 추가):
```python
if use_summary:
    h_text = h.get("summary", "") or h.get("text", "")[:500]
else:
    h_text = h.get("text", "") or h.get("summary", "")
```

### 1-2. `history_check_max_episodes` 설정 연결

**파일 2개**:

(A) `modules/domain/agents/director.py` ~L57:
```python
# 변경 전
self.history_check_max_episodes = 10
# 변경 후 (기존 동작 30화 유지)
self.history_check_max_episodes = 30
```

(B) `modules/domain/agents/director_continuity.py` ~L369:
```python
# 변경 전
recent_history = manuscript_history[-30:]
# 변경 후
recent_history = manuscript_history[-self._d.history_check_max_episodes:]
```

### 1-3. 캐시 경로 `story_context` 주입

**파일**: `modules/domain/agents/director_continuity.py`
**위치**: `check_manuscript_continuity_with_cache()` 메서드 내부, ~L710-721

현재 코드 (버그):
```python
story_context="(캐시 경로 — 설정 정보 미전달)",
```

수정:
- 이 메서드의 시그니처에 `story_context: str = ""` 파라미터가 있는지 확인
- 없으면 추가
- 프롬프트 조립에서 실제 `story_context` 값을 전달
- **주의**: 캐시 content(원고 역사)에는 story_context를 넣지 않음 (캐시 키에 영향 주면 안 됨). 프롬프트 부분에만 삽입.

찾아야 할 것: 이 메서드를 호출하는 곳 (`stage4_interview_round.py` ~L426)에서 story_context를 전달하는지 확인. 안 하면 호출부도 수정.

### 1-4. 200K 절삭 방향 수정 — head+tail 혼합

**Step A**: `modules/core/constants.py`에 헬퍼 추가 (ContextLimits 클래스 아래):

```python
def smart_truncate(text: str, max_chars: int = 200_000, head_chars: int = 20_000) -> str:
    """앞 head_chars(세계관 기초) + 뒤 나머지(최신 우선) 보존."""
    if len(text) <= max_chars:
        return text
    tail_budget = max_chars - head_chars - 50
    return text[:head_chars] + "\n\n...(중간 생략)...\n\n" + text[-tail_budget:]
```

**Step B**: 4곳 교체 (각 파일 상단에 `from modules.core.constants import smart_truncate` 추가):

| 파일 | 라인 | 변경 전 | 변경 후 |
|------|------|---------|---------|
| `modules/domain/agents/chief_writer_context.py` | ~L299 | `prev_manuscripts_text[:ContextLimits.MAX_CONTEXT_CHARS]` | `smart_truncate(prev_manuscripts_text)` |
| `modules/domain/agents/director_ensemble.py` | ~L339-340 | `_prev_ms_for_director[:ContextLimits.MAX_CONTEXT_CHARS] + "\n..."` | `smart_truncate(_prev_ms_for_director)` |
| `modules/domain/agents/director_continuity.py` | ~L383-384 | `history_text[:ContextLimits.MAX_CONTEXT_CHARS] + "\n..."` | `smart_truncate(history_text)` |
| `modules/domain/agents/blueprint_ensemble.py` | ~L678 | `result[:ContextLimits.MAX_CONTEXT_CHARS] + "\n..."` | `smart_truncate(result)` |

### 1-5. Director 후보 원고 심사 컷 12K → 전문

**파일**: `modules/domain/agents/director_ensemble.py` ~L328

```python
# 변경 전
"manuscript": c.get("manuscript", "")[:12000],
# 변경 후
"manuscript": c.get("manuscript", ""),
```

### 1-6. Director 연속성 현재원고 12K → 전문

**파일**: `modules/domain/agents/director_continuity.py`

2곳 수정:
- ~L392: `current_manuscript[:12000]` → `current_manuscript`
- ~L719: `new_manuscript[:12000]` → `new_manuscript`

---

## Phase 2: 컨텍스트 상한 외부화 + 확장 (7건)

### 2-1. `validation.yaml`에 context 섹션 추가

**파일**: `config/settings/validation.yaml`
**위치**: 파일 맨 끝에 추가

```yaml

# [V71] Gemini 컨텍스트 활용 설정
context:
  mandatory_context_max: 80000        # Stage4 mandatory_context 상한 (기존 50K)
  director_mandatory_max: 40000       # Director 앙상블 mandatory_context (기존 25K)
  lookback_excerpt_chars: 500         # 확장 lookback 발췌 글자수 (기존 200)
  lookback_total_chars: 4000          # 확장 lookback 총량 (기존 1500)
  vector_max_results_s4: 10           # Stage4 벡터 검색 결과 수 (기존 5)
  vector_max_results_s2: 5            # Stage2 벡터 검색 결과 수 (기존 2)
  cache_merge_chars_per_ep: 4000      # 캐시 병합 화당 글자수 (기존 2000)
```

### 2-2. mandatory_context 50K → 80K

**파일**: `modules/core/stage4_orchestrator.py` ~L479

```python
# 변경 전
if len(mandatory_context) > 50000:
# 변경 후
from modules.validation.threshold_helper import _threshold
_mc_max = _threshold("context.mandatory_context_max", 80000)
if len(mandatory_context) > _mc_max:
```
그리고 같은 함수 내의 `50000` → `_mc_max`, `49950` → `_mc_max - 50` 으로 모두 교체.

### 2-3. Director mandatory 25K → 40K

**파일**: `modules/domain/agents/director_ensemble.py` ~L374-377

```python
# 변경 전
_mc_for_director = mandatory_context[:25000]
if len(mandatory_context) > 25000:
    _mc_for_director = _mc_for_director[:24950] + "\n...(mandatory_context 25,000자 초과로 일부 생략)"
# 변경 후
from modules.validation.threshold_helper import _threshold
_dir_mc_max = _threshold("context.director_mandatory_max", 40000)
_mc_for_director = mandatory_context[:_dir_mc_max]
if len(mandatory_context) > _dir_mc_max:
    _mc_for_director = _mc_for_director[:_dir_mc_max - 50] + f"\n...(mandatory_context {_dir_mc_max:,}자 초과로 일부 생략)"
```

### 2-4. 확장 lookback 200자 → 500자, 총 1500 → 4000자

**파일**: `modules/core/stage4_context_builder.py`

(A) ~L80: `max_chars=200` → `max_chars=_threshold("context.lookback_excerpt_chars", 500)`
(B) ~L94-98: 발췌 150자 → 400자로 확대
```python
# 변경 전
first_para = content.split("\n\n")[0] if "\n\n" in content else content[:150]
...
if len(first_para) > 150:
    first_para = first_para[:147] + "..."
# 변경 후
_excerpt_max = _threshold("context.lookback_excerpt_chars", 500)
paragraphs = content.split("\n\n")
first_para = "\n\n".join(paragraphs[:2]) if len(paragraphs) > 1 else content[:_excerpt_max]
first_para = re.sub(r"\s+", " ", first_para).strip()
if len(first_para) > _excerpt_max:
    first_para = first_para[:_excerpt_max - 3] + "..."
```
(C) ~L105-106: `1500` → `_threshold("context.lookback_total_chars", 4000)`
```python
# 변경 전
if len(digest) > 1500:
    digest = digest[:1497] + "..."
# 변경 후
_total_max = _threshold("context.lookback_total_chars", 4000)
if len(digest) > _total_max:
    digest = digest[:_total_max - 3] + "..."
```

**import 추가**: 파일 상단에 `from modules.validation.threshold_helper import _threshold`

### 2-5. 벡터 검색 결과 확장

(A) **파일**: `modules/core/stage4_context_builder.py` ~L446
```python
# 변경 전
max_results=5,
# 변경 후
max_results=_threshold("context.vector_max_results_s4", 10),
```

(B) **파일**: `modules/core/stage2_preflight.py` ~L464
```python
# 변경 전
n_results=2
# 변경 후
from modules.validation.threshold_helper import _threshold
n_results=_threshold("context.vector_max_results_s2", 5)
```

### 2-6. 캐시 병합 화당 2000자 → 4000자

**파일**: `modules/domain/agents/base_agent.py` ~L1227
```python
# 변경 전
lines.append(f"내용 요약: {content[:2000]}...")
# 변경 후
from modules.validation.threshold_helper import _threshold
_merge_chars = _threshold("context.cache_merge_chars_per_ep", 4000)
lines.append(f"내용 요약: {content[:_merge_chars]}...")
```

### 2-7. 벡터 쿼리 입력 확대

**파일**: `modules/core/stage4_context_builder.py` ~L434
```python
# 변경 전
_mq_queries.append(arc_tactical[:300])
# 변경 후
_mq_queries.append(arc_tactical[:600])
```

---

## Phase 3: 벡터 메모리 보강 (4건)

### 3-1. 벡터 저장 summary 보강

**파일**: `modules/core/stage4_post_processor.py` ~L114-123

현재:
```python
self.ctx.memory.memorize_v20_episode(
    ep_num=next_ep,
    text=final_manuscript,
    summary=final_title[:100] if final_title else f"제{next_ep}화",
    ...
)
```

수정 — summary 조립 로직을 memorize 호출 직전에 추가:
```python
# [V71] 벡터 메모리 요약 보강 — 제목 + 핵심사건 + 상태변화
_summary_parts = [final_title or f"제{next_ep}화"]
if arc_data and isinstance(arc_data.get("state_changes"), dict):
    _sc = arc_data["state_changes"]
    if _sc.get("npc_deaths"):
        _summary_parts.append("사망: " + ", ".join(
            str(d.get("name", "")) for d in (_sc["npc_deaths"] if isinstance(_sc["npc_deaths"], list) else [])
        )[:60])
    if _sc.get("relationship_changes"):
        _summary_parts.append("관계: " + ", ".join(
            f"{r.get('npc','')or r.get('target','')}-{r.get('change','')}"
            for r in (_sc["relationship_changes"] if isinstance(_sc["relationship_changes"], list) else [])
        )[:80])
    if _sc.get("major_items"):
        _summary_parts.append("아이템: " + ", ".join(
            str(i.get("name", "")) for i in (_sc["major_items"] if isinstance(_sc["major_items"], list) else [])
        )[:60])
    if _sc.get("resolved_plots"):
        _rp = _sc["resolved_plots"]
        if isinstance(_rp, list):
            _summary_parts.append("해결: " + ", ".join(str(p)[:30] for p in _rp[:2]))
if blueprint and isinstance(blueprint, dict):
    _scene = blueprint.get("scene_summary", "") or blueprint.get("핵심장면", "")
    if _scene:
        _summary_parts.append(f"장면: {str(_scene)[:80]}")
_rich_summary = " | ".join(p for p in _summary_parts if p)[:500]

self.ctx.memory.memorize_v20_episode(
    ep_num=next_ep,
    text=final_manuscript,
    summary=_rich_summary,
    ...
)
```

### 3-2. 벡터 동기화 경로 summary 보강

**파일**: `modules/core/vec_memory.py` ~L416-417

```python
# 변경 전
first_line = content.split("\n")[0].strip()[:100]
self.memorize_v20_episode(ep_num, content, f"[동기화] {first_line}", {})
# 변경 후
excerpt = content[:500].replace("\n", " ").strip()
self.memorize_v20_episode(ep_num, content, f"[동기화] {excerpt}", {})
```

### 3-3. 벡터 검색 결과 포맷 보강

**파일**: `modules/core/vec_memory.py`

(A) `_recent_ep_context()` 메서드 ~L298-301:
```python
# 변경 전
blocks.append(f"{header}\n요약: {summary}")
# 변경 후
evt = meta.get("event_types", "")
ent = meta.get("entity_names", "")
block = f"{header}\n요약: {summary}"
if evt:
    block += f"\n사건: {evt}"
if ent:
    block += f"\n인물: {ent}"
blocks.append(block)
```

(B) `_knn_search()` 메서드 ~L327-328:
```python
# 변경 전
block = f"### [제 {rowid} 화의 기억]\n요약: {summary}"
# 변경 후
evt = meta.get("event_types", "")
ent = meta.get("entity_names", "")
block = f"### [제 {rowid} 화의 기억]\n요약: {summary}"
if evt:
    block += f"\n사건: {evt}"
if ent:
    block += f"\n인물: {ent}"
```

### 3-4. 벡터 쿼리 정보 확대

**파일**: `modules/core/stage4_context_builder.py` ~L434

이건 Phase 2-7에서 이미 처리됨 (300→600자). 중복이므로 스킵.

---

## Phase 4: 면담 전 전체 후보 사전검사 (3건)

### 4-1. 연속성 캐시 검사 → 전체 후보

**파일**: `modules/core/stage4_interview_round.py` ~L422-435

현재 (candidates[0]만 검사):
```python
if round_num == 0 and next_ep > 1 and candidates:
    stage4_spinner.update_detail(f"제{next_ep}화 · 연속성 검사")
    first_manuscript = candidates[0].get("manuscript", "")
    continuity_check = self.ctx.agents["director"].check_manuscript_continuity_with_cache(
        new_manuscript=first_manuscript,
        ep_num=next_ep,
        db=self.ctx.current_project.db,
        limit=10,
    )
    if continuity_check.get("decision") == "CONFLICT":
        conflict_summary = continuity_check.get("summary", "연속성 충돌 감지")
        self.ctx.ui.log(f"   ⚠️ [V61.5] 연속성 검사: {conflict_summary[:50]}...")
        director_feedback += f"\n[연속성 충돌]\n{conflict_summary}"
```

수정 (전체 후보 루프):
```python
if round_num == 0 and next_ep > 1 and candidates:
    stage4_spinner.update_detail(f"제{next_ep}화 · 연속성 검사")
    _continuity_conflicts = []
    for ci, cand in enumerate(candidates):
        _ms = cand.get("manuscript", "")
        if not _ms:
            continue
        continuity_check = self.ctx.agents["director"].check_manuscript_continuity_with_cache(
            new_manuscript=_ms, ep_num=next_ep,
            db=self.ctx.current_project.db, limit=10,
        )
        if continuity_check.get("decision") == "CONFLICT":
            conflict_summary = continuity_check.get("summary", "연속성 충돌 감지")
            self.ctx.ui.log(f"   ⚠️ [V61.5] 후보{ci+1} 연속성: {conflict_summary[:50]}...")
            if ci < len(validation_results):
                validation_results[ci]["warnings"].append(f"[연속성 충돌] {conflict_summary}")
                validation_results[ci]["warning_count"] = len(validation_results[ci]["warnings"])
            _continuity_conflicts.append(f"후보{ci+1}: {conflict_summary[:80]}")
    if _continuity_conflicts:
        director_feedback += "\n[연속성 충돌]\n" + "\n".join(_continuity_conflicts)
```

### 4-2. 역사 충돌 검사 → 전체 후보

**파일**: `modules/core/stage4_interview_round.py` ~L453-468

현재 (candidates[0]만):
```python
if _ms_history_for_check and candidates:
    _first_ms = candidates[0].get("manuscript", "")
    if _first_ms:
        _conflict_result = self.ctx.agents["director"].check_manuscript_history_conflicts(...)
```

수정 (전체 후보 루프):
```python
if _ms_history_for_check and candidates:
    _history_conflicts = []
    for ci, cand in enumerate(candidates):
        _cand_ms = cand.get("manuscript", "")
        if not _cand_ms:
            continue
        try:
            _conflict_result = self.ctx.agents["director"].check_manuscript_history_conflicts(
                ep_num=next_ep,
                current_manuscript=_cand_ms,
                manuscript_history=_ms_history_for_check,
                use_summary=False,
                story_context=_story_context,
            )
            if _conflict_result.get("decision") == "CONFLICT":
                _conflict_summary = _conflict_result.get("summary", "모순 감지")
                self.ctx.ui.log(f"   ⚠️ [V67] 후보{ci+1} 역사 충돌: {_conflict_summary[:80]}")
                if ci < len(validation_results):
                    validation_results[ci]["warnings"].append(f"[V67 역사 충돌] {_conflict_summary}")
                    validation_results[ci]["warning_count"] = len(validation_results[ci]["warnings"])
                _history_conflicts.append(f"후보{ci+1}: {_conflict_summary[:80]}")
        except Exception as _hc_err:
            logging.warning(f"⚠️ [V67] 후보{ci+1} 역사 충돌 검사 실패: {_hc_err}")
    if _history_conflicts:
        director_feedback += "\n[V67 원고 역사 충돌]\n" + "\n".join(_history_conflicts)
```

### 4-3. 호출부에서 story_context 전달 확인

`check_manuscript_continuity_with_cache()` 호출 시 `story_context` 파라미터가 전달되는지 확인.
Phase 1-3에서 시그니처에 추가했으므로, 여기서도 전달해야 함:
```python
continuity_check = self.ctx.agents["director"].check_manuscript_continuity_with_cache(
    new_manuscript=_ms, ep_num=next_ep,
    db=self.ctx.current_project.db, limit=10,
    story_context=_story_context,  # ← 추가
)
```

---

## 검증

```bash
# Ruff
python -m ruff check modules/ main_a.py tests/ --no-fix

# 전체 테스트
set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -q --tb=short --capture=no
# 기준선: 2100 passed, 68 xfailed
```

---

## Codex 실행 설정

```
모드: 코드 수정
모델: o3 또는 o4-mini
라운드: 제한 없음
컨텍스트: 이 파일 + 코드베이스 전체
Phase 순서: 반드시 1 → 2 → 3 → 4 순서
```

## 주의사항

- `_threshold` import는 이미 여러 파일에서 사용 중 — 기존 패턴 참고
- `constants.py`의 `smart_truncate`는 모듈 레벨 함수 (클래스 바깥)
- `ContextLimits.MAX_CONTEXT_CHARS`는 200K로 유지 (smart_truncate의 기본값으로 사용)
- Phase 4의 전체 후보 검사는 LLM 호출 3배 증가 — 이것은 의도된 동작
- 수정 후 기존 테스트 **전량 통과** 필수. 깨지는 테스트가 있으면 테스트 코드의 assertion을 새 동작에 맞게 수정
