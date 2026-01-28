# HUD 업데이트 수정 검증 가이드

## 🧪 테스트 절차

### 1. 애플리케이션 실행
```bash
python main_a.py
```

### 2. 기존 프로젝트 선택
- 테스트하고 싶은 프로젝트 선택
- 장르 선택 (무협/헌터/투자)

### 3. Stage 4 실행 (새 회차 생성)
- 메뉴에서 "Stage 4: Episode Production" 선택
- 다음 회차 번호 확인

---

## 🔍 확인해야 할 로그 메시지

### ✅ 성공적인 HUD 업데이트 시그널

#### Step 1: 데이터 추출 확인
```
✅ [HUD] actual_truth 데이터 정상 추출 (키 개수: 15)
```
- 키 개수가 10개 이상이면 정상
- 무협: 15개, 헌터: 13개, 투자: 13개 예상

#### Step 2: 데이터 구조 확인
```
🔍 [DEBUG] actual_truth_data 주요 키: ['alias', 'rank', 'realm', 'internal_energy', 'mental_method', ...]
```
- `actual_truth`가 키 목록에 **없어야** 정상
- 만약 `actual_truth`가 있다면 → 여전히 중첩 구조 문제

#### Step 3: HUD 업데이트 확인
```
🔥 [HUD Update] internal_energy: 0.0 -> 5.0
🔥 [HUD Update] realm: 초출 -> 후천초입
🔥 [HUD Update] mental_method: 기본 심법 -> 구양신공
```
- **이 메시지들이 나타나면 수정 성공!**
- 변경사항이 없으면 메시지 없음 (정상)

### ⚠️ 경고 메시지 (문제 징후)

```
⚠️ [HUD] actual_truth 키 없음. raw_updates 전체 사용 (키 개수: N)
```
- Manager가 예상과 다른 JSON 구조 반환
- 레거시 형식으로 작동 중 (동작은 하지만 비표준)

```
🚨 [WARNING] actual_truth가 중첩되어 있음! HUD 업데이트 실패 예상
```
- **여전히 중첩 구조 문제 있음**
- 다음 로그에서 HUD Update 메시지가 없을 것

```
⚠️ [HUD] 리스트 형식 state_updates 감지 (항목 수: N)
```
- Manager가 리스트 형식으로 반환 (비정상)
- 데이터 손실 가능성 있음

### 🚨 오류 메시지 (즉시 보고 필요)

```
🚨 [HUD] state_updates 형식 오류: <class 'str'>
```
- Manager가 완전히 잘못된 형식 반환
- JSON 파싱 자체가 실패했을 가능성

```
🚨 [HUD] 상태 업데이트 실패: [에러 메시지]
```
- update_physical_status() 실행 중 예외 발생
- 에러 메시지 내용을 확인해야 함

---

## 📊 추가 검증 방법

### A. HUD 리포트 확인
회차 생성 과정 중 콘솔에 표시되는 HUD 리포트 확인:

**무협:**
```
[🛡️ V25 SOVEREIGN HUD - 실시간 다층 통합 상태]
─────────── [실제 진실 (Actual Truth)] ───────────
- 성명: 주인공 (별호) | 직위: 평민
- 경지: 후천초입 | 내공: 상당한 내공을 축적 (25년) | 심법: 구양신공
- 상태: 정상 | 자금: 은자 500냥
```
→ **수치가 업데이트되어 있는지 확인**

### B. DB 직접 확인 (고급)
```bash
# SQLite CLI로 확인
sqlite3 projects/[프로젝트명]/project_data.db

# 최신 회차의 HUD 스냅샷 확인
SELECT ep_num, hud_snapshot FROM manuscripts ORDER BY ep_num DESC LIMIT 1;

# Bible의 MartialHUD 확인
SELECT data FROM anchors WHERE key = 'bible';
```

### C. 파일 확인
```
projects/[프로젝트명]/drafts/[회차번호].txt
```
- 파일 상단의 원고가 정상적으로 생성되었는지 확인

---

## 🎯 성공/실패 판정 기준

### ✅ 성공 조건 (모두 충족)
1. ✅ `actual_truth 데이터 정상 추출` 로그 표시
2. ✅ `actual_truth_data 주요 키`에 `actual_truth` **없음**
3. ✅ `🔥 [HUD Update]` 메시지가 **1개 이상** 표시 (변경사항이 있을 경우)
4. ✅ HUD 리포트에서 수치 변경 확인
5. ✅ 에러 메시지 없음

### ❌ 실패 조건 (하나라도 해당)
1. ❌ `🚨 [WARNING] actual_truth가 중첩되어 있음` 표시
2. ❌ `🔥 [HUD Update]` 메시지가 **전혀 없음** (변경사항이 분명히 있는데도)
3. ❌ HUD 리포트 수치가 이전과 동일
4. ❌ `🚨 [HUD] 상태 업데이트 실패` 에러 발생

---

## 📝 테스트 결과 보고 템플릿

테스트 후 다음 정보를 공유해주세요:

```
## 테스트 환경
- 프로젝트명: [이름]
- 장르: [무협/헌터/투자]
- 생성한 회차: [N]화
- 이전 회차: [N-1]화

## 로그 출력
[여기에 관련 로그 복사]

## HUD 리포트
[여기에 HUD 리포트 복사]

## 결과
- [ ] 성공
- [ ] 실패
- [ ] 부분 성공 (설명 추가)

## 추가 관찰사항
[이상한 점이나 예상과 다른 점 기록]
```

---

## 🔧 문제 발생 시 추가 진단

### 만약 여전히 HUD 업데이트가 안 된다면:

1. **Manager 응답 확인**
   - `main_a.py:2663` 근처에 임시 로그 추가:
   ```python
   self.ui.log(f"🔍 [DEBUG] Manager 응답: {json.dumps(audit, ensure_ascii=False, indent=2)[:500]}")
   ```

2. **actual_truth_data 전체 덤프**
   - `main_a.py:2697` 근처에 추가:
   ```python
   self.ui.log(f"🔍 [DEBUG] actual_truth_data 전체: {json.dumps(actual_truth_data, ensure_ascii=False, indent=2)[:500]}")
   ```

3. **update_physical_status 반환값 확인**
   - `main_a.py:2707` 확인:
   ```python
   changes = self.sys.hud.update_physical_status(actual_truth_data)
   self.ui.log(f"🔍 [DEBUG] 변경사항 개수: {len(changes)}")
   ```

---

## 💡 팁

- **첫 회차 생성 시:** HUD 변화가 적을 수 있음 (정상)
- **수련/전투 회차 생성 시:** 내공/경지 변화가 크게 나타남 (이상적)
- **로그가 너무 빠르게 지나가면:** 로그 파일 확인 (`logs/` 디렉토리)
- **콘솔 출력이 꼬이면:** 터미널 재시작 후 다시 실행

**준비가 되었습니다. 애플리케이션을 실행하고 결과를 알려주세요!**
