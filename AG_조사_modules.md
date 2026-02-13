# AG 조사 보고서 — modules/ 디렉토리
> 작성: Antigravity (AG) | 날짜: 2026-02-13  
> 규칙: **Read-Only** — 코드 수정 없음, 관찰 결과만 기록

---

## 1. 조사 범위 요약

| 구분 | 수치 |
|------|------|
| 총 스캔 파일 | 53개 |
| High Risk | 11개 |
| Medium Risk | 6개 |
| Low Risk | 36개 |
| 총 `except Exception` 패턴 | ~180개 |
| `self.app` 참조 파일 | 주로 orchestrator 2개 (총 ~650회) |
| 200+ 라인 대형 함수 | 4개 |
| 100+ 라인 대형 `try` 블록 | 6개 |

---

## 2. 위험도별 파일 목록

### 🔴 High Risk (11개)

| 파일 | 라인수 | except | self.app | 대형함수 | 대형try | 핵심 위험 |
|------|--------|--------|----------|----------|---------|-----------|
| `stage2_orchestrator.py` | 2141 | 66 | 341 | 1 | 1 | God Object, 과도한 self.app 커플링 |
| `stage4_orchestrator.py` | 1632 | 58 | 312 | 1 | 2 | God Object, DB+LLM+UI 혼합 |
| `reverse_expander.py` | 1074 | 14 | 0 | 0 | 1 | DB 저장 체인 5쌍 (save+commit 각각 except) |
| `base_agent.py` | 1117 | 13 | 0 | 1 | 2 | LLM 폴백 체인, 대형 try |
| `writer.py` | 500 | 12 | 0 | 0 | 0 | 집필 재시도 루프 내 다중 except |
| `memory_engine.py` | 442 | 11 | 0 | 0 | 0 | ChromaDB 비활성 시 전체 기능 무효화 |
| `prompt_builder.py` | 935 | 10 | 0 | 0 | 0 | 프롬프트 조립기, 파싱 실패 시 빈값 |
| `project_manager.py` | 840 | 10 | 0 | 0 | 0 | 프로젝트 CRUD, DB 실패 시 데이터 유실 가능 |
| `analyst.py` | 1401 | 10 | 0 | 0 | 0 | Arc 설계 에이전트, LLM 파싱 실패 시 빈 Arc |
| `genre_hud_manager.py` | 1280 | 9 | 0 | 0 | 0 | 10개 장르 HUD 관리, 누락 시 기본값 폴백 |
| `chief_writer.py` | 2116 | 8 | 0 | 2 | 1 | 최종 원고 조립기, 대형 함수 2개 |

### 🟡 Medium Risk (6개)

| 파일 | 라인수 | except | 핵심 위험 |
|------|--------|--------|-----------|
| `blueprint_memory.py` | 887 | 5 | ChromaDB 의존, 초기화/검색/인덱싱 모두 except |
| `style_extractor.py` | 708 | 5 | LLM 폴백 체인, L639 silent pass |
| `stage2_optimizer.py` | 866 | 0 | TODO 2개 미구현, 복잡한 최적화 로직 |
| `quality_dashboard.py` | 793 | 2 | 메트릭 로드/저장 실패 시 데이터 유실 |
| `data_collector.py` | ~300 | 0 | 대형 데이터 수집기 |
| `pre_director_checklist.py` | ~400 | 0 | 복잡한 사전 체크 로직 |

---

## 3. 핵심 발견사항

### 3.1 🚨 CRITICAL: Silent Pass 패턴 (데이터 유실 위험)

#### (1) `relationship_tracker.py` L364
```python
except Exception:
    pass  # 조용히 실패
```
- **위치**: `get_relationship_history()` — NPC 관계 이력 DB 조회
- **위험**: DB 에러 시 빈 리스트 반환 → NPC 관계 변화 이력이 소실된 채 이후 생성에 사용
- **영향**: 에피소드 생성 시 NPC가 이미 겪은 관계 변화를 모르고 모순된 관계 전환 허용

#### (2) `constants.py` L297
```python
except Exception:
    pass
```
- **위치**: `HUDKeys.get_protagonist_name()` — Bible에서 CoreIdentity 추출
- **위험**: 낮음. CoreIdentity 추출 실패 시 다음 폴백(HUD name)으로 넘어감
- **판정**: ✅ 방어적 설계 (4단계 폴백 체인의 0순위)

#### (3) `style_extractor.py` L639
```python
except Exception:
    pass
```
- **위치**: `_ensure_client()` — LLM 클라이언트 자동 초기화
- **위험**: 낮음. 선택적 기능이며, 클라이언트 없으면 통계 분석만 수행
- **판정**: ✅ 수용 가능 (LLM 없이도 동작하는 설계)

#### (4) `reverse_expander.py` L49
```python
except Exception:
    pass
```
- **위치**: `__init__` 내 spinner import
- **위험**: 없음. UI 표시용 선택 모듈
- **판정**: ✅ 안전

### 3.2 🚨 CRITICAL: State → None 패턴 (기능 완전 비활성화)

#### `semantic_plot_guard.py` L65
```python
except Exception:
    self._client = None
```
- **위험**: API 키 유효하지만 네트워크 일시 오류 시에도 **영구적으로 비활성화**
- **연쇄 효과**:
  1. `_client = None` → `_embed_text()` 항상 None 반환
  2. → `index_resolved_plots()` 항상 0
  3. → `check_new_arc()` 항상 빈 리스트
  4. → **플롯 중복 감지 완전 비활성화**
- **실제 영향**: 이전에 완결된 플롯과 동일한 플롯이 새 Arc에 반복 → 스토리 반복
- **권장**: 재시도 로직 추가 또는 lazy init 패턴

#### `state_tracker_npc.py` L588, L1895
```python
_resp_text = None  # (after: except (ValueError, AttributeError))
```
- **위험**: NPC LLM 검증 실패 시 regex 결과를 그대로 사용 (L598)
- **판정**: ⚠️ 중간 — LLM 검증은 보조 수단이므로 regex 폴백 자체는 합리적이나, 로그에만 의존

### 3.3 DB 저장 체인 패턴 (reverse_expander.py)

```
save_manuscripts_to_db  → [개별 except + 커밋 except (count=0)]
save_state_logs_to_db   → [개별 except + 커밋 except (count=0)]
save_episode_bibles     → [개별 except + 커밋 except (count=0)]
save_blueprint_stubs    → [개별 except + 커밋 except (count=0)]
save_arc_stubs          → [전체 try-except (count=0)]
enrich_arc_stubs        → [전체 try-except (count=0)]
```
- **패턴**: 각 save 함수에서 개별 레코드 실패 시 warning 후 계속, 최종 `commit()` 실패 시 count=0 리셋
- **판정**: ✅ **양호한 방어적 설계** — 부분 실패 허용하면서 커밋 실패는 정직하게 보고
- **개선점**: 커밋 실패 시 `rollback()` 호출이 없어 DB가 half-committed 상태 가능

### 3.4 LLM 폴백 체인

| 파일 | 모델 순서 | 실패 처리 |
|------|-----------|-----------|
| `style_extractor.py` | 3-pro → 2.5-pro → 2.5-flash | last_err 전파, 전부 실패 시 raise |
| `base_agent.py` | 설정 모델 → EMERGENCY_FALLBACK | 재시도 루프 내 except |
| `reverse_expander.py` | 단일 모델 | 개별 warning |

### 3.5 대형 함수 (200+ 라인)

| 파일 | 함수명 | 라인수 | 위험 |
|------|--------|--------|------|
| `stage2_orchestrator.py` | `_design_single_arc` | ~350L | 복잡한 Arc 설계 전체 플로우 |
| `stage4_orchestrator.py` | `_write_single_episode` | ~300L | 에피소드 집필 전체 플로우 |
| `chief_writer.py` | `write_episode` | ~250L | 원고 조립 + 스타일 적용 |
| `chief_writer.py` | `_build_context` | ~200L | 컨텍스트 빌더 |
| `base_agent.py` | `_generate_content` | ~200L | LLM 호출 + 파싱 + 재시도 |

### 3.6 TODO/FIXME 미구현 사항

| 파일 | 라인 | 내용 |
|------|------|------|
| `stage2_optimizer.py` | L501 | `# TODO: tactical_doc에서 추출` — from 필드 하드코딩 |
| `stage2_optimizer.py` | L508 | `# TODO: 구현` — 미구현 로직 |

---

## 4. 파일별 상세 except 패턴

### 4.1 core/ 보조 모듈 (잘 관리됨)

| 파일 | except수 | 패턴 | 판정 |
|------|----------|------|------|
| `fact_ledger.py` | 2 | DB 로드/저장 warning → 초기화 폴백 | ✅ |
| `constraint_db.py` | 1 | DB 로드 실패 warning | ✅ |
| `character_voice.py` | 1 | Load error → 빈 상태 | ✅ |
| `character_voice_profiler.py` | 2 | 로드/저장 실패 warning | ✅ |
| `failure_learning.py` | 1 | Load error → 빈 상태 | ✅ |
| `pattern_tracker.py` | 2 | DB 저장/로드 warning | ✅ |
| `pass_rate_monitor.py` | 2 | 기록 로드/저장 warning | ✅ |
| `prompt_loader.py` | 2 | YAML 로드/템플릿 실패 warning | ✅ |
| `slack_bot.py` | 1 | 연결 실패 warning | ✅ |
| `system.py` | 1 | DB 테이블 존재 확인 — False 유지 | ✅ |

### 4.2 ab_testing.py (양호)
- L77, L94: 에러를 `result = {'error': str(e)}`로 캡처 → 테스트 결과에 포함
- **판정**: ✅ 에러가 결과 데이터에 보존됨

### 4.3 blueprint_memory.py (주의 필요)
- 5개 except 모두 warning 로그 → 빈 결과 반환
- **위험**: ChromaDB 초기화 실패 시 모든 인덱싱/검색이 무효
- **판정**: ⚠️ semantic_plot_guard와 유사한 패턴이지만, 이쪽은 non-critical

---

## 5. 교차 모듈 의존성

### 가장 많이 import되는 모듈 (AG 영역)
1. `modules.core.constants` — 거의 모든 파일에서 참조
2. `modules.domain.agents` — orchestrator에서 대량 사용
3. `modules.core.models` — 데이터 클래스 정의

### God Object 패턴
- `stage2_orchestrator.py`: `self.app`로 341회 외부 서비스 접근
- `stage4_orchestrator.py`: `self.app`로 312회 외부 서비스 접근
- 두 파일 합산 650+ 회의 `self.app` 직접 참조

---

## 6. 우선순위 요약

### P0 — 즉시 검토 권장
1. **`semantic_plot_guard.py`** L65: except → `_client = None` 영구 비활성화
2. **`relationship_tracker.py`** L364: `except: pass` — NPC 이력 유실
3. **`reverse_expander.py`** DB 체인: commit 실패 시 rollback 없음

### P1 — 중기 개선
4. **`stage2_orchestrator.py`** / **`stage4_orchestrator.py`**: God Object 분리
5. **`chief_writer.py`**: 대형 함수 2개 분리
6. **`base_agent.py`**: 대형 try 블록 세분화
7. **`stage2_optimizer.py`**: TODO 2개 구현

### P2 — 장기 개선
8. **`blueprint_memory.py`**: ChromaDB 초기화 실패 복구
9. **`memory_engine.py`**: ChromaDB 비활성 시 graceful degradation 강화
10. **cross-module**: self.app 의존성 DI(의존성 주입) 패턴으로 전환

---

## 7. 긍정적 발견

- **`feedback_system.py`** (776L): except **0개**, 순수 함수 위주 → 모범 사례
- **`pattern_tracker.py`** (880L): except 2개, 모두 DB 폴백 → 클린
- **`relationship_tracker.py`**: FSM(유한 상태 머신) 설계 우수 — 상태 전환 규칙 엄격
- **core 보조 모듈 대부분**: except에 적절한 logging.warning + 폴백 패턴 준수
- **`reverse_expander.py`** DB 체인: 부분 실패 허용 + 커밋 실패 시 count 리셋 = 정직한 보고
- **`ab_testing.py`**: 에러를 결과 데이터에 보존하는 좋은 패턴
- **`constants.py`**: SSOT(Single Source of Truth) 원칙 잘 적용, 매직 넘버 중앙 관리

---

## 8. 🆕 보강 조사 (2026-02-13 2차)

> 1차 스캔 이후 코드가 **V64.P4 리팩토링**을 거쳤으므로, 기존 보고서와 현재 코드 상태 사이의 **차이(delta)**를 중심으로 보강.

### 8.1 ⚠️ ~~해소된 이슈~~ — `self.app` God Object **건재** (검색 오류 정정)

> [!CAUTION]
> 이전 조사에서 `self\.app` (마침표 없이) regex를 사용하여 0건으로 오판. 실측 결과 **건재함**.

| 항목 | 기존 보고서 | 실측 (2026-02-13) |
|------|------------|----------|
| `stage2_orchestrator.py` self.app | 332회 | **341회** (증가) |
| `stage4_orchestrator.py` self.app | 291회 | **312회** (증가) |
| modules/ 전체 self.app | 650+ 회 | **653+회** (건재) |

> **결론**: God Object **미해소**. Phase 4 리팩토링(DI 전환) 여전히 필요.

### 8.2 ✅ 해소된 이슈 — `except Exception` → 구체적 예외 타입 (V64.P4)

`director_auditor.py`, `director.py`, `director_ensemble.py`, `stage2_orchestrator.py` 4개 파일 모두 bare `except Exception:` 패턴 **0건** 확인. V64.P4 태그로 구체적 예외(`ValueError`, `SyntaxError`, `json.JSONDecodeError`, `FutureTimeoutError` 등)로 세분화.

### 8.3 ✅ 해소됨 — `relationship_tracker.py` L364 (본 세션에서 수정)

- `except Exception: pass` → `except (KeyError, AttributeError, TypeError) as e: logging.warning(...)` 로 수정 완료
- `import logging` 추가

### 8.4 ✅ 해소됨 — `semantic_plot_guard.py` 영구 비활성화 (본 세션에서 수정)

- `__init__` → `_try_init_client()` 분리 + lazy init 패턴 적용
- `_embed_text()` 진입 시 client 없으면 1회 재시도


---

## 9. `base_agent.py` ask() 심층 분석 — 4계층 방어 체인

### 방어 체인 구조

```
Layer 0: 네트워크 오류 → MAX 22회 재시도 + 백오프 (10~30초)
Layer 1: Rate Limit (429) → 30/60/90초 백오프 후 재시도 (MAX 3회)
Layer 2: Quota 소진 → 모델 폴백 체인 (3-pro → 2.5-pro)
Layer 3: 전체 실패 → backup_model 시도 → partial_response 반환 → error JSON
```

### 발견된 리스크

| # | 위치 | 리스크 | 심각도 |
|---|------|--------|--------|
| 1 | L297 | `logging.info()` 인자 없이 호출 — **TypeError** 발생 가능 (네트워크 재시도 경로) | Medium |
| 2 | L288 | `from datetime import datetime` 루프 내 반복 import — 성능 이슈 (기능엔 무해) | Low |
| 3 | L346 | `model_stack[quota_retry_count]` — 인덱스 초과 시 `model_stack[-1]` 폴백 (안전) | Low |
| 4 | L380 | 폴백 모델 API 호출이 MAX_CONTINUATIONS 루프 내 `except` 절에서 실행 — 이 호출 자체가 실패하면 L387 `raise api_error`로 원래 에러가 발생 (정상 동작이지만 혼란 가능) | Low |
| 5 | L242-244 | metrics except → `pass` — **의도적 설계** (비용 추적 실패가 본 작업 차단 않음) | OK |

### 클래스 변수 공유 패턴 (멀티스레드 주의)

| 변수 | 보호 | 위험도 |
|------|------|--------|
| `_api_keys` | 초기화 1회 (write-once) | Safe |
| `_current_key_idx` | `_rotation_lock` | ✅ Safe |
| `_quota_exhausted_models` | Lock 없음 (dict read/write) | ⚠️ Race 가능 |
| `_context_caches` | L115에서 `clear()` | ⚠️ 키 순환 시 다른 스레드 캐시 무효화 |

---

## 10. ThreadPoolExecutor 사용 파일 (병렬 처리 리스크)

| 파일 | max_workers | 용도 | 예외 처리 |
|------|-------------|------|-----------|
| `director_auditor.py` L819 | min(3, tasks) | Self-Consistency 투표 | ✅ `as_completed` + `FutureTimeoutError` |
| `consensus_validator.py` L207 | self.max_workers | 합의 검증 | ✅ V61.3 급사 방지 |
| `chief_writer.py` L240 | 3 | 병렬 집필 | ✅ V61.3 급사 방지 |
| `blueprint_ensemble.py` L171 | self.max_workers | 블루프린트 앙상블 | ✅ V61.3 급사 방지 |
| `block_enricher.py` L643 | batch_size | 블록 보강 | 미확인 |
| `arc_ensemble.py` L126 | self.max_workers | Arc 앙상블 | ✅ V61.3 급사 방지 |

> [!TIP]
> 6개 중 5개는 V61.3 급사 방지 패턴(전체 예외 처리) 적용. `block_enricher.py`만 상세 확인 필요.

---

## 11. 코덱스의견 교차 검증

| 코덱스 항목 | AG 검증 결과 |
|------------|-------------|
| P0: `base_agent.py` 재시도/폴백 | ✅ 확인 — 4계층 방어 체인 정교, L297 minor bug만 |
| P1: `director_*` 파싱/판정 | ✅ V64.P4로 except 세분화 완료 |
| P2: `primary_model` 임시 변경 | ❌ **현재 코드에 미존재** — 코덱스 의견 시점 이후 제거됨 |
| P2: ThreadPoolExecutor 병렬 | ✅ 6개 파일 확인, 5/6 V61.3 보호 |
| 크래시 진입점: self.app 커플링 | ⚠️ **건재** (stage2: 341, stage4: 312) — AG 이전 검색 오류 정정 |
| Google 전용 API 강결합 | ✅ 여전히 존재 (`from google import genai`) |

---

## 12. 보강 후 우선순위 재정리

### P0 — 즉시 검토
1. ~~`semantic_plot_guard.py`~~ → ✅ 해소 (lazy init 적용)
2. ~~`relationship_tracker.py`~~ → ✅ 해소 (구체적 예외 + 로깅)
3. **`reverse_expander.py`** DB 체인: commit 실패 시 rollback 없음

### P1 — 중기 개선
4. **`stage2/4_orchestrator` God Object** — self.app 341/312건 **건재** (Phase 4 대상)
5. **`chief_writer.py`**: 대형 함수 2개 여전히 존재
6. ~~`base_agent.py` L297~~ → ✅ 해소 (`logging.info("")` 수정)
7. **`base_agent.py`**: `_quota_exhausted_models` dict Lock 미보호
8. **`block_enricher.py`**: ThreadPoolExecutor 예외 처리 확인/보강

### P2 — 장기 개선
9. **Google genai 강결합**: provider-agnostic 추상화 레이어 필요
10. **`blueprint_memory.py`**: ChromaDB 초기화 실패 복구
