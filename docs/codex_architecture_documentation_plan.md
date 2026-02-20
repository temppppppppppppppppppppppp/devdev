# [Codex Task] 전체 시스템 아키텍처 문서 작성

## 목표
시스템을 전혀 모르는 개발자가 Stage 0~4의 **전체 파이프라인**을 이해할 수 있는 
`docs/system_architecture.md` 문서를 작성하라.

## 산출물
- `docs/system_architecture.md` (신규 생성)

---

## ⛔ 강제 규칙 (위반 시 태스크 무효)

### 규칙 1: 검색 도구 사용 절대 금지
- 금지 도구: `rg`, `grep`, `freg`, `greg`, `Select-String`, `findstr`, `git grep`, `codebase_search`, IDE 전역 검색, 기타 패턴 검색 자동화 **전부**.
- 허용 방식: `view_file`, `view_file_outline`, `view_code_item` 등 대상 파일을 **직접 열람하는 단순 읽기만** 허용.
- 근거 규칙: 모든 기술은 최소 1개 이상의 `file:line` 근거를 포함해야 하며, 근거는 수동 열람 내용이어야 한다.
- **위반 처리**: 검색 기반 근거가 1회라도 확인되면 해당 Phase를 처음부터 재수행한다.

### 규칙 2: 파일 별 최소 열람 깊이
- 각 Phase에서 지정된 파일은 **반드시 `view_file` 또는 `view_file_outline`으로 직접 열람**한 후에만 기술할 수 있다.
- "아마 이럴 것이다" 류의 추측 기술 금지 — **코드에서 직접 확인한 것만** 기술한다.

### 규칙 3: 무중단 수행
- Phase 1~8을 사용자 재질문 없이 연속 수행한다.
- 하드 블로커(파일 부재, 권한 오류) 발생 시에만 1회 보고 후 다음 Phase로 진행한다.

### 규칙 4: 컨텍스트 컴팩트 내성
- 컨텍스트 컴팩트 발생 시 즉시 `docs/system_architecture.md`의 마지막 완료 Phase를 확인하고, 다음 Phase부터 재개한다.
- 각 Phase 완료 시 문서에 `<!-- Phase N complete -->` 주석을 남긴다.

---

## Phase 구조 (총 8 Phase)

### Phase 1: 진입점 + 전체 흐름 개요
**필수 열람 파일:**
1. `main_a.py` — 전체 진입점, Stage 순서, CLI 인터페이스
2. `modules/core/project_manager.py` — Stage 오케스트레이션 통합 관리
3. `modules/protocols/app_services.py` — 서비스 프로토콜 정의
4. `modules/protocols/agents.py` — 에이전트 프로토콜 정의

**기술 내용:**
- 프로그램 실행 시작부터 Stage 0→1→2→3→4 호출 순서
- 각 Stage가 무엇을 입력받고 무엇을 출력하는지 (1줄 요약)
- DI(Dependency Injection) 구조 개요
- 전체 파이프라인 흐름도 (텍스트 다이어그램)

---

### Phase 2: Stage 0 — 세계관 초기화
**필수 열람 파일:**
1. `modules/core/stage0/__init__.py` — Stage 0 진입점
2. `modules/core/stage0/preset_registry.py` — 프리셋 레지스트리
3. `modules/core/stage0/reverse_expander.py` — 역확장기
4. `modules/core/stage0/story_expander.py` — 스토리 확장기
5. `modules/core/stage0/style_extractor.py` — 스타일 추출기
6. `modules/core/stage0/spinner.py` — 스피너 (UI?)

**기술 내용:**
- Stage 0의 목적 (세계관/바이블 생성)
- 입력: 사용자 프롬프트 → 출력: MasterBible 구조
- 프리셋 시스템 동작 방식
- reverse_expander vs story_expander 차이
- style_extractor 역할

---

### Phase 3: Stage 1 — 블록 DNA 생성
**필수 열람 파일:**
1. `modules/core/stage01_helpers.py` — Stage 0→1 공용 헬퍼
2. `modules/domain/agents/block_enricher.py` — 블록 농축기
3. `modules/domain/strategies/wuxia_strategy.py` — 전략 예시 (장르별)
4. `modules/domain/strategies/base_strategy.py` — 전략 기반 클래스

**기술 내용:**
- Stage 1의 목적 (서사 블록 분할)
- Block DNA 구조 (context, event_villain, solution, reward 등)
- 장르별 전략(Strategy) 패턴
- block_enricher의 역할과 출력

---

### Phase 4: Stage 2 — Arc 설계
**필수 열람 파일 (순서대로 열람):**
1. `modules/core/stage2_orchestrator.py` — Stage 2 메인 오케스트레이터
2. `modules/core/stage2_context.py` — Stage 2 컨텍스트 객체
3. `modules/core/stage2_preflight.py` — 프리플라이트 (재시도/피드백 루프)
4. `modules/core/stage2_validation_pipeline.py` — 검증 파이프라인
5. `modules/core/stage2_finalizer.py` — 최종 확정기
6. `modules/core/stage2_optimizer.py` — 최적화기
7. `modules/domain/agents/four_phase_arc_generator.py` — 3단계 Arc 생성 파이프라인
8. `modules/domain/agents/arc_ensemble.py` — Arc 앙상블 (3전략 병렬 생성)
9. `modules/domain/agents/analyst.py` — Analyst 에이전트 (Arc 초안 생성)
10. `modules/domain/agents/preflight_checker.py` — 프리플라이트 체커
11. `modules/domain/agents/constraint_compiler.py` — 제약 컴파일러
12. `modules/domain/agents/unified_arc_validator.py` — 통합 Arc 검증기
13. `modules/domain/agents/arc_corrector.py` — Arc 교정기
14. `modules/domain/agents/consensus_validator.py` — 합의 검증기
15. `modules/domain/agents/negative_example_injector.py` — 네거티브 예시 주입기

**기술 내용:**
- Stage 2 전체 흐름도 (Constraint → Generate → Validate)
- Arc 데이터 구조 (`modules/models/arc.py` 참조)
- 앙상블 시스템: 3전략 (conservative/balanced/creative) 병렬 생성 → 최적 선택
- 피드백 루프: REJECT → 피드백 → 재생성 (max_internal_retries)
- Patch Mode: 원본 보존 + 지적사항만 수정
- 검증 파이프라인: Python 검증 + LLM 검증 이중 구조
- Director 피드백 주입 경로

---

### Phase 5: Stage 3 — Blueprint 생성
**필수 열람 파일 (순서대로 열람):**
1. `modules/core/stage3_orchestrator.py` — Stage 3 메인 오케스트레이터
2. `modules/core/stage3_context.py` — Stage 3 컨텍스트
3. `modules/domain/agents/three_phase_blueprint_generator.py` — 3단계 Blueprint 생성
4. `modules/domain/agents/blueprint_ensemble.py` — Blueprint 앙상블 (3전략)
5. `modules/domain/agents/blueprint_constraint_compiler.py` — Blueprint 제약 컴파일러
6. `modules/domain/agents/unified_blueprint_validator.py` — Blueprint 검증기
7. `modules/domain/agents/director.py` — Director 에이전트 (메인)
8. `modules/domain/agents/director_ensemble.py` — Director 앙상블 선택
9. `modules/domain/agents/director_auditor.py` — Director 감사/심사
10. `modules/domain/agents/director_grading.py` — Director 채점

**기술 내용:**
- Stage 3 전체 흐름도
- Blueprint 데이터 구조 (`modules/models/blueprint.py` 참조)
- 앙상블 전략: action_focused / emotion_focused / dialogue_focused
- Director의 역할: 후보 비교 → 선택 → PASS/REJECT 판정
- Director 분해 구조 (director.py, director_ensemble.py, director_auditor.py, director_grading.py)
- Stage 2 Arc → Stage 3 Blueprint 데이터 흐름

---

### Phase 6: Stage 4 — 원고 생성
**필수 열람 파일 (순서대로 열람):**
1. `modules/core/stage4_orchestrator.py` — Stage 4 메인 오케스트레이터
2. `modules/core/stage4_context.py` — Stage 4 컨텍스트
3. `modules/core/stage4_context_builder.py` — 컨텍스트 빌더
4. `modules/core/stage4_interview_round.py` — 인터뷰 라운드
5. `modules/core/stage4_post_processor.py` — 후처리기
6. `modules/domain/agents/chief_writer.py` — ChiefWriter (원고 생성 메인)
7. `modules/domain/agents/chief_writer_context.py` — ChiefWriter 컨텍스트
8. `modules/domain/agents/chief_writer_prompts.py` — ChiefWriter 프롬프트
9. `modules/domain/agents/chief_writer_quality.py` — ChiefWriter 품질 관리
10. `modules/domain/agents/writer.py` — Writer 기본 에이전트
11. `modules/domain/agents/manuscript_validator.py` — 원고 검증기
12. `modules/domain/agents/critic.py` — 비평가 에이전트

**기술 내용:**
- Stage 4 전체 흐름도
- ManuscriptCandidate 구조 (`modules/models/manuscript.py` 참조)
- ChiefWriter 앙상블: 3전략 병렬 생성 + Director 선택
- 인터뷰 라운드 시스템 (Director ↔ Writer 반복 대화)
- 후처리: 원고 정제, 포맷팅
- Stage 3 Blueprint → Stage 4 원고 데이터 흐름
- CoVe(Chain of Verification) 사후검증

---

### Phase 7: 횡단 시스템 (Cross-cutting)
**필수 열람 파일:**
1. `modules/domain/agents/base_agent.py` — 모든 에이전트의 기반 클래스
2. `modules/domain/agents/state_tracker.py` — 상태 추적기 (17+ 필드)
3. `modules/domain/agents/state_extractor.py` — 상태 추출기
4. `modules/domain/agents/continuity_arc.py` — Arc 연속성 검증
5. `modules/domain/agents/continuity_blueprint.py` — Blueprint 연속성 검증
6. `modules/domain/agents/continuity_manuscript.py` — 원고 연속성 검증
7. `modules/core/db_manager.py` — DB 관리자
8. `modules/core/vec_memory.py` — 벡터 메모리
9. `modules/core/feedback_system.py` — 피드백 시스템
10. `modules/core/fact_ledger.py` — 사실 원장
11. `modules/core/prompt_loader.py` — 프롬프트 로더 (YAML)
12. `modules/core/constants.py` — 상수/제한값 정의
13. `modules/models/arc.py` — ArcData Pydantic 모델
14. `modules/models/blueprint.py` — Blueprint Pydantic 모델
15. `modules/models/manuscript.py` — ManuscriptCandidate 모델
16. `modules/models/npc.py` — NPC 모델
17. `modules/validation/validation_orchestrator.py` — 검증 오케스트레이터

**기술 내용:**
- BaseAgent 구조 (ask, _extract_json_robust, Thinking Level 등)
- 상태 관리 체계: StateTracker 필드 목록과 각 Stage 간 계승 흐름
- 연속성 시스템: 3종 Continuity 에이전트의 역할 분담
- DB 구조: anchors, episode_bibles, 캐시
- 벡터 메모리: 임베딩 기반 유사 맥락 검색
- 프롬프트 로더: YAML 기반 프롬프트 관리
- Pydantic 모델: 각 도메인 객체의 필드와 검증 규칙

---

### Phase 8: 문서 조립 + 다이어그램
**작업:**
1. Phase 1~7에서 수집한 내용을 `docs/system_architecture.md`로 조립
2. 전체 파이프라인 다이어그램 (Mermaid flowchart)
3. 각 Stage별 내부 흐름 다이어그램 (Mermaid sequence diagram)
4. 데이터 흐름 표 (입력 → 처리 → 출력)
5. 에이전트 관계 표 (누가 누구를 호출하는지)

---

## 출력 문서 구조 (필수)

```markdown
# 글도비 시스템 아키텍처

## 1. 시스템 개요
### 1.1 전체 파이프라인 흐름도
### 1.2 Stage 요약 표
### 1.3 핵심 설계 철학

## 2. Stage 0 — 세계관 초기화
### 2.1 목적과 입출력
### 2.2 내부 구조
### 2.3 데이터 흐름

## 3. Stage 1 — 블록 DNA 생성
### 3.1 목적과 입출력
### 3.2 내부 구조
### 3.3 장르별 전략 시스템

## 4. Stage 2 — Arc 설계
### 4.1 목적과 입출력
### 4.2 3단계 파이프라인 (Constraint → Generate → Validate)
### 4.3 앙상블 시스템
### 4.4 피드백 / 재시도 루프
### 4.5 검증 파이프라인

## 5. Stage 3 — Blueprint 생성
### 5.1 목적과 입출력
### 5.2 3전략 앙상블
### 5.3 Director 심사 체계
### 5.4 Blueprint 데이터 구조

## 6. Stage 4 — 원고 생성
### 6.1 목적과 입출력
### 6.2 ChiefWriter 앙상블
### 6.3 인터뷰 라운드 시스템
### 6.4 후처리 파이프라인
### 6.5 CoVe 사후검증

## 7. 횡단 시스템
### 7.1 BaseAgent 구조
### 7.2 상태 관리 (StateTracker)
### 7.3 연속성 검증 체계
### 7.4 DB 구조
### 7.5 벡터 메모리
### 7.6 Pydantic 모델
### 7.7 프롬프트 관리 (YAML)

## 8. 데이터 흐름 종합
### 8.1 Stage 간 데이터 전달 표
### 8.2 에이전트 호출 관계 표
### 8.3 피드백/재시도 경로 종합
```

---

## 품질 기준
1. **완전성**: 각 Stage의 모든 주요 파일이 기술에 반영되어야 한다
2. **정확성**: 코드에서 직접 확인한 내용만 기술 (추측 금지)
3. **가독성**: 시스템을 모르는 사람이 읽어도 이해 가능해야 한다
4. **근거**: 핵심 구조 설명에는 반드시 `file:line` 참조 포함
5. **다이어그램**: 최소 3개 이상의 Mermaid 다이어그램 포함

## 최종 유효성 판정
- 위 출력 문서 구조의 모든 섹션이 빠짐없이 존재해야 한다
- 각 Phase에서 지정된 필수 열람 파일이 최소 1회 이상 `file:line`으로 참조되어야 한다
- 검색 도구 사용 흔적이 발견되면 전체 재수행
