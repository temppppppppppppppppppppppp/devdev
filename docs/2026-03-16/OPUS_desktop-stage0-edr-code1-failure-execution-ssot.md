# Desktop Stage 0 edr Code:1 Failure — Execution SSOT

Date: 2026-03-16
Status: ready (패치 금지 턴 — 다음 턴에서 실행)
Canonical Path: `docs/2026-03-16/OPUS_desktop-stage0-edr-code1-failure-execution-ssot.md`
Temp Mirror Path: `docs/temp/OPUS_desktop-stage0-edr-code1-failure-execution-ssot.md`
Source Survey Docs: `docs/2026-03-16/OPUS_desktop-stage0-edr-code1-failure-full-survey.md`
Evidence Artifacts: `docs/2026-03-16/OPUS_desktop-stage0-edr-code1-failure-evidence.txt`

Commit State:
- Baseline Commit: `5a017766`
- Baseline Dirty Summary: `dirty: 2 files`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

---

## Intent

Packaged desktop app에서 `/run` 디스패치된 `main_a.py` subprocess가 `ModuleNotFoundError`로 즉사하는 문제를 수정하여, 모든 Stage의 desktop 실행을 정상화한다.

---

## Baseline Facts

1. `python-embed/python.exe` (Python 3.12)의 `python312._pth` 파일이 스크립트 디렉터리를 `sys.path`에 추가하지 않음
2. `process_runner._build_env()`가 `PYTHONPATH`를 설정하지 않음
3. `main_a.py`에 자체 `sys.path` bootstrap 코드 없음
4. `backend_entry.py`는 L21-23에서 `sys.path.insert(0, engine_root)` 수행하지만, 이 코드는 subprocess에 전달되지 않음

---

## Execution Tranches

### Tranche 1: CRITICAL — sys.path 수정 (1곳)

**선택지 A (추천): `process_runner._build_env()`에 PYTHONPATH 주입**

파일: `modules/api/process_runner.py`
위치: `_build_env()` 메서드 (L775-803)
변경: `env["PYTHONPATH"] = os.environ.get("GEULDOBI_ENGINE_ROOT", "")` 추가

```python
# L783 이후에 추가:
engine_root = os.environ.get("GEULDOBI_ENGINE_ROOT")
if engine_root:
    env["PYTHONPATH"] = engine_root
```

- 장점: main_a.py 수정 불필요, 영향 범위 최소
- 단점: GEULDOBI_ENGINE_ROOT가 미설정된 dev 환경에서는 무효 (하지만 dev에서는 CWD=프로젝트루트이므로 문제 없음)

**선택지 B: `main_a.py` 상단에 self-bootstrap**

파일: `main_a.py`
위치: L6 부근 (`import sys` 이후)
변경:

```python
# Engine root self-bootstrap for embedded Python distributions
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)
```

- 장점: 모든 실행 컨텍스트에서 동작
- 단점: main_a.py 수정 필요

**추천: 선택지 A + B 모두 적용** (belt-and-suspenders)

### Tranche 2: HIGH — preload.js 모듈 번들 수정

파일: `geuldobi-desktop/src/preload.js`
문제: L6에서 `require("./desktop_control_plane_contract")` → app.asar에 미포함
수정 방향:
- 빌드 스크립트에서 `desktop_control_plane_contract.js`를 app.asar에 포함
- 또는 preload.js에서 require 실패 시 graceful fallback (이미 부분적으로 존재)
- 빌드 파이프라인 확인 필요: `package.json`의 `files` 또는 `electron-builder.yml`

### Tranche 3: LATENT — python-embed 패키지 보충

파일: `python-embed/Lib/site-packages/`
누락: `anthropic`, `openai`, `tiktoken` (최소)
수정: desktop installer 빌드 시 `pip install` 목록에 추가
시점: Tranche 1 수정 후 실제 LLM 호출까지 도달 시 재검증

---

## Side-Effect Map

| Tranche | File Write | DB | Log | UI | Rollback | Cache |
|---|---|---|---|---|---|---|
| T1 (PYTHONPATH) | None | None | None | None | env var 제거로 복원 | None |
| T2 (preload) | app.asar rebuild | None | None | splash 정상화 | asar 재빌드로 복원 | None |
| T3 (packages) | pip install | None | None | None | pip uninstall로 복원 | None |

---

## Acceptance Criteria

### T1
- [ ] `python-embed/python.exe -u engine/main_a.py`가 `ModuleNotFoundError` 없이 실행
- [ ] `POST /run key=0 sub_key=1` 시 세션 로그 생성 확인
- [ ] `projects/edr/`에 `config/`, `project_data.db` 등 정상 생성 확인
- [ ] 기존 `projects/test` 프로젝트의 기동도 정상 확인 (회귀 없음)

### T2
- [ ] electron-main.log에서 `module not found: ./desktop_control_plane_contract` 에러 소멸
- [ ] splash 화면의 `getSplashConfig` 에러 소멸

### T3
- [ ] LLM 호출 시 `ModuleNotFoundError` 미발생 (anthropic/openai provider)

---

## Verification Plan

1. **T1 단위 검증**: embedded Python으로 main_a.py import 테스트 → `ModuleNotFoundError` 부재 확인
2. **T1 통합 검증**: packaged desktop app에서 `/run` 디스패치 → 세션 로그 생성 + 프로젝트 구조 생성 확인
3. **T2 빌드 검증**: app.asar에 `desktop_control_plane_contract.js` 포함 확인
4. **T3 런타임 검증**: Stage 4 실행 시 LLM 호출 정상 동작 확인

---

## Non-Goals / Guardrails

- 이번 SSOT는 desktop packaged app의 subprocess launch 경로만 다룸
- CLI 직접 실행 (`python main_a.py`)은 이미 정상 동작하므로 변경 대상 아님
- `backend.exe` (PyInstaller 번들) 자체는 정상 동작하므로 변경 대상 아님
- python-embed의 `python312._pth` 직접 수정은 portable하지 않으므로 비추천
