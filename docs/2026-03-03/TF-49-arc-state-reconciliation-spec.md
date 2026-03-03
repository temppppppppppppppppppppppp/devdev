# TF-49: Arc 상태 사후 보정 LLM (Arc State Reconciliation Advisor)

> **상태**: 미구현 — 설계 문서만 작성
> **선행**: TF-48 (Arc 간 실행 상태 연속성 보정) 완료 (`00bcef5`)
> **목적**: Arc 생성 후 state_constraints를 실제 실행 상태(WorldState/FactLedger)와 대조, LLM이 불일치를 보정

---

## 문제

TF-48이 Arc 생성 시 실행 상태를 컨텍스트에 주입하지만, LLM이 이를 **무시하거나 잘못 해석**할 수 있음.
예: Arc 2 tactical_doc에 "자본금 20억" 언급 → 실제로는 전액 마진 투입 상태.

**해법**: Arc 생성 **직후**, Director 판정 **직전**에 사후 보정 LLM을 추가.

---

## 설계

### 위치: Stage 2 Finalizer (stage2_finalizer.py)

**삽입 지점**: L390 (enriched_block 주입) ~ L518 (Equipment Sync) 사이.
Director 판정 전, DB 커밋 전.

```
Arc 생성 (FourPhase) → Validation Pipeline → [★ 사후 보정 LLM] → Equipment Sync → Director 판정 → DB 커밋
```

### 클래스: `ArcStateReconciliationAdvisor`

**파일**: `modules/core/arc_state_reconciler.py` (신규)

```python
class ArcStateReconciliationAdvisor:
    """Arc state_constraints vs 실행 상태 불일치 보정."""

    def __init__(self, llm_ask=None):
        self._llm_ask = llm_ask

    @staticmethod
    def build_execution_snapshot(db, arc_no: int, genre: str) -> dict:
        """DB에서 실행 상태 스냅샷 추출.

        Returns:
            {
                "world_state": {protagonist assets, location, injuries, active_items},
                "fact_ledger": {key: {value, last_ep}},
                "last_episode_bible": {capital, total_assets, ...},
                "critical_keys": [genre-specific fields]
            }
        """
        # WorldState anchor → protagonist 상태
        # FactLedger anchor → 수치 팩트
        # episode_bibles → 마지막 에피소드 상태
        # genre_schema_builder.build_state_constraints_schema() → 장르별 핵심 필드
        ...

    def reconcile(self, arc: dict, execution_snapshot: dict, *, genre: str = "wuxia") -> dict:
        """Arc state_constraints를 실행 상태와 대조 후 보정.

        Args:
            arc: 생성된 Arc dict (state_constraints 포함)
            execution_snapshot: build_execution_snapshot() 결과
            genre: 장르 코드

        Returns:
            보정된 arc dict (state_constraints 수정됨, 나머지 불변)
            arc["_reconciliation_log"]: 보정 내역 리스트
        """
        ...
```

### 보정 흐름

```
1. Python 사전 검증 (LLM 불필요한 경우 스킵)
   - arc_start_state vs WorldState 수치 비교
   - fact_ledger 핵심 수치 vs state_constraints 수치 비교
   - 차이 없으면 → 보정 불필요, 원본 반환

2. 차이 발견 시 → LLM 보정 호출
   프롬프트:
   - "다음 Arc의 state_constraints가 실제 실행 상태와 불일치합니다."
   - [실행 상태 스냅샷] vs [Arc state_constraints]
   - "불일치 항목을 실행 상태 기준으로 보정한 state_constraints JSON을 반환하세요."
   - "tactical_doc 내 수치 언급도 함께 보정하세요."

3. LLM 응답 파싱 → arc["state_constraints"] 덮어쓰기
   - 실패 시 → 원본 유지 + 경고 로그 (fail-safe)

4. 보정 내역 arc["_reconciliation_log"]에 기록
```

### 장르별 핵심 필드 (genre_schema_builder 재활용)

| 장르 | 보정 대상 핵심 필드 |
|------|---------------------|
| wuxia | power_level, cultivation_realm, injuries, techniques |
| hunter | awakening_rank, mana, level, skills |
| investment | capital, total_assets, stocks, market_insight |
| composer | composition, reputation, wealth |
| cooking | chef_rank, restaurant_tier, reputation |
| alt_history | court_rank, faction, political_influence, wealth |
| actor | fame, filmography, box_office, wealth |
| sports | athlete_tier, ranking, record |
| medical | doctor_rank, surgery_count, success_rate |

### Stage 2 배선

```python
# stage2_finalizer.py — Director 판정 전
from modules.core.arc_state_reconciler import ArcStateReconciliationAdvisor

_exec_snap = ArcStateReconciliationAdvisor.build_execution_snapshot(
    db=self.ctx.current_project.db,
    arc_no=refined_arc.get("arc_no", 1),
    genre=self.ctx.selected_genre.get("type", "wuxia"),
)
if _exec_snap.get("world_state") or _exec_snap.get("fact_ledger"):
    _reconciler = ArcStateReconciliationAdvisor(llm_ask=_llm_ask_fn)
    refined_arc = _reconciler.reconcile(
        refined_arc, _exec_snap,
        genre=self.ctx.selected_genre.get("type", "wuxia"),
    )
```

### llm_ask 확보

기존 패턴 따름: `self.ctx.agents["director"].ask(prompt, temperature=0.1)`
(Stage 2에서 director agent 사용 가능)

---

## 2차 방어선: generate_arc_context_v60() 보강

**파일**: `modules/core/prompt_builder.py` L528 `generate_arc_context_v60()`

이 함수도 Arc 간 컨텍스트를 만드는 별도 경로. TF-48이 `_generate_prev_context()`만 수정했으므로,
여기에도 실행 상태 블록 추가 필요.

```python
# prompt_builder.py generate_arc_context_v60() 내부
# 기존: Arc N의 arc_end_state만 참조
# 추가: WorldState/FactLedger 실행 상태 블록 삽입
```

---

## 원칙

1. **Python 사전 검증 → LLM은 불일치 있을 때만** (비용 절감)
2. **fail-safe**: LLM 실패 시 원본 Arc 유지 (advisory, not blocking)
3. **기존 패턴 준수**: llm_ask callable, static DB 메서드, JSON 반환
4. **Director 주권 보존**: 보정은 state_constraints 수치만, 서사 구조(tactical_doc 줄거리)는 건드리지 않음
5. **genre_schema_builder 재활용**: 장르별 핵심 필드 새로 정의하지 않음

---

## 검증 계획

1. `py_compile` + `ruff check` 구문/린트
2. `pytest tests/ -q` 회귀 (3,170 passed 유지)
3. 투자물 Arc 1→2 생성 테스트:
   - Arc 1 에피소드 실행 후 마진 20억 투입 상태
   - Arc 2 생성 시 `_reconciliation_log`에 "capital 보정" 기록 확인
   - Arc 2 state_constraints.arc_start_state에 실제 자본 상태 반영 확인
4. 무협 Arc 테스트: 보정 불필요 시 스킵 확인 (불필요한 LLM 호출 없음)
