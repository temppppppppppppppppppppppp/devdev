# Bug Report: Step 1 & 4 통합 후 디버깅

**Date**: 2026-01-30
**Scope**: main_a.py 및 연결된 에이전트 시스템 점검
**Status**: ✅ 디버깅 완료

---

## 요약

Step 1 (Self-Refine 통합) + Step 4 (Lightweight Alternatives 구현) 이후 전체 시스템 코드 재점검을 수행하여 **2개의 버그를 발견하고 수정**했습니다.

---

## 발견된 버그

### 🔴 Bug #1: Self-Refine JSON 타입 불일치 (CRITICAL)

**위치**: `main_a.py` lines 3108-3152

**문제**:
1. `Writer._self_refine()` 메서드는 JSON 문자열을 입력으로 기대하지만, 평문 텍스트 `temp_content`를 전달하고 있었음
2. `_self_refine()`은 JSON 문자열을 반환하지만, 코드에서 평문 텍스트로 처리하고 있었음

**영향**:
- Self-Refine 기능이 트리거되면 TypeError 발생 또는 부정확한 결과 생성
- Phase 5.2.3 기능이 실질적으로 작동하지 않음

**수정 내용**:
```python
# Before (버그):
refined_json = self.agents['writer']._self_refine(
    manuscript=temp_content,  # ❌ 평문 전달
    ...
)
temp_content = refined_json  # ❌ JSON을 평문으로 취급

# After (수정):
# 1. JSON 빌드
manuscript_json = json.dumps({
    'title': temp_title,
    'content': temp_content,
    'state_updates': writer_state_updates
}, ensure_ascii=False)

# 2. Self-Refine 호출
refined_json = self.agents['writer']._self_refine(
    manuscript=manuscript_json,  # ✅ JSON 전달
    target_areas=['emotion', 'prose', 'cliffhanger', 'sensory']
)

# 3. JSON 파싱
refined_data = self.agents['writer']._extract_json_robust(refined_json)
if refined_data and isinstance(refined_data, dict):
    refined_content = refined_data.get('content', '')
    if refined_content and len(refined_content) > len(temp_content) * 0.8:
        temp_content = refined_content  # ✅ 파싱된 content 사용
        if refined_data.get('title'):
            temp_title = refined_data['title']
```

**검증 결과**: ✅ 수정 완료

---

### 🟡 Bug #2: Self-Refine 메서드 시그니처 불일치 (HIGH)

**위치**: `main_a.py` line 3124

**문제**:
Bug #1 수정 과정에서 `_self_refine()` 호출 시 존재하지 않는 `ep_num` 파라미터를 전달함

**메서드 시그니처**:
```python
# modules/domain/agents/writer.py:991
def _self_refine(self, manuscript: str, target_areas: list = None) -> str:
    # ep_num 파라미터 없음!
```

**호출 코드 (버그)**:
```python
refined_json = self.agents['writer']._self_refine(
    manuscript=manuscript_json,
    ep_num=next_ep,  # ❌ 존재하지 않는 파라미터
    target_areas=['emotion', 'prose', 'cliffhanger', 'sensory']
)
```

**영향**:
- Self-Refine 호출 시 TypeError 발생
- `TypeError: _self_refine() got an unexpected keyword argument 'ep_num'`

**수정 내용**:
```python
# After (수정):
refined_json = self.agents['writer']._self_refine(
    manuscript=manuscript_json,
    target_areas=['emotion', 'prose', 'cliffhanger', 'sensory']
)  # ✅ ep_num 파라미터 제거
```

**검증 결과**: ✅ 수정 완료

---

## 검증 완료 항목

### ✅ Writer Agent 통합
- `_count_recent_cliches()`: ✅ 구현 확인
- `_check_cliche_overuse(ep_num)`: ✅ 파라미터 전파 확인
- `_get_npc_frequency(ep_num)`: ✅ 구현 확인
- `_get_npc_frequency_warning(ep_num)`: ✅ 호출 확인
- `_get_hud_trend_safe(ep_num)`: ✅ 구현 및 호출 확인
- `write_v20_manuscript()`: ✅ 프롬프트 주입 확인 (lines 181, 191)
- `_self_critique()`: ✅ ep_num 파라미터 전파 확인
- `_apply_self_critique()`: ✅ ep_num 파라미터 전파 확인
- `_fallback_full_request()`: ✅ ep_num 파라미터 전파 확인

### ✅ Architect Agent 통합
- `_get_hud_trend_safe(ep_num)`: ✅ 구현 확인 (lines 17-35)
  - 예외 처리: ✅ try-except 구조
  - 폴백 경로: ✅ context.sys.hud → martial → 기본 메시지
- `design_v20_breakdown(ep_num, ...)`: ✅ 파라미터 확인
- 프롬프트 주입 (line 204): ✅ `_get_hud_trend_safe(ep_num)` 호출 확인

### ✅ MartialManager 통합
- `get_hud_trend(ep_num, window=5)`: ✅ 구현 확인 (lines 374-439)
  - 엣지 케이스 처리:
    - ep_num=1 (첫 화): ✅ "안정적 (변화 없음)" 반환
    - 누락된 원고: ✅ try-except로 안전하게 스킵
    - 잘못된 HUD 스냅샷: ✅ isinstance() 타입 체크
    - 숫자가 아닌 값: ✅ 예외 처리 + regex 추출 폴백
  - 타입 안전성: ✅ 우수 (dict/int/float/str 검증)

### ✅ ValidationOrchestrator 통합
- `refine_recommended` 플래그 설정: ✅ 조건 확인 (lines 185-207)
  - 조건 1: 88-90점 (아쉬운 점수) ✅
  - 조건 2: 중요 화 (1, 25, 50, 75, ...) ✅
- `refine_reason` 메시지: ✅ 올바르게 설정됨

### ✅ 파라미터 전파 체인
모든 ep_num 파라미터가 올바르게 전파됨:

```
1. write_v20_manuscript(ep_num, ...)
   → _get_npc_frequency_warning(ep_num) ✅
   → _get_hud_trend_safe(ep_num) ✅

2. _fallback_full_request(..., ep_num)
   → _apply_self_critique(..., ep_num) ✅

3. _apply_self_critique(..., ep_num)
   → _self_critique(..., ep_num) ✅

4. _self_critique(..., ep_num)
   → _check_cliche_overuse(..., ep_num) ✅

5. design_v20_breakdown(ep_num, ...)
   → _get_hud_trend_safe(ep_num) ✅
```

---

## 테스트 상태

### Phase 5 테스트: ✅ 6/6 통과
```
✅ PASS          Phase 5.1.1 (Architect CoT)
✅ PASS          Phase 5.1.2 (Conditional SC)
✅ PASS          Phase 5.1.3 (Contrastive CoT)
✅ PASS          Phase 5.2.1 (Writer Self-Critic)
✅ PASS          Phase 5.2.2 (Reflexion)
✅ PASS          Phase 5.2.3 (Self-Refine)
```

### Lightweight Alternatives 테스트: ✅ 3/3 통과
```
✅ PASS          Cliché Counter
✅ PASS          HUD Trend Injection
✅ PASS          NPC Frequency Warning
```

---

## 수정된 파일

| 파일 | 변경 사항 | 라인 수 |
|------|----------|--------|
| `main_a.py` | Self-Refine 호출 버그 2개 수정 | ~35 lines |

---

## 결론

**✅ 디버깅 완료 및 프로덕션 준비 완료**

1. ✅ **2개의 버그 발견 및 수정**
   - Bug #1: Self-Refine JSON 타입 불일치 (Critical)
   - Bug #2: 메서드 시그니처 불일치 (High)

2. ✅ **전체 시스템 검증 완료**
   - Writer Agent: ✅ 통합 확인
   - Architect Agent: ✅ 통합 확인
   - MartialManager: ✅ 엣지 케이스 검증
   - ValidationOrchestrator: ✅ 플래그 설정 확인
   - 파라미터 전파: ✅ 전체 체인 검증

3. ✅ **모든 테스트 통과**
   - Phase 5: 6/6
   - Lightweight: 3/3

**추천**: 즉시 프로덕션 배포 가능. Step 2 (실전 테스트)로 진행하여 실제 효과 측정.

---

**문서 생성**: 2026-01-30
**작성자**: Claude Code
**검증 상태**: ✅ 완료
