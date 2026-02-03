# Stage 3: Blueprint Design Logic

## 1. 개요

Stage 3는 Arc 전술 문서(tactical_doc)를 기반으로 에피소드별 **상세 설계도(Blueprint)**를 생성하는 단계입니다.

```
입력: Arc tactical_doc + 장르 레퍼런스 + 이전 원고 엔딩
출력: 에피소드별 scene_breakdown + integrated_scenario + ending_hook
```

### 담당 에이전트
- **Architect**: 블루프린트 설계 (V55.4 2단계 모델 시스템)
- **Director**: 품질 검증
- **ContinuityInspector**: 연속성 검증

### 모델 티어 시스템 (V55.4)
| 시도 | 모델 | 조건 |
|------|------|------|
| 1차 | `gemini-2.5-pro` | 기본 시도 |
| 2차+ | `gemini-3-pro-preview` | REJECT 시 자동 격상 |

---

## 2. 전체 흐름도

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Stage 3: Blueprint Design                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 1. 초기화                                                    │   │
│  │    - Arc 데이터 로드 (ep_start, ep_end, tactical_doc)        │   │
│  │    - 장르별 레퍼런스 로드 (cliche, location)                 │   │
│  │    - V48 서사 다양성 엔진 초기화                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 2. 에피소드 루프 (working_ep → target_ep)                   │   │
│  │    ┌─────────────────────────────────────────────────────┐   │   │
│  │    │ 2.1 Arc 컨텍스트 확보                                │   │   │
│  │    │     - _get_arc_context_for_episode(working_ep)      │   │   │
│  │    │     - arc_pos = 현재화 - arc_start + 1              │   │   │
│  │    └─────────────────────────────────────────────────────┘   │   │
│  │                           ▼                                  │   │
│  │    ┌─────────────────────────────────────────────────────┐   │   │
│  │    │ 2.2 직전 화 원고 엔딩 추출                           │   │   │
│  │    │     - prev_ms_ending (마지막 3문장)                  │   │   │
│  │    │     - 연속성 연결고리 제공                           │   │   │
│  │    └─────────────────────────────────────────────────────┘   │   │
│  │                           ▼                                  │   │
│  │    ┌─────────────────────────────────────────────────────┐   │   │
│  │    │ 2.3 Blueprint 생성 루프 (Strike-Enrichment System)  │   │   │
│  │    │     ┌─────────────────────────────────────────┐     │   │   │
│  │    │     │ A. Focus Package 구성                   │     │   │   │
│  │    │     │    - MUST_FOCUS: 이번 화 전술 설계       │     │   │   │
│  │    │     │    - FULL_MAP: 마스킹 (미래 정보 차단)   │     │   │   │
│  │    │     │    - STOP_LINE: 다음 화 비트 (정지선)    │     │   │   │
│  │    │     └─────────────────────────────────────────┘     │   │   │
│  │    │                      ▼                              │   │   │
│  │    │     ┌─────────────────────────────────────────┐     │   │   │
│  │    │     │ B. V50+ 모듈 주입                       │     │   │   │
│  │    │     │    - V48 Diversity Injection            │     │   │   │
│  │    │     │    - V51.2 Quality Amplifier            │     │   │   │
│  │    │     │    - V51.3 Agent Intelligence           │     │   │   │
│  │    │     │    - V51.4 Failure Learning             │     │   │   │
│  │    │     │    - V51.6 Foreshadow Tracker           │     │   │   │
│  │    │     │    - V55.2 Constitutional Self-Check    │     │   │   │
│  │    │     │    - V60.3 정지선 경고                   │     │   │   │
│  │    │     │    - V60.9 Stage 4→3 역방향 피드백      │     │   │   │
│  │    │     └─────────────────────────────────────────┘     │   │   │
│  │    │                      ▼                              │   │   │
│  │    │     ┌─────────────────────────────────────────┐     │   │   │
│  │    │     │ C. Architect 호출 (생성 방식 분기)       │     │   │   │
│  │    │     │    ┌─ reject=0 → Diversity Sampling     │     │   │   │
│  │    │     │    ├─ reject=1 → Two-Phase Blueprint    │     │   │   │
│  │    │     │    └─ reject≥2 → Tree of Thoughts       │     │   │   │
│  │    │     └─────────────────────────────────────────┘     │   │   │
│  │    │                      ▼                              │   │   │
│  │    │     ┌─────────────────────────────────────────┐     │   │   │
│  │    │     │ D. 검증 체인                            │     │   │   │
│  │    │     │    D.1 V52.1 Self-Reflection            │     │   │   │
│  │    │     │    D.2 V52.4 Cross-Agent Verification   │     │   │   │
│  │    │     │    D.3 Pattern Check (패턴 반영)        │     │   │   │
│  │    │     │    D.4 Stopline Violation (정지선)      │     │   │   │
│  │    │     │    D.5 V48.1 ContinuityInspector        │     │   │   │
│  │    │     │    D.6 V60.3 Pre-Director Checklist     │     │   │   │
│  │    │     │    D.7 Director 품질 검증               │     │   │   │
│  │    │     └─────────────────────────────────────────┘     │   │   │
│  │    │                      ▼                              │   │   │
│  │    │     ┌─────────────────────────────────────────┐     │   │   │
│  │    │     │ E. 결과 처리                            │     │   │   │
│  │    │     │    - PASS → 저장 + 다음 화              │     │   │   │
│  │    │     │    - REJECT → retry_feedback 갱신       │     │   │   │
│  │    │     │    - 3 Strike → Enrichment Level ↑      │     │   │   │
│  │    │     └─────────────────────────────────────────┘     │   │   │
│  │    └─────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 3. 저장 (에피소드별 원자적 저장)                             │   │
│  │    - SQLite: blueprints 테이블                              │   │
│  │    - 벡터 DB: 시맨틱 인덱싱                                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. 핵심 컴포넌트

### 3.1 Focus Package (Spotlight 시스템)

미래 정보 오염을 방지하기 위한 핵심 메커니즘:

```python
focus_package = {
    "MUST_FOCUS": ep_material,          # 이번 화 핵심 재료 (Spotlight)
    "FULL_MAP": masked_full_map,        # 마스킹된 아크 전체 맵
    "STOP_LINE": next_beat,             # 넘지 말아야 할 선 (Pacing Guard)
    "target_episode_focus": focus_tag,  # "[제 N화 전술 설계]"
    "beat_sequence": arc_data.get('beat_sequence', []),
    "arc_drive": arc_data.get('arc_drive', {}),
    "joint_docs": arc_data.get('joint_docs', {}),
    "status_shadow": arc_data.get('status_shadow', {}),
    "tactical_doc": arc_data.get('tactical_doc', ''),
    "hybrid_composition": arc_data.get('hybrid_composition', {})
}
```

### 3.2 정지선(Stopline) 시스템 (V60.3)

다음 화 내용이 현재 화에 유출되는 것을 방지:

```python
stopline_warning = (
    f"🚨🚨🚨 [정지선 경고 - 절대 준수] 🚨🚨🚨\n"
    f"다음 화 내용: 「{next_beat}」\n"
    f"→ 위 내용은 이번 화에서 절대 다루지 마세요.\n"
    f"→ 정지선을 넘으면 즉시 REJECT됩니다.\n"
)
```

### 3.3 Blueprint 생성 방식 분기

| 조건 | 생성 방식 | 설명 |
|------|----------|------|
| `reject_count=0` | **Diversity Sampling** | 3개 후보 병렬 생성 후 최적 선택 |
| `reject_count=1` | **Two-Phase Blueprint** | V54.4.1 Skeleton→Flesh 2단계 |
| `reject_count≥2` | **Tree of Thoughts** | V53.5 4분기 탐색 필살기 |

---

## 4. Two-Phase Blueprint (V54.4.1)

첫 번째 REJECT 시 발동하는 2단계 생성 시스템:

### Phase 1: Skeleton (구조 설계)
```json
{
    "ep_num": 5,
    "scene_count": 5,
    "scene_skeleton": [
        {
            "scene_id": 1,
            "scene_type": "대화",
            "location": "객잔",
            "characters": ["주인공", "장로"],
            "core_beat": "장로로부터 임무 하달",
            "tension_level": 3,
            "purpose": "사건 발단"
        }
    ],
    "item_movements": {
        "acquired": ["비급"],
        "consumed": [],
        "revealed": ["장로의 과거"]
    },
    "emotional_trajectory": {
        "start": "평온",
        "peak": "긴장",
        "end": "결의"
    },
    "cliffhanger_type": "위기"
}
```

### Phase 2: Flesh (상세화)
```json
{
    "ep_num": 5,
    "arc_num": 1,
    "volume_num": 1,
    "scene_breakdown": {
        "scene_1": {
            "scene_type": "대화",
            "purpose": "장로로부터 마교 침투 임무 하달",
            "characters": ["주인공", "장로"],
            "beats": ["장로 등장", "임무 설명", "비급 전수"],
            "emotional_note": "긴장과 결의",
            "spatial_anchor": "객잔 2층 밀실"
        }
    },
    "integrated_scenario": "상세 시나리오 (1500자 이상)...",
    "ending_hook": "객잔 밖에서 마교의 그림자가...",
    "relationship_changes": [],
    "time_flow": "저녁 → 밤"
}
```

---

## 5. 검증 체인

### 5.1 Self-Reflection (V52.1)
Architect 스스로 출력물을 검토하고 개선:

```python
if self.self_reflector and reject_count == 0 and blueprint_candidate:
    reflection_result = self.self_reflector.reflect_and_improve(
        output=bp_text,
        context=arc_context,
        target=ReflectionTarget.ARCHITECT
    )
    if reflection_result.improvement_score > 0:
        blueprint_candidate['integrated_scenario'] = reflection_result.improved
```

### 5.2 Cross-Agent Verification (V52.4)
Arc 설계 준수 검증:

```python
compliance_result = self.cross_verifier.verify_architect_compliance(
    blueprint=blueprint_candidate,
    arc_design=arc_data,
    use_llm=True
)

if compliance_result.level == ComplianceLevel.VIOLATION:
    # 점수 80% 미만 → REJECT
    retry_feedback = self.cross_verifier.generate_feedback(compliance_result, "architect")
    reject_count += 1
```

### 5.3 ContinuityInspector (V48.1)
전체 블루프린트 연속성 검증:

```python
prev_blueprints = self.agents['continuity_inspector'].get_prev_blueprints(
    current_ep=working_ep, window=None  # 전체 조회
)

continuity_result = self.agents['continuity_inspector'].inspect(
    current_ep=working_ep,
    current_blueprint=blueprint_candidate,
    prev_blueprints=prev_blueprints
)

if continuity_result.get('decision') == 'REJECT':
    # 연속성 위반 시 피드백과 함께 재시도
    retry_feedback = f"[연속성 위반] {fix_instructions}"
```

### 5.4 Director 품질 검증

```
┌─────────────────────────────────────────────────────────────┐
│ Director 검증 기준                                          │
├─────────────────────────────────────────────────────────────┤
│ 1. integrated_scenario 분량 검증 (1,200자 이상)             │
│ 2. 패턴 반영 여부 (hybrid_composition 준수)                 │
│ 3. 정지선 위반 검사 (다음 화 내용 포함 시 REJECT)           │
│ 4. 씬 완성도 평가 (scene_breakdown 품질)                    │
│ 5. 엔딩 훅 품질 (ending_hook 존재 및 적절성)                │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. V50+ 모듈 주입 상세

### 6.1 Diversity Engine (V48)

```python
diversity_injection = self.diversity_engine.get_architect_injection()
# 최근 10화 패턴 분석 → 사용 빈도 낮은 패턴 추천
```

### 6.2 Quality Amplifier (V51.2)

```python
architect_constraints = self.quality_amplifier.generate_architect_constraints(
    ep_num=working_ep,
    arc_data=arc_data,
    prev_blueprint=prev_blueprint
)
# 품질 제약 조건 동적 생성
```

### 6.3 Failure Learner (V51.4)

```python
learned_constraints = self.failure_learner.generate_constraint_prompt(stage=3)
# 과거 REJECT 사유 기반 제약 조건 학습
```

### 6.4 Stage 4→3 역방향 피드백 (V60.9)

```python
# 직전 화 Writer REJECT 이력 확인
stage4_rejects = [r for r in self.stage_rejection_history
                  if r.get('stage') == 4 and r.get('ep_num') == working_ep - 1]

if stage4_rejects:
    latest_reject = stage4_rejects[-1]
    reverse_guidance = latest_reject.get('reverse_guidance', '')
    # Blueprint 설계에 Writer 실패 원인 반영
```

---

## 7. Strike-Enrichment 시스템 (V35)

연속 REJECT 시 정밀도 레벨을 높이는 시스템:

```
┌──────────────────────────────────────────────────────────────────┐
│ Enrichment Level 진행                                            │
├──────────────────────────────────────────────────────────────────┤
│ Level 0 (기본)  → 3 Strike 누적 시                               │
│                    ↓                                             │
│ Level 1 (HIGH)  → 추가 3 Strike 누적 시                          │
│                    ↓                                             │
│ Level 2 (EXTREME) → 최대 정밀도                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Enrichment Directive 예시:

```python
enrichment_directive = (
    f"[🚨 SYSTEM OVERRIDE: ENRICHMENT LEVEL {enrichment_level} ({intensity})]\n"
    "1. **Micro-Segmentation**: 사건을 0.1초 단위로 쪼개어 묘사\n"
    "2. **Sensory Amplification**: 시각, 청각, 후각적 디테일 필수\n"
    "3. **Reaction Shot**: 조연들의 미세한 표정 변화 포함"
)
```

---

## 8. 블루프린트 데이터 구조

### 최종 저장 형태

```json
{
    "ep_num": 5,
    "arc_num": 1,
    "volume_num": 1,
    "scene_breakdown": {
        "scene_1": {
            "scene_type": "액션",
            "purpose": "적과의 첫 조우",
            "characters": ["주인공", "마교 제자"],
            "beats": ["기척 감지", "대치", "첫 공방"],
            "emotional_note": "긴장 고조",
            "spatial_anchor": "협곡 입구"
        },
        "scene_2": { ... },
        "scene_3": { ... }
    },
    "integrated_scenario": "상세 시나리오 (1,500자 이상)...",
    "ending_hook": "주인공의 검이 멈추는 순간, 마교 장로의 목소리가...",
    "prev_cliffhanger": "이전 화 클리프행어",
    "protagonist_state": {
        "location": "협곡",
        "inventory": ["철검", "금창약"],
        "injuries": "없음"
    },
    "relationship_changes": [],
    "time_flow": "새벽 → 아침"
}
```

---

## 9. 에러 처리

| 에러 유형 | 처리 방식 |
|----------|----------|
| Arc 데이터 누락 | 조기 종료 + 감사 로그 |
| Architect API 오류 | retry_feedback 갱신 후 재시도 |
| 정지선 위반 | 즉시 REJECT + 피드백 |
| 연속성 위반 | REJECT + fix_instructions 주입 |
| 12회 시도 초과 | Safety Stop + return |

---

## 10. 참조 파일

| 파일 | 역할 |
|------|------|
| `main_a.py:6228-7400` | `_stage_3_batch_blueprinting()` 메인 로직 |
| `modules/core/two_phase_generator.py:718-1045` | `TwoPhaseBlueprintGenerator` |
| `modules/domain/agents/continuity_inspector.py` | 연속성 검증 |
| `modules/domain/agents/architect.py` | `design_v20_breakdown()` |
