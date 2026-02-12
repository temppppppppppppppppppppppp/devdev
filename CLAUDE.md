# 글도비 (GloDoBi) — AI 웹소설 자동 생성 시스템

## 프로젝트 개요

Python + Gemini API 기반 AI 웹소설 자동 생성 파이프라인.
사용자(PD)가 세계관·캐릭터를 설정하면, AI 에이전트들이 Arc 설계 → Blueprint → 원고 집필을 자동 수행.

## 핵심 파이프라인

```
Stage 0 (초기 설정)  →  Stage 2 (Arc/Blueprint 설계)  →  Stage 4 (원고 집필)
   ↓                        ↓                              ↓
세계관 바이블 추출      Analyst → Arc → Blueprint       Chief Writer → Director 심사
NPC 등록              앙상블 + 검증 체인               합격/불합격 → 재작성 루프
문체 분석              연속성 검사                     카카오/네이버 포맷 출력
```

## 핵심 파일 맵

| 파일 | 역할 | 비고 |
|------|------|------|
| `modules/core/stage2_orchestrator.py` | Arc 오케스트레이터 (2134줄) | God Object, 리팩토링 예정 |
| `modules/core/stage4_orchestrator.py` | 원고 오케스트레이터 (1633줄) | 1354줄 단일 try-except |
| `modules/core/db_manager.py` | SQLite DB 매니저 | 모범 패턴 |
| `modules/core/prompt_loader.py` | YAML 프롬프트 로더 (싱글톤) | |
| `config/prompts/*.yaml` | 외부화된 프롬프트 (43개) | |
| `modules/domain/agents/*.py` | AI 에이전트 20+개 | |
| `modules/core/genre_guards/*.py` | 장르 가드 3개 | 외부화 예정 |
| `modules/validation/*.py` | 검증 파이프라인 | |
| `참고자료.md` | **종합 참고자료 (2000줄+)** | **반드시 먼저 읽을 것** |

## 현재 상태 (2026-02-12)

- **작동함**: 원고 생성 파이프라인(Stage 0→2→4) 정상 동작
- **완료된 리팩토링**: Phase 1(logging), 1.5(에러핸들링), 2-B(type hints 95.5%), 5-A(프롬프트 외부화), 5-C(의존성 정리)
- **주요 약점**: NPC 연속성 추적 약함, 플롯 중복 감지 불안정

## 즉시 실행 가능한 SAFE 작업

1. **5-A'**: PromptLoader import 전환 (40+파일)
2. **5-B**: Settings YAML 통합 + 장르/작품 가드 외부화
3. **6-A**: pytest 테스트 도입
4. **6-C**: pre-commit + ruff 설정

## RISKY 작업 (순서 중요)

1. **2-A**: Pydantic 모델 도입 (전제: 2-B ✅)
2. **2.5**: sqlite-vec 도입 — ChromaDB 교체 (전제: 2-A)
3. **3**: NPC 이력 테이블 + 관계 그래프 + 수정 모드 (전제: 2-A)
4. **4**: God Object 분해 + 파일 분할 (전제: 3)

## ⚠️ 주의 사항

- `writer.py`는 레거시이나 유틸리티 3개 메서드가 stage4에서 직접 호출됨 — Phase 2에서 이전 후 삭제
- `memory_engine.py`는 ChromaDB 비활성화 상태 — import하면 에러남 (sqlite-vec 도입 전까지)
- NPC 속성 변경은 DB 덮어쓰기 방식 — 이력 없음 (Phase 3에서 개선 예정)
- `self.app`은 God Object (stage2: 332건, stage4: 291건) — DI 패턴 전환 예정

## 개발 환경

- Python 3.11+
- Google Gemini API (google-genai)
- SQLite (내장 DB)
- PySide6 (UI)
- 참고: `requirements.txt` 참조

## 상세 정보

**`참고자료.md`를 반드시 먼저 읽을 것.** 아키텍처 상세, 버그 패턴 분석, 리팩토링 로드맵, 개선 아이디어 26개 + 대리만족 프레임워크, 기존 기능 대조표 등 전체 컨텍스트가 포함되어 있음.
