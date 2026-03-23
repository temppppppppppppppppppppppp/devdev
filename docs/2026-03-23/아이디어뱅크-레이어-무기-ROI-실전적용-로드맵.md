# 아이디어 뱅크: 레이어+무기 ROI/실전 적용 가능성 순위 로드맵

> **출처**: `보고서-pass-with-fix-부분수정-메커니즘-분석.md` Part 3
> **작성일**: 2026-03-23
> **목적**: 아이디어를 "실제로 코드에 넣을 수 있는가?" 순으로 정렬

---

## 판별 기준

| 축 | 설명 | 가중치 |
|---|---|---|
| **ROI** | 에피소드당 토큰 절감 × 발생 빈도 | 40% |
| **실전 적용 가능성** | 삽입점 명확성 + 기존 코드 변경량 + 부작용 리스크 | 40% |
| **품질 영향** | 오염 방지 / 정확도 향상 효과 | 20% |

---

## 종합 순위표

| 순위 | ID | 이름 | 분류 | ROI | 적용성 | 품질 | 종합 | 구현 LOC |
|:---:|:---:|------|:----:|:---:|:------:|:----:|:----:|--------:|
| **1** | L-5 | EarlyReturnGate | 레이어 | ★★★★★ | ★★★★★ | ★★★ | **96** | ~80 |
| **2** | L-1+L-4 | DEA + 조사엔진 | 레이어 | ★★★ | ★★★★★ | ★★★★★ | **90** | ~80 |
| **3** | L-1A | SurgicalRewriteLayer | 레이어 | ★★★★ | ★★★★ | ★★★★★ | **88** | ~150 |
| **4** | W-5 | PatchVerifier | 무기 | ★★★★ | ★★★★★ | ★★★ | **85** | ~50 |
| **5** | W-4 | ContradictionIndex | 무기 | ★★★★★ | ★★★ | ★★★★ | **84** | ~250 |
| **6** | L-2 | RegexParser | 레이어 | ★★ | ★★★ | ★★★ | **65** | ~200 |
| **7** | L-3 | EntityMatcher | 레이어 | ★★★ | ★★★ | ★★★★ | **68** | ~120 |
| **8** | W-3 | SceneContextFilter | 무기 | ★★ | ★★★★ | ★★ | **58** | ~130 |
| **9** | L-6 | DeterministicScorer | 레이어 | ★ | ★★★★★ | ★★★ | **55** | ~40 |
| **10** | W-1 | FactDatabase | 무기 | ★★ | ★★ | ★★★★ | **52** | ~200 |
| **11** | W-2 | TemporalValidator | 무기 | ★★ | ★★ | ★★★★ | **50** | ~150 |
| **12** | W-6 | AdvisoryBatcher | 무기 | ★★★★ | ★★ | ★★ | **52** | ~300 |
| **13** | W-7 | FeedbackCompiler | 무기 | ★ | ★★ | ★★★ | **38** | ~100 |

---

## Tier 1: 즉시 착수 (1주 내, 비파괴적)

### #1. L-5 EarlyReturnGate — Advisory LLM skip

**왜 1등인가**: 가장 큰 토큰 절감 (40K-80K/에피) + 삽입이 가장 쉬움 + 부작용 0

**삽입점**: `stage4_interview_round.py` 각 advisory 메서드 최상단

```
현재:
  def _advisory_truth_gate(self, candidates, ...):
      # 바로 LLM 호출
      result = self._tg.validate(manuscript=ms, ...)

변경:
  def _advisory_truth_gate(self, candidates, ...):
      python_result = self._tg.python_precheck(manuscript=ms, ...)
      if not python_result.needs_llm:      # ← gate 추가
          return python_result.as_advisory()
      result = self._tg.validate(manuscript=ms, ...)
```

**적용 대상 Advisory별 gate 조건**:

| Advisory | 파일 위치 | Gate 조건 | 예상 skip률 |
|----------|---------|----------|:----------:|
| TruthGate | L4614 | deceased 0건 + 파괴지역 0건 + 미보유아이템 0건 | 60% |
| NpcDrift | L4651 | 등장 NPC 0명 | 30% |
| NumericDrift | L4701 | `_detect_exponential_growth()` 경고 0건 | 50% |
| Flashback | L4729 | 회상 마커 regex 매치 0건 | 70% |
| InfoParadox | L4796 | knowledge_summary와 원고 교집합 0건 | 40% |
| RelDrift | L4855 | 관계 변화 기록 0건 | 30% |
| LongTermRep | L4903 | scene_type 반복 패턴 < 3회 | 40% |

**구현 전략**: 각 Advisory에 `_python_precheck()` 메서드 추가, 기존 LLM 호출 전에 gate 삽입.
**기존 코드 변경**: 각 advisory 메서드 상단에 5-10줄 추가. 기존 로직 불변.
**테스트**: gate 통과 시 기존 결과와 동일한지 100에피 비교 검증.
**롤백**: gate 조건을 `return True` (항상 LLM 호출)로 변경하면 원상복구.

---

### #2. L-1 DEA + L-4 조사엔진 — entity_ref 무오염 패치

**왜 2등인가**: 오염 0% 보장 (핵심 품질 향상) + 구현 단순 + PASS_WITH_FIX 경험 직접 개선

**삽입점**: `stage4_retry_runtime.py` L416 (`_run_inplace_retry_lane()` 또는 PASS_WITH_FIX 루프 진입 전)

```
현재 (L90-236 execute_pass_with_fix_loop):
  for fix_i in range(max_fix):
      patch_attempt = chief_writer.inplace_patch(...)  # LLM 전문 재생성

변경:
  for fix_i in range(max_fix):
      # L-1 DEA 시도 (entity_ref만)
      if fix_pack.get("target_kind") == "entity_ref":
          dea_result = DEA.apply(current_ms, fix_pack)
          if dea_result is not None:
              dea_result = KoreanParticleEngine.fix_all(dea_result, fix_pack)
              current_ms = dea_result
              continue  # LLM 호출 skip
      # DEA 실패 또는 비 entity_ref → 기존 LLM 패치
      patch_attempt = chief_writer.inplace_patch(...)
```

**필요 데이터** (삽입점에서 이미 사용 가능):
- `current_ms`: 현재 원고 (str) ✓
- `fix_pack`: Director가 발행한 수정 지시 (dict) ✓
- `fix_pack["target_kind"]`: "entity_ref" / "local_phrase" / etc ✓
- `fix_pack["must_fix"]`: `["주혁→강혁"]` 형태 ✓

**DEA 코어 구현** (~50줄):
```python
# modules/core/deterministic_edit.py (신규 파일)

import re

class DeterministicEditApplicator:
    def apply(self, manuscript: str, fix_pack: dict) -> str | None:
        edits = self._parse_must_fix(fix_pack.get("must_fix", []))
        if not edits:
            return None
        result = manuscript
        for old, new in edits:
            if old not in result:
                return None  # 대상 문자열 없음 → LLM 폴백
            result = result.replace(old, new)
        return result

    def _parse_must_fix(self, must_fix: list) -> list[tuple[str,str]] | None:
        edits = []
        for item in must_fix:
            if "→" in item:
                old, new = item.split("→", 1)
                edits.append((old.strip(), new.strip()))
            else:
                return None  # 파싱 불가 → LLM 폴백
        return edits if edits else None
```

**조사 엔진 코어** (~30줄):
```python
# modules/core/korean_particle.py (신규 파일)

class KoreanParticleEngine:
    _PAIRS = [("이","가"),("을","를"),("은","는"),("과","와"),("으로","로"),("아","야")]

    @staticmethod
    def has_jongseong(char: str) -> bool:
        code = ord(char) - 0xAC00
        return 0 <= code and (code % 28) > 0

    def fix_all(self, text: str, fix_pack: dict) -> str:
        for item in fix_pack.get("must_fix", []):
            if "→" not in item:
                continue
            old_name, new_name = [s.strip() for s in item.split("→", 1)]
            if not old_name or not new_name:
                continue
            old_j = self.has_jongseong(old_name[-1])
            new_j = self.has_jongseong(new_name[-1])
            if old_j == new_j:
                continue  # 받침 동일 → 조사 변경 불필요
            for p1, p2 in self._PAIRS:
                wrong = new_name + (p1 if old_j else p2)
                right = new_name + (p2 if old_j else p1)
                text = text.replace(wrong, right)
        return text
```

**기존 코드 변경량**: stage4_retry_runtime.py에 ~15줄 추가 + 신규 파일 2개.
**테스트**: "주혁→강혁" 패턴 단위 테스트 + 조사 보정 테스트 + 통합 테스트.
**롤백**: DEA 분기의 `if` 조건을 `if False:`로 변경하면 원상복구.

---

### #3. L-1A SurgicalRewriteLayer — 문단 단위 수술적 재작성

**왜 3등인가**: L-1 DEA가 못 커버하는 "문장 재작성" 영역 (PASS_WITH_FIX의 ~40%) + 오염 0%

**삽입점**: `chief_writer.py` L1424 (`_attempt_structural_inplace_patch()`) 내부, 또는 병렬 메서드로 추가

```
현재 structural_inplace_patch:
  장면(scene) 단위 분리 → 타겟 장면만 LLM

L-1A 추가:
  target_kind in {local_phrase, local_sentence}일 때
  → 문단(paragraph) 단위 분리 → 타겟 문단만 LLM
```

**기존 scene 분리 메커니즘 재사용**:
- `_build_structural_patch_plan()` (L1424-1480): scene_ids + target 식별
- 이 패턴을 paragraph 레벨로 축소하면 됨

**삽입 방식**: `_attempt_structural_inplace_patch()` 앞에 paragraph-level 시도 추가
```python
# chief_writer.py, inplace_patch() 메서드 내부
def inplace_patch(self, *, original_manuscript, director_feedback, fix_pack, ...):
    # Phase 0: L-1 DEA (entity_ref)
    if fix_pack.get("target_kind") == "entity_ref":
        ...  # 이미 stage4_retry_runtime에서 처리

    # Phase 1: L-1A Surgical (local_phrase / local_sentence)
    if fix_pack.get("target_kind") in ("local_phrase", "local_sentence"):
        surgical = self._attempt_paragraph_surgical_patch(
            original_manuscript, fix_pack, director_feedback)
        if surgical is not None:
            return [{"manuscript": surgical}]

    # Phase 2: 기존 structural (scene_model)
    structural = self._attempt_structural_inplace_patch(...)
    if structural:
        return structural

    # Phase 3: 기존 whole-text inplace
    ...
```

**구현 핵심** (~120줄):
- 문단 분리: `re.split(r"\n\s*\n", text)` (빈 줄 기준)
- 타겟 식별: `fix_pack["patch_targets"]` 문자열이 포함된 문단 인덱스
- LLM 호출: 타겟 문단 + 전후 1문단 (boundary context)만 전송
- Splice: `result_paragraphs[idx] = llm_result`

**기존 코드 변경량**: chief_writer.py에 메서드 1개 추가 (~120줄) + 라우팅 분기 ~10줄.
**리스크**: 문단 분리가 대화체에서 부정확할 수 있음 → 대화 연속 블록은 하나의 문단으로 취급하는 규칙 추가.

---

### #4. W-5 PatchVerifier — 재감사 자동 검증 (거울)

**왜 4등인가**: 구현 가장 쉬움 (50줄) + 재감사 LLM 호출 skip = 20K-30K 토큰/회

**삽입점**: `stage4_retry_runtime.py` L160-180 (PASS_WITH_FIX 루프 내, reaudit 호출 직전)

```
현재:
  patched_ms = chief_writer.inplace_patch(...)
  reaudit_result = director.reaudit(patched_ms, ...)  # LLM 호출

변경:
  patched_ms = chief_writer.inplace_patch(...)
  if PatchVerifier.verify(original_ms, patched_ms, fix_pack):
      # Python 검증 통과 → 재감사 skip
      reaudit_result = {"verdict": "PASS", "source": "patch_verifier"}
  else:
      reaudit_result = director.reaudit(patched_ms, ...)
```

**구현** (~50줄):
```python
# modules/core/patch_verifier.py (신규 파일)

from modules.core.constants import calc_patch_change_ratio

class PatchVerifier:
    @staticmethod
    def verify(original: str, patched: str, fix_pack: dict) -> bool:
        # 1. must_fix의 "A→B" 패턴 검증
        for item in fix_pack.get("must_fix", []):
            if "→" not in item:
                return False  # 비구조 수정 → LLM 재감사 필요
            old, new = item.split("→", 1)
            if old.strip() in patched:
                return False  # 아직 남아있음
            if new.strip() not in patched:
                return False  # 교체 안 됨

        # 2. 변경량 검증
        ratio = calc_patch_change_ratio(original, patched)
        if ratio > 0.10:  # entity_ref는 10% 이내여야 함
            return False

        # 3. 길이 검증
        if abs(len(patched) - len(original)) > len(original) * 0.05:
            return False

        return True
```

**적용 조건**: `fix_pack["target_kind"] == "entity_ref"` 일 때만 Python 검증. 그 외는 기존 LLM 재감사.
**기존 코드 변경량**: 신규 파일 1개 + stage4_retry_runtime.py에 ~10줄 분기.

---

## Tier 2: 2주차 (중간 규모, 설계 검토 필요)

### #5. W-4 ContradictionIndex — Director 컨텍스트 95% 절감 (지도)

**ROI가 높지만 5등인 이유**: 구현 규모가 크고 (250줄), episode_bible 구조에 의존

**삽입점**: `director_ensemble.py` L748-774 (prev_manuscripts_text 조립 구간)

```
현재:
  prev_manuscripts_text = smart_truncate(prev_manuscripts_text)  # 80-150KB 그대로

변경:
  if use_contradiction_index:  # feature flag
      prev_manuscripts_text = ContradictionIndex.build(
          db=self._db, up_to_ep=ep_num, lookback=30)  # 3-5KB
  else:
      prev_manuscripts_text = smart_truncate(prev_manuscripts_text)
```

**필요 데이터**:
- `episode_bible` 테이블에서 에피소드별 핵심 사실 추출
- 이미 `db.get_episode_bible(ep)` 메서드 존재
- episode_bible에 `state_changes`, `key_events`, `deaths` 등 구조화 데이터 포함

**구현 규모**: ~250줄 (인덱스 빌더 + 캐시 + 테스트)
**리스크**: 인덱스가 너무 압축되면 Director가 서사적 모순을 놓칠 수 있음
**완화**: feature flag로 A/B 테스트 → 인덱스 vs 전문 비교

---

### #6. L-3 EntityMatcher — 고유명사 결정론적 매칭

**삽입점**: `director_continuity.py` L122 (LLM entity consistency 호출 전)

```
현재:
  result = self._d.ask(prompt, ...)  # LLM이 전체 원고에서 이름 불일치 탐색

변경:
  python_mismatches = EntityMatcher(registry).find_mismatches(manuscript)
  if python_mismatches:
      # Python이 찾은 문제를 Director 프롬프트에 삽입 (무기로 활용)
      prompt += f"\n\n[Python 사전탐지] {python_mismatches}"
  elif not self._needs_contextual_check(manuscript):
      return python_result  # 문제 없음 → LLM skip (레이어로 활용)
  result = self._d.ask(prompt, ...)
```

**이중 활용**: 문제 발견 시 → 무기 (LLM 프롬프트에 삽입), 문제 없음 시 → 레이어 (LLM skip)
**기존 truth_gate.py 패턴 재사용**: L126-135의 lookbehind regex 패턴 그대로 활용
**구현 규모**: ~120줄

---

### #7. L-6 DeterministicScorer — 폴백 편향 제거

**삽입점**: `director_ensemble.py` 폴백 경로 (LLM 파싱 실패 시)

```
현재:
  logging.warning("[TF-47] 폴백 — 첫 번째 후보 선택")
  return candidates[0]

변경:
  ranked = DeterministicScorer.rank(candidates)
  logging.info(f"[TF-47] 폴백 — 결정론적 순위 1위 선택: {ranked[0]['strategy']}")
  return ranked[0]
```

**구현 규모**: ~40줄. 가장 작지만 ROI도 낮음 (폴백 발생 빈도 자체가 낮음).

---

## Tier 3: 3-4주차 (아키텍처 영향)

### #8~#13 요약

| 순위 | ID | 핵심 블로커 | 비고 |
|:---:|:---:|-----------|------|
| 8 | W-3 SceneContextFilter | `_get_npc_equipment_summary()`에 blueprint 파라미터 추가 필요 | 파라미터 스레딩 |
| 9 | L-2 RegexParser | 에피소드 생성 시 마커 삽입 필요 (생성 프롬프트 변경) | 2단계 구현 |
| 10 | W-1 FactDatabase | fact_ledger + truth_gate + world_state 통합 래퍼 | 기존 모듈 결합 |
| 11 | W-2 TemporalValidator | knowledge_map 인덱스 빌드 필요 | InfoParadox 연동 |
| 12 | W-6 AdvisoryBatcher | Advisory 공통 컨텍스트 추출 + Gemini 캐시 공유 | 아키텍처 변경 |
| 13 | W-7 FeedbackCompiler | Director 출력 형식 변경 → 하위 호환 필요 | 프롬프트 변경 |

---

## 구현 플로우 차트

```
Week 1 (비파괴적, feature flag 방식)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Day 1-2: L-5 EarlyReturnGate
           → TruthGate, Flashback, NumericDrift 3개 먼저
           → 테스트 통과 시 나머지 4개 확장

  Day 3-4: L-1 DEA + L-4 조사엔진
           → deterministic_edit.py, korean_particle.py 신규
           → stage4_retry_runtime.py 분기 추가
           → entity_ref 패치 단위 테스트

  Day 4-5: L-1A SurgicalRewriteLayer
           → chief_writer.py에 _attempt_paragraph_surgical_patch() 추가
           → 문단 분리 + splice 로직

  Day 5:   W-5 PatchVerifier
           → patch_verifier.py 신규
           → PASS_WITH_FIX 루프에 Python 선검증 삽입

  검증:     100에피 A/B 비교
           → 레이어 ON vs OFF 결과 diff
           → 토큰 사용량 비교

Week 2 (중간 규모)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Day 1-3: W-4 ContradictionIndex
           → 에피소드별 팩트 인덱스 빌더
           → Director 프롬프트 교체 (feature flag)

  Day 4:   L-3 EntityMatcher
           → truth_gate.py 패턴 재사용
           → director_continuity.py 분기 추가

  Day 5:   L-6 DeterministicScorer
           → director_ensemble.py 폴백 교체

Week 3-4 (아키텍처 영향)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  W-3, L-2, W-1, W-2, W-6, W-7
  → 각각 feature flag로 점진 도입
```

---

## 신규 파일 목록

| 파일 | 대상 | LOC |
|------|------|----:|
| `modules/core/deterministic_edit.py` | L-1 DEA | ~50 |
| `modules/core/korean_particle.py` | L-4 조사엔진 | ~30 |
| `modules/core/surgical_rewrite.py` | L-1A 수술적 재작성 | ~120 |
| `modules/core/patch_verifier.py` | W-5 패치 검증 | ~50 |
| `modules/core/contradiction_index.py` | W-4 모순 인덱스 | ~200 |
| `modules/core/entity_matcher.py` | L-3 고유명사 매칭 | ~100 |
| `tests/test_deterministic_edit.py` | L-1 테스트 | ~80 |
| `tests/test_korean_particle.py` | L-4 테스트 | ~60 |
| `tests/test_surgical_rewrite.py` | L-1A 테스트 | ~80 |
| `tests/test_patch_verifier.py` | W-5 테스트 | ~50 |

**총 신규 코드**: ~820줄 (Tier 1+2)
**기존 코드 변경**: ~100줄 (분기 삽입)

---

## 예상 절감 효과 (Tier 1만 적용 시)

```
현재 (PASS_WITH_FIX 에피소드):
  LLM 호출: 52회
  토큰: ~400K

Tier 1 적용 후:
  L-5 → Advisory 3-4개 skip         = -60K~-80K 토큰
  L-1 → entity_ref DEA 처리          = -5K 토큰 + 오염 0%
  L-1A → local_sentence 문단 수술    = -3K 토큰 + 오염 0%
  W-5 → 재감사 skip                  = -25K 토큰
  ─────────────────────────────────
  절감: ~93K-113K 토큰/에피소드 (23-28%)
  LLM 호출: 52회 → ~35회 (33% 절감)

  + 비타겟 오염 0% 보장 (L-1, L-1A)
```

---

## 핵심 원칙

> 1. **레이어는 LLM을 안 부른다** — 코드가 처리하고, 실패 시만 LLM 폴백
> 2. **무기는 LLM에게 쥐여준다** — LLM이 더 정확하게 판단하도록 사전 정보 제공
> 3. **모든 도입은 feature flag** — `validation.yaml`에 on/off 설정
> 4. **비파괴적 삽입** — 기존 코드의 `if` 분기 앞에 추가, 기존 로직 불변
> 5. **실패 = 폴백** — 레이어/무기 실패 시 기존 LLM 경로로 자동 복귀

---

*끝.*
