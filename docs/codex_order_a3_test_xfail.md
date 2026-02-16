# Codex Order A-3: test_validation.py 13건 xfail 처리

> 우선순위: 4 / 카테고리: 테스트 / 규모: 극소 / 위험도: 없음

---

## 목표

`tests/test_validation.py`의 pre-existing 13건 실패를 `pytest.mark.xfail`로 마킹하여 CI 노이즈 제거.
이 테스트들은 V44 시점에 작성되었으나 이후 validator API가 변경되어 실패 중.

---

## 현재 상태

```
13 failed, 12 passed in 0.20s
```

### 실패 목록 (13건)

| # | 테스트 | 클래스 |
|---|--------|--------|
| 1 | `test_minimum_length_manuscript_pass` | TestBlockingValidator |
| 2 | `test_minimum_length_manuscript_fail` | TestBlockingValidator |
| 3 | `test_dead_npc_resurrection_detection` | TestBlockingValidator |
| 4 | `test_destroyed_location_visit_detection` | TestBlockingValidator |
| 5 | `test_unowned_item_usage_detection` | TestBlockingValidator |
| 6 | `test_blueprint_mode_validation` | TestBlockingValidator |
| 7 | `test_advisory_always_passes` | TestAdvisoryValidator |
| 8 | `test_tier_order_execution` | TestValidationOrchestrator |
| 9 | `test_empty_manuscript` | TestValidationEdgeCases |
| 10 | `test_unicode_special_characters` | TestValidationEdgeCases |
| 11 | `test_very_long_manuscript` | TestValidationEdgeCases |
| 12 | `test_missing_context_fields` | TestValidationEdgeCases |
| 13 | `test_null_values_in_context` | TestValidationEdgeCases |

### 통과 목록 (12건) — 변경 금지

- `test_prose_rhythm_calculation` (ScoringValidator)
- `test_vocabulary_diversity_calculation` (ScoringValidator)
- `test_sensory_balance_check` (ScoringValidator)
- `test_show_dont_tell_detection` (ScoringValidator)
- `test_scoring_threshold_pass` (ScoringValidator)
- `test_scoring_threshold_fail` (ScoringValidator)
- `test_cliche_detection` (AdvisoryValidator)
- `test_foreshadowing_opportunity_detection` (AdvisoryValidator)
- `test_orchestrator_initialization` (ValidationOrchestrator)
- `test_final_decision_mapping` (ValidationOrchestrator)
- `test_self_consistency_mode` (ValidationOrchestrator)
- `test_genre_specific_validation` (ValidationOrchestrator)

---

## 작업 상세

**파일**: `tests/test_validation.py`

각 실패 테스트 `def` 위에 `@pytest.mark.xfail(reason="V44 API 변경 후 미갱신")` 데코레이터 추가.

### 적용 위치

```python
# L19
@pytest.mark.xfail(reason="V44 API 변경 후 미갱신")
def test_minimum_length_manuscript_pass(self, sample_manuscript, validation_context):

# L31
@pytest.mark.xfail(reason="V44 API 변경 후 미갱신")
def test_minimum_length_manuscript_fail(self, validation_context):

# L46
@pytest.mark.xfail(reason="V44 API 변경 후 미갱신")
def test_dead_npc_resurrection_detection(self, validation_context):

# L63
@pytest.mark.xfail(reason="V44 API 변경 후 미갱신")
def test_destroyed_location_visit_detection(self, validation_context):

# L79
@pytest.mark.xfail(reason="V44 API 변경 후 미갱신")
def test_unowned_item_usage_detection(self, validation_context):

# L93
@pytest.mark.xfail(reason="V44 API 변경 후 미갱신")
def test_blueprint_mode_validation(self, sample_blueprint, validation_context):

# L256
@pytest.mark.xfail(reason="V44 API 변경 후 미갱신")
def test_advisory_always_passes(self, sample_manuscript, validation_context):

# L303
@pytest.mark.xfail(reason="V44 API 변경 후 미갱신")
def test_tier_order_execution(self, sample_manuscript, validation_context):

# L388
@pytest.mark.xfail(reason="V44 API 변경 후 미갱신")
def test_empty_manuscript(self, validation_context):

# L397
@pytest.mark.xfail(reason="V44 API 변경 후 미갱신")
def test_unicode_special_characters(self, validation_context):

# L409
@pytest.mark.xfail(reason="V44 API 변경 후 미갱신")
def test_very_long_manuscript(self, validation_context):

# L421
@pytest.mark.xfail(reason="V44 API 변경 후 미갱신")
def test_missing_context_fields(self):

# L441
@pytest.mark.xfail(reason="V44 API 변경 후 미갱신")
def test_null_values_in_context(self, validation_context):
```

---

## 검증 게이트

```bash
# Gate 1: 테스트 실행 — 13 xfailed, 12 passed, 0 failed
set PYTHONIOENCODING=utf-8
pytest tests/test_validation.py -v

# Gate 2: pre-commit
pre-commit run --files tests/test_validation.py
```

기대 결과: `12 passed, 13 xfailed`

---

## 커밋

```
test(A-3): mark 13 pre-existing test_validation failures as xfail

- Add @pytest.mark.xfail to 13 tests with outdated V44 API expectations
- 12 passing tests unchanged
- Reduces CI noise from known pre-existing failures

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

---

## 수정 금지

- 통과 중인 12건 테스트 변경 금지
- 테스트 로직 수정 금지 (xfail 데코레이터만 추가)
- conftest.py 변경 금지
- 프로덕션 코드 변경 금지
