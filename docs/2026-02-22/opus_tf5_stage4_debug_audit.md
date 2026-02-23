# Opus TF-5: Stage 4 Debug Audit (TF-B)

> 감사일: 2026-02-22
> 범위: `modules/core/stage4_orchestrator.py`, `modules/core/stage4_context_builder.py`, `modules/core/stage4_interview_round.py`, `modules/core/stage4_post_processor.py`, `modules/domain/agents/chief_writer.py`, `modules/domain/agents/chief_writer_context.py`, `modules/domain/agents/chief_writer_quality.py`
> 호출 추적 보강: `modules/core/context_advisor.py`, `modules/models/blueprint.py`, `modules/domain/agents/three_phase_blueprint_generator.py`
> 방법: 수동 라인 단위 검토 (Read/cat), 호출자 → 피호출자 계약 추적

## Executive Summary

| 위험도 | 건수 |
|--------|------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 2 |
| LOW | 0 |

### [B-1] Manager 비동기 타임아웃 시 정산 결과가 조용히 유실됨 — HIGH
- **위치**: `modules/core/stage4_post_processor.py:165`, `modules/core/stage4_post_processor.py:299`, `modules/core/stage4_post_processor.py:316`, `modules/core/stage4_post_processor.py:319`
- **코드 인용**:
```python
audit = {}
...
if _bible_future is not None:
    raw_audit = _bible_future.result(timeout=120)  # 최대 2분 대기
...
except Exception as mgr_err:
    self.ctx.ui.log(f"      ⚠️ Manager 호출 실패: {str(mgr_err)[:50]}")

new_lore = audit.get("new_lore", {}) if isinstance(audit, dict) else {}
```
- **현상**: Manager future가 120초를 넘기면 예외로 빠지고 `audit`는 `{}` 상태로 유지된다. 이후 정산 파이프라인은 빈 `audit`를 정상값처럼 사용해 Bible/State 갱신을 진행한다.
- **재현 시나리오**: 외부 LLM 응답 지연으로 `update_state_and_lore_v20()`이 120초 초과 시, Stage 4는 실패로 중단하지 않고 빈 정산 결과로 후처리를 계속한다.
- **영향**: 에피소드별 상태 정산(`new_lore`, `knowledge_map_updates`, `state_updates`, `causal_links`)이 누락되어 연속성 데이터가 손실된다(침묵형 품질 저하).
- **수정 제안**:
```python
except TimeoutError:
    raw_audit = self.ctx.agents["manager"].update_state_and_lore_v20(...)
```
또는 타임아웃 시 명시적으로 `process_pass_result`를 실패 처리해 불완전 정산 커밋을 막는다.

### [B-2] Post-select 역사 충돌 검사에서 Tier2(11~30화) 요약이 파싱되지 않음 — MEDIUM
- **위치**: `modules/core/stage4_context_builder.py:386`, `modules/core/stage4_interview_round.py:718`, `modules/core/stage4_interview_round.py:908`, `modules/core/stage4_interview_round.py:915`
- **코드 인용**:
```python
# stage4_context_builder.py
_tier2_parts.append(f"[EP {_ep_no} summary] {_summary[:500]}")

# stage4_interview_round.py
_m = _re_hist.match(r"^\[[^\d]*(\d+)[^\]]*\]\n", _block)
...
if not _ms_history_for_check:
    for _prev_ep in range(max(1, next_ep - 30), next_ep):
```
- **현상**: Tier2 요약 포맷은 `]` 뒤가 공백+본문(`... summary] 텍스트`)인데, 파서는 `]` 다음에 줄바꿈(`\n`)이 있어야만 매칭한다. 그래서 Tier2 블록이 history 리스트에 들어가지 않는다.
- **재현 시나리오**: 장기 연재(ep 31+)에서 `_prev_manuscripts_text`에 Tier1(최근 10화 전문)+Tier2(11~30화 요약)가 같이 있을 때, 파서가 Tier1만 읽고 Tier2를 버린다. Tier1이 존재하므로 DB fallback(30화 재조회)도 실행되지 않는다.
- **영향**: 역사 충돌 검사 범위가 의도(최근 30화)보다 축소되어, 11~30화 구간의 모순 탐지율이 떨어진다.
- **수정 제안**:
```python
_m = _re_hist.match(r"^\[[^\d]*(\d+)[^\]]*\]\s*(.*)$", _block)
```
또는 Tier2 생성 포맷을 `[EP N summary]\n...`로 통일한다.

### [B-3] SC-3 Stage4 검색이 `scene_breakdown` dict 계약과 불일치해 장면/NPC 슬롯을 놓침 — MEDIUM
- **위치**: `modules/models/blueprint.py:39`, `modules/core/context_advisor.py:586`, `modules/core/stage4_context_builder.py:91`, `modules/core/stage4_context_builder.py:684`
- **코드 인용**:
```python
# blueprint.py
scene_breakdown: dict = Field(default_factory=dict)

# context_advisor.py
scene_breakdown = blueprint.get("scene_breakdown", [])
if not isinstance(scene_breakdown, list) or not scene_breakdown:
    return ""

# stage4_context_builder.py
scene_blocks = bp.get("scene_breakdown") or bp.get("scenes") or []
if isinstance(scene_blocks, list):
    ...
```
- **현상**: Blueprint 표준 모델은 `scene_breakdown`을 `dict`로 정의하는데, SC Stage4 쿼리 생성/로스터 수집은 `list`만 처리한다. dict 입력이면 장면 기반 쿼리와 장면 기반 NPC 수집이 건너뛰어진다.
- **재현 시나리오**: Stage3 PASS 경로에서 `validate_blueprint()`를 거친 dict형 `scene_breakdown` Blueprint가 Stage4로 들어오면, `plan_stage4_retrieval()`의 `scene_context` 슬롯과 `_collect_npc_roster()`의 scene-derived NPC가 비활성화된다.
- **영향**: SC 검색이 `prev_ending`/`arc_tactical` 중심으로 편향되고, 장면 맥락·NPC 최근 행적 회수가 감소해 Stage4 컨텍스트 품질이 저하된다.
- **수정 제안**:
```python
# dict/list 모두 허용
if isinstance(scene_breakdown, dict):
    iterable = list(scene_breakdown.values())
elif isinstance(scene_breakdown, list):
    iterable = scene_breakdown
```
이 패턴을 `context_advisor._build_scene_query()`와 `stage4_context_builder._collect_npc_roster()`에 동일 적용.

## 비고
- `[Phase A-3]` PASS→REJECT downgrade 분기(`modules/core/stage4_interview_round.py:735`) 자체는 호출 경로상 정상 동작을 확인했다.
- `[Tier4-12]` 하이브리드 lookback의 Tier1 범위 쿼리(`get_manuscripts_range(start, end)`)는 end-exclusive 계약과 호출부가 일치한다.
