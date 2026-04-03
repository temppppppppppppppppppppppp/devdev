# ep2 FAILED

Stage3 PASS / Stage4 FAILED (Round 7/10에서 사용자 종료, 7회 연속 REJECT)

## Verdict Summary

| 항목 | 결과 |
|------|------|
| ep1 frozen 유지 | YES |
| ep2 blueprint fresh 생성 | YES (PASS, score 100) |
| ep2 Stage4 draft 최종 저장 | NO |
| ep3+ 생성 없음 | YES (오염 0건) |

## Answer-First

- **ep2 통과 여부**: FAILED
- **ep1 frozen 유지 여부**: 확인 — draft, blueprint, world_state, fact_ledger 모두 보존
- **총 소요시간**: ~60분 (prepare~kill), 유효 런타임 ~55분
- **최종 round 수**: 7 완료 + Round 8 진입 시 사용자 종료 (10라운드 중)
- **현재 dominant blocker**: Flashback/Spatial Continuity + EP1 opening 중복 서술 — LLM이 EP1 통화 장면을 EP2 도입부에 반복 재서술하는 패턴 탈출 불가
- **운영상 사용 가능 여부**: 아직 불가 — Stage4 PASS 미달성

## Before vs After (r1 대비 r2)

| 항목 | r1 (focus_r1) | r2 (focus_r2) | 변화 |
|------|---------------|---------------|------|
| Rounds completed | 3 (+R4 진입) | 7 (+R8 진입) | +4라운드 관찰 |
| R1 score | 98 | 98 | 동일 |
| R2 score | 64 | 83 | +19 향상 |
| R3 score | 94 | 86 | -8 하락 |
| Score range | 64~98 | 44~98 | 하한 악화 |
| TF-3 continuity conflict | 미존재 | **신규 작동** | 개선 |
| TF-PATCH-GATE | 미존재 | **신규 작동** | 개선 |
| PreCheck 시작 계약 검증 | 미존재 | **신규 작동** | 개선 |
| V75-D blueprint patch | 미발동 | 미발동 | 동일 |
| continuity_firewall gate | 미발동 | R7에서 발동 (score 44) | 신규 |
| ep2 PASS | NO | NO | 동일 |

## Before vs After (demo_r2 대비)

| 항목 | demo_r2 | focus_r2 | 변화 |
|------|---------|----------|------|
| ep2 PASS | YES (R6) | NO | 퇴보 |
| V75-D blueprint patch | R5에서 발동 | 미발동 | 핵심 차이 |
| continuity_firewall | R5 (score 44) | R7 (score 44) | 유사 |
| Total rounds | 6 | 7+ (중단) | 비수렴 |

## 핵심 질문 답변

### 1. ep1 authority가 frozen 유지되는가?
**YES.** prepare 단계에서 anchor_validation status=ok. ep1 draft/blueprint 보존. world_state ep1 기준 복원 확인. fact_ledger ep1 기준 복원 확인. beyond_target 오염 0건.

### 2. ep2 blueprint가 fresh 생성되는가?
**YES.** Stage3 ep2 PASS, score 100, blueprint_0002.txt 생성 완료.

### 3. ep2 Stage4 draft가 최종 저장되는가?
**NO.** 7라운드 완료 + 8라운드 진입 시 사용자 종료. 모든 라운드에서 flashback/spatial continuity 또는 EP1 중복 서술로 최종 REJECT. ep_0002.txt 미생성.

### 4. EP1→EP2 opening spatial continuity가 여전히 dominant blocker인가?
**YES.** 7라운드 전부 동일 계열 blocker:
- R1: Director PASS(98) → advisory escalation → TF-3 continuity conflict → REJECT
- R2: Director REJECT(83) — EP1 엔딩 중복 서술
- R3: Director REJECT(86) — EP1 엔딩 중복 서술
- R4: Director REJECT(82) — EP1 엔딩 중복 서술
- R5: Director REJECT(86) — EP1 엔딩 중복 서술
- R6: Director REJECT(82) — EP1 엔딩 중복 서술
- R7: continuity_firewall REJECT(44) — 전면 연속성 실패

패턴: LLM이 "통화 끝난 직후부터 시작하라"는 Director 피드백을 반복 수신하지만, 매번 EP1 통화 장면을 opening에 재서술함. 7라운드 연속 동일 피드백 → 동일 실패.

### 5. fix_pack → patch_revision이 이번에는 실제 수렴으로 이어지는가?
**NO.** TF-PATCH-GATE가 fix_pack 미준비로 patch 경로를 차단하여 매번 full rewrite 경로로 전환. full rewrite에서도 LLM이 동일 패턴을 반복.

### 6. 총 소요시간과 최종 round 수는 얼마인가?
- 전체 벽시계: ~60분 (19:54 prepare ~ 사용자 종료)
- 유효 런타임: ~55분
- Round 완료: 7라운드 (R8 진입 시 종료)
- API hang: 없음

### 7. 이 결과로 ep2 통과를 운영상 신뢰할 수 있는가?
**아직 불가.** Stage4 PASS 미달성. 하드바인딩(TF-3, TF-PATCH-GATE, PreCheck)의 **감지력은 확인**되었으나 **수렴력은 미확인**. V75-D blueprint inplace patch가 발동하지 않아 demo_r2와 달리 PASS에 도달하지 못함. 10라운드 소진까지 진행했더라도 동일 패턴 반복 예상.

## 판정 프레임

### Artifact Truth
- `ep_0001.txt` — frozen, 존재 확인
- `ep_0002.txt` — 미생성 (Stage4 미통과)
- `blueprint_0001.txt` — frozen, 존재 확인
- `blueprint_0002.txt` — 존재, PASS score 100
- `attempt_01` ~ `attempt_07` — 7개 시도 artifact

### Metadata Truth
- Stage3 sink alignment: ok, hard gates pass
- Stage4 sink alignment: warn, hard gates **fail**
  - `draft_count_mismatch:1!=2`
  - `runtime_tag_not_complete:stage3_complete`
- Stage4 attempts in DB: 0 (최종 PASS 미기록)
- Director selection rows: 8 (R1~R7 완료 + R8 lifecycle)
- demo_boundary: pass (ep3+ 오염 없음)
- prep_anchor_validation: ok

### Narrative Truth
- Round 1 (full ensemble): PASS(98) → advisory escalation (flashback MAJOR) → TF-3 continuity conflict → REJECT
- Round 2 (patch → continuity patch retry): REJECT(83) — EP1→EP2 중복 서술
- Round 3 (TF-PATCH-GATE → full rewrite + ASP): REJECT(86) — EP1→EP2 중복 서술
- Round 4 (full rewrite + ASP): REJECT(82) — EP1→EP2 중복 서술, TF-29 발동
- Round 5 (TF-PATCH-GATE → full rewrite): REJECT(86) — EP1→EP2 중복 서술
- Round 6 (TF-PATCH-GATE → full rewrite + ASP): REJECT(82) — EP1→EP2 중복 서술
- Round 7 (TF-PATCH-GATE → full rewrite + ASP): continuity_firewall REJECT(44) — 전면 연속성 실패

## 신규 하드바인딩 작동 확인

| 기능 | 작동 여부 | 효과 |
|------|-----------|------|
| TF-3 post-select continuity conflict | YES (R1) | Director PASS를 REJECT로 다운그레이드 — 감지력 확인 |
| TF-PATCH-GATE | YES (R3~R7) | fix_pack 미준비 시 patch 차단 → full rewrite 강제 |
| PreCheck 시작 장소 계약 | YES (R3~R6) | '본가 저택 서재 앞 복도' 토큰 0/3 위반 감지 |
| QR-7 plateau detection | YES (R3) | Score 하락 추세 감지, local retry 차단 |
| TF-29 제약 위반 연속 경고 | YES (R4) | 블루프린트 단계 문제 가능성 경고 |
| continuity_firewall gate | YES (R7) | Score 44로 전면 연속성 차단 |

## 근본 원인 분석

1. **LLM 수렴 실패**: Director가 "통화 끝난 직후부터 시작하라"를 7번 반복 지시했으나 LLM이 매번 EP1 통화 장면을 재서술. 피드백 루프가 작동하지 않음.
2. **V75-D 미발동**: demo_r2에서는 continuity_firewall(score 44) 발동 시 V75-D blueprint inplace patch가 트리거되어 opening 장소/시점을 블루프린트에 명시적으로 고정 → R6에서 PASS. 이번 r2에서는 continuity_firewall가 R7에서 발동했으나 V75-D 패치가 트리거되지 않음.
3. **하드바인딩의 한계**: 감지력(detection)은 강화되었으나 교정력(correction)은 미달. LLM에 대한 피드백 강도를 높여도 동일 패턴 반복.

## Scope Boundaries
- Arc1 full closure proof가 아님
- ep2 only go/no-go proof임
- Stage4 전체 closure 선언 아님
- source 0_0 미수정

## Evidence Reference
- `docs/2026-04-02/0_0-stage34-ep2-focused-bounded-canary-r2-evidence.json`

## Confidence
- 3-pass audit 완료
- Pass 1: 구조/범위 — 모든 필수 항목 존재, 비교 기준 명시
- Pass 2: 증거 일치 — summary JSON, runtime output, attempt artifacts 교차 검증
- Pass 3: 실행 가능성 — 후속 action 명확 (V75-D 발동 조건 조사), 과장 없음
- **Estimated confidence: 96%**

---

Date: 2026-04-02
Mode: ep2-focused bounded Stage34 single-episode canary (r2)
Source: 0_0
Target: canary_0_0_stage34_ep2_focus_r2
