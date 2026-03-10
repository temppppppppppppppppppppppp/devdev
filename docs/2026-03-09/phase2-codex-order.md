
# Phase 2 코덱스 오더 — PC-1-A + QI-1-A2 + QI-1-A3

> ⚠️ **반드시 UTF-8 인코딩으로 읽으세요.** 모든 파일은 UTF-8입니다.
> 작성일: 2026-03-09
> 전제: Phase 1 구현 완료 (PC-1-C/D + QI-1-A1/A3min/A4/A5/A6)
> 테스트 기준선: 3,696 passed (기존 실패 2건 test_process_runner.py 제외)

---

## 범위

| 명세 | 항목 | 위험도 | 요약 |
|------|------|--------|------|
| PC-1 | **PC-1-A** | MED | DEFAULT_EP_COUNT 5→4 + YAML 3곳 + 하드코딩 폴백 11파일 20곳 |
| QI-1 | **QI-1-A2** | MED | ending_hook 리터럴 매칭 → 키워드 매칭 전환 |
| QI-1 | **QI-1-A3** | LOW | PatternTracker 엔딩 문구 추적 (Phase 1에서 minimal 완료, 나머지 보강) |

---

## Step 1: PC-1-A — ep_count 기본값 5→4 + SSOT 정리

### Step 1-A: 핵심 상수 변경 (2파일 2곳)

| # | 파일 | 위치 | 현재 | 변경 |
|---|------|------|------|------|
| 1 | `modules/core/constants.py` | L241 | `DEFAULT_EP_COUNT = 5` | `DEFAULT_EP_COUNT = 4` |
| 2 | `modules/core/constants.py` | L328 | `EPISODES_PER_ARC = 5` | `EPISODES_PER_ARC = 4` |

### Step 1-B: YAML 프롬프트 권장값 조정 (2파일 3곳)

| # | 파일 | 위치 | 현재 | 변경 |
|---|------|------|------|------|
| 3 | `config/prompts/analyst.yaml` | L291 | `Blitz(3~4화), Standard(5화), Epic(5~6화)` | `Blitz(3화), Standard(4화), Epic(5~6화)` |
| 4 | `config/prompts/analyst.yaml` | L352 | `Blitz(3-4화) / Standard(4-5화) / Epic(5-6화)` | `Blitz(3화) / Standard(3-4화) / Epic(5-6화)` |
| 5 | `config/prompts/ensemble.yaml` | L86 ep_count 설명 | `3~6 중 사건 밀도에 맞게 결정` | `3~6 중 결정 (4화 권장, 5화 이상은 사건 밀도 충분한 경우만)` |

### Step 1-C: 하드코딩 `5` 폴백 → `Stage2Limits.DEFAULT_EP_COUNT` (11파일 16곳 + except 5곳 = 21곳)

> ⚠️ 각 파일에 `from modules.core.constants import Stage2Limits` import가 필요할 수 있음. 기존 import 확인 후 추가.

| # | 파일 | 위치 | 현재 | 변경 |
|---|------|------|------|------|
| 6 | `modules/models/arc.py` | L198 | `ep_count: int = 5` | `ep_count: int = Stage2Limits.DEFAULT_EP_COUNT` |
| 7 | `modules/domain/agents/arc_ensemble.py` | L248 | `.get("ep_count", 5) if isinstance(curr_block, dict) else 5` | `.get("ep_count", Stage2Limits.DEFAULT_EP_COUNT) if isinstance(curr_block, dict) else Stage2Limits.DEFAULT_EP_COUNT` |
| 8 | `modules/domain/agents/arc_ensemble.py` | L805 | `.get("ep_count", 5)` | `.get("ep_count", Stage2Limits.DEFAULT_EP_COUNT)` |
| 9 | `modules/domain/agents/arc_ensemble.py` | L811 | `ep_count = 5` (except) | `ep_count = Stage2Limits.DEFAULT_EP_COUNT` |
| 10 | `modules/domain/agents/arc_draft_validator.py` | L415 | `.get("ep_count", 5)` | `.get("ep_count", Stage2Limits.DEFAULT_EP_COUNT)` |
| 11 | `modules/domain/agents/arc_draft_validator.py` | L417 | `ep_count = 5` (except) | `ep_count = Stage2Limits.DEFAULT_EP_COUNT` |
| 12 | `modules/domain/agents/blueprint_constraint_compiler.py` | L56 | `.get("ep_count", 5)` | `.get("ep_count", Stage2Limits.DEFAULT_EP_COUNT)` |
| 12b | `modules/domain/agents/arc_draft_validator.py` | L509 | `.get("ep_count", 5)` | `.get("ep_count", Stage2Limits.DEFAULT_EP_COUNT)` |
| 13 | `modules/domain/agents/continuity_arc.py` | L255 | `.get("ep_count", 5)` | `.get("ep_count", Stage2Limits.DEFAULT_EP_COUNT)` |
| 14 | `modules/domain/agents/continuity_arc.py` | L257 | `ep_count = 5` (except) | `ep_count = Stage2Limits.DEFAULT_EP_COUNT` |
| 15 | `modules/domain/agents/unified_arc_validator.py` | L241 | `.get("ep_count", 5)` | `.get("ep_count", Stage2Limits.DEFAULT_EP_COUNT)` |
| 16 | `modules/domain/agents/unified_arc_validator.py` | L243 | `ep_count = 5` (except) | `ep_count = Stage2Limits.DEFAULT_EP_COUNT` |
| 17 | `modules/domain/agents/unified_blueprint_validator.py` | L218 | `.get("ep_count", 5)` | `.get("ep_count", Stage2Limits.DEFAULT_EP_COUNT)` |
| 18 | `modules/core/services/state_service.py` | L74 | `else 5` | `else Stage2Limits.DEFAULT_EP_COUNT` |
| 19 | `modules/core/services/state_service.py` | L76 | `ep_count = 5` (except) | `ep_count = Stage2Limits.DEFAULT_EP_COUNT` |
| 20 | `modules/core/stage4_context_builder.py` | L540 | `.get("ep_count", 5)` | `.get("ep_count", Stage2Limits.DEFAULT_EP_COUNT)` |

### Step 1-D: 프롬프트 하드코딩 동적화 (2파일 4곳)

| # | 파일 | 위치 | 현재 | 변경 |
|---|------|------|------|------|
| 21 | `state_locked_arc_generator.py` | L95 | `"5개 에피소드를 하나의 Arc로 통합하세요."` | `f"{Stage2Limits.DEFAULT_EP_COUNT}개 에피소드를 하나의 Arc로 통합하세요."` (**주의**: `ARC_SYNTHESIS_PROMPT`는 dead code — SSOT 일관성용 변경) |
| 22 | `state_locked_arc_generator.py` | L113 | `"ep_count": 5,` | `"ep_count": {Stage2Limits.DEFAULT_EP_COUNT},` |
| 23 | `state_locked_arc_generator.py` | L117 | `"5개 에피소드 본문 통합"` | `f"{Stage2Limits.DEFAULT_EP_COUNT}개 에피소드 본문 통합"` |
| 24 | `narrative_structure_analyzer.py` | L26 | `"아래 5개 에피소드 비트에서"` | 수량 한정어 제거: `"아래 에피소드 비트에서"` |

### Step 1-E: 테스트 업데이트 (1파일 1곳)

| # | 파일 | 위치 | 현재 | 변경 |
|---|------|------|------|------|
| 25 | `tests/test_pydantic_models.py` | L49 | `assert arc.ep_count == 5` | `assert arc.ep_count == 4` |

---

## Step 2: QI-1-A2 — ending_hook 리터럴 매칭 → 키워드 매칭 전환

### 변경 대상: `modules/domain/agents/chief_writer_quality.py` `_check_ending_hook_presence()`

**현재 (L714-715)**:
```python
key_fragment = ending_hook[:20]
if key_fragment not in tail:
    return [{"type": "missing_ending_hook", ..., "severity": "high"}]
```

**변경** (`import re`는 L7에 이미 존재):
```python
keywords = [w for w in re.findall(r"[가-힣]{2,}|[a-zA-Z]{3,}", ending_hook) if len(w) >= 2]
top_keywords = keywords[:5]
if len(top_keywords) < 2:
    return []  # 키워드 부족 → 검사 스킵
matched = sum(1 for kw in top_keywords if kw in tail)
if matched < 2:
    return [{"type": "missing_ending_hook", ..., "severity": "medium"}]  # high→medium
```

**핵심 변경점**:
- 앞 20자 리터럴 매칭 → 핵심 키워드 2~5개 추출, 2개+ 매칭 시 PASS
- severity `high` → `medium` 하향 (CW 자유도 확보)
- 키워드 2개 미만이면 검사 스킵 (너무 짧은 ending_hook)

---

## Step 3: QI-1-A3 보강 — PatternTracker 엔딩 문구 to_summary_text 반영

Phase 1에서 `recent_ending_texts` 필드 추가 + `build_report()` 수집은 완료.
남은 작업: `to_summary_text()`에서 `recent_ending_texts` 요약 출력.

**변경 대상**: `modules/core/pattern_tracker.py` `to_summary_text()` 메서드

**추가**:
```python
if self.recent_ending_texts:
    lines.append("【직전 엔딩】 " + " / ".join(f"'{t[-30:]}'" for t in self.recent_ending_texts[-3:]))
```

---

## 체크리스트

### 구현 전 확인
- [ ] `constants.py` L241, L328 현재 값이 `5`인지 확인
- [ ] `arc.py` L198이 Pydantic 모델 필드인지, `Stage2Limits` import 가능한지 확인
- [ ] 11파일 각각에 `Stage2Limits` import 존재 여부 확인 → 없으면 추가
- [ ] `state_locked_arc_generator.py` L95/113/117에서 `ep_count` 변수 스코프 확인 (f-string 접근 가능?)
- [ ] `chief_writer_quality.py` 상단에 `import re` 존재 여부 확인

### 구현 중 확인
- [ ] Step 1-A: `constants.py` 2곳 변경 완료
- [ ] Step 1-B: `analyst.yaml` 2곳 + `ensemble.yaml` 1곳 변경 완료
- [ ] Step 1-C: 11파일 20곳 전량 변경 완료 (import 포함)
- [ ] Step 1-D: `state_locked_arc_generator.py` 3곳 + `narrative_structure_analyzer.py` 1곳 변경 완료
- [ ] Step 1-E: 테스트 1곳 변경 완료
- [ ] Step 2: `_check_ending_hook_presence()` 키워드 매칭 전환 완료
- [ ] Step 3: `to_summary_text()` 엔딩 문구 요약 추가 완료

### 구현 후 검증
- [ ] `pytest tests/ -q` → 기존 3,696 passed 이상 유지 (regression 0건)
- [ ] `ruff check modules/ config/` → 0 violations
- [ ] `grep -rn "ep_count.*= 5\b\|get.*ep_count.*5" modules/ models/` → 잔여 하드코딩 0건
- [ ] `grep -rn "5개 에피소드" modules/` → 잔여 하드코딩 0건
- [ ] `_check_ending_hook_presence` 에서 `ending_hook[:20]` 리터럴 매칭 코드 완전 제거 확인

### 롤백 계획
- **Step 1 롤백**: `constants.py` 2곳 + YAML 3곳 + 11파일 20곳 + 프롬프트 4곳 + 테스트 1곳 원복 (git revert 1 commit)
- **Step 2 롤백**: `chief_writer_quality.py` 1곳 원복
- **Step 3 롤백**: `pattern_tracker.py` 1곳 원복
- 전체 롤백: `git revert` 단일 커밋

---

## 주의사항

1. **Pydantic 모델 `arc.py`**: `ep_count: int = Stage2Limits.DEFAULT_EP_COUNT` — Pydantic Field default에 상수 참조가 가능한지 확인. `from modules.core.constants import Stage2Limits`가 순환 import을 유발하지 않는지 확인. 문제 시 `ep_count: int = 4` 리터럴로 대체.
2. **`state_locked_arc_generator.py` 프롬프트**: f-string 내부에 `ep_count` 변수가 스코프에 있는지 확인. 없으면 `Stage2Limits.DEFAULT_EP_COUNT` 직접 사용.
3. **`stage2_orchestrator.py` L20**: `DEFAULT_EP_COUNT = VolumeSettings.EPISODES_PER_ARC` alias는 **수정 불필요** — `VolumeSettings.EPISODES_PER_ARC` 변경 시 자동 연동.
4. **기존 프로젝트 호환성**: DB에 `ep_count` 저장된 Arc는 영향 없음. fallback 경로만 5→4.
