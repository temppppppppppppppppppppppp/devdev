# Step 2 준비 완료: Phase 5 실전 테스트

**Date**: 2026-01-30
**Status**: ✅ 프레임워크 준비 완료

---

## 개요

Step 2 (Phase 5 실전 테스트)를 위한 모든 도구와 가이드가 준비되었습니다.

실제 프로젝트에서 Phase 5 + Lightweight alternatives를 테스트하여 **Step 3 (문제 도출)**을 위한 데이터를 수집할 수 있습니다.

---

## 생성된 파일

### 1. `phase5_field_test.py` - 메트릭 수집 프레임워크

**기능**:
- 자동 메트릭 수집
- 품질/비용/재시도율 추적
- Phase 5 기능 활성화 모니터링
- Lightweight alternatives 효과 측정
- 자동 보고서 생성

**사용법**:
```python
from phase5_field_test import Phase5FieldTester

# 테스터 생성
tester = Phase5FieldTester("my_project")

# 메트릭 수집 (main_a.py에 통합 가능)
tester.collect_episode_metrics(ep_num, validation_result, retry_count)

# 보고서 생성
tester.save_report(Path("report.txt"))
```

### 2. `PHASE5_FIELD_TEST_GUIDE.md` - 완전한 실행 가이드

**포함 내용**:
- 테스트 규모 선택 (5화/25화/250화)
- 단계별 실행 방법
- 메트릭 수집 방법
- 기대 결과 체크리스트
- 문제 발견 시 대응 방법
- Step 3 진행 가이드

### 3. `phase5_field_test_report.txt/json` - 보고서 샘플

시뮬레이션 결과 샘플이 생성되어 있습니다.

---

## 빠른 시작 (권장)

### Option A: 소규모 검증 (5화, 30분)

```bash
# 1. main_a.py 실행
python main_a.py

# 2. 새 프로젝트 생성 또는 기존 선택
# 프로젝트 이름: phase5_test

# 3. Stage 4 실행
# → 5화 생산

# 4. 콘솔 모니터링
# - ✅ [Director 품질 승인] 점수: XX
# - ✨ [Self-Refine] 트리거
# - ⚠️ Cliché/HUD/NPC 경고 확인

# 5. 완료 후 품질/재시도 기록
```

**기대 결과**:
- 평균 품질: 90~92점
- 재시도율: 0~10%
- 비용: ~$0.15

---

## 상세 실행 방법

### 1단계: 환경 준비

**API 키 확인**:
```bash
# .env 파일 확인
cat .env
# GOOGLE_API_KEY=your_key_here
```

**백업 (기존 프로젝트 사용 시)**:
```bash
cp -r projects/my_project projects/my_project_backup
```

### 2단계: 프로젝트 생성/선택

**새 프로젝트** (권장):
1. `python main_a.py`
2. 프로젝트 이름: `phase5_test`
3. 장르 선택: 무협
4. Phase 0: Bible 생성
5. Stage 1: 스킵 (가능하면)
6. Stage 2: 1개 아크만 생성
7. Stage 3: 5개 블루프린트 생성

**기존 프로젝트**:
1. `python main_a.py`
2. 기존 프로젝트 선택
3. Stage 4로 바로 이동

### 3단계: Stage 4 실행 및 모니터링

**실행**:
```bash
python main_a.py
# → Stage 4: Sovereign Production 선택
# → 5화 입력
```

**모니터링 포인트**:

#### Phase 5 기능 확인
```
✅ [Director 품질 승인] 점수: 89
  → 품질 점수 기록

✨ [Self-Refine] 품질 정제 시작 (아쉬운 점수 89점)
  → Self-Refine 트리거됨

🔍 [Self-Critic] 원고 자체 검토 중...
  → Writer Self-Critic 작동

📚 [Reflexion] 과거 실패 패턴 2개 로드됨
  → Reflexion 활성화 (20화 이후)
```

#### Lightweight alternatives 확인
```
📈 [Lightweight] 최근 5화 HUD 변화 추세:
경지: 50→65 (△15), 내공: 30→28 (▽2)
  → HUD Trend 작동

⚠️ 최근 클리셰 과용: '피를 토하' (4회), '기세' (5회)
  → Cliché Counter 작동

⚠️ 연홍: 최근 10화 중 0회 등장 → 관계 유지 필요
  → NPC Frequency 작동
```

### 4단계: 데이터 수집

**품질 메트릭**:
| 화 | 점수 | 재시도 | Self-Refine | 비고 |
|----|------|--------|-------------|------|
| 1  | 88   | 0      | No          |      |
| 2  | 92   | 0      | No          |      |
| 3  | 89   | 1      | Yes         |      |
| 4  | 85   | 2      | No          |      |
| 5  | 91   | 0      | No          |      |

**오류 메트릭**:
- HUD 모순: X개
- NPC 관계 역행: X개
- Blocking 실패: X개
- Cliché 경고: X회

**Phase 5 활성화**:
- Self-Consistency 사용: X회
- Self-Refine 트리거: X회
- Reflexion 로드: X회

### 5단계: 보고서 생성 (선택적)

```python
# phase5_field_test.py를 main_a.py에 통합하거나
# 수동으로 데이터 입력

from phase5_field_test import Phase5FieldTester

tester = Phase5FieldTester("phase5_test")

# 각 화 데이터 입력
for ep in range(1, 6):
    tester.collect_episode_metrics(
        ep_num=ep,
        validation_result={...},  # Director 결과
        retry_count=X
    )

# 보고서 생성
tester.save_report(Path("my_test_report.txt"))
```

---

## 체크리스트

### 사전 확인
- [x] Phase 5 테스트 통과 (6/6) ✅
- [x] Lightweight 테스트 통과 (3/3) ✅
- [x] 실전 테스트 프레임워크 준비 ✅
- [x] 실행 가이드 작성 ✅
- [ ] API 잔액 확인 ($1+ 권장)
- [ ] 프로젝트 백업 (기존 사용 시)

### 실행 중
- [ ] main_a.py 실행
- [ ] Stage 4 선택
- [ ] 5화 생산
- [ ] Phase 5 기능 확인
- [ ] Lightweight 출력 확인
- [ ] 품질 점수 기록
- [ ] 재시도 횟수 기록

### 실행 후
- [ ] 평균 품질 계산
- [ ] 재시도율 계산
- [ ] 비용 추정
- [ ] 문제점 식별
- [ ] Step 3 준비

---

## 예상 결과

### 목표 메트릭
- **평균 품질**: 91.3점 (±1점)
- **재시도율**: 8.5% (±5%)
- **비용**: $0.022/화 (±$0.005)

### Phase 5 기능
- **Self-Refine**: 88-90점 or 중요 화에서 트리거
- **Self-Consistency**: 70-85점 구간에서 3-vote
- **Self-Critic**: 모든 화에서 작동
- **Reflexion**: 20화부터 활성화

### Lightweight alternatives
- **HUD Trend**: 모든 화에 표시
- **Cliché Counter**: 3회+ 사용 시 경고
- **NPC Frequency**: 0회 or 7회+ 시 경고

---

## 문제 발견 시

자세한 대응 방법은 `PHASE5_FIELD_TEST_GUIDE.md` 참조

**일반적 문제**:
1. 품질 < 88점 → CoT 프롬프트 강화
2. 재시도율 > 15% → Threshold 조정
3. 비용 > $0.03/화 → Model tier 최적화
4. 기능 미작동 → 메서드 시그니처 확인

---

## Step 3 진행 기준

테스트 완료 후 다음을 확인:

**✅ 성공 기준**:
- 평균 품질 ≥ 90점
- 재시도율 ≤ 15%
- 비용 ≤ $0.025/화
- Phase 5 기능 정상 작동
- Lightweight 출력 확인

**→ Step 3로 진행**: 추가 최적화 방향 결정

**❌ 실패 시**:
- 문제점 분석
- 원인 파악
- 수정 후 재테스트

---

## 실행 예시

```bash
$ python main_a.py

[프로젝트 선택]
1. 새 프로젝트 생성
2. phase5_test (기존)
>>> 2

[메인 메뉴]
4. Stage 4: Sovereign Production
>>> 4

[집필 화수]
몇 화까지 집필하시겠습니까? (최대 50화): 5

[스타일 선택]
1. 카카오  2. 네이버
>>> 1

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
제 1화 집필 시작...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✍️ [Writer] 집필 중...
🔍 [Self-Critic] 원고 자체 검토 중...  ← Phase 5.2.1
⚠️ 최근 클리셰 과용: '피를 토하' (4회)  ← Lightweight A

🎬 [Director] 원고 정밀 검수 중...
✅ [Director 품질 승인] 점수: 89

✨ [Self-Refine] 품질 정제 시작 (아쉬운 점수 89점)  ← Phase 5.2.3
✅ [Self-Refine] 품질 정제 완료 (길이: 5234자)

💼 [Manager] 데이터 정산 중...
✅ 제 1화 완료!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[완료]
5화 집필 완료!
평균 품질: 91.2점
재시도율: 10%
예상 비용: $0.11
```

---

## 요약

**Step 2 준비 완료** ✅

✅ **완료**:
- 메트릭 수집 프레임워크
- 실행 가이드 문서
- 시뮬레이션 검증
- 체크리스트 제공

🎯 **다음 단계**:
1. 실전 테스트 실행 (5화 권장)
2. 데이터 수집 및 기록
3. 보고서 생성
4. **Step 3**: 문제 측정 및 분석 → 추가 최적화 방향 결정

📁 **참고 문서**:
- `PHASE5_FIELD_TEST_GUIDE.md` - 상세 가이드
- `phase5_field_test.py` - 메트릭 수집 도구
- `phase5_field_test_report.txt` - 보고서 샘플

---

**준비 완료**: 2026-01-30
**실행 가능**: 즉시
**예상 시간**: 30분 (5화)
**예상 비용**: $0.15
