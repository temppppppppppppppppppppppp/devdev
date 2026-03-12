# TF-250 전수조사: 250화 완결 장기연재 스케일 이슈

> 작성: 2026-03-10
> 상태: 8pass 감리 완료 (최근 코드 반영 교정 5건, LS-5/LS-7 재분류, 기준선 갱신)
> 전제: TF-DB + Beyond-DB + TF-QR + TF-OPT 4개 문서에 **없는** 항목만 수록
> 방법: DB/메모리 스케일 → 서사 연속성 → 컨텍스트 윈도우 → 에러/엣지케이스 4개 영역 병렬 전수조사 → 코드 검증 → 6pass 오탐/과장 제거
> 시나리오: 250화 완결 1작품 (≈ 42~83 Arc, NPC 100+명, 복선 125+개)

---

## 공통 원칙

- 기존 동작 불변 — 상한 확대·조회 최적화만, 기능 변경 금지
- LLM 호출 추가 0회
- 테스트 회귀 0건
- 기존 4개 문서(TF-DB/Beyond-DB/TF-QR/TF-OPT) 항목과 중복 금지

---

## 오탐/사실 교정 기록

| 초기 후보 | 판정 | 근거 |
|-----------|------|------|
| ep_num/arc_num integer overflow | **오탐** | Python int 무한 + SQLite 64-bit (±9.2×10¹⁸). 250화는 안전. |
| manuscripts 테이블 query 성능 | **오탐** | `get_context_manuscripts()` LIMIT 3, `get_recent_manuscript_excerpts()` SUBSTR(content,1,200)+LIMIT 10. **이미 최적화됨.** |
| lookback 크기 성장 | **오탐** | `validation.yaml` lookback_total_chars=40000 **고정 상한**. 에피소드 증가 영향 0. |
| episode_production.jsonl 크기 | **오탐** | 250화 × 2KB = ~500KB. 파일시스템 한도 내. append-only로 성능 영향 없음. |
| destroyed[] 무한 성장 (LS-6) | **오탐** | `world_state.py` L561-564에 `if len(self._state["destroyed"]) > 100: self._state["destroyed"] = self._state["destroyed"][-100:]` **이미 구현**. 100개 FIFO cap 존재. |
| Director advisory 40K 상한 근접 (LS-7) | **사실 교정** | 실제 상한은 `validation.yaml`의 `context.director_mandatory_max=400000`. 또 `stage4_interview_round.py`에 advisory suppress, reference-only 분리, 개별 advisory 6~8줄 cap이 이미 있어 **O(N) 선형 성장** 진술은 과장. |

---

## LS-1. Series/Volume Summary 압축 한계 — 1,000자 상한

**현황**:
- `stage2_finalizer.py`의 Volume/Series 요약 프롬프트가 둘 다 **1,000자 상한**
- Volume 요약 생성 cadence는 **10 Arc마다 1개** (`global_arc_no % 10 == 0`)
- 그런데 `stage4_context_builder.py`는 최근 볼륨 계산에 `(_current_arc_no - 1) // 5 + 1`을 사용해 **5 Arc 단위 볼륨 가정**으로 `volume_summary_{n}`을 조회
- 즉, 현재는 **압축 한계 + volume 번호 체계 불일치**가 동시에 존재

**갭**:
- 250화 규모에서 전체 서사를 1,000자로 유지하면 Arc 단위 복선/관계 변화를 보존하기 어렵다
- 추가로 write 측은 10 Arc, read 측은 5 Arc 기준이라 **볼륨 요약 참조 창이 어긋날 수 있다**
- 문제는 단순 "짧다"가 아니라 **압축 + 인덱싱 불일치**다

**해법**:
- Volume/Series 요약 상한을 각각 **2,000 / 5,000자**로 확대
- 구조화 지시 추가: `"[인물 아크] [핵심 갈등] [미해결 복선]"` 3섹션
- `ARCS_PER_VOLUME`의 SSOT를 **5 또는 10 중 하나로 통일**하고, 생성/조회 양쪽을 동일 기준으로 맞춘다

**우선순위**: P1 (장기연재 서사 연속성 + 볼륨 참조 정합성 직결)
**파일**: `modules/core/stage2_finalizer.py`, `modules/core/stage4_context_builder.py`

---

## LS-2. Active Plots FIFO 30개 상한 — 숨겨진 플롯 소실

**현황**:
- `world_state.py` L923-926: `_MAX_ACTIVE_PLOTS = 30` + FIFO 슬라이싱 (`active_plots[-30:]`)
- `get_summary()` L843-848: 최근 **10개만** 표시 (`plots[-10:]`)
- 250화 시나리오: 평균 1.5개/화 × 250 = 375개 신규 플롯, 완결 0.5개/화 = 125개 완결 → **활성 250개 중 30개만 메모리 보존**

**갭**:
- 31번째 플롯부터 FIFO 제거 → **LLM과 시스템 모두 존재 자체를 모름**
- "ep30에서 시작된 '비밀 조직 추적' 플롯" → ep100에서 FIFO 탈락 → ep200에서 재개 불가
- TF-DB-A3(절삭 카운터)은 **표시 계층**의 문제만 다룸, 본 항목은 **저장 계층**의 소실

**해법**:
- `_MAX_ACTIVE_PLOTS` 30 → **100** 확대 (250화 규모 커버)
- get_summary()의 표시 상한(10개)은 유지 — 절삭 카운터로 보완 (TF-DB-A3)
- 또는 DB에 `active_plots` 전량 백업 + 메모리 cap 유지

**우선순위**: P1 (플롯 영구 소실 = 서사 연속성 파괴)
**파일**: `modules/core/world_state.py` (L923 `_MAX_ACTIVE_PLOTS`)

---

## LS-3. Causal Graph lookback=10 고정 — 장거리 인과 단절

**현황**:
- `db_manager.py` L1763: `get_recent_causal_links(current_ep, lookback=10)` — 기본값 10
- 250화 분량의 causal_graph 데이터가 **DB에 전량 저장**되어 있으나, 조회 범위가 최근 10화로 고정
- Stage 4 post-processor + LM-post-1(Director MC)에서만 소비
- TF-DB-H2는 "Stage 2/3 미참조"를 다루지만, **lookback 범위 자체의 한계**는 미다룸

**갭**: ep250에서 ep1~240의 인과관계 참조 불가.
- ep50에서 "A가 B를 배신" → ep200에서 "B의 복수" 서사 시 인과 링크 미참조
- DB에 데이터는 있지만 **조회 로직이 최근 10화만 반환**

**해법**:
- `get_recent_causal_links()` 기본 lookback 10 → **30** 확대 (Arc 5~6개 커버)
- 별도 `get_causal_links_by_entities(entity_names)` API 추가 — 특정 NPC/아이템 관련 인과만 검색
- Stage 2 `_generate_prev_context()`에서 entity 기반 장거리 인과 조회

**우선순위**: P1 (장거리 서사 연속성)
**파일**: `modules/core/db_manager.py` (L1763 lookback 기본값)

---

## LS-4. Foreshadow Tracker MAX_HOOKS=100 — 복선 추적 누락

**현황**:
- `foreshadow_tracker.py` L127: `max_hooks: int = 100`
- 초과 시 L176-185: PAYOFF 완료 → 가장 오래된 것부터 FIFO 제거. PAYOFF 없으면 가장 오래된 PLANT 제거
- DB 저장(L419-473: `save_to_db()`)은 완비 — **DB에는 전량 보존**
- 250화 × Arc당 5개 복선 = **125+ 복선** → 초과분 25개 런타임 추적 탈락

**갭**:
- 런타임 메모리에서 탈락한 복선은 `is_overdue()` 검사 미적용
- "ep20에서 심은 MYSTERY 복선(20화 내 회수 목표)" → ep100에서 FIFO 탈락 → 미회수 경고 없음
- DB에 데이터는 보존되지만 **운영 중 자동 감지가 불가**

**해법**:
- MAX_HOOKS 100 → **200** 확대 (250화 충분 커버)
- 또는 `load_from_db()` 시 overdue 검사를 DB 쿼리 기반으로 전환 (메모리 제한 무관)

**우선순위**: P2 (DB 백업 존재로 데이터 소실은 없음. 런타임 감지만 누락)
**파일**: `modules/core/foreshadow_tracker.py` (L127 `max_hooks`)

---

## LS-5. mandatory_context 예산 분리 — 250화에서도 tail-drop 절삭 위험

**현황**:
- `validation.yaml` 기준 상한은 `mandatory_context_max=400000`, `director_mandatory_max=400000`
- 동시에 Smart Retrieval 예산은 `stage4_total_budget=300000`, `director_total_budget=300000`
- `stage4_context_builder.py`는 `_mc_parts`에만 `_apply_context_budget()`을 적용하고, Smart Context 결과인 `_sc_parts`는 별도 조립 후 앞쪽에 붙인다
- 이후 최종 `mandatory_context`는 `stage4_orchestrator.py` / Director 경로에서 다시 `400000`자 cap으로 tail-trim 된다

**갭**:
- 현재 리스크는 "300화+에서 언젠가 넘칠 수 있음"이 아니라, **250화 규모에서도 Smart Context가 두꺼우면 `_sc_parts + _mc_parts` 합산이 400K를 넘을 수 있다는 점**이다
- 이 경우 시스템 장애는 아니지만, 최종 단계에서 **뒤쪽 섹션이 잘리는 tail-drop**이 발생한다
- 즉 문제의 본질은 총량 부족이 아니라 **예산 관리가 `SC`와 비-`SC`로 분리되어 있어 합산 상한을 사전에 보장하지 못한다**는 데 있다

**해법**:
- `stage4_context_builder.py`에 `_sc_header`, `_mc_body`, 최종 합산 길이 로깅 추가
- `SC`와 비-`SC`가 합쳐진 뒤에도 `mandatory_context_max` 여유분을 보장하도록 headroom 규칙 추가
- 상한 자체를 더 키우기보다, 후반 절삭이 자주 나는 슬롯을 먼저 줄이는 방식으로 재배분

**우선순위**: P1 (250화 목표 스케일에서 이미 컨텍스트 tail-drop 가능)
**파일**: `modules/core/stage4_context_builder.py`, `modules/core/stage4_orchestrator.py`

---

## LS-6. get_all_episode_bibles() 전체 로드 — 비효율 쿼리

**현황**:
- `db_manager.py` L1210: `SELECT * FROM episode_bibles ORDER BY ep_num` — **WHERE 필터 없음**
- `info_paradox_checker.py` L46: `all_bibles = db.get_all_episode_bibles()` → 전체 로드
- L59-60: `if ep >= up_to_ep: continue` — **Python-side 필터링**

**갭**: 250화 × 5KB/화 = 1.25MB 전체 메모리 로드 + 11 JSON 필드 × 250 = 2,750회 파싱.
- 실행 시간: ~25-50ms (SQLite + JSON 파싱)
- **치명적이진 않지만 비효율** — DB WHERE 절로 해결 가능

**해법**:
- `get_all_episode_bibles()` → `get_episode_bibles_before(up_to_ep)` 래퍼 추가
- SQL: `SELECT * FROM episode_bibles WHERE ep_num < ? ORDER BY ep_num`
- 선택적 파싱: reveals + knowledge_map 2필드만 파싱 (나머지 9필드 불필요)

**우선순위**: P2 (성능 경미, 250화에서도 50ms 미만)
**파일**: `modules/core/db_manager.py`, `modules/core/info_paradox_checker.py`

---

## LS-7. Advisory 선형 성장 — 장애 이슈보다 정보 밀도 이슈로 재분류

**현황**:
- 실제 `director_mandatory_max`는 40K가 아니라 **400K**
- `stage4_interview_round.py`에는 이미 다음 방어가 있다
  - 상위 티어와 주제가 겹치는 advisory suppress
  - `win_rates` / `fix_scope` / `DB-1,2,6,8`의 `[참고 — 판정 무관]` 분리
  - `NpcDrift`/`NumericDrift`/`Flashback`/`InfoParadox`/`RelDrift`/`LongTermRep` 개별 줄수 cap
- 따라서 "advisory가 에피소드 수에 따라 무한히 선형 팽창한다"는 초기 진술은 현재 코드 기준으로 과장이다

**잔여 갭**:
- 남은 문제는 상한 초과 자체보다, **250화 시점에서도 advisory block이 두꺼워지면 Director가 읽어야 할 핵심 신호 대비 히스토리 설명 비율이 커질 수 있다**는 점이다
- 즉 장애/절삭 이슈라기보다 **정보 밀도와 가독성** 문제에 가깝다

**해법**:
- 현행 cap/suppress/reference-only 구조는 유지
- 필요 시 INFO 티어 advisory만 1줄 요약 우선으로 더 압축
- 실파이프라인에서 Director reasoning이 길어지거나 중요 경고 회수가 밀릴 때만 후속 최적화

**우선순위**: P3 (현재는 구조적 방어가 있어 모니터링 우선)
**파일**: `modules/core/stage4_interview_round.py`

---

## LS-8. alive_npcs dict 무한 성장

**현황**:
- `world_state.py` L169-176: NPC 등장/관계 변경마다 `alive_npcs[name]` 추가
- 사망 시 `alive_npcs.pop(name)` → dead_npcs 이동
- **상한 없음** — 250화에서 100+ NPC 누적 가능
- `get_summary()`에서 `sorted_alive[:30]` (상위 30명만 표시)는 존재

**갭**: 메모리 dict 자체는 O(1) lookup이나, NPC당 known_attrs 누적으로 메모리 선형 성장.
- 100 NPC × 평균 5 known_attrs = 500개 속성 엔트리
- 메모리: ~100KB (경미)

**해법**:
- importance 기반 정리 로직 추가 — 50화 미등장 + importance=0 → 아카이브
- 또는 현상 유지 (100KB는 경미, 성능 영향 없음)

**우선순위**: P2 (메모리 영향 경미)
**파일**: `modules/core/world_state.py`

---

## 우선순위 요약

### P1 (250화 서사 연속성 직결)

| ID | 항목 | 영향 | 비용 |
|----|------|------|------|
| LS-1 | Series/Volume Summary 압축 한계 | 250화 전체 서사 99% 정보 손실 | 낮 (프롬프트 2곳 상한 변경) |
| LS-2 | Active Plots FIFO 30 | 숨겨진 플롯 영구 소실 | 극저 (상수 1개 변경) |
| LS-3 | Causal Graph lookback=10 | 장거리 인과 연결 불가 | 낮 (기본값 변경 + API 1개) |
| LS-5 | mandatory_context 예산 분리 | 250화에서도 후반 컨텍스트 tail-drop 가능 | 낮~중 (예산 재배분/로깅) |

### P2 (성능/위생/모니터링)

| ID | 항목 | 영향 | 비용 |
|----|------|------|------|
| LS-4 | Foreshadow MAX_HOOKS=100 | 런타임 overdue 감지 누락 (DB 보존됨) | 극저 (상수 변경) |
| LS-6 | get_all_episode_bibles() | 비효율 쿼리 (50ms 미만) | 낮 (WHERE 추가) |
| LS-8 | alive_npcs 무한 성장 | 메모리 경미 | 낮~중 (아카이브 로직) |

### P3 (모니터링)

| ID | 항목 | 영향 | 비용 |
|----|------|------|------|
| LS-7 | Advisory 정보 밀도 | Director 가독성 저하 가능성 | 낮~중 (INFO 요약 추가) |

---

## 기존 4개 문서와의 관계

| 본 LS | TF-DB | Beyond-DB | TF-QR | TF-OPT | 관계 |
|--------|-------|-----------|-------|--------|------|
| LS-1 (Summary 압축) | — | — | — | — | **신규** (스케일 고유) |
| LS-2 (Plots FIFO) | A3 보완 | — | — | — | **보완** — A3은 표시 절삭, LS-2는 저장 소실 |
| LS-3 (Causal lookback) | H2 보완 | — | — | — | **보완** — H2는 Stage 2/3 미주입, LS-3은 조회 범위 |
| LS-4 (Foreshadow) | — | — | — | — | **신규** (스케일 고유) |
| LS-5 (Context 예산 분리) | — | — | — | — | **신규** (스케일 고유, 250화에서도 tail-drop 가능) |
| LS-6 (Bible query) | — | — | — | — | **신규** (성능) |
| LS-7 (Advisory 정보 밀도) | — | — | — | — | **신규** (부분 해소 후 모니터링) |
| LS-8 (alive_npcs) | — | — | — | — | **신규** (코드 위생) |

---

## 파일 변경 목록 (예상)

| 파일 | 변경 | LS ID |
|------|------|-------|
| `modules/core/stage2_finalizer.py` | Series 1,000→5,000자 + Volume 1,000→2,000자 프롬프트 | LS-1 |
| `modules/core/world_state.py` | `_MAX_ACTIVE_PLOTS` 30→100 | LS-2 |
| `modules/core/db_manager.py` | `get_recent_causal_links()` lookback 10→30 + `get_episode_bibles_before()` | LS-3, LS-6 |
| `modules/core/foreshadow_tracker.py` | `max_hooks` 100→200 | LS-4 |
| `modules/core/stage4_context_builder.py` | `_sc_parts`/`_mc_parts`/최종 합산 길이 로깅 + headroom 규칙 | LS-5 |
| `modules/core/stage4_orchestrator.py` | 최종 tail-trim 관측성 보강 | LS-5 |
| `modules/core/info_paradox_checker.py` | `get_episode_bibles_before(up_to_ep)` 전환 | LS-6 |
| `modules/core/stage4_interview_round.py` | 필요 시 INFO tier 1줄 요약 추가 | LS-7 |

---

## 절대 하지 말 것

- `get_summary()` / `to_summary()` 기존 cap 값(30/20/15)을 변경하지 말 것
- `mandatory_context_max: 400000` 을 변경하지 말 것 — 모니터링만
- `lookback_total_chars: 40000` 을 변경하지 말 것
- Advisory 체인 실행 순서나 ThreadPoolExecutor 설정을 변경하지 말 것
- `director_mandatory_max: 400000` 을 임의 상향하지 말 것 — 예산 재배분이 우선
- ForeshadowTracker의 DB 저장 로직(save_to_db)을 변경하지 말 것
- WorldState `_INIT_STATE` 스키마를 변경하지 말 것
- WorldState `destroyed[]` 기존 100개 FIFO cap을 변경하지 말 것

---

## 검증 기준

- `pytest tests/ -q` 전체 회귀 PASS
- `pytest --collect-only -q tests` 기준 전체 테스트 **3,794개 수집 유지**
- `ruff check` 변경 파일 전량 0 violations
- LS-1: Series 요약 5,000자 이내 생성 확인 테스트
- LS-2: `_MAX_ACTIVE_PLOTS=100` 시 31~100번째 플롯 보존 확인 테스트
- LS-3: `get_recent_causal_links(ep=250, lookback=30)` 시 ep220~250 범위 반환 테스트
- LS-5: retrieval-heavy 시나리오에서 `_sc_parts + _mc_parts` 합산 길이와 최종 trim 발생 여부 로깅 확인 테스트
- LS-6: `get_episode_bibles_before(up_to_ep=100)` 시 ep100 미만만 반환 테스트

---

## 250화 DB 크기 추정 (참고)

| 테이블 | 예상 행 수 | 용량 |
|--------|----------|------|
| vec_episodes (임베딩) | 250 | ~4 MB |
| episode_bibles | 250 | ~1.3 MB |
| manuscripts | 250 | ~2 MB |
| npc_history | 3,750~225,000 | 1~61 MB |
| npc_relationship_history | ~22,500 | ~7 MB |
| llm_calls | ~7,500 | ~7 MB |
| stage_attempts | ~1,500 | ~2 MB |
| 기타 | 500+ | ~10 MB |
| **합계** | | **~34~94 MB** |

> 보수 추정 35MB, 최악 95MB. SQLite 정상 범위 (GB 단위까지 지원).
