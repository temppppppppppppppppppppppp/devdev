# stage_map 고도화 오더 — Codex 실행용

> 생성: 2026-02-25
> 목적: 새 세션 AI가 stage_map만 읽고 바로 작업 가능하도록 "왜"와 "함정" 추가

---

## 실행 제약 (필수)

- rg/grep/find/bash 자동화 금지 — Read 툴로 파일 직접 읽기만
- 파일 하나 완료 즉시 Write/Edit 저장 → doc_status.md 업데이트
- 추측 금지, 코드 확인된 것만. 모르면 TBD
- 컨텍스트 소진 시: ENHANCE_ORDER.md + doc_status.md 읽고 미완료부터 재개

---

## 작업 1: `gotchas.md` 신규 생성

경로: `C:\Users\wjjo\Desktop\글도비\docs\stage_map\gotchas.md`

### 목적
새 세션 AI가 "당연히 이렇겠지" 하고 잘못 판단하는 것들을 사전에 막는 문서.
코드 읽지 않아도 함정을 피할 수 있어야 함.

### 반드시 포함할 항목 (확인된 사실)

#### G-1. Stage 3 REJECT 거의 안 발동
- Director가 3개 후보 중 최소 1개에 95~100점 부여하는 경향
- 실제로 전량 1회 PASS 발생함 (2026-02-25 0225_1 프로젝트 6~19화 로그 기준)
- in-place patch (_inplace_patch_blueprint) 경로 구현은 됐으나 실제 발동 드묾
- 원인: 프롬프트에 점수 앵커링 없음. LLM이 "모순 없음 = 고득점" 경향
- 확인 파일: `modules/domain/agents/three_phase_blueprint_generator.py`

#### G-2. PASS_WITH_WARNING 사실상 항상 발동
- 3회 재시도 전부 REJECT여도 score ≥ 50이면 PASS_WITH_WARNING으로 통과
- 진정한 FAILED = score < 50 또는 생성 자체 실패. 실제로 거의 도달 불가
- 확인 파일: `three_phase_blueprint_generator.py` L442 부근

#### G-3. Blueprint txt 파일은 컨텍스트 아님
- `projects/{name}/plans/blueprints/blueprint_XXXX.txt` → 사람 읽기용 백업
- Stage 4는 DB 전용: `project_manager.get_blueprint(ep_num)` → `db.get_blueprint()`
- txt 수정해도 Stage 4에 반영 안 됨
- 확인 파일: `modules/core/project_manager.py` L832

#### G-4. WARNING 로그 레벨 남용 — 정상 동작임
- `WARNING:root:🎲 [BPEnsemble] 3개 후보 병렬 생성 중...` 같은 정보성 메시지가 WARNING으로 출력
- 버그 아님. 로그 레벨 정리가 안 된 레거시 패턴
- 실제 오류 WARNING과 구분 어려울 수 있으나 무시해도 됨

#### G-5. Director 주권주의 — Python이 LLM 판단 뒤집으면 안 됨
- 4대 원칙 중 하나. Director(LLM)가 PASS를 줬으면 Python이 REJECT로 뒤집으면 안 됨
- 위반 사례 발견 및 수정됨: Stage 3 QualityGate가 90점으로 Director 프롬프트(80점) 기준보다 높게 설정됐었음
- 수정: `blueprint_quality_gate_score: 80` 분리 (커밋 f99119d, 2026-02-25)
- 새 코드 짤 때 Python QualityGate를 Director 프롬프트 REJECT 기준보다 높게 설정하면 안 됨

#### G-6. quality_gate_score는 Stage마다 다름
- Stage 3 Blueprint: `scoring.blueprint_quality_gate_score: 80`
- Stage 2 Arc / Stage 4 원고: `scoring.quality_gate_score: 90`
- 확인 파일: `config/settings/validation.yaml`

#### G-7. 수치 모순은 Blueprint 레벨에서 잡힘
- Director 비교 선택 프롬프트가 수치 모순을 실제로 잡아냄
- 예: 14화 "110억 수익 vs 215억 자산 충돌"로 후보 2,3 탈락 (2026-02-25 확인)
- 단, 이건 "후보 탈락"이지 "전체 라운드 REJECT"가 아님

#### G-8. data_anchors 테이블 키 규칙
- Arc 저장: `key="arcs"`, `stage="arcs"`
- 단일 JSON 덩어리로 전체 Arc 목록 저장 (화별 분리 아님)
- 삭제 시 주의: `DELETE WHERE key='arcs'`면 전체 Arc 날아감 (메뉴 88 동작)

### 포맷
```markdown
# Gotchas — 새 세션 AI 주의사항

> 이 문서를 먼저 읽어라. 코드 보기 전에 알아야 할 함정들.

## G-1. [제목]
**현상**: ...
**원인**: ...
**실제 영향**: ...
**확인 위치**: 파일명 + 라인
```

---

## 작업 2: `agent_graph.md` 신규 생성

경로: `C:\Users\wjjo\Desktop\글도비\docs\stage_map\agent_graph.md`

### 목적
어떤 에이전트가 어떤 에이전트를 호출하는지 텍스트 다이어그램으로 표현.
"이 버그 어디서 나왔지?" 추적 시 출발점 역할.

### 읽어야 할 파일
- `modules/core/stage3_orchestrator.py` — Stage 3 에이전트 호출 순서
- `modules/core/stage4_orchestrator.py` — Stage 4 에이전트 호출 순서
- `modules/core/stage2_orchestrator.py` — Stage 2 에이전트 호출 순서
- `modules/domain/agents/three_phase_blueprint_generator.py` — Blueprint 생성 내부
- `modules/domain/agents/unified_blueprint_validator.py` — Validator 내부
- `modules/domain/agents/director_ensemble.py` — Director 비교 선택

### 포함할 내용
텍스트 기반 호출 트리 (ASCII):
```
Stage 3 호출 트리:
stage3_orchestrator
  └─ ThreePhaseBlueprintGenerator.generate()
       ├─ BlueprintConstraintCompiler.compile()
       ├─ BlueprintEnsembleGenerator.generate_ensemble()  ← 3개 병렬
       │    └─ [LLM 3회 병렬 호출]
       ├─ UnifiedBlueprintValidator.validate()
       │    ├─ DirectorEnsemble.compare_and_select_blueprint()  ← 3개 비교
       │    └─ [QualityGate: blueprint_quality_gate_score=80]
       └─ (REJECT 시) _inplace_patch_blueprint()  ← 단일 LLM 1회
```
Stage 2, Stage 4도 동일 형식으로.

### 확인 필요 항목
- `BlueprintEnsembleGenerator`가 실제로 병렬인지 (ThreadPoolExecutor 확인)
- `UnifiedBlueprintValidator` 내부에서 DirectorEnsemble 외에 다른 에이전트 호출하는지
- Stage 4에서 Director가 `director_continuity.py`인지 `director_auditor.py`인지

---

## 작업 3: 기존 stage 문서에 "설계 의도(Why)" 섹션 추가

대상 파일: `stage2.md`, `stage3.md`, `stage4.md`
각 파일에 `## Why` 섹션 추가 (3~5줄 이내).

### stage3.md에 추가할 내용
```markdown
## Why
- **왜 3개 후보 병렬 생성?** 전략 다양성 확보 (액션/감정/대화 전략). Director가 비교 선택해 최선 채택.
- **왜 in-place patch?** score ≥ 60이면 전면 재생성보다 단일 수정이 빠름 (~30초 vs ~2분).
- **왜 blueprint_quality_gate_score=80?** Director 프롬프트 "80점 미만 REJECT" 기준과 일치시켜 주권주의 유지.
```

### stage2.md에 추가할 내용
읽어야 할 파일: `docs/stage_map/stage2.md` (기존 내용 확인 후 Why 섹션 추가)
내용: 왜 4Phase인가, 왜 앙상블인가, 왜 Director audit이 분리됐는가

### stage4.md에 추가할 내용
읽어야 할 파일: `docs/stage_map/stage4.md` (기존 내용 확인 후 Why 섹션 추가)
내용: 왜 Blueprint를 DB에서만 읽는가, 왜 Chief Writer와 Director가 분리됐는가

---

## 작업 4: doc_status.md 업데이트

완료된 파일마다 행 추가:
```
| `gotchas.md`      | Active | Yes | 2026-02-25 | ENHANCE_ORDER 실행 | Codex | G-1~G-8 |
| `agent_graph.md`  | Active | Yes | 2026-02-25 | ENHANCE_ORDER 실행 | Codex | 호출 트리 |
```

---

## 실행 순서

### 1차 (핵심 — 반드시 완료)
1. `gotchas.md` 생성 (코드 확인 거의 불필요, 이미 확인된 사실만)
2. `agent_graph.md` 생성 (파일 읽기 필요 — 호출 트리 추적)

### 2차 (보완)
3. `stage3.md` Why 섹션 추가
4. `stage2.md` Why 섹션 추가
5. `stage4.md` Why 섹션 추가

### 3차 (마무리)
6. `doc_status.md` 업데이트

---

## 완료 기준

새 세션 AI가 stage_map 폴더만 읽고 아래를 할 수 있으면 성공:
- Stage 3에서 REJECT 안 나오는 이유를 코드 안 봐도 설명 가능
- Blueprint 수정 시 txt가 아닌 DB를 건드려야 한다는 걸 앎
- Director 주권주의 위반하는 코드 안 짬
- 에이전트 호출 순서를 보고 버그 발생 위치 추론 가능
