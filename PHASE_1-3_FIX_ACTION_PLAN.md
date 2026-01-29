# Phase 1-3 코드 수정 실행 계획

**생성일**: 2026-01-28
**목표**: Critical/High 이슈 우선 해결 → 안정적 배포

---

## 📅 수정 일정 (총 10일 예상)

| Phase | 일정 | 이슈 개수 | 목표 |
|-------|------|-----------|------|
| **Phase A** | Day 1-2 | Critical 8건 | 크래시 방지 |
| **Phase B** | Day 3-7 | High 12건 | 정확도 향상 |
| **Phase C** | Day 8-10 | Medium 5건 (선별) | 안정성 강화 |

---

## 🔴 Phase A: Critical 이슈 수정 (Day 1-2)

### ✅ Issue #1: blocking_validator.py - HUD equipment 타입 체크

**파일**: `modules/validation/blocking_validator.py`
**라인**: 100-148

**현재 코드**:
```python
def _check_unowned_item_usage(self, manuscript: str, context: dict) -> dict:
    encyclopedia = context.get('encyclopedia', {})
    martial_hud = context.get('martial_hud', {})

    # HUD에서 소유 아이템 목록
    owned_items = []
    if isinstance(martial_hud, dict):
        actual_truth = martial_hud.get('actual_truth', {})
        if isinstance(actual_truth, dict):
            owned_items = actual_truth.get('equipment', [])
            if isinstance(owned_items, str):
                owned_items = [owned_items]
            elif not isinstance(owned_items, list):
                owned_items = []
```

**수정 후 코드**:
```python
def _check_unowned_item_usage(self, manuscript: str, context: dict) -> dict:
    """미획득 아이템 사용 체크 (개선된 타입 안전성)"""
    encyclopedia = context.get('encyclopedia', {})
    martial_hud = context.get('martial_hud', {})

    # HUD에서 소유 아이템 목록 (방어적 추출)
    owned_items = []
    if isinstance(martial_hud, dict):
        actual_truth = martial_hud.get('actual_truth', {})
        if isinstance(actual_truth, dict):
            equipment = actual_truth.get('equipment', [])

            # 다양한 타입 처리
            if isinstance(equipment, list):
                owned_items = equipment
            elif isinstance(equipment, str):
                owned_items = [equipment] if equipment else []
            elif isinstance(equipment, dict):
                # HUD가 dict 형태일 경우 (예: {'혼철대도': True})
                owned_items = [k for k, v in equipment.items() if v]
            else:
                # 예상치 못한 타입
                print(f"[WARNING] Unexpected equipment type: {type(equipment)}")
                owned_items = []

    # 안전성 확인 로그
    if not isinstance(owned_items, list):
        print(f"[ERROR] owned_items is not a list: {type(owned_items)}")
        owned_items = []
```

**추가 작업**:
- HUD 데이터 구조 문서화 (`modules/core/martial_manager.py` 확인 필요)
- Unit test 추가

---

### ✅ Issue #2: scoring_validator.py - LLM 실패 시 fallback 개선

**파일**: `modules/validation/scoring_validator.py`
**라인**: 79-164

**현재 코드**:
```python
def _calculate_llm_scores(self, manuscript: str, context: dict) -> dict:
    if not self.client:
        # LLM 없으면 중간 점수로 가정
        return {
            'character_consistency': {'score': 10, 'max': 15},
            'emotion_arc': {'score': 14, 'max': 20},
            ...
        }
```

**수정 후 코드**:
```python
def _calculate_llm_scores(self, manuscript: str, context: dict) -> dict:
    """LLM으로 평가해야 하는 점수"""
    if not self.client:
        # LLM 없으면 경고하고 NULL 반환
        print(f"[ERROR] LLM client not available for SCORING evaluation!")
        print(f"       This will result in INCOMPLETE validation.")
        return self._get_null_scores(reason="LLM_CLIENT_MISSING")

    try:
        # LLM 호출 (기존 코드)
        ...

    except Exception as e:
        print(f"[ERROR] LLM evaluation failed: {e}")
        print(f"       Attempting Python-based fallback...")

        # Python 기반 간단 휴리스틱 fallback
        return self._fallback_heuristic_scores(manuscript, context)

def _get_null_scores(self, reason: str) -> dict:
    """NULL 점수 반환 (검증 실패 표시)"""
    return {
        'character_consistency': {'score': 0, 'max': 15, 'reason': f'EVAL_FAILED: {reason}'},
        'emotion_arc': {'score': 0, 'max': 20, 'reason': f'EVAL_FAILED: {reason}'},
        'dialogue_quality': {'score': 0, 'max': 15, 'reason': f'EVAL_FAILED: {reason}'},
        'commercial_appeal': {'score': 0, 'max': 20, 'reason': f'EVAL_FAILED: {reason}'},
        'pattern_diversity': {'score': 0, 'max': 10, 'reason': f'EVAL_FAILED: {reason}'},
        '_warning': 'LLM evaluation failed - scores are unreliable'
    }

def _fallback_heuristic_scores(self, manuscript: str, context: dict) -> dict:
    """Python 기반 간단 휴리스틱 평가 (LLM 실패 시)"""
    # 최소한의 품질 체크
    length = len(manuscript)
    has_dialogue = '"' in manuscript or '"' in manuscript
    has_action = any(w in manuscript for w in ['휘둘', '날아', '뛰어', '달려'])

    # 기본 점수 (보수적)
    base_score = 7 if length > 4000 else 5

    return {
        'character_consistency': {
            'score': base_score,
            'max': 15,
            'reason': 'HEURISTIC: Minimal check passed'
        },
        'emotion_arc': {
            'score': base_score + 2,
            'max': 20,
            'reason': 'HEURISTIC: Basic structure present'
        },
        'dialogue_quality': {
            'score': base_score if has_dialogue else base_score - 2,
            'max': 15,
            'reason': f'HEURISTIC: Dialogue {"found" if has_dialogue else "missing"}'
        },
        'commercial_appeal': {
            'score': base_score + 1,
            'max': 20,
            'reason': 'HEURISTIC: Length appropriate'
        },
        'pattern_diversity': {
            'score': base_score - 1 if has_action else base_score - 3,
            'max': 10,
            'reason': f'HEURISTIC: Action scenes {"present" if has_action else "limited"}'
        },
        '_warning': 'Scores based on heuristics only - LLM evaluation recommended'
    }
```

**추가 작업**:
- `validation_orchestrator.py`에서 `_warning` 필드 감지 시 사용자에게 경고 표시
- 로그 파일에 LLM 실패 기록

---

### ✅ Issue #3: validation_orchestrator.py - Constitution 로드 에러 처리

**파일**: `modules/validation/validation_orchestrator.py`
**라인**: 24-26

**현재 코드**:
```python
# Constitution 로드
from modules.core.quality_constitution import get_constitution_for_genre
self.constitution = get_constitution_for_genre(genre)
```

**수정 후 코드**:
```python
# Constitution 로드 (에러 처리 추가)
try:
    from modules.core.quality_constitution import get_constitution_for_genre
    self.constitution = get_constitution_for_genre(genre)
    print(f"[V0128] Constitution loaded for genre: {genre}")
except (ImportError, FileNotFoundError) as e:
    print(f"[WARNING] Constitution load failed: {e}")
    print(f"          Using default constitution")
    self.constitution = self._get_default_constitution()
except Exception as e:
    print(f"[ERROR] Unexpected error loading constitution: {e}")
    self.constitution = self._get_default_constitution()

def _get_default_constitution(self) -> str:
    """기본 Constitution 반환 (파일 로드 실패 시)"""
    return """
# Default Quality Constitution

## Article 1: 문장 품질 (20점)
명확하고 리듬감 있는 문장 사용

## Article 2: 캐릭터 일관성 (15점)
등장인물의 행동이 설정과 일치

## Article 3: 감정선 (20점)
자연스러운 감정 변화

## Article 4: 대화 품질 (15점)
캐릭터 특성을 반영한 대사

## Article 5: 상업성 (20점)
독자를 끌어당기는 요소

## Article 6: 패턴 다양성 (10점)
클리셰 회피
"""
```

---

### ✅ Issue #4: performance_dashboard.py - 무한 새로고침 제거

**파일**: `performance_dashboard.py`
**라인**: 384-387

**현재 코드**:
```python
# 자동 새로고침
import time
time.sleep(refresh_interval)
st.rerun()
```

**수정 후 코드**:
```python
# 자동 새로고침 (조건부)
if st.sidebar.checkbox("Auto-refresh", value=False):
    import time
    time.sleep(refresh_interval)
    st.rerun()
else:
    # 수동 새로고침 버튼
    if st.sidebar.button("🔄 Refresh"):
        st.rerun()
```

**또는 더 나은 방법**:
```python
# 페이지 하단에 새로고침 안내
st.markdown("---")
col1, col2 = st.columns([3, 1])
with col1:
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
with col2:
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
```

---

### ✅ Issue #5: data_collector.py - 파일명 충돌 방지

**파일**: `modules/core/data_collector.py`
**라인**: 84-98

**현재 코드**:
```python
def _save_approved(self, ep_num: int, data: dict):
    filename = f"ep_{ep_num:03d}_approved.json"
    filepath = os.path.join(self.project_dir, "approved", filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
```

**수정 후 코드**:
```python
def _save_approved(self, ep_num: int, data: dict):
    """승인된 원고 저장 (버전 관리)"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"ep_{ep_num:03d}_{timestamp}_approved.json"
    filepath = os.path.join(self.project_dir, "approved", filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # 최신 버전 심볼릭 링크 (선택적)
    latest_link = os.path.join(self.project_dir, "approved", f"ep_{ep_num:03d}_latest.json")
    try:
        if os.path.exists(latest_link):
            os.remove(latest_link)
        # Windows는 심볼릭 링크 대신 복사
        import shutil
        shutil.copy2(filepath, latest_link)
    except Exception as e:
        print(f"[WARNING] Could not create latest link: {e}")

def _save_rejected(self, ep_num: int, data: dict):
    """거부된 원고 저장 (버전 관리)"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"ep_{ep_num:03d}_{timestamp}_rejected.json"
    filepath = os.path.join(self.project_dir, "rejected", filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
```

---

### ✅ Issue #6: response_schemas.py - 검증 함수 개선 또는 제거

**파일**: `modules/core/response_schemas.py`
**라인**: 265-286

**현재 코드**:
```python
def validate_response_against_schema(response: dict, schema: types.Schema) -> bool:
    if not isinstance(response, dict):
        return False

    # required 필드 체크
    required_props = schema.properties.keys() if hasattr(schema, 'properties') else []
    for prop in required_props:
        if prop not in response:
            return False

    return True
```

**수정 후 코드** (Option 1: 개선):
```python
def validate_response_against_schema(response: dict, schema: types.Schema) -> tuple[bool, list[str]]:
    """
    응답이 스키마를 만족하는지 검증

    Returns:
        (is_valid, errors) 튜플
    """
    errors = []

    if not isinstance(response, dict):
        return False, ["Response is not a dictionary"]

    # required 필드 체크
    if hasattr(schema, 'required'):
        for prop in schema.required:
            if prop not in response:
                errors.append(f"Missing required field: {prop}")

    # 타입 체크 (기본만)
    if hasattr(schema, 'properties'):
        for prop_name, prop_schema in schema.properties.items():
            if prop_name in response:
                value = response[prop_name]
                expected_type = prop_schema.type if hasattr(prop_schema, 'type') else None

                if expected_type:
                    type_mapping = {
                        types.Type.STRING: str,
                        types.Type.INTEGER: int,
                        types.Type.NUMBER: (int, float),
                        types.Type.BOOLEAN: bool,
                        types.Type.ARRAY: list,
                        types.Type.OBJECT: dict
                    }
                    expected_python_type = type_mapping.get(expected_type)

                    if expected_python_type and not isinstance(value, expected_python_type):
                        errors.append(f"Field '{prop_name}' has wrong type: expected {expected_python_type}, got {type(value)}")

    return len(errors) == 0, errors
```

**수정 후 코드** (Option 2: 제거 및 주석):
```python
# def validate_response_against_schema(...):
#     """
#     DEPRECATED: Gemini API의 response_schema가 자동으로 구조를 보장하므로
#     이 함수는 불필요합니다. 실제 검증이 필요하면 pydantic 사용을 권장합니다.
#     """
#     pass
```

---

### ✅ Issue #7: prompt_optimizer.py - Division by zero 방지 전역 적용

**파일**: `modules/core/prompt_optimizer.py`
**라인**: 73-98

**현재 코드**:
```python
def _analyze_category_scores(self, results: List[Dict]) -> Dict[str, float]:
    for category in categories:
        scores = []
        for r in results:
            breakdown = r.get('scoring_result', {}).get('breakdown', {})
            if category in breakdown:
                score = breakdown[category].get('score', 0)
                max_score = breakdown[category].get('max', 100)
                percentage = (score / max_score * 100) if max_score > 0 else 0  # 여기만 방어
                scores.append(percentage)
```

**수정 후 코드**:
```python
def _analyze_category_scores(self, results: List[Dict]) -> Dict[str, float]:
    """카테고리별 평균 점수 분석 (개선된 에러 처리)"""
    categories = [
        'character_consistency',
        'emotion_arc',
        'dialogue_quality',
        'commercial_appeal',
        'pattern_diversity'
    ]

    category_scores = {}

    for category in categories:
        scores = []
        for r in results:
            try:
                breakdown = r.get('scoring_result', {}).get('breakdown', {})
                if category not in breakdown:
                    continue

                cat_data = breakdown[category]
                if not isinstance(cat_data, dict):
                    print(f"[WARNING] Invalid category data for {category}: {type(cat_data)}")
                    continue

                score = cat_data.get('score', 0)
                max_score = cat_data.get('max', 100)

                # 안전한 나눗셈
                if max_score > 0:
                    percentage = (score / max_score) * 100
                    scores.append(percentage)
                else:
                    print(f"[WARNING] max_score is 0 for {category}")

            except (TypeError, ValueError, KeyError) as e:
                print(f"[WARNING] Error processing {category}: {e}")
                continue

        if scores:
            category_scores[category] = statistics.mean(scores)
        else:
            print(f"[WARNING] No valid scores for {category}")
            category_scores[category] = 0.0

    return category_scores
```

---

### ✅ Issue #8: batch_validator.py - Event loop 안전성 개선

**파일**: `modules/validation/batch_validator.py`
**라인**: 263-276

**현재 코드**:
```python
if use_async:
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            results = validator.validate_batch_sync(manuscripts)
        else:
            results = loop.run_until_complete(
                validator.validate_batch_async(manuscripts)
            )
    except RuntimeError:
        results = validator.validate_batch_sync(manuscripts)
```

**수정 후 코드**:
```python
if use_async:
    try:
        # 실행 중인 루프 감지
        try:
            loop = asyncio.get_running_loop()
            # 이미 async 컨텍스트 안에 있음
            print("[INFO] Running inside async context - using sync mode")
            results = validator.validate_batch_sync(manuscripts)
        except RuntimeError:
            # async 컨텍스트 밖 - 새 루프 생성
            print("[INFO] Creating new event loop for async validation")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                results = loop.run_until_complete(
                    validator.validate_batch_async(manuscripts)
                )
            finally:
                loop.close()

    except Exception as e:
        print(f"[WARNING] Async validation failed: {e}")
        print(f"          Falling back to sync mode")
        results = validator.validate_batch_sync(manuscripts)
else:
    # ThreadPoolExecutor 사용
    results = validator.validate_batch_sync(manuscripts)
```

---

## 🟠 Phase B: High 이슈 수정 (Day 3-7)

### ✅ Issue #9: blocking_validator.py - 문맥 기반 검증 개선

**파일**: `modules/validation/blocking_validator.py`
**라인**: 127-146

**개선 방향**:
1. 부정문 감지 추가
2. 동사 활용 분석 (간단한 패턴)
3. 2차 LLM 검증 (선택적)

**수정 후 코드**:
```python
def _check_unowned_item_usage(self, manuscript: str, context: dict) -> dict:
    """미획득 아이템 사용 체크 (개선: 문맥 고려)"""
    # ... (기존 코드)

    for item in all_items:
        item_name = item.get('name', '')
        if not item_name or item_name in owned_items:
            continue

        if item_name not in manuscript:
            continue

        # 사용 패턴 체크 (개선됨)
        usage_patterns = [
            f"{item_name}을 휘둘",
            f"{item_name}를 휘둘",
            f"{item_name}으로",
            f"{item_name}를 사용",
            f"{item_name}을 사용",
            f"{item_name}를 꺼내",
            f"{item_name}을 꺼내"
        ]

        # 부정문 패턴 (제외)
        negation_patterns = [
            f"{item_name}을 휘두르지",
            f"{item_name}를 사용하지",
            f"{item_name}이 없",
            f"{item_name}가 없"
        ]

        # 관찰 패턴 (제외)
        observation_patterns = [
            f"{item_name}을 보았",
            f"{item_name}를 보았",
            f"{item_name}이 보였",
            f"{item_name}에 대해",
            f"{item_name}를 떠올렸"
        ]

        for pattern in usage_patterns:
            if pattern in manuscript:
                # 부정문인지 체크
                idx = manuscript.find(pattern)
                context_window = manuscript[max(0, idx-30):idx+len(pattern)+30]

                # 부정 키워드 있으면 PASS
                if any(neg in context_window for neg in ['않', '못', '없', '말']):
                    continue

                # 관찰 패턴이면 PASS
                if any(obs in context_window for obs in ['보았', '보였', '떠올렸']):
                    continue

                # 실제 사용으로 판정
                return {
                    "check": "unowned_item_usage",
                    "passed": False,
                    "reason": f"미획득 아이템 '{item_name}' 사용",
                    "severity": "CRITICAL",
                    "owned_items": owned_items,
                    "location": idx,
                    "context": context_window
                }

    return {"check": "unowned_item_usage", "passed": True}
```

---

### ✅ Issue #10: scoring_validator.py - TTR 대신 MTLD 사용

**파일**: `modules/validation/scoring_validator.py`
**라인**: 202-236

**개선: MTLD (Measure of Textual Lexical Diversity) 구현**

```python
def _evaluate_vocabulary_diversity(self, manuscript: str) -> dict:
    """어휘 다양성 평가 (MTLD 사용)"""
    words = self._tokenize(manuscript)

    if len(words) < 50:
        return {'score': 3, 'max': 5, 'reason': '단어 수 부족'}

    # MTLD 계산
    mtld_score = self._calculate_mtld(words)

    # 점수 매기기 (MTLD 기준값 참고)
    if mtld_score >= 80:
        score = 5
        reason = f"MTLD={mtld_score:.1f} (우수)"
    elif mtld_score >= 60:
        score = 4
        reason = f"MTLD={mtld_score:.1f} (양호)"
    elif mtld_score >= 40:
        score = 3
        reason = f"MTLD={mtld_score:.1f} (보통)"
    elif mtld_score >= 20:
        score = 2
        reason = f"MTLD={mtld_score:.1f} (미흡)"
    else:
        score = 1
        reason = f"MTLD={mtld_score:.1f} (부족)"

    # 과다 사용 단어 체크
    word_counts = Counter(words)
    overused = [w for w, c in word_counts.most_common(10) if c > 5]

    if overused:
        reason += f" (과다: {', '.join(overused[:3])})"

    return {'score': score, 'max': 5, 'reason': reason, 'mtld': mtld_score}

def _calculate_mtld(self, words: List[str], threshold: float = 0.72) -> float:
    """
    MTLD (Measure of Textual Lexical Diversity) 계산

    Args:
        words: 단어 리스트
        threshold: TTR 임계값 (기본 0.72)

    Returns:
        MTLD 점수
    """
    if len(words) < 10:
        return 0.0

    # Forward MTLD
    forward_factors = 0
    current_ttr = 0.0
    current_segment = []

    for word in words:
        current_segment.append(word)
        unique = len(set(current_segment))
        total = len(current_segment)
        current_ttr = unique / total

        if current_ttr < threshold:
            forward_factors += 1
            current_segment = []

    # 마지막 불완전 세그먼트 처리
    if current_segment:
        unique = len(set(current_segment))
        total = len(current_segment)
        if total > 0:
            partial_factor = (1 - (unique / total)) / (1 - threshold)
            forward_factors += partial_factor

    # Backward MTLD
    backward_factors = 0
    current_segment = []

    for word in reversed(words):
        current_segment.append(word)
        unique = len(set(current_segment))
        total = len(current_segment)
        current_ttr = unique / total

        if current_ttr < threshold:
            backward_factors += 1
            current_segment = []

    if current_segment:
        unique = len(set(current_segment))
        total = len(current_segment)
        if total > 0:
            partial_factor = (1 - (unique / total)) / (1 - threshold)
            backward_factors += partial_factor

    # 최종 MTLD (forward + backward 평균)
    forward_mtld = len(words) / forward_factors if forward_factors > 0 else 0
    backward_mtld = len(words) / backward_factors if backward_factors > 0 else 0

    mtld = (forward_mtld + backward_mtld) / 2

    return mtld
```

---

### ✅ Issue #11-15: 나머지 High 이슈 간략 가이드

**Issue #11**: 오감 묘사 키워드 개선
- "보" → "보이", "보다", "바라" 등으로 확장
- 형태소 분석기 도입 고려 (`konlpy` 또는 `kiwipiepy`)

**Issue #12**: 클리셰 패턴 구체화
- 연속 3문장 분석으로 문맥 확인
- 예: "눈을 떴다" + "낯선 천장" + "과거로" → 회귀물

**Issue #13**: Semaphore 동적 조정
```python
# Gemini RPM 기반 계산
api_rpm = 1000  # Gemini Pro RPM
safety_margin = 0.8
max_concurrent = int((api_rpm / 60) * safety_margin)  # ~13
```

**Issue #14**: Retry 로직 추가
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def validate_one(ms_data):
    # 기존 코드
```

**Issue #15**: 통계적 유의성 검정
```python
from scipy import stats

t_stat, p_value = stats.ttest_ind(scores_a, scores_b)
if p_value < 0.05:
    comparison['statistically_significant'] = True
```

---

## 🟡 Phase C: Medium 이슈 선별 수정 (Day 8-10)

### 우선 수정할 Medium 이슈 5개

1. **Issue #21**: Self-consistency를 별도 모듈로 분리
2. **Issue #22**: 설정값을 `config/validation_v0128.json`으로 이동
3. **Issue #31**: Dashboard 캐싱 최적화
4. **Issue #44**: 순환 import 해소
5. **Issue #46**: 통일된 로깅 전략

---

## 📝 수정 체크리스트

### Day 1-2: Critical 이슈
- [ ] Issue #1: HUD equipment 타입 체크
- [ ] Issue #2: LLM fallback 개선
- [ ] Issue #3: Constitution 에러 처리
- [ ] Issue #4: Dashboard 무한 루프 제거
- [ ] Issue #5: 파일명 충돌 방지
- [ ] Issue #6: Schema 검증 개선
- [ ] Issue #7: Division by zero 전역 적용
- [ ] Issue #8: Event loop 안전성

### Day 3-5: High 이슈 (1차)
- [ ] Issue #9: 문맥 기반 검증
- [ ] Issue #10: MTLD 도입
- [ ] Issue #11: 오감 키워드 개선
- [ ] Issue #12: 클리셰 패턴 구체화
- [ ] Issue #13: Semaphore 동적 조정

### Day 6-7: High 이슈 (2차)
- [ ] Issue #14: Retry 로직
- [ ] Issue #15: 통계 검정
- [ ] Issue #16: 메모리 최적화
- [ ] Issue #17: 프롬프트 길이 제한
- [ ] Issue #18: Fine-tuning API 통합 (선택적)

### Day 8-10: Medium 이슈 (선별)
- [ ] Issue #21: 모듈 분리
- [ ] Issue #22: 설정 파일 통합
- [ ] Issue #31: 캐싱 최적화
- [ ] Issue #44: Import 정리
- [ ] Issue #46: 로깅 통일

---

## 🧪 테스트 계획

### Unit Tests
```python
# tests/validation/test_blocking_validator.py
def test_equipment_type_handling():
    """HUD equipment의 다양한 타입 처리 테스트"""
    validator = BlockingValidator()

    # List 타입
    context = {'martial_hud': {'actual_truth': {'equipment': ['혼철대도']}}}
    assert validator._check_unowned_item_usage("", context)['passed']

    # String 타입
    context = {'martial_hud': {'actual_truth': {'equipment': '혼철대도'}}}
    assert validator._check_unowned_item_usage("", context)['passed']

    # Dict 타입
    context = {'martial_hud': {'actual_truth': {'equipment': {'혼철대도': True}}}}
    assert validator._check_unowned_item_usage("", context)['passed']

    # 빈 값
    context = {'martial_hud': {'actual_truth': {'equipment': []}}}
    assert validator._check_unowned_item_usage("혼철대도를 휘둘렀다", context)['passed'] == False
```

### Integration Tests
```python
# tests/integration/test_validation_pipeline.py
def test_full_validation_pipeline():
    """전체 검증 파이프라인 통합 테스트"""
    orchestrator = ValidationOrchestrator(config={}, genre='wuxia')

    manuscript = "..."  # 테스트 원고
    context = {...}  # 테스트 컨텍스트

    result = orchestrator.validate(1, manuscript, context)

    assert 'final_decision' in result
    assert result['blocking_result']['passed'] == True
    assert 0 <= result['total_score'] <= 100
```

---

## 📊 성공 지표

### Phase A 완료 기준
- [ ] 모든 Critical 이슈 수정 완료
- [ ] Unit test 통과율 100%
- [ ] 크래시 없이 10개 원고 연속 검증 성공
- [ ] 로그에 ERROR 없음

### Phase B 완료 기준
- [ ] High 이슈 80% 이상 수정
- [ ] MTLD 정확도 검증 (수동 샘플 10개)
- [ ] 문맥 기반 검증 오탐률 < 5%
- [ ] 배치 처리 속도 2배 향상

### Phase C 완료 기준
- [ ] 코드 리뷰 통과
- [ ] 문서 업데이트 (CLAUDE.md)
- [ ] 프로덕션 배포 가능 상태

---

## 🚀 배포 계획

### Stage 1: 내부 테스트 (Day 11-12)
- 개발 환경에서 전체 파이프라인 실행
- 20개 원고로 A/B 테스트 (Legacy vs V0128)

### Stage 2: Canary 배포 (Day 13-15)
- 10% 원고만 V0128로 검증
- 통과율, 정확도 모니터링

### Stage 3: 점진적 확대 (Day 16-20)
- 50% → 100% 전환
- 성능 대시보드 상시 모니터링

---

**작성자**: Claude Sonnet 4.5
**최종 업데이트**: 2026-01-28
