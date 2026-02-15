# Phase 3 Feature B — 크로스 에피소드 반복 감지 청사진

> 작성: 2026-02-15, checkpoint `db07efd`
> 상태: **Step 1 완료** (`db07efd`)

---

## 1) 현재 기준선

| 항목 | 값 |
|------|-----|
| checkpoint | `b91e9bc` |
| 테스트 합계 | 263 (unit 43 + quality 15 + pipeline 89 + E2E 22 + regression 94) |
| 선행조건 A (품질 회귀 감지) | ✅ 완료 (`4b6ad8e`) |
| 선행조건 C (NPC 과잉 등장 경고) | ✅ 완료 (`409093c`) |
| 선행조건 Obs Step 1 (관측성 계측) | ✅ 완료 (`b4eaa58`) |
| ctx refs | stage2 350/43, stage4 325/23 |

---

## 2) 문제 정의

### 2-1. "반복"이란 무엇인가

장편 웹소설(30화+)에서 발생하는 반복은 3가지 수준으로 분류된다:

| 수준 | 예시 | 현재 감지 | 이번 범위 |
|------|------|----------|----------|
| **구문 반복** (Phrase) | "살기가 뿜어져 나왔다"가 매화 등장 | ✅ RepetitionGuard 3-gram (blocking) | ❌ 기존 유지 |
| **문장 반복** (Sentence) | 동일/유사 문장이 3화 연속 등장 | ❌ 미감지 | ✅ **이번 범위** |
| **구조 반복** (Structure) | "수련→돌파→적 조우→승리" 패턴 반복 | ⚠️ PatternTracker (비지속적) | ❌ 후속 |

**이번 범위: 문장 수준 크로스 에피소드 반복 감지**

- 정규화된 문장 단위로 최근 N화 대비 반복률 측정
- advisory WARNING만 출력 (blocking/REJECT 없음)
- Python 감지 → LLM 판단 대원칙 준수

### 2-2. 기존 RepetitionGuard와의 차이

| 속성 | RepetitionGuard (기존) | Feature B (신규) |
|------|----------------------|-----------------|
| 단위 | 3-gram (3단어 조합) | 정규화 문장 (15자+) |
| 위치 | `director_auditor.py` L568 | `stage4_orchestrator.py` `_process_pass_result()` |
| 시점 | Director 심사 전 (blocking) | PASS 확정 후 (advisory) |
| 저장 | ❌ 매회 재구축 | ✅ DB 지속 저장 |
| 정책 | `clean_score < 0.85` → REJECT | advisory WARNING만 |
| 임계값 | `premium.repetition.threshold: 3` | `cross_episode_repetition.overlap_warning: 5` |

### 2-3. False Positive / False Negative 위험

| 위험 | 원인 | 완화 |
|------|------|------|
| **FP: 장르 관용구** | "그는 검을 뽑았다", "눈을 감았다" 등 무협 필수 표현 | `min_sentence_length: 15`로 짧은 관용구 제외 + 정규화 후 해싱 |
| **FP: 고정 묘사** | 장소/인물 외모 묘사 재사용 | 최소 `overlap_warning: 5`로 소수 반복은 허용 |
| **FP: 의도적 반복** | 복선 회수, 반복 수사법 | advisory-only이므로 LLM이 최종 판단 (대원칙 준수) |
| **FN: 동의어 치환** | "뿜어져 나왔다" → "쏟아져 나왔다" | 이번 범위 밖 (후속: 임베딩 기반 유사도) |
| **FN: 구조적 반복** | 문장은 다르지만 장면 흐름 동일 | 이번 범위 밖 (후속: PatternTracker 지속화) |

---

## 3) 데이터/저장 설계

### 3-1. 신규 테이블: `episode_sentence_hashes`

```sql
CREATE TABLE IF NOT EXISTS episode_sentence_hashes (
    ep_num    INTEGER NOT NULL,
    sent_hash TEXT    NOT NULL,
    preview   TEXT,                          -- 원문 앞 50자 (디버깅/로그용)
    PRIMARY KEY (ep_num, sent_hash)
);
CREATE INDEX IF NOT EXISTS idx_sent_hash
    ON episode_sentence_hashes(sent_hash);
```

| 컬럼 | 타입 | 목적 |
|------|------|------|
| `ep_num` | INTEGER | 에피소드 번호 |
| `sent_hash` | TEXT | 정규화 문장의 SHA-256 해시 (hex, 64자) |
| `preview` | TEXT | 원문 미리보기 (WARNING 로그에 표시) |

**인덱스 `idx_sent_hash`**: 해시 기반 조회 최적화 — `WHERE sent_hash IN (...)` 쿼리에 필수.

### 3-2. 마이그레이션 전략

- `CREATE TABLE IF NOT EXISTS` + `CREATE INDEX IF NOT EXISTS` 패턴 사용
- `db_manager.py`의 `_initialize_tables()` 또는 동등 위치에 추가
- **기존 DB 호환**: 신규 테이블만 추가, 기존 테이블/컬럼 변경 없음
- **빈 DB 시작**: 테이블 자동 생성, 데이터 0건 → 감지 스킵 (graceful)
- **기존 프로젝트 마이그레이션**: 과거 에피소드 핑거프린트 미존재 → 다음 PASS부터 축적 시작

### 3-3. 저장 규모 추정

| 항목 | 추정값 |
|------|--------|
| 에피소드당 문장 수 | ~100-200 (5000자 기준) |
| 문장당 레코드 크기 | ~130B (ep_num 4B + hash 64B + preview 50B + overhead) |
| 에피소드당 저장 | ~20-26KB |
| 30화 프로젝트 | ~600-780KB |
| 100화 프로젝트 | ~2-2.6MB |

**결론**: SQLite에 부담 없는 수준. 별도 정리/압축 불필요.

### 3-4. DB Manager 신규 메서드

```python
# 저장
def store_sentence_hashes(self, ep_num: int, hashes: list[tuple[str, str]]) -> None:
    """(sent_hash, preview) 리스트를 episode_sentence_hashes에 저장."""

# 조회: 현재 에피소드 해시 vs 과거 에피소드 해시 교차
def find_repeated_sentence_hashes(
    self, current_hashes: list[str], before_ep: int, lookback: int = 5
) -> list[dict]:
    """현재 해시 중 최근 N화에 존재하는 것들을 반환.
    Returns: [{"sent_hash": str, "ep_num": int, "preview": str}, ...]"""

# 특정 에피소드 해시 조회 (테스트용)
def get_sentence_hashes(self, ep_num: int) -> list[dict]:
    """해당 에피소드의 저장된 해시 전량 반환."""
```

---

## 4) 감지 로직 설계

### 4-1. 문장 핑거프린팅 파이프라인

```
원고 텍스트 (5000자+)
  │
  ├─ 1) 문장 분리: 한국어 종결어미 기반 split
  │     패턴: r'(?<=[다요죠함임음됨었았겠습])[\.\!\?]\s+'
  │     + 줄바꿈 기반 보조 split
  │
  ├─ 2) 정규화: 공백 통일 + 특수문자 제거 + strip
  │     re.sub(r'\s+', ' ', sent).strip()
  │
  ├─ 3) 필터링: min_sentence_length (기본 15자) 미만 제외
  │     대화문 태그("", 「」) 내부도 포함
  │
  └─ 4) 해싱: hashlib.sha256(normalized.encode()).hexdigest()
       → (hash, preview=original[:50]) 튜플 리스트 반환
```

**모듈 위치**: `modules/core/repetition_guard.py` — 기존 RepetitionGuard 클래스에 `@staticmethod` 추가

```python
@staticmethod
def extract_sentence_fingerprints(
    manuscript: str,
    min_length: int = 15,
) -> list[tuple[str, str]]:
    """원고에서 정규화 문장 핑거프린트 추출.
    Returns: [(sha256_hex, preview_50chars), ...]"""
```

### 4-2. 크로스 에피소드 비교 로직

```
PASS 확정 후 (_process_pass_result)
  │
  ├─ 1) 현재 원고 핑거프린팅
  │     fps = RepetitionGuard.extract_sentence_fingerprints(manuscript, min_length)
  │
  ├─ 2) DB 저장 (축적)
  │     db.store_sentence_hashes(ep_num, fps)
  │
  ├─ 3) 과거 대비 조회
  │     repeated = db.find_repeated_sentence_hashes(
  │         [h for h, _ in fps], before_ep=ep_num, lookback=lookback
  │     )
  │
  ├─ 4) 중복률 계산
  │     overlap_count = len(set(r["sent_hash"] for r in repeated))
  │     overlap_ratio = overlap_count / len(fps) if fps else 0
  │
  └─ 5) 임계값 비교 → advisory WARNING
        overlap_count >= warning_threshold → WARNING
        overlap_count >= regression_threshold → 강한 WARNING
```

### 4-3. 감지 함수 (모듈 레벨 순수 함수)

`stage4_orchestrator.py`에 추가:

```python
def _detect_cross_episode_repetition(
    fingerprints: list[tuple[str, str]],
    repeated: list[dict],
    *,
    warning_threshold: int = 5,
    regression_threshold: int = 10,
) -> dict | None:
    """크로스 에피소드 문장 반복 감지 (advisory-only).
    Returns: {detected, severity, overlap_count, overlap_ratio, top_repeated, warning} or None"""
```

### 4-4. 정책

| 정책 | 값 | 근거 |
|------|-----|------|
| **advisory-only** | WARNING 로그만 | 대원칙 "Python은 수집만" |
| **비차단** | REJECT/재생성 없음 | Director 주권주의 |
| **soft-fail** | DB/해싱 예외 시 비전파 | 기존 패턴 동일 |
| **warning_threshold** | 5 문장 | 100-200 문장 중 5개(2.5-5%) 반복은 주의 수준 |
| **regression_threshold** | 10 문장 | 5-10% 반복은 심각 수준 |
| **lookback** | 5화 | 기존 RepetitionGuard window_size와 일치 |
| **min_sentence_length** | 15자 | "그는 웃었다"(5자) 같은 관용구 제외 |

### 4-5. 성능/복잡도 추정

| 작업 | 복잡도 | 예상 시간 |
|------|--------|----------|
| 문장 분리 + 정규화 + 해싱 | O(N) (N=문장 수) | <10ms |
| DB 저장 (INSERT) | O(N) batch | <50ms |
| DB 조회 (hash IN + ep 필터) | O(N × log M) (M=인덱스 크기) | <100ms |
| 총 오버헤드 | | <200ms (LLM 호출 대비 무시 가능) |

---

## 5) 수용 기준(AC)

| # | 수용 기준 | 검증 방법 |
|---|----------|----------|
| AC-1 | 동일 정규화 문장이 최근 5화 중 1화 이상에서 발견되고 overlap_count ≥ warning_threshold일 때 WARNING 로그 출력 | Unit: mock DB + caplog → WARNING 키워드 확인 |
| AC-2 | `_detect_cross_episode_repetition()` 반환 dict에 `detected`, `severity`, `overlap_count`, `overlap_ratio`, `top_repeated` 키 포함 | Unit: 반환 dict 키/타입 검증 |
| AC-3 | `validation.yaml`에 `cross_episode_repetition` 섹션 추가, `_threshold()` 헬퍼로 조회 가능 | Unit: YAML 없을 때 기본값 검증 |
| AC-4 | 첫 에피소드(DB 비어있음) 또는 lookback 내 데이터 없을 시 `None` 반환 (크래시 없음) | Unit: 빈 DB 테스트 |
| AC-5 | `episode_sentence_hashes` 테이블이 `CREATE TABLE IF NOT EXISTS`로 자동 생성됨 | Unit: 빈 DB → 테이블 존재 확인 |
| AC-6 | DB/해싱 예외 발생 시 `_process_pass_result()` 정상 완료 (비전파) | Unit: DB side_effect=RuntimeError → 정상 반환 |
| AC-7 | `extract_sentence_fingerprints()` 결과에 min_length 미만 문장 미포함 | Unit: 짧은 문장 필터링 검증 |
| AC-8 | 기존 263개 테스트 전량 통과 (회귀 없음) | Gate: pytest 5 스위트 |

---

## 6) 테스트 전략

### 6-1. Unit 테스트 (10~12개)

**파일**: `tests/test_cross_episode_repetition.py` (신규)

| # | 테스트 | 검증 |
|---|--------|------|
| 1 | `test_fingerprint_extraction_basic` | 3문장 원고 → 3개 (hash, preview) 튜플 |
| 2 | `test_fingerprint_min_length_filter` | 10자 미만 문장 제외 확인 |
| 3 | `test_fingerprint_normalization` | 공백 차이 있는 동일 문장 → 동일 해시 |
| 4 | `test_fingerprint_different_sentences` | 다른 문장 → 다른 해시 |
| 5 | `test_detection_overlap_warning` | overlap_count ≥ 5 → severity="warning" |
| 6 | `test_detection_overlap_regression` | overlap_count ≥ 10 → severity="regression" |
| 7 | `test_detection_below_threshold` | overlap_count < 5 → None |
| 8 | `test_detection_empty_fingerprints` | 빈 리스트 → None |
| 9 | `test_detection_keys_complete` | 반환 dict 키 5개 존재 확인 |
| 10 | `test_top_repeated_sorted` | top_repeated가 ep_num 오름차순 정렬 |

### 6-2. Integration 테스트 (4~5개)

**파일**: `tests/test_cross_episode_repetition.py` (같은 파일, 별도 클래스)

| # | 테스트 | 검증 |
|---|--------|------|
| 11 | `test_db_store_and_retrieve` | store → get_sentence_hashes → 일치 확인 |
| 12 | `test_db_find_repeated_across_episodes` | 2화 저장 → 동일 문장 → find_repeated 반환 |
| 13 | `test_db_lookback_respects_window` | 10화 전 데이터 → lookback=5 → 미반환 |
| 14 | `test_db_empty_no_crash` | 빈 DB → find_repeated → 빈 리스트 |

### 6-3. Hook 테스트 (2~3개)

**파일**: `tests/test_stage4_orchestrator.py` (기존 파일에 추가)

| # | 테스트 | 검증 |
|---|--------|------|
| 15 | `test_cross_repetition_hook_logs_warning` | overlap ≥ threshold → WARNING 로그 |
| 16 | `test_cross_repetition_hook_exception_non_propagating` | DB 예외 → 비전파 |
| 17 | `test_cross_repetition_hook_first_episode_no_crash` | ep=1 → 정상 완료 |

### 6-4. 멀티에피소드 Fixture 설계

```python
@pytest.fixture
def multi_episode_manuscripts():
    """3화분 원고 — 의도적 반복 문장 포함."""
    SHARED_SENTENCE = "이청풍은 검을 높이 들어 창공을 향해 한 줄기 검기를 뿜어냈다."
    UNIQUE_PREFIX = [
        "제1화: 청풍산장의 아침이 밝았다.",
        "제2화: 낙양의 거리는 인파로 붐볐다.",
        "제3화: 흑풍채의 암흑 속에서 그림자가 움직였다.",
    ]
    return [
        f"{UNIQUE_PREFIX[i]} {SHARED_SENTENCE} 그 외 고유 내용..." * 10
        for i in range(3)
    ]

@pytest.fixture
def e2e_db_with_hashes(tmp_path, multi_episode_manuscripts):
    """DB에 2화분 핑거프린트 사전 저장."""
    db = DBManager(tmp_path / "test.db")
    for ep, ms in enumerate(multi_episode_manuscripts[:2], 1):
        fps = RepetitionGuard.extract_sentence_fingerprints(ms)
        db.store_sentence_hashes(ep, fps)
    yield db
    db.close()
```

### 6-5. 회귀 스위트

| 스위트 | 통과 기대 |
|--------|----------|
| `test_stage2_preflight_helpers.py` | 43 |
| `test_quality_regression.py` | 15 |
| `test_stage2_pipeline.py` + `test_stage2_context.py` | 89 |
| `tests/e2e/` | 22 |
| `test_npc_history` + `test_config_manager` + `test_stage4_orchestrator` | 94+ |
| **합계** | **263+ (신규 추가분 제외 불변)** |

---

## 7) 실행 단계 계획

### Step 1: Core — 핑거프린팅 + DB + 감지 로직 ✅ 완료

**커밋**: `db07efd`

**수정 파일**:
- `modules/core/db_manager.py` — `episode_sentence_hashes` 테이블 + 인덱스 + 3 메서드 (+62줄)
- `modules/core/repetition_guard.py` — `extract_sentence_fingerprints()` 정적 메서드 (+43줄)
- `modules/core/stage4_orchestrator.py` — `_detect_cross_episode_repetition()` + hook (+87줄)
- `config/settings/validation.yaml` — `cross_episode_repetition` 섹션 (+8줄)
- `tests/test_cross_episode_repetition.py` — 신규 (13건, 169줄)
- `tests/test_stage4_orchestrator.py` — hook 테스트 3건 추가

**결과**:
- 신규 16건 + 기존 263건 = 279건 전량 통과
- pre-commit 통과

### Step 2: 문서 동기화 ✅ 완료

**수정 파일**:
- `내일작업.md` — 완료 행 추가, 테스트 기준선 갱신, 우선순위 갱신
- `docs/프로젝트_현황_로드맵_2026-02-14.md` — checkpoint/테스트/완료 갱신
- `CLAUDE.md` — checkpoint/테스트/완료/RISKY 갱신
- 본 문서 상태 → "완료"

**종료 조건**:
- 4개 문서 checkpoint/테스트 수 일치
- 커밋

---

## 8) 비범위

- RepetitionGuard 기존 3-gram 로직 변경 — **불변**
- Director audit blocking 로직 변경 — **불변**
- PatternTracker 구조 반복 감지 확장 — **후속**
- 임베딩 기반 의미 유사도 비교 — **후속** (sqlite-vec 활용 가능)
- Stage 2 arc context에 반복 경고 주입 — **후속** (A의 trend injection 패턴 활용)
- Streamlit UI 대시보드 — **불변**
- 자동 REJECT/재생성 — **대원칙 위반, 금지**

---

## 9) 롤백 전략

| 방법 | 조치 |
|------|------|
| **코드 롤백** | `git revert <commit>` — 감지 로직만 제거, 파이프라인 동작 불변 |
| **런타임 비활성화** | `validation.yaml`에 `cross_episode_repetition.enabled: false` → hook 스킵 |
| **DB 정리** | `DROP TABLE IF EXISTS episode_sentence_hashes` — 다른 테이블 무영향 |
| **영향 범위** | advisory-only이므로 비활성화 시 기존 동작과 100% 동일 |

---

## 10) 향후 확장 경로

| 순서 | 기능 | 전제 |
|------|------|------|
| 다음 | Stage 2 context에 반복 경고 주입 | B 완료 후 |
| 중기 | 임베딩 기반 의미 유사도 (sqlite-vec) | B 안정 후 |
| 장기 | PatternTracker 구조 반복 지속화 | B + 임베딩 완료 후 |
| 장기 | D. 대리만족 프레임워크 | A~C 전체 안정 후 |
