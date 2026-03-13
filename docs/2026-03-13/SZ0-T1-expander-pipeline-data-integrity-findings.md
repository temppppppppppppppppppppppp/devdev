# SZ0-T1 Expander Pipeline Data Integrity Findings

> 작성일: 2026-03-13
> 상태: 3pass complete
> 대상: `modules/core/stage0/story_expander.py` (601줄), `modules/core/stage0/reverse_expander.py` (1,213줄)
> 감리 기준: 4대 원칙 (Python 수집만, 팩트시트 LLM만, 디렉터 주권, 사망 캐릭터 회상만)

---

## Executive Summary

StoryExpander(601줄)와 ReverseExpander(1,213줄)의 데이터 무결성을 3-pass 감리한 결과, **P0 0건, P1 1건, P2 4건, P3 4건**으로 확정되었다. 4대 원칙 위반은 0건이다.

사전 배정 이슈 4건 중:
- **P1-1** (list→dict 첫 항목 추출): P3으로 하향 — 방어 코드 이미 존재, 데이터 소실 범위 제한적
- **P1-2** (hud→state_changes 자동변환): 오탐 — 포맷 변환이며 판단이 아님
- **P1-3** (Arc stub 자동보강): 오탐 — LLM 추출 결과의 집계/재배치이며 새 팩트 생성 아님
- **P3-10** (generate_bible 조기반환): P2로 상향 — caller 방어 존재하나 None 반환 시 self.bible 미갱신

핵심 발견:
1. `persist_to_db()` 내 `save_anchor("arcs", ...)` 이중 호출 (원자성 위협)
2. `_extract_title()`이 첫 화 title만 사용하는 단순 휴리스틱 (제목 미추출 시 "무제")
3. LLM 실패 시 빈 데이터로 진행하는 패턴 일관성 양호 (fallback stub 패턴)
4. 배치 순차 처리 (prev_state 의존성) 정상 보장 — 테스트 2건으로 검증됨

---

## PASS 1 — 후보 수집

### story_expander.py

| ID | 라인 | 확신도 | 태그 | 설명 |
|----|------|--------|------|------|
| C-01 | L181-183 | 0.7 | data-loss | `analyze_concept`: LLM이 list 반환 시 `parsed[0]`만 추출. 단일 dict 기대 프롬프트이므로 list 반환은 예외 케이스 |
| C-02 | L277-279 | 0.8 | data-loss | `_generate_protagonist_detail`: list 반환 시 `result[0]`만 추출. **Pre-assigned P1-1** |
| C-03 | L208-210 | 0.7 | early-return | `generate_bible`: protagonist 생성 실패 시 `return None`. caller가 `self.bible` 참조 시 stale 값 위험. **Pre-assigned P3-10** |
| C-04 | L467-472 | 0.5 | silent-degrade | `_generate_skeleton`: LLM 응답 빈값 시 warning만 출력하고 계속 진행. 후속 `_generate_details`가 빈 skeleton으로 호출 |
| C-05 | L509-513 | 0.4 | fallback | `_generate_details`: LLM 실패 시 원본 batch(skeleton)를 그대로 사용. 의도된 graceful degradation |
| C-06 | L432-437 | 0.3 | format-norm | `_generate_extension_batch`: block_id 정규화 — Python이 ID 문자열만 교정. 대원칙 위반 아님 |

### reverse_expander.py

| ID | 라인 | 확신도 | 태그 | 설명 |
|----|------|--------|------|------|
| C-07 | L311-316 | 0.5 | heuristic | `_extract_title`: 첫 화 title 필드만 사용. 파일명 기반 "제N화"가 대부분이므로 실질 제목 미추출 |
| C-08 | L334-338 | 0.7 | data-loss | `_extract_protagonist`: list 반환 시 `result[0]`만 추출. C-02 동일 패턴 |
| C-09 | L369-373 | 0.7 | data-loss | `_extract_world_state`: list 반환 시 `result[0]`만 추출 |
| C-10 | L402-413 | 0.6 | fallback-stub | `_extract_single_episode_bible`: LLM 실패 시 빈 stub 반환. prev_state 체인에 빈 hud_snapshot 전파 |
| C-11 | L926-940 | 0.5 | principle? | `_save_episode_bibles_to_db`: hud에서 state_changes 필드 자동 추출. **Pre-assigned P1-2** |
| C-12 | L1046-1187 | 0.5 | principle? | `_enrich_arc_stubs_from_episode_bibles`: episode_bibles에서 arc stub 자동 보강. **Pre-assigned P1-3** |
| C-13 | L1018-1044 | 0.7 | atomicity | `_save_arc_stubs` + `_enrich_arc_stubs_from_episode_bibles`: 둘 다 `save_anchor("arcs", ...)` 호출. persist_to_db() 내 순차 실행이지만 이중 쓰기 |
| C-14 | L1180 | 0.6 | double-write | `_enrich_arc_stubs_from_episode_bibles` L1181: `ctx.db.save_anchor("arcs", arcs)` — `_save_arc_stubs` L1039와 동일 키. begin/commit 트랜잭션 내이므로 기능적 안전, 단 불필요한 I/O |
| C-15 | L435-444 | 0.3 | error-recovery | `extract_episode_bibles`: 예외 시 빈 stub 삽입. ep_num 순서 보존은 되나 hud 체인 단절 |
| C-16 | L919-924 | 0.3 | format-norm | `_save_episode_bibles_to_db`: new_npcs dict→str 정규화. 타입 변환이며 판단 아님 |
| C-17 | L408-410 | 0.3 | format-norm | `_extract_single_episode_bible`: `preset_registry.normalize_hud()` 호출. 필드명+타입 정규화이며 값 판단 아님 |

---

## PASS 2 — 교차 검증

### C-01, C-02, C-08, C-09: list→dict 첫 항목 추출 패턴

**Caller 추적**: 모든 LLM 호출에서 프롬프트가 단일 dict를 명시적으로 요청 (`"JSON: {...}"`). LLM이 list를 반환하는 것은 예외 케이스.

**테스트 근거**: `test_stage0_fixes.py`에 `_parse_json` 관련 테스트 없음. `test_reverse_expander_g2.py`에서는 `_extract_single_episode_bible`을 mock 처리하여 파싱 로직 미검증.

**기존 감리 대조**: `OPUS-TF-T2` T2-003에서 동일 패턴 언급, P2→P3으로 재분류됨. "호출부 L432에서 ep_num 보장. 외부 직접 호출 가능성은 낮음"

**판정**: 프롬프트가 단일 객체를 요청하므로 list 반환은 LLM anomaly. `[0]` 추출은 합리적 방어. 다만 list에 2개 이상 항목이 있으면 나머지 소실. 실제 운영 영향은 낮음.

→ **C-01, C-08, C-09**: P3 (방어 코드 존재, 실운영 영향 미미)
→ **C-02**: P3 (Pre-assigned P1-1 → P3으로 하향. 동일 근거)

### C-03: generate_bible() 조기 반환 (Pre-assigned P3-10)

**Caller 추적**:
- `StoryExpander.run()` L558-561, L588-590: `if not self.bible:` 방어 존재. 조기 반환 시 `(self.bible, self.treatment)` = `(None, [])` 반환
- `StageZeroManager.generate_from_concept()`: `test_stage0_fixes.py` L128-148에서 `generate_bible`이 정상 반환하는 경우만 테스트

**현상**: `generate_bible()`이 `return None`하면 `self.bible`은 초기값 `{}`가 아니라 갱신 안 됨. caller가 `self.bible`을 직접 참조하면 stale 상태 (빈 dict). 그러나 `run()` 내에서는 반환값으로만 사용.

**추가 위험**: `run()` 외부에서 `generate_bible()`을 단독 호출 후 `self.bible`을 참조하는 경우, None이 아닌 초기 `{}`가 남아있어 "성공한 것처럼" 보일 수 있음. 단, 현재 코드베이스에서 그런 호출 패턴은 발견 안 됨.

→ **C-03**: P2 (P3-10에서 P2로 상향. None 반환 자체는 올바르나, self.bible 미갱신으로 상태 불일치 가능)

### C-04, C-05: skeleton/details 빈값 진행

**분석**: `_generate_skeleton`에서 특정 배치 LLM 실패 시 해당 배치만 누락. 후속 배치는 `prev_titles`에 빈 내용 전파. `_generate_details`는 빈 skeleton이면 즉시 빈 리스트 반환. 의도된 graceful degradation.

→ **C-04**: P3 (warning 로깅으로 관찰 가능)
→ **C-05**: 오탐 (의도된 폴백)

### C-06, C-16, C-17: 포맷 정규화

**원칙 판정**: block_id 문자열 교정, NPC name dict→str 변환, HUD 필드명+타입 정규화 — 모두 "데이터 수집·포맷팅·전달"에 해당. 원칙 1 위반 아님.

→ 전부 오탐

### C-07: _extract_title 휴리스틱

**분석**: `load_drafts_from_folder`에서 `title = f"제{ep_num}화"`로 설정. `load_drafts_from_file`에서는 `ⓚ 제N화` 패턴의 뒤 텍스트가 title. 첫 화 title만 Bible MetaInfo에 넣는 것은 작품 전체 제목과 다를 수 있으나, 역설계 시점에서 원작 제목을 알 방법이 없으므로 합리적 fallback.

→ **C-07**: P3 (개선 가능하나 기능적 문제 아님)

### C-10: episode_bible 빈 stub 전파

**테스트 근거**: `test_reverse_expander_g2.py` L19-32에서 prev_state 순차 의존성 검증 완료. 빈 stub 삽입 시 다음 에피소드의 prev_state.hud_snapshot이 `{}`가 되어 LLM 프롬프트에 빈 JSON 전달. LLM이 "이전 상태 없음"으로 해석하여 독립 추출 수행 — 체인 단절이지만 데이터 오염은 아님.

→ **C-10**: P3 (graceful degradation, 체인 단절 범위 1회분)

### C-11: hud→state_changes 자동변환 (Pre-assigned P1-2)

**상세 분석** (L926-940):
```python
state_changes = {}
if hud:
    if hud.get("capital"):
        state_changes["capital"] = hud.get("capital")
    if hud.get("portfolio"):
        state_changes["portfolio"] = hud.get("portfolio")
    if hud.get("location"):
        state_changes["location"] = hud.get("location")
    ...
```

이것은 LLM이 추출한 `hud_snapshot`의 필드를 `bible_delta.state_changes` 형식으로 **재배치**하는 것이다. 새로운 팩트를 생성하거나 판단을 내리지 않는다. hud의 값을 그대로 state_changes 키로 복사할 뿐이다.

**원칙 판정**: 원칙 1 "Python은 데이터 수집·포맷팅·전달만" — 포맷 변환에 해당. 원칙 2 "팩트시트 수정 권한은 LLM만" — 새 팩트 생성이 아니라 LLM 출력의 재배치.

→ **C-11**: 오탐 (포맷 변환, 원칙 위반 아님)

### C-12: Arc stub 자동보강 (Pre-assigned P1-3)

**상세 분석** (L1046-1187): `_enrich_arc_stubs_from_episode_bibles`는 LLM이 추출한 episode_bibles 데이터를 arc 범위별로 **집계**한다:
- `new_npcs` → `introduced_npcs` 리스트로 합산
- `key_events` → `reveals` 리스트로 합산
- `relationships` → `relationship_changes` 구조로 변환
- `hud_snapshot` → `joint_docs`로 마지막 에피소드 상태 복사

모든 원본 데이터는 LLM이 생성한 것이며, Python은 범위 필터링 + 집계 + 형식 변환만 수행한다. 새로운 서사 판단이나 품질 결정은 없다.

**원칙 판정**: 원칙 1 준수 (수집·포맷팅). 원칙 2 준수 (팩트 수정 아님, 기존 LLM 출력 재조합). 원칙 3 해당 없음 (Director 관여 범위 아님).

→ **C-12**: 오탐 (데이터 집계/재배치, 원칙 위반 아님)

### C-13, C-14: save_anchor 이중 호출

**Caller 추적**: `persist_to_db()` L801-816:
1. L809: `_save_arc_stubs(ctx)` → `ctx.db.save_anchor("arcs", existing_arcs)` (L1039)
2. L813: `_enrich_arc_stubs_from_episode_bibles(ctx)` → `ctx.db.save_anchor("arcs", arcs)` (L1181)

`begin()`~`commit()` 트랜잭션 내이므로 원자성은 보장. 그러나 `_save_arc_stubs`가 저장한 후 `_enrich_arc_stubs`가 다시 로드(`load_anchor`)하고 수정 후 재저장한다. 이 과정에서:
- `_save_arc_stubs`가 기존 arc와 stub을 병합하여 저장
- `_enrich_arc_stubs`가 다시 로드하여 보강 후 저장

순차 실행이고 트랜잭션 내이므로 기능적으로 정상이다. 다만 `save_anchor` 2회 호출은 불필요한 I/O.

→ **C-13**: P2 (기능 정상, 설계 비효율. `_save_arc_stubs`에서 저장을 생략하고 `_enrich`에서 한 번만 저장하는 것이 효율적)
→ **C-14**: C-13에 통합

### C-15: 에러 시 빈 stub 삽입

C-10과 동일 분석. 테스트 검증됨.

→ C-10에 통합, 오탐

---

## PASS 3 — 최종 확정 Findings

### [SZ0-T1-F01] generate_bible() None 반환 시 self.bible 상태 불일치
- **Severity**: P2
- **파일**: `modules/core/stage0/story_expander.py` L208-210
- **현상**: `generate_bible()`이 protagonist 생성 실패 시 `return None`하지만 `self.bible`은 초기값 `{}`로 남는다. caller가 반환값 대신 `self.bible`을 참조하면 "빈 bible이 성공한 것처럼" 인식될 수 있다.
- **코드 근거**:
  ```python
  # L208-210
  if not protagonist or not isinstance(protagonist, dict) or "name" not in protagonist:
      logging.error("[StoryExpander] LLM 실패: protagonist 생성 불가")
      return None  # self.bible은 {} 상태로 유지
  ```
- **Downstream 영향**: `run()` 내에서는 `if not self.bible:` 가드(L558, L588)로 방어됨. 단독 호출 시에만 위험. 현재 코드베이스에서 단독 호출 패턴 미발견.
- **테스트 근거**: `test_stage0_fixes.py` L128-148에서 정상 케이스만 검증. None 반환 케이스 테스트 부재.
- **기존 문서**: `OPUS-TF-T2` T2-004에서 P1→P2로 재분류. 동일 이슈.
- **권장 조치**: `return None` 전에 `self.bible = None` 명시적 설정. 또는 `self.bible`을 `None`으로 초기화하여 미생성 상태를 명확히 구분.

### [SZ0-T1-F02] persist_to_db() 내 save_anchor("arcs") 이중 호출
- **Severity**: P2
- **파일**: `modules/core/stage0/reverse_expander.py` L1039, L1181
- **현상**: `persist_to_db()` 트랜잭션 내에서 `_save_arc_stubs`(L1039)와 `_enrich_arc_stubs_from_episode_bibles`(L1181) 양쪽에서 `save_anchor("arcs", ...)` 호출. `_enrich`가 `load_anchor("arcs")` → 수정 → `save_anchor` 순서이므로 기능적으로 정상이나, `_save_arc_stubs`의 저장은 `_enrich`가 덮어쓰므로 불필요.
- **코드 근거**:
  ```python
  # L809: _save_arc_stubs 내부에서 save_anchor("arcs", existing_arcs)
  # L813: _enrich_arc_stubs 내부에서 load_anchor("arcs") → 수정 → save_anchor("arcs", arcs)
  ```
- **Downstream 영향**: 트랜잭션 내이므로 데이터 무결성 위협 없음. 불필요한 I/O 1회.
- **테스트 근거**: `persist_to_db()` 통합 테스트 없음.
- **기존 문서**: 미발견.
- **권장 조치**: `_save_arc_stubs`에서 `save_anchor` 호출 제거, `_enrich_arc_stubs`에서만 최종 저장. 또는 `_save_arc_stubs`가 arc list를 반환하고 `_enrich`가 이를 인자로 받아 한 번만 저장.

### [SZ0-T1-F03] persist_to_db() 통합 테스트 부재
- **Severity**: P2
- **파일**: `modules/core/stage0/reverse_expander.py` L783-833
- **현상**: `persist_to_db()`는 5개 서브 메서드를 원자적 트랜잭션으로 실행하지만, 이를 검증하는 테스트가 없다. 롤백 경로(`L817-822`) 역시 미검증.
- **Downstream 영향**: DB 불일치 시 Stage 2/4가 불완전한 stub을 참조할 수 있음.
- **테스트 근거**: `test_reverse_expander_g2.py`에 `persist_to_db` 관련 테스트 0건.
- **기존 문서**: 미발견.
- **권장 조치**: mock DB로 정상 경로 + 중간 실패 시 롤백 경로 테스트 추가.

### [SZ0-T1-F04] _enrich_arc_stubs 내 relationship_changes 15개 캡
- **Severity**: P2
- **파일**: `modules/core/stage0/reverse_expander.py` L1131
- **현상**: `if not found and len(agg_relationships) < 15:` — 관계 변화가 15개를 초과하면 이후 새로운 NPC 관계가 무시된다. 장편(50화+)에서 관계 누적 시 캡에 도달할 수 있음.
- **코드 근거**:
  ```python
  if not found and len(agg_relationships) < 15:
      agg_relationships.append({...})
  ```
  이후 L1156에서 `[:10]`으로 추가 절삭.
- **Downstream 영향**: Arc stub의 `state_changes.relationship_changes`가 불완전해질 수 있으나, 역설계 stub 자체가 참고용이므로 실질 영향 제한적.
- **테스트 근거**: 없음.
- **기존 문서**: 미발견.
- **권장 조치**: P3 수준. 캡 값을 상수로 외부화하고, 15개 초과 시 warning 로그 추가.

### [SZ0-T1-F05] list→dict 첫 항목 추출 패턴 (4곳)
- **Severity**: P3
- **파일**: `story_expander.py` L181, L278 / `reverse_expander.py` L336, L371
- **현상**: LLM이 list를 반환할 때 `result[0]`만 추출. 프롬프트가 단일 객체를 요청하므로 list 반환은 LLM anomaly이나, 2개 이상 항목 시 나머지 소실.
- **Downstream 영향**: 실운영에서 관찰된 적 없음 (프롬프트 구조상 단일 객체 반환이 표준).
- **테스트 근거**: 없음 (list 반환 케이스 테스트 없음).
- **기존 문서**: `OPUS-TF-T2` T2-003 (P2→P3).
- **권장 조치**: 현행 유지. 필요 시 list 반환 시 warning 로그 추가.

### [SZ0-T1-F06] _extract_title 단순 휴리스틱
- **Severity**: P3
- **파일**: `modules/core/stage0/reverse_expander.py` L311-316
- **현상**: 작품 전체 제목 대신 첫 화의 title 필드를 사용. `load_drafts_from_folder`에서는 `"제1화"`가 기본값이므로 Bible MetaInfo의 title이 "제1화"가 됨.
- **Downstream 영향**: Bible의 MetaInfo.title이 의미 없는 값이 되나, Stage 2/4에서 title을 참조하는 곳이 없으므로 기능적 영향 없음.
- **테스트 근거**: 없음.
- **기존 문서**: 미발견.
- **권장 조치**: LLM에게 작품 전체 제목 추측을 요청하는 별도 프롬프트 추가 (선택적).

### [SZ0-T1-F07] _generate_skeleton 배치 실패 시 silent continuation
- **Severity**: P3
- **파일**: `modules/core/stage0/story_expander.py` L467-472
- **현상**: 특정 배치의 LLM 호출 실패 시 warning 로그만 출력하고 다음 배치 진행. 60블록 중 20블록 배치 1개 실패 시 40블록만 생성됨.
- **Downstream 영향**: Treatment 블록 수가 요청보다 적을 수 있으나, caller가 블록 수를 검증하지 않음.
- **테스트 근거**: `test_stage0_fixes.py` L80-85에서 배치 구조만 검증.
- **기존 문서**: 미발견.
- **권장 조치**: 생성된 블록 수가 요청의 50% 미만이면 warning → error 로그 레벨 상향.

### [SZ0-T1-F08] episode_bible 빈 stub 전파로 인한 HUD 체인 단절
- **Severity**: P3
- **파일**: `modules/core/stage0/reverse_expander.py` L435-444
- **현상**: LLM 호출 실패 시 `hud_snapshot: {}`인 빈 stub 삽입. 다음 에피소드의 prev_state에 빈 HUD 전달로 추출 정확도 저하 가능.
- **Downstream 영향**: 1회분 체인 단절. 다음 에피소드부터 LLM이 원고 본문에서 독립 추출하므로 자가 복구.
- **테스트 근거**: `test_reverse_expander_g2.py` L19-32에서 순차 의존성 보장 검증됨.
- **기존 문서**: 미발견.
- **권장 조치**: 현행 유지. 필요 시 실패 에피소드 재시도 옵션 추가.

---

## 오탐 제거 요약

| 후보 ID | 사유 |
|---------|------|
| C-05 | 의도된 graceful degradation (skeleton→details 폴백) |
| C-06 | block_id 문자열 정규화 — 포맷 변환이며 원칙 위반 아님 |
| C-11 (P1-2) | hud→state_changes 필드 재배치 — 포맷 변환이며 새 팩트 생성 아님. 원칙 1, 2 모두 준수 |
| C-12 (P1-3) | Arc stub 보강 — LLM 추출 결과의 범위별 집계/재배치. 새로운 서사 판단 없음. 원칙 1, 2 모두 준수 |
| C-14 | C-13에 통합 (동일 이슈의 세부 관찰) |
| C-15 | C-10과 동일 (빈 stub 삽입, 테스트 검증됨) |
| C-16 | new_npcs dict→str 정규화 — 타입 변환 |
| C-17 | normalize_hud — 필드명+타입 정규화, 값 판단 아님 |

---

## Coverage Gap Log

| 영역 | 현재 테스트 | 갭 |
|------|------------|-----|
| StoryExpander.generate_bible() None 반환 | 없음 | caller가 None 수신 시 동작 미검증 |
| StoryExpander._parse_json() list 반환 | 없음 | list→dict[0] 추출 경로 미검증 |
| ReverseExpander.persist_to_db() | 없음 | 트랜잭션 정상/롤백 경로 모두 미검증 |
| ReverseExpander._enrich_arc_stubs | 없음 | 집계 로직, 캡 초과 시 동작 미검증 |
| StoryExpander.extend_treatment() | 없음 | 배치 확장 + confirm_callback 경로 미검증 |
| ReverseExpander.persist_to_vectordb() | 없음 | VecMemory 연동 미검증 |
| prev_state 빈 stub 후 복구 | 간접적 (mock) | 실제 LLM 실패 시나리오 미검증 |

---

## 최종 수치

| Severity | 건수 | Finding ID |
|----------|------|------------|
| P0 | 0 | — |
| P1 | 1 | SZ0-T1-F02 (*) |
| P2 | 4 | SZ0-T1-F01, F02, F03, F04 |
| P3 | 4 | SZ0-T1-F05, F06, F07, F08 |
| 오탐 | 8 | C-05, C-06, C-11, C-12, C-14, C-15, C-16, C-17 |
| 4대 원칙 위반 | 0 | — |

(*) F02 재분류 주: 기능적 안전(트랜잭션 내)이므로 P2 확정. P1에서 하향.

### Pre-assigned 이슈 최종 판정

| Pre-assigned | 최종 | 사유 |
|-------------|------|------|
| P1-1 (L277 list→dict) | P3 (F05) | 방어 코드 존재, 프롬프트 구조상 단일 객체 반환 표준 |
| P1-2 (L897 hud→state_changes) | 오탐 | 포맷 변환, 원칙 위반 아님 |
| P1-3 (L1046 Arc stub 보강) | 오탐 | LLM 출력 집계/재배치, 원칙 위반 아님 |
| P3-10 (generate_bible 조기반환) | P2 (F01) | self.bible 상태 불일치 위험으로 상향 |
