# 00_test_02 / 00_test_03 Control-Treatment Cross-Check Report — OPUS

> 작성일: 2026-03-11
> 작성자: OPUS
> 오더 문서: `docs/2026-03-11/00-test-02-03-control-treatment-crosscheck-order.md`
> 성격: control-vs-treatment decision layer

---

## 최종 한줄 판정

- `00_test_02`: **재현함** — 4/4 ep 완주, 비용·품질·재시도 모두 00_test_01 대비 동등 이상.
- `00_test_03`: **채택 불가** — Arc 1 미완주 (ep_0003 5회 실패, ep_0004 미도달). 로그 근거만으로 충분.

---

## Pass 1. 실행 사실 고정

### 표 A. Run Snapshot

| project | profile | scope | stage2 | stage3 | stage4 | blueprint_count | draft_count | stage_attempts | director_selections | total_tokens | total_cost_usd | source |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
| 00_test_02 | control-2.5-pro | Arc 1 / ep_0001~ep_0004 | 1 PASS_WITH_FIX | 4 PASS | 4 PASS + 1 REJECT | 4 | 4 | 10 | 6 | 880,936 | 1.6364 | DB + metrics_20260311_200432.json |
| 00_test_03 | treatment-3.1-flash-lite | Arc 1 / ep_0001~ep_0004 | 1 PASS | 4 PASS | 2 PASS + 7 REJECT | 4 | 2 | 14 | 10 | 1,169,027 | 0.8872 | DB + metrics_20260311_201738.json |

### 표 B. Artifact / Completion Matrix

| project | artifact | expected | observed | parity | notes | source |
|---|---|---|---|---|---|---|
| 00_test_02 | arc_001 | 1 | 1 | match | 4화 Arc, 투자물 장르 | plans/arcs/ |
| 00_test_02 | blueprint_0001 | 1 | 1 | match | score 100, PASS | plans/blueprints/ |
| 00_test_02 | blueprint_0002 | 1 | 1 | match | score 100, PASS | plans/blueprints/ |
| 00_test_02 | blueprint_0003 | 1 | 1 | match | score 100, PASS | plans/blueprints/ |
| 00_test_02 | blueprint_0004 | 1 | 1 | match | score 100, PASS | plans/blueprints/ |
| 00_test_02 | ep_0001 | 1 | 1 | match | score 98 | drafts/ |
| 00_test_02 | ep_0002 | 1 | 1 | match | score 98 | drafts/ |
| 00_test_02 | ep_0003 | 1 | 1 | match | score 90 (1 retry) | drafts/ |
| 00_test_02 | ep_0004 | 1 | 1 | match | score 98 | drafts/ |
| 00_test_02 | runtime_audit_summary | 1 | 1 | match | 11 events | logs/ |
| 00_test_02 | quality_metrics | 1 | 1 | match | 25 entries | logs/ |
| 00_test_02 | episode_production | 1 | 1 | match | 5 entries (4ep + 1 retry) | logs/ |
| 00_test_03 | arc_001 | 1 | 1 | match | 4화 Arc, 투자물 장르 | plans/arcs/ |
| 00_test_03 | blueprint_0001 | 1 | 1 | match | score 90, PASS | plans/blueprints/ |
| 00_test_03 | blueprint_0002 | 1 | 1 | match | score 95, PASS | plans/blueprints/ |
| 00_test_03 | blueprint_0003 | 1 | 1 | match | score 92, PASS | plans/blueprints/ |
| 00_test_03 | blueprint_0004 | 1 | 1 | match | score 90, PASS | plans/blueprints/ |
| 00_test_03 | ep_0001 | 1 | 1 | match | score 90 (1 retry) | drafts/ |
| 00_test_03 | ep_0002 | 1 | 1 | match | score 92 (1 retry) | drafts/ |
| 00_test_03 | ep_0003 | 1 | 0 | **missing** | 5회 시도 후 실패 | drafts/ |
| 00_test_03 | ep_0004 | 1 | 0 | **missing** | ep_0003 실패로 미도달 | drafts/ |
| 00_test_03 | runtime_audit_summary | 1 | 1 | match | 13 events | logs/ |
| 00_test_03 | quality_metrics | 1 | 1 | match | 33 entries | logs/ |
| 00_test_03 | episode_production | 1 | 1 | match | 11 entries | logs/ |

---

## Pass 2. 차이 분해

### 표 C. Decision Taxonomy

| id | project | taxonomy | evidence | current interpretation | impact on operating-profile decision | next check point | confidence |
|---|---|---|---|---|---|---|---|
| C-01 | 00_test_02 | confirmed control parity | 4/4 ep 완주, artifacts 전량 존재, stage_attempts=10, director_selections=6 | 00_test_01 (11 attempts, $1.66) 대비 동등 — retry 1건 감소, 비용 $0.02 절감 | none | — | 97% |
| C-02 | 00_test_02 | confirmed control parity | 평균 점수 96.0 (98/98/90/98), Blueprint 전량 100 | 00_test_01 대비 품질 동등 이상 | none | — | 97% |
| C-03 | 00_test_02 | acceptable drift | Stage 2 verdict PASS_WITH_FIX (auto-correct: 무협 필드 제거, 추상 아이템 제거) | 투자물 장르 스키마 정리 — 설계된 동작. 00_test_01에서도 동일 패턴 | none | — | 95% |
| C-04 | 00_test_02 | acceptable drift | ep_0003 round 0 REJECT (Aquila 말→차 연속성 모순), round 1 inplace_patch PASS 90 | 단일 retry로 해소, 시스템 건강 신호 | none | — | 95% |
| T-01 | 00_test_03 | **failure signal** | ep_0003 미완성: 5회 시도 후 실패 (score 86→90→50→50→43, 하강 궤적) | flash-lite 모델이 공간 연속성 + 분량 제약을 동시 충족 불가. 피드백 누적에도 개선 없이 악화 | **high** | — | 98% |
| T-02 | 00_test_03 | **failure signal** | ep_0004 미도달 — ep_0003 실패로 파이프라인 정지 | Arc 1 미완주 확정 | **high** | — | 99% |
| T-03 | 00_test_03 | **failure signal** | Stage 4 REJECT 7건 / 14 total attempts (REJECT율 50%) vs control 1건 / 10 attempts (10%) | retry 폭증으로 비용 이득 상쇄, 시간 초과 (68분 vs 51분) | **high** | — | 97% |
| T-04 | 00_test_03 | acceptable drift | ep_0001, ep_0002 각 1회 retry 후 PASS (score 90, 92) | 초기 2화는 flash-lite로도 통과 가능 — 단순 구조 에피소드 한정 | low | manual reading | 85% |
| T-05 | 00_test_03 | acceptable drift | Stage 2 PASS (1회), Stage 3 전량 PASS (score 90~95) | Arc/Blueprint 생성은 flash-lite로도 동작 — Stage 2/3은 profile 무관 | low | — | 90% |
| T-06 | 00_test_03 | acceptable drift | 비용 $0.89 vs control $1.64 (46% 절감) | 비용 이득 존재하나, 미완주로 인해 "4화 기준 비용"으로 비교 불가. 완료분 2화만 비교하면 control 2화분 ~$0.51 vs treatment 2화분 ~$0.50 — 동등 | medium | 완주 시 재비교 | 80% |
| T-07 | 00_test_03 | hypothesis pending | flash-lite의 chronic length shortfall (ep1r0: 3,085자, ep2r0: 3,293자, ep3r2: 2,769자) — 4,000자 미달 반복 | 모델 고유 한계 vs 프롬프트 분량 지시 부족 미분리. 프롬프트에 분량 강조를 추가하면 개선될 수 있으나, 현재 근거로는 모델 한계가 우세 | medium | 프롬프트 실험 | 70% |
| T-08 | 00_test_03 | hypothesis pending | ep_0003 공간 연속성 실패가 모델 한계인지 blueprint 품질 차이인지 | blueprint_0003 score=92 (control도 92 이상은 아님), Director 피드백 4회 누적에도 교정 불가 → 모델 한계 쪽 증거 우세 | low | blueprint 차이 정밀 대조 | 75% |

### 핵심 failure 경로 분석: 00_test_03 ep_0003

```
Round 0: score 86, REJECT — 공간 연속성 위반 (로비 → 법무사 사무소)
Round 1: score 90, PASS_WITH_FIX → InPlace patch 시도
Round 2: score 50, REJECT — patch가 2,769자로 축소 + V60.97 auto-swap + 타임라인 혼동
Round 3: score 50, REJECT — 3,211자, 여전히 분량 미달 + 키워드 누락
Round 4: score 43, REJECT — 양쪽 후보 모두 집에서 시작 (ep2 ending 무시), 분량 미달
→ 5회 소진, FAILED
```

**패턴**: InPlace patch 후 오히려 분량 축소 → full rewrite에서도 이전 에피소드 ending을 무시 → 피드백 누적이 instruction following 한계에 부딪힘. 이는 `gemini-3.1-flash-lite-preview` 모델의 **복합 제약 동시 충족 능력 부족**으로 해석됨.

---

## Pass 3. 운영 권고 판정

### 표 D. Decision Ladder

| claim | 00_test_02 | 00_test_03 | blocker to 95% | confidence_now | confidence_if_resolved |
|---|---|---|---|---|---|
| control profile reproducibility | 재현 확인 — 00_test_00→01→02 3연속 동등 | N/A | 없음 | **97%** | — |
| control profile cost/runtime observability | $1.64 / 51분 / 881K tokens — 00_test_01 ($1.66) 대비 ±2% | N/A | 없음 | **97%** | — |
| treatment profile viability | N/A | Arc 1 미완주 (2/4 ep) | 미완주는 로그 근거만으로 fail-closed | **98% 채택 불가** | — |
| treatment profile quality trustworthiness | N/A | 완료 2화 score 90/92 — 수치만 보면 양호하나 manual reading 미실시 | manual reading 미실시 + 미완주 | **60%** (완료분 한정) | 80% (manual reading 후) |
| next operating recommendation | 현행 2.5-pro 프로파일 유지 | all-lite 단독 운영 불가 | — | **95%** | — |

### 판정 근거 정리

**00_test_02 = 재현함 (97%)**:
- 00_test_00 (18 attempts, $1.97) → 00_test_01 (11 attempts, $1.66) → 00_test_02 (10 attempts, $1.64): 일관된 개선 추세
- 4/4 ep 완주, artifact 전량 존재, quality label 4건
- Stage 4 REJECT 1건 (ep3 Aquila 모순) → 1회 retry로 해소
- Blueprint 전량 score 100, ep 평균 96.0
- LLM 호출 실패 0건 / 135건

**00_test_03 = 채택 불가 (98%)**:
- fail-closed 규칙 1.4.3 적용: "ep_0003 또는 ep_0004 미생산" → 채택 불가 판정 가능
- ep_0003: 5회 시도 후 실패, score 하강 궤적 (86→90→50→50→43)
- ep_0004: 미도달
- Stage 4 REJECT율 50% (7/14) vs control 10% (1/10)
- 비용 $0.89이나, 미완주이므로 단가 비교 무의미
- 시간 68분 > control 51분 — 비용 절감 효과마저 시간에서 상쇄

**실패가 시스템 코어 결함인가, profile 비적합인가**:
- **profile 비적합으로 분리 가능** (confidence 92%)
  - 동일 코드베이스에서 control (2.5-pro)은 3연속 재현 성공
  - treatment의 Stage 2/3은 정상 동작 (Arc PASS, Blueprint 4/4 PASS)
  - 실패는 Stage 4 복합 제약 (공간 연속성 + 분량 4,000자+) 동시 충족 — flash-lite 모델 한계
  - chronic length shortfall은 flash-lite 고유 패턴 (ep1r0: 3,085자, ep2r0: 3,293자)
  - control에서는 분량 미달이 한 번도 발생하지 않음

---

## 비교용 요약

1. **00_test_02는 control run으로서 재현되었는가**: 예. 00_test_00→01→02 3연속 재현. retry 감소 추세, 비용 안정 ($1.64), 품질 동등 이상 (avg 96.0).

2. **00_test_03는 all-lite profile로 채택 가능한가**: 아니오. Arc 1 미완주 (2/4 ep). fail-closed 규칙에 의해 로그 근거만으로 채택 불가.

3. **비용/시간 기준에서 treatment의 이득 또는 손해는 무엇인가**: 미완주이므로 공정 비교 불가. 완료 2화만 비교하면 단가 동등 (~$0.25/ep). 시간은 오히려 손해 (68분 > 51분, retry 폭증 때문).

4. **quality 신뢰성은 어디서 흔들리는가**: treatment ep_0003에서 붕괴. InPlace patch 후 분량 축소 → full rewrite에서 이전 ep ending 무시 → 피드백 누적이 모델 instruction following 한계에 부딪힘. 이는 flash-lite 모델의 복합 제약 동시 충족 능력 부족.

5. **다음 단계는 무엇인가**: **운영 채택** (현행 2.5-pro 프로파일 유지). all-lite 단독 운영은 중단. 향후 flash-lite 활용을 원한다면 Stage 2/3 한정 또는 hybrid profile (Stage 4는 2.5-pro 유지) 실험으로 전환 검토.

---

## Appendix A. Agent-specific observations

1. **treatment Blueprint 품질은 양호**: Stage 3 score 90/95/92/90 — control (100/100/100/100)보다 낮지만 전량 PASS. flash-lite가 구조적 계획에는 기능한다는 신호.

2. **treatment의 chronic length shortfall 패턴**: ep1r0 (3,085자), ep2r0 (3,293~3,763자), ep3r2 (2,769자), ep3r3 (3,211자). 첫 시도에서 4,000자 미달이 반복됨. 이는 flash-lite가 한국어 웹소설 5,000자 target을 프롬프트만으로 달성하기 어렵다는 증거.

3. **control ep3 vs treatment ep3**: control도 ep3에서 1회 REJECT (Aquila 모순)이 발생했으나 InPlace patch 1회로 해소 (score 90). treatment는 동일 ep 위치에서 5회 소진. ep3는 양쪽 모두에서 가장 어려운 에피소드였으나, 모델 능력 차이가 결정적.

4. **treatment 토큰 소비 역설**: treatment (1,169K) > control (881K). flash-lite가 저가이므로 비용은 낮으나, retry 폭증으로 총 토큰은 33% 더 소비. API 할당량 관점에서는 오히려 불리.

5. **treatment에서 LLM 호출 1건 실패**: Director agent에서 1/190 실패. control은 0/135 실패. 단독으로는 의미 없으나, flash-lite의 안정성이 pro보다 약간 낮을 수 있다는 약한 신호.

6. **treatment work_focus/scene_engines 미활성**: 전체 retrieval observation에서 `work_focus_present=false`, `scene_engines_count=0`. 이는 테스트 프로젝트 경량 설정 때문이지 모델 문제가 아님. control에서도 확인 필요.

## Appendix B. 반례 / 이견 / 추가 가설

1. **가설: 프롬프트 분량 강조로 length shortfall 해소 가능?** — 현재 chief_writer.yaml에 분량 지시가 있으나 (TARGET=5,000자, MIN=4,000자), flash-lite가 이를 무시하는 패턴이 반복됨. 프롬프트 강화만으로 해소될 가능성은 낮으나 (confidence 30%), 정식 실험 없이 단정할 수는 없음.

2. **가설: hybrid profile (S2/S3=flash-lite, S4=2.5-pro)의 비용 이득**: Stage 2/3에서 flash-lite가 정상 동작했으므로, S2/S3만 flash-lite로 전환하면 비용 절감 가능. 다만 S2/S3 비용은 전체의 ~15%이므로 절감 효과는 $0.10~0.15/arc 수준으로 제한적.

3. **treatment ep_0003 실패가 blueprint 품질 차이 때문일 가능성**: blueprint_0003 score가 control 100 vs treatment 92. 이 차이가 Stage 4 실패에 기여했을 수 있으나, control에서도 ep3가 유일한 retry 에피소드였다는 점에서 ep3 자체의 서사적 난이도가 더 큰 요인으로 보임.

---

## Appendix C. InPlace Patch Guard 갭 분석

> 00_test_03 ep_0003의 PASS_WITH_FIX → 분량 축소 → 연쇄 REJECT 패턴을 계기로,
> 전 Stage InPlace patch 경로의 guard 현황을 조사한 결과.

### 발견 갭 요약

| ID | Stage | 심각도 | 내용 | 실제 피해 사례 |
|---|---|---|---|---|
| GAP-1 | S4 | HIGH | `chief_writer.inplace_patch()` L997의 2,000자 최소 체크가 raw LLM 응답 기준. JSON wrapper 포함 시 추출된 manuscript는 체크 없이 반환 | — |
| GAP-2 | S4 | HIGH | REJECT retry 경로 (L2847-2863)에 `min_patched_length` 체크 없음. PASS_WITH_FIX 경로(L2242)에만 존재 | — |
| GAP-3 | 전체 | MEDIUM | **원본 대비 축소 guard 없음.** patch가 원본의 50%로 줄어도 F-2 advisory(로깅만) 외에 차단 없음 | **00_test_03 ep3r1→r2: 5,000자+→2,769자 (45% 축소), score 90→50** |
| GAP-4 | S4-V75D | MEDIUM | V75-D blueprint inplace 경로(`stage4_orchestrator.py` L1116-1134)에서 재심사·변경비율·diff 로깅 없이 바로 채택 | — |
| GAP-5 | S2-preflight | LOW | preflight retry 경로(`stage2_preflight.py` L1247-1257)에 change ratio / diff 로깅 없음 | — |
| GAP-6 | 전체 | LOW | `log_patch_diff()`가 글자수 delta를 안 찍음 (unified diff만 출력) | — |
| GAP-7 | 전체 | INFO | 핵심 섹션 보존 검증 없음 (ending_hook, core_tension, tactical_doc 등). Pydantic은 구조만 체크 | — |

### 기존 guard 현황 대조

| 검사 항목 | S4 원고 | S2 Arc | S3 Blueprint |
|---|---|---|---|
| 최소 길이 (절대 하한) | 2,000자 (PASS_WITH_FIX 경로만) | 없음 | 없음 |
| 원본 대비 축소 방지 | **없음** | **없음** | **없음** |
| 변경 비율 체크 | 30% 초과 시 advisory (차단 안함) | 30% 초과 시 advisory (차단 안함) | 30% 초과 시 advisory (차단 안함) |
| 구조 검증 | 없음 | `validate_arc()` ✅ | `validate_blueprint()` ✅ |
| 원본 필드 병합 | 해당없음 | 1-depth deep merge ✅ | 1-depth deep merge ✅ |
| 30KB 절단 방지 | 해당없음 | return None ✅ | return None ✅ |
| Director 재심사 | ✅ | ✅ | ✅ (V75D 경로 제외) |

### 인과 관계: 00_test_03 ep3 붕괴 경로

```
ep3r0: score 86, REJECT (공간 연속성)
ep3r1: score 90, PASS_WITH_FIX → InPlace patch 진입
  → GAP-3 발동: patch 결과 2,769자 (원본 대비 ~45% 축소)
  → min_patched_length=2,000 통과 (절대 하한만 체크)
  → F-2 advisory 발생 (change_ratio > 30%) but 차단 안함
  → Director 재심사: score 50, REJECT (분량 미달 + V60.97 auto-swap + 타임라인 혼동)
ep3r2: full rewrite → 3,211자, 여전히 미달
ep3r3: full rewrite → 양쪽 후보 ep2 ending 무시, score 43
→ 5회 소진, FAILED
```

핵심: GAP-3가 있어도 Director 재심사가 잡긴 하지만, **이미 retry 1회를 소모**하고 축소된 상태에서 시작하므로 회복이 어려워짐. 원본 대비 70% 미만 축소 시 patch를 즉시 버리고 원본으로 되돌렸다면, retry 예산을 아낄 수 있었음.

### 권고 (코드 수정 시)

1. **GAP-3 해소 (P0)**: S4 `stage4_interview_round.py` L2243 직후에 `len(_patched_ms) < len(_current_ms) * 0.7` → patch 폐기, 원본 유지
2. **GAP-1 해소 (P0)**: `chief_writer.inplace_patch()` L1054에서 `len(_manuscript) < 2000` → `return []`
3. **GAP-2 해소 (P1)**: REJECT retry 경로 L2859에도 `min_patched_length` 체크 추가
4. **GAP-4 해소 (P1)**: V75-D blueprint 경로에 change_ratio + diff 로깅 추가
5. **GAP-6 해소 (P2)**: `log_patch_diff()`에 `len(original)→len(patched)` 1줄 로깅 추가

---

## 3-Pass 감리 자체 점검

### Pass 1. 오더 문서 자체 감리
- [x] 입력 파일 목록 고정: 양쪽 모두 오더 명시 파일 전량 사용
- [x] control/treatment 역할 고정: 00_test_02=control-2.5-pro, 00_test_03=treatment-3.1-flash-lite
- [x] 표 헤더 고정: 표 A/B/C/D 오더 명세 준수
- [x] taxonomy 4개 고정: confirmed control parity / acceptable drift / failure signal / hypothesis pending
- [x] 00_test_03 채택 가능에 manual reading 필요 규칙 준수: 미완주로 인해 manual reading 없이 채택 불가 판정 (fail-closed 1.4.3)

### Pass 2. 비교 가능성 감리
- [x] 동일 표 구조 사용
- [x] 00_test_02와 00_test_03 혼동 없음
- [x] 사실과 해석 분리 (표 C evidence vs interpretation)
- [x] control 재현과 treatment 채택 가능성이 별개 질문임이 드러남

### Pass 3. 과장 방지 감리
- [x] 00_test_02 재현 성공을 00_test_03 채택으로 승격하지 않음
- [x] 00_test_03의 단순 PASS 로그만으로 quality 신뢰 선언하지 않음 (T-04 confidence 85%, manual reading 미실시 명시)
- [x] manual reading 없이 채택 가능/95%를 허용하지 않음
- [x] 반복 REJECT + 미완주로 logs만으로 채택 불가 판정 가능함을 명시
