# Arc 수동 검사 후속 완화 패치 — 03_2727

> 근거: Arc 1~5 수동 모순 검사 결과 MAJOR 4건 + MINOR 7건
> 기존 코덱스 오더(감사03) 7 Step 대비 미대응 항목 식별 + 추가 완화 설계
> 테스트 기준선: 3,598 passed

---

## 1. 기존 패치 대응 상태 분류

### 기존 패치로 대응 완료 (추가 조치 불필요)

| 모순 | 내용 | 대응 패치 | 판정 |
|------|------|----------|------|
| 모순 5 | Arc 4→5 종료 자산 일치 | `_fix_start_state` 자동 계승 | OK |
| 모순 7 | Arc 4→5 종료 자산 일치 | 동일 | OK |
| 모순 14 | Arc 1 시간 배경 미명시 | NS-4-S2 시간 연속성 advisory | P3, 미패치 허용 |

### 기존 패치로 부분 대응 (완화 강화 필요)

| 모순 | 내용 | 기존 대응 | 갭 |
|------|------|----------|-----|
| 모순 1 | Arc 2→3 위치 점프 (강남 계약→여의도 출현) | BUG-A: SSOT 우선순위 변경 | **근본 원인**: LLM이 Arc 내부에서 tactical_doc은 "강남"이라고 쓰면서 arc_end_state.location은 "여의도"로 설정. Arc 내부 정합성 교차검증 없음 |
| 모순 2 | Arc 2→3 강남→여의도→강남 이중 이동 | BUG-A 동일 | 동일 |
| 모순 3,4 | Arc 2 수익률 과대 (290%) | NS-3-B 30% 괴리 경고 | 경고가 LLM에 무시됨. 자산 성장률 Python 교차검증 없음 |
| 모순 8-10 | 소지품 출현/소멸 미설명 | `_remove_duplicate_items` (중복만 제거) | 새로 등장한 아이템의 출처 검증 없음 |

### 기존 패치 미대응 (신규 완화 필요)

| 모순 | 내용 | 현재 상태 |
|------|------|----------|
| 모순 2 | Arc 3 ep11 잔여 현금 38억 누락 기술 | 에피소드 간 현금 잔고 교차검증 없음 |
| 모순 6 | Arc 5 ep19 금 청산 111.7→110억 (1.7억 감소) | 청산 전후 자산 차이 advisory 없음 |
| 모순 12 | Arc 5에서 ThinkPad T60 장비 목록 소멸 | 소지품 소멸 감지 없음 |

---

## 2. 추가 완화 패치 설계 + 구현 현황

### PATCH-A: 자산 성장률 상한 advisory [P1] ✅ 구현 완료

**대상 모순**: 모순 3, 4 (Arc 2 수익 290% 과대)

**현재 상태**: NS-3-B(`_check_arc_vs_block_targets`)가 Phase 2.55에서 Treatment 목표 대비 30% 괴리 경고 생성. 그러나 이 경고는 `feedback` 문자열에 prepend될 뿐, Director가 이미 선택한 후(Phase 2.6 후)에 발동하므로 **선택 시점에 영향을 주지 못함**. 또한 Arc 내부의 자산 성장률 자체(시작→종료)의 비현실성은 검증하지 않음.

**구현**: `auto_correct()` 단계 10에 `_check_asset_growth_rate()` advisory 추가.

- 시작 자산 대비 종료 자산이 3배(200% 성장)를 초과하면 MAJOR 경고
- 투자물에서 레버리지 3배 x 기초자산 30% 변동 = 90% 수익이 현실적 상한
- `_parse_korean_number()` 유틸: "78억" → 7800000000 변환

**영향 파일**: `modules/core/stage2_optimizer.py`

**테스트**: 2개 (test_asset_growth_rate_over_200pct, test_asset_growth_rate_under_200pct)

---

### PATCH-B: 소지품 출현/소멸 감지 advisory [P2] ✅ 구현 완료

**대상 모순**: 모순 8 (PC 출처 불명), 모순 9 (PC 대수 불일치), 모순 12 (ThinkPad 소멸)

**구현**: `auto_correct()` 단계 2에 `_check_equipment_continuity()` advisory 추가.

- 출처 불명 등장: end_equip에 있는데 start_equip에도 acquired에도 없음
- 소멸 감지: prev_equip에 있었는데 start_equip에서 사라짐
- `_normalize_items()` 유틸: list 내 str/dict 혼합 정규화

**영향 파일**: `modules/core/stage2_optimizer.py`

**테스트**: 3개 (test_equipment_unexplained_appearance, test_equipment_disappearance, test_equipment_normal_flow)

---

### PATCH-C: tactical_doc ↔ arc_end_state 위치 교차검증 [P1] ✅ 구현 완료

**대상 모순**: 모순 1 (강남 계약→여의도 출현), 모순 2 (이중 이동)

**이전 설계 (폐기)**: analyst.yaml/ensemble.yaml에 "처분 사유 명시하라" 프롬프트 1줄 추가 → **효과 없음**. 프롬프트에 이미 "tactical_doc 내용과 state_constraints는 반드시 일치해야 합니다"(ensemble.yaml L39-41)가 있는데도 LLM이 안 지킴. 프롬프트 추가로는 해결 불가.

**근본 원인 (DB 확인 완료)**:
- Arc 2의 tactical_doc ep8 종료: **강남** 테헤란로 신규 중형 오피스
- Arc 2의 arc_end_state.location: **여의도** SW인베스트먼트 사무실
- Arc 2의 joint_docs.final_location: **여의도** SW인베스트먼트 사무실
- → LLM이 같은 Arc 내에서 tactical_doc과 state_constraints를 불일치하게 생성
- → `_sync_final_location()`은 joint_docs → arc_end_state 단방향 동기화만 수행, tactical_doc 원문과 대조 없음

**신규 설계**: `_check_tactical_location_consistency()` Python 교차검증 advisory

```python
def _check_tactical_location_consistency(self, arc: dict) -> dict:
    """[PATCH-C] tactical_doc 마지막 화 종료 위치 ↔ arc_end_state.location 교차검증."""
    tactical = arc.get("tactical_doc", "")
    if not tactical or len(tactical) < 100:
        return arc

    end_loc = arc.get("state_constraints", {}).get("arc_end_state", {}).get("location", "")
    if not end_loc:
        return arc

    # tactical_doc 마지막 500자에서 위치 키워드 추출
    tail = tactical[-500:]
    # arc_end_state.location의 핵심 지명(첫 번째 명사구) 추출
    loc_keywords = re.findall(r"[가-힣]{2,}", end_loc)
    if not loc_keywords:
        return arc

    # 핵심 지명이 tactical_doc 말미에 1개도 없으면 불일치 경고
    matched = [kw for kw in loc_keywords[:3] if kw in tail]
    if not matched and loc_keywords:
        self.corrections_made.append(
            f"[PATCH-C] tactical_doc 종료 위치와 arc_end_state.location 불일치 — "
            f"arc_end_state: '{end_loc[:50]}', tactical_doc 말미에 해당 지명 미발견"
        )

    return arc
```

**효과**: tactical_doc 마지막 종료 위치와 arc_end_state.location의 핵심 지명이 불일치하면 advisory. Director가 심사 시 "위치 내부 모순" 참고.

**제약**: 대원칙 1 준수 — advisory만, 자동 수정 없음. Python은 키워드 매칭만 수행.

**영향 파일**: `modules/core/stage2_optimizer.py`

**테스트**:
1. `test_tactical_location_mismatch` — 불일치 시 경고 생성
2. `test_tactical_location_match` — 일치 시 경고 없음

---

### PATCH-D: Arc 간 청산 전후 자산 차이 advisory [P3] ✅ 구현 완료

**대상 모순**: 모순 6 (111.7억→110억, 1.7억 감소)

**구현**: `_fix_start_state()` 내 소지품 계승 블록 이후에 자산 차이 advisory 추가.

- Arc N 종료 total_assets와 Arc N+1 시작 total_assets의 5% 초과 차이 시 advisory
- `_parse_korean_number()` 유틸 공유

**영향 파일**: `modules/core/stage2_optimizer.py`

**테스트**: 1개 (test_asset_diff_between_arcs_advisory)

---

### PATCH-E: Director 심사 프롬프트 "Arc 내부 정합성" 항목 추가 [P2] ✅ 구현 완료

**대상**: 갭 3 — Director `audit_strategic_plan()` 프롬프트에 "현재 Arc 내부 tactical_doc ↔ state_constraints 일치도" 검사 항목 없음

**현재 상태**:
- `STRATEGIC_AUDIT_PROMPT_V30` Step 1~5: Arc **간** 연속성만 검사 (이전 Arc→현재 Arc)
- Arc **내부**에서 tactical_doc의 사건 설명이 state_constraints 수치와 일치하는지 검사 항목 **미명시**
- ensemble.yaml L39-41 "일치해야 합니다" 선언만 있고 검증 방법 모호

**설계**:
- director.yaml `STRATEGIC_AUDIT_PROMPT_V30` Step 1 직후에 Step 1.5 추가:

```
Step 1.5: Arc 내부 상태-서사 정합성 검사
- arc_start_state와 arc_end_state를 비교하여 변동 항목을 추출하라:
  - 자산 변동액 (시작→종료 차이)
  - 소지품 변동 (+신규획득, -폐기)
  - 부상 상태 변화 (치유/악화)
  - 위치 변경 (시작→종료)
- 각 변동 항목이 tactical_doc의 사건 서술에 대응되는가?
  - 예: "자산 50억 증가" → 투자/판매/보상 서술 있어야 함
  - 예: "위치 강남→여의도" → 이동 사유/과정 서술 있어야 함
- 일치하지 않는 항목은 contradictions에 기록
```

**효과**: Director가 Arc 내부 정합성을 명시적으로 검사하게 됨. 대원칙 3(Director 주권) 강화.

**제약**: 프롬프트 변경이므로 LLM 토큰 소비 미미. Director 판단 기준 명확화.

**영향 파일**: `config/prompts/director.yaml`

**테스트**: 기존 테스트 커버 (실파이프라인 검증)

---

## 3. 미패치 항목 (대응 불가 또는 ROI 부족)

| 모순 | 사유 |
|------|------|
| 모순 2 (ep11 잔여 현금 38억 누락) | tactical_doc 내 에피소드 서술은 자유 텍스트. Python으로 에피소드별 현금 잔고를 추적하려면 tactical_doc 전문 파싱 필요 — ROI 대비 복잡도 과대. Director 심사에서 "자산 합계 불일치" 체크리스트(NC-3 11번 카테고리)가 커버. |
| 모순 11 (PC 1→2대 증가) | PATCH-B로 equipment 레벨에서 감지 가능. 그러나 tactical_doc 내 "PC N대" 서술까지 추적하려면 자유 텍스트 파싱 필요 — 동일 사유로 미패치. |
| 모순 15 (1개월 미만 주장) | 서사적 시간 표현의 정확도 검증은 LLM 판단 영역. NS-4가 Arc 간 날짜 연속성만 체크하고, Arc 내 서술의 시간 감각은 LLM에 위임. 대원칙 1 준수. |

---

## 4. 영향 범위 요약

| 파일 | 변경 | 상태 |
|------|------|------|
| `modules/core/stage2_optimizer.py` | PATCH-A `_check_asset_growth_rate` + PATCH-B `_check_equipment_continuity` + PATCH-D 자산 차이 advisory + `_parse_korean_number`/`_normalize_items` 유틸 | ✅ 구현 완료 |
| `modules/core/stage2_optimizer.py` | PATCH-C `_check_tactical_location_consistency` | ✅ 구현 완료 |
| `config/prompts/director.yaml` | PATCH-E: Step 1.5 Arc 내부 정합성 검사 항목 | ✅ 구현 완료 |

**테스트**: 8개 구현 완료 (PATCH-A 2 + PATCH-B 3 + PATCH-C 2 + PATCH-D 1) + PATCH-E 실파이프라인 검증

---

## 5. 제약 사항

1. **대원칙 1 준수**: 전 패치 advisory-only. 자산 수치/위치 자동 수정 없음.
2. **대원칙 3 준수**: Director가 advisory를 무시할 수 있음. REJECT 강제 없음.
3. **tactical_doc 자유 텍스트 한계**: 에피소드별 현금 잔고, PC 대수 등은 구조화되지 않은 서술. Python 파싱 ROI 대비 복잡도 과대하여 미패치.
4. **한국어 숫자 파서**: "78억", "111.7억" 등 파싱 필요. `_parse_korean_number()` 유틸로 해결 완료.
5. **PATCH-C 위치 키워드 매칭 한계**: 정확 매칭이므로 유사 표현("강남 오피스" vs "테헤란로 사무실")은 탐지 불가. 핵심 지명(강남, 여의도 등) 수준에서는 유효.

---

## 6. 리스크

| 리스크 | 확률 | 완화 |
|--------|------|------|
| PATCH-A 200% 상한이 합법적 고수익 Arc를 오탐 | 낮음 | advisory-only, 자동 REJECT 없음. 200%는 레버리지 3배 x 67% 기초자산 변동에 해당하며 단기간 달성 비현실적 |
| PATCH-B 소지품 정규화 불일치로 오탐 | 중간 | `_normalize_items`에서 dict/str 혼합 처리. 이름 유사도(ThinkPad vs IBM ThinkPad T60)는 정확 매칭이므로 표기 불일치 시 오탐 가능 → 부분 매칭 검토 가능하나 P2에서 정확 매칭으로 시작 |
| PATCH-C 위치 키워드 매칭 오탐 (동일 지명이 다른 맥락 등장) | 낮음 | tactical_doc 마지막 500자만 대조. 종료 위치 맥락에 집중. advisory-only |
| PATCH-D 한국어 숫자 파서 오동작 | 낮음 | 기존 유사 파서 검증 완료. 파싱 실패 시 advisory 미발동(안전 방향) |
| PATCH-E Director 프롬프트 길이 증가로 토큰 비용 | 무시 | Step 1.5 추가 ~200자, 전체 프롬프트 대비 <1% |

---

## 7. 전수 조사 결과 — Arc 품질 사각지대 3건

### 사각지대 1: 현재 Arc 내 위치 불일치 [P1] → PATCH-C로 대응

- **현황**: `_sync_final_location()`은 joint_docs → arc_end_state 단방향만 동기화. tactical_doc 원문과의 대조 없음
- **근본 원인**: LLM이 Arc 생성 시 tactical_doc과 state_constraints를 독립적으로 생성, 내부 정합성 보장 안 됨
- **대응**: PATCH-C Python regex 교차검증 advisory

### 사각지대 2: 자산 변동 근거 미검증 [P2] → PATCH-E로 대응

- **현황**: 시작→종료 자산 변동의 tactical_doc 서사적 설명가능성 미검증
- **근본 원인**: Director audit_strategic_plan 프롬프트에 "Arc 내부 state↔tactical 정합성" 검사 항목 없음
- **대응**: PATCH-E Director 프롬프트 Step 1.5 추가 (LLM 판단)

### 사각지대 3: Director 검사 항목 미명시 [P2] → PATCH-E에 포함

- **현황**: ensemble.yaml "일치해야 합니다" 선언만 있고 구체적 검사 방법 부재
- **대응**: PATCH-E에서 변동 항목 추출 → 서사 대응 여부 명시적 검사로 해결
