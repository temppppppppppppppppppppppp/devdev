# Phase 4 잔여 리팩토링 실행 계획

> Phase 6-B E2E 기준선 확보 후 착수.
> 기준선: E2E 22 passed (1.09s), 회귀 78 passed, unit 22 passed, pipeline 89 passed
> 기준 커밋: `1678550`
> **현재 상태**: Phase 4-R1 완료, Phase 4-R2(a–e) 완료, **Phase 4-R3(a–h) 완료**, checkpoint `38a5ab5`

---

## 1. 정량 분석 결과

### 1-A. 파일 규모

| 파일 | 줄수 (시작) | 줄수 (현재) | 함수 수 | self.ctx 참조 |
|------|------------|------------|---------|---------------|
| `stage2_orchestrator.py` | 2,368 | **2,592** | **16** | 348 |
| `stage4_orchestrator.py` | 1,892 | **2,230** | **17** | 321 |
| **합계** | **4,260** | **4,822** | **33** | **669** |

> stage4 줄수 증가는 10개 서브메서드 시그니처 + 4개 dataclass 정의 (구조 개선 비용). 몬스터 함수 1,693줄 → 33줄.
> stage2 줄수 증가는 7개 서브메서드 시그니처 + 메트릭 헬퍼 2종 (구조 개선 비용). 몬스터 함수 1,763줄 → 100줄.

### 1-B. 함수 길이 Top 10

| # | 파일 | 함수명 | 범위 | 줄수 |
|---|------|--------|------|------|
| 1 | stage2 | `_compute_preflight` | L460–L2222 | ~~1,763~~ → **100** ✅ |
| 2 | stage4 | `stage_4_v2_chief_writer` | L200–L1892 | ~~1,693~~ → **33** ✅ |
| 3 | stage2 | `stage_2_arcs_async_logic` | L60–L289 | 230 |
| 4 | stage2 | `throttled_enrich` | L290–L442 | 153 |
| 5 | stage2 | `_stage2_flow_guard` | L2270–L2345 | 76 |
| 6 | stage4 | `_build_extended_lookback_digest` | L146–L199 | 54 |
| 7 | stage4 | `_extract_chain_link` | L55–L105 | 51 |
| 8 | stage4 | `_load_chain_link_section` | L106–L145 | 40 |
| 9 | stage2 | `_is_tactical_doc_duplicate` | L2234–L2261 | 28 |
| 10 | stage2 | `jaccard` | L2349–L2368 | 20 |

**핵심 문제**: ~~2개 몬스터 함수(1,763 + 1,693 = 3,456줄)가 전체의 81%.~~ → **해결 완료** (1,763→100, 1,693→33).

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

### Phase 4-R1: stage4 몬스터 분할 ✅ 완료

| 커밋 | 해시 | 작업 | 줄수 변화 |
|------|------|------|-----------|
| **4-R1-a** | `40b43b9` | `_prepare_episode_context()` 추출 — 컨텍스트 구성 | +136/-130 |
| **4-R1-b** | `5761aa8` | `_build_mandatory_context()` 추출 — 필수 컨텍스트 조립 | +103/-89 |
| **4-R1-c** | `35d6035` | `_process_pass_result()` 추출 — 합격 후처리 | +146/-136 |
| **4-R1-d** | `f94822e` | `_run_post_episode_tasks()` 추출 — V68 시스템 갱신 | +93/-79 |
| **4-R1-e-1** | `c5784de` | `_run_interview_round()` 추출 — 단일 라운드 실행 | +282/-273 |
| **4-R1-e-2** | `fc0999a` | `_build_round_context()` 추출 — 라운드 컨텍스트 빌더 | +145/-123 |
| **4-R1-e-3** | `2f30b9d` | `_handle_round_outcome()` 추출 — 3라운드+냉동인간 | +144/-99 |
| **4-R1-e-4** | `cc54deb` | `_run_interview_loop()` 추출 — 에피소드 생산 루프 | +239/-206 |
| **4-R1-f** | `6c5f292` | `_prepare_stage4_session()` 추출 — 세션 부트스트랩 | +99/-89 |

**결과**: `stage_4_v2_chief_writer()` 1,693줄 → 33줄 (98% 축소), 10개 서브메서드 추출

### Phase 4-R2: stage4 typed context carriers ✅ 완료

| 커밋 | 해시 | 작업 | 줄수 변화 |
|------|------|------|-----------|
| **4-R2-a** | `df88aca` | `_SessionConfig` dataclass (12 fields) — 세션 파라미터 번들링 | +49/-31 |
| **4-R2-b** | `611fefa` | `_RoundContext` dataclass (33 fields) — 라운드 kwargs 번들링 | +121/-79 |
| **4-R2-b-hotfix** | `9ade2db` | `return {{...}}` set-literal 버그 수정 (2곳) | +8/-12 |
| **4-R2-c-test** | `20b60d6` | 에러 경로 회귀 테스트 2건 추가 | +145/0 |
| **4-R2-d** | `3530c00` | `_RoundOutcome` dataclass (4 fields) — 라운드 결과 타입화 | +52/-41 |
| **4-R2-e** | `210cb47` | `_InterviewRoundResult` dataclass (6 fields) — 면담 결과 타입화 | +53/-29 |

**결과**: 4개 typed context carrier, 37-param 시그니처 → 5-param, untyped dict 반환 전량 제거

### Phase 4-R3: stage2 몬스터 분할 ✅ 완료

| 커밋 | 해시 | 작업 | 줄수 변화 |
|------|------|------|-----------|
| **4-R3-a** | `4288497` | `_preflight_state_setup()` 추출 — 상태 초기화 | +71/-58 |
| **4-R3-b** | `0ed3ef7` | `_preflight_arc_analysis()` 추출 — Arc 분석 | +81/-60 |
| **4-R3-c** | `5a1790d` | `_preflight_enrichment()` 추출 — FourPhase + 상태 보강 | +60/-39 |
| **4-R3-d** | `c1e0575` | `_preflight_validation()` 추출 — 검증 체인 (12 continue→return) | +128/-65 |
| **4-R3-e** | `afb5787` | `_preflight_finalize()` 추출 — Director 심사 + 후처리 (async) | +142/-55 |
| **4-R3-f** | `adcda5e` | PASS/REJECT 메트릭 헬퍼 추출 (7 try/except → 2 call) | +117/-100 |
| **4-R3-g** | `882cd0a` | `_preflight_enrichment()` 안전 초기화 5개 + 테스트 4개 | +97/-0 |
| **4-R3-h** | `38a5ab5` | `_preflight_validation()` REJECT-path 단위테스트 7건 | +211/-0 |

**결과**: `_compute_preflight()` 1,763줄 → 100줄 (94% 축소), 7개 서브메서드 추출, ctx refs 348/43 불변
**R3-g 보강**: FourPhase 미사용/예외/REJECT 경로에서 `NameError` 방지
**R3-h 보강**: DraftValidator/Consensus/FlowGuard/DuplicateGuard/ContinuityInspector REJECT + enriched_block 무효 + proceed 키 회귀
**테스트 기준선**: unit 29 + pipeline 89 + E2E 22 + regression 78 = **218 passed**
**잔여 미커버**: ArcCorrector nested branch, SelfReflector mutation path, Consensus exception path

### Phase 4-R4: async/sync 통일 (선택적)

| 커밋 | 작업 |
|------|------|
| **4-R4-a** | `_compute_preflight` 내 ThreadPoolExecutor → `asyncio.to_thread` 전환 |
| **4-R4-b** | stage2 진입점 async 호출 체인 정리 |

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
