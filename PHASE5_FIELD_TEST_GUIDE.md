# Phase 5 실전 테스트 가이드

**목적**: Phase 5 + Lightweight alternatives의 실제 효과를 측정하여 Step 3 (문제 도출) 진행

---

## 테스트 개요

### 목표
- Phase 5 기능들이 실제로 작동하는지 확인
- 품질/비용/재시도율 실측
- 예상 효과와 실제 효과 비교
- 개선이 필요한 부분 식별 (Step 3)

### 테스트 규모
**Option A: 소규모 검증 (권장)**
- 화수: 5화
- 시간: ~30분
- 비용: ~$0.15
- 목적: 시스템 정상 작동 확인

**Option B: 중규모 검증**
- 화수: 25화 (1 아크)
- 시간: ~2시간
- 비용: ~$0.75
- 목적: 통계적 유의성 확보

**Option C: 전체 프로젝트**
- 화수: 250화
- 시간: ~20시간 (분산 가능)
- 비용: ~$5.5
- 목적: 최종 프로덕션 검증

---

## 실행 방법

### 1. 새 프로젝트 생성 (권장)

```bash
python main_a.py
```

1. 프로젝트 이름: `phase5_test_250화무협`
2. 장르 선택: 무협 (또는 원하는 장르)
3. Phase 0: Bible 생성
4. Stage 1: Volume Strategy (스킵 가능하면 스킵)
5. Stage 2: Arc Tactical Design (1개 아크만)
6. Stage 3: Episode Blueprinting (5화 또는 원하는 화수)
7. **Stage 4: Sovereign Production** ← 여기서 테스트

### 2. 기존 프로젝트 사용

기존 프로젝트가 있다면:
1. `python main_a.py`
2. 기존 프로젝트 선택
3. **Stage 4: Sovereign Production** 바로 실행
4. 5화 생산 후 중단 (Ctrl+C)

---

## 메트릭 수집 방법

### 자동 수집 (main_a.py 내장)

main_a.py는 이미 audit 시스템이 내장되어 있습니다:
- `runtime_audit[]`: 모든 이벤트 기록
- `_audit_event()`: 이벤트 로깅

확인 방법:
```python
# main_a.py 실행 후
# self.runtime_audit 배열에서 다음 이벤트 찾기:
# - "self_refine_success": Self-Refine 실행
# - "pattern_warning": 패턴 부족
# - "character_logic_reject": 캐릭터 논리 거부
```

### 수동 수집

Stage 4 실행 중 콘솔 출력에서 확인:
- `✅ [Director 품질 승인] 점수: XX` → 품질 점수
- `✨ [Self-Refine] 품질 정제 시작` → Self-Refine 트리거
- `⚠️ 최근 클리셰 과용: ...` → Cliché Counter 작동
- `📈 [Lightweight] 최근 5화 HUD 변화 추세` → HUD Trend 작동
- `👥 [Lightweight] 주요 NPC 등장 빈도` → NPC Frequency 작동

### 로그 파일 분석

```bash
# logs 폴더 확인
ls logs/

# 최근 로그 보기
tail -f logs/latest.log
```

---

## 기대 결과 체크리스트

### Phase 5.1 (무료 최적화)

**✅ Architect CoT**
- [ ] Blueprint 생성 시 5단계 구조 확인
- [ ] 로그에 `[STEP 1]`, `[STEP 2]` 등 출력

**✅ Conditional Self-Consistency**
- [ ] 70-85점 구간에서 3-vote 실행
- [ ] 로그에 `Self-Consistency 사용` 출력

**✅ Contrastive CoT**
- [ ] Justification 가이드에 ❌/✅ 대조 예시
- [ ] Writer 프롬프트에 wrong_approach/correct_approach

### Phase 5.2 (고급 최적화)

**✅ Writer Self-Critic**
- [ ] 원고 작성 후 자동 검토
- [ ] 로그에 `🔍 [Self-Critic] 원고 자체 검토 중` 출력
- [ ] 문제 발견 시 자동 수정 시도

**✅ Reflexion (20화 이후)**
- [ ] 20화부터 활성화
- [ ] 과거 실패 패턴 학습
- [ ] 로그에 `📚 [Reflexion] 과거 실패 패턴 X개 로드됨`

**✅ Conditional Self-Refine**
- [ ] 88-90점 or 중요 화에서 트리거
- [ ] 로그에 `✨ [Self-Refine] 품질 정제 시작` 출력

### Lightweight Alternatives

**✅ Cliché Counter**
- [ ] Writer 프롬프트에 최근 클리셰 빈도
- [ ] 3회 이상 사용 시 경고 메시지

**✅ HUD Trend**
- [ ] Writer/Architect 프롬프트에 HUD 추세
- [ ] 예시: `경지: 50→65 (△15)`

**✅ NPC Frequency**
- [ ] Writer 프롬프트에 NPC 등장 빈도
- [ ] 0회 or 7회+ 시 경고 메시지

---

## 결과 분석

### 데이터 수집 항목

생산 완료 후 다음 데이터를 기록하세요:

**1. 품질 메트릭**
```
에피소드 | 점수 | 재시도 | Self-Refine | 비고
1        | 88   | 0      | No          |
2        | 92   | 0      | No          |
3        | 89   | 1      | Yes         | 88점→89점 정제
4        | 85   | 2      | No          |
5        | 91   | 0      | No          |
--------------------------------------------------
평균     | 89.0 | 0.6    | 20%         |
```

**2. 오류 메트릭**
- HUD 모순: X개
- NPC 관계 역행: X개
- Blocking 실패: X개

**3. Phase 5 활성화**
- Self-Consistency 사용: X회
- Self-Refine 트리거: X회
- Reflexion 로드: X회 (20화 이후)

**4. Lightweight 효과**
- Cliché 경고: X회
- HUD Trend 표시: 모든 화
- NPC Frequency 경고: X회

### 자동 분석 도구 사용

```bash
python phase5_field_test.py
```

이 스크립트는:
1. 메트릭 수집 프레임워크 제공
2. 자동 보고서 생성
3. 예상 vs 실제 비교

---

## 문제 발견 시 대응

### Case 1: 품질이 예상보다 낮음 (< 88점)

**원인 가능성**:
- Architect CoT가 제대로 작동 안함
- Writer Self-Critic 스킵됨
- 장르별 가이드 부족

**확인 방법**:
```python
# Writer 프롬프트에 CoT 구조 있는지 확인
# Self-Critic 로그 확인
```

**해결책**:
- CoT 프롬프트 강화
- Self-Critic threshold 낮추기

### Case 2: 재시도율이 높음 (> 15%)

**원인 가능성**:
- Blocking validator가 너무 엄격
- Scoring threshold가 높음 (70점)
- Writer가 요구사항 이해 못함

**확인 방법**:
```python
# Blocking 실패 원인 로그 확인
# Scoring 결과 상세 분석
```

**해결책**:
- Blocking 조건 완화
- Scoring threshold 조정 (70 → 65)
- Writer 프롬프트 개선

### Case 3: 비용이 예상보다 높음 (> $0.025/화)

**원인 가능성**:
- Self-Consistency가 너무 자주 사용됨
- 재시도가 많음
- Model tier가 높음

**확인 방법**:
```python
# Self-Consistency 사용 빈도 확인
# Retry count 분석
```

**해결책**:
- Conditional SC threshold 조정 (70-85 → 75-80)
- Retry limit 감소
- Tier 1 모델 더 오래 사용

### Case 4: Lightweight 기능이 작동 안함

**확인 방법**:
```bash
# 프롬프트에 실제로 주입되는지 확인
grep -r "Lightweight" logs/

# 메서드 호출 확인
python test_lightweight_alternatives.py
```

**해결책**:
- 메서드 시그니처 확인 (ep_num 전달되는지)
- context.sys.hud 객체 존재 확인
- 에러 로그 확인

---

## 실전 테스트 체크리스트

### 사전 준비
- [ ] Phase 5 테스트 통과 (6/6)
- [ ] Lightweight 테스트 통과 (3/3)
- [ ] 프로젝트 백업 (기존 프로젝트 사용 시)
- [ ] API 키 잔액 확인 ($1+ 권장)

### 테스트 실행
- [ ] main_a.py 실행
- [ ] Stage 4 선택
- [ ] 5화 생산
- [ ] 콘솔 출력 모니터링
- [ ] 로그 파일 확인

### 데이터 수집
- [ ] 품질 점수 기록
- [ ] 재시도 횟수 기록
- [ ] Phase 5 기능 활성화 확인
- [ ] Lightweight 출력 확인
- [ ] 오류 메시지 기록

### 결과 분석
- [ ] phase5_field_test.py 실행
- [ ] 보고서 생성
- [ ] 예상 vs 실제 비교
- [ ] 문제점 식별 (Step 3)

---

## Step 3으로 진행

테스트 완료 후 다음 질문에 답하세요:

1. **품질이 예상대로인가?** (목표: 91.3점)
   - Yes → ✅ 성공
   - No → 원인 분석 필요

2. **재시도율이 예상대로인가?** (목표: 8.5%)
   - Yes → ✅ 성공
   - No → Blocking/Scoring 조정 필요

3. **비용이 예상대로인가?** (목표: $0.022/화)
   - Yes → ✅ 성공
   - No → Model tier 또는 SC 조정 필요

4. **어떤 문제가 여전히 발생하는가?**
   - HUD 모순
   - NPC 관계 역행
   - 클리셰 과용
   - 기타

이 답변들이 **Step 3: 문제 측정 및 분석**의 기초 데이터가 됩니다.

---

## 빠른 시작 (TL;DR)

```bash
# 1. 테스트 실행
python main_a.py
# → Stage 4 선택 → 5화 생산

# 2. 로그 확인
tail -f logs/latest.log

# 3. 콘솔에서 확인
# - ✅ [Director 품질 승인] 점수
# - ✨ [Self-Refine] 트리거
# - ⚠️ Cliché/NPC 경고

# 4. 보고서 생성
python phase5_field_test.py

# 5. 결과 분석
cat phase5_field_test_report.txt
```

---

**문서 생성**: 2026-01-30
**다음 단계**: 실전 테스트 실행 → Step 3 (문제 도출)
