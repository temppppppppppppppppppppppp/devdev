# 에스컬레이션 TF 잔여 항목 통합 SSOT

> Independent Re-Audit (Codex, 2026-03-16)
>
> Status: historical research memo, not live execution SSOT.
>
> Primary caution: the `TF-E2` R2 rationale says `UI 경고 없음`, but the current code already emits explicit `V75-B` UI warnings in `modules/core/stage4_orchestrator.py` during regeneration failure and terminal failure handling.
>
> Operational note: keep `TF-E3`, `TF-E8`, `TF-E11`, and `TF-E13` only as follow-up leads; do not treat the current severity text as fully authoritative without line-by-line live revalidation.
>
> Confidence: 97% for memo-only use. Direct execution confidence is below 95%.

| Field | Value |
|-------|-------|
| **Baseline** | `bbb00a77` |
| **Date** | 2026-03-15 |
| **Scope** | `stage4-escalation-bp-fix-deepdive-tf.md` 13건 중 기존 SSOT 미포함 10건 |
| **원본** | stage4-escalation-bp-fix-deepdive-tf.md (R2) |
| **이미 포함된 3건** | TF-E7 → fix-candidates S4-6, TF-E9 → fix-candidates S4-1, TF-E10 → fix-candidates S4-2 |
| **본 문서 대상** | 잔여 10건 (IMPORTANT 3 / INSIGHT 6 / MERGED 1) |

---

## 요약

Stage 4 에스컬레이션(V75-D InPlace / V75-B Full Regen) 딥다이브에서 발견된 13건 중 CRITICAL 1건(TF-E9) + IMPORTANT 2건(TF-E7, TF-E10)은 `all-stage-deepdive-fix-candidates-ssot.md`에서 S4-1, S4-2, S4-6으로 이미 참조되었다. 나머지 10건은 어떤 통합 SSOT에도 포함되지 않았으므로 본 문서에서 정리한다.

---

## 잔여 항목 매트릭스

| ID | 심각도 | 제목 | 파일:라인 | 상태 |
|----|--------|------|----------|------|
| TF-E1 | INSIGHT P3 | V75-D streak 리셋이 V75-B 발동 지연 | stage4_orchestrator.py:L1248 | CLOSED (의도된 설계) |
| TF-E2 | IMPORTANT P2 | V75-B 실패 시 결함 BP로 무언 계속 | stage4_orchestrator.py:L1298-1300 | OPEN |
| TF-E3 | IMPORTANT P1 | `_log_escalation_event` 스키마 불충분 (5필드→11필드) | stage4_orchestrator.py:L1353-1372 | OPEN |
| TF-E4 | INSIGHT P3 | 30KB 초과 BP 절단 가드 정상 동작 | three_phase_bp_generator.py:L716-718 | CLOSED (양성 확인) |
| TF-E5 | INSIGHT P2 | `prev_blueprints=[]` 하드코딩 | stage4_orchestrator.py:L1412 | MERGED → TF-E10 (S4-2) |
| TF-E6 | INSIGHT P3 | Reverse feedback은 문자열 조합만 (LLM 0회) | feedback_system.py:L554-602 | CLOSED (비용 효율적 설계) |
| TF-E8 | IMPORTANT P1 | 에스컬레이션 감사 추적이 4개 채널에 분산 | (다수) | OPEN |
| TF-E11 | INSIGHT P2 | V75-D 패치 프롬프트 컨텍스트 제한 | blueprint_generator.yaml:L3-22, three_phase_bp_generator.py:L726-732 | OPEN |
| TF-E12 | INSIGHT P3 | PASS_WITH_FIX는 에스컬레이션 대체안이 아님 | stage4_interview_round.py:L2975-3226 | CLOSED (문서화 목적) |
| TF-E13 | INSIGHT P2 | V75-D deep-merge가 씬 내부 콘텐츠 변경을 허용 | three_phase_bp_generator.py:L771-787 | OPEN |

---

## IMPORTANT 항목 상세 (3건)

### TF-E2 — V75-B 실패 시 결함 BP로 무언 계속 `IMPORTANT P2`

- **위치**: `stage4_orchestrator.py:L1298-1300`
- **현상**: V75-B Full Regen 실패 → `_blueprint_regenerated = True`로 재시도 차단 + `logging.warning`만. 기존 결함 BP로 남은 라운드를 계속 진행.
- **영향**: 사용자가 V75-B 실패를 인지 못한 채 품질 저하된 결과물 수신.
- **수정 방향**: UI 경고 추가 + escalation 로그에 `fallback_reason` 필드 추가 (TF-E3과 연계).

### TF-E3 — `_log_escalation_event` 스키마 불충분 `IMPORTANT P1`

- **위치**: `stage4_orchestrator.py:L1353-1372`
- **현상**: 현재 스키마 `{ts, ep, event, streak, success}` 5필드만. 사후 분석에 필요한 `round_num`, `error_category`, `quality_risk`, `change_ratio`, `fallback_reason`, `elapsed_ms` 누락.
- **수정 방향**: 6개 필드 확장 + `_log_escalation_event` 시그니처에 `**extra` kwargs 추가.

### TF-E8 — 에스컬레이션 감사 추적이 4개 채널에 분산 `IMPORTANT P1`

- **위치**: episode_production.jsonl, logging.warning, ctx.ui.log, _log_escalation_event
- **현상**: 에스컬레이션 이벤트 사후 분석에 4개 채널 교차 조회 필요.
- **수정 방향**: JSONL 통합 — 모든 에스컬레이션 이벤트를 단일 structured log로.

---

## INSIGHT 항목 상세 (6건)

### TF-E1 — V75-D streak 리셋이 V75-B 발동 지연 `INSIGHT P3` — CLOSED

- **위치**: `stage4_orchestrator.py:L1248`
- **판단**: 의도된 설계. InPlace 성공 = 새 BP → 새 streak 시작이 논리적으로 타당.

### TF-E4 — 30KB 초과 BP 절단 가드 정상 동작 `INSIGHT P3` — CLOSED

- **위치**: `three_phase_bp_generator.py:L716-718`
- **판단**: 양성 확인. 30KB 초과 시 InPlace 불가 → V75-B fallback 경로 존재.

### TF-E5 — `prev_blueprints=[]` 하드코딩 `INSIGHT P2` — MERGED

- **위치**: `stage4_orchestrator.py:L1412`
- **판단**: TF-E10 (fix-candidates S4-2)으로 통합. 별도 액션 불필요.

### TF-E6 — Reverse feedback LLM 0회 `INSIGHT P3` — CLOSED

- **위치**: `feedback_system.py:L554-602`
- **판단**: 비용 효율적 설계. 키워드 패턴 매칭 기반 역방향 피드백. 현재 수준으로 충분.

### TF-E11 — V75-D 패치 프롬프트 컨텍스트 제한 `INSIGHT P2` — OPEN

- **위치**: `blueprint_generator.yaml:L3-22`, `three_phase_bp_generator.py:L726-732`
- **현상**: V75-D InPlace 패치 시 이전 EP BP/원고, HUD, NPC 레지스트리 미제공. Director 피드백이 "연속성" 지적 시 LLM이 이전 화 정보 없이 수정해야 하는 한계.
- **영향**: 낮음 — deep-merge가 원본 씬 키 복원하여 구조적 드리프트 방지.
- **수정 방향**: Director 피드백에 "연속성" 키워드 포함 시 prev_blueprint 정보를 패치 프롬프트에 추가 권고.

### TF-E12 — PASS_WITH_FIX는 에스컬레이션 대체안 아님 `INSIGHT P3` — CLOSED

- **위치**: `stage4_interview_round.py:L2975-3226`
- **판단**: 해결하는 문제 영역이 다름 (PASS_WITH_FIX = 원고 미세 교정, 에스컬레이션 = BP 구조 결함). 대체 불가 확인.

### TF-E13 — V75-D deep-merge 씬 내부 콘텐츠 보호 없음 `INSIGHT P2` — OPEN

- **위치**: `three_phase_bp_generator.py:L771-787`
- **현상**: deep-merge가 씬 키(최상위)와 최상위 BP 필드는 보호하지만, 씬 내부 콘텐츠(summary, dialogue_hints, action_points)는 LLM이 자유 재작성 가능. 검 획득 이벤트가 패치로 소실되면 후속 씬에서 아이템 타임라인 불일치.
- **수정 방향**: 패치 전후 씬 콘텐츠 diff를 로그 기록하여 드리프트 사후 감지 지원.

---

## 우선순위별 액션

| 우선순위 | ID | 작업 | 상태 |
|---------|-----|------|------|
| P1 | TF-E3 | 에스컬레이션 로그 스키마 6필드 확장 | OPEN |
| P1 | TF-E8 | 감사 추적 JSONL 통합 | OPEN |
| P2 | TF-E2 | V75-B 실패 시 UI 경고 + fallback_reason | OPEN |
| P2 | TF-E11 | 연속성 피드백 시 패치 프롬프트 보강 | OPEN |
| P2 | TF-E13 | 패치 전후 씬 diff 로그 | OPEN |
| — | TF-E1, E4, E6, E12 | 코드 변경 없음 (의도된 설계 / 양성 확인) | CLOSED |
| — | TF-E5 | TF-E10 (S4-2)으로 통합 | MERGED |

---

## 전체 SSOT 크로스레퍼런스

| 통합 SSOT | 커버 항목 |
|----------|----------|
| `all-stage-deepdive-fix-candidates-ssot.md` | 25건 (S0~X-4) + TF-E7/E9/E10 참조 |
| `all-subsystem-tf-consolidated-ssot.md` | 109건 (거시 8 서브시스템) |
| `detail-subsystem-tf-consolidated-ssot.md` | 114건 (디테일 8 서브시스템) |
| **`escalation-residual-tf-consolidated-ssot.md`** | **10건 (본 문서)** |
| **전체 누적** | **258건** |

---

---

## [3PA] 3-Pass Audit 감리 결과 (2026-03-16)

| ID | 판정 | 확신도 | 사유 |
|----|------|--------|------|
| TF-E1 | **[3PA] CONFIRMED (CLOSED)** | 99% | 의도된 설계 확인. V75-D 성공 후 streak 리셋 논리적으로 타당. |
| TF-E2 | **[3PA] CONFIRMED** | 90% | V75-B 실패 시 UI 경고 존재하나 불충분. 결함 BP로 계속 진행. |
| TF-E3 | **[3PA] CONFIRMED** | 95% | 5필드 스키마 확인. 6개 유용 필드 누락. |
| TF-E4 | **[3PA] CONFIRMED (CLOSED)** | 100% | 30KB 가드 정상 동작 확인. |
| TF-E5 | **[3PA] CONFIRMED (MERGED)** | 99% | S4-2로 통합 확인. |
| TF-E6 | **[3PA] CONFIRMED (CLOSED)** | 99% | 비용 효율적 키워드 기반 역방향 피드백. |
| TF-E8 | **[3PA] CONFIRMED** | 90% | 4채널 분산 확인. 사후 분석에 교차 조회 필요. |
| TF-E11 | **[3PA] CONFIRMED** | 85% | 컨텍스트 제한 실재하나 InPlace 패치 설계 철학에 부합. |
| TF-E12 | **[3PA] CONFIRMED (CLOSED)** | 99% | PASS_WITH_FIX와 에스컬레이션은 별도 문제 영역 확인. |
| TF-E13 | **[3PA] CONFIRMED** | 90% | 1-depth merge 갭 실재. 프롬프트 규칙 + temperature=0.3으로 경감. |

**요약**: 10건 전량 CONFIRMED. CLOSED 4건 (의도된 설계), MERGED 1건, OPEN 5건 유지.

*3-Pass Audit by Claude Opus 4.6 — 2026-03-16*

### [3PA-R2] 대원칙 적용 재감리 (2026-03-16)

대원칙 #3 (디렉터 주권주의)을 감사 렌즈로 추가 적용한 결과, 본 SSOT에서 2건 변경.

| ID | R1 판정 | R2 판정 | R2 확신도 | 대원칙 | 사유 |
|----|---------|---------|-----------|--------|------|
| **TF-E2** | CONFIRMED(IMP) P2 (90%) | **CONFIRMED(HIGH) P1** | **95%** | **#3** | V75-B 실패 시 Director가 결함 BP를 인지 못함 = **Director 정보 비대칭으로 주권 약화**. UI 경고 없음 → 사용자(및 Director)가 BP 재생성 실패 미인지. **심각도 상향: IMPORTANT P2 → HIGH P1.** |
| **TF-E6** | CONFIRMED(CLOSED) (99%) | **CONFIRMED(CLOSED)** | 99% | **#1** | 비용 효율적 키워드 기반 역방향 피드백 = **대원칙#1 정합**. Python은 문자열 조합(수집/포맷)만, LLM 판단 0회. 설계 compliance 명시 추가. |
| TF-E8 | CONFIRMED (90%) | 유지 | **92%** | #3 | 4채널 감사 분산 → Director 사후 분석 복잡도 증가. NEEDS-RUNTIME-VERIFICATION. |
| TF-E11 | CONFIRMED (85%) | 유지 | **88%** | #1+#3 | V75-D 패치 프롬프트 컨텍스트 제한. InPlace 설계 철학에 부합하나 연속성 피드백 시 LLM 기초 약화. NEEDS-RUNTIME-VERIFICATION. |
| TF-E13 | CONFIRMED (90%) | 유지 | **93%** | #3 | deep-merge 씬 내부 보호 없음. Director가 다음 라운드에서 감지 가능 (사후 대응). NEEDS-RUNTIME-VERIFICATION. |

**R2 신규 발견**: TF-E2 심각도 상향 (IMPORTANT→HIGH). Director 정보 비대칭이 #3 위반.

**R2 요약**: 10건 중 CLOSED 4건(유지), MERGED 1건(유지), OPEN 5건(유지, TF-E2 HIGH 상향).

*3-Pass Audit R2 (대원칙) by Claude Opus 4.6 — 2026-03-16*
