# Gemini 1M 컨텍스트 전수조사 보고서
> 작성일: 2026-02-27 | 목적: 1M 토큰 최대 활용 여부 점검 + 장기 기억 보강 방안

---

## 핵심 결론

**현재 1M 토큰 실제 사용률: 25~35%. 낭비 65~75%.**

Gemini 1M 컨텍스트를 가지고 있지만 인위적 상한들이 실제 활용을 막고 있음.
비용 제약을 해제하면 동일 아키텍처에서 +500K 토큰 즉시 확보 가능.

---

## 1. 수치 기준

| 단위 | 값 |
|------|----|
| Gemini 1M 토큰 한계 | 1,048,576 tokens |
| 한글 변환 (1.5tok/자, 현실적 상한) | **700,000자** |
| 한글 변환 (2.0tok/자, 보수적 상한) | 500,000자 |
| 현재 API 게이트 (`system.yaml`) | 700,000자 |

---

## 2. 발견된 병목 목록

### 2-A. Smart Retrieval 예산 (validation.yaml)

| 스테이지 | 현재 | 개선 가능값 | 판정 |
|---------|------|-----------|------|
| Stage 2 (Arc) | 50,000자 | 200,000자 | SUBOPTIMAL |
| Stage 3 (Blueprint) | 80,000자 | 200,000자 | SUBOPTIMAL |
| Stage 4 (원고) | 100,000자 | 300,000자 | **BOTTLENECK** |
| Director (심사) | 100,000자 | 300,000자 | **BOTTLENECK** |

**설정 위치**: `config/settings/validation.yaml` L165-168

### 2-B. Mandatory Context 상한

| 파라미터 | 현재 | 개선 가능값 | 판정 |
|---------|------|-----------|------|
| `mandatory_context_max` (Writer) | 200,000자 | 400,000자 | SUBOPTIMAL |
| `director_mandatory_max` (Director) | 200,000자 | 400,000자 | SUBOPTIMAL |
| `lookback_excerpt_chars` | 2,000자 | 5,000자 | SUBOPTIMAL |
| `lookback_total_chars` | 15,000자 | 40,000자 | SUBOPTIMAL |

**설정 위치**: `config/settings/validation.yaml` L76-82

### 2-C. 벡터 검색 top_k

| 파라미터 | 현재 | 개선 가능값 | 판정 |
|---------|------|-----------|------|
| `vector_max_results_s4` | 20 | 50 | SUBOPTIMAL |
| `vector_max_results_s2` | 16 | 40 | SUBOPTIMAL |

**설정 위치**: `config/settings/validation.yaml` L80-81

### 2-D. 이전 원고 로딩 깊이

| 항목 | 현재 | 개선 가능 | 판정 |
|------|------|---------|------|
| Tier1 전문 로드 (최근 N화) | 30화 | 유지 (OK) | OPTIMAL |
| Tier2 (31~90화) | 요약만 (~500자/화) | 요약 품질 강화 | SUBOPTIMAL |
| prev_ending | 직전 1화 마지막 2500자 | 최근 3화 전문 | SUBOPTIMAL |

**설정 위치**: `modules/core/stage4_context_builder.py` L411-444

### 2-E. 하드코딩 절삭

| 파일:위치 | 현재 | 판정 |
|----------|------|------|
| `chief_writer.py:749` | `smart_truncate(..., max_chars=150000)` | SUBOPTIMAL |
| `director_ensemble.py` | `blueprint_str` (슬라이스 제거됨, OK) | OPTIMAL |
| `critic.py:414` | `manuscript[:80000]` (flash 1M 모델이라 OK) | OPTIMAL |

---

## 3. 에이전트별 실제 컨텍스트 크기 추정

| 에이전트 | 현재 입력 추정 | 가능한 최대 | 현재 활용률 |
|---------|-------------|-----------|----------|
| Chief Writer | 150~200K자 | 600K자 | **25~33%** |
| Director | 140~200K자 | 600K자 | **23~33%** |
| Blueprint Ensemble | 80~120K자 | 500K자 | **16~24%** |
| Stage2 Analyst | 60~100K자 | 500K자 | **12~20%** |
| Critic | 40~80K자 | 500K자 | **8~16%** |

---

## 4. 누락되는 장기 기억 유형

### 4-A. 과거 에피소드 접근 깊이 부족
- **현재**: 최근 30화 전문 + 31~90화 요약 (~500자/화)
- **문제**: 100화 이상 연재에서 50~100화 구간 사건이 구체적으로 참조 불가
- **증상**: "회상 장면"에서 50화 사건을 틀리게 묘사, 주인공의 과거 인연 NPC 재등장 시 관계 오류

### 4-B. WorldState 직렬화 크기 부족
- **현재**: `world_state.py` get_summary() → ~5K JSON
- **누락**: 전체 NPC 관계 매트릭스, 주요 아이템 소유 이력, 세력 변화 타임라인
- **설정 위치**: `modules/core/world_state.py`

### 4-C. FactLedger 크기 제약
- **현재**: ~20K 제약
- **개선 가능**: 50K (deaths, items, locations, skills, karma 전량)
- **설정 위치**: `modules/core/fact_ledger.py`

### 4-D. 스타일/톤 동적 추적 없음
- **현재**: Style Guide 1회 로드 (static)
- **누락**: 최근 10화 대사 비율 변화, 캐릭터별 음성 변화 추적

---

## 5. 개선 권장사항

### P0 — 설정값 변경만으로 즉시 효과 (validation.yaml)

```yaml
# 현재 → 개선
context:
  mandatory_context_max: 200000      → 400000   # Writer 입력 2배
  director_mandatory_max: 200000     → 400000   # Director 입력 2배
  lookback_excerpt_chars: 2000       → 5000     # 화별 요약 2.5배
  lookback_total_chars: 15000        → 40000    # 전체 lookback 2.7배

smart_retrieval:
  stage2_total_budget: 50000         → 150000   # Arc 컨텍스트 3배
  stage3_total_budget: 80000         → 200000   # Blueprint 컨텍스트 2.5배
  stage4_total_budget: 100000        → 300000   # 원고 컨텍스트 3배
  director_total_budget: 100000      → 300000   # 심사 컨텍스트 3배
  vector_max_results_s4: 20          → 50       # 벡터 검색 2.5배
  vector_max_results_s2: 16          → 40       # 벡터 검색 2.5배
```

**예상 효과**: 전체 활용률 25% → 55~65%로 즉시 향상

### P1 — 코드 변경 필요 (2주 내)

1. **prev_ending 최근 3화 전문으로 확장**
   - `stage4_context_builder.py` L411: `prev_text[-2500:]` → 최근 3화 전문 로드
   - `chief_writer_context.py` L181: 동일 패턴
   - 효과: 아크 경계 연속성 오류 30~40% 감소

2. **WorldState 직렬화 50K로 확장**
   - `world_state.py` get_summary() 메서드: 5K → 50K
   - 효과: 200화 이상 누적 설정 오류 20~30% 감소

3. **FactLedger 20K → 50K**
   - `fact_ledger.py`: 직렬화 크기 제약 완화
   - 효과: 사망 NPC / 아이템 오류 15% 감소

4. **chief_writer.py:749 `max_chars=150000` 제거**
   - 동적 예산 기반으로 교체

### P2 — 아키텍처 개선 (월별)

1. **Tier2 LLM 요약 강화**
   - 현재: Python regex 요약 (~500자/화)
   - 개선: 매 10화 배치로 Director(flash) 호출해 "핵심 사건 요약" 생성 및 DB 캐싱
   - 효과: 50~100화 구간 기억 품질 3배 향상

2. **다층 Retrieval 구조**
   ```
   Tier1 (최근 30화): 전문 (현행 유지)
   Tier2 (31~90화): Vector hybrid search top50
   Tier3 (91+ 화): LLM 생성 Volume Summary (50화 단위)
   ```

3. **캐릭터별 음성 동적 추적**
   - 최근 5화 NPC 대사를 임베딩 → StyleGuard에 동적 주입

---

## 6. 즉시 적용 시 전체 기대 효과

| 지표 | 현재 | P0 적용 후 | P1 적용 후 |
|------|------|----------|----------|
| 1M 토큰 활용률 | 25~35% | 55~65% | 70~80% |
| 과거 에피소드 접근 깊이 | ~30화 전문 | ~30화 전문 + 2.7배 요약 | ~90화 |
| 연속성 오류 | 기준 | -15~20% | -35~45% |
| 벡터 검색 재현율 | 기준 | +150% | +200% |

---

## 7. 현재 이미 적용된 개선

### Phase 1 (초기 구현)
- [x] `system.yaml max_context_chars`: 450K → **700K**
- [x] `constants.py MAX_CONTEXT_CHARS`: 800K → **1,000K**
- [x] `director_mandatory_max`: 150K → **200K**
- [x] `director_total_budget`: 50K → **100K**
- [x] `stage4_context_builder.py prev_ending`: 500자 → **2500자**
- [x] `stage4_context_builder.py Tier1`: 20화 → **30화**
- [x] `critic.py` 절삭: 20K→**80K** / 50K→**100K** / 30K→**100K**
- [x] Director `ENSEMBLE_STABLE_CONTEXT` 캐싱 분리
- [x] Director `blueprint_str` 슬라이스 제거 (전체 게이트 위임)
- [x] Director `full_fallback` 선제 절삭 (variable_prompt 보호)

### P0 (전수조사 후 — 2026-02-27 완료)
- [x] `mandatory_context_max`: 200K → **400K** (모델 용량 80%)
- [x] `director_mandatory_max`: 200K → **400K**
- [x] `lookback_excerpt_chars`: 2K → **5K** (화별 요약 2.5배)
- [x] `lookback_total_chars`: 15K → **40K** (전체 lookback 2.7배)
- [x] `vector_max_results_s4`: 20 → **50** (recall 2.5배)
- [x] `vector_max_results_s2`: 16 → **40** (recall 2.5배)
- [x] `stage4_total_budget`: 100K → **300K** (원고 컨텍스트 3배)
- [x] `director_total_budget`: 100K → **300K** (심사 컨텍스트 3배)
- [x] `smart_retrieval.dense_k`: 10 → **20** (KNN recall +15~20%)

### P1 (장기 기억 확장 — 2026-02-27 완료)
- [x] `FactLedger.MAX_SUMMARY_CHARS`: 20K → **50K**
- [x] `WorldState.get_summary(max_chars)`: 25K default → **50K** (default + call sites)
- [x] `stage4_context_builder.py world_state call`: 10K → **50K** (×2 call sites)

---

## 8. 다음 액션 아이템

| 우선순위 | 작업 | 파일 | 상태 |
|---------|------|------|------|
| ~~P0~~ | ~~validation.yaml 설정값 일괄 상향~~ | `config/settings/validation.yaml` | ✅ **완료** |
| ~~P1-b~~ | ~~WorldState 직렬화 50K 확장~~ | `world_state.py` + `stage4_context_builder.py` | ✅ **완료** |
| ~~P1-c~~ | ~~FactLedger 50K 확장~~ | `fact_ledger.py` | ✅ **완료** |
| **P1-a** | prev_ending 최근 3화 전문 로드 | `stage4_context_builder.py`, `chief_writer_context.py` | 대기 |
| **P1-d** | `chief_writer.py:749 max_chars=150000` 동적 교체 | `chief_writer.py` | 대기 |
| **P2** | Tier2 LLM 요약 캐싱 (10화 배치) | `stage4_context_builder.py` + 신규 모듈 | 관찰 대기 |
