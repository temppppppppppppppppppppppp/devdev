# 컨텍스트 정상화 플랜 (1M 토큰 기준)
> 작성: 2026-02-27 | 상태: 미실행 | 다음 세션에서 순서대로 실행

## 배경

- Gemini 3.x Pro = 1M tokens 입력 = 한글 약 500K자 (호출 1회 기준)
- ep250 실제 사용량: ~132K자 = ~264K tokens = 1M의 **26%** (74% 미사용)
- 이번 세션 완료: Wave A~E(토큰 제약 수정) + 감리3차(director_mandatory_max 40K→150K 등)

## 이미 완료된 것 (이번 세션)

| 항목 | 변경 |
|------|------|
| `director_mandatory_max` | 40K → 150K |
| `mandatory_context_max` | 80K → 200K |
| `lookback_excerpt_chars` | 500 → 2,000 |
| `lookback_total_chars` | 4K → 15K |
| SC 예산 (stage2/3/4/director) | 20/30/50/20K → 50/80/100/50K |
| `slot_max_chars_default` | 1,500 → 3,000 |
| `director_ensemble.py` blueprint | [:15K] → [:50K] |
| `cross_agent_verifier.py` arc/bp | 12K/18K → 40K/60K |
| `continuity_manuscript.py` blueprint | [:10K] → [:40K] |
| `critic.py` blueprint | [:10K] → [:50K] |
| `stage4_interview_round.py` blueprint_text | [:3K] → [:8K] |
| `stage4_context_builder.py` FactLedger | max_chars=15K → 25K |
| `stage4_context_builder.py` WorldState | max_chars=5K → 10K (2곳) |
| `stage4_context_builder.py` Tier2 summary | [:500] → [:800] |
| `stage4_context_builder.py` Tier3 summary | [:1K] → [:1.5K] |
| `stage4_interview_round.py` director_feedback | [:300] → [:500] |
| Wave B: SC → mandatory_context 앞배치 | _sc_parts 분리 |
| Wave C: director_enabled | false → true |
| Wave D: CW D-Step2 대리만족 주입 | YAML + prompts.py |
| Wave E: state_changes cause 필드 | blueprint_constraint_compiler.py |

---

## 미실행 Phase (다음 세션 실행 대상)

### Phase 1 — Safety Gate (P0, 1줄)

```yaml
# config/system.yaml
api:
  max_context_chars: 450000   # 900000 → 450000
  # 근거: 900K자 × 2tok/char = 1.8M tok > 1M 모델 한계. 게이트 역할 불능.
  # 450K자 = 한글 기준 1M tokens의 90%. 안전 마진 10%.
```

### Phase 2 — Director 모델 업그레이드 (P1)

파일: `config/models.yaml` (존재 여부 확인 후 수정, 없으면 base_agent.py에서 모델명 찾아 수정)

| 에이전트 | 현재 | 변경 | 근거 |
|---------|------|------|------|
| `director` | gemini-2.5-pro | gemini-3.1-pro-preview | 최종 심판관 < CW = 내각제 원칙 위반 |
| `continuity_inspector` | gemini-2.5-pro | gemini-3.1-pro-preview | 250화 연속성 고도 추론 필요 |
| `four_phase_arc_generator.ensemble` | gemini-2.5-pro | gemini-3.1-pro-preview | Arc 방향 결정 = 스토리 핵심 |

Flash군(검증/보조)은 유지.

### Phase 3-A — 250화 연속성 보장 (P1, 코드 6줄)

| 파일 | 현재 | 변경 |
|------|------|------|
| `stage4_context_builder.py` Tier1 에피소드 수 | 10화 | 20화 (파라미터 찾아서 수정) |
| `stage4_context_builder.py` Tier2 `_summary[:800]` | 800 | 2,000 |
| `stage4_context_builder.py` Tier3 `_sum_text[:1500]` | 1,500 | 4,000 |
| `modules/core/world_state.py` `get_summary(max_chars=5000)` 기본값 | 5,000 | 25,000 |

> 변경 후 ep250 예상: ~310K자 = ~620K tokens = 1M의 62%. 38% 여유.

### Phase 3-B — Focus Mode 확장 (P2, 1줄)

```python
# modules/core/stage2_preflight.py L535
minimal_prev_context = enhanced_context[:15000]  # [:2000] → [:15000]
# 근거: 실패 반복 시 컨텍스트를 오히려 줄이는 역설 제거
```

### Phase 4 — 장기 연재 대비 (관찰 대기, 조건부)

ep500+ 시 발생 조건:
- Tier3 Arc 요약 100개+ → 400K자 초과 위험
- 대비: `volume_summary` 계층 활성화 (이미 구현됨, 배선만 확인)

---

## 검증 기준 (각 Phase 후)

```bash
pytest tests/ -q        # 2694 passed 유지
ruff check modules/     # 0 violations
pytest tests/ -k truth_gate -v  # 22 passed
```

## ep 규모별 토큰 예산 (변경 후)

| 에피소드 | 프롬프트 크기 | 토큰(×2) | 1M 대비 |
|---------|------------|---------|--------|
| ep50    | ~180K자    | ~360K   | 36%    |
| ep100   | ~220K자    | ~440K   | 44%    |
| ep150   | ~260K자    | ~520K   | 52%    |
| ep200   | ~290K자    | ~580K   | 58%    |
| ep250   | ~310K자    | ~620K   | 62%    |
| ep300   | ~340K자    | ~680K   | 68%    |
| ep400   | ~390K자    | ~780K   | 78%    | ← Phase 4 검토 시점
