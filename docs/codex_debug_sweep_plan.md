# Codex 디버깅 전면 스윕 플랜

> 작성: 2026-02-16
> 대상: 리팩토링(B-1/R1-R3/4C/A-1~E-2) 이후 전체 코드베이스
> 전략: 10개 카테고리 순차 스윕, 각 카테고리를 독립 Codex 오더로 실행
> 안전망: 1,656 passed + 68 xfailed (전체 그린 스위트)

---

## 스캔 결과 총괄

| # | 카테고리 | 발견 건수 | 심각도 |
|---|---------|----------|--------|
| A | 콜백 배선 누락 | 1건 | CRITICAL |
| B | 캐시 무효화 갭 | 1건 | HIGH |
| C | Silent Swallow (예외 삼킴) | 6건 | HIGH |
| D | 스레드 안전성 | 3건 (CRITICAL 2 + HIGH 1) | CRITICAL |
| E | DI 잔류 (self.app) | 99건 (Stage3: 96, Stage2: 2, Stage4: 1) | MEDIUM |
| F | DB 스키마 | 1건 (중복 정의) | LOW |
| G | YAML 설정 | 0건 | CLEAN |
| H | 데드 코드 | 0건 | CLEAN |
| I | 테스트 mock 정합성 | 0건 | CLEAN |
| J | Protocol 적합성 | 0건 | CLEAN |

---

## 카테고리 A: 콜백 배선 누락 (1건)

### A-1: Stage4Context `quality_dashboard` 누락

**심각도**: CRITICAL — 3-QR 품질 회귀 감지가 런타임에 죽을 수 있음

**파일**: `main_a.py` L2771~2795 (Stage4Context 수동 초기화 블록)

**현상**: `Stage4Context.from_app()`에는 `quality_dashboard` 매핑이 있으나,
L2771의 수동 초기화에는 빠져 있음. `stage4_post_processor.py:413`에서
`self.ctx.quality_dashboard.detect_score_regression(stage=2)` 호출 시 AttributeError.

**수정**:
```python
# main_a.py L2786 (selected_genre= 다음 줄)
quality_dashboard=getattr(self, "quality_dashboard", None),
```

**검증**: `pytest tests/test_stage4_post_processor.py tests/test_quality_regression.py -v`

---

## 카테고리 B: 캐시 무효화 갭 (1건)

### B-1: `_item_timeline_cache` 롤백 미무효화

**심각도**: HIGH — 에피소드 롤백 후 삭제된 에피소드의 아이템 타임라인이 캐시에서 제공됨

**파일**: `main_a.py` — 롤백 핸들러 (`db.reset_after()` 호출부)

**현상**: `db_manager.reset_after(target_ep)` 호출 시:
- ✅ `_cumulative_bible_cache` 무효화됨 (db_manager.py L1147)
- ✅ `_narrative_summaries_cache` — 확인 필요
- ❌ `_prompt_builder._item_timeline_cache` — **무효화 없음**

**수정**: `reset_after()` 호출 직후에 추가:
```python
self._prompt_builder._item_timeline_cache = {}
```

**검증**: `pytest tests/test_prompt_builder.py tests/test_rollback*.py -v`

---

## 카테고리 C: Silent Swallow (6건)

**심각도**: HIGH — DB 읽기 실패가 완전히 묻혀 디버깅 불가

E-1(Silent Pass 보강)과 동일 패턴. `except Exception: pass` → `except Exception: logging.warning(...)`

| # | 파일 | 라인 | 메서드 | 내용 |
|---|------|------|--------|------|
| C-1 | `modules/validation/retrospective_validator.py` | 266 | `_get_past_realms` | 과거 경지 DB 읽기 실패 |
| C-2 | `modules/validation/retrospective_validator.py` | 287 | `_get_past_items` | 과거 장비 DB 읽기 실패 |
| C-3 | `modules/validation/retrospective_validator.py` | 339 | `_get_resolved_conflicts` | 해결된 갈등 DB 읽기 실패 |
| C-4 | `modules/core/stage4_post_processor.py` | 385 | (bible_delta) | FactLedger 갱신 실패 (코멘트는 있으나 logging 없음) |
| C-5 | `main_a.py` | 2696 | (volume summary) | 상위 요약 로드 실패 |
| C-6 | `tests/test_integrity.py` | 92, 96 | (teardown) | 테스트 정리 bare except (LOW) |

**수정 패턴**:
```python
# Before
except Exception:
    pass

# After
except Exception:
    logging.warning("[카테고리] 설명: %s", e)  # 또는 pass 유지 + logging 추가
```

**검증**: `pytest tests/ -q` 전체 회귀

---

## 카테고리 D: 스레드 안전성 (3건)

### D-1: block_enricher 리스트/딕셔너리 레이스 (CRITICAL)

**파일**: `modules/domain/agents/block_enricher.py` L616~632, L667~679

**현상**: ThreadPoolExecutor 내에서 `enriched_blocks[idx] = result` 및
`stats["enriched_count"] += 1`을 락 없이 다중 스레드에서 쓰기.

**영향**: 데이터 손실, 카운터 부정확

**수정**: 리스트 인덱스 쓰기는 CPython GIL로 원자적이긴 하나,
`stats` 딕셔너리 += 연산은 원자적이지 않음. `threading.Lock()` 추가 또는
`collections.Counter`/`atomic` 패턴 도입.

### D-2: batch_validator stats 레이스 (HIGH)

**파일**: `modules/validation/batch_validator.py` L104~107

**현상**: `self.stats["completed"] += 1` / `self.stats["failed"] += 1` 레이스

**수정**: D-1과 동일 패턴 — Lock 도입

### D-3: stage2_preflight perf_timer 레이스 (HIGH)

**파일**: `modules/core/stage2_preflight.py` L99~103

**현상**: 2개 워커가 `perf_timer` 딕셔너리에 동시 쓰기

**수정**: perf_timer가 메트릭 수집용이라 정밀도가 덜 중요하지만,
dict 키 충돌 시 KeyError 가능. Lock 추가 권장.

**검증**: 기존 테스트로 스레드 버그 잡기 어려움 — 단위 테스트에서 Lock 존재 확인 + 전체 회귀

---

## 카테고리 E: DI 잔류 — self.app 직접 접근 (99건)

### E-1: Stage3 DI 전면 마이그레이션 (96건, LARGE)

**파일**: `modules/core/stage3_orchestrator.py`

**현상**: `app = self.app` 로컬 변수 패턴으로 96곳에서 직접 접근.
Stage3Context는 슬롯 3개(ui, current_project, get_protagonist_name)뿐.

**필요 추가 슬롯**:
- 속성 7개: `agents`, `sys`, `state_tracker`, `world_state`, `fact_ledger`, `preset_registry`, `selected_genre`
- 콜백 9개: `audit_event`, `write_audit_summary`, `get_arc_context_for_episode`,
  `get_max_episode_from_manuscripts`, `get_int_input`, `safe_commit`,
  `validate_arc_data_fields`, `validate_blueprint_integrity`, `fix_entity_registry_protagonist`

**작업**: Phase 4C 표준 패턴 적용 (Stage2Context 확장과 동일)

**규모**: stage3_context.py 확장 + stage3_orchestrator.py 전면 치환 + main_a.py from_app 주입

### E-2: Stage2 잔류 2건 (SMALL)

| 라인 | 현재 | 수정 |
|------|------|------|
| L154 | `getattr(self.app, "_state_tracker_loaded_arcs", 0)` | `self.ctx.state_tracker_loaded_arcs` |
| L597 | `getattr(self.app, "state_tracker", None)` | `self.ctx.state_tracker` (존재 확인 후) |

### E-3: Stage4 잔류 1건 (SMALL)

| 라인 | 현재 | 수정 |
|------|------|------|
| L422 | `getattr(self.app, "pacing_analyzer", None)` | Stage4Context에 슬롯 추가 후 전환 |

**검증**: `pytest tests/ -q` 전체 회귀

---

## 카테고리 F: DB 스키마 (1건)

### F-1: reflexion_memory 테이블 중복 정의

**파일**: `modules/core/db_manager.py` L164 / L302

**현상**: 같은 테이블이 두 번 CREATE TABLE IF NOT EXISTS됨.
L164는 TIMESTAMP, L302는 TEXT. SQLite는 첫 번째만 실행하므로 실동작에 영향 없으나,
의도와 코드가 불일치.

**수정**: L302의 중복 정의 제거하고, 실제 사용하는 타입(TEXT)으로 L164를 통일.

**검증**: `pytest tests/test_db_manager.py -v`

---

## 카테고리 G~J: 이상 없음 (CLEAN)

| 카테고리 | 스캔 결과 |
|---------|----------|
| G. YAML 설정 | 장르 10/10, 프롬프트 43개, validation.yaml 키 전량 매칭 |
| H. 데드 코드 | 8개 서브모듈 전수 검사 — 0건 |
| I. 테스트 mock | B-1 이후 전량 갱신됨, xfail 68건 전부 B-1 이전 이슈 |
| J. Protocol | 9개 테스트 통과, 비적합 에이전트는 의도적 문서화됨 |

---

## 실행 순서

```
Phase 1: 실제 버그 (A + B + C)         ← ✅ 완료 (8dc154f)
Phase 2: 스레드 안전성 (D)              ← ✅ 완료 (b649418) — D-1/D-3 오탐, D-2만 실제 수정
Phase 3+4: DI 위생 + DB 스키마          ← ✅ 완료 (5e1b6e9) — E-2ab + E-3 + F-1 + 테스트 보정 1건
Phase 5a: Stage3Context 확장 (E-1a)       ← ✅ 완료 (14d737f) — 3→19 슬롯, from_app 매핑
Phase 5b: Stage3 DI 전면 전환 (E-1b)      ← ✅ 완료 (883f438) — 84 refs → self.ctx, lazy init sync
```

### Phase 1~4 커밋 메시지 (예시)

```
fix(debug-sweep): patch callback wiring, cache invalidation, silent swallows

- A-1: add quality_dashboard to Stage4Context manual init
- B-1: clear _item_timeline_cache on rollback
- C-1~5: add logging.warning to 5 silent except blocks
- D-1~3: add threading.Lock to block_enricher, batch_validator, preflight timer
- E-2/3: replace 3 residual self.app with self.ctx
- F-1: deduplicate reflexion_memory CREATE TABLE
```

---

## 검증 게이트 (모든 Phase 공통)

1. `py_compile` 변경 파일
2. `python -m pytest tests/ -q` → 1,659 passed, 68 xfailed
3. `pre-commit run --files <변경파일>`
4. 수동 확인: 스레드 Lock이 실제 concurrent 경로에 걸리는지

---

## Phase 5 (E-1) 상세 — Stage3 DI 마이그레이션 ✅ 완료

### Phase 5a (`14d737f`): Stage3Context 확장
- `stage3_context.py` — `__slots__` 3개 → 19개 (필수 2 + 속성 7 + 콜백 10)
- `from_app()` 매핑 19종 추가
- 테스트 2개 추가 (`test_from_app_all_slots`, `test_slots_count_19`)

### Phase 5b (`883f438`): Stage3Orchestrator 전면 전환
- 전환 대상 6메서드: `app = self.app` → `ctx = self.ctx`, `app.xxx` 84건 → `ctx.xxx`
- Lazy init 3메서드(`_init_*_if_needed`): `self.app` 유지 (write-back 필요)
- `stage_3_batch_blueprinting()`: lazy init 직후 ctx sync 3줄 추가
- E2E smoke test: `Stage3Context(...)` → `Stage3Context.from_app(app)` 전환
- 테스트 1개 추가 (`test_ctx_sync_after_lazy_init`)
- 최종: 1,659 passed, 68 xfailed
