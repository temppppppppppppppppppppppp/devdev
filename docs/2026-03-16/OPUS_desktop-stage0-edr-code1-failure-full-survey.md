# Desktop Stage 0 edr Code:1 Failure — Full Survey

Date: 2026-03-16
Status: final
Canonical Path: `docs/2026-03-16/OPUS_desktop-stage0-edr-code1-failure-full-survey.md`
Evidence: `docs/2026-03-16/OPUS_desktop-stage0-edr-code1-failure-evidence.txt`
Execution SSOT: `docs/2026-03-16/OPUS_desktop-stage0-edr-code1-failure-execution-ssot.md`

Commit State:
- Baseline Commit: `5a017766`
- Baseline Dirty Summary: `dirty: 2 files (0_temp.txt untracked, preload.js untracked)`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

---

## 1. Incident Summary

| Field | Value |
|---|---|
| Time | 2026-03-16 13:06:47 KST (04:06:47 UTC) |
| Action | Stage 0 · 기존 방식 (key=0, sub_key=1) |
| Workspace | `C:\Users\wjjo\Documents\글도비` |
| Project | `edr` (신규, 장르: 투자물) |
| Symptom | `[System] 실행 실패 (code: 1)` after ~4 seconds |
| Run ID | `343432eb-8348-407e-898b-d76b6f33166e` |

---

## 2. Root Cause (Confidence: 99%)

**Embedded Python의 `python312._pth` 파일이 스크립트 디렉터리의 `sys.path` 자동 삽입을 억제하여, `main_a.py`가 자기 자신의 `modules` 패키지를 찾지 못하고 `ModuleNotFoundError`로 즉사한다.**

### Failure Chain

```
desktop UI → POST /run (key=0, sub_key=1, mode=B)
  → ProcessRunner.start()
    → _resolve_launch_command()
      → ["python-embed/python.exe", "-u", "engine/main_a.py"]
    → _build_env()
      → os.environ.copy() (PYTHONPATH NOT set)
    → subprocess spawn (CWD = workspace root)
      → python-embed/python.exe runs engine/main_a.py
        → python312._pth suppresses script-dir in sys.path
        → sys.path = [python312.zip, python-embed/, Lib/site-packages/]
        → engine/ NOT in sys.path
        → main_a.py L99: import modules.core.spinners → ModuleNotFoundError
        → Unhandled exception → exit code 1
```

### 근거

1. **직접 재현**: `python-embed/python.exe -u engine/main_a.py` → `ModuleNotFoundError: No module named 'modules'` (Evidence E8)
2. **sys.path 덤프**: engine/ 디렉터리 부재 확인 (Evidence E9)
3. **python312._pth**: `.` 항목이 CWD가 아닌 python-embed/ 디렉터리로 resolve됨 (Evidence E7)
4. **ProjectContext 미도달**: `projects/edr/`에 하위 디렉터리/DB 전무 (Evidence E3)
5. **세션 로그 부재**: 모든 desktop 발사 run에 대해 세션 로그 미생성 (Evidence E5)
6. **대조군**: `backend_entry.py`는 L21-23에서 engine_root를 `sys.path.insert(0, ...)` 하지만, subprocess로 실행되는 `main_a.py`에는 동일 로직 부재 (Evidence E10)

---

## 3. Failure Phase 특정

| Phase | Reached? | Evidence |
|---|---|---|
| POST /run dispatch | ✅ | electron-main.log: 202 Accepted |
| ProcessRunner subprocess spawn | ✅ | provenance.jsonl: run_id 기록 |
| main_a.py module-level import | ❌ FAIL | No session log, no project files |
| _select_genre() | ❌ | Never reached |
| _select_project() | ❌ | Never reached |
| _bind_selected_project() | ❌ | projects/edr empty |
| ProjectContext.__init__() | ❌ | No config/, no DB |
| Stage 0 menu | ❌ | Never reached |

**실패 지점: `main_a.py` 라인 99, 모듈 수준 import 단계 (boot() 이전)**

---

## 4. Side-Effect Sweep

| Category | Status | Detail |
|---|---|---|
| File writes | ❌ None | `projects/edr/`에 아무 파일도 생성되지 않음 |
| DB writes | ❌ None | `project_data.db` 미생성 |
| JSONL/log/audit sink | ✅ Partial | `control-plane-provenance.jsonl`에 run 기록 (bridge_server 측) |
| Console/UI output | ✅ Partial | `[System] 실행 실패 (code: 1)` (desktop UI) |
| Rollback/retry | N/A | 실패 전 생성물이 없으므로 rollback 대상 없음 |
| Cache/global state | ❌ None | subprocess 즉사로 상태 변경 없음 |
| Config/env/bootstrap | ✅ Env set | `GEULDOBI_ENGINE_ROOT`, `GEULDOBI_PYTHON_PATH` 정상 전달 |

---

## 5. 추가 Findings

### F2. preload.js `desktop_control_plane_contract` 미번들 (HIGH)

- **증상**: 모든 세션에서 `Error: module not found: ./desktop_control_plane_contract`
- **원인**: `geuldobi-desktop/src/preload.js`가 `require("./desktop_control_plane_contract")`하지만, app.asar 빌드 시 이 모듈이 포함되지 않음
- **영향**: `window.geuldobiDesktop` undefined → splash 설정 실패 (`getSplashConfig` 에러)
- **현재 완화**: renderer가 HTTP 직접 호출 fallback으로 동작 (POST /run은 정상 발사)

### F3. 누락 패키지: anthropic, openai (LATENT)

- `python-embed/Lib/site-packages/`에 `anthropic`, `openai` 미설치
- 현재: main_a.py가 L99에서 이미 죽으므로 미노출
- F1 수정 후: LLM 호출 시점에 `ModuleNotFoundError` 재발 예상

### F4. `projects/edr` 고스트 디렉터리 (LOW)

- desktop `project:create` IPC가 `fs.mkdirSync`만 수행
- `ProjectContext`가 실행되지 않아 DB/하위구조 미생성
- 정상 flow에서는 `ProjectContext.__init__`이 하위구조를 생성하므로 설계 의도와 일치
- 다만 subprocess 실패 시 "빈 프로젝트"가 목록에 계속 표시되는 UX 문제 존재

---

## 6. `edr` vs `test` 구조 비교

| Item | projects/edr | projects/test |
|---|---|---|
| config/ | ❌ | ✅ (author_directives.txt) |
| drafts/ | ❌ | ✅ |
| logs/ | ❌ | ✅ (session logs, metrics, error.log) |
| memory/ | ❌ | ✅ |
| plans/ | ❌ | ✅ (arcs/, blueprints/) |
| project_data.db | ❌ | ✅ (897KB) |

`test` 프로젝트는 직접 `python main_a.py` 실행(시스템 Python)으로 정상 bootstrap됨 (12:27 KST 세션 로그 확인). Desktop `/run` 경유 성공 사례는 **없음**.

---

## 7. Regression Surface

1. **`python-embed` sys.path 수정 시**: main_a.py import chain 전체 재검증 필요 (특히 `from google import genai` L97, lazy provider imports)
2. **PYTHONPATH 주입 시**: `_build_env()`만 수정하면 CWD 오염 없이 engine root만 추가 가능
3. **main_a.py sys.path self-bootstrap 시**: 모든 실행 컨텍스트(desktop, CLI, pytest)에서 동작 확인 필요
4. **preload.js 수정 시**: app.asar 빌드 파이프라인에 `desktop_control_plane_contract.js` 포함 여부 확인

---

## 8. Open Questions

1. `backend.exe`(Python 3.11) ↔ `python-embed`(Python 3.12) 버전 차이가 런타임에 문제를 일으킬 수 있는가?
2. `anthropic`/`openai` 패키지 미설치 상태에서 LLM 호출 경로가 정상 동작하는가?
3. desktop installer 빌드 스크립트에서 `python-embed` 패키지 설치 목록은 어디서 관리되는가?
4. `preload.js`의 `desktop_control_plane_contract` 누락은 빌드 스크립트 이슈인가, 의도적 분리인가?
