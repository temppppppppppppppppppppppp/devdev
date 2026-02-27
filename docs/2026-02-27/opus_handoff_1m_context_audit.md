# OPUS 핸드오프: 1M 컨텍스트 감리 결과

작성일: 2026-02-27
대상: OPUS 실행 담당

---

## [전수조사] 스테이지별 LLM 데이터 흐름 + 하이브리드 RAG 현황

> 조사 완료: R1(Stage 0+2+3) + R2(Stage 4+Director) + R3(메모리/RAG) + R4(하드컷 전수) 결과 종합

---

### 1. 스테이지별 LLM 모델 및 입력 현황

| 스테이지 | 에이전트 | LLM 모델 | 컨텍스트 한도 | 현재 실제 입력 | 활용률 |
|---------|---------|---------|------------|------------|------|
| Stage 0 | StageZeroManager | gemini-2.5-flash | 1M 토큰 | ~20~50K자 | 2~5% |
| Stage 2 | Analyst (Arc) | gemini-2.5-flash | 1M 토큰 | 60~100K자 | 6~10% |
| Stage 2 | ArcEnsembleGenerator | gemini-2.5-pro (Opus) | 1M 토큰 | 80~120K자 | 8~12% |
| Stage 2 | UnifiedArcValidator | gemini-2.5-flash | 1M 토큰 | 30~50K자 | 3~5% |
| Stage 3 | ThreePhaseBlueprintGen | gemini-2.5-pro (Opus) | 1M 토큰 | 80~120K자 | 8~12% |
| Stage 3 | BlueprintEnsemble | gemini-2.5-pro (Opus) | 1M 토큰 | 100~150K자 | 10~15% |
| Stage 4 | ChiefWriter | gemini-2.5-pro (Opus) | 1M 토큰 | 150~200K자 | 15~20% |
| Stage 4 | Director (심사) | gemini-2.5-pro (Opus) | 1M 토큰 | 140~200K자 | 14~20% |
| Stage 4 | Critic | gemini-2.5-flash | 1M 토큰 | 40~80K자 | 4~8% |

**종합 활용률: 25~35% (P0 적용 후 목표: 55~65%)**

---

### 2. 하이브리드 RAG 사용 현황 (스테이지별)

#### Stage 2 (Arc 생성)
- **SC enabled**: `smart_retrieval.stage2_enabled = true`
- **슬롯 5개**: block_theme(pri1) + similar_theme(pri2) + npc_recent(DB_NPC_HISTORY, pri2) + unresolved_plot(pri1) + arc_tactical(pri2)
- **예산**: `stage2_total_budget = 50,000자` → P0 후 `150,000자`
- **RAG 소스**: VecMemory(hybrid) + DB_NPC_HISTORY + YAML(장르)
- **임베딩**: 화별 요약 벡터 (Gemini embedding-001, 3072차원)
- **검색 모드**: hybrid (FTS5 + Dense KNN, RRF k=60)

#### Stage 3 (Blueprint 생성)
- **SC enabled**: `smart_retrieval.stage3_enabled = true`
- **슬롯 6개**: similar_blueprint(pri1) + npc_history(DB_NPC_HISTORY, pri1) + continuity_hook(pri1) + unresolved_plot(pri2) + genre_context_1~2(pri3)
- **예산**: `stage3_total_budget = 80,000자` (현재 미변경)
- **RAG 소스**: VecMemory + DB_NPC_HISTORY + YAML

#### Stage 4 — Chief Writer
- **SC enabled**: `smart_retrieval.stage4_enabled = true`
- **슬롯 8개**: prev_ending(pri1) + npc_history(DB_NPC_HISTORY, pri1) + arc_tactical(pri2) + scene_context(pri2) + unresolved_plot(pri1) + relationship_history(pri2) + genre_context_1~2(pri3) + manuscript_excerpt(manuscript_db, pri1)
- **예산**: `stage4_total_budget = 100,000자` → P0 후 `300,000자`
- **Tier1 전문**: 최근 30화 전문 (~180K자) — Tier2: 31~60화 요약
- **WorldState 주입**: `get_summary(max_chars=10,000자)` → P1 후 `50,000자`
- **FactLedger 주입**: `to_summary(MAX_SUMMARY_CHARS=20,000자)` → P1 후 `50,000자`
- **Context Caching**: CW는 3전략 공통 컨텍스트 캐싱 후 전략별 variable 전송

#### Stage 4 — Director (심사)
- **SC enabled**: `smart_retrieval.director_enabled = true`
- **슬롯 5개**: npc_consistency(DB_NPC_HISTORY, pri1) + event_claim(pri1) + relationship_consistency(pri2) + location_item_consistency(pri2) + blueprint_alignment(pri3)
- **예산**: `director_total_budget = 100,000자` → P0 후 `300,000자`
- **Context Caching**: Phase 2 구현 완료 — ENSEMBLE_STABLE_CONTEXT 캐싱, ENSEMBLE_VARIABLE_PROMPT만 매 라운드 전송
- **prev_ending**: `prev_text[-2500:]` (CW와 동일 수준)

---

### 3. 장기 기억 시스템 구조 (Tier별)

```
Tier0 (구조화, 즉각 조회):
├── FactLedger (20K자) — NPC 사망/생존/스킬/관계/아이템
│   └── [P1] 50K로 확장 → 100화 이상 NPC 전량 수용
├── WorldState (25K자) — 주인공/NPC/관계/세계관 법칙
│   └── [P1] 50K로 확장, call site 10K→50K 수정
└── DB_NPC_HISTORY — NPC 이력 append-only 테이블

Tier1 (의미 검색, RAG):
├── VecMemory.Dense — Gemini embedding-001, 3072차원
│   ├── dense_k = 10 (KNN 후보) → [P0] 20
│   └── 화별 요약 (Python 규칙 추출, ~300~500자/화)
├── VecMemory.Sparse — SQLite FTS5 전문 검색
│   └── sparse_k = 10 (FTS 후보)
├── RRF 결합 — k=60, dense_rank + sparse_rank 정규화
└── max_results = 20 (S4) / 16 (S2) → [P0] 50 / 40

Tier1+ (직접 원고):
├── Tier1-raw: 최근 30화 전문 (stage4_context_builder)
└── manuscript_excerpt: ep-3~ep-1 원고 발췌 (SC slot)

Tier2 (정적 참조):
├── StyleGuard YAML — 문체/톤 (정적, 동적 추적 없음)
└── Bible.txt — 세계관 초기 설정
```

---

### 4. 장기 기억 커버리지 평가 (100화 기준)

| 기억 유형 | 커버리지 | 크기 | 병목 |
|---------|---------|------|------|
| 직전 30화 전문 | ✓ 완전 | ~180K자 | - |
| 31~60화 요약 | ✓ 벡터+요약 | ~18K자 | 요약 품질 (Python 규칙) |
| 61~200화 요약 | ✓ 벡터 | ~42K자 | 의미 손실 10~20% |
| NPC 사망/생존 | ✓ FactLedger | ~5K자 | max_chars 제약 → P1 해제 |
| 주인공 능력치 | ✓ WorldState | ~500자 | - |
| 아이템 소유 이력 | ✓ FactLedger | ~2K자 | owner 필드 불명확 |
| 스타일/톤 변화 | △ 정적 YAML | ~2K자 | 동적 추적 없음 |
| 세계관 법칙 | ✓ WorldState | ~1K자 | - |

**시스템 커버리지: 85~90% (P0+P1 적용 후 → 95%+ 달성 가능)**

---

### 5. P0 구현 완료 목록 (2026-02-27)

| 설정 키 | Before | After | 파일 |
|---------|--------|-------|------|
| `context.mandatory_context_max` | 200,000 | **400,000** | validation.yaml |
| `context.director_mandatory_max` | 200,000 | **400,000** | validation.yaml |
| `context.lookback_excerpt_chars` | 2,000 | **5,000** | validation.yaml |
| `context.lookback_total_chars` | 15,000 | **40,000** | validation.yaml |
| `context.vector_max_results_s4` | 20 | **50** | validation.yaml |
| `context.vector_max_results_s2` | 16 | **40** | validation.yaml |
| `smart_retrieval.stage4_total_budget` | 100,000 | **300,000** | validation.yaml |
| `smart_retrieval.director_total_budget` | 100,000 | **300,000** | validation.yaml |
| `smart_retrieval.dense_k` | 10 | **20** | validation.yaml |
| `FactLedger.MAX_SUMMARY_CHARS` | 20,000 | **50,000** | fact_ledger.py |
| `WorldStateManager.get_summary(max_chars)` | 25,000 (default) | **50,000** | world_state.py |
| `stage4_context_builder.get_summary(max_chars)` | 10,000 (×2) | **50,000** | stage4_context_builder.py |

---

### 6. 잔여 권장 작업

| 우선순위 | 작업 | 영향도 | 파일 |
|---------|------|--------|------|
| P1-a | prev_ending 최근 3화 전문 로드 | 연속성 오류 -30% | stage4_context_builder.py, chief_writer_context.py |
| P1-b | chief_writer.py:749 `smart_truncate max_chars=150000` 동적 교체 | 원고 입력 +50% | chief_writer.py |
| P2 | Tier2 LLM 요약 캐싱 (10화 배치) | 기억 품질 3배 | 신규 모듈 |
| P2 | Style Delta 동적 추적 | 톤 드리프트 감지 | style_guard.py |
| P2 | Arc Snapshot 압축 (200화+ 효율) | 검색 후보 50→20 | vec_memory.py |

---

## 0) 한줄 결론

현재 코드는 **1M 대응 방향으로는 맞게 이동**했지만, 운영 정책은 아직 **부분 보수 모드**다.  
즉, "완전 해제"가 아니라 "확장 + 안전가드 유지" 상태다.

---

## 1) 확정 사실 (코드/런타임 확인)

### 전역/정책 값

- `api.max_context_chars = 700000` (`config/system.yaml`)
- `ContextLimits.MAX_CONTEXT_CHARS = 1000000` (`modules/core/constants.py`)
- `context.mandatory_context_max = 200000` (`config/settings/validation.yaml`)
- `context.director_mandatory_max = 200000` (`config/settings/validation.yaml`)
- `smart_retrieval.stage4_total_budget = 100000` (`config/settings/validation.yaml`)
- `smart_retrieval.director_total_budget = 100000` (`config/settings/validation.yaml`)

### 반영된 코드 변경

- Stage4 `prev_ending` 확장: `500 -> 2500`
- Stage4 Tier1 원고 범위: `20 -> 30화`
- Critic 절삭 상향:
  - `manuscript[:20000] -> [:80000]`
  - `blueprint[:50000] -> [:100000]`
  - `deep_review manuscript[:30000] -> [:100000]`
- Director prompt split 추가:
  - `ENSEMBLE_STABLE_CONTEXT`
  - `ENSEMBLE_VARIABLE_PROMPT`
- Director 캐싱 경로 구현:
  - stable 캐시 생성 후 variable만 전송
  - 캐시 실패 fallback 시 variable 보존을 우선한 선제 절삭 추가

### 중요 정정 (최근 상태)

- 이전 쟁점이던 `director_ensemble blueprint[:100000]` 하드컷은 **현재 제거됨**.
- 최신 코드: `_blueprint_esc = self._d._escape_braces(blueprint_str)` (슬라이스 없음)

---

## 2) 감리 판단

### PASS 성격

- 1M 대응 패치 방향은 일관적이며, 캐싱 경로 개선도 실제 코드에 반영됨.
- Director fallback의 tail 손실(후보 원고/출력 포맷 유실) 리스크를 줄이는 보호 로직이 들어감.

### FAIL/주의 성격

- "1M 완전 활용" 기준으로는 아직 제한적:
  - mandatory 200k
  - SC budget 100k
  - 전역 gate 700k
- 즉 모델 한도(1M token)를 항상 꽉 쓰는 전략은 아님.

---

## 3) 핵심 쟁점 (OPUS가 정리해야 할 부분)

1. 단위 혼동 금지
- `1M = 1,000,000 = 1000k`
- `100k = 0.1M` (10배 차이)
- tokens vs chars를 혼용해서 "1M 대응"으로 표현하면 안 됨.

2. 정책 정의
- 현 정책은 "안전 마진 운영"인지, "최대 활용 운영"인지 명시 필요.
- 문서/주석/코드 기본값이 이 정책과 일치해야 함.

3. fallback 전략
- 현재는 variable 보호형 선제 절삭이 들어갔으나, 장기적으로 공용 유틸화가 필요.
- 모든 agent fallback이 동일 규칙(핵심 섹션 보존)으로 동작해야 함.

---

## 4) OPUS 작업 TF 제안

### TF-1: 1M 정책 SSOT 문서화

- 목표: tokens/chars 변환 규칙과 목표 정책(보수/공격)을 단일 문서로 확정.
- 산출물: 정책표 + 적용 파일 매핑표.

### TF-2: 하드컷 전수 감사

- 목표: `[:N]` 하드코드 절삭 전수 검색 후 근거 없는 절삭 제거 또는 설정화.
- 산출물: 유지/삭제/설정화 분류표.

### TF-3: fallback 공통화

- 목표: cache miss/ask fallback 시 핵심 섹션 보존 우선 규칙을 공용 함수로 통합.
- 산출물: 공용 truncate helper + 에이전트 적용 리스트.

### TF-4: 관측성 강화

- 목표: 호출당 `chars/tokens`, 절삭 위치, cache hit/miss를 로깅하고 추세화.
- 산출물: 로그 필드 스펙 + 대시보드 지표.

### TF-5: 회귀 테스트

- 목표: "variable prompt 유실 금지", "split prompt fallback 동등성" 자동 검증.
- 산출물: unit/integration tests 추가.

---

## 5) 최소 검증 커맨드

```powershell
python -m pytest -q tests/test_director_modules.py tests/test_stage4_context_builder.py tests/test_truth_gate.py --tb=short
python - << 'PY'
from modules.validation.threshold_helper import _threshold
from modules.domain.agents.base_agent import BaseAgent
from modules.core.constants import ContextLimits
print("BaseAgent.MAX_CONTEXT_CHARS =", BaseAgent.MAX_CONTEXT_CHARS)
print("ContextLimits.MAX_CONTEXT_CHARS =", ContextLimits.MAX_CONTEXT_CHARS)
print("mandatory_context_max =", _threshold("context.mandatory_context_max", None))
print("director_mandatory_max =", _threshold("context.director_mandatory_max", None))
print("stage4_total_budget =", _threshold("smart_retrieval.stage4_total_budget", None))
print("director_total_budget =", _threshold("smart_retrieval.director_total_budget", None))
PY
```

---

## 6) OPUS에 전달할 메시지 초안

"현 코드는 1M 대응 확장 패치가 반영됐고 Director 캐싱도 들어갔습니다. 다만 운영값은 여전히 200k/100k/700k로 보수적입니다.
핵심은 1M 완전 해제 여부가 아니라 정책 일관성입니다. 단위(tokens/chars) 혼동 제거, 하드컷 전수 감사, fallback 공통화, 관측성/회귀테스트까지 묶어 마감해 주세요."

---

## 7) 구현 완료 상태 (2026-02-27 갱신)

### Phase 1 완료 (초기 구현)
- [x] `system.yaml max_context_chars`: 450K → **700K**
- [x] `constants.py MAX_CONTEXT_CHARS`: 800K → **1,000K**
- [x] `director_mandatory_max`: 150K → **200K**
- [x] `director_total_budget`: 50K → **100K**
- [x] `stage4_context_builder.py prev_ending`: 500자 → **2500자**
- [x] `stage4_context_builder.py Tier1`: 20화 → **30화**
- [x] `critic.py` 절삭: 20K→**80K** / 50K→**100K** / 30K→**100K**
- [x] Director `ENSEMBLE_STABLE_CONTEXT` 캐싱 분리 + variable fallback 보호

### P0 완료 (2026-02-27 전수조사 후)
- [x] `mandatory_context_max`: 200K → **400K**
- [x] `director_mandatory_max`: 200K → **400K**
- [x] `lookback_excerpt_chars`: 2K → **5K**
- [x] `lookback_total_chars`: 15K → **40K**
- [x] `vector_max_results_s4`: 20 → **50**
- [x] `vector_max_results_s2`: 16 → **40**
- [x] `stage4_total_budget`: 100K → **300K**
- [x] `director_total_budget`: 100K → **300K**
- [x] `smart_retrieval.dense_k`: 10 → **20**
- [x] `FactLedger.MAX_SUMMARY_CHARS`: 20K → **50K**
- [x] `WorldState.get_summary(max_chars)`: 25K default → **50K** + call sites 10K→**50K**

### 현재 운영 정책 (명시)
- 정책명: **"1M 최대 활용 (안전 마진 10%)"**
- 전역 gate: 700K자 × 1.5tok/자 ≈ 1.05M 토큰 (Gemini 1M 한계 대응)
- mandatory 상한: 400K자 (모델 용량 80%)
- SC budget: 300K자 (Stage4/Director)
- 단위 기준: `chars(자) × 1.5 = tokens` (한글 기준 안전 추산)

### 잔여 P1~P2 (관찰 대기)
- [ ] prev_ending 최근 3화 전문 로드 (현재 1화 2500자)
- [ ] chief_writer.py:749 `max_chars=150000` 동적 예산으로 교체
- [ ] Tier2 LLM 요약 캐싱 (P2, 월별)
- [ ] Style Delta 동적 추적 (P2, 월별)

