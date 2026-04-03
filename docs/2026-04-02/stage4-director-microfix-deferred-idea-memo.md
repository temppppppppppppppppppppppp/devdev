Date: 2026-04-02
Status: deferred-idea
Path: `docs/2026-04-02/stage4-director-microfix-deferred-idea-memo.md`

# Answer First

`Director-authored micro-fix`는 검토할 가치가 있는 아이디어다.

다만 지금 당장 execution SSOT로 승격할 본선은 아니다.

현재 판단:

- 아이디어 차원에서는 유효
- 범위를 아주 좁게 자르지 않으면 위험
- 지금은 `memo-only defer`로 보관

# Idea

현재 구조는 아래처럼 분리돼 있다.

- Director: 판정
- Chief Writer / patch lane: 수정 실행

그런데 runtime에서 반복적으로 드러난 문제는,

- Director가 문제를 정확히 안다
- `PASS_WITH_FIX` 또는 strong advisory까지 올린다
- 그런데 downstream `fix_pack` 또는 patch lane이 수렴에 실패한다

이 경우 `Director가 초국소 수정만 직접 제안/생성`하는 보조 경로를 두면 churn을 줄일 가능성이 있다.

# Intended Scope

허용 가능한 범위는 매우 좁아야 한다.

- `local_phrase`
- `local_sentence`
- bounded proper noun correction
- bounded continuity wording correction
- bounded opening/closing bridge wording correction

즉 `micro-fix`만 허용한다.

# Explicit Non-Goals

아래는 금지다.

- 세계관 팩트 수정
- 인물 속성 덮어쓰기
- 관계도 재작성
- 구조적 scene rewrite
- blueprint 재설계
- Director가 최종 판정권 + 수정권 + 재판정권을 무제한으로 동시에 독점하는 구조

# Why It Is Deferred

1. provenance가 흐려질 수 있다.
   Director가 판정과 수정을 동시에 하면 audit/readability가 나빠질 수 있다.

2. 현재는 Stage4 contract와 fix-pack substrate를 먼저 닫는 편이 우선순위상 맞다.

3. 이 아이디어를 너무 빨리 넣으면 시스템적 개선 대신 detector/arbiter가 임시로 다 때우는 구조가 될 수 있다.

# Minimal Safe Shape If Revisited Later

나중에 다시 검토한다면 최소한 아래 조건이 필요하다.

1. advisory-only 또는 bounded execution flag
2. `director_authored_micro_fix` provenance 명시
3. `local_phrase / local_sentence`로만 scope 제한
4. fact ownership mutation 금지
5. 기존 patch lane보다 우선이 아니라 bounded fallback으로만 사용

# Recommendation

지금은 구현하지 않는다.

기억만 남긴다.

- 이름: `Stage4 director-authored micro-fix`
- 분류: deferred idea
- 상태: memo-only

# 3-Pass Audit

Pass 1. Structure/Scope
- memo-only deferred idea로 한정
- execution SSOT 승격 금지 명시

Pass 2. Evidence/Consistency
- 최근 Stage4 fix-pack / PWF churn 관찰과 정합
- 현재 governance와 충돌하는 지점 명시

Pass 3. Execution/Readability
- why deferred / safe shape / non-goals 분리
- active queue 미편입 방침 명확

Confidence: `96%`
