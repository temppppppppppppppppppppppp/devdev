# T09: Lite Mode / Desktop / Bridge 주변 시스템

Surveyor: Claude Code (Terminal 9)
Date: 2026-04-19
Scope: `lite_mode/`, `geuldobi-desktop/`, `modules/api/` (특히 `bridge_server.py`), `visual_lab/` — 주변 시스템 성숙도와 코어 통합 품질 감사

---

## 1. Executive Summary

- **성숙도 판정**: **MVP → Pre-production 혼재**
  - `geuldobi-desktop` + `modules/api/`: **Pre-production** (견고한 Electron 격리·24개 IPC 핸들러·FastAPI + WebSocket·리스크 듀얼컨트롤이 완성도 높음)
  - `lite_mode/`: **MVP** (Selenium 기반, 수동 프로브 15개·상태 ledger 원자 쓰기 부재·재개 체크포인트 부재)
  - `visual_lab/`: **POC/실험** (578 LOC·잡 스펙 2개·14일 정체·하드코딩된 외부 사용자 경로)
- **한줄 요약**: 주변 시스템은 격리·계약·보안 경계는 대체로 잘 그어졌으나, **bridge_server의 Pydantic/CORS 부재**, **lite_mode의 원자 파일 I/O 누락**, **visual_lab의 하드코딩 경로/정체**가 주요 리스크이며, 프로덕션 투입 전 표면적 좁히기가 필요하다.

---

## 2. 강점 (Strengths)

- **계층 격리가 명확**. `lite_mode/`는 `modules/`/`main_a.py`를 전혀 import하지 않음 (grep 결과 0건). `main_lite.py:7-9`에 "NOT part of supported runtime authority chain" 경고 명시. `visual_lab/`도 `main_a.py`에서 참조 0건 — 각 주변 시스템이 독립 단위로 동작.
- **Electron 보안 경계 잘 구성**. `geuldobi-desktop/src/main.js:591-640`에서 `contextIsolation:true, nodeIntegration:false` 강제, `src/preload.js:34-91`은 `contextBridge.exposeInMainWorld`로 31개 메서드만 노출. `src/index.html:6` CSP는 `connect-src ws://127.0.0.1:8300 https://generativelanguage.googleapis.com`로 제한.
- **IPC 경로 방어**. 24개 `ipcMain` 핸들러가 경로 traversal 차단 (`src/main.js:967`는 `..`/`/` 거부), 재료 폴더는 `{bible, treatments}` 화이트리스트만 (`src/main.js:990-999`). 파일명 sanitize 규칙 일관.
- **백엔드 프로세스 생명주기 관리**. `src/main.js:400, 537-551`에 재시작 카운터+최대 2회 후 사용자 확인, 5초 `AbortController` 타임아웃(`src/main.js:722-777`) 적용. WebSocket 포트 8300 localhost 고정.
- **Dual-control 승인 체계**. `modules/api/risk_approval.py:144-159, 162`에 primary ≠ secondary 강제 + 만료 검증. 모든 결정을 JSONL 감사 로그(`risk_approval.py:184-214`)에 영구 기록. 고위험 키(44/77/88/99)에 게이트 적용.
- **Director + Cross-checker 다계층 QA (lite)**. `lite_mode/bridge/runner.py`의 10라운드 Director + 2라운드 교차 검증·연속 0-streak 종료 조건 (`runner.py:1046-1050`)·5회 retry × 3층 (upload/send/skip)로 Selenium 불안정성을 완화.
- **Visual_lab 심사 스키마 엄격**. `run_cover_pipeline.py`/`run_illustration_pipeline.py` 모두 JSON schema를 Gemini에 전달해 랭킹/심사 출력을 구조화. 후보별 `*.judge.json` + `ranking.json` + `summary.md` 산출물 보존 → 재현 가능.
- **API 계약 양방향 정합**. `modules/api/control_plane_contract.py`(92 LOC) ↔ `geuldobi-desktop/src/desktop_control_plane_contract.js`(3.4KB)가 IPC_CHANNELS/라우팅을 양측에서 동기화. 계약 기반 테스트 존재(`tests/test_bridge_server_http_contract.py` 등 8개).
- **테스트 존재 (데스크톱/브리지)**. `npm test`가 15개 pytest + 3개 Node 테스트 실행 (브리지 계약·렌더러·패키징 커버).

---

## 3. 개선 필수 (Critical Issues) — P0

### P0-1. bridge_server가 요청 스키마 검증 없이 원시 JSON 파싱
- **파일:라인**: `modules/api/bridge_server.py:2384-2392`
- **설명**: `/run` 엔드포인트가 Pydantic 모델 없이 `body.get("key", "")`, `body.get("inputs") or {}`로 수동 파싱. `grep pydantic|BaseModel` 결과 0건 — FastAPI를 쓰면서 Pydantic 스키마를 전혀 사용하지 않음.
- **영향도**: 악성/변형 payload가 경계에서 거부되지 않고 하류로 전파. `inputs`가 그대로 `process_runner`의 stdin으로 (`process_runner.py:350-369, 391`) 흘러 프롬프트 파서 우회·주입 가능.
- **권장 조치**: `RunRequest(BaseModel)` 정의 → `key: Literal[...]`, `approval_id: Optional[UUID]`, `inputs: Dict[str, Union[str, int, bool, List[str]]]`. FastAPI가 422로 자동 차단하도록.

### P0-2. CORS/Origin 정책 부재
- **파일:라인**: `modules/api/bridge_server.py:2365-2369` (app 생성부), `grep CORSMiddleware|add_middleware` 결과 0건
- **설명**: FastAPI 앱에 `CORSMiddleware`·origin 체크 전무. 현재는 `127.0.0.1:8300` 바인딩에 의존하지만 환경변수 하나로 외부 바인딩 가능.
- **영향도**: 바인딩이 확장되는 순간 임의 origin이 `/run`·`/stop`·`/quality/*`를 호출. Electron 외 브라우저가 localhost 접근 가능한 배포 형상에서 특히 위험.
- **권장 조치**: `add_middleware(CORSMiddleware, allow_origins=["file://", "app://geuldobi"], allow_credentials=False, allow_methods=["GET","POST"], allow_headers=["Content-Type"])` + `uvicorn --host 127.0.0.1` 강제.

### P0-3. lite_mode state_ledger 원자 쓰기·스키마 검증 부재
- **파일:라인**: `lite_mode/bridge/state_ledger.py:59, 66-75, 62-63, 108-109, 145-146, 215-216, 239-240, 386-387`
- **설명**: `path.write_text()`로 직접 JSON 저장 — 파일 락 없음, 임시파일+`os.replace` 없음. 로드(`line 59`) 시 `_INIT_STATE` 대비 스키마 검증 없음. 6곳의 `except Exception:`이 예외를 삼킴.
- **영향도**: Chrome 크래시/동시 Selenium 세션·스레드 종료 시 `_state.json` 손상 → 이후 `KeyError` 연쇄. 데스(NPC 사망) 워닝·NPC 추출이 조용히 유실될 수 있음.
- **권장 조치**: `tempfile.NamedTemporaryFile(dir=..., delete=False)` → fsync → `os.replace()`. 로드 시 `jsonschema.validate` 또는 pydantic `State(BaseModel)`. `except Exception` 구체화.

### P0-4. lite_mode Pro quota 고갈 시 체크포인트 없이 파이프라인 전체 중단
- **파일:라인**: `lite_mode/bridge/runner.py:39-42, 962-967`
- **설명**: `ProLimitStop` 예외가 세션을 즉시 종료. Flash/Think 등 다른 모델로 폴백하거나 중간 상태를 저장하는 경로 없음.
- **영향도**: 장시간 실행 중 쿼터 소진 시 수 시간 분량의 중간 산출 손실. 수동 재시작 시 이전 에피소드 재생성 필요.
- **권장 조치**: 각 스테이지 전후 `state_ledger.checkpoint()` 저장 + `ProLimitStop` 포착 후 모델 다운그레이드 재시도 루프.

### P0-5. Visual_lab 잡 스펙 경로가 타 사용자 절대 경로로 하드코딩
- **파일:라인**: `visual_lab/cover_pipeline/jobs/isekai_helper.json:3-4`, `visual_lab/illustration_pipeline/jobs/d_ropan.json:3`
- **설명**: `C:/Users/wjjo/Desktop/...` — 현재 머신(`PC`)이 아닌 외부 사용자 경로. 레포 체크아웃 직후 그대로는 실행 불가.
- **영향도**: 재현·CI 불가. 파이프라인이 사실상 "실험 결과물 박제" 상태.
- **권장 조치**: `${WORKSPACE_ROOT}` 혹은 상대 경로 + `os.path.expandvars`/`pathlib.Path` 정규화. `visual_lab/README.md`에 상대 경로 규약 명시.

---

## 4. 개선 권장 (Major Issues) — P1

### P1-1. ProcessRunner 상태머신 경쟁 조건
- **파일:라인**: `modules/api/process_runner.py:333-378, 411-456`
- **설명**: `self._state != "idle"` 체크와 `"starting"` 세팅이 비원자적. `stop()`은 `terminate()→kill()` 실패 시에도 `self._state = "idle"`(line 445) 실행 → 좀비 프로세스 가능.
- **권장 조치**: `asyncio.Lock` 또는 `threading.Lock`으로 상태 전이 보호. `stop()`은 idempotent하게, `kill()` 실패 시 `"stuck"` 상태 유지.

### P1-2. PromptBroker 타임아웃 시 prompt 영구 잔존
- **파일:라인**: `modules/api/prompt_broker.py:126-142`
- **설명**: `asyncio.wait_for(..., timeout=300)` 타임아웃 후 기본값 적용·`prompt_timeout` emit까지만 하고 `self._prompts`에서 제거되지 않음.
- **영향도**: 장기 실행 시 메모리 누적, stale prompt_id 참조 오류.
- **권장 조치**: `finally` 블록에서 `self._prompts.pop(prompt_id, None)`.

### P1-3. 31개 `except Exception` in bridge_server.py 침묵 처리
- **파일:라인**: `modules/api/bridge_server.py:2386, 2459, 2476, 2309, 2664` 외 다수
- **설명**: 감사 로그 쓰기 실패·DB close 실패 등이 `except Exception` + log.warn로 무음 처리.
- **권장 조치**: 쓰기 실패는 별도 메트릭/알람 경로로 분리. `except (OSError, json.JSONDecodeError)` 구체화.

### P1-4. WebSocket 브로드캐스트가 연결 끊김 조용히 정리
- **파일:라인**: `modules/api/bridge_server.py:138-147`
- **설명**: 죽은 연결을 조용히 제거 — 로그 없음. 클라이언트 측 실패 관측 불가.
- **권장 조치**: 제거 이벤트 카운터/로깅, `dropped_client_count` 메트릭 노출.

### P1-5. Selenium 선택자 캐시 72시간 stale 검증 약함
- **파일:라인**: `lite_mode/bridge/ui_discovery.py:283-284`, `lite_mode/bridge/gemini_driver.py:194-195`
- **설명**: UIDiscovery가 Gemini DOM 선택자를 72h 캐시. 캐리브레이션은 core 선택자만 검증. 세션 중 Gemini UI 변경 시 `.get()`이 stale 반환.
- **권장 조치**: 각 send_with_file 실패 시 자동 recalibrate + fallback 사용 횟수 카운터 로깅.

### P1-6. 테스트 프로브 15개 파일이 pytest 외부에 방치
- **파일:라인**: `lite_mode/test_hide.py`, `test_offscreen.py`, `test_minimized{,2,3}.py`, `test_background.py`, `test_bg_check.py`, `test_bg_covered.py`, `test_delete_diag.py`, `test_delete_full.py`, `test_model_select.py`, `test_new_chat.py`, `test_model_select.py`, `inspect_delete.py`, `inspect_gemini_ui.py`, `inspect_sidebar.py`, `manual_ui_discovery_probe.py`
- **설명**: pytest 집합이 아닌 수동 프로브 스크립트. CI가 실행하지 않고, `import` 되지 않음. 유지보수 불명.
- **권장 조치**: `lite_mode/probes/` 하위로 이동 + README에 "수동 진단 도구" 명시, 혹은 `tests/integration/test_lite_*.py`로 정식화.

### P1-7. lite_mode `tests/` 커버리지 0
- **파일:라인**: 전역 `tests/` 하 grep 결과 lite_mode 커버 테스트 없음
- **설명**: 5,611 LOC 주변 시스템에 대한 자동 회귀 부재.
- **권장 조치**: Selenium mock + fake Gemini stub으로 `tests/test_lite_runner_smoke.py`.

### P1-8. innerHTML 할당 잔존 (XSS 위험, 완화됨)
- **파일:라인**: `geuldobi-desktop/src/quality_page_bootstrap.js:36, 52, 74, 101, 155` 외 다수
- **설명**: `escapeHtml`/`sanitizeToken`로 감쌌으나 패턴 자체가 위험. 신규 필드 추가 시 escape 누락하면 즉시 XSS.
- **권장 조치**: 점진적으로 `textContent`/`createElement`/`appendChild`로 마이그레이션. lint 규칙으로 `innerHTML` 금지.

### P1-9. subprocess가 부모 env 상속 → 비밀 유출 가능
- **파일:라인**: `modules/api/process_runner.py:226-233`
- **설명**: `_resolve_provider_mode()`가 입력 누락 시 `os.getenv(PROVIDER_MODE_ENV)`로 폴백하며, 기본 `env=None` subprocess는 부모의 전체 env 상속. CI 비밀·다른 API 키 노출.
- **권장 조치**: 명시적 화이트리스트 env dict을 `create_subprocess_exec(env=...)`에 전달.

### P1-10. Control-plane 감사 JSONL 무한 증가
- **파일:라인**: `modules/api/bridge_server.py:468-477`, `modules/api/risk_approval.py:209-215`
- **설명**: 감사/승인 로그가 append-only. 로테이션·크기 상한 없음.
- **권장 조치**: `logging.handlers.RotatingFileHandler` 혹은 일별 날짜 suffix로 분할.

### P1-11. Lite 컨텍스트 토큰 한계 직전 무음 절삭
- **파일:라인**: `lite_mode/bridge/runner.py:931` (ARCHITECTURE.md:411 참조)
- **설명**: 150KB 상한 근처에서 silent trim. 임계 초과 시 경고/메트릭 없음.
- **권장 조치**: 80%·95% 두 단계 경고 로그 + `state_ledger`에 트림 이벤트 기록.

### P1-12. Visual_lab 외부 스크립트 의존 (`scripts/gemini_cover_title_edit.py`)
- **파일:라인**: `visual_lab/cover_pipeline/scripts/run_cover_pipeline.py:49, 56-80`
- **설명**: 커버 파이프라인이 `visual_lab/` 바깥 레포 루트 스크립트에 의존. 존재/버전 검증 없음.
- **권장 조치**: 의존을 `visual_lab/` 내부로 인라인하거나, 존재 확인 + 버전 체크 추가.

### P1-13. Visual_lab 재현성 부재
- **파일:라인**: `run_cover_pipeline.py:150, 224`, `run_illustration_pipeline.py:150, 224`
- **설명**: `temperature=0.35/0.1` 하드코딩, seed 미지정. Gemini 모델 업데이트 시 랭킹 결과 변동 → "best" 후보 재현 불가.
- **권장 조치**: 잡 스펙에 `seed`·`temperature` 필드 추가, 결과 JSON에 모델 버전 기록.

### P1-14. 데스크톱 코드 서명 비활성
- **파일:라인**: `geuldobi-desktop/package.json` build 설정 (`signAndEditExecutable:false`)
- **설명**: 패키지 .exe가 서명 없음 — 탬퍼링 가능, Windows SmartScreen 경고.
- **권장 조치**: 인증서 발급 후 electron-builder `win.certificateFile` 지정.

### P1-15. Dual-control 조작자(operator) 빈 문자열 허용
- **파일:라인**: `modules/api/risk_approval.py:104, 121-128, 161-173`
- **설명**: `operator` 기본값 빈 문자열. approval_id 조회 이후 듀얼컨트롤 검사가 오므로, 서버 측 non-empty 강제 부재.
- **권장 조치**: Pydantic `constr(min_length=1)` + primary≠secondary 선검사.

---

## 5. 개선 검토 (Minor Issues) — P2

- **P2-1. free_writer.py가 runner.py 내부 심볼에 직접 의존**: `lite_mode/free_writer.py:29, 34` — `from runner import GeminiDriver, Spinner, log, DIRECTOR_PROMPT`. 공통 로직을 `bridge/common.py`로 추출 권장.
- **P2-2. reset_session의 chat delete 재시도 없음**: `lite_mode/bridge/gemini_driver.py` (ARCHITECTURE.md:412). 실패 시 사이드바 채팅 누적 → 장기 세션 UI 열화. 지수 백오프 재시도 권장.
- **P2-3. /quality/dashboard pagination 없음**: `modules/api/bridge_server.py:2594-2607`. 1000+ 에피소드 프로젝트 시 payload 비대.
- **P2-4. 설정 payload 상한 1MB 과다**: `geuldobi-desktop/src/main.js:136` — `SETTINGS_PAYLOAD_MAX_BYTES = 1024*1024`. 50–100KB로 하향 권장.
- **P2-5. 쿨러티 오버레이 React Error Boundary 부재**: `geuldobi-desktop/src/quality_page_bootstrap.js`, `quality_react_runtime.js`. 렌더 실패 시 전체 패널 dead.
- **P2-6. 백엔드 stdout 앱 로그 파일에 미캡처**: `geuldobi-desktop/src/main.js:508-517`. 콘솔로만 흘려보냄 — 사용자 문제 진단 어려움.
- **P2-7. README PowerShell line-continuation**: `visual_lab/cover_pipeline/README.md:38-39`, `visual_lab/illustration_pipeline/README.md:19-20`. `^` 사용은 비-Windows에서 혼란.
- **P2-8. Visual_lab 가중치 매직 넘버**: `run_cover_pipeline.py:170-178`, `run_illustration_pipeline.py:229-239`. 가중치·정규식 상수에 주석·config화 권장.
- **P2-9. 샌디타이저 정규식 유효성 검증 없음**: `lite_mode/bridge/runner.py:850-890` 영역 — Gemini 응답 노이즈 제거 정규식. `len(clean)/len(raw) < 0.5` 이면 경고 로그.
- **P2-10. first-run 마커 변조 가능**: `geuldobi-desktop/src/main.js:391` — `.first_run`은 단순 파일, 삭제 시 워크스페이스 시드 재복사. 최소 파급, 서명·해시 검증까진 과투자.

---

## 6. 수치 지표 (Metrics)

| 항목 | 값 |
|------|----|
| **lite_mode/ 총 LOC** | 5,611 (bridge 4,862 + top-level 749) |
| **lite_mode 수동 프로브 스크립트** | 15 (test_*.py/inspect_*.py/manual_*.py) |
| **lite_mode → modules/ import** | 0 (완전 격리) |
| **geuldobi-desktop JS LOC (src/*.js)** | ~4,101 (vendor/React 제외) |
| **데스크톱 IPC 핸들러 수** | 24 (`ipcMain.handle`) |
| **preload 노출 메서드** | 31 (`contextBridge.exposeInMainWorld`) |
| **Electron 버전** | 40.8.0 |
| **React 버전 (vendored)** | 18.3.1 (자동 갱신 없음) |
| **modules/api 총 LOC** | 4,333 (bridge_server 2,688 + process_runner 867 + 기타) |
| **bridge_server endpoints** | 8 (`/run`, `/stop`, `/status`, `/events` WS, `/run/{id}/input`, `/quality/summary`, `/quality/dashboard`, `/quality/review`, `/safe-ops/preview`) |
| **bridge_server Pydantic 사용** | 0 (수동 검증) |
| **bridge_server CORSMiddleware** | 0 |
| **bridge_server `except Exception` 수** | 31 |
| **visual_lab Python LOC** | 578 (2 스크립트) |
| **visual_lab 잡 스펙** | 2 (`isekai_helper.json`, `d_ropan.json`) |
| **visual_lab 산출물** | 20 (후보 judge JSON 8 + ranking 2 + summary 2 + README 3 + 잡 2 + 이미지 다수) |
| **visual_lab 최근 수정** | 2026-04-05 (14일 정체) |

---

## 7. 성숙도 근거 (Maturity Evidence)

### Pre-production 신호 (geuldobi-desktop + modules/api)
- **보안 경계 완성도**: context isolation·restrictive CSP·24개 IPC 핸들러 전원 경로 traversal 방어·화이트리스트 적용.
- **계약 양방향 동기화**: `control_plane_contract.py ↔ desktop_control_plane_contract.js` 쌍으로 설계. 계약 테스트 존재.
- **프로세스 생명주기 관리**: 재시작 카운터·AbortController 타임아웃·WebSocket 재연결.
- **감사·Dual-control**: 고위험 키 접근 시 듀얼컨트롤 강제 + JSONL 영구 감사 기록.
- **테스트 스위트**: `npm test`에 15 pytest + 3 Node; HTTP 계약·렌더러·패키징 커버.

### MVP 신호 (lite_mode)
- **기능 동작**: Selenium UI 자동화가 10라운드 Director + 2라운드 교차 검증까지 구성됨.
- **격리 깨끗**: 코어와 import 0건 — 실험적 경로로 안전 분리.
- **그러나 운영 부재**: 자동 회귀 테스트 0건·15개 수동 프로브·파일 락 없음·재개 체크포인트 없음·메트릭 없음. UI 변경 시 사람이 재캘리브레이션.

### POC/실험 신호 (visual_lab)
- **소규모 + 정체**: 2 스크립트·14일 미변경.
- **사용자 고정 경로 하드코딩**: `C:/Users/wjjo/...` — 내 머신에서 그대로 못 돌림.
- **체크인된 산출물 기반 설계**: 재현보다 "결과물 보존"에 가까움 (seed·버전 기록 없음).

### 전반 평가
- 외향 표면(데스크톱 UI + HTTP 브리지)은 **Pre-production급 방어**.
- 비공식 백도어(Selenium lite, 실험 파이프라인)는 **각자 다른 성숙도**로 공존.
- **프로덕션 진입 전 블로커**: Pydantic 도입·CORS 정책 명시·state_ledger 원자 쓰기 → 이 3건 해소 시 Pre-production 상향 가능.

---

## 8. 권장 로드맵 (Recommendations)

### 스프린트 1 (Blocker 해소, 1–2주)
1. `bridge_server.py`에 Pydantic `RunRequest`/`StopRequest`/`InputRequest` 도입 — 모든 POST 엔드포인트 교체. [P0-1]
2. CORSMiddleware 추가 + `uvicorn --host 127.0.0.1` 문서화·코드 강제. [P0-2]
3. `state_ledger.py`에 `tempfile+os.replace` 원자 쓰기 + `jsonschema` 검증. [P0-3]
4. Visual_lab 잡 스펙 경로를 `${WORKSPACE_ROOT}`/상대경로로 변환. [P0-5]

### 스프린트 2 (안정성 강화, 2–3주)
5. `ProLimitStop` 포착 후 Flash 폴백 + state checkpoint 저장. [P0-4]
6. `process_runner.py` 상태머신 락·idempotent stop. [P1-1]
7. `prompt_broker.py` 타임아웃 시 `_prompts` 정리. [P1-2]
8. `lite_mode/tests/` 신설 (Selenium mock 기반 smoke). [P1-7]
9. 15개 수동 프로브를 `lite_mode/probes/`로 이전 + README 명시. [P1-6]

### 스프린트 3 (운영·관측, 2주)
10. 감사 JSONL 로테이션 (일별 분할 또는 RotatingFileHandler). [P1-10]
11. subprocess env 화이트리스트. [P1-9]
12. WebSocket 드롭 카운터 노출 + `/metrics` 엔드포인트 검토. [P1-4]
13. 데스크톱 코드 서명 파이프라인 구축 (CI에 인증서 주입). [P1-14]
14. `innerHTML → textContent` 점진 마이그레이션 + ESLint 규칙. [P1-8]

### 장기 (리팩토링)
15. `bridge_server.py` 2,688 LOC 분할 — 라우터/비즈니스/저장소 레이어 분리 (T04 트랙 교차 참고).
16. `runner.py` 1,998 LOC에서 Director 루프·샌디타이저·모델 선택을 모듈화.
17. Visual_lab에 seed·버전 핀·CI smoke 도입 후 Stage4 orchestrator와 얇은 연결 (선택).

---

### 부록: 감사 검증 근거 스냅샷

- `grep "pydantic\|BaseModel" modules/api/bridge_server.py` → 0건 (P0-1 근거)
- `grep "CORSMiddleware\|add_middleware" modules/api/bridge_server.py` → 0건 (P0-2 근거)
- `grep -r "from modules\.\|import modules\." lite_mode/` → 0건 (Strength·격리 근거)
- `grep "visual_lab" main_a.py` → 0건 (visual_lab 고립 근거)
- `find visual_lab -name "*.json" -o -name "*.md"` → 최신 수정 2026-04-05 (14일 정체 근거)
