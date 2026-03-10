# PC-1: 페이싱 개선 명세 (전개 속도 보수적 → 공격적)

> 작성일: 2026-03-09
> 상태: **감리 6·7·8차 3연속 PASS — 구현 승인**
> 구현: 미착수 (감리 3-PASS 후 판단)

---

## 1. 문제 정의

**증상**: 실파이프라인 생성 결과물의 전개 속도가 느리다는 평가가 반복됨.
**근본 원인 분석**:

| # | 원인 | 현재 값 | 영향도 |
|---|------|---------|--------|
| R-1 | `DEFAULT_EP_COUNT = 5`로 화수가 높아 이벤트 희석 | 기본 5화, 최대 6화 | **HIGH** |
| R-2 | `_determine_ep_count()` 휴리스틱이 500~1500자 구간에서 5화(Standard) 편향 | 문장 9~14개 → 무조건 5화 | **HIGH** |
| R-3 | Analyst/Ensemble 프롬프트에 "매 화 최소 상황 변화" 지시 부재 | LLM이 보수적 전개 선호 | **MEDIUM** |
| R-4 | 블록 간 인과 연결 지시 부재 → 블록 시작마다 도입부 반복 | setup 과다 | **MEDIUM** |

---

## 2. 제안 항목 (4건)

### PC-1-A: ep_count 기본값 하향 + 권장 범위 조정

**변경 대상**: 3파일 5곳 + 하드코딩 폴백 정리 11파일 20곳

**A. 핵심 변경 (3파일 5곳)**:

| 파일 | 위치 | 현재 | 변경 | 비고 |
|------|------|------|------|------|
| `constants.py` L241 | `DEFAULT_EP_COUNT` | 5 | **4** | Python 휴리스틱 기본값 |
| `constants.py` L328 | `VolumeSettings.EPISODES_PER_ARC` | 5 | **4** | Volume 전략 baseline |
| `analyst.yaml` L291 | 가변 페이싱 가이드 | `Blitz(3~4화), Standard(5화), Epic(5~6화)` | `Blitz(3화), Standard(4화), Epic(5~6화)` | LLM 지시 |
| `analyst.yaml` L352 | pacing_decision 스키마 | `Blitz(3-4화) / Standard(4-5화) / Epic(5-6화)` | `Blitz(3화) / Standard(3-4화) / Epic(5-6화)` | JSON 스키마 |
| `ensemble.yaml` L83 | ep_count 설명 | `3~6 중 사건 밀도에 맞게 결정` | `3~6 중 결정 (4화 권장, 5화 이상은 사건 밀도 충분한 경우만)` | LLM 지시 |

**B. 하드코딩 `5` 폴백 → `Stage2Limits.DEFAULT_EP_COUNT` 참조로 교체 (11파일 15곳, except절 5곳 포함 총 20곳)**:

이 폴백들은 LLM 응답 dict에서 `ep_count`가 누락된 경우의 안전장치. 실제 발동 빈도는 매우 낮으나(Analyst가 ep_count를 항상 설정), 기본값 SSOT 일관성을 위해 상수 참조로 교체.

| 파일 | 위치 | 현재 | 변경 |
|------|------|------|------|
| `models/arc.py` L198 | `ep_count: int = 5` | 리터럴 5 | `Stage2Limits.DEFAULT_EP_COUNT` |
| `arc_ensemble.py` L248 | `.get("ep_count", 5)` | 리터럴 5 | `.get("ep_count", Stage2Limits.DEFAULT_EP_COUNT)` |
| `arc_ensemble.py` L805 | `.get("ep_count", 5)` | 리터럴 5 | `.get("ep_count", Stage2Limits.DEFAULT_EP_COUNT)` |
| `arc_draft_validator.py` L415 | `.get("ep_count", 5)` | 리터럴 5 | `.get("ep_count", Stage2Limits.DEFAULT_EP_COUNT)` |
| `arc_draft_validator.py` L509 | `.get("ep_count", 5)` | 리터럴 5 | `.get("ep_count", Stage2Limits.DEFAULT_EP_COUNT)` |
| `blueprint_constraint_compiler.py` L56 | `.get("ep_count", 5)` | 리터럴 5 | `.get("ep_count", Stage2Limits.DEFAULT_EP_COUNT)` |
| `continuity_arc.py` L255 | `.get("ep_count", 5)` | 리터럴 5 | `.get("ep_count", Stage2Limits.DEFAULT_EP_COUNT)` |
| `unified_arc_validator.py` L241 | `.get("ep_count", 5)` | 리터럴 5 | `.get("ep_count", Stage2Limits.DEFAULT_EP_COUNT)` |
| `unified_blueprint_validator.py` L218 | `.get("ep_count", 5)` | 리터럴 5 | `.get("ep_count", Stage2Limits.DEFAULT_EP_COUNT)` |
| `state_service.py` L74 | `else 5` | 리터럴 5 | `else Stage2Limits.DEFAULT_EP_COUNT` |
| `stage4_context_builder.py` L540 | `.get("ep_count", 5)` | 리터럴 5 | `.get("ep_count", Stage2Limits.DEFAULT_EP_COUNT)` |
| `state_locked_arc_generator.py` L95 | `"5개 에피소드를 하나의 Arc로 통합하세요."` (프롬프트) | 리터럴 5 | `"{ep_count}개 에피소드를 하나의 Arc로 통합하세요."` |
| `state_locked_arc_generator.py` L113 | `"ep_count": 5` (프롬프트 예시) | 리터럴 5 | `"ep_count": {ep_count}` 플레이스홀더로 교체 |
| `state_locked_arc_generator.py` L117 | `"5개 에피소드 본문 통합"` (프롬프트 예시) | 리터럴 5 | `"{ep_count}개 에피소드 본문 통합"` |
| `narrative_structure_analyzer.py` L26 | `"아래 5개 에피소드 비트에서"` (프롬프트) | 리터럴 5 | `"아래 {ep_count}개 에피소드 비트에서"` 또는 수량 한정어 제거 |

**참고**: 위 테이블의 `.get("ep_count", 5)` 패턴이 있는 파일 중 5곳(`arc_ensemble.py` L811, `arc_draft_validator.py` L417, `continuity_arc.py` L257, `unified_arc_validator.py` L243, `state_service.py` L76)은 인접한 except 절에도 `ep_count = 5` 폴백이 있음 → 같은 try/except 블록이므로 구현 시 함께 교체. 총 실제 교체 지점: **11파일 20곳**.

**테스트 영향**: `test_pydantic_models.py` L49 `assert arc.ep_count == 5` → `== 4`로 수정 필요.

**참고**: L291과 L352의 범위 표기가 기존에도 불일치 상태임 (L291: `Standard(5화)` 단일값, L352: `Standard(4-5화)` 범위값). 변경 후에도 동일 패턴 유지: L291은 권장 단일값, L352는 허용 범위. 의도적 차이이므로 현상 유지.

**사이드 이펙트 분석**:
- `_determine_ep_count()` L377: 500~1500자 + 9~14문장 → 기존 5화가 4화로 변경. **전체 블록의 ~60%가 이 구간에 해당할 것으로 추정** → 영향 범위 큼
- `tactical_doc` 최소 분량: `ep_count × 500자` → 4화 기준 2,000자 (기존 2,500자). 밀도 유지되나 총량 감소 → **정보 누락 위험 낮음** (화당 밀도는 오히려 증가)
- `analyst.yaml` L553: `{ep_count} * 800자` 재료 투입 → 4화 기준 3,200자 (기존 4,000자). 마찬가지로 화당 밀도 증가
- `_determine_ep_count()` L359-364: 500자 미만(3화)/1500자 초과(6화) 구간은 **변경 없음**
- tension_level ±1 보정은 그대로 유지 → 고긴장(≥8) 시 4→5화, 저긴장(≤3) 시 4→3화
- **MAX_EP_COUNT=6 유지** — Epic 스케일 자체를 제거하지 않음. 대규모 사건은 여전히 5~6화 가능
- **`stage2_orchestrator.py` L20**: `DEFAULT_EP_COUNT = VolumeSettings.EPISODES_PER_ARC` alias. `VolumeSettings.EPISODES_PER_ARC` 변경 시 자동 연동. L806/808/813/842/844/849에서 Arc resume(건너뛰기) 시 fallback ep_count로 사용 → **기존 프로젝트 재개 시 ep_start 계산이 4화 기준으로 변경됨**. 이미 진행 중인 프로젝트는 `arcs_source[n].get("ep_count", DEFAULT_EP_COUNT)` 1순위로 DB 저장된 실제 값을 사용하므로 **영향 제한적** (DB에 ep_count 없는 레거시 Arc만 해당).
- **`reverse_expander.py` L907/934/1151**: Stage 0에서 `(ep_num - 1) // EPISODES_PER_ARC + 1`로 Arc 번호 매핑. 5→4 변경 시 **동일 에피소드 번호가 다른 Arc에 매핑**될 수 있음 → ⚠️ **기존 프로젝트 호환성 위험**. 단, Stage 0은 신규 프로젝트 초기 설정 시에만 실행되므로 기존 프로젝트에는 영향 없음 (Arc 번호는 생성 시점에 고정).
- **`state_service.py` L251/254**: `arc_data.get("ep_count", EPISODES_PER_ARC)` fallback. DB에 ep_count 저장된 Arc는 영향 없음. fallback 경로(ep_count 미저장)만 5→4 변경.
- **`analyst.py` L644-645**: `MIN_EPISODES_PER_ARC`/`MAX_EPISODES_PER_ARC` 참조 — 이 값들은 변경 대상이 아니므로(MIN=3, MAX=6 유지) **영향 없음**.

**위험도**: ⚠️ MEDIUM — 화수 감소로 블록당 사건 소화 압축. 블록 경계 침범(TF-B) 재발 가능성 존재하나, 이벤트가 줄어드는 게 아니라 화수가 줄어드는 것이므로 밀도 증가로 긍정적. reverse_expander.py는 신규 프로젝트 전용이므로 호환성 위험 낮음.

---

### PC-1-B: _determine_ep_count() 휴리스틱 보정

**변경 대상**: 1파일 1곳

| 파일 | 위치 | 현재 | 변경 |
|------|------|------|------|
| `four_phase_arc_generator.py` L366-378 | 500~1500자 구간 분기 | 문장 ≤8→4화, 9~14→5화, ≥15→6화 | 문장 ≤8→3화, 9~14→**4화**, ≥15→**5화** |

**변경 전 (현재)**:
```python
if sentence_count <= 8:
    ep_count = 4
elif sentence_count >= 15:
    ep_count = 6
else:
    ep_count = Stage2Limits.DEFAULT_EP_COUNT  # 5화
```

**변경 후 (제안)**:
```python
if sentence_count <= 8:
    ep_count = 3  # 기존 4 → 3
elif sentence_count >= 15:
    ep_count = 5  # 기존 6 → 5
else:
    ep_count = Stage2Limits.DEFAULT_EP_COUNT  # 5→4 (PC-1-A 연동)
```

**사이드 이펙트 분석**:
- 문장 ≤8개 블록: 4화→3화. **최소 3개 에피소드에 이벤트 압축** → 한 화에 2+ 이벤트 발생 가능. 원고 분량(5,000자) 내 소화 가능 여부 검증 필요
- 문장 ≥15개 블록: 6화→5화. 풍부한 블록의 화수 1화 감소 → 이벤트 밀도 ~20% 증가. 원고 품질에 미치는 영향은 미미할 것으로 판단 (5화도 충분)
- tension_level ≥8 보정 시: 3→4, 4→5, 5→6 → 기존 동작 범위 내
- tension_level ≤3 보정 시: 3→**3**(MIN clamp), 4→3, 5→4 → MIN_EP_COUNT=3 안전장치 작동
- **PC-1-A와 결합 시**: 전체적으로 화수가 1~2화씩 줄어듦 → 평균 Arc 화수 5화 → ~3.5화 예상

**위험도**: ⚠️ MEDIUM-HIGH — PC-1-A와 결합 효과가 누적됨. 독립 적용 시 MEDIUM이나, 두 항목 동시 적용 시 화수 급감 가능. **단계적 적용 권장** (PC-1-A 먼저, 효과 확인 후 PC-1-B).

---

### PC-1-C: "매 화 상황 변화 1건 이상" 규칙 추가

**변경 대상**: 3파일 4곳

| 파일 | 위치 | 변경 내용 |
|------|------|-----------|
| `analyst.yaml` L291 이후 | 가변 페이싱 강령 **6번째 항목** 추가 (현재 1~5) | `6. **전개 밀도**: 매 화(에피소드)마다 최소 1개의 상황 변화(인물 관계 변동, 자산 변동, 위기 발생/해소, 정보 획득 중 1가지 이상)가 포함되어야 한다. 준비/이동만으로 한 화를 채우지 마라.` |
| `ensemble.yaml` L29 이후 | 서사 흥미 설계 **5번째 항목** 추가 (현재 1~4) | `5. **전개 밀도**: 매 화 최소 1건의 상황 변화(관계·자산·위기·정보 중 1가지). "준비만 하는 화"는 금지.` |
| `chief_writer.yaml` COMMON_RULES | **규칙 16** 추가 (현재 1~15) | `16. [페이싱] 이번 화에서 최소 1개의 상황 변화(인물 관계·자산·위기·정보)가 발생해야 합니다. 준비/이동만으로 한 화 전체를 채우지 마세요.` |
| `analyst.yaml` L601 이후 | self-critic **9번째 항목** 추가 (현재 1~8) | `9. **전개 밀도 검사**: 매 화마다 최소 1개의 상황 변화가 포함되어 있는가? "준비만 하는 화"가 없는가?` |

**사이드 이펙트 분석**:
- **긍정적**: "이동/관찰만 하는 화" 근절 → 체감 속도 직접 개선
- **부정적 가능성**: LLM이 매 화 억지 이벤트 삽입 → 서사 자연스러움 저하. 단, "상황 변화"를 넓게 정의(관계·자산·위기·정보)하여 완화
- **Director 검증**: Director가 이 규칙을 강제할 방법이 없음 (advisory 수준). NC-3 체크리스트에 항목 추가 고려 가능하나 현 단계에서는 불필요
- **기존 규칙 충돌**: 없음. 블록 경계 규칙(TF-B)과 상호보완적 — "다른 블록 사건을 가져오지 마라" + "현재 블록 사건을 매 화 진행시켜라"

**위험도**: 🟢 LOW — 프롬프트 추가만으로 코드 로직 변경 없음. 롤백 용이.

---

### PC-1-D: 블록 간 인과 연결 강화 지시

**변경 대상**: 2파일 2곳

| 파일 | 위치 | 변경 내용 |
|------|------|-----------|
| `analyst.yaml` L293 이후 | 하이브리드 설계 강령 **6번째 항목** 추가 (현재 1~5) | `6. **블록 간 인과 가속**: 이전 블록의 reward가 현재 블록의 context를 직접 촉발해야 한다. 새 블록 시작 시 "상황 재설명"은 3문장 이내로 제한하고, 즉시 사건에 돌입하라. 독자는 이미 이전 블록을 읽었다.` |
| `ensemble.yaml` 블록 경계 규칙 직후 (L61 이후) | 추가 항목 | `- 블록 시작 시 이전 블록 reward를 context의 출발점으로 사용하라. "상황 재설명"은 최소화(3문장 이내)하고, 새로운 사건으로 즉시 전환하라.` |

**사이드 이펙트 분석**:
- **긍정적**: Arc 첫 화의 도입부 과다 문제 해소. 이전 Arc reward → 현재 Arc context 직결로 "쉬어가는 화" 제거
- **부정적 가능성**: Arc 경계 공간연속성(감사04) 규칙과 충돌 우려 — "Arc 첫 화는 위치 변경 묘사 의무화" 지시가 있으나, 이것은 Stage 4 원고 집필 단계(CW mandatory_context)에서 적용되고 PC-1-D는 Stage 2 Arc 설계 단계 프롬프트이므로 **레이어가 다름, 충돌 없음**. 다만 LLM이 "3문장 이내" 제한을 원고까지 내재화할 경우 위치 묘사 축소 위험이 미약하게 존재 → 모니터링 대상.
- **"3문장 이내" 제한**: 정량적 제한이므로 LLM이 준수 가능. 다만 복잡한 세계관에서 3문장으로 컨텍스트 전달이 부족할 수 있음 → 실행 후 4~5문장으로 완화 가능
- **Treatment 블록 구조**: `context → event_villain → solution → reward` 4키에서 context의 비중이 줄어듦 → reward/solution 비중 상대적 증가 → 전개 속도 체감 개선

**위험도**: 🟢 LOW — 프롬프트 추가만. 롤백 용이.

---

## 3. 적용 전략 (단계적)

```
Phase 1 (LOW risk):  PC-1-C + PC-1-D  ← 프롬프트만 추가, 코드 변경 없음
Phase 2 (MED risk):  PC-1-A            ← DEFAULT_EP_COUNT 5→4 + 프롬프트 권장값 조정
Phase 3 (MED-HIGH):  PC-1-B            ← 휴리스틱 분기 보정 (Phase 2 효과 확인 후)
```

**Phase 1만 적용해도 체감 효과 있음** — "매 화 상황 변화" + "블록 간 인과 가속"이 LLM 보수성을 직접 교정.

Phase 2는 Phase 1 적용 후 실파이프라인 1회 실행 → 전개 속도 개선 여부 확인 후 결정.
Phase 3은 Phase 2 적용 후에도 느리다면 추가 적용.

---

## 4. 영향받는 기존 시스템

| 시스템 | 영향 | 대응 |
|--------|------|------|
| TF-B 블록 경계 4대 규칙 | 화수 감소 → 블록 내 이벤트 압축 → 경계 침범 위험 | TF-B 규칙 자체가 방어. 모니터링 |
| TF-D ep_count 3~6 제한 | 범위 내 변경이므로 영향 없음 | 없음 |
| NS-3-B 블록 목표 교차검증 | 화수 감소해도 목표 자체는 불변 | 없음 |
| NC-1 수치 정합성 | 화수 감소 → 화당 수치 변동 증가 가능 | NC-1이 자동 감지. 모니터링 |
| tactical_doc 분량 기준 | `ep_count × 500자` → 4화 기준 2,000자 | 화당 밀도 증가로 보상 |
| Director 평가 기준 | 원고 분량 4,000자 기준 불변 | 없음 |
| WritingDirective(TF-54) | 직전 N화 패턴 → 화수 감소해도 N은 불변 | 없음 |
| `stage2_orchestrator.py` L20 | `DEFAULT_EP_COUNT` alias → 자동 연동 | resume 경로에서 DB 우선 참조, fallback만 변경 |
| `reverse_expander.py` L907/934/1151 | Stage 0 Arc 번호 매핑 | 신규 프로젝트 전용, 기존 프로젝트 불변 |
| `state_service.py` L251/254 | ep_count fallback | DB 우선, fallback만 5→4 |
| `analyst.py` L644-645 | MIN/MAX 참조 | MIN=3, MAX=6 불변 → 영향 없음 |
| `test_stage234_fixes.py` L50-53 | `DEFAULT_EP_COUNT == EPISODES_PER_ARC` 동일성 검증 | 둘 다 4로 변경 시 PASS 유지 |
| `state_locked_arc_generator.py` L95/113/117 | 프롬프트에 `"5개 에피소드"` 하드코딩 | `{ep_count}` 플레이스홀더로 교체 |
| `narrative_structure_analyzer.py` L26 | 프롬프트에 `"5개 에피소드 비트"` 하드코딩 | 수량 한정어 제거 또는 동적화 |

---

## 5. 롤백 계획

- **Phase 1 롤백**: YAML 4곳 원복 (git revert 1 commit)
- **Phase 2 롤백**: constants.py 2곳 + YAML 3곳(analyst.yaml 2곳 + ensemble.yaml 1곳) + 하드코딩 폴백 11파일 20곳 원복 + test_pydantic_models.py 1곳 원복
- **Phase 3 롤백**: four_phase_arc_generator.py 1곳 원복
- **전체 롤백**: 단일 커밋이면 `git revert`, 분리 커밋이면 Phase 역순 revert

---

## 6. 검증 계획

1. 기존 테스트 3,614개 전량 PASS 확인
2. 실파이프라인 1회 실행 → 평균 ep_count 변화 측정
3. 생성된 원고에서 "준비만 하는 화" 비율 수동 확인
4. 블록 경계 침범 발생 여부 모니터링
5. arc_pos==1 원고에서 위치 묘사 누락 여부 확인 (PC-1-D 영향)

---

## 7. 감리 이력

| 차수 | 결과 | 지적 사항 | 대응 |
|------|------|-----------|------|
| 1차 | FAIL (7건) | ①CW 규칙번호 15→16 ②Analyst self-critic 8→9 ③stage2_orch alias 누락 ④reverse_expander 누락 ⑤state_service 누락 ⑥analyst.py MIN/MAX 미언급 ⑦L291/L352 불일치 미언급 | 전량 반영 완료 |
| 2차 | FAIL (1건) | ①리터럴 `5` 하드코딩 9파일 11곳 미커버 (arc.py/arc_ensemble/arc_draft_validator/blueprint_constraint_compiler/continuity_arc/unified_arc_validator/unified_blueprint_validator/state_service/stage4_context_builder) + test_pydantic_models.py 누락 | PC-1-A에 "B. 하드코딩 폴백 정리" 섹션 추가 + 테스트 영향 명시 |
| 3차 | FAIL (3건) | ①`state_locked_arc_generator.py` L113/117 프롬프트 예시 미커버(P1) ②Phase 2 롤백 "YAML 2곳"→3곳 + 폴백 원복 누락(P2) ③"9파일 11곳" → except절 5곳 미포함(P2) | state_locked_arc_generator 추가, 카운트 10파일 17곳으로 수정, 롤백 상세화 |
| 4차 | FAIL (2건) | ①`state_locked_arc_generator.py` L95 "5개 에피소드를..." 추가 미커버(P1) ②`narrative_structure_analyzer.py` L26 "아래 5개 에피소드 비트" 미커버(P1) + 카운트 불일치(P2) | 2건 추가, 카운트 11파일 20곳으로 수정, 영향 시스템 테이블 반영 |
| 5차 | FAIL (1건) | ①B 소제목 "(9파일 11곳)" 미갱신 → 실제 테이블 11파일 15곳 + except 5곳 = 20곳 | 소제목 갱신, state_tracker.py L497/511 기존 버그 참고 기록 |
| 6차 | **PASS** | 5차 수정 반영 확인. 5개 교차 검증 지점 전량 정합. 감리 이력 5건 존재 | — |
| 7차 | **PASS** | 대원칙 3건 위반 없음. Phase 의존성 검증 정확. 위험도 평가 적절. `{ep_count}` 플레이스홀더 기존 패턴과 일관 | — |
| 8차 | **PASS** | 엣지케이스(빈 블록, tension clamp) 안전. 테스트 2건 커버 완료. 프롬프트 간섭 없음. 코드베이스 잔여 하드코딩 0건 | — |
