utf8-hygiene: allow-file -- regex pattern literals contain Korean characters rendered as literal evidence
Date: 2026-03-24
Status: final
Document Type: raw evidence ledger (T4 lane)
Master Report: `docs/2026-03-24/opus-residual/t4-current-episode-extraction.md`

---

# T4 Evidence Ledger: Current-Episode Extraction

## A. `extract_episode_tactical()` — Function Signature and Logic

**Source: `modules/core/tactical_utils.py:31-73`**

```python
def extract_episode_tactical(
    tactical_doc,
    ep_num: int,
    *,
    episode_details=None,
    fallback_full: bool = True,  # <-- default is True
) -> str:
```

Priority chain:
1. `episode_details` — iterates list, matches `item.get("ep_num") == ep_num`
2. Regex — 6 patterns in `_EPISODE_HEADER_PATTERNS`, all anchored on `{ep}` placeholder
3. Fallback — if `fallback_full=True`, returns full `_safe_tactical_str(tactical_doc)`; if False, returns `""`

## B. `_extract_episode_focus()` — Must-Focus Derivation

**Source: `modules/domain/agents/blueprint_constraint_compiler.py:230-268`**

- Calls `extract_episode_tactical(..., fallback_full=False)`
- Falls back to `beat_sequence[arc_position - 1]` if extraction returns empty
- Extracts key_events from content lines (bullet points or 10-100 char lines)
- Returns dict: `{content, key_events[:5], arc_position, arc_title}`

## C. `_resolve_blueprint_arc_focus()` — Blueprint Ensemble Focus

**Source: `modules/domain/agents/blueprint_ensemble.py:215-238`**

Step 1: `constraint_block.get("must_focus", {}).get("content", "")`
Step 2 (fallback): `extract_episode_tactical(...)` — uses default `fallback_full=True`
Step 3: Prepends `episode_details[ep_num]` items as `[{ep_num}화 추가 사건 (Arc 단계 보강)]`
Truncation: `smart_truncate(arc_focus, max_chars=15000, ...)`

## D. Full Caller Inventory

### Callers with `fallback_full=False` (SAFE)

1. **bcc:232** `_extract_episode_focus` — `fallback_full=False`
2. **ci:392** `continuity_inspector.py` — `fallback_full=False`
3. **ca:583** `continuity_arc.py` — `fallback_full=False`
4. **ca:990** `continuity_arc.py` first ep — `fallback_full=False`
5. **ca:996** `continuity_arc.py` last ep — `fallback_full=False`
6. **s4cb:1788** `stage4_context_builder.py` — `fallback_full=False`

### Callers with `fallback_full=True` (default, latent risk)

7. **bp_ens:218** `blueprint_ensemble.py _resolve_blueprint_arc_focus` — True (default), 15000c truncation
8. **s3o:1950** `stage3_orchestrator.py` continuity pins — True (default), no truncation
9. **tpbg:186** `three_phase_blueprint_generator.py` patch mode — True (default), :3000 truncation
10. **pb:691** `prompt_builder.py` Stage 4 context — True (default), :1800 truncation
11. **de:1529** `director_ensemble.py` Director verdict — True (default), :6000 truncation
12. **tot:389** `tree_of_thoughts.py` ToT — True (default), context-dependent truncation
13. **s4o:746** `stage4_orchestrator.py` — True (default), :3000 truncation

## E. `00_001` Episode Details Data

**Source: `projects/00_001/logs/artifacts/stage2/arc_001/attempt_01/final_arc__balanced.json:103-132`**

```json
"episode_details": [
  {"ep_num": 1, "details": ["2024년 고독사 후 2006년 본가 침실에서 눈을 뜸", "18년 치 거시경제 데이터 복기 및 두통 극복"]},
  {"ep_num": 2, "details": ["아버지 한정호의 서재로 호출됨", "형들의 무관심 속에서 그룹 지원을 거절하고 독자적인 투자사 설립 선언"]},
  {"ep_num": 3, "details": ["은행 PB 박성호를 만나 신탁 펀드 및 스폰서십 해지 강행", "자산 20억 원 현금화 완료"]},
  {"ep_num": 4, "details": ["여의도 낡은 오피스텔 계약 및 SW인베스트먼트 설립 완료", "저녁 뉴스에서 이란 핵 문제 보도를 보며 WTI 투자 준비"]}
]
```

All 4 episodes populated with 2 items each. For ep1, extraction returns:
```
- 2024년 고독사 후 2006년 본가 침실에서 눈을 뜸
- 18년 치 거시경제 데이터 복기 및 두통 극복
```

## F. `00_001` Tactical Doc Structure

**Source: `final_arc__balanced.json:363`**

The tactical_doc has clear `제 N화:` headers:
- `제 1화: 깨어난 기억` → [시작 상태] ... [종료 상태]
- `제 2화: 서재의 선언` → [시작 상태] ... [종료 상태]
- `제 3화: 자본금 20억의 무게` → [시작 상태] ... [종료 상태]
- `제 4화: SW인베스트먼트의 탄생` → [시작 상태] ... [종료 상태]

Regex pattern `r"\[제\s*{ep}\s*화[^\]]*\](.*?)(?=\[제\s*\d+\s*화|\Z)"` would NOT match these (no brackets around header). But pattern `r"제\s*{ep}\s*화\s*[:\-\u2013\u2014]\s*(.*?)(?=제\s*\d+\s*화\s*[:\-\u2013\u2014]|\Z)"` (pattern 4) WOULD match `제 1화: 깨어난 기억`.

Even if regex fails, `episode_details` path succeeds first (Priority 1), so regex is never needed.

## G. ep1 Blueprint Overconsumption Evidence

**Source: `projects/00_001/logs/artifacts/stage3/ep_0001/attempt_09/final_blueprint__emotion_focused.json`**

- `ending_state.protagonist_status`: "자본금 20억 확보 및 법인 설립을 완료하고 첫 투자를 목전에 둔 상태"
- This is ep4's end state, not ep1's.
- The `integrated_scenario` describes ALL 4 episodes compressed into ep1: reincarnation, headache, asset liquidation (ep3), office setup + OTP (ep4), news broadcast (ep4), father's study summon (ep2).
- BUT `must_focus` for ep1 contains only "고독사" and "거시경제 데이터" — correctly ep1-scoped.
- The overconsumption comes from other prompt channels, not from the extraction layer.

## H. Regex Pattern Inventory

**Source: `modules/core/tactical_utils.py:6-19`**

| # | Pattern | Example Match | Notes |
|---|---------|---------------|-------|
| 1 | `\[제\s*{ep}\s*화[^\]]*\]` | `[제 1화 제목]` | Bracket-wrapped |
| 2 | `#{{2,3}}\s*제\s*{ep}\s*화` | `### 제1화` | Markdown headers |
| 3 | `\*\*제\s*{ep}\s*화[^*]*\*\*` | `**제1화 제목**` | Markdown bold |
| 4 | `제\s*{ep}\s*화\s*[:\-\u2013\u2014]` | `제 1화: 제목` | Colon/dash separator |
| 5 | `[\(]?제\s*{ep}\s*화[\)]` | `(제1화)` or `제1화)` | Parenthesized |
| 6 | `Beat\s*{ep}\s*:` | `Beat 1:` | English format |

All patterns use `re.DOTALL` and capture content until the next episode header or end of string.
