# Opus TF 전체 구조 감사 보고서
> **날짜**: 2026-02-20
> **TF 구성**: 5개 Opus 에이전트 병렬 감사
> **범위**: LLM 상호작용, 데이터 흐름, 검증 파이프라인, 아키텍처, 도메인 로직
> **재검토**: 2회 (중복 병합 + 오탐 제거 → 심각도 재분류 + 실행 가능성 확인)
> **목적**: "사용자가 지능이 높거나 지식이 많았으면 좋았을 것들" — 전문성이 필요한 개선 사항

---

## Executive Summary

| 심각도 | 건수 | 설명 |
|--------|------|------|
| CRITICAL | 14 | 데이터 손실, 품질 바이패스, 장기연재 파괴 위험 |
| IMPORTANT | 25 | 품질 저하, 비효율, 미활용 시스템 |
| INSIGHT | 16 | 기술부채, 설계 개선 기회, 관측 사항 |
| **합계** | **55** | (중복 13건 병합, 오탐 1건 제거 후) |

**가장 심각한 3개 클러스터:**
1. **검증 파이프라인 무력화** — Pre-LLM 항상 통과, 장르 가중치 미적용, RetrospectiveValidator 비활성
2. **장기연재 컨텍스트 손실** — FactLedger 10건 한도, WorldState 30 NPC 요약 절단, 수치 팩트 미추적
3. **DB 트랜잭션 안전성** — Stage2 실패 시 암묵적 트랜잭션 미롤백, WorldState/원고 비원자적 저장

---

## 1. CRITICAL Findings (14건)

### 1-A. 검증 파이프라인 (4건)

#### C-01. Pre-LLM Validator 항상 통과 — 점수 차감 미적용
- **TF**: TF-3 (Validation)
- **파일**: `modules/validation/pre_llm_validator.py:130`, `validation_orchestrator.py:238-260`
- **내용**: `pre_llm_result["passed"]`가 항상 `True`. ValidationOrchestrator의 `if not pre_llm_result["passed"]` 분기는 **도달 불가 코드**. Pre-LLM에서 감지한 과도한 반복, 대화 부재, 물리법칙 위반 등의 `score_deduction`(최대 10점)이 최종 점수에 **반영되지 않음**.
- **영향**: Python으로 확실히 감지 가능한 표면 결함이 점수에 무영향
- **난이도**: LOW (score_deduction 합산 배선만 추가)

#### C-02. 장르별 가중치 스코어링(validate_v59) 미호출
- **TF**: TF-3 (Validation)
- **파일**: `modules/validation/scoring_validator.py:726`, `validation_orchestrator.py:365`
- **내용**: `validate_v59`에 정의된 장르별 가중치 프로필(무협: sensory 1.3x, 투자: dialogue 1.3x 등)이 **프로덕션 경로에서 한 번도 호출되지 않음**. Orchestrator는 `self.scoring.validate()`만 호출.
- **영향**: 모든 장르가 동일 가중치로 평가됨. 무협 원고의 감각묘사 부족이 가중 감점 안 됨
- **난이도**: LOW (호출 교체)

#### C-03. Degraded Blocking Check 자동 통과
- **TF**: TF-3 (Validation)
- **파일**: `modules/validation/blocking_validator.py:165-176`, `blocking_validator_consistency_checks.py:291-293`
- **내용**: `_check_relationship_consistency` 또는 `_check_information_consistency` 예외 발생 시 `{"passed": True, "degraded": True}` 반환. 의존 모듈 초기화 오류 시 **영구적 검증 공백** 발생.
- **영향**: RelationshipTracker/InformationDiffusion 오류 시 관계/정보 일관성 검사 무효화
- **난이도**: MEDIUM (degraded 카운터 + 임계값 알림 추가)

#### C-04. RetrospectiveValidator 기본 비활성
- **TF**: TF-3 (Validation)
- **파일**: `modules/validation/validation_orchestrator.py:184`
- **내용**: `use_retrospective = config.get("use_retrospective", False)`. 다중 에피소드 일관성 검사(경지 퇴행, 아이템 소실, 해결된 갈등 재발)가 **수동 활성화 전까지 동작하지 않음**.
- **영향**: 3화 이상 걸친 플롯홀 자동 감지 불가
- **난이도**: LOW (기본값 True 변경 + 성능 테스트)

### 1-B. 장기연재 컨텍스트 손실 (4건)

#### C-05. FactLedger MAX_HISTORY_PER_ENTITY = 10 — 주요 캐릭터에 부족
- **TF**: TF-5 (Domain)
- **파일**: `modules/core/fact_ledger.py` 상수
- **내용**: 200화 연재 시 주인공/주적의 중요 사건이 50건 이상. 11번째 사실 입력 시 1번째(예: "왼팔 절단") 영구 삭제. LLM이 양팔 사용 장면을 생성할 수 있음.
- **영향**: 장기연재 시 핵심 팩트 소실 → 연속성 파괴
- **난이도**: LOW (상수 증가, 주요 캐릭터 별도 한도)

#### C-06. WorldState 요약 NPC 30명 절단
- **TF**: TF-5 (Domain)
- **파일**: `modules/core/world_state.py:280-320`
- **내용**: `get_summary()`에서 alive NPC를 30명까지만 표시. 100화+ 무협 소설은 50-80명 NPC 보유. 절단된 NPC가 LLM 컨텍스트에서 소실 → 새 캐릭터로 재도입, 관계 초기화, 사망 NPC 부활 위험.
- **영향**: 장기연재 시 NPC 맥락 손실
- **난이도**: MEDIUM (중요도 기반 정렬 + 동적 한도)

#### C-07. 수치 팩트(가격, 거리, 병력) 자동 추출 미구현
- **TF**: TF-5 (Domain)
- **파일**: `modules/core/fact_ledger.py:247` (update_number 정의만, 호출 0건)
- **내용**: `update_number()` 메서드가 존재하지만 파이프라인에서 **한 번도 호출되지 않음**. 5화에서 금 1만냥 → 7화에서 금 100만냥이 되어도 자동 감지 불가. 투자 장르에서 특히 위험.
- **영향**: 수치 연속성 오류 전면 미감지
- **난이도**: MEDIUM (LLM 기반 수치 추출 + 이상치 감지)

#### C-08. 주제(Theme) 추적 시스템 부재
- **TF**: TF-5 (Domain)
- **파일**: 전체 modules/ 디렉토리에서 "thematic", "theme_track", "주제 추적" 0건
- **내용**: 1~10화 "권력의 대가" → 11~20화 "우정이 최고" 로 주제 표류해도 감지 불가. 장기연재에서 주제 일관성은 작품 완성도의 핵심.
- **영향**: 볼륨 단위 주제 표류 미감지
- **난이도**: HIGH (새 시스템 설계 필요)

### 1-C. DB/트랜잭션 안전성 (2건)

#### C-09. Stage2 Finalizer DB 실패 시 암묵적 트랜잭션 미롤백
- **TF**: TF-2 (Data Flow) + TF-4 (Architecture)
- **파일**: `modules/core/stage2_finalizer.py:310-334`, `main_a.py:301-316`
- **내용**: `save_v20_anchor` INSERT → `safe_commit_async` 실패 시, except 블록에서 `all_refined_arcs.pop()`은 하지만 **DB 롤백 미실행**. `asyncio.to_thread` 래퍼 자체 실패 시 `_safe_commit` 내부 롤백도 미동작. 다음 성공 커밋 시 실패한 아크 데이터가 함께 커밋될 수 있음.
- **영향**: 실패 아크가 DB에 잔류하는 데이터 손상 위험
- **난이도**: MEDIUM (explicit BEGIN/ROLLBACK 추가)

#### C-10. Stage4 원고 저장과 WorldState/FactLedger 갱신 비원자적
- **TF**: TF-2 (Data Flow)
- **파일**: `modules/core/stage4_post_processor.py:38-55, 401-451`
- **내용**: 원고 commit 성공 → WorldState/FactLedger save 실패 시, 원고는 저장되었으나 세계 상태는 갱신 안 됨. 다음 실행 시 DB에서 stale 상태 로드. 의도적 비차단이지만 **갭 복구 메커니즘 부재**.
- **영향**: 원고-세계상태 간 일관성 손상 (좁은 윈도우)
- **난이도**: MEDIUM (WAL 모드 + 갭 감지)

### 1-D. LLM 상호작용 (2건)

#### C-11. JSON 평탄화 엔진의 형제 dict 키 충돌
- **TF**: TF-1 (LLM)
- **파일**: `modules/domain/agents/base_agent.py:922-968`
- **내용**: `_extract_json_robust()`의 `process_node()`가 중첩 dict의 **내부 키를 최상위로 승격**. `state_updates.summary`와 `feedback.summary`가 동시 존재 시 후자가 전자를 덮어씀. `_RECURSE_KEYS` 화이트리스트(`actual_truth`, `ProjectData`, `MasterBible`)만 재귀 — 일반 키는 평탄화.
- **영향**: Director 앙상블 응답에서 5개 중첩 객체 간 키 충돌 시 데이터 손상
- **난이도**: MEDIUM (_RECURSE_KEYS 확장 또는 평탄화 비활성 옵션)

#### C-12. CatharsisTimer 순수 키워드 카운팅 — 의미 맥락 무시
- **TF**: TF-5 (Domain)
- **파일**: `modules/validation/catharsis_timer.py:122-160`
- **내용**: "복수"(revenge) → 항상 +2.0 카타르시스. "복수를 포기했다"(frustrating)와 "복수를 완수했다"(satisfying) 동일 점수. 한국 웹소설에서 맥락이 만족감을 결정하나, 키워드만 카운팅.
- **영향**: 독자 만족도 측정 정확도 저하
- **난이도**: HIGH (LLM 기반 감성 분석 또는 패턴 개선)

### 1-E. 아이템 연속성 (1건)

#### C-13. 아이템 매칭 exact-only — 한국어 별칭 미인식
- **TF**: TF-5 (Domain)
- **파일**: `modules/domain/agents/continuity_inspector.py`
- **내용**: `_is_same_item()`이 정확 문자열 매칭만 사용. "천잠사의" = "비단 갑옷" = "갑옷"을 동일 아이템으로 인식 못함. 오탐(동일 아이템을 새 아이템으로 판단)과 미탐(별칭 사용 시 연속성 오류 미감지) 동시 발생.
- **영향**: 아이템 연속성 검사 정확도 저하
- **난이도**: HIGH (임베딩 기반 유사도 또는 별칭 레지스트리)

### 1-F. 개별 NPC 관계 추적 (1건)

#### C-14. 관계 추적이 집단 키워드 8개만 — 개별 NPC 미검증
- **TF**: TF-5 (Domain)
- **파일**: `modules/domain/agents/continuity_tracker.py:151-196`
- **내용**: `_check_relationship_with_tracker()`가 "사병", "무사들", "병사들" 등 8개 집단 키워드만 검증. "소검마"가 적→아군 전환 같은 **개별 NPC 관계 변화는 미검증**. NPC 레지스트리에 관계 데이터가 있으나 연속성 검사에 연결 안 됨.
- **영향**: 가장 극적으로 중요한 개별 관계 전환이 검증 사각지대
- **난이도**: MEDIUM (NPC 레지스트리 → ContinuityTracker 배선)

---

## 2. IMPORTANT Findings (25건)

### 2-A. 검증 파이프라인 (7건)

#### I-01. 적응형 임계값 캐스케이드 — 품질 점진적 하락
- **파일**: `validation_orchestrator.py:1210-1275`
- **내용**: 5연속 통과 시 -2점, 10연속 시 -3점, 최소 60. 낮은 임계값 → 더 많은 통과 → 더 낮은 임계값 자기강화 루프. 50화+ 연재 시 임계값이 60까지 하락 가능.

#### I-02. 성격 모순 감지 높은 오탐률
- **파일**: `continuity_validator.py:726-866`
- **내용**: NPC 이름 + 모순 키워드 150자 이내 근접 검색. "냉혹한 NPC 옆에서 다른 캐릭터가 울어도" 오탐. 캐릭터 성장에 의한 자연스러운 변화도 오탐. (결과가 WARNING이라 영향은 피드백 노이즈 수준)

#### I-03. Dead NPC 필드명 불일치 가능성 (deceased vs status)
- **파일**: `blocking_validator_entity_checks.py:63`, CLAUDE.md
- **내용**: CLAUDE.md는 `deceased=True`, 코드는 `status == "dead"` 검사. NPC 레지스트리와 백과사전이 다른 필드를 사용하면 사망 NPC 감지 실패.

#### I-04. ConsistencyValidator 6-8번 체크 사실상 미작동
- **파일**: `consistency_validator.py:46-73, 171`
- **내용**: `check_authority_delegation`, `check_unresolved_conflict`, `check_villain_response`에 필요한 `authority_context`, `karma_matrix`, `villain_context`가 대부분 미제공. 고급 서사 검증이 사실상 비활성.

#### I-05. Self-Consistency 투표 범위 70-85만 — 경계 리스크
- **파일**: `validation_orchestrator.py:544-618`
- **내용**: 69점(단일 투표 REJECT)과 70점(3회 투표 검증) 사이 1점 차이가 검증 방식을 결정. LLM 점수 분산 고려 시 경계값 부근 오판 위험.

#### I-06. 프로덕션 임계값 65 vs 문서화된 70 불일치
- **파일**: `director_auditor.py:225`, `validation.yaml:31`, `scoring_validator.py:26`
- **내용**: Director가 ValidationOrchestrator를 `scoring_threshold: 65`로 초기화. YAML은 70. `CONDITIONAL_PASS`가 "PASS"로 매핑되어 **실효 임계값 65**. 문서와 5점 괴리.

#### I-07. 물리법칙 검사 3개 중복
- **파일**: `pre_llm_validator.py:267-294`, `continuity_validator.py:380-517`, `blocking_validator_consistency_checks.py:28-135`
- **내용**: Pre-LLM(현재 에피소드 내), Continuity(에피소드 간), Blocking(HUD 태그 기반) 3곳에서 부상-행동 모순 검사. Pre-LLM 결과는 C-01에 의해 무효 → 실질 2곳 중복.

### 2-B. LLM 상호작용 (5건)

#### I-08. 자기비평 우회 — 표면 루브릭 ≥3.5 시 LLM 비평 스킵
- **파일**: `chief_writer_quality.py:354-446, 91-95`
- **내용**: 감정어 밀도, 문장 시작 다양성, 대화 비율, 감각어 4개 휴리스틱으로 4.0 만점 → 3.5 이상이면 LLM 자기비평 전체 스킵. 사망 NPC 활동, 블루프린트 위반, 논리 오류 등 **구조적 결함은 루브릭으로 감지 불가**.

#### I-09. 원고 수정 프롬프트 8,000자 절단
- **파일**: `chief_writer_quality.py:317-352`
- **내용**: `manuscript[:8000]`만 수정 프롬프트에 전달. 8,000~15,000자 원고의 후반부 이슈를 `fix_instructions`에 기술하되 **실제 텍스트 미제공**. 수정 결과가 전체를 교체하므로 **후반부 소실**.

#### I-10. Director 연속성 카테고리 이진 절벽 (40점 or 0점)
- **파일**: `config/prompts/director.yaml:70, 87-93`
- **내용**: CRITICAL 모순 1건 → 해당 후보 0점. NPC 이름 띄어쓰기("한미증권" vs "한미 증권")와 사망 캐릭터 부활이 동일 페널티. 40점 범위 내 비례적 감점 가이드 부재.

#### I-11. 수정 작업 temperature 0.5 — 보수적 작업에 부적절
- **파일**: 다수
- **내용**: `_fix_manuscript_issues` temp=0.5. 특정 이슈 수정은 0.1-0.2가 적절. Self-Consistency 추가 투표 0.05 간격은 다양성 확보에 불충분.

#### I-12. `_auto_sanitize_injuries()` — LLM 부상/에너지 판단 덮어쓰기
- **파일**: `four_phase_arc_generator.py:717-754`
- **내용**: 매 아크 종료 시 `injuries = "없음"`, `internal_energy = 100` 강제. LLM의 부상 모델링이 장식적 — 다음 아크에 영구 영향 없음. 프로젝트 원칙 #1("판단은 LLM이") 위반.

### 2-C. 데이터 흐름 (4건)

#### I-13. WorldState를 매 에피소드마다 아크 단위 state_changes로 갱신
- **파일**: `stage4_post_processor.py:401-451`
- **내용**: 아크 3화에서 NPC 사망해도, 1화 처리 시점에 이미 사망 기록. `last_updated_ep`가 실제보다 이른 에피소드 번호. 시간적 불일치.

#### I-14. DI Context + App 캐시 이중 쓰기 불일치
- **파일**: `stage2_context.py:212-235`, `prompt_builder.py:530-535`
- **내용**: `PromptBuilder`가 `app._cumulative_state_cache`에 직접 쓰기 — `Stage2Context`의 `sync_cache_key_to_app` 콜백 우회. PromptBuilder 실행 후 Stage2가 ctx에서 stale 데이터 사용 가능.

#### I-15. `_item_timeline_cache` 순방향 진행 시 미무효화
- **파일**: `prompt_builder.py:44`, `db_manager.py:614`
- **내용**: 에피소드 N 처리 중 설정된 캐시가 같은 에피소드 재시도 시 stale. 무효화는 rewind/rollback에서만 발생. (순차 처리에서 위험 낮음)

#### I-16. `main_a.py`가 서브객체 private 캐시 직접 조작
- **파일**: `main_a.py:2671, 2684, 2700-2706`
- **내용**: `self._prompt_builder._item_timeline_cache = {}`, `Director._caching.manuscript_cache_name` 등 직접 접근. 캡슐화 위반 — `invalidate_cache()` 공개 메서드 필요.

### 2-D. 아키텍처 (4건)

#### I-17. 서브모듈 순환 import (lazy import으로 은폐)
- **파일**: `stage4_interview_round.py:25`, `stage4_context_builder.py:553`
- **내용**: 자식→부모 lazy import (`from stage4_orchestrator import _PATCH_REWRITE_THRESHOLD`). 모듈 레벨로 이동 시 `ImportError`. 공유 타입 모듈 필요.

#### I-18. `_quota_exhausted_models` 클래스 변수 무잠금 경쟁
- **파일**: `base_agent.py:136, 277, 452`
- **내용**: 3 스레드(앙상블) 동시 접근. CPython GIL로 크래시 없으나, 한 스레드가 429 마킹한 모델을 다른 스레드가 즉시 사용 → 불필요한 API 호출 낭비.

#### I-19. `FantasyHUD` 폴백 후보 목록 누락
- **파일**: `modules/core/constants.py:391-401`
- **내용**: `get_protagonist_name` 하드코딩 후보에 `FantasyHUD` 누락. V66 판타지 독립 후 동기화 안 됨. genre 파라미터 없이 호출 시 판타지 프로젝트 주인공명 탐색 실패.

#### I-20. `_context_caches` 에빅션 TOCTOU 경쟁
- **파일**: `base_agent.py:1076-1088`
- **내용**: `RuntimeError` catch 후 동일 로직 재시도. 동시 수정 시 에빅션이 dict 크기를 줄이지 못할 수 있음.

### 2-E. 도메인 로직 (5건)

#### I-21. 투자 장르 수익률 검증 시간 무인식
- **파일**: `investment_guard.py` (637줄)
- **내용**: 암호화폐 수익률 -90%~+50000% 정적 범위. 단일 에피소드 50000% 달성도 통과. 시장 사이클, 시간 경과 고려 없음.

#### I-22. 파워 스케일링 키워드 휴리스틱 고정 델타
- **파일**: `continuity_tracker.py:206-224`
- **내용**: "각성" +25, "돌파" +20 고정. "과거 각성을 회상" vs "지금 각성" 구분 불가. 복수 키워드 시 `max()` — 각성+돌파 동시 시 25만 반영(45 아님).

#### I-23. 만족도 태깅이 다음 블루프린트 기획에 미반영
- **파일**: `state_extractor.py:38-55`
- **내용**: 6종 만족도 태그(성취/성장/전투/이행/일상/좌절) 추출 후 저장만. 10화 좌절 에피소드 후 11화 블루프린트가 카타르시스 편향되어야 하나 **피드백 루프 부재**.

#### I-24. 긴장 곡선 관리 시스템 부재
- **파일**: 없음
- **내용**: CatharsisTimer가 이진(만족/좌절)만 제공. "상승 긴장 → 위기 → 카타르시스 → 소강 → 새 긴장" 아크 패턴 계획/강제 불가.

#### I-25. 캐릭터 보이스 시스템 ChiefWriter 전용 컨텍스트에 미연결
- **파일**: `character_voice.py`, `chief_writer_context.py`
- **내용**: `CharacterVoiceTracker`/`Profiler`가 Stage4 오케스트레이터와 PromptBuilder에는 주입되나, **`chief_writer_context.py`의 전용 빌더에는 미연결**. ChiefWriter가 전용 경로로 원고 작성 시 보이스 가이드 미수신.

---

## 3. INSIGHT Findings (16건)

### 3-A. 코드 품질 (5건)

#### S-01. 프롬프트 템플릿 Python/YAML 이중 유지
- **파일**: `chief_writer_prompts.py:12-56`, `config/prompts/chief_writer.yaml`
- 4개 상수 양쪽 유지. YAML 우선 로드 후 Python 폴백. 동기화 누락 시 한쪽만 업데이트.

#### S-02. `max_output_tokens = 8192` 하드코딩
- **파일**: `base_agent.py:297`
- 한국어 토큰화로 10,000자 원고 초과 가능 → 빈번한 continuation(MAX_CONTINUATIONS=5). 짧은 감사 응답에는 낭비.

#### S-03. `_escape_braces()` 패치 모드 계약 취약
- **파일**: `four_phase_arc_generator.py:479-485`
- YAML 템플릿 작성자가 이 특정 템플릿이 `.format()` 사용을 인지해야 함. 다른 템플릿은 직접 삽입.

#### S-04. `sync_cache_key_to_app` 람다 참조 순환
- **파일**: `stage2_context.py:232-235`
- `app → _stage2_orch → _ctx → lambda → app` 순환. GC 처리되나 대규모 중간 상태의 GC 지연.

#### S-05. 30+ 파일의 `except Exception: pass` PerfTimer 래핑
- PerfTimer API가 예외를 발생시키지 않도록 설계되어야 함. 30+ 호출 지점의 try/except은 노이즈.

### 3-B. 검증 (4건)

#### S-06. POV 검사 "시우" 하드코딩
- **파일**: `pre_llm_validator.py:428-462`
- 3인칭 감지 패턴에 "시우는|시우가" 하드코딩. 다른 주인공명에서 3인칭 감지 불완전.

#### S-07. 페이싱 검증 부재
- 과도한 설명, 액션 과잉, 스토리 압축, 스톨링 감지 시스템 없음.

#### S-08. 캐시 키 리셋 `= 0` (센티넬 아님)
- **파일**: `stage2_finalizer.py:337-338`
- `cache_key = 0`이 유효한 `arc_count`와 일치 가능. `-1` 센티넬이 명확.

#### S-09. Stage3 콜드스타트 전체 리빌드 (설계 의도)
- **파일**: `stage3_orchestrator.py:175-196`
- Stage2 미실행 시 StateTracker 전체 재구축. 17개 extract × 아크 수. 순수 Python이라 빠르지만 50+ 아크 시 부하.

### 3-C. 도메인 (4건)

#### S-10. 무협 금기어 목록 비유적 사용 미구분
- "DNA에 새겨진 본능" (한국어 문학 관용구) 같은 비유적 현대어 사용도 차단. 단순 `term in manuscript` 매칭.

#### S-11. 요리 장르 가드 미문서화
- **파일**: `cooking_guard.py`
- CLAUDE.md에 4종만 기재, 실제 10종 존재. 확장 장르 6개 문서 누락.

#### S-12. God Object 잔존 — main_a.py 87 메서드 / 2,995줄
- 캐시 관리, 서사 요약 생성, 에이전트 초기화 추출 가능.

### 3-D. 아키텍처 (3건)

#### S-13. Stage4Context 8개 Conditional Intelligence 슬롯 → 1개 Composite 가능
- **파일**: `stage4_context.py:38-47`
- 8개 nullable 슬롯을 `IntelligenceModules` 1개로 통합 시 7 슬롯 절감.

#### S-14. DI Context에 뮤터블 런타임 상태 혼재
- **파일**: `stage2_context.py` (`cumulative_state_cache`, `cumulative_state_cache_key`)
- DI Context는 불변 의존성용. 런타임 상태는 별도 `RuntimeState` 객체가 적절.

#### S-15. 클리프행어 강도 측정 미구현
- **파일**: `blocking_validator_scene_checks.py:231-369`
- 30+ 패턴 중 1개만 매칭되면 "있음". 약한 클리프행어와 강한 클리프행어 구분 불가.

#### S-16. Fantasy Guard 금기어 커버리지 부족
- **파일**: `fantasy_guard.py` (334줄 vs WuxiaGuard 662줄)
- 현대 슬랭 필터, 아카데미 계층 규칙, 회귀물 미래지식 오염 방지 등 미구현.

---

## 4. 도메인별 교차 참조 매트릭스

| 도메인 | CRITICAL | IMPORTANT | INSIGHT | 핵심 파일 |
|--------|----------|-----------|---------|-----------|
| 검증 파이프라인 | C-01~04 | I-01~07 | S-06~08 | `validation_orchestrator.py`, `scoring_validator.py`, `pre_llm_validator.py` |
| 장기연재 | C-05~08 | I-13, I-23~24 | S-09 | `fact_ledger.py`, `world_state.py`, `catharsis_timer.py` |
| DB/트랜잭션 | C-09~10 | I-15~16 | S-08 | `stage2_finalizer.py`, `stage4_post_processor.py`, `db_manager.py` |
| LLM 상호작용 | C-11~12 | I-08~12 | S-01~03 | `base_agent.py`, `chief_writer_quality.py`, `director.yaml` |
| 아키텍처 | — | I-14, I-17~20 | S-04~05, S-12~14 | `stage2_context.py`, `constants.py`, `main_a.py` |
| 도메인/서사 | C-13~14 | I-21~22, I-25 | S-10~11, S-15~16 | `continuity_tracker.py`, `continuity_inspector.py`, guards |

---

## 5. 권장 우선순위 (ROI 기반)

### Tier 1 — 즉시 실행 ✅ (사용자 결정 2026-02-20)
1. **C-01** Pre-LLM score_deduction → **1점 캡**: `score_deduction > 0`이면 최종 점수에서 정확히 1점만 차감. 0이면 미적용. (대원칙 #1 존중: Python 판단 최소화)
2. **C-02** validate_v59 장르 가중치 → **1점 캡**: v59 호출하되 기존 validate 대비 차이 `±1`점 클램핑. (대원칙 #1 존중: Python 가중치 영향력 제한)
3. **C-04** RetrospectiveValidator → **활성화 + LLM 연결**: 기본값 `True` 변경. 순수 Python이므로 violations를 SCORING LLM 컨텍스트에 전달하여 LLM이 최종 판단.
4. **C-05** FactLedger → **`MAX_HISTORY_PER_ENTITY = 100`**: Gemini 컨텍스트 방대, DB도 방대. 상수로 가둘 필요 없음.
5. **I-06** 프로덕션 임계값 → **65→70 일치**: `director_auditor.py:225`를 70으로 변경.
6. **I-19** FantasyHUD → **폴백 리스트에 추가**: V66 동기화 누락 버그 수정.

### Tier 2 — 단기 실행 ✅ (2026-02-20 구현 완료)
7. **C-09** ✅ Stage2 Finalizer DB 실패 시 `conn.rollback()` 추가 — 반쪽 커밋 방지
8. **C-06** ✅ WorldState NPC 요약 중요도 기반 정렬 — 동행자>관계>역할 순 truncation
9. **C-14** ✅ ContinuityTracker 개별 NPC 관계 검증 추가 — `npc_states` dict에서 이름 추출
10. **I-08** ✅ 루브릭 ≥3.5 스킵 전 구조적 적신호 확인 — medium+ 이슈 있으면 Self-Critique 진행
11. **I-09** ✅ 원고 수정 프롬프트 `manuscript[:8000]` → 전문 전달
12. **I-14** 스킵 — `arc_count` key check로 stale cache 이미 방지됨. False positive.

### Tier 3 — 중기 실행 ✅ (2026-02-20 구현 완료)
13. **C-07** ✅ 수치 팩트 자동 추출 — `_extract_numerical_facts()` 헬퍼 추가, 기존 `update_number()` 배선
14. **C-10** ✅ WorldState/원고 원자적 저장 — `db.transaction()`으로 WS+FL 묶기, 원고는 밖 유지
15. **C-11** ✅ JSON 평탄화 엔진 안전화 — 500KB 크기 가드, visit_count 상한, 숫자/불리언 regex
16. **I-23** ✅ 만족도 → Blueprint 피드백 — `_build_reader_feedback_context()` advisory 주입
17. **I-24** ✅ 호흡 분석 DB 저장 + Blueprint 피드백 — `episode_pacing` 테이블, Stage4 PASS 후 저장

### Tier 4 — 장기 (새 시스템)
18. **C-08** 주제 추적 시스템
19. **C-12** CatharsisTimer LLM 기반 감성 분석
20. **C-13** 아이템 별칭 레지스트리/임베딩 매칭

---

## 6. 오탐/중복 제거 기록

### 제거된 오탐 (1건)
- ~~TF-3.F1 "LLM max score 미검증"~~ → 코드 확인 결과 Python 정의 max로 클램핑, LLM 반환 max 무시. 정상 동작.

### 병합된 중복 (13건)
- TF-2.F2 + TF-2.F8 → **C-09** (DB 트랜잭션 안전성)
- TF-4.F2 + TF-2.F3 → **I-14** (캐시 이중 쓰기)
- TF-3.F4 + TF-3.F2 → **C-01** (Pre-LLM 미적용의 결과)
- TF-1.F2 "프롬프트 인젝션" → **제거** (단일 사용자 폐쇄 시스템, 실질 위험 낮음)
- TF-1.F3 "컨텍스트 400K+" → **C-06, S-02** 분리 (NPC 절단은 별개 이슈)
- TF-1.F7 "인라인 프롬프트" → **S-01** 병합
- TF-4.F5 "뮤터블 상태 on DI" → **S-14**
- TF-4.F7 "except pass 30파일" → **S-05**
- TF-4.F9 "God Object 잔존" → **S-12**
- TF-4.F10 "8 intelligence 슬롯" → **S-13**
- TF-4.F11 "람다 참조 순환" → **S-04**
- TF-5 "Fantasy guard 커버리지" → C→S 재분류 (**S-16**, 기존 guard로 동작은 함)
- TF-5 "상태 델타 manuscripts only" → **I-22** 연관 (별도 유지)

---

## 7. 부록 — TF 에이전트별 원본 요약

| TF | 범위 | 원본 건수 | 병합 후 |
|----|------|-----------|---------|
| TF-1 (LLM 상호작용) | base_agent, chief_writer, director, four_phase | 12 | 8 |
| TF-2 (데이터 흐름) | stage2/3/4 context, db_manager, prompt_builder | 8 | 5 |
| TF-3 (검증 파이프라인) | validation 전체, orchestrator | 14 | 11 |
| TF-4 (아키텍처) | DI context, constants, base_agent, main_a | 11 | 7 |
| TF-5 (도메인/서사) | guards, trackers, world_state, fact_ledger | 23 | 19 |
| **합계** | | **68** | **55** (중복 병합 12 + 오탐 1) |
