# Stage 4 에스컬레이션 → BP 수정 딥다이브 TF

| Field | Value |
|-------|-------|
| **Baseline** | `bbb00a77` |
| **Date** | 2026-03-15 |
| **Revision** | R2 — 연속성/드리프트/PASS_WITH_FIX 대체안 심층 조사 추가 |
| **Scope** | V75-D InPlace / V75-B Full Regen 2단계 에스컬레이션 |
| **Source files** | `stage4_orchestrator.py`, `three_phase_blueprint_generator.py`, `stage4_types.py`, `feedback_system.py`, `stage4_interview_round.py`, `blueprint_ensemble.py`, `director_continuity.py`, `blueprint_generator.yaml`, `ensemble.yaml` |
| **TF Items** | 13 (CRITICAL 1 / IMPORTANT 6 / INSIGHT 6) |

---

## 1. Executive Summary

Stage 4 인터뷰 라운드에서 `LOGIC_ERROR` 연속 발생 시 블루프린트를 자동 수정하는 2단계 에스컬레이션 시스템을 감사했다.

- **V75-D (InPlace Patch)**: 단일 LLM 호출로 논리 오류만 외과적 수정 (1~2연속 LOGIC_ERROR에서 트리거)
- **V75-B (Full Regen)**: InPlace 실패 시 블루프린트 전체 재생성 (2연속 이상 + InPlace 시도 후)

### R2 추가 조사 질문 4건

| # | 질문 | 판정 |
|---|------|------|
| Q1 | 에스컬레이션 후 실제로 잘 되는가? | **조건부 YES** — V75-D는 구조 보존형이라 안전. V75-B는 prev_blueprints=[]로 패턴 학습 없이 재생성하므로 드리프트 위험 존재 |
| Q2 | 앞뒤 BP들과 어울리는가? | **NO** — 에스컬레이션 후 연속성 재검증 미실행 (TF-E9 CRITICAL) |
| Q3 | PASS_WITH_FIX를 적용해야 하는 거 아닌가? | **NO** — 해결하는 문제 영역이 다름. PASS_WITH_FIX=원고 수준 미세 교정, 에스컬레이션=BP 구조 결함 수정 |
| Q4 | 완전 다른 내용으로 써 버릴 가능성은 없는가? | **V75-D: 낮음, V75-B: 있음** — V75-B는 prev_blueprints 없이 재생성하므로 플롯 방향 전환 가능 (TF-E10) |

**결론**: 에스컬레이션 메커니즘 자체는 건전하나, **교체된 BP에 대한 연속성 재검증이 부재**하여 인접 에피소드와 모순이 발생할 수 있다. 이것이 이번 조사에서 발견된 유일한 CRITICAL (TF-E9).

---

## 2. Architecture Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    INTERVIEW ROUND LOOP (L926-1351)             │
│                                                                 │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │ Round N   │───▶│ CoVe 사후검증 │───▶│ CoVe REJECT?         │  │
│  │ (LLM call)│    │ (L989-1076) │    │ continue → 다음 라운드 │  │
│  └──────────┘    └──────────────┘    │ (streak 불변!)        │  │
│       │                               └──────────────────────┘  │
│       ▼                                                         │
│  ┌──────────────────────────┐                                   │
│  │ error_category 평가      │                                   │
│  │ (L1131-1135)             │                                   │
│  │ LOGIC_ERROR → streak++   │                                   │
│  │ 그 외       → streak = 0 │                                   │
│  └────────────┬─────────────┘                                   │
│               ▼                                                 │
│  ┌──────────────────────────────────────────┐                   │
│  │ V75-D InPlace Trigger (L1196-1265)       │                   │
│  │ streak ≥ threshold AND !inplace_attempted │                   │
│  │ threshold = quality_risk ? 1 : 2          │                   │
│  │                                           │                   │
│  │  ① Reverse feedback 추출 (L1215-1218)    │                   │
│  │  ② Feedback 병합 (L1219-1222)            │                   │
│  │  ③ _inplace_patch_blueprint (L1223-1228) │                   │
│  │  ④ 성공 → streak=0, BP 교체 (L1247-1248)│                   │
│  │  ⑤ 실패 → V75-B로 진행                   │                   │
│  │                                           │                   │
│  │  ⚠ 교체 후 연속성 재검증 없음 (TF-E9)    │                   │
│  └────────────┬─────────────────────────────┘                   │
│               ▼                                                 │
│  ┌──────────────────────────────────────────┐                   │
│  │ V75-B Full Regen Trigger (L1268-1307)    │                   │
│  │ streak ≥ 2 AND inplace_attempted         │                   │
│  │            AND !blueprint_regenerated     │                   │
│  │                                           │                   │
│  │  ① Reverse feedback 추출 (L1274-1277)    │                   │
│  │  ② _regenerate_blueprint (L1278-1283)    │                   │
│  │     └─ prev_blueprints=[] (TF-E10)       │                   │
│  │     └─ prev_manuscripts_text 미전달       │                   │
│  │  ③ 성공 → streak=0, BP 교체 (L1286-1288)│                   │
│  │  ④ 실패 → _blueprint_regenerated=True    │                   │
│  │           (재시도 방지, L1299)             │                   │
│  │                                           │                   │
│  │  ⚠ 교체 후 연속성 재검증 없음 (TF-E9)    │                   │
│  │  ⚠ 플롯 방향 전환 가능 (TF-E10)          │                   │
│  └────────────┬─────────────────────────────┘                   │
│               ▼                                                 │
│  ┌──────────────────────────────────────────┐                   │
│  │ Post-Loop Fallback (L1309-1351)          │                   │
│  │ final_manuscript 없으면:                  │                   │
│  │  - V75-B 후 실패 경고 (L1311-1313)       │                   │
│  │  - 최선 결과물 사용 / 건너뛰기 (L1314+)  │                   │
│  └──────────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. TF Items

### TF-E1 — V75-D streak 리셋이 V75-B 발동 지연 `INSIGHT P3`

- **파일**: `modules/core/stage4_orchestrator.py:1248`
- **현상**: V75-D InPlace 성공 시 `_logic_error_streak = 0`으로 리셋. 패치 후에도 LOGIC_ERROR 재발하면 streak을 처음부터 다시 쌓아야 V75-B에 도달한다. quality_risk 없을 경우 최소 4회 LOGIC_ERROR 필요 (2회 → V75-D → 리셋 → 2회 → V75-B).
- **영향**: V75-B 도달까지 추가 라운드 소모. 그러나 InPlace가 실제로 성공한 경우 streak 리셋은 합리적이다 — InPlace가 BP를 교체했으므로 새 BP에 대해 새로 평가해야 한다.
- **판단**: **의도된 설계**. InPlace 성공 = 새 BP → 새 streak 시작이 논리적으로 타당.
- **액션**: 코멘트만. 현 로직 유지.

---

### TF-E2 — V75-B 실패 시 결함 BP로 무언 계속 `IMPORTANT P2`

- **파일**: `modules/core/stage4_orchestrator.py:1298-1300`
- **현재 코드**:
  ```python
  else:
      _blueprint_regenerated = True   # L1299 — 재시도 방지
      logging.warning("[V75-B] 블루프린트 재생성 실패 — 기존 Blueprint 유지")  # L1300
  ```
- **문제**: V75-B 전체 재생성이 실패하면 `_blueprint_regenerated = True`로 재시도를 차단하고, 기존 결함 BP로 남은 라운드를 계속 진행한다. `logging.warning`만 남기고 UI 표시나 구조화된 로그가 없다.
- **영향**: 사용자가 V75-B 실패를 인지하지 못한 채 품질 저하된 결과물을 받을 수 있다.
- **수정안**: UI 경고 추가 + escalation 로그에 `fallback_reason` 필드 추가 (TF-E3과 연계).
- **액션**: P2 — UI 경고 + fallback_reason 로그.

---

### TF-E3 — `_log_escalation_event` 스키마 불충분 `IMPORTANT P1`

- **파일**: `modules/core/stage4_orchestrator.py:1353-1372`
- **현재 스키마**: `{ts, ep, event, streak, success}` — 5필드만.
- **문제**: 사후 분석에 필요한 `round_num`, `error_category`, `quality_risk`, `change_ratio`, `fallback_reason`, `elapsed_ms` 누락.
- **액션**: P1 — 6개 필드 확장. `_log_escalation_event` 시그니처에 `**extra` kwargs 추가.

---

### TF-E4 — 30KB 초과 BP 절단 가드 정상 동작 `INSIGHT P3`

- **파일**: `modules/domain/agents/three_phase_blueprint_generator.py:716-718`
- **판단**: 정상 동작. 30KB 초과 시 InPlace 불가 → V75-B fallback 경로 존재.
- **액션**: No action.

---

### TF-E5 — `_regenerate_blueprint`에서 `prev_blueprints=[]` 하드코딩 `INSIGHT P2`

- **파일**: `modules/core/stage4_orchestrator.py:1412`
- **판단**: 의도된 설계이나 연속성 측면에서 위험. TF-E10에서 상세 분석.
- **액션**: TF-E10 참조.

---

### TF-E6 — Reverse feedback은 문자열 조합만 (LLM 0회) `INSIGHT P3`

- **파일**: `modules/core/feedback_system.py:554-602`
- **판단**: 비용 효율적 설계. 키워드 패턴 매칭 기반 역방향 피드백.
- **액션**: No action.

---

### TF-E7 — CoVe REJECT가 에스컬레이션 streak 카운터 우회 `IMPORTANT P2`

- **파일**: `modules/core/stage4_orchestrator.py:1029, 1055, 1076`
- **문제**: CoVe REJECT 시 `continue`로 streak 카운터 평가(L1131)를 건너뜀. CoVe 반복 실패 시 에스컬레이션 미발동.
- **액션**: P2 — CoVe 전용 streak 카운터 + 임계값 경고 추가.

---

### TF-E8 — 에스컬레이션 감사 추적이 4개 채널에 분산 `IMPORTANT P1`

- **파일**: 다수 (episode_production.jsonl, logging.warning, ctx.ui.log)
- **문제**: 에스컬레이션 이벤트 추적에 4개 채널 교차 조회 필요.
- **액션**: P1 — JSONL 통합.

---

### TF-E9 — 에스컬레이션 후 연속성 재검증 부재 `CRITICAL P0` (R2 신규)

- **파일**: `modules/core/stage4_orchestrator.py:1246-1256` (V75-D), `1284-1296` (V75-B)
- **현재 동작**:
  ```python
  # V75-D 성공 후 (L1246-1256):
  round_ctx = dataclasses.replace(round_ctx, blueprint=_patched_bp)
  _logic_error_streak = 0
  # → 바로 다음 라운드에서 ChiefWriter에게 전달. 연속성 재검증 없음.

  # V75-B 성공 후 (L1284-1296):
  round_ctx = dataclasses.replace(round_ctx, blueprint=_new_bp)
  _logic_error_streak = 0
  # → 동일. 연속성 재검증 없음.
  ```
- **문제**: 정상 BP 생성 경로(Stage 3)에서는 `check_blueprint_continuity_with_cache()`가 Phase 3 검증으로 실행된다 (`three_phase_blueprint_generator.py:368-386`). 이 검증은:
  - 이전 화 종료 위치 → 현재 화 시작 위치 연속성
  - 사망 캐릭터 재등장 여부
  - 시간 흐름 일관성
  - CRITICAL 발견 시 REJECT → 재생성 루프

  그러나 에스컬레이션(V75-D/V75-B) 후 교체된 BP는 이 검증을 **건너뛴다**. 교체된 BP가 바로 ChiefWriter에게 전달되어 원고 생성에 사용된다.

- **구체적 위험 시나리오**:
  ```
  Ep 9 BP: 주인공이 북경 도착, 장문인과 회합
  Ep 10 원래 BP: 북경 장문인 회합 이어서 진행
  Ep 10 V75-B 재생성 BP: 주인공이 남경에서 새로운 NPC와 만남
  → 위치 불연속 (북경→남경), 장문인 소실, 플롯 단절
  → check_blueprint_continuity_with_cache 미실행으로 미감지
  ```

- **근거 — 정상 경로 vs 에스컬레이션 경로 비교**:

  | 검증 단계 | Stage 3 정상 생성 | V75-D InPlace | V75-B Full Regen |
  |----------|------------------|---------------|------------------|
  | Pydantic 스키마 검증 | ✅ | ✅ `validate_blueprint()` L787 | ✅ `generate()` 내부 |
  | Director 연속성 검증 | ✅ `check_blueprint_continuity_with_cache` L368-386 | ❌ **미실행** | ❌ **미실행** |
  | Unified Blueprint Validator | ✅ Phase 3 검증 루프 | ❌ 미실행 | ❌ 미실행 |
  | Entity Consistency | ✅ Phase 3 | ❌ 미실행 | ❌ 미실행 |

- **영향**: V75-B에서 생성된 BP가 인접 에피소드와 위치/시간/캐릭터 불일치를 가진 채 원고 생성에 사용될 수 있다. 특히 V75-B는 `prev_blueprints=[]`이므로 Arc 패턴 학습 없이 생성되어 드리프트 가능성이 높다.

- **수정안**:
  ```python
  # V75-D/V75-B 성공 후 (L1248 / L1288 직후):
  if self.ctx.agents.get("director") and getattr(self.ctx.current_project, "db", None) and next_ep > 1:
      _cont = self.ctx.agents["director"].check_blueprint_continuity_with_cache(
          ep_num=next_ep,
          new_blueprint=_patched_bp,  # 또는 _new_bp
          db=self.ctx.current_project.db,
      )
      if _cont.get("decision") == "REJECT":
          logging.warning("[V75-D/V75-B] 에스컬레이션 BP 연속성 검증 실패: %s", _cont.get("issues"))
          # 교체 취소, 원본 BP로 복원
          round_ctx = dataclasses.replace(round_ctx, blueprint=_original_bp)
  ```
- **액션**: P0 — 에스컬레이션 후 연속성 재검증 게이트 추가.

---

### TF-E10 — V75-B Full Regen 콘텐츠 드리프트 위험 `IMPORTANT P1` (R2 신규)

- **파일**: `modules/core/stage4_orchestrator.py:1374-1428`
- **문제**: V75-B `_regenerate_blueprint`가 `bp_agent.generate()`를 호출할 때 다음이 **누락**됨:

  | 파라미터 | 정상 생성 시 | V75-B 재생성 시 | 영향 |
  |---------|-------------|----------------|------|
  | `prev_blueprints` | Arc 내 이전 EP BP 전체 | `[]` (빈 리스트) | Arc 패턴 학습 없음 → 스타일/구조 불일치 |
  | `prev_manuscripts_text` | 직전 에피소드 원고 전문 | 미전달 (`""` 기본값) | 이미 쓰인 내용 모름 → 이벤트/대화 반복 가능 |
  | `prev_hud` | HUD 컨텍스트 | 미전달 (`None` 기본값) | NPC 상태/부상/장비 최신 정보 부재 |
  | `adversarial_self_play` | ASP 교차 검증 | 미전달 (`None`) | 자기 교차 검증 없이 생성 |
  | `semantic_context` | 시맨틱 검색 결과 | 미전달 (`""`) | DB 기반 유사 장면 참조 불가 |

- **V75-B가 받는 컨텍스트**:
  - ✅ `arc_data` — Arc 전략/비트/제약
  - ✅ `prev_blueprint` — 직전 1개 EP의 BP (종료 위치/시간/상태 전달)
  - ✅ `entity_registry` — 누적 상태 (`extract_cumulative_state(ep_num-1)`)
  - ✅ `protagonist_name/config` — 주인공 설정
  - ✅ `external_feedback` — Director 거부 사유 + Reverse feedback
  - ✅ `director`, `state_tracker`, `db` — Phase 3 검증 루프 사용 가능

- **결론**: V75-B는 "최소한의 컨텍스트"로 재생성하며, 핵심 Arc 목표와 직전 EP 연결은 유지하지만, **Arc 전체 패턴**(prev_blueprints)과 **이미 생성된 원고**(prev_manuscripts_text)를 모른다. 이로 인해:
  1. 같은 에피소드인데 전혀 다른 씬 구성이 나올 수 있음
  2. 직전 에피소드에서 이미 발생한 이벤트를 반복할 수 있음
  3. Arc 전체에서 유지되던 톤/페이싱 패턴이 끊길 수 있음

- **위험도 정량 추정**:
  - V75-D InPlace: 드리프트 위험 **낮음** — 원본 BP 구조 보존 + 지적 사항만 수정 (BLUEPRINT_PATCH_MODE_PROMPT 규칙 5항 "NPC 설정, 세계관, 관계도 절대 변경 금지")
  - V75-B Full Regen: 드리프트 위험 **높음** — 원본 BP의 ~20-30%만 생존 (플롯 골격은 arc_data 제약으로 유지, 씬 구성/대화/감정곡선은 자유 재설계)

- **수정안**: `_regenerate_blueprint`에서 누락 파라미터 보충:
  ```python
  # prev_blueprints 복원 (DB에서 조회):
  _prev_bps = []
  if db:
      for _prev_ep in range(max(1, ep_num - 3), ep_num):
          _bp = db.get_blueprint(_prev_ep)
          if _bp:
              _prev_bps.append(_bp)

  new_bp, _ = bp_agent.generate(
      ...
      prev_blueprints=_prev_bps,  # ← 최근 3개 EP BP
      prev_manuscripts_text=db.get_manuscript(ep_num - 1) or "",  # ← 직전 원고
      ...
  )
  ```
- **액션**: P1 — prev_blueprints + prev_manuscripts_text 최소 복원. 전체 파라미터 복원은 비용 대비 효과 검토 후 결정.

---

### TF-E11 — V75-D InPlace 패치 프롬프트의 컨텍스트 제한 `INSIGHT P2` (R2 신규)

- **파일**: `config/prompts/blueprint_generator.yaml:3-22`, `three_phase_blueprint_generator.py:726-732`
- **BLUEPRINT_PATCH_MODE_PROMPT 핵심 규칙**:
  ```
  1. Blueprint의 씬 배분, 감정 곡선, 핵심 장면 구조를 보존
  2. Director가 지적한 문제점만 정확히 수정
  3. 수정하지 않는 부분은 원본 그대로 유지
  4. scene_list 구조(씬 번호, 기본 흐름)를 유지
  5. NPC 설정, 세계관, 관계도는 절대 변경 금지
  ```
- **LLM에게 제공되는 컨텍스트**:
  - ✅ `original_blueprint` — 원본 BP 전문 (JSON)
  - ✅ `director_feedback` — Director 거부 사유 + Reverse feedback
  - ✅ `arc_tactical` — Arc 전술 문서 발췌 (3,000자 상한, L726-732)
  - ❌ 이전 에피소드 BP/원고 — 미제공
  - ❌ 주인공 현재 상태 (HUD) — 미제공
  - ❌ NPC 레지스트리 — 미제공
- **판단**: V75-D는 "원본 보존 + 지적 사항만 수정"이므로 이전 컨텍스트 필요성이 낮다. 다만, Director 피드백이 "이전 화와의 연속성"을 지적하는 경우 LLM이 이전 화 정보 없이 수정해야 하는 한계가 있다.
- **영향**: 낮음 — V75-D의 deep-merge (L771-787)가 원본 씬 키를 복원하므로 구조적 드리프트는 방지됨. 콘텐츠 수준 드리프트는 제한적.
- **액션**: P2 권고 — Director 피드백에 "연속성" 키워드가 포함된 경우 prev_blueprint 정보를 패치 프롬프트에 추가하는 방안 검토.

---

### TF-E12 — PASS_WITH_FIX는 에스컬레이션 대체안이 아님 `INSIGHT P3` (R2 신규)

- **파일**: `stage4_interview_round.py:2975-3226`, `stage4_orchestrator.py:974-1078`
- **분석**: PASS_WITH_FIX와 에스컬레이션은 **서로 다른 문제 영역**을 해결한다:

  | 차원 | PASS_WITH_FIX | V75-D/V75-B 에스컬레이션 |
  |------|---------------|------------------------|
  | **트리거 조건** | Director 판정 score≥90 + MINOR 이슈 | REJECT + error_category=LOGIC_ERROR 연속 |
  | **수정 대상** | **원고** (Manuscript) | **블루프린트** (Blueprint) |
  | **수정 방식** | `chief_writer.inplace_patch()` 최대 3회 | `_inplace_patch_blueprint()` 또는 `_regenerate_blueprint()` |
  | **재심사** | Director 재판정 (매 패치 후) | ❌ 연속성 재검증 미실행 (TF-E9) |
  | **error_category** | 항상 `""` (빈 문자열) | `"LOGIC_ERROR"` |
  | **인터뷰 루프** | PASS_WITH_FIX 판정 시 **즉시 종료** (L974 break) | REJECT 시 **계속 루프** |

- **판정 분기 흐름**:
  ```
  Director 판정
  ├─ score ≥ 90, 이슈 없음     → PASS          → 루프 종료
  ├─ score ≥ 90, MINOR 이슈    → PASS_WITH_FIX → 원고 패치 최대 3회 → 루프 종료
  ├─ score < 90, 구조 결함 없음 → REJECT        → 다음 라운드 (streak 불변)
  └─ score < 90, LOGIC_ERROR   → REJECT        → streak++ → V75-D/V75-B 에스컬레이션
  ```

- **왜 PASS_WITH_FIX로 대체할 수 없는가**:
  1. PASS_WITH_FIX는 score≥90인 원고에만 적용 — LOGIC_ERROR 연속은 score<90이므로 대상 외
  2. PASS_WITH_FIX는 원고를 수정 — 그러나 BP 구조가 결함이면 원고 패치로 해결 불가
  3. PASS_WITH_FIX 후 Director가 재심사 — 에스컬레이션 후에는 재심사 없음 (오히려 에스컬레이션이 PASS_WITH_FIX보다 검증이 약함)

- **판단**: 대체 불가. 다만, 에스컬레이션 후 최소한 PASS_WITH_FIX 수준의 재심사(Director 연속성 검증)는 필요 — TF-E9 참조.
- **액션**: No action (문서화 목적). TF-E9의 연속성 재검증이 이 문제를 커버.

---

### TF-E13 — V75-D deep-merge가 씬 내부 콘텐츠 변경을 허용 `INSIGHT P2` (R2 신규)

- **파일**: `modules/domain/agents/three_phase_blueprint_generator.py:771-787`
- **현재 deep-merge 로직**:
  ```python
  # 1-depth shallow merge: 원본 필드 복원
  for key, val in original_blueprint.items():
      if key not in result:
          result[key] = val
      elif isinstance(val, dict) and isinstance(result[key], dict):
          for sub_key, sub_val in val.items():
              if sub_key not in result[key]:
                  result[key][sub_key] = sub_val

  # 누락된 씬 키 복원
  _lost = set(_orig_sb) - set(_result_sb)
  if _lost:
      for sk in _lost:
          _result_sb[sk] = _orig_sb[sk]
  ```
- **보호되는 것**: 씬 키(scene_breakdown의 최상위 키), 최상위 BP 필드(emotion_curve, setting 등)
- **보호되지 않는 것**: 씬 내부 콘텐츠(summary, dialogue_hints, action_points 등). LLM이 scene_breakdown["scene_3"]["summary"]를 완전히 다시 쓸 수 있다.
- **예시 시나리오**:
  ```
  원본 scene_3.summary: "주인공이 검을 획득하고 장문인에게 보고"
  패치 scene_3.summary: "주인공이 산을 내려가며 독백" (Director가 "scene 3 전환 급함" 지적)
  → 검 획득 이벤트 소실, 그러나 scene_7에서 검 사용 참조 남음
  → 아이템 타임라인 불일치
  ```
- **영향**: 중간 — 프롬프트 규칙 5("NPC 설정, 세계관, 관계도 절대 변경 금지")가 방어하지만, 이벤트 순서나 아이템 획득은 명시적으로 보호되지 않음.
- **액션**: P2 권고 — 패치 전후 씬 콘텐츠 diff를 로그에 기록하여 드리프트 사후 감지 지원. 이미 change_ratio를 L1242에서 계산하므로, 씬별 diff를 추가 기록하면 됨.

---

## 4. 에스컬레이션 후 "잘 되는가?" 상세 분석

### 4.1 V75-D InPlace — 비교적 안전

**LLM에게 주어지는 지시**:
- "지적된 부분만 정확히 수정" + "전면 재설계하지 마세요"
- 씬 배분/감정곡선/핵심장면 구조 보존 명시
- NPC/세계관/관계도 변경 금지

**코드 레벨 안전장치**:
- deep-merge: 원본 필드 + 누락 씬 키 복원 (L771-787)
- Pydantic 스키마 검증 (L787)
- 30KB 초과 시 InPlace 포기 → V75-B fallback (L716-718)
- temperature=0.3 (낮은 창의성, L764-765)

**위험 요소**:
- 연속성 재검증 미실행 (TF-E9)
- 씬 내부 콘텐츠 보호 없음 (TF-E13)
- 이전 화 정보 미제공 (TF-E11)

**종합 판정**: **비교적 안전**. 구조적 드리프트 가능성 낮음. 콘텐츠 수준 미세 드리프트 가능하나, 프롬프트 규칙이 강력히 제한.

### 4.2 V75-B Full Regen — 주의 필요

**LLM에게 주어지는 컨텍스트** (generate() 파이프라인 내부):
- arc_data 전체 (전략/비트/제약)
- prev_blueprint (직전 1개 EP만)
- entity_registry (누적 상태)
- protagonist 설정
- external_feedback (거부 사유)
- V67 모순방지 절대준수 사항 6항 (ensemble.yaml L369-378)
- ❌ prev_blueprints (Arc 패턴) → 빈 리스트
- ❌ prev_manuscripts_text (직전 원고) → 빈 문자열

**코드 레벨 안전장치**:
- generate() 내부의 Phase 3 검증 루프가 실행됨 (BlueprintConstraintCompiler, Director 연속성 검증 포함)
- Pydantic 검증
- max_retries=9 (재시도 가능)

**위험 요소**:
- prev_blueprints=[] → Arc 패턴 학습 없음 (TF-E10)
- prev_manuscripts_text 미전달 → 이미 쓰인 내용 모름 (TF-E10)
- 에스컬레이션 후 Orchestrator 레벨 연속성 재검증 없음 (TF-E9)

**종합 판정**: **주의 필요**. generate() 내부 검증은 동작하지만, 에스컬레이션 컨텍스트가 부족하여 Arc 전체 일관성이 약화될 수 있음. 플롯 골격은 arc_data 제약으로 유지되나, 씬 구성/대화/톤이 달라질 수 있음.

### 4.3 "앞뒤 BP와 어울리는가?"

| 연결 요소 | V75-D | V75-B |
|----------|-------|-------|
| **위치 연속성** (이전 화 종료 → 현재 화 시작) | ⚠ 원본에서 상속되나, 패치로 변경 가능 | ✅ prev_blueprint에서 추출 |
| **시간 흐름** | ⚠ 원본에서 상속 | ✅ prev_blueprint에서 추출 |
| **캐릭터 등장** | ⚠ 프롬프트 규칙 5로 보호 | ⚠ entity_registry로 부분 보호 |
| **플롯 진행 방향** | ✅ 원본 구조 보존 | ❌ 다른 방향으로 갈 수 있음 |
| **톤/페이싱** | ✅ 원본 emotion_curve 보존 | ❌ prev_blueprints 없으므로 Arc 패턴 학습 불가 |
| **다음 화 기대 충족** | ❌ 다음 화 BP 미참조 | ❌ 다음 화 BP 미참조 |

**핵심 결론**: "앞" 에피소드와의 연결은 prev_blueprint을 통해 부분적으로 유지되지만, "뒤" 에피소드와의 정합성은 **양쪽 다 전혀 검증하지 않음**. 다만 이는 정상 생성 경로도 동일한 한계 (다음 화 BP는 아직 생성 전).

---

## 5. 로깅 체계 개선안

### 5.1 통합 이벤트 스키마

```json
{
  "ts": "2026-03-15T14:30:00",
  "ep": 42,
  "event": "V75-D_INPLACE",
  "round_num": 3,
  "streak": 2,
  "success": true,
  "error_category": "LOGIC_ERROR",
  "quality_risk": false,
  "change_ratio": 0.18,
  "fallback_reason": null,
  "elapsed_ms": 4200,
  "prev_verdict": "REJECT",
  "continuity_recheck": "PASS"
}
```

### 5.2 이벤트 라우팅 테이블

| # | 이벤트 | `event` 값 | 기록 시점 |
|---|--------|------------|-----------|
| 1 | LOGIC_ERROR streak 증가 | `STREAK_INC` | L1133 직후 |
| 2 | streak 리셋 | `STREAK_RESET` | L1135 직후 |
| 3 | V75-D 시도 | `V75-D_INPLACE` | L1265 |
| 4 | V75-B 시도 | `V75-B_FULL_REGEN` | L1307 |
| 5 | CoVe REJECT | `COVE_REJECT` | L1029, 1055, 1076 |
| 6 | 30KB 절단 가드 | `BP_TRUNCATION_GUARD` | three_phase_bp L718 |
| 7 | Post-loop fallback 선택 | `POSTLOOP_FALLBACK` | L1314-1344 |
| 8 | Preflight 검증 | `TF49b_PREFLIGHT` | L565 (기존) |
| 9 | 에스컬레이션 후 연속성 재검증 | `ESC_CONTINUITY_RECHECK` | TF-E9 수정 후 추가 |

### 5.3 하위 호환성 고려사항

- 기존 5필드 스키마 유지. 신규 필드는 optional.
- `_log_escalation_event` 시그니처에 `**extra` kwargs 추가.

---

## 6. Summary Matrix

| TF ID | 심각도 | 제목 | 파일 | 라인 | 액션 | 상태 |
|-------|--------|------|------|------|------|------|
| TF-E1 | INSIGHT P3 | V75-D streak 리셋이 V75-B 발동 지연 | stage4_orchestrator.py | 1248 | 코멘트만 (의도된 설계) | CLOSED |
| TF-E2 | IMPORTANT P2 | V75-B 실패 시 결함 BP로 무언 계속 | stage4_orchestrator.py | 1298-1300 | UI 경고 + fallback_reason 로그 | OPEN |
| TF-E3 | IMPORTANT P1 | `_log_escalation_event` 스키마 불충분 | stage4_orchestrator.py | 1353-1372 | 6개 필드 확장 | OPEN |
| TF-E4 | INSIGHT P3 | 30KB 초과 BP 절단 가드 정상 동작 | three_phase_bp_generator.py | 716-718 | No action | CLOSED |
| TF-E5 | INSIGHT P2 | `prev_blueprints=[]` 하드코딩 | stage4_orchestrator.py | 1412 | TF-E10으로 통합 | MERGED |
| TF-E6 | INSIGHT P3 | Reverse feedback LLM 0회 | feedback_system.py | 554-602 | No action | CLOSED |
| TF-E7 | IMPORTANT P2 | CoVe REJECT가 streak 카운터 우회 | stage4_orchestrator.py | 1029, 1055, 1076 | CoVe 전용 streak 추가 | OPEN |
| TF-E8 | IMPORTANT P1 | 감사 추적 4채널 분산 | (다수) | — | JSONL 통합 | OPEN |
| **TF-E9** | **CRITICAL P0** | **에스컬레이션 후 연속성 재검증 부재** | stage4_orchestrator.py | 1246-1296 | **연속성 게이트 추가** | **OPEN** |
| **TF-E10** | **IMPORTANT P1** | **V75-B Full Regen 콘텐츠 드리프트 위험** | stage4_orchestrator.py | 1374-1428 | **prev_blueprints + prev_ms 복원** | **OPEN** |
| TF-E11 | INSIGHT P2 | V75-D 패치 프롬프트 컨텍스트 제한 | blueprint_generator.yaml, three_phase_bp_generator.py | 3-22, 726-732 | 연속성 피드백 시 prev_bp 추가 권고 | OPEN |
| TF-E12 | INSIGHT P3 | PASS_WITH_FIX는 에스컬레이션 대체안 아님 | stage4_interview_round.py | 2975-3226 | 문서화 목적 | CLOSED |
| TF-E13 | INSIGHT P2 | V75-D deep-merge 씬 내부 콘텐츠 보호 없음 | three_phase_bp_generator.py | 771-787 | 씬별 diff 로그 권고 | OPEN |

### 심각도 분포

| 심각도 | 건수 |
|--------|------|
| CRITICAL | 1 |
| IMPORTANT | 6 |
| INSIGHT | 6 |
| **합계** | **13** |

### 우선순위별 액션

| 우선순위 | TF | 작업 내용 |
|----------|-----|----------|
| **P0** | **TF-E9** | **에스컬레이션 후 check_blueprint_continuity_with_cache 재실행 게이트** |
| P1 | TF-E3, TF-E8, TF-E10 | 로그 스키마 확장 + JSONL 통합 + V75-B 컨텍스트 복원 |
| P2 | TF-E2, TF-E7, TF-E11, TF-E13 | UI 경고 + CoVe streak + 패치 프롬프트 보강 + diff 로그 |
| P3 | TF-E1, TF-E4, TF-E6, TF-E12 | 코멘트/문서화만, 코드 변경 없음 |

---

## 7. 핵심 코드 참조 (Appendix)

### A. 에스컬레이션 카운터 초기화

```
stage4_orchestrator.py L940-946
```
```python
_logic_error_streak = 0          # [V75-B] 연속 LOGIC_ERROR 카운터
_inplace_attempted = False       # [V75-D] inplace 패치 1회 제한
_blueprint_regenerated = False   # [V75-B] 재생성 1회 제한
_prev_reject_bucket = ""         # [TF-29] reject_bucket 연속 패턴 감지
_bucket_streak = 0
_prev_dominant_contradiction = ""# [A-4] contradiction type 수렴 추적
_contradiction_type_streak = 0
```

### B. V75-D 성공 후 BP 교체 (연속성 재검증 없음)

```
stage4_orchestrator.py L1246-1256
```
```python
if _patched_bp:
    _v75d_success = True
    round_ctx = dataclasses.replace(round_ctx, blueprint=_patched_bp)  # BP 교체
    _logic_error_streak = 0                                             # streak 리셋
    # ← check_blueprint_continuity_with_cache 미호출 (TF-E9)
    director_feedback = "[V75-D 블루프린트 inplace 패치 완료]\n..."
    previous_attempt = {}
```

### C. V75-B _regenerate_blueprint 호출

```
stage4_orchestrator.py L1407-1420
```
```python
new_bp, _ = bp_agent.generate(
    ep_num=ep_num,
    arc_data=arc_data,
    arc_idx=(arc_data.get("arc_no") or 1) - 1,
    prev_blueprint=prev_bp,        # ← 직전 1개 EP만
    prev_blueprints=[],            # ← 빈 리스트 (TF-E10)
    external_feedback=str(external_feedback or ""),
    entity_registry=_entity_registry,
    protagonist_name=_prot_name,
    protagonist_config=_prot_config,
    director=self.ctx.agents.get("director"),
    state_tracker=getattr(self.ctx, "state_tracker", None),
    db=getattr(self.ctx.current_project, "db", None),
    # prev_manuscripts_text 미전달 (TF-E10)
    # prev_hud 미전달
    # semantic_context 미전달
    # adversarial_self_play 미전달
)
```

### D. BLUEPRINT_PATCH_MODE_PROMPT

```
config/prompts/blueprint_generator.yaml L3-22
```
```
[패치 모드: Blueprint 원본 보존 + 지적사항만 수정]
## 패치 규칙
1. Blueprint의 씬 배분, 감정 곡선, 핵심 장면 구조를 보존
2. Director가 지적한 문제점만 정확히 수정
3. 수정하지 않는 부분은 원본 그대로 유지
4. scene_list 구조(씬 번호, 기본 흐름)를 유지
5. NPC 설정, 세계관, 관계도는 절대 변경 금지
# 전면 재설계하지 마세요. 지적된 부분만 고치세요.
```

### E. 정상 BP 생성 시 V67 모순방지 프롬프트

```
config/prompts/ensemble.yaml L369-378
```
```
### [V67] 모순 방지 - 절대 준수 사항
1. 사망 캐릭터 재등장 금지
2. 이벤트 반복 금지
3. 위치/시간 연속성
4. 아이템/능력 연속성
5. 관계 연속성
6. 정보 연속성
```

### F. PASS_WITH_FIX 실행 루프

```
stage4_interview_round.py L2975-3226
```
- Director verdict PASS_WITH_FIX (score≥90 + MINOR 이슈)
- `chief_writer.inplace_patch()` 최대 3회 호출 (원고 패치)
- 매 패치 후 Director 재심사
- 에스컬레이션과 수정 대상이 다름 (원고 vs 블루프린트)

### G. Director 연속성 검증 (정상 경로에서 실행됨)

```
three_phase_blueprint_generator.py L368-386
```
```python
if director and db and ep_num > 1:
    continuity_result = director.check_blueprint_continuity_with_cache(
        ep_num=ep_num,
        new_blueprint=best_blueprint,
        db=db,
    )
    if continuity_result.get("decision") == "REJECT":
        # 연속성 실패 → 재생성 루프
```

### H. deep-merge 씬 키 복원

```
three_phase_blueprint_generator.py L771-787
```
```python
# 원본 필드 복원 (1-depth)
for key, val in original_blueprint.items():
    if key not in result:
        result[key] = val

# 누락 씬 키 복원
_lost = set(_orig_sb) - set(_result_sb)
if _lost:
    for sk in _lost:
        _result_sb[sk] = _orig_sb[sk]
```

---

*Generated by Opus TF Deep Dive — 2026-03-15, R2*
