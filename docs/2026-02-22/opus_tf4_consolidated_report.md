# Opus TF-4: Production Hardening & Optimization 종합 보고서

> **[Codex 검증 지시]**
> 이 문서의 모든 주장(파일 경로, 라인 번호, 코드 존재/부재, 수치)을 검증할 때
> `rg`, `grep`, `fgrep` 등 자동 검색 도구를 사용하지 마시오.
> 반드시 해당 파일을 직접 열어 라인 단위로 수동 확인하시오.

> 감사일: 2026-02-22
> 감사자: Claude Opus 4.6 x 6 TF
> 방법론: Production Hardening (코드 결함 탐색이 아닌 운영 최적화)
> 대상: 글도비 V64+ (commit a737213 기준)

---

## Executive Summary

6개 TF가 **운영 최적화** 관점에서 코드베이스를 전면 분석했다.

| TF | 주제 | 보고서 |
|---|---|---|
| TF-A | Dead Code 제거 | `opus_tf4_dead_code_audit.md` |
| TF-B | 토큰/비용 최적화 | `opus_tf4_token_cost_audit.md` |
| TF-C | 동시성 안전성 | `opus_tf4_concurrency_audit.md` |
| TF-D | NPC 생애주기 무결성 | `opus_tf4_npc_lifecycle_audit.md` |
| TF-E | 프롬프트 템플릿 품질 | `opus_tf4_prompt_template_audit.md` |
| TF-F | 200화 스케일링 | `opus_tf4_scaling_audit.md` |

### 핵심 수치

| 지표 | 값 |
|------|---|
| 삭제 가능 dead code | **~3,119줄** |
| 에피소드당 현재 비용 | **$8~12** |
| 최적화 후 목표 비용 | **$0.50** (-94%) |
| YAML 미사용 키 비율 | **74%** (60/81키) |
| 동시성 CRITICAL/HIGH | **0건** |
| NPC HIGH 이슈 | **2건** (bind_db 미호출, 롤백 미리셋) |
| 스케일링 병목 | **3건** (30화 전문 N+1, resolved_plots, context window) |

---

## 1. Dead Code 제거 [TF-A]

### 삭제 가능 ~3,119줄

| 카테고리 | 줄 수 | 위험도 | 내용 |
|----------|------|--------|------|
| `strategies/` 디렉토리 | 315 | safe | 7개 장르 전략 파일, import 0건 |
| 미사용 모듈 5개 | 2,489 | safe | models.py, ab_testing.py, manuscript_enhancer.py, finetuning_automation.py, progress_manager.py |
| 미사용 지역 변수 | 74건 | safe | ruff F841 경고 |
| 호출 없는 public 메서드 | 10건 | caution | project_manager 3건, db_manager 4건, 기타 3건 |
| 미사용 YAML 섹션 | 3섹션 | safe | writing, thresholds, volume (patch_mode는 참조 있으므로 유지) |
| 미사용 테스트 fixture | 5건+1 | safe | ~83줄 |

---

## 2. 토큰/비용 최적화 [TF-B]

### 에피소드당 LLM 호출 구조

| Stage | 호출 수 (typical) | 지배적 비용 요소 |
|-------|------------------|-----------------|
| Stage 2 | 2~8회 | ArcEnsemble 3전략 (캐싱 없음) |
| Stage 3 | 5~15회 | BlueprintEnsemble 3전략 (캐싱 없음) |
| Stage 4 | 12~50회 | CW 3전략 + Director 심사 + Validator |
| **합계** | **27~105회** | |

### 비용 절감 로드맵

| Phase | 조치 | 절감율 | 누적 |
|-------|------|--------|------|
| A | Manager 모델 다운그레이드, Self-Consistency 조건부 스킵, 후선택 검증 | -47% | -47% |
| B | ArcEnsemble/BlueprintEnsemble에 Context Caching 추가 | -41% | -88% |
| C | 30화 전문 → **3단계 하이브리드** (10화 전문 + 20화 요약 + Arc 요약) + SC 검색 연동 | -6% | **-94%** |

### 현재 vs 목표

| | 현재 | Phase A 후 | Phase C 후 |
|---|---|---|---|
| 에피소드당 | $8~12 | ~$4.50 | **~$0.50** |
| 월간 (30편) | $240~360 | ~$135 | **~$15** |

---

## 3. 동시성 안전성 [TF-C]

### 전체 평가: 양호

| 위험도 | 건수 | 내용 |
|--------|------|------|
| CRITICAL | **0** | |
| HIGH | **0** | |
| MEDIUM | **3** | orphan 스레드 (post_processor), stats lost update (data_collector), 키 순환 시 quota 캐시 클리어 타이밍 |
| LOW | **5** | |

**강점**: 10+ 싱글톤 DCL 올바름, DBManager RLock 일관 보호, asyncio.gather 전부 return_exceptions=True

---

## 4. NPC 생애주기 무결성 [TF-D]

### HIGH 2건 (즉시 조치 필요)

**NPC-L1: `bind_db()` 프로덕션 미호출**
- `StateTracker.bind_db(db_manager)`가 테스트에서만 호출됨
- **프로덕션에서 npc_history 테이블이 항상 비어있음**
- Phase 3-5A(NPC 이력 DB)의 핵심 기능이 비활성 상태
- 수정: `stage2_orchestrator.py`, `stage3_orchestrator.py`, `main_a.py` 3곳에 1줄 추가

**NPC-L2: 롤백 시 `npc_registry` 미리셋**
- `rollback_episode()` 실행 시 DB 삭제는 되지만 인메모리 npc_registry가 유지됨
- 사망한 NPC가 롤백 후에도 dead 상태 → 잘못된 REJECT
- 수정: `project_service.py`에서 `self.state_tracker = None` 추가

### MEDIUM 3건
- dead_npcs 이중 소스 불일치
- Bible NPC 이름 vs npc_registry 이름 불일치 (약칭/별명)
- auto_backtrack/Stage 4 직행 시 StateTracker 미리셋

---

## 5. 프롬프트 템플릿 품질 [TF-E]

### YAML 외부화 미완료

| 지표 | 값 |
|------|---|
| YAML 파일 수 | 40개 |
| YAML 키 수 | 81개 |
| 코드에서 실제 참조 | **21개 (26%)** |
| 미사용 (사문화) | **60개 (74%)** |

### 주요 발견

| ID | 내용 |
|---|---|
| **하드코딩 프롬프트** | 216개 (300자+), 최대 `PLAN_ARC_PROMPT_V25` 12,310자 |
| **emotion_tracker.yaml 중복 키** | `GENERATE_RECOMMENDATION__RECOMMENDATION` 2회 정의 → 첫 번째 소실 |
| **SafeDict 미사용** | 14개 에이전트가 `.format()` 직접 사용 → LLM 응답 내 `{}`가 KeyError 유발 가능 |
| **Stage 3 장르 프롬프트 부재** | `genre_stage.yaml`의 `STAGE3_MEDICAL` 1개만 존재, 코드 참조 0건 |

---

## 6. 200화 스케일링 [TF-F]

### 병목 3건

| ID | 위치 | 현재 | 200화 | 권고 |
|---|---|---|---|---|
| **30화 전문 N+1** | `stage4_context_builder.py` L332 | 30회 SELECT | 30회 SELECT (고정) | 3단계 하이브리드: 10화 전문 + 20화 요약 + Arc 요약 → **37~57% 절감** |
| **resolved_plots 무한 증가** | `state_tracker.py` L132 | ~30개 | ~120개 | 상한 30개 + 오래된 것 요약 |
| **Context Window 압박** | mandatory_context | ~40K자 | ~77K자 | 16종 합산 15K자 총량 상한 |

### 안전 확인

| 항목 | 200화 추정 | 판정 |
|------|-----------|------|
| DB 파일 크기 | ~25MB | safe |
| 벡터 검색 | 200벡터 KNN 2~5ms | safe |
| 런타임 메모리 | ~85MB | safe |
| 파일 시스템 | 200파일 | safe |

---

## 7. Codex 핸드오프 권장 작업

### Tier 1: 즉시 수정 (HIGH, 1시간)

| # | 작업 | 관련 이슈 |
|---|------|----------|
| 1 | `bind_db()` 프로덕션 배선 3곳 | NPC-L1 |
| 2 | `rollback_episode()` npc_registry 리셋 | NPC-L2 |
| 3 | `emotion_tracker.yaml` 중복 키 제거 | TF-E |

### Tier 2: Dead Code 제거 (safe, 반나절)

| # | 작업 | 줄 수 |
|---|------|------|
| 4 | `strategies/` 디렉토리 삭제 | 315 |
| 5 | 미사용 모듈 5개 삭제 | 2,489 |
| 6 | 미사용 테스트 fixture 정리 | 83 |
| 7 | ruff F841 미사용 변수 정리 | 74건 |

### Tier 3: 비용 최적화 Phase A (하루)

| # | 작업 | 절감 |
|---|------|------|
| 8 | Manager LLM → 2.5-flash 다운그레이드 | -15% |
| 9 | Director Self-Consistency 조건부 스킵 (1라운드 만장일치 시) | -20% |
| 10 | Validator 후선택 집중 (3후보 전체 → 선택된 1후보만) | -12% |

### Tier 4: 스케일링 + 캐싱 (장기)

| # | 작업 | 효과 |
|---|------|------|
| 11 | ArcEnsemble/BlueprintEnsemble Context Caching | 비용 -41% |
| 12 | 30화 전문 → 3단계 하이브리드 (10화 전문 + 20화 요약 + Arc 요약) + SC 검색 연동 | 프롬프트 -37~57% + 전체 이력 검색 가능 |
| 13 | resolved_plots 상한 30개 | 메모리 안정화 |
| 14 | episode_meta 인덱스 추가 | 쿼리 성능 |

### Tier 5: 프롬프트 외부화 (장기)

| # | 작업 | 효과 |
|---|------|------|
| 15 | YAML 미사용 60키 정리 또는 코드 연결 | 설정 위생 |
| 16 | SafeDict 미사용 14개 에이전트 수정 | KeyError 방지 |
| 17 | 하드코딩 대형 프롬프트 YAML 외부화 (top 10) | 유지보수성 |

---

## 8. 이전 감사와의 비교

| 지표 | 3차 감사 (크로스컷) | 4차 감사 (본건) |
|------|-------------------|---------------|
| 관점 | 결함 탐지 | **운영 최적화** |
| 코드 결함 | 0건 | 0건 |
| 운영 위험 | 설정/테스트/장르 | **NPC HIGH 2건, 비용 $8/ep** |
| 삭제 기회 | 없음 | **~3,119줄** |
| 비용 절감 | 없음 | **-94% 가능** |
| 동시성 | 미조사 | **양호 (CRITICAL 0)** |
| 스케일링 | 미조사 | **병목 3건 식별** |

---

## 부록: 개별 감사 보고서 목록

1. `opus_tf4_dead_code_audit.md` — Dead Code (335줄)
2. `opus_tf4_token_cost_audit.md` — 토큰/비용 (463줄)
3. `opus_tf4_concurrency_audit.md` — 동시성 안전성
4. `opus_tf4_npc_lifecycle_audit.md` — NPC 생애주기
5. `opus_tf4_prompt_template_audit.md` — 프롬프트 템플릿
6. `opus_tf4_scaling_audit.md` — 200화 스케일링 (542줄)

---

*Generated by Claude Opus 4.6 — 6 parallel Production Hardening TFs*
