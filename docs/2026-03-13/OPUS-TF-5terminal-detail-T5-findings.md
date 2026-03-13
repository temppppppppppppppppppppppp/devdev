# OPUS TF 2차 디테일 감사 — Terminal 5: 스크립트, 프런트엔드, 루트 파일, Treatments, Projects

> **작성일**: 2026-03-13
> **범위**: scripts/ 16개 + 루트 파일 13개 + Desktop Electron 8개 + treatments/ 489개 JSON + projects/ 5개 + MagicMock/
> **방법**: 자체 3PASS (PASS1 발견 → PASS2 교차검증+오탐제거 → PASS3 확정)
> **서브태스크**: Sub-A(Scripts+Root+MagicMock), Sub-B(Desktop Electron), Sub-C(Treatments+Projects)

---

## 최종 집계

| Severity | 건수 |
|----------|------|
| P0 CRITICAL | 0 |
| P1 IMPORTANT | 2 |
| P2 MODERATE | 11 |
| P3 LOW/HYGIENE | 9 |
| **합계** | **22** |

**3PASS 오탐 통계**: PASS1 103건 후보 → PASS2 81건 제거 → **최종 22건 확정** (오탐률 79%)

---

## P1 — IMPORTANT (2건)

### [D-T5-001] 3중 main.js Dead File — 루트 및 geuldobi-desktop/main.js 삭제 필요

**파일**:
| 파일 | 줄수 | 상태 | 역할 |
|------|------|------|------|
| `geuldobi-desktop/src/main.js` | 843 | tracked (M) | **실제 진입점** — `package.json` `"main": "src/main.js"` |
| `geuldobi-desktop/main.js` | 758 | untracked | src/main.js의 **구버전 복사본** — WorkGuard 핸들러 2개 누락 |
| `main.js` (루트) | 14 | untracked | splash.html 로드 테스트용 1회성 스크립트 |

**증거**:
- `geuldobi-desktop/main.js`에 `project:list-work-guard-templates`, `project:apply-work-guard-template` 핸들러 없음
- `geuldobi-desktop/main.js`에 `debugLog()` 인프라 없음
- 루트 `main.js`는 14줄짜리 splash 로드 확인 후 `app.quit()` — 완전히 다른 목적

**위험**: 개발자가 잘못된 main.js를 편집하면 변경이 무시됨. package.json `main` 변경 시 WorkGuard 기능 소실.

**권고**: 두 파일 모두 삭제.

---

### [D-T5-002] 렌더러에서 googleapis.com 직접 fetch — API 키 노출 경로

**파일**: `geuldobi-desktop/src/index.html` L6 (CSP), L7369 (fetch)

**증거**:
- CSP: `connect-src ... https://generativelanguage.googleapis.com`
- L7369: `fetch(\`https://generativelanguage.googleapis.com/v1beta/models?key=${encodeURIComponent(key)}\`)`
- 설정 모달의 API 키 테스트 기능이 렌더러에서 직접 Gemini API 호출

**위험**:
1. API 키가 렌더러 메모리에 평문 존재 — XSS 시 키 유출 가능
2. CSP `script-src 'unsafe-inline'`과 결합 시 XSS → API 키 탈취 체인 성립
3. 최소 권한 원칙 위반 — API 키 검증은 main process에서 수행해야 함

**권고**: API 키 테스트를 main process IPC 핸들러로 이전. CSP에서 `googleapis.com` 제거.

---

## P2 — MODERATE (10건)

### [D-T5-003] CSP `script-src 'unsafe-inline'` 허용

**파일**: `geuldobi-desktop/src/index.html` L6

**증거**: index.html이 7,800줄+ 인라인 `<script>` 블록 포함 → `unsafe-inline` 필요한 구조. D-T5-002와 결합 시 공격 표면 확대.

**완화**: `contextIsolation: true` + `nodeIntegration: false`로 Node.js API 직접 접근 불가. localhost 전용.

**권고**: 장기 — 인라인 스크립트를 외부 `.js`로 분리 + `unsafe-inline` 제거. 단기 — nonce 기반 CSP 검토.

---

### [D-T5-004] preload.js `material:delete-file` — main process 측 확인 다이얼로그 부재

**파일**: `geuldobi-desktop/src/preload.js`, `geuldobi-desktop/src/main.js`

**증거**: 렌더러에서 파일 삭제 트리거 가능. folder 화이트리스트(`bible`/`treatments`) + 경로 탈출 방지(`..`, `/`, `\\` 거부)로 현재 안전하지만, 삭제 전 사용자 확인이 UI측에서만 수행됨 (main process 미검증).

**권고**: main process에서 `dialog.showMessageBox()` 확인 추가 검토.

---

### [D-T5-005] DESKTOP-GUIDE.md 3건 문서 괴리

**파일**: `geuldobi-desktop/DESKTOP-GUIDE.md`

**괴리**:
1. 파일 구조 설명이 `src/main.js`만 언급 — dead file 2개(루트 main.js, geuldobi-desktop/main.js) 미기재
2. 통신 구조에 렌더러→googleapis.com 직접 fetch 경로 누락
3. WorkGuard IPC 핸들러 2개(`project:list-work-guard-templates`, `project:apply-work-guard-template`) 미기재

---

### [D-T5-006] `stopBackend()` taskkill 비동기 race — 의도치 않은 재시작 가능

**파일**: `geuldobi-desktop/src/main.js` L222-243

**증거**:
```javascript
function stopBackend() {
  const pid = backendProcess.pid;
  spawn("taskkill", ["/pid", String(pid), "/t", "/f"]);
  backendProcess = null;  // L242: taskkill 완료 전 즉시 null
}
```
taskkill 강제 종료 → exit code ≠ 0 → `exit` 콜백의 재시작 로직 트리거 가능. `app.isQuitting` 가드로 `before-quit` 경로는 방어되나, `window-all-closed` → `stopBackend()` 경로에서는 `app.isQuitting`이 아직 false일 수 있음.

**권고**: `stopBackend()` 내부에서 재시작 방지 플래그 설정.

---

### [D-T5-007] `startupTimer` clearTimeout 누락

**파일**: `geuldobi-desktop/src/main.js` L192

**증거**: `setTimeout(15000)` 생성 후 `clearTimeout()` 없음. 백엔드 정상 기동 시에도 15초 후 콜백 실행. `exitCode === null` 가드로 크래시는 없으나, 자동 재시작 시 이전 타이머가 잔존.

**권고**: 백엔드 ready 또는 exit 시 `clearTimeout(startupTimer)`.

---

### [D-T5-008] `smoke_sc.py` — atexit-only config 복구 (비정상 종료 미대응)

**파일**: `/smoke_sc.py` L38-41, L105-108

**증거**:
- `validation.yaml`을 런타임에 직접 수정 (smart_retrieval false→true)
- `atexit.register(_restore_yaml)`로 복구 — SIGKILL/강제종료 시 복구 불가
- `BaseAgent._keys_initialized`, `_current_key_idx`, `_context_caches` private 상태 직접 조작

**위험**: 비정상 종료 시 `validation.yaml`이 변경된 상태로 잔류. BaseAgent 내부 조작은 리팩터링 시 무조건 깨짐.

**권고**: try/finally 래퍼 또는 signal handler 추가.

---

### [D-T5-009] `RESET.py` — SQL 동적 테이블명 + FinanceHUD 미처리 롤백

**파일**: `/RESET.py` L86, L95, L149

**증거**:
- L95: `f"DELETE FROM {t} WHERE ep_num >= ?"` — 테이블명 f-string 삽입 (sqlite_master 출처이므로 현실 공격 벡터 낮음)
- L149: `f"DROP TABLE IF EXISTS [{t}]"` — `t.isidentifier()` 가드는 한국어 테이블명 통과
- L86: `bible_data["MasterBible"]["MartialHUD"]`만 롤백 — 투자물(`FinanceHUD`), 판타지(`FantasyHUD`) 등 미처리
- `nuclear_reset`은 확인 없이 전 테이블 DROP

**권고**: 장르별 HUD 분기 추가. 파라미터화 쿼리로 테이블명 처리 불가하므로 화이트리스트 방식 권장.

---

### [D-T5-010] `tf_c1_patch.py` — 적용 완료 1회성 패치 잔류

**파일**: `/scripts/tf_c1_patch.py`

**증거**: L4에 `C:\Users\wjjo\Desktop\글도비` (다른 사용자 경로) 하드코딩. commit `ddef308`에서 이미 적용 완료. 재실행 시 이중 적용 위험.

**권고**: 삭제.

---

### [D-T5-011] `treatments/defense_defect_engineer_phase0_design.json` 스키마 불일치

**파일**: `treatments/defense_defect_engineer_phase0_design.json`

**증거**: flat 구조 (top-level에 `arcs`, `protagonist` 등 직접 배치), 반면 `chaebol_allowance_zero_phase0_design.json`은 `{project, setting, protagonist, phase0_design}` 4-section wrapper. `scripts/build_bi_from_phase0_and_tr.py` L519의 검증(`"project" in phase0 and "setting" in phase0`)을 defense 파일은 통과 못함.

**운영 영향**: 현재 없음 (별도 빌드 경로). 향후 통합 시 장애 가능.

---

### [D-T5-012] `StoryExpander.save_all()` dict wrapper vs `load_state()` raw load 불일치

**파일**: `modules/core/stage0/story_expander.py` L529, `modules/core/stage0/__init__.py` L718

**증거**:
- `save_all()`: `{"_genre": ..., "total_blocks": N, "treatments": [...]}` dict wrapper로 저장
- `load_state()`: `manager.treatment = json.load(f)` — unwrap 없이 raw load
- concept generation 경로(메뉴 [2])에서 save→load 시 `manager.treatment`에 dict가 들어가 list 기대 코드 오동작

**운영 영향**: 현재 4개 프로젝트는 역설계 경로 사용이므로 미발현. concept generation 경로 사용 시 재현.

---

### [D-T5-013] `test_project` 최소 로그 스키마 — 프로덕션 로그 파싱 검증 갭

**파일**: `projects/test_project/logs/episode_production.jsonl` (30줄)

**증거**: test_project의 `episode_production.jsonl`은 `TF49b_PREFLIGHT` 이벤트만 포함 (5개 키: `ts`, `ep`, `event`, `streak`, `success`). 실제 프로덕션 로그(projects/00)에는 43+ 키 (`round`, `score`, `verdict`, `content_hash`, `artifact_path` 등). 테스트가 test_project 로그에 의존할 경우 프로덕션 로그 파싱 검증 누락.

**운영 영향**: 커버리지 갭 (포맷 위반 아님 — PREFLIGHT는 유효한 subset 이벤트).

---

## P3 — LOW/HYGIENE (9건)

### [D-T5-014] `MagicMock/` 디렉토리 — 테스트 부작용 잔여물

**파일**: `/MagicMock/mock.current_project.paths.root/{object_id}/logs/soft_failures.jsonl`

**원인**: `MagicMock().__str__()` → `"MagicMock"` → `Path("MagicMock/...")` 실제 디렉토리 생성. `soft_failure.py`에 mock 가드 추가 완료(`_coerce_path()`)이므로 재발 없음. 잔여물만 남아 있음.

**권고**: 디렉토리 삭제 + `.gitignore`에 `MagicMock/` 추가.

---

### [D-T5-015] `run_stage4_smoke.py` — manuscripts 테이블 무조건 DELETE

**파일**: `/scripts/run_stage4_smoke.py` L172-173

**증거**: `db.cursor.execute("DELETE FROM manuscripts")` + `db.conn.commit()` — 확인 없이 전량 삭제. `PROJECT_NAME = "코덱스_테스트"` 하드코딩이므로 실 프로젝트 영향은 낮음.

---

### [D-T5-016] `backendRestartCount` 미리셋

**파일**: `geuldobi-desktop/src/main.js` L126

**증거**: 앱 수명 동안 단조 증가만. 성공 기동 시 리셋 없음. Windows 전용이므로 `activate` 이벤트 경로는 사실상 미사용.

**권고**: `startBackend()` 성공 시 `backendRestartCount = 0` 리셋 추가 (방어적).

---

### [D-T5-017] chaebol batch candidate==fixed 전량 동일 (디스크 낭비)

**파일**: `treatments/chaebol_allowance_zero_batch_{001~024}_candidate.json` + `_fixed.json`

**증거**: 24쌍 전부 바이트 동일. 감사 프로세스에서 수정 불필요 판정 시 candidate→fixed 복사는 정상 workflow. ~1.2MB 중복.

---

### [D-T5-018] defense_defect_engineer preprocess 디렉토리 구조 미비

**파일**: `treatments/preprocess/defense_defect_engineer/`

**증거**: template에는 `00_brief/`~`07_archive/` + `docs/` 14개 하위 디렉토리, defense에는 root JSON 4개만. 작업 진행 중 상태.

---

### [D-T5-019] preprocess JSON 스키마 template 상이

**파일**: `treatments/preprocess/defense_defect_engineer/material_bundle_summary.json` 등

**증거**: template 대비 4필드 누락, 6필드 추가. 작품별 확장/변형은 설계 의도. schema validation 없는 수동 프로세스.

---

### [D-T5-020] temp 파일 2건 (Desktop) 삭제 대상

**파일**:
- `geuldobi-desktop/temp-electron-loadcheck.js` (14줄)
- `geuldobi-desktop/temp-electron-paths.js` (7줄)

**증거**: untracked 1회성 디버그 스크립트.

---

### [D-T5-021] Defense block_id 제로패딩 불일치

**파일**: `treatments/defense_defect_engineer_block_*_candidate.json` (12개)

**증거**: Defense block candidates는 `"Block 01"`, `"Block 02"` 제로패딩 형식 사용. 반면 `story_expander.py` L414/L434는 `f"Block {start_block}"` (패딩 없음: `"Block 1"`, `"Block 2"`). `extend_treatment()` L432-436에서 exact string match로 block_id를 검증하므로, defense treatment를 `story_expander`에 넣으면 불일치.

**운영 영향**: defense block candidates는 독립 설계 산출물이므로 현재 영향 없음. 통합 시 주의.

---

### [D-T5-022] Defense block candidates 단일 블록 배열 — enrichment 파이프라인 거부

**파일**: `treatments/defense_defect_engineer_block_*_candidate.json` (12개)

**증거**: 각 파일이 단일 블록을 `[{...}]` 배열로 래핑. `main_a.py` L1310에서 `len(treatment_blocks) < 2` 시 enrichment를 skip하므로, 이 파일들은 `_enrich_treatment_blocks()`를 통과하지 못함.

**운영 영향**: defense blocks는 pre-enriched 설계 산출물이므로 enrichment 파이프라인 대상 아님. 누군가 오인하여 투입 시 skip됨.

---

## 삭제 권고 파일 목록

### 즉시 삭제 (untracked, 프로덕션 무관)
| # | 파일 | 사유 |
|---|------|------|
| 1 | `MagicMock/` (전체) | 테스트 부작용 잔여물 |
| 2 | `main.js` (루트) | splash 로드 테스트 1회성 |
| 3 | `geuldobi-desktop/main.js` | src/main.js 구버전 복사본 |
| 4 | `temp-electron-paths.js` (루트) | 디버그 프로브 |
| 5 | `geuldobi-desktop/temp-electron-paths.js` | 디버그 프로브 |
| 6 | `geuldobi-desktop/temp-electron-loadcheck.js` | 디버그 프로브 |
| 7 | `temp-proc-poll.ps1` | 프로세스 폴링 디버그 |
| 8 | `temp-proc-poll-oswarn.ps1` | OS 경고 폴링 디버그 |
| 9 | `temp-proc-trace.ps1` | WMI 이벤트 추적 디버그 |
| 10 | `temp-run-packaged.ps1` | 패키지 실행 테스트 |
| 11 | `temp-run-packaged-ascii.ps1` | ASCII 경로 패키지 테스트 |
| 12 | `tmp_utf8_check.py` | UTF-8 쓰기 테스트 5줄 |
| 13 | `generate_empire_reborn_tr70.py` | 산출물 이미 존재, 1회성 |
| 14 | `scripts/tf_c1_patch.py` | 적용 완료 패치 (다른 PC 경로 하드코딩) |

### .gitignore 추가 권고
| 패턴 | 사유 |
|------|------|
| `MagicMock/` | MagicMock `__str__` path 생성 재발 방지 |

---

## Electron 보안 종합 점검

| 항목 | 상태 |
|------|------|
| `nodeIntegration: false` | **PASS** — mainWindow + splashWindow 모두 |
| `contextIsolation: true` | **PASS** — mainWindow + splashWindow 모두 |
| `contextBridge` 사용 | **PASS** — `exposeInMainWorld("geuldobiDesktop", {...})` |
| `webSecurity` | **PASS** — 기본값(true) 유지 |
| Remote module | **PASS** — 미사용 |
| CSP | **PARTIAL** — `unsafe-inline` + `googleapis.com` 잔류 |
| IPC 채널 1:1 대응 | **PASS** — 27개 채널 preload↔main 전량 확인 |
| 경로 탈출 방지 | **PASS** — `..`, `/`, `\\` 거부 + folder 화이트리스트 |

---

## DB 스키마 정합성

- 4개 프로젝트(00/01/03/0w) DB 스키마 동일
- `db_manager.py` CREATE TABLE 정의 31개 테이블 전량 존재
- `npc_history` 10컬럼, `manuscripts` 5컬럼 (`hud_snapshot` 포함) 정확히 일치
- **PASS** — 이상 없음

---

## 3PASS 오탐 제거 로그

| 서브태스크 | PASS1 | PASS2 제거 | 최종 확정 | 오탐률 |
|-----------|-------|-----------|----------|--------|
| Sub-A (Scripts+Root+MagicMock) | 33건 | 27건 | 6건 (+삭제목록) | 82% |
| Sub-B (Desktop Electron) | 32건 | 21건 | 11건 | 66% |
| Sub-C (Treatments+Projects) | 70건 | 65건 | 5건 | 93% |
| **합계** | **135건** | **113건** | **22건** | **84%** |

### 주요 오탐 제거 사유
- FP-1 (의도적 설계): canary 스크립트 private method 호출, repair_tr 덮어쓰기
- FP-2 (테스트 검증): DB 스키마 정합성, treatment block 필수 필드
- FP-3 (호출자 추적): backfill_quality_sidecars DBManager API, slash_bot import
- FP-4 (교차 확인): subprocess 체인 안전성, preload splash 공유
- FP-5 (스타일 차이): smoke 스크립트 private import, settings.json 무검증
