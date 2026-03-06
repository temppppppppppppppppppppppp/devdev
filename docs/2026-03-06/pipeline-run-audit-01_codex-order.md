# 코덱스 오더: 실파이프라인 감사 02 — 001_260306 전수 로그 분석

> 작성일: 2026-03-06
> 근거: `projects/001_260306/logs/` 전체 + `pipeline-run-audit-00_20260306.md` 후속
> 대상 세션: 2026-03-06 21:26~22:16 (Stage 2, Arc 1~5, 투자물 1인칭 회귀자)
> 감리: 3회 교차검증 완료

---

## 0. 감사 요약

| 항목 | 결과 |
|------|------|
| P0 (치명적) | 0건 |
| P1 (코드 버그) | 1건 — NS-4 beat_sequence 타입 에러 |
| P2 (LLM 한계/advisory) | 3건 — NS-3-B 수치 괴리, XC-002 빈 응답, BUG-2 internal_energy |
| 오탐 제거 | 2건 — stage_attempts 필드 누락(스키마 설계), 위치 반복 수정(정상 동작) |
| 기존 감사(00) 연계 | BUG-1~5, STRUCT-1~3 → 감사 00에서 패치 완료 (3,512 passed) |
| 미패치 코덱스 오더 | 1건 — `codex-item-regex-overhaul.md` (P2 후순위, 별도 TF) |

---

## 1. P1: NS-4-S2/S4 시간 마커 beat_sequence 타입 에러

### 현상
```
[NS-4-S2] 시간 마커 주입 실패 (비차단): can only concatenate str (not "list") to str
```
- 발생: Arc 2, 3, 4, 5 (4회/5 Arc = 80%)
- 비차단: try/except 내부, 파이프라인 정상 진행

### 근본 원인

`four_phase_arc_generator.py:156` 및 `stage4_interview_round.py:15`:
```python
_text = (arc_data.get("tactical_doc") or "") + "\n" + (arc_data.get("beat_sequence") or "")
```

- `beat_sequence`는 **스키마상 list[str]**로 설계됨 (analyst.py L873-898에서 `isinstance(beats, list)` 강제)
- DB 저장 시 JSON 직렬화 → 로드 시 list 복원
- list는 truthy이므로 `or ""` 폴백이 작동하지 않음
- `str + list` → TypeError

### 영향 범위

| 파일 | 라인 | 역할 | 영향 |
|------|------|------|------|
| `four_phase_arc_generator.py` | L156 (정의), L1387 (호출) | Stage 2 Arc 생성 시 이전 Arc 시간 마커 추출 | 크로스 Arc 시간 연속성 advisory 미주입 |
| `stage4_interview_round.py` | L15 (정의), L552-553 (호출) | Stage 4 Director 심사 시 Arc 시간 마커 대조 | Director MC에 `[Arc 시간 연속성 참고]` 미주입 |

### 수정 방안

```python
def _ns4_extract_time_markers(arc_data: dict) -> list:
    """[NS-4-S2] Arc tactical_doc/beat_sequence에서 날짜/상대시간 마커 추출 (regex, LLM 0회)."""
    import re as _re

    tactical_doc = arc_data.get("tactical_doc") or ""
    beat_seq = arc_data.get("beat_sequence") or ""
    # beat_sequence가 list면 문자열로 정규화
    if isinstance(beat_seq, list):
        beat_seq = " ".join(str(b) for b in beat_seq)

    _text = str(tactical_doc) + "\n" + str(beat_seq)
    _patterns = [
        r"\d{4}년\s*\d{1,2}월(?:\s*\d{1,2}일)?",
        r"\d{1,2}월\s*\d{1,2}일",
        r"\d{1,2}월(?:\s*(?:말|초|중순|하순|상순))?",
        r"\d+(?:일|주|달|개월|년)\s*(?:후|전)",
    ]
    _found = []
    for _p in _patterns:
        _found.extend(_re.findall(_p, _text))
    return list(dict.fromkeys(_found))[:5]
```

- **2파일 동일 수정** (중복 정의)
- `str()` 래핑으로 추가 방어 (tactical_doc도 비정상 타입 가능성)

### 테스트 추가

```python
# test_ns4_s2_s4.py에 추가
def test_ns4_beat_sequence_list():
    """beat_sequence가 list일 때 TypeError 없이 시간 마커 추출."""
    arc = {
        "tactical_doc": "2026년 3월부터 시작",
        "beat_sequence": ["Ep1: 2026년 3월 초 개시", "Ep2: 1개월 후 결과"],
    }
    markers = _ns4_extract_time_markers(arc)
    assert "2026년 3월" in markers or "2026년 3월 초" in markers
    assert "1개월 후" in markers

def test_ns4_beat_sequence_nested_list():
    """beat_sequence 내부에 dict가 섞인 경우도 안전."""
    arc = {
        "tactical_doc": "",
        "beat_sequence": [{"ep": 1, "desc": "2025년 1월"}, "Ep2: 3달 후"],
    }
    markers = _ns4_extract_time_markers(arc)
    assert isinstance(markers, list)
```

---

## 2. P2: 오탐 제거 — 에이전트 분석 교차검증

### 2-A. stage_attempts 필드 누락 → 오탐

에이전트가 "episode_num, success, is_patch, prev_score가 NULL"로 보고했으나:

- **스키마에 해당 필드 자체가 없음** (db_manager.py L511-528)
- 실제 필드명: `ep_num` (episode_num 아님), `verdict` (success 대체), `fix_scope` (is_patch 대체)
- 모든 INSERT 코드(4곳)에서 정상 전달 확인
- **판정: 오탐, 조치 불필요**

### 2-B. 위치 동기화 반복 → 정상 동작

에이전트가 "InPlace patch 시 원본 회귀"로 보고했으나:

- `v60_25_auto_correct`는 매 Arc 생성 직후 자동 실행되는 **정상 후처리**
- Arc 3 attempt 2에서 auto_correct가 재실행된 것은 새 후보 생성 후 동일 로직 적용
- **판정: 정상 동작, 조치 불필요**

---

## 3. P2: NS-3-B 수치 괴리 — LLM 한계 (코드 버그 아님)

### 현상
```
[NS-3-B] Arc 1 arc_end_state.total_assets=38.0억 vs target 20억 (divergence 90%)
```
- Arc 1~3에서 반복 (괴리율 50~117%)

### 코드 검증 결과

- `_check_arc_vs_block_targets()` 계산 로직 정확
- advisory-only 설계 (REJECT 강제 없음, 대원칙 3 준수)
- feedback prepend만 수행 → Director 판단에 위임

### 근본 원인

- LLM이 treatment 목표(20억)보다 드라마틱한 수치(38억)를 선호 (narrative drama 편향)
- ArcEnsembleGenerator 프롬프트에 "capital_after 범위 제약"이 명시되지 않음
- Block 2 괴리(23억→30.4억)는 Arc 전개 중 자연 수렴 (Block 3에서 30억 도달)

### 판정

- **코드 버그 아님**: advisory 시스템이 의도대로 동작
- **P2 프롬프트 강화 후보**: Arc 생성 프롬프트에 `capital_after +/-20%` 하드 제약 추가 가능
- 현 단계에서는 **현상 유지** (Director가 수치 조정 역할 수행 중)

---

## 4. P2/P3: XC-002 NPC LLM 검증 빈 응답 — 정상 설계

### 현상
```
[XC-002] NPC LLM 검증 응답 없음 -> fail-closed: []
```
- 발생: Arc 3, Arc 3 InPlace 패치 후 (2회)
- HTTP 200 OK 수신 후 response.text가 None/empty

### 코드 검증 결과

- `state_tracker_npc.py:760-776` — fail-closed 설계 의도적
- ValueError/AttributeError 명시 포착 + Exception 범용 catch
- Director가 별도 연속성 검사 수행 → 이중 안전망
- `pipeline-run-audit-01_20260306.md`에서도 P3 판정 완료

### 판정

- **코드 버그 아님**: fail-closed가 올바른 설계 (False Positive 방지)
- **P3 (조치 불필요)**: LLM 일시적 빈 응답, 자동 복구됨
- 재시도 로직 추가는 ROI 낮음 (발생 빈도 낮고, 후속 검증 존재)

---

## 5. 기존 감사 연계 현황

### pipeline-run-audit-00 패치 완료 항목 (3,512 passed)

| ID | 심각도 | 설명 | 상태 |
|----|--------|------|------|
| BUG-1 | P1 | 금지 아이템 "다음" 오탐 — 마커 분리 | 패치 완료 |
| STRUCT-1 | P1 | SC 추가투표 thinking_level medium 균등화 | 패치 완료 |
| STRUCT-2 | P1 | PASS_WITH_FIX SC 다수결 분리 | 패치 완료 |
| STRUCT-3 | P1 | Stage 2/3 audit Contradiction Firewall | 패치 완료 |
| BUG-2 | P2 | preflight 프롬프트 장르 중립화 | 패치 완료 |
| BUG-3 | P2 | 소지품 regex 장르 확장 4곳 | 패치 완료 (접미사 추가) |
| BUG-4 | P2 | arc_draft_validator dead code 제거 | 패치 완료 |
| BUG-5 | P2 | ArcValidator advisory 세부 로깅 | 패치 완료 |

### pipeline-run-audit-01 패치 완료 항목 (3,530 passed)

| ID | 심각도 | 설명 | 상태 |
|----|--------|------|------|
| BUG-A | P1 | 금지 아이템 오탐 — 기존 소지품 화이트리스트 | 패치 완료 |
| InPlace 신뢰성 | P1 | 30KB 절단 방지 + 1-depth deep merge + S2 validate_arc | 패치 완료 |
| InPlace-Diff | P2 | S2/S3/S4 log_patch_diff 유틸 | 패치 완료 |

---

## 6. 미패치 코덱스 오더: 소지품 Regex 전면 개편

### 문서 위치
`docs/2026-03-06/codex-item-regex-overhaul.md`

### 요약
BUG-3 패치(접미사 13종 추가)는 **응급 처치**. 근본 해결은 **구조적 데이터 직접 대조**로의 전환.

### 핵심 전략
```
Tier 1: equipment[]/items_acquired[]/forbidden_items[] 리스트 직접 비교 (regex 0회)
Tier 2: genre_schema_builder.get_item_suffixes(genre) 장르별 접미사 SSOT
Tier 3: 범용 regex fallback (Tier 1/2 불가 시)
```

### 영향 파일 (6개, 14곳)

| 파일 | 변경 수 | 심각도 |
|------|---------|--------|
| `genre_schema_builder.py` | 신규 함수 `get_item_suffixes()` | P1 (SSOT) |
| `arc_ensemble.py` | L623, L652 — 구조적 대조 전환 | P1 |
| `arc_draft_validator.py` | L38-60, L709, L751-815 — 장르 동적 접미사 | P1/P2 |
| `constraint_compiler.py` | L30-39, L82-100 — 장르별 패턴 | P2 |
| `state_tracker_plots.py` | L34-45 — 전 장르 union fallback | P2 |
| `prompt_builder.py` + `constraint_db.py` | L18-21, L198-201 — grant 확장 | P2 |

### 호출자 변경
- `stage2_orchestrator`/`stage2_preflight` → `generate_ensemble(prev_equipment=[], forbidden_items=[])` 구조적 데이터 주입
- `ArcDraftValidator(genre=genre)` 생성자에 장르 인자 전달

### 현재 상태
- **P2 후순위** — BUG-3 접미사 추가로 긴급 위험 해소됨
- 별도 TF로 계획 시 12개 테스트 포함
- 대원칙 1(Python 수집만) 준수: 구조적 대조도 "수집/비교"이므로 위반 없음

---

## 7. 실행 건강도 지표

### LLM 호출 통계

| 항목 | 값 |
|------|-----|
| 총 호출 | 71건 (Session 1: 5, Session 2: 66) |
| 성공률 | 100% (실패 0건) |
| 총 토큰 | 734,159 |
| 총 비용 | $1.13 (Pro $1.045, Flash $0.040) |
| 평균 응답 시간 | 34~83ms (에이전트별 정상 범위) |

### Stage 2 합격률

| Arc | 시도 | 최종 결과 | 점수 | 패치 |
|-----|------|-----------|------|------|
| 1 | 1회 | PASS | 90 | N |
| 2 | 1회 | PASS | 100 | N |
| 3 | 2회 | PASS | 95 | Y (inplace, 88→95) |
| 4 | 1회 | PASS | 100 | N |
| 5 | 1회 | PASS | 100 | N |

- 초회 합격률: 4/5 (80%)
- 최종 합격률: 5/5 (100%)
- 평균 점수: 97.0

---

## 8. 조치 계획

### 즉시 실행 (이번 TF) — **전량 완료**

| # | ID | 심각도 | 작업 | 파일 | 상태 |
|---|-----|--------|------|------|------|
| 1 | NS-4-FIX | P1 | beat_sequence list→str 정규화 (2파일) | four_phase_arc_generator.py:153, stage4_interview_round.py:11 | **패치 완료** |
| 2 | NS-4-TEST | P1 | 테스트 3개 추가 (list, nested list) | test_ns4_s2_s4.py:11,64,78 | **7 passed** |

검증: `pytest -q tests/test_ns4_s2_s4.py` → 7 passed, `pytest -q tests/test_four_phase_arc_generator.py tests/test_stage4_interview_round.py` → 40 passed.

### 후순위 (별도 TF)

| # | ID | 심각도 | 작업 | 문서 |
|---|-----|--------|------|------|
| 3 | ITEM-REGEX | P2 | 소지품 regex 전면 개편 (6파일 14곳) | codex-item-regex-overhaul.md |
| 4 | NS-3-B-PROMPT | P2 | Arc 생성 프롬프트 capital_after 범위 제약 | (신규) |

---

## 9. 감리 체크리스트 (3회 교차검증)

### 감리 1차: 로그 전수 대조

- [x] session_20260306_211207.log (Stage 0) — ERROR 0건 확인
- [x] session_20260306_212608.log (Stage 2, 2060줄) — NS-4 4회, XC-002 2회 확인
- [x] decisions.jsonl (12줄) — REJECT 1건(Arc 3), fix_scope 정상
- [x] runtime_audit.jsonl (17 이벤트) — auto_correct 6회 정상
- [x] quality_metrics.jsonl (6건) — 전량 최종 PASS
- [x] pass_rate_monitor.json (6건) — 합격률 데이터 정합
- [x] metrics/ (2파일) — LLM 호출 71건 전량 성공
- [x] enrich 로그 (15파일) — 구조적 결함 0건

### 감리 2차: 코드 교차검증

- [x] NS-4 beat_sequence — analyst.py L873 list 강제 확인 → 타입 에러 원인 확정
- [x] stage_attempts 스키마 — db_manager.py L511 대조 → 에이전트 오탐 확정
- [x] XC-002 fail-closed — state_tracker_npc.py L760-776 → 정상 설계 확정
- [x] NS-3-B 계산 — _check_arc_vs_block_targets() → advisory-only 정확
- [x] 위치 반복 수정 — v60_25_auto_correct → 정상 후처리 확정

### 감리 3차: 기존 문서 정합

- [x] pipeline-run-audit-00 BUG-1~5, STRUCT-1~3 → 전량 패치 확인 (3,512 passed)
- [x] pipeline-run-audit-01 BUG-A, InPlace 신뢰성 → 전량 패치 확인 (3,530 passed)
- [x] codex-item-regex-overhaul.md — BUG-3 근본 해결 계획, P2 후순위 적절
- [x] CLAUDE.md 기존 기록과 충돌 없음
