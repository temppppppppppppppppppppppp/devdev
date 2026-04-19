# T10: 보안 / 성능 / 운영 관점

Surveyor: Claude Code (Terminal 10)
Date: 2026-04-19
Scope: 시크릿 관리·인젝션·인증/인가·DB/리소스·로깅/관측·재시도/비용·메모리/크래시복구 — 크로스컷 감사

## 1. Executive Summary

- **성숙도 판정: Pre-production (보류) / 현상은 MVP+**
  - 핵심 기능(DB 트랜잭션, WAL, 메트릭 수집, 키 로테이션)은 갖춰져 있으나,
  - **프로덕션 블로커 4건**(시크릿 노출·브리지 인증 부재·WebDriver 누출·로그 로테이션 부재)으로 인해 **현 상태로는 실 서비스 투입 불가**.
  - 블로커 해소 시 Pre-production 상단 진입 가능.
- **한줄 요약**: "계약·자원관리·관측성의 뼈대는 있으나, 배포 전 필수 하드닝이 누락된 상태."

---

## 2. 강점 (Strengths)

- **DB 트랜잭션 계층** — `modules/core/db_manager.py:436-470, 1855-1890`
  - `@contextmanager def transaction()` 중첩 안전 + RLock 보호된 `begin/commit/rollback`
  - `close()` 시 in_transaction 감지 후 자동 rollback (`db_manager.py:472-484`)
- **WAL + 타임아웃** — `modules/core/db_bootstrap_runtime.py:34-35`, `db_manager.py:257`
  - `PRAGMA journal_mode=WAL`, `synchronous=NORMAL`, `timeout=30.0`
- **키 로테이션** — `modules/domain/agents/base_agent.py:193-270`
  - 다중 키 풀 + `threading.RLock` + exhaustion/cooldown 로직 (`MIN_ROTATION_INTERVAL` + counter 기반 소진 감지 라인 243-250)
- **중앙 로거 + 메트릭** — `modules/core/logger.py`, `modules/core/metrics_collector.py`
  - StudioLogger 싱글톤, 세션별 로그 파일 생성
  - 토큰/비용/응답시간/모델별 분석 메트릭 JSON 137개 누적 (~2026-01-31 ~ 2026-04-19)
- **원자적 메타데이터 저장** — `modules/core/stage4_post_pass_runtime.py:1687-1736`
  - `_save_world_state_atomic()` 트랜잭션 + rollback + 실패 핸들러
- **경로 탐색 방어** — `runtime_paths.py:88-102`
  - `.resolve().relative_to(projects_root)` 로 path traversal 차단
- **UTF-8 일관성** — `main_a.py:47-66` (`_bootstrap_windows_stdio_utf8`)
  - 16+ 곳에서 `encoding="utf-8"` 명시, `scripts/check_utf8_hygiene.py` 전역 위생성 검사 도구 존재
- **faulthandler 크래시 덤프** — `main_a.py:95-98`
  - `faulthandler.enable(file=_fault_log, all_threads=True)` + `atexit.register(_fault_log.close)`

---

## 3. 개선 필수 (Critical Issues) — P0

### P0-1. 실제 API 키가 작업 트리에 평문으로 존재 (BLOCKER)
- **파일:라인**
  - `.env:1` — `GOOGLE_API_KEY= AIzaSyCkPOYa5OHk_x-r2KKv0yWVYIbpREbn7Gk`
  - `.env:2` — `VERTEX_API_KEY =AQ.Ab8RN6IRKeUVJT8YvWvkM1p-aHRDifS5unPLoDVA9iYKBFQX8A`
  - `.env:5` — `CLAUDE_API=sk-ant-api03-...`
  - `secrets/clickup.env:1` — `CLICKUP_API_TOKEN=pk_306885786_...`
  - `test_mode/.env:1,3` — Google API 키 + Slack 웹훅 전체 경로
  - `tests/stage4_v2_test/project/.env:1` — `GOOGLE_API_KEY=AIzaSyC9Xu3Wrf...`
- **설명**: `.gitignore:12`에 `.env`는 포함되어 있어 현 HEAD에는 스테이지되지 않으나, 파일 자체가 평문 키를 보관 중. `test_mode/.env`·`tests/stage4_v2_test/project/.env`는 하위 경로라 `.gitignore` 패턴 커버리지 검토 필요.
- **영향도**: Critical — 키 유출 시 비용 청구·쿼터 고갈·외부 계정 오남용.
- **권장 조치**
  1. 노출된 4종 키 **즉시 로테이션** (Google/Vertex/Claude/ClickUp)
  2. `git log -p --all -- .env secrets/ test_mode/.env` 로 과거 커밋 유출 여부 확인 → 유출 시 `git-filter-repo`
  3. `.gitignore`에 `**/test_mode/.env`, `tests/**/.env`, `**/project/.env` 재귀 패턴 추가
  4. 로컬도 `secrets-manager` / `keyring` 기반 저장으로 이전

### P0-2. bridge_server FastAPI 엔드포인트 9개 전부 무인증 (BLOCKER)
- **파일:라인**
  - `modules/api/bridge_server.py:2373` `@app.post("/run")`
  - `:2486` `/run/{run_id}/input`
  - `:2516` `/stop`, `:2534` `/status`
  - `:2577` `/quality/summary`, `:2594` `/quality/dashboard`
  - `:2608` `/safe-ops/preview`, `:2624` `/quality/review`
  - `:2671` `@app.websocket("/events")`
- **설명**: `Depends(Security(...))`·APIKey·Bearer 전무. `CORSMiddleware` 미구성. 전량 오픈 상태. RiskApprovalGate는 `/run`의 RISK_KEYS에만 적용.
- **영향도**: Critical — 데스크톱 앱 로컬호스트 전제를 벗어나는 순간 임의 실행/상태 조회/원고 유출. LAN 노출 시 즉시 악용 가능.
- **권장 조치**
  1. APIKey 헤더(`X-Bridge-Token`) 검증 `Depends`를 모든 라우트에 적용, 토큰은 `.env`에서 로드
  2. `bind = 127.0.0.1`만 허용하도록 uvicorn 구동 옵션 강제
  3. CORS 화이트리스트(데스크톱 오리진) 명시
  4. WebSocket `/events`는 핸드셰이크 쿼리 토큰 검증

### P0-3. Selenium WebDriver 누출 — `.quit()` 호출 부재
- **파일:라인**
  - `lite_mode/bridge/gemini_driver.py:158-161` ChromeDriver 생성 지점
  - `lite_mode/` 전역 `driver.quit()` 검색 결과 **0건** (grep: `.quit()` 매칭은 `tmp.close()`만 2건)
- **설명**: 드라이버 소멸자/정리 경로가 없어 예외 종료 시 Chrome 프로세스 고아화, `--remote-debugging-port=9222` 포트 점유. 반복 실행으로 누적 시 시스템 안정성 침해.
- **영향도**: Critical (장기 운영) — 브리지 모드 사용자 머신 저하.
- **권장 조치**
  1. `GeminiDriver`에 `__enter__/__exit__` 구현 후 호출측 `with`로 감쌈
  2. `atexit.register(self.driver.quit)` 등록
  3. `BridgeRunner.shutdown()` 경로에 명시적 `quit()`

### P0-4. 로그/DB 파일 무경계 누적 (로테이션 부재)
- **파일:라인**
  - `modules/core/logger.py:112-116` 포맷 정의 — `TimedRotatingFileHandler/RotatingFileHandler` **미사용**
  - `logs/` 디렉토리 **180개 파일**, `.db/.sqlite*` **121개 파일** (find 집계)
  - `crash_dump.log` — stack overflow 다량 기록 누적
  - 세션 로그에 원고 전체 JSON 덤프 포함 (예: `logs/session_20260301_160017.log` 첫 블록에서 수 KB 원문 덤프 확인)
- **설명**: 크기 제한·보관 정책 없음. 원고 전체 문자열 기록으로 로그 팽창 가속. 장기 실행 시 디스크 압박.
- **영향도**: High — 디스크 풀 → 세션 중단 / 포렌식 가치 저하.
- **권장 조치**
  1. `TimedRotatingFileHandler(when='midnight', backupCount=14)` 도입
  2. 원고·API 키 패턴 필터링 `logging.Filter` 추가 (민감정보 redaction)
  3. `logs/metrics/*.json`은 별도 월별 아카이브

---

## 4. 개선 권장 (Major Issues) — P1

### P1-1. 재시도/백오프 정책 파편화
- **파일:라인**
  - `modules/core/adaptive_retry.py:88-96, 188-212` — 에러 타입별 고정 지연 맵
  - `modules/domain/agents/base_agent.py:719, 1327` — 선형 증가 `30 * retry_count` (30/60/90s)
  - `modules/core/stage01_helpers.py:461-498` — 최대 2회
  - `modules/core/stage2_orchestrator.py:1131` — `analyst_max_attempts: 5`
- **설명**: 3곳 이상에서 서로 다른 정책(고정/선형). 지수 백오프 및 지터 전무. `tenacity`·`backoff` 미사용.
- **영향도**: Medium — rate-limit 폭주 시 동기화된 재시도로 thundering herd 가능.
- **권장 조치**: `tenacity.Retrying(exponential_backoff + jitter)` 단일 진입점으로 통합, `config/retry.yaml` 외부화.

### P1-2. HTTP/LLM 클라이언트 타임아웃 미명시
- **파일:라인**
  - `modules/providers/anthropic_provider.py`, `vertex_provider.py:115-121`, `gemini_provider.py` — `timeout=` 파라미터 부재, SDK 기본값(보통 600s 내외) 의존
  - `subprocess.run(..., timeout=...)` 명시 사례 검색 결과 없음
  - Selenium `WebDriverWait` 명시적 대기 거의 없음 (`lite_mode/bridge/gemini_driver.py`)
- **영향도**: High — 네트워크 스톨 시 세션 단위 데드락.
- **권장 조치**: 모든 프로바이더 `timeout=(connect=10, read=120)` 표준화, `WebDriverWait(driver, 30).until(...)` 패턴 적용.

### P1-3. 프로바이더 간 페일오버 부재
- **파일:라인**
  - `modules/domain/agents/base_agent.py:707-762` — `model_stack` 내 모델 로테이션만 존재
  - `modules/providers/anthropic_provider.py:14-17` — `ANTHROPIC_API_KEY → CLAUDE_API` fallback 외 교차 프로바이더 경로 없음
- **영향도**: Medium — Google 전역 장애 시 복구 불가.
- **권장 조치**: 상위 오케스트레이터에 Provider 우선순위 + circuit breaker (`pybreaker`) 도입.

### P1-4. SQL 동적 식별자 f-string
- **파일:라인**
  - `modules/core/db_manager.py:174, 193, 1989`
  - 라인 193: `f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"` (`# noqa: S608`)
  - 라인 616-626: 컬럼명 f-string (`_SAFE_COLUMN_RE.match(k)`로 방어 — 수용 가능하나 문서화 필요)
- **영향도**: Low-Medium — 현재 호출자는 전부 내부이나 계약 드리프트 시 위험.
- **권장 조치**: 식별자 화이트리스트 상수화 + `sqlite3.sqlite_version` 기반 파라미터 바인딩 재검토.

### P1-5. 비용 한도/서킷 차단 메커니즘 없음
- **파일:라인**
  - `modules/core/metrics_collector.py:76-101` — `MODEL_COSTS` 인라인(주석: "Target: move to config/models.yaml")
  - budget/cap/threshold 로직 grep 결과 0건
- **영향도**: High — 토큰 폭증 에피소드에서 비용 폭주 가능.
- **권장 조치**: 에피소드/세션별 USD 상한 + 90%에서 `logger.warning`, 초과 시 중단.

### P1-6. 공유 상태 무경계 누적
- **파일:라인**
  - `modules/core/adaptive_retry.py:203` `ctx.error_history.append(...)` — 경계 없음
  - `modules/core/lore_manager.py:89,172,184` — `_lore_cache` eviction 없음
  - `modules/core/prompt_loader.py:60-66,117,129` — `_cache` 크기 제한 없음
  - `modules/api/process_runner.py:507` `_stdout_tail.append()` (개별 라인 240자 trim, 전체 경계 없음)
- **영향도**: Medium — 장기 세션 시 메모리 팽창.
- **권장 조치**: `collections.deque(maxlen=N)` 또는 `cachetools.LRUCache(maxsize=N)` 도입.

### P1-7. 직접 `conn.commit()` lock 미보호
- **파일:라인**: `modules/core/db_bootstrap_runtime.py:75, 86` — 테이블 생성 경로에서 DBManager `_lock` 우회
- **영향도**: Low-Medium — 부트스트랩 경로라 경합 적지만 계약 불일치.
- **권장 조치**: `with self.owner._lock:` 래핑 또는 DBManager API 경유.

### P1-8. 세션 로그에 원고/민감정보 평문 포함
- **근거**: `logs/session_20260301_160017.log` 첫 블록에 ~2KB 원문 JSON 덤프
- **영향도**: Medium — 로그 유출 시 창작물/사용자 입력 누출.
- **권장 조치**: `logging.Filter`로 `api_key|token|password|Authorization` 패턴 redaction, 원고는 해시/요약만 기록.

### P1-9. `bare except` 10건 (5개 파일)
- **파일:라인**
  - `tools/story_expander.py:574`, `tools/treatment_extractor.py:99`
  - `tools2/reverse_bible.py:85`, `tools2/studio_dashboard.py:445,457,469,935,2009` (5건)
  - `tests/test_integrity.py:92,96`
- **MEMORY.md 언급 "~68"에서 대폭 축소 확인됨** — 핵심 코어는 정리 완료, tools/tests 잔여.
- **권장 조치**: `except Exception as e:` + `logger.exception(...)` 교체.

### P1-10. Sequential-fallback 시 원자성 약화
- **파일:라인**: `modules/core/stage4_post_pass_runtime.py:1708-1715`
  - `sequential_mode = txn is None` — 트랜잭션 불가 시 "sequential save recovery mode" 경고 후 진행
- **영향도**: Medium — WorldState 저장 후 FactLedger 실패 시 부분 상태 잔존.
- **권장 조치**: fallback 경로에 snapshot+swap(tmp→rename) 보강.

---

## 5. 개선 검토 (Minor Issues) — P2

- **P2-1. 구조화 로깅 부재** — `structlog`/`loguru` 미도입, 텍스트 포맷만. 검색/집계 비용 증가. (`modules/core/logger.py:112-116`)
- **P2-2. print() 잔재** — 프로덕션+테스트 합계 ~2,860건 (샘플: `lite_mode/bridge/state_ledger.py`, `main_a.py`). logger 일원화 권장.
- **P2-3. 메모리 프로파일링 비활성** — `tracemalloc`/`memory_profiler` 미사용, `gc.collect()`은 테스트 conftest에서만.
- **P2-4. `lru_cache(maxsize=1)`** — `stage4_policy_digest.py:23` 단일 엔트리 캐시 효용 미미.
- **P2-5. Prompt caching 측정 메트릭 미노출** — `cached_tokens` 수집되나 히트율 리포트 없음.
- **P2-6. `resolve_prompt()` 교차-run 보호 부재** — `modules/api/bridge_server.py:2486-2512` prompt_id만으로 해소.
- **P2-7. MODEL_COSTS 인라인** — `metrics_collector.py:85` 주석에도 "Target: config/models.yaml" 명시, 미이행.
- **P2-8. ClickUp 토큰 README만 있음** — `secrets/README.md` 존재하지만 키 관리 표준(암호화·vault) 부재.
- **P2-9. 에러 체이닝 불일치** — `raise X from e` 17개 파일만 사용. bare except와 혼재.
- **P2-10. crash_dump.log에 JSON encoder 재귀 스택오버플로우 기록** — 메트릭 직렬화 경로에 순환 참조 가능성 (`crash_dump.log` 첫 블록: `json/encoder.py _iterencode_list`). 트리거 조건 조사 필요.

---

## 6. 수치 지표 (Metrics)

| 지표 | 값 | 근거 |
|------|---:|------|
| `.env` 실제 키 보유 파일 수 | 4 | `.env`, `secrets/clickup.env`, `test_mode/.env`, `tests/stage4_v2_test/project/.env` |
| 하드코딩 키(앱 코드) | 0 | grep on `sk-ant`, `AIza`, `pk_` in `modules/` |
| 무인증 bridge 엔드포인트 | 9 | `bridge_server.py:2373..2671` |
| `eval/exec/compile` 위험 사용 | 0 | Agent 조사 결과 |
| `subprocess shell=True` | 0 | Agent 조사 결과 |
| SQL f-string 식별자 | 3 | `db_manager.py:174, 193, 1989` |
| `bare except` (프로덕션+tools+tests) | 10 (5파일) | grep 집계 |
| `raise ... from e` 사용 파일 | 17 | grep 집계 |
| `logging.getLogger/basicConfig` 사용 파일 | 64 | grep 집계 |
| `print()` 호출 (프로젝트 전체) | ~2,860 | grep 집계 |
| `.db/.sqlite*` 파일 수 | 121 | find 집계 |
| `logs/` 디렉토리 파일 수 | 180 | ls 집계 |
| 수집된 메트릭 JSON | 137 | `logs/metrics/` |
| MODEL_COSTS 등록 모델 | 6+ | `metrics_collector.py:85-101` |
| WebDriver `.quit()` 호출 | 0 | `lite_mode/` grep |
| `TimedRotatingFileHandler` 사용 | 0 | grep |
| Circuit breaker 라이브러리 사용 | 0 | grep |
| `tenacity`/`backoff` 사용 | 0 | grep |

---

## 7. 성숙도 근거 (Maturity Evidence)

**POC 배제 근거**: 트랜잭션/WAL/키 로테이션/메트릭/크래시 덤프/원자적 저장 등 프로덕션 관심사가 이미 구현됨.

**Production-ready 배제 근거 (블로커 존재)**:
1. 시크릿이 작업 트리에 평문 (P0-1)
2. 브리지 엔드포인트 무인증 (P0-2)
3. Selenium 프로세스 누출 (P0-3)
4. 로그/DB 로테이션 부재로 장기 실행 불가 (P0-4)
5. 프로바이더 간 페일오버 없음 (P1-3)
6. 비용 상한/차단 메커니즘 없음 (P1-5)

**Pre-production 근거**: 블로커 4건은 각각 설정·미들웨어·컨텍스트매니저 수준으로 해결 가능한 범위이며, 근본적 재설계가 필요한 항목 아님. 블로커 해소 시 Pre-production 진입 판정 가능.

**현 판정: Pre-production (Blocked) — MVP+ 실질 동작**
- 내부/로컬 사용: 가능
- 로컬호스트 외 노출: 금지
- 지속 배포: 블로커 해소 후 가능

---

## 8. 권장 로드맵 (Recommendations)

### 스프린트 0 — 배포 블로커 제거 (1주 이내)
1. **P0-1 키 로테이션** — Google/Vertex/Claude/ClickUp 4종 즉시 교체, git 히스토리 감사
2. **P0-2 브리지 인증** — `X-Bridge-Token` 헤더 검증 미들웨어, `127.0.0.1` 바인드 강제
3. **P0-3 WebDriver 컨텍스트매니저** — `GeminiDriver.__enter__/__exit__` + `atexit` 등록
4. **P0-4 로그 로테이션** — `TimedRotatingFileHandler(backupCount=14)` + 민감정보 `logging.Filter`

### 스프린트 1 — 안정성 표준화 (2주)
5. **P1-1/2 재시도·타임아웃 통합** — `tenacity` 기반 단일 진입점, 모든 프로바이더 `timeout` 표준화
6. **P1-5 비용 상한** — 세션/에피소드 USD 캡, 90% 경고, 초과 중단
7. **P1-6 캐시 경계** — `deque(maxlen)`/`LRUCache` 일괄 적용
8. **P1-8 로그 redaction** — 원고 해시/요약, 키 패턴 자동 마스킹

### 스프린트 2 — 관측성/페일오버 (2-3주)
9. **P1-3 프로바이더 페일오버** — 회로차단기 + 교차 프로바이더 라우팅
10. **P2-1 구조화 로깅** — `structlog` 도입, JSON 출력
11. **P2-5 캐시 히트율 리포트** — 세션 리포트에 prompt-cache 효율 노출
12. **P2-7 MODEL_COSTS 외부화** — `config/models.yaml` 이관

### 스프린트 3 — 위생 (상시)
13. **P1-9 bare except 정리** — tools/tests 10건 `except Exception + logger.exception`
14. **P2-2 print 제거** — 프로덕션 경로 일괄 logger 전환
15. **P2-10 JSON 재귀 조사** — crash_dump의 `_iterencode_list` 트리거 경로 추적
16. **P1-10 sequential fallback 강화** — snapshot+swap 패턴으로 원자성 회복

---

**감사 완료**: 2026-04-19
**조사 방식**: 5개 Explore 에이전트 병렬 + P0 원본 교차 검증 (`.env` 실물, bridge_server 라우트 9건, bare except grep, WAL PRAGMA, MODEL_COSTS 인라인)
**다음 단계**: T01~T09 결과와 교차 검증 후 `AUDIT-REPORT.md` 통합
