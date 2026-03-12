# TF-OPT 전수조사: 효율화·인프라·스케일링 잔여 개선 경로

> 작성: 2026-03-10
> 상태: 실행 완료 (OPT-1/OPT-3 구현 완료, OPT-2 deferred 유지, 전체 pytest/ruff 통과)
> 전제: TF-DB(DB 활용) + Beyond-DB(DB 외 3대 방향) + TF-QR(잔여 퀄리티) 3개 문서에 **없는** 항목만 수록
> 방법: Context Caching → Advisory 체인 → 장기연재 → A/B 인프라 → 회귀 탐지 5개 영역 병렬 전수조사 → 코드 검증 → 6pass 오탐/과장 제거

---

## 공통 원칙

- 기존 동작 불변 — 성능/비용 최적화만, 기능 변경 금지
- LLM 호출 추가 0회
- 테스트 회귀 0건

---

## 오탐/사실 교정 기록

| 초기 후보 | 판정 | 근거 |
|-----------|------|------|
| Advisory 체인 병렬화 | **오탐** | `ThreadPoolExecutor(max_workers=8)` + `as_completed(timeout=300)` **이미 구현** (`stage4_interview_round.py` L2330-2367). 8개 advisory 동시 실행, per-advisory timeout=60s. 순차 대비 ~4-5x 빠름. |
| Context Caching 2개만 사용 | **오탐** | 실제 **5개 에이전트** 사용 중: ChiefWriter(L265), ArcEnsemble(L265), BprintEnsemble(L204), DirectorEnsemble(L772), DirectorContinuity(L653/L767). CLAUDE.md 부정확 → 수정 완료. |
| Blueprint-Aware Truncation 전면 부재 | **사실 교정** | `stage4_context_builder.py`에 `_extract_blueprint_entities()` + `Continuity Packet` + condensed WorldState/FactLedger 요약이 **이미 존재**. 현재 잔여 갭은 `get_summary()/to_summary()` 범용 whitelist API 부재와 `blueprint full_text` 중심 entity 추출의 edge case다. |

> **CLAUDE.md 수정 2건 반영 완료**:
> 1. Context Caching: "2개 에이전트" → "5개 에이전트" (chief_writer·arc_ensemble·blueprint_ensemble·director_ensemble·director_continuity)
> 2. Advisory 체인: "ThreadPoolExecutor(max_workers=8)로 병렬 실행" 명시 추가

---

## OPT-1. Context Caching 확장 — Analyst 미적용

**현황**:
- `base_agent.py` L1599-1820: `_get_or_create_context_cache()` + `_ask_with_cached_context()` 인프라 완비
- Gemini Context Caching API 기반, 최소 50,000자(~32K 토큰) 이상 시 캐시 생성
- 캐시 사용 시 **90% 토큰 할인** (10% 비용만 과금)
- **5개 에이전트 적용 완료**: ChiefWriter, ArcEnsemble, BprintEnsemble, DirectorEnsemble, DirectorContinuity

**미적용 에이전트**:
- `analyst.py`: **10+ `self.ask()` 호출** (L199, 846, 920, 1170, 1187, 1261, 1368, 1449, 1460)
- Treatment 템플릿 + world_origin + protagonist_config 등 **반복 컨텍스트 ~20-48K자**
- 현재: 매 호출마다 전체 프롬프트 재전송

**갭**: Arc 생성 1회당 Analyst가 10회 LLM 호출. 동일 Treatment/설정 컨텍스트를 10회 중복 전송. 단, **stable_context가 50K 이상인 프로젝트에서만 캐시 생성** — Treatment가 짧은 프로젝트에서는 min_content_chars 미달로 캐시 스킵됨.

**⚠️ 50K 미달 가능성**: Analyst stable_context 구성 = structured_context(5~10K) + previous_volumes(10~20K) + target_blocks(5~15K) + protagonist_config(~0.3K). 하한 ~20K, 상한 ~48K. **50K 최소 기준 미달 빈도가 높을 수 있음**. 참고: ChiefWriter도 ~40-45K로 임계값 근처이나 이미 캐시 사용 중(미달 시 자동 skip).

**해법**:
- Analyst 호출 전 `stable_context` (Treatment + 설정 + 세계관) 캐시 생성
- 10+ `ask()` 호출을 `_ask_with_cached_context()` 전환
- 50K 미만 시 자동 skip (기존 인프라 동작)

**우선순위**: P2 (50K 미달 가능성 높아 효과 불확실 — Treatment 대형 프로젝트에서만 절감 체감, 인프라 완비)
**파일**: `modules/domain/agents/analyst.py`

**주의사항**:
- Analyst 메서드별로 variable_prompt가 다름 → stable/variable 분리 설계 필요
- 50K 최소 요건 미달 시 자동 fallback → 안전 (기능 변경 0)
- TTL=600s(10분) 적용 — Arc 생성 1회 내 충분
- **핵심 리스크**: 구현 비용(stable/variable 분리) 대비 효과(캐시 미생성 빈도)가 ROI 낮을 수 있음

---

## OPT-2. 장기연재 컨텍스트 스케일링 — Stage4는 부분 해소, 범용 API는 미부재

**현황**:
- `WorldState.get_summary()`: NPC **importance 기반** 정렬 (companion=3 > relation=2 > role=1) → 상위 30명 표시
- `FactLedger.to_summary()`: 활성 아이템 상위 20개, 수치 상위 15개 표시
- `stage4_context_builder.py`: `_extract_blueprint_entities()` + `_build_continuity_packet()` + `_build_condensed_world_state_summary()` + `_build_condensed_fact_ledger_summary()`로 **Blueprint 언급 엔티티를 Stage 4 mandatory_context에서 우회 보호**

**잔여 갭**:
- **Stage 4 경로 자체는 대부분 보강됨**. Blueprint 또는 `arc.state_changes`에 명시된 NPC/아이템/플롯/장소는 CP와 condensed summary에서 보호된다.
- 다만 `WorldState.get_summary()` / `FactLedger.to_summary()` 자체에는 whitelist 파라미터가 없어, **다른 호출자**는 여전히 고정 cap(30/20/15)에 묶인다.
- 남은 edge case는 Blueprint와 `arc.state_changes` 모두에 **명시 이름이 없는 엔티티/관계**다. Smart Retrieval과 condensed summary가 일부 보완하지만, 범용 해결은 아니다.

**해법**:
- **즉시 배치에서는 현행 Stage4 우회 경로 유지**
- 후속 범용화가 필요하면 `get_summary(npc_whitelist=None)` / `to_summary(item_whitelist=None)`를 **additive** 하게 추가
- 필요 시 `stage4_context_builder.py`에서 명시 이름이 없는 관계/역할성 힌트까지 CP 후보로 승격하는 보강만 검토

**우선순위**: P3 (Stage 4는 이미 부분 해소, 잔여는 범용 API/edge coverage)
**파일**: `modules/core/stage4_context_builder.py`, 선택적으로 `modules/core/world_state.py`, `modules/core/fact_ledger.py`

---

## OPT-3. 프롬프트 A/B 테스트 인프라

**현황**:
- `llm_calls` 테이블: 18컬럼 — `context_tag`(범용 태그)만 존재, **프롬프트 버전 컬럼 없음**
- `stage_attempts` 테이블: 16컬럼 — **버전 태그 없음**
- `director_selections` 테이블: 12컬럼 — **버전 태그 없음**
- `advisory_reject_correlation()`: 상관분석 계산 가능하나 **프롬프트 버전 세그먼트 불가**

**갭**: director.yaml 규칙 1개 변경 효과를 측정할 수 없음.
- "규칙 14 추가 후 합격률 변화?" → 답변 불가
- "NC-3 체크리스트 도입 후 점수 분포 변화?" → 답변 불가
- 모든 프롬프트 변경이 **감 기반** — 데이터 기반 최적화 불가

**해법**:
- `stage_attempts` 테이블에 `prompt_version TEXT` 컬럼 추가
- `save_stage_attempt()` 호출 시 현재 프롬프트 해시 또는 버전 태그 저장
- YAML 파일에 `_version: "v1.2"` 메타 키 추가 → PromptLoader가 자동 읽기
- `FailureAnalyzer`에 `compare_versions(v1, v2)` 메서드 추가
- 최소 구현: YAML `_version` + DB 컬럼 1개 + FailureAnalyzer 메서드 1개

**우선순위**: P2 (인프라 성격, 즉시 퀄리티 개선은 아님)
**파일**: `modules/core/db_manager.py`, `config/prompts/*.yaml`, `modules/core/prompt_loader.py`, `modules/core/failure_analyzer.py`

---

## 우선순위 요약

### P1

- 없음 — 최근 코드 기준으로 `OPT-2`는 Stage 4 경로에서 이미 부분 해소됨

### P2 (인프라 / 조건부 효과)

| ID | 항목 | 효과 | 비용 |
|----|------|------|------|
| OPT-1 | Analyst Context Caching | LLM 비용 절감 (**50K 이상 프로젝트 한정**, 미달 시 효과 0) | 중 (stable/variable 분리 설계) |
| OPT-3 | A/B 테스트 인프라 | 프롬프트 변경 효과 데이터 기반 측정 | 중 (DB 스키마 + YAML + FailureAnalyzer) |

---

## 기존 4개 문서와의 관계

| 본 OPT | TF-DB | Beyond-DB | TF-QR | 관계 |
|--------|-------|-----------|-------|------|
| OPT-1 (Caching) | — | — | — | **신규** (비용 최적화) |
| OPT-2 (Scaling residual) | A3 보완 | SNR-1 보완 | NPC-G5 보완 | **부분 해소 후 잔여** — A3은 절삭 카운터, SNR-1은 Stage4 중복 제거, OPT-2 잔여는 범용 whitelist API/CP 후보 범위 |
| OPT-3 (A/B) | — | FL-3 보완 | — | **보완** — FL-3은 FailureAnalyzer 소비, OPT-3은 버전 세그먼트 추가 |

---

## 절대 하지 말 것

- 기존 Context Caching 5개 에이전트의 TTL/threshold를 변경하지 말 것
- `get_summary()` / `to_summary()` 기존 cap 값(30/20/15)을 변경하지 말 것 — 필요하면 whitelist만 additive하게 추가
- Advisory 체인 실행 순서나 ThreadPoolExecutor 설정을 변경하지 말 것
- DB 테이블 기존 컬럼을 삭제/변경하지 말 것 — 추가만 허용
- `system.yaml` `min_content_chars: 50000` 을 변경하지 말 것

---

## 검증 기준

- `pytest tests/ -q` 전체 회귀 PASS
- `pytest --collect-only -q tests` 기준 전체 테스트 **3,832개 수집 유지**
- `ruff check` 변경 파일 전량 0 violations
- OPT-1: Analyst 경로 LLM 호출 횟수 변경 없음 (캐시 적용만, 호출 제거 아님)
- OPT-2: Blueprint 언급 NPC/아이템이 Stage4에서 `Continuity Packet` 또는 `[CP 상세 참조]` 경로로 보호되는 테스트
- OPT-3: `stage_attempts` 테이블에 `prompt_version` 컬럼 존재 + NULL 허용 (기존 호환)
