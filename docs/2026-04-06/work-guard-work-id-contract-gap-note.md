# WorkGuard `work_id` Contract Gap Note

- Date: 2026-04-06
- Status: active note
- Scope: `work_guards/` library identity contract

## 1. Problem

`work_guard`는 runtime에서 잘 읽히더라도, 기존 계약상 내부에 `work_id`를 꼭 들고 있을 필요는 없었다.

그래서 아래 같은 공백이 있었다.

- 파일명으로는 어떤 작품용 guard인지 보이는데
- YAML 내부에는 작품 식별자가 없을 수 있다
- Stage 0는 템플릿을 그냥 복사하므로, 내용-파일명 불일치를 loader가 직접 잡지 못한다

즉 문제의 본질은 `block id`가 없는 것이 아니라, `work-level identity marker`가 약하다는 점이다.

## 2. Decision

이번 wave에서는 가볍게 아래만 잠근다.

- published work-specific guard는 `work_identity.work_id`를 가능하면 채운다
- `work_identity.work_id`는 scalar string이어야 한다
- `block id` 같은 block-level 식별자는 `work_guard` 정식 계약으로 올리지 않는다

한 줄 요약:

- `work_guard`는 작품 단위 guard다
- `block id`가 아니라 `work_id`를 들고 있으면 충분하다

## 3. Why This Is Low-Priority But Worth Fixing

- 이건 현재 치명 런타임 blocker는 아니다
- Stage 0와 runtime은 여전히 파일 경로 기준으로 동작한다
- 하지만 library가 커질수록 work-specific traceability가 좋아진다
- YAML 내용이 나중에 복사/이동/승격돼도 내부 식별자가 남는다

## 4. Non-Goal

이번 note는 아래를 하지 않는다.

- `work_guard`를 block-level artifact로 바꾸지 않는다
- `block_id`, `arc_id`, `episode_number`를 정식 필수 필드로 올리지 않는다
- Stage 0 browse semantics를 바꾸지 않는다

## 5. Practical Rule

- published work-specific guard:
  - `work_identity.work_id` 채움 권장
  - file stem과 같은 값 권장
- generic default template:
  - 빈 문자열 또는 미지정 허용

즉 운영상으로는:

- `default template`는 느슨하게
- `published work-specific guard`는 `work_id`를 들고 가게 한다
