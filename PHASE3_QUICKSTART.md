# Phase 3 Quick Start Guide

Phase 3 시스템을 실제로 사용하기 위한 빠른 시작 가이드입니다.

## 📋 목차

1. [시스템 개요](#시스템-개요)
2. [사전 준비](#사전-준비)
3. [테스트 실행](#테스트-실행)
4. [대시보드 사용](#대시보드-사용)
5. [RLHF 인터페이스 사용](#rlhf-인터페이스-사용)
6. [Fine-tuning 준비](#fine-tuning-준비)
7. [프롬프트 최적화](#프롬프트-최적화)
8. [통합 워크플로우](#통합-워크플로우)

---

## 🎯 시스템 개요

Phase 3에서 구현된 4개 시스템:

| 시스템 | 파일 | 용도 |
|--------|------|------|
| **Performance Dashboard** | `performance_dashboard.py` | 실시간 성능 모니터링 |
| **Prompt Optimizer** | `modules/core/prompt_optimizer.py` | 자동 프롬프트 개선 |
| **Fine-tuning Automation** | `modules/core/finetuning_automation.py` | Gemini 모델 학습 |
| **RLHF Interface** | `rlhf_interface.py` | 인간 피드백 수집 |

---

## 🔧 사전 준비

### 1. Streamlit 설치 (대시보드용)

```bash
pip install streamlit plotly pandas
```

### 2. 프로젝트 데이터 준비

Phase 3 시스템은 실제 검증 데이터가 필요합니다:

```
datasets/
└── {project_name}/
    ├── approved/      # 승인된 원고들
    │   └── ep_001.json
    └── rejected/      # 거부된 원고들
        └── ep_002.json
```

---

## 🧪 테스트 실행

### Phase 3 통합 테스트

```bash
python test_phase3_systems.py
```

이 스크립트는 다음을 테스트합니다:
- ✅ 데이터 수집 시스템
- ✅ 프롬프트 최적화
- ✅ Fine-tuning 준비 상태
- ✅ RLHF 데이터 수집

**예상 출력:**
```
🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀
  PHASE 3 SYSTEMS INTEGRATION TEST
  All Systems Operational Check
🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀

================================================================================
  1️⃣ Data Collection System Test
================================================================================

✅ Collecting sample validation result...
📊 Dataset Status:
   Approved: 1
   Rejected: 0
   Location: datasets\test_project

🔍 Checking fine-tuning readiness...
   Ready: False
   Approved count: 1
   Required minimum: 100
   ⚠️ Insufficient data: 1/100. Collect 99 more manuscripts.
```

---

## 📊 대시보드 사용

### 실행 방법

```bash
streamlit run performance_dashboard.py
```

브라우저에서 자동으로 `http://localhost:8501` 열림

### 대시보드 기능

1. **KPI 카드**
   - 총 원고 수
   - 승인률
   - 평균 점수
   - 거부 수

2. **점수 분포 차트**
   - 히스토그램: 점수 분포
   - 트렌드 차트: 시간별 점수 변화
   - 상관관계: 원고 길이 vs 점수

3. **검증 단계별 통과율**
   - TIER 1 (BLOCKING) 통과율
   - TIER 2 (SCORING) 통과율
   - Self-Consistency 사용률

4. **데이터 내보내기**
   - CSV 형식으로 다운로드

### 사용 팁

- **프로젝트 선택**: 사이드바에서 프로젝트 이름 입력
- **자동 새로고침**: 기본 10초마다 자동 갱신
- **Raw Data 표시**: 사이드바 체크박스 활성화

---

## 👤 RLHF 인터페이스 사용

### 실행 방법

```bash
streamlit run rlhf_interface.py
```

### 워크플로우

1. **프로젝트 로드**
   - 사이드바에서 프로젝트 이름 입력
   - "Load Manuscripts" 버튼 클릭

2. **원고 검토**
   - AI 평가 결과 확인 (점수, 판정, 피드백)
   - 원고 전문 읽기

3. **인간 평가 입력**
   - 점수 (0-100) 슬라이더로 선택
   - 판정 (APPROVE/REVISE/REJECT) 드롭다운
   - 피드백 텍스트 입력

4. **제출 및 이동**
   - "Submit Feedback" - 현재 평가 저장 후 다음으로
   - "Previous" - 이전 원고로
   - "Skip" - 평가 없이 다음으로

5. **불일치 분석**
   - "Analyze AI vs Human" 버튼 클릭
   - AI와 인간의 평가 차이 통계 확인
   - "Export RLHF Data" - 학습 데이터로 내보내기

### 피드백 가이드라인

인터페이스 하단 "Review Guidelines" 확장 패널 참조:

- **점수 기준**: 85-100 (최상급), 70-84 (통과), 50-69 (재작성), 0-49 (심각)
- **평가 항목**: 설정 일관성, 문장력, 감정 몰입, 상업성, 신선함
- **피드백 작성**: 구체적으로, 건설적으로, 일관되게

---

## 🔬 Fine-tuning 준비

### 준비 상태 확인

```python
from modules.core.finetuning_automation import quick_finetuning_check

# 프로젝트 준비 상태 확인
report = quick_finetuning_check(
    project_name="my_project",
    data_dir="datasets/my_project"
)
```

**출력 예시:**
```
================================================================================
FINE-TUNING READINESS REPORT
================================================================================
Project: my_project
Base Model: gemini-2.5-pro
Timestamp: 2026-01-28 22:30:00

--- Data Readiness ---
Status: ⚠️ NOT READY
Approved Manuscripts: 45
Required Minimum: 100
Reason: Insufficient data: 45/100. Collect 55 more manuscripts.

--- Next Steps ---
1. Continue collecting approved manuscripts
2. Target: 100 approved manuscripts
3. Run this report again when ready
================================================================================
```

### 학습 데이터 준비

준비 완료 후 (100개 이상):

```python
from modules.core.finetuning_automation import FineTuningManager

manager = FineTuningManager("my_project")

# 1. 학습 데이터 생성
training_file = manager.prepare_training_data(
    data_dir="datasets/my_project",
    max_samples=200  # 선택적 제한
)

# 2. 데이터 검증
validation = manager.validate_training_data(training_file)
print(f"Valid: {validation['valid']}")
print(f"Samples: {validation['num_samples']}")
print(f"Issues: {validation['issues']}")

# 3. 비용 추정
cost = manager.estimate_cost(num_samples=200, epochs=3)
print(f"Estimated cost: ${cost['estimated_cost_usd']:.2f} USD")

# 4. 학습 작업 생성
job_info = manager.start_fine_tuning_job(
    training_file=training_file,
    tuned_model_name="my_project_v1",
    learning_rate=0.001,
    epochs=3
)
```

### Google AI Studio에서 실제 학습

위 코드는 준비만 해줍니다. 실제 학습은:

1. https://aistudio.google.com/app/tuned_models 접속
2. "Create tuned model" 클릭
3. 준비된 `.jsonl` 파일 업로드
4. 하이퍼파라미터 설정:
   - Base model: `gemini-2.5-pro`
   - Learning rate: `0.001`
   - Epochs: `3`
5. "Start training" 클릭

---

## 🎯 프롬프트 최적화

### 자동 최적화 실행

```python
from modules.core.prompt_optimizer import quick_optimize

# 검증 결과 로드 (실제 데이터)
validation_results = [...]  # 리스트 형태

# 프롬프트 최적화
improved_prompt, report = quick_optimize(
    prompt=original_prompt,
    validation_results=validation_results,
    prompt_name="director_v2"
)

print(report)
# 최적화된 프롬프트는 optimized_prompts/ 폴더에 저장됨
```

### 반복적 최적화

```python
from modules.core.prompt_optimizer import PromptOptimizer

optimizer = PromptOptimizer("my_project")

# 목표 점수 도달까지 반복
optimal_prompt, history = optimizer.optimize_prompt_iteratively(
    original_prompt=current_prompt,
    validation_results=results,
    target_score=85.0,
    max_iterations=5
)

# 히스토리 확인
for entry in history:
    print(f"Iteration {entry['iteration']}: {entry['avg_score']:.1f}")
```

### A/B 테스트

```python
from modules.core.prompt_optimizer import PromptOptimizer

optimizer = PromptOptimizer()

comparison = optimizer.compare_prompts(
    prompt_a=old_prompt,
    prompt_b=new_prompt,
    results_a=old_results,
    results_b=new_results
)

print(f"Winner: {comparison['winner']}")
print(f"Score improvement: {comparison['improvements']['score_diff']:.1f}")
```

---

## 🔄 통합 워크플로우

전체 Phase 3 시스템을 프로젝트에 통합하는 워크플로우:

### 1단계: 데이터 수집 설정

`main_a.py`에 데이터 수집 추가:

```python
from modules.core.data_collector import DataCollector

class SovereignApp:
    def __init__(self):
        # 기존 초기화 코드...
        self.data_collector = DataCollector(self.current_project.name)

    async def _execute_stage4(self):
        # 기존 Stage 4 로직...

        # V0128 검증 후 데이터 수집
        validation_result = await director.audit_manuscript_v0128(...)

        # 자동 데이터 수집
        self.data_collector.collect_validation_result(
            ep_num=ep_num,
            manuscript=manuscript,
            validation_result=validation_result,
            validation_context=context
        )
```

### 2단계: 실시간 모니터링

별도 터미널에서 대시보드 실행:

```bash
streamlit run performance_dashboard.py
```

프로젝트 진행하면서 실시간으로 성능 모니터링

### 3단계: 주기적 프롬프트 최적화

50개 에피소드마다:

```python
# 최근 50개 검증 결과 로드
recent_results = load_recent_validation_results(50)

# 프롬프트 최적화
optimizer = PromptOptimizer(project_name)
analysis = optimizer.analyze_validation_results(recent_results)

if analysis['avg_score'] < 80:
    # 약점 발견 시 프롬프트 개선
    improved = optimizer.generate_improved_prompt(
        current_prompt,
        analysis['weaknesses'],
        analysis
    )
    # 새 프롬프트 적용
    update_director_prompt(improved)
```

### 4단계: 인간 검토 (주기적)

주말마다 또는 milestone 시점에:

```bash
streamlit run rlhf_interface.py
```

- 승인된 원고 20-30개 샘플링
- 인간 편집자 검토
- AI vs 인간 불일치 분석
- RLHF 데이터 수출

### 5단계: Fine-tuning (100개 이상 달성 시)

```python
from modules.core.finetuning_automation import FineTuningManager

manager = FineTuningManager(project_name)

# 1. 준비 확인
readiness = manager.check_readiness(data_dir)
if readiness['ready']:
    # 2. 데이터 준비
    training_file = manager.prepare_training_data(data_dir)

    # 3. 검증
    validation = manager.validate_training_data(training_file)

    # 4. 비용 추정 확인
    cost = manager.estimate_cost(readiness['approved_count'])
    print(f"Cost: ${cost['estimated_cost_usd']:.2f}")

    # 5. Google AI Studio에 업로드
    print(f"Upload {training_file} to AI Studio")
```

### 6단계: 튜닝 모델 비교

```python
from modules.core.finetuning_automation import FineTuningMonitor

monitor = FineTuningMonitor(project_name)

# 기본 모델 vs 튜닝 모델 비교
comparison = monitor.compare_base_vs_tuned(
    base_results=base_validation_results,
    tuned_results=tuned_validation_results
)

print(f"Score improvement: {comparison['improvements']['score_improvement']:.1f}")
print(f"ROI: {comparison['roi']}")
```

---

## 📈 성공 지표

Phase 3 시스템이 제대로 작동하는지 확인:

| 지표 | 목표 | 확인 방법 |
|------|------|----------|
| **데이터 수집률** | 100% | 모든 검증 결과가 datasets/에 저장됨 |
| **대시보드 응답** | < 2초 | 대시보드 로딩 시간 |
| **프롬프트 개선** | +5점 | 최적화 전후 avg_score 비교 |
| **인간-AI 일치율** | > 85% | RLHF 불일치 분석 |
| **Fine-tuning 준비** | 100+ 원고 | check_readiness() 결과 |

---

## 🚨 문제 해결

### 대시보드가 안 뜨는 경우

```bash
# Streamlit 재설치
pip uninstall streamlit
pip install streamlit

# 포트 충돌 확인
streamlit run performance_dashboard.py --server.port 8502
```

### 데이터가 안 보이는 경우

1. 프로젝트 이름 확인 (대소문자 구분)
2. `datasets/{project_name}/approved` 폴더 존재 확인
3. JSON 파일 형식 확인:
   ```python
   import json
   with open('datasets/my_project/approved/ep_001.json') as f:
       data = json.load(f)
       print(data.keys())  # 필수 키 확인
   ```

### Fine-tuning 준비 안 되는 경우

- 100개 미만: 더 많은 원고 수집 필요
- 원고 너무 짧음: 최소 1000자 이상 권장
- JSON 형식 오류: `validate_training_data()` 실행하여 오류 확인

---

## 📚 추가 문서

- **Phase 3 상세 문서**: `PHASE3_COMPLETE.md`
- **통합 테스트**: `test_phase3_systems.py`
- **V0128 검증 시스템**: `V0128_PHASE1_COMPLETE.md`
- **Phase 2 업그레이드**: `PHASE2_COMPLETE.md`

---

## 🎉 다음 단계

Phase 3 시스템이 준비되었습니다! 이제:

1. ✅ `test_phase3_systems.py` 실행하여 동작 확인
2. ✅ 실제 프로젝트에 데이터 수집 통합
3. ✅ 대시보드로 실시간 모니터링
4. ✅ 100개 원고 달성 시 Fine-tuning 시작
5. ✅ RLHF로 AI 성능 지속 개선

**Happy writing! 🚀**
