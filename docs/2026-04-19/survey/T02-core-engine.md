# T02: modules/core/ 핵심 엔진 심층 조사

Surveyor: Claude Code (Terminal 2)
Date: 2026-04-19
Scope: `modules/core/` 196 Python 파일(166 root + 30 subdir, ~127K LOC)의 책임/패턴/품질/결합도 정밀 진단

## 1. Executive Summary

- **성숙도 판정: Pre-production (상)**
- 핵심 엔진은 **타입 디스크라인·스레드 안전성·DB 추상화·상속 계층**에서 견고한 인프라(0 bare-except, RLock 보호된 단일 DBManager, BaseGuard/GenreHUDManager 추상화)를 갖춘 반면, **Stage4의 18-파일·29,695 LOC 분산, 161건의 무로깅 except Exception, V24 시대 wuxia 잔재 모듈**이 정합성·운영 가시성·청결도를 끌어내린다. 운영 안정성은 입증되었으나 모듈 분해·계약 타입화·잔재 정리가 production-ready 진입의 마지막 길목이다.

## 2. 강점 (Strengths)

- **Bare except 완전 제거**: 0건. (`grep -rE "except\s*:" modules/core` 결과 0). MEMORY.md의 "~68 bare except 잔존"은 modules/core 외부 잔재이며, 이 디렉토리는 정화 완료 상태.
- **DB 단일 진입점 + 커스텀 예외 계층**: `modules/core/db_manager.py:17-48`에서 `DBError → DBIntegrityError/DBConnectionError/DBTransactionError` 4계층 + 심각도 enum(CRITICAL/HIGH/WARN). 전 코드베이스 516 참조가 이 게이트로 모임.
- **스레드 안전성 일관**: DBManager `_lock = threading.RLock()` (`db_manager.py:87`) 보호된 `with self._lock:` 블록 112개. 단일-스레드 설계 모듈은 `fact_ledger.py:177`, `failure_analyzer.py:463`처럼 **명시적 주석으로 의도 선언**.
- **장르 추상화 — 깔끔한 Strategy/Template Method**: `BaseGuard(ABC)` ← 12 genre guard 상속, `GenreHUDManager(ABC)` ← 9 genre HUD 매니저 상속. `genre_guards/__init__.py:22 create_genre_guard()`, `genre_hud_manager.py:640 create_hud_manager()` 두 팩토리로 진입점 일원화.
- **LLM Provider 추상화**: `modules/core/llm_provider.py:36 class LLMProvider(Protocol)` + `providers/{anthropic,anthropic_vertex,gemini,openai,vertex}_provider.py` 5종. `llm_router.py:12-16`에서 명시적 dispatch — 신규 provider 추가 비용 낮음.
- **타입 힌트 커버리지 ~69%**: 3782 함수 중 2620개가 `-> ReturnType` 보유. dataclass 57파일 사용.
- **Migration 멱등성**: `db_bootstrap_runtime.py:140-142, 293-295`처럼 `ALTER TABLE ... ADD COLUMN` 후 `except sqlite3.OperationalError: pass` — 재실행 안전.
- **TODO/FIXME 5건만**: 127K LOC 대비 0.004% — 적극적 부채 정리 흔적.
- **stdout 오염 거의 없음**: `print()` 사용 모듈 1개(8건)뿐. 로깅 표준화됨.

## 3. 개선 필수 (Critical Issues) — P0

### P0-1. `stage4_interview_round.py` 8,193 LOC 단일 파일 — 책임 과적
- **파일**: `modules/core/stage4_interview_round.py`
- **수치**: 8193 LOC, 11 클래스, 22 top-level 함수. modules/core 전체 1위.
- **영향**: 단일 파일 변경 위험, 리뷰 불가능, 테스트 격리 불가, 메모리 캐싱 효율 저하.
- **권장**: round-controller / question-generator / response-collector / scoring / persistence 5–7 모듈로 강제 분해. 분해 우선순위 1순위.

### P0-2. `stage4_*` 18 파일 29,695 LOC — 파이프라인 단일 단계가 modules/core의 23%를 차지
- **파일군**: `stage4_canary_tools.py`(2141) + `stage4_context_builder.py`(3388) + `stage4_director_runtime.py`(1559) + `stage4_interview_round.py`(8193) + `stage4_orchestrator.py`(2802) + `stage4_outcome_runtime.py`(1392) + `stage4_post_pass_runtime.py`(1965) + `stage4_post_processor.py`(1365) + `stage4_postselect_runtime.py`(803) + `stage4_reject_runtime.py`(1952) + `stage4_retry_runtime.py`(1503) + 7 보조파일.
- **영향**: 명명 충돌 위험(`post_pass_runtime` vs `post_processor` vs `postselect_runtime` 의미 분간 어려움), 의존 그래프 탐색 비용 증가, Stage 진입점 불명확.
- **권장**: `modules/core/stage4/` 서브패키지로 격리하고 책임 영역(`runtime/`, `evaluation/`, `repair/`) 디렉토리로 분류. T07(Stage Pipeline 트랙)과 교차 검토 필요.

### P0-3. 무로깅 `except Exception` 161건 — 운영 가시성 침식
- **수치**: 105 파일에 걸쳐 `except Exception` 785건 발생, 그중 **다음 줄에 log/raise/warn 없음** 161건.
- **대표 핫스팟**: `stage4_context_builder.py`(47건), `stage3_orchestrator.py`(47), `stage4_interview_round.py`(45), `db_manager.py`(41), `stage2_preflight.py`(39).
- **영향**: 생산 환경에서 silent failure → 디버깅 불가. db_manager 일부는 rollback 보조 cleanup으로 정당하지만, orchestrator 계층의 silent 누락은 위험.
- **권장**: orchestrator/runtime 계층(stage{2,3,4}_orchestrator, stage{2,3,4}_*_runtime)부터 lint rule(`B902`/`broad-except`)로 강제. cleanup용은 `# noqa: BLE001` 주석으로 의도 명시.

### P0-4. Wuxia 레거시 thin shim — 다른 장르와 형평성 깨짐
- **파일**: `modules/core/technique_weaver.py:1-43` (42 LOC, 12 무공류 하드코딩 dict), `modules/core/jianghu_logic.py:1-26` (5 도시 ANCHORS 하드코딩), `modules/core/karma_service.py:1-25` (sect_relations 단일 호출).
- **트리거**: `modules/core/system.py:42-50` `if genre == "wuxia": from .jianghu_logic import...` — 9개 장르 중 wuxia 하나만 4개 모듈 추가 부팅.
- **영향**: 장르 패리티 위배(MEMORY.md 16-checkpoint 미적용), 신규 장르 추가 시 "wuxia만 특별취급" 패턴이 재발할 위험.
- **권장**: 3 모듈을 `lore_manager.py` 산하 wuxia 장르 plugin으로 흡수하거나, V62.x 이후 장르처럼 `genre_guards/` + 데이터 JSON 분리 패턴으로 통일.

### P0-5. 죽은 데이터 — `modules/core/laws/` 루트 4개 JSON 미참조
- **파일**: `modules/core/laws/hunter.json`, `wuxia.json`, `investment.json`, `common.json`. (확인: 코드 0건, 문서 0건 grep)
- **차이**: 같은 디렉토리 `laws/archetypes/{...}.json`(`state_service.py:154`에서 사용), `laws/seeds/*.json`(`state_service.py:292`에서 사용), `laws/primitive_forbidden.json`(`primitive_guard.py:39` 사용)은 살아있음.
- **영향**: 신규 contributor가 forbidden 어휘 추가 시 어느 파일을 수정할지 혼동(`forbidden`, `system_priority`, `genre_name` 키가 두 곳에 중복됨).
- **권장**: 4 파일 삭제 또는 `laws/_legacy/`로 이동. 단, 제거 전 git blame으로 마지막 참조 시점 확인.

## 4. 개선 권장 (Major Issues) — P1

### P1-1. `investment_arithmetic_checker.py` ↔ `investment_math_verifier.py` 명칭 중복
- **파일**: `modules/core/investment_arithmetic_checker.py:34 class InvestmentArithmeticChecker`, `modules/core/investment_math_verifier.py:34 class InvestmentMathVerifier`.
- **사용처**: 전자는 `arc_ensemble.py` + `four_phase_arc_runtime.py`, 후자는 `four_phase_arc_generator.py` + `four_phase_arc_runtime.py`. **`four_phase_arc_runtime.py`는 둘 다 사용**.
- **영향**: 장기적으로 동일 도메인 두 검증기가 미묘한 검증 결과 divergence를 유발할 위험.
- **권장**: 한 모듈로 통합하거나, `Checker(syntactic)` vs `Verifier(semantic)` 책임 차이를 모듈 docstring 1줄로 명시.

### P1-2. `pre_director_*.py` 4개 — 작은 책임 분산 vs SRP의 과잉
- **파일**: `pre_director_checklist.py`(766), `pre_director_manuscript_checker.py`(?), `pre_director_narrative_checker.py`(?), `pre_director_style_checker.py`(?).
- **영향**: 4 모듈이 같은 director 호출 직전 단계에서 호출됨. 일관성 보장 모듈이지만 진입 순서·우선순위가 코드 외부에 있어 추적 곤란.
- **권장**: `pre_director/` 서브패키지화 + `__init__.py`에서 `RUN_ORDER = [...]` 명시.

### P1-3. `modules/core/services/` — God-Object 추출 진행 중 (Phase 4B)
- **파일**: `services/__init__.py:1-7` 주석 "[Phase 4B] God Object 추출 서비스 모듈". audit/project/state/ui 4개 서비스만 추출됨.
- **영향**: 미완 리팩토링 흔적. 다른 책임은 여전히 main_a.py에 남았음(T01 트랙 영역).
- **권장**: T01 결과와 교차 참조하여 추가 추출 후보 식별. services 디렉토리에 `__init__.py` 외 5 파일뿐 → "Phase 4B" 진행률 ~25% 추정.

### P1-4. `audit_service.py` 직접 sqlite3 연결 — DB 추상화 우회
- **파일**: `modules/core/services/audit_service.py:24` `self.conn = sqlite3.connect(...)`.
- **영향**: `DBManager`의 RLock·예외 분류·트랜잭션 헬퍼 우회. 동시성 시나리오에서 lock contention 패턴 다양화.
- **권장**: `DBManager` 인스턴스 주입 또는 `DBManager`에 audit-전용 read-only 메서드 추가.

### P1-5. `vec_memory.py` 직접 sqlite3 + `check_same_thread=False`
- **파일**: `modules/core/vec_memory.py:75 self._conn: sqlite3.Connection | None = None`, `:123 sqlite3.connect(self._db_path, check_same_thread=False)`.
- **영향**: SQLite의 thread-safety guard 비활성화. lock 8개에 의존하지만 1개만 `with self._lock:` 형태(grep 결과 1건). race window 잔존 가능.
- **권장**: vec store는 별도 `VectorDBManager` 클래스로 격리하고 RLock 보호 패턴을 db_manager.py와 동일하게 적용.

### P1-6. `from __future__ import annotations` 일관성 결여 (56/166 = 34%)
- **영향**: Python 3.10+에서 `dict[str, Any]` vs `Dict[str, Any]` 혼용. forward-reference 평가 시점이 모듈마다 다름.
- **권장**: ruff `F` rule + `I001` 정렬과 함께 일괄 추가. PR 1건으로 해결 가능.

### P1-7. logger 사용 비율 25/166 모듈 — 중앙 집중 vs 분산 로깅의 모호함
- **수치**: `getLogger(__name__)` 사용 25 파일. 나머지는 `logging.info(...)` 모듈-레벨 호출 또는 `session_logger.py`/`logger.py` 헬퍼 경유.
- **영향**: 운영 환경에서 로그 namespace가 일관되지 않음 → log filtering 어려움.
- **권장**: 모든 핵심 모듈에 `logger = logging.getLogger(__name__)` 패턴 강제 (ruff custom rule).

### P1-8. TypedDict 3건 / pydantic 0건 — Stage 간 IO 계약이 dict로 흐름
- **영향**: dataclass는 57건 사용되지만 `dict[str, Any]` 핸드오프가 stage{2,3,4}_context_packets/builder 전반에 만연. JSON 스키마 검증 누락.
- **권장**: stage 경계(stage_cross_stage_contract.py 등)에 한해 pydantic v2 또는 TypedDict 강제. T04(API/Protocol) 트랙과 협업 필요.

### P1-9. `failure_analyzer.py` 4,102 LOC / 단일 클래스 / 10 함수
- **파일**: `modules/core/failure_analyzer.py`. cls=1, def=10 → 메서드 수는 적은데 파일은 거대 → 메서드 본문이 매우 길거나 모듈-레벨 헬퍼 다수.
- **영향**: 변경 영향 평가 곤란, 분석 알고리즘 격리 어려움.
- **권장**: 분석 카테고리(timeline/numeric/narrative/style)별 모듈 분리.

## 5. 개선 검토 (Minor Issues) — P2

- **P2-1. constants.py 28 클래스**: `modules/core/constants.py:1-893`에 28 클래스. enum 모음에 가까운 편의 묶음이지만 의미 그룹별(`hud_keys.py`, `genre_keys.py`, `metric_keys.py`) 분해 가능.
- **P2-2. tree_of_thoughts.py 752 LOC + ExplorationStrategy(Enum)**: V20 시대 ToT 패턴 — 실제 호출 빈도와 비용 대비 효과 재평가 필요.
- **P2-3. `world_state.py` 1512 LOC, 1 클래스, 5 def**: cls=1/def=5 비율은 거대한 메서드 본문 의심. 메서드별 LOC 측정 후 분해 후보 결정.
- **P2-4. `relationship_tracker_*.py` 3분할**: `relationship_tracker.py`(?), `_factions.py`(848), `_npc.py`(?). 적절한 SRP이지만 `relationship/` 패키지화로 가시성↑.
- **P2-5. `__pycache__` 디렉토리 git 추적 여부 확인**: `find` 결과 196 vs `*.py` 166 차이는 root + subdir 합산. `.gitignore`에 `__pycache__/` 누락 시 권장.
- **P2-6. `stage4_types.py` 91 LOC**: 타입 모음 모듈 — 다른 stage에도 동일 패턴 도입(`stage2_types.py`, `stage3_types.py`) 권장.
- **P2-7. 132건 `with self._lock:` vs 30 lock 생성자**: lock 1개당 평균 4.4 acquire — 합리적이지만 lock contention 프로파일링은 미실시.

## 6. 수치 지표 (Metrics)

| 항목 | 값 |
|------|----|
| Python 파일 (modules/core 전체) | 196 (root 166 + genre_guards 14 + providers 5 + services 5 + stage0 6) |
| 총 LOC | 126,709 |
| 평균 LOC/파일 | 646 |
| p50 / p75 / p90 / p95 LOC | 409 / 803 / 1365 / 1965 |
| ≥1000 LOC 파일 수 | 32 (16%) |
| Stage4 파일군 합계 | 18 파일, 29,695 LOC (23.4%) |
| Stage2 파일군 합계 | 10 파일, 12,929 LOC (10.2%) |
| Stage3 파일군 합계 | 5 파일, 3,961 LOC (3.1%) |
| 클래스 총수 (top-level) | ~270+ |
| 함수 총수 (def + async def) | 3,782 |
| 함수 중 return-type 어노테이션 | 2,620 (69.3%) |
| `from __future__ import annotations` 사용 모듈 | 56 / 166 (33.7%) |
| `@dataclass` 사용 모듈 | 57 |
| `TypedDict` 사용 모듈 | 3 |
| `pydantic` 사용 모듈 | 0 |
| `Protocol` 사용 모듈 | 3 (llm_provider, services/state_service, services/ui_service) |
| ABC 상속 계층 | 2 (BaseGuard, GenreHUDManager) |
| Enum 정의 모듈 | 10+ |
| Bare `except:` 건수 | **0** |
| `except Exception` 총 건수 | 785 (104 파일) |
| 그중 다음 줄 logging/raise 없음 | 161 |
| `except: pass` 침묵 패턴 | 89 (대부분 rollback/migration cleanup) |
| `raise` 문 (any) | 129 (24 파일) |
| `raise` 단독 재발생 | 15 |
| TODO/FIXME/XXX/HACK | 5 |
| `print()` 사용 | 1 파일 (8건) |
| `getLogger` 사용 | 25 파일 |
| threading.{Lock,RLock,...} 생성자 | 30 (20 파일) |
| `with self._lock:` 류 컨텍스트 | 132 |
| DBManager 직접 sqlite3 우회 | 3 (audit_service, vec_memory, modules/api/process_runner) |
| DBManager 참조 (repo 전체) | 516 |
| 정적 인덱스 기준 orphan 모듈 | 5 (모두 wuxia-only/transitive 사용으로 확인됨) |
| 죽은 JSON 데이터 | 4 (`laws/{hunter,wuxia,investment,common}.json`) |

## 7. 성숙도 근거 (Maturity Evidence)

**Production-ready 근거 (포지티브)**
- DB 단일 진입점 + 4계층 커스텀 예외 + RLock + transaction context manager → 데이터 무결성 인프라는 production-grade.
- 0 bare except, 0 NamedTuple 잔재, 5건 TODO만 → 적극적 부채 청소 흔적.
- BaseGuard/GenreHUDManager ABC 패턴, Provider Protocol → 9 장르 × 5 LLM provider 확장이 안정적.
- `stage_cross_stage_contract.py`, `cross_stage_authority_packet.py`, `partial_fix_contract.py` 등 **명시적 계약 모듈** 존재 → 운영 정합성 보장 의도가 코드에 반영됨.
- `_safe_commit` 회복(V61.7.1), threading.Lock for API key rotation(V61.7.1), MEMORY.md 기록 → 장기 운영 중 발견된 버그가 재발 방지 패턴으로 흡수됨.

**Pre-production 미달 요소 (네거티브)**
- Stage4 모듈 분산 23,000+ LOC가 단일 파이프라인 단계에 집중 → 변경 위험 매우 높음. Production은 단일 PR이 18 파일을 동시 수정하는 상황을 회피해야 함.
- 무로깅 `except Exception` 161건 → 생산 환경에서 silent failure ⇒ **운영 가시성 부족**, 이는 production의 핵심 요건 미충족.
- pydantic/TypedDict 부재 → stage 경계에서 dict 핸드오프 → IO 스키마 drift 위험.
- 4개 죽은 JSON, 3개 wuxia thin-shim → 신규 기여자 onboarding 비용 증가.

**판정**: 코어 인프라(DB/Lock/Provider/Guard)는 Production-ready 수준이지만, Stage4 거대화 + 161 silent except + IO 계약 타입화 결여로 **Pre-production (상)** 단계. T01(monolith) + T07(stage pipeline) 트랙 결과와 합산 시 종합 등급은 Pre-production로 수렴 예상.

## 8. 권장 로드맵 (Recommendations)

**즉시 (1–2 주)**
1. P0-3: orchestrator 계층(`stage{2,3,4}_orchestrator.py`)의 `except Exception` 161건 audit → 의도된 silent는 `# noqa: BLE001 — reason`, 나머지는 `logger.exception(...)` 추가.
2. P0-5: `laws/{hunter,wuxia,investment,common}.json` 삭제 PR (5분 작업).
3. P1-6: `from __future__ import annotations` 일괄 추가 PR (ruff auto-fix 가능).

**단기 (4–6 주)**
4. P0-1: `stage4_interview_round.py` 8193 LOC 분해 → `stage4/interview/{round_controller, question_generator, response_collector, scoring, persistence}.py`.
5. P0-2: `modules/core/stage4/` 서브패키지화. 18 파일을 `runtime/`, `evaluation/`, `repair/` 로 그룹화.
6. P1-4, P1-5: `audit_service.py`, `vec_memory.py` DB 접근을 DBManager 게이트로 통합.
7. P1-1: investment_arithmetic_checker ↔ investment_math_verifier 통합 또는 책임 명문화.

**중기 (2–3 개월)**
8. P0-4: wuxia thin-shim 3 모듈 → `lore_manager` 산하 plugin 또는 다른 장르와 동일 패턴으로 통일.
9. P1-8: `stage_cross_stage_contract.py` 등 stage 경계 IO를 pydantic v2 모델로 정의.
10. P1-3: `services/` Phase 4B 추출 완료(T01 트랙 결과와 협업).
11. P1-9: `failure_analyzer.py` 4102 LOC 분해(timeline/numeric/narrative/style).

**장기 (6 개월+)**
12. P2-1: `constants.py` 28 클래스 분해(`hud_keys.py`, `genre_keys.py`, `metric_keys.py`).
13. lock contention 프로파일링 후 RLock vs Lock 선택 재검토.
14. `getLogger(__name__)` 패턴 강제 → 모든 핵심 모듈 namespace 일관화.
