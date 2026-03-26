# PyArmor 90-Day Expiry Build Note

Date: 2026-03-26
Status: final
Scope: desktop/package build chain에서 PyArmor 만료 제어 가능 여부와 현재 workspace 접점 메모
Canonical Path: `docs/2026-03-26/pyarmor-90day-expiry-build-note.md`

Commit State:
- Baseline Commit: `8ffd512defb17b6ff1c01c7995e9cceab49d81cf`
- Baseline Dirty Summary: `clean`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Short Answer

가능하다.

PyArmor는 공식 문서 기준으로 만료일/유효기간을 지원한다. 실무적으로는 아래 두 방식이 있다.

1. 코드 자체를 만료 포함으로 생성
   - 예: `pyarmor gen -e 90 ...`
   - 빌드 시점부터 90일 유효
2. outer key(`pyarmor.rkey`)에 만료를 분리
   - 예: `pyarmor gen --outer ...` 후 `pyarmor gen key -e 90`
   - 나중에 키만 교체해 연장하거나 재발급하기 쉽다

## 2. Current Workspace Context

현재 desktop release chain의 primary contract는 `source_bundle_primary`다.

- `build/build_release.ps1`
  - `backend.exe`를 PyInstaller로 만들고
  - `main_a.py + modules + config + ...`를 `dist/engine`에 source bundle로 stage한 뒤
  - Electron installer를 만든다
- `geuldobi-desktop/DESKTOP-GUIDE.md`
  - 현재 배포 구조도 `backend.exe + engine source bundle + embedded python`으로 설명한다

즉 현재 정식 build path는 `engine.exe` 독립 배포가 아니라 `source bundle` staging 쪽이다.

다만 workspace에는 PyArmor 접점이 이미 있다.

- `build/engine.patched.spec`
  - PyInstaller spec 안에 `apply_pyarmor_patch()`가 들어 있다
- `.pyarmor/pack`
  - 로컬 PyArmor pack 산출물 흔적이 존재한다

Inference:

- PyArmor는 이 repo에서 완전히 미도입 상태가 아니라, 적어도 한 번은 `engine` 쪽 obfuscation/packing 실험을 한 흔적이 있다
- 하지만 현재 공식 release path인 `build/build_release.ps1`에는 아직 PyArmor 단계가 연결돼 있지 않다

## 3. 90-Day Expiry Design Options

### Option A. Obfuscated source bundle with embedded expiry

개념:

- 현재 `dist/engine` source bundle을 PyArmor로 난독화해서 stage
- 만료도 같은 산출물에 포함

장점:

- build flow가 단순하다
- 배포물 하나로 끝난다

단점:

- 90일 연장 시 보통 재빌드/재배포가 필요하다
- 현재 `source_bundle_primary` 계약과 어떻게 정렬할지 별도 검토가 필요하다

### Option B. Outer key expiry on top of obfuscated runtime

개념:

- obfuscated runtime과 별도로 `pyarmor.rkey`를 생성
- `pyarmor gen key -e 90`로 90일 만료를 건다

장점:

- 기간 연장 시 키만 교체하는 운영이 가능하다
- trial/demo/기간제 배포에 더 적합하다

단점:

- key 배포/교체 경로를 운영 설계해야 한다
- 설치 경로, onefile/onedir, Electron resource layout에 맞는 key search path를 맞춰야 한다

## 4. Time Source Tradeoff

PyArmor 만료는 시간 기준을 어떻게 잡느냐가 중요하다.

- `-e .90`
  - 로컬 시스템 시간 기준 90일
  - 오프라인 배포는 편하지만, 사용자 PC 시간 조작 우회에 약하다
- `-e 90`
  - 네트워크 시간 기준 90일
  - 로컬 시계 되돌리기 우회에 더 강하다
  - 대신 시간 조회 실패/네트워크 제약 상황을 고려해야 한다

운영 권장:

- 내부 테스트/오프라인 배포: 로컬 시간 기준도 가능
- 외부 배포/기간제 체험판: 네트워크 시간 기준 쪽이 더 안전

## 5. Recommended Direction For This Repo

현재 repo 기준 추천 순서는 아래다.

1. 먼저 공식 release path에 PyArmor를 정식 연결할지 결정
   - 현재는 `build/build_release.ps1`가 정식 경로이고, 여기에 PyArmor 단계가 없다
2. 기간제 배포가 목적이면 outer key 방식을 우선 검토
   - 재배포보다 키 갱신이 운영상 유리하다
3. 시간 조작 우회를 신경 쓰면 네트워크 시간 기준을 우선 검토
4. 정식 연결 전에는 `engine.patched.spec`와 `.pyarmor/pack`을 reference artifact로만 취급
   - 현재 build SSOT는 아니다

짧게 말하면:

- "90일 만료 가능 여부"는 `예`
- "지금 build chain에 바로 붙어 있나"는 `아니오`
- "이 repo에서 제일 현실적인 형태"는 `정식 build_release 경로 + PyArmor outer key 만료`다

## 6. Risks and Guardrails

- PyArmor를 붙여도 완전한 복제 방지는 아니다
- 로컬 시간 기준 만료는 시스템 시간 조작으로 우회될 수 있다
- 네트워크 시간 기준은 연결 실패/방화벽/시간 서버 의존성을 고려해야 한다
- 기존 desktop runtime contract, packaged resource inventory, smoke gate와 정합성을 같이 봐야 한다
- 현재 workspace의 PyArmor registration/activation artifact는 operator-only 민감 자료로 취급하는 것이 안전하다

## 7. If Implemented Later

실행 순서 메모:

1. `build/build_release.ps1` 앞단 또는 engine staging 직전에 PyArmor step 삽입
2. packaged resource inventory에 runtime/key artifact 반영
3. desktop smoke gate에 "만료 전 실행" proof 추가
4. 별도 bounded test로 "만료 후 실패" 동작 확인
5. `geuldobi-desktop/DESKTOP-GUIDE.md`에 운영 절차 반영

## 8. Sources

- PyArmor documentation, `--expired` / key generation / outer key support:
  - https://pyarmor.readthedocs.io/_/downloads/en/v9.2.0/pdf/
- PyArmor CI/license notes:
  - https://pyarmor.readthedocs.io/en/latest/how-to/ci.html

3-pass audit status: complete
Estimated confidence: `0.97`
