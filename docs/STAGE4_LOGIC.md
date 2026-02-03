# Stage 4: Manuscript Production Logic

## 1. 개요

Stage 4는 블루프린트를 기반으로 **최종 원고(Manuscript)**를 생성하는 단계입니다.

```
입력: Blueprint (scene_breakdown, integrated_scenario, ending_hook)
출력: 최종 원고 텍스트 (4,000~8,000자/화)
```

### 담당 에이전트
- **Writer**: 원고 집필 (모델 고정)
- **Director**: 품질 검증

### 모델 고정 (V40)
```python
# Stage 4에서는 Writer 모델 고정 (품질 저하 방지)
AIModels.STAGE4_FIXED_WRITER_MODEL = "gemini-3-pro-preview"
```

**중요**: Stage 4에서는 REJECT 횟수와 관계없이 `gemini-3-pro-preview` 고정 사용.

---

## 2. 전체 흐름도

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Stage 4: Manuscript Production                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 1. 초기화                                                    │   │
│  │    - Writer 모델 고정 (gemini-3-pro-preview)                 │   │
│  │    - Quad-Cache 시스템 점화                                  │   │
│  │    - V48 서사 다양성 엔진 초기화                              │   │
│  │    - 플랫폼 스타일 선택 (카카오/네이버)                       │   │
│  │    - 제1화: DNA 선택 (CYNICAL/CHRONICLE/SENSORY/PERSONAL)    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 2. 원고 생산 루프 (Sovereign Production)                     │   │
│  │    ┌─────────────────────────────────────────────────────┐   │   │
│  │    │ 2.1 데이터 준비                                      │   │   │
│  │    │     - Blueprint 로드                                │   │   │
│  │    │     - Arc 데이터 확보                                │   │   │
│  │    │     - 직전 화 원고 + 엔딩 추출                       │   │   │
│  │    │     - HUD 상태 스냅샷                                │   │   │
│  │    │     - 장르별 레퍼런스 샘플링                         │   │   │
│  │    └─────────────────────────────────────────────────────┘   │   │
│  │                           ▼                                  │   │
│  │    ┌─────────────────────────────────────────────────────┐   │   │
│  │    │ 2.2 Writer 집필 루프 (최대 4회)                      │   │   │
│  │    │     ┌─────────────────────────────────────────┐     │   │   │
│  │    │     │ A. 컨텍스트 구성                        │     │   │   │
│  │    │     │    - enriched_breakdown (BP + 벡터메모리)│     │   │   │
│  │    │     │    - fact_sheet (설정집 참조)           │     │   │   │
│  │    │     │    - focus_tag (이번 화 전술 포커스)    │     │   │   │
│  │    │     │    - purism_prompt (장르 가이드)        │     │   │   │
│  │    │     └─────────────────────────────────────────┘     │   │   │
│  │    │                      ▼                              │   │   │
│  │    │     ┌─────────────────────────────────────────┐     │   │   │
│  │    │     │ B. V50+ 모듈 주입                       │     │   │   │
│  │    │     │    - V48 Diversity Injection            │     │   │   │
│  │    │     │    - V51.2 Quality Amplifier            │     │   │   │
│  │    │     │    - V51.3 Agent Intelligence           │     │   │   │
│  │    │     │    - V51.4 Failure Learner              │     │   │   │
│  │    │     │    - V53.1 Dynamic Prompt Weighter      │     │   │   │
│  │    │     │    - V54.2 Context Compressor           │     │   │   │
│  │    │     │    - V54.5 Success Pattern Guide        │     │   │   │
│  │    │     │    - V55 Manuscript Enhancer            │     │   │   │
│  │    │     │    - V55.2 Constitutional Self-Check    │     │   │   │
│  │    │     │    - V55.3 Writer Template              │     │   │   │
│  │    │     │    - V60.3 재시도별 유연 기준           │     │   │   │
│  │    │     │    - V60.4 점수 추이 피드백             │     │   │   │
│  │    │     │    - V60.5 PASS 확률 예측               │     │   │   │
│  │    │     │    - V60.6 성공 원고 스타일 주입        │     │   │   │
│  │    │     │    - V60.8 사전 가이드 5종              │     │   │   │
│  │    │     └─────────────────────────────────────────┘     │   │   │
│  │    │                      ▼                              │   │   │
│  │    │     ┌─────────────────────────────────────────┐     │   │   │
│  │    │     │ C. Writer 호출 (생성 방식 분기)         │     │   │   │
│  │    │     │    ┌─ audit_attempt<2 → 기본 생성기     │     │   │   │
│  │    │     │    ├─ audit_attempt≥2 → Two-Phase MS    │     │   │   │
│  │    │     │    └─ (V60.6) → Beat 단위 분할 생성     │     │   │   │
│  │    │     └─────────────────────────────────────────┘     │   │   │
│  │    │                      ▼                              │   │   │
│  │    │     ┌─────────────────────────────────────────┐     │   │   │
│  │    │     │ D. 검증 체인                            │     │   │   │
│  │    │     │    D.1 분량 검증 (4,000자 이상)         │     │   │   │
│  │    │     │    D.2 씬 커버리지 검증 (80% 이상)      │     │   │   │
│  │    │     │    D.3 Hard Constraints 검증            │     │   │   │
│  │    │     │    D.4 Director 품질 검증               │     │   │   │
│  │    │     └─────────────────────────────────────────┘     │   │   │
│  │    │                      ▼                              │   │   │
│  │    │     ┌─────────────────────────────────────────┐     │   │   │
│  │    │     │ E. 결과 처리                            │     │   │   │
│  │    │     │    - PASS → 저장 + HUD 갱신 + 다음 화   │     │   │   │
│  │    │     │    - REJECT → feedback 갱신 + 재시도    │     │   │   │
│  │    │     │    - 4회 실패 → V60 강제 PASS 옵션      │     │   │   │
│  │    │     └─────────────────────────────────────────┘     │   │   │
│  │    └─────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 3. 저장 (원자적 트랜잭션)                                    │   │
│  │    - SQLite: manuscripts 테이블                              │   │
│  │    - 파일: drafts/{ep_num}.txt                               │   │
│  │    - 벡터 DB: 시맨틱 인덱싱                                  │   │
│  │    - HUD 스냅샷 저장                                         │   │
│  │    - Episode Bible 갱신                                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. 핵심 컴포넌트

### 3.1 플랫폼 최적화 스타일

```python
# 카카오페이지 스타일
{
    "tag": "KAKAO",
    "guide": (
        "카카오페이지: 매 화 사이다 전개 및 절벽걸기. "
        "설명을 생략하는 것이 아니라, 장면의 해상도를 4K 수준으로 높여라. "
        "인물이 숨을 들이키는 찰나의 폐부 감각, 옷자락이 스치는 소리까지 문장에 녹여내라."
    )
}

# 네이버 시리즈 스타일
{
    "tag": "NAVER",
    "guide": (
        "네이버 시리즈: 유려한 문장, 심리 묘사 강조. "
        "3~4문장 단위로 줄바꿈을 수행하여 여백을 극대화하라."
    )
}
```

### 3.2 DNA 선택 (제1화 전용)

| DNA | 특징 |
|-----|------|
| CYNICAL | 냉소적 관찰자 시점, 세상에 대한 비판적 시선 |
| CHRONICLE | 연대기적 서술, 사건 중심 전개 |
| SENSORY | 감각적 묘사 중심, 시각/청각/후각 디테일 |
| PERSONAL | 내면 독백 중심, 심리 묘사 강조 |

### 3.3 Writer 생성 방식 분기

| 조건 | 생성 방식 | 설명 |
|------|----------|------|
| `audit_attempt < 2` | **기본 생성기** | `write_v20_manuscript()` 직접 호출 |
| `audit_attempt ≥ 2` | **Two-Phase Manuscript** | V54.4 구조→본문 2단계 |
| 후반부 요약 문제 | **Beat 단위 분할** | V60.6 씬별 분리 생성 |

---

## 4. Two-Phase Manuscript (V54.4)

3회 이상 REJECT 시 발동하는 2단계 생성 시스템:

### Phase 1: Structure (구조 설계)
```json
{
    "scene_count": 5,
    "scene_structures": [
        {
            "scene_id": 1,
            "scene_type": "대화",
            "location": "객잔",
            "characters": ["주인공", "장로"],
            "purpose": "임무 하달",
            "emotional_beat": "상승",
            "key_dialogue_points": ["임무 설명", "경고"],
            "sensory_focus": "시각",
            "word_count_target": 800
        }
    ],
    "emotional_arc": {
        "start": "평온",
        "climax": "긴장",
        "end": "결의"
    },
    "cliffhanger_setup": "마교의 그림자"
}
```

### Phase 2: Content (본문 작성)
- Phase 1 구조를 기반으로 실제 원고 작성
- 각 씬의 `word_count_target` 준수
- `emotional_beat` 흐름 반영
- `sensory_focus` 감각 묘사 강화

---

## 5. V50+ 모듈 주입 상세

### 5.1 Quality Amplifier (V51.2)

```python
quality_constraints = self.quality_amplifier.generate_writer_constraints(
    ep_num=next_ep,
    blueprint=blueprint,
    prev_manuscript=prev_text,
    prev_items=prev_items  # 직전 화 아이템 추출
)
# 아이템 연속성, 상태 일관성 제약 생성
```

### 5.2 Failure Learner (V51.4)

```python
# 재시도 횟수에 따라 제약 강도 증가
learned_constraints = self.failure_learner.generate_constraint_prompt(
    stage=4,
    severity_filter="CRITICAL" if audit_attempt >= 2 else None
)
# 과거 REJECT 패턴 학습 → 동일 실수 방지
```

### 5.3 Writer Template (V55.3 + V56)

```python
ms_template = self.writer_template.generate_template(
    blueprint=blueprint,
    prev_ending=prev_text[-500:],
    inventory=current_inventory
)

# V56 구조 강제 주입
structure_enforcement = f"""
[V56 MANDATORY STRUCTURE ENFORCEMENT]
제{working_ep}화는 다음 구조를 절대 변경하면 안 됩니다:

1. 씬 개수: 정확히 {scene_count}개 (추가/삭제 금지)
2. 분량 목표: {total_min}~{total_max}자 (미달/초과 시 REJECT)
3. 클리프행어: 반드시 다음 내용으로 마무리
   → "{closing_hook[:100]}..."
4. 소지품 제약: 다음 아이템만 사용 가능
   → {', '.join(current_inventory[:5])}
"""
```

### 5.4 Context Compressor (V54.2)

```python
compression_result = self.context_compressor.compress(
    context={
        "blueprint": blueprint,
        "prev_text": prev_text[-3000:],
        "arc_data": arc_data
    },
    target_type="manuscript",
    max_chars=6000
)
# 토큰 절감: 압축률 80% 이하 시 압축 컨텍스트 사용
```

### 5.5 Success Pattern Guide (V54.5 + V60.4)

```python
# 재시도 시: REJECT 사유 기반 패턴 검색
target_context = {
    "ep_num": next_ep,
    "arc_num": arc_no
}

if audit_attempt > 0 and current_feedback:
    target_context["rejection_context"] = current_feedback[:500]
    target_context["retry_mode"] = True

pattern_guidance = self.success_patterns.get_guidance_from_patterns(
    content_type="manuscript",
    target_context=target_context
)
```

---

## 6. 재시도별 유연 기준 (V60.3)

| 시도 | Director 기준 | 분량 기준 | 씬 커버리지 |
|------|---------------|----------|------------|
| 1회차 | 엄격 | 5,000자 이상 | 100% |
| 2회차 | 약간 완화 | 4,500자 이상 | 80% (5개 씬 이상) |
| 3회차+ | 관대 | 4,000자 이상 | 60% (3~4개 씬) |

```python
if audit_attempt == 1:
    retry_guidance = (
        "- Director 기준이 약간 완화됩니다.\n"
        "- 5개 씬 이상 반영이면 PASS 가능.\n"
        "- 핵심 80% 반영 + Hard Constraints 준수 시 승인."
    )
elif audit_attempt >= 2:
    retry_guidance = (
        "- Director 기준이 관대해집니다.\n"
        "- 3~4개 씬만 있어도 밀도가 충분하면 PASS.\n"
        "- 치명적 오류(Hard Constraints)만 없으면 승인 가능.\n"
        "- 분량 4,000자만 넘으면 통과 가능성 높음."
    )
```

---

## 7. 검증 체인

### 7.1 분량 검증

```
최소 분량: 4,000자 (3회차+: 관대하게 적용)
권장 분량: 5,000~8,000자
초과 경고: 10,000자 이상 시 경고 (비차단)
```

### 7.2 씬 커버리지 검증

Blueprint의 `scene_breakdown` 대비 실제 반영률:

```python
# 씬 키워드 매칭으로 커버리지 계산
scene_keywords = extract_keywords(blueprint['scene_breakdown'])
covered = count_matched_keywords(manuscript, scene_keywords)
coverage = covered / total_scenes

# 기준
# - 1회차: 100% 필요
# - 2회차: 80% (5개 씬 중 4개)
# - 3회차+: 60% (5개 씬 중 3개)
```

### 7.3 Hard Constraints 검증

```
┌─────────────────────────────────────────────────────────────┐
│ Hard Constraints (위반 시 무조건 REJECT)                    │
├─────────────────────────────────────────────────────────────┤
│ 1. 죽은 NPC 부활 금지                                       │
│ 2. 소지품 연속성 위반 금지 (없는 아이템 사용)               │
│ 3. 시간 역행 금지 (저녁 → 아침 등)                         │
│ 4. 위치 점프 금지 (순간이동 없이 장소 변경)                 │
│ 5. 경지 급상승 금지 (복선 없는 돌파)                        │
└─────────────────────────────────────────────────────────────┘
```

### 7.4 Director 품질 검증

Director가 평가하는 항목:

| 항목 | 가중치 | 설명 |
|------|--------|------|
| 씬 완성도 | 30% | scene_breakdown 반영률 |
| 캐릭터 음성 | 20% | 대화 자연스러움 |
| 감각 묘사 | 15% | 시각/청각/촉각 디테일 |
| 엔딩 훅 | 15% | 클리프행어 품질 |
| 연속성 | 10% | 이전 화와의 연결 |
| 분량 | 10% | 목표 분량 달성 |

---

## 8. 저장 구조

### 8.1 SQLite (manuscripts 테이블)

```sql
CREATE TABLE manuscripts (
    ep_num INTEGER PRIMARY KEY,
    text TEXT NOT NULL,
    hud_snapshot TEXT,  -- JSON: 저장 시점 HUD 상태
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 8.2 파일 저장

```
projects/{project_name}/
└── drafts/
    ├── 0001.txt  # 제1화 원고
    ├── 0002.txt  # 제2화 원고
    └── ...
```

### 8.3 벡터 DB

```python
# 원고 청크를 벡터 DB에 인덱싱
self.memory.index_manuscript(
    ep_num=next_ep,
    content=final_pure_content,
    metadata={
        "arc_num": arc_no,
        "volume_num": volume_num,
        "style": selected_style["tag"]
    }
)
```

---

## 9. V60 강제 PASS 옵션

4회 연속 REJECT 시 마지막 원고를 강제로 PASS하는 옵션:

```python
# 재시도 실패 시 마지막 원고 저장
self._v60_last_manuscript = writer_res

# 4회 실패 후
if audit_attempt >= RetryLimits.WRITER_MAX_ATTEMPTS:
    if self._v60_last_manuscript:
        # 경고와 함께 강제 저장
        self.ui.log("⚠️ [V60] 4회 실패. 마지막 원고를 강제 저장합니다.")
        final_pure_content = self._v60_last_manuscript.get('content', '')
        self._v60_force_passed = True
```

---

## 10. Writer 호출 구조

```python
writer_res = self.agents['writer'].write_v20_manuscript(
    ep_num=next_ep,
    breakdown_doc=enriched_breakdown,      # BP + 벡터메모리 + fact_sheet
    master_bible=self.current_project.master_bible,
    hud_report=hud_report,                 # 현재 캐릭터 상태
    purism_prompt=purism,                  # 장르 가이드
    style_mode=selected_style["guide"],    # 플랫폼 스타일
    intro_dna=getattr(self.current_project, 'intro_dna', 'CYNICAL'),
    feedback=enhanced_feedback,            # V50+ 모듈 주입된 피드백
    prev_full_manuscript=effective_prev_text,  # 압축된 이전 원고
    arc_doc={
        "MUST_FOCUS_ON": focus_tag,
        "FULL_ARC_MAP": arc_tactical,
        "PATTERN_PROFILE": arc_data.get('hybrid_composition', {}),
        "PATTERN_MIXING_LOGIC": arc_data.get('hybrid_composition', {}).get('mixing_logic', '')
    },
    tactical_references=tactical_refs      # 클리셰 + 지리 + NPC HUD
)
```

---

## 11. 에러 처리

| 에러 유형 | 처리 방식 |
|----------|----------|
| Blueprint 없음 | 조기 종료 + Stage 3 선행 안내 |
| Arc 데이터 누락 | 조기 종료 + 감사 로그 |
| Writer API 오류 | feedback 갱신 후 재시도 |
| 분량 미달 | REJECT + 분량 증가 지시 |
| 4회 연속 실패 | V60 강제 PASS 또는 중단 |

---

## 12. 참조 파일

| 파일 | 역할 |
|------|------|
| `main_a.py:7411-8500+` | `_stage_4_sovereign_writing()` 메인 로직 |
| `modules/core/two_phase_generator.py:546-716` | `TwoPhaseManuscriptGenerator` |
| `modules/domain/agents/writer.py` | `write_v20_manuscript()` |
| `modules/domain/agents/director.py` | 품질 검증 |

---

## 13. 원고 품질 향상 팁

### 13.1 V55 Manuscript Enhancer 활용

```python
v55_result = self.manuscript_enhancer.analyze(
    manuscript=prev_text[-5000:],
    current_ep=next_ep
)

# 분석 결과 기반 피드백
if v55_result.subtext_ratio > 0.3:
    # 직접 서술을 묘사로 변환 유도
    guidance = f"직접 서술을 묘사로 변환하세요 (현재 {v55_result.subtext_ratio:.0%})"

if v55_result.page_turner_score < 60:
    # 문단 끝 훅 추가 유도
    guidance = f"문단 끝에 훅을 추가하세요 (현재 {v55_result.page_turner_score:.0f}점)"
```

### 13.2 Constitutional Self-Check (V55.2)

```python
constitutional_prompt = self.constitutional_checker.get_full_injection(
    stage=4,
    context={
        'blueprint': blueprint,
        'prev_manuscript': prev_text[-1000:],
        'inventory': current_inventory,
        'feedback': enhanced_feedback
    }
)
# 자체 검증 체크리스트 주입
```

### 13.3 Arc 위치 기반 기대치 가이드 (V60.5)

```python
arc_position_guide = self._generate_arc_position_guide(
    arc_pos, total_ep_in_arc
)

# 예시:
# - 아크 1화: 도입부, 캐릭터 소개 + 사건 발단
# - 아크 중반: 갈등 심화, 복선 배치
# - 아크 막화: 클라이막스, 강력한 클리프행어 필수
```
