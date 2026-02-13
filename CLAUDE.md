# 글도비 — 후임 에이전트 인수인계

> AI 웹소설 자동 생성 시스템. Python + Gemini API.
> 상세 참고: `참고자료.md` (2000줄+ 종합 자료)

---

## ⚖️ 대원칙 (절대 위반 금지)

1. **Python은 수집만, 판단은 LLM이** — Python은 데이터 수집·포맷팅·전달만. "오류인가?", "수정할까?" 같은 판단은 LLM 에이전트가 담당.
2. **팩트시트 수정 권한은 LLM만** — NPC 속성, 세계관 설정, 관계도를 수정하는 건 LLM뿐. Python이 자동으로 팩트를 덮어쓰면 안 됨.
3. **디렉터 주권주의 (내각제)** — Director가 최종 품질 결정권. Chief Writer·Analyst 등은 초안 제출만, 합격/불합격/수정 지시는 Director가 내림. Director를 우회하면 안 됨.
4. **사망 캐릭터는 회상/언급만 허용** — `deceased=True` NPC가 행동/대사로 등장하면 REJECT. 회상·과거 장면·타인 언급은 허용.

---

## 파이프라인

```
Stage 0 (초기 설정)  →  Stage 2 (Arc/Blueprint)  →  Stage 4 (원고)
세계관 바이블 추출       Analyst → Arc → Blueprint     Chief Writer → Director 심사
NPC 등록                앙상블 + 검증 체인              합격/불합 → 재작성 루프
문체 분석                연속성 검사                    카카오/네이버 포맷 출력
```

---

## 현재 상태 (2026-02-13)

- **작동함**: Stage 0→2→4 정상 동작
- **완료된 것**: Phase 1(logging), 1.5(에러핸들링), 2-B(type hints 95.5%), 5-A(프롬프트 외부화 43개), 5-C(의존성 정리), 6-C(pre-commit+ruff), 6-A(pytest 63개 신규)
- **약점**: NPC 연속성 추적 약함 (시나리오 24개 — 참고자료 3-C), 플롯 중복 감지 불안정 (Chain 1, lazy init + 재시도 1회 적용 완료)

---

## 핵심 파일

| 파일 | 역할 | 비고 |
|------|------|------|
| `modules/core/stage2_orchestrator.py` | Arc 오케스트레이터 (2134줄) | God Object (`self.app` 341건) |
| `modules/core/stage4_orchestrator.py` | 원고 오케스트레이터 (1633줄) | God Object (`self.app` 312건) |
| `modules/core/db_manager.py` | SQLite DB 매니저 | 모범 패턴 |
| `modules/core/prompt_loader.py` | YAML 프롬프트 로더 (싱글톤) | |
| `config/prompts/*.yaml` | 외부화된 프롬프트 43개 | |
| `modules/domain/agents/*.py` | AI 에이전트 20+개 | |
| `modules/core/genre_guards/*.py` | 장르 가드 3개 | 외부화 예정 |
| `modules/validation/*.py` | 검증 파이프라인 | |

---

## ⚠️ 주의

- `writer.py` — 레거시이나 유틸리티 3개가 stage4에서 직접 호출됨. Phase 2에서 이전 후 삭제.
- `memory_engine.py` — ChromaDB 비활성화 상태. import하면 에러남.
- NPC 속성 변경 — DB 덮어쓰기 방식. 이력 없음. Phase 3에서 개선 예정.
- `base_agent.py`의 `_context_caches` — Gemini Context Caching 필드가 있지만 미활성. 활성화하면 토큰 절감.

---

## SAFE 작업

| Phase | 작업 | 상태 |
|-------|------|------|
| 6-C | pre-commit + ruff 설정 | ✅ 완료 |
| 6-A | pytest 테스트 (GenreGuard, RepetitionGuard, PromptLoader — 63개) | ✅ 완료 |
| 5-A' | PromptLoader import 전환 (7파일 완료) | ✅ 완료 (2026-02-13) |
| 5-B | Settings YAML 통합 + 장르/작품 가드 외부화 | 미착수 |

## RISKY 작업 (순서 지킬 것)

| 순서 | Phase | 작업 | 전제 |
|------|-------|------|------|
| 1 | 2-A | Pydantic 모델 도입 | 2-B ✅ |
| 2 | 2.5 | sqlite-vec (ChromaDB 교체) | 2-A |
| 3 | 3 | NPC 이력 + 관계 그래프 + 수정 모드 + 대리만족 검증 | 2-A |
| 4 | 4 | God Object 분해 + 파일 분할 | 3 |

---

## 기존에 있지만 제대로 안 쓰이는 것들

| 기능 | 파일 | 상태 |
|------|------|------|
| 시점 전환 프리셋 | `blueprint_ensemble.py` L81~84 | ✅ 존재, YAML 연동만 필요 |
| 시점(POV) 일관성 체크 | `pre_llm_validator.py` V70 | ✅ 구현됨 |
| A/B 테스트 | `ab_testing.py` | ⚠️ `quick_ab_test()` 존재, 확장 필요 |
| 에피소드 롤백 | `project_manager.py` | ⚠️ `auto_backtrack_v35()`, NPC 되감기 추가 필요 |
| 문체 분석 | `stage0/style_extractor.py` | ⚠️ 있음, 가드 자동생성 연동 필요 |
| Context Caching | `base_agent.py` | ⚠️ 필드만 존재, 활성화 필요 |

---

## 상세 정보

**`참고자료.md`를 반드시 읽을 것.** 포함 내용:
- 시스템 아키텍처 전체 구조도
- 버그 패턴 분석 (Tier 1~8)
- NPC 연속성 실패 시나리오 24개 (3-C)
- 수정 모드 전략 (3-D)
- 개선 아이디어 27개 + 대조표 (3-E)
- 독자 대리만족 프레임워크 (3-F)
- 리팩토링 Phase 1~6 로드맵

