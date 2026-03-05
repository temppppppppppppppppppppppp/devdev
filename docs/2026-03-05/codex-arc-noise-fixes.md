# Codex Order: ARC-NOISE — Arc 생성 품질 노이즈 3종 패치

**작업 ID**: ARC-NOISE-1/2/3
**우선순위**: P1
**테스트 기준선**: 3,370 passed (유지)

---

## 패치 1 — ARC-NOISE-1: I-12 내공 체크 비무협 장르 스킵

### 문제
`four_phase_arc_generator.py` `_check_arc_end_state()`가 장르 구분 없이
`internal_energy` 필드를 체크함. 투자물 Arc에서:
```
[I-12] 아크 종료 상태 점검: ['내공 미복원: 95%']
```
투자물에는 "내공" 개념 없음 → 무의미한 WARNING 노이즈.

### 대상 파일
`modules/domain/agents/four_phase_arc_generator.py`

### 수정 명세

`_check_arc_end_state` 메서드 내 `internal_energy` 체크 앞에 장르 가드 추가.

**변경 전** (약 L1282):
```python
energy = end_state.get("internal_energy")
if isinstance(energy, (int, float)) and energy < 100:
    warnings.append(f"내공 미복원: {energy}% (아크 간 회복 고려)")
```

**변경 후**:
```python
# [ARC-NOISE-1] 내공(internal_energy)은 무협/헌터 장르만 해당
_energy_genres = {"wuxia", "hunter", "fantasy"}
energy = end_state.get("internal_energy")
if isinstance(energy, (int, float)) and energy < 100 and self._genre in _energy_genres:
    warnings.append(f"내공 미복원: {energy}% (아크 간 회복 고려)")
```

---

## 패치 2 — ARC-NOISE-2: 금지 아이템 프롬프트 강화

### 문제
`arc_ensemble.py` `_generate_prohibition_summary()`가 constraint_compiler의
`❌ item (Arc N에서 획득)│   ...│` 포맷에서 박스 문자(`│`, 공백 패딩)를 포함한
채로 item 이름을 추출 → LLM 프롬프트에 지저분하게 표시됨.

실증: Arc 2에서 3개 후보 중 2개(balanced 40점, creative 25점)가 이미 보유한
`한미증권 해외 선물 계좌 거래내역서`를 다른 잔고(300억)로 재획득 시도.
LLM이 "잔고가 바뀐 다른 아이템"으로 인식.

### 대상 파일
`modules/domain/agents/arc_ensemble.py`

### 수정 명세

`_generate_prohibition_summary` 메서드 수정:

**변경 전** (약 L817-824):
```python
forbidden = re.findall(r"❌\s*([^\n❌]+)", constraint_block)
if forbidden:
    lines.append("")
    lines.append("🚫 절대 다시 획득/수여 금지:")
    for item in forbidden[:10]:  # 최대 10개
        clean_item = item.strip()[:50]
        if clean_item:
            lines.append(f"   ❌ {clean_item}")
```

**변경 후**:
```python
forbidden = re.findall(r"❌\s*([^\n❌]+)", constraint_block)
if forbidden:
    lines.append("")
    lines.append("🚫 절대 다시 획득/수여 금지 (잔고·수량이 달라도 동일 아이템으로 간주):")
    for item in forbidden[:10]:
        # 박스 문자, 패딩, Arc 출처 주석 제거 → 핵심 아이템명만 추출
        clean_item = re.sub(r"\s*\(Arc\s*\d+.*?\)", "", item)  # (Arc N에서 ...) 제거
        clean_item = re.sub(r"[│┤├─+|]", "", clean_item).strip()  # 박스 문자 제거
        clean_item = clean_item[:60]
        if clean_item:
            lines.append(f"   ❌ {clean_item}")
    lines.append("   ⚠️ items_acquired에 위 아이템명이 포함되면 즉시 REJECT됩니다.")
```

---

## 패치 3 — ARC-NOISE-3: V61 Entity 약칭 오탐 완화

### 문제
`director_continuity.py` LLM이 약칭을 불일치로 판정:
```
[concept] WTI 원유 선물 6월물 롱 포지션 → WTI 6월물 롱 포지션  (약칭, 동일 개념)
[concept] 평가손익 → 평가수익                                    (실제로는 다른 개념)
```
첫 번째는 명백한 오탐(부분 포함 관계). 두 번째는 진짜 불일치이나 WARNING 수준.
현재는 양쪽 모두 WARNING으로 Director 컨텍스트에 포함되어 노이즈 발생.

### 대상 파일
`modules/domain/agents/director_continuity.py`

### 수정 명세

LLM 응답에서 `mismatches`를 받은 후 Python으로 약칭 필터링 추가.

**변경 전** (약 L127-133):
```python
mismatches = result.get("mismatches", [])
if mismatches:
    decision = result.get("decision", "WARNING")
    logging.warning(f" [V61] Entity 일관성 검증: {decision} ({len(mismatches)}개 불일치)")
    for m in mismatches[:3]:
        logging.info(f"- [{m.get('category', '?')}] {m.get('registered_name', '?')} → {m.get('found_variant', '?')}"
        )
```

**변경 후**:
```python
mismatches = result.get("mismatches", [])

# [ARC-NOISE-3] 약칭/부분 포함 관계인 경우 MINOR로 다운그레이드 또는 필터
def _is_abbreviation(registered: str, variant: str) -> bool:
    """variant가 registered의 약칭(부분 포함)인지 확인."""
    r, v = registered.strip(), variant.strip()
    if not r or not v:
        return False
    # 한쪽이 다른 쪽을 포함하고 길이 차이가 30% 이상인 경우 약칭으로 간주
    if (v in r or r in v) and abs(len(r) - len(v)) / max(len(r), len(v)) >= 0.15:
        return True
    return False

filtered_mismatches = []
for m in mismatches:
    reg = m.get("registered_name", "")
    var = m.get("found_variant", "")
    if _is_abbreviation(reg, var):
        # 약칭은 MINOR로 다운그레이드하고 필터 (WARNING 트리거 안 함)
        logging.debug(" [V61-ABBREV] 약칭 오탐 필터: %s → %s", reg, var)
        continue
    filtered_mismatches.append(m)

mismatches = filtered_mismatches
result["mismatches"] = mismatches  # 필터된 결과 반환

if mismatches:
    decision = result.get("decision", "WARNING")
    logging.warning(f" [V61] Entity 일관성 검증: {decision} ({len(mismatches)}개 불일치)")
    for m in mismatches[:3]:
        logging.info(f"- [{m.get('category', '?')}] {m.get('registered_name', '?')} → {m.get('found_variant', '?')}"
        )
```

---

## 테스트 명세

```python
# ARC-NOISE-1: 투자물 장르에서 I-12 내공 WARNING 미발생
def test_arc_noise1_investment_no_internal_energy_warning():
    from modules.domain.agents.four_phase_arc_generator import FourPhaseArcGenerator
    # genre=investment로 인스턴스 생성 후 _check_arc_end_state 호출
    # internal_energy=90이 있어도 WARNING 없어야 함
    ...

# ARC-NOISE-1: 무협에서는 여전히 경고
def test_arc_noise1_wuxia_still_warns():
    ...

# ARC-NOISE-2: 박스 문자 제거 확인
def test_arc_noise2_prohibition_summary_clean():
    from modules.domain.agents.arc_ensemble import ArcEnsembleGenerator
    constraint = "│   ❌ 한미증권 해외 선물 계좌 (Arc 1에서 획득)                    │"
    gen = ArcEnsembleGenerator.__new__(ArcEnsembleGenerator)
    result = gen._generate_prohibition_summary("", constraint)
    assert "│" not in result
    assert "Arc 1에서" not in result
    assert "한미증권" in result

# ARC-NOISE-3: 약칭 필터
def test_arc_noise3_abbreviation_filtered():
    from modules.domain.agents.director_continuity import DirectorContinuity
    # "WTI 원유 선물 6월물 롱 포지션" vs "WTI 6월물 롱 포지션" → 필터
    ...

# ARC-NOISE-3: 실제 불일치는 통과
def test_arc_noise3_real_mismatch_passes_through():
    # "박성호" vs "이성호" → 필터 안 됨
    ...
```

---

## 감리 포인트

1. `pytest tests/ -q` → **3,370 passed** (기준선 유지)
2. `ruff check modules/` → 0 violations
3. `grep -n "내공 미복원" modules/domain/agents/four_phase_arc_generator.py` — 무협 가드 확인
4. 투자물 실파이프라인: `[I-12]` WARNING에 "내공 미복원" 미출력 확인
5. `_generate_prohibition_summary` 결과에 `│` 박스 문자 없음 확인

---

## 주의: LOG-EMOJI 패치 진행 중

`LOG-EMOJI` 패치(codex-log-emoji-strip.md) 병행 작업 중.
`logging.*()` 호출에 이모지 사용 금지. ASCII 태그 사용.
단, LLM 프롬프트 문자열 내 `🚫`, `❌` 등은 유지.
