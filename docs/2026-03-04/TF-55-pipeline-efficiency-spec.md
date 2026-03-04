# TF-55: 파이프라인 효율성 개선

> **상태**: 미구현 (스펙 확정 — 재감사 완료, TF-55a 비활성화 방침 원복)
> **작성일**: 2026-03-04
> **근거**: 로그 분석 + `feature-activation-audit-result.md` + `code-verification-result.md` + `advisory-reaudit-result.md`
> **원칙**: 코드 수정 전 각 TF별 보류 조건 재확인

---

## 배경 요약

로그 분석에서 발견된 비효율 3건 + Codex 감사로 확장된 2건.
자세한 근거: `TF-54-writing-directive-spec.md § 11`, `feature-activation-audit-result.md`

| ID | 비효율 | 에피소드당 낭비 | 확인 상태 |
|----|--------|--------------|----------|
| INEFF-1 | Advisory 7개 모듈 중 5개 발화 0건, 2개만 실발화 | LLM 호출 소모 | ✅ **재감사 확정 (→ 마커 기준, 번복 0건)** |
| INEFF-2 | VecMemory 히트율 0% 쿼리 8종 매번 실패 | 벡터 검색 8회 + fallback_entry | ✅ **Codex 감사 확정** |
| INEFF-3 | Director-CACHE 항상 MISS (stable < 50K자, 초반 화) | full_fallback 57K~62K자 전송 | ✅ 구조 확인 (초반 화 불가피) |

**Codex 감사 핵심 수치:**
- Advisory 발화 건수: FlashbackVerifier 6건, InfoParadoxChecker 4건, 나머지 5개 모듈 0건 **(→ 마커 재감사 완료, 번복 0건 — 0건 확정)**
- VecMemory hits=0 쿼리: **8종** (장르맥락×2, 아크전술×2, 관계이력×2, 씬쿼리×2)
- 1차 합격률: 전체 80.00%, 구간별 83.33% / 72.73% / 83.33%
- Director response_len=2: 13건 / 75건 (17.33%), 전량 1K~5K 구간에서 발생

**코드 검증 (`code-verification-result.md`) + 재감사 (`advisory-reaudit-result.md`):**
- 5개 모듈 로그 마커 전량 `→` (U+2192) 사용. 최초 감사 검색어 `->` (ASCII)와 불일치.
- `→` 마커 재감사 결과: 5개 모듈 전량 **0건 유지** (번복 0건).
- 마커 불일치는 검색 오류였으나, 발화 0건 판정 자체는 정확했다.
- **TF-55a 비활성화 방침 원복. 구현 진행 가능.**

---

## TF-55a: Advisory 0건 모듈 비활성화 ✅ **비활성화 확정**

### 재감사 결과 요약 (`advisory-reaudit-result.md`)

Advisory chain 7개 모듈, 8개 세션 전수 집계 (`→` U+2192 마커 기준):

| 모듈 | 발화 건수 | 실행 가능 화수 | Guard 0건 가능성 | 처리 방향 |
|------|---:|---:|---|------|
| FlashbackVerifier | **6** | 전 화수 | 없음 | 유지 |
| InfoParadoxChecker | **4** | 전 화수 | 없음 | 유지 |
| NpcDriftAdvisor | **0** | 전 화수 | 없음 | **비활성화** |
| TruthGate | **0** | 전 화수 | 없음 | **비활성화** |
| RelationshipDriftAdvisor | **0** | 5~25화 (21화) | 있음 | **비활성화** |
| LongTermRepetitionAdvisor | **0** | 20~25화 (6화) | 있음 | **비활성화** |
| NumericDriftAdvisor | **0** | 5·10·15·20·25화 (5회) | 있음 | **비활성화** |

NpcDriftAdvisor·TruthGate는 에피소드 Guard 없음에도 0건 → 내부 Guard(원고/스냅샷/LLM 주입 여부) 차단으로 추정.

### 주요 경과

1. Feature Activation Audit (`->` ASCII 검색): 5개 모듈 0건
2. 코드 검증: 실제 마커가 `→` (U+2192) — 검색 오류 가능성 제기
3. 재감사 (`→` 마커 재검색): **5개 모듈 전량 0건 유지, 번복 0건**
4. 결론: 마커 불일치는 검색 오류였으나 0건 판정 자체는 정확

### 플래그 비활성화 방식

```yaml
# config/settings/validation.yaml 추가
advisory_chain:
  npc_drift: false
  truth_gate: false
  rel_drift: false
  long_term_rep: false
  numeric_drift: false
  flashback: true
  info_paradox: true
```

코드에서는 플래그 로드 후 `executor.submit()` 호출 여부만 분기.
모듈 파일 삭제 금지 — 플래그로만 제어.

### 변경 파일

| 파일 | 변경 내용 | 줄 수 변화 |
|------|----------|-----------|
| `config/settings/validation.yaml` | advisory_chain 활성화 플래그 7개 추가 | +8줄 |
| `modules/core/stage4_interview_round.py` | `_run_advisory_chain()` 플래그 체크 분기 추가 | L1691~1698, ~14줄 수정 |

---

## TF-55b: VecMemory hits=0 쿼리 3종 → DB/정적 주입 전환

### 현재 동작

`context_advisor.py:_build_stage4_slots()` 에서 3개 슬롯이 벡터 검색으로 생성:

```
슬롯 "arc_tactical"       → q='아크 전술 연속성: {tactical_doc[:320]}'  hits=0 매번
슬롯 "relationship_history" → q='관계 변화 이력: {npc_pair_names}'      hits=0 매번
슬롯 "genre_context_1/2"  → q='장르 맥락 키워드: {GENRE_HINTS phrase}'  hits=0 매번
```

### 근본 원인 (슬롯별)

**arc_tactical**: `tactical_doc`은 Arc 생성 시 DB에 저장되지만, VecMemory에는 임베딩이 없음.
쿼리 텍스트가 "아크 전술 연속성: [전체 전술 문서 320자]"로 너무 길어
임베딩 유사도가 0에 수렴. → 벡터 검색 자체가 의미 없음.
**데이터가 이미 context_data에 있는데 벡터로 검색하는 구조적 오류.**

**relationship_history**: NPC 관계 이력은 `npc_relationship_history` 테이블(SQLite)에 있음.
VecMemory에는 관계 이력 임베딩이 없음. → DB를 직접 조회해야 하는 데이터.

**genre_context**: `_GENRE_HINTS[genre]`는 Python 딕셔너리에 하드코딩된 키워드 목록.
VecMemory에 저장된 적 없음. → 벡터 검색 자체가 불가능한 데이터.

### 개선 방향

3개 슬롯의 `source`를 벡터 검색 → 직접 주입/DB 조회로 전환.

#### arc_tactical 슬롯

```python
# context_advisor.py:486 현재
slots.append(RetrievalSlot("arc_tactical", f"아크 전술 연속성: {tactical[:320]}", priority=2))

# 개선: RetrievalSources.STATIC 또는 새로운 source="direct" 추가
# VecMemory 검색을 건너뛰고 tactical_doc 원문을 직접 컨텍스트에 삽입
```

또는 더 간단히: 해당 슬롯을 제거하고, stage4_context_builder에서
`arc_data["tactical_doc"]`를 CW 컨텍스트에 직접 주입 (이미 다른 경로로 주입 중인지 확인 필요).

#### relationship_history 슬롯

```python
# 현재: 벡터 검색 (hits=0)
# 개선: source=RetrievalSources.DB_NPC_RELATIONSHIP 추가
#        실행 시 db.get_npc_relationship_history(npc_names, limit=10) 직접 호출
```

`RetrievalSources`에 `DB_NPC_RELATIONSHIP = "db_npc_relationship"` 추가.
VecMemory 실행기에서 이 source를 처리하는 분기 추가.

#### genre_context 슬롯

```python
# 현재: 벡터 검색 (hits=0)
# 개선: source=RetrievalSources.STATIC으로 변경
#        STATIC source는 query 텍스트 자체를 결과로 그대로 반환
```

`RetrievalSources.STATIC` 이미 있는지 확인 필요. 없으면 추가.

### 변경 파일

| 파일 | 변경 내용 | 줄 수 변화 |
|------|----------|-----------|
| `modules/core/context_advisor.py` | L486/504/507~508 슬롯 source 변경 | ~10줄 수정 |
| `modules/core/vec_memory.py` | STATIC/DB_NPC_RELATIONSHIP source 처리 분기 추가 | +20~30줄 |
| `modules/core/db_manager.py` | `get_npc_relationship_history()` 존재 여부 확인 (기존 메서드 재사용) | 수정 없음 가능성 높음 |

### 예상 효과

- 벡터 검색 API 3회/에피소드 제거
- `fallback_entry n=50` (DB 전체 스캔) 3회 제거
- 관계 이력이 실제 DB 값으로 정확히 주입됨 (품질 향상 부수효과)

### Codex 감사 결과 반영 — 범위 확장

최초 3종 → **8종**으로 확장 확정. 전 세션 일관 0%:

| 쿼리 타입 | 미스 건수 | 히트율 |
|----------|---:|---:|
| 장르 맥락 키워드: 포트폴리 | 7 | 0.00% |
| 장르 맥락 키워드: 레버리지 | 7 | 0.00% |
| 아크 전술 연속성: [제 1 | 5 | 0.00% |
| 관계 변화 이력: 한정호, | 5 | 0.00% |
| 장면1: 한미증권을 나선 한 | 2 | 0.00% |
| 아크 전술 연속성: 제 5화 | 2 | 0.00% |
| 관계 변화 이력: 박성호 | 2 | 0.00% |
| 장면1: 한시우가 다이닝룸에 | 1 | 0.00% |

참고: `한시우 한정호 한태준 한태민` 쿼리는 92.31% 히트 → 유지.

씬 쿼리 (`장면1:`) 2종은 `_build_scene_query(blueprint)` 에서 생성.
arc_tactical과 동일하게 context_data에 이미 있는 데이터를 벡터로 찾는 구조.
→ 55b 범위에 포함.

---

## TF-55c: Director-CACHE 10화+ 실측 검증

### 현재 상황

- `_MIN_CACHE_CONTENT = 50,000자` (default, settings.json에 미설정)
- 1~5화 stable_context: 18K~25K자 → 50K 미달 → `content_too_short` 즉시 반환
- Gemini Context Caching API 최소 요건: ~32,768 토큰 ≈ 40K자(한국어)
- **초반 화(1~5)는 구조적으로 캐시 불가, 피할 수 없음**

### 검증 필요 사항

10화 이상 연속 실행 시:
- stable_context(이전 원고 누적)가 50K를 넘는 화가 어디서부터인가
- 그 화에서 실제로 `[CTX-CACHE] HIT` 로그가 발생하는가
- HIT 발생 시 전송 토큰이 실제로 줄어드는가

### 조치

코드 수정 없음. **운영 관찰만.**
10화 이상 파이프라인 실행 후 로그에서 확인:

```
grep "CTX-CACHE\|Director-CACHE" session_*.log
```

HIT가 발생하지 않는다면 `_MIN_CACHE_CONTENT` 값 조정 또는
stable_context 구성 방식(무엇을 stable로 볼 것인가) 재검토.

---

## 구현 순서

```
[→ 마커 재감사 (Codex 오더)]
       │
       ├─ 0건 확인 → TF-55a (플래그 비활성화) 진행
       └─ 발화 있음 → TF-55a 폐기

TF-55b (VecMemory 8종 전환)   ← 재감사와 독립, 지금 진행 가능
       │
TF-55c (Director-CACHE 검증)   ← 코드 수정 없음, 운영 관찰
```

55b는 재감사 결과와 무관하게 진행 가능 → 먼저 진행 권장.
55a는 재감사 완료 후 방향 확정 → 보류.

---

## 테스트 계획

### TF-55a

보류 — 재감사 완료 후 방향 확정 시 작성.

비활성화 방향 확정 시 예상 테스트:
```python
# tests/test_stage4_interview_round.py 추가
def test_advisory_chain_skips_disabled_modules():
    """validation.yaml 플래그 false 시 executor.submit() 미호출 검증."""

def test_advisory_chain_flag_default_true():
    """플래그 미설정 시 기본값 true (기존 동작 유지) 검증."""
```

### TF-55b

```python
# tests/test_context_advisor.py 추가
def test_arc_tactical_slot_no_vector_search():
    """arc_tactical 슬롯이 벡터 검색을 호출하지 않는지 검증."""

def test_relationship_history_slot_uses_db():
    """relationship_history 슬롯이 DB 직접 조회를 사용하는지 검증."""

def test_genre_context_slot_static():
    """genre_context 슬롯이 STATIC source로 즉시 반환하는지 검증."""
```

---

## 변경 범위 요약

| TF | 변경 파일 수 | 신규 줄 | 수정 줄 | 리스크 |
|----|------------|--------|--------|--------|
| 55a | 2 | ~8 | ~14 | Low (플래그 체크, 로직 변경 없음) — **재감사 후 확정** |
| 55b | 2~3 | ~30 | ~10 | Low (슬롯 source 변경, 기존 로직 유지) |
| 55c | 0 | 0 | 0 | None |

---

## 미결 항목

- [x] NpcDriftAdvisor 25화 발화 건수 집계 완료 (Codex 감사: 0건)
- [x] 다른 advisory 발화 건수 집계 완료 (TruthGate/RelDrift/LongTermRep/NumericDrift 0건)
- [x] VecMemory hits=0 쿼리 전 세션 일관성 → **8종 전량 0%** → 55b 범위 확정
- [x] 합격률 구간 비교 → 11~20화 72.73%로 소폭 하락
- [x] 로그 마커 불일치 여부 → **5개 모듈 전량 `→`(U+2192) 사용, 감사 `->` 검색과 불일치** (코드 검증 완료)
- [x] 씬 쿼리 소스 경로 → **`_build_scene_query()` 단일 경로, source=VEC_MEMORY 기본값** (코드 검증 완료)

- [x] `→` 마커 재감사 완료 → 5개 모듈 0건 확정 (`advisory-reaudit-result.md`)
- [x] TF-55a 비활성화 방침 확정
