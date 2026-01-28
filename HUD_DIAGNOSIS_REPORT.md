# HUD 업데이트 문제 진단 보고서

**날짜:** 2026-01-28
**증상:** HUD가 잘 업데이트되지 않는 현상
**심각도:** 🔴 CRITICAL - 데이터 파싱 로직 오류

---

## 1. HUD 업데이트 흐름 분석

### 정상적인 데이터 흐름
```
1. Writer 원고 생성
2. Manager.update_state_and_lore_v20() 호출 (main_a.py:2643)
   └─ 원고 + 현재 상태 → AI 정산 요청 → JSON 반환
3. main_a.py에서 JSON 파싱 (2668-2702)
   └─ state_updates.actual_truth 추출 → actual_truth_data
4. sys.hud.update_physical_status(actual_truth_data) (main_a.py:2707)
   └─ MartialManager/HunterHUD/FinanceHUD 업데이트
5. Bible 저장 및 DB 커밋
```

---

## 2. 🔥 발견된 핵심 문제

### 문제 위치: `main_a.py:2674-2683`

**현재 코드:**
```python
# 4. 🛡️ state_updates 추출 (리스트/딕셔너리 어떤 형식이 와도 대응)
raw_updates = audit.get('state_updates', [])
if isinstance(raw_updates, list):
    for item in raw_updates:
        if isinstance(item, dict):
            t = item.get("target") or item.get('"target"')
            v = item.get("value") or item.get('"value"')
            if t: actual_truth_data[str(t).strip("'\" ")] = v
elif isinstance(raw_updates, dict):
    actual_truth_data = raw_updates  # ❌ 여기가 문제!
```

### Manager가 반환하는 실제 JSON 구조 (manager.py:42-86)
```json
{
  "context_audit": { ... },
  "state_updates": {
    "location": "현재 위치",
    "actual_truth": {          // 👈 진짜 HUD 데이터는 여기!
      "alias": "별호",
      "rank": "직위",
      "realm": "경지",
      "internal_energy": 60.0,
      "mental_method": "심법",
      "reputation": "명성",
      // ... 15개 표준 키
    },
    "public_reputation": { ... },
    "karma_matrix": [ ... ]
  },
  "knowledge_map_updates": { ... },
  "new_lore": { ... }
}
```

### 문제 원인
**`state_updates`는 딕셔너리이므로 `elif isinstance(raw_updates, dict):` 브랜치 실행**

→ `actual_truth_data = raw_updates` 실행
→ `actual_truth_data`에 `location`, `actual_truth`, `public_reputation`, `karma_matrix` 전부 할당됨

**결과:**
- `actual_truth_data`의 구조가 잘못됨
- `actual_truth` 키가 중첩된 딕셔너리로 들어가서 MartialManager가 올바르게 파싱 못함
- `update_physical_status()`가 `actual_truth_data['realm']`을 찾으려 하지만, 실제로는 `actual_truth_data['actual_truth']['realm']`에 있음
- HUD 업데이트 실패

---

## 3. 해결 방법

### Option A: 즉시 수정 (권장)
**파일:** `main_a.py:2682-2683`

**변경 전:**
```python
elif isinstance(raw_updates, dict):
    actual_truth_data = raw_updates
```

**변경 후:**
```python
elif isinstance(raw_updates, dict):
    # actual_truth 키가 있으면 그것을 사용, 없으면 raw_updates 전체 사용
    actual_truth_data = raw_updates.get('actual_truth', raw_updates)
```

### Option B: 더 안전한 수정 (강력 추천)
Manager의 JSON 스키마를 정확히 따르는 방식:

```python
# 4. 🛡️ state_updates 추출
raw_updates = audit.get('state_updates', {})

# [V40.1 Fix] Manager JSON 스키마 준수
if isinstance(raw_updates, dict):
    # 1순위: actual_truth 키 사용 (정상 경로)
    if 'actual_truth' in raw_updates:
        actual_truth_data = raw_updates['actual_truth']
    # 2순위: 전체 딕셔너리 사용 (레거시 대응)
    else:
        actual_truth_data = raw_updates
elif isinstance(raw_updates, list):
    # 리스트 형식 대응 (예외 케이스)
    actual_truth_data = {}
    for item in raw_updates:
        if isinstance(item, dict):
            t = item.get("target") or item.get('"target"')
            v = item.get("value") or item.get('"value"')
            if t: actual_truth_data[str(t).strip("'\" ")] = v
else:
    actual_truth_data = {}
```

---

## 4. 추가 확인 사항

### 4.1 Manager와 main_a.py 간 계약 불일치
- **Manager 프롬프트 (manager.py:42-86):** `state_updates.actual_truth` 구조 명시
- **main_a.py 파싱 로직 (2674-2683):** `state_updates` 전체를 사용
- **결론:** 계약 위반 → 데이터 손실

### 4.2 MartialManager의 canonical_map 로직
`martial_manager.py:178-234`의 `update_physical_status()`는:
```python
actual = pro.setdefault('actual_truth', {})
actual_in = full_state_data.get('actual_truth', full_state_data)

for canonical_key in MARTIAL_METRICS:
    for alt_key in self.canonical_map.get(canonical_key, [canonical_key]):
        if alt_key in actual_in:  # 👈 actual_in에서 직접 키 검색
            val = actual_in[alt_key]
            break
```

**이 로직은 `actual_in`이 평평한(flat) 딕셔너리일 것을 가정함.**
만약 `actual_in`에 `actual_truth` 키가 중첩되어 있으면 검색 실패!

### 4.3 헌터/투자 HUD도 동일 문제
`genre_hud_manager.py`의 `HunterHUDManager.update_physical_status()` (128-157)와 `FinanceHUDManager.update_physical_status()` (238-267)도 동일한 로직 사용:
```python
actual_in = full_state_data.get('actual_truth', full_state_data)
```

따라서 **모든 장르에서 HUD 업데이트 문제 발생 가능.**

---

## 5. 검증 방법

### 5.1 즉시 확인 가능한 로그
main_a.py:2708-2709에서 HUD 변경사항 로깅:
```python
changes = self.sys.hud.update_physical_status(actual_truth_data)
for c in changes:
    self.ui.log(f"🔥 [HUD Update] {c}")
```

**만약 changes가 빈 리스트라면 → HUD 업데이트 실패**

### 5.2 디버깅용 임시 로그 추가
`main_a.py:2683` 다음에 추가:
```python
# [디버깅] actual_truth_data 구조 확인
self.ui.log(f"🔍 [DEBUG] actual_truth_data keys: {list(actual_truth_data.keys())}")
if 'actual_truth' in actual_truth_data:
    self.ui.log(f"⚠️ [WARNING] actual_truth가 중첩되어 있음!")
```

---

## 6. 권장 조치

### 즉시 조치 (Priority 1)
1. ✅ **main_a.py:2682-2683 수정** (위 Option B 적용)
2. ✅ **디버깅 로그 추가** (5.2 참고)
3. ✅ **테스트 회차 생성** 후 HUD 변경사항 확인

### 중기 조치 (Priority 2)
1. Manager 응답 스키마 검증 로직 추가
2. actual_truth_data 구조 검증 유닛 테스트 작성
3. HUD 업데이트 실패 시 명확한 에러 메시지 출력

### 장기 조치 (Priority 3)
1. Manager와 main_a.py 간 데이터 계약 문서화
2. JSON 스키마 검증 라이브러리 도입 (jsonschema)
3. HUD 업데이트 실패 시 자동 복구 메커니즘 구현

---

## 7. 연결 상태 점검 결과

### ✅ Manager.py → main_a.py 연결 상태
- **에이전트 초기화:** `main_a.py:485` ✅ 정상
- **호출 인터페이스:** `main_a.py:2643` ✅ 정상
- **예외 처리:** `main_a.py:2651-2657` ✅ 정상

### ❌ main_a.py → HUD Manager 데이터 전달
- **데이터 파싱:** `main_a.py:2674-2683` ❌ **버그 발견**
- **HUD 업데이트 호출:** `main_a.py:2707` ✅ 정상
- **변경사항 로깅:** `main_a.py:2708-2709` ✅ 정상

### ✅ HUD Manager 내부 로직
- **MartialManager:** `martial_manager.py:178-234` ✅ 정상
- **HunterHUDManager:** `genre_hud_manager.py:128-157` ✅ 정상
- **FinanceHUDManager:** `genre_hud_manager.py:238-267` ✅ 정상
- **Bible 저장:** 모두 `context.save_v20_anchor()` 호출 ✅ 정상

---

## 8. 결론

**HUD가 업데이트되지 않는 근본 원인:**
- `main_a.py:2682-2683`에서 `state_updates` 딕셔너리를 그대로 할당
- Manager가 반환한 `state_updates.actual_truth`를 추출하지 않음
- 중첩된 딕셔너리가 HUD Manager로 전달됨
- HUD Manager가 평평한 구조를 기대하므로 키 검색 실패
- 결과적으로 HUD 수치 변경 없음 (changes = [])

**수정 후 예상 효과:**
- ✅ actual_truth 데이터 정확히 추출
- ✅ HUD 수치 정상 업데이트
- ✅ Bible에 변경사항 저장
- ✅ 로그에 "🔥 [HUD Update] realm: 초출 -> 후천" 등 표시

**추가 점검 필요:**
- Manager AI가 실제로 올바른 JSON을 반환하는지 확인
- `internal_energy` 등 수치형 데이터가 문자열("60갑자")로 오는 경우 guard 변환 동작 확인
