# Stage 0 작품가드 · 스타일캐시 보강 실행 SSOT

> 작성일: 2026-03-13
> 상태: 실행 오더 SSOT
> 범위: Stage 0 진입점, 작품가드 입력 경로, 스타일 레퍼런스 캐시 무효화 규칙
> 제외: 실제 코드 수정, UI 개편, 모델 변경

---

## 0. 결론

이번 이슈는 두 개로 보이지만, 실제로는 같은 `Stage 0 준비물 계약` 문제다.

1. `작품가드(work_guard.yaml)`는 백엔드에서 이미 Stage 2~4에 연결돼 있다.
2. 그러나 `언제 넣는가`에 대한 Stage 0 진입점이 없다.
3. `style_guide`는 캐시를 쓰는 구조가 맞다.
4. 그러나 현재 무효화 규칙이 `레퍼런스 txt의 mtime` 위주라서, 사용자가 체감하기엔 “진짜 재분석이 되는지”가 불명확하다.

따라서 본 SSOT는 아래를 고정한다.

- 작품가드는 `BI/TR처럼 별도 소스 폴더`를 두고 Stage 0 세부 옵션에서 import/init 하게 한다.
- 단, 작품가드는 필수 입력이 아니라 선택적 보강물로 유지한다.
- 런타임 소비 경로는 그대로 `{project}/config/work_guard.yaml`로 유지한다.
- 스타일 캐시는 계속 유지하되, `재사용 / 강제 재분석 / 캐시 삭제 후 재생성`이 분명히 구분되도록 Stage 0 옵션과 무효화 규칙을 강화한다.

한 줄 결론:

- **작품가드는 “백엔드 소비는 이미 있음, 입력 타이밍만 없음”**
- **작품가드는 선택적이어야 하며, 없는 상태도 정상 baseline이어야 한다**
- **스타일 캐시는 “이미 캐시 중이나, 무효화 규칙과 사용자 제어가 약함”**

---

## 1. 현재 사실 고정

### 1.1 작품가드의 현재 백엔드 소비 경로

작품가드는 이미 엔진에 연결돼 있다.

- 프로젝트 부팅 시 `{project}/config/work_guard.yaml`이 있으면 `GenreGuard` 위에 `WorkGuard`를 래핑한다.
  - `main_a.py`
- 이후 Stage 2~4에서 아래 방식으로 소비된다.
  - `get_v20_purism_prompt()`를 통한 작품 정체성 규칙 주입
  - `get_retrieval_contract_prompt()`를 통한 retrieval contract 주입
  - `select_retrieval_focus()`를 통한 tracking slot / scene engine / registry profile 선택
  - `get_director_review_advisory()`를 통한 Director open_review/advisory 강화
  - `run_deep_validation()`를 통한 warning-only 검증

핵심 파일:

- `main_a.py`
- `modules/core/genre_guards/work_guard.py`
- `modules/core/stage2_preflight.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/director_auditor.py`

판정:

- 작품가드는 “백엔드에 안 붙어 있다”가 아니라 **“입력 진입점이 뒤에 숨어 있다”**가 맞다.

### 1.2 작품가드의 현재 입력 경로

현재 사용자가 작품가드를 넣는 공식 경로는 사실상 이것뿐이다.

- `{project}/config/work_guard.yaml`을 수동 배치
- 또는 데스크톱 설정 surface를 통해 같은 파일에 write-through

즉:

- Stage 0 준비 단계에서 `BI`, `TR`, `스타일 레퍼런스`처럼 취급되지 않는다
- 그래서 실제 사용자는 “작품가드를 언제 넣는가”를 놓치기 쉽다

### 1.3 스타일 레퍼런스 캐시의 현재 구조

현재 캐시는 실제로 존재한다.

- 공용 장르 캐시:
  - `config/style_references/{genre}/style_guide.json`
- 프로젝트 로컬 산출물:
  - `{project}/stage0_output/style_guide.json`
- DB anchor:
  - `style_guide`

현재 동작:

1. `Stage 0 > 스타일 레퍼런스 분석` 실행
2. `config/style_references/{genre}` 아래 `.txt` 레퍼런스들을 읽음
3. `config/style_references/{genre}/style_guide.json` 캐시가 있고
4. 그 캐시의 mtime이 레퍼런스 `.txt` 최신 mtime보다 같거나 최신이면 캐시 재사용
5. 아니면 실제 재분석 후 캐시 갱신
6. 이후 프로젝트 `stage0_output/style_guide.json`과 DB anchor에도 저장

판정:

- **“이미 만들어 둔 걸로만 쓰는 구조”는 아님**
- **“공용 장르 캐시가 최신이면 재사용”이 맞음**
- **“공용 장르 캐시가 없거나 오래됐으면 진짜 다시 분석”이 맞음**

### 1.4 현재 구조의 사용성 문제

문제는 캐시가 아니라 `사용자가 무엇을 지워야 재분석되는지 알기 어렵다`는 점이다.

- `{project}/stage0_output/style_guide.json`만 지워도 공용 장르 캐시가 살아 있으면 재분석 안 될 수 있다
- `config/style_references/{genre}/style_guide.json`을 지우면 재분석된다
- 레퍼런스 `.txt`를 건드리면 mtime 비교로 재분석된다
- 하지만 분석 프롬프트, 모델 체인, 샘플링 규칙 변경은 자동 무효화 조건이 아니다

---

## 2. 최종 판단

### 2.1 작품가드

`BI/TR처럼 별도 소스 폴더 + Stage 0 세부 옵션` 방향이 맞다.

다만 주의:

- 작품가드는 필수 준비물이 아니다. 없는 프로젝트도 Stage 0~4를 정상 진행할 수 있어야 한다.
- 작품가드의 **실제 런타임 경로는 계속 `{project}/config/work_guard.yaml`** 이어야 한다
- 별도 소스 폴더는 “원본 라이브러리/템플릿/선택지” 역할만 해야 한다

권장 구조:

- 소스 라이브러리:
  - `work_guards/`
  - 필요 시 `work_guards/{genre}/`
- 프로젝트 적용 파일:
  - `{project}/config/work_guard.yaml`

즉:

- `bible/`, `treatments/`처럼 소스 풀을 둔다
- Stage 0에서 필요할 때만 고른 뒤 프로젝트 config로 복사/초기화한다
- 엔진 소비 코드는 건드리지 않는다
- 작품가드가 없으면 `no-work-guard baseline`으로 그대로 진행한다

### 2.2 스타일 레퍼런스 캐시

현재 캐싱 방향 자체는 맞다.  
문제는 “캐시 사용”이 아니라 “캐시 제어가 불명확”한 점이다.

따라서 방향은:

- 캐시는 유지
- 재분석 제어는 강화
- 무효화 규칙은 mtime만 보지 말고 명시적 버전 정보도 본다

즉:

- `캐시를 없애자`가 아니라
- `캐시를 믿되, 강제 재분석 옵션과 무효화 메타를 추가하자`가 맞다

---

## 3. 실행 오더

### R-1. 작품가드 소스 라이브러리 신설

목표:

- 작품가드를 Stage 0 선택형 준비물로 승격

구조:

- 새 소스 폴더 추가
  - 기본안: `work_guards/`
  - 선택안: `work_guards/{genre}/`

정책:

- 여기는 `원본/템플릿/샘플`만 둔다
- 실제 실행 파일은 언제나 `{project}/config/work_guard.yaml`
- work_guard 미선택은 정상 경로이며, 기본 성공 경로를 막지 않는다

### R-2. Stage 0 세부 옵션에 작품가드 추가

목표:

- Stage 0에서 `BI / TR / 스타일` 옆에 `작품가드`도 넣을 수 있게 함

권장 옵션:

1. `작품가드 가져오기`
2. `장르 기본 템플릿으로 초기화`
3. `현재 프로젝트 작품가드 미리보기`
4. `현재 프로젝트 작품가드 삭제`

최소 구현 기준:

- Stage 0 메뉴에 새 세부 선택지 추가
- 선택 결과는 `{project}/config/work_guard.yaml`에 write-through
- 기존 런타임 로드는 변경하지 않음
- 작품가드를 넣지 않고 건너뛰어도 Stage 0 종료와 이후 Stage 2~4 진행이 막히지 않음

### R-3. 스타일 캐시 정책을 Stage 0 옵션으로 노출

목표:

- 사용자가 “이건 캐시 재사용인지, 진짜 재분석인지”를 알 수 있게 함

권장 옵션:

1. `캐시 사용`
2. `캐시 무시하고 재분석`
3. `장르 캐시 삭제 후 재분석`

최소 구현 기준:

- Stage 0 스타일 분석 실행 전에 모드 선택
- 현재 기본값은 `캐시 사용`

### R-4. 스타일 캐시 무효화 규칙 보강

현재 규칙:

- 레퍼런스 `.txt` 최신 mtime > 캐시 mtime 이면 재분석

보강 규칙:

- 아래 메타를 캐시에 같이 저장
  - `analysis_version`
  - `genre`
  - `model family / model id`
  - `sampling policy`
  - `reference file manifest`
  - `prompt contract hash`

재분석 조건:

- 레퍼런스 `.txt` 변경
- 분석 버전 변경
- 프롬프트 계약 변경
- 샘플링 정책 변경
- 사용자가 강제 재분석 선택

### R-5. 캐시 층위 문서화

혼동 방지용으로 문서와 로그에서 아래를 구분해야 한다.

- 공용 장르 캐시:
  - `config/style_references/{genre}/style_guide.json`
- 프로젝트 결과물:
  - `{project}/stage0_output/style_guide.json`
- DB anchor:
  - `style_guide`

핵심 메시지:

- 프로젝트 로컬 파일 삭제와 공용 장르 캐시 삭제는 같은 의미가 아니다

---

## 4. 권장 UX/CLI 의미론

### 4.1 작품가드

Stage 0에서 사용자에게 보이는 의미는 아래처럼 고정하는 편이 좋다.

- `Bible`: 세계관 원천
- `Treatment`: 줄거리 원천
- `Style Reference`: 문체/서술 원천
- `Work Guard`: 작품 정체성/금기/추적 슬롯 원천

즉 작품가드는 `설정 파일`이 아니라 `준비물`로 보여야 한다.

### 4.2 스타일 캐시

Stage 0에서 사용자에게 아래 중 하나로 명확히 보여야 한다.

- `캐시 재사용`
- `강제 재분석`
- `캐시 삭제 후 재생성`

지금처럼 내부적으로만 캐시 히트/미스를 판단하면 사용자가 체감하기 어렵다.

---

## 5. 비목표

이번 오더의 비목표:

- WorkGuard 검증 로직 자체의 내용 확장
- style_guide prompt 내용 재설계
- UI 화면 구조 개편
- Stage 2~4 prompt 리라이트
- 캐시를 완전히 제거하는 설계

즉 이번 오더는 `준비물 진입점`과 `캐시 제어`를 고치는 문서다.

---

## 6. 수용 기준

### 작품가드

- Stage 0에서 작품가드 import/init이 가능하다
- 소스 라이브러리에서 고른 내용이 `{project}/config/work_guard.yaml`에 반영된다
- 엔진은 기존과 같은 경로를 그대로 읽는다

### 스타일 캐시

- 사용자가 캐시 사용/강제 재분석/캐시 삭제 후 재생성을 명시적으로 선택할 수 있다
- 공용 장르 캐시와 프로젝트 로컬 산출물의 차이가 문서와 로그에서 드러난다
- 레퍼런스 파일뿐 아니라 분석 계약 변경도 캐시 무효화 조건으로 다룬다

---

## 7. 최종 판단

이번 이슈의 정답은 아래다.

- 작품가드는 새 검증 로직을 만들 문제가 아니라 **Stage 0 입력 타이밍을 만들어야 하는 문제**
- 스타일 레퍼런스는 새 캐시를 만들 문제가 아니라 **현재 캐시의 무효화 규칙과 사용자 제어를 강화해야 하는 문제**

따라서 구현 우선순위는:

1. `작품가드 소스 폴더 + Stage 0 import/init`
2. `스타일 캐시 모드 선택`
3. `스타일 캐시 무효화 메타 강화`

---

## 8. 근거 문서

- `main_a.py`
- `modules/core/genre_guards/work_guard.py`
- `modules/core/stage0/__init__.py`
- `modules/core/stage0/style_extractor.py`
- `modules/core/stage01_helpers.py`
- `modules/core/stage2_preflight.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/director_auditor.py`
- `docs/stage_map/stage0.md`
- `docs/2026-03-10/TF-work-guard-identity-ssot-plan.md`
- `docs/2026-02-28/TF-31-style-pipeline-audit.md`
- `docs/2026-03-12/ui-feedback-response-survey.md`
- `docs/2026-03-12/ui-structure-overhaul-execution-ssot.md`
