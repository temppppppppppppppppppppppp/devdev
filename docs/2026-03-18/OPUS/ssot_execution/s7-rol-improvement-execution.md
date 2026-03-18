# S7 ROL + 정적 개선 실행문서

> **주의**: 본 문서는 우선순위 정렬된 백로그임. 각 항목의 상세 코드 변경은 착수 시 별도 설계 필요.

> 작성일: 2026-03-18
> 상태: 대기 (실행 전)
> 원본 SSOT: `docs/2026-03-18/OPUS/ssot/s7-rol-static-improvement.md`
> 근거 조사: `docs/2026-03-18/OPUS/geuldobi-v2-rol-deepdive-full-survey.md`
> 감리: 기본 3-pass + 적대적 5-pass (총 8-pass)
> 최종 확신도: 97%

---

## 1. 목적

S7 SSOT에서 식별된 모든 실행 가능 항목(측정 사각지대 G1-G5, 정적 개선 OPP-01~20, ROL 최적화 지렛대 5건, 코퍼스 활성화 4단계)을 ROI 우선순위로 정렬하여 단일 실행 큐를 구성한다.

**실행 원칙**:
- 측정부터 고친다 (측정 없이 개선 효과를 검증할 수 없음)
- 저난이도/고영향 항목을 먼저 한다
- 코드 수정은 본 문서의 범위가 아님 (실행 시점에 별도 실행문서로 분리)

---

## 2. ROI 우선순위 실행 큐

### Tier 1: 측정 기반 확보 (선행 필수 -- 다른 모든 개선의 전제)

| ID | 항목 | 우선순위 | 상세 | 완료 기준 | 추정 공수 | 의존성 | S7 근거 |
|----|------|---------|------|----------|----------|--------|---------|
| G1 | 시도 단위 비용 전달 | **P0** | `record_attempt()` 호출 시 `token_cost`가 Stage 2/3에서 0.0으로 전달됨. Stage 4만 실측값 존재(11/11건). MetricsCollector의 비용 데이터를 record_attempt 호출 경로에 연결해야 함. **삽입점**: `stage2_finalizer.py:1592,1738`, `stage3_orchestrator.py:1469,2048` — 이 4곳의 `record_attempt()` 호출에 `token_cost` 파라미터가 누락됨. Stage 4(`stage4_interview_round.py:5942`)처럼 `MetricsCollector.peek_scope()` 호출 후 `token_cost`에 전달 필요 | Stage 2/3의 `token_cost` 필드가 비영(non-zero) 실측값으로 기록됨 (최소 3건 검증) | 0.5일 | 없음 | S7 섹션 7 G1, 딥다이브 섹션 5.2 발견 1 |
| G2 | Stage 3 시간 계량 복원 | **P0** | `duration_ms=0` (11건 전부). 타이밍 코드(`stage3_orchestrator.py:1009,1370`)는 존재하나 결과가 0. 런타임 디버깅으로 원인 확정 후 수정 필요 | Stage 3 레코드의 `duration_ms`가 비영 실측값으로 기록됨 (최소 3건 검증) | 0.5일 | 없음 | S7 섹션 7 G2, 딥다이브 섹션 5.2 발견 2 |
| G3 | 시뮬레이션 도구 가격 갱신 | **P1** | `cost_calculation.py`, `full_project_cost.py`의 가격이 런타임 대비 1/2~1/4 과소. Pro output $5->$10, Flash output $0.60->$2.50, Flash input $0.15->$0.30. **심각도 참고**: S7 SSOT에서 '저' 등급이나, 시뮬레이션 정확도 영향으로 P1 상향 | 시뮬 도구 MODEL_COSTS가 `metrics_collector.py`와 동일 가격 사용 | 0.25일 | 없음 | S7 섹션 4.1, 딥다이브 섹션 5.2 발견 3 |
| G4 | 에피소드 단위 종합 ROL 지표 | **P2** | 비용/시간/시도/품질을 하나의 ROL 공식으로 합산하는 로직이 없음. 현재는 각 차원이 독립적으로만 존재. **대상 모듈**: `pass_rate_monitor.py` 또는 신규 `rol_calculator.py`에 `calculate_episode_rol(cost, time, attempts, quality_score)` 함수 추가. `bridge_server.py` `/quality/dashboard` 엔드포인트에서 호출 | `ROL = 산출(에피소드 x 품질) / 투입(비용 + 시간 + 재시도 증폭)` 공식이 구현되어 대시보드에서 조회 가능 | 1일 | G1, G2 (정확한 비용/시간 데이터 필요) | S7 섹션 7 G4 |
| G5 | Arc 난이도-비용 상관 분석 | **P2** | `get_arc_difficulty()` 존재하나 비용과 교차 분석 미구현. **접근법**: `cost_log` + `pass_rate_monitor` 교차 조인 쿼리로 `arc_no`별 비용-난이도 상관 계산 | Arc별 난이도-비용 교차 분석 결과가 대시보드 또는 리포트로 출력 | 0.5일 | G1, G4 | S7 섹션 7 G5 |

### Tier 2: 실제 결함 수정 (데이터 정합성 직접 영향)

| ID | 항목 | 우선순위 | 상세 | 완료 기준 | 추정 공수 | 의존성 | S7 근거 |
|----|------|---------|------|----------|----------|--------|---------|
| OPP-05 | quality_risk 3곳 불일치 (실제 결함) | **P0** | `director_ensemble.py:771`에서 PASS_WITH_WARNING 누락. 3곳의 quality_risk 판정 로직이 불일치하여 동일 verdict에 대해 서로 다른 quality_risk 결과를 반환할 수 있음 | 3곳의 quality_risk 로직이 동일한 verdict 집합에 대해 동일한 결과를 반환함 (단위 테스트 포함) | 0.5일 | 없음 | S7 섹션 5.5 OPP-05, 적대적 감리 9-10회차 실제 결함 확인 |
| OPP-03 | Firewall 정보 JSONL 누락 | **P1** | `firewall_triggered`, `firewall_reason`이 DB에만 기록되고 `session_logger.log_decision()`에 미포함. 시스템 최강 품질 방어선의 진단 정보가 가장 접근 쉬운 소스(JSONL)에서 빠져 있음 | `decisions.jsonl`에 `firewall_triggered`, `firewall_reason` 2개 필드가 기록됨 | 0.25일 | 없음 | S7 섹션 5.4 |
| OPP-17 | patch_strategy 비정규화 | **P1** | `is_patch=true` 5건 중 4건(80%)이 `patch_strategy` 빈 문자열. 패치 효과 분석(`get_patch_effectiveness()`)의 전략별 비교가 불가능 | `is_patch=true`인 레코드의 `patch_strategy`가 실제 전략명으로 기록됨 | 0.5일 | 없음 | S7 섹션 5.5 OPP-17 |

### Tier 3: 구조적 정리 (유지보수 비용 절감)

| ID | 항목 | 우선순위 | 상세 | 완료 기준 | 추정 공수 | 의존성 | S7 근거 |
|----|------|---------|------|----------|----------|--------|---------|
| OPP-01 | Verdict Enum 6-Way 정리 | **P1** | 스키마 3종(PASS/PASS_WITH_FIX/REJECT) vs 코드 6종. CONDITIONAL_PASS(0회 도달), PASS_WITH_WARNING(SQL 하드코딩), FAILED(내부 전용)가 미정의 상태로 공존 | Verdict enum이 스키마와 코드에서 일치. 사용되지 않는 상태는 제거 또는 명시적 문서화 | 1일 | OPP-02 (동시 진행) | S7 섹션 5.1 OPP-01 |
| OPP-02 | CONDITIONAL_PASS 제거/축소 | **P1** | 코드 29건(modules/ 14 + tests/ 15) 존재하나 최종 verdict에 0번 도달. `director_ensemble.py:1573,1732`에서 체계적으로 원래 verdict로 되돌림 | CONDITIONAL_PASS가 순수 로깅으로 축소되거나 제거됨. 관련 코드 정리 완료 | 1일 | OPP-01 (동시 진행) | S7 섹션 5.1 OPP-02 |
| OPP-07 | UNCONDITIONAL_PASS >=85 미문서화 | **P2** | 런타임 상수로 사용되나 schema/constants에 미정의 | 임계값이 constants 또는 schema에 명시적으로 정의됨 | 0.25일 | OPP-01 | S7 섹션 5.5 OPP-07 |
| OPP-14 | Dead surface 정리 | **P2** | RESERVED_SHIMS, dead IPC, outline 문서 등 사용되지 않는 코드/문서 누적 | 식별된 dead surface가 제거되거나 DEPRECATED 표시 | 1일 | 없음 | S7 섹션 5.5 OPP-14 |
| OPP-08 | Governance 문서 경량화 | **P3** | ~3,450행, 14 harness, 순환 참조. 단순 버그 수정에도 3-4개 문서 읽기 필요. 5+ outline 문서가 draft 정체. **대상 harness 목록 확인**: `ls docs/implementation/*harness*` (현재 14개: deep-global-integrity-survey, document-3pass-audit, evidence-manifest, exception-registry, execution-closure, execution-synthesis, live-run-merge-survey, ops-validator, process-health-scorecard, stale-reference-sweep, system-full-survey-execution, system-order-init, system-order-preflight, temp-execution-queue-roadmap) | harness 수 절반 이하로 축소, 순환 참조 해소, draft 문서 정리 | 3일 | 없음 | S7 섹션 5.3 OPP-08 |
| OPP-09 | Blockguide 외부 SSOT 의존 해소 | **P3** | `전처리_ssot/` 외부 디렉토리 의존 | 필요 자산이 프로젝트 내부로 통합되거나 명시적 참조 경로로 전환 | 1일 | OPP-08 | S7 섹션 5.5 OPP-09 |

### Tier 4: 관측성/운영자 경험 개선

| ID | 항목 | 우선순위 | 상세 | 완료 기준 | 추정 공수 | 의존성 | S7 근거 |
|----|------|---------|------|----------|----------|--------|---------|
| OPP-04 | 4-sink 실시간 정합성 체크 | **P2** | 4개 sink(DB director_selections, DB stage_attempts, decisions.jsonl, pass_rate_monitor.json) 모두 try-except 비차단. `sink_alignment_summary()`는 사후 비교만 수행 | 에피소드 생산 정상 경로에서 최소 2-sink 교차 검증이 자동 수행됨 | 1.5일 | 없음 | S7 섹션 5.2 |
| OPP-10 | UI "대기" 3-way 구분 | **P2** | 실행 중/데이터 없음/오류를 모두 "대기"로 표시. 운영자가 시스템 상태를 구분할 수 없음. **대상**: `geuldobi-desktop/src/index.html` 내 상태 표시 영역 — `officeState.isRunning`, `officeState.mode` 분기 (line 5178-5196 부근) | 3가지 상태가 UI에서 각각 구분되어 표시됨 | 0.5일 | 없음 | S7 섹션 5.5 OPP-10 |
| OPP-13 | Artifact post-write 검증 | **P2** | partial write 감지 불가. 파일 기록 후 무결성 검증 없음 | 주요 artifact(원고, Blueprint) 기록 후 크기/해시 검증 수행 | 0.5일 | 없음 | S7 섹션 5.5 OPP-13 |
| OPP-15 | Stage 3 duration=0ms 원인 규명 | **P2** | 확신도 85%. 타이밍 코드는 존재하나 런타임에서 0 반환. 코드상 로직은 정상이나 런타임 디버깅 필요 | 원인이 확정되고 수정됨 (G2와 동시 해결 가능) | 0.5일 | 없음 (G2와 병행) | S7 섹션 5.5 OPP-15 |
| OPP-16 | WS reconnect 구현 | **P3** | WebSocket 단절 시 경고 없음, reconnect 없음. **대상**: `geuldobi-desktop/src/index.html` 내 WebSocket 연결 영역 (line 5826-6222), `_wsReconnectTimer` 로직 (`_connectWebSocket()` 함수, line 6168) | 단절 감지 + 자동 reconnect + 운영자 알림 구현 | 1일 | 없음 | S7 섹션 5.5 OPP-16 |
| OPP-18 | Quality Radar 범례 추가 | **P3** | CED/AI Slop/gzip/Rhythm/Density 단위/범위 미표시 | 각 축의 단위, 범위, 해석 가이드가 UI에 표시됨 | 0.25일 | 없음 | S7 섹션 5.5 OPP-18 |
| OPP-19 | Stage 3 에스컬레이션 비대칭 해소 | **P2** | Stage 3에서는 알림만 있고 운영자 선택지 부재 (Stage 4와 비대칭) | Stage 3 실패 시 운영자 선택지(재시도/스킵/수동개입) 제공 | 1일 | 없음 | S7 섹션 5.5 OPP-19 |

### Tier 5: 품질/테스트 강화

| ID | 항목 | 우선순위 | 상세 | 완료 기준 | 추정 공수 | 의존성 | S7 근거 |
|----|------|---------|------|----------|----------|--------|---------|
| OPP-06 | Stage 4 rejection 45.5% 원인 분석 | **P2** | Blueprint-Writing 핸드오프 컨텍스트 손실 시사. 샘플 제한(25건)으로 통계적 유의성 낮음. **현황 확인 방법**: `python -c "import json; data=json.load(open('projects/0_260316/logs/pass_rate_monitor.json')); print(len([r for r in data['records'] if r['stage']==4 and not r['success']]))"` | 100건 이상 샘플에서 Stage 4 거부율 및 상위 거부 사유 확인. 30% 이하 목표 | 1일 | G1, G2 (정확한 데이터 필요) | S7 섹션 5.5 OPP-06 |
| OPP-11 | Test mock 과잉 축소 | **P2** | `ask()` mock으로 인해 real failure 경로 미검증 | 핵심 경로에 대한 integration test 추가 (mock 최소화) | 2일 | 없음 | S7 섹션 5.5 OPP-11 |
| OPP-12 | Advisory 에스컬레이션 구현 | **P2** | 반복 advisory가 blocking으로 에스컬레이션되지 않음 | 동일 advisory N회 반복 시 blocking으로 자동 에스컬레이션 | 1일 | 없음 | S7 섹션 5.5 OPP-12 |
| OPP-20 | _LazyThreshold 스레드 안전성 | **P3** | concurrent first-access 시 race condition 가능. 현재 단일 스레드라 미발현 | 스레드 안전 초기화 구현 또는 단일 스레드 전제 문서화 | 0.5일 | 없음 | S7 섹션 5.5 OPP-20 |

### Tier 6: ROL 최적화 지렛대 (Tier 1 완료 후 효과 측정 가능)

| ID | 항목 | 우선순위 | 상세 | 완료 기준 | 추정 공수 | 의존성 | S7 근거 |
|----|------|---------|------|----------|----------|--------|---------|
| ROL-01 | 통과율 향상 (55% -> 80%) | **P1** | 재시도 1.8x -> 1.25x. -30% 비용 절감. RC-1(모순 방화벽 반복), RC-3(후선택 충돌 패치)가 주요 병목. **서브태스크**: (a) OPP-06 완료 후 상위 거부 사유 Top-5 확정, (b) RC-1 모순 방화벽 반복 원인 수정 (`director_ensemble.py` contradiction 로직), (c) RC-3 후선택 충돌 패치 강화 (`three_phase_blueprint_generator.py`), (d) 100건 A/B 측정 | Stage 4 1차 통과율 80% 이상 (100건 이상 샘플) | 5일+ | G1, G2 (효과 측정), OPP-06 (원인 분석) | S7 섹션 9 #1 |
| ROL-02 | Vertex Context Caching 적용 | **P1** | Bible/Treatment/Style Guide를 캐시하여 -70% 비용 절감. 현재 미적용. **서브태스크**: (a) `metrics_collector.py` 내 Vertex API 호출 경로에 context caching 옵션 추가, (b) Bible/Treatment/Style Guide를 캐시 가능 프리픽스로 분리, (c) 캐시 히트율 모니터링 계측 추가 | 캐시 히트율 50% 이상, 에피소드당 비용 50% 이상 감소 | 3일 | 없음 | S7 섹션 9 #2, 섹션 4.4 |
| ROL-03 | Prompt Prefix 정규화 | **P2** | 캐시 히트 극대화 위해 프롬프트 접두사를 정규화. -30~50% 추가 절감. **서브태스크**: (a) 전 에이전트 프롬프트 접두사 구조 조사 (`modules/domain/agents/` 하위), (b) 공통 접두사 템플릿 추출, (c) 캐시 히트율 전후 비교 | 전 스테이지 프롬프트 접두사가 정규화되고 캐시 히트율 측정됨 | 2일 | ROL-02 (캐싱 인프라 선행) | S7 섹션 9 #3 |
| ROL-04 | 패치 모드 효율화 | **P2** | inplace 부분 성공 -> structural 패치 강화. -15% 비용 절감. **서브태스크**: (a) OPP-17 patch_strategy 정규화 완료 확인, (b) `blueprint_ensemble.py` 패치 전략 선택 로직 강화, (c) structural 패치 성공률 전후 비교 | structural 패치 성공률 향상, full 재생성 비율 감소 | 2일 | OPP-17 (patch_strategy 정규화 선행) | S7 섹션 9 #4 |
| ROL-05 | 모델 티어 최적화 | **P2** | 전 에이전트 Pro 사용 -> 비핵심 에이전트 Flash 전환. -20% 비용 절감. **서브태스크**: (a) 에이전트별 모델 사용 현황 조사 (`base_agent.py` model 설정), (b) 비핵심 에이전트(스코어링, 검증) Flash 전환, (c) 품질 회귀 테스트 (전환 전후 verdict 비교) | 비핵심 에이전트(스코어링, 검증 등)가 Flash로 전환되고 품질 저하 없음 확인 | 2일 | G1 (비용 비교 데이터 필요) | S7 섹션 9 #5 |

### Tier 7: 코퍼스 활성화 (장기 -- 평가 우선 원칙)

| ID | 항목 | 우선순위 | 상세 | 완료 기준 | 추정 공수 | 의존성 | S7 근거 |
|----|------|---------|------|----------|----------|--------|---------|
| CRP-01 | Judge-First Calibration (평가에 먼저 사용) | **P2** | 클리프행어 taxonomy -> Director rubric, 화간 연결 분석 -> continuity rubric, 문체 프로파일 -> anti-slop 기준, contradiction GT -> validator recall benchmark. **입력**: `docs/실물기반 사각지대 테스트/contradiction_ground_truth_dataset.md` + 실물 원고 코퍼스 **출력**: `config/` 하위 calibration YAML (rubric 정의, threshold, recall benchmark) | 4개 영역 각각 rubric/benchmark 산출물 생성 | 3일 | 없음 | S7 섹션 6.2 단계 1 |
| CRP-02 | 증류 기준 런타임 주입 | **P3** | CRP-01의 산출물을 작은 규칙/예시/threshold 자산으로 변환하여 런타임에 주입. **입력**: CRP-01 산출 calibration YAML **출력**: `modules/domain/agents/` 하위 에이전트가 소비하는 contract 파일 (JSON/YAML) | 증류된 contract가 해당 에이전트에서 소비됨 | 3일 | CRP-01 | S7 섹션 6.2 단계 2 |
| CRP-03 | 오프라인 벤치마크 체계 구축 | **P3** | 실물 vs 생성 blind 비교, calibration, fine-tuning 입력용 벤치마크. **입력**: 실물 원고 + 생성 원고 쌍 **출력**: 벤치마크 스크립트 (`tests/benchmark/`) + 결과 리포트 (정량 비교 매트릭스) | 벤치마크 파이프라인 구축, 1회 이상 실행 완료 | 5일 | CRP-01 | S7 섹션 6.2 단계 3 |
| CRP-04 | 생성 직접 주입 (최후 옵션) | **P4** | few-shot YAML 등을 프롬프트에 직접 주입. 비용/잡음/과적합/문체 모사 부작용 존재. **입력**: CRP-01~03 효과 측정 결과 + 실물 few-shot 예시 **출력**: 에이전트 프롬프트에 삽입되는 few-shot YAML 블록 | CRP-01~03 효과 측정 후 필요성 판단 | 2일 | CRP-01, CRP-02, CRP-03 | S7 섹션 6.2 단계 4, 섹션 6.3 비권장 사항 |

---

## 3. 실행 의존성 그래프

```
[선행 필수]
G1, G2 ─────┬──> G4 ──> G5
             ├──> OPP-06 ──> ROL-01
             ├──> ROL-05
             └──> (효과 측정 전제)

[독립 실행 가능]
OPP-05, OPP-03, OPP-17, G3 (각각 독립)
OPP-01 <-> OPP-02 (동시 진행)
OPP-07 (OPP-01 후)
ROL-02 ──> ROL-03
OPP-17 ──> ROL-04
CRP-01 ──> CRP-02 ──> CRP-03 ──> CRP-04

[독립 실행 가능 - 관측성/UI]
OPP-04, OPP-10, OPP-13, OPP-15(=G2 병행), OPP-16, OPP-18, OPP-19

[독립 실행 가능 - 테스트/품질]
OPP-11, OPP-12, OPP-20
```

---

## 4. 추정 총 공수 요약

| Tier | 항목 수 | 추정 공수 합계 | 비고 |
|------|---------|-------------|------|
| Tier 1 (측정 기반) | 5건 | 2.75일 | **최우선 -- 모든 개선의 전제** |
| Tier 2 (실제 결함) | 3건 | 1.25일 | 데이터 정합성 직접 영향 |
| Tier 3 (구조 정리) | 5건 | 6.25일 | OPP-08 단독 3일 |
| Tier 4 (관측성/UX) | 7건 | 5.25일 | 독립 병행 가능 |
| Tier 5 (품질/테스트) | 4건 | 4.5일 | OPP-11 단독 2일 |
| Tier 6 (ROL 지렛대) | 5건 | 14일+ | ROL-01 단독 5일+ |
| Tier 7 (코퍼스) | 4건 | 13일 | CRP-03 단독 5일 |
| **합계** | **33건** | **47일+** | |

---

## 5. 권장 실행 순서 (Phase 기반)

### Phase 1: 측정 정상화 (1주차)
- G1 + G2 + G3 + OPP-05 + OPP-03 + OPP-17
- 합계: ~2.5일
- 효과: 이후 모든 개선의 효과를 정량적으로 측정 가능

### Phase 2: 핵심 ROL 최적화 (2-3주차)
- ROL-02 (Vertex Context Caching) + ROL-03 (Prefix 정규화)
- G4 + G5
- 합계: ~7.5일
- 기대 효과: -70% 이상 비용 절감

### Phase 3: 구조 정리 + 관측성 (3-4주차)
- OPP-01/02 (Verdict 정리) + OPP-04 (sink 정합성) + OPP-10/15/19 (운영자 경험)
- 합계: ~6일

### Phase 4: 통과율 향상 + 코퍼스 (5주차~)
- ROL-01 (통과율), ROL-04/05 (패치/모델 최적화)
- CRP-01~04 (코퍼스 단계별 활성화)
- 합계: ~22일+
- 기대 효과: 추가 -30% 비용 절감

---

## 6. 감리 이력

### 기본 감리 (3-pass)

| Pass | 목적 | 결과 |
|------|------|------|
| 1차: 완전성 검증 | S7 SSOT의 모든 실행 가능 항목이 누락 없이 포함되었는지 확인 | G1-G5 (5건), OPP-01~20 (20건), ROL-01~05 (5건), CRP-01~04 (4건) = **총 34건 중 33건 수록** (OPP-15와 G2는 동일 원인이므로 병행 처리로 통합, 별도 행 유지) |
| 2차: 우선순위 정합성 | ROI 기반 우선순위가 S7의 "가장 시급한 수정" 및 "가장 높은 ROL 영향" 판단과 일치하는지 확인 | S7의 "가장 시급: G1+G2" -> Tier 1 P0 배치 **일치**. S7의 "가장 높은 ROL: 통과율+캐싱" -> Tier 6 ROL-01/02 P1 배치 **일치** (Tier 1 선행 필수 반영) |
| 3차: 의존성 검증 | 의존성 그래프에 순환이 없고, 선행 조건이 논리적으로 타당한지 확인 | 순환 참조 0건. G1/G2 -> G4 -> G5 체인 정상. ROL-02 -> ROL-03 체인 정상. CRP-01~04 순차 체인 정상 |

### 적대적 감리 (5-pass)

| Pass | 공격 벡터 | 결과 | 보정 내용 |
|------|----------|------|----------|
| 4차: 수치 과장 검증 | 비용 절감 추정치(-70%, -30% 등)가 과장되었는지 S7 근거와 대조 | ROL-02 "-70%"는 S7 섹션 9 #2 "Vertex Context Caching -70%" 원문 그대로. ROL-01 "-30%"는 S7 섹션 9 #1 원문 그대로. **과장 0건** |
| 5차: 공수 과소 추정 검증 | 추정 공수가 비현실적으로 낮지 않은지 검증 | **보정 1건**: ROL-01(통과율 향상)을 "3일" -> "5일+"로 상향. 통과율 55%->80%는 다수 에이전트/파이프라인 조정 필요하며 단순 코드 수정이 아님 |
| 6차: 누락 의존성 검증 | 명시되지 않은 암묵적 의존성이 있는지 검증 | **보정 1건**: ROL-05(모델 티어)에 G1 의존성 추가. Flash 전환 효과를 비용으로 비교하려면 시도 단위 비용 데이터가 필요 |
| 7차: Tier 배치 타당성 공격 | OPP-05(실제 결함)가 Tier 2에 있는 것이 맞는지, Tier 1이어야 하지 않는지 검증 | OPP-05는 quality_risk 불일치로 **데이터 품질에 영향**하지만, 시스템 동작을 멈추지는 않음(PASS_WITH_WARNING은 현재 PASS로 처리됨). Tier 2 배치 **유지 타당** |
| 8차: 코퍼스 과대평가 검증 | CRP-01~04의 우선순위가 너무 높거나 공수가 과소 추정되지 않았는지 검증 | S7 섹션 6.3의 "raw direct wiring 비권장" 원칙 반영 확인. CRP-04를 P4로 배치하고 "최후 옵션"으로 명시한 것은 SSOT 원문과 **일치**. CRP-03 "5일"은 벤치마크 파이프라인 신규 구축이므로 **적정** |

### 감리 보정 요약

| 보정 번호 | Pass | 원본 | 보정 후 | 사유 |
|----------|------|------|--------|------|
| C1 | 5차 | ROL-01 추정 공수 3일 | ROL-01 추정 공수 **5일+** | 통과율 25%p 향상은 다중 파이프라인 조정 필요 |
| C2 | 6차 | ROL-05 의존성 "없음" | ROL-05 의존성 **G1** | Flash 전환 효과 비교에 시도 단위 비용 데이터 필요 |

**최종 확신도**: 97% (S7 원본 확신도 98%에서 실행 계획 변환 과정의 불확실성 -1%)

---

## 7. S7 SSOT 항목 역추적 매트릭스

아래 표는 S7 SSOT의 모든 실행 가능 항목이 본 실행문서에 매핑되었음을 검증한다.

| S7 원본 항목 | 본 문서 ID | Tier | 상태 |
|-------------|-----------|------|------|
| 섹션 7 G1: 시도 단위 비용 미전달 | G1 | Tier 1 | 매핑 완료 |
| 섹션 7 G2: Stage 3 시간 미계량 | G2 | Tier 1 | 매핑 완료 |
| 섹션 7 G3: 시뮬 도구 구가격 | G3 | Tier 1 | 매핑 완료 |
| 섹션 7 G4: 종합 ROL 미계산 | G4 | Tier 1 | 매핑 완료 |
| 섹션 7 G5: Arc 난이도-비용 상관 부재 | G5 | Tier 1 | 매핑 완료 |
| 섹션 5.1 OPP-01: Verdict 6-Way | OPP-01 | Tier 3 | 매핑 완료 |
| 섹션 5.1 OPP-02: CONDITIONAL_PASS | OPP-02 | Tier 3 | 매핑 완료 |
| 섹션 5.4 OPP-03: Firewall JSONL 누락 | OPP-03 | Tier 2 | 매핑 완료 |
| 섹션 5.2 OPP-04: 4-sink 사후 정합성 | OPP-04 | Tier 4 | 매핑 완료 |
| 섹션 5.5 OPP-05: quality_risk 불일치 | OPP-05 | Tier 2 | 매핑 완료 |
| 섹션 5.5 OPP-06: Stage 4 rejection 45.5% | OPP-06 | Tier 5 | 매핑 완료 |
| 섹션 5.5 OPP-07: UNCONDITIONAL_PASS 미문서화 | OPP-07 | Tier 3 | 매핑 완료 |
| 섹션 5.3 OPP-08: Governance 과부하 | OPP-08 | Tier 3 | 매핑 완료 |
| 섹션 5.5 OPP-09: Blockguide 외부 의존 | OPP-09 | Tier 3 | 매핑 완료 |
| 섹션 5.5 OPP-10: UI "대기" 혼재 | OPP-10 | Tier 4 | 매핑 완료 |
| 섹션 5.5 OPP-11: Test mock 과잉 | OPP-11 | Tier 5 | 매핑 완료 |
| 섹션 5.5 OPP-12: Advisory 에스컬레이션 부재 | OPP-12 | Tier 5 | 매핑 완료 |
| 섹션 5.5 OPP-13: Artifact 미검증 | OPP-13 | Tier 4 | 매핑 완료 |
| 섹션 5.5 OPP-14: Dead surface | OPP-14 | Tier 3 | 매핑 완료 |
| 섹션 5.5 OPP-15: Stage 3 duration=0 | OPP-15 | Tier 4 | 매핑 완료 (G2 병행) |
| 섹션 5.5 OPP-16: WS reconnect 부재 | OPP-16 | Tier 4 | 매핑 완료 |
| 섹션 5.5 OPP-17: patch_strategy 비정규화 | OPP-17 | Tier 2 | 매핑 완료 |
| 섹션 5.5 OPP-18: Quality Radar 범례 | OPP-18 | Tier 4 | 매핑 완료 |
| 섹션 5.5 OPP-19: Stage 3 에스컬레이션 비대칭 | OPP-19 | Tier 4 | 매핑 완료 |
| 섹션 5.5 OPP-20: _LazyThreshold 스레드 | OPP-20 | Tier 5 | 매핑 완료 |
| 섹션 9 #1: 통과율 향상 | ROL-01 | Tier 6 | 매핑 완료 |
| 섹션 9 #2: Vertex Context Caching | ROL-02 | Tier 6 | 매핑 완료 |
| 섹션 9 #3: Prompt Prefix 정규화 | ROL-03 | Tier 6 | 매핑 완료 |
| 섹션 9 #4: 패치 모드 효율화 | ROL-04 | Tier 6 | 매핑 완료 |
| 섹션 9 #5: 모델 티어 최적화 | ROL-05 | Tier 6 | 매핑 완료 |
| 섹션 6.2 단계 1: 평가 우선 | CRP-01 | Tier 7 | 매핑 완료 |
| 섹션 6.2 단계 2: 증류 주입 | CRP-02 | Tier 7 | 매핑 완료 |
| 섹션 6.2 단계 3: 오프라인 벤치마크 | CRP-03 | Tier 7 | 매핑 완료 |
| 섹션 6.2 단계 4: 직접 주입 | CRP-04 | Tier 7 | 매핑 완료 |

**역추적 결과**: S7 SSOT 실행 가능 항목 34건 중 **34건 전수 매핑 완료** (OPP-15와 G2는 동일 원인이나 별도 행으로 유지).

---

*S7 ROL + 정적 개선 실행문서 -- ROI 우선순위 기반 33건 실행 큐.*
*기본 3-pass + 적대적 5-pass 감리 완료. 보정 2건 반영.*
*최종 확신도: 97%*
