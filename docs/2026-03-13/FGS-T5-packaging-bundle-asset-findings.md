# FGS-T5 Packaging Bundle Asset Findings

> 작성일: 2026-03-13
> 상태: `PASS3 complete`
> 범위: release build, packaged runtime bundle, asset inventory, docs/build coherence

## 조사 범위

- `geuldobi-desktop/package.json`
- `build/build_release.ps1`
- `build/backend_entry.py`
- `geuldobi-desktop/DESKTOP-GUIDE.md`
- `dist/engine`
- `geuldobi-desktop/dist/win-unpacked/resources`
- `geuldobi-desktop/src/sprites`
- `UI`

## PASS 1 사실 수집

- package build는 `../dist/backend`, `../dist/engine`, `../python-embed`를 extra resource로 포함한다.
- `build_release.ps1`는 backend.exe를 만든 뒤 `Sync-EngineBundle`로 `main_a.py`, `modules`, `config`, `datasets`, `libraries` 등을 `dist/engine`으로 복사한다.
- `backend_entry.py`는 frozen 모드에서 `GEULDOBI_ENGINE_ROOT=resources/engine`, `GEULDOBI_PYTHON_PATH=resources/python-embed/python.exe`를 주입한다.
- `src/main.js`는 packaged 모드에서 `GEULDOBI_ENGINE_EXE=resources/engine/engine.exe`까지 추가로 주입한다.
- 실제 파일시스템에는 `dist/engine/main_a.py`가 존재하고, `geuldobi-desktop/dist/win-unpacked/resources/engine/`에도 source bundle이 존재한다.
- `DESKTOP-GUIDE.md`는 여전히 `engine.exe`, `소스 코드 비공개`, `PyInstaller 바이너리` 모델을 전면 설명한다.

## PASS 2 교차 검증

- build script와 packaged resources inventory는 `engine.exe`가 아니라 source-tree engine bundle을 기준으로 맞물린다.
- `process_runner._resolve_launch_command()`는 `GEULDOBI_ENGINE_EXE`가 존재하지 않으면 warning 후 `python main_a.py` fallback을 사용한다.
- `tests/test_process_runner.py`도 이 fallback을 정상 경로로 검증한다.
- `UI/` 폴더는 대량 자산 archive지만 runtime 참조나 shipping evidence는 확인되지 않았다. live asset은 `geuldobi-desktop/src/sprites`다.

## PASS 3 오탐 제거

- `FGS-T5-H1`: packaged project root split이 아직 열려 있다
  - 판정: `rejected`
  - 이유: explicit `GEULDOBI_PROJECTS_ROOT` contract와 관련 테스트가 현재는 해당 drift를 닫고 있다.
- `FGS-T5-H2`: `UI/` archive가 실제 패키지에 실린다
  - 판정: `rejected`
  - 이유: shipping pattern과 runtime 참조 증거를 찾지 못했다.

## 확정 findings

### FGS-T5-001

- Severity: `P1`
- 현상 요약: 릴리스 문서와 실제 패키징 산출물이 `engine.exe 비공개 바이너리` vs `source-tree engine bundle`로 정면 충돌한다.
- 코드 근거:
  - `geuldobi-desktop/package.json:39-56`
  - `build/build_release.ps1:27-64`
  - `build/build_release.ps1:113-117`
  - `build/backend_entry.py:19-25`
- 보조 근거:
  - `dist/engine/main_a.py` 실존
  - `geuldobi-desktop/dist/win-unpacked/resources/engine/main_a.py` 실존
  - `geuldobi-desktop/DESKTOP-GUIDE.md:4`, `:17`, `:24-25`는 `소스 코드 비공개`, `engine.exe`를 설명
- counter-evidence review:
  - 현재 빌드는 동작 자체를 위해 source bundle + embedded python 구조를 선택한 것으로 보인다.
  - 그러나 이 경우 문서의 배포 모델과 confidentiality 설명은 더 이상 참이 아니다.
- 상태: `confirmed`
- 권장 후속 조치:
  - 문서와 빌드 모델을 하나로 통일
  - 실제 목표가 source-closed distribution이면 engine packaging 전략을 재설계
  - 목표가 source bundle이면 guide에서 `engine.exe`와 `소스 코드 비공개` 문구 제거

### FGS-T5-002

- Severity: `P2`
- 현상 요약: packaged main process는 `resources/engine/engine.exe`를 env로 주입하지만, 현재 빌드 산출물은 그 파일을 만들지 않아 every-launch fallback 경로가 정상 경로가 됐다.
- 코드 근거:
  - `geuldobi-desktop/src/main.js:167`
  - `modules/api/process_runner.py:190-196`
  - `build/build_release.ps1:27-64`
- 보조 근거:
  - `dist/engine`와 `win-unpacked/resources/engine` inventory에는 `engine.exe`가 없다.
  - `tests/test_process_runner.py`는 missing `engine.exe` fallback을 expected behavior로 고정한다.
- counter-evidence review:
  - 즉시 런타임 failure는 아니다.
  - 그러나 main process env, build output, runner warning semantics가 한 단계 어긋난 상태다.
- 상태: `confirmed`
- 권장 후속 조치:
  - `GEULDOBI_ENGINE_EXE`를 실제 산출물에 맞게 제거/수정하거나
  - build에서 정말 `engine.exe`를 생산하도록 계약을 맞춘다

## 기각 findings

- packaged root split persists
- `UI/` archive ships with desktop runtime

## coverage gap / open question

- packaged installer를 실제 실행해 source bundle fallback 로그와 first-run UX를 검증한 증거는 없다.

## PASS 요약

- PASS1 후보 4건
- PASS2 제거 2건
- 최종 2건
