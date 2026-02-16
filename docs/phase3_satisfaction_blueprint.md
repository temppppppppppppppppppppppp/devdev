# D. 대리만족 프레임워크 — Reader Satisfaction 검증 청사진

> 작성: 2026-02-16, checkpoint `0d676c8`
> 상태: **Step 1 완료** (reader_satisfaction 점수축 + 배점/가중치 재분배)

---

## 1) 현황 분석

### 현재 점수 체계

**ScoringValidator TIER 2** (LLM 5차원 + Python 4차원 = 100점):

| 차원 | 배점 | 산출 | 대리만족 관련 |
|------|------|------|-------------|
| `character_consistency` | 15 | LLM | - |
| `emotion_arc` | 20 | LLM | **간접** (감정 곡선) |
| `dialogue_quality` | 15 | LLM | - |
| `commercial_appeal` | 20 | LLM | **간접** (상업적 매력) |
| `pattern_diversity` | 10 | LLM | - |
| `prose_rhythm` | 5 | Python | - |
| `vocabulary_diversity` | 5 | Python | - |
| `sensory_balance` | 5 | Python | - |
| `show_dont_tell` | 5 | Python | - |
| **합계** | **100** | | |

**Director QUALITY_WEIGHTS** (scoring_validator → 최종 등급):

| 카테고리 | 가중치 | 매핑 차원 |
|----------|--------|-----------|
| `structure` | 0.15 | scene_completeness, scope_overflow, required_scenes |
| `prose` | 0.15 | prose_rhythm, vocabulary_diversity, show_dont_tell |
| `consistency` | 0.30 | character_consistency, relationship_consistency, continuity |
| `engagement` | 0.20 | emotion_arc, commercial_appeal, cliffhanger |
| `commercial` | 0.20 | commercial_appeal, pattern_diversity |
| **합계** | **1.00** | |

### 문제점 (Gap)

**"대리만족"을 직접 측정하는 차원이 없다.**

- `emotion_arc` (20점): 감정 곡선의 존재 여부만 평가. "독자가 쾌감을 느끼는가?"는 미포함.
- `commercial_appeal` (20점): 클리셰·트렌드 적합성 중심. "주인공이 유능해 보이는가?"는 미포함.
- `engagement` 카테고리 (0.20): emotion_arc + commercial_appeal + cliffhanger 평균. 대리만족 전용 축 없음.

**웹소설 핵심 재미인 "읽는 재미 = 대리만족" 검증이 빠져 있다.**

---

## 2) 범위

### 5대 만족도 축 (참고자료.md 3-F)

| # | 축 | 핵심 질문 | 적용 위치 |
|---|------|----------|-----------|
| S-1 | **대리만족** | 독자가 주인공을 통해 쾌감을 느끼는가? | ScoringValidator LLM |
| S-2 | **보상 체감** | 주인공 노력에 합당한 보상을 받는가? | 좌절-보상 타이머 |
| S-3 | **유능함** | 주인공이 유능해 보이는가? | ScoringValidator LLM |
| S-4 | **공감** | 독자가 주인공 감정에 공감하는가? | ScoringValidator LLM |
| S-5 | **좌절-보상 밸런스** | 무능해 보이는 구간이 너무 길지 않은가? | 에피소드 태깅 + 타이머 |

### 수정 파일

| 파일 | 변경 | 규모 |
|------|------|------|
| `modules/validation/scoring_validator.py` | `reader_satisfaction` 차원 추가 + 배점 재분배 | ~40줄 |
| `modules/domain/agents/director_grading.py` | `satisfaction` 카테고리 추가 + 가중치 재분배 | ~15줄 |
| `config/prompts/director_ensemble.yaml` | 대리만족 심사 기준 텍스트 추가 | ~30줄 |
| `modules/domain/agents/state_extractor.py` | 에피소드 만족도 태깅 메서드 추가 | ~60줄 |
| `modules/core/db_manager.py` | `episode_satisfaction_tags` 테이블 + CRUD | ~40줄 |
| `modules/validation/continuity_validator.py` | 좌절-보상 타이머 advisory 검사 | ~50줄 |
| `config/settings/validation.yaml` | `satisfaction:` 섹션 추가 | ~15줄 |
| `tests/test_satisfaction_framework.py` | 단위 테스트 | ~250줄 |
| **합계** | | **~500줄** |

---

## 3) 비범위

- Director PASS/REJECT 판정 로직 자체 변경 — **불변** (가중치만 조정)
- 기존 6-tier 검증 파이프라인 구조 변경 — **불변** (SCORING tier 내부 확장만)
- 재시도/패치 모드 분기 로직 — **불변**
- async/sync 구조 — **불변**
- LLM 모델 변경 — **불변**
- 새로운 validation tier 추가 — **불변** (기존 SCORING + ADVISORY tier 내에서 처리)

---

## 4) 설계안

### 4-1. ScoringValidator LLM 차원 확장

**변경: 배점 재분배 (총 80점 LLM 불변)**

| 차원 | 현재 | 변경 | 차이 |
|------|------|------|------|
| `character_consistency` | 15 | 15 | 0 |
| `emotion_arc` | 20 | **15** | **-5** |
| `dialogue_quality` | 15 | 15 | 0 |
| `commercial_appeal` | 20 | **15** | **-5** |
| `pattern_diversity` | 10 | 10 | 0 |
| `reader_satisfaction` | — | **10** | **+10** |
| **LLM 소계** | **80** | **80** | **0** |

Python 4차원 (20점): **불변**

**`reader_satisfaction` LLM 프롬프트 평가 기준:**

```
Article 7 — 독자 대리만족 (reader_satisfaction, max 10)
다음 3개 하위 항목으로 평가:
1. 성취/쾌감 장면 (0~4점): 주인공이 승리, 성장, 인정받는 장면이 존재하는가?
2. 주인공 유능함 (0~3점): 주인공이 자력으로 문제를 해결하는가? (타인 구출 의존 ×)
3. 감정 공감 (0~3점): 독자가 주인공의 감정에 공감할 수 있는 내면 묘사가 있는가?
```

**장르별 가중치 (GENRE_WEIGHTS 확장):**

```python
# scoring_validator.py GENRE_WEIGHTS 추가
"reader_satisfaction": {
    "wuxia": 1.3,       # 무협: 대리만족 비중 높음 (경지돌파, 복수)
    "hunter": 1.2,      # 헌터: 레벨업, 아이템 획득
    "investment": 0.8,   # 투자: 대리만족보다 전략/서스펜스
    "fantasy": 1.2,      # 판타지: 레벨업, 던전 클리어
}
```

### 4-2. Director QUALITY_WEIGHTS 재분배

**변경: `satisfaction` 카테고리 신설 (합계 1.00 불변)**

| 카테고리 | 현재 | 변경 | 차이 |
|----------|------|------|------|
| `structure` | 0.15 | 0.15 | 0 |
| `prose` | 0.15 | 0.15 | 0 |
| `consistency` | 0.30 | **0.25** | **-0.05** |
| `engagement` | 0.20 | **0.15** | **-0.05** |
| `commercial` | 0.20 | 0.20 | 0 |
| `satisfaction` | — | **0.10** | **+0.10** |
| **합계** | **1.00** | **1.00** | **0** |

**category_mapping 추가:**

```python
category_mapping = {
    # ... 기존 5개 유지 ...
    'satisfaction': ['reader_satisfaction', 'emotion_arc'],
}
```

> `satisfaction` 카테고리는 `reader_satisfaction` (10점) + `emotion_arc` (15점)의 평균.
> 이를 통해 대리만족 + 감정 곡선을 통합 평가.

### 4-3. Director 프롬프트 확장

`config/prompts/director_ensemble.yaml` 에 대리만족 심사 기준 추가:

```yaml
satisfaction_criteria: |
  ## 대리만족 심사 기준

  다음 항목을 확인하세요:
  1. 이 에피소드에 독자가 쾌감을 느낄 수 있는 장면이 있는가?
     - 성취: 주인공이 목표를 달성하거나 강적을 제압
     - 성장: 주인공의 능력이 눈에 띄게 향상
     - 인정: 주인공이 타인으로부터 인정/존경을 받음
  2. 주인공이 유능해 보이는가?
     - 자력 해결 > 타인 도움 (이상적: 60% 이상 자력)
  3. 좌절 구간이 너무 길지 않은가?
     - 현재 좌절 연속 화수 참고 (3화 이상이면 보상 필요)

satisfaction_genre_examples:
  wuxia: "경지 돌파, 강자 제압, 비급 획득, 복수 달성"
  hunter: "레벨업, 레어 아이템 획득, 던전 클리어, 동료 인정"
  fantasy: "스킬 습득, 퀘스트 완료, 보스 격파, 영지 확장"
  investment: "투자 성공, 정보 선점, 라이벌 제압, 자산 증가"
```

### 4-4. 에피소드 만족도 태깅

**위치: `state_extractor.py` — `extract_satisfaction_tag()` 메서드 추가**

LLM에게 에피소드 완료 후 자동 분류를 요청:

```python
def extract_satisfaction_tag(self, manuscript: str, ep_num: int) -> dict:
    """에피소드의 만족도 태그를 추출한다.

    Returns:
        {
            "ep_num": 3,
            "primary_tag": "성취",          # 성취|좌절|이행|일상|전투|성장
            "satisfaction_score": 7,         # 1~10 (독자 쾌감 체감 예상치)
            "protagonist_agency": "자력",    # 자력|협력|타인의존
            "frustration_flag": False,       # 좌절 에피소드 여부
        }
    """
```

**DB 저장: `episode_satisfaction_tags` 테이블 (db_manager.py)**

```sql
CREATE TABLE IF NOT EXISTS episode_satisfaction_tags (
    ep_num INTEGER PRIMARY KEY,
    primary_tag TEXT NOT NULL,
    satisfaction_score INTEGER DEFAULT 5,
    protagonist_agency TEXT DEFAULT '자력',
    frustration_flag INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
```

**호출 시점**: Stage4 PASS 후 후처리 훅 (기존 `_post_pass_hooks()` 확장)

### 4-5. 좌절-보상 타이머

**위치: `continuity_validator.py` — `_check_frustration_streak()` 메서드 추가**

```python
def _check_frustration_streak(self, ep_num: int, db) -> list[str]:
    """최근 에피소드의 좌절 연속 화수를 검사한다.

    Rules:
    - 좌절 3화 연속: WARNING "보상 에피소드 권장"
    - 좌절 5화 연속: WARNING "대리만족 부재 심각" (Director에 전달)

    Returns:
        경고 메시지 리스트 (빈 리스트 = 정상)
    """
    tags = db.get_recent_satisfaction_tags(ep_num, lookback=5)
    streak = 0
    for tag in reversed(tags):
        if tag["frustration_flag"]:
            streak += 1
        else:
            break

    warnings = []
    if streak >= 5:
        warnings.append(
            f"[Satisfaction] 좌절 {streak}화 연속 — 대리만족 부재 심각. "
            f"다음 에피소드에 보상 장면 필수."
        )
    elif streak >= 3:
        warnings.append(
            f"[Satisfaction] 좌절 {streak}화 연속 — 보상 에피소드 권장."
        )
    return warnings
```

**주입 시점**: ADVISORY tier (Stage4 `_run_validation_pipeline()` 내)

> **핵심 원칙 준수**: Python은 좌절 연속 화수를 "감지"만 하고, 경고를 Director에 전달.
> Python이 REJECT하지 않으며, Director가 최종 판단.

### 4-6. YAML 설정

`config/settings/validation.yaml` 확장:

```yaml
satisfaction:
  max_frustration_streak: 3        # 좌절 연속 화수 경고 임계값
  critical_frustration_streak: 5   # 좌절 연속 화수 심각 경고 임계값
  min_reward_frequency: 5          # N화당 최소 1회 대리만족 장면
  protagonist_agency_ratio: 0.6    # 자력해결 / 전체해결 >= 60%
  rescue_limit_per_arc: 2          # Arc당 타인구출 상한
```

---

## 5) 수용 기준 (AC)

| # | 수용 기준 | 검증 방법 |
|---|----------|----------|
| AC-1 | `reader_satisfaction` 차원이 ScoringValidator LLM 프롬프트에 포함됨 | Unit: mock LLM → 프롬프트에 `reader_satisfaction` 키워드 확인 |
| AC-2 | LLM 배점 합계 80점 불변 (15+15+15+15+10+10) | Unit: 차원별 max 합산 == 80 |
| AC-3 | `satisfaction` 카테고리가 QUALITY_WEIGHTS에 존재 (0.10) | Unit: QUALITY_WEIGHTS 합계 == 1.00, `satisfaction` in keys |
| AC-4 | `category_mapping['satisfaction']` 에 `reader_satisfaction` 포함 | Unit: 키 존재 검증 |
| AC-5 | `extract_satisfaction_tag()` 가 6개 태그 중 하나를 반환 | Unit: mock LLM → 유효한 tag dict 반환 |
| AC-6 | `episode_satisfaction_tags` 테이블에 태그 저장/조회 가능 | Unit: in-memory DB → insert → select 검증 |
| AC-7 | 좌절 3화 연속 시 WARNING 메시지 생성 | Unit: mock tags → 경고 리스트 길이 1 |
| AC-8 | 좌절 5화 연속 시 CRITICAL WARNING 메시지 생성 | Unit: mock tags → "심각" 키워드 포함 |
| AC-9 | validation.yaml `satisfaction` 섹션이 로드됨 | Unit: threshold_helper → satisfaction.max_frustration_streak 반환 |
| AC-10 | 기존 테스트 286개 전량 통과 (회귀 없음) | Gate: pytest 전체 |

---

## 6) 테스트 전략

### Unit 테스트 (~15개)

| # | 클래스 | 테스트 | 검증 |
|---|--------|--------|------|
| 1 | `TestScoringDimensions` | `test_reader_satisfaction_dimension_exists` | LLM 프롬프트에 `reader_satisfaction` 포함 |
| 2 | | `test_llm_dimensions_total_80` | LLM 5→6차원 합계 80 |
| 3 | | `test_reader_satisfaction_genre_weights` | GENRE_WEIGHTS에 reader_satisfaction 키 존재 |
| 4 | `TestQualityWeights` | `test_satisfaction_category_exists` | QUALITY_WEIGHTS 6개 키, 합계 1.00 |
| 5 | | `test_category_mapping_satisfaction` | category_mapping['satisfaction'] 에 reader_satisfaction 포함 |
| 6 | | `test_grade_with_satisfaction` | satisfaction 카테고리 포함 시 등급 계산 정상 |
| 7 | `TestSatisfactionTag` | `test_extract_tag_valid` | mock LLM → 유효한 태그 반환 |
| 8 | | `test_extract_tag_fallback` | LLM 실패 시 기본값 반환 |
| 9 | | `test_tag_db_roundtrip` | in-memory DB → 저장 → 조회 일치 |
| 10 | `TestFrustrationTimer` | `test_no_frustration_no_warning` | 좌절 0회 → 빈 리스트 |
| 11 | | `test_frustration_3_warning` | 좌절 3회 → 경고 1건 |
| 12 | | `test_frustration_5_critical` | 좌절 5회 → "심각" 경고 |
| 13 | | `test_frustration_reset_after_reward` | 중간에 성취 → streak 초기화 |
| 14 | `TestYAMLConfig` | `test_satisfaction_settings_loaded` | validation.yaml satisfaction 섹션 로드 |
| 15 | | `test_threshold_helper_satisfaction` | threshold_helper로 satisfaction 값 조회 |

### 회귀 스위트

| 스위트 | 통과 기대 |
|--------|----------|
| 기존 286개 | 286 (불변) |
| 신규 ~15개 | 15 |
| **합계** | **~301** |

---

## 7) 실행 단계 계획

### Step 1: ScoringValidator 확장 (MVP) ✅ 완료 (`0d676c8`)

**수정 파일**:
- `modules/validation/scoring_validator.py` — `reader_satisfaction` 차원 추가, 배점 재분배
- `modules/domain/agents/director_grading.py` — `satisfaction` 카테고리 + 가중치 재분배
- `tests/test_satisfaction_framework.py` — 테스트 1~6

**삽입 내용**:
1. `scoring_validator.py`: LLM 프롬프트에 Article 7 추가 (reader_satisfaction, max 10)
2. `scoring_validator.py`: `emotion_arc` max 20→15, `commercial_appeal` max 20→15
3. `scoring_validator.py`: GENRE_WEIGHTS에 `reader_satisfaction` 가중치 추가
4. `director_grading.py`: QUALITY_WEIGHTS에 `satisfaction: 0.10` 추가, consistency 0.30→0.25, engagement 0.20→0.15
5. `director_grading.py`: category_mapping에 `satisfaction: ['reader_satisfaction', 'emotion_arc']` 추가

**게이트**: py_compile + SovereignApp import + 기존 286 + 신규 6 + pre-commit

### Step 2: Director 프롬프트 확장

**수정 파일**:
- `config/prompts/director_ensemble.yaml` — 대리만족 심사 기준 텍스트 추가

**삽입 내용**:
1. `satisfaction_criteria` 키: 3개 평가 항목 (성취/유능함/좌절 밸런스)
2. `satisfaction_genre_examples` 키: 4개 장르별 대리만족 유형 예시

**게이트**: py_compile + 기존 + pre-commit

### Step 3: 에피소드 태깅 + DB

**수정 파일**:
- `modules/domain/agents/state_extractor.py` — `extract_satisfaction_tag()` 추가
- `modules/core/db_manager.py` — `episode_satisfaction_tags` 테이블 + CRUD
- `modules/core/stage4_orchestrator.py` — `_post_pass_hooks()` 에서 태깅 호출
- `tests/test_satisfaction_framework.py` — 테스트 7~9 추가

**게이트**: py_compile + SovereignApp import + 기존 + 신규 9 + pre-commit

### Step 4: 좌절-보상 타이머

**수정 파일**:
- `modules/validation/continuity_validator.py` — `_check_frustration_streak()` 추가
- `modules/core/stage4_orchestrator.py` — ADVISORY tier에서 좌절 검사 호출
- `tests/test_satisfaction_framework.py` — 테스트 10~13 추가

**게이트**: py_compile + SovereignApp import + 기존 + 신규 13 + pre-commit

### Step 5: YAML 설정 + 문서

**수정 파일**:
- `config/settings/validation.yaml` — `satisfaction:` 섹션 추가
- `tests/test_satisfaction_framework.py` — 테스트 14~15 추가
- `내일작업.md`, `CLAUDE.md`, `docs/프로젝트_현황_로드맵_2026-02-14.md` — 문서 동기화

**게이트**: py_compile + 전체 pytest + pre-commit

---

## 8) 영향도 분석

### 점수 변동 예상

| 원고 유형 | 현재 점수 | 예상 변동 | 근거 |
|----------|----------|----------|------|
| 대리만족 高 (경지돌파, 복수 달성) | 75 | **+3~5** | reader_satisfaction 10/10, 무협 가중치 1.3 |
| 대리만족 中 (일상, 수련) | 70 | **±0~2** | reader_satisfaction 5/10, 재분배 상쇄 |
| 대리만족 低 (연속 좌절, 패배) | 72 | **-3~5** | reader_satisfaction 2/10, emotion_arc도 감소 |

> 의도된 효과: 대리만족이 없는 원고의 점수가 낮아져서, Director가 자연스럽게
> "보상 장면 추가" 피드백을 제공하게 됨.

### 기존 차원 영향

- `emotion_arc` 20→15: 감정 곡선은 여전히 평가하되, 비중 축소. `satisfaction` 카테고리에서 합산되므로 실질 영향은 미미.
- `commercial_appeal` 20→15: 상업적 매력은 `commercial` 카테고리에서 독립 평가. 비중 축소분은 reader_satisfaction으로 보완.
- `consistency` 0.30→0.25: 일관성 여전히 최고 가중치. 0.05 감소분은 연속 좌절 감지로 보완.

---

## 9) 리스크 및 완화

| 리스크 | 심각도 | 완화 |
|--------|--------|------|
| LLM이 `reader_satisfaction`을 일관되게 평가하지 못함 | 중 | 프롬프트에 구체적 하위 항목 3개 + 장르별 예시 제공 |
| 배점 재분배로 기존 합격/불합격 경계 변동 | 중 | Step 1 완료 후 기존 원고 5개로 점수 비교 테스트 |
| 에피소드 태깅 LLM 호출 추가 → latency | 저 | 태깅은 PASS 후 후처리 (비차단). 실패 시 비전파 |
| 좌절 타이머 오탐 (의도적 긴장 구간) | 중 | Advisory 전용 (Python은 REJECT 금지), Director가 판단 |
| YAML 설정 미로드 시 기본값 | 저 | threshold_helper 기존 패턴 (default 인자) 활용 |

---

## 10) 롤백 전략

| 방법 | 조치 |
|------|------|
| **코드 롤백** | `git revert <commit>` — reader_satisfaction 차원 제거, 배점 원복 |
| **점수 비활성화** | GENRE_WEIGHTS `reader_satisfaction: 0.0` → 실질 0점 |
| **타이머 비활성화** | validation.yaml `satisfaction.max_frustration_streak: 999` → 실질 무한 |
| **태깅 비활성화** | Stage4 후처리 훅에서 태깅 호출 주석 처리 |
| **영향 범위** | ScoringValidator + DirectorGrading 배점만 원복하면 기존 동작 100% 복원 |
