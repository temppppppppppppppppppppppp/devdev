# Runtime Warnings 수정 완료 보고 (2026-02-24)

> 프로젝트 0224_2 (투자물) Stage 4 생산 로그에서 발견된 반복 경고 3건 — **전량 수정 완료**

---

## 수정 요약

| # | 경고 | 등급 | 수정 내용 | 상태 |
|---|------|------|---------|------|
| 1 | protagonist_name 주입 실패 | P1 | `HUDKeys.get_protagonist_name()` 5-tier 탐색으로 교체 | **FIXED** |
| 2 | prev_hud 누락 | P1 | `self.ctx.sys.hud.pro_root` → `_cv_context["prev_hud"]` 배선 추가 | **FIXED** |
| 3 | ConsistencyValidator 3 checks skipped | P2 | `karma_matrix` + `villain_context` + `authority_context` 조립 로직 추가 | **FIXED** |

## 수정 파일

| 파일 | 변경 |
|------|------|
| `modules/core/stage4_interview_round.py` | P1×2 + P2×1 context 배선 수정 |
| `tests/test_stage4_cv_context.py` (신규) | 14개 배선 검증 테스트 |
| `tests/integration/test_patch_wiring.py` | 기존 protagonist_name 테스트 2건 Bible 구조 갱신 |

## 검증 결과

- `python -m py_compile`: OK
- `ruff check`: 0 violations
- `pytest tests/test_stage4_cv_context.py -v`: **14 passed**
- `pytest tests/ -q`: **2616 passed, 0 failed**

---

## 상세 수정

### 1. protagonist_name — HUDKeys.get_protagonist_name() (P1)

**이전**: `_mb_root.get("protagonist_name")` / `protagonist_config.name` — 존재하지 않는 경로
**이후**: `HUDKeys.get_protagonist_name(_mb_root, genre_name)` — 5-tier 탐색 (CoreIdentity → 장르HUD → AllHUD → KeyNPCs → 기본값)
- `"주인공"` 기본값 반환 시에도 warning 유지 (실제 이름이 아니므로)

### 2. prev_hud — sys.hud.pro_root 배선 (P1)

**이전**: `_cv_context`에 `prev_hud` 키 없음, `martial_hud: {}` 빈 dict
**이후**: `next_ep > 1`일 때 `self.ctx.sys.hud.pro_root` → `_cv_context["prev_hud"]` + `martial_hud` 동시 채움
- ContinuityValidator 장비/부상/위치 연속성 검증 활성화

### 3. ConsistencyValidator 3 checks (P2)

**karma_matrix**: DB `episode_bibles.karma_matrix` JSON 배열 → NPC별 dict 집계
**villain_context**: `KeyNPCs[]`에서 빌런 키워드 매칭 (사망 빌런 제외)
**authority_context**: `KeyNPCs[]`에서 상사 키워드 매칭 (사망 여부 반영)

---

## Stage 0~3 전수조사 결과 (참고)

3건 모두 **Stage 4 context 조립 버그**가 근본 원인. 상류 데이터는 정상 존재.

| 런타임 경고 | Stage 0 | Stage 4 |
|-------------|---------|---------|
| protagonist_name | 데이터 정상 | **잘못된 경로** → FIXED |
| prev_hud | 무관 | **배선 누락** → FIXED |
| CV 3 checks | NPC role 비구조화 | **context 미조립** → FIXED (키워드 매칭) |
