# Phase 4 잔여 리팩토링 실행 계획

> Phase 6-B E2E 기준선 확보 후 착수.
> 기준선: E2E 22 passed (1.15s), 회귀 76 passed (2.88s)
> 기준 커밋: `1678550`

---

## 1. 정량 분석 결과

### 1-A. 파일 규모

| 파일 | 총 줄수 | 함수 수 | try/except | self.ctx 고유속성 | self.ctx 참조 |
|------|---------|---------|------------|-------------------|---------------|
| `stage2_orchestrator.py` | 2,368 | 10 | 73 | 43 | 348 |
| `stage4_orchestrator.py` | 1,892 | 7 | 63 | 22 | 320 |
| **합계** | **4,260** | **17** | **136** | **65** | **668** |

### 1-B. 함수 길이 Top 10

| # | 파일 | 함수명 | 범위 | 줄수 |
|---|------|--------|------|------|
| 1 | stage2 | `_compute_preflight` | L460–L2222 | **1,763** |
| 2 | stage4 | `stage_4_v2_chief_writer` | L200–L1892 | **1,693** |
| 3 | stage2 | `stage_2_arcs_async_logic` | L60–L289 | 230 |
| 4 | stage2 | `throttled_enrich` | L290–L442 | 153 |
| 5 | stage2 | `_stage2_flow_guard` | L2270–L2345 | 76 |
| 6 | stage4 | `_build_extended_lookback_digest` | L146–L199 | 54 |
| 7 | stage4 | `_extract_chain_link` | L55–L105 | 51 |
| 8 | stage4 | `_load_chain_link_section` | L106–L145 | 40 |
| 9 | stage2 | `_is_tactical_doc_duplicate` | L2234–L2261 | 28 |
| 10 | stage2 | `jaccard` | L2349–L2368 | 20 |

**핵심 문제**: 2개 몬스터 함수(1,763 + 1,693 = 3,456줄)가 전체의 81%.

### 1-C. try/except 분포

| 파일 | 총 블록 | 몬스터 함수 내 | 비율 |
|------|---------|---------------|------|
| stage2 | 73 | ~58 (`_compute_preflight`) | 79% |
| stage4 | 63 | ~48 (`stage_4_v2_chief_writer`) | 76% |

### 1-D. async/sync 혼용 지점

| 파일 | 위치 | 키워드 | 함수 |
|------|------|--------|------|
| stage2 | L60 | `async def` | `stage_2_arcs_async_logic` |
| stage2 | L290 | `async def` | `throttled_enrich` |
| stage2 | L307 | `asyncio.gather` | `throttled_enrich` |
| stage2 | L478 | `ThreadPoolExecutor` | `_compute_preflight` |
| stage4 | — | (없음) | **완전 동기** |

**혼용**: stage2에서 async 진입점 → 내부 `ThreadPoolExecutor`로 CPU-bound 분기. stage4는 동기 전용.

### 1-E. self.ctx 의존 클러스터

#### stage2_orchestrator (43속성, 348참조)

| 기능 클러스터 | 속성 | 참조수 |
|--------------|------|--------|
| **UI** | `ui` | 99 |
| **상태 추적** | `state_tracker` | 63 |
| **감사/로깅** | `audit_event` | 36 |
| **에이전트** | `agents` | 22 |
| **프로젝트** | `current_project` | 21 |
| **최적화** | `stage2_optimizer` | 12 |
| **캐시** | `cumulative_state_cache`, `cumulative_state_cache_key` | 14 |
| **검증** | `arc_draft_validator`, `constraint_compiler`, `semantic_plot_guard`, `arc_corrector` | 16 |
| **품질** | `pass_rate_monitor`, `quality_dashboard`, `quality_amplifier`, `failure_learner` | 16 |
| **콜백** | `get_int_input`, `safe_commit_async`, `write_audit_summary` 등 20종 | 49 |

#### stage4_orchestrator (22속성, 320참조)

| 기능 클러스터 | 속성 | 참조수 |
|--------------|------|--------|
| **UI** | `ui` | 112 |
| **프로젝트** | `current_project` | 58 |
| **상태 추적** | `state_tracker` | 51 |
| **시스템** | `sys` | 25 |
| **에이전트** | `agents` | 13 |
| **V68 시스템** | `world_state`, `fact_ledger` | 15 |
| **부가 기능** | `memory`, `character_voice`, `foreshadow_tracker`, `perf_timer` | 26 |
| **콜백** | `get_int_input`, `flush_audit_buffer`, `safe_commit` 등 7종 | 20 |

---

## 2. 분할 우선순위

**원칙**: 가장 큰 함수부터, 기능 경계에서 자른다.

| 우선순위 | 대상 | 현재 | 목표 | 난이도 |
|---------|------|------|------|--------|
| **P1** | `stage4.stage_4_v2_chief_writer` (1,693줄) | 1함수 | 8~10 서브함수 | 중 |
| **P2** | `stage2._compute_preflight` (1,763줄) | 1함수 | 10~12 서브함수 | 고 |
| **P3** | try/except 정리 (136블록) | 산재 | 에러 핸들링 헬퍼 도입 | 저 |
| **P4** | stage2 async/sync 통일 | ThreadPool+asyncio 혼용 | async 단일 경로 | 고 |

**P1이 먼저인 이유**:
- stage4는 동기 전용 → async 복잡도 없음
- E2E 테스트가 stage4 파이프라인을 더 두텁게 커버
- ctx 속성 22개 (stage2의 절반) → 분할 시 인자 전달이 단순

---

## 3. 무중단 리팩토링 순서 (커밋 단위)

### Phase 4-R1: stage4 몬스터 분할

| 커밋 | 작업 | 예상 줄수 변화 |
|------|------|---------------|
| **4-R1-a** | `_prepare_episode_context()` 추출 (L200~L470) — 컨텍스트 구성 블록 | ±0 (이동) |
| **4-R1-b** | `_run_interview_loop()` 추출 (L470~L1200) — 3라운드 심사 루프 | ±0 |
| **4-R1-c** | `_process_pass_result()` 추출 (L1200~L1600) — 합격 후처리 | ±0 |
| **4-R1-d** | `_run_post_episode_tasks()` 추출 (L1600~L1892) — V68 시스템 갱신 | ±0 |
| **4-R1-e** | 인터뷰 루프 내부 분할: `_execute_round()`, `_handle_reject()`, `_handle_pass()` | ±0 |
| **4-R1-f** | try/except 정리 — stage4 내 63블록 → 헬퍼 `_safe_call()` 도입 | -50~80줄 |

### Phase 4-R2: stage2 몬스터 분할

| 커밋 | 작업 | 예상 줄수 변화 |
|------|------|---------------|
| **4-R2-a** | `_preflight_state_setup()` 추출 (L460~L750) — 상태 초기화 | ±0 |
| **4-R2-b** | `_preflight_arc_analysis()` 추출 (L750~L1200) — Arc 분석 | ±0 |
| **4-R2-c** | `_preflight_enrichment()` 추출 (L1200~L1600) — 보강 루프 | ±0 |
| **4-R2-d** | `_preflight_validation()` 추출 (L1600~L2000) — 검증 체인 | ±0 |
| **4-R2-e** | `_preflight_finalize()` 추출 (L2000~L2222) — 마무리/저장 | ±0 |
| **4-R2-f** | try/except 정리 — stage2 내 73블록 | -60~100줄 |

### Phase 4-R3: async/sync 통일 (선택적)

| 커밋 | 작업 |
|------|------|
| **4-R3-a** | `_compute_preflight` 내 ThreadPoolExecutor → `asyncio.to_thread` 전환 |
| **4-R3-b** | stage2 진입점 async 호출 체인 정리 |

---

## 4. 게이트 (각 커밋마다)

```
# Gate 1: py_compile (변경 파일)
python -m py_compile modules/core/stage4_orchestrator.py

# Gate 2: SovereignApp import
python -c "from main_a import SovereignApp; print('OK')"

# Gate 3: E2E 기준선 (22 passed)
$env:PYTHONIOENCODING='utf-8'; pytest tests/e2e/ -v

# Gate 4: 회귀 (76 passed)
$env:PYTHONIOENCODING='utf-8'; pytest tests/test_npc_history.py tests/test_config_manager.py tests/test_stage4_orchestrator.py -v

# Gate 5: 전체 테스트 (선택)
$env:PYTHONIOENCODING='utf-8'; pytest tests/ -v

# Gate 6: pre-commit
pre-commit run --files modules/core/stage4_orchestrator.py

# Gate 7: self.ctx 참조 불변 확인
python -c "
import re
with open('modules/core/stage4_orchestrator.py') as f:
    refs = re.findall(r'self\.ctx\.(\w+)', f.read())
print(f'ctx refs: {len(refs)}, unique: {len(set(refs))}')
"
```

**통과 기준**: Gate 1~4 필수, Gate 5~7 권장.

---

## 5. 롤백 기준

| 상황 | 조치 |
|------|------|
| Gate 3 실패 (E2E) | 즉시 `git revert HEAD` |
| Gate 4 실패 (회귀) | 즉시 `git revert HEAD` |
| self.ctx 참조수 변동 ±5% 이상 | 커밋 전 원인 확인, 의도적이 아니면 중단 |
| `SovereignApp` import 실패 | 즉시 `git revert HEAD` |
| 커밋 후 실 파이프라인 실행 실패 | 해당 커밋 revert + 원인 분석 후 재시도 |

**안전 장치**: 각 Phase 시작 전 `git tag phase4-rN-start` 태그.

---

## 6. 착수 첫 커밋 상세 — 4-R1-a

**대상**: `stage4_orchestrator.py` L200~L470 (에피소드 컨텍스트 구성)

**변경 내용**:
```python
# Before
async def stage_4_v2_chief_writer(self, ...):
    # L200~L470: 에피소드 컨텍스트 구성 (bible, blueprint, lookback, chain_link 등)
    # L470~L1892: 인터뷰 루프 + 후처리
    ...

# After
def _prepare_episode_context(self, ep_no, current_arc, blueprint, ...):
    """에피소드 컨텍스트 구성: bible, blueprint, lookback, chain_link, world_state"""
    # L200~L470 내용 이동
    return episode_context

async def stage_4_v2_chief_writer(self, ...):
    episode_context = self._prepare_episode_context(...)
    # L470~ 이후 계속
    ...
```

**ctx 의존**: `ui`(5), `current_project`(12), `sys`(4), `state_tracker`(2) → 인자 대신 `self.ctx` 그대로 사용.

**예상 위험**: 없음 (순수 Extract Method, 로직 변경 0).
