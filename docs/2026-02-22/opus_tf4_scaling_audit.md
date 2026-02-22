# Opus TF-4: 200화 장기연재 스케일링 병목 감사 보고서

> **작성일**: 2026-02-22
> **대상**: 글도비 V63 코드베이스 전체
> **시나리오**: 200화 (40 Arc, 약 100만 자 누적 원고) 기준

---

## 요약 (Executive Summary)

200화 장기연재 시 **7개 병목 지점**이 확인되었다. 가장 심각한 것은 (1) 매 에피소드마다 30화 원고 전문을 개별 쿼리로 로드하는 N+1 패턴, (2) `resolved_plots`와 `entity_destructions` 등 상한 없이 무한 누적되는 인메모리 데이터, (3) `episode_sentence_hashes` 테이블의 비제한적 성장이다. DB 파일 크기는 약 250-350MB로 추정되며, SQLite 단일 파일 기반으로는 충분히 관리 가능하나 LIKE 풀스캔 쿼리가 성능 저하를 유발할 수 있다.

| 등급 | 항목 수 | 설명 |
|------|---------|------|
| **BOTTLENECK** | 3 | 즉시 개선 권장 |
| **MANAGEABLE** | 5 | 현재 작동하지만 200화 시 감시 필요 |
| **SAFE** | 4 | 200화에서도 문제 없음 |

---

## 1. DB 쿼리 N+1 문제

### 1-1. get_manuscript(ep) 루프 호출 -- 30화 전문 로드

**위치**: `modules/core/stage4_context_builder.py` L332-345

```python
# [V67] 이전 30화 원고 전문 로드
for _prev_ep in range(max(1, next_ep - 30), next_ep):
    _prev_ms_data = self.ctx.current_project.db.get_manuscript(_prev_ep)
    # ... 전문 텍스트 수집
```

**현재 동작**: 매 에피소드 생성 시 최대 30회의 개별 `SELECT * FROM manuscripts WHERE ep_num = ?` 쿼리 실행. 각 쿼리는 인덱스(PK)를 타므로 개별 쿼리 자체는 O(1)이나, **30회 반복 + RLock 획득/해제 30회**가 오버헤드다.

**200화 시점 추정**:
- 원고 1화 평균 5,000자 x 30화 = **150,000자 (약 300KB)** 메모리 적재
- 30회 SELECT + JSON 역직렬화 + RLock 30회 = 약 30-50ms (SSD 기준)
- 이 데이터가 `prev_manuscripts_text`에 합쳐져 context window에 주입됨

**판정**: **BOTTLENECK**

**권고 조치**:
1. `get_manuscripts_range(start_ep, end_ep)` 배치 쿼리 메서드 추가:
   ```sql
   SELECT ep_num, title, content FROM manuscripts
   WHERE ep_num >= ? AND ep_num < ?
   ORDER BY ep_num ASC
   ```
2. 최근 5화만 전문, 6-30화는 `get_recent_manuscript_excerpts()` (이미 존재하는 SUBSTR 기반 발췌 쿼리) 활용
3. 결과를 세션 내 캐시 (dict[int, str])에 보관하여 Director 심사 시 재로드 방지

---

### 1-2. get_blueprint(ep) 개별 호출

**위치**: `modules/core/db_manager.py` L689-704

**현재 동작**: `get_blueprint(ep_num)`은 PK 인덱스 단건 조회. Stage4에서는 현재 화의 blueprint만 조회하므로 N+1 아님.

`get_recent_blueprints(before_ep, limit=10)` 메서드가 별도로 존재하여 배치 조회가 이미 가능하다.

**200화 시점 추정**: 단건 조회이므로 영향 없음. Blueprint JSON은 평균 5-10KB로 작다.

**판정**: **SAFE**

---

### 1-3. get_cumulative_bible(up_to_ep) 증분 캐시

**위치**: `modules/core/db_manager.py` L817-908

**현재 동작**: 증분 캐시(`_cumulative_bible_cache`) 구현 완료.
- 캐시에 정확히 같은 ep가 있으면 즉시 반환 (deepcopy)
- 이전 캐시 중 가장 큰 ep를 찾아 그 이후 에피소드만 DB에서 조회
- **LRU 캐시 크기: 최대 5개** (L902, `_MAX_BIBLE_CACHE = 5`)

**200화 시점 추정**:
- 최악의 경우 (캐시 미스): `SELECT * FROM episode_bibles WHERE ep_num >= 1 AND ep_num <= 200` = 200행 풀스캔
- 각 행의 JSON 파싱 8~12개 필드 x 200 = 약 2,400회 `json.loads()` 호출
- 그러나 증분 캐시가 작동하면 최대 5화분만 추가 조회 = **실질적으로 안전**
- **주의**: `save_episode_bible()` 호출 시 캐시 무효화 발생 (해당 ep 이후 전체 삭제)

**판정**: **MANAGEABLE** -- 증분 캐시가 유효하게 작동하지만, 5개 슬롯이 적다. 장기 세션에서 캐시 미스율이 높아질 수 있다.

**권고 조치**:
1. `_MAX_BIBLE_CACHE`를 10으로 상향 (메모리 비용 미미: 캐시 1개 = 수십 KB)
2. deepcopy 대신 frozen/immutable dict 패턴 고려 (copy 비용 절감)

---

### 1-4. npc_history 조회

**위치**: `modules/core/db_manager.py` L1729-1749

**현재 동작**:
- `get_npc_history(npc_name, limit=50)`: 이름 인덱스(`idx_npc_history_name`) 활용, LIMIT 50. O(log N)
- `get_npc_latest_fields(npc_name)`: 상관 서브쿼리 `SELECT MAX(id) FROM npc_history WHERE npc_name = ? GROUP BY field_name` 사용

**200화 시점 추정**:
- NPC당 평균 변경 이력 5-10건/Arc x 40 Arc = 200-400건/NPC
- 누적 NPC 50명 기준 npc_history 총 행: 약 10,000-20,000행
- `idx_npc_history_name` 인덱스가 있으므로 개별 조회는 O(log N) = 안전
- 그러나 `get_npc_latest_fields()`의 상관 서브쿼리는 NPC별 field 종류 * 인덱스 탐색 = 약 10-15회 내부 조회

**판정**: **SAFE** -- 인덱스가 잘 설정되어 있음

---

## 2. 누적 데이터 무한 증가

### 2-1. resolved_plots (StateTracker)

**위치**: `modules/domain/agents/state_tracker.py` L132

```python
self.resolved_plots: list[dict] = []
```

**현재 동작**: Arc마다 `extract_resolved_plots_from_arc()`가 호출되어 완결된 플롯을 append. **상한이 없다.**

중복 방지 로직은 존재 (`plot+arc_no 조합 중복 체크`, state_tracker_plots.py L112-117):
```python
if not any(
    p.get("plot") == entry["plot"] and p.get("arc_no") == arc_no
    for p in self.tracker.resolved_plots
):
    self.tracker.resolved_plots.append(entry)
```
하지만 이 중복 체크 자체가 O(N) 선형 탐색이므로 N이 커지면 느려진다.

**200화 시점 추정**:
- Arc당 평균 2-3개 플롯 완결 x 40 Arc = 80-120개 항목
- 각 항목 dict 약 200바이트 -> 총 약 24KB
- 중복 체크: 120개 리스트에서 `any()` 탐색 = 무시할 수준
- `get_resolved_plots_summary()`에서 **전량 프롬프트 주입** (L122-131, 제한 없음)
- 120개 플롯 요약 x 80자/줄 = 약 9,600자 프롬프트에 무조건 삽입

**판정**: **MANAGEABLE** -- 메모리는 안전하지만 프롬프트 주입 시 **context window 압박** 유발

**권고 조치**:
1. `get_resolved_plots_summary(max_items=30)` 파라미터 추가, 최근 30개만 출력
2. 오래된 플롯은 "요약 블록"으로 압축 (예: "Arc 1-20에서 65건의 플롯이 완결됨")
3. resolved_plots 자체에 최대 200개 상한 설정, 초과 시 FIFO 퇴출

---

### 2-2. _cumulative_bible_cache (DBManager)

**위치**: `modules/core/db_manager.py` L65

```python
self._cumulative_bible_cache: dict = {}
```

**현재 동작**: 최대 5개 슬롯 (`_MAX_BIBLE_CACHE = 5`, L902). 오래된 키부터 삭제. deepcopy로 mutation 방지.

**200화 시점 추정**:
- 캐시 값 1개: cumulative bible dict = items(리스트) + npcs(리스트) + dead_npcs(리스트) + relationships(dict) + states(dict) + all_reveals(리스트)
- 200화 누적 시 items 50개, npcs 100개, relationships 50쌍, all_reveals 200개 정도
- dict 1개 약 50-100KB x 5 슬롯 = **500KB** (deepcopy 포함 1MB 이내)
- `save_episode_bible()` 호출 시 해당 ep 이후 캐시 전량 무효화

**판정**: **SAFE** -- 5 슬롯 상한이 잘 작동

---

### 2-3. entity_name_registry (상한 500개)

**위치**: `modules/domain/agents/state_tracker.py` L134-135

```python
self.entity_name_registry: OrderedDict = OrderedDict()
self._entity_registry_max_size = 500
```

**현재 동작**: LRU 패턴 -- `register_entity_name()`에서 500개 초과 시 가장 오래된 것부터 퇴출 (`popitem(last=False)`).

**200화 시점 추정**:
- 총 등장 엔티티 (비-NPC): 장소, 조직, 아이템 등
- Arc당 평균 5-10개 신규 엔티티 x 40 Arc = 200-400개
- 500개 상한은 200화 시점에서 **적절**. 중요 엔티티가 퇴출될 가능성은 낮음
- 각 엔티티 dict 약 100바이트 x 500 = 50KB (무시할 수준)

**판정**: **SAFE** -- 현재 상한 500이 200화에 적절

**참고**: 300화+ 초장기 연재 시에는 700-1000으로 상향 검토

---

### 2-4. episode_sentence_hashes (크로스 에피소드 반복 감지)

**위치**: DB 테이블 `episode_sentence_hashes` (db_manager.py L401-412)

```sql
CREATE TABLE episode_sentence_hashes (
    episode_number INTEGER NOT NULL,
    sentence_hash  TEXT NOT NULL,
    sentence_preview TEXT,
    PRIMARY KEY (episode_number, sentence_hash)
)
CREATE INDEX idx_episode_sentence_hashes_hash ON episode_sentence_hashes(sentence_hash)
```

**현재 동작**: 매 에피소드 PASS 시 문장별 해시를 DB에 저장. 다음 에피소드에서 과거 해시와 교차 비교.

**200화 시점 추정**:
- 원고 1화 평균 5,000자 / 평균 문장 길이 50자 = 100문장/화
- 200화 x 100문장 = **20,000행**
- 각 행: episode_number(INT 4B) + sentence_hash(TEXT ~32B) + sentence_preview(TEXT ~50B) + 인덱스 오버헤드
- 테이블 크기: 약 **2-4MB** (인덱스 포함)
- 교차 비교 쿼리: `WHERE sentence_hash IN (?, ?, ...) AND episode_number >= ? AND episode_number < ?`
  - sentence_hash 인덱스로 O(K log N) (K=현재 화 문장 수, N=총 해시 수)
  - 100개 해시 x log(20,000) = ~1,400 인덱스 탐색 = **2-5ms**

**판정**: **MANAGEABLE** -- 인덱스가 있어 쿼리는 빠르지만, **정리 정책이 없어 DB 파일이 무한 증가**

**권고 조치**:
1. lookback 윈도우 (예: 최근 50화)만 비교하는 것은 이미 쿼리에서 `episode_number >= ?` 조건으로 구현됨
2. 100화 이상 오래된 해시는 주기적 정리 (VACUUM 포함):
   ```sql
   DELETE FROM episode_sentence_hashes WHERE episode_number < (최신화 - 100)
   ```

---

### 2-5. 기타 무한 증가 데이터

| 데이터 | 위치 | 200화 추정 크기 | 상한 | 판정 |
|--------|------|-----------------|------|------|
| `entity_destructions` | state_tracker.py L137 | 80-160개 dict (16KB) | **없음** | MANAGEABLE |
| `npc_npc_relationships` | state_tracker.py L139 | 50-100쌍 (10KB) | **없음** | SAFE |
| `in_world_timeline` | state_tracker.py L154 | 400-800 이벤트 (80KB) | **없음** | MANAGEABLE |
| `pending_commitments` | state_tracker.py L160 | 20-50개 (5KB) | **없음** | SAFE |
| `current_companions` | state_tracker.py L157 | 1-5명 (1KB) | **없음** | SAFE |
| `npc_registry` | state_tracker.py L126 | 50-100명 (50KB) | **없음** | MANAGEABLE |
| `npc_dialogue_profiles` | state_tracker.py L151 | 50-100명 (20KB) | **없음** | SAFE |
| `active_plots` | state_tracker.py L149 | 50-100개 (20KB) | **없음** | MANAGEABLE |

**종합 판정**: StateTracker 인메모리 데이터 총합 약 **200-400KB**로 200화에서는 문제 없음. 그러나 상한이 설정된 것이 `entity_name_registry` (500) 하나뿐이므로, 500화+ 초장기 연재 시에는 정리 정책이 필요하다.

---

## 3. 메모리 증가 시뮬레이션

### 200화 시점 런타임 메모리 추정

| 데이터 구조 | 소스 | 200화 추정 크기 | 비고 |
|-------------|------|-----------------|------|
| `prev_manuscripts_text` | stage4_context_builder L345 | **300KB** (30화 전문) | 매 에피소드마다 재생성 |
| `_cumulative_bible_cache` | db_manager L65 | 500KB (5 슬롯) | deepcopy 포함 |
| `_embed_cache` | vec_memory.py L73 | **1.5MB** (128 x 12KB 벡터) | LRU 128개 상한 |
| StateTracker 전체 | state_tracker.py | 300KB | 22개 dict/list 합산 |
| `fact_ledger._ledger` | fact_ledger.py | 100-200KB | 200화 누적 |
| `world_state` | world_state.py | 50-100KB | 요약 캐시 |
| Blueprint/Arc 데이터 | stage4_orchestrator | 50-100KB | 현재 Arc만 보유 |
| Python 프로세스 기본 | - | 80MB | 인터프리터 + 라이브러리 |

**총 런타임 메모리**: 약 **83-85MB** (Python 기본 포함)

**병목 요소**: `prev_manuscripts_text` 300KB가 매 에피소드마다 재구성되고, GC 전까지 이전 복사본이 메모리에 잔존. 5라운드 재시도 시 5 x 300KB = 1.5MB의 일시적 중복 할당.

**판정**: **MANAGEABLE** -- 현대 시스템에서 85MB는 문제 없으나, `prev_manuscripts_text`의 불필요한 전문 로드는 개선 대상.

---

## 4. DB 파일 크기 증가

### project_data.db 200화 시 테이블별 추정

| 테이블 | 행 수 | 행당 평균 크기 | 총 크기 | 비고 |
|--------|-------|---------------|---------|------|
| `manuscripts` | 200 | 5-15KB | **1-3MB** | content TEXT 전문 |
| `blueprints` | 200 | 5-10KB (JSON) | **1-2MB** | |
| `episode_bibles` | 200 | 2-5KB (JSON x12) | **400KB-1MB** | |
| `state_logs` | 200 | 2-5KB (JSON) | **400KB-1MB** | |
| `npc_history` | 10,000-20,000 | 100-200B | **1-4MB** | append-only |
| `episode_sentence_hashes` | 20,000 | 80-100B | **2-4MB** | 정리 정책 없음 |
| `causal_graph` | 2,000-4,000 | 200-500B | **400KB-2MB** | |
| `karma_status` | 50-100 | 50B | **5KB** | UPSERT이므로 행 증가 적음 |
| `encyclopedia` | 200-500 | 200B | **100KB** | UPSERT |
| `seeds` | 100-200 | 100B | **20KB** | |
| `episode_meta` | 200 | 500B-2KB | **100-400KB** | |
| `vec_episodes` | 200 | **12KB** (3072-dim float32) | **2.4MB** | 벡터 데이터 |
| `director_selections` | 600-1,000 | 100B | **100KB** | 5라운드/화 x 200화 |
| `cost_log` | 1,000-2,000 | 100B | **200KB** | |
| `episode_satisfaction_tags` | 200 | 50B | **10KB** | |
| `episode_pacing` | 200 | 100B | **20KB** | |
| `anchors` | 50-100 | 1-50KB | **500KB-5MB** | 가변 (world_state, fact_ledger 등) |
| `martial_tracker` | 200 | 200B | **40KB** | |
| `sync_status` | 200 | 20B | **4KB** | |
| **SQLite 오버헤드** | - | - | **~10%** | 인덱스 + 프리리스트 |
| **WAL 파일** | - | - | **0-10MB** | 체크포인트 전 |

**200화 총 DB 크기 추정**: **10-25MB** (WAL 제외)

**500화 추정**: **30-70MB** (선형 증가)

**판정**: **SAFE** -- SQLite는 수 GB까지 문제없이 처리. 200화 25MB는 매우 가볍다.

**참고**: `anchors` 테이블에 `world_state`, `fact_ledger`, `series_summary`, `volume_summary_*`, `arc_summary_*` 등 대형 JSON이 저장되므로, 이 부분이 가장 가변적이다. 최대 5MB까지 증가할 수 있다.

---

## 5. 쿼리 성능

### 5-1. 인덱스 현황

| 테이블 | PK | 추가 인덱스 | 비고 |
|--------|-----|-------------|------|
| `manuscripts` | ep_num | -- | PK만으로 충분 |
| `blueprints` | ep_num | -- | PK만으로 충분 |
| `episode_bibles` | ep_num | -- | PK만으로 충분 |
| `state_logs` | ep_num | -- | PK만으로 충분 |
| `npc_history` | id (AUTO) | `idx_npc_history_name`, `idx_npc_history_arc` | **양호** |
| `episode_sentence_hashes` | (episode_number, sentence_hash) | `idx_episode_sentence_hashes_hash` | **양호** |
| `director_selections` | id (AUTO) | `idx_director_selections_ep` | 양호 |
| `cost_log` | id (AUTO) | `idx_cost_log_scope`, `idx_cost_log_session` | 양호 |
| `karma_status` | npc_name | -- | PK만으로 충분 |
| `encyclopedia` | id (AUTO) + UNIQUE(item) | -- | 양호 |
| `episode_meta` | ep_num | **없음** | **개선 필요** |
| `causal_graph` | id (AUTO) | **없음** | ep_num 인덱스 필요 |

### 5-2. LIKE 풀스캔 쿼리

**위치 1**: `db_manager.py` L1650-1657 (`get_npc_recent_episodes`)
```sql
WHERE ep_num < ? AND (',' || REPLACE(IFNULL(entity_names, ''), ' ', '') || ',') LIKE ?
```
- `episode_meta` 테이블에 `entity_names` 관련 인덱스 **없음**
- 200화 = 200행 풀스캔 + 문자열 연결 + REPLACE + LIKE
- **소요 시간**: 200행 x 문자열 가공 = 1-3ms (경미하지만 비효율)

**위치 2**: `vec_memory.py` L548-564 (`retrieve_npc_context` entity token match)
```sql
WHERE ep_num < ? AND (
  (',' || REPLACE(IFNULL(entity_names, ''), ' ', '') || ',') LIKE ? ESCAPE '\\' OR ...
)
```
- 동일 패턴. NPC 이름 최대 5개에 대해 각각 LIKE 조건 = 5개 OR 조건 풀스캔
- **소요 시간**: 200행 x 5 LIKE = 3-10ms

**위치 3**: `vec_memory.py` L724-733 (`_keyword_fallback_search`)
```sql
WHERE (summary LIKE ? OR event_types LIKE ? OR entity_names LIKE ? OR ...) AND ep_num < ?
```
- 키워드 최대 5개 x 3개 컬럼 = 15개 LIKE 조건 풀스캔
- **소요 시간**: 200행 x 15 LIKE = 5-15ms

**판정**: **MANAGEABLE** -- 200행 규모에서 LIKE 풀스캔은 수 밀리초. 500화+에서는 체감될 수 있음.

**권고 조치**:
1. `episode_meta`에 `entity_names` FTS(Full-Text Search) 인덱스 또는 별도 정규화 테이블 검토
2. `causal_graph`에 `ep_num` 인덱스 추가:
   ```sql
   CREATE INDEX IF NOT EXISTS idx_causal_graph_ep ON causal_graph(ep_num)
   ```
3. `episode_meta`에 `arc_no` 인덱스 추가 (벡터 검색 결과 필터링 시 유용):
   ```sql
   CREATE INDEX IF NOT EXISTS idx_episode_meta_arc ON episode_meta(arc_no)
   ```

---

### 5-3. 서브쿼리 성능

**위치**: `get_npc_latest_fields()` (db_manager.py L1739-1749)
```sql
SELECT field_name, new_value FROM npc_history
WHERE npc_name = ? AND id IN (
    SELECT MAX(id) FROM npc_history WHERE npc_name = ? GROUP BY field_name
)
```
- 상관 서브쿼리 내 GROUP BY는 `idx_npc_history_name` 인덱스를 활용
- NPC 1명의 field 종류 약 10-15개 -> 15회 MAX 집계 = **1-2ms**

**판정**: **SAFE** -- 인덱스로 보호됨

---

## 6. 벡터 검색 성능

### 6-1. vec_episodes 가상 테이블

**현재 구성**:
- sqlite-vec `vec0` 확장 사용
- 임베딩 차원: 3072 (gemini-embedding-001)
- 각 벡터: 3072 x 4 bytes = **12,288 bytes (12KB)**
- 검색 알고리즘: KNN (brute-force, sqlite-vec 기본)

**200화 시점 추정**:
- 200개 벡터 x 12KB = **2.4MB** 벡터 데이터
- KNN 검색: 200개 벡터 전체 스캔 (sqlite-vec는 ANN이 아닌 정확한 KNN)
- 검색 시간: 200 x 3072 내적 연산 = 약 **2-5ms**
- 멀티쿼리 검색 (`retrieve_multi_query_context`): 쿼리당 1회 KNN x 최대 5-7쿼리 = **10-35ms**
- NPC 컨텍스트 검색 (`retrieve_npc_context`): entity LIKE + 벡터 쿼리 최대 7개 = **30-70ms**

**500화 시점 추정**:
- 500 x 12KB = 6MB 벡터 데이터
- KNN 500벡터: 약 **5-12ms/쿼리**
- 멀티쿼리: **25-84ms**

**판정**: **MANAGEABLE** -- 200화에서는 충분히 빠르다. 1,000화+ 에서는 ANN (Approximate Nearest Neighbor) 전환 검토가 필요하다.

**권고 조치**:
1. 현재는 개선 불필요. 500화 시점에서 벡터 검색 latency 계측 (이미 `perf_timer` 인프라 존재)
2. 1,000화+ 대비: sqlite-vec의 `vec0_flat` → `vec0_hnswlib` 전환 또는 별도 벡터 DB 검토

### 6-2. 임베딩 캐시

**현재**: `_embed_cache` OrderedDict, 최대 128개 슬롯, MD5 해시 키

**200화 시점**:
- 128개 x 3072 float x 4B = **1.5MB** (가득 차도 무시할 수준)
- 동일 텍스트 재임베딩 방지 효과: API 호출 절감 (비용 + latency)
- 세션 간 캐시는 초기화됨 (인메모리 전용)

**판정**: **SAFE** -- 128개 상한과 LRU가 적절

---

## 7. Context Window 압박

### 7-1. 200화 시 프롬프트 주입 컨텍스트 총량

`build_mandatory_context()` (stage4_context_builder.py L413-724)에서 조립되는 컨텍스트 섹션별 추정:

| 섹션 | 200화 추정 크기 | 상한 | 비고 |
|------|-----------------|------|------|
| fact_ledger.to_summary() | 5,000-15,000자 | `max_chars=15000` | 인물 30명, 아이템 20개, 장소 10개 |
| world_state.get_summary() | 3,000-5,000자 | `max_chars=5000` | |
| state_tracker 16종 요약 | 5,000-20,000자 | **없음** | **병목** |
| resolved_plots_summary | 3,000-10,000자 | **없음** | **병목** |
| 벡터 검색 결과 | 2,000-5,000자 | `vector_max_results_s4=16` | |
| 확장 Lookback (4-10화 발췌) | 1,500-4,000자 | `lookback_total_chars=4000` | |
| Arc 요약 (최근 3개 Arc) | 1,000-3,000자 | | |
| 시리즈/볼륨 요약 | 1,000-3,000자 | | |
| SemanticPlotGuard 경고 | 500-1,000자 | | |
| 페이싱 분석 | 300-500자 | | |
| ForeshadowTracker | 500-1,000자 | | |
| SC Retrieval 섹션 | 2,000-10,000자 | `stage4_total_budget=50000` | |
| **mandatory_context 합계** | **25,000-77,000자** | | |

여기에 추가로:
| 추가 컨텍스트 | 200화 추정 | 비고 |
|---------------|-----------|------|
| prev_manuscripts_text (30화 전문) | **150,000자** | **최대 병목** |
| arc_tactical | 3,000-10,000자 | |
| hud_report | 1,000-3,000자 | |
| blueprint | 5,000-10,000자 | |
| style_guide | 2,000-3,000자 | |
| purism_prompt | 500-1,000자 | |
| chain_link_section | 200-500자 | |
| **전체 프롬프트 추정** | **190,000-260,000자** | |

### 7-2. Gemini Context Window 대비

- Gemini 1.05M 토큰 입력 제한
- 한국어 1자 = 약 1.2-1.5 토큰
- 260,000자 x 1.3 = **338,000 토큰** (제한의 약 32%)
- `smart_truncate()` 상한: 800,000자 (`MAX_CONTEXT_CHARS`)
- `_apply_context_budget()` 예산: 50,000자 (mandatory_context 부분만)

**판정**: **BOTTLENECK** -- Context Window 자체는 여유가 있으나, **30화 전문 (150,000자)이 전체 프롬프트의 60%를 차지**한다. 이 데이터의 대부분은 Director/Writer가 실질적으로 참조하지 않는 구간이다.

**권고 조치**:
1. **30화 전문 로드를 5화 전문 + 25화 요약으로 변경** (가장 큰 개선 효과):
   - 최근 5화: 전문 (25,000자)
   - 6-30화: `get_recent_manuscript_excerpts()` 활용 (500자 x 25 = 12,500자)
   - **절감 효과**: 150,000자 -> 37,500자 (**112,000자, 75% 절감**)
2. state_tracker 16종 요약에 총량 상한 추가 (예: 15,000자)
3. `resolved_plots_summary`에 최대 출력 항목 수 제한

---

## 8. 파일 시스템

### 8-1. drafts/ 디렉토리 파일 누적

**현재 동작**: 에피소드마다 `drafts/` 디렉토리에 원고 파일 저장. 형식: `{ep_num}_draft.txt` 또는 유사 패턴.

**200화 시점**:
- 200개 텍스트 파일 x 평균 5-15KB = **1-3MB** 총 디스크
- NTFS/ext4에서 200개 파일은 디렉토리 탐색에 전혀 부담이 되지 않음 (수천 개부터 체감)
- `os.listdir()` 또는 `pathlib.Path.glob()` 성능: 200파일 = **<1ms**

**판정**: **SAFE** -- 10,000개 파일까지 문제 없음

---

## 종합 권고 조치 우선순위

| 순위 | 대상 | 등급 | 조치 | 예상 효과 |
|------|------|------|------|-----------|
| **1** | 30화 전문 로드 (1-1) | BOTTLENECK | 5화 전문 + 25화 발췌로 변경 | Context 75% 절감, I/O 80% 절감 |
| **2** | resolved_plots 무한 증가 (2-1) | BOTTLENECK | 최대 30개 출력 + 오래된 것 요약 압축 | 프롬프트 3,000-7,000자 절감 |
| **3** | state_tracker 요약 총량 (7-1) | BOTTLENECK | 16종 합산 15,000자 상한 | 프롬프트 안정화 |
| **4** | episode_meta 인덱스 (5-2) | MANAGEABLE | entity_names 인덱스 또는 FTS | LIKE 쿼리 최적화 |
| **5** | causal_graph 인덱스 (5-2) | MANAGEABLE | ep_num 인덱스 추가 | 인과관계 조회 최적화 |
| **6** | sentence_hashes 정리 (2-4) | MANAGEABLE | 100화 이전 해시 정리 정책 | DB 파일 크기 안정화 |
| **7** | _MAX_BIBLE_CACHE (1-3) | MANAGEABLE | 5 -> 10 슬롯 | 캐시 미스율 감소 |
| **8** | entity_destructions 상한 (2-5) | MANAGEABLE | 최대 200개 FIFO | 초장기 연재 안전망 |

---

## 부록 A: 200화 프로필 요약

```
에피소드 수:       200
Arc 수:            40
원고 총 자수:      ~1,000,000자
DB 파일 크기:      ~15-25MB
벡터 데이터:       ~2.4MB (200 x 12KB)
NPC 이력 행:       ~10,000-20,000
문장 해시 행:      ~20,000
인메모리 합계:     ~85MB (Python 기본 포함)
프롬프트 크기:     ~190,000-260,000자 (현재)
프롬프트 크기:     ~80,000-110,000자 (권고 적용 후)
Gemini 토큰 사용:  ~338,000 (현재) / ~130,000 (권고 적용 후)
```

---

## 부록 B: 코드 위치 참조

| 항목 | 파일 | 줄 번호 |
|------|------|---------|
| 30화 전문 로드 | `modules/core/stage4_context_builder.py` | L332-345 |
| 누적 Bible 캐시 | `modules/core/db_manager.py` | L817-908 |
| resolved_plots | `modules/domain/agents/state_tracker.py` | L132 |
| entity_name_registry | `modules/domain/agents/state_tracker.py` | L134-135 |
| sentence_hashes 테이블 | `modules/core/db_manager.py` | L401-412 |
| LIKE 풀스캔 쿼리 | `modules/core/db_manager.py` | L1650-1657 |
| LIKE 풀스캔 (벡터) | `modules/core/vec_memory.py` | L548-564, L724-733 |
| 벡터 KNN 검색 | `modules/core/vec_memory.py` | L672-711 |
| 임베딩 캐시 | `modules/core/vec_memory.py` | L73-74 |
| smart_truncate | `modules/core/constants.py` | L135-153 |
| context budget | `modules/core/stage4_context_builder.py` | L171-227 |
| fact_ledger 요약 | `modules/core/fact_ledger.py` | L390-470 |
| StateTracker 16종 요약 | `modules/domain/agents/state_tracker.py` | L1230-1280 |
| NPC 이력 조회 | `modules/core/db_manager.py` | L1729-1749 |
| DB 인덱스 선언 | `modules/core/db_manager.py` | L397-458 |
