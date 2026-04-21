# 2026-04-21 Context Snapshot: `00_260421` Supervised Runs And Push Readiness

## Scope

- 대상: 시스템 트랙 기준 `00_260421`의 `Stage 2 / Stage 3` supervised run 진행 상태, 관련 root-fix, 현재 미해결 이슈, 커밋/푸시 직전 브랜치 상태
- 포함:
  - direct supervised runner 추가 및 사용 상태
  - `Stage 2 -> Arc 5` 확장 결과
  - `Stage 3 -> ep17`까지 저장 결과
  - `ep18` 실패 원인에 대한 현재 판정
  - `main` 직접 푸시 가능성에 대한 로컬 확인 결과
- 제외:
  - 작품 품질 자체에 대한 서사 감리 결론
  - `Stage 4` 진행 여부 판단
  - GitHub branch protection의 서버측 강제 정책에 대한 단정

## Current State

- `Stage 2`는 direct supervised run으로 `Arc 5`까지 확장 완료
  - 근거: [stage2_direct_supervised_result.json](/c:/Users/wjjo/Desktop/글도비/projects/00_260421/logs/stage2_direct_supervised_result.json)
- `Stage 3`는 direct supervised run 기준 `ep17`까지 저장 완료
  - 생성 파일:
    - [blueprint_0014.txt](/c:/Users/wjjo/Desktop/글도비/projects/00_260421/plans/blueprints/blueprint_0014.txt)
    - [blueprint_0015.txt](/c:/Users/wjjo/Desktop/글도비/projects/00_260421/plans/blueprints/blueprint_0015.txt)
    - [blueprint_0016.txt](/c:/Users/wjjo/Desktop/글도비/projects/00_260421/plans/blueprints/blueprint_0016.txt)
    - [blueprint_0017.txt](/c:/Users/wjjo/Desktop/글도비/projects/00_260421/plans/blueprints/blueprint_0017.txt)
- `ep18`은 supervised cap `5` 내에서 실패했고 아직 저장되지 않음
  - `blueprint_0018.txt` 없음
  - 근거: [stage3_direct_supervised_result.json](/c:/Users/wjjo/Desktop/글도비/projects/00_260421/logs/stage3_direct_supervised_result.json)

## What Changed

- `PASS_WITH_FIX`가 실제 local repair contract를 아래 runtime까지 전달하지 못하던 `Stage 3` 계약 결함 보정
  - [director_ensemble.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/director_ensemble.py)
- 상대 월 표현(`2월 초`, `2월 말`, `4월 중순`)을 잘못 파싱하던 timeline validator 보정
  - [unified_blueprint_validator.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py)
- `Stage 2` direct supervised runner 추가
  - [run_stage2_direct_supervised.py](/c:/Users/wjjo/Desktop/글도비/scripts/run_stage2_direct_supervised.py)
- `Stage 3` direct supervised runner 추가 및 사용
  - [run_stage3_direct_supervised.py](/c:/Users/wjjo/Desktop/글도비/scripts/run_stage3_direct_supervised.py)
- 관련 테스트 보강
  - [test_director_modules.py](/c:/Users/wjjo/Desktop/글도비/tests/test_director_modules.py)
  - [test_unified_blueprint_validator_lane_c.py](/c:/Users/wjjo/Desktop/글도비/tests/test_unified_blueprint_validator_lane_c.py)

## Open Issue: `ep18`

현재 판정은 `전부 drift`도 아니고 `전부 진짜 위반`도 아니다.

### 1. Continuity / Start Location

- 이 축은 현재 authority 기준으로는 실제 충돌이다.
- [blueprint_0017.txt](/c:/Users/wjjo/Desktop/글도비/projects/00_260421/plans/blueprints/blueprint_0017.txt) 종료 위치는 `여의도 한미증권 본점 한시우 전용 좌석`
- 반면 `Arc 5` authority payload는 `ep18` 시작을 `서울 강남, SW인베스트먼트 오피스 대표실`로 시작시킨다.
- 따라서 `bridge` 없이 곧바로 넘어가면 validator가 `위치 불연속`을 잡는 것이 자연스럽다.

### 2. `arc_timeline`

- 이 축은 drift/authority 오염 가능성이 높다.
- `project_data.db`의 `anchors.key='arcs'` 안 `Arc 5` timeline numeric field는 `2000-09-01 ~ 2000-12-31`로 들어가 있다.
- 같은 payload의 설명/본문은 `2006년 9월`, `2006년 12월` 축을 말한다.
- 즉 숫자 year와 narrative description이 서로 충돌한다.

요약:

- `continuity` = 현재 계약 충돌
- `arc_timeline` = 현재 metadata drift 의심

## Benchmark / Logging Readiness

- 지금 원천 로그만으로도 `S2/S3/S4` 평균 시간 추세 비교를 시작할 수 있다.
- 특히 `S3`, `S4`는 이미 충분히 읽힌다.
- `S2`는 가능하지만 `whole-arc wall-clock`이 다소 재구성형이다.
- 따라서 지금 단계에서 대공사보다는 `기존 sink 활용`이 우선이다.

## Push Readiness

- 현재 브랜치: `main`
- 추적 브랜치: `origin/main`
- 확인 시점 기준 로컬 브랜치 상태는 `origin/main`과 동기화된 상태였음
- 원격:
  - `origin https://github.com/temppppppppppppppppppppppp/devdev.git`
- 로컬 드라이런 확인:
  - `git push --dry-run origin main`
  - 결과: `Everything up-to-date`

이 결과가 의미하는 것:

- 최소한 현재 로컬 인증/remote 경로/branch 명 자체는 정상이다.
- 다만 `새 커밋이 있는 상태에서의 main 직접 write`는 실제 push 전까지 100% 단정할 수는 없다.
- 현 시점 로컬 근거만 보면 `main에 바로 시도해도 되는 상태`로 본다.

## Commit Scope Note

이번 `전량 커밋` 범위에는 코드 변경뿐 아니라 현재 워크트리의 untracked 문서/운영 파일도 포함된다.

- `.github/ISSUE_TEMPLATE/`
- `.github/PULL_REQUEST_TEMPLATE/`
- `docs/2026-04-21/` 신규 문서들
- `ops/` 하위 신규 운영 파일들
- 신규 supervised runner 스크립트들
- 루트의 untracked `.xlsx` 파일 1개

## 3-Pass Audit

### Pass 1. Structure / Scope

- 문서 타입을 `context snapshot`으로 고정
- 범위를 `run 상태 + root-fix + ep18 open issue + push readiness`로 제한
- narrative 감리 결론은 제외

### Pass 2. Evidence / Consistency

- run 결과는 `result.json`과 실제 `blueprint_0014~0017.txt` 존재 기준으로 확인
- `ep18` 미생성은 `blueprint_0018.txt` 부재와 result summary로 확인
- `continuity` 판단은 `blueprint_0017.txt` 실물 기준
- `arc_timeline drift` 판단은 `project_data.db -> anchors['arcs']` numeric year 기준
- `main` 푸시 확인은 `git branch -vv`, `git remote -v`, `git push --dry-run origin main` 기준

### Pass 3. Execution / Readability

- 다음 행동이 바로 보이도록 `open issue`와 `push readiness`를 분리
- 과한 서사 해설 대신 운영 판단만 남김
- 실제 커밋 전 체크 포인트를 `Commit Scope Note`로 명시

## Confidence

- 추정 확신도: `97%`
- 남은 불확실성:
  - `main`의 서버측 보호 규칙은 실제 write push 전에는 최종 확정 불가
  - `ep18 continuity`를 어디서 풀지(`Arc 5 authority 수정` vs `ep18 bridge 보강`)는 아직 미결
