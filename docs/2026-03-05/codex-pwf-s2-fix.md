# Codex 구현 오더: PWF-S2 — Stage 2 PASS_WITH_FIX 무력화 수정

## 배경 (읽기 전용 — 수정 금지)

실파이프라인(project `0_20260305`) 실행 중 Arc 1이 다음 경로로 REJECT됨:

```
PASS_WITH_FIX (score=94) → inplace patch #1 → 재심사 PASS_WITH_FIX (score=95)
                         → inplace patch #2 → 재심사 PASS_WITH_FIX (score=95)
                         → inplace patch #3 → 재심사 PASS_WITH_FIX (score=90)
                         → PF-3 소진 → REJECT
```

inplace patch(ArcEnsembleGenerator)는 정상 동작했으나 Director 재심사가
동일 오류를 3회 반복 감지 → PASS_WITH_FIX 무한 루프.

**근본 원인**: `audit_strategic_plan` 재심사 호출 시 `curr_block=enriched_block`
(원본 치료 텍스트)을 변경 없이 그대로 전달. Director 프롬프트가
`{curr_block}`과 `{tactical_doc}` 양쪽을 모두 주입하므로,

- `tactical_doc` → 패치 완료, "18억" (정상)
- `curr_block`   → 원본 그대로, "40억" (오류)

Director가 두 소스의 불일치를 새로운 모순으로 재감지 → PASS_WITH_FIX 반복.

증거: Director 재심사 #3 발언:
> "이는 **전술서 내용**의 서술('약 18억')과도 일치합니다"
(= tactical_doc는 이미 수정됐음을 Director가 인지했으나 curr_block 원문을 계속 문제 삼음)

Director prompt_len 3회 모두 정확히 17043 → enriched_block 변경 없음 확인.

---

## 대원칙 (CLAUDE.md 발췌 — 절대 위반 금지)

1. **Python은 수집만, 판단은 LLM이** — Python이 "이건 오류" 판단을 직접 하면 안 됨.
2. **디렉터 주권주의** — Director(LLM)가 최종 품질 결정권. Python이 Director를 우회하면 안 됨.
3. 테스트 기준선: **3,348 passed + 0 xfailed** (`pytest tests/ -q` 기준)

---

## 변경 파일

| 파일 | 역할 |
|------|------|
| `modules/core/stage2_finalizer.py` | PASS_WITH_FIX 재심사 루프에서 패치 이력 주입 |

---

## 구현 스펙

### 변경 위치

`stage2_finalizer.py` 내 PASS_WITH_FIX 루프 (`# [TF-32-VERIFY]` 주석 블록):
- 대략 L254~L385 구간
- `for _fix_i in range(_MAX_FIX):` 루프 내부
- Director 재심사 호출부: `self.ctx.agents["director"].audit_strategic_plan(...)` (~L317)

### 변경 내용

**1. 루프 진입 전 누적 패치 이력 리스트 초기화**

```python
# [TF-32-VERIFY] PASS_WITH_FIX → patch + Director 재심사 반복 (최대 3회)
_d_decision = audit.get("decision", "")
if _d_decision == "PASS_WITH_FIX":
    _MAX_FIX = 3
    _four_phase = self.ctx.agents.get("four_phase")
    _current_arc = dict(refined_arc)
    _current_audit = audit
    _fix_ok = False
    _applied_patches: list[str] = []  # ← 추가: 누적 패치 이력
```

**2. 패치 지시를 이력에 추가 (패치 실행 후, Director 재심사 전)**

`_patched` 확인 후, `self.ctx.ui.log(f"      🔄 [TF-38] Director 재심사...")` 호출 직전에 삽입:

```python
# 패치 이력 누적 (Director 재심사 컨텍스트용)
_applied_patches.append(str(_fix_instr)[:200])
```

**3. Director 재심사 호출 시 패치 이력을 story_context에 주입**

기존 코드:
```python
_re_audit = self.ctx.agents["director"].audit_strategic_plan(
    _patched,
    _expanded_prev_context,
    curr_block=enriched_block,
    protagonist_name=protagonist_name,
    suspected_duplicates=suspected_duplicates,
    entity_registry=entity_registry_for_director,
    story_context=_story_context,
)
```

변경 후:
```python
# [PWF-S2] 재심사 시 이미 적용된 패치를 story_context에 주입
# → Director가 curr_block 원문의 동일 오류를 재감지하지 않도록 컨텍스트 제공
_patch_ctx = ""
if _applied_patches:
    _patch_lines = "\n".join(f"- {p}" for p in _applied_patches)
    _patch_ctx = (
        "\n\n[PASS_WITH_FIX 재심사 — 이미 적용된 패치]\n"
        f"{_patch_lines}\n"
        "위 사항은 tactical_doc에 이미 반영되었습니다. "
        "curr_block 원문에 동일 오류가 보여도 tactical_doc에서 수정되었다면 수용하세요."
    )
_re_audit = self.ctx.agents["director"].audit_strategic_plan(
    _patched,
    _expanded_prev_context,
    curr_block=enriched_block,
    protagonist_name=protagonist_name,
    suspected_duplicates=suspected_duplicates,
    entity_registry=entity_registry_for_director,
    story_context=_story_context + _patch_ctx,  # ← 패치 이력 추가
)
```

---

## 구현 시 주의사항

1. `_applied_patches`는 루프 외부에서 초기화, 루프 내에서 append — 순서 유지
2. `_patch_ctx` 문자열은 `_story_context`가 None일 경우를 대비해 `(_story_context or "") + _patch_ctx`로 처리
3. `_fix_instr`이 None/빈 문자열일 경우 append 스킵:
   ```python
   if _fix_instr:
       _applied_patches.append(str(_fix_instr)[:200])
   ```
4. 기존 로직(`_current_arc = _patched`, `_current_audit = _re_audit` 등) 변경 금지
5. `audit_strategic_plan` 시그니처 변경 금지 — `story_context` 파라미터에만 추가

---

## 테스트 요구사항

### 신규 테스트 작성 위치
`tests/` 내 적절한 파일 (기존 stage2 관련 테스트 파일이 있으면 거기에 추가)

### 테스트 시나리오 3개

**테스트 1: 패치 이력이 story_context에 주입되는지 확인**

```python
def test_pwf_s2_patch_history_injected_to_story_context():
    """PASS_WITH_FIX 재심사 호출 시 패치 이력이 story_context에 포함되는지 확인."""
    # setup: stage2_finalizer의 PASS_WITH_FIX 루프를 mock으로 구성
    # - 첫 번째 Director 심사: PASS_WITH_FIX 반환 (fix_scope="inplace")
    # - _inplace_patch_arc: 성공 반환 (mock dict)
    # - 두 번째 Director 심사(재심사): PASS 반환
    # assert: 재심사 시 audit_strategic_plan에 전달된 story_context에
    #         "[PASS_WITH_FIX 재심사" 문자열이 포함되어 있어야 함
```

**테스트 2: 재심사가 PASS 반환하면 _fix_ok=True로 루프 종료**

```python
def test_pwf_s2_fix_ok_on_pass():
    """패치 후 Director가 PASS 반환하면 refined_arc가 _patched로 업데이트되고 PASS 확정."""
    # - 첫 번째 Director: PASS_WITH_FIX
    # - patch: 성공
    # - 재심사: PASS (score >= quality_gate_score)
    # assert: result decision == "PASS", refined_arc == _patched
```

**테스트 3: 3회 모두 PASS_WITH_FIX 반환 시 REJECT 전환**

```python
def test_pwf_s2_reject_after_max_fix():
    """3회 패치 후에도 PASS_WITH_FIX이면 REJECT 전환 + PF-3 패치본 채택."""
    # - 첫 번째 Director: PASS_WITH_FIX
    # - patch 1~3: 모두 성공
    # - 재심사 1~3: 모두 PASS_WITH_FIX
    # assert: result decision == "REJECT"
    # assert: refined_arc == 마지막 _patched (PF-3 채택)
    # assert: audit_strategic_plan 총 호출 횟수 == 3 (재심사만)
```

---

## 완료 기준

- [ ] `stage2_finalizer.py` 변경 완료
- [ ] 신규 테스트 3개 작성 및 PASS
- [ ] `pytest tests/ -q` 기준선 **3,348 passed 이상, xfailed 0** 유지
- [ ] `ruff check modules/core/stage2_finalizer.py` 0 violations

---

## 감리 포인트 (나중에 별도 요청)

감리 시 아래를 확인할 것:

1. `_applied_patches` 초기화 위치가 루프 진입 전인지 (루프 내부면 이력 누적 안 됨)
2. `story_context + _patch_ctx` 연산 시 None 가드 존재 여부
3. `_fix_instr` 빈 문자열 방어 존재 여부
4. 테스트 3개가 실제로 재심사 호출 횟수를 검증하는지 (`call_count` 등)
5. `audit_strategic_plan` 시그니처가 변경되지 않았는지
6. 기준선 테스트 수 이상으로 통과하는지
