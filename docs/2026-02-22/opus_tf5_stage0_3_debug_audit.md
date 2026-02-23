# Opus TF-5: Stage 0 + Stage 3 Debug Audit (TF-G)

> 감사일: 2026-02-23  
> 범위: `modules/core/stage0/__init__.py`, `modules/core/stage0/preset_registry.py`, `modules/core/stage0/story_expander.py`, `modules/core/stage0/reverse_expander.py`, `modules/core/stage0/style_extractor.py`, `modules/core/stage3_orchestrator.py`, `modules/core/stage3_context.py`  
> 방법: 수동 라인 단위 검토 (Read/cat), 호출자→피호출자 계약 추적

## Executive Summary

| 위험도 | 건수 |
|--------|------|
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 1 |
| LOW | 0 |

### [G-1] Stage3 DI 콜백 nullable 계약 위반으로 런타임 TypeError 가능 — HIGH
- **위치**: `modules/core/stage3_orchestrator.py:102`, `modules/core/stage3_orchestrator.py:120`, `modules/core/stage3_orchestrator.py:157`, `modules/core/stage3_context.py:60`, `modules/core/stage3_context.py:106`
- **코드 인용**:
```python
# stage3_context.py
get_max_episode_from_manuscripts=None,
get_int_input=None,
...
get_int_input=getattr(app, "_get_int_input", None),
```
```python
# stage3_orchestrator.py
existing_ms_max_ep = ctx.get_max_episode_from_manuscripts()
target_ep = ctx.get_int_input(...)
...
ctx.write_audit_summary("stage3_complete")
```
- **현상**: `Stage3Context`는 콜백 기본값을 `None`으로 허용하지만, 오케스트레이터 본문 일부 경로는 `callable()` 가드 없이 직접 호출한다.
- **재현 시나리오**: SovereignApp 외부 DI/테스트 컨텍스트에서 `_get_int_input` 또는 `_get_max_episode_from_manuscripts` 미주입 상태로 `stage_3_batch_blueprinting()` 실행 시 즉시 `TypeError: 'NoneType' object is not callable`.
- **영향**: Stage 3가 생성 루프 진입 전 크래시하며 Blueprint 배치 생성이 중단된다.
- **수정 제안**:
```python
existing_ms_max_ep = ctx.get_max_episode_from_manuscripts() if callable(ctx.get_max_episode_from_manuscripts) else 0
target_ep = ctx.get_int_input(...) if callable(ctx.get_int_input) else total_planned_ep
if callable(ctx.write_audit_summary):
    ctx.write_audit_summary("stage3_complete")
```

### [G-2] ReverseExpander 배치 병렬 추출이 `prev_state`를 배치 내 모든 화에 동일 적용 — HIGH
- **위치**: `modules/core/stage0/reverse_expander.py:361`, `modules/core/stage0/reverse_expander.py:400`, `modules/core/stage0/reverse_expander.py:402`, `modules/core/stage0/reverse_expander.py:410`, `modules/core/stage0/reverse_expander.py:655`, `modules/core/stage0/reverse_expander.py:660`
- **코드 인용**:
```python
# _extract_single_episode_bible
## 이전 상태
{json.dumps(prev_state.get("hud_snapshot", {}), ensure_ascii=False)[:1000]}
```
```python
# extract_episode_bibles
prev_state = self.episode_bibles[-1] if self.episode_bibles else {}
future_map = {
    pool.submit(self._extract_single_episode_bible, draft, prev_state, schema): draft["ep_num"]
    for draft in batch
}
```
- **현상**: 함수 목적은 "회차별 상태 변화 추출"인데, 배치 병렬 처리 시 배치 내 모든 에피소드가 동일 `prev_state`를 받는다.
- **재현 시나리오**: 배치가 `11~15화`일 때, 12~15화도 모두 10화 상태를 기준으로 추출되어 11화 변화가 반영되지 않는다.
- **영향**: `episode_bibles`, `state_logs`, 이후 Arc 보강(`_enrich_arc_stubs_from_episode_bibles`)의 연속성 데이터가 누적 왜곡된다.
- **수정 제안**:
```python
# prev_state 의존 경로는 배치 내 순차 처리로 전환하거나
# 병렬 1차 추출 후 ep 순서 재보정 단계에서 이전 화 상태를 다시 반영
```

### [G-3] Bible 임포트 시 `_genre` 누락이면 투자물 프리셋으로 강제 귀결 — MEDIUM
- **위치**: `modules/core/stage0/__init__.py:320`, `modules/core/stage0/__init__.py:323`, `modules/core/stage0/__init__.py:326`
- **코드 인용**:
```python
self.genre = self.bible.get("_genre", "")
if not self.genre:
    master = self.bible.get("MasterBible", {})
    self.genre = master.get("_genre", GenreTypes.INVESTMENT)
self.preset_registry = PresetRegistry(base_genre=self.genre)
```
- **현상**: `_genre` 누락 JSON을 임포트하면 자동 감지/중립 모드가 아니라 `investment` 프리셋이 기본 적용된다.
- **재현 시나리오**: 구형/외부 Bible(JSON)에서 장르 메타 누락 시 임포트 직후 HUD/스키마가 투자물 기준으로 초기화된다.
- **영향**: 실제 장르와 다른 필드(`capital`, `portfolio` 등)가 활성화되어 Stage 2~4에서 문맥 오염과 검증 오탐이 발생할 수 있다.
- **수정 제안**:
```python
self.genre = master.get("_genre", "")
if not self.genre:
    self.genre = self.show_genre_menu() or ""  # 또는 detect_genre 경로
```

## 비고
- `reverse_expander.py`의 UTF-8 → CP949 → replace 폴백(`:131-142`, `:194-205`)은 인코딩 복원 관점에서 의도된 방어 로직으로 확인.
- `stage3_orchestrator.py`의 직전 화 Blueprint 필수 중단(`:266-278`)은 파일 내 주석/반환(`break=True`)과 일치하여 의도된 순차 의존성 제어로 판단.
