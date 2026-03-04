# Codex Order: God Object 해체 2차 — `_attach_agents()` 분할

> **목적**: `SovereignApp._attach_agents()` 570줄 → ~163줄 (-71%), 2개 private 메서드 추출.
>   파일 분리 없이 `main_a.py` 내 메서드 분리만 수행.
> **금지**: 로직 변경. 기존 동작/출력 변경. 새 파일 생성. 모델 값 변경.
> **출력 보고서**: `docs/2026-03-04/god-object-2-result.md`

---

## 0) 강제 제약

- 수정 파일: **1개** (`main_a.py`).
- 완료 후 즉시 `python -m py_compile main_a.py` 통과 필수.
- `pytest tests/ -q` 기준선: **3227 passed, 0 failed**.
- `ruff check main_a.py` 위반 0건.

---

## 1) 현재 상태 파악 (수동 검사 필수)

구현 전 아래를 직접 읽어라:

```
파일: main_a.py
읽을 범위:
  - _attach_agents() 전체 (L1428~L1998)
```

확인 사항:
- **섹션 경계**: V50 블록의 시작(`if V50_MODULES_AVAILABLE and _v50:` L1658 근방)과 끝(`except Exception as v50_err:` L1985 근방) 라인 번호 확인
- **섹션 경계**: `self.agents = {...}` dict 시작(L1480 근방)~`self.constraint_compiler = ...` 끝(L1543 근방) 라인 번호 확인
- **공유 변수**: `_v50`, `genre_type`, `default_model`, `Analyst`, `Writer` 등 로컬 변수 중 어느 것이 V50 블록과 core-agents 블록 양쪽에서 사용되는지 확인

---

## 2) 추출 대상 2개 메서드

### A) `_init_core_agents()` — self.agents dict + Python 헬퍼 추출

**추출 대상** (현재 L1480~L1553 근방):

```python
self.agents = {
    "analyst": Analyst(...),
    "writer": Writer(...),
    ...14개 에이전트...
}
self.arc_draft_validator = ArcDraftValidator()
self.constraint_compiler = ConstraintCompiler()
self.arc_corrector = ArcCorrector(...)
self.use_arc_corrector = True
self.stage2_optimizer = ...
self.ui.log(...)  # 초기화 완료 로그 3줄
```

**시그니처**:

```python
def _init_core_agents(self, _agents: dict, _v50: dict | None, models: dict, default_model: str) -> None:
    """[God-2] self.agents dict 구성 + arc_corrector/stage2_optimizer 초기화.

    Args:
        _agents: _lazy_load_agents() 반환값
        _v50: _lazy_load_v50_modules() 반환값 (None 허용)
        models: _get_agent_model_map() 반환값
        default_model: 기본 모델 tier 문자열
    """
```

**`_attach_agents()` 호출부** (self.agents dict 직전에):

```python
self._init_core_agents(_agents=_agents, _v50=_v50, models=models, default_model=default_model)
```

**주의**:
- 추출된 메서드 내에서 클래스 참조(Analyst, Writer 등)는 `_agents` dict에서 꺼내 쓸 것:
  `Analyst = _agents["Analyst"]` 등
- `self.arc_corrector`, `self.arc_draft_validator`, `self.constraint_compiler`, `self.stage2_optimizer` 등 모두 `self.*` 설정이므로 `self` 통해 접근 가능
- 로그 3줄 포함 추출 ("`Stage 2 고도화 모듈...`", "`Stage 2 초기통과율...`", "`Arc Corrector...`")

---

### B) `_init_v50_modules()` — V50 서사 품질 모듈 블록 전체 추출

**추출 대상** (현재 L1655~L1988 근방):

```python
if V50_MODULES_AVAILABLE and _v50:
    try:
        genre_type = ...
        self.pacing_analyzer = ...
        self.quality_amplifier = ...
        ...20+개 V50 모듈 초기화...
        self._load_v50_history()
    except Exception as v50_err:
        self.ui.log(...)
else:
    self.ui.log("   ⚠️ [V50] 모듈 미설치 - 기본 모드")
```

**시그니처**:

```python
def _init_v50_modules(self, _v50: dict | None) -> None:
    """[God-2] V50 서사 품질 향상 모듈 전체 초기화.

    Args:
        _v50: _lazy_load_v50_modules() 반환값 (None이면 기본 모드)
    """
```

**`_attach_agents()` 호출부** (V49.7 트래커 블록 직후):

```python
self._init_v50_modules(_v50=_v50)
```

**주의**:
- `V50_MODULES_AVAILABLE` 전역 변수는 `global V50_MODULES_AVAILABLE` 이미 선언되어 있으므로 접근 가능
- 블록 내부의 `genre_type` 은 `self.selected_genre.get("type", "wuxia") if self.selected_genre else "wuxia"` 패턴으로 메서드 내부에서 재선언
- `self._PROJECTS_DIR`, `self.ui`, `self.current_project`, `self.sys.api_client`, `self.failure_learner`, `self.selected_genre` 등 모두 `self.*`로 접근 가능
- `_V50_MODULE_MODEL`, `AIModels`, `_FLASH_ANALYSIS_MODEL`, `_SUMMARY_MODEL` 은 모듈 레벨 상수이므로 접근 가능
- `self.failure_learner`는 `_init_core_agents()`에서 설정되지 않음 — V50 블록 안에서 설정되므로 `_init_v50_modules()` 내부에서 `self.failure_learner = ...` 선언해야 함

---

## 3) `_attach_agents()` 추출 후 골격

추출 후 `_attach_agents()` 는 아래와 같은 골격이 되어야 함:

```python
def _attach_agents(self) -> bool:
    """[V38 패치] 방어적 에이전트 초기화 ..."""
    try:
        # 1. lazy import
        global V50_MODULES_AVAILABLE, STAGE0_AVAILABLE
        _agents = _lazy_load_agents()
        _v50 = _lazy_load_v50_modules()
        _lazy_load_stage0()
        _spinners_mod.V50_MODULES_AVAILABLE = V50_MODULES_AVAILABLE
        _spinners_mod.STAGE0_AVAILABLE = STAGE0_AVAILABLE

        # 2. models
        models = self._get_agent_model_map()
        if not models:
            self.ui.log("🚨 [Critical] 모델 설정을 불러올 수 없습니다.")
            return False
        default_model = AIModels.STAGE2_MAIN_MODEL

        # 3. core agents + helpers
        self._init_core_agents(_agents=_agents, _v50=_v50, models=models, default_model=default_model)

        # 4. 초기화 검증
        for name, agent in self.agents.items():
            if not hasattr(agent, "ask"):
                self.ui.log(f"🚨 [Critical] {name} 에이전트 초기화 실패")
                return False

        # 5. 장르/Guard/V0128 설정 (기존 코드 그대로)
        if self.selected_genre:
            ...기존 장르 설정 블록...

        # 6. V49.7 ContinuityInspector 트래커 (기존 코드 그대로)
        try:
            ...기존 트래커 블록...

        # 7. V50 모듈
        self._init_v50_modules(_v50=_v50)

        self.ui.log("✅ [System] 모든 에이전트 안전하게 초기화 완료")
        return True

    except Exception as e:
        self.ui.log(f"🚨 [Critical] 에이전트 초기화 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False
```

---

## 4) 실행 순서

```bash
# 패치 후
python -m py_compile main_a.py

# ruff
ruff check main_a.py

# 전체 회귀
pytest tests/ -q
```

---

## 5) 검증 포인트

패치 후 수동 확인:

```python
import ast
src = open('main_a.py', encoding='utf-8').read()
tree = ast.parse(src)
for cls in ast.walk(tree):
    if isinstance(cls, ast.ClassDef) and cls.name == 'SovereignApp':
        for m in cls.body:
            if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and m.name in (
                '_attach_agents', '_init_core_agents', '_init_v50_modules'
            ):
                print(f'  {m.end_lineno - m.lineno:4d}줄  L{m.lineno}~{m.end_lineno}  {m.name}')
```

기대 결과:
- `_attach_agents()`: **≤ 200줄** (기존 570줄 대비 -65% 이상)
- `_init_core_agents()`: **신규 존재**
- `_init_v50_modules()`: **신규 존재 (~340줄)**

---

## 6) 보고서 형식

출력: `docs/2026-03-04/god-object-2-result.md`

```markdown
# God Object 해체 2차 결과

> 감사일: 2026-03-04

## 추출 내역

| 메서드 | 추출 구간 | 크기 |
|--------|----------|------|
| `_init_core_agents()` | L1480~L1553 근방 | N줄 |
| `_init_v50_modules()` | L1655~L1988 근방 | N줄 |

## _attach_agents() 크기 변화

- Before: 570줄 (L1428~L1998)
- After: N줄 (-N%)

## 검증 결과

- py_compile: 통과
- ruff: 위반 0건
- 전체 테스트: N passed, 0 failed (N skipped)
```

---

## 7) 합격 기준

- `_attach_agents()` 줄 수 **≤ 200줄** (기존 570 대비 -65% 이상)
- `_init_core_agents()`, `_init_v50_modules()` **전부 존재**
- **기존 메서드 시그니처 불변** (`_get_agent_model_map`, `_load_v50_history` 등)
- 전체 테스트 **3227+ passed, 0 failed**
- ruff 위반 **0건**
