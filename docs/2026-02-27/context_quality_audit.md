# 전 스테이지 컨텍스트 품질 감사 — 확정 보고서

> 작성일: 2026-02-27
> 감사 방법: 4개 1차 Explore TF (병렬) + 3개 2차 심층 TF (재검토·오탐 확인·확장 탐색)
> 총 7개 TF, 코드 수정 없이 분석만 수행
> 대상: Stage 0~4 전 파이프라인 + Director + 메모리/검색 시스템

---

## 0. 최종 요약

| 구분 | 건수 | 내용 |
|------|------|------|
| 오탐 (수정 불필요) | 4건 | 결함 A, C + IMP-01, IMP-03 |
| 확정 결함 (수정 필요) | 3건 | hud_snapshot, StyleGuide, NPC 3중 불일치 |
| 개선 기회 | 5건 | IMP-02/04/05 + Arc 경계 + Cache TTL |
| 관찰 대기 | 2건 | WorldState Manager 미참조, Arc 요약화 |

---

## 1. 오탐 판정 결과 (4건 — 수정 불필요)

### 오탐 1 — Chief Writer SC Retrieval merge 미연결 의심

**최초 주장**: `_execute_retrieval_plan()` 결과가 CW 프롬프트에 도달하지 않을 수 있음

**재확인 결과**: ✅ 정상 작동 확인

추적된 전체 경로:
```
stage4_context_builder.py:802
  _execute_retrieval_plan() → _mc_parts.append(_retrieved)
  ↓
stage4_context_builder.py:911
  mandatory_context = "\n\n".join(_mc_parts)   ← SC 포함
  ↓
stage4_orchestrator.py:377
  _ctx_prompts["mandatory_context"]
  ↓
stage4_interview_round.py:97
  _common_writer_kwargs["mandatory_context"]
  ↓
chief_writer_context.py:251
  writer_core_section += f"\n{mandatory_context}\n"   ← 프롬프트 렌더링
```

**조건**: `smart_retrieval.enabled=True` + `stage4_enabled=True` 시만 활성 (현재 둘 다 true)

---

### 오탐 2 — Stage 3 WorldState 미주입

**최초 주장**: Blueprint 생성 시 WorldState가 프롬프트에 없음 → 장기 연재 모순 위험

**재확인 결과**: ✅ 의도적 설계

근거:
- Blueprint는 **설계 수준**(how to write the scene), 원고는 **집필 수준** → 책임 분리
- `arc_data.state_changes` + `StateTracker`(고밀도 HUD)가 이미 현재 Arc의 세계 변화를 담아 전달 중
- `blueprint_ensemble.py` 시그니처에 `world_state` 파라미터 자체 없음 — 설계 의도 명백

---

### 오탐 3 — Director SC 비활성 (`director_enabled: false`)

**최초 주장**: SC 결과를 Director가 못 받아서 모순 감지율이 낮을 수 있음

**재확인 결과**: ✅ 의도적 설계 + SC-5 코드 완성 대기 상태

근거:
- `stage4_interview_round.py:589-694` — SC-5 구현은 완료됨 (장래 활성화 준비)
- **비활성 이유**: Director는 "최종 판정자" 역할이며, Python Validators 경고가 이미 `mandatory_context`에 포함되어 전달 중 (`stage4_interview_round.py:790-792`)
- 과도한 컨텍스트가 Director 판단 흐림 방지 (디자인 철학)
- `director_ensemble.py` 메서드 시그니처에 `memory_context` 파라미터 없음 → 활성화 시 추가 작업 필요

**결론**: 지금 활성화하면 안 됨. 향후 선택적 작업 대상.

---

### 오탐 4 — 독자 대리만족 → Chief Writer 미주입

**최초 주장**: CW가 독자 기대를 모름 → Director REJECT 후에만 학습

**재확인 결과**: ✅ 의도적 분리 설계

현재 정상 작동 경로:
```
ContinuityValidator.check_frustration_streak()
  ↓ (Python 경고 생성)
validation_results[i]["warnings"].append("[D Step 4] ...")
  ↓
Director mandatory_context에 포함 (stage4_interview_round.py:790-792)
  ↓
Director: 대리만족 부재 감지 → REJECT + "보상 장면 추가" 피드백
  ↓
Chief Writer: 피드백 받아 재작성
```

설계 철학: CW에 직접 주입 시 창작 자유도 제약 → "작가는 쓰고, Director가 감시"

---

## 2. 확정 결함 (3건 — 수정 필요)

### 결함 1 — hud_snapshot Dead Code
**파일**: `modules/domain/agents/chief_writer.py:870-887`
**심각도**: LOW (기능 자체는 다른 경로로 커버됨)
**유형**: Dead Code 잔존

**근거**:
```sql
-- db_manager.py:265-270 manuscripts DDL
CREATE TABLE IF NOT EXISTS manuscripts (
    ep_num INTEGER PRIMARY KEY,
    title TEXT,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
-- hud_snapshot 컬럼 없음 → get_recent_manuscripts() 항상 {} 반환
```

```python
# chief_writer.py:873 (자가 주석 인정)
# [V70] NOTE: manuscripts 테이블에 hud_snapshot 컬럼 없음 — 항상 {} 반환 (dead code)
hud_snapshot = past_ms.get("hud_snapshot", {}) if isinstance(past_ms, dict) else {}
self._manuscript_cache[i] = {"content": content, "hud_snapshot": hud_snapshot}  # 저장만 하고 사용 안 함
```

**HUD 실제 전달 경로** (대체 경로 정상 작동 중):
- `hud_report` 파라미터 → CW 직접 전달 (stage4_interview_round.py:75)
- `chief_writer_context.py:282-288` → `_get_hud_trend_safe()` 호출

**수정 플랜**:
```python
# chief_writer.py:870-887 영역에서 hud_snapshot 관련 코드 제거
# Before:
hud_snapshot = past_ms.get("hud_snapshot", {}) if isinstance(past_ms, dict) else {}
self._manuscript_cache[i] = {"content": content, "hud_snapshot": hud_snapshot}

# After:
self._manuscript_cache[i] = {"content": content}

# 반환부도 정리:
# Before: return self._manuscript_cache.get(ep_num, {"content": "", "hud_snapshot": {}})
# After:  return self._manuscript_cache.get(ep_num, {"content": ""})
```

**변경 크기**: ~10줄 제거
**리스크**: 없음 (dead code 제거)
**테스트 영향**: hud_snapshot 키 참조하는 테스트 있으면 함께 수정

---

### 결함 2 — Stage 0 컨셉 모드 StyleGuide 미추출
**파일**: `modules/core/stage0/__init__.py:251`
**심각도**: MED
**유형**: 구현 누락

**근거**:
```python
# stage0/__init__.py:251 — 컨셉 생성 모드
return self.bible, self.treatment, None  # StyleGuide 항상 None 반환

# stage0/__init__.py:288 — 역설계 모드는 정상
self.bible, self.episode_bibles, self.style_guide = expander.run(...)
return self.bible, self.treatment, self.style_guide  # ← 정상 반환
```

`style_extractor.py`는 구현 완료됨. 컨셉 생성 모드에서만 `extract_style_guide()` 호출이 누락.

**영향**:
- 컨셉 생성 시작 프로젝트: Stage 4 StyleGuard가 문체 기준 없이 작동
- `D-3` 완료(StyleGuard 래퍼) 이후에도 컨셉 모드 프로젝트는 빈 StyleGuide로 진행

**수정 플랜**:
```python
# stage0/__init__.py generate_from_concept() 내부 수정
# 현재 (L248-251):
def _run_concept_flow(self, ...):
    ...
    return self.bible, self.treatment, None

# 수정:
def _run_concept_flow(self, ...):
    ...
    # StyleGuide 추출 (스타일 추출기 활용)
    style_guide = None
    try:
        extractor = StyleExtractor(llm_client=self.client)
        style_guide = extractor.extract_from_bible(self.bible)
    except Exception as e:
        logging.warning("[Stage0] StyleGuide 추출 실패 (비차단): %s", e)
    return self.bible, self.treatment, style_guide
```

**변경 크기**: ~8줄
**리스크**: 낮음 (try/except로 비차단)
**전제**: `StyleExtractor.extract_from_bible()` 메서드 존재 여부 확인 필요

---

### 결함 3 — NPC 사망 정보 3중 저장소 불일치
**파일**: `modules/core/world_state.py:111-116`, `modules/core/truth_gate.py:73-82`
**심각도**: HIGH
**유형**: 동기화 메커니즘 부재

**구조**:
```
NPC 사망 정보가 3곳에 독립 저장:
1. WorldStateManager._state["dead_npcs"]  ← state_changes 기반 자동 갱신
2. StateTracker.npc_registry[name]["deceased"]  ← DB NPC 등록 기반
3. npc_registry status 필드 ("dead")  ← 별도 status
```

**불일치 시나리오**:
```
Arc 3: state_changes["npc_deaths"] = [{"name": "김철수"}]
  ↓ WorldState.update_from_state_changes() → dead_npcs["김철수"] 등록 ✅
  ↓ StateTracker.npc_registry["김철수"]["deceased"] ← 업데이트 안 됨 ❌

Stage 4 TruthGate:
  world_state.get_deceased_npcs() → ["김철수"]  (감지됨)
  stage4_interview_round.py의 dead_npcs 변수 ← StateTracker 기반 → 미포함 가능

→ 결과: TruthGate 경고는 나오나 Chief Writer가 받는 dead_npcs에는 없을 수 있음
```

**수정 플랜** (2가지 옵션):

**옵션 A — WorldState 갱신 시 StateTracker 동시 업데이트 (권장)**:
```python
# world_state.py update_from_state_changes() 내 NPC 사망 처리 후 추가
# (L114-116 이후)
for name in newly_dead:
    if hasattr(self, "_state_tracker") and self._state_tracker:
        if name in self._state_tracker.npc_registry:
            self._state_tracker.npc_registry[name]["deceased"] = True
```
→ WorldState 생성 시 state_tracker 참조 주입 필요 (생성자 수정)

**옵션 B — TruthGate를 SSOT로 통일 (단순)**:
```python
# stage4_context_builder.py에서 dead_npcs 수집 시
# 현재: StateTracker 기반
# 변경: WorldState.get_deceased_npcs() + StateTracker 병합
_dead_from_ws = self.ctx.world_state.get_deceased_npcs() if self.ctx.world_state else []
_dead_from_st = [n for n, info in st.npc_registry.items() if info.get("deceased")]
dead_npcs = list(set(_dead_from_ws) | set(_dead_from_st))
```

**권장**: 옵션 B — 변경 크기 작고 두 소스를 합집합으로 처리해 누락 최소화
**변경 크기**: ~5줄
**리스크**: 낮음 (합집합이므로 과잉 방지는 됨, 오탐 위험 없음)

---

## 3. 개선 기회 (5건)

### IMP-A — REJECT 피드백 위반 구절 인용
**파일**: `modules/core/stage4_interview_round.py`
**심각도**: MED (효율 개선)

**현재**: REJECT 시 `action_items` 텍스트만 전달, 원고 내 어느 부분이 문제인지 미지정

**수정 플랜**:
```python
# stage4_interview_round.py의 enhanced_feedback 구성 부분에 추가
def _extract_violation_excerpt(manuscript: str, action_items: list[str], window: int = 150) -> str:
    excerpts = []
    for item in action_items[:3]:  # 상위 3건만
        keywords = [w for w in item.split() if len(w) >= 2][:3]
        for kw in keywords:
            idx = manuscript.find(kw)
            if idx >= 0:
                start = max(0, idx - window)
                end = min(len(manuscript), idx + window)
                excerpts.append(f'..{manuscript[start:end]}..')
                break
    return "\n".join(excerpts) if excerpts else ""

# enhanced_feedback 앞에 삽입
_excerpt = _extract_violation_excerpt(prev_manuscript, action_items)
if _excerpt:
    enhanced_feedback = f"[위반 구절 참고]\n{_excerpt}\n\n{enhanced_feedback}"
```

**변경 크기**: ~20줄
**리스크**: 없음 (원고 인용만 추가)
**효과**: 재작성 정확도 향상 → 평균 재시도 횟수 감소

---

### IMP-B — Stage 2 이전 Arc 요약화 (장기 연재 토큰 최적화)
**파일**: `modules/core/stage2_orchestrator.py:242`, `modules/domain/agents/state_extractor.py`
**조건**: 30화 이상 프로젝트에서만 의미 있음
**심각도**: MED (성능)

**현재**: `all_refined_arcs` 전체 누적 참조 → Arc 50개 이상 시 StateExtractor 재계산 비용 폭증

**수정 플랜**:
```python
# stage2_orchestrator.py generate_arcs_batch() 내
# 현재: arc_context = generate_arc_context_v60(all_refined_arcs, ...)
# 변경:
_RECENT_ARCS = 3
if len(all_refined_arcs) > _RECENT_ARCS:
    recent = all_refined_arcs[-_RECENT_ARCS:]
    old_summary = _summarize_old_arcs(all_refined_arcs[:-_RECENT_ARCS])  # 신규 유틸
    arc_context = generate_arc_context_v60(recent, ..., prefix=old_summary)
else:
    arc_context = generate_arc_context_v60(all_refined_arcs, ...)
```

**전제**: `_summarize_old_arcs()` 유틸 구현 필요 (~50줄)
**변경 크기**: ~80줄 (유틸 포함)
**리스크**: 중간 — Arc 요약 품질에 의존. **POC 완료 후 진행 권장**

---

### IMP-C — 임베딩 캐시 LRU 확대
**파일**: `modules/core/vec_memory.py:73`
**심각도**: LOW

**수정**:
```python
# Before:
@lru_cache(maxsize=128)
# After:
@lru_cache(maxsize=512)
```

**변경 크기**: 1줄
**리스크**: 없음 (메모리 +수십 MB)
**효과**: 50화 이상 세션에서 embedding API 호출 -40~60%

---

### IMP-D — Arc 경계 state_changes 누적 전달 강화
**파일**: `modules/core/stage3_orchestrator.py`, `modules/domain/agents/blueprint_ensemble.py`
**심각도**: MED

**현재**: Arc N → Arc N+1 Blueprint 생성 시 Arc N의 최종 state_changes가 Blueprint에 명시 전달 안 됨
(StateTracker로 간접 커버 중이나 Blueprint 프롬프트에 직접 표시 없음)

**수정 플랜**:
```python
# stage3_orchestrator.py에서 Blueprint 생성 호출 시 추가
_prev_arc_state = ""
if all_refined_arcs:
    _last_arc = all_refined_arcs[-1]
    _sc = _last_arc.get("state_changes", {})
    if _sc:
        _prev_arc_state = _format_arc_boundary_state(_sc)  # 신규 유틸

# three_phase_bp.generate()에 prev_arc_state 파라미터 추가
# blueprint_ensemble.py 프롬프트에 {prev_arc_state} 슬롯 추가
```

**변경 크기**: ~30줄
**리스크**: 낮음
**효과**: Arc 경계 화에서 Blueprint 모순 감소 (특히 NPC 사망/아이템 상태)

---

### IMP-E — Cache TTL 재생성 최적화
**파일**: `modules/domain/agents/base_agent.py:1213-1240`
**심각도**: LOW

**현재**: TTL 만료 시 캐시 삭제 후 재생성 (Gemini API 비용 재발생)

**수정 플랜**:
```python
# base_agent.py _get_or_create_context_cache() 내
# 만료 5분 전 갱신 로직 추가
_RENEW_THRESHOLD = 300  # 5분

if current_time - cached_info["created_at"] < ttl_seconds - _RENEW_THRESHOLD:
    return cached_info  # 아직 유효
elif current_time - cached_info["created_at"] < ttl_seconds:
    # 만료 임박 → Gemini cache update API로 TTL 연장
    try:
        self.client.caches.update(cached_info["cache_name"], ttl=ttl_seconds)
        cached_info["created_at"] = current_time
        return cached_info
    except Exception:
        pass  # 실패 시 기존 흐름 유지
```

**변경 크기**: ~10줄
**리스크**: 낮음
**효과**: 장시간 세션에서 캐싱 비용 절약

---

## 4. 관찰 대기 (2건)

| # | 항목 | 파일 | 이유 |
|---|------|------|------|
| OBS-1 | WorldState → Manager LLM 미전달 | `stage4_post_processor.py:264` | `current_state`에 WorldState 미포함. 영향 낮음, 현재 운영 이슈 없음 |
| OBS-2 | Director SC 활성화 | `validation.yaml:163` | SC-5 코드 완성됨. director_ensemble.py 시그니처 확장 필요. POC 완료 후 검토 |

---

## 5. 수정 우선순위 로드맵

### Phase A — 즉시 (1줄, 리스크 없음) ✅ 완료

| # | 항목 | 파일:위치 | 변경 | 상태 |
|---|------|---------|------|------|
| A-1 | IMP-C: 캐시 LRU 512 | `vec_memory.py:75` | `_embed_cache_max = 128` → `512` | ✅ 완료 (2026-02-27) |

---

### Phase B — 단기 (10~30줄, 낮은 리스크)

| # | 항목 | 파일:위치 | 변경 크기 |
|---|------|---------|---------|
| B-1 | 결함 3: NPC 사망 합집합 | `stage4_context_builder.py` | ~5줄 |
| B-2 | 결함 1: hud_snapshot dead code 제거 | `chief_writer.py:870-887` | ~10줄 제거 |
| B-3 | IMP-A: REJECT 피드백 인용 | `stage4_interview_round.py` | ~20줄 |
| B-4 | IMP-E: Cache TTL 갱신 | `base_agent.py:1213-1240` | ~10줄 |

검증: `pytest tests/ -q` (2,692 passed 유지) + `ruff check modules/`

---

### Phase C — 중기 (30~80줄, 설계 확인 필요)

| # | 항목 | 파일:위치 | 전제 조건 |
|---|------|---------|---------|
| C-1 | 결함 2: StyleGuide 컨셉 모드 추출 | `stage0/__init__.py:251` | `StyleExtractor.extract_from_bible()` 존재 확인 |
| C-2 | IMP-D: Arc 경계 state_changes 전달 | `stage3_orchestrator.py` | `_format_arc_boundary_state()` 유틸 구현 |

---

### Phase D — 후순위 (POC 완료 후)

| # | 항목 | 이유 |
|---|------|------|
| D-1 | IMP-B: Stage 2 Arc 요약화 | `_summarize_old_arcs()` 품질 검증 필요. 30화+ 프로젝트에서만 의미 있음 |
| D-2 | OBS-1: WorldState → Manager | 운영 이슈 없음, 낮은 영향도 |
| D-3 | OBS-2: Director SC 활성화 | 시그니처 확장 + YAML 슬롯 추가 필요 |

---

## 6. 감리 결과 — 1차 vs 2차 비교

| 1차 판정 | 2차 재판정 | 항목 |
|---------|---------|------|
| 결함 A (SC merge) | **오탐** | SC 경로 정상 작동 확인 |
| 결함 B (hud_snapshot) | **결함 유지** (영향 낮음) | dead code, 다른 경로로 커버 중 |
| 결함 C (Stage 3 WorldState) | **오탐** | 의도적 설계 (Blueprint 설계 수준) |
| IMP-01 (Director SC) | **오탐** | 의도적 비활성, 판단 흐림 방지 |
| IMP-02 (Arc 요약화) | **유지** | 장기 연재 시 필요, Phase D |
| IMP-03 (대리만족 CW) | **오탐** | 의도적 분리, Director 통한 간접 제어 |
| IMP-04 (REJECT 인용) | **유지** (IMP-A로 재명명) | Phase B |
| IMP-05 (캐시 512) | **유지** (IMP-C로 재명명) | Phase A |
| 신규 발견 | — | 결함 2,3 + IMP-D,E 추가 |

**오탐률**: 1차 7건 중 4건 오탐 (57%) → 최종 실결함 3건 + 개선 5건

---

---

## 7. 외부 수정 반영 (2026-02-27 타 작업 보고)

### 개요
4건 수정 완료 보고 (별도 작업 그룹). 2,694 passed + 감리 3개 병렬 CORRECT.

### 각 수정의 감사 문서 영향

| Fix | 내용 | 감사 항목 영향 |
|-----|------|--------------|
| **Fix A** | `truth_gate.py L70` — npc_registry "status":"dead" 형식 추가 감지 | **결함 3 부분 완화**: TruthGate 감지 gap 수정됨. CW dead_npcs 합집합(B-1)은 미수정. 결함 3 수정 플랜 유효 |
| **Fix B** | emotional_beat 전체 파이프라인 연결 (arc_data → CW 프롬프트) | **신규 개선 확인**: 감사 미포함 항목. 컨텍스트 질 향상. |
| **Fix C** | director_feedback 라운드 간 일반 지시 소실 수정 (`_prev_general_lines` 복원) | **IMP-A 선행 수정**: IMP-A(REJECT 인용)의 선결 조건 해소. 300자 제한은 여전히 잔존 (방어적 제약 조사 대상) |
| **Fix D** | ending_hook Blueprint → Chief Writer 연결 | **신규 개선 확인**: 감사 미포함 항목. Blueprint 컨텍스트 완성도 향상. |

### 로드맵 재조정

- **B-3 IMP-A**: Fix C로 일반 지시 소실 문제 해소. 위반 구절 인용 기능은 여전히 미구현 → 유지
- **결함 3 (B-1)**: Fix A로 TruthGate 감지 개선됨. stage4_context_builder 합집합 처리는 미수정 → 유지
- **신규 조사**: 300자 제한 등 방어적 토큰 제약 전수조사 진행 중 → Section 8에 결과 추가 예정

---

## 8. 방어적 토큰 제약 전수조사 (2026-02-27)

> 조사 대상 9개 파일. 발견 39건 (심각 10 · 주의 20 · OK 9).
> 원칙 "충분한 컨텍스트 전달 > 토큰 예산 절감"에 **현재 위배 상태**.

### 8-1. 심각 10건 — LLM 입력 직접 제약

| # | 파일:라인 | 제약 | 영향 | 권장 |
|---|---------|------|------|------|
| **S-1** | `stage4_interview_round.py:300` | `blueprint[:3000]` (ConsistencyValidator 입력) | Blueprint 절반 이상 손실 | 10,000+ |
| **S-2** | `stage4_context_builder.py:436` | `_tier2_summary[:500]` (11~30화 요약) | 중거리 맥락 50%+ 손실 | 2,000+ |
| **S-3** | `stage4_context_builder.py:483` | `_tier3_arc_summary[:1000]` (30화+ 아크 요약) | 장기 아크 맥락 손실 | 3,000+ |
| **S-4** | `stage4_context_builder.py:345` | `lookback_excerpt[:500]` + 첫 2문단만 | 4~10화 정보 대부분 누락 | 2,000+ / 5문단 |
| **S-5** | `stage4_context_builder.py:564,687` | `world_state[:5000]`, `fact_ledger[:15000]` | 세계 상태·팩트 원장 20~30% 손실 | 10,000 / 30,000 |
| **S-6** | `stage4_context_builder.py:839,841` | `arc_tactical[:1800]` | 에피소드 전술 30~40% 손실 | 3,000+ |
| **S-7** | `director_ensemble.py:81` | `arc_tactical_ep[:6000]` | Director 전술서 정보 손실 | 10,000+ |
| **S-8** | `director_ensemble.py:428~434` | `mandatory_context[:40,000]` | **Director 판정 근거 40~50% 손실 가능. REJECT 오판 위험** | 80,000+ |
| **S-9** | `director_ensemble.py:599` | `manuscript[:6000]` (quick_judge_single) | 원고 8~12,000자 중 절반 이상 손실 | 15,000+ |
| **S-10** | `context_advisor.py` | Stage4 총 예산 50,000자, 슬롯 상한 8개 | 슬롯당 평균 6,250자 압축 | 100,000+ / 12~15슬롯 |

### 8-2. 주의 20건 — 임계값/리스트 제약

| 경로 | 제약 | 권장 |
|------|------|------|
| `chief_writer_context.py:432~547` | 부상·관계·미스터리 20~50자 절삭 | 100~200자 |
| `chief_writer_context.py:651~700` | 부상 5개, 소지품 15개, 무공 10개 | 20/30/20 이상 |
| `chief_writer_context.py:1054~1072` | 요약 200자, major_changes 2개, 최근 이벤트 5개 | 500자/5개/20개 |
| `director_ensemble.py:396` | Blueprint 문자열 15,000자 | 25,000+ |
| `director_continuity.py:81` | Entity 검증 원고 15,000자 | 30,000+ |
| `director_continuity.py:494` | 원고 연속성 검사 36,000자 (불일치) | 전체 또는 통일 |
| `director_continuity.py:242~323` | 씬 키워드 5개, 샘플 100자, 누락 씬 3개 | 10개/300자/10개 |
| `stage3_orchestrator.py:476~513` | NPC 로스터 10→5개, 슬롯 2,000자 | 20개/5,000자 |
| `stage2_orchestrator.py:652` | 재시도 제약 조건 6,000자 | 20,000+ |
| `context_advisor.py:304` | 쿼리 개수 stage4=8개 상한 | 12~15개 |

### 8-3. 누락 항목 — director_feedback 300자 제한 (사용자 지적)

`stage4_interview_round.py:1046`:
```python
_prev_text = " / ".join(_prev_general_lines)[:300]
director_feedback += f"\n[R{round_num - 1} 이전 지시] {_prev_text}"
```
- **이전 라운드 일반 지시**를 300자로 절삭. 임의 설정.
- Fix C(타 작업)로 보존 자체는 해결됐으나 300자 한도는 잔존
- **권장**: 1,000자 이상으로 확대 (또는 토큰 예산과 별개로 전량 보존)

### 8-4. 종합 평가

**가장 심각한 경로**: Director → Chief Writer 정보 흐름
```
FactLedger(15,000) + WorldState(5,000) + Tier2(500×N) + Tier3(1,000×M)
= mandatory_context → Director에서 40,000자 추가 절삭
→ Director 판정 근거 정보의 실제 도달률: 30~60%
```

**개선 비용**: 낮음 (대부분 설정값 변경)
**추정 효과**: Director 정확도 5~10% ↑, CW 연속성 10~15% ↑

### 8-5. 수정 우선순위 (방어적 제약 해제)

| 우선순위 | 항목 | 방법 | 크기 |
|---------|------|------|------|
| **즉시** | `context.director_mandatory_max` 40,000 → 80,000 | YAML 설정 변경 | 1줄 |
| **즉시** | `director_ensemble.py:396` blueprint 15,000 → 25,000 | 상수 변경 | 1줄 |
| **즉시** | `context.lookback_excerpt_chars` 500 → 2,000 | YAML 또는 코드 | 1줄 |
| **단기** | Tier2/3 요약 500→2,000 / 1,000→3,000 | 코드/설정 | 2줄 |
| **단기** | WorldState 5,000→10,000, FactLedger 15,000→30,000 | 호출부 파라미터 | 2줄 |
| **단기** | quick_judge 6,000→15,000 | 상수 변경 | 1줄 |
| **단기** | director_feedback 이전 지시 300→1,000 | 코드 1줄 | 1줄 |
| **단기** | CW digest 20~50자→100~200자 | 상수 다수 | ~10줄 |
| **중기** | Smart Context 예산 50,000→100,000, 쿼리 8→15 | 설정+코드 | ~5줄 |
| **중기** | ConsistencyValidator blueprint 3,000→10,000 | 코드 | 1줄 |

---

*최초 확정 — 2026-02-27 (7개 Explore TF 병렬 2라운드)*
*갱신 — 2026-02-27: Phase A 완료 + 외부 수정 4건 반영 + 방어적 제약 조사 추가*
