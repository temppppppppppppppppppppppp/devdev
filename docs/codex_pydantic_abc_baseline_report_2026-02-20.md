# Codex Pydantic/ABC 코드 실측 1차 보고서

> 측정일: 2026-02-20  
> 범위: `modules/**/*.py`  
> 방식: 저장소 코드 직접 계측(정량 + 라인 근거)

---

## 1. 요약 결론

1. `Pydantic`은 **부분 도입 완료** 상태다.
2. `ABC`는 **선택 지점(가드/전략/HUD 추상화)**에만 적용된 상태다.
3. 따라서 현재는 “전면 완료”가 아니라 **핵심 경계 일부 보호 + 확장 여지 다수** 상태다.

---

## 2. 정량 실측

| 항목 | 값 |
|---|---:|
| 전체 Python 파일 수 (`modules`) | 211 |
| `pydantic` import 파일 수 | 4 |
| `BaseModel` 클래스 수 | 15 |
| `model_validate()` 호출 hit | 7 *(주석 포함)* |
| `model_dump()` 호출 hit | 7 *(주석 포함)* |
| 실제 파이프라인 `validate_*` 호출 지점 | 3 |
| `ABC` 추상 클래스 수 | 3 |
| `@abstractmethod` 개수 | 6 |

---

## 3. Pydantic 현황 (실측 근거)

적용 모델 파일:

1. `modules/models/arc.py`
2. `modules/models/blueprint.py`
3. `modules/models/manuscript.py`
4. `modules/models/npc.py`

주요 모델(총 15개):

1. `modules/models/arc.py:24` `ArcState`
2. `modules/models/arc.py:163` `ArcData`
3. `modules/models/blueprint.py:29` `Blueprint`
4. `modules/models/manuscript.py:18` `ManuscriptCandidate`
5. `modules/models/npc.py:20` `NPCEntry`

실제 파이프라인 주입 지점:

1. `modules/core/stage2_finalizer.py:307` `validate_arc(refined_arc)`
2. `modules/domain/agents/chief_writer.py:382` `validate_manuscript_candidate(c)`
3. `modules/domain/agents/three_phase_blueprint_generator.py:376` `validate_blueprint(best_blueprint)`

판정:

1. Stage2/3/Writer 경계 일부는 Pydantic ingress/egress가 적용됨.
2. Stage0, Stage4 핵심 경계 전반은 아직 광범위하게 모델 검증이 들어간 상태는 아님.

---

## 4. ABC 현황 (실측 근거)

적용 지점:

1. `modules/core/genre_hud_manager.py:10` `GenreHUDManager(ABC)`
2. `modules/core/genre_guards/base_guard.py:16` `BaseGuard(ABC)`
3. `modules/domain/strategies/base_strategy.py:4` `BaseStrategy(ABC)`

`@abstractmethod`:

1. `modules/core/genre_hud_manager.py:63`
2. `modules/core/genre_hud_manager.py:68`
3. `modules/core/genre_guards/base_guard.py:48`
4. `modules/core/genre_guards/base_guard.py:165`
5. `modules/domain/strategies/base_strategy.py:12`
6. `modules/domain/strategies/base_strategy.py:16`

미적용 대표:

1. `modules/domain/agents/base_agent.py:125` `class BaseAgent:` *(ABC 아님)*

판정:

1. ABC는 “확장 포인트 일부”에 의도적으로 적용됨.
2. 에이전트 공통 베이스까지 일괄 추상화된 상태는 아님.

---

## 5. 갭 요약

1. Pydantic 도입 범위는 `modules/models` + 3개 호출 지점에 집중되어 있음.
2. Stage4 경계(`interview_round`, `post_processor`)는 타입 경계가 상대적으로 느슨함.
3. ABC는 가드/전략/HUD 추상화에는 유효하나, 전체 에이전트 계층 표준화까지는 미도달.

---

## 6. 2차 확장 우선순위 제안

1. P0: Stage4 입출력 경계에 Pydantic ingress 추가 (`director_result`, `candidates`, `state_updates`).
2. P1: Stage0/Stage2/Stage4 공통 `state_changes`, `joint_docs`, `episode_bible_delta` 모델 표준화.
3. P2: ABC는 `검증기/후처리 인터페이스` 같은 교체 가능 지점만 선택 확장.
4. P3: `BaseAgent`는 즉시 ABC 전환보다 “프로토콜/인터페이스 명세 + 점진 분리” 권장.

---

## 7. 최종 판정

1. 질문: “Pydantic/ABC 다 된 상태인가?”  
2. 답: **아니다. Pydantic은 부분 완료, ABC는 선택 지점 적용 상태다.**

