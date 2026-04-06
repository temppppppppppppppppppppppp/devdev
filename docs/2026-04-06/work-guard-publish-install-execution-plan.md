# WorkGuard Publish/Install Execution Plan

- Date: 2026-04-06
- Status: active operating plan
- Scope: no-code publish/install contract for material-side-complete `work_guard`
- Goal: let material-side-finished `work_guard` leave draft state and become selectable in Stage 0

## 1. Goal

재료 사이드에서 `work_guard`를 끝까지 만들고 감리까지 통과했다면, 결과가 `docs/...` 안 draft에만 남지 않고 실제 Stage 0 선택 라이브러리까지 가야 한다.

이번 계획의 핵심은 이거다.

- `draft`는 `docs`에 남긴다
- `publish`는 Stage 0이 바로 볼 수 있는 `work_guards/` 가시 경로로 보낸다
- `install`은 필요할 때 `{project}/config/work_guard.yaml`로 보낸다

한 줄 요약:

- `docs draft -> work_guards visible publish -> project install`

## 2. Current Reality

현재 시스템은 이미 아래 세 surface를 갖고 있다.

### 2.1 Library lane already exists

- `work_guards/`는 Stage 0에서 선택적으로 가져오는 작품가드 라이브러리다

Evidence:

- [work_guards/README.md](../../work_guards/README.md)

### 2.2 Install lane already exists

- 실제 런타임 적용 파일은 언제나 `{project}/config/work_guard.yaml`이다

Evidence:

- [work_guards/README.md](../../work_guards/README.md#L5)
- [stage0.md](../../docs/stage_map/stage0.md#L64)
- [main_a.py](../../main_a.py#L1344)

### 2.3 Stage 0 template apply surface already exists

- Stage 0 CLI와 desktop 둘 다 `work_guards/` 템플릿을 project config로 적용하는 surface를 이미 갖고 있다

Evidence:

- [modules/core/stage0/__init__.py](../../modules/core/stage0/__init__.py#L138)
- [modules/core/stage0/__init__.py](../../modules/core/stage0/__init__.py#L182)
- [geuldobi-desktop/src/main.js](../../geuldobi-desktop/src/main.js#L1029)
- [geuldobi-desktop/src/main.js](../../geuldobi-desktop/src/main.js#L1168)

### 2.4 Visibility constraint matters

- 현재 Stage 0 browse는 deep recursive lane을 기본 전제로 하지 않는다
- 따라서 publish 결과는 Stage 0이 바로 볼 수 있는 경로에 있어야 한다

즉 새로운 lane를 발명할 필요는 없고, 이미 있는 library lane에 맞는 publish 계약만 잠그면 된다.

## 3. Recommended Model

추천 모델은 `draft -> audit -> publish -> optional install`이다.

### Step A. Draft

- 배치 생성 결과를 `docs/.../work_guard_<batch>/`에 저장
- 이 단계는 review, diff, verdict 기록용이다

### Step B. Audit / Freeze

- `WG-V1`, `WG-V2`, 필요 시 `WG-V3`로 감리한다
- unresolved authority conflict나 `HOLD/REJECT`는 publish하지 않는다

### Step C. Publish

- `WG-V2 PASS` 난 final yaml을 Stage 0 가시 경로인 `work_guards/`로 보낸다
- 이 단계에서 library asset이 된다

### Step D. Install

- 필요한 프로젝트에 `{project}/config/work_guard.yaml`로 복사한다
- 이 단계에서 runtime live asset이 된다

추천 정책:

- `publish`는 material-side standard
- `install`은 작품/project 지정 이후의 operator step

즉:

- `standard producer -> publish`
- `runtime consumer -> install when needed`

## 4. Publish Target Rule

최종 publish는 아래 두 경로만 표준으로 인정한다.

### 4.1 Preferred lane

- `work_guards/<genre>/<work_id>.yaml`

예:

- `work_guards/investment/office_checkup_next_day.yaml`
- `work_guards/wuxia/wuxia_heavenly_physician.yaml`

### 4.2 Fallback lane

- `work_guards/<work_id>.yaml`

이 fallback은 아래 경우에 사용한다.

- genre lane이 아직 정리되지 않았을 때
- family/genre label이 애매할 때
- Stage 0 가시성이 최우선일 때

### 4.3 Not Recommended

- `work_guards/generated/...`
- Stage 0 browse가 기본으로 보지 않는 deep nested lane

핵심은 이거다.

- `publish path must be Stage 0-visible`

## 5. Why This Model Fits The Existing System

### 5.1 `docs` draft가 필요한 이유

- batch review와 verdict 근거를 남기기 좋다
- 억지 PASS를 막는다
- authority note를 같이 보관할 수 있다

### 5.2 `work_guards/` publish가 필요한 이유

- Stage 0이 이미 library root를 여기로 본다
- desktop / CLI template apply surface가 이미 여기를 사용한다
- 파이프라인 코드를 안 건드리고도 operator UX를 바로 활용할 수 있다

### 5.3 `{project}/config` install이 마지막이어야 하는 이유

- 런타임 적용은 실제 project 대상이 정해졌을 때만 필요하다
- 잘못된 project에 덮어쓰는 위험이 있다
- install은 publish보다 더 보수적이어야 한다

## 6. Publish Gate

`publish`는 아래 조건에서만 수행한다.

- `WG-V2 verdict == PASS`
- hard gate key 전부 존재
- authority conflict unresolved 상태가 아님
- operator가 `freeze-ready`로 판정

즉:

- `HOLD/REJECT` draft는 `docs`에만 남긴다
- `PASS` draft만 `work_guards/` visible lane으로 간다

## 7. Install Gate

`install`은 아래 조건에서만 수행한다.

- publish 완료
- 대상 project가 명확함
- 기존 `{project}/config/work_guard.yaml` 덮어쓰기 정책이 확인됨

권장 overwrite 정책:

- 기본값: 덮어쓰기 금지
- install 대상에 기존 파일이 있으면 stop + report
- 명시적 `force install`일 때만 교체

## 8. Practical Operating Flow

오늘 기준 실무 flow는 이렇게 잠근다.

1. `material_ssot`와 active pitch/phase0 truth에서 `work_guard` draft 생성
2. `docs/.../work_guard_<batch>/`에 draft + verdict 저장
3. `WG-V2 PASS`면 final yaml을 `work_guards/<genre>/<work_id>.yaml` 또는 `work_guards/<work_id>.yaml`로 publish
4. 필요하면 Stage 0 `작품가드 설정`에서 선택해 `{project}/config/work_guard.yaml`로 install

한 줄로 쓰면:

- `material truth -> draft/audit -> Stage 0-visible library publish -> project install`

## 9. Highest-ROI Next Automation

코드화한다면 가장 ROI 높은 순서는 아래다.

1. `draft -> publish` 반자동화
2. publish 시 Stage 0-visible target path 강제
3. install은 나중에 별도 명령으로 유지

이 순서가 좋은 이유:

- publish만 자동화해도 운영 마찰이 크게 줄어든다
- install은 runtime 영향이 직접적이라 더 보수적으로 두는 편이 낫다
- 현재 Stage 0 surface를 그대로 재사용할 수 있다

## 10. Recommended Decision

오늘 기준 추천은 아래다.

### 지금 당장 운영으로 잠글 것

- `WG-V2 PASS` draft는 `work_guards/<genre>/<work_id>.yaml` 또는 `work_guards/<work_id>.yaml`로 publish한다
- `HOLD/REJECT` draft는 `docs`에만 남긴다
- project install은 Stage 0 선택 또는 별도 install step로 둔다

### 다음 wave에서 구현할 것

- `draft -> publish` 반자동화
- publish path validator

### 아직 미룰 것

- publish와 install을 한 번에 자동 수행
- default overwrite install
- Stage 0 browse semantics 변경을 전제로 한 deep lane 설계

## 11. One-Line Conclusion

재료 사이드에서 `work_guard`를 끝까지 밀었다면, 표준 끝점은 `docs`가 아니라 Stage 0이 바로 볼 수 있는 `work_guards/` 가시 경로다.
